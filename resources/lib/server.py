import xbmc
import xbmcgui
import xbmcplugin
import urllib.request, urllib.error, urllib.parse
import xml.etree.ElementTree
import re
import xml.etree.ElementTree as ET
import xbmcaddon
import ssdp
import json
from media import openNosyncDB, settings, mezlogUpdate, printexception, mgenlogUpdate, translate

addon = xbmcaddon.Addon()
addon_path = addon.getAddonInfo("path")
addon_icon = addon_path + '/resources/icon.png'

def updateServers(url, name, controlurl, manufacturer, model, icon, description, udn):

    svrfile = openNosyncDB()                                     # Open server database
    curps = svrfile.execute('SELECT srvName FROM mServers WHERE controlUrl=?', (controlurl,))
    srvrtuple = curps.fetchone()                                 # Get servers from database
    if not srvrtuple:				                 # If not found add server
        svrfile.execute('INSERT into mServers (srvUrl, srvName, controlUrl, mSync, sManuf, sModel,  \
        sIcon, sDescr, sUdn) values (?, ?, ?, ?, ?, ?, ?, ?, ?)', (url, name, controlurl, 'No',     \
        manufacturer, model, icon, description, udn[5:]))

    svrfile.commit()
    svrfile.close()


def displayServers():

    svrfile = openNosyncDB()                                     # Open server database
    while True:
        servers = ["Refresh"]
        curps = svrfile.execute('SELECT srvName, mSync, sManuf, controlUrl FROM mServers        \
        WHERE sManuf LIKE ?', ('Conceiva%',))
        srvresults = curps.fetchall()                            # Get servers from database
        a = 0
        while a < len(srvresults):
            if srvresults[a][1] == 'Yes':                        # Is sync server ?
                syncserver = srvresults[a][0] + ' - [COLOR blue]Sync Server[/COLOR]'
                servers.append(syncserver)            
            elif srvresults[a][1] == 'No':
                servers.append(srvresults[a][0])                 # Convert rows to list for dialog box
            a += 1
        ddialog = xbmcgui.Dialog()  
        ssync = ddialog.select(translate(30392), servers)
        if ssync < 0:                                            # User cancel
            svrfile.close()
            break
        elif ssync == 0:                                         # Refresh uPNP server list
            clearServers()
            mscount = getServers()
            if mscount == 0:
                msynclog = translate(30399)
                xbmcgui.Dialog().ok(translate(30398), msynclog)
                xbmc.log(msynclog, xbmc.LOGINFO)
                mezlogUpdate(msynclog)
            else:
                msynclog = 'Mezzmo refresh sync servers found: ' +  str(mscount)
                xbmc.log(msynclog, xbmc.LOGINFO)
                mezlogUpdate(msynclog)  
        elif ssync > 0:
            if updateSync(srvresults[ssync - 1][3]) == 0:        # Update sync server from selection
                msynclog ='Mezzmo sync server updated manually: ' +          \
                str(srvresults[ssync - 1][0])
                xbmc.log(msynclog, xbmc.LOGINFO)
                mezlogUpdate(msynclog) 
            
    svrfile.close()
    return


def updateSync(controlurl):                                      # Set sync for Mezzmo server

    try:
        svrfile = openNosyncDB()                                 # Open server database
        svrfile.execute('UPDATE mServers SET mSync=?', ('No',))
        xbmc.log('Mezzmo controlurl is: ' + controlurl, xbmc.LOGDEBUG)    
        svrfile.execute('UPDATE mServers SET mSync=? WHERE controlUrl=?', ('Yes', controlurl,))
        svrfile.commit()
        svrfile.close()
        return 0

    except Exception as e:
        printexception()
        msynclog = 'Mezzmo sync server update error.'
        xbmc.log(msynclog, xbmc.LOGINFO)
        mezlogUpdate(msynclog)
        return 1      


