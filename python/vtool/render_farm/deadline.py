# Copyright (C) 2016 Louis Vottero louis.vot@gmail.com    All rights reserved.

import os
import subprocess
import traceback
from vtool import util_shotgun

from vtool import util_file
from vtool.maya_lib import anim



class Job(object):

    def __init__(self):
        
        self.name = 'cache'
        
        self.pool = ''
        self.secondary_pool = ''
        
        self.in_value = 0
        self.out_value = 100
        self.chunk_value = 101
        
        self.script = ''
        self.namespace = ''
        self.version = ''
        self.submit_file = ''
        
        #self.deadline_path = os.environ['DEADLINE_PATH']
        
        self.deadline_path = 'C:\\Program Files\\Thinkbox\\Deadline9\\bin\\deadlinecommand.exe'
        
    def _get_temp_dir(self):
        return os.environ["TEMP"]
        
    def _get_script_dir(self):
        return util_file.get_dirname(__file__)
        
    def _get_script_name(self):
        
        return ''
    
    def _get_shotgun_fields(self):
        
        fields = None
        
        try:
            fields = util_shotgun.get_file_info(self.submit_file)
        except:
            pass
        
        return fields
    
    def _get_command(self):
        
        return ''
    
    def _create_temp_script(self):
        
        
        if not self.script:
                        
            temp_script = util_file.join_path(self._get_temp_dir(), ('temp_' + self._get_script_name()))
            script = util_file.join_path(self._get_script_dir(), self._get_script_name())
        
            util_file.copy_file(script, temp_script)
        
            self.script = temp_script
        
            temp_file = open(temp_script, "r")
            temp_lines = temp_file.readlines()
            
            fields = util_shotgun.get_file_info(self.submit_file)
            
            name = 'cache'
            
            if fields:
                if fields.has_key('Shot'):
                    name = fields["Shot"]
                if fields.has_key('Asset'):
                    name = fields["Asset"]
            
            version = fields['version']
            
            self.name = name    
            command = self._get_command()
            
            temp_lines[0] = 'namespace = "%s"\n' % self.namespace
            temp_lines[1] = 'name = "%s"\n' % name
            temp_lines[2] = 'version = "%s"\n' % version
            temp_lines[3] = 'command = "%s"\n' % command
            
            temp_file = open(temp_script, "w")
            temp_file.writelines(temp_lines)
            temp_file.close()
            
        
    def _create_file(self, name):
        
        temp_dir = self._get_temp_dir()
        
        filename = util_file.create_file(name, temp_dir)
                
        return filename
    
    def _initialize_job(self):
        
        self.job_dict = {
        'Plugin' : '',
        'Name' : '',
        'Comment' : 'Auto Submit',
        #'Department' : '',
        'Pool' : self.pool,
        'Group' : '',
        #'SecondaryPool' : self.secondary_pool,
        'Group' : '',
        'Priority' : 99,
        #'TaskTimeoutMinutes' : 0, 
        #'EnableAutoTimeout' : '',
        #'ConcurrentTasks' : '',
        #'LimitConcurrentTasksToNumberOfCpus' : '',
        #'Whitelist' : '',
        #'MachineName' : '',
        'MachineLimit' : 0,
        #'LimitGroups' : '',
        #'JobDependencies' : '',
        #'OnJobComplete' : '',
        #'InitialStatus' : 'Suspended',
        'Frames' : str(self.in_value) + '-' + str(self.out_value),
        'ChunkSize' : self.chunk_value
        }
    
    def _initialize_plugin(self):
        
        self.plugin_dict = {
        'SceneFile' : self.submit_file,
        'Version' : self.version,
        'ProjectPath' : '',
        'StrictErrorChecking' : False,
        'ScriptJob' : True,
        'ScriptFilename' : util_file.get_basename(self.script)
        }
    
    def _create_job_file(self):
        
        lines = []
        
        for key in self.job_dict:
            line = key + '=' + str(self.job_dict[key])
            lines.append(line)
            
        filepath = self._create_file('maya_job_info.job')
        
        util_file.write_lines(filepath, lines)
        
        return filepath
        
    def _create_plugin_file(self):
        
        lines = []
        
        for key in self.plugin_dict:
            line = key + '=' + str(self.plugin_dict[key])
            lines.append(line)
            
        filepath = self._create_file('maya_plugin_info.job')
        
        util_file.write_lines(filepath, lines)
        
        return filepath
        
    def set_frames(self, in_value, out_value):
        
        self.in_value = in_value
        self.out_value = out_value
        
        self.chunk_value = (self.out_value - self.in_value) + 1
        
    def set_pool(self, pool_name, secondary_pool_name = ''):
        self.pool = pool_name
        self.secondary_pool = secondary_pool_name
        
        
    def set_group(self, group_name):
        
        self.job_dict['Group'] = group_name
    
    def set_submit_file(self, filename, version = ''):
        
        self.submit_file = filename
        

        
    def set_script(self, script_path):
        
        self.script = script_path
        
        
    def set_priority(self, priority_int):
        self.job_dict['Priority'] = priority_int
            
    def set_namespace(self, namespace):
        self.namespace = namespace
            
    def submit(self):
        
        self._create_temp_script()
        
        self._initialize_job()
        self._initialize_plugin()
        
        job_file = self._create_job_file()
        plugin_file = self._create_plugin_file()
        
        try:
            
            print 'submit :', self.deadline_path, job_file, plugin_file, self.submit_file, self.script
            subprocess.call([self.deadline_path, job_file, plugin_file, self.submit_file, self.script])
        except:
            print traceback.format_exc()   
        

