"""
This modules allows integration of this application into the HBP collab
"""

from django.http import HttpResponse
import json
import urllib2
from rendering_resource_manager_service.service.settings import SOCIAL_AUTH_HBP_KEY

HBP_ENV_URL = 'https://collab.humanbrainproject.eu/config.json'


# pylint: disable=W0613
def config(request):
    '''Render the config file'''

    print str(HBP_ENV_URL)
    res = urllib2.urlopen(urllib2.Request(url=HBP_ENV_URL))
    conf = res.read()
    res.close()
    json_response = json.loads(conf)

    # Use this app client ID
    json_response['auth']['clientId'] = SOCIAL_AUTH_HBP_KEY

    return HttpResponse(json.dumps(json_response), content_type='application/json')
