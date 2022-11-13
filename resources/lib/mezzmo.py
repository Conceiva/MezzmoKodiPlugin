import sys
import pickle
import xbmcgui
import xbmcplugin
import ssdp
import xbmcaddon
import urllib2
import urllib
import xml.etree.ElementTree
import re
import xml.etree.ElementTree as ET
import urlparse
import browse
import contentrestriction
import xbmc
import datetime
import time
import json
import os
import media
import sync
from server import updateServers, getContentURL, picDisplay, showSingle
from server import clearPictures, updatePictures, addServers, checkSync
from views import content_mapping, setViewMode
from generic import ghandleBrowse, gBrowse

addon = xbmcaddon.Addon()
base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])

addon_path = xbmcaddon.Addon().getAddonInfo("path")
addon_icon = addon_path + '/resources/icon.png'
addon_fanart = addon_path + '/resources/fanart.jpg'

installed_version = media.get_installedversion()   

def perfStats(TotalMatches, brtime, endtime, patime, srtime, ctitle, pobject):    # Log performance stats
    tduration = endtime - brtime
    sduration = (patime - brtime) + srtime
    pduration = tduration - sduration
    displayrate = int(TotalMatches) / tduration

    try:
        psfile = media.openNosyncDB()                                    # Open Perf Stats database
        xbmc.log('Mezzmo perfstats: ' + str(ctitle) + ' ' + str(pobject), xbmc.LOGDEBUG)
        currDate = datetime.datetime.now().strftime('%Y-%m-%d')
        currTime = datetime.datetime.now().strftime('%H:%M:%S')
        if ctitle != ".." and ctitle != "":                              # Do not save Go up and refresh actions
            sduration = '{:.2f}'.format(sduration)  + "s"
            pduration = '{:.2f}'.format(pduration)  + "s"
            tduration = '{:.2f}'.format(tduration)  + "s"
            displayrate = "{:.2f}".format(displayrate) + " i/s" 
            objects = psfile.execute('SELECT psPlaylist FROM mperfIndex WHERE psObject=?', (pobject,))
            objtuple = objects.fetchone() 
            if objtuple == None:                                         # Ensure objectId doesn't exist
                psfile.execute('INSERT into mperfIndex (psObject, psPlaylist) values (?, ?)', (pobject, ctitle))             
            else:
                ctitle = objtuple[0]       
            psfile.execute('INSERT into mperfStats (psDate, psTime, psPlaylist, psCount, pSrvTime, mSrvTime,   \
            psTTime, psDispRate) values (?, ?, ?, ?, ?, ?, ?, ?)', (currDate, currTime, ctitle, TotalMatches,  \
            pduration, sduration, tduration, displayrate))
                          
        psfile.commit()
        psfile.close()
    except:
        xbmc.log('Mezzmo there was a problem adding perfstats to the database: ', xbmc.LOGNOTICE)
        pass              
    
def message(msg):
    __addon__ = xbmcaddon.Addon()
    __addonname__ = __addon__.getAddonInfo('name')
 
 
    xbmcgui.Dialog().ok(__addonname__, str(msg))


def listServers(force):
    timeoutval = float(media.settings('ssdp_timeout'))
    contenturl = ''

    msgdialogprogress = xbmcgui.DialogProgress()
    dialogmsg = media.translate(30402)
    dialoghead = media.translate(30398)
    msgdialogprogress.create(dialoghead, dialogmsg)
    saved_servers = media.settings('saved_servers')
    if len(saved_servers) < 5 or saved_servers == 'none' or force:
        servers = ssdp.discover("urn:schemas-upnp-org:device:MediaServer:1", timeout=timeoutval)
        # save the servers for faster loading
        media.settings('saved_servers', pickle.dumps(servers))
    else:
        servers = pickle.loads(saved_servers)      
    
    onlyShowMezzmo = media.settings('only_mezzmo_servers') == 'true'

    itemurl = build_url({'mode': 'serverList', 'refresh': True})        
    li = xbmcgui.ListItem(addon.getLocalizedString(30347))
    li.setArt({'icon': addon_path + '/resources/media/refresh.png'})
   
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=itemurl, listitem=li, isFolder=True)

    itemurl = build_url({'mode': 'manual'})        
    li = xbmcgui.ListItem(addon.getLocalizedString(30447))
    li.setArt({'icon': addon_icon})

    xbmcplugin.addDirectoryItem(handle=addon_handle, url=itemurl, listitem=li, isFolder=True)

    srvcount = len(servers)
    addtlmsg = '  ' + str(srvcount) + '  uPNP servers discovered.'
    ddialogmsg = dialogmsg + addtlmsg
    msgdialogprogress.update(50, ddialogmsg)
    if force:
        xbmc.sleep(1000)
    a = 0

    mgenlog ='Mezzmo server search: ' + str(len(servers)) + ' uPNP servers found.'
    xbmc.log(mgenlog, xbmc.LOGNOTICE)
    media.mgenlogUpdate(mgenlog)
    for server in servers:
        try:
            url = server.location
        except:
            url = server.get('serverurl')           
        try:
            response = urllib2.urlopen(url, timeout=int(timeoutval))
            xmlstring = re.sub(' xmlns="[^"]+"', '', response.read(), count=1)
          
            e = xml.etree.ElementTree.fromstring(xmlstring)
            mgenlog = 'Mezzmo uPNP server url: ' + url[:48]  
            xbmc.log(mgenlog, xbmc.LOGNOTICE)
            media.mgenlogUpdate(mgenlog)   
            device = e.find('device')
            friendlyname = device.find('friendlyName').text
            manufacturer = device.find('manufacturer')
            if manufacturer != None:
                manufacturer = manufacturer.text
            else:
                manufacturer = 'None'
            modelnumber = device.find('modelNumber')
            if modelnumber != None:
                modelnumber = modelnumber.text
            else:
                modelnumber = 'None'
            udn = device.find('UDN')
            if udn != None:
                udn = udn.text
            else:
                udn = 'None'
            description = device.find('modelDescription')
            if description != None:
                description = description.text
            else:
                description = 'None'            
            serviceList = device.find('serviceList')
            iconList = device.find('iconList')
            iconurl = ''
            isMezzmo = False
            
            if manufacturer != None and manufacturer == 'Conceiva Pty. Ltd.':
                iconurl = addon_icon  
                isMezzmo = True
            elif iconList != None:
                bestWidth = 0
                for icon in iconList.findall('icon'):
                    mimetype = icon.find('mimetype').text
                    width = icon.find('width').text
                    height = icon.find('height').text
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
                iconurl = addon_path + '/resources/media/otherserver.png'        
            
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
                        elif 'http' not in contenturl:
                            end = url.rfind('/')
                            length = len(url)                            
                            contenturl = url[:end-length] + '/' + contenturl

                itemurl = build_url({'mode': 'server', 'contentdirectory': contenturl})   
                
                li = xbmcgui.ListItem(friendlyname, iconImage=iconurl)
                li.setArt({'thumb': iconurl, 'poster': iconurl, 'icon': iconurl, 'fanart': addon_fanart})
                xbmcplugin.addDirectoryItem(handle=addon_handle, url=itemurl, listitem=li, isFolder=True)
                updateServers(url, friendlyname, contenturl, manufacturer, modelnumber, iconurl, description, udn) 
        except urllib2.URLError, urllib2.HTTPError:    # Detect Server Issues
            mgenlog = 'Mezzmo uPNP server not responding: ' + url
            xbmc.log(mgenlog, xbmc.LOGNOTICE)
            media.mgenlogUpdate(mgenlog)  
            dialog_text = media.translate(30405) + url
            xbmcgui.Dialog().ok(media.translate(30404), dialog_text) 
            pass                  
        except Exception as e:
            media.printexception()
            pass
        a += 1
        percent = int(a / float(srvcount) * 50) + 50
        dialogmsg = str(a) + ' / ' + str(srvcount) + ' server completed.' 
        msgdialogprogress.update(percent, dialogmsg)
        if srvcount > 5:
            xbmc.sleep(200)
        else:
            xbmc.sleep(100)            
    msgdialogprogress.close() 
    setViewMode('servers')
    xbmcplugin.endOfDirectory(addon_handle, updateListing=force )
    if contenturl != None:
        media.kodiCleanDB(0)                    # Call function to delete Kodi actor database if user enabled.
        if media.settings('kodiclean') == 'Full Sync':
            syncpin = media.settings('content_pin')
            syncurl = checkSync()                         # Get server control URL
            if syncpin and syncurl != 'None':            
                sync.syncMezzmo(syncurl, syncpin, 15)     # Trigger resync process
            media.settings('kodiclean', 'Off')            # reset back to false after resync

    
