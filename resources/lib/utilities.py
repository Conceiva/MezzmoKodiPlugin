import xbmc
import xbmcgui
import xbmcplugin
import os
import sys
import bookmark
import playcount
import xbmcaddon
from media import openNosyncDB, get_installedversion, playCount,openKodiDB
import media
from server import displayServers, picDisplay, displayTrailers
from datetime import datetime, timedelta
from exports import selectExport
from sync import deleteTexturesCache


def autoStart():
    autdialog = xbmcgui.Dialog()
    if sys.argv[2] == "clear":                                    # Ensure user really wants to clear autostart
        aumsg = "Are you sure you want to clear your curent Mezzmo addon autostart setting ?"
        cselect = autdialog.yesno('Mezzmo Autostart Clear', aumsg)
        auplaylist = sys.argv[2]
    else:                                                         # Confirm new autostart setting
        auplaylist = sys.argv[3]
        aumsg = "Confirm setting Mezzmo addon autostart to: \n\n" + auplaylist 
        cselect = autdialog.yesno('Mezzmo Autostart Setting', aumsg)
    if cselect == 1 :
        media.settings('autostart', sys.argv[2])
        mgenlog ='Mezzmo autostart set to: ' + auplaylist
        xbmc.log(mgenlog, xbmc.LOGINFO)
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
            xbmc.executebuiltin('Dialog.Close(all, true)')
            xbmc.sleep(2000)
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
    pdates = ["Most Recent"]
    curpf = pdfile.execute('SELECT DISTINCT psDate FROM mperfStats ORDER BY psDate DESC LIMIT 30', )
    pstatdates = curpf.fetchall()                                # Get dates from database
    for a in range(len(pstatdates)):
        pdates.append(pstatdates[a][0])                          # Convert rows to list for dialog box
    ddialog = xbmcgui.Dialog()  
    vdate = ddialog.select('Select Mezzmo Performance Stats Date', pdates)
    if vdate < 0:                                                # User cancel
        pdfile.close()
        return
    elif (pdates[vdate]) == "Most Recent":
        curpf = pdfile.execute('SELECT * FROM mperfStats ORDER BY psDate DESC, psTime DESC LIMIT 2000',)
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
    for a in range(len(pstatlists)):
        plists.append(pstatlists[a][0])                          # Convert rows to list for dialog box
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

    dldates = ["Most Recent"]
    mdate = 0
    dialog = xbmcgui.Dialog()

    dupdate = dlfile.execute('SELECT DISTINCT dtDate FROM dupeTrack ORDER BY dtDate DESC LIMIT 30', ) 
    mstatdates = dupdate.fetchall()                              # Get dates from database
    if mstatdates:        
        for a in range(len(mstatdates)):
            dldates.append(mstatdates[a][0])                     # Convert rows to list for dialog box
        mdate = dialog.select('Select Duplicate Videos Date', dldates)
        if mdate < 0:                                            # User cancel
            dlfile.close()
            return
        elif (dldates[mdate]) == "Most Recent":
            curdl = dlfile.execute('SELECT * FROM dupeTrack ORDER BY dtDate DESC LIMIT 2000',)
            headval = "Mezzmo Most Recent Duplicate Video Logs"
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

    msdates = ["Most Recent"]
    msdialog = xbmcgui.Dialog()   

    cursync = dsfile.execute('SELECT DISTINCT msDate FROM msyncLog ORDER BY msDate DESC LIMIT 30', )
    mstatdates = cursync.fetchall()                              # Get dates from database
    if mstatdates:        
        for a in range(len(mstatdates)):
            msdates.append(mstatdates[a][0])                     # Convert rows to list for dialog box
        mdate = msdialog.select('Select Sync Logs Date', msdates)
        if mdate < 0:                                            # User cancel
            dsfile.close()
            return
        elif (msdates[mdate]) == "Most Recent":
            cursync = dsfile.execute('SELECT * FROM msyncLog ORDER BY msDate DESC, msTime DESC LIMIT 2000',)
            headval = "Mezzmo Most Recent Sync Logs" 
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

    msdates = ["Most Recent"]
    msdialog = xbmcgui.Dialog()   

    cursync = dsfile.execute('SELECT DISTINCT mgDate FROM mgenLog ORDER BY mgDate DESC LIMIT 30', )
    mstatdates = cursync.fetchall()                              # Get dates from database
    if mstatdates:        
        for a in range(len(mstatdates)):
            msdates.append(mstatdates[a][0])                     # Convert rows to list for dialog box
        mdate = msdialog.select('Select General Logs Date', msdates)
        if mdate < 0:                                            # User cancel
            dsfile.close()
            return
        elif (msdates[mdate]) == "Most Recent":
            cursync = dsfile.execute('SELECT * FROM mgenLog ORDER BY mgDate DESC, mgTime DESC LIMIT 2000',)
            headval = "Mezzmo Most Recent General Logs" 
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
        xbmc.log(mgenlog, xbmc.LOGINFO)
        media.mgenlogUpdate(mgenlog)   
        dialog_text = "All Mezzmo performance logs were deleted."
        perfdialog.ok("Mezzmo Clear Performance Logs", dialog_text)            
    perfile.close()
    return