def checkSync():                                                 # Check for Sync server

    svrfile = openNosyncDB()                                     # Open server database    
    curps = svrfile.execute('SELECT controlUrl FROM mServers WHERE mSync=?', ('Yes',))
    srvrtuple = curps.fetchone()                                 # Get server from database
    if srvrtuple:
        syncurl = srvrtuple[0]
    else:
        contenturl = settings('contenturl')                      # Check for content URL
        curpc = svrfile.execute('SELECT srvName, sIcon FROM mServers WHERE controlUrl=?',  \
        (contenturl,))
        srvrtuple = curpc.fetchone()                             # Get server from database
        if srvrtuple:                                            # Auto update if Mezzmo found
            syncurl = contenturl
            sname = srvrtuple[0]
            if updateSync(contenturl) == 0:                      # Update sync server flag
                iconimage = srvrtuple[1]
                msynclog = translate(30400) + str(sname)
                xbmc.log(msynclog, xbmc.LOGINFO)
                mezlogUpdate(msynclog) 
                notify = xbmcgui.Dialog().notification(translate(30401), msynclog, addon_icon, 5000)
        else:                                                    # Sync srver not set yet
            syncurl = 'None'
    svrfile.close()
    return syncurl    


def getServers():                                                # Find uPNP servers

    try:
        timeoutval = float(settings('ssdp_timeout'))
        contenturl = ''
        msgdialogprogress = xbmcgui.DialogProgress()
        dialogmsg = translate(30402)
        dialoghead = translate(30401)
        msgdialogprogress.create(dialoghead, dialogmsg)
        servers = ssdp.discover("urn:schemas-upnp-org:device:MediaServer:1", timeout=timeoutval)     
        srvcount = len(servers)
        addtlmsg = '  ' + str(srvcount) + '  uPNP servers discovered.'
        ddialogmsg = dialogmsg + addtlmsg
        msgdialogprogress.update(50, ddialogmsg)
        xbmc.sleep(1000)

        if srvcount > 0:
            msynclog ='Mezzmo sync server search: ' + str(srvcount) + ' uPNP servers found.'
            xbmc.log(msynclog, xbmc.LOGINFO)
            mezlogUpdate(msynclog)
        else:
            msynclog = translate(30403)
            xbmcgui.Dialog().notification(translate(30401), msynclog, addon_icon, 5000)            
            xbmc.log(msynclog, xbmc.LOGINFO)
            mezlogUpdate(msynclog)
            return 0
        onlyShowMezzmo = False
        a = 0
        mcount = 0                                                # Count of Mezzmo serves found

        for server in servers:
            url = server.location                
            try:
                response = urllib.request.urlopen(url)
                xmlstring = re.sub(' xmlns="[^"]+"', '', response.read().decode(), count=1)
            
                e = xml.etree.ElementTree.fromstring(xmlstring)    
                device = e.find('device')
                friendlyname = device.find('friendlyName').text
                manufacturer = device.find('manufacturer').text
                modelnumber = device.find('modelNumber').text
                udn = device.find('UDN').text
                description = device.find('modelDescription')
                if description != None:
                    description = description.text
                else:
                    description = 'None'    
                serviceList = device.find('serviceList')
                iconList = device.find('iconList')
                iconurl = ''
                isMezzmo = False
            
                if manufacturer != None and manufacturer == 'Conceiva Pty. Ltd.':
                    iconurl = addon_icon   
                    isMezzmo = True
                    mcount += 1
                elif iconList != None:
                    bestWidth = 0
                    for icon in iconList.findall('icon'):
                        mimetype = icon.find('mimetype').text
                        width = icon.find('width').text
                        height = icon.find('height').text
                        width = int(width)
                        if width > bestWidth:
                            bestWidth = width
                            iconurl = icon.find('url').text
                            if iconurl.startswith('/'):
                                end = url.find('/', 8)
                                length = len(url)
                            
                                iconurl = url[:end-length] + iconurl
                            else:
                                end = url.rfind('/')
                                length = len(url)
                            
                                iconurl = url[:end-length] + '/' + iconurl
                else:
                    iconurl = addon_path + '/resources/media/otherserver.png'        
            
                if isMezzmo or onlyShowMezzmo == False:
                    contenturl = ''
                    for service in serviceList.findall('service'):
                        serviceId = service.find('serviceId')
                    
                        if serviceId.text == 'urn:upnp-org:serviceId:ContentDirectory':
                            contenturl = service.find('controlURL').text
                            if contenturl.startswith('/'):
                                end = url.find('/', 8)
                                length = len(url)                            
                                contenturl = url[:end-length] + contenturl
                            elif 'http' not in contenturl:
                                end = url.rfind('/')
                                length = len(url)                            
                                contenturl = url[:end-length] + '/' + contenturl
                updateServers(url, friendlyname, contenturl, manufacturer, modelnumber,            \
                iconurl, description, udn) 

            except (urllib.error.URLError, urllib.error.HTTPError) :    # Detect Server Issues
                msynclog = 'Mezzmo uPNP server not responding: ' + url
                xbmc.log(msynclog, xbmc.LOGINFO)
                mezlogUpdate(msynclog)  
                dialog_text = translate(30405) + url
                xbmcgui.Dialog().ok(translate(30404), dialog_text)
                pass
            a += 1
            percent = int(a / float(srvcount) * 50) + 50
            dialogmsg = str(a) + ' / ' + str(srvcount) + ' server completed.' 
            msgdialogprogress.update(percent, dialogmsg)
            xbmc.sleep(500)            
        msgdialogprogress.close()
        return mcount        
    except Exception as e:
        printexception()
        msynclog = 'Mezzmo sync server discover error.'
        xbmc.log(msynclog, xbmc.LOGINFO)
        mezlogUpdate(msynclog)
        return 0  


