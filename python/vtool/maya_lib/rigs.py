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