def trDisplay(title, trcount, icon, imdb_id = ''):                # Play trailers

    try:
        #xbmc.log("Mezzmo trailer title request: " + title, xbmc.LOGINFO)
        mtitle = title
        dsfile = openNosyncDB()                                   # Open Sync logs database

        traillist = []
        msdialog = xbmcgui.Dialog()   

        curtrail = dsfile.execute('SELECT trUrl, trPlay, trVar1 from mTrailers WHERE trTitle = ?  \
        OR trVar2 = ? ORDER BY trID ASC LIMIT ?', (mtitle, imdb_id, trcount,))
        mtrailers = curtrail.fetchall()                            # Get trailers from database
        dsfile.close()
        trselect = x = 1
        if mtrailers:        
            for a in range(len(mtrailers)):                        # Convert rows to list for dialog box
                if media.settings('entrailer') == 'false':
                    if int(mtrailers[a][1]) == 0:
                        traillist.append("Trailer  #" + str(x))    # Convert rows to list for dialog box
                    else:
                        traillist.append("Trailer  #" + str(x) + "     [COLOR blue]Played[/COLOR]") 
                else:
                    plcolor = "[COLOR " + media.settings('playcolor').lower() + "]" 
                    imcolor = "[COLOR " + media.settings('imcolor').lower() + "]"
                    ytcolor = "[COLOR " +  media.settings('ytcolor').lower() + "]"
                    if int(mtrailers[a][1]) > 0:
                        traillist.append("Trailer  #" + str(x) + "     " + plcolor + "Played[/COLOR]") 
                    elif '\imdb_' in str(mtrailers[a][2]):
                        traillist.append("Trailer  #" + str(x) + "     " + imcolor + "Local IMDB[/COLOR]")
                    elif 'www.youtube' not in str(mtrailers[a][2]):
                        traillist.append("Trailer  #" + str(x) + "     " + ytcolor + "Local YouTube[/COLOR]")  
                    else:
                        traillist.append("Trailer  #" + str(x) + "     YouTube")
                x += 1
            trselect = msdialog.select('Select Trailer: ' + mtitle[:60], traillist)
            if trselect < 0:                                       # User cancel
                #dsfile.close()
                return
            else:                                                  # Play trailer and update playcount
              itemurl = mtrailers[trselect][0]
              displayTrailers(title, itemurl, icon, str(trselect + 1))
              dsfile = openNosyncDB()
              dsfile.execute('UPDATE mTrailers SET trPlay=? WHERE trUrl=?', (1, itemurl))
              dsfile.commit()
              dsfile.close()  
        else:
            #xbmc.log("Mezzmo no trailers found: " + title, xbmc.LOGINFO)
            mgenlog ='Mezzmo no trailers found for: ' + title
            xbmc.log(mgenlog, xbmc.LOGINFO)
            media.mgenlogUpdate(mgenlog)         
            trdialog = xbmcgui.Dialog()
            dialog_text = "No trailers found. Please wait for the daily sync process."        
            trdialog.ok("Mezzmo Trailer Playback Error", dialog_text)   

    except:
        mgenlog ='Mezzmo problem displaying trailers for: ' + title
        xbmc.log(mgenlog, xbmc.LOGINFO)
        media.mgenlogUpdate(mgenlog)
        trdialog = xbmcgui.Dialog()
        dialog_text = mgenlog        
        trdialog.ok("Mezzmo Trailer Playback Error", dialog_text)   


