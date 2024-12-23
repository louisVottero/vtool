# Copyright (C) 2024 Louis Vottero louis.vot@gmail.com    All rights reserved.

from . import rigs

from vtool import util
from vtool import util_file
from vtool import util_math

from ..maya_lib import curve

in_maya = util.in_maya

if in_maya:
    import maya.cmds as cmds

    from ..maya_lib import attr
    from ..maya_lib import space
    from ..maya_lib import core
    from ..maya_lib import expressions
    from ..maya_lib import geo
    from ..maya_lib import deform

curve_data = curve.CurveDataInfo()
curve_data.set_active_library('default_curves')


class Control(object):

    def __init__(self, name):

        self._color = None
        self._use_joint = False

        self.name = ''
        self.shape = ''
        self.tag = True
        self.shapes = []

        self._shape = 'circle'

        self.name = name

        self.uuid = None

        if cmds.objExists(self.name):
            curve_type = cmds.getAttr('%s.curveType' % self.name)
            self.uuid = cmds.ls(self.name, uuid=True)[0]
            self._shape = curve_type
        else:
            self._create()

    def __repr__(self):
        return self.name

    # def __str__(self):
    #    return self.name

    def _get_components(self):

        if not self.shapes:
            self.shapes = core.get_shapes(str(self))

        return core.get_components_from_shapes(self.shapes)

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
            try:
                cmds.parent(to_parent, w=True)
            except:
                pass

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

    def _post_build(self):
        super(MayaUtilRig, self)._post_build()

        found = []
        found += self._controls
        found += self._nodes
        found += self._blend_matrix_nodes
        found += self._mult_matrix_nodes

        self._add_to_set(found)

        cmds.refresh()

    def _create_control(self, description='', sub=False):
        control_name = self.get_control_name(description, sub)
        control_name = control_name.replace('__', '_')

        control_name = core.inc_name(control_name, inc_last_number=not sub)

        control = Control(control_name)
        control.shape = self.rig.shape

        if sub:
            control.color = self.rig.sub_color
        else:
            attr.append_multi_message(self.set, 'control', str(control))
            self._controls.append(control)
            control.color = self.rig.color

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

        control_inst.rotate_shape(self._rotate_shape[0][0], self._rotate_shape[0][1], self._rotate_shape[0][2])
        control_inst.scale_shape(self._scale_shape[0][0], self._scale_shape[0][1], self._scale_shape[0][2])
        control_inst.translate_shape(self._translate_shape[0][0], self._translate_shape[0][1], self._translate_shape[0][2])

    def _reset_offset_matrix(self, joint):
        attr.unlock_attributes(joint, ['offsetParentMatrix'])
        attr.disconnect_attribute('%s.offsetParentMatrix' % joint)
        identity_matrix = [1, 0, 0, 0,
                           0, 1, 0, 0,
                           0, 0, 1, 0,
                           0, 0, 0, 1]
        cmds.setAttr('%s.offsetParentMatrix' % joint, *identity_matrix, type="matrix")

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
        if shape:
            return shape[0]

    @shape.setter
    def shape(self, str_shape):

        if not str_shape:
            str_shape = 'circle'

        self.rig.attr.set('shape', str_shape)

        # eventually can have this interpolate over the sequence of joints, for now just take the first.
        str_shape = str_shape[0]

        if not self._controls:
            return

        if not self.rig.joints:
            return

        for joint, control in zip(self.rig.joints, self._controls):
            control_inst = Control(control)
            control_inst.shape = str_shape
            self._place_control_shape(control_inst)
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
        if joints:
            attr.fill_multi_message(self.set, 'joint', joints)

    def unbuild(self):

        super(MayaUtilRig, self).unbuild()
        if self.set and cmds.objExists(self.set):
            visited = set()
            # TODO break into smaller functions, simplify, use comprehension
            if self._controls:

                for control in self._controls:
                    if not control:
                        continue

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
                        rel_parent = cmds.listRelatives(rel, p=True)
                        if orig_parent != rel_parent[0]:
                            if orig_parent:
                                cmds.parent(rel, orig_parent)
                            else:
                                cmds.parent(rel, w=True)

            joints = attr.get_multi_message(self.set, 'joint')

            attr.clear_multi(self.set, 'joint')
            attr.clear_multi(self.set, 'control')

            result = core.remove_non_existent(self._mult_matrix_nodes)
            if result:
                cmds.delete(result)

            result = core.remove_non_existent(self._blend_matrix_nodes)
            if result:
                cmds.delete(result)

            children = core.get_set_children(self.set)

            found = []
            if children:
                for child in children:
                    if 'dagNode' not in cmds.nodeType(child, inherited=True):
                        found.append(child)
            if found:
                cmds.delete(found)

            if cmds.objExists(self.set):
                core.delete_set_contents(self.set)

            for joint in joints:
                self._reset_offset_matrix(joint)

        self._controls = []
        self._mult_matrix_nodes = []
        self._blend_matrix_nodes = []
        self._nodes = []

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

        return name

    def get_control_name(self, description=None, sub=False):

        if not sub:
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
        else:
            control_name = description.replace('CNT_', 'CNT_SUB_1_')

        return control_name

    def get_sub_control_name(self, control_name):
        control_name = control_name.replace('CNT_', 'CNT_SUB_1_')

    def create_control(self, description=None, sub=False):

        control = self._create_control(description, sub)

        self._place_control_shape(control)

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

            sub_control_inst = self._create_control(core.get_basename(control), sub=True)

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

    def _create_maya_controls(self):
        joints = cmds.ls(self.rig.joints, l=True)
        joints = core.get_hierarchy_by_depth(joints)

        watch = util.StopWatch()
        watch.round = 2

        watch.start('build')

        last_joint = None
        joint_control = {}

        parenting = {}

        rotate_cvs = True

        if len(joints) == 1:
            rotate_cvs = False

        use_joint_name = self.rig.attr.get('use_joint_name')
        hierarchy = self.rig.attr.get('hierarchy')
        joint_token = self.rig.attr.get('joint_token')[0]
        self._sub_control_count = self.rig.attr.get('sub_count')[0]

        description = None

        for joint in joints:

            if use_joint_name:
                joint_nice_name = core.get_basename(joint)
                if joint_token:
                    description = joint_nice_name
                    description = description.replace(joint_token, '')
                    description = util.replace_last_number(description, '')
                    description = description.lstrip('_')
                    description = description.rstrip('_')

                else:
                    description = joint_nice_name

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

        for control in self._controls:
            space.zero_out(control)

        self.rig.attr.set('controls', self._controls)

        watch.end()

    def build(self):
        super(MayaFkRig, self).build()

        self._parent_controls([])

        self._create_maya_controls()
        self._attach()

        self._tag_parenting()
        self._parent_controls(self.parent)

        return self._controls


