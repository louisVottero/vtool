# Copyright (C) 2016 Louis Vottero louis.vot@gmail.com    All rights reserved.

from vtool import qt_ui, qt


from vtool import util_file
    
import maya.cmds as cmds

from vtool.maya_lib import ui_core
import ui_check
import ui_presets
import ui_picker
import ui_model
import ui_anim

from vtool.maya_lib import core
from vtool.maya_lib import geo
from vtool.maya_lib import attr    
from vtool.maya_lib import space
from vtool.maya_lib import deform
from vtool.maya_lib import rigs_util
from vtool.process_manager import ui_process_manager

def pose_manager(shot_sculpt_only = False):
    from vtool.maya_lib.ui_lib import ui_corrective
    
    window = ui_corrective.PoseManager(shot_sculpt_only)
    
    return window

def shape_combo():
    
    from vtool.maya_lib.ui_lib import ui_shape_combo
    window = ui_shape_combo.ComboManager()
    
    return window
    
def checker():
    
    window = ui_check.CheckView()
    window.add_check(ui_check.Check_Empty_Groups())
    window.add_check(ui_check.Check_Empty_Intermediate_Objects())
    window.add_check(ui_check.Check_Empty_Nodes())
    window.add_check(ui_check.Check_Non_Default_Transforms())
    window.add_check(ui_check.Check_Non_Unique())
    window.add_check(ui_check.Check_Triangles())
    window.add_check(ui_check.Check_NSided())
    
    
    return window
    
def picker():
    
    
    window = ui_picker.PickManager()
    
    return window
    

def process_manager():
    
    window = ProcessMayaWindow()
    
    return window

def presets():
    
    window = ui_presets.Presets()
    
    return window


class ProcessMayaWindow(ui_process_manager.ProcessManagerWindow):
    
    def __init__(self):
        super(ProcessMayaWindow, self).__init__( ui_core.get_maya_window() )
    
vetala_version = util_file.get_vetala_version()
    