def checkGuiTags(taglist, mtitle):                 #  Looks for collections in taglist

    try:
        if len(taglist) == 0:
            return 'none'
        else:
            xbmc.log('Mezzmo taglist is: ' + str(taglist), xbmc.LOGDEBUG)
            tagsplit = taglist.split('$')
            for tag in tagsplit:
                if '###' in tag:
                    return tag.strip()
            return 'none'    

    except:
        mgenlog ='Mezzmo problem parsing GUI collection tags for: ' + mtitle
        xbmc.log(mgenlog, xbmc.LOGINFO)
        media.mgenlogUpdate(mgenlog)
        return 'none'


def selectKeywords(mtype, header, callingm, contenturl):     #  Select Mezzmo keyword

    try:
        pdfile = openNosyncDB()                              # Open keyword database
        curpk = pdfile.execute('SELECT kyTitle FROM mKeywords WHERE kyType=? and kyTitle not like \
        ? AND (kyVar1 <> ? OR kyVar1 IS NULL) ORDER BY kyTitle ASC', (mtype, '%###%', 'No',))
        kcontext = curpk.fetchall()                          # Get keywords from database    
        pdfile.close()

        cselect = []
        for kword in range(len(kcontext)):                   # Build selection list
            cselect.append(kcontext[kword][0])

        ddialog = xbmcgui.Dialog()    
        vcontext = ddialog.select(header, cselect)

        if vcontext < 0:                                     # User cancel
            xbmc.executebuiltin('Dialog.Close(all, true)') 
            return
        else:
            mkeyword = cselect[vcontext] 
            xbmc.executebuiltin('RunAddon(%s, %s)' % ("plugin.video.mezzmo", "contentdirectory=" \
            + contenturl + ';mode=collection;source=' + callingm + ';searchset=' + mkeyword))  

    except:
        mgenlog ='Mezzmo problem parsing Mezzmo keywords for: ' + mtype
        xbmc.log(mgenlog, xbmc.LOGINFO)
        media.mgenlogUpdate(mgenlog)
        pass


def checkItemChange(header, message):                        # Verify user wants to change item

    if media.settings('cconfirm') == 'false':                # Check if confirmation is enabled
        return 1

    checkdialog = xbmcgui.Dialog()                           # Confirm context menu action
    cselect = checkdialog.yesno(header, message)
    return cselect


