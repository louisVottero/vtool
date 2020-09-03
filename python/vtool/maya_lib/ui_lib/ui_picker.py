# Copyright (C) 2016 Louis Vottero louis.vot@gmail.com    All rights reserved.

from vtool.maya_lib import ui_core
from vtool import qt_ui, qt

from vtool import util
        
import maya.cmds as cmds
from vtool.maya_lib import rigs_util
from vtool.maya_lib import attr
from vtool.maya_lib import core

from vtool.maya_lib import picker

class PickManager(ui_core.MayaWindow):
    
    title = 'Picker'
    
    def __init__(self):
        
        self.pickers = []
        self.namespace = None
        self._create_picker_group()
        
        super(PickManager, self).__init__()
        
        if util.get_maya_version() > 2016:
            self.setStyleSheet("""
                qt.QTabBar::tab {
                    min-height: 30px;
                }
            """)
    
        self._import()
    
    def _build_widgets(self):
        
        self.tab_widget = qt_ui.NewItemTabWidget()
        
        
        
        self.tab_widget.tab_closed.connect(self._close_tab)
        self.tab_widget.tab_renamed.connect(self._rename_tab)
        
        picker_inst = self._create_picker()
        
        print 'pickers', self.pickers
        
        picker_inst.item_added.connect(self._picker_item_added)
        
        self.tab_widget.addTab(picker_inst, 'View')
        
        
        self.namespace_widget = NamespaceWidget()
        if self.namespace_widget.currentText() != '-':
            self._set_namespace(str(self.namespace_widget.currentText()))
        self.namespace_widget.activated.connect(self._namespace_combo_activate)
        
        self.corner_widget = CornerWidget()
        self.edit_button = self.corner_widget.edit_button
        
        self.tab_widget.setCornerWidget(self.corner_widget)
        
        
        self.edit_button.clicked.connect(self._edit_mode)
        
        self.main_layout.addWidget(self.namespace_widget)
        self.main_layout.addWidget(self.tab_widget)
        
        self.tab_widget.currentChanged.connect(self._tab_changed)
        self.tab_widget.tab_add.connect(self._tab_add)
        
        
        
        
        
        self._build_btm_widgets()
        
    def _tab_changed(self):
        
        
        
        index = self.tab_widget.currentIndex()
        title = self.tab_widget.tabText(index)
        
        if index == -1:
            return
        
        if not title == '+':
            self.edit_buttons.set_picker(self.pickers[index])

    def _set_namespace(self, namespace):
        
        self.namespace = namespace
        self._set_picker_group(self._get_picker_group())
        
        if self.picker_group:
            self._import()
            
            for picker in self.pickers:
                picker.set_namespace(self.namespace)
                picker.namespace = self.namespace
                
        if not self.picker_group:
            util.warning('Could not load. No picker group in namespace: %s' % namespace)
        
    def _namespace_combo_activate(self, index):
        
        namespace = self.namespace_widget.itemText(index)
        
        self._set_namespace(namespace)
        
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
            picker_widget = self.tab_widget.widget(inc)
            background = picker_widget.background_file
            
            view_dict['title'] = title
            view_dict['background'] = background
            
            picker = self.pickers[inc]
            
            
            
            items = picker.scene().items()
            
            found_items = []
            
            for item in items:
                
                item_dict = self._get_item_dict(item)
                
                found_items.append(item_dict)
                
            view_dict['items'] = found_items
            
            view_data.append(view_dict)
                
        return view_data
    
    def _get_item_dict(self, item):
        
        item_dict = {}
        item_type = str(item.picker_item_type)
        name = item.name
        
        x = item.x()
        y = item.y()
        size = item.scale()
        
        level = item.zValue()
        text = item.get_text()
        
        item_dict['name'] = name
        item_dict['x'] = x
        item_dict['y'] = y
        item_dict['size'] = size
        item_dict['level'] = level
        item_dict['type'] = item_type
        item_dict['text'] = text
        
        return item_dict
    
    def _export(self):
        
        if self._is_picker_reference():
            return
        
        view_data = self._get_data_from_views()
        
        
        
        picker_inst = picker.Picker()
        picker_inst.set_data(view_data)
    
    def _import(self):
        
        picker_inst = picker.Picker(self.picker_group)
        view_data = picker_inst.get_data()
        
        if not view_data:
            return
        
        self.tab_widget.close_tabs()
        
        for view in view_data:
            
            view_name = view['title']
            background = view['background']
            
            picker_inst = self._create_picker()
            self.tab_widget.addTab(picker_inst, view_name)
            picker_inst.set_background(background)
            
            
            items = view['items']
            
            for item in items:
                item_type = item['type']
                
                if item_type == Picker.ITEM_TYPE_SIMPLE_SQUARE:
                    name = item['name']
                    x = item['x']
                    y = item['y']
                    size = item['size']
                    level = item['level']
                    text = item['text']
                    item = picker_inst.add_item(name, x, y, size, level, text)
                    
                    
        
        self._export()
        
    def _create_picker_group(self):
        picker_group = picker.Picker().create_picker_group()
        
        self.picker_group = picker_group
    
    def _set_picker_group(self, picker_name):
        
        self.picker_group = picker_name
    
    
    
    def _tab_add(self):
        
        picker_inst = self._create_picker()
        self.tab_widget.addTab(picker_inst, 'View')

    def _create_picker(self):
        
        picker_inst = Picker()
        self.pickers.append(picker_inst)
        picker_inst.scene_update.connect(self._export)
        return picker_inst
    
    def _get_picker_group(self):
        
        picker = 'picker_gr'
        
        if self.namespace:
            picker = self.namespace + ':picker_gr'
        
        if cmds.objExists(picker):
            return picker
            
    def _is_picker_reference(self):
        
        return core.is_referenced(self._get_picker_group())
    
    def _edit_mode(self):
        
        current_index = self.tab_widget.currentIndex()
        
        if self._is_picker_reference():
            self.edit_buttons.setHidden(True)
            self.pickers[current_index].set_edit_mode(False)
            
        self.edit_buttons.set_picker(self.pickers[current_index])
        
        if self.edit_button.isChecked():
            
            self.tab_widget.addTab(qt.QWidget(), '+')
            
            self.edit_buttons.setHidden(False)
            
            self.pickers[current_index].set_edit_mode(True)
            
        if not self.edit_button.isChecked():
            self.edit_buttons.setHidden(True)
            self.pickers[current_index].set_edit_mode(False)  
            
            tab_count = self.tab_widget.count()
            
            for inc in range(0, tab_count):
            
                if self.tab_widget.tabText(inc) == '+':
                    self.tab_widget.removeTab(inc)
            
            self._export()
            
    def _rename_tab(self, current_index):
        
        self._export()
    
    def _close_tab(self, current_index):
        
        self.pickers.pop(current_index)
        self._export()
            
    def _build_btm_widgets(self):
        
        self.edit_buttons = EditButtons(None)
        self.edit_buttons.item_changed.connect(self._export)
        
        self.main_layout.addWidget(self.edit_buttons)
        
        self.edit_buttons.setHidden(True)
        
