import sys
import pickle
import xbmcgui
import xbmcplugin
import ssdp
import xbmcaddon
import xbmcgui
import urllib.request, urllib.error, urllib.parse
import urllib.request, urllib.parse, urllib.error
import xml.etree.ElementTree
import re
import xml.etree.ElementTree as ET
import urllib.parse
import browse
import contentrestriction
import xbmc
import linecache
import sys
import datetime
import time
import json
import os

addon = xbmcaddon.Addon()
base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urllib.parse.parse_qs(sys.argv[2][1:])

def get_installedversion():
    # retrieve current installed version
    json_query = xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Application.GetProperties", "params": {"properties": ["version", "name"]}, "id": 1 }')
    json_query = json.loads(json_query)
    version_installed = []
    if 'result' in json_query and 'version' in json_query['result']:
        version_installed  = json_query['result']['version']['major']
    return str(version_installed)
    
installed_version = get_installedversion()

def getDatabaseName():
    if installed_version == '10':
        return "MyVideos37.db"
    elif installed_version == '11':
        return "MyVideos60.db"
    elif installed_version == '12':
        return "MyVideos75.db"
    elif installed_version == '13':
        return "MyVideos78.db"
    elif installed_version == '14':
        return "MyVideos90.db"
    elif installed_version == '15':
        return "MyVideos93.db"
    elif installed_version == '16':
        return "MyVideos99.db"
    elif installed_version == '17':
        return "MyVideos107.db"
    elif installed_version == '18':
        return "MyVideos116.db"
    elif installed_version == '19':
        return "MyVideos117.db"
       
    return ""   

def kodiCleanDB():
    if addon.getSetting('kodiclean') == 'true':     #  clears Kodi actor DB if enabled in setings
        try:
            from sqlite3 import dbapi2 as sqlite
        except:
            from pysqlite2 import dbapi2 as sqlite
                      
        DB = os.path.join(xbmc.translatePath("special://database"), "MyVideos117.db")  # only use on Kodi 19 and higher
        db = sqlite.connect(DB)

        db.execute('DELETE FROM art;',);
        db.execute('DELETE FROM movie;',);
        db.execute('DELETE FROM files;',);
        db.execute('DELETE FROM actor;',);
        db.execute('DELETE FROM actor_link;',);
        db.execute('DELETE FROM streamdetails;',);
    
        xbmc.log('Kodi actor database cleared: ', xbmc.LOGNOTICE)
        db.commit()
        db.close()
        addon.setSetting('kodiclean', 'false')   # reset back to false after clearing

def writeActorsToDb(actors, movieId, imageSearchUrl, mtitle):
    actorlist = actors.replace(', Jr.' , ' Jr.').replace(', Sr.' , ' Sr.').split(', ')    
    try:
        from sqlite3 import dbapi2 as sqlite
    except:
        from pysqlite2 import dbapi2 as sqlite
                      
    DB = os.path.join(xbmc.translatePath("special://database"), "MyVideos117.db")  # only use on Kodi 19 and higher
    db = sqlite.connect(DB)
    #xbmc.log('The current movieID is: ' + str(movieId), xbmc.LOGNOTICE)
    if movieId == 999999:                                         # Actor info needs updated
        curm = db.execute('SELECT idMovie FROM movie WHERE c00=?',(mtitle,))  # Get movie ID
        movietuple = curm.fetchone()
        movieId = movietuple[0]                                   # Get real movieId
        delete_query = 'DELETE FROM actor_link WHERE media_id = ' + str(movieId)
        db.execute(delete_query)                                  #  Delete old actor link info
    if movieId != 0:
        for actor in actorlist:     
            f = { 'imagesearch' : actor}
            searchUrl = imageSearchUrl + "?" + urllib.parse.urlencode(f)
            #xbmc.log('The current actor is: ' + str(actor), xbmc.LOGNOTICE)      # actor insertion debugging
            #xbmc.log('The movieId is: ' + str(movieId), xbmc.LOGNOTICE)          # actor insertion debugging
            #cur = db.execute('SELECT actor_id FROM actor WHERE name=?',(actor.decode('utf-8'),))   
            cur = db.execute('SELECT actor_id FROM actor WHERE name=?',(actor,))   
            actortuple = cur.fetchone()                                           #  Get actor id from actor table
            cur.close()
            if not actortuple:             #  If actor not in actor table insert and fetch new actor ID
                #db.execute('INSERT into ACTOR (name, art_urls) values (?, ?)', (actor.decode('utf-8'), searchUrl,))
                #cur = db.execute('SELECT actor_id FROM actor WHERE name=?',(actor.decode('utf-8'),))   
                db.execute('INSERT into ACTOR (name, art_urls) values (?, ?)', (actor, searchUrl,))
                cur = db.execute('SELECT actor_id FROM actor WHERE name=?',(actor,)) 
                actortuple = cur.fetchone()                       #  Get actor id from actor table
                cur.close()
            if actortuple:                 #  Insert actor to movie link in actor link table
                actornumb = actortuple[0] 
                db.execute('INSERT OR REPLACE into ACTOR_LINK (actor_id, media_id, media_type) values (?, ?, ?)', \
                (actornumb, movieId, 'movie',))
                #xbmc.log('The current actor number is: ' + str(actornumb) + "  " + str(movieId), xbmc.LOGNOTICE)
    db.commit()
    db.close()       

def deleteTexturesCache(contenturl):    # do not cache texture images if caching disabled
    if addon.getSetting('caching') == 'false':    
        try:
            from sqlite3 import dbapi2 as sqlite
        except:
            from pysqlite2 import dbapi2 as sqlite
                      
        DB = os.path.join(xbmc.translatePath("special://database"), "Textures13.db")
        db = sqlite.connect(DB)
    
        imageDeleteURL = '"' + contenturl.replace('ContentDirectory/control','content/%"')
        delete_query = 'DELETE FROM texture WHERE url LIKE ' + imageDeleteURL 
        #xbmc.log('Image delete query: ' + delete_query, xbmc.LOGNOTICE)
    
        cur = db.execute(delete_query)        # delete only cached images from Mezzmo server
        rows = cur.rowcount
        xbmc.log('Mezzmo addon texture rows deleted: ' + str(rows), xbmc.LOGNOTICE)
        db.commit()
        db.close()       

