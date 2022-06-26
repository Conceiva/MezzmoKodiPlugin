import xbmc
import xbmcgui
import xbmcplugin
import os
import xbmcaddon
import media
import sys
import bookmark

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
    minfo = sys.listitem.getVideoInfoTag()
    mtitle = minfo.getTitle()
    trcount = media.settings('trcount')
    contenturl = media.settings('contenturl')
    icon = sys.listitem.getArt('poster')   

    titleinfo = getPlayCount(mtitle)                     # Get info for title
    title = titleinfo[0]
    vurl = titleinfo[1]
    vseason = titleinfo[2]
    vepisode = titleinfo[3]    
    pcount = titleinfo[4]
    vseries = titleinfo[5] 
    xbmc.log('Mezzmo titleinfo is: ' + str(titleinfo), xbmc.LOGDEBUG)


    pdfile = media.openNosyncDB()                        # Open Trailer database
    cselect = []
    curpt = pdfile.execute('SELECT count (trUrl) FROM mTrailers WHERE trTitle=?', (title,))
    tcontext = curpt.fetchone()                          # Get trailer count from database
    pdfile.close()

    pdfile = media.openKodiDB()                          # Open Kodi DB
    curpt = pdfile.execute('SELECT idBookmark FROM bookmark INNER JOIN episode_view USING     \
    (idFile) WHERE episode_view.c00=?', (mtitle,))
    bcontext = curpt.fetchone()                          # Get bookmark from database
    if not bcontext:
        curpt = pdfile.execute('SELECT idBookmark FROM bookmark INNER JOIN movie_view USING  \
        (idFile) WHERE movie_view.c00=?', (mtitle,))
        bcontext = curpt.fetchone()                      # Get bookmark from database
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

    if bcontext:                                         # If bookmark exists
        cselect.append(menuitem7)

    cselect.append(menuitem2)                            # Logs & Stats
    cselect.append(menuitem6)                            # Mezzmo Search
    cselect.append(menuitem5)                            # Mezzmo Addon Gui
    ddialog = xbmcgui.Dialog()    
    vcontext = ddialog.select('Select Mezzmo Feature', cselect)

    if vcontext < 0:                                     # User cancel
        return      
    elif (cselect[vcontext]) == menuitem1:               # Mezzmo trailers
        xbmc.executebuiltin('RunScript(%s, %s, %s, %s, %s)' % ("plugin.video.mezzmo", "trailer",  \
        title, trcount, icon ))
    elif (cselect[vcontext]) == menuitem2:               # Mezzmo Logs & stats
        xbmc.executebuiltin('RunScript(%s, %s)' % ("plugin.video.mezzmo", "performance"))
    elif (cselect[vcontext]) == menuitem3 or (cselect[vcontext]) == menuitem4: 
        if not vurl:
            pcdialog = xbmcgui.Dialog()
            dialog_text = "Unable to modify the playcount.  Selected item URL is missing."        
            pcdialog.ok("Mezzmo Addon Playcount Error", dialog_text)  
            return       
        media.playCount(title, vurl, vseason, vepisode, \
        pcount, vseries, 'video', contenturl)            # Mezzmo Playcount
    elif (cselect[vcontext]) == menuitem7:               # Mezzmo Clear Bookmark
        rtrimpos = contenturl.rfind('/')
        kobjectID = contenturl[rtrimpos+1:]              # Get Kodi objectID
        rtrimpos = vurl.rfind('/')
        mobjectID = vurl[rtrimpos+1:]                    # Get Mezzmo objectID
        #xbmc.log('Mezzmo bookmark info is: ' + str(mobjectID) + ' ' + str(contenturl), xbmc.LOGINFO)
        bookmark.SetBookmark(contenturl, mobjectID, '0')
        bookmark.updateKodiBookmark(kobjectID, '0', mtitle)
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
        mezzmostart = 'plugin://plugin.video.mezzmo/?contentdirectory=' + contenturl + ';mode=search'
        xbmc.executebuiltin('ActivateWindow(%s, %s)' % ('10025', mezzmostart))


def getPlayCount(mtitle):                                # Get playcount for selected listitem

    pcount = -1
    mseason = mepisode = 0
    mseries = murl = ''
    dbfile = media.openKodiDB()
    curpc = dbfile.execute('select playCount, c22 from movie_view where C00=?', (mtitle,)) 
    pcursor = curpc.fetchone()                                      # Is title a movie ?   
    if pcursor:
        pcount =  pcursor[0]
        murl = pcursor[1]       
    if pcount == -1:
        curpc = dbfile.execute('select playCount, c18, c12, c13, strTitle from episode_view   \
        where C00=?', (mtitle,))                                    # Is title an episode ?
        pcursor = curpc.fetchone()
        if pcursor:
            pcount =  pcursor[0]
            murl = pcursor[1]
            mseason = pcursor[2]
            mepisode = pcursor[3]
            mseries = pcursor[4]   

    pcursor = curpc.fetchone()   
    dbfile.close()
    del pcursor
    return [mtitle, murl, mseason, mepisode, pcount, mseries]    


if __name__ == '__main__':
    contextMenu()


