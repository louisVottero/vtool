# Copyright (C) 2022 Louis Vottero louis.vot@gmail.com    All rights reserved.

from __future__ import absolute_import

from .. import logger
log = logger.get_logger(__name__) 

from .. import qt_ui, qt
from .. import util_file
from .. import util

class SettingsWidget(qt_ui.BasicWindow):
    
    project_directory_changed = qt_ui.create_signal(object)
    template_directory_changed = qt_ui.create_signal(object)
    code_directory_changed = qt_ui.create_signal(object)
    code_text_size_changed = qt_ui.create_signal(object)
    code_expanding_tab_changed = qt_ui.create_signal(object)
    data_expanding_tab_changed = qt_ui.create_signal(object)
    data_sidebar_visible_changed = qt_ui.create_signal(object)
    
    title = 'Process Settings'
    
    def __init__(self, parent = None):
        
        super(SettingsWidget, self).__init__(parent = parent)
        
        self.code_directories = []
        self.template_history = []
        self.settings = None
        
    def sizeHint(self):
        return qt.QtCore.QSize(550,600)
        
    def _define_main_layout(self):
        layout = qt.QVBoxLayout()
        
        return layout 
    
    def _build_widgets(self):
        
        self.setContentsMargins(1,1,1,1)
        
        self.hint = qt.QLabel('Hit the Settings Button in Vetala to see settings.')
        self.browse = qt.QPushButton('Browse')
        self.browse.clicked.connect(self._open_browser)
        self.browse.hide()
        self.browse.setMaximumWidth(util.scale_dpi(70))
        self.browse.setMaximumHeight(util.scale_dpi(20))
        
        self.tab_widget = qt.QTabWidget()
        self.tab_widget.hide()
        
        self.dir_widget = qt_ui.BasicWidget()
        
        
        self.project_directory_widget = ProjectDirectoryWidget()
        self.project_directory_widget.directory_changed.connect(self._project_directory_changed)
        
        self.code_directory_widget = CodeDirectoryWidget()
        self.code_directory_widget.directory_changed.connect(self._code_directory_changed)

        self.template_directory_widget  = TemplateDirectoryWidget()
        self.template_directory_widget.directory_changed.connect(self._template_directory_changed)

        option_scroll_widget = self._build_option_widgets()

        self.tab_widget.addTab(self.project_directory_widget, 'Project')
        self.tab_widget.addTab(option_scroll_widget, 'Settings')
        #self.tab_widget.addTab(self.code_directory_widget, 'External Code')
        self.tab_widget.addTab(self.template_directory_widget, 'Template')
        
        self.main_layout.addSpacing(util.scale_dpi(5))
        self.main_layout.addWidget(self.browse, alignment = qt.QtCore.Qt.AlignRight)
        self.main_layout.addSpacing(util.scale_dpi(5))
        self.main_layout.addWidget(self.tab_widget)
        self.main_layout.addWidget(self.hint)
        
    def _build_option_widgets(self):
        
        self.options_widget = qt_ui.BasicWidget()
        self.options_widget.main_layout.setSpacing(5)
        self.options_widget.main_layout.setContentsMargins(1,1,1,1)
        
        scroll = qt.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.options_widget)
        
        self.process_group = ProcessGroup()
        
        self.code_tab_group = CodeTabGroup()
        self.code_tab_group.code_text_size_changed.connect(self.code_text_size_changed)
        self.code_tab_group.code_expanding_tab_changed.connect(self.code_expanding_tab_changed)
        
        self.shotgun_group = ShotgunGroup()
        self.deadline_group = DeadlineGroup()
        
        self.options_widget.main_layout.addWidget(self.process_group)        
        self.options_widget.main_layout.addWidget(self.code_tab_group)
        
        self.data_tab_group = DataTabGroup()
        self.data_tab_group.data_expanding_tab_changed.connect(self.data_expanding_tab_changed)
        self.data_tab_group.data_sidebar_visible_changed.connect(self.data_sidebar_visible_changed)
        
        self.options_widget.main_layout.addWidget(self.data_tab_group)
        
        self.options_widget.main_layout.addWidget(self.shotgun_group)
        self.options_widget.main_layout.addWidget(self.deadline_group)
        
        self.process_group.collapse_group()
        self.shotgun_group.collapse_group()
        self.deadline_group.collapse_group()
        self.code_tab_group.collapse_group()
        
        scroll.setWidget(self.options_widget)
        
        return scroll
    
    def _project_directory_changed(self, project):
        
        self.project_directory_changed.emit(project)
        
    def _template_directory_changed(self, project):
        self.template_directory_changed.emit(project)
        
    def _code_directory_changed(self, code_directory):
        self.code_directory_changed.emit(code_directory)
    
    def _open_browser(self):
        filepath = self.settings.filepath
        
        util_file.open_browser( util_file.get_dirname(filepath) )
    
    def get_project_directory(self):
        return self.project_directory_widget.get_directory()
        
    def set_project_directory(self, directory):
        self.project_directory_widget.set_directory(directory, set_setting=False)
    
    def set_template_directory(self, directory):
        self.template_directory_widget.set_directory(directory, set_setting=False)
        
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
        self.code_tab_group.editor_directory_widget.set_settings(settings)
        
        self.process_group.set_settings(settings)
        self.shotgun_group.set_settings(settings)
        self.deadline_group.set_settings(settings)
        self.code_tab_group.set_settings(settings)
        self.data_tab_group.set_settings(settings)
        self.template_directory_widget.set_settings(settings)
        
        self.tab_widget.show()
        self.browse.show()
        self.hint.hide()
        
    def refresh_template_list(self):
        
        current = self.settings.get('template_directory')
        history = self.settings.get('template_history')
        
        self.template_directory_widget.list.refresh_list(current, history)


