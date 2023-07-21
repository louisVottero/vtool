# Copyright (C) 2022 Louis Vottero louis.vot@gmail.com    All rights reserved.

"""
    A library of tools for rigging.
"""

from __future__ import absolute_import

import os

from . import util
from . import util_file

#Environment variables, do not edit
util.suggest_env('VETALA_STOP', 'False')
util.suggest_env('VETALA_RUN', 'False')
util.suggest_env('VETALA_PATH', os.path.dirname(__file__))
util.suggest_env('VETALA_PROJECT_PATH', '')
util.suggest_env('VETALA_CURRENT_PROCESS', '')
util.suggest_env('VETALA_COPIED_PROCESS', '')
util.suggest_env('VETALA_PRE_SAVE_INITIALIZED', 'False')
util.suggest_env('VETALA_SAVE_COMMENT', '')
util.suggest_env('VETALA_KEEP_TEMP_LOG', 'False')
util.suggest_env('VETALA_CURRENT_PROCESS_SKELETAL_MESH', '')

util.show('VETALA %s' % util_file.get_vetala_version())
util.suggest_env('VETALA_SETTINGS',util_file.get_default_directory())