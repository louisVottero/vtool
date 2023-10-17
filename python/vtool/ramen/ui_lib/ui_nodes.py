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
from ... import util_math

from ...process_manager import process

in_maya = util.in_maya
if in_maya:
    import maya.cmds as cmds

in_unreal = util.in_unreal
#if util.in_unreal:
from vtool import unreal_lib
from .. import rigs
from .. import rigs_crossplatform
from .. import rigs_maya

uuids = {}

def update_socket_value(socket, update_rig = False, eval_targets = False):
    source_node = socket.parentItem()
    uuid = source_node.uuid
    util.show('\tUpdate socket value %s.%s' % (source_node.name, socket.name))
    has_lines = False
    if hasattr(socket, 'lines'):
        if socket.lines:
            has_lines = True

    if has_lines:
        if socket.lines[0].target == socket:
            socket = socket.lines[0].source
            log.info('update source as socket %s' % socket.name)

    value = socket.value

    if update_rig:
        source_node.rig.set_attr(socket.name, value)
        if socket.name in source_node._widgets:
            widget = source_node._widgets
            widget.value = value


    socket.dirty = False

    outputs = source_node.get_outputs(socket.name)

    target_nodes = []

    for output in outputs:

        target_node = output.parentItem()
        if not target_node in target_nodes:
            target_nodes.append(target_node)

        util.show('\tUpdate target node %s.%s: %s\t%s' % (target_node.name, output.name, value, target_node.uuid))
        run = False

        if in_unreal:

            if socket.name == 'controls' and output.name == 'parent':

                if target_node.rig.rig_util.construct_node is None:
                    target_node.rig.rig_util.load()
                    target_node.rig.rig_util.build()

                if source_node.rig.rig_util.construct_node is None:
                    source_node.rig.rig_util.load()
                    source_node.rig.rig_util.build()

                if source_node.rig.rig_util.construct_controller:
                    source_node.rig.rig_util.construct_controller.add_link('%s.controls' % source_node.rig.rig_util.construct_node.get_node_path(),
                                                                       '%s.parent' % target_node.rig.rig_util.construct_node.get_node_path())

        target_node.set_socket(output.name, value, run)

    if eval_targets:
        for target_node in target_nodes:

            util.show('\tRun target %s' % target_node.uuid)
            target_node.dirty = True
            #if in_unreal:
            #    target_node.rig.dirty = True

            target_node.run()

def connect_socket(source_socket, target_socket, run_target = True):




    source_node = source_socket.parentItem()
    target_node = target_socket.parentItem()


    current_inputs = target_node.get_inputs(target_socket.name)

    if current_inputs:
        disconnect_socket(target_socket, run_target=False)
        target_socket.remove_line(target_socket.lines[0])

    util.show('Connect socket %s.%s into %s.%s' % (source_node.name, source_socket.name, target_node.name, target_socket.name))

    value = source_socket.value
    util.show('connect source value %s %s' % (source_socket.name, value))


    if source_node.dirty:
        source_node.run()

    if in_unreal:

        if source_socket.name == 'controls' and target_socket.name == 'parent':

            if target_node.rig.rig_util.construct_node is None:
                target_node.rig.rig_util.load()
                target_node.rig.rig_util.build()
            if source_node.rig.rig_util.construct_controller:
                source_node.rig.rig_util.construct_controller.add_link('%s.controls' % source_node.rig.rig_util.construct_node.get_node_path(),
                                                                       '%s.parent' % target_node.rig.rig_util.construct_node.get_node_path())
                run_target = False

    target_node.set_socket(target_socket.name, value, run = run_target)



