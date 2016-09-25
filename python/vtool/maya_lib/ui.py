# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

import maya.cmds as cmds

import maya.OpenMayaUI as OpenMayaUI
import maya.mel as mel
import maya.utils

import vtool.qt_ui

from vtool.process_manager import ui_process_manager

import core
import attr
import space
import geo
import deform
import rigs_util

#import util
if vtool.qt_ui.is_pyqt():
    from PyQt4 import QtCore, Qt, uic
    from PyQt4.QtGui import *
if vtool.qt_ui.is_pyside():
    from PySide import QtCore
    from PySide.QtGui import *
if vtool.qt_ui.is_pyside2():
    from PySide2 import QtCore
    from PySide2.QtGui import *
    from PySide2.QtWidgets import *
    

#--- signals

class new_scene_object(QtCore.QObject):
    signal = vtool.qt_ui.create_signal()

class open_scene_object(QtCore.QObject):
    signal = vtool.qt_ui.create_signal()
    
class read_scene_object(QtCore.QObject):
    signal = vtool.qt_ui.create_signal()

        
new_scene_signal = new_scene_object()
open_scene_signal = open_scene_object()
read_scene_signal = read_scene_object()

def emit_new_scene_signal():
    new_scene_signal.signal.emit()

def emit_open_scene_signal():
    new_scene_signal.signal.emit()
    
def emit_read_scene_signal():
    read_scene_signal.signal.emit()

#--- script jobs
job_new_scene = None
job_open_scene = None
job_read_scene = None

def create_scene_script_jobs():
    
    global job_new_scene
    global job_open_scene
    global job_read_scene
    
    job_new_scene = cmds.scriptJob( event = ['NewSceneOpened', 'from vtool.maya_lib import ui;ui.emit_new_scene_signal();print "V:\t\tEmit new scene."'], protected = False)
    job_open_scene = cmds.scriptJob( event = ['SceneOpened', 'from vtool.maya_lib import ui;ui.emit_open_scene_signal();print "V:\t\tEmit open scene."'], protected = False)
    job_read_scene = cmds.scriptJob( ct = ['readingFile', 'from vtool.maya_lib import ui;ui.emit_read_scene_signal();print "V:\t\tEmit reading scene."'], protected = False)

create_scene_script_jobs()
  
def delete_scene_script_jobs():
    
    global job_new_scene
    global job_open_scene
    global job_read_scene
    
    cmds.scriptJob(kill = job_new_scene)
    cmds.scriptJob(kill = job_open_scene)
    cmds.scriptJob(kill = job_read_scene)
    
#--- ui 

def get_maya_window():
    
    if vtool.qt_ui.is_pyqt():
        import sip
        #Get the maya main window as a QMainWindow instance
        ptr = OpenMayaUI.MQtUtil.mainWindow()
        return sip.wrapinstance(long(ptr), QtCore.QObject)
    
    if vtool.qt_ui.is_pyside():
        try:
            from shiboken import wrapInstance
        except:
            from PySide.shiboken import wrapInstance
    
    if vtool.qt_ui.is_pyside2():
        from shiboken2 import wrapInstance
             
    maya_window_ptr = OpenMayaUI.MQtUtil.mainWindow()
    return wrapInstance(long(maya_window_ptr), QWidget)

def create_window(ui, dock_area = 'right'): 
    
    
    
    ui_name = str(ui.objectName())
    dock_name = '%sDock' % ui_name
    dock_name = dock_name.replace(' ', '_')
    dock_name = dock_name.replace('-', '_')
    
    path = 'MayaWindow|%s' % dock_name
    
    if cmds.dockControl(path,ex = True):
        cmds.deleteUI(dock_name, control = True)
        ui.close()
        
    allowedAreas = ['right', 'left']
    
    #do not remove
    vtool.util.show('Creating dock window.', ui_name)
    
    #this was needed to have the ui predictably load. 
    mel.eval('updateRendererUI;')
    
    try:
        cmds.dockControl(dock_name,aa=allowedAreas, a = dock_area, content=ui_name, label=ui_name, w=350, fl = False, visible = True)
        ui.show()
    
    except:
        #do not remove
        vtool.util.warning('%s window failed to load. Maya may need to finish loading.' % ui_name)
        
    
def pose_manager(shot_sculpt_only = False):
    import ui_corrective
    
    window = ui_corrective.PoseManager(shot_sculpt_only)
    
    if ToolManager._last_instance:
        ToolManager._last_instance.add_tab(window, window.title)
    
    if not ToolManager._last_instance:
        create_window(window)

