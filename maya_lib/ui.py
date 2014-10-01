import maya.cmds as cmds

import maya.OpenMayaUI as OpenMayaUI
import maya.mel as mel

import vtool.qt_ui

from vtool.process_manager import ui_process_manager

import util

if vtool.qt_ui.is_pyqt():
    from PyQt4 import QtGui, QtCore, Qt, uic
if vtool.qt_ui.is_pyside():
    from PySide import QtCore, QtGui
   

def get_maya_window():
    
    if vtool.qt_ui.is_pyqt():
        import sip
        #Get the maya main window as a QMainWindow instance
        ptr = OpenMayaUI.MQtUtil.mainWindow()
        return sip.wrapinstance(long(ptr), QtCore.QObject)
    
    if vtool.qt_ui.is_pyside():
        from shiboken import wrapInstance
        maya_window_ptr = OpenMayaUI.MQtUtil.mainWindow()
        return wrapInstance(long(maya_window_ptr), QtGui.QWidget)
    
def create_window(ui, dock_area = 'right'): 
    
    ui_name = str(ui.objectName())
    
    dockName = '%sDock' % ui_name
    
    if (cmds.dockControl(dockName, q=1, ex=1)):
        cmds.deleteUI(dockName)
        
    allowedAreas = ['right', 'left']
    
    cmds.dockControl(dockName,aa=allowedAreas, a = dock_area, content=ui_name, label=ui_name, w=350, fl = False)
    
    ui.show()

def pose_manager():
    create_window(PoseManager())
    
def tool_manager(name = None, directory = None):
    tool_manager = ToolManager(name)
    tool_manager.set_directory(directory)
    
    create_window(tool_manager)
    
    return tool_manager


    
def process_manager(directory = None):
    window = ProcessMayaWindow()
    
    
    create_window(window)
    
    if directory:
        window.set_code_directory(directory)
        
    return window

class MayaWindow(vtool.qt_ui.BasicWindow):
    def __init__(self):
        super(MayaWindow, self).__init__( get_maya_window() )
        
class MayaDirectoryWindow(vtool.qt_ui.DirectoryWindow):
    def __init__(self):
        super(MayaDirectoryWindow, self).__init__( get_maya_window() )
        
class ProcessMayaWindow(ui_process_manager.ProcessManagerWindow):
    
    def __init__(self):
        super(ProcessMayaWindow, self).__init__( get_maya_window() )
    
class ToolManager(MayaDirectoryWindow):
    title = 'HUB'
    
    def __init__(self, name = None):
        if name:
            self.title = name
    
        super(ToolManager, self).__init__()
        
    def _build_widgets(self):
        self.tab_widget = QtGui.QTabWidget()
        self.tab_widget.setTabPosition(self.tab_widget.West)
        
        
        self.modeling_widget = ModelManager()
        self.rigging_widget = RigManager()
        self.shot_widget = QtGui.QWidget()
        
        self.tab_widget.addTab(self.rigging_widget, 'RIG')
        self.tab_widget.setCurrentIndex(1)
        
        self.main_layout.addWidget(self.tab_widget)
        
    def set_directory(self, directory):
        super(ToolManager, self).set_directory(directory)
        self.rigging_widget.set_directory(directory)
     
class LightManager(vtool.qt_ui.BasicWidget):
    pass
     
class ModelManager(vtool.qt_ui.BasicWidget):
    def _build_widgets(self):
        pass
        