class RigManager(qt_ui.DirectoryWidget):
    
    def __init__(self):
        super(RigManager, self).__init__()
        
        self.scale_controls = []
        self.last_scale_value = None
        self.last_scale_center_value = None
    
    def _build_widgets(self):
        
        self.main_layout.setContentsMargins(10,10,10,10)
        
        manager_group = qt.QGroupBox('Applications')
        manager_group.setFlat(True)
        manager_layout = qt.QVBoxLayout()
        manager_layout.setContentsMargins(10,10,10,10)
        manager_layout.setSpacing(2)
        manager_layout.setAlignment(qt.QtCore.Qt.AlignCenter)
        
        manager_group.setLayout(manager_layout)
        
        button_width = 150        
        
        manager_layout.addSpacing(15)
        
        h_layout = qt.QHBoxLayout()
        other_buttons_layout = qt.QVBoxLayout()
        
        manager_layout.addLayout(h_layout)
        
        
        process_button = qt.QPushButton('VETALA')
        process_button.clicked.connect(self._process_manager)
        process_button.setMinimumWidth(button_width)
        process_button.setToolTip('Manage and rebuild rigs.')
        manager_layout.addWidget(process_button)
        
        h_layout.addWidget(process_button)
        h_layout.addSpacing(15)
        h_layout.addLayout(other_buttons_layout)
        
        pose_button = qt.QPushButton('Correctives')
        pose_button.clicked.connect(self._pose_manager)
        pose_button.setMinimumWidth(button_width)
        pose_button.setToolTip('Create correctives on meshes deformed by a rig.')
        other_buttons_layout.addWidget(pose_button)
        
        
        
        shape_combo_button = qt.QPushButton('Shape Combos')
        shape_combo_button.clicked.connect(self._shape_combo)
        shape_combo_button.setMinimumWidth(button_width)
        shape_combo_button.setToolTip('Create combo shapes for use in facial setups.')
        other_buttons_layout.addWidget(shape_combo_button)
        
        
        
        
        #manager_layout.addSpacing(15)
        
        check_button = qt.QPushButton('Checks - ALPHA')
        check_button.clicked.connect(self._checker)
        check_button.setMinimumWidth(button_width)
        
        other_buttons_layout.addWidget(check_button)
        
        picker_button = qt.QPushButton('Picker - ALPHA')
        picker_button.clicked.connect(self._picker)
        picker_button.setMinimumWidth(button_width)
        picker_button.setToolTip('Create a picker for the character that gets stored on "picker_gr" node.')
        #removed indefinitly
        #manager_layout.addWidget(picker_button)
        
        
        
        presets_button = qt.QPushButton('Presets - ALPHA')
        presets_button.clicked.connect(self._presets)
        presets_button.setMinimumWidth(button_width)
        presets_button.setToolTip('Presets creates a node in Maya called "presets" that stores attribute values. Values can be read from referenced assets in the FX tab.')
        #removed indefinitly
        #manager_layout.addWidget(presets_button)
        
        
        manager_layout.addSpacing(15)
        
        tool_group = qt_ui.Group('Utilities')
        tool_group.setFlat(True)
        
        tool_tab = qt.QTabWidget()
        
        deformation_widget = qt_ui.BasicWidget()
        structure_widget = qt_ui.BasicWidget()
        control_widget = qt_ui.BasicWidget()
        tool_group.main_layout.addWidget(tool_tab)
        
        deformation_widget.main_layout.setContentsMargins(10,10,10,10)
        structure_widget.main_layout.setContentsMargins(10,10,10,10)
        control_widget.main_layout.setContentsMargins(10,10,10,10)
        
        tool_tab.addTab(structure_widget, 'Structure')
        tool_tab.addTab(control_widget, 'Controls')
        tool_tab.addTab(deformation_widget, 'Deform')
        tool_tab.addTab(ui_model.ModelManager(), 'Model')
        tool_tab.addTab(ui_anim.AnimationManager(), 'Animate')
        
        self._create_structure_widgets(structure_widget)
        self._create_control_widgets(control_widget)
        self._create_deformation_widgets(deformation_widget)
        
        self.main_layout.addWidget(manager_group)
        self.main_layout.addSpacing(15)
        self.main_layout.addWidget(tool_group)
        
        self.main_layout.setAlignment(qt.QtCore.Qt.AlignTop)
        
        
    def _create_structure_widgets(self, parent):
        
        subdivide_joint_button =  qt_ui.GetIntNumberButton('Subdivide Joint')
        subdivide_joint_button.set_value(1)
        subdivide_joint_button.clicked.connect(self._subdivide_joint)
        subdivide_joint_button.setToolTip('select parent and child joint')
        
        add_orient = qt.QPushButton('Add Orient')
        #add_orient.setMaximumWidth(140)
        add_orient.setToolTip('select joints')
        
        add_joint_orient = qt.QPushButton('Convert to Orient Joint')
        #add_joint_orient.setMaximumWidth(140)
        
        
        orient_joints = qt.QPushButton('Orient Joints')
        orient_joints.setMinimumHeight(40)
        
        mirror = qt.QPushButton('Mirror Transforms')
        mirror.setMinimumHeight(40)
        
        #match_joints = qt.QPushButton('Match')
        #match_joints.setMinimumHeight(40)
        
        joints_on_curve = qt_ui.GetIntNumberButton('Create Joints On Curve')
        joints_on_curve.set_value(10)
        
        snap_to_curve = qt_ui.GetIntNumberButton('Snap Joints to Curve')
        
        transfer_joints = qt.QPushButton('Transfer Joints  ( Mesh to Mesh with same topology )')
        transfer_process = qt.QPushButton('transfer process weights to parent')
        
        self.joint_axis_check = qt.QCheckBox('Joint Axis Visibility')
        
        mirror_invert = qt.QPushButton('Mirror Invert')
        mirror_invert.clicked.connect(self._mirror_invert)
        
        remove_orient = qt.QPushButton('Remove Orient')
        remove_orient.clicked.connect(self._remove_orient)
        
        add_orient.clicked.connect(self._add_orient)
        orient_joints.clicked.connect(self._orient)
        
        add_joint_orient.clicked.connect(self._add_joint_orient)
        
        mirror.clicked.connect(self._mirror)
        #match_joints.clicked.connect(self._match_joints)
        joints_on_curve.clicked.connect(self._joints_on_curve)
        snap_to_curve.clicked.connect(self._snap_joints_to_curve)
        transfer_joints.clicked.connect(self._transfer_joints)
        transfer_process.clicked.connect(self._transfer_process)
        self.joint_axis_check.stateChanged.connect(self._set_joint_axis_visibility)
        
        main_layout = parent.main_layout
        
        orient_layout = qt.QHBoxLayout()
        
        sub_orient_layout = qt.QVBoxLayout()
        orient_layout.addWidget(orient_joints)
        orient_layout.addSpacing(10)
        orient_layout.addLayout(sub_orient_layout)
        
        sub_orient_layout.addWidget(add_orient)
        sub_orient_layout.addWidget(add_joint_orient)
        sub_orient_layout.addWidget(mirror_invert)
        sub_orient_layout.addWidget(remove_orient)
        
        
        
        main_layout.addSpacing(20)
        #main_layout.addWidget(add_orient)
        main_layout.addWidget(mirror)
        main_layout.addSpacing(15)
        main_layout.addLayout(orient_layout)
        #main_layout.addWidget(mirror_invert)
        main_layout.addSpacing(20)
        main_layout.addWidget(self.joint_axis_check)
        
        main_layout.addSpacing(20)
        #main_layout.addWidget(orient_joints)
        #main_layout.addWidget(match_joints)
        main_layout.addWidget(subdivide_joint_button)
        main_layout.addWidget(joints_on_curve)
        main_layout.addWidget(snap_to_curve)
        main_layout.addSpacing(15)
        main_layout.addWidget(transfer_joints)
        
        
        #removed, no longer used that much
        #main_layout.addWidget(transfer_process)
        
    def _match_joints(self):
        space.match_joint_xform('joint_', 'guideJoint_')
        space.match_orient('joint_', 'guideJoint_')
        
    def _create_control_widgets(self, parent):
        
        mirror_control = qt.QPushButton('Mirror Control')
        mirror_control.clicked.connect(self._mirror_control)
        
        mirror_controls = qt.QPushButton('Mirror Controls')
        mirror_controls.clicked.connect(self._mirror_controls)
        mirror_controls.setMinimumHeight(40)
        
        size_slider = qt_ui.Slider('Scale Controls at Pivot')
        size_slider.value_changed.connect(self._scale_control)
        size_slider.slider.setRange(-200, 200)
        size_slider.set_auto_recenter(True)
        size_slider.slider.sliderReleased.connect(self._reset_scale_slider)
        
        size_center_slider = qt_ui.Slider('Scale Controls at Center')
        size_center_slider.value_changed.connect(self._scale_center_control)
        size_center_slider.slider.setRange(-200, 200)
        size_center_slider.set_auto_recenter(True)
        size_center_slider.slider.sliderReleased.connect(self._reset_scale_center_slider)
        
        number_button = qt_ui.GetNumberButton('Global Size Controls')
        number_button.set_value(2)
        number_button.clicked.connect(self._size_controls)
        self.scale_control_button = number_button
        
        self.fix_sub_controls = qt.QPushButton('Fix Sub Controls')
        self.fix_sub_controls.clicked.connect(rigs_util.fix_sub_controls)
        
        project_curve = qt_ui.GetNumberButton('Project Curves on Mesh')
        project_curve.set_value(1)
        project_curve.set_value_label('Offset')
        project_curve.clicked.connect(self._project_curve)
        
        snap_curve = qt_ui.GetNumberButton('Snap Curves to Mesh')
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
        corrective_button = qt.QPushButton('Create Corrective')
        corrective_button.setToolTip('Select deformed mesh then sculpted mesh.')
        #corrective_button.setMaximumWidth(200)
        corrective_button.clicked.connect(self._create_corrective)
        
        skin_mesh_from_mesh = qt.QPushButton('Skin Mesh From Mesh')
        skin_mesh_from_mesh.setToolTip('Select skinned mesh then mesh without skin cluster.')
        #skin_mesh_from_mesh.setMaximumWidth(200)
        skin_mesh_from_mesh.clicked.connect(self._skin_mesh_from_mesh)
        
        cluster_mesh = qt.QPushButton('Create Tweak Cluster')
        cluster_mesh.setToolTip('Go into cluster creation context.  Click on a mesh to add cluster at point and start paint weighting.')
        cluster_mesh.clicked.connect(self._cluster_tweak_mesh)
        
        parent.main_layout.addWidget(corrective_button)
        parent.main_layout.addWidget(skin_mesh_from_mesh)
        parent.main_layout.addSpacing(10)
        parent.main_layout.addWidget(cluster_mesh)
            
    def _pose_manager(self):
        window = pose_manager()
        ui_core.emit_new_tool_signal(window)
        
    def _process_manager(self):
        window = process_manager()
        ui_core.emit_new_tool_signal(window)

    def _shape_combo(self):
        window = shape_combo()
        ui_core.emit_new_tool_signal(window)

    def _checker(self):
        window = checker()
        ui_core.emit_new_tool_signal(window)

    def _picker(self):
        window = picker()
        ui_core.emit_new_tool_signal(window)
        
    def _presets(self):
    
        window = presets()
        ui_core.emit_new_tool_signal(window)

    def _create_corrective(self):
        
        selection = cmds.ls(sl = True)
        
        deform.chad_extract_shape(selection[0], selection[1])
    
    def _skin_mesh_from_mesh(self):
        selection = cmds.ls(sl = True)
        deform.skin_mesh_from_mesh(selection[0], selection[1])
    
    def _cluster_tweak_mesh(self):
        
        ctx = deform.ClusterTweakCtx()
        ctx.run()
    
    def _subdivide_joint(self, number):
        space.subdivide_joint(count = number)
        
    def _add_orient(self):
        selection = cmds.ls(sl = True, type = 'joint')
        
        attr.add_orient_attributes(selection)
    
    def _remove_orient(self):
        
        selection = cmds.ls(sl = True, type = 'joint')
        
        attr.remove_orient_attributes(selection)
    
    def _add_joint_orient(self):
        selection = cmds.ls(sl = True, type = 'joint')
        
        for thing in selection:
            space.add_orient_joint(thing)
        
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
        self.last_scale_value = None
        
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
            self.last_scale_value = None
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
            self.last_scale_center_value = None
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