class ProcessGroup(qt_ui.Group):

    def __init__(self):
        super(ProcessGroup, self).__init__('Process')
        
    def _build_widgets(self):
        
        
        self.backup_directory = qt_ui.GetDirectoryWidget()
        self.backup_directory.set_label('Backup Directory')
        self.backup_directory.directory_changed.connect(self._set_backup_directory)
        
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
        
        self.main_layout.addWidget(self.backup_directory)
        self.main_layout.addWidget(self.error_stop)
        self.main_layout.addWidget(process_maya_group)
        
    def _set_backup_directory(self, directory):
        self.settings.set('backup_directory', directory)
        
    def _set_stop_on_error(self):
        self.settings.set('stop_on_error', self.error_stop.get_state())
        
    def _set_start_new_scene_on_process(self):
        
        self.settings.set('start_new_scene_on_process', self.process_start_new_scene.get_state())
        
    def _set_auto_focus_scene(self):
        
        self.settings.set('auto_focus_scene', self.auto_focus_scene.get_state())
        
    def _get_backup_directory(self):
        backup = self.settings.get('backup_directory')
        self.backup_directory.set_directory(backup)
        
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
            
    def set_settings(self, settings):
        
        self.settings = settings
        
        self._get_backup_directory()
        self._get_stop_on_error()
        self._get_start_new_scene_on_process()
        self._get_auto_focus_scene()
  
class SettingGroup(qt_ui.Group):     
    
    def __init__(self, name):
        self._setting_insts = []
        super(SettingGroup, self).__init__(name)
        self.collapse_group()
        
    def set_settings(self, settings):
        
        self.settings = settings
        
        for setting_inst in self._setting_insts:
            setting_inst.set_setting_inst(self.settings)
            setting_inst.get_setting()
        
    def add_setting(self, setting_inst):
        
        self._setting_insts.append(setting_inst)
        
        self.main_layout.addWidget(setting_inst)

