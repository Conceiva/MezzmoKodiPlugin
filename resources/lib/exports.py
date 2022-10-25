import xbmc
import xbmcgui
import xbmcplugin
import os
import xbmcaddon
import xbmcvfs
from media import openKodiDB, openNosyncDB, printexception, mgenlogUpdate, translate
from mumedia import openKodiMuDB
import media
import csv  
from datetime import datetime

addon = xbmcaddon.Addon()
addon_path = addon.getAddonInfo("path")
addon_icon = addon_path + '/resources/icon.png'

def exportData(selectbl):                                        # CSV Output selected table

    try:

        #xbmc.log("Mezzmo selectable is: " +  str(selectbl), xbmc.LOGNINFO)

        folderpath = xbmcvfs.translatePath(os.path.join("special://home/", "output/"))
        if not xbmcvfs.exists(folderpath):
            xbmcvfs.mkdir(folderpath)
            xbmc.log("Mezzmo Export Output folder not found: " +  str(folderpath), xbmc.LOGINFO)

        for a in range(len(selectbl)):
            fpart = datetime.now().strftime('%H%M%S')
            selectindex = int(selectbl[a][:2])                   # Get list index to determine DB
            selectname = selectbl[a][2:]                         # Parse table name in DB

            #xbmc.log("Mezzmo selectable is: " +  str(selectindex) + ' ' + selectname, xbmc.LOGINFO)
            if selectindex < 11:
                dbexport = openKodiDB()
                dbase = 'videos_'
            elif selectindex < 18:
                dbexport = openKodiMuDB()
                dbase = 'music_'                
            else:
                dbexport = openNosyncDB() 
                dbase = 'addon_'

            outfile = folderpath + "mezzmo_" + dbase + selectname + "_" + fpart + ".csv"
            curm = dbexport.execute('SELECT * FROM '+selectname+'')
            recs = curm.fetchall()
            headers = [i[0] for i in curm.description]
            csvFile = csv.writer(open(outfile, 'w', encoding='utf-8'),
                             delimiter=',', lineterminator='\n',
                             quoting=csv.QUOTE_ALL, escapechar='\\')

            csvFile.writerow(headers)                       # Add the headers and data to the CSV file.
            for row in recs:
                recsencode = []
                # xbmc.log("Mezzmo output string length is: " +  str(len(row)), xbmc.LOGINFO)
                for item in range(len(row)):
                    if isinstance(row[item], int) or isinstance(row[item], float):  # Convert to strings
                        rectemp = str(row[item])
                        try:
                            recitem = rectemp.decode('utf-8')
                        except:
                            recitem = rectemp
                    else:
                        rectemp = row[item]
                        try:
                            recitem = rectemp.decode('utf-8')
                        except:
                            recitem = rectemp
                    recsencode.append(recitem) 
                csvFile.writerow(recsencode)                
            dbexport.close()

        outmsg = folderpath
        dialog_text = translate(30428) + outmsg 
        xbmcgui.Dialog().ok(translate(30429), dialog_text)

    except Exception as e:
        printexception()
        dbexport.close()
        mgenlog = translate(30431) + selectname
        xbmcgui.Dialog().notification(translate(30432), mgenlog, addon_icon, 5000)            
        xbmc.log(mgenlog, xbmc.LOGINFO)
        mgenlogUpdate(mgenlog)


def selectExport():                                            # Select table to export

    try:
        while True:
            stable = []
            selectbl = []
            tables = ["Kodi Video DB - Actors","Kodi Video DB - Episodes","Kodi Video DB - Movies",              \
            "Kodi Video DB - TV Shows","Kodi Video DB - Artwork","Kodi Video DB - Path","Kodi Video DB - Files", \
            "Kodi Video DB - Streamdetails", "Kodi Video DB - Episode View", "Kodi Video DB - Movie View",       \
            "Kodi Video DB - Music Video View", "Kodi Music DB - Artist","Kodi Music DB - Album Artist View",    \
            "Kodi Music DB - Album View ","Kodi Music DB - Artist View", "Kodi Music DB - Song",                 \
            "Kodi Music DB - Song Artist View","Kodi Music DB - Song View", "Addon DB - uPNP Servers",           \
            "Addon DB - Duplicates", "Addon DB - Performance Stats", "Addon DB - General Logs",                  \
            "Addon DB - Sync Logs","Addon DB - No Sync Videos","Addon DB - Trailers"]
            ddialog = xbmcgui.Dialog()    
            stable = ddialog.multiselect(translate(30432), tables)
            if stable == None:                                 # User cancel
                break
            if 0 in stable:
                selectbl.append('00actor')
            if 1 in stable:
               selectbl.append('01episode')   
            if 2 in stable:
                selectbl.append('02movie')
            if 3 in stable:
                selectbl.append('03tvshow')
            if 4 in stable:
                selectbl.append('04art')    
            if 5 in stable:
                selectbl.append('05path')  
            if 6 in stable:
                selectbl.append('06files')  
            if 7 in stable:
                selectbl.append('07streamdetails')
            if 8 in stable:
                selectbl.append('08episode_view')
            if 9 in stable:
                selectbl.append('09movie_view')
            if 10 in stable:
                selectbl.append('10musicvideo_view')
            if 11 in stable:
                selectbl.append('11artist')
            if 12 in stable:
                selectbl.append('12albumartistview')
            if 13 in stable:
                selectbl.append('13albumview')
            if 14 in stable:
                selectbl.append('14artistview')
            if 15 in stable:
                selectbl.append('15song')
            if 16 in stable:
                selectbl.append('16songartistview')
            if 17 in stable:
                selectbl.append('17songview')
            if 18 in stable:
                selectbl.append('18mServers')
            if 19 in stable:
                selectbl.append('19dupeTrack')
            if 20 in stable:
                selectbl.append('20mperfStats')
            if 21 in stable:
                selectbl.append('21mgenLog')
            if 22 in stable:
                selectbl.append('22msyncLog')
            if 23 in stable:
                selectbl.append('23nosyncVideo')
            if 24 in stable:
                selectbl.append('24mTrailers')
            exportData(selectbl)         

    except Exception as e:
        printexception()