# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

import sys
import traceback

from vtool import util
from vtool import util_file
from vtool import data

if util.is_in_maya():
    import maya.cmds as cmds

def find_processes(directory = None):
    
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
    
    description = 'process'
    data_folder_name = '_data'
    code_folder_name = '_code'
    process_data_filename = 'manifest.data'
    
    def __init__(self, name = None):
        
        self.directory = util_file.get_cwd()
        
        self.process_name = name
        self.parts = []
        self.external_code_paths = []
        
    def _set_name(self, new_name):
        
        self.process_name = new_name
            
    def _create_folder(self):
                
        if not util_file.is_dir(self.directory):
            util.show('%s was not created.' %  self.process_name)
            return
        
        path = util_file.create_dir(self.process_name, self.directory)
    
        if path and util_file.is_dir(path):
        
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
        
        self.directory = directory
        
    def set_external_code_library(self, directory):
        directory = util.convert_to_sequence(directory)
        
        self.external_code_paths = directory
        
    def is_process(self):
        if not util_file.is_dir(self.get_code_path()):
            return False
        
        if not util_file.is_dir(self.get_data_path()):
            return False
        
        return True
        
    def get_path(self):
        
        if self.process_name:
            return util_file.join_path(self.directory, self.process_name)
        
        if not self.process_name:
            return self.directory
    
    def get_name(self):
        return self.process_name
    
    def get_basename(self):
        
        name = self.process_name
        
        if not name:
            name = self.directory
        
        
        return util_file.get_basename(name)
    
    def get_relative_process(self, relative_path):
                    
        path = self.get_path()
        
        if not path:
            return
        
        split_path = self.get_path().split('/')
        split_relative_path = relative_path.split('/')
        
        if not len(split_relative_path):
            return
        
        position = len(split_relative_path)
        
        import string
        if position > 1:
            start_path = string.join(split_path[:-position], '/')
        if position == 1:
            start_path = string.join(split_path,'/')
        
        split_path_count = len(split_path[:-position])
        
        end_path = [] 
        
        for inc in range(0, position):
            if split_relative_path[inc] == '..':
                
                folder = split_path[split_path_count + inc]
                
                end_path.append(folder)
                continue
            
            end_path.append(split_relative_path[inc])

        if end_path:
            end_path = string.join(end_path, '/')
        if not end_path:
            end_path = relative_path
        
        process = Process(end_path)
        process.set_directory(start_path)
        
        return process
    
    def get_sub_processes(self):
        
        process_path = self.get_path()
        
        found = find_processes(process_path)
                                
        return found
    
    def get_sub_process(self, part_name):
        
        part_process = Process(part_name)
        
        part_process.set_directory(self.get_path())  
        
        
        
        return part_process    
        
    #--- data
        
    def is_data_folder(self, name):
        
        path = self.get_data_folder(name)
        
        if not path:
            return False
        if util_file.is_dir(path):
            return True
        
        return False
        
    def get_data_path(self):
        return self._get_path(self.data_folder_name)        
    
    def get_data_folder(self, name):
        folders = self.get_data_folders()
        for folder in folders:
            if folder == name:
                return util_file.join_path(self.get_data_path(), name)
            
    def get_data_type(self, name):
        data_folder = data.DataFolder(name, self.get_data_path())
        data_type = data_folder.get_data_type()
        
        return data_type
        
    def get_data_folders(self):
        
        directory = self.get_data_path()
        
        return util_file.get_folders(directory)      
     
    def get_data_instance(self, name):
        path = self.get_data_path()
        data_folder = data.DataFolder(name, path)
        
        return data_folder.get_folder_data_instance()
     
    def create_data(self, name, data_type):
        path = self.get_data_path()
        
        test_path = util_file.join_path(path, name)
        test_path = util_file.inc_path_name(test_path)
        name = util_file.get_basename(test_path)
        
        data_folder = data.DataFolder(name, path)
        data_folder.set_data_type(data_type)
        
        return data_folder.folder_path
    
    def import_data(self, name):
        
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
        path = self.get_data_path()
        
        data_folder = data.DataFolder(name, path)
        
        instance = data_folder.get_folder_data_instance()
        
        if hasattr(instance, 'save'):
            instance.save()
    
    def rename_data(self, old_name, new_name):
                
        data_folder = data.DataFolder(old_name, self.get_data_path())
        
        return data_folder.rename(new_name)
    
    def delete_data(self, name):
        data_folder = data.DataFolder(name, self.get_data_path())
        
        data_folder.delete()
        
    
    #code ---
    
    def is_code_folder(self, name):
        
        path = self.get_code_folder(name)
        
        if not path:
            return False
        if util_file.is_dir(path):
            return True
        
        return False
    
    def get_code_path(self):
        return self._get_path(self.code_folder_name)
    
    def get_code_folder(self, name):
    
        folders = self.get_code_folders()
        for folder in folders:
            if folder == name:
                return util_file.join_path(self.get_code_path(), name)

    def get_code_folders(self):
        directory = self.get_code_path()
        
        return util_file.get_folders(directory)  

    def get_code_type(self, name):
    
        data_folder = data.DataFolder(name, self.get_code_path())
        data_type = data_folder.get_data_type()
        return data_type
    
    def get_code_files(self, basename = False):
        directory = self.get_code_path()
        
        folders = util_file.get_folders(directory)
        
        files = []
        
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
        
        
        
        
        data_folder = data.DataFolder(name, self.get_code_path())
        
        
        data_instance = data_folder.get_folder_data_instance()
        
        return_value = None
        
        if data_instance:
            filepath = data_instance.get_file()
            
            if basename:
                return_value = util_file.get_basename(filepath)
            
            if not basename:
                return_value = filepath
        
            
        return return_value
        
        
        
    def create_code(self, name, data_type = 'script.python', inc_name = False, import_data = None):
        
        path = self.get_code_path()
        
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
        
    def rename_code(self, old_name, new_name):
        
        new_name = util.clean_string(new_name)
        
        code_folder = data.DataFolder(old_name, self.get_code_path())
        code_folder.rename(new_name)
        
        instance = code_folder.get_folder_data_instance()
                
        file_name = instance.get_file()
        file_name = util_file.get_basename(file_name)
                
        return file_name
        
    def delete_code(self, name):
        
        util_file.delete_dir(name, self.get_code_path())
        
        
    #--- manifest
        
    def get_manifest_folder(self):
        
        code_path = self.get_code_path()
        
        path = util_file.join_path(code_path, 'manifest')
        
        if not util_file.is_dir(path):
            self.create_code('manifest', 'script.manifest')      
        
        return path
        
    def get_manifest_file(self):
        
        manifest_path = self.get_manifest_folder()
        
        filename =  util_file.join_path(manifest_path, self.process_data_filename)
        
        if not util_file.is_file(filename):
            self.create_code('manifest', 'script.manifest')
        
        return filename
    
    def get_manifest_scripts(self, basename = True):
        
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
                
                for filename in files:
                    
                    if filename.endswith(script):
                        
                        found.append(filename)
                        break
            
            return found
    
    def set_manifest(self, scripts, states = [], append = False):
        
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
        
        manifest_file = self.get_manifest_file()
        
        lines = util_file.get_file_lines(manifest_file)
        
        if not lines:
            return
        
        scripts = []
        states = []
        
        for line in lines:
            
            if not line:
                continue
            
            split_line = line.split()
            if len(split_line):
                scripts.append(split_line[0])
                
            if len(split_line) == 2:
                states.append(eval(split_line[1]))
                
            if len(split_line) == 1:
                states.append(False)
                           
        return scripts, states
        
    def sync_manifest(self):
                
        scripts, states = self.get_manifest()
        
        synced_scripts = []
        synced_states = []
                
        for inc in range(0, len(scripts)):
            
            current_script = scripts[inc]
            current_state = states[inc]
            
            name = current_script.split('.')
            
            if len(name) == 2:
                name = name[0]
            
            
            code_file = self.get_code_file(name)
            
            if not util_file.is_file( code_file ):
                continue
                        
            synced_scripts.append(current_script)
            synced_states.append(current_state)
            
        code_folders = self.get_code_folders()
        
        for code_folder in code_folders:
            
            if code_folder == 'manifest':
                continue
            
            code_file_basename = code_folder + '.py'
            
            if not code_file_basename in synced_scripts:
                synced_scripts.append(code_file_basename)
                synced_states.append(False)
            
        self.set_manifest(synced_scripts, synced_states)
                
    #--- run
    
    def load(self, name):
        self._set_name(name)
        
    def add_part(self, name):
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
        return self._create_folder()
        
    def delete(self):
        util_file.delete_dir(self.process_name, self.directory)
    
    def rename(self, new_name):
        
        split_name = new_name.split('/')
        
        if util_file.rename( self.get_path(), split_name[-1]):
            
            self._set_name(new_name)
            
            return True
            
        return False
    
    
    def run_script(self, script):
        if util.is_in_maya():
            import maya.cmds as cmds
            cmds.refresh()
            
        status = None
        read = None
            
        try:
                 
            self._center_view()
            name = util_file.get_basename(script)
            path = util_file.get_parent_path(script)
            
            for external_code_path in self.external_code_paths:
                if util_file.is_dir(external_code_path):
                    if not external_code_path in sys.path:
                        sys.path.append(external_code_path)
            
            util.show('\n\t\a\t%s\n\n' % name)
            
            module = util_file.source_python_module(script)     
            
            if type(module) == str:
                return module
            
            if not module:
                return
            
            module.process = self
            
            
        except Exception:
            status = traceback.format_exc()
            
            util.show(status)
            
            return status
              
        try:
            if hasattr(module, 'main'):
                                
                
                
                if util.is_in_maya():
                    import vtool.maya_lib.util as maya_util
                    
                    # read
                    read = maya_util.ScriptEditorRead()
                    read.start()
                    # read
                    
                    import maya.cmds as cmds
                    module.cmds = cmds
                    module.show = util.show
                        
                
                module.main()
                status = 'Success'
                
                # read
                if read:
                    value = maya_util.script_editor_value
                    read.end()
                    
                    for line in value:
                        util.show('\t%s' % line)
                    
                    if value:
                        util.show('\n')
                #read
                                
        except Exception:
            
            status = traceback.format_exc()
            
            #read
            if read:
                value = maya_util.script_editor_value
                read.end()
                
                for line in value:
                    util.show('\t' + line)
            #read
            util.show(status)
            return status
        
        return status
               
    def run(self):
           
        if util.is_in_maya():
            cmds.file(new = True, f = True)
            
        util.show('\n\a\tRunning %s Scripts\t\a' % self.get_name())
 
        scripts = self.get_manifest_scripts(False)
        
        for script in scripts:
            self.run_script(script)
 
