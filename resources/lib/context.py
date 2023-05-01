import xbmc
import xbmcgui
import xbmcplugin
import os
import xbmcaddon
import media
import sys
import bookmark
import utilities

#xbmc.log('Name of script: ' + str(sys.argv[0]), xbmc.LOGINFO)
#xbmc.log('Number of arguments: ' + str(len(sys.argv)), xbmc.LOGINFO)
#xbmc.log('The arguments are: ' + str(sys.argv), xbmc.LOGINFO)


def contextMenu():                                       # Display contxt menu for native Kodi skin

    addon = xbmcaddon.Addon()
    menuitem1 = addon.getLocalizedString(30434)
    menuitem2 = addon.getLocalizedString(30384)
    menuitem3 = addon.getLocalizedString(30372)
    menuitem4 = addon.getLocalizedString(30373) 
    menuitem5 = addon.getLocalizedString(30436) 
    menuitem6 = addon.getLocalizedString(30437) 
    menuitem7 = addon.getLocalizedString(30440)
    menuitem8 = addon.getLocalizedString(30467)
    menuitem9 = addon.getLocalizedString(30468)    
    menuitem10 = addon.getLocalizedString(30469)
    menuitem11 = addon.getLocalizedString(30470)
    menuitem12 = addon.getLocalizedString(30481)       
    minfo = sys.listitem.getVideoInfoTag()
    mtitle = minfo.getTitle()
    mtype = minfo.getMediaType()
    dbid = minfo.getDbId()
    trcount = media.settings('trcount')
    prviewct = int(media.settings('prviewct')) 
    contenturl = media.settings('contenturl')
    icon = sys.listitem.getArt('poster')   

    xbmc.executebuiltin('Dialog.Close(all, true)')
    titleinfo = getPlayCount(mtitle, mtype)              # Get info for title
    title = titleinfo[0]
    vurl = titleinfo[1]
    vseason = titleinfo[2]
    vepisode = titleinfo[3]    
    pcount = titleinfo[4]
    vseries = titleinfo[5]
    movieset = titleinfo[6]
    mezyear = titleinfo[7] 
    xbmc.log('Mezzmo titleinfo is: ' + str(titleinfo), xbmc.LOGDEBUG)
    #xbmc.log('Mezzmo mediatype is: ' + str(mtype), xbmc.LOGINFO)

    psfile = media.openNosyncDB()                        # Open Trailer database
    cselect = []
    collection = 'none'
    curpt = psfile.execute('SELECT count (trUrl) FROM mTrailers WHERE trTitle=?', (title,))
    tcontext = curpt.fetchone()                          # Get trailer count from database
    curpk = psfile.execute('SELECT count (kyTitle) FROM mKeywords WHERE kyType=? and kyTitle \
    not like ? AND (kyVar1 <> ? OR kyVar1 IS NULL)', (mtype, '%###%', 'No',))
    kcontext = curpk.fetchone()                          # Get keyword count from database   

    pdfile = media.openKodiDB()                          # Open Kodi DB
    musicvid = media.settings('musicvid')                # Check if musicvideo sync is enabled
    if mtype == 'musicvideo' and musicvid == 'true':     # Find musicvideo bookmark
        curpt = pdfile.execute('SELECT idBookmark FROM bookmark INNER JOIN musicvideo_view USING  \
        (idFile) WHERE musicvideo_view.c00=?', (mtitle,))
        bcontext = curpt.fetchone()                      # Get bookmark from database
        curpc = psfile.execute('SELECT name FROM mCollection INNER JOIN mCollection_link USING    \
        (coll_id) WHERE media_id=? and media_type=?', (dbid, 'musicvideo',))
        tcollection = curpc.fetchall()                   # Get tags for collections
        if tcollection:
            collection = tcollection[0][0].strip()
        else:
            collection = 'none' 
    elif mtype == 'episode':                             # Find episode bookmark
        curpt = pdfile.execute('SELECT idBookmark FROM bookmark INNER JOIN episode_view USING     \
        (idFile) WHERE episode_view.c00=?', (mtitle,))
        bcontext = curpt.fetchone()                      # Get bookmark from database
        curpc = psfile.execute('SELECT name FROM mCollection INNER JOIN mCollection_link USING    \
        (coll_id) WHERE media_id=? and media_type=?', (dbid, 'episode',))
        tcollection = curpc.fetchall()                   # Get tags for collections
        if tcollection:
            collection = tcollection[0][0].strip()
        else:
            collection = 'none' 
    else:
        curpt = pdfile.execute('SELECT idBookmark FROM bookmark INNER JOIN movie_view USING       \
        (idFile) WHERE movie_view.c00=?', (mtitle,))
        bcontext = curpt.fetchone()                      # Get bookmark from database
        curpc = psfile.execute('SELECT name FROM mCollection INNER JOIN mCollection_link USING    \
        (coll_id) WHERE media_id=? and media_type=?', (dbid, 'movie',))
        tcollection = curpc.fetchall()                   # Get tags for collections
        if tcollection:
            collection = tcollection[0][0].strip()
        else:
            collection = 'none'      
    pdfile.close()
    psfile.close()

    if pcount == None:                                   # Kodi playcount is null
        cselect.append(menuitem3)
        pcount = 0
    elif pcount == 0:                                    # Kodi playcount is 0
        cselect.append(menuitem3)
    elif pcount > 0:
        cselect.append(menuitem4)

    if bcontext:                                         # If bookmark exists
        cselect.append(menuitem7)             

    if tcontext[0] > 0 and int(trcount) > 0:             # If trailers for movie and enabled
        cselect.append(menuitem1)

    if prviewct > 0 and mtype == 'movie':                # If Mezmo Movie Previews > 0
        cselect.append(menuitem12)

    if movieset != 'Unknown Album' and mtype == 'movie': # If movieset and type is movie
        cselect.append(menuitem8)

    if collection != 'none' and (mtype == 'movie' or mtype == 'episode'):  # If collection tag and type
        cselect.append(menuitem9) 

    if collection != 'none' and mtype == 'musicvideo':   # If collection tag and type is musicv
        cselect.append(menuitem10)   

    if kcontext[0] > 0 :                                 # If Keywords for media type
        cselect.append(menuitem11)  

    cselect.append(menuitem2)                            # Logs & Stats
    cselect.append(menuitem6)                            # Mezzmo Search
    cselect.append(menuitem5)                            # Mezzmo Addon Gui
    ddialog = xbmcgui.Dialog()    
    vcontext = ddialog.select(addon.getLocalizedString(30471), cselect)

    if vcontext < 0:                                     # User cancel
        xbmc.executebuiltin('Dialog.Close(all, true)')
        return      
    elif (cselect[vcontext]) == menuitem1:               # Mezzmo trailers
        utilities.trDisplay(title, trcount, icon)
    elif (cselect[vcontext]) == menuitem12:              # Mezzmo Movie Previews
        utilities.moviePreviews(title, vurl, prviewct, mezyear, icon)
    elif (cselect[vcontext]) == menuitem2:               # Mezzmo Logs & stats
        utilities.displayMenu()
    elif (cselect[vcontext]) == menuitem3 or (cselect[vcontext]) == menuitem4:
        if utilities.checkItemChange(cselect[vcontext], addon.getLocalizedString(30473)) < 1:
            return  
        if not vurl:
            pcdialog = xbmcgui.Dialog()
            dialog_text = "Unable to modify the playcount.  Selected item URL is missing."        
            pcdialog.ok(addon.getLocalizedString(30474), dialog_text)  
            return       
        media.playCount(title, vurl, vseason, vepisode, \
        pcount, vseries, mtype, contenturl)              # Mezzmo Playcount
    elif (cselect[vcontext]) == menuitem7:               # Mezzmo Clear Bookmark
        if utilities.checkItemChange(cselect[vcontext], addon.getLocalizedString(30472)) < 1:
            return
        rtrimpos = contenturl.rfind('/')
        kobjectID = contenturl[rtrimpos+1:]              # Get Kodi objectID
        rtrimpos = vurl.rfind('/')
        mobjectID = vurl[rtrimpos+1:]                    # Get Mezzmo objectID
        #xbmc.log('Mezzmo bookmark info is: ' + str(mobjectID) + ' ' + str(contenturl), xbmc.LOGINFO)
        bookmark.SetBookmark(contenturl, mobjectID, '0')
        bookmark.updateKodiBookmark(kobjectID, '0', mtitle, mtype)
        media.nativeNotify()                             # Kodi native notification
        mgenlog ='Mezzmo Kodi bookmark cleared for: ' + title
        xbmc.log(mgenlog, xbmc.LOGINFO)
        mgenlog = '###' + mtitle
        media.mgenlogUpdate(mgenlog)   
        mgenlog ='Mezzmo Kodi bookmark cleared for: '
        media.mgenlogUpdate(mgenlog)           
    elif (cselect[vcontext]) == menuitem5:               # Mezzmo GUI
        autourl = media.settings('autostart')
        if len(autourl) > 6: 
            media.autostart()
        else:
            xbmc.executebuiltin('RunAddon(%s)' % ("plugin.video.mezzmo"))
    elif (cselect[vcontext]) == menuitem6:               # Mezzmo Search
        xbmc.executebuiltin('Dialog.Close(all)')
        xbmc.executebuiltin('RunAddon(%s, %s)' % ("plugin.video.mezzmo", "contentdirectory=" + contenturl + \
        ';mode=search;source=native'))
    elif (cselect[vcontext]) == menuitem8:               # Mezzmo movie sets
        xbmc.executebuiltin('RunAddon(%s, %s)' % ("plugin.video.mezzmo", "contentdirectory=" + contenturl + \
        ';mode=movieset;source=native;searchset=' + movieset))        
    elif (cselect[vcontext]) == menuitem9 or (cselect[vcontext]) == menuitem10 : # Mezzmo display collections          
        xbmc.executebuiltin('RunAddon(%s, %s)' % ("plugin.video.mezzmo", "contentdirectory=" + contenturl + \
        ';mode=collection;source=native;searchset=' + collection)) 
    elif (cselect[vcontext]) == menuitem11:              # Mezzmo display keywords  
        utilities.selectKeywords(mtype, menuitem11, 'native', contenturl)   


