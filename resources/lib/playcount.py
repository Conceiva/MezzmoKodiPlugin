import xbmc
import xbmcgui
import xbmcplugin
import os
import json
import urllib
import urllib2
import sys
from datetime import datetime, timedelta

#xbmc.log('Name of script: ' + str(sys.argv[0]), xbmc.LOGNOTICE)
#xbmc.log('Number of arguments: ' + str(len(sys.argv)), xbmc.LOGNOTICE)
#xbmc.log('The arguments are: ' + str(sys.argv), xbmc.LOGNOTICE)


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
        curf = db.execute('SELECT idFile, strFileName FROM movie_view WHERE strPATH LIKE ? and c00=?',  \
        (serverport, mtitle,))  
        filetuple = curf.fetchone()
        if filetuple != None:
            filenumb = filetuple[0]
            objectID = filetuple[1]
        else:
            filenumb = 0
            objectID = None
        curf.close()
    elif mseason > 0 or mseason > 0:                       #  Find TV Episode file number
        curf = db.execute('SELECT idFile, strFileName FROM episode_view WHERE strPATH LIKE ? and strTitle=? \
        and c12=? and c13=? ',(serverport, mseries, mseason, mepisode,))  
        filetuple = curf.fetchone()
        if filetuple != None:
            filenumb = filetuple[0]
            objectID = filetuple[1]
        else:
            filenumb = 0
            objectID = None        
        curf.close()

    if filenumb != 0 and mseason == 0 and mepisode == 0:   #  Update movie playcount
        if mplaycount == 0 and filenumb > 0:               #  Set playcount to 1
            newcount = '1'
            db.execute('UPDATE files SET playCount=? WHERE idFile=?', (newcount, filenumb))
        elif mplaycount > 0 and filenumb > 0:              #  Set playcount to 0
            newcount = '0'
            db.execute('UPDATE files SET playCount=?, lastPlayed=?  WHERE idFile=?', (newcount, '', filenumb))
    elif filenumb != 0 and (mseason > 0 or mepisode > 0):  #  Update episode playcount
        if mplaycount == 0 and filenumb > 0:               #  Set playcount to 1
            newcount = '1'
            db.execute('UPDATE files SET playCount=? WHERE idFile=?', (newcount, filenumb))
        elif mplaycount > 0 and filenumb > 0:              #  Set playcount to 0
            newcount = '0'
            db.execute('UPDATE files SET playCount=?, lastPlayed=?  WHERE idFile=?', (newcount, '', filenumb))   
    elif filenumb == 0:   
        xbmc.log('Mezzmo no watched action taken.  File not found in Kodi DB. Please wait for sync.' +      \
        mtitle.encode('utf-8', 'ignore'), xbmc.LOGNOTICE)    

    if filenumb > 0:
         xbmc.log('Mezzmo Kodi playcount set to ' + newcount + ' for: ' +          \
         mtitle.encode('utf-8', 'ignore'), xbmc.LOGNOTICE)  

    db.commit()
    db.close()
    return[objectID, str(newcount)]                        #  Return Mezzmo objectID and new playcount


def SetPlaycount(url, objectID, count, mtitle):            #  Set Mezzmo play count

    headers = {'content-type': 'text/xml', 'accept': '*/*', 'SOAPACTION' : '"urn:schemas-upnp-org:service:ContentDirectory:1#X_SetPlaycount"', 'User-Agent': 'Kodi (Mezzmo Addon)'}
    body = '''<?xml version="1.0"?>
    <s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
  <s:Body>
    <u:X_SetPlaycount xmlns:u="urn:schemas-upnp-org:service:ContentDirectory:1">
     <ObjectID>'''
    body += objectID
    body += '''</ObjectID>
      <Playcount>'''
    body += count
    body += '''</Playcount>
    </u:X_SetPlaycount>
  </s:Body>
</s:Envelope>'''
    req = urllib2.Request(url, body, headers) 
    response = ''
    try:
        response = urllib2.urlopen(req, timeout=60).read()
    except Exception as e:
        xbmc.log( 'EXCEPTION IN SetPlaycount: ' + str(e))
        pass
    xbmc.log('Mezzmo server playcount set to ' + count + ' for: ' + mtitle.encode('utf-8', 'ignore'), xbmc.LOGNOTICE)          
    return response


title = sys.argv[1]                                                 # Extract passed variables
vurl = sys.argv[2]
vseason = sys.argv[3]
vepisode = sys.argv[4]
playcount = sys.argv[5]
vseries = sys.argv[6]
dbfile = sys.argv[7]
contenturl = sys.argv[8]

vtitle = title.decode('utf-8', 'ignore')

mezzmovars = updateKodiPlaycount(int(playcount), vtitle, vurl,      \
int(vseason), int(vepisode), vseries, dbfile)                       #  Update Kodi DB playcount

if mezzmovars[0] != None:                                           #  Update Mezzmo playcount if in Kodi DB
    SetPlaycount(contenturl, mezzmovars[0], mezzmovars[1], vtitle)
    xbmc.executebuiltin('Container.Refresh()')