def shape_combo():
    
    import ui_shape_combo
    window = ui_shape_combo.ComboManager()
    
    if ToolManager._last_instance:
        ToolManager._last_instance.add_tab(window, window.title)
    
    if not ToolManager._last_instance:
        create_window(window)
    
def picker():
    
    import ui_picker
    window = ui_picker.PickManager()
    
    if ToolManager._last_instance:
        ToolManager._last_instance.add_tab(window, window.title)
    
    if not ToolManager._last_instance:
        create_window(window)
    
    
def character_manager():
    
    import ui_character
    create_window(ui_character.CharacterManager())
    
def tool_manager(name = None, directory = None):
    
    manager = ToolManager(name)
    manager.set_directory(directory)
    
    funct = lambda : create_window(manager)
    
    maya.utils.executeDeferred(funct)
    
    return manager

def process_manager(directory = None):
    
    window = ProcessMayaWindow()
    
    if ToolManager._last_instance:
        ToolManager._last_instance.add_tab(window, 'VETALA')
    
    if not ToolManager._last_instance:
        funct = lambda : create_window(window)
        maya.utils.executeDeferred(funct)
    
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
    
vetala_version = vtool.util_file.get_vetala_version()
    
class ToolManager(MayaDirectoryWindow):
    title = 'VETALA  HUB'
    
    def __init__(self, name = None):
        if name:
            self.title = name
    
        super(ToolManager, self).__init__()
        
    def _build_widgets(self):
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(self.tab_widget.West)
        
        #self.modeling_widget = ModelManager()
        self.rigging_widget = RigManager()
        self.animation_widget = AnimationManager()
        #self.shot_widget = QWidget()
        
        #temporary
        #self.tab_widget.addTab(self.animation_widget, 'ANIMATION')
        self.tab_widget.addTab(self.rigging_widget, 'RIG')
        
        self.tab_widget.setCurrentIndex(1)
        
        self.tab_widget.setMovable(True)
        self.tab_widget.setTabsClosable(True)
        
        
        
        version = QLabel('%s' % vtool.util_file.get_vetala_version())
        self.main_layout.addWidget(version)
        self.main_layout.addWidget(self.tab_widget)
        
        self.tab_widget.tabBar().tabButton(0, QTabBar.RightSide).hide()
        
        #temporary
        #self.tab_widget.tabBar().tabButton(1, QTabBar.RightSide).hide()
        
        self.tab_widget.tabCloseRequested.connect(self._close_tab)
        
    def _close_tab(self, index):
        
        self.tab_widget.removeTab(index)
        
    def add_tab(self, widget, name):
        
        tab_count = self.tab_widget.count()
        
        for inc in range(0, tab_count):
            tab_title = self.tab_widget.tabText(inc)
            
            if tab_title == name:
                self.tab_widget.removeTab(inc)
                break
                
        self.tab_widget.addTab(widget, name)
        
        tab_count = self.tab_widget.count()
            
        self.tab_widget.setCurrentIndex( (tab_count-1) )
        
    def set_directory(self, directory):
        super(ToolManager, self).set_directory(directory)
        self.rigging_widget.set_directory(directory)
     
class LightManager(vtool.qt_ui.BasicWidget):
    pass
     
class ModelManager(vtool.qt_ui.BasicWidget):
    def _build_widgets(self):
        pass

class AnimationManager(vtool.qt_ui.BasicWidget):
    def _build_widgets(self):
        manager_group = QGroupBox('Applications')
        manager_layout = QVBoxLayout()
        manager_layout.setContentsMargins(2,2,2,2)
        manager_layout.setSpacing(2)
        manager_layout.setAlignment(QtCore.Qt.AlignCenter)
        
        manager_group.setLayout(manager_layout)
        
        character_button = QPushButton('Character Manager')
        character_button.clicked.connect(self._character_manager)
        
        manager_layout.addWidget(character_button)
        
        self.main_layout.addWidget(manager_group)
        
    def _character_manager(self):
        
        character_manager()
        
