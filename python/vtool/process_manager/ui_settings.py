# Copyright (C) 2014-2016 Louis Vottero louis.vot@gmail.com    All rights reserved.

from vtool import qt_ui, qt
from vtool import util_file
from vtool import util

    
class SettingsWidget(qt_ui.BasicWidget):
    
    project_directory_changed = qt_ui.create_signal(object)
    template_directory_changed = qt_ui.create_signal(object)
    code_directory_changed = qt_ui.create_signal(object)
    
    def __init__(self):
        
        
        super(SettingsWidget, self).__init__()
        
        self.code_directories = []
        self.template_history = []
        self.settings = None
    
    def _define_main_layout(self):
        layout = qt.QVBoxLayout()
        #layout.setAlignment(qt.QtCore.Qt.AlignTop)
        return layout 
    
    def _build_widgets(self):
        
        self.setContentsMargins(10,10,10,10)
        
        self.tab_widget = qt.QTabWidget()
        
        self.dir_widget = qt_ui.BasicWidget()
        
        
        
        #self.tab_widget.addTab(self.dir_widget, 'Paths')
        
        #self.tab_widget.setTabPosition(self.tab_widget.West)
        
        self._build_dir_widgets()
        option_scroll_widget = self._build_option_widgets()
        
        self.tab_widget.addTab(option_scroll_widget, 'Options')
        
        self.main_layout.addWidget(self.tab_widget)
        
    def _build_dir_widgets(self):
        
        self.project_directory_widget = ProjectDirectoryWidget()
        self.project_directory_widget.directory_changed.connect(self._project_directory_changed)
        
        #tabs = qt.QTabWidget()
                             
        self.code_directory_widget = CodeDirectoryWidget()
        self.code_directory_widget.directory_changed.connect(self._code_directory_changed)

        self.template_directory_widget  = TemplateDirectoryWidget()
        self.template_directory_widget.directory_changed.connect(self._template_directory_changed)

        self.tab_widget.addTab(self.project_directory_widget, 'Project')
        self.tab_widget.addTab(self.code_directory_widget, 'Code')
        self.tab_widget.addTab(self.template_directory_widget, 'Template')

        #self.editor_directory_widget = ExternalEditorWidget()
        #self.editor_directory_widget.set_label('External Editor')
        
        #self.dir_widget.main_layout.addWidget(tabs)
        
        #self.dir_widget.main_layout.addSpacing(10)
        #self.dir_widget.main_layout.addWidget(self.editor_directory_widget)
        #self.dir_widget.main_layout.addSpacing(10)
        
    def _build_option_widgets(self):
        
        self.options_widget = qt_ui.BasicWidget()
        self.options_widget.main_layout.setSpacing(5)
        self.options_widget.main_layout.setContentsMargins(10,10,10,10)
        #self.options_widget.setSizePolicy(qt.QSizePolicy(qt.QSizePolicy.Maximum, qt.QSizePolicy.Maximum))
        
        scroll = qt.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.options_widget)
        
        self.editor_directory_widget = ExternalEditorWidget()
        self.editor_directory_widget.set_label('External Editor')
        
        self.options_widget.main_layout.addWidget(self.editor_directory_widget)
        
        process_group = qt.QGroupBox('Process Settings')
        group_layout = qt.QVBoxLayout()
        process_group.setLayout(group_layout)
        
        
        process_maya_group = qt.QGroupBox('Maya')
        maya_group_layout = qt.QVBoxLayout()
        process_maya_group.setLayout(maya_group_layout)
        
        self.auto_focus_scene = qt_ui.GetCheckBox('Auto Focus Scene')
        self.auto_focus_scene.set_state(True)
        
        self.error_stop = qt_ui.GetCheckBox('Stop Process on error.')
        self.error_stop.check_changed.connect(self._set_stop_on_error)
        
        self.process_start_new_scene = qt_ui.GetCheckBox('Start New Scene on Process')
        self.process_start_new_scene.set_state(True)
        
        self.process_start_new_scene.check_changed.connect(self._set_start_new_scene_on_process)
        
        self.auto_focus_scene.check_changed.connect(self._set_auto_focus_scene)
        
        maya_group_layout.addWidget(self.process_start_new_scene)
        maya_group_layout.addWidget(self.auto_focus_scene)
        
        group_layout.addWidget(self.error_stop)
        group_layout.addWidget(process_maya_group)
        
        self.options_widget.main_layout.addWidget(process_group)
        
        self.shotgun_group = ShotgunGroup()
        
        self.options_widget.main_layout.addWidget(self.shotgun_group)
        
        
        
        scroll.setWidget(self.options_widget)
        
        
        return scroll
        
        #self.options_widget.main_layout.addWidget(self.error_stop)
        #self.options_widget.main_layout.addWidget(self.process_start_new_scene)
        
    def _set_stop_on_error(self):
        self.settings.set('stop_on_error', self.error_stop.get_state())
        
    def _set_start_new_scene_on_process(self):
        
        self.settings.set('start_new_scene_on_process', self.process_start_new_scene.get_state())
        
    def _set_auto_focus_scene(self):
        
        self.settings.set('auto_focus_scene', self.auto_focus_scene.get_state())
        
    
        
    def _get_stop_on_error(self):
        value = self.settings.get('stop_on_error')
        
        if value:
            self.error_stop.set_state(True)
    
            
    def _get_start_new_scene_on_process(self):
        value = self.settings.get('start_new_scene_on_process')
        
        if value:
            self.process_start_new_scene.set_state(True)
        if value == None:
            self.settings.set('start_new_scene_on_process', True)
        if value == False:
            self.process_start_new_scene.set_state(False)
    
    def _get_auto_focus_scene(self):
        value = self.settings.get('auto_focus_scene')
        
        if value:
            self.auto_focus_scene.set_state(True)
        if value == None:
            self.settings.set('auto_focus_scene', True)
        if value == False:
            self.auto_focus_scene.set_state(False)
    
    def _project_directory_changed(self, project):
        
        self.project_directory_changed.emit(project)
        
    def _template_directory_changed(self, project):
        self.template_directory_changed.emit(project)
        
    def _code_directory_changed(self, code_directory):
        self.code_directory_changed.emit(code_directory)
    
    def get_project_directory(self):
        return self.project_directory_widget.get_directory()
        
    def set_project_directory(self, directory):
        self.project_directory_widget.set_directory(directory)
    
    def set_template_directory(self, directory):
        self.template_directory_widget.set_directory(directory)
        
    def set_code_directory(self, directory):
        if directory:
            self.code_directory_widget.set_directory(directory)
        
    def set_code_list(self, code_directories):
        
        self.code_directories = code_directories
        self.code_list.clear()
        
        items = []
        
        for code in self.code_directories:
            item = qt.QListWidgetItem()
            item.setText(code)
            item.setSizeHint(qt.QtCore.QSize(30, 40))
            
            items.append(item)
            self.code.addItem(item)
            
    def set_settings(self, settings):
        self.settings = settings
        self.project_directory_widget.set_settings(settings)
        self.editor_directory_widget.set_settings(settings)
        
        self._get_stop_on_error()
        self._get_start_new_scene_on_process()
        self._get_auto_focus_scene()
        
        self.shotgun_group.set_settings(settings)
        
    def set_template_settings(self, settings):
        
        self.template_directory_widget.set_settings(settings)
        
    def refresh_template_list(self):
        
        current = self.settings.get('template_directory')
        history = self.settings.get('template_history')
        
        self.template_directory_widget.list.refresh_list(current, history)
        
