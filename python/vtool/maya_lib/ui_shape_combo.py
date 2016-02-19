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
    
    title = 'Shape Combo -Alpha-'
    
    def __init__(self):
        super(ComboManager, self).__init__()
        
        self.manager = blendshape.ShapeComboManager()
        self.refresh_combo_list = True
        
        self.shape_widget.tree.manager = self.manager
        self.update_on_select = True
        #self._refresh()
    
    def _define_main_layout(self):
        layout = QtGui.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)
        
        return layout
        
    def _build_widgets(self):
        
        header_layout = QtGui.QHBoxLayout()
        header_layout.setAlignment(QtCore.Qt.AlignLeft)
        
        layout_1 = QtGui.QHBoxLayout()
        base = QtGui.QPushButton('Set')
        #base.setMinimumWidth(100)
        base.setMaximumWidth(100)
        base.setMinimumHeight(25)
        
        base.clicked.connect(self._set_base)
        
        self.current_base = QtGui.QLabel('-')
        
        layout_1.addWidget(base)
        layout_1.addSpacing(10)
        layout_1.addWidget(self.current_base)
        
        
        layout_2 = QtGui.QHBoxLayout()
        layout_2.setAlignment(QtCore.Qt.AlignLeft)
        
        self.add = QtGui.QPushButton('Shape')
        self.add.setMinimumWidth(100)
        self.add.setMaximumWidth(200)
        self.add.setMinimumHeight(50)
        
        self.add.clicked.connect(self._add_command)
        
        layout_2.addWidget(self.add)
        
        button_layout = QtGui.QVBoxLayout()
        button_layout.addSpacing(10)
        button_layout.addLayout(layout_1)
        button_layout.addSpacing(10)
        button_layout.addLayout(layout_2)
                
        header_layout.addLayout(button_layout)
        
        self.slider = WeightSlider()
        self.slider.value_change.connect(self._update_value)
        
        button_layout.addSpacing(10)
        button_layout.addWidget(self.slider)
        
        
        #header_layout.addWidget(slider)
        
        
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
        
    def _refresh(self):
        
        shapes = self.manager.get_shapes()
        
        if shapes:
            self._add_meshes(shapes)

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
            
            value = 1
            
            """
            if len(shapes) == 1:
                if self.manager.is_inbetween(shapes[0]):
                    inbetween_value = self.manager.get_inbetween_value(shapes[0])
                    
                    if inbetween_value != None:
                        value = (inbetween_value * .01)
            """
            #for shape in shapes:
                #self.manager.turn_on_shape(shape)
                
            self.slider.set_value(value)
        
    def _shape_selection_changed(self):
        
        if not self.update_on_select:
            return
        
        self.manager.zero_out()
        
        shape_items = self.shape_widget.tree.selectedItems()
        
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
                previous_item.setSelected(False)
            
        shape_items = self.shape_widget.tree.selectedItems()
            
        
        for item in shape_items:
            parent = item.parent()

            if parent:
                for inc in range(0, parent.childCount()):
                    
                    parent.child(inc).setSelected(False)
                    parent.setSelected(False)
                    
                self.update_on_select = False
                self.shape_widget.tree.setCurrentItem(item)
                self.update_on_select = True
        
        shapes = self._get_selected_shapes()
        
        if self.refresh_combo_list:
            self._update_combo_selection(shapes)
            
        self._update_slider_for_shapes(shapes)
        
    def _combo_selection_changed(self):
        
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
        
        #if not shapes:
        #    self.combo_widget.tree.clear()
        #    return
                
        combos = self.manager.get_combos()
        possible_combos = self.manager.find_possible_combos(shapes)
        
        self.combo_widget.tree.load(combos, possible_combos)
    
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
                    self.current_base.setText(mesh)
                
                if not self.manager.setup_group:
                    self.current_base.setText('-')
        
        if meshes:
            mesh = None
            if meshes:
                mesh = meshes[0]
            
            self.manager.create(mesh)
            
            self.current_base.setText(mesh)

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
            
            #self.combo_widget.tree.load()   
                    
        if shape_items and not combo_items and not inbetween_items and len(shape_items) == 1:

            shape_name = str(shape_items[0].text(0))
            self.manager.add_shape(shape_name, mesh)
            
            self.shape_widget.tree.select_shape(shape_name)
        
        if inbetween_items and not combo_items and not shape_items and len(inbetween_items) == 1:
            item = inbetween_items[0]
            name = inbetween_items[0].text(0)
            self.manager.add_shape(name, mesh)
            
            brush = QtGui.QBrush()
            color = QtGui.QColor()
            color.setRgb(200,200,200)
            brush.setColor(color)
            item.setForeground(0, brush)
            
        if not combo_items and not shape_items and not inbetween_items:
            self._add_meshes([mesh])
            
        
    def _add_meshes(self, meshes):
        
        shapes, combos, inbetweens = self.manager.get_shape_and_combo_lists(meshes)
        
        for shape in shapes:
            self.manager.add_shape(shape)    
        
        for inbetween in inbetweens:
            
            last_number = vtool.util.get_last_number(inbetween)
            
            if not len(str(last_number)) >= 2:
                continue
            
            self.manager.add_shape(inbetween)
            
        for combo in combos:
            for mesh in meshes:
                if mesh == combo:
                    self.manager.add_combo(mesh)
        
        self.shape_widget.tree.load(inbetweens = inbetweens)
        self.combo_widget.tree.load()   
    
    def _add_command(self):
        
        meshes = geo.get_selected_meshes()
        mesh_count = len(meshes)
        
        if mesh_count == 1:
            
            self._add_mesh(meshes[0])
            
            #if not self.manager.blendshape.is_target(meshes[0]):
                #self._add_mesh(meshes[0])
                
            #if self.manager.blendshape.is_target(meshes[0]):
            #    self._add_meshes([meshes[0]])
            
        
        if mesh_count > 1:
            self._add_meshes(meshes)
            
    def _update_value(self, value):
        
        self.manager.zero_out()
        
        shapes = self._get_selected_shapes()
        
        if not shapes:
            return
        
        for shape in shapes:
            
            self.manager.turn_on_shape(shape, value)
            
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
        
        self.text_edit = False
        
        self.setSelectionMode(self.ExtendedSelection)
        
        self.setSortingEnabled(False)
        
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._item_menu)
        
        self._create_context_menu()
        
        self.manager = None
        
        self.ctrl_active = False
        
    def _item_menu(self, position):
                
        #item = self.itemAt(position)
        
        self.context_menu.exec_(self.viewport().mapToGlobal(position))
        
    def _create_context_menu(self):
        
        self.context_menu = QtGui.QMenu()
        
        self.recreate_action = self.context_menu.addAction('Recreate')
        
        self.rename_action = self.context_menu.addAction('Rename')
        
        self.remove_action = self.context_menu.addAction('Remove')
        self.context_menu.addSeparator()
        
        self.recreate_action.triggered.connect(self.recreate)
        self.rename_action.triggered.connect(self.rename)
        self.remove_action.triggered.connect(self.remove)
        
    def _create_item(self, shape, inbetweens = None):
        
        item = QtGui.QTreeWidgetItem()
        item.setSizeHint(0, QtCore.QSize(100, 20))
        
        
        
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
        
        child_item = QtGui.QTreeWidgetItem(parent)
        child_item.setSizeHint(0, QtCore.QSize(100, 20))
        child_item.setText(0, name)
        
        return child_item
        
    def _highlight_child(self, item, bool_value = True):
        
        if bool_value:
            font = item.font(0)
            font.setBold(True)
            item.setFont(0, font)
            
            brush = QtGui.QBrush()
            color = QtGui.QColor()
            color.setRgb(200,200,200)
            brush.setColor(color)
            item.setForeground(0, brush)
        
        if not bool_value:
            brush = QtGui.QBrush()
            color = QtGui.QColor()
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
            self.setItemSelected(item, True)
    
    def recreate(self):
        
        items = self.selectedItems()
        
        if not items:
            return
        
        for item in items:
            name = item.text(0)
            self.manager.recreate_shape(name)
            
        
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
        
        self.text_edit = False
        
        self.setSortingEnabled(False)
        
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._item_menu)
        
        self._create_context_menu()
        
    def _item_menu(self, position):
        
        self.context_menu.exec_(self.viewport().mapToGlobal(position))
        
    def _create_context_menu(self):
        
        self.context_menu = QtGui.QMenu()
        
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
            
            brush = QtGui.QBrush()
            color = QtGui.QColor()
            color.setRgb(200,200,200)
            brush.setColor(color)
        
        if not bool_value:
            
            font.setBold(False)
            brush = QtGui.QBrush()
            color = QtGui.QColor()
            color.setRgb(100,100,100)
            brush.setColor(color)
        
        item.setForeground(0, brush)
        item.setFont(0, font)
        
    def recreate(self):
        
        items = self.selectedItems()
        
        if not items:
            return
        
        name = str(items[0].text(0))
        
        self.manager.recreate_combo(name)
        
            
    
    def remove(self):

        items = self.selectedItems()
        
        if not items:
            return
        
        name = str(items[0].text(0))
        
        self.manager.remove_combo(name)
        
        self.highlight_item(items[0], False)
        self.setItemSelected(items[0], False)
    
    def load(self, combos = None, possible_combos = None):
        
        if not combos:
            combos = self.manager.get_combos()
        
        self.clear()
        
        for combo in combos:
            item = QtGui.QTreeWidgetItem()
            item.setSizeHint(0, QtCore.QSize(100, 20))
            item.setText(0, combo)
            self.highlight_item(item)
            
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
                
                self.highlight_item(item, False)
                
                
                self.addTopLevelItem(item)
    
    def set_manager(self, manager):
        self.manager = manager
        
        
