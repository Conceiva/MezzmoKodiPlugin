import xbmc
import xbmcgui
import xbmcplugin
import os
import bookmark
import xbmcaddon
import playcount
from media import openNosyncDB, get_installedversion
import media
from server import displayServers
from datetime import datetime, timedelta

#xbmc.log('Name of script: ' + str(sys.argv[0]), xbmc.LOGNOTICE)
#xbmc.log('Number of arguments: ' + str(len(sys.argv)), xbmc.LOGNOTICE)
#xbmc.log('The arguments are: ' + str(sys.argv), xbmc.LOGNOTICE)


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
        media.settings('autostart', sys.argv[2])
        mgenlog ='Mezzmo autostart set to: ' + str(sys.argv[2])
        xbmc.log(mgenlog, xbmc.LOGNOTICE)
        media.mgenlogUpdate(mgenlog)       
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


def displayMenu():
    if int(get_installedversion()) < 18:                         # Textviewer function added in Kodi 18
        dialog_text = "Mezzmo Logs & Performance Stats are only available in Kodi version 18 and higher."
        xbmcgui.Dialog().ok("Mezzmo Logs & Performance Stats", dialog_text)
        return       

    while True:
        try:
            pdfile = openNosyncDB()                              # Open Perf Stats database
            pselect = []
            curpf = pdfile.execute('SELECT dtDate FROM dupeTrack LIMIT 1', )
            pstatdates = curpf.fetchone()                        # Get dates from dupe database
            if pstatdates:                                       # If dates in duplicate table
                pselect = ["Mezzmo Duplicate Logs"]

            curpf = pdfile.execute('SELECT msDate FROM msyncLog LIMIT 1', )
            mstatdates = curpf.fetchone()                        # Get dates from sync database
            if mstatdates and len(pselect) > 0:                  # If dates in sync table 
                pselect.extend(["Mezzmo Addon Sync Logs"])
            elif mstatdates and len(pselect) == 0: 
                pselect = ["Mezzmo Addon Sync Logs"]   

            curpf = pdfile.execute('SELECT psDate FROM mperfStats LIMIT 1', )
            pstatdates = curpf.fetchone()                        # Get dates from perf database
            if pstatdates and len(pselect) > 0:                  # If dates in performance table
                pselect.extend(["Mezzmo Addon Performance Logs", "Performance By Playlist"])
            elif pstatdates and len(pselect) == 0: 
                pselect = ["Mezzmo Addon Performance Logs", "Performance By Playlist"] 

            curpf = pdfile.execute('SELECT mgDate FROM mgenLog LIMIT 1', )
            gstatdates = curpf.fetchone()                        # Get dates from general log database
            if gstatdates and len(pselect) > 0:                  # If dates in general table
                pselect.extend(["Mezzmo Addon General Logs"])
            elif gstatdates and len(pselect) == 0: 
                pselect = ["Mezzmo Addon General Logs"]

            if pstatdates and len(pselect) > 0:                  # Add performance DB clear option
                pselect.extend(["[COLOR blue]Mezzmo Clear Performance Logs[/COLOR]"])
            elif len(pselect) == 0: 
                pselect(["There are no logs or stats to display"])         

            ddialog = xbmcgui.Dialog()    
            vdate = ddialog.select('Select Mezzmo Logs or Stats View', pselect)
            xbmc.log('Mezzmo performance selection is: ' + pselect[vdate], xbmc.LOGDEBUG)    
            pdfile.close()
        except:
            perfdialog = xbmcgui.Dialog()
            dialog_text = "Error connecting to the Logs & Statistics database.  "
            dialog_text = dialog_text + "Please restart Kodi to correct."
            perfdialog.ok("Mezzmo Addon Database Error", dialog_text)
            break            

        if vdate < 0:                                            # User cancel
            pdfile.close()
            break      
        elif (pselect[vdate]) == "Mezzmo Duplicate Logs":
            displayDupeLogs()
        elif (pselect[vdate]) == "Mezzmo Addon Sync Logs":
            displaySyncLogs()
        elif (pselect[vdate]) == "Mezzmo Addon General Logs":
            displayGenLogs()
        elif "Mezzmo Clear Performance Logs" in (pselect[vdate]): 
            clearPerf()
        elif (pselect[vdate]) == "Performance By Playlist": 
            perfPlaylist()        
        elif (pselect[vdate]) == "Mezzmo Addon Performance Logs":
            perfStats()


