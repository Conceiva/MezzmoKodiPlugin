v2.0.0.0wa New Beta test release

-  Fixed daily sync scan counter from double counting the last 20 records
   in Mezzmo.
-  Added initial Kodi Mark as Watched and Mark as Unwatched integration with
   the Mezzmo addon.

v2.0.0.0v New Beta release

-  Fixed a bug where TV episodes might be duplicated in the Kodi database
   when a client switches between DNS and IP addresses in the path table.
-  Updated movie dupe checking introduced in v2.0.0.0u to match the new 
   episode dupe checking method.
-  Loosened episode check to allow for the season to equal 0 in the case
   of some TV shows like Good Witch and similar.
-  Added database vacuum command to daily database maintenance to keep
   Kodi database compact.
-  Added daily counter reset which tracks the sync process schedule.
-  Fixed a bug where a very small number of videos weren't being added to
   the Kodi database during the daily sync process due to an offset pointer
   value.  This was only happening with very large Mezzmo databases and 
   they were getting caught by the hourly sync process.

v2.0.0.0u New Beta release

-  Fixed issue where Kodi sync setting was only being read when the addon 
   starts vs. right after a setting change.
-  Added Database cleanup functions on Kodi shutdown.
-  Addressed potential minor memory leak by explicitly closing database
   cursors. 
-  Fixed a bug where a Kodi 18 call was causing the background sync 
   process to crash.  The Kodi 18 code was removed. 
-  Fixed a bug where a movie may not get inserted into the Kodi database
   due to a path conflict between a path using DNS vs. the IP address.
-  Cleaned up some class deletion error messages in the Kodi logfile when
   running on the Android OS.
-  Improved sync detection and added log messages when the addon enables
   and disables real time updates automatically.

v2.0.0.0t New Beta release

-  Fixed issue where sync process could run while a video was playing.
-  Added feature to check on Kodi startup if the database is in sync 
   with Mezzmo and disable real time updating in the Kodi addon options 
   and leverage the background sync process to detect changes. If they
   are not in sync real time updating remains enabled until sync occurs.
-  Added feature to handle certain Kodi Linux clients which alternate
   between IP address and DNS names for artwork and icon URLs.  Previously
   the addon would detect that as a change and update the Kodi database.  
   Now it can handle either format.
-  Added Kodi database reindexing after the daily sync process in order
   to maintain performance.
-  Added Kodi log messages showing the number of Mezzmo records in the Kodi
   database after each hourly sync process.     

v2.0.0.0s New Beta release

-  Major rewrite of the code which adds Mezzmo artwork to the Kodi database.
   2/3rds of the code was eliminated and functionality was added so that 
   the artwork will be updated when a Mezzmo metadata change is detected in
   a video.  Previously only a video codec change would cause the video 
   artwork to be updated.
-  Added background sync feature that syncs Kodi with Mezzmo.  
     - Syncs 400 most recently added Mezzmo videos on Kodi startup
     - Syncs next 800 Mezzmo videos each hour until all videos are added 
       and then loops back through the Mezzmo database looking for new
       videos and metadata changes.
     - Kodi DB clear and resync of all Mezzmo data between midnight and 1AM
     - Automatically disables real time updates after full synchronization 
       and leverages the background sync process to detect changes.  

             ***  Important notes ***

     - Mezzmo version 6.0.5.0r patch is required for sync capability.
       Please request from support@conceiva.com 
     - The sync functionality does not honor Mezzmo playlist sharing 
       permissions and syncs all Mezzmo videos to Kodi regardless of
       playlist permissions.  

v2.0.0.0r New Beta release

-  Added background task feature.  Initial task feature updates the Kodi
   image cache timers for Mezzmo images on startup and every 30 minutes.
   Images which were recently viewed will have their timers reset to check
   for a newer image.  This will eliminate the need to clear the Kodi 
   cache to detect Mezzmo image updates.  Image updates will now be 
   detected automatically.  