class ShotgunGroup(qt_ui.Group):
    
    def __init__(self):
        super(ShotgunGroup, self).__init__('Shotgun Settings')
        
        
    
    def _build_widgets(self):
        super(ShotgunGroup,self)._build_widgets()
        
        shotgun_group = qt.QGroupBox('Shotgun Settings')
        shotgun_group_layout = qt.QVBoxLayout()
        shotgun_group.setLayout(shotgun_group_layout)
        
        
        #self.get_shotgun_url = qt_ui.GetString('Webpage')
        self.get_shotgun_name = qt_ui.GetString('Script Name')
        self.get_shotgun_code = qt_ui.GetString('Application Key')
        
        self.get_shotgun_asset_publish_code = qt_ui.GetString('Tank Asset Publish Template')
        self.get_shotgun_asset_publish_code.set_text('maya_asset_publish')
        self.get_shotgun_asset_work_code = qt_ui.GetString('Tank Asset Work Template')
        self.get_shotgun_asset_work_code.set_text('maya_asset_work')
        
        toolkit_warning = qt.QLabel('If "import sgtk" is not in your PYTHONPATH,\nload the path above the folder sgtk:')
        self.get_shotgun_toolkit = ShotgunToolkitWidget()
        
        
        self.get_shotgun_name.text_changed.connect(self._set_shotgun_name)
        self.get_shotgun_code.text_changed.connect(self._set_shotgun_code)
        #self.get_shotgun_url.text_changed.connect(self._set_shotgun_url)
        
        self.get_shotgun_asset_publish_code.text_changed.connect(self._set_shotgun_asset_publish_code)
        self.get_shotgun_asset_work_code.text_changed.connect(self._set_shotgun_asset_work_code)
        
        
        #self.main_layout.addWidget(self.get_shotgun_url)
        self.main_layout.addWidget(self.get_shotgun_name)
        self.main_layout.addWidget(self.get_shotgun_code)
        
        self.main_layout.addWidget(self.get_shotgun_asset_publish_code)
        self.main_layout.addWidget(self.get_shotgun_asset_work_code)
        self.main_layout.addSpacing(10)
        
        self.main_layout.addSpacing(10)
        self.main_layout.addWidget(toolkit_warning)
        self.main_layout.addWidget(self.get_shotgun_toolkit)

    def _set_shotgun_name(self):
        self.settings.set('shotgun_name', str(self.get_shotgun_name.get_text()))
    
    def _set_shotgun_code(self):
        self.settings.set('shotgun_code', str(self.get_shotgun_code.get_text()))
        
    def _set_shotgun_url(self):
        self.settings.set('shotgun_url', str(self.get_shotgun_url.get_text()))
        
    def _set_shotgun_asset_publish_code(self):
        self.settings.set('shotgun_asset_publish_template', str(self.get_shotgun_asset_publish_code.get_text()))
    
    def _set_shotgun_asset_work_code(self):
        self.settings.set('shotgun_asset_work_template', str(self.get_shotgun_asset_work_code.get_text()))
        
    def _get_shotgun_name(self):
        value = self.settings.get('shotgun_name')
        if value:
            self.get_shotgun_name.set_text(value)
    
    def _get_shotgun_code(self):
        value = self.settings.get('shotgun_code')
        if value:
            self.get_shotgun_code.set_text(value)
            
    def _get_shotgun_url(self):
        value = self.settings.get('shotgun_url')
        if value:
            self.get_shotgun_url.set_text(value)
        
    def _get_shotgun_asset_publish_code(self):
        value = self.settings.get('shotgun_asset_publish_template')
        
        if not value:
            value = 'maya_asset_publish'
            self.settings.set('shotgun_asset_publish_template', value)
        
        if value:
            self.get_shotgun_asset_publish_code.set_text(value)
        
    def _get_shotgun_asset_work_code(self):
        value = self.settings.get('shotgun_asset_work_template')
        
        if not value:
            value = 'maya_asset_work'
            self.settings.set('shotgun_asset_work_template', value)
        
        if value:
            self.get_shotgun_asset_work_code.set_text(value)
        
    def set_settings(self, settings):
        
        self.settings = settings
        self.get_shotgun_toolkit.set_settings(settings)
        
        #self._get_shotgun_url()
        self._get_shotgun_name()
        self._get_shotgun_code()
        
        self._get_shotgun_asset_publish_code()
        self._get_shotgun_asset_work_code()
        
