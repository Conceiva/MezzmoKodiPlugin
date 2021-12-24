import xbmc
import xbmcgui
import xbmcplugin
import os
import xbmcvfs
import media
import urllib.request, urllib.error, urllib.parse
import urllib.request, urllib.parse, urllib.error
from datetime import datetime, timedelta

def updateKodiPlaycount(mplaycount, mtitle, murl, mseason, mepisode, mseries, kdbfile):

    try:
        from sqlite3 import dbapi2 as sqlite
    except:
        from pysqlite2 import dbapi2 as sqlite
                      
    DB = os.path.join(xbmcvfs.translatePath("special://database"), kdbfile)  
    db = sqlite.connect(DB)

    rfpos = murl.find(':',7)                               #  Get Mezzmo server port info
    serverport = '%' + murl[rfpos+1:rfpos+6] + '%'      

    lastplayed = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    newcount = '0'      

    xbmc.log('Mezzmo playcount mtitle, murl and serverport ' + mtitle + ' ' + murl + ' ' + serverport,  \
    xbmc.LOGDEBUG)
    xbmc.log('Mezzmo playcount mseason, mepisode and mseries ' + str(mseason) + ' ' + str(mepisode) +   \
    ' ' + str(mseries), xbmc.LOGDEBUG)     

    if mseason == 0 and mepisode == 0:                     #  Find movie file number
        curf = db.execute('SELECT idFile FROM movie_view WHERE strPATH LIKE ? and c00=?', (serverport, mtitle,))
        filetuple = curf.fetchone()
        if filetuple != None:
            filenumb = filetuple[0]
        else:
            filenumb = 0
        curf.close()
    elif mseason > 0 or mseason > 0:                       #  Find TV Episode file number
        curf = db.execute('SELECT idFile FROM episode_view WHERE strPATH LIKE ? and strTitle=? and c12=? \
        and c13=? ',(serverport, mseries, mseason, mepisode,))  
        filetuple = curf.fetchone()
        if filetuple != None:
            filenumb = filetuple[0]
        else:
            filenumb = 0      
        curf.close()

    if filenumb != 0 and mseason == 0 and mepisode == 0:   #  Update movie playcount
        if mplaycount == 0 and filenumb > 0:               #  Set playcount to 1
            newcount = '1'
            db.execute('UPDATE files SET playCount=?, lastPlayed=? WHERE idFile=?', (newcount, lastplayed, filenumb))
        elif mplaycount > 0 and filenumb > 0:              #  Set playcount to 0
            db.execute('UPDATE files SET playCount=?, lastPlayed=? WHERE idFile=?', (newcount, '', filenumb))
    elif filenumb != 0 and (mseason > 0 or mepisode > 0):  #  Update episode playcount
        if mplaycount == 0 and filenumb > 0:               #  Set playcount to 1
            newcount = '1'
            db.execute('UPDATE files SET playCount=?, lastPlayed=? WHERE idFile=?', (newcount, lastplayed, filenumb))
        elif mplaycount > 0 and filenumb > 0:              #  Set playcount to 0
            db.execute('UPDATE files SET playCount=?, lastPlayed=? WHERE idFile=?', (newcount, '', filenumb))   
    elif filenumb == 0:   
        mgenlog ='Mezzmo no watched action taken.  File not found in Kodi DB.  Please wait for sync. ' +  mtitle
        xbmc.log(mgenlog, xbmc.LOGINFO)
        mgenlog = '###' + mtitle
        media.mgenlogUpdate(mgenlog)   
        mgenlog ='Mezzmo no watched action taken.  File not found in Kodi DB.  Please wait for sync.'
        media.mgenlogUpdate(mgenlog)  
    if filenumb > 0:
        mgenlog ='Mezzmo Kodi playcount set to ' + newcount + ' for: ' + mtitle
        xbmc.log(mgenlog, xbmc.LOGINFO)
        mgenlog = '###' + mtitle
        media.mgenlogUpdate(mgenlog)   
        mgenlog ='Mezzmo Kodi playcount set to ' + newcount + ' for: '
        media.mgenlogUpdate(mgenlog)  

    db.commit()
    db.close()


def setPlaycount(url, objectID, count, mtitle):            #  Set Mezzmo play count

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
    req = urllib.request.Request(url, body.encode('utf-8'), headers)
    response = ''
    try:
        response = urllib.request.urlopen(req, timeout=60).read()
    except Exception as e:
        xbmc.log( 'EXCEPTION IN SetBookmark: ' + str(e), xbmc.LOGINFO)
        pass

    mgenlog ='Mezzmo server playcount set to ' + count + ' for: ' +      \
    mtitle
    xbmc.log(mgenlog, xbmc.LOGINFO)
    mgenlog = '###' + mtitle
    media.mgenlogUpdate(mgenlog)   
    mgenlog ='Mezzmo server playcount set to ' + count + ' for: '
    media.mgenlogUpdate(mgenlog)             

    return response


