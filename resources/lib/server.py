import xbmc
import xbmcgui
import xbmcplugin
import urllib2
import urllib
import pickle
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
    else:
        svrfile.execute('UPDATE mServers SET sManuf=?, sModel=?, sDescr=? WHERE controlUrl=?',       \
        (manufacturer, model, description, controlurl,)) 

    svrfile.commit()
    svrfile.close()


def displayServers():

    svrfile = openNosyncDB()                                     # Open server database
    while True:
        servers = ["Refresh"]
        curps = svrfile.execute('SELECT srvName, mSync, sManuf, controlUrl FROM mServers           \
        WHERE sManuf LIKE ?', ('Conceiva%',))
        srvresults = curps.fetchall()                            # Get servers from database
        for a in range(len(srvresults)):
            if srvresults[a][1] == 'Yes':                        # Is sync server ?
                syncserver = srvresults[a][0] + ' - [COLOR blue]Sync Server[/COLOR]'
                servers.append(syncserver)            
            elif srvresults[a][1] == 'No':
                servers.append(srvresults[a][0])                 # Convert rows to list for dialog box
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
                xbmc.log(msynclog, xbmc.LOGNOTICE)
                mezlogUpdate(msynclog)
            else:
                msynclog = 'Mezzmo refresh sync servers found: ' +  str(mscount)
                xbmc.log(msynclog, xbmc.LOGNOTICE)
                mezlogUpdate(msynclog)  
        elif ssync > 0:
            if updateSync(srvresults[ssync - 1][3]) == 0:        # Update sync server from selection
                msynclog ='Mezzmo sync server updated manually: ' +                                \
                str(srvresults[ssync - 1][0])
                xbmc.log(msynclog, xbmc.LOGNOTICE)
                mezlogUpdate(msynclog) 
            
    svrfile.close()
    return


def addServers():                                                #  Manually add uPNP servers

    serverdict = [ {'name': 'Mezzmo', 'port': '53168', 'uri': '/desc'},
                   {'name': 'HDHomeRun', 'port': '80', 'uri': '/dms/device.xml'},
                   {'name': 'PlayOn', 'port': '52478', 'uri': '/'},
                   {'name': 'Plex', 'port': '32469', 'uri': '/DeviceDescription.xml'},
                   {'name': 'Tversity', 'port': '41952', 'uri': '/description/fetch'},
                   {'name': 'Twonky', 'port': '9000', 'uri': '/dev0/desc.xml'}  ]

    ipdialog = xbmcgui.Dialog()
    serverip = ipdialog.input(translate(30448), '0.0.0.0', type=xbmcgui.INPUT_IPADDRESS)   
    if len(serverip) == 0 or serverip == '0.0.0.0':             # Return if cancel or bad IP
        return 'None'

    serverlist = []
    for s in range(len(serverdict)):
        serverlist.append(serverdict[s]['name'])                 # Convert dict list to list for dialog box
    #xbmc.log('Mezzmo uPNP server list: ' + str(serverlist), xbmc.LOGNOTICE)
    sdialog = xbmcgui.Dialog()  
    server = sdialog.select(translate(30450), serverlist)
    #xbmc.log('Mezzmo uPNP server selection: ' + str(server), xbmc.LOGNOTICE)

    if server < 0:
        return 'None'
    else:
        sport = sdialog.input(translate(30449), serverdict[server]['port'], type=xbmcgui.INPUT_NUMERIC)

    if len(sport) == 0:
        return 'None'
    else:
        serverurl = 'http://' + str(serverip) + ':' + str(sport) + serverdict[server]['uri']
        xbmc.log('Mezzmo uPNP URL is: ' + str(serverurl), xbmc.LOGDEBUG)
        return serverurl


