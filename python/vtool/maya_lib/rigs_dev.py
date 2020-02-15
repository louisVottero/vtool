# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

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
import rigs_util

    
class CurveTweakRig(rigs.CurveRig):
    
    def __init__(self, description, side):
        super(CurveTweakRig, self).__init__(description, side)
        
        self.local_group = []
        self.orient_transform = None
    
    def _create_center_group(self, description):
        
        center = space.get_center(self.curves)
        
        group = cmds.group(em = True, n = self._get_name('group', description))
        
        cmds.move(center[0], center[1], center[2], group, ws = True)
    
        return group
    
    def _cluster_curves(self):
        
        for curve in self.curves:
            
            clusters = deform.cluster_curve(curve, self._get_name())
            
        self.clusters = clusters
        
        cmds.parent(self.clusters, self.setup_group)
        
    def _create_controls(self):
        
        self.local_group = self._create_center_group('local')
        xform = space.create_xform_group(self.local_group)
        cmds.parent(xform, self.setup_group)
        
        if self.orient_transform:
            cmds.orientConstraint(self.orient_transform, xform)
        
        for cluster in self.clusters:
            control = self._create_control()
            
            xform = space.create_xform_group(control.get())
            space.MatchSpace(cluster, xform).translation_to_rotate_pivot()
            
            if self.orient_transform:
                cmds.orientConstraint(self.orient_transform, xform)
            
            local, local_xform = space.constrain_local(control.get(), cluster)
            
            cmds.parent(local_xform, self.local_group)
            
            control.hide_scale_attributes()
    
    def set_orient_transform(self, transform):
        self.orient_transform = transform
         
    def create(self):
        super(CurveTweakRig, self).create()
        
        self._cluster_curves()
        
        self._create_controls()
        
    def create_wire(self, mesh, falloff):
        
        for curve in self.curves:
            wire, curve = cmds.wire( mesh, w = curve, dds=[(0, falloff)], gw = False, n = 'wire_%s' % curve)
            cmds.setAttr('%s.rotation' % wire, 0)
    
    def create_main_control(self, control_shape = None):
        
        control = self._create_control('main')
        
        if control_shape:
            control.set_curve_type(control_shape)
        
        space.MatchSpace(self.local_group, control.get()).translation_rotation()
        
        space.create_xform_group(control.get())
        
        attr.connect_translate(control.get(), self.local_group)
        attr.connect_rotate(control.get(), self.local_group)
        
        xforms = cmds.listRelatives(self.control_group)
        cmds.parent(xforms, control.get())
        
        control.hide_scale_attributes()
    
          
        

class SurfaceFollowCurveRig(rigs.CurveRig):
    
    def __init__(self, description, side):
        super(SurfaceFollowCurveRig, self).__init__(description, side)
        
        self.surface = None
        self.join_start_end = False
    
    def _cluster_curve(self):
        
        clusters = deform.cluster_curve(self.curves[0], 'hat', True, join_start_end = self.join_start_end)
        return clusters
    
    def _create_follow_control(self, cluster):
        
        control = self._create_control()
        control.set_curve_type('cube')
        control.hide_rotate_attributes()
        control.hide_scale_attributes()
        
        sub_control = self._create_control(sub = True)
        sub_control.set_curve_type('cube')
        sub_control.scale_shape(.5, .5, .5)
        sub_control.hide_rotate_attributes()
        sub_control.hide_scale_attributes()
        
        match = space.MatchSpace(cluster, control.get())
        match.translation_to_rotate_pivot()
        
        xform_control = space.create_xform_group(control.get())
        cmds.parent(sub_control.get(), control.get(), r = True)
        
        local, xform = space.constrain_local(sub_control.get(), cluster, parent = True)
        
        cmds.parent(cluster, w = True)
        
        driver = space.create_xform_group(local, 'driver')
        
        attr.connect_translate(control.get(), driver)
        
        cmds.geometryConstraint(self.surface, driver)
        
        cmds.parent(cluster, local)
        
        cmds.parent(xform, self.setup_group)
                
    def _create_controls(self, clusters):
        
        for cluster in clusters:
            self._create_follow_control(cluster)
    
    def set_surface(self, surface_name):
        self.surface = surface_name
    
    def set_join_start_end(self, bool_value):
        self.join_start_end = bool_value
    
    def set_locator_only(self):
        pass
    
    def create(self):
        clusters = self._cluster_curve()
        
        self._create_controls(clusters)


class FkWithSubControlRig(rigs.FkRig):
    
    def _create_control(self, sub = False):
        
        self.control = super(rigs.FkRig, self)._create_control(sub = sub)
        self.control.scale_shape(self.control_size,self.control_size,self.control_size)
        
        self.control.hide_scale_and_visibility_attributes()
        
        if self.control_shape:
            self.control.set_curve_type(self.control_shape)
        
        self.current_xform_group = space.create_xform_group(self.control.get())
        driver = space.create_xform_group(self.control.get(), 'driver')
        
        self.drivers.append(driver)
        self.control = self.control.get()
        
        sub_control = self._create_sub_control(self.control)
        
        return sub_control
        
    def _create_sub_control(self, parent):
        
        self.last_control = self.control
        
        sub_control = super(rigs.FkRig, self)._create_control(sub = True)

        sub_control.scale_shape(self.control_size*0.9,self.control_size*0.9,self.control_size*0.9)
        
        sub_control.hide_scale_and_visibility_attributes()
        
        if self.control_shape:
            sub_control.set_curve_type(self.control_shape)
        
        space.create_xform_group(self.control)
        space.create_xform_group(self.control, 'driver')
        
        sub_control = sub_control.get()
        
        attr.connect_visibility('%s.subVisibility' % self.control, '%sShape' % sub_control, 1)
        
        cmds.parent(sub_control, self.control)
        
        return sub_control
    
class PointingFkCurveRig(rigs.SimpleFkCurveRig): 
    def _create_curve(self, span_count):
        
        if not self.curve:
        
            name = self._get_name()
            
            self.set_control_count(1)
            
            self.curve = geo.transforms_to_curve(self.joints, self.control_count - 1, name)
            
            self.curve = cmds.rebuildCurve( self.curve, 
                                   constructionHistory = False,
                                   replaceOriginal = True,
                                   rebuildType = 0,
                                   endKnots = 1,
                                   keepRange = 0,
                                   keepControlPoints = 0, 
                                   keepEndPoints = 1, 
                                   keepTangents = 0, 
                                   spans = 1,
                                   degree =3,
                                   name = name)[0]
            
            cmds.parent(self.curve, self.setup_group)
    
    def _create_clusters(self):
        
        name = self._get_name()
        
        cluster_group = cmds.group(em = True, n = core.inc_name('clusters_%s' % name))
        
        btm_handle = cmds.cluster('%s.cv[0]' % self.curve, n = name)[1]
        mid_handle = cmds.cluster('%s.cv[1:2]' % self.curve, n = name)[1]
    
        pos = cmds.xform('%s.cv[1]' % self.curve, q = True, ws = True, t = True)
        cmds.xform(mid_handle, ws = True, rp = pos, sp = pos)
    
        top_handle = cmds.cluster('%s.cv[3:4]' % self.curve, n = name)[1]
        
        self.clusters = [btm_handle, mid_handle, top_handle]
        
        cmds.parent(self.clusters, cluster_group)
        cmds.parent(cluster_group, self.setup_group)
    
    def _last_increment(self, control, current_transform):
        pass
    
    def create(self):
        super(PointingFkCurveRig, self).create()
        
        constraint_editor = space.ConstraintEditor()
        constraint = constraint_editor.get_constraint(self.clusters[-1], 'parentConstraint')
        
        cmds.delete(constraint)
        cmds.parentConstraint(self.controls[-1], self.clusters[-1])
        
        space.create_local_follow_group(self.sub_controls[-1], self.buffer_joints[-1], orient_only = False)
        cmds.setAttr('%s.subVisibility' % self.controls[-1], 1)
        space.create_follow_group(self.buffer_joints[-2], 'xform_%s' % self.sub_controls[-1])
        
        cmds.parent(self.end_locator, self.controls[-1])


class SimpleSplineIkRig(rigs.BufferRig):
    
    #to be removed, use TweakCurveRig instead.
    
    def __init__(self, name, side):
        super(SimpleSplineIkRig, self).__init__(name, side)
        self.curve = None
        self.cv_count = 10
    
    def _create_curve(self):

        name = self._get_name()
        
        joints = self.buffer_joints
        if not self.buffer_joints:
            joints = self.joints

        if not self.curve:
                
            self.curve = geo.transforms_to_curve(joints, len(joints), name)
            
            name = self._get_name()
            
            cmds.rebuildCurve(self.curve, 
                              spans = self.cv_count,
                              rpo = True,  
                              rt = 0, 
                              end = 1, 
                              kr = False, 
                              kcp = False, 
                              kep = True,  
                              kt = False,
                              d = 3)
            
            self.curve = cmds.rename(self.curve, 'curve_%s' % name)
            
            cmds.parent(self.curve, self.setup_group)
    
    def _create_spline_ik(self):
    
        if self.buffer_joints:
            joints = self.buffer_joints
        if not self.buffer_joints:
            joints = self.joints
            
        children = cmds.listRelatives(joints[-1])
        
        if children:
            cmds.parent(children, w = True)
        
        handle = cmds.ikHandle( sol = 'ikSplineSolver', 
                       ccv = False, 
                       pcv = False , 
                       sj = joints[0], 
                       ee = joints[-1], 
                       c = self.curve, n = 'splineIk_%s' % self._get_name())[0]
                       
        if children:
            cmds.parent(children, joints[-1])
            
        cmds.parent(handle, self.setup_group)
            
        if self.buffer_joints != self.joints:
            
            follow = space.create_follow_group(self.controls[0], self.buffer_joints[0])
            cmds.parent(follow, self.setup_group)
        
        cmds.rename(handle[1], 'effector_%s' % handle[0])
        
        """
        var = attr.MayaNumberVariable('twist')
        var.set_variable_type(var.TYPE_DOUBLE)
        var.create(self.controls[0])
        var.connect_out('%s.twist' % handle)
        """
    def set_curve(self, curve):
        self.curve = curve
    
    def set_cv_count(self, count):
        self.cv_count = count 
    
    def create(self):
        super(SimpleSplineIkRig, self).create()
        
        self._create_curve()
        self._create_spline_ik()

#--- Face

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
        
        self.sticky_control_group = cmds.group(em = True, n = core.inc_name(self._get_name('group', 'sticky_controls')))
        cmds.parent(self.sticky_control_group, self.control_group)
        
        self.follow_control_groups = {}
        
        self.local_orient = None 

    def _loop_joints(self):
        
        self.top_joint_group = cmds.group(em = True, n = core.inc_name( self._get_name('group', 'joints_top')))
        self.btm_joint_group = cmds.group(em = True, n = core.inc_name( self._get_name('group', 'joints_btm')))
        
        self.top_locator_group = cmds.group(em = True, n = core.inc_name( self._get_name('group', 'locators_top')))
        self.mid_locator_group = cmds.group(em = True, n = core.inc_name( self._get_name('group', 'locators_mid')))
        self.btm_locator_group = cmds.group(em = True, n = core.inc_name( self._get_name('group', 'locators_btm')))
        
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
                
                if not self.controls:
                    top_control1 = self.sub_controls[-1]
                    btm_control1 = self.sub_controls[-2]
                if self.controls:
                    top_control1 = self.controls[-1]
                    btm_control1 = self.controls[-2]
                    
                if inc == negative_inc:
                    self.locators.append([locators1])
                    self.zip_controls.append([[top_control1, btm_control1]])
                    break
                
                self._create_increment(negative_inc)
                
                locators2 = [self.top_locator, self.btm_locator]
                
                if not self.controls:
                    top_control2 = self.sub_controls[-1]
                    btm_control2 = self.sub_controls[-2]
                if self.controls:
                    top_control2 = self.controls[-1]
                    btm_control2 = self.controls[-2]\
                    
                self.locators.append([locators1, locators2])
                self.zip_controls.append([[top_control1, btm_control1],[top_control2,btm_control2]])
                
        self.side = self.first_side
           
    def _create_increment(self, inc):
        top_joint = self.top_joints[inc]
        btm_joint = self.btm_joints[inc]
        
        if self.respect_side:
            
            side = space.get_side(top_joint, self.respect_side_tolerance)
            self.side = side
            
        old_top_joint = top_joint
        old_btm_joint = btm_joint
        
        top_joint = cmds.duplicate(top_joint, po = True, n = core.inc_name(self._get_name('inputJoint', 'top')))[0]
        btm_joint = cmds.duplicate(btm_joint, po = True, n = core.inc_name(self._get_name('inputJoint', 'btm')))[0]
        
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
        
        space.MatchSpace(top_joint, self.top_locator[1]).translation_rotation()
        space.MatchSpace(btm_joint, self.btm_locator[1]).translation_rotation()
        
        midpoint = space.get_midpoint(top_joint, btm_joint)
        
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
        
        space.MatchSpace(self.top_locator[0], self.mid_top_locator[0]).translation_rotation()
        space.MatchSpace(self.btm_locator[0], self.mid_btm_locator[0]).translation_rotation()
        
        #top
        attr.connect_translate(top_xform, control_top[1])
        attr.connect_translate(control_top[2], top_driver)
        attr.connect_translate(control_top[0], top_joint)
        
        attr.connect_rotate(top_xform, control_top[1])
        attr.connect_rotate(control_top[2], top_driver)
        attr.connect_rotate(control_top[0], top_joint)
        
        attr.connect_scale(top_xform, control_top[1])
        attr.connect_scale(control_top[2], top_driver)
        attr.connect_scale(control_top[0], top_joint)
        
        #btm
        attr.connect_translate(btm_xform, control_btm[1])
        attr.connect_translate(control_btm[2], btm_driver)
        attr.connect_translate(control_btm[0], btm_joint)
        
        attr.connect_rotate(btm_xform, control_btm[1])
        attr.connect_rotate(control_btm[2], btm_driver)
        attr.connect_rotate(control_btm[0], btm_joint)
        
        attr.connect_scale(btm_xform, control_btm[1])
        attr.connect_scale(control_btm[2], btm_driver)
        attr.connect_scale(control_btm[0], btm_joint)
           
    def _create_follow(self, source_list, target, target_control ):
        
        constraint = cmds.parentConstraint(source_list, target)[0]
        cmds.setAttr('%s.interpType' % constraint, 2)
        constraint_editor = space.ConstraintEditor()    
        constraint_editor.create_switch(target_control, 'stick', constraint)
        
    def _create_sticky_control(self, transform, description):

        control = self._create_control(description)
        control.scale_shape(.8, .8, .8)

        control_name = control.get()
        
        
        space.MatchSpace(transform, control_name).translation_rotation()
                        
        control = control_name
        
        xform = space.create_xform_group(control)
        driver = space.create_xform_group(control, 'driver')
        
        cmds.parent(xform, self.sticky_control_group)
        
        return control, xform, driver
               
    def _group_joint(self, joint):
        
        xform = space.create_xform_group(joint)
        driver = space.create_xform_group(joint, 'driver')
        
        return xform, driver
                
    def _create_locator(self, description):
        
        locator = cmds.spaceLocator(n = core.inc_name(self._get_name('locator', description)))[0]
        
        xform = space.create_xform_group(locator)
        driver = space.create_xform_group(locator, 'driver')
        
        return locator, xform, driver
    
    def _create_follow_control_group(self, follow_control):
    
        if not follow_control in self.follow_control_groups.keys():
            
            group = cmds.group(em = True, n = 'follow_group_%s' % follow_control)
            space.MatchSpace(follow_control, group).translation_rotation()
            cmds.parent(group, self.follower_group)
            space.create_xform_group(group)
                        
            cmds.parentConstraint(follow_control, group)
                        
            #attr.connect_translate_plus(follow_control, group)
            #attr.connect_rotate(follow_control, group)
            
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
    
    def set_local_orient(self, transform):
        self.local_orient = transform
    
    def create(self):
        super(StickyRig, self).create()
        
        self._loop_joints()
        
    def create_follow(self, follow_transform, increment, value):
        
        if not self.follower_group:
            #self.local_follower_group = cmds.group(em = True, n = core.inc_name(self._get_name('group', 'local_follower')))
            self.follower_group = cmds.group(em = True, n = core.inc_name(self._get_name('group', 'follower')))
            
            #cmds.parent(self.local_follower_group, self.setup_group)
            cmds.parent(self.follower_group, self.setup_group)
            
            if self.local_orient:
                cmds.parent(self.follower_group, self.local_orient)
            
            #cmds.orientConstraint(local_follower_group, self.follower_group)
        
        follow_transform = self._create_follow_control_group(follow_transform)
        
        locators = self.locators[increment]
        
        top_locator1 = locators[0][0][1]
        btm_locator1 = locators[0][1][1]
        
        space.create_multi_follow([self.follower_group, follow_transform], top_locator1, top_locator1, value = value)
        space.create_multi_follow([self.follower_group, follow_transform], btm_locator1, btm_locator1, value = 1-value)
        
        if len(locators) > 1:
            top_locator2 = locators[1][0][1]
            btm_locator2 = locators[1][1][1]
        
            space.create_multi_follow([self.follower_group, follow_transform], top_locator2, top_locator2, value = value)
            space.create_multi_follow([self.follower_group, follow_transform], btm_locator2, btm_locator2, value = 1-value)
        
    def create_zip(self, attribute_control, increment, start, end, end_value = 1):
        
        left_over_value = 1.0 - end_value
        
        attr.create_title(attribute_control, 'ZIP')
        
        if not cmds.objExists('%s.zipL' % attribute_control):
            cmds.addAttr(attribute_control, ln = 'zipL', min = 0, max = 10, k = True)
            
        if not cmds.objExists('%s.zipR' % attribute_control):
            cmds.addAttr(attribute_control, ln = 'zipR', min = 0, max = 10, k = True)
            
        anim.quick_driven_key('%s.zipL' % attribute_control, '%s.stick' % self.zip_controls[increment][0][0], [start,end], [0,end_value])
        anim.quick_driven_key('%s.zipL' % attribute_control, '%s.stick' % self.zip_controls[increment][0][1], [start,end], [0,end_value])
                
        if left_over_value:
            anim.quick_driven_key('%s.zipR' % attribute_control, '%s.stick' % self.zip_controls[increment][0][0], [start,end], [0,left_over_value])
            anim.quick_driven_key('%s.zipR' % attribute_control, '%s.stick' % self.zip_controls[increment][0][1], [start,end], [0,left_over_value])
        
        right_increment = 1
        
        if len(self.zip_controls[increment]) == 1:
            right_increment = 0
        
        anim.quick_driven_key('%s.zipR' % attribute_control, '%s.stick' % self.zip_controls[increment][right_increment][0], [start,end], [0,end_value])
        anim.quick_driven_key('%s.zipR' % attribute_control, '%s.stick' % self.zip_controls[increment][right_increment][1], [start,end], [0,end_value])
        
        if left_over_value:
            anim.quick_driven_key('%s.zipL' % attribute_control, '%s.stick' % self.zip_controls[increment][right_increment][0], [start,end], [0,left_over_value])
            anim.quick_driven_key('%s.zipL' % attribute_control, '%s.stick' % self.zip_controls[increment][right_increment][1], [start,end], [0,left_over_value])

            
        
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
        
        self.control_count = 4
        
        self.main_control_group = cmds.group(em = True, n = core.inc_name(self._get_name('group', 'main_controls')))
        cmds.parent(self.main_control_group, self.control_group)
    
    def _create_curves(self):
        
        top_cv_count = len(self.top_joints) - 3
        #btm_cv_count = len(self.btm_joints) - 3
        
        self.top_curve = geo.transforms_to_curve(self.top_joints, self.control_count, self.description + '_top')
        self.btm_curve = geo.transforms_to_curve(self.btm_joints, self.control_count, self.description + '_btm')
        
        self.top_guide_curve = geo.transforms_to_curve(self.top_joints, top_cv_count, self.description + '_top_guide')
        self.btm_guide_curve = geo.transforms_to_curve(self.btm_joints, top_cv_count, self.description + '_btm_guide')
        
        cmds.parent(self.top_curve, self.setup_group)
        cmds.parent(self.btm_curve, self.setup_group)
        cmds.parent(self.top_guide_curve, self.btm_guide_curve, self.setup_group)
        
    def _cluster_curves(self):
        
        cluster_group = cmds.group(em = True, n = core.inc_name(self._get_name('group', 'clusters')))
        
        self.clusters_top = deform.cluster_curve(self.top_curve, self.description + '_top')
        self.clusters_btm = deform.cluster_curve(self.btm_curve, self.description + '_btm')
        
        self.clusters_guide_top = deform.cluster_curve(self.top_guide_curve, self.description + '_top_guide')
        self.clusters_guide_btm = deform.cluster_curve(self.btm_guide_curve, self.description + '_btm_guide')
        
        cmds.parent(self.clusters_top, self.clusters_btm, self.clusters_guide_top, self.clusters_guide_btm, cluster_group)
        cmds.parent(cluster_group, self.setup_group)
    
    def _create_curve_joints(self):
        
        self.top_tweak_joints, self.top_joint_group, top_controls =  rigs_util.create_joints_on_curve(self.top_curve, len(self.top_joints), self.description)
        self.btm_tweak_joints, self.btm_joint_group, btm_controls = rigs_util.create_joints_on_curve(self.btm_curve, len(self.btm_joints), self.description)
        
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
            attr.connect_translate_plus(self.top_tweak_joints[inc], driver)

            driver = cmds.listRelatives(left_btm_control, p = True)[0]
            attr.connect_translate_plus(self.btm_tweak_joints[inc], driver)
                
            if inc == negative_inc:
                break
            
            #do second part
            if len(controls) > 1:
                right_top_control = controls[1][1]
                right_btm_control = controls[1][0]            

                driver = cmds.listRelatives(right_top_control, p = True)[0]
                attr.connect_translate_plus(self.top_tweak_joints[negative_inc], driver)

                driver = cmds.listRelatives(right_btm_control, p = True)[0]
                attr.connect_translate_plus(self.btm_tweak_joints[negative_inc], driver)
            
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

            top_local, top_xform = space.constrain_local(top_locator, self.clusters_guide_top[inc])
            btm_local, btm_xform = space.constrain_local(btm_locator, self.clusters_guide_btm[inc])

            cmds.parent(top_xform, btm_xform, self.setup_group)
    
            if inc == negative_inc:
                break
            
            #do second part
            if len(locators) > 1:
                top_locator = controls[1][1]
                btm_locator = controls[1][0]
            
                top_locator = self.control_dict[top_locator][0]
                btm_locator = self.control_dict[btm_locator][0]
                
                top_local, top_xform = space.constrain_local(top_locator, self.clusters_guide_top[negative_inc])
                btm_local, btm_xform = space.constrain_local(btm_locator, self.clusters_guide_btm[negative_inc])
                
                cmds.parent(top_xform, btm_xform, self.setup_group)
            
            inc += 1
        
    def _create_main_controls(self):
        
        inc = 0
        
        cluster_count = len(self.clusters_top)
        

        
        for inc in range(0, cluster_count):
        
            
            if inc == cluster_count:
                break
            
            negative_inc = cluster_count - (inc+1)
            
            self._create_main_control(self.clusters_top[inc], self.top_guide_curve, 'top')
            self._create_main_control(self.clusters_btm[inc], self.btm_guide_curve, 'btm')

            if inc == negative_inc:
                break
            
            self._create_main_control(self.clusters_top[negative_inc], self.top_guide_curve, 'top')
            self._create_main_control(self.clusters_btm[negative_inc], self.btm_guide_curve, 'btm')
            
            inc += 1
                    
    def _create_main_control(self, cluster, attach_curve, description):
        
        control = self._create_control(description)
        control.hide_scale_attributes()
        control.rotate_shape(90, 0, 0)
            
        control = control.get()
        space.MatchSpace(cluster, control).translation_to_rotate_pivot()
        
        control = rigs_util.Control(control)
        side = control.color_respect_side(False, self.center_tolerance)
        
        if side == 'C':
            control = control.get()
        
        if side != 'C':
            control = cmds.rename(control.get(), core.inc_name(control.get()[0:-1] + side))
        
        cmds.parent(control, self.main_control_group)
        
        xform = space.create_xform_group(control)
        driver = space.create_xform_group(control, 'driver')
        
        if self.local_orient:
            attr.connect_rotate(self.local_orient, driver)
        
        geo.attach_to_curve(xform, attach_curve)
        
        local_control, local_xform = space.constrain_local(control, cluster)
        driver_local_control = space.create_xform_group(local_control, 'driver')
        
        attr.connect_translate(driver, driver_local_control)
        
        cmds.parent(local_xform, self.setup_group)
        
        self.main_controls.append([control, xform, driver])
        
        return control
        
    def _create_sticky_control(self, transform, description):
        
        if not self.sticky_control_group:
            self.sticky_control_group = cmds.group(em = True, n = core.inc_name(self._get_name('group', 'sticky_controls')))
            
            cmds.parent(self.sticky_control_group, self.control_group)
        
        control = self._create_control(description, sub = True)
        
        control.rotate_shape(90,0,0)
        control.scale_shape(.5, .5, .5)
        
        control_name = control.get()
        
        space.MatchSpace(transform, control_name).translation_rotation()
                        
        control = control_name
        
        xform = space.create_xform_group(control)
        driver = space.create_xform_group(control, 'driver')
        
        cmds.parent(xform, self.sticky_control_group)
        
        return control, xform, driver
        
    def _create_corner_controls(self):
               
        orig_side = self.side
        
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
            
            space.MatchSpace(top_control_driver, control.get()).translation_rotation()
            
            xform = space.create_xform_group(control.get())
            driver = space.create_xform_group(control.get(), 'driver')
            
            if self.local_orient:
                attr.connect_rotate(self.local_orient, driver)
            
            self.corner_controls.append([control.get(), xform])
            
            top_plus = attr.connect_translate_plus(control.get(), top_control_driver)
            btm_plus = attr.connect_translate_plus(control.get(), btm_control_driver)
            
            cmds.connectAttr('%s.translateX' % sub_control.get(), '%s.input3D[2].input3Dx' % top_plus)
            cmds.connectAttr('%s.translateY' % sub_control.get(), '%s.input3D[2].input3Dy' % top_plus)
            cmds.connectAttr('%s.translateZ' % sub_control.get(), '%s.input3D[2].input3Dz' % top_plus)
            
            cmds.connectAttr('%s.translateX' % sub_control.get(), '%s.input3D[2].input3Dx' % btm_plus)
            cmds.connectAttr('%s.translateY' % sub_control.get(), '%s.input3D[2].input3Dy' % btm_plus)
            cmds.connectAttr('%s.translateZ' % sub_control.get(), '%s.input3D[2].input3Dz' % btm_plus)
            
            geo.attach_to_curve(xform, self.top_guide_curve)
            
        self.side = orig_side
        
    def set_control_count(self, int_value):
        self.control_count = int_value
        
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
        
            attr.connect_translate_multiply(corner_control, top_control_driver, value)
            attr.connect_translate_multiply(corner_control, btm_control_driver, value)
        
    def create_roll(self, increment, percent):
        
        top_center_control, top_center_xform, top_center_driver = self.main_controls[-2]
        btm_center_control, btm_center_xform, btm_center_driver = self.main_controls[-1]

        attr.create_title(top_center_control, 'LIP')
        
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
                
        attr.connect_multiply('%s.roll' % top_center_control, '%s.rotateX' % top_left_driver, percent)
        attr.connect_multiply('%s.roll' % btm_center_control, '%s.rotateX' % btm_left_driver, -1*percent)
        
        cmds.connectAttr('%s.bulge' % top_center_control, '%s.scaleX' % top_left_driver)
        cmds.connectAttr('%s.bulge' % top_center_control, '%s.scaleY' % top_left_driver)
        cmds.connectAttr('%s.bulge' % top_center_control, '%s.scaleZ' % top_left_driver)
            
        cmds.connectAttr('%s.bulge' % btm_center_control, '%s.scaleX' % btm_left_driver)
        cmds.connectAttr('%s.bulge' % btm_center_control, '%s.scaleY' % btm_left_driver)
        cmds.connectAttr('%s.bulge' % btm_center_control, '%s.scaleZ' % btm_left_driver)
        
        if len(self.zip_controls[increment]) > 1: 
        
            top_right_control = self.zip_controls[increment][1][1]
            btm_right_control = self.zip_controls[increment][1][0]
            
            top_right_driver = self.control_dict[top_right_control][1]
            btm_right_driver = self.control_dict[btm_right_control][1]
            
            attr.connect_multiply('%s.roll' % top_center_control, '%s.rotateX' % top_right_driver, percent)
            attr.connect_multiply('%s.roll' % btm_center_control, '%s.rotateX' % btm_right_driver, -1*percent)
            
            cmds.connectAttr('%s.bulge' % top_center_control, '%s.scaleX' % top_right_driver)
            cmds.connectAttr('%s.bulge' % top_center_control, '%s.scaleY' % top_right_driver)
            cmds.connectAttr('%s.bulge' % top_center_control, '%s.scaleZ' % top_right_driver)
            
            cmds.connectAttr('%s.bulge' % btm_center_control, '%s.scaleX' % btm_right_driver)
            cmds.connectAttr('%s.bulge' % btm_center_control, '%s.scaleY' % btm_right_driver)
            cmds.connectAttr('%s.bulge' % btm_center_control, '%s.scaleZ' % btm_right_driver)
            
    def create_follow(self, follow_transform, increment, value):
        
        super(StickyLipRig, self).create_follow(follow_transform, increment, value)
        
    def create(self):
        super(StickyLipRig, self).create()
        
        self._create_curves()
        
        self._cluster_curves()
        
        self._create_curve_joints()
        
        self._connect_curve_joints()
                
        self._connect_guide_clusters()
        
        self._create_main_controls()
        
        self._create_corner_controls()
        
