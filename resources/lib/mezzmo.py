import sys
import xbmcgui
import xbmcplugin
import ssdp
import xbmcaddon
import xbmcgui
import urllib2
import urllib
import xml.etree.ElementTree
import re
import xml.etree.ElementTree as ET
import urlparse
import browse
import xbmc
import linecache
import sys
import datetime
import time

addon = xbmcaddon.Addon()
base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])

def getSeconds(t):
    x = time.strptime(t.split(',')[0],'%H:%M:%S.000')
    seconds = datetime.timedelta(hours=x.tm_hour,minutes=x.tm_min,seconds=x.tm_sec).total_seconds()
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
    message( 'EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj))

def listServers():
    servers = ssdp.discover("urn:schemas-upnp-org:device:MediaServer:1")
    
    itemurl = build_url({'mode': 'serverList', 'refresh': True})        
    li = xbmcgui.ListItem('Refresh', iconImage='DefaultVideo.png')
    
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=itemurl, listitem=li, isFolder=True)

    for server in servers:
        url = server.location
        
        response = urllib2.urlopen(url)
        try:
            xmlstring = re.sub(' xmlns="[^"]+"', '', response.read(), count=1)
            
            e = xml.etree.ElementTree.fromstring(xmlstring)
	    
            device = e.find('device')
	    friendlyname = device.find('friendlyName').text
            serviceList = device.find('serviceList')
            
            contenturl = ''
            for service in serviceList.findall('service'):
                serviceId = service.find('serviceId')
                
                if serviceId.text == 'urn:upnp-org:serviceId:ContentDirectory':
                    contenturl = service.find('controlURL').text
                    if contenturl.startswith('/'):
                        end = url.rfind('/')
                        length = len(url)
                        
                        contenturl = url[:end-length] + contenturl
                    else:
                        end = url.rfind('/')
                        length = len(url)
                        
                        contenturl = url[:end-length] + '/' + contenturl

            itemurl = build_url({'mode': 'server', 'contentdirectory': contenturl})        
            li = xbmcgui.ListItem(friendlyname, iconImage='DefaultVideo.png')
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=itemurl, listitem=li, isFolder=True)
        except Exception as e:
            message(e)
            pass
    xbmcplugin.endOfDirectory(addon_handle)

def build_url(query):
    return base_url + '?' + urllib.urlencode(query)

def setViewMode():
   if not addon.getSetting('view_mode') == "0":
       try:
           if addon.getSetting('view_mode') == "1": # List
               xbmc.executebuiltin('Container.SetViewMode(502)')
           elif addon.getSetting('view_mode') == "2": # Big List
               xbmc.executebuiltin('Container.SetViewMode(51)')
           elif addon.getSetting('view_mode') == "3": # Thumbnails
               xbmc.executebuiltin('Container.SetViewMode(500)')
           elif addon.getSetting('view_mode') == "4": # Poster Wrap
               xbmc.executebuiltin('Container.SetViewMode(501)')
           elif addon.getSetting('view_mode') == "5": # Fanart
               xbmc.executebuiltin('Container.SetViewMode(508)')
           elif addon.getSetting('view_mode') == "6":  # Media info
               xbmc.executebuiltin('Container.SetViewMode(504)')
           elif addon.getSetting('view_mode') == "7": # Media info 2
               xbmc.executebuiltin('Container.SetViewMode(503)')
           elif addon.getSetting('view_mode') == "8": # Media info 3
               xbmc.executebuiltin('Container.SetViewMode(515)')
       except:
           addon_log("SetViewMode Failed: "+addon.getSetting('view_mode'))
           addon_log("Skin: "+xbmc.getSkinDir())


