# Copyright (C) 2024 Louis Vottero louis.vot@gmail.com    All rights reserved.

from .. import util
from .. import util_math

if util.is_in_maya():
    import maya.cmds as cmds

    from . import core
    from . import attr
    from . import space
    from . import curve
    from . import geo
    from . import deform
    from . import rigs
    from . import rigs_util

# --- Body


class IkQuadrupedBackLegRig(rigs.IkAppendageRig):

    def __init__(self, description, side):
        super(IkQuadrupedBackLegRig, self).__init__(description, side)

        self.offset_control_to_locator = False

    def _duplicate_joints(self):

        super(rigs.IkAppendageRig, self)._duplicate_joints()

        duplicate = space.DuplicateHierarchy(self.joints[0])
        duplicate.stop_at(self.joints[-1])
        duplicate.replace('joint', 'ik')
        self.ik_chain = duplicate.create()

        ik_group = self._create_group()

        cmds.parent(self.ik_chain[0], ik_group)
        cmds.parent(ik_group, self.setup_group)

        self._create_offset_chain(ik_group)

        for inc in range(0, len(self.offset_chain)):
            cmds.parentConstraint(self.offset_chain[inc], self.buffer_joints[inc], mo=True)
            attr.connect_scale(self.offset_chain[inc], self.buffer_joints[inc])

            cmds.connectAttr('%s.scaleX' % self.ik_chain[inc],
                             '%s.scaleX' % self.offset_chain[inc])

        cmds.parentConstraint(self.ik_chain[-1], self.buffer_joints[-1], mo=True)
        attr.connect_scale(self.offset_chain[-1], self.buffer_joints[-1])

        cmds.parentConstraint(self.ik_chain[0], self.offset_chain[0], mo=True)

    def _create_offset_chain(self, parent=None):

        if not parent:
            parent = self.setup_group

        duplicate = space.DuplicateHierarchy(self.joints[0])
        duplicate.stop_at(self.joints[-1])
        duplicate.replace('joint', 'offset')
        self.offset_chain = duplicate.create()

        duplicate = space.DuplicateHierarchy(self.offset_chain[-2])
        duplicate.replace('offset', 'sway')
        self.lower_offset_chain = duplicate.create()

        cmds.parent(self.lower_offset_chain[1], self.offset_chain[-2])
        cmds.parent(self.lower_offset_chain[0], self.lower_offset_chain[1])
        cmds.makeIdentity(self.lower_offset_chain, apply=True, t=1, r=1, s=1, n=0, jointOrient=True)
        cmds.parent(self.lower_offset_chain[1], self.setup_group)
        self.lower_offset_chain.reverse()

        cmds.connectAttr('%s.scaleX' % self.offset_chain[-2], '%s.scaleX' % self.lower_offset_chain[0])

        cmds.delete(self.offset_chain[-1])
        self.offset_chain.pop(-1)

        cmds.orientConstraint(self.lower_offset_chain[0], self.offset_chain[-1])

    def _create_offset_control(self):

        if not self.offset_control_to_locator:
            control = self._create_control(description='offset')
            control.hide_scale_and_visibility_attributes()
            control.scale_shape(2, 2, 2)
            control.set_curve_type('square')

            self.offset_control = control.get()

            match = space.MatchSpace(self.lower_offset_chain[1], self.offset_control)
            match.rotation()

            match = space.MatchSpace(self.lower_offset_chain[0], self.offset_control)
            match.translation()

        if self.offset_control_to_locator:
            self.offset_control = cmds.spaceLocator(n='locator_%s' % self._get_name('offset'))[0]

            match = space.MatchSpace(self.lower_offset_chain[0], self.offset_control)
            match.translation()
            cmds.hide(self.offset_control)

        cmds.parentConstraint(self.offset_control, self.lower_offset_chain[0], mo=True)

        xform_group = space.create_xform_group(self.offset_control)
        driver_group = space.create_xform_group(self.offset_control, 'driver')

        attr.create_title(self.btm_control, 'OFFSET_ANKLE')

        offset = attr.MayaNumberVariable('offsetAnkle')

        offset.create(self.btm_control)
        offset.connect_out('%s.rotateZ' % driver_group)

        follow_group = space.create_follow_group(self.ik_chain[-2], xform_group)

        scale_constraint = cmds.scaleConstraint(self.ik_chain[-2], follow_group)[0]

        space.scale_constraint_to_local(scale_constraint)

        cmds.parent(follow_group, self.top_control)

        if not self.offset_control_to_locator:
            control.hide_translate_attributes()

        return self.offset_control

    def _rig_offset_chain(self):

        ik_handle = space.IkHandle(self._get_name('offset_top'))

        ik_handle.set_start_joint(self.offset_chain[0])
        ik_handle.set_end_joint(self.offset_chain[-1])
        ik_handle.set_solver(ik_handle.solver_rp)
        ik_handle = ik_handle.create()

        cmds.parent(ik_handle, self.lower_offset_chain[-1])

        ik_handle_btm = space.IkHandle(self._get_name('offset_btm'))
        ik_handle_btm.set_start_joint(self.lower_offset_chain[0])
        ik_handle_btm.set_end_joint(self.lower_offset_chain[-1])
        ik_handle_btm.set_solver(ik_handle_btm.solver_sc)
        ik_handle_btm = ik_handle_btm.create()

        follow = space.create_follow_group(self.offset_control, ik_handle_btm)
        cmds.parent(follow, self.setup_group)
        cmds.hide(ik_handle_btm)

    def set_offset_control_to_locator(self, bool_value):
        self.offset_control_to_locator = bool_value

    def create(self):

        super(IkQuadrupedBackLegRig, self).create()

        self._create_offset_control()

        self._rig_offset_chain()

        cmds.setAttr('%s.translateY' % self.pole_vector_xform, 0)


