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

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])


def message(msg):
    __addon__ = xbmcaddon.Addon()
    __addonname__ = __addon__.getAddonInfo('name')
 
 
    xbmcgui.Dialog().ok(__addonname__, str(msg))

def listServers():
    servers = ssdp.discover("urn:schemas-upnp-org:device:MediaServer:1")
    xbmcplugin.setContent(addon_handle, 'movies')
    

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

def handleBrowse(content, contenturl, objectID, parentID):
    try:
        if objectID != parentID:
            itemurl = build_url({'mode': 'server', 'objectID': parentID, 'contentdirectory': contenturl})        
            li = xbmcgui.ListItem('Go back', iconImage='resources/media/go-up-md.png')
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=itemurl, listitem=li, isFolder=True)
        
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
            
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=itemurl, listitem=li, isFolder=True)

        for item in elems.findall('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}item'):
            title = item.find('.//{http://purl.org/dc/elements/1.1/}title').text
            itemid = item.get('id')
            icon = item.find('.//{urn:schemas-upnp-org:metadata-1-0/upnp/}albumArtURI').text
            itemurl = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}res').text        
            backdropurl = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}cvabackdrop')
            if backdropurl != None:
                backdropurl = backdropurl.text
            
            li = xbmcgui.ListItem(title, iconImage=icon)
            li.setArt({'thumb': icon, 'poster': icon, 'fanart': backdropurl})
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=itemurl, listitem=li, isFolder=False)
    except Exception as e:
        message(e)
        pass
    xbmcplugin.endOfDirectory(addon_handle, updateListing=True)

mode = args.get('mode', 'none')

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

