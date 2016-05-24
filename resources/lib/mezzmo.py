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

            itemurl = build_url({'mode': 'server', 'contentdirectory': contenturl})        
            li = xbmcgui.ListItem(friendlyname, iconImage='DefaultVideo.png')
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=itemurl, listitem=li)
        except Exception as e:
            message(e)
            pass
    xbmcplugin.endOfDirectory(addon_handle)

def build_url(query):
    return base_url + '?' + urllib.urlencode(query)

mode = args.get('mode', 'none')

if mode[0] == 'serverlist':
    listServers()

elif mode[0] == 'server':
    url = args.get('contentdirectory', '')
    objectID = args.get('objectID', '0')
    content = browse.Browse(url[0], objectID[0], 'BrowseDirectChildren', 0, 10)
    message(content)

def start():
    listServers()

