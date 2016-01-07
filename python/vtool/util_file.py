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
import ast

import util


class WatchDirectoryThread(threading.Thread):
    """
    Not developed fully.
    """
    
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

class FileManager(object):
    """
    Convenience to deal with file write/read.
    
    Args
        filepath (str): Path to the file to work on.
        skip_warning (bool): Wether to print warnings out or not.
    """
    def __init__(self, filepath, skip_warning = False):
        
        self.filepath = filepath
        
        if not skip_warning:
            self.warning_if_invlid_path('path is invalid')
                
        self.open_file = None       

    def read_file(self):
        """
        Start read the file.
        """
        self.warning_if_invalid_file('file is invalid')
        
        self.open_file = open(self.filepath, 'r')
        
    def write_file(self):
        """
        Start write the file.
        """
        self.warning_if_invalid_file('file is invalid')
        self.open_file = open(self.filepath, 'w')
        
    def append_file(self):
        """
        Start append file.
        """
        self.warning_if_invalid_file('file is invalid')
        self.open_file = open(self.filepath, 'a')       
    
    def close_file(self):
        """
        Close file.
        """
        if self.open_file:
            self.open_file.close()
        
    def get_open_file(self):
        """
        Get open file object.
        """
        return self.open_file()
        
    def warning_if_invalid_folder(self, warning_text):
        """
        Check if folder is invalid and raise and error.
        """
        if not is_dir(self.filepath):
            raise NameError(warning_text)
    
    def warning_if_invalid_file(self, warning_text):
        """
        Check if file is invalid and raise and error.
        """
        if not is_file(self.filepath):
            raise NameError(warning_text)
        
    def warning_if_invlid_path(self, warning_text):
        """
        Check if path to file is invalid and raise error.
        """
        dirname = get_dirname(self.filepath)
                
        if not is_dir(dirname):
            raise UserWarning(warning_text)

class ReadFile(FileManager):
    """
    Class to deal with reading a file.
    """
    
    def __init__(self, filename):
        super(ReadFile, self).__init__(filename)        
        self.open_file = None
    
    def _get_lines(self):
        
        try:
            lines = self.open_file.read()
        except:
            return []
        
        return get_text_lines(lines)
        
        
    
    def read(self ):
        """
        Read the file.
        
        Return
            list: A list of file lines.
        """
        
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
        """
        Write file. Basically creates the file if it doesn't exist.
        If set_append is True than append any lines to the file instead of replacing.
        """
        if self.append:
            self.append_file()
            
        if not self.append:
            super(WriteFile, self).write_file()
        
    def set_append(self, bool_value):
        """
        Append new lines to end of document instead of replace.
        
        Args
            bool_value (bool)
        """
        self.append = bool_value
        
    def write_line(self, line):
        """
        Write a single line to the file.
        
        Args
            line (str): The line to add to the file.
        """
        
        self.write_file()
        self.open_file.write('%s\n' % line)
        self.close_file()
                
    def write(self, lines, last_line_empty = True):
        """
        Write the lines to the file.
        
        Args
            lines (list): A list of lines. Each entry is a new line in the file.
            last_line_empty (bool): Wether or not to add a line after the last line.
        """
        self.write_file()
        
        try:
            inc = 0
            for line in lines:
    
                if inc == len(lines)-1 and not last_line_empty:
                    self.open_file.write(str('%s' % line))
                    break
                
                self.open_file.write(str('%s\n' % line))
                
                inc+= 1
        except:
            print 'Could not write to file %s.' % self.filepath
            
        self.close_file()

