v1.1.5.2

-  Fixed bug introduced in v1.1.4.8 which was causing invalid handle errors
   in the Kodi logs and improper displaying of uPNP servers after a Refresh.

v1.1.5.1

-  Added CSV export capability for Kodi and Mezzmo addon databases.
-  Modified Logs & Stats GUI reporting limit to the 2,000 most recent records.
   Older records can be access via the new CSV export utility.
-  Added inserting the Mezzmo audio track language field to the Kodi DB 
   streamdetails table.  Previously just the codec type and # of channels
   were inserted. 
-  Fixed improper duration information from Twonky uPNP server impacting 
   displaying music and videos.
-  Fixed artist information from Windows 10 uPNP server.
-  Fixed displaying some audio tracks from Tversity uPNP server.

v1.1.5.0

-  Fixed another bug introduced in v1.1.4.8 which caused metadata updates to 
   changed episodes in Kodi DB to fail due to userrating added to database.

v1.1.4.9

-  Fixed bug introduced in v1.1.4.8 which caused metadata updates to changed
   movies / episodes in Kodi DB to fail due to userrating added to database.

v1.1.4.8

-  Additional metadata for uPNP servers including MPAA rating, playcount,
   user rating, tagline and artwork.
-  Fixed bug where Kodi database manual clearing would fail if uPNP servers
   were displayed. 

v1.1.4.7

-  Additional code cleanup and optimization for the Logs & Stats reporting.
-  Improved metadata for uPNP servers including actors, directors and genre.

v1.1.4.6

- Added context menu item for all pictures to be able to launch Mezzmo addon
  slideshow viewer.
- Fixed slideshow bug introduced in v1.1.4.5.

v1.1.4.4

-  Fixed search function often returning no results due to duration error.
-  Added a GUI notification when browsing a playlist and the server returns
   no results due to it being empty on the server.
-  New feature allows for viewing pictures in a slideshow or individually
   with a normal or extended presentation time.  A View Setting was added to
   allow adjusting the slideshow and picture presentation times.  The 
   slideshow has 3 controls:  Pause, Play / Resume, and Stop. An additional
   View setting was added to enable / disable the slideshow feature.  The 
   default is enabled.
-  Added ability to display pictures regardless of whether the addon is 
   launched in Kodi under Pictures, Videos or Music.
-  Added / restored support for non-Mezzmo uPNP servers.  The addon will now
   detect the model of the uPNP server it is connecting to and will adjust
   capabilities to what the uPNP server will support.  Mezzmo advanced
   functionality like sync, bookmark / playcount sharing and more will only
   work with Mezzmo servers. 
-  Added GUI progress notification during uPNP server discovery so you can
   now see what is happening.
-  Added setting for sync server selection.  This will allow syncing to your
   Mezzmo server while browsing another uPNP server or another Mezzmo server.
   If there is only one Mezzmo server found the addon will automatically make
   it the sync server.  Syncing to multiple Mezzmo servers isn't supported at 
   this time.  
-  Improved uPNP server discovery by adjusting the multicast TTL timer.
-  Improved uPNP server response validation to ignore missing or invalid 
   responses.
-  Created Kodi Mezzmo repository for updates.  Updates will now be automatic
   and available via the Kodi GUI.

v1.1.4.3

-  Added Mezzmo server timeout setting and reorganized all timer settings
   into a common tab.
-  Added prior search history for quick repeat searches with user defined
   setting for number of prior searches to display.
-  Added GUI notification if the Mezzmo server stops responding while 
   performing searches.
-  Added GUI notification if a uPNP server stops responding during addon
   startup. 

v1.1.4.2

-  Additional fixes to detect improper Kodi settings causing exception errors
   in sync process.
-  Changed default setting for syncing Mezzmo TV episodes to the Kodi database
   from disabled to enabled.
-  Added GUI confirmation when clearing the Kodi DB via the addon settings.  
   This will avoid accidental clearing of Mezzmo data in the Kodi database. 
