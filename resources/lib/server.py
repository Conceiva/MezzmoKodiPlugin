import xbmc
import xbmcgui
import xbmcplugin
import urllib.request, urllib.error, urllib.parse
import pickle
import xml.etree.ElementTree
import re
import xml.etree.ElementTree as ET
import xbmcaddon
import ssdp
import json
import socket
from media import openNosyncDB, settings, mezlogUpdate, printexception
from media import mgenlogUpdate, translate, get_installedversion

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
        curps = svrfile.execute('SELECT srvName, mSync, sManuf, controlUrl FROM mServers        \
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
        elif ssync == 0:                                         # Refresh UPnP server list
            clearServers()
            mscount = getServers()
            if mscount == 0:
                msynclog = translate(30399)
                xbmcgui.Dialog().ok(translate(30398), msynclog)
                mezlogUpdate(msynclog)
            else:
                msynclog = 'Mezzmo refresh sync servers found: ' +  str(mscount)
                mezlogUpdate(msynclog)  
        elif ssync > 0:
            if updateSync(srvresults[ssync - 1][3]) == 0:        # Update sync server from selection
                msynclog ='Mezzmo sync server updated manually: ' +          \
                str(srvresults[ssync - 1][0])
                mezlogUpdate(msynclog) 
            
    svrfile.close()
    return


def addServers():                                                #  Manually add UPnP servers

    serverdict = [ {'name': 'Mezzmo', 'port': '53168', 'uri': '/desc'},
                   {'name': 'HDHomeRun', 'port': '80', 'uri': '/dms/device.xml'},
                   {'name': 'MediaMonkey', 'port': '4000', 'uri': '/DeviceDescription.xml'},
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
    #xbmc.log('Mezzmo UPnP server list: ' + str(serverlist), xbmc.LOGINFO)
    sdialog = xbmcgui.Dialog()  
    server = sdialog.select(translate(30450), serverlist)
    #xbmc.log('Mezzmo UPnP server selection: ' + str(server), xbmc.LOGINFO)

    if server < 0:
        return 'None'
    else:
        sport = sdialog.input(translate(30449), serverdict[server]['port'], type=xbmcgui.INPUT_NUMERIC)

    if len(sport) == 0:
        return 'None'
    else:
        serverurl = 'http://' + str(serverip) + ':' + str(sport) + serverdict[server]['uri']
        xbmc.log('Mezzmo UPnP URL is: ' + str(serverurl), xbmc.LOGDEBUG)
        return serverurl


def delServer(srvurl):                                           # Delete server from server list

    try:
        newlist = []
        saved_servers = settings('saved_servers')
        saved_servers = saved_servers.encode('utf-8')
        servers = pickle.loads(saved_servers, fix_imports=True)        

        xbmc.log('Mezzmo UPnP servers: ' + str(servers), xbmc.LOGDEBUG)
        
        if len(saved_servers) > 5 and saved_servers != 'none': 
            for server in servers:
                try:
                    url = server.location
                except:
                    url = server.get('serverurl')  
                if srvurl != url:
                    newlist.append(server)                       # Do not delete from newlist              
            settings('saved_servers', pickle.dumps(newlist,0,fix_imports=True))
            mgenlog = translate(30466) + srvurl
            mgenlogUpdate(mgenlog) 
            xbmcgui.Dialog().notification(translate(30404), mgenlog, addon_icon, 5000)

    except Exception as e:
        printexception()
        mgenlog = 'Mezzmo error deleting UPnP server.'
        xbmc.log(mgenlog, xbmc.LOGINFO)
        mgenlogUpdate(mgenlog)


def downServer(srvrtype='mezzmo'):                               # Handle downed server

    try:
        mgenlog ='Mezzmo no response from server. '
        mgenlogUpdate(mgenlog)
        if srvrtype == 'mezzmo':                                 # Mezzmo server error
            dialog_text = translate(30407)
        else:
            dialog_text = translate(30405).split('.')[0]         # UPnP server error            
        if settings('srvrdialog') == 'true':                     # Ok dialog box for downed server
            xbmcgui.Dialog().ok(translate(30408), dialog_text)
        else:
            xbmcgui.Dialog().notification(translate(30408), dialog_text, addon_icon, 5000)
        return
    except:
        mgenlog = 'Mezzmo error displaying server down message.'
        xbmc.log(mgenlog, xbmc.LOGINFO)                    


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


def checkMezzmo(srvurl):                                         # Check / Update sync sever info

    try:
        timeoutval = int(settings('ssdp_timeout'))
        response = urllib.request.urlopen(srvurl, timeout=timeoutval)
        xmlstring = re.sub(' xmlns="[^"]+"', '', response.read().decode(), count=1)
            
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

    except IOError:                                              # Socket timeout
        msynclog = 'Mezzmo sync server socket timeout: ' + srvurl
        xbmc.log(msynclog, xbmc.LOGINFO)
        mezlogUpdate(msynclog)  
        return '0.0.0.0'

    except (urllib.error.URLError, urllib.error.HTTPError) :    # Detect Server Issues
        msynclog = 'Mezzmo sync server not responding: ' + srvurl
        xbmc.log(msynclog, xbmc.LOGINFO)
        mezlogUpdate(msynclog)  
        return '0.0.0.0'

    except Exception as e:
        printexception()
        msynclog = 'Mezzmo sync server check error.'
        xbmc.log(msynclog, xbmc.LOGINFO)
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
        xbmc.log(msynclog, xbmc.LOGINFO)
        mezlogUpdate(msynclog)
        return 0      


def onlyDiscMezzmo(srvrlist):                                    # Discover only Mezzmo servers

    try:
        if settings('discover_only_mezzmo') == 'false':          # Disable return original UPnP server list
            return srvrlist
        else:
            svrfile = openNosyncDB()                             # Open server database
            curps = svrfile.execute('SELECT srvUrl FROM mServers WHERE sManuf LIKE ?', ('%Conceiva%',))
            svrtuples = curps.fetchall()                         # Get Mezzmo servers from database
            svrfile.close()
            del curps 
            if not svrtuples:                                    # No Mezzmo servers found
                mgenlog = 'Mezzmo only discovery no Mezzmo servers found.'
                mgenlogUpdate(mgenlog)
                return srvrlist
            else:
                mezzlist = []                                    # Mezzmo server list
                for server in srvrlist:
                    try:                                         # Get server URL from SSDP object
                        url = server.location
                    except:
                        url = server.get('serverurl')                        
                    if url in str(svrtuples):                    # Is there a match in kwnon servers
                        mezzlist.append(server) 

                mgenlog = 'Mezzmo only Mezzmo servers enabled. ' + str(len(mezzlist)) + ' Mezzmo server(s) found.'
                mgenlogUpdate(mgenlog)
                if len(mezzlist) > 0:                            # If Mezzmo server(s) found return list
                    return mezzlist
                else:
                    return srvrlist 

    except Exception as e:
        printexception()
        mgenlog = 'Mezzmo discover only Mezzmo server error.'
        xbmc.log(mgenlog, xbmc.LOGINFO)
        mgenlogUpdate(mgenlog)
        return srvrlist  


def checkSync(count):                                            # Check for Sync server

    svrfile = openNosyncDB()                                     # Open server database    
    curps = svrfile.execute('SELECT controlUrl, srvUrl, srvName FROM mServers WHERE mSync=?', ('Yes',))
    srvrtuple = curps.fetchone()                                 # Get server from database
    if srvrtuple:
        syncurl = srvrtuple[0]
        if count < 12 or count > 3600:                           # Don't check Mezzmo server on fast sync
            modelnumb = checkMezzmo(srvrtuple[1])
            if modelnumb != '0.0.0.0':
                sname = srvrtuple[2]
                msynclog = 'Mezzmo sync server responded: ' + sname
                mezlogUpdate(msynclog)
                msynclog = 'Mezzmo sync server version: ' + modelnumb 
                mezlogUpdate(msynclog)
            else:
                sname = srvrtuple[2]
                msynclog = 'Mezzmo sync server did not respond: ' + sname
                mezlogUpdate(msynclog)
                syncurl = 'None'        
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
                mezlogUpdate(msynclog) 
                notify = xbmcgui.Dialog().notification(translate(30401), msynclog, addon_icon, 5000)
        else:                                                    # Sync server not set yet
            syncurl = 'None'
    svrfile.close()
    return syncurl    


def getServers():                                                # Find UPnP servers

    try:
        timeoutval = float(settings('ssdp_timeout'))
        contenturl = ''
        msgdialogprogress = xbmcgui.DialogProgress()
        dialogmsg = translate(30402)
        dialoghead = translate(30401)
        msgdialogprogress.create(dialoghead, dialogmsg)
        servers = ssdp.discover("urn:schemas-upnp-org:device:MediaServer:1", timeout=timeoutval)     
        srvcount = len(servers)
        addtlmsg = '  ' + str(srvcount) + '  UPnP servers discovered.'
        ddialogmsg = dialogmsg + addtlmsg
        msgdialogprogress.update(50, ddialogmsg)
        xbmc.sleep(1000)

        if srvcount > 0:
            msynclog ='Mezzmo sync server search: ' + str(srvcount) + ' UPnP servers found.'
            mezlogUpdate(msynclog)
        else:
            msynclog = translate(30403)
            xbmcgui.Dialog().notification(translate(30401), msynclog, addon_icon, 5000)            
            mezlogUpdate(msynclog)
            return 0
        onlyShowMezzmo = False
        a = 0
        mcount = 0                                                # Count of Mezzmo serves found

        for server in servers:
            url = server.location                
            try:
                response = urllib.request.urlopen(url, timeout=int(timeoutval))
                xmlstring = re.sub(' xmlns="[^"]+"', '', response.read().decode(), count=1)
            
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
                updateServers(url, friendlyname, contenturl, manufacturer, modelnumber,            \
                iconurl, description, udn) 

            except (urllib.error.URLError, urllib.error.HTTPError) :    # Detect Server Issues
                msynclog = 'Mezzmo UPnP server not responding: ' + url
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


def getItemlUrl(contenturl, itemid):                             # Get itemurl for generic UPnP

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


def upnpCheck():                                                 # Check Kodi UPnP setting

    json_query = xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"Settings.GetSettingValue",       \
    "params":{"setting":"services.upnp"}, "id":1}')
    json_query = json.loads(json_query)
    upnp_enabled = ''
    if 'result' in json_query and 'value' in json_query['result']:
        upnp_enabled  = json_query['result']['value']
    xbmc.log('The UPnP status is: ' + str(upnp_enabled), xbmc.LOGDEBUG)

    if upnp_enabled == True:
        return
    else:
        dialog_text = translate(30394)
        cselect = xbmcgui.Dialog().yesno(translate(30406), dialog_text)
    if cselect == 1 :                                           #  Enable UPnP support in Kodi
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
                mgenlog ='Mezzmo Kodi UPnP Set to Enabled.'
                mgenlogUpdate(mgenlog)
            else:        
                dialog_text = translate(30395)
                xbmcgui.Dialog().ok(translate(30396), dialog_text)
                mgenlog ='Mezzmo Kodi UPnP Setting failed.'
                mgenlogUpdate(mgenlog)

            
def clearServers():                                              # Clear server data

    try:
        svrfile = openNosyncDB()                                 # Open server database
        svrfile.execute('DELETE FROM mServers',)  
        svrfile.commit()
        svrfile.close()
        msynclog = 'Mezzmo sync servers cleared.'
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
        #mgenlogUpdate(mgenlog)  

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
            width = piclist[a]['iwidth'] 
            height = piclist[a]['iheight'] 
            date = piclist[a]['idate'].replace('T',' ').strip('Z') 
            desc = piclist[a]['idesc']  
            picfile.execute('INSERT into mPictures (mpTitle, mpUrl, iWidth, iHeight, iDate, idesc)  \
            values (?, ?, ?, ?, ?, ?)', (title, url, width, height, date, desc))
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
        curps = picfile.execute('SELECT mpTitle, mpUrl, iWidth, iHeight, iDate, iDesc FROM mPictures')
        pictuple = curps.fetchall()                              # Get pictures from database
        piclist = []
        for a in range(len(pictuple)):
            itemdict = {
                'title': pictuple[a][0],
                'url': pictuple[a][1],
                'iheight': pictuple[a][2],
                'iwidth': pictuple[a][3],
                'idate': pictuple[a][4],
                'idesc': pictuple[a][5], 
            }
            piclist.append(itemdict)
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


class SlideWindow(xbmcgui.Window):                               # Window class for monitoring 
                                                                 # slideshow controls
    def __init__(self, *args):
        xbmcgui.Window.__init__(self)
        self.slideIdx = self.piclength = self.actionkey = self.exiting = 0
        self.infoflag = self.timed = False
        self.piclist = []
        self.ititle = self.iwidth = self.iheight = self.idate = self.idesc = ''
        self.x = self.getWidth()
        self.y = self.getHeight()
        self.backdropimg = addon_path + '/resources/backdrop.jpg'
        self.icontrol = xbmcgui.ControlImage(0, 0, self.x, self.y, "", 2)
        self.imgcontrol = xbmcgui.ControlImage(int((self.x - 430) / 2), int((self.y - 300) /  2), 400, 400, self.backdropimg)
        self.infcontrol = xbmcgui.ControlLabel(int((self.x - 400) / 2), int((self.y - 270) /  2), 380, 380, "")
        self.infcontrol.setVisible(False)
        self.imgcontrol.setVisible(False)
        self.addControl(self.icontrol)
        self.addControl(self.imgcontrol)
        self.addControl(self.infcontrol)  
        pass

    def onAction(self, action):
        actionkey = action.getId()
        self.actionkey = actionkey

        if actionkey in [10, 13, 92] and self.timed == False :                   # Exit slideshow
            self.exiting = 1
            self.exitClass()

        if actionkey == 11:                                                      # Display image information
            if self.infcontrol.isVisible() == False:
                newlabel = self.formatInfo(self.piclist[self.slideIdx])
                self.infcontrol.setLabel(newlabel)
                self.infcontrol.setVisible(True)
                self.imgcontrol.setVisible(True)               
                self.infoflag = True                                             # Stop navigation during info
            else:
                self.imgcontrol.setVisible(False)
                self.infcontrol.setVisible(False)
                self.infoflag = False                                            # Restart navigation                

        if not self.infoflag or not self.timed:                                  # Navigate if not info or timed
            if actionkey in [2, 5] and self.slideIdx < (self.piclength - 1):     # Next slide
                self.slideIdx += 1
            elif actionkey in [2, 5] and self.slideIdx >= (self.piclength - 1):  # Stop on last slide
                self.exiting = 1
                self.exitClass()

            if actionkey in [1, 6] :                                             # Previous slide
                if self.slideIdx > 0:
                    self.slideIdx -= 1

            if actionkey == 77 and (self.slideIdx + 10) < (self.piclength - 1):  # FF 10 slides
                self.slideIdx += 10
            elif actionkey == 77 and (self.slideIdx + 10) >= (self.piclength - 1):
                self.slideIdx = (self.piclength - 1)             

            if actionkey == 78 and (self.slideIdx - 10) >= 0:                    # RW 10 slides
                self.slideIdx -= 10
            elif actionkey == 78 and (self.slideIdx - 10) < 0:
                self.slideIdx = 0            

            if actionkey == 14 and (self.slideIdx + 25) < (self.piclength - 1):  # Jump +25 slides
                self.slideIdx += 25
            elif actionkey == 14 and (self.slideIdx + 25) >= (self.piclength - 1):
                self.slideIdx = self.piclength - 1             

            if actionkey == 15 and (self.slideIdx - 25) >= 0:                    # Jump - 25 slides
                self.slideIdx -= 25
            elif actionkey == 15 and (self.slideIdx - 25) < 0:
                self.slideIdx = 0            

        if not self.timed and self.exiting == 0:                                 # Update for manual slideshow
            self.updatePic()     

        xbmc.log('Mezzmo slide control action: ' + str(actionkey) , xbmc.LOGDEBUG)

    def exitClass(self):                                                         # Close slideWindow class)
        del self.icontrol
        del self.infcontrol
        del self.imgcontrol
        self.close()        

    def formatInfo(self, playinfo):                                              # Format image information
        ititle = playinfo['title']
        idate = playinfo['idate']            
        iheight = playinfo['iheight']
        iwidth = playinfo['iwidth']
        idesc = playinfo['idesc']
        splitchar = '\n'
        idesclines = idesc.count(splitchar)
        if idesclines > 8:                                                       # Display 8 lines of description
            idesctemp = idesc.split(splitchar)
            idescfpart = splitchar.join(idesctemp[:8])
            idesc = idescfpart + '\n...'
        xbmc.log('Mezzmo idesc line count: ' + str(idesclines) , xbmc.LOGDEBUG)
        newlabel = 'Slide: ' + str(self.slideIdx + 1) + ' of ' + str(self.piclength) + '\n\n'       \
         + '{0:10}'.format('Name:') + ititle + '\n' + '{0:13}'.format('Res:') + str(iwidth) + ' x ' \
         + str(iheight) +  '\n' + '{0:12}'.format('Date:') +  idate + '\n\n' + idesc
        return newlabel
        
    def showPic(self, piclist):                                              # Initial manual slide show starting point
        self.piclist = piclist
        self.piclength = len(self.piclist)                                   # Get number of slides in list
        mgenlog = 'Mezzmo manual slideshow started with ' + str(len(piclist)) + ' slides.'
        mgenlogUpdate(mgenlog)         
        playitem = picURL(piclist[self.slideIdx]['url']).strip('"')
        xbmc.log('Mezzmo slide control showPic: ' + str(playitem) , xbmc.LOGDEBUG)    
        self.icontrol.setImage(playitem, False)

    def updatePic(self):                                                     # Update slide image
        playitem = picURL(self.piclist[self.slideIdx]['url']).strip('"')
        self.icontrol.setImage(playitem, False)
        #xbmc.log('Mezzmo slide control showPic2: ' + str(playitem) , xbmc.LOGDEBUG)


def picURL(itemurl):                                            # Check for proper file extension

    try:
        if itemurl[len(itemurl)-4] == '.' or 'upnp' in itemurl:    # Add .jpg for urllib issue
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
        photoupnp = settings('photoupnp')                        # Get photo UPnP setting
        #xbmc.log('Mezzmo picture list: ' + str(piclist) , xbmc.LOGINFO)  
        if 'upnp' in str(piclist[0]['url']) and photoupnp == 'false':    # Kodi cannot display pictures over UPnP
             dialog_text = translate(30413)
             xbmcgui.Dialog().ok(translate(30412), dialog_text)
             xbmc.executebuiltin('Action(ParentDir)')
             return
        #else:
        cselect = 0
        while cselect >= 0 :
            pictures = [translate(30417), translate(30493), translate(30476), translate(30418), translate(30419)]
            ddialog = xbmcgui.Dialog() 
            cselect = ddialog.select(translate(30415), pictures)
            if cselect < 0:
                #xbmc.executebuiltin('Action(ParentDir)')
                xbmc.executebuiltin('Dialog.Close(all, true)')
                break
            elif cselect == 0:                               # User selects manual slideshow
                manualSlides(piclist)
            elif cselect == 1:                               # User selects normal timed slideshow
                ShowSlide(piclist, slidetime, 'no')
            elif cselect == 2:                               # User selects continuous slideshow
                ShowSlide(piclist, slidetime, 'yes')
            elif cselect == 3:                               # User selects pictures normal
                showPictureMenu(piclist, slidetime)
                #xbmc.executebuiltin('Action(ParentDir)')
            elif cselect == 4:                               # User selects pictures extended
                showPictureMenu(piclist, (slidetime * 3))
                #xbmc.executebuiltin('Action(ParentDir)')

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
            for a in range(len(piclist)):
                pictures.append(piclist[a]['title'])             # Convert rows to list for dialog box    
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


def ShowSlide(piclist, slidetime, ssmode):                             # Timed Slidehow viewier (new)

    try:
        if settings('slideshow') == 'true':                            # Automatic slideshow enabled ?
            xbmc.executebuiltin('Dialog.Close(all, true)')             # If so, close modal display
            xbmc.sleep(1000)             
        slidePause = pausetime = 0 
        slwindow = SlideWindow()              
        slwindow.show()
        slwindow.timed = True                                          # Notify class of timed slideshow
        slwindow.piclist = piclist
        slwindow.piclength = len(piclist)
        if 'yes' in ssmode:
            mgenlog = 'Mezzmo continuous slideshow started with ' + str(len(piclist)) + ' slides.'
        else:
            mgenlog = 'Mezzmo timed slideshow started with ' + str(len(piclist)) + ' slides.'
        mgenlogUpdate(mgenlog)   
        while slwindow.slideIdx < slwindow.piclength: 
            playitem = picURL(piclist[slwindow.slideIdx]['url']).strip('"')
            xbmc.log('Mezzmo slide control showPic: ' + str(playitem) + ' ' + str(slwindow.slideIdx), xbmc.LOGDEBUG)    
            slwindow.updatePic()
            actionkey = slwindow.actionkey
            slwindow.actionkey = 0
            while pausetime <= (slidetime * 1000) and slwindow.actionkey == 0:
                xbmc.sleep(200)                                                  # Check for keystroke every 200ms
                pausetime += 200
                #xbmc.log('Mezzmo timed slideshow pausetime: ' + str(pausetime) , xbmc.LOGINFO)
            xbmc.log('Mezzmo slide key command: ' + str(actionkey) , xbmc.LOGDEBUG)
            if actionkey in [10, 13, 92]:                                        # End slideshow
                break
            elif actionkey in [2, 5] and slwindow.slideIdx < len(piclist)- 1 :   # Go forward 1 slide
                slwindow.slideIdx += 1
            elif actionkey in [7, 12] and slidePause == 0:                       # Pause slideshow
                slidePause = 1
            elif actionkey in [7, 12] and slidePause == 1:                       # Resume slideshow
                slidePause = 0
                slwindow.slideIdx += 1
            elif actionkey == 11 and slidePause == 0:                            # Slide information
                slidePause = 1                
            elif actionkey == 11 and slidePause == 1:                            # Resume after information
                slidePause = 0
                slwindow.slideIdx += 1    
            elif slwindow.slideIdx == len(piclist) - 1 and ssmode == 'yes':      # Continuous slideshow
                slwindow.slideIdx = 0
            elif slidePause == 0 and slwindow.actionkey == 0:
                slwindow.slideIdx += 1
            pausetime = 0

        slwindow.timed = False                                                   # Notify class slideshow ending
        slwindow.close()
        del slwindow
        xbmc.sleep(1500)                                        # Pause on window closing to give Kodi a chance
    except:
        printexception()
        mgenlog = 'Mezzmo timed slideshow error displaying slides.'
        xbmc.log(mgenlog, xbmc.LOGINFO)
        mgenlogUpdate(mgenlog)    


def manualSlides(piclist):                                      # Manual slideshow with full controls

    try:
        slwindow =  SlideWindow()
        xbmc.executebuiltin('Dialog.Close(all, true)')               
        slideIdx = 0
        slwindow.showPic(piclist)
        slwindow.doModal()
        xbmc.sleep(1500)                                         # Pause on window closing to give Kodi a chance
        del slwindow
    except:
        printexception()
        mgenlog = 'Mezzmo manual slideshow error displaying slides.'
        xbmc.log(mgenlog, xbmc.LOGINFO)
        mgenlogUpdate(mgenlog)        


def showSingle(url):                                             # Display individual native picture

    try:
        photoupnp = settings('photoupnp')                        # Get photo UPnP setting
        if 'upnp' in str(url[0]) and photoupnp == 'false':       # Kodi cannot display pictures over UPnP
             dialog_text = translate(30413)
             xbmcgui.Dialog().ok(translate(30406), dialog_text)
             xbmc.executebuiltin('Action(ParentDir)')
             return
        #else:
        itemurl = picURL(url[0])
        json_query = xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"Player.Open",        \
        "params":{"item":{"file":%s }},"id":1}' % (itemurl))  

    except Exception as e:    
        printexception()
        mgenlog = 'Mezzmo error displaying single picture.'
        xbmc.log(mgenlog, xbmc.LOGINFO)
        mgenlogUpdate(mgenlog) 


def displayTrailers(title, itemurl, icon, trselect):              # Display trailers

    try:
        mtitle = title                                            # Handle commas
        mgenlog ='Mezzmo trailer #' + trselect + ' selected for: '  + title
        mgenlogUpdate(mgenlog) 
        #xbmc.log("Mezzmo trailer selected: " + itemurl, xbmc.LOGINFO)
        #xbmc.log("Mezzmo trailer icon: " + str(icon), xbmc.LOGINFO)
        lititle = "Trailer  #" + trselect + " - " + mtitle
        li = xbmcgui.ListItem(lititle)
        if int(get_installedversion()) == 19:
            li.setInfo('video', {'Title': lititle})
        else:
            linfo = li.getVideoInfoTag()
            linfo.setTitle(lititle)
        li.setArt({'thumb': icon, 'poster': icon}) 
        xbmc.Player().play(itemurl, li)
    except:
        mgenlog ='Mezzmo problem playing trailer #' + trselect + ' - ' + title
        xbmc.log(mgenlog, xbmc.LOGINFO)
        mgenlogUpdate(mgenlog)         
        trdialog = xbmcgui.Dialog()
        dialog_text = mgenlog        
        trdialog.ok("Mezzmo Trailer Playback Error", dialog_text) 

