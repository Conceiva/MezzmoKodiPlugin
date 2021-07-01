import xbmc
import xbmcgui
import xbmcplugin
import os
import bookmark
import xbmcaddon
import playcount
from media import openNosyncDB, get_installedversion
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
        auplaylist = sys.argv[3].encode('utf-8', 'ignore')
        aumsg = "Confirm setting Mezzmo addon autostart to: \n\n" + auplaylist 
        cselect = autdialog.yesno('Mezzmo Autostart Setting', aumsg)
    if cselect == 1 :
        addon.setSetting('autostart', sys.argv[2])
        xbmc.log('Mezzmo autostart set to: ' + str(sys.argv[2]), xbmc.LOGNOTICE)      
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
    if int(get_installedversion()) < 18:                      # Textviewer function added in Kodi 18
        dialog_text = "Mezzmo Logs & Performance Stats are only available in Kodi version 18 and higher."
        xbmcgui.Dialog().ok("Mezzmo Logs & Performance Stats", dialog_text)
        return       
    pdfile = openNosyncDB()                                   # Open Perf Stats database
    pdates = []
    plists = []
    pselect = []
    curpf = pdfile.execute('SELECT DISTINCT psDate FROM mperfStats ORDER BY psDate DESC', )
    pstatdates = curpf.fetchall()                             # Get dates from database
    pselect = ["Duplicate Video Logs", "All Sync Logs", "Sync Logs By Day"]
    if pstatdates:                                            # If dates in performance database
        pselect.insert(3, "All Performance Logs")
        pselect.insert(4, "Performance By Playlist")
        pselect.insert(5, "Performance By Date")
    ddialog = xbmcgui.Dialog()    
    vdate = ddialog.select('Select Mezzmo Logs or Stats View', pselect)
    xbmc.log('Mezzmo performance selection is: ' + pselect[vdate], xbmc.LOGDEBUG)    

    if vdate < 0:                                             # User cancel
        pdfile.close()
        return      
    elif (pselect[vdate]) == "All Performance Logs":          # Display all performance records
        curpf = pdfile.execute('SELECT * FROM mperfStats ORDER BY psDate DESC, psTime DESC',)
        headval = 'Mezzmo Performance Stats for:  ' + pselect[vdate]
    elif (pselect[vdate]) == "Duplicate Video Logs":
        displayDupeLogs()
        pdfile.close()
        return
    elif (pselect[vdate]) == "All Sync Logs" or (pselect[vdate]) == "Sync Logs By Day":
        displaySyncLogs(pselect[vdate])
        pdfile.close()
        return
    elif (pselect[vdate]) == "Performance By Playlist":       # Select Playlist to display
        curpf = pdfile.execute('SELECT DISTINCT psPlaylist FROM mperfStats ORDER BY psPlaylist ASC', )
        pstatlists = curpf.fetchall()                         # Get playlists from database
        for rlist in pstatlists:
            x = str(rlist).replace("('","").replace("',)","")
            plists.append(x[3:])                              # Convert rows to list for dialog box
        vdate = ddialog.select('Select Mezzmo Performance Stats Playlist', plists)
        if vdate < 0:                                         # User cancel
            pdfile.close()
            return
        curpf = pdfile.execute('SELECT * FROM mperfStats WHERE psPlaylist=? ORDER BY psDate DESC,              \
        psTime DESC', (plists[vdate],))
        headval = 'Mezzmo Performance Stats for:  ' + plists[vdate]         
    elif (pselect[vdate]) == "Performance By Date":           # Select Date to display:
        for rdate in pstatdates:
            x = str(rdate).replace("('","").replace("',)","")
            pdates.append(x[3:])                              # Convert rows to list for dialog box
        vdate = ddialog.select('Select Mezzmo Performance Stats Date', pdates)
        if vdate < 0:                                         # User cancel
            pdfile.close()
            return
        curpf = pdfile.execute('SELECT * FROM mperfStats WHERE psDate=? ORDER BY psTime DESC', (pdates[vdate],))
        headval = 'Mezzmo Performance Stats for:  ' + pdates[vdate][5:] + "-" + \
        pdates[vdate][:4]

    textval1 = "{:^25}".format("Time") + "{:^21}".format("# of") + "{:<15}".format("Mezzmo") + "{:<15}".format("Kodi")   \
    + "{:<11}".format("Total") +  "Items per" + "{:>24}".format("Playlist") +  "\n" + "{:>41}".format("Items")  \
    + "{:>14}".format("Time") + "{:>16}".format("Time") + "{:>16}".format("Time") + "{:>13}".format("sec") + "\n" 
    dialog = xbmcgui.Dialog()
    pstatslist = curpf.fetchall()

    if pstatslist and vdate >= 0:                            # Check for records in perfdb and not cancel
        for a in range(len(pstatslist)):                     # Display stats   
            perfdate = pstatslist[a][0]
            perfdate = perfdate[5:].replace("-", "/") + "   "
            perftime = pstatslist[a][1] + "     "
            ctitle = pstatslist[a][2]
            TotalMatches = pstatslist[a][3]
            pduration = pstatslist[a][4]
            sduration = pstatslist[a][5]
            tduration = pstatslist[a][6]
            displayrate = pstatslist[a][7]
            plist = "        " + ctitle[:24]                 # Limit playlist name to 24 chars to stop wrapping
            if int(TotalMatches) < 10:
                tmatches = "{:>10}".format(TotalMatches)
            elif int(TotalMatches) < 100:
                tmatches = "{:>9}".format(TotalMatches)
            else:
                tmatches = "{:>8}".format(TotalMatches)
            ptime = "{:>16}".format(pduration)
            stime = "{:>16}".format(sduration)
            ttime = "{:>16}".format(tduration)
            if displayrate.find(".") == 2:
                drate = "{:>17}".format(displayrate)
            else:
                drate = "{:>16}".format(displayrate) 
            textval1 = textval1 + "\n" + perfdate + perftime + tmatches + stime + ptime + ttime + drate +  plist
        dialog.textviewer(headval, textval1)
                                       
    else:                                                   # No records found for date selected   
        textval1 = "No Mezzmo addon performance stats found."
        dialog.textviewer('Mezzmo Performance Stats', textval1)  
        xbmc.log('Mezzmo no performance stats found in database. ', xbmc.LOGNOTICE)       
    pdfile.close()


