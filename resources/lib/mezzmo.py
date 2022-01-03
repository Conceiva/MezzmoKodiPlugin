import sys
import pickle
import xbmcgui
import xbmcplugin
import ssdp
import xbmcaddon
import xbmcvfs
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
import media
import sync

#addon = xbmcaddon.Addon()
base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
argmod = sys.argv[2][1:].replace(';','&')    #  Handle change in urllib parsing to default to &
args = urllib.parse.parse_qs(argmod)

installed_version = media.get_installedversion()

def perfStats(TotalMatches, brtime, endtime, patime, srtime, ctitle):    # Log performance stats
    tduration = endtime - brtime
    sduration = (patime - brtime) + srtime
    pduration = tduration - sduration
    displayrate = int(TotalMatches) / tduration

    if media.settings('refreshflag') == '0':                             # Only update if not refresh
        psfile = media.openNosyncDB()                                    # Open Perf Stats database

        currDate = datetime.datetime.now().strftime('%Y-%m-%d')
        currTime = datetime.datetime.now().strftime('%H:%M:%S')
        if ctitle != ".." and ctitle != "":                              # Do not save Go up and refresh actions
            sduration = '{:.2f}'.format(sduration)  + "s"
            pduration = '{:.2f}'.format(pduration)  + "s"
            tduration = '{:.2f}'.format(tduration)  + "s"
            displayrate = "{:.2f}".format(displayrate) + " i/s"        
            psfile.execute('INSERT into mperfStats (psDate, psTime, psPlaylist, psCount, pSrvTime, mSrvTime,   \
            psTTime, psDispRate) values (?, ?, ?, ?, ?, ?, ?, ?)', (currDate, currTime, ctitle, TotalMatches,  \
            pduration, sduration, tduration, displayrate))
                          
        psfile.commit()
        psfile.close()
    else:                                                                # Reset refresh flag
        media.settings('refreshflag', '0')      
  

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
    timeoutval = float(media.settings('ssdp_timeout'))
    contenturl = ''    

    saved_servers = media.settings('saved_servers')
    if len(saved_servers) < 3 or force:
        servers = ssdp.discover("urn:schemas-upnp-org:device:MediaServer:1", timeout=timeoutval)
        # save the servers for faster loading
        media.settings('saved_servers', pickle.dumps(servers,0,fix_imports=True))
    else:
        saved_servers = saved_servers.encode('utf-8')
        servers = pickle.loads(saved_servers, fix_imports=True)
        
    onlyShowMezzmo = media.settings('only_mezzmo_servers') == 'true'

    itemurl = build_url({'mode': 'serverList', 'refresh': True})        
    li = xbmcgui.ListItem('Refresh')
    li.setArt({'icon':xbmcaddon.Addon().getAddonInfo("path") + '/resources/media/refresh.png'})
    
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=itemurl, listitem=li, isFolder=True)

    mgenlog ='Mezzmo server search: ' + str(len(servers)) + ' uPNP servers found.'
    xbmc.log(mgenlog, xbmc.LOGINFO)
    media.mgenlogUpdate(mgenlog)
    for server in servers:
        url = server.location        
        mgenlog ='Mezzmo server url: ' + url[:48]
        xbmc.log(mgenlog, xbmc.LOGINFO)
        media.mgenlogUpdate(mgenlog)
        
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
                iconurl = xbmcaddon.Addon().getAddonInfo("path") + '/icon.png'   
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
                iconurl = xbmcaddon.Addon().getAddonInfo("path") + '/resources/media/otherserver.png'        
            
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
                li.setArt({'thumb': iconurl, 'poster': iconurl, 'icon': iconurl, 'fanart': xbmcaddon.Addon().getAddonInfo("path") + 'fanart.jpg'})
                xbmcplugin.addDirectoryItem(handle=addon_handle, url=itemurl, listitem=li, isFolder=True)
        except Exception as e:
            printexception()
            pass
    setViewMode('servers')
    xbmcplugin.endOfDirectory(addon_handle, updateListing=force )
    if contenturl != None:
        media.kodiCleanDB(contenturl,0)         # Call function to delete Kodi actor database if user enabled.

    
def build_url(query):
    return base_url + '?' + urllib.parse.urlencode(query)


