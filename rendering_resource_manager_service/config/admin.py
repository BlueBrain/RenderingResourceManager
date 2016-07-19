#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=W0212

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
This modules allows database tables to be access from the django admin interface
"""

from django.contrib import admin
from django.contrib.admin.sites import NotRegistered
from .models import RenderingResourceSettings, SystemGlobalSettings


class RenderingResourceSettingsAdmin(admin.ModelAdmin):
    """
    This class exposes the RenderingResourceSettings table to the admin interface
    """
    fields = ['id', 'command_line', 'environment_variables', 'modules',
              'process_rest_parameters_format', 'scheduler_rest_parameters_format',
              'project', 'queue', 'exclusive', 'nb_nodes', 'nb_cpus', 'nb_gpus',
              'graceful_exit', 'wait_until_running']

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