class NamespaceWidget(qt.QComboBox):
    
    def __init__(self):
        super(NamespaceWidget, self).__init__()
        
        self._load_namespaces()
        
    def _load_namespaces(self):
        self.clear()
        
        names = self._get_namespaces()
        
        names.remove('UI')
        names.remove('shared')
        
        if names:
            for name in names:
                self.addItem(name)
            
        if not names:
            self.addItem('-')
    
    def mousePressEvent(self, event):
        
        self._load_namespaces()
        
        return super(NamespaceWidget, self).mousePressEvent(event)
        
    def _get_namespaces(self):
        
        namespaces = cmds.namespaceInfo(lon = True)
        
        return namespaces
        
        

class CornerWidget(qt_ui.BasicWidget):
    
    
    def _define_main_layout(self):
        return qt.QHBoxLayout()
    
    def _build_widgets(self):
        
        self.edit_button = qt.QPushButton('Edit')
        self.edit_button.setCheckable(True)
        self.edit_button.setChecked(False)
        
        self.main_layout.addWidget(self.edit_button)
        
class EditButtons(qt_ui.BasicWidget):
    
    item_changed = qt_ui.create_signal()
    
    
    def __init__(self, picker = None):
        
        self.picker = picker
        
        super(EditButtons, self).__init__()
        
    
    def _build_widgets(self):
        
        btm_layout = qt.QHBoxLayout()
        self.btm_layout = btm_layout
        
        self.main_layout.addLayout(btm_layout)
        
        side_buttons = qt.QVBoxLayout()
        
        self.add_button = qt.QPushButton('Add Control')
        self.add_button.clicked.connect(self._add_item)
        side_buttons.addWidget(self.add_button)
        
        self.add_controls = qt.QPushButton('Add All Controls')
        self.add_controls.clicked.connect(self._add_controls)
        side_buttons.addWidget(self.add_controls)
        
        select_from_viewport = qt.QPushButton('Select From Maya')
        select_from_viewport.clicked.connect( self._select_from_viewport )
        side_buttons.addWidget(select_from_viewport)
        
        set_background = qt.QPushButton('Set Background')
        set_background.clicked.connect(self._set_background)
        side_buttons.addWidget(set_background)
        
        btm_layout.addLayout(side_buttons, alignment = qt.QtCore.Qt.AlignLeft)
        
        self.main_layout.addLayout(btm_layout)
        
        group = qt_ui.Group('Options')
        group.setMaximumWidth(200)
        
        alignment_layout = qt.QHBoxLayout()
        
        self.load_positions = qt.QPushButton('Load Positions')
        self.load_positions.clicked.connect(self._load_positions)
        self.load_alignments = qt.QComboBox()
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
        
        
        
        self.item_values = ItemValues()
        
        btm_layout.addWidget(self.item_values)
        btm_layout.addWidget(group)
        
    def _set_background(self):
        
        image_file = qt_ui.get_file('')
        
        self.picker.set_background(image_file)
        
    def _load_positions(self):
        
        items = self.picker.scene().selectedItems()
        
        for item in items:
            
            axis = self.load_alignments.currentText()
            
            control = item.name
            x,y,size,level = get_control_position(control, axis)
            
            item.setPos(x,y)
            
    def _scale_item(self, value):
        
        if self.scale_slider.last_value == None:
            self.scale_slider.last_value = 0
        
        if value == self.scale_slider.last_value:
            return
        
        if value > self.scale_slider.last_value:
            pass_value = 0.05
        
        if value < self.scale_slider.last_value:
            pass_value = -0.05
        
        items = self.picker.scene().selectedItems()
        
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
        
        self.item_changed.emit()
        
    def _add_controls(self):
        
        self.picker.add_controls()
        
        self.item_changed.emit()
        
    def _clicked(self, item):
        
        self.item_values.load_item(item)
        
    def _select_from_viewport(self):
        
        scope = cmds.ls(sl = True)
        
        for node in scope:
            items = self.picker.items()
            
            for item in items:
                if item.name == node:
                    item.setSelected(True)
                    
    def set_picker(self, picker):
        self.picker = picker
        self.item_values.picker = self.picker
        self.picker.clicked.connect(self._clicked)
        
