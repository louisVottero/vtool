# Copyright (C) 2016 Louis Vottero louis.vot@gmail.com    All rights reserved.

import ui
from vtool import qt_ui
from vtool import util

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
        
import maya.cmds as cmds
import rigs_util
import attr
import core

class PickManager(ui.MayaWindow):
    
    title = 'Picker'
    
    def __init__(self):
        
        self.pickers = []
        
        self._create_picker_group()
        
        super(PickManager, self).__init__()
        
        if util.get_maya_version() > 2016:
            self.setStyleSheet("""
                QTabBar::tab {
                    min-height: 30px;
                }
            """)
    
    def _build_widgets(self):
        
        #self._build_top_widgets()
        
        self.tab_widget = PickerTab()
        
        self.tab_widget.tabBar().setMinimumHeight(60)
        self.tab_widget.tab_closed.connect(self._close_tab)
        
        picker = self._create_picker()
        
        picker.item_added.connect(self._picker_item_added)
        
        self.tab_widget.addTab(picker, 'View')
        
        self.tab_widget.addTab(QWidget(), '+')
        
        corner_widget = CornerWidget()
        
        self.edit_button = corner_widget.edit_button
        
        self.tab_widget.setCornerWidget(corner_widget)
        
        
        self.edit_button.clicked.connect(self._edit_mode)
        
        self.tab_widget.currentChanged.connect(self._tab_changed)
        
        self.main_layout.addWidget(self.tab_widget)
        
        self._build_btm_widgets()
        
    def _picker_item_added(self):
        self._export()
        
    def _get_data_from_views(self):
        
        tab_count = self.tab_widget.count()
        
        view_data = []
        
        for inc in range(0, tab_count):
            
            if inc >= len(self.pickers):
                continue
                
            
            view_dict = {}
            
            title = self.tab_widget.tabText(inc)
            
            view_dict['title'] = title
            
            picker = self.pickers[inc]
            
            items = picker.scene.items()
            
            found_items = []
            
            for item in items:
                
                item_dict = self._get_item_dict(item)
                
                found_items.append(item_dict)
                
            view_dict['items'] = found_items
            
            view_data.append(view_dict)
                
        return view_data
    
    def _get_item_dict(self, item):
        
        item_dict = {}
        name = item.name
        rect = item.rect()
        x = rect.x()
        y = rect.y()
        height = rect.height()
        width = rect.width()
        size = rect.size()
        
        item_dict['name'] = name
        item_dict['x'] = x
        item_dict['y'] = y
        item_dict['height'] = height
        item_dict['width'] = width
        #item_dict['size'] = size.height()
        
        return item_dict
    
    def _export(self):
        view_data = self._get_data_from_views()
        
        self._create_picker_group()
        
        attribute = '%s.DATA' % self.picker_group
        
        if cmds.objExists(attribute):
            cmds.setAttr(attribute, l = False)
            cmds.setAttr(attribute, str(view_data), type = 'string')
        
        
        cmds.setAttr(attribute, l = True)
    
    def _import(self):
        pass
        
    def _create_picker_group(self):
        picker_group = create_picker_group()
        
        self.picker_group = picker_group
        
    def _tab_changed(self):
        
        index = self.tab_widget.currentIndex()
        
        title = self.tab_widget.tabText(index)
        
        if title == '+':
            picker = self._create_picker()
            self.tab_widget.removeTab(index)
            self.tab_widget.addTab(picker, 'View')
            self.tab_widget.addTab(QWidget(), '+')
            self.tab_widget.setCurrentIndex(index)
            index = index + 1
            
        if not title == '+':
            self.edit_buttons.set_picker(self.pickers[index])
        
    def _create_picker(self):
        
        picker = Picker()
        self.pickers.append(picker)
        return picker
        
    def _build_top_widgets(self):
        
        top_layout = QHBoxLayout()
        self.main_layout.addLayout(top_layout)
        
        self.title = QLabel()
        
        self.edit_button = QPushButton('Edit')
        self.edit_button.setCheckable(True)
        self.edit_button.setChecked(False)
        self.edit_button.setMaximumWidth(150)
        self.edit_button.setMinimumHeight(60)
        self.edit_button.clicked.connect(self._edit_mode)
        top_layout.addWidget(self.title, alignment = QtCore.Qt.AlignLeft)
        top_layout.addWidget(self.edit_button, alignment = QtCore.Qt.AlignRight)
        
        self.main_layout.addLayout(top_layout)
        
    def _edit_mode(self):
        
        current_index = self.tab_widget.currentIndex()
        
        self.edit_buttons.set_picker(self.pickers[current_index])
        
        if self.edit_button.isChecked():
            self.edit_buttons.setHidden(False)
            
            self.pickers[current_index].set_edit_mode(True)
            
        if not self.edit_button.isChecked():
            self.edit_buttons.setHidden(True)
            self.pickers[current_index].set_edit_mode(False)            
            
    def _close_tab(self, current_index):
        
        self.pickers.pop(current_index)
            
    def _build_btm_widgets(self):
        
        self.edit_buttons = EditButtons(None)
        
        self.main_layout.addWidget(self.edit_buttons)
        
        self.edit_buttons.setHidden(True)
        

        