class ExternalEditorWidget(qt_ui.GetDirectoryWidget):
    
    def __init__(self, parent = None):
           
        super(ExternalEditorWidget, self).__init__(parent)
        
        self.settings = None
        
    def _browser(self):
        
        filename = qt_ui.get_file(self.get_directory() , self)
        
        if filename:
        
            if util_file.is_file(filename):
                filename = util_file.fix_slashes(filename)
                self.directory_edit.setText(filename)
                self.directory_changed.emit(filename)
                self.settings.set('external_editor', str(filename))
    
    def set_settings(self, settings):
        
        self.settings = settings
        
        filename = self.settings.get('external_editor')
        
        if util_file.is_file(str(filename)):
            self.set_directory_text(filename)
        
class ShotgunToolkitWidget(qt_ui.GetDirectoryWidget):
    
    def __init__(self, parent = None):
           
        super(ShotgunToolkitWidget, self).__init__(parent)
        
        self.set_label('Shotgun Toolkit Path')
        self.settings = None
        
        self.api_passed = qt.QLabel(' Works ')
        self.api_passed.setStyleSheet("QLabel { background-color : lightGreen; color : black; }")
        self.api_passed.hide()
        self.main_layout.addWidget(self.api_passed)

    def _test_python_path(self, path):
        
        util.add_to_PYTHONPATH(path)
        
        if util.has_shotgun_tank():
            self.api_passed.show()
        else:
            self.api_passed.hide()
            
    def _browser(self):
        
        filename = qt_ui.get_folder(self.get_directory() , self)
        
        if filename:
        
            if util_file.is_dir(filename):
                filename = util_file.fix_slashes(filename)
                self.directory_edit.setText(filename)
                self.directory_changed.emit(filename)
                self.settings.set('shotgun_toolkit', str(filename))
                
                self._test_python_path(filename)
    
    
    
    def set_settings(self, settings):
        
        self.settings = settings
        
        filename = self.settings.get('shotgun_toolkit')
        
        if util_file.is_dir(str(filename)):
            self.set_directory_text(filename)
            self._test_python_path(filename)
            
        
        