def perfStats():                                                 # Mezzmo Addon Performance Logs

    pdfile = openNosyncDB()                                      # Open Perf Stats database
    pdates = ["All"]
    curpf = pdfile.execute('SELECT DISTINCT psDate FROM mperfStats ORDER BY psDate DESC', )
    pstatdates = curpf.fetchall()                                # Get dates from database
    a = 0
    while a < len(pstatdates) and a < 30:
        pdates.append(pstatdates[a][0])                          # Convert rows to list for dialog box
        a += 1
    ddialog = xbmcgui.Dialog()  
    vdate = ddialog.select('Select Mezzmo Performance Stats Date', pdates)
    if vdate < 0:                                                # User cancel
        pdfile.close()
        return
    elif (pdates[vdate]) == "All":
        curpf = pdfile.execute('SELECT * FROM mperfStats ORDER BY psDate DESC, psTime DESC',)
        headval = 'Mezzmo Performance Stats for:  ' + pdates[vdate]
    else:
        curpf = pdfile.execute('SELECT * FROM mperfStats WHERE psDate=? ORDER BY psTime DESC', (pdates[vdate],))
        headval = 'Mezzmo Performance Stats for:  ' + pdates[vdate][5:] + "-" + \
        pdates[vdate][:4]
    pstatslist = curpf.fetchall()
    pdfile.close()
    displayPerf(pstatslist, headval)


def displayPerf(pstatslist, headval):

    textval1 = "{:^25}".format("Time") + "{:^21}".format("# of") + "{:<15}".format("Mezzmo") + "{:<15}".format("Kodi")   \
    + "{:<11}".format("Total") +  "Items per" + "{:>24}".format("Playlist") +  "\n" + "{:>41}".format("Items")  \
    + "{:>14}".format("Time") + "{:>16}".format("Time") + "{:>16}".format("Time") + "{:>13}".format("sec") + "\n" 
    dialog = xbmcgui.Dialog()


    if pstatslist:                                               # Check for records in perfdb and not cancel
        for a in range(len(pstatslist)):                         # Display stats   
            perfdate = pstatslist[a][0]
            perfdate = perfdate[5:].replace("-", "/") + "   "
            perftime = pstatslist[a][1] + "     "
            ctitle = pstatslist[a][2]
            TotalMatches = pstatslist[a][3]
            pduration = pstatslist[a][4]
            sduration = pstatslist[a][5]
            tduration = pstatslist[a][6]
            displayrate = pstatslist[a][7]
            plist = "        " + ctitle[:24]                     # Limit playlist name to 24 chars to stop wrapping
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
                                       
    else:                                                        # No records found for date selected   
        perfdialog = xbmcgui.Dialog()
        dialog_text = "No performance logs found for the selected date or playlist."        
        perfdialog.ok("Mezzmo Addon Database Error", dialog_text)     


def perfPlaylist():                                              # Performance By Playlist

    pdfile = openNosyncDB()                                      # Open Perf Stats database
    plists = []
    curpf = pdfile.execute('SELECT DISTINCT psPlaylist FROM mperfStats ORDER BY psPlaylist ASC', )
    pstatlists = curpf.fetchall()                                # Get playlists from database
    a = 0
    while a < len(pstatlists):
        plists.append(pstatlists[a][0])                          # Convert rows to list for dialog box
        a += 1                                    # Convert rows to list for dialog box
    ddialog = xbmcgui.Dialog() 
    vdate = ddialog.select('Select Mezzmo Performance Stats Playlist', plists)
    if vdate < 0:                                                # User cancel
        pdfile.close()
        return
    curpf = pdfile.execute('SELECT * FROM mperfStats WHERE psPlaylist=? ORDER BY psDate DESC,              \
    psTime DESC', (plists[vdate],))
    headval = 'Mezzmo Performance Stats for:  ' + plists[vdate]
    pstatslist = curpf.fetchall() 
    pdfile.close()
    displayPerf(pstatslist, headval)


