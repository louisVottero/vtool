# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

import sys
import traceback
import string

from vtool import util
from vtool import util_file
from vtool import data

if util.is_in_maya():
    import maya.cmds as cmds

def find_processes(directory = None):
    """
    This will try to find the processes in the supplied directory. If no directory supplied, it will search the current working directory.
    
    Args
        directory(str): The directory to search for processes.
        
    Returns
        list: The procceses in the directory.
    """
    
    if not directory:
        directory = util_file.get_cwd()
    
    files = util_file.get_folders(directory)
    
    found = []
    
    if not files:
        return found
    
    for file_name in files:
        
        full_path = util_file.join_path(directory, file_name)
        
        if not util_file.is_dir(full_path):
            continue
        
        process = Process(file_name)
        process.set_directory(directory)
        
        if process.is_process():
            found.append(file_name)
            
    found.sort()
               
    return found

def get_unused_process_name(directory = None, name = None):
    """
    This will try to find a a process named process in the directory.
    
    It will increment the name to process1 and beyond until it finds a unique name. 
    If no directory supplied, it will search the current working directory.
    
    Args
        directory (str): Direcotry to search for processes.
        name (str): name to give the process.
        
    Returns
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
            new_name = (name + str(inc))
            inc += 1
            not_name = True
        
        if not new_name in processes:
            not_name = False
            
        if inc > 1000:
            break
        
    return new_name
    

class Process(object):
    """
    This class has functions to work on individual processes in the Process Manager.
    """
     
    description = 'process'
    data_folder_name = '.data'
    code_folder_name = '.code'
    process_data_filename = 'manifest.data'
    
    def __init__(self, name = None):
        
        self.directory = util_file.get_cwd()
        
        self.process_name = name
        self.parts = []
        self.external_code_paths = []
        self.runtime_values = {}
        
    def _set_name(self, new_name):
        
        self.process_name = new_name
            
    def _handle_old_folders(self, path):
        
        #here temporarily until old paths are out of use... 
        #could take a long time.
        
        old_data_name = self.data_folder_name.replace('.', '_')
        old_code_name = self.code_folder_name.replace('.', '_')
        
        old_data_path = util_file.join_path(path, old_data_name)
        old_code_path = util_file.join_path(path, old_code_name)
        
        if util_file.is_dir(old_data_path):
            util_file.rename(old_data_path, self.data_folder_name)
            
        if util_file.is_dir(old_code_path):
            util_file.rename(old_code_path, self.code_folder_name)
        """    
        code_folders = self.get_code_folders()
        data_folders = self.get_data_folders()
        
        if code_folders:
            for folder in code_folders:
                
                path = util_file.join_path(self.get_code_path(), folder)
                
                util_file.VersionFile(path)
                
                
        if data_folders:
            for folder in data_folders:
                
                path = util_file.join_path(self.get_data_path(), folder)
                
                util_file.VersionFile(path)
                
            #util_file.VersionFile()
        """     
    def _create_folder(self):
                
        if not util_file.is_dir(self.directory):
            util.show('%s was not created.' %  self.process_name)
            return
        
        path = util_file.create_dir(self.process_name, self.directory)
    
        if path and util_file.is_dir(path):

            self._handle_old_folders(path)
            
            util_file.create_dir(self.data_folder_name, path)
            util_file.create_dir(self.code_folder_name, path)
            
            code_files = self.get_code_files()
            
            found = False
            
            for code_file in code_files:
                basename = util_file.get_basename(code_file)
                if basename == self.process_data_filename:
                    found = True
                    break
            
            if not found:
                self.create_code('manifest', 'script.manifest')        
        
        return path
            
    def _get_path(self, name):
        
        directory = util_file.join_path(self.get_path(), name)
                
        return directory
    
    def _center_view(self):
        if util.is_in_maya():
            try:
                cmds.select(cl = True)
                cmds.viewFit(an = True)
            except:
                util.show('Could not center view')
                
            
    def set_directory(self, directory):
        """
        Args
            directory (str): Directory path to the process that should be created or where an existing process lives.
        """ 
        self.directory = directory
        
    def set_external_code_library(self, directory):
        """
        Args
            directory (str,list): Directory or list of directories where code can be sourced from. This makes it more convenient when writing scripts in a process. 
        """
        directory = util.convert_to_sequence(directory)
        
        self.external_code_paths = directory
        
    def is_process(self):
        """
        Return
            bool: Check to see if the initialized process is valid.
        """
        
        path = self.get_path()
        self._handle_old_folders(path)
        
        if not util_file.is_dir(self.get_code_path()):
            return False
        
        if not util_file.is_dir(self.get_data_path()):
            return False
        
        return True
        
    def get_path(self):
        """
        Return
            str: The full path to the process folder. 
            If the process hasn't been created yet, this will return the directory set in set_directory.        """
        
        if self.process_name:
            return util_file.join_path(self.directory, self.process_name)
        
        if not self.process_name:
            return self.directory
    
    def get_name(self):
        """
        Return
            str: The name of the process.
        """
        return self.process_name
    
    def get_basename(self):
        """
        Return
            str: The name of the process. If no name return basename of directory.
        """
        name = self.process_name
        
        if not name:
            name = self.directory
        
        
        return util_file.get_basename(name)
    
    def get_relative_process(self, relative_path):
        """
        Args
            relative_path (str): The path to a relative process. 
        Return
            (Process):An instance of a process at the relative path. 
            
            If a name with no backslash is supplied, this will return any matching process parented directly under the current process. 
            
            A relative path like, '../face' or '../../other_character' can be used. 
            
            Every '..' signifies a folder above the current process. 
        """
        path = self.get_path()
        
        if not path:
            return
        
        split_path = self.get_path().split('/')
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
        process_directory = string.join(new_path[:-1], '/')
        
        """
        test_path = util_file.join_path(process_directory, process_name)
        if not util_file.is_dir(test_path):
            util.warning('%s is not a valid path.' % test_path)
        """
        
        process = Process(process_name)
        process.set_directory(process_directory)
        
        return process
    
    def get_sub_processes(self):
        """
        Return
            list: The process names found directly under the current process.
        """
        process_path = self.get_path()
        
        found = find_processes(process_path)
                                
        return found
    
    def get_sub_process(self, part_name):
        """
        Args
            part_name (str): The name of a child process.
            
        Return
            A sub process if there is one that matches part_name.
        """
        part_process = Process(part_name)
        
        part_process.set_directory(self.get_path())  
        
        return part_process    
        
    def get_parent_process(self):
        
        process_path = self.get_path()
        
        dir_name = util_file.get_dirname(process_path)
        
        process = Process()
        process.set_directory(dir_name)
        
        if process.is_process():
        
            basename = util_file.get_basename(dir_name)
            path = util_file.get_dirname(dir_name)
            
            parent_process = Process(basename)
            parent_process.set_directory(path)
        
            return parent_process
        
    #--- data
        
    def is_data_folder(self, name):
        """
        Args
            name (str): The name of a data folder in the process.
            
        Return
            bool: True if the supplied name string matches the name of the a data folder in the current process.
        """
        
        path = self.get_data_folder(name)
        
        if not path:
            return False
        if util_file.is_dir(path):
            return True
        
        return False
        
    def get_data_path(self):
        """
        Return
            (str): The path to the data folder for this process.
        """
        return self._get_path(self.data_folder_name)        
    
    def get_data_folder(self, name):
        """
        Args
            name (str): The name of a data folder in the process.

        Return
            (str): The path to the data folder with the same name if it exists.
        """
        
        folders = self.get_data_folders()
        for folder in folders:
            if folder == name:
                return util_file.join_path(self.get_data_path(), name)
            
    def get_data_type(self, name):
        """
        Args
            name (str): The name of a data folder in the process.
            
        Return
            (str): The name of the data type of the data folder with the same name if it exists.
        """
        
        data_folder = data.DataFolder(name, self.get_data_path())
        data_type = data_folder.get_data_type()
        
        return data_type
        
    def get_data_folders(self):
        """
        Return
            (list): A list of data folder names found in the current process.
        """
        directory = self.get_data_path()
        
        return util_file.get_folders(directory)      
     
    def get_data_instance(self, name):
        """
        Args
            name (str): The name of a data folder in the process. 
            
        Return
            ( Process ): An instance of the data type class for data with the specified name in the current process. 
            
            This gives access to the data functions like import_data found in the data type class.
        """
        path = self.get_data_path()
        data_folder = data.DataFolder(name, path)
        
        return data_folder.get_folder_data_instance()
     
    def create_data(self, name, data_type):
        """
        Args
            name (str): The name of a data folder in the process.
            data_type (str): A string with the name of the data type of the data in the process.
        
        Return
            (str): The path to the new data folder.
        
        """
        
        path = self.get_data_path()
        
        test_path = util_file.join_path(path, name)
        test_path = util_file.inc_path_name(test_path)
        name = util_file.get_basename(test_path)
        
        data_folder = data.DataFolder(name, path)
        data_folder.set_data_type(data_type)
        
        return data_folder.folder_path
    
    def import_data(self, name):
        """
        Convenience function which will run the import_data function found on the data_type instance for the specified data folder.
        
        Args
            name (str): The name of a data folder in the process.
        
        Return
            None
        """
        path = self.get_data_path()
        
        data_folder_name = self.get_data_folder(name)
        
        if not util_file.is_dir(data_folder_name):
            util.show('%s data does not exist in %s' % (name, self.get_name()) )
            return
            
        data_folder = data.DataFolder(name, path)
        
        instance = data_folder.get_folder_data_instance()
        
        if hasattr(instance, 'import_data'):
            instance.import_data()
            
    def save_data(self, name):
        """
        Convenience function that tries to run the save function function found on the data_type instance for the specified data folder. Not all data type instances have a save function. 
        
        Args
            name (str): The name of a data folder in the process.
        
        Return
            None
        """
        
        path = self.get_data_path()
        
        data_folder = data.DataFolder(name, path)
        
        instance = data_folder.get_folder_data_instance()
        
        if hasattr(instance, 'save'):
            instance.save()
    
    def rename_data(self, old_name, new_name):
        """
        Renames the data folder specified with old_name to the new_name.
        
        Args
            old_name (str): The current name of the data.
            new_name (str): The new name for the data.
            
        Return
            (str): The new path to the data if rename was successful.
        """
        data_folder = data.DataFolder(old_name, self.get_data_path())
        
        return data_folder.rename(new_name)
    
    def delete_data(self, name):
        """
        Deletes the specified data folder from the file system.
        
        Args 
            name (str): The name of a data folder in the process.
        
        Return
            None
        """
        data_folder = data.DataFolder(name, self.get_data_path())
        
        data_folder.delete()
    
    #code ---
    
    def is_code_folder(self, name):
        """
        Args 
            name (str): The name of a code folder in the process.
            
        Return
            (bool): If the supplied name string matches the name of a code folder in the current process. 
            
        """
        path = self.get_code_folder(name)
        
        if not path:
            return False
        if util_file.is_dir(path):
            return True
        
        return False
    
    def get_code_path(self):
        """
        Return
            (str): The path to the code folder for this process.
        """
        return self._get_path(self.code_folder_name)
    
    def get_code_folder(self, name):
        """
        Args 
            name (str): The name of a code folder in the process.
            
        Return
            (str): A path to the code folder with the supplied name string if it exists.
        """
        
        folder = util_file.join_path(self.get_code_path(), name)
        
        if util_file.is_dir(folder):
            return folder

    def get_code_folders(self, code_name = None):
        """
        Return
            (list): A list of code folder names found in the current process. 
        """
        directory = self.get_code_path()
        
        if code_name:
            directory = util_file.join_path(directory, code_name)
        
        return util_file.get_folders_without_prefix_dot(directory, recursive = True)  

    def get_code_type(self, name):
        """
        Args 
            name (str): The name of a code folder in the process.
            
        Return 
            (str): The code type name of the code folder with the supplied name if the code folder exists. Otherwise return None. Right now only python code type is used by the Process Manager.
        """
    
        data_folder = data.DataFolder(name, self.get_code_path())
        data_type = data_folder.get_data_type()
        return data_type
    
    def get_code_files(self, basename = False):
        """
        Args 
            basename (bool): Wether to return the full path or just the name of the file.
        
        Return
            (list): The path to the code files found in the code folder for the current process. 
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
                    files.append(util_file.get_basename(file_path))

        return files
    
    def get_code_file(self, name, basename = False):
        """
        Args 
            name (str): The name of a code folder in the process.
            basename (bool): Wether to return the full path or just the name of the file.
        
        Return
            (str): The path to the code file with the specified name in the current process. 
        """
        
        path = util_file.join_path(self.get_code_path(), name)
        
        if not util_file.is_dir(path):
            return
        
        data_folder = data.DataFolder(name, self.get_code_path())
        
        data_instance = data_folder.get_folder_data_instance()
        
        data_folder = data.DataFolder(name, self.get_code_path())
        data_type = data_folder.get_data_type()
        
        if data_type == 'None':
            data_folder.set_data_type('script.python')
        
        return_value = None
        
        if data_instance:
            filepath = data_instance.get_file()
            
            if basename:
                return_value = util_file.get_basename(filepath)
            
            if not basename:
                return_value = filepath
        
        return return_value

        
    def create_code(self, name, data_type = 'script.python', inc_name = False, import_data = None):
        """
        Create a new code folder with the specified name and data_type. 
        
        Args
            name (str): The name of the code to create.
            data_type (str): Usually 'script.python'.
            inc_name (bool): Wether or not to increment the name.
            import_data (str): The name of data in the process. 
            Lines will be added to the code file to import the data.
        
        Return
            (str): Filename
        """
        path = self.get_code_path()
        
        if not path:
            return
        
        if inc_name:
            test_path = util_file.join_path(path, name)
            
            if util_file.is_dir(test_path):
                test_path = util_file.inc_path_name(test_path)
                name = util_file.get_basename(test_path)
        
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
        
        self.set_manifest(['%s.py' % name], append = True)
        
        return filename 
        
    def move_code(self, old_name, new_name):
        
        code_path = self.get_code_path()
        
        old_path = util_file.join_path(code_path, old_name)
        new_path = util_file.join_path(code_path, new_name)
        
        basename = util_file.get_basename(new_name)
        dirname = util_file.get_dirname(new_name)
        
        test_path = new_path
        
        while util_file.is_dir(test_path):
        
            last_number = util.get_last_number(basename)
            last_number += 1
            
            basename = util.replace_last_number(basename, last_number)
            
            new_name = basename
            
            if dirname:
                new_name = util_file.join_path(dirname, basename)
            
            test_path = util_file.join_path(code_path, new_name) 
                        
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
        
        Args
            old_name (str): The current name of the code.
            new_name (str): The new name for the code.
            
        Return
            (str): The new path to the code if rename was successful.
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
        
        instance = code_folder.get_folder_data_instance()
                
        file_name = instance.get_file()
        file_name = util_file.get_basename(file_name)
            
        name = new_name + '.py'
            
        return name
        
    def delete_code(self, name):
        """
        Deletes the specified data folder from the file system.
        
        Args 
            name (str): The name of a data folder in the process.
        
        Return
            None
        """
        util_file.delete_dir(name, self.get_code_path())
        
        
        
    #--- manifest
        
    def get_manifest_folder(self):
        """
        Return
            (str): The path to the manifest folder.
        """
        code_path = self.get_code_path()
        
        path = util_file.join_path(code_path, 'manifest')
        
        if not util_file.is_dir(path):
            self.create_code('manifest', 'script.manifest')      
        
        return path
        
    def get_manifest_file(self):
        """
        Return
            (str): The path to the manifest file.
        """
        manifest_path = self.get_manifest_folder()
        
        filename =  util_file.join_path(manifest_path, self.process_data_filename)
        
        if not util_file.is_file(filename):
            self.create_code('manifest', 'script.manifest')
        
        return filename
    
    def get_manifest_scripts(self, basename = True):
        """
        Args
            basename (bool): Wether to return the full path or just the name of the file. 
        Return
            The code files named in the manifest.  
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
    
    def set_manifest(self, scripts, states = [], append = False):
        """
        This will tell the manifest what scripts to list. Scripts is a list of python files that need to correspond with code data.
        
        Args
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
        
    def get_manifest(self):
        """
        Return
            (list, list): Two lists, scripts and states. 
            The scripts list contains the name of scripts in the manifest. 
            States contains the enabled/disabled state of the script. 
        """
        
        manifest_file = self.get_manifest_file()
        
        if not util_file.is_file(manifest_file):
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
        
    def sync_manifest(self):
        """
        Sync the manifest with whats on disk.
        """
        
        scripts, states = self.get_manifest()
        
        synced_scripts = []
        synced_states = []
        
        code_folders = self.get_code_folders()
        
        for inc in range(0,len(scripts)):
            
            script_name = util_file.remove_extension(scripts[inc])
            
            filepath = self.get_code_file(script_name)
            
            if not util_file.is_file(filepath):
                continue
            
            synced_scripts.append(scripts[inc])
            synced_states.append(states[inc])
            
            remove_inc = None
            
            for inc in range(0, len(code_folders)):
                
                if code_folders[inc] == script_name:
                    remove_inc = inc
                    
                if code_folders[inc] in synced_scripts:
                    
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
            
            if not remove_inc == None:
                code_folders.pop(remove_inc)
            
        for code_folder in code_folders:
            
            code_script = code_folder + '.py'
            
            synced_scripts.append(code_script)
            synced_states.append(False)
            
        self.set_manifest(synced_scripts, synced_states)
                
                
    #--- run
    
    def load(self, name):
        """
        Loads the named process into the instance.
        
        Args
            name (str): Name of a process found in the directory.
            
        Return
            None
            
        """
        self._set_name(name)
        
    def add_part(self, name):
        """
        Args
            name (str): Name for a new process.
            
        Return
            (Process): Instnace of the added part.
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
        
        Return
            None
        """
        util_file.delete_dir(self.process_name, self.directory)
    
    def rename(self, new_name):
        """
        Rename the process.
        
        Args
            new_name (str): New name for the process.
            
        Return
            (bool): Wether or not the process was renamed properly.
        """
        
        split_name = new_name.split('/')
        
        if util_file.rename( self.get_path(), split_name[-1]):
            
            self._set_name(new_name)
            
            return True
            
        return False
    
    def run_script(self, script, hard_error = True):
        """
        Run a script in the process.
        
        Args
            script(str): Name of a code in the process.
            hard_error (bool): Wether to error hard when errors encountered, or to just pass an error string.

        Return
            (str): The status from running the script. This includes error messages.
        """
        
        if util.is_in_maya():
            import maya.cmds as cmds
            cmds.refresh()
            
        status = None
        #read = None
            
        try:
            
            if not script.find(':') > -1:
                
                script = util_file.remove_extension(script)
                
                script = self.get_code_file(script)
                
            if not util_file.is_file(script):
                return
            
            self._center_view()
            name = util_file.get_basename(script)
            #path = util_file.get_parent_path(script)
            
            for external_code_path in self.external_code_paths:
                if util_file.is_dir(external_code_path):
                    if not external_code_path in sys.path:
                        sys.path.append(external_code_path)
            
            util.show('\n\t\a\t%s\n\n' % name)
            
            util_file.delete_pyc(script)
            
            module = util_file.source_python_module(script)     
            
            if type(module) == str:
                return module
            
            if not module:
                return
            
            module.process = self
            
            
        except Exception:
            status = traceback.format_exc()
            
            if hard_error:
                raise
            
            if not hard_error:
                #util.show(status)
                return status
            
        try:
            
            if util.is_in_maya():
                import vtool.maya_lib.util as maya_util
                
                # read
                #read = maya_util.ScriptEditorRead()
                #read.start()
                # read
                
                import maya.cmds as cmds
                module.cmds = cmds
                module.show = util.show
            
            if hasattr(module, 'main'):
                
                module.main()
                status = 'Success'
                
                # read
                #if read:
                #    value = maya_util.script_editor_value
                #    read.end()
                    
                #    for line in value:
                #        util.show('\t%s' % line)
                    
                #    if value:
                #        util.show('\n')
                #read
                
            if not hasattr(module, 'main'):
                
                util_file.get_basename(script)
                
                util.warning('main() not found in %s.' % script)
                                
            del module
                                
        except Exception:
            
            status = traceback.format_exc()

            #read
            #if read:
            #    value = maya_util.script_editor_value
            #    read.end()
                
            #    for line in value:
            #        util.show('\t' + line)
            #read
            
            
            
            if hard_error:
                raise
            
            if not hard_error:
                #util.show(status)
                return status
        
        return status
               
    def run(self):
        """
        Run all the scripts in the manifest, respecting their on/off state.
        
        Return
            None
        """
        
        if util.is_in_maya():
            cmds.file(new = True, f = True)
            
        util.show('\n\a\tRunning %s Scripts\t\a' % self.get_name())
 
        scripts = self.get_manifest_scripts(False)
        
        for script in scripts:
            self.run_script(script)
            
    def set_runtime_value(self, name, value):
        """
        This stores data to run between scripts.
        
        Args
            name (str): The name of the script.
            value : Can be many different types including str, list, tuple, float, int, etc.
            
        Return
            None
        """
        self.runtime_values[name] = value
        
    def get_runtime_value(self, name):
        """
        Get the value stored with set_runtime_value.
        
        Args
            name (str): The name given to the runtime value in set_runtime_value.
        
        Return
            The value stored in set_runtime_value.
        """
        if self.runtime_values.has_key(name):
            return self.runtime_values[name]
        
    def get_runtime_value_keys(self):
        """
        Get the runtime value dictionary keys.
        Every time a value is set with set_runtime_value, and dictionary entry is made.
        
        Return
            (list): keys in runtime value dictionary.
        """
        return self.runtime_values.keys()
    
    def set_runtime_dict(self, dict_value):
        self.runtime_values = dict_value
 
def get_default_directory():
    """
    Get a default directory to begin in.  
    The directory is different if running from inside Maya.
    
    Return
        str: Path to the default directory.
    """
    if util.is_in_maya():
        return util_file.join_path(util_file.get_user_dir(), 'process_manager')
    if not util.is_in_maya():
        return util_file.join_path(util_file.get_user_dir(), 'documents/process_manager')
    
def copy_process(source_process, target_process = None ):
    """
    source process is an instance of a process that you want to copy 
    target_process is the instance of a process you want to copy to. 
    If no target_process is specified, the target process will be set to the directory where the source process is located automatically. 
    If there is already a process named the same in the target process, the name will be incremented. 
    If you need to give the copy a specific name, you should rename it after copy. 
    
    Args
        source_process (str): The instance of a process.
        target_process (str): The instance of a process. If None give, duplicate the source_process.
    """
    
    sub_folders = source_process.get_sub_processes()
    
    source_name = source_process.get_name()
    source_name = source_name.split('/')[-1]
    
    if not target_process:
        target_process = Process()
        target_process.set_directory(source_process.directory)
    
    if source_process.process_name == target_process.process_name and source_process.directory == target_process.directory:
        
        parent_process = target_process.get_parent_process()
        
        if parent_process:
            target_process = parent_process
        
    
    path = target_process.get_path()
    
    new_name = get_unused_process_name(path, source_name)
    
    new_process = target_process.add_part(new_name)
    
    data_folders = source_process.get_data_folders()
    code_folders = source_process.get_code_folders()
    
    for data_folder in data_folders:
        copy_process_data(source_process, new_process, data_folder)
    
    if 'manifest' in code_folders:
        code_folders.remove('manifest')
        code_folders.append('manifest')
    
    for code_folder in code_folders:
        copy_process_code(source_process, new_process, code_folder)
        
    for sub_folder in sub_folders:
        
        sub_process = new_process.get_sub_process(sub_folder)
        source_sub_process = source_process.get_sub_process(sub_folder)
        
        if not sub_process.is_process():
            copy_process(source_sub_process, new_process)
    
    return new_process
    
def copy_process_data(source_process, target_process, data_name, replace = False):
    """
    source_process and target_process need to be instances of the Process class. 
    The instances should be set to the directory and process name desired to work with. 
    data_name specifies the name of the data folder to copy. 
    If replace the existing data with the same name will be deleted and replaced by the copy. 
    
    Args
        source_process (str): The instance of a process.
        target_process (str): The instance of a process.
        data_name (str): The name of the data to copy.
        replace (bool): Wether to replace the code in the target process or just version up.
    """
    
    data_type = source_process.get_data_type(data_name)
    
    data_folder_path = None
      
    if target_process.is_data_folder(data_name):
        
        data_folder_path = target_process.get_data_folder(data_name)
        
        other_data_type = target_process.get_data_type(data_name)
        
        if data_type != other_data_type:
            if replace:
                target_process.delete_data(data_name)
                
                copy_process_data(source_process, target_process, data_name)
                return
    
    if not target_process.is_data_folder(data_name):
        data_folder_path = target_process.create_data(data_name, data_type)
        
    path = source_process.get_data_path()
    data_folder = data.DataFolder(data_name, path)

    instance = data_folder.get_folder_data_instance()
    if not instance:
        return

    filepath = instance.get_file()
    
    if filepath:
        basename = util_file.get_basename(filepath)
    
        destination_directory = util_file.join_path(data_folder_path, basename)
    
        if util_file.is_file(filepath):
            copied_path = util_file.copy_file(filepath, destination_directory)
        if util_file.is_dir(filepath):
            
            basename = util_file.get_basename(destination_directory)
            dirname = util_file.get_dirname(destination_directory)
            
            util_file.delete_dir(basename, dirname)
            copied_path = util_file.copy_dir(filepath, destination_directory)
          
        version = util_file.VersionFile(copied_path)
        version.save('Copied from %s' % filepath)
        
    util.show('Finished copying data from %s' % filepath)          
            
def copy_process_code(source_process, target_process, code_name, replace = False):
    """
    source_process and target_process need to be instances of the Process class. 
    The instances should be set to the directory and process name desired to work with. 
    code_name specifies the name of the code folder to copy. 
    If replace the existing code with the same name will be deleted and replaced by the copy.
    
    Args
        source_process (str): The instance of a process.
        target_process (str): The instance of a process.
        code_name (str): The name of the code to copy.
        replace (bool): Wether to replace the code in the target process or just version up.
    """
    
    if code_name == None:
        return
    
    data_type = source_process.get_code_type(code_name)
    
    if not data_type:
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
    
    if filepath:
        destination_directory = code_folder_path
        
        if util_file.is_file(filepath):
            copied_path = util_file.copy_file(filepath, destination_directory)
        if util_file.is_dir(filepath):
            copied_path = util_file.copy_dir(filepath, destination_directory)
          
        version = util_file.VersionFile(copied_path)
        version.save('Copied from %s' % filepath)
        
    util.show('Finished copying code from %s' % filepath)