# Copyright (C) 2025 Louis Vottero louis.vot@gmail.com    All rights reserved.

from . import rigs

from . import util as ramen_util

from vtool import util
from vtool import util_file
from vtool import util_math

from ..maya_lib import curve
from vtool.maya_lib.space import create_xform_group

in_maya = util.in_maya

if in_maya:
    import maya.cmds as cmds

    from ..maya_lib import attr
    from ..maya_lib import space
    from ..maya_lib import core
    from ..maya_lib import anim
    from ..maya_lib import expressions
    from ..maya_lib import geo
    from ..maya_lib import deform
    from ..maya_lib import rigs_util

curve_data = curve.CurveDataInfo()
curve_data.set_active_library('default_curves')


class Control(object):

    def __init__(self, name, shape='circle'):

        self._color = None
        self._use_joint = False

        self.name = ''
        self.shape = ''
        self.tag = True
        # self.shapes = []

        self._shape = shape

        self.name = name

        self.uuid = None

        if cmds.objExists(self.name):
            if cmds.objExists('%s.curveType' % self.name):
                curve_type = cmds.getAttr('%s.curveType' % self.name)
                self._shape = curve_type

            self.uuid = cmds.ls(self.name, uuid=True)[0]

        else:
            self._create()

    def __repr__(self):
        return self.name

    # def __str__(self):
    #    return self.name

    def _get_components(self):

        transform = core.get_uuid(self.uuid)

        if cmds.nodeType('%sShape' % transform) == 'locator':
            return

        components = '%s.cv[*]' % transform
        return components

    def _create(self):
        self.name = cmds.group(em=True, n=self.name)

        self.uuid = cmds.ls(self.name, uuid=True)[0]

        if self._shape:
            self._create_curve()
        if self.tag:
            try:
                cmds.controller(self.name)
            except:
                pass

        cmds.setAttr('%s.visibility' % self.name, k=False, l=True)

    def _create_curve(self):
        shapes = core.get_shapes(self.name)
        color = None
        if shapes:
            color = attr.get_color_rgb(shapes[0], as_float=True)

        names = curve_data.get_curve_names()
        if not self._shape in names:
            self._shape = 'circle'
        curve_data.set_shape_to_curve(self.name, self._shape)

        if color:
            self.shapes = core.get_shapes(self.name)
            attr.set_color_rgb(self.shapes, *color)

        self.scale_shape(2, 2, 2)

    @classmethod
    def get_shapes(cls):

        return curve_data.get_curve_names()

    @property
    def shape(self):
        return self._shape

    @shape.setter
    def shape(self, str_shape):
        if not str_shape:
            return
        if str_shape == self._shape:
            return

        self._shape = str_shape
        self._create_curve()

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, rgb):

        if not rgb:
            return

        self._color = rgb

        self.shapes = core.get_shapes(self.name)

        rgb = rgb[0]
        attr.set_color_rgb(self.shapes, rgb[0], rgb[1], rgb[2])

    @property
    def use_joint(self):
        return self._use_joint

    @use_joint.setter
    def use_joint(self, bool_value):
        self._use_joint = bool_value

        cmds.select(cl=True)
        joint = cmds.joint()

        match = space.MatchSpace(self.name, joint)
        match.translation_rotation()
        match.scale()

        shapes = core.get_shapes(self.name)

        for shape in shapes:
            cmds.parent(shape, joint, s=True, r=True)

        cmds.delete(self.name)
        self.name = cmds.rename(joint, self.name)

        self.shapes = core.get_shapes(self.name)

    def translate_shape(self, x, y, z):
        """
        Translate the shape curve cvs in object space
        
        Args:
            x (float)
            y (float)
            z (float)
        """
        components = self._get_components()

        if components:
            cmds.move(x, y, z, components, relative=True)

    def rotate_shape(self, x, y, z):
        """
        Rotate the shape curve cvs in object space
        
        Args:
            x (float)
            y (float)
            z (float)
        """
        components = self._get_components()
        if components:
            cmds.rotate(x, y, z, components, relative=True)

    def scale_shape(self, x, y, z):
        """
        Scale the shape curve cvs in object space
        
        Args:
            x (float)
            y (float)
            z (float)
        """

        components = self._get_components()

        if components:
            cmds.scale(x, y, z, components, relative=True)


