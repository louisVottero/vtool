# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

import sys
import os
import shutil
import imp
import traceback
import getpass
import string
import re
import datetime
import subprocess
import tempfile
import threading
import stat


import util

class WatchDirectoryThread(threading.Thread):
    
    def __init__(self):
        super(WatchDirectoryThread, self).__init__()

    def run(self, directory): 
        import time
        path_to_watch = "."
        before = dict ([(f, None) for f in os.listdir (path_to_watch)])
        
        while 1:
            time.sleep (10)
            
            after = dict ([(f, None) for f in os.listdir (path_to_watch)])
            
            added = [f for f in after if not f in before]
            removed = [f for f in before if not f in after]
    
            if added: print "Added: ", ", ".join (added)
            if removed: print "Removed: ", ", ".join (removed)
            
            before = after

class FolderEditor(object):
    
    def __init__(self, directory):
        
        if not directory:
            self.directory_path = get_cwd()
        
        if directory:
            self.directory_path = directory
        
    def _create_folder(self, name):
        
        if not is_dir(self.directory_path):
            
            util.show('%s was not created.' % name)
             
            return
        
        path = create_dir(name, self.directory_path, True)        
        
        return path
        
    def list(self):
        return get_folders(self.directory_path)
        
    def create(self, name):
        return self._create_folder(name)
    
    def delete(self, name):
        path = join_path(self.directory_path, name)
        delete_dir(path)
        
    def rename(self, folder, name):
        path = join_path(self.directory_path, folder)
        
        return rename(path, name)
        
    def go_to(self, folder):
        path = join_path(self.directory_path, folder)
        
        self.directory_path = path
        
    def go_to_parent(self):
        pass

class FileManager(object):
    
    def __init__(self, filepath, skip_warning = False):
        
        self.filepath = filepath
        
        if not skip_warning:
            self.warning_if_invlid_path('path is invalid')
                
        self.open_file = None       

    def read_file(self):
        self.warning_if_invalid_file('file is invalid')
        
        self.open_file = open(self.filepath, 'r')
        
    def write_file(self):
        self.warning_if_invalid_file('file is invalid')
        self.open_file = open(self.filepath, 'w')
        
    def append_file(self):
        self.warning_if_invalid_file('file is invalid')
        self.open_file = open(self.filepath, 'a')       
    
    def close_file(self):
        if self.open_file:
            self.open_file.close()
        
    def get_open_file(self):
        return self.open_file()
        
    def warning_if_invalid_folder(self, warning_text):
        if not is_dir(self.filepath):
            raise NameError(warning_text)
    
    def warning_if_invalid_file(self, warning_text):
        if not is_file(self.filepath):
            raise NameError(warning_text)
        
    def warning_if_invlid_path(self, warning_text):
        dirname = get_dirname(self.filepath)
                
        if not is_dir(dirname):
            raise UserWarning(warning_text)

class ReadFile(FileManager):
    
    def __init__(self, filename):
        super(ReadFile, self).__init__(filename)        
        self.open_file = None
    
    def _get_lines(self):
        lines = self.open_file.read()
        return get_text_lines(lines)
        
        
    
    def read(self ):

        self.read_file()
        
        lines = self._get_lines()
        
        self.close_file()
        
        return lines

class WriteFile(FileManager):
    def __init__(self, filepath):
        super(WriteFile, self).__init__(filepath)
        
        self.filepath = filepath
        self.open_file = None
        
        self.append = False
        
    def write_file(self):
        if self.append:
            self.append_file()
            
        if not self.append:
            super(WriteFile, self).write_file()
        
    def set_append(self, bool_value):
        self.append = bool_value
        
    def write_line(self, line):
        self.write_file()
        self.open_file.write('%s\n' % line)
        self.close_file()
                
    def write(self, lines):
        
        self.write_file()
        
        for line in lines:
            self.open_file.write('%s\n' % line)
            
        self.close_file()