def moviePreviews(mtitle, vurl, prviewct, myear, icon):      # Play Mezzmo movie previews

    try:
        prflocaltr = media.settings('prflocaltr')   
        prviewyr = media.settings('prviewyr')
        prvrefresh = media.settings('prvrefresh')            # Is refresh Kodi screen enabled ?
        curryear = datetime.now().strftime('%Y')

        if prviewyr == 'true':                               # Preview year or current year
            taryear = int(myear)
        else:
            taryear = curryear

        if prflocaltr == 'true':                             # Prefer local or local and You Tube
            tartrail = '%youtube%'
        else:
            tartrail = '% %'

        mpfile = openNosyncDB()
        mpcurr = mpfile.execute('SELECT trTitle, trUrl, trVar3 from mTrailers where trVar1  \
        NOT LIKE ? AND mPcount=? AND trYear=? AND trID=? AND trPlay=? AND NOT trTitle=?     \
        ORDER BY RANDOM() LIMIT ?', (tartrail, 0, taryear, '1', '0', mtitle, prviewct,))
        mptuples = mpcurr.fetchall()

        if len(mptuples) < prviewct:                         # If all movies played in the requested year
            mpcurr = mpfile.execute('SELECT trTitle, trUrl, trVar3 from mTrailers where trVar1  \
            NOT LIKE ? AND trYear=? AND trID=? AND trPlay=? AND NOT trTitle=? ORDER BY RANDOM() \
            LIMIT ?', (tartrail, taryear, '1', '0', mtitle, prviewct,))
            mptuples = mpcurr.fetchall()
        
        mpfile.close()

        xbmc.log('Mezzmo Movie Previews: ' + str(taryear) + ' ' + str(len(mptuples)) + ' '  \
        + vurl, xbmc.LOGDEBUG)
        mezzlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)        # Create playlist
        mezzlist.clear()
        if len(mptuples) > 0:                                # Build playlist of trailers
            for m in range(len(mptuples)):
                lititle = str(taryear) + " Trailer - " + mptuples[m][0]
                trurl = mptuples[m][1]
                tricon = mptuples[m][2]
                li = xbmcgui.ListItem(lititle, trurl)
                if int(get_installedversion()) == 19:
                    li.setInfo('video', {'Title': lititle})
                else:
                    linfo = li.getVideoInfoTag()
                    linfo.setTitle(lititle)
                li.setArt({'thumb': tricon, 'poster': tricon})
                mezzlist.add(url=trurl, listitem=li)
                dsfile = openNosyncDB()                      # Open trailer database
                dsfile.execute('UPDATE mTrailers SET trPlay=? WHERE trUrl=?', (1, trurl))
                dsfile.commit()
                dsfile.close()  
        else:                                                # No matching trailers found
            xbmcgui.Dialog().notification(media.translate(30481), media.translate(30482), icon, 3000)

        li = xbmcgui.ListItem(mtitle, vurl)                  # Add main feature to playlist
        if int(get_installedversion()) == 19:
            li.setInfo('video', {'Title': mtitle})
        else:
            linfo = li.getVideoInfoTag()
            linfo.setTitle(mtitle)
        li.setArt({'thumb': icon, 'poster': icon})
        mezzlist.add(url=vurl, listitem=li)

        if prvrefresh == 'true':                             # Set movie preview flag if enabled
            media.settings('movieprvw', 'true') 
        xbmc.Player().play(mezzlist)   
        del mezzlist

    except:
        mgenlog ='Mezzmo problem with Mezzmo Movie Previews for: ' + str(myear)
        xbmc.log(mgenlog, xbmc.LOGINFO)
        media.mgenlogUpdate(mgenlog)