class PickerTab(QTabWidget):
    
    tab_closed = qt_ui.create_signal(object)
    tab_renamed = qt_ui.create_signal()
    
    def __init__(self):
        super(PickerTab, self).__init__()
        
        self.tabBar().setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.tabBar().customContextMenuRequested.connect(self._item_menu)
        
        self._create_context_menu()
        
    def _create_context_menu(self):
        
        self.context_menu = QMenu()
        
        rename = self.context_menu.addAction('Rename')
        rename.triggered.connect(self._rename_tab)
        
        close = self.context_menu.addAction('Close')
        close.triggered.connect(self._close_tab)
        
    def _item_menu(self, position):
        
        self.context_menu.exec_(self.tabBar().mapToGlobal(position))
    
    def _rename_tab(self):
        
        index = self.currentIndex()
        
        tab_name = self.tabText(index)
        
        new_name = qt_ui.get_new_name('New Name', self, tab_name)
        
        self.setTabText(index, new_name)
        
        self.tab_renamed.emit()
        
    def _close_tab(self):
        
        
        current_index = self.currentIndex()
        
        if current_index == 0:
            return
        
        
        
        self.setCurrentIndex( (current_index - 1) )
        
        widget = self.widget( current_index )
        widget.scene.clearSelection()
        widget.close()
        widget.deleteLater()
        
        
        self.removeTab( current_index )
        
        self.tab_closed.emit(current_index)
        
        
        

class CornerWidget(qt_ui.BasicWidget):
    
    
    def _define_main_layout(self):
        return QHBoxLayout()
    
    def _build_widgets(self):
        self.edit_button = QPushButton('Edit')
        self.edit_button.setCheckable(True)
        self.edit_button.setChecked(False)
        
        self.main_layout.addWidget(self.edit_button)
        
class EditButtons(qt_ui.BasicWidget):
    
    def __init__(self, picker = None):
        
        self.picker = picker
        
        super(EditButtons, self).__init__()
        
    
    def _build_widgets(self):
        
        btm_layout = QHBoxLayout()
        self.btm_layout = btm_layout
        
        self.main_layout.addLayout(btm_layout)
        
        side_buttons = QVBoxLayout()
        
        self.add_button = QPushButton('Add Control')
        self.add_button.clicked.connect(self._add_item)
        side_buttons.addWidget(self.add_button)
        
        self.add_controls = QPushButton('Add All Controls')
        self.add_controls.clicked.connect(self._add_controls)
        side_buttons.addWidget(self.add_controls)
        
        btm_layout.addLayout(side_buttons, alignment = QtCore.Qt.AlignLeft)
        
        self.main_layout.addLayout(btm_layout)
        
        group = qt_ui.Group('Options')
        
        alignment_layout = QHBoxLayout()
        
        self.load_positions = QPushButton('Load Positions')
        self.load_positions.clicked.connect(self._load_positions)
        self.load_alignments = QComboBox()
        self.load_alignments.addItem('X')
        self.load_alignments.addItem('Y')
        self.load_alignments.addItem('Z')
        
        alignment_layout.addWidget(self.load_positions)
        alignment_layout.addWidget(self.load_alignments)
        
        group.main_layout.addLayout(alignment_layout)
        
        scale_slider = qt_ui.Slider()
        scale_slider.set_title('Scale')
        scale_slider.slider.setRange(-1000, 1000)
        scale_slider.set_auto_recenter(True)
        scale_slider.value_changed.connect(self._scale_item)
        self.scale_slider = scale_slider
        
        group.main_layout.addWidget(scale_slider)
        
        btm_layout.addWidget(group)
        
    def _load_positions(self):
        
        items = self.picker.scene.selectedItems()
        
        
        for item in items:
            
            axis = self.load_alignments.currentText()
            
            control = item.name
            x,y,size,level = get_control_position(control, axis)
            
            item.setPos(x,y)
            #item.setScale(size)
            #item.setZValue(level)
        
    def _scale_item(self, value):
        
        if self.scale_slider.last_value == None:
            self.scale_slider.last_value = 0
        
        if value == self.scale_slider.last_value:
            return
        
        if value > self.scale_slider.last_value:
            pass_value = 0.05
        
        if value < self.scale_slider.last_value:
            pass_value = -0.05
        
        items = self.picker.scene.selectedItems()
        
        
        
        for inc in range(0, len(items)):
            
            item = items[inc]
            
            scale = item.scale()
            
            
            if inc == 0:
                pass_value = scale + pass_value
            
            if pass_value < 0.5 or pass_value > 6:
                continue
            
            item.setScale(pass_value)

        self.scale_slider.last_value = value
        
    def _add_item(self):
        
        self.picker.add_item()
        
    def _add_controls(self):
        self.picker.add_controls()
        
    def set_picker(self, picker):
        self.picker = picker
        
