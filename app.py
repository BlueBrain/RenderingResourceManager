#!/usr/bin/env python
# pylint: disable=R0801,W0122,E0602

# Copyright (c) 2014-2015, Human Brain Project
#                          Cyrille Favreau <cyrille.favreau@epfl.ch>
#
# This file is part of RenderingResourceManager
# <https://github.com/BlueBrain/HTTPImageStreaming>
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

"""app.py"""
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE',
                      'rendering_resource_manager_service.service.settings')

from django.core.management import execute_from_command_line

args = []
args.append('manage.py')
args.append('runserver')
args.append('8080')

execute_from_command_line(args)
