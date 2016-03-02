# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

import sys

from vtool import qt_ui
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
    
    title = 'VETALA'
    
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
        self.sync_code = False
        self.kill_process = False
        self.build_widget = None
        self.last_item = None
        self.runtime_values = {}
        self.handle_selection_change = True
        
        super(ProcessManagerWindow, self).__init__(parent) 
        
        self._set_default_directory()
        self._setup_settings_file()
        
        shortcut = QtGui.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Escape), self)
        shortcut.activated.connect(self._set_kill_process)
        
        project_directory = self.settings.get('project_directory')
        project_history = self.settings.get('project_history')
        self._set_default_project_directory(project_directory, project_history)
        
        code_directory = self.settings.get('code_directory')
        if code_directory:
            self.set_code_directory(code_directory)
            
        self.view_widget.tree_widget.itemChanged.connect(self._item_changed)
        self.view_widget.tree_widget.item_renamed.connect(self._item_changed)
        self.view_widget.tree_widget.itemSelectionChanged.connect(self._item_selection_changed)
        self.view_widget.sync_code.connect(self._sync_code)
        self.view_widget.tree_widget.itemDoubleClicked.connect(self._item_double_clicked)
           
        self.view_widget.set_settings( self.settings )
        self.settings_widget.set_settings(self.settings)
        
    def _sync_code(self):
        self.sync_code = True
          
    def _item_double_clicked(self):
        
        self.tab_widget.setCurrentIndex(3)
                
    def _item_changed(self, item):
        
        name = '-'
        
        if hasattr(item, 'name'):
            
            name = item.get_name()
        
        self._set_title(name)
        
        self._update_build_widget(name)
        
    def _item_selection_changed(self):
        
        if not self.handle_selection_change:
            return
        
        items = self.view_widget.tree_widget.selectedItems()
        
        if not items:
            
            if self.last_item:
                self.view_widget.tree_widget.setCurrentItem(self.last_item)
                return
            if not self.last_item:
                self._update_process(None)
                self.build_widget.hide()
                return
        
        item = items[0]
        
        name = item.get_name()

        self._update_build_widget(name)

        self._set_title(name)
        self._update_process(name)
        self.last_item = item
        
    def _update_build_widget(self, process_name):
        
        path = self.view_widget.tree_widget.directory
        path = util_file.join_path(path, process_name)
        data_path = util_file.join_path(path, '.data/build')
        
        data_dir = util_file.join_path(path, '.data')
        
        if not util_file.is_dir(data_dir):
            return
        
        self.build_widget.update_data(data_dir)
        
        self.build_widget.set_directory(data_path)
        
        self.build_widget.show()
        
    def sizeHint(self):
        return QtCore.QSize(400,800)
        
    def _setup_settings_file(self):
        
        settings_file = util_file.SettingsFile()
        
        settings_file.set_directory(self.directory)
        
        self.settings = settings_file
        
    def _build_widgets(self):
        
        self.header_layout = QtGui.QHBoxLayout()
        
        self.active_title = QtGui.QLabel('-')
        self.active_title.setAlignment(QtCore.Qt.AlignCenter)
        
        self.header_layout.addWidget(self.active_title, alignment = QtCore.Qt.AlignCenter)
        
        self.tab_widget = QtGui.QTabWidget()
        self.tab_widget.currentChanged.connect(self._tab_changed)
                
        self.view_widget = ui_view.ViewProcessWidget()
        
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
        
        self.main_layout.addSpacing(4)
        self.main_layout.addLayout(self.header_layout)
        
        self.main_layout.addSpacing(4)
        self.main_layout.addWidget( self.tab_widget )
        
        #self.process_layout = QtGui.QVBoxLayout()
        
        self.process_button = QtGui.QPushButton('PROCESS')
        self.process_button.setDisabled(True)
        self.process_button.setMinimumWidth(150)
        self.process_button.setMinimumHeight(40)
        
        self.stop_button = QtGui.QPushButton('STOP!')
        self.stop_button.setMaximumWidth(50)
        self.stop_button.hide()
        
        self.browser_button = QtGui.QPushButton('Browse')
        self.browser_button.setMaximumWidth(100)
        help_button = QtGui.QPushButton('?')
        help_button.setMaximumWidth(60)       
        
        btm_layout = QtGui.QVBoxLayout()
        
        button_layout = QtGui.QHBoxLayout()
        button_layout.setAlignment(QtCore.Qt.AlignLeft)
        button_layout.addWidget(self.process_button)
        button_layout.addWidget(self.stop_button)
        
                
        button_layout.addWidget(self.browser_button)
        button_layout.addWidget(help_button)
        
        self.build_widget = ui_data.ProcessBuildDataWidget()
        self.build_widget.hide()
        
        
        btm_layout.addLayout(button_layout)
        btm_layout.addSpacing(10)
        btm_layout.addWidget(self.build_widget, alignment = QtCore.Qt.AlignBottom)
        
                
        self.browser_button.clicked.connect(self._browser)
        self.process_button.clicked.connect(self._process)
        help_button.clicked.connect(self._open_help)
        self.stop_button.clicked.connect(self._set_kill_process)
        
        self.main_layout.addLayout(btm_layout)
        
        self.build_widget.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        
    def _update_process(self, name):
        
        self.code_widget.code_widget.code_edit.close_tabs()
        self.code_widget.script_widget.code_manifest_tree.clearSelection()
        self.code_widget.code_widget.code_edit.clear()
        
        
        items = self.view_widget.tree_widget.selectedItems()
        
        title = '-'
        
        if items and name != None:
            title = items[0].get_name()
        
        if name:
            
            self.process.load(name)  
            
            if self.runtime_values:
                self.process.set_runtime_dict(self.runtime_values)      
            
            self._set_title(title)

            self.tab_widget.setTabEnabled(2, True)
            self.tab_widget.setTabEnabled(3, True)
            
            self.process_button.setEnabled(True)
        
        if not name:
            
            self._set_title('-')

            self.tab_widget.setTabEnabled(2, False)
            self.tab_widget.setTabEnabled(3, False)
            
            self.process_button.setDisabled(True)
            
        self.last_process = name
        
    def _set_default_directory(self):
        default_directory = process.get_default_directory()
        
        self.set_directory(default_directory)
        
    def _set_default_project_directory(self, directory, history = None):
        
        if directory:
            if type(directory) != list:
                directory = ['', directory]
        
        if not directory:
            directory = ['default', util_file.join_path(self.directory, 'project')]
        
        self.settings_widget.set_project_directory(directory, history)
        
        self.set_project_directory(directory)
        
    def _set_title(self, name):
        
        if not name:
            return
        
        if self.project_directory:
            self.settings.set('process', [name, str(self.project_directory[1])])
        
        name = name.replace('/', '  /  ')
        
        self.active_title.setText(name)
        

        
    def _open_help(self):
        import webbrowser
        
        filename = __file__
        folder = util_file.get_dirname(filename)
        
        split_folder = folder.split('\\')
        folder = split_folder[:-1]
        
        path = 'http://www.vetalarig.com/docs/html/index.html'
        webbrowser.open(path, 0)
        
        
    def _tab_changed(self):
        
        if self.tab_widget.currentIndex() == 0:
            if self.build_widget:
                self.build_widget.hide()     
             
        if self.tab_widget.currentIndex() == 1:
            if self.build_widget:
                self.build_widget.show()
                
        if self.tab_widget.currentIndex() > 1:
            item = self.view_widget.tree_widget.currentItem()
            
            if not item:
                return
            
            process_name = item.get_name()
            self.process.load(process_name)
            
            if item and self.tab_widget.currentIndex() == 2:
                if self.build_widget:
                    self.build_widget.hide()
                
                path = self.view_widget.tree_widget.directory
                path = util_file.join_path(path, self.process.get_name())
                
                self.data_widget.set_directory(path)
                
                self.last_tab = 2
                return
            
            if item and self.tab_widget.currentIndex() == 3:
                
                if self.build_widget:
                    self.build_widget.show()
                
                path = self.view_widget.tree_widget.directory
                path = util_file.join_path(path, self.process.get_name())
                
                self.code_widget.set_directory(path, sync_code = self.sync_code)
                if self.sync_code:
                    self.sync_code = False
         
                code_directory = self.settings.get('code_directory')
                self.code_widget.set_external_code_library(code_directory)
                
                self.code_widget.set_settings(self.settings)
                self.code_widget.set_current_process(self.process.get_name())
                
                self.last_tab = 3
                
                return
        
        self.last_tab = 1
        

        
    def _get_current_path(self):
        items = self.view_widget.tree_widget.selectedItems()
        
        item = None
        
        if items:
            item = items[0]
        
        if item:
            process_name = item.get_name()
            self.process.load(process_name)
            
            return self.process.get_path()
           
    def _set_kill_process(self):
        self.kill_process = True
        
    def _process(self):
        
        if util.is_in_maya():
            import maya.cmds as cmds
            if cmds.file(q = True, mf = True):
                result = qt_ui.get_permission('Changes not saved. Run process anyways?', self)
                if not result:
                    return
                
        self.kill_process = False
        self.stop_button.show()
        
        self.process_button.setDisabled(True)
        
        self.code_widget.reset_process_script_state()
        
        try:
            #this was not working when processing in a new Vetala session without going to the code tab.
            self.code_widget.refresh_manifest()
        except:
            pass
        
        self.tab_widget.setCurrentIndex(3)
        
        code_directory = self.settings.get('code_directory')
        self.process.set_external_code_library(code_directory)
        
        if util.is_in_maya():
            cmds.file(new = True, f = True)
        
        scripts, states = self.process.get_manifest()
        
        if not scripts:
            self.process_button.setEnabled(True)
            return
        
        stop_on_error = self.settings.get('stop_on_error')
        
        script_count = len(scripts)
        
        util.show('\n\a\tRunning %s Scripts\t\a\n' % self.process.get_name())
        
        skip_scripts = []
        
        for inc in range(0, script_count):
            
            script = scripts[inc]
            script_name = util_file.remove_extension(script)
            
            if self.kill_process:
                self.kill_process = False
                break
            
            if states:
                state = states[inc]
                
                if not state:
                    self.code_widget.set_process_script_state(scripts[inc], -1)
                    skip_scripts.append(script_name)
                    continue
            
            skip = False
            
            for skip_script in skip_scripts:
                common_path = util_file.get_common_path(script, skip_script)
                if common_path == skip_script:
                    if script.startswith(skip_script):
                        skip = True
            
            if skip:
                continue
            
            self.code_widget.set_process_script_state(scripts[inc], 2)
            
            status = self.process.run_script(script_name, False)
            
            if not status == 'Success':
                
                self.code_widget.set_process_script_state(scripts[inc], 0)
                util.show(status)
                
                if stop_on_error:
                    break
                #util.show(status)
                
            if status == 'Success':
                self.code_widget.set_process_script_state(scripts[inc], 1)
                
                util.show('\tSuccess')
            
            
            
        self.process_button.setEnabled(True)
        self.stop_button.hide()
        
    def _browser(self):
        
        directory = self._get_current_path()
        
        if not directory:
            
            directory = str(self.project_directory[1])

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
                
                history_inc = history[inc]
                
                if not util_file.is_dir(history_inc[1]):
                    continue
                
                if history_inc in found_history:
                    continue

                found_history.append(history_inc)
                   
            history = found_history
            
            if not current_directory in history:
                history.insert(0, current_directory) 
                
            self.settings.set('project_history', history)
            return
            
        if history:
            if not current_directory in history:
                history.insert(0, current_directory)
                
            self.settings_widget.set_history(current_directory, history)
            
        
    def set_directory(self, directory):
        
        self.directory = directory
        
        if not util_file.is_dir(directory):
            util_file.create_dir(name = None, directory = directory)
        
    def set_project_directory(self, directory, sub_part = None):
        #history should not be there...
        
        #handle selection change should use a decorator...
        self.handle_selection_change = False
        
        if type(directory) != list:
            directory = ['', directory]
        
        self._update_process(None)
        
        if not directory:
            self.process.set_directory(None)
            self.view_widget.set_directory(None)
            self.handle_selection_change = True
            return

        if not sub_part:
            
            if self.project_directory:
                previous_project = str(self.project_directory[1])
            if not self.project_directory:
                previous_project = None
            
            if not util_file.is_dir(str(directory[1])):
                util_file.create_dir(None, str(directory[1]))
        
            self.project_directory = directory
            
            clean_list = []
            
            #needed for PyQt
            for project in self.project_directory:
                clean_list.append( str(project) )
            
            self.settings.set('project_directory', clean_list)
            
            self._set_project_history(directory, previous_project)
            
            self.view_widget.clear_sub_path_filter()
        
            directory = str(directory[1])
        
        if sub_part:
            directory = sub_part
            
        self.process.set_directory(directory)
        self.view_widget.set_directory(directory)
        
        self.handle_selection_change = True
        
    def set_code_directory(self, directory):
        
        if directory == None:
            directory = self.settings.get('code_directory')            
        
        self.settings.set('code_directory', directory)
        self.code_widget.set_code_directory(directory)
        self.settings_widget.set_code_directory(directory)
        
        directories = util.convert_to_sequence(directory)
        
        for directory in directories:
            
            if util_file.is_dir(directory):
                if not directory in sys.path:
                    sys.path.append(directory)
        
