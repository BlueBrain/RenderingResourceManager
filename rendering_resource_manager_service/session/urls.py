#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=W0403
# pylint: disable=F0401

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
Defines application URLs
"""

from django.conf.urls import patterns, url
from rendering_resource_manager_service.session.views import \
    SessionViewSet, CommandViewSet, SessionDetailsViewSet
from rest_framework.urlpatterns import format_suffix_patterns

session_list = SessionViewSet.as_view({
    'post': 'create_session',
    'delete': 'destroy_session',
    'get': 'list_sessions',
})
session_details = SessionDetailsViewSet.as_view({
    'get': 'get_session',
})
session_command = CommandViewSet.as_view({
    'get': 'execute',
    'put': 'execute',
})

urlpatterns = patterns(
    '',
    url(r'session/$', session_list),
    url(r'session/(?P<pk>[a-zA-Z0-9]+)/$', session_details),
    url(r'session/(?P<command>[a-zA-Z0-9]+)', session_command),
)

urlpatterns = format_suffix_patterns(urlpatterns)