class MayaUtilRig(rigs.PlatformUtilRig):

    def __init__(self):
        super(MayaUtilRig, self).__init__()

        self.set = None
        self._controls = []
        self._sub_control_count = 0
        self._subs = {}
        self._blend_matrix_nodes = []
        self._mult_matrix_nodes = []
        self._nodes = []

    def _parent_controls(self, parent):

        controls = self.rig.attr.get('controls')

        if not controls:
            return

        to_parent = [controls[0]]
        to_parent = cmds.ls(to_parent)
        if not to_parent:
            return

        if self.rig.attr.exists('hierarchy'):
            hierarchy = self.rig.attr.get('hierarchy')

            if not hierarchy:
                to_parent = controls

        if parent:
            parent = util.convert_to_sequence(parent)
            parent = parent[-1]
            try:
                cmds.parent(to_parent, parent)
            except:
                util.warning('Could not parent %s under %s' % (to_parent, parent))

        else:
            parent = cmds.listRelatives(to_parent, p=True)
            if parent:
                cmds.parent(to_parent, w=True)

        controls = self._get_set_controls()

        for control in controls:
            if not control:
                continue
            if cmds.objExists(control):
                space.zero_out(control)

    def _create_rig_set(self):

        if self.set:
            return
        self.set = cmds.createNode('objectSet', n='rig_%s' % self.rig._get_name())
        attr.create_vetala_type(self.set, 'Rig2')
        cmds.addAttr(ln='rigType', dt='string')
        cmds.addAttr(ln='ramen_uuid', dt='string')
        cmds.setAttr('%s.rigType' % self.set, str(self.rig.__class__.__name__), type='string', l=True)

        cmds.addAttr(self.set, ln='parent', at='message')
        attr.create_multi_message(self.set, 'child')
        attr.create_multi_message(self.set, 'joint')
        attr.create_multi_message(self.set, 'control')

        cmds.setAttr('%s.ramen_uuid' % self.set, self.rig.uuid, type='string')

    def _add_to_set(self, nodes):

        if not self.set:
            return
        cmds.sets(nodes, add=self.set)

        # if not self._set or not cmds.objExists(self._set):
        #    self._create_rig_set()

    def _attach(self):
        if self._blend_matrix_nodes:
            space.blend_matrix_switch(self._blend_matrix_nodes, 'switch', attribute_node=self.rig.joints[0])

    def _tag_parenting(self):

        for control in self._controls:
            parent = cmds.listRelatives(control, p=True)
            if not parent:
                attr.add_message(control, 'parent')
            else:
                attr.connect_message(parent[0], control, 'parent')

    def _get_set_controls(self):

        controls = attr.get_multi_message(self.set, 'control')

        self._controls = controls
        self.rig.attr.set('controls', controls)

        return controls

    def _create_control(self, description='', sub=False):
        control_name = self.get_control_name(description)
        control_name = control_name.replace('__', '_')

        control_name = core.inc_name(control_name, inc_last_number=not sub)

        shape = self.rig.shape[0]
        if shape == 'Default':
            shape = 'circle'

        control = Control(control_name, shape)

        self._controls.append(control)

        if sub:
            control.color = self.rig.sub_color
        else:
            control.color = self.rig.color

        return control

    def _create_control_sub(self, control_name):

        control_name = control_name.replace('CNT_', 'CNT_SUB_1_')
        control_name = control_name.replace('__', '_')

        control_name = core.inc_name(control_name, inc_last_number=False)

        shape = self.rig.shape[0]
        if shape == 'Default':
            shape = 'circle'

        control = Control(control_name, shape)

        control.color = self.rig.sub_color

        return control

    def _track_sub(self, control, sub_control):
        control = str(control)
        sub_control = str(sub_control)
        if not cmds.objExists('%s.sub' % control):
            attr.create_multi_message(control, 'sub')
        attr.append_multi_message(control, 'sub', sub_control)

    def _place_control_shape(self, control_inst):

        self._translate_shape = self.rig.attr.get('shape_translate')
        self._rotate_shape = self.rig.attr.get('shape_rotate')
        self._scale_shape = self.rig.attr.get('shape_scale')

        if self._rotate_shape:
            control_inst.rotate_shape(self._rotate_shape[0][0], self._rotate_shape[0][1], self._rotate_shape[0][2])
        if self._scale_shape:
            control_inst.scale_shape(self._scale_shape[0][0], self._scale_shape[0][1], self._scale_shape[0][2])
        if self._translate_shape:
            control_inst.translate_shape(self._translate_shape[0][0], self._translate_shape[0][1], self._translate_shape[0][2])

    def _place_control_shapes(self, controls=[]):

        if not controls:
            controls = self._controls

        for control in self._controls:
            control_value_type = type(control)
            if control_value_type == str or control_value_type == type(u''):
                control = Control(core.get_basename(control))
            self._place_control_shape(control)

    def _style_controls(self):
        return

    def _reset_offset_matrix(self, joint):
        attr.unlock_attributes(joint, ['offsetParentMatrix'])
        attr.disconnect_attribute('%s.offsetParentMatrix' % joint)
        identity_matrix = [1, 0, 0, 0,
                           0, 1, 0, 0,
                           0, 0, 1, 0,
                           0, 0, 0, 1]
        cmds.setAttr('%s.offsetParentMatrix' % joint, *identity_matrix, type="matrix")

    def _get_unbuild_joints(self):
        return attr.get_multi_message(self.set, 'joint')

    def _build_rig(self, joints):
        return

    def _post_build(self):
        super(MayaUtilRig, self)._post_build()

        found = []
        found += self._controls
        found += self._nodes
        found += self._blend_matrix_nodes
        found += self._mult_matrix_nodes

        self._add_to_set(found)

        cmds.refresh()

    def _unbuild_ik(self):

        outs = self.rig.get_outs()
        if 'ik' in outs:

            ik = self.rig.attr.get('ik')
            found = []
            if ik:
                for thing in ik:
                    if cmds.objExists('%s.origMatrix' % thing):
                        matrix = cmds.getAttr('%s.origMatrix' % thing)
                        orig_position = (matrix[12], matrix[13], matrix[14])
                        const_inst = space.ConstraintEditor()
                        const_inst.delete_constraints(thing, 'pointConstraint')
                        cmds.xform(thing, ws=True, t=orig_position)
                        # this was needed to update the ik bones after deleting the ik
                        core.refresh()
                    if cmds.objExists(thing):
                        found.append(thing)

                if found:
                    cmds.sets(found, remove=self.set)
                    cmds.delete(found)

    def _unbuild_controls(self):
        if not self._controls:
            return

        visited = set()
        for control in self._controls:

            if not control:
                continue

            if not cmds.objExists(control):
                continue

            stored_parent = attr.get_message_input(control, 'parent')

            other_parent = cmds.listRelatives(control, p=True)
            if other_parent:
                if stored_parent == other_parent[0]:
                    attr.zero_xform_channels(control)
        core.refresh()
        for control in self._controls:

            if not cmds.objExists(control):
                continue

            rels = cmds.listRelatives(control, ad=True, type='transform', f=True)

            # searching relatives to find if any should be parented else where.
            if not rels:
                continue
            for rel in rels:
                if rel in visited:
                    continue
                visited.add(rel)
                if not cmds.objExists('%s.parent' % rel):
                    continue
                orig_parent = attr.get_message_input(rel, 'parent')
                if orig_parent:
                    rel_parent = cmds.listRelatives(rel, p=True)
                    if orig_parent != rel_parent[0]:
                        if orig_parent:
                            cmds.parent(rel, orig_parent)
                        else:
                            cmds.parent(rel, w=True)

                else:
                    control_sets = set(cmds.listSets(object=control) or [])
                    rel_sets = set(cmds.listSets(object=rel) or [])

                    if not control_sets & rel_sets or not rel_sets:
                        cmds.parent(rel, w=True)

    def is_valid(self):
        if self.set and cmds.objExists(self.set):
            return True

        return False

    def is_built(self):
        return False
        # Is built needs to be handled more gracefully in Maya.  However for now just gets left False to force building.
        # There's difference between Unreal and Maya, where Unreal just needs to update the function.
        # Maya needs to rebuild a bunch of nodes, etc
        # return self.is_valid()

    @property
    def parent(self):
        return self.rig.attr.get('parent')

    @parent.setter
    def parent(self, parent):
        self.rig.attr.set('parent', parent)
        self._parent_controls(parent)

    @property
    def color(self):
        return self.rig.attr.get('color')

    @color.setter
    def color(self, color):
        self.rig.attr.set('color', color)

        for control in self._controls:
            control_inst = Control(control)
            control_inst.color = color

    @property
    def sub_color(self):
        return self.rig.attr.get('sub_color')

    @sub_color.setter
    def sub_color(self, color):
        self.rig.attr.set('sub_color', color)

        if in_maya:
            for control in self._controls:
                subs = attr.get_multi_message(control, 'sub')
                for sub in subs:
                    control_inst = Control(sub)
                    control_inst.color = color

    @property
    def shape(self):
        shape = self.rig.attr.get('shape')
        return shape

    @shape.setter
    def shape(self, str_shape):

        if not str_shape:
            str_shape = ['circle']

        if str_shape == ['Default']:
            str_shape = ['circle']

        self.rig.attr.set('shape', str_shape)

        # eventually can have this interpolate over the sequence of joints, for now just take the first.
        str_shape = str_shape[0]

        if not self._controls:
            return

        if not self.rig.joints:
            return

        changed = []
        for control in self._controls:
            control_inst = Control(control)
            current_control_shape = control_inst.shape
            if current_control_shape == str_shape:
                continue

            control_inst.shape = str_shape
            changed.append(control_inst)

        self._style_controls()
        self._place_control_shapes(changed)

        # this needs a zip between joints and controls
        # self.rotate_cvs_to_axis(control_inst, joint)

    def load(self):
        super(MayaUtilRig, self).load()

        self.set = None
        sets = cmds.ls(type='objectSet')

        for set_name in sets:
            if not cmds.objExists('%s.ramen_uuid' % set_name):
                continue

            ramen_uuid = cmds.getAttr('%s.ramen_uuid' % set_name)

            if ramen_uuid == self.rig.uuid:
                self.set = set_name
                self._get_set_controls()
                break

        self.rig.state = rigs.RigState.LOADED

    def build(self):
        super(MayaUtilRig, self).build()

        self._create_rig_set()

        joints = self.rig.attr.get('joints')
        if not joints:
            return

        attr.fill_multi_message(self.set, 'joint', joints)

        self._build_rig(joints)

        for control in self._controls:
            space.zero_out(control)

        self._style_controls()
        self._place_control_shapes()

        for control in self._controls:
            attr.append_multi_message(self.set, 'control', control)

        self.rig.attr.set('controls', self._controls)
        self._tag_parenting()
        self._parent_controls(self.parent)

    def unbuild(self):
        super(MayaUtilRig, self).unbuild()

        if self.set and cmds.objExists(self.set):

            self._unbuild_ik()
            self._unbuild_controls()

            attr.clear_multi(self.set, 'joint')
            attr.clear_multi(self.set, 'control')

            result = core.remove_non_existent(self._mult_matrix_nodes)
            if result:
                cmds.sets(result, remove=self.set)
                cmds.delete(result)

            result = core.remove_non_existent(self._blend_matrix_nodes)
            if result:
                cmds.sets(result, remove=self.set)
                cmds.delete(result)

            if cmds.objExists(self.set):
                children = core.get_set_children(self.set)

                found = []
                if children:
                    for child in children:
                        if 'dagNode' not in cmds.nodeType(child, inherited=True):
                            found.append(child)
                if found:
                    cmds.sets(found, remove=self.set)
                    cmds.delete(found)

            if cmds.objExists(self.set):
                core.delete_set_contents(self.set)

            for joint in self._get_unbuild_joints() or []:
                self._reset_offset_matrix(joint)

        self._controls = []
        self._mult_matrix_nodes = []
        self._blend_matrix_nodes = []
        self._nodes = []
        self._subs = {}

    def delete(self):
        super(MayaUtilRig, self).delete()

        if not self.set:
            return

        self.unbuild()
        if self.set:
            cmds.delete(self.set)
        self.set = None

    def get_name(self, prefix=None, description=None):

        side = self.rig.attr.get('side')
        if side:
            side = side[0]

        rig_description = self.rig.attr.get('description')
        if rig_description:
            rig_description = rig_description[0]

        name_list = [prefix, rig_description, description, '1', side]

        filtered_name_list = []

        for name in name_list:
            if name:
                filtered_name_list.append(str(name))

        name = '_'.join(filtered_name_list)

        name = core.inc_name(name)

        return name

    def get_control_name(self, description=None):

        control_name_inst = util_file.ControlNameFromSettingsFile()
        control_name_inst.set_use_side_alias(False)

        restrain_numbering = self.rig.attr.get('restrain_numbering')
        control_name_inst.set_number_in_control_name(not restrain_numbering)

        rig_description = self.rig.attr.get('description')
        if rig_description:
            rig_description = rig_description[0]
        side = self.rig.attr.get('side')
        if side:
            side = side[0]

        if description:
            description = rig_description + '_' + description
        else:
            description = rig_description

        control_name = control_name_inst.get_name(description, side)

        return control_name

    def get_sub_control_name(self, control_name):
        control_name = control_name.replace('CNT_', 'CNT_SUB_1_')

    def create_control(self, description=None, sub=False):

        control = self._create_control(description, sub)

        if not sub:
            self.create_sub_control(str(control), description)

        return control

    def create_sub_control(self, control, description):

        if self._sub_control_count == 0:
            return

        self._subs[control] = []
        last_sub_control = None

        for inc in range(self._sub_control_count):
            weight = float(inc + 1) / self._sub_control_count
            scale = util_math.lerp(1.0, 0.5, weight)

            sub_control_inst = self._create_control_sub(core.get_basename(control))

            sub_control_inst.scale_shape(scale, scale, scale)

            self._place_control_shape(sub_control_inst)

            sub_control = str(sub_control_inst)

            if not last_sub_control:
                sub_parent = control
            else:
                sub_parent = str(last_sub_control)
            cmds.parent(sub_control, sub_parent)

            last_sub_control = sub_control
            self._track_sub(control, sub_control)
            self._subs[control].append(sub_control)

        return sub_control

    def rotate_cvs_to_axis(self, control_inst, joint):
        axis = space.get_axis_letter_aimed_at_child(joint)
        if axis:
            if axis == 'X':
                control_inst.rotate_shape(0, 0, -90)

            if axis == 'Y':
                pass
                # control_inst.rotate_shape(0, 90, 0)

            if axis == 'Z':
                control_inst.rotate_shape(90, 0, 0)

            if axis == '-X':
                control_inst.rotate_shape(0, 0, 90)

            if axis == '-Y':
                pass
                # control_inst.rotate_shape(0, 180, 0)

            if axis == '-Z':
                control_inst.rotate_shape(-90, 0, 0)