class FkQuadrupedSpineRig(rigs.FkCurveRig):

    def __init__(self, name, side):
        super(FkQuadrupedSpineRig, self).__init__(name, side)

        self.mid_control_joint = None

    def _create_sub_control(self):

        sub_control = rigs_util.Control(self._get_control_name(sub=True))
        sub_control.color(attr.get_color_of_side(self.side, True))
        if self.control_shape:
            sub_control.set_curve_type(self.control_shape)

        sub_control.scale_shape(.75, .75, .75)

        if self.current_increment == 0:
            sub_control.set_curve_type('cube')

        if self.current_increment == 1:
            other_sub_control = rigs_util.Control(self._get_control_name('reverse', sub=True))
            other_sub_control.color(attr.get_color_of_side(self.side, True))

            if self.control_shape:
                other_sub_control.set_curve_type(self.control_shape)

            other_sub_control.scale_shape(2, 2, 2)

            control = self.controls[-1]
            other_sub = other_sub_control.get()

            if self.mid_control_joint:
                space.MatchSpace(self.mid_control_joint, other_sub).translation()
                space.MatchSpace(control, other_sub).rotation()

            if not self.mid_control_joint:
                space.MatchSpace(control, other_sub).translation_rotation()

            xform = space.create_xform_group(other_sub_control.get())

            cmds.parent(xform, self.controls[-2])
            parent = cmds.listRelatives(self.sub_controls[-1], p=True)[0]
            xform = cmds.listRelatives(parent, p=True)[0]

            other_sub_control.hide_scale_and_visibility_attributes()

            cmds.parent(xform, other_sub)

        if self.current_increment == 2:
            pass

        return sub_control

    def set_mid_control_joint(self, joint_name):
        self.mid_control_joint = joint_name


class IkQuadrupedScapula(rigs.BufferRig):

    def __init__(self, description, side):
        super(IkQuadrupedScapula, self).__init__(description, side)

        self.control_offset = 10

    def _create_top_control(self):
        control = self._create_control()
        control.set_curve_type('cube')
        control.hide_scale_and_visibility_attributes()

        self._offset_control(control)

        space.create_xform_group(control.get())

        return control.get()

    def _create_shoulder_control(self):
        control = self._create_control()
        control.set_curve_type('cube')
        control.hide_scale_and_visibility_attributes()

        space.MatchSpace(self.joints[0], control.get()).translation()
        cmds.pointConstraint(control.get(), self.joints[0], mo=True)

        space.create_xform_group(control.get())

        return control.get()

    def _offset_control(self, control):
        offset = cmds.group(em=True)
        match = space.MatchSpace(self.joints[-1], offset)
        match.translation_rotation()

        cmds.move(self.control_offset, 0, 0, offset, os=True, wd=True, r=True)

        match = space.MatchSpace(offset, control.get())
        match.translation()

        cmds.delete(offset)

    def _create_ik(self, control):
        handle = space.IkHandle(self._get_name())
        handle.set_start_joint(self.joints[0])
        handle.set_end_joint(self.joints[-1])
        handle = handle.create()

        cmds.pointConstraint(control, handle)

        cmds.parent(handle, control)
        cmds.hide(handle)

    def set_control_offset(self, value):
        self.control_offset = value

    def create(self):
        control = self._create_top_control()
        self._create_shoulder_control()

        self._create_ik(control)

        rig_line = rigs_util.RiggedLine(control, self.joints[-1], self._get_name()).create()
        cmds.parent(rig_line, self.control_group)


