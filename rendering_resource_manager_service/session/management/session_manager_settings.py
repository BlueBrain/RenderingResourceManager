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
This module contains the global constants for the rendering resource manager
"""

import rendering_resource_manager_service.service.settings as global_settings


# HTTP Cookie ID
COOKIE_ID = "HBP"

# Logging level
LOGGING_LEVEL = 3

# Default values
DEFAULT_RENDERER_HTTP_PORT = 3000
DEFAULT_RENDERER_HOST = 'localhost'

# REST
REST_VERB_POST = 'POST'
REST_VERB_GET = 'GET'
REST_VERB_PUT = 'PUT'
REST_VERB_DELETE = 'DELETE'
REST_VERB_PATCH = 'PATCH'

# Command line arguments
REQUEST_ARGUMENT_METHOD = 'method'
REQUEST_ARGUMENT_COMMAND = 'command'
REQUEST_ARGUMENT_RENDERER = 'renderer'
REQUEST_ARGUMENT_PARAMS = 'parameters'

# Request parameters
REQUEST_PARAMETER_SESSIONID = 'session_id'
REQUEST_HEADER_AUTHORIZATION = 'HTTP_AUTHORIZATION'

# SLURM
SLURM_OUTPUT_PREFIX = '/gpfs/bbp.cscs.ch/home/' + global_settings.SLURM_USERNAME +\
                      '/var/log/vws'
SLURM_ERR_FILE = 'err.log'
SLURM_OUT_FILE = 'out.log'
SLURM_ALLOCATION_TIMEOUT = 10

# Session management
RRM_SPECIFIC_COMMAND_KEEPALIVE = 'keepalive'
RRM_SPECIFIC_COMMAND_RESUME = 'resume'
RRM_SPECIFIC_COMMAND_SUSPEND = 'suspend'

# Rendering resource commands
RR_SPECIFIC_COMMAND_VOCABULARY = 'registry'
RR_SPECIFIC_COMMAND_EXIT = 'v1/exit'
