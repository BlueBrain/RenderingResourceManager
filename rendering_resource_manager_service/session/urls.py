#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=W0403
# pylint: disable=F0401

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
    url(r'/session/$', session_list),
    url(r'/session/(?P<pk>[a-zA-Z0-9]+)/$', session_details),
    url(r'/session/(?P<command>[a-zA-Z0-9]+)', session_command),
)

urlpatterns = format_suffix_patterns(urlpatterns)
