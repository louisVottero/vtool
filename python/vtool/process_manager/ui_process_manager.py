# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

import sys
import __builtin__

from vtool import qt_ui
from vtool import util_file
from vtool import util

import process
import ui_view
import ui_options
import ui_templates
import ui_data
import ui_code
import ui_settings
import os

if qt_ui.is_pyqt():
    from PyQt4 import QtGui, QtCore, Qt, uic
if qt_ui.is_pyside():
    from PySide import QtCore, QtGui
    
class ProcessManagerWindow(qt_ui.BasicWindow):
    
    title = 'VETALA'
    
    def __init__(self, parent = None):
        
        self.settings = None
        self.template_settings = None
        
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
        
        shortcut = QtGui.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Escape), self)
        shortcut.activated.connect(self._set_kill_process)
            
        self.view_widget.tree_widget.itemChanged.connect(self._item_changed)
        self.view_widget.tree_widget.item_renamed.connect(self._item_changed)
        self.view_widget.tree_widget.itemSelectionChanged.connect(self._item_selection_changed)
        self.view_widget.copy_done.connect(self._copy_done)
        self.view_widget.tree_widget.itemDoubleClicked.connect(self._item_double_clicked)
        self.view_widget.tree_widget.show_options.connect(self._show_options)
        self.view_widget.tree_widget.show_templates.connect(self._show_templates)
        self.view_widget.tree_widget.process_deleted.connect(self._process_deleted)
        
        
        self._set_default_directory()
        self._setup_settings_file()
        
        self._set_default_project_directory()
        self._set_default_template_directory()
        
        code_directory = self.settings.get('code_directory')
        if code_directory:
            self.set_code_directory(code_directory)
        
        
    def _show_options(self):
        
        self.process_splitter.setSizes([1,1])
        self._load_options(self.process.get_path())
        self.option_tabs.setCurrentIndex(0)
        
    def _show_templates(self):
        
        self.process_splitter.setSizes([1,1])
        self.option_tabs.setCurrentIndex(1)
        
    def _process_deleted(self):
        self._clear_code(close_windows=True)
        
    def _copy_done(self):
        self.sync_code = True
        
        self._load_options(self.process.get_path())
          
    def _item_double_clicked(self):
        
        self.tab_widget.setCurrentIndex(3)
                
    def _item_changed(self, item):
        
        name = '-'
        
        if hasattr(item, 'name'):
            
            name = item.get_name()
        
        self._set_title(name)
        
        self._update_build_widget(name)
        
        self._load_options(item.get_path())
        
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
        
        path = item.get_path()
        
        self._load_options(path)
        
    def _load_options(self, directory):
        
        self.option_widget.set_directory(directory)
        
        has_options = self.option_widget.has_options()
        
        if has_options:
            self.process_splitter.setSizes([1,1])
        if not has_options and self.option_tabs.currentIndex() == 0:
            self.process_splitter.setSizes([1,0])
        
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
        return QtCore.QSize(650,800)
        
    def _setup_settings_file(self):
        
        settings_file = util_file.SettingsFile()
        
        settings_file.set_directory(self.directory)
        
        self.settings = settings_file
        
        self.view_widget.set_settings( self.settings )
        self.settings_widget.set_settings(self.settings)
        
        #template stuff
        vetala_path = util.get_env('VETALA_PATH')
        vetala_path = util_file.join_path(vetala_path, 'templates')
        custom_template_file = 'template_settings.txt'
        
        settings = self.settings
        
        template_custom_settings = util_file.join_path(vetala_path, custom_template_file)
        
        if util_file.is_file(template_custom_settings):
            
            settings = util_file.SettingsFile()
            settings.set_directory(vetala_path, custom_template_file)
            util.show('Custom template file found. %s' % template_custom_settings)
            self.template_settings = settings
        else:
            if not self.settings.has_setting('template_directory') or not self.settings.get('template_directory'):
                self.settings.set('template_directory', ['Vetala Templates', vetala_path])
        
        self.settings_widget.set_template_settings(settings)
        self.template_widget.set_settings(settings)
        
    def _build_widgets(self):
        
        self.header_layout = QtGui.QHBoxLayout()
        
        self.active_title = QtGui.QLabel('-')
        self.active_title.setAlignment(QtCore.Qt.AlignCenter)
        
        self.header_layout.addWidget(self.active_title, alignment = QtCore.Qt.AlignCenter)
        
        self.tab_widget = QtGui.QTabWidget()
        self.tab_widget.currentChanged.connect(self._tab_changed)
        
        self.view_widget = ui_view.ViewProcessWidget()
        
        self.option_tabs = QtGui.QTabWidget()
        
        option_layout = QtGui.QVBoxLayout()
        self.option_scroll = QtGui.QScrollArea()
        self.option_scroll.setWidgetResizable(True)
        self.option_scroll.setMinimumWidth(350)
        self.option_widget = ui_options.ProcessOptionsWidget()
        self.option_scroll.setWidget(self.option_widget)
        self.option_scroll.setFocusPolicy(QtCore.Qt.NoFocus)
        option_layout.addWidget(self.option_scroll)
        
        option_widget = QtGui.QWidget()
        option_widget.setLayout(option_layout)
        
        self.template_widget = ui_templates.TemplateWidget()
        self.template_widget.set_active(False)
        self.template_widget.current_changed.connect(self._template_current_changed)
        self.template_widget.add_template.connect(self._add_template)
        self.template_widget.merge_template.connect(self._merge_template)
        
        self.option_tabs.addTab(option_widget, 'Options')
        self.option_tabs.addTab(self.template_widget, 'Templates')
        
        self.option_tabs.currentChanged.connect(self._option_changed)
        
        self.data_widget = ui_data.DataProcessWidget()
        
        self.code_widget = ui_code.CodeProcessWidget()
        self.settings_widget = ui_settings.SettingsWidget()
        self.settings_widget.project_directory_changed.connect(self.set_project_directory)
        self.settings_widget.code_directory_changed.connect(self.set_code_directory)
        self.settings_widget.template_directory_changed.connect(self.set_template_directory)
        
        #splitter stuff
        self.process_splitter = QtGui.QSplitter()
        self.process_splitter.addWidget(self.view_widget)
        self.process_splitter.addWidget(self.option_tabs)
        self.process_splitter.setSizes([1,0])
        
        self.tab_widget.addTab(self.settings_widget, 'Settings')       
        self.tab_widget.addTab(self.process_splitter, 'View')
        #self.tab_widget.addTab(self.view_widget, 'View')
        self.tab_widget.addTab(self.data_widget, 'Data')
        self.tab_widget.addTab(self.code_widget, 'Code')
        
        self.tab_widget.setTabEnabled(2, False)
        self.tab_widget.setTabEnabled(3, False)
        self.tab_widget.setCurrentIndex(1)
        
        self.main_layout.addSpacing(4)
        self.main_layout.addLayout(self.header_layout)
        
        self.main_layout.addSpacing(4)
        self.main_layout.addWidget( self.tab_widget )
        
        left_button_layout = QtGui.QHBoxLayout()
        right_button_layout = QtGui.QHBoxLayout()
        
        self.process_button = QtGui.QPushButton('PROCESS')
        self.process_button.setDisabled(True)
        self.process_button.setMinimumWidth(150)
        self.process_button.setMinimumHeight(40)
        
        self.stop_button = QtGui.QPushButton('STOP (Esc key)')
        self.stop_button.setMaximumWidth(140)
        self.stop_button.setMinimumHeight(30)
        self.stop_button.hide()
        
        self.browser_button = QtGui.QPushButton('Browse')
        self.browser_button.setMaximumWidth(120)
        help_button = QtGui.QPushButton('Help')
        help_button.setMaximumWidth(100)       
        
        btm_layout = QtGui.QVBoxLayout()
        
        button_layout = QtGui.QHBoxLayout()
        
        left_button_layout.setAlignment(QtCore.Qt.AlignLeft)
        left_button_layout.addWidget(self.process_button)
        left_button_layout.addSpacing(10)
        left_button_layout.addWidget(self.stop_button)
        
        right_button_layout.setAlignment(QtCore.Qt.AlignRight)
        right_button_layout.addWidget(self.browser_button)
        right_button_layout.addWidget(help_button)
        
        button_layout.addLayout(left_button_layout)
        button_layout.addLayout(right_button_layout)
        
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
        
    def _add_template(self, process_name, directory):
        
        source_process = process.Process(process_name)
        source_process.set_directory(directory)
        
        self.view_widget.tree_widget.paste_process(source_process)
        """
        target_process = None
        
        items = self.view_widget.tree_widget.selectedItems()
        if items:
            target_item = items[0]
            target_process = target_item.get_process()
        if not items:
            target_item = None
        
        if not target_process:
            target_process = process.Process()
            target_process.set_directory(self.view_widget.tree_widget.directory)
            target_item = None 
        
        new_process = process.copy_process(source_process, target_process)
        
        if not new_process:
            return
        
        new_item = self.view_widget.tree_widget._add_process_item(new_process.get_name(), target_item)
        
        if target_process:
            if target_item:
                self.view_widget.tree_widget.collapseItem(target_item)
                self.view_widget.tree_widget.expandItem(target_item)
            
        if not target_process:
            self.view_widget.tree_widget.scrollToItem(new_item)
            
        self.view_widget.tree_widget.copy_process.emit()
        """
        
    def _merge_template(self, process_name, directory):
        
        source_process = process.Process(process_name)
        source_process.set_directory(directory)
        
        self.view_widget.tree_widget.merge_process(source_process)
        
    def _option_changed(self):
        
        if self.option_tabs.currentIndex() == 0:
            self.template_widget.set_active(False)
        
        if self.option_tabs.currentIndex() == 1:
            self.template_widget.set_active(True)
            
    def _clear_code(self, close_windows = False):
        
        self.code_widget.code_widget.code_edit.close_tabs()
        self.code_widget.script_widget.code_manifest_tree.clearSelection()
        self.code_widget.code_widget.code_edit.clear()
        self.code_widget.set_directory(None, sync_code = False)
        #self.code_widget
        if close_windows:
            self.code_widget.code_widget.code_edit.close_windows()
        
    def _update_process(self, name):
        
        self._clear_code()
        
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
        
    def _set_default_project_directory(self):
        
        directory = self.settings.get('project_directory')
        
        if directory == None:
            return
        
        if directory:
            if type(directory) != list:
                directory = ['', directory]
        
        if not directory:
            directory = ['default', util_file.join_path(self.directory, 'project')]
        
        self.settings_widget.set_project_directory(directory)
        
        self.set_project_directory(directory)
        
    def _set_default_template_directory(self):
        
        if not self.template_settings:
            directory = self.settings.get('template_directory')
        if self.template_settings:
            directory = self.template_settings.get('template_directory')
        
        if directory == None:
            return
        
        if directory:
            if type(directory) != list:
                directory = ['',directory]
        
        self.settings_widget.set_template_directory(directory)
        
        self.set_template_directory(directory)
            
    
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
                
            self.set_template_directory()
                
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
        util.set_env('VETALA_STOP', True)
        self.kill_process = True
        
    def _process(self):
        
        if util.is_in_maya():
            import maya.cmds as cmds
            if cmds.file(q = True, mf = True):
                result = qt_ui.get_permission('Changes not saved. Run process anyways?', self)
                if not result:
                    return
        
        watch = util.StopWatch()
        watch.start(feedback = False)
                
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
        
        util.set_env('VETALA_RUN', True)
        util.set_env('VETALA_STOP', False)
        
        stop_on_error = self.settings.get('stop_on_error')
        
        script_count = len(scripts)
        
        util.show('\n\a\tRunning %s Scripts\t\a\n' % self.process.get_name())
        
        skip_scripts = []
        
        finished = False
        
        for inc in range(0, script_count):
        
            if util.get_env('VETALA_RUN') == 'True':
                if util.get_env('VETALA_STOP') == 'True':
                    break
            
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
                
                if stop_on_error:
                    break
                
            if status == 'Success':
                self.code_widget.set_process_script_state(scripts[inc], 1)
            
            if inc == script_count-1:
                finished = True
            
        util.set_env('VETALA_RUN', False)
        util.set_env('VETALA_STOP', False)
            
        self.process_button.setEnabled(True)
        self.stop_button.hide()
        
        seconds = watch.stop()
        
        if finished:
            util.show('Process %s built in %s' % (self.process.get_name(), seconds))
            
        if not finished:
            util.show('Process %s finished with errors.' % self.process.get_name())
        
    def _browser(self):
        
        if self.tab_widget.currentIndex() == 0:
            util_file.open_browser(self.directory)
            return
        
        directory = self._get_current_path()
        
        if not directory:
            
            directory = str(self.project_directory[1])
            
        if directory and self.tab_widget.currentIndex() == 1:
            util_file.open_browser(directory)
        if directory and self.tab_widget.currentIndex() == 2:
            path = self.process.get_data_path()
            util_file.open_browser(path)
        if directory and self.tab_widget.currentIndex() == 3:
            path = self.process.get_code_path()
            util_file.open_browser(path)   
            
    def _template_current_changed(self):
        
        self.settings_widget.refresh_template_list()        
        
    def set_directory(self, directory):
        
        self.directory = directory
        
        if not util_file.is_dir(directory):
            util_file.create_dir(name = None, directory = directory)
        
    def set_project_directory(self, directory, sub_part = None):
        
        if type(directory) != list:
            directory = ['', directory]
        
        self._clear_code()
        
        if not directory:
            self.process.set_directory(None)
            self.view_widget.set_directory(None)
            return

        if not sub_part:
            self.project_directory = directory
            self.view_widget.clear_sub_path_filter()
            directory = str(directory[1])
            
        if sub_part:
            directory = sub_part
            
        self.process.set_directory(directory)
        self.view_widget.set_directory(directory)
        
        self.option_widget.set_directory(directory)
        self.process_splitter.setSizes([1,0])
        
    def set_template_directory(self, directory = None):
        
        if not self.template_settings:
            if not self.settings:
                return
        
        settings = self.settings
        
        if self.template_settings:
            settings = self.template_settings
        
        current = settings.get('template_directory')
        history = settings.get('template_history')
        
        if not current:
            if history:
                self.template_widget.set_templates(history)
            return
        
        current_name = None
        
        if not history:
            current_name = current
            history = [['', current]]
            
        self.template_widget.set_templates(history)
            
        if not current_name:
            for setting in history:
                if setting[1] == current:
                    current_name = setting[0]
        
        if not current_name:
            current_name = current
                    
        if current_name:
            
            self.template_widget.set_current(current_name)
        
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
                    