-  Fixed performance logging sometimes recording the selected item instead of 
   the playlist name during folder refreshes, utilizing the Mezzmo mark 
   watched / unwatched function and other similar activities. 
-  Added menu option to clear performance logs.
-  Fixed addon fanart not displaying due to improper file location pointer.
-  Fixed Kodi.log message "default.py has left several classes in memory 
   that we couldn't clean up." when running on LibreElec.
-  Added GUI notification if the Mezzmo server stops responding while browsing
   playlists. 
-  Improved the speed, stability and user friendliness of the Logs & Stats
   reporting.

v1.1.4.1

-  Fixed new Mezzmo addon installation bug where sync process would cause an
   exception error prior to a Mezzmo server being selected. The sync process
   will now skip until a valid Mezzmo server is selected. 

v1.1.4.0

-  Fixed very obscure bug which could cause exception errors till the daily
   sync process ran if the Mezzmo hourly sync process attempted to add a video
   to the Kodi DB at the exact same time Mezzmo was adding the same record
   to its database and had not completed gathering all of the artwork.  

v1.1.3.9

-  Fixed bug which would cause a sync failure if the Mezzmo addon received
   a bad setting value from Kodi.
-  Added All Other view mapping setting to the Confluence skin to match
   the Estuary and Aeon skin views.

v1.1.3.8

-  Fixed bug which would cause sync failures if the Mezzmo TCP port 
   number was less than 10000.
-  Code cleanup and fixing some Mezzmo addon settings error messages
   when running Kodi in debug mode. 

v1.1.3.7

-  Adjusted stopped playback feature introduced in v1.1.2.8 to only work
   with paused Mezzmo playback.  Previously it stopped any paused Kodi 
   audio or video file.

v1.1.3.6

-  Fixed exception bug which could occur if Kodi stopped playing a file 
   at exactly the same time the addon attempted to stop playback.
-  Added setting to allow enabling / disabling the Mezzmo addon from 
   managing Kodi views.
-  Added workaround for Kodi Leila bug breaking view mapping.
   ***  Note this fix may not work on Kodi running on some platforms *** 

v1.1.3.5

-  Added check to ensue proper audio codec information is received from
   Mezzmo before inserting video into the Kodi database.
-  Added log entry to indicate whether the new autosync feature introduced
   in v1.1.3.4 is enabled or disabled.
-  Updated the addon.xml and language file formats to align to the newer
   Kodi addon standards.

v1.1.3.4

-  New autosync feature which will adjust background sync process based
   upon sync % between Kodi and Mezzmo.  If < 90% sync the sync process 
   will be changed to Normal and once > 90% it will be moved back to 
   Newest.  The default for this feature is disabled and it will not work
   if the sync setting is Off.

v1.1.3.3

-  Additional improvements with logs into the Mezzmo statistics & Logs 
   interface and reporting including now showing all uPNP servers known
   by the Mezzmo addon.
-  Added the ability to tune the background sync process.  There are now
   4 options:  Off, Daily, Newest and Normal.  Off and Normal are the same
   On / Off options from previous versions.  Daily only runs the daily full
   sync process and no hourly sync.  Newest only checks for new Mezzmo 
   videos each hour and then a full daily sync.  Newest is sufficient for 
   most instances where a lot of changes are not taking place to existing 
   videos and Mezzmo information.  Normal is the default setting.  
-  Standardized how addon settings are written and retrieved from Kodi. This
   eliminated an issue where settings values were sometimes changing if you 
   didn't retstart Kodi after making a change.

v1.1.3.2

-  Updated and simplified Mezzmo duplicate checking algorithm.  It is now
   accurate and consistent across all platforms and versions of Kodi.
-  Improved and streamlined Mezzmo statistics & Logs interface
-  Added remaining Mezzmo addon general logs to Mezzmo stats & logs 
   interface. 
 
v1.1.3.1

-  Improved Mezzmo duplicate video detection across all platforms and moved
   reporting from the Kodi.log file to the addon database and they are now
   available via the addon context menu GUI.  Previously a number of duplicate
   videos were not being detected due to the vast differences between Kodi 
   18 & 19 and all of the different client environments.