def disconnect_socket(target_socket, run_target = True):
    node = target_socket.parentItem()
    util.show('Disconnect socket %s.%s %s' % (node.name, target_socket.name, node.uuid))

    node = target_socket.parentItem()

    current_input = node.get_inputs(target_socket.name)

    if not current_input:
        return

    source_socket = current_input[0]

    log.info('Remove socket value: %s %s' % (target_socket.name, node.name))

    if target_socket.name == 'joints' and not target_socket.value:
        out_nodes = node.get_output_connected_nodes()

        for out_node in out_nodes:
            if hasattr(out_node, 'rig'):
                out_node.rig.parent = []

    if target_socket.name == 'parent':

        if in_unreal:

            source_node = source_socket.parentItem()
            target_node = target_socket.parentItem()

            if source_socket.name == 'controls' and target_socket.name == 'parent':

                if target_node.rig.rig_util.construct_node is None:
                    target_node.rig.rig_util.load()
                    target_node.rig.rig_util.build()
                if source_node.rig.rig_util.construct_controller:

                    source_node.rig.rig_util.construct_controller.break_link('%s.controls' % source_node.rig.rig_util.construct_node.get_node_path(),
                                                                           '%s.parent' % target_node.rig.rig_util.construct_node.get_node_path())
                    run_target = False


    node.set_socket(target_socket.name, None, run = run_target)


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



        connect_socket(source_socket, target_socket)

        #exec_string = 'node_item._rig.%s = %s' % (socket_item.name, socket_item.value)
        #exec(exec_string, {'node_item':node_item})

    def _node_disconnected(self, source_socket, target_socket):
        disconnect_socket(target_socket)

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
        self._zoom_min = 0.1
        self._zoom_max = 3.0

        self._cancel_context_popup = False
        self.drag = False
        self.right_click = False
        self.drag_accum = 0

        self.setRenderHints(qt.QPainter.Antialiasing | qt.QPainter.HighQualityAntialiasing)

        brush = qt.QBrush()
        brush.setColor(qt.QColor(15,15,15,1))
        self.setBackgroundBrush(brush)

        self.setFocusPolicy(qt.QtCore.Qt.StrongFocus)

        #self.setRenderHints(qt.QPainter.Antialiasing | qt.QPainter.SmoothPixmapTransform | qt.QPainter.HighQualityAntialiasing)

        #self.main_scene.addItem(NodeSocket())

    def drawBackground(self, painter, rect):

        size = 40

        pixmap = qt.QPixmap(size, size)
        pixmap.fill(qt.QtCore.Qt.transparent)

        pix_painter = qt.QPainter(pixmap)
        pix_painter.setBrush(qt.QColor.fromRgbF(.15, .15, .15, 1))

        pen = qt.QPen()
        pen.setStyle(qt.Qt.NoPen)
        pix_painter.setPen(pen)
        pix_painter.drawRect(0,0,size,size)

        pen = qt.QPen()
        pen.setColor(qt.QColor.fromRgbF(0, 0, 0, .6))
        pen.setStyle(qt.Qt.SolidLine)

        middle = size*.5

        if self._zoom >= 2.5:
            pen.setWidth(1.5)
            pix_painter.setPen(pen)


            offset = 2

            pix_painter.drawLine(middle-offset,middle,middle+offset,middle)
            pix_painter.drawLine(middle,middle-offset,middle,middle+offset)
            #pix_painter.drawLine(38,0,40,0)
            #pix_painter.drawLine(0,38,0,40)

        if self._zoom >= .75 and self._zoom < 2.5:

            pen.setWidth(3)
            pix_painter.setPen(pen)
            pix_painter.drawPoint(qt.QtCore.QPointF(middle,middle))


        pix_painter.end()

        painter.fillRect(rect, pixmap)

    def _define_main_scene(self):
        self.main_scene = NodeScene()

        self.main_scene.setObjectName('main_scene')
        self.main_scene.setSceneRect(-5000,-5000,5000,5000)

        self.setScene(self.main_scene)

        self.setResizeAnchor(self.AnchorViewCenter)


    def keyPressEvent(self, event):

        items = self.main_scene.selectedItems()
        """
        if event.key() == qt.Qt.Key_F:


            position = items[0].pos()
            #position = self.mapToScene(items[0].pos())
            self.centerOn(position)
        """
        if event.key() == qt.Qt.Key_Delete:
            for item in items:
                item.delete()

        super(NodeView, self).keyPressEvent(event)

    def wheelEvent(self, event):
        """
        Zooms the QGraphicsView in/out.

        """

        mouse_pos = event.pos()

        item = self.itemAt(mouse_pos)
        item_string = str(item)

        if item_string.find('widget=QComboBoxPrivateContainer') > -1:
            super(NodeView, self).wheelEvent(event)
            return

        else:
            inFactor = .85
            outFactor = 1.0 / inFactor
            mouse_pos = event.pos() * 1.0
            oldPos = self.mapToScene(mouse_pos)
            if event.delta() < 0:
                zoomFactor = inFactor
            if event.delta() > 0:
                zoomFactor = outFactor
            if event.delta() == 0:
                return

            self._zoom *= zoomFactor

            if self._zoom <= self._zoom_min:
                self._zoom = self._zoom_min

            if self._zoom >= self._zoom_max:
                self._zoom = self._zoom_max

            self.setTransform(qt.QTransform().scale(self._zoom, self._zoom))

            newPos = self.mapToScene(event.pos())
            delta = newPos - oldPos
            self.translate(delta.x(), delta.y())

    def mousePressEvent(self, event):
        if event.button() == qt.QtCore.Qt.MiddleButton or event.button() == qt.QtCore.Qt.RightButton:
            self.setDragMode(qt.QGraphicsView.NoDrag)
            self.drag = True
            self.prev_position = event.pos()

        if event.button() == qt.QtCore.Qt.RightButton:
            self.right_click = True

        elif event.button() == qt.QtCore.Qt.LeftButton:
            self.setDragMode(qt.QGraphicsView.RubberBandDrag)

            super(NodeView, self).mousePressEvent(event)


    def mouseMoveEvent(self, event):
        super(NodeView, self).mouseMoveEvent(event)
        if self.drag:
            self.setCursor(qt.QtCore.Qt.SizeAllCursor)
            offset = self.prev_position - event.pos()

            distance = util_math.get_distance_2D([self.prev_position.x(), self.prev_position.y()], [event.pos().x(), event.pos().y()])
            self.drag_accum += distance
            self.prev_position = event.pos()



            self.verticalScrollBar().setValue(self.verticalScrollBar().value() + offset.y())
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + offset.x())

            return



    def mouseReleaseEvent(self, event):

        if self.drag:
            self.drag = False

            self.setCursor(qt.QtCore.Qt.ArrowCursor)
            self.setDragMode(qt.QGraphicsView.RubberBandDrag)

        super(NodeView, self).mouseReleaseEvent(event)

        if self.right_click:


            if abs(self.drag_accum) > 30:
                self._cancel_context_popup = True
            #    self._build_context_menu(event)

            self.right_click = False
            self.drag_accum = 0

    def contextMenuEvent(self, event):
        super(NodeView, self).contextMenuEvent(event)

        if self._cancel_context_popup:
            self._cancel_context_popup = False
            return

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

        #item_inst.setZValue(self._z_value)
        #self._z_value -= 1

        uuids[uuid_value] = item_inst

        item_inst.load(item_dict)

        if item_inst:
            self.main_scene.addItem(item_inst)
            item_inst.setZValue(item_inst._z_value)

    def _build_line(self, item_dict):
        line_inst = NodeLine()
        line_inst.load(item_dict)
        self.main_scene.addItem(line_inst)

    def add_rig_item(self, node_type, position):

        if node_type in register_item:

            item_inst = register_item[node_type]()

            self.main_scene.addItem(item_inst)
            item_inst.setPos(position)
            item_inst.setZValue(item_inst._z_value)

