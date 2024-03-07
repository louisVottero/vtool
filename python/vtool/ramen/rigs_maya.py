from . import rigs

from vtool import util
from vtool import util_file
from vtool import util_math

from ..maya_lib import curve

in_maya = util.in_maya

if in_maya:
    import maya.cmds as cmds

    from ..maya_lib import attr
    from ..maya_lib import space as space_old
    from ..maya_lib2 import space
    from ..maya_lib import core
    from ..maya_lib import expressions

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

        match = space_old.MatchSpace(self.name, joint)
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
        identity_matrix = [1, 0, 0, 0,
                           0, 1, 0, 0,
                           0, 0, 1, 0,
                           0, 0, 0, 1]
        cmds.setAttr('%s.offsetParentMatrix' % joint, *identity_matrix, type="matrix")

    def is_valid(self):
        if self.set and cmds.objExists(self.set):
            return True

        return False

    @property
    def parent(self):
        return self.rig.attr.get('parent')

    @parent.setter
    def parent(self, parent):
        util.show('\t\tSetting parent: %s' % parent)
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
        return self.rig.attr.get('shape')[0]

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
            for control in self._controls:
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

    def get_control_name(self, description=None, sub=False):

        control_name_inst = util_file.ControlNameFromSettingsFile()

        # if sub == False and len(self.rig.joints) == 1:

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

        if sub == True:
            description = 'sub_1_%s' % description

        control_name = control_name_inst.get_name(description, side)
        return control_name

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

            sub_control_inst = self._create_control(description, sub=True)

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
        axis = space_old.get_axis_letter_aimed_at_child(joint)
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
        self._subs = {}

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

            nice_joint = core.get_basename(joint)

            attach_control = control
            if control in self._subs:
                attach_control = self._subs[control][-1]

            mult_matrix, blend_matrix = space.attach(attach_control, nice_joint)

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
        joint_token = self.rig.attr.get('joint_token')

        for joint in joints:

            description = None
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

            sub_control_count = self.rig.attr.get('sub_count')

            joint_control[joint] = control

            if rotate_cvs:
                self.rotate_cvs_to_axis(control_inst, joint)

            last_control = None
            parent = cmds.listRelatives(joint, p=True, f=True)
            if parent:
                parent = parent[0]
                if parent in joint_control:
                    last_control = joint_control[parent]
            if not parent and last_joint:
                last_control = joint_control[last_joint]

            if last_control:

                if last_control not in parenting:
                    parenting[last_control] = []

                parenting[last_control].append(control)

            cmds.matchTransform(control, joint)

            nice_joint = core.get_basename(joint)
            mult_matrix, blend_matrix = space.attach(control, nice_joint)

            self._mult_matrix_nodes.append(mult_matrix)
            self._blend_matrix_nodes.append(blend_matrix)

            last_joint = joint

        for parent in parenting:
            children = parenting[parent]

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

        self._parent_controls(self.parent)

        self.rig.attr.set('controls', self._controls)

        return self._controls


class MayaWheelRig(MayaUtilRig):

    def _build_wheel_automation(self, control, spin_control):

        forward_axis = self.rig.attr.get('forward_axis')
        rotate_axis = self.rig.attr.get('rotate_axis')
        diameter = self.rig.attr.get('wheel_diameter')

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

        cmds.connectAttr('%s.outputMatrix' % compose, '%s.offsetParentMatrix' % spin_control)

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

        mult_matrix, blend_matrix = space.attach(spin_control, joints[0])

        self._mult_matrix_nodes.append(mult_matrix)
        self._blend_matrix_nodes.append(blend_matrix)

        self._tag_parenting()
        self._parent_controls(self.parent)

        return self._controls
