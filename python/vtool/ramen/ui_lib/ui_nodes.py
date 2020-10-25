import uuid
import math
import string

from vtool import qt
from vtool import qt_ui

from vtool import util

in_maya = False
if util.is_in_maya():
    in_maya = True
    import maya.cmds as cmds
    
from vtool.maya_lib2 import rigs

uuids = {}    

def set_socket_value(socket):
    
    if not socket.lines:
        return
    
    if socket.lines[0].target == socket:
        socket = socket.lines[0].source
        
    value = socket.value    
    
    source_node = socket.parentItem()
    
    outputs = source_node.get_outputs(socket.name)
    
    for output in outputs:
        target_node = output.parentItem()
        
        target_node.set_socket(output.name, value)
        
        dependency_sockets = None
        
        if output.name in target_node._dependency:
            dependency_sockets = target_node._dependency[output.name]
        
        if not dependency_sockets:
            continue
        
        for socket_name in dependency_sockets:
            dep_socket = target_node.get_socket(socket_name)
            value = target_node._rig.get_attr(socket_name)
            dep_socket.value = value

def connect_socket(source_socket, target_socket):
    
    value = source_socket.value
    
    target_node = target_socket.parentItem()
        
    target_node.set_socket(target_socket.name, value)
        
    dependency_sockets = None
    
    if target_socket.name in target_node._dependency:
        dependency_sockets = target_node._dependency[target_socket.name]
    
    if not dependency_sockets:
        return 
    
    for socket_name in dependency_sockets:
        dep_socket = target_node.get_socket(socket_name)
        value = target_node._rig.get_attr(socket_name)
        dep_socket.value = value


def remove_socket_value(socket):

    node = socket.parentItem()
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
    RIG = 20002
    FKRIG = 20003
    IKRIG = 20004

class SocketType(object):
    
    IN = 'in'
    OUT = 'out'
    TOP = 'top'
   
class NodeWindow(qt_ui.BasicGraphicsWindow):
    def __init__(self):
        
        super(NodeWindow, self).__init__()
        self.setWindowTitle('Ramen')
        
    def _define_main_view(self):
        self.main_view = NodeView()
        
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
        
        if node_items:
            self.side_menu.show()
            self.side_menu.nodes = node_items
        else:
            self.side_menu.hide()
            self.side_menu.nodes = []
            
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
        

        
    
            
        
class NodeView(qt_ui.BasicGraphicsView):
    
    def __init__(self, parent = None):
        super(NodeView, self).__init__(parent)
        
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
        pen.setColor(qt.QColor.fromRgbF(0, 0, 0, .25))
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
        
        self.menu.addSeparator()
        
        for node_number in register_item:
            
            node_name = register_item[node_number].item_name
            
            item_action = qt.QAction(node_name, self.menu)
            self.menu.addAction(item_action)
            
            item_action_dict[item_action] = node_number
        
        self.menu.addSeparator()
        
        self.store_action = qt.QAction('store', self.menu)
        self.rebuild_action = qt.QAction('rebuild', self.menu)
        self.menu.addAction(self.store_action)
        self.menu.addAction(self.rebuild_action) 
                
        action = self.menu.exec_(event.globalPos())
        
        pos = event.pos()
        pos = self.mapToScene(pos)
        
        if action in item_action_dict:
            node_number = item_action_dict[action]
            self.add_rig_item(node_number, pos)
            
        if action == self.store_action:
            self._store()
            
        if action == self.rebuild_action:
            self._rebuild()
            
            
        
    def _store(self):
        
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
        
        self._stored_data = found
        return found       
           
    def _rebuild(self):
        
        item_dicts = self._stored_data
        
        self.main_scene.clear()
        
        lines = []
        
        for item_dict in item_dicts:
            
            type_value = item_dict['type']
            
            
            
            if type_value == ItemType.LINE:
                lines.append(item_dict)
            
            if type_value >= ItemType.NODE:
                
                uuid_value = item_dict['uuid']
                
                item_inst = register_item[type_value](uuid_value = uuid_value)
                
                uuids[uuid_value] = item_inst
                
                item_inst.load(item_dict)
                
                if item_inst:
                    self.main_scene.addItem(item_inst)
                     
                    
    
        for line in lines:
            
            line_inst = NodeLine()
            
            line_inst.load(line)
            
            self.main_scene.addItem(line_inst)
                        
            
            
            
    
        #for item in     
            
    
    def add_rig_item(self, node_type, position):
        
        if node_type in register_item:
            
            item_inst = register_item[node_type]()
            self.main_scene.addItem(item_inst)
            #item_inst.setPos(position)
            item_inst.setPos(position)    
        
        #box.setPos(window.main_view.main_scene.width()/2.0, window.main_view.main_scene.height()/2.0)

        
        
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
        
        self._nodes = []
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
    def nodes(self):
        return self._nodes
    
    @nodes.setter
    def nodes(self, nodes):
        self._nodes = nodes
        
        self._clear_widgets()
        
        for node in self._nodes:
            name = node.name
            
            group = qt_ui.Group(name)
            self.main_layout.addWidget(group)
            self._group_widgets.append(group)
            
            if hasattr(node, '_rig'):
                
                rig_class = node._rig
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

