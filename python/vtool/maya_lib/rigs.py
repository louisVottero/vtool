# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

import string

import util
import maya.cmds as cmds


class Rig(object):
    
    side_left = 'L'
    side_right = 'R'
    side_center = 'C'
    
    def __init__(self, description, side):
        self._refresh()
        self.description = description
        self.side = side
        
        self.control_group = self._create_group('controls')
        self.setup_group = self._create_group('setup')
        
        cmds.hide(self.setup_group)
        
        self.control_shape = self._define_control_shape()
        
    def _refresh(self):
        cmds.refresh()
        
    def _define_control_shape(self):
        return 'circle'
        
    def _get_name(self, prefix = None, description = None):
        
        name_list = [prefix,self.description, description, '1', self.side]
        
        filtered_name_list = []
        
        for name in name_list:
            if name:
                filtered_name_list.append(str(name))
        
        name = string.join(filtered_name_list, '_')
        
        return name
        
    def _get_control_name(self, description = None, sub = False):
        
        prefix = 'CNT'
        if sub:
            prefix = 'CNT_SUB'
            
        control_name = self._get_name(prefix, description)
            
        control_name = control_name.upper()
        
        control_name = util.inc_name(control_name)
        
        return control_name
        
    def _create_control(self, description = None, sub = False):
        
        sub_value = False
        
        if sub:
            sub_value = True
        
        control = util.Control( self._get_control_name(description, sub_value) )
        
        control.color( util.get_color_of_side( self.side , sub_value)  )
        control.hide_visibility_attribute()
        control.set_curve_type(self.control_shape)
        
        return control
    
    def _create_group(self,  prefix = None, description = None):
        
        rig_group_name = self._get_name(prefix, description)
        
        group = cmds.group(em = True, n = util.inc_name(rig_group_name))
        
        return group
        
    def set_control_shape(self, shape_name):
        self.control_shape = shape_name
                
    def create(self):
        pass

class JointRig(Rig):
    def __init__(self, description, side):
        super(JointRig, self).__init__(description, side)
        
        self.joints = []
        
        self.attach_joints = True

    def _hook_scale_constraint(self, node):
        
        constraint_editor = util.ConstraintEditor()
        scale_constraint = constraint_editor.get_constraint(node, constraint_editor.constraint_scale)
        
        if not scale_constraint:
            return
        
        weight_count = constraint_editor.get_weight_count(scale_constraint)
        
        cmds.connectAttr('%s.parentInverseMatrix' % node, '%s.constraintParentInverseMatrix' % scale_constraint)
        
        for inc in range(0, weight_count):
            
            target = util.get_attribute_input('%s.target[%s].targetScale' % (scale_constraint, inc), True)
            
            cmds.connectAttr('%s.parentInverseMatrix' % target, '%s.target[%s].targetParentMatrix' % (scale_constraint, inc) )

    def _unhook_scale_constraint(self, scale_constraint):
        constraint_editor = util.ConstraintEditor()
        
        weight_count = constraint_editor.get_weight_count(scale_constraint)
        util.disconnect_attribute('%s.constraintParentInverseMatrix' % scale_constraint)
        
        for inc in range(0, weight_count):
            util.disconnect_attribute('%s.target[%s].targetParentMatrix' % (scale_constraint, inc))

    def _attach_joint(self, source_joint, target_joint):
        if not self.attach_joints:
            return
        self._hook_scale_constraint(target_joint)
        
        parent_constraint = cmds.parentConstraint(source_joint, target_joint, mo = True)[0]
        
        scale_constraint = cmds.scaleConstraint(source_joint, target_joint)[0]
        
        constraint_editor = util.ConstraintEditor()
        constraint_editor.create_switch(self.joints[0], 'switch', parent_constraint)
        constraint_editor.create_switch(self.joints[0], 'switch', scale_constraint)
        
        self._unhook_scale_constraint(scale_constraint)
        
    def _attach_joints(self, source_chain, target_chain):
        
        if not self.attach_joints:
            return
        
        util.AttachJoints(source_chain, target_chain).create()
        
        #for inc in range( 0, len(source_chain) ):
        #    self._attach_joint(source_chain[inc], target_chain[inc] )
    
    def set_joints(self, joints):
        
        if type(joints) != list:
            self.joints = [joints]
            return
        
        self.joints = joints

    def set_attach_joints(self, bool_value):
        
        self.attach_joints = bool_value
        