class QuadFootRollRig(rigs.FootRollRig):

    def __init__(self, description, side):
        super(QuadFootRollRig, self).__init__(description, side)

        self.ball_attrtribute = None

    def _define_joints(self):
        index_list = self.defined_joints

        if not index_list:
            index_list = [0, 2, 1, 3, 4, 5]

        self.ankle_index = index_list[0]
        self.heel_index = index_list[1]
        self.ball_index = index_list[2]
        self.toe_index = index_list[3]
        self.yawIn_index = index_list[4]
        self.yawOut_index = index_list[5]

        self.ankle = self.ik_chain[self.ankle_index]
        self.heel = self.ik_chain[self.heel_index]
        self.ball = self.ik_chain[self.ball_index]
        self.toe = self.ik_chain[self.toe_index]
        self.yawIn = self.ik_chain[self.yawIn_index]
        self.yawOut = self.ik_chain[self.yawOut_index]

    def _create_roll_attributes(self):
        attribute_control = self._get_attribute_control()

        cmds.addAttr(attribute_control, ln='heelRoll', at='double', k=True)
        cmds.addAttr(attribute_control, ln='ballRoll', at='double', k=True)
        cmds.addAttr(attribute_control, ln='toeRoll', at='double', k=True)

        cmds.addAttr(attribute_control, ln='yawIn', at='double', k=True)
        cmds.addAttr(attribute_control, ln='yawOut', at='double', k=True)

        cmds.addAttr(attribute_control, ln='bankIn', at='double', k=True)
        cmds.addAttr(attribute_control, ln='bankOut', at='double', k=True)

    def _create_yawout_roll(self, parent, name, scale=1):
        control, xform, driver = self._create_pivot_control(self.yawOut, name, scale=scale)

        cmds.parent(xform, parent)

        attribute_control = self._get_attribute_control()

        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.side_roll_axis), cd='%s.%s' % (attribute_control, name),
                               driverValue=0, value=0, itt='spline', ott='spline')
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.side_roll_axis), cd='%s.%s' % (attribute_control, name),
                               driverValue=10, value=-45, itt='spline', ott='spline')

        cmds.setInfinity('%s.rotate%s' % (driver, self.side_roll_axis), preInfinite='linear')
        cmds.setInfinity('%s.rotate%s' % (driver, self.side_roll_axis), postInfinite='linear')

        return control

    def _create_yawin_roll(self, parent, name, scale=1):
        control, xform, driver = self._create_pivot_control(self.yawIn, name, scale=scale)

        cmds.parent(xform, parent)

        attribute_control = self._get_attribute_control()

        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.side_roll_axis), cd='%s.%s' % (attribute_control, name),
                               driverValue=0, value=0, itt='spline', ott='spline')
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.side_roll_axis), cd='%s.%s' % (attribute_control, name),
                               driverValue=-10, value=-45, itt='spline', ott='spline')

        cmds.setInfinity('%s.rotate%s' % (driver, self.side_roll_axis), preInfinite='linear')
        cmds.setInfinity('%s.rotate%s' % (driver, self.side_roll_axis), postInfinite='linear')

        return control

    def _create_pivot_groups(self):
        heel_pivot = self._create_pivot('heel', self.heel, self.control_group)
        ball_pivot = self._create_pivot('ball', self.ball, heel_pivot)
        toe_pivot = self._create_pivot('toe', self.toe, ball_pivot)

        toe_roll = self._create_toe_roll(toe_pivot)
        heel_roll = self._create_heel_roll(toe_roll)
        yawin_roll = self._create_yawin_roll(heel_roll, 'yawIn')
        yawout_roll = self._create_yawout_roll(yawin_roll, 'yawOut')
        bankin_roll = self._create_yawin_roll(yawout_roll, 'bankIn')
        bankout_roll = self._create_yawout_roll(bankin_roll, 'bankOut')
        ball_roll = self._create_ball_roll(bankout_roll)

        toe_control, toe_control_xform = self._create_toe_rotate_control()
        toe_fk_control, toe_fk_control_xform = self._create_toe_fk_rotate_control()

        self._create_ik()

        cmds.parent(toe_control_xform, bankout_roll)

        follow_toe_control = cmds.group(em=True, n='follow_%s' % toe_control)
        space.MatchSpace(toe_control, follow_toe_control).translation_rotation()
        xform_follow = space.create_xform_group(follow_toe_control)

        cmds.parent(xform_follow, yawout_roll)
        attr.connect_rotate(toe_control, follow_toe_control)

        cmds.parentConstraint(ball_roll, self.roll_control_xform, mo=True)

        cmds.parentConstraint(toe_control, self.ball_handle, mo=True)
        cmds.parentConstraint(ball_roll, self.ankle_handle, mo=True)

        return [ball_pivot, toe_fk_control_xform]

    def set_index_order(self, index_list):
        self.defined_joints = index_list


