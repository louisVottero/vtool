# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

import sys

from vtool import qt_ui, qt, maya_lib

from vtool import util_file
from vtool import util

import process
import ui_view
import ui_options
import ui_templates
import ui_process_settings
import ui_data
import ui_code
import ui_settings
import os
        

vetala_version = util_file.get_vetala_version()

class ProcessManagerWindow(qt_ui.BasicWindow):
    
    title = 'VETALA'
    
    def __init__(self, parent = None):
        
        util.show('VETALA_PATH: %s' % util.get_env('VETALA_PATH'))
        
        self.directory = None
        self._current_tab = None
        
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
        self.last_project = None
        self.sync_code = False
        self.kill_process = False
        self.build_widget = None
        self.last_item = None
        self.runtime_values = {}
        self.handle_selection_change = True
        
        super(ProcessManagerWindow, self).__init__(parent = parent, use_scroll = True) 
        
        icon = qt_ui.get_icon('vetala.png')
        self.setWindowIcon(icon)
        
        
        shortcut = qt.QShortcut(qt.QKeySequence(qt.QtCore.Qt.Key_Escape), self)
        shortcut.activated.connect(self._set_kill_process)
            
        self.view_widget.tree_widget.itemChanged.connect(self._item_changed)
        self.view_widget.tree_widget.item_renamed.connect(self._item_renamed)
        
        self.view_widget.tree_widget.itemSelectionChanged.connect(self._item_selection_changed)
        self.view_widget.copy_done.connect(self._copy_done)
        self.view_widget.tree_widget.itemDoubleClicked.connect(self._item_double_clicked)
        self.view_widget.tree_widget.show_options.connect(self._show_options)
        self.view_widget.tree_widget.show_notes.connect(self._show_notes)
        self.view_widget.tree_widget.show_templates.connect(self._show_templates)
        self.view_widget.tree_widget.show_settings.connect(self._show_settings)
        self.view_widget.tree_widget.process_deleted.connect(self._process_deleted)
        
        
        self._set_default_directory()
        self._setup_settings_file()
        
        self._set_default_project_directory()
        self._set_default_template_directory()
        
        if self.settings.has_setting('process_split_alignment'):
            alignment = self.settings.get('process_split_alignment')
        
            if alignment:
                if alignment == 'horizontal':
                    self.process_splitter.setOrientation(qt.QtCore.Qt.Horizontal)
                    
                if alignment == 'vertical':
                    self.process_splitter.setOrientation(qt.QtCore.Qt.Vertical)
                
        code_directory = self.settings.get('code_directory')
        if code_directory:
            self.set_code_directory(code_directory)
        
        self.last_process_script_inc = 0
        
    def _show_options(self):
        
        sizes = self.process_splitter.sizes()
        self._load_options(self.process.get_path())
        
        current_index = self.option_tabs.currentIndex()
        
        if current_index != 0:
            self.option_tabs.setCurrentIndex(0)
        
        if sizes[1] == 0:
            self.process_splitter.setSizes([1,1])
        
        if current_index == 0 and sizes[1] > 0:
            self.process_splitter.setSizes([1,0])
            self._current_tab = None
            return
        
        self._current_tab = 0
        
    def _show_notes(self):
        sizes = self.process_splitter.sizes()
        self._load_notes()
        
        current_index = self.option_tabs.currentIndex()
        
        if current_index != 1:
            self.option_tabs.setCurrentIndex(1)
        
        if sizes[1] == 0:
            self.process_splitter.setSizes([1,1])
        
        if current_index == 1 and sizes[1] > 0:
            self.process_splitter.setSizes([1,0])
            self._current_tab = None
            return
        
        self._current_tab = 1
        
    def _show_templates(self):
        
        self.process_splitter.setSizes([1,1])
        self.option_tabs.setCurrentIndex(2)
    
    def _show_settings(self):
        
        self.process_splitter.setSizes([1,1])
        self.option_tabs.setCurrentIndex(3)
        
    def _process_deleted(self):
        self._clear_code(close_windows=True)
        self._clear_data()
        
        self._set_title('-')
        
        self.build_widget.hide()
        
    def _copy_done(self):
        self.sync_code = True
        
        self._load_options(self.process.get_path())
        self._load_notes()
          
    def _item_double_clicked(self):
        
        pass
        #self.tab_widget.setCurrentIndex(3)
                
    def _item_changed(self, item):
        
        name = '-'
        
        if hasattr(item, 'name'):
            
            name = item.get_name()
        
        self._set_title(name)
        
        self._update_build_widget(name)
        
        #if hasattr(item, 'get_path'):
        #    self._load_options(item.get_path())
        
    def _item_renamed(self, item):
        
        self._item_changed(item)
        
        if hasattr(item, 'get_path'):
            self._load_options(item.get_path())
            self._load_notes()
        
    def _item_selection_changed(self):
        
        if not self.handle_selection_change:
            return
        
        items = self.view_widget.tree_widget.selectedItems()
                
        if not items:
            
            self._update_process(None)
            self.build_widget.hide()
            return
        
        item = items[0]
        
        if item.matches(self.last_item):
            return
        
        name = item.get_name()
        
        self._update_build_widget(name)

        #self._set_title(name)
        self._update_process(name)
        
        
        path = item.get_path()
        
        if self.option_tabs.currentIndex() == 0:
            self._load_options(path)
        if self.option_tabs.currentIndex() == 1:
            self._load_notes()
        if self.option_tabs.currentIndex() == 3:
            self._load_process_settings()
        
        self.view_widget.setFocus()
        
    def _load_options(self, directory):
        self.option_widget.set_directory(directory)
        
        has_options = self.option_widget.has_options()
        
        if self.option_tabs.currentIndex() == 1:
            note_lines = self._get_note_lines()
            
            if not note_lines and has_options and self._current_tab == None:
                self.option_tabs.setCurrentIndex(0)
        
        if self.option_tabs.currentIndex() == 0:
            has_options = self.option_widget.has_options()
            
            if has_options:
                self.process_splitter.setSizes([1,1])
            if not has_options and self._current_tab == None:
                self.process_splitter.setSizes([1,0])
            return
        
    def _get_note_lines(self):
        
        current_path = self._get_current_path()
        
        notes_path = util_file.join_path(current_path, 'notes.html')
        
        if util_file.is_file(notes_path):
            note_lines = util_file.get_file_text(notes_path)
            
            parser = util.VetalaHTMLParser()
            parser.feed(note_lines)
            if not parser.get_body_data():
                return
            
            return note_lines

            
    def _load_notes(self):
        
        note_lines = self._get_note_lines()
        
        if not note_lines:
            
            self.notes.clear()
            

        if note_lines:
            
            self.notes.clear()
            
            self.notes.setHtml(note_lines)
            self._save_notes()
                
        if self.option_tabs.currentIndex() == 1:
            if not note_lines and self._current_tab == None:
                self.process_splitter.setSizes([1,0])
            if note_lines:
                self.process_splitter.setSizes([1,1])
                
        if self.option_tabs.currentIndex() == 0:
            has_options = self.option_widget.has_options()
            
            if not has_options and self._current_tab == None:
                
                if note_lines:
                    self.option_tabs.setCurrentIndex(1)
                    self.process_splitter.setSizes([1,1])
    
    def _load_process_settings(self):
        
        self.process_settings.set_directory(self._get_current_path())
        
              
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
        return qt.QtCore.QSize(450,450)
        
    def _setup_settings_file(self):
        
        settings_file = util_file.SettingsFile()
        
        settings_file.set_directory(self.directory)
        
        self.settings = settings_file
        
        util.set_env('VETALA_SETTINGS', self.directory)
        
        self.view_widget.set_settings( self.settings )
        self.settings_widget.set_settings(self.settings)
        
        #template stuff
        vetala_path = util_file.get_vetala_directory()
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
                self.settings.set('template_history', [['Vetala Templates', vetala_path]])
        
        self.settings_widget.set_template_settings(settings)
        self.template_widget.set_settings(settings)
        
    def _build_widgets(self):
        
        self.header_layout = qt.QHBoxLayout()
        
        self.active_title = qt.QLabel('-')
        self.active_title.setAlignment(qt.QtCore.Qt.AlignCenter)
        
        self.header_layout.addWidget(self.active_title, alignment = qt.QtCore.Qt.AlignCenter)
        
        self.tab_widget = qt.QTabWidget()
        self.tab_widget.currentChanged.connect(self._tab_changed)
        
        self.view_widget = ui_view.ViewProcessWidget()
        
        self.option_tabs = qt.QTabWidget()
        
        option_layout = qt.QVBoxLayout()
        option_layout.setContentsMargins(1,1,1,1)
        self.option_widget = ui_options.ProcessOptionsWidget()
        
        
        option_layout.addWidget(self.option_widget)
        #self.option_widget.toggle_alignment.connect(self._toggle_alignment)
        
        option_widget = qt.QWidget()
        option_widget.setLayout(option_layout)
        
        self.template_widget = ui_templates.TemplateWidget()
        self.template_widget.set_active(False)
        self.template_widget.current_changed.connect(self._template_current_changed)
        self.template_widget.add_template.connect(self._add_template)
        self.template_widget.merge_template.connect(self._merge_template)
        self.template_widget.match_template.connect(self._match_template)
        
        self.notes = NoteText()
        
        self.notes.textChanged.connect(self._save_notes)
        
        self.process_settings = ui_process_settings.ProcessSettings()
        
        self.option_tabs.addTab(option_widget, 'Options')
        self.option_tabs.addTab(self.notes, 'Notes')
        self.option_tabs.addTab(self.template_widget, 'Templates')
        self.option_tabs.addTab(self.process_settings, 'Settings')
        self.option_tabs.setCurrentIndex(1)
        
        self.option_tabs.currentChanged.connect(self._option_changed)
        
        splitter_button_layout = qt.QHBoxLayout()
        
        full_button = qt.QPushButton('Full')
        full_button.setMaximumHeight(18)
        full_button.setMaximumWidth(60)
        full_button.setSizePolicy(qt.QSizePolicy(qt.QSizePolicy.Minimum,qt.QSizePolicy.Minimum,))
        full_button.clicked.connect(self._toggle_full)
        
        close_button = qt.QPushButton('Close')
        close_button.setMaximumHeight(18)
        close_button.setMaximumWidth(60)
        close_button.setSizePolicy(qt.QSizePolicy(qt.QSizePolicy.Minimum,qt.QSizePolicy.Minimum,))
        close_button.clicked.connect(self._close_tabs)
        
        self.full_button = full_button
        self.close_button = close_button
        
        orientation_button = qt.QPushButton('Alignment')
        orientation_button.setMaximumHeight(18)
        orientation_button.clicked.connect(self._toggle_alignment)
        orientation_button.setSizePolicy(qt.QSizePolicy(qt.QSizePolicy.Minimum,qt.QSizePolicy.Maximum,))
        
        splitter_button_layout.addWidget(full_button)
        splitter_button_layout.addWidget(orientation_button)
        splitter_button_layout.addWidget(close_button)
        
        
        btm_tab_widget = qt_ui.BasicWidget()
        btm_tab_widget.main_layout.addLayout(splitter_button_layout)
        btm_tab_widget.main_layout.addWidget(self.option_tabs)
        
        self.data_widget = ui_data.DataProcessWidget()
        
        self.code_widget = ui_code.CodeProcessWidget()
        self.settings_widget = ui_settings.SettingsWidget()
        self.settings_widget.project_directory_changed.connect(self.set_project_directory)
        self.settings_widget.code_directory_changed.connect(self.set_code_directory)
        self.settings_widget.template_directory_changed.connect(self.set_template_directory)
        
        #splitter stuff
        self.process_splitter = qt.QSplitter()
        self.process_splitter.setOrientation(qt.QtCore.Qt.Vertical)
        
        
        
        self.process_splitter.setContentsMargins(1,1,1,1)
        self.process_splitter.addWidget(self.view_widget)
        
        self.process_splitter.addWidget(btm_tab_widget)
        #self.process_splitter.addWidget(self.option_tabs)
        self.process_splitter.setSizes([1,0])
        
        settings_icon = qt_ui.get_icon('gear.png')
        
        if util.is_in_maya():
            self.tab_widget.addTab(self.settings_widget, settings_icon, '')
        else:
            self.tab_widget.addTab(self.settings_widget, 'Settings')
            
        self.tab_widget.addTab(self.process_splitter, 'View')
        self.tab_widget.addTab(self.data_widget, 'Data')
        self.tab_widget.addTab(self.code_widget, 'Code')
        
        
        self.tab_widget.setTabEnabled(2, False)
        self.tab_widget.setTabEnabled(3, False)
        self.tab_widget.setCurrentIndex(1)
        
        self.main_layout.addSpacing(4)
        self.main_layout.addLayout(self.header_layout)
        
        self.main_layout.addSpacing(4)
        self.main_layout.addWidget( self.tab_widget )
        
        left_button_layout = qt.QHBoxLayout()
        right_button_layout = qt.QHBoxLayout()
        
        self.process_button = qt.QPushButton('PROCESS')
        self.process_button.setDisabled(True)
        self.process_button.setMinimumWidth(140)
        self.process_button.setMinimumHeight(30)
            
        self.batch_button = qt.QPushButton('BATCH')
        self.batch_button.setDisabled(True)
        self.batch_button.setMinimumHeight(30)
        self.batch_button.setMinimumWidth(70)
        
        self.stop_button = qt.QPushButton('STOP (Hold Esc)')
        self.stop_button.setMaximumWidth(110)
        self.stop_button.setMinimumHeight(30)
        self.stop_button.hide()
        
        self.continue_button = qt.QPushButton('CONTINUE')
        self.continue_button.setMaximumWidth(120)
        self.continue_button.setMinimumHeight(30)
        self.continue_button.hide()
        
        self.browser_button = qt.QPushButton('Browse')
        self.browser_button.setMaximumWidth(70)
        help_button = qt.QPushButton('?')
        help_button.setMaximumWidth(20)
        
        btm_layout = qt.QVBoxLayout()
        
        button_layout = qt.QHBoxLayout()
        
        left_button_layout.setAlignment(qt.QtCore.Qt.AlignLeft)
        left_button_layout.addWidget(self.process_button)
        
        left_button_layout.addSpacing(10)
        left_button_layout.addWidget(self.stop_button)
        left_button_layout.addWidget(self.continue_button)
        
        left_button_layout.addSpacing(10)
        
        right_button_layout.setAlignment(qt.QtCore.Qt.AlignLeft)
        
        right_button_layout.addWidget(self.batch_button)
        right_button_layout.addSpacing(5)
        right_button_layout.addWidget(self.browser_button)
        right_button_layout.addWidget(help_button)
        
        button_layout.addLayout(left_button_layout)
        
        button_layout.addLayout(right_button_layout)
        
        self.build_widget = ui_data.ProcessBuildDataWidget()
        self.build_widget.hide()
        
        btm_layout.addLayout(button_layout)
        btm_layout.addSpacing(5)
        btm_layout.addWidget(self.build_widget, alignment = qt.QtCore.Qt.AlignBottom)
        
        self.browser_button.clicked.connect(self._browser)
        self.process_button.clicked.connect(self._process)
        self.batch_button.clicked.connect(self._batch)
        help_button.clicked.connect(self._open_help)
        self.stop_button.clicked.connect(self._set_kill_process)
        self.continue_button.clicked.connect(self._continue)
        
        self.main_layout.addLayout(btm_layout)
        
        self.build_widget.setSizePolicy(qt.QSizePolicy.Minimum, qt.QSizePolicy.Minimum)
        
    def _toggle_alignment(self):
        
        orientation = self.process_splitter.orientation()
        
        if orientation == qt.QtCore.Qt.Horizontal:
            self.process_splitter.setOrientation(qt.QtCore.Qt.Vertical)
            self.settings.set('process_split_alignment', 'vertical')
        
        if orientation == qt.QtCore.Qt.Vertical:
            self.process_splitter.setOrientation(qt.QtCore.Qt.Horizontal)
            self.settings.set('process_split_alignment', 'horizontal')
            
    def _toggle_full(self):
        
        sizes = self.process_splitter.sizes()
        
        if sizes[0] == 0 and sizes[1] > 0:
            self.process_splitter.setSizes([1,1])
            
        if sizes[0] > 1 and sizes[1] >= 0:
            self.process_splitter.setSizes([0,1])
        
    
    def _close_tabs(self):
        
        self.process_splitter.setSizes([1, 0])

        
        
    def _add_template(self, process_name, directory):
        
        source_process = process.Process(process_name)
        source_process.set_directory(directory)
        
        self.view_widget.tree_widget.paste_process(source_process)
        
    def _merge_template(self, process_name, directory):
        
        source_process = process.Process(process_name)
        source_process.set_directory(directory)
        
        self.view_widget.tree_widget.merge_process(source_process)
        
    def _match_template(self, process_name, directory):
        
        self.view_widget.manager_widget.copy_match(process_name, directory)
        
    def _option_changed(self):
        
        if self.option_tabs.currentIndex() == 0:
            self.template_widget.set_active(False)
            self.process_settings.set_active(False)
            self._current_tab = 0
            self._load_options(self._get_current_path())
        
        if self.option_tabs.currentIndex() == 1:
            self.template_widget.set_active(False)
            self.process_settings.set_active(False)
            self._current_tab = 1
            self._load_notes()
            
        if self.option_tabs.currentIndex() == 2:
            self.template_widget.set_active(True)
            self.process_settings.set_active(False)
            self._current_tab = None
        
        if self.option_tabs.currentIndex() == 3:
            
            self.template_widget.set_active(False)
            self.process_settings.set_active(True)
            self._current_tab = 3
            
            print self._get_current_path()
            
            self.process_settings.set_directory(self._get_current_path())
            
    def _clear_code(self, close_windows = False):
        
        self.code_widget.close_widgets(close_windows)
        
    def _clear_data(self):
        
        self.data_widget.clear_data()
        
    def _update_process(self, name):
        
        self._set_vetala_current_process(name)
        
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
            self.batch_button.setEnabled(True)
        
        if not name:
            
            self._set_title('-')

            self.tab_widget.setTabEnabled(2, False)
            self.tab_widget.setTabEnabled(3, False)
            
            self.process_button.setDisabled(True)
            self.batch_button.setDisabled(True)
            
        self.last_process = name
        
    def _set_default_directory(self):
        default_directory = process.get_default_directory()
        
        self.set_directory(default_directory)
        
    def _set_default_project_directory(self):
        
        directory = self.settings.get('project_directory')
        
        if directory:
            if type(directory) != list:
                directory = ['', directory]
        
        if not directory:
            directory = ['default', util_file.join_path(self.directory, 'project')]
        
        self.settings_widget.set_project_directory(directory)
        
        self.set_project_directory(directory)
        self.set_directory(directory[1])
        
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
            
    def _set_vetala_current_process(self, name):
        
        if not name:
            self.active_title.setText('')
            util.set_env('VETALA_CURRENT_PROCESS', '')
            return
        
        if self.project_directory:
            self.settings.set('process', [name, str(self.project_directory)])
            
            fullpath = util_file.join_path(self.project_directory, name)
            
            util.set_env('VETALA_CURRENT_PROCESS', fullpath)    
            
    def _set_title(self, name = None):
        
        name = name.replace('/', '  /  ')
        
        self.active_title.setText(name)
        
    def _open_help(self):
        import webbrowser
        
        filename = __file__
        folder = util_file.get_dirname(filename)
        
        split_folder = folder.split('\\')
        folder = split_folder[:-1]
        
        path = 'http://docs.vetalarig.com'
        webbrowser.open(path, 0)
        
        
    def _tab_changed(self):
        
        if self.tab_widget.currentIndex() == 0:
            if self.build_widget:
                self.build_widget.hide()
                
            self.last_tab = 0
             
        if self.tab_widget.currentIndex() == 1:
            
            self.set_template_directory()
            self.last_tab = 1
            
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
        if not item:
            return self.directory
           
    def _set_kill_process(self):
        util.set_env('VETALA_STOP', True)
        self.kill_process = True
        
    def _auto_save(self):
        if not util.is_in_maya():
            return
        
        import maya.cmds as cmds
        
        filepath = cmds.file(q = True, sn = True)
        
        saved = maya_lib.core.save(filepath)
        
        return saved
        
    def _get_checked_children(self, tree_item):
        
        if not tree_item:
            return 
        
        expand_state = tree_item.isExpanded()
        
        tree_item.setExpanded(True)
        
        children = self.view_widget.tree_widget.get_tree_item_children(tree_item)
        
        checked_children = []
        
        for child in children:
            check_state = child.checkState(0)
                    
            if check_state == qt.QtCore.Qt.Checked:
                checked_children.append(child)
                
        levels = []
        if checked_children:
            levels.append(checked_children)
        
        while children:
            
            new_children = []
            checked_children = []
            
            for child in children:
                
                current_check_state = child.checkState(0)
                
                if current_check_state != qt.QtCore.Qt.Checked:
                    continue
                    
                child.setExpanded(True)
                
                sub_children = self.view_widget.tree_widget.get_tree_item_children(child)
                
                checked = []
                
                for sub_child in sub_children:
                    check_state = sub_child.checkState(0)
                    
                    if check_state == qt.QtCore.Qt.Checked:
                        checked.append(sub_child)
                        
                
                if sub_children:
                    new_children += sub_children
                    
                if checked:
                    checked_children += checked
                    
                    
            if not checked_children:
                children = []
                continue
            
            children = new_children
            
            if checked_children:
                levels.append(checked_children)
        
        tree_item.setExpanded(expand_state)
        
        levels.reverse()
        return levels
        
    def _process_item(self, item, comment):
        
        
        
        if util.is_in_maya():
            import maya.cmds as cmds
            cmds.file(new = True, f = True)
        
        process_inst = item.get_process()
        process_inst.run(start_new = True)
        
        
        
        if util.is_in_maya():
            import maya.cmds as cmds
            
            build_comment = 'auto built'
            
            if comment:
                build_comment = comment
            
            process_inst.save_data('build', build_comment)
        
    def _process(self, last_inc = None):
        
        if util.is_in_maya():
            import maya.cmds as cmds
            
            cmds.select(cl = True)
            
            if cmds.file(q = True, mf = True):
                
                filepath = cmds.file(q = True, sn = True)
                
                process_path = util.get_env('VETALA_CURRENT_PROCESS')
                filepath = util_file.remove_common_path_simple(process_path, filepath)
                
                result = qt_ui.get_permission('Continue?', self, cancel = False, title = 'Changes not saved.')
                
                if result == None or result == False:
                    return
                
            cmds.file(renameToSave = True)
        
        item = self.view_widget.tree_widget.currentItem()
        
        children_run_comment = ''
        
        if self.tab_widget.currentIndex() == 1:
            children = self._get_checked_children(item)
                    
            if children:
                
                result = qt_ui.get_comment(self, 'Found process children checked on:\n\nHit Ok to auto build children first.\n\nHit Cancel to process only the current process.\n\n\nAdd comment to the auto build? ', 'Children Checked', comment_text='Auto Build' )
                
                if result:
                    
                    children_run_comment = result
                    
                    util.set_env('VETALA_RUN', True)
                    util.set_env('VETALA_STOP', False)
                    
                    for level in children:
                        for level_item in level:
                            
                            if util.get_env('VETALA_RUN') == 'True':
                                if util.get_env('VETALA_STOP') == 'True':
                                    return
                                
                            self.view_widget.tree_widget.setCurrentItem(level_item)
                            self._process_item(level_item, comment = result)

                    if util.get_env('VETALA_RUN') == 'True':
                        if util.get_env('VETALA_STOP') == 'True':
                            return
                        
                if not result:
                    result2 = qt_ui.get_permission('Continue This Process?', self, title = 'Sub process build cancelled.')
                    
                    if not result2:
                        return
                    
                import time
                self.view_widget.tree_widget.setCurrentItem(item)
                self.view_widget.tree_widget.repaint()
                time.sleep(1)


                
        self.continue_button.hide()
        
        watch = util.StopWatch()
        watch.start(feedback = False)
                
        self.kill_process = False
                
        self.stop_button.show()
        
        self.process_button.setDisabled(True)
        self.batch_button.setDisabled(True)
        
        if last_inc == None:
            self.code_widget.reset_process_script_state()
            
            try:
                #this was not working when processing in a new Vetala session without going to the code tab.
                self.code_widget.refresh_manifest()
            except:
                pass
        
        self.tab_widget.setCurrentIndex(3)
        
        code_directory = self.settings.get('code_directory')
        self.process.set_external_code_library(code_directory)
        
        start_new_scene = self.settings.get('start_new_scene_on_process')
        
        if util.is_in_maya() and start_new_scene and last_inc == None:
            cmds.file(new = True, f = True)
        
        scripts, states = self.process.get_manifest()
        
        if not scripts:
            self.process_button.setEnabled(True)
            self.batch_button.setEnabled(True)
            return
        
        util.set_env('VETALA_RUN', True)
        util.set_env('VETALA_STOP', False)
        
        stop_on_error = self.settings.get('stop_on_error')
        
        script_count = len(scripts)
        
        util.show('\n\n\n\a\tRunning %s Scripts\t\a\n' % self.process.get_name())
        
        skip_scripts = []
        
        finished = False
        
        code_manifest_tree = self.code_widget.script_widget.code_manifest_tree
        
        start = 0
        
        if last_inc != None:
            start = last_inc + 1
            
        found_start = False
        
        progress_bar = None
        
        if util.is_in_maya():
            progress_bar = maya_lib.core.ProgressBar('Process', script_count)
            progress_bar.status('Processing: getting ready...')
        
        for inc in range(start, script_count):
            
            if util.get_env('VETALA_RUN') == 'True':
                if util.get_env('VETALA_STOP') == 'True':
                    if progress_bar:
                        progress_bar.end()
                    break
            
            script = scripts[inc]
            script_name = util_file.remove_extension(script)
            
            if progress_bar:
                
                progress_bar.status('Processing: %s' % script_name)
                
                if progress_bar.break_signaled():
                    self._set_kill_process()
            
            if self.kill_process:
                self.kill_process = False
                if progress_bar:
                    progress_bar.end()
                break
            
            skip = False
            
            if states:
                state = states[inc]
                
                if not state:
                    self.code_widget.set_process_script_state(scripts[inc], -1)
                    skip_scripts.append(script_name)
                    skip = True
            
            
            if not skip:
                #this checks if the current script is a child of a skipped scipt.
                for skip_script in skip_scripts:
                    common_path = util_file.get_common_path(script, skip_script)
                    if common_path == skip_script:
                        if script.startswith(skip_script):
                            skip = True
            
            
            
            if not skip:
                
                if code_manifest_tree.has_startpoint() and not found_start:
                    if not code_manifest_tree.is_process_script_startpoint(scripts[inc]):
                        found_start = True
                        if progress_bar:
                            progress_bar.inc()
                        continue
                    
                    
                self.code_widget.set_process_script_state(scripts[inc], 2)
                
                if progress_bar:
                
                    if progress_bar.break_signaled():
                        self._set_kill_process()
                
                status = self.process.run_script(script_name, False, self.settings.settings_dict)
                temp_log = util.get_env('VETALA_LAST_TEMP_LOG')
                
                self.code_widget.set_process_script_log(scripts[inc], temp_log)
                
                if not status == 'Success':
                    
                    self.code_widget.set_process_script_state(scripts[inc], 0)
                    
                    if stop_on_error:
                        if progress_bar:
                            progress_bar.end()
                        break
                    
                if status == 'Success':
                    self.code_widget.set_process_script_state(scripts[inc], 1)
                
                if inc == script_count-1:
                    finished = True
            
            if code_manifest_tree.break_index != None:
                if code_manifest_tree.is_process_script_breakpoint(scripts[inc]):
                    self.continue_button.show()
                    self.last_process_script_inc = inc
                    finished = True
                    if progress_bar:
                        progress_bar.end()
                    break
            
            if progress_bar:
                progress_bar.inc()
        
        progress_bar.end()
        
        util.set_env('VETALA_RUN', False)
        util.set_env('VETALA_STOP', False)
            
        self.process_button.setEnabled(True)
        self.batch_button.setEnabled(True)
        self.stop_button.hide()
        
        minutes, seconds = watch.stop()
        
        if finished:
            if minutes == None:
                util.show('Process %s built in %s seconds\n\n' % (self.process.get_name(), seconds))
            if minutes != None:
                util.show('Process %s built in %s minutes, %s seconds\n\n' % (self.process.get_name(), minutes,seconds))
        if not finished:
            util.show('Process %s finished with errors.\n' % self.process.get_name())
    
    def _continue(self):
        
        self._process(self.last_process_script_inc)
        
    def _batch(self):
        
        dirpath = None
        
        if util.is_in_maya():
            dirpath = os.environ['MAYA_LOCATION']
        
        if not dirpath:
            util.warning('Could not find Maya.')
            
        import subprocess
        
        filepath = __file__
        filepath = util_file.get_dirname(filepath)
        
        batch_python = util_file.join_path(filepath, 'batch.py')
        
        mayapy = subprocess.Popen(['%s/bin/mayapy.exe' % dirpath, batch_python], shell = False)
        
        
    def _browser(self):
        
        if self.tab_widget.currentIndex() == 0:
            util_file.open_browser(process.get_default_directory())
            return
        
        directory = self._get_current_path()
        
        if not directory:
            
            directory = str(self.project_directory)
            
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
        
    
    def _save_notes(self):
        current_path = self._get_current_path()
        notes_path = util_file.join_path(current_path, 'notes.html')
        notes_path = util_file.create_file(notes_path)
        
        util_file.write_replace(notes_path, self.notes.toHtml())
        
        self.process.set_setting('notes', '')
        
    def set_directory(self, directory):
        
        self.directory = directory
        
        if not util_file.is_dir(directory):
            util_file.create_dir(name = None, directory = directory)
        
    def set_project_directory(self, directory, sub_part = None):
        
        self.handle_selection_change = False
        
        self.view_widget.tree_widget.clearSelection()
        
        if type(directory) != list:
            directory = ['', str(directory)]
        
        if not directory:
        
            self.process.set_directory(None)
            self.view_widget.set_directory(None)
            self.handle_selection_change = True
            self.settings_widget.set_directory(None)
            return

        self.handle_selection_change = True

        if not sub_part:
            
            self.view_widget.clear_sub_path_filter()
            directory = str(directory[1])
        
        if sub_part:
            directory = sub_part
            
        if directory != self.last_project:
        
            self.project_directory = directory
        
            self.clear_stage()
            
            self.process.set_directory(self.project_directory)
            self.view_widget.set_directory(self.project_directory)
            self.process_settings.set_directory(self.project_directory)    
        
        self.last_project = directory
        
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
        """ 
        if not current_name:
            for setting in history:
                
                if setting[1] == current:
                    current_name = setting[0]
        """
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
    
    def clear_stage(self):
        
        self._clear_code()
        self.active_title.setText('-')
        self.process_splitter.setSizes([1,0])
        self.build_widget.hide()

class NoteText(qt.QTextEdit):
    
    def __init__(self):
        super(NoteText, self).__init__()
        
    def canInsertFromMimeData(self, source):
        
        urls = source.urls()
        
        for url in urls:
            try:
                path = url.path()
                path = path[1:]
                
                image = qt.QImage(path)
                
                if not image.isNull():
                    return True
                
            except:
                pass
        
        return super(NoteText, self).canInsertFromMimeData(source)
        
    def insertFromMimeData(self, source):
        urls = source.urls()
        
        for url in urls:
            #try:
            path = url.path()
            path = str(path[1:])
            
            image = qt.QImage(path)
            
            if image.isNull():
                continue
            
            cursor = self.textCursor()
            document = self.document()
            
            document.addResource(qt.QTextDocument.ImageResource, qt.QtCore.QUrl(path), image)
            cursor.insertImage(path)
            #except:
            #    util.show('Could not paste image')
            
        super(NoteText, self).insertFromMimeData(source)