class BufferRig(JointRig):
    
    def __init__(self, name, side):
        super(BufferRig, self).__init__(name, side)
        
        self.create_buffer_joints = False
    
    def _duplicate_joints(self):
        
        if self.create_buffer_joints:
            duplicate_hierarchy = util.DuplicateHierarchy( self.joints[0] )
            
            duplicate_hierarchy.stop_at(self.joints[-1])
            duplicate_hierarchy.replace('joint', 'buffer')
            
            self.buffer_joints = duplicate_hierarchy.create()
    
            cmds.parent(self.buffer_joints[0], self.setup_group)

        if not self.create_buffer_joints:
            self.buffer_joints = self.joints
        
        return self.buffer_joints
        
    def set_buffer(self, bool_value):
        self.create_buffer_joints = bool_value
            
    def create(self):
        super(BufferRig, self).create()
        
        self._duplicate_joints()
        
        if self.create_buffer_joints:
            self._attach_joints(self.buffer_joints, self.joints)

class SparseRig(JointRig):
    
    def __init__(self, description, side):
        super(SparseRig, self).__init__(description, side)
        self.control_shape = 'cube'
        self.is_scalable = False
        self.respect_side = False
        self.respect_side_tolerance = 0.001
        
    def set_control_shape(self, name):
        self.control_shape = name
        
    def set_scalable(self, bool_value):
        self.is_scalable = bool_value
        
    def set_respect_side(self, bool_value, tolerance = 0.001):
        self.respect_side = bool_value
        self.respect_side_tolerance = tolerance
        
    def create(self):
        
        super(SparseRig, self).create()
        
        for joint in self.joints:
            
            
            
            control = self._create_control()
            control.hide_visibility_attribute()
            control.set_curve_type(self.control_shape)
        
            
        
            
            control_name = control.get()
        
            match = util.MatchSpace(joint, control_name)
            match.translation_rotation()
            
            if self.respect_side:
                side = control.color_respect_side(True, self.respect_side_tolerance)
            
                if side != 'C':
                    control_name = cmds.rename(control_name, util.inc_name(control_name[0:-1] + side))
                    control = util.Control(control_name)
                        
            xform = util.create_xform_group(control.get())
            driver = util.create_xform_group(control.get(), 'driver')
            
            cmds.parentConstraint(control_name, joint)

            if self.is_scalable:
                cmds.scaleConstraint(control.get(), joint)
            if not self.is_scalable:
                control.hide_scale_attributes()
            
            cmds.parent(xform, self.control_group)
            