class RigManager(vtool.qt_ui.DirectoryWidget):
    def _build_widgets(self):
        
        manager_group = QtGui.QGroupBox('Managers')
        manager_layout = QtGui.QVBoxLayout()
        manager_layout.setContentsMargins(2,2,2,2)
        manager_layout.setSpacing(2)
        
        manager_group.setLayout(manager_layout)
        
        process_button = QtGui.QPushButton('Process Manager')
        pose_button = QtGui.QPushButton('Pose Manager')
        
        process_button.clicked.connect(self._process_manager)
        pose_button.clicked.connect(self._pose_manager)
        
        manager_layout.addWidget(process_button)
        manager_layout.addWidget(pose_button)
        
        tool_group = QtGui.QGroupBox('Tools')
        tool_layout = QtGui.QVBoxLayout()
        tool_layout.setContentsMargins(2,2,2,2)
        tool_layout.setSpacing(2)
        tool_group.setLayout(tool_layout)
        
        tool_tab = QtGui.QTabWidget()
        deformation_widget = vtool.qt_ui.BasicWidget()
        structure_widget = vtool.qt_ui.BasicWidget()
        control_widget = vtool.qt_ui.BasicWidget()
        tool_layout.addWidget(tool_tab)
        
        tool_tab.addTab(structure_widget, 'structure')
        tool_tab.addTab(control_widget, 'controls')
        tool_tab.addTab(deformation_widget, 'deformation')
        
        self._create_structure_widgets(structure_widget)
        self._create_control_widgets(control_widget)
        self._create_deformation_widgets(deformation_widget)
        
        self.main_layout.addWidget(manager_group)
        self.main_layout.addWidget(tool_group)
        
        self.main_layout.setAlignment(QtCore.Qt.AlignTop)
        
    def _create_structure_widgets(self, parent):
        subdivide_joint_button =  vtool.qt_ui.GetIntNumberButton('subdivide joint')
        subdivide_joint_button.set_value(1)
        subdivide_joint_button.clicked.connect(self._subdivide_joint)
        subdivide_joint_button.setToolTip('select parent and child joint')
        
        add_orient = QtGui.QPushButton('Add Orient')
        add_orient.setToolTip('select joints')
        orient_joints = QtGui.QPushButton('Orient')
        orient_joints.setMinimumHeight(40)
        
        mirror = QtGui.QPushButton('Mirror')
        mirror.setMinimumHeight(40)
        
        match_joints = QtGui.QPushButton('Match')
        match_joints.setMinimumHeight(40)
        
        joints_on_curve = vtool.qt_ui.GetIntNumberButton('create joints on curve')
        joints_on_curve.set_value(10)
        
        snap_to_curve = vtool.qt_ui.GetIntNumberButton('snap joints to curve')
        
        transfer_joints = QtGui.QPushButton('transfer joints')
        transfer_process = QtGui.QPushButton('transfer process weights to parent')
        
        self.joint_axis_check = QtGui.QCheckBox('joint axis visibility')
        
        
        add_orient.clicked.connect(self._add_orient)
        orient_joints.clicked.connect(self._orient)
        mirror.clicked.connect(self._mirror)
        match_joints.clicked.connect(self._match_joints)
        joints_on_curve.clicked.connect(self._joints_on_curve)
        snap_to_curve.clicked.connect(self._snap_joints_to_curve)
        transfer_joints.clicked.connect(self._transfer_joints)
        transfer_process.clicked.connect(self._transfer_process)
        self.joint_axis_check.stateChanged.connect(self._set_joint_axis_visibility)
        
        main_layout = parent.main_layout
        
        main_layout.addWidget(add_orient)
        main_layout.addWidget(orient_joints)
        main_layout.addWidget(mirror)
        main_layout.addWidget(match_joints)
        main_layout.addWidget(subdivide_joint_button)
        main_layout.addWidget(joints_on_curve)
        main_layout.addWidget(snap_to_curve)
        main_layout.addWidget(transfer_joints)
        main_layout.addWidget(transfer_process)
        main_layout.addWidget(self.joint_axis_check)
        
    def _match_joints(self):
        print 'matching'
        util.match_joint_xform('joint_', 'guideJoint_')
        util.match_orient('joint_', 'guideJoint_')
        
    def _create_control_widgets(self, parent):
        
        mirror_control = QtGui.QPushButton('Mirror Control')
        mirror_control.clicked.connect(self._mirror_control)
        
        mirror_controls = QtGui.QPushButton('Mirror Controls')
        mirror_controls.clicked.connect(self._mirror_controls)
        mirror_controls.setMinimumHeight(40)
        
        parent.main_layout.addWidget(mirror_control)
        parent.main_layout.addWidget(mirror_controls)
        
    def _create_deformation_widgets(self, parent):
        corrective_button = QtGui.QPushButton('Create Corrective')
        corrective_button.setToolTip('select deformed mesh then fixed mesh')
        corrective_button.clicked.connect(self._create_corrective)
        
        skin_mesh_from_mesh = QtGui.QPushButton('Skin Mesh From Mesh')
        corrective_button.clicked.connect(self._skin_mesh_from_mesh)
        
        parent.main_layout.addWidget(corrective_button)
        parent.main_layout.addWidget(skin_mesh_from_mesh)
        
    
        
    def _pose_manager(self):
        pose_manager()
        
    def _process_manager(self):
        process_manager(self.directory)

    def _create_corrective(self):
        
        selection = cmds.ls(sl = True)
        
        util.chad_extract_shape(selection[0], selection[1])
    
    def _skin_mesh_from_mesh(self):
        selection = cmds.ls(sl = True)
        util.skin_mesh_from_mesh(selection[0], selection[1])
    
    def _subdivide_joint(self, number):
        util.subdivide_joint(count = number)
        
    def _add_orient(self):
        selection = cmds.ls(sl = True, type = 'joint')
        
        util.add_orient_attributes(selection)
        
    def _orient(self):
        util.orient_attributes()
        
    def _mirror(self):
        util.mirror_xform('joint_')
        util.mirror_xform('guideJoint_')
        util.mirror_xform('process_')
        
    def _mirror_control(self):
        
        selection = cmds.ls(sl = True)
        util.mirror_control(selection[0])
        
    def _mirror_controls(self):
        
        util.mirror_controls()
        
    def _joints_on_curve(self, count):
        selection = cmds.ls(sl = True)
        
        util.create_oriented_joints_on_curve(selection[0], count, False)
         
    def _snap_joints_to_curve(self, count):
        
        scope = cmds.ls(sl = True)
        
        if not scope:
            return
        
        node_types = util.get_node_types(scope)
        
        joints = node_types['joint']
        
        curve = None
        if 'nurbsCurve' in node_types:
            curves = node_types['nurbsCurve']
            curve = curves[0]
            
        if not joints:
            return

        util.snap_joints_to_curve(joints, curve, count)
        
    def _transfer_joints(self):
        
        scope = cmds.ls(sl = True)
        
        node_types = util.get_node_types(scope)
        
        if not scope or len(scope) < 2:
            return
        
        meshes = node_types['mesh']
        
        if len(meshes) < 2:
            return
        
        mesh_source = meshes[0]
        mesh_target = meshes[1]
        
        guideJoints = cmds.ls('guideJoint_*', type = 'joint')
        joints = cmds.ls('joint_*', type = 'joint')
        
        joints = guideJoints + joints
        
        if not joints:
            return
        
        transfer = util.XformTransfer()
        transfer.set_scope(joints)
        transfer.set_source_mesh(mesh_source)
        transfer.set_target_mesh(mesh_target)
        
        transfer.run()
        
    def _transfer_process(self):
        
        selection = cmds.ls(sl = True)
        
        if not selection:
            return
        
        node_types = util.get_node_types(selection)
        
        if not 'mesh' in node_types:
            return
        
        meshes = node_types['mesh']
        
        
        for mesh in meshes:
            util.process_joint_weight_to_parent(mesh)
            
    def _set_joint_axis_visibility(self):
        
        bool_value = self.joint_axis_check.isChecked()
        
        util.joint_axis_visibility(bool_value)


