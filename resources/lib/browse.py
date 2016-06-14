import urllib2
import urllib
import xbmc

def Browse(url, objectID, flag, startingIndex, requestedCount):

    
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
    body += '''</RequestedCount>
      <SortCriteria></SortCriteria>
    </u:Browse>
  </s:Body>
</s:Envelope>'''
    req = urllib2.Request(url, body, headers)
    response = ''
    try:
        response = urllib2.urlopen(req, timeout=60).read()
    except Exception as e:
        xbmc.log( 'EXCEPTION IN Browse: ' + str(e))
        pass
        
    return response
