# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.


import util

import maya.cmds as cmds

import vtool.util
import rigs
from vtool.maya_lib.util import MatchSpace, create_xform_group


class StickyRig(rigs.JointRig):
    
    def __init__(self, description, side):
        super(StickyRig, self).__init__(description, side)
        
        self.top_joints = []
        self.btm_joints = []
        self.respect_side = True
        self.respect_side_tolerance = 0.01
        self.straight_loop = False
        
        self.locators = []
        self.zip_controls = []
        
        self.follower_group = None
        
        self.first_side = side
        
        self.control_dict = {}
        
        self.sticky_control_group = cmds.group(em = True, n = util.inc_name(self._get_name('group', 'sticky_controls')))
        cmds.parent(self.sticky_control_group, self.control_group)
        
        self.follow_control_groups = {} 

    
    def _loop_joints(self):
        
        self.top_joint_group = cmds.group(em = True, n = util.inc_name( self._get_name('group', 'joints_top')))
        self.btm_joint_group = cmds.group(em = True, n = util.inc_name( self._get_name('group', 'joints_btm')))
        
        self.top_locator_group = cmds.group(em = True, n = util.inc_name( self._get_name('group', 'locators_top')))
        self.mid_locator_group = cmds.group(em = True, n = util.inc_name( self._get_name('group', 'locators_mid')))
        self.btm_locator_group = cmds.group(em = True, n = util.inc_name( self._get_name('group', 'locators_btm')))
        
        cmds.parent(self.top_joint_group, self.btm_joint_group, self.setup_group)
        cmds.parent(self.top_locator_group, self.mid_locator_group, self.btm_locator_group, self.setup_group)
        
        joint_count = len(self.top_joints)
        
        if self.straight_loop:
            for inc in range(0, joint_count):
                self._create_increment(inc)
                
        if not self.straight_loop:
            for inc in range(0, joint_count):
                
                negative_inc = joint_count - (inc+1)
                
                self._create_increment(inc)
                
                locators1 = [self.top_locator, self.btm_locator]
                top_control1 = self.controls[-1]
                btm_control1 = self.controls[-2]
                
                if inc == negative_inc:
                    self.locators.append([locators1])
                    self.zip_controls.append([[top_control1, btm_control1]])
                    break
                
                self._create_increment(negative_inc)
                
                locators2 = [self.top_locator, self.btm_locator]
                top_control2 = self.controls[-1]
                btm_control2 = self.controls[-2]
                
                self.locators.append([locators1, locators2])
                self.zip_controls.append([[top_control1, btm_control1],[top_control2,btm_control2]])
                
        self.side = self.first_side
           
    def _create_increment(self, inc):
        top_joint = self.top_joints[inc]
        btm_joint = self.btm_joints[inc]
        
        if self.respect_side:
            side = util.get_side(top_joint, self.respect_side_tolerance)
            self.side = side
            
        old_top_joint = top_joint
        old_btm_joint = btm_joint
        
        top_joint = cmds.duplicate(top_joint, n = util.inc_name(self._get_name('inputJoint', 'top')))[0]
        btm_joint = cmds.duplicate(btm_joint, n = util.inc_name(self._get_name('inputJoint', 'btm')))[0]
        
        cmds.parentConstraint(top_joint, old_top_joint)
        cmds.scaleConstraint(top_joint, old_top_joint)
        
        cmds.parentConstraint(btm_joint, old_btm_joint)
        cmds.scaleConstraint(btm_joint, old_btm_joint)
        
        cmds.parent(top_joint, self.top_joint_group)
        cmds.parent(btm_joint, self.btm_joint_group)
        
        control_top = self._create_sticky_control(top_joint, 'top')
        control_btm = self._create_sticky_control(btm_joint, 'btm')
        
        self.top_locator = self._create_locator('top')
        self.mid_top_locator = self._create_locator('mid_top')
        self.mid_btm_locator = self._create_locator('mid_btm')
        self.btm_locator = self._create_locator('btm')
        
        self.control_dict[control_top[0]] = [control_top[1], control_top[2]]
        self.control_dict[control_btm[0]] = [control_btm[1], control_btm[2]]
        
        util.MatchSpace(top_joint, self.top_locator[1]).translation_rotation()
        util.MatchSpace(btm_joint, self.btm_locator[1]).translation_rotation()
        
        midpoint = util.get_midpoint(top_joint, btm_joint)
        
        cmds.xform(self.mid_top_locator[1], t = midpoint, ws = True)
        cmds.xform(self.mid_btm_locator[1], t = midpoint, ws = True)
        
        cmds.parent(self.top_locator[1], self.top_locator_group)
        cmds.parent(self.mid_top_locator[1], self.mid_locator_group)
        cmds.parent(self.mid_btm_locator[1], self.mid_locator_group)
        cmds.parent(self.btm_locator[1], self.btm_locator_group)   

        top_xform, top_driver = self._group_joint(top_joint)
        btm_xform, btm_driver = self._group_joint(btm_joint)
        
        self._create_follow([self.top_locator[0], self.mid_top_locator[0]], top_xform, top_joint)
        
        cmds.addAttr(control_top[0], ln = 'stick', min = 0, max = 1, k = True)
        
        cmds.connectAttr('%s.stick' % control_top[0], '%s.stick' % top_joint)
        
        self._create_follow([self.btm_locator[0], self.mid_btm_locator[0]], btm_xform, control_btm[0])
        
        self._create_follow([self.top_locator[0], self.btm_locator[0]], self.mid_top_locator[1], self.mid_top_locator[0])
        self._create_follow([self.top_locator[0], self.btm_locator[0]], self.mid_btm_locator[1], self.mid_btm_locator[0])
        
        cmds.setAttr('%s.stick' % self.mid_top_locator[0], 0.5)
        cmds.setAttr('%s.stick' % self.mid_btm_locator[0], 0.5)
        
        util.MatchSpace(self.top_locator[0], self.mid_top_locator[0]).translation_rotation()
        util.MatchSpace(self.btm_locator[0], self.mid_btm_locator[0]).translation_rotation()
        
        #top
        util.connect_translate(top_xform, control_top[1])
        util.connect_translate(control_top[2], top_driver)
        util.connect_translate(control_top[0], top_joint)
        
        util.connect_rotate(top_xform, control_top[1])
        util.connect_rotate(control_top[2], top_driver)
        util.connect_rotate(control_top[0], top_joint)
        
        util.connect_scale(top_xform, control_top[1])
        util.connect_scale(control_top[2], top_driver)
        util.connect_scale(control_top[0], top_joint)
        
        #btm
        util.connect_translate(btm_xform, control_btm[1])
        util.connect_translate(control_btm[2], btm_driver)
        util.connect_translate(control_btm[0], btm_joint)
        
        util.connect_rotate(btm_xform, control_btm[1])
        util.connect_rotate(control_btm[2], btm_driver)
        util.connect_rotate(control_btm[0], btm_joint)
        
        util.connect_scale(btm_xform, control_btm[1])
        util.connect_scale(control_btm[2], btm_driver)
        util.connect_scale(control_btm[0], btm_joint)
           
    def _create_follow(self, source_list, target, target_control ):
        
        constraint = cmds.parentConstraint(source_list, target)[0]
        cmds.setAttr('%s.interpType' % constraint, 2)
        constraint_editor = util.ConstraintEditor()    
        constraint_editor.create_switch(target_control, 'stick', constraint)
         
        
         
    def _create_sticky_control(self, transform, description):
        
        
        
            
        
        control = self._create_control(description)
        control.scale_shape(.8, .8, .8)
        control.hide_scale_attributes()
        control_name = control.get()
        
        
        util.MatchSpace(transform, control_name).translation_rotation()
                        
        control = control_name
        
        xform = util.create_xform_group(control)
        driver = util.create_xform_group(control, 'driver')
        
        cmds.parent(xform, self.sticky_control_group)
        
        return control, xform, driver
               
    def _group_joint(self, joint):
        
        print joint
        
        xform = util.create_xform_group(joint)
        driver = util.create_xform_group(joint, 'driver')
        
        return xform, driver
                
    def _create_locator(self, description):
        
        locator = cmds.spaceLocator(n = util.inc_name(self._get_name('locator', description)))[0]
        
        xform = util.create_xform_group(locator)
        driver = util.create_xform_group(locator, 'driver')
        
        return locator, xform, driver
    
    def _create_follow_control_group(self, follow_control):
    
        if not follow_control in self.follow_control_groups.keys():
            
            group = cmds.group(em = True, n = 'follow_group_%s' % follow_control)
            util.MatchSpace(follow_control, group).translation_rotation()
            cmds.parent(group, self.follower_group)
            util.create_xform_group(group)
                        
            #cmds.parentConstraint(follow_control, group)
            util.connect_translate_plus(follow_control, group)
            util.connect_rotate(follow_control, group)
            
            #local, xform = util.constrain_local(follow_control, group)
            #cmds.parent(xform, self.setup_group)
            
            self.follow_control_groups[follow_control] = group
            
            
            
        return self.follow_control_groups[follow_control]
        
    
    def set_respect_side(self, bool_value, tolerance = 0.001):
        self.respect_side = bool_value
        self.respect_side_tolerance = tolerance
    
    def set_top_joints(self, joint_list):
        self.top_joints = joint_list
        
    def set_btm_joints(self, joint_list):
        self.btm_joints = joint_list
    
    def set_top_stick_values(self, float_list):
        self.top_stick_values = float_list
    
    def set_btm_stick_values(self, float_list):
        self.btm_stick_values = float_list
    
    def create(self):
        super(StickyRig, self).create()
        
        self._loop_joints()
        
    def create_follow(self, follow_transform, increment, value):
        
        if not self.follower_group:
            self.follower_group = cmds.group(em = True, n = util.inc_name(self._get_name('group', 'follower')))
            cmds.parent(self.follower_group, self.setup_group)
        
        follow_transform = self._create_follow_control_group(follow_transform)
        
        locators = self.locators[increment]
        
        top_locator1 = locators[0][0][1]
        btm_locator1 = locators[0][1][1]
        
        util.create_multi_follow([self.follower_group, follow_transform], top_locator1, top_locator1, value = value)
        util.create_multi_follow([self.follower_group, follow_transform], btm_locator1, btm_locator1, value = 1-value)
        
        if len(locators) > 1:
            top_locator2 = locators[1][0][1]
            btm_locator2 = locators[1][1][1]
        
            util.create_multi_follow([self.follower_group, follow_transform], top_locator2, top_locator2, value = value)
            util.create_multi_follow([self.follower_group, follow_transform], btm_locator2, btm_locator2, value = 1-value)
        
    def create_zip(self, attribute_control, increment, start, end, end_value = 1):
        
        left_over_value = 1.0 - end_value
        
        if not cmds.objExists('%s.zipL' % attribute_control):
            cmds.addAttr(attribute_control, ln = 'zipL', min = 0, max = 10, k = True)
            
        if not cmds.objExists('%s.zipR' % attribute_control):
            cmds.addAttr(attribute_control, ln = 'zipR', min = 0, max = 10, k = True)
            
        util.quick_driven_key('%s.zipL' % attribute_control, '%s.stick' % self.zip_controls[increment][0][0], [start,end], [0,end_value])
        util.quick_driven_key('%s.zipL' % attribute_control, '%s.stick' % self.zip_controls[increment][0][1], [start,end], [0,end_value])
                
        if left_over_value:
            util.quick_driven_key('%s.zipR' % attribute_control, '%s.stick' % self.zip_controls[increment][0][0], [start,end], [0,left_over_value])
            util.quick_driven_key('%s.zipR' % attribute_control, '%s.stick' % self.zip_controls[increment][0][1], [start,end], [0,left_over_value])
        
        right_increment = 1
        
        if len(self.zip_controls[increment]) == 1:
            right_increment = 0
        
        util.quick_driven_key('%s.zipR' % attribute_control, '%s.stick' % self.zip_controls[increment][right_increment][0], [start,end], [0,end_value])
        util.quick_driven_key('%s.zipR' % attribute_control, '%s.stick' % self.zip_controls[increment][right_increment][1], [start,end], [0,end_value])
        
        if left_over_value:
            util.quick_driven_key('%s.zipL' % attribute_control, '%s.stick' % self.zip_controls[increment][right_increment][0], [start,end], [0,left_over_value])
            util.quick_driven_key('%s.zipL' % attribute_control, '%s.stick' % self.zip_controls[increment][right_increment][1], [start,end], [0,left_over_value])
            
     
        
