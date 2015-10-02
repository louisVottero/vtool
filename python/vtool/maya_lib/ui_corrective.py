# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

from vtool import qt_ui

import ui
import util
import corrective
import vtool.util

import maya.cmds as cmds
import maya.mel as mel

if qt_ui.is_pyqt():
    from PyQt4 import QtGui, QtCore, Qt, uic
if qt_ui.is_pyside():
    from PySide import QtCore, QtGui

class PoseManager(ui.MayaWindow):
    
    title = 'Correctives'
    
    def _define_main_layout(self):
        layout = QtGui.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)
        return layout
        
    def _build_widgets(self):
        
        self.pose_set = PoseSetWidget()
        self.pose_list = PoseListWidget()
        
        self.sculpt = SculptWidget()
        self.sculpt.setMaximumHeight(200)
        
        self.pose_list.set_pose_widget(self.sculpt)
        
        self.sculpt.sculpted_mesh.connect(self.pose_list.update_current_pose)
        self.pose_list.pose_list_refresh.connect(self.sculpt.mesh_widget.update_meshes)
        self.pose_list.pose_list.itemSelectionChanged.connect(self.select_pose)
        self.pose_list.pose_renamed.connect(self._pose_renamed)
        self.pose_list.pose_deleted.connect(self._pose_deleted)
        self.pose_list.pose_list.check_for_mesh.connect(self.check_for_mesh)
        self.pose_set.pose_reset.connect(self.pose_list.pose_reset)
        self.sculpt.pose_mirror.connect(self.pose_list.mirror_pose)
        
        self.main_layout.addWidget(self.pose_set)
        self.main_layout.addWidget(self.pose_list)
        self.main_layout.addWidget(self.sculpt)
        
    def _pose_renamed(self, new_name):
        
        new_name = str(new_name)
        self.sculpt.set_pose(new_name)
        self.pose_list.update_current_pose()
        
    def _pose_deleted(self):
        
        self.sculpt.set_pose(None)
        
    def select_pose(self):
        
        self.pose_list.pose_list.select_pose()
        
        items = self.pose_list.pose_list.selectedItems()
        
        if items:
            pose_name = items[0].text(0)
        
        if not items:
            return    
        
        pose_name = str(pose_name)
        self.sculpt.set_pose(pose_name)
        
        cmds.select(pose_name, r = True)
        
        #pose_control_widget = self.pose_list.pose_widget.pose_control_widget
        
        #if type(pose_control_widget) == PoseConeWidget:
        #    pose_control_widget._get_pose_values()
        
    def check_for_mesh(self, pose):
        
        selection = cmds.ls(sl = True)
        
        self.sculpt.set_pose(pose)
        self.sculpt.mesh_widget.add_mesh(selection)
        
class PoseSetWidget(QtGui.QWidget): 
    
    pose_reset = qt_ui.create_signal()
    
    def __init__(self):
        
        super(PoseSetWidget, self).__init__()
        
        self.main_layout = QtGui.QHBoxLayout()
        self.setLayout(self.main_layout)
        self.main_layout.setAlignment(QtCore.Qt.AlignTop)
            
        self._add_buttons()
        
        self.pose = None
        
    def _add_buttons(self):
        
        button_default = QtGui.QPushButton('Set Default Pose')
        button_reset = QtGui.QPushButton('To Default Pose')
        
        button_reset.clicked.connect(self._button_reset)
        button_default.clicked.connect(self._button_default)
        
        self.main_layout.addWidget(button_reset)
        self.main_layout.addWidget(button_default)
        
    def _button_default(self):
        corrective.PoseManager().set_default_pose()
    
    def _button_reset(self):
        self.pose_reset.emit()
        corrective.PoseManager().set_pose_to_default()
        
