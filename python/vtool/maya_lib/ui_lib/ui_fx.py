# Copyright (C) 2016 Louis Vottero louis.vot@gmail.com    All rights reserved.

from vtool import qt_ui, qt, util


import ui_character

from vtool.maya_lib import attr
from vtool.maya_lib import fx
from vtool.maya_lib import anim

#this will need a function to check for deadline
if util.has_shotgun_tank():
    from vtool.render_farm import deadline


import maya.cmds as cmds

class FxManager(qt_ui.BasicWidget):
    def _build_widgets(self):
        
        self.main_layout.setContentsMargins(10,10,10,10)
        
        character_tree = ui_character.CharacterTree()
        
        character_tree.characters_selected.connect(self._update_characters)
        character_tree.setMaximumHeight(200)
        
        self.fx_tabs = FxTabWidget()
        
        self.main_layout.addWidget(character_tree)
        self.main_layout.addSpacing(15)
        self.main_layout.addWidget(self.fx_tabs)
        
    def _update_characters(self, characters):
        
        self.fx_tabs.set_namespaces(characters)
        

class FxTabWidget(qt_ui.BasicWidget):
    
    def __init__(self):
        super(FxTabWidget, self).__init__()
        
        self.namespaces = []
        
    def _build_widgets(self):
        
        self.tabs = qt.QTabWidget()
        
        self.settings_widget = FxSettingsWidget()
        self.cache_widget = CacheWidget()
        
        self.tabs.addTab(self.settings_widget,'Presets')
        
        if util.has_shotgun_tank():
            self.tabs.addTab(self.cache_widget, 'Cache')
        
        self.main_layout.addWidget(self.tabs)
        
    def set_namespaces(self, namespaces):
        
        self.namespaces = namespaces
        
        self.settings_widget.set_namespace(namespaces)
        self.cache_widget.set_namespace(namespaces)

class CacheWidget(qt_ui.BasicWidget):
    
    def __init__(self):
        super(CacheWidget, self).__init__()
        self.main_layout.setContentsMargins(10,10,10,10)
        
    def _build_widgets(self):
        
        if util.has_shotgun_tank():
        
            self.min_value = qt_ui.GetInteger('Start Frame')
            self.max_value = qt_ui.GetInteger('End Frame')
            self.max_value.set_value(100)
            update_min_max = qt.QPushButton('Update')
            update_min_max.setMaximumWidth(100)
            
            min_max_layout = qt.QHBoxLayout()
            min_max_layout.addWidget(self.min_value)
            min_max_layout.addWidget(self.max_value)
            min_max_layout.addSpacing(10)
            min_max_layout.addWidget(update_min_max)
        
        
            
            yeti_cache_button = qt.QPushButton('Yeti')
            alembic_cache_button = qt.QPushButton('Alembic')
            maya_cache_button = qt.QPushButton('Maya Cache')
            
            yeti_cache_button.clicked.connect(self._yeti_cache)
            alembic_cache_button.clicked.connect(self._alembic_cache)
            maya_cache_button.clicked.connect(self._maya_cache)
            
            group = qt_ui.Group('Deadline')
            group.main_layout.addWidget(yeti_cache_button)
            group.main_layout.addWidget(alembic_cache_button)
            group.main_layout.addWidget(maya_cache_button)
        
            self.main_layout.addSpacing(10)
            
            self.main_layout.addLayout(min_max_layout)
            self.main_layout.addSpacing(5)

            self.main_layout.addWidget(group)
        
        self.namespaces = []
        
    def _yeti_cache(self):
        
        if not self.namespaces:
            return
        
        for namespace in self.namespaces:
            job = deadline.YetiJob()
            job.set_namespace(namespace)
            
            in_value = self.min_value.get_value()
            out_value = self.max_value.get_value()
            
            job.set_frames(in_value, out_value)
            job.submit()
        
    
    def _alembic_cache(self):
        
        if not self.namespaces:
            return
        
        for namespace in self.namespaces:
            job = deadline.AlembicJob()
            job.set_namespace(namespace)
            
            in_value = self.min_value.get_value()
            out_value = self.max_value.get_value()
            
            job.set_frames(in_value, out_value)
            job.submit()
        
    
    def _maya_cache(self):
        
        if not self.namespaces:
            return
        
        for namespace in self.namespaces:
            job = deadline.MayaCacheJob()
            job.set_namespace(namespace)
            
            in_value = self.min_value.get_value()
            out_value = self.max_value.get_value()
            
            job.set_frames(in_value, out_value)
            job.submit()
        
    def _update_min_max(self):
        
        min_value, max_value = anim.get_min_max_time()
        
        self.min_value.set_value(min_value)
        self.max_value.set_value(max_value)
    
    """    
    def _maya_cache(self):
        

        anim_model = "%s:model" % self.namespaces[0]
        render_model = "%s1:model" % self.namespaces[0]

        fx.export_maya_cache_group(anim_model)
        fx.import_maya_cache_group(render_model, source_group = anim_model)
    """    
    def set_namespace(self, namespaces):
        self.namespaces = namespaces
    


