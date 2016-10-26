# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

from vtool import qt_ui, qt
    
from vtool.maya_lib import ui_core

class AnimationManager(qt_ui.BasicWidget):
    def _build_widgets(self):
        pass

"""
        manager_group = qt.QGroupBox('Applications')
        manager_layout = qt.QVBoxLayout()
        manager_layout.setContentsMargins(2,2,2,2)
        manager_layout.setSpacing(2)
        manager_layout.setAlignment(qt.QtCore.Qt.AlignCenter)
        
        manager_group.setLayout(manager_layout)
        
        character_button = qt.QPushButton('Character Manager')
        character_button.clicked.connect(self._character_manager)
        
        manager_layout.addWidget(character_button)
        
        self.main_layout.addWidget(manager_group)
        
    def _character_manager(self):
        
        character_manager()
    
def character_manager():
    
    from vtool.maya_lib.ui_lib import ui_character
    ui_core.create_window(ui_character.CharacterManager())
    
"""