def build_url(query):
    return base_url + '?' + urllib.urlencode(query)


def handleBrowse(content, contenturl, objectID, parentID):
    contentType = 'movies'
    itemsleft = -1 
    pitemsleft = -1
    global brtime, patime 
    srtime = 0  
    media.settings('contenturl', contenturl)
    koditv = media.settings('koditv')
    knative = media.settings('knative')
    nativeact = media.settings('nativeact')
    perflog = media.settings('perflog')
    musicvid = media.settings('musicvid')               # Check if musicvideo sync is enabled
    duplogs = media.settings('mdupelog')                # Check if Mezzmo duplicate logging is enabled
    synlogs = media.settings('kodisync')                # Check if Mezzmo background sync is enabled
    slideshow = media.settings('slideshow')             # Check if slideshow is enabled        
    kodichange = media.settings('kodichange')           # Checks for change detection user setting
    kodiactor = media.settings('kodiactor')             # Checks for actor info setting
    trcount = media.settings('trcount')                 # Checks multiple trailer setting
    menuitem1 = addon.getLocalizedString(30347)
    menuitem2 = addon.getLocalizedString(30346)
    menuitem3 = addon.getLocalizedString(30372)
    menuitem4 = addon.getLocalizedString(30373)
    menuitem5 = addon.getLocalizedString(30379)
    menuitem6 = addon.getLocalizedString(30380)
    menuitem7 = addon.getLocalizedString(30384)
    menuitem8 = addon.getLocalizedString(30412)
    menuitem9 = addon.getLocalizedString(30434)
    autostart = media.settings('autostart')
    sync.deleteTexturesCache(contenturl)                # Call function to delete textures cache if user enabled.  
    #xbmc.log('Kodi version: ' + installed_version, xbmc.LOGNOTICE)

    try:
        while True:
            e = xml.etree.ElementTree.fromstring(content)
            
            body = e.find('.//{http://schemas.xmlsoap.org/soap/envelope/}Body')
            browseresponse = body.find('.//{urn:schemas-upnp-org:service:ContentDirectory:1}BrowseResponse')
            result = browseresponse.find('Result')
            NumberReturned = browseresponse.find('NumberReturned').text
            TotalMatches = browseresponse.find('TotalMatches').text

            if int(NumberReturned) == 0:
                dialog_text = media.translate(30421) + '\n' + xbmc.getInfoLabel("ListItem.Label")
                xbmcgui.Dialog().ok(media.translate(30423), dialog_text)
                xbmc.executebuiltin('Action(ParentDir)')
                break; #sanity check
                
            if itemsleft == -1:
                itemsleft = int(TotalMatches)
            
            elems = xml.etree.ElementTree.fromstring(result.text.encode('utf-8'))
            picnotify = 0              
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

                itemurl = build_url({'mode': 'server', 'parentID': objectID, 'objectID': containerid,        \
                'contentdirectory': contenturl})        
                li = xbmcgui.ListItem(title, iconImage=icon)
                li.setArt({'banner': icon, 'poster': icon, 'icon': icon, 'fanart': addon_fanart})  
              
                mediaClass_text = 'video'
                info = {
                        'plot': description_text,
                }
                li.setInfo(mediaClass_text, info)
                    
                searchargs = urllib.urlencode({'mode': 'search', 'contentdirectory': contenturl,            \
                'objectID': containerid})
                
                itempath = xbmc.getInfoLabel("ListItem.FileNameAndPath ")
                autitle = xbmc.getInfoLabel("ListItem.Label")         #  Get title of selected playlist 
                if (autostart == '' or autostart == 'clear' or len(autostart) < 6):
                    li.addContextMenuItems([ (menuitem1, 'Container.Refresh'), (menuitem2, 'Action(ParentDir)'),    \
                    ('Search', 'Container.Update( plugin://plugin.video.mezzmo?' + searchargs + ')'),               \
                    (menuitem7, 'RunScript(%s, %s)' % ("plugin.video.mezzmo", "performance")), (menuitem5,          \
                    'RunScript(%s, %s, %s, %s)' % ("plugin.video.mezzmo", "auto", itempath, autitle)) ])
                elif len(autostart) > 6 :
                    li.addContextMenuItems([ (menuitem1, 'Container.Refresh'), (menuitem2, 'Action(ParentDir)'),    \
                    ('Search', 'Container.Update( plugin://plugin.video.mezzmo?' + searchargs + ')'),               \
                    (menuitem7, 'RunScript(%s, %s)' % ("plugin.video.mezzmo", "performance")), (menuitem6,          \
                    'RunScript(%s, %s, %s, %s)' % ("plugin.video.mezzmo", "auto", "clear", autitle)) ])

                if '###' not in title:                 
                    xbmcplugin.addDirectoryItem(handle=addon_handle, url=itemurl, listitem=li, isFolder=True)
                picnotify += 1
                if parentID == '0':
                    contentType = 'top'
                else:
                    contentType = 'folders'
                contentType = content_mapping(contentType)


            piclist = []
            clearPictures()  
            ctitle = xbmc.getInfoLabel("ListItem.Label")         #  Get title of selected playlist
            xbmc.log('Mezzmo content title: ' + str(ctitle) + ' ' + str(parentID) + ' ' + objectID +     \
            ' Content type: ' + contentType, xbmc.LOGDEBUG)            
            dbfile = media.openKodiDB()                          #  Open Kodi database
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
                        
                backdropurl = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}cvabackdrop')
                if backdropurl != None:
                    backdropurl = backdropurl.text
                    if (backdropurl [-4:]) !=  '.jpg': 
                        backdropurl  = backdropurl  + '.jpg'
                
                li = xbmcgui.ListItem(title, iconImage=icon)
                li.setArt({'thumb': icon, 'poster': icon, 'fanart': backdropurl})
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

                actor_list = ''
                cast_dict = []    # Added cast & thumbnail display from Mezzmo server
                cast_dict_keys = ['name','thumbnail']
                actors = item.find('.//{urn:schemas-upnp-org:metadata-1-0/upnp/}artist')
                if actors != None and imageSearchUrl != None:
                    actor_list = actors.text.encode('utf-8', 'ignore').replace(', Jr.' , ' Jr.').replace(', Sr.' , ' Sr.').split(',')
                    for a in actor_list:                  
                        actorSearchUrl = imageSearchUrl + "?imagesearch=" + a.lstrip().replace(" ","+")
                        #xbmc.log('search URL: ' + actorSearchUrl, xbmc.LOGNOTICE)  # uncomment for thumbnail debugging
                        new_record = [ a.strip() , actorSearchUrl]
                        cast_dict.append(dict(zip(cast_dict_keys, new_record)))

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

                tags_text = ''
                tags = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}keywords')
                if tags != None:
                    tags_text = tags.text
                    
                categories_text = 'movie'
                categories = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}categories')
                if categories != None and categories.text != None:
                    categories_text = categories.text 
                    xbmc.log('Mezzmo categories_text: ' + str(categories_text), xbmc.LOGDEBUG)
                    if album_text:
                        movieset = album_text
                    else:
                        movieset =  album_text = ''                      

                    if 'tv show' in categories_text.lower():
                        categories_text = 'episode'
                        contentType = 'episodes'
                        showtitle = album_text
                    elif 'movie' in categories_text.lower():
                        categories_text = 'movie'
                        contentType = 'movies'
                        showtitle = title
                    elif 'music video' in categories_text.lower():
                        categories_text = 'musicvideo'
                        contentType = 'musicvideos'
                        showtitle = title
                    else:
                        categories_text = 'video'
                        contentType = 'videos'
                        showtitle = title
                else:
                    movieset = album_text = ''
                    categories_text = 'video'
                    contentType = 'videos'
                    showtitle = title

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

                moviedb_text = ''
                moviedb = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}the_moviedb_id')
                if moviedb != None:
                    moviedb_text = moviedb.text

                tvdb_text = ''
                tvdb = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}tvdb_id')
                if tvdb != None:
                    tvdb_text = tvdb.text
                
                dcmInfo_text = '0'
                dcmInfo = item.find('.//{http://www.sec.co.kr/}dcmInfo')
                if dcmInfo != None:
                    dcmInfo_text = dcmInfo.text
                    valPos = dcmInfo_text.find('BM=') + 3
                    dcmInfo_text = dcmInfo_text[valPos:]
              
                rating_val = ''
                rating = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}rating')
                if rating != None:
                    rating_val = rating.text
                    rating_valf = float(rating_val) * 2
                    rating_val = str(rating_valf) #kodi ratings are out of 10, Mezzmo is out of 5
                
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
                        mediaClass_text = 'pictures'

                durationsecs = sync.getSeconds(duration_text)                           #  convert movie duration to seconds                     
                if mediaClass_text == 'video' and validf == 1:    
                    mtitle = media.displayTitles(title)					#  Normalize title
                    pctitle = '"' + mtitle.encode('utf-8','ignore')  + '"'  		#  Handle commas
                    pcseries = '"' + album_text.encode('utf-8','ignore') + '"'          #  Handle commas
                    if int(trcount) > 0 and trailerurl != None:
                        if playcount == 0:
                            li.addContextMenuItems([ (menuitem1, 'Container.Refresh'), (menuitem2, 'Action(ParentDir)'),        \
                            (menuitem3, 'RunScript(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)' % ("plugin.video.mezzmo", "count",  \
                            pctitle, itemurl, season_text, episode_text, playcount, pcseries, "video", contenturl)), (menuitem9,\
                            'RunScript(%s, %s, %s, %s, %s)' % ("plugin.video.mezzmo", "trailer", pctitle, trcount, icon ))])
                        elif playcount > 0:
                            li.addContextMenuItems([ (menuitem1, 'Container.Refresh'), (menuitem2, 'Action(ParentDir)'),        \
                            (menuitem4, 'RunScript(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)' % ("plugin.video.mezzmo", "count",  \
                            pctitle, itemurl, season_text, episode_text, playcount, pcseries, "video", contenturl)), (menuitem9,\
                            'RunScript(%s, %s, %s, %s, %s)' % ("plugin.video.mezzmo", "trailer", pctitle, trcount, icon)) ])       
                    else:  
                        if playcount == 0:
                            li.addContextMenuItems([ (menuitem1, 'Container.Refresh'), (menuitem2, 'Action(ParentDir)'),        \
                            (menuitem3, 'RunScript(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)' % ("plugin.video.mezzmo", "count",  \
                            pctitle, itemurl, season_text, episode_text, playcount, pcseries, "video", contenturl)) ])
                        elif playcount > 0:
                            li.addContextMenuItems([ (menuitem1, 'Container.Refresh'), (menuitem2, 'Action(ParentDir)'),        \
                            (menuitem4, 'RunScript(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)' % ("plugin.video.mezzmo", "count",  \
                            pctitle, itemurl, season_text, episode_text, playcount, pcseries, "video", contenturl)) ])       

                    info = {
                        'duration': durationsecs,
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
                        'imdbnumber': imdb_text,
                        'mediatype': categories_text,
                        'season': season_text,
                        'episode': episode_text,
                        'lastplayed': last_played_text,
                        'aired': release_date_text,
                        'mpaa':content_rating_text,
                        'studio':production_company_text,
                        'playcount':playcount,
                        'trailer':trailerurl,
                        'tvshowtitle':showtitle,
                        'dateadded':date_added_text,
                    }
                    li.setInfo(mediaClass_text, info)
                    li.setProperty('ResumeTime', dcmInfo_text)
                    li.setProperty('TotalTime', str(durationsecs))
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
                    tvcheckval = media.tvChecker(season_text, episode_text, koditv, mtitle, categories)  # Check if Ok to add
                    if installed_version >= '17' and kodiactor == 'true' and tvcheckval[0] == 1:  
                        pathcheck = media.getPath(itemurl)                  #  Get path string for media file
                        serverid = media.getMServer(itemurl)                #  Get Mezzmo server id
                        filekey = media.checkDBpath(itemurl, mtitle, playcount, dbfile, pathcheck, serverid,           \
                        season_text, episode_text, album_text, last_played_text, date_added_text, 'false', koditv,     \
                        categories_text, knative, musicvid)
                        #xbmc.log('Mezzmo filekey is: ' + str(filekey), xbmc.LOGNOTICE) 
                        showId = 0                                          #  Set default 
                        if filekey[4] == 1:
                            showId = media.checkTVShow(filekey, album_text, genre_text, dbfile, content_rating_text,    \
                            production_company_text, icon, backdropurl)
                            mediaId = media.writeEpisodeToDb(filekey, mtitle, description_text, tagline_text,           \
                            writer_text, creator_text, aired_text, rating_val, durationsecs, genre_text, trailerurl,    \
                            content_rating_text, icon, kodichange, backdropurl, dbfile, production_company_text,        \
                            sort_title_text, season_text, episode_text, showId, 'false', itemurl, imdb_text, tags_text)
                        elif filekey[4] == 2:
                            mediaId = media.writeMusicVToDb(filekey, mtitle, description_text, tagline_text, writer_text, \
                            creator_text, release_date_text, rating_val, durationsecs, genre_text, trailerurl,            \
                            content_rating_text, icon, kodichange, backdropurl, dbfile, production_company_text,          \
                            sort_title_text, 'false', itemurl, imdb_text, tags_text, knative, movieset, episode_text,     \
                            artist_text)   
                        else:  
                            mediaId = media.writeMovieToDb(filekey, mtitle, description_text, tagline_text, writer_text, \
                            creator_text, release_date_text, rating_val, durationsecs, genre_text, trailerurl,           \
                            content_rating_text, icon, kodichange, backdropurl, dbfile, production_company_text,         \
                            sort_title_text, 'false', itemurl, imdb_text, tags_text, knative, movieset)
                        if (artist != None and filekey[0] > 0) or mediaId == 999999: #  Add actor information to new movie
                            media.writeActorsToDb(artist_text, mediaId, imageSearchUrl, mtitle, dbfile, filekey, 
                            nativeact, showId)
                        media.writeMovieStreams(filekey, video_codec_text, aspect, video_height, video_width,        \
                        audio_codec_text, audio_channels_text, audio_lang, durationsecs, mtitle, kodichange, itemurl,\
                        icon, backdropurl, dbfile, pathcheck, 'false', knative)      # Update movie stream info 
                        xbmc.log('The movie name is: ' + mtitle.encode('utf-8'), xbmc.LOGDEBUG)
                                       
                elif mediaClass_text == 'music':
                    mtitle = media.displayTitles(title)					#  Normalize title
                    pctitle = '"' + mtitle.encode('utf-8','ignore')  + '"'  		#  Handle commas
                    pcseries = '"' + album_text.encode('utf-8','ignore') + '"'          #  Handle commas
                    offsetmenu = 'Resume from ' + time.strftime("%H:%M:%S", time.gmtime(int(dcmInfo_text)))
                    if int(dcmInfo_text) > 0 and playcount == 0:
                        li.addContextMenuItems([ (menuitem1, 'Container.Refresh'), (menuitem2, 'Action(ParentDir)'),       \
                        (menuitem3, 'RunScript(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)' % ("plugin.video.mezzmo", "count", \
                        pctitle, itemurl, season_text, episode_text, playcount, pcseries, 'audiom', contenturl)),          \
                        (offsetmenu, 'RunScript(%s, %s, %s, %s, %s, %s, %s, %s)' % ("plugin.video.mezzmo", "playm",        \
                        itemurl, li, title, icon, backdropurl, dcmInfo_text)) ])
                    elif int(dcmInfo_text) > 0 and playcount > 0:
                        li.addContextMenuItems([ (menuitem1, 'Container.Refresh'), (menuitem2, 'Action(ParentDir)'),       \
                        (menuitem4, 'RunScript(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)' % ("plugin.video.mezzmo", "count", \
                        pctitle, itemurl, season_text, episode_text, playcount, pcseries, 'audiom', contenturl)),          \
                        (offsetmenu, 'RunScript(%s, %s, %s, %s, %s, %s, %s, %s)' % ("plugin.video.mezzmo", "playm",        \
                        itemurl, li, title, icon, backdropurl, dcmInfo_text)),  ])
                    elif int(dcmInfo_text) == 0 and playcount > 0:
                        li.addContextMenuItems([ (menuitem1, 'Container.Refresh'), (menuitem2, 'Action(ParentDir)'),       \
                        (menuitem4, 'RunScript(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)' % ("plugin.video.mezzmo", "count", \
                        pctitle, itemurl, season_text, episode_text, playcount, pcseries, 'audiom', contenturl)) ])
                    elif int(dcmInfo_text) == 0 and playcount == 0:
                        li.addContextMenuItems([ (menuitem1, 'Container.Refresh'), (menuitem2, 'Action(ParentDir)'),       \
                        (menuitem3, 'RunScript(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)' % ("plugin.video.mezzmo", "count", \
                         pctitle, itemurl, season_text, episode_text, playcount, pcseries, 'audiom', contenturl)) ])   
              
                    info = {
                        'duration': durationsecs,
                        'genre': genre_text,
                        'year': release_year_text,
                        'title': title,
                        'artist': artist_text.split(','),
                        'rating': rating_val,
                        'discnumber': season_text,
                        'mediatype': 'song',
                        #'dbid': '5',
                        'tracknumber': episode_text,
                        'album': album_text,
                        'playcount': playcount,
                        'lastplayed': last_played_text,
                    }
                    mcomment = media.mComment(info, duration_text, offsetmenu[12:])
                    info.update(comment = mcomment)
                    li.setInfo(mediaClass_text, info)
                    validf = 1	     #  Set valid file info flag
                    contentType = 'songs'

                elif mediaClass_text == 'pictures':
                    li.addContextMenuItems([ (menuitem1, 'Container.Refresh'), (menuitem2, 'Action(ParentDir)'), \
                    (menuitem8, 'RunScript(%s, %s)' % ("plugin.video.mezzmo", "pictures")) ])                    
                    info = {
                        'title': title,
                    }
                    li.setInfo(mediaClass_text, info)
                    validf = 1	     #  Set valid file info flag
                    contentType = 'files'
                    picnotify += 1
                    itemdict = {
                        'title': title,
                         'url': itemurl,
                    }
                    piclist.append(itemdict)
                    if picnotify == int(NumberReturned):                   # Update picture DB
                        updatePictures(piclist)
                        if slideshow == 'true':                            # Slideshow display prompt
                            picDisplay()
                    itemurl = build_url({'mode': 'picture', 'itemurl': itemurl})
                if validf == 1: 
                    xbmcplugin.addDirectoryItem(handle=addon_handle, url=itemurl, listitem=li, isFolder=False)
                    #xbmc.log('Mezzmo item URL is: ' + str(itemurl), xbmc.LOGNOTICE)
                else:
                    dialog_text = "Video file:  " + title.encode('utf-8') + " is invalid."
                    dialog_text2 = "Check Mezzmo video properties for this file."
                    xbmcgui.Dialog().ok("Mezzmo", dialog_text, dialog_text2)
            
            itemsleft = itemsleft - int(NumberReturned)
            xbmc.log('Mezzmo items left: ' + str(itemsleft), xbmc.LOGDEBUG) 
            dbfile.commit()                #  Commit writes

            if itemsleft == 0:
                dbfile.commit()
                dbfile.close()             #  Final commit writes and close Kodi database
                if int(TotalMatches) > 49 and perflog == "true":
                    endtime = time.time()
                    perfStats(TotalMatches, brtime, endtime, patime, srtime, ctitle, objectID)
                    xbmc.log('Mezzmo perfstats: ' + str(ctitle) + ' ' + str(parentID), xbmc.LOGDEBUG) 
                break

            if pitemsleft == itemsleft:    #  Detect items left not incrementing 
                dbfile.commit()
                dbfile.close()             #  Final commit writes and close Kodi database
                mgenlog ='Mezzmo items not displayed: ' + str(pitemsleft)
                xbmc.log(mgenlog, xbmc.LOGNOTICE)
                media.mgenlogUpdate(mgenlog)
                if int(TotalMatches) > 49 and perflog == "true":
                    endtime = time.time()
                    perfStats(TotalMatches, brtime, endtime, patime, srtime, ctitle, objectID)
                    xbmc.log('Mezzmo perfstats: ' + str(ctitle) + ' ' + str(parentID), xbmc.LOGDEBUG)
                break
            else:
                pitemsleft = itemsleft            
                        
            # get the next items
            offset = int(TotalMatches) - itemsleft
            requestedCount = 1000
            if itemsleft < 1000:
                requestedCount = itemsleft
            
            pin = media.settings('content_pin')
            brtime2 = time.time()                       #  Additional browse begin time   
            content = browse.Browse(contenturl, objectID, 'BrowseDirectChildren', offset, requestedCount, pin)
            srtime = srtime + (time.time() - brtime2)   #  Calculate total server time
    except Exception as e:
        media.printexception()
        pass
    setViewMode(contentType)
    if contentType == 'top' or contentType == 'folders':
        contentType = ''
    xbmcplugin.setContent(addon_handle, contentType)
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_DATE)
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_TITLE_IGNORE_THE)
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_GENRE)
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_DURATION)
    xbmcplugin.endOfDirectory(addon_handle)