class VersionFile(object):
    def __init__(self, filepath):
        self.filepath = filepath
                
        self.file = get_basename(self.filepath)
        self.path = get_dirname(filepath)
        
        self.version_folder = None
        
    def _create_version_folder(self):

        self.version_folder = create_dir('version', self.path)
        
    def _create_comment_file(self):
        self.comment_file = create_file('comments.txt', self.version_folder)
        
    def _increment_version_file_name(self):
        
        path = join_path(self.version_folder, 'version.1')
        
        return inc_path_name(path)
        
    def _get_version_path(self, version_int):
        path = join_path(self._get_version_folder(), 'version.%s' % version_int)
        
        return path
        
    def _get_version_folder(self):
        path = join_path(self.filepath, 'version')
        
        return path
    
    def _get_comment_path(self):
        folder = self._get_version_folder()
        
        filepath = None
        
        if folder:
            filepath = join_path(folder, 'comments.txt')
            
        return filepath
            
    def save_comment(self, comment = None, version_file = None, ):
        
        version = version_file.split('.')
        if version:
            version = version[-1]
        
        user = getpass.getuser()
        
        if not comment:
            comment = '-'
        
        comment.replace('"', '\"')
        
        comment_file = WriteFile(self.comment_file)
        comment_file.set_append(True)
        comment_file.write(['version = %s; comment = "%s"; user = "%s"' % (version, comment, user)])
        comment_file.close_file()
            
    def save(self, comment = None):
        
        self._create_version_folder()
        
        self._create_comment_file()
        
        inc_file_name = self._increment_version_file_name()
        
        #copy_file(self.filepath, inc_file_name)
        
        if is_dir(self.filepath):
            copy_dir(self.filepath, inc_file_name)
        if is_file(self.filepath):
            copy_file(self.filepath, inc_file_name)
            
        self.save_comment(comment, inc_file_name)
        
        return inc_file_name
    
    def set_version_folder(self, folder_path):
        self.path = folder_path
        
    def get_version_path(self, version_int):
        return self._get_version_path(version_int)
        
    def get_version_comment(self, version_int):
        comment, user = self.get_version_data(version_int)
        return comment
                
    def get_version_data(self, version_int):
        filepath = self._get_comment_path()

        if not filepath:
            return None, None
        
        if is_file(filepath):
            read = ReadFile(filepath)
            lines = read.read()
            
            version = None
            comment = None
            user = None
            
            for line in lines:
                
                start_index = line.find('"')
                if start_index > -1:
                    end_index = line.find('";')
                    
                    subpart = line[start_index+1:end_index]
                    
                    subpart = subpart.replace('"', '\\"')
                    
                    line = line[:start_index+1] + subpart + line[end_index:]
                
                
                
                exec(line)
                
                if version == version_int:
                    
                    return comment, user
                
        return None, None
                
    def get_versions(self):
        
        version_folder = self._get_version_folder()
        
        files = get_files_and_folders(version_folder)
        
        if not files:
            return
        
        number_dict = {} 
        number_list = []
        pass_files = []
            
        for filepath in files: 
            
            if not filepath.startswith('version'):
                continue
            
            split_name = filepath.split('.')
            
            if not len(split_name) == 2:
                continue
            
            name = split_name[0]
            number = int(split_name[1])
            
            number_list.append(number)
            number_dict[number] = filepath
            
        
        number_list.sort()
        
        for number in number_list:
            pass_files.append(number_dict[number])
        
        return pass_files
    
    def get_latest_version(self):
        
        versions = self.get_versions()
        
        latest_version = versions[-1]
        
        return join_path(self.filepath, 'version/%s' % latest_version)
       
class SettingsFile(object):
    
    def __init__(self):
        self.directory = None
        self.filepath = None
        
        self.settings_dict = {}
        self.write = None 
    
    def _read(self):
        
        if not self.filepath:
            return
        
        lines = get_file_lines(self.filepath)
        
        if not lines:
            return
        
        self.settings_dict = {}
        
        for line in lines:
            if not line:
                continue
            
            split_line = line.split('=')
            
            name = split_line[0].strip()
            value = split_line[-1].strip()
            
            value = fix_slashes(value)
            
            value = eval(str(value))
            
            self.settings_dict[name] = value
            
    def _write(self):
                
        keys = self.settings_dict.keys()
        
        keys.sort()
        
        lines = []
        
        for key in keys:
            value = self.settings_dict[key]
            
            if type(value) == str or type(value) == unicode:
                value = "'%s'" % value
            
            line = '%s = %s' % (key, str(value))
            
            lines.append(line)
        
        write = WriteFile(self.filepath)
        
        write.write(lines)
    
    def set(self, name, value):
        
        self.settings_dict[name] = value
        self._write()
    
    def get(self, name): 
           
        if name in self.settings_dict:
            return self.settings_dict[name]
    
    def has_setting(self, name):
        
        if not self.settings_dict.has_key(name):
            return False
        
        return True
    
    def set_directory(self, directory, filename = 'settings.txt'):
        self.directory = directory
        
        self.filepath = create_file(filename, self.directory)
        
        self._read()
        
        return self.filepath

