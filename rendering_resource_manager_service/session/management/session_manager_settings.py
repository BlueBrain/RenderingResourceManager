#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module contains the global constants for the rendering resource manager
"""

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
SLURM_QUEUE = 'interactive'
SLURM_PROJECT = 'proj3'
SLURM_OUTPUT_PREFIX = '/gpfs/bbp.cscs.ch/project/proj3/tmp/vws_%A_'
SLURM_ERR_FILE = '_err.txt'
SLURM_OUT_FILE = '_out.txt'
SLURM_DEFAULT_MODULE = 'BBP/viz/latest'

# Session management
RRM_SPECIFIC_COMMAND_KEEPALIVE = 'keepalive'
RRM_SPECIFIC_COMMAND_RESUME = 'resume'
RRM_SPECIFIC_COMMAND_SUSPEND = 'suspend'

# Rendering resource commands
RR_SPECIFIC_COMMAND_VOCABULARY = 'vocabulary'
