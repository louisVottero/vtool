# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

import util

import vtool.util

if vtool.util.is_in_maya():
    import maya.cmds as cmds
    
import core
import attr
import space
import anim
import curve
import geo
import deform
import rigs
    


#--- Body

class IkQuadrupedBackLegRig(rigs.IkAppendageRig):
    
    def __init__(self, description, side):
        super(IkQuadrupedBackLegRig, self).__init__(description, side)
        
        self.offset_control_to_locator = False
    
    def _duplicate_joints(self):
        
        super(rigs.IkAppendageRig, self)._duplicate_joints()
        
        duplicate = util.DuplicateHierarchy(self.joints[0])
        duplicate.stop_at(self.joints[-1])
        duplicate.replace('joint', 'ik')
        self.ik_chain = duplicate.create()
        
        ik_group = self._create_group()
        
        cmds.parent(self.ik_chain[0], ik_group)
        cmds.parent(ik_group, self.setup_group)
        
        self._create_offset_chain(ik_group)
        
        for inc in range(0, len(self.offset_chain)):
            
            cmds.parentConstraint(self.offset_chain[inc], self.buffer_joints[inc], mo = True)
            util.connect_scale(self.offset_chain[inc], self.buffer_joints[inc])
            
            cmds.connectAttr('%s.scaleX' % self.ik_chain[inc], 
                             '%s.scaleX' % self.offset_chain[inc])
        
        cmds.parentConstraint(self.ik_chain[-1], self.buffer_joints[-1], mo = True)
        util.connect_scale(self.offset_chain[-1], self.buffer_joints[-1])
        
        cmds.parentConstraint(self.ik_chain[0], self.offset_chain[0], mo = True)
    
    def _create_offset_chain(self, parent = None):
        
        if not parent:
            parent = self.setup_group
        
        duplicate = util.DuplicateHierarchy(self.joints[0])
        duplicate.stop_at(self.joints[-1])
        duplicate.replace('joint', 'offset')        
        self.offset_chain = duplicate.create()
        
        #cmds.parent(self.offset_chain[0], self.ik_chain[0])
        
        duplicate = util.DuplicateHierarchy(self.offset_chain[-2])
        duplicate.replace('offset', 'sway')
        self.lower_offset_chain = duplicate.create()
        
        cmds.parent(self.lower_offset_chain[1], self.offset_chain[-2])
        cmds.parent(self.lower_offset_chain[0], self.lower_offset_chain[1])
        cmds.makeIdentity(self.lower_offset_chain, apply = True, t = 1, r = 1, s = 1, n = 0, jointOrient = True)
        cmds.parent(self.lower_offset_chain[1], self.setup_group)
        self.lower_offset_chain.reverse()
        
        cmds.connectAttr('%s.scaleX' % self.offset_chain[-2], '%s.scaleX' % self.lower_offset_chain[0])
        
        cmds.delete(self.offset_chain[-1])
        self.offset_chain.pop(-1)
        
        cmds.orientConstraint(self.lower_offset_chain[0], self.offset_chain[-1])
        
    def _create_offset_control(self):
        
        
        if not self.offset_control_to_locator:
            control = self._create_control(description = 'offset')
            control.hide_scale_and_visibility_attributes()
            control.scale_shape(2, 2, 2)
            control.set_curve_type('square')
            
            self.offset_control = control.get()
            
            match = util.MatchSpace(self.lower_offset_chain[1], self.offset_control)
            match.rotation()

            match = util.MatchSpace(self.lower_offset_chain[0], self.offset_control)
            match.translation()
        
        if self.offset_control_to_locator:
            self.offset_control = cmds.spaceLocator(n = 'locator_%s' % self._get_name('offset'))[0]
            
            match = util.MatchSpace(self.lower_offset_chain[0], self.offset_control)
            match.translation()
            cmds.hide(self.offset_control)
        
        cmds.parentConstraint(self.offset_control, self.lower_offset_chain[0], mo = True)

        xform_group = util.create_xform_group(self.offset_control)
        driver_group = util.create_xform_group(self.offset_control, 'driver')
        
        util.create_title(self.btm_control, 'OFFSET_ANKLE')
                
        offset = util.MayaNumberVariable('offsetAnkle')
        
        offset.create(self.btm_control)
        offset.connect_out('%s.rotateZ' % driver_group)
        
        follow_group = util.create_follow_group(self.ik_chain[-2], xform_group)
        
        scale_constraint = cmds.scaleConstraint(self.ik_chain[-2], follow_group)[0]
        
        util.scale_constraint_to_local(scale_constraint)
                
        cmds.parent(follow_group, self.top_control)
        
        if not self.offset_control_to_locator:
            control.hide_translate_attributes()
        
        return self.offset_control
    
    def _rig_offset_chain(self):
        
        ik_handle = util.IkHandle( self._get_name('offset_top') )
        
        ik_handle.set_start_joint( self.offset_chain[0] )
        ik_handle.set_end_joint( self.offset_chain[-1] )
        ik_handle.set_solver(ik_handle.solver_rp)
        ik_handle = ik_handle.create()

        cmds.parent(ik_handle, self.lower_offset_chain[-1])

        ik_handle_btm = util.IkHandle( self._get_name('offset_btm'))
        ik_handle_btm.set_start_joint(self.lower_offset_chain[0])
        ik_handle_btm.set_end_joint(self.lower_offset_chain[-1])
        ik_handle_btm.set_solver(ik_handle_btm.solver_sc)
        ik_handle_btm = ik_handle_btm.create()
        
        follow = util.create_follow_group( self.offset_control, ik_handle_btm)
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
        
        sub_control = util.Control( self._get_control_name(sub = True) )
        sub_control.color( util.get_color_of_side( self.side , True)  )
        if self.control_shape:
            sub_control.set_curve_type(self.control_shape)
        
        sub_control.scale_shape(.75, .75, .75)
        
        if self.current_increment == 0:
            sub_control.set_curve_type('cube')
        
        if self.current_increment == 1:
            other_sub_control = util.Control( self._get_control_name('reverse', sub = True))
            other_sub_control.color( util.get_color_of_side( self.side, True ) )
        
            if self.control_shape:
                other_sub_control.set_curve_type(self.control_shape)
            
            other_sub_control.scale_shape(2, 2, 2)
            
            control = self.controls[-1]
            other_sub = other_sub_control.get()
            
            if self.mid_control_joint:
                util.MatchSpace(self.mid_control_joint, other_sub).translation()
                util.MatchSpace(control, other_sub).rotation()
            
            if not self.mid_control_joint:
                util.MatchSpace(control, other_sub).translation_rotation()
            
            #cmds.parent(other_sub,  )
            
            xform = util.create_xform_group(other_sub_control.get())
                
            cmds.parent(xform, self.controls[-2])
            parent = cmds.listRelatives(self.sub_controls[-1], p = True)[0]
            xform = cmds.listRelatives(parent, p = True)[0]
            
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
        
        util.create_xform_group(control.get())
        
        return control.get()
    
    
    
    def _create_shoulder_control(self):
        control = self._create_control()
        control.set_curve_type('cube')
        control.hide_scale_and_visibility_attributes()
        
        util.MatchSpace(self.joints[0], control.get()).translation()
        cmds.pointConstraint(control.get(), self.joints[0], mo = True)
        
        util.create_xform_group(control.get())
        
        return control.get()
    
    def _offset_control(self, control ):
        
        offset = cmds.group(em = True)
        match = util.MatchSpace(self.joints[-1], offset)
        match.translation_rotation()
        
        cmds.move(self.control_offset, 0,0 , offset, os = True, wd = True, r = True)
        
        match = util.MatchSpace(offset, control.get())
        match.translation()
        
        cmds.delete(offset)
    
    def _create_ik(self, control):
        
        handle = util.IkHandle(self._get_name())
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
        
        rig_line = util.RiggedLine(control, self.joints[-1], self._get_name()).create()
        cmds.parent(rig_line, self.control_group) 


