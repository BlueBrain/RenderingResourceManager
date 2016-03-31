#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=W0403

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
This module is the main class of the rendering resource manager. It registers handlers and
starts the web server application.
"""

import threading
import time
import datetime

from django.db import transaction
import rendering_resource_manager_service.utils.custom_logging as log
from rendering_resource_manager_service.session.models import SESSION_STATUS_STOPPING
import job_manager
import process_manager


# Default values
KEEP_ALIVE_TIMEOUT = 600  # Delay after which a session is closed if no keep-alive
# message is received (in seconds)
KEEP_ALIVE_FREQUENCY = 100  # Frequency at which the keep-alive messages are checked


class KeepAliveThread(threading.Thread):
    """
    Session Information Data Structure
    """
    def __init__(self, sessions):
        threading.Thread.__init__(self)
        self.signal = True
        self.sessions = sessions
        log.info(1, "Keep-Alive thread started...")

    def run(self):
        """
        Checks for active sessions. If no keep-alive message was received in the last
        n seconds, the session is closed.
        """
        while self.signal:
            log.info(1, 'Checking for inactive sessions')
            for session in self.sessions.all():
                log.info(1, 'Session ' + str(session.id) +
                         ' is valid until ' + str(session.valid_until))
                if datetime.datetime.now() > session.valid_until:
                    log.info(1, "Session " + str(session.id) +
                             " timed out. Session will now be closed")
                    session.status = SESSION_STATUS_STOPPING
                    with transaction.atomic():
                        session.save()
                    if session.process_pid != -1:
                        process_manager.ProcessManager.stop(session)
                    if session.job_id is not None and session.job_id != '':
                        job_manager.globalJobManager.stop(session)
                    with transaction.atomic():
                        session.delete()
            time.sleep(KEEP_ALIVE_FREQUENCY)
