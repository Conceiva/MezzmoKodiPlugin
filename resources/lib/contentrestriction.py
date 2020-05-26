import urllib.request, urllib.error, urllib.parse
import urllib.request, urllib.parse, urllib.error
import xbmc

def SetContentRestriction(url, ip, enabled, pin):

    
    headers = {'content-type': 'text/xml', 'accept': '*/*', 'SOAPACTION' : '"urn:schemas-upnp-org:service:ContentDirectory:1#CVA_SetContentRestriction"', 'User-Agent': 'Kodi (Mezzmo Addon)'}
    body = '''<?xml version="1.0"?>
    <s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
  <s:Body>
    <u:CVA_SetContentRestriction xmlns:u="urn:schemas-upnp-org:service:ContentDirectory:1">
     <PIN>'''
    body += pin
    body += '''</PIN><IP>'''
    body += ip
    body += '''</IP><enabled>'''
    body += enabled
    body += '''</enabled>
      <SortCriteria></SortCriteria>
    </u:CVA_SetContentRestriction>
  </s:Body>
</s:Envelope>'''
    req = urllib.request.Request(url, body, headers)
    response = ''
    try:
        response = urllib.request.urlopen(req, timeout=60).read()
    except Exception as e:
        xbmc.log( 'EXCEPTION IN CVA_SetContentRestriction: ' + str(e))
        pass
        
    return response
