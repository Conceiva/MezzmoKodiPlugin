import xbmc
import xbmcgui
import xbmcplugin
import os
import urllib
import urllib2
import sys
import media
from datetime import datetime, timedelta


def updateKodiPlaycount(mplaycount, mtitle, murl, mseason, mepisode, mseries):

    db = media.openKodiDB()

    serverport = '%' + media.getServerport(murl) + '%'     #  Get Mezzmo server port info

    lastplayed = datetime.now().strftime('%Y-%m-%d %H:%M:%S')      
    newcount = '0'

    #xbmc.log('Mezzmo playcount mtitle and murl ' + mtitle.encode('utf-8', 'ignore') + ' ' + murl, xbmc.LOGDEBUG)
    #xbmc.log('Mezzmo playcount mseason, mepisode and mseries ' + str(mseason) + ' ' + str(mepisode) +   \
    #' ' + str(mseries), xbmc.LOGDEBUG)

    filenumb = 0     
    curf = db.execute('SELECT idFile FROM musicvideo_view WHERE strPATH LIKE ? and c00=?', (serverport, mtitle,))
    filetuple = curf.fetchone()
    if filetuple != None:
        filenumb = filetuple[0]     

    if mseason == 0 and mepisode == 0 and filenumb == 0:    #  Find movie file number
        curf = db.execute('SELECT idFile FROM movie_view WHERE strPATH LIKE ? and c00=?', (serverport, mtitle,))
        filetuple = curf.fetchone()
        if filetuple != None:
            filenumb = filetuple[0]
        else:
            filenumb = 0
        curf.close()
    elif mseason > 0 or mseason > 0 and filenumb == 0:      #  Find TV Episode file number
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
        mgenlog ='Mezzmo no watched action taken.  File not found in Kodi DB.  Please wait for sync. ' +      \
        mtitle.encode('utf-8', 'ignore')
        xbmc.log(mgenlog, xbmc.LOGNOTICE)
        mgenlog = '###' + mtitle.encode('utf-8', 'ignore')
        media.mgenlogUpdate(mgenlog)   
        mgenlog ='Mezzmo no watched action taken.  File not found in Kodi DB.  Please wait for sync.'
        media.mgenlogUpdate(mgenlog)     
    if filenumb > 0:
        mgenlog ='Mezzmo Kodi playcount set to ' + newcount + ' for: ' + mtitle.encode('utf-8', 'ignore')
        xbmc.log(mgenlog, xbmc.LOGNOTICE)
        mgenlog = '###' + mtitle.encode('utf-8', 'ignore')
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
    req = urllib2.Request(url, body, headers) 
    response = ''
    try:
        response = urllib2.urlopen(req, timeout=60).read()
    except Exception as e:
        xbmc.log( 'EXCEPTION IN SetPlaycount: ' + str(e))
        pass

    mgenlog ='Mezzmo server playcount set to ' + count + ' for: ' +      \
    mtitle.encode('utf-8', 'ignore')
    xbmc.log(mgenlog, xbmc.LOGNOTICE)
    mgenlog = '###' + mtitle.encode('utf-8', 'ignore')
    media.mgenlogUpdate(mgenlog)   
    mgenlog ='Mezzmo server playcount set to ' + count + ' for: '
    media.mgenlogUpdate(mgenlog)         
    return response