class PoseManager(MayaWindow):
    
    title = 'PoseManager'
    
    def _define_main_layout(self):
        layout = QtGui.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)
        return layout
        
    def _build_widgets(self):
        
        self.pose_set = PoseSetWidget()
        self.pose_list = PoseListWidget()
        
        self.pose_control = PoseControlWidget()
        
        self.pose_list.set_pose_widget(self.pose_control)
        
        self.pose_set.pose_reset.connect(self.pose_list.pose_reset)
        
        self.pose_control.pose_create.connect(self.pose_list.create_pose)
        self.pose_control.pose_delete.connect(self.pose_list.delete_pose)
        self.pose_control.pose_mirror.connect(self.pose_list.mirror_pose)
        self.pose_control.pose_mesh.connect(self.pose_list.add_mesh)
        self.pose_control.pose_mesh_view.connect(self.pose_list.view_mesh)
        self.pose_control.mesh_change.connect(self.pose_list.change_mesh)
        self.pose_control.axis_change.connect(self.pose_list.change_axis)
        self.pose_control.value_changed.connect(self.pose_list.value_changed)

        self.main_layout.addWidget(self.pose_set)
        self.main_layout.addWidget(self.pose_list)
        self.main_layout.addWidget(self.pose_control)
        
    def _update_lists(self):
        self.pose_list.refresh()
        