class StickyLipRig(StickyRig):

    def __init__(self, description, side):
        super(StickyLipRig, self).__init__(description, side)
        
        self.top_curve = None
        self.btm_curve = None
        
        self.clusters_top = []
        self.clusters_btm = []
        
        self.center_tolerance = 0.01
        
        self.main_controls = []
        self.corner_controls = []
        
        self.first_side = side
        
        self.left_corner_control = None
        self.right_corner_control = None
        
        self.corner_control_shape = 'square'
        
    
        self.main_control_group = cmds.group(em = True, n = util.inc_name(self._get_name('group', 'main_controls')))
        cmds.parent(self.main_control_group, self.control_group)
    
    def _create_curves(self):
        
        top_cv_count = len(self.top_joints) - 3
        btm_cv_count = len(self.btm_joints) - 3
        
        self.top_curve = util.transforms_to_curve(self.top_joints, 4, self.description + '_top')
        self.btm_curve = util.transforms_to_curve(self.btm_joints, 4, self.description + '_btm')
        
        self.top_guide_curve = util.transforms_to_curve(self.top_joints, top_cv_count, self.description + '_top_guide')
        self.btm_guide_curve = util.transforms_to_curve(self.btm_joints, top_cv_count, self.description + '_btm_guide')
        
        cmds.parent(self.top_curve, self.setup_group)
        cmds.parent(self.btm_curve, self.setup_group)
        cmds.parent(self.top_guide_curve, self.btm_guide_curve, self.setup_group)
        
    def _cluster_curves(self):
        
        cluster_group = cmds.group(em = True, n = util.inc_name(self._get_name('group', 'clusters')))
        
        self.clusters_top = util.cluster_curve(self.top_curve, self.description + '_top')
        self.clusters_btm = util.cluster_curve(self.btm_curve, self.description + '_btm')
        
        self.clusters_guide_top = util.cluster_curve(self.top_guide_curve, self.description + '_top_guide')
        self.clusters_guide_btm = util.cluster_curve(self.btm_guide_curve, self.description + '_btm_guide')
        
        cmds.parent(self.clusters_top, self.clusters_btm, self.clusters_guide_top, self.clusters_guide_btm, cluster_group)
        cmds.parent(cluster_group, self.setup_group)
    
    def _create_curve_joints(self):
        
        self.top_tweak_joints, self.top_joint_group, top_controls =  util.create_joints_on_curve(self.top_curve, len(self.top_joints), self.description)
        self.btm_tweak_joints, self.btm_joint_group, btm_controls = util.create_joints_on_curve(self.btm_curve, len(self.btm_joints), self.description)
        
    def _connect_curve_joints(self):
        
        inc = 0
        
        control_count = len(self.zip_controls)
        joint_count = len(self.top_joints)
        
        for controls in self.zip_controls:
            
            if inc == control_count:
                break
            
            negative_inc = joint_count - (inc+1)
            
            left_top_control = controls[0][1]
            left_btm_control = controls[0][0]
            
            #do first part
            driver = cmds.listRelatives(left_top_control, p = True)[0]
            util.connect_translate_plus(self.top_tweak_joints[inc], driver)

            driver = cmds.listRelatives(left_btm_control, p = True)[0]
            util.connect_translate_plus(self.btm_tweak_joints[inc], driver)
                
            if inc == negative_inc:
                break
            
            #do second part
            if len(controls) > 1:
                right_top_control = controls[1][1]
                right_btm_control = controls[1][0]            

                driver = cmds.listRelatives(right_top_control, p = True)[0]
                util.connect_translate_plus(self.top_tweak_joints[negative_inc], driver)

                driver = cmds.listRelatives(right_btm_control, p = True)[0]
                util.connect_translate_plus(self.btm_tweak_joints[negative_inc], driver)

            
            inc += 1

        cmds.parent(self.top_joint_group, self.setup_group)
        cmds.parent(self.btm_joint_group, self.setup_group)
        
    def _connect_guide_clusters(self):
        
        inc = 0
        
        cluster_count = len(self.clusters_guide_top)
        
        for inc in range(0, cluster_count):
        
            locators = self.locators[inc]
            controls = self.zip_controls[inc]

            top_locator = controls[0][1]
            btm_locator = controls[0][0]
            
            top_locator = self.control_dict[top_locator][0]
            btm_locator = self.control_dict[btm_locator][0]
            
            if inc == cluster_count:
                break
            
            negative_inc = cluster_count - (inc+1)
            
            #do first part

            top_local, top_xform = util.constrain_local(top_locator, self.clusters_guide_top[inc])
            btm_local, btm_xform = util.constrain_local(btm_locator, self.clusters_guide_btm[inc])

            cmds.parent(top_xform, btm_xform, self.setup_group)

            #cmds.pointConstraint(top_locator, self.clusters_guide_top[inc])
            #cmds.pointConstraint(btm_locator, self.clusters_guide_btm[inc])
    
            if inc == negative_inc:
                break
            
            #do second part
            if len(locators) > 1:
                top_locator = controls[1][1]
                btm_locator = controls[1][0]
            
                top_locator = self.control_dict[top_locator][0]
                btm_locator = self.control_dict[btm_locator][0]
                
                top_local, top_xform = util.constrain_local(top_locator, self.clusters_guide_top[negative_inc])
                btm_local, btm_xform = util.constrain_local(btm_locator, self.clusters_guide_btm[negative_inc])
                
                cmds.parent(top_xform, btm_xform, self.setup_group)

                #cmds.pointConstraint(top_locator, self.clusters_guide_top[negative_inc])
                #cmds.pointConstraint(btm_locator, self.clusters_guide_btm[negative_inc])
            
            inc += 1
        
    def _create_main_controls(self):
        
        inc = 0
        
        cluster_count = len(self.clusters_top)
        

        
        for inc in range(0, cluster_count):
        
            
            if inc == cluster_count:
                break
            
            negative_inc = cluster_count - (inc+1)
            
            #do first part
            
            self._create_main_control(self.clusters_top[inc], self.top_guide_curve, 'top')
            self._create_main_control(self.clusters_btm[inc], self.btm_guide_curve, 'btm')

            if inc == negative_inc:
                break
            
            self._create_main_control(self.clusters_top[negative_inc], self.top_guide_curve, 'top')
            self._create_main_control(self.clusters_btm[negative_inc], self.btm_guide_curve, 'btm')
            
            inc += 1
                    
    def _create_main_control(self, cluster, attach_curve, description):
        
        control = self._create_control(description)
            
        control.rotate_shape(90, 0, 0)
        
            
        control = control.get()
        util.MatchSpace(cluster, control).translation_to_rotate_pivot()
        
        control = util.Control(control)
        side = control.color_respect_side(False, self.center_tolerance)
        
        if side == 'C':
            control = control.get()
        
        if side != 'C':
            control = cmds.rename(control.get(), util.inc_name(control.get()[0:-1] + side))
        
        cmds.parent(control, self.main_control_group)
        
        xform = util.create_xform_group(control)
        driver = util.create_xform_group(control, 'driver')
        
        util.attach_to_curve(xform, attach_curve)
        
        local_control, local_xform = util.constrain_local(control, cluster)
        driver_local_control = util.create_xform_group(local_control, 'driver')
        
        util.connect_translate(driver, driver_local_control)
        
        cmds.parent(local_xform, self.setup_group)
        
        self.main_controls.append([control, xform, driver])
        
        return control
        
    def _create_sticky_control(self, transform, description):
        
        if not self.sticky_control_group:
            self.sticky_control_group = cmds.group(em = True, n = util.inc_name(self._get_name('group', 'sticky_controls')))
            
            cmds.parent(self.sticky_control_group, self.control_group)
        
        control = self._create_control(description, sub = True)
        
        control.rotate_shape(90,0,0)
        control.scale_shape(.5, .5, .5)
        control.hide_scale_attributes()
        
        control_name = control.get()
        
        util.MatchSpace(transform, control_name).translation_rotation()
                        
        control = control_name
        
        xform = util.create_xform_group(control)
        driver = util.create_xform_group(control, 'driver')
        
        cmds.parent(xform, self.sticky_control_group)
        
        return control, xform, driver
        
    def _create_corner_controls(self):
               
        orig_side = self.side
    
        print self.main_controls
       
        for side in ['L','R']:
            
            self.side = side
               
            control = self._create_control('corner')
            control.set_curve_type(self.corner_control_shape)
            control.rotate_shape(90,0,0)
            control.hide_scale_attributes()
            
            sub_control = self._create_control('corner', sub = True)
            sub_control.set_curve_type(self.corner_control_shape)
            sub_control.rotate_shape(90,0,0)
            sub_control.scale_shape(.8, .8, .8)
            sub_control.hide_scale_attributes()
            
            if side == 'L':
                self.left_corner_control = control.get()
                top_control_driver = self.main_controls[0][2]
                btm_control_driver = self.main_controls[1][2]
                
                self.main_controls[0][0] = cmds.rename(self.main_controls[0][0], self.main_controls[0][0].replace('CNT_', 'ctrl_') )
                cmds.delete('%sShape' % self.main_controls[0][0])
                self.main_controls[1][0] = cmds.rename(self.main_controls[1][0], self.main_controls[1][0].replace('CNT_', 'ctrl_') )
                cmds.delete('%sShape' % self.main_controls[1][0])
            
            if side == 'R':
                self.right_corner_control = control.get()
                top_control_driver = self.main_controls[2][2]
                btm_control_driver = self.main_controls[3][2]
                
                self.main_controls[2][0] = cmds.rename(self.main_controls[2][0], self.main_controls[2][0].replace('CNT_', 'ctrl_') )
                cmds.delete('%sShape' % self.main_controls[2][0])
                self.main_controls[3][0] = cmds.rename(self.main_controls[3][0], self.main_controls[3][0].replace('CNT_', 'ctrl_') )
                cmds.delete('%sShape' % self.main_controls[3][0])
            
            cmds.parent(sub_control.get(), control.get())
            
            util.MatchSpace(top_control_driver, control.get()).translation_rotation()
            
            xform = util.create_xform_group(control.get())
            
            self.corner_controls.append([control.get(), xform])
            
            top_plus = util.connect_translate_plus(control.get(), top_control_driver)
            btm_plus = util.connect_translate_plus(control.get(), btm_control_driver)
            
            cmds.connectAttr('%s.translateX' % sub_control.get(), '%s.input3D[2].input3Dx' % top_plus)
            cmds.connectAttr('%s.translateY' % sub_control.get(), '%s.input3D[2].input3Dy' % top_plus)
            cmds.connectAttr('%s.translateZ' % sub_control.get(), '%s.input3D[2].input3Dz' % top_plus)
            
            cmds.connectAttr('%s.translateX' % sub_control.get(), '%s.input3D[2].input3Dx' % btm_plus)
            cmds.connectAttr('%s.translateY' % sub_control.get(), '%s.input3D[2].input3Dy' % btm_plus)
            cmds.connectAttr('%s.translateZ' % sub_control.get(), '%s.input3D[2].input3Dz' % btm_plus)
            
            util.attach_to_curve(xform, self.top_guide_curve)
            
            cmds.parent(xform, self.control_group)
            
            
        
        self.side = orig_side
        
    def set_corner_control_shape(self, shape_name):
        self.corner_control_shape = shape_name
        
    def create_corner_falloff(self, inc, value):

        if inc > 0:
            inc = inc * 4

        for side in ['L','R']:
            
            self.side = side
                 
            if side == 'L':
                corner_control = self.left_corner_control
                top_control_driver = self.main_controls[inc][2]
                btm_control_driver = self.main_controls[inc+1][2]
            
            if side == 'R':
                corner_control = self.right_corner_control
                top_control_driver = self.main_controls[inc+2][2]
                btm_control_driver = self.main_controls[inc+3][2]
        
            util.connect_translate_multiply(corner_control, top_control_driver, value)
            util.connect_translate_multiply(corner_control, btm_control_driver, value)
        
    def create_roll(self, increment, percent):
        
        top_center_control, top_center_xform, top_center_driver = self.main_controls[-2]
        btm_center_control, btm_center_xform, btm_center_driver = self.main_controls[-1]
        
        if not cmds.objExists('%s.roll' % top_center_control):
            cmds.addAttr(top_center_control, ln = 'roll', k = True)
            
        if not cmds.objExists('%s.roll' % btm_center_control):
            cmds.addAttr(btm_center_control, ln = 'roll', k = True)
        
        if not cmds.objExists('%s.bulge' % top_center_control):
            cmds.addAttr(top_center_control, ln = 'bulge', k = True, dv =1, min = 0.1 )
            
        if not cmds.objExists('%s.bulge' % btm_center_control):
            cmds.addAttr(btm_center_control, ln = 'bulge', k = True, dv = 1, min = 0.1)    
            
        top_left_control = self.zip_controls[increment][0][1]
        btm_left_control = self.zip_controls[increment][0][0]
        
        top_left_driver = self.control_dict[top_left_control][1]
        btm_left_driver = self.control_dict[btm_left_control][1]
                
        util.connect_multiply('%s.roll' % top_center_control, '%s.rotateX' % top_left_driver, percent)
        util.connect_multiply('%s.roll' % btm_center_control, '%s.rotateX' % btm_left_driver, -1*percent)
        
        cmds.connectAttr('%s.bulge' % top_center_control, '%s.scaleX' % top_left_driver)
        cmds.connectAttr('%s.bulge' % top_center_control, '%s.scaleY' % top_left_driver)
        cmds.connectAttr('%s.bulge' % top_center_control, '%s.scaleZ' % top_left_driver)
            
        cmds.connectAttr('%s.bulge' % btm_center_control, '%s.scaleX' % btm_left_driver)
        cmds.connectAttr('%s.bulge' % btm_center_control, '%s.scaleY' % btm_left_driver)
        cmds.connectAttr('%s.bulge' % btm_center_control, '%s.scaleZ' % btm_left_driver)
        
        """
        util.quick_driven_key('%s.bulge' % top_center_control, '%s.scaleX' % top_left_driver, [1,2], [1,percent*2])
        cmds.connectAttr('%s.scaleX' % top_left_driver, '%s.scaleY' % top_left_driver)
        cmds.connectAttr('%s.scaleX' % top_left_driver, '%s.scaleZ' % top_left_driver)
        
        util.quick_driven_key('%s.bulge' % btm_center_control, '%s.scaleX' % btm_left_driver, [1,2], [1,percent*2])
        cmds.connectAttr('%s.scaleX' % btm_left_driver, '%s.scaleY' % btm_left_driver)
        cmds.connectAttr('%s.scaleX' % btm_left_driver, '%s.scaleZ' % btm_left_driver)
        """
        """
        multiply = util.connect_multiply('%s.bulge' % top_center_control, '%s.scaleX' % top_left_driver, percent)
        cmds.connectAttr('%s.outputX' % multiply, '%s.scaleY' % top_left_control)
        cmds.connectAttr('%s.outputX' % multiply, '%s.scaleZ' % top_left_control)
        
        multiply = util.connect_multiply('%s.fatten' % btm_center_control, '%s.scaleX' % btm_left_driver, percent)
        cmds.connectAttr('%s.outputX' % multiply, '%s.scaleY' % btm_left_control)
        cmds.connectAttr('%s.outputX' % multiply, '%s.scaleZ' % btm_left_control)
        """
        
        if len(self.zip_controls[increment]) > 1: 
        
            top_right_control = self.zip_controls[increment][1][1]
            btm_right_control = self.zip_controls[increment][1][0]
            
            top_right_driver = self.control_dict[top_right_control][1]
            btm_right_driver = self.control_dict[btm_right_control][1]
            
            util.connect_multiply('%s.roll' % top_center_control, '%s.rotateX' % top_right_driver, percent)
            util.connect_multiply('%s.roll' % btm_center_control, '%s.rotateX' % btm_right_driver, -1*percent)
            
            cmds.connectAttr('%s.bulge' % top_center_control, '%s.scaleX' % top_right_driver)
            cmds.connectAttr('%s.bulge' % top_center_control, '%s.scaleY' % top_right_driver)
            cmds.connectAttr('%s.bulge' % top_center_control, '%s.scaleZ' % top_right_driver)
            
            cmds.connectAttr('%s.bulge' % btm_center_control, '%s.scaleX' % btm_right_driver)
            cmds.connectAttr('%s.bulge' % btm_center_control, '%s.scaleY' % btm_right_driver)
            cmds.connectAttr('%s.bulge' % btm_center_control, '%s.scaleZ' % btm_right_driver)
            
            """
            multiply = util.connect_multiply('%s.fatten' % top_center_control, '%s.scaleX' % top_right_driver, percent)
            cmds.connectAttr('%s.outputX' % multiply, '%s.scaleY' % top_right_control)
            cmds.connectAttr('%s.outputX' % multiply, '%s.scaleZ' % top_right_control)
        
            multiply = util.connect_multiply('%s.fatten' % btm_center_control, '%s.scaleX' % btm_right_driver, percent)
            cmds.connectAttr('%s.outputX' % multiply, '%s.scaleY' % btm_right_control)
            cmds.connectAttr('%s.outputX' % multiply, '%s.scaleZ' % btm_right_control)
            """
            """
            util.quick_driven_key('%s.bulge' % top_center_control, '%s.scaleX' % top_right_driver, [1,2], [1,percent*10])
            cmds.connectAttr('%s.scaleX' % top_right_driver, '%s.scaleY' % top_right_driver)
            cmds.connectAttr('%s.scaleX' % top_right_driver, '%s.scaleZ' % top_right_driver)
        
            util.quick_driven_key('%s.bulge' % btm_center_control, '%s.scaleX' % btm_right_driver, [1,2], [1,percent*10])
            cmds.connectAttr('%s.scaleX' % btm_right_driver, '%s.scaleY' % btm_right_driver)
            cmds.connectAttr('%s.scaleX' % btm_right_driver, '%s.scaleZ' % btm_right_driver)
            """
            
    def create_follow(self, follow_transform, increment, value):
        
        super(StickyLipRig, self).create_follow(follow_transform, increment, value)
        
        for control in self.main_controls:
            cmds.orientConstraint(self.follower_group, control[2])
            
        for control in self.corner_controls:
            cmds.orientConstraint(self.follower_group, control[1])
            
    def create(self):
        super(StickyLipRig, self).create()
        
        self._create_curves()
        
        self._cluster_curves()
        
        self._create_curve_joints()
        
        self._connect_curve_joints()
                
        self._connect_guide_clusters()
        
        self._create_main_controls()
        
        self._create_corner_controls()
        
       
