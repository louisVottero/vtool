# Copyright (C) 2024 Louis Vottero louis.vot@gmail.com    All rights reserved.

from __future__ import absolute_import
from __future__ import print_function

from ... import qt_ui, qt
from ... import util, util_file

if util.is_in_maya():
    import maya.cmds as cmds

from .. import ui_core

from .. import blendshape
from .. import core
from .. import geo
from .. import attr
from .. import space
from .. import deform
from .. import rigs_util
from .. import curve

from . import ui_check
from . import ui_picker
from . import ui_model
from . import ui_anim

from ...process_manager import ui_process_manager
from ...process_manager import ui_settings
from ...ramen.ui_lib import ui_ramen
from ...script_manager import script_view


def pose_manager(shot_sculpt_only=False):
    from vtool.maya_lib.ui_lib import ui_corrective
    ui_core.delete_workspace_control(ui_corrective.PoseManager.title + 'WorkspaceControl')

    window = ui_corrective.PoseManager(shot_sculpt_only)

    window.show()

    return window


def shape_combo():
    from vtool.maya_lib.ui_lib import ui_shape_combo
    ui_core.delete_workspace_control(ui_shape_combo.ComboManager.title + 'WorkspaceControl')

    window = ui_shape_combo.ComboManager()
    window.show()
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


def process_manager(directory=None):
    ui_core.delete_workspace_control(ProcessMayaWindow.title + 'WorkspaceControl')
    window = ProcessMayaWindow(load_settings=False)

    if directory:
        window.set_directory(directory)

    window.show()
    return window


def process_manager_settings():
    ui_core.delete_workspace_control(ProcessMayaSettingsWindow.title + 'WorkspaceControl')
    window = ProcessMayaSettingsWindow()

    window.show()

    return window


def presets():
    window = ui_presets.Presets()

    return window


class ProcessMayaWindow(ui_core.MayaDockMixin, ui_process_manager.ProcessManagerWindow):
    title = 'VETALA'

    def __init__(self, load_settings=False):
        super(ProcessMayaWindow, self).__init__(load_settings=load_settings)


class ProcessMayaSettingsWindow(ui_core.MayaDockMixin, ui_settings.SettingsWidget):
    title = 'VETALA Settings'

    def __init__(self):
        super(ProcessMayaSettingsWindow, self).__init__()


class RamenMayaWindow(ui_core.MayaDockMixin, ui_ramen.MainWindow):
    title = 'RAMEN'

    def __init__(self):
        super(RamenMayaWindow, self).__init__()


class ScriptMayaWindow(ui_core.MayaDockMixin, script_view.ScriptManagerWidget):
    title = 'Scripts'

    def __init__(self):
        super(ScriptMayaWindow, self).__init__()


vetala_version = util_file.get_vetala_version()


class RigManager(qt_ui.DirectoryWindow):

    def __init__(self):
        super(RigManager, self).__init__()

    def _build_widgets(self):

        self.main_layout.setContentsMargins(10, 10, 10, 10)

        manager_group = qt.QGroupBox('Applications')
        manager_group.setFlat(True)
        manager_layout = qt.QVBoxLayout()
        manager_layout.setContentsMargins(10, 10, 10, 10)
        manager_layout.setSpacing(2)
        manager_layout.setAlignment(qt.QtCore.Qt.AlignCenter)

        manager_group.setLayout(manager_layout)

        button_width = util.scale_dpi(150)

        manager_layout.addSpacing(15)

        h_layout = qt.QHBoxLayout()
        other_buttons_layout = qt.QVBoxLayout()

        manager_layout.addLayout(h_layout)

        icon = qt_ui.get_icon('vetala.png')
        icon_size = util.scale_dpi(48)

        process_button = qt_ui.BasicButton(icon, util.get_custom('vetala_name', 'VETALA'))
        process_button.setIconSize(qt.QtCore.QSize(icon_size, icon_size))
        process_button.setFlat(True)
        process_button.setMinimumHeight(util.scale_dpi(icon_size))
        process_button.clicked.connect(self._process_manager)
        process_button.setMinimumWidth(button_width)
        process_button.setToolTip('Manage and rebuild rigs.')

        h_layout.addWidget(process_button)
        h_layout.addSpacing(15)
        h_layout.addLayout(other_buttons_layout)

        pose_button = qt_ui.BasicButton('Correctives')
        pose_button.clicked.connect(self._pose_manager)
        pose_button.setMinimumWidth(button_width)
        pose_button.setToolTip('Create correctives on meshes deformed by a rig.')
        other_buttons_layout.addWidget(pose_button)

        shape_combo_button = qt_ui.BasicButton('Shape Combos')
        shape_combo_button.clicked.connect(self._shape_combo)
        shape_combo_button.setMinimumWidth(button_width)
        shape_combo_button.setToolTip('Create combo shapes for use in facial setups.')
        other_buttons_layout.addWidget(shape_combo_button)

        check_button = qt_ui.BasicButton('Checks - ALPHA')
        check_button.clicked.connect(self._checker)
        check_button.setMinimumWidth(button_width)

        other_buttons_layout.addWidget(check_button)

        picker_button = qt_ui.BasicButton('Picker - ALPHA')
        picker_button.clicked.connect(self._picker)
        picker_button.setMinimumWidth(button_width)
        picker_button.setToolTip('Create a picker for the character that gets stored on "picker_gr" node.')

        presets_button = qt_ui.BasicButton('Presets - ALPHA')
        presets_button.clicked.connect(self._presets)
        presets_button.setMinimumWidth(button_width)
        presets_button.setToolTip('Presets creates a node in Maya called "presets" that stores attribute values.'
                                  ' Values can be read from referenced assets in the FX tab.')

        manager_layout.addSpacing(15)

        tool_group = qt_ui.Group('Utilities')
        tool_group.set_collapsable(False)
        tool_group.setFlat(True)

        tool_tab = qt.QTabWidget()

        deformation_widget = DeformWidget()
        structure_widget = StructureWidget()
        control_widget = ControlWidget()
        tool_group.main_layout.addWidget(tool_tab)

        model_widget = ui_model.ModelManager(scroll=True)

        tool_tab.addTab(structure_widget, 'Structure')
        tool_tab.addTab(control_widget, 'Controls')
        tool_tab.addTab(deformation_widget, 'Deform')
        tool_tab.addTab(model_widget, 'Model')
        tool_tab.addTab(ui_anim.AnimationManager(), 'Animate')

        self.main_layout.addWidget(manager_group)
        self.main_layout.addSpacing(15)
        self.main_layout.addWidget(tool_group)

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
        if cmds.workspaceControl(name, exists=True):
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

        info = qt.QLabel('Apply the skin from the source to the target.\n'
                         'This will automatically skin the target\nand copy skin weights.'
                         '\n\nSet exclude and include joints\nThis helps control what joints get applied.')

        self.exclude = qt_ui.GetString('Exclude Joints')
        self.exclude.set_use_button(True)
        self.exclude.set_placeholder('Optional')
        self.include = qt_ui.GetString('Include Joints')
        self.include.set_use_button(True)
        self.include.set_placeholder('Optional')

        self.uv = qt_ui.GetBoolean('Copy weights using UVs')

        label = qt.QLabel('Select source and target mesh.')

        run = qt_ui.BasicButton('Run')
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

        selection = cmds.ls(sl=True)
        is_group = False

        if selection and len(selection) == 2:
            if not geo.is_a_mesh(selection[0]):
                if not geo.is_a_surface(selection[0]):
                    if not geo.is_a_curve(selection[0]):
                        util.warning('Please select a mesh, surface or curve as the first selection.')
                        return

            if not geo.is_a_mesh(selection[1]):
                if not geo.is_a_surface(selection[1]):
                    if not geo.is_a_curve(selection[1]):
                        # util.warning('Please select a mesh, surface or curve as the second selection.')
                        is_group = True
                        # return

            if is_group:
                deform.skin_group_from_mesh(selection[0], selection[1], include_joints=exclude, exclude_joints=include, leave_existing_skins=False)
            else:
                deform.skin_mesh_from_mesh(selection[0], selection[1], exclude_joints=exclude, include_joints=include,
                                           uv_space=uv)
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
        mirror = qt_ui.BasicButton('Mirror Selected')

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

    def __init__(self, scroll=True):
        super(RigWidget, self).__init__(scroll=scroll)

        self.main_layout.setContentsMargins(0, 0, 0, 0)