class WeightSlider(qt_ui.BasicWidget):
    
    value_change = qt_ui.create_signal(object)
    
    def __init__(self):
        super(WeightSlider, self).__init__()
        
    def _define_main_layout(self):
        return QtGui.QHBoxLayout()

    def _build_widgets(self):
        
        self.value = QtGui.QDoubleSpinBox()
        self.value.setMinimum(0)
        self.value.setMaximum(1)
        self.value.setSingleStep(.05)
        
        self.value.setMinimumWidth(60)
        self.value.setButtonSymbols(self.value.NoButtons)
        
        self.slider = QtGui.QSlider()
        self.slider.setMinimum(0)
        self.slider.setMaximum(100)
        self.slider.setTickPosition(self.slider.TicksBelow)
        self.slider.setSingleStep(5)
        
        
        self.slider.setOrientation(QtCore.Qt.Horizontal)
        self.slider.setMinimumWidth(80)
        #self.slider.setMaximumWidth(120)
        
        #self.main_layout.setSpacing(1)
        #self.main_layout.addSpacing(5)
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
        self.value.setValue(value*0.01)
        self.update_value = True
        
        self.value_change.emit(value*0.01)
        
    def _value_change(self):
        
        if not self.update_value:
            return
        
        self.update_slider = False
        value = self.value.value()
        self.slider.setValue(value*100)
        self.update_slider = True
        
        self.value_change.emit(value)
        
    def set_min_max(self, min_value, max_value):
        
        self.value.setMinimum(min_value)
        self.value.setMaximum(max_value)
        
        self.slider.setMinimum(min_value*100)
        self.slider.setMaximum(max_value*100)
        
    def set_value(self, value):
        
        self.slider.setValue(value*100)
        
        self.value_change.emit( value )
        
