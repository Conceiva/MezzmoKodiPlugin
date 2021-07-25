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
        contenturl = media.settings('contenturl')
        objectID = getObjectID(file)
        bmdelay = 15 - int(media.settings('bmdelay'))
        bookmark.SetBookmark(contenturl, objectID, str(pos + bmdelay))
        self.paflag = 1
 
    def onPlayBackResumed(self):
        file = self.getPlayingFile()
        xbmc.log("Mezzmo Playback resumed - LED ON" , xbmc.LOGDEBUG)
        self.paflag = 0
 
    def onPlayBackEnded(self):
        xbmc.log("Mezzmo Playback ended - LED OFF" , xbmc.LOGDEBUG)
        contenturl = media.settings('contenturl')
        objectID = getObjectID(file)
        pos = 0
        bookmark.SetBookmark(contenturl, objectID, str(pos))
        self.paflag = 0
 
    def onPlayBackStopped(self):
        contenturl = media.settings('contenturl')
        objectID = getObjectID(file)
        bmdelay = 15 - int(media.settings('bmdelay'))
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
            contenturl = media.settings('contenturl')
            objectID = getObjectID(file)
            bmdelay = 15 - int(media.settings('bmdelay'))            
            bookmark.SetBookmark(contenturl, objectID, str(pos + bmdelay))    
        
    count += 1
    if count == 2:                          # Check for autostarting the Mezzmo GUI
        media.autostart()

    pacount += 1 
    if pacount % 30 == 0:                   # Check for paused video every 30 seconds
        pastoptime = int(media.settings('pastop'))
        xbmc.log('Mezzmo count and stop time ' + str(pacount) + ' ' + str(pastoptime) +    \
        ' ' + str(player.paflag), xbmc.LOGDEBUG)
        if pastoptime > 0 and pacount >= pastoptime * 60 and player.paflag == 1:
            ptag = xbmc.Player().getVideoInfoTag()
            ptitle = media.displayTitles(ptag.getTitle())
            xbmc.Player().stop()
            pacount = 0
            mgenlog ='Mezzmo stopped paused playback: ' + ptitle +     \
            ' at: ' + time.strftime("%H:%M:%S", time.gmtime(pos))
            xbmc.log(mgenlog, xbmc.LOGINFO)
            mgenlog ='###' + ptitle
            media.mgenlogUpdate(mgenlog)
            mgenlog ='Mezzmo stopped paused playback at: ' + time.strftime("%H:%M:%S", time.gmtime(pos))
            media.mgenlogUpdate(mgenlog)   
        elif player.paflag == 0:
            pacount = 0

    if count % 1800 == 0 or count == 10:    # Update cache on Kodi start and every 30 mins
        if xbmc.Player().isPlayingVideo():
            ptag = xbmc.Player().getVideoInfoTag()
            ptitle = media.displayTitles(ptag.getTitle())
            mgenlog ='A video file is playing: ' + ptitle + ' at: ' +        \
            time.strftime("%H:%M:%S", time.gmtime(pos))
            xbmc.log(mgenlog, xbmc.LOGINFO)
            mgenlog ='###' + ptitle
            media.mgenlogUpdate(mgenlog)
            mgenlog ='A video file is playing at: ' + time.strftime("%H:%M:%S", time.gmtime(pos))
            media.mgenlogUpdate(mgenlog)     
        elif xbmc.Player().isPlayingAudio():
            ptag = xbmc.Player().getMusicInfoTag()
            ptitle = media.displayTitles(ptag.getTitle())
            mgenlog ='A music file is playing: ' + ptitle + ' at: ' +        \
            time.strftime("%H:%M:%S", time.gmtime(pos))
            xbmc.log(mgenlog, xbmc.LOGINFO)
            mgenlog ='###' + ptitle
            media.mgenlogUpdate(mgenlog)
            mgenlog ='A music file is playing at: ' + time.strftime("%H:%M:%S", time.gmtime(pos))
            media.mgenlogUpdate(mgenlog)                
        else:
            contenturl = media.settings('contenturl')
            sync.updateTexturesCache(contenturl)

    if count % 3600 == 0 or count == 11:    # Mezzmo sync process
        if xbmc.Player().isPlaying():
            msynclog = 'Mezzmo sync skipped. A video is playing.'
            xbmc.log(msynclog, xbmc.LOGINFO)
            media.mezlogUpdate(msynclog)
        else:
            syncpin = media.settings('content_pin')
            syncurl = media.settings('contenturl')           
            if syncpin and syncurl:       
                sync.syncMezzmo(syncurl, syncpin, count)
                del syncpin, syncurl

    if count > 86419:                      # Reset counter daily
        count = 20

    if monitor.waitForAbort(1): # Sleep/wait for abort for 1 second.
        try:
            pin = media.settings('content_pin')
            media.settings('content_pin', '')
            url = media.settings('contenturl')
        except:
            pass
        ip = ''
        try:
            ip = socket.gethostbyname(socket.gethostname())
        except Exception as e:
            xbmc.log("gethostbyname exception: " + str(e))
            pass
        try:
            xbmc.log("SetContentRestriction Off: " + url)
            contentrestriction.SetContentRestriction(url, ip, 'false', pin)
            sync.dbClose()
            del pin, url, player, monitor, ptag, ptitle, pastoptime
            del contenturl, pos, file, pacount, player.paflag, bmdelay
            mgenlog ='Mezzmo addon shutdown.'
            xbmc.log(mgenlog, xbmc.LOGINFO)
            media.mgenlogUpdate(mgenlog)  
        except:
            pass
            
        break # Abort was requested while waiting. Exit the while loop.

