# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

import string

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
    from PyQt4 import QtCore, Qt, uic
    from PyQt4.QtGui import *
if qt_ui.is_pyside():
        from PySide import QtCore
        from PySide.QtGui import *
if qt_ui.is_pyside2():
        from PySide2 import QtCore
        from PySide2.QtGui import *
        from PySide2.QtWidgets import *

class ComboManager(ui.MayaWindow):
    
    title = 'Shape Combo'
    
    def __init__(self):
        super(ComboManager, self).__init__()
        
        self.manager = blendshape.ShapeComboManager()
        self.refresh_combo_list = True
        self.combo_select_update = True
        
        self.shape_widget.tree.manager = self.manager
        self.update_on_select = True
        self.shape_widget.tree.shape_renamed.connect(self._shape_renamed)
        #self._refresh()
    
    def _define_main_layout(self):
        layout = QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)
        
        return layout
        
    def _build_widgets(self):
        
        header_layout = QVBoxLayout()
        header_layout.setAlignment(QtCore.Qt.AlignLeft)
        
        
        self.add = QPushButton('ADD')
        self.add.setMinimumWidth(100)
        self.add.setMaximumWidth(200)
        self.add.setMinimumHeight(50)
        
        self.add.clicked.connect(self._add_command)
        
        layout_1 = QVBoxLayout()
        
        self.slider = WeightSlider()
        self.slider.value_change.connect(self._update_value)
        
        header_layout.addSpacing(5)
        header_layout.addWidget(self.slider)
        header_layout.addSpacing(5)
        
        self.preserve_check = QCheckBox('Preserve Combos')
        
        recreate_all = QPushButton('Recreate All')
        recreate_all.setMaximumWidth(100)
        recreate_all.clicked.connect(self._recreate_all)
        
        to_default = QPushButton('To Default')
        to_default.setMaximumWidth(100)
        to_default.clicked.connect(self._to_default)
        
        
        layout_1.addWidget(recreate_all)
        layout_1.addWidget(to_default)

        button_layout = QHBoxLayout()
        button_layout.setAlignment(QtCore.Qt.AlignLeft)
        button_layout.addWidget(self.add)
        button_layout.addSpacing(10)
        button_layout.addLayout(layout_1)
        button_layout.addSpacing(10)
        button_layout.addWidget(self.preserve_check)
        
        self.preserve_check.stateChanged.connect(self._preserve_state_change)
                
        header_layout.addLayout(button_layout)
        
        base = QPushButton('Set')
        
        base.setMinimumWidth(50)
        base.setMaximumWidth(100)
        #base.setMinimumHeight(20)
        
        base.clicked.connect(self._set_base)
        
        self.current_base = QLabel('    Base: -')
        self.current_base.setMaximumWidth(300)
        
        layout_base = QHBoxLayout()
        layout_base.setAlignment(QtCore.Qt.AlignLeft)
        layout_base.addWidget(base)
        layout_base.addWidget(self.current_base)
        
        header_layout.addSpacing(5)
        header_layout.addLayout(layout_base)
        header_layout.addSpacing(5)
        
        self.shape_widget = ShapeWidget()
        
        self.combo_widget = ComboWidget()
        
        splitter = QSplitter()
        
        self.shape_widget.tree.itemSelectionChanged.connect(self._shape_selection_changed)
        self.combo_widget.tree.itemSelectionChanged.connect(self._combo_selection_changed)
        
        splitter.addWidget(self.shape_widget)
        splitter.addWidget(self.combo_widget)
        splitter.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))
        splitter.setSizes([120,200])
        
        self.main_layout.addWidget(splitter)
        self.main_layout.addLayout(header_layout)
        
    def _preserve_state_change(self):
        
        pass_state = False
        
        state = self.preserve_check.checkState()
        
        if state == QtCore.Qt.Checked:
            pass_state = True
            
        if state == QtCore.Qt.Unchecked:
            pass_state = False
        
        self.shape_widget.tree.preserve_state = pass_state
        
    def _refresh(self):
        
        shapes = self.manager.get_shapes()
        
        state = self.preserve_check.checkState()
        
        preserve = False
        if state > 0:
            preserve = True
        
        if shapes:
            self._add_meshes(shapes, preserve, ui_only = True)

    def _get_selected_shapes(self):
        
        shape_items = self.shape_widget.tree.selectedItems()
        
        if not shape_items:
            return
        
        shapes = []
        
        for item in shape_items:
            name = str(item.text(0))
            
            shapes.append(name)
            
        return shapes
    
    def _update_slider_for_shapes(self, shapes):
        
        if not shapes:
            self.slider.setDisabled(True)
            return
        
        if shapes:
            self.slider.setEnabled(True)
            
            self.slider.set_value(1)
        
    def _shape_selection_changed(self):
        
        if not self.update_on_select:
            return
        
        self.manager.zero_out()
        
        shape_items = self.shape_widget.tree.selectedItems()
        
        #handle corresponding shape selected.
        if len(shape_items) > 1:
            
            test_item = shape_items[-1]
            test_name = test_item.text(0)
            
            previous_item = shape_items[-2]
            previous_name = previous_item.text(0)
            
            inbetween_parent = self.manager.get_inbetween_parent(test_name)
            if inbetween_parent:
                test_name = inbetween_parent

            negative_parent = self.manager.get_negative_parent(test_name)
            if negative_parent:
                test_name = negative_parent
            
            inbetween_parent = self.manager.get_inbetween_parent(previous_name)
            if inbetween_parent:
                previous_name = inbetween_parent
            
            negative_parent = self.manager.get_negative_parent(previous_name)
            if negative_parent:
                previous_name = negative_parent
                
            if previous_name == test_name:
                self.update_on_select = False
                previous_item.setSelected(False)
                self.update_on_select = True
            
            #handle parent selected... clear children.
            child_count = shape_items[-1].childCount()
                
            if child_count:
                for inc in range(0, child_count):
                    if shape_items[-1].child(inc).isSelected():
                        shape_items[-1].child(inc).setSelected(False)
            
        #handle, is a child, clear parent and sibling.
        shape_items = self.shape_widget.tree.selectedItems()
        
        for item in shape_items:
            parent = item.parent()

            if parent:
                
                parent.setSelected(False)
                
                self.update_on_select = False
                self.shape_widget.tree.setCurrentItem(item)
                self.update_on_select = True
                
                child_count = parent.childCount()
            
                if child_count:
                    for inc in range(0, child_count):
                        if item.text(0) != parent.child(inc).text(0):
                            parent.child(inc).setSelected(False)
        
        shapes = self._get_selected_shapes()
        
        if self.refresh_combo_list:
            if shapes:
                
                self.update_on_select = False
                self.refresh_combo_list = False
                
                self.combo_widget.tree.clearSelection()
                shapes.sort()
                
                self._update_combo_selection(shapes)
                self.update_on_select = True
                self.refresh_combo_list = True
                
        self._update_slider_for_shapes(shapes)
        
    def _combo_selection_changed(self):
        
        if not self.combo_select_update:
            return
        
        combo_items = self.combo_widget.tree.selectedItems()
        
        if not combo_items:
            
            return
        
        combo_name = str(combo_items[0].text(0))
        
        shapes = self.manager.get_shapes_in_combo(combo_name)
        
        #if self.manager.blendshape.is_target(combo_name):
            
            #self.manager.set_shape_weight(combo_name, 1)
            
        self.refresh_combo_list = False
        self.update_on_select = False
        self.shape_widget.tree.select_shapes(shapes)
        self._update_slider_for_shapes(shapes)
        self.refresh_combo_list = True
        self.update_on_select = True
        
    def _update_combo_selection(self, shapes):
        
        if not self.combo_select_update:
            return
        #if not shapes:
        #    self.combo_widget.tree.clear()
        #    return
                
        combos = self.manager.get_combos()
        possible_combos = self.manager.find_possible_combos(shapes)
        
        self.combo_select_update = False
        self.combo_widget.tree.load(combos, possible_combos, shapes)
        self.combo_select_update = True
    
    def _set_base(self):
        
        self.shape_widget.tree.clear()
        self.combo_widget.tree.clear()
        
        meshes = geo.get_selected_meshes()
        
        if not meshes:
            selected = cmds.ls(sl = True, type = 'transform')
            
            if selected:
                if self.manager.is_shape_combo_manager(selected[0]):
                    self.manager.load(selected[0])
                    mesh = self.manager.get_mesh()
                    self.current_base.setText('    Base: ' + mesh)
                
                if not self.manager.setup_group:
                    self.current_base.setText('    Base: -')
        
        if meshes:
            mesh = None
            if meshes:
                mesh = meshes[0]
            
            self.manager.create(mesh)
            
            self.current_base.setText('    Base: ' + mesh)

        self.shape_widget.tree.set_manager(self.manager)
        self.combo_widget.tree.set_manager(self.manager)
            
        self._refresh()
        
    def _get_selected_items(self):
        
        combo_items = self.combo_widget.tree.selectedItems()
        shape_items = self.shape_widget.tree.selectedItems()
        
        shapes = []
        inbetweens = []
        
        for shape_item in shape_items:
            
            if shape_item.parent():
                inbetweens.append(shape_item)
               
            if not shape_item.parent():
                shapes.append(shape_item) 
        
        return shapes, combo_items, inbetweens
    
    def _add_mesh(self, mesh):
        
        shape_items, combo_items, inbetween_items = self._get_selected_items()
        
        if combo_items and len(combo_items) == 1:
            combo_name = str(combo_items[0].text(0))
            self.manager.add_combo( combo_name, mesh )
            self.combo_widget.tree.highlight_item(combo_items[0])
            
        if shape_items and not combo_items and not inbetween_items and len(shape_items) == 1:

            shape_name = str(shape_items[0].text(0))
            self.manager.add_shape(shape_name, mesh)
            
            self.shape_widget.tree.select_shape(shape_name)
        
        if inbetween_items and not combo_items and not shape_items and len(inbetween_items) == 1:
            item = inbetween_items[0]
            name = inbetween_items[0].text(0)
            self.manager.add_shape(name, mesh)
            
            brush = QBrush()
            color = QColor()
            color.setRgb(200,200,200)
            brush.setColor(color)
            item.setForeground(0, brush)
            
        if not combo_items and not shape_items and not inbetween_items:
            self._add_meshes([mesh])
            
    def _add_meshes(self, meshes, preserve, ui_only = False):
        
        for mesh in meshes:
            if mesh.find('|') > -1:
                nice_name = core.get_basename(mesh)
                qt_ui.warning('%s is not unique. Aborting ADD.' % nice_name, self)
                return
                
                
        shapes = None
        
        if ui_only:
            inbetweens = self.manager.get_inbetweens()
        if not ui_only:
            shapes, combos, inbetweens = self.manager.add_meshes(meshes, preserve)
        
        self.shape_widget.tree.load(inbetweens = inbetweens)
        self.combo_widget.tree.load() 
        
        if shapes and len(shapes) == 1:
            self.shape_widget.tree.select_shape(shapes[0])
    
    def _add_command(self):
        
        if not self.manager.get_mesh():
            vtool.util.warning('No base mesh set.')
            return
        
        meshes = geo.get_selected_meshes()
        
        #mesh_count = len(meshes)
        
        #if mesh_count == 1:
            
        #    self._add_mesh(meshes[0])
            
        #if mesh_count > 1:
        #    self._add_meshes(meshes)
        
        state = self.preserve_check.checkState()
        
        preserve = False
        if state > 0:
            preserve = True
            
        self._add_meshes(meshes, preserve)
        
    def _shape_renamed(self, shape):
        
        self.combo_widget.tree.load()
        
    def _recreate_all(self):
        
        self.manager.recreate_all()
            
    def _to_default(self):
        
        self.manager.zero_out()
        self.shape_widget.tree.clearSelection()
            
    def _update_value(self, value):
        
        self.manager.zero_out()
        
        shapes = self._get_selected_shapes()
        
        if not shapes:
            return
        
        for shape in shapes:
            
            self.manager.turn_on_shape(shape, value)
            
