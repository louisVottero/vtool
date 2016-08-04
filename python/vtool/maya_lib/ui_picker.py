# Copyright (C) 2016 Louis Vottero louis.vot@gmail.com    All rights reserved.

import ui
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
        
import maya.cmds as cmds
import rigs_util
import attr
import core




class PickManager(ui.MayaWindow):
    
    title = 'Picker'
    
    def _build_widgets(self):
        
        self._build_top_widgets()
        
        self.picker = Picker()
        self.picker.scene.selectionChanged.connect(self._selection_changed)
        self.main_layout.addWidget(self.picker)
        
        self._build_btm_widgets()
        
        self.items = []
        
    def _build_top_widgets(self):
        
        top_layout = QHBoxLayout()
        self.main_layout.addLayout(top_layout)
        
        self.title = QLabel()
        
        self.edit_button = QPushButton('Edit')
        self.edit_button.setCheckable(True)
        self.edit_button.setChecked(False)
        self.edit_button.setMaximumWidth(150)
        self.edit_button.clicked.connect(self._edit_mode)
        top_layout.addWidget(self.title, alignment = QtCore.Qt.AlignLeft)
        top_layout.addWidget(self.edit_button, alignment = QtCore.Qt.AlignRight)
        
        
        self.main_layout.addLayout(top_layout)
        
    def _edit_mode(self):
        if self.edit_button.isChecked():
            self.edit_buttons.setHidden(False)
            
            self.picker.set_edit_mode(True)
            
        if not self.edit_button.isChecked():
            self.edit_buttons.setHidden(True)
            self.picker.set_edit_mode(False)            
            
    def _build_btm_widgets(self):
        
        self.edit_buttons = EditButtons(self.picker)
        
        self.main_layout.addWidget(self.edit_buttons)
        
        self.edit_buttons.setHidden(True)
        
    def _selection_changed(self):
        
        items = self.picker.scene.selectedItems()
        
        item = None
        
        if items:
            item = items[0]
        
        if not item:
            return
        
        self.title.setText(item.name)
        
class EditButtons(qt_ui.BasicWidget):
    
    def __init__(self, picker):
        
        self.picker = picker
        
        super(EditButtons, self).__init__()
        
    
    def _build_widgets(self):
        
        btm_layout = QHBoxLayout()
        self.btm_layout = btm_layout
        
        self.main_layout.addLayout(btm_layout)
        
        self.add_button = QPushButton('Add Control')
        btm_layout.addWidget(self.add_button, alignment = QtCore.Qt.AlignLeft)
        self.add_button.clicked.connect(self.picker.add_item)
        
        self.main_layout.addLayout(btm_layout)
        
        group = qt_ui.Group('Options')
        
        scale_slider = qt_ui.Slider()
        scale_slider.set_title('Scale')
        scale_slider.slider.setRange(-1000, 1000)
        scale_slider.set_auto_recenter(True)
        scale_slider.value_changed.connect(self._scale_item)
        self.scale_slider = scale_slider
        
        group.main_layout.addWidget(scale_slider)
        
        btm_layout.addWidget(group)
        
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
     
class Picker(qt_ui.BasicGraphicsView):
    
    def __init__(self):
        
        super(Picker, self).__init__()
        
        line_pen = QPen()
        line_pen.setColor(QColor(100,100,100))
        line_pen.setStyle(QtCore.Qt.DashLine)
        line_pen.setWidth(2)
        
        line = QGraphicsLineItem()
        line.setPen(line_pen)
        
        height = self.height()
        
        line.setLine(0,height, 0, height*-1)
        

        self.scene.addItem(line)
        
    def add_item(self):
        
        selection = cmds.ls(sl = True)
        
        item = PickerItem(selection[0])
        self.scene.addItem(item)
        
    def set_edit_mode(self, bool_value):
        
        items = self.items()
        
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
        
        
        print 'color!', color
        
        
        self.setRect(-10,-10,20,20)
        
        brush = QBrush()
        brush.setColor(QColor(color[0],color[1], color[2]))
        brush.setStyle(QtCore.Qt.SolidPattern)
        self.setBrush(brush)
        
        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable)
        
        
        effect = QGraphicsDropShadowEffect()
        #effect.setBlurRadius(5)
        
        self.setGraphicsEffect(effect)
        
        
        self.name = node
        
    def mousePressEvent(self, event):
        super(PickerItem, self).mousePressEvent(event)
        
        cmds.select(self.name)
        
    def set_edit_mode(self, bool_value):
        
        if bool_value == True:
            self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable)
        if bool_value == False:
            self.setFlags(QGraphicsItem.ItemIsSelectable)
            