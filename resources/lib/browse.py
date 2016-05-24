import urllib2
import urllib

def Browse(url, objectID, flag, startingIndex, requestedCount):

    
    headers = {'content-type': 'text/xml', 'accept': '*/*'}
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
      <Filter>*</Filter>
      <StartingIndex>'''
    body += str(startingIndex)
    body += '''</StartingIndex>
      <RequestedCount>'''
    body += str(requestedCount)
    body += '''</RequestedCount>
      <SortCriteria>dc:title</SortCriteria>
    </u:Browse>
  </s:Body>
</s:Envelope>'''
    req = urllib2.Request(url, body, headers)
    response = urllib2.urlopen(req).read()
    return response