class StructureWidget(RigWidget):

    def __init__(self, scroll=True):
        super(StructureWidget, self).__init__(scroll=scroll)

    def _build_widgets(self):

        self.setMinimumHeight(util.scale_dpi(300))

        main_layout = self.main_layout

        main_layout.addSpacing(10)
        main_layout.addLayout(self._build_create_widgets())
        main_layout.addSpacing(10)
        main_layout.addLayout(self._build_transfer_widgets())
        main_layout.addWidget(qt_ui.add_separator(30))
        main_layout.addLayout(self._build_mirror_widgets())
        main_layout.addWidget(qt_ui.add_separator(30))
        main_layout.addLayout(self._build_orient_widgets())

    def _build_create_widgets(self):
        create_layout = qt.QHBoxLayout()

        create_group = qt_ui.Group('Create')
        create_group.collapse_group()

        set_color = qt_ui.BasicButton('Open Color Picker')
        set_color.clicked.connect(self._set_color)

        create_group.main_layout.addWidget(set_color)
        create_group.main_layout.addSpacing(5)

        mirror_create = qt_ui.BasicButton('Mirror Create')
        mirror_create.clicked.connect(self._mirror_create)

        subdivide_joint_button = qt_ui.GetIntNumberButton('Subdivide Joint')
        subdivide_joint_button.set_value(1)
        subdivide_joint_button.clicked.connect(self._subdivide_joint)
        subdivide_joint_button.setToolTip('select parent and child joint')

        joints_on_curve = qt_ui.GetIntNumberButton('Create Joints On Curve')
        joints_on_curve.set_value(10)

        joints_in_tube = qt_ui.GetIntNumberButton('Create Joints In Tube')
        joints_in_tube.set_value(10)

        snap_to_curve = qt_ui.GetIntNumberButton('Snap Joints to Curve')

        create_curve_from_joints = qt_ui.BasicButton('Create Curve from Joints')
        create_curve_in_tube = qt_ui.BasicButton('Create Curve In Tube')

        joints_on_curve.clicked.connect(self._joints_on_curve)
        joints_in_tube.clicked.connect(self._joints_in_tube)
        snap_to_curve.clicked.connect(self._snap_joints_to_curve)

        create_curve_from_joints.clicked.connect(self._create_curve_from_joints)
        create_curve_in_tube.clicked.connect(self._create_curve_in_tube)

        create_layout.addWidget(create_group)

        create_group.main_layout.addWidget(mirror_create)
        create_group.main_layout.addSpacing(5)
        create_group.main_layout.addWidget(subdivide_joint_button)
        create_group.main_layout.addWidget(joints_on_curve)
        create_group.main_layout.addWidget(joints_in_tube)
        create_group.main_layout.addWidget(snap_to_curve)
        create_group.main_layout.addWidget(create_curve_from_joints)
        create_group.main_layout.addWidget(create_curve_in_tube)

        return create_layout

    def _build_mirror_widgets(self):

        mirror_translate_layout = qt.QVBoxLayout()

        mirror_group = qt_ui.Group('Mirror Tools')
        mirror_group.collapse_group()

        mirror = qt_ui.BasicButton('Mirror Transforms')
        mirror.clicked.connect(self._mirror)

        mirror_sel = qt_ui.BasicButton('Mirror Selected')
        mirror_sel.clicked.connect(self._mirror_selected)

        mirror_off = qt_ui.BasicButton('Set Skip Mirror')
        mirror_off.clicked.connect(self._mirror_off)
        mirror_on = qt_ui.BasicButton('Set Unskip Mirror')
        mirror_on.clicked.connect(self._mirror_on)

        mirror_right_left = qt_ui.BasicButton('Mirror R to L')
        mirror_right_left.clicked.connect(self._mirror_r_l)

        mirror_meshes = qt_ui.BasicButton('Mirror Mesh Positions L to R')
        mirror_meshes.clicked.connect(self._mirror_meshes)

        mirror_curves = qt_ui.BasicButton('Mirror Curves')
        mirror_curves.clicked.connect(self._mirror_curves)

        mirror_invert = qt_ui.BasicButton('Mirror Invert')
        mirror_invert.clicked.connect(self._mirror_invert)

        mirror_translate_layout.addWidget(mirror)
        mirror_translate_layout.addSpacing(5)
        mirror_translate_layout.addWidget(mirror_sel)
        mirror_translate_layout.addSpacing(5)
        mirror_translate_layout.addWidget(mirror_group)

        mirror_group.main_layout.addWidget(mirror_right_left)
        mirror_group.main_layout.addWidget(mirror_meshes)
        mirror_group.main_layout.addWidget(mirror_curves)
        mirror_group.main_layout.addWidget(mirror_invert)
        mirror_group.main_layout.addSpacing(3)
        mirror_group.main_layout.addWidget(mirror_off)
        mirror_group.main_layout.addWidget(mirror_on)

        return mirror_translate_layout

    def _build_orient_widgets(self):

        orient_layout = qt.QVBoxLayout()

        orient_group = qt_ui.Group('Orient Tools')
        orient_group.collapse_group()

        add_orient = qt_ui.BasicButton('Add Orient Attributes')
        add_orient.clicked.connect(self._add_orient)

        remove_orient = qt_ui.BasicButton('Remove Orient Attributes')
        remove_orient.clicked.connect(self._remove_orient)

        add_joint_orient = qt_ui.BasicButton('Add Joint Aim and Up')
        add_joint_orient.clicked.connect(self._add_joint_orient)

        skip_orient = qt_ui.BasicButton('Set Skip Orient')
        unskip_orient = qt_ui.BasicButton('Set Unskip Orient')
        skip_orient.clicked.connect(self._skip_orient)
        unskip_orient.clicked.connect(self._unskip_orient)

        orient_button_layout = qt.QVBoxLayout()

        orient_joints = qt_ui.BasicButton('Orient Joints')
        orient_joints.clicked.connect(self._orient)

        orient_hier_joints = qt_ui.BasicButton('Orient Hierarchy')
        orient_hier_joints.clicked.connect(self._orient_selected_hier)

        orient_sel_joints = qt_ui.BasicButton('Orient Selected')
        orient_sel_joints.clicked.connect(self._orient_selected_only)

        self.joint_axis_check = qt.QCheckBox('Joint Axis Visibility')
        self.joint_axis_check.stateChanged.connect(self._set_joint_axis_visibility)

        auto_orient = qt_ui.BasicButton('Auto Orient Hierarchy')
        auto_orient.setMinimumHeight(util.scale_dpi(20))
        auto_orient.setMinimumWidth(util.scale_dpi(125))
        auto_orient.clicked.connect(self._auto_orient_attributes)

        mirror_orient = qt_ui.BasicButton('Mirror')
        mirror_orient.setMinimumHeight(20)
        mirror_orient.clicked.connect(self._mirror_orient_attributes)

        orient_button_layout.addWidget(orient_joints)
        orient_button_layout.addSpacing(5)
        orient_button_layout.addWidget(orient_hier_joints)
        orient_button_layout.addSpacing(5)
        orient_button_layout.addWidget(orient_sel_joints)

        orient_group.main_layout.addWidget(add_orient)
        orient_group.main_layout.addWidget(remove_orient)

        auto_orient_group = qt_ui.Group('Auto Orient')
        auto_orient_group.set_collapsable(False)

        combo_layout = qt.QHBoxLayout()
        combo_forward = qt.QComboBox()
        combo_forward.addItems(['X', 'Y', 'Z'])
        combo_forward.setCurrentIndex(2)
        combo_up = qt.QComboBox()
        combo_up.addItems(['X', 'Y', 'Z'])
        combo_up.setCurrentIndex(1)
        forward_label = qt.QLabel('Forward')
        combo_layout.addWidget(forward_label)
        combo_layout.addWidget(combo_forward)
        up_label = qt.QLabel('Up')
        combo_layout.addWidget(up_label)
        combo_layout.addWidget(combo_up)
        auto_orient_group.main_layout.addLayout(combo_layout)
        auto_orient_group.main_layout.addWidget(auto_orient)

        self.combo_forward = combo_forward
        self.combo_up = combo_up

        orient_group.main_layout.addSpacing(5)
        orient_group.main_layout.addWidget(add_joint_orient)
        orient_group.main_layout.addSpacing(3)
        orient_group.main_layout.addWidget(skip_orient)
        orient_group.main_layout.addWidget(unskip_orient)

        orient_group.main_layout.addSpacing(2)
        orient_group.main_layout.addWidget(auto_orient_group)

        orient_button_layout.addSpacing(5)
        orient_button_layout.addWidget(self.joint_axis_check)

        orient_layout.addLayout(orient_button_layout)

        orient_layout.addSpacing(5)
        orient_layout.addWidget(orient_group)

        return orient_layout

    def _build_transfer_widgets(self):
        transfer_layout = qt.QHBoxLayout()

        transfer_group = qt_ui.Group('Transfer')
        transfer_group.collapse_group()

        transfer_joints = qt_ui.BasicButton('Quick Transfer Bones  ( Mesh to Mesh with same topology )')
        transfer_joints.clicked.connect(self._transfer_joints)

        label = qt.QLabel("""The tool below allows for accurate bone transfer. 
Bones must be tagged with components of a mesh to work.
Start By using the Auto Find Joint Vertex button to automatically find nearby components to each joint.
On Transfer the component order of the target mesh should match the component order stored on the bones.
""")
        label.setWordWrap(True)
        label.setSizePolicy(qt.QSizePolicy.Maximum, qt.QSizePolicy.Maximum)

        auto_layout = qt.QVBoxLayout()
        self.transfer_get_root = qt_ui.GetString('Root Joint   ')
        self.transfer_get_root.set_use_button(True)
        self.transfer_get_root.set_placeholder('This hierarchy will be tagged')
        self.transfer_get_root.set_select_button(True)

        self.transfer_get_mesh = qt_ui.GetString('Source Mesh')
        self.transfer_get_mesh.set_use_button(True)
        self.transfer_get_mesh.set_placeholder('The mesh to search for components for tagging')
        self.transfer_get_mesh.set_select_button(True)

        transfer_find_layout = qt.QVBoxLayout()
        transfer_find_layout.setAlignment(qt.QtCore.Qt.AlignLeft)
        transfer_find_layout1 = qt.QHBoxLayout()
        transfer_find_layout2 = qt.QHBoxLayout()

        self.transfer_find_radius = qt_ui.GetNumber('radius')
        self.transfer_find_radius.set_value(1.0)
        self.transfer_find_increment = qt_ui.GetNumber('grow')
        self.transfer_find_increment.set_value(1.25)
        self.transfer_find_count = qt_ui.GetNumber('minimum_count')
        self.transfer_find_count.set_value(20)
        self.transfer_find_iterations = qt_ui.GetNumber('maximum_iterations')
        self.transfer_find_iterations.set_value(30)

        transfer_find_layout1.addWidget(self.transfer_find_radius)
        transfer_find_layout1.addWidget(self.transfer_find_increment)
        transfer_find_layout2.addWidget(self.transfer_find_count)
        transfer_find_layout2.addWidget(self.transfer_find_iterations)

        transfer_auto_find_vertices = qt_ui.BasicButton('Auto Find Joint and Vertex')
        transfer_auto_find_vertices.clicked.connect(self._transfer_auto_find)
        auto_layout.addWidget(self.transfer_get_root)
        auto_layout.addWidget(self.transfer_get_mesh)
        auto_layout.addLayout(transfer_find_layout)
        auto_layout.addWidget(transfer_auto_find_vertices)

        transfer_find_layout.addSpacing(util.scale_dpi(5))
        transfer_find_layout.addLayout(transfer_find_layout1)
        transfer_find_layout.addSpacing(util.scale_dpi(5))
        transfer_find_layout.addLayout(transfer_find_layout2)
        transfer_find_layout.addSpacing(util.scale_dpi(10))

        joint_vertex_select_tool = qt_ui.BasicButton('Activate Joint and Vertices Selection Tool')
        joint_vertex_select_tool.clicked.connect(self._transfer_joint_vertex_select_tool)

        update_joint = qt_ui.BasicButton('Store Selected Bone Components')
        update_joint.setMinimumHeight(40)
        update_joint.clicked.connect(self._transfer_update_bone_components)

        select_components = qt_ui.BasicButton('Select Stored Components for Selected Bone and Mesh(es)')
        select_components.clicked.connect(self._transfer_select_bone_components)

        mirror_components = qt_ui.BasicButton('Mirror All Stored Components on X Plane on Selected Meshes')
        mirror_components.clicked.connect(self._mirror_bone_components_x)

        transfer = qt_ui.BasicButton('Transfer Bones ( Select Target Mesh )')
        transfer.setMinimumHeight(60)
        transfer.clicked.connect(self._transfer_accurate)

        transfer_group.main_layout.addWidget(transfer_joints)
        transfer_group.main_layout.addWidget(qt_ui.add_separator(20))

        transfer_group.main_layout.addWidget(label)
        transfer_group.main_layout.addSpacing(10)

        transfer_group.main_layout.addLayout(auto_layout)
        transfer_group.main_layout.addSpacing(20)

        transfer_group.main_layout.addWidget(joint_vertex_select_tool)
        transfer_group.main_layout.addSpacing(5)
        transfer_group.main_layout.addWidget(update_joint)
        transfer_group.main_layout.addSpacing(5)
        transfer_group.main_layout.addWidget(select_components)
        transfer_group.main_layout.addSpacing(10)
        transfer_group.main_layout.addWidget(mirror_components)
        transfer_group.main_layout.addSpacing(20)
        transfer_group.main_layout.addWidget(transfer)

        transfer_layout.addWidget(transfer_group)

        return transfer_layout

    def _set_color(self):

        picker = qt_ui.ColorPicker()
        picker.apply_to_selected.connect(self._set_color_selected)
        picker.show()

    def _set_color_selected(self, color):
        set_color_selected(color)

    def _subdivide_joint(self, number):
        space.subdivide_joint(count=number)

    def _add_orient(self):
        selection = cmds.ls(sl=True, type='joint')

        if not selection:
            core.print_warning('Please select joints to add orient to.')

        attr.add_orient_attributes(selection, context_sensitive=True)
        core.print_help('Added orient attributes to the selected joints.')

    def _remove_orient(self):

        selection = cmds.ls(sl=True, type='joint')

        if not selection:
            core.print_warning('Please select joints to remove orient from.')

        attr.remove_orient_attributes(selection)
        core.print_help('Removed orient attributes from the selected joints.')

    @core.undo_chunk
    def _add_joint_orient(self):
        selection = cmds.ls(sl=True, type='joint')

        if not selection:
            core.print_warning('Please select joints to add aim and up to.')

        for thing in selection:
            space.add_orient_joint(thing)

        core.print_help('Added aim and up to selected joints.')

    @core.undo_chunk
    def _orient(self):

        selection = cmds.ls(sl=True)

        oriented = space.orient_attributes_all()

        if oriented:
            core.print_help('Oriented joints with orient attributes.')
        if not oriented:
            core.print_warning('No joints oriented. Check that there are joints with orient attributes.')

        cmds.select(selection)

    @core.undo_chunk
    def _orient_selected_hier(self):
        selected = cmds.ls(sl=True, type='joint')

        if not selected:
            core.print_warning('Please select joints to orient.')

        oriented = space.orient_attributes(selected)

        if oriented:
            core.print_help('Oriented selected joints')

        cmds.select(selected)

    def _orient_selected_only(self):

        selected = cmds.ls(sl=True, type='joint')

        if not selected:
            core.print_warning('Please select joints to orient.')

        oriented = space.orient_attributes(selected, hierarchy=False)

        if oriented:
            core.print_help('Oriented selected joints')

        cmds.select(selected)

    def _auto_orient_attributes(self):

        scope = cmds.ls(sl=True, l=True)

        forward_axis = self.combo_forward.currentText()
        up_axis = self.combo_up.currentText()

        if forward_axis == up_axis:
            core.print_warning('Forward Axis cannot be the same as Up Axis')
            cmds.select(scope)
            return

        for thing in scope:
            space.auto_generate_orient_attributes(thing, forward_axis, up_axis)
            space.orient_attributes([thing], initialize_progress=True, hierarchy=True)

        cmds.select(scope)

    def _mirror_orient_attributes(self):
        pass

    def _unskip_orient(self):

        selection = cmds.ls(sl=True, type='joint')

        for thing in selection:
            if cmds.objExists('%s.active' % thing):
                cmds.setAttr('%s.active' % thing, 1)

        if not selection:
            core.print_help('Please select joints to unskip running orient.')

    def _skip_orient(self):

        selection = cmds.ls(sl=True, type='joint')

        for thing in selection:
            if cmds.objExists('%s.active' % thing):
                cmds.setAttr('%s.active' % thing, 0)

        if not selection:
            core.print_help('Please select joints to skip running orient.')

    @core.undo_chunk
    def _mirror(self, *args):

        fixed = space.mirror_xform()

        if fixed:
            core.print_help('Mirrored transforms left to right')
        if not fixed:
            core.print_warning('No joints mirrored. Check there are joints on the left that can mirror right.'
                               '  Make sure translate rotate do not have connections.')

    @core.undo_chunk
    def _mirror_selected(self, *args):
        selected = cmds.ls(sl=True, type='transform')

        if not selected:
            core.print_warning('Please select joints to mirror.')
            return

        fixed = space.mirror_xform(transforms=selected)

        if fixed:
            core.print_help('Mirrored selected left to right')

    def _mirror_on(self):

        transforms = cmds.ls(sl=True, type='transform')

        if not transforms:
            core.print_warning('Please select some joints or transforms to unskip.')
            return

        for transform in transforms:
            space.mirror_toggle(transform, True)

        if transforms:
            core.print_help('mirror attribute set on. This transform will be affected by mirror transforms.')

    def _mirror_off(self):

        transforms = cmds.ls(sl=True, type='transform')

        if not transforms:
            core.print_warning('Please select some joints or transforms to unskip.')
            return

        for transform in transforms:
            space.mirror_toggle(transform, False)

        if transforms:
            core.print_help('mirror attribute set off. This transform will no longer be affected by mirror transforms.')

    @core.undo_chunk
    def _mirror_r_l(self):

        selected = cmds.ls(sl=True, type='transform')
        fixed = space.mirror_xform(transforms=selected, left_to_right=False)

        if selected and fixed:
            core.print_warning('Only mirrored selected right to left')
        if not selected and fixed:
            core.print_help('Mirrored transforms right to left')
        if not fixed:
            core.print_warning('No joints mirrored. Check there are joints on the right that can mirror left.'
                               '  Check your selected transform is not on the left.'
                               ' Make sure translate rotate do not have connections.')

    @core.undo_chunk
    def _mirror_create(self):

        selected = cmds.ls(sl=True, type='transform')

        created = space.mirror_xform(transforms=selected, create_if_missing=True)

        if created and selected:
            core.print_warning('Only created transforms on the right side that were selected on the left.')
        if created and not selected:
            core.print_help('Created transforms on the right side that were on the left.')
        if not created:
            core.print_warning('No transforms created. Check that there are missing transforms on the right or that'
                               ' the right side does not already exist. Check your selected transform is on the left.')

    @core.undo_chunk
    def _mirror_curves(self, *args):

        rigs_util.mirror_curve()

    def _mirror_meshes(self):

        meshes = cmds.ls(type='mesh')

        mesh_dict = {}
        for mesh in meshes:
            parent = cmds.listRelatives(mesh, p=True)[0]
            mesh_dict[parent] = None

        space.mirror_xform(transforms=list(mesh_dict.keys()), skip_meshes=False)

    @core.undo_chunk
    def _mirror_invert(self):

        selection = cmds.ls(sl=True)

        for thing in selection:
            space.mirror_invert(thing)

    def _joints_on_curve(self, count):
        selection = cmds.ls(sl=True)

        for thing in selection:
            if geo.is_a_curve(thing):
                geo.create_oriented_joints_on_curve(thing, count)

    def _joints_in_tube(self, count):
        selection = cmds.ls(sl=True)
        for thing in selection:
            if geo.is_a_mesh(thing):
                geo.create_joints_in_tube(thing, '%s_1' % thing, count)

    def _snap_joints_to_curve(self, count):

        scope = cmds.ls(sl=True)

        if not scope:
            return

        node_types = core.get_node_types(scope)

        joints = []

        if 'joint' in node_types:
            joints = node_types['joint']

        curve = None
        if 'nurbsCurve' in node_types:
            curves = node_types['nurbsCurve']
            curve = curves[0]

        if joints:
            geo.snap_joints_to_curve(joints, curve, count)

    def _create_curve_from_joints(self):

        joints = cmds.ls(sl=True, type='joint')

        geo.transforms_to_curve(joints, len(joints), 'curve_joints')

    def _create_curve_in_tube(self):

        selection = cmds.ls(sl=True)
        for thing in selection:
            if geo.is_a_mesh(thing):
                geo.create_curve_in_tube(thing, 'curve_%s_1' % thing)

    def _transfer_joints(self):

        scope = cmds.ls(sl=True)

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

        selection = cmds.ls(sl=True)

        if not selection:
            return

        node_types = core.get_node_types(selection)

        if 'mesh' not in node_types:
            return

        meshes = node_types['mesh']

        for mesh in meshes:
            rigs_util.process_joint_weight_to_parent(mesh)

    def _transfer_auto_find(self):

        root = self.transfer_get_root.get_text()
        mesh = self.transfer_get_mesh.get_text()

        root = util.convert_str_to_list(root)
        root = cmds.ls(root, type='joint')
        rels = []
        if len(root) == 1:
            rels = cmds.listRelatives(root, type='joint', ad=True)
        skeleton = root
        if rels:
            skeleton = rels + root

        skeleton.reverse()

        radius = self.transfer_find_radius.get_value()
        grow = self.transfer_find_increment.get_value()
        count = self.transfer_find_count.get_value()
        iterations = self.transfer_find_iterations.get_value()

        transfer_accurate = deform.XformTransferAccurate()
        transfer_accurate.set_source_mesh(mesh)
        transfer_accurate.set_find_verts_options(grow, count, iterations)
        transfer_accurate.tag_skeleton(skeleton, radius)

    def _transfer_joint_vertex_select_tool(self):
        core.get_joint_vertex_context()

    def _transfer_update_bone_components(self):

        selection = cmds.ls(sl=True)
        joint = None
        vertices = []

        for thing in selection:
            if cmds.nodeType(thing) == 'joint':
                joint = thing
            if thing.find('.vtx[') > -1:
                vertices.append(thing)

        if not joint or not vertices:
            core.print_warning('Please first select a joint and vertices')
            return

        mesh = geo.get_mesh_from_vertex(vertices[0])

        transfer_accurate = deform.XformTransferAccurate()
        transfer_accurate.set_source_mesh(mesh)
        components = geo.get_strip_vertex_indices(vertices)
        transfer_accurate.tag_bone(joint, components)

    def _transfer_select_bone_components(self):

        selection = cmds.ls(sl=True)
        joint = None
        meshes = []

        for thing in selection:
            if cmds.nodeType(thing) == 'joint':
                joint = thing
            if geo.is_a_mesh(thing):
                meshes.append(thing)

        if not joint or not meshes:
            core.print_warning('Please first select a joint and a mesh.')
            return

        cmds.select(cl=True)

        cmds.selectType(ocm=True, alc=False)
        cmds.selectType(ocm=True, vertex=True)
        cmds.select(meshes[0], deselect=True)
        cmds.select(joint, addFirst=True)

        cmds.hilite(meshes[0])
        transfer_accurate = deform.XformTransferAccurate()
        transfer_accurate.set_source_mesh(meshes[0])
        transfer_accurate.select_bone_components(joint)

    def _transfer_accurate(self):
        bones = cmds.ls(type='joint')
        found = [bone for bone in bones if cmds.objExists('%s.vetalaTransferData' % bone)]

        selection = cmds.ls(sl=True, l=True, type='transform')
        node_types = core.get_node_types(selection)

        if 'mesh' not in node_types:
            util.warning('Please select a mesh to transfer to.')
            return

        meshes = node_types['mesh']

        transfer = deform.XformTransferAccurate()
        transfer.set_target_mesh(meshes[0])
        transfer.transfer_skeleton(found)

    def _mirror_bone_components_x(self):

        selection = cmds.ls(sl=True, l=True, type='transform')
        node_types = core.get_node_types(selection)

        if 'mesh' not in node_types:
            util.warning('Please select a mesh to transfer to.')
            return

        meshes = node_types['mesh']

        for mesh in meshes:
            transfer = deform.XformTransferAccurate()
            transfer.set_source_mesh(mesh)
            transfer.mirror_components()

    def _set_joint_axis_visibility(self):

        bool_value = self.joint_axis_check.isChecked()

        rigs_util.joint_axis_visibility(bool_value)


