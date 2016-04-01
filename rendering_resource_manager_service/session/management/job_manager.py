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

import signal
import subprocess
import urllib2
import traceback
from threading import Lock
import json

import rendering_resource_manager_service.session.management.session_manager_settings as settings
import rendering_resource_manager_service.utils.custom_logging as log
from rendering_resource_manager_service.config.management import \
    rendering_resource_settings_manager as manager
import saga
import re
from rendering_resource_manager_service.session.models import \
    SESSION_STATUS_STARTING, SESSION_STATUS_RUNNING, \
    SESSION_STATUS_SCHEDULING, SESSION_STATUS_SCHEDULED
import rendering_resource_manager_service.service.settings as global_settings


class JobManager(object):
    """
    The job manager class provides methods for managing slurm jobs via saga.
    """

    def __init__(self):
        """
        Setup saga context, session and service
        """
        self._context = None
        self._session = None
        self._service = None
        self._connected = False
        self._mutex = Lock()

    def __connect(self):
        """
        Utility method to connect to slurm queue, if not already done
        """
        response = [200, 'Connected']
        self._mutex.acquire()
        if not self._connected:
            try:
                self._context = saga.Context('SSH')
                self._context.user_id = global_settings.SLURM_USERNAME
                self._context.user_key = global_settings.SLURM_KEY
                self._session = saga.Session()
                self._session.add_context(self._context)

                url = settings.SLURM_SERVICE_URL
                self._service = saga.job.Service(rm=url, session=self._session)
                log.info(1, 'Connected to slurm queue ' + str(self._service.get_url()))
                self._connected = True
            except saga.SagaException as e:
                log.error(str(e))
                response = [400, str(e)]
        self._mutex.release()
        return response

    def schedule(self, session, params, environment):
        """
        Utility method to schedule an instance of the renderer on the cluster
        """
        status = self.__connect()
        if status[0] != 200:
            return status
        try:
            self._mutex.acquire()
            rr_settings = \
                manager.RenderingResourceSettingsManager.get_by_id(session.renderer_id.lower())
            rest_parameters = manager.RenderingResourceSettingsManager.format_rest_parameters(
                str(rr_settings.scheduler_rest_parameters_format),
                str(session.http_host),
                str(session.http_port),
                'rest' + str(rr_settings.id + session.id))

            session.status = SESSION_STATUS_SCHEDULING
            session.save()
            parameters = rest_parameters.split()
            parameters.append(params)
            environment_variables = rr_settings.environment_variables.split()
            modules = rr_settings.modules.split()
            environment_variables.append(environment)
            log.info(1, 'Scheduling job: ' +
                     str(rr_settings.command_line) + ' ' + str(parameters) + ', ' +
                     str(environment_variables))
            session.job_id = self.create_job(str(rr_settings.id), str(rr_settings.command_line),
                                             parameters, environment_variables, modules)
            session.status = SESSION_STATUS_SCHEDULED
            session.save()
            response = json.dumps({'message': 'Job scheduled', 'jobId': session.job_id})
            return [200, response]
        except saga.SagaException as e:
            log.error(str(e))
            response = json.dumps({'contents': str(e)})
            return [400, response]
        finally:
            self._mutex.release()

    def create_job(self, job_id, executable, params, environment, modules):
        """
        Launch a job on the cluster with the given executable and parameters
        :return: The ID of the job
        """
        log.debug(1, 'Creating job for ' + executable)
        description = saga.job.Description()
        description.name = settings.SLURM_JOB_NAME_PREFIX + job_id
        description.executable = 'module purge\n'
        for module in modules:
            description.executable += 'module load ' + module.strip() + '\n'
        description.executable += executable
        description.total_physical_memory = 2000
        description.arguments = params
        description.queue = settings.SLURM_QUEUE
        description.project = global_settings.SLURM_PROJECT
        description.output = settings.SLURM_OUTPUT_PREFIX + job_id + settings.SLURM_OUT_FILE
        description.error = settings.SLURM_OUTPUT_PREFIX + job_id + settings.SLURM_ERR_FILE

        # Add environment variables
        environment_variables = ''
        for variable in environment:
            variable = variable.strip()
            if variable != '':
                environment_variables = environment_variables + variable + ' '
        if environment_variables != '':
            description.environment = environment_variables

        # Create job
        log.info(1, 'About to submit job for ' + executable)
        job = self._service.create_job(description)
        job.run()
        log.info(1, 'Submitted job for ' + executable + ', got id ' +
                 str(job.get_id()) + ', state ' + str(job.get_state()))
        return job.get_id()

    def query(self, job_id):
        """
        Verifies that a given job is up and running
        :param job_id: The ID of the job
        :return: A Json response containing on ok status or a description of the error
        """
        status = self.__connect()
        if status[0] != 200:
            return status
        if job_id is not None:
            try:
                self._mutex.acquire()
                job = self._service.get_job(job_id)
                response = json.dumps({'contents': str(job.get_state())})
                return [200, response]
            except saga.SagaException as e:
                log.error(str(e))
                response = json.dumps({'contents': str(e.message)})
                return [400, response]
            finally:
                self._mutex.release()

        return [400, 'Invalid job_id ' + str(job_id)]

    # subprocess.check_output is backported from python 2.7
    @staticmethod
    def check_output(*popenargs, **kwargs):
        """Run command with arguments and return its output as a byte string.
        Backported from Python 2.7 as it's implemented as pure python on stdlib.
        >>> check_output(['/usr/bin/python', '--version'])
        Python 2.6.2

        https://gist.github.com/edufelipe/1027906
        """
        process = subprocess.Popen(
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, *popenargs, **kwargs)
        output, unused_err = process.communicate()
        if not unused_err is None:
            log.error(str(unused_err))
        retcode = process.poll()
        if retcode:
            cmd = kwargs.get("args")
            if cmd is None:
                cmd = popenargs[0]
            error = subprocess.CalledProcessError(retcode, cmd)
            error.output = output
            raise error
        return output

    @staticmethod
    def hostname(job_id):
        """
        Retrieve the hostname for the batch host of the given job.
        Note: this uses ssh and scontrol on the SLURM_HOST as saga does not support this feature,
              especially if the job is not persisted. Retrieving the job from the saga service by
              the job_id only sets the state in the job, nothing else.
        :param job_id: The ID of the job
        :return: The hostname of the batch host if the job is running, empty otherwise
        """
        job_id_as_int = re.search(r'(?=)-\[(\w+)\]', job_id).group(1)
        log.info(1, 'Job id as int: ' + str(job_id_as_int))
        result = JobManager.check_output(['ssh', '-i', global_settings.SLURM_KEY,
                                          global_settings.SLURM_USERNAME + '@' +
                                          settings.SLURM_HOST, 'scontrol show job', job_id_as_int])
        log.info(1, str(result))
        state = re.search(r'JobState=(\w+)', result).group(1)
        if state == 'FAILED':
            # Job does not exist
            return state
        if state != 'RUNNING':
            # Job is scheduled but not running
            return ''
        hostname = re.search(r'BatchHost=(\w+)', result).group(1)
        log.info(1, 'Hostname = ' + hostname)
        if hostname.find(settings.SLURM_HOST_DOMAIN) == -1:
            hostname += settings.SLURM_HOST_DOMAIN
        return hostname

    # Stop Process
    def stop(self, session):
        """
        Gently stops a given job, waits for 2 seconds and checks for its disappearance
        :param job_id: The ID of the job
        :return: A Json response containing on ok status or a description of the error
        """
        status = self.__connect()
        if status[0] != 200:
            return status
        if session.job_id is not None:
            try:
                self._mutex.acquire()
                log.info(1, 'Stopping job <' + str(session.job_id) + '>')
                job = self._service.get_job(session.job_id)
                wait_timeout = 2.0
                # pylint: disable=E1101
                setting = \
                    manager.RenderingResourceSettings.objects.get(
                        id=session.renderer_id)
                if setting.graceful_exit:
                    try:
                        url = "http://" + session.http_host + ":" + \
                              str(session.http_port) + "/" + "EXIT"
                        req = urllib2.Request(url=url)
                        urllib2.urlopen(req).read()
                    # pylint: disable=W0702
                    except urllib2.HTTPError as e:
                        msg = str(traceback.format_exc(e))
                        log.debug(1, msg)
                        log.error('Failed to contact rendering resource')
                    except urllib2.URLError as e:
                        msg = str(traceback.format_exc(e))
                        log.debug(1, msg)
                        log.error('Failed to contact rendering resource')

                job.cancel(wait_timeout)
                if job.get_state() == saga.job.CANCELED:
                    msg = 'Job successfully cancelled'
                    log.info(1, msg)
                    response = json.dumps({'contents': msg})
                    result = [200, response]
                else:
                    msg = 'Could not cancel job ' + str(session.job_id)
                    log.info(1, msg)
                    response = json.dumps({'contents': msg})
                    result = [400, response]
            except saga.NoSuccess as e:
                msg = str(traceback.format_exc(e))
                log.error(msg)
                response = json.dumps({'contents': msg})
                result = [400, response]
            except saga.DoesNotExist as e:
                msg = str(traceback.format_exc(e))
                log.info(1, msg)
                response = json.dumps({'contents': msg})
                result = [400, response]
            finally:
                self._mutex.release()
        else:
            log.debug(1, 'No job to stop')

        return result

    # Kill Process
    def kill(self, job_id):
        """
        Kills the given job. This method should only be used if the stop method failed.
        :param job_id: The ID of the job
        :return: A Json response containing on ok status or a description of the error
        """
        if not self.__connect():
            return
        if job_id is not None:
            try:
                self._mutex.acquire()
                job = self._service.get_job(job_id)
                job.signal(signal.SIGKILL)
                if job.get_state() != saga.job.RUNNING:
                    response = json.dumps({'contents': 'Job successfully killed'})
                    return [200, response]
            except saga.SagaException as e:
                msg = str(e)
                log.error(msg)
                response = json.dumps({'contents': msg})
                return [400, response]
            finally:
                self._mutex.release()
        msg = 'Could not kill job ' + str(job_id)
        log.error(msg)
        response = json.dumps({'contents': msg})
        return [400, response]

    @staticmethod
    def job_information(session):
        """
        Returns information about the job
        :param session: the session to be queried
        :return: A string containing the information about the job
        """
        try:
            job_id_as_int = re.search(r'(?=)-\[(\w+)\]', session.job_id).group(1)
            result = JobManager.check_output(['ssh', '-i', global_settings.SLURM_KEY,
                                              global_settings.SLURM_USERNAME + '@' +
                                              settings.SLURM_HOST, 'scontrol show job',
                                              job_id_as_int])
            return result
        except IOError as e:
            return str(e)

    @staticmethod
    def rendering_resource_log(session, filename):
        """
        Returns the contents of the specified file
        :param session: the session to be queried
        :return: A string containing the error log
        """
        try:
            result = 'Not available'
            if session.status in [SESSION_STATUS_STARTING, SESSION_STATUS_RUNNING]:
                job_id_as_int = re.search(r'(?=)-\[(\w+)\]', session.job_id).group(1)
                rr_settings = \
                    manager.RenderingResourceSettingsManager.get_by_id(session.renderer_id.lower())
                filename = settings.SLURM_OUTPUT_PREFIX + \
                           str(rr_settings.id) + filename
                filename = filename.replace('%A', str(job_id_as_int), 1)
                result = filename + ':\n'
                result += JobManager.check_output(['ssh', '-i', global_settings.SLURM_KEY,
                                                   global_settings.SLURM_USERNAME + '@' +
                                                   settings.SLURM_HOST, 'cat ', filename])
            return result
        except IOError as e:
            return str(e)

    @staticmethod
    def rendering_resource_out_log(session):
        """
        Returns the contents of the rendering resource output file
        :param session: the session to be queried
        :return: A string containing the error log
        """
        return globalJobManager.rendering_resource_log(session, settings.SLURM_OUT_FILE)

    @staticmethod
    def rendering_resource_err_log(session):
        """
        Returns the contents of the rendering resource error file
        :param session: the session to be queried
        :return: A string containing the error log
        """
        return globalJobManager.rendering_resource_log(session, settings.SLURM_ERR_FILE)

# Global job manager used for all allocations
globalJobManager = JobManager()
