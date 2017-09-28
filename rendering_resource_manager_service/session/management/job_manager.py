#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
    SESSION_STATUS_SCHEDULING, SESSION_STATUS_SCHEDULED, SESSION_STATUS_FAILED
import rendering_resource_manager_service.service.settings as global_settings

_HBP_REGISTRY_URL = "https://hbp-unic.fz-juelich.de:7112/HBP/rest/registries/default_registry"


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
        self.nb_cpus = 0
        self.nb_gpus = 0
        self.nb_nodes = 0
        self.memory = 0
        self.queue = ''
        self.allocation_time = ''


class UnicoreJobManager(object):
    """
    The job manager class provides methods for managing slurm jobs
    """

    def __init__(self):
        """
        Setup job manager
        """
        self._mutex = Lock()

    @classmethod
    def get_sites(self, registry_url=None, headers={}):
        """
        read the base URLs of the available sites from the registry. If the registry_url is None,
        the HBP registry is used
        :param registry_url:
        :param headers:
        :return: available sites
        """
        if registry_url is None:
            registry_url = _HBP_REGISTRY_URL
        my_headers = headers.copy()
        my_headers['Accept'] = "application/json"
        r = requests.get(registry_url, headers=my_headers, verify=False)
        if r.status_code != 200:
            raise RuntimeError("Error accessing registry at %s: %s" % (registry_url, r.status_code))
        sites = {}
        for x in r.json()['entries']:
            try:
                # just want the "core" URL and the site ID
                href = x['href']
                service_type = x['type']
                if "TargetSystemFactory" == service_type:
                    base = re.match(r"(https://\S+/rest/core).*", href).group(1)
                    site_name = re.match(r"https://\S+/(\S+)/rest/core", href).group(1)
                    sites[site_name] = base
            except Exception as e:
                print(e)
        return sites

    @classmethod
    def get_site(self, name, headers=[]):
        """
        :param name:
        :param headers:
        :return:
        """
        return self.get_sites(headers=headers).get(name, None)

    @classmethod
    def get_properties(self, resource, headers={}):
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

    @classmethod
    def get_working_directory(self, job, headers={}, properties=None):
        """
        Returns the URL of the working directory resource of a job
        :param headers: Headers
        :param properties: Properties
        :return: Working directory on remote station
        """
        if properties is None:
            properties = self.get_properties(job, headers)
        return properties['_links']['workingDirectory']['href']

    @classmethod
    def invoke_action(self, resource, action, headers, data={}):
        """
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

    @classmethod
    def upload(self, destination, file_desc, headers):
        """
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

    @classmethod
    def schedule(self, session, job_information):
        """
        Allocates a job and starts the rendering resource process. If successful, the session
        job_id is populated and the session status is set to SESSION_STATUS_STARTING
        :param session: Current user session
        :param job_information: Information about the job
        :return: A Json response containing on ok status or a description of the error
        """
        status = self.allocate(session, job_information)
        if status[0] == 200:
            session.http_host = self.hostname(session)
            status = self.start(session, job_information)
        return status

    @classmethod
    def submit(self, url, job, headers, inputs=[]):
        """
        Submits a job to the given URL, which can be the ".../jobs" URL or a ".../sites/site_name/"
        URL. If inputs is not empty, the listed input data files are uploaded to the job's working
        directory, and a "start" command is sent to the job.
        """
        my_headers = headers.copy()
        my_headers['Content-Type'] = "application/json"
        if len(inputs) > 0:
            # make sure UNICORE does not start the job
            # before we have uploaded data
            job['haveClientStageIn'] = 'true'

        r = requests.post(url, data=json.dumps(job), headers=my_headers, verify=False)
        print(r.content)
        if r.status_code != 201:
            raise RuntimeError("Error submitting job: %s" % r.status_code)
        else:
            jobURL = r.headers['Location']

        # upload input data and explicitly start job
        if len(inputs) > 0:
            working_directory = self.get_working_directory(jobURL, headers)
            for input in inputs:
                self.upload(working_directory + "/files", input, headers)
            self.invoke_action(jobURL, "start", headers)

        return jobURL

    @classmethod
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

    @classmethod
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

    @classmethod
    def get_oidc_auth(self):
        """ returns HTTP headers containing OIDC bearer token """
        # hdr = get_bbp_client().task.oauth_client.get_auth_header()
        from bbp_client.client import get_services
        from bbp_client.oidc.client import BBPOIDCClient
        import os
        services = get_services()
        oauth_url = services['oidc_service']['prod']['url']
        user = os.environ['USER']
        oidc = BBPOIDCClient.implicit_auth(user=user, oauth_url=oauth_url)
        hdr = oidc.get_auth_header()
        return {'Authorization': hdr}

    def allocate(self, session, job_information):
        """
        Allocates a job according to rendering resource configuration. If the allocation is
        successful, the session job_id is populated and the session status is set to
        SESSION_STATUS_SCHEDULED
        :param session: Current user session
        :param job_information: Information about the job
        :return: A Json response containing on ok status or a description of the error
        """
        status = None
        auth = self.get_oidc_auth()
        base_url = self.get_sites(headers=auth)['HBP_JURECA']
        # get information about the current user, e.g.
        # role, Unix login and group(s)
        props = self.get_properties(base_url, auth)
        if not 'user' == props['client']['role']['selected']:
            log.error('Account is not registered on the selected site')
            self.clear_jobs(props, auth)
        # setup the job - please refer to
        # http://unicore.eu/documentation/manuals/unicore/files/ucc/ucc-manual.html
        # for more options
        job = {}

        # Use a shell script, often it is better to setup a server-side 'Application' for a
        # simulation code and invoke that
        job['ApplicationName'] = 'test'
        job['Executable'] = '/bin/date'
        job['Parameters'] = {'SOURCE': 'input.sh'}
        # Request resources nodes etc
        # job['Resources'] = {'Nodes': '1'}

        # the 'input.sh' script that will be uploaded
        input_sh_content = '"#!/bin/sh\ndate\nhostname\nwhoami\n"'

        # list of files to be uploaded
        # NOTE files can also be staged-in from remote locations or can be already present on the
        # HPC filesystem
        input_sh = {'To': 'input.sh', 'Data': input_sh_content}
        inputs = [input_sh]

        # Submit the job
        job_url = self.submit(base_url + "/jobs", job, auth, inputs)
        log.info(1, 'Job submitted to %s' % job_url)

        # check status
        log.info(1, self.get_properties(job_url, auth)['status'])

        # list files in job working directory
        work_dir = self.get_working_directory(job_url, auth)
        log.info(1, 'Working directory ' + work_dir)
        log.info(1, self.get_properties(work_dir + "/files", auth)['children'])

        # we can also wait for the job to finish
        self.wait_for_completion(job_url, auth)
        log.info(1, self.get_properties(job_url, auth)['status'])

        # list files in job working directory
        work_dir = self.get_working_directory(job_url, auth)
        log.info(1, self.get_properties(work_dir + "/files", auth)['children'])

        # download and show stdout
        log.info(1, self.get_file_content(work_dir + "/files" + "/stdout", auth))

        return status

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

            rr_settings = \
                manager.RenderingResourceSettingsManager.get_by_id(session.renderer_id.lower())

            # Modules
            full_command = 'module purge\n'
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

            # Output redirection
            full_command += ' > ' + self._file_name(session, settings.SLURM_OUT_FILE)
            full_command += ' 2> ' + self._file_name(session, settings.SLURM_ERR_FILE)
            full_command += ' &\n'

            # Start Process on cluster
            command_line = '/usr/bin/ssh -i ' + \
                           global_settings.SLURM_SSH_KEY + ' ' + \
                           global_settings.SLURM_USERNAME + '@' + \
                           session.http_host

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

            if rr_settings.wait_until_running:
                session.status = SESSION_STATUS_STARTING
            else:
                session.status = SESSION_STATUS_RUNNING
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
                command_line = SLURM_SSH_COMMAND + session.cluster_node + \
                               ' scancel ' + session.job_id
                log.info(1, 'Stopping job ' + session.job_id)
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

    def hostname(self, session):
        """
        Retrieve the hostname for the host of the given job is allocated.
        Note: this uses ssh and scontrol on the SLURM_HOST
        :param session: Current user session
        :return: The hostname of the host if the job is running, empty otherwise
        """
        hostname = self._query(session, 'BatchHost')
        if hostname != '':
            hostname = hostname + '.' + str(session.cluster_node.partition('.')[2])
        return hostname

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
        return self._rendering_resource_log(session, settings.SLURM_OUT_FILE)

    def rendering_resource_err_log(self, session):
        """
        Returns the contents of the rendering resource error file
        :param session: Current user session
        :return: A string containing the error log
        """
        return self._rendering_resource_log(session, settings.SLURM_ERR_FILE)

    @staticmethod
    def _query(session, attribute=None):
        """
        Queries Slurm for information
        :param session: Current user session
        :param attribute: Attribute to be queried
        :return: A Json response containing an ok status or a description of the error
        """
        value = ''
        if session.job_id is not None:
            try:
                command_line = SLURM_SSH_COMMAND + session.cluster_node + \
                               ' scontrol show job ' + str(session.job_id)
                process = subprocess.Popen(
                    [command_line],
                    shell=True,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE)
                output = process.communicate()[0]
                if attribute is None:
                    return output
                status = re.search(r'JobState=(\w+)', output).group(1)
                if status != 'CANCELLED':
                    value = re.search(attribute + r'=(\w+)', output).group(1)
                    log.info(1, attribute + ' = ' + value)
                log.info(1, 'Job status: ' + status + ' hostname: ' + value)
                return value
            except OSError as e:
                log.error(str(e))
        return value

    @staticmethod
    def _file_name(session, extension):
        """
        Returns the contents of the log file with the specified extension
        :param session: Current user session
        :param extension: file extension (typically err or out)
        :return: A string containing the error log
        """
        return settings.SLURM_OUTPUT_PREFIX + '_' + str(session.job_id) + \
               '_' + session.renderer_id + '_' + extension

    def _rendering_resource_log(self, session, extension):
        """
        Returns the contents of the specified file
        :param session: Current user session
        :param extension: File extension (typically err or out)
        :return: A string containing the log
        """
        try:
            result = 'Not currently available'
            if session.status in [SESSION_STATUS_STARTING, SESSION_STATUS_RUNNING]:
                filename = self._file_name(session, extension)
                command_line = SLURM_SSH_COMMAND + session.cluster_node + \
                               ' cat ' + filename
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

    @staticmethod
    def _build_allocation_command(session, job_information):
        """
        Builds the SLURM allocation command line
        :param session: Current user session
        :param job_information: Information about the job
        :return: A string containing the SLURM command
        """

        rr_settings = \
            manager.RenderingResourceSettingsManager.get_by_id(session.renderer_id.lower())

        options = ''
        if job_information.exclusive_allocation or rr_settings.exclusive:
            options += ' --exclusive'

        value = rr_settings.nb_nodes
        if job_information.nb_nodes != 0:
            value = job_information.nb_nodes
        if value != 0:
            options += ' -N ' + str(value)

        value = rr_settings.nb_cpus
        if job_information.nb_cpus != 0:
            value = job_information.nb_cpus
        options += ' -c ' + str(value)

        value = rr_settings.nb_gpus
        if job_information.nb_gpus != 0:
            value = job_information.nb_gpus
        options += ' --gres=gpu:' + str(value)

        value = rr_settings.memory
        if job_information.memory != 0:
            value = job_information.memory
        options += ' --mem=' + str(value)

        if job_information.reservation != '' and job_information.reservation is not None:
            options += ' --reservation=' + job_information.reservation

        allocation_time = global_settings.SLURM_DEFAULT_TIME
        if job_information.allocation_time != '':
            allocation_time = job_information.allocation_time

        log.info(1, 'Scheduling job for session ' + session.id)

        job_name = session.owner + '_' + rr_settings.id
        command_line = SLURM_SSH_COMMAND + session.cluster_node + \
                       ' salloc --no-shell' + \
                       ' --immediate=' + str(settings.SLURM_ALLOCATION_TIMEOUT) + \
                       ' -p ' + rr_settings.queue + \
                       ' --account=' + rr_settings.project + \
                       ' --job-name=' + job_name + \
                       ' --time=' + allocation_time + \
                       options
        return command_line


# Global job manager used for all allocations
globalUnicoreJobManager = UnicoreJobManager()