class PoseListWidget(qt_ui.BasicWidget):
    
    pose_added = qt_ui.create_signal(object)
    pose_renamed = qt_ui.create_signal(object)
    pose_deleted = qt_ui.create_signal()
    pose_update = qt_ui.create_signal(object)
    pose_list_refresh = qt_ui.create_signal()
    
    def __init__(self):
        super(PoseListWidget, self).__init__()
        
        self.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
             
    def _define_main_layout(self):
        layout = QtGui.QVBoxLayout()
        return layout
        
    def _build_widgets(self):
        
        self.pose_list = PoseTreeWidget()
        
        self.pose_list.list_refresh.connect(self.pose_list_refresh.emit)
        
        self.pose_list.itemSelectionChanged.connect(self._update_pose_widget)
        
        self.pose_widget = PoseWidget()
        self.pose_widget.hide()
        
        self.pose_list.pose_renamed.connect(self._pose_renamed)
        self.pose_list.pose_deleted.connect(self._pose_deleted)
        
        self.filter_names = QtGui.QLineEdit()
        self.filter_names.setPlaceholderText('filter names')

        self.filter_names.textChanged.connect(self._filter_names)
        
        self.main_layout.addWidget(self.pose_list)
        self.main_layout.addWidget(self.filter_names)
        self.main_layout.addWidget(self.pose_widget)
    
    def _filter_names(self, text):
        
        self.pose_list.filter_names(text)
        self.skip_name_filter = False

    def _set_sub_pose_weight(self, pose, weight_value):
        
        manager = corrective.PoseManager()
        manager.set_pose_group(pose)
        sub_poses = manager.get_poses()
        
        for sub_pose in sub_poses:
            self._set_sub_pose_weight(sub_pose, weight_value)
            
            weight_attribute = '%s.weight' % sub_pose
            
            if cmds.objExists(weight_attribute):
                try:    
                    cmds.setAttr(weight_attribute, weight_value)
                except:
                    pass

    def _update_pose_widget(self):
       
        current_pose = self.pose_list._current_pose()
        current_weight_attribute = '%s.weight' % current_pose
        
        items = self.pose_list.selectedItems()
        
        if items:
            self.pose_widget.show()
            self.pose_widget.set_pose(current_pose)
            
        if not items:
            self.pose_widget.hide()
            
        self.pose_update.emit(current_pose)
        
        item_count = self.pose_list.topLevelItemCount()
        
        auto_key_state = cmds.autoKeyframe(q = True, state = True)
        cmds.autoKeyframe(state = False)
        
        for inc in range(0, item_count):
            
            inc_pose_name = self.pose_list.topLevelItem(inc).text(0)    
            
            inc_pose_attribute = '%s.weight' % inc_pose_name
            
            if inc_pose_name == current_pose:
                
                if cmds.objExists(current_weight_attribute):
                    
                    try:
                        self._set_sub_pose_weight(current_pose, 0)    
                        cmds.setAttr(current_weight_attribute, 1)
                    except:
                        pass
                    
                continue

            if cmds.objExists(inc_pose_attribute):
                
                try:
                    self._set_sub_pose_weight(inc_pose_name, 0)
                    cmds.setAttr(inc_pose_attribute, 0)
                except:
                    pass
                    #vtool.util.warning('Could not set %s to 0.' % current_weight_attribute )

        cmds.autoKeyframe(state = auto_key_state)
        
        
                
    def _pose_renamed(self, new_name):
        self.pose_renamed.emit(new_name)
        
    def _pose_deleted(self):
        self.pose_deleted.emit()

    def update_current_pose(self):
        
        current_pose = self.pose_list._current_pose()
        self.pose_widget.set_pose(current_pose)
        
    def set_pose_widget(self, widget):
        self.pose_list.pose_widget = widget
        
    def create_pose(self):
        self.pose_list.create_pose()
        
    def delete_pose(self):
        self.pose_list.delete_pose()

    def mirror_pose(self):
        self.pose_list.mirror_pose()
        
    def add_mesh(self):
        self.pose_list.add_mesh()
        self.select(self.pose)
        
    def view_mesh(self):
        self.pose_list.view_mesh()
        
    def change_mesh(self, int):
        self.pose_list.mesh_change(int)
        
    def change_axis(self, string):
        
        self.pose_list.axis_change(string)
        
    def pose_reset(self):
        item = self.pose_list.currentItem()
        
        if item:
            item.setSelected(False)
        
    def value_changed(self, max_angle, max_distance, twist_on, twist):
        
        self.pose_list.value_changed(max_angle, max_distance, twist_on, twist)
        
    def parent_changed(self, parent):
        
        self.pose_list.parent_changed(parent)
        
    def pose_enable_changed(self, value):
        self.pose_list.pose_enable_changed(value)
    
class BaseTreeWidget(qt_ui.TreeWidget):

    list_refresh = qt_ui.create_signal()
    pose_deleted = qt_ui.create_signal()
    pose_renamed = qt_ui.create_signal(object)
    
    def __init__(self):
        
        self.edit_state = False
        super(BaseTreeWidget, self).__init__()
        self.setSortingEnabled(True)
        self.setSelectionMode(self.SingleSelection)
        
        ui.new_scene_signal.signal.connect(self.refresh)
        
        self.text_edit = False
        
        self._populate_list()
        
        self.pose_widget = None

    def _populate_list(self):
        self.clear()
        self.list_refresh.emit()
        
    def _current_pose(self):
        selected = self.selectedItems()
        
        item = None
        
        if selected:
            item = selected[0]
            
        if item:
            return str(item.text(0))

    def _get_selected_items(self, get_names = False):
        selected = self.selectedIndexes()
        
        items = []
        names = []
        
        for index in selected:
            
            item = self.itemFromIndex(index)
            
            if not get_names:
                items.append(item)
            if get_names:
                name = str( item.text(0) )
                names.append(name)

        if not get_names:
            return items
        if get_names:
            return names

    def _rename_pose(self):
        
        items = self.selectedItems()
        
        item = None
        
        if items:
            item = items[0]
            
        if not items:
            return
        
        self.old_name = item.text(0)
        
        new_name = qt_ui.get_new_name('Please specify a name.', self, old_name = self.old_name)
                
        item.setText(0, new_name)
        
        state = self._item_rename_valid(self.old_name, item)
        
        if state:
            self._item_renamed(item)
        if not state:
            item.setText(0, self.old_name)
            
        self.pose_renamed.emit(item.text(0))
        self.resizeColumnToContents(0)
        
    def _item_renamed(self, item):    
        
        new_name = item.text(0)
        
        new_name = corrective.PoseManager().rename_pose(str(self.old_name), str(new_name))
        
        item.setText(0, new_name)
    
    def refresh(self):
        self._populate_list()
      
    """  
    def mesh_change(self, index):
        
        pose_name = self._current_pose()
        
        if not pose_name:
            return
        
        pose = corrective.PoseCone()
        pose.set_pose(pose_name)
    """ 
    def _remove_current_item(self):
        
        item = self.currentItem()
        
        parent_item = item.parent()
        
        if not parent_item:
            parent_item = self.invisibleRootItem()    
        
        index = parent_item.indexOfChild(item)
        item = parent_item.takeChild(index)
        
        
        del(item)
        
    def delete_pose(self):
        
        permission = qt_ui.get_permission('Delete Pose?', self)
        
        if not permission:
            return
        
        pose = self._current_pose()
        
        if not pose:
            return
        
        corrective.PoseManager().delete_pose(pose)
        
        self._remove_current_item()
        
        self.last_selection = None
        
        self.pose_deleted.emit()
    
    def parent_changed(self, parent):
        
        pose_name = self._current_pose()
        
        if not pose_name:
            return
        
        pose = corrective.PoseCone()
        pose.set_pose(pose_name)
        
        pose.set_parent(parent)
        
    def pose_enable_changed(self, value):
        
        pose_name = self._current_pose()
        
        if not pose_name:
            return
        
        cmds.setAttr('%s.enable' % pose_name, value)
        
