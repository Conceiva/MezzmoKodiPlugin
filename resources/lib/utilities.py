import xbmc
import xbmcgui
import xbmcplugin
import os
import bookmark
import playcount
import xbmcaddon
from datetime import datetime, timedelta

addon = xbmcaddon.Addon()


def playCount():
    title = sys.argv[2]                                          # Extract passed variables
    vurl = sys.argv[3]
    vseason = sys.argv[4]
    vepisode = sys.argv[5]
    mplaycount = sys.argv[6]
    series = sys.argv[7]
    dbfile = sys.argv[8]
    contenturl = sys.argv[9]

    if dbfile != 'audiom':                                        #  Don't update Kodi for music
        playcount.updateKodiPlaycount(int(mplaycount), title, vurl, int(vseason),     \
        int(vepisode), series, dbfile)                            #  Update Kodi DB playcount

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
    xbmc.log('Mezzmo autostart set to: ' + str(sys.argv[2]), xbmc.LOGINFO)      
    xbmc.executebuiltin('Container.Refresh()')    


def playMusic():
    itemurl = sys.argv[2]                                         # Extract passed variables
    listItem = sys.argv[3]
    mtitle = sys.argv[4]
    micon = sys.argv[5]
    mbackdropurl = sys.argv[6]
    mbookmark = int(sys.argv[7])
    lim=xbmcgui.ListItem(listItem)
    lim.setInfo('music', {'Title': mtitle, })
    lim.setArt({'thumb': micon, 'poster': micon, 'fanart': mbackdropurl})
    xbmc.Player().play(item=itemurl, listitem=lim)
    waitTime = 1
    while True:                                                   # Wait for player to set seek time
        if (xbmc.Player().isPlaying() == 0) and (waitTime < 5): 
            waitTime += 1
            xbmc.sleep(500)
        elif (xbmc.Player().isPlaying() == 1) or (waitTime >= 5): # only wait 2.5 seconds
            xbmc.sleep(300)
            try:
                xbmc.Player().seekTime(mbookmark)
                xbmc.log('Mezzmo player seek time: ' + str(mbookmark), xbmc.LOGDEBUG)
            except:
                pass
            break 


if sys.argv[1] == 'count':                                        # Playcount modification call
    playCount()
elif sys.argv[1] == 'auto':                                       # Set / Remove autostart
    autoStart()
elif sys.argv[1] == 'playm':                                      # Play music with bookmark
    playMusic()

