import xbmc
import time
import xbmcaddon
from common import GLOBAL_SETUP  #Needed first to setup import locations
import bookmark
import socket
import contentrestriction
import sync

pos = 0
file = ''
count = 0 

def settings(setting, value = None):
    # Get or add addon setting
    addon = xbmcaddon.Addon()
    if value:
        addon.setSetting(setting, value)
    else:
        return addon.getSetting(setting)
   
class XBMCPlayer(xbmc.Player):
    
    def __init__(self, *args):
        pass
 
    def onPlayBackStarted(self):
        file = xbmc.Player().getPlayingFile()
        xbmc.log("Mezzmo Playback started - " + file, xbmc.LOGDEBUG)
 
    def onPlayBackPaused(self):
        xbmc.log("Mezzmo Playback paused - LED OFF" , xbmc.LOGDEBUG)
 
    def onPlayBackResumed(self):
        file = self.getPlayingFile()
        xbmc.log("Mezzmo Playback resumed - LED ON" , xbmc.LOGDEBUG)
 
    def onPlayBackEnded(self):
        xbmc.log("Mezzmo Playback ended - LED OFF" , xbmc.LOGDEBUG)
 
    def onPlayBackStopped(self):
        contenturl = settings('contenturl')
        xbmc.log("contenturl " + contenturl)
        end = file.rfind('/') + 1
        objectID = file[end:]
        xbmc.log("Mezzmo Playback stopped at " + str(pos) + " in " + objectID, xbmc.LOGDEBUG)
        bookmark.SetBookmark(contenturl, objectID, str(pos))

             
player = XBMCPlayer()
 
monitor = xbmc.Monitor()
 
while True:
    if xbmc.Player().isPlaying():
        file = xbmc.Player().getPlayingFile()
        pos = int(xbmc.Player().getTime())
        
    count += 1
    if count % 1800 == 0 or count == 10:    # Update cache on Kodi start and every 30 mins
        if xbmc.Player().isPlaying():
            xbmc.log('A file is playing ' + str(count), xbmc.LOGNOTICE) 
        else:
            contenturl = settings('contenturl')
            sync.updateTexturesCache(contenturl) 

    if monitor.waitForAbort(1): # Sleep/wait for abort for 1 second.
        pin = settings('content_pin')
        settings('content_pin', '')
        url = settings('contenturl')
        ip = ''
        try:
            ip = socket.gethostbyname(socket.gethostname())
        except Exception as e:
            xbmc.log("gethostbyname exception: " + str(e))
            pass
        xbmc.log("SetContentRestriction Off: " + url)
        contentrestriction.SetContentRestriction(url, ip, 'false', pin)
        break # Abort was requested while waiting. Exit the while loop.