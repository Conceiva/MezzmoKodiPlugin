import urllib.request, urllib.error, urllib.parse
import urllib.request, urllib.parse, urllib.error
import xbmc

def SetBookmark(url, objectID, pos):

    
    headers = {'content-type': 'text/xml', 'accept': '*/*', 'SOAPACTION' : '"urn:schemas-upnp-org:service:ContentDirectory:1#X_SetBookmark"', 'User-Agent': 'Kodi (Mezzmo Addon)'}
    body = '''<?xml version="1.0"?>
    <s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
  <s:Body>
    <u:X_SetBookmark xmlns:u="urn:schemas-upnp-org:service:ContentDirectory:1">
     <ObjectID>'''
    body += objectID
    body += '''</ObjectID>
      <PosSecond>'''
    body += pos
    body += '''</PosSecond>
    </u:X_SetBookmark>
  </s:Body>
</s:Envelope>'''
    req = urllib.request.Request(url, body.encode('utf-8'), headers)
    response = ''
    try:
        response = urllib.request.urlopen(req, timeout=60).read()
    except Exception as e:
        xbmc.log( 'EXCEPTION IN SetBookmark: ' + str(e))
        pass
        
    return response
