#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=W0403
# pylint: disable=E1101
# pylint: disable=R0901

"""
This modules defines the data structure used by the rendering resource manager to manager
user session
"""
import urllib2
import random
import json
import traceback

from rest_framework import serializers, viewsets
from django.http import HttpResponse
import management.session_manager_settings as consts
import rendering_resource_manager_service.utils.custom_logging as log
from rendering_resource_manager_service.session.models import Session
from rendering_resource_manager_service.session.management import job_manager
from rendering_resource_manager_service.session.management import process_manager
import management.session_manager as session_manager


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
        status = sm.delete_session(session_id)
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
            sm = session_manager.SessionManager()
            session_id = sm.get_session_id_from_request(request)
            log.debug(1, 'Processing command <' + command + '> for session ' + str(session_id))
            session = Session.objects.get(id=session_id)
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
            log.debug(1, 'Executing command <' + command + '> parameters=' + str(parameters) +
                      ' environment=' + str(environment))

            response = None
            if command == 'schedule':
                response = cls.__schedule_job(session, parameters, environment)
            elif command == 'open':
                response = cls.__open_process(session, parameters, environment)
            elif command == 'status':
                status = cls.__session_status(session)
                response = HttpResponse(status=status[0], content=status[1])
            elif command == 'log':
                status = cls.__rendering_resource_log(session)
                response = HttpResponse(status=status[0], content=status[1])
            else:
                response = cls.__forward_request(session, command, request)
            return response
        except KeyError as e:
            log.debug(1, str(traceback.format_exc(e)))
            return HttpResponse(status=404, content='Cookie ' + str(e) + ' is missing')
        except Session.DoesNotExist as e:
            log.debug(1, str(traceback.format_exc(e)))
            return HttpResponse(status=404,
                                content='Session does not exist')
        except Exception as e:
            log.error(str(traceback.format_exc(e)))
            return HttpResponse(status=500, content=str(traceback.format_exc(e)))

    @classmethod
    def __schedule_job(cls, session, parameters, environment):
        """
        Starts a rendering resource by scheduling a slurm job
        :param : session: Session holding the rendering resource
        :param : parameters: Parameters passed in the HTTP request
        :rtype : An HTTP response containing the status and description of the command
        """
        session.http_host = ''
        session.http_port = consts.DEFAULT_RENDERER_HTTP_PORT + random.randint(0, 1000)
        status = job_manager.globalJobManager.schedule(session, parameters, environment)
        return HttpResponse(status=status[0], content=status[1])

    @classmethod
    def __open_process(cls, session, parameters, environment):
        """
        Starts a local rendering resource process
        :param : session: Session holding the rendering resource
        :param : parameters: Parameters passed in the HTTP request
        :rtype : An HTTP response containing the status and description of the command
        """
        log.info(1, 'Opening ' + session.renderer_id)
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
            return HttpResponse(status=401, content=msg)

    @classmethod
    def __get_request_headers(cls, request):
        """
        Reads headers from given http request and returns them as a dictionary
        :param request: HTTP request to be processed
        :return: Dictionary of header values
        """
        def format_header_name(name):
            """
            Formats an http parameters to suit dictionaries requirements
            :param name: name of the http parameter
            :return: Formatted header parameter
            """
            return "-".join([x[0].upper() + x[1:] for x in name[5:].lower().split("_")])
        headers = dict([(format_header_name(k), v) for k, v in request.META.items()
                        if k.startswith("HTTP_")])
        headers["Cookie"] = "; ".join([k + "=" + v for k, v in request.COOKIES.items()])
        return headers

    @classmethod
    def __verify_hostname(cls, session):
        """
        Verify the existence of an hostname for the current session, and tries
        to populate it if null
        :param : session: Session holding the rendering resource
        """
        if session.job_id and session.http_host == '':
            log.debug(1, 'Querying JOB hostname for job id: ' + str(session.job_id))
            hostname = job_manager.JobManager.hostname(session.job_id)
            if hostname == '':
                msg = 'Job scheduled but ' + session.renderer_id + ' is not yet running'
                log.error(msg)
                return [404, msg]
            elif hostname == 'FAILED':
                sm = session_manager.SessionManager()
                sm.delete_session(session.id)
                return [404, 'Job as been cancelled']
            else:
                session.http_host = hostname
                msg = 'Resolved hostname for job ' + str(session.job_id) + ' to ' +\
                      str(session.http_host)
                log.info(1, msg)
                session.save()
                return [200, msg]
        return [200, 'Job is running on host ' + session.http_host]

    @classmethod
    def __rendering_resource_log(cls, session):
        """
        Forwards the HTTP request to the rendering resource held by the given session
        :param : session: Session holding the rendering resource
        :rtype : An HTTP response containing the status and description of the command
        """
        # check if the hostname of the rendering resource is currently available
        contents = ''
        if session.job_id:
            contents = job_manager.globalJobManager.rendering_resource_log(session)
        return [200, contents]

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

        url = ''
        try:
            # Any other command is forwarded to the rendering resource
            url = 'http://' + session.http_host + ':' + str(session.http_port) + '/' + command
            log.info(1, 'Querying ' + str(url))
            headers = cls.__get_request_headers(request)

            input_data = None
            if request.DATA:
                input_data = json.dumps(request.DATA)
            req = urllib2.Request(url=url, headers=headers, data=input_data)
            req.get_method = lambda: request.method
            response = urllib2.urlopen(req)

            # Response processing
            data_size = int(response.headers['content-length'])
            log.debug(1, 'Reading bytes ' + str(data_size) + ' bytes')
            data = response.read()
            response.close()

            # Make sure that the number of received bytes is correct
            missing_bytes = int(response.headers['content-length']) - len(data)
            if missing_bytes != 0:
                msg = 'Missing bytes:  ' + str(missing_bytes)
                log.error(msg)
                return HttpResponse(status=400, content=msg)
            else:
                return HttpResponse(status=200, content=data)
        except urllib2.URLError as e:
            # Check that job or process is still running
            if session.job_id:
                if job_manager.globalJobManager.hostname(session.job_id) == 'FAILED':
                    session_manager.SessionManager.delete_session(session.id)
                    return HttpResponse(status=400,
                                        content=session.renderer_id + ' is down')
            else:
                msg = str(traceback.format_exc(e))
                log.debug(1, msg)
                return HttpResponse(status=400,
                                    content='Failed to contact rendering resource: ' + url)
