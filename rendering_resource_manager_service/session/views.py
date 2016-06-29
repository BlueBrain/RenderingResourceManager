#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=W0403
# pylint: disable=E1101
# pylint: disable=R0901
# pylint: disable=R0915

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
This modules defines the data structure used by the rendering resource manager to manager
user session
"""
import requests
import random
import json
import traceback

from rest_framework import serializers, viewsets
from django.http import HttpResponse
import management.session_manager_settings as consts
import rendering_resource_manager_service.service.settings as settings
import rendering_resource_manager_service.utils.custom_logging as log
import rendering_resource_manager_service.utils.tools as tools
from rendering_resource_manager_service.session.models import Session
from rendering_resource_manager_service.session.management import job_manager
from rendering_resource_manager_service.session.management import process_manager
from rendering_resource_manager_service.session.management import image_feed_manager
import management.session_manager as session_manager
from rendering_resource_manager_service.session.models import \
    SESSION_STATUS_GETTING_HOSTNAME, SESSION_STATUS_SCHEDULED


class SessionSerializer(serializers.ModelSerializer):
    """
    Serializer to session data
    """

    def __len__(self):
        pass

    def __getitem__(self, item):
        pass

    class Meta(object):
        """
        Meta class for the Session Serializer
        """
        model = Session
        fields = ('owner', 'renderer_id')


class SessionDetailsSerializer(serializers.ModelSerializer):
    """
    Serializer to session data
    """

    def __len__(self):
        pass

    def __getitem__(self, item):
        pass

    class Meta(object):
        """
        Meta class for the Session Serializer
        """
        model = Session
        fields = ('owner', 'created', 'renderer_id', 'job_id', 'status',
                  'http_host', 'http_port', 'valid_until')


class CommandSerializer(serializers.ModelSerializer):
    """
    Serializer to command data
    """
    def __len__(self):
        pass

    def __getitem__(self, item):
        pass

    class Meta(object):
        """
        Meta class for the Command Serializer
        """
        model = Session
        fields = ('parameters', )


class DefaultSerializer(serializers.ModelSerializer):
    """
    Serializer to default view (No parameters)
    """
    def __len__(self):
        pass

    def __getitem__(self, item):
        pass

    class Meta(object):
        """
        Meta class for the Command Serializer
        """
        model = Session
        fields = ('created',)


class KeepAliveSerializer(serializers.ModelSerializer):
    """
    Serializer to default view (No parameters)
    """
    def __len__(self):
        pass

    def __getitem__(self, item):
        pass

    class Meta(object):
        """
        Meta class for the Command Serializer
        """
        model = Session
        fields = ('status', )


class SessionDetailsViewSet(viewsets.ModelViewSet):
    """
    Displays all attributes of the current session
    """
    queryset = Session.objects.all()
    serializer_class = SessionDetailsSerializer

    @classmethod
    def get_session(cls, request, pk):
        """
        Retrieves a user session
        :param : request: The REST request
        :rtype : A Json response containing on ok status or a description of the error
        """
        sm = session_manager.SessionManager()
        status = sm.get_session(pk, request, SessionSerializer)
        return HttpResponse(status=status[0], content=status[1])


class SessionViewSet(viewsets.ModelViewSet):
    """
    Displays a minimal set of information related to a given session
    """

    queryset = Session.objects.all()
    serializer_class = SessionSerializer

    @classmethod
    def create_session(cls, request):
        """
        Creates a user session
        :param : request: request containing the launching parameters of the rendering resource
        :rtype : An HTTP response containing on ok status or a description of the error
        """
        sm = session_manager.SessionManager()
        # Create new Cookie ID for new session
        session_id = sm.get_session_id()
        try:
            status = sm.create_session(
                session_id, request.DATA['owner'], request.DATA['renderer_id'])
            response = HttpResponse(status=status[0], content=status[1])
            response.set_cookie(consts.COOKIE_ID, session_id)
            log.info(1, 'Session created ' + str(session_id))
            return response
        except KeyError as e:
            return HttpResponse(status=401, content=str(e))
        else:
            return HttpResponse(status=401, content='Unexpected exception')

    @classmethod
    # pylint: disable=W0613
    def list_sessions(cls, request):
        """
        List all session
        :param : request: request containing the launching parameters of the rendering resource
        :rtype : An HTTP response containing on ok status or a description of the error
        """
        sm = session_manager.SessionManager()
        status = sm.list_sessions(SessionSerializer)
        return HttpResponse(status=status[0], content=status[1])

    @classmethod
    def destroy_session(cls, request):
        """
        Stops the renderer and destroys the user session
        :param : request: The REST request
        :rtype : An HTTP response containing on ok status or a description of the error
        """
        sm = session_manager.SessionManager()
        session_id = sm.get_session_id_from_request(request)
        log.info(1, 'Remove image feed route if it exists')
        ifm = image_feed_manager.ImageFeedManager(session_id)
        status = ifm.remove_route()
        if status[0] != 200:
            log.error(status[1])
        log.info(1, 'Remove session from db')
        status = sm.delete_session(session_id)
        log.info(1, 'Session deleted ' + str(session_id))
        return HttpResponse(status=status[0], content=status[1])


class CommandViewSet(viewsets.ModelViewSet):
    """
    ViewSets define the view behavior
    """

    queryset = Session.objects.all()
    serializer_class = CommandSerializer

    @classmethod
    def execute(cls, request, command):
        """
        Executes a command on the rendering resource
        :param : request: The REST request
        :param : command: Command to be executed on the rendering resource
        :rtype : A Json response containing on ok status or a description of the error
        """
        # pylint: disable=R0912
        try:
            session_id = session_manager.SessionManager().get_session_id_from_request(request)
            log.debug(1, 'Processing command <' + command + '> for session ' + str(session_id))
            session = Session.objects.get(id=session_id)
            response = None
            if command == 'schedule':
                response = cls.__schedule_job(session, request)
            elif command == 'open':
                response = cls.__open_process(session, request)
            elif command == 'status':
                status = cls.__session_status(session)
                response = HttpResponse(status=status[0], content=status[1])
            elif command == 'log':
                status = cls.__rendering_resource_out_log(session)
                response = HttpResponse(status=status[0], content=status[1])
            elif command == 'err':
                status = cls.__rendering_resource_err_log(session)
                response = HttpResponse(status=status[0], content=status[1])

            elif command == 'job':
                status = cls.__job_information(session)
                response = HttpResponse(status=status[0], content=status[1])
            elif command == 'imagefeed':
                status = cls.__image_feed(session_id)
                response = HttpResponse(status=status[0], content=status[1])
            else:
                url = request.get_full_path()
                prefix = settings.BASE_URL_PREFIX + '/session/'
                cmd = url[url.find(prefix) + len(prefix) + 1: len(url)]
                response = cls.__forward_request(session, cmd, request)
            return response
        except KeyError as e:
            log.debug(1, str(traceback.format_exc(e)))
            response = json.dumps({'contents': 'Cookie ' + str(e) + ' is missing'})
            return HttpResponse(status=404, content=response)
        except Session.DoesNotExist as e:
            log.debug(1, str(traceback.format_exc(e)))
            response = json.dumps({'contents': 'Session does not exist'})
            return HttpResponse(status=404, content=response)
        except Exception as e:
            msg = traceback.format_exc(e)
            log.error(str(msg))
            response = json.dumps({'contents': str(msg)})
            return HttpResponse(status=500, content=response)

    @classmethod
    def __schedule_job(cls, session, request):
        """
        Starts a rendering resource by scheduling a slurm job
        :param : session: Session holding the rendering resource
        :param : request: HTTP request with a body containing a JSON representation of the job
                 parameters
        :rtype : An HTTP response containing the status and description of the command
        """
        job_information = job_manager.JobInformation()
        try:
            job_information.params = request.DATA['params']
        except KeyError:
            log.debug(1, 'No parameters specified')

        try:
            job_information.environment = request.DATA['environment']
        except KeyError:
            log.debug(1, 'No environment specified')

        try:
            job_information.reservation_name = request.DATA['reservation_name']
        except KeyError:
            log.debug(1, 'No reservation name specified')

        try:
            job_information.queue_name = request.DATA['queue_name']
        except KeyError:
            log.debug(1, 'No queue name specified')

        try:
            job_information.exclusive_allocation = \
                request.DATA['exclusive_allocation']
        except KeyError:
            log.debug(1, 'No exclusive allocation specified')

        session.http_host = ''
        session.http_port = consts.DEFAULT_RENDERER_HTTP_PORT + random.randint(0, 1000)
        status = job_manager.globalJobManager.schedule(
            session, job_information)
        return HttpResponse(status=status[0], content=status[1])

    @classmethod
    def __open_process(cls, session, request):
        """
        Starts a local rendering resource process
        :param : session: Session holding the rendering resource
        :param : request: HTTP request with a body containing a JSON representation of the process
                 parameters
        :rtype : An HTTP response containing the status and description of the command
        """
        parameters = ''
        try:
            parameters = request.DATA['params']
        except KeyError:
            log.debug(1, 'No parameters specified')

        environment = ''
        try:
            environment = request.DATA['environment']
        except KeyError:
            log.debug(1, 'No environment specified')

        log.debug(1, 'Executing command <Open> parameters=' + str(parameters) +
                  ' environment=' + str(environment))

        if session.process_pid == -1:
            session.http_host = consts.DEFAULT_RENDERER_HOST
            session.http_port = consts.DEFAULT_RENDERER_HTTP_PORT + random.randint(0, 1000)
            pm = process_manager.ProcessManager
            status = pm.start(session, parameters, environment)
            session.save()
            return HttpResponse(status=status[0], content=status[1])
        else:
            msg = 'process is already started'
            log.error(msg)
            response = json.dumps({'contents': str(msg)})
            return HttpResponse(status=401, content=response)

    @classmethod
    def __verify_hostname(cls, session):
        """
        Verify the existence of an hostname for the current session, and tries
        to populate it if null
        :param : session: Session holding the rendering resource
        """
        log.info(1, 'Verifying hostname ' + session.http_host + ' for session ' + str(session.id))
        if not session.status == SESSION_STATUS_GETTING_HOSTNAME and \
                session.job_id and session.http_host == '':
            session.status = SESSION_STATUS_GETTING_HOSTNAME
            session.save()
            log.info(1, 'Querying JOB hostname for job id: ' + str(session.job_id))
            hostname = job_manager.JobManager.hostname(session.job_id)
            if hostname == '':
                msg = 'Job scheduled but ' + session.renderer_id + ' is not yet running'
                log.error(msg)
                session.status = SESSION_STATUS_SCHEDULED
                session.save()
                response = json.dumps({'contents': str(msg)})
                return [404, response]
            elif hostname == 'FAILED':
                sm = session_manager.SessionManager()
                sm.delete_session(session.id)
                msg = 'Job as been cancelled'
                log.error(msg)
                response = json.dumps({'contents': str(msg)})
                return [404, response]
            else:
                session.http_host = hostname
                session.save()
                msg = 'Resolved hostname for job ' + str(session.job_id) + ' to ' + \
                      str(session.http_host)
                log.info(1, msg)
                response = json.dumps({'contents': str(msg)})
                return [200, response]
        response = json.dumps({'contents': str('Job is running on host ' + session.http_host)})
        return [200, response]

    @classmethod
    def __rendering_resource_out_log(cls, session):
        """
        Forwards the HTTP request to the rendering resource held by the given session
        :param : session: Session holding the rendering resource
        :rtype : An HTTP response containing the status and description of the command
        """
        # check if the hostname of the rendering resource is currently available
        contents = 'Rendering resource is currently unavailable'
        if session.job_id:
            contents = job_manager.globalJobManager.rendering_resource_out_log(session)
        response = json.dumps({'contents': str(contents)})
        return [200, response]

    @classmethod
    def __rendering_resource_err_log(cls, session):
        """
        Forwards the HTTP request to the rendering resource held by the given session
        :param : session: Session holding the rendering resource
        :rtype : An HTTP response containing the status and description of the command
        """
        # check if the hostname of the rendering resource is currently available
        contents = 'Rendering resource is currently unavailable'
        if session.job_id:
            contents = job_manager.globalJobManager.rendering_resource_err_log(session)
        response = json.dumps({'contents': str(contents)})
        return [200, response]

    @classmethod
    def __job_information(cls, session):
        """
        Forwards the HTTP request to the rendering resource held by the given session
        :param : session: Session holding the rendering resource
        :rtype : An HTTP response containing the status and description of the command
        """
        # check if the hostname of the rendering resource is currently available
        contents = 'Rendering resource is currently unavailable'
        if session.job_id:
            contents = job_manager.globalJobManager.job_information(session)
        response = json.dumps({'contents': str(contents)})
        return [200, response]

    @classmethod
    def __session_status(cls, session):
        """
        Forwards the HTTP request to the rendering resource held by the given session
        :param : session: Session holding the rendering resource
        :param : command: Command passed to the rendering resource
        :param : request: HTTP request
        :rtype : An HTTP response containing the status and description of the command
        """
        # check if the hostname of the rendering resource is currently available
        status = cls.__verify_hostname(session)
        if status[0] != 200:
            return status

        # query the status of the current session
        status = session_manager.SessionManager.query_status(session.id)
        if status[0] == 200:
            return status
        else:
            msg = 'Rendering resource is not yet available: ' + status[1]
            log.debug(1, msg)
            return status

    @classmethod
    def __image_feed(cls, session_id):
        """
        Get the route to image streaming server
        :param : session_id: Id of the session holding the rendering resource
        :rtype : An HTTP response containing uri of the image streaming server for the given session
        """
        log.info(1, 'Requesting image feed')
        ifm = image_feed_manager.ImageFeedManager(session_id)
        return ifm.get_route()

    @classmethod
    def __forward_request(cls, session, command, request):
        """
        Forwards the HTTP request to the rendering resource held by the given session
        :param : session: Session holding the rendering resource
        :param : command: Command passed to the rendering resource
        :param : request: HTTP request
        :rtype : An HTTP response containing the status and description of the command
        """
        # query the status of the current session
        status = cls.__session_status(session)
        if status[0] != 200:
            return HttpResponse(status=status[0], content=status[1])

        try:
            # Any other command is forwarded to the rendering resource
            url = 'http://' + session.http_host + ':' + str(session.http_port) + '/' + command
            log.info(1, 'Querying ' + str(url))
            headers = tools.get_request_headers(request)

            input_data = None
            if request.DATA:
                input_data = json.dumps(request.DATA)
            response = requests.request(
                method=request.method, timeout=settings.REQUEST_TIMEOUT,
                url=url, headers=headers, data=input_data)

            data = response.content
            response.close()
            return HttpResponse(status=response.status_code, content=data)
        except requests.exceptions.RequestException as e:
            response = json.dumps({'contents': str(e)})
            return HttpResponse(status=400, content=response)