def delServer(srvurl):                                           # Delete server from server list

    try:
        newlist = []
        saved_servers = settings('saved_servers')
        servers = pickle.loads(saved_servers)        

        xbmc.log('Mezzmo UPnP servers: ' + str(servers).encode('utf-8','ignore'), xbmc.LOGDEBUG)
        
        if len(saved_servers) > 5 and saved_servers != 'none': 
            for server in servers:
                try:
                    url = server.location
                except:
                    url = server.get('serverurl')  
                if srvurl != url:
                    newlist.append(server)                       # Do not delete from newlist              
            settings('saved_servers', pickle.dumps(newlist))
            mgenlog = translate(30466) + srvurl
            xbmc.log(mgenlog, xbmc.LOGNOTICE)
            mgenlogUpdate(mgenlog) 
            xbmcgui.Dialog().notification(translate(30404), mgenlog, addon_icon, 5000)

    except Exception as e:
        printexception()
        mgenlog = 'Mezzmo error deleting UPnP server.'
        xbmc.log(mgenlog, xbmc.LOGNOTICE)
        mgenlogUpdate(mgenlog)


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
        xbmc.log(msynclog, xbmc.LOGNOTICE)
        mezlogUpdate(msynclog)
        return 1      


def checkMezzmo(srvurl):                                         # Check / Update sync sever info

    try:
        response = urllib2.urlopen(srvurl)
        xmlstring = re.sub(' xmlns="[^"]+"', '', response.read(), count=1)
            
        e = xml.etree.ElementTree.fromstring(xmlstring)    
        device = e.find('device')
        friendlyname = device.find('friendlyName').text
        manufacturer = device.find('manufacturer')
        if manufacturer != None:
            manufacturer = manufacturer.text
        else:
            manufacturer = 'None'
        modelnumber = device.find('modelNumber')
        if modelnumber != None:
            modelnumber = modelnumber.text
        else:
            modelnumber = 'None'
        udn = device.find('UDN')
        if udn != None:
            udn = udn.text
        else:
            udn = 'None'
        description = device.find('modelDescription')
        if description != None:
            description = description.text
        else:
            description = 'None'    
        serviceList = device.find('serviceList')
        iconurl = addon_icon

        contenturl = ''
        for service in serviceList.findall('service'):
            serviceId = service.find('serviceId')
                    
            if serviceId.text == 'urn:upnp-org:serviceId:ContentDirectory':
                contenturl = service.find('controlURL').text
                if contenturl.startswith('/'):
                    end = srvurl.find('/', 8)
                    length = len(srvurl)                            
                    contenturl = srvurl[:end-length] + contenturl
                elif 'http' not in contenturl:
                    end = srvurl.rfind('/')
                    length = len(srvurl)                            
                    contenturl = srvurl[:end-length] + '/' + contenturl
        updateServers(srvurl, friendlyname, contenturl, manufacturer, modelnumber,            \
        iconurl, description, udn)
        return modelnumber.strip()

    except urllib2.URLError, urllib2.HTTPError:                  # Detect Server Issues
        msynclog = 'Mezzmo sync server not responding: ' + srvurl
        xbmc.log(msynclog, xbmc.LOGNOTICE)
        mezlogUpdate(msynclog)  
        return '0.0.0.0'

    except Exception as e:
        printexception()
        msynclog = 'Mezzmo sync server check error.'
        xbmc.log(msynclog, xbmc.LOGNOTICE)
        mezlogUpdate(msynclog)
        return '0.0.0.0'


def checkMezzmoVersion():                                        # Returns Mezzmo server version in number form

    try:
        svrfile = openNosyncDB()                                 # Open server database
        curps = svrfile.execute('SELECT sModel FROM mServers WHERE mSync=?', ('Yes',))
        svrtuple = curps.fetchone()                              # Get server from database
        svrfile.close()
        if svrtuple:
            model = svrtuple[0].replace('.','')            
            return model

    except Exception as e:
        printexception()
        msynclog = 'Mezzmo Mezzmo error checking sync server model number or no Mezzmo sync server selected.'
        xbmc.log(msynclog, xbmc.LOGNOTICE)
        mezlogUpdate(msynclog)
        return 0  