class PoseListWidget(QtGui.QWidget):
    
    pose_added = vtool.qt_ui.create_signal(object)
    
    #pose_added = QtCore.pyqtSignal(object)
 
    
    def __init__(self):
        super(PoseListWidget, self).__init__()
        
        self.main_layout = QtGui.QHBoxLayout()
        self.setLayout(self.main_layout)
        
        self.pose_list = PoseTreeWidget()
        combo_list = ComboTreeWidget()
        
        self.pose_list.itemSelectionChanged.connect(self.pose_list.select_pose)
        
        self.main_layout.addWidget(self.pose_list)
        self.main_layout.addWidget(combo_list)
        
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
        
    def view_mesh(self):
        self.pose_list.view_mesh()
        
    def change_mesh(self, int):
        self.pose_list.mesh_change(int)
        
    def change_axis(self, string):
        
        self.pose_list.axis_change(string)
        #if self.pose:
        #    self.pose.set_axis(text)
        
    def pose_reset(self):
        item = self.pose_list.currentItem()
        
        item.setSelected(False)
        
    def value_changed(self, max_angle, max_distance, twist_on, twist):
        
        self.pose_list.value_changed(max_angle, max_distance, twist_on, twist)
       
     
class BaseTreeWidget(vtool.qt_ui.TreeWidget):
    def __init__(self):
        super(BaseTreeWidget, self).__init__()
        self.setSortingEnabled(True)
        self.setSelectionMode(self.ExtendedSelection)
        
        self._populate_list()
        
        self.pose_widget = None

    def _edit_finish(self, item):
        item = super(BaseTreeWidget, self)._edit_finish(item)
        
        if not item:
            return
        
        new_name = str(item.text(0))
        
        new_name = new_name.replace(' ', '_')
        
        if not self.old_name == new_name:
            new_name = self.rename_pose(str(self.old_name), new_name)
        
        if self.old_name == new_name:
            new_name = None
        
        
        if new_name:
            item.setText(0, new_name)
        
        if not new_name and self.old_name:
            item.setText(0, self.old_name ) 


    def _populate_list(self):
        pass

    def _current_pose(self):
        item = self.currentItem()
        if item:
            return str(item.text(0))

    def _update_meshes(self, pose_name):
        
        pose = util.BasePoseControl()
        pose.set_pose(pose_name)
        meshes =  pose.get_target_meshes()
        
        self.pose_widget.update_meshes(meshes,pose.mesh_index)

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
    
    def refresh(self):
        self._populate_list()
        
    def create_pose(self):
        pass

    def rename_pose(self, pose_name, new_name):
        return util.PoseManager().rename_pose(str(pose_name), str(new_name))

    def add_mesh(self):
                  
        current_str = self.pose_widget.get_current_mesh()
        
        pose_name = self._current_pose()
            
        if not pose_name:
            return
        
        if current_str == '- new mesh -':
            
            util.PoseManager().add_mesh_to_pose(pose_name)
        
            self._update_meshes(pose_name)
            
        if not current_str == '- new mesh -':
            util.PoseManager().toggle_visibility(pose_name)
            
    def view_mesh(self):
        current_str = self.pose_widget.get_current_mesh()
        pose_name = self._current_pose()
        
        if not pose_name:
            return
        
        if not current_str == '- new mesh -':
            util.PoseManager().toggle_visibility(pose_name, True)
            
            
    def mesh_change(self, index):
        
        pose_name = self._current_pose()
        
        if not pose_name:
            return
        
        pose = util.PoseControl()
        pose.set_pose(pose_name)
        pose.set_mesh_index(index)
        
    def delete_pose(self):
        pose = self._current_pose()
        item = self.currentItem()
        
        if not pose:
            return
        
        util.PoseManager().delete_pose(pose)
        
        index = self.indexOfTopLevelItem(item)
        self.takeTopLevelItem(index)
        del(item)
        
    def select_pose(self):
        pass
        