class QuadFootRollRig(rigs.FootRollRig):
    
    def __init__(self, description, side):
        super(QuadFootRollRig, self).__init__(description, side)
        
        self.ball_attrtribute = None
    
    def _define_joints(self):
        
        index_list = self.defined_joints
        
        if not index_list:
            index_list = [0,2,1,3,4,5]
        
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
        
        cmds.addAttr(attribute_control, ln = 'heelRoll', at = 'double', k = True)
        cmds.addAttr(attribute_control, ln = 'ballRoll', at = 'double', k = True)
        cmds.addAttr(attribute_control, ln = 'toeRoll', at = 'double', k = True)
        
        cmds.addAttr(attribute_control, ln = 'yawIn', at = 'double', k = True)
        cmds.addAttr(attribute_control, ln = 'yawOut', at = 'double', k = True)
        
        cmds.addAttr(attribute_control, ln = 'bankIn', at = 'double', k = True)
        cmds.addAttr(attribute_control, ln = 'bankOut', at = 'double', k = True)
        
    def _create_yawout_roll(self, parent, name, scale = 1):
        
        control, xform, driver = self._create_pivot_control(self.yawOut, name, scale = scale)

        cmds.parent(xform, parent)
        
        attribute_control = self._get_attribute_control()
        
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.side_roll_axis),cd = '%s.%s' % (attribute_control, name), driverValue = 0, value = 0, itt = 'spline', ott = 'spline')
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.side_roll_axis),cd = '%s.%s' % (attribute_control, name), driverValue = 10, value = -45, itt = 'spline', ott = 'spline')
        
        cmds.setInfinity('%s.rotate%s' % (driver, self.side_roll_axis), preInfinite = 'linear')
        cmds.setInfinity('%s.rotate%s' % (driver, self.side_roll_axis), postInfinite = 'linear')
                
        return control
        
    def _create_yawin_roll(self, parent, name, scale = 1):
        
        control, xform, driver = self._create_pivot_control(self.yawIn, name, scale = scale)

        cmds.parent(xform, parent)
        
        attribute_control = self._get_attribute_control()
        
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.side_roll_axis),cd = '%s.%s' % (attribute_control, name), driverValue = 0, value = 0, itt = 'spline', ott = 'spline')
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.side_roll_axis),cd = '%s.%s' % (attribute_control, name), driverValue = -10, value = -45, itt = 'spline', ott = 'spline')
        
        cmds.setInfinity('%s.rotate%s' % (driver, self.side_roll_axis), preInfinite = 'linear')
        cmds.setInfinity('%s.rotate%s' % (driver, self.side_roll_axis), postInfinite = 'linear')
                
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
        
        follow_toe_control = cmds.group(em = True, n = 'follow_%s' % toe_control)
        util.MatchSpace(toe_control, follow_toe_control).translation_rotation()
        xform_follow = util.create_xform_group(follow_toe_control)
        
        cmds.parent(xform_follow, yawout_roll)
        util.connect_rotate(toe_control, follow_toe_control)
        
        cmds.parentConstraint(ball_roll, self.roll_control_xform, mo = True)
        
        cmds.parentConstraint(toe_control, self.ball_handle, mo = True)
        cmds.parentConstraint(ball_roll, self.ankle_handle, mo = True)
        
        
        return [ball_pivot, toe_fk_control_xform]
                
    def set_index_order(self,index_list):
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
        
        match = util.MatchSpace(control, xform_locator)
        match.translation_rotation()
        
        spacer = util.create_xform_group(xform_locator)
        
        for letter in self.right_side_fix_axis:
        
            cmds.setAttr('%s.rotate%s' % (xform_locator, letter.upper()), 180)
        
        match = util.MatchSpace(xform_locator, control)
        match.translation_rotation()
        
        cmds.delete(spacer)
    
    def _create_toe_roll(self, parent, name = 'toeRoll', scale = 1):
        
        control, xform, driver = self._create_pivot_control(self.toe, name, scale = scale)
        
        cmds.parent(xform, parent)
        
        attribute_control = self._get_attribute_control()
        
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.forward_roll_axis),cd = '%s.%s' % (attribute_control,name), driverValue = 0, value = 0, itt = 'spline', ott = 'spline' )
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.forward_roll_axis),cd = '%s.%s' % (attribute_control,name), driverValue = 10, value = 45, itt = 'spline', ott = 'spline')
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.forward_roll_axis),cd = '%s.%s' % (attribute_control,name), driverValue = -10, value = -45, itt = 'spline', ott = 'spline')
        
        cmds.setInfinity('%s.rotate%s' % (driver, self.forward_roll_axis), postInfinite = 'linear')
        cmds.setInfinity('%s.rotate%s' % (driver, self.forward_roll_axis), preInfinite = 'linear')
        
        return control
    
    def _create_heel_roll(self, parent, name = 'heelRoll', scale = 1):
        control, xform, driver = self._create_pivot_control(self.heel, name, scale = scale)
        
        cmds.parent(xform, parent)
        
        attribute_control = self._get_attribute_control()
        
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.forward_roll_axis),cd = '%s.%s' % (attribute_control,name), driverValue = 0, value = 0, itt = 'spline', ott = 'spline' )
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.forward_roll_axis),cd = '%s.%s' % (attribute_control,name), driverValue = 10, value = 45, itt = 'spline', ott = 'spline')
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.forward_roll_axis),cd = '%s.%s' % (attribute_control,name), driverValue = -10, value = -45, itt = 'spline', ott = 'spline')
        cmds.setInfinity('%s.rotate%s' % (driver, self.forward_roll_axis), preInfinite = 'linear')
        cmds.setInfinity('%s.rotate%s' % (driver, self.forward_roll_axis), postInfinite = 'linear')
        
        return control
    
    def _create_ball_roll(self, parent):

        control, xform, driver = self._create_pivot_control(self.ball, 'ball')
                
        cmds.parent(xform, parent)
        
        attribute_control = self._get_attribute_control()
        
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.forward_roll_axis),cd = '%s.ballRoll' % attribute_control, driverValue = 0, value = 0, itt = 'spline', ott = 'spline')        
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.forward_roll_axis),cd = '%s.ballRoll' % attribute_control, driverValue = 10, value = 45, itt = 'spline', ott = 'spline')
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.forward_roll_axis),cd = '%s.ballRoll' % attribute_control, driverValue = -10, value = -45, itt = 'spline', ott = 'spline')
        #cmds.setDrivenKeyframe('%s.rotateX' % driver,cd = '%s.ballRoll' % attribute_control, driverValue = 20, value = 0, itt = 'spline', ott = 'spline')
        cmds.setInfinity('%s.rotate%s' % (driver, self.forward_roll_axis), postInfinite = 'linear')
        cmds.setInfinity('%s.rotate%s' % (driver, self.forward_roll_axis), preInfinite = 'linear')
        
        return control
    
    def _create_roll_control(self, transform):
        
        roll_control = self._create_control('roll') 
        roll_control.set_curve_type('square')
        
        self.roll_control = roll_control
        
        roll_control.scale_shape(.8,.8,.8)
        
        xform_group = util.create_xform_group(roll_control.get())
        
        roll_control.hide_scale_and_visibility_attributes()
        roll_control.hide_rotate_attributes()
        
        
        match = util.MatchSpace( transform, xform_group )
        match.translation_rotation()
        
        if self.right_side_fix and self.side == 'R':
            self._fix_right_side_orient(xform_group)

        #cmds.parentConstraint(roll_control.get(), transform)
        
        self.roll_control_xform = xform_group 
        
        return roll_control
    
    def _define_joints(self):
        
        index_list = self.defined_joints
        
        if not index_list:
            index_list = [0,1,2,3,4,5]
        
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
        
        util.create_title(attribute_control, 'roll')
        
        cmds.addAttr(attribute_control, ln = 'ballRoll', at = 'double', k = True)
        cmds.addAttr(attribute_control, ln = 'toeRoll', at = 'double', k = True)
        cmds.addAttr(attribute_control, ln = 'heelRoll', at = 'double', k = True)
        
        cmds.addAttr(attribute_control, ln = 'yawIn', at = 'double', k = True)
        cmds.addAttr(attribute_control, ln = 'yawOut', at = 'double', k = True)
        
        if self.add_bank:
            
            util.create_title(attribute_control, 'bank')
            
            cmds.addAttr(attribute_control, ln = 'bankIn', at = 'double', k = True)
            cmds.addAttr(attribute_control, ln = 'bankOut', at = 'double', k = True)
        
            cmds.addAttr(attribute_control, ln = 'bankForward', at = 'double', k = True)
            cmds.addAttr(attribute_control, ln = 'bankBack', at = 'double', k = True)
    
    def _create_ik(self):
        self.ankle_handle = self._create_ik_handle( 'ankle', self.ankle, self.toe)
        cmds.parent( self.ankle_handle, self.setup_group )
    
    def _create_pivot_groups(self):

        attribute_control = self._get_attribute_control()

        self._create_ik() 
        
        util.create_title(attribute_control, 'pivot')
        
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
            
            bankin_roll = self._create_yawin_roll(ball_roll, 'bankIn', scale = .5)
            bankout_roll = self._create_yawout_roll(bankin_roll, 'bankOut', scale = .5)
            bankforward_roll = self._create_toe_roll(bankout_roll, 'bankForward', scale = .5)
            bankback_roll = self._create_heel_roll(bankforward_roll, 'bankBack', scale = .5)
            
            util.create_follow_group(bankback_roll,self.roll_control_xform)
            #cmds.parentConstraint(bankback_roll, self.roll_control_xform, mo = True)
            cmds.parentConstraint(bankback_roll, self.ankle_handle, mo = True)
        
        if not self.add_bank:
        
            cmds.parentConstraint(ball_roll, self.roll_control_xform, mo = True)
            cmds.parentConstraint(ball_roll, self.ankle_handle, mo = True)
                    
    def set_add_bank(self, bool_value):
        self.add_bank = bool_value
                 
    def set_right_side_fix(self, bool_value):
        self.right_side_fix = bool_value
                    
    def create(self):
        super(rigs.FootRollRig,self).create()
        
        self._define_joints()
        
        self._create_roll_attributes()
        
        self._create_pivot_groups()


