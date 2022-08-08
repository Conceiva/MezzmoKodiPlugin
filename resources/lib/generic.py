import sys
import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmcvfs
import urllib.request, urllib.error, urllib.parse
import xml.etree.ElementTree
import re
import xml.etree.ElementTree as ET
import browse
import xbmc
import sys
import json
import os
import media
import sync
import time
from server import getItemlUrl, upnpCheck, picDisplay
from server import clearPictures, updatePictures

addon = xbmcaddon.Addon()
base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
argmod = sys.argv[2][1:].replace(';','&')    #  Handle change in urllib parsing to default to &
args = urllib.parse.parse_qs(argmod)

addon_path = addon.getAddonInfo("path")
addon_icon = addon_path + '/resources/icon.png'
addon_fanart = addon_path + '/resources/fanart.jpg'

logcount = 0
gsrvrtime = int(media.settings('gsrvrtime'))
if not gsrvrtime:
    gsrvrtime = 60
generic_response = int(media.settings('generic_response'))
if generic_response > 0:
    logcount = int(media.settings('genrespcount'))
    
def build_url(query):
    return base_url + '?' + urllib.parse.urlencode(query)


def content_mapping(contentType):               # Remap for skins which have limited Top / Folder views
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
    #xbmc.log('The content type is ' + contentType, xbmc.LOGINFO)
    #xbmc.log('The current skin name is ' + current_skin_name, xbmc.LOGINFO)    
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
            
    elif current_skin_name == 'skin.aeon.madnox':
        aeon_nox_views = { 'List'   : 50  ,
                       'InfoWall'   : 51  ,
                       'Landscape'  : 503 ,
                       'ShowCase1'  : 501 ,
                       'ShowCase2'  : 501 ,
                       'TriPanel'   : 52  ,
                       'Posters'    : 510 ,
                       'Shift'      : 57  ,
                       'BannerWall' : 508 ,
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
        
    elif current_skin_name == 'skin.estuary':
        estuary_views = { 'List'    : 50  ,
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

    elif media.settings(contentType + '_view_mode') != "0":
       try:
           if media.settings(contentType + '_view_mode') == "1": # List
               xbmc.executebuiltin('Container.SetViewMode(502)')
           elif media.settings(contentType + '_view_mode') == "2": # Big List
               xbmc.executebuiltin('Container.SetViewMode(51)')
           elif media.settings(contentType + '_view_mode') == "3": # Thumbnails
               xbmc.executebuiltin('Container.SetViewMode(500)')
           elif media.settings(contentType + '_view_mode') == "4": # Poster Wrap
               xbmc.executebuiltin('Container.SetViewMode(501)')
           elif media.settings(contentType + '_view_mode') == "5": # Fanart
               xbmc.executebuiltin('Container.SetViewMode(508)')
           elif media.settings(contentType + '_view_mode') == "6":  # Media info
               xbmc.executebuiltin('Container.SetViewMode(504)')
           elif media.settings(contentType + '_view_mode') == "7": # Media info 2
               xbmc.executebuiltin('Container.SetViewMode(503)')
           elif media.settings(contentType + '_view_mode') == "8": # Media info 3
               xbmc.executebuiltin('Container.SetViewMode(515)')
           elif media.settings(contentType + '_view_mode') == "9": # Music info
               xbmc.executebuiltin('Container.SetViewMode(506)')    
       except:
           xbmc.log("SetViewMode Failed: "+media.settings('_view_mode'))
           xbmc.log("Skin: "+xbmc.getSkinDir())


def ghandleBrowse(content, contenturl, objectID, parentID):
    contentType = 'movies'
    itemsleft = -1
    pitemsleft = -1
    media.settings('contenturl', contenturl)
    slideshow = media.settings('slideshow')             # Check if slideshow is enabled   
    menuitem1 = addon.getLocalizedString(30347)
    menuitem2 = addon.getLocalizedString(30346)
    menuitem3 = addon.getLocalizedString(30372)
    menuitem4 = addon.getLocalizedString(30373)
    menuitem5 = addon.getLocalizedString(30379)
    menuitem6 = addon.getLocalizedString(30380)
    menuitem7 = addon.getLocalizedString(30384)
    menuitem8 = addon.getLocalizedString(30412)
    sync.deleteTexturesCache(contenturl)                # Call function to delete textures cache if user enabled.  
    #xbmc.log('Kodi version: ' + installed_version, xbmc.LOGINFO)
    try:
        while True:
            e = xml.etree.ElementTree.fromstring(content)
            
            body = e.find('.//{http://schemas.xmlsoap.org/soap/envelope/}Body')
            browseresponse = body.find('.//{urn:schemas-upnp-org:service:ContentDirectory:1}BrowseResponse')
            result = browseresponse.find('Result')
            NumberReturned = browseresponse.find('NumberReturned').text
            TotalMatches = browseresponse.find('TotalMatches').text
            
            if int(NumberReturned) == 0:
                dialog_text = media.translate(30421) + '\n' + xbmc.getInfoLabel("ListItem.Label")
                xbmcgui.Dialog().ok(media.translate(30424), dialog_text)
                xbmc.executebuiltin('Action(ParentDir)')
                break; #sanity check
                
            if itemsleft == -1:
                itemsleft = int(TotalMatches)
            
            #elems = xml.etree.ElementTree.fromstring(result.text.encode('utf-8'))
            elems = xml.etree.ElementTree.fromstring(result.text)
            picnotify = 0               
            for container in elems.findall('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}container'):
                title = container.find('.//{http://purl.org/dc/elements/1.1/}title').text 
                containerid = container.get('id')
                
                description_text = ''
                description = container.find('.//{urn:schemas-upnp-org:metadata-1-0/upnp/}longDescription')
                if description != None and description.text != None:
                    description_text = description.text
    
                icon = container.find('.//{urn:schemas-upnp-org:metadata-1-0/upnp/}albumArtURI')
                if icon != None:
                    icon = icon.text
                    if (icon[-4:]) !=  '.jpg': 
                        icon = icon + '.jpg'
                        xbmc.log('Handle browse initial icon is: ' + icon, xbmc.LOGDEBUG)    

                itemurl = build_url({'mode': 'server', 'parentID': objectID, 'objectID': containerid,             \
                'contentdirectory': contenturl})        
                li = xbmcgui.ListItem(title)
                li.setArt({'banner': icon, 'poster': icon, 'icon': icon, 'fanart': addon_fanart})

                mediaClass_text = 'video'
                info = {
                        'plot': description_text,
                }
                li.setInfo(mediaClass_text, info)
                    
                searchargs = urllib.parse.urlencode({'mode': 'search', 'contentdirectory': contenturl,        \
                'objectID': containerid})

                li.addContextMenuItems([ (menuitem1, 'Container.Refresh'), (menuitem2, 'Action(ParentDir)') ])                 
                xbmcplugin.addDirectoryItem(handle=addon_handle, url=itemurl, listitem=li, isFolder=True)
                picnotify += 1
                if parentID == '0':
                    contentType = 'top'
                else:
                    contentType = 'folders'
                contentType = content_mapping(contentType)

            piclist = []
            clearPictures() 
            upnpnotify = 0  
            for item in elems.findall('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}item'):
                title = item.find('.//{http://purl.org/dc/elements/1.1/}title').text
                itemid = item.get('id')
                icon = None
                albumartUri = item.find('.//{urn:schemas-upnp-org:metadata-1-0/upnp/}albumArtURI')
                if albumartUri != None:
                    icon = albumartUri.text
                    if (icon[-4:]) !=  '.jpg': 
                        icon = icon + '.jpg'
                        xbmc.log('Handle browse second icon is: ' + icon, xbmc.LOGDEBUG)    

                res = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}res')
                subtitleurl = None
                duration_text = ''
                video_width = 0
                video_height = 0
                aspect = 0.0
                validf = 0
                protocol_text = ''

                if res != None:
                    itemurl = res.text
                    #xbmc.log('The current URL is: ' + itemurl, xbmc.LOGINFO)
                    subtitleurl = res.get('{http://www.pv.com/pvns/}subtitleFileUri')            
                    duration_text = res.get('duration')
                    if duration_text == None:
                        duration_text = '00:00:00.000'
                    elif len(duration_text) < 9:          #  Check for proper duration Twonky
                        duration_text = duration_text + '.000'           
                    elif int(duration_text[len(duration_text)-3:len(duration_text)]) != 0:  
                        duration_text = duration_text[:6] + '.000'    
                    #xbmc.log('The duration is: ' + str(duration_text), xbmc.LOGINFO)  
                    resolution_text = res.get('resolution')
                    if resolution_text != None:
                        mid = resolution_text.find('x')
                        video_width = int(resolution_text[0:mid])
                        video_height = int(resolution_text[mid + 1:])
                        aspect = float(float(video_width) / float(video_height))
                    protocol = res.get('protocolInfo')
                    if protocol != None:
                        protocol_text = protocol
                    #xbmc.log('The protocol is: ' + str(protocol), xbmc.LOGINFO) 
                else:
                    duration_text = '00:00:00.000'
                    itemurl = getItemlUrl(contenturl, itemid)
                    if upnpnotify == 0:      # Do not repeat notification
                        upnpCheck()          # Check Kodi service uPNP setting                    
                    upnpnotify = 1
                    if itemurl == 'None':
                        dialog_text = media.translate(30393)
                        xbmcgui.Dialog().ok(media.translate(30406), dialog_text)
                        xbmc.executebuiltin('Action(ParentDir)')             
                        break

                backdropurl = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}cvabackdrop')
                if backdropurl != None:
                    backdropurl = backdropurl.text
                    if (backdropurl [-4:]) !=  '.jpg': 
                        backdropurl  = backdropurl  + '.jpg'

                poster = ''
                thumb = ''
                res2 = item.findall('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}res')
                for protocol in res2:
                    protocolinfo = protocol.attrib["protocolInfo"]
                    if 'poster' in protocolinfo:
                        poster = protocol.text
                    if 'thumb' in protocolinfo:
                        thumb = protocol.text
                    if 'fanart' in protocolinfo and backdropurl == None:
                        backdropurl = protocol.text
                    if 'icon' in protocolinfo and icon == None:
                        icon = protocol.text     

                upnpclass_text = ''
                upnpclass = item.find('.//{urn:schemas-upnp-org:metadata-1-0/upnp/}class')
                if upnpclass != None:
                    upnpclass_text = upnpclass.text
                    #xbmc.log('The class is: ' + str(upnpclass_text), xbmc.LOGINFO)  

                li = xbmcgui.ListItem(title)
                li.setArt({'thumb': icon, 'poster': icon, 'icon': icon, 'fanart': backdropurl})
                if subtitleurl != None:
                    li.setSubtitles([subtitleurl])
                  
                trailerurl = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}trailer')
                if len(thumb) > 0 and len(poster) > 0:
                    li.setArt({'thumb': thumb, 'poster': poster, 'icon': icon, 'fanart': backdropurl})
                else:
                    li.setArt({'thumb': icon, 'poster': icon, 'icon': icon, 'fanart': backdropurl})
                
                genre_text = []
                for genre in item.findall('.//{urn:schemas-upnp-org:metadata-1-0/upnp/}genre'):
                    if genre != None:
                        genre_text.append(genre.text)              
                #xbmc.log('Mezzmo genre list is: ' + str(genre_text), xbmc.LOGINFO)
                    
                aired_text = ''
                aired = item.find('.//{http://purl.org/dc/elements/1.1/}date')
                if aired != None:
                    aired_text = aired.text
                  
                album_text = ''
                album = item.find('.//{urn:schemas-upnp-org:metadata-1-0/upnp/}album')
                if album != None:
                    album_text = album.text
                  
                release_year_text = ''
                release_year = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}release_year')
                if release_year != None:
                    release_year_text = release_year.text

                release_date_text = ''
                release_date = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}release_date')
                if release_date != None:
                    release_date_text = release_date.text
                
                description_text = ''
                description = item.find('.//{urn:schemas-upnp-org:metadata-1-0/upnp/}longDescription')
                if description != None and description.text != None:
                    description_text = description.text
                      
                imageSearchUrl = ''
                imageSearchUrl = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}imageSearchUrl')
                if imageSearchUrl != None:
                    imageSearchUrl = imageSearchUrl.text
                   
                artist_text = ''
                artist = item.find('.//{urn:schemas-upnp-org:metadata-1-0/upnp/}artist')
                if artist != None:
                    artist_text = artist.text

                actor_list = ''
                cast_dict = []    # Added cast & thumbnail display from Mezzmo server
                cast_dict_keys = ['name','thumbnail']
                actors = item.find('.//{urn:schemas-upnp-org:metadata-1-0/upnp/}artist')
                #xbmc.log('Mezzmo actor list is: ' + str(actors.text), xbmc.LOGINFO) 
                if actors != None and imageSearchUrl != None:
                    #xbmc.log('Mezzmo actor list is: ' + actors.text.encode('utf-8'), xbmc.LOGINFO)  
                    actor_list = actors.text.replace(', Jr.' , ' Jr.').replace(', Sr.' , ' Sr.').split(',')
                    for a in actor_list:                  
                        actorSearchUrl = imageSearchUrl + "?imagesearch=" + a.lstrip().replace(" ","+")
                        #xbmc.log('search URL: ' + actorSearchUrl, xbmc.LOGINFO)  # uncomment for thumbnail debugging
                        new_record = [ a.strip() , actorSearchUrl]
                        cast_dict.append(dict(list(zip(cast_dict_keys, new_record))))
                elif actors == None:
                    actor_list = []
                    for actor in item.findall('.//{urn:schemas-upnp-org:metadata-1-0/upnp/}actor'):
                        if actor != None:
                            actor_list.append(actor.text)
                    artist_text = actor_list                
                    #xbmc.log('Mezzmo actor list is: ' + str(actor_list), xbmc.LOGINFO)

                if isinstance(artist_text, str):            # Sanity check for missing artists
                    artist_text = ["Unknown artist"]  

                creator_text = ''
                creator = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}creator')
                if creator != None:
                    creator_text = creator.text
                else:
                    creator = item.find('.//{http://purl.org/dc/elements/1.1/}creator')
                    if creator != None:
                        creator_text = creator.text

                director_text = ''
                director = item.find('.//{urn:schemas-upnp-org:metadata-1-0/upnp/}director')
                if director != None:
                    creator_text = director.text

                date_added_text = ''                
                date_added = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}date_added')
                if date_added != None:
                    date_added_text = date_added.text
                else:                                                  # Kodi uPNP 
                    date_added = item.find('.//{urn:schemas-xbmc-org:metadata-1-0/}dateadded')
                    if date_added != None:
                        date_added_text = date_added.text
                   
                tagline_text = ''
                tagline = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}tag_line')
                if tagline != None:
                    tagline_text = tagline.text
                else:                                                 # Kodi uPNP
                    tagline = item.find('.//{http://purl.org/dc/elements/1.1/}description')
                    if tagline != None:
                        tagline_text = tagline.text
                    
                categories_text = 'movie'
                categories = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}categories')
                if categories != None and categories.text != None:
                    categories_text = categories.text.split(',')[0]   #  Kodi can only handle 1 media type
                    if categories_text[:7].lower() == 'tv show':
                        categories_text = 'episode'
                        contentType = 'episodes'
                    elif categories_text[:5].lower() == 'movie':
                        categories_text = 'movie'
                        contentType = 'movies'
                        album_text = ''
                    elif categories_text[:11].lower() == 'music video':
                        categories_text = 'musicvideo'
                        contentType = 'musicvideos'
                        album_text = ''
                    else:
                        categories_text = 'video'
                        contentType = 'videos'
                        album_text = ''
                        
                episode_text = ''
                episode = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}episode')
                if episode != None:
                    episode_text = episode.text
                 
                season_text = ''
                season = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}season')
                if season != None:
                    season_text = season.text
                 
                playcount = 0
                playcount_text = ''
                playcountElem = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}playcount')            
                if playcountElem != None:
                    playcount_text = playcountElem.text
                    playcount = int(playcount_text)

                playcountElem = item.find('.//{urn:schemas-upnp-org:metadata-1-0/upnp/}playbackCount')               
                if playcountElem != None:                              # Kodi uPNP
                    playcount_text = playcountElem.text
                    playcount = int(playcount_text)
                 
                last_played_text = ''
                last_played = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}last_played')
                if last_played != None:
                    last_played_text = last_played.text

                last_played_text = ''                                 # Kodi uPNP
                last_played = item.find('.//{urn:schemas-upnp-org:metadata-1-0/upnp/}lastPlaybackTime')
                if last_played != None:
                    last_played_text = last_played.text
                        
                writer_text = ''
                writer = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}writers')
                if writer != None:
                    writer_text = writer.text

                writer_text = ''                                      # Kodi uPNP
                writer = item.find('.//{urn:schemas-upnp-org:metadata-1-0/upnp/}author')
                if writer != None:
                    writer_text = writer.text
                       
                content_rating_text = ''
                content_rating = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}content_rating')
                if content_rating != None:
                    content_rating_text = content_rating.text

                content_rating_text = ''                              # Kodi uPNP
                content_rating = item.find('.//{urn:schemas-upnp-org:metadata-1-0/upnp/}rating')
                if content_rating != None:
                    content_rating_text = content_rating.text
              
                imdb_text = ''
                imdb = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}imdb_id')
                if imdb != None:
                    imdb_text = imdb.text
                
                
                dcmInfo_text = '0'
                dcmInfo = item.find('.//{http://www.sec.co.kr/}dcmInfo')
                if dcmInfo != None:
                    dcmInfo_text = dcmInfo.text
                    valPos = dcmInfo_text.find('BM=') + 3
                    dcmInfo_text = dcmInfo_text[valPos:]
              
                rating_val = ''
                rating = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}rating')
                if rating != None:
                    rating_val = rating.text
                    rating_val = float(rating_val) * 2
                    rating_val = str(rating_val) #kodi ratings are out of 10, Mezzmo is out of 5

                rating_val = ''                                        # Kodi uPNP
                rating = item.find('.//{urn:schemas-xbmc-org:metadata-1-0/}userrating')
                if rating != None:
                    rating_val = rating.text
                
                production_company_text = ''
                production_company = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}production_company')
                if production_company != None:
                    production_company_text = production_company.text

                production_company_text = ''
                production_company = item.find('.//{http://purl.org/dc/elements/1.1/}publisher')
                if production_company != None:
                    production_company_text = production_company.text

                sort_title_text = ''
                sort_title = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}sort_title')
                if sort_title != None:
                    sort_title_text = sort_title.text    

                video_codec_text = ''
                video_codec = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}video_codec')
                if video_codec != None:
                    video_codec_text = video_codec.text
                if video_codec_text == 'vc1':     #  adjust for proper Kodi codec display
                    video_codec_text = 'vc-1'
                
                audio_codec_text = ''
                audio_codec = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}audio_codec')
                if audio_codec != None:
                    audio_codec_text = audio_codec.text
                
                audio_channels_text = '0'
                audio_channels = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}audio_channels')
                if audio_channels != None:
                    audio_channels_text = audio_channels.text               
                audio_lang = ''
                audio_streams = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}audio')
                if audio_streams != None:
                    for stream in audio_streams.findall('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}stream'):
                        if stream.get('selected') == 'auto' or stream.get('selected') == 'true':
                            audio_lang = stream.get('lang')
                            break
                     
                subtitle_lang = ''
                captions_streams = item.find('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}captions')
                if captions_streams != None:
                    for stream in captions_streams.findall('.//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}stream'):
                        if stream.get('selected') == 'auto' or stream.get('selected') == 'true':
                            subtitle_lang = stream.get('language')
                            break
                                   
                #mediaClass 
                if 'video' in upnpclass_text or 'video' in protocol_text:
                    mediaClass_text = 'video'
                if 'audio' in upnpclass_text or 'audio' in protocol_text:
                    mediaClass_text = 'music'
                if 'photo' in upnpclass_text or 'image' in protocol_text:
                    mediaClass_text = 'pictures'
                        
                if mediaClass_text == 'video':  
                    li.addContextMenuItems([ (menuitem1, 'Container.Refresh'), (menuitem2, 'Action(ParentDir)') ]) 
               
                    info = {
                        'duration': sync.getSeconds(duration_text),
                        'genre': genre_text,
                        'year': release_year_text,
                        'title': title,
                        'plot': description_text,
                        'director': creator_text,
                        'tagline': tagline_text,
                        'writer': writer_text,
                        'cast': artist_text,
                        'artist': artist_text,
                        'rating': rating_val,
                        'imdbnumber': imdb_text,
                        'mediatype': categories_text,
                        'season': season_text,
                        'episode': episode_text,
                        'lastplayed': last_played_text,
                        'aired': aired_text,
                        'mpaa':content_rating_text,
                        'studio':production_company_text,
                        'playcount':playcount,
                        'trailer':trailerurl,
                        'tvshowtitle':album_text,
                        'dateadded':date_added_text,
                    }
                    li.setInfo(mediaClass_text, info)
                    li.setProperty('ResumeTime', dcmInfo_text)
                    li.setProperty('TotalTime', str(sync.getSeconds(duration_text)))
                    video_info = {
                        'codec': video_codec_text,
                        'aspect': aspect,
                        'width': video_width,
                        'height': video_height,
                    }
                    li.addStreamInfo('video', video_info)
                    li.addStreamInfo('audio', {'codec': audio_codec_text, 'language': audio_lang, 'channels': int(audio_channels_text)})
                    li.addStreamInfo('subtitle', {'language': subtitle_lang})
                             
                elif mediaClass_text == 'music':
                    li.addContextMenuItems([ (menuitem1, 'Container.Refresh'), (menuitem2, 'Action(ParentDir)') ]) 
                    #offsetmenu = 'Resume from ' + time.strftime("%H:%M:%S", time.gmtime(int(dcmInfo_text)))
                    info = {
                        'duration': sync.getSeconds(duration_text),
                        'genre': genre_text,
                        'year': release_year_text,
                        'title': title,
                        'artist': artist_text,
                        'rating': rating_val,
                        'discnumber': season_text,
                        'mediatype': 'song',
                        'tracknumber': episode_text,
                        'album': album_text,
                        'playcount':playcount,
                        'lastplayed': last_played_text,
                    }
                    #mcomment = media.mComment(info, duration_text, offsetmenu[11:])
                    #info.update(comment = mcomment)
                    li.setInfo(mediaClass_text, info)
                    contentType = 'songs'

                elif mediaClass_text == 'pictures':
                    li.addContextMenuItems([ (menuitem1, 'Container.Refresh'), (menuitem2, 'Action(ParentDir)'), \
                    (menuitem8, 'RunScript(%s, %s)' % ("plugin.video.mezzmo", "pictures")) ])    
                    info = {
                        'title': title,
                    }
                    li.setInfo(mediaClass_text, info)
                    contentType = 'files'
                    picnotify += 1
                    itemdict = {
                        'title': title,
                         'url': itemurl,
                    }
                    piclist.append(itemdict)
                    if picnotify == int(NumberReturned):                   # Update picture DB
                        updatePictures(piclist)
                        if slideshow == 'true':                            # Slideshow display prompt
                            picDisplay()
                    itemurl = build_url({'mode': 'picture', 'itemurl': itemurl})  
                xbmcplugin.addDirectoryItem(handle=addon_handle, url=itemurl, listitem=li, isFolder=False)

            itemsleft = itemsleft - int(NumberReturned) - 1
            
            xbmc.log('Mezzmo items left: ' + str(itemsleft), xbmc.LOGDEBUG) 
            if itemsleft <= 0:
                break

            if pitemsleft == itemsleft:    #  Detect items left not incrementing 
                mgenlog ='Mezzmo items not displayed: ' + str(pitemsleft)
                xbmc.log(mgenlog, xbmc.LOGINFO)
                media.mgenlogUpdate(mgenlog)
                break
            else:
                pitemsleft = itemsleft            
                        
            # get the next items
            offset = int(TotalMatches) - itemsleft
            requestedCount = 1000
            if itemsleft < 1000:
                requestedCount = itemsleft

            pin = media.settings('content_pin')
            content = browse.Browse(contenturl, objectID, 'BrowseDirectChildren', offset, requestedCount, pin)        
    except Exception as e:
        media.printexception()
        pass
    setViewMode(contentType)
    if contentType == 'top' or contentType == 'folders':
        contentType = ''
    xbmcplugin.setContent(addon_handle, contentType)
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_DATE)
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_TITLE_IGNORE_THE)
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_GENRE)
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_DURATION)
    xbmcplugin.endOfDirectory(addon_handle)


