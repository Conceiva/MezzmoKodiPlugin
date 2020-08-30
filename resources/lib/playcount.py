import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import os
import json
import urllib.request, urllib.error, urllib.parse
import urllib.request, urllib.parse, urllib.error
from datetime import datetime, timedelta

#xbmc.log('Name of script: ' + str(sys.argv[0]), xbmc.LOGINFO)
#xbmc.log('Number of arguments: ' + str(len(sys.argv)), xbmc.LOGINFO)
#xbmc.log('The arguments are: ' + str(sys.argv), xbmc.LOGINFO)


def updateKodiPlaycount(mplaycount, mtitle, murl, mseason, mepisode, mseries, kdbfile):

    try:
        from sqlite3 import dbapi2 as sqlite
    except:
        from pysqlite2 import dbapi2 as sqlite
                      
    DB = os.path.join(xbmc.translatePath("special://database"), kdbfile)  
    db = sqlite.connect(DB)

    rfpos = murl.find(':',7)                               #  Get Mezzmo server port info
    serverport = '%' + murl[rfpos+1:rfpos+6] + '%'      

    if mseason == 0 and mepisode == 0:                     #  Find movie file number
        curf = db.execute('SELECT idFile FROM movie_view WHERE strPATH LIKE ? and c00=?',(serverport, mtitle,))  
        filetuple = curf.fetchone()
        if filetuple != None:
            filenumb = filetuple[0]
        else:
            filenumb = 0
        curf.close()
    elif mseason > 0 or mseason > 0:                       #  Find TV Episode file number
        curf = db.execute('SELECT idFile FROM episode_view WHERE strPATH LIKE ? and strTitle=? and c12=? and \
        c13=? ',(serverport, mseries, mseason, mepisode,))  
        filetuple = curf.fetchone()
        if filetuple != None:
            filenumb = filetuple[0]
        else:
            filenumb = 0        
        curf.close()

    if filenumb != 0 and mseason == 0 and mepisode == 0:   #  Update movie playcount
        #xbmc.log('Filetuple ' + str(filenumb), xbmc.LOGINFO) 
        if mplaycount == 0 and filenumb > 0:               #  Set playcount to 1
            db.execute('UPDATE files SET playCount=? WHERE idFile=?', ('1', filenumb))
            xbmc.log('Mezzmo movie playcount set to watched: ' + mtitle, xbmc.LOGINFO)
        elif mplaycount > 0 and filenumb > 0:              #  Set playcount to 0
            db.execute('UPDATE files SET playCount=?, lastPlayed=?  WHERE idFile=?', ('0', '', filenumb))
            xbmc.log('Mezzmo movie playcount set to unwatched: ' + mtitle, xbmc.LOGINFO)
    elif filenumb != 0 and (mseason > 0 or mepisode > 0):  #  Update episode playcount
        #xbmc.log('Filetuple ' + str(filenumb), xbmc.LOGINFO) 
        if mplaycount == 0 and filenumb > 0:               #  Set playcount to 1
            db.execute('UPDATE files SET playCount=? WHERE idFile=?', ('1', filenumb))
            xbmc.log('Mezzmo episode playcount set to watched: ' + mtitle, xbmc.LOGINFO)
        elif mplaycount > 0 and filenumb > 0:              #  Set playcount to 0
            db.execute('UPDATE files SET playCount=?, lastPlayed=?  WHERE idFile=?', ('0', '', filenumb))
            xbmc.log('Mezzmo episode playcount set to unwatched: ' + mtitle, xbmc.LOGINFO)     
    elif filenumb == 0:   
        xbmc.log('Mezzmo no watched action taken.  File not found in Kodi DB. ', xbmc.LOGINFO)     

    db.commit()
    db.close()


vtitle = sys.argv[1]
vurl = sys.argv[2]
vseason = sys.argv[3]
vepisode = sys.argv[4]
playcount = sys.argv[5]
vseries = sys.argv[6]
dbfile = sys.argv[7]
updateKodiPlaycount(int(playcount), vtitle, vurl, int(vseason), int(vepisode), vseries, dbfile)