# Copyright (C) 2016 Louis Vottero louis.vot@gmail.com    All rights reserved.

from vtool import qt_ui, qt


from vtool import util_file
from vtool import util

from vtool.maya_lib import ui_core

import maya.cmds as cmds

from vtool.maya_lib import blendshape
from vtool.maya_lib import core
from vtool.maya_lib import geo
from vtool.maya_lib import attr    
from vtool.maya_lib import space
from vtool.maya_lib import deform
from vtool.maya_lib import rigs_util
from vtool.maya_lib import curve

import ui_check
import ui_presets
import ui_picker
import ui_model
import ui_anim

from vtool.process_manager import ui_process_manager
from vtool.script_manager import script_view


def pose_manager(shot_sculpt_only = False):
    
    from vtool.maya_lib.ui_lib import ui_corrective
    ui_core.delete_workspace_control(ui_corrective.PoseManager.title + 'WorkspaceControl')
    
    window = ui_corrective.PoseManager(shot_sculpt_only)
    
    window.show()
    
    return window

def shape_combo():
    
    from vtool.maya_lib.ui_lib import ui_shape_combo
    ui_core.delete_workspace_control(ui_shape_combo.ComboManager.title + 'WorkspaceControl')
    
    window = ui_shape_combo.ComboManager()
    
    return window
    
def checker():
    
    ui_core.delete_workspace_control(ui_check.CheckView.title + 'WorkspaceControl')
    
    window = ui_check.CheckView()
    window.setWindowTitle('Checks')
    window.add_check(ui_check.Check_References())
    window.add_check(ui_check.Check_Empty_Groups())
    window.add_check(ui_check.Check_Empty_Intermediate_Objects())
    window.add_check(ui_check.Check_Empty_Nodes())
    window.add_check(ui_check.Check_Non_Default_Transforms())
    window.add_check(ui_check.Check_Non_Unique())
    window.add_check(ui_check.Check_Triangles())
    window.add_check(ui_check.Check_NSided())
    
    window.show()
    
    return window
    
def picker():
    
    window = ui_picker.PickManager()
    
    
    
    return window
    

def process_manager(directory = None):
    
    ui_core.delete_workspace_control(ProcessMayaWindow.title + 'WorkspaceControl')
    
    window = ProcessMayaWindow(load_settings = False)
    
    if directory:
        window.set_directory(directory, load_as_project=True)
    
    window.show()
    
    return window

def presets():
    
    window = ui_presets.Presets()
    
    return window

class ProcessMayaWindow(ui_core.MayaDockMixin,ui_process_manager.ProcessManagerWindow):
    title = 'VETALA'
    def __init__(self, load_settings = False):
        super(ProcessMayaWindow, self).__init__( load_settings= load_settings)

class ScriptMayaWindow(ui_core.MayaDockMixin, script_view.ScriptManagerWidget):
    title = 'Scripts'
    def __init__(self):
        super(ScriptMayaWindow, self).__init__()

vetala_version = util_file.get_vetala_version()
    
class RigManager(qt_ui.DirectoryWindow):
    
    def __init__(self):
        super(RigManager, self).__init__()
    
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
        
        icon = qt_ui.get_icon('vetala.png')
        
        process_button = qt.QPushButton(icon, util.get_custom('vetala_name', 'VETALA'))
        process_button.setIconSize(qt.QtCore.QSize(48,48))
        process_button.setFlat(True)
        process_button.setMinimumHeight(48)
        process_button.clicked.connect(self._process_manager)
        process_button.setMinimumWidth(button_width)
        process_button.setToolTip('Manage and rebuild rigs.')
        #manager_layout.addWidget(process_button)
        
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
        tool_group.set_collapsable(False)
        tool_group.setFlat(True)
        
        tool_tab = qt.QTabWidget()
        
        deformation_widget = DeformWidget()
        structure_widget = StructureWidget()
        control_widget = ControlWidget()
        tool_group.main_layout.addWidget(tool_tab)
        
        model_widget = ui_model.ModelManager(scroll = True)

        
        tool_tab.addTab(structure_widget, 'Structure')
        tool_tab.addTab(control_widget, 'Controls')
        tool_tab.addTab(deformation_widget, 'Deform')
        tool_tab.addTab(model_widget, 'Model')
        tool_tab.addTab(ui_anim.AnimationManager(), 'Animate')
        
        self.main_layout.addWidget(manager_group)
        self.main_layout.addSpacing(15)
        self.main_layout.addWidget(tool_group)
        
        #self._load_existing()
        
    def _load_existing(self):
        from vtool.maya_lib.ui_lib import ui_corrective
        from vtool.maya_lib.ui_lib import ui_shape_combo
        
        if self._check_exists(ProcessMayaWindow):
            self._process_manager()
            
        if self._check_exists(ui_shape_combo.ComboManager):
            self._shape_combo()
            
        if self._check_exists(ui_corrective.PoseManager):
            self._pose_manager()
            
        if self._check_exists(ui_check.CheckView):
            self._checker()
        
    def _check_exists(self, ui_class):
        if not hasattr(ui_class, 'title'):
            return
        
        name = ui_class.title + 'WorkspaceControl'
        if cmds.workspaceControl(name, exists = True):
            return True
        
        return False
        
    def _pose_manager(self):
        window = pose_manager()
        ui_core.emit_new_tool_signal(window)
        
    def _process_manager(self):
        window = process_manager(self.directory)
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
    
