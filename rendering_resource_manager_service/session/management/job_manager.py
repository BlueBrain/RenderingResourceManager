#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=W0403
# pylint: disable=R0915

# Copyright (c) 2014-2015, Human Brain Project
#                          Cyrille Favreau <cyrille.favreau@epfl.ch>
#                          Daniel Nachbaur <daniel.nachbaur@epfl.ch>
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
The job manager is in charge of managing slurm jobs.
"""

import subprocess
import requests
import traceback
from threading import Lock
import json
import re

import rendering_resource_manager_service.session.management.session_manager_settings as settings
from rendering_resource_manager_service.config.management import \
    rendering_resource_settings_manager as manager
import rendering_resource_manager_service.utils.custom_logging as log
from rendering_resource_manager_service.session.models import \
    SESSION_STATUS_STARTING, SESSION_STATUS_RUNNING, \
    SESSION_STATUS_SCHEDULING, SESSION_STATUS_SCHEDULED
import rendering_resource_manager_service.service.settings as global_settings


SLURM_SSH_COMMAND = '/usr/bin/ssh -i ' + \
                  global_settings.SLURM_SSH_KEY + ' ' + \
                  global_settings.SLURM_USERNAME + '@' + \
                  global_settings.SLURM_HOST + ' '


class JobInformation(object):
    """
    The job information class holds slurm job attributes
    """

    def __init__(self):
        """
        Initialization
        """
        self.name = ''
        self.params = ''
        self.environment = ''
        self.reservation = ''
        self.project = ''
        self.exclusive_allocation = False


class JobManager(object):
    """
    The job manager class provides methods for managing slurm jobs
    """

    def __init__(self):
        """
        Setup job manager
        """
        self._mutex = Lock()

    def schedule(self, session, job_information):
        """
        Allocates a job and starts the rendering resource process. If successful, the session
        job_id is populated and the session status is set to SESSION_STATUS_STARTING
        :param session: Session for which the Slurm job is to be scheduled
        :param job_information: Information about the job
        :return: A Json response containing on ok status or a description of the error
        """
        status = self.allocate(session, job_information)
        if status[0] == 200:
            session.http_host = self.hostname(session.job_id)
            status = self.start(session, job_information)
        return status

    def allocate(self, session, job_information):
        """
        Allocates a job according to rendering resource configuration. If the allocation is
        successful, the session job_id is populated and the session status is set to
        SESSION_STATUS_SCHEDULED
        :param session: Session for which the Slurm job is to be allocated
        :param job_information: Information about the job
        :return: A Json response containing on ok status or a description of the error
        """
        try:
            self._mutex.acquire()
            session.status = SESSION_STATUS_SCHEDULING
            session.save()

            rr_settings = \
                manager.RenderingResourceSettingsManager.get_by_id(session.renderer_id.lower())

            options = ''
            if rr_settings.exclusive:
                options += ' --exclusive'
            if rr_settings.nb_nodes != 0:
                options += ' -N ' + str(rr_settings.nb_nodes)
            else:
                options += ' -c ' + str(rr_settings.nb_cpus)
                options += ' --gres=gpu:' + str(rr_settings.nb_gpus)

            if job_information.reservation != '':
                options += ' --reservation=' + job_information.reservation

            log.info(1, 'Scheduling job for session ' + session.id)

            job_name = session.owner + '_' + rr_settings.id
            command_line = SLURM_SSH_COMMAND + \
                'salloc --no-shell' + \
                ' --immediate=' + str(settings.SLURM_ALLOCATION_TIMEOUT) + \
                ' -p ' + rr_settings.queue + \
                ' --account=' + rr_settings.project + \
                ' --job-name=' + job_name + \
                options
            log.info(1, command_line)
            process = subprocess.Popen(
                [command_line],
                shell=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)

            error = process.communicate()[1]
            if len(re.findall('Granted', error)) != 0:
                session.job_id = re.findall('\\d+', error)[0]
                log.info(1, 'Allocated job ' + str(session.job_id))
            else:
                log.error(error)
                response = json.dumps({'contents': error})
                return [400, response]
            process.stdin.close()
            session.status = SESSION_STATUS_SCHEDULED
            session.save()
            response = json.dumps({'message': 'Job scheduled', 'jobId': session.job_id})
            return [200, response]
        except OSError as e:
            log.error(str(e))
            response = json.dumps({'contents': str(e)})
            return [400, response]
        finally:
            if self._mutex.locked():
                self._mutex.release()

    def start(self, session, job_information):
        """
        Start the rendering resource using the job allocated by the schedule method. If successful,
        the session status is set to SESSION_STATUS_STARTING
        :param session: Session for which the rendering resource is started
        :param job_information: Information about the job
        :return: A Json response containing on ok status or a description of the error
        """
        try:
            self._mutex.acquire()
            session.status = SESSION_STATUS_STARTING
            session.save()

            rr_settings = \
                manager.RenderingResourceSettingsManager.get_by_id(session.renderer_id.lower())

            # Modules
            full_command = 'module purge\n'
            values = rr_settings.modules.split()
            for module in values:
                full_command += 'module load ' + module.strip() + '\n'

            # Environment variables
            values = rr_settings.environment_variables.split()
            values += job_information.environment.split()
            for variable in values:
                full_command += variable + ' '

            # Command lines parameters
            rest_parameters = manager.RenderingResourceSettingsManager.format_rest_parameters(
                str(rr_settings.scheduler_rest_parameters_format),
                str(session.http_host),
                str(session.http_port),
                'rest' + str(rr_settings.id + session.id))
            values = rest_parameters.split()
            values += job_information.params.split()
            full_command += rr_settings.command_line
            for parameter in values:
                full_command += ' ' + parameter

            # Output redirection
            full_command += ' > ' + self._file_name(session, settings.SLURM_OUT_FILE)
            full_command += ' 2> ' + self._file_name(session, settings.SLURM_ERR_FILE)
            full_command += ' &\n'

            # Start Process on cluster
            command_line = '/usr/bin/ssh -i ' + \
                           global_settings.SLURM_SSH_KEY + ' ' + \
                           global_settings.SLURM_USERNAME + '@' + \
                           session.http_host + global_settings.SLURM_HOST_DOMAIN

            log.info(1, 'Connect to cluster machine: ' + command_line)
            process = subprocess.Popen(
                [command_line],
                shell=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)

            log.info(1, 'Full command:\n' + full_command)
            process.stdin.write(full_command)
            output = process.communicate()[0]
            log.info(1, output)
            process.stdin.close()

            session.status = SESSION_STATUS_STARTING
            session.save()
            response = json.dumps({'message': session.renderer_id + ' successfully started'})
            return [200, response]
        except OSError as e:
            log.error(str(e))
            response = json.dumps({'contents': str(e)})
            return [400, response]
        finally:
            if self._mutex.locked():
                self._mutex.release()

    def stop(self, session):
        """
        Gently stops a given job, waits for 2 seconds and checks for its disappearance
        :param session: Session for which the rendering resource is stopped
        :return: A Json response containing on ok status or a description of the error
        """
        result = [500, 'Unexpected error']
        try:
            self._mutex.acquire()
            # pylint: disable=E1101
            setting = \
                manager.RenderingResourceSettings.objects.get(
                    id=session.renderer_id)
            if setting.graceful_exit:
                log.info(1, 'Gracefully exiting rendering resource')
                try:
                    url = 'http://' + session.http_host + global_settings.SLURM_HOST_DOMAIN + \
                          ':' + str(session.http_port) + '/' + \
                          settings.RR_SPECIFIC_COMMAND_EXIT
                    log.info(1, url)
                    r = requests.put(
                        url=url,
                        timeout=global_settings.REQUEST_TIMEOUT)
                    r.close()
                # pylint: disable=W0702
                except requests.exceptions.RequestException as e:
                    log.error(traceback.format_exc(e))
            result = self.kill(session.job_id)
        except OSError as e:
            msg = str(e)
            log.error(msg)
            response = json.dumps({'contents': msg})
            result = [400, response]
        finally:
            if self._mutex.locked():
                self._mutex.release()
        return result

    @staticmethod
    def kill(job_id):
        """
        Kills the given job. This method should only be used if the stop method failed.
        :param job_id: The ID of the job
        :return: A Json response containing on ok status or a description of the error
        """
        result = [500, 'Unexpected error']
        if job_id is not None:
            try:
                command_line = SLURM_SSH_COMMAND + 'scancel ' + job_id
                log.info(1, 'Stopping job ' + job_id)
                process = subprocess.Popen(
                    [command_line],
                    shell=True,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE)
                output = process.communicate()[0]
                log.info(1, output)
                msg = 'Job successfully cancelled'
                log.info(1, msg)
                response = json.dumps({'contents': msg})
                result = [200, response]
            except OSError as e:
                msg = str(e)
                log.error(msg)
                response = json.dumps({'contents': msg})
                result = [400, response]
        return result

    def hostname(self, job_id):
        """
        Retrieve the hostname for the host of the given job is allocated.
        Note: this uses ssh and scontrol on the SLURM_HOST
        :param job_id: The ID of the job
        :return: The hostname of the host if the job is running, empty otherwise
        """
        return self._query(job_id, 'BatchHost')

    def job_information(self, job_id):
        """
        Returns information about the job
        :param job_id: The ID of the job
        :return: A string containing the status of the job
        """
        return self._query(job_id, 'JobStatus')

    def rendering_resource_out_log(self, session):
        """
        Returns the contents of the rendering resource output file
        :param session: The session to be queried
        :return: A string containing the output log
        """
        return self._rendering_resource_log(session, settings.SLURM_OUT_FILE)

    def rendering_resource_err_log(self, session):
        """
        Returns the contents of the rendering resource error file
        :param session: The session to be queried
        :return: A string containing the error log
        """
        return self._rendering_resource_log(session, settings.SLURM_ERR_FILE)

    @staticmethod
    def _query(job_id, attribute):
        """
        Verifies that a given job is up and running
        :param job_id: The ID of the job
        :return: A Json response containing an ok status or a description of the error
        """
        value = ''
        if job_id is not None:
            try:
                command_line = SLURM_SSH_COMMAND + \
                               'scontrol show job ' + job_id
                process = subprocess.Popen(
                    [command_line],
                    shell=True,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE)
                output = process.communicate()[0]
                value = re.search(attribute + r'=(\w+)', output).group(1)
                log.info(1, attribute + ' = ' + value)
                return value
            except OSError as e:
                log.error(str(e))
        return value

    @staticmethod
    def _file_name(session, extension):
        """
        Returns the contents of the log file with the specified extension
        :param session: The session to be queried
        :param extension: file extension (typically err or out)
        :return: A string containing the error log
        """
        return settings.SLURM_OUTPUT_PREFIX + '_' + str(session.job_id) + \
               '_' + session.renderer_id + '_' + extension

    def _rendering_resource_log(self, session, extension):
        """
        Returns the contents of the specified file
        :param session: The session to be queried
        :param extension: File extension (typically err or out)
        :return: A string containing the log
        """
        try:
            result = 'Not currently available'
            if session.status in [SESSION_STATUS_STARTING, SESSION_STATUS_RUNNING]:
                filename = self._file_name(session, extension)
                command_line = SLURM_SSH_COMMAND + 'cat ' + filename
                log.info(1, 'Querying log: ' + command_line)
                process = subprocess.Popen(
                    [command_line],
                    shell=True,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE)
                output = process.communicate()[0]
                result = output
            return result
        except OSError as e:
            return str(e)
        except IOError as e:
            return str(e)


# Global job manager used for all allocations
globalJobManager = JobManager()