def checkDBpath(itemurl, mtitle, mplaycount):           #  Check if video path already exists in Kodi databae
    rtrimpos = itemurl.rfind('/')
    pathcheck = itemurl[:rtrimpos+1]
    filecheck = itemurl[rtrimpos+1:]
    #xbmc.log('Item path: ' + pathcheck, xbmc.LOGNOTICE)
    #xbmc.log('Item file: ' + filecheck, xbmc.LOGNOTICE)

    try:
        from sqlite3 import dbapi2 as sqlite
    except:
        from pysqlite2 import dbapi2 as sqlite
                      
    DB = os.path.join(xbmc.translatePath("special://database"), "MyVideos117.db")  # only use on Kodi 19 and higher
    db = sqlite.connect(DB)
    
    curf = db.execute('SELECT idFile, playcount FROM files INNER JOIN movie USING (idFile)  \
    WHERE c00=?',(mtitle,))           # Check if movie exists in Kodi DB  
    filetuple = curf.fetchone()
    # xbmc.log('Checking path for : ' + mtitle.encode('utf-8','ignore'), xbmc.LOGNOTICE)            # Path check debugging

    if not filetuple:                 # if doesn't exist insert into Kodi DB and return file key value
        curp = db.execute('SELECT idPath FROM path WHERE strPATH=?',(pathcheck,))  #  Check path table
        pathtuple = curp.fetchone()
        # xbmc.log('File not found : ' + mtitle.encode('utf-8','ignore'), xbmc.LOGNOTICE)
        if not pathtuple:             # if path doesn't exist insert into Kodi DB and return path key value
            db.execute('INSERT into PATH (strpath) values ("' + pathcheck + '")')
            curp = db.execute('SELECT idPath FROM path WHERE strPATH=?',(pathcheck,)) 
            pathtuple = curp.fetchone()
        pathnumb = pathtuple[0]

        db.execute('INSERT into FILES (idPath, strFilename, playCount) values (?, ?, ? )', (str(pathnumb), filecheck, mplaycount))
        #cur = db.execute('SELECT idFile FROM files WHERE strFilename=?',(filecheck.decode('utf-8'),)) 
        cur = db.execute('SELECT idFile FROM files WHERE strFilename=?',(filecheck,)) 
        filetuple = cur.fetchone()
        filenumb = filetuple[0] 
    else:                            # Return 0 if file already exists and check for play count change 
        filenumb = filetuple[0] 
        # xbmc.log('File found : ' + filecheck.encode('utf-8','ignore') + ' ' + str(filenumb), xbmc.LOGNOTICE)
        fpcount = filetuple[1]
        if fpcount != mplaycount:    # If Mezzmo playcount different than Kodi DB, update Kodi DB
            db.execute('UPDATE files SET playCount=? WHERE idFile=?', (mplaycount, filenumb,))
            # xbmc.log('File Play mismatch: ' + str(fpcount) + ' ' + str(mplaycount), xbmc.LOGNOTICE)
        filenumb = 0                 
    
    db.commit()
    db.close()  
    return(filenumb) 

def writeMovieToDb(fileId, mtitle, mplot, mtagline, mwriter, mdirector, myear, poster, mduration, mgenre, mtrailer, mrating, micon, kchange):  
    try:
        from sqlite3 import dbapi2 as sqlite
    except:
        from pysqlite2 import dbapi2 as sqlite
                      
    DB = os.path.join(xbmc.translatePath("special://database"), "MyVideos117.db")  # only use on Kodi 19 and higher
    db = sqlite.connect(DB)

    if fileId > 0:                                          #  Insert movie if does not exist in Kodi DB
        #xbmc.log('The current movie is: ' + mtitle, xbmc.LOGNOTICE)
        #xbmc.log('The current icon is: ' + micon, xbmc.LOGNOTICE)
        mgenres = mgenre.replace(',' , ' /')                #  Format genre for proper Kodi display
        db.execute('INSERT into MOVIE (idFile, c00, c01, c03, c06, c11, c15, premiered, c14, c19, c12) values \
        (?, ?, ?, ?, ?, ?, ? ,? ,? ,? ,?)', (fileId, mtitle, mplot, mtagline, mwriter, mduration, mdirector,  \
        myear, mgenres, mtrailer, mrating))  #  Add movie information
        cur = db.execute('SELECT idMovie FROM movie WHERE idFile=?',(fileId,))  
        movietuple = cur.fetchone()
        movienumb = movietuple[0]                           # get new movie id    
        db.execute('INSERT into ART (media_id, media_type, type, url) values (?, ?, ?, ?)', (movienumb, 'movie', 'poster', micon))
        db.execute('INSERT into ART (media_id, media_type, type, url) values (?, ?, ?, ?)', (movienumb, 'fanart', 'poster', micon))

    elif kchange == 'true':                                 #  Update metadata if changes
        curm = db.execute('SELECT idMovie, c01, c03, c06, c11, c15, c14, c12, premiered, idFile FROM movie WHERE c00=?',(mtitle,))  
        movietuple = curm.fetchone()
        movienumb = movietuple[0]
        kplot = movietuple[1]
        ktagline = movietuple[2]
        kwriter = movietuple[3]     
        kduration = movietuple[4]
        kdirector = movietuple[5]
        kgenre = movietuple[6]
        krating = movietuple[7]
        kyear = movietuple[8]
        kfile = movietuple[9]
        kgenres = kgenre.replace(' /' , ',')                 #  Format genre for proper Kodi display
        #xbmc.log('Checking movie for changes : ' + mtitle.encode('utf-8', 'ignore'), xbmc.LOGNOTICE)        
        if kplot != mplot or ktagline != mtagline or kwriter != mwriter or kdirector != mdirector \
        or kyear != myear or krating != mrating or kgenres != mgenre or int(kduration) != mduration:  # Update movie info if changed
            mgenres = mgenre.replace(',' , ' /')             #  Format genre for proper Kodi display
            db.execute('UPDATE MOVIE SET c01=?, c03=?, c06=?, c11=?, c15=?, premiered=?, c14=?, c19=?, \
            c12=? WHERE idMovie=?', (mplot,  mtagline, mwriter, mduration, mdirector, myear, mgenres,  \
            mtrailer, mrating, movienumb))                   #  Update movie information
            movienumb = 999999                               # Trigger actor update
            xbmc.log('There was a Mezzmo metadata change detected: ' + mtitle, xbmc.LOGNOTICE)
    else:
        movienumb = 0                                        # disable change checking

    db.commit()
    db.close()  
    return(movienumb)

