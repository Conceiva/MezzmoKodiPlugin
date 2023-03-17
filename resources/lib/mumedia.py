import xbmc
import xbmcgui
import xbmcplugin
import os
import xbmcaddon
from media import mgenlogUpdate, translate, settings, get_installedversion
import csv  
from datetime import datetime

addon = xbmcaddon.Addon()
addon_path = addon.getAddonInfo("path")
addon_icon = addon_path + '/resources/icon.png'

def getmuDatabaseName():
    installed_version = get_installedversion()
    if installed_version == '18':
        return "MyMusic72.db"
       
    return ""  


def openKodiMuDB():                                   #  Open Kodi music database
    try:
        from sqlite3 import dbapi2 as sqlite
    except:
        from pysqlite2 import dbapi2 as sqlite
                      
    DB = os.path.join(xbmc.translatePath("special://database"), getmuDatabaseName())  
    db = sqlite.connect(DB)

    return(db)    