class FaceCurveRig(rigs.JointRig):

    def __init__(self, description, side):
        
        super(FaceCurveRig, self).__init__(description, side)
        
        self.curve = None
        
        self.joint_dict = {}
        
        self.span_count = 4
        
    def _create_curve(self):
        
        self.curve = util.transforms_to_curve(self.joints, self.span_count, self.description)
        
        cmds.parent(self.curve, self.setup_group)
        
    def _cluster_curve(self):
        
        self.clusters = util.cluster_curve(self.curve, self.description, True)
        
        cmds.parent(self.clusters, self.setup_group)
        
    def _create_controls(self):
        
        for cluster in self.clusters:
            
            control = self._create_control()
            control.hide_scale_attributes()
            control.rotate_shape(90, 0, 0)
            
            util.MatchSpace(cluster, control.get()).translation_to_rotate_pivot()
            
            xform = util.create_xform_group(control.get())
            
            util.connect_translate(control.get(), cluster)
            
            cmds.parent(xform, self.control_group)
            
            
    def _create_sub_joint_controls(self):
        
        group = cmds.group(em = True, n = self._get_name('group', 'sub_controls'))
        
        cmds.parent(group, self.control_group)
        
        self.sub_control_group = group
        
        for joint in self.joints:
            
            joint_xform = self.joint_dict[joint]
            
            sub_control = self._create_control(sub = True)
            sub_control.rotate_shape(90, 0, 0)
            sub_control.scale_shape(.8,.8,.8)
            sub_control.hide_scale_attributes()
            
            util.MatchSpace(joint, sub_control.get())
            
            xform = util.create_xform_group(sub_control.get())
            
            util.connect_translate(joint_xform, xform)
                        
            util.connect_translate(sub_control.get(), joint)
            
            cmds.parent(xform, group)
            
    def _attach_joints_to_curve(self):
        
        for joint in self.joints:
            xform = util.create_xform_group(joint)
            
            self.joint_dict[joint] = xform
            
            util.attach_to_curve(xform, self.curve)
        
    def set_curve(self, curve_name):
        self.curve = curve_name
        
    def set_control_count(self, count):
        
        self.span_count = count - 1
        
        
    def create(self):
        super(FaceCurveRig, self).create()
        
        if not self.curve:
            self._create_curve()
        
        self._attach_joints_to_curve()
        
        self._cluster_curve()
                    
        self._create_controls()
        
        self._create_sub_joint_controls()      
     
class BrowRig(FaceCurveRig):
    
    def __init__(self, description, side):
        
        super(BrowRig, self).__init__(description, side)
        
        self.span_count = 3
        
