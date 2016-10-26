# Copyright (C) 2016 Louis Vottero louis.vot@gmail.com    All rights reserved.

from vtool import qt_ui,qt
    
from vtool.maya_lib import geo

class ModelManager(qt_ui.BasicWidget):
    def _build_widgets(self):
        
        self.main_layout.setContentsMargins(20,20,1,1)
        
        grow_edge_loop = qt.QPushButton('Grow Edge Loop')
        grow_edge_loop.setMaximumWidth(100)
        
        grow_edge_loop.clicked.connect(self._grow_edge_loop)
        
        self.main_layout.addWidget(grow_edge_loop)
        
    def _grow_edge_loop(self):
        
        geo.expand_selected_edge_loop()