#--- face

class FaceFollowCurveRig(rigs.CurveRig):
    def __init__(self, description, side):
        super(FaceFollowCurveRig, self).__init__(description, side)
        
        self.controls = []
        self.drivers = []
        self.clusters = []
        self.local_controls = []
        
        self.wire_falloff = 20
        
        self.create_joints = 0
        
        self.mesh = None
        self.create_follow = False

    def _rebuild_curve(self, curve, description = None, spans = 4, delete_cvs = False):
        
        if self.create_follow:
            
            follow_curve, cluster_curve = self._rebuild_with_follow(curve, description, spans, delete_cvs)
            
            return follow_curve, cluster_curve
                
        rebuilt_curve = cmds.rebuildCurve( curve, 
                                                 constructionHistory = False,
                                                 replaceOriginal = False,
                                                 rebuildType = 0,
                                                 endKnots = 1,
                                                 keepRange = 0,
                                                 keepControlPoints = 0, 
                                                 keepEndPoints = 1, 
                                                 keepTangents = 0, 
                                                 spans = spans,
                                                 degree = 3 )[0]
        
        if delete_cvs:
            cvs = cmds.ls('%s.cv[*]' % rebuilt_curve, flatten = True)
            cmds.delete(cvs[1], cvs[-2])
        
        new_curve = cmds.rename(rebuilt_curve, 'curve_%s' % self._get_name(description))
        
        
        cluster_curve = new_curve
        follow_curve = None
        
        cmds.parent(cluster_curve, self.setup_group)
        
        return follow_curve, cluster_curve
        
    def _rebuild_with_follow(self, curve, description, spans, delete_cvs):
        rebuilt_curve, node = cmds.rebuildCurve( curve, 
                                           constructionHistory = True,
                                           replaceOriginal = False,
                                           rebuildType = 0,
                                           endKnots = 1,
                                           keepRange = 0,
                                           keepControlPoints = 0, 
                                           keepEndPoints = 1, 
                                           keepTangents = 0, 
                                           spans = spans,
                                           degree =3)
        
        #cmds.delete('%s.cv[1]' % rebuilt_curve)
        
        if delete_cvs:
            cvs = cmds.ls('%s.cv[*]' % rebuilt_curve, flatten = True)
            cmds.delete(cvs[1], cvs[-2])
        
        new_curve = cmds.duplicate(rebuilt_curve, n = 'curve_%s' % self._get_name(description))[0]
        
        cmds.blendShape(rebuilt_curve, new_curve, w = [0,1])
        
        follow_curve = rebuilt_curve
        cluster_curve = new_curve
        
        cmds.parent(follow_curve, self.setup_group)
        cmds.parent(cluster_curve, self.setup_group)
        
        return follow_curve, cluster_curve

    def _create_inc_control(self, follow_curve, cluster_curve, inc, description = None, center_tolerance = 0.001):
        control = self._create_control(description)
        
        control.rotate_shape(90, 0, 0)
        control.hide_scale_attributes()
        
        cluster, handle = util.create_cluster('%s.cv[%s]' % (cluster_curve, inc), self._get_name())
        self.clusters.append(handle)
        
        match = util.MatchSpace(handle, control.get())
        match.translation_to_rotate_pivot()
        
        control_name = control.get()
        

        if description:
        
            side = control.color_respect_side(center_tolerance = center_tolerance)
            
            if side != 'C':
                control_name = cmds.rename(control.get(), util.inc_name(control.get()[0:-1] + side))
        
        xform = util.create_xform_group(control_name)
        driver = util.create_xform_group(control_name, 'driver')
        
        bind_pre = util.create_cluster_bindpre(cluster, handle)
        
        local_group, xform_group = util.constrain_local(control_name, handle, parent = True)
        
        local_driver = util.create_xform_group(local_group, 'driver')
        util.connect_translate(driver, local_driver)
        util.connect_translate(xform, xform_group)
        
        cmds.parent(bind_pre, xform_group)
        
        util.attach_to_curve(xform, follow_curve)
        
        cmds.parent(xform_group, self.setup_group)
        
        self.local_controls.append(local_group)
        self.drivers.append(driver)
        
        return control_name, driver

    def _create_controls(self, follow_curve, cluster_curve, description):
        pass

    def _create_deformation(self, deform_curve, follow_curve):
        
        
        if self.mesh:
            if not self.create_joints:
                for mesh in self.mesh:
                    wire, curve = cmds.wire( self.mesh, w = deform_curve, dds=[(0, self.wire_falloff)], gw = False, n = 'wire_%s' % deform_curve)
        
                    cmds.setAttr('%s.rotation' % wire, 0.1)
        
                cmds.blendShape(follow_curve, '%sBaseWire' % curve, w = [0,1])
                
            if self.create_joints:
                util.create_joints_on_curve(deform_curve, self.create_joints, self.description, create_controls = False)
                
    def set_wire_falloff(self, value):
        self.wire_falloff = value

    def set_mesh_to_deform(self, mesh):
        self.mesh = mesh
        
        if type(mesh) == type('') or type(mesh) == type(u''):
            self.mesh = [mesh]
            
    def set_create_joints(self, int_value):
        self.create_joints = int_value

    def set_curves(self, top_lip_curve, btm_lip_curve):
        super(MouthCurveRig, self).set_curves([top_lip_curve, btm_lip_curve])
        
    def set_create_follow(self, bool_value):
        self.create_follow = bool_value

