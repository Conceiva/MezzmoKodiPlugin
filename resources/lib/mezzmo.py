import sys
import xbmcgui
import xbmcplugin
import ssdp
import xbmcaddon
import xbmcgui
 
def message(msg):
    __addon__ = xbmcaddon.Addon()
    __addonname__ = __addon__.getAddonInfo('name')
 
 
    xbmcgui.Dialog().ok(__addonname__, str(msg))

def start():
    addon_handle = int(sys.argv[1])

    servers = ssdp.discover("urn:schemas-upnp-org:device:MediaServer:1")
    xbmcplugin.setContent(addon_handle, 'movies')
    message( servers )

    for server in servers:
        url = 'http://localhost/some_video.mkv'
        li = xbmcgui.ListItem(server.location, iconImage='DefaultVideo.png')
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li)

    xbmcplugin.endOfDirectory(addon_handle)
