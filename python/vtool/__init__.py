"""
    A library of tools for rigging.
"""

import os


#Environment variables, do not edit
os.environ['VETALA_STOP'] = 'False'
os.environ['VETALA_RUN'] = 'False'
os.environ['VETALA_PATH'] = os.path.dirname(__file__)
os.environ['VETALA_PROJECT_PATH'] = ''

os.environ['VETALA_CURRENT_PROCESS'] = ''
os.environ['VETALA_COPIED_PROCESS'] = ''
os.environ['VETALA_PRE_SAVE_INITIALIZED'] = 'False'
os.environ['VETALA_SAVE_COMMENT'] = ''
os.environ['VETALA_KEEP_TEMP_LOG'] = 'False'

import util
import util_file
util.show('VETALA %s' % util_file.get_vetala_version())
os.environ['VETALA_SETTINGS'] = util_file.get_default_directory()