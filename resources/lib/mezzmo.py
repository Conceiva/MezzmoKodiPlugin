import sys
import xbmcgui
import xbmcplugin
import ssdp
import xbmcaddon
import xbmcgui
import urllib2
import xml.etree.ElementTree

def message(msg):
    __addon__ = xbmcaddon.Addon()
    __addonname__ = __addon__.getAddonInfo('name')
 
 
    xbmcgui.Dialog().ok(__addonname__, str(msg))

def start():
    addon_handle = int(sys.argv[1])

    servers = ssdp.discover("urn:schemas-upnp-org:device:MediaServer:1")
    xbmcplugin.setContent(addon_handle, 'movies')
    

    for server in servers:
        url = server.location
        response = urllib2.urlopen(url)
        try:
            e = xml.etree.ElementTree.parse(response).getroot()
	    device = e.find('.//root/device/friendlyName')
	    #friendlyname = e.find('friendlyName').text
            message( device)
            li = xbmcgui.ListItem(server.location, iconImage='DefaultVideo.png')
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li)
        except Exception as e:
            message(e)
            pass
    xbmcplugin.endOfDirectory(addon_handle)
