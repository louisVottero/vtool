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

class AnimationManager(qt_ui.BasicWidget):
    def _build_widgets(self):
        pass

"""
        manager_group = QGroupBox('Applications')
        manager_layout = QVBoxLayout()
        manager_layout.setContentsMargins(2,2,2,2)
        manager_layout.setSpacing(2)
        manager_layout.setAlignment(QtCore.Qt.AlignCenter)
        
        manager_group.setLayout(manager_layout)
        
        character_button = QPushButton('Character Manager')
        character_button.clicked.connect(self._character_manager)
        
        manager_layout.addWidget(character_button)
        
        self.main_layout.addWidget(manager_group)
        
    def _character_manager(self):
        
        character_manager()
    
def character_manager():
    
    from vtool.maya_lib.ui_lib import ui_character
    ui_core.create_window(ui_character.CharacterManager())
    
"""