def writeMovieStreams(fileId, mvcodec, maspect, mvheight, mvwidth, macodec, mchannels, mduration, mtitle, kchange, itemurl, micon):
    try:
        from sqlite3 import dbapi2 as sqlite
    except:
        from pysqlite2 import dbapi2 as sqlite
                      
    DB = os.path.join(xbmc.translatePath("special://database"), "MyVideos117.db")  # only use on Kodi 19 and higher
    db = sqlite.connect(DB)

    #xbmc.log('Checking movie for streamchanges : ' + mtitle, xbmc.LOGNOTICE)
    if fileId > 0:                      #  Insert stream details if file does not exist in Kodi DB
        db.execute('INSERT into STREAMDETAILS (idFile, iStreamType, strVideoCodec, fVideoAspect, iVideoWidth, \
        iVideoHeight, iVideoDuration) values (?, ?, ?, ?, ? ,? ,?)', (fileId, '0', mvcodec, maspect, mvwidth, \
        mvheight, mduration))
        db.execute('INSERT into STREAMDETAILS (idFile, iStreamType, strAudioCodec, iAudioChannels) values     \
        (?, ?, ? ,?)', (fileId, '1', macodec, mchannels))
    elif kchange == 'true':             #  Update stream details, filename, artwork and movie duration if changes
        scur = db.execute('SELECT iVideoDuration, strVideoCodec, strAudioCodec, idFile, strFilename, idmovie, url \
        FROM STREAMDETAILS INNER JOIN movie USING (idFile) INNER JOIN files USING (idfile) INNER JOIN art ON      \
        movie.idMovie=art.media_id WHERE c00=?',(mtitle,))      
        scheck = scur.fetchone()
        sdur = scheck[0]		     # Get duration from Kodi DB
        svcodec = scheck[1]		     # Get video codec from Kodi DB
        scheck = scur.fetchone()
        sacodec = scheck[2]		     # Get audio codec from Kodi DB
        filenumb = scheck[3]
        rtrimpos = itemurl.rfind('/')        # Check for container / file name change
        pathcheck = itemurl[:rtrimpos+1]
        filecheck = itemurl[rtrimpos+1:]
        mextpos = filecheck.rfind('.')       # get Mezzmo file extension
        mext = filecheck[mextpos+1:]
        pfilename = scheck[4]
        movienumb = scheck[5]
        kextpos = pfilename.rfind('.')       # get Kodi file extension
        kext = pfilename[kextpos+1:]
        kicon = scheck[6]                    # Get Kodi DB poster URL
        if sdur != mduration or svcodec != mvcodec or sacodec != macodec  or kext != mext or kicon != micon:
            xbmc.log('There was a Mezzmo streamdetails or artwork change detected: ' +   \
            mtitle, xbmc.LOGNOTICE)
            delete_query = 'DELETE FROM streamdetails WHERE idFile = ' + str(filenumb)
            db.execute(delete_query)         #  Delete old stream info
            db.execute('INSERT into STREAMDETAILS (idFile, iStreamType, strVideoCodec, fVideoAspect, iVideoWidth,  \
            iVideoHeight, iVideoDuration) values (?, ?, ?, ?, ? ,? ,?)', (filenumb, '0', mvcodec, maspect, mvwidth,\
            mvheight, mduration))
            db.execute('INSERT into STREAMDETAILS (idFile, iStreamType, strAudioCodec, iAudioChannels) values      \
            (?, ?, ? ,?)', (filenumb, '1', macodec, mchannels))
            db.execute('UPDATE movie SET c11=? WHERE idFile=?', (mduration, filenumb,))
            curp = db.execute('SELECT idPath FROM path WHERE strPATH=?',(pathcheck,))  #  Check path table
            pathtuple = curp.fetchone()
            if not pathtuple:               # if path doesn't exist insert into Kodi DB and return path key value
                db.execute('INSERT into PATH (strpath) values ("' + pathcheck + '")')
                curp = db.execute('SELECT idPath FROM path WHERE strPATH=?',(pathcheck,)) 
                pathtuple = curp.fetchone()
            pathnumb = pathtuple[0]
            db.execute('UPDATE files SET idPath=?, strFilename=? WHERE idFile=?', (pathnumb, filecheck, filenumb))
            delete_query = 'DELETE FROM art WHERE media_id = ' + str(movienumb)
            db.execute(delete_query)                         #  Update old art info in case of extension change
            db.execute('INSERT into ART (media_id, media_type, type, url) values (?, ?, ?, ?)', (movienumb, 'movie', 'poster', micon))
            db.execute('INSERT into ART (media_id, media_type, type, url) values (?, ?, ?, ?)', (movienumb, 'fanart', 'poster', micon))

    db.commit()
    db.close()  

def displayTitles(mtitle):                              #  Remove common Mezzmo Display Title variables
    if len(mtitle) >= 8:
        if mtitle[4] == '-' and int(mtitle[:3]) <= 999: # check for Mezzmo %FILECOUNTER% in video title
            dtitle = mtitle[6:len(mtitle)]
        elif mtitle[len(mtitle)-6] == '(' and mtitle[len(mtitle)-1] == ')' and int(mtitle[-5:-1]) >= 1900 and \
        mtitle[len(mtitle)-8] != '-':
            dtitle = mtitle[:-7]                        # check for Mezzmo %YEAR% in video title
        else:
            dtitle = mtitle                             # else leave unchanged    
    else:
        dtitle = mtitle

    return(dtitle)    

def tvChecker(mseason, mepisode):       # add TV shows to Kodi DB if enabled and is TV show
    tvcheck = 1
    if int(mseason) > 0  and int(mepisode) > 0 and addon.getSetting('koditv') == 'false':
        tvcheck = 0 
    #xbmc.log('TV check value is: ' + str(tvcheck), xbmc.LOGNOTICE)

    return(tvcheck)

def dbIndexes():			# Improve performance for database lookups
    try:
        from sqlite3 import dbapi2 as sqlite
    except:
        from pysqlite2 import dbapi2 as sqlite
                      
    DB = os.path.join(xbmc.translatePath("special://database"), "MyVideos117.db")  # only use on Kodi 19 and higher
    db = sqlite.connect(DB)
    
    db.execute('DROP INDEX IF EXISTS ix_movie_file_3;',)     
    db.execute('CREATE UNIQUE INDEX "ix_movie_file_3" ON "movie" ("c00", "idFile");',)
    db.commit()
    db.close()  
    