class ProjectDirectoryWidget(qt_ui.GetDirectoryWidget):
    
    def __init__(self, parent = None):
        self.list = None
    
        super(ProjectDirectoryWidget, self).__init__(parent)
        self.directory_entry = 'project_directory'
        self.history_entry = 'project_history'
        self.settings = None
        self._setting_entries()
    
    def _setting_entries(self):
        self.directory_entry = 'project_directory'
        self.history_entry = 'project_history' 
    
    def _define_main_layout(self):
        return qt.QVBoxLayout()
    
    def _define_history_list(self):
        return ProjectList()
    
    def _build_widgets(self):
    
        file_layout = qt.QHBoxLayout()
    
        #self.directory_label = qt.QLabel('directory')

        #self.label = qt.QLabel('Paths')
        
        directory_browse = qt.QPushButton('Browse')
        directory_browse.setMaximumWidth(100)
        
        directory_browse.clicked.connect(self._browser)

        #file_layout.addWidget(self.directory_label)
        file_layout.addWidget(directory_browse)
        
        self.list = self._define_history_list()
        self.list.setAlternatingRowColors(True)
        self.list.setSelectionMode(self.list.SingleSelection)
        self.list.directories_changed.connect(self._send_directories)
        self.list.itemClicked.connect(self._item_selected)
        
        self.main_layout.addSpacing(5)
        #self.main_layout.addWidget(self.label)
        self.main_layout.addWidget(self.list)
        self.main_layout.addLayout(file_layout)
        
        self.main_layout.addSpacing(15)
        
    def _item_selected(self):
        
        item = self.list.currentItem()
        
        if not item:
            return
        
        directory = [item.text(0), item.text(1)]
        
        self.set_directory(directory)
        
        self.directory_changed.emit(directory)

    def _text_changed(self, directory):
         
        if type(directory) != list:
            directory = ['', directory]
        
        if not util_file.is_dir(directory[1]):    
            return
        
        found = self.list.get_directories()
        
        if directory in found:    
            return
        
        if found:
            found.insert(0, directory)
            
        if not found:
            found = directory 
        
        self.directory_changed.emit(directory)
        
        #self.list.select(directory)
        #self.set_label(directory[1])
        
        #self.list.refresh_list(directory, found)
        
    def _send_directories(self, directory):
        self.directory_changed.emit(directory)
        
    def _browser(self):
        
        current_dir = self.list.current_directory()
        
        if not current_dir:
            current_dir = 'C:/'
        
        filename = qt_ui.get_folder(current_dir, self)
        
        if not filename:
            return
        
        filename = util_file.fix_slashes(filename)
        
        found = self.list.get_directories()
        
        for item in found:
            if item[1] == filename:
                return
        
        if found:
            found.insert(0, filename)
            
        if not found:
            found = [filename] 
        
        if filename and util_file.is_dir(filename):
            
            self.settings.set(self.directory_entry, filename)
            self._set_history(filename)
            self.list.refresh_list(filename, found)
            
            
            self._send_directories(filename)
            
    def _set_history(self, current_directory):
        
        if not type(current_directory) == list:
            current_directory = ['', str(current_directory)]
        
        item = self.list.currentItem()
        selected = self.list.selectedItems()
        
        if not item:
            if selected:
                item = selected[0]
        
        previous_directory = None
        
        if item:
        
            previous_directory = str(item.text(1))
        
        history = self.settings.get(self.history_entry)
        
        if not history and previous_directory:
            history = []
            history.append([str(item.text(0)), previous_directory])
        
        if previous_directory != current_directory[1] and previous_directory:

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
            
        if history:
            if not current_directory in history:
                history.insert(0, current_directory)
                
        
        
        if self.settings:
            self.settings.set(self.history_entry, history)
        
    def set_directory(self, directory):
        
        history = None
        
        if not directory:
            return
        
        if self.settings:
            history = self.settings.get(self.history_entry)
        
        if type(directory) != list:
            directory = ['', str(directory)]
            
        self.settings.set(self.directory_entry, directory[1])
        
        self.list.refresh_list(directory, history)
        
        self.list.select(directory)
            
    def set_settings(self, settings):
        
        self.settings = settings
        self.list.set_settings(settings)