class ShapeWidget(qt_ui.BasicWidget):
    
    def _build_widgets(self):
        
        header_layout = QVBoxLayout()
        
        info_layout = QHBoxLayout()
        info_widget = QLabel('Shape')
        info_widget.setAlignment(QtCore.Qt.AlignCenter)
        
        info_layout.addWidget(info_widget)
        
        header_layout.addLayout(info_layout)
                
        self.tree = ShapeTree()
        self.tree.setHeaderHidden(True)
        
        self.main_layout.addLayout(header_layout)
        self.main_layout.addWidget(self.tree)

class ShapeTree(qt_ui.TreeWidget):
    
    shape_renamed = qt_ui.create_signal(object)
    
    def __init__(self):
        
        self.text_edit = False
        self.preserve_state = False
        self.update_selection = True
        
        super(ShapeTree, self).__init__()
        
        self.text_edit = False
        
        self.setSortingEnabled(False)
        
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._item_menu)
        
        self._create_context_menu()
        
        self.manager = None
        
        self.ctrl_active = False
        
        self.doubleClicked.connect(self.recreate)

        self.left_press = False
        
        
        
    def _item_menu(self, position):
                
        item = self.itemAt(position)
        
        parent = item.parent()
        
        if parent:
            self.rename_action.setVisible(False)
            
        if not parent:
            self.rename_action.setVisible(True)
            
        name = item.text(0)
        
        if self.manager.is_negative(name):
            self.rename_action.setVisible(False)
        
        self.context_menu.exec_(self.viewport().mapToGlobal(position))
        
    def _create_context_menu(self):
        
        self.context_menu = QMenu()
        
        self.recreate_action = self.context_menu.addAction('Recreate')
        
        self.rename_action = self.context_menu.addAction('Rename')
        
        self.remove_action = self.context_menu.addAction('Remove')
        self.context_menu.addSeparator()
        
        self.recreate_action.triggered.connect(self.recreate)
        self.rename_action.triggered.connect(self.rename)
        self.remove_action.triggered.connect(self.remove)
        
    def _create_item(self, shape, inbetweens = None):
        
        item = QTreeWidgetItem()
        item.setSizeHint(0, QtCore.QSize(100, 18))
        
        item.setText(0, shape)
        
        self.addTopLevelItem(item)
        
        self._create_children(item, inbetweens)
        
        return item
        
    def _create_children(self, item, inbetweens = None):
        
        for inc in range(item.childCount(), -1, -1):
            child_item = item.child(inc)
            item.removeChild(child_item)
        
        shape = str(item.text(0))
        
        if not inbetweens:
            inbetweens = self.manager.get_inbetweens(shape)
        
        default_inbetweens = ['75','50','25']
        
        existing = []
        
        child_dict = {}
        children = []
        
        for inbetween in default_inbetweens:
            
            name = '%s%s' % (shape, inbetween)
            
            child_item = self._create_child_item(name)
            
            if not self.manager.blendshape.is_target(name):
                self._highlight_child(child_item, False)
                
            if self.manager.blendshape.is_target(name):
                self._highlight_child(child_item, True)
                existing.append(name)
                
            child_dict[name] = child_item
            children.append(name)
                
        for inbetween in inbetweens:
            
            if not inbetween in existing:
                child_item = self._create_child_item(inbetween)
                
                self._highlight_child(child_item, True)
                
                child_dict[inbetween] = child_item
                children.append(inbetween)
            
        children.sort()
        children.reverse()
                
        for child in children:
            child_item = child_dict[child]
            item.addChild(child_item)
        
    def _create_child_item(self, name, parent = None):
        
        child_item = QTreeWidgetItem(parent)
        child_item.setSizeHint(0, QtCore.QSize(100, 15))
        child_item.setText(0, name)
        
        return child_item
        
    def _highlight_child(self, item, bool_value = True):
        
        if bool_value:
            font = item.font(0)
            font.setBold(True)
            item.setFont(0, font)
            
            brush = QBrush()
            color = QColor()
            color.setRgb(200,200,200)
            brush.setColor(color)
            item.setForeground(0, brush)
        
        if not bool_value:
            brush = QBrush()
            color = QColor()
            color.setRgb(100,100,100)
            brush.setColor(color)
            
            item.setForeground(0, brush)
    
    def _get_item(self, name):
        
        for inc in range(0, self.topLevelItemCount()):
            
            item = self.topLevelItem(inc)
            if item.text(0) == name:
                return item
            
    def keyPressEvent(self, event):
        ctrl_key = QtCore.Qt.Key_Control
        shift_key = QtCore.Qt.Key_Shift
        
        if event.key() == ctrl_key or event.key() == shift_key:
            self.ctrl_active = True
            
        if event.key() != ctrl_key and event.key() != shift_key:
            self.ctrl_active = False
        
        super(ShapeTree, self).keyPressEvent(event)
        
    def keyReleaseEvent(self, event):
        
        ctrl_key = QtCore.Qt.Key_Control
        shift_key = QtCore.Qt.Key_Shift
        
        if event.key() == ctrl_key or event.key() == shift_key:
            self.ctrl_active = False
        
        super(ShapeTree, self).keyReleaseEvent(event)

    def selectionCommand(self, index, event):
        
        if not self.update_selection:
            return
        
        self.update_selection = False
        
        modifiers = QApplication.keyboardModifiers()
        
        if modifiers == QtCore.Qt.ControlModifier or modifiers == QtCore.Qt.ShiftModifier:
            self.ctrl_active = True
        
        mouse = QApplication.mouseButtons()
        if mouse == QtCore.Qt.LeftButton:
            self.left_press = True
        if not mouse == QtCore.Qt.LeftButton:
            self.left_press = False
            
        if not event:
            
            self.update_selection = True
            return QItemSelectionModel.NoUpdate
        
        if event.button() == QtCore.Qt.LeftButton:
            
            if self.left_press:
                
                item = None
                
                if not self.ctrl_active:
                    
                    self.clearSelection()
                
                parent_index = index.parent().row()
                
                if parent_index > -1:
                    parent_item = self.topLevelItem(parent_index)
                    item = parent_item.child(index.row())
                    
                if parent_index == -1:
                    item = self.topLevelItem(index.row())
                
                if item:
                    
                    if not item.isSelected():
                        
                        self.setItemSelected(item, True)
                        self.update_selection = True
                        return QItemSelectionModel.Select
                    
                    if item.isSelected():    
                        
                        self.setItemSelected(item, False)
                        self.update_selection = True
                        return QItemSelectionModel.Deselect
                
            if not self.left_press:
                self.update_selection = True
                return QItemSelectionModel.NoUpdate
        
        self.update_selection = True
        
    
    def recreate(self):
        
        items = self.selectedItems()
        
        if not items:
            return
        
        for item in items:
            
            name = item.text(0)
            
            new_shape = name
            
            if not cmds.objExists(name):
                new_shape = self.manager.recreate_shape(name)
            
            new_shape_list = cmds.ls(new_shape)
            match_count = len(new_shape_list)
            
            if match_count == 1:
                self.manager.add_shape(name, new_shape, preserve_combos = self.preserve_state)
            
            if match_count > 1:
                vtool.util.warning('Shape not updated. More than one object matches %s. Selecting all.' % new_shape)
                
            cmds.select(new_shape_list)
            
            
            
            parent = item.parent()
            if parent:
                self._highlight_child(item, True)
        
    def rename(self):
        
        items = self.selectedItems()
        
        if not items:
            return
        
        item = items[0]
        
        old_name = str(item.text(0))
        
        new_name = qt_ui.get_new_name('New name', self, item.text(0))
        
        new_name = vtool.util.clean_name_string(new_name)
        
        if new_name == old_name:
            return
        
        new_name = self.manager.rename_shape(old_name, new_name)
        
        if not new_name:
            return
        
        item.setText(0, new_name)
        self.manager.set_shape_weight(new_name, 1)
        
        self._create_children(item)
        
        negative = self.manager.get_negative_name(old_name)
        negative_item = self._get_item(negative)
        
        new_negative = self.manager.get_negative_name(new_name)
        new_negative_item = self._get_item(new_negative)
        
        if new_negative_item:
            if negative_item:
                index = self.indexFromItem(negative_item)
                self.takeTopLevelItem(index.row())
            
        if not new_negative_item:
            if negative_item:
                negative_item.setText(0, new_negative) 
                self._create_children(negative_item)
            
        
        self.shape_renamed.emit(new_name)
        
    def remove(self):
        
        items = self.selectedItems()
        
        if not items:
            return
        
        for item in items:
        
            name = item.text(0)
            
            self.manager.remove_shape(name)
            
            if self.manager.is_inbetween(name):
                self._highlight_child(item, False)
                self.setItemSelected(item, False)
            
            if not self.manager.is_inbetween(name):
                index = self.indexFromItem(item)
                self.takeTopLevelItem(index.row())
                
    def select_shape(self, shape):
        
        for inc in range(0, self.topLevelItemCount()):
            item = self.topLevelItem(inc)
            
            item_name = str(item.text(0))
            
            if item_name == shape:
                item.setSelected(True)
        
    def select_shapes(self, shapes):
        
        self.clearSelection()
        
        for inc in range(0, self.topLevelItemCount()):
            
            item = self.topLevelItem(inc)
            
            item_name = str(item.text(0))
            
            if item_name in shapes:
                item.setSelected(True)
                
            if not item_name in shapes:
                for inc in range(0, item.childCount()):
                    child_item = item.child(inc)
                    child_name = str(child_item.text(0))
                    
                    if child_name in shapes:
                        child_item.setSelected(True)
                        self.expandItem(item)
                        
                        
        count = self.topLevelItemCount()
        
        for inc in range(0, count):
            
            collapse = True
            
            item = self.topLevelItem(inc)
            
            child_count = item.childCount()
            
            if child_count:
                for inc2 in range(0, child_count):
                    if item.child(inc2).isSelected():
                        collapse = False
                        break
            
            if collapse:
                item.setExpanded(False)
        
    def load(self, mesh = None, inbetweens = None):
        
        self.clear()
        
        shapes = self.manager.get_shapes()
        
        select_item = None
        
        for shape in shapes:
            
            if self.manager.is_inbetween(shape):
                continue

            shape_betweens = []

            for inbetween in inbetweens:
                
                front_part = inbetween[:-2]
                
                if front_part == shape:
                    shape_betweens.append(inbetween)

            item = self._create_item(shape, shape_betweens)
            
            if shape == mesh:
                select_item = item
                
        if select_item:
            self.setItemSelected(select_item, True)
            self.scrollToItem(select_item)
            
    def set_manager(self, manager):
        self.manager = manager