class PoseTreeWidget(BaseTreeWidget):
    
    check_for_mesh = qt_ui.create_signal(object)

    def __init__(self):
        
        
        self.item_context = []
        self.context_menu_item = None
        
        super(PoseTreeWidget, self).__init__()
        
        self.setDragDropMode(self.InternalMove)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)  
        
        self.setAutoScroll(True)
        
        
        self.setHeaderLabels(['pose', 'type'])
       
        self.header().setStretchLastSection(False)
        self.header().setResizeMode(0, self.header().Stretch)
        
        self.last_selection = []
    
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._item_menu)
        
        self._create_context_menu()
        
        self.update_select = True
        self.item_select = True
        
    def mousePressEvent(self, event):
        
        model_index =  self.indexAt(event.pos())
        
        item = self.itemAt(event.pos())
        
        parent = self.invisibleRootItem()
        
        if item:
            item_parent = item.parent()
            
            if item_parent:
                parent = item_parent
        
        self.drag_parent = parent
        self.dragged_item = item
        
        if not item or model_index.column() == 1:
            self.clearSelection()
            
        
        if event.button() == QtCore.Qt.RightButton:
            return
        
        if model_index.column() == 0 and item:
            super(PoseTreeWidget, self).mousePressEvent(event)
    
    def dropEvent(self, event):
        
        position = event.pos()
        entered_item = self.itemAt(position)
        index = self.indexAt(position)
        
        is_dropped = True
        
        if event.source == self and event.dropAction() == QtCore.Qt.MoveAction or self.dragDropMode() == QtGui.QAbstractItemView.InternalMove:
            topIndex = QtCore.QModelIndex()
            col = -1
            row = -1
            l = [event, row, col, topIndex]

            if self.drop_on(l):
                event, row, col, topIndex = l
                
                print index.row(), row
                
                if row > -1:
                    if row == index.row():
                        is_dropped = False
                if row == -1 or row == (index.row() + 1):
                    is_dropped = True
        
        super(PoseTreeWidget, self).dropEvent(event)

        print 'drop', is_dropped

        if not is_dropped:
            if entered_item:
                
                if entered_item.parent():
                    parent_item = entered_item.parent()
                    
                if not entered_item.parent():
                    parent_item = self.invisibleRootItem()
                    
                if not self.drag_parent is parent_item:
                    
                    index = entered_item.indexOfChild(self.dragged_item)
                    child = entered_item.takeChild(index)
                    parent_item.addChild(child)
                    
                    entered_item = parent_item
        
        if entered_item:
            entered_item.setExpanded(True)
        self.dragged_item.setDisabled(True)
            
        if entered_item is self.drag_parent:
            self.dragged_item.setDisabled(False)
            return
            
        result = qt_ui.get_permission('Parent item %s?' % self.dragged_item.text(0), self)
        
        if not result:
            entered_item.removeChild(self.dragged_item)
            
            index = entered_item.indexOfChild(self.dragged_item)
            child = entered_item.takeChild(index)
            
            self.drag_parent.addChild(child)
            self.dragged_item.setDisabled(True)
            return      
        
        if result:
            
            pose_parent = 'pose_gr'
            
            pose = self.dragged_item.text(0)
            
            current_parent = cmds.listRelatives(pose, p = True)
            
            #print entered_item.text(0)
            
            if entered_item:
                pose_parent = entered_item.text(0)
            if entered_item is self.invisibleRootItem():
                pose_parent = 'pose_gr'
            
            if current_parent:
                
                current_parent = current_parent[0]
                
                if pose_parent != current_parent:
                    if pose_parent:
                        cmds.parent(pose, pose_parent)
            
            self.dragged_item.setDisabled(False)
    
    def _item_menu(self, position):
                
        item = self.itemAt(position)
        
        self.context_menu_item = item
        
        self._create_pose_options_context()
        
        if item:
            for item in self.item_context:
                
                item.setVisible(True)
            
        if not item:
            for item in self.item_context:
                
                item.setVisible(False)
        
        self.context_menu.exec_(self.viewport().mapToGlobal(position))
        
    def _create_context_menu(self):
        
        self.context_menu = QtGui.QMenu()
        self.context_menu.setTearOffEnabled(True)
        
        self.create_cone = self.context_menu.addAction('New Cone')
        self.create_no_reader = self.context_menu.addAction('New No Reader')
        self.create_timeline = self.context_menu.addAction('New Timeline')
        
        self.item_context = []
        
        #self.create_rbf = pose_menu.addAction('RBF')
        self.context_menu.addSeparator()
        
        self.rename_action = self.context_menu.addAction('Rename')
        self.delete_action = self.context_menu.addAction('Delete')
        self.context_menu.addSeparator()
        self.option_menu = self.context_menu.addMenu('Options')
        #self._create_pose_options_context()
        self.context_menu.addSeparator()
        self.set_pose_action = self.context_menu.addAction('Update Pose')
        self.reset_sculpts_action = self.context_menu.addAction('Reset Sculpt')
        self.context_menu.addSeparator()
        self.refresh_action = self.context_menu.addAction('Refresh')
        
        self.item_context = self.item_context + [self.rename_action, 
                                                 self.delete_action,
                                                 self.reset_sculpts_action,
                                                 self.set_pose_action]
        
        self.create_cone.triggered.connect(self.create_cone_pose)
        self.create_no_reader.triggered.connect(self.create_no_reader_pose)
        self.create_timeline.triggered.connect(self.create_timeline_pose)
        
        self.rename_action.triggered.connect(self._rename_pose)
        self.delete_action.triggered.connect(self.delete_pose)
        self.set_pose_action.triggered.connect(self._set_pose_data)
        self.reset_sculpts_action.triggered.connect(self._reset_sculpts)
        
        self.refresh_action.triggered.connect(self._populate_list)

    def _create_pose_options_context(self):
        
        self.option_menu.clear()
        
        if not self.context_menu_item:
            self.option_menu.setDisabled(True)
        
        if self.context_menu_item:
            
            self.option_menu.setDisabled(False)
            
            self.select_pose_action = self.option_menu.addAction('Select Pose')
            self.select_blend_action = self.option_menu.addAction('Select Blendshape')
        
            self.select_pose_action.triggered.connect(self._select_pose)
            self.select_blend_action.triggered.connect(self._select_blend)
            
            pose = self.context_menu_item.text(0)
            
            if cmds.objExists('%s.type' % pose):
                pose_type = cmds.getAttr('%s.type' % pose)
                
                if pose_type == 'cone':
                    self._create_cone_context_menu()
        
        
    def _create_base_context_menu(self):
        pass
    
    def _create_cone_context_menu(self):
        self.select_joint_action = self.option_menu.addAction('Select Joint')
        self.select_joint_action.triggered.connect(self._select_joint)
        
    def _create_no_reader_context_menu(self):
        pass
    
    def _add_item(self, pose, parent):
        
        item = QtGui.QTreeWidgetItem(parent)
        item.setSizeHint(0, QtCore.QSize(100, 26))
        item.setText(0, pose)
        
        if cmds.objExists('%s.type' % pose):
            type_name = cmds.getAttr('%s.type' % pose)
            item.setText(1, type_name)
        
        self.addTopLevelItem(item)
        
        return item
        
    def _populate_list(self):
        
        super(PoseTreeWidget, self)._populate_list()   
        
        if not cmds.objExists('pose_gr'):
            return
        
        poses = corrective.PoseManager().get_poses()
        
        if not poses:
            return
        
        self.item_select = False
        
        for pose in poses:
            
            cmds.select(cl = True)
            
            pose_item = self._add_pose_item(pose)
        
            sub_manager = corrective.PoseManager()
            sub_manager.set_pose_group(pose)
            
            sub_poses = sub_manager.get_poses()
            
            if not sub_poses:
                continue
            
            for sub_pose in sub_poses:
                self._add_pose_item(sub_pose, pose_item)
               
        self.item_select = True
               
    def _add_pose_item(self, pose_name, parent = None):
         
        if cmds.objExists('%s.type' % pose_name):
            pose_type = cmds.getAttr('%s.type' % pose_name)
        
        if not cmds.objExists('%s.type' % pose_name):
            pose_type = 'cone'
        
        new_item = self.create_pose(pose_type, pose_name, parent)
        
        return new_item 
                      
    def _select_joint(self):
        name = self._current_pose()
        transform = corrective.PoseManager().get_transform(name)
        
        util.show_channel_box()
        
        cmds.select(transform)
        
    def _select_pose(self):
        
        name = self._current_pose()
        
        control = corrective.PoseManager().get_pose_control(name)
        
        util.show_channel_box()
        
        cmds.select(control)

    def _set_pose_data(self):
        
        name = self._current_pose()
        control = corrective.PoseManager().get_pose_control(name)
        corrective.PoseManager().set_pose_data(control)

    def _reset_sculpts(self):
        
        name = self._current_pose()
        corrective.PoseManager().reset_pose(name)
        
    def _select_blend(self):
        
        name = self._current_pose()
        
        if not name:
            return
        
        pose_inst = corrective.PoseCone()
        pose_inst.set_pose(name)
        
        blend = pose_inst.get_blendshape()
        
        util.show_channel_box()
           
        cmds.select(blend, r = True)
        
    def create_pose(self, pose_type, name = None, parent = None):
        
        selection = cmds.ls(sl = True, l = True)
        
        pose = None
        
        if name:
            pose = name
        
        if not pose:
            pose = corrective.PoseManager().create_pose(pose_type, name)
        
        if not pose:
            return
        
        if selection:
            
            cmds.select(selection, r = True)
                
            self.check_for_mesh.emit(pose)
            
        item = self._add_item(pose, parent)
        
        self.update_select = False
        if self.item_select:
            item.setSelected(True)
        self.update_select = True
        
        return item
    
    def create_cone_pose(self):
        self.create_pose('cone', None, None)
    
    def create_no_reader_pose(self):
        self.create_pose('no reader', None, None)
        
    def create_timeline_pose(self):
        self.create_pose('timeline', None, None)
    
    def mirror_pose(self):
        
        pose = self._current_pose()
        
        if not pose:
            return
        
        mirror = corrective.PoseManager().mirror_pose(pose)
        self.refresh()
        
        self.select_pose(mirror)
        
    def select_pose(self, pose_name = None):
                
        if not self.update_select:
            return
                
        if pose_name:
            for inc in range(0, self.topLevelItemCount()):
                
                if pose_name ==  str(self.topLevelItem(inc).text(0)):
                    self.topLevelItem(inc).setSelected(True)
                    
                    auto_key_state = cmds.autoKeyframe(q = True, state = True)
                    cmds.autoKeyframe(state = False)
                    
                    try:
                        cmds.setAttr('%s.weight' % pose_name, 1)
                    except:
                        pass
                    
                    cmds.autoKeyframe(state = auto_key_state)
        
        items = self.selectedItems()
        
        if not items:
            return
        
        if self.last_selection:
            if cmds.objExists(self.last_selection[0]): 
                corrective.PoseManager().visibility_off(self.last_selection[0])

        pose_names = self._get_selected_items(get_names = True)
        
        if pose_names:
            if not cmds.objExists(pose_names[0]):
                self._remove_current_item()
            
            if cmds.objExists(pose_names[0]):
                
                corrective.PoseManager().set_pose(pose_names[0])
                
        self.last_selection = pose_names
        