class MayaIkRig(MayaUtilRig):

    def _create_maya_controls(self):
        joints = cmds.ls(self.rig.joints, l=True)
        joints = core.get_hierarchy_by_depth(joints)

        if not joints:
            return

        watch = util.StopWatch()
        watch.round = 2

        watch.start('build')

        joint_control = {}

        parenting = {}

        pole_vector_offset = self.rig.attr.get('pole_vector_offset')[0]
        pole_vector_shape = self.rig.attr.get('pole_vector_shape')[0]

        first_control = None

        self._sub_control_count = 0

        for joint in joints:

            if joint == joints[-1]:
                self._sub_control_count = self.rig.attr.get('sub_count')[0]

            description = None
            control_inst = self.create_control(description=description)

            if joint == joints[1]:
                control_inst.shape = pole_vector_shape

            control = str(control_inst)

            joint_control[joint] = control

            cmds.matchTransform(control, joint)

            if first_control:
                parenting[first_control].append(control)

            if joint == joints[0]:
                first_control = control
                parenting[control] = []
                # nice_joint = core.get_basename(joint)
                # mult_matrix, blend_matrix = space.attach(control, nice_joint)

            # self._mult_matrix_nodes.append(mult_matrix)
            # self._blend_matrix_nodes.append(blend_matrix)

            # last_joint = joint

        for parent in parenting:
            children = parenting[parent]

            cmds.parent(children, parent)

        pole_posiition = space.get_polevector_at_offset(joints[0], joints[1], joints[-1], pole_vector_offset)
        cmds.xform(self._controls[1], ws=True, t=pole_posiition)

        for control in self._controls:
            space.zero_out(control)

        self.rig.attr.set('controls', self._controls)

        watch.end()

    def _create_ik_chain(self, joints):
        if not joints:
            return

        ik_chain_group = cmds.group(n=self.get_name('setup'), em=True)

        dup_inst = space.DuplicateHierarchy(joints[0])
        dup_inst.only_these(joints)
        dup_inst.stop_at(joints[-1])
        self._ik_joints = dup_inst.create()

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
        handle.set_end_joint(self._ik_joints[-1])
        handle.set_solver(handle.solver_rp)
        handle.create()
        cmds.hide(handle.ik_handle)
        ik_handle = handle.ik_handle

        subs = attr.get_multi_message(self._controls[-1], 'sub')

        ik_control = self._controls[-1]
        if subs:
            ik_control = subs[-1]

        cmds.parent(ik_handle, ik_control)

        cmds.poleVectorConstraint(self._controls[1], ik_handle)
        if not subs:
            cmds.orientConstraint(self._controls[-1], self._ik_joints[-1], mo=True)
        else:
            cmds.orientConstraint(subs, self._ik_joints[-1], mo=True)

        space.attach(self._controls[0], self._ik_joints[0])

        for joint, ik_joint in zip(joints, self._ik_joints):

            mult_matrix, blend_matrix = space.attach(ik_joint, joint)

            self._mult_matrix_nodes.append(mult_matrix)
            self._blend_matrix_nodes.append(blend_matrix)

        if self._blend_matrix_nodes:
            space.blend_matrix_switch(self._blend_matrix_nodes, 'switch', attribute_node=self.rig.joints[0])

        return group

    def build(self):
        super(MayaIkRig, self).build()

        joints = cmds.ls(self.rig.joints, l=True)
        joints = core.get_hierarchy_by_depth(joints)

        self._parent_controls([])

        if joints:
            ik_chain_group = self._create_ik_chain(joints)

            self._create_maya_controls()

            group = self._attach(joints)
            cmds.parent(ik_chain_group, group)

            cmds.parent(group, self._controls[0])

        self._parent_controls(self.parent)

        self.rig.attr.set('controls', self._controls)

        return self._controls


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

        watch = util.StopWatch()
        watch.round = 2

        watch.start('build')

        last_control = None

        parenting = {}

        rotate_cvs = True

        if len(joints) == 1:
            rotate_cvs = False

        # use_joint_name = self.rig.attr.get('use_joint_name')
        hierarchy = self.rig.attr.get('hierarchy')
        joint_token = self.rig.attr.get('joint_token')[0]
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
                # if parent in self._subs:
                #    parent = self._subs[parent][-1]
                cmds.parent(children, parent)

        for control in self._controls:
            space.zero_out(control)

        self.rig.attr.set('controls', self._controls)

        watch.end()

    def build(self):
        super(MayaSplineIkRig, self).build()

        joints = cmds.ls(self.rig.joints, l=True)
        joints = core.get_hierarchy_by_depth(joints)

        if not joints:
            return

        self._parent_controls([])

        self._create_maya_controls(joints)
        self._attach(joints)

        self._tag_parenting()
        self._parent_controls(self.parent)

        return self._controls