-  Improved performance statistics viewing by fixing missing playlist data,
   adding new views by playlist and all.  Changed retention period to 500
   performance records instead of 14 days.  Improved view formatting and 
   added date field.  Fixed issues with GoUp and Refresh actions causing
   incomplete playlist information.
-  Added viewing of Mezzmo addon sync logs via the context menu GUI.  

v1.1.3.0

-  Added dialog boxes asking to confirm clearing the autostart setting and
   providing the playlist name when you set the addon to autostart.  These
   will prevent accidentally clearing the autostart setting by simply 
   clicking on the context menu and ensures the autostart setting is set
   to the correct playlist you have selected.
-  Updated the performance statistics to be available via the GUI for 14
   days vs. previously just writing a log message to the Kodi.log file.  
   The statistics can help you see the performance of your Mezzmo server 
   and Kodi device as you browse playlists.  Statistics are only written to 
   the database if the playlist has 50 or more items.  Smaller playlists
   generally will not have any performance concerns.  

v1.1.2.9

-  Fixed issue with intermittient failures when upgrading the addon. 
   Cause was service.py file not properly detecting Kodi force shutting
   down the addon to do the upgrade.    

v1.1.2.8

-  Added dialog box response when no matching search results are found
   on the Mezzmo server when performing a search.  Previously an empty
   playlist was presented.
-  Added new setting which you can select between 0 - 60 minutes to 
   stop a paused playback.  0 means never stop a paused playback.  This
   feature is useful if you walk away for a length of time and forget to
   stop something you are watching.  The bookmark will be set so you can
   resume watching where you left off.   

v1.1.2.7

-  Added displaying bookmark position to music / audio information
   screen.
-  Added new functionality Mezzmo Mark Watched context menu option 
   for music / audio files which will update the Mezzmo database 
   when clicked. This is the same feature which exists for video 
   files except the Kodi database isn't updated since audio files
   currently don't sync between the Mezzmo and Kodi databases.   

v1.1.2.6

-  Fixed Kodi sync % calculation could be greater than 100% if Mezzmo
   records were deleted.
-  Added bookmark feature to music / audio files.  Mezzmo will now
   automatically set the bookmark so you can continue replay from the
   bookmark point like with video files.  This will be helpful for long
   audio / music files like audio books and similar.
   ***  Note this feature requires a Mezzmo update.  Please contact
        Mezzmo support for the update *** 
   
v1.1.2.5

-  Improved fix of contentType errors.  The addon settings now include 
   an All Other Content View setting to handle default contentType
   view mapping vs. v1.1.2.4 which had a hard coded default.
-  Fixed an obscure bug where the sync process could fail if a duplicate
   file was found but it was not fully discovered by Mezzmo and was
   missing information.
-  Added support for a Music Video Mezzmo category type and associated
   Kodi view settings.

v1.1.2.4

-  Major fix of contentType errors impacting many Kodi skins not being 
   able to display content with certain Mezzmo categories including the
   nosync category feature implemented in v1.1.2.2.
  
v1.1.2.3

-  Fixed error condition if the addon tried to start and no Mezzmo servers
   were found or selected.
-  Fixed invalid handle messages in the Kodi logfile when browsing Mezzmo.
-  Added autostart feature to allow you to mark / unmark a folder via the
   context menu.  A folder marked for autostart will cause the addon to
   start the addon automatically and load that folder whenever Kodi is
   restarted.  You no longer need to deal with the various ways Kodi 
   handles autoexec.py or manually determining the path to a folder.  

v1.1.2.2

-  Added a new separate nosync tracking database in Kodi to allow real
   time tracking of nosync and Live Channels not written to the main 
   Kodi database.  The new database name is Mezzmo10.db.  Nosync and
   Live channel log counters will now update with each hourly background 
   sync process.

v1.1.2.1

-  Fixed Kodi DB record count to only count Mezzmo records in the Kodi
   database vs. all Kodi DB records
-  Improved the last played time to include both the date and time vs.
   only the date.