class VersionFile(object):
    """
    Convenience to version a file or folder.
    
    Args
        filepath (str): The path to the file to version.
    """
    
    def __init__(self, filepath):
        self.filepath = filepath
                
        self.filename = get_basename(self.filepath)
        self.path = get_dirname(filepath)
        
        self.version_folder_name = 'version'
        self.version_name = 'version'
        self.version_folder = None
        
    def _create_version_folder(self):
        
        self.version_folder = create_dir(self.version_folder_name, self.path)
        
    def _create_comment_file(self):
        self.comment_file = create_file('comments.txt', self.version_folder)
        
    def _increment_version_file_name(self):
        
        path = join_path(self.version_folder, self.version_name + '.1')
        
        return inc_path_name(path)
        
    def _get_version_path(self, version_int):
        path = join_path(self._get_version_folder(), self.version_name + '.' + str(version_int))
        
        return path
        
    def _get_version_folder(self):
        path = join_path(self.filepath, self.version_folder_name)
        
        return path
    
    def _get_comment_path(self):
        folder = self._get_version_folder()
        
        filepath = None
        
        if folder:
            filepath = join_path(folder, 'comments.txt')
            
        return filepath
            
    def save_comment(self, comment = None, version_file = None, ):
        """
        Save a comment to a log file.
        
        Args
            comment (str)
            version_file (str): The corresponding version file.
        """
         
        
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
        """
        Save a version.
        
        Args
            comment (str): The comment to add to the version.
        
        Return
            str: The new version file name
        """
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
        """
        Set the folder where the version folder should be created.
        
        Args
            folder_path (str): Full path to where the version folder should be created.
        """
        self.path = folder_path
        
    def set_version_folder_name(self, name):
        """
        Set the name of the version folder.
        
        Args
            name (str)
        """
        self.version_folder_name = name
        
    def set_version_name(self, name):
        """
        Set the version name.
        
        Args
            name (str): The name of the version.
        """
        self.version_name = name
        
    def get_version_path(self, version_int):
        """
        Get the path to a version.
        
        Args
            version_int (int): The version number.
            
        Return
            str: The path to the version.
        """
        return self._get_version_path(version_int)
        
    def get_version_comment(self, version_int):
        """
        Get the version comment.
                
        Args
            version_int (int): The version number.
            
        Return
            str: The version comment.
        """
        comment, user = self.get_version_data(version_int)
        return comment
                
    def get_version_data(self, version_int):
        """
        Get the version data.  Comment and user.
                
        Args
            version_int (int): The version number.
            
        Return
            tuple: (comment, user)
        """
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
        """
        Get filepaths of all versions.
        
        Return
            list: List of version filepaths.
        """
        version_folder = self._get_version_folder()
        
        files = get_files_and_folders(version_folder)
        
        if not files:
            return
        
        number_dict = {} 
        number_list = []
        pass_files = []
            
        for filepath in files: 
            
            if not filepath.startswith(self.version_name):
                continue
            
            split_name = filepath.split('.')
            
            if not len(split_name) == 2:
                continue
            
            number = int(split_name[1])
            
            number_list.append(number)
            number_dict[number] = filepath
            
        
        number_list.sort()
        
        for number in number_list:
            pass_files.append(number_dict[number])
        
        return pass_files
    
    def get_latest_version(self):
        """
        Get the filepath to the latest version.
        
        Return
            str: Filepath to latest version.
        """
        versions = self.get_versions()
        
        latest_version = versions[-1]
        
        return join_path(self.filepath, '%s/%s' % (self.version_folder_name, latest_version))
       
       
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
            
            if not value:
                continue
            
            value = fix_slashes(value)
            
            value = eval( str(value) )
            
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
        return get_dirname(directory)
    
    def _get_scope_list(self):
        return get_files_and_folders(self.parent_path)
    
    def _search(self):
        name = super(FindUniquePath, self)._search()
        
        return join_path(self.parent_path, name)