class PoseTreeWidget(BaseTreeWidget):

    def __init__(self):
        super(PoseTreeWidget, self).__init__()
        self.setHeaderLabels(['pose'])
        
        self.last_selection = []
    
    def _populate_list(self):
        
        self.clear()
        
        poses = util.PoseManager().get_poses()
        
        if not poses:
            return
        
        for pose in poses:
            self.create_pose(pose)
        
    def _get_pose_values(self, pose):
        max_angle = cmds.getAttr('%s.maxAngle' % pose)
        max_distance = cmds.getAttr('%s.maxDistance' % pose)
        twist_on = cmds.getAttr('%s.twistOffOn' % pose)
        twist = cmds.getAttr('%s.maxTwist' % pose)
        
        return max_angle, max_distance, twist_on, twist
        
    def create_pose(self, name = None):
        pose_names = self._get_selected_items(True)
        
        
        #if len(pose_names) > 1:
        #    util.PoseManager().create_combo(pose_names, 'combo')
        #    return
        
        
        pose = None
        
        if name:
            pose = name
        
        if not pose:
            pose = util.PoseManager().create_pose()
        
        if not pose:
            return
        
        item = QtGui.QTreeWidgetItem()
        item.setText(0, pose)
        self.addTopLevelItem(item)
        

    def mirror_pose(self):
        
        pose = self._current_pose()
        item = self.currentItem()
        
        if not pose:
            return
        
        mirror = util.PoseManager().mirror_pose(pose)
        
        self.refresh()
        self.select_pose(mirror)
        
        #items = self.findItems(mirror, Qt.QMatchFlags(0), 0)
        
        #self.setItemSelected(item, True)
        
    def axis_change(self, string):
        pose_name = self._current_pose()
        
        if not pose_name:
            return
        
        pose = util.PoseControl()
        pose.set_pose(pose_name)
        pose.set_axis(string)
        
    def select_pose(self, pose_name = None):
        
        if self.last_selection:
            util.PoseManager().visibility_off(self.last_selection[0])
        
        
        pose_names = self._get_selected_items(get_names = True)
        
        
        
        if len( pose_names ) > 1:
            
            util.PoseManager().set_poses(pose_names)
            
            values = self._get_pose_values(pose_names[0])
            
            self.pose_widget.set_values(values[0], values[1], values[2], values[3])
            return
        
        if len( pose_names ) == 1:
            pose = pose_names[0]
            
            #cmds.select(pose)
            util.PoseManager().set_pose(pose)
            self._update_meshes(pose)
            
            values = self._get_pose_values(pose)
            
            self.pose_widget.set_values(values[0], values[1], values[2], values[3])
            
        self.last_selection = pose_names
            
    def value_changed(self, max_angle, max_distance, twist_on, twist):
        poses = self._get_selected_items(True)
        
        if not poses:
            return
        
        cmds.setAttr('%s.maxAngle' % poses[-1], max_angle)
        cmds.setAttr('%s.maxDistance' % poses[-1], max_distance)
        cmds.setAttr('%s.maxTwist' % poses[-1], twist)
        cmds.setAttr('%s.twistOffOn' % poses[-1], twist_on)
        