class MayaFkRig(MayaUtilRig):

    def _create_maya_controls(self, joints):

        last_joint = None
        joint_control = {}

        parenting = {}

        # rotate_cvs = True

        # if len(joints) == 1:
        #    rotate_cvs = False

        use_joint_name = self.rig.attr.get('use_joint_name')
        hierarchy = self.rig.attr.get('hierarchy')
        self._sub_control_count = self.rig.attr.get('sub_count')[0]

        description = None

        for joint in joints:

            if use_joint_name:
                joint_nice_name = core.get_basename(joint)
                description = self.get_joint_description(joint_nice_name)

            control_inst = self.create_control(description=description)

            control = str(control_inst)

            # if rotate_cvs:
                # self.rotate_cvs_to_axis(control_inst, joint)

            joint_control[joint] = control
            last_control = None
            parent = cmds.listRelatives(joint, p=True, f=True)
            if parent:
                parent = parent[0]
                if parent in joint_control:
                    last_control = joint_control[parent]

            if not last_control and last_joint in joint_control:
                last_control = joint_control[last_joint]
            if last_control:
                if last_control not in parenting:
                    parenting[last_control] = []

                parenting[last_control].append(control)

            cmds.matchTransform(control, joint)

            attach_control = control
            if control in self._subs:
                attach_control = self._subs[control][-1]

            mult_matrix, blend_matrix = space.attach(attach_control, joint)

            self._mult_matrix_nodes.append(mult_matrix)
            self._blend_matrix_nodes.append(blend_matrix)

            last_joint = joint

        if hierarchy:
            for parent in parenting:
                children = parenting[parent]
                if parent in self._subs:
                    parent = self._subs[parent][-1]
                cmds.parent(children, parent)

    def _build_rig(self, joints):
        super(MayaFkRig, self)._build_rig(joints)

        if not joints:
            return

        joints = cmds.ls(joints, l=True)

        # self._parent_controls([])

        self._create_maya_controls(joints)
        self._attach()

        return self._controls


class MayaIkRig(MayaUtilRig):

    def _has_pole_vector(self, joints=None):
        if not joints:
            joints = self.rig.joints

        if len(joints) > 2:
            return True
        return False

    def _get_pole_vector_position(self, joints):

        pole_vector_offset = self.rig.attr.get('pole_vector_offset')[0]

        pole_position = space.get_polevector_at_offset(joints[0], joints[1], joints[2], pole_vector_offset)

        return pole_position

    def _create_pole_line(self, joints):
        joint_count = len(joints)

        if joint_count == 3:
            rig_line = rigs_util.RiggedLine(joints[1], self._controls[1], self.get_name('line')).create()
        else:
            rig_line = rigs_util.RiggedLine(joints[0], self._controls[1], self.get_name('line')).create()
        cmds.parent(rig_line, self._controls[0])

    def _create_maya_controls(self, joints):

        world = self.rig.attr.get('world')
        mirror = self.rig.attr.get('mirror')

        if not joints:
            return

        joint_control = {}

        parenting = {}

        first_control = None

        self._sub_control_count = 0

        create_pole_vector = self._has_pole_vector(joints)

        joint_count = len(joints)

        if joint_count == 1:
            return

        orig_joints = list(joints)

        if joint_count > 3:
            joints = [joints[0], joints[1], joints[-1]]

        for joint in joints:

            if joint == joints[-1]:
                self._sub_control_count = self.rig.attr.get('sub_count')[0]

            description = None
            control_inst = self.create_control(description=description)

            control = str(control_inst)

            joint_control[joint] = control

            if joint != joints[1] or not create_pole_vector:

                cmds.matchTransform(control, joint)

            if world:
                cmds.xform(control, ws=True, rotation=[0, 0, 0])
            if mirror:
                space.mirror_matrix(control, axis=[1, 0, 0], translation=False)

            if first_control:
                parenting[first_control].append(control)

            if joint == joints[0]:
                first_control = control
                parenting[control] = []

        for parent in parenting:
            children = parenting[parent]

            cmds.parent(children, parent)

        if create_pole_vector:
            pole_position = self._get_pole_vector_position(orig_joints)
            cmds.xform(self._controls[1], ws=True, t=pole_position)

    def _create_setup_group(self):
        group = cmds.group(n=self.get_name('setup'), em=True)
        cmds.setAttr('%s.inheritsTransform' % group, 0)
        cmds.hide(group)
        return group

    def _create_ik_chain(self, joints):
        if not joints:
            return

        ik_chain_group = cmds.group(n=self.get_name('chain'), em=True)

        dup_inst = space.DuplicateHierarchy(joints[0])
        dup_inst.only_these(joints)
        dup_inst.stop_at(joints[-1])
        self._ik_joints = dup_inst.create()

        for joint in self._ik_joints:
            cmds.makeIdentity(joint, apply=True, t=True, r=True, s=True)

        cmds.parent(self._ik_joints[0], ik_chain_group)

        self._add_to_set(self._ik_joints)

        return ik_chain_group

    def _create_elbow_lock_stretchy(self, soft=False):

        stretch = self.rig.attr.get('stretch')
        if not stretch:
            return

        if len(self._controls) < 3:
            return
        if len(self._ik_joints) != 3:
            return

        controls = [str(self._controls[0]), str(self._controls[1]), str(self._controls[2])]

        axis = space.get_axis_letter_aimed_at_child(self._ik_joints[0])
        if axis.startswith('-'):
            axis = axis[-1]

        elbow_lock = rigs_util.StretchyElbowLock(self._ik_joints, controls)
        # elbow_lock.set_attribute_control(controls[-1])
        elbow_lock.set_stretch_axis(axis)
        # if self.twist_guide:
            # elbow_lock.set_top_aim_transform(self.twist_guide)

        elbow_lock.set_top_aim_transform(controls[0])
        elbow_lock.set_description(self.get_name('stretch'))
        elbow_lock.set_create_soft_ik(soft)
        # elbow_lock.set_parent(self.setup_group)
        elbow_lock.create()

        # if elbow_lock.soft_locator:
        #    xform = space.get_xform_group(self.ik_handle)
        #    cmds.parent(xform, elbow_lock.soft_locator)
        #    cmds.parent(elbow_lock.soft_locator, self.setup_group)

    def _attach_ik(self):
        loc_ik = cmds.spaceLocator(n=self.get_name('loc', 'ik'))[0]
        cmds.hide(loc_ik + 'Shape')
        space.MatchSpace(self._ik_joints[-1], loc_ik).translation_rotation()

        handle = space.IkHandle(self.get_name('ik'))
        handle.set_start_joint(self._ik_joints[0])
        handle.set_end_joint(self._ik_joints[-1])
        handle.set_solver(handle.solver_rp)
        handle.create()
        cmds.hide(handle.ik_handle)
        ik_handle = handle.ik_handle

        attr.store_world_matrix_to_attribute(ik_handle, 'origMatrix')

        subs = attr.get_multi_message(self._controls[-1], 'sub')

        ik_control = self._controls[-1]
        if subs:
            ik_control = subs[-1]

        cmds.parent(ik_handle, ik_control)
        cmds.parent(loc_ik, ik_control)

        cmds.poleVectorConstraint(self._controls[1], ik_handle)
        cmds.orientConstraint(loc_ik, self._ik_joints[-1], mo=True)

        self._ik_transform = [ik_handle, loc_ik]

    def _attach(self, joints):

        self._attach_ik()

        space.attach(self._controls[0], self._ik_joints[0])

        for joint, ik_joint in zip(joints, self._ik_joints):

            mult_matrix, blend_matrix = space.attach(ik_joint, joint)

            self._mult_matrix_nodes.append(mult_matrix)
            self._blend_matrix_nodes.append(blend_matrix)

        if self._blend_matrix_nodes:
            space.blend_matrix_switch(self._blend_matrix_nodes, 'switch', attribute_node=self.rig.joints[0])

    def _build_rig(self, joints):
        print('build rig')
        super(MayaIkRig, self)._build_rig(joints)

        if not joints:
            return

        joints = cmds.ls(joints, l=True)
        # joints = core.get_hierarchy_by_depth(joints)

        self._ik_transform = None

        # self._parent_controls([])

        ik_chain_group = self._create_ik_chain(joints)

        self._create_maya_controls(joints)

        self._create_elbow_lock_stretchy(soft=False)

        self._attach(joints)

        group = self._create_setup_group()

        cmds.parent(ik_chain_group, group)
        cmds.parent(group, self._controls[0])

        self._create_pole_line(joints)

        self.rig.attr.set('ik', self._ik_transform)

        return self._controls

    def _style_controls(self):
        if self._has_pole_vector():
            pole_vector_shape = self.rig.attr.get('pole_vector_shape')[0]
            pole_control = Control(self._controls[1])

            if pole_vector_shape == 'Default':
                pole_vector_shape = 'sphere'

            pole_control.shape = pole_vector_shape
            pole_control.scale_shape(.5, .5, .5)


