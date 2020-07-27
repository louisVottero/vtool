# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

import traceback

from vtool import qt_ui, qt
from vtool.maya_lib import ui_core
import vtool.util



if vtool.util.is_in_maya():
    import maya.cmds as cmds
    import maya.mel as mel
    from vtool.maya_lib import core
    from vtool.maya_lib import attr
    from vtool.maya_lib import space
    from vtool.maya_lib import corrective
    

class PoseManager(ui_core.MayaWindowMixin):
    
    title = 'Correctives'
    
    def __init__(self, shot_sculpt_only = False):
        self.shot_sculpt_only = shot_sculpt_only
        
        super(PoseManager, self).__init__()
        
        self.setSizePolicy(qt.QSizePolicy.Expanding, qt.QSizePolicy.Expanding)
    
    def _define_main_layout(self):
        layout = qt.QVBoxLayout()
        layout.setAlignment(qt.QtCore.Qt.AlignTop)
        return layout
        
    def _build_widgets(self):
        
        self.pose_set = PoseSetWidget()
        self.pose_list = PoseListWidget(self.shot_sculpt_only)
        
        self.sculpt = SculptWidget()
        self.sculpt.setMaximumHeight(200)
        
        self.pose_list.set_pose_widget(self.sculpt)
        
        self.sculpt.sculpted_mesh.connect(self.pose_list.update_current_pose)
        self.pose_list.pose_list_refresh.connect(self._list_refreshed)
        self.pose_list.pose_list.itemSelectionChanged.connect(self.select_pose)
        self.pose_list.pose_list.itemSelectionChanged.connect(self.pose_list.update_pose_widget)
        self.pose_list.pose_renamed.connect(self._pose_renamed)
        self.pose_list.pose_deleted.connect(self._pose_deleted)
        self.pose_list.pose_list.check_for_mesh.connect(self.check_for_mesh)
        self.pose_set.pose_reset.connect(self.pose_list.pose_reset)
        self.pose_set.poses_mirrored.connect(self.pose_list.mirror_all)
        self.pose_set.poses_reconnect.connect(self.pose_list.reconnect_all)
        self.sculpt.pose_mirror.connect(self.pose_list.mirror_pose)
        
        
        self.sculpt.hide()
        
        self.main_layout.addWidget(self.pose_set)
        self.main_layout.addWidget(self.pose_list)
        self.main_layout.addWidget(self.sculpt)
        
    def _pose_renamed(self, new_name):
        
        new_name = str(new_name)
        self.sculpt.set_pose(new_name)
        self.pose_list.update_current_pose()
        
    def _pose_deleted(self):
        
        self.sculpt.set_pose(None)
        
    def _list_refreshed(self):
        self.sculpt.mesh_widget.update_meshes
        self.pose_list.set_filter_names()
        
    def select_pose(self):
        
        self.pose_list.pose_list.select_pose()
        
        items = self.pose_list.pose_list.selectedItems()
        
        if items:
            pose_name = items[0].text(0)
        
        if not items:
            return    
        
        pose_name = str(pose_name)
        
        pose_type = cmds.getAttr('%s.type' % pose_name)
        
        if pose_type != 'group':
            self.sculpt.set_pose(pose_name)
            self.sculpt.show()
        if pose_type == 'group':
            self.sculpt.hide()
        
        cmds.select(pose_name, r=True)
        
    def check_for_mesh(self, pose):
        
        selection = cmds.ls(sl=True)
        
        self.sculpt.set_pose(pose)
        self.sculpt.mesh_widget.add_mesh(selection)
        
class PoseSetWidget(qt_ui.BasicWidget): 
    
    pose_reset = qt_ui.create_signal()
    poses_mirrored = qt_ui.create_signal()
    poses_reconnect = qt_ui.create_signal()
    
    def __init__(self):
        
        super(PoseSetWidget, self).__init__()
        
        self.main_layout.setAlignment(qt.QtCore.Qt.AlignTop)
        self.main_layout.setContentsMargins(2,2,2,2)
        
        self.pose = None
        
    def _define_main_layout(self):
        return qt.QHBoxLayout()
        
    def _build_widgets(self):
        
        #top_layout = qt.QHBoxLayout()
        button_default = qt.QPushButton('Set Default Pose')
        button_reset = qt.QPushButton('To Default Pose')
        #top_layout.addWidget(button_default)
        #top_layout.addSpacing(5)
        #top_layout.addWidget(button_reset)
        #btm_layout = qt.QHBoxLayout()
        button_mirror_all = qt.QPushButton('Mirror All')
        button_reconnect = qt.QPushButton('Reconnect All')
        #btm_layout.addWidget(button_mirror_all)
        #btm_layout.addSpacing(5)
        #btm_layout.addWidget(button_reconnect)
        
        button_reset.clicked.connect(self._button_reset)
        button_default.clicked.connect(self._button_default)
        button_mirror_all.clicked.connect(self._mirror_all)
        button_reconnect.clicked.connect(self._reconnect_all)
        
        #self.main_layout.addLayout(top_layout)
        #self.main_layout.addLayout(btm_layout)
        
        self.main_layout.addWidget(button_reset)
        self.main_layout.addSpacing(5)
        self.main_layout.addWidget(button_default)
        self.main_layout.addSpacing(15)
        self.main_layout.addWidget(button_mirror_all)
        self.main_layout.addSpacing(5)
        self.main_layout.addWidget(button_reconnect)
        
    def _button_default(self):
        corrective.PoseManager().set_default_pose()
    
    def _button_reset(self):
        self.pose_reset.emit()
        corrective.PoseManager().set_pose_to_default()
        
    def _mirror_all(self):
        
        self.poses_mirrored.emit()
    
    def _reconnect_all(self):
        
        self.poses_reconnect.emit()
        
        
