import xbmc
import xbmcgui
import xbmcplugin
import os
import xbmcaddon
import media
import sys
import bookmark
import utilities

#xbmc.log('Name of script: ' + str(sys.argv[0]), xbmc.LOGNOTICE)
#xbmc.log('Number of arguments: ' + str(len(sys.argv)), xbmc.LOGNOTICE)
#xbmc.log('The arguments are: ' + str(sys.argv), xbmc.LOGNOTICE)


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
    minfo = sys.listitem.getVideoInfoTag()
    mtitle = minfo.getTitle()
    mtype = minfo.getMediaType()
    dbid = minfo.getDbId()
    ttitle = mtitle.decode('utf-8','ignore')
    trcount = media.settings('trcount')
    contenturl = media.settings('contenturl')
    icon = sys.listitem.getArt('poster')   

    xbmc.executebuiltin('Dialog.Close(all, true)')
    titleinfo = getPlayCount(ttitle, mtype)               # Get info for title
    title = titleinfo[0]
    vurl = titleinfo[1]
    vseason = titleinfo[2]
    vepisode = titleinfo[3]    
    pcount = titleinfo[4]
    vseries = titleinfo[5]
    movieset = titleinfo[6]  
    xbmc.log('Mezzmo titleinfo is: ' + str(titleinfo), xbmc.LOGDEBUG)
    #xbmc.log('Mezzmo mediatype is: ' + str(mtype), xbmc.LOGNOTICE)

    pdfile = media.openNosyncDB()                        # Open Trailer database
    cselect = []
    collection = 'none'
    curpt = pdfile.execute('SELECT count (trUrl) FROM mTrailers WHERE trTitle=?', (ttitle,))
    tcontext = curpt.fetchone()                          # Get trailer count from database
    pdfile.close()

    pdfile = media.openKodiDB()                          # Open Kodi DB
    musicvid = media.settings('musicvid')                # Check if musicvideo sync is enabled
    if mtype == 'musicvideo' and musicvid == 'true':     # Find musicvideo bookmark
        curpt = pdfile.execute('SELECT idBookmark FROM bookmark INNER JOIN musicvideo_view USING  \
        (idFile) WHERE musicvideo_view.c00=?', (mtitle,))
        bcontext = curpt.fetchone()                      # Get bookmark from database
        curpc = pdfile.execute('SELECT name FROM tag INNER JOIN tag_link USING (tag_id) WHERE   \
        media_id=? and media_type=?', (dbid, 'musicvideo',))
        tcollection = curpc.fetchall()                   # Get tags for collections
        if tcollection:
            collection = checkNativeTags(tcollection, mtitle)
        else:
            collection = 'none' 
    elif mtype == 'episode':                             # Find episode bookmark
        curpt = pdfile.execute('SELECT idBookmark FROM bookmark INNER JOIN episode_view USING     \
        (idFile) WHERE episode_view.c00=?', (mtitle,))
        bcontext = curpt.fetchone()                      # Get bookmark from database
    else:
        curpt = pdfile.execute('SELECT idBookmark FROM bookmark INNER JOIN movie_view USING       \
        (idFile) WHERE movie_view.c00=?', (mtitle,))
        bcontext = curpt.fetchone()                      # Get bookmark from database
        curpc = pdfile.execute('SELECT name FROM tag INNER JOIN tag_link USING (tag_id) WHERE   \
        media_id=? and media_type=?', (dbid, 'movie',))
        tcollection = curpc.fetchall()                   # Get tags for collections
        if tcollection:
            collection = checkNativeTags(tcollection, mtitle)
        else:
            collection = 'none' 
    pdfile.close()

    if pcount == None:                                   # Kodi playcount is null
        cselect.append(menuitem3)
        pcount = 0
    elif pcount == 0:                                    # Kodi playcount is 0
        cselect.append(menuitem3)
    elif pcount > 0:
        cselect.append(menuitem4)           

    if tcontext[0] > 0 and int(trcount) > 0:             # If trailers for movie and enabled
        cselect.append(menuitem1)

    if movieset != 'Unknown Album' and mtype == 'movie': # If movieset and type is movie
        cselect.append(menuitem8)

    if collection != 'none' and mtype == 'movie':        # If collection tag and type is movie
        cselect.append(menuitem9) 

    if collection != 'none' and mtype == 'musicvideo':   # If collection tag and type is musicv
        cselect.append(menuitem10)    
    
    if bcontext:                                         # If bookmark exists
        cselect.append(menuitem7)

    cselect.append(menuitem2)                            # Logs & Stats
    cselect.append(menuitem6)                            # Mezzmo Search
    cselect.append(menuitem5)                            # Mezzmo Addon Gui
    ddialog = xbmcgui.Dialog()    
    vcontext = ddialog.select('Select Mezzmo Feature', cselect)

    if vcontext < 0:                                     # User cancel
        xbmc.executebuiltin('Dialog.Close(all, true)')
        return      
    elif (cselect[vcontext]) == menuitem1:               # Mezzmo trailers
        utilities.trDisplay(title, trcount, icon)
    elif (cselect[vcontext]) == menuitem2:               # Mezzmo Logs & stats
        utilities.displayMenu()
    elif (cselect[vcontext]) == menuitem3 or (cselect[vcontext]) == menuitem4:
        if not vurl:
            pcdialog = xbmcgui.Dialog()
            dialog_text = "Unable to modify the playcount.  Selected item URL is missing."        
            pcdialog.ok("Mezzmo Addon Playcount Error", dialog_text)  
            return       
        media.playCount(mtitle, vurl, vseason, vepisode, \
        pcount, vseries, mtype, contenturl)              # Mezzmo Playcount
    elif (cselect[vcontext]) == menuitem7:               # Mezzmo Clear Bookmark
        rtrimpos = contenturl.rfind('/')
        kobjectID = contenturl[rtrimpos+1:]              # Get Kodi objectID
        rtrimpos = vurl.rfind('/')
        mobjectID = vurl[rtrimpos+1:]                    # Get Mezzmo objectID
        #xbmc.log('Mezzmo bookmark info is: ' + str(mobjectID) + ' ' + str(contenturl), xbmc.LOGNOTICE)
        bookmark.SetBookmark(contenturl, mobjectID, '0')
        bookmark.updateKodiBookmark(kobjectID, '0', ttitle, mtype)
        media.nativeNotify()                              # Kodi native notification
        mgenlog ='Mezzmo Kodi bookmark cleared for: ' + title.encode('utf-8', 'ignore')
        xbmc.log(mgenlog, xbmc.LOGNOTICE)
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


