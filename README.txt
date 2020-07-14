v1.0.8.9

-  Added TV series name display when browsing TV show episodes.

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
