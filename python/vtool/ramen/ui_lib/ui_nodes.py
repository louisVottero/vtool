# Copyright (C) 2024 Louis Vottero louis.vot@gmail.com    All rights reserved.
from __future__ import print_function
from __future__ import absolute_import

import os
import uuid
import math

from .. import rigs_maya
from .. import rigs_crossplatform
from .. import rigs

from ...process_manager import process
from ... import util_math
from ... import util_file
from ... import util
from .. import util as util_ramen
from ... import qt_ui
from ... import qt
from ...util import StopWatch

from ... import logger

log = logger.get_logger(__name__)

in_maya = util.in_maya
if in_maya:
    import maya.cmds as cmds

in_unreal = util.in_unreal

from ... import unreal_lib

uuids = {}


class ItemType(object):
    SOCKET = 1
    WIDGET = 2
    PROXY = 3
    LINE = 4
    NODE = 10001
    JOINTS = 10002
    COLOR = 10003
    CURVE_SHAPE = 10004
    TRANSFORM_VECTOR = 10005
    PLATFORM_VECTOR = 10006
    CONTROLS = 10005
    RIG = 20002
    FKRIG = 20003
    IKRIG = 20004
    SPLINEIKRIG = 20005
    WHEELRIG = 20010
    GET_SUB_CONTROLS = 21000
    GET_TRANSFORM = 21001
    DATA = 30002
    PRINT = 30003
    UNREAL_SKELETAL_MESH = 30004


class SocketType(object):
    IN = 'in'
    OUT = 'out'
    TOP = 'top'


class NodeWindow(qt_ui.BasicGraphicsWindow):
    title = 'RAMEN'

    def __init__(self, parent=None):

        super(NodeWindow, self).__init__(parent)
        self.setWindowTitle('Ramen')

    def sizeHint(self):
        return qt.QtCore.QSize(800, 800)

    def _define_main_view(self):

        self.main_view_class = NodeViewDirectory()
        self.main_view = self.main_view_class.node_view

    def _build_widgets(self):

        self.side_menu = SideMenu()
        self.main_layout.addWidget(self.side_menu)

        self.side_menu.hide()

    def focusNextPrevChild(self, next):
        # this helps insure that focus doesn't drift when hitting tab
        return False


class NodeDirectoryWindow(NodeWindow):

    def __init__(self, parent=None):
        super(NodeDirectoryWindow, self).__init__(parent)
        self.directory = None

    def set_directory(self, directory):
        self.directory = directory
        self.main_view_class.set_directory(directory)