class PoseWidget(qt_ui.BasicWidget):

    def __init__(self):
        super(PoseWidget, self).__init__()
        
        self.pose_name = None
        self.pose_control_widget = None
        
        self.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
    
    def _define_main_layout(self):
        layout = QtGui.QHBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignRight)
        return layout
    
    def set_pose(self, pose_name):
        
        if not pose_name:
            return
        
        self.pose_name = pose_name
        
        if cmds.objExists('%s.type' % pose_name):
            pose_type = cmds.getAttr('%s.type' % pose_name)
        if not cmds.objExists('%s.type' % pose_name):
            pose_type = 'cone'
        
        if self.pose_control_widget:
            self.pose_control_widget.close()
            self.pose_control_widget.deleteLater()
            del self.pose_control_widget
            self.pose_control_widget = None
        
        
        if pose_type == 'no reader':
            self.pose_control_widget = PoseNoReaderWidget()
            
        if pose_type == 'cone':
            
            self.pose_control_widget = PoseConeWidget()
            
        if pose_type == 'timeline':
            self.pose_control_widget = PoseTimelineWidget()
        
        self.pose_control_widget.set_pose(pose_name)
        
        self.main_layout.addWidget(self.pose_control_widget)
        
    def set_pose_parent_name(self, parent_name):

        if not parent_name:
            parent_name = ''
        
        self.pose_control_widget.set_parent_name(parent_name)
        
    def set_pose_enable(self, value):
        self.pose_control_widget.set_pose_enable(value)
        
    def get_current_mesh(self):
        return self.mesh_widget.get_current_mesh()


