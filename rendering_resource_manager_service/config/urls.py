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
from views import RenderingResourceSettingsViewSet, RenderingResourceSettingsDetailsViewSet
from rest_framework.urlpatterns import format_suffix_patterns

settings_list = RenderingResourceSettingsViewSet.as_view({
    'post': 'create',
    'get': 'list',
    'put': 'update',
})
settings_details = RenderingResourceSettingsDetailsViewSet.as_view({
    'delete': 'delete',
})

urlpatterns = patterns(
    '',
    url(r'/config/$', settings_list),
    url(r'/config/(?P<id>[a-zA-Z0-9]+)/$', settings_details),
)

urlpatterns = format_suffix_patterns(urlpatterns)