def handleSearch(content, contenturl, objectID, term):
    contentType = 'movies'
    itemsleft = -1
    pitemsleft = -1
    media.settings('contenturl', contenturl)
    koditv = media.settings('koditv')
    knative = media.settings('knative')
    nativeact = media.settings('nativeact')
    musicvid = media.settings('musicvid')               # Check if musicvideo sync is enabled
    trcount = media.settings('trcount')                 # Checks multiple trailer setting
    menuitem1 = addon.getLocalizedString(30347)
    menuitem2 = addon.getLocalizedString(30346)
    menuitem9 = addon.getLocalizedString(30434)
    kodichange = media.settings('kodichange')           # Checks for change detection user setting
    kodiactor = media.settings('kodiactor')             # Checks for actor info setting    
    sync.deleteTexturesCache(contenturl)                # Call function to delete textures cache if user enabled. 
    
    try:
        while True:
            e = xml.etree.ElementTree.fromstring(content)
            
            body = e.find('.//{http://schemas.xmlsoap.org/soap/envelope/}Body')
            browseresponse = body.find('.//{urn:schemas-upnp-org:service:ContentDirectory:1}SearchResponse')
            result = browseresponse.find('Result')
            NumberReturned = browseresponse.find('NumberReturned').text
            TotalMatches = browseresponse.find('TotalMatches').text
        
            if int(NumberReturned) == 0:
                dialog_text = media.translate(30414)
                xbmcgui.Dialog().ok(media.translate(30420), dialog_text)
                xbmc.executebuiltin('Action(ParentDir)')
                break; #sanity check
                
            if itemsleft == -1:
                itemsleft = int(TotalMatches)
            
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
                        xbmc.log('Handle search initial icon is: ' + icon, xbmc.LOGDEBUG)  

                itemurl = build_url({'mode': 'server', 'parentID': objectID, 'objectID': containerid, 'contentdirectory': contenturl})        
                li = xbmcgui.ListItem(title, iconImage=icon)
                li.setArt({'banner': icon, 'poster': icon, 'fanart': addon_fanart})
                
                mediaClass_text = 'video'
                info = {
                        'plot': description_text,
                }
                li.setInfo(mediaClass_text, info)
                    
                searchargs = urllib.urlencode({'mode': 'search', 'contentdirectory': contenturl, 'objectID': containerid})
                li.addContextMenuItems([ ('Refresh', 'Container.Refresh'), ('Go up', 'Action(ParentDir)'), ('Search', 'Container.Update( plugin://plugin.video.mezzmo?' + searchargs + ')') ])
                
                xbmcplugin.addDirectoryItem(handle=addon_handle, url=itemurl, listitem=li, isFolder=True)
                if parentID == '0':
                    contentType = 'top'
                else:
                    contentType = 'folders'
                
            dbfile = media.openKodiDB()   
            for item in elems.findall('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}item'):
                title = item.find('.//{http://purl.org/dc/elements/1.1/}title').text
                itemid = item.get('id')
                icon = None
                albumartUri = item.find('.//{urn:schemas-upnp-org:metadata-1-0/upnp/}albumArtURI')
                if albumartUri != None:
                    icon = albumartUri.text  
                    if (icon[-4:]) !=  '.jpg': 
                        icon = icon + '.jpg'
                        xbmc.log('Handle search second icon is: ' + icon, xbmc.LOGDEBUG)    

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
                        
                backdropurl = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}cvabackdrop')
                if backdropurl != None:
                    backdropurl = backdropurl.text
                    if (backdropurl [-4:]) !=  '.jpg': 
                        backdropurl  = backdropurl  + '.jpg'
                
                li = xbmcgui.ListItem(title, iconImage=icon)
                li.setArt({'thumb': icon, 'poster': icon, 'fanart': backdropurl})
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

                actor_list = ''
                cast_dict = []    # Added cast & thumbnail display from Mezzmo server
                cast_dict_keys = ['name','thumbnail']
                actors = item.find('.//{urn:schemas-upnp-org:metadata-1-0/upnp/}artist')
                if actors != None and imageSearchUrl != None:
                    actor_list = actors.text.encode('utf-8', 'ignore').replace(', Jr.' , ' Jr.').replace(', Sr.' , ' Sr.').split(',')
                    for a in actor_list:                  
                        actorSearchUrl = imageSearchUrl + "?imagesearch=" + a.lstrip().replace(" ","+")
                        #xbmc.log('search URL: ' + actorSearchUrl, xbmc.LOGNOTICE)  # uncomment for thumbnail debugging
                        new_record = [ a.strip() , actorSearchUrl]
                        cast_dict.append(dict(zip(cast_dict_keys, new_record)))

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

                tags_text = ''
                tags = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}keywords')
                if tags != None:
                    tags_text = tags.text
                    
                categories_text = 'movie'
                categories = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}categories')
                if categories != None and categories.text != None:
                    categories_text = categories.text 
                    xbmc.log('Mezzmo categories_text: ' + str(categories_text), xbmc.LOGDEBUG)
                    if album_text:
                        movieset = album_text
                    else:
                        movieset =  album_text = ''                      

                    if 'tv show' in categories_text.lower():
                        categories_text = 'episode'
                        contentType = 'episodes'
                        showtitle = album_text
                    elif 'movie' in categories_text.lower():
                        categories_text = 'movie'
                        contentType = 'movies'
                        showtitle = title
                    elif 'music video' in categories_text.lower():
                        categories_text = 'musicvideo'
                        contentType = 'musicvideos'
                        showtitle = title
                    else:
                        categories_text = 'video'
                        contentType = 'videos'
                        showtitle = title
                else:
                    movieset = album_text = ''
                    categories_text = 'video'
                    contentType = 'videos'
                    showtitle = title
                        
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

                moviedb_text = ''
                moviedb = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}the_moviedb_id')
                if moviedb != None:
                    moviedb_text = moviedb.text

                tvdb_text = ''
                tvdb = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}tvdb_id')
                if tvdb != None:
                    tvdb_text = tvdb.text
                
                dcmInfo_text = '0'
                dcmInfo = item.find('.//{http://www.sec.co.kr/}dcmInfo')
                if dcmInfo != None:
                    dcmInfo_text = dcmInfo.text
                    valPos = dcmInfo_text.find('BM=') + 3
                    dcmInfo_text = dcmInfo_text[valPos:]
              
                rating_val = ''
                rating = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}rating')
                if rating != None:
                    rating_val = rating.text
                    rating_valf = float(rating_val) * 2
                    rating_val = str(rating_valf) #kodi ratings are out of 10, Mezzmo is out of 5

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

                durationsecs = sync.getSeconds(duration_text)                           #  convert movie duration to seconds  
                if mediaClass_text == 'video' and validf == 1:
                    mtitle = media.displayTitles(title)					#  Normalize title
                    pctitle = '"' + mtitle.encode('utf-8','ignore')  + '"'  		#  Handle commas
                    if int(trcount) > 0 and trailerurl != None:        
                        li.addContextMenuItems([ (menuitem1, 'Container.Refresh'), (menuitem2, 'Action(ParentDir)'),        \
                        (addon.getLocalizedString(30348), 'Action(Info)'), (menuitem9, 'RunScript(%s, %s, %s, %s, %s)'      \
                        % ("plugin.video.mezzmo", "trailer", pctitle, trcount, icon)) ])  
                    else:                              
                        li.addContextMenuItems([ (menuitem1, 'Container.Refresh'), (menuitem2, 'Action(ParentDir)'),        \
                        (addon.getLocalizedString(30348), 'Action(Info)') ])    
       
                    info = {
                        'duration': durationsecs,
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
                        'imdbnumber': imdb_text,
                        'mediatype': categories_text,
                        'season': season_text,
                        'episode': episode_text,
                        'lastplayed': last_played_text,
                        'aired': aired_text,
                        'mpaa':content_rating_text,
                        'studio':production_company_text,
                        'playcount':playcount,
                        'trailer':trailerurl,
                        'tvshowtitle':showtitle,
                        'dateadded':date_added_text,
                    }
                    li.setInfo(mediaClass_text, info)
                    li.setProperty('ResumeTime', dcmInfo_text)
                    li.setProperty('TotalTime', str(durationsecs))
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
                    mtitle = media.displayTitles(title) 
                    tvcheckval = media.tvChecker(season_text, episode_text, koditv, mtitle, categories)  # Check if Ok to add
                    if installed_version >= '17' and kodiactor == 'true' and tvcheckval[0] == 1:  
                        pathcheck = media.getPath(itemurl)                  #  Get path string for media file
                        serverid = media.getMServer(itemurl)                #  Get Mezzmo server id
                        filekey = media.checkDBpath(itemurl, mtitle, playcount, dbfile, pathcheck, serverid,           \
                        season_text, episode_text, album_text, last_played_text, date_added_text, 'false', koditv,     \
                        categories_text, knative, musicvid)
                        #xbmc.log('Mezzmo filekey is: ' + str(filekey), xbmc.LOGNOTICE) 
                        showId = 0                                          #  Set default 
                        if filekey[4] == 1:
                            showId = media.checkTVShow(filekey, album_text, genre_text, dbfile, content_rating_text,    \
                            production_company_text, icon, backdropurl)
                            mediaId = media.writeEpisodeToDb(filekey, mtitle, description_text, tagline_text,           \
                            writer_text, creator_text, aired_text, rating_val, durationsecs, genre_text, trailerurl,    \
                            content_rating_text, icon, kodichange, backdropurl, dbfile, production_company_text,        \
                            sort_title_text, season_text, episode_text, showId, 'false', itemurl, imdb_text, tags_text)
                        elif filekey[4] == 2:
                            mediaId = media.writeMusicVToDb(filekey, mtitle, description_text, tagline_text, writer_text, \
                            creator_text, release_date_text, rating_val, durationsecs, genre_text, trailerurl,            \
                            content_rating_text, icon, kodichange, backdropurl, dbfile, production_company_text,          \
                            sort_title_text, 'false', itemurl, imdb_text, tags_text, knative, movieset, episode_text,     \
                            artist_text)   
                        else:  
                            mediaId = media.writeMovieToDb(filekey, mtitle, description_text, tagline_text, writer_text, \
                            creator_text, release_date_text, rating_val, durationsecs, genre_text, trailerurl,           \
                            content_rating_text, icon, kodichange, backdropurl, dbfile, production_company_text,         \
                            sort_title_text, 'false', itemurl, imdb_text, tags_text, knative, movieset)
                        if (artist != None and filekey[0] > 0) or mediaId == 999999: #  Add actor information to new movie
                            media.writeActorsToDb(artist_text, mediaId, imageSearchUrl, mtitle, dbfile, filekey, 
                            nativeact, showId)
                        media.writeMovieStreams(filekey, video_codec_text, aspect, video_height, video_width,        \
                        audio_codec_text, audio_channels_text, audio_lang, durationsecs, mtitle, kodichange, itemurl,\
                        icon, backdropurl, dbfile, pathcheck, 'false', knative)      # Update movie stream info 
                        #xbmc.log('The movie name is: ' + mtitle.encode('utf-8'), xbmc.LOGNOTICE) 
                        #dbfile.commit()
                        #dbfile.close()  
                          
                elif mediaClass_text == 'music':
                    offsetmenu = 'Play from ' + time.strftime("%H:%M:%S", time.gmtime(int(dcmInfo_text)))
                    if int(dcmInfo_text) > 0:
                        li.addContextMenuItems([ (menuitem1, 'Container.Refresh'), (menuitem2, 'Action(ParentDir)'),     \
                        (offsetmenu, 'RunScript(%s, %s, %s, %s, %s, %s, %s, %s)' % ("plugin.video.mezzmo", "playm",      \
                        itemurl, li, title, icon, backdropurl, dcmInfo_text)) ])
                    else:
                        li.addContextMenuItems([ (menuitem1, 'Container.Refresh'), (menuitem2, 'Action(ParentDir)') ])    

                    info = {
                        'duration': durationsecs,
                        'genre': genre_text,
                        'year': release_year_text,
                        'title': title,
                        'artist': artist_text.split(','),
                        'rating': rating_val,
                        'discnumber': season_text,
                        'mediatype': 'song',
                        'tracknumber': episode_text,
                        'album': album_text,
                        'playcount':playcount,
                        'lastplayed': last_played_text,
                    }
                    mcomment = media.mComment(info, duration_text, offsetmenu[12:])
                    info.update(comment = mcomment)
                    li.setInfo(mediaClass_text, info)
                    validf = 1	     #  Set valid file info flag
                    contentType = 'songs'

                elif mediaClass_text == 'picture':
                    li.addContextMenuItems([ (menuitem1, 'Container.Refresh'), (menuitem2, 'Action(ParentDir)') ])                    
                    info = {
                        'title': title,
                    }
                    li.setInfo(mediaClass_text, info)
                    validf = 1	     #  Set valid file info flag
                    contentType = 'files'
                    itemurl = build_url({'mode': 'picture', 'itemurl': itemurl})
                 
                if validf == 1:   
                    xbmcplugin.addDirectoryItem(handle=addon_handle, url=itemurl, listitem=li, isFolder=False)
            
            itemsleft = itemsleft - int(NumberReturned)
            if itemsleft == 0:
                dbfile.commit()
                dbfile.close()             #  Final commit writes and close Kodi database
                break             

            if pitemsleft == itemsleft:    #  Detect items left not incrementing 
                dbfile.commit()
                dbfile.close()             #  Final commit writes and close Kodi database 
                mgenlog ='Mezzmo items not displayed: ' + str(pitemsleft)
                xbmc.log(mgenlog, xbmc.LOGNOTICE)
                media.mgenlogUpdate(mgenlog) 
                break
            else:
                pitemsleft = itemsleft            
            
            # get the next items
            offset = int(TotalMatches) - itemsleft
            requestedCount = 1000
            if itemsleft < 1000:
                requestedCount = itemsleft
            
            pin = media.settings('content_pin')   
            content = browse.Search(contenturl, objectID, term, offset, requestedCount, pin)
    except Exception as e:
        media.printexception()
        pass
    xbmcplugin.setContent(addon_handle, contentType)
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_DATE)
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_TITLE_IGNORE_THE)
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_GENRE)
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_DURATION)
    setViewMode(contentType)
    xbmcplugin.endOfDirectory(addon_handle)
    
    #xbmc.executebuiltin("Dialog.Close(busydialog)")