class EyeLidRig(rigs.JointRig):
    
    def __init__(self, description, side):
        
        super(EyeLidRig, self).__init__(description, side)
        
        self.surface = None
        
        self.offset_group = None
        
        self.main_joint_dict = {}
        
        self.main_controls = []
        
    def _create_curve(self):
        
        self.curve = util.transforms_to_curve(self.joints, 4, self.description)
        
        self.sub_curve = util.transforms_to_curve(self.joints, 4, 'sub_' + self.description)
        
        cmds.parent(self.curve, self.setup_group)        
        cmds.parent(self.sub_curve, self.setup_group)
        
    def _cluster_curve(self):
        
        self.clusters = util.cluster_curve(self.curve, self.description)
        
        self.sub_cluster = util.cluster_curve(self.sub_curve, 'sub_' + self.description)
        
        cmds.parent(self.clusters, self.setup_group)
        cmds.parent(self.sub_cluster, self.setup_group)
        
    def _create_controls(self):
        
        inc = 0
        
        for cluster in self.clusters:
            
            control = self._create_control()
            control.hide_scale_attributes()
            control.rotate_shape(90, 0, 0)
            
            self.main_controls.append(control.get())
            
            sub_control = self._create_control(sub = True)
            sub_control.hide_scale_attributes()
            
            sub_control.scale_shape(0.5, .5, .5)
            sub_control.rotate_shape(90, 0, 0)
            
            cmds.parent(sub_control.get(), control.get())
            
            util.MatchSpace(cluster, control.get()).translation_to_rotate_pivot()
            
            xform = util.create_xform_group(control.get())
            driver = util.create_xform_group(control.get(), 'driver')
            
            util.connect_translate(control.get(), cluster)
            util.connect_translate(driver, cluster)
            util.connect_translate(sub_control.get(), self.sub_cluster[inc])
            
            cmds.parent(xform, self.control_group)
            
            inc += 1
        
    def _create_joint_offsets(self, joint):
        
        if not self.offset_group:
            self.offset_group = cmds.group(em = True, n = util.inc_name(self._get_name('group', 'offset')))
            cmds.parent(self.offset_group, self.setup_group)
            
        offset = cmds.spaceLocator(n = util.inc_name(self._get_name('locator')))[0]
        offset_sub = cmds.spaceLocator(n = util.inc_name(self._get_name('locator_sub')))[0]
        
        self.offset_dict[joint] = [offset, offset_sub]
        
        util.MatchSpace(joint, offset).translation()
        util.MatchSpace(joint, offset_sub).translation()
        
        cmds.parent(offset, self.offset_group)
        cmds.parent(offset_sub, self.offset_group)
        
        return offset, offset_sub        
        
    def _attach_joints_to_curve(self):
        
        for joint in self.joints:
            
            parent = cmds.listRelatives(joint, p = True)[0]
            xform = cmds.group(em = True, n = 'xform_%s' % joint)
            MatchSpace(joint, xform).translation()
            cmds.parent(xform, parent)
            
            offset = util.create_xform_group(joint, 'offset')
            driver = util.create_xform_group(joint, 'driver')
            
            if not joint in self.main_joint_dict:
                self.main_joint_dict[joint] = {}
            
                
            self.main_joint_dict[joint]['xform'] = xform
            self.main_joint_dict[joint]['driver'] = driver
            
            util.attach_to_curve(xform, self.curve)
            
            if self.surface:
                cmds.geometryConstraint(self.surface, xform)
                
            cmds.parent(offset, xform)
            
            util.attach_to_curve(driver, self.sub_curve)
            
            plus = cmds.createNode('plusMinusAverage', n = 'subtract_%s' % driver)
            
            input_x = util.get_attribute_input('%s.translateX' % driver)
            input_y = util.get_attribute_input('%s.translateY' % driver)
            input_z = util.get_attribute_input('%s.translateZ' % driver)
            
            value_x = cmds.getAttr('%s.translateX' % driver)
            value_y = cmds.getAttr('%s.translateY' % driver)
            value_z = cmds.getAttr('%s.translateZ' % driver)
            
            cmds.connectAttr(input_x, '%s.input3D[0].input3Dx' % plus)
            cmds.connectAttr(input_y, '%s.input3D[0].input3Dy' % plus)
            cmds.connectAttr(input_z, '%s.input3D[0].input3Dz' % plus)
            
            cmds.setAttr('%s.input3D[1].input3Dx' % plus, -1*value_x)
            cmds.setAttr('%s.input3D[1].input3Dy' % plus, -1*value_y)
            cmds.setAttr('%s.input3D[1].input3Dz' % plus, -1*value_z)
            
            util.disconnect_attribute( '%s.translateX' % driver)
            util.disconnect_attribute( '%s.translateY' % driver)
            util.disconnect_attribute( '%s.translateZ' % driver)
            
            cmds.connectAttr('%s.output3Dx' % plus, '%s.translateX' % driver)
            cmds.connectAttr('%s.output3Dy' % plus, '%s.translateY' % driver)
            cmds.connectAttr('%s.output3Dz' % plus, '%s.translateZ' % driver)
            
            
            
    def set_surface(self, surface_name):
        self.surface = surface_name    
        
    def create(self):
        super(EyeLidRig, self).create()
        
        self._create_curve()
        
        self._cluster_curve()
        
        self._create_controls()
        
        self._attach_joints_to_curve()
            
    def create_fade_row(self, joints, weight):
        
        if len(joints) != len(self.joints):
            util.warning('Row joint count and rig joint count do not match.')
  
        for inc in range(0, len(self.joints)):

            util.create_xform_group(joints[inc])
            offset = util.create_xform_group(joints[inc], 'offset')
            driver = util.create_xform_group(joints[inc], 'driver')
            cmds.parent(driver, w = True)
            
            main_xform = self.main_joint_dict[self.joints[inc]]['xform']
            main_driver = self.main_joint_dict[self.joints[inc]]['driver']
            
            util.connect_translate_multiply(main_xform, offset, weight, respect_value = True)
            util.connect_translate_multiply(main_driver, joints[inc], weight, respect_value = True)

            if self.surface:
                cmds.geometryConstraint(self.surface, offset)
                
            cmds.parent(driver, offset)
            
    def create_control_follow(self, control, increment, weight):
        
        main_control = self.main_controls[increment]
        parent = cmds.listRelatives(main_control, p = True)[0]
        
        util.connect_translate_multiply(control, parent, weight)

    
        
class EyeLidSphereRig(util.BufferRig):
    
    def __init__(self, description, side):
        super(EyeLidSphereRig, self).__init__(description, side)
        
        self.radius = 2
        self.axis = 'X'
        self.sections = 15
        self.curve = None
        self.ik_handles = []
        
        self.slice_group = None
    
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
            
        ik_groups = []
                
        if self.curve:
            inc = 1
            
            
            
            for ik_handle in self.ik_handles:
                
                group_ik = cmds.group(em = True, n = util.inc_name('group_ik%s_%s' % (inc,self._get_name())))
                util.MatchSpace(ik_handle, group_ik).translation()
                cmds.parent(ik_handle, group_ik)
                
                cmds.parent(group_ik, self.slice_group)
                
                util.attach_to_curve(group_ik, self.curve)
                
                ik_groups.append(group_ik)
                
                inc+=1