class ComboWidget(qt_ui.BasicWidget):
    
    def _build_widgets(self):
        
        header_layout = QVBoxLayout()
        
        info_layout = QHBoxLayout()
        info_widget = QLabel('Combo')
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
        
        self.text_edit = False
        
        self.setSortingEnabled(False)
        
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._item_menu)
        
        self._create_context_menu()
        
        self.doubleClicked.connect(self.recreate)
        
    def _item_menu(self, position):
        
        self.context_menu.exec_(self.viewport().mapToGlobal(position))
        
    def _create_context_menu(self):
        
        self.context_menu = QMenu()
        
        self.recreate_action = self.context_menu.addAction('Recreate')
        self.remove_action = self.context_menu.addAction('Remove')
        
        self.recreate_action.triggered.connect(self.recreate)
        self.remove_action.triggered.connect(self.remove)
        
    def highlight_item(self, item, bool_value = True):
        
        brush = None
        font = item.font(0)
        
        if bool_value:
            font = item.font(0)
            font.setBold(True)
            
            brush = QBrush()
            color = QColor()
            color.setRgb(200,200,200)
            brush.setColor(color)
        
        if not bool_value:
            
            font.setBold(False)
            brush = QBrush()
            color = QColor()
            color.setRgb(100,100,100)
            brush.setColor(color)
        
        item.setForeground(0, brush)
        item.setFont(0, font)
        
    def recreate(self):
        
        items = self.selectedItems()
        
        if not items:
            return
        
        name = str(items[0].text(0))
        
        new_combo = name
        
        if not cmds.objExists(name):
            new_combo = self.manager.recreate_combo(name)
            
        
        
        self.highlight_item(items[0], True)
        
        new_combo_list = cmds.ls(new_combo)
        match_count = len(new_combo_list)
        
        if match_count == 1:
            self.manager.add_combo(name, new_combo)
        
        if match_count > 1:
            vtool.util.warning('Shape not updated. More than one object matches %s. Selecting all.' % new_combo)
            
        cmds.select(new_combo_list)
        
    def remove(self):

        items = self.selectedItems()
        
        if not items:
            return
        
        name = str(items[0].text(0))
        
        self.manager.remove_combo(name)
        
        self.highlight_item(items[0], False)
        self.setItemSelected(items[0], False)
    
    def load(self, combos = None, possible_combos = None, current_shapes = None):
        
        if not combos:
            combos = self.manager.get_combos()
        
        self.clear()
        
        for combo in combos:
            item = QTreeWidgetItem()
            item.setSizeHint(0, QtCore.QSize(100, 20))
            item.setText(0, combo)
            self.highlight_item(item)
            
            self.addTopLevelItem(item)
            
            current_combo = None
            if current_shapes:
                current_combo = string.join(current_shapes, '_')
            
            if current_combo == item.text(0):
            
                item.setSelected(True)
            
            if possible_combos:
            
                if combo in possible_combos:
                    index = possible_combos.index(combo)
                    possible_combos.pop(index)
        
        if possible_combos:
            for combo in possible_combos:
                
                item = QTreeWidgetItem()
                item.setSizeHint(0, QtCore.QSize(100, 18))
                item.setText(0, combo)
                
                self.highlight_item(item, False)
                
                
                self.addTopLevelItem(item)
                
        
    
    def set_manager(self, manager):
        self.manager = manager
        
        
