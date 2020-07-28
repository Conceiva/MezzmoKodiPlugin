import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon

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
        #xbmc.log('TV Show added ' + seriesname + " " + str(shownumb), xbmc.LOGINFO)
    else:
        shownumb = showtuple[0]
        #xbmc.log('TV Show found ' + seriesname + " " + str(shownumb), xbmc.LOGINFO)                 

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
    else:
        seasonnumb = seasontuple[0]
    #xbmc.log('The current season number is: ' + str(seasonnumb), xbmc.LOGINFO)

    return(seasonnumb)                           # Return seasons table idSeason  


def writeMovieToDb(fileId, mtitle, mplot, mtagline, mwriter, mdirector, myear, murate, mduration, mgenre, mtrailer, \
    mrating, micon, kchange, murl, db, mstudio, mstitle):  

    if fileId[0] > 0:                             # Insert movie if does not exist in Kodi DB
        #xbmc.log('The current movie is: ' + mtitle, xbmc.LOGINFO)
        mgenres = mgenre.replace(',' , ' /')      # Format genre for proper Kodi display
        db.execute('INSERT into MOVIE (idFile, c00, c01, c03, c06, c11, c15, premiered, c14, c19, c12, c18, c10, C23)  \
        values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (fileId[0], mtitle, mplot, mtagline, mwriter, mduration,   \
        mdirector, myear, mgenres, mtrailer, mrating, mstudio, mstitle, fileId[5]))        #  Add movie information
        cur = db.execute('SELECT idMovie FROM movie WHERE idFile=?',(str(fileId[0]),))  
        movietuple = cur.fetchone()
        movienumb = movietuple[0]                 # get new movie id    
        db.execute('INSERT into ART (media_id, media_type, type, url) values (?, ?, ?, ?)', \
        (movienumb, 'movie', 'poster', micon))
        db.execute('INSERT into ART (media_id, media_type, type, url) values (?, ?, ?, ?)', \
        (movienumb, 'movie', 'fanart', murl))
        db.execute('INSERT into ART (media_id, media_type, type, url) values (?, ?, ?, ?)', \
        (movienumb, 'movie', 'thumb', micon))
        db.execute('INSERT into ART (media_id, media_type, type, url) values (?, ?, ?, ?)', \
        (movienumb, 'movie', 'icon', micon))
        db.execute('INSERT into RATING (media_id, media_type, rating_type, rating) values   \
        (?, ?, ?, ?)', (movienumb,  'movie', 'imdb', murate,))
        curr = db.execute('SELECT rating_id FROM rating WHERE media_id=? and media_type=?', \
        (movienumb, 'movie',))
        ratetuple = curr.fetchone() 
        ratenumb = ratetuple[0]
        db.execute('UPDATE movie SET c05=? WHERE idMovie=?', (ratenumb, movienumb))

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
            movienumb = 999999                                        # Trigger actor update
            xbmc.log('There was a Mezzmo metadata change detected: ' + mtitle, xbmc.LOGINFO)
    else:
        movienumb = 0                                                 # disable change checking

    return(movienumb)


def writeEpisodeToDb(fileId, mtitle, mplot, mtagline, mwriter, mdirector, maired, murate, mduration, mgenre, mtrailer, \
    mrating, micon, kchange, murl, db, mstudio, mstitle, mseason, mepisode, shownumb):  

    #xbmc.log('Mezzmo fileId is: ' + str(fileId), xbmc.LOGINFO)
    if fileId[0] > 0:                                                #  Insert movie if does not exist in Kodi DB
        #xbmc.log('The current episode is: ' + mtitle, xbmc.LOGINFO)
        mgenres = mgenre.replace(',' , ' /')                         #  Format genre for proper Kodi display
        db.execute('INSERT into EPISODE (idFile, c00, c01, c09, c10, c04, c12, c13, c05, idshow, c19) values    \
        (?, ?, ?, ?, ?, ?, ? ,? ,? ,?, ?)', (fileId[0], mtitle, mplot, mduration, mdirector, mwriter, mseason,  \
        mepisode, maired[:10], shownumb, fileId[5]))                 #  Add episode information
        cur = db.execute('SELECT idEpisode FROM episode WHERE idFile=?',(str(fileId[0]),))  
        episodetuple = cur.fetchone()
        movienumb = episodetuple[0]                                  # get new movie id    
        db.execute('INSERT into ART (media_id, media_type, type, url) values (?, ?, ?, ?)', \
        (movienumb, 'episode', 'poster', micon))
        db.execute('INSERT into ART (media_id, media_type, type, url) values (?, ?, ?, ?)', \
        (movienumb, 'episode', 'fanart', murl))
        db.execute('INSERT into ART (media_id, media_type, type, url) values (?, ?, ?, ?)', \
        (movienumb, 'episode', 'thumb', micon))
        db.execute('INSERT into ART (media_id, media_type, type, url) values (?, ?, ?, ?)', \
        (movienumb, 'episode', 'icon', micon))
        db.execute('INSERT into RATING (media_id, media_type, rating_type, rating) values   \
        (?, ?, ?, ?)', (movienumb,  'episode', 'imdb', murate,))
        curr = db.execute('SELECT rating_id FROM rating WHERE media_id=? and media_type=?', \
        (movienumb, 'episode',))
        ratetuple = curr.fetchone() 
        ratenumb = ratetuple[0]
        seasonId = checkSeason(db, shownumb, mseason)
        db.execute('UPDATE episode SET c03=?, idSeason=? WHERE idEpisode=?', (ratenumb, seasonId, movienumb,))

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
        or kseason != mseason or kepisode != mepisode or kaired != maired or kshow != shownumb: 
            db.execute('UPDATE EPISODE SET c01=?, c09=?, c10=?, c04=?, c12=?, c13=?, c05=?, idShow=?, C19=? \
            WHERE idEpisode=?', (mplot, mduration, mdirector, mwriter, mseason, mepisode, maired[:10],      \
            shownumb, fileId[5], movienumb))                          #  Update Episode information
            db.execute('UPDATE rating SET rating=? WHERE rating_id=?', (murate, krate))
            seasonId = checkSeason(db, shownumb, mseason)
            db.execute('UPDATE episode SET idSeason=? WHERE idEpisode=?', (seasonId, movienumb,))
            movienumb = 999999                                        # Trigger actor update
            xbmc.log('There was a Mezzmo metadata change detected: ' + mtitle, xbmc.LOGINFO)            
        movienumb = 0                                                 # disable change checking

    return(movienumb)