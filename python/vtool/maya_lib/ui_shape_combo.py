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
        add = QtGui.QPushButton('Add')
        add.setMinimumWidth(100)
        add.setMinimumHeight(50)
        
        add.clicked.connect(self._add_command)
        
        base = QtGui.QPushButton('Base')
        base.setMinimumWidth(100)
        base.setMinimumHeight(50)
        
        base.clicked.connect(self._base_command)
        
        button_layout.addWidget(add)
        button_layout.addWidget(base)
        
        header_layout.addLayout(button_layout)
        
        shape_widget = ShapeWidget()
        
        combo_widget = ComboWidget()
        
        splitter = QtGui.QSplitter()
        
        splitter.addWidget(shape_widget)
        splitter.addWidget(combo_widget)
        splitter.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding))
        
        self.main_layout.addLayout(header_layout)
        self.main_layout.addWidget(splitter)
        
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
                
        
        
        
class ShapeWidget(qt_ui.BasicWidget):
    
    def _build_widgets(self):
        
        header_layout = QtGui.QVBoxLayout()
        
        info_layout = QtGui.QHBoxLayout()
        info_widget = QtGui.QLabel('Shape')
        info_widget.setAlignment(QtCore.Qt.AlignCenter)
        
        info_layout.addWidget(info_widget)
        
        header_layout.addLayout(info_layout)
                
        tree = ShapeTree()
        tree.setHeaderHidden(True)
        
        self.main_layout.addLayout(header_layout)
        self.main_layout.addWidget(tree)

class ShapeTree(qt_ui.TreeWidget):
    pass

class ComboWidget(qt_ui.BasicWidget):
    
    def _build_widgets(self):
        
        header_layout = QtGui.QVBoxLayout()
        
        info_layout = QtGui.QHBoxLayout()
        info_widget = QtGui.QLabel('Combo')
        info_widget.setAlignment(QtCore.Qt.AlignCenter)
        
        info_layout.addWidget(info_widget)
        
        header_layout.addLayout(info_layout)
        
        tree = ComboTree()
        tree.setHeaderHidden(True)
        
        self.main_layout.addLayout(header_layout)
        self.main_layout.addWidget(tree)

class ComboTree(qt_ui.TreeWidget):
    pass