def getUPnPClass():

    upnpClass = ''
    if media.settings('search_video') == 'true':
        upnpClass = "upnp:class derivedfrom &quot;object.item.videoItem&quot;"

    if media.settings('search_music') == 'true':
        if len(upnpClass) != 0:
            upnpClass += " or "

        upnpClass += "upnp:class derivedfrom &quot;object.item.audioItem&quot;"

    if media.settings('search_photo') == 'true':
        if len(upnpClass) != 0:
            upnpClass += " or "
            
        upnpClass += "upnp:class derivedfrom &quot;object.item.imageItem&quot;"
    
    return upnpClass

def getSearchCriteria(term):

    searchCriteria = ""
    
    if media.settings('search_title') == 'true':
        searchCriteria += "dc:title=&quot;" + term + "&quot;"

    if media.settings('search_album') == 'true':
        if len(searchCriteria) != 0:
            searchCriteria += " or "

        searchCriteria += "upnp:album=&quot;" + term + "&quot;"

    if media.settings('search_artist') == 'true':
        if len(searchCriteria) != 0:
            searchCriteria += " or "

        searchCriteria += "upnp:artist=&quot;" + term + "&quot;"

    if media.settings('search_tagline') == 'true':
        if len(searchCriteria) != 0:
            searchCriteria += " or "

        searchCriteria += "dc:description=&quot;" + term + "&quot;"
    
    if media.settings('search_description') == 'true':
        if len(searchCriteria) != 0:
            searchCriteria += " or "

        searchCriteria += "upnp:longDescription=&quot;" + term + "&quot;"
    
    if media.settings('search_keywords') == 'true':
        if len(searchCriteria) != 0:
            searchCriteria += " or "

        searchCriteria += "keywords=&quot;" + term + "&quot;"

    if media.settings('search_creator') == 'true':
        if len(searchCriteria) != 0:
            searchCriteria += " or "

        searchCriteria += "creator=&quot;" + term + "&quot;"

    return searchCriteria
    