class FaceSquashRig(rigs.JointRig):
    
    def __init__(self, description, side):
        super(FaceSquashRig, self).__init__(description, side)
        
        self.surface = None
        self.cluster_handles = []
        self.locators = []
    
    def _create_ribbon(self):
        
        self.surface = geo.transforms_to_curve(self.joints, 3, self.description)
        
        geo.transforms_to_curve
        
        cmds.parent(self.surface, self.setup_group)
        
    def _cluster_surface(self):
        
        cluster_surface = deform.ClusterCurve(self.surface, self.description)
        
        cluster_surface.create()
        
        self.cluster_handles = cluster_surface.get_cluster_handle_list()
        
        cmds.parent(self.cluster_handles, self.setup_group)
        
    def _attach_joints(self):
        
        ik = space.IkHandle(self.description)
        
        ik.set_joints(self.joints)
        ik.set_curve(self.surface)
        ik.set_solver(ik.solver_spline)
        ik.create()
        
        cmds.parent(ik.ik_handle, self.setup_group)
        
    def _create_locators(self):
        
        locators = []
        
        for handle in self.cluster_handles:
            
            locator = cmds.spaceLocator(n = core.inc_name( self._get_name('locator') ) )[0]
            
            space.MatchSpace(handle, locator).translation_to_rotate_pivot()
            
            xform = space.create_xform_group(locator)
            
            cmds.pointConstraint(locator, handle)
            
            cmds.parent(xform, self.setup_group)
            
            locators.append(locator)

        attr.connect_translate_multiply(locators[0], locators[1], .95)
        attr.connect_translate_multiply(locators[0], locators[2], .8)
        attr.connect_translate_multiply(locators[0], locators[3], .4)
        attr.connect_translate_multiply(locators[0], locators[4], .1)
        
        attr.connect_translate_multiply(locators[-1], locators[4], .8)
        attr.connect_translate_multiply(locators[-1], locators[3], .5)
        attr.connect_translate_multiply(locators[-1], locators[2], .2)
        attr.connect_translate_multiply(locators[-1], locators[1], .05)
        
        self.locators = locators
    
    def _create_controls(self):
        
        top_control = self._create_control()
        top_control.hide_scale_attributes()
        
        space.MatchSpace(self.locators[0], top_control.get() ).translation_rotation()
        
        btm_control = self._create_control()
        btm_control.hide_scale_attributes()
        
        space.MatchSpace(self.locators[-1], btm_control.get() ).translation_rotation()
        
        space.create_xform_group(top_control.get())
        space.create_xform_group(btm_control.get())
        
        top_local, top_xform = space.constrain_local(top_control.get(), self.locators[0] )
        btm_local, btm_xform = space.constrain_local(btm_control.get(), self.locators[-1] )
        
        cmds.parent(top_xform, self.setup_group)
        cmds.parent(btm_xform, self.setup_group)
        
    def create(self):
        super(FaceSquashRig, self).create()
        
        self._create_ribbon()
        
        self._cluster_surface()
        
        self._create_locators()
        
        self._attach_joints()
        
        rigs_util.create_spline_ik_stretch(self.surface, self.joints, self.locators[0], create_bulge = False)
        
        self._create_controls()
        
    def set_scale_bulge(self, increment, squash_value, stretch_value):
        
        joint = self.joints[increment]
        
        anim.quick_driven_key('%s.scaleX' % joint, '%s.scaleY' % joint, [1,0.5, 2], [1, squash_value, stretch_value])
        cmds.connectAttr('%s.scaleY' % joint, '%s.scaleZ' % joint)
       
class FaceCurveRig(rigs.JointRig):

    def __init__(self, description, side):
        
        super(FaceCurveRig, self).__init__(description, side)
        
        self.curve = None
        
        self.joint_dict = {}
        
        self.span_count = 4
        
        self.respect_side = False
        
        self.sub_controls_create = True
        
        self.local_controls = []
        self.main_controls = []
        
    def _create_curve(self):
        
        self.curve = geo.transforms_to_curve(self.joints, self.span_count, self.description)

        cmds.parent(self.curve, self.setup_group)
        
    def _cluster_curve(self):
        
        self.clusters = deform.cluster_curve(self.curve, self.description, True, last_pivot_end=True)
        
        cmds.parent(self.clusters, self.setup_group)
        
    def _create_main_control(self, cluster):
        
        control = self._create_control()
        control.hide_scale_attributes()
        control.rotate_shape(90, 0, 0)
                
        space.MatchSpace(cluster, control.get()).translation_to_rotate_pivot()
                
        space.create_xform_group(control.get())
        driver = space.create_xform_group(control.get(), 'driver')
                
        local, local_xform = space.constrain_local(control.get(), cluster)
        local_driver = space.create_xform_group(local, 'driver')
        
        attr.connect_translate(driver, local_driver)
        
        cmds.parent(local_xform, self.setup_group)
        
        self.local_controls.append([local, local_driver])
        self.main_controls.append([control.get(), driver])
        
    def _create_controls(self):
        
        if not self.respect_side:

            for cluster in self.clusters:        
                self._create_main_control(cluster)
                
        if self.respect_side:
            cluster_count = len(self.clusters)
            
            orig_side = self.side
            
            for inc in range(0, cluster_count):

                negative_inc = cluster_count - (inc+1)    
                
                if inc == cluster_count:
                    break
                
                side = space.get_side(self.clusters[inc], 0.1)
                self.side = side
                
                self._create_main_control(self.clusters[inc])
                
                if inc == negative_inc:
                    break
            
                side = space.get_side(self.clusters[negative_inc], 0.1)
                self.side = side
            
                self._create_main_control(self.clusters[negative_inc])
            
                inc += 1
                
            self.side = orig_side
                
    def _create_sub_control(self, joint, joint_xform, parent):
        
        sub_control = self._create_control(sub = True)
        sub_control.rotate_shape(90, 0, 0)
        sub_control.scale_shape(.8,.8,.8)
        
        space.MatchSpace(joint, sub_control.get())
        
        xform = space.create_xform_group(sub_control.get())
        
        
        attr.connect_translate(joint_xform, xform)
                    
        attr.connect_translate(sub_control.get(), joint)
        attr.connect_rotate(sub_control.get(), joint)
        attr.connect_scale(sub_control.get(), joint)
        
        cmds.parent(xform, parent)
            
    def _create_sub_joint_controls(self):
        
        group = cmds.group(em = True, n = self._get_name('group', 'sub_controls'))
        
        cmds.parent(group, self.control_group)
        
        self.sub_control_group = group
        
        if not self.respect_side:
            
            for joint in self.joints:
            
                joint_xform = self.joint_dict[joint]
                self._create_sub_control(joint, joint_xform, group)
        
        if self.respect_side:
            
            joint_count = len(self.joints)
            
            orig_side = self.side
            
            for inc in range(0, joint_count):
            
                negative_inc = joint_count - (inc+1)    
                
                if inc == joint_count:
                    break
                
                if inc > negative_inc:
                    break
                
                side = space.get_side(self.joints[inc], 0.1)
                self.side = side
                
                joint_xform = self.joint_dict[self.joints[inc]]
                self._create_sub_control(self.joints[inc], joint_xform, group)
                
                if inc == negative_inc:
                    break
            
                side = space.get_side(self.joints[negative_inc], 0.1)
                self.side = side
            
                joint_xform = self.joint_dict[self.joints[negative_inc]]
                self._create_sub_control(self.joints[negative_inc], joint_xform, group)
            
                inc += 1
                
            self.side = orig_side
            
    def _attach_joints_to_curve(self):
        
        for joint in self.joints:
            xform = space.create_xform_group(joint)
            
            self.joint_dict[joint] = xform
            
            geo.attach_to_curve(xform, self.curve)
        
    def set_curve(self, curve_name):
        self.curve = curve_name
        
    def set_control_count(self, count):
        
        self.span_count = count - 1
        
    def set_create_sub_controls(self, bool_value):
        self.sub_controls_create = bool_value
        
    def set_respect_side(self, bool_value):
        self.respect_side = bool_value
        
    def create(self):
        super(FaceCurveRig, self).create()
        
        if not self.curve:
            self._create_curve()
        
        self._attach_joints_to_curve()
        
        self._cluster_curve()
                    
        self._create_controls()
        
        if self.sub_controls_create:
            self._create_sub_joint_controls()
            
    def create_control_follow(self, control, increment, weight):
        
        driver = self.main_controls[increment][1]
                
        attr.connect_translate_multiply(control, driver, weight)
              
        
class BrowRig(FaceCurveRig):
    
    def __init__(self, description, side):
        
        super(BrowRig, self).__init__(description, side)
        
        self.span_count = 4
        
    def _create_curve(self):
        
        self.curve = geo.transforms_to_curve(self.joints, self.span_count, self.description)
        
        if self.span_count >= 3:
            cmds.delete(['%s.cv[1]' % self.curve,'%s.cv[5]' % self.curve])
        
        cmds.parent(self.curve, self.setup_group)
        
    def _cluster_curve(self):
        
        
        if self.span_count >= 3:
            self.clusters = deform.cluster_curve(self.curve, self.description)
            
        if self.span_count == 2:
            self.clusters = deform.cluster_curve(self.curve, self.description, join_ends = True)
        
        cmds.parent(self.clusters, self.setup_group)
        
class EyeLidRig(rigs.JointRig):
    
    def __init__(self, description, side):
        
        super(EyeLidRig, self).__init__(description, side)
        
        self.surface = None
        
        self.offset_group = None
        
        self.main_joint_dict = {}
        self.row_joint_dict = {}
        self.main_controls = []
        
    def _create_curve(self):
        
        self.curve = geo.transforms_to_curve(self.joints, 4, self.description)
        
        self.sub_curve = geo.transforms_to_curve(self.joints, 4, 'sub_' + self.description)
        
        cmds.parent(self.curve, self.setup_group)        
        cmds.parent(self.sub_curve, self.setup_group)
        
    def _cluster_curve(self):
        
        self.clusters = deform.cluster_curve(self.curve, self.description)
        
        self.sub_cluster = deform.cluster_curve(self.sub_curve, 'sub_' + self.description)
        
        cmds.parent(self.clusters, self.setup_group)
        cmds.parent(self.sub_cluster, self.setup_group)
        
    def _create_controls(self):
        
        inc = 0
        
        for cluster in self.clusters:
            
            control = self._create_control()
            control.hide_scale_attributes()
            control.rotate_shape(90, 0, 0)
            
            self.main_controls.append(control.get())
            
            if self.surface:
                sub_control = self._create_control(sub = True)
                sub_control.hide_scale_attributes()
                
                sub_control.scale_shape(0.5, .5, .5)
                sub_control.rotate_shape(90, 0, 0)
            
                cmds.parent(sub_control.get(), control.get())
                
                space.create_xform_group(sub_control.get())
                sub_driver = space.create_xform_group(sub_control.get(), 'driver')
                
                attr.connect_translate(sub_control.get(), self.sub_cluster[inc])
                attr.connect_translate(sub_driver, self.sub_cluster[inc])
            
            space.MatchSpace(cluster, control.get()).translation_to_rotate_pivot()
            
            xform = space.create_xform_group(control.get())
            driver = space.create_xform_group(control.get(), 'driver')
            
            attr.connect_translate(control.get(), cluster)
            attr.connect_translate(driver, cluster)
            
            inc += 1
                
    def _attach_joints_to_curve(self):
        
        for joint in self.joints:
            
            parent = cmds.listRelatives(joint, p = True)[0]
            xform = cmds.group(em = True, n = 'xform_%s' % joint)
            space.MatchSpace(joint, xform).translation()
            cmds.parent(xform, parent)
            
            offset = space.create_xform_group(joint, 'offset')
            driver = space.create_xform_group(joint, 'driver')
            
            if not joint in self.main_joint_dict:
                self.main_joint_dict[joint] = {}
                        
            self.main_joint_dict[joint]['xform'] = xform
            self.main_joint_dict[joint]['driver'] = driver
            
            geo.attach_to_curve(xform, self.curve)
            
            if self.surface:
                cmds.geometryConstraint(self.surface, xform)
                
            geo.attach_to_curve(driver, self.sub_curve)
            
            plus = cmds.createNode('plusMinusAverage', n = 'subtract_%s' % driver)
            
            input_x = attr.get_attribute_input('%s.translateX' % driver)
            input_y = attr.get_attribute_input('%s.translateY' % driver)
            input_z = attr.get_attribute_input('%s.translateZ' % driver)
            
            value_x = cmds.getAttr('%s.translateX' % driver)
            value_y = cmds.getAttr('%s.translateY' % driver)
            value_z = cmds.getAttr('%s.translateZ' % driver)
            
            cmds.connectAttr(input_x, '%s.input3D[0].input3Dx' % plus)
            cmds.connectAttr(input_y, '%s.input3D[0].input3Dy' % plus)
            cmds.connectAttr(input_z, '%s.input3D[0].input3Dz' % plus)
            
            cmds.setAttr('%s.input3D[1].input3Dx' % plus, -1*value_x)
            cmds.setAttr('%s.input3D[1].input3Dy' % plus, -1*value_y)
            cmds.setAttr('%s.input3D[1].input3Dz' % plus, -1*value_z)
            
            attr.disconnect_attribute( '%s.translateX' % driver)
            attr.disconnect_attribute( '%s.translateY' % driver)
            attr.disconnect_attribute( '%s.translateZ' % driver)
            
            cmds.connectAttr('%s.output3Dx' % plus, '%s.translateX' % driver)
            cmds.connectAttr('%s.output3Dy' % plus, '%s.translateY' % driver)
            cmds.connectAttr('%s.output3Dz' % plus, '%s.translateZ' % driver)

            cmds.parent(offset, xform)
            
            
    def set_surface(self, surface_name):
        self.surface = surface_name    
        
    def create(self):
        super(EyeLidRig, self).create()
        
        self._create_curve()
        
        self._cluster_curve()
        
        self._create_controls()
        
        self._attach_joints_to_curve()
            
    def create_fade_row(self, joints, weight, ignore_surface = False):
        
        if len(joints) != len(self.joints):
            cmds.warning('Row joint count and rig joint count do not match.')
  
        for inc in range(0, len(self.joints)):
            
            driver = cmds.listRelatives(joints[inc], p = True)[0]
            offset = cmds.listRelatives(driver, p = True)
            xform = cmds.listRelatives(offset, p = True)
            
            if driver:
                driver = driver[0]
            if offset:
                offset = offset[0]
            if xform:
                xform = xform[0]
            
            if not xform == 'xform_%s' % joints[inc]:
                xform = space.create_xform_group(joints[inc])
            
            if not offset == 'offset_%s' % joints[inc]:
                offset = space.create_xform_group(joints[inc], 'offset')
                
            if not driver == 'driver_%s' % joints[inc]:
                driver = space.create_xform_group(joints[inc], 'driver')
            
            cmds.parent(driver, w = True)
            
            main_xform = self.main_joint_dict[self.joints[inc]]['xform']
            main_driver = self.main_joint_dict[self.joints[inc]]['driver']
            
            if not ignore_surface:
                attr.connect_translate_multiply(main_xform, offset, weight, respect_value = True)
                attr.connect_translate_multiply(main_driver, joints[inc], weight, respect_value = True)
                
            if ignore_surface:
                attr.connect_translate_multiply(main_xform, joints[inc], weight, respect_value = True)
            
            if self.surface:
                connection = attr.get_attribute_input('%s.geometry' % offset, node_only = True)
                
                if not cmds.nodeType(connection) == 'geometryConstraint':
                    cmds.geometryConstraint(self.surface, offset)
                
            cmds.parent(driver, offset)
            
    def create_control_follow(self, control, increment, weight):
        
        main_control = self.main_controls[increment]
        parent = cmds.listRelatives(main_control, p = True)[0]
        
        attr.connect_translate_multiply(control, parent, weight)