class NodeViewDirectory(NodeView):
    def set_directory(self, directory):

        self._cache = None
        self.directory = directory

        self.main_scene.clear()
        self.open()


    def get_file(self):

        if not hasattr(self, 'directory'):
            return

        if not util_file.exists(self.directory):
            util_file.create_dir(self.directory)

        path = os.path.join(self.directory, 'ramen.json')

        return path

    def save(self):
        result = super(NodeViewDirectory, self).save()

        filepath = self.get_file()

        util_file.set_json(filepath, self._cache, append = False)

        util.show('Saved Ramen to: %s' % filepath)

        return filepath

    def open(self):
        self.main_scene.clear()
        filepath = self.get_file()
        if filepath and util_file.exists(filepath):
            self._cache = util_file.get_json(filepath)
        util.show('Loading %s' % filepath)
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

        if not event.buttons() == qt.QtCore.Qt.LeftButton:
            return

        for item in self.selection:

            sockets = item.get_all_sockets()

            visited = {}

            for socket_name in sockets:
                socket = sockets[socket_name]
                if socket_name in visited:
                    continue
                if hasattr(socket, 'lines'):
                    for line in socket.lines:
                        if line.source and line.target:
                            line.pointA = line.source.get_center()
                            line.pointB = line.target.get_center()

                visited[socket_name] = None

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

    def _set_name(self, name):
        self._name = name

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
        self._set_name(name)

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
        self._z_value = 3000
        super(ProxyItem, self).__init__(parent)
        BaseAttributeItem.__init__(self)

        self.widget = self._widget()

        if self.widget:
            self.setWidget(self.widget)

        self.setPos(10,10)

    def _convert_to_nicename(self, name):

        name = name.replace('_', ' ')
        name = name.title()

        return name

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

        widget.setMaximumWidth(160)
        widget.setMaximumHeight(20)
        return widget

    def _get_value(self):
        return str(self.widget.text())

    def _set_value(self, value):
        super(LineEditItem, self)._set_value(value)

        if type(value) == list and len(value) == 1:
            value = value[0]

        if value:
            self.widget.setText(value)
        if not value:
            self.widget.setText('')

    def _set_name(self, name):
        super(ProxyItem, self)._set_name(name)
        self.widget.setPlaceholderText(self._convert_to_nicename(name))

class BoolItem(ProxyItem):

    def _widget(self):
        widget = qt.QCheckBox()

        font = qt.QFont()
        font.setPixelSize(10)

        widget.setFont(font)

        style = qt_ui.get_style()
        widget.setStyleSheet(style)
        #widget.setMinimumWidth(125)
        #widget.setMaximumWidth(130)
        #widget.setMaximumHeight(20)
        return widget

    def _get_value(self):


        return self.widget.isChecked()

    def _set_value(self, value):
        super(BoolItem, self)._set_value(value)
        if value:
            self.widget.setCheckState(qt.QtCore.Qt.Checked)
        else:
            self.widget.setCheckState(qt.QtCore.Qt.Unchecked)

    def _set_name(self, name):
        super(BoolItem, self)._set_name(name)

        name = self._convert_to_nicename(name)
        self.widget.setText(name)

class IntItem(ProxyItem):
    def _widget(self):
        widget = qt_ui.GetInteger()
        widget.setMaximumHeight(18)

        style = qt_ui.get_style()
        widget.setStyleSheet(style)

        widget.set_label_to_right()

        return widget

    def _get_value(self):
        return self.widget.get_value()

    def _set_value(self, value):
        super(IntItem, self)._set_value(value)
        if type(value) == list:
            value = value[0]
        self.widget.set_value(value)

    def _set_name(self, name):
        super(IntItem, self)._set_name(name)

        #self.widget.main_layout.takeAt(1)
        self.widget.set_value_label('   ' + self._convert_to_nicename(name))

class NumberItem(IntItem):

    def _widget(self):
        widget = qt_ui.GetNumber()
        widget.setMaximumHeight(18)
        style = qt_ui.get_style()
        widget.setStyleSheet(style)
        widget.set_label_to_right()
        return widget

class VectorItem(IntItem):

    def _widget(self):
        widget = qt_ui.GetVector(alignment = qt.QtCore.Qt.AlignAbsolute)
        widget.setMaximumHeight(18)
        style = qt_ui.get_style()
        widget.setStyleSheet(style)
        widget.set_label_to_right()
        return widget

    def _set_name(self, name):
        super(IntItem, self)._set_name(name)

        #self.widget.main_layout.takeAt(1)
        self.widget.set_value_label(' ' + self._convert_to_nicename(name))

    def _set_value(self, value):
        super(ProxyItem, self)._set_value(value)
        if len(value) == 1 and type(value) == list:
            value = value[0]
        self.widget.set_value(value)

class NodeComboBox(qt.QComboBox):

    show_pop = qt.create_signal()
    hide_pop = qt.create_signal()

    def showPopup(self):
        super(NodeComboBox, self).showPopup()
        self.show_pop.emit()

    def hidePopup(self):
        super(NodeComboBox, self).hidePopup()
        self.hide_pop.emit()


class ComboBoxItem(ProxyItem):

    def _widget(self):
        self._z_value = 10000

        widget = NodeComboBox()
        widget.setMinimumWidth(125)
        #widget.setMaximumWidth(130)
        widget.setMaximumHeight(20)

        style = qt_ui.get_style()
        widget.setStyleSheet(style)

        widget.show_pop.connect(self._set_to_front)
        widget.hide_pop.connect(self._set_to_default)

        self.setZValue(self._z_value)

        return widget

    def _set_to_front(self):
        self.parentItem().setZValue(5000)

    def _set_to_default(self):
        self.parentItem().setZValue(self.parentItem()._z_value)

    def _get_value(self):
        return self.widget.currentIndex()

    def _set_value(self, value):
        super(ComboBoxItem, self)._set_value(value)
        self.widget.setCurrentIndex(value)

    def _highlight(self):
        parent = self.widget.parent()
        while parent:
            if isinstance(parent, qt.QGraphicsView):

                break
            parent = parent.parent()