def gBrowse(url, objectID, flag, startingIndex, requestedCount, pin):
    global logcount      
    headers = {'content-type': 'text/xml', 'accept': '*/*', 'SOAPACTION' : '"urn:schemas-upnp-org:service:ContentDirectory:1#Browse"', 'User-Agent': 'Kodi (Mezzmo Addon)'}
    body = '''<?xml version="1.0"?>
    <s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
  <s:Body>
    <u:Browse xmlns:u="urn:schemas-upnp-org:service:ContentDirectory:1">
     <ObjectID>'''
    body += objectID
    body += '''</ObjectID>
      <BrowseFlag>'''
    body += flag
    body += '''</BrowseFlag>
      <Filter>*,cva_richmetadata,cva_bookmark</Filter>
      <StartingIndex>'''
    body += str(startingIndex)
    body += '''</StartingIndex>
      <RequestedCount>'''
    body += str(requestedCount)
    body += '''</RequestedCount>'''

    body += '''<SortCriteria></SortCriteria>
    </u:Browse>
  </s:Body>
</s:Envelope>'''
    req = urllib.request.Request(url, body.encode('utf-8'), headers)
    response = ''
    try:
        response = urllib.request.urlopen(req, timeout=gsrvrtime).read().decode('utf-8')
        if logcount < generic_response and generic_response > 0:
            xbmc.log(response, xbmc.LOGINFO)
            logcount += 1
            media.settings('genrespcount', str(logcount))
        elif logcount >= generic_response and generic_response > 0:
            media.settings('generic_response', '0')            
            media.settings('genrespcount', '0')
            mgenlog = 'Mezzmo generic server response logging limit.'   
            xbmc.log(mgenlog, xbmc.LOGINFO)
            media.mgenlogUpdate(mgenlog)
    except Exception as e:
        xbmc.log( 'EXCEPTION IN Browse: ' + str(e))
        pass
    #xbmc.log('The current response is: ' + str(response), xbmc.LOGINFO)    
    return response

