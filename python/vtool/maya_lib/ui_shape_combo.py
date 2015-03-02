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
        self.manager.zero_out()
        self.refresh_combo_list = True
        
        self.shape_widget.tree.manager = self.manager
    
    def _define_main_layout(self):
        layout = QtGui.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)
        
        return layout
        
    def _build_widgets(self):
        
        header_layout = QtGui.QHBoxLayout()
        header_layout.setAlignment(QtCore.Qt.AlignLeft)
        
        button_layout = QtGui.QVBoxLayout()
        self.add = QtGui.QPushButton('Shape')
        self.add.setMinimumWidth(100)
        self.add.setMinimumHeight(50)
        
        self.add.clicked.connect(self._add_command)
        
        base = QtGui.QPushButton('Home')
        base.setMinimumWidth(100)
        base.setMinimumHeight(25)
        
        base.clicked.connect(self._base_command)
        
        button_layout.addSpacing(10)
        button_layout.addWidget(base)
        button_layout.addSpacing(10)
        button_layout.addWidget(self.add)
        
        
        header_layout.addLayout(button_layout)
        
        self.shape_widget = ShapeWidget()
        
        self.combo_widget = ComboWidget()
        
        splitter = QtGui.QSplitter()
        
        self.shape_widget.tree.itemSelectionChanged.connect(self._shape_selection_changed)
        self.combo_widget.tree.itemSelectionChanged.connect(self._combo_selection_changed)
        
        
        splitter.addWidget(self.shape_widget)
        splitter.addWidget(self.combo_widget)
        splitter.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding))
        
        self.main_layout.addLayout(header_layout)
        self.main_layout.addSpacing(10)
        self.main_layout.addWidget(splitter)
        
        self.shape_widget.tree.refresh()

    def _get_selected_shapes(self):
        
        items = self.shape_widget.tree.selectedItems()
        
        if not items:
            return
        
        shapes = []
        
        for item in items:
            name = str(item.text(0))
        
            shapes.append(name)
            
        return shapes
        
    def _shape_selection_changed(self):
        
        self.manager.zero_out()
        
        shapes = self._get_selected_shapes()
        
        if self.refresh_combo_list:
            self._update_combo_selection(shapes)
            
        if not shapes:
            return
            
        for shape in shapes:
            self.manager.set_shape_weight(shape, 1)
            
        
               
    def _combo_selection_changed(self):
        
        items = self.combo_widget.tree.selectedItems()
        
        if not items:
            return
        
        combo_name = str(items[0].text(0))
        
        shapes = self.manager.get_shapes_in_combo(combo_name)
        
        self.refresh_combo_list = False
        self.shape_widget.tree.select_shapes(shapes)
        self.refresh_combo_list = True
        
        
    def _update_combo_selection(self, shapes):
        
        if not shapes:
            self.combo_widget.tree.clear()
            return
                
        combos = self.manager.get_combos(shapes)
        
        if not combos:
            self.combo_widget.tree.clear()
            return
        
        self.combo_widget.tree.load(combos)
    
    def _base_command(self):
        
        meshes = util.get_selected_meshes()
        
        mesh = None
        if meshes:
            mesh = meshes[0]
        
        self.manager.setup(mesh)
        
        self.shape_widget.tree.clearSelection()
        #self.manager.zero_out()
        
        
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
        
        self.setSelectionMode(self.ExtendedSelection)
        
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._item_menu)
        
        self._create_context_menu()
        
        self.manager = None
        
    def _item_menu(self, position):
                
        item = self.itemAt(position)
        
        self.context_menu.exec_(self.viewport().mapToGlobal(position))
        
    def _create_context_menu(self):
        
        self.context_menu = QtGui.QMenu()
        
        self.create_action = self.context_menu.addAction('Remove')
        self.context_menu.addSeparator()
        
        self.create_action.triggered.connect(self.remove)
        
    def remove(self):
        
        items = self.selectedItems()
        
        if not items:
            return
        
        for item in items:
        
            self.manager.remove_shape(item.text(0))
        
            index = self.indexFromItem(item)
        
            self.takeTopLevelItem(index.row())
        
    def select_shapes(self, shapes):
        self.clearSelection()
        
        for inc in range(0, self.topLevelItemCount()):
            
            item = self.topLevelItem(inc)
            
            item_name = str(item.text(0))
            
            if item_name in shapes:
                item.setSelected(True)
        
    def refresh(self, mesh = None):
        
        self.clear()
        
        manager = blendshape.BlendshapeManager()
        shapes = manager.get_shapes()
        
        select_item = None
        
        for shape in shapes:
            
            item = QtGui.QTreeWidgetItem()
            item.setSizeHint(0, QtCore.QSize(100, 25))
            
            item.setText(0, shape)
            
            self.addTopLevelItem(item)
            
            if shape == mesh:
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
    
    def load(self, combos):
        
        self.clear()
        
        if not combos:
            return
        
        for combo in combos:
            item = QtGui.QTreeWidgetItem()
            item.setText(0, combo)
            
            self.addTopLevelItem(item)