class ParsePython(object):
    """
    This needs to be replaced by something that uses the AST instead.
    """
    def __init__(self, filepath):
        
        self.filepath = filepath
        
        self.main_scope = PythonScope('main')
        self.main_scope.set_indent(0)
        
        self.last_scope = self.main_scope
        self.last_parent_scope = self.main_scope
        
        self.scope_types = ['class', 'def'] 
        self.logic_scope_types = ['if', 'elif', 'else', 'while']
        self.try_scope_types = ['try','except','finally']
        
        self.indents = []
        self.current_scope_lines = []
        
        
        self._parse()
        
        
    def _set_scope(self, scope):
        
        self.last_scope.set_scope_lines(self.current_scope_lines)
        self.current_scope_lines = []
        self.last_scope = scope
        
    def _parse(self):
        
        lines = []
        
        if is_file(self.filepath):
            lines = get_file_lines(self.filepath)
        
        for line in lines:

            strip_line = line.strip()
            
            if not strip_line:
                continue
            
            indent = 0
            
            match = re.search('^ +(?=[^ ])', line)
            
            if match:
                indent = len(match.group(0))
 
            if self.indents:
                last_indent = self.indents[-1]
                
                if indent < last_indent:            
                    pass
        
            self.find_scope_type(strip_line, indent)
            
            self.current_scope_lines.append(line)
            
    def find_scope_type(self, line, indent):
            
        for scope_type in self.scope_types:
            match = re.search('%s(.*?):' % scope_type, line)
            
            if not match:
                continue
            
            scope_line = match.group(0)
            
            match = re.search('(?<=%s)(.*?)(?=\()' % scope_type, scope_line)
            
            if not match:
                continue
            
            scope_name = match.group(0)
            scope_name = scope_name.strip()
            
            match = re.search('\((.*?)\)', scope_line)
            
            if not match:
                continue
            
            scope_bracket = match.group()
            
            parent_scope = self.main_scope
            
            if self.indents:
            
                if indent > self.indents[-1]:
                    parent_scope = self.last_scope
                
                if indent == self.indents[-1]:
                    parent_scope = self.last_parent_scope
                
                if indent < self.indents[-1]:
                    
                    if indent == 0:
                        parent_scope == self.main_scope
                    
                    if indent > 0:
                        parent_indent = self.last_scope.parent.indent
                        parent_scope = self.last_scope.parent
                        
                        #need to go up the scope until finding a matching indent
                        """
                        while parent_indent != indent:
                            
                            parent_indent = self.last_scope.parent.indent
                            parent_scope = self.last_scope.parent
                        """
                    
            sub_scope = PythonScope(scope_name)
            sub_scope.set_bracket(scope_bracket)
            sub_scope.set_parent(parent_scope)   
            sub_scope.set_indent(indent)
            sub_scope.set_scope_type(scope_type)         
            
            self.last_parent_scope = parent_scope
            self.last_scope = sub_scope
            self.indents.append(indent)
            
            return True
        
        return False
            
class PythonScope(object):
    
    def __init__(self, name):
        
        self.name = name
        self.parent = None
        self.children = []
        
        self.bracket_string = '()'
        self.docstring = ''
        self.scope_lines = []
        self.scope_type = ''
        
        self.indent = None
        
    def set_scope_type(self, scope_type_name):
        self.scope_type = scope_type_name
        
    def set_bracket(self, bracket_string):
        
        self.bracket_string = bracket_string
    
    def set_scope_lines(self, lines):
        self.scope_lines = lines

    def set_parent(self, parent_scope):
        self.parent = parent_scope
        parent_scope.set_child(self)
    
    def set_child(self, child_scope):
        self.children.append(child_scope)
        
    def set_indent(self, indent):
        self.indent = indent
    
    

#---- get

def get_basename(directory):
    """
    Get the last part of a directory name. If the name is C:/goo/foo, this will return foo.
    
    Args
        directoroy(str): A directory path.
        
    Return
        str: The last part of the directory path.
    """
    return os.path.basename(directory)

def get_basename_no_extension(filepath):
    """
    Get the last part of a directory name. If the name is C:/goo/foo.py, this will return foo.
    
    Args
        directoroy(str): A directory path.
        
    Return
        str: The last part of the directory path, without any extensions.
    """
    
    basename = get_basename(filepath)
    dot_split = basename.split('.')
    
    new_name = string.join(dot_split[:-1], '.')
    
    return new_name

