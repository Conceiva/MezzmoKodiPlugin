import sys
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import os
import xml.etree.ElementTree
import re
import xml.etree.ElementTree as ET
import urlparse
import browse
import linecache
import contentrestriction
import media
import time
import datetime
import socket

syncoffset = 400
mezzmorecs = 0
dupelog = 'false'

def updateTexturesCache(contenturl):     # Update Kodi image cache timers
  
    try:
        from sqlite3 import dbapi2 as sqlite
    except:
        from pysqlite2 import dbapi2 as sqlite
                      
    DB = os.path.join(xbmc.translatePath("special://database"), "Textures13.db")
    db = sqlite.connect(DB)

    serverport = '%' + media.getServerport(contenturl) + '%'     #  Get Mezzmo server port info
    newtime = (datetime.datetime.now() + datetime.timedelta(days=-3)).strftime('%Y-%m-%d %H:%M:%S')
    cur = db.execute('UPDATE texture SET lasthashcheck=? WHERE URL LIKE ? and lasthashcheck=?', \
    (newtime, serverport, ""))          # Update Mezzmo image cache timers with no dates 
    rows = cur.rowcount       
    db.commit()
    cur.close()
    db.close()
    mgenlog = 'Mezzmo textures cache timers '  + str(rows) + ' rows updated.'
    xbmc.log(mgenlog, xbmc.LOGNOTICE)
    media.mgenlogUpdate(mgenlog)
  

def deleteTexturesCache(contenturl):        # do not cache texture images if caching disabled
    if media.settings('caching') == 'false':    
        try:
            from sqlite3 import dbapi2 as sqlite
        except:
            from pysqlite2 import dbapi2 as sqlite
                      
        DB = os.path.join(xbmc.translatePath("special://database"), "Textures13.db")
        db = sqlite.connect(DB)

        serverport = '%' + media.getServerport(contenturl) + '%'     #  Get Mezzmo server port info     
        cur = db.execute('DELETE FROM texture WHERE url LIKE ?', (serverport,))        
        rows = cur.rowcount
        mgenlog ='Mezzmo addon texture rows deleted: ' + str(rows)
        xbmc.log(mgenlog, xbmc.LOGNOTICE)
        media.mgenlogUpdate(mgenlog)

        db.commit()
        cur.close()
        db.close()
        media.settings('caching', 'true')   # reset back to true after clearing 


def dbClose():		 	        # Close database and commit any pending writes on abort
    try:
        from sqlite3 import dbapi2 as sqlite
    except:
        from pysqlite2 import dbapi2 as sqlite
                      
    DB = os.path.join(xbmc.translatePath("special://database"), media.getDatabaseName())
    db = sqlite.connect(DB)    
    
    db.commit()
    db.close()  