def guiContext(mtitle, vurl, vseason, vepisode, playcount, mseries, mtype, contenturl, \
    bmposition, icon, movieset, taglist, mezyear, trtype, imdb_id) :

    addon = xbmcaddon.Addon()
    addon_path = addon.getAddonInfo("path")
    addon_icon = addon_path + '/resources/icon.png'
    menuitem1 = addon.getLocalizedString(30434)
    menuitem2 = addon.getLocalizedString(30384)
    menuitem3 = addon.getLocalizedString(30372)
    menuitem4 = addon.getLocalizedString(30373) 
    menuitem5 = addon.getLocalizedString(30436) 
    menuitem6 = addon.getLocalizedString(30437) 
    menuitem7 = addon.getLocalizedString(30440)
    menuitem8 = addon.getLocalizedString(30467)
    menuitem9 = addon.getLocalizedString(30468)
    menuitem10 = addon.getLocalizedString(30469)
    menuitem11 = addon.getLocalizedString(30470)
    menuitem12 = addon.getLocalizedString(30481)
    menuitem13 = addon.getLocalizedString(30494)                     # Play movie from mezzmo
    menuitem14 = addon.getLocalizedString(30495)                     # Show TV Episodes
    menuitem15 = addon.getLocalizedString(30498)  
    menuitem16 = addon.getLocalizedString(30812)	             # Last Played        
    trcount = media.settings('trcount')
    prviewct = int(media.settings('prviewct'))    
    mplaycount = int(playcount)
    currpos = int(bmposition)
    lastvpl = int(media.settings('lastvpl'))                        # Last played setting
    if mtype == 'movie' or mtype == 'musicvideo' or mtype == 'episode' :  # Check for collection tag
        collection = checkGuiTags(taglist, mtitle)
    else:
        collection = 'none'

    xbmc.executebuiltin('Dialog.Close(all, true)')    
    #xbmc.log('Mezzmo titleinfo is: ' + str(titleinfo), xbmc.LOGDEBUG)
    #xbmc.log('Mezzmo mediatype is: ' + str(mtype) + ' ' + str(trtype), xbmc.LOGINFO)
    #xbmc.log('Mezzmo collection is: ' + str(collection) + ' ' + mseries, xbmc.LOGINFO) 

    pdfile = openNosyncDB()                              # Open Trailer database
    cselect = []
    curpt = pdfile.execute('SELECT count (trUrl) FROM mTrailers WHERE trTitle=? or         \
    trVar2=?', (title,imdb_id,))
    tcontext = curpt.fetchone()                          # Get trailer count from database
    if mtype == 'movie' or  'trailer' in trtype.lower():
        keytarget = 'movie'
    else:
        keytarget = mtype  
    curpk = pdfile.execute('SELECT count (kyTitle) FROM mKeywords WHERE kyType=? and kyTitle \
    not like ? AND (kyVar1 <> ? OR kyVar1 IS NULL)', (keytarget, '%###%', 'No',))
    kcontext = curpk.fetchone()                          # Get keyword count from database  
    pdfile.close()

    pdfile = openKodiDB()                                # Open Kodi DB
    musicvid = media.settings('musicvid')                # Check if musicvideo sync is enabled
    if mtype == 'musicvideo' and musicvid == 'true':     # Find musicvideo bookmark
        curpt = pdfile.execute('SELECT idBookmark FROM bookmark INNER JOIN musicvideo_view USING  \
        (idFile) WHERE musicvideo_view.c00=?', (mtitle,))
        bcontext = curpt.fetchone()                      # Get bookmark from database
    elif mtype == 'episode':                             # Find episode bookmark
        curpt = pdfile.execute('SELECT idBookmark FROM bookmark INNER JOIN episode_view USING     \
        (idFile) WHERE episode_view.c00=?', (mtitle,))
        bcontext = curpt.fetchone()                      # Get bookmark from database
    else:
        curpt = pdfile.execute('SELECT idBookmark FROM bookmark INNER JOIN movie_view USING       \
        (idFile) WHERE movie_view.c00=?', (mtitle,))
        bcontext = curpt.fetchone()                      # Get bookmark from database
    if trtype.lower() == 'trailer':
        curtr = pdfile.execute('SELECT c22, c01 from movie_view WHERE uniqueid_value = ?', (imdb_id,))
        trcontext = curtr.fetchone()
    else:
        trcontext = None
    if mtype == 'episode' or 'tvtrailer' in  trtype.lower(): # check for TV episodes for TV trailers
        curptv= pdfile.execute('SELECT c00 FROM tvshow WHERE c00=?', (movieset,))
        tvcontext = curptv.fetchone()                    # Get TV Show from database if exists
    else:
        tvcontext = None  
    pdfile.close()

    if mplaycount <= 0 and 'trailer' not in trtype.lower():  # Mezzmo playcount is 0
        cselect.append(menuitem3)
    elif mplaycount > 0 and 'trailer' not in trtype.lower():
        cselect.append(menuitem4)

    if currpos > 0 and 'trailer' not in trtype.lower():      # If bookmark exists
        cselect.append(menuitem7)

    if lastvpl > 0 and 'trailer' not in trtype.lower():      # If last played value > 0
        cselect.append(menuitem16)              

    if tcontext[0] > 0 and int(trcount) > 0:             # If trailers for movie and enabled
        cselect.append(menuitem1)

    if prviewct > 0 and mtype == 'movie' and 'trailer' not in trtype.lower():  # If Mezmo Movie Previews > 0
        cselect.append(menuitem12)

    if movieset != 'Unknown Album' and movieset != 'None' and (mtype == 'movie' or trtype.lower() \
    == 'trailer') and (mtype == 'movie' and trtype.lower() != 'tvtrailer'):  # If movieset and type is movie
        cselect.append(menuitem8)

    if collection != 'none' and (mtype == 'movie' or mtype == 'episode'):  # If collection tag and type
        cselect.append(menuitem9) 

    if collection != 'none' and mtype == 'musicvideo':   # If collection tag and type is musicv
        cselect.append(menuitem10)

    if kcontext[0] > 0 :                                 # If Keywords for media type
        cselect.append(menuitem11)

    if tvcontext != None :                               # If TV Episodes exist for TV Trailer
        cselect.append(menuitem14)    

    cselect.append(menuitem2)                            # Logs & Stats

    if trcontext != None:                                # Trailer play movie
        cselect.append(menuitem13)

    if media.settings('caching')  == 'Demand':           # Clear Kodi cache
        cselect.append(menuitem15)        

    ddialog = xbmcgui.Dialog()    
    vcontext = ddialog.select(addon.getLocalizedString(30471), cselect)

    if vcontext < 0:                                     # User cancel
        xbmc.executebuiltin('Dialog.Close(all, true)') 
        return      
    elif (cselect[vcontext]) == menuitem1:               # Mezzmo trailers
        trDisplay(title, trcount, icon, imdb_id)
    elif (cselect[vcontext]) == menuitem12:              # Mezzmo Movie Previews
        moviePreviews(title, vurl, prviewct, mezyear, icon)
    elif (cselect[vcontext]) == menuitem2:               # Mezzmo Logs & stats
        displayMenu()
    elif (cselect[vcontext]) == menuitem3 or (cselect[vcontext]) == menuitem4:
        if checkItemChange(cselect[vcontext], addon.getLocalizedString(30473)) < 1:
            return 
        if not vurl:
            pcdialog = xbmcgui.Dialog()
            dialog_text = "Unable to modify the playcount.  Selected item URL is missing."        
            pcdialog.ok(addon.getLocalizedString(30474), dialog_text)
            return       
        media.playCount(title, vurl, vseason, vepisode, \
        mplaycount, mseries, mtype, contenturl)          # Mezzmo Playcount
    elif (cselect[vcontext]) == menuitem7:               # Mezzmo Clear Bookmark
        if checkItemChange(cselect[vcontext], addon.getLocalizedString(30472)) < 1:
            return
        rtrimpos = contenturl.rfind('/')
        kobjectID = contenturl[rtrimpos+1:]              # Get Kodi objectID
        rtrimpos = vurl.rfind('/')
        mobjectID = vurl[rtrimpos+1:]                    # Get Mezzmo objectID
        #xbmc.log('Mezzmo bookmark info is: ' + str(mobjectID) + ' ' + str(contenturl), xbmc.LOGINFO)
        bookmark.SetBookmark(contenturl, mobjectID, '0')
        bookmark.updateKodiBookmark(kobjectID, '0', mtitle, mtype)
        media.nativeNotify()                             # Kodi native notification
        xbmc.sleep(1000)  
        xbmc.executebuiltin('Container.Refresh')
        mgenlog ='Mezzmo Kodi bookmark cleared for: ' + title
        xbmc.log(mgenlog, xbmc.LOGINFO)
        mgenlog = '###' + mtitle
        media.mgenlogUpdate(mgenlog)   
        mgenlog ='Mezzmo Kodi bookmark cleared for: '
        media.mgenlogUpdate(mgenlog) 
    elif (cselect[vcontext]) == menuitem8 or (cselect[vcontext]) == menuitem14:   # Display movie sets or episodes
        xbmc.executebuiltin('RunAddon(%s, %s)' % ("plugin.video.mezzmo", "contentdirectory=" + contenturl + \
        ';mode=movieset;source=browse;searchset=' + movieset))
    elif (cselect[vcontext]) == menuitem9 or (cselect[vcontext]) == menuitem10 : # Mezzmo display collections          
        xbmc.executebuiltin('RunAddon(%s, %s)' % ("plugin.video.mezzmo", "contentdirectory=" + contenturl + \
        ';mode=collection;source=browse;searchset=' + collection))
    elif (cselect[vcontext]) == menuitem11:              # Mezzmo display keywords
        selectKeywords(keytarget, menuitem11, 'browse', contenturl)
    elif (cselect[vcontext]) == menuitem13:              # Play trailer movie  
        trPlayMovie(mtitle, trcontext[0], icon, trcontext[1])  
    elif (cselect[vcontext]) == menuitem15:
        deleteTexturesCache(contenturl, 'yes')  
        xbmcgui.Dialog().notification(media.translate(30435), media.translate(30499), addon_icon, 3000)
    elif (cselect[vcontext]) == menuitem16:              # Display last played video items
        xbmc.executebuiltin('RunAddon(%s, %s)' % ("plugin.video.mezzmo", "contentdirectory=" + contenturl + \
        ';mode=lastvpl;source=browse;count=' + str(lastvpl)))   