-  Improved category mapping logic to allow users to maintain complete
   flexibility with Mezzmo categories that will be mapped into the standard
   Kodi media type categories.  
-  Improved stream details change detection so that it now repairs missing
   Kodi database stream details by resyncing with Mezzmo.  Previously just
   a log message was written into the Kodi.log file.

v2.0.0.0q New Beta release

-  Fixed 3 bugs found in streamdetails change detection and title checking
   during bulk Mezzmo/Kodi sync testing which would cause Kodi not to be 
   updated with Mezzmo data when browsing playlists and would abort the 
   upcoming Mezzmo / Kodi sync process feature. 
-  Updated TV Episode dupe checking to match on series name, season and 
   episode.  This eliminates duplicates in the Kodi database due to episode
   naming and display title differences across playlists.

v2.0.0.0p New Beta release

-  Fixed bug introduced in v2.0.0.0o which would cause invalid metadata
   changes to be detected in TV episodes.  The only impacts were a slight
   slowness loading large TV episode playlists and erroneous Kodi log
   messages stating that a metadata change was detected.

v2.0.0.0o New Beta release

-  Fixed issue with Kodi database cache clearing where not all records
   in the cache table associated with Mezzmo were being deleted.
-  Improved handling of TV Episodes in the Kodi database so that they
   now appear as TV episodes vs. movies, with the proper season, episode
   and similar information when an actor search is performed.
   *** If the Add TV Episodes option has previously been enabled a 
   Kodi database clear on startup is required to repopulate with 
   the proper tags.  *** 

v2.0.0.0n New Beta release

-  Improved database queries to support other Kodi addons populating
   the Kodi database with movies having the exact same names as 
   Mezzmo movies.  The addon will now only query and update Mezzmo
   generated movies and media files in the Kodi database.  
-  Fixed issue introduced in v2.0.0.0b where not all Mezzmo records 
   were being deleted with a Kodi ClearDB on some Linux clients which
   populate the path table with a mix of IP address and DNS based entries
   or if the Mezzmo server IP addressed changed.
-  Fixed issue with v2.0.0.0m where the TV Show name is now only added 
   when browsing TV shows.  This resolves issue with some movies 
   showing unknown titles in the Info/Details panel.
-  Updated actor and artwork change updates to differentiate between
   movies and TV show episodes.  This is the first step in handling
   TV show episodes better in future addon versions.
-  Automatically re-enable image caching after cache clear to improve 
   performance and reduce Mezzmo server overhead.

v2.0.0.0m New beta release

-  Added TV series name display when browsing TV show episode details.

v2.0.0.0l New beta release

-  Added Mezzmo sort title support into the Kodi database.  Now actor searches will
   honor the sort titles.  No database clear is required.  Sort titles will be added
   as you browse playlists.
  
   ***  Note Mezzmo version 6.0.5.0o is required to leverage this function ***
   You will need to E-mail support@conceiva.com to request the patch. 

v2.0.0.0k New beta release

-  Added studio information from Mezzmo to Kodi database and movie information panel.

v2.0.0.0j New beta release

-  Fixed issue where playlists wouldn't load comnpletely if there was an invalid file
   in Mezzmo.  Invalid files will now be skipped and not displayed in Kodi nor will
   they be inserted into the Kodi database.  A popup dialog will alert on invalid files.

v2.0.0.0i New beta release

-  Additional significant database improvements when adding playlists to the Kodi
   database.  Moved from a database commit per item to a commit per playlist fetch
   from Mezzmo.

v2.0.0.0h New beta release

-  Significant database speed improvement (>75%) by reducing the number of times 
   the addon opens and closes the Kodi database.
-  Added user ratings from Mezzmo to movie search panel.
-  Fixed logging error which could cause a playlist not to load completely if Kodi
   was in debug mode and a playlist item was missing the icon variable from Mezzmo. 