class CustomCurveRig(rigs.BufferRig):
    
    def __init__(self, name, side):
        super(CustomCurveRig, self).__init__(name, side)
        self.locators = []
        self.drivers = []   
        self.control_shape = 'square'
        self.surface = None 
        
    def _create_control_on_curve(self, curve, percent, sub = True, description = None):
        
        position = cmds.pointOnCurve(curve, top = True, pr = percent)
        
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
        
        space.create_xform_group(control_name)
        driver = space.create_xform_group(control_name, 'driver')
        
        return control_name, sub_control, driver
    
    def _create_locator(self, transform):
        locator = cmds.spaceLocator(n = core.inc_name('locator_%s' % self._get_name()))[0]
                    
        space.MatchSpace(transform, locator).translation_rotation()
        xform = space.create_xform_group(locator)
        driver = space.create_xform_group(locator, 'driver')
        
        if self.surface:
            cmds.geometryConstraint(self.surface, driver)
        
        return locator, driver, xform
    
    def add_fade_control(self, name, percent, sub = False, target_curve = None, extra_drivers = []):
        
        curve = geo.transforms_to_curve(self.locators, 6, 'temp')
        
        control_name, sub_control_name, driver = self._create_control_on_curve(curve, percent, sub, name)
        
        cmds.delete(curve)
        
        drivers = self.drivers + extra_drivers
        
        multiplies = space.create_follow_fade(control_name, drivers, -1)
        
        if sub:
            sub_multiplies = space.create_follow_fade(sub_control_name, self.locators, -1)
        
        
        if target_curve:
            rigs_util.fix_fade(target_curve, multiplies)
            
            if sub:
                
                rigs_util.fix_fade(target_curve, sub_multiplies)
                
        return multiplies
    
        if sub:
            return multiplies, sub_multiplies
            
    def insert_fade_control(self, control, sub_control = None, target_curve = None):
        multiplies = space.create_follow_fade(control, self.drivers, -1)
        
        if sub_control:
            sub_multiplies = space.create_follow_fade(sub_control, self.locators, -1)
        
        if target_curve:
            rigs_util.fix_fade(target_curve, multiplies)
            rigs_util.fix_fade(target_curve, sub_multiplies)
           
    def insert_follows(self, joints, percent = 0.5, create_locator = True):
        
        joint_count = len(joints)
        
        if create_locator:
            locator_group = cmds.group(em = True, n = core.inc_name('locators_follow_%s' % self._get_name()))
        
        locators = []
        xforms = []
        
        for inc in range(0, joint_count):
            
            if create_locator:
                locator, driver, xform = self._create_locator(joints[inc])
            
            if not create_locator:
                locator = joints[inc]
                driver = cmds.listRelatives(joints[inc], p = True)[0]
            
            all_axis = ['X','Y','Z']
            
            for axis in all_axis:
                attr.connect_multiply('%s.translate%s' % (self.drivers[inc], axis), '%s.translate%s' % (driver, axis), percent, skip_attach = True)
                
                attr.connect_multiply('%s.translate%s' % (self.locators[inc], axis), '%s.translate%s' % (locator, axis), percent, skip_attach = True)
            
            if create_locator:
                cmds.parentConstraint(locator, joints[inc])
                xforms.append(xform)
            
            locators.append(locator)
            
        if create_locator:
            cmds.parent(xforms, locator_group)
            cmds.parent(locator_group, self.setup_group)
            
        return locators
            
    def set_surface(self, surface):
        self.surface = surface
          
    
            
    def create(self):        
        rigs.BufferRig.create(self)
        
        locator_group = cmds.group(em = True, n = 'locators_%s' % self._get_name())
        cmds.parent(locator_group, self.setup_group)
        
        for joint in self.joints:
            
            locator, driver, xform = self._create_locator(joint)
            
            self.locators.append(locator)
            self.drivers.append(driver)
            
            cmds.parent(xform, locator_group)
            
            cmds.parentConstraint(locator, joint)
        
class CurveAndSurfaceRig(rigs.BufferRig):
    
    def __init__(self, description, side):
        super(CurveAndSurfaceRig, self).__init__(description, side)
        self.span_count = 4
        self.surface = None
        self.clusters = []
        self.control_shape = 'square'
        self.delete_end_cvs = True
        self.respect_side = False
        
    def _create_inc_control(self, curve, inc, sub = False, description = None, center_tolerance = 0.001):
        
        control = self._create_control(description, sub = sub)
        
        control.rotate_shape(90, 0, 0)
        control.hide_scale_attributes()
        
        cluster, handle = deform.create_cluster('%s.cv[%s]' % (curve, inc), self._get_name())
        self.clusters.append(handle)
        
        match = space.MatchSpace(handle, control.get())
        match.translation_to_rotate_pivot()
        
        control_name = control.get()
        
        if self.respect_side:
            side = control.color_respect_side(sub, center_tolerance = center_tolerance)
            
            if side != 'C':
                control_name = cmds.rename(control.get(), core.inc_name(control.get()[0:-1] + side))
        
        xform = space.create_xform_group(control_name)
        driver = space.create_xform_group(control_name, 'driver')
        
        bind_pre = deform.create_cluster_bindpre(cluster, handle)
        
        local_group, xform_group = space.constrain_local(control_name, handle, parent = True)
        
        local_driver = space.create_xform_group(local_group, 'driver')
        attr.connect_translate(driver, local_driver)
        attr.connect_translate(xform, xform_group)
        
        cmds.parent(bind_pre, xform_group)
        
        cmds.parent(xform_group, self.setup_group)
        
        return control_name, driver
        
    def _create_inc_sub_control(self, control, curve, inc):
        sub_control = self._create_inc_control(self.no_follow_curve, inc, sub = True)
        sub_control = rigs_util.Control(sub_control[0])
            
        sub_control.scale_shape(.8,.8,.8)
        sub_control.hide_scale_attributes()
        
        match = space.MatchSpace(control, sub_control.get())
        match.translation_rotation()
        cmds.parent(sub_control.get(), control)
        
    def _create_controls(self, description = None):
        
        cvs1 = cmds.ls('%s.cv[*]' % self.curve, flatten = True)
        count = len(cvs1)
        
        controls = []
        
        for inc in range(0, count):
            
            control, driver = self._create_inc_control(self.curve, inc)
            if self.surface:
                self._create_inc_sub_control(control, self.curve, inc)
            
            if self.respect_side:
                reverse_inc = (count-inc) -1
                
                if inc != reverse_inc:     
                    control, driver = self._create_inc_control(self.curve, reverse_inc)
                    if self.surface:
                        self._create_inc_sub_control(control, self.curve, reverse_inc)    
                
                if inc == reverse_inc:
                    break
                
        return controls               

    def _attach_joints_to_curve(self):
        
        for joint in self.joints:
            
            follow_locator = cmds.spaceLocator(n = 'locatorFollow_%s' % joint)[0]
            locator = cmds.spaceLocator(n = 'locatorNoFollow_%s' % joint)[0]
            
            xform = space.create_xform_group(locator)
            
            space.MatchSpace(joint, follow_locator).translation_rotation()
            space.MatchSpace(joint, locator).translation_rotation()
            
            geo.attach_to_curve(follow_locator, self.curve, maintain_offset = True)
            geo.attach_to_curve(locator, self.no_follow_curve, maintain_offset = True)
            
            if self.surface:
                cmds.geometryConstraint(self.surface, follow_locator)
            
            cmds.parent(xform, follow_locator)
            
            cmds.pointConstraint(locator, joint)
            
            cmds.parent(follow_locator, self.setup_group)
       
    def set_surface(self, surface_name):
        self.surface = surface_name
    
    def set_curve_spans(self, span_count):
        
        self.span_count = span_count
        
    def set_respect_side(self, bool_value):
        self.respect_side = bool_value
        
    def set_delete_end_cvs(self, bool_value):
        self.delete_end_cvs = bool_value
        
    def create(self):
        
        self.curve = geo.transforms_to_curve(self.joints, self.span_count, self.description)
        cmds.parent(self.curve, self.setup_group)
        
        if self.delete_end_cvs:
            cvs = cmds.ls('%s.cv[*]' % self.curve, flatten = True)
            cmds.delete(cvs[1], cvs[-2])
        
        self.no_follow_curve = cmds.duplicate(self.curve)[0]
        
        self._create_controls(self.curve)
        
        self._attach_joints_to_curve()

class EyeLidSphereRig(rigs.BufferRig):
    
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
            
            ik = space.IkHandle(self._get_name())
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
                
                group_ik = cmds.group(em = True, n = core.inc_name('group_ik%s_%s' % (inc,self._get_name())))
                space.MatchSpace(ik_handle, group_ik).translation()
                cmds.parent(ik_handle, group_ik)
                
                cmds.parent(group_ik, self.slice_group)
                
                geo.attach_to_curve(group_ik, self.curve)
                
                ik_groups.append(group_ik)
                
                inc+=1

class EyeLidSphereRig2(rigs.BufferRig):
    
    def __init__(self, description, side):
        
        super(EyeLidSphereRig2, self).__init__(description, side)
        
        self.radius = 1
        self.horizontal_sections = 10
        self.vertical_sections = 10
        
        self.follicle_group = None
        self.first_folicle = None
        
        self.control_curves = []
                
    def _create_nurbs_sphere(self):
        
        self.surface = cmds.sphere( ch = False, o = True, po = False, ax = [0, 1, 0], radius = self.radius, nsp = 4, n = 'surface_%s' % core.inc_name(self._get_name()) )[0]
        
        space.MatchSpace(self.buffer_joints[0], self.surface).translation()
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
        
        follicle = geo.create_surface_follicle(self.surface, self._get_name(description), [u_value, v_value] )
        cmds.select(cl = True)
        
        
        joint = cmds.joint( n = core.inc_name( self._get_name('joint', description) ) )
        space.MatchSpace(follicle, joint).translation()
        
        cmds.parent(joint, follicle)
        cmds.makeIdentity(joint, jo = True, apply = True)
        
        locator_top = False
        locator_btm = False
        
        if locator:
            locator_top = cmds.spaceLocator(n = core.inc_name(self._get_name('locatorFollicle', description)))[0]
            cmds.setAttr('%s.localScaleX' % locator_top, .1)
            cmds.setAttr('%s.localScaleY' % locator_top, .1)
            cmds.setAttr('%s.localScaleZ' % locator_top, .1)
        
            space.MatchSpace(self.sub_locator_group, locator_top).translation()
            cmds.parent(locator_top, self.sub_locator_group)
            cmds.makeIdentity(locator_top, t = True, apply = True)  
            
            locator_btm = cmds.spaceLocator(n = core.inc_name(self._get_name('locatorBtmFollicle', description)))[0]
            cmds.setAttr('%s.localScaleX' % locator_btm, .1)
            cmds.setAttr('%s.localScaleY' % locator_btm, .1)
            cmds.setAttr('%s.localScaleZ' % locator_btm, .1)
        
            space.MatchSpace(self.sub_locator_group, locator_btm).translation()
            
            cmds.parent(locator_btm, self.sub_locator_group)
            cmds.makeIdentity(locator_btm, t = True, apply = True) 
            
            if not reverse:
                cmds.setAttr('%s.translateY' % locator_btm, 1)      
        
        return follicle, locator_top, locator_btm
        
    def _create_locator_group(self):
        
        top_group = cmds.group(em = True, n = core.inc_name(self._get_name('group', 'scale')))
        locator_group = cmds.group(em = True, n = core.inc_name(self._get_name('group', 'locator')))
        sub_locator_group = cmds.group(em = True, n = core.inc_name(self._get_name('group', 'sub_locator')))
        btm_sub_locator_group = cmds.group(em = True, n = core.inc_name(self._get_name('group', 'btmsub_locator')))
        
        cmds.parent(sub_locator_group, locator_group)
        cmds.parent(btm_sub_locator_group, locator_group)
        cmds.parent(locator_group, top_group)
        space.MatchSpace(self.buffer_joints[0], locator_group).translation()
        
        cmds.setAttr('%s.scaleX' % locator_group, (self.radius*2) )
        cmds.setAttr('%s.scaleY' % locator_group, (self.radius*4) )
        
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
            
            group = cmds.group(em = True, n = core.inc_name(self._get_name('group', 'follicleSection%s' % (inc+1))))
            
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
                        
                        plus = cmds.createNode('plusMinusAverage', n = core.inc_name(self._get_name('plusMinusAverage', 'comboBtm')))
                        
                        attr.connect_multiply('%s.parameterV' % self.first_folicle, '%s.input1D[0]' % plus, multiply_value)
                        attr.connect_multiply('%s.parameterV' % self.last_folicle, '%s.input1D[1]' % plus, (1-multiply_value) )
                        
                        cmds.connectAttr('%s.output1D' % plus, '%s.parameterV' % folicle)
                        
                    if not reverse:
                
                        
                        remap_front2 = cmds.createNode('remapValue', n = self._get_name('remapValueFront'))
        
                        attr.connect_multiply('%s.outValue' % remap_front, '%s.inputValue' % remap_front2, multiply_value)
                        
                        cmds.setAttr('%s.value[0].value_FloatValue' % remap_front2, 1)
                        cmds.setAttr('%s.value[1].value_FloatValue' % remap_front2, 0)

                        plus = cmds.createNode('plusMinusAverage', n = core.inc_name(self._get_name('plusMinusAverage', 'combo')))
                        cmds.setAttr('%s.operation' % plus, 2)
                        cmds.connectAttr('%s.outValue' % remap_front2, '%s.input1D[0]' % plus)

                        attr.connect_multiply('%s.outValue' % remap_back, '%s.input1D[1]' % plus, (1-multiply_value))
                        
                        cmds.connectAttr('%s.output1D' % plus, '%s.parameterV' % folicle)
                        
                    cmds.connectAttr('%s.parameterU' % self.first_folicle, '%s.parameterU' % folicle)
                    
                if not self.first_folicle:
                    
                    self.first_folicle = folicle
                    self.last_folicle = reverse_folicle
                    
                    
                    cmds.setAttr('%s.translateX' % locator_top, u_value)
                    cmds.setAttr('%s.translateY' % locator_top, sub_v_value)
                    
                    cmds.setAttr('%s.translateX' % locator_btm, u_value)
                     
                    cmds.connectAttr('%s.translateX' % locator_top, '%s.parameterU' % folicle)
                    cmds.connectAttr('%s.translateY' % locator_top, '%s.parameterV' % folicle)
                    
                    cmds.connectAttr('%s.translateY' % locator_btm, '%s.parameterV' % reverse_folicle)
                
                if reverse:
                    sub_v_value -= sub_section_value
                    multiply_value += multiply_section_value
                        
                if not reverse:
                    sub_v_value += sub_section_value
                    multiply_value -= multiply_section_value
            
            cmds.parent(group, self.follicle_group)
            
            
        space.MatchSpace(center_joint, self.top_group).world_pivots()
        space.MatchSpace(center_joint, self.top_group).rotation()
        
        locator_group = cmds.group(em = True, n = core.inc_name(self._get_name('locators')))
        
        self.curve_locators = []
        
        for sub_locator in locators:
            
            locator = sub_locator[0]
            
            locator_world = cmds.spaceLocator(n = core.inc_name(self._get_name('locator')))[0]
            
            self.curve_locators.append(locator_world)
            
            cmds.setAttr('%s.localScaleX' % locator_world, .1)
            cmds.setAttr('%s.localScaleY' % locator_world, .1)
            cmds.setAttr('%s.localScaleZ' % locator_world, .1)
            
            space.MatchSpace(locator, locator_world).translation()
            
            cmds.parent(locator_world, locator_group)
            cmds.pointConstraint(locator_world, locator)
        
        
        
        cmds.parent(locator_group, self.setup_group)
        
    def _attach_locators_to_curve(self):
        curve = geo.transforms_to_curve(self.curve_locators, 3, self._get_name())
        
        cmds.parent(curve, self.setup_group)
        
        self.control_curves.append(curve)
        
        for locator in self.curve_locators:
            geo.attach_to_curve(locator, curve)
        
    def _create_controls(self):
        
        inc = 1
        
        for curve in self.control_curves:
            clusters = deform.cluster_curve(curve, self._get_name(), join_ends = False)
            
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
            
            cmds.parent(group, self.control_group)
            cmds.parent(local_group, self.setup_group)
                        
            for cluster in clusters:
                control = self._create_control(sub = sub)
                
                control.hide_scale_and_visibility_attributes()
                if inc == 1:
                    control.scale_shape(.1, .1, .1)
                if inc == 2:
                    control.scale_shape(.08, .08, .08)
                    
                xform = space.create_xform_group(control.get())
                
                space.MatchSpace(cluster, xform).translation_to_rotate_pivot()
                
                local, xform_local = space.constrain_local(control.get(), cluster, constraint = 'pointConstraint')
                
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
       
class MouthTweakers(rigs.Rig):


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
                
                cmds.aimConstraint(locators1[inc+1], locators1[inc])[0]
                cmds.aimConstraint(locators2[inc+1], locators2[inc])[0]
                    
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
    
            locator1,locator2 = rigs_util.create_distance_scale( joints1[inc], child3 )
    
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
                geo.attach_to_curve(locators2[inc], curve)
    
    
    
    def _create_locators(self, joints1, joints2):
        
        locator1_gr = cmds.group(em = True, n = core.inc_name(self._get_name('group', 'locators1')))
        locator2_gr = cmds.group(em = True, n = core.inc_name(self._get_name('group', 'locators2')))
        
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
            
            space.MatchSpace( joints1[inc] , loc1 ).translation_rotation()
    
            loc2 = cmds.spaceLocator(n = 'locator_%s' % joints2[inc])[0]
            
            cmds.setAttr('%s.localScaleX' % loc2, .1)
            cmds.setAttr('%s.localScaleY' % loc2, .1)
            cmds.setAttr('%s.localScaleZ' % loc2, .1)
    
            space.MatchSpace( child3 , loc2 ).translation_rotation()    
            
            locators1.append(loc1)
            locators2.append(loc2)
            
        cmds.parent(locators1, locator1_gr)
        cmds.parent(locators2, locator2_gr)
    
        return locators1, locators2
    
    def _create_joints_from_locators(self, locators, control = False):
        
        joints = []
        
        for locator in locators:
            cmds.select(cl = True)
            
            joint = cmds.joint(n = core.inc_name(self._get_name('joint', 'temp')))
            
            const = cmds.parentConstraint(locator, joint)
            cmds.delete(const)
            
            joints.append(joint)
            
        return joints
    
    def _create_joint(self, curve, length, control = False):
        
        param = geo.get_parameter_from_curve_length(curve, length)
        position = geo.get_point_from_curve_parameter(curve, param)
        
        point_on_curve = cmds.pointOnCurve(curve, parameter = param, ch = True)
        
        cmds.select(cl = True)
        joint = cmds.joint(p = position, n = core.inc_name(self._get_name('joint')))
        side = space.get_side(position, 0.1)
        
        joint = cmds.rename(joint, core.inc_name(joint[:-1] + side))
        
        if not control:
            return joint
        
        
        if not self.joint_control_group:
            group = cmds.group(em = True, n = self._get_name('controls', 'joint'))
            cmds.parent(group, self.control_group)
            self.joint_control_group = group
        
        if control:
        
        
            xform = space.create_xform_group(joint)
            #aim = space.create_xform_group(joint, 'aim')
            aim = None
            aim_control = None
            
            control = self._create_control(sub = True)
            control.rotate_shape(0,0,90)
            control.scale_shape(.09, .09, .09)
            
            control_name = control.get()
            
            control_name = cmds.rename(control_name, core.inc_name(control_name[:-1] + side))
            
            
            xform_control = space.create_xform_group(control_name)
            driver_control = space.create_xform_group(control_name, 'driver')
            
            cmds.connectAttr('%s.positionX' % point_on_curve, '%s.translateX' % xform_control)
            cmds.connectAttr('%s.positionY' % point_on_curve, '%s.translateY' % xform_control)
            cmds.connectAttr('%s.positionZ' % point_on_curve, '%s.translateZ' % xform_control)

            cmds.connectAttr('%s.positionX' % point_on_curve, '%s.translateX' % xform)
            cmds.connectAttr('%s.positionY' % point_on_curve, '%s.translateY' % xform)
            cmds.connectAttr('%s.positionZ' % point_on_curve, '%s.translateZ' % xform)
            
            space.MatchSpace(joint, xform_control).translation_rotation()
            
            driver = space.create_xform_group(joint, 'driver')
            
            attr.connect_translate(control_name, joint)
            attr.connect_rotate(control_name, joint)
            attr.connect_scale(control_name, joint)
            
            attr.connect_translate(driver_control, driver)
            attr.connect_rotate(driver_control, driver)
            attr.connect_scale(driver_control, driver)
            
            cmds.parent(xform_control, self.joint_control_group)
            cmds.parent(xform, self.setup_group)
            
            return [joint, aim, xform,control_name, aim_control, xform_control]
    
    def _create_joints_on_curve(self, curve, section_count):
        
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
        
        length = cmds.arclen(curve, ch = False)
        
        sections = section_count*2
        
        section_length = length/float(sections)
        start_offset = 0
        end_offset = length
        
        joints1 = []
        joints2 = []
        
        middle_joint, middle_aim, middle_xform, middle_control, middle_aim_control, middle_xform_control = self._create_joint(curve, length/2.0, control = True)
        
        for inc in range(0, sections/2):
        
            param1 = geo.get_parameter_from_curve_length(curve, start_offset)
            position1 = geo.get_point_from_curve_parameter(curve, param1)
            
            param2 = geo.get_parameter_from_curve_length(curve, end_offset)
            position2 = geo.get_point_from_curve_parameter(curve, param2)
            
            side1 = space.get_side(position1, 0.1)
            side2 = space.get_side(position2, 0.1)
            
            
            joint1, aim1, xform1, control1, aim_control1, xform_control1 = self._create_joint(curve, start_offset, control = True)    
            joint2, aim2, xform2, control2, aim_control2, xform_control2 = self._create_joint(curve, end_offset, control = True)

            start_offset += section_length
            end_offset -= section_length
            
            joints1.append(joint1)
            joints2.append(joint2)
            
        return joints1 + [middle_joint] + joints2
    
    def _create_joints(self, curve1, curve2, count = 11):
    
        joints_gr = cmds.group(em = True, n = core.inc_name(self._get_name('group', 'joints')))
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
            
            end_joint = cmds.duplicate(lip_joints[inc], n = core.inc_name( 'joint_%s' % self._get_name('sub') ))[0]
            cmds.parent(end_joint, muzzle_joint)
            cmds.makeIdentity(end_joint, jo = True, apply = True)
            
    
            sub_joints = space.subdivide_joint(muzzle_joint, end_joint, name = self._get_name('sub'), count = 2)
            
              
            joints += sub_joints
            
            joints.append(end_joint)
            
            new_joints = []
        
            for joint in joints:
                
                new_joint = cmds.rename(joint, core.inc_name(self._get_name('joint', 'lip_span%s' % (inc+1))))
                new_joints.append(new_joint)
            
            lip_joint = cmds.rename(lip_joints[inc], core.inc_name(self._get_name('joint', 'lip_offset%s' % (inc+1))))
            new_joints.append(lip_joint)
            
            
            new_muzzle_joints.append( new_joints[0] )
            new_lip_joints.append( new_joints[-1] )
        
        muzzle_joints = new_muzzle_joints
        lip_joints = new_lip_joints
        cmds.parent(muzzle_joints, joints_gr)
        
        
        
        if self.lip_locators:
            
            cmds.parent(lip_joints[0], muzzle_joints[-1])
        
        return muzzle_joints, lip_joints
    
    def _create_ik(self, joints1, joints2 ):
    
        ik_gr = cmds.group(em = True, n = core.inc_name(self._get_name('group', 'ik')))
        cmds.parent(ik_gr, self.setup_group)
    
        ik_handles = []
    
        for inc in range(0, len(joints1)):
            
            ik = space.IkHandle('top_lip')
            ik.set_start_joint( joints1[inc] )
            
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
        
        if self.lip_curve and not locators:
            curve = self.lip_curve
            
            clusters = deform.cluster_curve(curve, self._get_name(), join_ends = False)
        
            cluster_group = cmds.group(em = True, name = self._get_name('group', 'cluster%s' % curve.capitalize()))
            cmds.parent(clusters, cluster_group)
        
            cmds.parent(cluster_group, self.setup_group)
            
        if locators:
            clusters = locators
        
        group = cmds.group(em = True, n = core.inc_name(self._get_name('group', 'local')))
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
                space.MatchSpace(cluster, control.get()).translation()
            if self.lip_curve:
                space.MatchSpace(cluster, control.get()).translation_to_rotate_pivot()

            if self.side == 'C':
                if self.respect_side:
                    side = control.color_respect_side(center_tolerance = 0.1)
                
                if side != 'C':
                    control_name = cmds.rename(control.get(), core.inc_name(control.get()[0:-1] + side))
                    control = rigs_util.Control(control_name)
            
            space.create_xform_group(control.get())
            driver = space.create_xform_group(control.get(), 'driver')
            
                
            local, xform_local = space.constrain_local(control.get(), cluster, constraint = 'pointConstraint')
            local_driver = space.create_xform_group(local, 'driver')
            
            attr.connect_translate(driver, local_driver)
            
            cmds.parent(xform_local, group)
            
            
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
            space.MatchSpace(locator, control.get()).translation_rotation()
            
            parent_locator = cmds.listRelatives(locator, p = True)[0]
            
            xform = space.create_xform_group(control.get())
            driver = space.create_xform_group(control.get(), 'driver')
            
            space.create_follow_group(parent_locator, xform)
            
            cmds.parent(locator, control.get())
    
    def create(self):
    
        super(MouthTweakers, self).create()
        
        muzzle_joints, lip_joints = self._create_joints( self.muzzel_curve , self.lip_curve, 15) 
        
        
        ik_handles = self._create_ik( muzzle_joints, lip_joints)
        
        locators1, locators2 = self._create_locators( muzzle_joints, lip_joints)
        
        self._attach_ik(locators1, locators2, ik_handles, self.lip_curve)
        
        distance_locators = self._attach_scale( muzzle_joints, lip_joints, locators1, locators2)
        
        
        if self.lip_curve:
            self._create_controls()
        if not self.lip_curve:
            self._create_controls(locators2)
            
