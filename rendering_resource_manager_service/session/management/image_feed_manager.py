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
The job manager is in charge of managing slurm jobs.
"""

# pylint: disable=W0403
# pylint: disable=E1101
import urllib2
import json
import rendering_resource_manager_service.service.settings as settings
from rendering_resource_manager_service.session.models import Session
import rendering_resource_manager_service.utils.custom_logging as log
from rendering_resource_manager_service.session.management.session_manager_settings \
    import COOKIE_ID


class ImageFeedManager(object):
    """
    Image feed manager. Establishes the connection to the Image Streaming Service and
    manages the routes for the different sessions held by the Rendering Resource
    Manager service.
    """
    def __init__(self, session_id):
        self._session_id = session_id

    def __get_uri(self):
        """
        Returns the route URI for current session
        """
        session = Session.objects.get(id=self._session_id)
        uri = 'http://' + str(session.http_host) + ':' + str(session.http_port)
        return json.dumps({'uri': uri})

    def add_route(self):
        """
        Invokes the image streaming service for the creation of a new route for the
        current session
        """
        return self.__do_request('POST', self.__get_uri())

    def remove_route(self):
        """
        Invokes the image streaming service for the removal of an  existing route for the
        current session
        """
        return self.__do_request('DELETE', '')

    def get_route(self):
        """
        Queries the image streaming service for the route corresponding to the
        current session
        """
        # Check if route already exists'
        status = self.__do_request('GET', '')
        if status[0] == 200:
            log.info(1, 'Route exists: ' + str(status[1]))
            return status
        elif status[0] == 404:
            # Create new route
            log.error('Route does not exist for session ' + str(self._session_id) +
                      ', creating it')
            status = self.add_route()
            if status[0] == 200:
                return self.__do_request('GET', '')
            else:
                response = 'Image streaming service (' + settings.IMAGE_STREAMING_SERVICE_URL + \
                           ') failed to create new route: ' + str(status[1])
                log.error(response)
                return [400, response]
        else:
            response = 'Image streaming service (' + settings.IMAGE_STREAMING_SERVICE_URL + \
                       ') is unreachable: ' + str(status[1])
            log.error(response)
            return [400, response]

    def __do_request(self, method, uri):
        """
        Creates an HTTP request and invokes the image streaming service
        :param method Method to be used by the HTTP request (GET, POST, DELETE, etc)
        :param uri JSON formatted URI to attach to the HTTP request
        :return 200 if successful, Error code and message otherwise
        """
        try:
            url = settings.IMAGE_STREAMING_SERVICE_URL + '/route'
            req = urllib2.Request(url=url, data=uri)
            req.get_method = lambda: method
            req.add_header('Content-Type', 'application/json')
            req.add_header('Cookie', COOKIE_ID + '=' + str(self._session_id))
            response = urllib2.urlopen(req).read()
            log.info(1, '__do_request(' + method + ',' + uri + '=' + response)
            return [200, response]
        except urllib2.HTTPError as e:
            log.error(str(e))
            return [e.code, e.reason]
        except urllib2.URLError as e:
            log.error(str(e))
            return [401, e.reason]