def getSeconds(t):
    x = time.strptime(t.split(',')[0],'%H:%M:%S.000')
    td = datetime.timedelta(hours=x.tm_hour,minutes=x.tm_min,seconds=x.tm_sec)
    seconds = int((td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6)
    if seconds == None:
        seconds = 0
    return seconds
    
def message(msg):
    __addon__ = xbmcaddon.Addon()
    __addonname__ = __addon__.getAddonInfo('name')
 
 
    xbmcgui.Dialog().ok(__addonname__, str(msg))

def printexception():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    xbmc.log( 'EXCEPTION IN ({0}, LINE {1} "{2}"): {3}'.format(filename, lineno, line.strip(), exc_obj))

def listServers(force):
    timeoutval = float(addon.getSetting('ssdp_timeout'))
    saved_servers = addon.getSetting('saved_servers')
    if len(saved_servers) == 0 or force:
        servers = ssdp.discover("urn:schemas-upnp-org:device:MediaServer:1", timeout=timeoutval)
        # save the servers for faster loading
        addon.setSetting('saved_servers', pickle.dumps(servers,0,fix_imports=True))
    else:
        saved_servers = saved_servers.encode('utf-8')
        servers = pickle.loads(saved_servers, fix_imports=True)
        
    onlyShowMezzmo = addon.getSetting('only_mezzmo_servers') == 'true'

    itemurl = build_url({'mode': 'serverList', 'refresh': True})        
    li = xbmcgui.ListItem('Refresh')
    li.setArt({'icon':addon.getAddonInfo("path") + '/resources/media/refresh.png'})
    
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=itemurl, listitem=li, isFolder=True)

    xbmc.log('Mezzmo server search: ' + str(len(servers)), xbmc.LOGNOTICE)
    for server in servers:
        url = server.location
        
        xbmc.log('Mezzmo server url: ' + url, xbmc.LOGNOTICE)
        
        try:
            response = urllib.request.urlopen(url)
            xmlstring = re.sub(' xmlns="[^"]+"', '', response.read().decode(), count=1)
            
            e = xml.etree.ElementTree.fromstring(xmlstring)
        
            device = e.find('device')
            friendlyname = device.find('friendlyName').text
            manufacturer = device.find('manufacturer').text
            serviceList = device.find('serviceList')
            iconList = device.find('iconList')
            iconurl = ''
            isMezzmo = False
            
            if manufacturer != None and manufacturer == 'Conceiva Pty. Ltd.':
                iconurl = addon.getAddonInfo("path") + '/icon.png'   
                isMezzmo = True
            elif iconList != None:
                bestWidth = 0
                for icon in iconList.findall('icon'):
                    mimetype = icon.find('mimetype').text
                    width = icon.find('width').text
                    height = icon.find('height').text
                    width = int(width)
                    if width > bestWidth:
                        bestWidth = width
                        iconurl = icon.find('url').text
                        if iconurl.startswith('/'):
                            end = url.find('/', 8)
                            length = len(url)
                            
                            iconurl = url[:end-length] + iconurl
                        else:
                            end = url.rfind('/')
                            length = len(url)
                            
                            iconurl = url[:end-length] + '/' + iconurl
            else:
                iconurl = addon.getAddonInfo("path") + '/resources/media/otherserver.png'        
            
            if isMezzmo or onlyShowMezzmo == False:
                contenturl = ''
                for service in serviceList.findall('service'):
                    serviceId = service.find('serviceId')
                    
                    if serviceId.text == 'urn:upnp-org:serviceId:ContentDirectory':
                        contenturl = service.find('controlURL').text
                        if contenturl.startswith('/'):
                            end = url.find('/', 8)
                            length = len(url)
                            
                            contenturl = url[:end-length] + contenturl
                        else:
                            end = url.rfind('/')
                            length = len(url)
                            
                            contenturl = url[:end-length] + '/' + contenturl

                itemurl = build_url({'mode': 'server', 'contentdirectory': contenturl})   
                
                li = xbmcgui.ListItem(friendlyname)
                li.setArt({'thumb': iconurl, 'poster': iconurl, 'icon': iconurl, 'fanart': addon.getAddonInfo("path") + 'fanart.jpg'})
                xbmcplugin.addDirectoryItem(handle=addon_handle, url=itemurl, listitem=li, isFolder=True)
        except Exception as e:
            printexception()
            pass
    setViewMode('servers')
    xbmcplugin.endOfDirectory(addon_handle, updateListing=force )
    kodiCleanDB()                     # Call function to delete Kodi actor database if user enabled. 
    dbIndexes()
    
def build_url(query):
    return base_url + '?' + urllib.parse.urlencode(query)

    