class MeshWidget(qt_ui.BasicWidget):
    
    mesh_change = qt_ui.create_signal(object)
    
    def __init__(self):
        super(MeshWidget, self).__init__()
        
        self.pose_name = None
        self.pose_class = None
        
        self.mesh_list.setSelectionMode(self.mesh_list.ExtendedSelection)
        
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._item_menu)
        
        self._create_context_menu()
        
        self.handle_selection_change = True
        
    def sizeHint(self):    
        return QtCore.QSize(200,100)
    
    def _item_menu(self, position):
        
        self.context_menu.exec_(self.mesh_list.viewport().mapToGlobal(position))
        
    def _create_context_menu(self):
        
        self.context_menu = QtGui.QMenu()
        
        remove = self.context_menu.addAction('Remove')
                
        remove.triggered.connect(self.remove_mesh)
    
    def _build_widgets(self):

        self.mesh_list = QtGui.QListWidget()        
        self.mesh_list.itemSelectionChanged.connect(self._item_selected)
        
        self.main_layout.addWidget(self.mesh_list)

    def _mesh_change(self, int_value):    
        self.mesh_change.emit(int_value)

    def get_current_meshes_in_list(self):
        items = self.mesh_list.selectedItems()
        
        found = []
        
        for item in items:
            found.append( str( item.longname ) )
        
        return found

    def _update_meshes(self, pose_name, meshes = []):
        
        pose = self.pose_class
        
        if not pose or not pose_name:
            return
        
        if not cmds.objExists(pose_name):
            return
        
        pose.set_pose(pose_name)
        
        target_meshes =  pose.get_target_meshes()
        
        self.update_meshes(target_meshes, meshes)
        
    def _is_in_mesh_list(self, mesh):
        
        mesh_list_count = self.mesh_list.count()
        
        for inc in range(0, mesh_list_count):
                    
            test_item = self.mesh_list.item(inc)
            
            if str( test_item.longname ) == mesh:                
                return True
            
        return False
    
    def _get_mesh_from_vertex(self, mesh):
        
        if mesh.find('.vtx') > -1:
            split_selected = mesh.split('.vtx')
            if split_selected > 1:
                mesh = split_selected[0]
                
                return mesh
        
        return mesh
    
    def _get_sculpt_permission(self, sculpt_meshes):
        
        mesh_info = 'mesh'
        sculpt_name = ''
                
        sculpt_count = len(sculpt_meshes)
                
        inc = 0
        
        for sculpt in sculpt_meshes:
            name = util.get_basename(sculpt)
            
            if sculpt_count == 1:
                sculpt_name = name
                continue
            if inc == (sculpt_count-1):
                sculpt_name += '\n%s' % name
                inc+=1
                continue
            if sculpt_count > 1:
                sculpt_name += '\n%s' % name
            
            inc+=1 
        
        if len(sculpt_meshes) > 1:
            mesh_info = 'meshes'
        
        permission = qt_ui.get_permission('Add %s:  %s  ?' % (mesh_info, sculpt_name), self)
        
        return permission        
        
        
    @util.undo_chunk
    def add_mesh(self, selection = None):
        
        if not selection:
            selection = cmds.ls(sl = True, l = True)
        
        if self.pose_class:
            self.pose_class.goto_pose()
        
        current_meshes = self.get_current_meshes_in_list()
        
        if not current_meshes:
            current_meshes = []
        
        missing_meshes = ''
        
        for current_mesh in current_meshes:
            if not current_mesh or not cmds.objExists(current_mesh):
                missing_meshes += '\n%s' % current_mesh
                
        if missing_meshes: 
            qt_ui.warning('Cannot find: %s' % missing_meshes, self)
            
        pose_name = self.pose_name
        
        if not pose_name:
            return
        
        sculpt_meshes = []
        list_meshes = []
        added_meshes = []
        
        if selection:
            
            for selected in selection:
                
                if not util.has_shape_of_type(selected, 'mesh'):
                    continue
                    
                selected = self._get_mesh_from_vertex(selected)
                
                pass_mesh = selected
                
                if cmds.objExists('%s.mesh_pose_source' % selected):
                    source_mesh = cmds.getAttr('%s.mesh_pose_source' % selected)
                    
                    pass_mesh = source_mesh
                    selected = source_mesh
                    
                if self._is_in_mesh_list(selected):
                    pass_mesh = None
                    list_meshes.append(selected)
                    
                if pass_mesh:   
                    sculpt_meshes.append(pass_mesh)
        
        if sculpt_meshes or not current_meshes:
            
            print 'sculpt meshes', sculpt_meshes, 'current', current_meshes
            
            if sculpt_meshes:
                
                sculpt_meshes = vtool.util.convert_to_sequence(sculpt_meshes)
                
                permission = self._get_sculpt_permission(sculpt_meshes)
                
                if not permission:
                    return
                
                corrective.PoseManager().add_mesh_to_pose(pose_name, sculpt_meshes)
        
            update_meshes = current_meshes + sculpt_meshes + added_meshes  
            self._update_meshes(pose_name, meshes = update_meshes)
        
        selection = cmds.ls(sl = True, l = True)
        
        
        if list_meshes:
            
            self.mesh_list.clearSelection()
            
            for mesh in list_meshes:
                
                if not mesh:
                    continue
                
                index = corrective.PoseManager().get_mesh_index(pose_name, mesh)
                
                if index == None:
                    continue
                
                item = self.mesh_list.item(index)
                if item:
                    item.setSelected(True)
                
                corrective.PoseManager().toggle_visibility(index, pose_name)
                
            cmds.select(selection)
            return
        
        if current_meshes:
            
            indices = self.mesh_list.selectedIndexes()
            
            if indices:
                for index in indices:
                    
                    index = index.row()
                
                    corrective.PoseManager().toggle_visibility(index, pose_name)
                    
    def remove_mesh(self):
        
        meshes = self.get_current_meshes_in_list()
        
        if not meshes:
            return
        
        self.pose_class.remove_mesh(meshes[0])
        
        indices = self.mesh_list.selectedIndexes()
        
        if indices:
            index = indices[0].row()
            self.mesh_list.takeItem(index)
        
    def _item_selected(self):
        
        if not self.handle_selection_change:
            return
        
        items = self.mesh_list.selectedItems()
        
        cmds.select(cl = True)
        
        for item in items:
            if cmds.objExists(item.longname):
                cmds.select(item.longname, add = True)
        
    def update_meshes(self, meshes = [], added_meshes = []):
        self.mesh_list.clear()    
        
        #self.handle_selection_change = False
        
        for mesh in meshes:
            
            if not mesh:
                continue
            
            item = QtGui.QListWidgetItem()
            item.setSizeHint(QtCore.QSize(0,20))
            basename = util.get_basename(mesh)
            item.setText(basename)
            item.longname = mesh
            self.mesh_list.addItem(item)
            
            #if mesh in added_meshes:
            item.setSelected(True)
        
        #if not added_meshes:   
            
        #    item = self.mesh_list.item(index)
        #    if item:
        #        item.setSelected(True)
                
        #self.handle_selection_change = True
            
    def set_pose(self, pose_name):
        
        self.pose_name = pose_name
        
        if cmds.objExists('%s.type' % pose_name):
            pose_type = cmds.getAttr('%s.type' % pose_name)
        
        if not cmds.objExists('%s.type' % pose_name):
            pose_type = 'cone'

        self.pose_class = corrective.corrective_type[pose_type]()
        
        self.pose_class.set_pose(pose_name)

        self._update_meshes(pose_name)

