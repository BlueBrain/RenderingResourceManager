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
Django settings for rendering_resource_manager_service project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import sys


BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Application name
APPLICATION_NAME = 'rendering-resource-manager'

# API version
API_VERSION = 'v1'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = False

ALLOWED_HOSTS = (
    'localhost',
    '127.0.0.1',
    '0.0.0.0',
)

# Quick-start development config - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'aS3cr3tK3y'


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    'corsheaders',
    'rest_framework',
    'rest_framework_swagger',
    'django_filters',
    'admin',
    'session',
    'config',
    'service',
)

MIDDLEWARE_CLASSES = (
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

# Cors headers
CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = False
CORS_ORIGIN_WHITELIST = (
    'localhost:8095',
    '127.0.0.1:8095',
    '127.0.0.1:4200',
    '0.0.0.0:8095',
)


ROOT_URLCONF = 'rendering_resource_manager_service.service.urls'

WSGI_APPLICATION = 'rendering_resource_manager_service.service.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.7/ref/config/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'OPTIONS': {'timeout': 20},
        'NAME': os.path.join(BASE_DIR + '/tests', 'db.sqlite3'),
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': '/var/tmp/django_cache',
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/

SWAGGER_SETTINGS = {
    'exclude_namespaces': [],
    'api_version': '0.1',
    'api_path': '/',
    'enabled_methods': [
        'get',
        'post',
        'put',
        'patch',
        'delete'
    ],
    'api_key': '',
    'is_authenticated': False,
    'is_superuser': False,
    'permission_denied_handler': None,
    'info': {
        'contact': 'cyrille.favreau@epfl.ch',
        'description': 'This is the Rendering Resource Manager Service. ',
        'title': 'Rendering Resource Manager',
    },
    'doc_expansion': 'full',
}

# Base URL prefix
BASE_URL_PREFIX = r''

# Needed by unit testing
sys.path.append(BASE_DIR)
sys.path.append(BASE_DIR + '/rendering_resource_manager_service')

# Job allocator
RESOURCE_ALLOCATOR_SLURM = 'SLURM'
RESOURCE_ALLOCATOR_UNICORE = 'UNICORE'
RESOURCE_ALLOCATOR = RESOURCE_ALLOCATOR_UNICORE

# Slurm (To be modified by deployment process)
SLURM_USERNAME = 'TO_BE_MODIFIED'
SLURM_SSH_KEY = 'TO_BE_MODIFIED'
SLURM_PROJECT = 'TO_BE_MODIFIED'
SLURM_HOSTS = ['TO_BE_MODIFIED']
SLURM_DEFAULT_QUEUE = 'TO_BE_MODIFIED'
SLURM_DEFAULT_TIME = 'TO_BE_MODIFIED'

# Unicore
UNICORE_DEFAULT_REGISTRY_URL = 'TO_BE_MODIFIED'
UNICORE_DEFAULT_SITE = 'TO_BE_MODIFIED'
UNICORE_DEFAULT_HTTP_PROXIES = {
    'http': 'TO_BE_MODIFIED',
    'ftp': 'TO_BE_MODIFIED',
    'https': 'TO_BE_MODIFIED',
}

# ClientID needed by the HBP collab project browser
SOCIAL_AUTH_HBP_KEY = 'TO_BE_MODIFIED'

# Image Streaming Service URL
IMAGE_STREAMING_SERVICE_URL = 'TO_BE_MODIFIED'
REQUEST_TIMEOUT = 5

try:
    from local_settings import * # pylint: disable=F0401,W0403,W0401,W0614
except ImportError as e:
    pass

# Static files
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR + '/../apps/AngularVwsViewer',
]