class EyeLidSphereRig2(util.BufferRig):
    
    def __init__(self, description, side):
        
        super(EyeLidSphereRig2, self).__init__(description, side)
        
        self.radius = 1
        self.horizontal_sections = 10
        self.vertical_sections = 10
        
        self.follicle_group = None
        self.first_folicle = None
        
        self.control_curves = []
                
    def _create_nurbs_sphere(self):
        
        self.surface = cmds.sphere( ch = False, o = True, po = False, ax = [0, 1, 0], radius = self.radius, nsp = 4, n = 'surface_%s' % util.inc_name(self._get_name()) )[0]
        
        util.MatchSpace(self.buffer_joints[0], self.surface).translation()
        cmds.refresh()
        cmds.parent(self.surface, self.top_group, r = True)
        
        
        cmds.rotate(90, 90, 0, self.surface, r = True, os = True)
        
        
    def _add_follicle(self, u_value, v_value, reverse, locator = False):
        
        
        if reverse:
            description = 'btm'
        if not reverse:
            description = 'top'
        
        if not self.follicle_group:
            self.follicle_group = cmds.group(em = True, n = self._get_name('groupFollicle'))
            cmds.parent(self.follicle_group, self.top_group)
            
            cmds.setAttr('%s.inheritsTransform' % self.follicle_group, 0)
        
        follicle = util.create_surface_follicle(self.surface, self._get_name(description), [u_value, v_value] )
        cmds.select(cl = True)
        
        
        joint = cmds.joint( n = util.inc_name( self._get_name('joint', description) ) )
        util.MatchSpace(follicle, joint).translation()
        
        cmds.parent(joint, follicle)
        cmds.makeIdentity(joint, jo = True, apply = True)
        
        locator_top = False
        locator_btm = False
        
        if locator:
            locator_top = cmds.spaceLocator(n = util.inc_name(self._get_name('locatorFollicle', description)))[0]
            cmds.setAttr('%s.localScaleX' % locator_top, .1)
            cmds.setAttr('%s.localScaleY' % locator_top, .1)
            cmds.setAttr('%s.localScaleZ' % locator_top, .1)
        
            util.MatchSpace(self.sub_locator_group, locator_top).translation()
            cmds.parent(locator_top, self.sub_locator_group)
            cmds.makeIdentity(locator_top, t = True, apply = True)  
            
            locator_btm = cmds.spaceLocator(n = util.inc_name(self._get_name('locatorBtmFollicle', description)))[0]
            cmds.setAttr('%s.localScaleX' % locator_btm, .1)
            cmds.setAttr('%s.localScaleY' % locator_btm, .1)
            cmds.setAttr('%s.localScaleZ' % locator_btm, .1)
        
            util.MatchSpace(self.sub_locator_group, locator_btm).translation()
            
            cmds.parent(locator_btm, self.sub_locator_group)
            cmds.makeIdentity(locator_btm, t = True, apply = True) 
            
            if not reverse:
                cmds.setAttr('%s.translateY' % locator_btm, 1)      
            
        
        
        return follicle, locator_top, locator_btm
        
    def _create_locator_group(self):
        
        top_group = cmds.group(em = True, n = util.inc_name(self._get_name('group', 'scale')))
        locator_group = cmds.group(em = True, n = util.inc_name(self._get_name('group', 'locator')))
        sub_locator_group = cmds.group(em = True, n = util.inc_name(self._get_name('group', 'sub_locator')))
        btm_sub_locator_group = cmds.group(em = True, n = util.inc_name(self._get_name('group', 'btmsub_locator')))
        
        #cmds.hide(locator_group)
        
        cmds.parent(sub_locator_group, locator_group)
        cmds.parent(btm_sub_locator_group, locator_group)
        cmds.parent(locator_group, top_group)
        util.MatchSpace(self.buffer_joints[0], locator_group).translation()
        
        cmds.setAttr('%s.scaleX' % locator_group, (self.radius*2) )
        cmds.setAttr('%s.scaleY' % locator_group, (self.radius*4) )
        #cmds.setAttr('%s.scaleZ' % locator_group, (self.radius*1) )
        
        cmds.setAttr('%s.translateX' % sub_locator_group, -0.5)
        cmds.setAttr('%s.translateY' % sub_locator_group, -0.5)
        cmds.setAttr('%s.translateZ' % sub_locator_group, 1*self.radius)
        
        self.top_group = top_group
        self.locator_group = locator_group
        self.sub_locator_group = sub_locator_group
        
    def _create_follicles(self, reverse):
        
        
        
        center_joint = self.joints[0]
        
        section_value = 1.0/self.horizontal_sections
        u_value = 0
        v_value = 0.5
        
        locators = []
        locator_top = None
        locator_btm = None
        
        for inc in range(0, self.horizontal_sections):
            
            #this is placed here so it skips the first increment...
            u_value += section_value
            
            if u_value > 0.9999999:
                continue
            
            sub_section_value = float(v_value)/self.vertical_sections 
            sub_v_value = v_value
            multiply_section_value = 1.0/self.vertical_sections
            
            if reverse:
                multiply_value = 0.0
            if not reverse:
                multiply_value = 1.0
            
            folicles = []
            
            group = cmds.group(em = True, n = util.inc_name(self._get_name('group', 'follicleSection%s' % (inc+1))))
            
            first_folicle = False
            
            for inc2 in range(0, self.vertical_sections+1):
                
                locator_state = False
                
                if not first_folicle:
                    locator_state = True
                
                folicle, locator_top, locator_btm = self._add_follicle(u_value, sub_v_value, reverse,locator_state,)
                
                if locator_top:
                    locators.append([locator_top, locator_btm])
                
                folicles.append(folicle)
                
                if not first_folicle:
                    first_folicle = folicle
                    
                cmds.parent(folicle, group)
            
            self.first_folicle = None
            self.last_folicle = None
            
            reverse_folicles = list(folicles)
            reverse_folicles.reverse()
            
            if not reverse:
                remap_front = cmds.createNode('remapValue', n = self._get_name('remapValueFront'))
                cmds.setAttr('%s.value[0].value_FloatValue' % remap_front, 1)
                cmds.setAttr('%s.value[1].value_FloatValue' % remap_front, 0)
                cmds.connectAttr('%s.parameterV' % folicles[0], '%s.inputValue' % remap_front)
            
                remap_back = cmds.createNode('remapValue', n = self._get_name('remapValueBack'))
                cmds.setAttr('%s.value[0].value_FloatValue' % remap_back, 1)
                cmds.setAttr('%s.value[1].value_FloatValue' % remap_back, 0)
                cmds.connectAttr('%s.parameterV' % reverse_folicles[0], '%s.inputValue' % remap_back)
            
                            
            for inc2 in range(0, len(folicles)):
                
                folicle = folicles[inc2]
                reverse_folicle = reverse_folicles[inc2]
                locator_top = locators[-1][0]
                locator_btm = locators[-1][1]
                
                if self.first_folicle and inc2 != len(folicles)-1:
                    
                    if reverse and inc2 != len(folicles)-1:
                        
                        plus = cmds.createNode('plusMinusAverage', n = util.inc_name(self._get_name('plusMinusAverage', 'comboBtm')))
                        
                        util.connect_multiply('%s.parameterV' % self.first_folicle, '%s.input1D[0]' % plus, multiply_value)
                        util.connect_multiply('%s.parameterV' % self.last_folicle, '%s.input1D[1]' % plus, (1-multiply_value) )
                        
                        cmds.connectAttr('%s.output1D' % plus, '%s.parameterV' % folicle)
                        
                        #util.connect_multiply('%s.parameterV' % self.first_folicle, '%s.parameterV' % folicle, multiply_value)
                        
                        
                    if not reverse:
                
                        
                        remap_front2 = cmds.createNode('remapValue', n = self._get_name('remapValueFront'))
                        #remap_back2 = cmds.createNode('remapValue', n = self._get_name('remapValueBack'))
        
                        util.connect_multiply('%s.outValue' % remap_front, '%s.inputValue' % remap_front2, multiply_value)
                        #util.connect_multiply('%s.outValue' % remap_back, '%s.inputValue' % remap_back2, (1-multiply_value))
                        
                        cmds.setAttr('%s.value[0].value_FloatValue' % remap_front2, 1)
                        cmds.setAttr('%s.value[1].value_FloatValue' % remap_front2, 0)

                        #cmds.setAttr('%s.value[0].value_FloatValue' % remap_back2, 1)
                        #cmds.setAttr('%s.value[1].value_FloatValue' % remap_back2, 0)
                        
                        plus = cmds.createNode('plusMinusAverage', n = util.inc_name(self._get_name('plusMinusAverage', 'combo')))
                        cmds.setAttr('%s.operation' % plus, 2)
                        cmds.connectAttr('%s.outValue' % remap_front2, '%s.input1D[0]' % plus)
                        #util.connect_multiply('%s.parameterV' % reverse_folicles[0], '%s.input1D[1]' % plus, (1-multiply_value))
                        util.connect_multiply('%s.outValue' % remap_back, '%s.input1D[1]' % plus, (1-multiply_value))
                        
                        #cmds.connectAttr('%s.outValue' % remap_back2, '%s.input1D[1]' % plus)
                        
                        cmds.connectAttr('%s.output1D' % plus, '%s.parameterV' % folicle)
                        
                        
                        #cmds.connectAttr('%s.outValue' % remap2, '%s.parameterV' % folicle)
                        
                    cmds.connectAttr('%s.parameterU' % self.first_folicle, '%s.parameterU' % folicle)
                    #util.connect_multiply('%s.parameterU' % self.first_folicle, '%s.parameterU' % folicle, multiply_value)
                    
                    
                if not self.first_folicle:
                    
                    self.first_folicle = folicle
                    self.last_folicle = reverse_folicle
                    
                    
                    cmds.setAttr('%s.translateX' % locator_top, u_value)
                    cmds.setAttr('%s.translateY' % locator_top, sub_v_value)
                    
                    cmds.setAttr('%s.translateX' % locator_btm, u_value)
                    
                   
                     
                    cmds.connectAttr('%s.translateX' % locator_top, '%s.parameterU' % folicle)
                    cmds.connectAttr('%s.translateY' % locator_top, '%s.parameterV' % folicle)
                    
                    
                    cmds.connectAttr('%s.translateY' % locator_btm, '%s.parameterV' % reverse_folicle)
                    
                    
                    
                    
                    #plus = cmds.createNode('plusMinusAverage', n = self._get_name('plusMinusAverage', 'combo'))
                    #cmds.connectAttr('%s.translateY' % locator_top, '%s.input1D[0]' % plus)
                    #util.connect_multiply('%s.translateY' % locator_btm, '%s.input1D[1]' % plus, sub_v_value )
                    #cmds.connectAttr('%s.output1D' % plus, '%s.parameterV' % reverse_folicle)
                
                if reverse:
                    sub_v_value -= sub_section_value
                    multiply_value += multiply_section_value
                        
                if not reverse:
                    sub_v_value += sub_section_value
                    multiply_value -= multiply_section_value
            
            cmds.parent(group, self.follicle_group)
            
            
        util.MatchSpace(center_joint, self.top_group).world_pivots()
        util.MatchSpace(center_joint, self.top_group).rotation()
        
        locator_group = cmds.group(em = True, n = util.inc_name(self._get_name('locators')))
        
        self.curve_locators = []
        
        for sub_locator in locators:
            
            locator = sub_locator[0]
            
            locator_world = cmds.spaceLocator(n = util.inc_name(self._get_name('locator')))[0]
            
            self.curve_locators.append(locator_world)
            
            cmds.setAttr('%s.localScaleX' % locator_world, .1)
            cmds.setAttr('%s.localScaleY' % locator_world, .1)
            cmds.setAttr('%s.localScaleZ' % locator_world, .1)
            
            util.MatchSpace(locator, locator_world).translation()
            
            cmds.parent(locator_world, locator_group)
            cmds.pointConstraint(locator_world, locator)
        
        
        
        cmds.parent(locator_group, self.setup_group)
        
    def _attach_locators_to_curve(self):
        curve = util.transforms_to_curve(self.curve_locators, 3, self._get_name())
        
        cmds.parent(curve, self.setup_group)
        
        self.control_curves.append(curve)
        
        for locator in self.curve_locators:
            util.attach_to_curve(locator, curve)
        
        
        
    def _create_controls(self):
        
        inc = 1
        
        for curve in self.control_curves:
            clusters = util.cluster_curve(curve, self._get_name(), join_ends = False)
            
            cluster_group = cmds.group(em = True, name = self._get_name('group', 'cluster%s' % curve.capitalize()))
            cmds.parent(clusters, cluster_group)
            
            cmds.parent(cluster_group, self.setup_group)
            
            
            if inc == 1:
                sub = False
                name = 'top'
            if inc == 2:
                sub = True
                name = 'btm'
                
            group = cmds.group(em = True, n = self._get_name('group', name))
            local_group = cmds.group(em = True, n = self._get_name('local_group', name))
            
            
            
            
            #group = cmds.group(em = True, n = util.inc_name(self._get_name('group', 'local')))
            cmds.parent(group, self.control_group)
            cmds.parent(local_group, self.setup_group)
                        
            for cluster in clusters:
                control = self._create_control(sub = sub)
                
                control.hide_scale_and_visibility_attributes()
                if inc == 1:
                    control.scale_shape(.1, .1, .1)
                if inc == 2:
                    control.scale_shape(.08, .08, .08)
                    
                xform = util.create_xform_group(control.get())
                
                util.MatchSpace(cluster, xform).translation_to_rotate_pivot()
                
                local, xform_local = util.constrain_local(control.get(), cluster, constraint = 'pointConstraint')
                #cmds.parent(xform_local, group)
                #cmds.pointConstraint(control.get(), cluster)
                
                
                
                cmds.parent(xform, self.control_group)
                
                cmds.parent(xform, group)
                cmds.parent(xform_local, local_group)
                
            inc += 1
        
        
        
    def set_horizontal_sections(self, int_value):
        self.horizontal_sections = int_value
        
    def set_vertical_sections(self, int_value):
        self.vertical_sections = int_value
    
    def set_radius(self, float_value):
        self.radius = float(float_value)
    
    def create(self):
        super(EyeLidSphereRig2, self).create()
        
        self._create_locator_group()
        self._create_nurbs_sphere()
        
        self._create_follicles(reverse = False)
        self._attach_locators_to_curve()
        
        self._create_follicles(reverse = True)
        self._attach_locators_to_curve()
        
        self._create_controls()
        
        cmds.parent(self.top_group, self.setup_group)
       
