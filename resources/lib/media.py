import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmcvfs
import os, sys, linecache
import json, base64
import urllib.request, urllib.error, urllib.parse
from datetime import datetime
import playcount, bookmark


def settings(setting, value = None):
    # Get or add addon setting
    if value:
        xbmcaddon.Addon().setSetting(setting, value)
    else:
        return xbmcaddon.Addon().getSetting(setting)   

def translate(text):
    return xbmcaddon.Addon().getLocalizedString(text)

def priorSearch():                                    # Check for prior searches
    
    try:
        srchlimit = int(settings('srchlimit'))        # Number of prior searches to present 
        if srchlimit == '':                           # Check search history setting
            srchlimit = 10
        if srchlimit == 0:                            # If zero new search
            return('')
        pdfile = openNosyncDB()                       # Open Perf Stats database
        pselect = []
        curps = pdfile.execute('SELECT msSearch FROM mSearch order by msDate desc LIMIT ?', (srchlimit,))
        psrchtext = curps.fetchall()                  # Get previous from search database
        if psrchtext:                                 # If prior searches in search table 
            pselect = ["[COLOR blue]Enter new search[/COLOR]"]
            for x in range(len(psrchtext)):
                pselect.append(psrchtext[x][0])       # Convert rows to list for dialog box
            ddialog = xbmcgui.Dialog()
            xbmc.log('The current list is: ' + str(pselect), xbmc.LOGDEBUG)  
            vdate = ddialog.select('Prior Search Text', pselect)
            if vdate > 0:                             # User selection
                term = pselect[vdate]
            elif vdate == -1:                         # User cancel
                term = 'cancel'
            elif vdate == 0:                          # User new search
                term = '' 
        else:                                         # No previous searches
            term = ''  
        pdfile.close()
        xbmc.log('The user selection is: ' + str(term), xbmc.LOGDEBUG) 
        return(term)
    except:
        mgenlog ='Mezzmo problem getting prior searches from DB: '
        xbmc.log(mgenlog, xbmc.LOGINFO)
        mgenlogUpdate(mgenlog)
        return('')
        pass          


def addSearch(stext):                                  # Add new searches
    
    try:
        psfile = openNosyncDB()                        # Open Perf Stats database
        currentDateTime = datetime.now()
        psfile.execute('INSERT or REPLACE into mSearch (msDate, msSearch) values (?, ?)',   \
        (currentDateTime, stext))
        psfile.execute('delete from mSearch where msDate not in (select msDate from         \
        mSearch order by msDate desc limit ?)', (30,))  
        psfile.commit() 
        psfile.close()
    except:
        mgenlog ='Mezzmo problem writing new search to DB: ' + str(stext)
        xbmc.log(mgenlog, xbmc.LOGINFO)
        mgenlogUpdate(mgenlog)          
        pass


def checkTVShow(fileId, seriesname, mgenre, db, mrating, mstudio, micon, murl, knative): 
                                                                     # Check if TV show exists in database

    cure = db.execute('SELECT idShow, c14 FROM tvshow WHERE c00=? and c17=?',(seriesname, \
    int(fileId[3]),))
    showtuple = cure.fetchone()
    if not showtuple:				 # If not found add show
        mgenres = mgenre.replace(',' , ' /')                         #  Format genre for proper Kodi display
        db.execute('INSERT into tvshow (c00, c06, c08, c09, c17, c13, c14) values         \
        (?, ?, ?, ?, ? ,? ,?)', (seriesname, micon, mgenres, seriesname, fileId[3],       \
        mrating, mstudio, ))
        curs = db.execute('SELECT idShow, c14 FROM tvshow WHERE c00=? and c17=?',         \
        (seriesname, fileId[3],))
        showtuple = curs.fetchone()       	 # Get new TV Show id
        shownumb = showtuple[0]
        curs.close()
        insertArt(shownumb, db, 'tvshow', murl, micon)
        insertStudios(shownumb, db, 'tvshow', mstudio, knative) 
        #xbmc.log('TV Show added ' + seriesname + " " + str(shownumb), xbmc.LOGINFO)
    else:
        shownumb = showtuple[0]
        sstudio = showtuple[1]
        #xbmc.log('TV Show found ' + seriesname + " " + str(shownumb), xbmc.LOGINFO)                 
        curs = db.execute('SELECT c05 from episode where idShow =? order by c05 asc        \
        limit 1',(shownumb,))
        showtuple = curs.fetchone()
        if showtuple:
            db.execute('UPDATE tvshow SET c05=? WHERE idShow=?', (showtuple[0], shownumb,))
            insertStudios(shownumb, db, 'tvshow', mstudio, knative) 
        if sstudio == None and mstudio != None:
            db.execute('UPDATE tvshow SET c14=? WHERE idShow=?', (mstudio, shownumb,)) 
        curs.close()        
    
    cure.close()
    return(shownumb)


def checkSeason(db, shownumb, season, murl, micon):   # Check if Episode season exists in seasons table

    curse = db.execute('SELECT idSeason FROM seasons WHERE idShow=? and season=?',(shownumb, season,))
    seasontuple = curse.fetchone()
    if not seasontuple:				 # If not found add season
        db.execute('INSERT into seasons(idshow, season, name) values (?, ?, ?)', \
        (shownumb, season, 'Season ' + str(season),))
        curss = db.execute('SELECT idSeason FROM seasons WHERE idShow=? and season=?',(shownumb, season,))
        seasontuple = curss.fetchone()
        seasonnumb = seasontuple[0]
        insertArt(seasonnumb, db, 'season', murl, micon)
        curss.close()
    else:
        seasonnumb = seasontuple[0]
    #xbmc.log('The current season number is: ' + str(seasonnumb), xbmc.LOGINFO)

    curse.close()
    return(seasonnumb)                           # Return seasons table idSeason  


def get_installedversion():
    # retrieve current installed version
    json_query = xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Application.GetProperties", "params": {"properties": ["version", "name"]}, "id": 1 }')
    json_query = json.loads(json_query)
    version_installed = []
    if 'result' in json_query and 'version' in json_query['result']:
        version_installed  = json_query['result']['version']['major']
    return str(version_installed)


def getDatabaseName():
    installed_version = get_installedversion()
    if installed_version == '19':
        return "MyVideos119.db"
    elif installed_version == '20':
        return "MyVideos121.db"
    elif installed_version == '21':
        return "MyVideos124.db"
      
    return ""  


def openKodiDB():                                   #  Open Kodi database
    try:
        from sqlite3 import dbapi2 as sqlite
    except:
        from pysqlite2 import dbapi2 as sqlite
                      
    DB = os.path.join(xbmcvfs.translatePath("special://database"), getDatabaseName())
    db = sqlite.connect(DB)

    db.execute('PRAGMA cache_size = -30000;')
    #db.execute('PRAGMA journal_mode = WAL;')
    #db.execute('PRAGMA synchronous = NORMAL;')

    return(db)    


def openNosyncDB():                                 #  Open Mezzmo noSync database
    try:
        from sqlite3 import dbapi2 as sqlite
    except:
        from pysqlite2 import dbapi2 as sqlite
                      
    DBconn = os.path.join(xbmcvfs.translatePath("special://database"), "Mezzmo10.db")  
    dbsync = sqlite.connect(DBconn)

    return(dbsync) 


def checkNosyncDB():                                 #  Verify Mezzmo noSync database

    dbsync = openNosyncDB()

    dbsync.execute('CREATE table IF NOT EXISTS nosyncVideo (VideoTitle TEXT, Type TEXT, idFile INTEGER)')
    dbsync.execute('CREATE INDEX IF NOT EXISTS nosync_1 ON nosyncVideo (VideoTitle)')
    dbsync.execute('CREATE INDEX IF NOT EXISTS nosync_2 ON nosyncVideo (Type)')

    dbsync.execute('CREATE table IF NOT EXISTS mperfStats (psDate TEXT, psTime TEXT, \
    psPlaylist TEXT, psCount TEXT, pSrvTime TEXT, mSrvTime TEXT, psTTime TEXT,       \
    psDispRate TEXT)')
    dbsync.execute('CREATE INDEX IF NOT EXISTS perfs_1 ON mperfStats (psDate)')
    dbsync.execute('CREATE INDEX IF NOT EXISTS perfs_2 ON mperfStats (psPlaylist)')

    dbsync.execute('CREATE table IF NOT EXISTS mperfIndex (psObject TEXT, psPlaylist TEXT)')
    dbsync.execute('CREATE INDEX IF NOT EXISTS mperfs_1 ON mperfIndex (psPlaylist)')

    dbsync.execute('CREATE table IF NOT EXISTS dupeTrack (dtDate TEXT, dtFnumb TEXT, \
    dtLcount TEXT, dtTitle TEXT, dtType TEXT)')
    dbsync.execute('CREATE INDEX IF NOT EXISTS dtrack_1 ON dupeTrack (dtDate)')

    dbsync.execute('CREATE table IF NOT EXISTS msyncLog (msDate TEXT, msTime TEXT,   \
    msSyncDat TEXT)')
    dbsync.execute('CREATE INDEX IF NOT EXISTS msync_1 ON msyncLog (msDate)')

    dbsync.execute('CREATE table IF NOT EXISTS mgenLog (mgDate TEXT, mgTime TEXT,   \
    mgGenDat TEXT)')
    dbsync.execute('CREATE INDEX IF NOT EXISTS mgen_1 ON mgenLog (mgDate)')

    dbsync.execute('CREATE table IF NOT EXISTS mSearch (msDate TIMESTAMP, msSearch TEXT)')
    dbsync.execute('CREATE UNIQUE INDEX IF NOT EXISTS msearch_2 ON mSearch (msSearch)')
    dbsync.execute('CREATE INDEX IF NOT EXISTS msearch_1 ON mSearch (msDate)')

    dbsync.execute('CREATE table IF NOT EXISTS mServers (srvUrl TEXT, srvName TEXT,  \
    controlUrl TEXT, mSync TEXT, sManuf TEXT, sModel TEXT, sIcon TEXT, sDescr TEXT,  \
    sUdn TEXT)')
    dbsync.execute('CREATE UNIQUE INDEX IF NOT EXISTS mserver_1 ON mServers (controlUrl)')

    dbsync.execute('CREATE table IF NOT EXISTS mPictures (mpTitle TEXT, mpUrl TEXT,   \
    mpVar1 TEXT, mpVar2 TEXT, mpVar3 TEXT)')
    dbsync.execute('CREATE INDEX IF NOT EXISTS mpicture_1 ON mPictures (mpTitle)')
    dbsync.execute('CREATE INDEX IF NOT EXISTS mpicture_2 ON mPictures (mpUrl)')
    dbsync.commit()

    dbsync.execute('CREATE table IF NOT EXISTS mTrailers (trTitle TEXT, trUrl TEXT,   \
    trID TEXT, trPlay TEXT, trVar1 TEXT, trVar2 TEXT)')
    dbsync.execute('CREATE INDEX IF NOT EXISTS mtrailer_1 ON mTrailers (trTitle)')
    dbsync.execute('CREATE INDEX IF NOT EXISTS mtrailer_2 ON mTrailers (trID)')
    dbsync.execute('CREATE INDEX IF NOT EXISTS mtrailer_3 ON mTrailers (trUrl)')
    dbsync.execute('CREATE INDEX IF NOT EXISTS mtrailer_4 ON mTrailers (trVar2)')
    dbsync.commit()

    dbsync.execute('CREATE table IF NOT EXISTS mKeywords (kyTitle TEXT, kyType TEXT,  \
    kyVar1 TEXT, kyVar2 TEXT, kyVar3 TEXT, kyVar4 TEXT)')
    dbsync.execute('CREATE INDEX IF NOT EXISTS mKeyword_1 ON mKeywords (kyTitle, kyType)')
    dbsync.execute('CREATE INDEX IF NOT EXISTS mKeyword_2 ON mKeywords (kyTitle, kyType, kyVar1)')
    dbsync.commit()

    dbsync.execute('CREATE TABLE IF NOT EXISTS mCollection (coll_id integer primary key,    \
    name TEXT)')
    dbsync.execute('CREATE TABLE  IF NOT EXISTS mCollection_link (coll_id integer,          \
    media_id integer, media_type TEXT)')
    dbsync.execute('CREATE UNIQUE INDEX IF NOT EXISTS mCollection_1 ON mCollection (name)')
    dbsync.execute('CREATE UNIQUE INDEX IF NOT EXISTS mCollection_link_1 ON mCollection_link \
    (coll_id, media_type, media_id)')
    dbsync.execute('CREATE UNIQUE INDEX IF NOT EXISTS mCollection_link_2 ON mCollection_link \
    (media_id, media_type, coll_id)')
    dbsync.execute('CREATE INDEX IF NOT EXISTS mCollection_link_3 ON mCollection_link (media_type)')

    try:
        dbsync.execute('ALTER TABLE mServers ADD COLUMN sUdn TEXT')
    except:
        xbmc.log('Mezzmo check nosync DB. No column sUdn: ' , xbmc.LOGDEBUG)     

    try:
        dbsync.execute('ALTER TABLE mTrailers ADD COLUMN trVar3 TEXT')
        dbsync.execute('ALTER TABLE mTrailers ADD COLUMN trPremiered TEXT')
        dbsync.execute('ALTER TABLE mTrailers ADD COLUMN trYear INTEGER')
        dbsync.execute('CREATE INDEX IF NOT EXISTS mtrailer_4 ON mTrailers (trYear)')
        dbsync.execute('CREATE INDEX IF NOT EXISTS mtrailer_5 ON mTrailers (trPremiered)')
    except:
        xbmc.log('Mezzmo check nosync DB. No column trVar3: ' , xbmc.LOGDEBUG) 

    try:
        dbsync.execute('ALTER TABLE mTrailers ADD COLUMN mPcount INTEGER')  
        dbsync.execute('CREATE INDEX IF NOT EXISTS mtrailer_6 ON mTrailers (mPcount)')
    except:
        xbmc.log('Mezzmo check nosync DB. No column mPcount: ' , xbmc.LOGDEBUG)

    try:
        dbsync.execute('ALTER TABLE mPictures ADD COLUMN iWidth INTEGER')
        dbsync.execute('ALTER TABLE mPictures ADD COLUMN iHeight INTEGER')
        dbsync.execute('ALTER TABLE mPictures ADD COLUMN iDate TEXT')
        dbsync.execute('ALTER TABLE mPictures ADD COLUMN iDesc TEXT')
    except:
        xbmc.log('Mezzmo check nosync DB. No column iWidth: ' , xbmc.LOGDEBUG)  

    dbsync.commit()
    dbsync.close()