class ControlWidget(RigWidget):

    def __init__(self, scroll=True):
        super(ControlWidget, self).__init__(scroll=scroll)

        self.scale_controls = []
        self.last_scale_value = None
        self.last_scale_center_value = None

    def _build_widgets(self):

        mirror_control = qt_ui.BasicButton('Mirror Selected Controls')
        mirror_control.clicked.connect(self._mirror_control)

        mirror_controls = qt_ui.BasicButton('Mirror All Controls')
        mirror_controls.clicked.connect(self._mirror_controls)
        mirror_controls.setMinimumHeight(40)

        set_color = qt_ui.BasicButton('Open Color Picker')
        set_color.clicked.connect(self._set_color)

        curve_names = curve.get_library_shape_names()

        curve_names = sorted(curve_names)
        self.curve_shape_combo = qt.QComboBox()
        self.curve_shape_combo.addItems(curve_names)
        self.curve_shape_combo.setMaximumWidth(110)

        curve_shape_label = qt.QLabel('Curve Type')

        replace_curve_shape = qt_ui.BasicButton('Replace Curve Shape')
        replace_curve_shape.clicked.connect(self._replace_curve_shape)

        replace_curve_layout = qt.QHBoxLayout()
        replace_curve_layout.addWidget(replace_curve_shape)
        replace_curve_layout.addSpacing(5)
        replace_curve_layout.addWidget(curve_shape_label, alignment=qt.QtCore.Qt.AlignRight)
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

        self.fix_sub_controls = qt_ui.BasicButton('Fix Sub Controls')
        self.fix_sub_controls.clicked.connect(rigs_util.fix_sub_controls)

        project_curve = qt_ui.GetNumberButton('Project Curves on Mesh')
        project_curve.set_value(1)
        project_curve.set_value_label('Offset')
        project_curve.clicked.connect(self._project_curve)

        snap_curve = qt_ui.GetNumberButton('Snap Curves to Mesh')
        snap_curve.set_value(1)
        snap_curve.set_value_label('Offset')
        snap_curve.clicked.connect(self._snap_curve)

        convert_curve_to_edge_loop = qt_ui.BasicButton('Convert Curve to Edge Loop')
        convert_curve_to_border_edge = qt_ui.BasicButton('Convert Curve to Border Edge')

        convert_curve_to_edge_loop.clicked.connect(self._curve_from_edge)
        convert_curve_to_border_edge.clicked.connect(self._curve_from_border)

        self.main_layout.addWidget(set_color)
        self.main_layout.addSpacing(15)
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

        self.main_layout.addSpacing(10)
        self.main_layout.addWidget(convert_curve_to_edge_loop)
        self.main_layout.addWidget(convert_curve_to_border_edge)

    def _set_color(self):

        picker = qt_ui.ColorPicker()
        picker.apply_to_selected.connect(self._set_color_selected)
        picker.show()

    def _set_color_selected(self, color):
        set_color_selected(color)

    def _mirror_control(self):

        selection = cmds.ls(sl=True)
        if not selection:
            return

        for thing in selection:
            rigs_util.mirror_control(thing)

    def _mirror_controls(self):

        rigs_util.mirror_controls()

    def _rotate_x_control(self):

        selection = cmds.ls(sl=True)

        for sel in selection:

            if core.has_shape_of_type(sel, 'nurbsCurve') or core.has_shape_of_type(sel, 'nurbsSurface'):
                x_value = self.rotate_x_widget.get_value()

                geo.rotate_shape(sel, x_value, 0, 0)

    def _rotate_y_control(self):

        selection = cmds.ls(sl=True)

        for sel in selection:

            if core.has_shape_of_type(sel, 'nurbsCurve') or core.has_shape_of_type(sel, 'nurbsSurface'):
                y_value = self.rotate_y_widget.get_value()

                geo.rotate_shape(sel, 0, y_value, 0)

    def _rotate_z_control(self):

        selection = cmds.ls(sl=True)

        for sel in selection:

            if core.has_shape_of_type(sel, 'nurbsCurve') or core.has_shape_of_type(sel, 'nurbsSurface'):
                z_value = self.rotate_z_widget.get_value()

                geo.rotate_shape(sel, 0, 0, z_value)

    def _reset_scale_slider(self):

        self.scale_controls = []
        self.last_scale_value = None

        cmds.undoInfo(closeChunk=True)

    def _reset_scale_center_slider(self):

        self.scale_center_controls = []
        self.last_scale_center_value = None

        cmds.undoInfo(closeChunk=True)

    def _get_components(self, thing):

        shapes = core.get_shapes(thing)

        return core.get_components_from_shapes(shapes)

    def _size_controls(self):

        value = self.scale_control_button.get_value()
        rigs_util.scale_controls(value)

    def _scale_control(self, value):

        if self.last_scale_value is None:
            self.last_scale_value = 0

            cmds.undoInfo(openChunk=True)

        if value == self.last_scale_value:
            self.last_scale_value = None
            return

        pass_value = None
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

                pivot = cmds.xform(thing, q=True, rp=True, ws=True)

                if components:
                    cmds.scale(pass_value, pass_value, pass_value, components, p=pivot, r=True)

        self.last_scale_value = value

    def _scale_center_control(self, value):

        if self.last_scale_center_value is None:
            self.last_scale_center_value = 0
            cmds.undoInfo(openChunk=True)

        if value == self.last_scale_center_value:
            self.last_scale_center_value = None
            return

        pass_value = None
        if value > self.last_scale_center_value:
            pass_value = 1.02
        if value < self.last_scale_center_value:
            pass_value = .99

        things = geo.get_selected_curves()

        if not things:
            return

        if things:
            for thing in things:

                shapes = core.get_shapes(thing, shape_type='nurbsCurve')
                components = core.get_components_from_shapes(shapes)

                bounding = space.BoundingBox(components)
                pivot = bounding.get_center()

                if components:
                    cmds.scale(pass_value, pass_value, pass_value, components, pivot=pivot, r=True)

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

    @core.undo_chunk
    def _curve_from_edge(self):

        scope = cmds.ls(sl=True)
        controls = []
        for thing in scope:
            if rigs_util.is_control(thing):
                controls.append(thing)

        if not controls:
            core.print_warning('Please select a control.')
            return

        edges = geo.get_edges_in_list(scope)

        if not edges:
            core.print_warning('Please select an edge in the edge loop.')
            return

        curve = geo.create_curve_from_edge_loop(edges[0], 0)

        control_inst = rigs_util.Control(controls[0])
        control_inst.copy_shapes(curve)

        cmds.delete(curve)

    @core.undo_chunk
    def _curve_from_border(self):

        scope = cmds.ls(sl=True)
        controls = []
        for thing in scope:
            if rigs_util.is_control(thing):
                controls.append(thing)

        if not controls:
            core.print_warning('Please select a control.')
            return

        meshes = geo.get_meshes_in_list(scope)

        if not meshes:
            core.print_warning('Select a mesh with border edges.')
            return

        curve = geo.create_curve_from_mesh_border(meshes[0], offset=0)

        if not curve:
            core.print_warning('Could not create border edge from mesh.')
            return

        control_inst = rigs_util.Control(controls[0])
        control_inst.copy_shapes(curve)

        cmds.delete(curve)


