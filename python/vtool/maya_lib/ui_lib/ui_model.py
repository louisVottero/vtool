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
    
from vtool.maya_lib import geo

class ModelManager(qt_ui.BasicWidget):
    def _build_widgets(self):
        
        self.main_layout.setContentsMargins(20,20,1,1)
        
        grow_edge_loop = QPushButton('Grow Edge Loop')
        grow_edge_loop.setMaximumWidth(100)
        
        grow_edge_loop.clicked.connect(self._grow_edge_loop)
        
        self.main_layout.addWidget(grow_edge_loop)
        
    def _grow_edge_loop(self):
        
        geo.expand_selected_edge_loop()