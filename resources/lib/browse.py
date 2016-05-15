import requests

def Browse(url, objectID, flag, startingIndex, requestedCount):

    
    headers = {'content-type': 'text/xml'}
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
    body += startingIndex
    body += '''</StartingIndex>
      <RequestedCount>'''
    body += requestedCount
    body += '''</RequestedCount>
      <SortCriteria>dc:title</SortCriteria>
    </u:Browse>
  </s:Body>
</s:Envelope>'''

    response = requests.post(url,data=body,headers=headers)
    return response.content
