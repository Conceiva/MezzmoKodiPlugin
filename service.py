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
        xbmc.log("Playback started - " + file)
        self.paflag = 0
 
    def onPlayBackPaused(self):
        xbmc.log("Playback paused - LED OFF")
        contenturl = media.settings('contenturl')
        objectID = getObjectID(file)
        bmdelay = 15 - int(media.settings('bmdelay'))
        bookmark.SetBookmark(contenturl, objectID, str(pos + bmdelay))
        self.paflag = 1
 
    def onPlayBackResumed(self):
        file = self.getPlayingFile()
        xbmc.log("Playback resumed - LED ON")
        self.paflag = 0
 
    def onPlayBackEnded(self):
        xbmc.log("Playback ended - LED OFF")
        contenturl = media.settings('contenturl')
        objectID = getObjectID(file)
        pos = 0
        bookmark.SetBookmark(contenturl, objectID, str(pos))
        self.paflag = 0
 
    def onPlayBackStopped(self):
        contenturl = media.settings('contenturl')
        objectID = getObjectID(file)
        bmdelay = 15 - int(media.settings('bmdelay'))
        xbmc.log("Playback stopped at " + str(pos  + bmdelay) + " in " + objectID)
        bookmark.SetBookmark(contenturl, objectID, str(pos + bmdelay))
        self.paflag = 0

             
player = XBMCPlayer()
 
monitor = xbmc.Monitor()

media.checkNosyncDB()                       # Check nosync database                      

while True:
    if xbmc.Player().isPlaying():
        file = xbmc.Player().getPlayingFile()
        pos = long(xbmc.Player().getTime())
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
        xbmc.log('Mezzmo count and stop time ' + str(pacount) + ' ' + str(pastoptime) +        \
        ' ' + str(player.paflag), xbmc.LOGDEBUG)
        if pastoptime > 0 and pacount >= pastoptime * 60 and player.paflag == 1:
            ptag = xbmc.Player().getVideoInfoTag()
            ptitle = media.displayTitles(ptag.getTitle().decode('utf-8','ignore'))
            xbmc.Player().stop()
            pacount = 0
            mgenlog ='Mezzmo stopped paused playback: ' + ptitle.encode('utf-8','ignore') +     \
            ' at: ' + time.strftime("%H:%M:%S", time.gmtime(pos))
            xbmc.log(mgenlog, xbmc.LOGNOTICE)
            mgenlog ='###' + ptitle.encode('utf-8','ignore')
            media.mgenlogUpdate(mgenlog)
            mgenlog ='Mezzmo stopped paused playback at: ' + time.strftime("%H:%M:%S", time.gmtime(pos))
            media.mgenlogUpdate(mgenlog)   
        elif player.paflag == 0:
            pacount = 0
 
    if count % 1800 == 0 or count == 10:    # Update cache on Kodi start and every 30 mins
        if xbmc.Player().isPlayingVideo():
            ptag = xbmc.Player().getVideoInfoTag()
            ptitle = media.displayTitles(ptag.getTitle().decode('utf-8','ignore'))
            mgenlog ='A video file is playing: ' + ptitle.encode('utf-8','ignore') + ' at: ' +  \
            time.strftime("%H:%M:%S", time.gmtime(pos))
            xbmc.log(mgenlog, xbmc.LOGNOTICE)
            mgenlog ='###' + ptitle.encode('utf-8','ignore')
            media.mgenlogUpdate(mgenlog)
            mgenlog ='A video file is playing at: ' + time.strftime("%H:%M:%S", time.gmtime(pos))
            media.mgenlogUpdate(mgenlog)  
        elif xbmc.Player().isPlayingAudio():
            ptag = xbmc.Player().getMusicInfoTag()
            ptitle = media.displayTitles(ptag.getTitle().decode('utf-8','ignore'))               
            mgenlog ='A music file is playing: ' + ptitle.encode('utf-8','ignore') + ' at: ' +  \
            time.strftime("%H:%M:%S", time.gmtime(pos))
            xbmc.log(mgenlog, xbmc.LOGNOTICE)
            mgenlog ='###' + ptitle.encode('utf-8','ignore')
            media.mgenlogUpdate(mgenlog)
            mgenlog ='A music file is playing at: ' + time.strftime("%H:%M:%S", time.gmtime(pos))
            media.mgenlogUpdate(mgenlog) 
        else:
            contenturl = media.settings('contenturl')
            sync.updateTexturesCache(contenturl)

    if count % 3600 == 0 or count == 11:    # Mezzmo sync process
        if xbmc.Player().isPlayingVideo():
            msynclog = 'Mezzmo sync skipped. A video is playing.'
            xbmc.log(msynclog, xbmc.LOGNOTICE)
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
        except:
            pass
        mgenlog ='Mezzmo addon shutdown.'
        xbmc.log(mgenlog, xbmc.LOGNOTICE)
        media.mgenlogUpdate(mgenlog)  
        
        break # Abort was requested while waiting. Exit the while loop.