class ItemValues( qt_ui.BasicWidget ):
    
    def __init__(self):
        super(ItemValues, self).__init__()
        
        self.picker = None
    
    def _build_widgets(self):
        
        self.x_widget = qt_ui.GetInteger('X')
        self.y_widget = qt_ui.GetInteger('Y')
        self.size_widget = qt_ui.GetNumber('Size')
        self.size_widget.set_value(1)
        self.level_widget = qt_ui.GetInteger('Level')
        
        self.text = qt_ui.GetString('label')
        self.text.label.setAlignment(qt.QtCore.Qt.AlignRight)
        self.text.text_entry.setMaximumWidth(100)
        
        self.x_widget.enter_pressed.connect(self.set_x_value)
        self.y_widget.enter_pressed.connect(self.set_y_value)
        self.size_widget.enter_pressed.connect(self.set_size_value)
        self.level_widget.enter_pressed.connect(self.set_level_value)
        self.text.text_changed.connect(self.set_text)
        
        self.main_layout.addWidget(self.x_widget)
        self.main_layout.addWidget(self.y_widget)
        self.main_layout.addWidget(self.size_widget)
        self.main_layout.addWidget(self.level_widget)
        self.main_layout.addWidget(self.text)
        
        self.skip_update_values = False
        
        
    def load_item(self, item):
        
        if not item:
            self.x_widget.set_value(0)
            self.y_widget.set_value(0)
            self.size_widget.set_value(1)
            self.level_widget.set_value(0)
            return
        
        self.skip_update_values = True
        
        x_value = item.x()
        y_value = item.y()
        size = item.scale()
        level = item.zValue()
        
        self.x_widget.set_value(x_value)
        self.y_widget.set_value(y_value)
        self.size_widget.set_value(size)
        self.level_widget.set_value(level)
        self.text.set_text(item.text)
        
        self.skip_update_values = False
        
    def set_x_value(self):
        
        if self.skip_update_values:
            return
        
        items = self.picker.scene().selectedItems()
        
        if not items:
            return
        
        if len(items) > 1:
            
            x_value = self.x_widget.get_value()
            
            for item in items:
                
                item.setX(x_value)
                
        if len(items) == 1:
            items[0].setX(self.x_widget.get_value())
            
    def set_y_value(self):
        
        if self.skip_update_values:
            
            return
        
        items = self.picker.scene().selectedItems()
        
        if not items:
            return
        
        if len(items) > 1:
            
            y_value = self.y_widget.get_value()
            
            for item in items:
                
                item.setY(y_value)
                
        if len(items) == 1:
            items[0].setY(self.y_widget.get_value())
            

    def set_size_value(self):
        
        if self.skip_update_values:
            return
        
        items = self.picker.scene().selectedItems()
        
        if not items:
            return
        
        if len(items) > 1:
            
            size_value = self.size_widget.get_value()

            for item in items:

                item.setScale(size_value)
        
        if len(items) == 1:
            items[0].setScale(self.size_widget.get_value())

    def set_level_value(self):
        
        if self.skip_update_values:
            return
        
        items = self.picker.scene().selectedItems()
        
        if not items:
            return
        
        if len(items) > 1:
            
            level_value = self.level_widget.get_value()

            for item in items:

                item.setScale(level_value)
        
        if len(items) == 1:
            items[0].setZValue(self.level_widget.get_value())    

    def set_text(self):
        
        items = self.picker.scene().selectedItems()
        
        for item in items:
            item.set_text(self.text.get_text())
    
