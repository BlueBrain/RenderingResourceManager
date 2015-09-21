#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2014-2015, Human Brain Project
#                          Cyrille Favreau <cyrille.favreau@epfl.ch>
#
# This file is part of RenderingResourceManager
# <https://github.com/BlueBrain/RenderingResourceManager>
#
# This library is free software; you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License version 3.0 as published
# by the Free Software Foundation.
#
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this library; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
# All rights reserved. Do not distribute without further notice.

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