def promptSearch():
    term = ''
    term = media.priorSearch()
    if term == 'cancel':
        return               #  User cancel
    if len(term) == 0:
        kb = xbmc.Keyboard('', 'Search')
        kb.setHeading('Enter Search text')
        kb.doModal()
        if (kb.isConfirmed()):
            term = kb.getText()
    if len(term) > 0:
        #xbmc.executebuiltin("ActivateWindow(busydialog)")
        media.addSearch(term)
        upnpClass = getUPnPClass()
        searchCriteria = getSearchCriteria(term)
        
        searchCriteria = "(" + searchCriteria + ") and (" + upnpClass + ")"
        
        url = args.get('contentdirectory', '')
        
        pin = media.settings('content_pin')
        content = browse.Search(url[0], '0', searchCriteria, 0, 1000, pin)
        if len(content) > 0:                                  #  Check for server response
            handleSearch(content, url[0], '0', searchCriteria)
        else:
            mgenlog ='Mezzmo no response from server. '
            xbmc.log(mgenlog, xbmc.LOGNOTICE)
            media.mgenlogUpdate(mgenlog)
            dialog_text = media.translate(30407)
            xbmcgui.Dialog().ok(media.translate(30408), dialog_text)
    
mode = args.get('mode', 'none')

refresh = args.get('refresh', 'False')

