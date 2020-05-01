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
