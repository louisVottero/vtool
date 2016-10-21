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
        
        print 'update characters!', characters
        
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
        for character in self.characters:
            
            preset = '%s:presets' % character
            
            print 'preset', preset
            
            if cmds.objExists(preset):
            
                print 'found preset!!!'
                
                store = attr.StoreData(preset)
                data = store.eval_data()
                
                for item in data:
                    
                    name = item[0]
                    
                    items = item[1]
                    item_count = len(items)
                        
                    number_slider = qt_ui.Slider(name)
                    number_slider.slider.setRange(0, item_count)
                    number_slider.slider.setSingleStep(True)
                    self.main_layout.addWidget(number_slider) 
            
    
    def set_characters(self, character_namespaces):
        
        self.characters = character_namespaces
        
        self.create_preset_widgets()
        
        
        
    