def get_dirname(directory):
    """
    Given a directory path, this will return the path above the last thing in the path.
    If C:/goo/foo is give, C:/goo will be returned.
    
    Args
        directory (str): A directory path. 
        
    Return
        str: The front portion of the path.
    """
    try:
        return os.path.dirname(directory)
    except:
        return False

def get_user_dir():
    """
    Get the path to the user directory.
    
    Return
        str: The path to the user directory.
    """
    return fix_slashes( os.path.expanduser('~') )

def get_temp_dir():
    """
    Get path to the temp directory.
    
    Return
        str: The path to the temp directory.
    """
    return fix_slashes( tempfile.gettempdir() ) 

def get_cwd():
    """
    Get the current working directory.
    
    Return
        str: The path to the current working directory.
    """
    return os.getcwd()

def get_files(directory):
    """
    Get files found in the directory.
    
    Args
        directory (str): A directory path.
    
    Return
        list: A list of files in the directory.
    """
    files = os.listdir(directory)
    
    found = []
    
    for filepath in files:
        path = join_path(directory, filepath)
        
        if is_file(path):
            found.append(filepath)
    
    return found

def get_folders(directory, recursive = False):
    """
    Get folders found in the directory.
    
    Args
        directory (str): A directory path.
    
    Return
        list: A list of folders in the directory.
    """
    if not is_dir(directory):
        return
    
    
    found_folders = []
    
    for root, dirs, files in os.walk(directory):
        
        del(files)
        
        for folder in dirs:
            
            folder_name = join_path(root, folder)
            
            folder_name = os.path.relpath(folder_name,directory)
            folder_name = fix_slashes(folder_name)
            
            found_folders.append(folder_name)
        
        if not recursive:
            break
        
    
    return found_folders           

def get_files_and_folders(directory):
    """
    Get files and folders found in the directory.
    
    Args
        directory (str): A directory path.
    
    Return
        list: A list of files and folders in the directory.
    """
        
    if not is_dir(directory):
        return
        
    files = os.listdir(directory)
    
    return files

def get_folders_date_sorted(directory):
    """
    Get folders date sorted found in the directory.
    
    Args
        directory (str): A directory path.
    
    Return
        list: A list of folders date sorted in the directory.
    """
    mtime = lambda f: os.stat(os.path.join(directory, f)).st_mtime

    return list(sorted(os.listdir(directory), key = mtime))

def get_files_date_sorted(directory, extension = None):
    """
    Get files date sorted found in the directory.
    
    Args
        directory (str): A directory path.
    
    Return
        list: A list of files date sorted in the directory.
    """    
    if not extension:
        files = get_files(directory)
        
    if extension:
        files = get_files_with_extension(extension, directory)
    
    mtime = lambda f: os.stat(os.path.join(directory, f)).st_mtime
    
    return list(sorted(files, key = mtime))
        

def get_files_with_extension(extension, directory, fullpath = False):
    """
    Get files that have the extensions.
    
    Args
        extension (str): eg. .py, .data, etc.
        directory (str): A directory path.
        fullpath (bool): Wether to returh the filepath or just the file names.
    
    Return
        list: A list of files with the extension.
    """
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
    """
    Get the size of a file.
    
    Args
        filepath (str)
        
    Retrun
        float: The size of the file specified by filepath.
    """
    
    size = os.path.getsize(filepath)
    size_format = round( size * 0.000001, 2 )

    return size_format

def get_last_modified_date(filepath):
    """
    Get the last data a file was modifief.
    
    Args
        filepath (str)
        
    Return
        str: A formatted date and time.
    """
    
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
    """
    Get the current user.
    
    Return
        str: The name of the current user.
    """
    return getpass.getuser()
    
def is_dir(directory):
    """
    Return 
        bool
    """
    if not directory:
        return False
    
    try:
        mode = os.stat(directory)[stat.ST_MODE]
        if stat.S_ISDIR(mode):
            return True
    except:
        return False
    
    
