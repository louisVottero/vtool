# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.


import util
import maya.cmds as cmds

import vtool.util

class EyeLidSphereRig(util.BufferRig):
    
    def __init__(self, description, side):
        super(EyeLidSphereRig, self).__init__(description, side)
        
        self.radius = 2
        self.axis = 'X'
        self.sections = 15
        self.curve = None
        self.ik_handles = []
    
    def _create_ik(self, joints):
        
        for joint in joints:
            
            parent = cmds.listRelatives(joint, parent = True, type = 'transform')[0]
            child_joint = cmds.listRelatives(joint, type = 'joint')[0]
            
            ik = util.IkHandle(self._get_name())
            ik.set_start_joint(joint)
            ik.set_end_joint(child_joint)
            
            ik.set_solver(ik.solver_sc)
            ik.create()
            
            cmds.parent(ik.ik_handle, parent)
            self.ik_handles.append(ik.ik_handle)
        
    def set_sections(self, int_value):
        self.sections = int(int_value)
        
    def set_radius(self, float_value):
        self.radius = float(float_value)
        
    def set_axis(self, axis_letter):
        self.axis = str(axis_letter).upper()
        
    def set_curve(self, curve_name):
        self.curve = curve_name
        
    def create(self):
        super(EyeLidSphereRig, self).create()
        
        center_joint = self.buffer_joints[0]
        
        joints, group = create_joint_slice( center_joint, '%s1_%s' % (self.description, self.side), radius = self.radius, sections = self.sections, axis = self.axis)
        
        self._create_ik(joints)
        
        cmds.parent(group, self.setup_group)
        
        util.MatchSpace(center_joint, self.setup_group).rotation()
        
        if self.curve:
            inc = 1
            
            for ik_handle in self.ik_handles:
                print ik_handle
                group_ik = cmds.group(em = True, n = util.inc_name('group_ik%s_%s' % (inc,self._get_name())))
                util.MatchSpace(ik_handle, group_ik).translation()
                cmds.parent(ik_handle, group_ik)
                
                util.attach_to_curve(group_ik, self.curve)
                cmds.parent(group_ik, self.setup_group)
                
                inc+=1
                
def create_joint_slice( center_joint, description, radius = 2, sections = 1, axis = 'X'):
    
    slice_group = cmds.group(em = True, n = util.inc_name('group_slice_%s' % description))
    
    section = radius/float( (sections/2) )
    
    offset = section/2.0
    
    angle_section = 90/((sections/2)+1)
    angle_offset = angle_section
    
    joints = []
    
    for inc in range(0, (sections/2)):
        
        group_pos = cmds.group(em = True, n = util.inc_name('group_slice%s_%s' % (inc+1, description)))
        group_neg = cmds.group(em = True, n = util.inc_name('group_slice%s_%s' % (inc+1, description)))
        cmds.parent(group_pos, group_neg, slice_group)
        
        dup_pos = cmds.duplicate(center_joint, n = util.inc_name('joint_guide%s_%s' % (inc+1, description)))[0]
        
        dup_neg = cmds.duplicate(center_joint, n = util.inc_name('joint_guide%s_%s' % (inc+1, description)))[0]
        
        
        
        joints.append(dup_pos)
        joints.append(dup_neg)
        
        cmds.parent(dup_pos, group_pos)
        cmds.parent(dup_neg, group_neg)
        
        import math
        edge = math.sqrt( (radius*radius) - (offset*offset) )
        
        vtool.util.Vector(1,0,0)
        #vector = []
        edge_vector = []
        
        if axis == 'X':
            
            vector = [1,0,0]
            vector = [offset, 0 , 0]
            edge_vector = [0,edge, 0]
            
            for dup in [dup_pos, dup_neg]:
                cmds.transformLimits( dup, ry = [0, 0], ery = [1, 1])
                cmds.transformLimits( dup, rz = [0, 0], erz = [1, 1])
        
        if axis == 'Y':
            vector = [0,1,0]
            vector = [0, offset, 0]
            edge_vector = [edge, 0, 0]
            
            for dup in [dup_pos, dup_neg]:
                cmds.transformLimits( dup, rx = [0, 0], erx = [1, 1])
                cmds.transformLimits( dup, rz = [0, 0], erz = [1, 1])
        
        if axis == 'Z':
            vector = [0,0,1]
            vector = [0, 0, offset]
            edge_vector = [0,edge, 0]
            
            for dup in [dup_pos, dup_neg]:
                cmds.transformLimits( dup, ry = [0, 0], ery = [1, 1])
                cmds.transformLimits( dup, rx = [0, 0], erx = [1, 1])
        
        cmds.move( vector[0],vector[1],vector[2], dup_pos, r = True )
        
        neg_vector = -1 * vtool.util.Vector(vector)
        
        cmds.move( neg_vector.x, neg_vector.y, neg_vector.z, dup_neg, r = True )
        
        offset += section
        
        for dup in [dup_pos, dup_neg]:
            dup2 = cmds.duplicate(dup, n = util.inc_name('joint_guideEnd%s_%s' % (inc+1, description)))[0]
            
            cmds.move(edge_vector[0],edge_vector[1],edge_vector[2], dup2, r = True)
            
            cmds.parent(dup2, dup)
            
            angle_offset = angle_section
            
            value = 1.0/((sections/2)+1)
            value_offset = 1.0-value
            
            for inc in range(0, (sections/2)+1):
                dup3 = cmds.duplicate(dup, n = util.inc_name('joint_angle%s_%s' % (inc+1, description)))[0]
                
                rels = cmds.listRelatives(dup3, f = True)
                
                cmds.rename(rels[0], util.inc_name('joint_angleEnd%s_%s' % (inc+1, description)))
                
                cmds.rotate(angle_offset, 0, 0, dup3)
                angle_offset += angle_section
                
                cmds.makeIdentity(dup3, r = True, apply = True)
                
                multiply = util.connect_multiply( '%s.rotate%s' % (dup, axis), '%s.rotate%s' % (dup3, axis), value_offset)
                
                cmds.connectAttr('%s.rotateY' % dup, '%s.input1Y' % multiply)
                cmds.connectAttr('%s.outputY' % multiply, '%s.rotateY' % dup3)
                cmds.setAttr('%s.input2Y' % multiply, value_offset)
                value_offset-=value
                
    return joints, slice_group