class ComboTreeWidget(BaseTreeWidget):
    def __init__(self):
        super(ComboTreeWidget, self).__init__()
        self.setHeaderLabels(['combo'])
        
class PoseTreeItem(QtGui.QTreeWidgetItem):
    def __init__(self, name):
        super(PoseTreeItem, self).__init__()
        
        self.pose = None
        
        self.setText(0, name)
        
    def _rename(self, new_name):
        if self.pose.rename(new_name):
            return self.pose.pose_control
        
    def load_pose(self, pose):
        if not util.PoseControl().is_a_pose(pose):
            return
    
        #self.pose = util.PoseControl()
        #self.pose.set_pose(pose)
        #self.pose.select()
        

class PoseControlWidget(vtool.qt_ui.BasicWidget):
    
    pose_create = vtool.qt_ui.create_signal()  
    pose_delete = vtool.qt_ui.create_signal()
    pose_mirror = vtool.qt_ui.create_signal() 
    pose_mesh = vtool.qt_ui.create_signal()
    pose_mesh_view = vtool.qt_ui.create_signal()
    axis_change = vtool.qt_ui.create_signal(object)
    mesh_change = vtool.qt_ui.create_signal(object)
    
    value_changed = vtool.qt_ui.create_signal(object, object, object, object)
    
    def __init__(self):
        
        super(PoseControlWidget, self).__init__()
        
        self.pose = None
        
    def _define_main_layout(self):
        layout = QtGui.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)
        return QtGui.QVBoxLayout()
        
    def _build_widgets(self):
        
        self.layout_pose = QtGui.QHBoxLayout()
        
        button_create = QtGui.QPushButton('create')
        button_delete = QtGui.QPushButton('delete')
        button_mirror = QtGui.QPushButton('mirror')
        
        self.combo_axis = QtGui.QComboBox()
        self.combo_axis.addItems(['X','Y','Z'])
        
        button_create.clicked.connect(self._button_create)
        button_delete.clicked.connect(self._button_delete)
        button_mirror.clicked.connect(self._button_mirror)
        
        
        self.layout_pose.addWidget(button_create)
        self.layout_pose.addWidget(button_delete)
        self.layout_pose.addWidget(button_mirror)
        self.layout_pose.addWidget(self.combo_axis)
        
        layout_slide = QtGui.QVBoxLayout()
        
        layout_angle, self.max_angle = self._add_spin_widget('max angle')
        layout_distance, self.max_distance = self._add_spin_widget('max distance')
        layout_twist, self.twist = self._add_spin_widget('max twist')
        layout_twist_on, self.twist_on = self._add_spin_widget('twist')
        
        self.max_angle.setRange(0, 180)
        
        self.twist.setRange(0, 180)
        self.twist_on.setRange(0,1)
        self.max_distance.setMinimum(0)
        self.max_distance.setMaximum(10000000)
        
        
        self.max_angle.valueChanged.connect(self._value_changed)
        self.max_distance.valueChanged.connect(self._value_changed)
        self.twist_on.valueChanged.connect(self._value_changed)
        self.twist.valueChanged.connect(self._value_changed)
        
        layout_slide.addLayout(layout_angle)
        layout_slide.addLayout(layout_twist)
        layout_slide.addLayout(layout_distance)
        layout_slide.addLayout(layout_twist_on)
        
        
        self.layout_mesh = QtGui.QHBoxLayout()
        button_mesh = QtGui.QPushButton('mesh')
        button_view = QtGui.QPushButton('view')
        self.combo_mesh = QtGui.QComboBox()
        self.update_meshes()
        self.combo_mesh.currentIndexChanged.connect(self._mesh_change)
        self.combo_axis.currentIndexChanged.connect(self._axis_change)
        
        button_mesh.clicked.connect(self._button_mesh)
        button_view.clicked.connect(self._button_view)
        
        self.layout_mesh.addWidget(button_mesh)
        self.layout_mesh.addWidget(button_view)
        self.layout_mesh.addWidget(self.combo_mesh)
        
        self.main_layout.addLayout(self.layout_pose)
        self.main_layout.addLayout(layout_slide)
        self.main_layout.addLayout(self.layout_mesh)
        
    def _add_spin_widget(self, name):
        layout = QtGui.QHBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0,0,0,0)
        
        label = QtGui.QLabel(name)
        label.setAlignment(QtCore.Qt.AlignRight)
        
        widget = QtGui.QDoubleSpinBox()
        
        widget.setCorrectionMode(widget.CorrectToNearestValue)
        widget.setWrapping(False)
        layout.addWidget(label)
        layout.addWidget(widget)
        
        return layout, widget      
        
    def _button_create(self):
        
        self.pose_create.emit()
        
    def _button_delete(self):

        self.pose_delete.emit()

    def _button_mirror(self):
        self.pose_mirror.emit()

    def _button_mesh(self):
        self.pose_mesh.emit()
        
    def _button_view(self):
        self.pose_mesh_view.emit()
        
    def _axis_change(self):
        
        text = str( self.combo_axis.currentText() )
        self.axis_change.emit(text)
        
       
    def _mesh_change(self, int):
        
        self.mesh_change.emit(int)
       
    def _value_changed(self):
        max_angle = self.max_angle.value()
        max_distance = self.max_distance.value()
        twist_on = self.twist_on.value()
        twist = self.twist.value()
        
        self.value_changed.emit(max_angle, max_distance, twist_on, twist)
        
        
    def get_current_mesh(self):
        return str( self.combo_mesh.currentText() )
        
    def update_meshes(self, meshes = [], index = 0):    
        self.combo_mesh.clear()
        
        if meshes:
            self.combo_mesh.addItems(meshes)
            
        self.combo_mesh.addItem('- new mesh -')
        self.combo_mesh.setCurrentIndex(index)
        
    def set_values(self, angle, distance, twist_on, twist):
        
        self.max_angle.setValue(angle)
        self.max_distance.setValue(distance)
        self.twist_on.setValue(twist_on)
        self.twist.setValue(twist)

class PoseSetWidget(QtGui.QWidget): 
    
    pose_reset = vtool.qt_ui.create_signal()
    
    def __init__(self):
        
        super(PoseSetWidget, self).__init__()
        
        self.main_layout = QtGui.QHBoxLayout()
        self.setLayout(self.main_layout)
        self.main_layout.setAlignment(QtCore.Qt.AlignTop)
            
        self._add_buttons()
        
        self.pose = None
        
    def _add_buttons(self):
        
        name_layout = QtGui.QHBoxLayout()
        
        button_default = QtGui.QPushButton('set default pose')
        button_reset = QtGui.QPushButton('reset')
        
        button_default.clicked.connect(self._button_default)
        button_reset.clicked.connect(self._button_reset)
        
        self.main_layout.addWidget(button_default)
        self.main_layout.addWidget(button_reset)
        
    def _button_default(self):
        util.PoseManager().set_default_pose()
    
    def _button_reset(self):
        self.pose_reset.emit()
        util.PoseManager().set_pose_to_default()
        