def is_file(filepath):
    """
    Return 
        bool
    """
    if not filepath:
        return False
    
    try:
        
        mode = os.stat(filepath)[stat.ST_MODE]
        if stat.S_ISREG(mode):
            return True
    except:
        return False
    
    
    

def is_file_in_dir(filename, directory):
    """
    
    Args
        filename (str): Filename including path.
        directory (str): Directory name including path.
    
    Return
        bool: Wether the file is in the directory.
    """
    filepath = join_path(directory, filename)
    
    return os.path.isfile(filepath)

def is_same_date(file1, file2):
    """
    Check if 2 files have the same data.
    
    Args
        file1 (str): Filename including path.
        file2 (str): Filename including path.
        
    Return 
        bool
    """
    date1 = os.path.getmtime(file1)
    date2 = os.path.getmtime(file2)
    
    
    value = date1 - date2
    
    if abs(value) < 0.01:
        return True
        
    return False

def inc_path_name(directory, padding = 0):
    """
    Add padding to a name if it is not unique.
    
    Args
        directory (str): Directory name including path.
        padding (int): Where the padding should start.
        
    Return
        str: The new directory with path.
    """
    unique_path = FindUniquePath(directory)
    unique_path.set_padding(padding) 
    
    return unique_path.get()

def get_file_text(filepath):
    """
    Get the text directly from a file. One long string, no parsing.
    
    """

    open_file = open(filepath, 'r')    
    lines = open_file.read()
    open_file.close()
    
    return lines

def get_file_lines(filepath):
    """
    Get the text from a file.
    
    Args
        filepath (str): The filename and path.
    
    Return
        str
    """
    read = ReadFile(filepath)
    
    return read.read()


def get_text_lines(text):
    """
    Get the text from a file. Each line is stored as a different entry in a list.
    
    Args
        text (str): Text from get_file_lines
        
    Return
        list
    """
    text = text.replace('\r', '')
    lines = text.split('\n')
        
    return lines

def open_browser(filepath):
    """
    Open the file browser to the path specified. Currently only works in windows.
    
    Args
        filepath (str): Filename with path.
        
    """
    if sys.platform == 'win32':
        os.startfile(filepath)
        
    else:
        opener ="open" if sys.platform == "darwin" else "xdg-open"
        subprocess.call([opener, filepath])  

#---- edit

def fix_slashes(directory):
    """
    Fix slashes in a path so the are all /
    
    Return
        str: The new directory path.
    """
    directory = directory.replace('\\','/')
    directory = directory.replace('//', '/')
    
    return directory

def set_windows_slashes(directory):
    """
    Set all the slashes in a name so they are all \
    
    Return
        str: The new directory path.
    """
    
    directory = directory.replace('/', '\\')
    directory = directory.replace('//', '\\')
    
    return directory
    
def join_path(directory1, directory2):
    """
    Append directory2 to the end of directory1
    
    Return
        str: The combined directory path.
    """
    if not directory1 or not directory2:
        return
    
    directory1 = fix_slashes( directory1 )
    directory2 = fix_slashes( directory2 )
    
    path = '%s/%s' % (directory1, directory2)
    
    path = fix_slashes( path )
    
    return path

    

def rename(directory, name, make_unique = False):
    """
    Args
        directory (str): Full path to the directory to rename.
        name (str): The new name.
        make_unique (bool): Wether to add a number to the name to make it unique, if needed.
        
    Retrun
        str: The path of the renamed folder, or False if rename fails. 
    """
    
    basename = get_basename(directory)
    
    if basename == name:
        return
    
    parentpath = get_dirname(directory)
    
    renamepath = join_path(parentpath, name)
    
    if make_unique:
        renamepath = inc_path_name(renamepath)

    try:
        print directory, renamepath
        os.rename(directory, renamepath)
    except:
        
        util.show(traceback.format_exc())
        
        return False
    
    return renamepath

