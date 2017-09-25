#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

from django.test import TestCase
from nose import tools as nt
import rendering_resource_manager_service.utils.custom_logging as log
from rendering_resource_manager_service.config.management.rendering_resource_settings_manager \
    import RenderingResourceSettingsManager
from rendering_resource_manager_service.config.views import \
    RenderingResourceSettingsSerializer


class TestSessionManager(TestCase):
    def setUp(self):
        log.debug(1, 'setUp')
        manager = RenderingResourceSettingsManager()
        # Clear session
        status = manager.clear()
        nt.assert_true(status[0] == 200)

    def tearDown(self):
        log.debug(1, 'tearDown')
        # Clear session
        manager = RenderingResourceSettingsManager()
        status = manager.clear()
        nt.assert_true(status[0] == 200)

    def test_create_settings(self):
        log.debug(1, 'test_create_settings')
        # Create Settings
        manager = RenderingResourceSettingsManager()
        params = dict()
        params['id'] = 'rtneuron'
        params['command_line'] = 'rtneuron-app.py'
        params['environment_variables'] = \
            'EQ_WINDOW_IATTR_HINT_HEIGHT=512,EQ_WINDOW_IATTR_HINT_WIDTH=512'
        params['modules'] = 'BBP/viz/latest'
        params['process_rest_parameters_format'] = '--rest {$rest_hostname}:${rest_port}'
        params['scheduler_rest_parameters_format'] = '--rest $SLURMD_NODENAME:${rest_port}'
        params['project'] = 'project'
        params['queue'] = 'test'
        params['exclusive'] = False
        params['nb_nodes'] = 1
        params['nb_cpus'] = 1
        params['nb_gpus'] = 1
        params['memory'] = 0
        params['graceful_exit'] = True
        params['wait_until_running'] = True
        params['name'] = 'name'
        params['description'] = 'description'
        status = manager.create(params)
        nt.assert_true(status[0] == 201)
        # Delete Settings
        status = manager.delete(params['id'])
        nt.assert_true(status[0] == 200)

    def test_duplicate_settings(self):
        log.debug(1, 'test_duplicate_settings')
        manager = RenderingResourceSettingsManager()
        params = dict()
        params['id'] = 'rtneuron'
        params['command_line'] = 'rtneuron-app.py'
        params['environment_variables'] = \
            'EQ_WINDOW_IATTR_HINT_HEIGHT=512,EQ_WINDOW_IATTR_HINT_WIDTH=512'
        params['modules'] = 'BBP/viz/latest'
        params['process_rest_parameters_format'] = '--rest {$rest_hostname}:${rest_port}'
        params['scheduler_rest_parameters_format'] = '--rest $SLURMD_NODENAME:${rest_port}'
        params['project'] = 'project'
        params['queue'] = 'test'
        params['exclusive'] = False
        params['nb_nodes'] = 1
        params['nb_cpus'] = 1
        params['nb_gpus'] = 1
        params['memory'] = 0
        params['graceful_exit'] = True
        params['wait_until_running'] = True
        params['name'] = 'name'
        params['description'] = 'description'
        status = manager.create(params)
        nt.assert_true(status[0] == 201)
        # Duplicate
        status = manager.create(params)
        nt.assert_true(status[0] == 409)
        # Delete Settings
        status = manager.delete(params['id'])
        nt.assert_true(status[0] == 200)

    def test_delete_invalid_settings(self):
        log.debug(1, 'test_delete_invalid_settings')
        manager = RenderingResourceSettingsManager()
        params = dict()
        params['id'] = '@%$#$'
        # Delete Settings
        status = manager.delete(params)
        nt.assert_true(status[0] == 404)

    def test_list_settings(self):
        log.debug(1, 'test_list_settings')
        manager = RenderingResourceSettingsManager()
        params = dict()
        params['id'] = 'rtneuron'
        params['command_line'] = 'rtneuron-app.py'
        params['environment_variables'] = \
            'EQ_WINDOW_IATTR_HINT_HEIGHT=512,EQ_WINDOW_IATTR_HINT_WIDTH=512'
        params['modules'] = 'BBP/viz/latest'
        params['process_rest_parameters_format'] = '--rest {$rest_hostname}:${rest_port}'
        params['scheduler_rest_parameters_format'] = '--rest $SLURMD_NODENAME:${rest_port}'
        params['project'] = 'project'
        params['queue'] = 'test'
        params['exclusive'] = False
        params['nb_nodes'] = 1
        params['nb_cpus'] = 1
        params['nb_gpus'] = 1
        params['memory'] = 0
        params['graceful_exit'] = True
        params['wait_until_running'] = True
        params['name'] = 'name'
        params['description'] = 'description'
        status = manager.create(params)
        nt.assert_true(status[0] == 201)

        params['id'] = 'livre'
        params['command_line'] = 'livre'
        params['environment_variables'] = \
            'EQ_WINDOW_IATTR_HINT_HEIGHT=512,EQ_WINDOW_IATTR_HINT_WIDTH=512'
        params['modules'] = 'BBP/viz/2015.R3'
        params['process_rest_parameters_format'] = \
            '--rest {$rest_hostname}:${rest_port}:${rest_schema}'
        params['scheduler_rest_parameters_format'] = \
            '--rest $SLURMD_NODENAME:${rest_port}:${rest_schema}'
        params['project'] = 'project'
        params['queue'] = 'test'
        params['exclusive'] = False
        params['nb_nodes'] = 1
        params['nb_cpus'] = 1
        params['nb_gpus'] = 1
        params['memory'] = 0
        params['graceful_exit'] = True
        params['wait_until_running'] = True
        params['name'] = 'name'
        params['description'] = 'description'
        status = manager.create(params)
        nt.assert_true(status[0] == 201)
        status = manager.list(RenderingResourceSettingsSerializer)
        nt.assert_true(status[0] == 200)
        value = status[1]
        reference = '[' \
                    '{"id": "livre", ' \
                    '"command_line": "livre", ' \
                    '"environment_variables": ' \
                    '"EQ_WINDOW_IATTR_HINT_HEIGHT=512,EQ_WINDOW_IATTR_HINT_WIDTH=512", ' \
                    '"modules": ' \
                    '"BBP/viz/2015.R3", ' \
                    '"process_rest_parameters_format": ' \
                    '"--rest {$rest_hostname}:${rest_port}:${rest_schema}", ' \
                    '"scheduler_rest_parameters_format": ' \
                    '"--rest $SLURMD_NODENAME:${rest_port}:${rest_schema}", ' \
                    '"project": "project", ' \
                    '"queue": "test", ' \
                    '"exclusive": false, ' \
                    '"nb_nodes": 1, ' \
                    '"nb_cpus": 1, ' \
                    '"nb_gpus": 1, ' \
                    '"memory": 0, ' \
                    '"graceful_exit": true, ' \
                    '"wait_until_running": true, ' \
                    '"name": "name", ' \
                    '"description": "description"}, ' \
                    '{"id": "rtneuron", ' \
                    '"command_line": "rtneuron-app.py", ' \
                    '"environment_variables": ' \
                    '"EQ_WINDOW_IATTR_HINT_HEIGHT=512,EQ_WINDOW_IATTR_HINT_WIDTH=512", ' \
                    '"modules": "BBP/viz/latest", ' \
                    '"process_rest_parameters_format": ' \
                    '"--rest {$rest_hostname}:${rest_port}", ' \
                    '"scheduler_rest_parameters_format": ' \
                    '"--rest $SLURMD_NODENAME:${rest_port}", ' \
                    '"project": "project", ' \
                    '"queue": "test", ' \
                    '"exclusive": false, ' \
                    '"nb_nodes": 1, ' \
                    '"nb_cpus": 1, ' \
                    '"nb_gpus": 1, ' \
                    '"memory": 0, ' \
                    '"graceful_exit": true, ' \
                    '"wait_until_running": true, ' \
                    '"name": "name", ' \
                    '"description": "description"}' \
                    ']'

        print value

        nt.assert_true(value == reference)

    def test_get_by_name_settings(self):
        log.debug(1, 'test_get_by_name_settings')
        manager = RenderingResourceSettingsManager()
        params = dict()
        params['id'] = 'rtneuron'
        params['command_line'] = 'rtneuron-app.py'
        params['environment_variables'] = \
            'EQ_WINDOW_IATTR_HINT_HEIGHT=512,EQ_WINDOW_IATTR_HINT_WIDTH=512'
        params['modules'] = 'BBP/viz/latest'
        params['process_rest_parameters_format'] = '--rest {$rest_hostname}:${rest_port}'
        params['scheduler_rest_parameters_format'] = '--rest $SLURMD_NODENAME:${rest_port}'
        params['project'] = 'project'
        params['queue'] = 'test'
        params['exclusive'] = False
        params['nb_nodes'] = 1
        params['nb_cpus'] = 1
        params['nb_gpus'] = 1
        params['memory'] = 0
        params['graceful_exit'] = True
        params['wait_until_running'] = True
        params['name'] = 'name'
        params['description'] = 'description'
        status = manager.create(params)
        nt.assert_true(status[0] == 201)

        settings = manager.get_by_id('rtneuron')
        nt.assert_true(settings.id == 'rtneuron')
        nt.assert_true(settings.command_line == 'rtneuron-app.py')
        nt.assert_true(settings.environment_variables ==
                       'EQ_WINDOW_IATTR_HINT_HEIGHT=512,EQ_WINDOW_IATTR_HINT_WIDTH=512')
        nt.assert_true(settings.process_rest_parameters_format ==
                       '--rest {$rest_hostname}:${rest_port}')
        nt.assert_true(settings.scheduler_rest_parameters_format ==
                       '--rest $SLURMD_NODENAME:${rest_port}')

    def test_format_rest_parameters(self):
        log.debug(1, 'test_format_rest_parameters')
        manager = RenderingResourceSettingsManager()
        job_id = '42'
        # test 1
        value = manager.format_rest_parameters(
            '--rest ${rest_hostname}:${rest_port}',
            'localhost', 3000, 'schema', job_id)
        nt.assert_true(value == '--rest localhost:3000')

        # test 2
        value = manager.format_rest_parameters(
            '--rest ${rest_hostname}:${rest_port} --rest-schema ${rest_schema}',
            'localhost', 3000, 'schema', job_id)
        nt.assert_true(value == '--rest localhost:3000 --rest-schema schema')

        # test 3
        value = manager.format_rest_parameters(
            '--rest ${rest_hostname}:${rest_port} --rest-schema ${rest_schema}',
            'localhost', 3000, 'schema', job_id)
        nt.assert_true(value == '--rest localhost:3000 --rest-schema schema')

        # test 4
        value = manager.format_rest_parameters(
            '--rest ${rest_hostname}:${rest_port} --rest-schema ${rest_schema}',
            'localhost', '3000', 'schema', job_id)
        nt.assert_true(value == '--rest localhost:3000 --rest-schema schema')

        # test 5
        value = manager.format_rest_parameters(
            '--rest $SLURMD_NODENAME:${rest_port}',
            'localhost', 3000, 'schema', job_id)
        nt.assert_true(value == '--rest $SLURMD_NODENAME:3000')

        # test 6
        value = manager.format_rest_parameters(
            '--rest ${rest_hostname}:${rest_port}:${rest_schema}',
            'localhost', 3000, 'schema', job_id)
        nt.assert_true(value == '--rest localhost:3000:schema')

        # test 7
        value = manager.format_rest_parameters(
            '--jobid=${job_id} --rest ${rest_hostname}:${rest_port}:${rest_schema}',
            'localhost', 3000, 'schema', job_id)
        nt.assert_true(value == '--jobid=42 --rest localhost:3000:schema')