class FindUniquePath(util.FindUniqueString):
    
    def __init__(self, directory):
        
        if not directory:
            directory = get_cwd()
        
        self.parent_path = self._get_parent_path(directory)
        basename = get_basename(directory)
        
        super(FindUniquePath, self).__init__(basename)
        
    def _get_parent_path(self, directory):
        return get_parent_path(directory)
    
    def _get_scope_list(self):
        return get_files_and_folders(self.parent_path)
    
    def _search(self):
        name = super(FindUniquePath, self)._search()
        
        return join_path(self.parent_path, name)

#---- get

def get_basename(directory):
    return os.path.basename(directory)

def get_dirname(directory):
    try:
        return os.path.dirname(directory)
    except:
        return False

def get_user_dir():
    return fix_slashes( os.path.expanduser('~') )

def get_temp_dir():
    return fix_slashes( tempfile.gettempdir() ) 

def get_cwd():
    return os.getcwd()

def get_files(directory):
    files = os.listdir(directory)
    
    found = []
    
    for filepath in files:
        path = join_path(directory, filepath)
        
        if is_file(path):
            found.append(filepath)
    
    return found

def get_folders(directory):
    
    if not is_dir(directory):
        return
    
    files = os.listdir(directory)
    
    folders = []
    
    
    for filepath in files:
        path = join_path(directory, filepath)
        
        if is_dir(path):
            
            folders.append(filepath)
            
    return folders           

def get_files_and_folders(directory):
    
    if not is_dir(directory):
        return
        
    files = os.listdir(directory)
    
    return files

def get_folders_date_sorted(directory):
    
    mtime = lambda f: os.stat(os.path.join(directory, f)).st_mtime

    return list(sorted(os.listdir(directory), key = mtime))

def get_files_date_sorted(directory, extension = None):
        
    if not extension:
        files = get_files(directory)
        
    if extension:
        files = get_files_with_extension(extension, directory)
    
    mtime = lambda f: os.stat(os.path.join(directory, f)).st_mtime
    
    return list(sorted(files, key = mtime))
        

def get_files_with_extension(extension, directory, fullpath = False):
    found = []
    
    
    
    objects = os.listdir(directory)
    for directory in objects:
        filename, found_extension = os.path.splitext(directory)
        if found_extension == '.%s' % extension:
            if not fullpath:
                found.append(os.path.basename(directory))
            if fullpath:
                found.append(directory)
            
    return found

def get_filesize(filepath):
    size = os.path.getsize(filepath)
    size_format = round( size * 0.000001, 2 )

    return size_format

def get_last_modified_date(filepath):
    mtime = os.path.getmtime(filepath)
    
    date_value = datetime.datetime.fromtimestamp(mtime)
    year = date_value.year
    month = date_value.month
    day = date_value.day
    
    hour = str(date_value.hour)
    minute = str(date_value.minute)
    second = date_value.second
    
    second = str( int(second) )
    
    if len(hour) == 1:
        hour = '0'+hour
    if len(minute) == 1:
        minute = '0'+minute
    if len(second) == 1:
        second = second + '0'

    return '%s-%s-%s  %s:%s:%s' % (year,month,day,hour,minute,second)
    
def get_user():
    return getpass.getuser()
    
def is_dir(directory):
    if not directory:
        return False
    """
    if os.path.isdir(directory):
        return True
    
    return False
    """
    
    try:
        mode = os.stat(directory)[stat.ST_MODE]
        if stat.S_ISDIR(mode):
            return True
    except:
        return False
    
    