class SettingWidget(qt_ui.BasicWidget):
    
    changed = qt.create_signal(object) 
    
    def __init__(self, title, setting_name = None):
        self.settings = None
        super(SettingWidget, self).__init__()
        self.title = title
        self.widget = self._define_widget(title)
        if setting_name:
            self._setting_name = setting_name
        if not setting_name:
            self._setting_name = self.title
        
        self.main_layout.addWidget(self.widget)
        
        self._customize()
        self._build_signals()
    
    def _define_widget(self, title):
        return None 
    
    def _build_signals(self):
        return
    
    def _customize(self):
        return
    
    def get_setting(self):
        value = self.settings.get(self._setting_name)
        if value != None:
            self.set_value(value)
        return value
    
    def set_setting(self):
        
        value =  self.get_value()
        
        
        
        if self.settings:
            self.settings.set(self._setting_name,value)
            
        self.changed.emit(value)
    
    def set_setting_inst(self, setting_inst):
        self.settings = setting_inst
    
    def set_value(self, value):
        return
        
    def get_value(self):
        return

class IntSettingWidget(SettingWidget):
    
    def _define_widget(self, title):
        return qt_ui.GetInteger(title)
    
    def _customize(self):
        self.widget.main_layout.setAlignment(qt.QtCore.Qt.AlignLeft)
    
    def _build_signals(self):
        self.widget.valueChanged.connect(self.set_setting)
        
    
    def set_value(self, value):
        self.widget.set_value(value)
        
    def get_value(self):
        return  self.widget.get_value()

class BoolSettingWidget(SettingWidget):
    
    def _define_widget(self, title):
        return qt_ui.GetBoolean(title)
    
    def _customize(self):
        self.widget.main_layout.setAlignment(qt.QtCore.Qt.AlignLeft)
    
    def _build_signals(self):
        self.widget.valueChanged.connect(self.set_setting)
    
    def set_value(self, value):
        self.widget.set_value(value)
        
    def get_value(self):
        return  self.widget.get_value()

class DataTabGroup(SettingGroup):
    
    data_expanding_tab_changed = qt.create_signal(object)
    data_sidebar_visible_changed = qt.create_signal(object)
    group_title = 'Data Tab'
    
    def __init__(self):
        super(DataTabGroup, self).__init__(self.group_title)
        
    def _build_widgets(self):
        
        expand_label = qt.QLabel('Expand Splitter When Data Tab Selected')
        self.expand_tab = BoolSettingWidget('Expand Tab', 'data expanding tab')
        self.main_layout.addWidget(expand_label)
        self.add_setting(self.expand_tab)
        self.main_layout.addSpacing(util.scale_dpi(10))
        self.expand_tab.changed.connect(self._set_expand_tab)
        
        sidebar_visible = BoolSettingWidget('Side Bar Visible', 'side bar visible')
        self.add_setting(sidebar_visible)
        sidebar_visible.set_value(1)
        sidebar_visible.changed.connect(self._set_side_bar)
        self.sidebar_visible = sidebar_visible
        
    
    def _set_expand_tab(self):
        value = self.expand_tab.get_value()
        self.data_expanding_tab_changed.emit(value)
        
    def _set_side_bar(self):
        value = self.sidebar_visible.get_value()
        self.data_sidebar_visible_changed.emit(value)
    