def displayDupeLogs():
   
    dlfile = openNosyncDB()                                      # Open Dupe logs database

    dldates = ["All"]
    mdate = 0
    dialog = xbmcgui.Dialog()

    dupdate = dlfile.execute('SELECT DISTINCT dtDate FROM dupeTrack ORDER BY dtDate DESC', ) 
    mstatdates = dupdate.fetchall()                              # Get dates from database
    if mstatdates:        
        a = 0       
        while a < len(mstatdates) and a < 30:
            dldates.append(mstatdates[a][0])                     # Convert rows to list for dialog box
            a += 1
        mdate = dialog.select('Select Duplicate Videos Date', dldates)
        if mdate < 0:                                            # User cancel
            dlfile.close()
            return
        elif (dldates[mdate]) == "All":
            curdl = dlfile.execute('SELECT * FROM dupeTrack ORDER BY dtDate DESC',)
            headval = "All Mezzmo Duplicate Video Logs"
        elif len(dldates[mdate]) > 0:                            # Get records for selected date
            curdl = dlfile.execute('SELECT * FROM dupeTrack WHERE dtDate=?', (dldates[mdate],))
            headval = 'Mezzmo Duplicate Videos for:  ' + dldates[mdate][5:] + "-" + dldates[mdate][:4]
    elif mdate < 0:                                              # User cancel
        displayMenu()       
    else:                                                        # No sync logs found for date selected
        textval1 = "No Mezzmo Duplicate Videos found."           # Should never happen. Safety check 
        dialog.textviewer("Mezzmo Duplicate Videos", textval1)            
        dlfile.close()
        return
      
    dllogs = curdl.fetchall()                                     # Get dupe logs from database      
    textval1 = "{:^25}".format("Date") + "{:^21}".format("Record #") + "{:>32}".format     \
    ("Duplicate Mezzmo Entry")
    textval1 = textval1 + "\n" 

    if dllogs:
        for a in range(len(dllogs)):                              # Display logs if exist   
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
        perfdialog = xbmcgui.Dialog()
        dialog_text = "No duplicate logs found for the selected date."        
        perfdialog.ok("Mezzmo Addon Database Error", dialog_text)     
    dlfile.close()
    return


def displaySyncLogs():

    dsfile = openNosyncDB()                                       # Open Sync logs database

    msdates = ["All"]
    msdialog = xbmcgui.Dialog()   

    cursync = dsfile.execute('SELECT DISTINCT msDate FROM msyncLog ORDER BY msDate DESC', )
    mstatdates = cursync.fetchall()                              # Get dates from database
    if mstatdates:        
        a = 0         
        while a < len(mstatdates) and a < 30:
            msdates.append(mstatdates[a][0])                     # Convert rows to list for dialog box
            a += 1
        mdate = msdialog.select('Select Sync Logs Date', msdates)
        if mdate < 0:                                            # User cancel
            dsfile.close()
            return
        elif (msdates[mdate]) == "All":
            cursync = dsfile.execute('SELECT * FROM msyncLog ORDER BY msDate DESC, msTime DESC',)
            headval = "Mezzmo All Sync Logs" 
        elif len(msdates[mdate]) > 0:                           # Get records for selected date
            cursync = dsfile.execute('SELECT * FROM msyncLog WHERE msDate=? ORDER BY msTime DESC', \
            (msdates[mdate],))
            headval = 'Mezzmo Sync Logs for:  ' + msdates[mdate][5:] + "-" + msdates[mdate][:4]
    else:                                                        # No sync logs found for date selected
        textval1 = "No Mezzmo sync logs found."                  # Should never happen. Safety check 
        msdialog.textviewer("Mezzmo Sync Logs", textval1)            
        dsfile.close()
        return       

    mslogs = cursync.fetchall()                                   # Get sync logs from database
    textval1 = "{:^38}".format("Date") + "{:>32}".format("Sync Log Message")
    textval1 = textval1 + "\n" 

    if mslogs:
        for a in range(len(mslogs)):                             # Display logs if exist   
            msdate = mslogs[a][0]
            mstime = mslogs[a][1][:8]                            # Strip off milliseconds
            msdatetime = msdate + "   " + mstime + "      "
            msynclog = mslogs[a][2]
            textval1 = textval1 + "\n" + msdatetime + msynclog
        msdialog.textviewer(headval, textval1)                                     
    else:                                                        # No records found for date selected  
        perfdialog = xbmcgui.Dialog()
        dialog_text = "No sync logs found for the selected date."        
        perfdialog.ok("Mezzmo Addon Database Error", dialog_text)     
    dsfile.close()
    return