class BaseItem(object):

    item_type = None
    
    def store(self):
        
        item_dict = {}    
        item_dict['type'] = self.item_type
        
        return item_dict
        
    
    def load(self, item_dict):
        
        pass

    def _get_value(self):
        return self.attribute.value
    
    def _set_value(self, value):
        self.attribute.value = value
        
    @property
    def value(self):
        return self._get_value()
    
    @value.setter
    def value(self, value):
        self._set_value(value)
        
    @property
    def name(self):
        return self.attribute.name
    
    @name.setter
    def name(self, name):
        self.attribute.name = name
    
    @property
    def data_type(self):
        return self.attribute.data_type
    
    @data_type.setter
    def data_type(self, data_type):
        self.attribute.data_type = data_type
        

class ProxyItem(qt.QGraphicsProxyWidget, BaseItem):
    
    item_type = ItemType.PROXY
    
    def __init__(self, parent = None):
        
        super(ProxyItem, self).__init__(parent)
        
        self.attribute = AttributeItem()
        self.widget = self._widget()
        
        if self.widget:
            self.setWidget(self.widget)
            
        print 'set pos!!!!'
        
        
        self.setPos(10,10)
        
    def _widget(self):
        widget = None
        return widget
    
    def _get_value(self):
        self.attribute.value
    
    def _set_value(self, value):
        self.attribute.value = value
    
    def store(self):
        
        item_dict = {}
        
        item_dict['name'] = self.attribute.name
        item_dict['data_type'] = self.attribute.data_type
        item_dict['value'] = self.value
        
        
    def load(self, item_dict):
        
        self.attribute.name = item_dict['name']
        self.attribute.data_type = item_dict['data_type']
        self.attribute.value = self.value = item_dict['value']
    
    @property
    def value(self):
        return self._get_value()
    
    @value.setter
    def value(self, value):
        if hasattr(self, 'blockSignals'):
            self.blockSignals(True)
        
        self._set_value(value)
        
        if hasattr(self, 'blockSignals'):
            self.blockSignals(True)
        
    
    
    
class LineEditItem(ProxyItem):

    def _widget(self):
        widget = qt.QLineEdit()
        widget.setMaximumWidth(130)
        widget.setMaximumHeight(20)        
        return widget
    
    def _get_value(self):
        return str(self.widget.text())
    
    def _set_value(self, value):
        self.widget.setText(value)

class ComboBoxItem(ProxyItem):
    
    def _widget(self):
        widget = qt.QComboBox()
        widget.setMaximumWidth(130)
        widget.setMaximumHeight(20)       
        return widget               

    def _get_value(self):
        return self.widget.currentIndex()

    def _set_value(self, value):
        self.widget.setCurrentIndex(value)


class ColorPickerItem(qt.QGraphicsObject, BaseItem):
    
    item_type = ItemType.WIDGET
    color_changed = qt_ui.create_signal(object)
    
    def __init__(self):
        super(ColorPickerItem, self).__init__()
        
        self.attribute = AttributeItem()
        
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
        
        self.color_changed.emit(color)

    def boundingRect(self):
        return qt.QtCore.QRectF(self.rect)
        
#--- socket
        
