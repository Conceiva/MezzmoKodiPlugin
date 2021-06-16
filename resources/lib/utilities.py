import xbmc
import xbmcgui
import xbmcplugin
import os
import bookmark
import playcount
import xbmcaddon
from media import openNosyncDB
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
    autdialog = xbmcgui.Dialog()
    if sys.argv[2] == "clear":                                    # Ensure user really wants to clear autostart
        aumsg = "Are you sure you want to clear your curent Mezzmo addon autostart setting ?"
        cselect = autdialog.yesno('Mezzmo Autostart Clear', aumsg)
    else:                                                         # Confirm new autostart setting
        auplaylist = sys.argv[3]
        aumsg = "Confirm setting Mezzmo addon autostart to: \n\n" + auplaylist 
        cselect = autdialog.yesno('Mezzmo Autostart Setting', aumsg)
    if cselect == 1 :
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

def displayPerfStats():       
    pdfile = openNosyncDB()                                       #  Open Perf Stats database
    pdates = []
    curpf = pdfile.execute('SELECT DISTINCT psDate FROM mperfStats ORDER BY psDate DESC', )
    pstatdates = curpf.fetchall()                                 #  Get dates from database 
    if pstatdates:                                                #  If dates in performance database
        for rdate in pstatdates:
            x = str(rdate).replace("('","").replace("',)","")
            pdates.append(x)                                  #  Convert rows to list for dialog box
        ddialog = xbmcgui.Dialog()    
        vdate = ddialog.select('Select Mezzmo Performance Stats Date', pdates)
        xbmc.log('Mezzmo performance date selected is: ' + pdates[vdate], xbmc.LOGDEBUG)         

        curpf = pdfile.execute('SELECT * FROM mperfStats WHERE psDate=? ORDER BY psTime DESC', (pdates[vdate],))

        textval1 = "   Time   " +  "{:^18}".format("# of Items") + "{:<15}".format("Mezzmo Time") \
        + "{:<15}".format("Kodi Time") + "{:<15}".format("Total Time") +  "Items per sec " +      \
        "{:^28}".format("Playlist") +  "\n"   

        dialog = xbmcgui.Dialog()
        pstatslist = curpf.fetchall()

        if pstatslist and vdate >= 0:                            # Check for records in perfdb and not cancel
            for a in range(len(pstatslist)):                     # Display stats   
                perftime = pstatslist[a][1] + "     "
                ctitle = pstatslist[a][2]
                TotalMatches = pstatslist[a][3]
                pduration = pstatslist[a][4]
                sduration = pstatslist[a][5]
                tduration = pstatslist[a][6]
                displayrate = pstatslist[a][7]
                plist = "        " + ctitle[:36]
                if int(TotalMatches) < 10:
                    tmatches = "{:>10}".format(TotalMatches)
                elif int(TotalMatches) < 100:
                    tmatches = "{:>9}".format(TotalMatches)
                else:
                    tmatches = "{:>8}".format(TotalMatches)
                ptime = "{:>22}".format(pduration)
                stime = "{:>22}".format(sduration)
                ttime = "{:>22}".format(tduration)
                if displayrate.find(".") == 2:
                    drate = "{:>23}".format(displayrate)
                else:
                    drate = "{:>22}".format(displayrate) 
                textval1 = textval1 + "\n" + perftime + tmatches + stime + ptime + ttime + drate +  plist
            dialog.textviewer('Mezzmo Performance Stats for:  ' + pdates[vdate][5:] + "-" + \
            pdates[vdate][:4], textval1)
        elif vdate < 0:                                           # User cancel
            pdfile.close()
            return                                          
        else:                                                     # No records found for date selected   
            textval1 = "No Mezzmo addon performance stats found."
            dialog.textviewer('Mezzmo Performance Stats', textval1)  
            xbmc.log('Mezzmo performance stats found in database. ', xbmc.LOGNINFO)      
    else:                                                         # No performance records found 
        ddialog = xbmcgui.Dialog()
        textval1 = "No Mezzmo addon performance stats found."
        ddialog.textviewer('Mezzmo Performance Stats', textval1)    
    pdfile.close()


if sys.argv[1] == 'count':                                        # Playcount modification call
    playCount()
elif sys.argv[1] == 'auto':                                       # Set / Remove autostart
    autoStart()
elif sys.argv[1] == 'playm':                                      # Play music with bookmark
    playMusic()
elif sys.argv[1] == 'performance':                                # Display Performance stats
    displayPerfStats()
