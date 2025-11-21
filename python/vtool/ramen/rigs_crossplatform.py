# Copyright (C) 2024 Louis Vottero louis.vot@gmail.com    All rights reserved.

from vtool import util
from . import rigs
from .. import logger

log = logger.get_logger(__name__)

if util.in_maya:
    from . import rigs_maya
if util.in_houdini:
    from . import rigs_houdini
if util.in_unreal:
    from . import rigs_unreal


class Fk(rigs.RigJoint):
    rig_type = rigs.RigType.FK
    rig_description = 'fk'

    def _init_variables(self):
        super(Fk, self)._init_variables()

        self.attr.add_to_node('FK', '', rigs.AttrType.TITLE)
        self.attr.add_to_node('hierarchy', True, rigs.AttrType.BOOL)
        self.attr.add_to_node('attach', True, rigs.AttrType.BOOL)

    def _maya_rig(self):
        return rigs_maya.MayaFkRig()

    def _unreal_rig(self):
        return rigs_unreal.UnrealFkRig()

    def _houdini_rig(self):
        return rigs_houdini.HoudiniFkRig()


class Ik(rigs.RigJoint):
    rig_type = rigs.RigType.IK
    rig_description = 'ik'

    def _init_variables(self):
        super(Ik, self)._init_variables()

        self.attr.add_to_node('IK', '', rigs.AttrType.TITLE)
        self.attr.add_in('world', False, rigs.AttrType.BOOL)
        self.attr.add_in('mirror', False, rigs.AttrType.BOOL)
        self.attr.add_in('stretch', False, rigs.AttrType.BOOL)
        self.attr.add_to_node('POLE VECTOR', '', rigs.AttrType.TITLE)
        self.attr.add_in('pole_vector_offset', [1], rigs.AttrType.NUMBER)
        self.attr.add_in('pole_vector_shape',
                         ['Default'], rigs.AttrType.STRING)

        self.attr.add_out('ik', [], rigs.AttrType.TRANSFORM)

    def _maya_rig(self):
        return rigs_maya.MayaIkRig()

    def _unreal_rig(self):
        return rigs_unreal.UnrealIkRig()


class SplineIk(rigs.RigJoint):
    rig_type = rigs.RigType.SPLINEIK
    rig_description = 'spline ik'

    def _init_variables(self):
        super(SplineIk, self)._init_variables()

        self.attr.add_to_node('IK', '', rigs.AttrType.TITLE)
        self.attr.add_to_node('hierarchy', False, rigs.AttrType.BOOL)
        self.attr.add_to_node('control_count', [4], rigs.AttrType.INT)
        # self.attr.add_in('aim_axis', [[0.0, 0.0, 0.0]], rigs.AttrType.VECTOR)
        # self.attr.add_in('up_axis', [[0.0, 0.0, 0.0]], rigs.AttrType.VECTOR)

    def _use_joint_name(self):
        return False

    def _maya_rig(self):
        return rigs_maya.MayaSplineIkRig()

    def _unreal_rig(self):
        return rigs_unreal.UnrealSplineIkRig()


class Wheel(rigs.RigJoint):

    rig_type = rigs.RigType.WHEEL
    rig_description = 'wheel'

    def _support_sub_controls(self):
        return False

    def _use_joint_name(self):
        return False

    def _init_variables(self):
        super(Wheel, self)._init_variables()

        self.attr.add_to_node('Wheel', '', rigs.AttrType.TITLE)
        self.attr.add_in('spin_control_shape',
                         ['Default'], rigs.AttrType.STRING)
        self.attr.add_in('spin_control_color', [
                         [.5, 0.5, 0, 1.0]], rigs.AttrType.COLOR)
        self.attr.add_to_node('wheel_diameter', [1.0], rigs.AttrType.NUMBER)
        self.attr.add_in('forward_axis',
                         [[0.0, 0.0, 1.0]], rigs.AttrType.VECTOR)
        self.attr.add_in('rotate_axis',
                         [[1.0, 0.0, 0.0]], rigs.AttrType.VECTOR)
        self.attr.add_to_node('Steer', '', rigs.AttrType.TITLE)
        self.attr.add_in('steer_control', [], rigs.AttrType.TRANSFORM)
        self.attr.add_in('steer_axis', [[0.0, 0.0, 1.0]], rigs.AttrType.VECTOR)
        self.attr.add_to_node('steer_use_rotate', False, rigs.AttrType.BOOL)

    def _maya_rig(self):
        return rigs_maya.MayaWheelRig()

    def _unreal_rig(self):
        return rigs_unreal.UnrealWheelRig()