def handleBrowse(content, contenturl, objectID, parentID):
    xbmcplugin.setContent(addon_handle, 'movies')
    try:
        
        e = xml.etree.ElementTree.fromstring(content)
        
        body = e.find('.//{http://schemas.xmlsoap.org/soap/envelope/}Body')
        browseresponse = body.find('.//{urn:schemas-upnp-org:service:ContentDirectory:1}BrowseResponse')
        result = browseresponse.find('Result')

        elems = xml.etree.ElementTree.fromstring(result.text.encode('utf-8'))
        
        for container in elems.findall('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}container'):
            title = container.find('.//{http://purl.org/dc/elements/1.1/}title').text
            containerid = container.get('id')
            icon = container.find('.//{urn:schemas-upnp-org:metadata-1-0/upnp/}albumArtURI')
            if icon != None:
                icon = icon.text
            itemurl = build_url({'mode': 'server', 'parentID': objectID, 'objectID': containerid, 'contentdirectory': contenturl})        
            li = xbmcgui.ListItem(title, iconImage=icon)
            li.addContextMenuItems([ ('Refresh', 'Container.Refresh'), ('Go up', 'Action(ParentDir)') ])
            
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=itemurl, listitem=li, isFolder=True)

        for item in elems.findall('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}item'):
            title = item.find('.//{http://purl.org/dc/elements/1.1/}title').text
            itemid = item.get('id')
            icon = None
            albumartUri = item.find('.//{urn:schemas-upnp-org:metadata-1-0/upnp/}albumArtURI')
            if albumartUri != None:
                icon = albumartUri.text  
            res = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}res')
            subtitleurl = None
            duration_text = ''
            
            if res != None:
                itemurl = res.text 
                subtitleurl = res.get('{http://www.pv.com/pvns/}subtitleFileUri')            
                duration_text = res.get('duration')
                if duration_text == None:
                    duration_text = '00:00:00.000'
                
            backdropurl = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}cvabackdrop')
            if backdropurl != None:
                backdropurl = backdropurl.text
            
            li = xbmcgui.ListItem(title, iconImage=icon)
            li.setArt({'thumb': icon, 'poster': icon, 'fanart': backdropurl})
            if subtitleurl != None:
                li.setSubtitles([subtitleurl])
                
            genre_text = ''
            genre = item.find('.//{urn:schemas-upnp-org:metadata-1-0/upnp/}genre')
            if genre != None:
                genre_text = genre.text
                
            release_year_text = ''
            release_year = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}release_year')
            if release_year != None:
                release_year_text = release_year.text
            
            description_text = ''
            description = item.find('.//{urn:schemas-upnp-org:metadata-1-0/upnp/}longDescription')
            if description != None and description.text != None:
                description_text = description.text
                
            artist_text = ''
            artist = item.find('.//{urn:schemas-upnp-org:metadata-1-0/upnp/}artist')
            if artist != None:
                artist_text = artist.text
                
            creator_text = ''
            creator = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}creator')
            if creator != None:
                creator_text = creator.text
                
            tagline_text = ''
            tagline = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}tag_line')
            if tagline != None:
                tagline_text = tagline.text
                
            categories_text = 'movie'
            categories = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}categories')
            if categories != None and categories.text != None:
                categories_text = categories.text
                if categories_text == 'TV show':
                    categories_text = 'tvshow'
                    
            episode_text = ''
            episode = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}episode')
            if episode != None:
                episode_text = episode.text
             
            season_text = ''
            season = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}season')
            if season != None:
                season_text = season.text
                      
            writer_text = ''
            writer = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}writers')
            if writer != None:
                writer_text = writer.text
          
            imdb_text = ''
            imdb = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}imdb_id')
            if imdb != None:
                imdb_text = imdb.text
          
            rating_val = ''
            rating = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}rating')
            if rating != None:
                rating_val = rating.text
                rating_val = float(rating_val) * 2
                rating_val = str(rating_val) #kodi ratings are out of 10, Mezzmo is out of 5
            
            info = {
                'duration': getSeconds(duration_text),
                'genre': genre_text,
                'year': release_year_text,
                'title': title,
                'plot': description_text,
                'director': creator_text,
                'tagline': tagline_text,
                'writer': writer_text,
                'artist': artist_text.split(),
                'rating': rating_val,
                'code': imdb_text,
                'mediatype': categories_text.split(),
                'season': season_text,
                'episode': episode_text,
            }
            li.setInfo('video', info)
            
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=itemurl, listitem=li, isFolder=False)
    except Exception as e:
        message(e)
        printexception()
        pass
    xbmcplugin.endOfDirectory(addon_handle)
    setViewMode()

mode = args.get('mode', 'none')

refresh = args.get('refresh', 'False')

if refresh[0] == 'True':
    xbmc.executebuiltin('Container.Refresh')
    
if mode[0] == 'serverlist':
    listServers()
    message('serverlist')

elif mode[0] == 'server':
    url = args.get('contentdirectory', '')
    objectID = args.get('objectID', '0')
    parentID = args.get('parentID', '0')
    content = browse.Browse(url[0], objectID[0], 'BrowseDirectChildren', 0, 500)
    handleBrowse(content, url[0], objectID[0], parentID[0])

def start():
    if mode == 'none':
        listServers()