class ItemValues( qt_ui.BasicWidget ):
    
    pass
    
class Picker(qt_ui.BasicGraphicsView):
    
    item_added = qt_ui.create_signal(object)
    
    def __init__(self):
        
        super(Picker, self).__init__()
        
        self.setDragMode(self.RubberBandDrag)
        
        #line = QGraphicsLineItem()
        #line.setPen(line_pen)
        
        #height = self.height()
        
        #line.setLine(0,self.rect().top(), 0, self.rect().bottom())
        
        self.scene.selectionChanged.connect(self._item_selected)
        self.current_item_names = []
        
        #self.addItem(line)
        
    def drawBackground(self, painter, rect):
        
        line_pen = QPen()
        line_pen.setColor(QColor(60,60,60))
        line_pen.setStyle(QtCore.Qt.DashLine)
        line_pen.setWidth(2)
        
        painter.setPen(line_pen)
        painter.drawLine(0, rect.top(), 0, rect.bottom())
        
        painter.drawLine((rect.right() / 2), 0, (rect.right()), 0)
        painter.drawLine((rect.left() / 2), 0, (rect.left()), 0)
        
    def drawForeground(self, painter, rect):
        if self.current_item_names:
            text_pen = QPen()
            text_pen.setColor(QColor(150,150,150))
            text_pen.setStyle(QtCore.Qt.SolidLine)
            painter.setPen(text_pen)
            name = self.current_item_names[0]
            if len(self.current_item_names) > 1:
                name += '  ...'
            painter.drawText((rect.left()+20),(rect.top()+20), name)
        #return qt_ui.BasicGraphicsView.drawBackground(self, *args, **kwargs)
        
    def _item_selected(self):
        
        items = self.scene.selectedItems()
        
        self.current_item_names = []
        
        if not items:
            return
        
        for item in items:
            
            self.current_item_names.append(item.name)
        
    
        
    def add_controls(self, view_axis = 'Z', namespace = ''):
        
        controls = rigs_util.get_controls()
        

        
        for control in controls:
            
            x,y,size,level = get_control_position(control)
            
            
            self.add_item(control, x, y, size, level)
        
    def add_item(self, name = None, x = 0, y = 0, size = 1, level = 0):
        
        if not name:
            selection = cmds.ls(sl = True)
            name = selection[0]
        
        for item in self.items():
            if item.name == name:
                return
            
        item = PickerItem(name)
        self.scene.addItem(item)
        
        item.setScale(size)
        item.setPos(x,y)
        item.setZValue(level)
        
        self.item_added.emit(item)
        
    def set_edit_mode(self, bool_value):
        
        items = self.scene.items()
        
        for item in items:
            if hasattr(item, 'set_edit_mode'):
                item.set_edit_mode(bool_value)

class PickerItem(QGraphicsRectItem):
    
    def __init__(self, node):
        super(PickerItem, self).__init__()
        
        shapes = core.get_shapes(node)
        
        color_node = None
        
        if shapes:
            color_node = shapes[0]
        
        if not shapes:
            color_node = node
        color = attr.get_color(color_node, rgb = True)
        
        self.setRect(-10,-10,20,20)
        
        brush = QBrush()
        brush.setColor(QColor(color[0],color[1], color[2]))
        brush.setStyle(QtCore.Qt.SolidPattern)
        self.setBrush(brush)
        
        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable)
        
        
        
        self.name = node
        

    def mousePressEvent(self, event):
        super(PickerItem, self).mousePressEvent(event)
        
        cmds.select(self.name)
        
    def set_edit_mode(self, bool_value):
        
        if bool_value == True:
            self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable)
        if bool_value == False:
            self.setFlags(QGraphicsItem.ItemIsSelectable)
            
def get_control_position(control, view_axis = 'Z'):
    
    size = 1
    level = 0
    
    pos = cmds.xform(control, q = True, ws = True, t = True)
    
    if view_axis == 'X':
        x = pos[2]* -3
        y = pos[1]* -3
    
    if view_axis == 'Y':
        x = pos[0]* 3
        y = pos[2]* -3
    
    if view_axis == 'Z':
        
        x = pos[0]* 3
        y = pos[1]* -3 
    
    if control.find('SUB') > -1:
        level = 1
        x *= 1.5
        size = .5
    
    return x,y,size,level

def create_picker_group():
    
    name = 'picker_gr'
    group = name
    
    if not cmds.objExists(name):
        group = cmds.group(em = True, n = name)
        attr.hide_keyable_attributes(group)
        
    attribute = '%s.DATA' % group
        
    if not cmds.objExists(attribute):
        cmds.addAttr(group, ln = 'DATA', dt = 'string')
        
    return group
    