class SkinMeshFromMesh(qt_ui.Group):
    def __init__(self):
        
        name = 'Skin Mesh From Mesh'
        super(SkinMeshFromMesh, self).__init__(name)
        
    def _build_widgets(self):
        
        info = qt.QLabel('Apply the skin from the source to the target.\nThis will automatically skin the target\nand copy skin weights.\n\nSet exclude and include joints\nThis helps control what joints get applied.')
        
        self.exclude = qt_ui.GetString('Exclude Joints')
        self.exclude.set_use_button(True)
        self.exclude.set_placeholder('Optional')
        self.include = qt_ui.GetString('Include Joints')
        self.include.set_use_button(True)
        self.include.set_placeholder('Optional')
        
        self.uv = qt_ui.GetBoolean('Copy weights using UVs')
        
        label = qt.QLabel('Select source and target mesh.')
        
        run = qt.QPushButton('Run')
        run.clicked.connect(self._run)
        
        self.main_layout.addWidget(info)
        self.main_layout.addWidget(self.exclude)
        self.main_layout.addWidget(self.include)
        self.main_layout.addWidget(self.uv)
        self.main_layout.addWidget(label)
        self.main_layout.addSpacing(10)
        self.main_layout.addWidget(run)
    
    def _run(self):
        
        exclude = self.exclude.get_text_as_list()
        include = self.include.get_text_as_list()
        
        uv = self.uv.get_value()
        
        selection = cmds.ls(sl = True)
        
        if selection and len(selection) == 2:
            if geo.is_a_mesh(selection[0]) and geo.is_a_mesh(selection[1]):
                deform.skin_mesh_from_mesh(selection[0], selection[1], exclude_joints = exclude, include_joints = include, uv_space = uv)
        else:
            util.warning('Please select 2 meshes that have skin clusters.')
                
class MirrorMesh(qt_ui.Group):
    def __init__(self):
        
        name = 'Mirror Mesh'
        super(MirrorMesh, self).__init__(name)
        
    def _build_widgets(self):
        mirror_shape_info = qt.QLabel('Mirror a shape from left to right.')
        self.base_mesh = qt_ui.GetString('Base Mesh')
        self.base_mesh.set_use_button(True)
        self.base_mesh.set_placeholder('Original Shape')
        mirror = qt.QPushButton('Mirror Selected')
        
        self.main_layout.addWidget(mirror_shape_info)
        self.main_layout.addWidget(self.base_mesh)
        self.main_layout.addSpacing(10)
        self.main_layout.addWidget(mirror)
        
        mirror.clicked.connect(self._run)
        
    def _run(self):
        
        base_mesh = self.base_mesh.get_text()
        
        meshes = geo.get_selected_meshes()
        
        for mesh in meshes:
            deform.mirror_mesh(mesh, base_mesh)
            
class RigWidget(qt_ui.BasicWidget):
    def __init__(self, scroll = True):
        super(RigWidget, self).__init__(scroll = scroll)
        
        self.main_layout.setContentsMargins(0,0,0,0)
        self.setMaximumWidth(550)