class MayaSplineIkRig(MayaUtilRig):

    def _setup_ribbon_stretchy(self, joints, control, rivets, stretch_curve, arc_len_node, surface):

        scale_compensate_node, blend_length = self._create_scale_compensate_node(control, arc_len_node)

        motion_paths = []

        for rivet in rivets:
            motion_path = self._motion_path_rivet(rivet, stretch_curve, blend_length, surface)
            motion_paths.append(motion_path)

        last_axis_letter = None

        length_condition = cmds.createNode('condition', n=core.inc_name(self.get_name('length_condition')))
        cmds.setAttr('%s.operation' % length_condition, 4)

        cmds.connectAttr('%s.arcLengthInV' % arc_len_node, '%s.firstTerm' % length_condition)
        cmds.connectAttr('%s.outputX' % scale_compensate_node, '%s.secondTerm' % length_condition)

        for joint, motion in zip(joints[1:], motion_paths[1:]):

            axis_letter = space.get_axis_letter_aimed_at_child(joint)

            if not axis_letter and last_axis_letter:
                axis_letter = last_axis_letter

            if axis_letter.startswith('-'):
                axis_letter = axis_letter[-1]

            last_axis_letter = axis_letter

            condition = cmds.createNode('condition', n=core.inc_name(self.get_name('lock_condition')))
            cmds.setAttr('%s.operation' % condition, 3)

            cmds.connectAttr('%s.uValue' % motion, '%s.firstTerm' % condition)
            param = cmds.getAttr('%s.uValue' % motion)
            max_value = self._get_max_value(param)
            cmds.setAttr('%s.secondTerm' % condition, max_value)

            cmds.connectAttr('%s.stretchOffOn' % control, '%s.colorIfTrueR' % condition)
            cmds.setAttr('%s.colorIfFalseR' % condition, 1)

            self._blend_two_lock('%s.outColorR' % condition, joint, axis_letter)

    def _blend_two_lock(self, condition_attr, transform, axis_letter):

        input_axis_attr = '%s.translate%s' % (transform, axis_letter)

        input_attr = attr.get_attribute_input(input_axis_attr)
        value = cmds.getAttr(input_attr)

        blend_two = cmds.createNode('blendTwoAttr', n=core.inc_name(self.get_name('lock_length')))

        cmds.connectAttr(condition_attr, '%s.attributesBlender' % blend_two)

        cmds.setAttr('%s.input[0]' % blend_two, value)

        cmds.connectAttr(input_attr, '%s.input[1]' % blend_two)

        attr.disconnect_attribute(input_axis_attr)
        cmds.connectAttr('%s.output' % blend_two, input_axis_attr)

        return blend_two

    def _create_scale_compensate_node(self, control, arc_length_node):

        cmds.addAttr(control, ln='stretchOffOn', dv=1, min=0, max=1, k=True)

        div_length = cmds.createNode('multiplyDivide', n=core.inc_name(self.get_name('normalize_length')))
        blend_length = cmds.createNode('blendTwoAttr', n=core.inc_name(self.get_name('blend_length')))

        cmds.setAttr(blend_length + '.input[1]', 1)
        cmds.connectAttr('%s.outputX' % div_length, blend_length + '.input[0]')
        cmds.connectAttr('%s.stretchOffOn' % control, '%s.attributesBlender' % blend_length)

        length = cmds.getAttr('%s.arcLengthInV' % arc_length_node)
        cmds.setAttr('%s.operation' % div_length, 2)

        mult_scale = cmds.createNode('multiplyDivide', n=core.inc_name(self.get_name('multiplyDivide_scaleOffset')))
        cmds.setAttr('%s.input1X' % mult_scale, length)
        cmds.connectAttr('%s.outputX' % mult_scale, '%s.input1X' % div_length)
        # cmds.connectAttr('%s.sizeY' % self.control_group, '%s.input2X' % mult_scale)

        cmds.connectAttr('%s.arcLengthInV' % arc_length_node, '%s.input2X' % div_length)

        return mult_scale, blend_length

    def _get_max_value(self, param):
        max_value = 1.0 - (1.0 - param) * 0.1
        return max_value

    def _motion_path_rivet(self, rivet, ribbon_curve, scale_compensate_node, surface):
        motion_path = cmds.createNode('motionPath', n=core.inc_name(self.get_name('motionPath')))
        cmds.setAttr('%s.fractionMode' % motion_path, 1)

        cmds.connectAttr('%s.worldSpace' % ribbon_curve, '%s.geometryPath' % motion_path)

        position_node = attr.get_attribute_input('%s.translateX' % rivet, node_only=True)

        param = cmds.getAttr('%s.parameterV' % position_node)

        mult_offset = cmds.createNode('multDoubleLinear', n=core.inc_name(self.get_name('multiply_offset')))
        cmds.setAttr('%s.input2' % mult_offset, param)
        cmds.connectAttr('%s.output' % scale_compensate_node, '%s.input1' % mult_offset)

        clamp = cmds.createNode('clamp', n=core.inc_name(self.get_name('clamp_offset')))

        max_value = self._get_max_value(param)
        cmds.setAttr('%s.maxR' % clamp, max_value)
        cmds.connectAttr('%s.output' % mult_offset, '%s.inputR' % clamp)

        cmds.connectAttr('%s.outputR' % clamp, '%s.uValue' % motion_path)
        cmds.connectAttr('%s.outputR' % clamp, '%s.parameterV' % position_node)

        attr.disconnect_attribute('%s.translateX' % rivet)
        attr.disconnect_attribute('%s.translateY' % rivet)
        attr.disconnect_attribute('%s.translateZ' % rivet)

        cmds.connectAttr('%s.xCoordinate' % motion_path, '%s.translateX' % rivet)
        cmds.connectAttr('%s.yCoordinate' % motion_path, '%s.translateY' % rivet)
        cmds.connectAttr('%s.zCoordinate' % motion_path, '%s.translateZ' % rivet)

        closest = cmds.createNode('closestPointOnSurface', n=core.inc_name(self.get_name('closestPoint')))

        cmds.connectAttr('%s.xCoordinate' % motion_path, '%s.inPositionX' % closest)
        cmds.connectAttr('%s.yCoordinate' % motion_path, '%s.inPositionY' % closest)
        cmds.connectAttr('%s.zCoordinate' % motion_path, '%s.inPositionZ' % closest)
        cmds.connectAttr('%s.worldSpace' % surface, '%s.inputSurface' % closest)

        cmds.connectAttr('%s.parameterV' % closest, '%s.parameterV' % position_node, f=True)

        return motion_path

    def _create_clusters(self, surface, description):

        cluster_surface = deform.ClusterSurface(surface, description)
        cluster_surface.set_first_cluster_pivot_at_start(True)
        cluster_surface.set_last_cluster_pivot_at_end(True)
        cluster_surface.set_join_ends(True)
        cluster_surface.create()

        clusters = cluster_surface.handles

        return clusters

    def _create_surface(self, joints, span_count, description=None):

        aim_axis = self.rig.attr.get('aim_axis')[0]
        up_axis = self.rig.attr.get('up_axis')[0]

        tangent_axis = util_math.vector_cross(aim_axis, up_axis, normalize=True)
        letter = util_math.get_vector_axis_letter(tangent_axis)

        if not letter:
            return None, None, None
        if letter.startswith('-'):
            letter = letter[1]

        surface = geo.transforms_to_nurb_surface(joints, self.get_name(description=description),
                                                      spans=span_count - 1,
                                                      offset_amount=1,
                                                      offset_axis=letter)

        cmds.setAttr('%s.inheritsTransform' % surface, 0)

        max_u = cmds.getAttr('%s.minMaxRangeU' % surface)[0][1]
        u_value = max_u / 2.0
        curve, curve_node = cmds.duplicateCurve(surface + '.u[' + str(u_value) + ']', ch=True, rn=0, local=0,
                                                r=True, n=core.inc_name(self.get_name('liveCurve')))
        curve_node = cmds.rename(curve_node, self.get_name('curveFromSurface'))
        ribbon_stretch_curve = curve
        ribbon_stretch_curve_node = curve_node

        cmds.setAttr('%s.inheritsTransform' % curve, 0)

        arclen = cmds.createNode('arcLengthDimension')

        parent = cmds.listRelatives(arclen, p=True)
        arclen = cmds.rename(parent, core.inc_name(self.get_name('arcLengthDimension')))

        ribbon_arc_length_node = arclen

        cmds.setAttr('%s.vParamValue' % arclen, 1)
        cmds.setAttr('%s.uParamValue' % arclen, u_value)
        cmds.connectAttr('%s.worldSpace' % surface, '%s.nurbsGeometry' % arclen)

        return surface, ribbon_stretch_curve, ribbon_arc_length_node

    def _create_ribbon_ik(self, joints, surface, group):

        rivet_group = group

        rivets = []
        ribbon_follows = []

        for joint in joints:

            joint_name = core.get_basename(joint)

            nurb_follow = None

            buffer_group = None

            constrain = True
            transform = joint

            # if buffer group
            buffer_group = cmds.group(em=True, n=core.inc_name('ribbonBuffer_%s' % joint_name))
            xform = space.create_xform_group(buffer_group)

            space.MatchSpace(joint, xform).translation_rotation()

            constrain = False
            transform = xform
            # if buffer group end

            rivet = None

            rivet = geo.attach_to_surface(transform, surface, constrain=constrain)
            nurb_follow = rivet
            cmds.setAttr('%s.inheritsTransform' % rivet, 0)
            cmds.parent(rivet, rivet_group)
            rivets.append(rivet)

            if buffer_group:
                cmds.parentConstraint(buffer_group, joint, mo=True)

            ribbon_follows.append(nurb_follow)

        return rivets, ribbon_follows

    def _aim_joints(self, joints, ribbon_follows):

        last_follow = None
        last_parent = None
        last_joint = None

        for joint, ribbon_follow in zip(joints, ribbon_follows):

            child = cmds.listRelatives(ribbon_follow, type='transform')

            for c in child:
                if not cmds.nodeType(c) == 'aimConstraint':
                    child = c

            space.create_xform_group(child)

            if last_follow:
                axis = space.get_axis_aimed_at_child(last_joint)

                ribbon_rotate_up = cmds.duplicate(ribbon_follow,
                                                  po=True,
                                                  n=core.inc_name(self.get_name('rotationUp'))
                                                  )[0]
                cmds.setAttr('%s.inheritsTransform' % ribbon_rotate_up, 1)
                cmds.parent(ribbon_rotate_up, last_parent)
                space.MatchSpace(last_follow, ribbon_rotate_up).translation_rotation()

                cmds.aimConstraint(child,
                                   last_follow,
                                   aimVector=axis,

                                   upVector=[0, 1, 0],
                                   wut='objectrotation',
                                   wuo=ribbon_rotate_up,
                                   mo=True,
                                   wu=[0, 1, 0])[0]

            last_joint = joint
            last_follow = child
            last_parent = ribbon_follow

    def _attach(self, joints):

        span_count = self.rig.attr.get('control_count')[0]

        group = cmds.group(n=self.get_name('setup'), em=True)
        cmds.setAttr('%s.inheritsTransform' % group, 0)
        cmds.hide(group)

        surface, ribbon_stretch_curve, ribbon_arc_length_node = self._create_surface(joints, span_count, None)

        if not surface:
            return

        cmds.parent(surface, ribbon_stretch_curve, ribbon_arc_length_node, group)

        clusters = self._create_clusters(surface, None)

        for control, cluster in zip(self._controls, clusters):
            sub = attr.get_multi_message(control, 'sub')
            if sub:
                control = sub[-1]
            cmds.parent(cluster, control)
            cmds.hide(cluster)

        rivets, ribbon_follows = self._create_ribbon_ik(joints, surface, group)

        self._setup_ribbon_stretchy(joints, self._controls[0], rivets, ribbon_stretch_curve, ribbon_arc_length_node, surface)

        self._aim_joints(joints, ribbon_follows)

        cmds.parent(group, self._controls[0])
        # if self._blend_matrix_nodes:
        #    space.blend_matrix_switch(self._blend_matrix_nodes, 'switch', attribute_node=self.rig.joints[0])

    def _create_maya_controls(self, joints):

        last_control = None

        parenting = {}

        rotate_cvs = True

        if len(joints) == 1:
            rotate_cvs = False

        # use_joint_name = self.rig.attr.get('use_joint_name')
        hierarchy = self.rig.attr.get('hierarchy')
        self._sub_control_count = self.rig.attr.get('sub_count')[0]
        self._subs = {}

        description = None

        control_count = self.rig.attr.get('control_count')[0]

        temp_curve = geo.transforms_to_curve(joints, len(joints), description)

        section = 1.0 / (control_count - 1)
        offset = 0

        for inc in range(0, control_count):

            position = cmds.pointOnCurve(temp_curve, pr=offset, p=True)
            offset += section

            control_inst = self.create_control(description=description)
            control = str(control_inst)
            cmds.xform(control, ws=True, t=position)

            if last_control:
                if last_control not in parenting:
                    parenting[last_control] = []

                parenting[last_control].append(control)

            last_control = control

        cmds.delete(temp_curve)

        if hierarchy:
            for parent in parenting:
                children = parenting[parent]
                cmds.parent(children, parent)

    def _build_rig(self, joints):
        super(MayaSplineIkRig, self)._build_rig(joints)

        if not joints:
            return

        joints = cmds.ls(joints, l=True)
        # joints = core.get_hierarchy_by_depth(joints)

        # self._parent_controls([])

        self._create_maya_controls(joints)
        self._attach(joints)

        return self._controls