class DeformWidget(RigWidget):

    def __init__(self, scroll=False):
        super(DeformWidget, self).__init__(scroll)

    def _build_widgets(self):
        skin_widget = SkinWidget(scroll=True)
        skin_widget.main_layout.setContentsMargins(0, 0, 0, 0)

        group = qt_ui.Group('Deformation Utilities')

        intermediate_button_info = qt.QLabel('This button updates the intermediate object.\n'
                                             'Select a mesh to be the new intermediate.\n'
                                             'And also a mesh with\nskinCluster and/or blendShape.')
        intermediate_button = qt_ui.BasicButton('Blend Into Intermediate')

        intermediate_button.clicked.connect(self._blend_into_intermediate)

        recreate_blends_info = qt.QLabel('Recreate all the targets of a blendshape.\n'
                                         'Select a mesh with blendshape history\n'
                                         'And optionally meshes that should follow.')
        recreate_blends = qt_ui.BasicButton('Recreate Blendshapes')

        recreate_blends.clicked.connect(self._recreate_blends)

        corrective_button_info = qt.QLabel('Select a mesh (in pose) deformed by a \nskinCluster and/or a blendShape\n'
                                           'And also the sculpted mesh to correct it.')
        corrective_button = qt_ui.BasicButton('Create Corrective')

        corrective_button.clicked.connect(self._create_corrective)

        cluster_mesh_info = qt.QLabel('This will add a cluster at the click point\n'
                                      'and go into paint weighting.\nPush button then click on a mesh.')
        cluster_mesh = qt_ui.BasicButton('Create Tweak Cluster')
        cluster_mesh.clicked.connect(self._cluster_tweak_mesh)

        self.main_layout.addWidget(skin_widget)
        # self.main_layout.addSpacing(15)

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
        # this fixed an expand contract bug
        skin_widget.main_layout.addSpacing(15)
        skin_widget.main_layout.addWidget(group)
        # self.main_layout.addWidget(group)

    def _create_corrective(self):
        selection = cmds.ls(sl=True)
        deform.chad_extract_shape(selection[0], selection[1])

    def _cluster_tweak_mesh(self):
        ctx = deform.ClusterTweakCtx()
        ctx.run()

    def _blend_into_intermediate(self):
        deform.blend_into_intermediate()

    def _recreate_blends(self):
        blendshape.recreate_blendshapes()