def getItemlUrl(contenturl, itemid):                             # Get itemurl for generic uPNP

    try:
        svrfile = openNosyncDB()                                 # Open server database    
        curps = svrfile.execute('SELECT sUdn FROM mServers WHERE controlUrl=?', (contenturl,))
        srvrtuple = curps.fetchone()                             # Get server from database
        #xbmc.log('Mezzmo getItemUrl:' + str(srvrtuple[0]), xbmc.LOGINFO)        
        if srvrtuple:
            itemurl = ('upnp://' + srvrtuple[0] + '/' + itemid).encode('utf-8','ignore') 
        else:
            itemurl = 'None'    
    except:   
        itemurl = 'None'
        pass
      
    svrfile.close()
    return itemurl 


def upnpCheck():                                                 # Check Kodi uPNP setting

    json_query = xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"Settings.GetSettingValue",       \
    "params":{"setting":"services.upnp"}, "id":1}')
    json_query = json.loads(json_query)
    upnp_enabled = ''
    if 'result' in json_query and 'value' in json_query['result']:
        upnp_enabled  = json_query['result']['value']
    xbmc.log('The uPNP status is: ' + str(upnp_enabled), xbmc.LOGDEBUG)

    if upnp_enabled == True:
        return
    else:
        dialog_text = translate(30394)
        cselect = xbmcgui.Dialog().yesno(translate(30406), dialog_text)
    if cselect == 1 :                                           #  Enable uPNP support in Kodi
        json_query = xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"Settings.SetSettingValue",   \
        "params":{"setting":"services.upnp","value":true}, "id":1}')
        json_query = xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"Settings.GetSettingValue",   \
        "params":{"setting":"services.upnp"}, "id":1}')
        json_query = json.loads(json_query)
        upnp_enabled = ''
        if 'result' in json_query and 'value' in json_query['result']:
            upnp_enabled  = json_query['result']['value']
            if upnp_enabled == True:
                dialog_text = translate(30397)
                xbmcgui.Dialog().ok(translate(30396), dialog_text)
                mgenlog ='Mezzmo Kodi uPNP Set to Enabled.'
                xbmc.log(mgenlog, xbmc.LOGINFO)
                mgenlogUpdate(mgenlog)
            else:        
                dialog_text = translate(30395)
                xbmcgui.Dialog().ok(translate(30396), dialog_text)
                mgenlog ='Mezzmo Kodi uPNP Setting failed.'
                xbmc.log(mgenlog, xbmc.LOGINFO)
                mgenlogUpdate(mgenlog)

            
def clearServers():                                              # Clear server data

    try:
        svrfile = openNosyncDB()                                 # Open server database
        svrfile.execute('DELETE FROM mServers',)  
        svrfile.commit()
        svrfile.close()
        msynclog = 'Mezzmo sync servers cleared.'
        xbmc.log(msynclog, xbmc.LOGINFO)
        mezlogUpdate(msynclog)  

    except Exception as e:
        printexception()
        msynclog = 'Mezzmo sync server clearing error.'
        xbmc.log(msynclog, xbmc.LOGINFO)
        mezlogUpdate(msynclog)   


