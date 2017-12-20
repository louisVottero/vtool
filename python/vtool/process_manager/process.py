# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

import os
import sys
import traceback
import string

from vtool import util
from vtool import util_file
from vtool import data
import __builtin__
import os
from multiprocessing import process

if util.is_in_maya():
    import maya.cmds as cmds
    from vtool.maya_lib import core



def find_processes(directory = None, return_also_non_process_list = False):
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
    
    for root, dirs, files in os.walk(directory):
        
        for folder in dirs:
            full_path = util_file.join_path(root, folder)
            
            if is_process(full_path):
                found.append(folder)
                continue
            else:
                if return_also_non_process_list:
                    if not folder.startswith('.'):
                        found_non.append(folder)
        break
    
    if not return_also_non_process_list:
        return found
    if return_also_non_process_list:
        return [found, found_non]

def is_process(directory):
    
    if not directory:
        return False
    
    code_path = util_file.join_path(directory, '.code')
    
    if not util_file.is_dir(code_path):
        return False
    
    #removing to increase speed
    #data_path = util_file.join_path(directory, '.data')
    
    #if not util_file.is_dir(data_path):
    #    return False
    
    return True

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
        self.option_values = {}
        self.runtime_values = {}
        self.option_settings = None
        self.settings = None
        
        
    def _setup_options(self):
        
        if not self.option_settings:
            options = util_file.SettingsFile()
            self.option_settings = options
            
        self.option_settings.set_directory(self.get_path(), 'options.txt')
        
    def _setup_settings(self):
        if not self.settings:
            settings = util_file.SettingsFile()
            self.settings = settings
            
        self.settings.set_directory(self.get_path(), 'settings.txt')
        
    def _set_name(self, new_name):
        
        new_name = new_name.strip()
        
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
        
    def _create_folder(self):
        
        path = util_file.create_dir(self.process_name, self.directory)
    
        if path and util_file.is_dir(path):

            self._handle_old_folders(path)
            
            util_file.create_dir(self.data_folder_name, path)
            code_folder = util_file.create_dir(self.code_folder_name, path)
            
            manifest_folder = util_file.join_path(code_folder, 'manifest')
            if not util_file.is_dir(manifest_folder):
                self.create_code('manifest', 'script.manifest')
        
        return path
            
    def _get_path(self, name):
        
        directory = util_file.join_path(self.get_path(), name)
                
        return directory
    
    def _prep_maya(self):
        
        
        
        if util.is_in_maya():
        
            cmds.select(cl = True)
            
            self._center_view()
    
    def _center_view(self):
        from vtool.maya_lib import core
        if not core.is_batch():
            try:
                cmds.select(cl = True)
                cmds.viewFit(an = True)
            except:
                util.show('Could not center view')
            
                
    def _reset_builtin(self, old_process, old_cmds, old_show, old_warning):
                
        try:
            builtins = __builtin__.dir()
            
            if old_process:
                __builtin__.process = old_process
            else:
                if 'process' in builtins:
                    del(__builtin__.process)
                    
            if old_cmds:
                __builtin__.cmds = old_cmds
            else:
                if 'cmds' in builtins:
                    del(__builtin__.cmds)
                    
            if old_show:
                __builtin__.show = old_show
            else:
                if 'show' in builtins:
                    del(__builtin__.show)
                    
            if old_warning:
                __builtin__.warning = old_warning
            else:
                if 'warning' in builtins:
                    del(__builtin__.warning)
                    
        except Exception:
            status = traceback.format_exc()
            util.error(status)
            

        
            
    def set_directory(self, directory):
        """
        Args:
            directory (str): Directory path to the process that should be created or where an existing process lives.
        """ 
        self.directory = directory
        
        
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
        
        if not util_file.is_dir(self.get_code_path()):
            
            path = self.get_path()
            self._handle_old_folders(path)
            if not util_file.is_dir(self.get_code_path()):
                return False
        
        return True
    
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
            If the process hasn't been created yet, this will return the directory set in set_directory.        """
        
        if self.process_name:
            return util_file.join_path(self.directory, self.process_name)
        
        if not self.process_name:
            return self.directory
    
    def get_name(self):
        """
        Returns:
            str: The name of the process.
        """
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
        
    def get_empty_process(self, path = None):
        
        process = Process()
        process.set_directory(path)
        return process
        
    #--- data
        
    def is_data_folder(self, name):
        """
        Args:
            name (str): The name of a data folder in the process.
            
        Returns:
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
        Returns:
            str: The path to the data folder for this process.
        """
        return self._get_path(self.data_folder_name)        
    
    def get_data_folder(self, name):
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
                return util_file.join_path(self.get_data_path(), name)
            
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
        
    def get_data_folders(self):
        """
        Returns:
            list: A list of data folder names found in the current process.
        """
        directory = self.get_data_path()
        
        return util_file.get_folders(directory)  
     
    def get_data_instance(self, name):
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
     
    def create_data(self, name, data_type):
        """
        Args:
            name (str): The name of a data folder in the process.
            data_type (str): A string with the name of the data type of the data in the process.
        
        Returns:
            str: The path to the new data folder.
        
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
        
        Args:
            name (str): The name of a data folder in the process.
        
        Returns:
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
            return instance.import_data()
        
        
    
    def open_data(self, name):
        path = self.get_data_path()
        
        data_folder_name = self.get_data_folder(name)
        
        if not util_file.is_dir(data_folder_name):
            util.show('%s data does not exist in %s' % (name, self.get_name()) )
            return
            
        data_folder = data.DataFolder(name, path)
        
        instance = data_folder.get_folder_data_instance()
        
        if hasattr(instance, 'open'):
            
            instance.open()
        if not hasattr(instance, 'open'):
            util.warning('Could not open data %s in process %s.  No open option.' % (name, self.process_name))
    
    def save_data(self, name, comment = ''):
        """
        Convenience function that tries to run the save function function found on the data_type instance for the specified data folder. Not all data type instances have a save function. 
        
        Args:
            name (str): The name of a data folder in the process.
        
        Returns:
            None
        """
        
        path = self.get_data_path()
        
        data_folder = data.DataFolder(name, path)
        
        instance = data_folder.get_folder_data_instance()
        
        if not comment:
            comment = 'Saved through process class with no comment.'
        
        if hasattr(instance, 'save'):
            saved = instance.save(comment)
            
            if saved:
                return True
        
        return False
            
    
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
    
    def delete_data(self, name):
        """
        Deletes the specified data folder from the file system.
        
        Args: 
            name (str): The name of a data folder in the process.
        
        Returns:
            None
        """
        data_folder = data.DataFolder(name, self.get_data_path())
        
        data_folder.delete()
    
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

    def get_code_type(self, name):
        """
        Args: 
            name (str): The name of a code folder in the process.
            
        Returns: 
            str: The code type name of the code folder with the supplied name if the code folder exists. Otherwise return None. Right now only python code type is used by the Process Manager.
        """
    
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
                    files.append(util_file.get_basename(file_path))

        return files
    
    def get_code_file(self, name, basename = False):
        """
        Args: 
            name (str): The name of a code folder in the process.
            basename (bool): Wether to return the full path or just the name of the file.
        
        Returns:
            str: The path to the code file with the specified name in the current process. 
        """
        
        path = util_file.join_path(self.get_code_path(), name)
        
        if not util_file.is_dir(path):
            return
        
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
        
    def delete_code(self, name):
        """
        Deletes the specified data folder from the file system.
        
        Args: 
            name (str): The name of a data folder in the process.
        
        Returns:
            None
        """
        util_file.delete_dir(name, self.get_code_path())
        
    #--- setting
    
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
    
    #--- settings
    
    def get_settings_file(self):
        
        self._setup_settings()
        return self.settings.get_file()
    
    def set_setting(self, name, value):
        self._setup_settings()
        
        self.settings.set(name, value)
            
    def get_setting(self, name):
        self._setup_settings()
        return self.settings.get(name)
        
    #--- options
    
    def has_options(self):
        self._setup_options()
        
        return self.option_settings.has_settings()
    
    def add_option(self, name, value, group = None):
        
        self._setup_options()
        
        if group:
            name = '%s.%s' % (group,name)
        if not group:
            name = '%s' % name
                
        self.option_settings.set(name, value)
        
    def set_option(self, name, value):
        self._setup_options()
        
        if self.option_settings.has_setting(name):
            self.option_settings.set(name, value)
        
    def get_unformatted_option(self, name, group):
        self._setup_options()
        
        if group:
            name = '%s.%s' % (group, name)
        if not group:
            name = '%s' % name
        
        value = self.option_settings.get(name)
        
        return value
        
    def get_option(self, name, group = None):
        
        self._setup_options()
        
        value = self.get_unformatted_option(name, group)
        
        if value == None:
            util.warning('Option not accessed - Option: %s, Group: %s. Perhaps the option does not exist in the group.'  % (name, group))
        
        new_value = None
        
        try:
            new_value = eval(value)
            
        except:
            pass
        
        if type(new_value) == list or type(new_value) == tuple or type(new_value) == dict:
            value = new_value
            
        if type(value) == str or type(value) == unicode:
            if value.find(',') > -1:
                value = value.split(',')
        
        util.show('Accessed - Option: %s, Group: %s, value: %s' % (name, group, value))
        
        return value
        
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
        
    #--- manifest
        
    def get_manifest_folder(self):
        """
        Returns:
            str: The path to the manifest folder.
        """
        code_path = self.get_code_path()
        
        path = util_file.join_path(code_path, 'manifest')
        
        if not util_file.is_dir(path):
            self.create_code('manifest', 'script.manifest')      
        
        return path
        
    def get_manifest_file(self):
        """
        Returns:
            str: The path to the manifest file.
        """
        manifest_path = self.get_manifest_folder()
        
        filename =  util_file.join_path(manifest_path, self.process_data_filename)
        
        if not util_file.is_file(filename):
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
        
    def get_manifest(self):
        """
        Returns:
            tuple: (list, list) Two lists, scripts and states. 
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
        
        script_count = 0
        
        if scripts:
            script_count = len(scripts)
        
        synced_scripts = []
        synced_states = []
        
        code_folders = self.get_code_folders()
        
        if not script_count and not code_folders:
            return
        
        if script_count:
            for inc in range(0,script_count):
                
                script_name = util_file.remove_extension(scripts[inc])
                
                filepath = self.get_code_file(script_name)
                
                if not util_file.is_file(filepath):
                    continue
                
                if scripts[inc] in synced_scripts:
                    continue
                
                synced_scripts.append(scripts[inc])
                synced_states.append(states[inc])
                
                remove_inc = None
                
                for inc in range(0, len(code_folders)):
                    
                    if code_folders[inc] == script_name:
                
                        remove_inc = inc
                        
                    #code_folders_py = code_folders[inc] + '.py'
                        
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
        
        Args:
            name (str): Name of a process found in the directory.
            
        Returns:
            None
            
        """
        self._set_name(name)
        self._setup_options()
        
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
    
    def run_script(self, script, hard_error = True, settings = None):
        """
        Run a script in the process.
        
        Args:
            script(str): Name of a code in the process.
            hard_error (bool): Wether to error hard when errors encountered, or to just pass an error string.

        Returns:
            str: The status from running the script. This includes error messages.
        """
        
        process_path = self.get_path()
        
        #util.start_temp_log(process_path)
        util.start_temp_log()
        builtins = dir(__builtin__)
        
        old_process = None
        old_cmds = None
        old_show = None
        old_warning = None
        
        if 'process' in builtins:
            old_process = __builtin__.process
        if 'cmds' in builtins:
            old_cmds = __builtin__.cmds
        if 'show' in builtins:
            old_show = __builtin__.show
        if 'warning' in builtins:
            old_warning = __builtin__.warning
        
        if util.is_in_maya():
            
            import maya.cmds as cmds
            cmds.refresh()
            
        status = None
        #read = None
        
        if util.is_in_maya():
            cmds.undoInfo(openChunk = True)
        
        init_passed = False
        
        try:
            
            if not script.find(':') > -1:
                
                script = util_file.remove_extension(script)
                
                script = self.get_code_file(script)
                
            if not util_file.is_file(script):
                self._reset_builtin(old_process, old_cmds, old_show, old_warning)
                return
            
            auto_focus = True
            
            if settings:
                if settings.has_key('auto_focus_scene'):
                    auto_focus = settings['auto_focus_scene']
            
            if auto_focus:
                self._prep_maya()
            
            name = util_file.get_basename(script)
            
            for external_code_path in self.external_code_paths:
                if util_file.is_dir(external_code_path):
                    if not external_code_path in sys.path:
                        sys.path.append(external_code_path)
            
            message = 'START\t%s\n\n' % name

            
            util.show('\n------------------------------------------------')
            util.show(message)
            
            
            util_file.delete_pyc(script)
            
            __builtin__.process = self
            __builtin__.show = util.show
            __builtin__.warning = util.warning
            
            if util.is_in_maya():
                
                import maya.cmds as cmds
                
                __builtin__.cmds = cmds
                
            module = util_file.source_python_module(script)
            
            if module and type(module) != str:
                
                module.process = self
                init_passed = True
            
            if not module or type(module) == str:
                status = module
                init_passed = False
            
        except Exception:
            
            util.warning('%s did not source' % script)
            
            status = traceback.format_exc()
            
            self._reset_builtin(old_process, old_cmds, old_show, old_warning)
            
            init_passed = False
            
            if hard_error:
                if util.is_in_maya():
                    cmds.undoInfo(closeChunk = True)
                    
                util.error('%s\n' % status)
                raise
            
        if init_passed:
            try:
                
                if hasattr(module, 'main'):
                    
                    module.main()
                    
                    status = 'Success'
        
                if not hasattr(module, 'main'):
                    
                    util_file.get_basename(script)
                    
                    util.warning('main() not found in %s.' % script)
                                    
                del module
                
            except Exception:
                
                status = traceback.format_exc()
                
                self._reset_builtin(old_process, old_cmds, old_show, old_warning)
                
                if hard_error:
                    if util.is_in_maya():
                        cmds.undoInfo(closeChunk = True)
                        
                    util.error('%s\n' % status)
                    raise
        
        if util.is_in_maya():
            cmds.undoInfo(closeChunk = True)        
        
        self._reset_builtin(old_process, old_cmds, old_show, old_warning)
         
        if not status == 'Success':
            util.show('%s\n' % status)
        
        message = '\nEND\t%s\n\n' % name
                
        util.show(message)
        util.end_temp_log()
        return status
               
    def run(self):
        """
        Run all the scripts in the manifest, respecting their on/off state.
        
        Returns:
            None
        """
        
        watch = util.StopWatch()
        watch.start(feedback = False)
        
        if util.is_in_maya():
            cmds.file(new = True, f = True)
            
        name = self.get_name()
        if not name:
            name = util_file.get_dirname(self.directory)
        
        
        message = '\n\n\aRunning %s Scripts\t\a\n\n' % name
        
        if util.is_in_maya():
            if core.is_batch():
                message = '\n\nRunning %s Scripts\n\n' % name
        
        util.show(message)
        
        scripts, states = self.get_manifest()
        
        scripts_that_error = []
        
        state_dict = {}
        
        for inc in range(0, len(scripts)):
            
            state = states[inc]
            script = scripts[inc]
            
            check_script = script[:-3]
            
            state_dict[check_script] = state
            
            
            
            if state:
                
                parent_state = True
                
                for key in state_dict:
                    
                    if script.find(key) > -1:
                        parent_state = state_dict[key]
                        
                        if parent_state == False:
                            break
                        
                if not parent_state:
                    util.show('\tSkipping: %s\n\n' % script)
                    continue 
                
                try:
                    status = self.run_script(script, hard_error=False)
                except:
                    status = 'fail'
                
                if not status == 'Success':
                    scripts_that_error.append(script)
            
            if not states[inc]:
                util.show('\n------------------------------------------------')
                util.show('Skipping: %s\n\n' % script)
        
        minutes, seconds = watch.stop()
        
        if scripts_that_error:
            
            
            
            util.show('\n\n\nThe following scripts errored during build:\n')
            for script in scripts_that_error:
                util.show('\n' + script)
                
            
        
        if minutes == None:
            util.show('\n\n\nProcess built in %s seconds.\n\n' % seconds)
        if minutes != None:
            util.show('\n\n\nProcess built in %s minutes, %s seconds.\n\n' % (minutes,seconds))
        
        
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
 
def get_default_directory():
    """
    Get a default directory to begin in.  
    The directory is different if running from inside Maya.
    
    Returns:
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
    
    Args:
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
    settings = source_process.get_setting_names()
    
    for data_folder in data_folders:
        copy_process_data(source_process, new_process, data_folder)
    
    manifest_found = False
    
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

def copy_process_into(source_process, target_process):
    
    sub_folders = source_process.get_sub_processes()
        
    source_name = source_process.get_name()
    source_name = source_name.split('/')[-1]
    
    if not target_process:
        return
    
    if source_process.process_name == target_process.process_name and source_process.directory == target_process.directory:
        return
    
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
        
    if sub_folders:
                
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
    
    
def copy_process_data(source_process, target_process, data_name, replace = False):
    """
    source_process and target_process need to be instances of the Process class. 
    The instances should be set to the directory and process name desired to work with. 
    data_name specifies the name of the data folder to copy. 
    If replace the existing data with the same name will be deleted and replaced by the copy. 
    
    Args:
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
            
            
            if util_file.is_dir( util_file.join_path(dirname, basename) ):
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