class SingleControlFaceCurveRig(FaceFollowCurveRig):
    def __init__(self, description, side):
        super(SingleControlFaceCurveRig, self).__init__(description, side)
        
        self.attach_surface = None
        self.curve_position_percent = 0
        self.shape_name = 'pin'

    def _rebuild_curve(self, curve, description = None, spans = 6):
        
        rebuilt_curve, node = cmds.rebuildCurve( curve, 
                                           constructionHistory = True,
                                           replaceOriginal = False,
                                           rebuildType = 0,
                                           endKnots = 1,
                                           keepRange = 0,
                                           keepControlPoints = 0, 
                                           keepEndPoints = 1, 
                                           keepTangents = 0, 
                                           spans = spans,
                                           degree =3)
        
        new_curve = cmds.duplicate(rebuilt_curve, n = 'curve_%s' % self._get_name(description))[0]
        
        cmds.blendShape(rebuilt_curve, new_curve, w = [0,1])
        
        follow_curve = rebuilt_curve
        cluster_curve = new_curve
        
        cmds.parent(follow_curve, self.setup_group)
        cmds.parent(cluster_curve, self.setup_group)
        
        return follow_curve, cluster_curve        
    
    def _create_control_on_curve(self, follow_curve, percent, sub = False, description = None):
        
        position = cmds.pointOnCurve(follow_curve, top = True, pr = percent)
        
        control = self._create_control(description)
        control.set_curve_type(self.shape_name)
        control.rotate_shape(90, 0, 0)
        control.hide_scale_attributes()
        
        sub_control = None
        
        if sub:
            sub_control = self._create_control(description, True)
            sub_control.set_curve_type('cube')
            sub_control.scale_shape(.8, .8, .8)
            sub_control.hide_scale_attributes()
            
            cmds.parent(sub_control.get(), control.get())
            
            sub_control = sub_control.get()
        
        cmds.move(position[0], position[1], position[2], control.get())
        
        control_name = control.get()
        
        xform = util.create_xform_group(control_name)
        driver = util.create_xform_group(control_name, 'driver')
        
        util.attach_to_curve(xform, follow_curve)
        
        return control_name, sub_control, driver, xform
    
    def _create_full_control(self, follow_curve, cluster, description = None):
        position = cmds.xform(cluster, q = True, ws = True, rp= True)
        
        control = self._create_control(description)
        control.set_curve_type(self.shape_name)
        control.rotate_shape(90, 0, 0)
        control.hide_scale_attributes()        
    
        cmds.move(position[0], position[1], position[2], control.get())
        
        control_name = control.get()
        
        xform = util.create_xform_group(control_name)
        driver = util.create_xform_group(control_name, 'driver')
        
        util.attach_to_curve(xform, follow_curve)
        
        return control_name, driver        
    
    def _create_cluster(self, cv_deform, cv_offset, description = None, follow = True):
        
        cluster_group = cmds.group(em = True, n = util.inc_name(self._get_name(description)))
        cmds.parent(cluster_group, self.setup_group)
        
        cluster, handle = util.create_cluster(cv_deform, self._get_name(description))
        self.clusters.append(handle)
        
        bind_pre = util.create_cluster_bindpre(cluster, handle)
        
        #buffer = cmds.group(em = True, n = util.inc_name('buffer_%s' % handle))
        
        match = util.MatchSpace(handle, buffer)
        match.translation_to_rotate_pivot()
        
        cmds.parent(handle, buffer)
        cmds.parent(buffer, cluster_group)
        
        xform = util.create_xform_group(buffer)
        driver3 = util.create_xform_group(buffer, 'driver3')
        driver2 = util.create_xform_group(buffer, 'driver2')
        driver1 = util.create_xform_group(buffer, 'driver1')
        
        if self.attach_surface and follow:
            
            surface_follow = cmds.group(em = True, n = util.inc_name('surfaceFollow_%s' % handle))
            
            cmds.parent(surface_follow, xform)
        
            match = util.MatchSpace(handle, surface_follow)
            match.translation_to_rotate_pivot()
            
            cmds.pointConstraint(driver3, surface_follow, mo = True)
            cmds.geometryConstraint(self.attach_surface, surface_follow)
            
            util.connect_translate(driver3, surface_follow)
            
            cmds.pointConstraint(surface_follow, driver2, mo = True)
        
        cmds.parent(bind_pre, xform)
        
        return xform, driver3, driver1
        
    def _create_full_cluster(self, follow_curve, cluster_curve, offset_curve, description= None, follow = False):
        
        cv_deform = '%s.cv[*]' % (cluster_curve)
        cv_offset = '%s.cv[*]' % (offset_curve)
        
        xform, driver, local_driver = self._create_cluster(cv_deform, cv_offset, description, follow)
        
        
        
        return driver, local_driver, xform
        
        
    def _create_inc_cluster(self, follow_curve, cluster_curve, offset_curve, inc, description = None, follow = True):
        
        cv_deform = '%s.cv[%s]' % (cluster_curve, inc)
        cv_offset = '%s.cv[%s]' % (offset_curve, inc)
        
        xform, driver, local_driver = self._create_cluster(cv_deform, cv_offset, description, follow)
            
        return driver, local_driver
    
    def _create_clusters(self, follow_curve, deform_curve, offset_curve, description = None, follow = True):
        
        cvs = cmds.ls('%s.cv[*]' % deform_curve, flatten = True)
        count = len(cvs)
        
        drivers = []
        local_drivers = []
        
        for inc in range(0, count):
            driver, local_driver = self._create_inc_cluster(follow_curve, deform_curve, offset_curve, inc, description, follow)
            drivers.append(driver)
            local_drivers.append(local_driver)
            
        return drivers, local_drivers
    
    def _create_fade(self, start_control, drivers):
        
        reverse_drivers = list(drivers) 
        reverse_drivers.reverse()
        
        multiply_groups = {}
        
        if start_control:
            multiply_groups['side1'] = util.create_follow_fade(start_control, drivers, -1)
        
        return multiply_groups
    
    def set_attach_surface(self, surface):
        self.attach_surface = surface
        
    def set_curve_position(self, percent):
        self.curve_position_percent = percent

    def set_curve_shape(self, shape_name):
        self.curve_shape = shape_name

    def create(self):
        
        follow_curve, deform_curve = self._rebuild_curve(self.curves[0])
        
        position = self.curve_position_percent
        if position == -1:
            position = .5
        
        start_control, sub, control_driver, xform_control = self._create_control_on_curve(self.curves[0], position)
        
        if self.curve_position_percent > -1:
            drivers, drivers_local = self._create_clusters(self.curves[0],
                                                           deform_curve,
                                                           follow_curve,
                                                           follow = False)
            
            self._create_fade(start_control, drivers)
            
        if self.curve_position_percent == -1:
            driver, driver_local, xform_cluster = self._create_full_cluster(self.curves[0], 
                                                               deform_curve, 
                                                               follow_curve)
            
            util.connect_translate(start_control, driver)
            util.connect_rotate(start_control, driver)
            util.connect_scale(start_control, driver)
            
            
            util.connect_translate(control_driver, driver)
            util.connect_rotate(control_driver, driver)
            #util.connect_scale(control_driver, driver)
            
            util.connect_translate(xform_control, xform_cluster)
            
            
            control = util.Control(start_control)
            control.show_scale_attributes()
            
            
            
        
            
        
        self._create_deformation(deform_curve, follow_curve)    

