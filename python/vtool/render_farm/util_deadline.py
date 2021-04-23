# Copyright (C) 2021 Louis Vottero louis.vot@gmail.com    All rights reserved.

from __future__ import print_function
from __future__ import absolute_import

import sys
import subprocess

from . import util_file

#---- Deadline

class DeadlineJob(object):
    
    def __init__(self):
        self._job_info_dict = {}
        self._deadline_info_dict = {
            'ChunkSize' : 1,
            'InitialStatus' : 'Active',
            'ConcurrentTasks' : 1,
            'Priority' : 100,
            'MachineLimit' : 0}
        self._output_path = ''
        self._scene_file_path = ''
        self._deadline_path = ''
    
    def _dict_to_deadline(self, dict_value):
        
        keys = list(dict_value.keys())
        keys.sort()
        
        txt = ''
        
        for key in keys:
            txt.append('%s=%s\n' % (key, dict_value[key]))
            
        return txt
        
    def _create_files(self):
        
        filepath_job = util_file.create_file('maya_deadline_job.job', self._output_path)
        text = self._dict_to_deadline(self._job_info_dict)
        util_file.write_replace(filepath_job, text)
        
        filepath_info = util_file.create_file('maya_deadline_info.job', self._output_path)
        text = self._dict_to_deadline(self._deadline_info_dict)
        util_file.write_replace(filepath_info, text)
        
        return [filepath_job, filepath_info]
    
    def set_job_info(self, dict_value = {}):
        self._job_info_dict.update(dict_value)
    
    def set_deadline_info(self, dict_value = {}):
        self._deadline_info_dict.update(dict_value)
    
    def set_task_info(self, pool, group, priority):
        
        dict_value = {
            'Pool' : pool,
            'Group' : group,
            'Priority' : priority}
        
        self._deadline_info_dict.update(dict_value)
    
    def set_task_description(self, name, department, comment):
        pass
    
    def set_scene_file_path(self, scene_file_path):
        self._scene_file_path = scene_file_path
    
    def set_output_path(self, output_path):
        self._output_path = output_path
    
    def set_deadline_path(self, deadline_path):
        
        self._deadline_path = deadline_path
    
    def submit(self):
        
        deadline_command = self._deadline_path
        job_file, info_file = self._create_files()
        
        command = '{deadline_command} "{job_file}" "{info_file}"'.format(**vars())
        
        process = subprocess.Popen(command, stdout=subprocess.PIPE)
        lines = iter(process.stdout.readline, b"")
        for line in lines:
            print(line)
            sys.stdout.flush()
        
    
class MayaScriptJob(object):
    
    def __init__(self):
        super(MayaScriptJob, self).__init__()
        
        self._deadline_info_dict = {
            
            'Plugin' : 'MayaScriptJob'
            
            }
    
    def set_script_path(self, script_path):
        pass
    
    