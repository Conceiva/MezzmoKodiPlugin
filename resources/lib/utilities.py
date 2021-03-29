import xbmc
import xbmcgui
import xbmcplugin
import os
import bookmark
import xbmcaddon
import playcount
from datetime import datetime, timedelta

#xbmc.log('Name of script: ' + str(sys.argv[0]), xbmc.LOGNOTICE)
#xbmc.log('Number of arguments: ' + str(len(sys.argv)), xbmc.LOGNOTICE)
#xbmc.log('The arguments are: ' + str(sys.argv), xbmc.LOGNOTICE)

addon = xbmcaddon.Addon()

def playCount():
    title = sys.argv[2]                                           # Extract passed variables
    vurl = sys.argv[3]
    vseason = sys.argv[4]
    vepisode = sys.argv[5]
    mplaycount = sys.argv[6]
    series = sys.argv[7]
    dbfile = sys.argv[8]
    contenturl = sys.argv[9]

    title = title.decode('utf-8', 'ignore')   			  #  Handle commas
    series = series.decode('utf-8', 'ignore')    		  #  Handle commas

    playcount.updateKodiPlaycount(int(mplaycount), title, vurl,     \
    int(vseason), int(vepisode), series, dbfile)                  #  Update Kodi DB playcount

    rtrimpos = vurl.rfind('/')
    mobjectID = vurl[rtrimpos+1:]                                 #  Get Mezzmo objectID

    if int(mplaycount) == 0:                                      #  Calcule new play count
        newcount = '1'
    elif int(mplaycount) > 0:
        newcount = '0'

    if mobjectID != None:                                         #  Update Mezzmo playcount if objectID exists
        playcount.setPlaycount(contenturl, mobjectID, newcount, title)
        bookmark.SetBookmark(contenturl, mobjectID, '0')          #  Clear bookmark
        xbmc.executebuiltin('Container.Refresh()')

def autoStart():

    addon.setSetting('autostart', sys.argv[2])
    xbmc.log('Mezzmo autostart set to: ' + str(sys.argv[2]), xbmc.LOGNOTICE)      
    xbmc.executebuiltin('Container.Refresh()')    


if sys.argv[1] == 'count':                                        # Playcount modification call
    playCount()
elif sys.argv[1] == 'auto':                                       # Set / Remove autostart
    autoStart()

