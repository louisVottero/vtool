# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

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
    dockName = dockName.replace(' ', '_')
    
    path = 'MayaWindow|%s' % dockName
    
    if cmds.dockControl(path,ex = True):    
        cmds.deleteUI(dockName, control = True)
        
    allowedAreas = ['right', 'left']
    
    cmds.dockControl(dockName,aa=allowedAreas, a = dock_area, content=ui_name, label=ui_name, w=350, fl = False, visible = True)
    
    ui.show()

def pose_manager():
    import ui_corrective
    create_window(ui_corrective.PoseManager())
    
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
        
    @util.undo_chunk
    def _mirror(self, *args ):
        #*args is for probably python 2.6, which doesn't work unless you have a key argument.
        
        
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