class PoseListWidget(qt_ui.BasicWidget):
    
    pose_added = qt_ui.create_signal(object)
    pose_renamed = qt_ui.create_signal(object)
    pose_deleted = qt_ui.create_signal()
    pose_update = qt_ui.create_signal(object)
    pose_list_refresh = qt_ui.create_signal()
    pose_mirror_all = qt_ui.create_signal()
    
    def __init__(self, shot_sculpt_only):
        self.shot_sculpt_only = shot_sculpt_only
        
        super(PoseListWidget, self).__init__()
        
        self.setSizePolicy(qt.QSizePolicy.Expanding, qt.QSizePolicy.Expanding)
             
    def _define_main_layout(self):
        layout = qt.QVBoxLayout()
        return layout
        
    def _build_widgets(self):
        
        self.pose_list = PoseTreeWidget(self.shot_sculpt_only)
        
        self.pose_list.list_refresh.connect(self.pose_list_refresh.emit)
        
        #self.pose_list.itemSelectionChanged.connect(self.update_pose_widget)
        
        self.pose_widget = PoseWidget()
        self.pose_widget.hide()
        
        self.pose_list.pose_renamed.connect(self._pose_renamed)
        self.pose_list.pose_deleted.connect(self._pose_deleted)
        
        self.filter_names = qt.QLineEdit()
        self.filter_names.setPlaceholderText('filter names')

        self.filter_names.textChanged.connect(self.set_filter_names)
        
        self.main_layout.addWidget(self.pose_list)
        self.main_layout.addWidget(self.filter_names)
        self.main_layout.addWidget(self.pose_widget)
    


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

    def _update_pose_no_reader(self, current_pose, current_weight_attribute):
        
        item_count = self.pose_list.topLevelItemCount()
        
        auto_key_state = cmds.autoKeyframe(q=True, state=True)
        cmds.autoKeyframe(state=False)
        
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
                    # vtool.util.warning('Could not set %s to 0.' % current_weight_attribute )

        cmds.autoKeyframe(state=auto_key_state)
        


        
        
                
    def _pose_renamed(self, new_name):
        self.pose_renamed.emit(new_name)
        
    def _pose_deleted(self):
        self.pose_deleted.emit()

    def update_pose_widget(self):
        
        current_pose = self.pose_list._current_pose()
        current_weight_attribute = '%s.weight' % current_pose
        
        items = self.pose_list.selectedItems()
        
        if items:
            self.pose_widget.show()
            self.pose_widget.set_pose(current_pose)
            
        if not items:
            self.pose_widget.hide()
            
        self.pose_update.emit(current_pose)
        
        if not current_pose:
            return
        
        pose_type = cmds.getAttr('%s.type' % current_pose)
        
        if pose_type == 'no reader':
            self._update_pose_no_reader(current_pose, current_weight_attribute)

    def update_current_pose(self):
        
        current_pose = self.pose_list._current_pose()
        
        if not current_pose:
            core.print_warning( 'Trying to update current pose but none selected.' )
            return
        
        pose_type = cmds.getAttr('%s.type' % current_pose)
        
        if pose_type == 'timeline':
            pass
        if not pose_type == 'timeline':
            pass
        
        
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
        
    def change_mesh(self, int_value):
        self.pose_list.mesh_change(int_value)
        
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
        
    def set_filter_names(self, text = None):
        
        if not text:
            text = str(self.filter_names.text())
        
        self.pose_list.filter_names(text)
        self.skip_name_filter = False
        
    def highlight_pose(self, pose_name):
        
        self.pose_list.highlight_pose(pose_name)
        
    def mirror_all(self):
        self.pose_list.mirror_all()
    
    def reconnect_all(self):
        self.pose_list.reconnect_all()
    
