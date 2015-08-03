#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=W0403
# pylint: disable=F0401

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