class NodeGraphicsView(qt_ui.BasicGraphicsView):

    def __init__(self, parent=None, base=None):
        super(NodeGraphicsView, self).__init__(parent)

        self.base = base

        self.prev_position = None
        self.prev_offset = 0
        self._cache = None
        self._zoom = 1
        self._zoom_min = 0.1
        self._zoom_max = 3.0

        self._cancel_context_popup = False
        self.drag = False
        self.alt_drag = False

        self.right_click = False
        self.drag_accum = 0
        self._build_context_menu_later = False

        if qt.is_pyside6():
            self.setRenderHints(qt.QPainter.Antialiasing)
        else:
            self.setRenderHints(qt.QPainter.Antialiasing |
                            qt.QPainter.HighQualityAntialiasing)

        brush = qt.QBrush()
        brush.setColor(qt.QColor(15, 15, 15, 1))
        self.setBackgroundBrush(brush)

        self.setFocusPolicy(qt.QtCore.Qt.StrongFocus)

        self.setHorizontalScrollBarPolicy(qt.QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(qt.QtCore.Qt.ScrollBarAlwaysOff)

    def drawBackground(self, painter, rect):

        size = 40

        pixmap = qt.QPixmap(size, size)
        pixmap.fill(qt.QtCore.Qt.transparent)

        pix_painter = qt.QPainter(pixmap)
        pix_painter.setBrush(qt.QColor.fromRgbF(.15, .15, .15, 1))

        pen = qt.QPen()
        pen.setStyle(qt.Qt.NoPen)
        pix_painter.setPen(pen)
        pix_painter.drawRect(0, 0, size, size)

        pen = qt.QPen()
        pen.setColor(qt.QColor.fromRgbF(0, 0, 0, .6))
        pen.setStyle(qt.Qt.SolidLine)

        middle = size * .5

        if self._zoom >= 2.5:
            pen.setWidth(1.5)
            pix_painter.setPen(pen)

            offset = 2

            pix_painter.drawLine(middle - offset, middle, middle + offset, middle)
            pix_painter.drawLine(middle, middle - offset, middle, middle + offset)

        if self._zoom >= .75 and self._zoom < 2.5:
            pen.setWidth(3)
            pix_painter.setPen(pen)
            pix_painter.drawPoint(qt.QtCore.QPointF(middle, middle))

        pix_painter.end()

        painter.fillRect(rect, pixmap)

    def _define_main_scene(self):

        if hasattr(self, 'main_scene') and self.main_scene:
            self.main_scene.clear()

        self.main_scene = NodeScene()

        self.main_scene.setObjectName('main_scene')

        self.setScene(self.main_scene)

        # small scene size helps the panning
        self.main_scene.setSceneRect(0, 0, 1, 1)

        self.setResizeAnchor(qt.QGraphicsView.AnchorViewCenter)

    def keyPressEvent(self, event):
        items = self.main_scene.selectedItems()

        if event.modifiers() == qt.QtCore.Qt.ControlModifier and event.key() == qt.QtCore.Qt.Key_D:
            new_items = []
            for item in items:
                new_item = self.duplicate_rig_node(item)
                new_items.append(new_item)

            for item in new_items:
                item.graphic.setSelected(True)

        if event.key() == qt.Qt.Key_F:
            if items:
                self.main_scene.center_on(items[0])

        if event.key() == qt.Qt.Key_Delete:
            self.base.delete(items)

        super(NodeGraphicsView, self).keyPressEvent(event)
        return True

    def wheelEvent(self, event):
        """
        Zooms the QGraphicsView in/out.

        """

        if qt.is_pyside6():
            mouse_pos = event.scenePosition()
            mouse_pos = mouse_pos.toPoint()
        else:
            mouse_pos = event.pos()

        item = self.itemAt(mouse_pos)
        item_string = str(item)

        if item_string.find('widget=QComboBoxPrivateContainer') > -1:
            return super(NodeGraphicsView, self).wheelEvent(event)

        else:
            in_factor = .85
            out_factor = 1.0 / in_factor

        if qt.is_pyside6():
            mouse_pos = event.scenePosition()
            mouse_pos = mouse_pos.toPoint()
        else:
            mouse_pos = event.pos()

        mouse_pos *= 1.0
        zoom_factor = None

        if qt.is_pyside6():
            delta = event.angleDelta().y()
        else:
            delta = event.delta()

        if delta < 0:
            zoom_factor = in_factor
        if delta > 0:
            zoom_factor = out_factor
        if delta == 0:
            return True

        self._zoom = self.transform().m11() * zoom_factor

        if self._zoom <= self._zoom_min:
            self._zoom = self._zoom_min

        if self._zoom >= self._zoom_max:
            self._zoom = self._zoom_max

        self.setTransform(qt.QTransform().scale(self._zoom, self._zoom))

        return True

    def mousePressEvent(self, event):
        if event.button() == qt.QtCore.Qt.MiddleButton or event.button() == qt.QtCore.Qt.RightButton:
            self.setDragMode(qt.QGraphicsView.NoDrag)
            self.prev_position = event.pos()
            if event.modifiers() == qt.QtCore.Qt.AltModifier and event.button() == qt.QtCore.Qt.RightButton:
                self.alt_drag = True
            else:
                self.drag = True

        if event.button() == qt.QtCore.Qt.RightButton:
            self.right_click = True
            return True

        if event.button() == qt.QtCore.Qt.MiddleButton:
            return True

        elif event.button() == qt.QtCore.Qt.LeftButton:
            self.setDragMode(qt.QGraphicsView.RubberBandDrag)

        return super(NodeGraphicsView, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):

        if self.drag:
            self.setCursor(qt.QtCore.Qt.SizeAllCursor)
            offset = self.prev_position - event.pos()

            distance = util_math.get_distance_2D([self.prev_position.x(), self.prev_position.y()],
                                                 [event.pos().x(), event.pos().y()])
            self.drag_accum += distance
            self.prev_position = event.pos()

            transform = self.transform()
            offset_x = offset.x() / transform.m11()
            offset_y = offset.y() / transform.m22()
            self.main_scene.setSceneRect(self.main_scene.sceneRect().translated(offset_x, offset_y))

            return True

        if self.alt_drag:
            self.setCursor(qt.QtCore.Qt.SizeAllCursor)
            offset = self.prev_position - event.pos()

            offset = offset.x()
            zoom_factor = 1
            in_factor = .9
            out_factor = 1.0 / in_factor

            if offset > self.prev_offset:
                zoom_factor = in_factor
            if offset < self.prev_offset:
                zoom_factor = out_factor

            self._zoom = self.transform().m11() * zoom_factor

            if self._zoom <= self._zoom_min:
                self._zoom = self._zoom_min

            if self._zoom >= self._zoom_max:
                self._zoom = self._zoom_max

            self.setTransform(qt.QTransform().scale(self._zoom, self._zoom))
            self.prev_offset = offset

            return True

        return super(NodeGraphicsView, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.drag:
            self.drag = False

            self.setCursor(qt.QtCore.Qt.ArrowCursor)
            self.setDragMode(qt.QGraphicsView.RubberBandDrag)

        if self.alt_drag:
            self.setCursor(qt.QtCore.Qt.ArrowCursor)
            self.setDragMode(qt.QGraphicsView.RubberBandDrag)
            self.alt_drag = False
            self._cancel_context_popup = True

        if self.right_click:
            if abs (self.drag_accum) > 30:
                self._cancel_context_popup = True

            # better for linux to build the context menu after mouse release
            if self._build_context_menu_later:
                self._build_context_menu(event)

            self.right_click = False
            self._build_context_menu_later = False

        self.drag_accum = 0
        return super(NodeGraphicsView, self).mouseReleaseEvent(event)
        # return True

    def contextMenuEvent(self, event):
        result = super(NodeGraphicsView, self).contextMenuEvent(event)

        if self._cancel_context_popup:
            self._cancel_context_popup = False
            return True
        else:
            if util.is_linux():
                self._build_context_menu_later = True
            else:
                self._build_context_menu(event)

        return result

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
            node_path = register_item[node_number].path
            actions = self.menu.actions()

            # this can be updated later to create nested sub menus.
            # for now it only handles one level
            path_menu = None
            for action in actions:
                if action.menu() and action.text() == node_path:
                    path_menu = action.menu()
            if not path_menu:
                path_menu = self.menu.addMenu(node_path)
                # self.menu.addMenu(path_menu)

            item_action = qt.QAction(node_name)
            if path_menu:
                path_menu.addAction(item_action)
            else:
                self.menu.addAction(item_action)

            item_action_dict[item_action] = node_number

        self.menu.addSeparator()

        action = self.menu.exec_(event.globalPos())

        pos = event.pos()
        pos = self.mapToScene(pos)

        if action in item_action_dict:
            node_number = item_action_dict[action]
            self.base.add_rig_item(node_number, pos)

        if action == self.store_action:
            self.base.save()

        if action == self.rebuild_action:
            self.base.open()

    def duplicate_rig_node(self, item):
        position = item.pos()

        new_position = [position.x() + 10, position.y() + 10]

        item_inst = self.base.add_rig_item(item.base.item_type, new_position)

        transfer_values(item.base, item_inst)

        return item_inst


class NodeView(object):

    def __init__(self):

        if not qt.is_batch():
            self.node_view = NodeGraphicsView(base=self)
        else:
            self.node_view = None

        self.items = []

        self._scene_signals()

    def _scene_signals(self):
        if not self.node_view:
            return

        self.node_view.main_scene.node_connect.connect(self._node_connected)
        self.node_view.main_scene.node_disconnect.connect(self._node_disconnected)
        self.node_view.main_scene.node_selected.connect(self._node_selected)

    def _node_connected(self, line_item):

        source_socket = line_item.source
        target_socket = line_item.target
        connect_socket(source_socket, target_socket)

        # exec_string = 'node_item._rig.%s = %s' % (socket_item.name, socket_item.value)
        # exec(exec_string, {'node_item':node_item})

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

    def delete(self, items):
        for item in items:
            self.items.remove(item.base)
            item.base.delete()

    def clear(self):
        self.items = []
        if self.node_view:
            self.node_view.main_scene.clear()

    def save(self):

        log.info('Save Nodes')

        found = []

        if self.node_view:
            graphic_items = self.node_view.scene().items()
            items = [graphic_item.base for graphic_item in graphic_items if hasattr(graphic_item, 'base')]
        else:
            items = self.items

        all_lines = []
        all_nodes = []
        for item in items:

            if not hasattr(item, 'item_type'):
                continue
            if not item.item_type:
                continue

            if item.item_type < ItemType.NODE:
                continue

            all_nodes.append(item)

            lines = []

            if hasattr(item, '_out_sockets'):
                for socket in item._out_sockets:
                    socket_lines = item._out_sockets[socket].lines
                    if socket_lines:
                        lines += socket_lines

            if lines:
                all_lines += lines

        for node in all_nodes:
            item_dict = node.store()
            found.append(item_dict)

        for line in all_lines:
            item_dict = line.store()
            found.append(item_dict)

        self._cache = found

        return found

    def open(self):

        watch = util.StopWatch()
        watch.start('Opening Graph')

        if not self._cache:
            watch.end()
            return

        item_dicts = self._cache

        self.clear()

        lines = []

        for item_dict in item_dicts:
            if len(item_dict) == 1:
                util.warning('Saved out item, only had one key: %s, skipping load on item.' % item_dict)
                continue
            type_value = item_dict['type']
            if type_value == ItemType.LINE:
                lines.append(item_dict)
            if type_value >= ItemType.NODE:
                self._build_rig_item(item_dict)

        for line in lines:
            self._build_line(line)

        util.show('%s items loaded' % len(item_dicts))
        watch.end()

    def _build_rig_item(self, item_dict):
        type_value = item_dict['type']
        uuid_value = item_dict['uuid']
        item_inst = register_item[type_value](uuid_value=uuid_value)

        uuids[uuid_value] = item_inst

        item_inst.load(item_dict)

        if item_inst:
            self.add_item(item_inst)

            if self.node_view:
                item_inst.graphic.setZValue(item_inst.graphic._z_value)

    def _build_line(self, item_dict):
        line_inst = NodeLine()
        line_inst.load(item_dict)

        self.add_item(line_inst)

    def add_item(self, item_inst):

        if self.node_view:
            if hasattr(item_inst, 'base'):
                item_inst = item_inst.base
            self.node_view.main_scene.addItem(item_inst.graphic)
            self.items.append(item_inst)

    def add_rig_item(self, node_type, position):
        item_inst = None
        if type(position) != qt.QtCore.QPointF:
            new_position = qt.QtCore.QPointF()

            new_position.setX(position[0])
            new_position.setY(position[1])
            position = new_position

        if node_type in register_item:
            item_inst = register_item[node_type]()

            self.add_item(item_inst)
            if self.node_view:

                item_inst.graphic.setPos(position)
                item_inst.graphic.setZValue(item_inst.graphic._z_value)

        self.node_view.main_scene.clearSelection()
        item_inst.graphic.setSelected(True)
        return item_inst


class NodeViewDirectory(NodeView):

    def set_directory(self, directory):

        self._cache = None
        self.directory = directory

        self.clear()
        self.open()

    def get_file(self):

        if not hasattr(self, 'directory'):
            return

        if not util_file.exists(self.directory):
            util_file.create_dir(self.directory)

        path = os.path.join(self.directory, 'ramen.json')

        return path

    def save(self, comment='Auto Saved'):
        result = super(NodeViewDirectory, self).save()

        filepath = self.get_file()

        util_file.set_json(filepath, self._cache, append=False)

        version = util_file.VersionFile(filepath)
        version.save(comment)

        util.show('Saved Ramen to: %s' % filepath)

        return filepath

    def open(self, filepath=None):
        self.node_view.main_scene.clear()
        if not filepath:
            filepath = self.get_file()
        if filepath and util_file.exists(filepath):
            self._cache = util_file.get_json(filepath)
        util.show('Loading %s' % filepath)
        super(NodeViewDirectory, self).open()


class NodeScene(qt.QGraphicsScene):
    node_disconnect = qt.create_signal(object, object)
    node_connect = qt.create_signal(object)
    node_selected = qt.create_signal(object)

    def __init__(self):
        super(NodeScene, self).__init__()
        self.selection = None
        self.selectionChanged.connect(self._selection_changed)

    def mouseMoveEvent(self, event):
        super(NodeScene, self).mouseMoveEvent(event)

        if not self.selection:
            return True

        if in_unreal:
            if self.selection:
                scope = get_base(self.selection)
                update_node_positions(scope)

        if not self.selection or len(self.selection) == 1:
            return True

        if not event.buttons() == qt.QtCore.Qt.LeftButton:
            return True

        for item in self.selection:

            item = item.base

            sockets = item.get_all_sockets()

            visited = {}

            for socket_name in sockets:
                socket = sockets[socket_name]
                if socket_name in visited:
                    continue
                if hasattr(socket, 'lines'):
                    for line in socket.lines:
                        if line.source and line.target:
                            line.graphic.point_a = line.source.graphic.get_center()
                            line.graphic.point_b = line.target.graphic.get_center()

                visited[socket_name] = None

        return True

    def _selection_changed(self):

        items = self.selectedItems()

        if items:
            self.selection = items
        else:
            self.selection = []

        self.node_selected.emit(items)

    def center_on(self, item):
        item_pos = item.scenePos()
        scene_rect = self.sceneRect()
        translation = item_pos - scene_rect.center()

        self.setSceneRect(scene_rect.translated(translation))


class SideMenu(qt.QFrame):

    def __init__(self, parent=None):
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

#--- Attributes


class AttributeItem(object):
    item_type = None

    name = None
    value = None
    data_type = None

    def __init__(self, graphic=None):

        self._name = None
        self._value = None
        self._data_type = None
        self.graphic = graphic
        if self.graphic:
            self.graphic.base = self
        self.parent = None

    def _get_value(self):
        if self._value == None and self.graphic:
            graphic_value = self.graphic.get_value()
            if graphic_value != None:
                self._value = graphic_value
        return self._value

    def _set_value(self, value):

        self._value = value

        if self.graphic:
            self.graphic.set_value(value)

    def _set_name(self, name):
        self._name = name
        if self.graphic:
            self.graphic.set_name(name)

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

    def set_graphic(self, item_inst):
        if not qt.is_batch():
            self.graphic = item_inst
            self.graphic.base = self

    def store(self):

        item_dict = {}
        if self.graphic:
            self.item_type = self.graphic.item_type
        else:
            item_dict['type'] = self.item_type

        return item_dict

    def load(self, item_dict):
        pass

    def set_parent(self, parent_item):
        if hasattr(parent_item, 'base'):
            parent_item = parent_item.base

        self.parent = parent_item

        if self.graphic:
            self.graphic.setParentItem(parent_item.graphic)

            if hasattr(parent_item.graphic, 'node_width'):
                self.graphic.node_width = parent_item.graphic.node_width

    def get_parent(self):
        return self.parent
        """
        if not self.graphic:
            return

        return self.graphic.parentItem().base
        """


class AttributeGraphicItem(qt.QGraphicsObject):
    item_type = ItemType.WIDGET
    changed = qt.create_signal(object, object)

    def __init__(self, parent=None, width=80, height=16):
        self.base = None
        self.value = None
        self.name = None
        super(AttributeGraphicItem, self).__init__(parent)

    def _convert_to_nicename(self, name):

        name = name.replace('_', ' ')
        name = name.title()

        return name

    def get_value(self):
        return self.value

    def set_value(self, value):
        self.value = value

    def set_name(self, name):
        self.name = name


class GraphicTextItem(qt.QGraphicsTextItem):

    edit = qt.create_signal(object)
    before_text_changed = qt.create_signal()
    after_text_changed = qt.create_signal()
    send_change = qt.create_signal()
    tab_pressed = qt.create_signal()
    backtab_pressed = qt.create_signal()

    def __init__(self, text=None, parent=None, rect=None):
        super(GraphicTextItem, self).__init__(text, parent)
        self.rect = rect
        self.setFlag(qt.QGraphicsTextItem.ItemIsSelectable, False)
        self.setFlag(qt.QGraphicsTextItem.ItemIsFocusable, True)

        self.setDefaultTextColor(qt.QColor(160, 160, 160, 255))
        self.limit = True
        self.setTabChangesFocus(False)
        self.setTextInteractionFlags(qt.QtCore.Qt.TextEditable)
        self._cache_value = None
        self._select_text = False
        self._just_mouse_pressed = True
        self._placeholder = False

    def boundingRect(self):

        if self.limit:
            return self.rect
        else:
            rect = super(GraphicTextItem, self).boundingRect()
            return rect

    def mousePressEvent(self, event):

        accepted = super(GraphicTextItem, self).mousePressEvent(event)

        if self._select_text:
            self.select_text()
            self._select_text = False

        if self._just_mouse_pressed:
            self._just_mouse_pressed = False

        if self._placeholder:
            self.cursor_start()

        return accepted

    def mouseMoveEvent(self, event):

        if self._placeholder:
            event.ignore()
        else:
            super(GraphicTextItem, self).mouseMoveEvent(event)

    def focusInEvent(self, event):
        self.setTextInteractionFlags(qt.QtCore.Qt.TextEditorInteraction)
        accepted = super(GraphicTextItem, self).focusInEvent(event)
        self._cache_value = self.toPlainText()
        self.edit.emit(True)
        return accepted

    def focusOutEvent(self, event):

        accepted = super(GraphicTextItem, self).focusOutEvent(event)

        self.edit.emit(False)
        self.setTextInteractionFlags(qt.QtCore.Qt.TextEditable)
        self._just_mouse_pressed = True
        return accepted

    def event(self, event):
        if event.type() == qt.QtCore.QEvent.KeyPress:
            if event.key() == qt.QtCore.Qt.Key_Tab:
                self._emit_tab(self.tab_pressed)
                return True
            if event.key() == qt.QtCore.Qt.Key_Backtab:
                self._emit_tab(self.backtab_pressed)
                return True

        return super(GraphicTextItem, self).event(event)

    def _emit_tab(self, tab_signal):
        self.clearFocus()
        if self.toPlainText() != self._cache_value:
            self.send_change.emit()
        tab_signal.emit()

    def keyPressEvent(self, event):
        self.limit = False
        self.before_text_changed.emit()
        key = event.key()
        if key == qt.QtCore.Qt.Key_Return or key == qt.QtCore.Qt.Key_Enter:
            self._cache_value = self.toPlainText()
            self.cursor_end()

            self.send_change.emit()
            self.edit.emit(False)

            return True
        else:
            result = super(GraphicTextItem, self).keyPressEvent(event)
            self.after_text_changed.emit()
            return result

    def paint(self, painter, option, widget):
        option.state = qt.QStyle.State_None
        super(GraphicTextItem, self).paint(painter, option, widget)

    def select_text(self):
        cursor = self.textCursor()
        cursor.select(qt.QTextCursor.Document)
        self.setTextCursor(cursor)

    def clear_selection(self):
        cursor = qt.QTextCursor(self.document())
        cursor.clearSelection()
        self.setTextCursor(cursor)

    def cursor_start(self):
        text_cursor = qt.QTextCursor(self.document())
        text_cursor.movePosition(qt.QTextCursor.Start)
        self.setTextCursor(text_cursor)

    def cursor_end(self):
        text_cursor = qt.QTextCursor(self.document())
        text_cursor.movePosition(qt.QTextCursor.End)
        self.setTextCursor(text_cursor)

    def cursor_reset(self):
        cursor = qt.QTextCursor()
        self.setTextCursor(cursor)

    def strip(self):
        text = self.toPlainText()
        text = text.strip()
        text.replace('\t', '')
        self.setPlainText(text)


class CompletionTextItem(GraphicTextItem):

    text_clicked = qt.create_signal(object)

    def __init__(self, text=None, parent=None, rect=None):
        super(CompletionTextItem, self).__init__(text, parent, rect)
        self.setFlag(qt.QGraphicsTextItem.ItemIsFocusable, False)
        self.setFlag(qt.QGraphicsTextItem.ItemStopsClickFocusPropagation, True)
        self.setFlag(qt.QGraphicsTextItem.ItemStopsFocusHandling, True)

    def mousePressEvent(self, event):

        position = event.pos()

        pos_y = position.y() - self.pos().y()
        if pos_y < 1:
            self.hide()
            return True
        font_metrics = qt.QFontMetrics(self.font())
        line_height = font_metrics.height()
        part = pos_y / line_height
        section = math.floor(part)

        block = self.document().findBlockByLineNumber(section)

        self.edit.emit(True)
        self.limit = False

        self.text_clicked.emit(block.text())
        self.hide()

        event.isAccepted()
        return True


class NumberTextItem(GraphicTextItem):

    # tab_pressed = qt.create_signal()

    def __init__(self, text=None, parent=None, rect=None):
        super(NumberTextItem, self).__init__(text, parent, rect)
        self.setDefaultTextColor(qt.QColor(0, 0, 0, 255))

    def keyPressEvent(self, event):
        self.before_text_changed.emit()

        accept_text = True
        result = True
        text = event.text()

        if event.key() == qt.QtCore.Qt.Key_Return:
            self.send_change.emit()
            self.edit.emit(False)

            accept_text = False

        if event.key() == qt.QtCore.Qt.Key_Tab:
            accept_text = False

        if accept_text and not self._is_text_acceptable(text):
            accept_text = False

        if accept_text:
            result = super(NumberTextItem, self).keyPressEvent(event)

        self.after_text_changed.emit()

        return result

    def mousePressEvent(self, event):
        just_pressed = self._just_mouse_pressed
        if just_pressed:
            self.select_text()
            if self._just_mouse_pressed:
                self._just_mouse_pressed = False
            return True
        else:
            return super(GraphicTextItem, self).mousePressEvent(event)

    def _is_text_acceptable(self, text):
        full_text = self.toPlainText()

        if text == '.' and full_text.find('.') > -1:
            selected_text = self.textCursor().selectedText()
            if selected_text.find('.') > -1:
                return True

            return False
        elif text.isalpha():
            return False
        else:
            return True


class StringItem(AttributeGraphicItem):
    item_type = ItemType.WIDGET
    edit = qt.create_signal(object)
    changed = qt.create_signal(object, object)

    def __init__(self, parent=None, width=80, height=16):
        self._using_placeholder = False

        super(StringItem, self).__init__()

        self.setParentItem(parent)
        self.width = width
        self.height = height
        self._init_values()
        self._init_paint()
        self._build_items()

        self.setFlag(qt.QGraphicsItem.ItemIsFocusable)

        self._paint_base_text = True

    def _init_values(self):

        self.limit = True
        self._text_pixel_size = 12
        self._background_color = qt.QColor(30, 30, 30, 255)
        self._edit_mode = False
        self._completion_examples = []
        self._completion_examples_current = []
        self._completion_rect = None

        self.rect = qt.QtCore.QRect(10, 2, self.width, self.height)
        text_rect = qt.QtCore.QRect(0, self.rect.y(), self.width, self.height)
        self.text_rect = text_rect

        self.text_item = None

    def _build_items(self):
        self.place_holder = ''

        self.text_item = self._define_text_item()

        self.text_item.setTextWidth(self.width)
        self.text_item.edit.connect(self._edit)

        self.text_item.setPos(10, -2)
        self.text_item.setFont(self.font)
        self.text_item.setFlag(qt.QGraphicsItem.ItemIsFocusable)
        self.text_item.setFlag(qt.QGraphicsItem.ItemClipsToShape)

        self.text_item.setParentItem(self)
        self.text_item.before_text_changed.connect(self._before_text_changed)
        self.text_item.after_text_changed.connect(self._after_text_changed)
        self.text_item.send_change.connect(self._emit_change)

        self.completion_text_item = CompletionTextItem(rect=self.text_rect)
        self.completion_text_item.hide()
        self.completion_text_item.setParentItem(self)
        self.completion_text_item.setPos(15, 5)
        self.completion_text_item.text_clicked.connect(self._update_text)

        self.dynamic_text_rect = self._get_dynamic_text_rect()

    def _init_paint(self):
        self.font = qt.QFont()
        self.font.setPixelSize(self._text_pixel_size)

        # Brush.
        self.brush = qt.QBrush()
        self.brush.setStyle(qt.QtCore.Qt.SolidPattern)
        self.brush.setColor(self._background_color)

        # Pen.
        self.pen = qt.QPen()
        self.pen.setStyle(qt.QtCore.Qt.SolidLine)
        self.pen.setWidth(.5)
        self.pen.setColor(qt.QColor(90, 90, 90, 255))

    def _define_text_item(self):
        return GraphicTextItem(rect=self.text_rect)

    def _define_text_color(self):
        return qt.QColor(160, 160, 160, 255)

    def boundingRect(self):
        return self.rect

    def paint(self, painter, option, widget):
        # TODO refactor into smaller functions
        self.brush.setColor(self._background_color)
        self.font.setPixelSize(self._text_pixel_size)
        if not self._paint_base_text:
            return
        if self.placeholder_state():
            self.text_item.setDefaultTextColor(qt.QColor(80, 80, 80, 255))
            self.text_item._placeholder = True
        else:
            self.text_item.setDefaultTextColor(self._define_text_color())
            self.text_item._placeholder = False

        painter.setBrush(self.brush)
        painter.setFont(self.font)
        painter.setPen(self.pen)

        painter.drawRoundedRect(self.dynamic_text_rect, 0, 0)

        if self._completion_examples_current and self._completion_rect:

            painter.drawRoundedRect(self._completion_rect, 0, 0)

    def _update_text(self, text):
        self.text_item.setPlainText(text)
        self.placeholder_state(False)

        self._completion_examples_current = []
        self.completion_text_item.hide()

        if self._edit_mode:
            self.text_item.setFocus(qt.QtCore.Qt.MouseFocusReason)
            self.text_item.cursor_end()

        else:
            self.text_item.clearFocus()

    def _edit(self, bool_value):
        if self._edit_mode == bool_value:
            return

        self._edit_mode = bool_value
        self.edit.emit(bool_value)
        self.scene().clearSelection()

        if bool_value:
            self._edit_on()

        else:
            self._edit_off()

    def _edit_on(self):
        self._edit_mode = True
        self.limit = False

        self.text_item.limit = False
        self.completion_text_item.setFlag(qt.QGraphicsItem.ItemClipsToShape)

        if self.placeholder_state():
            self.text_item.cursor_start()
        #    self.text_item._select_text = True
        else:
            self.text_item.cursor_end()

        current_text = self.text_item.toPlainText()
        self._update_completion(current_text)
        self.dynamic_text_rect = self._get_dynamic_text_rect()

    def _edit_off(self):
        self._edit_mode = False
        self.limit = True
        self.text_item.limit = True

        self._completion_examples_current = []
        self.completion_text_item.hide()

        self.dynamic_text_rect = self._get_dynamic_text_rect()
        self.text_item.clear_selection()

        if self.text_item.toPlainText() != self.text_item._cache_value:
            self._emit_change()

        self.text_item.clearFocus()
        self.text_item.cursor_reset()

    def _before_text_changed(self):

        current_text = self.text_item.toPlainText()
        if self.placeholder_state() and current_text:
            self.text_item.setPlainText('')
            self.placeholder_state(False)

    def _after_text_changed(self):
        self.dynamic_text_rect = self._get_dynamic_text_rect()
        current_text = self.text_item.toPlainText()
        if current_text:
            self._update_completion(current_text)
        else:
            if self.place_holder:
                self.text_item.setPlainText(self.place_holder)
                self.placeholder_state(True)

    def _update_completion(self, current_text):
        matches = self._get_completion_matches(current_text)
        if matches:
            self._load_matches(matches)

    def _get_completion_matches(self, text):
        if self._completion_examples:
            matches = []

            for example in self._completion_examples:
                found = False
                if example.find(text) > -1:
                    matches.append(example)
                    found = True
                if not found:
                    if example.find(text.title()) > -1:
                        matches.append(example)

            return matches

    def _load_matches(self, matches):
        self._completion_examples_current = matches

        text = ''
        for example in self._completion_examples_current:
            text += '\n%s' % example

        self.completion_text_item.setPlainText(text)
        self.completion_text_item.setFlag(qt.QGraphicsItem.ItemClipsToShape)
        self.completion_text_item.show()

        self._completion_rect = self._get_completion_rect()

    def _get_completion_rect(self):

        size_value = self.completion_text_item.document().size()
        width = self.rect.width() * 1.3
        height = size_value.height()
        if height > 200:
            height = 200
        rect = qt.QtCore.QRect(0,
                               12,
                               width,
                               height)
        self.completion_text_item.rect = rect

        rect = qt.QtCore.QRect(10,
                   self.height + 7,
                   width,
                   height + 7)

        return rect

    def _get_dynamic_text_rect(self):
        size_value = self.text_item.document().size()

        if self.text_item.limit:
            rect = self.rect
        else:

            width = self.rect.width() * 1.3

            rect = qt.QtCore.QRect(10,
                                   0,
                                   width,
                                   size_value.height())
            if self.text_item:
                self.text_item.setTextWidth(width)

        return rect

    def _emit_change(self):
        if self.text_item:
            self.base.value = self.get_value()
        self.changed.emit(self.base.name, self.get_value())

    def set_background_color(self, qcolor):

        self._background_color = qcolor

    def set_text_pixel_size(self, pixel_size):
        self._text_pixel_size = pixel_size
        self.font.setPixelSize(self._text_pixel_size)

    def set_placeholder(self, text):
        self.place_holder = text
        self.placeholder_state(True)
        if self.text_item:
            self.text_item.setPlainText(self.place_holder)

    def placeholder_state(self, state=None):
        if state != None:
            self._using_placeholder = state

            if self.text_item:
                self.text_item._placeholder = self._using_placeholder

        return self._using_placeholder

    def set_completion_examples(self, list_of_strings):
        self._completion_examples = list_of_strings

    def get_value(self):
        if self.placeholder_state():
            return ['']
        value = self.text_item.toPlainText()
        return [value]

    def set_value(self, value):

        if isinstance(value, list) and len(value) == 1:
            value = value[0]

        if not value:
            self.placeholder_state(True)
            if self.place_holder:
                self.text_item.setPlainText(self.place_holder)
            return

        self.placeholder_state(False)

        self.text_item.setPlainText(str(value))

    def set_name(self, name):
        self.set_placeholder(self._convert_to_nicename(name))


class BoolGraphicItem(AttributeGraphicItem):
    item_type = ItemType.WIDGET
    changed = qt_ui.create_signal(object, object)

    def __init__(self, parent=None, width=15, height=15):
        self.value = None
        super(AttributeGraphicItem, self).__init__(parent)
        self.setFlag(qt.QGraphicsItem.ItemIsSelectable, False)
        self.nice_name = ''

        self.rect = qt.QtCore.QRect(10, 0, width, height)

        self._init_paint()

    def _init_paint(self):
        # Brush.
        self.brush = qt.QBrush()
        self.brush.setStyle(qt.QtCore.Qt.SolidPattern)
        self.brush.setColor(qt.QColor(30, 30, 30, 255))

        # Pen.
        self.pen = qt.QPen()
        self.pen.setStyle(qt.QtCore.Qt.SolidLine)
        self.pen.setWidth(1)
        self.pen.setColor(qt.QColor(120, 120, 120, 255))

        self.pen_select = qt.QPen()
        self.pen_select.setStyle(qt.QtCore.Qt.SolidLine)
        self.pen_select.setWidth(3)
        self.pen_select.setColor(qt.QColor(255, 255, 255, 255))

        self.title_font = qt.QFont()
        self.title_font.setPixelSize(10)
        self.title_pen = qt.QPen()
        self.title_pen.setWidth(.5)
        self.title_pen.setColor(qt.QColor(200, 200, 200, 255))

        self.check_pen = qt.QPen()
        self.check_pen.setWidth(2)
        self.check_pen.setCapStyle(qt.QtCore.Qt.RoundCap)
        self.check_pen.setColor(qt.QColor(200, 200, 200, 255))

    def paint(self, painter, option, widget):
        painter.setBrush(self.brush)
        painter.setPen(self.pen)

        painter.drawRoundedRect(self.rect, 5, 5)

        painter.setPen(self.title_pen)
        painter.setFont(self.title_font)
        painter.drawText(30, 12, self.nice_name)
        if self.value:
            painter.setPen(self.check_pen)
            line1 = qt.QtCore.QLine(self.rect.x() + 3,
                            self.rect.y() + 7,
                            self.rect.x() + 6,
                            self.rect.y() + 12)

            line2 = qt.QtCore.QLine(self.rect.x() + 6,
                            self.rect.y() + 12,
                            self.rect.x() + 12,
                            self.rect.y() + 4)

            painter.drawLines([line1, line2])

        # painter.drawRect(self.rect)

    def mousePressEvent(self, event):

        # super(BoolGraphicItem, self).mousePressEvent(event)

        if self.value == 1:
            self.value = 0
        else:
            self.value = 1

        self.update()
        self.changed.emit(self.name, self.value)

        return True

    def boundingRect(self):
        return qt.QtCore.QRectF(self.rect)

    def get_value(self):
        value = super(BoolGraphicItem, self).get_value()
        return value

    def set_value(self, value):
        super(BoolGraphicItem, self).set_value(value)

    def set_name(self, name):
        super(BoolGraphicItem, self).set_name(name)
        self.nice_name = self._convert_to_nicename(name)


class IntGraphicItem(StringItem):

    def __init__(self, parent=None, width=50, height=14):
        super(IntGraphicItem, self).__init__(parent, width, height)

        self._using_placeholder = False
        self._nice_name = None
        self._background_color = qt.QColor(255 * .6 * .8, 255 * 1 * .8, 255 * .8 * .8, 255)

    def _define_text_item(self):
        return NumberTextItem(rect=self.text_rect)

    def _define_text_color(self):
        return qt.QColor(20, 20, 20, 255)

    def _init_paint(self):

        self.font = qt.QFont()
        self.font.setPixelSize(self._text_pixel_size)
        self.font.setBold(False)

        # Brush.
        self.brush = qt.QBrush()
        self.brush.setStyle(qt.QtCore.Qt.SolidPattern)
        self.brush.setColor(self._background_color)

        # Pen.
        self.pen = qt.QPen()
        self.pen.setStyle(qt.QtCore.Qt.SolidLine)
        self.pen.setWidth(.5)
        self.pen.setColor(qt.QColor(90, 90, 90, 255))

        self.title_font = qt.QFont()
        self.title_font.setPixelSize(10)
        self.title_pen = qt.QPen()
        self.title_pen.setWidth(.5)
        self.title_pen.setColor(qt.QColor(200, 200, 200, 255))

    def paint(self, painter, option, widget):
        option.state = qt.QStyle.State_None
        if self._nice_name:
            painter.setPen(self.title_pen)
            painter.setFont(self.title_font)
            painter.drawText(self.width + 15, 15, self._nice_name)

        super(IntGraphicItem, self).paint(painter, option, widget)

    def _edit(self, bool_value):
        if self._edit_mode == bool_value:
            return

        self._edit_mode = bool_value

        self.edit.emit(bool_value)
        self.scene().clearSelection()
        if bool_value:
            self.limit = False
            self.text_item.limit = False
            self.text_item.select_text()
            self.dynamic_text_rect = self._get_dynamic_text_rect()
        else:
            self.limit = True
            self.text_item.limit = True
            self.text_item.clear_selection()
            self.text_item.clearFocus()
            self.dynamic_text_rect = self._get_dynamic_text_rect()
            # self._emit_change()

    def _number_to_text(self, number):
        return str(int(number))

    def _text_to_number(self, text):
        number = 0
        if text:
            number = int(round(float(text), 0))

        return number

    def _current_text_to_number(self):

        if not self.text_item:
            return
        text = self.text_item.toPlainText()
        if text:
            number = self._text_to_number(text)
        else:
            number = 0

        return number

    def _emit_change(self):
        if self.text_item:
            if self.text_item.toPlainText() == self.text_item._cache_value:
                return
            number = self._current_text_to_number()
            self.text_item.setPlainText(str(number))
        super(IntGraphicItem, self)._emit_change()

    def _before_text_changed(self):
        return

    def _after_text_changed(self):
        return

    def get_value(self):
        value = self._current_text_to_number()
        return [value]

    def set_value(self, value):
        if value:
            value = value[0]

        if self.text_item:
            self.text_item.setPlainText(self._number_to_text(value))

    def set_name(self, name):
        super(IntGraphicItem, self).set_name(name)
        self._nice_name = self._convert_to_nicename(name)


class NumberGraphicItem(IntGraphicItem):

    def _text_to_number(self, text):
        number = 0.00
        if text:
            number = round(float(text), 3)

        return number

    def _number_to_text(self, number):
        return str(round(number, 3))

    def set_value(self, value):
        super(StringItem, self).set_value(value)
        if isinstance(value, float):
            value = [value]

        value = value[0]
        if self.text_item:
            self.text_item.setPlainText(self._number_to_text(value))


class VectorGraphicItem(NumberGraphicItem):

    def __init__(self, parent=None, width=100, height=14):
        super(VectorGraphicItem, self).__init__(parent, width, height)
        self._paint_base_text = False

    def _build_items(self):
        text_size = 8
        self.vector_x = AttributeItem()
        self.vector_x.set_graphic(NumberGraphicItem(self, 35))
        self.vector_x.graphic.setZValue(100)
        self.vector_x.graphic.set_background_color(qt.QColor(255 * .8, 200 * .8, 200 * .8, 255))

        self.vector_y = AttributeItem()
        self.vector_y.set_graphic(NumberGraphicItem(self, 35))
        self.vector_y.graphic.moveBy(35, 0)
        self.vector_y.graphic.setZValue(90)
        self.vector_y.graphic.set_background_color(qt.QColor(200 * .8, 255 * .8, 200 * .8, 255))

        self.vector_z = AttributeItem()
        self.vector_z.set_graphic(NumberGraphicItem(self, 35))
        self.vector_z.graphic.moveBy(70, 0)
        self.vector_z.graphic.setZValue(80)
        self.vector_z.graphic.set_background_color(qt.QColor(200 * .8, 200 * .8, 255 * .8, 255))

        self.vector_x.graphic.changed.connect(self._emit_vector_change)
        self.vector_y.graphic.changed.connect(self._emit_vector_change)
        self.vector_z.graphic.changed.connect(self._emit_vector_change)

        self.numbers = [self.vector_x, self.vector_y, self.vector_z]

        for vector in self.numbers:
            vector.graphic.set_text_pixel_size(text_size)

        self.vector_x.graphic.text_item.tab_pressed.connect(self._handle_tab_x)
        self.vector_y.graphic.text_item.tab_pressed.connect(self._handle_tab_y)
        self.vector_z.graphic.text_item.tab_pressed.connect(self._handle_tab_z)
        self.vector_x.graphic.text_item.backtab_pressed.connect(self._handle_backtab_x)
        self.vector_y.graphic.text_item.backtab_pressed.connect(self._handle_backtab_y)
        self.vector_z.graphic.text_item.backtab_pressed.connect(self._handle_backtab_z)

    def _set_other_focus(self, other_item):
        graphic = other_item.graphic

        graphic.text_item.setTextInteractionFlags(qt.QtCore.Qt.TextEditorInteraction)
        graphic.text_item.setFocus(qt.QtCore.Qt.TabFocusReason)

    def _handle_tab_x(self):
        self._set_other_focus(self.vector_y)

    def _handle_tab_y(self):
        self._set_other_focus(self.vector_z)

    def _handle_tab_z(self):
        self._set_other_focus(self.vector_x)

    def _handle_backtab_x(self):
        self._set_other_focus(self.vector_z)

    def _handle_backtab_y(self):
        self._set_other_focus(self.vector_x)

    def _handle_backtab_z(self):
        self._set_other_focus(self.vector_y)

    def _emit_vector_change(self):
        self._emit_change()

    def _emit_change(self):
        self.changed.emit(self.base.name, self.get_value())

    def _init_paint(self):
        super(VectorGraphicItem, self)._init_paint()
        self.title_font = qt.QFont()
        self.title_font.setPixelSize(8)

    def get_value(self):

        value_x = self.numbers[0].value[0]
        value_y = self.numbers[1].value[0]
        value_z = self.numbers[2].value[0]

        return [(value_x, value_y, value_z)]

    def set_value(self, value):
        if not value:
            return
        self.numbers[0].value = [value[0][0]]
        self.numbers[1].value = [value[0][1]]
        self.numbers[2].value = [value[0][2]]


class ColorPickerItem(AttributeGraphicItem):
    item_type = ItemType.WIDGET
    changed = qt_ui.create_signal(object, object)

    def __init__(self, parent=None, width=40, height=14):
        super(ColorPickerItem, self).__init__(parent)
        self._name = 'color'

        self.rect = qt.QtCore.QRect(10, 15, width, height)

        self._init_paint()

    def _init_paint(self):
        # Brush.
        self.brush = qt.QBrush()
        self.brush.setStyle(qt.QtCore.Qt.SolidPattern)
        self.brush.setColor(qt.QColor(90, 90, 90, 255))

        # Pen.
        self.pen = qt.QPen()
        self.pen.setStyle(qt.QtCore.Qt.SolidLine)
        self.pen.setWidth(1)
        self.pen.setColor(qt.QColor(20, 20, 20, 255))

        self.pen_select = qt.QPen()
        self.pen_select.setStyle(qt.QtCore.Qt.SolidLine)
        self.pen_select.setWidth(3)
        self.pen_select.setColor(qt.QColor(255, 255, 255, 255))

    def paint(self, painter, option, widget):
        painter.setBrush(self.brush)
        if self.isSelected():
            painter.setPen(self.pen_select)
        else:
            painter.setPen(self.pen)

        painter.drawRoundedRect(self.rect, 5, 5)

    def mousePressEvent(self, event):

        # super(ColorPickerItem, self).mousePressEvent(event)

        color_dialog = qt.QColorDialog(self.scene().activeWindow())
        color_dialog.setWindowFlags(color_dialog.windowFlags() | qt.QtCore.Qt.WindowStaysOnTopHint)
        # color = color_dialog.getColor()
        color_dialog.activateWindow()
        color_dialog.setFocus()

        initial_value = self.get_value()[0]
        initial_color = qt.QColor()
        initial_color.setRgbF(initial_value[0], initial_value[1], initial_value[2], 1.0)
        color_dialog.setCurrentColor(initial_color)

        color_dialog.exec_()

        color = color_dialog.currentColor()

        if not color.isValid():
            return True

        self.brush.setColor(color)
        self.update()

        self.changed.emit(self.name, self.get_value())

        return True

    def boundingRect(self):
        return qt.QtCore.QRectF(self.rect)

    def get_value(self):
        color = self.brush.color()
        color_value = color.getRgbF()
        color_value = [color_value[0], color_value[1], color_value[2], 1.0]
        return [color_value]

    def set_value(self, value):
        if not value:
            return
        if isinstance(value, list) and len(value) == 1:
            value = value[0]
        color = qt.QColor()
        color.setRgbF(value[0], value[1], value[2], 1.0)
        self.brush.setColor(color)


class TitleItem(AttributeGraphicItem):

    item_type = ItemType.WIDGET

    def __init__(self, parent=None):
        super(TitleItem, self).__init__(parent)

        self.rect = qt.QtCore.QRect(0, 0, 150, 20)
        # self.rect = qt.QtCore.QRect(10,10,50,20)

        self.font = qt.QFont()
        self.font.setPixelSize(10)
        self.font.setBold(True)

        self.font_metrics = qt.QFontMetrics(self.font)

        # Brush.
        self.brush = qt.QBrush()
        self.brush.setStyle(qt.QtCore.Qt.SolidPattern)
        self.brush.setColor(qt.QColor(60, 60, 60, 255))

        # Pen.
        self.pen = qt.QPen()
        self.pen.setStyle(qt.QtCore.Qt.DotLine)
        self.pen.setWidth(.5)
        self.pen.setColor(qt.QColor(200, 200, 200, 255))

    def paint(self, painter, option, widget):
        painter.setBrush(self.brush)
        painter.setFont(self.font)
        painter.setPen(self.pen)

        bounding_rect = self.font_metrics.boundingRect(self.name)

        painter.drawText(6, 13, self.name)

        parent_item = self.parentItem()
        rect = parent_item.boundingRect()
        painter.drawLine(bounding_rect.width() + 15, 10, rect.width() - 20, 10)

    def boundingRect(self):
        return qt.QtCore.QRectF(self.rect)

#--- Sockets


class NodeSocketItem(AttributeGraphicItem):

    def __init__(self, base=None):
        super(NodeSocketItem, self).__init__()
        self.base = base
        self.new_line = None
        self.color = None
        self.rect = None
        self.side_socket_height = None
        self.pen = None
        self.brush = None
        self.node_width = None

        self.init_socket(self.base.socket_type, self.base.data_type)

        self.font = qt.QFont()
        self.font.setPixelSize(10)

        self.get_nice_name()

    def get_nice_name(self):

        name = self.base._name

        if name:
            split_name = name.split('_')
            if split_name:
                found = []
                for name in split_name:
                    name = name.title()
                    found.append(name)
                self.nice_name = ' '.join(found)
            else:
                self.nice_name = name.title()
        else:
            self.nice_name = None

    def init_socket(self, socket_type, data_type):
        self.node_width = 150
        self.rect = qt.QtCore.QRectF(0.0, 0.0, 0.0, 0.0)

        self.side_socket_height = 0

        # Brush.
        self.brush = qt.QBrush()
        self.brush.setStyle(qt.QtCore.Qt.SolidPattern)

        self.color = qt.QColor(60, 60, 60, 255)

        self.brush.setColor(self.color)

        # Pen.
        self.pen = qt.QPen()

        self.pen.setColor(qt.QColor(200, 200, 200, 255))

        if data_type == rigs.AttrType.TRANSFORM:
            self.color = qt.QColor(100, 200, 100, 255)
        if data_type == rigs.AttrType.STRING:
            self.color = qt.QColor(100, 150, 220, 255)
        if data_type == rigs.AttrType.COLOR:
            self.color = qt.QColor(220, 150, 100, 255)
        if data_type == rigs.AttrType.INT:
            self.color = qt.QColor(170, 90, 160, 255)
        if data_type == rigs.AttrType.NUMBER:
            self.color = qt.QColor(170, 110, 160, 255)
        if data_type == rigs.AttrType.VECTOR:
            self.color = qt.QColor(170, 70, 160, 255)
        self.brush.setColor(self.color)

        if socket_type == SocketType.IN:
            self.rect = qt.QtCore.QRect(-10.0, self.side_socket_height, 20.0, 20.0)

        if socket_type == SocketType.OUT:
            self.rect = qt.QtCore.QRect(self.node_width + 23, 5, 20.0, 20.0)

        if socket_type == SocketType.TOP:
            self.rect = qt.QtCore.QRect(10.0, -10.0, 15.0, 15.0)

    def boundingRect(self):
        return qt.QtCore.QRectF(self.rect)

    def paint(self, painter, option, widget):
        painter.setBrush(self.brush)
        painter.setPen(self.pen)
        self.pen.setStyle(qt.QtCore.Qt.NoPen)
        self.pen.setWidth(0)
        painter.setPen(self.pen)

        painter.setFont(self.font)

        if self.base.socket_type == SocketType.IN:

            rect = qt.QtCore.QRectF(self.rect)
            rect.adjust(3.0, 3.0, -3.0, -3.0)
            painter.drawEllipse(rect)

            self.pen.setStyle(qt.QtCore.Qt.SolidLine)
            self.pen.setWidth(1)
            painter.setPen(self.pen)

            if self.base._data_type == rigs.AttrType.STRING:
                pass
            elif self.base._data_type == rigs.AttrType.VECTOR:
                pass
            elif self.base._data_type == rigs.AttrType.COLOR:
                painter.drawText(qt.QtCore.QPoint(55, self.side_socket_height + 14), self.nice_name)
            else:
                painter.drawText(qt.QtCore.QPoint(15, self.side_socket_height + 14), self.nice_name)

        if self.base.socket_type == SocketType.OUT:

            parent = self.get_parent()
            if parent:
                self.node_width = parent.graphic.node_width

            self.rect.setX(self.node_width)

            poly = qt.QPolygon()

            poly.append(qt.QtCore.QPoint(0, 3))
            poly.append(qt.QtCore.QPoint(0, 17))
            poly.append(qt.QtCore.QPoint(6, 17))

            poly.append(qt.QtCore.QPoint(14, 12))
            poly.append(qt.QtCore.QPoint(15, 10))
            poly.append(qt.QtCore.QPoint(14, 8))

            poly.append(qt.QtCore.QPoint(6, 3))

            poly.translate(self.rect.x(), self.rect.y())
            painter.drawPolygon(poly)

            self.pen.setStyle(qt.QtCore.Qt.SolidLine)
            self.pen.setWidth(1)
            painter.setPen(self.pen)
            if qt.is_pyside6():
                name_len = painter.fontMetrics().horizontalAdvance(self.nice_name)
            else:
                name_len = painter.fontMetrics().width(self.nice_name)

            offset = self.node_width - 10 - name_len

            painter.drawText(qt.QtCore.QPoint(offset, self.side_socket_height + 17), self.nice_name)

        if self.base.socket_type == SocketType.TOP:
            rect = qt.QtCore.QRectF(self.rect)
            painter.drawRect(rect)

            self.pen.setStyle(qt.QtCore.Qt.SolidLine)
            self.pen.setWidth(1)
            painter.setPen(self.pen)

    def mousePressEvent(self, event):

        self.new_line = None

        if self.base.socket_type == SocketType.OUT:
            point_a = self.get_center()

            point_b = self.mapToScene(event.pos())
            self.new_line = NodeLine(point_a, point_b)

        elif self.base.socket_type == SocketType.IN:

            point_a = self.mapToScene(event.pos())
            point_b = self.get_center()

            self.new_line = NodeLine(point_a, point_b)

        else:
            super(NodeSocketItem, self).mousePressEvent(event)

        if self.new_line:
            self.base.add_line(self.new_line)

            views = self.scene().views()
            for view in views:
                view.base.add_item(self.new_line)
            self.new_line.graphic.color = self.color

        return True

    def mouseMoveEvent(self, event):
        if self.base.socket_type == SocketType.OUT:
            point_b = self.mapToScene(event.pos())
            self.new_line.graphic.point_b = point_b
        elif self.base.socket_type == SocketType.IN:
            point_a = self.mapToScene(event.pos())
            self.new_line.graphic.point_a = point_a
        else:
            super(NodeSocketItem, self).mouseMoveEvent(event)

        return True

    def mouseReleaseEvent(self, event):
        self.new_line.graphic.hide()

        graphic = self.scene().itemAt(event.scenePos().toPoint(), qt.QTransform())

        if not graphic or not hasattr(graphic, 'base'):
            self.base.remove_line(self.new_line)
            self.new_line = None
            return True

        item = graphic.base

        self.new_line.graphic.show()

        connection_fail = False
        if item:
            if not hasattr(item, 'data_type'):
                self.base.remove_line(self.new_line)
                self.new_line = None
                return True

            item_socket_type = None
            if hasattr(graphic, 'base'):
                if hasattr(graphic.base, 'socket_type'):
                    item_socket_type = graphic.base.socket_type

            if item == self.get_parent():
                connection_fail = 'Same node'

            if self.base.data_type != item.data_type:

                if self.base.socket_type == SocketType.IN and not self.base.data_type == rigs.AttrType.ANY:
                    connection_fail = 'Different Type'

                if hasattr(item, 'socket_type'):
                    if item.socket_type == SocketType.IN and not item.data_type == rigs.AttrType.ANY:
                        connection_fail = 'Different Type'

        if connection_fail:
            self.base.remove_line(self.new_line)
            self.new_line = None
            util.warning('Cannot connect sockets: %s' % connection_fail)
            return True

        if not item:
            self.base.remove_line(self.new_line)
            self.new_line = None
            return True

        socket_type = self.base.socket_type

        if item == self.new_line or not item_socket_type:
            self.base.remove_line(self.new_line)
            self.new_line = None
            return True
        if socket_type == item_socket_type:
            self.base.remove_line(self.new_line)
            self.new_line = None
            return True
        if socket_type == SocketType.OUT and item_socket_type == SocketType.IN:
            self.new_line.source = self.base
            self.new_line.target = item
            self.new_line.graphic.point_b = item.graphic.get_center()

        elif socket_type == SocketType.OUT and item_socket_type == SocketType.TOP:
            self.new_line.source = self.base
            self.new_line.target = item
            self.new_line.graphic.point_b = item.graphic.get_center()

        elif socket_type == SocketType.TOP and item_socket_type == SocketType.OUT:
            self.new_line.source = item
            self.new_line.target = self.base
            self.new_line.graphic.point_a = item.graphic.get_center()

        elif socket_type == SocketType.IN and item_socket_type == SocketType.OUT:
            self.new_line.source = item
            self.new_line.target = self.base
            self.new_line.graphic.point_a = item.graphic.get_center()

        else:
            super(NodeSocketItem, self).mouseReleaseEvent(event)

        if self.new_line:
            self.connect_line(item, self.new_line)
        return True

    def remove_existing(self, new_line):
        target_socket = new_line.target
        if target_socket.lines:
            disconnect_socket(target_socket, run_target=False)

    def connect_line(self, socket, new_line):
        self.remove_existing(new_line)

        socket.lines.append(new_line)
        self.scene().node_connect.emit(new_line)

    def get_center(self):
        rect = self.boundingRect()
        center = None
        if self.base.socket_type == SocketType.OUT:
            center = qt.QtCore.QPointF(self.node_width + 14, rect.y() + rect.height() / 2.0)
        if self.base.socket_type == SocketType.IN:
            center = qt.QtCore.QPointF(rect.x() + rect.width() / 2.0, rect.y() + rect.height() / 2.0)
        if self.base.socket_type == SocketType.TOP:
            center = qt.QtCore.QPointF(rect.x() + rect.width() / 2.0, rect.y() + rect.height() / 2.0)

        center = self.mapToScene(center)

        return center

    def get_parent(self):
        return self.base.parent


class NodeSocket(AttributeItem):
    item_type = ItemType.SOCKET

    def __init__(self, socket_type=SocketType.IN, name=None, value=None, data_type=None):
        self.socket_type = socket_type
        self.dirty = True
        self.parent = None
        self.lines = []

        super(NodeSocket, self).__init__()

        self._name = name
        self._value = value
        self._data_type = data_type

        self.graphic = None
        if not qt.is_batch():
            self.graphic = NodeSocketItem(self)

    def check_draw_number(self):
        if not self.graphic:
            return
        line_count = len(self.lines)

        draw = False

        if line_count > 1:
            draw = True

        for line in self.lines:
            line.graphic.draw_number = draw

    def add_line(self, line_item):

        self.lines.append(line_item)

        line_count = len(self.lines)
        line_item.number = line_count

        self.check_draw_number()

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
            self.graphic.scene().removeItem(line_item.graphic)

        self.check_draw_number()


class GraphicLine(qt.QGraphicsPathItem):

    def __init__(self, base, point_a=None, point_b=None):
        self.base = base
        super(GraphicLine, self).__init__()

        self.color = None
        self.number = 0
        self.draw_number = False
        self._point_a = point_a
        self._point_b = point_b
        self.setZValue(0)

        self.brush = qt.QBrush()
        self.brush.setStyle(qt.QtCore.Qt.SolidPattern)
        self.brush.setColor(qt.QColor(200, 200, 200, 255))

        self.pen = qt.QPen()
        self.pen.setStyle(qt.QtCore.Qt.SolidLine)
        self.pen.setWidth(2)
        self.pen.setColor(qt.QColor(200, 200, 200, 255))
        self.setPen(self.pen)

    def mousePressEvent(self, event):
        self.point_b = event.pos()
        return True

    def mouseMoveEvent(self, event):
        self.point_b = event.pos()
        return True

    def mouseReleaseEvent(self, event):

        items = self.scene().items(event.scenePos().toPoint())
        for item in items:
            if hasattr(item, 'item_type'):
                if item.item_type == ItemType.SOCKET:
                    if item.socket_type == SocketType.IN:
                        self.point_b = item.get_center()
                        return

        if hasattr(self.base._target.graphic, 'scene'):
            self.base._target.graphic.scene().node_disconnect.emit(self.base.source, self.base.target)

        self.base._source.remove_line(self)
        return True

    def update_path(self):
        path = qt.QPainterPath()
        path.moveTo(self.point_a)

        distance = util_math.get_distance_2D([self.point_a.x(), self.point_a.y()], [self.point_b.x(), self.point_b.y()])
        if distance == 0:
            distance = .1

        offset_out = .3
        offset_in = .4

        max_distance = 500
        fade = 1
        if distance > max_distance:
            fade = max(0.5, 1 - (util_math.fade_smoothstep(1 - (max_distance / distance))))

        spacing_out = distance * offset_out * fade
        spacing_in = distance * offset_in * fade

        ctrl1 = qt.QtCore.QPointF(self.point_a.x() + spacing_out, self.point_a.y())
        ctrl2 = qt.QtCore.QPointF(self.point_b.x() + -spacing_in, self.point_b.y())

        path.cubicTo(ctrl1, ctrl2, self.point_b)

        self.setPath(path)

    def paint(self, painter, option, widget):

        if hasattr(self, 'color') and self.color:
            lighter = False
            if self.color == qt.QColor(60, 60, 60, 255):
                lighter = True

            if lighter:
                color = self.color.darker(70)
            else:
                color = self.color.lighter(70)
            self.brush.setColor(color)
            self.pen.setColor(color)

        path = self.path()
        painter.setPen(self.pen)
        painter.drawPath(path)

        painter.setBrush(self.brush)
        if self.point_a and self.point_b:
            painter.drawEllipse(self.point_b.x() - 3.0,
                                self.point_b.y() - 3.0,
                                6.0,
                                6.0)

        # draw arrow

        if path.length() < 50:
            return

        point = path.pointAtPercent(0.5)
        point_test = path.pointAtPercent(0.51)

        point_orig = qt.QtCore.QPointF(point.x() + 1.0, point.y())

        point_orig = point_orig - point
        point_test = point_test - point

        dot = point_orig.x() * point_test.x() + point_orig.y() * point_test.y()
        det = point_orig.x() * point_test.y() - point_orig.y() * point_test.x()
        angle = math.atan2(det, dot)

        poly = qt.QPolygonF()
        poly.append(qt.QtCore.QPointF(math.cos(angle) * 0 - math.sin(angle) * -5,
                                      math.sin(angle) * 0 + math.cos(angle) * -5))
        poly.append(qt.QtCore.QPointF(math.cos(angle) * 10 - math.sin(angle) * 0,
                                      math.sin(angle) * 10 + math.cos(angle) * 0))

        poly.append(qt.QtCore.QPointF(math.cos(angle) * 0 - math.sin(angle) * 5,
                                      math.sin(angle) * 0 + math.cos(angle) * 5))

        poly.translate(point.x(), point.y())

        painter.drawPolygon(poly)

        if self.draw_number:

            if hasattr(self, 'color') and self.color:
                color = self.color.lighter(60)
                self.pen.setColor(color)
            painter.setPen(self.pen)
            rect = poly.boundingRect()
            rect.translate(30, 0)
            text_point = rect.bottomLeft()
            painter.drawText(text_point, str(self.number))

    @property
    def point_a(self):
        return self._point_a

    @point_a.setter
    def point_a(self, point):
        self._point_a = point
        self.update_path()

    @property
    def point_b(self):
        return self._point_b

    @point_b.setter
    def point_b(self, point):
        self._point_b = point
        self.update_path()


class NodeLine(object):
    item_type = ItemType.LINE

    def __init__(self, point_a=None, point_b=None):
        self.graphic = None
        self._source = None
        self._target = None
        self._number = 0

        if not qt.is_batch():
            self.graphic = GraphicLine(self, point_a, point_b)

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

    @property
    def number(self):
        return self._number

    @number.setter
    def number(self, value):
        if self.graphic:
            self.graphic.number = value
        self._number = value

    def store(self):
        item_dict = {}

        source = self._source
        target = self._target

        item_dict['type'] = self.item_type

        if source:
            item_dict['source'] = source.get_parent().uuid
            item_dict['source name'] = source.name
        if target:
            item_dict['target'] = target.get_parent().uuid
            item_dict['target name'] = target.name

        return item_dict

    def load(self, item_dict):
        if 'source' not in item_dict:
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

            if not source_socket:
                return

            if not target_socket:
                return

            self._source = source_socket
            self._target = target_socket

            source_socket.lines.append(self)
            target_socket.lines.append(self)

            line_count = len(source_socket.lines)
            self.number = line_count

            if self.graphic:

                center_a = source_socket.graphic.get_center()
                center_b = target_socket.graphic.get_center()

                self.graphic._point_a = center_a
                self.graphic._point_b = center_b

                self.graphic.color = source_socket.graphic.color
                source_socket.check_draw_number()

                self.graphic.update_path()

#--- Nodes


__nodes__ = {}


class GraphicsItem(qt.QGraphicsItem):

    def __init__(self, parent=None, base=None):
        self.base = base
        self.node_width = self._init_node_width()
        self._left_over_space = None
        self._current_socket_pos = None
        self.brush = None
        self.pen_run = None
        self.pen_select = None
        self.pen = None
        self.rect = None
        self._running = False

        super(GraphicsItem, self).__init__(parent)

        self._z_value = 2000

        self.draw_node()

        self.setFlag(qt.QGraphicsItem.ItemIsFocusable)

        self.timer = qt.QtCore.QTimer()

        self.timer.timeout.connect(self._update_running)

    def _init_node_width(self):
        return 150

    def mouseMoveEvent(self, event):
        super(GraphicsItem, self).mouseMoveEvent(event)

        if not self.scene():
            return

        selection = self.scene().selectedItems()
        if len(selection) > 1:
            return True

        for name in self.base._out_sockets:
            socket = self.base._out_sockets[name]
            for line in socket.lines:
                line.graphic.point_a = line.source.graphic.get_center()
                line.graphic.point_b = line.target.graphic.get_center()

        for name in self.base._in_sockets:
            socket = self.base._in_sockets[name]
            for line in socket.lines:
                line.graphic.point_a = line.source.graphic.get_center()
                line.graphic.point_b = line.target.graphic.get_center()

        return True

    def draw_node(self):

        self._left_over_space = 0
        self._current_socket_pos = 0

        self.rect = qt.QtCore.QRect(0, 0, self.node_width, 40)
        self.setFlag(qt.QGraphicsItem.ItemIsMovable)
        self.setFlag(qt.QGraphicsItem.ItemIsSelectable)

        # Brush.
        self.brush = qt.QBrush()
        self.brush.setStyle(qt.QtCore.Qt.SolidPattern)

        self.brush.setColor(qt.QColor(*self.base._init_color()))

        self.node_text_pen = qt.QPen()
        self.node_text_pen.setStyle(qt.QtCore.Qt.SolidLine)
        self.node_text_pen.setWidth(1)
        self.node_text_pen.setColor(qt.QColor(255, 255, 255, 255))

        # Pen.
        self.pen = qt.QPen()
        self.pen.setStyle(qt.QtCore.Qt.SolidLine)
        self.pen.setWidth(2)
        self.pen.setColor(qt.QColor(120, 120, 120, 255))

        self.pen_select = qt.QPen()
        self.pen_select.setStyle(qt.QtCore.Qt.SolidLine)
        self.pen_select.setWidth(3)
        self.pen_select.setColor(qt.QColor(255, 255, 255, 255))

        self.pen_run = qt.QPen()
        self.pen_run.setStyle(qt.QtCore.Qt.SolidLine)
        self.pen_run.setWidth(6)
        self.pen_run.setColor(qt.QColor(0, 255, 0, 100))

    def boundingRect(self):
        return qt.QtCore.QRectF(self.rect)

    def paint(self, painter, option, widget):
        painter.setBrush(self.brush)
        painter.setPen(self.node_text_pen)
        painter.drawText(35, -5, self.base.name)

        pen = self.pen

        if self._running:
            pen = self.pen_run
        elif self.isSelected():
            pen = self.pen_select

        painter.setPen(pen)
        painter.drawRoundedRect(self.rect, 5, 5)

    def contextMenuEvent(self, event):
        # self._build_context_menu(event)
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
            self.add_top_socket('parent', '', None)

        if selected_action == add_in_socket:
            self.add_in_socket('goo', '', None)

        if selected_action == add_out_socket:
            self.add_out_socket('foo', '', None)

    def _update_running(self):
        if self._running:
            self._running = False
            self.update()
            self.timer.stop()

    def add_space(self, item, offset=0):

        y_value = 0
        offset_y_value = 0

        if self._left_over_space:
            y_value += self._left_over_space

            self._left_over_space = 0

        # if item.item_type == ItemType.PROXY:
        #    offset_y_value += 4

        y_value = self._current_socket_pos + offset + offset_y_value

        self.rect = qt.QtCore.QRect(0, 0, self.node_width, y_value + 35)
        item.setY(y_value)

        y_value += 18

        self._current_socket_pos = y_value
        self._left_over_space = offset

        item.setZValue(self._z_value)
        self._z_value -= 1

    def set_running(self, bool_value):
        if bool_value == True:
            self._running = bool_value

            self.update()

        else:
            self.timer.start(50)


class NodeItem(object):
    item_type = ItemType.NODE
    item_name = 'Node'
    path = ''

    def __init__(self, name='', uuid_value=None, rig=None):
        self.uuid = None
        self._current_socket_pos = None
        self._dirty = None
        self.orig_position = [0, 0]

        self._color = self._init_color()

        self.graphic = None
        if not qt.is_batch():
            self.graphic = GraphicsItem(base=self)
            self.graphic.node_width = self._init_node_width()

        super(NodeItem, self).__init__()

        self.rig = self._init_rig_class_instance()
        self._init_uuid(uuid_value)
        self._dirty = True
        self._signal_eval_targets = False

        if name:
            self.name = name
        else:
            self.name = self.item_name

        self._widgets = []
        self._in_sockets = {}
        self._in_socket_widgets = {}
        self._out_sockets = {}
        self._sockets = {}
        self._dependency = {}

        # if self.graphic:
        self._build_items()

        __nodes__[self.uuid] = self

    def __getattribute__(self, item):
        dirty = object.__getattribute__(self, '_dirty')

        if item == 'run':
            if not dirty:
                return lambda *args: None

        return object.__getattribute__(self, item)

    def _init_uuid(self, uuid_value):

        if self.uuid in uuids:
            uuids.pop(self.uuid)

        if uuid_value:
            self.uuid = uuid_value
        else:
            self.uuid = str(uuid.uuid4())

        uuids[self.uuid] = self

    def _init_rig_class_instance(self):
        return rigs.Base()

    def _init_color(self):
        return [68, 68, 68, 255]

    def _init_node_width(self):
        return 150

    def _dirty_run(self, attr_name=None, value=None):

        self.dirty = True
        if hasattr(self, 'rig'):
            self.rig.dirty = True
        for out_name in self._out_sockets:
            out_sockets = self.get_outputs(out_name)
            for out_socket in out_sockets:
                out_node = out_socket.get_parent()
                if in_unreal:
                    out_node.set_socket(out_name, value, False)

                else:
                    out_node.dirty = True
                    out_node.rig.dirty = True

        if value != None:
            socket = self.get_socket(attr_name)
            socket.value = value

        self._signal_eval_targets = True
        self.run(attr_name)
        self._signal_eval_targets = False

    def _in_widget_run(self, attr_name, attr_value=None, widget=None):
        if not widget:
            widget = self.get_widget(attr_name)

        if attr_value:
            self._set_widget_socket(attr_name, attr_value, widget)
        else:
            self._set_widget_socket(attr_name, widget.value, widget)

        self._dirty_run(attr_name, attr_value)

    def _set_widget_socket(self, name, value, widget):
        # util.show('\tSet widget socket %s %s' % (name, value))
        socket = self.get_socket(name)

        if not socket:
            return
        if value == None or value == []:
            return

        socket.value = value
        if widget:
            widget.value = value

    def _disconnect_lines(self):
        other_sockets = {}

        for name in self._in_sockets:
            socket = self._in_sockets[name]
            if not hasattr(socket, 'lines'):
                continue
            for line in socket.lines:
                line.target = None

                if line.source not in other_sockets:
                    other_sockets[line.source] = []

                other_sockets[line.source].append(line)

                self.graphic.scene().removeItem(line.graphic)

            socket.lines = []

        for name in self._out_sockets:
            socket = self._out_sockets[name]
            if not hasattr(socket, 'lines'):
                continue

            for line in socket.lines:
                line.source = None

                if line.target not in other_sockets:
                    other_sockets[line.target] = []

                other_sockets[line.target].append(line)

                self.graphic.scene().removeItem(line.graphic)

            socket.lines = []

        for socket in other_sockets:
            lines = other_sockets[socket]

            for line in lines:
                if line in socket.lines:
                    socket.lines.remove(line)

    def _build_items(self):
        return

    def _add_space(self, item, offset=0):
        if not self.graphic:
            return

        if hasattr(item, 'graphic'):
            item = item.graphic

        self.graphic.add_space(item, offset)

    def _implement_run(self):
        return

    @property
    def dirty(self):
        return self._dirty

    @dirty.setter
    def dirty(self, bool_value):
        self._dirty = bool_value

    def add_top_socket(self, name, value, data_type):

        socket = NodeSocket('top', name, value, data_type)
        socket.set_parent(self)

        if not self.rig.attr.exists(name):
            self.rig.attr.add_in(name, value, data_type)

        self._in_sockets[name] = socket

        return socket

    def add_in_socket(self, name, value, data_type):
        socket = NodeSocket('in', name, value, data_type)
        socket.set_parent(self)

        if self.graphic:
            self._add_space(socket)
            current_space = self.graphic._current_socket_pos

        widget = None

        if data_type == rigs.AttrType.STRING:
            if self.graphic:
                self.graphic._current_socket_pos -= 18
            widget = self.add_string(name)

        if data_type == rigs.AttrType.COLOR:
            if self.graphic:
                self.graphic._current_socket_pos -= 30
            widget = self.add_color_picker(name)

        if data_type == rigs.AttrType.INT:
            if self.graphic:
                self.graphic._current_socket_pos -= 17
            widget = self.add_int(name)

        if data_type == rigs.AttrType.NUMBER:
            if self.graphic:
                self.graphic._current_socket_pos -= 17
            widget = self.add_number(name)

        if data_type == rigs.AttrType.VECTOR:
            if self.graphic:
                self.graphic._current_socket_pos -= 17
            widget = self.add_vector(name)

        if widget:
            widget.value = value
            self._in_socket_widgets[name] = widget

            if self.graphic:
                widget.graphic.changed.connect(self._in_widget_run)

        if self.graphic:
            self.graphic._current_socket_pos = current_space

        if not self.rig.attr.exists(name):
            self.rig.attr.add_in(name, value, data_type)

        self._in_sockets[name] = socket

        return socket

    def add_out_socket(self, name, value, data_type):

        socket = NodeSocket('out', name, value, data_type)
        socket.set_parent(self)

        if self.graphic:
            self._add_space(socket)

        if not self.rig.attr.exists(name):
            self.rig.attr.add_out(name, value, data_type)

        self._out_sockets[name] = socket

        return socket

    def add_item(self, name, item_inst=None, track=True):

        attribute = AttributeItem(item_inst)
        attribute.name = name
        attribute.set_parent(self)

        if track:
            self._widgets.append(attribute)
            self._sockets[name] = attribute
        return attribute

    def add_bool(self, name):
        widget = None
        if self.graphic:
            widget = BoolGraphicItem(self.graphic)

        attribute_item = self.add_item(name, widget)

        self._add_space(widget, 2)

        return attribute_item

    def add_int(self, name):
        widget = None
        if self.graphic:

            widget = IntGraphicItem(self.graphic, 50)

        attribute_item = self.add_item(name, widget)

        self._add_space(widget, 4)

        return attribute_item

    def add_number(self, name):
        widget = None
        if self.graphic:
            widget = NumberGraphicItem(self.graphic)

        attribute_item = self.add_item(name, widget)

        self._add_space(widget)

        return attribute_item

    def add_vector(self, name):
        widget = None
        if self.graphic:
            widget = VectorGraphicItem(self.graphic, 105)

        attribute_item = self.add_item(name, widget)

        self._add_space(widget)

        return attribute_item

    def add_string(self, name):
        widget = None

        if self.graphic:
            rect = self.graphic.boundingRect()
            width = rect.width()
            widget = StringItem(self.graphic, width - 20)

        attribute_item = self.add_item(name, widget)

        self._add_space(widget)

        return attribute_item

    def add_color_picker(self, name, width=40, height=14):
        widget = None
        if self.graphic:
            widget = ColorPickerItem(self.graphic, width, height)

        attribute_item = self.add_item(name, widget)

        self._add_space(widget)

        return attribute_item

    def add_title(self, name):
        widget = None
        if self.graphic:
            widget = TitleItem(self.graphic)

        attribute_item = self.add_item(name, widget, track=False)
        self._add_space(widget, 3)

        return attribute_item

    def delete(self):

        self._disconnect_lines()

        if self.graphic:
            if not self.graphic.scene():
                return
            self.graphic.scene().removeItem(self.graphic)

    def get_widget(self, name):

        for widget in self._widgets:
            if widget.name == name:
                return widget

    def get_widgets(self):
        return self._widgets

    def set_socket(self, name, value, run=False):
        socket = self.get_socket(name)

        if not socket:
            return

        socket.value = value

        widget = self.get_widget(name)
        if widget:
            widget.value = value

        if run:
            self.dirty = True
            self.rig.dirty = True
            self.run()

        if in_unreal:
            if self.rig.has_rig_util():
                self.rig.set_attr(name, value)

    def has_socket(self, name):
        sockets = self.get_all_sockets()
        if name in sockets:
            return True
        return False

    def has_in_socket(self, name):
        if name in self._in_sockets:
            return True
        return False

    def has_out_socket(self, name):
        if name in self._out_sockets:
            return True
        return False

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
        if not name in self._in_sockets:
            return found

        socket_inst = self._in_sockets[name]
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

    def get_input_connected_nodes(self):
        found = []
        for name in self._in_sockets:
            socket = self._in_sockets[name]
            for line in socket.lines:
                found.append(line.source.get_parent())

        return found

    def get_output_connected_nodes(self):
        found = []
        for name in self._out_sockets:
            socket = self._out_sockets[name]
            for line in socket.lines:
                found.append(line.target.get_parent())

        return found

    def run_inputs(self):
        if self.rig.has_rig_util() and in_unreal:
            return

        sockets = self._in_sockets

        if sockets:
            if 'Eval In' in sockets:
                self.run_connnection('Eval In')
                sockets.pop('Eval In')
            for socket_name in sockets:
                self.run_connection(socket_name)

    def run_outputs(self):

        if self.rig.has_rig_util() and in_unreal:
            return

        sockets = self._out_sockets

        if sockets:
            if self.has_socket('Eval Out'):
                self.run_connnection('Eval Out')
            for socket_name in sockets:
                if socket_name == 'Eval Out':
                    continue
                self.run_connection(socket_name)

    def run_connection(self, socket_name, send_output=True):
        input_sockets = self.get_inputs(socket_name)
        output_sockets = self.get_outputs(socket_name)

        if in_unreal:
            if is_rig(self):
                output_sockets = []

        sockets = input_sockets + output_sockets
        for socket in sockets:
            if not socket:
                continue
            input_node = socket.get_parent()
            if input_node.dirty:
                input_node.run(send_output=send_output)

            value = socket.value
            if hasattr(self, 'rig'):
                self.load_rig()
                self.rig.attr.set(socket_name, value)

            current_socket = self.get_socket(socket_name)
            current_socket.value = value

    def run(self, socket=None, send_output=True):

        run_inputs = True
        run_outputs = True
        if self.rig.has_rig_util() and in_unreal:
            run_inputs = False
            run_outputs = False

        self.dirty = False

        if self.graphic:
            self.graphic.set_running(True)

        if run_inputs:
            self.run_inputs()

        self._implement_run(socket)
        if self.graphic:
            self.graphic.set_running(False)

        if send_output:
            if run_outputs:
                self.run_outputs()

        if socket:
            util.show('\tDone: %s.%s' % (self.__class__.__name__, socket), self.uuid)
        else:
            util.show('\tDone: %s' % self.__class__.__name__, self.uuid)

    def store(self):

        if self.graphic:
            position = [self.graphic.pos().x(), self.graphic.pos().y()]
        else:
            position = self.orig_position

        item_dict = {'name': self.item_name,
                     'uuid': self.uuid,
                     'type': self.item_type,
                     'position': position,
                     'widget_value': {}}
        for widget in self._widgets:
            name = widget.name
            value = widget.value

            data_type = widget.data_type

            item_dict['widget_value'][name] = {'value': value,
                                               'data_type': data_type}

        return item_dict

    def load(self, item_dict):

        self.name = item_dict['name']
        self._init_uuid(item_dict['uuid'])
        self.rig.uuid = self.uuid

        util.show('Load Node: %s    %s' % (self.name, self.uuid))
        position = item_dict['position']
        self.orig_position = position

        if self.graphic:
            self.graphic.setPos(qt.QtCore.QPointF(position[0], position[1]))

        for widget_name in item_dict['widget_value']:
            value = item_dict['widget_value'][widget_name]['value']
            widget = self.get_widget(widget_name)

            self._set_widget_socket(widget_name, value, widget)

    def load_rig(self):
        return


class ColorItem(NodeItem):
    item_type = ItemType.COLOR
    item_name = 'Color'
    path = 'data'

    def _build_items(self):

        picker = self.add_color_picker('color value', 50, 30)
        picker.data_type = rigs.AttrType.COLOR
        self.picker = picker

        if picker.graphic:
            picker.graphic.changed.connect(self._color_changed)

        self.add_out_socket('color', None, rigs.AttrType.COLOR)

    def _color_changed(self, name, color):

        self.color = color
        self.value = color
        self.picker.value = color

        self._dirty_run()

    def _implement_run(self, socket=None):
        socket = self.get_socket('color')
        if hasattr(self, 'color') and self.color:
            socket.value = self.color
        else:
            socket.value = self.picker.value

        update_socket_value(socket, eval_targets=self._signal_eval_targets)


class CurveShapeItem(NodeItem):
    item_type = ItemType.CURVE_SHAPE
    item_name = 'Curve Shape'
    path = 'data'

    def _init_node_width(self):
        return 180

    def _build_items(self):
        self._current_socket_pos = 10
        shapes = rigs_maya.Control.get_shapes()

        shapes.insert(0, 'Default')
        self.add_title('Maya')

        maya_widget = self.add_string('Maya')
        maya_widget.data_type = rigs.AttrType.STRING
        self._maya_curve_entry_widget = maya_widget

        if maya_widget.graphic:
            maya_widget.graphic.set_completion_examples(shapes[:-1])
            maya_widget.graphic.set_placeholder('Maya Curve Name')

            maya_widget.graphic.changed.connect(self._dirty_run)

        unreal_items = unreal_lib.core.get_unreal_control_shapes()

        self.add_title('Unreal')
        unreal_widget = self.add_string('Unreal')
        unreal_widget.data_type = rigs.AttrType.STRING
        self._unreal_curve_entry_widget = unreal_widget

        if unreal_widget.graphic:
            unreal_widget.graphic.set_completion_examples(unreal_items)
            unreal_widget.graphic.changed.connect(self._dirty_run)

        self.add_out_socket('curve_shape', [], rigs.AttrType.STRING)

    def _implement_run(self, socket=None):

        curve = None

        if in_maya:
            curve = self._maya_curve_entry_widget.value
        if in_unreal:
            curve = self._unreal_curve_entry_widget.value

        if curve:
            socket = self.get_socket('curve_shape')
            socket.value = curve

            update_socket_value(socket, eval_targets=self._signal_eval_targets)


class PlatformVectorItem(NodeItem):
    item_type = ItemType.PLATFORM_VECTOR
    item_name = 'Platform Vector'
    path = 'data'

    def _init_node_width(self):
        return 180

    def _build_items(self):
        self._current_socket_pos = 10

        self.add_title('Maya')

        self.add_in_socket('Maya Vector', [[0.0, 0.0, 0.0]], rigs.AttrType.VECTOR)

        self.add_title('Unreal')
        self.add_in_socket('Unreal Vector', [[0.0, 0.0, 0.0]], rigs.AttrType.VECTOR)

        self.add_title('Output')
        self.add_out_socket('Vector', [], rigs.AttrType.VECTOR)

    def _implement_run(self, socket=None):

        if in_maya:
            socket = self.get_socket('Maya Vector')

        if in_unreal:
            socket = self.get_socket('Unreal Vector')

        out = self.get_socket('Vector')
        out.value = socket.value
        update_socket_value(out, eval_targets=self._signal_eval_targets)


class TransformVectorItem(NodeItem):
    item_type = ItemType.TRANSFORM_VECTOR
    item_name = 'Transform Vector'
    path = 'data'

    def _init_node_width(self):
        return 180

    def _build_items(self):
        self._current_socket_pos = 10

        self.add_title('Maya')

        t_v = self.add_in_socket('Maya Translate', [[0.0, 0.0, 0.0]], rigs.AttrType.VECTOR)
        r_v = self.add_in_socket('Maya Rotate', [[0.0, 0.0, 0.0]], rigs.AttrType.VECTOR)
        s_v = self.add_in_socket('Maya Scale', [[1.0, 1.0, 1.0]], rigs.AttrType.VECTOR)

        self.add_title('Unreal')
        u_t_v = self.add_in_socket('Unreal Translate', [[0.0, 0.0, 0.0]], rigs.AttrType.VECTOR)
        u_r_v = self.add_in_socket('Unreal Rotate', [[0.0, 0.0, 0.0]], rigs.AttrType.VECTOR)
        u_s_v = self.add_in_socket('Unreal Scale', [[1.0, 1.0, 1.0]], rigs.AttrType.VECTOR)

        self.add_title('Output')

        self.add_out_socket('Translate', [], rigs.AttrType.VECTOR)
        self.add_out_socket('Rotate', [], rigs.AttrType.VECTOR)
        self.add_out_socket('Scale', [], rigs.AttrType.VECTOR)

    def _implement_run(self, socket=None):

        sockets = []

        parts = ['Translate', 'Rotate', 'Scale']

        out_dict = {'Translate':self.get_socket('Translate'),
                    'Rotate':self.get_socket('Rotate'),
                    'Scale':self.get_socket('Scale')}

        if not socket:

            for part in parts:
                if in_unreal:
                    platform_socket = 'Unreal ' + part
                else:
                    platform_socket = 'Maya ' + part
                sockets.append((part, platform_socket))

        if socket:
            for part in parts:
                if socket.find(part) > -1:
                    if in_unreal:
                        platform_socket = 'Unreal ' + part
                    else:
                        platform_socket = 'Maya ' + part
                    sockets.append((part, platform_socket))
                    break

        for part_socket in sockets:
            part = part_socket[0]
            platform_socket = part_socket[1]

            out = out_dict[part]
            out.value = self.get_socket(platform_socket).value
            update_socket_value(out, eval_targets=self._signal_eval_targets)


class JointsItem(NodeItem):
    item_type = ItemType.JOINTS
    item_name = 'Joints'
    path = 'data'

    def _build_items(self):

        # self.add_in_socket('Scope', [], rigs.AttrType.TRANSFORM)
        self._current_socket_pos = 10
        line_edit = self.add_string('joint filter')
        if self.graphic:
            line_edit.graphic.set_placeholder('Joint Search')
            line_edit.graphic.changed.connect(self._dirty_run)
        line_edit.data_type = rigs.AttrType.STRING
        self.add_out_socket('joints', [], rigs.AttrType.TRANSFORM)
        # self.add_socket(socket_type, data_type, name)

        self._joint_entry_widget = line_edit

    def _get_joints(self):
        filter_text = self.get_socket_value('joint filter')
        joints = util_ramen.get_joints(filter_text[0])
        return joints

    def _implement_run(self, socket=None):

        joints = self._get_joints()
        if joints is None:
            joints = []

        util.show('\tFound: %s' % joints)

        socket = self.get_socket('joints')
        socket.value = joints

        update_socket_value(socket, eval_targets=self._signal_eval_targets)


class ImportDataItem(NodeItem):
    item_type = ItemType.DATA
    item_name = 'Import Data'
    path = 'data'

    def _build_items(self):

        line_edit = self.add_string('data name')

        line_edit.data_type = rigs.AttrType.STRING
        self.add_in_socket('Eval IN', [], rigs.AttrType.EVALUATION)
        self.add_bool('Clear Current Data')

        self.add_out_socket('result', [], rigs.AttrType.STRING)
        self.add_out_socket('Eval OUT', [], rigs.AttrType.EVALUATION)

        self._data_entry_widget = line_edit

        if line_edit.graphic:
            line_edit.graphic.set_placeholder('Data Name')
            line_edit.graphic.changed.connect(self._dirty_run)

    def _implement_run(self, socket=None):

        new_scene_widget = self._sockets['Clear Current Data']
        if new_scene_widget.value:
            if in_maya:
                cmds.file(new=True, f=True)
            if in_unreal:
                unreal_lib.graph.reset_current_control_rig()

        process_inst = process.get_current_process_instance()
        result = process_inst.import_data(self._data_entry_widget.value[0],
                                          sub_folder=None)
        """
        if result is None:
            result = []

        socket = self.get_socket('result')
        socket.value = result

        # update_socket_value(socket, eval_targets=self._signal_eval_targets)
        """
        # return result


class PrintItem(NodeItem):
    item_type = ItemType.PRINT
    item_name = 'Print'
    path = 'utility'

    def _build_items(self):
        self.add_in_socket('input', [], rigs.AttrType.ANY)

    def _implement_run(self, socket=None):

        socket = self.get_socket('input')
        util.show('Ramen Print: %s' % socket.value)


class RigItem(NodeItem):
    item_type = ItemType.RIG
    path = 'rig'

    def __init__(self, name='', uuid_value=None):

        self._temp_parents = {}
        super(RigItem, self).__init__(name, uuid_value)

        self.rig_state = None
        # self.rig.load()

        # self.run()

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

        self._dependency.update(self.rig.get_attr_dependency())

        for attr_name in attribute_names:

            if attr_name in items:

                value, attr_type = self.rig.get_node_attribute(attr_name)
                widget = None

                if attr_type == rigs.AttrType.TITLE:
                    title = self.add_title(attr_name)
                    title.data_type = attr_type

                if attr_type == rigs.AttrType.STRING:
                    widget = self.add_string(attr_name)

                if attr_type == rigs.AttrType.BOOL:
                    widget = self.add_bool(attr_name)

                if attr_type == rigs.AttrType.INT:
                    widget = self.add_int(attr_name)

                if attr_type == rigs.AttrType.NUMBER:
                    widget = self.add_number(attr_name)

                if attr_type == rigs.AttrType.VECTOR:
                    widget = self.add_vector(attr_name)

                if widget:
                    widget.data_type = attr_type
                    widget.value = value

                    if widget.graphic:
                        widget.graphic.changed.connect(self._dirty_run)

            if attr_name in ins:
                value, attr_type = self.rig.get_in(attr_name)

                if attr_name == 'parent':
                    self.add_top_socket(attr_name, value, attr_type)
                else:
                    self.add_in_socket(attr_name, value, attr_type)

        for attr_name in outs:
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
            self.rig.attr.set(node_socket.name, value)

        if isinstance(socket, str):
            socket = sockets[socket]

        if socket:
            self.dirty = True
            self.rig.dirty = True
            update_socket_value(socket, update_rig=True)
        else:

            self.rig.create()

            if in_unreal:
                return

            for name in self._out_sockets:
                out_socket = self._out_sockets[name]
                value = self.rig.attr.get(name)
                out_socket.value = value

    def _unparent(self):
        if in_unreal:
            return

        nodes = self.get_output_connected_nodes()
        for node in nodes:
            self._temp_parents[node.uuid] = node

            node.rig.parent = []

    def _reparent(self):
        if in_unreal:
            pass

        if not self._temp_parents:
            return

        if self.rig.attr.exists('controls'):
            controls = self.rig.get_attr('controls')
            if controls:
                for uuid in self._temp_parents:
                    node = self._temp_parents[uuid]
                    node.rig.parent = controls

    def _custom_run(self):
        # this is used when a rig doesn't have a rig_util. Meaning it doesn't require a custom node/set in the DCC package
        return

    def _implement_run(self, socket=None):

        if in_unreal:
            unreal_lib.graph.open_undo('Node Run')

        if not self.rig.rig_util:
            # no rig util associated with the rig. Try running _custom_run
            self._custom_run()

        self._unparent()
        self._run(socket)
        self._reparent()

        if in_maya:
            if self.rig.attr.exists('controls'):
                value = self.rig.attr.get('controls')
                outputs = self.get_outputs('controls')
                for output in outputs:
                    output.value = value

        self.update_position()

        if in_unreal:

            # self._remove_unreal_evaluation()

            self._handle_unreal_connections()
            # handle_unreal_evaluation(nodes)

            unreal_lib.graph.close_undo('Node Run')

    def _handle_unreal_connections(self):
        unreal_rig = self.rig.rig_util
        if not unreal_rig:
            return

        self._disconnect_unreal()

        sockets = self.get_all_sockets()

        for socket_name in sockets:
            self._connect_unreal_inputs(socket_name)
            self._connect_unreal_outputs(socket_name)

    def _connect_unreal_inputs(self, name):
        inputs = self.get_inputs(name)

        for in_socket in inputs:
            socket = self.get_socket(name)
            self._connect_unreal(in_socket, socket)

    def _connect_unreal_outputs(self, name):
        if name == 'Eval OUT':
            return
        outputs = self.get_outputs(name)

        for out_socket in outputs:
            socket = self.get_socket(name)
            self._connect_unreal(socket, out_socket)

    def _connect_unreal(self, source_socket, target_socket):

        node = source_socket.get_parent()

        if not is_rig(node):
            return

        name = source_socket.name

        in_node = target_socket.get_parent()
        in_name = target_socket.name

        if not hasattr(node.rig, 'rig_util'):
            util.warning('No source rig util')
            return
        unreal_rig = node.rig.rig_util
        if not unreal_rig:
            util.warning('Source rig util equals None')
            return

        if not hasattr(in_node.rig, 'rig_util'):
            util.warning('No target rig util')
            return
        in_unreal_rig = in_node.rig.rig_util
        if not in_unreal_rig:
            util.warning('Target rig util equals None')
            return

        unreal_rig.load()
        in_unreal_rig.load()

        if unreal_rig.construct_node and in_unreal_rig.construct_node:
            construct_node = unreal_rig.construct_node
            construct_in = in_unreal_rig.construct_node

            node_pairs = [[construct_node, construct_in]]

            constructs = [in_unreal_rig.construct_controller]

            for pair, construct in zip(node_pairs, constructs):
                node_unreal, in_node_unreal = pair

                unreal_lib.graph.add_link(node_unreal, name,
                                          in_node_unreal, in_name,
                                          construct)

    def _disconnect_unreal(self):

        self.rig.rig_util.remove_connections()

    def update_position(self):
        if not self.graphic:
            return

        if in_unreal:
            if self.rig.has_rig_util():
                self.rig.load()

            if not self.rig.is_valid():
                return

            offset = 0
            spacing = 2
            position = [0, 0]
            if self.graphic:
                position = [self.graphic.pos().x(), self.graphic.pos().y()]
            else:
                position = self.orig_position
            self.rig.rig_util.set_node_position((position[0] - offset) * spacing, (position[1] - offset) * spacing)

    def run_inputs(self):
        self.load_rig()
        super(RigItem, self).run_inputs()

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

    def load_rig(self):
        if self.rig.is_valid():
            return

        self.rig.load()

        self.rig.uuid = self.uuid
        if in_maya:

            if self.rig.attr.exists('controls'):
                value = self.rig.attr.get('controls')
                if value:
                    self.dirty = False
                    self.rig.dirty = False

                    self.set_socket('controls', value, run=False)
            else:
                self.dirty = False
                self.rig.dirty = False


class GetTransform(RigItem):
    item_type = ItemType.GET_TRANSFORM
    item_name = 'Get Transform'
    path = 'data'

    def _custom_run(self, socket=None):
        data = self.get_socket('transforms').value

        if data:
            index = self.get_socket_value('index')[0]
            data_at_index = data[index]
        else:
            data_at_index = None

        util.show('Found: %s' % data_at_index)
        socket = self.get_socket('transform')
        socket.value = data_at_index

        update_socket_value(socket, eval_targets=self._signal_eval_targets)

    def _init_rig_class_instance(self):
        return rigs_crossplatform.GetTransform()


class GetSubControls(RigItem):
    item_type = ItemType.GET_SUB_CONTROLS
    item_name = 'Get Sub Controls'
    path = 'data'

    def _custom_run(self, socket=None):
        controls = self.get_socket('controls').value

        if controls:
            control_index = self.get_socket_value('control_index')[0]
            sub_controls = util_ramen.get_sub_controls(controls[control_index])
        else:
            sub_controls = None

        util.show('Found: %s' % sub_controls)
        socket = self.get_socket('sub_controls')
        socket.value = sub_controls

        update_socket_value(socket, eval_targets=self._signal_eval_targets)

    def _init_rig_class_instance(self):
        return rigs_crossplatform.GetSubControls()


class FkItem(RigItem):
    item_type = ItemType.FKRIG
    item_name = 'FkRig'

    def _init_color(self):
        return [80, 80, 80, 255]

    def _init_rig_class_instance(self):
        return rigs_crossplatform.Fk()


class IkItem(RigItem):
    item_type = ItemType.IKRIG
    item_name = 'IkRig'

    def _init_color(self):
        return [80, 80, 80, 255]

    def _init_rig_class_instance(self):
        return rigs_crossplatform.Ik()


class SplineIkItem(RigItem):
    item_type = ItemType.SPLINEIKRIG
    item_name = 'SplineIkRig'

    def _init_color(self):
        return [80, 80, 80, 255]

    def _init_rig_class_instance(self):
        return rigs_crossplatform.SplineIk()


class WheelItem(RigItem):
    item_type = ItemType.WHEELRIG
    item_name = 'WheelRig'

    def _init_color(self):
        return [80, 80, 80, 255]

    def _init_rig_class_instance(self):
        return rigs_crossplatform.Wheel()

#--- registry


register_item = {
    # NodeItem.item_type : NodeItem,
    FkItem.item_type: FkItem,
    IkItem.item_type: IkItem,
    SplineIkItem.item_type: SplineIkItem,
    JointsItem.item_type: JointsItem,
    ColorItem.item_type: ColorItem,
    CurveShapeItem.item_type: CurveShapeItem,
    ImportDataItem.item_type: ImportDataItem,
    PrintItem.item_type: PrintItem,
    GetTransform.item_type: GetTransform,
    GetSubControls.item_type: GetSubControls,
    TransformVectorItem.item_type: TransformVectorItem,
    PlatformVectorItem.item_type:PlatformVectorItem,
    WheelItem.item_type: WheelItem
}


def update_socket_value(socket, update_rig=False, eval_targets=False):
    if in_unreal:
        unreal_lib.graph.open_undo('update socket')
        eval_targets = False
    # TODO break apart it smaller functions
    source_node = socket.get_parent()
    uuid = source_node.uuid

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

    outputs = source_node.get_outputs(socket.name)
    target_nodes = []
    for output in outputs:

        target_node = output.get_parent()
        if target_node not in target_nodes:
            target_nodes.append(target_node)

        run = False

        target_node.set_socket(output.name, value, run)

    socket.dirty = False

    if eval_targets:
        for target_node in target_nodes:

            util.show('\tRun target %s' % target_node.uuid)
            target_node.dirty = True

            target_node.run()

    if in_unreal:
        unreal_lib.graph.close_undo('update socket')
        # unreal_lib.graph.compile_control_rig()


def connect_socket(source_socket, target_socket, run_target=True):

    source_node = source_socket.get_parent()
    target_node = target_socket.get_parent()

    util.show('Connect socket %s.%s into %s.%s' % (source_node.name,
                                                   source_socket.name, target_node.name, target_socket.name))

    if in_unreal:
        unreal_lib.graph.open_undo('Connect')

        run_target = False

        nodes = get_nodes()
        handle_unreal_evaluation(nodes)

        if is_rig(source_node) and is_rig(target_node):
            if source_socket._data_type == rigs.AttrType.TRANSFORM and target_socket._data_type == rigs.AttrType.TRANSFORM:
                if target_node.rig.rig_util.construct_node is None:
                    target_node.rig.rig_util.load()
                    target_node.rig.rig_util.build()
                if source_node.rig.rig_util.construct_node is None:
                    source_node.rig.rig_util.load()
                    source_node.rig.rig_util.build()

                if source_node.rig.rig_util.construct_controller:
                    source_node.rig.rig_util.construct_controller.add_link('%s.%s' % (source_node.rig.rig_util.construct_node.get_node_path(), source_socket.name),
                                                                           '%s.%s' % (target_node.rig.rig_util.construct_node.get_node_path(), target_socket.name))
    else:
        target_node.dirty = True

    if source_node.dirty:
        source_node.run(source_socket.name)

    value = source_socket.value

    target_node.set_socket(target_socket.name, value, run=run_target)

    if in_unreal:
        unreal_lib.graph.close_undo('Connect')


def disconnect_socket(target_socket, run_target=True):
    # TODO break apart into smaller functions
    node = target_socket.get_parent()
    util.show('Disconnect socket %s.%s %s' % (node.name, target_socket.name, node.uuid))

    node = target_socket.get_parent()

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

    if in_unreal:
        run_target = False

        source_node = source_socket.get_parent()
        target_node = target_socket.get_parent()

        if is_rig(source_node) and is_rig(target_node):
            if target_socket._data_type == rigs.AttrType.TRANSFORM:

                if target_node.rig.rig_util.construct_node is None:
                    target_node.rig.rig_util.load()
                    target_node.rig.rig_util.build()

                if source_node.rig.rig_util.construct_node is None:
                    source_node.rig.rig_util.load()
                if source_node.rig.rig_util.construct_controller:

                    source_node.rig.rig_util.construct_controller.break_link('%s.%s' % (source_node.rig.rig_util.construct_node.get_node_path(), source_socket.name),
                                                                             '%s.%s' % (target_node.rig.rig_util.construct_node.get_node_path(), target_socket.name))

                target_node = target_socket.get_parent()
                nodes = get_nodes()
                target_node = target_socket.get_parent()
                handle_unreal_evaluation(nodes)

    target_socket.remove_line(target_socket.lines[0])

    if target_socket.data_type == rigs.AttrType.TRANSFORM:
        node.set_socket(target_socket.name, None, run=run_target)

    # if in_unreal:
    #    unreal_lib.graph.compile_control_rig()


def get_nodes():
    return __nodes__.values()


def is_registered(node):

    if hasattr(node, 'item_type'):
        if node.item_type in register_item:
            return True
    if not hasattr(node, 'base'):
        return False
    if node.base.item_type in register_item:
        return True

    return False


def is_rig(node):
    if issubclass(node.__class__, RigItem):
        return True
    return False


def get_base(nodes):
    nodes = [node.base for node in nodes if hasattr(node, 'base')]

    return nodes


def filter_nonregistered(nodes):
    found = list(filter(is_registered, nodes))

    return found


def filter_rigs(nodes):
    found = list(filter(is_rig, nodes))
    return found


def remove_unreal_evaluation(nodes):
    nodes = filter_nonregistered(nodes)
    for node in nodes:
        if not node.rig.has_rig_util():
            continue
        node.rig.load()
        if not node.rig.state == rigs.RigState.CREATED:
            continue

        for controller in node.rig.rig_util.get_controllers():
            node_name = node.rig.rig_util.name()
            try:
                controller.break_all_links('%s.ExecuteContext' % node_name, True)
                controller.break_all_links('%s.ExecuteContext' % node_name, False)
            except:
                util.warning('Unable to deal with Execute Context')


def remove_unreal_connections(nodes):
    for node in nodes:

        node.rig.rig_util.remove_connections()


def add_unreal_evaluation(nodes):
    last_node = None
    for node in nodes:
        if not node.rig.rig_util.is_built():
            node.rig.load()
            if not node.rig.state == rigs.RigState.CREATED:
                node.rig.create()
            if not node.rig.state == rigs.RigState.CREATED:
                continue
        controllers = node.rig.rig_util.get_controllers()
        start_nodes = node.rig.rig_util.get_graph_start_nodes()
        name = node.rig.rig_util.name()

        for controller, start_node in zip(controllers, start_nodes):

            source_node = last_node
            if not last_node:
                source_node = start_node

            unreal_lib.graph.add_link(source_node, 'ExecuteContext', name, 'ExecuteContext', controller)
        last_node = name


def handle_unreal_evaluation(nodes):
    unreal_lib.graph.open_undo('handle_eval')
    nodes = filter_nonregistered(nodes)

    remove_unreal_evaluation(nodes)

    start_tip_nodes = []
    start_nodes = []

    mid_nodes = []
    end_nodes = []
    disconnected_nodes = []

    for node in nodes:
        if node.rig.has_rig_util():
            node.rig.load()

        inputs = node.get_input_connected_nodes()
        outputs = node.get_output_connected_nodes()

        if not inputs and not outputs:
            disconnected_nodes.append(node)
            continue
        if inputs and outputs:
            mid_nodes.append(node)
            continue
        if not inputs:
            has_ancestor_input = False
            for output_node in outputs:
                sub_inputs = output_node.get_input_connected_nodes()
                if sub_inputs:
                    has_ancestor_input = True
                    break
            if has_ancestor_input:
                start_nodes.append(node)
            else:
                start_tip_nodes.append(node)
        if not outputs:
            parent_inputs = node.get_inputs('parent')
            if not parent_inputs:
                disconnected_nodes.append(node)
            else:
                end_nodes.append(node)

    disconnected_nodes = list(filter(lambda x:x.rig.has_rig_util(), disconnected_nodes))

    start_nodes = list(filter(lambda x:x.rig.has_rig_util(), start_nodes))
    nodes_in_order = []
    nodes_in_order += disconnected_nodes
    nodes_in_order += start_nodes

    if len(mid_nodes) > 1:
        mid_nodes = post_order(end_nodes, mid_nodes)

    mid_nodes.reverse()

    nodes_in_order += mid_nodes
    nodes_in_order += end_nodes

    add_unreal_evaluation(nodes_in_order)
    unreal_lib.graph.close_undo('handle_eval')


def post_order(end_nodes, filter_nodes):
    node_set = set(filter_nodes)
    results = []
    visited = set()

    def traverse(node):
        if node is None or node in visited:
            if node in node_set:
                results.remove(node)
            else:
                return
        visited.add(node)
        if node in node_set:
            results.append(node)
        parents = node.get_input_connected_nodes()

        for parent in parents:
            traverse(parent)

    for end_node in end_nodes:
        traverse(end_node)

    return results


def pre_order(start_nodes, filter_nodes):
    node_set = set(filter_nodes)
    results = []
    visited = set()

    def traverse(node):
        if node is None or node in visited:
            return
        visited.add(node)
        if node in node_set:
            results.append(node)
        children = node.get_output_connected_nodes()

        for child in children:
            traverse(child)

    for start_node in start_nodes:
        traverse(start_node)

    return results


def update_node_positions(nodes):

    nodes = filter_rigs(nodes)

    if not nodes:
        return

    for node in nodes:
        node.update_position()


def transfer_values(source_item, target_item):

        widgets = source_item.get_widgets()

        for widget in widgets:
            attr_name = widget.name
            if attr_name == 'joints':
                continue
            current_value = widget.value

            target_item.set_socket(attr_name, current_value)

