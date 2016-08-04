# Copyright (C) 2016 Louis Vottero louis.vot@gmail.com    All rights reserved.

import ui
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
        
import maya.cmds as cmds
import rigs_util

class CharacterManager(ui.MayaWindow):

    title = 'Character'
    
    def __init__(self):
        super(CharacterManager, self).__init__()
        
        self.main_layout.setAlignment(QtCore.Qt.AlignTop)
        
    def _build_widgets(self):
        
        self.character_tree = CharacterTree()
        self.character_tree.setMaximumHeight(200)
        self.main_layout.addWidget(self.character_tree)
        
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
        
class CharacterTree(QTreeWidget):
    
    def __init__(self):
        super(CharacterTree, self).__init__()
        
        self.setHeaderHidden(True)
        
        ui.new_scene_signal.signal.connect(self.refresh)
        ui.open_scene_signal.signal.connect(self.refresh)
        ui.read_scene_signal.signal.connect(self.refresh)
        
        self.refresh()
    
    def refresh(self):
        
        self.clear()
        
        characters = get_characters()
        
        for character in characters:
            item = QTreeWidgetItem()
            item.setText(0, character)
            item.setSizeHint(0, QtCore.QSize(30,30) )
            
            self.insertTopLevelItem(0, item)

def get_characters():
    
    namespaces = cmds.namespaceInfo(lon = True)
    
    found = []
    
    for namespace in namespaces:
        
        if cmds.objExists('%s:controls' % namespace):
            found.append(namespace)
            
    return found
