#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=W0403
# pylint: disable=F0401
# pylint: disable=E1101

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


admin.autodiscover()

urlpatterns = patterns(
    r'',
    url(settings.BASE_URL_PREFIX + r'/config.json$',
        'rendering_resource_manager_service.service.views.config'),
    url(settings.BASE_URL_PREFIX + r'/api-docs', include(rest_framework_swagger.urls)),
    url(settings.BASE_URL_PREFIX, include(rendering_resource_manager_service.admin.urls)),
    url(settings.BASE_URL_PREFIX, include(rendering_resource_manager_service.config.urls)),
    url(settings.BASE_URL_PREFIX, include(rendering_resource_manager_service.session.urls)),
)
