#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=W0403
# pylint: disable=F0401

"""
Defines application URLs
"""

from django.conf.urls import patterns, include, url
from django.contrib import admin
from views import AdminViewSet
from rest_framework.urlpatterns import format_suffix_patterns


admin_view = AdminViewSet.as_view({
    'put': 'admin_command',
})

urlpatterns = patterns(
    '',
    url(r'/admin', include(admin.site.urls)),
    url(r'/admin/(?P<command>[a-zA-Z0-9]+)', admin_view),
)

urlpatterns = format_suffix_patterns(urlpatterns)
