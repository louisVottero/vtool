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
import ui_process_maintenance
import ui_data
import ui_code
import ui_settings

from functools import wraps

in_maya = False

if util.is_in_maya():
    in_maya = True
    import maya.cmds as cmds

from vtool import logger
log = logger.get_logger(__name__) 

vetala_version = util_file.get_vetala_version()

def decorator_process_run(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        
        args[0].continue_button.hide()
        
        
        #before        
        args[0].kill_process = False
                
        args[0].stop_button.show()
        
        args[0].process_button.setDisabled(True)
        args[0].batch_button.setDisabled(True)
        
        #process function
        try:
            return_value = function(*args, **kwargs)
        except:
            pass
        
        #after
        util.set_env('VETALA_RUN', False)
        util.set_env('VETALA_STOP', False)
        
        args[0].process_button.setEnabled(True)
        args[0].batch_button.setEnabled(True)
        args[0].stop_button.hide()
        
        return return_value
    return wrapper


class ProcessManagerWindow(qt_ui.BasicWindow):
    
    title = util.get_custom('vetala_name', 'VETALA')
    
    def __init__(self, parent = None, load_settings = True):
        
        log.info('initialize %s' % self.__class__.__name__)
        
        util.show('VETALA_PATH: %s' % util.get_env('VETALA_PATH'))
        
        self._is_inside_process = False
        
        self.directory = None
        self._current_tab = None
        
        self.settings = None
        self.process_history_dict = {}
        self._path_filter = ''
        
        self._process_runtime_values = {}
        
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
        self.kill_process = False
        self.build_widget = None
        self.last_item = None
        
        self.handle_selection_change = True
        self._note_text_change_save = True
        
        super(ProcessManagerWindow, self).__init__(parent = parent, use_scroll = False) 
        
        icon = qt_ui.get_icon('vetala.png')
        self.setWindowIcon(icon)
        
        shortcut = qt.QShortcut(qt.QKeySequence(qt.QtCore.Qt.Key_Escape), self)
        shortcut.activated.connect(self._set_kill_process)
        
        if load_settings:
            self.initialize_settings()
        
        log.info('end initialize %s' % self.__class__.__name__)

    def _build_widgets(self):
        
        log.info('build widgets')
                
        self.header_layout = qt.QHBoxLayout()
        
        self.progress_bar = qt.QProgressBar()
        self.progress_bar.hide()
        self.progress_bar.setMaximumHeight(12)
        
        self.info_title = qt.QLabel('')
        self.info_title.hide()
        #self.info_title.setAlignment(qt.QtCore.Qt.AlignLeft)
        self.info_title.setSizePolicy(qt.QSizePolicy.Minimum, qt.QSizePolicy.Minimum)
        
        self.active_title = qt.QLabel('-')
        self.active_title.setAlignment(qt.QtCore.Qt.AlignCenter)
        
        self.header_layout.addWidget(self.progress_bar, alignment = qt.QtCore.Qt.AlignLeft)
        self.header_layout.addWidget(self.active_title, alignment = qt.QtCore.Qt.AlignCenter)
        self.header_layout.addWidget(self.info_title, alignment = qt.QtCore.Qt.AlignRight)
        
        self.tab_widget = qt.QTabWidget()
        
        self.view_widget = ui_view.ViewProcessWidget()
        
        self.view_widget.tree_widget.progress_bar = self.progress_bar
        
        self.option_tabs = qt.QTabWidget()
        
        option_layout = qt.QVBoxLayout()
        option_layout.setContentsMargins(0,0,0,0)
        self.option_widget = ui_options.ProcessOptionsWidget()
        
        
        option_layout.addWidget(self.option_widget)
        
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
        self.process_maintenance = ui_process_maintenance.ProcessMaintenance()
        
        self.option_tabs.addTab(option_widget, 'Options')
        self.option_tabs.addTab(self.notes, 'Notes')
        self.option_tabs.addTab(self.template_widget, 'Templates')
        self.option_tabs.addTab(self.process_settings, 'Settings')
        self.option_tabs.addTab(self.process_maintenance, 'Maintenance')
        self.option_tabs.setCurrentIndex(1)
        
        self.option_tabs.currentChanged.connect(self._option_changed)
        
        splitter_button_layout = qt.QHBoxLayout()
        
        full_button = qt.QPushButton('Full')
        full_button.setMaximumHeight(18)
        full_button.setMaximumWidth(60)
        full_button.setSizePolicy(qt.QSizePolicy(qt.QSizePolicy.Minimum,qt.QSizePolicy.Minimum))
        full_button.clicked.connect(self._toggle_full)
        
        close_button = qt.QPushButton('Close')
        close_button.setMaximumHeight(18)
        close_button.setMaximumWidth(60)
        close_button.setSizePolicy(qt.QSizePolicy(qt.QSizePolicy.Minimum,qt.QSizePolicy.Minimum))
        close_button.clicked.connect(self._close_tabs)
        
        self.full_button = full_button
        self.close_button = close_button
        
        orientation_button = qt.QPushButton('Alignment')
        orientation_button.setMaximumHeight(18)
        orientation_button.clicked.connect(self._toggle_alignment)
        orientation_button.setSizePolicy(qt.QSizePolicy(qt.QSizePolicy.Minimum,qt.QSizePolicy.Maximum))
        
        splitter_button_layout.addWidget(full_button)
        splitter_button_layout.addWidget(orientation_button)
        splitter_button_layout.addWidget(close_button)
        
        
        btm_tab_widget = SideTabWidget()
        btm_tab_widget.main_layout.addLayout(splitter_button_layout)
        btm_tab_widget.main_layout.addWidget(self.option_tabs)

        
        self.data_widget = ui_data.DataProcessWidget()
        
        self.code_widget = ui_code.CodeProcessWidget()
        self.settings_widget = ui_settings.SettingsWidget()
        self.settings_widget.project_directory_changed.connect(self.set_project_directory)
        self.settings_widget.code_directory_changed.connect(self.set_code_directory)
        self.settings_widget.template_directory_changed.connect(self.set_template_directory)
        self.settings_widget.code_text_size_changed.connect(self.code_widget.code_text_size_changed)
        
        #splitter stuff
        self.process_splitter = qt.QSplitter()
        self.process_splitter.setOrientation(qt.QtCore.Qt.Vertical)
                
        self.process_splitter.setContentsMargins(0,0,0,0)
        self.process_splitter.addWidget(self.view_widget)
        
        self.process_splitter.addWidget(btm_tab_widget)
        self.process_splitter.setSizes([1,0])
                
        if in_maya:
            settings_icon = qt_ui.get_icon('gear.png')
        else:
            settings_icon = qt_ui.get_icon('gear2.png')
            
        self.tab_widget.addTab(self.settings_widget, settings_icon, '')
        
            
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
        
        self.bottom_widget = qt_ui.BasicWidget()
        
        left_button_layout = qt.QHBoxLayout()
        right_button_layout = qt.QHBoxLayout()
        
        self.process_button = qt_ui.BasicButton('PROCESS')
        self.process_button.setWhatsThis("Process button\n\n"
                                         "This button runs the current process' code recipe defined in the code tab.\n"
                                         "You can hit ESC multiple times to stop the process after it starts.\n"
                                         "Somtimes holding ESC works better.\n"
                                         "Use the build widget below to save the process after it finishes.")
        #self.process_button = qt.QPushButton('PROCESS')
        self.process_button.setDisabled(True)
        self.process_button.setMinimumWidth(140)
        self.process_button.setMinimumHeight(30)
        
        
        self.batch_button = qt_ui.BasicButton('BATCH')
        self.batch_button.setWhatsThis('Batch button \n\n'
                                        'This will do the same as the Process button, but it will run it in Maya Batch mode.')
        self.batch_button.setDisabled(True)
        self.batch_button.setMinimumHeight(30)
        self.batch_button.setMinimumWidth(70)
        
        self.deadline_button = qt.QPushButton('DEADLINE')
        self.deadline_button.setDisabled(True)
        self.deadline_button.setMinimumHeight(30)
        self.deadline_button.setMinimumWidth(70)
        self.deadline_button.setHidden(True)
        
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
        right_button_layout.addWidget(self.deadline_button)
        right_button_layout.addSpacing(5)
        right_button_layout.addWidget(self.browser_button)
        right_button_layout.addWidget(help_button)
        
        button_layout.addLayout(left_button_layout)
        
        button_layout.addLayout(right_button_layout)
        
        self.bottom_widget.main_layout.addLayout((button_layout))
        
        self.build_widget = ui_data.ProcessBuildDataWidget()
        self.build_widget.hide()
        
        btm_layout.addWidget(self.bottom_widget)
        btm_layout.addSpacing(1)
        btm_layout.addWidget(self.build_widget, alignment = qt.QtCore.Qt.AlignBottom)
        
        self.tab_widget.currentChanged.connect(self._tab_changed)
        
        self.browser_button.clicked.connect(self._browser)
        self.process_button.clicked.connect(self._process)
        self.batch_button.clicked.connect(self._batch)
        self.deadline_button.clicked.connect(self._deadline)
        help_button.clicked.connect(self._open_help)
        self.stop_button.clicked.connect(self._set_kill_process)
        self.continue_button.clicked.connect(self._continue)
        
        self.main_layout.addLayout(btm_layout)
        
        self.build_widget.setSizePolicy(qt.QSizePolicy.Minimum, qt.QSizePolicy.Minimum)
        
        
        self.view_widget.tree_widget.itemChanged.connect(self._item_changed)
        self.view_widget.tree_widget.item_renamed.connect(self._item_renamed)
        
        self.view_widget.tree_widget.itemSelectionChanged.connect(self._item_selection_changed)
        self.view_widget.copy_done.connect(self._copy_done)
        self.view_widget.tree_widget.itemDoubleClicked.connect(self._item_double_clicked)
        self.view_widget.tree_widget.show_options.connect(self._show_options)
        self.view_widget.tree_widget.show_notes.connect(self._show_notes)
        self.view_widget.tree_widget.show_templates.connect(self._show_templates)
        self.view_widget.tree_widget.show_settings.connect(self._show_settings)
        self.view_widget.tree_widget.show_maintenance.connect(self._show_maintenaince)
        self.view_widget.tree_widget.process_deleted.connect(self._process_deleted)
        self.view_widget.path_filter_change.connect(self._update_path_filter)
        
        
        log.info('end build widgets')
           
    def resizeEvent(self, event):
        log.info('Resize')
        super(ProcessManagerWindow, self).resizeEvent(event)
        
                
    def sizeHint(self):
        return qt.QtCore.QSize(550,600)
        
    def _setup_settings_file(self):
        
        log.info('Setup Vetala Settings')
        
        util.set_env('VETALA_SETTINGS', self.directory)
        
        settings_file = util_file.SettingsFile()
        settings_file.set_directory(self.directory)
        self.settings = settings_file       
        
        self.view_widget.set_settings( self.settings )
        self.settings_widget.set_settings(self.settings)
        
        self._load_templates_from_settings()
        self._load_splitter_settings()
        
    def _show_options(self):
        log.info('Show options')
        sizes = self.process_splitter.sizes()
        self._load_options()
        
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
        
        log.info('Show notes')
        
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
        log.info('Show templates')
        self.process_splitter.setSizes([1,1])
        self.option_tabs.setCurrentIndex(2)
    
    def _show_settings(self):
        log.info('Show settings')
        self.process_splitter.setSizes([1,1])
        self.option_tabs.setCurrentIndex(3)
        
    def _show_maintenaince(self):
        log.info('Show maintenaince')
        self.process_splitter.setSizes([1,1])
        self.option_tabs.setCurrentIndex(4)
        
    def _process_deleted(self):
        self._clear_code(close_windows=True)
        self._clear_data()
        
        self._set_title('-')
        
        self.build_widget.hide()
        
    def _copy_done(self):
        
        log.info('Finished copying process')
        
        path = self._get_current_path()
        self.code_widget.set_directory(path, sync_code = True)
        
        self._load_options()
        self._load_notes()
          
    def _item_double_clicked(self):
        
        pass
        #self.tab_widget.setCurrentIndex(3)
                
    def _item_changed(self, item):
        
        log.info('Process item changed')
        
    def _item_renamed(self, item):
        
        log.info('Process item renamed')
        
        self._update_process(item.get_name())
        
    def _close_tabs(self):
        self.process_splitter.setSizes([1, 0])
    
    def _close_item_ui_parts(self):
        log.info('Close item ui parts')
        #self._update_process(None)
        
        #self._update_sidebar_tabs()
        
        self.build_widget.hide()
        self._close_tabs()
        
        self.tab_widget.setTabEnabled(2, False)
        self.tab_widget.setTabEnabled(3, False)

    def _item_selection_changed(self):
        
        log.info('process selection changed')
        
        if not self.handle_selection_change:
            return
        
        items = self.view_widget.tree_widget.selectedItems()
                
        if not items:
            
            if self._is_inside_process:
                path = self._get_filtered_project_path(self._path_filter)
                self._update_process(util_file.get_basename(path), store_process = False)
            else:
                self._close_item_ui_parts()
            return
        
        item = items[0]
        
        if hasattr(item, 'matches'):
            if item.matches(self.last_item):
                return
        
        if hasattr(item, 'get_name'):
            name = item.get_name()
        
            self.build_widget.show()
            
            log.info('Selection changed %s' % name)
            
            self._update_process(name)
            
        self.view_widget.setFocus()
    
    def _update_process(self, name, store_process = True):
        
        if not self.process:
            self._update_build_widget()
            self._update_sidebar_tabs()
            self._update_tabs(False)
            return
        
        
        self._set_vetala_current_process(name, store_process)
        
        items = self.view_widget.tree_widget.selectedItems()
        
        title = '-'
        
        folder = None
        
        if items and name != None:
            title = items[0].get_name()
            folder = items[0].is_folder()
        
            if not title:
                title = name
        
        if folder:
            self._set_title(title)
            self._close_item_ui_parts()
            return
        
        util.show('Load process: %s' % name)
        
        if name:
            log.info('Update process name')
            self.process.load(name)  
            
            self._set_title(title)
            
            self.process_button.setEnabled(True)
            self.batch_button.setEnabled(True)
            if util_file.has_deadline():
                self.deadline_button.setVisible(True)
                self.deadline_button.setEnabled(True)
                
            self._update_tabs(True)
                
        if not name:
            log.info('Update process no name')
            self._set_title('-')

            self.tab_widget.setTabEnabled(2, False)
            self.tab_widget.setTabEnabled(3, False)
            
            self.process_button.setDisabled(True)
            self.batch_button.setDisabled(True)
            if util_file.has_deadline():
                self.deadline_button.setVisible(True)
                self.deadline_button.setDisabled(True)
        
            self._update_tabs(False)
        
        self._clear_code()
        self._clear_data()
        
        self._update_build_widget()
        self._update_sidebar_tabs()
        
        self.last_process = name 
        
    def _update_sidebar_tabs(self):
        
        log.info('Update sidebar')
        
        if self.option_tabs.currentIndex() == 0:
            self._load_options()
        if self.option_tabs.currentIndex() == 1:
            self._load_notes()
        if self.option_tabs.currentIndex() == 2:
            pass
        if self.option_tabs.currentIndex() == 3:
            self._load_process_settings()
        if self.option_tabs.currentIndex() == 4:
            self._load_process_maintenance()
           

       
         
    def _update_path_filter(self, path):
        
        self._is_inside_process = False
        
        log.info('Update path filter: %s' % path)
        self.info_title.setText('')
        self.info_title.hide()
        
        if not path:
            self._path_filter = None
            path = self._get_filtered_project_path(path)
            self.process.set_directory(path)
            self._update_sidebar_tabs()
            self._set_title()
            self.view_widget.tree_widget.top_is_process = False
            
            return
        
        sub_processes = not process.find_processes(path, return_also_non_process_list = False, stop_at_one = True)
        
        if not sub_processes:
            return
        
        self._path_filter = path
        
        path = self._get_filtered_project_path(path)
        
        self.process.set_directory(path)
        
        items = self.view_widget.tree_widget.selectedItems()
        
        if not items:
            
            self._is_inside_process = True
            self.info_title.show()
            self.info_title.setText('Note: The view is a child of the process')
            self._update_process(util_file.get_basename(path), store_process = False)
            
        self.view_widget.tree_widget.top_is_process = True
        
    def _update_build_widget(self):
        
        if self.build_widget.isHidden():
            return
        
        log.info('Update build file widget')
        
        path = self._get_current_path()
        data_path = util_file.join_path(path, '.data/build')
        
        data_dir = util_file.join_path(path, '.data')
        
        if not util_file.exists(data_dir):
            return
        
        self.build_widget.update_data(data_dir)
        
        self.build_widget.set_directory(data_path)
        
        log.info('Finished loading build file widget')

    def _update_tabs(self, active = True):
        if active:
            self.tab_widget.setTabEnabled(2, True)
            self.tab_widget.setTabEnabled(3, True)
        if not active:
            self.tab_widget.setTabEnabled(2, False)
            self.tab_widget.setTabEnabled(3, False)
            
        
            
    def _tab_changed(self):
        
        log.debug('Tab changed %s' % self.tab_widget.currentIndex())
        
        item = self.view_widget.tree_widget.currentItem()
        
        if self.tab_widget.currentIndex() == 0:
            if self.build_widget:
                self.build_widget.hide()
            
            self.process_button.hide()
            self.batch_button.hide()
            self.deadline_button.hide()
            
            self.last_tab = 0
             
        else:
            if self.build_widget and item:
                self.build_widget.show()
            
            self.process_button.show()
            self.batch_button.show()
            if util_file.has_deadline():
                self.deadline_button.show()
            
        if self.tab_widget.currentIndex() == 1:
                        
            if self.last_tab == 3:
                self._update_sidebar_tabs()
                
            
            self.set_template_directory()
            self.last_tab = 1
            
        if self.tab_widget.currentIndex() > 1:
            
            if self.process and self.tab_widget.currentIndex() == 2:
                path = self._get_current_path()
                self.data_widget.set_directory(path)
                
                self.last_tab = 2
                return
            
            if self.process and self.tab_widget.currentIndex() == 3:
                self._load_code_ui()
                self.last_tab = 3
                
                return
        
        self.last_tab = 1
        
    def _get_filtered_project_path(self, filter_value = None):
        
        if not filter_value:
            filter_value = self._path_filter
        
        if filter_value:
            path = util_file.join_path(self.project_directory, filter_value)
        else:
            path = self.project_directory
        
        if path.endswith('/'):
            path = path[:-1]
        
        return path
         
            
    def _set_vetala_current_process(self, name, store_process = True):
        
        log.info('Set current vetala process %s' % name)
        
        if not name:
            self.active_title.setText('-')
            
            if self.project_directory and store_process:
                self._set_project_setting('process', name )
                self.settings.set('process', [name, str(self.project_directory)])
            
            util.set_env('VETALA_CURRENT_PROCESS', '')
            #self.process = process.Process()
            return
        
        current_path = self._get_current_path()
        
        if self.project_directory:
            
            #this needs to happen first because it reloads the settings.  If not the settings are retained from whats loaded into the settings class
            if store_process:
                self._set_project_setting('process', name )
                self.settings.set('process', [name, str(self.project_directory)])
            
            if not util_file.get_permission(current_path):
                util.warning('Could not get permission for process: %s' % current_path)
            
            util.set_env('VETALA_CURRENT_PROCESS', current_path)
        
        
    def _initialize_project_settings(self):
        
        
        process.initialize_project_settings(self.project_directory, self.settings)
        
        
    
    def _get_project_setting(self, name):
        
        value = process.get_project_setting(name, self.project_directory, self.settings)
    
        return value
    
    def _set_project_setting(self, name, value):
        
        process.set_project_setting(name, value, self.project_directory, self.settings)

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
        
    def _load_options(self):
        
        log.info('Load options')
        
        current_path = self._get_current_path()
        
        self.option_widget.set_directory(current_path)
        
        has_options = self.option_widget.has_options()
        
        if self.option_tabs.currentIndex() == 1:
            note_lines = self._get_note_lines()
            
            if not note_lines and has_options and self._current_tab == None:
                self.option_tabs.setCurrentIndex(0)
        
        if self.option_tabs.currentIndex() == 0:
            has_options = self.option_widget.has_options()
            
            if has_options:
                sizes = self.process_splitter.sizes()
                
                open_size_x = 1
                open_size_y = 1
                
                if sizes[0] > 0:
                    open_size_x = sizes[0]
                if sizes[1] > 0:
                    open_size_y = sizes[1]
                
                self.process_splitter.setSizes([open_size_x,open_size_y])
            if not has_options and self._current_tab == None:
                self.process_splitter.setSizes([1,0])
            return
        
    def _load_notes(self):
        
        log.info('Load notes')
        
        self._note_text_change_save = False
        
        note_lines = self._get_note_lines()
        
        if not note_lines:
            
            self.notes.clear()
            

        if note_lines:
            
            self.notes.clear()
            
            self.notes.setHtml(note_lines)
            #self._save_notes()
                
        if self.option_tabs.currentIndex() == 1:
            if not note_lines and self._current_tab == None:
                
                path = self._get_current_path()
                if not path:
                    self._note_text_change_save = True
                    return
                
                #self.option_widget.set_directory(path)
                #has_options = self.option_widget.has_options()
                
                has_options = self.process.has_options()
                
                if has_options:
                    self.option_tabs.setCurrentIndex(0)
                    self.process_splitter.setSizes([1,1])
                    self._note_text_change_save = True
                    return
                else:
                    self.process_splitter.setSizes([1,0])
                
            if note_lines:
                self.process_splitter.setSizes([1,1])
                
                
        if self.option_tabs.currentIndex() == 0:
            has_options = self.option_widget.has_options()
            
            if not has_options and self._current_tab == None:
                
                if note_lines:
                    self.option_tabs.setCurrentIndex(1)
                    self.process_splitter.setSizes([1,1])
        
        self._note_text_change_save = True
        
    def _load_process_settings(self):
        
        log.info('Load process settings')
        
        self.process_settings.set_directory(self._get_current_path())
        
    def _load_process_maintenance(self):
        log.info('Load process maintenance')
        self.process_maintenance.set_directory(self._get_current_path())
        
    def _load_templates_from_settings(self):
        
        if not self.settings:
            return
        
        #vetala_path = util_file.get_vetala_directory()
        #vetala_path = util_file.join_path(vetala_path, 'templates')
        
        template_directory = util.get_custom('template_directory','')
        if template_directory:
        
            template_history = util.get_custom('template_history', [])
            
            if util_file.exists(template_directory):
            
                util.show('Using custom template directory: %s' % template_directory)
                
                self.settings.set('template_directory', template_directory)
                if template_history:
                    history_list = self.settings.get('template_history')
                    
                    if not history_list:
                        history_list = template_history
                    else:
                        for history in template_history:
                            if not history in history_list:
                                history_list.append(history)
                            
                    self.settings.set('template_history', history_list) 
        
        self.settings_widget.set_template_settings(self.settings)
        self.template_widget.set_settings(self.settings)
    
    def _load_splitter_settings(self):
        
        if not self.settings:
            return
        
        if self.settings.has_setting('process_split_alignment'):
            alignment = self.settings.get('process_split_alignment')
        
            if alignment:
                if alignment == 'horizontal':
                    self.process_splitter.setOrientation(qt.QtCore.Qt.Horizontal)
                    
                if alignment == 'vertical':
                    self.process_splitter.setOrientation(qt.QtCore.Qt.Vertical)
    
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
        
    def _is_splitter_open(self):
        
        sizes = self.process_splitter.sizes()
        
        if sizes[1] > 0:
            return True
        
        return False
        
    def _add_template(self, process_name, directory):
        
        source_process = process.Process(process_name)
        source_process.set_directory(directory)
        
        self.view_widget.tree_widget.paste_process(source_process)
        
    def _merge_template(self, process_name, directory):
        
        source_process = process.Process(process_name)
        source_process.set_directory(directory)
        
        self.view_widget.tree_widget.merge_process(source_process)
        
    def _match_template(self, process_name, directory):
                
        self.view_widget.copy_match(process_name, directory, show_others = False)
        
    def _option_changed(self):
        
        if self.option_tabs.currentIndex() == 0:
            self.template_widget.set_active(False)
            self.process_settings.set_active(False)
            self._current_tab = 0
            self._load_options()
        
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
            
            self._load_process_settings()
            
        if self.option_tabs.currentIndex() == 4:
            self.template_widget.set_active(False)
            self.process_settings.set_active(False)
            self._current_tab = 4
            
            self._load_process_maintenance()
            
    def _clear_code(self, close_windows = False):
        
        self.code_widget.close_widgets(close_windows)
        
    def _clear_data(self):
        
        self.data_widget.clear_data()

        
    def _set_default_directory(self):
        default_directory = process.get_default_directory()
        
        self.set_directory(default_directory)
        
    def _set_default_project_directory(self, directory = None):
        
        if not directory:
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
        
        
        directory = self.settings.get('template_directory')
        
        if directory == None:
            return
        
        if directory:
            if type(directory) != list:
                directory = ['',directory]
        
        self.settings_widget.set_template_directory(directory)
        
        self.set_template_directory(directory)

            
    def _set_title(self, name = None):
        
        if not name:
            self.active_title.setText('-')
            return
        
        name = name.replace('/', '  /  ')
        
        self.active_title.setText(name)
        
    def _open_help(self):
        
        filename = __file__
        folder = util_file.get_dirname(filename)
        
        split_folder = folder.split('\\')
        folder = split_folder[:-1]
        
        util_file.open_website('http://docs.vetalarig.com')
        
    def _load_code_ui(self):
        
        path = self._get_current_path()
        
        self.code_widget.set_directory(path, False)
        
        code_directory = self.settings.get('code_directory')
        self.code_widget.set_external_code_library(code_directory)
        
        self.code_widget.set_settings(self.settings)
        
    def _get_current_name(self):
        
        
        item = self.view_widget.tree_widget.currentItem()
        
        if not item:
            items = self.view_widget.tree_widget.selectedItems()
            if items:
                item = items[0]
            else:
                return
        
        if hasattr(item, 'get_name'):
            process_name = item.get_name()
        
            return process_name
        
    def _get_current_path(self):
        
        log.debug('Get current vetala process')
        
        process_name = self._get_current_name()
        
        if process_name:    
            process_name = self._get_current_name()
            
            filter_str = self.view_widget.filter_widget.get_sub_path_filter()
            
            directory = self.directory
            
            if filter_str:
                directory = util_file.join_path(self.directory, filter_str)
            
            directory = util_file.join_path(directory, process_name)
            
        if not process_name:
            
            filter_value = self.view_widget.filter_widget.get_sub_path_filter()
            
            if filter_value:
                directory = util_file.join_path(self.directory, filter_value)
            else:
                directory =self.directory
        
        return directory
           
    def _set_kill_process(self):
        util.set_env('VETALA_STOP', True)
        self.kill_process = True
        
    def _auto_save(self):
        if not in_maya:
            return
        
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
        
        process_inst = item.get_process()
        process_inst.run(start_new = True)
        
        if in_maya:
            
            build_comment = 'auto built'
            
            if comment:
                build_comment = comment
            
            process_inst.save_data('build', build_comment)
    
    @decorator_process_run    
    def _process(self, last_inc = None):
        
        code_directory = self.settings.get('code_directory')
        self.process.set_external_code_library(code_directory)
        self.process.set_runtime_dict(self._process_runtime_values)
        
        if in_maya:
            
            from vtool.maya_lib import core
            core.ProgressBar().end()
            
            if cmds.file(q = True, mf = True):
                
                filepath = cmds.file(q = True, sn = True)
                
                process_path = util.get_env('VETALA_CURRENT_PROCESS')
                filepath = util_file.remove_common_path_simple(process_path, filepath)
                
                result = qt_ui.get_permission('Continue?', self, cancel = False, title = 'Changes not saved.')
                
                if result == None or result == False:
                    return
                
            cmds.file(renameToSave = True)
        
        item = self.view_widget.tree_widget.currentItem()
        
        if self.tab_widget.currentIndex() == 1:
            self._process_children(item)
            
        watch = util.StopWatch()
        watch.start(feedback = False)

        has_last_inc = False
        if last_inc != None and last_inc != False:
            has_last_inc = True
        
        if not has_last_inc:
            self.code_widget.reset_process_script_state()
            
            try:
                #this was not working when processing in a new Vetala session without going to the code tab.
                self.code_widget.refresh_manifest()
            except:
                pass
        
        self.code_widget.save_code()
                
        self.tab_widget.setCurrentIndex(3)
        
        scripts, states = self.process.get_manifest()
        
        manage_node_editor_inst = None
        
        if util.is_in_maya():
            
            start_new_scene = self.settings.get('start_new_scene_on_process')
            
            manage_node_editor_inst = maya_lib.core.ManageNodeEditors()
            
            if start_new_scene and not has_last_inc:
                core.start_new_scene()
            
            manage_node_editor_inst.turn_off_add_new_nodes()
                
        util.set_env('VETALA_RUN', True)
        util.set_env('VETALA_STOP', False)
        
        stop_on_error = self.settings.get('stop_on_error')
        
        script_count = len(scripts)
        
        util.show('\n\n\n\a\tRunning %s Scripts\t\a\n' % self.process.get_name())
        
        skip_scripts = []
        
        code_manifest_tree = self.code_widget.script_widget.code_manifest_tree
        
        start = 0
        
        if has_last_inc:
            start = last_inc + 1
            
        found_start = False
        
        progress_bar = None
        
        if util.is_in_maya():
            progress_bar = maya_lib.core.ProgressBar('Process', script_count)
            progress_bar.status('Processing: getting ready...')
        
        errors = False
        
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
                if inc > 0:
                    if progress_bar.break_signaled():
                        util.show('Process: progress bar break signaled')
                        self._set_kill_process()
            
            if inc > 0:
                if self.kill_process:
                    self.kill_process = False
                    if progress_bar:
                        progress_bar.end()
                    util.show('Prcoess - stopped')
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
            
            if skip:
                util.show('Process skipping %s' % script_name)
            
            if not skip:
            
                #util.show('Process: %s' % script_name)
                
                if code_manifest_tree.has_startpoint() and not found_start:
                    
                    if not code_manifest_tree.is_process_script_startpoint(scripts[inc]):
                        
                        if progress_bar:
                            progress_bar.inc()
                        util.show('Skipping script %s, it is before the start.' % scripts[inc])
                        continue
                    else:
                        found_start = True
                    
                self.code_widget.set_process_script_state(scripts[inc], 2)
                
                if inc > 0:
                    if progress_bar:
                    
                        if progress_bar.break_signaled():
                            util.show('Process: progress bar break signalled.')
                            self._set_kill_process()
                
                if in_maya:
                    cmds.select(cl = True)
                    core.auto_focus_view()
                
                status = self.process.run_script(script_name, False, self.settings.settings_dict)
                
                self._process_runtime_values = self.process.runtime_values
                self.code_widget.script_widget.code_manifest_tree.set_process_runtime_dict(self.process.runtime_values)
                
                temp_log = util.get_last_temp_log()
                
                self.code_widget.set_process_script_log(scripts[inc], temp_log)
                
                if not status == 'Success':
                    
                    errors = True
                    
                    self.code_widget.set_process_script_state(scripts[inc], 0)
                    
                    if stop_on_error:
                        if progress_bar:
                            progress_bar.end()
                        util.show('Prcoess - stopped on error')                            
                        break
                    
                if status == 'Success':
                    self.code_widget.set_process_script_state(scripts[inc], 1)
                                
                if temp_log.find('Warning!') > -1:
                    self.code_widget.set_process_script_state(scripts[inc], 3)
                
            
            if code_manifest_tree.break_index != None:
                if code_manifest_tree.is_process_script_breakpoint(scripts[inc]):
                    self.continue_button.show()
                    self.last_process_script_inc = inc
                    
                    if progress_bar:
                        progress_bar.end()
                    break
            
            if progress_bar:
                progress_bar.inc()
        
        if progress_bar:
            progress_bar.end()
        
        if manage_node_editor_inst:
            manage_node_editor_inst.restore_add_new_nodes()
        
        minutes, seconds = watch.stop()
        
        if minutes == None:
            util.show('Process %s built in %s seconds\n\n' % (self.process.get_name(), seconds))
        if minutes != None:
            util.show('Process %s built in %s minutes, %s seconds\n\n' % (self.process.get_name(), minutes,seconds))
        
        if errors:
            util.show('Process %s finished with errors.\n' % self.process.get_name())
    
    def _process_children(self, item):
        
        children = self._get_checked_children(item)
                    
        if children:
            
            result = qt_ui.get_comment(self, 'Found process children checked on:\n\nHit Ok to auto build children first.\n\nHit Cancel to process only the current process.\n\n\nAdd comment to the auto build? ', 'Children Checked', comment_text='Auto Build' )
            
            if result:
                
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
    
    def _continue(self):
        
        self._process(self.last_process_script_inc)
        
    def _batch(self):
        
        self.process.run_batch()
        
    def _deadline(self):
        
        self.process.run_deadline()
        
        
    
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
        if not self._note_text_change_save:
            return
        
        current_path = self._get_current_path()
        notes_path = util_file.join_path(current_path, 'notes.html')
        notes_path = util_file.create_file(notes_path)
        
        util_file.write_replace(notes_path, self.notes.toHtml())
        
        self.process.set_setting('notes', '')
        
    def initialize_settings(self):
        util.show('Initializing Vetala Process View')
        self._set_default_directory()
        self._setup_settings_file()
        
        self._set_default_project_directory()
        self._set_default_template_directory()
        
    def set_directory(self, directory, load_as_project = False):
        
        self.directory = directory
        
        if not util_file.exists(directory):
            success = util_file.create_dir(name = None, directory = directory)
            
            if not success:
                util.show('Could not find or create path: %s' % directory)
        
        if load_as_project:
            
            util.show('Loading Default path: %s' % self.directory)
            
            history = self.settings.get('project_history')
            
            found = False
            
            for thing in history:
                if thing[0] == 'Default':
                    thing[1] = self.directory
                    found = True
                    
            if not found:
                history.append(['Default', self.directory])
            
            self.settings.set('project_directory', ['Default', self.directory])
            self.settings.set('project_history', history)
            
            self.set_project_directory(self.directory)
            
            self.settings_widget.set_project_directory(directory)
            
    def set_project_directory(self, directory, sub_part = None):
        
        log.debug('Setting project directory: %s' % directory)
        
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
        
        if not sub_part:
            
            directory = str(directory[1])
        
        if sub_part:
            directory = sub_part
            
        if directory != self.last_project:
            
            self.project_directory = directory
            util.set_env('VETALA_PROJECT_PATH', self.project_directory)
            self.directory = directory
            
            self.clear_stage()
            
            self.process.set_directory(self.project_directory)
            
            self.handle_selection_change = True
            self.view_widget.set_directory(self.project_directory)            
            
        self.last_project = directory
        
        self.handle_selection_change = True
        
        self._initialize_project_settings()
                
    def set_template_directory(self, directory = None):
        
        
        if not self.settings:
            return
        
        settings = self.settings
                
        current = settings.get('template_directory')
        history = settings.get('template_history')
        
        if not current:
            if history:
                self.template_widget.set_templates(history)
            return
        
        current_name = None
        
        if not history:
            current_name = current
            history = current
            
        self.template_widget.set_templates(history)
        
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
            
            if util_file.exists(directory):
                if not directory in sys.path:
                    sys.path.append(directory)
    
    def clear_stage(self):
        
        self._clear_code()
        self.active_title.setText('-')
        self.process_splitter.setSizes([1,0])
        self.build_widget.hide()


class SideTabWidget(qt_ui.BasicWidget):
        
    def _build_widgets(self):
        
        policy = self.sizePolicy()
        
        policy.setHorizontalPolicy(policy.Minimum)
        policy.setHorizontalStretch(2)
        
        self.setSizePolicy(policy)

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