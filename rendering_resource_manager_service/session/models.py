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

"""
This modules defines the data model for the rendering resource manager
"""

from django.db import models


SESSION_STATUS_STOPPED = 0
SESSION_STATUS_SCHEDULING = 1
SESSION_STATUS_SCHEDULED = 2
SESSION_STATUS_GETTING_HOSTNAME = 3
SESSION_STATUS_STARTING = 4
SESSION_STATUS_RUNNING = 5
SESSION_STATUS_STOPPING = 6
SESSION_STATUS_FAILED = 7
SESSION_STATUS_BUSY = 8


class Session(models.Model):
    """
    An user session
    """

    id = models.CharField(max_length=20, primary_key=True)
    created = models.DateTimeField(auto_now_add=True)
    valid_until = models.DateTimeField(auto_now_add=False)
    owner = models.CharField(max_length=20)
    renderer_id = models.CharField(default='undefined', max_length=50)
    job_id = models.CharField(max_length=2048, default='')
    process_pid = models.IntegerField(default=-1)
    http_host = models.CharField(default='localhost', max_length=20)
    http_port = models.IntegerField(default=0)
    command = models.CharField(max_length=20, default='')
    parameters = models.CharField(max_length=2048, default='')
    status = models.IntegerField(default=0)
    cluster_node = models.CharField(max_length=512, default='')

    class Meta(object):
        """
        A Meta object for the Session
        """
        ordering = ('id', 'created',)

    def __str__(self):
        return '%s, %s' % (self.owner, self.renderer_id)

    __unicode__ = __str__