class WorldJawRig(rigs.BufferRig):
    
    def __init__(self, description, side):
        super(WorldJawRig, self).__init__(description, side)
        self.jaw_slide_offset = .1
        self.jaw_slide_attribute = True
    
    def _create_control(self):
        
        self.control = super(WorldJawRig, self)._create_control()
        
        space.MatchSpace(self.buffer_joints[0], self.control.get()).translation_rotation()
        
        xform = space.create_xform_group(self.control.get())
        driver = space.create_xform_group(self.control.get(), 'driver')
        
        self.control_dict[self.control.get()]['xform'] = xform
        self.control_dict[self.control.get()]['driver'] = driver
        
    def _attach(self):
        
        driver = self.control_dict[self.control.get()]['driver']
            
        cmds.parentConstraint(self.control.get(), self.buffer_joints[0])
        attr.connect_scale(self.control.get(), self.buffer_joints[0])
        
        var = attr.MayaNumberVariable('autoSlide')
        var.set_variable_type(var.TYPE_DOUBLE)
        var.set_value(self.jaw_slide_offset)
        var.set_keyable(self.jaw_slide_attribute)
        var.create(self.control.get())
        
        multi = attr.connect_multiply('%s.rotateX' % self.control.get(), '%s.translateZ' % driver)
        var.connect_out('%s.input2X' % multi)
    
    def set_jaw_slide_offset(self, value):
        self.jaw_slide_offset = value
        
    def set_create_jaw_slide_attribute(self, bool_value):
        self.jaw_slide_attribute = bool_value
        
    def create(self):
        super(WorldJawRig, self).create()
        
        self._create_control()
        self._attach()

class WorldStickyRig(rigs.JointRig):
    
    def __init__(self, description, side):
        super(WorldStickyRig, self).__init__(description, side)
        
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
        
        self.sticky_control_group = cmds.group(em = True, n = core.inc_name(self._get_name('group', 'sticky_controls')))
        cmds.parent(self.sticky_control_group, self.control_group)
        
        self.follow_control_groups = {}
        
        self.top_controls = []
        self.btm_controls = []
        
        
        
    def _loop_joints(self):
        
        self.top_joint_group = cmds.group(em = True, n = core.inc_name( self._get_name('group', 'joints_top')))
        self.btm_joint_group = cmds.group(em = True, n = core.inc_name( self._get_name('group', 'joints_btm')))
        
        self.top_locator_group = cmds.group(em = True, n = core.inc_name( self._get_name('group', 'locators_top')))
        self.mid_locator_group = cmds.group(em = True, n = core.inc_name( self._get_name('group', 'locators_mid')))
        self.btm_locator_group = cmds.group(em = True, n = core.inc_name( self._get_name('group', 'locators_btm')))
        
        cmds.parent(self.top_joint_group, self.btm_joint_group, self.setup_group)
        cmds.parent(self.top_locator_group, self.mid_locator_group, self.btm_locator_group, self.control_group)
        
        cmds.hide(self.top_locator_group, self.mid_locator_group, self.btm_locator_group)
        
        joint_count = len(self.top_joints)
        
        if self.straight_loop:
            for inc in range(0, joint_count):
                self._create_increment(inc)
                
        if not self.straight_loop:
            for inc in range(0, joint_count):
                
                negative_inc = joint_count - (inc+1)
                
                self._create_increment(inc)
                
                locators1 = [self.top_locator, self.btm_locator]
                
                if not self.controls:
                    top_control1 = self.sub_controls[-1]
                    btm_control1 = self.sub_controls[-2]
                if self.controls:
                    top_control1 = self.controls[-1]
                    btm_control1 = self.controls[-2]
                    
                if inc == negative_inc:
                    self.locators.append([locators1])
                    self.zip_controls.append([[top_control1, btm_control1]])
                    break
                
                self._create_increment(negative_inc)
                
                locators2 = [self.top_locator, self.btm_locator]
                
                if not self.controls:
                    top_control2 = self.sub_controls[-1]
                    btm_control2 = self.sub_controls[-2]
                if self.controls:
                    top_control2 = self.controls[-1]
                    btm_control2 = self.controls[-2]
                    
                self.locators.append([locators1, locators2])
                self.zip_controls.append([[top_control1, btm_control1],[top_control2,btm_control2]])
                
        self.side = self.first_side
           
    def _create_increment(self, inc):
        top_joint = self.top_joints[inc]
        btm_joint = self.btm_joints[inc]
        
        if self.respect_side:
            side = space.get_side(top_joint, self.respect_side_tolerance)
            self.side = side
        
        control_top = self._create_sticky_control(top_joint, 'top')
        self.top_controls.append(control_top[0])
        control_btm = self._create_sticky_control(btm_joint, 'btm')
        self.btm_controls.append(control_btm[0])

        cmds.parentConstraint(control_top[0], top_joint)
        constraint = cmds.scaleConstraint(control_top[0], top_joint)[0]
        space.scale_constraint_to_local(constraint)
        
        cmds.parentConstraint(control_btm[0], btm_joint)
        constraint = cmds.scaleConstraint(control_btm[0], btm_joint)[0]
        space.scale_constraint_to_local(constraint)
        
        self.top_locator = self._create_locator('top')
        self.mid_top_locator = self._create_locator('mid_top')
        self.mid_btm_locator = self._create_locator('mid_btm')
        self.btm_locator = self._create_locator('btm')
        
        self.control_dict[control_top[0]] = [control_top[1], control_top[2]]
        self.control_dict[control_btm[0]] = [control_btm[1], control_btm[2]]
        
        space.MatchSpace(top_joint, self.top_locator[1]).translation()
        space.MatchSpace(btm_joint, self.btm_locator[1]).translation()
        
        midpoint = space.get_midpoint(top_joint, btm_joint)
        
        cmds.xform(self.mid_top_locator[1], t = midpoint, ws = True)
        cmds.xform(self.mid_btm_locator[1], t = midpoint, ws = True)
        
        cmds.parent(self.top_locator[1], self.top_locator_group)
        cmds.parent(self.mid_top_locator[1], self.mid_locator_group)
        cmds.parent(self.mid_btm_locator[1], self.mid_locator_group)
        cmds.parent(self.btm_locator[1], self.btm_locator_group)   
        
        self._create_follow([self.top_locator[0], self.mid_top_locator[0]], control_top[1], top_joint)
        
        cmds.addAttr(control_top[0], ln = 'stick', min = 0, max = 1, k = True)
        
        cmds.connectAttr('%s.stick' % control_top[0], '%s.stick' % top_joint)
        
        self._create_follow([self.btm_locator[0], self.mid_btm_locator[0]], control_btm[1], control_btm[0])
        
        self._create_follow([self.top_locator[0], self.btm_locator[0]], self.mid_top_locator[1], self.mid_top_locator[0])
        self._create_follow([self.top_locator[0], self.btm_locator[0]], self.mid_btm_locator[1], self.mid_btm_locator[0])
        
        cmds.setAttr('%s.stick' % self.mid_top_locator[0], 0.5)
        cmds.setAttr('%s.stick' % self.mid_btm_locator[0], 0.5)
        
        space.MatchSpace(self.top_locator[0], self.mid_top_locator[0]).translation()
        space.MatchSpace(self.btm_locator[0], self.mid_btm_locator[0]).translation()

    def _create_follow(self, source_list, target, target_control ):
        
        constraint = cmds.parentConstraint(source_list, target)[0]
        cmds.setAttr('%s.interpType' % constraint, 2)
        constraint_editor = space.ConstraintEditor()    
        constraint_editor.create_switch(target_control, 'stick', constraint)
        
    def _create_sticky_control(self, transform, description):

        control = self._create_control(description)
        control.rotate_shape(90,0,0)
        control.scale_shape(.5, .5, .5)

        control_name = control.get()
        
        space.MatchSpace(transform, control_name).translation_rotation()
                
        control = control_name
        
        xform = space.create_xform_group(control)
        driver = space.create_xform_group(control, 'driver')
        scale = space.create_xform_group(control, 'scale')
        
        if self.side == 'R':
            cmds.setAttr('%s.rotateY' % scale, 180)
            cmds.setAttr('%s.scaleZ' % scale, -1)
        
        cmds.parent(xform, self.sticky_control_group)
        
        return control, xform, driver
    
    def _create_locator(self, description):
        
        locator = cmds.spaceLocator(n = core.inc_name(self._get_name('locator', description)))[0]
        
        xform = space.create_xform_group(locator)
        driver = space.create_xform_group(locator, 'driver')
        
        return locator, xform, driver
    
    def _create_follow_control_group(self, follow_control):
    
        if not follow_control in self.follow_control_groups.keys():
            
            group = cmds.group(em = True, n = 'follow_group_%s' % follow_control)
            space.MatchSpace(follow_control, group).translation_rotation()
            
            cmds.parent(group, self.follower_group)
            space.create_xform_group(group)
                        
            attr.connect_translate_plus(follow_control, group)
            attr.connect_rotate(follow_control, group)
            attr.connect_scale(follow_control, group)
            
            self.follow_control_groups[follow_control] = group
            
        return self.follow_control_groups[follow_control]
        
    def _connect_bulge_scale(self, main_control, joint, joint_control):
        
        constraint = cmds.listRelatives(joint, type = 'scaleConstraint')
        if constraint:
            cmds.delete(constraint)
            
        multiply = attr.connect_multiply('%s.bulge' % main_control, '%s.scaleX' % joint)
        cmds.connectAttr('%s.outputY' % multiply, '%s.scaleY' % joint)
        cmds.connectAttr('%s.outputZ' % multiply, '%s.scaleZ' % joint)
        
        cmds.connectAttr('%s.bulge' % main_control, '%s.input1Y' % multiply)
        cmds.connectAttr('%s.bulge' % main_control, '%s.input1Z' % multiply)
        
        cmds.connectAttr('%s.scaleX' % joint_control, '%s.input2X' % multiply)
        cmds.connectAttr('%s.scaleY' % joint_control, '%s.input2Y' % multiply)
        cmds.connectAttr('%s.scaleZ' % joint_control, '%s.input2Z' % multiply)
    
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
        super(WorldStickyRig, self).create()
        
        self._loop_joints()
        
    def create_follow(self, follow_transform, increment, value):
        
        if not self.follower_group:
            
            self.follower_group = cmds.group(em = True, n = core.inc_name(self._get_name('group', 'follower')))
            cmds.parent(self.follower_group, self.control_group)
        
        follow_transform = self._create_follow_control_group(follow_transform)
        
        if increment >= 0:
            locators = self.locators[increment]
            
        top_locator1 = locators[0][0][1]
        btm_locator1 = locators[0][1][1]
        
        follow_top = space.create_multi_follow([self.follower_group, follow_transform], top_locator1, top_locator1, value = value)
        follow_btm = space.create_multi_follow([self.follower_group, follow_transform], btm_locator1, btm_locator1, value = 1-value)
        
        if len(locators) > 1:
            top_locator2 = locators[1][0][1]
            btm_locator2 = locators[1][1][1]
        
            space.create_multi_follow([self.follower_group, follow_transform], top_locator2, top_locator2, value = value) 
            space.create_multi_follow([self.follower_group, follow_transform], btm_locator2, btm_locator2, value = 1-value)
            
    def create_zip(self, attribute_control, increment, start, end, end_value = 1):
        
        left_over_value = 1.0 - end_value
        
        attr.create_title(attribute_control, 'ZIP')
        
        if not cmds.objExists('%s.zipL' % attribute_control):
            cmds.addAttr(attribute_control, ln = 'zipL', min = 0, max = 10, k = True)
            
        if not cmds.objExists('%s.zipR' % attribute_control):
            cmds.addAttr(attribute_control, ln = 'zipR', min = 0, max = 10, k = True)
            
        left_top_control = self.zip_controls[increment][0][0]
        left_btm_control = self.zip_controls[increment][0][1]
            
        anim.quick_driven_key('%s.zipL' % attribute_control, '%s.stick' % left_top_control, [start,end], [0,end_value])
        anim.quick_driven_key('%s.zipL' % attribute_control, '%s.stick' % left_btm_control, [start,end], [0,end_value])
                
        if left_over_value:
            anim.quick_driven_key('%s.zipR' % attribute_control, '%s.stick' % left_top_control, [start,end], [0,left_over_value])
            anim.quick_driven_key('%s.zipR' % attribute_control, '%s.stick' % left_btm_control, [start,end], [0,left_over_value])
        
        cmds.setAttr('%s.stick' % left_top_control, lock = True)
        cmds.setAttr('%s.stick' % left_btm_control, lock = True)
        
        right_increment = 1
        
        if len(self.zip_controls[increment]) == 1:
            right_increment = 0
        
        right_top_control = self.zip_controls[increment][right_increment][0]
        right_btm_control = self.zip_controls[increment][right_increment][1]
        
        anim.quick_driven_key('%s.zipR' % attribute_control, '%s.stick' % right_top_control, [start,end], [0,end_value])
        anim.quick_driven_key('%s.zipR' % attribute_control, '%s.stick' % right_btm_control, [start,end], [0,end_value])
        
        if left_over_value:
            anim.quick_driven_key('%s.zipL' % attribute_control, '%s.stick' % right_top_control, [start,end], [0,left_over_value])
            anim.quick_driven_key('%s.zipL' % attribute_control, '%s.stick' % right_btm_control, [start,end], [0,left_over_value])

        cmds.setAttr('%s.stick' % right_top_control, lock = True)
        cmds.setAttr('%s.stick' % right_btm_control, lock = True)
        
    def create_roll(self, control, increment, percent):
        
        control = vtool.util.convert_to_sequence(control)
        
        if len(control) == 1:
            top_center_control = control[0]
            btm_center_control = control[0]
        if len(control) > 1:
            top_center_control = control[0]
            btm_center_control = control[1]
        
        attr.create_title(top_center_control, 'LIP')
        
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
        
        top_joint = self.top_joints[increment]
        btm_joint = self.btm_joints[increment]
        
        attr.connect_multiply('%s.roll' % top_center_control, '%s.rotateX' % top_left_driver, percent)
        attr.connect_multiply('%s.roll' % btm_center_control, '%s.rotateX' % btm_left_driver, -1*percent)
        
        self._connect_bulge_scale(top_center_control, top_joint, top_left_control)
        self._connect_bulge_scale(btm_center_control, btm_joint, btm_left_control)
        
        cmds.connectAttr('%s.bulge' % top_center_control, '%s.scaleX' % top_left_driver)
        cmds.connectAttr('%s.bulge' % top_center_control, '%s.scaleY' % top_left_driver)
        cmds.connectAttr('%s.bulge' % top_center_control, '%s.scaleZ' % top_left_driver)
            
        cmds.connectAttr('%s.bulge' % btm_center_control, '%s.scaleX' % btm_left_driver)
        cmds.connectAttr('%s.bulge' % btm_center_control, '%s.scaleY' % btm_left_driver)
        cmds.connectAttr('%s.bulge' % btm_center_control, '%s.scaleZ' % btm_left_driver)
        
        if len(self.zip_controls[increment]) > 1: 
        
            top_right_control = self.zip_controls[increment][1][1]
            btm_right_control = self.zip_controls[increment][1][0]
            
            top_right_driver = self.control_dict[top_right_control][1]
            btm_right_driver = self.control_dict[btm_right_control][1]
            
            attr.connect_multiply('%s.roll' % top_center_control, '%s.rotateX' % top_right_driver, percent)
            attr.connect_multiply('%s.roll' % btm_center_control, '%s.rotateX' % btm_right_driver, -1*percent)
        
            top_joint = self.top_joints[(increment+1)*-1]
            btm_joint = self.btm_joints[(increment+1)*-1]
        
            self._connect_bulge_scale(top_center_control, top_joint, top_right_control)
            self._connect_bulge_scale(btm_center_control, btm_joint, btm_right_control)
            
            cmds.connectAttr('%s.bulge' % top_center_control, '%s.scaleX' % top_right_driver)
            cmds.connectAttr('%s.bulge' % top_center_control, '%s.scaleY' % top_right_driver)
            cmds.connectAttr('%s.bulge' % top_center_control, '%s.scaleZ' % top_right_driver)
            
            cmds.connectAttr('%s.bulge' % btm_center_control, '%s.scaleX' % btm_right_driver)
            cmds.connectAttr('%s.bulge' % btm_center_control, '%s.scaleY' % btm_right_driver)
            cmds.connectAttr('%s.bulge' % btm_center_control, '%s.scaleZ' % btm_right_driver)
            
class WorldStickyFadeRig(WorldStickyRig):       

    def __init__(self, description, side):
        super(WorldStickyFadeRig, self).__init__(description, side)
        
        self.corner_offsets = []
        self.sub_corner_offsets = []
        
        self.corner_control_shape = 'square'
        
        self.corner_match = []
        self.corner_xforms = []
        self.corner_controls = []

    def _create_corner_fades(self):
               
        orig_side = self.side
        
        for side in ['L','R']:
            
            self.side = side
            
            corner_offset = cmds.group(em = True, n = self._get_name('offset', 'corner'))
            
            sub_corner_offset = cmds.duplicate(corner_offset, n = self._get_name('subOffset', 'corner'))[0]
            
            if side == 'L':
                joint = self.top_joints[0]
            if side == 'R':
                joint = self.top_joints[-1]
                
            control = self._create_control('corner')
            control.set_curve_type(self.corner_control_shape)
            control.rotate_shape(90,0,0)
            control.hide_rotate_attributes()
            control.hide_scale_attributes()
            
            sub_control = self._create_control('corner', sub = True)
            sub_control.set_curve_type(self.corner_control_shape)
            sub_control.rotate_shape(90,0,0)
            sub_control.scale_shape(.8, .8, .8)
            sub_control.hide_rotate_attributes()
            sub_control.hide_scale_attributes()
            
            cmds.parent(sub_control.get(), control.get())
                
            xform = space.create_xform_group(control.get())
            driver = space.create_xform_group(control.get(), 'driver')
            
            self.corner_xforms.append(xform)
            self.corner_controls.append(control.get())
            
            if not self.corner_match:
                space.MatchSpace(joint, xform).translation_rotation()
            if self.corner_match:
                
                if side == 'L':
                    corner_match = self.corner_match[0]
                if side == 'R':
                    corner_match = self.corner_match[1]
                    
                space.MatchSpace(corner_match, xform).translation_rotation()
                
                const = cmds.scaleConstraint( corner_match, xform)
                cmds.delete(const)
            
            self.corner_offsets.append(corner_offset)
            self.sub_corner_offsets.append(sub_corner_offset)
            
            cmds.pointConstraint(control.get(), corner_offset)
            cmds.pointConstraint(sub_control.get(), sub_corner_offset)
            
            corner_offset_xform = space.create_xform_group(corner_offset)
            cmds.parent(corner_offset_xform, xform)
            cmds.parent(sub_corner_offset, corner_offset_xform)
            
        self.side =orig_side

    def _rename_followers(self, follow, description):
        
        const = space.ConstraintEditor()
        constraint = const.get_constraint(follow, 'parentConstraint')
        names = const.get_weight_names(constraint)
        
        follower1 = names[0][:-2]
        follower2 = names[1][:-2]
        
        cmds.rename(follower1, core.inc_name('%s_%s' % (description, follower1)))
        cmds.rename(follower2, core.inc_name('%s_%s' % (description, follower2)))
        
    def set_corner_match(self, left_transform, right_transform):
        self.corner_match = [left_transform, right_transform]

    def set_corner_control_shape(self, shape_name):
        self.corner_control_shape = shape_name

    def create(self):
        super(WorldStickyFadeRig, self).create()
        
        self._create_corner_fades()

    def create_follow(self, follow_transform, increment, value):
        
        if not self.follower_group:
            
            self.follower_group = cmds.group(em = True, n = core.inc_name(self._get_name('group', 'follower')))
            cmds.parent(self.follower_group, self.control_group)
        
        follow_transform = self._create_follow_control_group(follow_transform)
        
        if increment != 'corner':
            locators = self.locators[increment]
    
            top_locator1 = locators[0][0][1]
            btm_locator1 = locators[0][1][1]
            
            follow_top = space.create_multi_follow([self.follower_group, follow_transform], top_locator1, top_locator1, value = value)
            follow_btm = space.create_multi_follow([self.follower_group, follow_transform], btm_locator1, btm_locator1, value = 1-value)        
            
                    
            self._rename_followers(follow_top, 'top')
            self._rename_followers(follow_btm, 'btm')
            
            if len(locators) > 1:
                top_locator2 = locators[1][0][1]
                btm_locator2 = locators[1][1][1]
            
                follow_top = space.create_multi_follow([self.follower_group, follow_transform], top_locator2, top_locator2, value = value)
                follow_btm = space.create_multi_follow([self.follower_group, follow_transform], btm_locator2, btm_locator2, value = 1-value)
            
                self._rename_followers(follow_top, 'top')
                self._rename_followers(follow_btm, 'btm')
                
        if increment == 'corner':
            
            space.create_multi_follow([self.follower_group, follow_transform], self.corner_xforms[0], self.corner_xforms[0], value = value)
            space.create_multi_follow([self.follower_group, follow_transform], self.corner_xforms[1], self.corner_xforms[1], value = value)

    def create_corner_falloff(self, inc, value):
        
        for side in ['L','R']:
            
            self.side = side
                 
            if side == 'L':
                
                corner_control = self.corner_offsets[0]
                
                if inc > 0:
                    corner_control = self.corner_offsets[0]
                if inc == 0:
                    corner_control = self.sub_corner_offsets[0]
                    
                top_control = self.zip_controls[inc][0][1]
                btm_control = self.zip_controls[inc][0][0]
        
                top_control_driver = self.control_dict[top_control][1]
                btm_control_driver = self.control_dict[btm_control][1]
            
            if side == 'R':
                
                corner_control = self.corner_offsets[1]
                
                if inc > 0:
                    corner_control = self.corner_offsets[1]
                if inc == 0:
                    corner_control = self.sub_corner_offsets[1]
                        
                #minus 4 and 3 to skip the corner controls
                top_control = self.zip_controls[inc][1][1]
                btm_control = self.zip_controls[inc][1][0]
            
                top_control_driver = self.control_dict[top_control][1]
                btm_control_driver = self.control_dict[btm_control][1]

        
            attr.connect_translate_multiply(corner_control, top_control_driver, value)
            attr.connect_translate_multiply(corner_control, btm_control_driver, value)
        