class ColorPickerItem(qt.QGraphicsObject, BaseAttributeItem):

    item_type = ItemType.WIDGET
    color_changed = qt_ui.create_signal(object)

    def __init__(self, width = 40, height = 14):
        super(ColorPickerItem, self).__init__()
        BaseAttributeItem.__init__(self)

        self._name = 'color'

        self.rect = qt.QtCore.QRect(10,15,width,height)
        #self.rect = qt.QtCore.QRect(10,10,50,20)


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

        painter.drawRoundedRect(self.rect, 5,5)

        #painter.drawRect(self.rect)

    def mousePressEvent(self, event):

        super(ColorPickerItem, self).mousePressEvent(event)

        color_dialog = qt.QColorDialog
        color = color_dialog.getColor()

        if not color.isValid():
            return

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

        if type(value) == list and len(value) == 1:
            value = value[0]

        color = qt.QColor()
        color.setRgbF(value[0],value[1],value[2], 1.0)
        self.brush.setColor(color)

class TitleItem(qt.QGraphicsObject, BaseAttributeItem):

    item_type = ItemType.WIDGET

    def __init__(self):
        super(TitleItem, self).__init__()
        BaseAttributeItem.__init__(self)

        self.rect = qt.QtCore.QRect(0,0,150,20)
        #self.rect = qt.QtCore.QRect(10,10,50,20)

        self.font = qt.QFont()
        self.font.setPixelSize(10)
        self.font.setBold(True)

        self.font_metrics = qt.QFontMetrics(self.font)

        # Brush.
        self.brush = qt.QBrush()
        self.brush.setStyle(qt.QtCore.Qt.SolidPattern)
        self.brush.setColor(qt.QColor(60,60,60,255))

        # Pen.
        self.pen = qt.QPen()
        self.pen.setStyle(qt.QtCore.Qt.DotLine)
        self.pen.setWidth(.5)
        self.pen.setColor(qt.QColor(200,200,200,255))

    def paint(self, painter, option, widget):
        painter.setBrush(self.brush)
        painter.setFont(self.font)
        painter.setPen(self.pen)

        bounding_rect = self.font_metrics.boundingRect(self.name)

        painter.drawText(6,13, self.name)

        parent_item = self.parentItem()
        rect = parent_item.boundingRect()
        painter.drawLine(bounding_rect.width()+15, 10, rect.width()-20, 10)


    def boundingRect(self):
        return qt.QtCore.QRectF(self.rect)

#--- socket

class NodeSocket(qt.QGraphicsItem, BaseAttributeItem):

    item_type = ItemType.SOCKET

    def __init__(self, socket_type = SocketType.IN, name = None, value = None, data_type = None):
        super(NodeSocket, self).__init__()
        BaseAttributeItem.__init__(self)

        self.dirty = True

        self._name = name
        self._value = value
        self._data_type = data_type

        self.socket_type = socket_type

        if self._name:
            split_name = self._name.split('_')
            if split_name:
                found = []
                for name in split_name:
                    name = name.title()
                    found.append(name)
                self.nice_name = ' '.join(found)
            else:
                self.nice_name = self._name.title()
        else:
            self.nice_name = None

        self.init_socket(socket_type, data_type)

        self.font = qt.QFont()
        self.font.setPixelSize(10)



    def init_socket(self, socket_type, data_type):
        self.node_width = 150

        self.rect = qt.QtCore.QRectF(0.0,0.0,0.0,0.0)

        self.side_socket_height = 0

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
        if data_type == rigs.AttrType.VECTOR:
            self.color = qt.QColor(170,70,160,255)
        self.brush.setColor(self.color)

        if socket_type == SocketType.IN:

            self.rect = qt.QtCore.QRect(-10.0, self.side_socket_height, 20.0,20.0)

            #self.setFlag(self.ItemStacksBehindParent)

        if socket_type == SocketType.OUT:
            node_width = 150
            parent = self.parentItem()
            if parent:
                node_width = self.parentItem().node_width
            self.rect = qt.QtCore.QRect(node_width + 23, 5, 20.0,20.0)

        if socket_type == SocketType.TOP:
            self.rect = qt.QtCore.QRect(10.0, -10.0, 15.0,15.0)

        self.lines = []



    def boundingRect(self):
        return qt.QtCore.QRectF(self.rect)

    def paint(self, painter, option, widget):
        painter.setBrush(self.brush)
        painter.setPen(self.pen)
        self.pen.setStyle(qt.QtCore.Qt.NoPen)
        self.pen.setWidth(0)
        painter.setPen(self.pen)


        painter.setFont(self.font)

        if self.socket_type == SocketType.IN:

            rect = qt.QtCore.QRectF(self.rect)
            rect.adjust(3.0,3.0,-3.0,-3.0)
            painter.drawEllipse(rect)

            self.pen.setStyle(qt.QtCore.Qt.SolidLine)
            self.pen.setWidth(1)
            painter.setPen(self.pen)

            if self._data_type == rigs.AttrType.STRING:
                pass
            elif self._data_type == rigs.AttrType.VECTOR:
                pass
            elif self._data_type == rigs.AttrType.COLOR:
                painter.drawText(qt.QtCore.QPoint(55,self.side_socket_height+14),self.nice_name)
            else:
                painter.drawText(qt.QtCore.QPoint(15,self.side_socket_height+14),self.nice_name)

        if self.socket_type == SocketType.OUT:

            parent = self.parentItem()
            if parent:
                self.node_width = self.parentItem().node_width

            self.rect.setX(self.node_width)

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
            offset = self.node_width - 10 - name_len

            painter.drawText(qt.QtCore.QPoint(offset,self.side_socket_height+17),self.nice_name)

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

        connection_fail = False

        if item:

            if item.parentItem() == self.parentItem():
                connection_fail = 'Same node'

            if self.data_type != item.data_type:

                if self.socket_type == SocketType.IN and not self.data_type == rigs.AttrType.ANY:
                    connection_fail = 'Different Type'

                if item.socket_type == SocketType.IN and not item.data_type == rigs.AttrType.ANY:
                    connection_fail = 'Different Type'

        if connection_fail:
            self.remove_line(self.new_line)
            self.new_line = None
            util.warning('Cannot connect sockets: %s' % connection_fail)
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
            self.scene().node_connect.emit(self.new_line)
            item.lines.append(self.new_line)


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
            center = qt.QtCore.QPointF(self.node_width+14, rect.y() + rect.height()/2.0)
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
        self.setZValue(0)

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

        self._target.scene().node_disconnect.emit(self.source, self.target)

        self._source.remove_line(self)
        self._target.remove_line(self)



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

        painter.drawEllipse(self.pointB.x() - 3.0,self.pointB.y() - 3.0 ,6.0,6.0)

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
        self.node_width = self._init_node_width()

        super(GraphicsItem, self).__init__(parent)


        self._z_value = 2000


        self.draw_node()

        self.setFlag(self.ItemIsFocusable)

    def _init_node_width(self):
        return 150

    def _init_color(self):
        return [68,68,68,255]

    def draw_node(self):

        self._left_over_space = 0
        self._current_socket_pos = 0

        self.rect = qt.QtCore.QRect(0,0,self.node_width,40)
        self.setFlag(qt.QGraphicsItem.ItemIsMovable)
        self.setFlag(qt.QGraphicsItem.ItemIsSelectable)


        # Brush.
        self.brush = qt.QBrush()
        self.brush.setStyle(qt.QtCore.Qt.SolidPattern)

        self.brush.setColor(qt.QColor(*self._init_color()))

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

        #self.setZValue(1000)
        #painter.drawRect(self.rect)

    def contextMenuEvent(self, event):
        self._build_context_menu(event)
        event.setAccepted(True)

    def _build_context_menu(self, event):

        menu = qt.QMenu()

        add_in_socket = menu.addAction('add in socket')
        add_out_socket = menu.addAction('add out socket')
        add_top_socket = menu.addAction('add top socket')
        add_string = menu.addAction('add string')
        add_combo = menu.addAction('add combo')
        add_color = menu.addAction('add color')

        selected_action = menu.exec_(event.screenPos())

        if selected_action == add_string:
            self.add_string()

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

        #if item.item_type == ItemType.PROXY:
        #    offset_y_value += 4


        y_value = self._current_socket_pos + offset + offset_y_value

        self.rect = qt.QtCore.QRect(0,0,self.node_width,y_value + 35)
        item.setY(y_value)

        y_value += 18

        self._current_socket_pos = y_value
        self._left_over_space = offset

        item.setZValue(self._z_value)
        self._z_value -= 1

