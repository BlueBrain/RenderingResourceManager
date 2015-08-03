#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=W0403

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
KEEP_ALIVE_FREQUENCY = 10  # Frequency at which the keep-alive messages are checked


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