def setViewMode(contentType):

    current_skin_name = xbmc.getSkinDir()
    
    if current_skin_name == 'skin.aeon.nox.5' or current_skin_name == 'skin.aeon.nox.silvo':
        aeon_nox_views = { 'List'       : 50  ,
                       'InfoWall'   : 51  ,
                       'Landscape'  : 52  ,
                       'ShowCase1'  : 53  ,
                       'ShowCase2'  : 54  ,
                       'TriPanel'   : 55  ,
                       'Posters'    : 56  ,
                       'Shift'      : 57  ,
                       'BannerWall' : 58  ,
                       'Logo'       : 59  ,
                       'Wall'       : 500 ,
                       'LowList'    : 501 ,
                       'Episode'    : 502 ,
                       'Wall'       : 503 ,
                       'BigList'    : 510 }
        
        view_mode = addon.getSetting(contentType + '_view_mode' + '_aeon')
        if view_mode != 'Default':
            selected_mode = aeon_nox_views[view_mode]
            xbmc.executebuiltin('Container.SetViewMode(' + str(selected_mode) + ')')
            
    elif current_skin_name == 'skin.aeon.madnox':
        aeon_nox_views = { 'List'       : 50  ,
                       'InfoWall'   : 51  ,
                       'Landscape'  : 503  ,
                       'ShowCase1'  : 501  ,
                       'ShowCase2'  : 501  ,
                       'TriPanel'   : 52  ,
                       'Posters'    : 510  ,
                       'Shift'      : 57  ,
                       'BannerWall' : 508  ,
                       'Logo'       : 59  ,
                       'Wall'       : 500 ,
                       'LowList'    : 501 ,
                       'Episode'    : 514 ,
                       'Wall'       : 500 ,
                       'BigList'    : 510 }
        
        view_mode = addon.getSetting(contentType + '_view_mode' + '_aeon')
        if view_mode != 'Default':
            selected_mode = aeon_nox_views[view_mode]
            xbmc.executebuiltin('Container.SetViewMode(' + str(selected_mode) + ')')
        
    elif current_skin_name == 'skin.estuary':
        estuary_views = { 'List'       : 50  ,
                       'InfoWall'   : 54  ,
                       'Landscape'  : 502  ,
                       'ShowCase1'  : 53  ,
                       'ShowCase2'  : 54  ,
                       'TriPanel'   : 50  ,
                       'Posters'    : 51  ,
                       'Shift'      : 52  ,
                       'BannerWall' : 502  ,
                       'Logo'       : 50  ,
                       'Wall'       : 500 ,
                       'LowList'    : 55 ,
                       'Episode'    : 50 ,
                       'Wall'       : 500 ,
                       'BigList'    : 501 }
        
        view_mode = addon.getSetting(contentType + '_view_mode' + '_estuary')
        if view_mode != 'Default':
        
            selected_mode = estuary_views[view_mode]
            xbmc.executebuiltin('Container.SetViewMode(' + str(selected_mode) + ')')

    elif addon.getSetting(contentType + '_view_mode') != "0":
       try:
           if addon.getSetting(contentType + '_view_mode') == "1": # List
               xbmc.executebuiltin('Container.SetViewMode(502)')
           elif addon.getSetting(contentType + '_view_mode') == "2": # Big List
               xbmc.executebuiltin('Container.SetViewMode(51)')
           elif addon.getSetting(contentType + '_view_mode') == "3": # Thumbnails
               xbmc.executebuiltin('Container.SetViewMode(500)')
           elif addon.getSetting(contentType + '_view_mode') == "4": # Poster Wrap
               xbmc.executebuiltin('Container.SetViewMode(501)')
           elif addon.getSetting(contentType + '_view_mode') == "5": # Fanart
               xbmc.executebuiltin('Container.SetViewMode(508)')
           elif addon.getSetting(contentType + '_view_mode') == "6":  # Media info
               xbmc.executebuiltin('Container.SetViewMode(504)')
           elif addon.getSetting(contentType + '_view_mode') == "7": # Media info 2
               xbmc.executebuiltin('Container.SetViewMode(503)')
           elif addon.getSetting(contentType + '_view_mode') == "8": # Media info 3
               xbmc.executebuiltin('Container.SetViewMode(515)')
       except:
           xbmc.log("SetViewMode Failed: "+addon.getSetting('_view_mode'))
           xbmc.log("Skin: "+xbmc.getSkinDir())


