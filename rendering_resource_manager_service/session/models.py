#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This modules defines the data model for the rendering resource manager
"""

from django.db import models


SESSION_STATUS_STOPPED = 0
SESSION_STATUS_SCHEDULED = 1
SESSION_STATUS_STARTING = 2
SESSION_STATUS_RUNNING = 3
SESSION_STATUS_STOPPING = 4


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

    class Meta(object):
        """
        A Meta object for the Session
        """
        ordering = ('created',)

    def __str__(self):
        return '%s, %s' % (self.owner, self.renderer_id)

    __unicode__ = __str__


class SystemGlobalSettings(models.Model):
    """
    Persistent Global Settings
    """

    id = models.IntegerField(primary_key=True, default=0)
    session_creation = models.BooleanField(default=True)
    session_keep_alive_timeout = models.IntegerField(default=1000)

    class Meta(object):
        """
        A Meta object for the Session
        """
        ordering = ('id', 'session_creation', 'session_keep_alive_timeout')

    def __str__(self):
        return '%s, %s' % (self.session_creation, self.session_keep_alive_timeout)

    __unicode__ = __str__
