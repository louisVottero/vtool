# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

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

from vtool.maya_lib import ui_core

from vtool.maya_lib import core
from vtool.maya_lib import rigs_util

import maya.cmds as cmds

class CharacterManager(qt_ui.BasicWidget):

    title = 'Character'
    
    def __init__(self):
        super(CharacterManager, self).__init__()
        
        self.main_layout.setAlignment(QtCore.Qt.AlignTop)
        
    def _build_widgets(self):
        
        self.character_tree = CharacterTree()
        self.character_tree.setMaximumHeight(200)
        self.main_layout.addWidget(self.character_tree)
        
        select_widget = CharacterSelectWidget()
        
        self.main_layout.addWidget(select_widget)
        
class CharacterTree(QTreeWidget):
    
    characters_selected = qt_ui.create_signal(object)
    
    def __init__(self):
        super(CharacterTree, self).__init__()
        
        self.setHeaderHidden(True)
        
        ui_core.new_scene_signal.signal.connect(self.refresh)
        ui_core.open_scene_signal.signal.connect(self.refresh)
        ui_core.read_scene_signal.signal.connect(self.refresh)
        
        self.itemSelectionChanged.connect(self._item_selected)
        
        self.setSelectionMode(self.ExtendedSelection)
        
        self.current_characters = []
        
        self.refresh()
    
    def _item_selected(self):
        
        selected = self.selectedItems()
        
        cmds.select(cl = True)
        
        self.current_characters = []
        
        for select in selected:
            
            namespace = select.text(0)
            
            top_nodes = core.get_top_dag_nodes(namespace = namespace)
            
            cmds.select(top_nodes, add = True)
            
            self.current_characters.append(namespace)
    
        self.characters_selected.emit(self.current_characters)

    
    def refresh(self):
        
        self.clear()
        
        characters = core.get_characters()
        
        self.current_characters = []
        
        for character in characters:
            item = QTreeWidgetItem()
            item.setText(0, character)
            item.setSizeHint(0, QtCore.QSize(30,30) )
            
            self.insertTopLevelItem(0, item)
            
class CharacterSelectWidget(qt_ui.BasicWidget):
    
    def _build_widgets(self):
        
        self._build_select()
    
    def _build_select(self):
        
        self.select_group = qt_ui.Group('Select')
        
        all_controls = QPushButton('All Controls')
        all_controls.clicked.connect(self._select_all_controls)
        
        self.select_group.main_layout.addWidget(all_controls)
        
        self.main_layout.addWidget(self.select_group)
        
    def _select_all_controls(self):
        
        controls = rigs_util.get_controls()
        
        cmds.select(controls)