class CodeTabGroup(SettingGroup):
    
    code_text_size_changed = qt.create_signal(object)
    code_expanding_tab_changed = qt.create_signal(object)
    group_title = 'Code Tab'
    
    def __init__(self):
        super(CodeTabGroup, self).__init__(self.group_title)
    
    def _build_widgets(self):
        
        expand_label = qt.QLabel('Expand Splitter When Code Tab Selected')
        self.expand_tab = BoolSettingWidget('Expand Tab', 'code expanding tab')
        self.main_layout.addWidget(expand_label)
        self.add_setting(self.expand_tab)
        self.expand_tab.changed.connect(self._set_expand_tab)
        
        self.editor_directory_widget = ExternalEditorWidget()
        self.editor_directory_widget.set_label('External Editor')
        
        self.code_text_size = IntSettingWidget('Code Text Size', 'code text size')
        
        self.code_text_size.widget.number_widget.setMinimum(14)
        self.code_text_size.widget.number_widget.setMaximum(23)
        self.code_text_size.set_value(8)
        self.code_text_size.changed.connect(self.code_text_size_changed)
        self.add_setting(self.code_text_size)
        
        label = qt.QLabel('Manifest Double Click')
        self.open_tab = qt.QRadioButton("Open In Tab")
        self.open_new = qt.QRadioButton("Open In New Window")
        self.open_external = qt.QRadioButton("Open In External")
        
        
        self.pop_save = qt_ui.GetCheckBox('Ctrl+S code save pop up for comment.')
        self.pop_save.set_state(True)
        self.pop_save.check_changed.connect(self._set_pop_save)
        
        
        
        self.open_tab.setChecked(True)
        
        self.open_tab.setAutoExclusive(True)
        self.open_new.setAutoExclusive(True)
        self.open_external.setAutoExclusive(True)
        
        self.open_tab.toggled.connect(self._set_manifest_double_click)
        self.open_new.toggled.connect(self._set_manifest_double_click)
        self.open_external.toggled.connect(self._set_manifest_double_click)
        
        
        
        
        
        self.main_layout.addSpacing(util.scale_dpi(10))
        
        self.main_layout.addWidget(self.editor_directory_widget)
        self.main_layout.addSpacing(util.scale_dpi(10))
        self.main_layout.addWidget(label)
        self.main_layout.addWidget(self.open_tab)
        self.main_layout.addWidget(self.open_new)
        self.main_layout.addWidget(self.open_external)
        self.main_layout.addSpacing(12)
        
        self.main_layout.addWidget(qt.QLabel('Code Text Size has limits\nMinimum: 14\nMaximum: 23'))
        self.main_layout.addWidget(self.code_text_size)
        self.main_layout.addWidget(self.pop_save)
        
    def _get_manifest_double_click(self):
        value = self.settings.get('manifest_double_click')
        if value:
            if value == 'open tab':
                self.open_tab.setChecked(True)
            if value == 'open new':
                self.open_new.setChecked(True)
            if value == 'open external':
                self.open_external.setChecked(True)
        
    def _get_popup_save(self):
        value = self.settings.get('code popup save')
        
        if value != None:
            self.pop_save.set_state(value)
        
    def _get_code_text_size(self):
        
        value = self.settings.get('code text size')
        if value != None:
            self.code_text_size.set_value(value)

    def _set_manifest_double_click(self):
        
        value = 'open tab'
        
        if self.open_new.isChecked():
            value = 'open new'
        if self.open_external.isChecked():
            value = 'open external'
            
        self.settings.set('manifest_double_click', value)
        
    def _set_pop_save(self):
        
        self.settings.set('code popup save', self.pop_save.get_state())
        
    def _set_code_text_size(self):
        
        value =  self.code_text_size.get_value()
        
        self.settings.set('code text size',value)
        self.code_text_size_changed.emit(value)

    def _set_expand_tab(self):
        value = self.expand_tab.get_value()
        self.code_expanding_tab_changed.emit(value)

    def set_settings(self, settings):
        super(CodeTabGroup, self).set_settings(settings)
        self.settings = settings
        
        self._get_manifest_double_click()
        self._get_popup_save() 

