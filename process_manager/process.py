import sys
import traceback

import vtool.util
import vtool.util_file
import vtool.data

if vtool.util.is_in_maya():
    import maya.cmds as cmds

def find_processes(directory = None):
    
    if not directory:
        directory = vtool.util_file.get_cwd()
    
    files = vtool.util_file.get_folders(directory)
    
    found = []
    
    for file_name in files:
        
        full_path = vtool.util_file.join_path(directory, file_name)
        
        if not vtool.util_file.is_dir(full_path):
            continue
        
        process = Process()
        process.set_directory(full_path)
        
        if process.is_process():
            found.append(file_name)
            
    found.sort()
               
    return found

def get_unused_process_name(directory = None):
    
    if not directory:
        directory = vtool.util_file.get_cwd()
    
    processes = find_processes(directory)
    
    
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
        
        self.directory = vtool.util_file.get_cwd()
        
        self.process_name = name
        self.parts = []
        
    def _set_name(self, new_name):
        
        self.process_name = new_name
            
    def _create_folder(self):
                
        if not vtool.util_file.is_dir(self.directory):
            print '%s was not created.' %  self.process_name
            return
        
        path = vtool.util_file.create_dir(self.process_name, self.directory)
    
        if path and vtool.util_file.is_dir(path):
        
            vtool.util_file.create_dir(self.data_folder_name, path)
            vtool.util_file.create_dir(self.code_folder_name, path)
            
            code_files = self.get_code_files()
            
            found = False
            
            for code_file in code_files:
                basename = vtool.util_file.get_basename(code_file)
                if basename == 'manifest.data':
                    found = True
                    break
            
            if not found:
                self.create_code('manifest', 'script.manifest')        
        
        return path
            
    def _get_path(self, name):
        
        directory = vtool.util_file.join_path(self.get_path(), name)
                
        return directory
    
    def _center_view(self):
        if vtool.util.is_in_maya():
            try:
                cmds.select(cl = True)
                cmds.viewFit(an = True)
            except:
                print 'Could not center view.'
            
    def set_directory(self, directory):
        self.directory = directory
        
    def set_external_code_library(self, directory):
        self.external_code_path = directory
        
    def is_process(self):
        if not vtool.util_file.is_dir(self.get_code_path()):
            return False
        
        if not vtool.util_file.is_dir(self.get_data_path()):
            return False
        
        return True
        
    def get_path(self):
        
        if self.process_name:
            return vtool.util_file.join_path(self.directory, self.process_name)
        
        if not self.process_name:
            return self.directory
    
    def get_name(self):
        return self.process_name
    
    def get_relative_process(self, relative_path):
        
        process = Process(relative_path)
        process.set_directory(self.directory)
        
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
        if vtool.util_file.is_dir(path):
            return True
        
        return False
        
    def get_data_path(self):
        return self._get_path(self.data_folder_name)        
    
    def get_data_folder(self, name):
        folders = self.get_data_folders()
        for folder in folders:
            if folder == name:
                return vtool.util_file.join_path(self.get_data_path(), name)
            
    def get_data_type(self, name):
        data_folder = vtool.data.DataFolder(name, self.get_data_path())
        data_type = data_folder.get_data_type()
        
        return data_type
        
    def get_data_folders(self):
        
        directory = self.get_data_path()
        
        return vtool.util_file.get_folders(directory)      
     
    def create_data(self, name, data_type):
        path = self.get_data_path()
        
        test_path = vtool.util_file.join_path(path, name)
        test_path = vtool.util_file.inc_path_name(test_path)
        name = vtool.util_file.get_basename(test_path)
        
        data_folder = vtool.data.DataFolder(name, path)
        data_folder.set_data_type(data_type)
        
        return data_folder.folder_path
    
    def import_data(self, name):
        
        path = self.get_data_path()
        
        data_folder = vtool.data.DataFolder(name, path)
        
        instance = data_folder.get_folder_data_instance()
        
        if hasattr(instance, 'import_data'):
            instance.import_data()
            
    def save_data(self, name):
        path = self.get_data_path()
        
        data_folder = vtool.data.DataFolder(name, path)
        
        instance = data_folder.get_folder_data_instance()
        
        if hasattr(instance, 'save'):
            instance.save()
    
    def rename_data(self, old_name, new_name):
        data_folder = vtool.data.DataFolder(old_name, self.get_data_path())
        return data_folder.rename(new_name)
    
    def delete_data(self, name):
        data_folder = vtool.data.DataFolder(name, self.get_data_path())
        
        
    
    #code ---
    
    def get_code_path(self):
        return self._get_path(self.code_folder_name)
    
    def get_code_folder(self, name):
    
        folders = self.get_code_folders()
        for folder in folders:
            if folder == name:
                return vtool.util_file.join_path(self.get_code_path(), name)

    def get_code_folders(self):
        directory = self.get_code_path()
        
        return vtool.util_file.get_folders(directory)  

    def get_code_type(self, name):
    
        folder = self.get_code_path(name)
        
        file = vtool.util_file.join_path(folder, '.type')
        
        lines = vtool.util_file.get_file_lines(file)
        
        return lines[0]
    
    def get_code_files(self, basename = False):
        directory = self.get_code_path()
        
        folders = vtool.util_file.get_folders(directory)
        
        files = []
        
        for folder in folders:
            
            data_folder = vtool.data.DataFolder(folder, directory)
            
            data_instance = data_folder.get_folder_data_instance()
            
            if data_instance:

                file_path = data_instance.get_file()

                if not basename:
                    files.append(file_path)
                if basename:
                    files.append(vtool.util_file.get_basename(file_path))

        return files
        
    def create_code(self, name, data_type, inc_name = False):
        path = self.get_code_path()
        
        if inc_name:
            test_path = vtool.util_file.join_path(path, name)
            
            if vtool.util_file.is_dir(test_path):
                test_path = vtool.util_file.inc_path_name(test_path)
                name = vtool.util_file.get_basename(test_path)
        
        data_folder = vtool.data.DataFolder(name, path)
        data_folder.set_data_type(data_type)
        
        
        data_instance = data_folder.get_folder_data_instance()
        if not name == 'manifest':
            data_instance.set_lines(['process = None','','def main():','    return'])
        data_instance.create()
        
        filename = data_instance.get_file()
        
        
        return filename 
        
    def rename_code(self, old_name, new_name):
        code_folder = vtool.data.DataFolder(old_name, self.get_code_path())
        instance = code_folder.get_folder_data_instance()
        
        file_name = instance.rename(new_name)
        code_folder.rename(new_name)
        
        return file_name
        
    #--- manifest
        
    def get_manifest_folder(self):
        
        code_path = self.get_code_path()
        return vtool.util_file.join_path(code_path, 'manifest')
        
    def get_manifest_file(self):
        
        manifest_path = self.get_manifest_folder()
        
        return vtool.util_file.join_path(manifest_path, self.process_data_filename)
        

    def get_manifest_scripts(self, basename = True):
        
        manifest_file = self.get_manifest_file()
        
        if not manifest_file:
            return
        
        if not vtool.util_file.is_file(manifest_file):
            return
        
        read = vtool.util_file.ReadFile(manifest_file)
        lines = read.read()
        
        code_files = self.get_code_files()
        
        found = []
        
        for line in lines:
                            
            for code_file in code_files:
                name = vtool.util_file.get_basename(code_file)
                
                if line == name:
                    
                    if basename == True:
                        found.append(name)
                    
                    if basename == False:
                        found.append(code_file)
                        
                    break
        
        return found
    
    #--- run
    
    def load(self, name):
        self._set_name(name)
        
    def add_part(self, name):
        part_process = Process(name)
        
        path = vtool.util_file.join_path(self.directory, self.process_name)
        
        part_process.set_directory(path)
        part_process.create()
        
    def create(self):
        return self._create_folder()
        
    def delete(self):
        vtool.util_file.delete_dir(self.process_name, self.directory)
        
    
        
    def rename(self, new_name):
        
        split_name = new_name.split('/')
        
        if vtool.util_file.rename( self.get_path(), split_name[-1]):
            self._set_name(new_name)
            return True
            
        return False
    
    def run_script(self, script):
        self._center_view()
        name = vtool.util_file.get_basename(script)
        path = vtool.util_file.get_parent_path(script)
        
        if not self.external_code_path in sys.path:
            sys.path.append(self.external_code_path)
            
        module = vtool.util_file.load_python_module(name, path)
        
        print 'Running script: %s' % script
        
        if type(module) == str:
            print '%s script error' % name
            print module
            return
          
        if not module:
            return
        
        if hasattr(module, 'process'):
            module.process = self
          
        status = None  
        try:
            if hasattr(module, 'main'):
                module.main()
                status = 'Success'
        except Exception:
            status = traceback.format_exc()
            print status
            
        return status
               
    def run(self):
           
        if vtool.util.is_in_maya():
            cmds.file(new = True, f = True)
 
        scripts = self.get_manifest_scripts(False)
        
        for script in scripts:
            self.run_script(script)

                
            
