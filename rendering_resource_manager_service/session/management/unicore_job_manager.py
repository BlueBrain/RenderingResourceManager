#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=W0102
# pylint: disable=W0613
# pylint: disable=R0201

# Copyright (c) 2014-2017, Human Brain Project
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
The Unicore job manager is in charge of managing Unicore jobs.
"""

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
    SESSION_STATUS_STARTING, SESSION_STATUS_RUNNING
import rendering_resource_manager_service.service.settings as global_settings


class UnicoreJobManager(object):
    """
    The job manager class provides methods for managing slurm jobs
    """

    def __init__(self):
        """
        Setup job manager
        """
        self._mutex = Lock()
        self._base_url = None

    @staticmethod
    def get_sites(registry_url=None, headers={}):
        """
        read the base URLs of the available sites from the registry. If the registry_url is None,
        the HBP registry is used
        :param registry_url:
        :param headers:
        :return: available sites
        """
        if registry_url is None:
            registry_url = global_settings.UNICORE_DEFAULT_REGISTRY_URL
        import copy
        my_headers = copy.deepcopy(headers)
        my_headers['Accept'] = "application/json"
        r = requests.get(registry_url, headers=my_headers, verify=False)
        if r.status_code != 200:
            raise RuntimeError("Error accessing registry at %s: %s" % (registry_url, r.status_code))
        sites = {}
        for x in r.json()['entries']:
            # just want the "core" URL and the site ID
            href = x['href']
            service_type = x['type']
            if "TargetSystemFactory" == service_type:
                base = re.match(r"(https://\S+/rest/core).*", href).group(1)
                site_name = re.match(r"https://\S+/(\S+)/rest/core", href).group(1)
                sites[site_name] = base
        log.info(1, 'Sites: ' + str(sites))
        return sites

    def get_site(self, name, headers=[]):
        """
        :param name:
        :param headers:
        :return:
        """
        return self.get_sites(headers=headers).get(name, None)

    @staticmethod
    def get_properties(resource, headers={}):
        """
        get JSON properties of a resource
        :param resource:
        :param headers:
        :return:
        """
        my_headers = headers.copy()
        my_headers['Accept'] = "application/json"
        r = requests.get(resource, headers=my_headers, verify=False)
        if r.status_code != 200:
            raise RuntimeError("Error getting properties: %s" % r.status_code)
        else:
            return r.json()

    def get_working_directory(self, job, headers={}, properties=None):
        """
        Returns the URL of the working directory resource of a job
        :param job: Job
        :param headers: Headers
        :param properties: Properties
        :return: Working directory on remote station
        """
        if properties is None:
            properties = self.get_properties(job, headers)
        return properties['_links']['workingDirectory']['href']

    def invoke_action(self, resource, action, headers, data={}):
        """
        :param resource:
        :param action:
        :param headers:
        :param data:
        :return:
        """
        my_headers = headers.copy()
        my_headers['Content-Type'] = "application/json"
        action_url = self.get_properties(resource, headers)['_links']['action:' + action]['href']
        r = requests.post(action_url, data=json.dumps(data), headers=my_headers, verify=False)
        if r.status_code != 200:
            raise RuntimeError("Error invoking action: %s" % r.status_code)
        return r.json()

    @staticmethod
    def upload(destination, file_desc, headers):
        """
        :param destination:
        :param file_desc:
        :param headers:
        :return:
        """
        my_headers = headers.copy()
        my_headers['Content-Typqe'] = "application/octet-stream"
        name = file_desc['To']
        data = file_desc['Data']
        # TODO file_desc could refer to local file
        r = requests.put(destination + "/" + name, data=data, headers=my_headers, verify=False)
        if r.status_code != 204:
            raise RuntimeError("Error uploading data: %s" % r.status_code)

    def schedule(self, session, job_information):
        """
        Allocates a job and starts the rendering resource process. If successful, the session
        job_id is populated and the session status is set to SESSION_STATUS_STARTING
        :param session: Current user session
        :param job_information: Information about the job
        :return: A Json response containing on ok status or a description of the error
        """
        self.allocate(session, job_information)
        if job_information.job is not None:
            status = self.start(session, job_information)
        return status

    def submit(self, url, job_information, auth_token, inputs={}):
        """
        Submits a job to the given URL, which can be the ".../jobs" URL or a ".../sites/site_name/"
        URL. If inputs is not empty, the listed input data files are uploaded to the job's working
        directory, and a "start" command is sent to the job.
        """
        headers = dict()
        headers['Content-Type'] = 'application/json'
        headers['authorization'] = auth_token
        if len(inputs) > 0:
            # make sure UNICORE does not start the job
            # before we have uploaded data
            job_information.job['haveClientStageIn'] = 'true'

        r = requests.post(url, data=json.dumps(job_information.job), headers=headers, verify=False)
        if r.status_code != 200:
            obj = json.loads(r.content)
            raise RuntimeError('Error submitting job: ' + obj['errorMessage'])
        else:
            job_information.http_host = r.headers['Location']

        # upload input data and explicitly start job
        if len(inputs) > 0:
            working_directory = self.get_working_directory(job_information.http_host, headers)
            for input_file in inputs:
                self.upload(working_directory + "/files", input_file, headers)
            self.invoke_action(job_information.http_host, "start", headers)

    def is_running(self, job, headers={}):
        """
        check status for a job
        :param job:
        :param headers:
        :return:
        """
        properties = self.get_properties(job, headers)
        status = properties['status']
        return ("SUCCESSFUL" != status) and ("FAILED" != status)

    def wait_for_completion(self, job, headers={}, refresh_function=None, refresh_interval=360):
        """
        Wait until job is done. If refresh_function is not none, it will be called to refresh the
        "Authorization" header
        :param headers:
        :param refresh_function:
        :param refresh_interval: refresh interval is seconds
        :return:
        """
        sleep_interval = 10
        do_refresh = refresh_function is not None
        # refresh every N iterations
        refresh = int(1 + refresh_interval / sleep_interval)
        count = 0
        while self.is_running(job, headers):
            import time
            time.sleep(sleep_interval)
            count += 1
            if do_refresh and count == refresh:
                headers['Authorization'] = refresh_function()
                count = 0

    @staticmethod
    def get_jobs(properties, headers={}):
        """ get JSON properties of a resource """
        my_headers = headers.copy()
        my_headers['Accept'] = "application/json"
        url = properties['_links']['jobs']['href']
        r = requests.get(url, headers=my_headers, verify=False)
        if r.status_code != 200:
            raise RuntimeError("Error getting jobs: %s" % r.status_code)
        return r.json()

    def clear_jobs(self, properties, headers={}):
        """ Clear all job placeholders a resource """
        jobs = self.get_jobs(properties, headers)["jobs"]
        for job in jobs:
            my_headers = headers.copy()
            my_headers['Accept'] = "application/json"
            r = requests.delete(job, headers=my_headers, verify=False)
            if r.status_code != 200 and r.status_code != 204:
                raise RuntimeError(
                    "Error deleting jobs %s: %s" % (job, r.status_code))

    def allocate(self, session, job_information):
        """
        Allocates a job according to rendering resource configuration. If the allocation is
        successful, the session job_id is populated and the session status is set to
        SESSION_STATUS_SCHEDULED
        :param session: Current user session
        :param job_information: Information about the job
        :return: A Json response containing on ok status or a description of the error
        """
        auth = {'Authorization': job_information.auth_token}
        session.http_host = self.get_sites(headers=auth)[global_settings.UNICORE_DEFAULT_SITE]
        # get information about the current user, e.g.
        # role, Unix login and group(s)
        props = self.get_properties(session.http_host, auth)
        if not 'user' == props['client']['role']['selected']:
            log.error('Account is not registered on the selected site')
            self.clear_jobs(props, auth)
        # setup the job - please refer to
        # http://unicore.eu/documentation/manuals/unicore/files/ucc/ucc-manual.html
        # for more options
        job_information.job = dict()

        # Use a shell script, often it is better to setup a server-side 'Application' for a
        # simulation code and invoke that
        job_information.job['ApplicationName'] = 'test'
        job_information.job['Executable'] = '/bin/date'
        job_information.job['Parameters'] = {'SOURCE': 'resource.sh'}
        # Request resources nodes etc
        job_information.job['Resources'] = {'Nodes': job_information.nb_nodes}

    @staticmethod
    def _build_start_command_line(session, job_information):
        """
        :param session:
        :param job_information:
        :return:
        """
        rr_settings = \
            manager.RenderingResourceSettingsManager.get_by_id(session.renderer_id.lower())

        # Modules
        full_command = '"#!/bin/sh\n'
        full_command = full_command + 'module purge\n'
        if rr_settings.modules is not None:
            values = rr_settings.modules.split()
            for module in values:
                full_command += 'module load ' + module.strip() + '\n'

        # Environment variables
        if rr_settings.environment_variables is not None:
            values = rr_settings.environment_variables.split()
            values += job_information.environment.split()
            for variable in values:
                full_command += variable + ' '

        # Command lines parameters
        rest_parameters = manager.RenderingResourceSettingsManager.format_rest_parameters(
            str(rr_settings.scheduler_rest_parameters_format),
            str(session.http_host),
            str(session.http_port),
            'rest' + str(rr_settings.id + session.id),
            str(session.job_id))
        if rr_settings.environment_variables != '':
            values = rest_parameters.split()
            values += job_information.params.split()
            full_command += rr_settings.command_line
            for parameter in values:
                full_command += ' ' + parameter

        full_command += ' &\n"'
        return full_command

    def start(self, session, job_information):
        """
        Start the rendering resource using the job allocated by the schedule method. If successful,
        the session status is set to SESSION_STATUS_STARTING
        :param session: Current user session
        :param job_information: Information about the job
        :return: A Json response containing on ok status or a description of the error
        """
        try:
            self._mutex.acquire()
            session.status = SESSION_STATUS_STARTING
            session.save()

            # the 'resource.sh' script that will be uploaded
            start_sh_content = \
                self._build_start_command_line(session, job_information)

            # list of files to be uploaded
            # NOTE files can also be staged-in from remote locations or can be
            # already present on the HPC filesystem
            start_sh = {'To': 'start.sh', 'Data': start_sh_content}
            inputs = [start_sh]

            # Submit the job
            self.submit(session.http_host + "/jobs",
                        job_information, job_information.auth_token, inputs)
            log.info(1, 'Job submitted to %s' % session.job_id)

            # check status
            log.info(1, self.get_properties(session.job_id,
                                            job_information.auth_token)['status'])

            # list files in job working directory
            job_information.work_dir = self.get_working_directory(
                session.job_id, job_information.auth_token)
            log.info(1, 'Working directory ' + job_information.work_dir)
            log.info(1, self.get_properties(
                job_information.work_dir + "/files",
                job_information.auth_token)['children'])

            rr_settings = \
                manager.RenderingResourceSettingsManager.get_by_id(session.renderer_id.lower())
            if rr_settings.wait_until_running:
                session.status = SESSION_STATUS_STARTING
            else:
                session.status = SESSION_STATUS_RUNNING
            session.save()
            response = json.dumps({'message': session.renderer_id + ' successfully started'})
            return [200, response]
        except RuntimeError as e:
            log.error(str(e))
            response = json.dumps({'contents': str(e)})
            return [400, response]
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
        :param session: Current user session
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
                    url = 'http://' + session.http_host + \
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
            result = self.kill(session)
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
    def kill(session):
        """
        Kills the given job. This method should only be used if the stop method failed.
        :param session: Current user session
        :return: A Json response containing on ok status or a description of the error
        """
        result = [500, 'Unexpected error']
        if session.job_id is not None:
            try:
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

    def hostname(self, session):
        """
        Returns the Job http url for the current session
        :param session: Current user session
        :return: The hostname of the host if the job is running, empty otherwise
        """
        return session.http_host

    def job_information(self, session):
        """
        Returns information about the job
        :param session: Current user session
        :return: A string containing the status of the job
        """
        return self._query(session)

    def rendering_resource_out_log(self, session, job_information):
        """
        Returns the contents of the rendering resource output file
        :param session: Current user session
        :return: A string containing the output log
        """
        return self._get_file_content(job_information.work_directory +
                                      '/files/stdout', job_information.auth_token)

    def rendering_resource_err_log(self, session, job_information):
        """
        Returns the contents of the rendering resource error file
        :param session: Current user session
        :return: A string containing the error log
        """
        return self._rendering_resource_log(settings.SLURM_ERR_FILE, job_information)

    def _get_file_content(self, file_url, headers, check_size_limit=True, max_size=2048000):
        """
        :param file_url:
        :param headers:
        :param check_size_limit:
        :param MAX_SIZE:
        :return:
        """
        if check_size_limit:
            size = self.get_properties(file_url, headers)['size']
            if size > max_size:
                raise RuntimeError("File size too large!")
        my_headers = headers.copy()
        my_headers['Accept'] = "application/octet-stream"
        r = requests.get(file_url, headers=my_headers, verify=False)
        if r.status_code != 200:
            raise RuntimeError("Error getting file data: %s" % r.status_code)
        else:
            return r.content

    def _query(self, session, attribute=None):
        """
        Queries Slurm for information
        :param session: Current user session
        :param attribute: Attribute to be queried
        :return: A Json response containing an ok status or a description of the error
        """
        if session.job_id is not None:
            try:
                return self.get_properties(session.job_id, session.auth_token)['status']
            except OSError as e:
                log.error(str(e))
                return None
        return None

    def _rendering_resource_log(self, extension, job_information):
        """
        Returns the contents of the specified file
        :param session: Current user session
        :param extension: File extension (typically err or out)
        :return: A string containing the log
        """
        if extension == 'out':
            return self._get_file_content(job_information.work_dir +
                                          '/files/stdout', job_information.auth_token)
        elif extension == 'err':
            return self._get_file_content(job_information.work_dir +
                                          '/files/stderr', job_information.auth_token)
        return 'Not currently available'
