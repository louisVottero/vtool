# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

from vtool import qt_ui


import ui
import util
import blendshape

import maya.cmds as cmds
import maya.mel as mel

if qt_ui.is_pyqt():
    from PyQt4 import QtGui, QtCore, Qt, uic
if qt_ui.is_pyside():
    from PySide import QtCore, QtGui

class ComboManager(ui.MayaWindow):
    
    title = 'Shape Combo'
    
    def __init__(self):
        super(ComboManager, self).__init__()
        
        self.manager = blendshape.BlendshapeManager()
    
    def _define_main_layout(self):
        layout = QtGui.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)
        
        return layout
        
    def _build_widgets(self):
        
        header_layout = QtGui.QHBoxLayout()
        header_layout.setAlignment(QtCore.Qt.AlignLeft)
        
        button_layout = QtGui.QHBoxLayout()
        self.add = QtGui.QPushButton('New')
        self.add.setMinimumWidth(100)
        self.add.setMinimumHeight(50)
        
        self.add.clicked.connect(self._add_command)
        
        base = QtGui.QPushButton('Base')
        base.setMinimumWidth(100)
        base.setMinimumHeight(50)
        
        base.clicked.connect(self._base_command)
        
        button_layout.addWidget(self.add)
        button_layout.addWidget(base)
        
        header_layout.addLayout(button_layout)
        
        self.shape_widget = ShapeWidget()
        
        self.combo_widget = ComboWidget()
        
        splitter = QtGui.QSplitter()
        
        self.shape_widget.tree.selectionChanged(self._selection_changed)
        
        splitter.addWidget(self.shape_widget)
        splitter.addWidget(self.combo_widget)
        splitter.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding))
        
        self.main_layout.addLayout(header_layout)
        self.main_layout.addWidget(splitter)
        
        self.shape_widget.tree.refresh()
        
    def _selection_changed(self):
        
        item = self.shape_widget.tree.currentItem()
        
        #continue working here
                
    def _base_command(self):
        
        meshes = util.get_selected_meshes()
        
        mesh = None
        if meshes:
            mesh = meshes[0]
        
        self.manager.setup(mesh)
        
    def _add_command(self):
        
        meshes = util.get_selected_meshes()
        
        for mesh in meshes:
            self.manager.add_shape(mesh)
        
        mesh = None
        
        if len(meshes) == 1:
            mesh = meshes[0]
        
        self.shape_widget.tree.refresh(mesh)
        
class ShapeWidget(qt_ui.BasicWidget):
    
    def _build_widgets(self):
        
        header_layout = QtGui.QVBoxLayout()
        
        info_layout = QtGui.QHBoxLayout()
        info_widget = QtGui.QLabel('Shape')
        info_widget.setAlignment(QtCore.Qt.AlignCenter)
        
        info_layout.addWidget(info_widget)
        
        header_layout.addLayout(info_layout)
                
        self.tree = ShapeTree()
        self.tree.setHeaderHidden(True)
        
        self.main_layout.addLayout(header_layout)
        self.main_layout.addWidget(self.tree)

class ShapeTree(qt_ui.TreeWidget):
    def __init__(self):
        super(ShapeTree, self).__init__()
        
        
    def refresh(self, mesh = None):
        
        self.clear()
        
        manager = blendshape.BlendshapeManager()
        targets = manager.get_targets()
        
        select_item = None
        
        for target in targets:
            
            item = QtGui.QTreeWidgetItem()
            item.setSizeHint(0, QtCore.QSize(100, 25))
            
            item.setText(0, target)
            
            self.addTopLevelItem(item)
            
            if target == mesh:
                select_item = item
                
        if select_item:
            self.setItemSelected(select_item, True)
            self.scrollToItem(select_item)

class ComboWidget(qt_ui.BasicWidget):
    
    def _build_widgets(self):
        
        header_layout = QtGui.QVBoxLayout()
        
        info_layout = QtGui.QHBoxLayout()
        info_widget = QtGui.QLabel('Combo')
        info_widget.setAlignment(QtCore.Qt.AlignCenter)
        
        info_layout.addWidget(info_widget)
        
        header_layout.addLayout(info_layout)
        
        self.tree = ComboTree()
        self.tree.setHeaderHidden(True)
        
        self.main_layout.addLayout(header_layout)
        self.main_layout.addWidget(self.tree)

class ComboTree(qt_ui.TreeWidget):
    pass