def get_default_directory():
    if vtool.util.is_in_maya():
        return vtool.util_file.join_path(vtool.util_file.get_user_dir(), 'process_manager')
    if not vtool.util.is_in_maya():
        return vtool.util_file.join_path(vtool.util_file.get_user_dir(), 'documents/process_manager')
    
def copy_process_data(source_process, target_process, data_name, replace = False):
    
    data_type = source_process.get_data_type(data_name)
        
    if target_process.is_data_folder(data_name):
        other_data_type = target_process.get_data_type(data_name)
        
        if data_type != other_data_type:
            if replace:
                target_process.delete_data(data_name)
                
                copy_process_data(source_process, target_process, data_name)
                return
    
    if not target_process.is_data_folder(data_name):
        data_folder_path = target_process.create_data(data_name, data_type)
        
        path = source_process.get_data_path()
        data_folder = vtool.data.DataFolder(data_name, path)
    
        instance = data_folder.get_folder_data_instance()
    
        filepath = instance.get_file()
        
        basename = vtool.util_file.get_basename(filepath)
        
        destination_directory = vtool.util_file.join_path(data_folder_path, basename)
        
        if vtool.util_file.is_file(filepath):
            copied_path = vtool.util_file.copy_file(filepath, destination_directory)
        if vtool.util_file.is_dir(filepath):
            copied_path = vtool.util_file.copy_dir(filepath, destination_directory)
            
        print copied_path
            
        version = vtool.util_file.VersionFile(copied_path)
        version.save('Copied from %s' % filepath)
              
            
def copy_process_code(source_process, target_process, code_name):
    pass