class FxSettingsWidget(qt_ui.BasicWidget):
    
    def __init__(self):
        self.characters = []
        
        
        
        super(FxSettingsWidget, self).__init__()
        
        
        self.main_layout.setContentsMargins(10,10,5,10)
        
    def _build_widgets(self):
        
        self.scroll_area = qt.QScrollArea()
        
        self.main_widget = qt_ui.BasicWidget()
        
        self.scroll_area.setWidget(self.main_widget) 
        self.scroll_area.setWidgetResizable(True)
        
        self.main_layout.addWidget(self.scroll_area)
        
    def create_preset_widgets(self):
        
        layout = self.main_widget.main_layout
        
        while layout.count():
            child = layout.takeAt(0)
            child.widget().deleteLater()
            
        for character in self.characters:
            
            preset = '%s:presets' % character
            
            if not cmds.objExists(preset):
                preset = 'presets'
            
            if cmds.objExists(preset):
                store = attr.StoreData(preset)
                data = store.eval_data()
                
                for item in data:
                    
                    name = item[0]
                    
                    items = item[1]
                
                    setting_tree = SettingWidget()
                    setting_tree.set_header(name)
                    setting_tree.set_namespace(character)   
                    
                    for sub_item in items:
                        
                        sub_name = sub_item[0]
                        sub_value = sub_item[1]
                        
                        setting_tree.add_setting(sub_name, sub_value)         
                    
                    layout.addWidget(setting_tree) 
                    
            if not cmds.objExists(preset):
                
                setting_tree = SettingWidget()
                setting_tree.set_header('No Presets')
                setting_tree.set_namespace(character)
                
                layout.addWidget(setting_tree)
            
    
    def set_namespace(self, character_namespaces):
        
        self.characters = character_namespaces
        self.create_preset_widgets()
        
class SettingWidget(qt_ui.BasicWidget):
    
    def _build_widgets(self):
        
        self.label = qt.QLabel()
        
        self.tree = SettingTree()
        self.tree.hide()
        
        self.main_layout.addWidget(self.label)
        self.main_layout.addWidget(self.tree)
        
    def set_header(self, label):
        self.label.setText(label)
        
    def set_namespace(self, namespace):
        self.namespace = namespace
        self.tree.set_namespace(namespace)
        
    def add_setting(self, name, value):
        self.tree.show()
        self.tree.add_setting(name, value)
        
class SettingTree(qt.QTreeWidget):
    
    def __init__(self):
        super(SettingTree, self).__init__()
        
        self.settings = {}
        self.namespace = None
        
        self.setHeaderHidden(True)
        
        self.itemClicked.connect(self._item_clicked)
        self.itemSelectionChanged.connect(self._item_selected)
        
    def _update_item(self, name):
        
        if self.settings.has_key(name):
            values = self.settings[name]
            
            for value in values:
                node = value[0]
                attributes = value[1]
                
                node_name = '%s:%s' % (self.namespace, node)
                
                if cmds.objExists(node_name):
                
                    attr.set_attribute_values(node_name, attributes)
                    
    def _item_clicked(self):
        
        item = self.currentItem()
        
        current_name = item.text(0)
        
        self._update_item(current_name)
        
    def _item_selected(self):
        
        item = self.currentItem()
        
        current_name = item.text(0)
        
        self._update_item(current_name)
        
    def set_namespace(self, namespace):
        self.namespace = namespace
    
    def set_header(self, header):
        self.setHeaderLabel(header)
    
    def add_setting(self, name, value):
        
        self.settings[name] = value
        
        item = qt.QTreeWidgetItem()
        item.setText(0, name)
        
        self.addTopLevelItem(item)
    