def clearPictures():                                             # Clear picture data

    try:
        picfile = openNosyncDB()                                 # Open picture database
        picfile.execute('DELETE FROM mPictures',)  
        picfile.commit()
        picfile.close()
        mgenlog = 'Mezzmo picture DB cleared.'
        xbmc.log(mgenlog, xbmc.LOGDEBUG)
        mgenlogUpdate(mgenlog)  

    except Exception as e:
        printexception()
        mgenlog = 'Mezzmo clearing picture error.'
        xbmc.log(mgenlog, xbmc.LOGINFO)
        mgenlogUpdate(mgenlog)   


def updatePictures(piclist):                                     # Update picture DB with list

    try:
        picfile = openNosyncDB()                                 # Open picture DB
        a = 0
        while a < len(piclist):
            title = str(piclist[a]['title'])
            url = str(piclist[a]['url'])
            picfile.execute('INSERT into mPictures (mpTitle, mpUrl) values (?, ?)', (title, url,))
            a += 1     
        picfile.commit()
        picfile.close()

    except Exception as e:
        printexception()
        mgenlog = 'Mezzmo update picture error.'
        xbmc.log(mgenlog, xbmc.LOGINFO)
        mgenlogUpdate(mgenlog)       

    
def getPictures():                                               # Get pictures from DB

    try:
        picfile = openNosyncDB()                                 # Open picture DB
        curps = picfile.execute('SELECT mpTitle, mpUrl FROM mPictures')
        pictuple = curps.fetchall()                              # Get pictures from database
        piclist = []
        a = 0
        while a < len(pictuple):
            itemdict = {
                'title': pictuple[a][0],
                'url': pictuple[a][1],
            }
            piclist.append(itemdict)
            a += 1
        picfile.close()     
        #xbmc.log('Mezzmo piclist dictionary: ' + str(piclist), xbmc.LOGINFO) 
        return(piclist)

    except Exception as e:
        printexception()
        mgenlog = 'Mezzmo get picture error.'
        xbmc.log(mgenlog, xbmc.LOGINFO)
        mgenlogUpdate(mgenlog)  


def getContentURL(contenturl):                                   # Check for manufacturer match

    try:
        rfpos = contenturl.rfind('/',7)
        searchurl = contenturl[:rfpos] + '%' 
        svrfile = openNosyncDB()                                 # Open server database    
        curps = svrfile.execute('SELECT sManuf FROM mServers WHERE controlUrl LIKE ?', (searchurl,))
        srvrtuple = curps.fetchone()                             # Get server from database
        if srvrtuple:
            manufacturer = srvrtuple[0]
        else:
            manufacturer = 'None'

        xbmc.log('Mezzmo manufacturer is: ' + str(manufacturer) , xbmc.LOGDEBUG)
        svrfile.close()
        return manufacturer

    except Exception as e:
        printexception()
        mgenlog = 'Mezzmo content server search error.'
        xbmc.log(mgenlog, xbmc.LOGINFO)
        mgenlogUpdate(mgenlog)   


class KodiMonitor(xbmc.Monitor):                                 # Notification class for monitoring 
                                                                 # slideshow controls
    def __init__(self, *args):
        xbmc.Monitor.__init__(self)
        self.flag = 'play'
        pass

    def onNotification( self, sender, method, data):

        if method == "Player.OnStop":
            self.flag = 'stop'
        if method == "Player.OnPause":
            self.flag = 'pause'
        if method == "Player.OnPlay":
            self.flag = 'play'        


def picURL(itemurl):                                            # Check for proper file extension

    try:
        if itemurl[len(itemurl)-4] == '.':                      # Add .jpg for urllib issue
            newurl = '"' + itemurl + '"'
        else:
            newurl = '"' + itemurl + '.jpg' + '"'        
        xbmc.log('Mezzmo new picture URL: ' + str(newurl) , xbmc.LOGDEBUG)  
        return newurl

    except Exception as e:  
        printexception()
        mgenlog = 'Mezzmo error converting picture URL'
        xbmc.log(mgenlog, xbmc.LOGINFO)
        mgenlogUpdate(mgenlog)   