class WeightSlider(qt_ui.BasicWidget):
    
    value_change = qt_ui.create_signal(object)
    
    def __init__(self):
        super(WeightSlider, self).__init__()
        
    def _define_main_layout(self):
        return QHBoxLayout()

    def _build_widgets(self):
        
        self.value = QDoubleSpinBox()
        self.value.setMinimum(0)
        self.value.setMaximum(1)
        self.value.setDecimals(3)
        
        self.value.setMinimumWidth(60)
        self.value.setButtonSymbols(self.value.NoButtons)
        
        self.slider = QSlider()
        self.slider.setMinimum(0)
        self.slider.setMaximum(1000)
        self.slider.setTickPosition(self.slider.TicksBelow)
        
        self.slider.setTickInterval(250)
        self.slider.setSingleStep(100)
        
        self.slider.setOrientation(QtCore.Qt.Horizontal)
        self.slider.setMinimumWidth(80)
        
        self.main_layout.addWidget(self.value)
        self.main_layout.addSpacing(10)
        self.main_layout.addWidget(self.slider)
        self.main_layout.addSpacing(10)
        
        self.slider.valueChanged.connect(self._slider_value_change)
        self.value.valueChanged.connect(self._value_change)
        
        self.update_value = True
        self.update_slider = True
        
        self.setDisabled(True)
        
    def _slider_value_change(self):
        
        if not self.update_slider:
            return
        
        self.update_value = False
        value = self.slider.value()
        self.value.setValue(value*0.001)
        self.update_value = True
        
        self.value_change.emit(value*0.001)
        
    def _value_change(self):
        
        if not self.update_value:
            return
        
        self.update_slider = False
        value = self.value.value()
        self.slider.setValue(value*1000)
        self.update_slider = True
        
        self.value_change.emit(value)
        
    def set_min_max(self, min_value, max_value):
        
        self.value.setMinimum(min_value)
        self.value.setMaximum(max_value)
        
        self.slider.setMinimum(min_value*1000)
        self.slider.setMaximum(max_value*1000)
        
    def set_value(self, value):
        
        self.slider.setValue(value*1000)
        
        self.value_change.emit( value )
        