class WorldStickyLipRig(WorldStickyRig):

    def __init__(self, description, side):
        super(WorldStickyLipRig, self).__init__(description, side)
        
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
        
        self.control_count = 4
        
        self.main_control_group = cmds.group(em = True, n = core.inc_name(self._get_name('group', 'main_controls')))
        cmds.parent(self.main_control_group, self.control_group)
    
    def _create_curves(self):
        
        top_cv_count = len(self.top_joints) - 3
        btm_cv_count = len(self.btm_joints) - 3
        
        self.top_curve = geo.transforms_to_curve(self.top_joints, self.control_count, self.description + '_top')
        self.btm_curve = geo.transforms_to_curve(self.btm_joints, self.control_count, self.description + '_btm')
        
        self.top_guide_curve = geo.transforms_to_curve(self.top_joints, top_cv_count, self.description + '_top_guide')
        self.btm_guide_curve = geo.transforms_to_curve(self.btm_joints, btm_cv_count, self.description + '_btm_guide')
        
        cmds.parent(self.top_curve, self.setup_group)
        cmds.parent(self.btm_curve, self.setup_group)
        cmds.parent(self.top_guide_curve, self.btm_guide_curve, self.setup_group)
        
    def _cluster_curves(self):
        
        cluster_group = cmds.group(em = True, n = core.inc_name(self._get_name('group', 'clusters')))
        
        self.clusters_top = deform.cluster_curve(self.top_curve, self.description + '_top')
        self.clusters_btm = deform.cluster_curve(self.btm_curve, self.description + '_btm')
        
        self.clusters_guide_top = deform.cluster_curve(self.top_guide_curve, self.description + '_top_guide')
        self.clusters_guide_btm = deform.cluster_curve(self.btm_guide_curve, self.description + '_btm_guide')
        
        cmds.parent(self.clusters_top, self.clusters_btm, self.clusters_guide_top, self.clusters_guide_btm, cluster_group)
        cmds.parent(cluster_group, self.setup_group)
    
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
            geo.attach_to_curve(driver, self.top_curve, maintain_offset = True)

            driver = cmds.listRelatives(left_btm_control, p = True)[0]
            geo.attach_to_curve(driver, self.btm_curve, maintain_offset = True)
                
            if inc == negative_inc:
                break
            
            #do second part
            if len(controls) > 1:
                right_top_control = controls[1][1]
                right_btm_control = controls[1][0]            

                driver = cmds.listRelatives(right_top_control, p = True)[0]
                geo.attach_to_curve(driver, self.top_curve, maintain_offset = True)

                driver = cmds.listRelatives(right_btm_control, p = True)[0]
                geo.attach_to_curve(driver, self.btm_curve, maintain_offset = True)
                
            
            inc += 1

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
            top_local, top_xform = space.constrain_local(top_locator, self.clusters_guide_top[inc])
            btm_local, btm_xform = space.constrain_local(btm_locator, self.clusters_guide_btm[inc])

            cmds.parent(top_xform, btm_xform, self.setup_group)
    
            if inc == negative_inc:
                break
            
            #do second part
            if len(locators) > 1:
                top_locator = controls[1][1]
                btm_locator = controls[1][0]
            
                top_locator = self.control_dict[top_locator][0]
                btm_locator = self.control_dict[btm_locator][0]
                
                top_local, top_xform = space.constrain_local(top_locator, self.clusters_guide_top[negative_inc])
                btm_local, btm_xform = space.constrain_local(btm_locator, self.clusters_guide_btm[negative_inc])
                
                cmds.parent(top_xform, btm_xform, self.setup_group)
            
            inc += 1
        
    def _create_main_controls(self):
        
        inc = 0
        
        cluster_count = len(self.clusters_top)
        

        
        for inc in range(0, cluster_count):
        
            
            if inc == cluster_count:
                break
            
            negative_inc = cluster_count - (inc+1)
            
            self._create_main_control(self.clusters_top[inc], self.top_guide_curve, 'top')
            self._create_main_control(self.clusters_btm[inc], self.btm_guide_curve, 'btm')

            if inc == negative_inc:
                break
            
            self._create_main_control(self.clusters_top[negative_inc], self.top_guide_curve, 'top')
            self._create_main_control(self.clusters_btm[negative_inc], self.btm_guide_curve, 'btm')
            
            inc += 1
                    
    def _create_main_control(self, cluster, attach_curve, description):
        
        control = self._create_control(description)
        control.hide_scale_attributes()
        control.rotate_shape(90, 0, 0)
            
        control = control.get()
        space.MatchSpace(cluster, control).translation_to_rotate_pivot()
        
        control = rigs_util.Control(control)
        side = control.color_respect_side(False, self.center_tolerance)
        
        if side == 'C':
            control = control.get()
        
        if side != 'C':
            control = cmds.rename(control.get(), core.inc_name(control.get()[0:-1] + side))
        
        cmds.parent(control, self.main_control_group)
        
        xform = space.create_xform_group(control)
        driver = space.create_xform_group(control, 'driver')
        
        geo.attach_to_curve(xform, attach_curve)
        
        local_control, local_xform = space.constrain_local(control, cluster)
        driver_local_control = space.create_xform_group(local_control, 'driver')
        
        attr.connect_translate(driver, driver_local_control)
        
        cmds.parent(local_xform, self.setup_group)
        
        self.main_controls.append([control, xform, driver])
        
        return control
        
    def _create_sticky_control(self, transform, description):
        
        if not self.sticky_control_group:
            self.sticky_control_group = cmds.group(em = True, n = core.inc_name(self._get_name('group', 'sticky_controls')))
            
            cmds.parent(self.sticky_control_group, self.control_group)
        
        control = self._create_control(description, sub = True)
        
        control.rotate_shape(90,0,0)
        control.scale_shape(.5, .5, .5)
        
        
        control_name = control.get()
        
        space.MatchSpace(transform, control_name).translation_rotation()
                        
        control = control_name
        
        xform = space.create_xform_group(control)
        driver = space.create_xform_group(control, 'driver')
        
        cmds.parent(xform, self.sticky_control_group)
        
        return control, xform, driver
        
    def _create_corner_controls(self):
               
        orig_side = self.side
        
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
            
            space.MatchSpace(top_control_driver, control.get()).translation_rotation()
            
            xform = space.create_xform_group(control.get())
            space.create_xform_group(control.get(), 'driver')
            
            
            self.corner_controls.append([control.get(), xform])
            
            top_plus = attr.connect_translate_plus(control.get(), top_control_driver)
            btm_plus = attr.connect_translate_plus(control.get(), btm_control_driver)
            
            cmds.connectAttr('%s.translateX' % sub_control.get(), '%s.input3D[2].input3Dx' % top_plus)
            cmds.connectAttr('%s.translateY' % sub_control.get(), '%s.input3D[2].input3Dy' % top_plus)
            cmds.connectAttr('%s.translateZ' % sub_control.get(), '%s.input3D[2].input3Dz' % top_plus)
            
            cmds.connectAttr('%s.translateX' % sub_control.get(), '%s.input3D[2].input3Dx' % btm_plus)
            cmds.connectAttr('%s.translateY' % sub_control.get(), '%s.input3D[2].input3Dy' % btm_plus)
            cmds.connectAttr('%s.translateZ' % sub_control.get(), '%s.input3D[2].input3Dz' % btm_plus)
            
            geo.attach_to_curve(xform, self.top_guide_curve)
            
        
        self.side = orig_side
        
    def set_control_count(self, int_value):
        self.control_count = int_value
        
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
        
            attr.connect_translate_multiply(corner_control, top_control_driver, value)
            attr.connect_translate_multiply(corner_control, btm_control_driver, value)
        


    def create(self):
        super(WorldStickyLipRig, self).create()
        
        self._create_curves()
        
        self._cluster_curves()
        
        self._connect_curve_joints()
                
        self._connect_guide_clusters()
        
        self._create_main_controls()
        
        self._create_corner_controls()
    

#--- Body

class BackLeg(rigs.BufferRig):

    def __init__(self, description, side):
        super(BackLeg, self).__init__(description, side)

        self.curve_type = 'square'
        self.btm_chain_xform = None
        self.pole_offset = -1

    def _create_guide_chain(self):
        
        duplicate = space.DuplicateHierarchy(self.joints[0])
        duplicate.stop_at(self.joints[-3])
        duplicate.replace('joint', 'ikGuide')
        self.ikGuideChain = duplicate.create()
        
        duplicate = space.DuplicateHierarchy(self.joints[-1])
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
        
        duplicate = space.DuplicateHierarchy(self.ikGuideChain[0])
        duplicate.stop_at(self.ikGuideChain[-2])
        duplicate.replace('ikGuide', 'ikGuideOffset')
        self.offsetGuideChain = duplicate.create()
        
        cmds.parent(self.offsetGuideChain[0], self.ikGuideChain[0])

        duplicate = space.DuplicateHierarchy(self.ikGuideChain[2])
        duplicate.stop_at(self.ikGuideChain[-1])
        duplicate.replace('ikGuide', 'ikGuideOffsetBtm')
        self.offsetGuideChainBtm = duplicate.create()

        joint1 = self.offsetGuideChainBtm[0]
        joint2 = self.offsetGuideChainBtm[1]
        
        cmds.parent(joint2, w = True)
        cmds.parent(joint1, joint2)

        xform = space.create_xform_group(joint2)
        self.btm_chain_xform = xform
        
        self.offsetGuideChainBtm = [joint2, joint1]

        cmds.parent(xform, self.ikGuideChain[2])      

    def _create_offset_chain(self):
        duplicate = space.DuplicateHierarchy(self.joints[2])
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
        duplicate = space.DuplicateHierarchy(self.joints[3])
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
        joint1 = cmds.joint(n = core.inc_name( self._get_name('joint', 'poleTop') ) )
        joint2 = cmds.joint(n = core.inc_name( self._get_name('joint', 'poleBtm') ) )

        space.MatchSpace(self.buffer_joints[0], joint1).translation()
        space.MatchSpace(self.buffer_joints[-1], joint2).translation()

        ik_handle = space.IkHandle( self._get_name(description = 'pole') )
        
        ik_handle.set_start_joint( joint1 )
        ik_handle.set_end_joint( joint2 )
        ik_handle.set_solver(ik_handle.solver_sc)
        self.ik_pole = ik_handle.create()

        self.top_pole_ik = joint1

        cmds.pointConstraint(self.btm_control, self.ik_pole)

        cmds.parent(self.ik_pole, self.top_control)

        cmds.parent(self.top_pole_ik, self.setup_group)
        space.create_follow_group(self.top_control, self.top_pole_ik)
        cmds.hide(self.ik_pole)
    
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
            
            cmds.parentConstraint(source, target, mo = True)
            attr.connect_scale(source, target)

    def _create_top_control(self):
        
        control = self._create_control(description = 'top')
        control.hide_scale_and_visibility_attributes()
        
        control.set_curve_type(self.curve_type)            
        control.scale_shape(2, 2, 2)
        
        self.top_control = control.get()

        space.MatchSpace(self.ikGuideChain[0], self.top_control).translation_rotation()

        cmds.parentConstraint(self.top_control, self.ikGuideChain[0])

        xform = space.create_xform_group(self.top_control)

    def _create_btm_control(self):
        control = self._create_control(description = 'btm')
        control.hide_scale_and_visibility_attributes()
        
        control.set_curve_type(self.curve_type)
        control.scale_shape(2, 2, 2)
        
        self.btm_control = control.get()

        space.MatchSpace(self.ikGuideChain[-1], self.btm_control).translation_rotation()

        cmds.orientConstraint(self.btm_control, self.ikGuideChain[-1])

        space.create_xform_group(self.btm_control)

    def _create_top_offset_control(self):

        control = self._create_control(description = 'top_offset')
        control.hide_scale_and_visibility_attributes()
        control.set_curve_type(self.curve_type)

        self.top_offset = control.get()

        space.MatchSpace(self.ikGuideChain[2], self.top_offset).translation()

        xform_offset = space.create_xform_group(self.top_offset)

        follow = space.create_follow_group(self.ikGuideChain[2], xform_offset)

        cmds.parent(follow, self.top_control)
        
        cmds.parent(self.btm_chain_xform, self.ikGuideChain[-1])

    def _create_btm_offset_control(self):

        control = self._create_control(description = 'btm_offset')
        control.hide_scale_and_visibility_attributes()
        control.scale_shape(2, 2, 2)
        control.set_curve_type(self.curve_type)
        
        self.btm_offset = control.get()

        space.MatchSpace(self.offset1Chain[0], self.btm_offset).translation()

        xform = space.create_xform_group(self.btm_offset)
        
        driver = space.create_xform_group(self.btm_offset, 'driver')
        space.MatchSpace(self.ikGuideChain[-1], driver).rotate_scale_pivot_to_translation()
        
        space.create_follow_group(self.offsetGuideChainBtm[1], xform)

        cmds.parentConstraint(self.ikGuideChain[-1], self.offset2Chain[0], mo = True)

        cmds.parentConstraint(self.offset2Chain[-1], self.offset1Chain[0], mo = True)

    def _create_pole_vector(self):

        #if self.side == 'L':
        #    self.pole_offset = -1
        #if self.side == 'R':
        #    self.pole_offset = 1      
        
        control = self._create_control('POLE')
        control.hide_scale_and_visibility_attributes()
        control.set_curve_type('cube')
        self.pole_control = control.get()
        
        pole_var = attr.MayaEnumVariable('POLE_VECTOR')
        pole_var.create(self.btm_control)
        
        pole_vis = attr.MayaNumberVariable('poleVisibility')
        pole_vis.set_variable_type(pole_vis.TYPE_BOOL)
        pole_vis.create(self.btm_control)
        
        twist_var = attr.MayaNumberVariable('twist')
        twist_var.create(self.btm_control)
        
        if self.side == 'L':
            twist_var.connect_out('%s.twist' % self.main_ik)
            
        if self.side == 'R':
            attr.connect_multiply('%s.twist' % self.btm_control, '%s.twist' % self.main_ik, -1)
        
        pole_joints = [self.ikGuideChain[0], self.ikGuideChain[1], self.ikGuideChain[2]]
      
        position = space.get_polevector( pole_joints[0], pole_joints[1], pole_joints[2], self.pole_offset )

        cmds.move(position[0], position[1], position[2], control.get())

        cmds.poleVectorConstraint(control.get(), self.main_ik)
        
        xform_group = space.create_xform_group( control.get() )
        
        name = self._get_name()
        
        rig_line = rigs_util.RiggedLine(pole_joints[1], control.get(), name).create()
        cmds.parent(rig_line, self.control_group)
        
        pole_vis.connect_out('%s.visibility' % xform_group)
        pole_vis.connect_out('%s.visibility' % rig_line)
        
        self.pole_vector_xform = xform_group

        space.create_follow_group(self.top_pole_ik, xform_group)

    def _create_ik_guide_handle(self):
        
        ik_handle = space.IkHandle( self._get_name() )
        
        ik_handle.set_start_joint( self.ikGuideChain[0] )
        ik_handle.set_end_joint( self.ikGuideChain[-1] )
        ik_handle.set_solver(ik_handle.solver_rp)
        self.ik_handle = ik_handle.create()
        self.main_ik = self.ik_handle
        
        xform_ik_handle = space.create_xform_group(self.ik_handle)
        cmds.parent(xform_ik_handle, self.setup_group)

        cmds.pointConstraint(self.btm_control, self.ik_handle)
        
    def _create_ik_sub_guide_handle(self):

        ik_handle = space.IkHandle( self._get_name('sub') )
        
        ik_handle.set_start_joint( self.offsetGuideChain[0] )
        ik_handle.set_end_joint( self.offsetGuideChain[-1] )
        ik_handle.set_solver(ik_handle.solver_sc)
        self.ik_handle = ik_handle.create()
        
        xform_ik_handle = space.create_xform_group(self.ik_handle)

        cmds.parent(xform_ik_handle, self.offset1Chain[-1])
         
        stretch = rigs_util.StretchyChain()
        stretch.set_joints(self.ikGuideChain[0:4])
        stretch.set_node_for_attributes(self.btm_control)
        stretch.set_per_joint_stretch(False)
        stretch.set_add_dampen(True)
        
        cmds.connectAttr('%s.scaleX' % self.ikGuideChain[0], '%s.scaleX' % self.offsetGuideChain[0])
        cmds.connectAttr('%s.scaleX' % self.ikGuideChain[1], '%s.scaleX' % self.offsetGuideChain[1])
        
        cmds.connectAttr('%s.scaleX' % self.ikGuideChain[2], '%s.scaleX' % self.btm_chain_xform)
        cmds.connectAttr('%s.scaleX' % self.ikGuideChain[2], '%s.scaleY' % self.btm_chain_xform)
        cmds.connectAttr('%s.scaleX' % self.ikGuideChain[2], '%s.scaleZ' % self.btm_chain_xform)
        
        top_locator, btm_locator = stretch.create()
        
        cmds.parent(top_locator, self.top_control)
        cmds.parent(btm_locator, self.btm_control)
        

    def _create_ik_sub_guide_btm_handle(self):
        ik_handle = space.IkHandle( self._get_name('sub_btm') )
        
        ik_handle.set_start_joint( self.offsetGuideChainBtm[0] )
        ik_handle.set_end_joint( self.offsetGuideChainBtm[-1] )
        ik_handle.set_solver(ik_handle.solver_sc)
        self.ik_handle = ik_handle.create()
        
        xform_ik_handle = space.create_xform_group(self.ik_handle)

        cmds.parent(xform_ik_handle, self.top_offset)        

    def _create_ik_offset_handle(self):
        ik_handle = space.IkHandle( self._get_name('offset') )
        
        ik_handle.set_start_joint( self.offset1Chain[0] )
        ik_handle.set_end_joint( self.offset1Chain[-1] )
        ik_handle.set_solver(ik_handle.solver_sc)
        self.ik_handle = ik_handle.create()
        
        xform_ik_handle = space.create_xform_group(self.ik_handle)

        cmds.parent(xform_ik_handle, self.offsetGuideChainBtm[0])          

    def _create_ik_offset2_handle(self):
        ik_handle = space.IkHandle( self._get_name('offset') )
        
        ik_handle.set_start_joint( self.offset2Chain[0] )
        ik_handle.set_end_joint( self.offset2Chain[-1] )
        ik_handle.set_solver(ik_handle.solver_sc)
        self.ik_handle = ik_handle.create()
        
        xform_ik_handle = space.create_xform_group(self.ik_handle)

        cmds.parent(xform_ik_handle, self.btm_offset) 

        cmds.refresh()

    def set_pole_offset(self, offset_value):
        self.pole_offset = offset_value

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
   