def move(path1, path2):
    """
    Move the folder or file pointed to by path1 under the directory path2
    
    Args
        path1 (str): File or folder including path.
        path2 (str): Path where path1 should move to.
        
    Return
        bool: Wether the move was successful.
    """
    try:
        shutil.move(path1, path2)
    except:
        util.warning('Failed to move %s to %s' % (path1, path2))
        return False
    
    return True

def comment(filepath, comment, comment_directory):
    """
    Add a comment to comments.txt
    
    Args
        filepath (str): Filename and path of the file that is being commented about.
        comment (str): The comment
        comment_directoyr (str): Directory where the comments.txt file should be saved. 
    """
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
    """
    Get the comments from a comments.txt file.
    
    Args
        comment_directory (str): Directory where the comments.txt file lives.
        comment_filename (str): The name of the comment file. By default comments.txt
        
    Return
        dict: comment dict, keys are filename, and value is (comment, user) 
    """
    
    if not comment_filename:
        comment_file = join_path(comment_directory, 'comments.txt')
    if comment_filename:
        comment_file = join_path(comment_directory, comment_filename)
    
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
    """
    Write a list of text lines to a file. Every entry in the list is a new line.
    
    Args
        filepath (str): filename and path
        lines (list): A list of text lines. Each entry is a new line.
        append (bool): Wether to append the text or if not replace it.
    
    """
    write_file = WriteFile(filepath)
    write_file.set_append(append)
    write_file.write(lines)
    

#---- create

def create_dir(name, directory, make_unique = False):
    """
    Args
        name (str): The name of the new directory.
        make_unique (bool): Wether to pad the name with a number to make it unique. Only if the name is taken.
        
    Return
        str: The folder name with path. False if create_dir failed.
    """
    
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
    """
    Delete the folder by name in the directory.
    
    Args
        name (str): The name of the folder to delete.
        directory (str): The dirpath where the folder lives.
        
    Return
        str: The folder that was deleted with path.
    """
    
    util.clean_file_string(name)
    
    full_path = join_path(directory, name)
    
    if not is_dir(full_path):
        
        util.show('%s was not deleted. It is not a folder.' % full_path)
        
        return full_path
    
    #read-only error fix
    #if not os.access(full_path, os.W_OK):
    #    os.chmod(full_path, stat.S_IWUSR)
    
    shutil.rmtree(full_path, onerror = delete_read_only_error)  
    
    return full_path

def delete_read_only_error(action, name, exc):
    """
    Helper to delete read only files.
    """
    
    os.chmod(name, stat.S_IWRITE)
    action(name)
    

def refresh_dir(directory):
    """
    Delete everything in the directory.
    """
    
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
    """
    Args
        name (str): The name of the new file. 
        make_unique (bool): Wether to pad the name with a number to make it unique. Only if the name is taken.
        
    Return
        str: The filename with path. False if create_dir failed.
    """
    
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
    """
    Delete the file by name in the directory.
    
    Args
        name (str): The name of the file to delete.
        directory (str): The dirpath where the file lives.
        
    Return
        str: The filepath that was deleted.
    """
    
    full_path = join_path(directory, name)
    
    if not is_file(full_path):
        
        util.show('%s was not deleted.' % full_path)
        
        return full_path
        
    os.chmod(full_path, stat.S_IWRITE)
    os.remove(full_path) 
    
    return full_path

def copy_dir(directory, directory_destination, ignore_patterns = []):
    """
    Copy the directory to a new directory.
    
    Args
        directory (str): The directory to copy with path.
        directory_destination (str): The destination directory.
        ignore_patterns (list): Add txt, py or extensions to ingore them from copying. 
        Eg. if py is added to the ignore patterns list, all *.py files will be ignored from the copy.
        
    Return
        str: The destination directory
    """
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
    """
    Copy the file to a new directory.
    
    Args
        filepath (str): The file to copy with path.
        filepath_destination (str): The destination directory. 
        
    Return
        str: The destination directory
    """
    shutil.copy2(filepath, filepath_destination)
    
    return filepath_destination

    
#---- python

