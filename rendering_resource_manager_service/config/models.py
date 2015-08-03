#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This modules defines the data model for the rendering resource manager
"""

from django.db import models


class RenderingResourceSettings(models.Model):
    """
    Persistent Rendering Resource Settings
    """

    id = models.CharField(max_length=50, primary_key=True)
    command_line = models.CharField(max_length=1024)
    environment_variables = models.CharField(max_length=4096)
    process_rest_parameters_format = models.CharField(max_length=1024)
    scheduler_rest_parameters_format = models.CharField(max_length=1024)
    graceful_exit = models.BooleanField(default=True)

    class Meta(object):
        """
        A Meta object for the Settings
        """
        ordering = (
            'id', 'command_line',
            'environment_variables',
            'process_rest_parameters_format',
            'scheduler_rest_parameters_format',
            'graceful_exit')

    def __str__(self):
        return '%s' % self.id

    __unicode__ = __str__