def trPlayMovie(title, itemurl, icon, mplot):                      # Display trailer movie

    try:
        li = xbmcgui.ListItem(title)
        if int(get_installedversion()) == 19:
            li.setInfo('video', {'Title': title, 'plot': mplot,})
        else:
            linfo = li.getVideoInfoTag()
            linfo.setTitle(title)
            linfo.setPlot(mplot)
        li.setArt({'thumb': icon, 'poster': icon}) 
        xbmc.Player().play(itemurl, li)
    except:
        mgenlog ='Mezzmo problem playing movie ' + title
        xbmc.log(mgenlog, xbmc.LOGINFO)
        media.mgenlogUpdate(mgenlog)         
        trdialog = xbmcgui.Dialog()
        dialog_text = mgenlog        
        trdialog.ok("Mezzmo Movie Playback Error", dialog_text)          


if len(sys.argv) > 1:
    if sys.argv[1] == 'count':                                        # Playcount modification call
        title = sys.argv[2]                                           # Extract passed variables
        vurl = sys.argv[3]
        vseason = sys.argv[4]
        vepisode = sys.argv[5]
        mplaycount = sys.argv[6]
        series = sys.argv[7]
        mtype = sys.argv[8]
        contenturl = sys.argv[9]
        playCount(title, vurl, vseason, vepisode, mplaycount,     \
        series, mtype, contenturl)
    elif sys.argv[1] == 'context':                                    # GUI context menu
        title = sys.argv[2]                                           # Extract passed variables
        vurl = sys.argv[3]
        vseason = sys.argv[4]
        vepisode = sys.argv[5]
        mplaycount = sys.argv[6]
        series = sys.argv[7]
        mtype = sys.argv[8]
        contenturl = sys.argv[9]
        currposs = sys.argv[10]
        icon = sys.argv[11]
        movieset = sys.argv[12]
        taglist = sys.argv[13]
        mezyear = sys.argv[14]
        if len(sys.argv) >= 16:                                       # Check for Mezzmp Movie Trailer Channel
            trtype = sys.argv[15]
            imdb_id = sys.argv[16]
        else:
            trtype = 'video'
            imdb_id = 0 
        guiContext(title, vurl, vseason, vepisode, mplaycount, series,  \
        mtype, contenturl, currposs, icon, movieset, taglist, mezyear,  \
        trtype, imdb_id)                                              # call GUI context menu
    elif sys.argv[1] == 'auto':                                       # Set / Remove autostart
        autoStart()
    elif sys.argv[1] == 'playm':                                      # Play music with bookmark
        playMusic()
    elif sys.argv[1] == 'performance':                                # Display Performance stats
        displayMenu()
    elif sys.argv[1] == 'servers':                                    # Display Sync servers
        displayServers()
    elif sys.argv[1] == 'pictures':                                   # Display Pictures
        picDisplay()
    elif sys.argv[1] == 'export':                                     # Export data
        selectExport()
    elif sys.argv[1] == 'trailer':                                    # Display trailers
        title = sys.argv[2]                                           # Extract passed variables
        trcount = int(sys.argv[3])
        icon = sys.argv[4]
        trDisplay(title, trcount, icon)
    elif sys.argv[1] == 'playlist':
        xbmc.log('Mezzmo Music playlist: ' + sys.argv[2] + ' ' + sys.argv[3], xbmc.LOGDEBUG)
        xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"Player.Open",      \
        "params":{"item":{"playlistid":%s, "position":%s}},"id":1}' % (sys.argv[2], sys.argv[3]))