class StructureWidget(RigWidget):
    
    def __init__(self, scroll = True):
        super(StructureWidget, self).__init__(scroll = scroll)
    
    
    def _build_widgets(self):
        
        self.setMinimumHeight(300)
        
        subdivide_joint_button =  qt_ui.GetIntNumberButton('Subdivide Joint')
        subdivide_joint_button.set_value(1)
        subdivide_joint_button.clicked.connect(self._subdivide_joint)
        subdivide_joint_button.setToolTip('select parent and child joint')
        
        add_orient = qt.QPushButton('Add Orient Attributes')
        add_orient.clicked.connect(self._add_orient)
        
        remove_orient = qt.QPushButton('Remove Orient Attributes')
        remove_orient.clicked.connect(self._remove_orient)
        
        add_joint_orient = qt.QPushButton('Add Joint Aim and Up')
        add_joint_orient.clicked.connect(self._add_joint_orient)
        #add_joint_orient.setMaximumWidth(140)
        
        skip_orient = qt.QPushButton('Set Skip Orient')
        unskip_orient = qt.QPushButton('Set Unskip Orient')
        skip_orient.clicked.connect(self._skip_orient)
        unskip_orient.clicked.connect(self._unskip_orient)
        
        orient_button_layout = qt.QVBoxLayout()
        
        orient_joints = qt.QPushButton('Orient Joints')
        orient_joints.setMinimumHeight(40)
        orient_joints.setMinimumWidth(125)
        orient_joints.clicked.connect(self._orient)
        
        orient_hier_joints = qt.QPushButton('Orient Hierarchy')
        orient_hier_joints.setMinimumHeight(20)
        orient_hier_joints.setMinimumWidth(125)
        orient_hier_joints.clicked.connect(self._orient_selected_hier)
        
        orient_sel_joints = qt.QPushButton('Orient Selected')
        orient_sel_joints.setMinimumHeight(20)
        orient_sel_joints.setMinimumWidth(125)
        orient_sel_joints.clicked.connect(self._orient_selected_only)
        
        self.joint_axis_check = qt.QCheckBox('Joint Axis Visibility')
        
        orient_button_layout.addWidget(orient_joints)
        orient_button_layout.addWidget(orient_hier_joints)
        orient_button_layout.addWidget(orient_sel_joints)
        orient_button_layout.addWidget(self.joint_axis_check)
        
        orient_button_layout.setAlignment(qt.QtCore.Qt.AlignLeft | qt.QtCore.Qt.AlignCenter)
        
        orient_layout = qt.QHBoxLayout()
        
        sub_orient_layout = qt.QVBoxLayout()
        orient_layout.addLayout(orient_button_layout)
        orient_layout.addSpacing(10)
        orient_layout.addLayout(sub_orient_layout)
        
        sub_orient_layout.addWidget(add_orient)
        sub_orient_layout.addWidget(remove_orient)
        sub_orient_layout.addSpacing(3)
        sub_orient_layout.addWidget(add_joint_orient)
        sub_orient_layout.addSpacing(3)
        sub_orient_layout.addWidget(skip_orient)
        sub_orient_layout.addWidget(unskip_orient)
        
        mirror_translate_layout = qt.QHBoxLayout()
        
        mirror = qt.QPushButton('Mirror Transforms')
        mirror.setMinimumHeight(40)
        mirror.setMinimumWidth(125)
        
        mirror_sel = qt.QPushButton('Mirror Selected Only')
        mirror_sel.setMinimumHeight(20)
        mirror_sel.setMinimumWidth(125)
        
        on_off_mirror_layout = qt.QVBoxLayout()
        
        mirror_off = qt.QPushButton('Set Skip Mirror')
        mirror_off.clicked.connect(self._mirror_off)
        mirror_on = qt.QPushButton('Set Unskip Mirror')
        mirror_on.clicked.connect(self._mirror_on)
        
        mirror_create = qt.QPushButton('Mirror Create')
        mirror_create.clicked.connect(self._mirror_create)
        
        
        mirror_right_left = qt.QPushButton('Mirror R to L')
        mirror_right_left.clicked.connect(self._mirror_r_l)
        
        mirror_curves = qt.QPushButton('Mirror Curves')
        
        mirror_invert = qt.QPushButton('Mirror Invert')
        mirror_invert.clicked.connect(self._mirror_invert)
        
        main_mirror_layout = qt.QVBoxLayout()
        main_mirror_layout.setAlignment(qt.QtCore.Qt.AlignCenter | qt.QtCore.Qt.AlignLeft)
        main_mirror_layout.addWidget(mirror)
        main_mirror_layout.addWidget(mirror_sel)
        
        mirror_translate_layout.addLayout(main_mirror_layout)
        mirror_translate_layout.addSpacing(10)
        mirror_translate_layout.addLayout(on_off_mirror_layout)
        
        on_off_mirror_layout.addWidget(mirror_create)
        on_off_mirror_layout.addWidget(mirror_right_left)
        on_off_mirror_layout.addWidget(mirror_curves)
        on_off_mirror_layout.addWidget(mirror_invert)
        on_off_mirror_layout.addSpacing(3)
        on_off_mirror_layout.addWidget(mirror_off)
        on_off_mirror_layout.addWidget(mirror_on)

        joints_on_curve = qt_ui.GetIntNumberButton('Create Joints On Curve')
        joints_on_curve.set_value(10)
        
        snap_to_curve = qt_ui.GetIntNumberButton('Snap Joints to Curve')
        
        transfer_joints = qt.QPushButton('Transfer Joints  ( Mesh to Mesh with same topology )')
        transfer_process = qt.QPushButton('transfer process weights to parent')

        mirror.clicked.connect(self._mirror)
        mirror_sel.clicked.connect(self._mirror_selected)
        mirror_curves.clicked.connect(self._mirror_curves)
        
        joints_on_curve.clicked.connect(self._joints_on_curve)
        snap_to_curve.clicked.connect(self._snap_joints_to_curve)
        transfer_joints.clicked.connect(self._transfer_joints)
        transfer_process.clicked.connect(self._transfer_process)
        self.joint_axis_check.stateChanged.connect(self._set_joint_axis_visibility)
        
        main_layout = self.main_layout

        main_layout.addSpacing(5)
        
        main_layout.addLayout(mirror_translate_layout)
        
        main_layout.addSpacing(10)
        main_layout.addLayout(orient_layout)
        
        main_layout.addSpacing(10)
        
        main_layout.addWidget(subdivide_joint_button)
        main_layout.addWidget(joints_on_curve)
        main_layout.addWidget(snap_to_curve)
        main_layout.addSpacing(10)
        main_layout.addWidget(transfer_joints)

    def _subdivide_joint(self, number):
        space.subdivide_joint(count = number)
        
    def _add_orient(self):
        selection = cmds.ls(sl = True, type = 'joint')
        
        if not selection:
            core.print_warning('Please select joints to add orient to.')
            
        
        
        attr.add_orient_attributes(selection, context_sensitive=True)
        core.print_help('Added orient attributes to the selected joints.')
    
    def _remove_orient(self):
        
        selection = cmds.ls(sl = True, type = 'joint')
        
        if not selection:
            core.print_warning('Please select joints to remove orient from.')
        
        
        
        attr.remove_orient_attributes(selection)
        core.print_help('Removed orient attributes from the selected joints.')
    
    @core.undo_chunk
    def _add_joint_orient(self):
        selection = cmds.ls(sl = True, type = 'joint')
        
        if not selection:
            core.print_warning('Please select joints to add aim and up to.')
        
        for thing in selection:
            space.add_orient_joint(thing)
            
        core.print_help('Added aim and up to selected joints.')
        
    @core.undo_chunk
    def _orient(self):
        
        selection = cmds.ls(sl = True)
        
        oriented = space.orient_attributes_all()
        
        if oriented:
            core.print_help('Oriented joints with orient attributes.')
        if not oriented:
            core.print_warning('No joints oriented. Check that there are joints with orient attributes.')
        
        cmds.select(selection)
        
    
    @core.undo_chunk
    def _orient_selected_hier(self):
        selected = cmds.ls(sl = True, type = 'joint')
        
        if not selected:
            core.print_warning('Please select joints to orient.')
        
        oriented = space.orient_attributes(selected)
        
        if oriented:
            core.print_help('Oriented selected joints')
        
        cmds.select(selected)

    def _orient_selected_only(self):
        
        selected = cmds.ls(sl = True, type = 'joint')
        
        if not selected:
            core.print_warning('Please select joints to orient.')
        
        oriented = space.orient_attributes(selected, hierarchy= False)
        
        if oriented:
            core.print_help('Oriented selected joints')
        
        cmds.select(selected)

    def _unskip_orient(self):
        
        selection = cmds.ls(sl = True, type = 'joint')
        
        for thing in selection:
            if cmds.objExists('%s.active' % thing):
                cmds.setAttr('%s.active' % thing, 1)
        
        if not selection:
            core.print_help('Please select joints to unskip running orient.')
    
    def _skip_orient(self):
        
        selection = cmds.ls(sl = True, type = 'joint')
        
        for thing in selection:
            if cmds.objExists('%s.active' % thing):
                cmds.setAttr('%s.active' % thing, 0)
        
        if not selection:
            core.print_help('Please select joints to skip running orient.')
            
    @core.undo_chunk
    def _mirror(self, *args ):
        #*args is for probably python 2.6, which doesn't work unless you have a key argument.
        
        fixed = space.mirror_xform()
        
        
        if fixed:
            core.print_help('Mirrored transforms left to right')
        if not fixed:
            core.print_warning('No joints mirrored. Check there are joints on the left that can mirror right.  Make sure translate rotate do not have connections.')
    
    @core.undo_chunk
    def _mirror_selected(self, *args):
        selected = cmds.ls(sl = True, type = 'transform')
        
        if not selected:
            core.print_warning('Please select joints to mirror.')
            return
        
        fixed = space.mirror_xform(transforms = selected)
        
        if fixed:
            core.print_help('Mirrored selected left to right')
            
    def _mirror_on(self):
        
        transforms = cmds.ls(sl = True, type = 'transform')
        
        if not transforms:
            core.print_warning('Please select some joints or transforms to unskip.')
            return
        
        for transform in transforms:
            space.mirror_toggle(transform, True)
    
        if transforms:
            core.print_help('mirror attribute set on. This transform will be affected by mirror transforms.')

        
    def _mirror_off(self):
        
        transforms = cmds.ls(sl = True, type = 'transform')
        
        if not transforms:
            core.print_warning('Please select some joints or transforms to unskip.')
            return
        
        for transform in transforms:
            space.mirror_toggle(transform, False)
            
        if transforms:
            core.print_help('mirror attribute set off. This transform will no longer be affected by mirror transforms.')
    
    @core.undo_chunk        
    def _mirror_r_l(self):
        
        selected = cmds.ls(sl = True, type = 'transform')
        fixed = space.mirror_xform(transforms = selected, left_to_right = False)
        
        if selected and fixed:
            core.print_warning('Only mirrored selected right to left')
        if not selected and fixed:
            core.print_help('Mirrored transforms right to left')
        if not fixed:
            core.print_warning('No joints mirrored. Check there are joints on the right that can mirror left.  Check your selected transform is not on the left. Make sure translate rotate do not have connections.')
            
    @core.undo_chunk
    def _mirror_create(self):
        
        selected = cmds.ls(sl = True, type = 'transform')
        
        created = space.mirror_xform(transforms = selected, create_if_missing=True)
        
        if created and selected:
            core.print_warning('Only created transforms on the right side that were selected on the left.')
        if created and not selected:
            core.print_help('Created transforms on the right side that were on the left.')
        if not created:
            core.print_warning('No transforms created. Check that there are missing transforms on the right or that the right side does not already exist. Check your selected transform is on the left.')

    @core.undo_chunk
    def _mirror_curves(self, *args ):
        #*args is for probably python 2.6, which doesn't work unless you have a key argument.
        
        rigs_util.mirror_curve()
        
        
    @core.undo_chunk
    def _mirror_invert(self):
        
        selection = cmds.ls(sl = True)
        
        for thing in selection:
            space.mirror_invert(thing)
        
        
        
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
        
        deform.transfer_skeleton(mesh_source, mesh_target)
        
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
        

