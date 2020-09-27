import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import os
import json
import urllib.request, urllib.error, urllib.parse
import urllib.request, urllib.parse, urllib.error
from datetime import datetime, timedelta

addon = xbmcaddon.Addon()

def checkTVShow(fileId, seriesname, mgenre, db, mrating, mstudio): # Check if TV show exists in database

    cure = db.execute('SELECT idShow FROM tvshow WHERE c00=? and c17=?',(seriesname,     \
    int(fileId[3]),))
    showtuple = cure.fetchone()
    if not showtuple:				 # If not found add show
        mgenres = mgenre.replace(',' , ' /')                         #  Format genre for proper Kodi display
        db.execute('INSERT into tvshow (c00, c08, c09, c17, c13, c14) values (?, ?, ?, ?, ? ,?)', \
        (seriesname, mgenres, seriesname, fileId[3], mrating, mstudio,))
        curs = db.execute('SELECT idShow FROM tvshow WHERE c00=? and c17=?',(seriesname,   \
        fileId[3],))
        showtuple = curs.fetchone()       	 # Get new TV Show id
        shownumb = showtuple[0]
        curs.close()
        #xbmc.log('TV Show added ' + seriesname + " " + str(shownumb), xbmc.LOGINFO)
    else:
        shownumb = showtuple[0]
        #xbmc.log('TV Show found ' + seriesname + " " + str(shownumb), xbmc.LOGINFO)                 

    cure.close()
    return(shownumb)


def checkSeason(db, shownumb, season):           # Check if Episode season exists in seasons table

    curse = db.execute('SELECT idSeason FROM seasons WHERE idShow=? and season=?',(shownumb, season,))
    seasontuple = curse.fetchone()
    if not seasontuple:				 # If not found add season
        db.execute('INSERT into seasons(idshow, season, name) values (?, ?, ?)', \
        (shownumb, season, 'Season ' + str(season),))
        curss = db.execute('SELECT idSeason FROM seasons WHERE idShow=? and season=?',(shownumb, season,))
        seasontuple = curss.fetchone()
        seasonnumb = seasontuple[0]
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
    
installed_version = get_installedversion()


def getDatabaseName():
    if installed_version == '10':
        return "MyVideos37.db"
    elif installed_version == '11':
        return "MyVideos60.db"
    elif installed_version == '12':
        return "MyVideos75.db"
    elif installed_version == '13':
        return "MyVideos78.db"
    elif installed_version == '14':
        return "MyVideos90.db"
    elif installed_version == '15':
        return "MyVideos93.db"
    elif installed_version == '16':
        return "MyVideos99.db"
    elif installed_version == '17':
        return "MyVideos107.db"
    elif installed_version == '18':
        return "MyVideos116.db"
    elif installed_version == '19':
        return "MyVideos117.db"
       
    return ""  


def openKodiDB():                                  #  Open Kodi database
    try:
        from sqlite3 import dbapi2 as sqlite
    except:
        from pysqlite2 import dbapi2 as sqlite
                      
    DB = os.path.join(xbmc.translatePath("special://database"), getDatabaseName())
    db = sqlite.connect(DB)

    return(db)    


def getPath(itemurl):		            # Find path string for media file

    rtrimpos = itemurl.rfind('/')           # Check for container / path change
    pathcheck = itemurl[:rtrimpos+1]
    #xbmc.log('The media file path is : ' + pathcheck, xbmc.LOGINFO)
    return(pathcheck)   

def getMServer(itemurl):		    # Find server string for media file

    rtrimpos = itemurl.rfind(':',7)      
    serverid = itemurl[:rtrimpos+7]
    #xbmc.log('The serverid : ' + serverid, xbmc.LOGINFO)
    return(serverid)  


def urlMatch(url1, url2):                       #  Check if URLs match with or without DNS

    if not url1[7].isdigit() or not url2[7].isdigit():    
        compare1 = url1[url1.rfind(':'):]       #  If DNS only compare port and file name
        compare2 = url2[url2.rfind(':'):]       
    else:
        compare1 = url1
        compare2 = url2
    #xbmc.log('Compare1 and Compare2 : ' + compare1 + " " + compare2, xbmc.LOGINFO)
    if compare1 == compare2:
        return(True)
    else:
        return(False)