def getSeconds(t):
    x = time.strptime(t.split(',')[0],'%H:%M:%S.000')
    td = datetime.timedelta(hours=x.tm_hour,minutes=x.tm_min,seconds=x.tm_sec)
    seconds = int((td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6)
    if seconds == None:
        seconds = 0
    return seconds


def updateRealtime(mrecords, krecords, mlvcount, mnsyncount): #  Disable real time updates when 90% sync achieved

    mezzmorecords = mrecords - mlvcount - mnsyncount          #  Calculate adjusted Mezzmo records
    if krecords  >= mezzmorecords:                            #  100% maximum is Kodi > Mezzmo
        completepct = 100.0
    elif krecords > 0 and mezzmorecords > 0:                  #  Calculate % sync
        completepct = 1 / (float(mezzmorecords)/krecords) * 100.0
    else:
        completepct = 0

    if int(mezzmorecords * .9) > krecords:                    #  Check if in sync
        media.settings('kodiactor', 'true')                   #  Enable real time updates  
        media.settings('kodichange', 'true')
        msynclog = 'Mezzmo sync process not yet in sync at {:.1f}'.format(completepct) +     \
        '%. Real time updates enabled.'
        xbmc.log(msynclog, xbmc.LOGNOTICE)
        media.mezlogUpdate(msynclog)
    else:
        media.settings('kodiactor', 'false')                  #  Disable real time updates  
        media.settings('kodichange', 'false') 
        msynclog = 'Mezzmo sync process in sync at {:.1f}'.format(completepct) +              \
        '%. Real time updates disabled.'
        xbmc.log(msynclog, xbmc.LOGNOTICE)
        media.mezlogUpdate(msynclog)

    kodisync = media.settings('kodisync')                     #  Check Kodi auto sync
    mksync = media.settings('kodisyncvar')                    #  Get sync setting 
    if kodisync == 'true':
        if int(completepct) > 90 and mksync != 'Off'      \
        and mksync != 'Newest':                               #  Set to Newest > 90%
            media.settings('kodisyncvar', 'Newest') 
            msynclog = 'Mezzmo autosync set to Newest.'
            xbmc.log(msynclog, xbmc.LOGNOTICE)
            media.mezlogUpdate(msynclog)
        elif int(completepct) <= 90 and mksync != 'Off'   \
        and mksync != 'Normal':                               #  Set to Normal <= 90%
            media.settings('kodisyncvar', 'Normal') 
            msynclog = 'Mezzmo autosync set to Normal.'
            xbmc.log(msynclog, xbmc.LOGNOTICE)
            media.mezlogUpdate(msynclog)
        else:
            msynclog = 'Mezzmo autosync is enabled.'
            xbmc.log(msynclog, xbmc.LOGNOTICE)
            media.mezlogUpdate(msynclog)
    else:
        msynclog = 'Mezzmo autosync is disabled.'
        xbmc.log(msynclog, xbmc.LOGNOTICE)
        media.mezlogUpdate(msynclog)            


def checkDailySync():
    currhour = datetime.datetime.now().strftime('%H')
    syncflag = media.settings('dailysync')
    if syncflag != '':
        dailysync = int(syncflag)
    else:
        dailysync = 0
        media.settings('dailysync', '0')               #  Set daily sync flag
        
    xbmc.log('Mezzmo initial daily sync flag is: ' + str(dailysync), xbmc.LOGDEBUG)   

    if int(currhour) > 5 and dailysync <> 0:
        dailysync = 0                                  #  Reset daily sync flag
        media.settings('dailysync', str(dailysync))
        msynclog = 'Mezzmo daily sync process flag reset.'
        xbmc.log(msynclog, xbmc.LOGNOTICE)
        media.mezlogUpdate(msynclog)
    elif int(currhour) >= 0 and int(currhour) <= 5 and dailysync == 0:
        dailysync = 1                                  #  Set daily sync flag if not run yet
        msynclog = 'Mezzmo daily sync process flag set.'
        xbmc.log(msynclog, xbmc.LOGNOTICE)
        media.mezlogUpdate(msynclog)
    elif int(currhour) >= 0 and int(currhour) <= 5 and dailysync == 1:
        dailysync = 0         

    xbmc.log('Mezzmo final daily sync flag is: ' + str(dailysync), xbmc.LOGDEBUG)             

    return(dailysync)


def syncMezzmo(syncurl, syncpin, count):                 #  Sync Mezzmo to Kodi
    global syncoffset, dupelog
    ksync = media.settings('kodisyncvar')                #  Get sync setting
    if 'ContentDirectory' not in syncurl:
        msynclog = 'Mezzmo sync process aborted.  Invalid server selected.'
        xbmc.log(msynclog, xbmc.LOGNOTICE)
        media.mezlogUpdate(msynclog)
        return 
    if ksync != 'Off':                                   #  Check if enabled
        msynclog = 'Mezzmo sync beginning.'
        xbmc.log(msynclog, xbmc.LOGNOTICE)
        media.mezlogUpdate(msynclog)
        starttime = time.time()
        rows = 0

        newoffset = media.settings('sync_offset')        #  Get saved offset setting  
        try:                         
            syncoffset = int(newoffset)
        except:
            syncoffset = 0
            media.settings('sync_offset', str(syncoffset))


        clean = checkDailySync()                          #  Check sync flag
        if clean == 1 and count > 12:
            force = 1
            media.kodiCleanDB(syncurl,force)              #  Clear Kodi database daily
        if count < 12:   
            content = browse.Browse(syncurl, 'recent', 'BrowseDirectChildren', 0, 400, syncpin)
            rows = syncContent(content, syncurl, 'recent', syncpin, 0, 400)
            recs = media.countKodiRecs(syncurl)           #  Get record count in Kodi DB
            recscount = media.countsyncCount()            #  Get nosync record count in nosync DB
            nsyncount = recscount[0]
            lvcount = recscount[1]                        #  Get Live Channel record count in nosync DB
            msynclog = 'Mezzmo total Mezzmo record count: ' + str(mezzmorecs)
            xbmc.log(msynclog, xbmc.LOGNOTICE)
            media.mezlogUpdate(msynclog)            
            msynclog = 'Mezzmo total Live Channels count: ' + str(lvcount)
            xbmc.log(msynclog, xbmc.LOGNOTICE)
            media.mezlogUpdate(msynclog)    
            msynclog = 'Mezzmo total nosync videos count: ' + str(nsyncount)
            xbmc.log(msynclog, xbmc.LOGNOTICE)
            media.mezlogUpdate(msynclog)    
            updateRealtime(mezzmorecs, recs, lvcount, nsyncount)
        elif clean == 0 and ksync != 'Daily':             #  Hourly sync set of records
            content = browse.Browse(syncurl, 'recent', 'BrowseDirectChildren', 0, 400, syncpin)
            rows = syncContent(content, syncurl, 'recent', syncpin, 0, 400)
            if rows == None:                              #  Did sync get data from Mezzmo server ?
                rows = 0
                msynclog = 'Mezzmo sync process could not contact the Mezzmo server'
                xbmc.log(msynclog, xbmc.LOGNOTICE)
                media.mezlogUpdate(msynclog)   
            xbmc.log('Mezzmo sync offset = ' + str(syncoffset), xbmc.LOGDEBUG)  
            if rows == 400 and syncoffset % 400 == 0  \
                and ksync != 'Newest':                    #  Mezzmo database > 400 records
                syncoffset = syncoffset + rows - 400
                if mezzmorecs > 5000:                     #  Faster hourly sync for large databases
                    fetch = (mezzmorecs // 800) // 6 * 800
                else:                                     #  Number of records to get from Mezzmo
                    fetch = 800                           #  Slow hourly fetch       
                itemsleft = (mezzmorecs - syncoffset)     #  Items remaining in Mezzmo
                if  itemsleft < fetch:                    #  Detect end of Mezzmo database
                     fetch = itemsleft
                xbmc.log('Mezzmo fetch = ' + str(fetch), xbmc.LOGDEBUG)                                
                content = browse.Browse(syncurl, 'recent', 'BrowseDirectChildren', syncoffset, fetch, syncpin)
                rows1 = syncContent(content, syncurl, 'recent', syncpin, syncoffset, fetch)
                xbmc.log('Mezzmo sync rows1 = ' + str(rows1), xbmc.LOGDEBUG)
                if rows1 != None and rows1 > 0:
                    syncoffset = syncoffset + rows1
                    rows = rows + rows1
                else:
                    syncoffset = 400  
            xbmc.log('Mezzmo sync rows test = ' + str(rows), xbmc.LOGDEBUG)
            if rows % 400 <> 0:                        #  Start back through the Mezzmo database
                syncoffset = 400 
            recs = media.countKodiRecs(syncurl)        #  Get record count in Kodi DB
            recscount = media.countsyncCount()         #  Get nosync record count in nosync DB
            nsyncount = recscount[0]
            lvcount = recscount[1]                     #  Get Live Channel record count in nosync DB
            msynclog = 'Mezzmo total Mezzmo record count: ' + str(mezzmorecs)
            xbmc.log(msynclog, xbmc.LOGNOTICE)
            media.mezlogUpdate(msynclog)            
            msynclog = 'Mezzmo total Live Channels count: ' + str(lvcount)
            xbmc.log(msynclog, xbmc.LOGNOTICE)
            media.mezlogUpdate(msynclog)    
            msynclog = 'Mezzmo total nosync videos count: ' + str(nsyncount)
            xbmc.log(msynclog, xbmc.LOGNOTICE)
            media.mezlogUpdate(msynclog)     
            updateRealtime(mezzmorecs, recs, lvcount, nsyncount)                                 
        elif clean == 1:                               #  Sync all daily
            media.settings('kodiactor', 'false')       #  Disable real time updating ahead of full sync
            media.settings('kodichange', 'false')
            dupelog = media.settings('mdupelog')       #  Check if Mezzmo duplicate logging is enabled
            if dupelog == 'true':
                msynclog = 'Mezzmo duplicate logging is enabled. '
                xbmc.log(msynclog, xbmc.LOGNOTICE)
                media.mezlogUpdate(msynclog)     
            syncoffset = 0
            lvcount = 0                                #  Reset live channel skip counter
            nsyncount = 0                              #  Reset nosync skip counter  
            content = browse.Browse(syncurl, 'recent', 'BrowseDirectChildren', 0, 1000, syncpin)
            rows = syncContent(content, syncurl, 'recent', syncpin, 0, 1000)   
            recs = media.countKodiRecs(syncurl)        #  Get record count in Kodi DB
            recscount = media.countsyncCount()         #  Get nosync record count in nosync DB
            nsyncount = recscount[0]
            lvcount = recscount[1]                     #  Get Live Channel record count in nosync DB
            msynclog = 'Mezzmo total Mezzmo record count: ' + str(mezzmorecs)
            xbmc.log(msynclog, xbmc.LOGNOTICE)
            media.mezlogUpdate(msynclog)            
            msynclog = 'Mezzmo total Live Channels count: ' + str(lvcount)
            xbmc.log(msynclog, xbmc.LOGNOTICE)
            media.mezlogUpdate(msynclog)    
            msynclog = 'Mezzmo total nosync videos count: ' + str(nsyncount)
            xbmc.log(msynclog, xbmc.LOGNOTICE)
            media.mezlogUpdate(msynclog)    
            media.optimizeDB()                         #  Optimize DB after resync
            media.settings('dailysync', '1')           #  Set daily sync flag  
        endtime = time.time()
        duration = endtime-starttime
        difference = str(int(duration // 60)) + 'm ' + str(int(duration % 60)) + 's checked.'
        media.settings('sync_offset', str(syncoffset))
        dupelog = 'false'                              #  Set Mezzmo duplicate logging to disable
        if ksync != 'Daily' or count < 30 or clean == 1:  #  Display summary stats if restart or not daily
            msynclog = 'Mezzmo sync completed. ' + str(rows) + ' videos in ' + difference
        elif ksync == 'Daily':
            msynclog = 'Mezzo sync Daily set.  Hourly sync not enabled.'  
        xbmc.log(msynclog, xbmc.LOGNOTICE)
        media.mezlogUpdate(msynclog)
    if ksync != 'Daily':
        msynclog = 'Mezzmo sync setting is: ' + media.settings('kodisyncvar') 
        xbmc.log(msynclog, xbmc.LOGNOTICE)
        media.mezlogUpdate(msynclog)    
    if media.settings('perflog') == 'true':          #  Check if performance logging is enabled
        msynclog = 'Mezzmo performance logging is enabled.'
        xbmc.log(msynclog, xbmc.LOGNOTICE)
        media.mezlogUpdate(msynclog) 

def syncContent(content, syncurl, objectId, syncpin, syncoffset, maxrecords):  # Mezzmo data parsing / insertion function
    contentType = 'movies'
    itemsleft = -1
    global mezzmorecs, dupelog
    koditv = media.settings('koditv')
    try:
        while True:
            e = xml.etree.ElementTree.fromstring(content)
            
            body = e.find('.//{http://schemas.xmlsoap.org/soap/envelope/}Body')
            browseresponse = body.find('.//{urn:schemas-upnp-org:service:ContentDirectory:1}BrowseResponse')
            result = browseresponse.find('Result')
            NumberReturned = browseresponse.find('NumberReturned').text
            TotalMatches = browseresponse.find('TotalMatches').text
            xbmc.log('Mezzmo total matches = ' + str(TotalMatches), xbmc.LOGDEBUG) 
            xbmc.log('Mezzmo number returned = ' + NumberReturned, xbmc.LOGDEBUG)
            xbmc.log('Mezzmo records = ' + str(mezzmorecs), xbmc.LOGDEBUG)
            if not TotalMatches:                       #  Sanity check
                TotalMatches = 0
            else:
                mezzmorecs = int(TotalMatches) + 5     #  Set global variable with record count
                    
            if int(NumberReturned) == 0:               #  Stop once offset = Total matches
                itemsleft = 0
                return(0)
                break; #sanity check
            
            if maxrecords == 1000 or maxrecords > int(TotalMatches):
                TotalMatches = int(TotalMatches) + 5
                dsyncflag = 1
            else:
                TotalMatches = maxrecords   
                dsyncflag = 0

            if itemsleft == -1:
                itemsleft = TotalMatches

            #xbmc.log('Mezzmo offset = ' + str(syncoffset), xbmc.LOGNOTICE)
            #xbmc.log('Mezzmo items left initial = ' + str(itemsleft), xbmc.LOGNOTICE)

            elems = xml.etree.ElementTree.fromstring(result.text.encode('utf-8'))
            
            for container in elems.findall('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}container'):
                title = container.find('.//{http://purl.org/dc/elements/1.1/}title').text 
                containerid = container.get('id')
                
                description_text = ''
                description = container.find('.//{urn:schemas-upnp-org:metadata-1-0/upnp/}longDescription')
                if description != None and description.text != None:
                    description_text = description.text
    
                icon = container.find('.//{urn:schemas-upnp-org:metadata-1-0/upnp/}albumArtURI')
                if icon != None:
                    icon = icon.text
                    if (icon[-4:]) !=  '.jpg': 
                        icon = icon + '.jpg'
                    xbmc.log('Handle browse initial icon is: ' + icon, xbmc.LOGDEBUG)             

            dbfile = media.openKodiDB()                   #  Open Kodi database
            dbsync = media.openNosyncDB()                 #  Open Mezzmo nosync database
            for item in elems.findall('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}item'):
                title = item.find('.//{http://purl.org/dc/elements/1.1/}title').text
                itemid = item.get('id')
                icon = None
                albumartUri = item.find('.//{urn:schemas-upnp-org:metadata-1-0/upnp/}albumArtURI')
                if albumartUri != None:
                    icon = albumartUri.text  
                    if (icon[-4:]) !=  '.jpg': 
                        icon = icon + '.jpg'
                    xbmc.log('Handle browse second icon is: ' + icon, xbmc.LOGDEBUG)
                else:
                    icon = ''    

                res = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}res')
                subtitleurl = None
                duration_text = ''
                video_width = 0
                video_height = 0
                aspect = 0.0
                validf = 0
                
                if res != None:
                    itemurl = res.text 
                    #xbmc.log('The current URL is: ' + itemurl, xbmc.LOGNOTICE)
                    subtitleurl = res.get('{http://www.pv.com/pvns/}subtitleFileUri')            
                    duration_text = res.get('duration')
                    if duration_text == None:
                        duration_text = '00:00:00.000'
                    resolution_text = res.get('resolution')
                    if resolution_text != None:
                        mid = resolution_text.find('x')
                        video_width = int(resolution_text[0:mid])
                        video_height = int(resolution_text[mid + 1:])
                        aspect = float(float(video_width) / float(video_height))
                        validf = 1	     #  Set valid file info flag
                    
                backdropurl = ''                        
                backdropurl = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}cvabackdrop')
                if backdropurl != None:
                    backdropurl = backdropurl.text
                    if (backdropurl [-4:]) !=  '.jpg': 
                        backdropurl  = backdropurl  + '.jpg'

                trailerurl = ''                                   
                trailerurl = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}trailer')
                if trailerurl != None:
                    trailerurl = trailerurl.text
                
                genre_text = ''
                genre = item.find('.//{urn:schemas-upnp-org:metadata-1-0/upnp/}genre')
                if genre != None:
                    genre_text = genre.text
                    
                aired_text = ''
                aired = item.find('.//{http://purl.org/dc/elements/1.1/}date')                
                if aired != None:
                    aired_text = aired.text
                  
                album_text = ''
                album = item.find('.//{urn:schemas-upnp-org:metadata-1-0/upnp/}album')
                if album != None:
                    album_text = album.text
                  
                release_year_text = ''
                release_year = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}release_year')
                if release_year != None:
                    release_year_text = release_year.text

                release_date_text = ''
                release_date = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}release_date')
                if release_date != None:
                    release_date_text = release_date.text
                
                description_text = ''
                description = item.find('.//{urn:schemas-upnp-org:metadata-1-0/upnp/}longDescription')
                if description != None and description.text != None:
                    description_text = description.text
                      
                imageSearchUrl = ''
                imageSearchUrl = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}imageSearchUrl')
                if imageSearchUrl != None:
                    imageSearchUrl = imageSearchUrl.text
                   
                artist_text = ''
                artist = item.find('.//{urn:schemas-upnp-org:metadata-1-0/upnp/}artist')
                if artist != None:
                    artist_text = artist.text.encode('utf-8', 'ignore')

                creator_text = ''
                creator = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}creator')
                if creator != None:
                    creator_text = creator.text   

                date_added_text = ''                
                date_added = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}date_added')
                if date_added != None:
                    date_added_text = date_added.text           
                   
                tagline_text = ''
                tagline = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}tag_line')
                if tagline != None:
                    tagline_text = tagline.text
                    
                categories = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}categories')

                episode_text = ''
                episode = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}episode')
                if episode != None:
                    episode_text = episode.text
                 
                season_text = ''
                season = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}season')
                if season != None:
                    season_text = season.text
                 
                playcount = 0
                playcount_text = ''
                playcountElem = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}playcount')                
                if playcountElem != None:
                    playcount_text = playcountElem.text
                    playcount = int(playcount_text)
                 
                last_played_text = ''
                last_played = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}last_played')
                if last_played != None:
                    last_played_text = last_played.text
                        
                writer_text = ''
                writer = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}writers')
                if writer != None:
                    writer_text = writer.text
                       
                content_rating_text = ''
                content_rating = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}content_rating')
                if content_rating != None:
                    content_rating_text = content_rating.text
              
                imdb_text = ''
                imdb = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}imdb_id')
                if imdb != None:
                    imdb_text = imdb.text
                
                
                dcmInfo_text = ''
                dcmInfo = item.find('.//{http://www.sec.co.kr/}dcmInfo')
                if dcmInfo != None:
                    dcmInfo_text = dcmInfo.text
                    valPos = dcmInfo_text.find('BM=') + 3
                    dcmInfo_text = dcmInfo_text[valPos:]
              
                rating_val = ''
                rating = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}rating')
                if rating != None:
                    rating_val = rating.text
                    rating_val = float(rating_val) * 2
                    rating_val = str(rating_val) #kodi ratings are out of 10, Mezzmo is out of 5
                
                production_company_text = ''
                production_company = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}production_company')
                if production_company != None:
                    production_company_text = production_company.text

                sort_title_text = ''
                sort_title = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}sort_title')
                if sort_title != None:
                    sort_title_text = sort_title.text
              
                video_codec_text = ''
                video_codec = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}video_codec')
                if video_codec != None:
                    video_codec_text = video_codec.text
                if video_codec_text == 'vc1':     #  adjust for proper Kodi codec display
                    video_codec_text = 'vc-1'
                
                audio_codec_text = ''
                audio_codec = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}audio_codec')
                if audio_codec != None:
                    audio_codec_text = audio_codec.text
                
                audio_channels_text = ''
                audio_channels = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}audio_channels')
                if audio_channels != None:
                    audio_channels_text = audio_channels.text
                
                audio_lang = ''
                audio_streams = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}audio')
                if audio_streams != None:
                    for stream in audio_streams.findall('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}stream'):
                        if stream.get('selected') == 'auto' or stream.get('selected') == 'true':
                            audio_lang = stream.get('lang')
                            break
                     
                subtitle_lang = ''
                captions_streams = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}captions')
                if captions_streams != None:
                    for stream in captions_streams.findall('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}stream'):
                        if stream.get('selected') == 'auto' or stream.get('selected') == 'true':
                            subtitle_lang = stream.get('language')
                            break

                #mediaClass 
                mediaClass_text = 'video'
                mediaClass = item.find('.//{urn:schemas-sony-com:av}mediaClass')
                if mediaClass != None:
                    mediaClass_text = mediaClass.text
                    if mediaClass_text == 'V':
                        mediaClass_text = 'video'
                    if mediaClass_text == 'M':
                        mediaClass_text = 'music'
                    if mediaClass_text == 'P':
                        mediaClass_text = 'picture'
                #xbmc.log('Checking title: ' + title.encode('utf-8', 'ignore'), xbmc.LOGNOTICE)  
                mtitle = media.displayTitles(title)                           
                tvcheckval = media.tvChecker(season_text, episode_text, koditv, mtitle, categories) # Check if Ok to add
                if tvcheckval[1] == 1 and validf == 1:                  #  Update nosync database live channel
                    media.syncCount(dbsync, mtitle, "livec")       
                if tvcheckval[2] == 1 and validf == 1:                  #  Update nosync database nosync
                    media.syncCount(dbsync, mtitle, "nosync")               
                if tvcheckval[0] == 1 and validf == 1:  
                    pathcheck = media.getPath(itemurl)                  #  Get path string for media file
                    serverid = media.getMServer(itemurl)                #  Get Mezzmo server id
                    filekey = media.checkDBpath(itemurl, mtitle, playcount, dbfile, pathcheck, serverid,        \
                    season_text, episode_text, album_text, last_played_text, date_added_text, dupelog)
                    #xbmc.log('Checking movie: ' + mtitle.encode('utf-8', 'ignore'), xbmc.LOGNOTICE)                    
                    #xbmc.log('Mezzmo filekey is: ' + str(filekey), xbmc.LOGNOTICE) 
                    durationsecs = getSeconds(duration_text)            #  convert movie duration to seconds before passing
                    kodichange = 'true'                                 #  Enable change detection during sync
                    if filekey[4] == 1:
                        showId = media.checkTVShow(filekey, album_text, genre_text, dbfile, content_rating_text, \
                        production_company_text)
                        mediaId = media.writeEpisodeToDb(filekey, mtitle, description_text, tagline_text,        \
                        writer_text, creator_text, aired_text, rating_val, durationsecs, genre_text, trailerurl, \
                        content_rating_text, icon, kodichange, backdropurl, dbfile, production_company_text,     \
                        sort_title_text, season_text, episode_text, showId, dupelog)  
                    else:  
                        mediaId = media.writeMovieToDb(filekey, mtitle, description_text, tagline_text,          \
                        writer_text, creator_text, release_date_text, rating_val, durationsecs, genre_text,      \
                        trailerurl, content_rating_text, icon, kodichange, backdropurl, dbfile,                  \
                        production_company_text, sort_title_text, dupelog)
                    if (artist != None and filekey[0] > 0) or mediaId == 999999: #  Add actor information to new movie
                        media.writeActorsToDb(artist_text, mediaId, imageSearchUrl, mtitle, dbfile, filekey)
                    media.writeMovieStreams(filekey, video_codec_text, aspect, video_height, video_width,  \
                    audio_codec_text, audio_channels_text, durationsecs, mtitle, kodichange, itemurl,      \
                    icon, backdropurl, dbfile, pathcheck, dupelog)      # Update movie stream info 
                    xbmc.log('The movie name is: ' + mtitle.encode('utf-8'), xbmc.LOGDEBUG)
                                                      
            itemsleft = itemsleft - int(NumberReturned)
            xbmc.log('Mezzmo items left: ' + str(itemsleft), xbmc.LOGDEBUG)
            dbfile.commit()                #  Commit writes

            if itemsleft <= 0:
                dbfile.commit()
                dbfile.close()             #  Final commit writes and close Kodi database
                dbsync.commit()
                dbsync.close()
                return(TotalMatches)  
                break
                        
            # get the next items
            offset = (TotalMatches - itemsleft) + syncoffset
            requestedCount = 1000
            if itemsleft < 1000:
                requestedCount = itemsleft
            
            pin = media.settings('content_pin')   
            content = browse.Browse(syncurl, objectId, 'BrowseDirectChildren', offset, requestedCount, syncpin)
    except Exception as e:
        printsyncexception()
        pass
        

def printsyncexception():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    xbmc.log( 'EXCEPTION IN ({0}, LINE {1} "{2}"): {3}'.format(filename, lineno, line.strip(), exc_obj))