class SculptWidget(qt_ui.BasicWidget):
    
    pose_mirror = qt_ui.create_signal()
    sculpted_mesh = qt_ui.create_signal()
    
    def __init__(self):
        super(SculptWidget, self).__init__()
        
        self.pose = None
    
    def sizeHint(self):
        
        return QtCore.QSize(200,200)
        
    def _define_main_layout(self):
        return QtGui.QVBoxLayout()
    
    def _button_sculpt(self):
        
        try:
            
            self.button_sculpt.setDisabled(True)
                       
            self.mesh_widget.add_mesh()
            self.sculpted_mesh.emit()
            
            self.button_sculpt.setEnabled(True)
            
            if self.pose:
                
                auto_key_state = cmds.autoKeyframe(q = True, state = True)
                cmds.autoKeyframe(state = False)
    
                try:
                    cmds.setAttr('%s.weight' % self.pose, 1)
                except:
                    pass
                
                cmds.autoKeyframe(state = auto_key_state)
            
                cmds.select(self.pose)
                
        except:
            self.button_sculpt.setEnabled(True)


    def _button_mirror(self):
        try:
            self.button_mirror.setDisabled(True)
            self.pose_mirror.emit()
            self.button_mirror.setEnabled(True)
        except:
            self.button_mirror.setEnabled(True)
    
    def _build_widgets(self):
        
        self.slider = QtGui.QSlider()
        
        self.slider.setOrientation(QtCore.Qt.Horizontal)
        self.slider.setMaximumHeight(30)
        self.slider.setMinimum(0)
        self.slider.setMaximum(100)
        self.slider.setTickPosition(self.slider.NoTicks)
        
        self.slider.valueChanged.connect(self._pose_enable)
        
        self.button_sculpt = QtGui.QPushButton('Sculpt')
        self.button_sculpt.setMinimumWidth(100)

        button_mirror = QtGui.QPushButton('Mirror')
        button_mirror.setMaximumWidth(100)
        button_mirror.clicked.connect(self._button_mirror)
        
        self.button_mirror = button_mirror
        
        v_layout = QtGui.QHBoxLayout()
        v_layout.addWidget(self.button_sculpt)
        v_layout.addSpacing(5)
        v_layout.addWidget(self.slider)
        v_layout.addSpacing(5)

        self.button_sculpt.clicked.connect(self._button_sculpt)
        
        self.mesh_widget = MeshWidget()

        self.main_layout.addLayout(v_layout)
        
        self.main_layout.addWidget(self.mesh_widget)
        self.main_layout.addWidget(button_mirror)

    def _pose_enable(self, value):
        
        value = value/100.00
        
        if not self.pose:
            return
        
        cmds.setAttr('%s.enable' % self.pose, value)
      
    def set_pose(self, pose_name):
        
        self.mesh_widget.set_pose(pose_name)
        
        if not pose_name:
            self.pose = None
            
            return
        
        self.pose = pose_name
        
        auto_key_state = cmds.autoKeyframe(q = True, state = True)
        cmds.autoKeyframe(state = False)
        
        try:
            cmds.setAttr('%s.weight' % pose_name, 1)
        except:
            pass
        
        cmds.autoKeyframe(state = auto_key_state)

        
        self.set_pose_enable()
        
    def set_pose_enable(self):
        
        value = cmds.getAttr('%s.enable' % self.pose)
        
        value = value*100
        self.slider.setValue(value)
        