def picDisplay():                                                # Picture slideshow presenter

    try:
        piclist = getPictures()                                  # Get pictures from picture DB
        slidetime = int(settings('slidetime'))                   # Get slide pause time
        #xbmc.log('Mezzmo picture list: ' + str(piclist) , xbmc.LOGINFO)  
        if 'upnp' in str(piclist[0]['url']):                     # Kodi cannot display pictures over uPNP
            dialog_text = translate(30413)
            xbmcgui.Dialog().ok(translate(30412), dialog_text)
            xbmc.executebuiltin('Action(ParentDir)')
            return
        else:
            cselect = 3
            while cselect >= 0:
                #pictures = ['Slideshow','Pictures Normal Delay']
                pictures = [translate(30417), translate(30418), translate(30419)]
                ddialog = xbmcgui.Dialog() 
                cselect = ddialog.select(translate(30415), pictures)
                if cselect == 1:                                 # User selects pictures normal
                    showPictureMenu(piclist, slidetime)
                    #xbmc.executebuiltin('Action(ParentDir)')
                if cselect == 2:                                 # User selects pictures extended
                    showPictureMenu(piclist, (slidetime * 3))
                    #xbmc.executebuiltin('Action(ParentDir)')
                elif cselect == 0:                               # User selects slideshow
                    ShowSlides(piclist, slidetime)
                elif cselect < 0:
                    #xbmc.executebuiltin('Action(ParentDir)')
                    break
                    #return

    except Exception as e:    
        printexception()
        mgenlog = 'Mezzmo error displaying picture slideshow.'
        xbmc.log(mgenlog, xbmc.LOGINFO)
        mgenlogUpdate(mgenlog)   


def showPictureMenu(piclist, slidetime):                         # Picture viewer and menu

    pselect = 0
    select = 0
    while pselect >= 0:
        try:
            pictures = []
            a = 0
   
            while a < len(piclist):
                pictures.append(piclist[a]['title'])             # Convert rows to list for dialog box
                a += 1     
            ddialog = xbmcgui.Dialog()  
            pselect = ddialog.select(translate(30416), pictures)
            if pselect < 0:                                      # User cancel
                if select > 0:
                    xbmc.executebuiltin('Action(ParentDir)')
                break
            else:                                                # Show picture
                selection = picURL(piclist[pselect]['url'])
                json_query = xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"Player.Open",        \
                "params":{"item":{"file":%s }},"id":1}' % (selection))   
                xbmc.sleep(slidetime * 1000)
                select =+ 1

        except Exception as e:  
            printexception()
            mgenlog = 'Mezzmo error displaying picture.'
            xbmc.log(mgenlog, xbmc.LOGINFO)
            mgenlogUpdate(mgenlog)   


def ShowSlides(piclist, slidetime):                              # Slidehow viewier

    try:    
        kbmonitor = KodiMonitor()                   
        slideIdx = 0   
        #xbmc.log('Mezzmo picture url is: ' + str(playitem) , xbmc.LOGINFO)

        while slideIdx < len(piclist):           
            if kbmonitor.flag == 'play':  
                playitem = picURL(piclist[slideIdx]['url'])      # Verify proper file name
                #xbmc.log('Mezzmo picture index is: ' + str(playitem) , xbmc.LOGINFO)
                json_query = xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"Player.Open",        \
                "params":{"item":{"file":%s }},"id":1}' % (playitem))           
            #xbmc.log('Mezzmo picture dictionary list  is: ' + str(piclist) , xbmc.LOGINFO)
            xbmc.sleep(slidetime * 1000)
            slideIdx += 1
            #xbmc.log('Mezzmo monitor data is: ' + (kbmonitor.flag) , xbmc.LOGINFO)
            if kbmonitor.flag == 'stop':
                del kbmonitor
                return
                break
            if kbmonitor.flag == 'pause':
                slideIdx = slideIdx

        xbmc.executebuiltin('Action(ParentDir)')
        del kbmonitor

    except Exception as e:  
        printexception()
        mgenlog = 'Mezzmo error displaying slides.'
        xbmc.log(mgenlog, xbmc.LOGINFO)
        mgenlogUpdate(mgenlog)       


def showSingle(url):                                             # Display individual native picture

    try:
        if 'upnp' in str(url[0]):                                # Kodi cannot display pictures over uPNP
            dialog_text = translate(30413)
            xbmcgui.Dialog().ok(translate(30406), dialog_text)
            xbmc.executebuiltin('Action(ParentDir)')
            return
        else:
            itemurl = picURL(url[0])
            json_query = xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"Player.Open",        \
            "params":{"item":{"file":%s }},"id":1}' % (itemurl))  

    except Exception as e:    
        printexception()
        mgenlog = 'Mezzmo error displaying single picture.'
        xbmc.log(mgenlog, xbmc.LOGINFO)
        mgenlogUpdate(mgenlog) 