class SimpleFaceCurveRig(FaceFollowCurveRig):
    def __init__(self, description, side):
        super(SimpleFaceCurveRig, self).__init__(description, side)
        
        self.attach_surface = None
    
    def _rebuild_curve(self, curve, description = None, spans = 6):
        
        rebuilt_curve, node = cmds.rebuildCurve( curve, 
                                           constructionHistory = True,
                                           replaceOriginal = False,
                                           rebuildType = 0,
                                           endKnots = 1,
                                           keepRange = 0,
                                           keepControlPoints = 0, 
                                           keepEndPoints = 1, 
                                           keepTangents = 0, 
                                           spans = spans,
                                           degree =3)
        
        new_curve = cmds.duplicate(rebuilt_curve, n = 'curve_%s' % self._get_name(description))[0]
        
        cmds.blendShape(rebuilt_curve, new_curve, w = [0,1])
        
        follow_curve = rebuilt_curve
        cluster_curve = new_curve
        
        cmds.parent(follow_curve, self.setup_group)
        cmds.parent(cluster_curve, self.setup_group)
        
        return follow_curve, cluster_curve
    
    def _create_control_on_curve(self, follow_curve, percent, sub = True, description = None):
        
        position = cmds.pointOnCurve(follow_curve, top = True, pr = percent)
        
        control = self._create_control(description)
        control.set_curve_type('cube')
        control.hide_scale_attributes()
        
        sub_control = None
        
        if sub:
            sub_control = self._create_control(description, True)
            sub_control.set_curve_type('cube')
            sub_control.scale_shape(.8, .8, .8)
            sub_control.hide_scale_attributes()
            
            cmds.parent(sub_control.get(), control.get())
            
            sub_control = sub_control.get()
        
        cmds.move(position[0], position[1], position[2], control.get())
        
        control_name = control.get()
        
        xform = util.create_xform_group(control_name)
        driver = util.create_xform_group(control_name, 'driver')
        
        util.attach_to_curve(xform, follow_curve)
        
        return control_name, sub_control, driver
    
    def _create_controls(self, curve, sub = False):
        
        control_dict = {}
        
        start_controls = self._create_control_on_curve(curve, 0, sub = sub)
        start_offset_controls = self._create_control_on_curve(curve, 0.25, sub = sub)
        
        mid_controls = self._create_control_on_curve(curve, 0.5, sub = sub)
        
        end_offset_controls = self._create_control_on_curve(curve,0.75, sub = sub)
        end_controls = self._create_control_on_curve(curve, 1, sub = sub)
        
        control_dict['start'] = start_controls
        control_dict['start_offset'] = start_offset_controls
        
        control_dict['mid'] = mid_controls
        
        control_dict['end_offset'] = end_offset_controls
        control_dict['end'] = end_controls
        
        return control_dict
    
    def _create_cluster(self, cv_deform, cv_offset, description = None, follow = True):
        
        cluster_group = cmds.group(em = True, n = util.inc_name(self._get_name(description)))
        cmds.parent(cluster_group, self.setup_group)
        
        cluster, handle = util.create_cluster(cv_deform, self._get_name(description))
        self.clusters.append(handle)
        
        bind_pre = util.create_cluster_bindpre(cluster, handle)
        
        #buffer = cmds.group(em = True, n = util.inc_name('buffer_%s' % handle))
        
        match = util.MatchSpace(handle, buffer)
        match.translation_to_rotate_pivot()
        
        cmds.parent(handle, buffer)
        cmds.parent(buffer, cluster_group)
        
        xform = util.create_xform_group(buffer)
        driver3 = util.create_xform_group(buffer, 'driver3')
        driver2 = util.create_xform_group(buffer, 'driver2')
        driver1 = util.create_xform_group(buffer, 'driver1')
        
        if self.attach_surface and follow:
            
            surface_follow = cmds.group(em = True, n = util.inc_name('surfaceFollow_%s' % handle))
            
            cmds.parent(surface_follow, xform)
        
            match = util.MatchSpace(handle, surface_follow)
            match.translation_to_rotate_pivot()
            
            cmds.pointConstraint(driver3, surface_follow, mo = True)
            cmds.geometryConstraint(self.attach_surface, surface_follow)
            
            util.connect_translate(driver3, surface_follow)
            
            cmds.pointConstraint(surface_follow, driver2, mo = True)
        
        cmds.parent(bind_pre, xform)
        
        return xform, driver3, driver1
        
    def _create_inc_cluster(self, follow_curve, cluster_curve, offset_curve, inc, description = None, follow = True):
        
        cv_deform = '%s.cv[%s]' % (cluster_curve, inc)
        cv_offset = '%s.cv[%s]' % (offset_curve, inc)
        
        xform, driver, local_driver = self._create_cluster(cv_deform, cv_offset, description, follow)
            
        return driver, local_driver
    
    def _create_clusters(self, follow_curve, deform_curve, offset_curve, description = None, follow = True):
        
        cvs = cmds.ls('%s.cv[*]' % deform_curve, flatten = True)
        count = len(cvs)
        
        drivers = []
        local_drivers = []
        
        for inc in range(0, count):
            driver, local_driver = self._create_inc_cluster(follow_curve, deform_curve, offset_curve, inc, description, follow)
            drivers.append(driver)
            local_drivers.append(local_driver)
            
        return drivers, local_drivers
    
    def _create_fade(self, start_control, mid_control, end_control, start_offset_control, end_offset_control, drivers):
        
        reverse_drivers = list(drivers) 
        reverse_drivers.reverse()
        
        multiply_groups = {}
        
        if start_control:
            multiply_groups['side1'] = util.create_follow_fade(start_control, drivers, -1)
        if end_control:
            multiply_groups['side2'] = util.create_follow_fade(end_control, reverse_drivers, -1)
        
        if mid_control:
            multiply_groups['sides'] = util.create_follow_fade(mid_control, drivers, -1)
            
        if start_offset_control:
            multiply_groups['offset1'] = util.create_follow_fade(start_offset_control, 
                                                            drivers[0:len(drivers)/2])
        
        if end_offset_control:
            multiply_groups['offset2'] = util.create_follow_fade(end_offset_control, 
                                                            drivers[len(drivers)/2:])
        
        return multiply_groups
    
    def set_attach_surface(self, surface):
        self.attach_surface = surface
    
    def create(self):
        
        follow_curve, deform_curve = self._rebuild_curve(self.curves[0])
        
        controls = self._create_controls(self.curves[0])
        
        drivers, drivers_local = self._create_clusters(self.curves[0],
                                                       deform_curve,
                                                       follow_curve,
                                                       follow = False)
        
        self._create_fade(controls['start'][0], 
                          controls['mid'][0], 
                          controls['end'][0],
                          controls['start_offset'][0],
                          controls['end_offset'][0],
                          drivers)
        
        self._create_deformation(deform_curve, follow_curve)
        
    
