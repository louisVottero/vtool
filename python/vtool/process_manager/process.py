# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

import os
import sys
import traceback
import string
import subprocess
import threading
import inspect
from functools import wraps
import __builtin__

from vtool import util
from vtool import util_file
from vtool import data

in_maya = False

def decorator_undo_chunk(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        try:
            return_value = function(*args, **kwargs)
        except:
            pass
        
        return return_value
    return wrapper

if util.is_in_maya():
    in_maya = True
    import maya.cmds as cmds
    from vtool.maya_lib import core
    
    decorator_undo_chunk = core.undo_chunk


from vtool import logger
log = logger.get_logger(__name__) 

log.info('Accessing')

def find_processes(directory = None, return_also_non_process_list = False, stop_at_one = False):
    """
    This will try to find the processes in the supplied directory. If no directory supplied, it will search the current working directory.
    
    Args:
        directory(str): The directory to search for processes.
        
    Returns:
        list: The procceses in the directory.
    """
    
    if not directory:
        directory = util_file.get_cwd()
    
    found = []
    found_non = []
    
    log.debug('Find Processes %s' % directory)
    
    root = directory
    dirs = []
    try:
        dirs = os.listdir(directory)
    except:
        pass
    
    for folder in dirs:
        
        if stop_at_one:
            #only check found not found_non, because function is find "processes"
            if found:
                break
            
            if found_non and return_also_non_process_list:
                break
            
        if folder.startswith('.'):
            continue
        
        full_path = util_file.join_path(directory, folder)
        
        if is_process(full_path):
            found.append(folder)    
        else:
            if return_also_non_process_list:
                if is_interesting_folder(folder, directory):
                    found_non.append(folder)
        
    if not return_also_non_process_list:
        return found
    if return_also_non_process_list:
        return [found, found_non]

def is_interesting_folder(folder_name, directory):
    full_path = util_file.join_path(directory, folder_name)
    if folder_name.find('.') > -1:
        
        if not folder_name.startswith('.'):
            
            if not util_file.is_file(full_path):
                return True
    else:
        return True
        
    return False    
        
def is_process(directory):
    
    if not directory:
        return False
    
    code_path = util_file.join_path(directory, '.code')
    
    if not util_file.exists(code_path):
        return False
    
    return True

def is_process_enabled(directory):
    path = directory
        
    enable_path = util_file.join_path(path,Process.enable_filename)
        
    if util_file.exists(enable_path):
        return True
        
    return False

def get_unused_process_name(directory = None, name = None):
    """
    This will try to find a a process named process in the directory.
    
    It will increment the name to process1 and beyond until it finds a unique name. 
    If no directory supplied, it will search the current working directory.
    
    Args:
        directory (str): Direcotry to search for processes.
        name (str): name to give the process.
        
    Returns:
        str: The unique process name.
    """
    if not directory:
        directory = util_file.get_cwd()
    
    processes = find_processes(directory)
    
    
    if name == None:
        name = Process.description
        
    new_name = name
    
    not_name = True
    
    inc = 1
    
    while not_name:
        if new_name in processes:
            
            new_name = util.increment_last_number(new_name)
            
        if not new_name in processes:
            not_name = False
            
        if inc > 1000:
            break
        
    return new_name

__internal_script_running = None

def decorator_process_run_script(function):
    #decorator meant only to work with run_script, not to be used
     
    @wraps(function)
    
    def wrapper(self, script, hard_error = True, settings = None):
        
        if in_maya:
            cmds.refresh()
        
        global __internal_script_running
        
        if __internal_script_running == None:
            
            __internal_script_running = True
            reset = True
            util.start_temp_log()
            try:
                if in_maya:
                    cmds.undoInfo(openChunk = True)
            except:
                util.warning('Trouble prepping maya for script')
        
        reset_process_builtins(self)
        value = None
        
        try:
            value = function(self, script, hard_error, settings)
        except:
            pass
        
        if 'reset' in locals():
            
            __internal_script_running = None
            reset_process_builtins(self)
            
            if in_maya:
                cmds.undoInfo(closeChunk = True)
                
            util.end_temp_log()
        
        return value
    
    return wrapper
    
class Process(object):
    """
    This class has functions to work on individual processes in the Process Manager.
    """
    
    description = 'process'
    data_folder_name = '.data'
    code_folder_name = '.code'
    backup_folder_name = '.backup'
    process_data_filename = 'manifest.data'
    enable_filename = '.enable'
    
    def __init__(self, name = None):
        
        log.debug('Initialize process %s' % name)
        
        self.directory = util_file.get_cwd()
        
        self.process_name = name
        
        self.external_code_paths = []
        
        self._reset()
        self._update_options = True
        
        

    def _reset(self):
        self.parts = []
        self.option_values = {}
        self.runtime_values = {}
        self.option_settings = None
        self.settings = None
        self._control_inst = None
        self._runtime_globals = {}
        self._data_override = None
        
    def _get_override_path(self):
        if not self._data_override:
            return self.get_path()
        if self._data_override:
            return self._data_override.get_path()
       
        
    def _setup_options(self):
        
        if not self.option_settings:
            self._load_options()
        
    def _load_options(self):
    
        log.debug('Setup options')
        options = util_file.SettingsFile()
        self.option_settings = options
        self.option_settings.set_directory(self._get_override_path(), 'options.json')
        
    def _setup_settings(self):
        
        if not self.settings:
            log.debug('Setup process settings')
            settings = util_file.SettingsFile()
            self.settings = settings
            
            self.settings.set_directory(self._get_override_path(), 'settings.json')
            
    def _set_name(self, new_name):
        
        new_name = new_name.strip()
        
        self.process_name = new_name
            
    def _handle_old_folders(self, path):
        
        #here temporarily until old paths are out of use... 
        #could take a long time.

        if util_file.is_dir(self.get_code_path()):
            return
        
        old_data_name = self.data_folder_name.replace('.', '_')
        old_code_name = self.code_folder_name.replace('.', '_')
        
        old_data_path = util_file.join_path(path, old_data_name)
        old_code_path = util_file.join_path(path, old_code_name)
        
        if util_file.is_dir(old_data_path):
            util_file.rename(old_data_path, self.data_folder_name)
            
        if util_file.is_dir(old_code_path):
            util_file.rename(old_code_path, self.code_folder_name)
        
    def _create_folder(self):
        
        path = util_file.create_dir(self.process_name, self.directory)
    
        if path and util_file.is_dir(path):

            self._handle_old_folders(path)
            
            util_file.create_dir(self.data_folder_name, path)
            code_folder = util_file.create_dir(self.code_folder_name, path)
            util_file.create_dir(self.backup_folder_name, path)
            
            manifest_folder = util_file.join_path(code_folder, 'manifest')
            if not util_file.is_dir(manifest_folder):
                self.create_code('manifest', 'script.manifest')
        
        return path
    
    def _create_sub_data_folder(self, data_name):
        
        data_path = self.get_data_folder(data_name)
        
        path = util_file.create_dir('.sub', data_path)
        return path
            
    def _get_path(self, name):
        
        directory = util_file.join_path(self.get_path(), name)
                
        return directory
    
    def _reset_builtin(self, old_process = None, old_cmds = None, old_show = None, old_warning = None):
        
        reset_process_builtins(self)
        
    
    def _get_control_inst(self):
        
        if not self._control_inst:
            self._control_inst = util_file.ControlNameFromSettingsFile(self.get_path())   

    def _refresh_process(self):
        
        self._setup_options()
        self._setup_settings()
        
        self.runtime_values = {}
        
        if self._control_inst:
            self._control_inst.set_directory(self.get_path())
    
    def _pass_module_globals(self,module):
        """
        this was a test that might go further in the future. 
        the major problem was integer variables where not passable the first time. 
        """
        keys = dir(module)
        
        for key in keys:
            
            
            
            if key.startswith('__'):
                continue
            
            result = eval('module.%s' % key)
            
            exec('self._runtime_globals["%s"] = result' % key)
            
        for global_key in self._runtime_globals:
            
            if not global_key in keys:
                
                module.goo = self._runtime_globals[global_key]
                value = self._runtime_globals[global_key]
                
                assign = 'module.%s = value' % key 
                
                exec(assign)
        
        
    def _get_data_instance(self, name, sub_folder):
        path = self.get_data_path()
            
        data_folder = data.DataFolder(name, path)
        
        current_sub_folder = sub_folder
        
        if sub_folder and sub_folder != False:
            current_sub_folder = data_folder.get_current_sub_folder()
            data_folder.set_sub_folder(sub_folder)
        if sub_folder == False:
            data_folder.set_sub_folder_to_default()
        
        instance = data_folder.get_folder_data_instance()      
            
        return instance, current_sub_folder
     
    def _source_script(self, script):
        
        util_file.delete_pyc(script)
        
        self._reset_builtin()
        
        setup_process_builtins(self)
        
        util.show('Sourcing %s' % script)
        
        module = util_file.source_python_module(script)
        
        status = None
        init_passed = False
        
        if module and type(module) != str:
            init_passed = True
        
        if not module or type(module) == str:
            status = module
            init_passed = False   
            
        return module, init_passed, status
        
    def _format_option_value(self, value):
        
        new_value = value
        
        option_type = None
        
        if type(value) == list:
            
            try:
                option_type = value[1]
            except:
                pass    
            value = value[0]
                
            if option_type == 'dictionary':
                
                new_value = value[0]
                
                if type(new_value) == list:
                    new_value = new_value[0]
            
            if option_type == 'note':
                new_value = value[0]
                
                
        
        if not option_type == 'script':
            if type(value) == str or type(value) == unicode:
                eval_value = None
                try:
                    if value:
                        eval_value = eval(value)
                except:
                    pass
               
                if eval_value:
                    if type(eval_value) == list or type(eval_value) == tuple or type(eval_value) == dict:
                        new_value = eval_value
                        value = eval_value
            
            if type(value) == str or type(value) == unicode:
                if value.find(',') > -1:
                    new_value = value.split(',')
            
        log.debug('Formatted value: %s' % new_value)
                
        return new_value
            

    def _get_parent_process_path(self, from_override = False):
        
        if not from_override:
            process_path = self.get_path()
        if from_override:
            process_path = self._get_override_path()
        
        dir_name = util_file.get_dirname(process_path)
        
        process = Process()
        process.set_directory(dir_name)
        
        if process.is_process():
        
            basename = util_file.get_basename(dir_name)
            path = util_file.get_dirname(dir_name)
        
            return basename, path
        
        else:
            return None, None

    def _get_code_file(self, name, basename = False):
        """
        Args: 
            name (str): The name of a code folder in the process.
            basename (bool): Wether to return the full path or just the name of the file.
        
        Returns:
            str: The path to the code file with the specified name in the current process. 
        """
        
        path = util_file.join_path(self.get_code_path(), name)
       
        code_name = util_file.get_basename(path)
        
        if not code_name == 'manifest':
            code_name = code_name + '.py'
        if code_name == 'manifest':
            code_name = code_name + '.data'
        
        if basename:
            return_value = code_name
        if not basename:
            
            return_value = util_file.join_path(path, code_name)
        
        return return_value

    def set_directory(self, directory):
        """
        Args:
            directory (str): Directory path to the process that should be created or where an existing process lives.
        """
        
        log.debug('Set process directory: %s' % directory) 
        self.directory = directory  
        
        self._reset()    
        
    def load(self, name):
        """
        Loads the named process into the instance.
        
        Args:
            name (str): Name of a process found in the directory.
            
        Returns:
            None
            
        """
        log.debug('Load process: %s' % name)
        self._set_name(name)
        
        self._reset()
        
    def set_external_code_library(self, directory):
        """
        Args:
            directory (str,list): Directory or list of directories where code can be sourced from. This makes it more convenient when writing scripts in a process. 
        """
        directory = util.convert_to_sequence(directory)
        
        self.external_code_paths = directory
        
    def is_process(self):
        """
        Returns:
            bool: Check to see if the initialized process is valid.
        """
        
        if not util_file.exists(self.get_code_path()):
            
            path = self.get_path()
            self._handle_old_folders(path)
            if not util_file.exists(self.get_code_path()):
                return False
        
        return True
    
    def set_enabled(self, bool_value):
        path = self.get_path()
        
        if bool_value:
            util_file.create_file(self.enable_filename, path)
        if not bool_value:
            util_file.delete_file(self.enable_filename, path, show_warning=False)
            
    def is_enabled(self):
        path = self.get_path()
        
        enable_path = util_file.join_path(path,self.enable_filename)
        
        if util_file.exists(enable_path):
            return True
        
        return False
        
    def has_sub_parts(self):
        
        process_path = self.get_path()
        
        if not process_path:
            return False
        
        files = util_file.get_folders(process_path)
        
        if not files:
            return False
        
        
        for filename in files:
            
            file_path = util_file.join_path(process_path, filename)
            
            if is_process(file_path):
                return True
            
        return False
        
    def get_non_process_parts(self):
        
        process_path = self.get_path()
        
        if not process_path:
            return
        
        folders = util_file.get_folders(process_path)
        
        found = []
        
        for folder in folders:
            
            full_path = util_file.join_path(process_path, folder)
            
            if not is_process(full_path):
                continue
            
            found.append(full_path)
            
        return found
            
            
    def get_path(self):
        """
        Returns:
            str: The full path to the process folder. 
            If the process hasn't been created yet, this will return the directory set in set_directory.        
        """
        
        if not self.directory:
            return
        
        if self.process_name:
            return util_file.join_path(self.directory, self.process_name)
        
        if not self.process_name:
            return self.directory
    
    def get_name(self):
        """
        Returns:
            str: The name of the process.
        """
        
        if not self.process_name:
            return util_file.get_basename(self.directory)
            
        
        return self.process_name
    
    def get_basename(self):
        """
        Returns:
            str: The name of the process. If no name return basename of directory.
        """
        name = self.process_name
        
        if not name:
            name = self.directory
        
        
        return util_file.get_basename(name)
    
    def _get_relative_process_path(self, relative_path, from_override = False):
        
        if not from_override:
            path = self.get_path()
        if from_override:
            path = self._get_override_path()
        
        if not path:
            return None, None
        
        split_path = path.split('/')
        split_relative_path = relative_path.split('/')
        
        up_directory = 0
        
        new_sub_path = []
        new_path = []
        
        for sub_path in split_relative_path:
            if sub_path == '..':
                up_directory +=1
            if sub_path != '..':
                new_sub_path.append(sub_path)
        
        if up_directory:
            
            new_path = split_path[:-up_directory]
            
            new_path = new_path + new_sub_path
                        
        if up_directory == 0:
            
            new_path = split_path + split_relative_path
            
            new_path_test = string.join(new_path, '/')
            
            if not util_file.is_dir(new_path_test):
                
                temp_split_path = list(split_path)
                
                temp_split_path.reverse()
                
                found_path = []
                
                for inc in range(0, len(temp_split_path)):
                    if temp_split_path[inc] == split_relative_path[0]:
                        found_path = temp_split_path[inc+1:]
                
                found_path.reverse()
                new_path = found_path + split_relative_path
        
        process_name = string.join([new_path[-1]], '/')
        process_path = string.join(new_path[:-1], '/')
        
        util.show('Relative process name: %s and path: %s' % (process_name, process_path))
        
        return process_name, process_path
        
    def get_relative_process(self, relative_path):
        """
        Args:
            relative_path (str): The path to a relative process. 
        Returns:
            Process:An instance of a process at the relative path. 
            
            If a name with no backslash is supplied, this will return any matching process parented directly under the current process. 
            
            A relative path like, '../face' or '../../other_character' can be used. 
            
            Every '..' signifies a folder above the current process. 
        """

        
        process_name, process_directory = self._get_relative_process_path(relative_path)
        
        if not process_name and process_directory:
            process_name = util_file.get_basename(process_directory)
            process_directory = util_file.get_dirname(process_directory)
        if not process_name and not process_directory:
            return
        """
        test_path = util_file.join_path(process_directory, process_name)
        if not util_file.is_dir(test_path):
            util.warning('%s is not a valid path.' % test_path)
        """
        
        process = Process(process_name)
        process.set_directory(process_directory)
        
        if self._data_override:
            override_process_name, override_process_directory = self._get_relative_process_path(relative_path, from_override=True)
            
            if override_process_name:
            
                override_process = Process(override_process_name)
                override_process.set_directory( override_process_directory ) 
                process.set_data_override(override_process)
        
        return process
    
    def get_sub_process_count(self):
        """
        Returns:
            int: The number of sub processes under the current.
        """
        found = self.get_sub_processes()
        
        if found:
            return len(found)
    
    def get_sub_processes(self):
        """
        Returns:
            list: The process names found directly under the current process.
        """
        process_path = self.get_path()
        
        found = find_processes(process_path)
        
        return found
    
    def get_sub_process(self, part_name):
        """
        Args:
            part_name (str): The name of a child process.
            
        Returns:
            Process: A sub process if there is one that matches part_name.
        """
        
        
        part_process = Process(part_name)
        part_process.set_directory(self.get_path())  
        
        return part_process    
        
    def get_sub_process_by_index(self, index):
        
        found = self.get_sub_processes()
        
        if index < len(found):
            
            sub_process = Process(found[index])
            sub_process.set_directory(self.get_path())
            return sub_process
        
    def get_parent_process(self):
        
        name, path = self._get_parent_process_path()
        
        if not name:
            return
        
        parent_process = Process(name)
        parent_process.set_directory(path)
        
        if self._data_override:
            name,path = self._get_parent_process_path(from_override = True)
            
            if name:
                override_process = Process(name)
                override_process.set_directory(path)
                parent_process.set_data_override(override_process) 
        
        util.show('Parent process: %s' % parent_process.get_path())
            
        return parent_process
        
    def get_empty_process(self, path = None):
        
        process = Process()
        process.set_directory(path)
        return process
        
    def get_backup_path(self, directory = None):
        
        if not self.directory:
            return None
        
        backup_directory = None
        
        if directory:
            backup_directory = directory
        
        if not directory:
            settings = util_file.get_vetala_settings_inst()
            backup = settings.get('backup_directory')
        
            if util_file.is_dir(backup):
            
                project = settings.get('project_directory')    
                
                backup_directory = self.directory    
                
                backup_settings = util_file.SettingsFile()
                backup_settings.set_directory(backup)
                project_name = util_file.fix_slashes(project)
                project_name = project_name.replace('/', '_')
                project_name = project_name.replace(':', '_')
                backup_settings.set(project_name, project)
                
                backup_directory = util_file.create_dir(project_name, backup)
                
                process_path =  self.get_path()
                common_path = util_file.remove_common_path_simple(project, process_path)
                
                if common_path:
                    backup_directory = util_file.create_dir(util_file.join_path(backup_directory, common_path))
        
        if not backup_directory:
            backup_directory = self.get_path()
        
        backup_path = util_file.join_path(backup_directory, self.backup_folder_name)    
        
        return backup_path
        
    def backup(self, comment = 'Backup', directory = None):
        
        backup_path = self.get_backup_path(directory)
        
        backup_path = util_file.create_dir('temp_process_backup', backup_path)
        
        target_process = Process()
        target_process.set_directory(backup_path)
        
        util.show('Backing up to custom directory: %s' % backup_path)
        
        copy_process(self, target_process)
        
        version = util_file.VersionFile(backup_path)
        version.save(comment)
        
        util_file.delete_dir(backup_path)
        
    #--- data
        
    def is_data_folder(self, name, sub_folder = None):
        """
        Args:
            name (str): The name of a data folder in the process.
            
        Returns:
            bool: True if the supplied name string matches the name of the a data folder in the current process.
        """
        
        path = self.get_data_folder(name, sub_folder)
        
        if not path:
            return False
        if util_file.is_dir(path):
            return True
        
        return False
        
    def get_data_path(self):
        """
        Returns:
            str: The path to the data folder for this process.
        """
        if not self._data_override:
            return self._get_path(self.data_folder_name)
        
        if self._data_override:
            return self._data_override._get_path(self.data_folder_name)
    
    def get_data_folder(self, name, sub_folder = None):
        """
        Args:
            name (str): The name of a data folder in the process.

        Returns:
            str: The path to the data folder with the same name if it exists.
        """
        
        folders = self.get_data_folders()
        
        if not folders:
            return
        
        for folder in folders:
            if folder == name:
                
                if not sub_folder:
                    return util_file.join_path(self.get_data_path(), name)
                if sub_folder:
                    sub_folder_path = util_file.join_path(self.get_data_sub_path(name), sub_folder) 
                    return  sub_folder_path
    
    def cache_data_type_read(self, name):
        
        data_folder = data.DataFolder(name, self.get_data_path())
        
        data_type = util_file.join_path(data_folder.folder_path, 'data.json')
        
        util_file.ReadCache.cache_read_data(data_type)
        
    def delete_cache_data_type_read(self, name):
        
        data_folder = data.DataFolder(name, self.get_data_path())
        data_type = util_file.join_path(data_folder.folder_path, 'data.json')
        
        util_file.ReadCache.remove_read_data(data_type)
       
    def get_data_type(self, name):
        """
        Args:
            name (str): The name of a data folder in the process.
            
        Returns:
            str: The name of the data type of the data folder with the same name if it exists.
        """
        
        data_folder = data.DataFolder(name, self.get_data_path())
        data_type = data_folder.get_data_type()
        
        return data_type
    
    def get_data_file_or_folder(self, name, sub_folder_name = None):
        """
        Data is either saved to a top file or a top folder. This is the main data saved under the data folder. 
        This file or folder is used for versioning. 
        This will return the file or folder that gets versioned.
        """
        
        path = self.get_data_path()
        data_folder = data.DataFolder(name, path)
            
        instance = data_folder.get_folder_data_instance()
        
        if not instance:
            return
        
        filepath = instance.get_file_direct(sub_folder_name)
        
        return filepath
    
    def get_data_version_count(self, data_name):
        
        data_folder = self.get_data_file_or_folder(data_name)
        
        version = util_file.VersionFile(data_folder)
        return len( version.get_version_numbers() )
    
    def get_data_versions(self, data_name):
        
        data_folder = self.get_data_file_or_folder(data_name)
        
        version = util_file.VersionFile(data_folder)
        return version.get_version_numbers() 
    
    def get_data_version_paths(self, data_name):
        data_folder = self.get_data_file_or_folder(data_name)
        
        version = util_file.VersionFile(data_folder)
        paths = version.get_versions(return_version_numbers_also = False)
        
        found = []
        for path in paths:
            
            path = version.get_version_path(path)
            found.append(path)
            
        return found
        
    def get_data_version_path(self, data_name, version_number):
        data_folder = self.get_data_file_or_folder(data_name)
        
        version = util_file.VersionFile(data_folder)
        path = version.get_version_path(version_number)
        
        return path
    
    
    def get_data_folders(self):
        """
        Returns:
            list: A list of data folder names found in the current process.
        """
        directory = self.get_data_path()
        
        return util_file.get_folders(directory)  
     
    def get_data_instance(self, name, sub_folder = None):
        """
        Args:
            name (str): The name of a data folder in the process. 
            
        Returns:
            Process: An instance of the data type class for data with the specified name in the current process. 
            
            This gives access to the data functions like import_data found in the data type class.
        """
        path = self.get_data_path()
        data_folder = data.DataFolder(name, path)
        
        return data_folder.get_folder_data_instance()
     
    def create_data(self, name, data_type, sub_folder = None):
        """
        Args:
            name (str): The name of a data folder in the process.
            data_type (str): A string with the name of the data type of the data in the process.
        
        Returns:
            str: The path to the new data folder.
        
        """
        
        orig_name = name
        path = self.get_data_path()
        
        test_path = util_file.join_path(path, name)
        if not sub_folder:
            test_path = util_file.inc_path_name(test_path)
        name = util_file.get_basename(test_path)
        
        data_folder = data.DataFolder(name, path)
        data_folder.set_data_type(data_type)
        
        return_path = data_folder.folder_path
        
        if sub_folder:
            
            sub_path = self.get_data_sub_path(orig_name)
            
            sub_folder_path = util_file.join_path(sub_path, sub_folder)
            
            if util_file.is_dir(sub_folder_path):
                return sub_folder_path
            
            sub_folder_path = util_file.inc_path_name(sub_folder_path)
            
            return_path = util_file.create_dir(sub_folder_path)
                
        return return_path
    
    
    def has_sub_folder(self, data_name, sub_folder_name):
        """
        Has a sub folder of name.
        """    
        
        sub_folders = self.get_data_sub_folder_names(data_name)
        
        if sub_folder_name in sub_folders:
            return True
        
        return False
    
    def create_sub_folder(self, data_name, sub_folder_name):
        
        data_type = self.get_data_type(data_name)
        
        return self.create_data(data_name, data_type, sub_folder_name)
        
    def get_data_sub_path(self, name):
        """
        Get that path where sub folders live
        """
        
        path = self._create_sub_data_folder(name)
        
        return path
    
    def get_data_sub_folder_names(self, data_name):
        
        sub_folder = self.get_data_sub_path(data_name)
        
        sub_folders = util_file.get_folders(sub_folder)
        
        return sub_folders
    
        
    def get_data_current_sub_folder(self, name):
        """
        Get the currently set sub folder
        """
        
        
        
        data_folder = data.DataFolder(name, self.get_data_path())
        sub_folder = data_folder.get_current_sub_folder()
        
        return sub_folder
    
    def get_data_current_sub_folder_and_type(self, name):
        """
        Get the currently set sub folder and its data type
        """
        data_folder = data.DataFolder(name, self.get_data_path())
        data_type = data_folder.get_data_type()
        sub_folder = data_folder.get_sub_folder()
        
        return sub_folder, data_type
    
    def import_data(self, name, sub_folder = None):
        """
        Convenience function which will run the import_data function found on the data_type instance for the specified data folder.
        
        Args:
            name (str): The name of a data folder in the process.
        
        Returns:
            None
        """
        
        
        data_folder_name = self.get_data_folder(name)
        
        util.show('Import data in: %s' % data_folder_name)
        
        if not util_file.is_dir(data_folder_name):
            util.warning('%s data does not exist in %s' % (name, self.get_name()) )
            return
        
        instance, original_sub_folder = self._get_data_instance(name, sub_folder)
        
        if hasattr(instance, 'import_data'):
            value = instance.import_data()
            
            instance.set_sub_folder(original_sub_folder)
            
            return value
        else:
            util.warning('Could not import data %s in process %s.  It has no import function.' % (name, self.process_name))        
        
    
    def open_data(self, name, sub_folder = None):
        
        data_folder_name = self.get_data_folder(name)
        
        util.show('Open data in: %s' % data_folder_name)
        
        if not util_file.is_dir(data_folder_name):
            util.show('%s data does not exist in %s' % (name, self.get_name()) )
            return
            
        instance, original_sub_folder = self._get_data_instance(name, sub_folder)
        
        return_value = None
        
        if hasattr(instance, 'import_data') and not hasattr(instance,'open'):
            return_value = instance.import_data()
            instance.set_sub_folder(original_sub_folder)
            return return_value
        
        if hasattr(instance, 'open'):
            return_value = instance.open()
            instance.set_sub_folder(original_sub_folder)
            return return_value
        else:
            util.warning('Could not open data %s in process %s.  It has no open function.' % (name, self.process_name))
    
        
        
    def reference_data(self, name, sub_folder = None):
                
        data_folder_name = self.get_data_folder(name)
        
        util.show('Reference data in: %s' % data_folder_name)
        
        if not util_file.is_dir(data_folder_name):
            util.show('%s data does not exist in %s' % (name, self.get_name()) )
            return

        instance, original_sub_folder = self._get_data_instance(name, sub_folder)
        
        return_value = None
        
        if hasattr(instance, 'maya_reference_data'):
            return_value = instance.maya_reference_data()
            
            
        else:
            util.warning('Could not reference data %s in process %s.  %s has no reference function.' % (name, self.process_name))
            
        instance.set_sub_folder(original_sub_folder)
            
        return return_value
            
    def save_data(self, name, comment = '', sub_folder = None):
        """
        Convenience function that tries to run the save function found on the data_type instance for the specified data folder. Not all data type instances have a save function. 
        
        Args:
            name (str): The name of a data folder in the process.
        
        Returns:
            None
        """
        
        instance, original_sub_folder = self._get_data_instance(name, sub_folder)
                
        if not comment:
            comment = 'Saved through process class with no comment.'
        
        if hasattr(instance, 'save'):
            saved = instance.save(comment)
            
            instance.set_sub_folder(original_sub_folder)
            
            if saved:
                return True
        
        return False
           
    def export_data(self, name, comment = '', sub_folder = None, list_to_export = []):
        """
        Convenience function that tries to run the export function found on the data_type instance for the specified data folder. Not all data type instances have a save function. 
        
        Args:
            name (str): The name of a data folder in the process.
        
        Returns:
            None
        """
        
        instance, original_sub_folder = self._get_data_instance(name, sub_folder)
                
        if not comment:
            comment = 'Exported through process class with no comment.'
        
        if hasattr(instance, 'export_data'):
            
            arg_spec = inspect.getargspec(instance.export_data)
            if 'selection' in arg_spec.args:
                exported = instance.export_data(comment, selection = list_to_export)
            else:
                exported = instance.export_data(comment)
                
            #need to get all the data types returning true or false on export
            
            instance.set_sub_folder(original_sub_folder)
            
            #if exported:
            #    return True
        
        #return False
            
    
    def rename_data(self, old_name, new_name):
        """
        Renames the data folder specified with old_name to the new_name.
        
        Args:
            old_name (str): The current name of the data.
            new_name (str): The new name for the data.
            
        Returns:
            str: The new path to the data if rename was successful.
        """
        data_folder = data.DataFolder(old_name, self.get_data_path())
        
        return data_folder.rename(new_name)
    
    def delete_data(self, name, sub_folder = None):
        """
        Deletes the specified data folder from the file system.
        
        Args: 
            name (str): The name of a data folder in the process.
        
        Returns:
            None
        """
        
        data_folder = data.DataFolder(name, self.get_data_path())
        data_folder.set_sub_folder(sub_folder)
        data_folder.delete()
    
    def copy_sub_folder_to_data(self, sub_folder_name, data_name):
        
        if not self.has_sub_folder(data_name, sub_folder_name):
            util.warning('Data %s has no sub folder: %s to copy from.' % (data_name, sub_folder_name))
            return
        
        source_file = self.get_data_file_or_folder(data_name, sub_folder_name)
        
        
        target_file = self.get_data_file_or_folder(data_name)
        
        copy(source_file, target_file)
        
        
        
    
    def copy_data_to_sub_folder(self, data_name, sub_folder_name):
        
        if not self.has_sub_folder(data_name, sub_folder_name):
            util.warning('Data %s has no sub folder: %s to copy to.' % (data_name, sub_folder_name))
            return
        
        source_file = self.get_data_file_or_folder(data_name)
        target_file = self.get_data_file_or_folder(data_name, sub_folder_name)
                
        copy(source_file, target_file)
        
    def remove_data_versions(self, name, sub_folder = None, keep = 1):
        
        folder = self.get_data_folder(name, sub_folder)
        
        util_file.delete_versions(folder, keep)
        
        
    #code ---
    
    def is_code_folder(self, name):
        """
        Args: 
            name (str): The name of a code folder in the process.
            
        Returns:
            bool: If the supplied name string matches the name of a code folder in the current process. 
            
        """
        path = self.get_code_folder(name)
        
        if not path:
            return False
        if util_file.is_dir(path):
            return True
        
        return False
        
    def get_code_path(self):
        """
        Returns:
            str: The path to the code folder for this process.
        """
        return self._get_path(self.code_folder_name)
    
    def get_code_folder(self, name):
        """
        Args: 
            name (str): The name of a code folder in the process.
            
        Returns:
            str: A path to the code folder with the supplied name string if it exists.
        """
        
        if name.endswith('.py'):
            name = name[:-3]
            
        if name.endswith('.data'):
            name = name[:-5]
        
        folder = util_file.join_path(self.get_code_path(), name)
        
        if util_file.is_dir(folder):
            return folder

    def get_code_folders(self, code_name = None):
        """
        Returns:
            list: A list of code folder names found in the current process. 
        """
        directory = self.get_code_path()
        
        if code_name:
            directory = util_file.join_path(directory, code_name)
        
        return util_file.get_folders_without_prefix_dot(directory, recursive = True)  
    
    def get_top_level_code_folders(self):
        
        folders = self.get_code_folders()
        
        found = []
        
        for folder in folders:
            if folder.count('/') > 1:
                continue
            
            found.append(folder)
            
        return found


    def get_code_names(self):
        codes, states = self.get_manifest()
        
        code_names = []
        
        if not codes:
            return code_names
        
        
        
        for code in codes:
            
            code_name = code.split('.')
            
            if not self.is_code_folder(code_name[0]):
                continue
            
            if len(code_name) > 1 and code_name[1] == 'py':
                code_names.append(code_name[0])
        
        code_names.insert(0, 'manifest')
        
        return code_names

    def get_code_children(self, code_name):
        
        found = []
        
        code_name = util_file.remove_extension(code_name)
        
        scripts, states = self.get_manifest()
        
        for script in scripts:
            if script.find('/') == -1:
                continue
            
            if script.startswith(code_name + '/'):
                
                sub_script = script[len(code_name+'/'):]
                
                if not sub_script.find('/') > -1:
                    found.append(script)
        
                
        return found
        
        

    def get_code_type(self, name):
        """
        Args: 
            name (str): The name of a code folder in the process.
            
        Returns: 
            str: The code type name of the code folder with the supplied name if the code folder exists. Otherwise return None. Right now only python code type is used by the Process Manager.
        """
    
        #this was added because data folder is sometimes faulty
        path = util_file.join_path(self.get_code_path(), name)
        python_file = util_file.join_path(path, util_file.get_basename(name) + '.py')
        
        if util_file.is_file(python_file):
            data_type = 'script.python'
            return data_type
        
        
        data_folder = data.DataFolder(name, self.get_code_path())
        data_type = data_folder.get_data_type()
        
        return data_type
    
    def get_code_files(self, basename = False):
        """
        Args: 
            basename (bool): Wether to return the full path or just the name of the file.
        
        Returns:
            list: The path to the code files found in the code folder for the current process. 
            If basename is True, only return the file names without the path.             
        """
        
        
        directory = self.get_code_path()
        
        #folders = util_file.get_folders(directory)
        
        files = []
        
        folders = self.get_code_folders()
        
        
        for folder in folders:
            
            data_folder = data.DataFolder(folder, directory)
            data_instance = data_folder.get_folder_data_instance()
            
            if data_instance:

                file_path = data_instance.get_file()

                if not basename:
                    files.append(file_path)
                if basename:
                    
                    rel_file_path = util_file.remove_common_path_simple(directory, file_path)
                    split_path = rel_file_path.split('/')
                    
                    code_path = string.join(split_path[:-1], '/')
                    files.append(code_path)

        return files
    
    def get_code_file(self, name, basename = False):
        """
        Args: 
            name (str): The name of a code folder in the process.
            basename (bool): Wether to return the full path or just the name of the file.
        
        Returns:
            str: The path to the code file with the specified name in the current process. 
        """
        
        path = self._get_code_file(name, basename)
        
        
        if not util_file.exists(path):
            util.warning('Could not find code file: %s' % name)
            return
        
        return path

    def get_code_name_from_path(self, code_path):
        
        split_path = code_path.split('%s/' % self.code_folder_name)
        
        if len(split_path) == 2:
            parts = split_path[1].split('/')
            
            if len(parts) > 2:
                last_part = util_file.remove_extension(parts[-1])
                
                if last_part == parts[-2]:
                    
                    if len(parts) > 2:
                        return string.join(parts[:-1], '/')

                if last_part != parts[-2]:
                    return string.join(parts, '/')
                    
            if len(parts) == 2:
                return parts[0]
                

    def get_code_module(self, name):
        """
        Returns:
            module: The module instance
            bool:  If the module sourced properly or not
            str:  The status of the source.  Error messages etc. 
            
        """
        
        script = self.get_code_file(name)
        
        module, init_passed, status = self._source_script(script)
        
        return module, init_passed, status
        
        
    def create_code(self, name, data_type = 'script.python', inc_name = False, import_data = None):
        """
        Create a new code folder with the specified name and data_type. 
        
        Args:
            name (str): The name of the code to create.
            data_type (str): Usually 'script.python'.
            inc_name (bool): Wether or not to increment the name.
            import_data (str): The name of data in the process. 
            Lines will be added to the code file to import the data.
        
        Returns:
            str: Filename
        """
        
        path = self.get_code_path()
        
        if not path:
            return
        
        if inc_name:
            test_path = util_file.join_path(path, name)
            
            if util_file.exists(test_path):
                test_path = util_file.inc_path_name(test_path)
                
                name = util_file.get_basename(test_path)
                path = util_file.get_dirname(test_path)
                
        
        log.info('Create code %s at path %s' % (name, path))
        
        data_folder = data.DataFolder(name, path)
        data_folder.set_data_type(data_type)
        
        data_instance = data_folder.get_folder_data_instance()
        
        if not data_instance:
            return
        
        if name == 'manifest':
            data_instance.create()
            return
    
        if import_data:
            data_instance.set_lines(['','def main():',"    process.import_data('%s')" % import_data])
        if not import_data:
            data_instance.set_lines(['','def main():','    return'])
    
        data_instance.create()
    
        filename = data_instance.get_file()
        
        if not self.is_in_manifest('%s.py' % name):
            
            self.set_manifest(['%s.py' % name], append = True)
        
        return filename 
        
    def move_code(self, old_name, new_name):
        
        code_path = self.get_code_path()
        
        old_path = util_file.join_path(code_path, old_name)
        new_path = util_file.join_path(code_path, new_name)
        
        basename = util_file.get_basename(new_name)
        dirname = util_file.get_dirname(new_name)
        
        test_path = new_path
        
        if util_file.is_dir(test_path):
            
            last_number = 1
        
            while util_file.is_dir(test_path):
                
                basename = util.replace_last_number(basename, last_number)
                
                new_name = basename
                
                if dirname:
                    new_name = util_file.join_path(dirname, basename)
                
                test_path = util_file.join_path(code_path, new_name) 
                
                last_number += 1
                
        util_file.move(old_path, test_path)
        
        file_name = new_name
        
        old_basename = util_file.get_basename(old_name)
        new_basename = util_file.get_basename(new_name)
        
        update_path = util_file.join_path(test_path, old_basename + '.py')
        
        util_file.rename(update_path, new_basename + '.py')
        
        return file_name
    
    def rename_code(self, old_name, new_name):
        """
        Renames the code folder specified with old_name to the new_name.
        
        Args:
            old_name (str): The current name of the code.
            new_name (str): The new name for the code.
            
        Returns:
            str: The new path to the code if rename was successful.
        """
        
        new_name = util.clean_file_string(new_name)
        new_name = new_name.replace('.', '_')
        
        old_len = old_name.count('/')
        new_len = new_name.count('/')
        
        if old_len != new_len:
            util.warning('Rename works on code folders in the same folder. Try move instead.')
            return
        
        sub_new_name = util_file.remove_common_path(old_name, new_name)
        
        code_folder = data.DataFolder(old_name, self.get_code_path())
        code_folder.rename(sub_new_name)
        
        #instance = code_folder.get_folder_data_instance()
                
        #file_name = instance.get_file()
        #if file_name:
        #    file_name = util_file.get_basename(file_name)
            
        name = new_name + '.py'
            
        return name
    """
    def duplicate_code(self, name):
        
        source_path = util_file.join_path(self.get_code_path(), name)
        destination_path = util_file.join_path(self.get_code_path(), '%s_copy' % name)
        
        util_file.copy_dir(source_path, destination_path)
        
        return destination_path
    """
    def delete_code(self, name):
        """
        Deletes the specified data folder from the file system.
        
        Args: 
            name (str): The name of a data folder in the process.
        
        Returns:
            None
        """
        util_file.delete_dir(name, self.get_code_path())
        
    def remove_code_versions(self, code_name, keep = 1):
        
        folder = self.get_code_folder(code_name)
        
        util_file.delete_versions(folder, keep)
        
    #--- settings
    
    def get_setting_names(self):
        
        option_file = self.get_option_file()
        option_name = util_file.get_basename_no_extension(option_file)
        
        settings_file = self.get_settings_file()
        settings_name = util_file.get_basename_no_extension(settings_file)
        
        return [settings_name, option_name]
    
    def get_setting_file(self, name):
        
        if name == 'options':
            return self.get_option_file()
        
        if name == 'settings':
            return self.get_settings_file()
    
    def get_settings_file(self):
        
        self._setup_settings()
        return self.settings.get_file()
    
    def get_settings_inst(self):
        
        self._setup_settings()
        return self.settings
    
    def set_setting(self, name, value):
        self._setup_settings()
        
        self.settings.set(name, value)
            
    def get_setting(self, name):
        self._setup_settings()
        return self.settings.get(name)
        
    def get_control(self,description, side):
        
        self._get_control_inst()
        
        return self._control_inst.get_name(description, side)
        
    #--- options
    
    def has_options(self):
        self._setup_options()
        
        return self.option_settings.has_settings()
    
    def add_option(self, name, value, group = None, option_type = None):
        
        self._setup_options()
        
        if group:
            name = '%s.%s' % (group,name)
        if not group:
            name = '%s' % name
        
        print_value = None
        
        if option_type == 'script':
            print_value = value
            value = [value, 'script']
        if option_type == 'dictionary':
            print_value = value
            value = [value, 'dictionary']
        if option_type == 'reference.group':
            print_value = value
            value = [value, 'reference.group']
        if option_type == 'note':
            value = str(value)
            print_value = value
            value = [value, 'note']
        
        has_option = self.option_settings.has_setting(name) 

        if not has_option:
            util.show('Creating option: %s with a value of: %s' % (name, print_value))
        
        self.option_settings.set(name, value)
        
    def set_option(self, name, value, group = None):
        self._setup_options()
        
        if group:
            name = '%s.%s' % (group,name)
        if not group:
            name = '%s' % name
        
        self.option_settings.set(name, value)
        
    def get_unformatted_option(self, name, group = None):
        self._setup_options()
        
        if group:
            name = '%s.%s' % (group, name)
        if not group:
            name = '%s' % name
        
        value = self.option_settings.get(name)
        
        return value
        
    def get_option(self, name, group = None):
        """
        Get an option by name and group
        """
        self._setup_options()
        
        value = self.get_unformatted_option(name, group)
        
        if value == None:
            
            value = self.get_option_match(name, return_first = True)
            if value and group:
                util.warning('Access option: %s, but it was not in group: % s' % (name, group))
            
            if value == None:
                util.warning('Trouble accessing option %s.' % name)
                if self.has_option(name, group):
                    if group:
                        util.warning('Could not find option: %s in group: %s' % (name, group))
                else:
                    util.warning('Could not find option: %s' % name)
        
        
        log.info('Get option: name: %s group: %s with value: %s' % (name,group, value))
        
        value = self._format_option_value(value)
        
        util.show('Accessed - Option: %s, Group: %s, value: %s' % (name, group, value))
        
        return value
        

    def get_option_match(self, name, return_first = True):
        """
        Try to find a matching option in all the options
        """
        
        self._setup_options()
        
        option_dict = self.option_settings.settings_dict
        
        found = {}
        
        for key in option_dict:
            if key.endswith(name):
                
                if return_first:
                    
                    value = self._format_option_value(option_dict[key])
                    
                    util.show('Accessed - Option: %s, value: %s' % (name, value))
                    return value
                
                found[name] = value
        
        if not found:
            found = None
        
        return found
        
        
    def has_option(self, name, group = None):
        
        self._setup_options()
        
        if group:
            name = '%s.%s' % (group, name)
        #if not group:
        #    name = '%s' % name
        
        return self.option_settings.has_setting_match(name)
        
    def get_options(self):
        
        self._setup_options()
        
        options = []
        
        if self.option_settings:
            
            options = self.option_settings.get_settings()
            
        return options
        
    def get_option_file(self):
        
        self._setup_options()
        return self.option_settings.get_file()
        
    def clear_options(self):
        
        if self.option_settings:
            self.option_settings.clear()
        

    def save_default_option_history(self):
        option_file = self.get_option_file()
        version_file = util_file.VersionFile(option_file)
        version_file.set_version_folder_name('.backup/.option_versions')
        return version_file
        
    def load_default_option_history(self):
        option_file = self.get_option_file()
        version_file = util_file.VersionFile(option_file)
        version_file.set_version_folder_name('.backup/.option_versions')
        return version_file


    def get_option_history(self):
        
        option_file = self.get_option_file()
        version_file = util_file.VersionFile(option_file)
        version_file.set_version_folder_name('.backup/.option_versions')
        return version_file
        
        
    
    #--- manifest
        
    def get_manifest(self, manifest_file = None):
        """
        Returns:
            tuple: (list, list) Two lists, scripts and states. 
            The scripts list contains the name of scripts in the manifest. 
            States contains the enabled/disabled state of the script. 
        """
        
        if not manifest_file:
            manifest_file = self.get_manifest_file()
        
        if not util_file.exists(manifest_file):
            return None, None
        
        lines = util_file.get_file_lines(manifest_file)
        
        if not lines:
            return None, None
        
        scripts = []
        states = []
        
        for line in lines:
            
            if not line:
                continue
            
            states.append(False)
            
            split_line = line.split()
            if len(split_line):
                
                script_name = string.join(split_line[:-1])
                
                scripts.append(script_name)
                
            if len(split_line) >= 2:
                
                state = eval(split_line[-1])
                
                states[-1] = state
                              
        return scripts, states
        
    def get_manifest_dict(self, manifest_file = None):
        """
        Returns:
            dict: name of code : state 
        """
        
        if not manifest_file:
            manifest_file = self.get_manifest_file()
        
        manifest_dict = {}
        
        if not util_file.is_file(manifest_file):
            return manifest_dict
        
        lines = util_file.get_file_lines(manifest_file)
        
        if not lines:
            return manifest_dict
        
        
        
        for line in lines:

            script_name = None
            
            if not line:
                continue
            
            split_line = line.split()
            
            if len(split_line):
                
                script_name = string.join(split_line[:-1])
                
                manifest_dict[script_name] = False
                
            if len(split_line) >= 2 and script_name:
                state = eval(split_line[-1])
                
                manifest_dict[script_name] = state
                              
        return manifest_dict
        
        
    def get_manifest_folder(self):
        """
        Returns:
            str: The path to the manifest folder.
        """
        code_path = self.get_code_path()
        
        path = util_file.join_path(code_path, 'manifest')
        
        if not util_file.exists(path):
            try:
                self.create_code('manifest', 'script.manifest')
            except:
                util.warning('Could not create manifest in directory: %s' % code_path)      
        
        return path
        
    def get_manifest_file(self):
        """
        Returns:
            str: The path to the manifest file.
        """
        manifest_path = self.get_manifest_folder()
        
        filename =  util_file.join_path(manifest_path, self.process_data_filename)
        
        if not util_file.exists(filename):
            self.create_code('manifest', 'script.manifest')
        
        return filename
    
    def get_manifest_scripts(self, basename = True):
        """
        Args:
            basename (bool): Wether to return the full path or just the name of the file. 
        Returns:
            list: The code files named in the manifest.  
        """
        
        manifest_file = self.get_manifest_file()
        
        if not manifest_file:
            return
        
        if not util_file.is_file(manifest_file):
            return
        
        files = self.get_code_files(False)
        
        scripts, states = self.get_manifest()
        
        if basename:
            return scripts
        
        if not basename:
            
            found = []
            
            for script in scripts:
                
                
                if script.count('/') > 0:
                    
                    dirname = util_file.get_dirname(script)
                    basename = util_file.get_basename(script)
                    
                    sub_basename = util_file.get_basename_no_extension(basename)
                    
                    script = util_file.join_path(dirname, sub_basename)
                    script = util_file.join_path(script, basename)
                
                    
                
                for filename in files:
                    
                    if not filename:
                        continue
                    
                    if filename.endswith(script):
                        
                        found.append(filename)
                        break
            
            return found
    
    def is_in_manifest(self, entry):
        
        filename = self.get_manifest_file()
        
        lines = util_file.get_file_lines(filename)
        
        for line in lines:
            
            split_line = line.split(' ')
            
            if split_line[0] == entry:
                return True
        
        return False
    
    def get_manifest_history(self):
        
        manifest_file = self.get_manifest_file()
        
        version_file = util_file.VersionFile(manifest_file)
        #version_file.set_version_folder_name('.backup/.option_versions')
        return version_file        
        
        
    
    def set_manifest(self, scripts, states = [], append = False):
        """
        This will tell the manifest what scripts to list. Scripts is a list of python files that need to correspond with code data.
        
        Args:
            scripts (list): List of scripts to add to the manifest.
            states (list): List that of states for that corresponds to the scripts list.
            append (bool): Wether to add the scripts to the end of the manifest or replace it.
        """
        
        
        
        manifest_file = self.get_manifest_file()
        
        lines = []
        
        script_count = len(scripts)
        if states:
            state_count = len(states)
        if not states:
            state_count = 0
        
        for inc in range(0, script_count):
            
            if scripts[inc] == 'manifest.py':
                continue
            
            if inc > state_count-1:
                state = False
                
            if inc < state_count:
                state = states[inc]
            
            line = '%s %s' % (scripts[inc], state)
            lines.append(line)
        
        util_file.write_lines(manifest_file, lines, append = append)
        
    def has_script(self, script_name):
        if not script_name.endswith('.py'):
            script_name = script_name + '.py'
        
        scripts, states = self.get_manifest()
        
        if script_name in scripts:
            return True
        
        return False
        
    def get_script_parent(self, script_name):
        
        if not script_name.endswith('.py'):
            script_name = script_name + '.py'
        
        scripts, states = self.get_manifest()
        
        for inc in range(0, len(scripts)):
        
            if script_name == scripts[inc]:
                
                test_inc = inc - 1
                
                if test_inc < 0:
                    break
                
                while scripts[test_inc].count('/') != scripts[inc].count('/'):
                    test_inc -= 1
                    
                    if test_inc < 0:
                        break
                
                if test_inc >= 0:
                    return scripts[test_inc]

        
    def get_previous_script(self, script_name):
        
        if not script_name.endswith('.py'):
            script_name = script_name + '.py'
        
        scripts, states = self.get_manifest()
        
        last_script = None
        last_state = None
        
        for script, state in zip(scripts, states):
            
            if last_script:
                if script_name == script:
                    return last_script, last_state 
                
            
            last_script = script
            last_state = state
        
    def insert_manifest_below(self, script_name, previous_script_name, state = False):
        
        if not script_name.endswith('.py'):
            script_name = script_name + '.py'
        if not previous_script_name.endswith('.py'):
            previous_script_name = previous_script_name + '.py'
            
        scripts, states = self.get_manifest()

        script_count = 0
        
        if scripts:
            script_count = len(scripts)
                
        code_folders = self.get_code_folders()
        
        if not script_count and not code_folders:
            return
        
        for inc in range(0, len(scripts)):
            
            script = scripts[inc]
            
            if script == previous_script_name:
                scripts.insert(inc+1, script_name)
                states.insert(inc+1, state)
                break
            
        self.set_manifest(scripts, states)
        
    def get_script_state(self, script_name):
        if not script_name.endswith('.py'):
            script_name = script_name + '.py'
            
        scripts, states = self.get_manifest()
        
        for script, state in zip(scripts, states):
            
            if script == script_name:
                return state
            
    def set_script_state(self, script_name, bool_value):
        if not script_name.endswith('.py'):
            script_name = script_name + '.py'
        
        scripts, states = self.get_manifest()
        
        for inc in range(0, len(scripts)):
            
            script = scripts[inc]
            
            if script == script_name:
                states[inc] = bool_value
        
        self.set_manifest(scripts, states)

    def sync_manifest(self):
        """
        Sync the manifest with whats on disk.
        """
        
        scripts, states = self.get_manifest()
        
        script_count = 0
        
        if scripts:
            script_count = len(scripts)
        
        synced_scripts = []
        synced_states = []
        
        code_folders = self.get_code_folders()
        
        if not script_count and not code_folders:
            return
    
        for inc in range(0,script_count):
            
            script_name = util_file.remove_extension(scripts[inc])
            
            filepath = self._get_code_file(script_name)
            
            if not util_file.exists(filepath):
                continue
            
            if scripts[inc] in synced_scripts:
                continue
            
            synced_scripts.append(scripts[inc])
            synced_states.append(states[inc])
            
            remove_inc = None
            
            for inc in range(0, len(code_folders)):
                
                if code_folders[inc] == script_name:
            
                    remove_inc = inc
                    break
                    
                if code_folders in synced_scripts:
                    
                    if not code_folders[inc].count('/'):
                        continue
                        
                    common_path = util_file.get_common_path(code_folders[inc], script_name)
                    
                    if common_path:
                        common_path_name = common_path + '.py'
                        if common_path_name in synced_scripts:
                            
                            code_script = code_folders[inc] + '.py'
            
                            synced_scripts.append(code_script)
                            synced_states.append(False)
                            
                            remove_inc = inc
                            break
            
            if not remove_inc == None:
                code_folders.pop(remove_inc)
        
        for code_folder in code_folders:
            
            code_script = code_folder + '.py'
            
            synced_scripts.append(code_script)
            synced_states.append(False)
            
        self.set_manifest(synced_scripts, synced_states)
                        
    #--- creation
        
    def add_part(self, name):
        """
        Args:
            name (str): Name for a new process.
            
        Returns:
            Process: Instnace of the added part.
        """
        part_process = Process(name)
        
        path = util_file.join_path(self.directory, self.process_name)
        
        if self.process_name:
            path = util_file.join_path(self.directory, self.process_name)
        
        if not self.process_name:
            path = self.directory
        
                
        part_process.set_directory(path)
        part_process.create()
        
        return part_process
        
    def create(self):
        """
        Create the process.
        
        Retrun
            (str): Path to the process.
        """
        return self._create_folder()
        
    def delete(self):
        """
        Delete the process.
        
        Returns:
            None
        """
        
        if self.process_name:
            util_file.delete_dir(self.process_name, self.directory)
        if not self.process_name:
            
            basename = util_file.get_basename(self.directory)
            dirname = util_file.get_dirname(self.directory)
            
            util_file.delete_dir(basename, dirname)
    
    def rename(self, new_name):
        """
        Rename the process.
        
        Args:
            new_name (str): New name for the process.
            
        Returns:
            bool: Wether or not the process was renamed properly.
        """
        
        split_name = new_name.split('/')
        
        if util_file.rename( self.get_path(), split_name[-1]):
            
            self.load(new_name)            
            return True
            
        return False
    
    #--- run
    @decorator_process_run_script
    def run_script(self, script, hard_error = True, settings = None):
        """
        Run a script in the process.
        
        Args:
            script(str): Name of a code in the process.
            hard_error (bool): Wether to error hard when errors encountered, or to just pass an error string.

        Returns:
            str: The status from running the script. This includes error messages.
        """
        
        if self._update_options:
            self.option_settings = None
            self._setup_options()
        
        orig_script = script
        
        status = None
        
        init_passed = False
        module = None
        
        try:
            
            if not util_file.is_file(script):
                script = util_file.remove_extension(script)
                script = self._get_code_file(script)
            
            if not util_file.is_file(script):
                util.show('Could not find script: %s' % orig_script)
                return
            
            name = util_file.get_basename(script)
            
            for external_code_path in self.external_code_paths:
                if util_file.is_dir(external_code_path):
                    if not external_code_path in sys.path:
                        sys.path.append(external_code_path)
            
            message = 'START\t%s\n\n' % name
            
            util.show('\n------------------------------------------------')
            util.show(message)
            
            module, init_passed, status = self._source_script(script)
            
        except Exception:

            util.warning('%s did not source' % script)
            status = traceback.format_exc()
            init_passed = False
            
            if hard_error:
                try: 
                    del module
                except:
                    util.warning('Could not delete module')
                util.error('%s\n' % status)
                raise Exception('Script did not source. %s' % script )
        
        if init_passed:
            try:
                
                if hasattr(module, 'main'):
                    
                    if not hasattr(module, 'process') or module.process == None:
                        #for legacy, if process was set to None override it with this process
                        module.process = self
                    
                    module.main()
                    status = 'Success'
                    
            except Exception:
                
                status = traceback.format_exc()
                
                if hard_error:
                    util.error('%s\n' % status)
                    raise Exception('Script errored on main. %s' % script )
                
        del module
        
        if not status == 'Success':
            util.show('%s\n' % status)
        
        message = '\nEND\t%s\n\n' % name
        util.show(message)
        
        return status
        
    def run_option_script(self, name, group = None, hard_error = True):
        
        script = self.get_option(name, group)
        
        self.run_code_snippet(script, hard_error)

    @decorator_undo_chunk
    def run_code_snippet(self, code_snippet_string, hard_error = True):
        
        script = code_snippet_string
         
        status = None
        
        try:
            
            for external_code_path in self.external_code_paths:
                if util_file.is_dir(external_code_path):
                    if not external_code_path in sys.path:
                        sys.path.append(external_code_path)
            
            builtins = get_process_builtins(self)
            
            exec(script, globals(), builtins)
            status = 'Success'
            
        except Exception:
            
            util.warning('script error!\n %s' % script)
            
            status = traceback.format_exc()
            
            if hard_error:
                util.error('%s\n' % status)
                raise
        
        if not status == 'Success':
            util.show('%s\n' % status)
        
        return status
    
    def run_script_group(self, script, clear_selection = True, hard_error = True):
        """
        This runs the script and all of its children/grandchildren.
        """
        
        status_list = []
        scripts_that_error = []
        
        if in_maya:
            if clear_selection:
                cmds.select(cl = True)
        
        try:
            status = self.run_script(script, hard_error=True)
        except:
            if hard_error:
                util.error('%s\n' % status)
                raise
            
            status = 'fail'
        
        if not status == 'Success':
            scripts_that_error.append(script)
            
            
            if hard_error:
                message = 'Script: %s in run_script_group.' % script
                #util.start_temp_log()
                temp_log = '\nError: %s' %  message
                util.record_temp_log(temp_log)
                
                #util.end_temp_log()
                raise Exception(message)
        
        #processing children
        children = self.get_code_children(script)
        
        manifest_dict = self.get_manifest_dict()

        progress_bar = None
        
        if in_maya:
            
            progress_bar = core.ProgressBar('Process Group', len(children))
            progress_bar.status('Processing Group: getting ready...')
        
        for child in children:
            
            if progress_bar:
                progress_bar.status('Processing: %s' % script)
                
                if progress_bar.break_signaled():
                    
                    message = 'The script group was cancelled before finishing.'
                    
                    #util.start_temp_log()
                    temp_log = '\nError: %s' % message
                    util.record_temp_log(temp_log)
                    
                    #util.end_temp_log()
                    raise Exception(message)
                    #break            
            
            if manifest_dict[child]:
                
                if in_maya:
                    if clear_selection:
                        cmds.select(cl = True)
                
                children = self.get_code_children(child)
                
                if children:
                    try:
                        status = self.run_script_group(child, hard_error=True)
                    except:
                        if hard_error:
                            util.error('%s\n' % status)
                            if progress_bar:              
                                progress_bar.end()
                            raise
                        
                        status = 'fail'
                
                if not children:
                    try:
                        status = self.run_script(child, hard_error=True)
                    except:
                        if hard_error:
                            util.error('%s\n' % status)
                            if progress_bar:              
                                progress_bar.end()
                            raise
                        
                        status = 'fail'
                        
                if status == 'fail':
                    scripts_that_error.append(child)
                    if hard_error:  
                        if progress_bar:              
                            progress_bar.end()
                        message = 'Script: %s in run_script_group.' % script
                        #util.start_temp_log()
                        temp_log = '\nError: %s' %  message
                        util.record_temp_log(temp_log)
                        #util.end_temp_log()
                        raise Exception(message)
                
            if progress_bar:
                progress_bar.inc()
            
            if not type(status) == list:
                status_list.append([child, status])
            else:
                status_list += status

        if progress_bar:
            progress_bar.end()  
        
        #util.start_temp_log()
        #util.record_temp_log(temp_log)
        #util.end_temp_log()
            
        return status_list            
            
    def run(self, start_new = False):
        """
        Run all the scripts in the manifest, respecting their on/off state.
        
        Returns:
            None
        """
        
        self.option_settings = None
        self._setup_options()
        
        prev_process = util.get_env('VETALA_CURRENT_PROCESS')
        
        util.set_env('VETALA_CURRENT_PROCESS', self.get_path())
        
        util.show('------------------------------------------------------------------------------------------------------')
        
        watch = util.StopWatch()
        watch.start(feedback = False)
                    
        name = self.get_name()
        
        message = '\n\n\n\aRunning %s Scripts\t\a\n\n' % name
        
        manage_node_editor_inst = None
        
        if in_maya:
        
            manage_node_editor_inst = core.ManageNodeEditors()
            
            if start_new:
                core.start_new_scene()
            
            manage_node_editor_inst.turn_off_add_new_nodes()
            
            if core.is_batch():
                message = '\n\n\nRunning %s Scripts\n\n' % name
        
        util.show(message)
        
        util.show('\n\nProcess path: %s' % self.get_path())
        util.show('Option path: %s' % self.get_option_file())
        util.show('Settings path: %s' % self.get_settings_file())
        util.show('Runtime values: %s\n\n' % self.runtime_values)
        
        scripts, states = self.get_manifest()
        
        scripts_that_error = []
        
        state_dict = {}
        
        progress_bar = None
        
        if in_maya:
            
            progress_bar = core.ProgressBar('Process', len(scripts))
            progress_bar.status('Processing: getting ready...')
            
        status_list = []
            
        for inc in range(0, len(scripts)):
            
            state = states[inc]
            script = scripts[inc]
            status = 'Skipped'
            
            check_script = script[:-3]
            
            state_dict[check_script] = state
            
            if progress_bar:
                progress_bar.status('Processing: %s' % script)
                
                if progress_bar.break_signaled():
                    break
            
            if state:
                
                parent_state = True
                
                for key in state_dict:
                    
                    if script.find(key) > -1:
                        parent_state = state_dict[key]
                        
                        if parent_state == False:
                            break
                        
                if not parent_state:
                    util.show('\tSkipping: %s\n\n' % script)
                    if progress_bar:
                        progress_bar.inc()
                    continue 
                
                
                self._update_options = False
                
                if in_maya:
                    cmds.select(cl = True)
                
                try:
                    status = self.run_script(script, hard_error=False)
                except:
                    status = 'fail'
                self._update_options = True
                
                if not status == 'Success':
                    scripts_that_error.append(script)
            
            if not states[inc]:
                util.show('\n------------------------------------------------')
                util.show('Skipping: %s\n\n' % script)
                
            if progress_bar:
                progress_bar.inc()
                
            status_list.append([script, status])
        
        minutes, seconds = watch.stop()
        
        if progress_bar:
            progress_bar.end()
        
        if scripts_that_error:
            
            util.show('\n\n\nThe following scripts errored during build:\n')
            for script in scripts_that_error:
                util.show('\n' + script)
        
        if minutes == None:
            util.show('\n\n\nProcess built in %s seconds.\n\n' % seconds)
        if minutes != None:
            util.show('\n\n\nProcess built in %s minutes, %s seconds.\n\n' % (minutes,seconds))
        
        util.show('\n\n')
        for status_entry in status_list:
            util.show('%s : %s' % (status_entry[1], status_entry[0]))
        util.show('\n\n') 
            
        util.set_env('VETALA_CURRENT_PROCESS', prev_process)
        
        if manage_node_editor_inst:
            manage_node_editor_inst.restore_add_new_nodes()
        
        return status_list
        
    def set_runtime_value(self, name, value):
        """
        This stores data to run between scripts.
        
        Args:
            name (str): The name of the script.
            value : Can be many different types including str, list, tuple, float, int, etc.
            
        Returns:
            None
        """
        util.show('!! Created Runtime Variable: %s, value: %s.' % (name, value))
        self.runtime_values[name] = value
        
    def get_runtime_value(self, name):
        """
        Get the value stored with set_runtime_value.
        
        Args:
            name (str): The name given to the runtime value in set_runtime_value.
        
        Returns:
            The value stored in set_runtime_value.
        """
        
        if self.runtime_values.has_key(name):
            
            value = self.runtime_values[name]
            
            util.show('Accessed - Runtime Variable: %s, value: %s' % (name, value))
        
            return value
        
    def get_runtime_value_keys(self):
        """
        Get the runtime value dictionary keys.
        Every time a value is set with set_runtime_value, and dictionary entry is made.
        
        Returns:
            list: keys in runtime value dictionary.
        """
        
        return self.runtime_values.keys()
    
    def set_runtime_dict(self, dict_value):
        self.runtime_values = dict_value
 
    def set_data_override(self, process_inst):
        self._data_override = process_inst
 
    def run_batch(self):
        process_path = self.get_path()
        
        util.set_env('VETALA_CURRENT_PROCESS', process_path)
        
        batch_path = util_file.get_process_batch_file()
        
        util_file.maya_batch_python_file(batch_path)
 
    def run_deadline(self):
        
        deadline_command = util_file.get_deadline_command_from_settings()
        mayapy = util_file.get_mayapy()
        if not mayapy:
            mayapy = 'python'
        batch_file = util_file.get_process_batch_file()
        
        if not deadline_command:
            return
        
        settings = util_file.get_vetala_settings_inst()
        pool = settings.get('deadline_pool')
        group = settings.get('deadline_group')
        department = settings.get('deadline_department')
        
        #vetala_path = util.get_env('VETALA_PATH')
        vetala_process = util.get_env('VETALA_CURRENT_PROCESS')
        
        command = []
        
        command.append(deadline_command)
        command.append('-SubmitCommandLineJob')
        command.append('-executable %s' % mayapy)
        command.append('-arguments %s' % batch_file)
        command.append('-chunksize 1')
        if pool:
            command.append('-pool ' + pool)
        if group:
            command.append('-group ' + group)
        command.append('-priority 100')
        command.append('-name "Vetala Process: %s"' % vetala_process)
        if department:
            command.append('-department ' + department)
        
        #command.append('-prop EnvironmentKeyValue0=VETALA_PATH=%s' % vetala_path)
        command.append('-prop IncludeEnvironment=true')
        #command.append('-prop PreJobScript=%s' % batch_file)
        
        command = string.join(command)
        subprocess.Popen(command, shell = True)
        
 
def get_default_directory():
    """
    Get a default directory to begin in.  
    The directory is different if running from inside Maya.
    
    Returns:
        str: Path to the default directory.
    """
    
    return util_file.get_default_directory()
    
    
    
    
def copy(source_file_or_folder, target_file_or_folder, description = ''):
    
    is_source_a_file = util_file.is_file(source_file_or_folder)
    
    copied_path = -1
    
    if is_source_a_file:
        copied_path = util_file.copy_file(source_file_or_folder, target_file_or_folder)
    
    if not is_source_a_file:
        
        if not util_file.exists(source_file_or_folder):
            util.warning('Nothing to copy: %s          Data was probably created but not saved to yet. ' % util_file.get_dirname(source_file_or_folder))
            return
        
        if util_file.exists(target_file_or_folder):
            util_file.delete_dir(target_file_or_folder)
        
        copied_path = util_file.copy_dir(source_file_or_folder, target_file_or_folder)
    
    if not copied_path:
        util.warning('Error copying %s   to    %s' % (source_file_or_folder, target_file_or_folder))
        return
    
    if copied_path > -1:
        
        util.show('Finished copying %s from %s to %s' % (description, source_file_or_folder, target_file_or_folder))
        version = util_file.VersionFile(copied_path)
        version.save('Copied from %s' % source_file_or_folder)
    
def copy_process(source_process, target_process = None ):
    """
    source process is an instance of a process that you want to copy 
    target_process is the instance of a process you want to copy to. 
    If no target_process is specified, the target process will be set to the directory where the source process is located automatically. 
    If there is already a process named the same in the target process, the name will be incremented. 
    If you need to give the copy a specific name, you should rename it after copy. 
    
    Args:
        source_process (str): The instance of a process.
        target_process (str): The instance of a process. If None give, duplicate the source_process.
    """
    
    parent = target_process.get_parent_process()
    
    if parent:
        if parent.get_path() == source_process.get_path():
            util.error('Cannot paste parent under child.  Causes recursion error')
            return
    
    
    sub_folders = source_process.get_sub_processes()
    
    source_name = source_process.get_name()
    source_name = source_name.split('/')[-1]
    
    if not target_process:
        target_process = Process()
        target_process.set_directory(source_process.directory)
    
    if not util_file.get_permission( target_process.get_path() ):
        util.warning('Could not get permsision in directory: %s' % target_process.get_path())
        return
    
    if source_process.process_name == target_process.process_name and source_process.directory == target_process.directory:
        
        parent_process = target_process.get_parent_process()
        
        if parent_process:
            target_process = parent_process
        
    
    path = target_process.get_path()
    
    new_name = get_unused_process_name(path, source_name)
    
    new_process = target_process.add_part(new_name)
    
    data_folders = source_process.get_data_folders()
    code_folders = source_process.get_code_folders()
    settings = source_process.get_setting_names()
    
    for data_folder in data_folders:
        copy_process_data(source_process, new_process, data_folder)
    
    manifest_found = False
    
    if code_folders:
        if 'manifest' in code_folders:
            code_folders.remove('manifest')
            manifest_found = True
        
        for code_folder in code_folders:
            copy_process_code(source_process, new_process, code_folder)
            
    for sub_folder in sub_folders:
        
        sub_process = new_process.get_sub_process(sub_folder)
        source_sub_process = source_process.get_sub_process(sub_folder)
        
        if not sub_process.is_process():
            copy_process(source_sub_process, new_process)
            
    if manifest_found:
        copy_process_code(source_process, new_process, 'manifest')
    
    for setting in settings:
        copy_process_setting(source_process, new_process, setting)
    
    return new_process

def copy_process_into(source_process, target_process, merge_sub_folders = False):
    """
    source_full_path = source_process.get_path()
    target_full_path = target_process.get_path()
    
    if source_full_path == target_full_path:
        
        return
    """
    
    if source_process.process_name == target_process.process_name and source_process.directory == target_process.directory:
        util.warning('Source and target process are the same.  Skipping merge.')
        return
    
    if not target_process:
        return
    
    if not target_process.is_process():
        return
    
    sub_folders = source_process.get_sub_processes()
        
    source_name = source_process.get_name()
    source_name = source_name.split('/')[-1]
    
    data_folders = source_process.get_data_folders()
    code_folders = source_process.get_code_folders()
    settings = source_process.get_setting_names()
    
    for data_folder in data_folders:
        copy_process_data(source_process, target_process, data_folder)
    
    manifest_found = False
    
    if 'manifest' in code_folders:
        code_folders.remove('manifest')
        manifest_found = True
    
    for code_folder in code_folders:
        copy_process_code(source_process, target_process, code_folder)
    
    if sub_folders and merge_sub_folders:
                
        for sub_folder in sub_folders:
        
            sub_target = target_process.get_sub_process(sub_folder)
            
            if sub_target:
            
                if not sub_target.is_process():
                    sub_target.create()
            
                sub_process = source_process.get_sub_process(sub_folder)
                                
                copy_process_into(sub_process, sub_target)
            
    if manifest_found:
        copy_process_code(source_process, target_process, 'manifest')
    
    for setting in settings:
        copy_process_setting(source_process, target_process, setting)
    
    
    
    
def copy_process_data(source_process, target_process, data_name, replace = False, sub_folder = None):
    """
    source_process and target_process need to be instances of the Process class. 
    The instances should be set to the directory and process name desired to work with. 
    data_name specifies the name of the data folder to copy. 
    If replace the existing data with the same name will be deleted and replaced by the copy. 
    
    Args:
        source_process (str): The instance of a process.
        target_process (str): The instance of a process.
        data_name (str): The name of the data to copy.
        replace (bool): Wether to replace the data in the target process or just version up.
        sub_folder (str): The name of the sub folder to copy
        
    """
    
    data_type = source_process.get_data_type(data_name)
    
    data_folder_path = None
    
    if not target_process.is_process():
        util.warning('Could not copy data, %s is not a vetala process.' % target_process)
        return
    
    if target_process.is_data_folder(data_name, sub_folder):
        
        data_folder_path = target_process.get_data_folder(data_name, sub_folder)
        
        if replace:
            other_data_type = target_process.get_data_type(data_name)
            
            if data_type != other_data_type:
                
                target_process.delete_data(data_name, sub_folder)
                copy_process_data(source_process, target_process, data_name, sub_folder)
                return
    
    if not target_process.is_data_folder(data_name, sub_folder):
        
        data_folder_path = target_process.create_data(data_name, data_type, sub_folder)
        
            
    path = source_process.get_data_path()
    data_folder = data.DataFolder(data_name, path)

    instance = data_folder.get_folder_data_instance()
    if not instance:
        util.warning('Could not get data folder instances for: %s' % data_name)
        return

    filepath = instance.get_file_direct(sub_folder)
    
    if not filepath:
        return
    
    name = util_file.get_basename(filepath)
    
    destination_directory = util_file.join_path(data_folder_path, name)
    
    if not util_file.is_dir(data_folder_path):
        util_file.create_dir(data_folder_path)

    if sub_folder:
        
        sub_path = target_process.create_sub_folder(data_name, sub_folder)
        
        destination_directory = util_file.join_path(sub_path, name)
        
    copy(filepath, destination_directory, data_name)
    
    if not sub_folder:
        sub_folders  = source_process.get_data_sub_folder_names(data_name)
        
        for sub_folder in sub_folders:
            copy_process_data(source_process, target_process, data_name, replace, sub_folder)  

            
def copy_process_code(source_process, target_process, code_name, replace = False):
    """
    source_process and target_process need to be instances of the Process class. 
    The instances should be set to the directory and process name desired to work with. 
    code_name specifies the name of the code folder to copy. 
    If replace the existing code with the same name will be deleted and replaced by the copy.
    
    Args:
        source_process (str): The instance of a process.
        target_process (str): The instance of a process.
        code_name (str): The name of the code to copy.
        replace (bool): Wether to replace the code in the target process or just version up.
    """
    
    if code_name == None:
        return
    
    data_type = source_process.get_code_type(code_name)
    
    if not data_type:
        util.warning('No data type found for %s' % code_name)
        return
    
    
    code_folder_path = None
    
    if target_process.is_code_folder(code_name):
        
        code_folder_path = target_process.get_code_folder(code_name)
        
        code_filepath =  target_process.get_code_file(code_name)
        
        if not code_filepath:
            util.show('Could not find code: %s' % code_name)
            return
        
        code_file = util_file.get_basename( code_filepath )
        
        code_folder_path = util_file.join_path(code_folder_path, code_file)
        
        other_data_type = target_process.get_code_type(code_name)
        
        if data_type != other_data_type:
            if replace:
                target_process.delete_code(code_name)
                
                copy_process_code(source_process, target_process, code_name)
                            
                return
    
    if not target_process.is_code_folder(code_name):
        code_folder_path = target_process.create_code(code_name, 'script.python')
    
    path = source_process.get_code_path()
    data_folder = data.DataFolder(code_name, path)
    instance = data_folder.get_folder_data_instance()
    if not instance:
        return
    
    filepath = instance.get_file()
    
    copied_path = None
    
    if filepath:
        
        destination_directory = code_folder_path
        
        path = target_process.get_code_path()
        data.DataFolder(code_name, path)
        data_folder.set_data_type(data_type)
        
        if util_file.is_file(filepath):
            copied_path = util_file.copy_file(filepath, destination_directory)
        if util_file.is_dir(filepath):
            copied_path = util_file.copy_dir(filepath, destination_directory)
          
        if copied_path:
            version = util_file.VersionFile(copied_path)
            version.save('Copied from %s' % filepath)
        if not copied_path:
            util.warning('Error copying %s    to    %s' % (filepath, destination_directory))
            return
    
        
    
    util.show('Finished copying code from %s    to    %s' % (filepath, destination_directory))
        
def copy_process_setting(source_process, target_process, setting_name):
    
    filepath = source_process.get_setting_file(setting_name)
    
    if not filepath:
        return
    
    destination_path = target_process.get_path()
    destination_filepath = target_process.get_setting_file(setting_name)
    
    if util_file.is_file(destination_filepath):
        
        name = util_file.get_basename(destination_filepath)
        directory = util_file.get_dirname(destination_filepath)
        
        util_file.delete_file(name, directory)
    
    util_file.copy_file(filepath, destination_path)
        
    source_path = source_process.get_path()
    
    util.show('Finished copying options from %s' % source_path)

def get_vetala_settings_inst():
    
    settings_path = util.get_env('VETALA_SETTINGS')
    
    if not settings_path:
        return

    settings_inst = util_file.SettingsFile()
    settings_inst.set_directory(settings_path)

    return settings_inst
        
def initialize_project_settings(project_directory, settings_inst = None):
    
    if not settings_inst:
        settings_inst = get_vetala_settings_inst()
        
    
    project_settings_dict = {}
    
    if not settings_inst.has_setting('project settings'):
        project_settings_dict = {}
        
        project_settings_dict[project_directory] = {}
        
        settings_inst.set('project settings', project_settings_dict)
    
    if not project_settings_dict:
        project_settings_dict = settings_inst.get('project settings')
        
    if not project_settings_dict.has_key(project_directory):
        project_settings_dict[project_directory] = {}
        settings_inst.set('project settings', project_settings_dict)
    
    return project_settings_dict
    
def get_project_setting(name, project_directory, settings_inst = None):
    
    if not settings_inst:
        settings_inst = get_vetala_settings_inst()
        
    
    if not settings_inst.has_setting('project settings'):
        return
    

    value = None

    project_settings_dict = settings_inst.get('project settings')
    if not project_settings_dict.has_key(project_directory):
        return
    
    if project_settings_dict[project_directory].has_key(name):
        value = project_settings_dict[project_directory][name]
    
    return value
    
def set_project_setting(name, value, project_directory,  settings_inst = None):
    
    if settings_inst:
        settings_inst.reload()
    
    if not settings_inst:
        settings_inst  = get_vetala_settings_inst()

    if not settings_inst.has_setting('project settings'):
        return

    
    project_settings_dict = settings_inst.get('project settings')
    
    if not project_settings_dict.has_key(project_directory):
        return
    
    project_settings_dict[project_directory][name] = value
    
    settings_inst.set('project settings', project_settings_dict)
    
def get_custom_backup_directory(process_directory):
        
    settings = util_file.get_vetala_settings_inst()
    backup = settings.get('backup_directory')
    
    backup_directory = None
    
    if util_file.is_dir(backup):
    
        project = settings.get('project_directory')    
        process_inst = Process()
        process_inst.set_directory(process_directory)
        
        backup_directory = process_directory    
        
        backup_settings = util_file.SettingsFile()
        backup_settings.set_directory(backup)
        project_name = util_file.fix_slashes(project)
        project_name = project_name.replace('/', '_')
        project_name = project_name.replace(':', '_')
        backup_settings.set(project_name, project)
        
        backup_directory = util_file.create_dir(project_name, backup)
        
        util.show('Backing up to custom directory: %s' % backup_directory)
        
        process_path =  process_inst.get_path()
        common_path = util_file.remove_common_path_simple(project, process_path)
        
        backup_directory = util_file.create_dir(util_file.join_path(backup_directory, common_path))
    
    if not backup_directory:
        return
    
    return backup_directory

def backup_process(process_path = None, comment = 'Backup', backup_directory = None):
    """
    Backs up the process at the path to the process/.backup folder
    If backup directory given, backs up there.
    
    """
    
    log.debug('Backup process at path: %s' % process_path)
    log.debug('Backup to custom path: %s' % backup_directory)
    
    process_inst = Process()
    process_inst.set_directory(process_path)
    
    if not backup_directory:
        backup_directory = get_custom_backup_directory(process_path)
    
    log.debug('Final backup path: %s' % backup_directory)
    
    process_inst.backup(comment, backup_directory)
    
def get_process_builtins(process):
    
    builtins = {'process': process}
    code_builtins = util.get_code_builtins()
    
    builtins.update(code_builtins)
    
    return builtins

def reset_process_builtins(process):
    builtins = get_process_builtins(process)
    
    util.reset_code_builtins(builtins)
    
def setup_process_builtins(process):
    builtins = get_process_builtins(process)
    
    util.setup_code_builtins(builtins)
    
