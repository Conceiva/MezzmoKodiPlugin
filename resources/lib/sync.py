import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import os
from datetime import datetime, timedelta


def updateTexturesCache(contenturl):     # Update Kodi image cache timers
  
    try:
        from sqlite3 import dbapi2 as sqlite
    except:
        from pysqlite2 import dbapi2 as sqlite
                      
    DB = os.path.join(xbmc.translatePath("special://database"), "Textures13.db")
    db = sqlite.connect(DB)

    rfpos = contenturl.find(':',7)      #  Get Mezzmo server info
    serverport = '%' + contenturl[rfpos+1:rfpos+6] + '%'
    newtime = (datetime.now() + timedelta(days=-3)).strftime('%Y-%m-%d %H:%M:%S')
    cur = db.execute('UPDATE texture SET lasthashcheck=? WHERE URL LIKE ? and lasthashcheck=?', \
    (newtime, serverport, ""))          # Update Mezzmo image cache timers with no dates 
    rows = cur.rowcount       
    db.commit()
    db.close()
    xbmc.log('Mezzmo textures cache timers '  + str(rows) + ' rows updated.', xbmc.LOGNOTICE)       