class SkinWidget(RigWidget):

    def __init__(self, scroll=True):
        super(SkinWidget, self).__init__(scroll)

    def _build_widgets(self):

        self.setMinimumHeight(300)

        group = qt_ui.Group('Edit Skin Weights')
        group.collapse_group()

        weights_label = qt.QLabel('Select a mesh or verts of a single mesh')

        average_weights = qt_ui.BasicButton('Average Weights')
        smooth_weights_layout = qt.QVBoxLayout()
        sub_smooth_weights_layout = qt.QHBoxLayout()
        smooth_weights = qt_ui.BasicButton('Smooth Weights')
        self.count_smooth_weights = qt_ui.GetInteger('Iterations')
        self.count_smooth_weights.set_value(1)

        self.percent_smooth_weights = qt_ui.GetNumber('Percent')
        self.percent_smooth_weights.set_value(1)

        self.smooth_mode = qt_ui.GetInteger('Mode: 0=Broad 1=Tight')
        self.smooth_mode.set_value(1)
        self.smooth_mode.number_widget.setMaximum(1)
        self.smooth_mode.number_widget.setMinimum(0)

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
        sharpen_weights = qt_ui.BasicButton('Sharpen Weights')
        self.count_sharpen_weights = qt_ui.GetInteger('Iterations')
        self.count_sharpen_weights.set_value(1)

        self.percent_sharpen_weights = qt_ui.GetNumber('Percent')
        self.percent_sharpen_weights.set_value(1)

        sharpen_weights_layout.addWidget(self.count_sharpen_weights)
        sharpen_weights_layout.addSpacing(5)
        sharpen_weights_layout.addWidget(self.percent_sharpen_weights)
        # sharpen_weights_layout.addWidget(sharpen_weights)

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

        self._remove_weights_layout(group.main_layout)
        self._transfer_weights_layout(group.main_layout)

        self.main_layout.addWidget(group)
        self.main_layout.addSpacing(15)

        self.main_layout.addWidget(skin_mesh_from_mesh)

    def _remove_weights_layout(self, layout):

        layout.addSpacing(15)
        v_layout = qt.QVBoxLayout()
        button = qt_ui.BasicButton('Remove on Selected Mesh/Vertices')

        self._remove_influence_string = qt_ui.GetString('Influences')
        self._remove_influence_string.set_use_button(True)
        self._remove_influence_string.set_select_button(True)
        self._remove_influence_string.set_text('*_R')

        v_layout.addWidget(self._remove_influence_string)
        v_layout.addWidget(button)

        button.clicked.connect(self._remove_weights)

        layout.addLayout(v_layout)

    def _transfer_weights_layout(self, layout):
        layout.addSpacing(15)
        v_layout = qt.QVBoxLayout()
        button = qt_ui.BasicButton('Transfer on Selected Mesh(es)')

        self._first_influence = qt_ui.GetString('Source Influence')
        self._first_influence.set_use_button(True)
        self._first_influence.set_select_button(True)
        self._second_influence = qt_ui.GetString('Target Influence')
        self._second_influence.set_use_button(True)
        self._second_influence.set_select_button(True)

        v_layout.addWidget(self._first_influence)
        v_layout.addWidget(self._second_influence)
        v_layout.addWidget(button)

        button.clicked.connect(self._joint_to_joint)

        layout.addLayout(v_layout)

    def _skin_mesh_from_mesh(self):
        selection = cmds.ls(sl=True)
        deform.skin_mesh_from_mesh(selection[0], selection[1])

    @core.undo_chunk
    def _smooth_weights(self):

        selection = cmds.ls(sl=True, flatten=True)

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

        selection = cmds.ls(sl=True, flatten=True)

        verts = []

        thing = selection[0]

        if geo.is_a_mesh(thing):
            verts = geo.get_vertices(thing)

        if geo.is_a_vertex(thing):
            verts = selection

        deform.average_skin_weights(verts)

    @core.undo_chunk
    def _sharpen_weights(self):

        selection = cmds.ls(sl=True, flatten=True)

        verts = []

        thing = selection[0]

        if geo.is_a_mesh(thing):
            verts = geo.get_vertices(thing)

        if geo.is_a_vertex(thing):
            verts = selection

        get_count = self.count_sharpen_weights.get_value()
        percent = self.percent_sharpen_weights.get_value()

        deform.sharpen_skin_weights(verts, get_count, percent)

    @core.undo_chunk
    def _remove_weights(self):

        selection = cmds.ls(sl=True, flatten=True)

        verts = []

        if not selection:
            core.print_warning('No meshes selected. Please one mesh, or vertices from one mesh.')
            return

        thing = selection[0]

        if geo.is_a_mesh(thing):
            verts = geo.get_vertices(thing)

        if geo.is_a_vertex(thing):
            verts = selection

        influence_entries = self._remove_influence_string.get_text_as_list()

        found = []

        for influence_entry in influence_entries:
            entry = cmds.ls(influence_entry, l=True)
            found += entry

        if not verts:
            core.print_warning('No meshes selected. Please one mesh, or vertices from one mesh.')
            return

        deform.remove_skin_weights(verts, found)

    @core.undo_chunk
    def _joint_to_joint(self):

        selection = cmds.ls(sl=True, flatten=True)

        if not selection:
            core.print_warning('No meshes selected. Please select at least one mesh with skin weights.')
            return

        first_influence = self._first_influence.get_text_as_list()

        first_influence = cmds.ls(first_influence, l=True)
        second_influence = self._second_influence.get_text_as_list()
        second_influence = cmds.ls(second_influence, l=True)

        if not first_influence or not second_influence:
            core.print_warning('Please provide influences in the text boxes.')

        meshes = geo.get_meshes_in_list(selection)

        if not meshes:
            core.print_warning('No meshes selected. Please select at least one mesh with skin weights.')

        for mesh in meshes:
            deform.transfer_joint_weight_to_joint(first_influence[0], second_influence[0], mesh)


def set_color_selected(color):
    scope = cmds.ls(sl=True, type='transform')

    rgb = color.getRgbF()
    attr.set_color_rgb(scope, *rgb[:-1])
    cmds.select(cl=True)