class NodeSocket(qt.QGraphicsItem, BaseItem):

    item_type = ItemType.SOCKET
    
    def __init__(self, socket_type = SocketType.IN, name = None, value = None, data_type = None):
        
        self.attribute = AttributeItem()
        self.attribute.name = name
        self.attribute.value = value
        self.attribute.data_type = data_type
        
        self.socket_type = socket_type
        
        if self.name:
            split_name = self.name.split('_')
            if split_name:
                found = []
                for name in split_name:
                    name = name.capitalize()
                    found.append(name)
                self.nice_name = string.join(found)
            else:
                self.nice_name = self.name.capitalize()
        else:
            self.nice_name = None
        
        super(NodeSocket, self).__init__()
        
        
        
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
            #poly << qt.QtCore.QPoint(0,0) << qt.QtCore.QPoint(0,16) << qt.QtCore.QPoint(20,10) << qt.QtCore.QPoint(20,6)
            poly.append( qt.QtCore.QPoint(0,2) )
            poly.append( qt.QtCore.QPoint(0,18) )
            poly.append( qt.QtCore.QPoint(6,18) )
            #poly.append( qt.QtCore.QPoint(6,13) )
            poly.append( qt.QtCore.QPoint(14,12) )
            poly.append( qt.QtCore.QPoint(15,10) )
            poly.append( qt.QtCore.QPoint(14,8) )
            #poly.append( qt.QtCore.QPoint(6, 7) )
            poly.append( qt.QtCore.QPoint(6, 2) )
            
            
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
            
            painter.drawText(qt.QtCore.QPoint(15,height+5), self.nice_name)
            

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
        
        if item:
            if self.data_type != item.data_type:
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
        
    
class NodeLine(qt.QGraphicsPathItem, BaseItem):
    
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
        item_dict = super(NodeLine, self).store()
        
        source = self._source
        target = self._target
                
        item_dict['source'] = source.parentItem().uuid
        item_dict['target'] = target.parentItem().uuid
        
        item_dict['source name'] = source.name
        item_dict['target name'] = target.name
        
        return item_dict 

    def load(self, item_dict):
        super(NodeLine, self).load(item_dict)
        
        source_uuid = item_dict['source']
        target_uuid = item_dict['target']
        
        source_name = item_dict['source name']
        target_name = item_dict['target name']
        
        if source_uuid in uuids and target_uuid in uuids:
            
            source_item = uuids[source_uuid]
            target_item = uuids[target_uuid]
            
            source_socket = source_item.get_socket(source_name)
            target_socket = target_item.get_socket(target_name)
            
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