class BaseTreeWidget(qt_ui.TreeWidget):

    list_refresh = qt_ui.create_signal()
    pose_deleted = qt_ui.create_signal()
    pose_renamed = qt_ui.create_signal(object)
    
    def __init__(self):
        
        self.edit_state = False
        super(BaseTreeWidget, self).__init__()
        self.setSortingEnabled(True)
        self.setSelectionMode(self.SingleSelection)
        
        ui_core.new_scene_signal.signal.connect(self.refresh)
        
        self.text_edit = False
        
        self._populate_list()
        
        self.pose_widget = None

    def _populate_list(self):
        self.clear()
        self.list_refresh.emit()
        
    def _current_item(self):
        
        selected = self.selectedItems()
        
        item = None
        
        if selected:
            item = selected[0]
            
        return item
        
    def _current_pose(self):
        
        item = self._current_item()
            
        if item:
            return str(item.text(0))

    def _get_selected_items(self, get_names=False):
        selected = self.selectedIndexes()
        
        items = []
        names = []
        
        for index in selected:
            
            item = self.itemFromIndex(index)
            
            if not get_names:
                items.append(item)
            if get_names:
                name = str(item.text(0))
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
        
        new_name = qt_ui.get_new_name('Please specify a name.', self, old_name=self.old_name)
                
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
    
    def _remove_current_item(self):
        
        item = self._current_item()
        
        parent_item = item.parent()
        
        if not parent_item:
            parent_item = self.invisibleRootItem()    
        
        index = parent_item.indexOfChild(item)
        item = parent_item.takeChild(index)
        
        
        del(item)
    
    def refresh(self):
        self._populate_list()
        
    def delete_pose(self):
        
        pose = self._current_pose()
        
        if not pose:
            return
        
        permission = qt_ui.get_permission('Delete Pose: %s?' % pose, self)
        
        if not permission:
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

    def __init__(self, shot_sculpt_only = False):
        
        self.shot_sculpt_only = shot_sculpt_only
        self.item_context = []
        self.context_menu_item = None
        self._highlighted_items = []
        
        super(PoseTreeWidget, self).__init__()
        
        self.setDragDropMode(self.InternalMove)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)  
        
        self.setAutoScroll(True)
        
        self.setHeaderLabels(['pose', 'type'])
       
        self.header().setStretchLastSection(False)
        
        if vtool.util.get_maya_version() < 2017:
            self.header().setResizeMode(0, self.header().Stretch)
        if vtool.util.get_maya_version() >= 2017:
            self.header().setSectionResizeMode(0, self.header().Stretch)
        
        self.last_selection = []
    
        self.setContextMenuPolicy(qt.QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._item_menu)
        
        self._create_context_menu()
        
        self.update_select = True
        self.item_select = True
        
    def mousePressEvent(self, event):
        
        model_index = self.indexAt(event.pos())
        
        item = self.itemAt(event.pos())
        
        parent = self.invisibleRootItem()
        
        if item:
            item_parent = item.parent()
            
            if item_parent:
                parent = item_parent
                
            self._reconnect_item(item)
        
        self.drag_parent = parent
        self.dragged_item = item
        
        if not item or model_index.column() == 1:
            self.clearSelection()
            
        
        if event.button() == qt.QtCore.Qt.RightButton:
            return
        
        if model_index.column() == 0 and item:
            super(PoseTreeWidget, self).mousePressEvent(event)
    
        if self._highlighted_items:
            self._remove_highlights()
            
    def dropEvent(self, event):
        
        position = event.pos()
        entered_item = self.itemAt(position)
        index = self.indexAt(position)
        
        is_dropped = self.is_item_dropped(event)
        
        super(PoseTreeWidget, self).dropEvent(event)
        
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
            
        # result = qt_ui.get_permission('Parent item %s?' % self.dragged_item.text(0), self)
        result = True
        
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
            
            current_parent = cmds.listRelatives(pose, p=True)
            
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
        
        self.context_menu = qt.QMenu()
        self.context_menu.setTearOffEnabled(True)
        
        self.create_group = self.context_menu.addAction('New Group')
        
        if not self.shot_sculpt_only:
            self.create_cone = self.context_menu.addAction('New Cone')
            self.create_no_reader = self.context_menu.addAction('New No Reader')
            self.create_combo = self.context_menu.addAction('New Combo')
            
        self.create_timeline = self.context_menu.addAction('New Timeline')
        
        self.item_context = []
        
        # self.create_rbf = pose_menu.addAction('RBF')
        self.context_menu.addSeparator()
        
        self.rename_action = self.context_menu.addAction('Rename')
        self.delete_action = self.context_menu.addAction('Delete')
        self.context_menu.addSeparator()
        self.option_menu = self.context_menu.addMenu('Options')
        # self._create_pose_options_context()
        self.context_menu.addSeparator()
        self.set_pose_action = self.context_menu.addAction('Update Pose (Controls with Current Deformation)')
        self.set_controls_action = self.context_menu.addAction('Update Pose (Controls with Stored Deformation)')
        self.set_controls_only_action = self.context_menu.addAction('Update Pose (Controls Only)')
        #self.update_sculpts_action = self.context_menu.addAction('Update Sculpt')
        self.revert_vertex_action = self.context_menu.addAction('Revert Vertex')
        self.reset_sculpts_action = self.context_menu.addAction('Reset Sculpt')
        
        self.context_menu.addSeparator()
        self.refresh_action = self.context_menu.addAction('Refresh')
        
        self.item_context = self.item_context + [self.rename_action,
                                                 self.delete_action,
                                                 self.revert_vertex_action,
                                                 self.reset_sculpts_action,
                                                 self.set_pose_action,
                                                 self.set_controls_action,
                                                 self.set_controls_only_action]
        
        if not self.shot_sculpt_only:
            self.create_cone.triggered.connect(self.create_cone_pose)
            self.create_no_reader.triggered.connect(self.create_no_reader_pose)
            self.create_combo.triggered.connect(self.create_combo_pose)
            
        self.create_timeline.triggered.connect(self.create_timeline_pose)
        self.create_group.triggered.connect(self.create_group_pose)
        
        self.rename_action.triggered.connect(self._rename_pose)
        self.delete_action.triggered.connect(self.delete_pose)
        self.set_pose_action.triggered.connect(self._set_pose_data)
        self.set_controls_action.triggered.connect(self._update_stored_controls)
        self.set_controls_only_action.triggered.connect(self._update_only_stored_controls)
        self.reset_sculpts_action.triggered.connect(self._reset_sculpts)
        #self.update_sculpts_action.triggered.connect(self._update_sculpts)
        self.revert_vertex_action.triggered.connect(self._revert_vertex)
        
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
        
        item = qt.QTreeWidgetItem(parent)
        item.setSizeHint(0, qt.QtCore.QSize(100, 20))
        item.setText(0, pose)
        
        if cmds.objExists('%s.type' % pose):
            type_name = cmds.getAttr('%s.type' % pose)
            item.setText(1, type_name)
        
        self.addTopLevelItem(item)
        
        return item
        
    def _populate_list(self):
        
        self.clear()
        
        if not cmds.objExists('pose_gr'):
            return
        
        poses = corrective.PoseManager().get_poses()
        
        if not poses:
            return
        
        self.item_select = False
        
        for pose in poses:
            
            cmds.select(cl=True)
            
            self._add_pose_item(pose)
               
        self.item_select = True
        
        self.list_refresh.emit()
    
    def _reconnect_item(self, item):
        pose = item.text(0)
        
        pose_inst = corrective.get_pose_instance(pose)
        if hasattr(pose_inst, 'reconnect_blends'):
            pose_inst.reconnect_blends()
    
    def _add_pose_item(self, pose_name, parent=None):
         
        if cmds.objExists('%s.type' % pose_name):
            pose_type = cmds.getAttr('%s.type' % pose_name)
        
        if not cmds.objExists('%s.type' % pose_name):
            pose_type = 'cone'
        
        new_item = self.create_pose(pose_type, pose_name, parent)
        
        sub_manager = corrective.PoseManager()
        sub_manager.set_pose_group(pose_name)
        
        sub_poses = sub_manager.get_poses()
        
        if sub_poses:
        
            for sub_pose in sub_poses:
                self._add_pose_item(sub_pose, new_item)
        

        
        return new_item 
                      
    def _select_joint(self):
        name = self._current_pose()
        pose = corrective.get_pose_instance(name)
        transform = pose.get_transform()
        
        core.show_channel_box()
        
        cmds.select(transform)
        
    def _select_pose(self):
        
        name = self._current_pose()
        
        control = corrective.PoseManager().get_pose_control(name)
        
        core.show_channel_box()
        
        cmds.select(control)

    def _update_stored_controls(self):
        
        name = self._current_pose()
        corrective.PoseManager().update_pose(name)
        
        pose_instance = corrective.PoseManager().get_pose_instance(name)
        pose_instance.create_all_blends()

    def _update_only_stored_controls(self):
        
        name = self._current_pose()
        corrective.PoseManager().update_pose(name)
        


    def _set_pose_data(self):
        
        name = self._current_pose()
        
        corrective.PoseManager().update_pose(name)
        
        pose_instance = corrective.PoseManager().get_pose_instance(name)
        
        if hasattr(pose_instance, 'update_target_meshes'):
            pose_instance.update_target_meshes()
            
        
        
        
    def _update_sculpts(self):
        
        name = self._current_pose()
        corrective.PoseManager().update_pose_meshes(name)
        
    def _revert_vertex(self):
        
        name = self._current_pose()
        corrective.PoseManager().revert_pose_vertex(name)
        
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
        
        core.show_channel_box()
           
        cmds.select(blend, r=True)
        
    def _get_item(self, pose_name):
        if pose_name and cmds.objExists(pose_name):
        
            iterator = qt.QTreeWidgetItemIterator(self)
            
            found_item = None
            
            while iterator.value():
                if found_item:
                    iterator+=1
                    continue
                
                item = iterator.value()
                
                if str(item.text(0)) == pose_name:
                    
                    found_item = item
                    
                iterator += 1
        
            return found_item
        
    def _expand_to_item(self, item):
        
        
        parent = item.parent()
        if not parent:
            return
        parent.setExpanded(True)
        
        while parent:
            
            parent = parent.parent()
            if parent:
                parent.setExpanded(True)
            
            
            
        
    def _remove_highlights(self):
        for item in self._highlighted_items:
            try:
                item.setBackground(0, qt.QBrush())
            except:
                pass
            
        self._highlighted_items = []
        
    def create_pose(self, pose_type, name=None, parent=None):
        
        selection = cmds.ls(sl=True, l=True)
        
        pose = None
        
        if name:
            pose = name
        
        if not pose:
            pose = corrective.PoseManager().create_pose(pose_type, name)
        
        if not pose:
            return
        
        if not pose_type == 'group':
            if selection:
                
                cmds.select(selection, r=True)
                self.check_for_mesh.emit(pose)
            
        item = self._add_item(pose, parent)
        
        self.update_select = False
        
        self.clearSelection()
        
        if self.item_select:
            item.setSelected(True)
            self.scrollToItem(item)
        self.update_select = True
        
        self._rename_pose()
        
        return item
    
    def create_cone_pose(self):
        self.create_pose('cone', None, None)
    
    def create_no_reader_pose(self):
        self.create_pose('no reader', None, None)
    
    def create_combo_pose(self):
        self.create_pose('combo', None, None)
        
    def create_timeline_pose(self):
        self.create_pose('timeline', None, None)
        
    def create_group_pose(self):
        self.create_pose('group', None, None)
        
    
    
    def mirror_pose(self):
        
        pose = self._current_pose()
        
        if not pose:
            return
        
        mirror = corrective.PoseManager().mirror_pose(pose)
        self.refresh()
        
        self.highlight_pose(mirror)
        self.reveal_pose(pose)
        self.select_pose(pose)
        
    def mirror_all(self):
        
        mirrors = corrective.PoseManager().mirror_all()
        
        self.refresh()
        
        self.highlight_pose(mirrors)
        
    def reconnect_all(self):
        
        reconnected_poses = corrective.PoseManager().reconnect_all()
        
        self.highlight_pose(reconnected_poses)
        
        
        
    def highlight_pose(self, pose_name):
        
        poses = vtool.util.convert_to_sequence(pose_name)
        
        if not poses:
            self._remove_highlights() 
        
        for pose in poses:
            item_to_highlight = self._get_item(pose)
            
            if not item_to_highlight:
                continue
            
            brush = qt.QBrush( qt_ui.yes_color)
            
            item_to_highlight.setBackground(0, brush)
            
            self._highlighted_items.append(item_to_highlight)
            self._expand_to_item(item_to_highlight)
        
    def reveal_pose(self, pose_name):
        item = self._get_item(pose_name)
        self._expand_to_item(item)
        
    def select_pose(self, pose_name=None):
        
        if not self.update_select:
            return
                
        if pose_name:
            
            auto_key_state = cmds.autoKeyframe(q=True, state=True)
            cmds.autoKeyframe(state=False)
            
            try:
                cmds.setAttr('%s.weight' % pose_name, 1)
            except:
                pass
            
            cmds.autoKeyframe(state=auto_key_state)
        
        if self.last_selection:
            if cmds.objExists(self.last_selection[0]): 
                corrective.PoseManager().visibility_off(self.last_selection[0])

        pose_names = self._get_selected_items(get_names=True)
        items = self._get_selected_items(get_names = False)
        
        if pose_names and not pose_name:
            if not cmds.objExists(pose_names[0]):
                self._remove_current_item()
            
            corrective.PoseManager().set_pose(pose_names[0])
        
        if pose_name and cmds.objExists(pose_name):
        
            if pose_names:
                if cmds.objExists(pose_names[0]):
                    if items:
                        items[0].setSelected(False)
        
            iterator = qt.QTreeWidgetItemIterator(self)
            
            while iterator.value():
                
                item = iterator.value()
                
                if str(item.text(0)) == pose_name:
                    
                    item.setSelected(True)
                    self.scrollToItem(item)
                    corrective.PoseManager().set_pose(pose_name)
                    
                iterator += 1
        
        self.last_selection = pose_names
        
        