def countKodiRecs(contenturl):                  # returns count records in Kodi DB 
    try:
        from sqlite3 import dbapi2 as sqlite
    except:
        from pysqlite2 import dbapi2 as sqlite
                      
    DB = os.path.join(xbmc.translatePath("special://database"), getDatabaseName())  
    db = sqlite.connect(DB)

    rfpos = contenturl.find(':',7)              #  Get Mezzmo server port info
    serverport = '%' + contenturl[rfpos+1:rfpos+6] + '%'

    curm = db.execute('SELECT count (DISTINCT idMovie) FROM movie INNER JOIN path    \
    WHERE strpath LIKE ?', (serverport,))
    mcount = curm.fetchone()[0]

    cure = db.execute('SELECT count (DISTINCT idEpisode) FROM episode INNER JOIN path \
    WHERE strpath LIKE ?', (serverport,))
    ecount = cure.fetchone()[0]
    
    recscount = mcount + ecount                 #  Total count of movies and TV episodes
    xbmc.log('Mezzmo total Kodi DB record count: ' + str(recscount), xbmc.LOGINFO)

    curm.close()
    cure.close()       
    db.close()
    return(recscount) 


def optimizeDB():                               # Optimize Kodi DB 
    try:
        from sqlite3 import dbapi2 as sqlite
    except:
        from pysqlite2 import dbapi2 as sqlite
                    
    DB = os.path.join(xbmc.translatePath("special://database"), getDatabaseName())  
    db = sqlite.connect(DB)

    db.execute('REINDEX',)
    db.execute('VACUUM',)
    xbmc.log('Mezzmo database reindex and vacuum complete.', xbmc.LOGNOTICE)

    db.commit()    
    db.close()


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


def tvChecker(mseason, mepisode):       # add TV shows to Kodi DB if enabled and is TV show
    tvcheck = 1
    if (int(mseason) > 0  or int(mepisode) > 0) and addon.getSetting('koditv') == 'false':
        tvcheck = 0 
    #xbmc.log('TV check value is: ' + str(tvcheck), xbmc.LOGINFO)

    return(tvcheck)


def kodiCleanDB(ContentDeleteURL, force):

    if addon.getSetting('kodiclean') == 'true' or force == 1:  #  clears Kodi DB Mezzmo data if enabled in setings

        try:
            from sqlite3 import dbapi2 as sqlite
        except:
            from pysqlite2 import dbapi2 as sqlite

        clean = addon.getSetting('kodiclean') == 'true'
        DB = os.path.join(xbmc.translatePath("special://database"), getDatabaseName())  
        db = sqlite.connect(DB)
        xbmc.log('Content delete URL: ' + ContentDeleteURL, xbmc.LOGDEBUG)
         
        rfpos = ContentDeleteURL.find(':',7)      #  Get Mezzmo server info
        serverport = '%' + ContentDeleteURL[rfpos+1:rfpos+6] + '%'

        db.execute('DELETE FROM art WHERE url LIKE ?', (serverport,))
        db.execute('DELETE FROM actor WHERE art_urls LIKE ?', (serverport,))
        db.execute('DELETE FROM tvshow WHERE c17 LIKE ?', (serverport,))
        xbmc.log('Mezzmo serverport is: ' + serverport, xbmc.LOGDEBUG)
        curf = db.execute('SELECT idFile FROM files INNER JOIN path USING (idPath) WHERE         \
        strpath LIKE ?', (serverport,))           #  Get file and movie list
        idlist = curf.fetchall()
        for a in range(len(idlist)):              #  Delete Mezzmo file and Movie data
            # xbmc.log('Clean rows found: ' + str(idlist[a][0]), xbmc.LOGINFO)
            db.execute('DELETE FROM files WHERE idFile=?',(idlist[a][0],))
            db.execute('DELETE FROM movie WHERE idFile=?',(idlist[a][0],))
            db.execute('DELETE FROM episode WHERE idFile=?',(idlist[a][0],))
        db.execute('DELETE FROM path WHERE strPath LIKE ?', (serverport,)) 

        xbmc.log('Kodi database Mezzmo data cleared. ' + str(clean) + ' ' + str(force), xbmc.LOGINFO)
        curf.close()  
        db.commit()
        db.close()
        addon.setSetting('kodiclean', 'false')    # reset back to false after clearing