def get_default_directory():
    if util.is_in_maya():
        return util_file.join_path(util_file.get_user_dir(), 'process_manager')
    if not util.is_in_maya():
        return util_file.join_path(util_file.get_user_dir(), 'documents/process_manager')
    
def copy_process(source_process, target_process = None, ):
    
    source_name = source_process.get_name()
    source_name = source_name.split('/')[-1]
    
    if not target_process:
        target_process = Process()
        target_process.set_directory(source_process.directory)
    
    path = target_process.get_path()
    
    new_name = get_unused_process_name(path, source_name)
    
    new_process = target_process.add_part(new_name)
    
    data_folders = source_process.get_data_folders()
    code_folders = source_process.get_code_folders()
    
    for data_folder in data_folders:
        copy_process_data(source_process, new_process, data_folder)
    
    code_folders.remove('manifest')
    code_folders.append('manifest')
    
    for code_folder in code_folders:
        copy_process_code(source_process, new_process, code_folder)
    
    sub_folders = source_process.get_sub_processes()
    
    for sub_folder in sub_folders:
        
        sub_process = target_process.get_sub_process(sub_folder)
        source_sub_process = source_process.get_sub_process(sub_folder)
        
        if not sub_process.is_process():
            copy_process(source_sub_process, new_process)
    
    return new_process
    
def copy_process_data(source_process, target_process, data_name, replace = False):
        
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