class BackLeg(BufferRig):

    def __init__(self, description, side):
        super(BackLeg, self).__init__(description, side)

        self.curve_type = 'square'
    

    def _create_guide_chain(self):
        
        duplicate = util.DuplicateHierarchy(self.joints[0])
        duplicate.stop_at(self.joints[-3])
        duplicate.replace('joint', 'ikGuide')
        self.ikGuideChain = duplicate.create()

        
        duplicate = util.DuplicateHierarchy(self.joints[-1])
        duplicate.stop_at(self.joints[-1])
        duplicate.replace('joint', 'ikGuide')
        ball = duplicate.create()


        
        aim = cmds.aimConstraint(ball, self.ikGuideChain[-1], upVector = [0,-1,0])
        cmds.delete(aim)

        cmds.makeIdentity(self.ikGuideChain[-1], r = True, apply = True)

        cmds.parent(ball, self.ikGuideChain[-1])
        
        self.ikGuideChain.append(ball[0])
        
        cmds.parent(self.ikGuideChain[0], self.setup_group)

    def _create_sub_guide_chain(self):
        
        duplicate = util.DuplicateHierarchy(self.ikGuideChain[0])
        duplicate.stop_at(self.ikGuideChain[-2])
        duplicate.replace('ikGuide', 'ikGuideOffset')
        self.offsetGuideChain = duplicate.create()

        cmds.parent(self.offsetGuideChain[0], self.ikGuideChain[0])

        duplicate = util.DuplicateHierarchy(self.ikGuideChain[2])
        duplicate.stop_at(self.ikGuideChain[-1])
        duplicate.replace('ikGuide', 'ikGuideOffsetBtm')
        self.offsetGuideChainBtm = duplicate.create()

        joint1 = self.offsetGuideChainBtm[0]
        joint2 = self.offsetGuideChainBtm[1]
        
        cmds.parent(joint2, w = True)
        cmds.parent(joint1, joint2)

        self.offsetGuideChainBtm = [joint2, joint1]

        cmds.parent(self.offsetGuideChainBtm[0], self.ikGuideChain[2])      

    def _create_offset_chain(self):
        duplicate = util.DuplicateHierarchy(self.joints[2])
        duplicate.stop_at(self.joints[-2])
        duplicate.replace('joint', 'offset1')
        self.offset1Chain = duplicate.create()


        joint1 = self.offset1Chain[0]
        joint2 = self.offset1Chain[1]

        cmds.parent(joint2, w = True)
        
        cmds.parent(joint1, joint2)

    
        self.offset1Chain = [joint2, joint1]

        cmds.parent(self.offset1Chain[0], self.offsetGuideChainBtm[1])

    def _create_offset_chain2(self):
        duplicate = util.DuplicateHierarchy(self.joints[3])
        duplicate.stop_at(self.joints[-1])
        duplicate.replace('joint', 'offset2')
        self.offset2Chain = duplicate.create()

        joint1 = self.offset2Chain[0]
        joint2 = self.offset2Chain[1]

        cmds.parent(joint2, w = True)
        
        cmds.parent(joint1, joint2)

    
        self.offset2Chain = [joint2, joint1]
        
        cmds.parent(self.offset2Chain[0], self.offsetGuideChainBtm[1])

    def _create_pole_chain(self):
        cmds.select(cl =True)
        joint1 = cmds.joint(n = util.inc_name( self._get_name('joint', 'poleTop') ) )
        joint2 = cmds.joint(n = util.inc_name( self._get_name('joint', 'poleBtm') ) )

        util.MatchSpace(self.buffer_joints[0], joint1).translation()
        util.MatchSpace(self.buffer_joints[-1], joint2).translation()

        ik_handle = util.IkHandle( self._get_name(description = 'pole') )
        
        ik_handle.set_start_joint( joint1 )
        ik_handle.set_end_joint( joint2 )
        ik_handle.set_solver(ik_handle.solver_sc)
        self.ik_pole = ik_handle.create()

        self.top_pole_ik = joint1

        cmds.pointConstraint(self.btm_control, self.ik_pole)

        cmds.parent(self.ik_pole, self.top_control)

        cmds.parent(self.top_pole_ik, self.setup_group)
        util.create_follow_group(self.top_control, self.top_pole_ik)
        cmds.hide(self.ik_pole)

        
    def _create_ankle_offset_chain(self):
        pass

    def _duplicate_joints(self):
        super(BackLeg, self)._duplicate_joints()

        self._create_guide_chain()
        self._create_sub_guide_chain()
        self._create_offset_chain()
        self._create_offset_chain2()

        ik_chain = [self.offsetGuideChain[0], self.offsetGuideChain[1], self.offset1Chain[1], self.offset2Chain[1], self.ikGuideChain[-1]]
        self._attach_ik_joints(ik_chain, self.buffer_joints)

    def _attach_ik_joints(self, source_chain, target_chain):
        for inc in range( 0, len(source_chain) ):
            source = source_chain[inc]
            target = target_chain[inc]
            
            print 'attaching', source, target

            cmds.parentConstraint(source, target, mo = True)
            util.connect_scale(source, target)

    def _create_top_control(self):
        
        control = self._create_control(description = 'top')
        control.hide_scale_and_visibility_attributes()
        
        control.set_curve_type(self.curve_type)            
        control.scale_shape(2, 2, 2)
        
        self.top_control = control.get()

        util.MatchSpace(self.ikGuideChain[0], self.top_control).translation_rotation()

        cmds.parentConstraint(self.top_control, self.ikGuideChain[0])

        xform = util.create_xform_group(self.top_control)
        cmds.parent(xform, self.control_group)

    def _create_btm_control(self):
        control = self._create_control(description = 'btm')
        control.hide_scale_and_visibility_attributes()
        
        control.set_curve_type(self.curve_type)
        control.scale_shape(2, 2, 2)
        
        self.btm_control = control.get()

        util.MatchSpace(self.ikGuideChain[-1], self.btm_control).translation_rotation()

        cmds.orientConstraint(self.btm_control, self.ikGuideChain[-1])

        xform = util.create_xform_group(self.btm_control)
        cmds.parent(xform, self.control_group)

    def _create_top_offset_control(self):

        control = self._create_control(description = 'top_offset')
        control.hide_scale_and_visibility_attributes()
        control.set_curve_type(self.curve_type)

        self.top_offset = control.get()

        util.MatchSpace(self.ikGuideChain[2], self.top_offset).translation_rotation()

        xform_offset = util.create_xform_group(self.top_offset)

        follow = util.create_follow_group(self.ikGuideChain[2], xform_offset)

        cmds.parent(follow, self.top_control)
        
        cmds.parent(self.offsetGuideChainBtm[0], self.ikGuideChain[-1])

    def _create_btm_offset_control(self):

        control = self._create_control(description = 'btm_offset')
        control.hide_scale_and_visibility_attributes()
        control.scale_shape(2, 2, 2)
        control.set_curve_type(self.curve_type)
        
        self.btm_offset = control.get()

        util.MatchSpace(self.offset1Chain[0], self.btm_offset).translation()

        xform = util.create_xform_group(self.btm_offset)
        cmds.parent(xform, self.control_group)

        util.create_follow_group(self.offsetGuideChainBtm[1], xform)

        cmds.parentConstraint(self.ikGuideChain[-1], self.offset2Chain[0], mo = True)

        cmds.parentConstraint(self.offset2Chain[-1], self.offset1Chain[0], mo = True)

    def _create_pole_vector(self):

        if self.side == 'L':
            self.pole_offset = -1
        if self.side == 'R':
            self.pole_offset = 1      
        
        control = self._create_control('POLE')
        control.hide_scale_and_visibility_attributes()
        control.set_curve_type('cube')
        self.pole_control = control.get()
        
        pole_var = util.MayaEnumVariable('POLE_VECTOR')
        pole_var.create(self.btm_control)
        
        pole_vis = util.MayaNumberVariable('poleVisibility')
        pole_vis.set_variable_type(pole_vis.TYPE_BOOL)
        pole_vis.create(self.btm_control)
        
        twist_var = util.MayaNumberVariable('twist')
        twist_var.create(self.btm_control)
        
        if self.side == 'L':
            twist_var.connect_out('%s.twist' % self.main_ik)
            
        if self.side == 'R':
            util.connect_multiply('%s.twist' % self.btm_control, '%s.twist' % self.main_ik, -1)
        
        pole_joints = [self.ikGuideChain[0], self.ikGuideChain[1], self.ikGuideChain[2]]

      
        position = util.get_polevector( pole_joints[0], pole_joints[1], pole_joints[2], self.pole_offset )

        cmds.move(position[0], position[1], position[2], control.get())

        cmds.poleVectorConstraint(control.get(), self.main_ik)
        
        xform_group = util.create_xform_group( control.get() )
        
        name = self._get_name()
        
        rig_line = util.RiggedLine(pole_joints[1], control.get(), name).create()
        cmds.parent(rig_line, self.control_group)
        
        pole_vis.connect_out('%s.visibility' % xform_group)
        pole_vis.connect_out('%s.visibility' % rig_line)
        
        self.pole_vector_xform = xform_group

        cmds.parent(xform_group, self.control_group)

        util.create_follow_group(self.top_pole_ik, xform_group)

        

    def _create_ik_guide_handle(self):
        
        ik_handle = util.IkHandle( self._get_name() )
        
        ik_handle.set_start_joint( self.ikGuideChain[0] )
        ik_handle.set_end_joint( self.ikGuideChain[-1] )
        ik_handle.set_solver(ik_handle.solver_rp)
        self.ik_handle = ik_handle.create()
        self.main_ik = self.ik_handle
        
        xform_ik_handle = util.create_xform_group(self.ik_handle)
        cmds.parent(xform_ik_handle, self.setup_group)

        cmds.pointConstraint(self.btm_control, self.ik_handle)
        

    def _create_ik_sub_guide_handle(self):

        ik_handle = util.IkHandle( self._get_name('sub') )
        
        ik_handle.set_start_joint( self.offsetGuideChain[0] )
        ik_handle.set_end_joint( self.offsetGuideChain[-1] )
        ik_handle.set_solver(ik_handle.solver_sc)
        self.ik_handle = ik_handle.create()
        
        xform_ik_handle = util.create_xform_group(self.ik_handle)

        cmds.parent(xform_ik_handle, self.offset1Chain[-1])
         

    def _create_ik_sub_guide_btm_handle(self):
        ik_handle = util.IkHandle( self._get_name('sub_btm') )
        
        ik_handle.set_start_joint( self.offsetGuideChainBtm[0] )
        ik_handle.set_end_joint( self.offsetGuideChainBtm[-1] )
        ik_handle.set_solver(ik_handle.solver_sc)
        self.ik_handle = ik_handle.create()
        
        xform_ik_handle = util.create_xform_group(self.ik_handle)

        cmds.parent(xform_ik_handle, self.top_offset)        

    def _create_ik_offset_handle(self):
        ik_handle = util.IkHandle( self._get_name('offset') )
        
        ik_handle.set_start_joint( self.offset1Chain[0] )
        ik_handle.set_end_joint( self.offset1Chain[-1] )
        ik_handle.set_solver(ik_handle.solver_sc)
        self.ik_handle = ik_handle.create()
        
        xform_ik_handle = util.create_xform_group(self.ik_handle)

        cmds.parent(xform_ik_handle, self.offsetGuideChainBtm[0])          

    def _create_ik_offset2_handle(self):
        ik_handle = util.IkHandle( self._get_name('offset') )
        
        ik_handle.set_start_joint( self.offset2Chain[0] )
        ik_handle.set_end_joint( self.offset2Chain[-1] )
        ik_handle.set_solver(ik_handle.solver_sc)
        self.ik_handle = ik_handle.create()
        
        xform_ik_handle = util.create_xform_group(self.ik_handle)

        cmds.parent(xform_ik_handle, self.btm_offset) 
        
        cmds.refresh()

    def create(self):
        super(BackLeg, self).create()
                
        self._create_top_control()
        self._create_btm_control()
        self._create_top_offset_control()
        self._create_btm_offset_control()


        self._create_ik_guide_handle()
        self._create_ik_sub_guide_handle()
        self._create_ik_sub_guide_btm_handle()
        self._create_ik_offset_handle()
        self._create_ik_offset2_handle()

        self._create_pole_chain()

        self._create_pole_vector()