def checkDBpath(itemurl, mtitle, mplaycount, db, mpath, mserver, mseason, mepisode, mseries, \
    mlplayed, mdupelog): #  Check if path exists
    rtrimpos = itemurl.rfind('/')
    filecheck = itemurl[rtrimpos+1:]
    rfpos = itemurl.find(':',7)
    serverport = itemurl[rfpos+1:rfpos+6]      #  Get Mezzmo server port info 
    xbmc.log('Mezzmo checkDbPath path check and file check: ' + str(mpath) + ' ' + str(filecheck), xbmc.LOGDEBUG)
    if mlplayed == '0':                        #  Set Mezzmo last played to null if 0
        mlplayed = ''

    curpth = db.execute('SELECT idPath FROM path WHERE strpath=?',(mserver,))   # Check if server path exists in Kodi DB
    ppathtuple = curpth.fetchone()
    if not ppathtuple:                # add parent server path to Kodi DB if it doesn't exist
        db.execute('INSERT into path (strpath, strContent) values (?, ?)', (mserver, 'movies',))
        curpp = db.execute('SELECT idPath FROM path WHERE strPATH=?',(mserver,)) 
        ppathtuple = curpp.fetchone()
        ppathnumb = ppathtuple[0]
        xbmc.log('Mezzmo checkDBpath parent path added: ' + str(ppathnumb) + " " + mserver, xbmc.LOGINFO)
        db.execute('UPDATE PATH SET strContent=?, idParentPath=? WHERE strPath LIKE ? AND idPath <> ?', \
        ('movies', ppathnumb, '%' + serverport + '%', ppathnumb))   # Update Child paths with parent information
        curpp.close() 
    ppathnumb = ppathtuple[0]         # Parent path number
    
    if int(mepisode) > 0 or int(mseason) > 0:
        media = 'episode'
        episodes = 1
        curf = db.execute('SELECT idFile, playcount, idPath, lastPlayed FROM files INNER JOIN episode \
        USING (idFile) INNER JOIN path USING (idPath) INNER JOIN tvshow USING (idshow)                \
        WHERE tvshow.c00=? and idParentPath=? and episode.c12=? and episode.c13=? COLLATE NOCASE',    \
        (mseries, ppathnumb, mseason, mepisode))     # Check if episode exists in Kodi DB under parent path 
        filetuple = curf.fetchone()
        curf.close()
        xbmc.log('Checking path for : ' + mtitle, xbmc.LOGDEBUG)     # Path check debugging
    else:
        media = 'movie'
        episodes = 0
        curf = db.execute('SELECT idFile, playcount, idPath, lastPlayed FROM files INNER JOIN movie   \
        USING (idFile) INNER JOIN path USING (idPath) WHERE c00=? and idParentPath=? COLLATE          \
        NOCASE', (mtitle, ppathnumb))   # Check if movie exists in Kodi DB under parent path  
        filetuple = curf.fetchone()
        curf.close()
        #xbmc.log('Checking path for : ' + mtitle, xbmc.LOGINFO)     # Path check debugging

    if not filetuple:                 # if not exist insert into Kodi DB and return file key value
        curp = db.execute('SELECT idPath FROM path WHERE strPATH=?',(mpath,))  #  Check path table
        pathtuple = curp.fetchone()
        xbmc.log('File not found : ' + mtitle, xbmc.LOGDEBUG)
        if not pathtuple:             # if path doesn't exist insert into Kodi DB
            db.execute('INSERT into PATH (strpath, strContent, idParentPath) values (?, ?, ?)', \
            (mpath, 'movies', ppathnumb))
            curp = db.execute('SELECT idPath FROM path WHERE strPATH=?',(mpath,)) 
            pathtuple = curp.fetchone()
        pathnumb = pathtuple[0]
        curp.close()

        db.execute('INSERT into FILES (idPath, strFilename, playCount, lastPlayed) values       \
        (?, ?, ?, ? )', (str(pathnumb), filecheck, mplaycount, mlplayed))
        cur = db.execute('SELECT idFile FROM files WHERE strFilename=?',(filecheck,)) 
        filetuple = cur.fetchone()
        filenumb = filetuple[0]
        cur.close()
        realfilenumb = filenumb      # Save real file number before resetting found flag
    else:                            # Return 0 if file already exists and check for play count change 
        filenumb = filetuple[0] 
        xbmc.log('File found : ' + filecheck + ' ' + str(filenumb), xbmc.LOGDEBUG)
        fpcount = filetuple[1]
        flplayed = filetuple[3]       
        if fpcount != mplaycount or flplayed != mlplayed :    # If Mezzmo playcount or lastPlayed different
            db.execute('UPDATE files SET playCount=?, lastPlayed=? WHERE idFile=?',   \
            (mplaycount, mlplayed, filenumb,))
            # xbmc.log('File Play mismatch: ' + str(fpcount) + ' ' + str(mplaycount), xbmc.LOGNINFO)
        if mdupelog == 'true':
            xbmc.log('Mezzmo duplicate found.  Kodi file table record #: ' + str(filenumb) + ' Title: ' + \
            mtitle, xbmc.LOGINFO)
        realfilenumb = filenumb      #  Save real file number before resetting found flag
        pathnumb = filetuple[2]
        filenumb = 0     
            
    curpth.close()    
    return[filenumb, realfilenumb, ppathnumb, serverport, episodes, pathnumb] # Return file, path and info