def handleBrowse(content, contenturl, objectID, parentID):
    contentType = 'movies'
    itemsleft = -1
    addon.setSetting('contenturl', contenturl)
    deleteTexturesCache(contenturl)   # Call function to delete textures cache if user enabled.  
    xbmc.log('Kodi version: ' + installed_version, xbmc.LOGNOTICE)
    try:
        while True:
            e = xml.etree.ElementTree.fromstring(content)
            
            body = e.find('.//{http://schemas.xmlsoap.org/soap/envelope/}Body')
            browseresponse = body.find('.//{urn:schemas-upnp-org:service:ContentDirectory:1}BrowseResponse')
            result = browseresponse.find('Result')
            NumberReturned = browseresponse.find('NumberReturned').text
            TotalMatches = browseresponse.find('TotalMatches').text
            
            if NumberReturned == 0:
                break; #sanity check
                
            if itemsleft == -1:
                itemsleft = int(TotalMatches)
            
            #elems = xml.etree.ElementTree.fromstring(result.text.encode('utf-8'))
            elems = xml.etree.ElementTree.fromstring(result.text)
            
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

                itemurl = build_url({'mode': 'server', 'parentID': objectID, 'objectID': containerid, 'contentdirectory': contenturl})        
                li = xbmcgui.ListItem(title)
                li.setArt({'banner': icon, 'poster': icon, 'icon': icon, 'fanart': addon.getAddonInfo("path") + 'fanart.jpg'})
                
                mediaClass_text = 'video'
                info = {
                        'plot': description_text,
                }
                li.setInfo(mediaClass_text, info)
                    
                searchargs = urllib.parse.urlencode({'mode': 'search', 'contentdirectory': contenturl, 'objectID': containerid})
                li.addContextMenuItems([ ('Refresh', 'Container.Refresh'), ('Go up', 'Action(ParentDir)'), ('Search', 'Container.Update( plugin://plugin.video.mezzmo?' + searchargs + ')') ])
                
                xbmcplugin.addDirectoryItem(handle=addon_handle, url=itemurl, listitem=li, isFolder=True)
                if parentID == '0':
                    contentType = 'top'
                else:
                    contentType = 'folders'
                
            for item in elems.findall('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}item'):
                title = item.find('.//{http://purl.org/dc/elements/1.1/}title').text
                itemid = item.get('id')
                icon = None
                albumartUri = item.find('.//{urn:schemas-upnp-org:metadata-1-0/upnp/}albumArtURI')
                if albumartUri != None:
                    icon = albumartUri.text + '.jpg'
                #xbmc.log('The current albumUri is: ' + str(albumartUri), xbmc.LOGNOTICE)
                res = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}res')
                subtitleurl = None
                duration_text = ''
                video_width = 0
                video_height = 0
                aspect = 0.0
                
                if res != None:
                    itemurl = res.text 
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
                        
                backdropurl = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}cvabackdrop')
                if backdropurl != None:
                    backdropurl = backdropurl.text
                
                li = xbmcgui.ListItem(title)
                li.setArt({'thumb': icon, 'poster': icon, 'icon': icon, 'fanart': backdropurl})
                if subtitleurl != None:
                    li.setSubtitles([subtitleurl])
                    
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
                    #artist_text = artist.text.encode('utf-8', 'ignore')
                    artist_text = artist.text
                    # writeActorsToDb(artist_text, imageSearchUrl) 

                actor_list = ''
                cast_dict = []    # Added cast & thumbnail display from Mezzmo server
                cast_dict_keys = ['name','thumbnail']
                actors = item.find('.//{urn:schemas-upnp-org:metadata-1-0/upnp/}artist')
                if actors != None:
                    actor_list = actors.text.replace(', Jr.' , ' Jr.').replace(', Sr.' , ' Sr.').split(',')
                    for a in actor_list:                  
                        actorSearchUrl = imageSearchUrl + "?imagesearch=" + a.lstrip().replace(" ","+")
                        #xbmc.log('search URL: ' + actorSearchUrl, xbmc.LOGNOTICE)  # uncomment for thumbnail debugging
                        new_record = [ a.strip() , actorSearchUrl]
                        cast_dict.append(dict(list(zip(cast_dict_keys, new_record))))

                creator_text = ''
                creator = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}creator')
                if creator != None:
                    creator_text = creator.text
                    
                lastplayed_text = ''
                lastplayed = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}lastplayed')
                if lastplayed != None:
                    lastplayed_text = lastplayed.text
                   
                tagline_text = ''
                tagline = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}tag_line')
                if tagline != None:
                    tagline_text = tagline.text
                    
                categories_text = 'movie'
                categories = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}categories')
                if categories != None and categories.text != None:
                    categories_text = categories.text
                    if categories_text == 'TV show':
                        categories_text = 'episode'
                        contentType = 'episodes'
                    elif categories_text == 'Movie':
                        categories_text = 'movie'
                        contentType = 'movies'
                        
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
                        
                if mediaClass_text == 'video':  
                    li.addContextMenuItems([ (addon.getLocalizedString(30347), 'Container.Refresh'), (addon.getLocalizedString(30346), 'Action(ParentDir)'), (addon.getLocalizedString(30348), 'Action(Info)') ])
                    
                    info = {
                        'duration': getSeconds(duration_text),
                        'genre': genre_text,
                        'year': release_year_text,
                        'title': title,
                        'plot': description_text,
                        'director': creator_text,
                        'tagline': tagline_text,
                        'writer': writer_text,
                        'cast': artist_text.split(','),
                        'artist': artist_text.split(','),
                        'rating': rating_val,
                        'code': imdb_text,
                        'mediatype': categories_text.split(',')[0],  # updated - Kodi can only accept 1 media type
                        'season': season_text,
                        'episode': episode_text,
                        'lastplayed': lastplayed_text,
                        'aired': aired_text,
                        'mpaa':content_rating_text,
                        'playcount':playcount,
                        'trailer':trailerurl,
                    }
                    li.setInfo(mediaClass_text, info)
                    li.setProperty('ResumeTime', dcmInfo_text)
                    li.setProperty('TotalTime', str(getSeconds(duration_text)))
                    video_info = {
                        'codec': video_codec_text,
                        'aspect': aspect,
                        'width': video_width,
                        'height': video_height,
                    }
                    li.addStreamInfo('video', video_info)
                    li.addStreamInfo('audio', {'codec': audio_codec_text, 'language': audio_lang, 'channels': int(audio_channels_text)})
                    li.addStreamInfo('subtitle', {'language': subtitle_lang})
                    if installed_version >= '17':       #  Update cast with thumbnail support in Kodi v17 and higher
                        li.setCast(cast_dict)                

                    tvcheckval = tvChecker(season_text, episode_text)          # Is TV show and user enabled Kodi DB adding
                    if installed_version >= '19' and addon.getSetting('kodiactor') == 'true' and tvcheckval == 1:  
                        mtitle = displayTitles(title) 
                        filekey = checkDBpath(itemurl, mtitle, playcount)      #  Check if file exists in Kodi DB
                        durationsecs = getSeconds(duration_text)               #  convert movie duration to seconds before passing
                        kodichange = addon.getSetting('kodichange')            #  Checks for change detection user setting
                        movieId = writeMovieToDb(filekey, mtitle, description_text, tagline_text, writer_text, creator_text, \
                        release_year_text, imageSearchUrl, durationsecs, genre_text, trailerurl, content_rating_text, icon,  \
                        kodichange)
                        if (artist != None and filekey > 0) or movieId == 999999:        #  Add actor information to new movie
                            writeActorsToDb(artist_text, movieId, imageSearchUrl, mtitle)
                        writeMovieStreams(filekey, video_codec_text, aspect, video_height, video_width, audio_codec_text, \
                        audio_channels_text, durationsecs, mtitle, kodichange, itemurl, icon)  #  Add / update movie stream info 
                        #xbmc.log('The movie name is: ' + mtitle.encode('utf-8'), xbmc.LOGNOTICE)

                            

                elif mediaClass_text == 'music':
                    li.addContextMenuItems([ (addon.getLocalizedString(30347), 'Container.Refresh'), (addon.getLocalizedString(30346), 'Action(ParentDir)') ])
                    info = {
                        'duration': getSeconds(duration_text),
                        'genre': genre_text,
                        'year': release_year_text,
                        'title': title,
                        'artist': artist_text.split(','),
                        'rating': rating_val,
                        'discnumber': season_text,
                        'tracknumber': episode_text,
                        'album': album_text,
                        'playcount':playcount,
                        'lastplayed': last_played_text,
                    }
                    li.setInfo(mediaClass_text, info)
                    contentType = 'songs'
                elif mediaClass_text == 'picture':
                    li.addContextMenuItems([ (addon.getLocalizedString(30347), 'Container.Refresh'), (addon.getLocalizedString(30346), 'Action(ParentDir)') ])
                    
                    info = {
                        'title': title,
                    }
                    li.setInfo(mediaClass_text, info)
                    contentType = 'files'
                 
                xbmcplugin.addDirectoryItem(handle=addon_handle, url=itemurl, listitem=li, isFolder=False)
            
            itemsleft = itemsleft - int(NumberReturned)
            if itemsleft == 0:
                break
                        
            # get the next items
            offset = int(TotalMatches) - itemsleft
            requestedCount = 1000
            if itemsleft < 1000:
                requestedCount = itemsleft
            
            pin = addon.getSetting('content_pin')   
            content = browse.Browse(contenturl, objectID, 'BrowseDirectChildren', offset, requestedCount, pin)
    except Exception as e:
        printexception()
        pass
    setViewMode(contentType)
    if contentType == 'top' or contentType == 'folders':
        contentType = ''
    xbmcplugin.setContent(addon_handle, contentType)
    xbmcplugin.endOfDirectory(addon_handle)


