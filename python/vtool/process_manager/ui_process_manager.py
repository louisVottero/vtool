# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

import sys

from vtool import qt_ui

#import qt_ui
from vtool import util_file
from vtool import util

import process
import ui_view
import ui_data
import ui_code
import ui_settings

if qt_ui.is_pyqt():
    from PyQt4 import QtGui, QtCore, Qt, uic
if qt_ui.is_pyside():
    from PySide import QtCore, QtGui
    
class ProcessManagerWindow(qt_ui.BasicWindow):
    
    title = 'Process Manager'
    
    def __init__(self, parent = None):
        
        self.process = process.Process()
        self.tab_widget = None
        self.view_widget = None
        self.data_widget = None
        self.code_widget = None
        self.directories = None
        self.project_directory = None
        self.last_tab = 0
        self.last_process = None
        super(ProcessManagerWindow, self).__init__(parent) 
        
        self._set_default_directory()
        self._setup_settings_file()
        
        project_directory = self.settings.get('project_directory')
        code_directory = self.settings.get('code_directory')
        
        self._set_default_project_directory(project_directory)
        if code_directory:
            self.set_code_directory(code_directory)
        
    def sizeHint(self):
        return QtCore.QSize(400,800)
        
    def _setup_settings_file(self):
        
        settings_file = util_file.SettingsFile()
        settings_file.set_directory(self.directory)
        
        self.settings = settings_file
        
    def _build_widgets(self):
        
        self.active_title = QtGui.QLabel('-')
        self.active_title.setAlignment(QtCore.Qt.AlignCenter)
        
        self.tab_widget = QtGui.QTabWidget()
        self.tab_widget.currentChanged.connect(self._tab_changed)
                
        self.view_widget = ui_view.ViewProcessWidget()
        self.view_widget.item_clicked.connect(self._update_process)
        
        self.data_widget = ui_data.DataProcessWidget()
        
        self.code_widget = ui_code.CodeProcessWidget()
        self.settings_widget = ui_settings.SettingsWidget()
        self.settings_widget.project_directory_changed.connect(self.set_project_directory)
        self.settings_widget.code_directory_changed.connect(self.set_code_directory)
        
        self.tab_widget.addTab(self.settings_widget, 'Settings')       
        self.tab_widget.addTab(self.view_widget, 'View')
        self.tab_widget.addTab(self.data_widget, 'Data')
        self.tab_widget.addTab(self.code_widget, 'Code')
        
        self.tab_widget.setTabEnabled(2, False)
        self.tab_widget.setTabEnabled(3, False)
        self.tab_widget.setCurrentIndex(1)
        
        self.main_layout.addWidget( self.active_title )
        self.main_layout.addWidget( self.tab_widget )
        
        self.process_button = QtGui.QPushButton('PROCESS')
        self.browser_button = QtGui.QPushButton('Browse')
        
        button_layout = QtGui.QHBoxLayout()
        
        button_layout.addWidget(self.process_button)
        button_layout.addWidget(self.browser_button)
        
        self.browser_button.clicked.connect(self._browser)
        self.process_button.clicked.connect(self._process)
        
        self.main_layout.addLayout( button_layout )
        
    def _set_default_directory(self):
        default_directory = process.get_default_directory()
        self.set_directory(default_directory)
        
    def _set_default_project_directory(self, directory):
        
        if not directory:
            directory = util_file.join_path(self.directory, 'project')
            
        self.settings_widget.set_project_directory(directory)
        
    def _set_title(self, name):
        self.active_title.setText(name)
        
    def _tab_changed(self):
                
        if self.tab_widget.currentIndex() > 1:
            item = self.view_widget.tree_widget.currentItem()
            
            if not item:
                return
            
            process_name = item.get_name()
            self.process.load(process_name)
            
            if item and self.tab_widget.currentIndex() == 2:
                self.data_widget.set_directory(self.process.get_path())
                
                self.last_tab = 2
                return
            
            if item and self.tab_widget.currentIndex() == 3:
                self.code_widget.set_directory(self.process.get_path())
                code_directory = self.settings.get('code_directory')
                self.code_widget.set_external_code_library(code_directory)
                
                self.last_tab = 3
                return
        
        self.last_tab = 1
        
    def _update_process(self, name, item):
               
         
        self.code_widget.code_widget.code_edit.save_tabs(self.last_process)
        self.code_widget.code_widget.code_edit.clear()
        self.code_widget.script_widget.code_manifest_tree.clearSelection()
                
        if name:
            
            self.process.load(name)        
            
            self._set_title(name)

            self.tab_widget.setTabEnabled(2, True)
            self.tab_widget.setTabEnabled(3, True)
            
        if not name:
            self._set_title('-')

            self.tab_widget.setTabEnabled(2, False)
            self.tab_widget.setTabEnabled(3, False)
            
        self.last_process = name
        
        
                                
    def _get_current_path(self):
        item = self.view_widget.tree_widget.currentItem()
        
        if item:
            process_name = item.get_name()
            self.process.load(process_name)
            return self.process.get_path()
           
    def _process(self):
        self.process_button.setDisabled(True)
        
        self.code_widget.reset_process_script_state()
        
        self.tab_widget.setCurrentIndex(3)
        
        code_directory = self.settings.get('code_directory')
        self.process.set_external_code_library(code_directory)
        
        if util.is_in_maya():
            import maya.cmds as cmds
            cmds.file(new = True, f = True)
        
        scripts, states = self.process.get_manifest()
        scripts = self.process.get_manifest_scripts(False)
        
        if not scripts:
            self.process_button.setEnabled(True)
            return
        
        script_count = len(scripts)
        
        for inc in range(0, script_count):
            
            state = states[inc]
            
            if not state:
                self.code_widget.set_process_script_state(scripts[inc], -1)
                continue
            
            self.code_widget.set_process_script_state(scripts[inc], 2)
            
            status = self.process.run_script(scripts[inc])
            
            if not status == 'Success':
                self.code_widget.set_process_script_state(scripts[inc], 0)
                #do not remove print
                print status
                
            if status == 'Success':
                self.code_widget.set_process_script_state(scripts[inc], 1)
            
        self.process_button.setEnabled(True)
                    
    def _browser(self):
        
        directory = self._get_current_path()
        
        if not directory:
            
            directory = self.project_directory

        if directory and self.tab_widget.currentIndex() == 0:
            util_file.open_browser(self.directory)
        if directory and self.tab_widget.currentIndex() == 1:
            util_file.open_browser(directory)
        if directory and self.tab_widget.currentIndex() == 2:
            path = self.process.get_data_path()
            util_file.open_browser(path)
        if directory and self.tab_widget.currentIndex() == 3:
            path = self.process.get_code_path()
            util_file.open_browser(path)    
              
    def _set_project_history(self, current_directory, previous_directory):
                
        history = self.settings.get('project_history')
        
        if previous_directory != current_directory and previous_directory:

            if not history:
                history = []
            
            found_history = []
            
            for inc in range(0, len(history)):
                
                if not util_file.is_dir(history[inc]):
                    continue
                
                if history[inc] == previous_directory:
                    continue

                if history[inc] == current_directory:
                    continue
                
                found_history.append(str(history[inc]))
                   
            history = found_history 

            history.insert(0, str(previous_directory))
            
            self.settings.set('project_history', history)
            
        if history:
            self.settings_widget.set_history(history)
        
    def set_directory(self, directory):
        
        self.directory = directory
        
        if not util_file.is_dir(directory):
            util_file.create_dir(name = None, directory = directory)
        
    def set_project_directory(self, directory, sub_part = None):
        
        if not directory:
            return

        if not sub_part:
        
            previous_project = self.project_directory
            
            if not util_file.is_dir(directory):
                util_file.create_dir(None, directory)
        
            self.project_directory = directory
            self.settings.set('project_directory', str(self.project_directory))
            self._set_project_history(directory, previous_project)
            
            self.view_widget.clear_sub_path_filter()
        
        
        if sub_part:
            directory = sub_part
            
        self.process.set_directory(directory)
        self.view_widget.set_directory(directory)
        
    def set_code_directory(self, directory):
        
        if directory == None:
            directory = ''
                    
        self.settings.set('code_directory', str(directory))
        self.code_widget.set_code_directory(directory)
        self.settings_widget.set_code_directory(directory)
        

        