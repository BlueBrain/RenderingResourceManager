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
This module provides helper functions for logging of info, debug and error information
"""

from threading import current_thread
import datetime
from threading import Lock
import sys

log_mutex = Lock()
LOGGING_LEVEL = 1


def print_message(prefix, destination, level, message):
    """
    This function logs a message in the system console with the following format:
    [type][message level][timestamp][thread name][message]
    :param destination: cerr or cout
    :param prefix: DEBUG, INFO or ERROR
    :param level: Message level. Only message with a level higher than LOGGING_LEVEL are processed
    :param message: Message to be logged
    """
    if level <= LOGGING_LEVEL:
        log_mutex.acquire()
        destination.write(prefix + ' [%s] [%s] [%s] %s\n' % (
              str(level),
              datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'),
              current_thread().getName(),
              message))
        log_mutex.release()


def info(level, message):
    """
    This function logs a message in the system console with the following format:
    [message level][timestamp][thread name][message]
    :param level: Message level. Only message with a level higher than LOGGING_LEVEL are processed
    :param message: Message to be logged
    """
    print_message('[INFO ]', sys.stdout, level, message)


def debug(level, message):
    """
    This function logs a message in the system console with the following format:
    [message level][timestamp][thread name][message]
    :param level: Message level. Only message with a level higher than LOGGING_LEVEL are processed
    :param message: Message to be logged
    """
    print_message('[DEBUG]', sys.stdout, level, message)


def error(message):
    """
    This function logs a message in the system console with the following format:
    ERROR [timestamp][thread name][message]
    :param message: Message to be logged
    """
    print_message('[ERROR]', sys.stderr, 1, message)