def checkSync(count):                                            # Check for Sync server

    svrfile = openNosyncDB()                                     # Open server database    
    curps = svrfile.execute('SELECT controlUrl, srvUrl, srvName FROM mServers WHERE mSync=?', ('Yes',))
    srvrtuple = curps.fetchone()                                 # Get server from database
    if srvrtuple:
        syncurl = srvrtuple[0]
        if count < 12 or count % 3600 == 0:                      # Don't check Mezzmo server on fast sync
            modelnumb = checkMezzmo(srvrtuple[1])
            if modelnumb != '0.0.0.0':
                sname = srvrtuple[2]
                msynclog = 'Mezzmo sync server responded: ' + sname
                xbmc.log(msynclog, xbmc.LOGNOTICE)
                mezlogUpdate(msynclog)
                msynclog = 'Mezzmo sync server version: ' + modelnumb 
                xbmc.log(msynclog, xbmc.LOGNOTICE)
                mezlogUpdate(msynclog)
            else:
                sname = srvrtuple[2]
                msynclog = 'Mezzmo sync server did not respond: ' + sname
                xbmc.log(msynclog, xbmc.LOGNOTICE)
                mezlogUpdate(msynclog)
                syncurl = 'None'   
    else:
        contenturl = settings('contenturl')                      # Check for content URL
        curpc = svrfile.execute('SELECT srvName, sIcon FROM mServers WHERE controlUrl=?',          \
        (contenturl,))
        srvrtuple = curpc.fetchone()                             # Get server from database
        if srvrtuple:                                            # Auto update if Mezzmo found
            syncurl = contenturl
            sname = srvrtuple[0]
            if updateSync(contenturl) == 0:                      # Update sync server flag
                iconimage = srvrtuple[1]
                msynclog ='Mezzmo sync server updated automatically: ' + str(sname)
                xbmc.log(msynclog, xbmc.LOGNOTICE)
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
            xbmc.log(msynclog, xbmc.LOGNOTICE)
            mezlogUpdate(msynclog)
        else:
            msynclog = translate(30403)
            xbmcgui.Dialog().notification(translate(30401), msynclog, addon_icon, 5000)             
            xbmc.log(msynclog, xbmc.LOGNOTICE)
            mezlogUpdate(msynclog)
            return 0
        onlyShowMezzmo = False
        a = 0
        mcount = 0                                                # Count of Mezzmo serves found

        for server in servers:
            url = server.location                
            try:
                response = urllib2.urlopen(url)
                xmlstring = re.sub(' xmlns="[^"]+"', '', response.read(), count=1)
            
                e = xml.etree.ElementTree.fromstring(xmlstring)    
                device = e.find('device')
                friendlyname = device.find('friendlyName').text
                manufacturer = device.find('manufacturer')
                if manufacturer != None:
                    manufacturer = manufacturer.text
                else:
                    manufacturer = 'None'
                modelnumber = device.find('modelNumber')
                if modelnumber != None:
                    modelnumber = modelnumber.text
                else:
                    modelnumber = 'None'
                udn = device.find('UDN')
                if udn != None:
                    udn = udn.text
                else:
                    udn = 'None'
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
                updateServers(url, friendlyname, contenturl, manufacturer, modelnumber,     \
                iconurl, description, udn) 

            except urllib2.URLError, urllib2.HTTPError:        # Detect Server Issues
                msynclog = 'Mezzmo uPNP server not responding: ' + url
                xbmc.log(msynclog, xbmc.LOGNOTICE)
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
        xbmc.log(msynclog, xbmc.LOGNOTICE)
        mezlogUpdate(msynclog)
        return 0  


def getItemlUrl(contenturl, itemid):                             # Get itemurl for generic uPNP

    try:
        svrfile = openNosyncDB()                                 # Open server database    
        curps = svrfile.execute('SELECT sUdn FROM mServers WHERE controlUrl=?', (contenturl,))
        srvrtuple = curps.fetchone()                             # Get server from database
        #xbmc.log('Mezzmo getItemUrl:' + str(srvrtuple[0]), xbmc.LOGNOTICE)        
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
        cselect = xbmcgui.Dialog().yesno("Mezzmo uPNP Playback", dialog_text)
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
                xbmc.log(mgenlog, xbmc.LOGNOTICE)
                mgenlogUpdate(mgenlog)
            else:        
                dialog_text = translate(30395)
                xbmcgui.Dialog().ok(translate(30396), dialog_text)
                mgenlog ='Mezzmo Kodi uPNP Setting failed.'
                xbmc.log(mgenlog, xbmc.LOGNOTICE)
                mgenlogUpdate(mgenlog)