class FootRoll(rigs.RigJoint):
    rig_type = rigs.RigType.IK
    rig_description = 'ik'

    def _custom_sub_control_count(self):
        return False

    def _init_variables(self):
        super(FootRoll, self)._init_variables()

        self.attr.add_to_node('Foot Roll', '', rigs.AttrType.TITLE)
        self.attr.add_in('ik', [], rigs.AttrType.TRANSFORM)
        self.attr.add_in('forward_axis',
                         [[0.0, 0.0, 1.0]], rigs.AttrType.VECTOR)
        self.attr.add_in('up_axis', [[0.0, 1.0, 0.0]], rigs.AttrType.VECTOR)
        self.attr.add_in('mirror', False, rigs.AttrType.BOOL)
        self.attr.add_in('attribute_control', [], rigs.AttrType.TRANSFORM)
        self.attr.add_to_node('Pivots', '', rigs.AttrType.TITLE)
        self.attr.add_in('heel_pivot', [[0.0, 0.0, 0.0]], rigs.AttrType.VECTOR)
        self.attr.add_in('yaw_in_pivot',
                         [[0.0, 0.0, 0.0]], rigs.AttrType.VECTOR)
        self.attr.add_in('yaw_out_pivot',
                         [[0.0, 0.0, 0.0]], rigs.AttrType.VECTOR)
        self.attr.add_to_node('Switch', '', rigs.AttrType.TITLE)
        self.attr.add_in('switch_control', [], rigs.AttrType.TRANSFORM)
        self.attr.add_in('fk_parent', [], rigs.AttrType.TRANSFORM)
        self.attr.add_in('fk_first', [], rigs.AttrType.BOOL)

    def _use_joint_name(self):
        return False

    def _maya_rig(self):
        return rigs_maya.MayaFootRollRig()

    def _unreal_rig(self):
        return rigs_unreal.UnrealFootRollRig()


class IkQuadruped(Ik):
    rig_type = rigs.RigType.IK
    rig_description = 'ik'

    def _init_variables(self):
        super(IkQuadruped, self)._init_variables()

    def _maya_rig(self):
        return rigs_maya.MayaIkQuadrupedRig()

    def _unreal_rig(self):
        return rigs_unreal.UnrealIkQuadrupedRig()


class GetTransform(rigs.RigUtil):
    rig_type = rigs.RigType.UTIL
    rig_description = 'get an item at index'

    def _init_variables(self):
        super(GetTransform, self)._init_variables()

        self.attr.add_in('transforms', [], rigs.AttrType.TRANSFORM)
        self.attr.add_to_node('index', [-1], rigs.AttrType.INT)
        self.attr.add_out('transform', [], rigs.AttrType.TRANSFORM)

    def _maya_rig(self):
        return None

    def _unreal_rig(self):
        return rigs_unreal.UnrealGetTransform()


class GetTransforms(rigs.RigUtil):
    rig_type = rigs.RigType.UTIL
    rig_description = 'get at index from multiple input items'

    def _init_variables(self):
        super(GetTransforms, self)._init_variables()

        self.attr.add_in('transforms1', [], rigs.AttrType.TRANSFORM)
        self.attr.add_to_node('index1', [-1], rigs.AttrType.INT)
        self.attr.add_in('transforms2', [], rigs.AttrType.TRANSFORM)
        self.attr.add_to_node('index2', [-1], rigs.AttrType.INT)
        self.attr.add_in('transforms3', [], rigs.AttrType.TRANSFORM)
        self.attr.add_to_node('index3', [-1], rigs.AttrType.INT)
        self.attr.add_in('transforms4', [], rigs.AttrType.TRANSFORM)
        self.attr.add_to_node('index4', [-1], rigs.AttrType.INT)
        self.attr.add_in('transforms5', [], rigs.AttrType.TRANSFORM)
        self.attr.add_to_node('index5', [-1], rigs.AttrType.INT)

        self.attr.add_out('transforms', [], rigs.AttrType.TRANSFORM)


class GetSubControls(rigs.RigUtil):
    rig_type = rigs.RigType.UTIL
    rig_description = 'get sub controls'

    def _init_variables(self):
        super(GetSubControls, self)._init_variables()

        self.attr.add_in('controls', [], rigs.AttrType.TRANSFORM)
        self.attr.add_to_node('control_index', [-1], rigs.AttrType.INT)
        self.attr.add_out('sub_controls', [], rigs.AttrType.TRANSFORM)

    def _maya_rig(self):
        return None

    def _unreal_rig(self):
        return rigs_unreal.UnrealGetSubControls()


class Parent(rigs.RigUtil):
    rig_type = rigs.RigType.UTIL
    rig_description = 'parent controls'

    def _init_variables(self):
        super(Parent, self)._init_variables()

        self.attr.add_in('parent', [], rigs.AttrType.TRANSFORM)
        self.attr.add_to_node('parent_index', [-1], rigs.AttrType.INT)
        self.attr.add_in('children', [], rigs.AttrType.TRANSFORM)
        self.attr.add_to_node('affect_all_children', False, rigs.AttrType.BOOL)
        self.attr.add_to_node('child_indices', ['-1'], rigs.AttrType.STRING)

    def _maya_rig(self):
        return None

    def _unreal_rig(self):
        return rigs_unreal.UnrealParent()