class NodeItem(qt.QGraphicsItem, BaseItem):
    
    item_type = ItemType.NODE
    item_name = 'Node'
    
    def __init__(self, name = '', uuid_value = None):
        
        self.attribute = AttributeItem()
        
        if not name:
            self.name = self.item_name
        else:
            self.name = name
        
        if not uuid_value:
            self.uuid = str(uuid.uuid4())
        else:
            self.uuid = uuid_value
            
        
            
        
        self._current_socket_pos = 0
        
        super(NodeItem, self).__init__()
        
        uuids[self.uuid] = self
        
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
        
        self._widgets = []
        self._in_sockets = []
        self._out_sockets = []
        self._dependency = {}
        self._build_items()
        
    """
    def shape(self):
        path = qt.QPainterPath()
        path.addRect(self.boundingRect())
        return path
    """
    
    def _build_items(self):
        #self.add_socket(socket_type, data_type, name)
        pass
        
    def boundingRect(self):
        return qt.QtCore.QRectF(self.rect)

    def paint(self, painter, option, widget):
        painter.setBrush(self.brush)
        if self.isSelected():
            painter.setPen(self.selPen)
        else:
            painter.setPen(self.pen)
        
        painter.drawRoundedRect(self.rect, 10,10)
        
        pen = qt.QPen()
        pen.setStyle(qt.QtCore.Qt.SolidLine)
        pen.setWidth(1)
        pen.setColor(qt.QColor(255,255,255,255))   
        painter.setPen(pen)     
        painter.drawText(35,-10,self.name )
        
        self.setZValue(1)
        #painter.drawRect(self.rect)
    
    def mouseMoveEvent(self, event):
        super(NodeItem, self).mouseMoveEvent(event)
        
        
        selection = self.scene().selectedItems()
        if len(selection) > 1:
            return
        
        for socket in self._out_sockets:
            for line in socket.lines:
                line.pointA = line.source.get_center()
                line.pointB = line.target.get_center()
        
        for socket in self._in_sockets:
            for line in socket.lines:
                line.pointA = line.source.get_center()
                line.pointB = line.target.get_center()
    
    #def mousePressEvent(self, event):
    #    super(NodeItem, self).mousePressEvent(event)
        
    #    print 'here!!!'
    #    self.scene().node_selected.emit(self)

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
         
    def _add_space(self, item):
        
        print 'add space', self._current_socket_pos
        
        if self._current_socket_pos > 0:
            
            print self.rect
            
            height = self.rect.height()
            height += 20
            
            print item.item_type
            
            y_value = 0
            
            if item.item_type == ItemType.PROXY:
                y_value += 10
        
            #print height
        
            self.rect = qt.QtCore.QRect(0,0,150,height)
            
            y_value = self._current_socket_pos * 20 + y_value
            
            
                
            
            print 'y value', y_value
            
            item.setY(y_value)
            
        self._current_socket_pos += 1

    def add_top_socket(self, name, value, data_type):
        
        socket = NodeSocket('top', name, value, data_type)
        socket.setParentItem(self)
        
        self._in_sockets.append(socket)
        #self._add_space(socket)
    
    def add_in_socket(self, name, value, data_type):
        
        socket = NodeSocket('in', name, value, data_type)
        socket.setParentItem(self)
        
        self._in_sockets.append(socket)
        self._add_space(socket)
    
    def add_out_socket(self, name, value, data_type):
        
        socket = NodeSocket('out', name, value, data_type)
        socket.setParentItem(self)
        
        self._out_sockets.append(socket)
        self._add_space(socket)
        
        
    def add_color_picker(self):
        
        color_picker = ColorPickerItem()
        color_picker.setParentItem(self)
        
        self._widgets.append(color_picker)
        
        self._add_space(color_picker)
        
        return color_picker
        
        
    def add_line_edit(self):
        
        line_edit = LineEditItem(self)
               
        self._add_space(line_edit)
        
        self._widgets.append(line_edit)
        
        return line_edit
        
    def add_combo_box(self):
        
        combo = ComboBoxItem(self)
        
        self._add_space(combo)
        
        self._widgets.append(combo)
        
        return combo
        
    def delete(self):
        
        if not self.scene():
            return

        other_sockets = {}
        
        for socket in self._in_sockets:
            
            for line in socket.lines:
                line.target = None
                
                if not line.source in other_sockets:
                    other_sockets[line.source] = [] 
                    
                other_sockets[line.source].append(line)
                
                self.scene().removeItem(line)

            socket.lines = []
        
        for socket in self._out_sockets:
        
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
            
        
        
        self.scene().removeItem(self)

    def get_widget(self, name):
        
        for widget in self._widgets:
            if widget.attribute.name == name:
                return widget
        
    def set_socket(self, name, value):
        
        socket = self.get_socket(name)
        
        socket.value = value
        
        outputs = self.get_outputs('color')
        for output in outputs:
            node = output.parentItem()
            node.run(output.name)
         
 

    def get_socket(self, name):
        
        sockets = self._in_sockets + self._out_sockets
        
        for socket in sockets:
            if socket.name == name:
                return socket
    
    def get_input(self, name):
        found = []
        
        for socket in self._in_sockets:
            
            if socket.name == name:
                for line in socket.lines:
                    found.append(line.source)
                    
        return found        

    def get_outputs(self, name):
        
        found = []
        
        for socket in self._out_sockets:
            
            if socket.name == name:
                
                for line in socket.lines:
                    found.append(line.target)
                    
        return found
    
    def run(self):
          
        util.show('Run %s' % self.__class__.__name__)

    def store(self):
        item_dict = super(NodeItem, self).store()
        
        item_dict['name'] = self.item_name
        item_dict['uuid'] = self.uuid
        item_dict['position'] = [self.pos().x(), self.pos().y()]
        
        item_dict['widget_value'] = {} 
        
        for widget in self._widgets:
            
            name = widget.attribute.name
            value = widget.value
            data_type = widget.attribute.data_type
            
            item_dict['widget_value'][name] = {'value':value, 
                                               'data_type':data_type}
            
            
        
        
        return item_dict
        
        
    def load(self, item_dict):
        
        self.name = item_dict['name']
        position = item_dict['position']
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
        
        picker = self.add_color_picker()
        
        picker.color_changed.connect(self._color_changed) 
        
        self.add_out_socket('color', None, rigs.AttrType.COLOR)
        
    def _color_changed(self, color):
        color_value =  color.getRgbF()
        color_value = [color_value[0], color_value[1], color_value[2]]
        
        self.color = color_value
        
        self.run()
    
    def run(self):
        
        socket = self.get_socket('color')
        socket.value = self.color
        
        set_socket_value(socket)
        
        return self.color