v2.0.0.0g  New beta release

-  Changed movie title name matching to case insensitive to avoid duplicate movies
   in the Kodi database.

v2.0.0.0f  New beta release

-  Added cast order function to actor search so the actor order in Kodi matches
   the order in Mezzmo.  Previously stars would appear in random order in the 
   actor search panel.
-  Added fanart to the Kodi database for movies.  Previously all 4 artwork types
   had the same image.
   *** The cast and fanart changes require a one time Kodi DB clear to add new data 
   elements to the Kodi database.  Otherwise they will only be added to new movies 
   which are discovered. *** 

v2.0.0.0e  New beta release

-  Added check to ensure all artwork entries are in the Kodi database.  If not, 
   they are added automatically.  This resolves issue in v2.0.0.0c where a 
   Kodi DB clear was needed to add missing artwork entries.

v2.0.0.0d  New beta release

-  Fixed issue where artwork URL file names might be missing or have duplicate
   file extensions depending upon which platform Kodi is running. This could cause
   missing artwork for some movies.  A Kodi DB clear on startup is needed to 
   remove any incorrect file names in the Kodi database.

v2.0.0.0c  New beta release

-  Fixed issue where movie thumbnails were not updating properly for certain 
   skins when doing an actor search. A Kodi DB clear on startup is needed to
   populate missing thumbnails in the Kodi database.

v2.0.0.0b  New beta release

-  Fixes Kodi DB clear on startup to only delete Mezzmo data in the Kodi 
   database vs. deleting all data in prior versions. 


v2.0.0.0a  New beta release

-  Updated Kodi logging to a new format which will be required after June 30, 2020
   for Kodi 19.
-  Changed file extension change checking method to use pathnumber vs. parsing file
   extensions. Eliminated issue with false positives on change detection with Kodi
   19 and improves addon performance.  

v2.0.0.0

-  Initial Kodi 19 supported release based upon 1.0.7.7 code.  This version is 
   only for Kodi 19 and will not load on Kodi 18.

v1.0.7.7

-  Fixed issue where actor names ending with "Jr." are stored multiple ways in 
   Mezzmo causing some actors to display incorrectly in the addon.  A clear 
   Kodi DB will need to performed to remove Jr. only actors displaying during
   actor searches. 

v1.0.7.6

-  Added detection for Mezzmo artwork only changes.  If just the Mezzmo artwork 
   for a movie is updated it will be now replicated to the Kodi DB.

v1.0.7.5

-  Fixed issue where Mezzmo updated artwork changes associated with file extension
   changes were not being updated in Kodi DB causing blank poster images.
-  Improved Kodi logging for metadata and streamdetail detected changes.

v1.0.7.4

-  Improved performance of playlist loading by reducing the number of Kodi DB SQL
   queries.
-  Cleaned up code readability and Kodi log messages.

v1.0.7.3

-  Detects file name extension changes associated with container changes. Useful
   when converting between file types but codecs and duration do not change.
-  Adds Kodi logfile message when a changed file is detected to help with 
   tracking down database issues and duplicate files.

v1.0.7.2

-  Detects file name / container changes for existing Mezzmo video items.  This
   can help when you might rerip a video file to another format but keep the Mezzmo
   name the same.  

v1.0.7.1

-  Added detection for Mezzmo metadata changes including tagline, rating, genre,
   description, writer and more.  Mezzmo metadata changes now sync to Kodi DB and
   updates all Kodi DB data for a given movie when a Mezzmo change is detected.
-  Added detection for audio codec changes
-  Added user setting to disable Mezzmo change detection to speed up playlist 
   loading on slower devices or if you have a Mezzmo database that doesn't change
   metadata very often.  On slow devices you can enable change detection, sync 
   the latest Mezzmo changes to the Kodi DB and then disable change detection. 
   Default is enabled since most devices aren't impacted by the slight overhead.
   When change detection is disabled new Mezzmo additions still sync to the Kodi DB
   as long as Kodi DB actor information copy is enabled.