class ProjectList(qt.QTreeWidget):

    directories_changed = qt_ui.create_signal(object)

    def __init__(self):
        super(ProjectList, self).__init__()
        
        self.setAlternatingRowColors(True)
        self.setSelectionMode(self.NoSelection)
        self.setHeaderLabels(['name', 'directory'])

        self.setColumnWidth(0, 200)
        
        self.setContextMenuPolicy(qt.QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._item_menu)
        
        self._create_context_menu()
        self.settings = None     
        
        self._setting_entries()
        
        
    def _setting_entries(self):
        self.directory_entry = 'project_directory'
        self.history_entry = 'project_history' 
        
    def _item_menu(self, position):
        
        item = self.itemAt(position)
        
        if item:
            self.setCurrentItem(item)
            self.context_menu.exec_(self.viewport().mapToGlobal(position))
        
    def _create_context_menu(self):
        
        self.context_menu = qt.QMenu()
        
        name_action = self.context_menu.addAction('Rename')
        
        moveup_action = self.context_menu.addAction('Move Up')
        movedown_action = self.context_menu.addAction('Move Down')
        
        remove_action = self.context_menu.addAction('Remove')
        
        remove_action.triggered.connect(self.remove_current_item)
        name_action.triggered.connect(self.name_current_item)
        moveup_action.triggered.connect(self.move_current_item_up)
        movedown_action.triggered.connect(self.move_current_item_down)
        
    def name_current_item(self):
        
        item = self.currentItem()
        
        old_name = str(item.text(0))
        directory = str(item.text(1))
        
        new_name = qt_ui.get_new_name('Name Project', self, old_name)
        
        if new_name:
            item.setText(0, new_name)
        
            if self.settings:
                
                self.settings.set(self.history_entry, self.get_directories())
                self.settings.set(self.directory_entry, [new_name, directory])
        
    def move_current_item_up(self):
        
        current_index = self.currentIndex()
        
        if current_index == None:
            return
        
        current_index = current_index.row()
        
        if current_index == 0:
            return
        
        current_item = self.takeTopLevelItem(current_index)
        
        self.insertTopLevelItem( (current_index - 1), current_item)

        self.setCurrentItem(current_item)
        
        name = str( current_item.text(0) )
        directory = str( current_item.text(1) )
        
        if self.settings:
            
            self.settings.set(self.history_entry, self.get_directories())
            self.settings.set(self.directory_entry, [name, directory])
        
    def move_current_item_down(self):
        
        current_index = self.currentIndex()
        
        if current_index == None:
            return
        
        current_index = current_index.row()
        
        count = self.topLevelItemCount()
        
        if current_index == (count-1):
            return
        
        current_item = self.takeTopLevelItem(current_index)
        
        self.insertTopLevelItem( (current_index + 1), current_item)
        
        self.setCurrentItem(current_item)
        
        name = str(current_item.text(0))
        directory = str(current_item.text(1))
        
        if self.settings:
            
            self.settings.set(self.history_entry, self.get_directories())
            self.settings.set(self.directory_entry, [name, directory])
        
    def remove_current_item(self):
        
        index = self.currentIndex()
        
        item = self.topLevelItem(index.row())
        
        self.takeTopLevelItem(index.row())
        
        project = self.settings.get('project_directory')
        
        if project == item.text(1):
            self.directories_changed.emit('')
        
        directories = self.get_directories()
        
        if self.settings:
            self.settings.set(self.history_entry, self.get_directories())
            if directories:
                self.settings.set(self.directory_entry, directories[0][1])
            if not directories:
                self.settings.set(self.directory_entry, None)
        
    def current_directory(self):
        
        selected_items = self.selectedItems()
        
        if selected_items:
            return selected_items[0].text(1)
        
    def refresh_list(self, current, history):
        
        if type(current) != list:
            current = ['', current]
        
        self.clear()
        
        self.history = history
        
        if not self.history:
            self.history = [current]
        
        items = []
        
        select_item = None
        
        for history in self.history:
            
            if history == None:
                continue
                
            if type(history) != list:
                history = ['', history]
            
            item = qt.QTreeWidgetItem()
            item.setText(0, history[0])
            item.setText(1, history[1])
            item.setSizeHint(0, qt.QtCore.QSize(20, 25))
            
            if current[1] == history[1]:
                select_item = item
            
            items.append(item)
            self.addTopLevelItem(item)
        
        self.scrollToItem(select_item)
        self.setItemSelected(select_item, True)
        
    def get_directories(self):
        
        count = self.topLevelItemCount()
        
        found = []
        
        if count:
            
            for inc in range(0, count):
            
                item = self.topLevelItem(inc)
                if item:
                    
                    name = str(item.text(0))
                    directory = str(item.text(1))
                    
                    found.append([name, directory])
            
        return found
     
    def set_settings(self, settings):
        
        self.settings = settings
        
    def select(self, directory):
        
        self.clearSelection()
        
        count = self.topLevelItemCount()
        
        if count:
            for inc in range(0, count):
                
                item = self.topLevelItem(inc)
                
                if item:
                    sub_directory = str(item.text(1))
                    
                    if sub_directory == directory[1]:
                        if not self.isItemSelected(item):
                            self.setItemSelected(item, True)
                        
