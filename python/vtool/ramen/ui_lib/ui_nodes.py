# Copyright (C) 2022 Louis Vottero louis.vot@gmail.com    All rights reserved.
from __future__ import print_function
from __future__ import absolute_import

import os
import uuid
import math
import string

from ... import logger
log = logger.get_logger(__name__)

from ... import qt
from ... import qt_ui

from .. import util as util_ramen

from ... import util
from ... import util_file

from ...process_manager import process

in_maya = util.in_maya
if in_maya:
    import maya.cmds as cmds
if util.in_unreal:
    from vtool import unreal_lib
from .. import rigs

uuids = {}    

def set_socket_value(socket):
    util.show('set socket value %s' % socket.name)
    has_lines = False
    if hasattr(socket, 'lines'):
        if socket.lines:
            has_lines = True
            
    if not has_lines:
        util.show('No socket lines')
        return
    
    if socket.lines[0].target == socket:
        
        socket = socket.lines[0].source
        log.info('set source as socket %s' % socket.name)
        
    value = socket.value
    
    source_node = socket.parentItem()
    log.info('source node %s' % source_node.name )
    
    #this causes an unterminating loop
    #if the source node never gets set past None during run()
    if socket.value == None:
        source_node.run()
        
    
    outputs = source_node.get_outputs(socket.name)
    
    for output in outputs:
        target_node = output.parentItem()
        target_node.set_socket(output.name, value)
        
        #if not target_node._out_sockets:
        target_node.run()
            
        util.show('Set target node %s.%s: %s' % (target_node.name, output.name, value))

def connect_socket(source_socket, target_socket):
    
    source_node = source_socket.parentItem()
    target_node = target_socket.parentItem()
    
    log.info('connect socket %s.%s to %s.%s' % (source_node.name, source_socket.name, target_node.name, target_socket.name))
    
    value = source_socket.value
    if not source_socket.value:
        source_node.run()
        
        value = source_socket.value
    
    target_node = target_socket.parentItem()
        
    target_node.set_socket(target_socket.name, value)
        
    


def remove_socket_value(socket):
    
    log.info('remove socket %s' % socket.name)
    node = socket.parentItem()
    
    log.info('Remove socket value: %s %s' % (socket.name, node.name))
    node.set_socket(socket.name, None)    
    

            
class ItemType(object):
    
    SOCKET = 1
    WIDGET = 2
    PROXY = 3
    LINE = 4
    NODE = 10001
    JOINTS = 10002
    COLOR = 10003
    CURVE_SHAPE = 10004
    CONTROLS = 10005
    RIG = 20002
    FKRIG = 20003
    IKRIG = 20004
    DATA = 30002
    PRINT = 30003
    UNREAL_SKELETAL_MESH = 30004

class SocketType(object):
    
    IN = 'in'
    OUT = 'out'
    TOP = 'top'
   
class NodeWindow(qt_ui.BasicGraphicsWindow):
    title = 'RAMEN'
    def __init__(self, parent = None):
        
        super(NodeWindow, self).__init__(parent)
        self.setWindowTitle('Ramen')
        
    def sizeHint(self):
        return qt.QtCore.QSize(400,500)
        
    def _define_main_view(self):
        self.main_view = NodeViewDirectory()
        
    def _node_connected(self, line_item):
        
        source_socket = line_item.source
        target_socket = line_item.target
        
        util.show('Connecting socket %s with value %s' % (target_socket.name, source_socket.value))
        
        connect_socket(source_socket, target_socket)
        
        #exec_string = 'node_item._rig.%s = %s' % (socket_item.name, socket_item.value)
        #exec(exec_string, {'node_item':node_item})
        
    def _node_disconnected(self, source_socket, target_socket):
        
        remove_socket_value(target_socket)
        
    def _node_selected(self, node_items):
        pass
        """
        if node_items:
            self.side_menu.show()
            self.side_menu.nodes = node_items
        else:
            self.side_menu.hide()
            self.side_menu.nodes = []
        """
    def _node_deleted(self, node_items):
        
        for node in node_items:
            if hasattr(node, '_rig'):
                node._rig.delete()
        
    def _build_widgets(self):
        
        
        self.main_view.main_scene.node_connect.connect(self._node_connected)
        self.main_view.main_scene.node_disconnect.connect(self._node_disconnected)
        self.main_view.main_scene.node_selected.connect(self._node_selected)
        self.main_view.main_scene.node_deleted.connect(self._node_deleted)
        
        self.side_menu = SideMenu()
        self.main_layout.addWidget(self.side_menu)    
        
        self.side_menu.hide()
        
class NodeDirectoryWindow(NodeWindow):
    
    def set_directory(self, directory):
        self.directory = directory
        self.main_view.set_directory(directory)
    