def clearServers():                                              # Clear server data

    try:
        svrfile = openNosyncDB()                                 # Open server database
        svrfile.execute('DELETE FROM mServers',)  
        svrfile.commit()
        svrfile.close()
        msynclog = 'Mezzmo sync servers cleared.'
        xbmc.log(msynclog, xbmc.LOGNOTICE)
        mezlogUpdate(msynclog)  

    except Exception as e:
        printexception()
        msynclog = 'Mezzmo sync server clearing error.'
        xbmc.log(msynclog, xbmc.LOGNOTICE)
        mezlogUpdate(msynclog)   


def clearPictures():                                             # Clear picture data

    try:
        picfile = openNosyncDB()                                 # Open picture database
        picfile.execute('DELETE FROM mPictures',)  
        picfile.commit()
        picfile.close()
        mgenlog = 'Mezzmo picture DB cleared.'
        xbmc.log(mgenlog, xbmc.LOGDEBUG)
        #mgenlogUpdate(mgenlog)  

    except Exception as e:
        printexception()
        mgenlog = 'Mezzmo clearing picture error.'
        xbmc.log(mgenlog, xbmc.LOGNOTICE)
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
        xbmc.log(mgenlog, xbmc.LOGNOTICE)
        mgenlogUpdate(mgenlog)       

    
def getPictures():                                               # Get pictures from DB

    try:
        picfile = openNosyncDB()                                 # Open picture DB
        curps = picfile.execute('SELECT mpTitle, mpUrl FROM mPictures')
        pictuple = curps.fetchall()                              # Get pictures from database
        piclist = []
        for a in range(len(pictuple)):
            itemdict = {
                'title': pictuple[a][0],
                'url': pictuple[a][1],
            }
            piclist.append(itemdict)
        picfile.close()     
        #xbmc.log('Mezzmo piclist dictionary: ' + str(piclist), xbmc.LOGNOTICE) 
        return(piclist)

    except Exception as e:
        printexception()
        mgenlog = 'Mezzmo get picture error.'
        xbmc.log(mgenlog, xbmc.LOGNOTICE)
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
        xbmc.log(mgenlog, xbmc.LOGNOTICE)
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


def picURL(itemurl):                                             # Check for proper file extension

    try:
        if itemurl[len(itemurl)-4] == '.':                       # Add .jpg for urllib issue
            newurl = '"' + itemurl + '"'
        else:
            newurl = '"' + itemurl + '.jpg' + '"'        
        xbmc.log('Mezzmo new picture URL: ' + str(newurl) , xbmc.LOGDEBUG)  
        return newurl

    except Exception as e:  
        printexception()
        mgenlog = 'Mezzmo error converting picture URL'
        xbmc.log(mgenlog, xbmc.LOGNOTICE)
        mgenlogUpdate(mgenlog)   


def picDisplay():                                                # Picture slideshow presenter

    try:
        piclist = getPictures()                                  # Get pictures from picture DB
        slidetime = int(settings('slidetime'))                   # Get slide pause time
        #xbmc.log('Mezzmo picture list: ' + str(piclist) , xbmc.LOGNOTICE)  
        if 'upnp' in str(piclist[0]['url']):                     # Kodi cannot display pictures over uPNP
            dialog_text = translate(30413)
            xbmcgui.Dialog().ok(translate(30412), dialog_text)
            xbmc.executebuiltin('Action(ParentDir)')
            return
        else:
            cselect = 3
            while cselect >= 0:
                pictures = [translate(30417), translate(30476), translate(30418), translate(30419)]
                ddialog = xbmcgui.Dialog() 
                cselect = ddialog.select(translate(30415), pictures)
                if cselect == 2:                                 # User selects pictures normal
                    showPictureMenu(piclist, slidetime)
                    #xbmc.executebuiltin('Action(ParentDir)')
                elif cselect == 3:                               # User selects pictures extended
                    showPictureMenu(piclist, (slidetime * 3))
                    #xbmc.executebuiltin('Action(ParentDir)')
                elif cselect == 0:                               # User selects normal slideshow
                    ShowSlides(piclist, slidetime, 'no')
                elif cselect == 1:                               # User selects continuous slideshow
                    ShowSlides(piclist, slidetime, 'yes')
                elif cselect < 0:
                    #xbmc.executebuiltin('Action(ParentDir)')
                    xbmc.executebuiltin('Dialog.Close(all, true)')
                    break

    except Exception as e:    
        printexception()
        mgenlog = 'Mezzmo error displaying picture slideshow.'
        xbmc.log(mgenlog, xbmc.LOGNOTICE)
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
            xbmc.log(mgenlog, xbmc.LOGNOTICE)
            mgenlogUpdate(mgenlog)   