class PoseWidget(qt_ui.BasicWidget):

    def __init__(self):
        super(PoseWidget, self).__init__()
        
        self.pose_name = None
        self.pose_control_widget = None
        
        self.setSizePolicy(qt.QSizePolicy.Minimum, qt.QSizePolicy.Minimum)
    
    def _define_main_layout(self):
        layout = qt.QHBoxLayout()
        layout.setAlignment(qt.QtCore.Qt.AlignRight)
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
            
        if pose_type == 'combo':
            self.pose_control_widget = PoseComboWidget()
            
        if pose_type == 'cone':
            self.pose_control_widget = PoseConeWidget()
            
        if pose_type == 'timeline':
            self.pose_control_widget = PoseTimelineWidget()
            
        if pose_type == 'group':
            self.pose_control_widget = PoseGroupWidget()
        
        self.pose_control_widget.set_pose(pose_name)
        
        self.main_layout.setAlignment(qt.QtCore.Qt.AlignLeft)
        self.setSizePolicy(qt.QSizePolicy.Expanding, qt.QSizePolicy.Minimum)
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
        
        self.setContextMenuPolicy(qt.QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._item_menu)
        
        self._create_context_menu()
        
        self.handle_selection_change = True
        
    def sizeHint(self):    
        return qt.QtCore.QSize(200, 100)
    
    def _item_menu(self, position):
        
        self.context_menu.exec_(self.mesh_list.viewport().mapToGlobal(position))
        
    def _create_context_menu(self):
        
        self.context_menu = qt.QMenu()
        
        remove = self.context_menu.addAction('Remove')
                
        remove.triggered.connect(self.remove_mesh)
    
    def _build_widgets(self):

        self.mesh_list = qt.QListWidget()        
        self.mesh_list.itemSelectionChanged.connect(self._item_selected)
        
        self.main_layout.addWidget(self.mesh_list)

    def _mesh_change(self, int_value):    
        self.mesh_change.emit(int_value)

    def get_current_meshes_in_list(self):
        items = self.mesh_list.selectedItems()
        
        found = []
        
        for item in items:
            found.append(str(item.longname))
        
        return found

    def _update_meshes(self, pose_name, meshes=[]):
        
        pose = self.pose_class
        
        if not pose or not pose_name:
            return
        
        if not cmds.objExists(pose_name):
            return
        
        pose.set_pose(pose_name)
        
        pose_type = cmds.getAttr('%s.type' % pose_name)
        
        if not pose_type == 'group':
            self.show()
            target_meshes = pose.get_target_meshes()            
            self.update_meshes(target_meshes, meshes)
            
        if pose_type == 'group':
            self.hide()
        
    def _is_in_mesh_list(self, mesh):
        
        mesh_list_count = self.mesh_list.count()
        
        for inc in range(0, mesh_list_count):
                    
            test_item = self.mesh_list.item(inc)
            
            if str(test_item.longname) == mesh:                
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
            name = core.get_basename(sculpt)
            
            if sculpt_count == 1:
                sculpt_name = name
                continue
            if inc == (sculpt_count - 1):
                sculpt_name += '\n%s' % name
                inc += 1
                continue
            if sculpt_count > 1:
                sculpt_name += '\n%s' % name
            
            inc += 1 
        
        if len(sculpt_meshes) > 1:
            mesh_info = 'meshes'
        
        permission = qt_ui.get_permission('Add %s:  %s  ?' % (mesh_info, sculpt_name), self)
        
        return permission        
    
    def _item_selected(self):
        
        if not self.handle_selection_change:
            return
        
        items = self.mesh_list.selectedItems()
        
        cmds.select(cl=True)
        
        for item in items:
            if cmds.objExists(item.longname):
                cmds.select(item.longname, add=True)
        
    def _warn_missing_meshes(self, meshes):
        missing_meshes = ''
        
        for mesh in meshes:
            if mesh: 
                if not cmds.objExists(mesh):
                    missing_meshes += '\n%s' % mesh
                
        if missing_meshes: 
            qt_ui.warning('Cannot find: %s' % missing_meshes, self)
        
    @core.undo_chunk
    def add_mesh(self, selection=None):
        
        pose_name = self.pose_name
        
        if not pose_name:
            return
        
        if not selection:
            selection = cmds.ls(sl=True, l=True)
        
        if self.pose_class:
            self.pose_class.goto_pose()
            
            
            
            """
            pose_type = self.pose_class.get_type()
            
            if pose_type == 'timeline':
                self.pose_class.update_target_meshes()
                corrective.PoseManager().update_pose(pose_name)
            """
        current_meshes = self.get_current_meshes_in_list()
        
        if not current_meshes:
            current_meshes = []
            
        self._warn_missing_meshes(current_meshes)
        
        sculpt_meshes = []
        list_meshes = []
        
        vert_checked = []
        
        if selection:
            
            for selected in selection:
                
                selected = self._get_mesh_from_vertex(selected)
                
                if selected in vert_checked:
                    continue
                
                vert_checked.append(selected)
                
                if not core.has_shape_of_type(selected, 'mesh'):
                    continue
                
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
            
            if sculpt_meshes:
                
                permission = self._get_sculpt_permission(sculpt_meshes)
                
                if not permission:
                    return
                
                corrective.PoseManager().add_mesh_to_pose(pose_name, sculpt_meshes)
            
            update_meshes = sculpt_meshes
            self._update_meshes(pose_name, meshes=update_meshes)
            
            list_meshes = []
            current_meshes = []
            
            self.mesh_list.clearSelection()
            
            items = []
            
            for mesh in sculpt_meshes:
                
                pose = corrective.get_pose_instance(pose_name)
                index = pose.get_target_mesh_index(mesh)
                
                if index != None:
                    item = self.mesh_list.item(index)
                    if item:
                        item.setSelected(True)
                        
                    items.append(item)
                    
            if items:
                self.mesh_list.scrollToItem(items[0])
            
        selection = cmds.ls(sl=True, l=True)
        
        if list_meshes:
            
            self.mesh_list.clearSelection()
            
            for mesh in list_meshes:
                
                if not mesh:
                    continue
                
                pose = corrective.get_pose_instance(pose_name)
                
                index = pose.get_target_mesh_index(mesh)
                
                if index == None:
                    continue
                
                item = self.mesh_list.item(index)
                if item:
                    item.setSelected(True)
                
                corrective.PoseManager().toggle_visibility(mesh, pose_name)
                
            cmds.select(selection)
            
            return
        

        
        if current_meshes:
            
            if corrective.PoseManager().get_pose_type(pose_name) == 'timeline':
                corrective.PoseManager().update_pose_meshes(pose_name, True)
                
            indices = self.mesh_list.selectedIndexes()
            
            if indices:
                for index in indices:
                    
                    index = index.row()
                    
                    mesh_item = self.mesh_list.item(index)
                    mesh = mesh_item.longname
                    
                    corrective.PoseManager().toggle_visibility(mesh, pose_name)
    
    def remove_mesh(self):
        items = self.mesh_list.selectedItems()
        
        if not items:
            return
        
        for item in items:
            mesh = str(item.longname)
            
            self.pose_class.remove_mesh(mesh)
            
            model_index = self.mesh_list.indexFromItem(item)
            
            index = model_index.row()
            item = self.mesh_list.takeItem(index)
            del item
            
    def update_meshes(self, meshes=[], added_meshes=[]):
        self.mesh_list.clear()    
        
        # self.handle_selection_change = False
        
        for mesh in meshes:
            
            if not mesh:
                continue
            
            item = qt.QListWidgetItem()
            item.setSizeHint(qt.QtCore.QSize(0, 20))
            basename = core.get_basename(mesh)
            item.setText(basename)
            item.longname = mesh
            self.mesh_list.addItem(item)
            
            # if mesh in added_meshes:
            item.setSelected(True)
        
        # if not added_meshes:   
            
        #    item = self.mesh_list.item(index)
        #    if item:
        #        item.setSelected(True)
                
        # self.handle_selection_change = True
            
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
        
        return qt.QtCore.QSize(200, 200)
        
    def _define_main_layout(self):
        return qt.QVBoxLayout()
    
    def _button_sculpt(self):
        
        try:
            
            self.button_sculpt.setDisabled(True)
            
            self.mesh_widget.add_mesh()
            self.sculpted_mesh.emit()
            
            self.button_sculpt.setEnabled(True)
            
            if self.pose:
                
                auto_key_state = cmds.autoKeyframe(q=True, state=True)
                cmds.autoKeyframe(state=False)
                
                try:
                    cmds.setAttr('%s.weight' % self.pose, 1)
                except:
                    pass
                
                cmds.autoKeyframe(state=auto_key_state)
            
                cmds.select(self.pose)
            
        except:
            
            vtool.util.error(traceback.format_exc())
            
            self.button_sculpt.setEnabled(True)
            
    def _button_mirror(self):
        try:
            self.button_mirror.setDisabled(True)
            self.pose_mirror.emit()
            self.button_mirror.setEnabled(True)
        except:
            self.button_mirror.setEnabled(True)
    
    def _build_widgets(self):
        
        self.slider = qt.QSlider()
        
        self.slider.setOrientation(qt.QtCore.Qt.Horizontal)
        self.slider.setMaximumHeight(30)
        self.slider.setMinimum(0)
        self.slider.setMaximum(100)
        self.slider.setTickPosition(self.slider.NoTicks)
        
        self.slider.valueChanged.connect(self._pose_enable)
        
        self.button_sculpt = qt.QPushButton('Sculpt')
        self.button_sculpt.setMinimumWidth(100)

        button_mirror = qt.QPushButton('Mirror')
        button_mirror.setMaximumWidth(100)
        button_mirror.clicked.connect(self._button_mirror)
        
        self.button_mirror = button_mirror
        
        v_layout = qt.QHBoxLayout()
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
        
        value = value / 100.00
        
        if not self.pose:
            return
        
        cmds.setAttr('%s.enable' % self.pose, value)
      
    def set_pose(self, pose_name):
        
        if pose_name == self.pose:
            return
        
        self.mesh_widget.set_pose(pose_name)
        
        if not pose_name:
            self.pose = None
            
            return
        
        pose_type = cmds.getAttr('%s.type' % pose_name)
        
        if pose_type == 'timeline':
            self.button_mirror.hide()
            
        if not pose_type == 'timeline':
            self.button_mirror.show()
            
        
            
        self.pose = pose_name
        
        auto_key_state = cmds.autoKeyframe(q=True, state=True)
        cmds.autoKeyframe(state=False)
        
        try:
            cmds.setAttr('%s.weight' % pose_name, 1)
        except:
            pass
        
        cmds.autoKeyframe(state=auto_key_state)

        
        self.set_pose_enable()
        
    def set_pose_enable(self):
        
        if not cmds.objExists('%s.enable' % self.pose):
            return
        
        value = cmds.getAttr('%s.enable' % self.pose)
        
        value = value * 100
        self.slider.setValue(value)
        
        