-  Improved the premiered date to include both the date and year vs.
   only the year.
 - Added syncing the Mezzmo date_added field to the Kodi database so
   that the native Kodi interface will match Mezzmo.  
   ***  Note this feature requires a Mezzmo update.  Please contact
        Mezzmo support for the update *** 

v1.1.2.0

-  Added Kodi DB nosync feature.  Adding a category named "nosync" to
   a video file will keep it from being added to the Kodi database. 
-  Improved sync logging to show total number of Live Channels and 
   nosync videos along with the overall Mezzmo / Kodi sync percentage. 

v1.1.1.9

-  Added a setting to enable performance logging on playlists with
   50 or more items.  The total time to load a playlist, the playlist
   items per second and the Mezzmo server response time will all be
   logged to the Kodi logfile.  Automatically disabled after the daily
   sync to avoid bloating the Kodi logfile.

v1.1.1.8

-  Adjusted bookmark sync timer from 1 minute to every 30 seconds
-  Removed unused code introduced in v1.1.1.6 .

v1.1.1.7

-  Fixed bookmarks not being reset when end of file playback reached.
-  Added bookmark delay adjustment to allow starting up to 30 seconds
   behind from when playback was stopped.
-  Added saving bookmark to Mezzmo once a minute during playback

v1.1.1.6

-  Improved Kodi logging when a video is playing.  The log will now
   show the movie / episode title which is playing vs. the raw uPNP
   file name.
-  Removed some duplicate code used for opening the Kodi database.
-  Added logging during daily sync when a TV episode is missing a
   series name in Mezzmo.
-  Fixed issue where marked playcount feature would fail on movie
   titles with nonASCII characters. 

v1.1.1.5

-  Minor performance improvement by streamlining and simplifying code
-  Added detection for Live Channel temporary files from HDHomeRun 
   OTA software found by Mezzmo and no longer syncs them to the Kodi 
   database.  A message in the Kodi.log file will indicate how many
   were found during the sync process.

v1.1.1.4

-  Added ability to select different view sort options when displaying
   Mezzmo playlists.

v1.1.1.3

-  Fixed an issue where the addon could go into a loop if there was
   a mismatch with the number of items it was attempting to retrieve 
   from Mezzmo.

v1.1.1.2

-  Added feature to allow remapping of the Top and Folder content
   types in the Estuary skin to movies or episodes to allow more 
   view types for folders.
-  Synchronized the Estuary view options in the addon with the latest
   Estuary skin views.
-  Added last played metadata view in the music information panel.   

v1.1.1.1

-  Added music mediatype variable to allow Kodi to display full Mezzmo
   music metadata.
-  Added music metadata to music information context menu item.
-  Added MusicInfo view to Confluence skin settings to improve viewing 
   of music files.

v1.1.1.0

-  Added feature to allow remapping of the Top and Folder content
   types in the AEON Nox skins to movies or episodes to allow 
   more view types for folders.  

v1.1.0.9

-  Synchronized view settings with Aeon Nox Silvo skin.  

v1.1.0.8

-  Fixed major speed issue with the Mark Watched function which 
   caused slow loading of playlists due to the insertion order of 
   context and list items.  This was especially noticeable on the 
   Vero 4K+ platform running Kodi on OSMC with large playlists.  
   The issue was less noticeable on other platforms.

v1.1.0.7

-  Improved code added in v1.1.0.0 to handle commas with Mark Watched 
   feature.  The new code is simpler and faster on some ARM platforms.

v1.1.0.6

-  Added Mezzmo duplicate logging feature which will log any duplicate 
   Mezzmo records found during the daily sync process into the Kodi 
   log file.
-  Fixed issue where if you tried to exit / start Kodi while the daily
   sync was running an exception error would occur due to a Kodi database
   locking contention.

v1.1.0.5

-  Added fast sync feature which allows larger Mezzmo databases to 
   process more hourly records reducing the time to cycle through the
   Mezzmo database between daily syncs. 

v1.1.0.4

