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
from threading import Lock
import json
import re

from rendering_resource_manager_service.config.management import \
    rendering_resource_settings_manager as manager
import rendering_resource_manager_service.utils.custom_logging as log
from rendering_resource_manager_service.session.models import \
    SESSION_STATUS_STARTING, SESSION_STATUS_RUNNING, \
    SESSION_STATUS_STOPPING, SESSION_STATUS_SCHEDULED
import rendering_resource_manager_service.service.settings as global_settings


class UnicoreJobManager(object):
    """
    The job manager class provides methods for managing Unicore jobs
    """

    def __init__(self):
        """
        Setup job manager
        """
        self._mutex = Lock()
        self._base_url = None
        self._registry_url = None
        self._http_proxies = global_settings.UNICORE_DEFAULT_HTTP_PROXIES
        # TODO: Move following members to session object
        self._auth_token = None
        self._work_dir = None

    def _get_json_headers(self):
        """
        :return: headers with authorization and content-type
        """
        headers = dict()
        headers['Authorization'] = self._auth_token
        headers['Content-type'] = 'application/json'
        headers['Accept'] = 'application/json'
        return headers

    def _get_octet_stream_headers(self):
        """
        :return: headers with authorization and content-type
        """
        headers = dict()
        headers['Authorization'] = self._auth_token
        headers['Content-type'] = 'application/octet-stream'
        headers['Accept'] = 'application/octet-stream'
        return headers

    def get_sites(self):
        """
        read the base URLs of the available sites from the registry. If the registry_url is None,
        the HBP registry is used
        :return: available sites
        """
        registry_url = global_settings.UNICORE_DEFAULT_REGISTRY_URL
        r = requests.get(registry_url, proxies=self._http_proxies,
                         headers=self._get_json_headers(), verify=False)
        if r.status_code != 200:
            raise RuntimeError('Error accessing registry at %s: [%s] %s' %
                               (registry_url, r.status_code, r.reason))
        sites = {}
        for x in r.json()['entries']:
            # just want the "core" URL and the site ID
            href = x['href']
            service_type = x['type']
            if 'TargetSystemFactory' == service_type:
                base = re.match(r"(https://\S+/rest/core).*", href).group(1)
                site_name = re.match(r"https://\S+/(\S+)/rest/core", href).group(1)
                sites[site_name] = base
        log.info(1, 'Sites: ' + str(sites))
        return sites

    def get_site(self, name):
        """
        :param name: Name of the site
        :return: Description of the site
        """
        return self.get_sites().get(name, None)

    def get_properties(self, resource):
        """
        get JSON properties of a resource
        :param resource: Resource to get the properties from
        :return: Properties of the specified resource
        """
        r = requests.get(resource, proxies=self._http_proxies,
                         headers=self._get_json_headers(), verify=False)
        if r.status_code != 200:
            raise RuntimeError('Error getting properties: %s' % r.status_code)
        else:
            return r.json()

    def get_working_directory(self, job, properties=None):
        """
        Returns the URL of the working directory resource of a job
        :param job: Job
        :param properties: Properties
        :return: Working directory on remote station
        """
        if properties is None:
            properties = self.get_properties(job)
        return properties['_links']['workingDirectory']['href']

    def invoke_action(self, job_url, action, data={}):
        """
        :param job_url: Url of the job on which the action is executed
        :param action: Action to execute
        :param data: Data associated with the action
        :return:
        """
        action_url = self.get_properties(job_url)['_links']['action:' + action]['href']
        r = requests.post(action_url, proxies=self._http_proxies, data=json.dumps(data),
                          headers=self._get_json_headers(), verify=False)
        if r.status_code != 200:
            log.error(r.content)
            raise RuntimeError('Error invoking action: %s' % r.status_code)
        return r.json()

    def upload(self, destination, file_desc):
        """
        :param destination: Where to upload the file
        :param file_desc: File descriptor
        """
        name = file_desc['To']
        data = file_desc['Data']
        # TODO file_desc could refer to local file
        r = requests.put(destination + "/" + name, proxies=self._http_proxies, data=data,
                         headers=self._get_octet_stream_headers(), verify=False)
        if r.status_code != 204:
            raise RuntimeError('Error uploading data: %s' % r.status_code)

    def is_running(self, job):
        """
        Check status for a job
        :param job: Job to check
        :return:
        """
        properties = self.get_properties(job)
        status = properties['status']
        return ('SUCCESSFUL' != status) and ('FAILED' != status)

    def get_jobs(self, properties):
        """
        Get list of jobs for the current user
        :param properties: Job properties
        :return: List of jobs in a JSon representation
        """
        url = properties['_links']['jobs']['href']
        r = requests.get(url, proxies=self._http_proxies,
                         headers=self._get_json_headers(), verify=False)
        if r.status_code != 200:
            raise RuntimeError("Error getting jobs: %s" % r.status_code)
        return r.json()

    def clear_jobs(self, properties):
        """
        Clear all job placeholders a resource
        :param properties: Job properties
        """
        jobs = self.get_jobs(properties)["jobs"]
        for job in jobs:
            r = requests.delete(job, proxies=self._http_proxies,
                                headers=self._get_json_headers(), verify=False)
            if r.status_code != 200 and r.status_code != 204:
                raise RuntimeError(
                    'Error deleting jobs %s: %s' % (job, r.status_code))

    def submit(self, session, job_information):
        """
        Submits a job to the given URL, which can be the ".../jobs" URL or a ".../sites/site_name/"
        URL. If inputs is not empty, the listed input data files are uploaded to the job's working
        directory, and a "start" command is sent to the job.
        :param session: Current user session
        :param job_information: Job properties
        """
        # make sure UNICORE does not start the job before we have uploaded data
        job_information.job['haveClientStageIn'] = 'true'

        r = requests.post(self._registry_url + '/jobs',
                          proxies=self._http_proxies,
                          data=json.dumps(job_information.job),
                          headers=self._get_json_headers(), verify=False)
        log.info(1, r.content)
        if r.status_code != 201:
            obj = json.loads(r.content)
            raise RuntimeError('Error submitting job: ' + obj['errorMessage'])
        else:
            session.job_id = r.headers['Location']

        r = requests.get(session.job_id, proxies=self._http_proxies,
                         headers=self._get_json_headers(), verify=False)
        body = json.loads(r.content)
        session.job_id = body['_links']['self']['href']
        self._work_dir = body['_links']['workingDirectory']['href']

        # Build command line
        input_sh_content = \
            self._build_start_command_line(session, job_information)
        inputs = [
            {'To': 'input.sh',
             'Data': input_sh_content}
        ]

        # upload input data and explicitly start job
        for input_file in inputs:
            self.upload(self._work_dir + "/files", input_file)
        log.info(1, r.content)

    def allocate(self, session, job_information):
        """
        Allocates a job according to rendering resource configuration. If the allocation is
        successful, the session job_id is populated and the session status is set to
        SESSION_STATUS_SCHEDULED
        :param session: Current user session
        :param job_information: Information about the job
        :return: A Json response containing on ok status or a description of the error
        """
        try:
            self._mutex.acquire()
            self._registry_url = self.get_sites()[global_settings.UNICORE_DEFAULT_SITE]
            # get information about the current user, e.g.
            # role, Unix login and group(s)
            props = self.get_properties(self._registry_url)
            if not 'user' == props['client']['role']['selected']:
                log.error('Account is not registered on the selected site')
            self.clear_jobs(props)
            # setup the job - please refer to the following link
            # https://unicore-dev.zam.kfa-juelich.de/documentation/
            #   ucc-7.8.0/ucc-manual.html#ucc_jobdescription
            job_information.job = dict()

            # Use a shell script, often it is better to setup a server-side 'Application' for a
            # simulation code and invoke that
            job_information.job['ApplicationName'] = 'Bash shell'
            job_information.job['Parameters'] = {'SOURCE': 'input.sh'}
            # Request resources nodes etc
            job_information.job['Resources'] = {'Nodes': max(1, job_information.nb_nodes)}

            # Submit the job
            self.submit(session, job_information)
            session.status = SESSION_STATUS_SCHEDULED
            session.save()
            response = 'Job submitted to %s' % session.job_id
            log.info(1, response)
            return [200, response]
        except RuntimeError as e:
            log.info(1, e)
            return [403, str(e)]
        finally:
            if self._mutex.locked():
                self._mutex.release()

    def schedule(self, session, job_information, auth_token):
        """
        Allocates a job and starts the rendering resource process. If successful, the session
        job_id is populated and the session status is set to SESSION_STATUS_STARTING
        :param session: Current user session
        :param job_information: Information about the job
        :param auth_token: Token for Unicore authentication
        :return: A Json response containing on ok status or a description of the error
        """
        self._auth_token = auth_token
        return self.allocate(session, job_information)

    @staticmethod
    def _build_start_command_line(session, job_information):
        """
        Builds the command line to start the rendering resource
        :param session: Current user session
        :param job_information: Job description
        :return: Command line to start the rendering resource
        """
        rr_settings = \
            manager.RenderingResourceSettingsManager.get_by_id(session.configuration_id.lower())

        # Modules
        full_command = '"#!/bin/sh\n'
        full_command = full_command + 'HOSTNAME=$HOSTNAME\n'
        full_command = full_command + 'unset LD_LIBRARY_PATH\n'
        full_command = full_command + 'export LD_LIBRARY_PATH=/global/opt/slurm/default/lib64/\n'
        full_command = full_command + 'module use /gpfs/work/pcp0/pcp0085/x64/modulefiles\n'

        if rr_settings.modules is not None:
            values = rr_settings.modules.split()
            for module_name in values:
                full_command += 'module load ' + module_name.strip() + '\n'

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
        full_command += '\n"'
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
            self.invoke_action(session.job_id, 'start')

            rr_settings = \
                manager.RenderingResourceSettingsManager.get_by_id(session.configuration_id.lower())
            if not rr_settings.wait_until_running:
                session.status = SESSION_STATUS_RUNNING
                session.save()
            response = json.dumps({'message': session.configuration_id + ' successfully started'})
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
            self._work_dir = None
            self._mutex.acquire()
            session.status = SESSION_STATUS_STOPPING
            session.save()

            # make sure UNICORE does not start the job before we have uploaded data
            r = requests.delete(session.job_id, proxies=self._http_proxies,
                                headers=self._get_json_headers(), verify=False)
            log.info(1, r.content)
            if r.status_code != 204:
                message = str(r.status_code)
                if r.content != '':
                    obj = json.loads(r.content)
                    message = obj['errorMessage']
                raise RuntimeError('Error deleting job: ' + message)
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
        value = ''
        r = requests.get(session.job_id, proxies=self._http_proxies,
                         headers=self._get_json_headers(), verify=False)
        try:
            if r.content == '':
                return value
            obj = json.loads(r.content)
            log.info(1, str(obj))
            status = obj['status']
            log.info(1, 'Unicore job status is ' + str(status))
            if status == 'READY':
                self.start(session, None)
            elif status == 'SUCCESSFUL' or status == 'FAILED':
                self.stop(session)
            else:
                # TODO: CHANGE TO STDOUT when Renderer is deployed on the cluster
                log_file = self._get_file_content(self._work_dir + '/files/stderr')
                if log_file is not None:
                    try:
                        log.info(1, 'Log: ' + log_file)
                        value = re.search(r'HOSTNAME=(\w+)', log_file).group(1)
                        log.info(1, 'HOSTNAME=' + str(value))
                        session.status = SESSION_STATUS_STARTING
                        session.save()
                    except AttributeError as e:
                        value = ''
        except KeyError as e:
            log.error(e)
        return value

    def job_information(self, session):
        """
        Returns information about the job
        :param session: Current user session
        :return: A string containing the status of the job
        """
        return self._query(session)

    def rendering_resource_out_log(self, session):
        """
        Returns the contents of the rendering resource output file
        :param session: Current user session
        :return: A string containing the output log
        """
        return self._get_file_content(self._work_dir + '/files/stdout')

    def rendering_resource_err_log(self, session):
        """
        Returns the contents of the rendering resource error file
        :param session: Current user session
        :return: A string containing the error log
        """
        return self._get_file_content(self._work_dir + '/files/stdout')

    def _get_file_content(self, file_url, check_size_limit=True, max_size=2048000):
        """
        Returns the contents of a file stored on the Unicore file system
        :param file_url: URL of the file
        :param check_size_limit: Check size limit before download
        :param max_size: The maximum size of the file
        :return: The contents of the remote file
        """
        try:
            log.info(2, 'Getting file content from ' + file_url)
            if check_size_limit:
                size = self.get_properties(file_url)['size']
                if size > max_size:
                    raise RuntimeError('File size too large!')
            r = requests.get(file_url, proxies=self._http_proxies,
                             headers=self._get_octet_stream_headers(), verify=False)
            if r.status_code == 200:
                return r.content
        except RuntimeError as e:
            log.error(e)
        return None

    def _query(self, session, attribute=None):
        """
        Queries Unicore for information
        :param session: Current user session
        :param attribute: Attribute to be queried
        :return: A Json response containing an ok status or a description of the error
        """
        if session.job_id is not None and attribute is not None:
            try:
                return self.get_properties(session.job_id)[attribute]
            except OSError as e:
                log.error(str(e))
                return None
        return None