class ShotgunGroup(qt_ui.Group):
    
    def __init__(self):
        super(ShotgunGroup, self).__init__('Shotgun Settings')
    
    def _build_widgets(self):
        super(ShotgunGroup,self)._build_widgets()
        
        #self.get_shotgun_url = qt_ui.GetString('Webpage')
        self.get_shotgun_name = qt_ui.GetString('Script Name')
        self.get_shotgun_code = qt_ui.GetString('Application Key')
        
        self.get_shotgun_asset_publish_code = qt_ui.GetString('Publish Template')
        self.get_shotgun_asset_publish_code.set_text('maya_asset_publish')
        self.get_shotgun_asset_work_code = qt_ui.GetString('Work Template')
        self.get_shotgun_asset_work_code.set_text('maya_asset_work')
        
        url_label = qt.QLabel('Optionally if your studio does not use sgtk, then provide the shotgun url.')
        self.get_shotgun_url = qt_ui.GetString('Shotgun Url')
        self.get_shotgun_url.set_placeholder('https://yourstudio.shotgunstudio.com')
        
        self.get_shotgun_url.text_entry.returnPressed.connect(self._check_url)
        self.api_url_passed = qt.QLabel(' Works ')
        self.api_url_passed.setStyleSheet("QLabel { background-color : lightGreen; color : black; }")
        self.api_url_passed.hide()
        
        
        toolkit_warning = qt.QLabel('If "import sgtk" is not in your PYTHONPATH,\nload the folder above the python module sgtk:')
        self.get_shotgun_toolkit = ShotgunToolkitWidget()
        
        
        self.get_shotgun_name.text_changed.connect(self._set_shotgun_name)
        self.get_shotgun_code.text_changed.connect(self._set_shotgun_code)
        self.get_shotgun_url.text_changed.connect(self._set_shotgun_url)
        
        self.get_shotgun_asset_publish_code.text_changed.connect(self._set_shotgun_asset_publish_code)
        self.get_shotgun_asset_work_code.text_changed.connect(self._set_shotgun_asset_work_code)
        
        
        #self.main_layout.addWidget(self.get_shotgun_url)
        self.main_layout.addWidget(self.get_shotgun_name)
        self.main_layout.addWidget(self.get_shotgun_code)
        self.main_layout.addSpacing(20)
        self.main_layout.addWidget(url_label)
        self.main_layout.addWidget(self.get_shotgun_url)
        self.main_layout.addWidget(self.api_url_passed)
        self.main_layout.addSpacing(20)
        self.main_layout.addWidget(self.get_shotgun_asset_publish_code)
        self.main_layout.addWidget(self.get_shotgun_asset_work_code)
        self.main_layout.addSpacing(20)
        
        self.main_layout.addWidget(toolkit_warning)
        self.main_layout.addWidget(self.get_shotgun_toolkit)

    def _check_url(self):
        script_name = self.get_shotgun_name.get_text()
        script_code = self.get_shotgun_code.get_text()
        script_url = self.get_shotgun_url.get_text()
        
        sg = None
        try:
            import shotgun_api3
        except:
            util.warning('Could not access shotgun_api3')
        try:
            sg = shotgun_api3.Shotgun(script_url, script_name, script_code)
        except:
            util.warning('Could not access shotgun ui using, %s, %s, %s' % (script_url, script_name, script_code))
        
        if sg:
            self.api_url_passed.show()
        if not sg:
            self.api_url_passed.hide()
        

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
        
        self._get_shotgun_name()
        self._get_shotgun_code()
        self._get_shotgun_url()
        
        self._get_shotgun_asset_publish_code()
        self._get_shotgun_asset_work_code()