def ShowSlides(piclist, slidetime, ssmode):                      # Slidehow viewier

    try:    
        kbmonitor = KodiMonitor()                   
        slideIdx = 0   
        #xbmc.log('Mezzmo picture url is: ' + str(playitem) , xbmc.LOGNOTICE)

        xbmc.executebuiltin('Dialog.Close(all, true)')
        while slideIdx < len(piclist):           
            if kbmonitor.flag == 'play':  
                playitem = picURL(piclist[slideIdx]['url'])      # Verify proper file name
                #xbmc.log('Mezzmo picture index is: ' + str(playitem) , xbmc.LOGNOTICE)
                json_query = xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"Player.Open",        \
                "params":{"item":{"file":%s }},"id":1}' % (playitem))           
                #xbmc.log('Mezzmo picture dictionary list  is: ' + str(piclist) , xbmc.LOGNOTICE)
                slideIdx += 1
            xbmc.sleep(slidetime * 1000)
            if slideIdx == len(piclist) and ssmode == 'yes':     # Continuous slideshow
                slideIdx = 0
            #xbmc.log('Mezzmo monitor data is: ' + (kbmonitor.flag) , xbmc.LOGNOTICE)
            if kbmonitor.flag == 'stop':
                del kbmonitor
                xbmc.executebuiltin('Dialog.Close(all, true)')
                return
                break
            if kbmonitor.flag == 'pause':
                slideIdx = slideIdx

        xbmc.executebuiltin('Action(ParentDir)')
        del kbmonitor

    except Exception as e:  
        printexception()
        mgenlog = 'Mezzmo error displaying slides.'
        xbmc.log(mgenlog, xbmc.LOGNOTICE)
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
        xbmc.log(mgenlog, xbmc.LOGNOTICE)
        mgenlogUpdate(mgenlog) 


def displayTrailers(title, itemurl, icon, trselect):              # Display trailers

    try:
        try:
            mtitle = title.encode('utf-8', 'ignore')   	          # Handle commas
        except:
            mtitle = title
        mgenlog ='Mezzmo trailer #' + trselect + ' selected for: '  + mtitle
        xbmc.log(mgenlog, xbmc.LOGNOTICE)
        mgenlogUpdate(mgenlog) 
        #xbmc.log("Mezzmo trailer selected: " + itemurl, xbmc.LOGNOTICE)
        #xbmc.log("Mezzmo trailer icon: " + str(icon), xbmc.LOGNOTICE)
        lititle = "Trailer  #" + trselect + " - " + mtitle
        li = xbmcgui.ListItem(lititle)
        li.setInfo('video', {'Title': lititle})
        li.setArt({'thumb': icon, 'poster': icon}) 
        xbmc.Player().play(itemurl, li)
    except:
        mgenlog ='Mezzmo problem playing trailer #' + trselect + ' - ' + mtitle
        xbmc.log(mgenlog, xbmc.LOGNOTICE)
        mgenlogUpdate(mgenlog)         
        trdialog = xbmcgui.Dialog()
        dialog_text = mgenlog        
        trdialog.ok("Mezzmo Trailer Playback Error", dialog_text) 