class MouthTweakers(util.Rig):


    def __init__(self, description, side):
        super(MouthTweakers, self).__init__(description, side)
        
        self.joint_control_group = None
        
        self.respect_side = True
        
        self.lip_curve = None
        self.muzzel_curve = None
        
        self.btm_lip_curve = None
        self.btm_muzzle_curve = None
        
        self.lip_locators = []
        self.muzzle_locators = []

    
    def _aim_locators(self, locators1, locators2):
    
        for inc in range(0, len(locators1)):
            if inc != len(locators1)-1:
                
                #pos = cmds.xform(locators1[inc+1], q = True, ws = True, t = True)
                
                #if pos[0] < -0.1 or pos[0] > 0.1:
                print locators1[inc], locators1[inc+1]
                aim = cmds.aimConstraint(locators1[inc+1], locators1[inc])[0]
                #cmds.setAttr('%s.worldUpType' % aim, 4)
                
                #if inc != 0:
                #    cmds.setAttr('%s.worldUpType' % aim, 2)
                #    cmds.connectAttr('%s.worldMatrix' % locators1[inc-1], '%s.worldUpMatrix' % aim)
            
                #pos = cmds.xform(locators2[inc+1], q = True, ws = True, t = True)
                
                #if pos[0] < -0.1 or pos[0] > 0.1:
                print locators2[inc], locators2[inc+1]
                aim = cmds.aimConstraint(locators2[inc+1], locators2[inc])[0]
                #cmds.setAttr('%s.worldUpType' % aim, 4)
                
                #if inc != 0:
                #    cmds.setAttr('%s.worldUpType' % aim, 2)
                #    cmds.connectAttr('%s.worldMatrix' % locators2[inc-1], '%s.worldUpMatrix' % aim)
                    
    def _add_joints(self, joints1, joints2):
    
        for inc in range(0, len(joints1)):
            cmds.select(cl = True)
            joint = cmds.joint( n = 'jnt' )
            cmds.parent( joint, joints1[inc], r = True )
    
        for inc in range(0, len(joints2)):
            cmds.select(cl = True)
            joint = cmds.joint( n = 'jnt'  )
            cmds.parent( joint, joints2[inc] , r = True)
    
    def _attach_scale(self, joints1, joints2, locators1, locators2):
    
    
        for inc in range(0, len(joints1)):

            child = cmds.listRelatives(joints1[inc], type = 'joint')[0]
            child2 = cmds.listRelatives(child, type = 'joint')[0]
            child3 = cmds.listRelatives(child2, type = 'joint')[0]    
    
            locator1,locator2 = util.create_distance_scale( joints1[inc], child3 )
    
            cmds.connectAttr('%s.scaleX' % joints1[inc], '%s.scaleX' % child)
            cmds.connectAttr('%s.scaleX' % joints1[inc], '%s.scaleX' % child2)
            cmds.connectAttr('%s.scaleX' % joints1[inc], '%s.scaleX' % child3)
    
            cmds.hide(locator1, locator2)
    
            cmds.parent(locator1, locators1[inc])
            cmds.parent(locator2, locators2[inc])
    
    
    def _attach_ik(self, locators1, locators2,  ik_handles, curve):
    
        for inc in range(0, len(locators1)):
            
            cmds.pointConstraint(locators2[inc], ik_handles[inc])
            
            if self.lip_curve:
                util.attach_to_curve(locators2[inc], curve)
    
    
    
    def _create_locators(self, joints1, joints2):
        
        locator1_gr = cmds.group(em = True, n = util.inc_name(self._get_name('group', 'locators1')))
        locator2_gr = cmds.group(em = True, n = util.inc_name(self._get_name('group', 'locators2')))
        
        cmds.parent(locator1_gr, self.setup_group)
        cmds.parent(locator2_gr, self.setup_group)
        
        locators1 = []
        locators2 = []
        
        self.sub_locators1 = []
        self.sub_locators2 = []
    
        for inc in range(0, len(joints1)):
            
            child = cmds.listRelatives(joints1[inc], type = 'joint')[0]
            child2 = cmds.listRelatives(child, type = 'joint')[0]
            child3 = cmds.listRelatives(child2, type = 'joint')[0]
            
            loc1 = cmds.spaceLocator(n = 'locator_%s' % joints1[inc])[0]
            cmds.setAttr('%s.localScaleX' % loc1, .1)
            cmds.setAttr('%s.localScaleY' % loc1, .1)
            cmds.setAttr('%s.localScaleZ' % loc1, .1)
            
            util.MatchSpace( joints1[inc] , loc1 ).translation_rotation()
    
            loc2 = cmds.spaceLocator(n = 'locator_%s' % joints2[inc])[0]
            
            cmds.setAttr('%s.localScaleX' % loc2, .1)
            cmds.setAttr('%s.localScaleY' % loc2, .1)
            cmds.setAttr('%s.localScaleZ' % loc2, .1)
    
            util.MatchSpace( child3 , loc2 ).translation_rotation()    
            
            locators1.append(loc1)
            locators2.append(loc2)
            
        cmds.parent(locators1, locator1_gr)
        cmds.parent(locators2, locator2_gr)
    
        return locators1, locators2
    
    def _create_joints_from_locators(self, locators, control = False):
        
        joints = []
        
        for locator in locators:
            cmds.select(cl = True)
            
            joint = cmds.joint(n = util.inc_name(self._get_name('joint', 'temp')))
            
            const = cmds.parentConstraint(locator, joint)
            cmds.delete(const)
            
            joints.append(joint)
            
        return joints
    
    def _create_joint(self, curve, length, control = False):
        
        param = util.get_parameter_from_curve_length(curve, length)
        position = util.get_point_from_curve_parameter(curve, param)
        
        point_on_curve = cmds.pointOnCurve(curve, parameter = param, ch = True)
        
        cmds.select(cl = True)
        joint = cmds.joint(p = position, n = util.inc_name(self._get_name('joint')))
        side = util.get_side(position, 0.1)
        
        joint = cmds.rename(joint, util.inc_name(joint[:-1] + side))
        
        if not control:
            return joint
        
        
        if not self.joint_control_group:
            group = cmds.group(em = True, n = self._get_name('controls', 'joint'))
            cmds.parent(group, self.control_group)
            self.joint_control_group = group
        
        if control:
        
        
            xform = util.create_xform_group(joint)
            #aim = util.create_xform_group(joint, 'aim')
            aim = None
            aim_control = None
            
            control = self._create_control(sub = True)
            control.rotate_shape(0,0,90)
            control.scale_shape(.09, .09, .09)
            
            control_name = control.get()
            
            control_name = cmds.rename(control_name, util.inc_name(control_name[:-1] + side))
            
            
            xform_control = util.create_xform_group(control_name)
            driver_control = util.create_xform_group(control_name, 'driver')
            
            cmds.connectAttr('%s.positionX' % point_on_curve, '%s.translateX' % xform_control)
            cmds.connectAttr('%s.positionY' % point_on_curve, '%s.translateY' % xform_control)
            cmds.connectAttr('%s.positionZ' % point_on_curve, '%s.translateZ' % xform_control)

            cmds.connectAttr('%s.positionX' % point_on_curve, '%s.translateX' % xform)
            cmds.connectAttr('%s.positionY' % point_on_curve, '%s.translateY' % xform)
            cmds.connectAttr('%s.positionZ' % point_on_curve, '%s.translateZ' % xform)
            
            #aim_control = util.create_xform_group(control_name, 'aim')
            
            util.MatchSpace(joint, xform_control).translation_rotation()
            
            
            #util.connect_translate(xform_control, xform)
            #util.connect_rotate(aim_control, aim)
            
            driver = util.create_xform_group(joint, 'driver')
            
            util.connect_translate(control_name, joint)
            util.connect_rotate(control_name, joint)
            util.connect_scale(control_name, joint)
            
            util.connect_translate(driver_control, driver)
            util.connect_rotate(driver_control, driver)
            util.connect_scale(driver_control, driver)
            
            cmds.parent(xform_control, self.joint_control_group)
            cmds.parent(xform, self.setup_group)
            
            return [joint, aim, xform,control_name, aim_control, xform_control]
    
    def _create_joints_on_curve(self, curve, section_count):
        print curve
        length = cmds.arclen(curve, ch = False)
        
        sections = section_count*2
        
        section_length = length/float(sections)
        start_offset = 0
        end_offset = length
        
        joints1 = []
        joints2 = []
        
        middle_joint = self._create_joint(curve, length/2, control = False)
        
        for inc in range(0, sections/2):
            
            joint1 = self._create_joint(curve, start_offset)
            joint2 = self._create_joint(curve, end_offset)
            
            start_offset += section_length
            end_offset -= section_length
            
            joints1.append(joint1)
            joints2.append(joint2)
             
        return joints1 + [middle_joint] + joints2
        
    def _create_joints_with_control_on_curve(self, curve, section_count = 5, control = False):
        
        
        print curve
        length = cmds.arclen(curve, ch = False)
        
        sections = section_count*2
        
        section_length = length/float(sections)
        start_offset = 0
        end_offset = length
        
        joints1 = []
        joints2 = []
        
        aim_controls1 = []
        aim_controls2 = []

        
        middle_joint, middle_aim, middle_xform, middle_control, middle_aim_control, middle_xform_control = self._create_joint(curve, length/2.0, control = True)
        
        for inc in range(0, sections/2):
        
            
            
            param1 = util.get_parameter_from_curve_length(curve, start_offset)
            position1 = util.get_point_from_curve_parameter(curve, param1)
            
            param2 = util.get_parameter_from_curve_length(curve, end_offset)
            position2 = util.get_point_from_curve_parameter(curve, param2)
            
            side1 = util.get_side(position1, 0.1)
            side2 = util.get_side(position2, 0.1)
            
            
            joint1, aim1, xform1, control1, aim_control1, xform_control1 = self._create_joint(curve, start_offset, control = True)    
            joint2, aim2, xform2, control2, aim_control2, xform_control2 = self._create_joint(curve, end_offset, control = True)
            
            """
            if len(joints1):
                
                aim = cmds.aimConstraint(aim_controls1[-1], aim_control1)
                
            if len(joints2):
                
                aim = cmds.aimConstraint(aim_control2, aim_controls2[-1])
            
            if inc == (sections/2)-1:
                
                aim = cmds.aimConstraint(aim_controls1[-1], aim_control1)    
                aim = cmds.aimConstraint(middle_aim_control, aim_control2)
            """
            start_offset += section_length
            end_offset -= section_length
        
            #aim_controls1.append(aim_control1)
            #aim_controls2.append(aim_control2)
            
            joints1.append(joint1)
            joints2.append(joint2)
            
        #aim = cmds.aimConstraint(aim_controls1[1], aim_controls1[0], aimVector = [-1,0,0])
                
        return joints1 + [middle_joint] + joints2
        
        
    
    
    def _create_joints(self, curve1, curve2, count = 11):
    
        joints_gr = cmds.group(em = True, n = util.inc_name(self._get_name('group', 'joints')))
        cmds.parent(joints_gr, self.setup_group)
    
        if self.lip_curve and self.muzzel_curve:
            
            muzzle_joints = self._create_joints_on_curve(curve1, 5)
            lip_joints = self._create_joints_with_control_on_curve(curve2, 5)
            
        if self.lip_locators and self.muzzle_locators:
            
            muzzle_joints = self._create_joints_from_locators(self.muzzle_locators)
            lip_joints = self._create_joints_from_locators(self.lip_locators)
            
            
 
        new_muzzle_joints = []
        new_lip_joints = []
        
        for inc in range(0, len(muzzle_joints)):
            
            joints = []    
            
            muzzle_joint = muzzle_joints[inc]
            
            joints.append(muzzle_joint)   
            
            aim = cmds.aimConstraint(lip_joints[inc], muzzle_joints[inc])[0]
            
            cmds.delete(aim)
            cmds.makeIdentity(muzzle_joints[inc], r = True, apply = True)
            
            end_joint = cmds.duplicate(lip_joints[inc], n = util.inc_name( 'joint_%s' % self._get_name('sub') ))[0]
            cmds.parent(end_joint, muzzle_joint)
            cmds.makeIdentity(end_joint, jo = True, apply = True)
            
    
            sub_joints = util.subdivide_joint(muzzle_joint, end_joint, name = self._get_name('sub'), count = 2)
            
              
            joints += sub_joints
            
            joints.append(end_joint)
            
            #cmds.parent(lip_joints[inc], end_joint)
            
            new_joints = []
        
            for joint in joints:
                
                new_joint = cmds.rename(joint, util.inc_name(self._get_name('joint', 'lip_span%s' % (inc+1))))
                new_joints.append(new_joint)
            
            lip_joint = cmds.rename(lip_joints[inc], util.inc_name(self._get_name('joint', 'lip_offset%s' % (inc+1))))
            new_joints.append(lip_joint)
            
            
            new_muzzle_joints.append( new_joints[0] )
            new_lip_joints.append( new_joints[-1] )
            
        
        
          
            
        
        muzzle_joints = new_muzzle_joints
        lip_joints = new_lip_joints
        cmds.parent(muzzle_joints, joints_gr)
        
        
        
        if self.lip_locators:
            
            print lip_joints[0], muzzle_joints
            cmds.parent(lip_joints[0], muzzle_joints[-1])
        
        return muzzle_joints, lip_joints
    
    def _create_ik(self, joints1, joints2 ):
    
        ik_gr = cmds.group(em = True, n = util.inc_name(self._get_name('group', 'ik')))
        cmds.parent(ik_gr, self.setup_group)
    
        ik_handles = []
    
        for inc in range(0, len(joints1)):
            
            ik = util.IkHandle('top_lip')
            ik.set_start_joint( joints1[inc] )
            
            #parent_joint = cmds.listRelatives(joints2[inc], p = True)[0]
            
            child = cmds.listRelatives(joints1[inc], type = 'joint')[0]
            child2 = cmds.listRelatives(child, type = 'joint')[0]
            child3 = cmds.listRelatives(child2, type = 'joint')[0]
            
            
            ik.set_end_joint( child3 )
            ik.create()
        
            ik_handles.append( ik.ik_handle )
    
        cmds.parent(ik_handles, ik_gr)
        cmds.hide(ik_gr)
        return ik_handles 

    def set_lip_curves(self, curve_lip, curve_muzzle):
        self.lip_curve = curve_lip
        self.muzzel_curve = curve_muzzle
    
    def set_lip_locators(self, lip_locators, muzzle_locators):
        self.lip_locators = lip_locators
        self.muzzle_locators = muzzle_locators

    def _create_controls(self, locators = []):
        
        inc = 1
        
        #control_curves = [self.lip_curve, self.muzzel_curve]
        
        #for curve in control_curves:
        
        if self.lip_curve and not locators:
            curve = self.lip_curve
            
            clusters = util.cluster_curve(curve, self._get_name(), join_ends = False)
        
            cluster_group = cmds.group(em = True, name = self._get_name('group', 'cluster%s' % curve.capitalize()))
            cmds.parent(clusters, cluster_group)
        
            cmds.parent(cluster_group, self.setup_group)
            
        if locators:
            clusters = locators
        
        group = cmds.group(em = True, n = util.inc_name(self._get_name('group', 'local')))
        cmds.parent(group, self.setup_group)
        
        if not locators:
            midpoint = len(clusters)/2.0
        
            sub_clusters = clusters[int(midpoint):]
        
            sub_clusters.reverse()
        
            clusters = clusters[:int(midpoint)] + sub_clusters
        
        for cluster in clusters:
            
            control = self._create_control()
            
            
            
            control.hide_scale_and_visibility_attributes()
            
            control.rotate_shape(90, 0, 0)
            control.scale_shape(.1, .1, .1)                
            
            if self.lip_locators:
                sub_control = self._create_control(sub = True)
                sub_control.rotate_shape(90, 0, 0)
                sub_control.scale_shape(.1, .1, .1)
                
                cmds.parent(sub_control.get(), control.get())
                
                
                
                
            
            if not self.lip_curve:
                util.MatchSpace(cluster, control.get()).translation()
            if self.lip_curve:
                util.MatchSpace(cluster, control.get()).translation_to_rotate_pivot()

            if self.side == 'C':
                if self.respect_side:
                    side = control.color_respect_side(center_tolerance = 0.1)
                
                if side != 'C':
                    control_name = cmds.rename(control.get(), util.inc_name(control.get()[0:-1] + side))
                    control = util.Control(control_name)
            
            xform = util.create_xform_group(control.get())
            driver = util.create_xform_group(control.get(), 'driver')
            
                
            local, xform_local = util.constrain_local(control.get(), cluster, constraint = 'pointConstraint')
            local_driver = util.create_xform_group(local, 'driver')
            
            util.connect_translate(driver, local_driver)
            
            cmds.parent(xform_local, group)
            #cmds.pointConstraint(control.get(), cluster)
            
            cmds.parent(xform, self.control_group)
            
        inc += 1

    def _attach_joints_to_locators(self, locators, joints, constraint = 'parent'):
        
        for inc in range(0, len(locators)):
            if constraint == 'parent':
                cmds.parentConstraint(locators[inc], joints[inc], mo = True)
            if constraint == 'orient':
                cmds.orientConstraint(locators[inc], joints[inc], mo = True)
    
    def _create_locator_controls(self, locators):
        
        for locator in locators:
            
            control = self._create_control(sub = True)
            control.scale_shape(.09, .09, .09)
            util.MatchSpace(locator, control.get()).translation_rotation()
            
            cmds.parent(control.get(), self.control_group)
            
            parent_locator = cmds.listRelatives(locator, p = True)[0]
            
            xform = util.create_xform_group(control.get())
            driver = util.create_xform_group(control.get(), 'driver')
            
            util.create_follow_group(parent_locator, xform)
            
            cmds.parent(locator, control.get())
    
    def create(self):
    
        super(MouthTweakers, self).create()
        
        #if self.muzzel_curve:
        #    self._create_joints_on_curve(self.muzzel_curve, 5)
        
        muzzle_joints, lip_joints = self._create_joints( self.muzzel_curve , self.lip_curve, 15) 
        
        
        ik_handles = self._create_ik( muzzle_joints, lip_joints)
        
        locators1, locators2 = self._create_locators( muzzle_joints, lip_joints)
        
        self._attach_ik(locators1, locators2, ik_handles, self.lip_curve)
        
        distance_locators = self._attach_scale( muzzle_joints, lip_joints, locators1, locators2)
        
        
        if self.lip_curve:
            self._create_controls()
        if not self.lip_curve:
            self._create_controls(locators2)
        
        """
        self._attach_joints_to_locators(self.sub_locators1, muzzle_joints)
        
        
        self._attach_joints_to_locators(self.sub_locators2, lip_joints)
        
        self._create_locator_controls(self.sub_locators2)
        """
     
     