def displayDupeLogs():
   
    dlfile = openNosyncDB()                                       # Open Dupe logs database

    curdl = dlfile.execute('SELECT * FROM dupeTrack ORDER BY dtDate DESC',)
    dllogs = curdl.fetchall()                                     # Get dupe logs from database

    textval1 = "{:^25}".format("Date") + "{:^21}".format("Record #") + "{:>32}".format(" Duplicate Playlist")
    textval1 = textval1 + "\n" 
    headval = "Mezzmo Duplicate Video Logs"
    dialog = xbmcgui.Dialog()

    if dllogs:
        for a in range(len(dllogs)):                             # Display logs if exist   
            dldate = dllogs[a][0]
            recnumb = dllogs[a][1]
            ctitle = "                " + dllogs[a][3]
            dldate = "{:>16}".format(dldate)
            if int(recnumb) < 10:
                frecnumb = "{:>16}".format(recnumb)
            elif int(recnumb) < 100:
                frecnumb = "{:>15}".format(recnumb)
            elif int(recnumb) < 1000:
                frecnumb = "{:>14}".format(recnumb)
            else :
                frecnumb = "{:>13}".format(recnumb)
            textval1 = textval1 + "\n" + dldate + frecnumb + ctitle[:64]
        dialog.textviewer(headval, textval1)                                     
    else:                                                        # No records found for date selected   
        textval1 = "No Mezzmo duplicate logs found."
        dialog.textviewer(headval, textval1)
        xbmc.log('Mezzmo no dupe logs found in database. ', xbmc.LOGNOTICE)                
    dlfile.close()


def displaySyncLogs(syncSelect):

    dsfile = openNosyncDB()                                       # Open Sync logs database

    msdates = []
    msdialog = xbmcgui.Dialog()
    if syncSelect == "All Sync Logs":
        cursync = dsfile.execute('SELECT * FROM msyncLog ORDER BY msDate DESC, msTime DESC',)
        headval = "Mezzmo All Sync Logs"     
    elif syncSelect == "Sync Logs By Day":
        cursync = dsfile.execute('SELECT DISTINCT msDate FROM msyncLog ORDER BY msDate DESC', )
        mstatdates = cursync.fetchall()                           # Get dates from database
        if mstatdates:        
            for rdate in mstatdates:
                x = str(rdate).replace("('","").replace("',)","")
                msdates.append(x[3:])                             # Convert rows to list for dialog box
            mdate = msdialog.select('Select Sync Logs Date', msdates)
            if mdate < 0:                                         # User cancel
                dsfile.close()
                return
            else:                                                 # Get records for selected date
                cursync = dsfile.execute('SELECT * FROM msyncLog WHERE msDate=? ORDER BY msTime DESC', \
                (msdates[mdate],))
                headval = 'Mezzmo Sync Logs for:  ' + msdates[mdate][5:] + "-" + msdates[mdate][:4]
        else:                                                     # No sync logs found for date selected
            textval1 = "No Mezzmo sync logs found."               # Should never happen. Safety check 
            msdialog.textviewer("Mezzmo Sync Logs", textval1)            
            dsfile.close()
            return        

    mslogs = cursync.fetchall()                                   # Get sync logs from database
    textval1 = "{:^38}".format("Date") + "{:>32}".format("Sync Log Message")
    textval1 = textval1 + "\n" 

    if mslogs:
        for a in range(len(mslogs)):                              # Display logs if exist   
            msdate = mslogs[a][0]
            mstime = mslogs[a][1][:8]                             # Strip off milliseconds
            msdatetime = msdate + "   " + mstime + "      "
            msynclog = mslogs[a][2]
            textval1 = textval1 + "\n" + msdatetime + msynclog
        msdialog.textviewer(headval, textval1)                                     
    else:                                                         # No records found for date selected   
        textval1 = "No Mezzmo Sync logs found."                   # Should never happen. Safety check
        msdialog.textviewer(headval, textval1)
    dsfile.close()


def containerRefresh():                                           # Refresh container 
    addon.setSetting('refreshflag', '1')                          # Set refresh flag for perf monitoring
    xbmc.executebuiltin('Container.Refresh()')

 
if sys.argv[1] == 'count':                                        # Playcount modification call
    playCount()
elif sys.argv[1] == 'auto':                                       # Set / Remove autostart
    autoStart()
elif sys.argv[1] == 'playm':                                      # Play music with bookmark
    playMusic()
elif sys.argv[1] == 'performance':                                # Display Performance stats
    displayPerfStats()
elif sys.argv[1] == 'refresh':                                    # Refresh container 
    containerRefresh()
