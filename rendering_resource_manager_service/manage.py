#!/usr/bin/env python

"""
Main Program
"""

import sys
import os

if __name__ == '__main__':

    os.environ.setdefault('DJANGO_SETTINGS_MODULE',
                          'rendering_resource_manager_service.service.settings')

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