class TimePosition(qt_ui.GetNumber):
    
    def __init__(self):
        super(TimePosition, self).__init__('Time Position')
        
        self.pose = None
        self.old_value = None
        self.update_value = True
        #self.update_value_permission = True
    
    def _define_main_layout(self):
        return qt.QHBoxLayout()
    
    def _build_widgets(self):
        
        self.main_layout.setContentsMargins(0,0,0,0)
        self.main_layout.setSpacing(0)
        
        self.number_widget = self._define_number_widget()
        self.number_widget.setMaximumWidth(100)
        
        self.number_widget.setAlignment(qt.QtCore.Qt.AlignLeft)
        
        
        self.label = qt.QLabel(self.name)
        self.label.setAlignment(qt.QtCore.Qt.AlignLeft)
        
        self.main_layout.addWidget(self.number_widget)
        self.main_layout.addSpacing(10)
        self.main_layout.addWidget(self.label)
    
    def _value_changed(self):
        
        if not self.update_value:
            return
        super(TimePosition, self)._value_changed()
        
        value = self.get_value()
        """
        if self.update_value_permission:
            permission = qt_ui.get_permission('Change Pose?\nMake sure you retime your animation first.', self)
            
            if not permission:
                
                self.update_value = False
                if self.pose:
                    
                    
                    value = cmds.getAttr('%s.timePosition' % self.pose)
                    self.set_value(value)
                    
                self.update_value = True
                
                return
        """
        if self.pose:
            
            pose = corrective.PoseTimeline()
            pose.set_pose(self.pose)
            
            pose.shift_time(value)
            
        
        
    def set_pose(self, name):
        self.pose = name
        
    