-  Added feature where if the daily sync process isn't able to run at 
   the scheduled time due to a video playing or Kodi not running it 
   will keep trying each hour until 6AM.
-  Fixed sync problem introduced in v1.1.0.1 where not all Mezzmo 
   records would be scanned and imported into Kodi  with the 
   background sync process.   

v1.1.0.3

-  Added saving sync offset counter to addon settings so that it will
   not restart at the beginning when the addon is shutdown.
-  Fixed Kodi addon error message in the logs when Mark Watched feature
   is used.

v1.1.0.2

-  Fixed issue where unexpected response from Mezzmo server could cause 
   background sync process to abort.
-  Decoupled Mark Watched Mezzmo and Kodi updates so that if a video isn't
   found in the Kodi database the Mezzmo database will still be updated. 
-  Added logging to show number of records in the Mezzmo database during sync.   
-  Added feature to clear Mezzmo bookmark when Mezzmo Mark Unwatched is
   clicked on a video file. 

v1.1.0.1

-  Fixed issue with Kodi 18 running on ARM devices (i.e. Raspberry Pi etc..) 
   not syncing all records between Mezzmo and Kodi.  Back ported the Kodi 19
   addon sync code to this release to resolve.  Kodi 18 and Kodi 19 addon 
   sync code is now standardized.

v1.1.0.0

-  Fixed Mezzmo Mark Watched feature not working on video files with a comma 
   in the title or the series name.
-  Fixed Mezzmo Mark watched feature not working when a video was not found 
   in the Kodi database.
-  Added last played time copy from Mezzmo to the Kodi database.

v1.0.9.9

-  Fixed daily sync scan counter from double counting the last 20 records
   in Mezzmo.
-  Added new functionality Mezzmo Mark Watched conext menu option which will
   update both the Kodi and Mezzmo databases when clicked.  

             ***  Important notes ***

-  Mezzmo version 6.0.5.0t patch or higher is required for Mezzmo Mark Watched
   new capability.   Please request from support@conceiva.com 
-  Kodi and Mezzmo databases need to be in sync for this to operate.  The 
   background sync process should enforce this but if this feature doesn't 
   operate properly please check the Kodi logs.

v1.0.9.8

-  Fixed a bug where TV episodes might be duplicated in the Kodi database
   when a client switches between DNS and IP addresses in the path table.
-  Updated movie dupe checking introduced in v1.0.9.7 to match the new 
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

v1.0.9.7

-  Fixed issue where Kodi sync setting was only being read when the addon 
   starts vs. right after a setting change.
-  Added database cleanup functions on Kodi shutdown.
-  Addressed potential minor memory leak by explicitly closing database
   cursors. 
-  Fixed a bug where a movie may not get inserted into the Kodi database
   due to a path conflict between a path using DNS vs. the IP address
-  Cleaned up some class deletion error messages in the Kodi logfile when
   running on the Android OS.
-  Improved sync detection and added log messages when the addon enables
   and disables real time updates automatically.

v1.0.9.6

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

v1.0.9.5

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
 
v1.0.9.4

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

v1.0.9.3

-  Fixed 2 bugs found in streamdetails change detection and title checking
   during bulk Mezzmo/Kodi sync testing which would cause Kodi not to be 
   updated with Mezzmo data when browsing playlists and would abort the 
   upcoming Mezzmo / Kodi sync process feature. 
-  Updated TV Episode dupe checking to match on series name, season and 
   episode.  This eliminates duplicates in the Kodi database due to episode
   naming and display title differences across playlists.

v1.0.9.2

-  Fixed bug introduced in v1.0.9.1 which would cause invalid metadata
   changes to be detected in TV episodes.  The only impacts were a slight
   slowness loading large TV episode playlists and erroneous Kodi log
   messages stating that a metadata change was detected.

v1.0.9.1

-  Fixed issue with Kodi database cache clearing where not all records
   in the cache table associated with Mezzmo were being deleted.
-  Improved handling of TV Episodes in the Kodi database so that they
   now appear as TV episodes vs. movies, with the proper season, episode
   and similar information when an actor search is performed.
   *** If the Add TV Episodes option has previously been enabled a 
   Kodi database clear on startup is required to repopulate with 
   the proper tags.  *** 