class CurveShapeItem(NodeItem):
    
    item_type = ItemType.CURVE_SHAPE
    item_name = 'Curve Shape'

    def _build_items(self):
        
        curve_shapes = rigs.Control.get_curve_shapes()
        
        curve_shapes.insert(0, 'Default')
        
        combo = self.add_combo_box()
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
        
        line_edit = self.add_line_edit()
        line_edit.widget.setPlaceholderText('joint search')
        self.add_out_socket('joints', [], rigs.AttrType.TRANSFORM)
        #self.add_socket(socket_type, data_type, name)
        
        self._joint_entry_widget = line_edit
        line_edit.widget.returnPressed.connect(self.run)
        
    def _get_joints(self):
        filter_text = self._joint_entry_widget.widget.text()
        
        joints = []
        if util.is_in_maya():
            joints = cmds.ls(filter_text, type = 'joint')
            
        return joints
        
    def run(self):
        super(JointsItem, self).run()
        
        joints = self._get_joints()
        
        util.show('Found: %s' % joints)
        
        socket = self.get_socket('joints')
        socket.value = joints
        
        set_socket_value(socket)
        
        return joints
        
        

class RigItem(NodeItem):
    
    item_type = ItemType.RIG
    
    def __init__(self, name = '', uuid_value = None):
        
        self._rig = self._init_rig_class_instance()
        
        
        super(RigItem, self).__init__(name, uuid_value)
    
        
        
    
        
        
    def _build_items(self):
        
        self._current_socket_pos = 1
        
        if self._rig:
            ins = self._rig.get_ins()
            outs = self._rig.get_outs()
            nodes = self._rig.get_node_attributes()
            
            self._dependency.update( self._rig.get_attr_dependency() ) 

            for node_attr_name in nodes:
                value, attr_type = self._rig.get_node_attribute(node_attr_name)
                
                if attr_type == rigs.AttrType.STRING:
                    line_edit = self.add_line_edit()
                    line_edit.widget.setPlaceholderText(node_attr_name)
                    line_edit.name = node_attr_name
                    line_edit.data_type = attr_type
                    
                    line_edit.value = value
            
            for in_value_name in ins:
                
                value, attr_type = self._rig.get_in(in_value_name)
                
                if in_value_name == 'parent':
                    self.add_top_socket(in_value_name, value, attr_type)
                else:
                    self.add_in_socket(in_value_name, value, attr_type)
            
            for out_value_name in outs:
                
                value, attr_type = self._rig.get_out(out_value_name)
                                
                self.add_out_socket(out_value_name, value, attr_type)    
            
            

                 
    
    def _init_rig_class_instance(self):
        return None

    def _pre_run(self):
        pass
    
    def _run(self, socket):
        if socket:
            util.show('Running socket %s' % socket.name)
            
            set_socket_value(socket)
            
    def _post_run(self):
        pass
        

    def set_socket(self, name, value):
        super(RigItem, self).set_socket(name, value)
        
        self._rig.set_attr(name, value)

    def run(self, socket = None):
        super(RigItem, self).run()
        
        util.show('Running %s' % self._rig.__class__.__name__)
        
        self._pre_run()
        self._run(socket)
        self._post_run()
        
        
    def delete(self):
        super(RigItem, self).delete()
        
        self._rig.delete()
        
    def store(self):
        item_dict = super(RigItem, self).store()
        
        rig_data = self._rig.get_data()
        item_dict['rig'] = rig_data
        item_dict['rig uuid'] = self._rig.uuid
        
        return item_dict
    
    def load(self, item_dict):
        super(RigItem, self).load(item_dict)
        
        if in_maya:
            rig_uuid = item_dict['rig uuid']
        
            set_name = cmds.ls(rig_uuid)
            
            if set_name:
                set_name = set_name[0]
            self._rig.uuid = rig_uuid
            self._rig._set = set_name
            
            rig_dict = item_dict['rig']
            
            self._rig.set_data(rig_dict)

class FkItem(RigItem):
    
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
        
        self._rig.joints = joints
    """ 

class IkItem(RigItem):
    
    item_type = ItemType.IKRIG
    item_name = 'IkRig'
    
    def _init_rig_class_instance(self):
        return rigs.Ik()

#--- registry

register_item = {
    NodeItem.item_type : NodeItem,
    FkItem.item_type : FkItem,
    IkItem.item_type : IkItem,
    JointsItem.item_type : JointsItem,
    ColorItem.item_type : ColorItem,
    CurveShapeItem.item_type : CurveShapeItem
}