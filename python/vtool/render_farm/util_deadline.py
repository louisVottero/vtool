# Copyright (C) 2021 Louis Vottero louis.vot@gmail.com    All rights reserved.

from __future__ import print_function
from __future__ import absolute_import

import sys
import subprocess

from .. import util_file
from .. import util

#---- Deadline

class DeadlineJob(object):
    
    def __init__(self):
        self._plugin_info_dict = {}
        self._job_info_dict = {
            'ChunkSize' : 1,
            'InitialStatus' : 'Active',
            'ConcurrentTasks' : 1,
            'Priority' : 100,
            'MachineLimit' : 0}
            #'IncludeEnvironment':'true'}
        self._output_path = ''
        self._scene_file_path = ''
        self._deadline_path = ''
        self._job_parents = []
    
    def _dict_to_deadline(self, dict_value):
        
        keys = list(dict_value.keys())
        keys.sort()
        
        txt = ''
        
        for key in keys:
            txt += '%s=%s\n' % (key, dict_value[key])
            
        return txt
        
    def _create_files(self):
        
        job_info = util_file.create_file('deadline_job_info.txt', self._output_path)
        text = self._dict_to_deadline(self._job_info_dict)
        util_file.write_replace(job_info, text)
        
        plugin_info = util_file.create_file('deadline_plugin_info.txt', self._output_path)
        text = self._dict_to_deadline(self._plugin_info_dict)
        util_file.write_replace(plugin_info, text)
        
        return [job_info, plugin_info]
    
    def set_job_info(self, dict_value = {}):
        self._job_info_dict.update(dict_value)
    
    def set_plugin_info(self, dict_value = {}):
        self._plugin_info_dict.update(dict_value)
    
    def set_task_info(self, pool, group, priority):
        
        dict_value = {
            'Pool' : pool,
            'Group' : group,
            'Priority' : priority}
        
        self._job_info_dict.update(dict_value)
    
    def set_task_description(self, name, department, comment):
        dict_value = {
            'Name' : name,
            'Department' : department,
            'Comment' : comment
            }
        
        self._job_info_dict.update(dict_value)
    
    def set_scene_file_path(self, scene_file_path):
        self._plugin_info_dict.update({'SceneFile':scene_file_path})
        self._scene_file_path = scene_file_path
    
    def set_output_path(self, output_path):
        self._output_path = output_path
    
    def set_deadline_path(self, deadline_path):
        
        self._deadline_path = deadline_path
    
    def set_parent_jobs(self, parents):
        
        util.convert_to_sequence(parents)
        
        job_string = ''
        for parent in parents:
            if parent == parents[-1]:
                job_string += str(parent)
            else:
                job_string += '%s,' % parent
        
        self._job_info_dict['JobDependencies'] = job_string 
    
    def set_job_setting(self, setting_name, setting_string):
        
        self._job_info_dict[setting_name] = setting_string
    
    def set_plugin_setting(self, setting_name, setting_string):
        
        self._plugin_info_dict[setting_name] = setting_string
    
    def submit(self):
        
        deadline_command = self._deadline_path
        job_info, plugin_info = self._create_files()
        
        command = '{deadline_command} "{job_info}" "{plugin_info}"'.format(**vars())
        
        process = subprocess.Popen(command, stdout=subprocess.PIPE)
        lines = iter(process.stdout.readline, b"")
        for line in lines:
            if line.find('JobID') > -1:
                split_line = line.split('=')
                job_id = split_line[-1]
                job_id = job_id.rstrip('\n')
                job_id = job_id.rstrip('\r')
            util.show(line)
            sys.stdout.flush()
            
        return job_id
        
    
class MayaJob(DeadlineJob):
    
    def __init__(self):
        super(MayaJob, self).__init__()
        
        import maya.cmds as cmds
        
        job_info_dict = {
            
            'Plugin' : 'MayaBatch',
            'EnvironmentKeyValue0' : 'PYTHONPATH=' + util.get_env('PYTHONPATH'),
            'EnvironmentKeyValue1' : 'VETALA_CURRENT_PROCESS=' + util.get_env('VETALA_CURRENT_PROCESS'), 
            }
        
        self._job_info_dict.update(job_info_dict)
        
        plugin_info_dict = {
            'Version' : cmds.about(version=True),
            'ScriptJob' : 'true',
            'ScriptFilename' : util_file.get_process_deadline_file()
            }
        
        self._plugin_info_dict.update(plugin_info_dict)
        
        
        
        #import os 
        #os.environ.pop('MAYA_APP_DIR')
        
    
    def set_script_path(self, script_path):
        pass
    
    