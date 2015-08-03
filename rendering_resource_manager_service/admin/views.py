#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=W0403
# pylint: disable=E1101
# pylint: disable=R0901

"""
This modules defines the data structure used by the rendering resource manager to manager
user session
"""

from rest_framework import serializers, viewsets
from django.http import HttpResponse
from rendering_resource_manager_service import utils as consts
from rendering_resource_manager_service.session.models import Session
import rendering_resource_manager_service.session.management.session_manager as session_manager


class AdminSerializer(serializers.ModelSerializer):
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


class AdminViewSet(viewsets.ModelViewSet):
    """
    ViewSets define the default view behavior
    """

    queryset = Session.objects.all()
    serializer_class = AdminSerializer

    @classmethod
    def admin_command(cls, request, command):
        """
        Updates the valid_until attribute of the user session
        :param : request: The REST request
        :rtype : A Json response containing an ok status or a description of the error
        """
        if command == consts.RRM_SPECIFIC_COMMAND_KEEPALIVE:
            session_id = session_manager.get_session_id_from_request(request)
            sm = session_manager.SessionManager()
            status = sm.keep_alive_session(session_id)
            return HttpResponse(status=status[0], content=status[1])
        elif command == consts.RRM_SPECIFIC_COMMAND_SUSPEND:
            sm = session_manager.SessionManager()
            status = sm.suspend_sessions()
            return HttpResponse(status=status[0], content=status[1])
        elif command == consts.RRM_SPECIFIC_COMMAND_RESUME:
            sm = session_manager.SessionManager()
            status = sm.resume_sessions()
            return HttpResponse(status=status[0], content=status[1])
        else:
            return HttpResponse(status=401, content=command + ' is an invalid command')
