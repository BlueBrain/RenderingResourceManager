#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=W0403
# pylint: disable=F0401
# pylint: disable=E1101

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

from django.contrib import admin
from django.conf.urls import patterns, include, url
import rest_framework_swagger.urls
import rendering_resource_manager_service.service.settings as settings
import rendering_resource_manager_service.admin.urls
import rendering_resource_manager_service.config.urls
import rendering_resource_manager_service.session.urls
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

admin.autodiscover()

urlpatterns = patterns(
    r'',
    url(settings.BASE_URL_PREFIX + r'/config.json$',
        'rendering_resource_manager_service.service.views.config'),
    url(settings.BASE_URL_PREFIX + r'/api-docs', include(rest_framework_swagger.urls)),
    url(settings.BASE_URL_PREFIX + r'/admin', include(admin.site.urls)),
    url(settings.BASE_URL_PREFIX, include(rendering_resource_manager_service.admin.urls)),
    url(settings.BASE_URL_PREFIX, include(rendering_resource_manager_service.config.urls)),
    url(settings.BASE_URL_PREFIX, include(rendering_resource_manager_service.session.urls)),
)

urlpatterns += staticfiles_urlpatterns()