def handleSearch(content, contenturl, objectID, term):
    contentType = 'movies'
    itemsleft = -1
    addon.setSetting('contenturl', contenturl)
    deleteTexturesCache(contenturl)   # Call function to delete textures cache if user enabled. 
    
    try:
        while True:
            e = xml.etree.ElementTree.fromstring(content)
            
            body = e.find('.//{http://schemas.xmlsoap.org/soap/envelope/}Body')
            browseresponse = body.find('.//{urn:schemas-upnp-org:service:ContentDirectory:1}SearchResponse')
            result = browseresponse.find('Result')
            NumberReturned = browseresponse.find('NumberReturned').text
            TotalMatches = browseresponse.find('TotalMatches').text
            
            if NumberReturned == 0:
                break; #sanity check
                
            if itemsleft == -1:
                itemsleft = int(TotalMatches)
            
            elems = xml.etree.ElementTree.fromstring(result.text.encode('utf-8'))
               
            for item in elems.findall('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}item'):
                title = item.find('.//{http://purl.org/dc/elements/1.1/}title').text
                itemid = item.get('id')
                icon = None
                albumartUri = item.find('.//{urn:schemas-upnp-org:metadata-1-0/upnp/}albumArtURI')
                if albumartUri != None:
                    icon = albumartUri.text + '.jpg' 
                res = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}res')
                subtitleurl = None
                duration_text = ''
                video_width = 0
                video_height = 0
                aspect = 0.0
                
                if res != None:
                    itemurl = res.text 
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
                        
                backdropurl = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}cvabackdrop')
                if backdropurl != None:
                    backdropurl = backdropurl.text
                
                li = xbmcgui.ListItem(title)
                li.setArt({'thumb': icon, 'poster': icon, 'icon': icon, 'fanart': backdropurl})
                if subtitleurl != None:
                    li.setSubtitles([subtitleurl])

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
                    artist_text = artist.text

                actor_list = ''
                cast_dict = []        # Added cast & thumbnail display from Mezzmo server
                cast_dict_keys = ['name','thumbnail']
                actors = item.find('.//{urn:schemas-upnp-org:metadata-1-0/upnp/}artist')
                if actors != None:
                    #actor_list = actors.text.encode('utf-8', 'ignore').replace(', Jr.' , ' Jr.').replace(', Sr.' , ' Sr.').split(',')
                    actor_list = actors.text.replace(', Jr.' , ' Jr.').replace(', Sr.' , ' Sr.').split(',')
                    for a in actor_list:                 
                        actorSearchUrl = imageSearchUrl + "?imagesearch=" + a.lstrip().replace(" ","+")
                        #xbmc.log('search URL: ' + actorSearchUrl, xbmc.LOGNOTICE)  
                        new_record = [ a.strip() , actorSearchUrl]
                        cast_dict.append(dict(list(zip(cast_dict_keys, new_record))))                  

                creator_text = ''
                creator = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}creator')
                if creator != None:
                    creator_text = creator.text
                    
                lastplayed_text = ''
                lastplayed = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}lastplayed')
                if lastplayed != None:
                    lastplayed_text = lastplayed.text
                   
                tagline_text = ''
                tagline = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}tag_line')
                if tagline != None:
                    tagline_text = tagline.text
                    
                categories_text = 'movie'
                categories = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}categories')
                if categories != None and categories.text != None:
                    categories_text = categories.text
                    if categories_text == 'TV show':
                        categories_text = 'episode'
                        contentType = 'episodes'
                    elif categories_text == 'Movie':
                        categories_text = 'movie'
                        contentType = 'movies'
                        
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
                        
                if mediaClass_text == 'video':  
                    li.addContextMenuItems([ (addon.getLocalizedString(30347), 'Container.Refresh'), (addon.getLocalizedString(30346), 'Action(ParentDir)'), (addon.getLocalizedString(30348), 'Action(Info)') ])
                    
                    info = {
                        'duration': getSeconds(duration_text),
                        'genre': genre_text,
                        'year': release_year_text,
                        'title': title,
                        'plot': description_text,
                        'director': creator_text,
                        'tagline': tagline_text,
                        'writer': writer_text,
                        'cast': artist_text.split(','),
                        'artist': artist_text.split(','),
                        'rating': rating_val,
                        'code': imdb_text,
                        'mediatype': categories_text.split(',')[0],  # updated - Kodi can only accept 1 media type
                        'season': season_text,
                        'episode': episode_text,
                        'lastplayed': lastplayed_text,
                        'aired': aired_text,
                        'mpaa':content_rating_text,
                        'playcount':playcount,
                        'lastplayed': last_played_text,
                        'trailer':trailerurl,
                    }
                    li.setInfo(mediaClass_text, info)
                    li.setProperty('ResumeTime', dcmInfo_text)
                    li.setProperty('TotalTime', str(getSeconds(duration_text)))
                    video_info = {
                        'codec': video_codec_text,
                        'aspect': aspect,
                        'width': video_width,
                        'height': video_height,
                    }
                    li.addStreamInfo('video', video_info)
                    li.addStreamInfo('audio', {'codec': audio_codec_text, 'language': audio_lang, 'channels': int(audio_channels_text)})
                    li.addStreamInfo('subtitle', {'language': subtitle_lang})
                    if installed_version >= '19':         #  Update cast with thumbnail support in Kodi v17 and higher
                        li.setCast(cast_dict)  
                    tvcheckval = tvChecker(season_text, episode_text)    # Is TV show and user enabled Kodi DB adding
                    if installed_version >= '17' and addon.getSetting('kodiactor') == 'true' and tvcheckval == 1:  
                        mtitle = displayTitles(title) 
                        filekey = checkDBpath(itemurl, mtitle, playcount)      #  Check if file exists in Kodi DB
                        durationsecs = getSeconds(duration_text)               #  convert movie duration to seconds before passing
                        kodichange = addon.getSetting('kodichange')            #  Checks for change detection user setting
                        movieId = writeMovieToDb(filekey, mtitle, description_text, tagline_text, writer_text, creator_text, \
                        release_year_text, imageSearchUrl, durationsecs, genre_text, trailerurl, content_rating_text, icon,  \
                        kodichange)
                        if (artist != None and filekey > 0) or movieId == 999999:        #  Add actor information to new movie
                            writeActorsToDb(artist_text, movieId, imageSearchUrl, mtitle)
                        writeMovieStreams(filekey, video_codec_text, aspect, video_height, video_width, audio_codec_text, \
                        audio_channels_text, durationsecs, mtitle, kodichange, itemurl, icon)  #  Add / update movie stream info 
                        #xbmc.log('The movie name is: ' + mtitle.encode('utf-8'), xbmc.LOGNOTICE)
                      
                elif mediaClass_text == 'music':
                    li.addContextMenuItems([ (addon.getLocalizedString(30347), 'Container.Refresh'), (addon.getLocalizedString(30346), 'Action(ParentDir)') ])
                    info = {
                        'duration': getSeconds(duration_text),
                        'genre': genre_text,
                        'year': release_year_text,
                        'title': title,
                        'artist': artist_text.split(','),
                        'rating': rating_val,
                        'discnumber': season_text,
                        'tracknumber': episode_text,
                        'album': album_text,
                        'playcount':playcount,
                        'lastplayed': last_played_text,
                    }
                    li.setInfo(mediaClass_text, info)
                    contentType = 'songs'
                elif mediaClass_text == 'picture':
                    li.addContextMenuItems([ (addon.getLocalizedString(30347), 'Container.Refresh'), (addon.getLocalizedString(30346), 'Action(ParentDir)') ])
                    
                    info = {
                        'title': title,
                    }
                    li.setInfo(mediaClass_text, info)
                    contentType = 'files'
                 
                xbmcplugin.addDirectoryItem(handle=addon_handle, url=itemurl, listitem=li, isFolder=False)
            
            itemsleft = itemsleft - int(NumberReturned)
            if itemsleft == 0:
                break
                        
            # get the next items
            offset = int(TotalMatches) - itemsleft
            requestedCount = 1000
            if itemsleft < 1000:
                requestedCount = itemsleft
            
            pin = addon.getSetting('content_pin')   
            content = browse.Search(contenturl, objectID, term, offset, requestedCount, pin)
    except Exception as e:
        printexception()
        pass
    xbmcplugin.setContent(addon_handle, contentType)
    setViewMode(contentType)
    xbmcplugin.endOfDirectory(addon_handle)
    
    xbmc.executebuiltin("Dialog.Close(busydialog)")