class WeightFade(object):
    
    def __init__(self, mesh):
        self.mesh = mesh
        self.joints = []
        self.verts = []
        self.joint_vectors_2D = []
        self.vertex_vectors_2D = []
        
        self._store_verts()
        self.multiplier_weights = []
        self.zero_weights = True
        
    def _store_verts(self):
        self.verts = cmds.ls('%s.vtx[*]' % self.mesh, flatten = True)
    
    def _get_joint_index(self, joint):
        for inc in range(0, len(self.joints)):
            if self.joints[inc] == joint:
                return inc
            
    def _store_vertex_vectors(self):
        self.vertex_vectors_2D = []
        self.vertex_vectors_3D = []
        self.vertex_normals = []
        
        for vert in self.verts:
            position = cmds.xform(vert, q = True, ws = True, t = True)
            position_vector_3D = vtool.util.Vector(position)
            position_vector_2D = vtool.util.Vector2D(position[0], position[2])
            
            normal_vector = util.get_vertex_normal(vert)

            self.vertex_vectors_2D.append(position_vector_2D)
            self.vertex_vectors_3D.append(position_vector_3D)
            self.vertex_normals.append(normal_vector)
                
    def _store_joint_vectors(self):
        
        self.joint_vectors_2D = []
        
        for joint in self.joints:
            position = cmds.xform(joint, q = True, ws = True, t = True)
            
            position = (position[0], position[2])
            
            self.joint_vectors_2D.append(position)
    
    def _get_adjacent(self, joint):
        
        joint_index = self._get_joint_index(joint)
        
        joint_count = len(self.joints)
        
        if joint_index == 0:
            return [1]
        
        if joint_index == joint_count-1:
            return [joint_index-1]
        
        return [joint_index+1, joint_index-1]

    def _skin(self):
        
        skin = util.find_deformer_by_type(self.mesh, 'skinCluster')
        
        joints = self.joints
        
        if not skin:
            skin = cmds.skinCluster(self.mesh, self.joints[0], tsb = True)[0]
            joints = joints[1:]
        
        if self.zero_weights:
            util.set_skin_weights_to_zero(skin)
        
        for joint in joints:
            cmds.skinCluster(skin, e = True, ai = joint, wt = 0.0)
            
        return skin
        
    def _weight_verts(self, skin):
        
        vert_count = len(self.verts)
        
        progress = util.ProgressBar('weighting %s:' % self.mesh, vert_count)
        
        for inc in range(0, vert_count):
            
            
            joint_weights = self._get_vert_weight(inc)

            if joint_weights:
                cmds.skinPercent(skin, self.verts[inc], r = False, transformValue = joint_weights)
            
            progress.inc()
            progress.status('weighting %s: vert %s' % (self.mesh, inc))
            if progress.break_signaled():
                progress.end()
                break
        
        progress.end()
            
    def _get_vert_weight(self, vert_index):
        
        if not self.multiplier_weights:
            multiplier = 1
            
        if self.multiplier_weights:
            multiplier = self.multiplier_weights[vert_index]
            
            if multiplier == 0 or multiplier < 0.0001:
                return
        
        vertex_vector = self.vertex_vectors_2D[vert_index]
        vertex_vector_3D = self.vertex_vectors_3D[vert_index]
        vertex_normal = self.vertex_normals[vert_index]
        
        joint_weights = []
        joint_count = len(self.joints)
        weight_total = 0
        
        for inc in range(0, joint_count):
            
            if inc == joint_count-1:
                break
            
            start_vector = vtool.util.Vector2D( self.joint_vectors_2D[inc] )
            joint_position = cmds.xform(self.joints[inc], q = True, ws = True, t = True)
            joint_vector = vtool.util.Vector(joint_position)
            check_vector = joint_vector - vertex_vector_3D
            
            dot_value = vtool.util.get_dot_product(vertex_normal, check_vector)
            
            if dot_value >= 0:
                continue
            
            joint = self.joints[inc]
            next_joint = self.joints[inc+1]
            
            end_vector = vtool.util.Vector2D( self.joint_vectors_2D[inc+1])
            
            percent = vtool.util.closest_percent_on_line_2D(start_vector, end_vector, vertex_vector, False)
            
            if percent <= 0:
                weight_total+=1.0
                if not weight_total > 1:
                    joint_weights.append([joint, (1.0*multiplier)])
                continue
                    
            if percent >= 1 and inc == joint_count-2:
                weight_total += 1.0
                if not weight_total > 1:
                    joint_weights.append([next_joint, (1.0*multiplier)])
                continue
            
            if percent > 1 or percent < 0:
                continue
            
            weight_total += 1.0-percent
            if not weight_total > 1:
                joint_weights.append([joint, ((1.0-percent)*multiplier)])
                
            weight_total += percent
            if not weight_total > 1:
                joint_weights.append([next_joint, percent*multiplier])
                
        return joint_weights
                
    def set_joints(self, joints):
        self.joints = joints
    
    def set_mesh(self, mesh):
        self.mesh = mesh
        
    def set_multiplier_weights(self, weights):
        self.multiplier_weights = weights
        
    def set_weights_to_zero(self, bool_value):
        self.zero_weights = bool_value
        
        
    def run(self):
        if not self.joints:
            return
        
        self._store_vertex_vectors()
        self._store_joint_vectors()
        skin = self._skin()
        
        self._weight_verts(skin)
   