def content_mapping(contentType):               # Remap for skins which have limited Top / Folder views
    current_skin_name = xbmc.getSkinDir()
    if current_skin_name == 'skin.aeon.nox.5' or current_skin_name == 'skin.aeon.nox.silvo':
        aeonfoldermap = media.settings('aeoncontentmap')
        if aeonfoldermap != 'Default':
            contentType = aeonfoldermap.lower()

    if current_skin_name == 'skin.estuary':
        estuaryfoldermap = media.settings('estuarycontentmap')
        if estuaryfoldermap != 'Default':
            contentType = estuaryfoldermap.lower()

    return(contentType)     


def setViewMode(contentType):

    if media.settings('viewmap')  == 'false':	#  Mezzmo view mapping is disabled
        return
    current_skin_name = xbmc.getSkinDir()
    #xbmc.log('The content type is ' + contentType, xbmc.LOGINFO)
    #xbmc.log('The current skin name is ' + current_skin_name, xbmc.LOGINFO)    
    if current_skin_name == 'skin.aeon.nox.5' or current_skin_name == 'skin.aeon.nox.silvo':
        aeon_nox_views = { 'List'   : 50  ,
                       'InfoWall'   : 51  ,
                       'Landscape'  : 52  ,
                       'ShowCase1'  : 53  ,
                       'ShowCase2'  : 54  ,
                       'TriPanel'   : 55  ,
                       'Posters'    : 56  ,
                       'Shift'      : 57  ,
                       'BannerWall' : 58  ,
                       'Logo'       : 59  ,
                       'Icons'      : 500 ,
                       'LowList'    : 501 ,
                       'Episode'    : 502 ,
                       'Wall'       : 503 ,
                       'Gallery'    : 504 ,
                       'Panel'      : 505 ,
                       'RightList'  : 506 ,
                       'BigList'    : 507 ,
                       'SongList'   : 508 ,
                       'MyFlix'     : 509 ,
                       'BigFan'     : 591 ,
                       'BannerPlex' : 601 ,
                       'FanartList' : 602 ,
                       'Music_JukeBox'   : 603,
                       'Fullscreen_Wall' : 609, }
        
        view_mode = media.settings(contentType + '_view_mode' + '_aeon')
        if view_mode != 'Default':
            selected_mode = aeon_nox_views[view_mode]
            xbmc.executebuiltin('Container.SetViewMode(' + str(selected_mode) + ')')
            
    elif current_skin_name == 'skin.aeon.madnox':
        aeon_nox_views = { 'List'   : 50  ,
                       'InfoWall'   : 51  ,
                       'Landscape'  : 503 ,
                       'ShowCase1'  : 501 ,
                       'ShowCase2'  : 501 ,
                       'TriPanel'   : 52  ,
                       'Posters'    : 510 ,
                       'Shift'      : 57  ,
                       'BannerWall' : 508 ,
                       'Logo'       : 59  ,
                       'Wall'       : 500 ,
                       'LowList'    : 501 ,
                       'Episode'    : 514 ,
                       'Wall'       : 500 ,
                       'BigList'    : 510 }
        
        view_mode = media.settings(contentType + '_view_mode' + '_aeon')
        if view_mode != 'Default':
            selected_mode = aeon_nox_views[view_mode]
            xbmc.executebuiltin('Container.SetViewMode(' + str(selected_mode) + ')')
        
    elif current_skin_name == 'skin.estuary':
        estuary_views = { 'List'    : 50  ,
                       'Posters'    : 51  ,
                       'IconWall'   : 52  ,
                       'Shift'      : 53  ,
                       'InfoWall'   : 54  ,
                       'WideList'   : 55  ,
                       'Wall'       : 500 ,
                       'Banner'     : 501 ,
                       'FanArt'     : 502 }
        
        view_mode = media.settings(contentType + '_view_mode' + '_estuary')
        if view_mode != 'Default':
        
            selected_mode = estuary_views[view_mode]
            xbmc.executebuiltin('Container.SetViewMode(' + str(selected_mode) + ')')

    elif media.settings(contentType + '_view_mode') != "0":
       try:
           if media.settings(contentType + '_view_mode') == "1": # List
               xbmc.executebuiltin('Container.SetViewMode(502)')
           elif media.settings(contentType + '_view_mode') == "2": # Big List
               xbmc.executebuiltin('Container.SetViewMode(51)')
           elif media.settings(contentType + '_view_mode') == "3": # Thumbnails
               xbmc.executebuiltin('Container.SetViewMode(500)')
           elif media.settings(contentType + '_view_mode') == "4": # Poster Wrap
               xbmc.executebuiltin('Container.SetViewMode(501)')
           elif media.settings(contentType + '_view_mode') == "5": # Fanart
               xbmc.executebuiltin('Container.SetViewMode(508)')
           elif media.settings(contentType + '_view_mode') == "6":  # Media info
               xbmc.executebuiltin('Container.SetViewMode(504)')
           elif media.settings(contentType + '_view_mode') == "7": # Media info 2
               xbmc.executebuiltin('Container.SetViewMode(503)')
           elif media.settings(contentType + '_view_mode') == "8": # Media info 3
               xbmc.executebuiltin('Container.SetViewMode(515)')
           elif media.settings(contentType + '_view_mode') == "9": # Music info
               xbmc.executebuiltin('Container.SetViewMode(506)')    
       except:
           xbmc.log("SetViewMode Failed: "+media.settings('_view_mode'))
           xbmc.log("Skin: "+xbmc.getSkinDir())


