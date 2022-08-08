import urllib2
import urllib
import xbmc
import media

logcount = 0
srvrtime = int(media.settings('srvrtime'))
if not srvrtime:
    srvrtime = 60
mezzmo_response = int(media.settings('mezzmo_response'))
if mezzmo_response > 0:
    logcount = int(media.settings('mrespcount'))


def Browse(url, objectID, flag, startingIndex, requestedCount, pin):
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
    body += '''</RequestedCount><CVA_PIN>'''
    body += pin
    body += '''</CVA_PIN><SortCriteria></SortCriteria>
    </u:Browse>
  </s:Body>
</s:Envelope>'''
    req = urllib2.Request(url, body, headers)
    response = ''
    try:
        response = urllib2.urlopen(req, timeout=srvrtime).read()
        if logcount < mezzmo_response and mezzmo_response > 0:
            xbmc.log(response.encode('utf-8'), xbmc.LOGNOTICE)
            logcount += 1
            media.settings('mrespcount', str(logcount))
        elif logcount >= mezzmo_response and mezzmo_response > 0:
            media.settings('mezzmo_response', '0')            
            media.settings('mrespcount', '0')
            mgenlog = 'Mezzmo server response logging limit.'   
            xbmc.log(mgenlog, xbmc.LOGNOTICE)
            media.mgenlogUpdate(mgenlog)            
    except Exception as e:
        xbmc.log( 'EXCEPTION IN Browse: ' + str(e))
        pass
        
    return response


def Search(url, objectID, searchCriteria, startingIndex, requestedCount, pin):
    
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
    req = urllib2.Request(url, body, headers)
    response = ''
    try:
        response = urllib2.urlopen(req, timeout=srvrtime).read()
        #response = urllib2.urlopen(req, timeout=60).read()
    except Exception as e:
        xbmc.log( 'EXCEPTION IN Search: ' + str(e))
        pass
        
    return response