def delete_pyc(python_script):
    """
    Delete the .pyc file the corresponds to the .py file
    """
    
    script_name = get_basename(python_script)
    
    if not python_script.endswith('.py'):
        util.warning('Could not delete pyc file for %s. Be careful not to run this command on files that are not .py extension.' % script_name)
        return
    
    compile_script = python_script + 'c'
            
    if is_file(compile_script):
        
        c_name = get_basename(compile_script)
        c_dir_name = get_dirname(compile_script)
        
        if not c_name.endswith('.pyc'):
            return
        
        delete_file( c_name, c_dir_name)
            
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
        
        except:
            return traceback.format_exc()
        
        finally:
            try: fin.close()
            except: pass
            
    except ImportError:
        traceback.print_exc(file = sys.stderr)
        return None

def load_python_module(module_name, directory):
    """
    Load a module by name and return its instance.
    
    Args
        module_name (str): The name of the module found in the directory.
        directory (str): The directory path where the module lives.
        
    Return
        module instance: The module instance. 
        With the module instance you can access programattically functions and attributes of the modules.
        
    """    
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
                filepath.close()
                return traceback.format_exc()
            
            finally:
                if filepath:
                    filepath.close()
            
            return module
        
def get_package_path_from_name(module_name, return_module_paths = False):
    
    split_name = module_name.split('.')
    
    path = None
    
    for name in split_name:
        
        if path:
            
            test_path = join_path(path, name)
            
            if not is_dir(test_path):
                
                if not return_module_paths:
                    return None
                
                if return_module_paths:
                    test_path = join_path(path, '%s.py' % name)
                    return test_path
                
            files = get_files(test_path)
            
            if '__init__.py' in files:
                path = test_path
            
            if not '__init__.py' in files:
                return None
        
        if not path:
            try:
                module = imp.find_module(name)
                
                path = module[1]
                path = fix_slashes(path)
                
            except:
                return None
            
    return path
    
def get_line_imports(lines):
    """
    This needs to be replaced by AST stuff.
    """
    module_dict = {}
    
    for line in lines:
        
        split_line = line.split()
        split_line_count = len(split_line)
        
        for inc in range(0, split_line_count):
            
            module_prefix = ''
            
            if split_line[inc] == 'import':
                
                if inc > 1:
                    if split_line[inc-2] == 'from':
                        module_prefix = split_line[inc-1]
                
                if inc < split_line_count - 1:
                    
                    module = split_line[inc+1]
                    namespace = module
                    
                    if module_prefix:
                        module = '%s.%s' % (module_prefix, module)
                    
                    module_path = get_package_path_from_name(module, return_module_paths=True)
                    
                    module_dict[namespace] = module_path
    
    return module_dict
                    
def get_defined(module_path):
    """
    Get classes and definitions from the text of a module.
    """
    file_text = get_file_text(module_path)
    
    defined = []
    
    ast_tree = ast.parse(file_text)
    
    for node in ast_tree.body:
        
        
        if isinstance(node, ast.FunctionDef):
            function_name = node.name + '()'
            defined.append( function_name )
            
        if isinstance(node, ast.ClassDef):
            defined.append(node.name)
            
    return defined
    

    
def launch_maya(version, script = None):
    """
    Needs maya installed. If maya is installed in the default directory, will launch the version specified.
    """
    if sys.platform == 'win32':
        path = 'C:\\Program Files\\Autodesk\\Maya%s\\bin\\maya.exe' % version
        
        if script:
            os.system("start \"maya\" \"%s\" -script \"%s\"" % (path, script))
        if not script:
            os.system("start \"maya\" \"%s\"" % path)
            
def launch_nuke(version, command = None):
    """
    Needs nuke installed. If nuke is installed in default path, it will launch the version specified.
    """
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
    """
    Needs ffmpeg installed. 
    """
    path = 'X:\\Tools\\ffmpeg\\bin\\ffmpeg.exe'
    
    os.system('start \"ffmpeg\" \"%s\"' % path)
    