def getServerport(contenturl):                  #  Get Mezzmo server port info

    lfpos = contenturl.find(':',7)
    rfpos = contenturl.find('/', lfpos)             
    serverport = contenturl[lfpos+1:rfpos]
    #xbmc.log('Mezzmo server port is: ' + serverport, xbmc.LOGINFO)     
    return(serverport)


def syncCount(dbsync, mtitle, mtype):

    #xbmc.log('Mezzmo nosync syncCount called: ' + mtitle, xbmc.LOGINFO)  
    dupes = dbsync.execute('SELECT VideoTitle FROM nosyncVideo WHERE VideoTitle=? and Type=?', \
    (mtitle, mtype))
    dupetuple = dupes.fetchone() 
    if dupetuple and settings('mdupelog') == 'true': #  Check for nosync duplicate 
        currdlDate = datetime.now().strftime('%Y-%m-%d')
        dbsync.execute('INSERT into dupeTrack(dtDate, dtFnumb, dtLcount, dtTitle, dtType) values \
        (?, ?, ?, ?, ?)', (currdlDate, 0, 0, mtitle, mtype))
        msynclog = 'Mezzmo ' + mtype + ' duplicate found - Title: ' +  mtitle
        currmsTime = datetime.now().strftime('%H:%M:%S:%f')
        dbsync.execute('INSERT into msyncLog(msDate, msTime, msSyncDat) values (?, ?, ?)',      \
        (currdlDate, currmsTime, msynclog))
        if settings('reduceslog') == 'false':
            xbmc.log(msynclog, xbmc.LOGINFO)
    elif not dupetuple:                         #  Insert into nosync table if not dupe
        dbsync.execute('INSERT into nosyncVideo (VideoTitle, Type) values (?, ?)', (mtitle, mtype))    

    dbsync.commit()        
    #dupes.close()
    del dupes, dupetuple


def countsyncCount():                           # returns count records in noSync DB 

    dbconn = openNosyncDB()
   
    curm = dbconn.execute('SELECT count (Type) FROM nosyncVideo WHERE Type LIKE ?', ("nosync",))
    nosynccount = curm.fetchone()[0]

    cure = dbconn.execute('SELECT count (Type) FROM nosyncVideo WHERE Type LIKE ?', ("livec",))
    liveccount = cure.fetchone()[0]

    curt = dbconn.execute('SELECT count (trUrl) FROM mTrailers',)
    trailcount = curt.fetchone()[0]

    cure.close()
    curm.close()
    curt.close()    
    dbconn.close()
    return[nosynccount, liveccount, trailcount] 


