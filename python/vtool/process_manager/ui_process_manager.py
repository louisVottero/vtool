# Copyright (C) 2022 Louis Vottero louis.vot@gmail.com    All rights reserved.

from __future__ import absolute_import

import sys
from functools import wraps

from .. import qt_ui, qt, maya_lib
from .. import logger
from .. import util_file
from .. import util
from ..ramen.ui_lib import ui_ramen 

from . import process
from . import ui_view
from . import ui_options
from . import ui_templates
from . import ui_process_settings
from . import ui_process_maintenance
from . import ui_data
from . import ui_code
from . import ui_settings

in_maya = False

if util.is_in_maya():
    in_maya = True
    import maya.cmds as cmds


log = logger.get_logger(__name__) 

vetala_version = util_file.get_vetala_version()

class Signals(qt.QtCore.QObject):
    process_list_update_signal = qt_ui.create_signal()
    
    def update_process_list(self):
        self.process_list_update_signal.emit()

signals = Signals()

def decorator_process_run(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        
        return_value = None
        self = args[0]
        
        if not self.continue_button.isVisible():
            self.process.reset_runtime()
        
        self.continue_button.hide()
        
        #before        
        self.kill_process = False
                
        self.stop_button.show()
        
        self.process_button.setDisabled(True)
        self.batch_button.setDisabled(True)
        
        #process function
        
        if self._process_put:
            self.process._put = self._process_put
        if self._process_runtime_values:
            self.process.runtime_values = self._process_runtime_values
        
        try:
            return_value = function(*args, **kwargs)
        except:
            pass
        
        self._process_runtime_values = self.process.runtime_values
        self._process_put = self.process._put
        
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
        self.settings_widget = None
        self.process_history_dict = {}
        self._path_filter = ''
        
        self._process_runtime_values = {}
        self._process_put = None
        
        self.process = process.Process()
        
        self.process_tabs = None
        self.view_widget = None
        
        self.data_widget = None
        self.code_widget = None
        self.ramen_widget = None
        
        self.directories = None
        self.project_directory = None
        self.last_tab = 0
        self.last_process = None
        self.last_project = None
        self.kill_process = False
        
        self.last_item = None
        
        self.handle_selection_change = True
        self._note_text_change_save = True
        
        super(ProcessManagerWindow, self).__init__(parent = parent, use_scroll = False) 
        
        icon = qt_ui.get_icon('vetala.png')
        self.setWindowIcon(icon)
        
        shortcut = qt.QShortcut(qt.QKeySequence(qt.QtCore.Qt.Key_Escape), self)
        shortcut.activated.connect(self._set_kill_process)
        
        self._code_expanding_tab = False
        self._data_expanding_tab = False
        
        if load_settings:
            
            self.initialize_settings()
        
        log.info('end initialize %s' % self.__class__.__name__)
    
    def initialize_settings(self):
        
        if not self.directory:
            self._set_default_directory()
        
        util.set_env('VETALA_SETTINGS', self.directory)
        
        settings = self._setup_settings_file()
        self._load_settings(settings)
        
        self._set_default_project_directory()
        self._set_default_template_directory()
        
    def _set_default_directory(self):
        default_directory = process.get_default_directory()
        self.directory = default_directory
        
    def _set_default_project_directory(self, directory = None):
        
        if not directory:
            directory = self.settings.get('project_directory')
        
        if directory:
            if type(directory) != list:
                directory = ['', directory]
        
        if not directory:
            directory = ['default', util_file.join_path(self.directory, 'project')]
        
        self.set_default_project(directory)
        
    def _set_default_template_directory(self):
        
        directory = self.settings.get('template_directory')
        
        if directory == None:
            return
        
        if directory:
            if type(directory) != list:
                directory = ['',directory]
        
        self.set_template_directory(directory)

    def _build_widgets(self):
        
        log.info('build widgets')
                
        self._build_header()
        
        self._build_view()
        
        self._build_process_tabs()
        self._build_misc_tabs()
        
        self._build_splitter()
        self._build_splitter_control()
        
        self._build_footer()
        
        self.main_layout.addSpacing(util.scale_dpi(4))
        self.main_layout.addLayout(self.header_layout)
        self.main_layout.addSpacing(util.scale_dpi(4))
        self.main_layout.addWidget(self.process_splitter)
        
        self.main_side_widget.main_layout.addLayout(self.splitter_button_layout)
        self.main_side_widget.main_layout.addSpacing(util.scale_dpi(4))
        self.main_side_widget.main_layout.addWidget(self.process_tabs)
        
        btm_layout = qt.QVBoxLayout()
        btm_layout.addWidget(self.bottom_widget)
        
        self.main_layout.addSpacing(4)
        self.main_layout.addLayout(btm_layout)
        self.main_layout.addSpacing(4)
        
        signals.process_list_update_signal.connect(self.view_widget.refresh)
        
        log.info('end build widgets')
            
    def _build_header(self):
        self.header_layout = qt.QHBoxLayout()
        
        self.progress_bar = qt.QProgressBar()
        self.progress_bar.hide()
        self.progress_bar.setMaximumWidth(util.scale_dpi(100))
        
        self.info_title = qt.QLabel('')
        self.info_title.hide()
        self.info_title.setSizePolicy(qt.QSizePolicy.Minimum, qt.QSizePolicy.Minimum)
        
        self.active_title = qt.QLabel('-')
        self.active_title.setAlignment(qt.QtCore.Qt.AlignCenter)
        
        
        if in_maya:
            settings_icon = qt_ui.get_icon('gear.png')
        else:
            settings_icon = qt_ui.get_icon('gear2.png')
        
        settings = qt.QPushButton(settings_icon, 'Settings')
        settings.setMaximumHeight(util.scale_dpi(20))
        settings.setMaximumWidth(util.scale_dpi(100))
        settings.clicked.connect(self._open_settings)
        
        self.browser_button = qt.QPushButton('Browse')
        self.browser_button.setMaximumWidth(util.scale_dpi(70))
        self.browser_button.setMaximumHeight(util.scale_dpi(20))
        help_button = qt.QPushButton('?')
        help_button.setMaximumWidth(util.scale_dpi(20))
        help_button.setMaximumHeight(util.scale_dpi(20))
        
        self.browser_button.clicked.connect(self._browser)
        help_button.clicked.connect(self._open_help)
        
        left_layout = qt.QHBoxLayout()
        left_layout.addWidget(settings)
        left_layout.addWidget(self.progress_bar)
        
        right_layout = qt.QHBoxLayout()
        right_layout.addWidget(self.info_title)
        right_layout.addWidget(self.browser_button)
        right_layout.addWidget(help_button)
        
        self.header_layout.addLayout(left_layout, alignment = qt.QtCore.Qt.AlignLeft)
        
        self.header_layout.addWidget(self.active_title, alignment = qt.QtCore.Qt.AlignCenter)
        
        self.header_layout.addLayout(right_layout, alignment = qt.QtCore.Qt.AlignRight)
    
    def _build_view(self):
        
        self.view_widget = ui_view.ViewProcessWidget()
        self.view_widget.tree_widget.progress_bar = self.progress_bar
        
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
        
    def _build_splitter(self):
        self.process_splitter = qt.QSplitter()
        self.process_splitter.setOrientation(qt.QtCore.Qt.Vertical)
                
        self.process_splitter.setContentsMargins(0,0,0,0)
        
        left_widget = qt_ui.BasicWidget()
        left_widget.main_layout.addWidget(self.view_widget)
        self.process_splitter.addWidget(left_widget)
        
        self.process_splitter.addWidget(self.main_side_widget)
        
        self.process_splitter.setSizes([1,0,0])
        self.process_splitter.setSizePolicy(qt.QSizePolicy.Expanding, qt.QSizePolicy.Expanding)
        
        self.template_holder_splitter = qt_ui.BasicWidget()
        self.process_splitter.addWidget(self.template_holder_splitter)
        self.template_holder_splitter.hide()
        
    def _build_process_tabs(self):
        
        self.process_tabs = qt.QTabWidget()
        self.main_side_widget = SideTabWidget()
        
        self.option_widget = ui_options.ProcessOptionsWidget()
        
        self.data_widget = ui_data.DataProcessWidget()
        
        self.code_widget = ui_code.CodeProcessWidget()
        
        ramen_spacer_widget = qt.QWidget()
        layout = qt.QVBoxLayout()
        ramen_spacer_widget.setLayout(layout)
        self.ramen_widget = ui_ramen.MainWindow()
        layout.addWidget(self.ramen_widget)
        #self.ramen_widget = ui_nodes.NodeDirectoryWindow()
        
        self.process_tabs.addTab(self.option_widget, 'Options')
        self.process_tabs.addTab(self.data_widget, 'Data')
        self.process_tabs.addTab(self.code_widget, 'Code')
        self.process_tabs.addTab(ramen_spacer_widget, 'Ramen')
        
        self.process_tabs.currentChanged.connect(self._tab_changed)
        
    def _build_misc_tabs(self):
        
        self.misc_tabs = qt.QTabWidget()
        
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
        
        misc_process_widget = qt_ui.BasicWidget()
        misc_process_widget.main_layout.addSpacing(20)
        misc_process_widget.main_layout.addWidget(self.misc_tabs)
        
        self.process_tabs.insertTab(0, misc_process_widget, 'Common')
        
        self.template_holder_tab = qt_ui.BasicWidget()
        self.template_holder_tab.main_layout.addWidget(self.template_widget)
        
        self.misc_tabs.addTab(self.notes, 'Notes')
        self.misc_tabs.addTab(self.template_holder_tab, 'Templates')
        self.misc_tabs.addTab(self.process_settings, 'Settings')
        self.misc_tabs.addTab(self.process_maintenance, 'Maintenance')
        self.misc_tabs.setCurrentIndex(0)
        
        self.misc_tabs.currentChanged.connect(self._misc_tab_changed)
        
        
    def _build_splitter_control(self):
        splitter_button_layout = qt.QHBoxLayout()
        self.splitter_button_layout = splitter_button_layout
        
        full_button = qt.QPushButton('Full')
        full_button.setMaximumHeight(util.scale_dpi(18))
        full_button.setMaximumWidth(util.scale_dpi(60))
        full_button.setSizePolicy(qt.QSizePolicy(qt.QSizePolicy.Minimum,qt.QSizePolicy.Minimum))
        full_button.clicked.connect(self._toggle_full)
        
        half_button = qt.QPushButton('Half')
        half_button.setMaximumHeight(util.scale_dpi(18))
        half_button.setMaximumWidth(util.scale_dpi(60))
        half_button.setSizePolicy(qt.QSizePolicy(qt.QSizePolicy.Minimum,qt.QSizePolicy.Minimum))
        half_button.clicked.connect(self._half)
        
        close_button = qt.QPushButton('Close')
        close_button.setMaximumHeight(util.scale_dpi(18))
        close_button.setMaximumWidth(util.scale_dpi(60))
        close_button.setSizePolicy(qt.QSizePolicy(qt.QSizePolicy.Minimum,qt.QSizePolicy.Minimum))
        close_button.clicked.connect(self._close_tabs)
        
        self.full_button = full_button
        self.close_button = close_button
        
        orientation_button = qt.QPushButton('Alignment')
        orientation_button.setMaximumHeight(util.scale_dpi(18))
        orientation_button.clicked.connect(self._toggle_alignment)
        orientation_button.setSizePolicy(qt.QSizePolicy(qt.QSizePolicy.Minimum,qt.QSizePolicy.Maximum))
        
        splitter_button_layout.addWidget(full_button)
        splitter_button_layout.addWidget(half_button)
        splitter_button_layout.addWidget(orientation_button)
        splitter_button_layout.addWidget(close_button)
        
    def _build_footer(self):
        self.bottom_widget = qt_ui.BasicWidget()
        
        left_button_layout = qt.QHBoxLayout()
        right_button_layout = qt.QHBoxLayout()
        
        self.process_button = qt_ui.BasicButton('PROCESS')
        self.process_button.setWhatsThis("Process button\n\n"
                                         "This button runs the current process' code recipe defined in the code tab.\n"
                                         "You can hit ESC multiple times to stop the process after it starts.\n"
                                         "Somtimes holding ESC works better.\n"
                                         "Use the build widget below to save the process after it finishes.")

        height = util.scale_dpi(25)
        self.process_button.setDisabled(True)
        self.process_button.setMinimumWidth(70)
        self.process_button.setMinimumHeight(height)
        
        build_layout = qt.QHBoxLayout()
        build_label = qt.QLabel('BUILD')
        build_label.setMaximumWidth(util.scale_dpi(40))
        
        save_button = qt_ui.BasicButton('Save')
        
        save_button.setMaximumWidth(util.scale_dpi(40))
        save_button.setMinimumHeight(height)
        
        save_button.clicked.connect(self._save_build)
        
        open_button = qt_ui.BasicButton('Open')
        open_button.setMaximumWidth(util.scale_dpi(45))
        open_button.setMinimumHeight(height)
        
        open_button.clicked.connect(self._open_build)
        
        build_layout.addWidget(build_label)
        build_layout.addSpacing(util.scale_dpi(5))
        build_layout.addWidget(save_button)
        build_layout.addWidget(open_button)
        
        self.batch_button = qt_ui.BasicButton('BATCH')
        self.batch_button.setWhatsThis('Batch button \n\n'
                                        'This will do the same as the Process button, but it will run it in Maya Batch mode.')
        self.batch_button.setDisabled(True)
        self.batch_button.setMinimumHeight(height)
        self.batch_button.setMinimumWidth(70)
        
        self.deadline_button = qt.QPushButton('DEADLINE')
        self.deadline_button.setDisabled(True)
        self.deadline_button.setMinimumHeight(height)
        self.deadline_button.setMinimumWidth(70)
        self.deadline_button.setHidden(True)
        
        self.stop_button = qt.QPushButton('STOP (Hold Esc)')
        self.stop_button.setMaximumWidth(util.scale_dpi(110))
        self.stop_button.setMinimumHeight(height)
        self.stop_button.hide()
        
        self.continue_button = qt.QPushButton('CONTINUE')
        self.continue_button.setMaximumWidth(util.scale_dpi(120))
        self.continue_button.setMinimumHeight(height)
        self.continue_button.hide()
        
        
        
        button_layout = qt.QHBoxLayout()
        
        left_button_layout.setAlignment(qt.QtCore.Qt.AlignLeft)
        left_button_layout.addWidget(self.process_button)
        
        left_button_layout.addSpacing(10)
        left_button_layout.addWidget(self.stop_button)
        left_button_layout.addWidget(self.continue_button)
        
        left_button_layout.addSpacing(10)
        
        right_button_layout.setAlignment(qt.QtCore.Qt.AlignLeft)
        
        right_button_layout.addStretch(1)
        right_button_layout.addSpacing(util.scale_dpi(5))
        right_button_layout.addLayout(build_layout)
        right_button_layout.addStretch(1)
        right_button_layout.addWidget(self.batch_button)
        right_button_layout.addWidget(self.deadline_button)
        
        button_layout.addLayout(left_button_layout)
        
        button_layout.addLayout(right_button_layout)
                
        self.process_button.clicked.connect(self._process)
        self.batch_button.clicked.connect(self._batch)
        self.deadline_button.clicked.connect(self._deadline)
        
        self.stop_button.clicked.connect(self._set_kill_process)
        self.continue_button.clicked.connect(self._continue)
        
        self.bottom_widget.main_layout.addLayout((button_layout))

        
        
    def _build_settings_widget(self):
        self.settings_widget = None
        if not in_maya:
            self.settings_widget = ui_settings.SettingsWidget()
            self.settings_widget.show()
        if in_maya:
            from ..maya_lib.ui_lib import ui_rig
            window = ui_rig.process_manager_settings()
            self.settings_widget = window
            
        self.settings_widget.project_directory_changed.connect(self.set_project_directory)
        self.settings_widget.code_directory_changed.connect(self.set_code_directory)
        self.settings_widget.template_directory_changed.connect(self.set_template_directory)
        self.settings_widget.code_text_size_changed.connect(self.code_widget.code_text_size_changed)
        self.settings_widget.code_expanding_tab_changed.connect(self._update_code_expanding_tab)
        self.settings_widget.data_expanding_tab_changed.connect(self._update_data_expanding_tab)
        self.settings_widget.data_sidebar_visible_changed.connect(self._update_data_sidebar)
        
        self.settings_widget.set_settings(self.settings)
        
    def _update_code_expanding_tab(self, value):
        log.info('Updated code expanding tab %s' % value)
        self._code_expanding_tab = value
        
    def _update_data_expanding_tab(self, value):
        log.info('Updated data expanding tab %s' % value)
        self._data_expanding_tab = value
        
    def _update_data_sidebar(self, value):
        log.info('Updated data sidebar %s' % value)
        self.data_widget.set_sidebar_visible(value)
           
    def resizeEvent(self, event):
        log.info('Resize')
        super(ProcessManagerWindow, self).resizeEvent(event)
        
                
    def sizeHint(self):
        return qt.QtCore.QSize(400,500)
        
    def _setup_settings_file(self):
        
        log.info('Setup Vetala Settings')
        
        settings_file = util_file.SettingsFile()
        settings_file.set_directory(self.directory)
        
        return settings_file
        
    def _load_settings(self, settings):
        self.settings = settings
        
        self.view_widget.set_settings( self.settings )
                
        self._load_templates_from_settings()
        self._load_splitter_settings()
        
        self._code_expanding_tab = self.settings.get('code expanding tab')
        self._data_expanding_tab = self.settings.get('data expanding tab')
        
    def _update_settings_widget(self):
        if self.settings_widget:
            self.settings_widget.set_settings(self.settings)
        
    def _show_options(self):
        log.info('Show options')
        
        sizes = self.process_splitter.sizes()
        self._load_options()
        
        current_index = self.process_tabs.currentIndex()
        
        if current_index != 1:
            self.process_tabs.setCurrentIndex(1)
        
        if sizes[1] == 0:
            self._splitter_to_open()
        
        if current_index == 1 and sizes[1] > 0:
            self.process_splitter.setSizes([1,0])
            return


    def _splitter_to_open(self):
        self._show_splitter()
        size = self.process_splitter.sizes()
        if size[0] > 0 and size[1] > 0:
            return
        
        else:
            self._splitter_to_half()
    
    def _splitter_to_half(self):
        width = self.process_splitter.width()
        half_width = width/2.0
        
        self.process_splitter.setSizes([half_width, half_width])

    def _close_tabs(self):
        self.process_splitter.setSizes([1,0])
        
    def _full_tabs(self):
        self.process_splitter.setSizes([0,1])

    def _hide_splitter(self):
        self.process_splitter.widget(1).hide()
        
    def _show_splitter(self):
        self.process_splitter.widget(1).show()

    def _show_notes(self):
        
        log.info('Show notes')
        
        self._load_notes()
        
        self.process_tabs.setCurrentIndex(0)
        
        sizes = self.process_splitter.sizes()
        if sizes[1] == 0:
            self._splitter_to_open()
        
        self._current_tab = 0
        
    def _show_templates(self):
        
        self.process_tabs.setCurrentIndex(0)
        log.info('Show templates')
        self._splitter_to_open()
        self.misc_tabs.setCurrentIndex(1)
    
    def _show_settings(self):
        self.process_tabs.setCurrentIndex(0)
        log.info('Show settings')
        self._splitter_to_open()
        self.misc_tabs.setCurrentIndex(2)
        
    def _show_maintenaince(self):
        self.process_tabs.setCurrentIndex(0)
        log.info('Show maintenaince')
        self._splitter_to_open()
        self.misc_tabs.setCurrentIndex(3)
        
    def _process_deleted(self):
        self._clear_code(close_windows=True)
        self._clear_data()
        
        self._set_title('-')
        
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
                self._set_title(None)
                self.clear_stage()
            
            self._hide_splitter()
            
            return
        else:
            self._show_splitter()
        
        item = items[0]
        
        if hasattr(item, 'matches'):
            if item.matches(self.last_item):
                return
        
        if hasattr(item, 'get_name'):
            name = item.get_name()
        
            log.info('Selection changed %s' % name)
            
            self.process.load(name)
            
            self._update_process(name)
            
        self.view_widget.setFocus()
    
    def _update_process(self, name = None, store_process = True):
        
        self._set_vetala_current_process(name, store_process)
        
        items = self.view_widget.tree_widget.selectedItems()
        
        title = '-'
        
        folder = None
        
        if items and name != None:
            title = items[0].get_name()
            folder = items[0].is_folder()
        
            if not title:
                title = name
        
        if not items and self._is_inside_process:
            self._set_title(title)
            self.clear_stage(update_process = False)
            return
            
        
        if folder:
            self._set_title(title + '   (folder)')
            self.clear_stage(update_process=False)
            
            self.set_template_directory()
            
            template = self.template_holder_tab.main_layout.takeAt(0)
            self.template_holder_splitter.main_layout.addWidget(template.widget())
            self.process_splitter.widget(2).show()
            
            return
        else:
            count = self.template_holder_splitter.main_layout.count()
            
            if count > 0:
                widget = self.template_holder_splitter.main_layout.takeAt(0)
                widget =widget.widget()
                self.template_holder_tab.main_layout.addWidget(widget)
                self.process_splitter.widget(2).hide()
        
        util.show('Load process: %s' % name)
        
        if name:
            log.info('Update process name')
            
            self._set_title(title)
            
            self.process_button.setEnabled(True)
            self.batch_button.setEnabled(True)
            if util_file.has_deadline():
                self.deadline_button.setVisible(True)
                self.deadline_button.setEnabled(True)
                                
        if not name:
            log.info('Update process no name')
            self._set_title('-')
            
            self.process_button.setDisabled(True)
            self.batch_button.setDisabled(True)
            if util_file.has_deadline():
                self.deadline_button.setVisible(True)
                self.deadline_button.setDisabled(True)
            
            self.current_process = None
            
        if not self.current_process:
            return
        
        self._clear_code()
        self._clear_data()
        
        self._update_sidebar_tabs()
        
        if not self._is_splitter_open():
            self._show_notes()
            if not self._last_note_lines and self.process.has_options():
                self._show_options()
                
        self._splitter_to_open()
        
        self.last_process = name 
        
    def _update_sidebar_tabs(self):
        
        log.info('Update sidebar')
        
        self.ramen_widget.hide()
        
        if self.process_tabs.currentIndex() == 0:
            
            if self.misc_tabs.currentIndex() == 0:
                self._load_notes()
            if self.misc_tabs.currentIndex() == 1:
                self.set_template_directory()
            if self.misc_tabs.currentIndex() == 2:
                self._load_process_settings()
            if self.misc_tabs.currentIndex() == 3:
                self._load_process_maintenance()
           
        if self.process_tabs.currentIndex() == 1:
            self._load_options()
        if self.process_tabs.currentIndex() == 2:
            self._load_data_ui()
        if self.process_tabs.currentIndex() == 3:
            self._load_code_ui()
        if self.process_tabs.currentIndex() == 4:
            self.ramen_widget.show()
            self._load_ramen_ui()
            
       
         
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
            
    def _tab_changed(self):
        
        log.debug('Tab changed %s' % self.process_tabs.currentIndex())
        
        self.process_button.show()
        self.batch_button.show()
        
        self._update_sidebar_tabs()
        
        if util_file.has_deadline():
            self.deadline_button.show()
        
        current_index = self.process_tabs.currentIndex()
        
        if current_index == 0:
            self._splitter_to_open()
            return
        
        if current_index == 1:
            return
        
        if self.process and current_index == 2:
            if self._data_expanding_tab:
                self._full_tabs()
            return
        
        if self.process and current_index == 3:
            if self._code_expanding_tab:
                self._full_tabs()
            return
        
        self.last_tab = current_index
        
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
            self.current_process = None
            return
        
        current_path = self._get_current_path()
        
        if self.project_directory:
            
            #this needs to happen first because it reloads the settings.  If not the settings are retained from whats loaded into the settings class
            if store_process:
                self._set_project_setting('process', name )
                self.settings.set('process', [name, str(self.project_directory)])
            
            if not util_file.get_permission(current_path):
                util.warning('Could not get permission for process: %s' % current_path)
                
            self.current_process = current_path
            util.set_env('VETALA_CURRENT_PROCESS', current_path)
            
        
        
    def _initialize_project_settings(self):
        
        process.initialize_project_settings(self.project_directory, self.settings)
        
        self._update_settings_widget()
        
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
        
    def _load_notes(self):
        
        log.info('Load notes')
        
        self._note_text_change_save = False
        
        note_lines = self._get_note_lines()
        
        self._last_note_lines = note_lines
        
        if not note_lines:
            
            self.notes.clear()
            self._note_text_change_save = True
            return False
            
        
        if note_lines:
            
            self.notes.clear()
            self.notes.setHtml(note_lines)
            
        self._note_text_change_save = True
        
        return True
        
    def _load_process_settings(self):
        
        log.info('Load process settings')
        
        self.process_settings.set_directory(self._get_current_path())
        
    def _load_process_maintenance(self):
        log.info('Load process maintenance')
        self.process_maintenance.set_directory(self._get_current_path())
        
    def _load_templates_from_settings(self):
        
        if not self.settings:
            return
        
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
            #self._splitter_to_half()
            
        if sizes[0] > 1 and sizes[1] >= 0:
            self._full_tabs()
    
    def _half(self):
        self._splitter_to_half()
    
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
        
    def _misc_tab_changed(self):
        
        if self.misc_tabs.currentIndex() == 0:
            self.template_widget.set_active(False)
            self.process_settings.set_active(False)
            self._current_tab = 0
            self._load_notes()
            
        if self.misc_tabs.currentIndex() == 1:
            self.template_widget.set_active(True)
            self.process_settings.set_active(False)
            self._current_tab = None
        
        if self.misc_tabs.currentIndex() == 2:
            
            self.template_widget.set_active(False)
            self.process_settings.set_active(True)
            self._current_tab = 2
            
            self._load_process_settings()
            
        if self.misc_tabs.currentIndex() == 3:
            self.template_widget.set_active(False)
            self.process_settings.set_active(False)
            self._current_tab = 3
            
            self._load_process_maintenance()
            
    def _clear_code(self, close_windows = False):
        
        self.code_widget.close_widgets(close_windows)
        
    def _clear_data(self):
        
        self.data_widget.clear_data()

    def _clear_options(self):
        self.option_widget.option_palette.clear_widgets()
        
    def _clear_notes(self):
        self._note_text_change_save = False
        self.notes.clear()
        
    
    def _set_title(self, name = None):
        
        if not name:
            self.active_title.setText('-')
            return
        
        name = name.replace('/', '  /  ')
        
        self.active_title.setText(name)
        
    def _open_help(self):
        
        util_file.open_website('https://vetala-auto-rig.readthedocs.io/en/latest/index.html')
        
    def _load_data_ui(self):
        
        if util.is_in_maya() and self.process:
            if not self.process.is_data_folder('build'):
                self.process.create_data('build', 'maya.ascii')
                
        path = self._get_current_path()
        self.data_widget.set_directory(path)
        
    def _load_code_ui(self):
        
        path = self._get_current_path()
        
        self.code_widget.set_directory(path, False)
        
        code_directory = self.settings.get('code_directory')
        self.code_widget.set_external_code_library(code_directory)
        
        self.code_widget.set_settings(self.settings)
        
    def _load_ramen_ui(self):
        path = self._get_current_path()
        
        self.ramen_widget.set_directory(path)
        
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
            
            directory = self.project_directory
            
            if filter_str:
                directory = util_file.join_path(self.project_directory, filter_str)
            
            directory = util_file.join_path(directory, process_name)
            
        if not process_name:
            
            filter_value = self.view_widget.filter_widget.get_sub_path_filter()
            
            if filter_value:
                directory = util_file.join_path(self.project_directory, filter_value)
            else:
                directory =self.project_directory
        
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
        
        #if self.tab_widget.currentIndex() == 1:
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
                
        self.process_tabs.setCurrentIndex(3)
        
        scripts, states = self.process.get_manifest()
        
        manage_node_editor_inst = None
        
        if in_maya:
            
            start_new_scene = self.settings.get('start_new_scene_on_process')
            
            if start_new_scene and not has_last_inc:
                core.start_new_scene()
            
            manage_node_editor_inst = maya_lib.core.ManageNodeEditors()
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
            
            if progress_bar:
                progress_bar.set_count(script_count)
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
                
                #-----------------------------Run the Script-------------------------------
                status = self.process.run_script(script_name, False, self.settings.settings_dict, return_status=True)
                children = self.process._skip_children
                if children:
                    skip_scripts.append(script_name)
                    self.process._skip_children = None
                
                self.code_widget.script_widget.code_manifest_tree.set_process_data(self.process.runtime_values, self.process._put)
                
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
            util.show('\nProcess %s built in %s seconds\n\n' % (self.process.get_name(), seconds))
        if minutes != None:
            util.show('\nProcess %s built in %s minutes, %s seconds\n\n' % (self.process.get_name(), minutes,seconds))
        
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
        
    def _save_build(self):
        
        if util.is_in_maya():
            comment = qt_ui.get_comment(self, 'Note: Check previous versions in the Data Tab\n\nWrite a comment for this save.', 'Get Comment', 'Build Update')
            
            if comment == None:
                return
            
            if not comment:
                comment = 'Build update'
            
            self.process.save_data('build', comment)
    
    def _open_build(self):
        
        result = True
        
        if cmds.file(q = True, mf = True):
            if util.is_in_maya():
                result = qt_ui.get_save_permission('Save changes?', self)
                    
                if result:
                    
                    filepath = cmds.file(q = True, sn = True)
                    if not filepath:
                        util.warning('Open cancelled! Maya file not saved: %s' % filepath)
                        return
                        
                    saved = maya_lib.core.save(filepath)
                    if not saved:
                        util.warning('Open cancelled! Maya file not saved: %s' % filepath)
                        return

                if result == None:
                    return
        
        self.process.open_data('build')
    
    def _batch(self):
        
        self.process.run_batch()
        
    def _deadline(self):
        
        self.process.run_deadline()
        
    def _open_settings(self):
        
        self._build_settings_widget()
        
    def _browser(self):
        
        directory = self._get_current_path()
        
        if not directory:
            
            directory = str(self.project_directory)
            
        if directory and self.process_tabs.currentIndex() == 0:
            path = directory
        if directory and self.process_tabs.currentIndex() == 1:
            path = directory            
        if directory and self.process_tabs.currentIndex() == 2:
            path = self.process.get_data_path()
        if directory and self.process_tabs.currentIndex() == 3:
            path = self.process.get_code_path()   
        if directory and self.process_tabs.currentIndex() == 4:
            path = self.process.get_ramen_path()
            
        util_file.open_browser(path)
            
    def _template_current_changed(self):
        
        if self.settings_widget:
            self.settings_widget.refresh_template_list()        
        
    def _save_notes(self):
        if not self._note_text_change_save:
            return
        
        current_path = self._get_current_path()
        notes_path = util_file.join_path(current_path, 'notes.html')
        notes_path = util_file.create_file(notes_path)
        
        if not notes_path:
            return
        
        util_file.write_replace(notes_path, self.notes.toHtml())
        self.process.set_setting('notes', '')
        
    def set_directory(self, directory = None):
        
        check_directory = self.directory
        if directory: 
            check_directory = directory
        
        if not util_file.exists(check_directory):
            success = util_file.create_dir(name = None, directory = check_directory)
            
            if not success:
                util.show('Could not find or create path: %s' % self.directory)
        
        if directory:
            
            if not self.directory or not os.path.samefile(directory, self.directory):
                self.directory = directory
                self.initialize_settings()
                
                directory = self.settings.get('project_directory')
                self.set_project_directory(directory)
                self._update_settings_widget()
        
    def set_default_project(self, directory = None):
        
        name = 'Default'
        
        if directory:
            name = directory[0]
            directory = directory[1]
        
        if not directory:
            name = 'default'
            directory = util_file.join_path(self.directory, 'project')
        
        util.show('Loading Default path: %s' % directory)
        
        self.append_project_history(directory, name)
        self.set_project_directory(directory)
        
    def append_project_history(self, directory, name = ''):
        history = self.settings.get('project_history')
        
        found = False
        
        if history:
            if name:
                for thing in history:
                    if thing[0] == name:
                        thing[1] = directory
                        found = True
            if not name:
                for thing in history:
                    if thing[1] == directory:
                        return
        else:
            history = []
                    
        if not found:
            history.append([name, directory])
        
        self.settings.set('project_directory', [name, directory])
        
        self.settings.set('project_history', history)
        
    def set_project_directory(self, directory, name = ''):
        
        log.info('Setting project directory: %s' % directory)
        
        self.handle_selection_change = False
        
        self.view_widget.tree_widget.clearSelection()
        
        if not directory:
            self.process.set_directory(None)
            self.view_widget.set_directory(None)
            self.handle_selection_change = True
            return

        if type(directory) != list:
            directory = ['', str(directory)]

        directory = str(directory[1])

        if directory != self.last_project:
            
            self.project_directory = directory
            util.set_env('VETALA_PROJECT_PATH', self.project_directory)
            
            self._set_title(None)
            self.clear_stage()
            if self.process:
                self.process.set_directory(self.project_directory)
            
            self.handle_selection_change = True
            self.view_widget.set_directory(self.project_directory)
            
        self.last_project = directory
        
        self.handle_selection_change = True
        
        self.append_project_history(directory, name)
        
        self._initialize_project_settings()
        
                
    def set_template_directory(self, directory = None):
        
        if not self.settings:
            return
        self.template_widget.active = True
        settings = self.settings
        
        current = None
        if not directory:
            current = settings.get('template_directory')
        else:
            current = directory
            
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
            
            if type(current_name) == list:
                self.template_widget.set_current(current_name[0])
            else:
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
    
    def clear_stage(self, update_process = True):
        
        self._clear_code()
        self._clear_data()
        self._clear_options()
        self._clear_notes()
        
        if update_process:
            self._update_process(None, store_process = False)
        self._hide_splitter()
        

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