class QuadBackFootRollRig(QuadFootRollRig):

    def __init__(self, name, side):
        super(QuadBackFootRollRig, self).__init__(name, side)

        self.add_bank = True
        self.right_side_fix = False
        self.right_side_fix_axis = ['X']

    def _fix_right_side_orient(self, control):

        if not self.right_side_fix:
            return

        if not self.side == 'R':
            return

        xform_locator = cmds.spaceLocator()[0]

        match = space.MatchSpace(control, xform_locator)
        match.translation_rotation()

        spacer = space.create_xform_group(xform_locator)

        for letter in self.right_side_fix_axis:
            cmds.setAttr('%s.rotate%s' % (xform_locator, letter.upper()), 180)

        match = space.MatchSpace(xform_locator, control)
        match.translation_rotation()

        cmds.delete(spacer)

    def _create_toe_roll(self, parent, name='toeRoll', scale=1):

        control, xform, driver = self._create_pivot_control(self.toe, name, scale=scale)

        cmds.parent(xform, parent)

        attribute_control = self._get_attribute_control()

        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.forward_roll_axis), cd='%s.%s' % (attribute_control, name),
                               driverValue=0, value=0, itt='spline', ott='spline')
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.forward_roll_axis), cd='%s.%s' % (attribute_control, name),
                               driverValue=10, value=45, itt='spline', ott='spline')
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.forward_roll_axis), cd='%s.%s' % (attribute_control, name),
                               driverValue=-10, value=-45, itt='spline', ott='spline')

        cmds.setInfinity('%s.rotate%s' % (driver, self.forward_roll_axis), postInfinite='linear')
        cmds.setInfinity('%s.rotate%s' % (driver, self.forward_roll_axis), preInfinite='linear')

        return control

    def _create_heel_roll(self, parent, name='heelRoll', scale=1):
        control, xform, driver = self._create_pivot_control(self.heel, name, scale=scale)

        cmds.parent(xform, parent)

        attribute_control = self._get_attribute_control()

        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.forward_roll_axis), cd='%s.%s' % (attribute_control, name),
                               driverValue=0, value=0, itt='spline', ott='spline')
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.forward_roll_axis), cd='%s.%s' % (attribute_control, name),
                               driverValue=10, value=45, itt='spline', ott='spline')
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.forward_roll_axis), cd='%s.%s' % (attribute_control, name),
                               driverValue=-10, value=-45, itt='spline', ott='spline')
        cmds.setInfinity('%s.rotate%s' % (driver, self.forward_roll_axis), preInfinite='linear')
        cmds.setInfinity('%s.rotate%s' % (driver, self.forward_roll_axis), postInfinite='linear')

        return control

    def _create_ball_roll(self, parent):

        control, xform, driver = self._create_pivot_control(self.ball, 'ball')

        cmds.parent(xform, parent)

        attribute_control = self._get_attribute_control()

        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.forward_roll_axis), cd='%s.ballRoll' % attribute_control,
                               driverValue=0, value=0, itt='spline', ott='spline')
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.forward_roll_axis), cd='%s.ballRoll' % attribute_control,
                               driverValue=10, value=45, itt='spline', ott='spline')
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.forward_roll_axis), cd='%s.ballRoll' % attribute_control,
                               driverValue=-10, value=-45, itt='spline', ott='spline')

        cmds.setInfinity('%s.rotate%s' % (driver, self.forward_roll_axis), postInfinite='linear')
        cmds.setInfinity('%s.rotate%s' % (driver, self.forward_roll_axis), preInfinite='linear')

        return control

    def _create_roll_control(self, transform):

        roll_control = self._create_control('roll')
        roll_control.set_curve_type('square')

        self.roll_control = roll_control

        roll_control.scale_shape(.8, .8, .8)

        xform_group = space.create_xform_group(roll_control.get())

        roll_control.hide_scale_and_visibility_attributes()
        roll_control.hide_rotate_attributes()

        match = space.MatchSpace(transform, xform_group)
        match.translation_rotation()

        if self.right_side_fix and self.side == 'R':
            self._fix_right_side_orient(xform_group)

        self.roll_control_xform = xform_group

        return roll_control

    def _define_joints(self):

        index_list = self.defined_joints

        if not index_list:
            index_list = [0, 1, 2, 3, 4, 5]

        self.ankle_index = index_list[0]
        self.heel_index = index_list[1]
        self.ball_index = index_list[2]
        self.toe_index = index_list[3]
        self.yawIn_index = index_list[4]
        self.yawOut_index = index_list[5]

        self.ankle = self.ik_chain[self.ankle_index]
        self.heel = self.ik_chain[self.heel_index]
        self.ball = self.ik_chain[self.ball_index]
        self.toe = self.ik_chain[self.toe_index]
        self.yawIn = self.ik_chain[self.yawIn_index]
        self.yawOut = self.ik_chain[self.yawOut_index]

    def _create_roll_attributes(self):

        attribute_control = self._get_attribute_control()

        attr.create_title(attribute_control, 'roll')

        cmds.addAttr(attribute_control, ln='ballRoll', at='double', k=True)
        cmds.addAttr(attribute_control, ln='toeRoll', at='double', k=True)
        cmds.addAttr(attribute_control, ln='heelRoll', at='double', k=True)

        cmds.addAttr(attribute_control, ln='yawIn', at='double', k=True)
        cmds.addAttr(attribute_control, ln='yawOut', at='double', k=True)

        if self.add_bank:
            attr.create_title(attribute_control, 'bank')

            cmds.addAttr(attribute_control, ln='bankIn', at='double', k=True)
            cmds.addAttr(attribute_control, ln='bankOut', at='double', k=True)

            cmds.addAttr(attribute_control, ln='bankForward', at='double', k=True)
            cmds.addAttr(attribute_control, ln='bankBack', at='double', k=True)

    def _create_ik(self):
        self.ankle_handle = self._create_ik_handle('ankle', self.ankle, self.toe)
        cmds.parent(self.ankle_handle, self.setup_group)

    def _create_pivot_groups(self):

        attribute_control = self._get_attribute_control()

        self._create_ik()

        attr.create_title(attribute_control, 'pivot')

        ankle_pivot = self._create_pivot('ankle', self.ankle, self.control_group)
        heel_pivot = self._create_pivot('heel', self.heel, ankle_pivot)
        ball_pivot = self._create_pivot('ball', self.ball, heel_pivot)
        toe_pivot = self._create_pivot('toe', self.toe, ball_pivot)

        toe_roll = self._create_toe_roll(toe_pivot)
        heel_roll = self._create_heel_roll(toe_roll)
        yawin_roll = self._create_yawin_roll(heel_roll, 'yawIn')
        yawout_roll = self._create_yawout_roll(yawin_roll, 'yawOut')
        ball_roll = self._create_ball_roll(yawout_roll)

        if self.add_bank:
            bankin_roll = self._create_yawin_roll(ball_roll, 'bankIn', scale=.5)
            bankout_roll = self._create_yawout_roll(bankin_roll, 'bankOut', scale=.5)
            bankforward_roll = self._create_toe_roll(bankout_roll, 'bankForward', scale=.5)
            bankback_roll = self._create_heel_roll(bankforward_roll, 'bankBack', scale=.5)

            space.create_follow_group(bankback_roll, self.roll_control_xform)
            cmds.parentConstraint(bankback_roll, self.ankle_handle, mo=True)

        if not self.add_bank:
            cmds.parentConstraint(ball_roll, self.roll_control_xform, mo=True)
            cmds.parentConstraint(ball_roll, self.ankle_handle, mo=True)

    def set_add_bank(self, bool_value):
        self.add_bank = bool_value

    def set_right_side_fix(self, bool_value):
        self.right_side_fix = bool_value

    def create(self):
        super(rigs.FootRollRig, self).create()

        self._define_joints()

        self._create_roll_attributes()

        self._create_pivot_groups()