class NodeItem(GraphicsItem):

    item_type = ItemType.NODE
    item_name = 'Node'


    def __init__(self, name = '', uuid_value = None):
        self._dirty = None

        self._color = self._init_color()

        super(NodeItem, self).__init__()

        self.rig = self._init_rig_class_instance()
        self._init_uuid(uuid_value)
        self._dirty = True
        self._signal_eval_targets = False

        if not name:
            self.name = self.item_name
        else:
            self.name = name

        self._widgets = []
        self._in_sockets = {}
        self._in_socket_widgets = {}
        self._out_sockets = {}
        self._sockets = {}
        self._dependency = {}
        self._build_items()

    def __getattribute__(self, item):
        dirty = object.__getattribute__(self,'_dirty')

        if item == 'run' and not dirty:
            return lambda *args: None

        return object.__getattribute__(self,item)

    def _init_uuid(self, uuid_value):
        if not uuid_value:
            self.uuid = str(uuid.uuid4())
        else:
            self.uuid = uuid_value

        uuids[self.uuid] = self

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

    def _dirty_run(self, attr_name = None):

        self.dirty = True
        if hasattr(self, 'rig'):
            self.rig.dirty = True
        for out_name in self._out_sockets:
            out_sockets = self.get_outputs(out_name)
            for out_socket in out_sockets:
                out_node = out_socket.parentItem()
                out_node.dirty = True
                out_node.rig.dirty = True

        self._signal_eval_targets = True
        self.run(attr_name)
        self._signal_eval_targets = False

    def _in_widget_run(self, attr_value, attr_name):

        self.set_socket(attr_name, attr_value)

        self._dirty_run(attr_name)

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

    def run_inputs(self):

        util.show('Prep: %s' % self.__class__.__name__, self.uuid)

        sockets = {}
        sockets.update(self._in_sockets)
        sockets.update(self._sockets)

        if sockets:


            for socket_name in sockets:

                input_sockets = self.get_inputs(socket_name)

                for input_socket in input_sockets:
                    if not input_socket:
                        continue
                    input_node = input_socket.parentItem()

                    if input_node.dirty:
                        input_node.run()
                    value = input_socket.value

                    current_socket = self.get_socket(socket_name)

                    current_socket.value = value

                    if hasattr(self, 'rig'):
                        self.rig.attr.set(socket_name, value)



    @property
    def dirty(self):
        return self._dirty

    @dirty.setter
    def dirty(self, bool_value):

        util.show('\tDIRTY: %s %s' % (bool_value, self.uuid))
        #util.show('\tRIG DIRTY: %s %s' % (self.rig.dirty, self.uuid))
        self._dirty = bool_value

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

        current_space = self._current_socket_pos

        widget = None

        if data_type == rigs.AttrType.STRING:
            self._current_socket_pos -= 18
            widget = self.add_string(name)
            #socket.value = value
            return_function = lambda attr_value, attr_name = name: self._in_widget_run(attr_value, attr_name)
            widget.widget.returnPressed.connect( return_function )

        if data_type == rigs.AttrType.COLOR:
            self._current_socket_pos -= 30
            widget = self.add_color_picker(name)
            #socket.value = widget.value
            return_function = lambda attr_value, attr_name = name : self._in_widget_run(attr_value, attr_name)
            widget.color_changed.connect( return_function )

        if data_type == rigs.AttrType.VECTOR:
            self._current_socket_pos -= 17
            widget = self.add_vector(name)
            #socket.value = value
            return_function = lambda attr_value, attr_name = name : self._in_widget_run(attr_value, attr_name)
            widget.widget.valueChanged.connect( return_function )

        if widget:
            widget.value = value
            self._in_socket_widgets[name] = widget

        self._current_socket_pos = current_space

        if not self.rig.attr.exists(name):
            self._current_socket_pos -= 6
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

    def add_bool(self, name):

        widget = BoolItem()
        widget.name = name
        widget.setParentItem(self)

        self._add_space(widget,2)
        self._widgets.append(widget)

        if not self.rig.attr.exists(name):
            self.rig.attr.add_to_node(name, widget.value, widget.data_type)

        self._sockets[name] = widget

        return widget

    def add_int(self, name):
        widget = IntItem()
        widget.name = name
        widget.setParentItem(self)
        self._add_space(widget, 4)
        self._widgets.append(widget)
        self._sockets[name] = widget
        return widget

    def add_number(self, name):
        widget = NumberItem(self)
        widget.name = name

        self._add_space(widget)
        self._widgets.append(widget)
        self._sockets[name] = widget
        return widget

    def add_vector(self, name):
        widget = VectorItem(self)
        widget.name = name
        self._add_space(widget)
        self._widgets.append(widget)
        self._sockets[name] = widget
        return widget

    def add_color_picker(self, name, width = 40, height = 14):

        color_picker = ColorPickerItem(width, height)
        color_picker.name = name
        color_picker.setParentItem(self)
        self._add_space(color_picker)

        self._widgets.append(color_picker)

        self._sockets[name] = color_picker

        return color_picker

    def add_string(self, name):

        rect = self.boundingRect()
        width = rect.width()

        line_edit = LineEditItem(self)
        line_edit.name = name
        line_edit.setMaximumWidth(width - 20)
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

        if not self.rig.attr.exists(name):
            self.rig.attr.add_to_node(name, combo.value, combo.data_type)

        self._widgets.append(combo)

        self._sockets[name] = combo

        return combo

    def add_title(self, name):
        title = TitleItem()
        title.name = name
        title.setParentItem(self)


        self._add_space(title,3)

        #title.setZValue(title.zValue() + 1)

        #self._widgets.append(title)

        #self._sockets[name] = title

        return title

    def delete(self):

        if not self.scene():
            return

        self._disconnect_lines()

        self.scene().removeItem(self)

    def get_widget(self, name):

        for widget in self._widgets:
            if widget.name == name:
                return widget

    def set_socket(self, name, value, run = False):
        util.show('\tSet socket %s %s, run: %s' % (name, value, run))
        socket = self.get_socket(name)

        if not socket:
            return

        socket.value = value

        if name in self._in_socket_widgets:
            widget = self._in_socket_widgets[name]

            widget.value = value

        if run:
            self.dirty = True
            self.rig.dirty = True
            self.run()

        """
        dependency_sockets = None

        if name in self._dependency:
            dependency_sockets = self._dependency[name]

        if not dependency_sockets:
            return

        for socket_name in dependency_sockets:
            dep_socket = self.get_socket(socket_name)
            value = self.rig.get_attr(socket_name)
            dep_socket.value = value
        """

        """
        for name in self._out_sockets:
            out_socket = self._out_sockets[name]

            outputs = self.get_outputs(out_socket.name)
            for output in outputs:
                node = output.parentItem()
                node.run(output.name)
        """
    def get_socket(self, name):
        sockets = self.get_all_sockets()

        if name in sockets:
            socket = sockets[name]
            return socket

    def get_all_sockets(self):
        sockets = {}
        sockets.update(self._sockets)
        sockets.update(self._in_sockets)
        sockets.update(self._out_sockets)

        return sockets

    def get_socket_value(self, name):
        socket = self.get_socket(name)
        return socket.value

    def get_inputs(self, name):
        found = []

        for socket in self._in_sockets:

            socket_inst = self._in_sockets[socket]

            if socket == name:
                for line in socket_inst.lines:
                    found.append(line.source)


        return found

    def get_outputs(self, name):

        found = []

        for out_name in self._out_sockets:
            socket = self._out_sockets[out_name]

            if socket.name == name:

                for line in socket.lines:
                    found.append(line.target)

        return found

    def get_output_connected_nodes(self):
        found = []
        for name in self._out_sockets:
            socket = self._out_sockets[name]
            for line in socket.lines:
                found.append(line.target.parentItem())

        return found

    def run(self, socket = None):

        self.run_inputs()

        if not socket:
            util.show('Running: %s' % self.__class__.__name__, self.uuid)
        if socket:
            util.show('Running: %s.%s' % (self.__class__.__name__, socket), self.uuid)



        self.dirty = False

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
        util.show('\tuuid: %s' % self.uuid)
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

        picker = self.add_color_picker('color value', 50, 30)
        picker.data_type = rigs.AttrType.COLOR
        self.picker = picker

        picker.color_changed.connect(self._color_changed)

        self.add_out_socket('color', None, rigs.AttrType.COLOR)

    def _color_changed(self, color):

        self.color = color

        self._dirty_run()

    def run(self, socket = None):
        super(ColorItem, self).run(socket)

        socket = self.get_socket('color')
        if hasattr(self, 'color') and self.color:

            socket.value = [self.color]
        else:
            socket.value = [self.picker.value]

        update_socket_value(socket, eval_targets = self._signal_eval_targets)

