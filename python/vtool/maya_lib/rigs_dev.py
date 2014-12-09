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
        
        if not self.follicle_group:
            self.follicle_group = cmds.group(em = True, n = self._get_name('groupFollicle'))
            cmds.parent(self.follicle_group, self.top_group)
            
            cmds.setAttr('%s.inheritsTransform' % self.follicle_group, 0)
        
        follicle = util.create_surface_follicle(self.surface, self._get_name(), [u_value, v_value] )
        cmds.select(cl = True)
        joint = cmds.joint( n = util.inc_name( self._get_name('joint') ) )
        util.MatchSpace(follicle, joint).translation()
        
        cmds.parent(joint, follicle)
        cmds.makeIdentity(joint, jo = True, apply = True)
        
        locator_top = False
        locator_btm = False
        
        if locator:
            locator_top = cmds.spaceLocator(n = util.inc_name(self._get_name('locatorFollicle')))[0]
            cmds.setAttr('%s.localScaleX' % locator_top, .1)
            cmds.setAttr('%s.localScaleY' % locator_top, .1)
            cmds.setAttr('%s.localScaleZ' % locator_top, .1)
        
            util.MatchSpace(self.sub_locator_group, locator_top).translation()
            cmds.parent(locator_top, self.sub_locator_group)
            cmds.makeIdentity(locator_top, t = True, apply = True)  
            
            locator_btm = cmds.spaceLocator(n = util.inc_name(self._get_name('locatorBtmFollicle')))[0]
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
            if inc == 2:
                sub = True
            
            group = cmds.group(em = True, n = util.inc_name(self._get_name('group', 'local')))
            cmds.parent(group, self.setup_group)
            
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
                cmds.parent(xform_local, group)
                #cmds.pointConstraint(control.get(), cluster)
                
                cmds.parent(xform, self.control_group)
                
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
                
                pos = cmds.xform(locators1[inc+1], q = True, ws = True, t = True)
                
                if pos[0] < -0.1 or pos[0] > 0.1:
                    print locators1[inc], locators1[inc+1]
                    aim = cmds.aimConstraint(locators1[inc+1], locators1[inc])[0]
                    cmds.setAttr('%s.worldUpType' % aim, 4)
                    
                    if inc != 0:
                        cmds.setAttr('%s.worldUpType' % aim, 2)
                        cmds.connectAttr('%s.worldMatrix' % locators1[inc-1], '%s.worldUpMatrix' % aim)
                
                pos = cmds.xform(locators2[inc+1], q = True, ws = True, t = True)
                
                if pos[0] < -0.1 or pos[0] > 0.1:
                    print locators2[inc], locators2[inc+1]
                    aim = cmds.aimConstraint(locators2[inc+1], locators2[inc])[0]
                    cmds.setAttr('%s.worldUpType' % aim, 4)
                    
                    if inc != 0:
                        cmds.setAttr('%s.worldUpType' % aim, 2)
                        cmds.connectAttr('%s.worldMatrix' % locators2[inc-1], '%s.worldUpMatrix' % aim)
                    
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
    
    
            locator1,locator2 = util.create_distance_scale( joints1[inc], joints2[inc] )
    
            child = cmds.listRelatives(joints1[inc], type = 'joint')[0]
            child2 = cmds.listRelatives(child, type = 'joint')[0]
            child3 = cmds.listRelatives(child2, type = 'joint')[0]
    
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
            
            loc1 = cmds.spaceLocator(n = 'locator_%s' % joints1[inc])[0]
            sub_loc1 = cmds.spaceLocator(n = 'locatorSub_%s' % joints1[inc])[0]
            cmds.setAttr('%s.localScaleX' % loc1, .1)
            cmds.setAttr('%s.localScaleY' % loc1, .1)
            cmds.setAttr('%s.localScaleZ' % loc1, .1)
            cmds.setAttr('%s.localScaleX' % sub_loc1, .1)
            cmds.setAttr('%s.localScaleY' % sub_loc1, .1)
            cmds.setAttr('%s.localScaleZ' % sub_loc1, .1)
            
            util.MatchSpace( joints1[inc] , loc1 ).translation_rotation()
            util.MatchSpace( joints1[inc] , sub_loc1 ).translation_rotation()
    
            loc2 = cmds.spaceLocator(n = 'locator_%s' % joints2[inc])[0]
            sub_loc2 = cmds.spaceLocator(n = 'locatorSub_%s' % joints2[inc])[0]
            cmds.setAttr('%s.localScaleX' % loc2, .1)
            cmds.setAttr('%s.localScaleY' % loc2, .1)
            cmds.setAttr('%s.localScaleZ' % loc2, .1)
            cmds.setAttr('%s.localScaleX' % sub_loc2, .1)
            cmds.setAttr('%s.localScaleY' % sub_loc2, .1)
            cmds.setAttr('%s.localScaleZ' % sub_loc2, .1)
    
            util.MatchSpace( joints2[inc] , loc2 ).translation_rotation()    
            util.MatchSpace( joints2[inc] , sub_loc2 ).translation_rotation()
            
            #cmds.parentConstraint(loc1, joints1[inc], mo = True)
            #cmds.orientConstraint(loc2, joints2[inc], mo = True)
    
            locators1.append(loc1)
            locators2.append(loc2)
            
            self.sub_locators1.append(sub_loc1)
            self.sub_locators2.append(sub_loc2)
            
            cmds.parent(sub_loc1, loc1)
            cmds.parent(sub_loc2, loc2)
    
        cmds.parent(locators1, locator1_gr)
        cmds.parent(locators2, locator2_gr)
    
        return locators1, locators2
    
    def _create_joints_from_locators(self, locators):
        
        joints = []
        
        for locator in locators:
            cmds.select(cl = True)
            joint = cmds.joint(n = util.inc_name(self._get_name('joint', 'temp')))
            
            const = cmds.parentConstraint(locator, joint)
            cmds.delete(const)
            
            joints.append(joint)
            
        return joints
            
        
    
    def _create_joints(self, curve1, curve2, count = 11):
    
        joints_gr = cmds.group(em = True, n = util.inc_name(self._get_name('group', 'joints')))
        cmds.parent(joints_gr, self.setup_group)
    
        if self.lip_curve and self.muzzel_curve:
    
            muzzle_joints = util.create_oriented_joints_on_curve( curve1, count, self._get_name('muzzle'))
            lip_joints = util.create_oriented_joints_on_curve( curve2, count, self._get_name('lip'))
            
            cmds.parent(muzzle_joints, w = True)
            cmds.parent(lip_joints, w = True)
            
        if self.lip_locators and self.muzzle_locators:
            
            muzzle_joints = self._create_joints_from_locators(self.muzzle_locators)
            lip_joints = self._create_joints_from_locators(self.lip_locators)
 
        new_muzzle_joints = []
        new_lip_joints = []
    
        for inc in range(0, len(muzzle_joints)):
            
            joints = []    
            
            muzzle_joint = muzzle_joints[inc]
            
            joints.append(muzzle_joint)
    
            pos = cmds.xform(muzzle_joints[inc], q = True, t = True, ws = True)
            if pos[0] > -0.01 and pos[0] < 0.1:
                cmds.setAttr('%s.jointOrientX' % muzzle_joint, -90)
                cmds.setAttr('%s.jointOrientZ' % muzzle_joint, -90)
    
            
            aim = cmds.aimConstraint(lip_joints[inc], muzzle_joints[inc])[0]
            # there is a cycle, create a temporary group at  lip_joints[inc] instead of using lip_joints[inc]
            cmds.setAttr('%s.worldUpType' % aim, 4)
            
            if inc > 0:
                cmds.setAttr('%s.worldUpType' % aim, 2)
                cmds.connectAttr('%s.worldMatrix' % new_muzzle_joints[-1], '%s.worldUpMatrix' % aim)
                
            #cmds.delete(aim)
            #cmds.makeIdentity(muzzle_joints[inc], r = True, apply = True)
            
            end_joint = cmds.duplicate(lip_joints[inc], n = util.inc_name( 'joint_%s' % self._get_name('sub') ))[0]
            cmds.parent(end_joint, muzzle_joint)
            cmds.makeIdentity(end_joint, jo = True, apply = True)
            cmds.parent(lip_joints[inc], end_joint)
    
            sub_joints = util.subdivide_joint(muzzle_joint, end_joint, name = self._get_name('sub'), count = 2)
            
            pos = cmds.xform(lip_joints[inc], q = True, t = True, ws = True)
            if pos[0] > -0.01 and pos[0] < 0.1:
            #    cmds.setAttr('%s.jointOrientX' % lip_joints[inc], 90)
                cmds.setAttr('%s.jointOrientY' % lip_joints[inc], 90)
            #    cmds.setAttr('%s.jointOrientZ' % lip_joints[inc], 180)
                    
            joints += sub_joints
            
            joints.append(end_joint)
            
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
        
        
        
        return muzzle_joints, lip_joints
    
    def _create_ik(self, joints1, joints2 ):
    
        ik_gr = cmds.group(em = True, n = util.inc_name(self._get_name('group', 'ik')))
        cmds.parent(ik_gr, self.setup_group)
    
        ik_handles = []
    
        for inc in range(0, len(joints1)):
            
            ik = util.IkHandle('top_lip')
            ik.set_start_joint( joints1[inc] )
            
            parent_joint = cmds.listRelatives(joints2[inc], p = True)[0]
            
            ik.set_end_joint( parent_joint )
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
        
        for cluster in clusters:
            
            
            control = self._create_control()
            
            control.hide_scale_and_visibility_attributes()
            
            control.rotate_shape(90, 0, 0)
            control.scale_shape(.1, .1, .1)                
            

                
            xform = util.create_xform_group(control.get())
            
            if not self.lip_curve:
                util.MatchSpace(cluster, xform).translation()
            if self.lip_curve:
                util.MatchSpace(cluster, xform).translation_to_rotate_pivot()

            if self.respect_side:
                side = control.color_respect_side(center_tolerance = 0.1)
            
            if side != 'C':
                control_name = cmds.rename(control.get(), util.inc_name(control.get()[0:-1] + side))
                control = util.Control(control_name)            
            
            local, xform_local = util.constrain_local(control.get(), cluster, constraint = 'pointConstraint')
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
        
        muzzle_joints, lip_joints = self._create_joints( self.muzzel_curve , self.lip_curve, 11) 
        
        ik_handles = self._create_ik( muzzle_joints, lip_joints)
        
        locators1, locators2 = self._create_locators( muzzle_joints, lip_joints)
        """
        self._attach_ik(locators1, locators2, ik_handles, self.lip_curve)
        
        distance_locators = self._attach_scale( muzzle_joints, lip_joints, locators1, locators2)
        
        if len(lip_joints) > 1:
            print 'adding aims$$$$$$$$$$$$$$$$$$$$$$$$'
            self._aim_locators(locators1, locators2)
        
        if self.lip_curve:
            self._create_controls()
        if not self.lip_curve:
            self._create_controls(locators2)
        
        self._attach_joints_to_locators(self.sub_locators1, muzzle_joints)
        
        
        self._attach_joints_to_locators(self.sub_locators2, lip_joints)
        
        self._create_locator_controls(self.sub_locators2)
        """
        
                
                
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