class MayaFootRollRig(MayaUtilRig):

    def __init__(self):
        super(MayaFootRollRig, self).__init__()
        self.offset_control = None
        self.ik_loc = None

    @property
    def ik(self):
        ik = self.rig.attr.get('ik')
        return ik

    @ik.setter
    def ik(self, ik_transform):

        self.rig.attr.set('ik', ik_transform)

        if not self._controls:
            return

        self._parent_ik()

    def _create_maya_controls(self):
        joints = cmds.ls(self.rig.joints, l=True)
        joints = core.get_hierarchy_by_depth(joints)

        if not joints:
            return

        joint_control = {}

        parenting = {}

        first_control = None
        last_control = None

        self._sub_control_count = 0

        for joint in joints:

            if joint == joints[0]:
                control = cmds.spaceLocator(n=self.get_name('loc', 'ankle'))[0]
                self._add_to_set(control)
                cmds.hide(control + 'Shape')
                self._controls.append(control)

            elif joint == joints[1]:
                control_inst = self.create_control(description='ball')

                control = str(control_inst)

                if not self.attribute_control:
                    self.attribute_control = control

                control_inst2 = self.create_control(description='ankle')
                control_inst2.shape = 'square'

                loc_ik = cmds.spaceLocator(n=self.get_name('loc', 'ik'))[0]
                cmds.hide(loc_ik + 'Shape')
                self.ik_loc = loc_ik

                cmds.matchTransform(str(control_inst2), joint)
                cmds.parent(loc_ik, str(control_inst2))
                cmds.matchTransform(loc_ik, joints[0])
                self.offset_control = control_inst2

            elif joint == joints[-1]:
                control = cmds.spaceLocator(n=self.get_name('loc', 'toe'))[0]
                cmds.hide(control + 'Shape')
                self._controls.append(control)

            joint_control[joint] = control

            cmds.matchTransform(control, joint)

            if joint == joints[1]:
                parenting[first_control] = [str(self.offset_control), control, ]

            if joint == joints[2]:
                parenting[last_control] = [control]

            if joint == joints[0]:
                first_control = control

            last_control = control

        for parent in parenting:
            children = parenting[parent]
            cmds.parent(children, parent)

        attr.create_title(self.attribute_control, 'FOOT_ROLL')
        xform_dict, control_dict = self._create_rolls(joints)
        self._connect_rolls(xform_dict, control_dict)

    def _create_rolls(self, joints):

        toe_pivot = cmds.xform(joints[-1], q=True, ws=True, t=True)
        heel_pivot = self.rig.attr.get('heel_pivot')[0]
        yaw_in_pivot = self.rig.attr.get('yaw_in_pivot')[0]
        yaw_out_pivot = self.rig.attr.get('yaw_out_pivot')[0]

        yaw_in_control = self.create_control('yaw_in', sub=True)
        yaw_out_control = self.create_control('yaw_out', sub=True)
        heel_control = self.create_control('heel', sub=True)
        toe_control = self.create_control('toe', sub=True)

        space.MatchSpace(joints[1], str(yaw_in_control)).rotation()
        space.MatchSpace(joints[1], str(yaw_out_control)).rotation()
        space.MatchSpace(joints[1], str(heel_control)).rotation()

        control_dict = {}
        control_dict['toe'] = toe_control
        control_dict['heel'] = heel_control
        control_dict['ball_toe'] = self._controls[1]
        control_dict['ball'] = self._controls[2]
        control_dict['yaw_out'] = yaw_out_control
        control_dict['yaw_in'] = yaw_in_control

        pivots = [toe_pivot, heel_pivot, yaw_in_pivot, yaw_out_pivot]
        controls = [toe_control, heel_control, yaw_in_control, yaw_out_control]

        xforms = {}

        for pivot, control in zip(pivots, controls):
            control_name = str(control)
            cmds.xform(control, ws=True, t=pivot)
            xforms[control] = space.create_xform_group_zeroed(control_name, 'driver')

        heel_pivot_xform = cmds.group(em=True, n=self.get_name('pivot', 'heel'))
        ball_pivot_xform = cmds.group(em=True, n=self.get_name('pivot', 'ball'))
        toe_pivot_xform = cmds.group(em=True, n=self.get_name('pivot', 'toe'))

        space.MatchSpace(joints[1], heel_pivot_xform).rotation()
        space.MatchSpace(joints[1], ball_pivot_xform).rotation()
        space.MatchSpace(joints[1], toe_pivot_xform).rotation()

        ball_pivot = cmds.xform(control_dict['ball'], q=True, ws=True, t=True)

        pivots = [heel_pivot, toe_pivot, ball_pivot]
        pivot_xforms = [heel_pivot_xform, toe_pivot_xform, ball_pivot_xform]

        for pivot, xform in zip(pivots, pivot_xforms):
            cmds.xform(xform, ws=True, t=pivot)

        cmds.parent(toe_pivot_xform, heel_pivot_xform)
        cmds.parent(ball_pivot_xform, toe_pivot_xform)
        cmds.parent(heel_pivot_xform, toe_control)

        cmds.parent(xforms[toe_control], heel_control)
        cmds.parent(xforms[heel_control], yaw_out_control)
        cmds.parent(xforms[yaw_out_control], yaw_in_control)
        cmds.parent(xforms[yaw_in_control], self._controls[0])

        xforms['heel_pivot'] = heel_pivot_xform
        xforms['ball_pivot'] = ball_pivot_xform
        xforms['toe_pivot'] = toe_pivot_xform

        for xform in xforms.values():
            space.zero_out(xform)

        cmds.parent(self.offset_control, ball_pivot_xform)
        cmds.parent(self._controls[1], ball_pivot_xform)

        xform_ball = space.create_xform_group_zeroed(str(control_dict['ball']), 'driver')
        xform_ball_2 = create_xform_group(str(control_dict['ball']), 'driver2')
        xform_ball_3 = create_xform_group(str(control_dict['ball']), 'driver3')

        xform_heel_2 = create_xform_group(str(control_dict['heel']), 'driver2')
        xform_toe_2 = create_xform_group(str(control_dict['toe']), 'driver2')

        xforms[control_dict['ball']] = xform_ball
        xforms['ball_offset'] = xform_ball_2
        xforms['ball_offset_2'] = xform_ball_3
        xforms['toe_offset'] = xform_toe_2
        xforms['heel_offset'] = xform_heel_2

        return xforms, control_dict

    def _connect_rolls(self, xform_dict, control_dict):

        mirror = self.rig.attr.get('mirror')

        forward_axis = self.rig.attr.get('forward_axis')[0]
        neg_forward_axis = util_math.vector_multiply(forward_axis, -1)

        up_axis = self.rig.attr.get('up_axis')[0]

        roll_axis = util_math.vector_cross(forward_axis, up_axis)

        neg_roll_axis = util_math.vector_multiply(roll_axis, -1)

        if mirror:
            temp = roll_axis
            roll_axis = neg_roll_axis
            neg_roll_axis = temp

            temp = forward_axis
            forward_axis = neg_forward_axis
            neg_forward_axis = temp

            up_axis = util_math.vector_multiply(up_axis, -1)

        self._connect_foot_roll(xform_dict, neg_roll_axis)

        xform_ball_2 = xform_dict['ball_offset']
        self._connect_roll(xform_ball_2, neg_forward_axis, 'ankle')

        rolls = ['heel', 'ball', 'toe']
        axis = [roll_axis, neg_roll_axis, neg_roll_axis]

        for current_axis, roll in zip(axis, rolls):

            control_inst = control_dict[roll]
            xform = xform_dict[control_inst]

            self._connect_roll(xform, current_axis, roll)

        self._connect_yaw(xform_dict, control_dict, neg_forward_axis, mirror)

        self._connect_pivot_rolls(xform_dict, control_dict, up_axis)

    def _connect_foot_roll(self, xform_dict, axis):

        ball_driver = xform_dict['ball_offset_2']
        heel_driver = xform_dict['heel_offset']
        toe_driver = xform_dict['toe_offset']
        title = 'roll'
        title2 = 'roll_offset'

        attribute = '%s.%s' % (self.attribute_control, title)
        attribute_offset = '%s.%s' % (self.attribute_control, title2)

        if not cmds.objExists(attribute):
            cmds.addAttr(self.attribute_control, ln=title, k=True)
        if not cmds.objExists(attribute_offset):
            cmds.addAttr(self.attribute_control, ln=title2, k=True, dv=30)

        mult_ball = self._connect_roll(ball_driver, axis, title, connect=False)
        mult_heel = self._connect_roll(heel_driver, axis, title, connect=False)
        mult_toe = self._connect_roll(toe_driver, axis, title, connect=False)

        key_ball = anim.quick_driven_key(attribute, '%s.input1X' % mult_ball, [0, 5, 10], [0, 1, 0], tangent_type=['spline', 'linear', 'spline'])
        cmds.connectAttr('%s.output' % key_ball, '%s.input1Y' % mult_ball)
        cmds.connectAttr('%s.output' % key_ball, '%s.input1Z' % mult_ball)

        mult_offset = attr.connect_multiply(attribute_offset, '%s.input2X' % mult_ball, axis[0])
        cmds.connectAttr(attribute_offset, '%s.input1Y' % mult_offset)
        cmds.connectAttr(attribute_offset, '%s.input1Z' % mult_offset)
        cmds.setAttr('%s.input2Y' % mult_offset, axis[1])
        cmds.setAttr('%s.input2Z' % mult_offset, axis[2])

        key_toe = anim.quick_driven_key(attribute, '%s.input1X' % mult_toe, [0, 5, 10], [0, 0, 45], tangent_type=['spline', 'linear', 'spline'])
        cmds.setInfinity('%s.input1X' % mult_toe, postInfinite='linear')
        cmds.connectAttr('%s.output' % key_toe, '%s.input1Y' % mult_toe)
        cmds.connectAttr('%s.output' % key_toe, '%s.input1Z' % mult_toe)

        key_heel = anim.quick_driven_key(attribute, '%s.input1X' % mult_heel, [0, -10], [0, -45], tangent_type='spline')
        cmds.setInfinity('%s.input1X' % mult_heel, preInfinite='linear')
        cmds.connectAttr('%s.output' % key_heel, '%s.input1Y' % mult_heel)
        cmds.connectAttr('%s.output' % key_heel, '%s.input1Z' % mult_heel)

    def _connect_pivot_rolls(self, xform_dict, control_dict, axis):

        rolls = ['heel', 'toe', 'ball']

        for roll in rolls:
            title = roll + '_pivot'
            xform = xform_dict[title]

            pass_axis = list(axis)

            if roll == 'toe':
                util_math.vector_multiply(pass_axis, -1)

            self._connect_roll(xform, pass_axis, title)

    def _connect_yaw(self, xform_dict, control_dict, axis, mirror):
        yaw_in_value = [0, -90]
        yaw_out_value = [0, 90]
        if mirror:
            temp = yaw_in_value
            yaw_in_value = yaw_out_value
            yaw_out_value = temp

        mult_yaw_in = self._connect_roll(xform_dict[control_dict['yaw_in']], axis, 'yaw', connect=False)
        mult_yaw_out = self._connect_roll(xform_dict[control_dict['yaw_out']], axis, 'yaw', connect=False)

        key_in = anim.quick_driven_key('%s.yaw' % self.attribute_control,
                                       '%s.input1X' % mult_yaw_in,
                                       yaw_in_value, yaw_in_value)
        cmds.connectAttr('%s.output' % key_in, '%s.input1Y' % mult_yaw_in)
        cmds.connectAttr('%s.output' % key_in, '%s.input1Z' % mult_yaw_in)

        key_out = anim.quick_driven_key('%s.yaw' % self.attribute_control,
                                      '%s.input1X' % mult_yaw_out,
                                      yaw_out_value, yaw_out_value)
        cmds.connectAttr('%s.output' % key_out, '%s.input1Y' % mult_yaw_out)
        cmds.connectAttr('%s.output' % key_out, '%s.input1Z' % mult_yaw_out)

    def _connect_roll(self, xform, roll_axis, title, connect=True):

        attribute = '%s.%s' % (self.attribute_control, title)

        if not cmds.objExists(attribute):
            cmds.addAttr(self.attribute_control, ln=title, k=True)

        mult = attr.connect_multiply(attribute, '%s.rotateX' % xform, roll_axis[0])

        if connect:
            cmds.connectAttr(attribute, '%s.input1Y' % mult)
            cmds.connectAttr(attribute, '%s.input1Z' % mult)
        else:
            attr.disconnect_attribute('%s.input1X' % mult)

        cmds.setAttr('%s.input2Y' % mult, roll_axis[1])
        cmds.setAttr('%s.input2Z' % mult, roll_axis[2])

        cmds.connectAttr('%s.outputY' % mult, '%s.rotateY' % xform)
        cmds.connectAttr('%s.outputZ' % mult, '%s.rotateZ' % xform)

        return mult

    def _create_ik_chain(self, joints):
        if not joints:
            return

        ik_chain_group = cmds.group(n=self.get_name('setup'), em=True)

        dup_inst = space.DuplicateHierarchy(joints[0])
        dup_inst.only_these(joints)
        dup_inst.stop_at(joints[-1])
        self._ik_joints = dup_inst.create()

        # cmds.pointConstraint(joints[0], self._ik_joints[0], mo=True)

        for joint in self._ik_joints:
            cmds.makeIdentity(joint, apply=True, r=True)

        cmds.parent(self._ik_joints[0], ik_chain_group)

        self._add_to_set(self._ik_joints)

        return ik_chain_group

    def _attach(self, joints):

        group = cmds.group(n=self.get_name('setup'), em=True)
        cmds.setAttr('%s.inheritsTransform' % group, 0)
        cmds.hide(group)

        handle = space.IkHandle(self.get_name('ik'))
        handle.set_start_joint(self._ik_joints[0])
        handle.set_end_joint(self._ik_joints[1])
        handle.set_solver(handle.solver_sc)
        handle.create()
        cmds.hide(handle.ik_handle)
        ik_handle = handle.ik_handle

        handle2 = space.IkHandle(self.get_name('ik'))
        handle2.set_start_joint(self._ik_joints[1])
        handle2.set_end_joint(self._ik_joints[2])
        handle2.set_solver(handle2.solver_sc)
        handle2.create()
        cmds.hide(handle2.ik_handle)
        ik_handle2 = handle2.ik_handle

        subs = attr.get_multi_message(self._controls[-1], 'sub')

        ik_control = self._controls[1]
        if subs:
            ik_control = subs[1]

        attr.store_world_matrix_to_attribute(ik_handle, 'origMatrix')
        attr.store_world_matrix_to_attribute(ik_handle2, 'origMatrix')

        cmds.parent(ik_handle, ik_control)
        cmds.parent(ik_handle2, self._controls[3])

        # cmds.poleVectorConstraint(self._controls[1], ik_handle)
        if not subs:
            cmds.orientConstraint(self._controls[-1], self._ik_joints[-1], mo=True)
        else:
            cmds.orientConstraint(subs, self._ik_joints[-1], mo=True)

        # space.attach(self._controls[0], self._ik_joints[0])

        for joint, ik_joint in zip(joints, self._ik_joints):
            if joint == joints[0]:
                continue
            mult_matrix, blend_matrix = space.attach(ik_joint, joint)

            self._mult_matrix_nodes.append(mult_matrix)
            self._blend_matrix_nodes.append(blend_matrix)

        if self._blend_matrix_nodes:
            space.blend_matrix_switch(self._blend_matrix_nodes, 'switch', attribute_node=self.rig.joints[0])

        return group

    def _get_unbuild_joints(self):
        joints = attr.get_multi_message(self.set, 'joint')
        if joints:
            return joints[1:]

    def _parent_ik(self):
        ik = self.rig.attr.get('ik')
        if ik:
            if cmds.objExists(ik[0]):
                effector = attr.get_attribute_input('%s.endEffector' % ik[0], node_only=True)
                if effector:
                    effector_transform = attr.get_attribute_input('%s.translateX' % effector, node_only=True)

                    cmds.pointConstraint(effector_transform, self._ik_joints[0], mo=True)

                cmds.pointConstraint(self.ik_loc, ik[0], mo=True)
            if cmds.objExists(ik[1]):
                cmds.orientConstraint(self._ik_joints[0], ik[1], mo=True)

    def _build_rig(self, joints):
        super(MayaFootRollRig, self)._build_rig(joints)

        if not joints:
            return

        for joint in joints:
            if not cmds.objExists(joint):
                return

        joints = cmds.ls(joints, l=True)
        # joints = core.get_hierarchy_by_depth(joints)

        attribute_control = self.rig.attr.get('attribute_control')

        if attribute_control:
            attribute_control = attribute_control[-1]

        if not attribute_control:
            parent = self.rig.attr.get('parent')
            if parent:
                attribute_control = parent[-1]
                sub_test = attr.get_attribute_outputs('%s.message' % attribute_control, node_only=False)
                if sub_test:
                    for thing in sub_test:
                        if thing.find('.sub[') > -1:
                            attribute_control = core.get_basename(thing, remove_namespace=True, remove_attribute=True)
                            break

        self.attribute_control = attribute_control

        self._parent_controls([])

        ik_chain_group = self._create_ik_chain(joints)

        self._create_maya_controls()

        group = self._attach(joints)
        cmds.parent(ik_chain_group, group)

        cmds.parent(group, self._controls[0])

        self._parent_ik()

        return self._controls

    def _style_controls(self):

        ankle_roll = Control(self._controls[2])
        ankle_roll.shape = 'square'
        ankle_roll.scale_shape(1.2, 1.2, 1.2)

        for control in self._controls[2:]:
            control_inst = Control(control)
            control_inst.scale_shape(.3, .3, .3)