class AutoWeight2D(object):
    
    def __init__(self, mesh):
        self.mesh = mesh
        self.joints = []
        self.verts = []
        self.joint_vectors_2D = []
        self.vertex_vectors_2D = []
        
        self._store_verts()
        self.multiplier_weights = []
        self.zero_weights = True
        
    def _store_verts(self):
        self.verts = cmds.ls('%s.vtx[*]' % self.mesh, flatten = True)
    
    def _get_joint_index(self, joint):
        for inc in range(0, len(self.joints)):
            if self.joints[inc] == joint:
                return inc
            
    def _store_vertex_vectors(self):
        self.vertex_vectors_2D = []
        
        for vert in self.verts:
            position = cmds.xform(vert, q = True, ws = True, t = True)
            position_vector_2D = vtool.util.Vector2D(position[0], position[2])
            
            self.vertex_vectors_2D.append(position_vector_2D)
                
    def _store_joint_vectors(self):
        
        self.joint_vectors_2D = []
        
        for joint in self.joints:
            position = cmds.xform(joint, q = True, ws = True, t = True)
            
            #position = (position[0], position[2])
            position = (position[0], 0.0)
            
            self.joint_vectors_2D.append(position)
    
    def _get_adjacent(self, joint):
        
        joint_index = self._get_joint_index(joint)
        
        joint_count = len(self.joints)
        
        if joint_index == 0:
            return [1]
        
        if joint_index == joint_count-1:
            return [joint_index-1]
        
        return [joint_index+1, joint_index-1]

    def _skin(self):
        
        skin = util.find_deformer_by_type(self.mesh, 'skinCluster')
        
        joints = self.joints
        
        if not skin:
            skin = cmds.skinCluster(self.mesh, self.joints[0], tsb = True)[0]
            joints = joints[1:]
        
        if self.zero_weights:
            util.set_skin_weights_to_zero(skin)
        
        for joint in joints:
            cmds.skinCluster(skin, e = True, ai = joint, wt = 0.0)
            
        return skin
        
    def _weight_verts(self, skin):
        
        vert_count = len(self.verts)
        
        progress = util.ProgressBar('weighting %s:' % self.mesh, vert_count)
        
        for inc in range(0, vert_count):
            
            
            joint_weights = self._get_vert_weight(inc)

            if joint_weights:
                cmds.skinPercent(skin, self.verts[inc], r = False, transformValue = joint_weights)
            
            progress.inc()
            progress.status('weighting %s: vert %s' % (self.mesh, inc))
            if progress.break_signaled():
                progress.end()
                break
        
        progress.end()
            
    def _get_vert_weight(self, vert_index):
        
        if not self.multiplier_weights:
            multiplier = 1
            
        if self.multiplier_weights:
            multiplier = self.multiplier_weights[vert_index]
            
            if multiplier == 0 or multiplier < 0.0001:
                return
        
        vertex_vector = self.vertex_vectors_2D[vert_index]
                
        joint_weights = []
        joint_count = len(self.joints)
        weight_total = 0
        
        for inc in range(0, joint_count):
            
            if inc == joint_count-1:
                break
            
            start_vector = vtool.util.Vector2D( self.joint_vectors_2D[inc] )
                        
            joint = self.joints[inc]
            next_joint = self.joints[inc+1]
            
            end_vector = vtool.util.Vector2D( self.joint_vectors_2D[inc+1])
            
            percent = vtool.util.closest_percent_on_line_2D(start_vector, end_vector, vertex_vector, False)
            
            if percent <= 0:
                weight_total+=1.0
                if not weight_total > 1:
                    joint_weights.append([joint, (1.0*multiplier)])
                continue
                    
            if percent >= 1 and inc == joint_count-2:
                weight_total += 1.0
                if not weight_total > 1:
                    joint_weights.append([next_joint, (1.0*multiplier)])
                continue
            
            if percent > 1 or percent < 0:
                continue
            
            weight_total += 1.0-percent
            if not weight_total > 1:
                joint_weights.append([joint, ((1.0-percent)*multiplier)])
                
            weight_total += percent
            if not weight_total > 1:
                joint_weights.append([next_joint, percent*multiplier])
                
        return joint_weights
                
    def set_joints(self, joints):
        self.joints = joints
    
    def set_mesh(self, mesh):
        self.mesh = mesh
        
    def set_multiplier_weights(self, weights):
        self.multiplier_weights = weights
        
    def set_weights_to_zero(self, bool_value):
        self.zero_weights = bool_value
        
        
    def run(self):
        if not self.joints:
            return
        
        self._store_vertex_vectors()
        self._store_joint_vectors()
        skin = self._skin()
        
        self._weight_verts(skin)

             
                
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
        
        cmds.move( vector[0],vector[1],vector[2], dup_pos, os = True, r = True )
        
        neg_vector = -1 * vtool.util.Vector(vector)
        
        cmds.move( neg_vector.x, neg_vector.y, neg_vector.z, dup_neg, os = True, r = True )
        
        offset += section
        
        for dup in [dup_pos, dup_neg]:
            dup2 = cmds.duplicate(dup, n = util.inc_name('joint_guideEnd%s_%s' % (inc+1, description)))[0]
            
            cmds.move(edge_vector[0],edge_vector[1],edge_vector[2], dup2, os = True, r = True)
            
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

def rig_joint_helix(joints, description, top_parent, btm_parent):
    
    setup = cmds.group(em = True, n = util.inc_name('setup_%s' % description))
    
    handle = util.IkHandle(description)
    handle.set_solver(handle.solver_spline)
    handle.set_start_joint(joints[0])
    handle.set_end_joint(joints[-1])
    handle.create()
    
    cmds.parent(handle.ik_handle, handle.curve, setup)
    
    ffd, lattice, base = util.create_lattice(handle.curve, description, [2,2,2])
    
    pos1 = cmds.xform(joints[0], q = True, ws = True, t = True)
    pos2 = cmds.xform(joints[-1], q = True, ws = True, t = True)
    
    cmds.select(cl = True)
    joint1 = cmds.joint(p = pos1, n = 'joint_%s_top' % description)
    cmds.select(cl = True)
    joint2 = cmds.joint(p = pos2, n = 'joint_%s_btm' % description)
    cmds.joint(joint1, e = True, zso = True, oj = 'xyz', sao = 'yup')
    
    cmds.skinCluster([joint1, joint2], lattice, tsb = True)
    
    cmds.parent(joint1, joint2, setup)
    
    if top_parent:
        cmds.parent(joint1, top_parent)
    if btm_parent:
        cmds.parent(joint2, btm_parent)
    
    cmds.parent(lattice, base, setup)
    
    
    
    return setup

def create_mouth_joints(curve, section_count, description, parent):
    
    group = cmds.group(em = True, n = 'joints_%s' % description )
    
    cmds.parent(group, parent)
    
    length = cmds.arclen(curve, ch = False)
    
    sections = section_count*2
    
    section_length = length/float(sections)
    start_offset = 0
    end_offset = length
    
    joints1 = []
    joints2 = []
    
    middle_joint = create_curve_joint(curve, length/2, description)
    
    cmds.parent(middle_joint, group)
    
    for inc in range(0, sections/2):
        
        joint1 = create_curve_joint(curve, start_offset, description)
        joint2 = create_curve_joint(curve, end_offset, description)
        
        cmds.parent(joint1, joint2, group)
        
        start_offset += section_length
        end_offset -= section_length
        
        joints1.append(joint1)
        joints2.append(joint2)
    
    joints2.reverse()
    
    return joints1 + [middle_joint] + joints2

def create_brow_joints(curve, section_count, description, side, parent):
    
    group = cmds.group(em = True, n = util.inc_name('joints_%s_1_%s' % (description, side)) )
    
    cmds.parent(group, parent)
    
    length = cmds.arclen(curve, ch = False)
    
    sections = section_count
    
    section_length = length/float(sections-1)
    offset = 0
    
    joints = []
        
    for inc in range(0, sections):
    
        joint =create_curve_joint(curve, offset, description, side)
        
        cmds.parent(joint, group)
        
        offset += section_length
        
        joints.append(joint)
    
    return joints

def create_curve_joint(curve, length, description, side = None):
    
    
    
    param = util.get_parameter_from_curve_length(curve, length)
    position = util.get_point_from_curve_parameter(curve, param)
    
    cmds.select(cl = True)
    joint = cmds.joint(p = position, n = util.inc_name( 'joint_%s_1' % (description) ) )
    
    if side == None:
        side = util.get_side(position, 0.1)
    
    joint = cmds.rename(joint, util.inc_name(joint + '_%s' % side))
    
    return joint

def create_mouth_muscle(top_transform, btm_transform, description, joint_count = 3, guide_prefix = 'guide'):
    
    
    
    cmds.select(cl = True) 
    top_joint = cmds.joint(n = util.inc_name('guide_%s' % top_transform))
    cmds.select(cl = True)
    btm_joint = cmds.joint(n = util.inc_name('guide_%s' % btm_transform))
    
    util.MatchSpace(top_transform, top_joint).translation_rotation()
    util.MatchSpace(btm_transform, btm_joint).translation_rotation()
    
    aim = cmds.aimConstraint(btm_joint, top_joint)[0]
    cmds.delete(aim)
    
    cmds.makeIdentity(top_joint, r = True, apply = True)
    cmds.parent(btm_joint, top_joint)
    cmds.makeIdentity(btm_joint, jo = True, apply = True)

    sub_joints = util.subdivide_joint(top_joint, btm_joint, name = description, count = joint_count)

    ik = util.IkHandle('top_lip')
    ik.set_start_joint( top_joint )
    ik.set_end_joint( btm_joint )
    ik.create()
    
    cmds.parent(top_joint, top_transform)
    cmds.parent(ik.ik_handle, btm_transform)
    
    locator1,locator2 = util.create_distance_scale( top_joint, btm_joint )
    
    for joint in sub_joints:
        cmds.connectAttr('%s.scaleX' % top_joint, '%s.scaleX' % joint)
        cmds.connectAttr('%s.scaleY' % top_joint, '%s.scaleY' % joint)
        cmds.connectAttr('%s.scaleZ' % top_joint, '%s.scaleZ' % joint)
    
        cmds.hide(locator1, locator2)
    
    cmds.parent(locator1, top_transform)
    cmds.parent(locator2, btm_transform)
    
    return sub_joints, ik.ik_handle 