if refresh[0] == 'True':
    listServers(True)

if mode[0] == 'manual':                          #  Manually add Mezzmo server IP
    serverurl = addServers()
    if serverurl != 'None':
        saved_servers = media.settings('saved_servers')
        servers = pickle.loads(saved_servers)
        add_server = {'serverurl': serverurl}
        servers.append(add_server) 
        media.settings('saved_servers', pickle.dumps(servers))
        mgenlog = media.translate(30451) + serverurl
        xbmc.log(mgenlog, xbmc.LOGNOTICE)
        media.mgenlogUpdate(mgenlog)
        notify = xbmcgui.Dialog().notification(media.translate(30447), mgenlog, addon_icon, 5000)
    listServers(False)
    
if mode[0] == 'serverlist':
    listServers(False)

elif mode[0] == 'server':
    url = args.get('contentdirectory', '')
    objectID = args.get('objectID', '0')
    parentID = args.get('parentID', '0')
    pin = media.settings('content_pin')
    if media.settings('only_mezzmo_servers') == 'false':
        manufacturer = getContentURL(url[0])
    else:
        manufacturer = 'Conceiva'
    #xbmc.log('Mezzmo contenturl is: ' + str(url[0]) + ' ' + str(manufacturer) + ' ' + str(mode), xbmc.LOGNOTICE)        
    if parentID[0] == '0':
        import socket
        ip = ''
        try:
            ip = socket.gethostbyname(socket.gethostname())
        except Exception as e:
            xbmc.log("gethostbyname exception: " + str(e))
            pass
        contentrestriction.SetContentRestriction(url[0], ip, 'true', pin)

    if 'Conceiva' in manufacturer:         #  Check for server response
        brtime = time.time()               #  Get start time of browse                  
        content = browse.Browse(url[0], objectID[0], 'BrowseDirectChildren', 0, 1000, pin)
        patime = time.time()               #  Get start time of parse 
        handleBrowse(content, url[0], objectID[0], parentID[0])
    elif 'Conceiva' not in manufacturer:   #  Check for server response
        content = gBrowse(url[0], objectID[0], 'BrowseDirectChildren', 0, 1000, pin)
        ghandleBrowse(content, url[0], objectID[0], parentID[0])

    if len(content) == 0:
        mgenlog ='Mezzmo no response from server. '
        xbmc.log(mgenlog, xbmc.LOGNOTICE)
        media.mgenlogUpdate(mgenlog)
        dialog_text = media.translate(30407)
        xbmcgui.Dialog().ok(media.translate(30408), dialog_text)
                 
elif mode[0] == 'search':
    source = args.get('source', 'browse')
    promptSearch()
    if source[0] == 'native':
        xbmc.sleep(1)
        sys.exit()

elif mode[0] == 'picture':
    url = args.get('itemurl', '')
    showSingle(url)
    
def start():
    if mode == 'none':
        listServers(False)