class MayaIkQuadrupedRig(MayaIkRig):

    def _create_maya_controls(self, joints):

        super(MayaIkQuadrupedRig, self)._create_maya_controls(joints)

        if not joints:
            return

        world = self.rig.attr.get('world')
        mirror = self.rig.attr.get('mirror')

        control_inst = self.create_control(description='ankle')
        control = str(control_inst)

        temp = self._controls[-2]
        self._controls[-2] = self._controls[-1]
        self._controls[-1] = temp

        cmds.matchTransform(control, joints[-1])

        if world:
            cmds.xform(control, ws=True, rotation=[0, 0, 0])
        if mirror:
            space.mirror_matrix(control, axis=[1, 0, 0], translation=False)

        self.control_ankle = control
        cmds.parent(control, self._controls[-1])

        space.create_xform_group_zeroed(control, 'driver')
        attr.hide_scale(control)
        attr.hide_translate(control)

    def _get_pole_vector_position(self, joints):

        pole_vector_offset = self.rig.attr.get('pole_vector_offset')[0]

        pole_position = space.get_polevector_4_joint_at_offset(joints[0], joints[1], joints[2], joints[3], pole_vector_offset)

        return pole_position

    def _create_ik_chain(self, joints):
        if not joints:
            return

        ik_chain_group = cmds.group(n=self.get_name('chain'), em=True)

        dup_inst = space.DuplicateHierarchy(joints[0])
        dup_inst.only_these(joints)
        dup_inst.stop_at(joints[-1])
        dup_inst.add_prefix('guide_')
        self._ik_joints = dup_inst.create()

        dup_inst = space.DuplicateHierarchy(joints[0])
        dup_inst.only_these(joints)
        dup_inst.add_prefix('topOffset_')
        dup_inst.stop_at(joints[-2])
        self._ik_joints_top = dup_inst.create()

        dup_inst = space.DuplicateHierarchy(joints[2])
        dup_inst.only_these(joints)
        dup_inst.add_prefix('btmOffset_')
        dup_inst.stop_at(joints[-1])
        self._ik_joints_btm = dup_inst.create()
        cmds.parent(self._ik_joints_btm, w=True)
        space.MatchSpace(self._ik_joints_btm[0], self._ik_joints_btm[1]).rotation()
        cmds.parent(self._ik_joints_btm[0], self._ik_joints_btm[1])
        self._ik_joints_btm.reverse()
        cmds.makeIdentity(self._ik_joints_btm, apply=True, r=True)

        all_joints = self._ik_joints + self._ik_joints_top + self._ik_joints_btm

        for joint in all_joints:
            cmds.makeIdentity(joint, apply=True, t=True, r=True, s=True)

        cmds.parent(self._ik_joints[0], ik_chain_group)
        cmds.parent(self._ik_joints_top[0], ik_chain_group)
        cmds.parent(self._ik_joints_btm[0], ik_chain_group)

        self._add_to_set(self._ik_joints)
        self._add_to_set(self._ik_joints_top)
        self._add_to_set(self._ik_joints_btm)

        return ik_chain_group

    def _attach_ik(self):
        loc_ik = cmds.spaceLocator(n=self.get_name('loc', 'ik'))[0]
        cmds.hide(loc_ik + 'Shape')
        space.MatchSpace(self._ik_joints[-1], loc_ik).translation_rotation()

        handle = space.IkHandle(self.get_name('ik'))
        handle.set_start_joint(self._ik_joints[0])
        handle.set_end_joint(self._ik_joints[-1])
        handle.set_solver(handle.solver_rp)
        handle.create()
        ik_handle = handle.ik_handle
        cmds.hide(ik_handle)

        handle = space.IkHandle(self.get_name('ik_top'))
        handle.set_start_joint(self._ik_joints_top[0])
        handle.set_end_joint(self._ik_joints_top[-1])
        handle.set_solver(handle.solver_sc)
        handle.create()
        top_ik_handle = handle.ik_handle
        cmds.hide(top_ik_handle)

        handle = space.IkHandle(self.get_name('ik_btm'))
        handle.set_start_joint(self._ik_joints_btm[0])
        handle.set_end_joint(self._ik_joints_btm[-1])
        handle.set_solver(handle.solver_sc)
        handle.create()
        btm_ik_handle = handle.ik_handle
        cmds.hide(btm_ik_handle)

        attr.store_world_matrix_to_attribute(ik_handle, 'origMatrix')
        attr.store_world_matrix_to_attribute(top_ik_handle, 'origMatrix')
        attr.store_world_matrix_to_attribute(btm_ik_handle, 'origMatrix')

        subs = attr.get_multi_message(self._controls[-1], 'sub')
        if subs:
            ik_control = subs[-1]
        else:
            ik_control = self._controls[-1]

        cmds.parent(ik_handle, ik_control)
        cmds.parent(loc_ik, ik_control)

        cmds.poleVectorConstraint(self._controls[1], ik_handle)
        cmds.orientConstraint(loc_ik, self._ik_joints[-1], mo=True)

        cmds.parent(top_ik_handle, self._ik_joints_btm[0])
        cmds.parent(btm_ik_handle, ik_control)

        cmds.parent(self._ik_joints_top[0], self._ik_joints[0])
        cmds.parent(self._ik_joints_btm[0], self._ik_joints[-1])
        cmds.parent(top_ik_handle, self._ik_joints_btm[-1])
        cmds.parent(btm_ik_handle, self.control_ankle)

        driver = space.get_xform_group(self.control_ankle, 'driver')
        space.MatchSpace(self._ik_joints[-2], driver).rotate_scale_pivot_to_translation()

        cmds.parentConstraint(self._ik_joints[-2], driver, mo=True)

        self._ik_transform = [ik_handle, loc_ik]

    def _attach(self, joints):

        self._attach_ik()

        space.attach(self._controls[0], self._ik_joints[0])

        joint_pairs = [[self._ik_joints_top[0], joints[0]],
                       [self._ik_joints_top[1], joints[1]],
                       [self._ik_joints_btm[1], joints[2]],
                       [self._ik_joints[-1], joints[3]]]

        for joint_pair in joint_pairs:
            ik_joint = joint_pair[0]
            joint = joint_pair[1]
            mult_matrix, blend_matrix = space.attach(ik_joint, joint)
            self._mult_matrix_nodes.append(mult_matrix)
            self._blend_matrix_nodes.append(blend_matrix)

        if self._blend_matrix_nodes:
            space.blend_matrix_switch(self._blend_matrix_nodes, 'switch', attribute_node=self.rig.joints[0])

    def _style_controls(self):
        super(MayaIkQuadrupedRig, self)._style_controls()

        control = Control(self._controls[-2])
        control.shape = 'square'

        # control.scale_shape(1, 1, 1)