class ControlWidget(RigWidget):
    
    def __init__(self, scroll = True):
        super(ControlWidget, self).__init__(scroll = scroll)
        
        self.scale_controls = []
        self.last_scale_value = None
        self.last_scale_center_value = None

    def _build_widgets(self):
        
        mirror_control = qt.QPushButton('Mirror Selected Controls')
        mirror_control.clicked.connect(self._mirror_control)
        
        mirror_controls = qt.QPushButton('Mirror All Controls')
        mirror_controls.clicked.connect(self._mirror_controls)
        mirror_controls.setMinimumHeight(40)
        
        curve_names = curve.get_library_shape_names()
        curve_names.sort()
        self.curve_shape_combo = qt.QComboBox()
        self.curve_shape_combo.addItems(curve_names)
        self.curve_shape_combo.setMaximumWidth(110)
        
        curve_shape_label = qt.QLabel('Curve Type') 
        
        replace_curve_shape = qt.QPushButton('Replace Curve Shape')
        replace_curve_shape.clicked.connect(self._replace_curve_shape)
        
        replace_curve_layout = qt.QHBoxLayout()
        replace_curve_layout.addWidget(replace_curve_shape)
        replace_curve_layout.addSpacing(5)
        replace_curve_layout.addWidget(curve_shape_label, alignment = qt.QtCore.Qt.AlignRight)
        replace_curve_layout.addWidget(self.curve_shape_combo)
        
        self.rotate_x_widget = qt_ui.GetNumberButton('X Rotate Control')
        self.rotate_x_widget.set_value(90)
        self.rotate_x_widget.clicked.connect(self._rotate_x_control)
        
        self.rotate_y_widget = qt_ui.GetNumberButton('Y Rotate Control')
        self.rotate_y_widget.set_value(90)
        self.rotate_y_widget.clicked.connect(self._rotate_y_control)
        
        self.rotate_z_widget = qt_ui.GetNumberButton('Z Rotate Control')
        self.rotate_z_widget.set_value(90)
        self.rotate_z_widget.clicked.connect(self._rotate_z_control)
        
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
        
        
        self.main_layout.addWidget(mirror_control)
        self.main_layout.addWidget(mirror_controls)
        self.main_layout.addSpacing(10)
        self.main_layout.addLayout(replace_curve_layout)
        self.main_layout.addSpacing(10)
        self.main_layout.addWidget(self.fix_sub_controls)
        self.main_layout.addSpacing(10)
        self.main_layout.addWidget(self.rotate_x_widget)
        self.main_layout.addWidget(self.rotate_y_widget)
        self.main_layout.addWidget(self.rotate_z_widget)
        self.main_layout.addSpacing(15)
        self.main_layout.addWidget(number_button)

        self.main_layout.addWidget(size_slider)
        self.main_layout.addWidget(size_center_slider)
        
        self.main_layout.addWidget(project_curve)
        self.main_layout.addWidget(snap_curve)
        
    def _mirror_control(self):
        
        selection = cmds.ls(sl = True)
        if not selection:
            return
        
        for thing in selection:
            rigs_util.mirror_control(thing)
        
    def _mirror_controls(self):
        
        rigs_util.mirror_controls()
    
    def _rotate_x_control(self):
        
        selection = cmds.ls(sl = True)
        
        
        
        for sel in selection:
            
            if core.has_shape_of_type(sel, 'nurbsCurve') or core.has_shape_of_type(sel, 'nurbsSurface'):
                
                x_value = self.rotate_x_widget.get_value()
                
                geo.rotate_shape(sel, x_value, 0, 0)
            
    
    def _rotate_y_control(self):
        
        selection = cmds.ls(sl = True)
        
        for sel in selection:
            
            if core.has_shape_of_type(sel, 'nurbsCurve') or core.has_shape_of_type(sel, 'nurbsSurface'):
                
                y_value = self.rotate_y_widget.get_value()
                
                geo.rotate_shape(sel, 0, y_value, 0)

    def _rotate_z_control(self):
        
        selection = cmds.ls(sl = True)
        
        for sel in selection:
            
            if core.has_shape_of_type(sel, 'nurbsCurve') or core.has_shape_of_type(sel, 'nurbsSurface'):
                
                z_value = self.rotate_z_widget.get_value()
                
                geo.rotate_shape(sel, 0, 0, z_value)
    
    
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
            
    @core.undo_chunk
    def _replace_curve_shape(self):
        
        shape = str(self.curve_shape_combo.currentText())
        
        curves = geo.get_selected_curves()
        
        for c in curves:
            inst = curve.CurveDataInfo()
            inst.set_active_library('default_curves')
            inst.set_shape_to_curve(str(c), shape, add_curve_type_attribute=False)
        
        cmds.select(curves)
        
