import urllib2
import urllib
import xbmc

def Browse(url, objectID, flag, startingIndex, requestedCount, pin):

    
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
        response = urllib2.urlopen(req, timeout=180).read()
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
        response = urllib2.urlopen(req, timeout=180).read()
    except Exception as e:
        xbmc.log( 'EXCEPTION IN Search: ' + str(e))
        pass
        
    return response