class Anchor(rigs.RigUtil):
    rig_type = rigs.RigType.UTIL
    rig_description = 'anchor controls'

    def _init_variables(self):
        super(Anchor, self)._init_variables()

        self.attr.add_in('parent', [], rigs.AttrType.TRANSFORM)
        self.attr.add_to_node('use_all_parents', False, rigs.AttrType.BOOL)
        self.attr.add_to_node('parent_index', ['-1'], rigs.AttrType.STRING)
        self.attr.add_to_node('Affected', '', rigs.AttrType.TITLE)
        self.attr.add_in('children', [], rigs.AttrType.TRANSFORM)
        self.attr.add_to_node('affect_all_children', False, rigs.AttrType.BOOL)
        self.attr.add_to_node('child_indices', ['-1'], rigs.AttrType.STRING)

        self.attr.add_to_node('Transform', '', rigs.AttrType.TITLE)
        self.attr.add_to_node('use_child_pivot', False, rigs.AttrType.BOOL)
        self.attr.add_to_node('translate', True, rigs.AttrType.BOOL)
        self.attr.add_to_node('rotate', True, rigs.AttrType.BOOL)
        self.attr.add_to_node('scale', True, rigs.AttrType.BOOL)

        # self.attr.add_to_node('weight', [1.0], rigs.AttrType.NUMBER)

    def _maya_rig(self):
        return rigs_maya.MayaAnchor()

    def _unreal_rig(self):
        return rigs_unreal.UnrealAnchor()


class Switch(rigs.RigUtil):
    rig_type = rigs.RigType.UTIL
    rig_description = 'hookup switch'

    def _init_variables(self):
        super(Switch, self)._init_variables()

        self.attr.add_in('parent', [], rigs.AttrType.TRANSFORM)
        self.attr.add_in('joints', [], rigs.AttrType.TRANSFORM)
        self.attr.add_in('attribute_control', [], rigs.AttrType.TRANSFORM)
        self.attr.add_to_node('control_index', [-1], rigs.AttrType.INT)
        self.attr.add_to_node('Name', [''], rigs.AttrType.TITLE)
        self.attr.add_in('description', ['switch'], rigs.AttrType.STRING)
        self.attr.add_in('side', [''], rigs.AttrType.STRING)
        self.attr.add_to_node('restrain_numbering', True, rigs.AttrType.BOOL)
        self.attr.add_to_node('Attribute', [''], rigs.AttrType.TITLE)
        self.attr.add_in('attribute_name', ['fkIk'], rigs.AttrType.STRING)
        self.attr.add_to_node('If Not Control', [''], rigs.AttrType.TITLE)

        self.attr.add_in('color', [[1, 0.0, 0, 1.0]], rigs.AttrType.COLOR)
        self.attr.add_in('shape', ['Default'], rigs.AttrType.STRING)
        self.attr.add_in('shape_translate',
                         [[0.0, 0.0, 0.0]], rigs.AttrType.VECTOR)
        self.attr.add_in('shape_rotate',
                         [[0.0, 0.0, 0.0]], rigs.AttrType.VECTOR)
        self.attr.add_in('shape_scale',
                         [[1.0, 1.0, 1.0]], rigs.AttrType.VECTOR)

        self.attr.add_out('controls', [], rigs.AttrType.TRANSFORM)

    def _maya_rig(self):
        return rigs_maya.MayaSwitch()

    def _unreal_rig(self):
        return rigs_unreal.UnrealSwitch()


class SpaceSwitch(rigs.RigUtil):
    rig_type = rigs.RigType.UTIL
    rig_description = 'space switch'

    def _init_variables(self):
        super(SpaceSwitch, self)._init_variables()

        self.attr.add_to_node('Spaces', '', rigs.AttrType.TITLE)
        self.attr.add_in('parent', [], rigs.AttrType.TRANSFORM)
        self.attr.add_to_node('names', [''], rigs.AttrType.STRING)
        self.attr.add_to_node('Affected', '', rigs.AttrType.TITLE)
        self.attr.add_in('children', [], rigs.AttrType.TRANSFORM)
        self.attr.add_to_node('affect_all_children', False, rigs.AttrType.BOOL)
        self.attr.add_to_node('child_indices', ['-1'], rigs.AttrType.STRING)
        self.attr.add_to_node('Attribute', '', rigs.AttrType.TITLE)
        self.attr.add_in('attribute_control', [], rigs.AttrType.TRANSFORM)
        self.attr.add_to_node('attribute_name', ['space'], rigs.AttrType.STRING)
        self.attr.add_to_node('Transform', '', rigs.AttrType.TITLE)
        self.attr.add_to_node('use_child_pivot', False, rigs.AttrType.BOOL)
        self.attr.add_to_node('translate', True, rigs.AttrType.BOOL)
        self.attr.add_to_node('rotate', True, rigs.AttrType.BOOL)
        self.attr.add_to_node('scale', True, rigs.AttrType.BOOL)

    def _maya_rig(self):
        return rigs_maya.MayaSpaceSwitch()