class Picker(qt_ui.BasicGraphicsView):
    
    ITEM_TYPE_SIMPLE_SQUARE = 'simple_square'
    
    item_added = qt_ui.create_signal(object)
    scene_update = qt_ui.create_signal()
    clicked = qt_ui.create_signal(object)
    
    def __init__(self):
        
        super(Picker, self).__init__()
        
        self.setDragMode(qt.QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(self.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(qt.QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(qt.QtCore.Qt.ScrollBarAlwaysOff)
        
        self.scene().selectionChanged.connect(self._item_selected)
        self.current_item_names = []
        
        self.setInteractive(True)
        
        
        self.background_image = None
        self.background_file = None
        
        self.edit_mode = False
        self.namespace = None
        
    
    def fitInView(self):
        rect = qt.QtCore.QRectF(self._photo.pixmap().rect())
        
        if not rect.isNull():
            unity = self.transform().mapRect(qt.QtCore.QRectF(0, 0, 1, 1))
            self.scale(1 / unity.width(), 1 / unity.height())
            viewrect = self.viewport().rect()
            scenerect = self.transform().mapRect(rect)
            factor = min(viewrect.width() / scenerect.width(),
                         viewrect.height() / scenerect.height())
            self.scale(factor, factor)
            self.centerOn(rect.center())
            self._zoom = 0
    
    def drawBackground(self, painter, rect):
        
        if self.background_image:
        
            size = self.background_image.size()
            
            width = size.width()
            height = size.height()
            
            sub_width = width/2
            sub_height = height/2
            
            painter.drawPixmap(-1*sub_width, -1*sub_height, self.background_image )
            self.setSceneRect(-1*sub_width, -1*sub_height, width, height)
        
        if self.edit_mode == True:
            line_pen = qt.QPen()
            line_pen.setColor(qt.QColor(60,60,60))
            line_pen.setStyle(qt.QtCore.Qt.DashLine)
            line_pen.setWidth(2)
            
            
            if self.background_image:
                painter.setPen(line_pen)
                painter.drawLine(0, (rect.top()-sub_height), 0, rect.bottom())
            
            if not self.background_image:
                painter.setPen(line_pen)
                painter.drawLine(0, rect.top(), 0, rect.bottom())
                
                painter.drawLine((rect.right()  / 2), 0, (rect.right()), 0)
                painter.drawLine((rect.left() / 2), 0, (rect.left()), 0)
            
        
    def drawForeground(self, painter, rect):
        if self.current_item_names:
            text_pen = qt.QPen()
            text_pen.setColor(qt.QColor(150,150,150))
            text_pen.setStyle(qt.QtCore.Qt.SolidLine)
            painter.setPen(text_pen)
            name = self.current_item_names[0]
            if len(self.current_item_names) > 1:
                name += '  ...'
                
            if self.namespace:
                name = self.namespace + ':' + name
            painter.drawText((rect.left()+20),(rect.top()+20), name)
        #return qt_ui.BasicGraphicsView.drawBackground(self, *args, **kwargs)
        
    def drawItems(self, painter, items, options):
        super(Picker, self).drawItems(painter,items,options)
        
        self.scene_update.emit()
        
    def mousePressEvent(self, event):
        super(Picker, self).mousePressEvent(event)
        
        x = event.x()
        y = event.y()
        
        item = self.itemAt(x,y)
        
        if item:
            self.clicked.emit(item)
        
        if not item:
            cmds.select(cl = True)
        
    def _item_selected(self):
        
        items = self.scene().selectedItems()
        
        self.current_item_names = []
        
        if not items:
            cmds.select(cl = True)
            return
        
        for item in items:
            self.current_item_names.append(item.name)
        
    def set_background(self, image_file):
        
        self.background_image = qt.QPixmap(image_file)
        self.viewport().update()
        
        self.background_file = image_file
        
    def add_controls(self, view_axis = 'Z', namespace = ''):
        
        controls = rigs_util.get_controls()
        
        for control in controls:
            
            x,y,size,level = get_control_position(control)
            
            self.add_item(control, x, y, size, level)
        
    def add_item(self, name = None, x = 0, y = 0, size = 1, level = 0, text = '', item_type = None):
        
        if name == None:
            selection = cmds.ls(sl = True)
            if selection:
                name = selection[0]
            else:
                name = 'empty_control'
            
            core.get_basename(name, remove_namespace = True)
        
        for item in self.items():
            if item.name == name:
                return
        
        item = None
        
        if not item_type:
            item_type = self.ITEM_TYPE_SIMPLE_SQUARE
        
        if item_type == self.ITEM_TYPE_SIMPLE_SQUARE:
            item = SimpleSquareItem(name)
            
        if not item:
            return
        
        self.scene().addItem(item)
        
        item.setScale(size)
        item.setPos(int(x),int(y))
        item.setZValue(level)
        item.set_text(text)
        
        self.item_added.emit(item)
        
        item.set_edit_mode(self.edit_mode)
        
        return item
        
    def set_namespace(self, namespace):
        self.namespace = namespace
        
        items = self.scene().items()
        
        for item in items:
            if hasattr(item, 'namespace'):
                item.namespace = self.namespace
        
    def set_edit_mode(self, bool_value):
        
        self.edit_mode = bool_value
        
        items = self.scene().items()
        
        for item in items:
            if hasattr(item, 'set_edit_mode'):
                item.set_edit_mode(bool_value)
                
        if not self.edit_mode:
            self.setDragMode(qt.QGraphicsView.ScrollHandDrag)
            self.setTransformationAnchor(self.AnchorUnderMouse)
            self.setVerticalScrollBarPolicy(qt.QtCore.Qt.ScrollBarAlwaysOff)
            self.setHorizontalScrollBarPolicy(qt.QtCore.Qt.ScrollBarAlwaysOff)
            
        if self.edit_mode:
            
            self.setDragMode(qt.QGraphicsView.RubberBandDrag)
            self.setTransformationAnchor(self.AnchorUnderMouse)
            self.setVerticalScrollBarPolicy(qt.QtCore.Qt.ScrollBarAlwaysOn)
            self.setHorizontalScrollBarPolicy(qt.QtCore.Qt.ScrollBarAlwaysOn)
            
class SimpleSquareItem(qt.QGraphicsRectItem):
    
    def __init__(self, node):
        super(SimpleSquareItem, self).__init__()
        
        self.picker_item_type = Picker.ITEM_TYPE_SIMPLE_SQUARE
        
        color = [1,1,1]
        
        if cmds.objExists(node):
            shapes = core.get_shapes(node)
            
            if shapes:
                color_node = shapes[0]
        
            if not shapes:
                color_node = node
            
            
            color = attr.get_color_rgb(color_node)
        
        self.setRect(-10,-10,20,20)
        
        brush = qt.QBrush()
        brush.setColor(qt.QColor(color[0],color[1], color[2], 150)) #255 is maximum
        brush.setStyle(qt.QtCore.Qt.SolidPattern)
        self.setBrush(brush)
        
        self.name = node
        self.text = None
        
        self.namespace = None
        

    def paint(self, painter, option, widget):
        
        super(SimpleSquareItem, self).paint(painter, option, widget)
        
        scale = self.scale()
        
        font = painter.font() 
        
        if scale > 1:
            
            font.setPointSizeF(10.0*1/scale)
        
        painter.setFont(font)
        
        line_pen = qt.QPen()
        line_pen.setColor(qt.QColor(255,255,255, 200))
        
        
        painter.setPen(line_pen)
        
        if not self.text:
            return
        
        rect = qt.QtCore.QRect(-25,-25,50,50)
        painter.drawText(rect, qt.QtCore.Qt.AlignCenter, self.text)

    def mousePressEvent(self, event):
        super(SimpleSquareItem, self).mousePressEvent(event)
        
        name = self.name
        
        if self.namespace:
            name = self.namespace + ':' + name
        
        if name and cmds.objExists(name):
            cmds.select(name)
        
    def set_edit_mode(self, bool_value):
        
        if bool_value == True:
            self.setFlags(qt.QGraphicsItem.ItemIsMovable | qt.QGraphicsItem.ItemIsSelectable)
        if bool_value == False:
            self.setFlags(self.flags() & ~qt.QGraphicsItem.ItemIsSelectable & ~qt.QGraphicsItem.ItemIsMovable)
            
    def set_text(self, text):
        
        self.text = text
        
        self.update()
    
    def get_text(self):
        
        return self.text
    
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
        x *= 1.75
        size = .75
    
    return x,y,size,level

