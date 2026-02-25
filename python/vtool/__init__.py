# Copyright (C) 2024 Louis Vottero louis.vot@gmail.com    All rights reserved.

"""
    A library of tools for rigging.
"""

import os

from . import util
from . import util_file

# Environment variables, do not edit
util.suggest_env('VETALA_STOP', '0')
util.suggest_env('VETALA_RUN', '0')
util.suggest_env('VETALA_PATH', os.path.dirname(os.path.abspath(__file__)))
util.suggest_env('VETALA_PROJECT_PATH', '')
util.suggest_env('VETALA_CURRENT_PROCESS', '')
util.suggest_env('VETALA_COPIED_PROCESS', '')
util.suggest_env('VETALA_PRE_SAVE_INITIALIZED', '0')
util.suggest_env('VETALA_SAVE_COMMENT', '')
util.suggest_env('VETALA_KEEP_TEMP_LOG', '0')
util.suggest_env('VETALA_CURRENT_PROCESS_SKELETAL_MESH', '')

util.show('VETALA %s' % util_file.get_vetala_version())
util.suggest_env('VETALA_SETTINGS', util_file.get_default_directory())
