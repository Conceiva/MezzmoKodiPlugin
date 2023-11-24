import urllib.request, urllib.error, urllib.parse
import urllib.request, urllib.parse, urllib.error
import xbmc
import media

logcount = 0
srvrtime = int(media.settings('srvrtime'))
if not srvrtime:
    srvrtime = 60
mezzmo_response = int(media.settings('mezzmo_response'))
if mezzmo_response > 0:
    logcount = int(media.settings('mrespcount'))


def Browse(url, objectID, flag, startingIndex, requestedCount, pin, mode='browse'):
    global logcount, srvrtime
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
    body += '''</RequestedCount><CVA_PIN>'''
    body += pin
    body += '''</CVA_PIN><SortCriteria></SortCriteria>
    </u:Browse>
  </s:Body>
</s:Envelope>'''
    req = urllib.request.Request(url, body.encode('utf-8'), headers)
    response = ''
    try:
        if 'browse' in mode:                       # Set timeout to 60 seconds during sync
            srvrtime = srvrtime
        else:
            srvrtime = 60
        xbmc.log('Mezzmo srvrtime is: ' + str(srvrtime), xbmc.LOGDEBUG) 
        response = urllib.request.urlopen(req, timeout=srvrtime).read().decode('utf-8')
        if logcount < mezzmo_response and mezzmo_response > 0:
            xbmc.log(response, xbmc.LOGINFO)
            logcount += 1
            media.settings('mrespcount', str(logcount))
        elif logcount >= mezzmo_response and mezzmo_response > 0:
            media.settings('mezzmo_response', '0')            
            media.settings('mrespcount', '0')
            mgenlog = 'Mezzmo server response logging limit.'   
            xbmc.log(mgenlog, xbmc.LOGINFO)
            media.mgenlogUpdate(mgenlog) 
    except Exception as e:
        xbmc.log( 'EXCEPTION IN Browse: ' + str(e))
        pass
    #xbmc.log('The current response is: ' + str(response), xbmc.LOGINFO)    
    return response


def Search(url, objectID, searchCriteria, startingIndex, requestedCount, pin):
    global logcount, srvrtime   
    headers = {'content-type': 'text/xml', 'accept': '*/*', 'SOAPACTION' : '"urn:schemas-upnp-org:service:ContentDirectory:1#Search"', 'User-Agent': 'Kodi (Mezzmo Addon)'}
    body = '''<?xml version="1.0"?>
    <s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
  <s:Body>
    <u:Search xmlns:u="urn:schemas-upnp-org:service:ContentDirectory:1">
     <ContainerID>'''
    body += objectID
    body += '''</ContainerID>
      <SearchCriteria>'''
    body += searchCriteria
    body += '''</SearchCriteria>
      <Filter>*,cva_richmetadata,cva_bookmark</Filter>
      <StartingIndex>'''
    body += str(startingIndex)
    body += '''</StartingIndex>
      <RequestedCount>'''
    body += str(requestedCount)
    body += '''</RequestedCount><CVA_PIN>'''
    body += pin
    body += '''</CVA_PIN><SortCriteria></SortCriteria>
    </u:Search>
  </s:Body>
</s:Envelope>'''
    req = urllib.request.Request(url, body.encode('utf-8'), headers)
    response = ''
    try:
        response = urllib.request.urlopen(req, timeout=srvrtime).read().decode('utf-8')
        if logcount < mezzmo_response and mezzmo_response > 0:
            xbmc.log(response, xbmc.LOGINFO)
            logcount += 1
            media.settings('mrespcount', str(logcount))
        elif logcount >= mezzmo_response and mezzmo_response > 0:
            media.settings('mezzmo_response', '0')            
            media.settings('mrespcount', '0')
            mgenlog = 'Mezzmo server response logging limit.'   
            xbmc.log(mgenlog, xbmc.LOGINFO)
            media.mgenlogUpdate(mgenlog) 
    except Exception as e:
        xbmc.log( 'EXCEPTION IN Search: ' + str(e))
        pass
        
    return response
