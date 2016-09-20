#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=E1101
# pylint: disable=W0403

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
This class is in charge of handling rendering resources config, such as the
application name, executable name and command line parameters,
and ensures persistent storage in a database
"""

from rendering_resource_manager_service.config.models import RenderingResourceSettings
import rendering_resource_manager_service.utils.custom_logging as log
import rest_framework.status as http_status
from django.db import IntegrityError, transaction
from rest_framework.renderers import JSONRenderer
import json


class RenderingResourceSettingsManager(object):
    """
    This class is in charge of handling session and ensures persistent storage in a database
    """

    @classmethod
    def create(cls, params):
        """
        Creates new rendering resource config
        :param params Settings for the new rendering resource
        """
        try:
            settings_id = params['id'].lower()
            settings = RenderingResourceSettings(
                id=settings_id,
                command_line=str(params['command_line']),
                environment_variables=str(params['environment_variables']),
                modules=str(params['modules']),
                process_rest_parameters_format=str(params['process_rest_parameters_format']),
                scheduler_rest_parameters_format=str(params['scheduler_rest_parameters_format']),
                project=str(params['project']),
                queue=str(params['queue']),
                exclusive=params['exclusive'],
                nb_nodes=params['nb_nodes'],
                nb_cpus=params['nb_cpus'],
                nb_gpus=params['nb_gpus'],
                graceful_exit=params['graceful_exit'],
                wait_until_running=params['wait_until_running'],
                name=params['name'],
                description=params['description']
            )
            with transaction.atomic():
                settings.save(force_insert=True)
            msg = 'Rendering Resource ' + settings_id + ' successfully configured'
            response = json.dumps({'contents': msg})
            return [http_status.HTTP_201_CREATED, response]
        except IntegrityError as e:
            log.error(str(e))
            response = json.dumps({'contents': str(e)})
            return [http_status.HTTP_409_CONFLICT, response]

    @classmethod
    def update(cls, params):
        """
        Updates some given rendering resource config
        :param params new config for the rendering resource
        """
        try:
            settings_id = params['id'].lower()
            settings = RenderingResourceSettings.objects.get(id=settings_id)
            settings.command_line = params['command_line']
            settings.environment_variables = params['environment_variables']
            settings.modules = params['modules']
            settings.process_rest_parameters_format = params['process_rest_parameters_format']
            settings.scheduler_rest_parameters_format = params['scheduler_rest_parameters_format']
            settings.project = params['project']
            settings.queue = params['queue']
            settings.exclusive = params['exclusive']
            settings.nb_nodes = params['nb_nodes']
            settings.nb_cpus = params['nb_cpus']
            settings.nb_gpus = params['nb_gpus']
            settings.graceful_exit = params['graceful_exit']
            settings.wait_until_running = params['wait_until_running']
            settings.name = params['name']
            settings.description = params['description']
            with transaction.atomic():
                settings.save()
            return [http_status.HTTP_200_OK, '']
        except RenderingResourceSettings.DoesNotExist as e:
            log.error(str(e))
            return [http_status.HTTP_404_NOT_FOUND, str(e)]

    @classmethod
    def list(cls, serializer):
        """
        Returns a JSON formatted list of active rendering resource config according
        to a given serializer
        :param serializer: Serializer used for formatting the list of session
        """
        settings = RenderingResourceSettings.objects.all()
        return [http_status.HTTP_200_OK,
                JSONRenderer().render(serializer(settings, many=True).data)]

    @staticmethod
    def get_by_id(settings_id):
        """
        Returns the config rendering resource config
        :param settings_id id of rendering resource or which we want the config
        """
        return RenderingResourceSettings.objects.get(id=settings_id)

    @classmethod
    def delete(cls, settings_id):
        """
        Removes some given rendering resource config
        :param settings_id Identifier of the Rendering resource config to remove
        """
        try:
            settings = RenderingResourceSettings.objects.get(id=settings_id)
            with transaction.atomic():
                settings.delete()
            return [http_status.HTTP_200_OK, 'Settings successfully deleted']
        except RenderingResourceSettings.DoesNotExist as e:
            log.error(str(e))
            return [http_status.HTTP_404_NOT_FOUND, str(e)]

    @staticmethod
    def format_rest_parameters(string_format, hostname, port, schema):
        """
        Returns a string of rest parameters formatted according to the
        string_format argument
        :param string_format Rest parameter string format
        :param hostname Rest hostname
        :param port Rest port
        :param schema Rest schema
        """
        response = string_format
        response = response.replace('${rest_hostname}', str(hostname))
        response = response.replace('${rest_port}', str(port))
        response = response.replace('${rest_schema}', str(schema))
        return response

    @classmethod
    def clear(cls):
        """
        Clear all config
        """
        with transaction.atomic():
            RenderingResourceSettings.objects.all().delete()
        return [http_status.HTTP_200_OK, 'Settings cleared']