def is_file(filepath):
    
    if not filepath:
        return False
    """
    if os.path.isfile(filepath):
            return True
    
    return False
    """
    
    try:
        
        mode = os.stat(filepath)[stat.ST_MODE]
        if stat.S_ISREG(mode):
            return True
    except:
        return False
    
    
    

def is_file_in_dir(filename, directory):
    
    filepath = join_path(directory, filename)
    
    return os.path.isfile(filepath)

def is_same_date(file1, file2):
    date1 = os.path.getmtime(file1)
    date2 = os.path.getmtime(file2)
    
    
    value = date1 - date2
    
    if abs(value) < 0.01:
        return True
        
    return False

def inc_path_name(directory, padding = 0):
    
    unique_path = FindUniquePath(directory)
    unique_path.set_padding(padding) 
    
    return unique_path.get()

def get_file_lines(filepath): 
    read = ReadFile(filepath)
    
    return read.read()


def get_text_lines(text):
    
    text = text.replace('\r', '')
    lines = text.split('\n')
        
    return lines

def open_browser(filepath):
    if sys.platform == 'win32':
        os.startfile(filepath)
        
    else:
        opener ="open" if sys.platform == "darwin" else "xdg-open"
        subprocess.call([opener, filepath])  

#---- edit

def fix_slashes(directory):
    directory = directory.replace('\\','/')
    directory = directory.replace('//', '/')
    
    return directory

def set_windows_slashes(directory):
    directory = directory.replace('/', '\\')
    directory = directory.replace('//', '\\')
    
    return directory
    
def join_path(directory1, directory2):
    
    if not directory1 or not directory2:
        return
    
    directory1 = fix_slashes( directory1 )
    directory2 = fix_slashes( directory2 )
    
    path = '%s/%s' % (directory1, directory2)
    
    path = fix_slashes( path )
    
    return path

def get_parent_path(directory):
    
    splitpath = os.path.split(directory)
    
    split_length = len(splitpath)
    
    if split_length > 2:
        path = string.join(splitpath[0:-1], '/')
    
    if split_length <= 2:
        path = splitpath[0]
    
    return path
    

def rename(directory, name, make_unique = False):
    
    basename = get_basename(directory)
    
    if basename == name:
        return
    
    parentpath = get_parent_path(directory)
    
    renamepath = join_path(parentpath, name)
    
    if make_unique:
        renamepath = inc_path_name(renamepath)

    try:
        os.rename(directory, renamepath)
    except:
        
        util.show(traceback.format_exc())
        
        return False
    
    return renamepath

def comment(filepath, comment, comment_directory):
    
    comment_file = create_file('comments.txt', comment_directory)
    
    version = get_basename(filepath)
    
    user = getpass.getuser()
    
    if not comment:
        comment = '-'
    
    comment_file = WriteFile(comment_file)
    comment_file.set_append(True)
    comment_file.write(['filename = "%s"; comment = "%s"; user = "%s"' % (version, comment, user)])
    comment_file.close_file()
    
def get_comments(comment_directory, comment_filename = None):
    
    comment_file = join_path(comment_directory, 'comments.txt')
    
    if not comment_file:
        return
    
    comments = {}
    
    if is_file(comment_file):
        read = ReadFile(comment_file)
        lines = read.read()
        
        filename = None
        comment = None
        user = None
        
        for line in lines:  

            exec(line)                            
            
            if comment_filename:
                if comment_filename == filename:
                    return comment, user
            
            comments[ filename ] = [ comment, user ]

    return comments

def write_lines(filepath, lines, append = False):
    write_file = WriteFile(filepath)
    write_file.set_append(append)
    write_file.write(lines)
    

#---- create

def create_dir(name, directory, make_unique = False):
    if not name:
        full_path = directory
    
    if name:    
        full_path = join_path(directory, name)
         
        if make_unique:
            full_path = inc_path_name(full_path)   
    
    if is_dir(full_path):
        return full_path
       
    try:
        os.makedirs(full_path)
    except:
        return False
    
    return full_path           
    
def delete_dir(name, directory):
    
    util.clean_file_string(name)
    
    full_path = join_path(directory, name)
    
    if not is_dir(full_path):
        
        util.show('%s was not deleted.' % full_path)
        
        return full_path
    
    shutil.rmtree(full_path)  
    
    return full_path