#--- pose widgets

class PoseBaseWidget(qt_ui.BasicWidget):
    
    def __init__(self):
        
        super(PoseBaseWidget, self).__init__()
        self.pose = None

        self.do_target_change = True

    
    def _build_widgets(self):
        super(PoseBaseWidget, self)._build_widgets()
        
    def _string_widget(self, name):
        layout = qt.QHBoxLayout()
        
        label = qt.QLabel(name)
        text = qt.QLineEdit()
        
        layout.addWidget(label)
        layout.addWidget(text)
        
        return layout, text
        
    def _add_spin_widget(self, name):
        layout = qt.QHBoxLayout()
        layout.setSpacing(1)
        layout.setContentsMargins(0, 0, 0, 0)
        
        label = qt.QLabel(name)
        label.setAlignment(qt.QtCore.Qt.AlignRight)
        
        widget = qt.QDoubleSpinBox()
        
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

class PoseGroupWidget(PoseBaseWidget):
    
    def _build_widgets(self):
        super(PoseGroupWidget, self)._build_widgets()
        
        layout = qt.QVBoxLayout()
        build_all = qt.QPushButton('Build Sub Poses')
        build_all.setMinimumSize(200, 40)
        
        layout.addSpacing(10)
        layout.addWidget(build_all, alignment=qt.QtCore.Qt.AlignLeft)
        layout.addSpacing(10)
        build_all.setSizePolicy(qt.QSizePolicy.Expanding, qt.QSizePolicy.Minimum)
        self.main_layout.setAlignment(qt.QtCore.Qt.AlignLeft)
        self.main_layout.addLayout(layout)
        
        build_all.clicked.connect(self._build_sub_poses)
        
    def _build_sub_poses(self):
        
        pose_instance = corrective.get_pose_instance(self.pose)
        pose_instance.create_sub_poses()
        
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
        
        self.input_text.setStyleSheet('qt.QLineEdit{background:red}')
        
        text = str(self.input_text.text())
        
        if not text:
            
            style = self.styleSheet()
            self.input_text.setStyleSheet(style)
        
        if attr.is_attribute_numeric(text):
                        
            style = self.styleSheet()
            self.input_text.setStyleSheet(style)
            
            self.set_input(text)
            
        if not attr.is_attribute_numeric(text):
            
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
    def _define_main_layout(self):
        layout = qt.QHBoxLayout()
        return layout
    
    def _build_widgets(self):
        super(PoseTimelineWidget, self)._build_widgets()
        
        self.frame_number = TimePosition()
        self.main_layout.addWidget(self.frame_number)
        
    def set_pose(self, pose_name):
        super(PoseTimelineWidget, self).set_pose(pose_name)
    
        time_position = cmds.getAttr('%s.timePosition' % pose_name)
        self.frame_number.set_value(time_position)
        self.frame_number.set_pose(pose_name)

