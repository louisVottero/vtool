# Copyright (C) 2024 Louis Vottero louis.vot@gmail.com    All rights reserved.

from .. import logger

log = logger.get_logger(__name__)

from . import rigs

from vtool import util


class Fk(rigs.RigJoint):
    rig_type = rigs.RigType.FK
    rig_description = 'fk'

    def _init_variables(self):
        super(Fk, self)._init_variables()

        self.attr.add_to_node('FK', '', rigs.AttrType.TITLE)
        self.attr.add_to_node('hierarchy', True, rigs.AttrType.BOOL)

    def _maya_rig(self):
        from . import rigs_maya
        return rigs_maya.MayaFkRig()

    def _unreal_rig(self):
        from . import rigs_unreal
        return rigs_unreal.UnrealFkRig()

    def _houdini_rig(self):

        from . import  rigs_houdini
        return rigs_houdini.HoudiniFkRig()


class Ik(rigs.RigJoint):
    rig_type = rigs.RigType.IK
    rig_description = 'ik'

    def _init_variables(self):
        super(Ik, self)._init_variables()

        self.attr.add_to_node('IK', '', rigs.AttrType.TITLE)
        self.attr.add_in('aim_axis', [[1.0, 0.0, 0.0]], rigs.AttrType.VECTOR)
        self.attr.add_in('pole_vector_offset', [1], rigs.AttrType.NUMBER)
        self.attr.add_in('pole_vector_shape', ['Default'], rigs.AttrType.STRING)

        self.attr.add_out('ik', [], rigs.AttrType.TRANSFORM)

    def _maya_rig(self):
        from . import rigs_maya
        return rigs_maya.MayaIkRig()

    def _unreal_rig(self):
        from . import rigs_unreal
        return rigs_unreal.UnrealIkRig()


class SplineIk(rigs.RigJoint):
    rig_type = rigs.RigType.SPLINEIK
    rig_description = 'spline ik'

    def _init_variables(self):
        super(SplineIk, self)._init_variables()

        self.attr.add_to_node('IK', '', rigs.AttrType.TITLE)
        self.attr.add_to_node('hierarchy', False, rigs.AttrType.BOOL)
        self.attr.add_to_node('control_count', [4], rigs.AttrType.INT)
        self.attr.add_in('aim_axis', [[1.0, 0.0, 0.0]], rigs.AttrType.VECTOR)
        self.attr.add_in('up_axis', [[0.0, 1.0, 0.0]], rigs.AttrType.VECTOR)

    def _maya_rig(self):
        from . import rigs_maya
        return rigs_maya.MayaSplineIkRig()

    def _unreal_rig(self):
        from . import rigs_unreal
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
        self.attr.add_in('spin_control_shape', ['Default'], rigs.AttrType.STRING)
        self.attr.add_in('spin_control_color', [[.5, 0.5, 0, 1.0]], rigs.AttrType.COLOR)
        self.attr.add_to_node('wheel_diameter', [1.0], rigs.AttrType.NUMBER)
        self.attr.add_in('forward_axis', [[0.0, 0.0, 1.0]], rigs.AttrType.VECTOR)
        self.attr.add_in('rotate_axis', [[1.0, 0.0, 0.0]], rigs.AttrType.VECTOR)
        self.attr.add_to_node('Steer', '', rigs.AttrType.TITLE)
        self.attr.add_in('steer_control', [], rigs.AttrType.TRANSFORM)
        self.attr.add_in('steer_axis', [[0.0, 0.0, 1.0]], rigs.AttrType.VECTOR)
        self.attr.add_to_node('steer_use_rotate', False, rigs.AttrType.BOOL)

    def _maya_rig(self):
        from . import rigs_maya
        return rigs_maya.MayaWheelRig()

    def _unreal_rig(self):
        from . import rigs_unreal
        return rigs_unreal.UnrealWheelRig()


class QuadrupedLegIk(rigs.RigJoint):
    rig_type = rigs.RigType.IK
    rig_description = 'ik'

    def _init_variables(self):
        super(QuadrupedLegIk, self)._init_variables()

        self.attr.add_to_node('IK', '', rigs.AttrType.TITLE)
        self.attr.add_in('aim_axis', [[1.0, 0.0, 0.0]], rigs.AttrType.VECTOR)
        self.attr.add_in('pole_vector_offset', [1], rigs.AttrType.NUMBER)
        self.attr.add_in('pole_vector_shape', ['Default'], rigs.AttrType.STRING)

    def _maya_rig(self):
        from . import rigs_maya
        return rigs_maya.MayaQuadrupedLegRig()

    def _unreal_rig(self):
        from . import rigs_unreal
        return rigs_unreal.UnrealQuadrupedLegIkRig()


class FootRoll(rigs.RigJoint):
    rig_type = rigs.RigType.IK
    rig_description = 'ik'

    def _init_variables(self):
        super(FootRoll, self)._init_variables()

        self.attr.add_to_node('IK', '', rigs.AttrType.TITLE)
        self.attr.add_in('ik', [], rigs.AttrType.TRANSFORM)

    def _use_joint_name(self):
        return False

    def _maya_rig(self):
        from . import rigs_maya
        return rigs_maya.MayaFootRollRig()

    def _unreal_rig(self):
        from . import rigs_unreal
        return rigs_unreal.UnrealFootRollRig()


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
        from . import rigs_unreal
        return rigs_unreal.UnrealGetTransform()


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
        from . import rigs_unreal
        return rigs_unreal.UnrealGetSubControls()