class FrontLeg(rigs.BufferRig):

    def __init__(self, description, side):
        super(FrontLeg, self).__init__(description, side)

        self.curve_type = 'square'
    

    def _create_guide_chain(self):
        
        duplicate = space.DuplicateHierarchy(self.joints[0])
        duplicate.stop_at(self.joints[-1])
        duplicate.replace('joint', 'ikGuide')
        self.ikGuideChain = duplicate.create()
        
        cmds.parent(self.ikGuideChain[0], self.setup_group)

    def _create_sub_guide_chain(self):
        
        duplicate = space.DuplicateHierarchy(self.ikGuideChain[0])
        duplicate.stop_at(self.ikGuideChain[-2])
        duplicate.replace('ikGuide', 'ikGuideOffset')
        self.offsetGuideChain = duplicate.create()

        cmds.parent(self.offsetGuideChain[0], self.ikGuideChain[0])

        duplicate = space.DuplicateHierarchy(self.ikGuideChain[2])
        duplicate.stop_at(self.ikGuideChain[-1])
        duplicate.replace('ikGuide', 'ikGuideOffsetBtm')
        self.offsetGuideChainBtm = duplicate.create()

        joint1 = self.offsetGuideChainBtm[0]
        joint2 = self.offsetGuideChainBtm[1]
        
        cmds.parent(joint2, w = True)
        cmds.parent(joint1, joint2)

        xform = space.create_xform_group(joint2)
        self.btm_chain_xform = xform

        self.offsetGuideChainBtm = [joint2, joint1]

        cmds.parent(xform, self.ikGuideChain[2])      

    def _create_offset_chain(self):
        duplicate = space.DuplicateHierarchy(self.joints[2])
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
        duplicate = space.DuplicateHierarchy(self.joints[3])
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
        joint1 = cmds.joint(n = core.inc_name( self._get_name('joint', 'poleTop') ) )
        joint2 = cmds.joint(n = core.inc_name( self._get_name('joint', 'poleBtm') ) )

        space.MatchSpace(self.buffer_joints[0], joint1).translation()
        space.MatchSpace(self.buffer_joints[-1], joint2).translation()

        ik_handle = space.IkHandle( self._get_name(description = 'pole') )
        
        ik_handle.set_start_joint( joint1 )
        ik_handle.set_end_joint( joint2 )
        ik_handle.set_solver(ik_handle.solver_sc)
        self.ik_pole = ik_handle.create()

        self.top_pole_ik = joint1

        cmds.pointConstraint(self.btm_control, self.ik_pole)

        cmds.parent(self.ik_pole, self.top_control)

        cmds.parent(self.top_pole_ik, self.setup_group)
        space.create_follow_group(self.top_control, self.top_pole_ik)
        cmds.hide(self.ik_pole)

    def _duplicate_joints(self):
        super(FrontLeg, self)._duplicate_joints()

        self._create_guide_chain()
        self._create_sub_guide_chain()

        ik_chain = [self.offsetGuideChain[0], self.offsetGuideChain[1],  self.offsetGuideChainBtm[1], self.ikGuideChain[-1]]
        
        self._attach_ik_joints(ik_chain, self.buffer_joints)

    def _attach_ik_joints(self, source_chain, target_chain):
        for inc in range( 0, len(source_chain) ):
            source = source_chain[inc]
            target = target_chain[inc]

            cmds.parentConstraint(source, target, mo = True)
            attr.connect_scale(source, target)

    def _create_top_control(self):
        
        control = self._create_control(description = 'top')
        control.hide_scale_and_visibility_attributes()
        
        control.set_curve_type(self.curve_type)            
        control.scale_shape(2, 2, 2)
        
        self.top_control = control.get()

        space.MatchSpace(self.ikGuideChain[0], self.top_control).translation_rotation()

        cmds.parentConstraint(self.top_control, self.ikGuideChain[0])

        space.create_xform_group(self.top_control)

    def _create_btm_control(self):
        control = self._create_control(description = 'btm')
        control.hide_scale_and_visibility_attributes()
        
        control.set_curve_type(self.curve_type)
        control.scale_shape(2, 2, 2)
        
        self.btm_control = control.get()

        space.MatchSpace(self.ikGuideChain[-1], self.btm_control).translation_rotation()

        cmds.orientConstraint(self.btm_control, self.ikGuideChain[-1])

        space.create_xform_group(self.btm_control)

    def _create_btm_offset_control(self):

        control = self._create_control(description = 'btm_offset')
        control.hide_scale_and_visibility_attributes()
        control.set_curve_type(self.curve_type)

        self.btm_offset = control.get()

        space.MatchSpace(self.ikGuideChain[2], self.btm_offset).translation()

        xform_offset = space.create_xform_group(self.btm_offset)
        driver = space.create_xform_group(self.btm_offset, 'driver')
        
        space.MatchSpace(self.ikGuideChain[-1], driver).rotate_scale_pivot_to_translation()
        
        follow = space.create_follow_group(self.ikGuideChain[2], xform_offset)

        cmds.parent(follow, self.top_control)
        
        cmds.parent(self.btm_chain_xform, self.ikGuideChain[-1])


    def _create_pole_vector(self):

        if self.side == 'L':
            self.pole_offset = 1
        if self.side == 'R':
            self.pole_offset = 1      
        
        control = self._create_control('POLE')
        control.hide_scale_and_visibility_attributes()
        control.set_curve_type('cube')
        self.pole_control = control.get()
        
        pole_var = attr.MayaEnumVariable('POLE_VECTOR')
        pole_var.create(self.btm_control)
        
        pole_vis = attr.MayaNumberVariable('poleVisibility')
        pole_vis.set_variable_type(pole_vis.TYPE_BOOL)
        pole_vis.create(self.btm_control)
        
        twist_var = attr.MayaNumberVariable('twist')
        twist_var.create(self.btm_control)
        
        if self.side == 'L':
            twist_var.connect_out('%s.twist' % self.main_ik)
            
        if self.side == 'R':
            attr.connect_multiply('%s.twist' % self.btm_control, '%s.twist' % self.main_ik, -1)
        
        pole_joints = [self.ikGuideChain[0], self.ikGuideChain[1], self.ikGuideChain[2]]

      
        position = space.get_polevector( pole_joints[0], pole_joints[1], pole_joints[2], self.pole_offset )

        cmds.move(position[0], position[1], position[2], control.get())

        cmds.poleVectorConstraint(control.get(), self.main_ik)
        
        xform_group = space.create_xform_group( control.get() )
        
        name = self._get_name()
        
        rig_line = rigs_util.RiggedLine(pole_joints[1], control.get(), name).create()
        cmds.parent(rig_line, self.control_group)
        
        pole_vis.connect_out('%s.visibility' % xform_group)
        pole_vis.connect_out('%s.visibility' % rig_line)
        
        self.pole_vector_xform = xform_group

        space.create_follow_group(self.top_pole_ik, xform_group)

        

    def _create_ik_guide_handle(self):
        
        ik_handle = space.IkHandle( self._get_name() )
        
        ik_handle.set_start_joint( self.ikGuideChain[0] )
        ik_handle.set_end_joint( self.ikGuideChain[-1] )
        ik_handle.set_solver(ik_handle.solver_rp)
        self.ik_handle = ik_handle.create()
        self.main_ik = self.ik_handle
        
        xform_ik_handle = space.create_xform_group(self.ik_handle)
        cmds.parent(xform_ik_handle, self.setup_group)

        cmds.pointConstraint(self.btm_control, self.ik_handle)

    def _create_ik_sub_guide_handle(self):

        ik_handle = space.IkHandle( self._get_name('sub') )
        
        ik_handle.set_start_joint( self.offsetGuideChain[0] )
        ik_handle.set_end_joint( self.offsetGuideChain[-1] )
        ik_handle.set_solver(ik_handle.solver_sc)
        self.ik_handle = ik_handle.create()
        
        xform_ik_handle = space.create_xform_group(self.ik_handle)

        cmds.parent(xform_ik_handle, self.offsetGuideChainBtm[1])
         
        stretch = rigs_util.StretchyChain()
        stretch.set_joints(self.ikGuideChain[0:4])
        stretch.set_node_for_attributes(self.btm_control)
        stretch.set_per_joint_stretch(False)
        stretch.set_add_dampen(True)
        
        cmds.connectAttr('%s.scaleX' % self.ikGuideChain[0], '%s.scaleX' % self.offsetGuideChain[0])
        cmds.connectAttr('%s.scaleX' % self.ikGuideChain[1], '%s.scaleX' % self.offsetGuideChain[1])
        
        cmds.connectAttr('%s.scaleX' % self.ikGuideChain[2], '%s.scaleX' % self.btm_chain_xform)
        cmds.connectAttr('%s.scaleX' % self.ikGuideChain[2], '%s.scaleY' % self.btm_chain_xform)
        cmds.connectAttr('%s.scaleX' % self.ikGuideChain[2], '%s.scaleZ' % self.btm_chain_xform)
        
        top_locator, btm_locator = stretch.create()
        
        cmds.parent(top_locator, self.top_control)
        cmds.parent(btm_locator, self.btm_control)

    def _create_ik_sub_guide_btm_handle(self):
        ik_handle = space.IkHandle( self._get_name('sub_btm') )
        
        ik_handle.set_start_joint( self.offsetGuideChainBtm[0] )
        ik_handle.set_end_joint( self.offsetGuideChainBtm[-1] )
        ik_handle.set_solver(ik_handle.solver_sc)
        self.ik_handle = ik_handle.create()
        
        xform_ik_handle = space.create_xform_group(self.ik_handle)

        cmds.parent(xform_ik_handle, self.btm_offset)        

    def _create_ik_offset_handle(self):
        ik_handle = space.IkHandle( self._get_name('offset') )
        
        ik_handle.set_start_joint( self.offset1Chain[0] )
        ik_handle.set_end_joint( self.offset1Chain[-1] )
        ik_handle.set_solver(ik_handle.solver_sc)
        self.ik_handle = ik_handle.create()
        
        xform_ik_handle = space.create_xform_group(self.ik_handle)

        cmds.parent(xform_ik_handle, self.offsetGuideChainBtm[0])          

    def _create_ik_offset2_handle(self):
        ik_handle = space.IkHandle( self._get_name('offset') )
        
        ik_handle.set_start_joint( self.offset2Chain[0] )
        ik_handle.set_end_joint( self.offset2Chain[-1] )
        ik_handle.set_solver(ik_handle.solver_sc)
        self.ik_handle = ik_handle.create()
        
        xform_ik_handle = space.create_xform_group(self.ik_handle)

        cmds.parent(xform_ik_handle, self.btm_offset) 

        cmds.refresh()

    def create(self):
        super(FrontLeg, self).create()
                
        self._create_top_control()
        self._create_btm_control()
        self._create_btm_offset_control()

        self._create_ik_guide_handle()
        self._create_ik_sub_guide_handle()
        self._create_ik_sub_guide_btm_handle()

        self._create_pole_chain()

        self._create_pole_vector()   

class FinRig(rigs.JointRig):
    
    def _create_top_control(self):
        top_control = self._create_control('top')
        top_control.hide_scale_and_visibility_attributes()
        top_control.set_curve_type('cube')
        top_control.scale_shape(2, 2, 2)
        
        top_control = top_control.get()
        
        match = space.MatchSpace(self.joints[0], top_control)
        match.translation_rotation()
        
        space.create_xform_group(top_control)
        
        spread = attr.MayaNumberVariable('spread')
        spread.create(top_control)
        
        return top_control
    
    def _create_sub_controls(self, parent):
        
        sub_controls = []
        drivers = []
        
        joint_count = len(self.joints)
        
        section = 2.00/joint_count
        
        spread_offset = 1.00
        
        for joint in self.joints:
    
            sub_control = self._create_control(sub = True)
            sub_control.hide_scale_and_visibility_attributes()
            
            sub_control = sub_control.get()
            
            match = space.MatchSpace(joint, sub_control)
            match.translation_rotation()
            
            #cmds.parent(sub_control, parent)
            
            space.create_xform_group(sub_control)
            driver = space.create_xform_group(sub_control, 'driver')
            
            cmds.parentConstraint(sub_control, joint)
            cmds.scaleConstraint(sub_control, joint)
            
            attr.connect_multiply('%s.spread' % parent, '%s.rotateZ' % driver, spread_offset)
            
            
            attr.connect_plus('%s.translateX' % parent, '%s.translateX' % driver)
            attr.connect_plus('%s.translateY' % parent, '%s.translateY' % driver)
            attr.connect_plus('%s.translateZ' % parent, '%s.translateZ' % driver)
            
            attr.connect_plus('%s.rotateX' % parent, '%s.rotateX' % driver)
            attr.connect_plus('%s.rotateY' % parent, '%s.rotateY' % driver)
            attr.connect_plus('%s.rotateZ' % parent, '%s.rotateZ' % driver)
            
            
            
            sub_controls.append(sub_control)
            drivers.append(driver)
            
            spread_offset -= section
            
        
        rigs_util.create_attribute_lag(sub_controls[0], 'rotateY',  drivers[1:])
    
    def create(self):
        super(FinRig, self).create()
        
        top_control = self._create_top_control()
        
        self._create_sub_controls(top_control)

class SuspensionRig(rigs.BufferRig):
    
    def __init__(self, description, side):
        
        self.sections = []
        self.scale_constrain = None
        
        super(SuspensionRig, self).__init__(description, side)
                    
    def _create_joint_section(self, top_joint, btm_joint):

        ik = space.IkHandle( self._get_name() )
        
        ik.set_start_joint(top_joint)
        ik.set_end_joint(btm_joint)
        ik.set_solver(ik.solver_sc)
        ik.create()
        
        handle = ik.ik_handle
        
        stretch = rigs_util.StretchyChain()
        stretch.set_simple(True)
        
        stretch.set_joints([top_joint, btm_joint])
        stretch.set_description(self._get_name())        
                
        top_locator, btm_locator = stretch.create()
        
        top_control = self._create_control('top')
        top_control.rotate_shape(0, 0, 90)
        xform_top_control = space.create_xform_group(top_control.get())
        space.MatchSpace(top_joint, xform_top_control).translation_rotation()
        
        btm_control = self._create_control('btm')
        btm_control.rotate_shape(0, 0, 90)
        xform_btm_control = space.create_xform_group(btm_control.get())
        space.MatchSpace(btm_joint, xform_btm_control).translation_rotation()
        
        cmds.parent(top_locator, top_control.get())
        cmds.parent(btm_locator, btm_control.get())
        
        cmds.pointConstraint(top_control.get(), top_joint)
        cmds.parent(handle, btm_control.get())
        
        self.controls = [top_control.control, btm_control.control]
        self.xforms = [xform_top_control, xform_btm_control]
        
        cmds.hide(handle)
                    
    def create(self):
        
        super(SuspensionRig, self).create()
        
        self._create_joint_section(self.buffer_joints[0], self.buffer_joints[1])


class SimpleBackLeg(rigs.BufferRig):
    def __init__(self, description, side):
        super(SimpleBackLeg, self).__init__(description, side)
        
        self.pole_offset = 5
        self.create_sub_control = True
        
    def _duplicate_joints(self):
        super(SimpleBackLeg, self)._duplicate_joints()
        
        duplicate = space.DuplicateHierarchy(self.joints[0])
        duplicate.replace('joint', 'ik')
        duplicate.stop_at(self.joints[2])
        ik_chain = duplicate.create()
        
        duplicate = space.DuplicateHierarchy(self.joints[-2])
        duplicate.replace('joint', 'offset')
        duplicate.stop_at(self.joints[-1])
        self.lower_offset_chain = duplicate.create()
        
        cmds.parent( self.lower_offset_chain[-1], w = True )
        cmds.parent(self.lower_offset_chain[0], self.lower_offset_chain[-1])
        self.lower_offset_chain = [self.lower_offset_chain[-1], self.lower_offset_chain[0]]
        
        cmds.joint(self.lower_offset_chain[0], e = True, oj = 'xyz', secondaryAxisOrient = 'yup', zso = True)
        cmds.makeIdentity(self.lower_offset_chain[-1], jo = True, apply = True)
        
        attach_chain = ik_chain[:-1] + [self.lower_offset_chain[-1], self.lower_offset_chain[0]]
        
        self._attach_ik_joints(attach_chain, self.buffer_joints)
        
        self.ik_chain = ik_chain
        
        cmds.parent(self.ik_chain[0], self.setup_group)
        cmds.parent(self.lower_offset_chain[0], self.setup_group)
        
        return self.ik_chain
    
    def _attach_ik_joints(self, source_chain, target_chain):
        for inc in range( 0, len(source_chain) ):
            source = source_chain[inc]
            target = target_chain[inc]
            
            cmds.parentConstraint(source, target, mo = True)
            attr.connect_scale(source, target)
            
        
    def _create_pole_chain(self):
        
        #first
        joint1, joint2, ik = space.create_pole_chain(self.buffer_joints[0], self.buffer_joints[-1], 'pole')
        
        joint1 = cmds.rename(joint1, self._get_name('joint', 'poleTop'))
        joint2 = cmds.rename(joint2, self._get_name('joint', 'poleBtm'))
        
        #cmds.pointConstraint(self.btm_control, ik)

        cmds.parent(ik, self.group_main_ik)

        cmds.parent(joint1, self.top_control)
        
        cmds.hide(ik)
        
        self.top_pole_joint = joint1
        self.ik_pole = ik
        self.xform_ik_pole = space.create_xform_group(ik)

        #second
        joint1, joint2, ik = space.create_pole_chain(self.buffer_joints[0], self.buffer_joints[-1], 'pole2')
        
        
        
        joint1 = cmds.rename(joint1, self._get_name('joint', 'poleTop2'))
        joint2 = cmds.rename(joint2, self._get_name('joint', 'poleBtm2'))
        
        #cmds.pointConstraint(self.btm_control, ik)

        cmds.parent(ik, self.group_main_ik)
        

        cmds.parent(joint1, self.top_control)
        
        cmds.hide(ik)
        
        self.top_pole_joint2 = joint1
        self.ik_pole2 = ik

    def _create_pole_vector(self):

        #if self.side == 'L':
        #    self.pole_offset = -1
        #if self.side == 'R':
        #    self.pole_offset = 1      
        
        control = self._create_control('POLE')
        control.hide_scale_and_visibility_attributes()
        control.set_curve_type('cube')
        self.pole_control = control.get()
        
        pole_var = attr.MayaEnumVariable('POLE_VECTOR')
        pole_var.create(self.btm_control)
        
        pole_vis = attr.MayaNumberVariable('poleVisibility')
        pole_vis.set_variable_type(pole_vis.TYPE_BOOL)
        pole_vis.create(self.btm_control)
        
        twist_var = attr.MayaNumberVariable('twist')
        twist_var.create(self.btm_control)
        
        
        if self.side == 'L':
            twist_var.connect_out('%s.twist' % self.ik_pole)
            
        if self.side == 'R':
            attr.connect_multiply('%s.twist' % self.btm_control, '%s.twist' % self.ik_pole, -1)
        
        
        """
        if self.side == 'L':
            twist_var.connect_out('%s.twist' % self.ik_handle_top)
            
        if self.side == 'R':
            attr.connect_multiply('%s.twist' % self.btm_control, '%s.twist' % self.ik_handle_top, -1)
        """
        pole_joints = [self.ik_chain[0], self.ik_chain[1], self.ik_chain[2]]
      
        position = space.get_polevector( pole_joints[0], pole_joints[1], pole_joints[2], self.pole_offset )

        cmds.move(position[0], position[1], position[2], control.get())

        #cmds.poleVectorConstraint(control.get(), self.ik_handle_top)
        cmds.poleVectorConstraint(control.get(), self.ik_pole2)
        
        xform_group = space.create_xform_group( control.get() )
        
        name = self._get_name()
        
        rig_line = rigs_util.RiggedLine(pole_joints[1], control.get(), name).create()
        cmds.parent(rig_line, self.control_group)
        
        pole_vis.connect_out('%s.visibility' % xform_group)
        pole_vis.connect_out('%s.visibility' % rig_line)
        
        self.pole_vector_xform = xform_group

        cmds.parent(xform_group, self.top_pole_joint)

        #space.create_follow_group(self.top_pole_ik, xform_group)
        
        
        #cmds.parent(self.xform_offset_control, follow)
        

        
        
        
    def _create_ik(self):
        
        ik_handle = space.IkHandle( self._get_name() )
        
        ik_handle.set_start_joint( self.ik_chain[0] )
        ik_handle.set_end_joint( self.ik_chain[-1] )
        ik_handle.set_solver(ik_handle.solver_sc)
        self.ik_handle_top = ik_handle.create()
        
        ik_handle = space.IkHandle( self._get_name() )
        
        ik_handle.set_start_joint( self.lower_offset_chain[0] )
        ik_handle.set_end_joint( self.lower_offset_chain[1] )
        ik_handle.set_solver(ik_handle.solver_sc)
        self.ik_handle_btm = ik_handle.create()
        
    def _create_top_control(self):
        
        control = self._create_control('top')
        
        control.rotate_shape(0, 0, 90)
        control.hide_scale_attributes()
        
        space.MatchSpace(self.buffer_joints[0], control.get()).translation_rotation()
        
        space.create_xform_group(control.get())
        
        cmds.pointConstraint(control.get(), self.ik_chain[0])
        
        self.top_control = control.get()
        
        cmds.parent(self.group_main_ik, self.top_control)
        
    def _create_btm_control(self):
        
        control = self._create_control('btm')
        control.hide_scale_attributes()
        
        space.MatchSpace(self.buffer_joints[-1], control.get()).translation_rotation()
        
        space.create_xform_group(control.get())
        
        self.btm_control = control.get()
        
        self.btm_ik_control = self.btm_control
        
        if self.create_sub_control:
            sub_control = self._create_control('BTM', sub = True)
            sub_control.scale_shape(.8, .8, .8)
            sub_control.hide_scale_and_visibility_attributes()
            
            xform_group = space.create_xform_group( sub_control.get() )
            
            self.sub_control = sub_control.get()
        
            cmds.parent(xform_group, control.get())
            
            space.MatchSpace(control.get(), xform_group).translation_rotation()
            
            attr.connect_visibility('%s.subVisibility' % self.btm_control, '%sShape' % self.sub_control, 1)
        
            self.btm_ik_control = self.sub_control
        
        cmds.orientConstraint(self.sub_control, self.ik_chain[-1])
        cmds.pointConstraint(self.btm_ik_control, self.group_main_ik)
        
    def _create_offset_control(self):
        
        control = self._create_control('offset', True)
        control.set_curve_type('square')
        control.hide_scale_attributes()
        
        space.MatchSpace(self.buffer_joints[-1], control.get()).translation_rotation()
        #space.MatchSpace(self.buffer_joints[-1], control.get()).rotation()
        
        xform = space.create_xform_group(control.get())
        driver = space.create_xform_group(control.get(), 'driver')
        
        cmds.parent(xform, self.top_pole_joint2)
        
        cmds.pointConstraint(self.group_main_ik, xform)
        space.create_follow_group(control.get(), self.lower_offset_chain[0])
        
        
        self.offset_control = control.get()
        self.xform_offset_control = xform
        
    def _attach_ik_handles(self):
        
        top_ik = self.ik_handle_top
        btm_ik = self.ik_handle_btm
        
        cmds.parent(top_ik, self.lower_offset_chain[0])
        cmds.parent(btm_ik, self.offset_control)
        
        cmds.hide(top_ik, btm_ik)
        
    def _create_stretchy(self, top_transform, btm_transform, control):
        
        stretchy = rigs_util.StretchyChain()
        stretchy.set_joints(self.ik_chain)
        #dampen should be damp... dampen means wet, damp means diminish
        stretchy.set_add_dampen(True)
        stretchy.set_node_for_attributes(control)
        stretchy.set_description(self._get_name())
        stretchy.set_extra_joint(self.lower_offset_chain[0])
        
        #this is new stretch distance
        #stretchy.set_vector_instead_of_matrix(False)
        top_locator, btm_locator = stretchy.create()
        
        
        
        cmds.parent(top_locator, top_transform)
        cmds.parent(btm_locator, btm_transform)
        
    def set_pole_offset(self, value):
        self.pole_offset = value
        
    def create(self):
        super(SimpleBackLeg, self).create()
        
        self.group_main_ik = cmds.group(em = True, n = core.inc_name(self._get_name('group', 'main_ik')))
        space.MatchSpace(self.joints[-1], self.group_main_ik).translation_rotation()
        
        self._create_ik()
        
        self._create_top_control()
        self._create_btm_control()
        
        self._create_pole_chain()
    
        self._create_pole_vector()
        
        self._create_offset_control()
        
        self._attach_ik_handles()
        
        self._create_stretchy(self.top_control, self.btm_control, self.btm_control)
        

