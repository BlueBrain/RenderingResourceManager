#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module provides helper functions for logging of info, debug and error information
"""

from threading import current_thread

import datetime
import logging

L = logging.getLogger(__name__)
logging.basicConfig(level=logging.ERROR)


def info(level, message):
    """
    This function logs a message in the system console with the following format:
    [message level][timestamp][thread name][message]
    :param level: Message level. Only message with a level higher than LOGGING_LEVEL are processed
    :param message: Message to be logged
    """
    L.info("[%s] [%s] [%s] %s",
           str(level),
           datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
           current_thread().getName(),
           message)


def debug(level, message):
    """
    This function logs a message in the system console with the following format:
    [message level][timestamp][thread name][message]
    :param level: Message level. Only message with a level higher than LOGGING_LEVEL are processed
    :param message: Message to be logged
    """
    L.debug("[%s] [%s] [%s] %s",
            str(level),
            datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            current_thread().getName(),
            message)


def error(message):
    """
    This function logs a message in the system console with the following format:
    ERROR [timestamp][thread name][message]
    :param message: Message to be logged
    """
    L.error("[%s] [%s] %s",
            datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            current_thread().getName(),
            message)