class CodeDirectoryWidget(qt_ui.GetDirectoryWidget):
    
    def __init__(self, parent = None):
        
        self.code_list = None
        self.label = 'directory'
        
        super(CodeDirectoryWidget, self).__init__(parent)
            
    def _define_main_layout(self):
        return qt.QVBoxLayout()
    
    def _build_widgets(self):
    
        file_layout = qt.QHBoxLayout()
    
        directory_browse = qt.QPushButton('Browse')
        directory_browse.setMaximumWidth(100)
        
        directory_browse.clicked.connect(self._browser)
        
        file_layout.addWidget(directory_browse)
        
        code_label = qt.QLabel('Paths')
        
        self.code_list = CodeList()
        self.code_list.setAlternatingRowColors(True)
        self.code_list.setSelectionMode(self.code_list.NoSelection)
        self.code_list.directories_changed.connect(self._send_directories)
        
        self.main_layout.addSpacing(5)
        self.main_layout.addWidget(code_label)
        self.main_layout.addWidget(self.code_list)
        self.main_layout.addLayout(file_layout)
        
        self.main_layout.addSpacing(15)
                
    def _text_changed(self, directory):
            
        directory = str(directory)
                
        if not util_file.is_dir(directory):
            return
        
        found = self.code_list.get_directories()
        
        if directory in found:
            return
        
        if found:
            found.insert(0, directory)
            
        if not found:
            found = [directory] 
             
        self.directory_changed.emit(found)
        
        self.code_list.refresh_code_list(found)
        
    def _send_directories(self, directories):
        
        self.directory_changed.emit(directories)
    
    def _browser(self):
        
        filename = qt_ui.get_folder('C:/', self)
        
        if not filename:
            return
        
        filename = util_file.fix_slashes(filename)
        
        if filename and util_file.is_dir(filename):
            self._text_changed(filename)
    
    def set_directory(self, directory):
        
        directory = util.convert_to_sequence(directory)
        
        self.last_directory = self.directory
        self.directory = directory      
        
        self.code_list.refresh_code_list(directory)
    
