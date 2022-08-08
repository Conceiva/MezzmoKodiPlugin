import xbmc
import time
import xbmcaddon
from common import GLOBAL_SETUP  #Needed first to setup import locations
import bookmark
import socket
import contentrestriction
import sync
import media
from server import checkSync, getContentURL

pos =  0
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
        self.mtitle = ''
        pass
 
    def onPlayBackStarted(self):
        try:
            file = xbmc.Player().getPlayingFile()
            xbmc.sleep(2000)
            if xbmc.Player().isPlayingVideo():
                finfo = xbmc.Player().getVideoInfoTag()
                self.mtitle = media.displayTitles(finfo.getTitle())
            if xbmc.Player().isPlayingAudio():
                finfo = xbmc.Player().getMusicInfoTag()
                self.mtitle = media.displayTitles(finfo.getTitle())
            xbmc.log("Playback started - " + file , xbmc.LOGDEBUG)
        except:
            file = 'File playing is not video or audio'
            pass
        self.paflag = 0
 
    def onPlayBackPaused(self):
        xbmc.log("Mezzmo Playback paused - LED OFF" , xbmc.LOGDEBUG)
        contenturl = media.settings('contenturl')
        manufacturer = getContentURL(contenturl)
        objectID = getObjectID(file)
        bmdelay = 15 - int(media.settings('bmdelay'))
        if len(contenturl) > 5 and 'Conceiva' in manufacturer and 'cva_extract' not in file: # Ensure Mezzmo server has been selected
            bookmark.SetBookmark(contenturl, objectID, str(pos + bmdelay))
            if media.getMServer(contenturl) in file:     #  Check for paused Mezzmo files
                self.paflag = 1
                bookmark.updateKodiBookmark(objectID, pos + bmdelay - 15, self.mtitle)
 
    def onPlayBackResumed(self):
        try:
            file = self.getPlayingFile()
            xbmc.log("Mezzmo Playback resumed - LED ON" , xbmc.LOGDEBUG)
        except:
            file = 'File playing is not video or audio'
            pass
        self.paflag = 0
 
    def onPlayBackEnded(self):
        xbmc.log("Mezzmo Playback ended - LED OFF" , xbmc.LOGDEBUG)
        contenturl = media.settings('contenturl')
        manufacturer = getContentURL(contenturl)
        objectID = getObjectID(file)
        pos = 0
        self.paflag = 0
        if len(contenturl) > 5 and 'Conceiva' in manufacturer and 'cva_extract' not in file: # Ensure Mezzmo server has been selected
            bookmark.SetBookmark(contenturl, objectID, str(pos))
            bookmark.updateKodiBookmark(objectID, pos, self.mtitle)
 
    def onPlayBackStopped(self):
        contenturl = media.settings('contenturl')
        manufacturer = getContentURL(contenturl)
        objectID = getObjectID(file)
        bmdelay = 15 - int(media.settings('bmdelay'))
        xbmc.log("Mezzmo Playback stopped at " + str(pos  + bmdelay) + " in " + objectID, xbmc.LOGDEBUG)
        self.paflag = 0
        if len(contenturl) > 5 and 'Conceiva' in manufacturer and 'cva_extract' not in file: # Ensure Mezzmo server has been selected
            bookmark.SetBookmark(contenturl, objectID, str(pos + bmdelay))
            bookmark.updateKodiBookmark(objectID, pos + bmdelay - 15, self.mtitle)
             
player = XBMCPlayer()
 
monitor = xbmc.Monitor()

media.checkNosyncDB()                       # Check nosync database            
 
while True:
    if xbmc.Player().isPlaying():
        try:
            file = xbmc.Player().getPlayingFile()
            pos = int(xbmc.Player().getTime())
            if count % 30 == 0:                 # Update bookmark once every 30 seconds during playback
                contenturl = media.settings('contenturl')
                manufacturer = getContentURL(contenturl)
                objectID = getObjectID(file)
                bmdelay = 15 - int(media.settings('bmdelay'))
                if contenturl != 'none' and 'Conceiva' in manufacturer and 'cva_extract' not in file:   # Ensure Mezzmo server has been selected            
                    bookmark.SetBookmark(contenturl, objectID, str(pos + bmdelay))   
                    if xbmc.Player().isPlayingVideo():
                        finfo = xbmc.Player().getVideoInfoTag()
                        mtitle = media.displayTitles(finfo.getTitle()) 
                        bookmark.updateKodiBookmark(objectID, pos + bmdelay - 15, mtitle)
                    if xbmc.Player().isPlayingAudio():
                        finfo = xbmc.Player().getMusicInfoTag()
                        mtitle = media.displayTitles(finfo.getTitle()) 
                        bookmark.updateKodiBookmark(objectID, pos + bmdelay - 15, mtitle)
        except:
            mgenlog ='Mezzmo problem saving bookmark.'
            xbmc.log(mgenlog, xbmc.LOGINFO)
            media.mgenlogUpdate(mgenlog)
        
    count += 1
    if count == 2:                          # Check for autostarting the Mezzmo GUI
        media.autostart()

    pacount += 1 
    if pacount % 30 == 0:                   # Check for paused video every 30 seconds
        pastoptime = int(media.settings('pastop'))
        xbmc.log('Mezzmo count and stop time ' + str(pacount) + ' ' + str(pastoptime) +    \
        ' ' + str(player.paflag), xbmc.LOGDEBUG)
        try:
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
        except:
            pass 

    if count % 1800 == 0 or count == 10:    # Update cache on Kodi start and every 30 mins
        contenturl = media.settings('contenturl')
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
        elif contenturl == 'none':
            mgenlog ='Mezzmo no servers selected yet.  Cache update process skipped.'
            xbmc.log(mgenlog, xbmc.LOGINFO)
            media.mgenlogUpdate(mgenlog)
        else:
            sync.updateTexturesCache(contenturl)

    if count % 3600 == 0 or count == 11:    # Mezzmo sync process
        if xbmc.Player().isPlaying():
            msynclog = 'Mezzmo sync skipped. A video is playing.'
            xbmc.log(msynclog, xbmc.LOGINFO)
            media.mezlogUpdate(msynclog)
        else:
            syncpin = media.settings('content_pin')
            syncset = media.settings('kodisyncvar')
            syncurl = checkSync()           # Get server control URL
            xbmc.log('Mezzmo contenturl is: ' + str(syncurl), xbmc.LOGDEBUG)                       
            if syncpin and syncset != 'Off' and syncurl != 'None':
                try:             
                    sync.syncMezzmo(syncurl, syncpin, count)
                except:
                    msynclog ='Mezzmo sync process failed with an exception error.'
                    xbmc.log(msynclog, xbmc.LOGINFO)
                    media.mezlogUpdate(msynclog)    
                    pass            
            elif syncset != 'Off' and syncurl == 'None':  # Ensure Mezzmo server has been selected 
                msynclog ='Mezzmo no servers selected yet.  Mezzmo sync skipped.'
                xbmc.log(msynclog, xbmc.LOGINFO)
                media.mezlogUpdate(msynclog)

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
            del pin, url, player, monitor, ptag, ptitle, pastoptime, GLOBAL_SETUP
            del contenturl, pos, file, pacount, player.paflag, bmdelay
            mgenlog = 'Mezzmo addon service shutdown.'
            xbmc.log(mgenlog, xbmc.LOGINFO)
            media.mgenlogUpdate(mgenlog)
        except:
            pass
            
        break # Abort was requested while waiting. Exit the while loop.