def refresh_dir(directory):
    
    base_name = get_basename(directory)
    dir_name = get_dirname(directory)
    
    if is_dir(directory):
        files = get_files(directory)
        for filename in files:
            delete_file(filename, directory)
            
        delete_dir(base_name, dir_name)
        
    if not is_dir(directory):
        create_dir(base_name, dir_name)

def create_file(name, directory, make_unique = False):
    
    name = util.clean_file_string(name)
    
    full_path = join_path(directory, name)
        
    if is_file(full_path) and not make_unique:
        return full_path
    
    if make_unique:
        full_path = inc_path_name(full_path)
       
    
        
    try:
        open_file = open(full_path, 'w')
        open_file.close()
    except:
        return False
    
    return full_path
    
def delete_file(name, directory):
    full_path = join_path(directory, name)
    
    if not is_file(full_path):
        
        util.show('%s was not deleted.' % full_path)
        
        return full_path
        
    os.remove(full_path) 
    
    return full_path

def copy_dir(directory, directory_destination, ignore_patterns = []):
    
    if not is_dir(directory):
        return        
    
    if not ignore_patterns:
        shutil.copytree(directory, 
                        directory_destination)        
    
    if ignore_patterns:
        shutil.copytree(directory, 
                        directory_destination, 
                        ignore = shutil.ignore_patterns(ignore_patterns) )
    
    return directory_destination
    
def copy_file(filepath, filepath_destination):
    
    shutil.copy2(filepath, filepath_destination)
    
    return filepath_destination

    
#---- python

def import_python_module(module_name, directory):
    if not is_dir(directory):
        return
        
    full_path = join_path(directory, module_name)
    
    module = None
    
    if is_file(full_path):
        if not directory in sys.path:
            sys.path.append(directory)
            
        split_name = module_name.split('.')
        script_name = split_name[0]
                        
        exec('import %s' % script_name)
        exec('reload(%s)' % script_name)
         
        
        module = eval(script_name)
        
        sys.path.remove(directory)
        
    return module

def source_python_module(code_directory):
    try:
        try:
            
            fin = open(code_directory, 'rb')
            import md5
            return  imp.load_source(md5.new(code_directory).hexdigest(), code_directory, fin)
        
        finally:            
            try: fin.close()
            except: pass
            
    except ImportError:
        traceback.print_exc(file = sys.stderr)
        return None
    
    except:
        traceback.print_exc(file = sys.stderr)
        return None
      

def load_python_module(module_name, directory):
        
    if is_dir(directory):
        
        full_path = join_path(directory, module_name)
                
        if is_file(full_path):
            
            split_name = module_name.split('.')
            
            filepath, pathname, description = imp.find_module(split_name[0], 
                                                        [directory])
            
            try:
                module = imp.load_module(module_name, 
                                         filepath, 
                                         pathname, 
                                         description)
                
            except:
                return traceback.format_exc()
            
            finally:
                if filepath:
                    filepath.close()
            
            return module
        
def launch_maya(version, script = None):
    if sys.platform == 'win32':
        path = 'C:\\Program Files\\Autodesk\\Maya%s\\bin\\maya.exe' % version
        
        if script:
            os.system("start \"maya\" \"%s\" -script \"%s\"" % (path, script))
        if not script:
            os.system("start \"maya\" \"%s\"" % path)
            
def launch_nuke(version, command = None):
    if sys.platform == 'win32':
        split_version = version.split('v')
        
        nuke_exe_version = split_version[0]
        
        path = 'C:\\Program Files\\Nuke%s\\Nuke%s.exe' % (version, nuke_exe_version)
        
        if not is_file(path):
            new_version = split_version[0] + 'v4' 
            path = 'C:\\Program Files\\Nuke%s\\Nuke%s.exe' % (new_version, nuke_exe_version) 
        
        
        if command:
            os.system('start "nuke" "%s" "%s"' % (path, command))
        if not command:
            os.system('start "nuke" "%s"' % path)
    
def run_ffmpeg():
    
    path = 'X:\\Tools\\ffmpeg\\bin\\ffmpeg.exe'
    
    os.system('start \"ffmpeg\" \"%s\"' % path)
    
    