#--- pose widgets

class PoseBaseWidget(qt_ui.BasicWidget):
    
    def __init__(self):
        
        super(PoseBaseWidget, self).__init__()
        self.pose = None

        self.do_target_change = True

    
    def _build_widgets(self):
        super(PoseBaseWidget, self)._build_widgets()
        
    def _string_widget(self, name):
        layout = QtGui.QHBoxLayout()
        
        label = QtGui.QLabel(name)
        text = QtGui.QLineEdit()
        
        layout.addWidget(label)
        layout.addWidget(text)
        
        return layout, text
        
    def _add_spin_widget(self, name):
        layout = QtGui.QHBoxLayout()
        layout.setSpacing(1)
        layout.setContentsMargins(0,0,0,0)
        
        label = QtGui.QLabel(name)
        label.setAlignment(QtCore.Qt.AlignRight)
        
        widget = QtGui.QDoubleSpinBox()
        
        widget.setCorrectionMode(widget.CorrectToNearestValue)
        widget.setWrapping(False)
        widget.setButtonSymbols(widget.NoButtons)
        layout.addWidget(label)
        layout.addSpacing(2)
        layout.addWidget(widget)
        
        return layout, widget      

    def set_pose(self, pose_name):
        
        if not pose_name:
            self.pose = None
            return
        
        self.pose = pose_name

class PoseNoReaderWidget(PoseBaseWidget):
    
    def _build_widgets(self):
        super(PoseNoReaderWidget, self)._build_widgets()
        
        layout, widget = self._string_widget('Input')
        
        self.input_text = widget
        
        self.input_text.textChanged.connect(self._input_change)
        
        self.main_layout.addLayout(layout)

    def _get_weight_input(self):
        
        pose_inst = corrective.PoseNoReader()
        pose_inst.set_pose(self.pose)
        input_value = pose_inst.get_input()
        
        self.input_text.setText(input_value)
        
        return input_value
        
    def _input_change(self):
        
        self.input_text.setStyleSheet('QLineEdit{background:red}')
        
        text = str( self.input_text.text() )
        
        if not text:
            
            style = self.styleSheet()
            self.input_text.setStyleSheet(style)
        
        if util.is_attribute_numeric(text):
                        
            style = self.styleSheet()
            self.input_text.setStyleSheet(style)
            
            self.set_input(text)
            
        if not util.is_attribute_numeric(text):
            
            self.set_input(text)
            
    def set_input(self, attribute):
        
        if not self.pose:
            return
        
        pose = corrective.PoseNoReader()
        pose.set_pose(self.pose)
        
        pose.set_input(attribute)
        
    def set_pose(self, pose_name):
        super(PoseNoReaderWidget, self).set_pose(pose_name)
        
        self._get_weight_input()
        
class PoseTimelineWidget(PoseBaseWidget):
    pass

