import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import media

#xbmc.log('Name of script: ' + str(sys.argv[0]), xbmc.LOGNOTICE)
#xbmc.log('Number of arguments: ' + str(len(sys.argv)), xbmc.LOGNOTICE)
#xbmc.log('The arguments are: ' + str(sys.argv), xbmc.LOGNOTICE)

def content_mapping(contentType):               # Remap for skins which have limied Top / Folder views
    current_skin_name = xbmc.getSkinDir()
    if current_skin_name == 'skin.aeon.nox.5' or current_skin_name == 'skin.aeon.nox.silvo':
        aeonfoldermap = media.settings('aeoncontentmap')
        if aeonfoldermap != 'Default':
            contentType = aeonfoldermap.lower()

    if current_skin_name == 'skin.estuary':
        estuaryfoldermap = media.settings('estuarycontentmap')
        if estuaryfoldermap != 'Default':
            contentType = estuaryfoldermap.lower()
 
    return(contentType)     
    
def setViewMode(contentType):

    if media.settings('viewmap')  == 'false':	#  Mezzmo view mapping is disabled
        return
    current_skin_name = xbmc.getSkinDir()
    #xbmc.log('The content type is ' + contentType, xbmc.LOGNOTICE)
    #xbmc.log('The current skin name is ' + current_skin_name, xbmc.LOGNOTICE)
    if current_skin_name == 'skin.aeon.nox.5' or current_skin_name == 'skin.aeon.nox.silvo':
        aeon_nox_views = { 'List'   : 50  ,
                       'InfoWall'   : 51  ,
                       'Landscape'  : 52  ,
                       'ShowCase1'  : 53  ,
                       'ShowCase2'  : 54  ,
                       'TriPanel'   : 55  ,
                       'Posters'    : 56  ,
                       'Shift'      : 57  ,
                       'BannerWall' : 58  ,
                       'Logo'       : 59  ,
                       'Icons'      : 500 ,
                       'LowList'    : 501 ,
                       'Episode'    : 502 ,
                       'Wall'       : 503 ,
                       'Gallery'    : 504 ,
                       'Panel'      : 505 ,
                       'RightList'  : 506 ,
                       'BigList'    : 507 ,
                       'SongList'   : 508 ,
                       'MyFlix'     : 509 ,
                       'BigFan'     : 591 ,
                       'BannerPlex' : 601 ,
                       'FanartList' : 602 ,
                       'Music_JukeBox'   : 603,
                       'Fullscreen_Wall' : 609, }
        
        view_mode = media.settings(contentType + '_view_mode' + '_aeon')
        if view_mode != 'Default':
            selected_mode = aeon_nox_views[view_mode]
            xbmc.executebuiltin('Container.SetViewMode(' + str(selected_mode) + ')')
            xbmc.executebuiltin('Container.SetViewMode(' + str(selected_mode) + ')')
            
    elif current_skin_name == 'skin.aeon.madnox':
        aeon_nox_views = { 'List'       : 50  ,
                       'InfoWall'   : 51  ,
                       'Landscape'  : 503  ,
                       'ShowCase1'  : 501  ,
                       'ShowCase2'  : 501  ,
                       'TriPanel'   : 52  ,
                       'Posters'    : 510  ,
                       'Shift'      : 57  ,
                       'BannerWall' : 508  ,
                       'Logo'       : 59  ,
                       'Wall'       : 500 ,
                       'LowList'    : 501 ,
                       'Episode'    : 514 ,
                       'Wall'       : 500 ,
                       'BigList'    : 510 }
        
        view_mode = media.settings(contentType + '_view_mode' + '_aeon')
        if view_mode != 'Default':
            selected_mode = aeon_nox_views[view_mode]
            xbmc.executebuiltin('Container.SetViewMode(' + str(selected_mode) + ')')
            xbmc.executebuiltin('Container.SetViewMode(' + str(selected_mode) + ')')
        
    elif current_skin_name == 'skin.estuary':
        estuary_views = { 'List'       : 50  ,
                       'Posters'    : 51  ,
                       'IconWall'   : 52  ,
                       'Shift'      : 53  ,
                       'InfoWall'   : 54  ,
                       'WideList'   : 55  ,
                       'Wall'       : 500 ,
                       'Banner'     : 501 ,
                       'FanArt'     : 502 }
        
        view_mode = media.settings(contentType + '_view_mode' + '_estuary')
        if view_mode != 'Default':      
            selected_mode = estuary_views[view_mode]          
            xbmc.executebuiltin('Container.SetViewMode(' + str(selected_mode) + ')')
            xbmc.executebuiltin('Container.SetViewMode(' + str(selected_mode) + ')')

    elif media.settings(contentType + '_view_mode') != "0":
       try:
           if media.settings(contentType + '_view_mode') == "1":   # List
               xbmc.executebuiltin('Container.SetViewMode(502)')
               xbmc.executebuiltin('Container.SetViewMode(502)')
           elif media.settings(contentType + '_view_mode') == "2": # Big List
               xbmc.executebuiltin('Container.SetViewMode(51)')
               xbmc.executebuiltin('Container.SetViewMode(51)')
           elif media.settings(contentType + '_view_mode') == "3": # Thumbnails
               xbmc.executebuiltin('Container.SetViewMode(500)')
               xbmc.executebuiltin('Container.SetViewMode(500)')
           elif media.settings(contentType + '_view_mode') == "4": # Poster Wrap
               xbmc.executebuiltin('Container.SetViewMode(501)')
               xbmc.executebuiltin('Container.SetViewMode(501)')
           elif media.settings(contentType + '_view_mode') == "5": # Fanart
               xbmc.executebuiltin('Container.SetViewMode(508)')
               xbmc.executebuiltin('Container.SetViewMode(508)')
           elif media.settings(contentType + '_view_mode') == "6":  # Media info
               xbmc.executebuiltin('Container.SetViewMode(504)')
               xbmc.executebuiltin('Container.SetViewMode(504)')
           elif media.settings(contentType + '_view_mode') == "7": # Media info 2
               xbmc.executebuiltin('Container.SetViewMode(503)')
               xbmc.executebuiltin('Container.SetViewMode(503)')
           elif media.settings(contentType + '_view_mode') == "8": # Media info 3
               xbmc.executebuiltin('Container.SetViewMode(515)')
               xbmc.executebuiltin('Container.SetViewMode(515)')
           elif media.settings(contentType + '_view_mode') == "9": # Music info
               xbmc.executebuiltin('Container.SetViewMode(506)')
               xbmc.executebuiltin('Container.SetViewMode(506)')    
       except:
           xbmc.log("SetViewMode Failed: "+media.settings('_view_mode'))
           xbmc.log("Skin: "+xbmc.getSkinDir())