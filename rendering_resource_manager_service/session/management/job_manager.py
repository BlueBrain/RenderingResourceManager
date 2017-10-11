#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=W0403
# pylint: disable=R0915

# Copyright (c) 2014-2015, Human Brain Project
#                          Cyrille Favreau <cyrille.favreau@epfl.ch>
#                          Daniel Nachbaur <daniel.nachbaur@epfl.ch>
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
The job manager is in charge of managing jobs.
"""

import rendering_resource_manager_service.session.management.slurm_job_manager \
    as slurm_job_manager
import rendering_resource_manager_service.session.management.unicore_job_manager \
    as unicore_job_manager
import rendering_resource_manager_service.service.settings \
    as global_settings


class JobInformation(object):
    """
    The job information class holds job attributes
    """

    def __init__(self):
        """
        Initialization
        """
        self.name = ''
        self.params = ''
        self.environment = ''
        self.reservation = ''
        self.project = ''
        self.exclusive_allocation = False
        self.nb_cpus = 0
        self.nb_gpus = 0
        self.nb_nodes = 0
        self.memory = 0
        self.queue = ''
        self.allocation_time = ''
        # self.work_dir = None
        self.job = None

# Global job manager used for all allocations
globalJobManager = None
if global_settings.JOB_ALLOCATOR == global_settings.JOB_ALLOCATOR_SLURM:
    globalJobManager = slurm_job_manager.SlurmJobManager()
elif global_settings.JOB_ALLOCATOR == global_settings.JOB_ALLOCATOR_UNICORE:
    globalJobManager = unicore_job_manager.UnicoreJobManager()