class CurveShapeItem(NodeItem):

    item_type = ItemType.CURVE_SHAPE
    item_name = 'Curve Shape'

    def _build_items(self):
        self._current_socket_pos = 10
        shapes = rigs_maya.Control.get_shapes()

        shapes.insert(0, 'Default')
        self.add_title('Maya')
        maya_combo = self.add_combo_box('Maya')
        maya_combo.data_type = rigs.AttrType.STRING
        maya_combo.widget.addItems(shapes)

        self._maya_curve_entry_widget = maya_combo

        maya_combo.widget.currentIndexChanged.connect(self._dirty_run)


        unreal_items = unreal_lib.util.get_unreal_control_shapes()

        self.add_title('Unreal')
        unreal_combo = self.add_combo_box('Unreal')
        unreal_combo.data_type = rigs.AttrType.STRING
        unreal_combo.widget.addItems(unreal_items)
        unreal_combo.widget.setCurrentIndex(1)

        self._unreal_curve_entry_widget = unreal_combo
        unreal_combo.widget.currentIndexChanged.connect(self._dirty_run)

        self.add_out_socket('curve_shape', [], rigs.AttrType.STRING)

    def run(self, socket = None):
        super(CurveShapeItem, self).run(socket)

        curve = None

        if in_maya:
            curve = self._maya_curve_entry_widget.widget.currentText()
        if in_unreal:
            curve = self._unreal_curve_entry_widget.widget.currentText()

        if curve:
            socket = self.get_socket('curve_shape')
            socket.value = curve

            update_socket_value(socket, eval_targets = self._signal_eval_targets)