def displayGenLogs():

    dsfile = openNosyncDB()                                       # Open Sync logs database

    msdates = ["All"]
    msdialog = xbmcgui.Dialog()   

    cursync = dsfile.execute('SELECT DISTINCT mgDate FROM mgenLog ORDER BY mgDate DESC', )
    mstatdates = cursync.fetchall()                              # Get dates from database
    if mstatdates:        
        a = 0       
        while a < len(mstatdates) and a < 30:
            msdates.append(mstatdates[a][0])                     # Convert rows to list for dialog box
            a += 1
        mdate = msdialog.select('Select General Logs Date', msdates)
        if mdate < 0:                                            # User cancel
            dsfile.close()
            return
        elif (msdates[mdate]) == "All":
            cursync = dsfile.execute('SELECT * FROM mgenLog ORDER BY mgDate DESC, mgTime DESC',)
            headval = "Mezzmo All General Logs" 
        elif len(msdates[mdate]) > 0:                            # Get records for selected date
            cursync = dsfile.execute('SELECT * FROM mgenLog WHERE mgDate=? ORDER BY mgTime DESC', \
            (msdates[mdate],))
            headval = 'Mezzmo General Logs for:  ' + msdates[mdate][5:] + "-" + msdates[mdate][:4]
    else:                                                        # No gen logs found for date selected
        textval1 = "No Mezzmo general logs found."               # Should never happen. Safety check 
        msdialog.textviewer("Mezzmo General Logs", textval1)            
        dsfile.close()
        return        

    mglogs = cursync.fetchall()                                   # Get sync logs from database
    textval1 = "{:^38}".format("Date") + "{:>32}".format("General Log Message")
    textval1 = textval1 + "\n" 

    if mglogs:
        for a in range(len(mglogs)):                              # Display logs if exist   
            msdate = mglogs[a][0]
            mstime = mglogs[a][1][:8]                             # Strip off milliseconds
            msynclog = mglogs[a][2]
            if msynclog[0:3] == '###':                            # Detect multiline logs
                msynclog = msynclog[3:]
                msdatetime = "{:>44}".format(" ")
            else:
                msdatetime = msdate + "   " + mstime + "      "
            textval1 = textval1 + "\n" + msdatetime + msynclog
        msdialog.textviewer(headval, textval1)                                     
    else:                                                         # No records found for date selected   
        perfdialog = xbmcgui.Dialog()
        dialog_text = "No general logs found for the selected date."        
        perfdialog.ok("Mezzmo Addon Database Error", dialog_text)     
    dsfile.close()
    return


def clearPerf():                                                  # Clear performance statistics

    perfile = openNosyncDB()                                      # Open perf stats database
    perfdialog = xbmcgui.Dialog()
    kcmsg = "Confirm clearing the Mezzmo performance logs.  "
    cselect = perfdialog.yesno('Mezzmo Clear Performance Logs', kcmsg)
    if cselect == 1 :
        perfile.execute('DELETE FROM mperfStats',)
        perfile.execute('DELETE FROM mperfIndex',)
        perfile.commit()
        mgenlog ='Mezzmo performance logs cleared by user.'
        xbmc.log(mgenlog, xbmc.LOGNOTICE)
        media.mgenlogUpdate(mgenlog)   
        dialog_text = "All Mezzmo performance logs were deleted."
        perfdialog.ok("Mezzmo Clear Performance Logs", dialog_text)            
    perfile.close()
    return

 
if sys.argv[1] == 'count':                                        # Playcount modification call
    playCount()
elif sys.argv[1] == 'auto':                                       # Set / Remove autostart
    autoStart()
elif sys.argv[1] == 'playm':                                      # Play music with bookmark
    playMusic()
elif sys.argv[1] == 'performance':                                # Display Performance stats
    displayMenu()
elif sys.argv[1] == 'servers':                                    # Display Sync srvers
    displayServers()