class DeadlineGroup(qt_ui.Group):
    
    def __init__(self):
        super(DeadlineGroup, self).__init__('Deadline Settings')
    
    def _build_widgets(self):
        super(DeadlineGroup,self)._build_widgets()
        
        self.deadline_directory = qt_ui.GetDirectoryWidget()
        self.deadline_directory.set_label('Deadline Command Directory')
        self.deadline_directory.directory_changed.connect(self._set_deadline_directory)
        self.deadline_directory.set_show_files(True)
        
        if util.is_linux():
            self.deadline_directory.set_example('/opt/Thinkbox/Deadline7/bin')
        else:
            self.deadline_directory.set_example('/Thinkbox/Deadline7/bin')
            
        self.vtool_directory = qt_ui.GetDirectoryWidget()
        self.vtool_directory.set_label('Deadline relative vtool Directory.')
        self.vtool_directory.directory_changed.connect(self._set_vtool_directory)
        self.vtool_directory.set_show_files(True)
        
        drive_label = qt.QLabel('Remapping the drive is only necessary if the drive has been remapped in deadline.\nLive blank otherwise')
        
        self.drive_letter = qt_ui.GetString('Drive Original')
        self.remap_drive = qt_ui.GetString('Remap Drive')
        
        self.drive_letter.text_changed.connect(self._set_drive_letter)
        self.remap_drive.text_changed.connect(self._set_remap_drive)
        
        self.get_deadline_pool = qt_ui.GetString('Pool')
        self.get_deadline_group = qt_ui.GetString('Group')
        self.get_deadline_department = qt_ui.GetString('Department')
        
        self.get_deadline_pool.text_changed.connect(self._set_deadline_pool)
        self.get_deadline_group.text_changed.connect(self._set_deadline_group)
        self.get_deadline_department.text_changed.connect(self._set_deadline_department)
        
        self.main_layout.addWidget(self.deadline_directory)
        self.main_layout.addWidget(self.vtool_directory)
        self.main_layout.addSpacing(10)
        self.main_layout.addWidget(drive_label)
        self.main_layout.addWidget(self.drive_letter)
        self.main_layout.addWidget(self.remap_drive)
        self.main_layout.addSpacing(10)
        self.main_layout.addWidget(self.get_deadline_pool)
        self.main_layout.addWidget(self.get_deadline_group)
        self.main_layout.addWidget(self.get_deadline_department)
        
    def _set_deadline_directory(self, directory):
        
        self.settings.set('deadline_directory', directory)
        
        if not util_file.has_deadline():
            self.deadline_directory.set_error(True)
            
    def _set_vtool_directory(self, directory):
        
        self.settings.set('deadline_vtool_directory', directory)
                
    def _set_deadline_pool(self):
        self.settings.set('deadline_pool', str(self.get_deadline_pool.get_text()))
    
    def _set_deadline_group(self):
        self.settings.set('deadline_group', str(self.get_deadline_group.get_text()))
    
    def _set_deadline_department(self):
        self.settings.set('deadline_department', str(self.get_deadline_department.get_text()))
        
    def _set_drive_letter(self):
        self.settings.set('deadline_orig_path_drive', str(self.drive_letter.get_text()))
        
        
    def _set_remap_drive(self):
        self.settings.set('deadline_remap_path_drive', str(self.remap_drive.get_text()))
        
    def _get_deadline_directory(self):
        path = self.settings.get('deadline_directory')
        self.deadline_directory.set_directory(path)
        
    def _get_vtool_directory(self):
        path = self.settings.get('deadline_vtool_directory')
        self.vtool_directory.set_directory(path)
        
    def _get_deadline_pool(self):
        value = self.settings.get('deadline_pool')
        if value:
            self.get_deadline_pool.set_text(value)
    
    def _get_deadline_group(self):
        value = self.settings.get('deadline_group')
        if value:
            self.get_deadline_group.set_text(value)
    
    def _get_deadline_department(self):
        value = self.settings.get('deadline_department')
        if value:
            self.get_deadline_department.set_text(value)
            
    def _get_driver_letter(self):
        value = self.settings.get('deadline_orig_path_drive')
        if value:
            self.drive_letter.set_text(value)
            
    def _get_remap_drive(self):
        value = self.settings.get('deadline_remap_path_drive')
        if value:
            self.remap_drive.set_text(value) 
    
    def set_settings(self, settings):
        
        self.settings = settings
        self._get_deadline_directory()
        self._get_vtool_directory()
        self._get_driver_letter()
        self._get_remap_drive()
        self._get_deadline_pool()
        self._get_deadline_group()
        self._get_deadline_department()
        