def getPlayCount(mtitle, mtype):                         # Get playcount for selected listitem

    pcount = -1
    mseason = mepisode = 0
    mseries = murl = mset = myear = ''

    dbfile = media.openKodiDB()
    musicvid = media.settings('musicvid')                # Check if musicvideo sync is enabled
    if mtype == 'musicvideo' and musicvid == 'true':     # Find musicvideo file number
        curpc = dbfile.execute('select playCount, c13 from musicvideo_view where C00=?', (mtitle,)) 
        pcursor = curpc.fetchone()                       # Is title a musicvideo ?   
        if pcursor:
            pcount =  pcursor[0]
            murl = pcursor[1]  
        curpc.close()
    elif mtype == 'episode':                             # Find TV Episode file number 
        curpc = dbfile.execute('select playCount, c18, c12, c13, strTitle from episode_view   \
        where C00=?', (mtitle,))                         # Is title an episode ?
        pcursor = curpc.fetchone()
        if pcursor:
            pcount =  pcursor[0]
            murl = pcursor[1]
            mseason = pcursor[2]
            mepisode = pcursor[3]
            mseries = pcursor[4] 
        curpc.close()  
    else:
        curpc = dbfile.execute('select playCount, c22, strSet, premiered from movie_view where \
        C00=?', (mtitle,)) 
        pcursor = curpc.fetchone()                      # Is title a movie ?   
        if pcursor:
            pcount =  pcursor[0]
            murl = pcursor[1]
            myear = pcursor[3][:4]
            if pcursor[2] != None:                      # Movie set information
                mset = pcursor[2]
            else:
                mset = 'Unknown Album' 
        curpc.close()

    dbfile.close()

    return [mtitle, murl, mseason, mepisode, pcount, mseries, mset, myear]    


if __name__ == '__main__':
    contextMenu()



