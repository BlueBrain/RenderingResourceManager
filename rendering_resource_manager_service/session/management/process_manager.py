#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=W0403
# pylint: disable=E1101

"""
The process manager is in charge of managing system processes using their PID
"""

import signal
import time
import subprocess
import urllib2

import rendering_resource_manager_service.utils.custom_logging as log
from rendering_resource_manager_service.config.management import \
    rendering_resource_settings_manager as manager
from rendering_resource_manager_service.session.models import SESSION_STATUS_STARTING
from rendering_resource_manager_service.config.models import RenderingResourceSettings
import os


class ProcessManager(object):
    """
    The process manager class provides methods for managing system processes using their PID
    """

    # Stop Process
    @staticmethod
    def start(session_info, params, environment):
        """
        Gently starts a given process, waits for 2 seconds and checks for its appearance
        :param session_info: Session information containing the PID of the process
        :return: A Json response containing on ok status or a description of the error
        """
        try:
            settings = manager.RenderingResourceSettingsManager.get_by_id(
                session_info.renderer_id.lower())
            default_parameters = manager.RenderingResourceSettingsManager.format_rest_parameters(
                str(settings.process_rest_parameters_format),
                str(session_info.http_host),
                str(session_info.http_port),
                'rest' + str(settings.id + session_info.id))

            command_line = [
                str(settings.command_line)
            ] + default_parameters.split()
            try:
                command_line += str(params).split()
            except KeyError:
                log.debug(1, 'No parameters specified')
            except TypeError:
                log.debug(1, 'No parameters specified')

            environment_variables = settings.environment_variables.split()
            environment_variables.append(environment)

            log.info(1, 'Launching ' + settings.id + ' with ' + str(command_line))
            process = subprocess.Popen(
                command_line,
                shell=False,
                stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            session_info.process_pid = process.pid
            session_info.status = SESSION_STATUS_STARTING
            return [200, settings.id + ' successfully started [' +
                    str(session_info.process_pid) + ']']
        except RenderingResourceSettings.DoesNotExist as e:
            log.error(str(e))
            return [404, str(e)]

    @staticmethod
    def query(session_info):
        """
        Verifies that a given PID is up and running
        :param session_info: Session information containing the PID of the process
        :return: A Json response containing on ok status or a description of the error
        """
        if session_info.process_pid != -1:
            response = "Process " + str(session_info.process_pid) + ": "
            try:
                os.kill(session_info.process_pid, 0)
            except OSError as e:
                log.error(str(response + e.message))
            else:
                log.error(str(response + 'is running since ' + session_info.timestamp.strftime(
                    '%Y-%m-%d %H:%M:%S')))
        else:
            log.error('Invalid Process Id (" + str(session_info.process_pid) + ")')

    @staticmethod
    def __kill(session_info):
        """
        Kills a given process. This method should only be used if the stop method failed.
        :param session_info: Session information containing the PID of the process
        :return: A Json response containing on ok status or a description of the error
        """
        try:
            os.kill(session_info.process_pid, 0)
        except OSError as e:
            log.info(1, str('Failed to stop process. Killing it: ' + e.message))
            os.kill(session_info.process_pid, signal.SIGKILL)
        # Make sure any zombie child process is removed
        os.waitpid(-1, os.WNOHANG)
        return [200, 'Successfully closed process ' + str(session_info.process_pid)]

    # Stop Process
    @staticmethod
    def stop(session_info):
        """
        Gently stops a given process, waits for 2 seconds and checks for its disappearance
        :param session_info: Session information containing the PID of the process
        :return: A Json response containing on ok status or a description of the error
        """
        if session_info.process_pid == -1:
            return [404, 'Process does not exist']

        try:
            settings = \
                manager.RenderingResourceSettings.objects.get(id=session_info.renderer_id)
            if settings.graceful_exit:
                try:
                    url = 'http://' + session_info.http_host + ':' + \
                          str(session_info.http_port) + '/' + 'EXIT'
                    req = urllib2.Request(url=url)
                    urllib2.urlopen(req).read()
                # pylint: disable=W0702
                except urllib2.URLError as e:
                    log.error('Cannot gracefully exit.' + str(e))

            log.info(1, 'Terminating process ' + str(session_info.process_pid))
            os.kill(session_info.process_pid, signal.SIGTERM)
            time.sleep(2.0)
            result = ProcessManager.__kill(session_info)
        except OSError as e:
            log.error(str(e))
            result = [400, str(e)]

        return result

    # Kill Process
    @staticmethod
    def kill(session_info):
        """
        Kills a given process. This method should only be used if the stop method failed.
        :param session_info: Session information containing the PID of the process
        :return: A Json response containing on ok status or a description of the error
        """
        return ProcessManager.__kill(session_info)