class MouthCurveRig(FaceFollowCurveRig):
    def __init__(self, description):
        super(MouthCurveRig, self).__init__(description, 'C')
        self.center_tolerance = 0.01
        self.control_shape = 'cube'
        self.center_fade = True
        
    def _create_controls(self, follow_curve, cluster_curve, description):
        
        cvs = cmds.ls('%s.cv[*]' % cluster_curve, flatten = True)
        count = len(cvs)
        
        controls = []
        drivers = []
        
        for inc in range(0, count):
        
            control, driver = self._create_inc_control(follow_curve, cluster_curve, inc, description, center_tolerance = self.center_tolerance)
            
            controls.append(control)
            drivers.append(driver)
            
            reverse_inc = (count - inc) -1
            
            if inc != reverse_inc:
                control, driver = self._create_inc_control(follow_curve, cluster_curve,  reverse_inc, description, center_tolerance = self.center_tolerance)
                
                controls.append(control)
                drivers.append(driver)
                
            if inc == reverse_inc:
                break
        
        front_list = drivers[2], drivers[4], drivers[6]
        back_list = drivers[3], drivers[5], drivers[6]
        
        util.create_follow_fade(controls[0], front_list)
        util.create_follow_fade(controls[1], back_list)
        
        util.create_follow_fade(drivers[0], front_list)
        util.create_follow_fade(drivers[1], back_list)
        
        if self.center_fade:
            util.create_follow_fade(controls[-1], front_list[:-1])
            util.create_follow_fade(controls[-1], back_list[:-1])
        
        return controls
        
    def _attach_corners(self, source_control, target_control, local_control, side, local_groups = []):
        
        control = self._create_control('corner', True)
        control.hide_scale_and_visibility_attributes()
        control.set_curve_type(self.control_shape)
        control.hide_rotate_attributes()
        
        control.scale_shape(.8, .8, .8)
        control.rotate_shape(90, 0, 0)
        
        match = util.MatchSpace(source_control, control.get())
        match.translation_rotation()
        
        control.color_respect_side(True)
        
        control_name = control.get()
        
        if side != 'C':
            control_name = cmds.rename(control_name, util.inc_name(control_name[0:-1] + side))
        
        cmds.parent(control_name, source_control)
        
        for local_group in local_groups:
            util.connect_translate(control_name, local_group)
        
        new_name = target_control.replace('CNT_', 'ctrl_')
        new_name = cmds.rename(target_control, new_name)
        cmds.delete( util.get_shapes( new_name ) )
        
        #cmds.parentConstraint(local_control, new_name)
        driver = cmds.listRelatives(source_control, p = True)[0]
        
        util.connect_translate(source_control, new_name)
        util.connect_rotate(source_control, new_name)
        
        util.connect_translate(driver, new_name)
        util.connect_rotate(driver, new_name)
        
        #local, xform = util.constrain_local(source_control, new_name)
        
    def set_center_tolerance(self, tolerance_value = 0.001):
        self.center_tolerance = tolerance_value
        
    def set_center_fade(self, bool_value):
        self.center_fade = bool_value
        
    def create(self):
        super(MouthCurveRig, self).create()

        follow_curve_top, cluster_curve_top = self._rebuild_curve(self.curves[0],'top')
        follow_curve_btm, cluster_curve_btm = self._rebuild_curve(self.curves[1], 'btm')
        
        controls_top = self._create_controls(self.curves[0], cluster_curve_top, 'top')
        controls_btm = self._create_controls(self.curves[1], cluster_curve_btm, 'btm')
        
        self._attach_corners(controls_top[0], controls_btm[0], self.local_controls[0], 'R', [self.local_controls[0], self.local_controls[7]])
        self._attach_corners(controls_top[1], controls_btm[1], self.local_controls[1], 'L', [self.local_controls[1], self.local_controls[8]])
        
        if follow_curve_top:
            self._create_deformation(cluster_curve_top, follow_curve_top)
        if follow_curve_btm:
            self._create_deformation(cluster_curve_btm, follow_curve_btm)
        
        
class CheekCurveRig(FaceFollowCurveRig):
    
    def _create_controls(self, follow_curve, cluster_curve, description = None):
        
        cvs = cmds.ls('%s.cv[*]' % cluster_curve, flatten = True)
        count = len(cvs)
        
        controls = []
        drivers = []
        
        for inc in range(0, count):
            control, driver = self._create_inc_control(follow_curve, cluster_curve, inc,)
            
            controls.append(control)
            drivers.append(driver)
            
        util.create_follow_fade(controls[2], [ drivers[0], drivers[1], drivers[3], drivers[4]])
        util.create_follow_fade(drivers[2], [ drivers[0], drivers[1], drivers[3], drivers[4]])
        util.create_follow_fade(controls[0], [ drivers[1], drivers[2], drivers[3] ])
        util.create_follow_fade(controls[-1], [ drivers[-2], drivers[-3], drivers[-4] ])
        
        return controls
    
    def create(self):
        super(CheekCurveRig, self).create()
        
        follow_curve_top, cluster_curve_top = self._rebuild_curve(self.curves[0], delete_cvs = True)
        
        self._create_controls(self.curves[0], cluster_curve_top)
        
        self._create_deformation(cluster_curve_top, follow_curve_top)
        

class BrowCurveRig(FaceFollowCurveRig):
    
    def __init__(self,description, side):
        super(BrowCurveRig, self).__init__(description, side)
        
        self.middle_fade = False
    
    def _create_control_on_curve(self, follow_curve, percent, sub = False, description = None):
        
        position = cmds.pointOnCurve(follow_curve, top = True, pr = percent)
        
        control = self._create_control(description)
        control.set_curve_type('square')
        control.rotate_shape(90, 0, 0)
        control.hide_scale_attributes()
        
        sub_control = None
        
        if sub:
            sub_control = self._create_control(description, True)
            sub_control.set_curve_type('cube')
            sub_control.scale_shape(.8, .8, .8)
            sub_control.hide_scale_attributes()
            
            cmds.parent(sub_control.get(), control.get())
            
            sub_control = sub_control.get()
        
        cmds.move(position[0], position[1], position[2], control.get())
        
        control_name = control.get()
        
        xform = util.create_xform_group(control_name)
        driver = util.create_xform_group(control_name, 'driver')
        
        util.attach_to_curve(xform, follow_curve)
        
        return control_name, sub_control, driver, xform
    
    def _create_controls(self, follow_curve, cluster_curve, description = None):
        
        cvs = cmds.ls('%s.cv[*]' % cluster_curve, flatten = True)
        count = len(cvs)
        
        controls = []
        drivers = []
        
        control, sub, driver, xform = self._create_control_on_curve(follow_curve, 0.5, False, description = 'all')
        controls.append(control)
        drivers.append(driver)
        
        for inc in range(0, count):
            control, driver = self._create_inc_control(follow_curve, cluster_curve, inc,)
            
            if inc == 0:
                sub_control = self._create_control('sub', True)
                sub_control.set_curve_type('cube')
                sub_control.scale_shape(.8,.8,.8)
                sub_control.hide_scale_attributes()
                
                match = util.MatchSpace(control, sub_control.get())
                match.translation_rotation()
                cmds.parent(sub_control.get(), control)
                
                constraint_editor = util.ConstraintEditor()
                constraint = constraint_editor.get_constraint(self.clusters[inc], 'pointConstraint')
                cmds.delete(constraint)
                
                local, xform = util.constrain_local(sub_control.get(), self.clusters[inc])\
                
                cmds.parent(xform, self.local_controls[-1])
                #cmds.pointConstraint(sub_control.get(), self.clusters[inc], mo = True)
            
            controls.append(control)
            drivers.append(driver)
            
        if self.middle_fade:
            util.create_follow_fade(controls[3], [drivers[1], drivers[2], drivers[4], drivers[5] ])
            
        util.create_follow_fade(controls[1], drivers[2:] )
        util.create_follow_fade(controls[-1], drivers[1:-1])
        
        for driver in drivers[1:]:
            util.connect_translate(controls[0], driver)
        
        return controls
    
    def set_middle_fade(self, bool_value):
        
        self.middle_fade = bool_value
        
    
    def create(self):
        super(BrowCurveRig, self).create()
        
        follow_curve_top, cluster_curve_top = self._rebuild_curve( self.curves[0], delete_cvs = True )
        
        self._create_controls(self.curves[0], cluster_curve_top)
        
        self._create_deformation(cluster_curve_top, follow_curve_top)
          
    
