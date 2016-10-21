# Copyright (C) 2016 Louis Vottero louis.vot@gmail.com    All rights reserved.

from vtool import qt_ui

if qt_ui.is_pyqt():
    from PyQt4 import QtCore, Qt, uic
    from PyQt4.QtGui import *
if qt_ui.is_pyside():
    from PySide import QtCore
    from PySide.QtGui import *
if qt_ui.is_pyside2():
    from PySide2 import QtCore
    from PySide2.QtGui import *
    from PySide2.QtWidgets import *

import ui_character

from vtool.maya_lib import attr

import maya.cmds as cmds

class FxManager(qt_ui.BasicWidget):
    def _build_widgets(self):
        
        self.main_layout.setContentsMargins(10,10,10,10)
        
        character_tree = ui_character.CharacterTree()
        
        character_tree.characters_selected.connect(self._update_characters)
        
        self.fx_tabs = FxTabWidget()
        
        self.main_layout.addWidget(character_tree)
        self.main_layout.addWidget(self.fx_tabs)
        
    def _update_characters(self, characters):
        
        self.fx_tabs.set_namespaces(characters)
        

class FxTabWidget(qt_ui.BasicWidget):
    
    def __init__(self):
        super(FxTabWidget, self).__init__()
        
        self.namespaces = []
        
    def _build_widgets(self):
        
        self.tabs = QTabWidget()
        
        self.settings_widget = FxSettingsWidget()
        
        self.tabs.addTab(self.settings_widget,'Presets')
        
        self.main_layout.addWidget(self.tabs)
        
    def set_namespaces(self, namespaces):
        
        self.namespaces = namespaces
        
        self.settings_widget.set_characters(namespaces)

class FxSettingsWidget(qt_ui.BasicWidget):
    
    def __init__(self):
        self.characters = []
        
        super(FxSettingsWidget, self).__init__()
        
    def _build_widgets(self):
        pass
        
    def create_preset_widgets(self):
        
        while self.main_layout.count():
            child = self.main_layout.takeAt(0)
            child.widget().deleteLater()
            
            
        
        for character in self.characters:
            
            preset = '%s:presets' % character
            
            if cmds.objExists(preset):
            
                store = attr.StoreData(preset)
                data = store.eval_data()
                
                for item in data:
                    
                    name = item[0]
                    
                    items = item[1]
                
                    setting_tree = SettingTree()
                    setting_tree.set_header(name)
                    setting_tree.set_namespace(character)   
                    
                    for sub_item in items:
                        
                        sub_name = sub_item[0]
                        sub_value = sub_item[1]
                        
                        setting_tree.add_setting(sub_name, sub_value)         
                    
                    self.main_layout.addWidget(setting_tree) 
            
    
    def set_characters(self, character_namespaces):
        
        self.characters = character_namespaces
        self.create_preset_widgets()
        
        
class SettingTree(QTreeWidget):
    
    def __init__(self):
        super(SettingTree, self).__init__()
    
        self.setMaximumHeight(100)
    
        self.settings = {}
        self.namespace = None
        
        self.itemClicked.connect(self._item_clicked)
        
    def _item_clicked(self):
        
        item = self.currentItem()
        
        current_name = item.text(0)
        
        if self.settings.has_key(current_name):
            values = self.settings[current_name]
            
            for value in values:
                node = value[0]
                attributes = value[1]
                
                node_name = '%s:%s' % (self.namespace, node)
                
                if cmds.objExists(node_name):
                
                    attr.set_attribute_values(node_name, attributes)
                    
        
    def set_namespace(self, namespace):
        self.namespace = namespace
    
    def set_header(self, header):
        self.setHeaderLabel(header)
    
    def add_setting(self, name, value):
        
        self.settings[name] = value
        
        item = QTreeWidgetItem()
        item.setText(0, name)
        
        self.addTopLevelItem(item)
    
