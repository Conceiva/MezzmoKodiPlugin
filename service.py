import xbmc
import time
import xbmcaddon
from common import GLOBAL_SETUP  #Needed first to setup import locations
import bookmark

pos = 0
file = ''

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
        xbmc.log("Playback started - " + file)
 
    def onPlayBackPaused(self):
        xbmc.log("Playback paused - LED OFF")
 
    def onPlayBackResumed(self):
        file = self.getPlayingFile()
        xbmc.log("Playback resumed - LED ON")
 
    def onPlayBackEnded(self):
        xbmc.log("Playback ended - LED OFF")
 
    def onPlayBackStopped(self):
        contenturl = settings('contenturl')
        xbmc.log("contenturl " + contenturl)
        end = file.rfind('/') + 1
        objectID = file[end:]
        xbmc.log("Playback stopped at " + str(pos) + " in " + objectID)
        bookmark.SetBookmark(contenturl, objectID, str(pos))
        
player = XBMCPlayer()
 
monitor = xbmc.Monitor()
 
while True:
    if xbmc.Player().isPlaying():
        file = xbmc.Player().getPlayingFile()
        pos = long(xbmc.Player().getTime())
        
    if monitor.waitForAbort(1): # Sleep/wait for abort for 1 second.
        break # Abort was requested while waiting. Exit the while loop.