class PoseConeWidget(PoseBaseWidget):
    
    def __init__(self):
        
        super(PoseConeWidget, self).__init__()
        self.value_update_enable = True
        
    def _define_main_layout(self):
        layout = QtGui.QVBoxLayout()
        return layout
        
    def _build_widgets(self):
        super(PoseConeWidget, self)._build_widgets()
        self.combo_label = QtGui.QLabel('Alignment')
        
        self.combo_axis = QtGui.QComboBox()
        self.combo_axis.addItems(['X','Y','Z'])
        
        layout_combo = QtGui.QHBoxLayout()
        
        layout_combo.addWidget(self.combo_label, alignment = QtCore.Qt.AlignRight)
        layout_combo.addWidget(self.combo_axis)
        
        layout_angle, self.max_angle = self._add_spin_widget('Max Angle')
        layout_distance, self.max_distance = self._add_spin_widget('Max Distance')
        layout_twist, self.twist = self._add_spin_widget('Max twist')
        layout_twist_on, self.twist_on = self._add_spin_widget('Twist')
                        
        self.max_angle.setRange(0, 180)
        
        self.twist.setRange(0, 180)
        self.twist_on.setRange(0,1)
        self.max_distance.setMinimum(0)
        self.max_distance.setMaximum(10000000)
        
        parent_combo = QtGui.QHBoxLayout()
        
        parent_label = QtGui.QLabel('Parent')
        self.parent_text = QtGui.QLineEdit()
        
        self.parent_text.textChanged.connect(self._parent_name_change)
        
        parent_combo.addWidget(parent_label, alignment = QtCore.Qt.AlignRight)
        parent_combo.addWidget(self.parent_text)
        
        self.max_angle.valueChanged.connect(self._value_changed)
        self.max_distance.valueChanged.connect(self._value_changed)
        self.twist_on.valueChanged.connect(self._value_changed)
        self.twist.valueChanged.connect(self._value_changed)
        self.combo_axis.currentIndexChanged.connect(self._axis_change)
        
        self.main_layout.addLayout(parent_combo)
        self.main_layout.addLayout(layout_combo)
        self.main_layout.addLayout(layout_angle)
        self.main_layout.addLayout(layout_twist)
        self.main_layout.addLayout(layout_distance)
        self.main_layout.addLayout(layout_twist_on)
        
    def _button_mirror(self):
        self.pose_mirror.emit()

    def _button_mesh(self):
        self.pose_mesh.emit()

        
    def _axis_change(self):
        
        text = str( self.combo_axis.currentText() )
        self.axis_change(text)
        
    def _set_ui_values(self, angle, distance, twist_on, twist):
        
        self.value_update_enable = False
        self.max_angle.setValue(angle)
        self.max_distance.setValue(distance)
        self.twist_on.setValue(twist_on)
        self.twist.setValue(twist)
        self.value_update_enable = True
        
    def _parent_name_change(self):
        
        self.parent_text.setStyleSheet('QLineEdit{background:red}')
        
        text = str( self.parent_text.text() )
        
        if not text:
            
            style = self.styleSheet()
            self.parent_text.setStyleSheet(style)
            
            return
        
        if cmds.objExists(text) and util.is_transform(text):
            
            style = self.styleSheet()
            self.parent_text.setStyleSheet(style)
            
            self.set_parent_name(text)
    
    def _value_changed(self):
        
        
        
        if not self.value_update_enable:
            return
        
        max_angle = self.max_angle.value()
        max_distance = self.max_distance.value()
        twist_on = self.twist_on.value()
        twist = self.twist.value()
        
        self.set_values(max_angle, max_distance, twist_on, twist)
        

    def _pose_enable(self, value):
        
        value = value/100.00
        
        self.pose_enable_change.emit(value)

    def _get_pose_node_values(self):
        
        pose = self.pose
        
        max_angle = cmds.getAttr('%s.maxAngle' % pose)
        max_distance = cmds.getAttr('%s.maxDistance' % pose)
        twist_on = cmds.getAttr('%s.twistOffOn' % pose)
        twist = cmds.getAttr('%s.maxTwist' % pose)
        
        return max_angle, max_distance, twist_on, twist

    def _get_pose_values(self):
        
        pose = self.pose
               
        x = cmds.getAttr("%s.axisRotateX" % pose)
        y = cmds.getAttr("%s.axisRotateY" % pose)
        z = cmds.getAttr("%s.axisRotateZ" % pose)
        
        axis = [x,y,z]
        
        if axis == [1,0,0]:
            self.combo_axis.setCurrentIndex(0)
        if axis == [0,1,0]:
            self.combo_axis.setCurrentIndex(1)
        if axis == [0,0,1]:
            self.combo_axis.setCurrentIndex(2)
        
        max_angle, max_distance, twist_on, twist = self._get_pose_node_values()
        
        self._set_ui_values(max_angle, max_distance, twist_on, twist)
        
        return max_angle, max_distance, twist_on, twist

    def _get_parent(self):
        
        pose_inst = corrective.PoseCone()
        pose_inst.set_pose(self.pose)
        parent = pose_inst.get_parent()
        
        self.set_parent_name(parent)
        
        return parent

    def set_pose(self, pose_name):
        
        super(PoseConeWidget, self).set_pose(pose_name)
        
        if not pose_name:
            self.pose = None
            return
        
        self.pose = pose_name
        self._get_pose_values()
        self._get_parent()
        

    def set_values(self, angle, distance, twist_on, twist):
        
        if not self.pose:
            return
                
        cmds.setAttr('%s.maxAngle' % self.pose, angle)
        cmds.setAttr('%s.maxDistance' % self.pose, distance)
        cmds.setAttr('%s.maxTwist' % self.pose, twist)
        cmds.setAttr('%s.twistOffOn' % self.pose, twist_on)
        
        
    def axis_change(self, string):
        
        if not self.pose:
            return
        
        pose_name = str(self.pose)
        
        pose = corrective.PoseCone()
        pose.set_pose(pose_name)
        pose.set_axis(string)
        
        
    def set_parent_name(self, parent_name):
        
        self.parent_text.setText(parent_name)
        
        if not self.pose:
            return
        
        pose = corrective.PoseCone()
        pose.set_pose(self.pose)
        
        pose.set_parent(parent_name)
        
    def set_pose_enable(self, value):
        value = value*100
        self.slider.setValue(value)
    
class PoseComboWidget(PoseBaseWidget):
    pass