class DeformWidget(RigWidget):
    
    def __init__(self, scroll = False):
        super(DeformWidget, self).__init__(scroll)
    
    def _build_widgets(self):
        
        skin_widget = SkinWidget(scroll = True)
        skin_widget.main_layout.setContentsMargins(0,0,0,0)
        
        group = qt_ui.Group('Deformation Utilities')
        
        intermediate_button_info = qt.QLabel('This button updates the intermediate object.\nSelect a mesh to be the new intermediate.\nAnd also a mesh with\nskinCluster and/or blendShape.')
        intermediate_button = qt.QPushButton('Blend Into Intermediate')
        
        intermediate_button.clicked.connect(self._blend_into_intermediate)
        
        recreate_blends_info = qt.QLabel('Recreate all the targets of a blendshape.\nSelect a mesh with blendshape history\nAnd optionally meshes that should follow.')
        recreate_blends = qt.QPushButton('Recreate Blendshapes')
        
        recreate_blends.clicked.connect(self._recreate_blends)
        
        corrective_button_info = qt.QLabel('Select a mesh (in pose) deformed by a \nskinCluster and/or a blendShape\nAnd also the sculpted mesh to correct it.')
        corrective_button = qt.QPushButton('Create Corrective')
        
        corrective_button.clicked.connect(self._create_corrective)
        
        cluster_mesh_info = qt.QLabel('This will add a cluster at the click point\nand go into paint weighting.\nPush button then click on a mesh.')
        cluster_mesh = qt.QPushButton('Create Tweak Cluster')
        cluster_mesh.clicked.connect(self._cluster_tweak_mesh)
        
        self.main_layout.addWidget(skin_widget)
        #self.main_layout.addSpacing(15)
        
        group.main_layout.addWidget(cluster_mesh_info)
        group.main_layout.addWidget(cluster_mesh)
        group.main_layout.addSpacing(15)
        group.main_layout.addWidget(recreate_blends_info)
        group.main_layout.addWidget(recreate_blends)
        group.main_layout.addSpacing(15)
        group.main_layout.addWidget(intermediate_button_info)
        group.main_layout.addWidget(intermediate_button)
        group.main_layout.addSpacing(15)
        group.main_layout.addWidget(corrective_button_info)
        group.main_layout.addWidget(corrective_button)
        group.collapse_group()
        #this fixed a expand contract bug
        skin_widget.main_layout.addSpacing(15)
        skin_widget.main_layout.addWidget(group)
        #self.main_layout.addWidget(group)

    def _create_corrective(self):        
        selection = cmds.ls(sl = True)
        deform.chad_extract_shape(selection[0], selection[1])
        
    def _cluster_tweak_mesh(self):
        
        ctx = deform.ClusterTweakCtx()
        ctx.run()
    
    def _blend_into_intermediate(self):
        
        deform.blend_into_intermediate()
    
    def _recreate_blends(self):
        blendshape.recreate_blendshapes()
    