class MayaJob( Job ):
    
    def __init__(self):
        super(MayaJob, self).__init__()
        
        import maya.cmds as cmds
        self.submit_file = cmds.file(q = True, sn = True)
        
        self.version = 2016

    def _initialize_job(self):
        super(MayaJob, self)._initialize_job()
        
        if self.namespace:
            self.job_dict['Name'] = self.namespace + ' ' + self.name
        
        if not self.namespace:
            self.job_dict['Name'] = self.name
            
        self.job_dict['Plugin'] = 'MayaBatch'

    def _initialize_plugin(self):
        super(MayaJob, self)._initialize_plugin()
        
        self.plugin_dict['ProjectPath'] = os.path.dirname(self.submit_file)


    def set_maya_version(self, version):
        self.version
        
class YetiJob(MayaJob): 
    
    def __init__(self):
        super(YetiJob, self).__init__()
        
        self.samples = 3
    
    def _get_script_name(self):
        
        return 'deadline_cache_yeti.py'
    
    def _initialize_job(self):
        super(YetiJob, self)._initialize_job()
        
        self.job_dict['Comment'] = 'Yeti'
        self.job_dict['Pool'] = 'lighting'
        self.job_dict['Group'] = 'yeti2016'
        
    
    def _get_command(self):
        
        command = "cmds.pgYetiCommand(yeti_node, writeCache=cache_path, range=(%s, %s), samples=%s)" % (self.in_value, self.out_value, self.samples)
        
        return command
    
    def set_samples(self, samples):
        
        self.sameples = samples
        
class AlembicJob(MayaJob):
    
    def _initialize_job(self):
        super(AlembicJob, self)._initialize_job()
        
        self.job_dict['Comment'] = 'Alembic'
    
    def _get_command(self):
        
        command = "cmds.AbcExport( j = '-frameRange {} {} -stripNamespaces -uvWrite -worldSpace -writeVisibility -dataFormat ogawa -root %s -file %s' % (node, cache_path))".format(self.in_value, self.out_value)
        return command
    
    def _get_script_name(self):
        
        return 'deadline_cache_alembic.py'    
    
class MayaCacheJob(MayaJob):
    
    def _initialize_job(self):
        super(MayaCacheJob, self)._initialize_job()
        
        self.job_dict['Comment'] = 'Maya Cache'
    
    def _get_command(self):
        
        command = "cmds.cacheFile(f=output_name,format='OneFile', points = nodes, dir = cache_path, ws = True, sch = True, st = %s, et = %s)" % (self.in_value, self.out_value)        
        return command
    
    def _get_script_name(self):
        
        return 'deadline_cache_maya.py'