def getUPnPClass():

    upnpClass = ''
    if addon.getSetting('search_video') == 'true':
        upnpClass = "upnp:class derivedfrom &quot;object.item.videoItem&quot;"

    if addon.getSetting('search_music') == 'true':
        if len(upnpClass) != 0:
            upnpClass += " or "

        upnpClass += "upnp:class derivedfrom &quot;object.item.audioItem&quot;"

    if addon.getSetting('search_photo') == 'true':
        if len(upnpClass) != 0:
            upnpClass += " or "
            
        upnpClass += "upnp:class derivedfrom &quot;object.item.imageItem&quot;"
    
    return upnpClass

def getSearchCriteria(term):

    searchCriteria = ""
    
    if addon.getSetting('search_title') == 'true':
        searchCriteria += "dc:title=&quot;" + term + "&quot;"

    if addon.getSetting('search_album') == 'true':
        if len(searchCriteria) != 0:
            searchCriteria += " or "

        searchCriteria += "upnp:album=&quot;" + term + "&quot;"

    if addon.getSetting('search_artist') == 'true':
        if len(searchCriteria) != 0:
            searchCriteria += " or "

        searchCriteria += "upnp:artist=&quot;" + term + "&quot;"

    if addon.getSetting('search_tagline') == 'true':
        if len(searchCriteria) != 0:
            searchCriteria += " or "

        searchCriteria += "dc:description=&quot;" + term + "&quot;"
    
    if addon.getSetting('search_description') == 'true':
        if len(searchCriteria) != 0:
            searchCriteria += " or "

        searchCriteria += "upnp:longDescription=&quot;" + term + "&quot;"
    
    if addon.getSetting('search_keywords') == 'true':
        if len(searchCriteria) != 0:
            searchCriteria += " or "

        searchCriteria += "keywords=&quot;" + term + "&quot;"

    if addon.getSetting('search_creator') == 'true':
        if len(searchCriteria) != 0:
            searchCriteria += " or "

        searchCriteria += "creator=&quot;" + term + "&quot;"

    return searchCriteria
    
def promptSearch():
    term = ''
    #search_window = search.PopupWindow()
    #search_window.doModal()
    #term = search_window.term
    #isCancelled = search_window.isCancelled
    #del search_window
    kb = xbmc.Keyboard('', 'Search')
    kb.setHeading('Enter Search text')
    kb.doModal()
    if (kb.isConfirmed()):
        term = kb.getText()
    if len(term) > 0:
        xbmc.executebuiltin("ActivateWindow(busydialog)")
        upnpClass = getUPnPClass()
        searchCriteria = getSearchCriteria(term)
        
        searchCriteria = "(" + searchCriteria + ") and (" + upnpClass + ")"
        
        url = args.get('contentdirectory', '')
        
        pin = addon.getSetting('content_pin')
        content = browse.Search(url[0], '0', searchCriteria, 0, 1000, pin)
        handleSearch(content, url[0], '0', searchCriteria)
    
mode = args.get('mode', 'none')

refresh = args.get('refresh', 'False')

if refresh[0] == 'True':
    listServers(True)
    
if mode[0] == 'serverlist':
    listServers(False)

elif mode[0] == 'server':
    url = args.get('contentdirectory', '')
    objectID = args.get('objectID', '0')
    parentID = args.get('parentID', '0')
    pin = addon.getSetting('content_pin')
    
    if parentID[0] == '0':
        import socket
        ip = ''
        try:
            ip = socket.gethostbyname(socket.gethostname())
        except Exception as e:
            xbmc.log("gethostbyname exception: " + str(e))
            pass
        contentrestriction.SetContentRestriction(url[0], ip, 'true', pin)
        
    content = browse.Browse(url[0], objectID[0], 'BrowseDirectChildren', 0, 1000, pin)
    handleBrowse(content, url[0], objectID[0], parentID[0])

elif mode[0] == 'search':
    promptSearch()
    
xbmcplugin.setPluginFanart(addon_handle, addon.getAddonInfo("path") + 'fanart.jpg', color2='0xFFFF3300')

def start():
    if mode == 'none':
        listServers(False)

