#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=W0212

"""
This modules allows database tables to be access from the django admin interface
"""

from django.contrib import admin
from django.contrib.admin.sites import NotRegistered
from .models import RenderingResourceSettings, SystemGlobalSettings


class RenderingResourceSettingsAdmin(admin.ModelAdmin):
    """
    This class exposes the RenderingResourceSettings table to the admin interface
    """
    fields = ['command_line', 'environment_variables', 'process_rest_parameters_format',
              'scheduler_rest_parameters_format', 'graceful_exit']

try:
    admin.site.unregister(RenderingResourceSettings)
except NotRegistered as e:
    admin.site.register(RenderingResourceSettings, RenderingResourceSettingsAdmin)


class SystemGlobalSettingsAdmin(admin.ModelAdmin):
    """
    This class exposes the SystemGlobalSettings table to the admin interface
    """
    fields = ['session_creation', 'session_keep_alive_timeout']

try:
    admin.site.unregister(SystemGlobalSettings)
except NotRegistered as e:
    admin.site.register(SystemGlobalSettings, SystemGlobalSettingsAdmin)