class JointsItem(NodeItem):

    item_type = ItemType.JOINTS
    item_name = 'Joints'

    def _build_items(self):

        #self.add_in_socket('Scope', [], rigs.AttrType.TRANSFORM)
        self._current_socket_pos = 10
        line_edit = self.add_string('joint filter')
        line_edit.widget.setPlaceholderText('Joint Search')
        line_edit.data_type = rigs.AttrType.STRING
        self.add_out_socket('joints', [], rigs.AttrType.TRANSFORM)
        #self.add_socket(socket_type, data_type, name)

        self._joint_entry_widget = line_edit
        line_edit.widget.returnPressed.connect(self._dirty_run)

    def _get_joints(self):
        filter_text = self._joint_entry_widget.widget.text()

        joints = util_ramen.get_joints(filter_text)

        return joints


    def run(self, socket = None):
        super(JointsItem, self).run(socket)

        joints = self._get_joints()
        if joints is None:
            joints = []

        util.show('\tFound: %s' % joints)

        socket = self.get_socket('joints')
        socket.value = joints

        update_socket_value(socket, eval_targets = self._signal_eval_targets)

class ImportDataItem(NodeItem):

    item_type = ItemType.DATA
    item_name = 'Import Data'

    def _build_items(self):



        line_edit = self.add_string('data name')
        line_edit.widget.setPlaceholderText('Data Name')
        line_edit.data_type = rigs.AttrType.STRING
        self.add_in_socket('Eval IN', [], rigs.AttrType.EVALUATION)

        self.add_out_socket('result', [], rigs.AttrType.STRING)
        self.add_out_socket('Eval OUT', [], rigs.AttrType.EVALUATION)

        self.add_bool('New Scene')


        self._data_entry_widget = line_edit
        line_edit.widget.returnPressed.connect(self._dirty_run)

    def run(self, socket = None):
        super(ImportDataItem, self).run(socket)

        new_scene_widget = self._sockets['New Scene']
        if new_scene_widget.value:
            if in_maya:
                cmds.file(new = True, f = True)

        process_inst = process.get_current_process_instance()
        result = process_inst.import_data(self._data_entry_widget.value, sub_folder=None)

        if result is None:
            result = []

        socket = self.get_socket('result')
        socket.value = result

        update_socket_value(socket, eval_targets = self._signal_eval_targets)

        return result

class PrintItem(NodeItem):

    item_type = ItemType.PRINT
    item_name = 'Print'

    def _build_items(self):

        self.add_in_socket('input', [], rigs.AttrType.ANY)

    def run(self, socket = None):
        super(PrintItem, self).run(socket)

        socket = self.get_socket('input')
        util.show(socket.value)

class SetSkeletalMeshItem(NodeItem):
    item_type = ItemType.UNREAL_SKELETAL_MESH
    item_name = 'Set Skeletal Mesh'

    def _build_items(self):
        self.add_in_socket('input',[], rigs.AttrType.STRING)

    def run(self, socket = None):
        super(SetSkeletalMeshItem, self).run(socket)

        socket = self.get_socket('input')

        util.show('\t%s' % socket.value)

        for path in socket.value:
            if unreal_lib.util.is_skeletal_mesh(path):
                unreal_lib.util.set_skeletal_mesh(path)
                util.show('Current graph: %s' % unreal_lib.util.current_control_rig)
                break