class CodeList(qt.QListWidget):
    
    directories_changed = qt_ui.create_signal(object)
    
    def __init__(self):
        super(CodeList, self).__init__()
        
        self.setAlternatingRowColors(True)
        self.setSelectionMode(self.NoSelection)

        self.setContextMenuPolicy(qt.QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._item_menu)
        
        self._create_context_menu()
        
    
    def _item_menu(self, position):
        
        item = self.itemAt(position)
        
        if item:
            
            self.context_menu.exec_(self.viewport().mapToGlobal(position))
        
    def _create_context_menu(self):
        
        self.context_menu = qt.QMenu()
        
        remove_action = self.context_menu.addAction('Remove')
        
        remove_action.triggered.connect(self.remove_current_item)
        
    def remove_current_item(self):
        
        index = self.currentIndex()
        self.takeItem(index.row())
        
        self.directories_changed.emit(self.get_directories())
        
    def refresh_code_list(self, directories):
        
        self.clear()
    
        for directory in directories:
            
            name = directory
            
            if not util_file.is_dir(directory):
                name = 'Directory Not Valid!   %s' % directory
            item = qt.QListWidgetItem()
            item.setText(name)
            item.setSizeHint(qt.QtCore.QSize(20, 25))
            
            self.addItem(item)
            
            
    def get_directories(self):
        
        code_count = self.count()
        
        found = []
        
        if code_count:
            
            for inc in range(0, code_count):
            
                item = self.item(inc)
                if item:
                    found.append(str(item.text()))
            
        return found
        
class TemplateDirectoryWidget(ProjectDirectoryWidget):
    
    def _setting_entries(self):
        self.directory_entry = 'template_directory'
        self.history_entry = 'template_history'
        
    def _define_history_list(self):
        return TemplateList() 
    
class TemplateList(ProjectList):
    
    def _setting_entries(self):
        self.directory_entry = 'template_directory'
        self.history_entry = 'template_history'