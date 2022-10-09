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
    if installed_version == '10':
        return "MyMusic7.db"
    elif installed_version == '11':
        return "MyMusic18.db"
    elif installed_version == '12':
        return "MyMusic32.db"
    elif installed_version == '13':
        return "MyMusic46.db"
    elif installed_version == '14':
        return "MyMusic48.db"
    elif installed_version == '15':
        return "MyMusic52.db"
    elif installed_version == '16':
        return "MyMusic56.db"
    elif installed_version == '17':
        return "MyMusic60.db"
    elif installed_version == '18':
        return "MyMusic72.db"
    elif installed_version == '19':
        return "MyMusic82.db"
    elif installed_version == '20':
        return "MyMusic82.db"
       
    return ""  


def openKodiMuDB():                                   #  Open Kodi music database
    try:
        from sqlite3 import dbapi2 as sqlite
    except:
        from pysqlite2 import dbapi2 as sqlite
                      
    DB = os.path.join(xbmc.translatePath("special://database"), getmuDatabaseName())  
    db = sqlite.connect(DB)

    return(db)    