class RigItem(NodeItem):

    item_type = ItemType.RIG

    def __init__(self, name = '', uuid_value = None):

        self._temp_parents = {}
        super(RigItem, self).__init__(name, uuid_value)

        self.rig.load()

        #self.run()

    def _init_node_width(self):
        return 180

    def _init_uuid(self, uuid_value):
        super(RigItem, self)._init_uuid(uuid_value)
        self.rig.uuid = self.uuid

    def _init_rig_class_instance(self):
        return rigs.Rig()

    def _build_items(self):

        self._current_socket_pos = 10

        if not self.rig:
            return

        attribute_names = self.rig.get_all_attributes()
        ins = self.rig.get_ins()
        outs = self.rig.get_outs()
        items = self.rig.get_node_attributes()


        self._dependency.update( self.rig.get_attr_dependency() )

        for attr_name in attribute_names:

            if attr_name in items:

                value, attr_type = self.rig.get_node_attribute(attr_name)

                if attr_type == rigs.AttrType.TITLE:
                    title = self.add_title(attr_name)

                    title.data_type = attr_type


                if attr_type == rigs.AttrType.STRING:
                    line_edit = self.add_string(attr_name)

                    line_edit.data_type = attr_type
                    line_edit.value = value

                    line_edit_return_function = lambda name = attr_name: self._dirty_run(name)
                    line_edit.widget.returnPressed.connect( line_edit_return_function )

                if attr_type == rigs.AttrType.BOOL:
                    bool_widget = self.add_bool(attr_name)
                    bool_widget.data_type = attr_type
                    bool_widget.value = value

                    bool_return_function = lambda value, name = attr_name: self._dirty_run(name)
                    bool_widget.widget.stateChanged.connect( bool_return_function )

                if attr_type == rigs.AttrType.INT:
                    int_widget = self.add_int(attr_name)
                    int_widget.data_type = attr_type
                    int_widget.value = value

                    return_function = lambda value, name = attr_name : self._dirty_run(name)
                    int_widget.widget.valueChanged.connect( return_function )

                if attr_type == rigs.AttrType.VECTOR:
                    widget = self.add_vector(attr_name)
                    widget.data_type = attr_type
                    widget.value = value

                    return_function = lambda value, name = attr_name : self._dirty_run(name)
                    widget.widget.valueChanged.connect( return_function )

            if attr_name in ins:
                value, attr_type = self.rig.get_in(attr_name)

                if attr_name == 'parent':
                    self.add_top_socket(attr_name, value, attr_type)
                else:
                    self.add_in_socket(attr_name, value, attr_type)

        for attr_name in attribute_names:
            if attr_name in outs:
                value, attr_type = self.rig.get_out(attr_name)

                self.add_out_socket(attr_name, value, attr_type)

    def _run(self, socket):
        sockets = self.get_all_sockets()

        if in_unreal:
            self.rig.rig_util.load()
            if self.rig.dirty == True:
                self.rig.rig_util.build()

        for name in sockets:
            node_socket = sockets[name]

            value = node_socket.value

            if name in self._out_sockets:
                if hasattr(self, 'rig_type'):
                    value = self.rig.attr.get(name)
                    node_socket.value = value

            self.rig.attr.set(node_socket.name, value)

        if isinstance(socket, str):
            socket = sockets[socket]

        if socket:
            self.dirty = True
            self.rig.dirty = True
            update_socket_value(socket, update_rig=True)
        else:

            self.rig.create()

            if not in_unreal:

                for name in self._out_sockets:
                    out_socket = self._out_sockets[name]

                    value = self.rig.attr.get(name)

                    out_socket.value = value

                    update_socket_value(out_socket)

    def _unparent(self):
        if in_unreal:
            return

        nodes = self.get_output_connected_nodes()
        for node in nodes:
            self._temp_parents[node.uuid] = node
            node.rig.parent = []

    def _reparent(self):
        if in_unreal:

            inputs = self.get_inputs('parent')

            for in_socket in inputs:
                if in_socket.name == 'controls':

                    in_node = in_socket.parentItem()

                    in_node.rig.rig_util.load()
                    self.rig.rig_util.load()

                    if in_node.rig.rig_util.construct_controller:
                        in_node_unreal = in_node.rig.rig_util.construct_node
                        node_unreal = self.rig.rig_util.construct_node

                        if in_node_unreal and node_unreal:
                            in_node.rig.rig_util.construct_controller.add_link('%s.controls' % in_node_unreal.get_node_path(),
                                                                               '%s.parent' % node_unreal.get_node_path())

        if not self._temp_parents:
            return

        controls = self.rig.get_attr('controls')
        if controls:
            for uuid in self._temp_parents:
                node = self._temp_parents[uuid]
                node.rig.parent = controls

    def run(self, socket = None):
        super(RigItem, self).run(socket)

        self._unparent()
        self._run(socket)
        self._reparent()

        if in_unreal:
            offset = -2300
            spacing = 1.25
            position = self.pos()
            self.rig.rig_util.set_node_position((position.x() - offset)*spacing, (position.y() - offset)*spacing)

    def delete(self):
        self._unparent()
        super(RigItem, self).delete()

        self.rig.delete()

    def store(self):
        item_dict = super(RigItem, self).store()

        item_dict['rig uuid'] = self.rig.uuid

        return item_dict

    def load(self, item_dict):
        super(RigItem, self).load(item_dict)

        self.rig.uuid = self.uuid

        if in_maya:
            value = self.rig.attr.get('controls')
            if value:

                self.dirty = False
                self.rig.dirty = False

                self.set_socket('controls', value, run = False)

class FkItem(RigItem):

    item_type = ItemType.FKRIG
    item_name = 'FkRig'

    def _init_color(self):
        return [68,68,88,255]

    def _init_rig_class_instance(self):
        return rigs_crossplatform.Fk()


class IkItem(RigItem):

    item_type = ItemType.IKRIG
    item_name = 'IkRig'

    def _init_color(self):
        return [68,88,68,255]

    def _init_rig_class_instance(self):
        return rigs_crossplatform.Ik()


#--- registry

register_item = {
    #NodeItem.item_type : NodeItem,
    FkItem.item_type : FkItem,
    IkItem.item_type : IkItem,
    JointsItem.item_type : JointsItem,
    ColorItem.item_type : ColorItem,
    CurveShapeItem.item_type : CurveShapeItem,
    ImportDataItem.item_type : ImportDataItem,
    PrintItem.item_type : PrintItem,
    SetSkeletalMeshItem.item_type : SetSkeletalMeshItem
}