class MayaWheelRig(MayaUtilRig):

    def _build_wheel_automation(self, control, spin_control):

        forward_axis = self.rig.attr.get('forward_axis')
        rotate_axis = self.rig.attr.get('rotate_axis')
        diameter = self.rig.attr.get('wheel_diameter')

        steer_control = self.rig.attr.get('steer_control')
        steer_axis = self.rig.attr.get('steer_axis')
        steer_use_rotate = self.rig.attr.get('steer_use_rotate')

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
            steer_control = steer_control[0]
            attr_name = 'translate'
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

            attr.connect_multiply('%s.%s%s' % (steer_control, attr_name, letter), '%s.steer' % control, value=value)

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

    def build(self):
        super(MayaWheelRig, self).build()

        joints = cmds.ls(self.rig.joints, l=True)
        joints = core.get_hierarchy_by_depth(joints)

        if not joints:
            return

        control = self._create_control()
        control.rotate_shape(0, 0, 90)
        spin_control = self._create_control('spin')
        spin_control.shape = self.rig.spin_control_shape[0]
        if spin_control.shape == 'Default':
            spin_control.shape = 'circle_point'

        spin_control.color = self.rig.spin_control_color
        spin_control.rotate_shape(0, 0, 90)
        spin_control.scale_shape(.8, .8, .8)

        self._place_control_shape(control)
        self._place_control_shape(spin_control)

        control = str(control)
        spin_control = str(spin_control)

        cmds.parent(str(spin_control), control)

        cmds.matchTransform(control, joints[0])

        for _control in self._controls:
            space.zero_out(_control)

        self._build_wheel_automation(control, spin_control)

        self.rig.attr.set('controls', self._controls)

        cmds.setAttr('%s.enable' % self._controls[0], 1)

        mult_matrix, blend_matrix = space.attach(spin_control, joints[0])

        self._mult_matrix_nodes.append(mult_matrix)
        self._blend_matrix_nodes.append(blend_matrix)

        self._tag_parenting()
        self._parent_controls(self.parent)

        return self._controls