class NodeView(qt_ui.BasicGraphicsView):
    
    def __init__(self, parent = None):
        super(NodeView, self).__init__(parent)
        
        self._cache = None
        self._zoom = 1
        self.drag = False
        
        self.setRenderHints(qt.QPainter.Antialiasing | qt.QPainter.HighQualityAntialiasing)
        
        brush = qt.QBrush()
        brush.setColor(qt.QColor(15,15,15,1))
        self.setBackgroundBrush(brush)
        #self.setRenderHints(qt.QPainter.Antialiasing | qt.QPainter.SmoothPixmapTransform | qt.QPainter.HighQualityAntialiasing)
        
        #self.main_scene.addItem(NodeSocket())

    def drawBackground(self, painter, rect):
        
        pixmap = qt.QPixmap(40, 40)
        pixmap.fill(qt.QtCore.Qt.transparent)
        
        pix_painter = qt.QPainter(pixmap)
        pix_painter.setBrush(qt.QColor.fromRgbF(.15, .15, .15, 1))
        
        pen = qt.QPen()
        pen.setStyle(qt.Qt.NoPen)
        pix_painter.setPen(pen)
        pix_painter.drawRect(0,0,40,40)
        
        
        pen = qt.QPen()
        pen.setColor(qt.QColor.fromRgbF(0, 0, 0, .6))
        pen.setStyle(qt.Qt.SolidLine)
        
        pix_painter.setPen(pen)
        
        pix_painter.drawLine(0,0,2,0)
        pix_painter.drawLine(0,0,0,2)
        pix_painter.drawLine(38,0,40,0)
        pix_painter.drawLine(0,38,0,40)
        
        pix_painter.end()
        
        painter.fillRect(rect, pixmap)      

    def _define_main_scene(self):
        self.main_scene = NodeScene()
        
        self.main_scene.setObjectName('main_scene')
        self.main_scene.setSceneRect(0,0,5000,5000)
        
        self.setScene(self.main_scene)
        
        self.setResizeAnchor(self.AnchorViewCenter)
        

    def keyPressEvent(self, event):
        
        items = self.main_scene.selectedItems()
        
        if event.key() == qt.Qt.Key_F:
            
            
            position = items[0].pos()
            #position = self.mapToScene(items[0].pos())
            self.centerOn(position)
            
        if event.key() == qt.Qt.Key_Delete:
            for item in items:
                item.delete()
                
            
        super(NodeView, self).keyPressEvent(event)

    def wheelEvent(self, event):
        """
        Zooms the QGraphicsView in/out.
        
        """
        
        if self._zoom < 0.5 or self._zoom > 2:
            return
        
        inFactor = 1.25
        outFactor = 1 / inFactor
        oldPos = self.mapToScene(event.pos())
        if event.delta() > 0:
            zoomFactor = inFactor
        else:
            zoomFactor = outFactor
        
        self._zoom *= zoomFactor
        
        if self._zoom < 0.5:
            self._zoom = 0.5
            return
        if self._zoom > 2.0:
            self._zoom = 2.0
            return
        
        self.scale(zoomFactor, zoomFactor)
        newPos = self.mapToScene(event.pos())
        delta = newPos - oldPos
        self.translate(delta.x(), delta.y())

    def mousePressEvent(self, event):
        if event.button() == qt.QtCore.Qt.MiddleButton:
            self.setDragMode(qt.QGraphicsView.NoDrag)
            self.drag = True
            self.prevPos = event.pos()
            self.setCursor(qt.QtCore.Qt.SizeAllCursor)
        elif event.button() == qt.QtCore.Qt.LeftButton:
            
            self.setDragMode(qt.QGraphicsView.RubberBandDrag)
            #self.setDragMode(qt.QGraphicsView.RubberBandDrag)
            super(NodeView, self).mousePressEvent(event)
        

    def mouseMoveEvent(self, event):
        
        if self.drag:
            
            delta = (event.pos() - self.prevPos) * -1.0
            
            center = qt.QtCore.QPoint(self.viewport().width()/2.0 + delta.x(), self.viewport().height()/2.0 + delta.y())
            
            newCenter = self.mapToScene(center)
            
            self.centerOn(newCenter)
            self.prevPos = event.pos()
            return
        
        super(NodeView, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.drag:
            self.drag = False
            self.setCursor(qt.QtCore.Qt.ArrowCursor)
            self.setDragMode(qt.QGraphicsView.RubberBandDrag)
        super(NodeView, self).mouseReleaseEvent(event) 
        
    def contextMenuEvent(self, event):
        super(NodeView, self).contextMenuEvent(event)
        
        if not event.isAccepted():
        
            self._build_context_menu(event)
        
    def _build_context_menu(self, event):
        
        self.menu = qt.QMenu()
        
        item_action_dict = {}
        
        self.store_action = qt.QAction('Save', self.menu)
        self.rebuild_action = qt.QAction('Open', self.menu)
        self.menu.addAction(self.store_action)
        self.menu.addAction(self.rebuild_action) 
        
        self.menu.addSeparator()
        
        for node_number in register_item:
            
            node_name = register_item[node_number].item_name
            
            item_action = qt.QAction(node_name, self.menu)
            self.menu.addAction(item_action)
            
            item_action_dict[item_action] = node_number
        
        self.menu.addSeparator()
        
        action = self.menu.exec_(event.globalPos())
        
        pos = event.pos()
        pos = self.mapToScene(pos)
        
        if action in item_action_dict:
            node_number = item_action_dict[action]
            self.add_rig_item(node_number, pos)
            
        if action == self.store_action:
            self.save()
            
        if action == self.rebuild_action:
            self.open()
        
    def save(self):
        
        log.info('Save Nodes')
        
        found = []
        
        items = self.main_scene.items()
        
        for item in items:
            
            if not hasattr(item, 'item_type'):
                continue
            
            if item.item_type < ItemType.NODE: 
                if item.item_type != ItemType.LINE:
                    continue
            item_dict = item.store()
            
            found.append(item_dict)
        
        self._cache = found
        
        return found       
           
    def open(self):
        
        if not self._cache:
            return
        
        item_dicts = self._cache
        
        self.main_scene.clear()
        
        lines = []
        
        for item_dict in item_dicts:
            
            type_value = item_dict['type']
            
            if type_value == ItemType.LINE:
                lines.append(item_dict)
            
            if type_value >= ItemType.NODE:
                self._build_rig_item(item_dict)
    
        for line in lines:
            self._build_line(line)
            
    def _build_rig_item(self, item_dict):
        type_value = item_dict['type']
        uuid_value = item_dict['uuid']
        item_inst = register_item[type_value](uuid_value = uuid_value)
        uuids[uuid_value] = item_inst
        
        item_inst.load(item_dict)
        
        if item_inst:
            self.main_scene.addItem(item_inst)
            
    def _build_line(self, item_dict):
        line_inst = NodeLine()
        line_inst.load(item_dict)
        self.main_scene.addItem(line_inst)
        
    def add_rig_item(self, node_type, position):
        
        if node_type in register_item:
            
            item_inst = register_item[node_type]()
            self.main_scene.addItem(item_inst)
            item_inst.setPos(position)    
        
        #box.setPos(window.main_view.main_scene.width()/2.0, window.main_view.main_scene.height()/2.0)
        
class NodeViewDirectory(NodeView):
    def set_directory(self, directory):
        
        self._cache = None
        self.directory = directory
        
        self.main_scene.clear()
        self.open()
        
        
    def get_file(self):
        if not util_file.exists(self.directory):
            util_file.create_dir(self.directory)
            
        path = os.path.join(self.directory, 'ramen.json')
        
        return path
        
    def save(self):
        result = super(NodeViewDirectory, self).save()
        
        filepath = self.get_file()
        
        util_file.set_json(filepath, self._cache, append = False)
        
        util.show('Saved to: %s' % filepath)
        
        return result
    
    def open(self):
        if not self._cache:
            filepath = self.get_file()
            if filepath and util_file.exists(filepath):
                self._cache = util_file.get_json(filepath)
        
        super(NodeViewDirectory, self).open()
     
class NodeScene(qt.QGraphicsScene):    
    node_disconnect = qt.create_signal(object, object)
    node_connect = qt.create_signal(object) 
    node_selected = qt.create_signal(object) 
    node_deleted = qt.create_signal(object)
    
    def __init__(self):
        super(NodeScene, self).__init__()
        self.selection = None
        self.selectionChanged.connect(self._selection_changed)

    def mouseMoveEvent(self, event):
        super(NodeScene, self).mouseMoveEvent(event)
        
        if not self.selection or len(self.selection) == 1:
            return
        
        sockets = []
        
        for item in self.selection:
            
            sockets+=item._in_sockets
            sockets+=item._out_sockets
                
        visited = {}
        for socket in sockets:
            if socket in visited:
                continue
            if hasattr(socket, 'lines'):
                for line in socket.lines:
                    if line.source and line.target:
                        line.pointA = line.source.get_center()
                        line.pointB = line.target.get_center()
            
            visited[socket] = None
        
    def _selection_changed(self):
        
        items = self.selectedItems()
        
        if items:
            self.selection = items
        else:
            self.selection = []
        
        self.node_selected.emit(items)
    
        
class SideMenu(qt.QFrame):
    def __init__(self, parent = None):
        super(SideMenu, self).__init__(parent)
        self.setObjectName('side_menu')
        self._build_widgets()
        
        self._items = []
        self._group_widgets = []

    def _build_widgets(self):
        # Frame.
        self.setFixedWidth(200)
        
        
        self.main_layout = qt.QVBoxLayout(self)
        self.main_layout.setAlignment(qt.Qt.AlignCenter)
        
    def _clear_widgets(self):
        for widget in self._group_widgets:
                
            self.main_layout.removeWidget(widget)
            widget.deleteLater()
            
        self._group_widgets = []
        
    @property
    def items(self):
        return self._items
    
    @items.setter
    def items(self, items):
        self._items = items
        
        self._clear_widgets()
        
        for item in self._items:
            name = item.name
            
            group = qt_ui.Group(name)
            self.main_layout.addWidget(group)
            self._group_widgets.append(group)
            
            if hasattr(item, '_rig'):
                
                rig_class = item._rig
                node_attributes = rig_class.get_node_attributes()
                
                for attribute in node_attributes:
                    
                    value, attr_type = rig_class.get_node_attribute(attribute)
                    
                    if attr_type == rigs.AttrType.STRING:
                        string_attr = qt_ui.GetString(attribute)
                        string_attr.set_text(value)
                        group.main_layout.addWidget(string_attr)
              
#--- widgets

class AttributeItem(object):

    name = None
    value = None
    data_type = None

    def __init__(self):
        
        self.name = None
        self.value = None
        self.data_type = None

class BaseAttributeItem(object):
    
    item_type = None
    
    name = None
    value = None
    data_type = None
    
    def __init__(self):
        
        self._name = None
        self._value = None
        self._data_type = None
    
    def store(self):
        
        item_dict = {}    
        item_dict['type'] = self.item_type
        
        return item_dict
        
    
    def load(self, item_dict):
        pass
    def _get_value(self):
        return self._value
    
    def _set_value(self, value):
        self._value = value
        
    @property
    def value(self):
        return self._get_value()
    
    @value.setter
    def value(self, value):
        if hasattr(self, 'blockSignals'):
            self.blockSignals(True)
        
        self._set_value(value)
        
        if hasattr(self, 'blockSignals'):
            self.blockSignals(False)
            
    @property
    def name(self):
        return self._name
    
    @name.setter
    def name(self, name):
        self._name = name
    
    @property
    def data_type(self):
        return self._data_type
    
    @data_type.setter
    def data_type(self, data_type):
        self._data_type = data_type
        

class ProxyItem(qt.QGraphicsProxyWidget, BaseAttributeItem):
    
    item_type = ItemType.PROXY
    changed = qt.create_signal(object) 
    
    def __init__(self, parent = None):
        
        super(ProxyItem, self).__init__(parent)
        BaseAttributeItem.__init__(self)
        
        self.widget = self._widget()
        
        if self.widget:
            self.setWidget(self.widget)
        
        self.setPos(10,10)
        
    def _widget(self):
        widget = None
        return widget
    
    def store(self):
        
        item_dict = {}
        
        item_dict['name'] = self.attribute.name
        item_dict['data_type'] = self.attribute.data_type
        item_dict['value'] = self.value
        
        item_dict['widget_value'] = {} 
        
        for widget in self._widgets:
            
            name = widget.attribute.name
            value = widget.value
            data_type = widget.attribute.data_type
            
            item_dict['widget_value'][name] = {'value':value, 
                                               'data_type':data_type}

        return item_dict
    
    def load(self, item_dict):
        
        self.attribute.name = item_dict['name']
        self.attribute.data_type = item_dict['data_type']
        self.attribute.value = self.value = item_dict['value']
    
        for widget_name in item_dict['widget_value']:
            
            value = item_dict['widget_value'][widget_name]['value']
            widget = self.get_widget(widget_name)
            
            if widget:
                widget.value = value
    
    
class LineEditItem(ProxyItem):

    def _widget(self):
        widget = qt.QLineEdit()
        style = qt_ui.get_style()
        widget.setStyleSheet(style)
        
        widget.setMaximumWidth(130)
        widget.setMaximumHeight(20)        
        return widget
    
    def _get_value(self):
        return str(self.widget.text())
    
    def _set_value(self, value):
        super(LineEditItem, self)._set_value(value)
        self.widget.setText(value)

class ComboBoxItem(ProxyItem):
    
    def _widget(self):
        widget = qt.QComboBox()
        widget.setMinimumWidth(125)
        #widget.setMaximumWidth(130)
        widget.setMaximumHeight(20)       
        return widget               

    def _get_value(self):
        return self.widget.currentIndex()

    def _set_value(self, value):
        super(ComboBoxItem, self)._set_value(value)
        self.widget.setCurrentIndex(value)


class ColorPickerItem(qt.QGraphicsObject, BaseAttributeItem):
    
    item_type = ItemType.WIDGET
    color_changed = qt_ui.create_signal(object)
    
    def __init__(self):
        super(ColorPickerItem, self).__init__()
        BaseAttributeItem.__init__(self)
        
        self._name = 'color'
        
        self.rect = qt.QtCore.QRect(10,10,50,20)
        
        
        # Brush.
        self.brush = qt.QBrush()
        self.brush.setStyle(qt.QtCore.Qt.SolidPattern)
        self.brush.setColor(qt.QColor(90,90,90,255))

        # Pen.
        self.pen = qt.QPen()
        self.pen.setStyle(qt.QtCore.Qt.SolidLine)
        self.pen.setWidth(1)
        self.pen.setColor(qt.QColor(20,20,20,255))

        self.selPen = qt.QPen()
        self.selPen.setStyle(qt.QtCore.Qt.SolidLine)
        self.selPen.setWidth(3)
        self.selPen.setColor(qt.QColor(255,255,255,255))

    def paint(self, painter, option, widget):
        painter.setBrush(self.brush)
        if self.isSelected():
            painter.setPen(self.selPen)
        else:
            painter.setPen(self.pen)
        
        painter.drawRoundedRect(self.rect, 10,10)
        
        #painter.drawRect(self.rect)

    def mousePressEvent(self, event):
        
        super(ColorPickerItem, self).mousePressEvent(event)
        
        color_dialog = qt.QColorDialog
        color = color_dialog.getColor()
        
        self.brush.setColor(color)
        self.update()

        self.color_changed.emit(self.value)

    def boundingRect(self):
        return qt.QtCore.QRectF(self.rect)

    def _get_value(self):
        color = self.brush.color()
        color_value =  color.getRgbF()
        color_value = [color_value[0], color_value[1], color_value[2]]
        return color_value
    
    def _set_value(self, value):
        super(ColorPickerItem, self)._set_value(value)
        if not value:
            return
        color = qt.QColor()
        color.setRgbF(value[0],value[1],value[2], 1.0)
        self.brush.setColor(color)
        


#--- socket
        
class NodeSocket(qt.QGraphicsItem, BaseAttributeItem):

    item_type = ItemType.SOCKET
    
    def __init__(self, socket_type = SocketType.IN, name = None, value = None, data_type = None):
        super(NodeSocket, self).__init__()
        BaseAttributeItem.__init__(self)
        
        self._name = name
        self._value = value
        self._data_type = data_type
        
        self.socket_type = socket_type
        
        if self._name:
            split_name = self._name.split('_')
            if split_name:
                found = []
                for name in split_name:
                    name = name.capitalize()
                    found.append(name)
                self.nice_name = ' '.join(found)
            else:
                self.nice_name = self._name.capitalize()
        else:
            self.nice_name = None
            
        self.draw_socket(socket_type, data_type)
        
    def draw_socket(self, socket_type, data_type):
        self.rect = qt.QtCore.QRectF(0,0,0,0)        
        
        self.side_socket_height = 12

        # Brush.
        self.brush = qt.QBrush()
        self.brush.setStyle(qt.QtCore.Qt.SolidPattern)
        self.brush.setColor(qt.QColor(60,60,60,255))
        

        # Pen.
        self.pen = qt.QPen()
        
        self.color = qt.QColor(60,60,60,255)
        
        self.pen.setColor(qt.QColor(200,200,200,255))
        
        if data_type == rigs.AttrType.TRANSFORM:
            self.color = qt.QColor(100,200,100,255)
        if data_type == rigs.AttrType.STRING:
            self.color = qt.QColor(100,150,220,255)
        if data_type == rigs.AttrType.COLOR:
            self.color = qt.QColor(220,150,100,255)
        
        self.brush.setColor(self.color)
        
        if socket_type == SocketType.IN:
            
            self.rect = qt.QtCore.QRect(-10, self.side_socket_height, 20,20)
            
            #self.setFlag(self.ItemStacksBehindParent)
            
        if socket_type == SocketType.OUT:
            
            self.rect = qt.QtCore.QRect(148, self.side_socket_height, 20,20)
            
        if socket_type == SocketType.TOP:
            self.rect = qt.QtCore.QRect(10, -10, 15,15)

        self.lines = []
    


    def boundingRect(self):
        return qt.QtCore.QRectF(self.rect)

    def paint(self, painter, option, widget):
        painter.setBrush(self.brush)
        painter.setPen(self.pen)
        self.pen.setStyle(qt.QtCore.Qt.NoPen)
        self.pen.setWidth(0)
        painter.setPen(self.pen)
        
        
        
        if self.socket_type == SocketType.IN:      
            
            rect = qt.QtCore.QRectF(self.rect)
            rect.adjust(3,3,-3,-3)
            painter.drawEllipse(rect)
            
            self.pen.setStyle(qt.QtCore.Qt.SolidLine)
            self.pen.setWidth(1) 
            painter.setPen(self.pen)
            
            painter.drawText(qt.QtCore.QPoint(15,self.side_socket_height+12),self.nice_name)
            
        if self.socket_type == SocketType.OUT:
            
            poly = qt.QPolygon()
            
            poly.append( qt.QtCore.QPoint(0,3) )
            poly.append( qt.QtCore.QPoint(0,17) )
            poly.append( qt.QtCore.QPoint(6,17) )
            
            poly.append( qt.QtCore.QPoint(14,12) )
            poly.append( qt.QtCore.QPoint(15,10) )
            poly.append( qt.QtCore.QPoint(14,8) )
            
            poly.append( qt.QtCore.QPoint(6, 3) )
            
            
            poly.translate(self.rect.x(), self.rect.y())
            painter.drawPolygon(poly)
            
            self.pen.setStyle(qt.QtCore.Qt.SolidLine)
            self.pen.setWidth(1)
            painter.setPen(self.pen)
            name_len = painter.fontMetrics().width(self.nice_name)
            offset = 140 - name_len
            painter.drawText(qt.QtCore.QPoint(offset,self.side_socket_height+12),self.nice_name)
            
        if self.socket_type == SocketType.TOP:
            
            rect = qt.QtCore.QRectF(self.rect)
            painter.drawRect(rect)
             
            self.pen.setStyle(qt.QtCore.Qt.SolidLine)
            self.pen.setWidth(1)
            painter.setPen(self.pen)
            height = self.rect.height()
            
            #painter.drawText(qt.QtCore.QPoint(15,height+5), self.nice_name)
            

    def mousePressEvent(self, event):
        
        self.new_line = None
        
        if self.socket_type == SocketType.OUT:
            pointA = self.get_center()
            
            pointB = self.mapToScene(event.pos())
            self.new_line = NodeLine(pointA, pointB)
            
            #self.new_line.stackBefore()
            
        elif self.socket_type == SocketType.IN:
            
            pointA = self.mapToScene(event.pos())
            pointB = self.get_center()
                        
            self.new_line = NodeLine(pointA, pointB)
            
            #self.new_line.stackBefore()

        else:
            super(NodeSocket, self).mousePressEvent(event)        
        """    
        elif self.socket_type == 'top':
            pointA = self.mapToScene(event.pos())
            pointB self.get_center()
            
            self.new_line = NodeLine(pointA,pointB)
            self.lines.append(self.new_line)
            self.scene().addItem(self.new_line)
        """    
        
        if self.new_line:
            self.lines.append(self.new_line)
            self.scene().addItem(self.new_line)
            self.new_line.color = self.color
            

    def mouseMoveEvent(self, event):
        if self.socket_type == SocketType.OUT:
            pointB = self.mapToScene(event.pos())
            self.new_line.pointB = pointB
        elif self.socket_type == SocketType.IN:
            pointA = self.mapToScene(event.pos())
            self.new_line.pointA = pointA
        else:
            super(NodeSocket, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        
        self.new_line.hide()
        
        item = self.scene().itemAt(event.scenePos().toPoint(), qt.QTransform())
        
        self.new_line.show()
        
        connection_pass = True
        
        if item:
            
            if self.data_type != item.data_type:
                
                if self.socket_type == SocketType.IN and not self.data_type == rigs.AttrType.ANY:
                    connection_pass = False
                    
                if item.socket_type == SocketType.IN and not item.data_type == rigs.AttrType.ANY:
                    connection_pass = False
                    
        if not connection_pass:
            self.remove_line(self.new_line)
            self.new_line = None
            util.warning('Cannot connect sockets of different type.')
            return
        
        if not item:
            self.remove_line(self.new_line)
            self.new_line = None   
            return 
        
        if item == self.new_line or not hasattr(item, 'socket_type'):
            self.remove_line(self.new_line)
            self.new_line = None
            return
        if self.socket_type == item.socket_type:
            self.remove_line(self.new_line)
            self.new_line = None
            return
        if self.socket_type == SocketType.OUT and item.socket_type == SocketType.IN:
            self.new_line.source = self
            self.new_line.target = item            
            self.new_line.pointB = item.get_center()
            
        elif self.socket_type == SocketType.OUT and item.socket_type == SocketType.TOP:
            self.new_line.source = self
            self.new_line.target = item
            self.new_line.pointB = item.get_center()
            
        elif self.socket_type == SocketType.TOP and item.socket_type == SocketType.OUT:
            self.new_line.source = item
            self.new_line.target = self
            self.new_line.pointA = item.get_center()
            
        elif self.socket_type == SocketType.IN and item.socket_type == SocketType.OUT:
            self.new_line.source = item
            self.new_line.target = self
            self.new_line.pointA = item.get_center()
            
        else:
            super(NodeSocket, self).mouseReleaseEvent(event)
            
        if self.new_line:
            item.lines.append(self.new_line)
            self.scene().node_connect.emit(self.new_line)  

    def remove_line(self, line_item):
        
        removed = False
        
        if line_item in self.lines:
            
            if line_item.source:
                line_item.source.lines.remove(line_item)
            if line_item.target:
                line_item.target.lines.remove(line_item)
            
            if line_item in self.lines:
                self.lines.remove(line_item)
                
            removed = True
        
        if removed:
            self.scene().removeItem(line_item)
            

    def get_center(self):
        rect = self.boundingRect()
        
        if self.socket_type == SocketType.OUT:
            center = qt.QtCore.QPointF(rect.x() + rect.width()-5, rect.y() + rect.height()/2)      
        if self.socket_type == SocketType.IN:
            center = qt.QtCore.QPointF(rect.x() + rect.width()/2.0, rect.y() + rect.height()/2.0)
        if self.socket_type == SocketType.TOP:
            center = qt.QtCore.QPointF(rect.x() + rect.width()/2.0, rect.y() + rect.height()/2.0)
        
        center = self.mapToScene(center)
        
        return center   
    
class NodeLine(qt.QGraphicsPathItem):
    
    item_type = ItemType.LINE
    
    def __init__(self, pointA = None, pointB = None):
        super(NodeLine, self).__init__()
        
        self._pointA = pointA
        self._pointB = pointB
        self._source = None
        self._target = None
        self.setZValue(3)
        
        self.brush = qt.QBrush()
        self.brush.setStyle(qt.QtCore.Qt.SolidPattern)
        self.brush.setColor(qt.QColor(200,200,200,255))
        
        
        self.pen = qt.QPen()
        self.pen.setStyle(qt.QtCore.Qt.SolidLine)
        self.pen.setWidth(2)
        self.pen.setColor(qt.QColor(200,200,200,255))
        self.setPen(self.pen)

    def mousePressEvent(self, event):
        self.pointB = event.pos()

    def mouseMoveEvent(self, event):
        self.pointB = event.pos()
        
    def mouseReleaseEvent(self, event):
        
        items = self.scene().items(event.scenePos().toPoint())
        for item in items:
            if hasattr(item, 'item_type'):
                if item.item_type == ItemType.SOCKET:
                    if item.socket_type == SocketType.IN:
                        self.pointB = item.get_center()
                        return
        
        self._source.remove_line(self)
        self._target.remove_line(self)
        
        self._target.scene().node_disconnect.emit(self.source, self.target)
        
    def update_path(self):
        path = qt.QPainterPath()
        path.moveTo(self.pointA)
        dx = self.pointB.x() - self.pointA.x()
        dy = self.pointB.y() - self.pointA.y()
        #ctrl1 = qt.QtCore.QPointF(self.pointA.x() + dx * 0.25, self.pointA.y() + dy * 0.1)
        #ctrl2 = qt.QtCore.QPointF(self.pointA.x() + dx * 0.75, self.pointA.y() + dy * 0.9)
        ctrl1 = qt.QtCore.QPointF(self.pointA.x() + dx * 0.5, self.pointA.y() + dy * 0.1)
        ctrl2 = qt.QtCore.QPointF(self.pointA.x() + dx * 0.5, self.pointA.y() + dy * 0.9)
        
        path.cubicTo(ctrl1, ctrl2, self.pointB)
        
        self.setPath(path)

    def paint(self, painter, option, widget):
        
        if hasattr(self, 'color'):
            color = self.color.darker(70)
            self.brush.setColor(color)
            self.pen.setColor(color)
        
        path = self.path()
        painter.setPen(self.pen)
        painter.drawPath(path)
        
        painter.setBrush(self.brush)
        painter.drawEllipse(self.pointB.x() - 2,self.pointB.y() - 2 ,5,5)
        
        #draw arrow
        
        if path.length() < 50:
            return
        
        point = path.pointAtPercent(0.5)
        point_test = path.pointAtPercent(0.51)
        
        point_orig = qt.QtCore.QPointF(point.x() + 1.0, point.y())
        
        point_orig = point_orig-point
        point_test = point_test-point
        
        dot = point_orig.x()*point_test.x() + point_orig.y()*point_test.y()
        det = point_orig.x()*point_test.y() - point_orig.y()*point_test.x()
        angle = math.atan2(det, dot)
        
        poly = qt.QPolygonF()
        poly.append( qt.QtCore.QPointF(math.cos(angle) * 0 - math.sin(angle) * -5,  
                                       math.sin(angle) * 0 + math.cos(angle) * -5) )
        poly.append( qt.QtCore.QPointF(math.cos(angle) * 10 - math.sin(angle) * 0,  
                                 math.sin(angle) * 10 + math.cos(angle) * 0)   )
         
        poly.append( qt.QtCore.QPointF(math.cos(angle) * 0 - math.sin(angle) * 5,
                                 math.sin(angle) * 0 + math.cos(angle) * 5)     )
        
        poly.translate(point.x(), point.y())
        
        painter.drawPolygon(poly)
        
    @property
    def pointA(self):
        return self._pointA

    @pointA.setter
    def pointA(self, point):
        self._pointA = point
        self.update_path()

    @property
    def pointB(self):
        return self._pointB

    @pointB.setter
    def pointB(self, point):
        self._pointB = point
        self.update_path()

    @property
    def source(self):
        return self._source

    @source.setter
    def source(self, widget):
        self._source = widget

    @property
    def target(self):
        return self._target

    @target.setter
    def target(self, widget):
        self._target = widget
        
    def store(self):
        item_dict = {}
        
        source = self._source
        target = self._target
        
        item_dict['type'] = self.item_type
        
        if source:
            item_dict['source'] = source.parentItem().uuid
            item_dict['source name'] = source.name
        if target:
            item_dict['target'] = target.parentItem().uuid
            item_dict['target name'] = target.name
        
        return item_dict 

    def load(self, item_dict):
        
        if not 'source' in item_dict:
            return
        
        source_uuid = item_dict['source']
        target_uuid = item_dict['target']
        
        source_name = item_dict['source name']
        target_name = item_dict['target name']
        
        if source_uuid in uuids and target_uuid in uuids:
            
            source_item = uuids[source_uuid]
            target_item = uuids[target_uuid]
            
            
            source_socket = source_item.get_socket(source_name)
            target_socket = target_item.get_socket(target_name)
            
            if not target_socket:
                return
            
            centerA = source_socket.get_center()
            centerB = target_socket.get_center()
            
            self._pointA = centerA
            self._pointB = centerB
            self._source = source_socket
            self._target = target_socket
            
            source_socket.lines.append(self)
            target_socket.lines.append(self)
            
            self.update_path()
            
            self.color = source_socket.color

#--- nodes

class GraphicsItem(qt.QGraphicsItem):
    def __init__(self, parent = None):
        super(GraphicsItem, self).__init__(parent)
        self.draw_node()

    def draw_node(self):
        
        self._left_over_space = 0
        self._current_socket_pos = 0
        
        self.rect = qt.QtCore.QRect(0,0,150,40)
        self.setFlag(qt.QGraphicsItem.ItemIsMovable)
        self.setFlag(qt.QGraphicsItem.ItemIsSelectable)
        
        
        # Brush.
        self.brush = qt.QBrush()
        self.brush.setStyle(qt.QtCore.Qt.SolidPattern)
        self.brush.setColor(qt.QColor(68,68,68,255))

        # Pen.
        self.pen = qt.QPen()
        self.pen.setStyle(qt.QtCore.Qt.SolidLine)
        self.pen.setWidth(2)
        self.pen.setColor(qt.QColor(120,120,120,255))

        self.selPen = qt.QPen()
        self.selPen.setStyle(qt.QtCore.Qt.SolidLine)
        self.selPen.setWidth(3)
        self.selPen.setColor(qt.QColor(255,255,255,255))        

    def boundingRect(self):
        return qt.QtCore.QRectF(self.rect)

    def paint(self, painter, option, widget):
        painter.setBrush(self.brush)
        if self.isSelected():
            painter.setPen(self.selPen)
        else:
            painter.setPen(self.pen)
        
        painter.drawRoundedRect(self.rect, 5,5)
        
        pen = qt.QPen()
        pen.setStyle(qt.QtCore.Qt.SolidLine)
        pen.setWidth(1)
        pen.setColor(qt.QColor(255,255,255,255))   
        painter.setPen(pen)     
        painter.drawText(35,-5,self.name )
        
        self.setZValue(1)
        #painter.drawRect(self.rect)

    def contextMenuEvent(self, event):
        self._build_context_menu(event)
        event.setAccepted(True)
        
    def _build_context_menu(self, event):
        
        menu = qt.QMenu()
        
        add_in_socket = menu.addAction('add in socket')
        add_out_socket = menu.addAction('add out socket')
        add_top_socket = menu.addAction('add top socket')
        add_line_edit = menu.addAction('add line edit')
        add_combo = menu.addAction('add combo')
        add_color = menu.addAction('add color')
        
        selected_action = menu.exec_(event.screenPos())

        if selected_action == add_line_edit:
            self.add_line_edit()
            
        if selected_action == add_combo:
            self.add_combo_box()
            
        if selected_action == add_color:
            self.add_color_picker()

        if selected_action == add_top_socket:
            self.add_top_socket('parent','', None)

        if selected_action == add_in_socket:
            self.add_in_socket('goo','', None)
            
        if selected_action == add_out_socket:
            self.add_out_socket('foo','', None)
         
    def _add_space(self, item, offset = 0):
        
        y_value = 0
        offset_y_value = 0
        
        if self._left_over_space:
            
            y_value += self._left_over_space
            
            self._left_over_space = 0
        
        if item.item_type == ItemType.PROXY:
            offset_y_value += 15
        
            
        y_value = self._current_socket_pos + offset + offset_y_value
        
        
        
        self.rect = qt.QtCore.QRect(0,0,150,y_value + 35)
        
        item.setY(y_value)
        
        y_value += 16
        
        #print('past socket pos', self._current_socket_pos)
        
        #if y_value == 0:
        #    y_value = 16
        
        self._current_socket_pos = y_value
        self._left_over_space = offset

class NodeItem(GraphicsItem):
    
    item_type = ItemType.NODE
    item_name = 'Node'
    
    
    def __init__(self, name = '', uuid_value = None):
        super(NodeItem, self).__init__()
        
        if not uuid_value:
            self.uuid = str(uuid.uuid4())
        else:
            self.uuid = uuid_value
        
        uuids[self.uuid] = self
        
        self.dirty = True
        
        self.rig = self._init_rig_class_instance()
        self.rig.uuid = self.uuid
        
        if not name:
            self.name = self.item_name
        else:
            self.name = name
        
        
        
        self._widgets = []
        self._in_sockets = {}
        self._out_sockets = {}
        self._sockets = {}
        self._dependency = {}
        self._build_items()
    
    def _init_rig_class_instance(self):
        return rigs.Base()

    def mouseMoveEvent(self, event):
        super(NodeItem, self).mouseMoveEvent(event)
        
        
        selection = self.scene().selectedItems()
        if len(selection) > 1:
            return
        
        for name in self._out_sockets:
            socket = self._out_sockets[name]
            for line in socket.lines:
                line.pointA = line.source.get_center()
                line.pointB = line.target.get_center()
        
        for name in self._in_sockets:
            socket = self._in_sockets[name]
            for line in socket.lines:
                line.pointA = line.source.get_center()
                line.pointB = line.target.get_center()
    
    #def mousePressEvent(self, event):
    #    super(NodeItem, self).mousePressEvent(event)
        
    #    self.scene().node_selected.emit(self)



    def _disconnect_lines(self):
        other_sockets = {}
        
        for name in self._in_sockets:
            socket = self._in_sockets[name]
            if not hasattr(socket, 'lines'):
                continue
            for line in socket.lines:
                line.target = None
                
                if not line.source in other_sockets:
                    other_sockets[line.source] = [] 
                    
                other_sockets[line.source].append(line)
                
                self.scene().removeItem(line)

            socket.lines = []
        
        for name in self._out_sockets:
            socket = self._out_sockets[name]
            if not hasattr(socket, 'lines'):
                continue
            
            for line in socket.lines:
                line.source = None
                
                if not line.target in other_sockets:
                    other_sockets[line.target] = []
                
                other_sockets[line.target].append(line)
                    
                self.scene().removeItem(line)
                    
        
            socket.lines = []
        
        for socket in other_sockets:
            lines = other_sockets[socket]
            
            for line in lines:
                if line in socket.lines:
                    socket.lines.remove(line)

    def add_top_socket(self, name, value, data_type):
        
        socket = NodeSocket('top', name, value, data_type)
        socket.setParentItem(self)
        
        if not self.rig.attr.exists(name):
            self.rig.attr.add_in(name, value, data_type)
            
        self._in_sockets[name] = socket
        
        return socket
    
    def add_in_socket(self, name, value, data_type):
        
        socket = NodeSocket('in', name, value, data_type)
        socket.setParentItem(self)
        self._add_space(socket)
        
        if not self.rig.attr.exists(name):
            self.rig.attr.add_in(name, value, data_type)
        
        self._in_sockets[name] = socket
        
        return socket
    
    def add_out_socket(self, name, value, data_type):
        
        socket = NodeSocket('out', name, value, data_type)
        socket.setParentItem(self)
        self._add_space(socket)
        
        if not self.rig.attr.exists(name):
            self.rig.attr.add_out(name, value, data_type)
        
        self._out_sockets[name] = socket
        
        return socket
        
    def add_color_picker(self, name):
        
        color_picker = ColorPickerItem()
        color_picker.name = name
        color_picker.setParentItem(self)
        self._add_space(color_picker,5)
        
        self._widgets.append(color_picker)
        
        if not self.rig.attr.exists(name):
            self.rig.attr.add_to_node(name, color_picker.value, color_picker.data_type)
            
        self._sockets[name] = color_picker 
        
        return color_picker
        
        
    def add_line_edit(self, name):
        
        line_edit = LineEditItem(self)
        line_edit.name = name
        self._add_space(line_edit)
        
        if not self.rig.attr.exists(name):
            self.rig.attr.add_to_node(name, line_edit.value, line_edit.data_type)
        
        self._widgets.append(line_edit)
        
        self._sockets[name] = line_edit
        
        return line_edit
        
    def add_combo_box(self, name):
        
        combo = ComboBoxItem(self)
        combo.name = name
        self._add_space(combo)
        combo.setZValue(combo.zValue() + 1)
        
        if not self.rig.attr.exists(name):
            self.rig.attr.add_to_node(name, combo.value, combo.data_type)
        
        self._widgets.append(combo)
        
        self._sockets[name] = combo
        
        return combo
        
    def delete(self):
        
        if not self.scene():
            return

        self._disconnect_lines()
        
        self.scene().removeItem(self)

    def get_widget(self, name):
        
        for widget in self._widgets:
            if widget.name == name:
                return widget
        
    def set_socket(self, name, value):
        
        socket = self.get_socket(name)
        
        if not socket:
            return
        
        socket.value = value
        self.rig.attr.set(name, value)
        
        
        
        dependency_sockets = None
        
        if name in self._dependency:
            dependency_sockets = self._dependency[name]
        
        if not dependency_sockets:
            return 
        
        for socket_name in dependency_sockets:
            dep_socket = self.get_socket(socket_name)
            value = self.rig.get_attr(socket_name)
            dep_socket.value = value
 
        for name in self._out_sockets:
            out_socket = self._out_sockets[name]

            outputs = self.get_outputs(out_socket.name)
            for output in outputs:
                node = output.parentItem()
                node.run(output.name)

    def get_socket(self, name):
        sockets = {}
        sockets.update(self._in_sockets)
        sockets.update(self._out_sockets)
        sockets.update(self._sockets)
        
        if name in sockets:
            socket = sockets[name]
            return socket
    
    def get_socket_value(self, name):
        socket = self.get_socket(name)
        return socket.value
    
    def get_inputs(self, name):
        found = []
        
        for socket in self._in_sockets:
            
            if socket.name == name:
                for line in socket.lines:
                    found.append(line.source)
                    
        return found        

    def get_outputs(self, name):
        
        found = []
        
        for name in self._out_sockets:
            socket = self._out_sockets[name]
            if socket.name == name:
                
                for line in socket.lines:
                    found.append(line.target)
                    
        return found
    
    def run(self):
          
        util.show('Run %s' % self.__class__.__name__)
        
    def store(self):
        item_dict = {}
        
        item_dict['name'] = self.item_name
        item_dict['uuid'] = self.uuid
        item_dict['type'] = self.item_type
        item_dict['position'] = [self.pos().x(), self.pos().y()]
        
        item_dict['widget_value'] = {} 
        
        for widget in self._widgets:
            
            name = widget.name
            value = widget.value
            data_type = widget.data_type
            
            item_dict['widget_value'][name] = {'value':value, 
                                               'data_type':data_type}
            
            
        
        
        return item_dict
        
        
    def load(self, item_dict):
        
        self.name = item_dict['name']
        position = item_dict['position']
        self.uuid = item_dict['uuid']
        self.setPos(qt.QtCore.QPointF(position[0], position[1]))
        
        for widget_name in item_dict['widget_value']:
            
            value = item_dict['widget_value'][widget_name]['value']
            widget = self.get_widget(widget_name)
            
            if widget:
                widget.value = value
            
    

class ColorItem(NodeItem):
    
    item_type = ItemType.COLOR
    item_name = 'Color'
    
    def _build_items(self):

        picker = self.add_color_picker('color value')
        picker.data_type = rigs.AttrType.COLOR
        self.picker = picker

        picker.color_changed.connect(self._color_changed) 
        
        self.add_out_socket('color', None, rigs.AttrType.COLOR)
        
    def _color_changed(self, color):

        #color_value =  color.getRgbF()
        #color_value = [color_value[0], color_value[1], color_value[2]]
        self.color = color
        
        self.run()
        
        self.color = None
    
    def run(self):
        super(ColorItem, self).run()
        socket = self.get_socket('color')
        if hasattr(self, 'color') and self.color:
            socket.value = self.color
        else:
            socket.value = self.picker.value 
        
        set_socket_value(socket)
        
        return socket.value

class CurveShapeItem(NodeItem):
    
    item_type = ItemType.CURVE_SHAPE
    item_name = 'Curve Shape'

    def _build_items(self):
        
        curve_shapes = rigs.Control.get_curve_shapes()
        
        curve_shapes.insert(0, 'Default')
        
        combo = self.add_combo_box('curve')
        combo.data_type = rigs.AttrType.STRING
        combo.widget.addItems(curve_shapes)
        
        self.add_out_socket('curve_shape', [], rigs.AttrType.STRING)
        
        self._curve_entry_widget = combo
        
        combo.widget.currentIndexChanged.connect(self.run)
        
        #self._joint_entry_widget = text_entry
        #text_entry.returnPressed.connect(self.run)    
    def run(self):
        super(CurveShapeItem, self).run()
        
        curve = self._curve_entry_widget.widget.currentText()
        
        socket = self.get_socket('curve_shape')
        socket.value = curve
        
        set_socket_value(socket)
        
        return curve

class JointsItem(NodeItem):
    
    item_type = ItemType.JOINTS
    item_name = 'Joints'
    
    def _build_items(self):
        
        #self.add_in_socket('Scope', [], rigs.AttrType.TRANSFORM)
        
        line_edit = self.add_line_edit('joint filter')
        line_edit.widget.setPlaceholderText('joint search')
        line_edit.data_type = rigs.AttrType.STRING
        self.add_out_socket('joints', [], rigs.AttrType.TRANSFORM)
        #self.add_socket(socket_type, data_type, name)
        
        self._joint_entry_widget = line_edit
        line_edit.widget.returnPressed.connect(self.run)
        
    def _get_joints(self):
        filter_text = self._joint_entry_widget.widget.text()
        
        joints = util_ramen.get_joints(filter_text)
        
        return joints
        
        
    def run(self):
        super(JointsItem, self).run()
        
        joints = self._get_joints()
        if joints == None:
            joints = []
        
        util.show('Found: %s' % joints)
        
        socket = self.get_socket('joints')
        socket.value = joints
        
        set_socket_value(socket)
        
        return joints
        
        

class ImportDataItem(NodeItem):
    
    item_type = ItemType.DATA
    item_name = 'Import Data'
    
    def _build_items(self):
        
        line_edit = self.add_line_edit('data name')
        line_edit.widget.setPlaceholderText('data name')
        line_edit.data_type = rigs.AttrType.STRING
        self.add_in_socket('eval', [], rigs.AttrType.EVALUATION)
        
        self.add_out_socket('result', [], rigs.AttrType.STRING)
        self.add_out_socket('eval', [], rigs.AttrType.EVALUATION)
        
        
        self._data_entry_widget = line_edit
        line_edit.widget.returnPressed.connect(self.run)
        
    def run(self):
        super(ImportDataItem, self).run()
        
        process_inst = process.get_current_process_instance()
        result = process_inst.import_data(self._data_entry_widget.value, sub_folder=None)
        
        if result == None:
            result = []
        
        socket = self.get_socket('result')
        socket.value = result
        
        set_socket_value(socket)
        
        return result
        

class PrintItem(NodeItem):

    item_type = ItemType.PRINT
    item_name = 'Print'
    
    def _build_items(self):
        
        self.add_in_socket('input', [], rigs.AttrType.ANY)
        
    def run(self):
        super(PrintItem, self).run()
        
        socket = self.get_socket('input')
        util.show(socket.value)

class SetSkeletalMeshItem(NodeItem):
    item_type = ItemType.UNREAL_SKELETAL_MESH
    item_name = 'Set Skeletal Mesh'

    def _build_items(self):
        self.add_in_socket('input',[], rigs.AttrType.STRING)

    def run(self):
        super(SetSkeletalMeshItem, self).run()

        socket = self.get_socket('input')
        
        util.show(socket.value)
        
        for path in socket.value:
            if unreal_lib.util.is_skeletal_mesh(path):
                unreal_lib.util.set_skeletal_mesh(path)
                
                break

class RigItem(NodeItem):
    
    item_type = ItemType.RIG
    
    def __init__(self, name = '', uuid_value = None):
        
        super(RigItem, self).__init__(name, uuid_value)
        
        self.rig.load()
        
        #self.run()

    def _init_rig_class_instance(self):
        return rigs.Rig()

    def _build_items(self):
        
        self._current_socket_pos = 1
        
        if self.rig:
            ins = self.rig.get_ins()
            outs = self.rig.get_outs()
            items = self.rig.get_node_attributes()
            
            self._dependency.update( self.rig.get_attr_dependency() ) 

            for node_attr_name in items:
                
                value, attr_type = self.rig.get_node_attribute(node_attr_name)
                if attr_type == rigs.AttrType.STRING:
                    line_edit = self.add_line_edit(node_attr_name)
                    line_edit.widget.setPlaceholderText(node_attr_name)
                    line_edit.data_type = attr_type
                    
                    line_edit.value = value
                    line_edit.widget.returnPressed.connect(self.run)
            
            for in_value_name in ins:
                value, attr_type = self.rig.get_in(in_value_name)
                
                if in_value_name == 'parent':
                    self.add_top_socket(in_value_name, value, attr_type)
                else:
                    self.add_in_socket(in_value_name, value, attr_type)
            
            for out_value_name in outs:
                value, attr_type = self.rig.get_out(out_value_name)
                                
                self.add_out_socket(out_value_name, value, attr_type)    
    
    def _run(self, socket):
        
        for name in self._sockets:
            
            node_socket = self._sockets[name]
            self.rig.attr.set(node_socket.name, node_socket.value)
        
        if socket:
            util.show('Running socket %s' % socket.name)
            
            set_socket_value(socket)
        else:
            self.rig.create()
        
    def set_socket(self, name, value):
        super(RigItem, self).set_socket(name, value)
        
        util.show('set %s %s' % (name,value))
        self.rig.set_attr(name, value)

    def run(self, socket = None):
        super(RigItem, self).run()
        
        util.show('Running %s' % self.rig.__class__.__name__)
        
        self._run(socket)
        
        
    def delete(self):
        super(RigItem, self).delete()
        
        self.rig.delete()
        
    def store(self):
        item_dict = super(RigItem, self).store()
        
        item_dict['rig uuid'] = self.rig.uuid
        
        return item_dict
    
    def load(self, item_dict):
        super(RigItem, self).load(item_dict)
        
        """
        rig_uuid = item_dict['rig uuid']
    
        set_name = cmds.ls(rig_uuid)
        
        if set_name:
            set_name = set_name[0]
        self.rig.uuid = rig_uuid
        self.rig._set = set_name
        """
        #rig_dict = item_dict['rig']
        #self.rig.set_data(rig_dict)

class FkItem(RigItem, rigs.Fk):
    
    item_type = ItemType.FKRIG
    item_name = 'FkRig'
    
    def _init_rig_class_instance(self):
        return rigs.Fk()
    
    """    
    def run(self):
        super(FkItem, self).run()
        
        joints_socket = self.get_input('joints')
        
        joints = []
        if joints_socket:
            joints = joints_socket[0].value
        
        self.rig.joints = joints
    """ 

class IkItem(RigItem, rigs.Ik):
    
    item_type = ItemType.IKRIG
    item_name = 'IkRig'
    
    def _init_rig_class_instance(self):
        return rigs.Fk()
    

#--- registry

register_item = {
    #NodeItem.item_type : NodeItem,
    FkItem.item_type : FkItem,
    #IkItem.item_type : IkItem,
    JointsItem.item_type : JointsItem,
    ColorItem.item_type : ColorItem,
    CurveShapeItem.item_type : CurveShapeItem,
    ImportDataItem.item_type : ImportDataItem,
    PrintItem.item_type : PrintItem,
    SetSkeletalMeshItem.item_type : SetSkeletalMeshItem
}