class MayaWheelRig(MayaUtilRig):

    def _build_wheel_automation(self, control, spin_control):

        forward_axis = self.rig.attr.get('forward_axis')
        rotate_axis = self.rig.attr.get('rotate_axis')
        diameter = self.rig.attr.get('wheel_diameter')

        steer_control = self.rig.attr.get('steer_control')

        attr.create_title(control, 'WHEEL')
        wheel_expression = expressions.initialize_wheel_script(control)
        expression_node = expressions.create_expression('wheel_expression', wheel_expression)

        cmds.setAttr('%s.targetAxisX' % control, forward_axis[0][0])
        cmds.setAttr('%s.targetAxisY' % control, forward_axis[0][1])
        cmds.setAttr('%s.targetAxisZ' % control, forward_axis[0][2])

        cmds.setAttr('%s.spinAxisX' % control, rotate_axis[0][0])
        cmds.setAttr('%s.spinAxisY' % control, rotate_axis[0][1])
        cmds.setAttr('%s.spinAxisZ' % control, rotate_axis[0][2])

        cmds.setAttr('%s.diameter' % control, diameter[0])

        compose = cmds.createNode('composeMatrix', n='composeMatrix_wheel_%s' % control)
        cmds.connectAttr('%s.spinX' % control, '%s.inputRotateX' % compose)
        cmds.connectAttr('%s.spinY' % control, '%s.inputRotateY' % compose)
        cmds.connectAttr('%s.spinZ' % control, '%s.inputRotateZ' % compose)

        cmds.addAttr(control, ln='steer', k=True)

        if steer_control:
            self._build_steer_control(steer_control[0], control)

        vector_product = cmds.createNode('vectorProduct', n=self.get_name('vectorProduct', 'steer'))

        cmds.setAttr('%s.operation' % vector_product, 2)
        cmds.connectAttr('%s.targetAxisX' % control, '%s.input1X' % vector_product)
        cmds.connectAttr('%s.targetAxisY' % control, '%s.input1Y' % vector_product)
        cmds.connectAttr('%s.targetAxisZ' % control, '%s.input1Z' % vector_product)

        cmds.connectAttr('%s.spinAxisX' % control, '%s.input2X' % vector_product)
        cmds.connectAttr('%s.spinAxisY' % control, '%s.input2Y' % vector_product)
        cmds.connectAttr('%s.spinAxisZ' % control, '%s.input2Z' % vector_product)

        mult = cmds.createNode('multiplyDivide', n=self.get_name('multiplyDivide', 'steer'))

        cmds.connectAttr('%s.outputX' % vector_product, '%s.input1X' % mult)
        cmds.connectAttr('%s.outputY' % vector_product, '%s.input1Y' % mult)
        cmds.connectAttr('%s.outputZ' % vector_product, '%s.input1Z' % mult)

        cmds.connectAttr('%s.steer' % control, '%s.input2X' % mult)
        cmds.connectAttr('%s.steer' % control, '%s.input2Y' % mult)
        cmds.connectAttr('%s.steer' % control, '%s.input2Z' % mult)

        compose_steer = cmds.createNode('composeMatrix', n=self.get_name('composeMatrix', 'steer'))
        mult_matrix_steer = cmds.createNode('multMatrix', n=self.get_name('multMatrix', 'steer'))
        mult_matrix_target = cmds.createNode('multMatrix', n=self.get_name('multMatrix', 'target'))

        cmds.connectAttr('%s.outputX' % mult, '%s.inputRotateX' % compose_steer)
        cmds.connectAttr('%s.outputY' % mult, '%s.inputRotateY' % compose_steer)
        cmds.connectAttr('%s.outputZ' % mult, '%s.inputRotateZ' % compose_steer)

        cmds.connectAttr('%s.outputMatrix' % compose, '%s.matrixIn[0]' % mult_matrix_steer)
        cmds.connectAttr('%s.outputMatrix' % compose_steer, '%s.matrixIn[1]' % mult_matrix_steer)

        cmds.connectAttr('%s.outputMatrix' % compose_steer, '%s.matrixIn[0]' % mult_matrix_target)
        cmds.connectAttr('%s.worldMatrix[0]' % control, '%s.matrixIn[1]' % mult_matrix_target)

        target_vector_product = attr.get_attribute_input('%s.targetX' % control, node_only=True)
        if target_vector_product:
            cmds.connectAttr('%s.matrixSum' % mult_matrix_target, '%s.matrix' % target_vector_product, f=True)

        cmds.connectAttr('%s.matrixSum' % mult_matrix_steer, '%s.offsetParentMatrix' % spin_control)

        self._add_to_set([expression_node])

    def _build_steer_control(self, steer_control, wheel_control):

        attr_name = 'translate'

        steer_axis = self.rig.attr.get('steer_axis')
        steer_use_rotate = self.rig.attr.get('steer_use_rotate')

        steer_axis = list(steer_axis[0])

        letter = util_math.get_vector_axis_letter(steer_axis)

        if letter.startswith('-'):
            letter = letter[1]

        if steer_use_rotate:
            attr_name = 'rotate'

        if letter == 'X':
            value = steer_axis[0]
        if letter == 'Y':
            value = steer_axis[1]
        if letter == 'Z':
            value = steer_axis[2]

        steer_attr = '%s.steer' % wheel_control
        steer_attr_name = steer_attr.replace('.', '_')
        multiply_name = 'multiplyDivide_' + steer_attr_name

        input_steer = attr.get_attribute_input(steer_attr, node_only=True)
        if input_steer == multiply_name:
            cmds.delete(multiply_name)
        else:
            attr.disconnect_attribute(steer_attr)

        attr.connect_multiply('%s.%s%s' % (steer_control, attr_name, letter), '%s.steer' % wheel_control, value=value)

    @property
    def steer_control(self):
        return self.rig.attr.get('steer_control')

    @steer_control.setter
    def steer_control(self, controls):
        self.rig.attr.set('steer_control', controls)

        steer_control = controls[0]

        controls = self.rig.attr.get('controls')
        if controls:
            self._build_steer_control(steer_control, controls[0])

    def _build_rig(self, joints):
        super(MayaWheelRig, self)._build_rig(joints)

        if not joints:
            return

        joints = cmds.ls(joints, l=True)
        # joints = core.get_hierarchy_by_depth(joints)

        control = self._create_control()
        spin_control = self._create_control('spin')

        control = str(control)
        spin_control = str(spin_control)

        cmds.parent(str(spin_control), control)

        cmds.matchTransform(control, joints[0])

        for _control in self._controls:
            space.zero_out(_control)

        self._build_wheel_automation(control, spin_control)

        cmds.setAttr('%s.enable' % self._controls[0], 1)

        mult_matrix, blend_matrix = space.attach(spin_control, joints[0])

        self._mult_matrix_nodes.append(mult_matrix)
        self._blend_matrix_nodes.append(blend_matrix)

        return self._controls

    def _style_controls(self):
        diameter = self.rig.attr.get('wheel_diameter')[0]
        diameter = diameter * .165453342157 * 2

        control = self._controls[0]
        spin_control = self._controls[1]

        control.rotate_shape(0, 0, 90)
        control.scale_shape(diameter, diameter, diameter)

        spin_shape = self.rig.spin_control_shape[0]
        if self.rig.attr.get('spin_control_shape') == ['Default']:
            spin_shape = 'circle_point'

        spin_control.shape = spin_shape

        spin_control.color = self.rig.spin_control_color
        spin_control.rotate_shape(0, 0, 90)
        spin_control.scale_shape(diameter * .5, diameter * .5, diameter * .5)