class BackLeg2(rigs.BufferRig):

    def __init__(self, description, side):
        super(BackLeg2, self).__init__(description, side)

        self.curve_type = 'square'
        self.btm_chain_xform = None
        self.pole_offset = -1

    def _create_guide_chain(self):
        
        
        duplicate = space.DuplicateHierarchy(self.joints[0])
        duplicate.stop_at(self.joints[-3])
        duplicate.replace('joint', 'ikGuide')
        self.ikGuideChain = duplicate.create()
        
        duplicate = space.DuplicateHierarchy(self.joints[-1])
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
        
        duplicate = space.DuplicateHierarchy(self.ikGuideChain[0])
        duplicate.stop_at(self.ikGuideChain[-2])
        duplicate.replace('ikGuide', 'ikGuideOffset')
        self.offsetGuideChain = duplicate.create()
        
        cmds.parent(self.offsetGuideChain[0], self.ikGuideChain[0])

        duplicate = space.DuplicateHierarchy(self.ikGuideChain[2])
        duplicate.stop_at(self.ikGuideChain[-1])
        duplicate.replace('ikGuide', 'ikGuideOffsetBtm')
        self.offsetGuideChainBtm = duplicate.create()

        joint1 = self.offsetGuideChainBtm[0]
        joint2 = self.offsetGuideChainBtm[1]
        
        cmds.parent(joint2, w = True)
        cmds.parent(joint1, joint2)

        xform = space.create_xform_group(joint2)
        
        self.triangle_xform = xform
        
        self.btm_chain_xform = xform
        
        self.offsetGuideChainBtm = [joint2, joint1]
        
        cmds.parent(xform, self.ikGuideChain[2])      

    def _create_offset_chain(self):
        duplicate = space.DuplicateHierarchy(self.joints[2])
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
        duplicate = space.DuplicateHierarchy(self.joints[3])
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
        joint1 = cmds.joint(n = core.inc_name( self._get_name('joint', 'poleTop') ) )
        joint2 = cmds.joint(n = core.inc_name( self._get_name('joint', 'poleBtm') ) )

        space.MatchSpace(self.buffer_joints[0], joint1).translation()
        space.MatchSpace(self.buffer_joints[-1], joint2).translation()

        ik_handle = space.IkHandle( self._get_name(description = 'pole') )
        
        ik_handle.set_start_joint( joint1 )
        ik_handle.set_end_joint( joint2 )
        ik_handle.set_solver(ik_handle.solver_sc)
        self.ik_pole = ik_handle.create()

        self.top_pole_ik = joint1

        cmds.pointConstraint(self.btm_control, self.ik_pole)

        cmds.parent(self.ik_pole, self.top_control)

        cmds.parent(self.top_pole_ik, self.setup_group)
        space.create_follow_group(self.top_control, self.top_pole_ik)
        cmds.hide(self.ik_pole)
    
    def _duplicate_joints(self):
        super(BackLeg2, self)._duplicate_joints()

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
            
            cmds.parentConstraint(source, target, mo = True)
            attr.connect_scale(source, target)

    def _create_top_control(self):
        
        control = self._create_control(description = 'top')
        control.hide_scale_and_visibility_attributes()
        
        control.set_curve_type(self.curve_type)            
        control.scale_shape(2, 2, 2)
        
        self.top_control = control 

        space.MatchSpace(self.ikGuideChain[0], self.top_control).translation_rotation()

        cmds.parentConstraint(self.top_control, self.ikGuideChain[0])

        space.create_xform_group(self.top_control)
        

    def _create_btm_control(self):
        control = self._create_control(description = 'btm')
        control.hide_scale_and_visibility_attributes()
        
        control.set_curve_type(self.curve_type)
        control.scale_shape(2, 2, 2)
        
        self.btm_control = control 

        space.MatchSpace(self.ikGuideChain[-1], self.btm_control).translation_rotation()

        #attr.connect_rotate(self.btm_control, self.ikGuideChain[-1])
        cmds.orientConstraint(self.btm_control, self.ikGuideChain[-1])

        space.create_xform_group(self.btm_control)

    def _create_top_offset_control(self):

        control = self._create_control(description = 'top_offset')
        control.hide_scale_and_visibility_attributes()
        control.set_curve_type(self.curve_type)

        self.top_offset = control 

        space.MatchSpace(self.ikGuideChain[2], self.top_offset).translation()

        xform_offset = space.create_xform_group(self.top_offset)

        follow = space.create_follow_group(self.ikGuideChain[2], xform_offset)
        

        cmds.parent(follow, self.top_control)
        
        #cmds.parent(self.btm_chain_xform, self.ikGuideChain[-1])

    def _create_btm_offset_control(self):

        control = self._create_control(description = 'btm_offset')
        control.hide_scale_and_visibility_attributes()
        control.scale_shape(2, 2, 2)
        control.set_curve_type(self.curve_type)
        
        self.btm_offset = control 

        space.MatchSpace(self.offset1Chain[0], self.btm_offset).translation()

        xform = space.create_xform_group(self.btm_offset)
        
        driver = space.create_xform_group(self.btm_offset, 'driver')
        space.MatchSpace(self.ikGuideChain[-1], driver).rotate_scale_pivot_to_translation()
        
        follow = space.create_follow_group(self.offsetGuideChainBtm[1], xform)
        attr.connect_scale(self.ikGuideChain[2], follow)

        cmds.parentConstraint(self.ikGuideChain[-1], self.offset2Chain[0], mo = True)
        cmds.parentConstraint(self.offset2Chain[-1], self.offset1Chain[0], mo = True)

    def _create_pole_vector(self):

        #if self.side == 'L':
        #    self.pole_offset = -1
        #if self.side == 'R':
        #    self.pole_offset = 1      
        
        control = self._create_control('POLE')
        control.hide_scale_and_visibility_attributes()
        control.set_curve_type('cube')
        self.pole_control = control.get()
        
        pole_var = attr.MayaEnumVariable('POLE_VECTOR')
        pole_var.create(self.btm_control)
        
        pole_vis = attr.MayaNumberVariable('poleVisibility')
        pole_vis.set_variable_type(pole_vis.TYPE_BOOL)
        pole_vis.create(self.btm_control)
        
        twist_var = attr.MayaNumberVariable('twist')
        twist_var.create(self.btm_control)
        
        if self.side == 'L':
            twist_var.connect_out('%s.twist' % self.main_ik)
            
        if self.side == 'R':
            attr.connect_multiply('%s.twist' % self.btm_control, '%s.twist' % self.main_ik, -1)
        
        pole_joints = [self.ikGuideChain[0], self.ikGuideChain[1], self.ikGuideChain[2]]
      
        position = space.get_polevector( pole_joints[0], pole_joints[1], pole_joints[2], self.pole_offset )

        cmds.move(position[0], position[1], position[2], control.get())

        cmds.poleVectorConstraint(control.get(), self.main_ik)
        
        xform_group = space.create_xform_group( control.get() )
        
        name = self._get_name()
        
        rig_line = rigs_util.RiggedLine(pole_joints[1], control.get(), name).create()
        cmds.parent(rig_line, self.control_group)
        
        pole_vis.connect_out('%s.visibility' % xform_group)
        pole_vis.connect_out('%s.visibility' % rig_line)
        
        self.pole_vector_xform = xform_group

        space.create_follow_group(self.top_pole_ik, xform_group)

    def _create_ik_guide_handle(self):
        
        ik_handle = space.IkHandle( self._get_name() )
        
        ik_handle.set_start_joint( self.ikGuideChain[0] )
        ik_handle.set_end_joint( self.ikGuideChain[-1] )
        ik_handle.set_solver(ik_handle.solver_rp)
        self.ik_handle = ik_handle.create()
        self.main_ik = self.ik_handle
        
        xform_ik_handle = space.create_xform_group(self.ik_handle)
        cmds.parent(xform_ik_handle, self.setup_group)

        cmds.pointConstraint(self.btm_control, self.ik_handle)
        
    def _create_ik_sub_guide_handle(self):

        ik_handle = space.IkHandle( self._get_name('sub') )
        
        ik_handle.set_start_joint( self.offsetGuideChain[0] )
        ik_handle.set_end_joint( self.offsetGuideChain[-1] )
        ik_handle.set_solver(ik_handle.solver_sc)
        self.ik_handle = ik_handle.create()
        
        xform_ik_handle = space.create_xform_group(self.ik_handle)

        cmds.parent(xform_ik_handle, self.offset1Chain[-1])
         
        
        

    def _create_ik_sub_guide_btm_handle(self):
        ik_handle = space.IkHandle( self._get_name('sub_btm') )
        
        ik_handle.set_start_joint( self.offsetGuideChainBtm[0] )
        ik_handle.set_end_joint( self.offsetGuideChainBtm[-1] )
        ik_handle.set_solver(ik_handle.solver_sc)
        self.ik_handle = ik_handle.create()
        
        xform_ik_handle = space.create_xform_group(self.ik_handle)

        cmds.parent(xform_ik_handle, self.triangle_xform)
        space.create_follow_group(self.top_offset, xform_ik_handle)

        #cmds.parent(xform_ik_handle, self.top_offset)        

    def _create_ik_offset_handle(self):
        ik_handle = space.IkHandle( self._get_name('offset') )
        
        ik_handle.set_start_joint( self.offset1Chain[0] )
        ik_handle.set_end_joint( self.offset1Chain[-1] )
        ik_handle.set_solver(ik_handle.solver_sc)
        self.ik_handle = ik_handle.create()
        
        xform_ik_handle = space.create_xform_group(self.ik_handle)
        
        cmds.parent(xform_ik_handle, self.offsetGuideChainBtm[0])          

    def _create_ik_offset2_handle(self):
        ik_handle = space.IkHandle( self._get_name('offset') )
        
        ik_handle.set_start_joint( self.offset2Chain[0] )
        ik_handle.set_end_joint( self.offset2Chain[-1] )
        ik_handle.set_solver(ik_handle.solver_sc)
        self.ik_handle = ik_handle.create()
        
        xform_ik_handle = space.create_xform_group(self.ik_handle)

        cmds.parent(xform_ik_handle, self.triangle_xform)
        #last
        space.create_follow_group(self.btm_offset, xform_ik_handle)
        #cmds.parent(xform_ik_handle, self.btm_offset) 

        cmds.refresh()

    def _setup_stretch(self):
        
        stretch = rigs_util.StretchyChain()
        stretch.set_joints(self.ikGuideChain[0:4])
        stretch.set_node_for_attributes(self.btm_control)
        stretch.set_per_joint_stretch(False)
        stretch.set_add_dampen(True)
        
        cmds.connectAttr('%s.scaleX' % self.ikGuideChain[0], '%s.scaleX' % self.offsetGuideChain[0])
        cmds.connectAttr('%s.scaleX' % self.ikGuideChain[1], '%s.scaleX' % self.offsetGuideChain[1])
        
        #cmds.connectAttr('%s.scaleX' % self.ikGuideChain[2], '%s.scaleX' % self.btm_chain_xform)
        #cmds.connectAttr('%s.scaleX' % self.ikGuideChain[2], '%s.scaleY' % self.btm_chain_xform)
        #cmds.connectAttr('%s.scaleX' % self.ikGuideChain[2], '%s.scaleZ' % self.btm_chain_xform)
        
        top_locator, btm_locator = stretch.create()
        
        cmds.parent(top_locator, self.top_control)
        cmds.parent(btm_locator, self.btm_control)
        

    def set_pole_offset(self, offset_value):
        self.pole_offset = offset_value

    def create(self):
        super(BackLeg2, self).create()
                
        self._create_top_control()
        self._create_btm_control()
        self._create_top_offset_control()
        self._create_btm_offset_control()

        self._create_ik_guide_handle()
        self._create_ik_sub_guide_handle()
        self._create_ik_sub_guide_btm_handle()
        self._create_ik_offset_handle()
        self._create_ik_offset2_handle()

        self._setup_stretch() 

        #self._create_pole_chain()

        #self._create_pole_vector()  
        
        self.create_aim_setup()
     
class IkFrontLegRig(rigs.IkAppendageRig):
    
    
    def __init__(self, description, side):
        super(IkFrontLegRig, self).__init__(description, side)
        
        self.right_side_fix = False
    
    def _create_twist_joint(self, top_control):
        
        top_guide_joint, btm_guide_joint, guide_ik = space.create_pole_chain(self.buffer_joints[0], self.buffer_joints[-1], 'guide')
        
        top_guide_joint = cmds.rename(top_guide_joint, self._get_name('joint', 'poleTop'))
        cmds.rename(btm_guide_joint, self._get_name('joint', 'poleBtm'))
        guide_ik = cmds.rename(guide_ik, self._get_name('ikHandle', 'poleGuide'))
        
        self.twist_guide = top_guide_joint
        
        cmds.parent(top_guide_joint, self.setup_group)
        cmds.parent(guide_ik, self.setup_group)
        
        cmds.pointConstraint( self.top_control, top_guide_joint)
        
        self.offset_locator = None
        self.off_offset_locator = cmds.spaceLocator(n = self._get_name('offset', 'guideTwist'))[0]
        space.MatchSpace( self.sub_control, self.off_offset_locator ).translation_rotation()
        cmds.parent(self.off_offset_locator, self.top_control)
        
        if self.sub_control:
            self.offset_locator = cmds.spaceLocator(n = 'offset_%s' % self.sub_control)[0]
            cmds.parent(self.offset_locator, self.sub_control)
            
            match = space.MatchSpace(self.sub_control, self.offset_locator)
            match.translation_rotation()
            
        if not self.sub_control:
            self.offset_locator = cmds.spaceLocator(n = 'offset_%s' % self.btm_control)[0]
            cmds.parent(self.offset_locator, self.btm_control)
            
            match = space.MatchSpace(self.btm_control, self.offset_locator)
            match.translation_rotation()
        
        cmds.hide(self.offset_locator, self.off_offset_locator)
        
        cmds.pointConstraint( self.offset_locator, guide_ik, mo = True )
        
        #cmds.orientConstraint( self.off_offset_locator, guide_ik, mo = True )
        #cmds.orientConstraint( self.offset_locator, guide_ik, mo = True )
        
        self.twist_guide_ik = guide_ik
        
        self.offset_pole_locator = self.offset_locator
                
        
    def _create_pole_vector(self):
        
        control = self.poleControl
        self.poleControl = self.poleControl.get()
        
        attr.create_title(self.btm_control, 'POLE_VECTOR')
        
        pole_vis = attr.MayaNumberVariable('poleVisibility')
        pole_vis.set_variable_type(pole_vis.TYPE_BOOL)
        pole_vis.create(self.btm_control)
        
        twist_var = attr.MayaNumberVariable('twist')
        twist_var.create(self.btm_control)
        
        if self.side == 'L':
            attr.connect_multiply('%s.twist' % self.btm_control, '%s.twist' % self.ik_handle, -1)
            
            
        if self.side == 'R':
            twist_var.connect_out('%s.twist' % self.ik_handle)
        
        
        pole_joints = self._get_pole_joints()
        
        position = space.get_polevector( pole_joints[0], pole_joints[1], pole_joints[2], self.pole_offset )
        cmds.move(position[0], position[1], position[2], control.get())
        
        cmds.poleVectorConstraint(control.get(), self.ik_handle)
        
        xform_group = space.create_xform_group( control.get() )
        
        follow_group = None
        self.pole_vector_xform = xform_group
        
        if self.create_twist:

                
            cmds.parentConstraint(self.twist_guide, xform_group, mo = True)[0]
            
            follow_group = xform_group
            
            #constraint_editor = util.ConstraintEditor()
            
            
            space.create_multi_follow([self.off_offset_locator, self.offset_locator], self.twist_guide_ik, self.btm_control, attribute_name = 'autoTwist', value = 0)
                        
        
        
        if not self.create_twist:
            if self.pole_follow_transform:
                space.create_follow_group(self.pole_follow_transform, xform_group)
                
            

        
        name = self._get_name()
        
        rig_line = rigs_util.RiggedLine(pole_joints[1], control.get(), name).create()
        cmds.parent(rig_line, self.control_group)
        
        pole_vis.connect_out('%s.visibility' % xform_group)
        pole_vis.connect_out('%s.visibility' % rig_line)
        
        
        
        
    def _create_stretchy(self, top_transform, btm_transform, control):
        stretchy = rigs_util.StretchyChain()
        stretchy.set_joints(self.ik_chain)
        #dampen should be damp... dampen means wet, damp means diminish
        stretchy.set_add_dampen(True, 'damp')
        stretchy.set_node_for_attributes(control)
        stretchy.set_description(self._get_name())
        #this is new stretch distance
        #stretchy.set_vector_instead_of_matrix(False)
        top_locator, btm_locator = stretchy.create()
        
        cmds.parent(top_locator, top_transform)
        cmds.parent(btm_locator, self.offset_locator)
        
        #this is new stretch distance
        """
        cmds.parent(top_locator, self.setup_group)
        cmds.parent(btm_locator, self.setup_group)
        
        cmds.pointConstraint(top_transform, top_locator)
        cmds.pointConstraint(btm_transform, btm_locator)
        """
        
    def create(self):
        super(IkFrontLegRig, self).create()
        #turn me back on right away
        
        cmds.setAttr('%s.translateY' % self.pole_vector_xform, 0)
        
        ik_xform = cmds.listRelatives(self.ik_handle, p = True)
        cmds.parent(ik_xform, self.offset_locator)
        
        
class IkBackLegRig(IkFrontLegRig):
    
    def __init__(self, description, side):
        super(IkBackLegRig, self).__init__(description, side)
        
        self.offset_control_to_locator = False
        self.right_side_fix = False
    
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
            
            cmds.parentConstraint(self.offset_chain[inc], self.buffer_joints[inc], mo = True)
            attr.connect_scale(self.offset_chain[inc], self.buffer_joints[inc])
            
            cmds.connectAttr('%s.scaleX' % self.ik_chain[inc], 
                             '%s.scaleX' % self.offset_chain[inc])
        
        cmds.orientConstraint(self.ik_chain[-1], self.buffer_joints[-1], mo = True)
        
        cmds.parentConstraint(self.ik_chain[0], self.offset_chain[0], mo = True)
    

    
    def _create_offset_chain(self, parent = None):
        
        if not parent:
            parent = self.setup_group
        
        duplicate = space.DuplicateHierarchy(self.joints[0])
        duplicate.stop_at(self.joints[-1])
        duplicate.replace('joint', 'offset')        
        self.offset_chain = duplicate.create()
        
        cmds.parent(self.offset_chain[0], self.setup_group)
        
        duplicate = space.DuplicateHierarchy(self.offset_chain[-2])
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
    

    def _get_pole_joints(self):
        
        if not self.pole_angle_joints:
        
            return [self.ik_chain[0], self.ik_chain[1], self.ik_chain[2]]
            
        return self.pole_angle_joints
                
        
    def _create_offset_control(self):
        
        
        if not self.offset_control_to_locator:
            control = self._create_control(description = 'offset')
            control.hide_scale_and_visibility_attributes()
            control.scale_shape(2, 2, 2)
            control.set_curve_type('square')
            
            self.offset_control = control.get()
            
            match = space.MatchSpace(self.lower_offset_chain[1], self.offset_control)
            match.rotation()

            match = space.MatchSpace(self.lower_offset_chain[0], self.offset_control)
            match.translation()
        
        if self.offset_control_to_locator:
            self.offset_control = cmds.spaceLocator(n = 'locator_%s' % self._get_name('offset'))[0]
            
            match = space.MatchSpace(self.lower_offset_chain[0], self.offset_control)
            match.translation()
            cmds.hide(self.offset_control)
        
        cmds.parentConstraint(self.offset_control, self.lower_offset_chain[0], mo = True)

        xform_group = space.create_xform_group(self.offset_control)
        driver_group = space.create_xform_group(self.offset_control, 'driver')
        
        attr.create_title(self.btm_control, 'OFFSET_ANKLE')
                
        offset = attr.MayaNumberVariable('offsetAnkle')
        
        offset.create(self.btm_control)
        offset.connect_out('%s.rotateZ' % driver_group)
        
        follow_group = space.create_follow_group(self.ik_chain[-2], xform_group)
        
        scale_constraint = cmds.scaleConstraint(self.ik_chain[-2], follow_group)[0]
        space.scale_constraint_to_local(scale_constraint)
        #self._unhook_scale_constraint(scale_constraint)
        
        cmds.parent(follow_group, self.top_control)
        
        if not self.offset_control_to_locator:
            control.hide_translate_attributes()
        
        return self.offset_control
    
    def _rig_offset_chain(self):
        
        ik_handle = space.IkHandle( self._get_name('offset_top') )
        
        ik_handle.set_start_joint( self.offset_chain[0] )
        ik_handle.set_end_joint( self.offset_chain[-1] )
        ik_handle.set_solver(ik_handle.solver_rp)
        ik_handle = ik_handle.create()

        cmds.parent(ik_handle, self.lower_offset_chain[-1])

        ik_handle_btm = space.IkHandle( self._get_name('offset_btm'))
        ik_handle_btm.set_start_joint(self.lower_offset_chain[0])
        ik_handle_btm.set_end_joint(self.lower_offset_chain[-1])
        ik_handle_btm.set_solver(ik_handle_btm.solver_sc)
        ik_handle_btm = ik_handle_btm.create()
        
        follow = space.create_follow_group( self.offset_control, ik_handle_btm)
        cmds.parent(follow, self.setup_group)
        cmds.hide(ik_handle_btm)
    
    def set_offset_control_to_locator(self, bool_value):
        self.offset_control_to_locator = bool_value
    
    def create(self):
        
        super(IkBackLegRig, self).create()
        
        self._create_offset_control()
        
        self._rig_offset_chain()
        
        
        

class IkScapulaRig(rigs.BufferRig):
    
    def __init__(self, description, side):
        super(IkScapulaRig, self).__init__(description, side)
        
        self.control_offset = 10
    
    def _create_top_control(self):
        control = self._create_control()
        control.set_curve_type(self.control_shape)
        control.hide_scale_and_visibility_attributes()
        
        self._offset_control(control)
        
        space.create_xform_group(control.get())
        
        return control.get()
    
    def _create_shoulder_control(self):
        control = self._create_control()
        control.set_curve_type(self.control_shape)
        control.hide_scale_and_visibility_attributes()
        
        space.MatchSpace(self.joints[0], control.get()).translation()
        cmds.parentConstraint(control.get(), self.joints[0], mo = True)
        #cmds.pointConstraint(control.get(), self.joints[0], mo = True)
        
        space.create_xform_group(control.get())
        
        return control.get()
    
    def _offset_control(self, control ):
        
        offset = cmds.group(em = True)
        match = space.MatchSpace(self.joints[-1], offset)
        match.translation_rotation()
        
        cmds.move(self.control_offset, 0,0 , offset, os = True, wd = True, r = True)
        
        match = space.MatchSpace(offset, control.get())
        match.translation()
        
        cmds.delete(offset)
    
    def _create_ik(self, control):
        
        handle = space.IkHandle(self._get_name())
        handle.set_start_joint(self.joints[0])
        handle.set_end_joint(self.joints[-1])
        handle.set_solver(handle.solver_sc)
        handle = handle.create()
        
        cmds.pointConstraint(control, handle)
        
        cmds.parent(handle, control)
        cmds.hide(handle)
        
    
    def set_control_offset(self, value):
        self.control_offset = value
    
    def create(self):
        super(IkScapulaRig, self).create()
        
        control = self._create_top_control()
        self._create_shoulder_control()
        
        self._create_ik(control)
        
        rig_line = rigs_util.RiggedLine(control, self.joints[-1], self._get_name()).create()
        cmds.parent(rig_line, self.control_group) 




class IkQuadSpineRig(rigs.FkCurveRig):
    def __init__(self, name, side):
        super(IkQuadSpineRig, self).__init__(name, side)
        
        self.mid_control_joint = None
    
    def _create_sub_control(self):
        
        sub_control = rigs_util.Control( self._get_control_name(sub = True) )
        sub_control.color( attr.get_color_of_side( self.side , True)  )
        if self.control_shape:
            sub_control.set_curve_type(self.control_shape)
        
        sub_control.scale_shape(.75, .75, .75)
        
        if self.current_increment == 0:
            sub_control.set_curve_type(self.control_shape)
        
        if self.current_increment == 1:
            other_sub_control = rigs_util.Control( self._get_control_name('reverse', sub = True))
            other_sub_control.color( attr.get_color_of_side( self.side, True ) )
        
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
            parent = cmds.listRelatives(self.sub_controls[-1], p = True)[0]
            xform = cmds.listRelatives(parent, p = True)[0]
            
            other_sub_control.hide_scale_and_visibility_attributes()
            
            cmds.parent(xform, other_sub)
        
        if self.current_increment == 2:
            pass
        
        return sub_control
    
    def set_mid_control_joint(self, joint_name):
        self.mid_control_joint = joint_name
        

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
        space.MatchSpace(toe_control, follow_toe_control).translation_rotation()
        xform_follow = space.create_xform_group(follow_toe_control)
        
        cmds.parent(xform_follow, yawout_roll)
        attr.connect_rotate(toe_control, follow_toe_control)
        
        cmds.parentConstraint(ball_roll, self.roll_control_xform, mo = True)
        
        cmds.parentConstraint(toe_control, self.ball_handle, mo = True)
        cmds.parentConstraint(ball_roll, self.ankle_handle, mo = True)
        
        
        return [ball_pivot, toe_fk_control_xform]
                
    def set_index_order(self,index_list):
        self.defined_joints = index_list  
        