class PoseConeWidget(PoseBaseWidget):
    
    def __init__(self):
        
        super(PoseConeWidget, self).__init__()
        self.value_update_enable = True
        
    def _define_main_layout(self):
        layout = qt.QVBoxLayout()
        return layout
        
    def _build_widgets(self):
        super(PoseConeWidget, self)._build_widgets()
        self.combo_label = qt.QLabel('Alignment')
        
        self.combo_axis = qt.QComboBox()
        self.combo_axis.addItems(['X', 'Y', 'Z'])
        
        layout_combo = qt.QHBoxLayout()
        
        layout_combo.addWidget(self.combo_label, alignment=qt.QtCore.Qt.AlignRight)
        layout_combo.addWidget(self.combo_axis)
        
        layout_angle, self.max_angle = self._add_spin_widget('Max Angle')
        layout_distance, self.max_distance = self._add_spin_widget('Max Distance')
        layout_twist, self.twist = self._add_spin_widget('Max twist')
        layout_twist_on, self.twist_on = self._add_spin_widget('Twist')
                        
        self.max_angle.setRange(0, 180)
        
        self.twist.setRange(0, 180)
        self.twist_on.setRange(0, 1)
        self.max_distance.setMinimum(0)
        self.max_distance.setMaximum(10000000)
        
        parent_combo = qt.QHBoxLayout()
        
        parent_label = qt.QLabel('Parent')
        self.parent_text = qt.QLineEdit()
        
        self.parent_text.textChanged.connect(self._parent_name_change)
        
        parent_combo.addWidget(parent_label, alignment=qt.QtCore.Qt.AlignRight)
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
        
        text = str(self.combo_axis.currentText())
        self.axis_change(text)
        
    def _set_ui_values(self, angle, distance, twist_on, twist):
        
        self.value_update_enable = False
        self.max_angle.setValue(angle)
        self.max_distance.setValue(distance)
        self.twist_on.setValue(twist_on)
        self.twist.setValue(twist)
        self.value_update_enable = True
        
    def _parent_name_change(self):
        
        self.parent_text.setStyleSheet('qt.QLineEdit{background:red}')
        
        text = str(self.parent_text.text())
        
        if not text:
            
            style = self.styleSheet()
            self.parent_text.setStyleSheet(style)
            
            return
            
        if cmds.objExists(text) and core.is_transform(text):
            
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
        
        value = value / 100.00
        
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
        
        if not cmds.objExists(pose):
            return
               
        x = cmds.getAttr("%s.axisRotateX" % pose)
        y = cmds.getAttr("%s.axisRotateY" % pose)
        z = cmds.getAttr("%s.axisRotateZ" % pose)
        
        axis = [x, y, z]
        
        if axis == [1, 0, 0]:
            self.combo_axis.setCurrentIndex(0)
        if axis == [0, 1, 0]:
            self.combo_axis.setCurrentIndex(1)
        if axis == [0, 0, 1]:
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
        
        if not pose_name or not cmds.objExists(pose_name):
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
        value = value * 100
        self.slider.setValue(value)
    
