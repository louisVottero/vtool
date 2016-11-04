# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

from vtool import qt_ui, qt
from vtool.maya_lib.ui_lib import ui_character
    
from vtool.maya_lib import ui_core

from vtool.maya_lib import rigs_util

class AnimationManager(qt_ui.BasicWidget):
    def _build_widgets(self):
        
        self.main_layout.setContentsMargins(10,10,10,10)
        
        character_tree = ui_character.CharacterTree()
        
        character_tree.characters_selected.connect(self._update_characters)
        character_tree.setMaximumHeight(200)
        
        self.animation_tabs = AnimTabWidget()
        
        self.main_layout.addWidget(character_tree)
        self.main_layout.addSpacing(15)
        self.main_layout.addWidget(self.animation_tabs)
        
    def _update_characters(self, characters):
        
        self.animation_tabs.set_namespaces(characters)

class AnimTabWidget(qt_ui.BasicWidget):
    
    def __init__(self):
        super(AnimTabWidget, self).__init__()
        
        self.namespaces = []
        
    def _build_widgets(self):
        
        self.tabs = qt.QTabWidget()
        
        self.settings_widget = AnimControlWidget()
        
        self.tabs.addTab(self.settings_widget,'Utilities')
        
        
        self.main_layout.addWidget(self.tabs)
        
    def set_namespaces(self, namespaces):
        
        self.namespaces = namespaces
        
        self.settings_widget.set_namespaces(namespaces)
        
        
class AnimControlWidget(qt_ui.BasicWidget):
    
    def __init__(self):
        super(AnimControlWidget, self).__init__()
        
        self.main_layout.setContentsMargins(10,10,10,10)
        
        self.namespaces = []
    
    def _build_widgets(self):
        
        select_controls = qt.QPushButton('Select All Controls')
        select_controls.setMaximumWidth(150)
        select_controls.clicked.connect(self._select_all_controls)
        
        
        key_controls = qt.QPushButton('Key All Controls')
        key_controls.setMaximumWidth(150)
        key_controls.clicked.connect(self._key_all_controls)
        
        
        self.main_layout.addWidget(select_controls)
        self.main_layout.addSpacing(10)
        #self.main_layout.addWidget(mirror_controls)
        #self.main_layout.addWidget(flip_controls)
        self.main_layout.addWidget(key_controls)
        #self.main_layout.addWidget(flip_controls)
        
    def set_namespaces(self, namespaces):
        
        self.namespaces = namespaces
        
    def _select_all_controls(self):
        
        namespace = ''
        
        if self.namespaces:
            namespace = self.namespaces[0]
        
        rigs_util.select_controls(namespace)
        
    def _key_all_controls(self):
        
        namespace = ''
        
        if self.namespaces:
            namespace = self.namespaces[0]
            
        rigs_util.key_controls(namespace)
        