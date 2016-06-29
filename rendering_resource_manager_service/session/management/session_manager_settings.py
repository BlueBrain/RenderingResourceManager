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
REQUEST_ARGUMENT_METHOD = "method"
REQUEST_ARGUMENT_COMMAND = "command"
REQUEST_ARGUMENT_RENDERER = "renderer"
REQUEST_ARGUMENT_PARAMS = "parameters"

# Renderers
RENDERER_ID_UNDEFINED = 0
RENDERER_ID_LIVRE = 1
RENDERER_ID_RTNEURON = 2
RENDERER_ID_PARAVIEW = 3

# SLURM
SLURM_HOST_DOMAIN = '.cscs.ch'
SLURM_HOST = 'bbpviz1' + SLURM_HOST_DOMAIN
SLURM_SERVICE_URL = 'slurm+ssh://' + SLURM_HOST
SLURM_JOB_NAME_PREFIX = 'VWS_'
SLURM_DEFAULT_QUEUE = 'interactive'
SLURM_PROJECT = 'proj49'
SLURM_OUTPUT_PREFIX = '/gpfs/bbp.cscs.ch/home/' + global_settings.SLURM_USERNAME +\
                      '/var/log/vws_%A_'
SLURM_ERR_FILE = '_err.txt'
SLURM_OUT_FILE = '_out.txt'
SLURM_DEFAULT_MODULE = 'BBP/viz/latest'

# Session management
RRM_SPECIFIC_COMMAND_KEEPALIVE = 'keepalive'
RRM_SPECIFIC_COMMAND_RESUME = 'resume'
RRM_SPECIFIC_COMMAND_SUSPEND = 'suspend'

# Rendering resource commands
RR_SPECIFIC_COMMAND_VOCABULARY = 'zerobuf/render/camera'
