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
This module provides various utility functions
"""


def get_request_headers(request):
    """
    Reads headers from given http request and returns them as a dictionary
    :param request: HTTP request to be processed
    :return: Dictionary of header values
    """
    def format_header_name(name):
        """
        Formats an http parameters to suit dictionaries requirements
        :param name: name of the http parameter
        :return: Formatted header parameter
        """
        return "-".join([x[0].upper() + x[1:] for x in name[5:].lower().split("_")])
    headers = dict([(format_header_name(k), v) for k, v in request.META.items()
                    if k.startswith("HTTP_")])
    headers["Cookie"] = "; ".join([k + "=" + v for k, v in request.COOKIES.items()])
    return headers


def str2bool(value):
    """
    Converts a string to a boolean
    :param value: String containing a boolean value
    :return: True is string is 'yes', 'true', 'on' or '1'. False otherwise
    """
    return value.lower() in ('yes', 'true', 'on', '1')