class EyeCurveRig(FaceFollowCurveRig):
    def __init__(self, description, side):
        super(EyeCurveRig, self).__init__(description, side)
        
        self.attach_surface = None
        self.top_eye_goal = None
        self.btm_eye_goal = None
        self.control_shape = 'cube'
        
    def _rebuild_curve(self, curve, description = None, spans = 21):
        
        rebuilt_curve, node = cmds.rebuildCurve( curve, 
                                           constructionHistory = True,
                                           replaceOriginal = False,
                                           rebuildType = 0,
                                           endKnots = 1,
                                           keepRange = 0,
                                           keepControlPoints = 0, 
                                           keepEndPoints = 1, 
                                           keepTangents = 0, 
                                           spans = spans,
                                           degree =3)
        
        new_curve = cmds.duplicate(rebuilt_curve, n = 'curve_%s' % self._get_name(description))[0]
        
        cmds.blendShape(rebuilt_curve, new_curve, w = [0,1])
        
        follow_curve = rebuilt_curve
        cluster_curve = new_curve
        
        cmds.parent(follow_curve, self.setup_group)
        cmds.parent(cluster_curve, self.setup_group)
        
        return follow_curve, cluster_curve
        
    def _create_cluster(self, cv_deform, cv_offset, description, follow = True):
        
        cluster_group = cmds.group(em = True, n = util.inc_name(self._get_name(description)))
        cmds.parent(cluster_group, self.setup_group)
        
        cluster, handle = util.create_cluster(cv_deform, self._get_name(description = description))
        self.clusters.append(handle)
        
        bind_pre = util.create_cluster_bindpre(cluster, handle)
        
        buffer = cmds.group(em = True, n = util.inc_name('buffer_%s' % handle))
        
        match = util.MatchSpace(handle, buffer)
        match.translation_to_rotate_pivot()
        
        cmds.parent(handle, buffer)
        cmds.parent(buffer, cluster_group)
        
        xform = util.create_xform_group(buffer)
        driver3 = util.create_xform_group(buffer, 'driver3')
        driver2 = util.create_xform_group(buffer, 'driver2')
        driver1 = util.create_xform_group(buffer, 'driver1')
        
        if self.attach_surface and follow:
            
            surface_follow = cmds.group(em = True, n = util.inc_name('surfaceFollow_%s' % handle))
            #surface_follow_offset = cmds.group(em = True, n = util.inc_name('surfaceFollowOffset_%s' % handle))
            
            cmds.parent(surface_follow, xform)
            #cmds.parent(surface_follow_offset, xform)
        
            match = util.MatchSpace(handle, surface_follow)
            match.translation_to_rotate_pivot()
            
            #match = util.MatchSpace(surface_follow, surface_follow_offset)
            #match.translation_rotation()
            
            cmds.pointConstraint(driver3, surface_follow, mo = True)
            cmds.geometryConstraint(self.attach_surface, surface_follow)
            #cmds.geometryConstraint(self.attach_surface, surface_follow_offset)
            
            util.connect_translate(driver3, surface_follow)
            
            cmds.pointConstraint(surface_follow, driver2, mo = True)
            
            
            #cmds.pointConstraint(xform, surface_follow_offset, mo = True)
        
        cmds.parent(bind_pre, xform)
        
        return xform, driver3, driver1
        
    def _create_inc_cluster(self, follow_curve, cluster_curve, offset_curve, inc, description, follow = True):
        
        cv_deform = '%s.cv[%s]' % (cluster_curve, inc)
        cv_offset = '%s.cv[%s]' % (offset_curve, inc)
        
        xform, driver, local_driver = self._create_cluster(cv_deform, cv_offset, description, follow)
            
        return driver, local_driver

    def _create_follow(self, source_drivers, target_drivers, percent = 0.6):
        
        count = len(source_drivers)
        
        for inc in range(0, count):
            
            util.connect_multiply('%s.translateX' % source_drivers[inc], '%s.translateX' % target_drivers[inc], percent, True)
            util.connect_multiply('%s.translateY' % source_drivers[inc], '%s.translateY' % target_drivers[inc], percent, True)
            util.connect_multiply('%s.translateZ' % source_drivers[inc], '%s.translateZ' % target_drivers[inc], percent, True)

        return
        
    def _create_clusters(self, follow_curve, deform_curve, offset_curve, description, follow = True):
        
        cvs = cmds.ls('%s.cv[*]' % deform_curve, flatten = True)
        count = len(cvs)
        
        drivers = []
        local_drivers = []
        
        for inc in range(0, count):
            driver, local_driver = self._create_inc_cluster(follow_curve, deform_curve, offset_curve, inc, description, follow)
            drivers.append(driver)
            local_drivers.append(local_driver)
            
        return drivers, local_drivers
        
    def _create_control_on_curve(self, follow_curve, percent, sub = True, description = None):
        
        position = cmds.pointOnCurve(follow_curve, top = True, pr = percent)
        
        control = self._create_control(description)
        control.set_curve_type(self.control_shape)
        control.hide_scale_attributes()
        
        sub_control = None
        
        if sub:
            sub_control = self._create_control(description, True)
            sub_control.set_curve_type(self.control_shape)
            sub_control.scale_shape(.8, .8, .8)
            sub_control.hide_scale_attributes()
            
            cmds.parent(sub_control.get(), control.get())
            
            sub_control = sub_control.get()
        
        cmds.move(position[0], position[1], position[2], control.get())
        
        control_name = control.get()
        
        util.create_xform_group(control_name)
        driver = util.create_xform_group(control_name, 'driver')
        
        return control_name, sub_control, driver
        
    def _create_fade(self, start_control, mid_control, end_control, drivers):
        
        reverse_drivers = list(drivers) 
        reverse_drivers.reverse()
        
        multiply_groups = {}
        
        if start_control:
            multiply_groups['side1'] = util.create_follow_fade(start_control, drivers, -1)
        if end_control:
            multiply_groups['side2'] = util.create_follow_fade(end_control, reverse_drivers, -1)
        
        if mid_control:
            multiply_groups['sides'] = util.create_follow_fade(mid_control, drivers, -1)
        
        return multiply_groups
    
    def _get_y_intersection(self, curve, vector):
        
        duplicate_curve = cmds.duplicate(curve)
        curve_line = cmds.curve( p=[(vector[0], vector[1]-100000, vector[2]), 
                                    (vector[0],vector[1]+100000, vector[2]) ], d = 1 )
        
        parameter = cmds.curveIntersect(duplicate_curve, curve_line, ud = True, d = [0, 0, 1])
        
        if parameter:
            parameter = parameter.split()
            
            parameter = float(parameter[0])
            
        if not parameter:
            parameter =  util.get_closest_parameter_on_curve(curve, vector)
            
        cmds.delete(duplicate_curve, curve_line)
        
        return parameter                
       
    def _fix_lid_fade(self, top_curve, btm_curve, multiplies):

        mid_control = multiplies[0]['source']
        
        control_position = cmds.xform(mid_control, q = True, ws = True, t = True)
        control_position_y = [0, control_position[1], 0]
        
        parameter = self._get_y_intersection(btm_curve, control_position)
        
        control_at_curve_position = cmds.pointOnCurve(btm_curve, parameter = parameter)
        control_at_curve_y = [0, control_at_curve_position[1], 0]
        
        total_distance = vtool.util.get_distance(control_position_y, control_at_curve_y)
        
        multi_count = len(multiplies)
        
        
        for inc in range(0, multi_count):
            multi = multiplies[inc]['node']
            driver = multiplies[inc]['target']
            
            driver_position = cmds.xform(driver, q = True, ws = True, t = True)
            driver_position_y = [0, driver_position[1], 0]
            
            parameter = self._get_y_intersection(btm_curve, driver_position)
            
            driver_at_curve = cmds.pointOnCurve(btm_curve, parameter = parameter)
            driver_at_curve_y = [0, driver_at_curve[1], 0]
            
            driver_distance = vtool.util.get_distance(driver_position_y, driver_at_curve_y)
            
            value = (driver_distance/total_distance)
        
            cmds.setAttr('%s.input2Y' % multi, value)

    def _create_controls(self, curve, sub = False):
        
        control_dict = {}
        
        start_controls = self._create_control_on_curve(curve, 0, sub = sub)
        
        mid_controls = self._create_control_on_curve(curve, 0.5, sub = sub)
        
        end_controls = self._create_control_on_curve(curve, 1, sub = sub)
        
        control_dict['start'] = start_controls
        control_dict['mid'] = mid_controls
        control_dict['end'] = end_controls
        
        return control_dict
    
    def set_top_eye_goal(self, curve):
        self.top_eye_goal = curve
    
    def set_btm_eye_goal(self, curve):
        self.btm_eye_goal = curve
    
    def set_attach_surface(self, surface):
        self.attach_surface = surface
    
    def create(self):
        super(EyeCurveRig, self).create()
        
        
        follow_curve_top, deform_curve_top = self._rebuild_curve(self.curves[0], 'top')
            
        follow_curve_btm, deform_curve_btm = self._rebuild_curve(self.curves[1], 'btm')
        
        if cmds.objExists(self.curves[2]):
            follow_curve_mid, deform_curve_mid = self._rebuild_curve(self.curves[2], 'mid')
        
        if cmds.objExists(self.curves[3]):
            follow_curve_top_liner, deform_curve_top_liner = self._rebuild_curve(self.curves[3], 'top_liner')
            
        follow_curve_btm_liner, deform_curve_btm_liner = self._rebuild_curve(self.curves[4], 'btm_liner')
        
        top_control, top_sub_control, top_driver = self._create_control_on_curve(self.curves[0], 0.5)
        
        drivers_top, drivers_local_top = self._create_clusters(self.curves[0], 
                                                               deform_curve_top,
                                                               follow_curve_top,
                                                               'top')
        
        btm_control, btm_sub_control, btm_driver = self._create_control_on_curve(self.curves[1], 0.5)
        corner_control1, corner_sub_control1, corner_driver1 = self._create_control_on_curve(self.curves[0], 0)
        corner_control2, corner_sub_control2, corner_driver2 = self._create_control_on_curve(self.curves[0], 1)
        
        if cmds.objExists(self.curves[3]):
            top_liner_controls = self._create_controls(self.curves[3])
            
        btm_liner_controls = self._create_controls(self.curves[4])
        
        drivers_btm, drivers_local_btm = self._create_clusters(self.curves[1], 
                                                               deform_curve_btm,
                                                               follow_curve_btm,
                                                               'btm')
        
        if cmds.objExists(self.curves[2]):
            drivers_mid, drivers_local_mid = self._create_clusters(self.curves[2],
                                                               deform_curve_mid,
                                                               follow_curve_mid,
                                                               'mid')
        
        if cmds.objExists(self.curves[3]):
            drivers_liner_top, drivers_local_liner_top = self._create_clusters(self.curves[3],
                                                                               deform_curve_top_liner,
                                                                               follow_curve_top_liner,
                                                                               'liner_top',
                                                                               follow = False)
        
        #if cmds.objExists(self.curves[3]):
        drivers_liner_btm, drivers_local_liner_btm = self._create_clusters(self.curves[4],
                                                                           deform_curve_btm_liner,
                                                                           follow_curve_btm_liner,
                                                                           'liner_btm',
                                                                           follow = False)
    
        if cmds.objExists(self.curves[2]):
            self._create_follow(drivers_top, drivers_mid, 0.5)
            self._create_follow(drivers_liner_top, drivers_mid, 0.225)
        
        top_fades = self._create_fade(corner_control1, top_control, corner_control2, drivers_top)
        btm_fades = self._create_fade(corner_control1, btm_control, corner_control2, drivers_btm)

        sub_fades_top = self._create_fade(corner_sub_control1, top_sub_control, corner_sub_control2, drivers_local_top)
        sub_fades_btm = self._create_fade(corner_sub_control1, btm_sub_control, corner_sub_control2, drivers_local_btm)

        if cmds.objExists(self.curves[3]):
            liner_top_fades = self._create_fade(top_liner_controls['start'][0], 
                                                top_liner_controls['mid'][0], 
                                                top_liner_controls['end'][0],
                                                drivers_liner_top)

        liner_btm_fades = self._create_fade(btm_liner_controls['start'][0], 
                                            btm_liner_controls['mid'][0], 
                                            btm_liner_controls['end'][0],
                                            drivers_liner_btm)
        
        if not self.top_eye_goal:
            self.top_eye_goal = deform_curve_btm
            
        if not self.btm_eye_goal:
            self.btm_eye_goal = deform_curve_top
            
            
        self._fix_lid_fade(deform_curve_top, self.top_eye_goal, top_fades['sides'])
        self._fix_lid_fade(deform_curve_top, self.top_eye_goal, sub_fades_top['sides'])
        
        self._fix_lid_fade(deform_curve_btm, self.btm_eye_goal, btm_fades['sides'])
        self._fix_lid_fade(deform_curve_btm, self.btm_eye_goal, sub_fades_btm['sides'])
        
        if cmds.objExists(self.curves[3]):
            self._fix_lid_fade(deform_curve_top_liner, self.top_eye_goal, liner_top_fades['sides'])
            
        self._fix_lid_fade(deform_curve_btm_liner, self.btm_eye_goal, liner_btm_fades['sides'])
        
        self._create_deformation(deform_curve_top, follow_curve_top)
        self._create_deformation(deform_curve_btm, follow_curve_btm)
        
        if cmds.objExists(self.curves[2]):
            self._create_deformation(deform_curve_mid, follow_curve_mid)
        
        if cmds.objExists(self.curves[3]):
            self._create_deformation(deform_curve_top_liner, follow_curve_top_liner)
            
        self._create_deformation(deform_curve_btm_liner, follow_curve_btm_liner)
