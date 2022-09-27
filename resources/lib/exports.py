import xbmc
import xbmcgui
import xbmcplugin
import os
import xbmcaddon
import xbmcvfs
from media import openKodiDB, openNosyncDB, printexception, mgenlogUpdate, translate
import media
import csv  
from datetime import datetime

addon = xbmcaddon.Addon()
addon_path = addon.getAddonInfo("path")
addon_icon = addon_path + '/resources/icon.png'

def exportData(selectbl):                                        # CSV Output selected table

    try:

        #xbmc.log("Mezzmo selectable is: " +  str(selectbl), xbmc.LOGNOTICE)

        folderpath = xbmc.translatePath(os.path.join("special://home/", "output/"))
        if not xbmcvfs.exists(folderpath):
            xbmcvfs.mkdir(folderpath)
            xbmc.log("Mezzmo Export Output folder not found: " +  str(folderpath), xbmc.LOGNOTICE)

        for a in range(len(selectbl)):
            fpart = datetime.now().strftime('%H%M%S')
            selectindex = int(selectbl[a][:2])                   # Get list index to determine DB
            selectname = selectbl[a][2:]                         # Parse table name in DB

            outfile = folderpath + "mezzmo_" + selectname + "_" + fpart + ".csv"
            #xbmc.log("Mezzmo selectable is: " +  str(selectindex) + ' ' + selectname, xbmc.LOGNOTICE)
            if selectindex < 8:
                dbexport = openKodiDB()
            else:
                dbexport = openNosyncDB() 

            curm = dbexport.execute('SELECT * FROM '+selectname+'')
            recs = curm.fetchall()
            headers = [i[0] for i in curm.description]
            csvFile = csv.writer(open(outfile, 'wb'),
                             delimiter=',', lineterminator='\n',
                             quoting=csv.QUOTE_ALL, escapechar='\\')

            csvFile.writerow(headers)                       # Add the headers and data to the CSV file.
            for row in recs:
                recsencode = []
                # xbmc.log("Mezzmo output string length is: " +  str(len(row)), xbmc.LOGNOTICE)
                for item in range(len(row)):
                    if isinstance(row[item], int) or isinstance(row[item], float):  # Convert to strings
                        recitem = str(row[item])
                        recitem = recitem.encode('utf-8')
                    elif row[item] != None:
                        recitem = row[item].encode('utf-8')
                    else:
                        recitem = row[item]
                    recsencode.append(recitem) 
                csvFile.writerow(recsencode)                
            dbexport.close()

        outmsg = folderpath
        dialog_text = translate(30428) + outmsg 
        xbmcgui.Dialog().ok(translate(30429), dialog_text)

    except Exception as e:
        printexception()
        dbexport.close()
        mgenlog = translate(30430) + selectname
        xbmcgui.Dialog().notification(translate(30431), mgenlog, addon_icon, 5000)            
        xbmc.log(mgenlog, xbmc.LOGNOTICE)
        mgenlogUpdate(mgenlog)


def selectExport():                                            # Select table to export

    try:
        while True:
            stable = []
            selectbl = []
            tables = ["Kodi DB - Actors","Kodi DB - Episodes","Kodi DB - Movies","Kodi DB - TV Shows",  \
            "Kodi DB - Artwork","Kodi DB - Path","Kodi DB - Files","Kodi DB - Streamdetails",           \
            "Addon DB - uPNP Servers","Addon DB - Duplicates", "Addon DB - Performance Stats",          \
            "Addon DB - General Logs","Addon DB - Sync Logs","Addon DB - No Sync Videos","Addon DB - Trailers"]
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
                selectbl.append('08mServers')
            if 9 in stable:
                selectbl.append('09dupeTrack')
            if 10 in stable:
                selectbl.append('10mperfStats')
            if 11 in stable:
                selectbl.append('11mgenLog')
            if 12 in stable:
                selectbl.append('12msyncLog')
            if 13 in stable:
                selectbl.append('13nosyncVideo')
            if 14 in stable:
                selectbl.append('14mTrailers')
            exportData(selectbl)        

    except Exception as e:
        printexception()