class ExternalEditorWidget(qt_ui.GetDirectoryWidget):
    
    def __init__(self, parent = None):
           
        super(ExternalEditorWidget, self).__init__(parent)
        
        self.directory_browse_button.setText('Load Executable')
        
        self.settings = None
        
    def _browser(self):
        
        filename = qt_ui.get_file(self.get_directory() , self)
        
        if filename:
        
            if util_file.is_file(filename):
                filename = util_file.fix_slashes(filename)
                self.directory_edit.setText(filename)
                self.directory_changed.emit(filename)
                self.settings.set('external_editor', str(filename))
    
    def _text_edited(self, text):
        super(ExternalEditorWidget, self)._text_edited(text)
        
        self.settings.set('external_editor', str(text))
    
    def set_settings(self, settings):
        
        self.settings = settings
        
        filename = self.settings.get('external_editor')
        
        self.set_directory(filename)
        
class ShotgunToolkitWidget(qt_ui.GetDirectoryWidget):
    
    def __init__(self, parent = None):
           
        super(ShotgunToolkitWidget, self).__init__(parent)
        
        self.set_label('Shotgun Toolkit Path')
        
        self.settings = None
        
        self.api_passed = qt.QLabel(' Works ')
        self.api_passed.setStyleSheet("QLabel { background-color : lightGreen; color : black; }")
        self.api_passed.hide()
        self.main_layout.addWidget(self.api_passed)
        
        self.directory_edit.setPlaceholderText('example: C:/shotgun_install_name/install/core/python')

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
        
        if filename:
        
            if util_file.is_dir(str(filename)):
                self.set_directory(filename)
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
        
        directory_browse = qt.QPushButton('Add Directory')
        directory_browse.setMaximumWidth(util.scale_dpi(100))
        
        directory_browse.clicked.connect(self._browser)
        
        file_layout.addWidget(directory_browse)
        
        self.list = self._define_history_list()
        self.list.setAlternatingRowColors(True)
        if util.in_houdini:
            self.list.setAlternatingRowColors(False)        
        self.list.setSelectionMode(self.list.SingleSelection)
        self.list.directories_changed.connect(self._send_directories)
        self.list.itemClicked.connect(self._item_selected)
        
        self.main_layout.addSpacing(5)
        
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
        
    def _send_directories(self, directory):
        log.info('Send directory %s' % directory)
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
        
    def set_directory(self, directory, set_setting = True):
        
        history = None
        
        if not directory:
            return
        
        if self.settings:
            history = self.settings.get(self.history_entry)
        
        if type(directory) != list:
            directory = ['', str(directory)]
        
        if set_setting:
            self.settings.set(self.directory_entry, directory[1])
        
        self.list.refresh_list(directory, history)
        
        self.list.select(directory)
            
    def set_settings(self, settings):
        
        self.settings = settings
        self.list.set_settings(settings)
        history = self.settings.get(self.history_entry)
        directory = self.settings.get(self.directory_entry)
        self.list.refresh_list(directory, history)
        

class ProjectList(qt.QTreeWidget):

    directories_changed = qt_ui.create_signal(object)

    def __init__(self):
        super(ProjectList, self).__init__()
        
        self.setAlternatingRowColors(True)
        if util.in_houdini:
            self.setAlternatingRowColors(False)        
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
        
        log.info('Remove current project %s' % item.text(1))
        
        self.takeTopLevelItem(index.row())
        
        project = self.settings.get('project_directory')
        
        if project == item.text(1):
            log.info('Remove directory change emitted')
            self.directories_changed.emit('')
        
        directories = self.get_directories()
        
        if self.settings:
            self.settings.set(self.history_entry, directories)
            if directories:
                self.settings.set(self.directory_entry, directories[0][1])
            if not directories:
                self.settings.set(self.directory_entry, None)
                
        self.clearSelection()
        log.info('Done Remove current project %s' % index)
        
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
    
        directory_browse = qt.QPushButton('Add Code Directory')
        directory_browse.setMaximumWidth(200)
        
        directory_browse.clicked.connect(self._browser)
        
        file_layout.addWidget(directory_browse)
        
        code_label = qt.QLabel('Paths')
        
        self.code_list = CodeList()
        self.code_list.setAlternatingRowColors(True)
        if util.in_houdini:
            self.code_list.setAlternatingRowColors(False)
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
        if util.in_houdini:
            self.setAlternatingRowColors(False)
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