def handleBrowse(content, contenturl, objectID, parentID):
    contentType = 'movies'
    itemsleft = -1
    pitemsleft = -1
    global brtime, patime
    srtime = 0  
    media.settings('contenturl', contenturl)
    koditv = media.settings('koditv')
    perflog = media.settings('perflog')   
    kodichange = media.settings('kodichange')         # Checks for change detection user setting
    kodiactor = media.settings('kodiactor')           # Checks for actor info setting
    menuitem1 = xbmcaddon.Addon().getLocalizedString(30347)
    menuitem2 = xbmcaddon.Addon().getLocalizedString(30346)
    menuitem3 = xbmcaddon.Addon().getLocalizedString(30372)
    menuitem4 = xbmcaddon.Addon().getLocalizedString(30373)
    menuitem5 = xbmcaddon.Addon().getLocalizedString(30379)
    menuitem6 = xbmcaddon.Addon().getLocalizedString(30380)
    menuitem7 = xbmcaddon.Addon().getLocalizedString(30384)
    autostart = media.settings('autostart')
    sync.deleteTexturesCache(contenturl)                # Call function to delete textures cache if user enabled.  
    #xbmc.log('Kodi version: ' + installed_version, xbmc.LOGINFO)
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
                    if (icon[-4:]) !=  '.jpg': 
                        icon = icon + '.jpg'
                        xbmc.log('Handle browse initial icon is: ' + icon, xbmc.LOGDEBUG)    

                itemurl = build_url({'mode': 'server', 'parentID': objectID, 'objectID': containerid, 'contentdirectory': contenturl})        
                li = xbmcgui.ListItem(title)
                li.setArt({'banner': icon, 'poster': icon, 'icon': icon, 'fanart': xbmcaddon.Addon().getAddonInfo("path") + 'fanart.jpg'})
                mediaClass_text = 'video'
                info = {
                        'plot': description_text,
                }
                li.setInfo(mediaClass_text, info)
                    
                searchargs = urllib.parse.urlencode({'mode': 'search', 'contentdirectory': contenturl, 'objectID': containerid})

                itempath = xbmc.getInfoLabel("ListItem.FileNameAndPath ") 
                autitle = xbmc.getInfoLabel("ListItem.Label")         #  Get title of selected playlist 
                if (autostart == '' or autostart == 'clear' or autostart == '""'):
                    li.addContextMenuItems([ ('Refresh', 'Container.Refresh'), ('Go up', 'Action(ParentDir)'), ('Search',          \
                    'Container.Update( plugin://plugin.video.mezzmo?' + searchargs + ')'), (menuitem7, 'RunScript(%s, %s)' %       \
                    ("plugin.video.mezzmo", "performance")), (menuitem5, 'RunScript(%s, %s, %s, %s)'  % ("plugin.video.mezzmo",    \
                    "auto", itempath, autitle)) ])
                elif len(autostart) > 6 :
                    li.addContextMenuItems([ ('Refresh', 'Container.Refresh'), ('Go up', 'Action(ParentDir)'), ('Search',          \
                    'Container.Update( plugin://plugin.video.mezzmo?' + searchargs + ')'), (menuitem7, 'RunScript(%s, %s)' %       \
                    ("plugin.video.mezzmo", "performance")), (menuitem6, 'RunScript(%s, %s, %s, %s)'  % ("plugin.video.mezzmo",    \
                    "auto", "clear", autitle)) ])
                
                xbmcplugin.addDirectoryItem(handle=addon_handle, url=itemurl, listitem=li, isFolder=True)
                if parentID == '0':
                    contentType = 'top'
                else:
                    contentType = 'folders'
                contentType = content_mapping(contentType)

            ctitle = xbmc.getInfoLabel("ListItem.Label")           #  Get title of selected playlist      
            dbfile = media.openKodiDB()                  #  Open Kodi database    
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
                    #xbmc.log('The current URL is: ' + itemurl, xbmc.LOGINFO)
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
                    artist_text = artist.text

                actor_list = ''
                cast_dict = []    # Added cast & thumbnail display from Mezzmo server
                cast_dict_keys = ['name','thumbnail']
                actors = item.find('.//{urn:schemas-upnp-org:metadata-1-0/upnp/}artist')
                if actors != None:
                    actor_list = actors.text.replace(', Jr.' , ' Jr.').replace(', Sr.' , ' Sr.').split(',')
                    for a in actor_list:                  
                        actorSearchUrl = imageSearchUrl + "?imagesearch=" + a.lstrip().replace(" ","+")
                        #xbmc.log('search URL: ' + actorSearchUrl, xbmc.LOGINFO)  # uncomment for thumbnail debugging
                        new_record = [ a.strip() , actorSearchUrl]
                        cast_dict.append(dict(list(zip(cast_dict_keys, new_record))))

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
                    
                categories_text = 'movie'
                categories = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}categories')
                if categories != None and categories.text != None:
                    categories_text = categories.text.split(',')[0]   #  Kodi can only handle 1 media type
                    if categories_text[:7].lower() == 'tv show':
                        categories_text = 'episode'
                        contentType = 'episodes'
                    elif categories_text[:5].lower() == 'movie':
                        categories_text = 'movie'
                        contentType = 'movies'
                        album_text = ''
                    elif categories_text[:11].lower() == 'music video':
                        categories_text = 'musicvideo'
                        contentType = 'musicvideos'
                        album_text = ''
                    else:
                        categories_text = 'video'
                        contentType = 'videos'
                        album_text = ''
                        
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
                        
                if mediaClass_text == 'video' and validf == 1:    
                    mtitle = media.displayTitles(title)					#  Normalize title
                    pctitle = '"' + mtitle + '"'  		                        #  Handle commas
                    pcseries = '"' + album_text + '"'                                   #  Handle commas
                    pcdbfile = media.getDatabaseName() 
                    if playcount == 0:
                        li.addContextMenuItems([ (menuitem1, 'RunScript(%s, %s)' % ("plugin.video.mezzmo", "refresh")),     \
                        (menuitem2, 'Action(ParentDir)'), (menuitem3, 'RunScript(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)' % \
                        ("plugin.video.mezzmo", "count", pctitle, itemurl, season_text, episode_text, playcount, pcseries,  \
                        pcdbfile, contenturl)) ])
                    elif playcount > 0:
                        li.addContextMenuItems([ (menuitem1, 'RunScript(%s, %s)' % ("plugin.video.mezzmo", "refresh")),     \
                        (menuitem2, 'Action(ParentDir)'), (menuitem4, 'RunScript(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)' % \
                        ("plugin.video.mezzmo", "count", pctitle, itemurl, season_text, episode_text, playcount, pcseries,  \
                        pcdbfile, contenturl)) ])      
               
                    info = {
                        'duration': sync.getSeconds(duration_text),
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
                        'tvshowtitle':album_text,
                        'dateadded':date_added_text,
                    }
                    li.setInfo(mediaClass_text, info)
                    li.setProperty('ResumeTime', dcmInfo_text)
                    li.setProperty('TotalTime', str(sync.getSeconds(duration_text)))
                    video_info = {
                        'codec': video_codec_text,
                        'aspect': aspect,
                        'width': video_width,
                        'height': video_height,
                    }
                    li.addStreamInfo('video', video_info)
                    li.addStreamInfo('audio', {'codec': audio_codec_text, 'language': audio_lang, 'channels': int(audio_channels_text)})
                    li.addStreamInfo('subtitle', {'language': subtitle_lang})
                    if installed_version >= '19':       #  Update cast with thumbnail support in Kodi v19 and higher
                        li.setCast(cast_dict)                
                    tvcheckval = media.tvChecker(season_text, episode_text, koditv, mtitle, categories)  # Check if Ok to add
                    if installed_version >= '19' and kodiactor == 'true' and tvcheckval[0] == 1:  
                        pathcheck = media.getPath(itemurl)                  #  Get path string for media file
                        serverid = media.getMServer(itemurl)                #  Get Mezzmo server id
                        filekey = media.checkDBpath(itemurl, mtitle, playcount, dbfile, pathcheck, serverid,      \
                        season_text, episode_text, album_text, last_played_text, date_added_text, 'false')
                        xbmc.log('Mezzmo filekey is: ' + str(filekey), xbmc.LOGDEBUG) 
                        durationsecs = sync.getSeconds(duration_text)       #  convert movie duration to seconds
                        if filekey[4] == 1:
                            showId = media.checkTVShow(filekey, album_text, genre_text, dbfile, content_rating_text, \
                            production_company_text)
                            mediaId = media.writeEpisodeToDb(filekey, mtitle, description_text, tagline_text,           \
                            writer_text, creator_text, aired_text, rating_val, durationsecs, genre_text, trailerurl,    \
                            content_rating_text, icon, kodichange, backdropurl, dbfile, production_company_text,        \
                            sort_title_text, season_text, episode_text, showId, 'false')  
                        else:  
                            mediaId = media.writeMovieToDb(filekey, mtitle, description_text, tagline_text, writer_text, \
                            creator_text, release_date_text, rating_val, durationsecs, genre_text, trailerurl,           \
                            content_rating_text, icon, kodichange, backdropurl, dbfile, production_company_text,         \
                            sort_title_text, 'false')
                        if (artist != None and filekey[0] > 0) or mediaId == 999999: #  Add actor information to new movie
                            media.writeActorsToDb(artist_text, mediaId, imageSearchUrl, mtitle, dbfile, filekey)
                        media.writeMovieStreams(filekey, video_codec_text, aspect, video_height, video_width,  \
                        audio_codec_text, audio_channels_text, durationsecs, mtitle, kodichange, itemurl,\
                        icon, backdropurl, dbfile, pathcheck, 'false')      # Update movie stream info 
                        xbmc.log('The movie name is: ' + mtitle, xbmc.LOGDEBUG)  
                             
                elif mediaClass_text == 'music':
                    mtitle = media.displayTitles(title)					#  Normalize title
                    pctitle = '"' + mtitle + '"'  		                        #  Handle commas
                    pcseries = '"' + album_text + '"'                                   #  Handle commas
                    offsetmenu = 'Resume from ' + time.strftime("%H:%M:%S", time.gmtime(int(dcmInfo_text)))
                    if int(dcmInfo_text) > 0 and playcount == 0:
                        li.addContextMenuItems([ (menuitem1, 'RunScript(%s, %s)' % ("plugin.video.mezzmo", "refresh")),   \
                        (menuitem2, 'Action(ParentDir)'), (menuitem3, 'RunScript(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)' \
                        % ("plugin.video.mezzmo", "count", pctitle, itemurl, season_text, episode_text, playcount,        \
                        pcseries, 'audiom', contenturl)), (offsetmenu, 'RunScript(%s, %s, %s, %s, %s, %s, %s, %s)' %      \
                        ("plugin.video.mezzmo", "playm", itemurl, li, title, icon, backdropurl, dcmInfo_text)) ])
                    elif int(dcmInfo_text) > 0 and playcount > 0:
                        li.addContextMenuItems([ (menuitem1, 'RunScript(%s, %s)' % ("plugin.video.mezzmo", "refresh")),   \
                        (menuitem2, 'Action(ParentDir)'), (menuitem4, 'RunScript(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)' \
                        % ("plugin.video.mezzmo", "count", pctitle, itemurl, season_text, episode_text, playcount,        \
                        pcseries, 'audiom', contenturl)), (offsetmenu, 'RunScript(%s, %s, %s, %s, %s, %s, %s, %s)' %      \
                        ("plugin.video.mezzmo", "playm", itemurl, li, title, icon, backdropurl, dcmInfo_text)),  ])
                    elif int(dcmInfo_text) == 0 and playcount > 0:
                        li.addContextMenuItems([ (menuitem1, 'RunScript(%s, %s)' % ("plugin.video.mezzmo", "refresh")),   \
                        (menuitem2, 'Action(ParentDir)'), (menuitem4, 'RunScript(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)' \
                        % ("plugin.video.mezzmo", "count", pctitle, itemurl, season_text, episode_text, playcount,        \
                        pcseries, 'audiom', contenturl)) ])
                    elif int(dcmInfo_text) == 0 and playcount == 0:
                        li.addContextMenuItems([ (menuitem1, 'RunScript(%s, %s)' % ("plugin.video.mezzmo", "refresh")),   \
                        (menuitem2, 'Action(ParentDir)'), (menuitem3, 'RunScript(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)' \
                        % ("plugin.video.mezzmo", "count", pctitle, itemurl, season_text, episode_text, playcount,        \
                        pcseries, 'audiom', contenturl)) ])  

                    info = {
                        'duration': sync.getSeconds(duration_text),
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
                    mcomment = media.mComment(info, duration_text, offsetmenu[11:])
                    info.update(comment = mcomment)
                    li.setInfo(mediaClass_text, info)
                    validf = 1	     #  Set valid file info flag
                    contentType = 'songs'

                elif mediaClass_text == 'picture':
                    li.addContextMenuItems([ (menuitem1, 'RunScript(%s, %s)' % ("plugin.video.mezzmo", "refresh")),     \
                    (xbmcaddon.Addon().getLocalizedString(30346), 'Action(ParentDir)') ])                     
                    info = {
                        'title': title,
                    }
                    li.setInfo(mediaClass_text, info)
                    validf = 1	     #  Set valid file info flag
                    contentType = 'files'
                 
                if validf == 1: 
                    xbmcplugin.addDirectoryItem(handle=addon_handle, url=itemurl, listitem=li, isFolder=False)
                else:
                    dialog_text = "Video file:  " + title + " is invalid. Check Mezzmo video properties for this file."
                    xbmcgui.Dialog().ok("Mezzmo", dialog_text)

            itemsleft = itemsleft - int(NumberReturned) - 1
            dbfile.commit()                #  Commit writes
            
            xbmc.log('Mezzmo items left: ' + str(itemsleft), xbmc.LOGDEBUG) 
            if itemsleft <= 0:
                dbfile.commit()            
                dbfile.close()             #  Final commit writes and close Kodi database  
                if int(TotalMatches) > 49 and perflog == "true":
                    endtime = time.time()
                    perfStats(TotalMatches, brtime, endtime, patime, srtime, ctitle)
                break

            if pitemsleft == itemsleft:    #  Detect items left not incrementing 
                dbfile.commit()
                dbfile.close()             #  Final commit writes and close Kodi database
                mgenlog ='Mezzmo items not displayed: ' + str(pitemsleft)
                xbmc.log(mgenlog, xbmc.LOGINFO)
                mgenlogUpdate(mgenlog)
                if int(TotalMatches) > 49 and perflog == "true":
                    endtime = time.time()
                    perfStats(TotalMatches, brtime, endtime, patime, srtime, ctitle)
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
        printexception()
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
    menuitem1 = xbmcaddon.Addon().getLocalizedString(30347)
    menuitem2 = xbmcaddon.Addon().getLocalizedString(30346)
    kodichange = media.settings('kodichange')         # Checks for change detection user setting
    kodiactor = media.settings('kodiactor')           # Checks for actor info setting
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
                dialog_text = "There were no matching search results found on your Mezzmo server."
                xbmcgui.Dialog().ok("Mezzmo Search Results", dialog_text)
                xbmc.executebuiltin('Action(ParentDir)')
                break; #sanity check
                
            if itemsleft == -1:
                itemsleft = int(TotalMatches)
            
            #elems = xml.etree.ElementTree.fromstring(result.text.encode('utf-8'))
            elems = xml.etree.ElementTree.fromstring(result.text)
               
            for item in elems.findall('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}item'):
                title = item.find('.//{http://purl.org/dc/elements/1.1/}title').text
                itemid = item.get('id')
                icon = None
                albumartUri = item.find('.//{urn:schemas-upnp-org:metadata-1-0/upnp/}albumArtURI')
                if albumartUri != None:
                    icon = albumartUri.text
                    if (icon[-4:]) !=  '.jpg': 
                        icon = icon + '.jpg'
                        xbmc.log('Handle search initial icon is: ' + icon, xbmc.LOGDEBUG)    
                res = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}res')
                subtitleurl = None
                duration_text = ''
                video_width = 0
                video_height = 0
                aspect = 0.0
                validf = 0
                
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
                        validf = 1	     #  Set valid file info flag

                backdropurl = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}cvabackdrop')
                if backdropurl != None:
                    backdropurl = backdropurl.text
                    if (backdropurl [-4:]) !=  '.jpg': 
                        backdropurl  = backdropurl  + '.jpg'
                
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
                    artist_text = artist.text

                actor_list = ''
                cast_dict = []        # Added cast & thumbnail display from Mezzmo server
                cast_dict_keys = ['name','thumbnail']
                actors = item.find('.//{urn:schemas-upnp-org:metadata-1-0/upnp/}artist')
                if actors != None:
                    actor_list = actors.text.replace(', Jr.' , ' Jr.').replace(', Sr.' , ' Sr.').split(',')
                    for a in actor_list:                 
                        actorSearchUrl = imageSearchUrl + "?imagesearch=" + a.lstrip().replace(" ","+")
                        #xbmc.log('search URL: ' + actorSearchUrl, xbmc.LOGINFO)  
                        new_record = [ a.strip() , actorSearchUrl]
                        cast_dict.append(dict(list(zip(cast_dict_keys, new_record))))                  

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
                    
                categories_text = 'movie'
                categories = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}categories')
                if categories != None and categories.text != None:
                    categories_text = categories.text.split(',')[0]   #  Kodi can only handle 1 media type
                    if categories_text[:7].lower() == 'tv show':
                        categories_text = 'episode'
                        contentType = 'episodes'
                    elif categories_text[:5].lower() == 'movie':
                        categories_text = 'movie'
                        contentType = 'movies'
                        album_text = ''
                    elif categories_text[:11].lower() == 'music video':
                        categories_text = 'musicvideo'
                        contentType = 'musicvideos'
                        album_text = ''
                    else:
                        categories_text = 'video'
                        contentType = 'videos'
                        album_text = ''
                        
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
                        
                if mediaClass_text == 'video' and validf == 1:  
                    li.addContextMenuItems([ (xbmcaddon.Addon().getLocalizedString(30347), 'Container.Refresh'), (xbmcaddon.Addon().getLocalizedString(30346), 'Action(ParentDir)'), (xbmcaddon.Addon().getLocalizedString(30348), 'Action(Info)') ])
                    
                    info = {
                        'duration': sync.getSeconds(duration_text),
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
                        'lastplayed': last_played_text,
                        'trailer':trailerurl,
                        'tvshowtitle':album_text,
                        'dateadded':date_added_text,
                    }
                    li.setInfo(mediaClass_text, info)
                    li.setProperty('ResumeTime', dcmInfo_text)
                    li.setProperty('TotalTime', str(sync.getSeconds(duration_text)))
                    video_info = {
                        'codec': video_codec_text,
                        'aspect': aspect,
                        'width': video_width,
                        'height': video_height,
                    }
                    li.addStreamInfo('video', video_info)
                    li.addStreamInfo('audio', {'codec': audio_codec_text, 'language': audio_lang, 'channels': int(audio_channels_text)})
                    li.addStreamInfo('subtitle', {'language': subtitle_lang})
                    if installed_version >= '19':         #  Update cast with thumbnail support in Kodi v19 and higher
                        li.setCast(cast_dict)  

                    mtitle = media.displayTitles(title) 
                    tvcheckval = media.tvChecker(season_text, episode_text, koditv, mtitle, categories)  # Check if Ok to add
                    if installed_version >= '19' and kodiactor == 'true' and tvcheckval[0] == 1:  
                        dbfile = media.openKodiDB()
                        mtitle = media.displayTitles(title)
                        pathcheck = media.getPath(itemurl)                  #  Get path string for media file
                        serverid = media.getMServer(itemurl)                #  Get Mezzmo server id
                        filekey = media.checkDBpath(itemurl, mtitle, playcount, dbfile, pathcheck, serverid,      \
                        season_text, episode_text, album_text, last_played_text, date_added_text, 'false')
                        #xbmc.log('Mezzmo filekey is: ' + str(filekey), xbmc.LOGINFO) 
                        durationsecs = sync.getSeconds(duration_text)       #  convert duration to seconds before passing
                        if filekey[4] == 1:
                            showId = media.checkTVShow(filekey, album_text, genre_text, dbfile, content_rating_text, \
                            production_company_text)
                            mediaId = media.writeEpisodeToDb(filekey, mtitle, description_text, tagline_text,           \
                            writer_text, creator_text, aired_text, rating_val, durationsecs, genre_text, trailerurl,    \
                            content_rating_text, icon, kodichange, backdropurl, dbfile, production_company_text,        \
                            sort_title_text, season_text, episode_text, showId, 'false')  
                        else:  
                            mediaId = media.writeMovieToDb(filekey, mtitle, description_text, tagline_text, writer_text, \
                            creator_text, release_date_text, rating_val, durationsecs, genre_text, trailerurl,           \
                            content_rating_text, icon, kodichange, backdropurl, dbfile, production_company_text,         \
                            sort_title_text, 'false')
                        if (artist != None and filekey[0] > 0) or mediaId == 999999: #  Add actor information to new movie
                            media.writeActorsToDb(artist_text, mediaId, imageSearchUrl, mtitle, dbfile, filekey)
                        media.writeMovieStreams(filekey, video_codec_text, aspect, video_height, video_width,  \
                        audio_codec_text, audio_channels_text, durationsecs, mtitle, kodichange, itemurl,\
                        icon, backdropurl, dbfile, pathcheck, 'false')      # Update movie stream info 
                        #xbmc.log('The movie name is: ' + mtitle, xbmc.LOGINFO)
                        dbfile.commit()
                        dbfile.close() 
                      
                elif mediaClass_text == 'music':
                    offsetmenu = 'Play from ' + time.strftime("%H:%M:%S", time.gmtime(int(dcmInfo_text)))
                    if int(dcmInfo_text) > 0:
                        li.addContextMenuItems([ (menuitem1, 'Container.Refresh'), (menuitem2, 'Action(ParentDir)'),     \
                        (offsetmenu, 'RunScript(%s, %s, %s, %s, %s, %s, %s, %s)' % ("plugin.video.mezzmo", "playm",      \
                        itemurl, li, title, icon, backdropurl, dcmInfo_text)) ])
                    else:
                        li.addContextMenuItems([ (menuitem1, 'Container.Refresh'), (menuitem2, 'Action(ParentDir)') ])  

                    info = {
                        'duration': sync.getSeconds(duration_text),
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
                    mcomment = media.mComment(info, duration_text, offsetmenu[11:])
                    info.update(comment = mcomment)
                    li.setInfo(mediaClass_text, info)
                    validf = 1	     #  Set valid file info flag
                    contentType = 'songs'

                elif mediaClass_text == 'picture':
                    li.addContextMenuItems([ (xbmcaddon.Addon().getLocalizedString(30347), 'Container.Refresh'), (xbmcaddon.Addon().getLocalizedString(30346), 'Action(ParentDir)') ])                   
                    info = {
                        'title': title,
                    }
                    li.setInfo(mediaClass_text, info)
                    validf = 1	           #  Set valid file info flag
                    contentType = 'files'

                if validf == 1:  
                    xbmcplugin.addDirectoryItem(handle=addon_handle, url=itemurl, listitem=li, isFolder=False)
            
            itemsleft = itemsleft - int(NumberReturned) - 1
            if itemsleft == 0:
                break

            if pitemsleft == itemsleft:    #  Detect items left not incrementing 
                dbfile.commit()
                dbfile.close()             #  Final commit writes and close Kodi database
                mgenlog ='Mezzmo items not displayed: ' + str(pitemsleft)
                xbmc.log(mgenlog, xbmc.LOGNOTICE)
                mgenlogUpdate(mgenlog)   
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
        printexception()
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
    
    xbmc.executebuiltin("Dialog.Close(busydialog)")

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
        
        pin = media.settings('content_pin')
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
    pin = media.settings('content_pin')
    
    if parentID[0] == '0':
        import socket
        ip = ''
        try:
            ip = socket.gethostbyname(socket.gethostname())
        except Exception as e:
            xbmc.log("gethostbyname exception: " + str(e))
            pass
        contentrestriction.SetContentRestriction(url[0], ip, 'true', pin)

    brtime = time.time()                                  #  Get start time of browse           
    content = browse.Browse(url[0], objectID[0], 'BrowseDirectChildren', 0, 1000, pin)
    patime = time.time()                                  #  Get start time of parse 
    handleBrowse(content, url[0], objectID[0], parentID[0])

elif mode[0] == 'search':
    promptSearch()
    
#xbmcplugin.setPluginFanart(addon_handle, addon.getAddonInfo("path") + 'fanart.jpg', color2='0xFFFF3300')

def start():
    if mode == 'none':
        listServers(False)