v1.0.7.0

-  Added index to improve Kodi DB perrformance which started degrading with
   version 1.0.6.2.  

v1.0.6.9

-  Added support for Mezzmo playcounts to be copied and updated into the Kodi DB 
   and will set the watched flag when the playcount is greater than 0.  Playcounts
   will automatically update from Mezzmo when browsing playlists.  The watched
   flag will be displayed when browsing by actor / actress in the movie info panel.   

v1.0.6.8

-  Supports Mezzmo 6.0.4 functionality to detect duration changes to videos, as
   well as video codec changes for reripping and similar situations.

   ***  Note that the addon will add data to the Kodi DB the first time through
   a Mezzmo playlist after the upgrade.  This will cause the playlist to load 
   slower.  This is a one time update.

v1.0.6.7

-  Resolved issue where actor insertion into Kodi DB would fail if existing movie
   name was changed in Mezzmo.
-  Fixed minor Kodi debugging log message failures with non-ASCII characters

v1.0.6.6

-  Changed clear Kodi DB setting so that once it executes it changes the setting
   automatically to disabled.  It will only run once now if you forget to manually
   disable the setting.
-  User setting for caching of Mezzmo images now clears cached Mezzmo images when you 
   browse or search a playlist vs. when Mezzmo add-on starts.   

v1.0.6.5

-  Fixed issue with quotes and double quotes in actors / actresses names 
   not inserting into Kodi DB.  A clear KodiDB function is needed to learn 
   the missing actors / actresses.  

v1.0.6.4

-  Fixed occasional missing video artwork issue 

v1.0.6.3

-  Added user option to not add TV shows to Kodi database limiting
   actor searches just to movies
-  Changed default setting to enable Kodi DB population from Mezzmo
   now that duplicates and TV shows have been addressed.

v1.0.6.2

-  Eliminated duplicate actor movie displays by searching on 
   movie name instead of filename 
-  Improved artwork matching by eliminating colons (:) in search

v1.0.6.1

-  Performance improvement when scanning folders and playlists
-  Fixed artwork for display titles with %FILECOUNTER% and %YEAR%  

v1.0.6

-  Added population of Kodi database from Mezzmo server.  This
   enables actor searches from the video information window.
*** The default is disabled.  Enabling will allow searching for
   video content based upon actor from the video information window.
   Note that when enabled the first time access to a folder or
   playlist will be much slower as the add-on pulls down data from 
   the Mezzmo server.  Subsequent access to the same folder or playlist
   should be normal speed.  Enabling this feature can improve the 
   overall add-on experience.
-  Added a setting to clear the Kodi database of movie and actor
   information.  The default is disabled.
***  Note this setting will clear all movie and actor data from
   the database not just Mezzmo video data.  This option should 
   be used if things go bad in your Kodi database and you wish 
   to start over.  The add-on will repopulate the Kodi database
   from the Mezzmo server and first time folder / playlist access
   will be slow, as mentioned above.

-  Fixed VC-1 codec display in the video information window
  

v1.0.5

-  Added actor thumbnail image support from Mezzmo server
-  Added user setting for caching control of Mezzmo images 
***  Note the default for image caching is disabled but enabling
   can slightly improve performance and reduce Mezzmo server traffic
   when browsing and searching folders / playlists.  Enabled was 
   the default behavior with prior versions of this add-on. 
   Disabling will clear the Kodi textures caching table of Mezzmo 
   content entries and allow Mezzmo to repopulate.  Disabling this 
   setting can be used when Mezzmo images are updated on your server.

-  Fixed Kodi content type detection to properly display movies vs. 
   TV episodes etc. in the video information window 
-  Fixed media id errors in Kodi debug logs
-  Fixed displaying the trailer button in the video information 
   window when using the search function.    