def addTrailers(dbsync, mtitle, trailers, prflocaltr, myear, mpcount, mpremiered, micon, imdb_id): 
    #  Add movie trailers to Mezzmo10db

    try:
        localcount = 0
        ytbase64 = 'aHR0cHM6Ly93d3cueW91dHViZS5jb20vd2F0Y2g'
        ytmatch = '%' + ytbase64 + '%'       
        trlength = len(trailers)
        #xbmc.log('Mezzmo trailers: ' + str(trlength) , xbmc.LOGINFO) 
        if trlength > 0:
            for trailer in trailers:            #  Get count of local trailers
                if ytbase64 not in trailer:
                    localcount += 1
                    xbmc.log('Mezzmo local trailer found: ' + mtitle , xbmc.LOGDEBUG)

            if prflocaltr == 'true' and localcount > 0: 
                dupes = dbsync.execute('SELECT count (trUrl), mPcount FROM mTrailers WHERE trTitle=?   \
                and trUrl NOT LIKE ?', (mtitle, ytmatch,))
            else:
                dupes = dbsync.execute('SELECT count (trUrl), mPcount FROM mTrailers WHERE trTitle=?', \
                (mtitle,))
            dupetuple = dupes.fetchone()
            xbmc.log('Mezzmo trailers: ' + str(trlength) + ' ' + str(dupetuple[0]) + ' ' +               \
            str(localcount) + ' ' + mtitle, xbmc.LOGDEBUG)

            if (mpcount != dupetuple[1] and dupetuple[0] > 0):  # Update trailer db play counts
                dbsync.execute('UPDATE mTrailers SET mPcount=? WHERE trTitle=?', (mpcount, mtitle,))          

            if (prflocaltr == 'false' and dupetuple[0] != trlength) or (prflocaltr == 'true' and          \
            localcount > 0 and dupetuple[0] != localcount) or (prflocaltr == 'true' and localcount == 0   \
            and dupetuple[0] != trlength): 
                xbmc.log('Mezzmo trailer updated needed: ' + mtitle , xbmc.LOGDEBUG)                 
                dbsync.execute('DELETE from mTrailers WHERE trTitle=?', (mtitle,))     
                a = 1
                match = 0
                for trailer in trailers:
                    if ytbase64 in trailer:
                        match = 1
                    else:
                        match = 0
                    if (match == 0) or (prflocaltr == 'false') or (prflocaltr == 'true' and match == 1     \
                    and localcount == 0):
                        if match == 1:
                            try:
                                slice = trailer[trailer.find('Y2g_') + 4:trailer.find('&cva')]  # Decode You Tube Trailer
                                sliceb = base64.b64decode(slice)
                                orgtrailer = 'https://www.youtube.com/watch?' + sliceb.decode()
                            except Exception as e:
                                orgtrailer = 'You Tube'
                                xbmc.log('Mezzmo error decoding You Tube trailer: ' + mtitle + ' ' + str(e), xbmc.LOGDEBUG)
                        else:
                            try:
                                slice = trailer[trailer.find('url=') + 4:trailer.find('&cva')]  # Decode Local Trailer
                                sliceb = base64.b64decode(slice)
                                orgtrailer = sliceb
                            except Exception as e:  
                                orgtrailer = 'Local'
                                xbmc.log('Mezzmo error decoding local trailer: ' + mtitle + ' ' + str(e), xbmc.LOGDEBUG)
                        try:
                            dbsync.execute('INSERT into mTrailers (trTitle, trUrl, trID, trPlay, trVar1, trYear, mPcount, \
                            trPremiered, trVar3, trVar2) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (mtitle, trailer,        \
                            str(a), "0", orgtrailer, int(myear), mpcount, mpremiered, micon, imdb_id))
                        except:
                            orgtrailer = "Unable to decode local trailer"
                            dbsync.execute('INSERT into mTrailers (trTitle, trUrl, trID, trPlay, trVar1, trYear, mPcount,  \
                            trPremiered, trVar3, trVar2) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (mtitle, trailer,         \
                            str(a), "0", orgtrailer, int(myear), mpcount, mpremiered, micon, imdb_id))
                        a += 1            
            dbsync.commit()


    except Exception as e:
        xbmc.log('Mezzmo problem adding trailers to db: ' + mtitle + ' ' + str(e), xbmc.LOGINFO)  
        pass


def autostart():                                #  Check for autostart

    autourl = settings('autostart')
    mgenlog ='Mezzmo background service started.'
    #xbmc.log(mgenlog, xbmc.LOGINFO)
    mgenlogUpdate(mgenlog, 'yes') 
    if len(autourl) > 6:    
        xbmc.executebuiltin('ActivateWindow(%s, %s)' % ('10025', autourl))   
        mgenlog ='Mezzmo autostart user GUI interface enabled.'
        #xbmc.log(mgenlog, xbmc.LOGINFO)
        mgenlogUpdate(mgenlog, 'yes') 


def getPath(itemurl):		            # Find path string for media file

    rtrimpos = itemurl.rfind('/')           # Check for container / path change
    pathcheck = itemurl[:rtrimpos+1]
    #xbmc.log('The media file path is : ' + pathcheck, xbmc.LOGINFO)
    return(pathcheck)   


def getMServer(itemurl):		    # Find server string for media file

    rtrimpos = itemurl.find('/', 7)  
    serverid = itemurl[:rtrimpos+1]
    #xbmc.log('The serverid : ' + serverid, xbmc.LOGINFO)
    return(serverid)  


def urlMatch(url1, url2):                       #  Check if URLs match with or without DNS

    try:
        if not url1[7].isdigit() or not url2[7].isdigit():    
            compare1 = url1[url1.rfind(':'):]   #  If DNS only compare port and file name
            compare2 = url2[url2.rfind(':'):]       
        else:
            compare1 = url1
            compare2 = url2
        #xbmc.log('Compare1 and Compare2 : ' + compare1 + " " + compare2, xbmc.LOGINFO)
        if compare1 == compare2:
            return(True)
        else:
            return(False)
    except:
        pass
        return(False)


def countKodiRecs(contenturl):                  # returns count records in Kodi DB 

    db = openKodiDB()

    serverport = '%' + getServerport(contenturl) + '%'     #  Get Mezzmo server port info

    curm = db.execute('SELECT count (idFile) FROM files INNER JOIN path ON path.idPath = files.idPath \
    WHERE strpath LIKE ?', (serverport,))
    recscount = curm.fetchone()[0]
    
    msynclog = 'Mezzmo total Kodi DB record count: ' + str(recscount)
    #xbmc.log(msynclog, xbmc.LOGINFO)
    mezlogUpdate(msynclog)

    curm.close()   
    db.close()
    return(recscount) 


def mComment(minfo, mduration,moffsetmenu):     #  Update music metadata comments

    artistpad = '{0:21}'.format('Artist:')
    songpad = '{0:19}'.format('Song:')
    playpad = '{0:16}'.format('Playcount:')
    pcount = '{0:50}'.format(str(minfo['playcount']))
    durpad = '{0:16}'.format('Duration: ')
    mdurpad = '{0:26}'.format(mduration[3:-4])
    lplaypad = '{0:15}'.format('Last Played: ')
    if minfo['lastplayed'] == '0':
        lplayed = 'Not Played Yet '
    else:
        lplayed = minfo['lastplayed']
    width = 55 - len(lplayed)
    lpcount = '{0:{width}}'.format(lplayed, width=width)
    if moffsetmenu == '00:00:00':
        moffsetmenu = 'No Bookmark Set'
    bmarkpad = '{0:13}'.format('Bookmark: ')
    
    comment = str('\n[COLOR blue]' + artistpad + '[/COLOR]' + minfo['artist'][0]  \
    + '\n[COLOR blue]' + songpad + '[/COLOR]' + minfo['title']                    \
    + '\n[COLOR blue]' + playpad + '[/COLOR]' + pcount                            \
    + '[COLOR blue]' + durpad + '[/COLOR]' + mduration[3:-4]                      \
    + '\n[COLOR blue]' + lplaypad + '[/COLOR]' + lpcount                          \
    + '[COLOR blue]' + bmarkpad + '[/COLOR]' + moffsetmenu)

    return(comment)


def optimizeDB():                               # Optimize Kodi DB 

    db = openKodiDB()
    db.execute('REINDEX',)
    db.execute('VACUUM',)
    db.commit()    
    db.close()

    db = openNosyncDB()                         # Optimize nosync DB
    db.execute('REINDEX',)
    db.execute('VACUUM',)
    db.commit()    
    db.close()

    mgenlog ='Mezzmo database reindex and vacuum complete.'
    #xbmc.log(mgenlog, xbmc.LOGINFO)
    mgenlogUpdate(mgenlog)


def displayTitles(mtitle):                     #  Remove common Mezzmo Display Title variables
    ctitle = mtitle
    if not str.isdigit(ctitle[:3]):
        intest1 = 1000
    else:
        intest1 = int(mtitle[:3])

    if not str.isdigit(ctitle[-5:-1]):    
        intest2 = 0
    else:
        intest2 = int(mtitle[-5:-1])

    if len(mtitle) >= 8:
        if mtitle[4] == '-' and intest1 <= 999:         # check for Mezzmo %FILECOUNTER% in video title
            dtitle = mtitle[6:len(mtitle)]
        elif mtitle[len(mtitle)-6] == '(' and mtitle[len(mtitle)-1] == ')' and intest2 >= 1900 and \
        mtitle[len(mtitle)-8] != '-':
            dtitle = mtitle[:-7]                        # check for Mezzmo %YEAR% in video title
        else:
            dtitle = mtitle                             # else leave unchanged    
    else:
        dtitle = mtitle

    return(dtitle)


def tvChecker(mseason, mepisode, mkoditv, mmtitle, mcategories):  # Kodi dB add check logic
    tvcheck = 1
    lvcheck = 0
    nsyncount = 0

    if (int(mseason) > 0  or int(mepisode) > 0) and mkoditv == 'Off':  #  Don't add TV shows
        tvcheck = 0

    if mcategories != None and mcategories.text != None:
        if 'nosync' in mcategories.text.lower():
            tvcheck = 0
            nsyncount = 1
            xbmc.log('Nosync file found: ' + mmtitle, xbmc.LOGDEBUG)
        if ('tv show' not in mcategories.text.lower()) and mkoditv == 'Category':
            tvcheck = 0
            
    if mmtitle[:13] == 'Live channel:' :                #  Do not add live channels to Kodi
        tvcheck = 0
        lvcheck = 1

    #xbmc.log('TV check value is: ' + str(tvcheck), xbmc.LOGINFO)

    return[tvcheck, lvcheck, nsyncount]


def checkDupes(filenumb, lastcount, mtitle):             #  Add Dupelicate logs to dupe DB

    dlfile = openNosyncDB()                              #  Open Dupe log database

    currdlDate = datetime.now().strftime('%Y-%m-%d')
    curdl = dlfile.execute('SELECT * FROM dupeTrack WHERE dtDate=? and dtTitle=?',(currdlDate, mtitle))
    dupltuple = curdl.fetchone()
    if not dupltuple:				         # If not found add dupe log
        dlfile.execute('INSERT into dupeTrack(dtDate, dtFnumb, dtLcount, dtTitle, dtType) values      \
        (?, ?, ?, ?, ?)', (currdlDate, filenumb, lastcount, mtitle, "V"))
        xbmc.log('Mezzmo duplicate found.  Kodi file table record #: ' + str(filenumb) + ' Title: ' +   \
        str(lastcount) + ' ' + mtitle, xbmc.LOGINFO)
    else:
        xbmc.log('Mezzmo duplicate already in DB.  Kodi record #: ' + str(filenumb) + ' Title: ' +      \
        str(lastcount) + ' ' + mtitle, xbmc.LOGINFO)        
    dlfile.commit()
    dlfile.close()


def mezlogUpdate(msynclog, reduceslog = 'no'): #  Add Mezzmo sync logs to DB and logfile

    msfile = openNosyncDB()                              #  Open Synclog database

    currmsDate = datetime.now().strftime('%Y-%m-%d')
    currmsTime = datetime.now().strftime('%H:%M:%S:%f')
    msfile.execute('INSERT into msyncLog(msDate, msTime, msSyncDat) values (?, ?, ?)',                 \
    (currmsDate, currmsTime, msynclog))
     
    msfile.commit()
    msfile.close()

    if settings('reduceslog') == 'false' or reduceslog != 'no':
        xbmc.log(msynclog, xbmc.LOGINFO)                 #  Write to Kodi logfile


def mgenlogUpdate(mgenlog, reduceglog = 'no'):           #  Add Mezzmo general logs to DB

    try:
        mgfile = openNosyncDB()                          #  Open Synclog database

        currmsDate = datetime.now().strftime('%Y-%m-%d')
        currmsTime = datetime.now().strftime('%H:%M:%S:%f')
        mgfile.execute('INSERT into mgenLog(mgDate, mgTime, mgGenDat) values (?, ?, ?)',                \
        (currmsDate, currmsTime, mgenlog))
     
        mgfile.commit()
        mgfile.close()

        if settings('reduceglog') == 'false' or reduceglog != 'no':
            xbmc.log(mgenlog, xbmc.LOGINFO)             #  Write to Kodi logfile

    except Exception as e:
        xbmc.log('Problem writing to general log DB: ' + str(e), xbmc.LOGINFO)
        pass


def getSyncURL():                                      # Get Sync srver URL

    svrfile = openNosyncDB()                           # Open server database    
    curps = svrfile.execute('SELECT controlUrl FROM mServers WHERE mSync=?', ('Yes',))
    srvrtuple = curps.fetchone()                       # Get server from database
    if srvrtuple:
        syncurl = srvrtuple[0]
    else:                                              # Sync srver not set yet
        syncurl = 'None'
    svrfile.close()
    return syncurl    


def kodiCleanDB(force):

    ContentDeleteURL = getSyncUrl()                    #  Get current sync contenturl
    if ContentDeleteURL == 'None':
        mgenlog = translate(30426)
        #xbmc.log(mgenlog, xbmc.LOGINFO)
        mgenlogUpdate(mgenlog)
        settings('kodiclean', 'false')
        name = xbmcaddon.Addon().getAddonInfo('name')
        cleanmsg = translate(30426)
        icon = xbmcaddon.Addon().getAddonInfo("path") + '/resources/icon.png'
        xbmcgui.Dialog().notification(name, cleanmsg, icon)
        return    
    if settings('kodiclean') != 'false':               #  clears Kodi DB Mezzmo data if enabled in setings
        autdialog = xbmcgui.Dialog()    
        kcmsg = "Confirm clearing the Mezzmo data in the Kodi database.  "
        kcmsg = kcmsg + "\nIt will be rebuilt with the sync process." 
        cselect = autdialog.yesno('Mezzmo Kodi Database Clear', kcmsg)
        if cselect == 0 :
            settings('kodiclean', 'false')             #  reset back to false
            return
        force = 1                                      #  Ok to clear database
    if force == 1:                                     #  clears Kodi DB Mezzmo data check for sync process

        syncurl = getSyncURL()                         #  Get Mezzmo sync server URL
        if syncurl == 'None':
            mgenlog ='Kodi database Mezzmo not cleared.  Missing valid Mezzmo sync server'
            #xbmc.log(mgenlog, xbmc.LOGINFO)
            mgenlogUpdate(mgenlog)            
            return
        db = openKodiDB()
        xbmc.log('Content delete URL: ' + syncurl, xbmc.LOGDEBUG)
        cleartype = settings('kodiclean')

        if cleartype != 'false':
            msgdialogprogress = ''
            msgdialogprogress = xbmcgui.DialogProgress()
            msgdialogprogress.create(translate(30459), translate(30460) + '0%')
            xbmc.sleep(500)
        serverport = '%' + getServerport(syncurl) + '%'     #  Get Mezzmo server port info

        db.execute('CREATE TRIGGER IF NOT EXISTS delete_episode_mezzmo AFTER DELETE ON episode FOR   \
        EACH ROW BEGIN DELETE FROM genre_link WHERE media_id=old.idEpisode AND media_type="tvshow";  \
        DELETE FROM actor_link WHERE media_id=old.idEpisode AND media_type="tvshow"; DELETE FROM     \
        genre_link WHERE media_id=old.idEpisode AND media_type="episode";END',)
        db.execute('CREATE INDEX IF NOT EXISTS ix_movie_file_mezzmo ON movie (c00)')
        db.execute('CREATE INDEX IF NOT EXISTS ix_episode_file_mezzmo ON episode (c00)')
        db.commit()

        try:  
            db.execute('DELETE FROM art WHERE url LIKE ?', (serverport,))
            db.execute('DELETE FROM actor WHERE art_urls LIKE ?', (serverport,))
            db.execute('DELETE FROM tvshow WHERE c17 LIKE ?', (serverport,))
            xbmc.log('Mezzmo serverport is: ' + serverport, xbmc.LOGDEBUG)
            if cleartype != 'false': 
                msgdialogprogress.update(25, translate(30460) + '25%')
                xbmc.sleep(1000) 
            curf = db.execute('SELECT idFile FROM files INNER JOIN path USING (idPath) WHERE          \
            strpath LIKE ?', (serverport,))             #  Get file and movie list
            idlist = curf.fetchall()
            for a in range(len(idlist)):                #  Delete Mezzmo file and Movie data
                xbmc.log('Clean rows found: ' + str(idlist[a][0]), xbmc.LOGDEBUG)
                db.execute('DELETE FROM files WHERE idFile=?',(idlist[a][0],))
                db.execute('DELETE FROM movie WHERE idFile=?',(idlist[a][0],))
                db.execute('DELETE FROM episode WHERE idFile=?',(idlist[a][0],))
                db.execute('DELETE FROM musicvideo WHERE idFile=?',(idlist[a][0],))
            db.execute('DELETE FROM path WHERE strPath LIKE ?', (serverport,))
            db.execute('DELETE FROM studio WHERE studio_id not in (SELECT studio_id FROM studio_link)') 
            mgenlog ='Kodi database Mezzmo data cleared.'
            #xbmc.log(mgenlog, xbmc.LOGINFO)
            mgenlogUpdate(mgenlog, 'yes')
            curf.close()
            db.commit()
            db.close()
            if cleartype != 'false': 
                msgdialogprogress.update(70, translate(30460) + '70%')
                xbmc.sleep(1000) 
        except db.OperationalError:        
            mgenlog = translate(30444)
            xbmc.log(mgenlog, xbmc.LOGINFO)
            mgenlogUpdate(mgenlog)
            name = xbmcaddon.Addon().getAddonInfo('name')
            icon = xbmcaddon.Addon().getAddonInfo("path") + '/resources/icon.png'
            xbmcgui.Dialog().notification(name, mgenlog, icon)
            db.close()
            return  

        try: 
            dbsync = openNosyncDB()                     #  clears nosync DB
            dbsync.execute('DELETE FROM nosyncVideo')
            dbsync.execute('DELETE FROM mTrailers')
            dbsync.execute('DELETE FROM mKeywords')
            dbsync.execute('DELETE FROM mCollection')
            dbsync.execute('DELETE FROM mCollection_link')
            dblimit = 10000
            dblimit2 = 10000
            dbsync.execute('delete from mperfStats where psDate not in (select psDate from  \
            mperfStats order by psDate desc limit ?)', (dblimit2,))
            dbsync.execute('delete from dupeTrack where dtDate not in (select dtDate from   \
            dupeTrack order by dtDate desc limit ?)', (dblimit2,))      
            dbsync.execute('delete from msyncLog where msDate not in (select msDate from    \
            msyncLog order by msDate desc limit ?)', (dblimit,))      
            dbsync.execute('delete from mgenLog where mgDate not in (select mgDate from     \
            mgenLog order by mgDate desc limit ?)', (dblimit,))
  
            dbsync.commit()
            dbsync.close()
            if cleartype != 'false': 
                msgdialogprogress.update(100, translate(30460) + '100%')
                xbmc.sleep(1000) 
                msgdialogprogress.close()

        except db.OperationalError:       
            dbsync.close()
            if msgdialogprogress: msgdialogprogress.close()  
            mgenlog = translate(30445)
            xbmc.log(mgenlog, xbmc.LOGINFO)
            name = xbmcaddon.Addon().getAddonInfo('name')
            icon = xbmcaddon.Addon().getAddonInfo("path") + '/resources/icon.png'
            xbmcgui.Dialog().notification(name, mgenlog, icon)

        if settings('kodiclean') == 'true':
            settings('kodiclean', 'false')    # reset back to false after clearing
            name = xbmcaddon.Addon().getAddonInfo('name')
            cleanmsg = translate(30389)
            icon = xbmcaddon.Addon().getAddonInfo("path") + '/resources/icon.png'
            xbmcgui.Dialog().notification(name, cleanmsg, icon)


def getSyncUrl():                                                # Get current sync content URLs

    try:
        svrfile = openNosyncDB()                                 # Open server database    
        curps = svrfile.execute('SELECT controlUrl FROM mServers WHERE mSync=?', ('Yes',))
        srvrtuple = curps.fetchone()                             # Get server from database
        if srvrtuple:
            syncurl = srvrtuple[0]
        else:
            syncurl = 'None'
        svrfile.close()
        return (syncurl)

    except Exception as e:
        printexception()
        msynclog = 'Mezzmo error getting sync URL.'
        #xbmc.log(msynclog, xbmc.LOGINFO)
        mezlogUpdate(msynclog, 'yes')
        return ('None')


def checkDBpath(itemurl, mtitle, mplaycount, db, mpath, mserver, mseason, mepisode, mseries, \
    mlplayed, mdateadded, mdupelog, mkoditv, mcategory, knative, musicvid): #  Check if path exists

    rtrimpos = itemurl.rfind('/')
    filecheck = itemurl[rtrimpos+1:]
    serverport = getServerport(itemurl)        #  Get Mezzmo server port info 
    xbmc.log('Mezzmo checkDbPath path check and file check: ' + str(mpath) + ' ' + str(filecheck), xbmc.LOGDEBUG)
    if mlplayed == '0':                        #  Set Mezzmo last played to null if 0
        mlplayed = ''

    if knative == 'true':                      #  Adjust paths for native mode
        rtrimpos = mpath.rfind('content/')       
        pathtrim = mpath[:rtrimpos+8]
        if mcategory == 'episode':
            mpath = pathtrim + 'tvshows/'
        elif mcategory == 'musicvideo' and musicvid == 'true':
            mpath = pathtrim + 'musicvideos/'
        else:
            mpath = pathtrim + 'movies/'      

    curpth = db.execute('SELECT idPath FROM path WHERE strpath=?',(mserver,))   # Check if server path exists in Kodi DB
    ppathtuple = curpth.fetchone()
    if not ppathtuple:                # add parent server path to Kodi DB if it doesn't exist
        db.execute('INSERT into path (strpath, strContent, noUpdate, exclude) values (?, ?, ?, ?)',   \
        (mserver, 'movies', '1', '0'))
        curpp = db.execute('SELECT idPath FROM path WHERE strPATH=?',(mserver,)) 
        ppathtuple = curpp.fetchone()
        ppathnumb = ppathtuple[0]
        mgenlog ='Mezzmo checkDBpath parent path added: ' + str(ppathnumb) + " " + mserver
        #xbmc.log(mgenlog, xbmc.LOGINFO)
        mgenlogUpdate(mgenlog)
        db.execute('UPDATE PATH SET strContent=?, idParentPath=? WHERE strPath LIKE ? AND idPath <> ?', \
        ('movies', ppathnumb, '%' + serverport + '%', ppathnumb))   # Update Child paths with parent information
        curpp.close() 
    ppathnumb = ppathtuple[0]         # Parent path number
    
    if ((int(mepisode) > 0 or int(mseason) > 0) and mkoditv == 'Season') or (mcategory == 'episode' and mkoditv == 'Category'):
        media = 'episode'
        contenttype = 'tvshows'
        episodes = 1
        if mdupelog == 'true' and mseries[:13] == "Unknown Album" : # Does TV episode have a blank series name
            mgenlog ='Mezzmo episode missing TV series name: ' + mtitle
            #xbmc.log(mgenlog, xbmc.LOGINFO)
            mgenlog = '###' + mtitle
            mgenlogUpdate(mgenlog)
            mgenlog ='Mezzmo episode missing TV series name: '
            mgenlogUpdate(mgenlog)   
        curf = db.execute('SELECT idFile, playcount, idPath, lastPlayed FROM files INNER JOIN episode   \
        USING (idFile) INNER JOIN path USING (idPath) INNER JOIN tvshow USING (idshow)                  \
        WHERE tvshow.c00=? and idParentPath=? and episode.c12=? and episode.c13=? and path.strContent=? \
        COLLATE NOCASE', (mseries, ppathnumb, mseason, mepisode, contenttype))    # Check if episode  
                                                                # exists in Kodi DB under parent path 
        filetuple = curf.fetchone()
        curf.close()
        xbmc.log('Checking path for : ' + mtitle, xbmc.LOGDEBUG)     # Path check debugging

    elif mcategory == 'musicvideo' and musicvid == 'true':
        media = 'musicvideo'
        contenttype = 'musicvideos'
        episodes = 2
        curf = db.execute('SELECT idFile, playcount, idPath, lastPlayed FROM files INNER JOIN musicvideo   \
        USING (idFile) INNER JOIN path USING (idPath) WHERE idParentPath=? and musicvideo.c00 = ?          \
        and musicvideo.c12=? and path.strContent=? COLLATE NOCASE', (ppathnumb, mtitle, mepisode,          \
        contenttype))    # Check if musicvideo exists in Kodi DB under parent path 
        filetuple = curf.fetchone()
        curf.close()
        xbmc.log('Checking path for : ' + mtitle, xbmc.LOGDEBUG)     # Path check debugging

    else:
        media = 'movie'
        contenttype = 'movies'
        episodes = 0
        curf = db.execute('SELECT idFile, playcount, idPath, lastPlayed FROM files INNER JOIN movie   \
        USING (idFile) INNER JOIN path USING (idPath) WHERE c00=? and idParentPath=? and              \
        path.strContent=? COLLATE NOCASE', (mtitle, ppathnumb, contenttype))      # Check if movie    
                                                             # exists in Kodi DB under parent path  
        filetuple = curf.fetchone()
        curf.close()
        #xbmc.log('Checking path for : ' + mtitle, xbmc.LOGINFO)     # Path check debugging

    if not filetuple:                 # if not exist insert into Kodi DB and return file key value
        if mcategory == 'musicvideo' and musicvid == 'true':
            catype = 'musicvideos'            
        elif mcategory == 'movie' or mcategory == 'video' or mcategory == 'musicvideo':
            catype = 'movies'
        else:
            catype = 'tvshows'

        curp = db.execute('SELECT idPath FROM path WHERE strPATH=? and strContent=?',                 \
        (mpath, catype,))          #  Check path table
        pathtuple = curp.fetchone()
        #xbmc.log('File not found movie: ' + mtitle), xbmc.LOGINFO)
        if not pathtuple:              # if path doesn't exist insert into Kodi DB
            if knative == 'false':  
                db.execute('INSERT into PATH (strpath, strContent, idParentPath) values (?, ?, ?)',   \
                (mpath, catype, ppathnumb))
            else:
                scraper = 'metadata.local'
                db.execute('INSERT into PATH (strpath, strContent, strScraper, noUpdate, exclude,     \
                idParentPath) values (?, ?, ?, ?, ?, ?)', (mpath, catype, scraper, '1', '0',          \
                ppathnumb))
            curp = db.execute('SELECT idPath FROM path WHERE strPATH=? and strContent=? ',            \
            (mpath, catype,)) 
            pathtuple = curp.fetchone()
        pathnumb = pathtuple[0]
        curp.close()

        if mcategory == 'episode' and mplaycount == 0:        # Adjust for Kodi expecting NULL vs. 0
            db.execute('INSERT into FILES (idPath, strFilename, lastPlayed, dateAdded) values          \
            (?, ?, ?, ? )', (str(pathnumb), filecheck, mlplayed, mdateadded,))
        else: 
            db.execute('INSERT into FILES (idPath, strFilename, playCount, lastPlayed, dateAdded) values  \
            (?, ?, ?, ?, ? )', (str(pathnumb), filecheck, mplaycount, mlplayed, mdateadded))
        cur = db.execute('SELECT idFile FROM files WHERE strFilename=?',(filecheck,)) 
        filetuple = cur.fetchone()
        filenumb = filetuple[0]
        cur.close()
        realfilenumb = filenumb      # Save real file number before resetting found flag
    else:                            # Return 0 if file already exists and check for play count change 
        filenumb = filetuple[0] 
        #xbmc.log('File found : ' + filecheck + ' ' + str(filenumb), xbmc.LOGDEBUG)
        fpcount = filetuple[1]
        flplayed = filetuple[3]       
        if fpcount != mplaycount or flplayed != mlplayed :    # If Mezzmo playcount or lastPlayed different
            if (mcategory != 'episode') or (mcategory == 'episode' and mplaycount > 0):
                db.execute('UPDATE files SET playCount=?, lastPlayed=?, dateAdded=? WHERE idFile=?',     \
                (mplaycount, mlplayed, mdateadded, filenumb,))    
        realfilenumb = filenumb      #  Save real file number before resetting found flag 
        pathnumb = filetuple[2]
        filenumb = 0  
    
    curpth.close()    
    return[filenumb, realfilenumb, ppathnumb, serverport, episodes, pathnumb] # Return file, path and info


def writeMovieToDb(fileId, mtitle, mplot, mtagline, mwriter, mdirector, myear, murate, mduration, mgenre, mtrailer, \
    mrating, micon, kchange, murl, db, mstudio, mstitle, mdupelog, mitemurl, mimdb_text, mkeywords, knative,        \
    movieset, imageSearchUrl, kdirector):  

    if fileId[0] > 0:                             # Insert movie if does not exist in Kodi DB
        #xbmc.log('The current movie is: ' + mtitle, xbmc.LOGINFO)
        mgenres = mgenre.replace(',' , ' /')      # Format genre for proper Kodi display
        dupm = db.execute('SELECT idMovie FROM movie WHERE idFile=? and c00=?', (fileId[0], mtitle))
        dupmtuple = dupm.fetchone() 
        if dupmtuple == None:                                        # Ensure movie doesn't exist
            db.execute('INSERT into MOVIE (idFile, c00, c01, c03, c06, c11, c15, premiered, c14, c19, c12, c18, c10,     \
            C23, userrating, C22) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (fileId[0], mtitle, mplot, mtagline, \
            mwriter, mduration, mdirector, myear, mgenres, mtrailer, mrating, mstudio, mstitle, fileId[5], murate, mitemurl)) #  Add movie
            cur = db.execute('SELECT idMovie FROM movie WHERE idFile=?',(str(fileId[0]),))  
            movietuple = cur.fetchone()
            movienumb = movietuple[0]                                # get new movie id 
            insertArt(movienumb, db, 'movie', murl, micon)           # Insert artwork for movie  
            insertGenre(movienumb, db, 'movie', mgenre)              # Insert genre for movie
            insertTags(movienumb, db, 'movie', mkeywords)            # Insert tags for movie
            insertKwords(mkeywords, 'movie', movienumb)              # Insert keywords for movie
            insertIMDB(movienumb, db, 'movie', mimdb_text)           # Insert IMDB for movie
            insertSets(movienumb, db, movieset, knative, murl, micon)  # Insert movie set for movie
            insertDirectors(movienumb, db, 'movie', mdirector, imageSearchUrl, kdirector)
            insertWriters(movienumb, db, 'movie', mwriter, imageSearchUrl, kdirector)
            insertStudios(movienumb, db, 'movie', mstudio, knative) 
            db.execute('INSERT into RATING (media_id, media_type, rating_type, rating) values   \
            (?, ?, ?, ?)', (movienumb,  'movie', 'imdb', murate,))
            curr = db.execute('SELECT rating_id FROM rating WHERE media_id=? and media_type=?', \
            (movienumb, 'movie',))
            ratetuple = curr.fetchone() 
            ratenumb = ratetuple[0]
            db.execute('UPDATE movie SET c05=? WHERE idMovie=?', (ratenumb, movienumb))
            cur.close()
            curr.close()
        else:
            movienumb = dupmtuple[0]                                 # If dupe, return existing movie id
        dupm.close()
    elif kchange == 'true':                                          # Update metadata if changes
        curm = db.execute('SELECT idMovie, c01, c03, c06, c11, c15, c14, c12, premiered, c05, \
        c18, c10 FROM movie INNER JOIN files USING (idfile) INNER JOIN path USING (idpath)    \
        WHERE idFile=? COLLATE NOCASE', (int(fileId[1]),))  
        movietuple = curm.fetchone()
        movienumb = movietuple[0]
        kplot = movietuple[1]
        ktagline = movietuple[2]
        kwriter = movietuple[3]     
        kduration = movietuple[4]
        kdirector = movietuple[5]
        kgenre = movietuple[6]
        krating = movietuple[7]
        kyear = movietuple[8]
        krate = movietuple[9]
        kstudio = movietuple[10]
        kstitle = movietuple[11]
        kgenres = kgenre.replace(' /' , ',')                          #  Format genre for proper Kodi display
        #xbmc.log('Checking movie for changes : ' + mtitle, xbmc.LOGINFO)        
        if kplot != mplot or ktagline != mtagline or kwriter != mwriter or kdirector != mdirector   \
        or kyear != myear or krating != mrating or kgenres != mgenre or int(kduration) != mduration \
        or kstudio != mstudio or kstitle != mstitle:                  # Update movie info if changed
            mgenres = mgenre.replace(',' , ' /')                      #  Format genre for proper Kodi display
            db.execute('UPDATE MOVIE SET c01=?, c03=?, c06=?, c11=?, c15=?, premiered=?, c14=?, c19=?, c12=?,     \
            c18=?, c10=?, c23=?, userrating=?, c22=? WHERE idMovie=?', (mplot,  mtagline, mwriter, mduration, mdirector, \
            myear, mgenres, mtrailer, mrating, mstudio, mstitle, fileId[5], murate, mitemurl, movienumb)) #  Update movie information
            db.execute('UPDATE rating SET rating=? WHERE rating_id=?', (murate, krate))
            db.execute('DELETE FROM art WHERE media_id=? and media_type=?',(str(movienumb), 'movie'))
            insertArt(movienumb, db, 'movie', murl, micon)            # Update artwork for movie
            db.execute('DELETE FROM genre_link WHERE media_id=? and media_type=?',(str(movienumb), 'movie'))
            insertGenre(movienumb, db, 'movie', mgenre)               # Insert genre for movie
            insertTags(movienumb, db, 'movie', mkeywords)             # Insert tags for movie
            insertKwords(mkeywords, 'movie', movienumb)               # Insert keywords for movie 
            insertIMDB(movienumb, db, 'movie', mimdb_text)            # Insert IMDB for movie
            insertSets(movienumb, db, movieset, knative, murl, micon)  # Insert movie set for movie
            insertDirectors(movienumb, db, 'movie', mdirector, imageSearchUrl, kdirector)
            insertWriters(movienumb, db, 'movie', mwriter, imageSearchUrl, kdirector)
            insertStudios(movienumb, db, 'movie', mstudio, knative)
            if mdupelog == 'false':
                mgenlog ='There was a Mezzmo metadata change detected: ' + mtitle
                #xbmc.log(mgenlog, xbmc.LOGINFO)
                mgenlog = '###' + mtitle
                mgenlogUpdate(mgenlog)
                mgenlog ='There was a Mezzmo metadata change detected: '
                mgenlogUpdate(mgenlog)
            else:
                checkDupes(movienumb, '0', mtitle)                    # Add dupes to database
            movienumb = 999999                                        # Trigger actor update
        curm.close()
    else:
        movienumb = 0                                                 # disable change checking

    return(movienumb)


def writeMusicVToDb(fileId, mtitle, mplot, mtagline, mwriter, mdirector, myear, murate, mduration, mgenre, mtrailer,   \
    mrating, micon, kchange, murl, db, mstudio, mstitle, mdupelog, mitemurl, mimdb_text, mkeywords, knative, movieset, \
    mepisode, martist, imageSearchUrl, kdirector):  

    if fileId[0] > 0:                             # Insert movie if does not exist in Kodi DB
        #xbmc.log('The current musicvideo is: ' + mtitle, xbmc.LOGINFO)
        mgenres = mgenre.replace(',' , ' /')      # Format genre for proper Kodi display
        dupm = db.execute('SELECT idMVideo FROM musicvideo WHERE idFile=? and c00=?', (fileId[0], mtitle))
        dupmtuple = dupm.fetchone() 
        if dupmtuple == None:                                        # Ensure movie doesn't exist
            db.execute('INSERT into MUSICVIDEO (idFile, c00, c01, c04, c05, c06, premiered, c08, c09, c10, c11, c12, \
            C13, userrating, C14) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (fileId[0], mtitle, murl,   \
            mduration, mdirector, mstudio, myear, mplot, movieset, martist, mgenres, mepisode, mitemurl, murate,     \
            fileId[5]))             #  Add musicvideo
            cur = db.execute('SELECT idMVideo FROM musicvideo WHERE idFile=?',(str(fileId[0]),))  
            movietuple = cur.fetchone()
            movienumb = movietuple[0]                                # get new movie id 
            insertArt(movienumb, db, 'musicvideo', murl, micon)      # Insert artwork for musicvideo 
            insertGenre(movienumb, db, 'musicvideo', mgenre)         # Insert genre for musicvideo 
            insertTags(movienumb, db, 'musicvideo', mkeywords)       # Insert tags for musicvideo
            insertKwords(mkeywords, 'musicvideo', movienumb)         # Insert keywords for musicvideo
            insertDirectors(movienumb, db, 'musicvideo', mdirector, imageSearchUrl, kdirector)
            insertStudios(movienumb, db, 'musicvideo', mstudio, knative)    
            cur.close()
        else:
            movienumb = dupmtuple[0]                                  # If dupe, return existing movie id
        dupm.close()
    elif kchange == 'true':                                           #  Update metadata if changes
        curm = db.execute('SELECT idMVideo, c08, c04, c05, c11, premiered, c06, c10    \
        FROM musicvideo INNER JOIN files USING (idfile) INNER JOIN path USING (idpath) \
        WHERE idFile=? COLLATE NOCASE', (int(fileId[1]),))  
        movietuple = curm.fetchone()
        movienumb = movietuple[0]
        kplot = movietuple[1]
        kduration = movietuple[2]
        kdirector = movietuple[3]
        kgenre = movietuple[4]
        kyear = movietuple[5]
        kstudio = movietuple[6]
        kartist = movietuple[7]
        kgenres = kgenre.replace(' /' , ',')                          #  Format genre for proper Kodi display
        #xbmc.log('Checking musicvideo for changes : ' + mtitle, xbmc.LOGINFO)        
        if kplot != mplot or kdirector != mdirector or kyear != myear or  kgenres != mgenre or int(kduration)  \
        != mduration or kstudio != mstudio or kartist != martist:     #  Update movie info if changed
            mgenres = mgenre.replace(',' , ' /')                      #  Format genre for proper Kodi display
            db.execute('UPDATE MUSICVIDEO SET c01=?, c04=?, c05=?, c06=?, premiered=?, c08=?, c09=?, c10=?, c11=?,    \
            c12=?, c13=?, userrating=?, c14=? WHERE idMVideo=?', (murl, mduration, mdirector, mstudio, myear, mplot,  \
            movieset, martist, mgenres, mepisode, mitemurl, murate, fileId[5], movienumb)) #  Update musicvideo information
            #db.execute('UPDATE rating SET rating=? WHERE rating_id=?', (murate, krate))
            db.execute('DELETE FROM art WHERE media_id=? and media_type=?',(str(movienumb), 'musicvideo'))
            insertArt(movienumb, db, 'musicvideo', murl, micon)       # Update artwork for musicvideo
            db.execute('DELETE FROM genre_link WHERE media_id=? and media_type=?',(str(movienumb), 'musicvideo'))
            insertGenre(movienumb, db, 'musicvideo', mgenre)          # Insert genre for musicvideo 
            insertTags(movienumb, db, 'musicvideo', mkeywords, movienumb) # Insert tags for musicvideo
            insertKwords(mkeywords, 'musicvideo', movienumb)          # Insert keywords for musicvideo 
            insertDirectors(movienumb, db, 'musicvideo', mdirector, imageSearchUrl, kdirector)
            insertStudios(movienumb, db, 'musicvideo', mstudio, kdirector)    
            if mdupelog == 'false':
                mgenlog ='There was a Mezzmo metadata change detected: ' + mtitle
                #xbmc.log(mgenlog, xbmc.LOGINFO)
                mgenlog = '###' + mtitle
                mgenlogUpdate(mgenlog)
                mgenlog ='There was a Mezzmo metadata change detected: '
                mgenlogUpdate(mgenlog)
            else:
                checkDupes(movienumb, '0', mtitle)                    # Add dupes to database
            movienumb = 999999                                        # Trigger actor update
        curm.close()
    else:
        movienumb = 0                                                 # disable change checking

    return(movienumb)


def writeEpisodeToDb(fileId, mtitle, mplot, mtagline, mwriter, mdirector, maired, murate, mduration, mgenre, \
    mtrailer, mrating, micon, kchange, murl, db, mstudio, mstitle, mseason, mepisode, shownumb, mdupelog,    \
    mitemurl, mimdb_text, mkeywords, imageSearchUrl, kdirector): 

    #xbmc.log('Mezzmo fileId is: ' + str(fileId), xbmc.LOGINFO)
    if fileId[0] > 0:                                                #  Insert movie if does not exist in Kodi DB
        #xbmc.log('The current episode is: ' + mtitle, xbmc.LOGINFO)
        mgenres = mgenre.replace(',' , ' /')                         #  Format genre for proper Kodi display
        dupe = db.execute('SELECT idEpisode FROM episode WHERE idFile=? and c00=?', (fileId[0], mtitle))
        dupetuple = dupe.fetchone() 
        if dupetuple == None:                                        # Ensure episode doesn't exist
            db.execute('INSERT into EPISODE (idFile, c00, c01, c09, c10, c04, c12, c13, c05, idshow, c19, userrating, c18) \
            values (?, ?, ?, ?, ?, ?, ? ,? ,? ,?, ?, ?, ?)', (fileId[0], mtitle, mplot, mduration, mdirector, mwriter,   \
            mseason, mepisode, maired[:10], shownumb, fileId[5], murate, mitemurl))  #  Add episode information
            cur = db.execute('SELECT idEpisode FROM episode WHERE idFile=?',(str(fileId[0]),))  
            episodetuple = cur.fetchone()
            movienumb = episodetuple[0]                              # get new movie id  
            insertArt(movienumb, db, 'episode', murl, micon)         # Insert artwork for episode
            insertGenre(movienumb, db, 'episode', mgenre)            # Insert genre for episode 
            insertGenre(shownumb, db, 'tvshow', mgenre)              # Insert genre for episode
            insertTags(shownumb, db, 'tvshow', mkeywords)            # Insert tags for episode
            insertKwords(mkeywords, 'episode', movienumb)            # Insert keywords for episode   
            insertIMDB(movienumb, db, 'episode', mimdb_text)         # Insert IMDB for episode
            insertDirectors(movienumb, db, 'episode', mdirector, imageSearchUrl, kdirector)
            insertWriters(movienumb, db, 'episode', mwriter, imageSearchUrl, kdirector)        
            db.execute('INSERT into RATING (media_id, media_type, rating_type, rating) values   \
            (?, ?, ?, ?)', (movienumb,  'episode', 'imdb', murate,))
            curr = db.execute('SELECT rating_id FROM rating WHERE media_id=? and media_type=?', \
            (movienumb, 'episode',))
            ratetuple = curr.fetchone() 
            ratenumb = ratetuple[0]
            seasonId = checkSeason(db, shownumb, mseason, murl, micon)
            db.execute('UPDATE episode SET c03=?, idSeason=? WHERE idEpisode=?', (ratenumb, seasonId, movienumb,))
            cur.close()
            curr.close()
        else:
            movienumb = dupetuple[0]                                  # If dupe, return existing episode id
        dupe.close()
    else:
        curm = db.execute('SELECT idEpisode, c01, c09, c10, c04, c12, c13, c05, idShow, c03 \
        FROM episode INNER JOIN files USING (idfile) INNER JOIN path USING (idpath)         \
        WHERE idFile=? COLLATE NOCASE', (int(fileId[1]),))  
        episodetuple = curm.fetchone()
        movienumb = episodetuple[0]
        kplot = episodetuple[1]
        kduration = episodetuple[2]
        kdirector = episodetuple[3]
        kwriter = episodetuple[4]     
        kseason = episodetuple[5]
        kepisode = episodetuple[6]
        kaired = episodetuple[7]
        kshow = episodetuple[8]
        krate = episodetuple[9]
        #xbmc.log('Checking episode for changes : ' + mtitle, xbmc.LOGINFO)     
        if kplot != mplot or int(kduration) != mduration or kdirector != mdirector or kwriter != mwriter    \
        or kseason != mseason or kepisode != mepisode or kaired != maired[:10] or kshow != shownumb: 
            db.execute('UPDATE EPISODE SET c01=?, c09=?, c10=?, c04=?, c12=?, c13=?, c05=?, idShow=?, C19=?,\
            userrating=?, c18=? WHERE idEpisode=?', (mplot, mduration, mdirector, mwriter, mseason, mepisode,      \
            maired[:10], shownumb, fileId[5], murate, mitemurl, movienumb))     #  Update Episode information
            db.execute('UPDATE rating SET rating=? WHERE rating_id=?', (murate, krate))
            seasonId = checkSeason(db, shownumb, mseason, murl, micon)
            db.execute('UPDATE episode SET idSeason=? WHERE idEpisode=?', (seasonId, movienumb,))
            db.execute('DELETE FROM art WHERE media_id=? and media_type=?',(str(movienumb), 'episode'))
            insertArt(movienumb, db, 'episode', murl, micon)          # Insert artwork for episode
            db.execute('DELETE FROM genre_link WHERE media_id=? and media_type=?',(str(movienumb), 'episode'))
            insertGenre(movienumb, db, 'episode', mgenre)              # Insert genre for episode
            db.execute('DELETE FROM genre_link WHERE media_id=? and media_type=?',(str(movienumb), 'tvshow'))
            insertGenre(shownumb, db, 'tvshow', mgenre)                # Insert genre for episode
            insertTags(shownumb, db, 'tvshow', mkeywords)              # Insert tags for episode
            insertKwords(mkeywords, 'episode', movienumb)              # Insert keywords for episode 
            insertIMDB(movienumb, db, 'episode', mimdb_text)           # Insert IMDB for episode
            insertDirectors(movienumb, db, 'episode', mdirector, imageSearchUrl, kdirector)
            insertWriters(movienumb, db, 'episode', mwriter, imageSearchUrl, kdirector) 
            if mdupelog == 'false':
                mgenlog ='There was a Mezzmo metadata change detected: ' + mtitle
                #xbmc.log(mgenlog, xbmc.LOGINFO)
                mgenlog = '###' + mtitle
                mgenlogUpdate(mgenlog)
                mgenlog ='There was a Mezzmo metadata change detected: '
                mgenlogUpdate(mgenlog) 
            else:
                checkDupes(movienumb, '0', mtitle)                    #  Add dupes to database
            movienumb = 999999                                        # Trigger actor update            
        movienumb = 0                                                 # disable change checking
        curm.close()

    return(movienumb)


def writeActorsToDb(actors, movieId, imageSearchUrl, mtitle, db, fileId, mnativeact, mshowId):
    actorlist = actors.replace(', Jr.' , ' Jr.').replace(', Sr.' , ' Sr.').split(', ')    

    if fileId[4] == 0:
       media_type = 'movie'
    elif fileId[4] == 1:
       media_type = 'episode'
    elif fileId[4] == 2:
       media_type = 'musicvideo'
    #xbmc.log('Mezzmo writeActorsToDb: ' + str(fileId) + ' ' + str(movieId), xbmc.LOGINFO)
    #xbmc.log('Mezzmo writeActorsToDb movie and movieID are: ' + str(movieId) + ' ' + mtitle, xbmc.LOGDEBUG)
    if movieId == 999999:                           # Actor info needs updated
        movieId = fileId[1]
        db.execute('DELETE FROM actor_link WHERE media_id=? and media_type=?',(str(movieId), media_type))
        if media_type == 'episode' and mnativeact == 'true':
            db.execute('DELETE FROM actor_link WHERE media_id=? and media_type=?',(str(mshowId), 'tvshow'))
    if movieId != 0:
        ordernum = 0
        for actor in actorlist:     
            f = { 'imagesearch' : actor}
            searchUrl = imageSearchUrl + "?" + urllib.parse.urlencode(f)
            #xbmc.log('The current actor is: ' + str(actor), xbmc.LOGINFO)      # actor insertion debugging
            #xbmc.log('The movieId is: ' + str(movieId), xbmc.LOGINFO)          # actor insertion debugging  
            cur = db.execute('SELECT actor_id FROM actor WHERE name=?',(actor,))   
            actortuple = cur.fetchone()                                         #  Get actor id from actor table
            cur.close()
            if not actortuple:              #  If actor not in actor table insert and fetch new actor ID
                db.execute('INSERT into ACTOR (name, art_urls) values (?, ?)', (actor, searchUrl,))
                cur = db.execute('SELECT actor_id FROM actor WHERE name=?',(actor,)) 
                actortuple = cur.fetchone()  #  Get actor id from actor table
                cur.close()
            if actortuple:                   #  Insert actor to movie link in actor link table
                actornumb = actortuple[0]
                ordernum += 1                #  Increment cast order
                db.execute('INSERT OR REPLACE into ACTOR_LINK (actor_id, media_id, media_type, cast_order) values  \
                (?, ?, ?, ?)', (actornumb, movieId, media_type, ordernum,))
                if media_type == 'episode' and mnativeact == 'true':
                    db.execute('INSERT OR REPLACE into ACTOR_LINK (actor_id, media_id, media_type, role, cast_order) \
                    values (?, ?, ?, ?, ?)', (actornumb, mshowId, 'tvshow', ' ', ordernum,)) 
                #xbmc.log('The current actor number is: ' + str(actornumb) + "  " + str(movieId), xbmc.LOGINFO)  


def writeMovieStreams(fileId, mvcodec, maspect, mvheight, mvwidth, macodec, mchannels, mlang, mduration, mtitle,  \
    kchange, itemurl, micon, murl, db, mpath, mdupelog, knative):

    rtrimpos = itemurl.rfind('/')       # Check for container / path change
    filecheck = itemurl[rtrimpos+1:]

    if fileId[4] == 0:
        media_type = 'movie'
        mcategory = 'movies'
    elif fileId[4] == 1:
        media_type = 'episode'
        mcategory = 'tvshows'
    elif fileId[4] == 2:
        media_type = 'musicvideo'
        mcategory = 'musicvideos'

    if knative == 'true' and media_type == 'movie':
        rtrimpos = mpath.rfind('content/')       
        pathtrim = mpath[:rtrimpos+8]
        mpath = pathtrim + 'movies/'
    elif knative == 'true' and media_type == 'episode':
        rtrimpos = mpath.rfind('content/')       
        pathtrim = mpath[:rtrimpos+8]
        mpath = pathtrim + 'tvshows/'
    elif knative == 'true' and media_type == 'musicvideo':
        rtrimpos = mpath.rfind('content/')       
        pathtrim = mpath[:rtrimpos+8]
        mpath = pathtrim + 'musicvideos/'

    if fileId[0] > 0:                   #  Insert stream details if file does not exist in Kodi DB
        insertStreams(fileId[0], db, mvcodec, maspect, mvwidth, mvheight, mduration, macodec, mchannels, mlang)
    elif kchange == 'true':             #  Update stream details, filename, artwork and movie duration if changes
        if fileId[4] == 0:
            scur = db.execute('SELECT DISTINCT iVideoDuration, strVideoCodec, strAudioCodec, idFile, strPath,     \
            idMovie, url FROM STREAMDETAILS INNER JOIN movie USING (idFile) INNER JOIN files USING (idfile) INNER \
            JOIN path USING (idpath) INNER JOIN art ON movie.idMovie=art.media_id WHERE idFile=? and media_type=? \
            ORDER BY strAudioCodec', (int(fileId[1]), media_type))
        elif  fileId[4] == 1:
            scur = db.execute('SELECT DISTINCT iVideoDuration, strVideoCodec, strAudioCodec, idFile, strPath,     \
            idEpisode, url FROM STREAMDETAILS INNER JOIN episode USING (idFile) INNER JOIN files USING (idfile)   \
            INNER JOIN path USING (idpath) INNER JOIN art ON episode.idEpisode=art.media_id WHERE idFile=? and    \
            media_type=? ORDER BY strAudioCodec', (int(fileId[1]), media_type))
        elif  fileId[4] == 2:
            scur = db.execute('SELECT DISTINCT iVideoDuration, strVideoCodec, strAudioCodec, idFile, strPath,     \
            idMVideo, url FROM STREAMDETAILS INNER JOIN musicvideo USING (idFile) INNER JOIN files USING (idfile) \
            INNER JOIN path USING (idpath) INNER JOIN art ON musicvideo.idMVideo=art.media_id WHERE idFile=? and  \
            media_type=? ORDER BY strAudioCodec', (int(fileId[1]), media_type))
        idflist = scur.fetchall()
        rows = len(idflist)     
        if rows >= 3:                              # Ensure all data exsts
            sdur = idflist[0][0]
            svcodec = idflist[0][1]		   # Get video codec from Kodi DB
            sacodec = idflist[2][2]		   # Get audio codec from Kodi DB
            filenumb = idflist[2][3]
            kpath = idflist[2][4]
            movienumb = idflist[2][5]
            kicon = idflist[1][6]                  # Get Kodi DB thumbnail URL 
            pathmatch = urlMatch(mpath, kpath)     # Check if paths match
            iconmatch = urlMatch(micon, kicon)     # Check if icons match 
            if (sdur != mduration or svcodec != mvcodec or sacodec != macodec or pathmatch is False or \
                iconmatch is False) and rows >= 3:
                if mdupelog == 'false':
                    mgenlog ='There was a Mezzmo streamdetails or artwork change detected: ' +                   \
                    mtitle
                    #xbmc.log(mgenlog, xbmc.LOGINFO)
                    mgenlog ='Mezzmo streamdetails artwork rowcount = : ' +  str(rows)
                    #xbmc.log(mgenlog, xbmc.LOGINFO)
                    mgenlog ='###Mezzmo streamdetails artwork rowcount = : ' +  str(rows)
                    mgenlogUpdate(mgenlog)
                    mgenlog = '###' + mtitle
                    mgenlogUpdate(mgenlog)
                    mgenlog ='There was a Mezzmo streamdetails or artwork change detected: '
                    mgenlogUpdate(mgenlog)   
                xbmc.log('Mezzmo streamdetails sdur and mduration are: ' + str(sdur) + ' ' + str(mduration), xbmc.LOGDEBUG)
                xbmc.log('Mezzmo streamdetails svcodec and mvcodec are: ' + str(svcodec) + ' ' + str(mvcodec), xbmc.LOGDEBUG)
                xbmc.log('Mezzmo streamdetails sacodec and macodec are: ' + str(sacodec) + ' ' + str(macodec), xbmc.LOGDEBUG)
                xbmc.log('Mezzmo streamdetails kpath and mpath are: ' + str(kpath) + ' ' + str(mpath), xbmc.LOGDEBUG)
                xbmc.log('Mezzmo streamdetails kicon micon are: ' + str(kicon) + ' ' + str(micon), xbmc.LOGDEBUG)
                delete_query = 'DELETE FROM streamdetails WHERE idFile = ' + str(filenumb)
                db.execute(delete_query)          #  Delete old stream info
                insertStreams(filenumb, db, mvcodec, maspect, mvwidth, mvheight, mduration, macodec, mchannels, mlang)
                curp = db.execute('SELECT idPath FROM path WHERE strPATH=? and strContent=?',(mpath, mcategory,))  #  Check path table
                pathtuple = curp.fetchone()
                if not pathtuple:                # if path doesn't exist insert into Kodi DB and return path key value
                    if knative == 'false':  
                        db.execute('INSERT into PATH (strpath, strContent, idParentPath) values (?, ?, ?)',     \
                        (mpath, mcategory, int(fileId[2])))
                    else:
                        #scraper = 'metadata.themoviedb.org.python'
                        scraper = 'metadata.local'
                        db.execute('INSERT into PATH (strpath, strContent, strScraper, noUpdate, exclude,       \
                        idParentPath) values (?, ?, ?, ?, ?, ?)', (mpath, mcategory, scraper, '1', '0',         \
                        int(fileId[2])))
                    curp = db.execute('SELECT idPath FROM path WHERE strPATH=?',(mpath,)) 
                    pathtuple = curp.fetchone()
                pathnumb = pathtuple[0]
                db.execute('UPDATE files SET idPath=?, strFilename=? WHERE idFile=?', (pathnumb, filecheck, filenumb))
                db.execute('UPDATE movie SET c23=? WHERE idFile=?', (pathnumb, filenumb))
                db.execute('UPDATE episode SET c19=? WHERE idFile=?', (pathnumb, filenumb))
                db.execute('UPDATE musicvideo SET c14=? WHERE idFile=?', (pathnumb, filenumb))
                db.execute('DELETE FROM art WHERE media_id=? and media_type=?',(str(movienumb), media_type))
                insertArt(movienumb, db, media_type, murl, micon)     # Insert artwork for episode / movie
                curp.close()
        else:                                   # Repair missing streamdetails data
            db.execute('DELETE FROM streamdetails WHERE idFile=?',(fileId[1],))
            insertStreams(fileId[1], db, mvcodec, maspect, mvwidth, mvheight, mduration, macodec, mchannels, mlang)
            mgenlog ='The Mezzmo incomplete streamdetails repaired for : ' + mtitle
            #xbmc.log(mgenlog, xbmc.LOGINFO)
            mgenlog = '###' + mtitle
            mgenlogUpdate(mgenlog)
            mgenlog ='The Mezzmo incomplete streamdetails repaired for : '
            mgenlogUpdate(mgenlog)   
        scur.close()

def insertStreams(filenumb, db, mvcodec, maspect, mvwidth, mvheight, mduration, macodec, mchannels, mlang):

    db.execute('INSERT into STREAMDETAILS (idFile, iStreamType, strVideoCodec, fVideoAspect, iVideoWidth,        \
    iVideoHeight, iVideoDuration) values (?, ?, ?, ?, ? ,? ,?)', (filenumb, '0', mvcodec, maspect, mvwidth,      \
    mvheight, mduration))
    db.execute('INSERT into STREAMDETAILS (idFile, iStreamType, strAudioCodec, iAudioChannels, strAudioLanguage) \
    values (?, ?, ? ,?, ?)', (filenumb, '1', macodec, mchannels, mlang))
    db.execute('UPDATE movie SET c11=? WHERE idFile=?', (mduration, filenumb,))


def insertArt(movienumb, db, media_type, murl, micon):

    db.execute('INSERT into ART (media_id, media_type, type, url) values (?, ?, ?, ?)', \
    (movienumb, media_type, 'poster', micon))
    db.execute('INSERT into ART (media_id, media_type, type, url) values (?, ?, ?, ?)', \
    (movienumb, media_type, 'fanart', murl))
    db.execute('INSERT into ART (media_id, media_type, type, url) values (?, ?, ?, ?)', \
    (movienumb, media_type, 'thumb', micon))
    db.execute('INSERT into ART (media_id, media_type, type, url) values (?, ?, ?, ?)', \
    (movienumb, media_type, 'icon', micon))


def insertIMDB(movienumb, db, media_type, mimdb_text):   

    db.execute('DELETE FROM uniqueid WHERE media_id=? and media_type=?',(str(movienumb), media_type))  
    if mimdb_text == None or len(mimdb_text) < 6:                                   # Ensure valid IMDB data
        return  
    if media_type == 'movie':
        db.execute('INSERT into UNIQUEID (media_id, media_type, value, type) values (?, ?, ? ,?)', \
        (movienumb, media_type, mimdb_text, 'imdb'))
        curi = db.execute('SELECT uniqueid_id FROM uniqueid WHERE media_id=? and media_type=?',    \
        (movienumb, media_type,))   
        imdbtuple = curi.fetchone()                                                 # Get IMDB uniqueid
        curi.close()
        if imdbtuple:
            db.execute('UPDATE movie SET c09=? WHERE idMovie=?', (imdbtuple[0], movienumb,))            
    if media_type == 'episode':
        db.execute('INSERT into UNIQUEID (media_id, media_type, value, type) values (?, ?, ? ,?)', \
        (movienumb, media_type, mimdb_text, 'imdb'))
        curi = db.execute('SELECT uniqueid_id FROM uniqueid WHERE media_id=? and media_type=?',    \
        (movienumb, media_type,))   
        imdbtuple = curi.fetchone()                                                 # Get IMDB uniqueid
        curi.close()
        if imdbtuple:
            db.execute('UPDATE episode SET c20=? WHERE idEpisode=?', (imdbtuple[0], movienumb,)) 


def insertSets(movienumb, db, setname, knative, murl, micon):

    db.execute('UPDATE movie SET idSet=? WHERE idMovie=?', (None, movienumb,))
    if settings('knative') == 'false':                                              # Native mode disabled
        return  
    if setname == None or len(setname) == 0 or 'Unknown' in setname:
        return    

    msetname = setname.strip()

    curs = db.execute('SELECT idSet FROM sets WHERE strSet=?',(msetname,))   
    sagtuple = curs.fetchone()                                                      # Get set id from set table
    curs.close()    

    if not sagtuple:                     #  If set not in set table insert and fetch new set ID
        db.execute('INSERT into SETS (strSet) values (?)', (msetname,))
        cur = db.execute('SELECT idSet FROM sets WHERE strSet=?',(msetname,))   
        sagtuple = cur.fetchone()        #  Get set id from set table
        cur.close()

    if sagtuple:                         #  Insert set to movie table
        setnumb = sagtuple[0] 
        db.execute('UPDATE movie SET idSet=? WHERE idMovie=?', (setnumb, movienumb,))
        #xbmc.log('The current set number is: ' + str(setnumb) + "  " + str(msetname), xbmc.LOGINFO)
        cura = db.execute('SELECT art_id FROM art WHERE media_id=? and media_type=?',(setnumb, 'set',))
        artuple = cura.fetchone()
        cura.close()        
        if not artuple:
            db.execute('INSERT into ART (media_id, media_type, type, url) values (?, ?, ?, ?)', \
            (setnumb, 'set', 'poster', micon))
            db.execute('INSERT into ART (media_id, media_type, type, url) values (?, ?, ?, ?)', \
            (setnumb, 'set', 'fanart', murl)) 


def insertTags(movienumb, db, media_type, keywords):

    if media_type != 'tvshow':
        db.execute('DELETE FROM tag_link WHERE media_id=? and media_type=?',(str(movienumb), media_type))
    if keywords == None or len(keywords) == 0:
        return
    if settings('nativetag') == 'false':                                             # Tag syncing not enabled
        return    
    taglist = keywords.split(',')                                                    # Convert keywords to list
    xbmc.log('Mezzmo taglist is: ' + str(taglist), xbmc.LOGDEBUG)                    # tags insertion debugging
    for tag in taglist:     
        xbmc.log('Mezzmo current tag is: ' + str(tag), xbmc.LOGDEBUG)
        mtag = tag.strip()
        curt = db.execute('SELECT tag_id FROM tag WHERE name=?',(mtag,))   
        tagtuple = curt.fetchone()                                                   # Get tag id from tag table
        curt.close()

        if "nosync" not in mtag.lower() and '###' not in mtag.lower():        # Skip nosync tags and collections
            if not tagtuple:                     #  If tag not in tag table insert and fetch new tag ID
                db.execute('INSERT into TAG (name) values (?)', (mtag,))
                cur = db.execute('SELECT tag_id FROM tag WHERE name=?',(mtag,))   
                tagtuple = cur.fetchone()        #  Get tag id from tag table
                cur.close()
            if tagtuple:                         #  Insert tag to media link in tag link table
                tagnumb = tagtuple[0] 
                db.execute('INSERT OR REPLACE into TAG_LINK (tag_id, media_id, media_type) values \
                (?, ?, ?)', (tagnumb, movienumb, media_type,))
                #xbmc.log('The current tag number is: ' + str(tagnumb) + "  " + str(movieId), xbmc.LOGINFO)


def insertDirectors(movienumb, db, mtype, directors, imageSearchUrl, kdirector):

    try:
        if kdirector == 'false':
            return
        db.execute('DELETE FROM director_link WHERE media_id=? and media_type=?',(movienumb, mtype,))
        if directors == None or len(directors) == 0:
            return
        directorlist = directors.replace(', Jr.' , ' Jr.').replace(', Sr.' , ' Sr.').split(', ')  # Convert to list

        xbmc.log('Mezzmo directorlist is: ' + str(directorlist), xbmc.LOGDEBUG)
        for director in directorlist:
            f = { 'imagesearch' : director }
            searchUrl = imageSearchUrl + "?" + urllib.parse.urlencode(f)     
            xbmc.log('Mezzmo current director is: ' + str(director), xbmc.LOGDEBUG)  # director insertion debugging
            mdirector = director.strip()
            curg = db.execute('SELECT actor_id FROM actor WHERE name=?',(mdirector,))   
            directortuple = curg.fetchone()                                          # Get director id from actor table
            curg.close()

            if not directortuple:                   #  If director not in actor table insert and fetch new actor ID
                db.execute('INSERT into actor (name, art_urls) values (?, ?)', (mdirector, searchUrl,))
                cur = db.execute('SELECT actor_id FROM actor WHERE name=?',(mdirector,))   
                directortuple = cur.fetchone()      #  Get director id from actor table
                cur.close()
            if directortuple:                       #  Insert director to movie link in director link table
                directornumb = directortuple[0] 
                db.execute('INSERT or REPLACE into DIRECTOR_LINK (actor_id, media_id, media_type) values \
                (?, ?, ?)', (directornumb, movienumb, mtype,))
                #xbmc.log('The current director number is: ' + str(directornumb) + "  " + str(movienumb), xbmc.LOGINFO)

    except Exception as e:
        printexception()
        msynclog ='Mezzmo problem inserting directors for: ' + str(directors) + ' ' + str(movienumb)
        xbmc.log(msynclog, xbmc.LOGINFO)



def insertWriters(movienumb, db, mtype, writers, imageSearchUrl, kdirector):

    try:
        if kdirector == 'false':
            return
        db.execute('DELETE FROM writer_link WHERE media_id=? and media_type=?',(movienumb, mtype,))
        if writers == None or len(writers) == 0:
            return
        writerlist = writers.replace(', Jr.' , ' Jr.').replace(', Sr.' , ' Sr.').split(', ')  # Convert to list

        xbmc.log('Mezzmo writerlist is: ' + str(writerlist), xbmc.LOGDEBUG)
        for writer in writerlist:
            f = { 'imagesearch' : writer }
            searchUrl = imageSearchUrl + "?" + urllib.parse.urlencode(f)     
            xbmc.log('Mezzmo current writer is: ' + str(writer), xbmc.LOGDEBUG)  # writer insertion debugging
            mwriter = writer.strip()
            curg = db.execute('SELECT actor_id FROM actor WHERE name=?',(mwriter,))   
            writertuple = curg.fetchone()                                          # Get writer id from actor table
            curg.close()

            if not writertuple:                   #  If writer not in actor table insert and fetch new actor ID
                db.execute('INSERT into actor (name, art_urls) values (?, ?)', (mwriter, searchUrl,))
                cur = db.execute('SELECT actor_id FROM actor WHERE name=?',(mwriter,))   
                writertuple = cur.fetchone()      #  Get writer id from actor table
                cur.close()
            if writertuple:                       #  Insert writer to movie link in writer link table
                writernumb = writertuple[0] 
                db.execute('INSERT or REPLACE into WRITER_LINK (actor_id, media_id, media_type) values \
                (?, ?, ?)', (writernumb, movienumb, mtype,))
                #xbmc.log('The current writer number is: ' + str(writernumb) + "  " + str(movienumb), xbmc.LOGINFO)

    except Exception as e:
        printexception()
        msynclog ='Mezzmo problem inserting writers for: ' + str(writers) + ' ' + str(movienumb)
        xbmc.log(msynclog, xbmc.LOGINFO)


def insertStudios(movienumb, db, media_type, studios, knative):

    try:
        if knative == 'false':                                                           # Native sync not enabled
            return
        if studios == None or len(studios) == 0:
            return    
        studiolist = studios.split(',')                                                  # Convert studios to list
        xbmc.log('Mezzmo studiolist is: ' + str(studiolist), xbmc.LOGDEBUG)
        for studio in studiolist:     
            xbmc.log('Mezzmo current studio is: ' + str(studio), xbmc.LOGDEBUG)          # studio insertion debugging
            mstudio = studio.strip()
            curs = db.execute('SELECT studio_id FROM studio WHERE name=?',(mstudio,))   
            studiotuple = curs.fetchone()                                                # Get studio id from studio table
            curs.close()

            if not studiotuple:                   #  If studio not in studio table insert and fetch new studio ID
                db.execute('INSERT into STUDIO (name) values (?)', (mstudio,))
                cur = db.execute('SELECT studio_id FROM studio WHERE name=?',(mstudio,))   
                studiotuple = cur.fetchone()      #  Get studio id from studio table
                cur.close()
            if studiotuple:                       #  Insert studio to movie link in studio link table
                studionumb = studiotuple[0] 
                db.execute('INSERT OR REPLACE into STUDIO_LINK (studio_id, media_id, media_type) values \
                (?, ?, ?)', (studionumb, movienumb, media_type,))
                #xbmc.log('The current studio number is: ' + str(studionumb) + "  " + str(movienumb), xbmc.LOGINFO)

    except Exception as e:
        printexception()
        msynclog ='Mezzmo problem inserting studios for: ' + str(studios) + ' ' + str(movienumb)
        xbmc.log(msynclog, xbmc.LOGINFO)


def insertGenre(movienumb, db, media_type, genres):

    genrelist = genres.split(',')                                                    # Convert genres to list
    xbmc.log('Mezzmo genrelist is: ' + str(genrelist), xbmc.LOGDEBUG)
    for genre in genrelist:     
        xbmc.log('Mezzmo current genre is: ' + str(genre), xbmc.LOGDEBUG)            # genre insertion debugging
        mgenre = genre.strip()
        curg = db.execute('SELECT genre_id FROM genre WHERE name=?',(mgenre,))   
        genretuple = curg.fetchone()                                                 # Get genre id from genre table
        curg.close()

        if not genretuple:                   #  If genre not in genre table insert and fetch new genre ID
            db.execute('INSERT into GENRE (name) values (?)', (mgenre,))
            cur = db.execute('SELECT genre_id FROM genre WHERE name=?',(mgenre,))   
            genretuple = cur.fetchone()      #  Get genre id from genre table
            cur.close()
        if genretuple:                       #  Insert genre to movie link in genre link table
            genrenumb = genretuple[0] 
            db.execute('INSERT OR REPLACE into GENRE_LINK (genre_id, media_id, media_type) values \
            (?, ?, ?)', (genrenumb, movienumb, media_type,))
            #xbmc.log('The current genre number is: ' + str(genrenumb) + "  " + str(movienumb), xbmc.LOGINFO)


def playCount(title, vurl, vseason, vepisode, mplaycount, series, mtype, contenturl):

    if mtype != 'audiom':                                         #  Don't update Kodi for music
        playcount.updateKodiPlaycount(int(mplaycount), title, vurl, int(vseason),     \
        int(vepisode), series, mtype)                             #  Update Kodi DB playcount

    rtrimpos = vurl.rfind('/')
    mobjectID = vurl[rtrimpos+1:]                                 #  Get Mezzmo objectID

    if int(mplaycount) <= 0:                                      #  Calcule new play count
        newcount = '1'
    elif int(mplaycount) > 0:
        newcount = '0'

    if mobjectID != None:                                         #  Update Mezzmo playcount if objectID exists
        playcount.setPlaycount(contenturl, mobjectID, newcount, title)
        bookmark.SetBookmark(contenturl, mobjectID, '0')          #  Clear bookmark
        bookmark.updateKodiBookmark(mobjectID, '0', title, mtype)
        nativeNotify()                                            #  Kodi native notification  
        xbmc.sleep(1000)  
        xbmc.executebuiltin('Container.Refresh')


def insertKwords(keywords, mtype, movienumb):

    try:
        if keywords == None or len(keywords) == 0:
            return

        db = openNosyncDB()
        kwordlist = keywords.split(',')                                      # Convert keywords to list
        xbmc.log('Mezzmo keyword list is: ' + str(kwordlist), xbmc.LOGDEBUG) # keywords insertion debugging
        for kword in kwordlist:     
            xbmc.log('Mezzmo current keyword is: ' + str(kword), xbmc.LOGDEBUG)
            mkword = kword.strip()
            curk = db.execute('SELECT kyTitle FROM mKeywords WHERE kyTitle=? and kyType=?',(mkword, mtype,))     
            kwordtuple = curk.fetchone()                                     # Get keyword from keywords

            if not kwordtuple:                                               # If keyword if not found
                if "noview" in mkword.lower():                               # Skip noviews
                    db.execute('INSERT into mKeywords (kyTitle, kyType, kyVar1) \
                    values (?, ?, ?)', (mkword, mtype, "No",))
                else:
                    db.execute('INSERT into mKeywords (kyTitle, kyType, kyVar1) \
                    values (?, ?, ?)', (mkword, mtype, "Yes",))
        if '###' in keywords:
            insertCollection(movienumb, db, mtype, keywords)
        db.commit()
        curk.close()

    except Exception as e:
        printexception()
        msynclog ='Mezzmo problem inserting keywords for: ' + mtype + ' ' + str(movienumb)
        xbmc.log(msynclog, xbmc.LOGINFO)


def insertCollection(movienumb, db, mtype, keywords):

    try:
        if '###' not in keywords:                                #  Only save collections
            return
        collectionlist = keywords.split(',')                     #  Convert keywords to list
        xbmc.log('Mezzmo collectionlist is: ' + str(collectionlist), xbmc.LOGDEBUG)      # collection debugging
        for collection in collectionlist:     
            xbmc.log('Mezzmo current collection is: ' + str(collection), xbmc.LOGDEBUG)
            mcoll = collection.strip()
            curt = db.execute('SELECT coll_id FROM mCollection WHERE name=?',(mcoll,))   
            colltuple = curt.fetchone()                           #  Get coll id from collection table
            curt.close()

            if "###" in mcoll.lower():                            #  Skip noncollection keywords 
                if not colltuple:                                 #  If collection insert and fetch new ID
                    db.execute('INSERT into mCollection (name) values (?)', (mcoll,))
                    cur = db.execute('SELECT coll_id FROM mCollection WHERE name=?',(mcoll,))   
                    colltuple = cur.fetchone()                    #  Get collection id from mCollection table
                    cur.close()
                if colltuple:                                     #  Insert collection into link table
                    collnumb = colltuple[0] 
                    db.execute('INSERT OR REPLACE into mCollection_link (coll_id, media_id, media_type) \
                    values (?, ?, ?)', (collnumb, movienumb, mtype,))
                    #xbmc.log('The current collection number is: ' + str(collnumb) + "  " +             \
                    #str(movienumb), xbmc.LOGINFO)

    except Exception as e:
        printexception()
        msynclog ='Mezzmo problem inserting collection tags for: ' + mtype + ' ' + str(movienumb)
        xbmc.log(msynclog, xbmc.LOGINFO)


def nativeNotify():

    if settings('kodiskin') == 'true':                            #  Kodi native notification
        #xbmc.executebuiltin('ReloadSkin()')
        xbmc.executebuiltin('UpdateLibrary(video)') 


def printexception():

    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    xbmc.log( 'EXCEPTION IN ({0}, LINE {1} "{2}"): {3}'.format(filename, lineno, line.strip(),     \
    exc_obj), xbmc.LOGINFO)