class BackFootRollRig(QuadFootRollRig):
    
    def __init__(self, name, side):
        super(BackFootRollRig, self).__init__(name, side)
        
        self.add_bank = True
        self.extra_ball = None
    
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
        
        attr.disconnect_attribute('%sShape.visibility' % control)
        cmds.setAttr('%sShape.visibility' % control, 1)
        
        attr.connect_reverse('%s.ikFk' % self.roll_control.get(), '%sShape.visibility' % control)
        
        cmds.parent(xform, parent)
        
        attribute_control = self._get_attribute_control()
        
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.forward_roll_axis),cd = '%s.ballRoll' % attribute_control, driverValue = 0, value = 0, itt = 'spline', ott = 'spline')        
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.forward_roll_axis),cd = '%s.ballRoll' % attribute_control, driverValue = 10, value = 45, itt = 'spline', ott = 'spline')
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.forward_roll_axis),cd = '%s.ballRoll' % attribute_control, driverValue = -10, value = -45, itt = 'spline', ott = 'spline')
        #cmds.setDrivenKeyframe('%s.rotateX' % driver,cd = '%s.ballRoll' % attribute_control, driverValue = 20, value = 0, itt = 'spline', ott = 'spline')
        cmds.setInfinity('%s.rotate%s' % (driver, self.forward_roll_axis), postInfinite = 'linear')
        cmds.setInfinity('%s.rotate%s' % (driver, self.forward_roll_axis), preInfinite = 'linear')
        
        return control
    
    def _create_extra_roll(self, parent):

        control, xform, driver = self._create_pivot_control(self.extra_ball, 'extra')
        
        attr.disconnect_attribute('%sShape.visibility' % control)
        cmds.setAttr('%sShape.visibility' % control, 1)
        
        attr.connect_reverse('%s.ikFk' % self.roll_control.get(), '%sShape.visibility' % control)
        
        cmds.parent(xform, parent)
        
        attribute_control = self._get_attribute_control()
        
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.forward_roll_axis),cd = '%s.extraRoll' % attribute_control, driverValue = 0, value = 0, itt = 'spline', ott = 'spline')        
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.forward_roll_axis),cd = '%s.extraRoll' % attribute_control, driverValue = 10, value = 45, itt = 'spline', ott = 'spline')
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.forward_roll_axis),cd = '%s.extraRoll' % attribute_control, driverValue = -10, value = -45, itt = 'spline', ott = 'spline')
        #cmds.setDrivenKeyframe('%s.rotateX' % driver,cd = '%s.ballRoll' % attribute_control, driverValue = 20, value = 0, itt = 'spline', ott = 'spline')
        cmds.setInfinity('%s.rotate%s' % (driver, self.forward_roll_axis), postInfinite = 'linear')
        cmds.setInfinity('%s.rotate%s' % (driver, self.forward_roll_axis), preInfinite = 'linear')
        
        return control
    
    def _create_roll_control(self, transform):
        
        roll_control = self._create_control('roll') 
        roll_control.set_curve_type('square')
        
        self.roll_control = roll_control
        
        roll_control.scale_shape(.8,.8,.8)
        
        xform_group = space.create_xform_group(roll_control.get())
        
        roll_control.hide_scale_and_visibility_attributes()
        roll_control.hide_rotate_attributes()
        
        
        match = space.MatchSpace( transform, xform_group )
        match.translation_rotation()
        
        self.roll_control_xform = xform_group 
        
        return roll_control
    
    def _define_joints(self):
        
        #index_list = self.defined_joints
        
        #if not index_list:
        #    index_list = [0,1,2,3,4,5]
        
        self.ankle_index = 0
        self.heel_index = 1
        
        if self.extra_ball:
            self.extra_ball_index = 2
            self.ball_index = 3
            self.toe_index = 4
            self.yawIn_index = 5
            self.yawOut_index = 6
        
        if not self.extra_ball:
            self.ball_index = 2
            self.toe_index = 3
            self.yawIn_index = 4
            self.yawOut_index = 5
            
        self.ankle = self.ik_chain[self.ankle_index]
        self.heel = self.ik_chain[self.heel_index]
        
        if self.extra_ball:
            self.extra_ball = self.ik_chain[self.extra_ball_index]
            
        self.ball = self.ik_chain[self.ball_index]
        self.toe = self.ik_chain[self.toe_index]
        self.yawIn = self.ik_chain[self.yawIn_index]
        self.yawOut = self.ik_chain[self.yawOut_index]
    
    def _create_roll_attributes(self):
        
        attribute_control = self._get_attribute_control()
        
        attr.create_title(attribute_control, 'roll')
        
        cmds.addAttr(attribute_control, ln = 'ballRoll', at = 'double', k = True)
        
        if self.extra_ball:
            cmds.addAttr(attribute_control, ln = 'extraRoll', at = 'double', k = True)
            
        cmds.addAttr(attribute_control, ln = 'toeRoll', at = 'double', k = True)
        cmds.addAttr(attribute_control, ln = 'heelRoll', at = 'double', k = True)
        
        cmds.addAttr(attribute_control, ln = 'yawIn', at = 'double', k = True)
        cmds.addAttr(attribute_control, ln = 'yawOut', at = 'double', k = True)
        
        if self.add_bank:
            
            attr.create_title(attribute_control, 'bank')
            
            cmds.addAttr(attribute_control, ln = 'bankIn', at = 'double', k = True)
            cmds.addAttr(attribute_control, ln = 'bankOut', at = 'double', k = True)
        
            #cmds.addAttr(attribute_control, ln = 'bankForward', at = 'double', k = True)
            #cmds.addAttr(attribute_control, ln = 'bankBack', at = 'double', k = True)
    
    def _create_ik(self):
        if not self.extra_ball:
            self.ankle_handle = self._create_ik_handle( 'ankle', self.ankle, self.toe)
            cmds.parent( self.ankle_handle, self.setup_group )
                
        if self.extra_ball:
            self.ankle_handle = self._create_ik_handle( 'ankle', self.ankle, self.extra_ball)
            self.extra_handle = self._create_ik_handle( 'ball', self.extra_ball, self.ball)
            self.ball_handle = self._create_ik_handle( 'ball', self.ball, self.toe)
            
            cmds.parent(self.ankle_handle, self.setup_group)
            cmds.parent(self.extra_handle, self.setup_group)
            cmds.parent(self.ball_handle, self.setup_group)
        
    def _create_pivot_groups(self):

        #toe_control, toe_control_xform = self._create_toe_rotate_control()
        toe_fk_control, toe_fk_control_xform = self._create_toe_fk_rotate_control()

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
        
        next_roll = yawout_roll
        
        if not self.extra_ball:
            ball_roll = self._create_ball_roll(yawout_roll)
            next_roll = ball_roll
        
            
        if self.add_bank:
            
            bankin_roll = self._create_yawin_roll(next_roll, 'bankIn', scale = .5)
            bankout_roll = self._create_yawout_roll(bankin_roll, 'bankOut', scale = .5)
            #testing
            #bankforward_roll = self._create_toe_roll(bankout_roll, 'bankForward', scale = .5)
            #bankback_roll = self._create_heel_roll(bankforward_roll, 'bankBack', scale = .5)

            next_roll = bankout_roll
            
        if not self.add_bank:
            if not self.extra_ball:
                next_roll = yawout_roll

        if self.extra_ball:
            ball_roll = self._create_ball_roll(next_roll)
            extra_roll = self._create_extra_roll(ball_roll)
            
            cmds.parentConstraint(ball_roll, self.extra_handle, mo = True)
            cmds.parentConstraint(ball_roll, self.ball_handle, mo = True)
            cmds.parentConstraint(extra_roll, self.ankle_handle, mo = True)
        
        if not self.extra_ball:
            
            if not self.add_bank:
                cmds.parentConstraint(ball_roll, self.ankle_handle, mo = True)
            if self.add_bank:
                cmds.parentConstraint(bankout_roll, self.ankle_handle, mo = True)
        
        cmds.parentConstraint(ball_roll, self.roll_control_xform, mo = True)
            
        cmds.connectAttr('%s.%s' % (self.roll_control.get(), self.ik_attribute), '%s.visibility' % toe_fk_control_xform)
                    
    def set_add_bank(self, bool_value):
        self.add_bank = bool_value
             
    def set_extra_ball(self, joint_name):
        
        self.extra_ball = joint_name
                    
    def create(self):
        
        if self.extra_ball:
            self.joints.insert(2, self.extra_ball)
        
        super(rigs.FootRollRig,self).create()
        
        self._define_joints()
        
        self._create_roll_attributes()
        
        self._create_pivot_groups()

class IkSpineRig(rigs.BufferRig):
    
    def _create_surface(self):
        
        surface = geo.transforms_to_nurb_surface(self.joints, self.description, 2, 'Z', 1)
        self.surface = surface
        cmds.parent(surface, self.setup_group)
        
    def _create_clusters(self):

        cluster_surface = deform.ClusterSurface(self.surface, self.description)
        cluster_surface.create()
        
        self.clusters = cluster_surface.handles
        
        cluster_group = self._create_setup_group('clusters')
        
        cmds.parent(self.clusters, cluster_group)
    
    def _attach_to_surface(self):
        
        rivet_group = self._create_setup_group('rivets')
        
        for joint in self.buffer_joints:
            rivet = geo.attach_to_surface(joint, self.surface)
            cmds.parent(rivet, rivet_group)
    
    def _create_btm_control(self):
        
        btm_control = self._create_control('btm')
        btm_control.hide_scale_attributes()
        sub_control = self._create_control('btm', sub = True)
        sub_control.hide_scale_attributes()
        
        btm_control = btm_control.get()
        sub_control = sub_control.get()
        
        space.MatchSpace(self.clusters[0], btm_control).translation_to_rotate_pivot()
        space.create_xform_group(btm_control)
        
        space.create_follow_group(btm_control, self.clusters[0])
        
        space.MatchSpace(self.clusters[1], sub_control).translation_to_rotate_pivot()
        xform = space.create_xform_group(sub_control)
        
        space.create_follow_group(sub_control, self.clusters[1])
        cmds.parent(xform, btm_control)
        
        self.btm_control = btm_control

    def _create_top_control(self):
        
        top_control = self._create_control('top')
        top_control.hide_scale_attributes()
        sub_control = self._create_control('top', sub = True)
        sub_control.hide_scale_attributes()
        
        top_control = top_control.get()
        sub_control = sub_control.get()
        
        space.MatchSpace(self.clusters[-1], top_control).translation_to_rotate_pivot()
        space.create_xform_group(top_control)
        
        space.create_follow_group(top_control, self.clusters[-1])
        
        space.MatchSpace(self.clusters[-2], sub_control).translation_to_rotate_pivot()
        xform = space.create_xform_group(sub_control)
        
        space.create_follow_group(sub_control, self.clusters[-2])
        cmds.parent(xform, top_control)  
        
        self.top_control = top_control      
        
    def _create_mid_control(self):

        mid_control = self._create_control('mid', True)
        mid_control.hide_scale_attributes()
        
        mid_control = mid_control.get()
        
        space.MatchSpace(self.clusters[2], mid_control).translation_to_rotate_pivot()
        xform = space.create_xform_group(mid_control)
        
        space.create_follow_group(mid_control, self.clusters[2])
        
        space.create_multi_follow([self.top_control, self.btm_control], xform, mid_control, value = .5)
    
    def _create_controls(self):
        
        cluster_count = len(self.clusters)
        
        for inc in range(0, cluster_count):
            
            if inc == 0:
                self._create_top_control()
                
            if inc == cluster_count-1:
                self._create_btm_control()
        
        self._create_mid_control()
    
    def create(self):
        super(IkSpineRig, self).create()
        
        self._create_surface()
        self._create_clusters()
        self._attach_to_surface()

        self._create_controls()

#--- Misc

class BendyRig(rigs.Rig):
    
    def __init__(self, description, side):
        super(BendyRig, self).__init__(description, side)
        
        self.guide_enabled = True
        self.top_twist_enabled = True
        self.btm_twist_enabled = True
        
        self.top_control_as_locator = False
        self.btm_control_as_locator = False
        
        self.start_joint = None
        self.end_joint = None
        
        self.joint_count = 5
        self.tweak_joints = []
        
        self.up_object = None
        
    def _create_tweak_joints(self):
        
        if not self.tweak_joints:
            
            joints = space.subdivide_joint(self.start_joint, 
                                     self.end_joint, 
                                     self.joint_count - 2, 'joint', 
                                     '%s_1_%s' % (self.description,self.side), True)
            
            for joint in joints[:-1]:
                orient = space.OrientJoint(joint)
                
                if not self.up_object:
                    self.up_object = self.start_joint
                
                orient.set_aim_up_at_object(self.up_object)
                orient.run()
            
            cmds.makeIdentity(joints[-1], r = True, jo = True, apply = True)
            
            self.tweak_joints = joints
            
        #cmds.parent(self.tweak_joints, self.start_joint)
            
        cmds.parentConstraint(self.top_control, joints[0])
        cmds.parentConstraint(self.btm_control, joints[-1])
    
    def _create_guide(self):
        
        if not self.start_joint or not self.end_joint:
            return
        
        name = self._get_name()
    
        position_top = cmds.xform(self.start_joint, q = True, t = True, ws = True)
        position_btm = cmds.xform(self.end_joint, q = True, t = True, ws = True)
    
        cmds.select(cl = True)
        guide_top = cmds.joint( p = position_btm, n = self._get_name('twist', 'top') )
        cmds.select(cl = True)
        guide_btm = cmds.joint( p = position_top, n = self._get_name('twist', 'btm') )
        
        space.MatchSpace(self.start_joint, guide_top).rotation()
        
        cmds.makeIdentity(guide_top, r = True, apply = True)
        
        cmds.parent(guide_btm, guide_top)
        
        cmds.makeIdentity(guide_btm, r = True, jo = True, apply = True)
        
        handle = space.IkHandle(name)
        handle.set_solver(handle.solver_sc)
        handle.set_start_joint(guide_top)
        handle.set_end_joint(guide_btm)
        
        handle = handle.create()
        
        cmds.parent(guide_top, self.setup_group)
        space.create_follow_group(self.start_joint, guide_top)
        
        control_guide = self._create_control_group('guide')
        
        cmds.parent(self.top_control_xform, control_guide)
        cmds.parent(self.mid_xforms, control_guide)
        
        space.create_follow_group(guide_top, control_guide)
        cmds.parent(handle, self.btm_control)
    
    def _create_controls(self):
        
        self.main_control_group = self._create_control_group('main')
        
        self._create_top_control()
        self._create_btm_control()
        
        space.create_follow_group(self.start_joint, self.main_control_group)
    
    def _create_top_control(self):
        
        control = None
        
        if not self.top_control_as_locator:
            control = self._create_control()
            control = control.get()
            
        if self.top_control_as_locator:
            locator = cmds.spaceLocator(n = self._get_name('locator'))[0]
            control = locator
            
        space.MatchSpace(self.start_joint, control).translation_rotation()
        xform = space.create_xform_group(control)
        
        cmds.parent(xform, self.main_control_group )
        
        self.top_control = control
        self.top_control_xform = xform
    
    def _create_btm_control(self):
        
        control = None
        
        if not self.btm_control_as_locator:
            control = self._create_control()
            control = control.get()
            
        if self.btm_control_as_locator:
            locator = cmds.spaceLocator(n = self._get_name('locator'))[0]
            control = locator
            
        space.MatchSpace(self.end_joint, control).translation_rotation()
        xform = space.create_xform_group(control)
        
        cmds.parent(xform, self.main_control_group )
        
        self.btm_control = control   
        self.btm_control_xform = xform
         
    def _create_mid_controls(self):
        
        self._create_sparse_mid_controls()
    
    def _create_sparse_mid_controls(self):
        
        self.mid_xforms = []
        self.mid_controls = []
        
        for joint in self.tweak_joints[1:-1]:
            control = self._create_control()
            control = control.get()
            
            space.MatchSpace(joint, control).translation_rotation()
            xform = space.create_xform_group(control)
            
            cmds.parent(xform, self.main_control_group)
            
            cmds.parentConstraint(control, joint)
            
            self.mid_xforms.append(xform)
            self.mid_controls.append(control)
            
    def _create_top_twist(self):
        pass
    
    def _create_btm_twist(self):
        pass
    
    def set_create_guide(self, bool_value):
        self.guide_enabled = bool_value
        
    def set_create_top_twist(self, bool_value):
        self.top_twist_enabled = bool_value
        
    def set_create_btm_twist(self, bool_value):
        self.btm_twist_enabled = bool_value
        
    def set_top_control_as_locator(self, bool_value):
        self.top_control_as_locator = bool_value
        
    def set_btm_control_as_locator(self, bool_value):
        self.btm_control_as_locator = bool_value
        
    def set_joint_count(self, value):
        self.joint_count = value
        
    def set_tweak_joints(self, list_of_joints):
        self.tweak_joints = list_of_joints
        
    def set_start_joint(self, joint_name):
        self.start_joint = joint_name
        
    def set_end_joint(self, joint_name):
        self.end_joint = joint_name
        
    def create(self):
        
        self._create_controls()
        
        self._create_tweak_joints()
        
        self._create_mid_controls()
        
        if self.guide_enabled:
            self._create_guide()
    
        
    
    
class BendyChainRig(rigs.Rig):
    pass

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
            
            normal_vector = geo.get_vertex_normal(vert)

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
        
        skin = deform.find_deformer_by_type(self.mesh, 'skinCluster')
        
        joints = self.joints
        
        if not skin:
            skin = cmds.skinCluster(self.mesh, self.joints[0], tsb = True)[0]
            joints = joints[1:]
        
        if self.zero_weights:
            deform.set_skin_weights_to_zero(skin)
        
        for joint in joints:
            cmds.skinCluster(skin, e = True, ai = joint, wt = 0.0)
            
        return skin
        
    def _weight_verts(self, skin):
        
        vert_count = len(self.verts)
        
        progress = core.ProgressBar('weighting %s:' % self.mesh, vert_count)
        
        for inc in range(0, vert_count):
            
            
            joint_weights = self._get_vert_weight(inc)

            if joint_weights:
                cmds.skinPercent(skin, self.verts[inc], r = False, transformValue = joint_weights)
            
            progress.inc()
            progress.status('weighting %s: vert %s' % (self.mesh, inc))
            
            
            
            if progress.break_signaled():
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
        
        skin = deform.find_deformer_by_type(self.mesh, 'skinCluster')
        
        joints = self.joints
        
        if not skin:
            skin = cmds.skinCluster(self.mesh, self.joints[0], tsb = True)[0]
            joints = joints[1:]
        
        if self.zero_weights:
            deform.set_skin_weights_to_zero(skin)
        
        for joint in joints:
            cmds.skinCluster(skin, e = True, ai = joint, wt = 0.0)
            
        return skin
        
    def _weight_verts(self, skin):
        
        vert_count = len(self.verts)
        
        progress = core.ProgressBar('weighting %s:' % self.mesh, vert_count)
        
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
    
    slice_group = cmds.group(em = True, n = core.inc_name('group_slice_%s' % description))
    
    section = radius/float( (sections/2) )
    
    offset = section/2.0
    
    angle_section = 90/((sections/2)+1)
    angle_offset = angle_section
    
    joints = []
    
    for inc in range(0, (sections/2)):
        
        group_pos = cmds.group(em = True, n = core.inc_name('group_slice%s_%s' % (inc+1, description)))
        group_neg = cmds.group(em = True, n = core.inc_name('group_slice%s_%s' % (inc+1, description)))
        cmds.parent(group_pos, group_neg, slice_group)
        
        dup_pos = cmds.duplicate(center_joint, n = core.inc_name('joint_guide%s_%s' % (inc+1, description)))[0]
        
        dup_neg = cmds.duplicate(center_joint, n = core.inc_name('joint_guide%s_%s' % (inc+1, description)))[0]
        
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
            dup2 = cmds.duplicate(dup, n = core.inc_name('joint_guideEnd%s_%s' % (inc+1, description)))[0]
            
            cmds.move(edge_vector[0],edge_vector[1],edge_vector[2], dup2, os = True, r = True)
            
            cmds.parent(dup2, dup)
            
            angle_offset = angle_section
            
            value = 1.0/((sections/2)+1)
            value_offset = 1.0-value
            
            for inc in range(0, (sections/2)+1):
                dup3 = cmds.duplicate(dup, n = core.inc_name('joint_angle%s_%s' % (inc+1, description)))[0]
                
                rels = cmds.listRelatives(dup3, f = True)
                
                cmds.rename(rels[0], core.inc_name('joint_angleEnd%s_%s' % (inc+1, description)))
                
                cmds.rotate(angle_offset, 0, 0, dup3)
                angle_offset += angle_section
                
                cmds.makeIdentity(dup3, r = True, apply = True)
                
                multiply = attr.connect_multiply( '%s.rotate%s' % (dup, axis), '%s.rotate%s' % (dup3, axis), value_offset)
                
                cmds.connectAttr('%s.rotateY' % dup, '%s.input1Y' % multiply)
                cmds.connectAttr('%s.outputY' % multiply, '%s.rotateY' % dup3)
                cmds.setAttr('%s.input2Y' % multiply, value_offset)
                value_offset-=value
                
    return joints, slice_group

def rig_joint_helix(joints, description, top_parent, btm_parent):
    
    setup = cmds.group(em = True, n = core.inc_name('setup_%s' % description))
    
    handle = space.IkHandle(description)
    handle.set_solver(handle.solver_spline)
    handle.set_start_joint(joints[0])
    handle.set_end_joint(joints[-1])
    handle.create()
    
    cmds.parent(handle.ik_handle, handle.curve, setup)
    
    ffd, lattice, base = deform.create_lattice(handle.curve, description, [2,2,2])
    
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
    
    group = cmds.group(em = True, n = core.inc_name('joints_%s_1_%s' % (description, side)) )
    
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
        
    param = geo.get_parameter_from_curve_length(curve, length)
    position = geo.get_point_from_curve_parameter(curve, param)
    
    cmds.select(cl = True)
    joint = cmds.joint(p = position, n = core.inc_name( 'joint_%s_1' % (description) ) )
    
    if side == None:
        side = space.get_side(position, 0.1)
    
    joint = cmds.rename(joint, core.inc_name(joint + '_%s' % side))
    
    return joint

def create_mouth_muscle(top_transform, btm_transform, description, joint_count = 3, guide_prefix = 'guide', offset = 1):
    
    cmds.select(cl = True) 
    top_joint = cmds.joint(n = core.inc_name('guide_%s' % top_transform))
    cmds.select(cl = True)
    btm_joint = cmds.joint(n = core.inc_name('guide_%s' % btm_transform))
    
    space.MatchSpace(top_transform, top_joint).translation_rotation()
    space.MatchSpace(btm_transform, btm_joint).translation_rotation()
    
    aim = cmds.aimConstraint(btm_joint, top_joint)[0]
    cmds.delete(aim)
    
    cmds.makeIdentity(top_joint, r = True, apply = True)
    cmds.parent(btm_joint, top_joint)
    cmds.makeIdentity(btm_joint, jo = True, apply = True)

    sub_joints = space.subdivide_joint(top_joint, btm_joint, name = description, count = joint_count)

    ik = space.IkHandle('top_lip')
    ik.set_start_joint( top_joint )
    ik.set_end_joint( btm_joint )
    ik.set_solver(ik.solver_rp)
    ik.create()
    
    cmds.parent(top_joint, top_transform)
    cmds.parent(ik.ik_handle, top_transform)
    cmds.pointConstraint(btm_transform, ik.ik_handle)
    
    
    locator1,locator2 = rigs_util.create_distance_scale( top_joint, btm_joint, offset = offset)
    
    for joint in sub_joints:
        cmds.connectAttr('%s.scaleX' % top_joint, '%s.scaleX' % joint)
        cmds.connectAttr('%s.scaleY' % top_joint, '%s.scaleY' % joint)
        cmds.connectAttr('%s.scaleZ' % top_joint, '%s.scaleZ' % joint)
    
        cmds.hide(locator1, locator2)
    
    cmds.parent(locator1, top_transform)
    cmds.parent(locator2, btm_transform)
    
    return sub_joints, ik.ik_handle 