v1.0.9.0

-  Improved database queries to support other Kodi addons populating
   the Kodi database with movies having the exact same names as 
   Mezzmo movies.  The addon will now only query and update Mezzmo
   generated movies and media files in the Kodi database.  
-  Fixed issue introduced in v1.0.7.8 where not all Mezzmo records 
   were being deleted with a Kodi ClearDB on some Linux clients which
   populate the path table with a mix of IP address and DNS based entries
   or if the Mezzmo server IP addressed changed.
-  Fixed issue with 1.0.8.9 where the TV Show name is now only added 
   when browsing TV shows.  This resolves issue with some movies 
   showing unknown titles in the Info/Details panel.
-  Updated actor and artwork change updates to differentiate between
   movies and TV show episodes.  This is the first step in handling
   TV show episodes better in future addon versions.
-  Automatically re-enable image caching after cache clear to improve 
   performance and reduce Mezzmo server overhead.

v1.0.8.9

-  Added TV series name display when browsing TV show episode details.

v1.0.8.8

-  Added Mezzmo sort title support into the Kodi database.  Now actor searches will
   honor the sort titles.  No database clear is required.  Sort titles will be added
   as you browse playlists.
  
   ***  Note Mezzmo version 6.0.5.0o is required to leverage this function ***
   You will need to E-mail support@conceiva.com to request the patch. 

v1.0.8.7

-  Added studio information from Mezzmo to Kodi database and movie information panel.

v1.0.8.6

-  Fixed issue where playlists wouldn't load completely if there was an invalid file
   in Mezzmo.  Invalid files will now be skipped and not displayed in Kodi nor will
   they be inserted into the Kodi database.  A popup dialog will alert on invalid files.

v1.0.8.5

-  Additional significant database improvements when adding playlists to the Kodi
   database.  Moved from a database commit per item to a commit per playlist fetch
   from Mezzmo.

v1.0.8.4

-  Significant database speed improvement (>75%) by reducing the number of times 
   the addon opens and closes the Kodi database.
-  Added user ratings from Mezzmo to movie search panel.
-  Fixed logging error which could cause a playlist not to load completely if Kodi
   was in debug mode and a playlist item was missing the icon variable from Mezzmo. 

v1.0.8.3

-  Changed movie title name matching to case insensitive to avoid duplicate movies
   in the Kodi database.

v1.0.8.2

-  Fixed bug which would cause some movies not to be displayed during a addon
   Search action due to a UTF-8 encoding issue.
-  Added cast order function to actor search so the actor order in Kodi matches
   the order in Mezzmo.  Previously stars would appear in random order in the 
   actor search panel.
-  Added fanart to the Kodi database for movies.  Previously all 4 artwork types
   had the same image.
   *** The cast and fanart changes require a one time Kodi DB clear to add new data 
   elements to the Kodi database.  Otherwise they will only be added to new movies 
   which are discovered. *** 

v1.0.8.1

-  Added check to ensure all artwork entries are in the Kodi database.  If not, 
   they are added automatically.  This resolves issue in v1.0.7.9 where a 
   Kodi DB clear was needed to add missing artwork entries.
-  Changed file extension change checking method to use pathnumber vs. parsing file
   extensions.  Kodi 18 and 19 versions of the addon are now back in sync.  

v1.0.8.0

-  Fixed issue where artwork URL file names might be missing or have duplicate
   file extensions depending upon which platform Kodi is running. This could cause
   missing artwork for some movies.  A Kodi DB clear on startup is needed to 
   remove any incorrect file names in the Kodi database.

v1.0.7.9

-  Fixed issue where movie thumbnails were not updating properly for certain 
   skins when doing an actor search. A Kodi DB clear on startup is needed to
   populate missing thumbnails in the Kodi database.

v1.0.7.8

-  Fixed Kodi DB clear on startup to only delete Mezzmo data in the Kodi 
   database vs. deleting all data in prior versions. 

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