class PoseComboWidget(PoseBaseWidget):
    
    def _define_main_layout(self):
        return qt.QHBoxLayout()
    
    def _build_widgets(self):
        
        add_layout = qt.QVBoxLayout()
        
        self.add_layout = add_layout
        
        self._add_pose_list(add_layout)
        
        add = qt.QPushButton('Add')
        add.setMinimumWidth(100)
        add.clicked.connect(self._add_pose)
        
        add_layout.addWidget(add, alignment = qt.QtCore.Qt.AlignRight)
        
        scroll = qt.QScrollArea()
        scroll.setWidgetResizable(True)
        
        self.main_layout.addLayout(add_layout)
        self.main_layout.addWidget(scroll)
        
        self.pose_combo_widget = PoseComboList()
        
        scroll.setWidget(self.pose_combo_widget)
        scroll.setMinimumWidth(200)
        
        
        self.pose_widgets = []
        
    def _add_pose_list(self, layout):
        tree = PoseTreeWidget(False)
        
        #tree.setMaximumHeight(80)
        
        self.tree = tree
        self.tree.setColumnCount(1)
        self.tree.setSelectionMode(self.tree.ExtendedSelection)
        self.tree.setHeaderHidden(True)
        self.tree.setDragEnabled(False)
        
        self.tree.itemSelectionChanged.connect(self._select_changed)
        
        layout.addWidget(self.tree)
        
    def _has_pose(self, pose):
        
        for widget in self.pose_widgets:
            
            if widget.get_name() == pose:
                return True
        
    def _add_pose(self):
        
        items = self.tree.selectedItems()
        
        if not items:
            return
        
        pose_instance = corrective.get_pose_instance(self.pose)
        
        for item in items:
            if self._has_pose(item.text(0)):
                continue
            
            
            pose_instance.add_pose(item.text(0))
            
        self._refresh_pose_list()
        pose_instance.refresh_multiply_connections()
        
    def _refresh_pose_list(self):
        
        pose_instance = corrective.get_pose_instance(self.pose)
        poses = pose_instance.get_poses()
        
        self.pose_combo_widget.clear_widgets()
            
        self.pose_widgets = []
        
        for pose in poses:
            
            if pose:
            
                widget = PoseInComboWidget(pose)
            
                self.pose_combo_widget.add_widget(widget)
                
        pose_instance.refresh_multiply_connections()
            
    def _select_changed(self):
        
        items = self.tree.selectedItems()
        
        if not items:
            return
        
        item = items[0]
        
        if item.text(0) == self.pose:
            item.setSelected(False)
        
    def set_pose(self, pose_name):
        pose = super(PoseComboWidget, self).set_pose(pose_name)
        
        
        self.pose_combo_widget.set_pose(pose_name)
        self._refresh_pose_list()
        
        
        return pose

class PoseComboList(qt_ui.BasicWidget):
    def __init__(self):
        super(PoseComboList, self).__init__()
        
        self.setSizePolicy(qt.QSizePolicy(qt.QSizePolicy.Expanding, qt.QSizePolicy.Expanding))
        
        self.pose_widgets = []
    
    def _remove_widget(self, widget):
        
        inc = 0
        pop_inc = None
        
        pose_instance = corrective.get_pose_instance(self.pose)
        pose_instance.remove_pose(widget.get_name())
        
        for pose_widget in self.pose_widgets:
            if widget.get_name() == pose_widget.get_name():
                
                pop_inc = inc 
            
            inc += 1 
            
        if pop_inc != None:
            self.pose_widgets.pop(pop_inc)
            self.main_layout.removeWidget(widget)
            widget.deleteLater()
        
    def clear_widgets(self):
        for widget in self.pose_widgets:
            self.main_layout.removeWidget(widget)
            widget.deleteLater()
            
            
        self.pose_widgets = []
        
    def add_widget(self, widget):
        
        widget.removed.connect(self._remove_widget)
        
        self.main_layout.addWidget(widget)
        
        self.pose_widgets.append(widget)
    
    def set_pose(self, pose_name):
        self.pose = pose_name
        
class PoseInComboWidget(qt_ui.BasicWidget):
    
    removed = qt_ui.create_signal(object)
    
    def __init__(self, name):
        super(PoseInComboWidget, self).__init__()
        
        self.set_name(name)
    
    def _build_widgets(self):
        
        self.label = qt.QLabel()
        weight = qt.QLabel('  ')
        self.number = qt.QLabel()
        
        self.remove = qt.QPushButton('Remove')
        self.remove.clicked.connect(self._remove)
        
        h_layout = qt.QHBoxLayout()
        
        h_layout.addWidget(self.label)
        h_layout.addWidget(weight)
        h_layout.addWidget(self.number)
        h_layout.addWidget(self.remove)
        
        self.main_layout.addLayout(h_layout)
        
    def _remove(self):
        self.removed.emit(self)
        
    def get_name(self):
        return str(self.label.text())
        
    def set_name(self, name):
        self.label.setText(name)
        
        pose_instance = corrective.get_pose_instance(name)
        
        if pose_instance.get_type() == 'cone' or pose_instance.get_type() == 'no reader':
            
            value = cmds.getAttr('%s.weight' % pose_instance.pose_control)
            self.set_value(value)
            
    def set_value(self, number):
        
        if number < 0.0001:
            number = 0.0
        
        self.number.setText(str(number))
        