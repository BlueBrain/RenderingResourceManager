#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=E1101
# pylint: disable=W0403

"""
This class is in charge of handling session and ensures persistent storage in a database
"""

import urllib2
import datetime
import uuid
import json

from django.db import IntegrityError, transaction
from django.http import HttpResponse
from rendering_resource_manager_service.config.models import SystemGlobalSettings
from rendering_resource_manager_service.session.models import Session, \
    SESSION_STATUS_STOPPED, SESSION_STATUS_SCHEDULED, SESSION_STATUS_STARTING, \
    SESSION_STATUS_RUNNING, SESSION_STATUS_STOPPING
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
import rendering_resource_manager_service.utils.custom_logging as log
import rendering_resource_manager_service.session.management.session_manager_settings as consts
from rendering_resource_manager_service.session.management import keep_alive_thread
import job_manager
import process_manager

HTTP_STATUS_ERROR = 503


class JSONResponse(HttpResponse):
    """
    This class constructs HTTP response with JSON formatted body
    """
    def __len__(self):
        pass

    def __getitem__(self, item):
        pass

    def __init__(self, data, **kwargs):
        content = JSONRenderer().render(data)
        kwargs['content_type'] = 'application/json'
        super(JSONResponse, self).__init__(content, **kwargs)


class SessionManager(object):
    """
    This class is in charge of handling session and ensures persistent storage in a database
    """

    def __init__(self):
        """
        Initializes the SessionManager class and creates the global config if
        they do not already exist in the database
        """
        try:
            SystemGlobalSettings.objects.get(id=0)
        except SystemGlobalSettings.DoesNotExist:
            sgs = SystemGlobalSettings(
                id=0,
                session_creation=True,
                session_keep_alive_timeout=keep_alive_thread.KEEP_ALIVE_TIMEOUT)
            sgs.save(force_insert=True)

    @classmethod
    def create_session(cls, session_id, owner, renderer_id):
        """
        Creates a user session
        :param session_id: Id for the new session
        :param owner: Session owner
        :param renderer_id: Id of the renderer associated to the session
        :rtype A tuple containing the status and the description of the potential error
        """
        sgs = SystemGlobalSettings.objects.get()
        if sgs.session_creation:
            try:
                session = Session(
                    id=session_id,
                    owner=owner,
                    renderer_id=renderer_id,
                    created=datetime.datetime.utcnow(),
                    valid_until=datetime.datetime.now() +
                    datetime.timedelta(seconds=sgs.session_keep_alive_timeout))
                with transaction.atomic():
                    session.save(force_insert=True)
                msg = 'Session ' + str(session_id) + ' successfully created'
                log.debug(1, msg)
                return [201, msg]
            except IntegrityError as e:
                log.error(e)
                return [409, e]
        else:
            msg = 'Session creation is currently suspended'
            log.error(msg)
            return [403, msg]

    @classmethod
    def get_session(cls, session_id, request, serializer):
        """
        Returns information about the session
        :param session_id: Id of the session
        :rtype A tuple containing the status and a JSON string with the
               serialized session, or a potential error description
        """
        try:
            session = Session.objects.get(id=session_id)
        except Session.DoesNotExist as e:
            log.error(e)
            return [404, e]

        if request.method == consts.REST_VERB_GET:
            serializer = serializer(session)
            return [200, JSONResponse(serializer.data)]

        elif request.method == consts.REST_VERB_PUT:
            data = JSONParser().parse(request)
            serializer = serializer(session, data=data)
            if serializer.is_valid():
                serializer.save()
                return [200, serializer.data]
            log.error(serializer.errors)
            return [400, serializer.errors]

    @classmethod
    def delete_session(cls, session_id):
        """
        Deletes a session
        :param session_id: Id of the session to delete
        :rtype A tuple containing the status and a potential error description
        """
        try:
            log.info(1, 'Removing session ' + str(session_id))
            session = Session.objects.get(id=session_id)
            session.status = SESSION_STATUS_STOPPING
            session.save()
            if session.process_pid != -1:
                process_manager.ProcessManager.stop(session)
            if session.job_id is not None and session.job_id != '':
                jm = job_manager.JobManager()
                jm.stop(session)
            session.delete()
            msg = str(session_id) + ' successfully destroyed'
            log.info(1, msg)
            return [200, msg]
        except Session.DoesNotExist as e:
            log.error(str(e))
            return [404, str(e)]
        except Exception as e:
            log.error(str(e))
            return [404, str(e)]

    @classmethod
    def list_sessions(cls, serializer):
        """
        Returns a JSON formatted list of active session according to a given serializer
        :param serializer: Serializer used for formatting the list of session
        """
        sessions = Session.objects.all()
        return [200, JSONResponse(serializer(sessions, many=True).data)]

    @classmethod
    def suspend_sessions(cls):
        """
        Suspends the creation of new session. This administration feature is
        here to prevent overloading of the system
        """
        sgs = SystemGlobalSettings.objects.get(id=0)
        if not sgs.session_creation:
            msg = 'Session creation already suspended'
        else:
            sgs.session_creation = False
            sgs.save()
            msg = 'Creation of new session now suspended'
        log.debug(1, msg)
        return [200, msg]

    @classmethod
    def clear_sessions(cls):
        """
        Suspends the creation of new session. This administration feature is
        here to prevent overloading of the system
        """
        Session.objects.all().delete()
        return [200, 'Sessions cleared']

    @classmethod
    def resume_sessions(cls):
        """
        Resumes the creation of new session.
        """
        sgs = SystemGlobalSettings.objects.get(id=0)
        if sgs.session_creation:
            msg = 'Session creation already resumed'
        else:
            sgs.session_creation = True
            sgs.save()
            msg = 'Creation of new session now resumed'
        log.debug(1, msg)
        return [200, msg]

    @staticmethod
    def request_vocabulary(session_id):
        """
        Queries the rendering resource vocabulary
        :param session_id: Id of the session to be queried
        :return 200 code if rendering resource is able to provide vocabulary. HTTP_STATUS_ERROR
                otherwise. 404 if specified session does not exist.
        """
        try:
            session = Session.objects.get(id=session_id)
            try:
                url = 'http://' + session.http_host + ':' + \
                      str(session.http_port) + '/' + consts.RR_SPECIFIC_COMMAND_VOCABULARY
                log.info(1, 'Requesting vocabulary on: ' + str(url))
                req = urllib2.Request(url=url)
                response = urllib2.urlopen(req).read()
                js = json.loads(response)
                if len(js['subscribed']) == 0 and len(js['published']) == 0:
                    return [HTTP_STATUS_ERROR, 'No vocabulary defined']
                else:
                    return [200, response]
            except urllib2.URLError as e:
                log.info(1, str(e))
                return [HTTP_STATUS_ERROR, str(e)]
        except Session.DoesNotExist as e:
            # Requested session does not exist
            log.info(1, str(e))
            return [404, str(e)]

    @staticmethod
    def query_status(session_id):
        """
        Queries the session status and updates it accordingly
        - Stopped: Default status, when no rendering resource is active
        - Scheduled: The slurm job was created but the rendering resource is not yet started.
        - Starting: The rendering resource is started but is not ready to respond to REST requests
        - Running: The rendering resource is started and ready to respond to REST requests
        - Stopping: tThe request for stopping the slurm job was made, but the application is not yet
          terminated
        :param session_id: Id of the session to be queried
        :return 200 code if rendering resource is able to process REST requests. HTTP_STATUS_ERROR
                otherwise. 404 if specified session does not exist.
        """
        try:
            session = Session.objects.get(id=session_id)
            status_description = session.renderer_id + ' running on ' + str(session.http_host)
            session_status = session.status

            log.info(1, 'Current session status is: ' + str(session_status))

            # Update the timestamp if the current value is expired
            sgs = SystemGlobalSettings.objects.get()
            if datetime.datetime.now() > session.valid_until:
                session.valid_until = datetime.datetime.now() + datetime.timedelta(
                    seconds=sgs.session_keep_alive_timeout)
                session.save()
            if session_status == SESSION_STATUS_SCHEDULED:
                if session.http_host != '':
                    log.info(1, 'Rendering resource is now starting!')
                    session.status = SESSION_STATUS_STARTING
                    session.save()
                else:
                    status_description = str(session.renderer_id + ' is scheduled')
            elif session_status == SESSION_STATUS_STARTING:
                # Rendering resource might be running but not yet capable of
                # serving REST requests. The vocabulary is invoked to make
                # sure that the rendering resource is ready to serve REST
                # requests.
                log.info(1, 'Requesting rendering resource vocabulary')
                status = SessionManager.request_vocabulary(session_id)
                if status[0] == 200:
                    log.info(1, 'Rendering resource is now RUNNING!')
                    session.status = SESSION_STATUS_RUNNING
                    session.save()
                else:
                    # Check job existence
                    hostname = job_manager.globalJobManager.hostname(session.job_id)
                    if hostname == '':
                        session.delete()
                        status_description = \
                            str(session.renderer_id +
                                ' bas been cancelled. Session will be deleted' + status[1])

                    else:
                        status_description = str(session.renderer_id + ' is starting... ' +
                                                 status[1])
            elif session_status == SESSION_STATUS_STOPPING:
                # Rendering resource is currently in the process of terminating.
                status_description = str(session.renderer_id + ' is terminating...')
                session.delete()
                session.save()
            elif session_status == SESSION_STATUS_STOPPED:
                # Rendering resource is currently not active.
                status_description = str(session.renderer_id + ' is not active')

            status_code = session.status
            response = [200, json.dumps({
                'session_id': str(session_id),
                'code': status_code,
                'description': str(status_description)})]
            return response
        except Session.DoesNotExist as e:
            # Requested session does not exist
            log.error(str(e))
            return [404, str(e)]

    @classmethod
    def keep_alive_session(cls, session_id):
        """
        Updated the specified session with a new expiration timestamp
        :param session_id: Id of the session to update
        """
        log.debug(1, 'Session ' + str(session_id) + ' is being updated')
        try:
            sgs = SystemGlobalSettings.objects.get(id=0)
            session = Session.objects.get(id=session_id)
            session.valid_until = datetime.datetime.now() + \
                datetime.timedelta(seconds=sgs.session_keep_alive_timeout)
            session.save()
            msg = 'Session ' + str(session_id) + ' successfully updated'
            return [200, msg]
        except Session.DoesNotExist as e:
            log.error(str(e))
            return [404, str(e)]

    @staticmethod
    def get_session_id():
        """
        Utility function that returns a unique session ID
        :return: a UUID session identifier
        """
        session_id = uuid.uuid1()
        return session_id

    @staticmethod
    def get_session_id_from_request(request):
        """
        Utility function that returns the session ID from a given HTTP request
        :return: a UUID session identifier
        """
        log.debug(1, 'Getting cookie from request')
        try:
            session_id = request.COOKIES[consts.COOKIE_ID]
        except KeyError as e:
            session_id = SessionManager.get_session_id()
            log.info(1, 'Cookie ' + str(e) + ' is missing. New session ID is ' + str(session_id))
        return session_id
