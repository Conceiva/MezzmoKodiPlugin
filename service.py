import xbmc
import time
import xbmcaddon
from common import GLOBAL_SETUP  #Needed first to setup import locations
import bookmark
import socket
import contentrestriction
import sync
import media

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

    count += 1
    if count % 1800 == 0 or count == 10:    # Update cache on Kodi start and every 30 mins
        if xbmc.Player().isPlaying():
            xbmc.log('A file is playing: ' + file.encode('utf-8','ignore'), xbmc.LOGNOTICE) 
        else:
            contenturl = settings('contenturl')
            sync.updateTexturesCache(contenturl)

    if count % 3600 == 0 or count == 11:    # Mezzmo sync process
        if xbmc.Player().isPlaying():
            xbmc.log('Mezzmo sync skipped. A video is playing.', xbmc.LOGNOTICE)
        else:
            syncpin = settings('content_pin')
            syncurl = settings('contenturl') 
            ksync = settings('kodisync')             
            if syncpin and syncurl:       
                sync.syncMezzmo(syncurl, syncpin, count, ksync)
            del syncpin
            del syncurl
            del ksync
    
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
        sync.dbClose()    
        del pin
        del url         
        break # Abort was requested while waiting. Exit the while loop.