class SkinWidget(RigWidget):
    def __init__(self, scroll = True):
        super(SkinWidget, self).__init__(scroll)
    def _build_widgets(self):
        
        self.setMinimumHeight(300)
        
        group = qt_ui.Group('Edit Skin Weights')
        group.collapse_group()
        
        weights_label = qt.QLabel('Select a mesh or verts of a single mesh')
        
        average_weights = qt.QPushButton('Average Weights')
        smooth_weights_layout = qt.QVBoxLayout()
        sub_smooth_weights_layout = qt.QHBoxLayout()
        smooth_weights = qt.QPushButton('Smooth Weights')
        self.count_smooth_weights = qt_ui.GetInteger('Iterations')
        self.count_smooth_weights.set_value(1)
        
        self.percent_smooth_weights = qt_ui.GetNumber('Percent')
        self.percent_smooth_weights.set_value(1)
        
        self.smooth_mode = qt_ui.GetInteger('Mode: 0=Broad 1=Tight')
        self.smooth_mode.set_value(1)
        self.smooth_mode.number_widget.setMaximum( 1 )
        self.smooth_mode.number_widget.setMinimum( 0 )
        
        self.smooth_api = qt_ui.GetBoolean('Use Api: No Undo, Buggy, Faster on heavy meshes')
        
        
        
        sub_smooth_weights_layout.addWidget(self.count_smooth_weights)
        sub_smooth_weights_layout.addSpacing(5)
        sub_smooth_weights_layout.addWidget(self.percent_smooth_weights)
        sub_smooth_weights_layout.addSpacing(5)
        smooth_weights_layout.addLayout(sub_smooth_weights_layout)
        smooth_weights_layout.addSpacing(5)
        smooth_weights_layout.addWidget(self.smooth_mode)
        smooth_weights_layout.addWidget(self.smooth_api)
        smooth_weights_layout.addSpacing(5)
        smooth_weights_layout.addWidget(smooth_weights)
        
        sharpen_weights_layout = qt.QHBoxLayout()
        sharpen_weights = qt.QPushButton('Sharpen Weights')
        self.count_sharpen_weights = qt_ui.GetInteger('Iterations')
        self.count_sharpen_weights.set_value(1)
        
        self.percent_sharpen_weights = qt_ui.GetNumber('Percent')
        self.percent_sharpen_weights.set_value(1)
        
        
        sharpen_weights_layout.addWidget(self.count_sharpen_weights)
        sharpen_weights_layout.addSpacing(5)
        sharpen_weights_layout.addWidget(self.percent_sharpen_weights)
        #sharpen_weights_layout.addWidget(sharpen_weights)
        
        average_weights.clicked.connect(self._average_weights)
        smooth_weights.clicked.connect(self._smooth_weights)
        sharpen_weights.clicked.connect(self._sharpen_weights)
        skin_mesh_from_mesh = SkinMeshFromMesh()
        skin_mesh_from_mesh.collapse_group()
        
        group.main_layout.addWidget(weights_label)
        group.main_layout.addSpacing(15)
        group.main_layout.addLayout(smooth_weights_layout)
        group.main_layout.addSpacing(15)
        group.main_layout.addLayout(sharpen_weights_layout)
        group.main_layout.addWidget(sharpen_weights)
        group.main_layout.addSpacing(15)
        group.main_layout.addWidget(average_weights)
        self.main_layout.addWidget(group)
        self.main_layout.addSpacing(15)
        self.main_layout.addWidget(skin_mesh_from_mesh)
        
        
    def _skin_mesh_from_mesh(self):
        selection = cmds.ls(sl = True)
        deform.skin_mesh_from_mesh(selection[0], selection[1])

        
    @core.undo_chunk    
    def _smooth_weights(self):
        
        selection = cmds.ls(sl = True, flatten = True)
        
        verts = []

        thing = selection[0]

        if geo.is_a_mesh(thing):
            verts = geo.get_vertices(thing)
        
        if geo.is_a_vertex(thing):
            verts = selection
    
        get_count = self.count_smooth_weights.get_value()
        percent = self.percent_smooth_weights.get_value()
        mode = self.smooth_mode.get_value()
        api = self.smooth_api.get_value()
        
        deform.smooth_skin_weights(verts, get_count, percent, mode, api)
    
    @core.undo_chunk
    def _average_weights(self):
        
        selection = cmds.ls(sl = True, flatten = True)
        
        verts = []

        thing = selection[0]

        if geo.is_a_mesh(thing):
            verts = geo.get_vertices(thing)
        
        if geo.is_a_vertex(thing):
            verts = selection
    
        deform.average_skin_weights(verts)
        
    @core.undo_chunk    
    def _sharpen_weights(self):
        
        selection = cmds.ls(sl = True, flatten = True)
        
        verts = []

        thing = selection[0]

        if geo.is_a_mesh(thing):
            verts = geo.get_vertices(thing)
        
        if geo.is_a_vertex(thing):
            verts = selection
    
        get_count = self.count_sharpen_weights.get_value()
        percent = self.percent_sharpen_weights.get_value()
        
        deform.sharpen_skin_weights(verts, get_count, percent)
    