def checkNativeTags(taglist, mtitle):                 #  Looks for collections in taglist

    try:
        if len(taglist) == 0:
            return 'none'
        else:
            xbmc.log('Mezzmo taglist is: ' + str(taglist), xbmc.LOGDEBUG)
            for tag in range(len(taglist)):
                if '###' in taglist[tag][0]:
                    return taglist[tag][0].strip()
            return 'none'    

    except:
        mgenlog ='Mezzmo problem parsing native collection tags for: ' + mtitle.encode('utf-8', 'ignore')
        xbmc.log(mgenlog, xbmc.LOGNOTICE)
        media.mgenlogUpdate(mgenlog)
        return 'none'


def getPlayCount(mtitle, mtype):                         # Get playcount for selected listitem

    pcount = -1
    mseason = mepisode = 0
    mseries = murl = mset = ''

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
        curpc = dbfile.execute('select playCount, c22, strSet from movie_view where C00=?', (mtitle,)) 
        pcursor = curpc.fetchone()                      # Is title a movie ?   
        if pcursor:
            pcount =  pcursor[0]
            murl = pcursor[1]
            if pcursor[2] != None:                      # Movie set information
                mset = pcursor[2]
            else:
                mset = 'Unknown Album' 
        curpc.close()

    dbfile.close()

    return [mtitle, murl, mseason, mepisode, pcount, mseries, mset]   


if __name__ == '__main__':
    contextMenu()



