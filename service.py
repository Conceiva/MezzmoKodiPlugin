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
pacount = 0

def settings(setting, value = None):
    # Get or add addon setting
    addon = xbmcaddon.Addon()
    if value:
        addon.setSetting(setting, value)
    else:
        return addon.getSetting(setting)

def getObjectID(file):
    end = file.rfind('/') + 1
    objectID = file[end:]
    return(objectID)  
   
class XBMCPlayer(xbmc.Player):
    
    def __init__(self, *args):
        self.paflag = 0
        pass
 
    def onPlayBackStarted(self):
        file = xbmc.Player().getPlayingFile()
        xbmc.log("Mezzmo Playback started - " + file, xbmc.LOGDEBUG)
        self.paflag = 0
 
    def onPlayBackPaused(self):
        xbmc.log("Mezzmo Playback paused - LED OFF" , xbmc.LOGDEBUG)
        contenturl = settings('contenturl')
        objectID = getObjectID(file)
        bmdelay = 15 - int(settings('bmdelay'))
        bookmark.SetBookmark(contenturl, objectID, str(pos + bmdelay))
        self.paflag = 1
 
    def onPlayBackResumed(self):
        file = self.getPlayingFile()
        xbmc.log("Mezzmo Playback resumed - LED ON" , xbmc.LOGDEBUG)
        self.paflag = 0
 
    def onPlayBackEnded(self):
        xbmc.log("Mezzmo Playback ended - LED OFF" , xbmc.LOGDEBUG)
        contenturl = settings('contenturl')
        objectID = getObjectID(file)
        pos = 0
        bookmark.SetBookmark(contenturl, objectID, str(pos))
        self.paflag = 0
 
    def onPlayBackStopped(self):
        contenturl = settings('contenturl')
        objectID = getObjectID(file)
        bmdelay = 15 - int(settings('bmdelay'))
        xbmc.log("Mezzmo Playback stopped at " + str(pos  + bmdelay) + " in " + objectID, xbmc.LOGDEBUG)
        bookmark.SetBookmark(contenturl, objectID, str(pos + bmdelay))
        self.paflag = 0

             
player = XBMCPlayer()
 
monitor = xbmc.Monitor()

media.checkNosyncDB()                       # Check nosync database            
 
while True:
    if xbmc.Player().isPlaying():
        file = xbmc.Player().getPlayingFile()
        pos = int(xbmc.Player().getTime())
        if count % 30 == 0:                 # Update bookmark once every 30 seconds during playback
            contenturl = settings('contenturl')
            objectID = getObjectID(file)
            bmdelay = 15 - int(settings('bmdelay'))            
            bookmark.SetBookmark(contenturl, objectID, str(pos + bmdelay))    
        
    count += 1
    if count == 2:                          # Check for autostarting the Mezzmo GUI
        media.autostart()

    pacount += 1 
    if pacount % 30 == 0:                   # Check for paused video every 30 seconds
        pastoptime = int(settings('pastop'))
        xbmc.log('Mezzmo count and stop time ' + str(pacount) + ' ' + str(pastoptime) +    \
        ' ' + str(player.paflag), xbmc.LOGDEBUG)
        if pastoptime > 0 and pacount >= pastoptime * 60 and player.paflag == 1:
            ptag = xbmc.Player().getVideoInfoTag()
            ptitle = media.displayTitles(ptag.getTitle())
            xbmc.log('Mezzmo stopped paused playback: ' + ptitle + ' at: ' + \
            time.strftime("%H:%M:%S", time.gmtime(pos)), xbmc.LOGINFO)
            xbmc.Player().stop()
            pacount = 0
        elif player.paflag == 0:
            pacount = 0

    if count % 1800 == 0 or count == 10:    # Update cache on Kodi start and every 30 mins
        if xbmc.Player().isPlayingVideo():
            ptag = xbmc.Player().getVideoInfoTag()
            ptitle = media.displayTitles(ptag.getTitle())
            xbmc.log('A video file is playing: ' + ptitle + ' at: ' +        \
            time.strftime("%H:%M:%S", time.gmtime(pos)), xbmc.LOGINFO)
        elif xbmc.Player().isPlayingAudio():
            ptag = xbmc.Player().getMusicInfoTag()
            ptitle = media.displayTitles(ptag.getTitle())
            xbmc.log('A music file is playing: ' + ptitle + ' at: ' +  \
            time.strftime("%H:%M:%S", time.gmtime(pos)), xbmc.LOGINFO)                 
        else:
            contenturl = settings('contenturl')
            sync.updateTexturesCache(contenturl)

    if count % 3600 == 0 or count == 11:    # Mezzmo sync process
        if xbmc.Player().isPlaying():
            xbmc.log('Mezzmo sync skipped. A video is playing.', xbmc.LOGINFO)
        else:
            syncpin = settings('content_pin')
            syncurl = settings('contenturl') 
            ksync = settings('kodisync')           
            if syncpin and syncurl:       
                sync.syncMezzmo(syncurl, syncpin, count, ksync)
                del syncpin
                del syncurl
            if ksync:
                del ksync

    if count > 86419:                      # Reset counter daily
        count = 20

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
        if pin and url:    
            del pin
            del url              
        break # Abort was requested while waiting. Exit the while loop.