class RigManager(vtool.qt_ui.DirectoryWidget):
    
    def __init__(self):
        super(RigManager, self).__init__()
        
        self.scale_controls = []
        self.last_scale_value = None
        self.last_scale_center_value = None
    
    def _build_widgets(self):
        
        manager_group = QGroupBox('Applications')
        manager_layout = QVBoxLayout()
        manager_layout.setContentsMargins(2,2,2,2)
        manager_layout.setSpacing(2)
        manager_layout.setAlignment(QtCore.Qt.AlignCenter)
        
        manager_group.setLayout(manager_layout)
        
        button_width = 200        
        
        process_button = QPushButton('VETALA')
        process_button.clicked.connect(self._process_manager)
        process_button.setMinimumWidth(button_width)
        manager_layout.addWidget(process_button)
        
        pose_button = QPushButton('Correctives')
        pose_button.clicked.connect(self._pose_manager)
        pose_button.setMinimumWidth(button_width)
        manager_layout.addWidget(pose_button)
        
        shape_combo_button = QPushButton('Shape Combos')
        shape_combo_button.clicked.connect(self._shape_combo)
        shape_combo_button.setMinimumWidth(button_width)
        manager_layout.addWidget(shape_combo_button)
        
        
        picker_button = QPushButton('Picker')
        picker_button.clicked.connect(self._picker)
        picker_button.setMinimumWidth(button_width)
        manager_layout.addWidget(picker_button)
        
        
        tool_group = QGroupBox('Utilities')
        tool_layout = QVBoxLayout()
        tool_layout.setContentsMargins(2,2,2,2)
        tool_layout.setSpacing(2)
        tool_group.setLayout(tool_layout)
        
        tool_tab = QTabWidget()
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
        
        add_orient = QPushButton('Add Orient')
        add_orient.setMaximumWidth(80)
        add_orient.setToolTip('select joints')
        orient_joints = QPushButton('Orient Joints')
        orient_joints.setMinimumHeight(40)
        
        mirror = QPushButton('Mirror Transforms')
        mirror.setMinimumHeight(40)
        
        #match_joints = QPushButton('Match')
        #match_joints.setMinimumHeight(40)
        
        joints_on_curve = vtool.qt_ui.GetIntNumberButton('create joints on curve')
        joints_on_curve.set_value(10)
        
        snap_to_curve = vtool.qt_ui.GetIntNumberButton('snap joints to curve')
        
        transfer_joints = QPushButton('transfer joints')
        transfer_process = QPushButton('transfer process weights to parent')
        
        self.joint_axis_check = QCheckBox('joint axis visibility')
        
        mirror_invert = QPushButton('Mirror Invert')
        mirror_invert.clicked.connect(self._mirror_invert)
        
        
        add_orient.clicked.connect(self._add_orient)
        orient_joints.clicked.connect(self._orient)
        mirror.clicked.connect(self._mirror)
        #match_joints.clicked.connect(self._match_joints)
        joints_on_curve.clicked.connect(self._joints_on_curve)
        snap_to_curve.clicked.connect(self._snap_joints_to_curve)
        transfer_joints.clicked.connect(self._transfer_joints)
        transfer_process.clicked.connect(self._transfer_process)
        self.joint_axis_check.stateChanged.connect(self._set_joint_axis_visibility)
        
        main_layout = parent.main_layout
        
        orient_layout = QHBoxLayout()
        orient_layout.addWidget(orient_joints)
        orient_layout.addWidget(add_orient)
        
        main_layout.addSpacing(20)
        #main_layout.addWidget(add_orient)
        main_layout.addWidget(mirror)
        main_layout.addLayout(orient_layout)
        main_layout.addWidget(mirror_invert)
        main_layout.addSpacing(20)
        main_layout.addWidget(self.joint_axis_check)
        
        main_layout.addSpacing(20)
        #main_layout.addWidget(orient_joints)
        #main_layout.addWidget(match_joints)
        main_layout.addWidget(subdivide_joint_button)
        main_layout.addWidget(joints_on_curve)
        main_layout.addWidget(snap_to_curve)
        main_layout.addWidget(transfer_joints)
        main_layout.addWidget(transfer_process)
        
        
        
    def _match_joints(self):
        space.match_joint_xform('joint_', 'guideJoint_')
        space.match_orient('joint_', 'guideJoint_')
        
    def _create_control_widgets(self, parent):
        
        mirror_control = QPushButton('Mirror Control')
        mirror_control.clicked.connect(self._mirror_control)
        
        mirror_controls = QPushButton('Mirror Controls')
        mirror_controls.clicked.connect(self._mirror_controls)
        mirror_controls.setMinimumHeight(40)
        
        size_slider = vtool.qt_ui.Slider('Scale Controls at Pivot')
        size_slider.value_changed.connect(self._scale_control)
        size_slider.slider.setRange(-200, 200)
        size_slider.set_auto_recenter(True)
        size_slider.slider.sliderReleased.connect(self._reset_scale_slider)
        
        size_center_slider = vtool.qt_ui.Slider('Scale Controls at Center')
        size_center_slider.value_changed.connect(self._scale_center_control)
        size_center_slider.slider.setRange(-200, 200)
        size_center_slider.set_auto_recenter(True)
        size_center_slider.slider.sliderReleased.connect(self._reset_scale_center_slider)
        
        number_button = vtool.qt_ui.GetNumberButton('Global Size Controls')
        number_button.set_value(2)
        number_button.clicked.connect(self._size_controls)
        self.scale_control_button = number_button
        
        self.fix_sub_controls = QPushButton('Fix Sub Controls')
        self.fix_sub_controls.clicked.connect(rigs_util.fix_sub_controls)
        
        project_curve = vtool.qt_ui.GetNumberButton('Project Curves on Mesh')
        project_curve.set_value(1)
        project_curve.set_value_label('Offset')
        project_curve.clicked.connect(self._project_curve)
        
        snap_curve = vtool.qt_ui.GetNumberButton('Snap Curves to Mesh')
        snap_curve.set_value(1)
        snap_curve.set_value_label('Offset')
        snap_curve.clicked.connect(self._snap_curve)
        
        
        
        
        parent.main_layout.addWidget(mirror_control)
        parent.main_layout.addWidget(mirror_controls)
        
        parent.main_layout.addWidget(self.fix_sub_controls)
        parent.main_layout.addWidget(number_button)
        parent.main_layout.addWidget(size_slider)
        parent.main_layout.addWidget(size_center_slider)
        
        parent.main_layout.addWidget(project_curve)
        parent.main_layout.addWidget(snap_curve)
        
    def _create_deformation_widgets(self, parent):
        corrective_button = QPushButton('Create Corrective')
        corrective_button.setToolTip('select deformed mesh then fixed mesh')
        corrective_button.clicked.connect(self._create_corrective)
        
        skin_mesh_from_mesh = QPushButton('Skin Mesh From Mesh')
        skin_mesh_from_mesh.clicked.connect(self._skin_mesh_from_mesh)
        
        parent.main_layout.addWidget(corrective_button)
        parent.main_layout.addWidget(skin_mesh_from_mesh)
            
    def _pose_manager(self):
        pose_manager()
        
    def _process_manager(self):
        process_manager(self.directory)

    def _shape_combo(self):
        shape_combo()

    def _picker(self):
        picker()

    def _create_corrective(self):
        
        selection = cmds.ls(sl = True)
        
        deform.chad_extract_shape(selection[0], selection[1])
    
    def _skin_mesh_from_mesh(self):
        selection = cmds.ls(sl = True)
        deform.skin_mesh_from_mesh(selection[0], selection[1])
    
    def _subdivide_joint(self, number):
        space.subdivide_joint(count = number)
        
    def _add_orient(self):
        selection = cmds.ls(sl = True, type = 'joint')
        
        attr.add_orient_attributes(selection)
        
    def _orient(self):
        space.orient_attributes()
        
    @core.undo_chunk
    def _mirror(self, *args ):
        #*args is for probably python 2.6, which doesn't work unless you have a key argument.
        
        rigs_util.mirror_curve('curve_')
        space.mirror_xform()
        #util.mirror_xform('guideJoint_')
        #util.mirror_xform('process_')
        #util.mirror_xform(string_search = 'lf_')
        
        #not sure when this was implemented... but couldn't find it, needs to be reimplemented.
        #util.mirror_curve(suffix = '_wire')
        
    @core.undo_chunk
    def _mirror_invert(self):
        
        selection = cmds.ls(sl = True)
        
        for thing in selection:
            space.mirror_invert(thing)
        
        
        
    def _mirror_control(self):
        
        selection = cmds.ls(sl = True)
        rigs_util.mirror_control(selection[0])
        
    def _mirror_controls(self):
        
        rigs_util.mirror_controls()
    
        
    def _joints_on_curve(self, count):
        selection = cmds.ls(sl = True)
        
        
        geo.create_oriented_joints_on_curve(selection[0], count)
         
    def _snap_joints_to_curve(self, count):
        
        scope = cmds.ls(sl = True)
        
        if not scope:
            return
        
        node_types = core.get_node_types(scope)
        
        joints = []
        
        if node_types.has_key('joint'):
            joints = node_types['joint']
        
        curve = None
        if 'nurbsCurve' in node_types:
            curves = node_types['nurbsCurve']
            curve = curves[0]
            
        if joints:
            geo.snap_joints_to_curve(joints, curve, count)
        
        
    def _transfer_joints(self):
        
        scope = cmds.ls(sl = True)
        
        node_types = core.get_node_types(scope)
        
        if not scope or len(scope) < 2:
            return
        
        meshes = node_types['mesh']
        
        if len(meshes) < 2:
            return
        
        mesh_source = meshes[0]
        mesh_target = meshes[1]
        
        locators = cmds.ls('*_locator', type = 'transform')
        ac_joints = cmds.ls('ac_*', type = 'joint')
        sk_joints = cmds.ls('sk_*', type = 'joint')
        
        guideJoints = cmds.ls('guideJoint_*', type = 'joint')
        joints = cmds.ls('joint_*', type = 'joint')
        
        joints = guideJoints + joints + ac_joints + locators + sk_joints
        
        if not joints:
            return
        
        transfer = deform.XformTransfer()
        transfer.set_scope(joints)
        transfer.set_source_mesh(mesh_source)
        transfer.set_target_mesh(mesh_target)
        
        transfer.run()
        
    def _transfer_process(self):
        
        selection = cmds.ls(sl = True)
        
        if not selection:
            return
        
        node_types = core.get_node_types(selection)
        
        if not 'mesh' in node_types:
            return
        
        meshes = node_types['mesh']
        
        
        for mesh in meshes:
            rigs_util.process_joint_weight_to_parent(mesh)
            
     
    def _set_joint_axis_visibility(self):
        
        bool_value = self.joint_axis_check.isChecked()
        
        rigs_util.joint_axis_visibility(bool_value)
        
    def _reset_scale_slider(self):
        
        self.scale_controls = []
        
        cmds.undoInfo(closeChunk = True)

    def _reset_scale_center_slider(self):
        
        self.scale_center_controls = []
        self.last_scale_center_value = None
        
        cmds.undoInfo(closeChunk = True)
        
    def _get_components(self, thing):
        
        shapes = core.get_shapes(thing)
        
        return core.get_components_from_shapes(shapes)
        
    def _size_controls(self):
        
        value = self.scale_control_button.get_value()
        rigs_util.scale_controls(value)
    
    def _scale_control(self, value):
        
        if self.last_scale_value == None:
            self.last_scale_value = 0
            cmds.undoInfo(openChunk = True)
        
        if value == self.last_scale_value:
            return
        
        if value > self.last_scale_value:
            pass_value = 1.02
        
        if value < self.last_scale_value:
            pass_value = .99
            
        
        things = geo.get_selected_curves()
        
        if not things:
            return
            
        if things:
            for thing in things:
                
                components = self._get_components(thing)
        
                pivot = cmds.xform( thing, q = True, rp = True, ws = True)
        
                if components:
                    cmds.scale(pass_value, pass_value, pass_value, components, p = pivot, r = True)
                
        self.last_scale_value = value   
        
    def _scale_center_control(self, value):
        
        if self.last_scale_center_value == None:
            self.last_scale_center_value = 0
            cmds.undoInfo(openChunk = True)
        
        if value == self.last_scale_center_value:
            return
        
        if value > self.last_scale_center_value:
            pass_value = 1.02
        
        if value < self.last_scale_center_value:
            pass_value = .99
            
        
        things = geo.get_selected_curves()
        
        if not things:
            return
            
        if things:
            for thing in things:
                
                shapes = core.get_shapes(thing, shape_type = 'nurbsCurve')
                components = core.get_components_from_shapes(shapes)
            
                bounding = space.BoundingBox(components)
                pivot = bounding.get_center()
                
                if components:
                    cmds.scale(pass_value, pass_value, pass_value, components, pivot = pivot, r = True)
                
        self.last_scale_center_value = value      
        
    @core.undo_chunk
    def _project_curve(self, value):
        
        curves = geo.get_selected_curves()
        meshes = geo.get_selected_meshes()
        
        for curve in curves:
            geo.snap_project_curve_to_surface(curve, meshes[0], value)
    @core.undo_chunk
    def _snap_curve(self, value):
        
        
        curves = geo.get_selected_curves()
        meshes = geo.get_selected_meshes()
        
        for curve in curves:
            geo.snap_curve_to_surface(curve, meshes[0], value)