def writeMovieToDb(fileId, mtitle, mplot, mtagline, mwriter, mdirector, myear, murate, mduration, mgenre, mtrailer, \
    mrating, micon, kchange, murl, db, mstudio, mstitle, mdupelog):  

    if fileId[0] > 0:                             # Insert movie if does not exist in Kodi DB
        #xbmc.log('The current movie is: ' + mtitle, xbmc.LOGINFO)
        mgenres = mgenre.replace(',' , ' /')      # Format genre for proper Kodi display
        dupm = db.execute('SELECT idMovie FROM movie WHERE idFile=? and c00=?', (fileId[0], mtitle))
        dupmtuple = dupm.fetchone() 
        if dupmtuple == None:                                        # Ensure movie doesn't exist
            db.execute('INSERT into MOVIE (idFile, c00, c01, c03, c06, c11, c15, premiered, c14, c19, c12, c18, c10, \
            C23) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (fileId[0], mtitle, mplot, mtagline, mwriter,   \
            mduration, mdirector, myear, mgenres, mtrailer, mrating, mstudio, mstitle, fileId[5])) #  Add movie 
            cur = db.execute('SELECT idMovie FROM movie WHERE idFile=?',(str(fileId[0]),))  
            movietuple = cur.fetchone()
            movienumb = movietuple[0]                                # get new movie id 
            insertArt(movienumb, db, 'movie', murl, micon)           # Insert artwork for movie  
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
            movienumb = dupmtuple[0]                                  # If dupe, return existing movie id
        dupm.close()
    elif kchange == 'true':                        #  Update metadata if changes
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
            db.execute('UPDATE MOVIE SET c01=?, c03=?, c06=?, c11=?, c15=?, premiered=?, c14=?, c19=?, c12=?, \
            c18=?, c10=?, c23=? WHERE idMovie=?', (mplot,  mtagline, mwriter, mduration, mdirector, myear,    \
            mgenres, mtrailer, mrating, mstudio, mstitle, fileId[5], movienumb)) #  Update movie information
            db.execute('UPDATE rating SET rating=? WHERE rating_id=?', (murate, krate))
            db.execute('DELETE FROM art WHERE media_id=? and media_type=?',(str(movienumb), 'movie'))
            insertArt(movienumb, db, 'movie', murl, micon)            # Update artwork for movie
            movienumb = 999999                                        # Trigger actor update
            if mdupelog == 'false':
                xbmc.log('There was a Mezzmo metadata change detected: ' + mtitle, xbmc.LOGINFO)
        curm.close()
    else:
        movienumb = 0                                                 # disable change checking

    return(movienumb)


def writeEpisodeToDb(fileId, mtitle, mplot, mtagline, mwriter, mdirector, maired, murate, mduration, mgenre, mtrailer, \
    mrating, micon, kchange, murl, db, mstudio, mstitle, mseason, mepisode, shownumb, mdupelog):  

    #xbmc.log('Mezzmo fileId is: ' + str(fileId), xbmc.LOGINFO)
    if fileId[0] > 0:                                                #  Insert movie if does not exist in Kodi DB
        #xbmc.log('The current episode is: ' + mtitle, xbmc.LOGINFO)
        mgenres = mgenre.replace(',' , ' /')                         #  Format genre for proper Kodi display
        dupe = db.execute('SELECT idEpisode FROM episode WHERE idFile=? and c00=?', (fileId[0], mtitle))
        dupetuple = dupe.fetchone() 
        if dupetuple == None:                                        # Ensure episode doesn't exist
            db.execute('INSERT into EPISODE (idFile, c00, c01, c09, c10, c04, c12, c13, c05, idshow, c19) values    \
            (?, ?, ?, ?, ?, ?, ? ,? ,? ,?, ?)', (fileId[0], mtitle, mplot, mduration, mdirector, mwriter, mseason,  \
            mepisode, maired[:10], shownumb, fileId[5]))             #  Add episode information
            cur = db.execute('SELECT idEpisode FROM episode WHERE idFile=?',(str(fileId[0]),))  
            episodetuple = cur.fetchone()
            movienumb = episodetuple[0]                              # get new movie id  
            insertArt(movienumb, db, 'episode', murl, micon)         # Insert artwork for episode    
            db.execute('INSERT into RATING (media_id, media_type, rating_type, rating) values   \
            (?, ?, ?, ?)', (movienumb,  'episode', 'imdb', murate,))
            curr = db.execute('SELECT rating_id FROM rating WHERE media_id=? and media_type=?', \
            (movienumb, 'episode',))
            ratetuple = curr.fetchone() 
            ratenumb = ratetuple[0]
            seasonId = checkSeason(db, shownumb, mseason)
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
        if kplot != mplot or int(kduration) != mduration or kdirector != mdirector or kwriter != mwriter \
        or kseason != mseason or kepisode != mepisode or kaired != maired[:10] or kshow != shownumb: 
            db.execute('UPDATE EPISODE SET c01=?, c09=?, c10=?, c04=?, c12=?, c13=?, c05=?, idShow=?, C19=? \
            WHERE idEpisode=?', (mplot, mduration, mdirector, mwriter, mseason, mepisode, maired[:10],      \
            shownumb, fileId[5], movienumb))                          #  Update Episode information
            db.execute('UPDATE rating SET rating=? WHERE rating_id=?', (murate, krate))
            seasonId = checkSeason(db, shownumb, mseason)
            db.execute('UPDATE episode SET idSeason=? WHERE idEpisode=?', (seasonId, movienumb,))
            db.execute('DELETE FROM art WHERE media_id=? and media_type=?',(str(movienumb), 'episode'))
            insertArt(movienumb, db, 'episode', murl, micon)          # Insert artwork for episode
            movienumb = 999999                                        # Trigger actor update
            if mdupelog == 'false':
                xbmc.log('There was a Mezzmo metadata change detected: ' + mtitle, xbmc.LOGINFO)            
        movienumb = 0                                                 # disable change checking
        curm.close()

    return(movienumb)


def writeActorsToDb(actors, movieId, imageSearchUrl, mtitle, db, fileId):
    actorlist = actors.replace(', Jr.' , ' Jr.').replace(', Sr.' , ' Sr.').split(', ')    

    if fileId[4] == 0:
       media_type = 'movie'
    elif fileId[4] == 1:
       media_type = 'episode'
 
    xbmc.log('Mezzmo writeActorsToDb movie and movieID are: ' + str(movieId) + ' ' + mtitle, xbmc.LOGDEBUG)
    if movieId == 999999:                           # Actor info needs updated
        curm = db.execute('SELECT idMovie FROM movie INNER JOIN files USING (idfile) \
        INNER JOIN path USING (idpath) WHERE idFile=? COLLATE NOCASE',    \
        (str(fileId[1]),))                          # Get real movie ID
        movietuple = curm.fetchone()
        movieId = movietuple[0]                     # Get real movieId
        db.execute('DELETE FROM actor_link WHERE media_id=? and media_type=?',(str(movieId), media_type))
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
                #xbmc.log('The current actor number is: ' + str(actornumb) + "  " + str(movieId), xbmc.LOGINFO)  


def writeMovieStreams(fileId, mvcodec, maspect, mvheight, mvwidth, macodec, mchannels, mduration, mtitle,   \
    kchange, itemurl, micon, murl, db, mpath, mdupelog):

    rtrimpos = itemurl.rfind('/')       # Check for container / path change
    filecheck = itemurl[rtrimpos+1:]

    if fileId[4] == 0:
       media_type = 'movie'
    elif fileId[4] == 1:
       media_type = 'episode'

    if fileId[0] > 0:                   #  Insert stream details if file does not exist in Kodi DB
        insertStreams(fileId[0], db, mvcodec, maspect, mvwidth, mvheight, mduration, macodec, mchannels)
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
        idflist = scur.fetchall()
        rows = len(idflist)
        if rows == 4:                              # Ensure all data exsts
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
                iconmatch is False) and rows == 4:
                if mdupelog == 'false':
                    xbmc.log('There was a Mezzmo streamdetails or artwork change detected: ' + mtitle, xbmc.LOGINFO)
                    xbmc.log('Mezzmo streamdetails artwork rowcount = ' +  str(rows), xbmc.LOGINFO)
                xbmc.log('Mezzmo streamdetails sdur and mduration are: ' + str(sdur) + ' ' + str(mduration), xbmc.LOGDEBUG)
                xbmc.log('Mezzmo streamdetails svcodec and mvcodec are: ' + str(svcodec) + ' ' + str(mvcodec), xbmc.LOGDEBUG)
                xbmc.log('Mezzmo streamdetails sacodec and macodec are: ' + str(sacodec) + ' ' + str(macodec), xbmc.LOGDEBUG)
                xbmc.log('Mezzmo streamdetails kpath and mpath are: ' + str(kpath) + ' ' + str(mpath), xbmc.LOGDEBUG)
                xbmc.log('Mezzmo streamdetails kicon micon are: ' + str(kicon) + ' ' + str(micon), xbmc.LOGDEBUG)
                delete_query = 'DELETE FROM streamdetails WHERE idFile = ' + str(filenumb)
                db.execute(delete_query)          #  Delete old stream info
                insertStreams(filenumb, db, mvcodec, maspect, mvwidth, mvheight, mduration, macodec, mchannels)
                curp = db.execute('SELECT idPath FROM path WHERE strPATH=?',(mpath,))  #  Check path table
                pathtuple = curp.fetchone()
                if not pathtuple:                # if path doesn't exist insert into Kodi DB and return path key value
                    db.execute('INSERT into PATH (strpath, strContent, idParentPath) values (?, ?, ?)', \
                    (mpath, 'movies', int(fileId[2])))
                    curp = db.execute('SELECT idPath FROM path WHERE strPATH=?',(mpath,)) 
                    pathtuple = curp.fetchone()
                pathnumb = pathtuple[0]
                db.execute('UPDATE files SET idPath=?, strFilename=? WHERE idFile=?', (pathnumb, filecheck, filenumb))
                db.execute('UPDATE movie SET c23=? WHERE idFile=?', (pathnumb, filenumb))
                db.execute('DELETE FROM art WHERE media_id=? and media_type=?',(str(movienumb), media_type))
                insertArt(movienumb, db, media_type, murl, micon)     # Insert artwork for episode / movie
                curp.close()
        else:                                   # Repair missing streamdetails data
            db.execute('DELETE FROM streamdetails WHERE idFile=?',(fileId[1],))
            insertStreams(fileId[1], db, mvcodec, maspect, mvwidth, mvheight, mduration, macodec, mchannels)
            xbmc.log('The Mezzmo incomplete streamdetails repaired for: ' + mtitle, xbmc.LOGINFO)
        scur.close()

def insertStreams(filenumb, db, mvcodec, maspect, mvwidth, mvheight, mduration, macodec, mchannels):

    db.execute('INSERT into STREAMDETAILS (idFile, iStreamType, strVideoCodec, fVideoAspect, iVideoWidth, \
    iVideoHeight, iVideoDuration) values (?, ?, ?, ?, ? ,? ,?)', (filenumb, '0', mvcodec, maspect,       \
    mvwidth, mvheight, mduration))
    db.execute('INSERT into STREAMDETAILS (idFile, iStreamType, strAudioCodec, iAudioChannels) values     \
    (?, ?, ? ,?)', (filenumb, '1', macodec, mchannels))
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