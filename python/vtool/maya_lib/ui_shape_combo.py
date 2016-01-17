# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

from vtool import qt_ui
import vtool.util
import ui

if vtool.util.is_in_maya():

    import maya.cmds as cmds
    import maya.mel as mel
    import blendshape
    import geo
    import core

if qt_ui.is_pyqt():
    from PyQt4 import QtGui, QtCore, Qt, uic
if qt_ui.is_pyside():
    from PySide import QtCore, QtGui

class ComboManager(ui.MayaWindow):
    
    title = 'Shape Combo'
    
    def __init__(self):
        super(ComboManager, self).__init__()
        
        self.manager = blendshape.BlendshapeManager()
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
        
        self.shape_widget.tree.load()
        self.combo_widget.tree.load()

    def _get_selected_shapes(self):
        
        shape_items = self.shape_widget.tree.selectedItems()
        
        if not shape_items:
            return
        
        shapes = []
        
        for item in shape_items:
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
        
        combo_items = self.combo_widget.tree.selectedItems()
        
        if not combo_items:
            return
        
        combo_name = str(combo_items[0].text(0))
        
        shapes = self.manager.get_shapes_in_combo(combo_name)
        
        if self.manager.blendshape.is_target(combo_name):
            self.manager.set_shape_weight(combo_name, 1)
            
        self.refresh_combo_list = False
        self.shape_widget.tree.select_shapes(shapes)
        self.refresh_combo_list = True
        
    def _update_combo_selection(self, shapes):
        
        if not shapes:
            self.combo_widget.tree.clear()
            return
                
        combos = self.manager.get_combos()
        possible_combos = self.manager.find_possible_combos(shapes)
        
        self.combo_widget.tree.load(combos, possible_combos)
    
    def _base_command(self):
        
        meshes = geo.get_selected_meshes()
        
        mesh = None
        if meshes:
            mesh = meshes[0]
        
        self.manager.setup(mesh)
        
        self.shape_widget.tree.clearSelection()
        #self.manager.zero_out()
        
    def _add_mesh(self, mesh):
        combo_items = self.combo_widget.tree.selectedItems()
        shape_items = self.combo_widget.tree.selectedItems()
        
        if combo_items and len(combo_items) == 1:
            combo_name = str(combo_items[0].text(0))
            self.manager.add_combo( combo_name, mesh)
                    
        if not combo_items and len(shape_items) == 1:
            shape_name = str(shape_items[0].text(0))
            self.manager.add_shape(shape_name, mesh)
            
        if not combo_items and not shape_items:
            self._add_meshes([mesh])
        
    def _add_meshes(self, meshes):
        shapes, combos, inbetweens = self.manager.get_shape_and_combo_lists(meshes)
        
        for shape in shapes:
            self.manager.add_shape(shape)    
        
        for combo in combos:
            for mesh in meshes:
                if mesh == combo:
                    self.manager.add_combo(mesh)
    
    def _add_command(self):
        
        meshes = geo.get_selected_meshes()
        mesh_count = len(meshes)
        
        if mesh_count == 1:
            self._add_mesh(meshes[0])
        
        if mesh_count > 1:
            self._add_meshes(meshes)
            
        if meshes:
            mesh = meshes[-1]
            self.shape_widget.tree.load(mesh)
            self.combo_widget.tree.load()            
            

        
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
        
        self.text_edit = False
        
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
        
        self.rename_action = self.context_menu.addAction('Rename')
        
        self.remove_action = self.context_menu.addAction('Remove')
        self.context_menu.addSeparator()
        
        self.rename_action.triggered.connect(self.rename)
        self.remove_action.triggered.connect(self.remove)
        
    def rename(self):
        
        items = self.selectedItems()
        
        if not items:
            return
        
        item = items[0]
        
        old_name = str(item.text(0))
        
        new_name = qt_ui.get_new_name('New name', self, item.text(0))
        
        new_name = vtool.util.clean_name_string(new_name)
        
        new_name = self.manager.rename_shape(old_name, new_name)
        
        if new_name == old_name:
            return
        
        item.setText(0, new_name)
        self.manager.set_shape_weight(new_name, 1)
        
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
        
    def load(self, mesh = None):
        
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
    
    def __init__(self):
        super(ComboTree, self).__init__()
        
        self.setSortingEnabled(False)
    
    def load(self, combos = None, possible_combos = None):
        
        if not combos:
            manager = blendshape.BlendshapeManager()
            combos = manager.get_combos()
        
        self.clear()
        
        for combo in combos:
            item = QtGui.QTreeWidgetItem()
            item.setSizeHint(0, QtCore.QSize(100, 25))
            item.setText(0, combo)
            font = item.font(0)
            font.setBold(True)
            item.setFont(0, font)
            
            self.addTopLevelItem(item)
            
            if possible_combos:
            
                if combo in possible_combos:
                    index = possible_combos.index(combo)
                    possible_combos.pop(index)
        
        if possible_combos:
            for combo in possible_combos:
                
                item = QtGui.QTreeWidgetItem()
                item.setSizeHint(0, QtCore.QSize(100, 25))
                item.setText(0, combo)
                
                self.addTopLevelItem(item)
                   