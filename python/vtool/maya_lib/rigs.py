# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

import string

import util
import vtool.util

import maya.cmds as cmds

#--- Base

class Rig(object):
    
    side_left = 'L'
    side_right = 'R'
    side_center = 'C'
    
    def __init__(self, description, side):
        
        cmds.refresh()
        
        self.description = description
        self.side = side
        
        self.control_parent = 'controls'
        self.setup_parent = 'setup'
        
        self._create_default_groups()
        
        self.control_shape = 'circle'
        self.sub_control_shape = None
        
        self.control_color = None
        self.sub_control_color = None
        
        self.control_size = 1
        self.sub_control_size = 0.8
        
        self.controls = []
        self.sub_controls = []
        self.control_dict = {}
    
    def _create_group(self,  prefix = None, description = None):
        
        rig_group_name = self._get_name(prefix, description)
        
        group = cmds.group(em = True, n = util.inc_name(rig_group_name))
        
        return group
        
    def _create_default_groups(self):
                        
        self.control_group = self._create_group('controls')
        self.setup_group = self._create_group('setup')
        
        cmds.hide(self.setup_group)
        
        self._parent_default_groups()
        
    def _parent_default_groups(self):
        
        self._parent_custom_default_group(self.control_group, self.control_parent)
        self._parent_custom_default_group(self.setup_group, self.setup_parent)
                
    def _parent_custom_default_group(self, group, custom_parent):
        
        if not cmds.objExists(group) or not cmds.objExists(custom_parent):
            return
            
        parent = cmds.listRelatives(group, p = True)
        
        if parent:
            parent = parent[0]
            
        if not parent:
            return
            
        if parent != custom_parent:
            cmds.parent(group, custom_parent)
        
    def _create_setup_group(self, description):
        
        group = self._create_group('setup', description)
        
        if self.setup_group:
            cmds.parent(group, self.setup_group)
        
        return group
        
    def _create_control_group(self, description):
        
        group = self._create_group('controls', description)
        
        if self.control_group:
            cmds.parent(group, self.control_group)
            
        return group
            
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
        
        control = util.Control( self._get_control_name(description, sub) )
        
        control.color( util.get_color_of_side( self.side , sub)  )
        
        if self.control_color >=0 and not sub:
            control.color( self.control_color )
            
        if self.sub_control_color >= 0 and sub:
            control.color( self.control_color )
            
        control.hide_visibility_attribute()
        
        if self.control_shape:
            
            control.set_curve_type(self.control_shape)
            
            if sub:
                control.set_curve_type(self.sub_control_shape)
            
        
        if not sub:
                        
            control.scale_shape(self.control_size, 
                                self.control_size, 
                                self.control_size)
        if sub:
            
            control.scale_shape(self.sub_control_size, 
                                self.sub_control_size, 
                                self.sub_control_size)
        
        if not sub:
            self.controls.append(control.get())
        
        if sub:
            self.sub_controls.append(control.get())
        
        
        self.control_dict[control.get()] = {}
        
        return control
            
    def set_control_shape(self, shape_name):
        self.control_shape = shape_name
        
    def set_sub_control_shape(self, shape_name):
        self.sub_control_shape = shape_name
    
    def set_control_color(self, color):
        self.control_color = color
        
    def set_sub_control_color(self, color):
        self.sub_control_color = color
        
    def set_control_size(self, float_value):
        self.control_size = float_value
        
    def set_sub_control_size(self, float_value):
        self.sub_control_size = float_value
        
    
                
    def set_control_parent(self, parent_transform):
        
        self.control_parent = parent_transform
        
        self._parent_custom_default_group(self.control_group, self.control_parent)
        
    def set_setup_parent(self, parent_transform):
        
        self.setup_parent = parent_transform
        
        self._parent_custom_default_group(self.setup_group, self.setup_parent)
        
    def get_control_entries(self, title):
        
        entries = []
        
        for control in self.controls:
            if self.control_dict[control].has_key(title):
                entries.append(self.control_dict[control][title])
        
        return entries
        
    def get_sub_control_entries(self, title):
        
        entries = []
        
        for control in self.sub_controls:
            if self.control_dict[control].has_key(title):
                entries.append(self.control_dict[control][title])
        
        return entries
        
    def create(self):
        
        self._parent_default_groups()
        
class JointRig(Rig):
    
    def __init__(self, description, side):
        super(JointRig, self).__init__(description, side)
        
        self.joints = []
        
        self.attach_joints = True
        
    def _attach_joints(self, source_chain, target_chain):
        
        if not self.attach_joints:
            return
        
        util.AttachJoints(source_chain, target_chain).create()
    
    def _check_joints(self, joints):
        
        for joint in joints:
            if cmds.nodeType(joint) == 'joint':
                continue
            
            if cmds.nodeType(joint) == 'transform':
                continue
            
            vtool.util.show('%s is not a joint or transform. %s may not build properly.' % (joint, self.__class__.__name__))
        
    
    def set_joints(self, joints):
        
        if type(joints) != list:
            self.joints = [joints]
            
            self._check_joints(self.joints)
            
            return
        
        self.joints = joints
        
        self._check_joints(self.joints)

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
            
class CurveRig(Rig):
    def __init__(self, description, side):
        super(CurveRig, self).__init__(description, side)
        
        self.curves = None
    
    def set_curve(self, curve_list):
        
        self.curves = vtool.util.convert_to_sequence(curve_list)

#--- Rigs

class SparseRig(JointRig):
    
    def __init__(self, description, side):
        super(SparseRig, self).__init__(description, side)
        
        self.control_shape = 'cube'
        self.is_scalable = False
        self.respect_side = False
        self.respect_side_tolerance = 0.001
        self.match_scale = False
        
    def set_scalable(self, bool_value):
        self.is_scalable = bool_value
        
    def set_respect_side(self, bool_value, tolerance = 0.001):
        self.respect_side = bool_value
        self.respect_side_tolerance = tolerance
    
    def set_match_scale(self, bool_value):
        self.match_scale = bool_value
        
    def create(self):
        
        super(SparseRig, self).create()
        
        for joint in self.joints:
            
            control = self._create_control()
        
            control_name = control.get()
        
            match = util.MatchSpace(joint, control_name)
            match.translation_rotation()
            
            if self.respect_side:
                side = control.color_respect_side(True, self.respect_side_tolerance)
            
                if side != 'C':
                    old_control_name = control_name
                    
                    control_data = self.control_dict[control_name]
                    self.control_dict.pop(control_name)
                    
                    control_name = cmds.rename(control_name, util.inc_name(control_name[0:-1] + side))
                    
                    control = util.Control(control_name)
                    
                    self.control_dict[control_name] = control_data
                    
                    
                    
              
            xform = util.create_xform_group(control.get())
            
            if self.match_scale:
                const = cmds.scaleConstraint(joint, xform)
                cmds.delete(const)
            
            driver = util.create_xform_group(control.get(), 'driver')
            
            cmds.parentConstraint(control_name, joint)

            if self.is_scalable:
                scale_constraint = cmds.scaleConstraint(control.get(), joint)[0]
                util.scale_constraint_to_local(scale_constraint)
            if not self.is_scalable:
                control.hide_scale_attributes()
            
            cmds.parent(xform, self.control_group)
            
            self.control_dict[control_name]['xform'] = xform
            self.control_dict[control_name]['driver'] = driver
            
    

class SparseLocalRig(SparseRig):

    def __init__(self, description, side):
        super(SparseLocalRig, self).__init__(description, side)
        
        self.local_constraint = True
        self.control_to_pivot = False
        self.local_parent = None
        self.local_xform = None

    def set_local_constraint(self, bool_value):
        self.local_constraint = bool_value

    def set_control_to_pivot(self, bool_value):
        self.control_to_pivot = bool_value

    def set_local_parent(self, local_parent):
        self.local_parent = local_parent

    def create(self):
        
        super(SparseRig, self).create()
        
        if self.local_parent:
            self.local_xform = cmds.group(em = True, n = 'localParent_%s' % self._get_name())
            cmds.parent(self.local_xform, self.setup_group)
        
        for joint in self.joints:
            
            control = self._create_control()
            
            control_name = control.get()
            
            if not self.control_to_pivot:
                match = util.MatchSpace(joint, control_name)
                match.translation_rotation()
            if self.control_to_pivot:    
                util.MatchSpace(joint, control_name).translation_to_rotate_pivot()
            
            if self.respect_side:
                side = control.color_respect_side(True, self.respect_side_tolerance)
            
                if side != 'C':
                    
                    control_data = self.control_dict[control_name]
                    self.control_dict.pop(control_name)
                    
                    control_name = cmds.rename(control_name, util.inc_name(control_name[0:-1] + side))
                    
                    self.control_dict[control_name] = control_data
                    
                    control = util.Control(control_name)
            
            xform = util.create_xform_group(control.get())
            driver = util.create_xform_group(control.get(), 'driver')
            
            if not self.local_constraint:
                xform_joint = util.create_xform_group(joint)
                
                if self.local_parent:
                    cmds.parent(xform_joint, self.local_xform)
                
                util.connect_translate(control.get(), joint)
                util.connect_rotate(control.get(), joint)
                
                util.connect_translate(driver, joint)
                util.connect_rotate(driver, joint)
            
            if self.local_constraint:
                local_group, local_xform = util.constrain_local(control.get(), joint)
                
                if self.local_xform:
                    cmds.parent(local_xform, self.local_xform)
                
                local_driver = util.create_xform_group(local_group, 'driver')
                
                util.connect_translate(driver, local_driver)
                util.connect_rotate(driver, local_driver)
                util.connect_scale(driver, local_driver)
                
                if not self.local_xform:
                    cmds.parent(local_xform, self.setup_group)
                
            util.connect_scale(control.get(), joint)
            
            cmds.parent(xform, self.control_group)
            
        if self.local_parent:
            util.create_follow_group(self.local_parent, self.local_xform)
            
        self.control_dict[control_name]['xform'] = xform
        self.control_dict[control_name]['driver'] = driver
            
class ControlRig(Rig):
    
    def __init__(self, name, side):
        super(ControlRig, self).__init__(name,side)
        
        
        
        self.transforms = None
        self.control_count = 1
        self.control_shape_types = {}
        self.control_descriptions = {}
    
    def set_transforms(self, transforms):
        self.transforms = transforms
        
    def set_control_count_per_transform(self, int_value):
        self.control_count = int_value
    
    def set_control_shape(self, index, shape_name):
        self.control_shape_types[index] = shape_name
    
    def set_control_description(self, index, description):
        self.control_descriptions[index] = description
    
    def create(self):
        
        for transform in self.transforms:
            for inc in range(0, self.control_count):
                
                description = None
                if inc in self.control_descriptions:
                    description = self.control_descriptions[inc]
                
                control = self._create_control(description)
                
                
                util.MatchSpace(transform, control.get()).translation_rotation()
                
                if inc in self.control_shape_types:
                    control.set_curve_type(self.control_shape_types[inc])
                
                xform = util.create_xform_group(control.get())    
                cmds.parent(xform, self.control_group)                
                
class GroundRig(JointRig):
    
    def __init__(self, name, side):
        super(GroundRig, self).__init__(name, side)
        
        self.control_shape = 'square_point'
    
    def create(self):
        super(GroundRig, self).create()
        
        scale = 1
        last_control = None
        
        controls = []
        
        first_control = None
        
        for inc in range(0, 3):
            
            
            if inc == 0:
                control = self._create_control()
                
                control.set_curve_type(self.control_shape)
                
                cmds.parent(control.get(), self.control_group)
                
                first_control = control.get()
                
            if inc > 0:
                control = self._create_control(sub =  True)
                control.set_curve_type(self.control_shape)
                
                util.connect_visibility('%s.subVisibility' % first_control, '%sShape' % control.get(), 1)
                
                
            controls.append(control.get())
                
            control.scale_shape(40*scale, 40*scale, 40*scale)
            
            if last_control:
                cmds.parent(control.get(), last_control)
            
            last_control = control.get()
            scale*=.9
            
            control.hide_scale_and_visibility_attributes()
        
        if self.joints and self.description != 'ground':
            xform = util.create_xform_group(controls[0])
            util.MatchSpace(self.joints[0], xform).translation_rotation()
        
        if self.joints:   
            cmds.parentConstraint(control.get(), self.joints[0])
        
    def set_joints(self, joints = None):
        super(GroundRig, self).set_joints(joints)

#--- FK

class FkRig(BufferRig):
    #CBB
    
    def __init__(self, name, side):
        super(FkRig, self).__init__(name, side)
        self.last_control = ''
        self.control = ''
        
        self.current_xform_group = ''
        self.control_size = 3
        
        self.transform_list = []
        self.drivers = []
        self.current_increment = None
        
        self.use_joints = False
        
        self.parent = None
        
        self.connect_to_driver = None
        self.match_to_rotation = True
        
        self.create_sub_controls = False

    def _create_control(self, sub = False):
        
        self.last_control = self.control
        
        self.control = super(FkRig, self)._create_control(sub = sub)
        
        self.control.hide_scale_attributes()
        
        if self.use_joints:
            self.control.set_to_joint()
        
        xform = util.create_xform_group(self.control.get())
        driver = util.create_xform_group(self.control.get(), 'driver')
        
        self.current_xform_group = xform
        self.control_dict[self.control.get()]['xform'] = self.current_xform_group
        self.control_dict[self.control.get()]['driver'] = driver
        
        self.drivers.append(driver)
        #self.control = self.control.get()

        if self.create_sub_controls and not sub:
            
            subs = []
            
            for inc in range(0,2):

                if inc == 0:
                    sub_control = super(FkRig, self)._create_control(sub =  True)
                    sub_control.set_curve_type(self.control_shape)
                    if self.sub_control_shape:
                        sub_control.set_curve_type(self.sub_control_shape)    
                    sub_control.scale_shape(2,2,2)
                if inc == 1:
                    sub_control = super(FkRig, self)._create_control(description = 'sub', sub =  True)
                    sub_control.set_curve_type(self.control_shape)
                    if self.sub_control_shape:
                        sub_control.set_curve_type(self.sub_control_shape)
                
                sub_control.hide_translate_attributes()
                sub_control.hide_scale_and_visibility_attributes()
                
                util.MatchSpace(self.control.get(), sub_control.get()).translation_rotation()
                
                util.connect_visibility('%s.subVisibility' % self.control.get(), '%sShape' % sub_control.get(), 1)
                
                subs.append(sub_control.get())
                
                if inc == 0:
                    cmds.parent(sub_control.get(), self.control.get())
                if inc == 1:
                    
                    cmds.parent(sub_control.get(), self.sub_controls[-2])
                
            self.control_dict[self.control.get()]['subs'] = subs
                
        return self.control
    
    def _edit_at_increment(self, control, transform_list):
        self.transform_list = transform_list
        current_transform = transform_list[self.current_increment]
        
        self._all_increments(control, current_transform)
        
        if self.current_increment == 0:
            self._first_increment(control, current_transform)

        if self.current_increment == ((len(transform_list))-1):
            self._last_increment(control, current_transform)
                    
        if self.current_increment > 0:
            self._increment_greater_than_zero(control, current_transform)
   
        if self.current_increment < (len(transform_list)):
            self._increment_less_than_last(control, current_transform)
            
        if self.current_increment < (len(transform_list)) and self.current_increment > 0:
            self._incrment_after_start_before_end(control, current_transform)
            
        if self.current_increment == (len(transform_list)-1) or self.current_increment == 0:
            self._increment_equal_to_start_end(control,current_transform)
    
    
    def _all_increments(self, control, current_transform):
        
                
        xform = self.control_dict[control]['xform']
        
        match = util.MatchSpace(current_transform, self.control_dict[control]['xform'])
        
        if self.match_to_rotation:
            match.translation_rotation()
            
        if not self.match_to_rotation:
            match.translation()
        
    def _first_increment(self, control, current_transform):
        
        cmds.parent(self.control_dict[control]['xform'], self.control_group)
        self._attach(control, current_transform)
    
    def _last_increment(self, control, current_transform):
        return
    
    def _increment_greater_than_zero(self, control, current_transform):
        
        self._attach(control, current_transform)
        
        if not self.create_sub_controls:
            cmds.parent(self.control_dict[control]['xform'], self.last_control.get())
            
        if self.create_sub_controls:
            
            last_control = self.control_dict[self.last_control.get()]['subs'][-1]
            
            cmds.parent(self.control_dict[control]['xform'], last_control)
            
    def _increment_less_than_last(self, control, current_transform):
        return
    
    def _increment_equal_to_start_end(self, control, current_transform):
        return
    
    def _incrment_after_start_before_end(self, control, current_transform):
        return
    
    def _loop(self, transforms):
        inc = 0
        
        for inc in range(0, len(transforms)):
            
            self.current_increment = inc
            
            control = self._create_control()
            
            control = control.get()
            
            self._edit_at_increment(control, transforms)

            inc += 1
    
    def _attach(self, source_transform, target_transform):
        
        if not self.create_sub_controls:
            cmds.parentConstraint(source_transform, target_transform, mo = True)
            
        if self.create_sub_controls:
            source_transform = self.control_dict[source_transform]['subs'][-1]
            cmds.parentConstraint(source_transform, target_transform, mo = True)        

    def set_parent(self, parent):
        #CBB this needs to be replaced with self.set_control_parent
        
        self.parent = parent
        
    def set_match_to_rotation(self, bool_value):
        self.match_to_rotation = bool_value
    
    def get_drivers(self):
        
        drivers = self.get_control_entries('driver')
            
        return drivers
    
    def set_use_joints(self, bool_value):
        
        self.use_joints = bool_value
    
    def set_create_sub_controls(self, bool_value):
        
        self.create_sub_controls = bool_value
    
    def create(self):
        super(FkRig, self).create()
        
        self._loop(self.buffer_joints)
        
        if self.parent:
            cmds.parent(self.control_group, self.parent)

class FkLocalRig(FkRig):
    
    def __init__(self, name, side):
        super(FkLocalRig, self).__init__(name, side)
        
        self.local_parent = None
        self.main_local_parent = None
        self.local_xform = None
        self.rig_scale = False
        
    def _attach(self, source_transform, target_transform):
        
        local_group, local_xform = util.constrain_local(source_transform, target_transform, scale_connect = self.rig_scale)
        
        if not self.local_parent:
            self.local_xform = local_xform
            cmds.parent(local_xform, self.setup_group)
        
        if self.local_parent:
            follow = util.create_follow_group(self.local_parent, local_xform)
            cmds.parent(follow, self.control_group)
        
        self.local_parent = local_group
            
        return local_group, local_xform

    def _create_control(self, sub = False):
        
        self.last_control = self.control
        
        self.control = super(FkLocalRig, self)._create_control(sub = sub)
        
        if self.rig_scale:
            
            self.control.show_scale_attributes()
        
        if self.rig_scale:
            self.control.hide_visibility_attribute()
        
        
        return self.control

    def set_control_scale(self, bool_value):
        self.rig_scale = bool_value
        
    def set_scalable(self, bool_value):
        self.rig_scale = bool_value

    def set_local_parent(self, local_parent):
        self.main_local_parent = local_parent 
    
    def create(self):
        super(FkLocalRig, self).create()
        
        if self.main_local_parent:
            util.create_follow_group(self.main_local_parent, self.local_xform)
            
class FkScaleRig(FkRig): 
    #CBB 
      
    def __init__(self, name, side): 
        super(FkScaleRig, self).__init__(name, side) 
        self.last_control = '' 
        self.control = '' 
        self.controls = [] 
        self.current_xform_group = '' 
          
    def _create_control(self, sub = False): 
        control = super(FkScaleRig, self)._create_control(sub) 
  
        control.show_scale_attributes() 
        cmds.setAttr( '%s.overrideEnabled' % control.get() , 1 ) 
          
          
        return self.control
          
    def _edit_at_increment(self, control, transform_list): 
        self.transform_list = transform_list 
        current_transform = transform_list[self.current_increment] 
          
        self._all_increments(control, current_transform) 
          
        if self.current_increment == 0: 
            self._first_increment(control, current_transform) 
  
        if self.current_increment == ((len(transform_list))-1): 
            self._last_increment(control, current_transform) 
                      
        if self.current_increment > 0: 
            self._increment_greater_than_zero(control, current_transform) 
     
        if self.current_increment < (len(transform_list)): 
            self._increment_less_than_last(control, current_transform) 
              
        if self.current_increment < (len(transform_list)) and self.current_increment > 0: 
            self._incrment_after_start_before_end(control, current_transform) 
              
        if self.current_increment == (len(transform_list)-1) or self.current_increment == 0: 
            self._increment_equal_to_start_end(control,current_transform) 
          
    def _first_increment(self, control, current_transform): 
        super(FkScaleRig, self)._first_increment(control, current_transform) 
          
        util.connect_scale(control, current_transform) 
      
    def _increment_greater_than_zero(self, control, current_transform): 

        cmds.select(cl = True) 
          
        name = self._get_name('jointFk') 
          
        buffer_joint = cmds.joint(n = util.inc_name( name ) ) 
          
        cmds.setAttr('%s.overrideEnabled' % buffer_joint, 1) 
        cmds.setAttr('%s.overrideDisplayType' % buffer_joint, 1) 
          
        cmds.setAttr('%s.radius' % buffer_joint, 0) 
          
        if not self.create_sub_controls:
            cmds.connectAttr('%s.scale' % self.last_control.get(), '%s.inverseScale' % buffer_joint)

        
        match = util.MatchSpace(control, buffer_joint) 
        match.translation_rotation() 
          
        cmds.makeIdentity(buffer_joint, apply = True, r = True) 
        
        if vtool.util.get_maya_version() >= 2015:  
            cmds.parentConstraint(control, current_transform)
        
        if vtool.util.get_maya_version() <= 2014:
            cmds.pointConstraint(control, current_transform) 
            util.connect_rotate(control, current_transform) 
           
        #drivers = self.get_control_entries('driver2')
        
        driver = self.control_dict[control]['driver']
        
        drivers = [driver]
        if self.control_dict[control].has_key('driver2'):
            driver2 = self.control_dict[control]['driver2']
            drivers.append(driver2)
        
        if vtool.util.get_maya_version() <= 2014:
            for transform in drivers:
                util.connect_rotate(transform, current_transform)
        
        util.connect_scale(control, current_transform) 
          
        cmds.parent(self.current_xform_group, buffer_joint) 
          
        if not self.create_sub_controls:
            cmds.parent(buffer_joint, self.last_control.get())
        if self.create_sub_controls: 
            last_control = self.control_dict[self.last_control.get()]['subs'][-1]
            cmds.parent(buffer_joint, last_control)
            
class FkCurlNoScaleRig(FkRig):
    def __init__(self, description, side):
        super(FkCurlNoScaleRig, self).__init__(description, side)
        
        self.attribute_control = None
        self.attribute_name =None
        self.curl_axis = 'Z'
        self.skip_increments = []
        
        
    def _create_control(self, sub = False):
        
        control = super(FkCurlNoScaleRig, self)._create_control(sub)
        
        if self.curl_axis == None:
            
            return self.control
        
        if not self.attribute_control:
            self.attribute_control = control.get()
            
        if not cmds.objExists('%s.CURL' % self.attribute_control):
            title = util.MayaEnumVariable('CURL')
            title.create(self.attribute_control)
        
        driver = util.create_xform_group(control.get(), 'driver2')
        self.control_dict[control.get()]['driver2'] = driver
        
        other_driver = self.drivers[-1]
        self.drivers[-1] = [other_driver, driver]
        
        if self.curl_axis != 'All':
            self._attach_curl_axis(driver)
            
        if self.curl_axis == 'All':
            all_axis = ['x','y','z']
            
            for axis in all_axis:
                self._attach_curl_axis(driver, axis)
                
        return self.control
    
    def _attach_curl_axis(self, driver, axis = None):

        if self.current_increment in self.skip_increments:
            return


        if not self.attribute_name:
            description = self.description
        if self.attribute_name:
            description = self.attribute_name

        if axis == None:
            var_name = '%sCurl' % description
        if axis:
            var_name = '%sCurl%s' % (description, axis.capitalize())
            
        if not axis:
            curl_axis = self.curl_axis
        if axis:
            curl_axis = axis.capitalize()
            
        curl_variable = util.MayaNumberVariable(var_name)
        curl_variable.set_variable_type(curl_variable.TYPE_DOUBLE)
        curl_variable.create(self.attribute_control)
        
        curl_variable.connect_out('%s.rotate%s' % (driver, curl_axis))
        
        if self.current_increment and self.create_buffer_joints:
            
            current_transform = self.transform_list[self.current_increment]
            util.connect_rotate(driver, current_transform)
    
    def set_curl_axis(self, axis_letter):
        self.curl_axis = axis_letter.capitalize()
    
    def set_attribute_control(self, control_name):
        self.attribute_control = control_name
        
    def set_attribute_name(self, attribute_name):
        self.attribute_name = attribute_name
        
    def set_skip_increments(self, increments):
        self.skip_increments = increments
        
class FkCurlRig(FkScaleRig):
    
    def __init__(self, description, side):
        super(FkCurlRig, self).__init__(description, side)
        
        self.attribute_control = None
        self.curl_axis = 'Z'
        self.curl_description = self.description
        self.skip_increments = []
        
    def _create_control(self, sub = False):
        control = super(FkCurlRig, self)._create_control(sub)
        
        if not self.attribute_control:
            self.attribute_control = control.get()
            
        util.create_title(self.attribute_control, 'CURL')
        
        driver = util.create_xform_group(control.get(), 'driver2')
        self.control_dict[control.get()]['driver2'] = driver
        
        other_driver = self.drivers[-1]
        self.drivers[-1] = [other_driver, driver]
        
        if self.curl_axis != 'All':
            self._attach_curl_axis(driver)
            
        if self.curl_axis == 'All':
            all_axis = ['x','y','z']
            
            for axis in all_axis:
                self._attach_curl_axis(driver, axis)
                
        return self.control
    
    def _attach_curl_axis(self, driver, axis = None):
        
        if self.current_increment in self.skip_increments:
            return
        
        if axis == None:
            var_name = '%sCurl' % self.curl_description
        if axis:
            var_name = '%sCurl%s' % (self.curl_description, axis.capitalize())
            
        if not axis:
            curl_axis = self.curl_axis
        if axis:
            curl_axis = axis.capitalize()
            
        curl_variable = util.MayaNumberVariable(var_name)
        curl_variable.set_variable_type(curl_variable.TYPE_DOUBLE)
        curl_variable.create(self.attribute_control)
        
        curl_variable.connect_out('%s.rotate%s' % (driver, curl_axis))
        
    def set_curl_axis(self, axis_letter):
        self.curl_axis = axis_letter.capitalize()
    
    def set_curl_description(self, description):
        self.curl_description = description
        
    def set_skip_increments(self, increments):
        
        self.skip_increments = increments
    
    def set_attribute_control(self, control_name):
        self.attribute_control = control_name
    
class SimpleFkCurveRig(FkCurlNoScaleRig):
    def __init__(self, name, side):
        super(SimpleFkCurveRig, self).__init__(name, side)
        self.controls = []
        self.orient_controls_to_joints = False
        self.sub_controls = []
        self.sub_control_on = True
        self.sub_drivers = []
        self.stretchy = True
        self.control_count = 3
        self.advanced_twist = True
        self.stretch_on_off = False
        self.orig_curve = None
        self.curve = None
        self.ik_curve = None
        self.span_count = self.control_count
        self.wire_hires = False
        self.curl_axis = None
        self.orient_joint = None
        self.control_xform = {}
        self.last_pivot_top_value = False
        self.fix_x_axis = False
        self.skip_first_control = False
        self.ribbon = False
        self.ribbon_offset = 1
        self.ribbon_offset_axis = 'Y'
        self.create_follows = True
        self.closest_y = False
        self.stretch_axis = 'X'

    def _create_curve(self):
        
        if not self.curve:
        
            name = self._get_name()
            
            self.orig_curve = util.transforms_to_curve(self.buffer_joints, self.span_count, name)
            self.curve = cmds.duplicate(self.orig_curve)[0]
            
            cmds.rebuildCurve(self.curve, 
                              spans = self.control_count - 1 ,
                              rpo = True,  
                              rt = 0, 
                              end = 1, 
                              kr = False, 
                              kcp = False, 
                              kep = True,  
                              kt = False,
                              d = 3)
            
            name = self.orig_curve
            self.orig_curve = cmds.rename(self.orig_curve, util.inc_name('orig_curve'))
            self.curve = cmds.rename(self.curve, name)
            
            cmds.parent(self.curve, self.setup_group)
            cmds.parent(self.orig_curve, self.setup_group)
    
    def _create_clusters(self):
        
        name = self._get_name()
        
        if self.last_pivot_top_value:
            last_pivot_end = True
            
        if not self.last_pivot_top_value:
            last_pivot_end = False
        
        cluster_group = cmds.group(em = True, n = util.inc_name('clusters_%s' % name))
        
        self.clusters = util.cluster_curve(self.curve, name, True, last_pivot_end = last_pivot_end)
        
        cmds.parent(self.clusters, cluster_group)
        cmds.parent(cluster_group, self.setup_group)
    
    """
    def _create_control(self, sub = False):
        

        control = super(SimpleFkCurveRig, self)._create_control(sub = sub)
        
        return control
    """
    
    def _create_sub_control(self):
            
        sub_control = util.Control( self._get_control_name(sub = True) )
        sub_control.color( util.get_color_of_side( self.side , True)  )
        
        if self.control_shape:
            
            sub_control.set_curve_type(self.control_shape)
        
        sub_control.scale_shape(self.control_size * .9, 
                                self.control_size * .9,
                                self.control_size * .9)
        
        return sub_control

    def _first_increment(self, control, current_transform):
        
        self.first_control = control

        if self.skip_first_control:
            control = util.Control(control)
            control.delete_shapes()
            self.controls[-1].rename(self.first_control.replace('CNT_', 'ctrl_'))
            self.first_control = self.controls[-1]

        if self.sub_controls:
            self.top_sub_control = self.sub_controls[0]
            
            if self.skip_first_control:
                control = util.Control(self.sub_controls[0])
                control.delete_shapes()
                self.top_sub_control = cmds.rename(self.top_sub_control, self.top_sub_control.replace('CNT_', 'ctrl_'))
                self.sub_controls[0] = self.top_sub_control
    
    def _increment_greater_than_zero(self, control, current_transform):
        
        cmds.parent(self.current_xform_group, self.controls[-2])    

    def _last_increment(self, control, current_transform):
        
        if self.create_follows:
            
            util.create_follow_fade(self.controls[-1], self.sub_drivers[:-1])
            util.create_follow_fade(self.sub_controls[-1], self.sub_drivers[:-1])
            util.create_follow_fade(self.sub_controls[0], self.sub_drivers[1:])
            util.create_follow_fade(self.sub_drivers[0], self.sub_drivers[1:])
        
        top_driver = self.drivers[-1]
        
        if self.create_follows:
            if not type(top_driver) == list:
                util.create_follow_fade(self.drivers[-1], self.sub_drivers[:-1])

    def _all_increments(self, control, current_transform):
        
        match = util.MatchSpace(self.clusters[self.current_increment], self.current_xform_group)
        match.translation_to_rotate_pivot()
        
        if self.orient_controls_to_joints:
            
            if not self.orient_joint:
                joint = self._get_closest_joint()
            if self.orient_joint:
                joint = self.orient_joint
                
            match = util.MatchSpace(joint, self.current_xform_group)
            match.rotation()
        
        if self.sub_control_on:
            
            sub_control = self._create_sub_control()
            sub_control_object = sub_control
            sub_control = sub_control.get()
        
            match = util.MatchSpace(control, sub_control)
            match.translation_rotation()
        
            xform_sub_control = util.create_xform_group(sub_control)
            self.sub_drivers.append( util.create_xform_group(sub_control, 'driver') )
            
            cmds.parentConstraint(sub_control, self.clusters[self.current_increment], mo = True)
            
            cmds.parent(xform_sub_control, self.control.get())
            
            self.sub_controls.append(sub_control)
            
            sub_vis = util.MayaNumberVariable('subVisibility')
            sub_vis.set_variable_type(sub_vis.TYPE_BOOL)
            sub_vis.create(control)
            sub_vis.connect_out('%sShape.visibility' % sub_control)
                
            sub_control_object.hide_scale_and_visibility_attributes()
            
        if not self.sub_control_on:
            cmds.parentConstraint(control, self.clusters[self.current_increment], mo = True)
        
        increment = self.current_increment+1
        
        if increment in self.control_xform:
            vector = self.control_xform[increment]
            cmds.move(vector[0], vector[1],vector[2], self.current_xform_group, r = True)
        
        cmds.parent(self.current_xform_group, self.control_group)
        
    def _get_closest_joint(self):
        
        current_cluster = self.clusters[self.current_increment]
        
        return util.get_closest_transform(current_cluster, self.buffer_joints)            
    
    def _setup_stretchy(self):
        if not self.attach_joints:
            return
        
        if self.stretchy:    
            util.create_spline_ik_stretch(self.ik_curve, self.buffer_joints[:-1], self.controls[-1], self.stretch_on_off, self.stretch_axis)
    
    def _loop(self, transforms):
                
        self._create_curve()
        self._create_clusters()
        
        super(SimpleFkCurveRig, self)._loop(self.clusters)

    def _create_ik_curve(self, curve):
        
        if self.span_count == self.control_count:
            self.ik_curve = curve
            return 
        
        if self.wire_hires:
            
            self.ik_curve = cmds.duplicate(self.orig_curve)[0]
            cmds.setAttr('%s.inheritsTransform' % self.ik_curve, 1)
            self.ik_curve = cmds.rename(self.ik_curve, 'ik_%s' % curve)
            cmds.rebuildCurve(self.ik_curve, 
                              ch = False, 
                              spans = self.span_count,
                              rpo = True,  
                              rt = 0, 
                              end = 1, 
                              kr = False, 
                              kcp = False, 
                              kep = True,  
                              kt = False,
                              d = 3)
            
            wire, base_curve = cmds.wire( self.ik_curve, 
                                          w = curve, 
                                          dds=[(0, 1000000)], 
                                          gw = False, 
                                          n = 'wire_%s' % self.curve)
            
            cmds.setAttr('%sBaseWire.inheritsTransform' % base_curve, 1)
            
            return
            
        if not self.wire_hires:
          
            cmds.rebuildCurve(curve, 
                              ch = True, 
                              spans = self.span_count,
                              rpo = True,  
                              rt = 0, 
                              end = 1, 
                              kr = False, 
                              kcp = False, 
                              kep = True,  
                              kt = False,
                              d = 3)
            
            self.ik_curve = curve
            return

    def _create_ribbon(self):
        pass
        
    def _create_spline_ik(self):
        
        self._create_ik_curve(self.curve)
        
        if self.buffer_joints:
            joints = self.buffer_joints
        if not self.buffer_joints:
            joints = self.joints
            

        if self.fix_x_axis:
            duplicate_hierarchy = util.DuplicateHierarchy( joints[0] )
        
            duplicate_hierarchy.stop_at(self.joints[-1])
            
            prefix = 'joint'
            if self.create_buffer_joints:
                prefix = 'buffer'
            
            duplicate_hierarchy.replace(prefix, 'xFix')
            x_joints = duplicate_hierarchy.create()
            cmds.parent(x_joints[0], self.setup_group)
            
            #working here to add auto fix to joint orientation.
            
            for inc in range(0, len(x_joints)):
                #util.OrientJointAttributes(x_joints[inc])
                
                orient = util.OrientJointAttributes(x_joints[inc])
                orient.delete()
                #orient._create_attributes()
                         
                orient = util.OrientJoint(x_joints[inc])
                
                aim = 3
                if inc == len(x_joints)-1:
                    aim = 5
                orient.set_aim_at(aim)
                
                aim_up = 0
                if inc > 0:
                    aim_up = 1
                orient.set_aim_up_at(aim_up)
                
                orient.run()
            
            self._attach_joints(x_joints, joints)
            
            joints = x_joints
            self.buffer_joints = x_joints
            
        children = cmds.listRelatives(joints[-1])
        
        if children:
            cmds.parent(children, w = True)
        
        handle = util.IkHandle(self._get_name())
        handle.set_solver(handle.solver_spline)
        handle.set_start_joint(joints[0])
        handle.set_end_joint(joints[-1])
        handle.set_curve(self.ik_curve)
        handle = handle.create()

        if self.closest_y:
            cmds.setAttr('%s.dWorldUpAxis' % handle, 2)
        
        if children:
            cmds.parent(children, joints[-1])
            
        cmds.parent(handle, self.setup_group)
        
        if self.advanced_twist:
            start_locator = cmds.spaceLocator(n = self._get_name('locatorTwistStart'))[0]
            end_locator = cmds.spaceLocator(n = self._get_name('locatorTwistEnd'))[0]
            
            self.start_locator = start_locator
            self.end_locator = end_locator
            
            cmds.hide(start_locator, end_locator)
            
            match = util.MatchSpace(self.buffer_joints[0], start_locator)
            match.translation_rotation()
            
            match = util.MatchSpace(self.buffer_joints[-1], end_locator)
            match.translation_rotation()
                        
            cmds.setAttr('%s.dTwistControlEnable' % handle, 1)
            cmds.setAttr('%s.dWorldUpType' % handle, 4)
            cmds.connectAttr('%s.worldMatrix' % start_locator, '%s.dWorldUpMatrix' % handle)
            cmds.connectAttr('%s.worldMatrix' % end_locator, '%s.dWorldUpMatrixEnd' % handle)
            
            if hasattr(self, 'top_sub_control'):
                cmds.parent(start_locator, self.sub_controls[0])
                
            if not hasattr(self, 'top_sub_control'):
                cmds.parent(start_locator, self.sub_controls[0])
                
            cmds.parent(end_locator, self.sub_controls[-1])
            
        if not self.advanced_twist and self.buffer_joints != self.joints:
            
            follow = util.create_follow_group(self.controls[0], self.buffer_joints[0])
            cmds.parent(follow, self.setup_group)
            
        if not self.advanced_twist:
            var = util.MayaNumberVariable('twist')
            var.set_variable_type(var.TYPE_DOUBLE)
            var.create(self.controls[0])
            var.connect_out('%s.twist' % handle)
    
    def set_control_xform(self, vector, inc):
        self.control_xform[inc] = vector
    
    def set_orient_joint(self, joint):
        self.orient_joint = joint
    
    def set_orient_controls_to_joints(self, bool_value):
        self.orient_controls_to_joints = bool_value
    
    def set_advanced_twist(self, bool_value):
        self.advanced_twist = bool_value
    
    def set_control_count(self, int_value, span_count = None, wire_hires = False):
        if int_value == 0 or int_value < 2:
            int_value = 2
            
        self.control_count = int_value
        
        if not span_count:
            self.span_count = self.control_count
            
        if span_count:
            self.span_count = span_count
            self.wire_hires = wire_hires
            
    
    def set_sub_control(self, bool_value):
        
        self.sub_control_on = bool_value
    
    def set_stretchy(self, bool_value):
        self.stretchy = bool_value
        
    def set_stretch_on_off(self, bool_value):
        self.stretch_on_off = bool_value
    
    def set_stretch_axis(self, axis_letter):
        self.stretch_axis = axis_letter
    
    def set_curve(self, curve):
        self.curve = curve
        
    def set_ribbon(self, bool_value):
        self.ribbon = bool_value
        
    def set_ribbon_offset(self, float_value):
        
        self.ribbon_offset = float_value
        
    def set_ribbon_offset_axis(self, axis_letter):
        self.ribbon_offset_axis = axis_letter
        
    def set_last_pivot_top(self, bool_value):
        self.last_pivot_top_value = bool_value
    
    def set_fix_x_axis(self, bool_value):
        self.fix_x_axis = bool_value

    def set_skip_first_control(self, bool_value):
        self.skip_first_control = bool_value
        
    def set_closest_y(self, bool_value):
        self.closest_y = bool_value
        
    def set_create_follows(self, bool_value):
        self.create_follows = bool_value
        
    def create(self):
        super(SimpleFkCurveRig, self).create()
        
        if not self.ribbon:
            self._create_spline_ik()
            self._setup_stretchy()
            
        if self.ribbon:
            surface = util.transforms_to_nurb_surface(self.buffer_joints, self._get_name(), spans = self.control_count-1, offset_amount = self.ribbon_offset, offset_axis = self.ribbon_offset_axis)
            
            cmds.setAttr('%s.inheritsTransform' % surface, 0)
            
            cluster_surface = util.ClusterSurface(surface, self._get_name())
            cluster_surface.set_join_ends(True)
            cluster_surface.create()
            handles = cluster_surface.handles
            
            self.ribbon_clusters = handles
            
            for inc in range(0, len(handles)):
                cmds.parentConstraint(self.sub_controls[inc], handles[inc], mo = True)
                
            cmds.parent(surface, self.setup_group)
            cmds.parent(handles, self.setup_group)
            
            if self.attach_joints:
                for joint in self.buffer_joints:
                    rivet = util.attach_to_surface(joint, surface)
                    cmds.setAttr('%s.inheritsTransform' % rivet, 0)
                    cmds.parent(rivet, self.setup_group)
        
        cmds.delete(self.orig_curve) 
    
class FkCurveRig(SimpleFkCurveRig):
    
    def __init__(self, name, side):
        super(FkCurveRig, self).__init__(name, side)
        
        self.aim_end_vectors = False
        
    def _create_aims(self, clusters):
        
        control1 = self.sub_controls[0]
        control2 = self.sub_controls[-1]
        
        cluster1 = clusters[0]
        cluster2 = clusters[-1]
        
        cmds.delete( cmds.listRelatives(cluster1, ad = True, type = 'constraint') )
        cmds.delete( cmds.listRelatives(cluster2, ad = True, type = 'constraint') )
        
        aim1 = cmds.group(em = True, n = util.inc_name('aimCluster_%s_1' % self._get_name()))
        aim2 = cmds.group(em = True, n = util.inc_name('aimCluster_%s_2' % self._get_name()))
        
        xform_aim1 = util.create_xform_group(aim1)
        xform_aim2 = util.create_xform_group(aim2)
        
        util.MatchSpace(control1, xform_aim1).translation()
        util.MatchSpace(control2, xform_aim2).translation()
        
        cmds.parentConstraint(control1, xform_aim1,  mo = True)
        cmds.parentConstraint(control2, xform_aim2,  mo = True)
        
        mid_control_id = len(self.sub_controls)/2
        
        cmds.aimConstraint(self.sub_controls[mid_control_id], aim1, wuo = self.controls[0], wut = 'objectrotation')
        cmds.aimConstraint(self.sub_controls[mid_control_id], aim2, wuo = self.controls[-1], wut = 'objectrotation')

        cmds.parent(cluster1, aim1)
        cmds.parent(cluster2, aim2)
        
        cmds.parent(xform_aim1, xform_aim2, self.setup_group)
    
    def set_aim_end_vectors(self, bool_value):
        self.aim_end_vectors = bool_value
        
    def create(self):
        super(FkCurveRig, self).create()
        
        if self.aim_end_vectors:    
            if not self.ribbon:
                self._create_aims(self.clusters)
            if self.ribbon:
                self._create_aims(self.ribbon_clusters)

class FkCurveLocalRig(FkCurveRig):
    
    def __init__(self, description, side):
        super(FkCurveLocalRig, self).__init__(description, side)
        
        self.last_local_group = None
        self.last_local_xform = None
        self.local_parent = None     
        self.sub_local_controls = []
        
    def _all_increments(self, control, current_transform):
        
        match = util.MatchSpace(self.clusters[self.current_increment], self.current_xform_group)
        match.translation_to_rotate_pivot()
        
        if self.orient_controls_to_joints:
            
            closest_joint = self._get_closest_joint()
            
            match = util.MatchSpace(closest_joint, self.current_xform_group)
            match.rotation()
        
        if self.sub_control_on:
            
            sub_control = util.Control( self._get_control_name(sub = True) )
        
            sub_control.color( util.get_color_of_side( self.side , True)  )
            
            if self.control_shape:
                sub_control.set_curve_type(self.control_shape)
            
            sub_control_object = sub_control
            sub_control = sub_control.get()
            
            match = util.MatchSpace(control, sub_control)
            match.translation_rotation()
        
            xform_sub_control = util.create_xform_group(sub_control)
            self.sub_drivers.append( util.create_xform_group(sub_control, 'driver') )
            
            local_group, local_xform = util.constrain_local(sub_control, self.clusters[self.current_increment])
            
            self.sub_local_controls.append( local_group )
            
            cmds.parent(local_xform, self.setup_group)
            
            control_local_group, control_local_xform = util.constrain_local(control, local_xform)
            
            if self.control_dict[self.control.get()].has_key('driver2'):
                control_driver = self.control_dict[self.control.get()]['driver2']
            
                driver = util.create_xform_group( control_local_group, 'driver')
                util.connect_rotate(control_driver, driver)
            
            
            cmds.parent(control_local_xform, self.setup_group)
            
            
            if self.last_local_group:
                cmds.parent(control_local_xform, self.last_local_group)
            
            self.last_local_group = control_local_group
            self.last_local_xform = control_local_xform
            
            cmds.parent(xform_sub_control, self.control.get())
            self.sub_controls.append(sub_control)
            
            sub_vis = util.MayaNumberVariable('subVisibility')
            sub_vis.set_variable_type(sub_vis.TYPE_BOOL)
            sub_vis.create(control)
            sub_vis.connect_out('%sShape.visibility' % sub_control)
            
            sub_control_object.hide_scale_and_visibility_attributes()
            
        if not self.sub_control_on:
            
            util.constrain_local(control, self.clusters[self.current_increment])
        
        cmds.parent(self.current_xform_group, self.control_group)
        
    def _first_increment(self, control, current_transform):
        super(FkCurveLocalRig, self)._first_increment(control, current_transform)
        
        if self.local_parent:
            cmds.parent(self.last_local_xform, self.local_parent)
    
    def _create_spline_ik(self):
        
        self._create_ik_curve(self.curve)
        
        children = cmds.listRelatives(self.buffer_joints[-1], c = True)
        
        if children:
            cmds.parent(children, w = True)
        
        handle = util.IkHandle(self._get_name())
        handle.set_solver(handle.solver_spline)
        handle.set_curve(self.curve)
        handle.set_start_joint(self.buffer_joints[0])
        handle.set_end_joint(self.buffer_joints[-1])
        handle = handle.create()
        
        """
        handle = cmds.ikHandle( sol = 'ikSplineSolver', 
                       ccv = False, 
                       pcv = False , 
                       sj = self.buffer_joints[0], 
                       ee = self.buffer_joints[-1], 
                       c = self.curve)[0]
        """
        if children:
            cmds.parent(children, self.buffer_joints[-1])
            
        cmds.parent(handle, self.setup_group)
        
        if self.advanced_twist:
            
            start_locator = cmds.spaceLocator(n = self._get_name('locatorTwistStart'))[0]
            end_locator = cmds.spaceLocator(n = self._get_name('locatorTwistEnd'))[0]
            
            self.start_locator = start_locator
            self.end_locator = end_locator
            
            cmds.hide(start_locator, end_locator)
            
            match = util.MatchSpace(self.buffer_joints[0], start_locator)
            match.translation_rotation()
            
            match = util.MatchSpace(self.buffer_joints[-1], end_locator)
            match.translation_rotation()
            
            
            cmds.setAttr('%s.dTwistControlEnable' % handle, 1)
            cmds.setAttr('%s.dWorldUpType' % handle, 4)
            cmds.connectAttr('%s.worldMatrix' % start_locator, '%s.dWorldUpMatrix' % handle)
            cmds.connectAttr('%s.worldMatrix' % end_locator, '%s.dWorldUpMatrixEnd' % handle)
            
            if hasattr(self, 'top_sub_control'):
                cmds.parent(start_locator, self.sub_local_controls[0])
                
            if not hasattr(self, 'top_sub_control'):
                cmds.parent(start_locator, self.sub_local_controls[0])
                
            
            cmds.parent(end_locator, self.sub_local_controls[-1])
            
        if not self.advanced_twist:
            
            util.create_local_follow_group(self.controls[0], self.buffer_joints[0])
            #util.constrain_local(self.controls[0], self.buffer_joints[0])
            
    def set_local_parent(self, parent):
        self.local_parent = parent

    def create(self):
        super(SimpleFkCurveRig, self).create()
        
        if not self.ribbon:
            self._create_spline_ik()
            self._setup_stretchy()
            
        if self.ribbon:
            surface = util.transforms_to_nurb_surface(self.buffer_joints, self._get_name(), spans = self.control_count-1, offset_amount = self.ribbon_offset, offset_axis = self.ribbon_offset_axis)
            
            cmds.setAttr('%s.inheritsTransform' % surface, 0)
            
            cluster_surface = util.ClusterSurface(surface, self._get_name())
            cluster_surface.set_join_ends(True)
            cluster_surface.create()
            handles = cluster_surface.handles
            
            self.ribbon_clusters = handles
            
            for inc in range(0, len(handles)):
                
                cmds.parentConstraint(self.sub_local_controls[inc], handles[inc], mo = True)
                #cmds.parent(handles[inc], self.sub_local_controls[inc])
            
            cmds.parent(surface, self.setup_group)
            cmds.parent(handles, self.setup_group)
            
            for joint in self.buffer_joints:
                rivet = util.attach_to_surface(joint, surface)
                cmds.setAttr('%s.inheritsTransform' % rivet, 0)
                cmds.parent(rivet, self.setup_group)
        
        cmds.delete(self.orig_curve) 

#---IK

class IkSplineNubRig(BufferRig):
    
    def __init__(self, description, side):
        
        super(IkSplineNubRig, self).__init__(description, side)
        
        self.end_with_locator = False
        self.top_guide = None
        self.btm_guide = None
        
        self.bool_create_middle_control = True
        
        self.right_side_fix = True
        self.right_side_fix_axis = 'x'
        
        self.control_shape = 'pin'
        
        self.control_orient = None
        
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

    def _create_twist_group(self, top_control, top_handle, top_guide):
        
        name = self._get_name()
        
        twist_guide_group = cmds.group(em = True, n = util.inc_name('guideSetup_%s' % name))
        cmds.hide(twist_guide_group)
        
        cmds.parent([top_guide, top_handle], twist_guide_group)
        
        cmds.parent(twist_guide_group, self.setup_group)
        
        cmds.parentConstraint(top_control, twist_guide_group,mo = True)
        
        self.end_locator = True
        
    def _create_joint_line(self):
    
        name = self._get_name()
    
        position_top = cmds.xform(self.buffer_joints[0], q = True, t = True, ws = True)
        position_btm = cmds.xform(self.buffer_joints[-1], q = True, t = True, ws = True)
    
        cmds.select(cl = True)
        guide_top = cmds.joint( p = position_top, n = util.inc_name('topTwist_%s' % name) )
        
        cmds.select(cl = True)
        guide_btm = cmds.joint( p = position_btm, n = util.inc_name('btmTwist_%s' % name) )
        
        util.MatchSpace(self.buffer_joints[0], guide_top).rotation()
        
        cmds.makeIdentity(guide_top, r = True, apply = True)
        
        cmds.parent(guide_btm, guide_top)
        
        cmds.makeIdentity(guide_btm, r = True, jo = True, apply = True)
        
        handle = util.IkHandle(name)
        handle.set_solver(handle.solver_sc)
        handle.set_start_joint(guide_top)
        handle.set_end_joint(guide_btm)
        
        handle = handle.create()
        
        return guide_top, handle
    
    def _create_spline(self, follow, btm_constrain, mid_constrain):
        
        name = self._get_name()
        
        spline_setup_group = cmds.group( em = True, n = util.inc_name('splineSetup_%s' % name))
        cmds.hide(spline_setup_group)
        cluster_group = cmds.group( em = True, n = util.inc_name('clusterSetup_%s' % name))
        
        #do not do this way unless heavily tested first
        """
        handle = util.IkHandle(name)
        handle.set_solver(handle.solver_spline)
        handle.set_start_joint(self.buffer_joints[0])
        handle.set_end_joint(self.buffer_joints[-1])
        
        ik_handle = handle.create()
        curve = handle.curve
        
        ik_handle = cmds.rename(ik_handle, util.inc_name('handle_spline_%s' % name))
        """
        
        #here 
        ik_handle, effector, curve = cmds.ikHandle(sj = self.buffer_joints[0], 
                                                ee = self.buffer_joints[-1], 
                                                sol = 'ikSplineSolver', 
                                                pcv = False, 
                                                name = util.inc_name('handle_spline_%s' % name))
        #to here  could be replaced some day
        
        cmds.setAttr('%s.inheritsTransform' % curve, 0)
        
        curve = cmds.rename(curve, util.inc_name('curve_%s' % name) )
        effector = cmds.rename(effector, util.inc_name('effector_%s' % name))
        
        top_cluster, top_handle = cmds.cluster('%s.cv[0]' % curve, n = 'clusterTop_%s' % name)
        mid_cluster, mid_handle = cmds.cluster('%s.cv[1:2]' % curve, n = 'clusterMid_%s' % name)
        btm_cluster, btm_handle = cmds.cluster('%s.cv[3]' % curve, n = 'clusterBtm_%s' % name)
        
        cmds.parent([top_handle, mid_handle, btm_handle], cluster_group )
        cmds.parent([ik_handle, curve], spline_setup_group)
        cmds.parent(cluster_group, spline_setup_group)
        
        cmds.parent(spline_setup_group, self.setup_group)
        
        cmds.parentConstraint(follow, cluster_group, mo = True)
        
        cmds.pointConstraint(btm_constrain, btm_handle, mo = True)
        cmds.parentConstraint(mid_constrain, mid_handle, mo = True)
        
        return ik_handle, curve
    
    def _setup_stretchy(self, curve, control):
        
        util.create_spline_ik_stretch(curve, self.buffer_joints[:-1], control)
    
    def _create_top_control(self):
        
        if not self.end_with_locator:
            control = self._create_control('top')
        if self.end_with_locator:
            control = self._create_control()
            
        control.set_curve_type(self.control_shape)
            
        control.hide_scale_and_visibility_attributes()
        
        xform = util.create_xform_group(control.get())
        
        orient_transform = self.control_orient
        
        if not orient_transform:
            orient_transform = self.joints[0]
        
        util.MatchSpace(orient_transform, xform).translation_rotation()
        
        self._fix_right_side_orient(xform)
        
        return control.get(), xform
    
    def _create_btm_control(self):
        control = self._create_control('btm')
        control.hide_scale_and_visibility_attributes()
        
        control.set_curve_type(self.control_shape)
        
        xform = util.create_xform_group(control.get())
        
        orient_translate = self.joints[-1]
        orient_rotate = self.control_orient
                
        if not orient_rotate:
            orient_rotate = self.joints[0]
        
        util.MatchSpace(orient_translate, xform).translation()
        util.MatchSpace(orient_rotate, xform).rotation()
        
        self._fix_right_side_orient(xform)
        
        return control.get(), xform
    
    def _create_btm_sub_control(self):
        control = self._create_control('btm', sub = True)
        control.scale_shape(.5, .5, .5)
        control.hide_scale_and_visibility_attributes()
        
        xform = util.create_xform_group(control.get())
        
        orient_translate = self.joints[-1]
        orient_rotate = self.control_orient
        
        if not orient_rotate:
            orient_rotate = self.joints[0]
        
        util.MatchSpace(orient_translate, xform).translation()
        util.MatchSpace(orient_rotate, xform).rotation()
        
        
        self._fix_right_side_orient(xform)
        
        return control.get(), xform
        
    def _create_mid_control(self):
        
        if self.bool_create_middle_control:
            control = self._create_control('mid', sub = True)
            control.scale_shape(.5, .5, .5)
            control.hide_scale_and_visibility_attributes()
            
            
            control = control.get()
        
        if not self.bool_create_middle_control:
            mid_locator = cmds.spaceLocator(n = util.inc_name(self._get_name('locator', 'mid')))[0]
            control = mid_locator
            cmds.hide(mid_locator)
        
        xform = util.create_xform_group(control)
        
        orient_transform = self.control_orient
        
        if not orient_transform:
            orient_transform = self.joints[0]
        
        util.MatchSpace(orient_transform, xform).translation_rotation()
        
        self._fix_right_side_orient(xform)
        
        return control, xform
    
    def _fix_right_side_orient(self, control):
        
        #goo = self.right_side_fix_axis
        
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
            
        #cmds.setAttr('%s.rotateZ' % xform_locator, 180)
        
        match = util.MatchSpace(xform_locator, control)
        match.translation_rotation()
        
        cmds.delete(spacer)
    
    def set_end_with_locator(self, True):
        self.end_with_locator = True
    
    def set_guide_top_btm(self, top_guide, btm_guide):
        self.top_guide = top_guide
        self.btm_guide = btm_guide
    
    def set_control_shape(self, name):
        self.control_shape = name
    
    def set_create_middle_control(self, bool_value):
        
        self.bool_create_middle_control = bool_value
    
    def set_right_side_fix(self, bool_value, axis):
        self.right_side_fix = bool_value
        self.right_side_fix_axis = axis
    
    def set_control_orient(self, transform):
        self.control_orient = transform
    
    def create(self):
        super(IkSplineNubRig, self).create()
        
        
        top_control, top_xform = self._create_top_control()
        
        self.top_control = top_control
        self.top_xform = top_xform
        
        if not self.end_with_locator:
            btm_control, btm_xform = self._create_btm_control()
            sub_btm_control, sub_btm_xform = self._create_btm_sub_control()
            cmds.parent(sub_btm_xform, btm_control)
            
        if self.end_with_locator:
            
            btm_control = cmds.spaceLocator(n = util.inc_name('locator_%s' % self._get_name()))[0]
            btm_xform = btm_control
            sub_btm_control = btm_control
            cmds.hide(btm_control)
            
            orient_translate = self.joints[-1]
            orient_rotate = self.control_orient
                    
            if not orient_rotate:
                orient_rotate = self.joints[0]
            
            util.MatchSpace(orient_translate, btm_control).translation()
            util.MatchSpace(orient_rotate, btm_control).rotation()
            
            self._fix_right_side_orient(btm_control)
            
        
        self.btm_control = btm_control
        self.btm_xform = btm_xform
            
        mid_control, mid_xform = self._create_mid_control()
        
        cmds.parent(top_xform, self.control_group)
            
        cmds.parent(mid_xform, top_control)
        
        top_joint, handle = self._create_joint_line()
        sub_joint, sub_handle = self._create_joint_line()
        
        
        
        cmds.parent(sub_joint, top_joint)
        cmds.parent(sub_handle, top_joint)
        
        self._create_twist_group(top_control, handle, top_joint)
        
        util.create_follow_group(top_joint, mid_xform)
        cmds.pointConstraint(top_control, sub_btm_control, mid_xform)
        
        spline_handle, curve = self._create_spline(top_joint, sub_btm_control, mid_control)
        #cmds.connectAttr( '%s.rotateX' % sub_joint, '%s.twist' % spline_handle)
        
        self._setup_stretchy(curve, top_control)
        
        util.create_follow_group(top_control, top_joint)
        #cmds.parentConstraint(top_control, top_joint, mo = True)
        util.create_follow_group(sub_btm_control, sub_handle)
        #cmds.parentConstraint(sub_btm_control, sub_handle, mo = True)
        
        top_twist = cmds.group(em = True, n = 'topTwist_%s' % spline_handle)
        btm_twist = cmds.group(em = True, n = 'btmTwist_%s' % spline_handle)
        
        cmds.parent(btm_twist, sub_joint)
        
        util.MatchSpace(self.buffer_joints[0], top_twist).translation_rotation()
        
        util.MatchSpace(self.buffer_joints[-1], btm_twist).translation()
        util.MatchSpace(self.buffer_joints[0], btm_twist).rotation()
        
        cmds.setAttr('%s.dTwistControlEnable' % spline_handle, 1)
        cmds.setAttr('%s.dWorldUpType' % spline_handle, 4)
        
        cmds.connectAttr('%s.worldMatrix' % top_twist, '%s.dWorldUpMatrix' % spline_handle)
        cmds.connectAttr('%s.worldMatrix' % btm_twist, '%s.dWorldUpMatrixEnd' % spline_handle)
                
        cmds.parent(top_twist, top_control)
        #cmds.parent(btm_twist, sub_btm_control)
        
        cmds.pointConstraint(sub_btm_control, handle, mo = True)
        util.create_xform_group(handle)
        util.create_xform_group(sub_handle)
        
        cmds.parent(btm_xform, top_control)
        
        if self.top_guide:
            cmds.parentConstraint(self.top_guide, top_xform, mo =  True)
        
        if self.btm_guide:
            cmds.parent(btm_xform, self.btm_guide)


class IkAppendageRig(BufferRig):
    
    def __init__(self, description, side):
        super(IkAppendageRig, self).__init__(description, side)
        
        self.create_twist = True
        self.create_stretchy = False
        self.btm_control = None
        self.offset_pole_locator = None
        self.pole_offset = 3
        self.right_side_fix = True
        self.orient_constrain = True
        self.curve_type = None
        self.create_sub_control = True
        self.sub_control = None
        self.top_as_locator = False
        self.match_btm_to_joint = True
        self.create_world_switch = True
        self.create_top_control = True
        self.pole_follow_transform = None
        self.pole_angle_joints = []
        self.top_control_right_side_fix = True
        self.stretch_axis = 'X'
        
    
    def _attach_ik_joints(self, source_chain, target_chain):
        
        for inc in range( 0, len(source_chain) ):
            source = source_chain[inc]
            target = target_chain[inc]
            
            cmds.parentConstraint(source, target)
            util.connect_scale(source, target)
            
    def _duplicate_joints(self):
        
        super(IkAppendageRig, self)._duplicate_joints()
        
        duplicate = util.DuplicateHierarchy(self.joints[0])
        duplicate.stop_at(self.joints[-1])
        duplicate.replace('joint', 'ik')
        
        self.ik_chain = self.buffer_joints
                
        if not self.create_buffer_joints:
            pass
            #util.AttachJoints(self.ik_chain, self.buffer_joints).create()
        
        if self.create_buffer_joints:
                
            
            #self._attach_ik_joints(self.ik_chain, self.buffer_joints)
            
            ik_group = self._create_group()
            cmds.parent(self.ik_chain[0], ik_group)
            cmds.parent(ik_group, self.setup_group)
    
    def _create_buffer_joint(self):
        
        buffer_joint = cmds.duplicate(self.ik_chain[-1], po = True)[0]
        
        cmds.parent(self.ik_chain[-1], buffer_joint)
        
        if not cmds.isConnected('%s.scale' % buffer_joint, '%s.inverseScale' % self.ik_chain[-1]):
            cmds.connectAttr('%s.scale' % buffer_joint, '%s.inverseScale' % self.ik_chain[-1])
                
        attributes = ['rotateX',
                      'rotateY',
                      'rotateZ',
                      'jointOrientX',
                      'jointOrientY',
                      'jointOrientZ'
                      ]
        
        for attribute in attributes:
            cmds.setAttr('%s.%s' % (self.ik_chain[-1], attribute), 0)
        
        return buffer_joint
        
    def _create_ik_handle(self):
        
        buffer_joint = self._create_buffer_joint()
        
        ik_handle = util.IkHandle( self._get_name() )
        
        ik_handle.set_start_joint( self.ik_chain[0] )
        ik_handle.set_end_joint( buffer_joint )
        ik_handle.set_solver(ik_handle.solver_rp)
        self.ik_handle = ik_handle.create()
        
        xform_ik_handle = util.create_xform_group(self.ik_handle)
        cmds.parent(xform_ik_handle, self.setup_group)
        
        cmds.hide(xform_ik_handle)
        
    def _create_top_control(self):
        
        if not self.top_as_locator:
            control = self._create_control(description = 'top')
            control.hide_scale_and_visibility_attributes()
        
            if self.curve_type:
                control.set_curve_type(self.curve_type)
            
                control.scale_shape(2, 2, 2)
        
            self.top_control = control.get()
            
            
            
        if self.top_as_locator:
            self.top_control = cmds.spaceLocator(n = 'locator_%s' % self._get_name())[0]
        
        return self.top_control
    
    def _xform_top_control(self, control):
        
        match = util.MatchSpace(self.ik_chain[0], control)
        match.translation_rotation()
        
        self._fix_right_side_orient(control)
        
        cmds.parentConstraint(control, self.ik_chain[0], mo = True)
        
        xform_group = util.create_xform_group(control)
        
        cmds.parent(xform_group, self.control_group)
    
    def _create_btm_control(self):
        
        control = self._create_control(description = 'btm')
        control.hide_scale_and_visibility_attributes()
        
            
        control.scale_shape(2, 2, 2)
        
        self.btm_control = control.get()
        
        self._fix_right_side_orient( control.get() )
        
        if self.create_sub_control:
            sub_control = self._create_control('BTM', sub = True)
            
            sub_control.hide_scale_and_visibility_attributes()
            
            xform_group = util.create_xform_group( sub_control.get() )
            
            self.sub_control = sub_control.get()
        
            cmds.parent(xform_group, control.get())
            
            util.connect_visibility('%s.subVisibility' % self.btm_control, '%sShape' % self.sub_control, 1)
        
        return control.get()
    
    def _fix_right_side_orient(self, control):
        
        
        if not self.right_side_fix:
            return
    
        if not self.side == 'R':
            return
        
        
        
        xform_locator = cmds.spaceLocator()[0]
        
        match = util.MatchSpace(control, xform_locator)
        match.translation_rotation()
        
        spacer = util.create_xform_group(xform_locator)
        
        cmds.setAttr('%s.rotateY' % xform_locator, 180)
        cmds.setAttr('%s.rotateZ' % xform_locator, 180)
        
        match = util.MatchSpace(xform_locator, control)
        match.translation_rotation()
        
        cmds.delete(spacer)
        
    def _xform_btm_control(self, control):
        
        if self.match_btm_to_joint:
            match = util.MatchSpace(self.ik_chain[-1], control)
            match.translation_rotation()
        if not self.match_btm_to_joint:
            util.MatchSpace(self.ik_chain[-1], control).translation()
        
        self._fix_right_side_orient(control)
        
        ik_handle_parent = cmds.listRelatives(self.ik_handle, p = True)[0]
        
        if self.sub_control:
            cmds.parent(ik_handle_parent, self.sub_control)
        if not self.sub_control:
            cmds.parent(ik_handle_parent, control)
        #cmds.parentConstraint(self.sub_control, ik_handle_parent, mo = True)
        
        xform_group = util.create_xform_group(control)
        drv_group = util.create_xform_group(control, 'driver')
        
        if self.create_world_switch:
            self._create_local_to_world_switch(control, xform_group, drv_group)
        
        cmds.parent(xform_group, self.control_group)
        
        if self.orient_constrain:
            
            if self.sub_control:
                cmds.orientConstraint(self.sub_control, self.ik_chain[-1], mo = True)
                
            if not self.sub_control:
                cmds.orientConstraint(control, self.ik_chain[-1], mo = True)
        
    def _create_local_to_world_switch(self, control, xform_group, driver_group):
        
        cmds.addAttr(control, ln = 'world', min = 0, max = 1, dv = 0, at = 'double', k = True)
        
        local_group = self._create_group('IkLocal')
        match = util.MatchSpace(control, local_group)
        match.translation_rotation()
        
        world_group = self._create_group('IkWorld')
        match = util.MatchSpace(control, world_group)
        match.translation()
            
        if not self.right_side_fix and self.side == 'R':
            cmds.rotate(180,0,0, world_group)
        
        cmds.parent([local_group,world_group], xform_group)
        
        cmds.orientConstraint(local_group, driver_group)
        cmds.orientConstraint(world_group, driver_group)
        
        constraint = util.ConstraintEditor()
        
        active_constraint = constraint.get_constraint(driver_group, constraint.constraint_orient)
        
        constraint.create_switch(control, 'world', active_constraint)
        
        self.world_group = world_group
        self.local_group = local_group
    
    def _create_top_btm_joint(self, joints, prefix):
        top_position = cmds.xform(joints[0], q = True, t = True, ws = True)
        btm_position = cmds.xform(joints[-1], q = True, t = True, ws = True)
        
        top_name = self._get_name(prefix, 'top')
        btm_name = self._get_name(prefix, 'btm')
        
        cmds.select( cl = True )
        
        top_joint = cmds.joint(p = top_position, n = top_name)
        btm_joint = cmds.joint(p = btm_position, n = btm_name)
        
        cmds.joint(top_joint, e = True, zso = True, oj = 'xyz', sao = 'yup')
        
        return [top_joint, btm_joint]
        
    def _create_twist_ik(self, joints, description):
        
        ik_handle = util.IkHandle(description)
        ik_handle.set_solver(ik_handle.solver_sc)
        ik_handle.set_start_joint(joints[0])
        ik_handle.set_end_joint(joints[-1])
        return ik_handle.create()
        
    def _create_twist_joint(self, top_control):
        
        top_guide_joint, btm_guide_joint = self._create_top_btm_joint( [self.buffer_joints[-1], self.buffer_joints[0]], 'guide')
        top_guidetwist_joint, btm_guidetwist_joint = self._create_top_btm_joint( [self.buffer_joints[0], self.buffer_joints[-1]], 'guideTwist')
        
        self.twist_guide = top_guidetwist_joint
        
        guide_ik = self._create_twist_ik([top_guide_joint, btm_guide_joint], 'guide')
        twist_guide_ik = self._create_twist_ik([top_guidetwist_joint, btm_guidetwist_joint], 'guideTwist')
        
        cmds.parent(top_guidetwist_joint, top_guide_joint)
        cmds.parent(twist_guide_ik, top_guide_joint)
        
        cmds.parent(top_guide_joint, self.setup_group)
        cmds.parent(guide_ik, self.setup_group)
        
        if self.sub_control:
            cmds.pointConstraint( self.sub_control, top_guide_joint )
        if not self.sub_control:
            cmds.pointConstraint( self.btm_control, top_guide_joint )
            
        cmds.pointConstraint( top_control, guide_ik )
        
        if self.sub_control:
            offset_locator = cmds.spaceLocator(n = 'offset_%s' % self.sub_control)[0]
            cmds.parent(offset_locator, self.sub_control)
            
            match = util.MatchSpace(self.sub_control, offset_locator)
            match.translation_rotation()
            
        if not self.sub_control:
            offset_locator = cmds.spaceLocator(n = 'offset_%s' % self.btm_control)[0]
            cmds.parent(offset_locator, self.btm_control)
            
            match = util.MatchSpace(self.btm_control, offset_locator)
            match.translation_rotation()
        
        cmds.hide(offset_locator)
        
        cmds.parentConstraint( offset_locator, twist_guide_ik, mo = True )
        
        self.offset_pole_locator = offset_locator
        
    def _get_pole_joints(self):
        if not self.pole_angle_joints:
            mid_joint_index  = len(self.ik_chain)/2
            mid_joint_index = int(mid_joint_index)
            mid_joint = self.ik_chain[mid_joint_index]
            
            joints = [self.ik_chain[0], mid_joint, self.ik_chain[-1]]
            
            return joints
        
        return self.pole_angle_joints            
        
    def _create_pole_vector(self):
        
        control = self._create_control('POLE')
        control.hide_scale_and_visibility_attributes()
        control.set_curve_type('cube')
        self.poleControl = control.get()
        
        util.create_title(self.btm_control, 'POLE_VECTOR')
        
        pole_vis = util.MayaNumberVariable('poleVisibility')
        pole_vis.set_variable_type(pole_vis.TYPE_BOOL)
        pole_vis.create(self.btm_control)
        
        twist_var = util.MayaNumberVariable('twist')
        twist_var.create(self.btm_control)
        
        if self.side == 'L':
            twist_var.connect_out('%s.twist' % self.ik_handle)
            
        if self.side == 'R':
            util.connect_multiply('%s.twist' % self.btm_control, '%s.twist' % self.ik_handle, -1)
        
        pole_joints = self._get_pole_joints()
        
        position = util.get_polevector( pole_joints[0], pole_joints[1], pole_joints[2], self.pole_offset )
        cmds.move(position[0], position[1], position[2], control.get())
        
        cmds.poleVectorConstraint(control.get(), self.ik_handle)
        
        xform_group = util.create_xform_group( control.get() )
        
        follow_group = None
        
        if self.create_twist:
            
            if not self.pole_follow_transform:
                follow_group = util.create_follow_group(self.top_control, xform_group)
            if self.pole_follow_transform:
                follow_group = util.create_follow_group(self.pole_follow_transform, xform_group)
                
            constraint = cmds.parentConstraint(self.twist_guide, follow_group, mo = True)[0]
            
            constraint_editor = util.ConstraintEditor()
            constraint_editor.create_switch(self.btm_control, 'autoTwist', constraint)
            cmds.setAttr('%s.autoTwist' % self.btm_control, 0)
        
        if not self.create_twist:
            if self.pole_follow_transform:
                follow_group = util.create_follow_group(self.pole_follow_transform, xform_group)
                
            
            if not self.pole_follow_transform:
                follow_group = xform_group
            #    follow_group = util.create_follow_group(self.top_control, xform_group)
        
        if follow_group:
            cmds.parent(follow_group,  self.control_group )
        
        name = self._get_name()
        
        rig_line = util.RiggedLine(pole_joints[1], control.get(), name).create()
        cmds.parent(rig_line, self.control_group)
        
        pole_vis.connect_out('%s.visibility' % xform_group)
        pole_vis.connect_out('%s.visibility' % rig_line)
        
        self.pole_vector_xform = xform_group
        

    def _create_stretchy(self, top_transform, btm_transform, control):
        stretchy = util.StretchyChain()
        
        stretchy.set_joints(self.ik_chain)
        #dampen should be damp... dampen means wet, damp means diminish
        stretchy.set_add_dampen(True)
        stretchy.set_node_for_attributes(control)
        stretchy.set_description(self._get_name())
        stretchy.set_scale_axis(self.stretch_axis)
        
        #this is new stretch distance
        #stretchy.set_vector_instead_of_matrix(False)
        top_locator, btm_locator = stretchy.create()
        
        cmds.parent(top_locator, top_transform)
        cmds.parent(btm_locator, btm_transform)
        
        #this is new stretch distance
        """
        cmds.parent(top_locator, self.setup_group)
        cmds.parent(btm_locator, self.setup_group)
        
        cmds.pointConstraint(top_transform, top_locator)
        cmds.pointConstraint(btm_transform, btm_locator)
        """
        
    def _create_tweakers(self):
        pass
    
    def set_create_twist(self, bool_value):
        
        self.create_twist = bool_value
    
    def set_create_stretchy(self, bool_value):
        self.create_stretchy = bool_value
    
    def set_stretch_axis(self, axis_letter):
        self.stretch_axis = axis_letter
    
    def set_pole_offset(self, value):
        self.pole_offset = value
    
    def set_pole_angle_joints(self, joints):
        self.pole_angle_joints = joints
    
    def set_right_side_fix(self, bool_value):
        self.right_side_fix = bool_value
    
    def set_orient_constrain(self, bool_value):
        self.orient_constrain = bool_value
        
    def set_curve_type(self, curve_name):
        self.curve_type = curve_name
    
    def set_create_sub_control(self, bool_value):
        self.create_sub_control = bool_value
    
    def set_create_world_switch(self, bool_value):
        self.create_world_switch = bool_value
    
    def set_top_control_as_locator(self, bool_value):
        self.top_as_locator = bool_value
    
    def set_match_btm_to_joint(self, bool_value):
        self.match_btm_to_joint = bool_value
        
    def set_create_top_control(self, bool_value):
        self.create_top_control = bool_value
    
    def set_pole_follow_transform(self, transform):
        
        self.pole_follow_transform = transform
        
    
    def create(self):
        super(IkAppendageRig, self).create()
        
        self._create_ik_handle()
        
        if self.create_top_control:
            top_control = self._create_top_control()
        if not self.create_top_control:
            top_control = cmds.spaceLocator(n = 'locator_top_%s' % self._get_name())[0]
            self.top_control = top_control
            util.MatchSpace(self.joints[0], top_control).translation_rotation()
            
        self._xform_top_control(top_control)
        
        btm_control = self._create_btm_control()
        self._xform_btm_control(btm_control)
        
        if self.create_twist:
            self._create_twist_joint(top_control)
        
        
        self._create_pole_vector()
        
        
        if self.sub_control:
            self._create_stretchy(top_control, self.sub_control, btm_control)
        if not self.sub_control:
            self._create_stretchy(top_control, self.btm_control, btm_control)
        
        
            
class TweakCurveRig(BufferRig):
    
    def __init__(self, name, side):
        super(TweakCurveRig, self).__init__(name, side)
        
        self.control_count = 4
        self.curve = None
        self.surface = None
        self.use_ribbon = True
        
        self.create_buffer_joints = False
        
        self.orient_controls_to_joints = True
        self.orient_joint = None
        
        self.join_both_ends = False
        
        self.ribbon_offset = 1
        self.ribbon_offset_axis = 'Z'
    
    def _create_control(self, sub = False):
        
        control = super(TweakCurveRig, self)._create_control(sub = sub)
        
        control.hide_scale_and_visibility_attributes()
        
        return control.get()
    
    def _create_ik_guide(self):
        
        if not self.use_ribbon:
            if not self.surface:
            
                name = self._get_name()
                
                self.surface = util.transforms_to_curve(self.buffer_joints, self.control_count, name)
                
                cmds.rebuildCurve(self.surface, 
                                  spans = self.control_count - 1 ,
                                  rpo = True,  
                                  rt = 0, 
                                  end = 1, 
                                  kr = False, 
                                  kcp = False, 
                                  kep = True,  
                                  kt = False,
                                  d = 3)
                
                
                self.surface = cmds.rename(self.surface, name)
                
                cmds.parent(self.surface, self.setup_group)
                
        
        if self.use_ribbon:
            if not self.surface:
                surface = util.transforms_to_nurb_surface(self.buffer_joints, self._get_name(self.description), spans = -1, offset_axis = self.ribbon_offset_axis, offset_amount = self.ribbon_offset)
                cmds.rebuildSurface(surface, ch = True, rpo = True, rt =  False,  end = True, kr = 0, kcp = 0, kc = 0, su = 1, du = 1, sv = self.control_count-1, dv = 3, fr = 0, dir = True)
        
                self.surface = surface
                
                cmds.parent(self.surface, self.setup_group)
    
    def _cluster(self, description):
        
        
        cluster_curve = util.ClusterSurface(self.surface, self._get_name(description))
        cluster_curve.set_join_ends(True)
        cluster_curve.set_join_both_ends(self.join_both_ends)
        cluster_curve.create()
        
        self.cluster_deformers = cluster_curve.clusters
        
        return cluster_curve.get_cluster_handle_list()
        
    def set_control_count(self, int_value):
        
        self.control_count = int_value
        
    def set_use_ribbon(self, bool_value):
        self.use_ribbon = bool_value
        
    def set_ribbon(self, bool_value):
        self.use_ribbon = bool_value
        
    def set_ribbon_offset(self, float_value):
        self.ribbon_offset = float_value
       
    def set_ribbon_offset_axis(self, axis_letter):
        self.ribbon_offset_axis = axis_letter
        
    def set_orient_controls_to_joints(self, bool_value):
        self.orient_controls_to_joints = bool_value
        
    def set_join_both_ends(self, bool_value):
        self.join_both_ends = bool_value
        
    def create(self):
        super(TweakCurveRig, self).create()
        
        self._create_ik_guide()
        
        clusters = self._cluster(self.description)
        
        cmds.parent(clusters, self.setup_group)
        
        for cluster in clusters:
            control = self._create_control()
            
            xform = util.create_xform_group(control)
            util.create_xform_group(control, 'driver')
            
            util.MatchSpace(cluster, xform).translation_to_rotate_pivot()
            
            if self.orient_controls_to_joints:
            
                if not self.orient_joint:
                    joint = util.get_closest_transform(cluster, self.buffer_joints)            
                    
                if self.orient_joint:
                    joint = self.orient_joint
                
                util.MatchSpace(joint, xform).translation_rotation()
            
            cmds.parentConstraint(control, cluster, mo = True)
            
            cmds.parent(xform, self.control_group)
        
        if util.has_shape_of_type(self.surface, 'nurbsCurve'):
            self.maya_type = 'nurbsCurve'
        if util.has_shape_of_type(self.surface, 'nurbsSurface'):
            self.maya_type = 'nurbsSurface'
            
        if self.attach_joints:
            for joint in self.buffer_joints:
                if self.maya_type == 'nurbsSurface':
                    rivet = util.attach_to_surface(joint, self.surface)
                    cmds.parent(rivet, self.setup_group)
                if self.maya_type == 'nurbsCurve':
                    util.attach_to_curve(joint, self.surface)
                    cmds.orientConstraint(self.control_group, joint)
                        
class RopeRig(CurveRig):

    def __init__(self, name, side):
        super(RopeRig, self).__init__(name, side)
        
        self.subdivision = 0
        
        self._sub_run = False
        
        self._division_value = 2
        self.cluster_deformers = []
        
    def _define_control_shape(self):
        return 'cube'

    def _rebuild_curve(self, curve, spans,inc):
        
        if self._sub_run:
            curve_split = curve.split('_')
            curve_split[-1] = 'sub%s' % (inc+1)
            name = string.join(curve_split, '_')
            
        if not self._sub_run:
            name = '%s_sub%s' % (curve, (inc+1))
        
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
                                           degree =3,
                                           name = name)
        
        
        cmds.delete(rebuilt_curve, ch = True)
        
        return rebuilt_curve, node
        
    def _cluster_curve(self, curve, description):
        
        cluster_curve = util.ClusterCurve(curve, self._get_name(description))
        cluster_curve.create()
        self.cluster_deformers = cluster_curve.clusters
        
        return cluster_curve.get_cluster_handle_list()
    
    def _subdivide(self):
        
        curves = [self.curves[0]]
        
        last_curve = None
        
        for inc in range(0, self.subdivision):


            if last_curve:
                curve = last_curve
            if not last_curve:
                curve = self.curves[0]

            curveObject = util.nodename_to_mobject(cmds.listRelatives(curve, s = True)[0])
            curve_object = util.NurbsCurveFunction(curveObject)
            spans = curve_object.get_span_count()
            
            
            rebuilt_curve, rebuild_node = self._rebuild_curve(curve, spans*self._division_value, inc)
            
            curves.append(rebuilt_curve)
            cmds.parent(rebuilt_curve, self.setup_group)
            last_curve = rebuilt_curve
        
            self._sub_run = True
            
        self._sub_run = False
        return curves
    
    def set_subdivisions(self, int_value):
        
        if int_value < 0:
            int_value = 0
        
        self.subdivision = int_value
        
    def set_division_value(self, int_value):
        if int_value < 2:
            int_value = 2
            
        self._division_value = int_value

    def create(self):

        curves = self._subdivide()
        
        
        scale = 1
        
        scale_section = 1.000/len(curves)
        alt_color = False
        
        description = None
        
        inc = 0
        
        last_curve = None

        for curve in curves:
            if inc > 0:
                description = 'sub%s' % inc
            if inc == 0:
                description = 'main'
            
            clusters = self._cluster_curve(curve, description)
            
            control_group = cmds.group(em = True, n = util.inc_name('controls_%s' % (self._get_name(description))))
            setup_group = cmds.group(em = True, n = util.inc_name('setup_%s' % (self._get_name(description))))
            
            cmds.parent(control_group, self.control_group)
            cmds.parent(setup_group, self.setup_group)
            
            inc2 = 0
            
            for cluster in clusters:
                
                if description:
                    control = self._create_control(description)
                if not description:
                    control = self._create_control()
                
                if not alt_color:
                    control.color(util.get_color_of_side(self.side))    
                if alt_color:
                    control.color(util.get_color_of_side(self.side, sub_color = True))
                
                util.MatchSpace(cluster, control.get()).translation_to_rotate_pivot()
                
                offset_cluster = cmds.group(em = True, n = 'offset_%s' % cluster)
                util.MatchSpace(cluster, offset_cluster).translation_to_rotate_pivot()
                
                xform_cluster = util.create_xform_group(cluster)
                
                cmds.parent(xform_cluster, offset_cluster)
                cmds.parent(offset_cluster, setup_group)
                
                xform_offset = util.create_xform_group(offset_cluster)
                
                
                control.scale_shape(scale, scale, scale) 
                
                
                xform = util.create_xform_group(control.get())
                util.connect_translate(control.get(), cluster)
                
                control.hide_scale_attributes()
                
                if last_curve:
                    util.attach_to_curve(xform, last_curve)
                    util.attach_to_curve(xform_offset, last_curve)
                    
                cmds.parent(xform, control_group)
                    
                inc2 +=1
                
            scale = scale - scale_section
            
            last_curve = curve
            
            inc += 1
            
            if alt_color:
                alt_color = False 
                continue
            
            if not alt_color:
                
                alt_color = True
                
class ConvertJointToNub(object):

    def __init__(self, name, side = 'C'):
        self.start_joint = None
        self.end_joint = None
        self.count = 10
        self.prefix = 'joint'
        self.name = name
        self.side = side
        
        self.add_mid_control = True
        
        self.joints = []
        self.control_group = None
        self.setup_group = None
        self.control_shape = 'pin_round'
        self.add_sub_joints = False
        
        self.right_side_fix = True
        self.right_side_fix_axis = 'x'
        
        self.up_object = None
        
    def set_start_joint(self, joint):
        self.start_joint = joint
    
    def set_end_joint(self, joint):
        self.end_joint = joint
        
    def set_joints(self, joints):
        self.joints = joints
        
    def set_create_mid_control(self, bool_value):
        self.add_mid_control = bool_value
        
    def set_joint_count(self, count):
        self.count = count
        
    def set_control_shape(self, shape_type_name):
        self.control_shape = shape_type_name
        
    def set_prefix(self, prefix):
        self.prefix = prefix
        
    def set_add_sub_joints(self, bool_value):
        self.add_sub_joints = bool_value
        
    def set_up_object(self, name):
        self.up_object = name
        
    def create(self):
        
        parent_joints = False
        
        if not self.joints:
            parent_joints = True
            joints = util.subdivide_joint(self.start_joint, 
                                     self.end_joint, 
                                     self.count, self.prefix, 
                                     '%s_1_%s' % (self.name,self.side), True)
            
            
            
            for joint in joints[:-1]:
                orient = util.OrientJoint(joint)
                
                if not self.up_object:
                    self.up_object = self.start_joint
                
                orient.set_aim_up_at_object(self.up_object)
                orient.run()
            
            cmds.makeIdentity(joints[-1], r = True, jo = True, apply = True)
            
            self.joints = joints
            
        parent_map = {}
            
        if self.add_sub_joints:
            
            new_joints = []
            
            for joint in self.joints:
                duplicate = cmds.duplicate(joint, po = True)
                
                new_name = joint[0].upper() + joint[1:]
                
                new_joint = cmds.rename(joint, 'xform%s' % new_name)
                duplicate = cmds.rename(duplicate, joint)
                cmds.parent(duplicate, w = True)
                
                new_joints.append(new_joint)
                
                parent_map[new_joint] = duplicate
                
            self.joints = new_joints
        
        rig = IkSplineNubRig(self.name, self.side)
        rig.set_joints(self.joints)
        rig.set_end_with_locator(True)
        rig.set_create_middle_control(self.add_mid_control)
        rig.set_control_shape(self.control_shape)
        #rig.set_control_orient(self.start_joint)
        rig.set_buffer(False)
        rig.set_right_side_fix(self.right_side_fix, self.right_side_fix_axis)
        rig.create()
        
        self.top_control = rig.top_control
        self.btm_control = rig.btm_control
        self.top_xform = rig.top_xform
        self.btm_xform = rig.btm_xform
        
        if parent_joints:
            cmds.parent(joints[0], rig.setup_group)
        
        if parent_map:
            for joint in parent_map:
                cmds.parent(parent_map[joint], joint)
        
        self.control_group = rig.control_group
        self.setup_group = rig.setup_group
        
    def get_control_group(self):
        return self.control_group
    
    def get_setup_group(self):
        return self.setup_group
    
    def get_joints(self):
        return self.joints
    
    def set_right_side_fix(self, bool_value, axis = 'x'):
        self.right_side_fix = bool_value
        self.right_side_fix_axis = axis

                          
#---Body Rig

class NeckRig(FkCurveRig):
    def _first_increment(self, control, current_transform):
        self.first_control = control

class IkLegRig(IkAppendageRig):
    
    def _fix_right_side_orient(self, control, axis = 'yz'):
        
        
        
        if not self.right_side_fix:
            return
    
        if not self.side == 'R':
            return
        
        xform_locator = cmds.spaceLocator()[0]
        
        match = util.MatchSpace(control, xform_locator)
        match.translation_rotation()
        
        spacer = util.create_xform_group(xform_locator)
        
        for letter in axis:
        
            cmds.setAttr('%s.rotate%s' % (xform_locator, letter.upper()), 180)
        
        match = util.MatchSpace(xform_locator, control)
        match.translation_rotation()
        
        cmds.delete(spacer)
           
    def _xform_top_control(self, control):
        
        match = util.MatchSpace(self.ik_chain[0], control)
        match.translation_rotation()
        
        self._fix_right_side_orient(control, 'z')
        
        cmds.parentConstraint(control, self.ik_chain[0], mo = True)
        
        xform_group = util.create_xform_group(control)
        
        cmds.parent(xform_group, self.control_group)
            
    def _create_pole_vector(self):
        
        control = self._create_control('POLE')
        control.hide_scale_and_visibility_attributes()
        control.set_curve_type('cube')
        self.poleControl = control.get()
        
        util.create_title(self.btm_control, 'POLE_VECTOR')
                
        pole_vis = util.MayaNumberVariable('poleVisibility')
        pole_vis.set_variable_type(pole_vis.TYPE_BOOL)
        pole_vis.create(self.btm_control)
        
        twist_var = util.MayaNumberVariable('twist')
        twist_var.create(self.btm_control)
        
        if self.side == 'L':
            twist_var.connect_out('%s.twist' % self.ik_handle)
            
        if self.side == 'R':
            util.connect_multiply('%s.twist' % self.btm_control, '%s.twist' % self.ik_handle, -1)
            #connect_reverse('%s.twist' % self.btm_control, '%s.twist' % self.ik_handle)
            
        pole_joints = self._get_pole_joints()
        
        position = util.get_polevector( pole_joints[0], pole_joints[1], pole_joints[2], self.pole_offset )
        cmds.move(position[0], position[1], position[2], control.get())

        match = util.MatchSpace(self.btm_control, control.get())
        match.rotation()
        
        cmds.poleVectorConstraint(control.get(), self.ik_handle)
        
        xform_group = util.create_xform_group( control.get() )
        
        if self.create_twist:
            
            follow_group = util.create_follow_group(self.top_control, xform_group)
            constraint = cmds.parentConstraint(self.twist_guide, follow_group, mo = True)[0]
            
            constraint_editor = util.ConstraintEditor()
            constraint_editor.create_switch(self.btm_control, 'autoTwist', constraint)
            cmds.setAttr('%s.autoTwist' % self.btm_control, 1)
            
            twist_offset = util.MayaNumberVariable('autoTwistOffset')
            twist_offset.create(self.btm_control)
            
            if self.side == 'L':
                twist_offset.connect_out('%s.rotateY' % self.offset_pole_locator)
            if self.side == 'R':
                util.connect_multiply('%s.autoTwistOffset' % self.btm_control, 
                                '%s.rotateY' % self.offset_pole_locator, -1)
        
        if not self.create_twist:
            follow_group = util.create_follow_group(self.top_control, xform_group)
        
        cmds.parent(follow_group,  self.control_group )
        
        name = self._get_name()
        
        rig_line = util.RiggedLine(pole_joints[1], control.get(), name).create()
        cmds.parent(rig_line, self.control_group)
        
        pole_vis.connect_out('%s.visibility' % xform_group)
        pole_vis.connect_out('%s.visibility' % rig_line) 
    
    
class RollRig(JointRig):
    
    def __init__(self, description, side):
        super(RollRig, self).__init__(description, side)
        
        self.create_roll_controls = True
        self.attribute_control = None
        
        self.ik_chain = []
        self.fk_chain = []
        
        self.add_hik = None
        
        self.ik_attribute = 'ikFk'
        self.control_shape = 'circle'
        
        self.forward_roll_axis = 'X'
        self.side_roll_axis = 'Z'
        self.top_roll_axis = 'Y'
        
        self.right_side_fix = False
        
    def duplicate_joints(self):
        
        duplicate = util.DuplicateHierarchy(self.joints[0])
        duplicate.only_these(self.joints)
        joints = duplicate.create()
        
        cmds.parent(joints[0], self.setup_group)
        
        return joints
    
    def _get_attribute_control(self):
        if not self.attribute_control:
            return self.roll_control.get()
            
        if self.attribute_control:
            return self.attribute_control        
    
    def _create_pivot_group(self, source_transform, description):
        
        name = self._get_name('pivot', description)
        
        group = cmds.group(em = True, n = name)
        
        match = util.MatchSpace(source_transform, group)
        match.translation_rotation()
        
        xform_group = util.create_xform_group(group)
        
        attribute_control = self._get_attribute_control()
        
        cmds.addAttr(attribute_control, ln = '%sPivot' % description, at = 'double', k = True)
        
        
        cmds.connectAttr('%s.%sPivot' % (attribute_control, description), '%s.rotateY' % group)
        
        if self.right_side_fix and self.side == 'R':
            util.insert_multiply('%s.rotateY' % group, -1) 
        
        return group, xform_group
    
    def _create_pivot_control(self, source_transform, description, sub = False, no_control = False, scale = 1):
        
        if self.create_roll_controls:
            control = self._create_control(description, sub)
            
            control_object = control
            control.set_curve_type(self.control_shape)
            if sub:
                if self.sub_control_shape:
                    control.set_curve_type(self.sub_control_shape)
                            
            control.scale_shape(scale, scale, scale)
            control = control.get()
        
        if not self.create_roll_controls or no_control:
            name = self._get_name('ctrl', description)
            control = cmds.group(em = True, n = util.inc_name(name))
        
        xform_group = util.create_xform_group(control)
        driver_group = util.create_xform_group(control, 'driver')
        
        match = util.MatchSpace(source_transform, xform_group)
        match.translation_rotation()
        
        if self.create_roll_controls:
            
            control_object.hide_scale_attributes()
            control_object.hide_translate_attributes()
            control_object.hide_visibility_attribute()
            
        if self.create_roll_controls:
            cmds.connectAttr('%s.controlVisibility' % self._get_attribute_control(), '%sShape.visibility' % control)
        
        return control, xform_group, driver_group
    
    def _create_roll_control(self, transform):
        
        roll_control = self._create_control('roll') 
        roll_control.set_curve_type('square')
        
        self.roll_control = roll_control
        
        roll_control.scale_shape(.8,.8,.8)
        
        xform_group = util.create_xform_group(roll_control.get())
        
        roll_control.hide_keyable_attributes()
        
        match = util.MatchSpace( transform, xform_group )
        match.translation_rotation()

        #cmds.parentConstraint(roll_control.get(), transform)
        
        cmds.parent(xform_group, self.control_group)
        
        self.roll_control_xform = xform_group 
        
        return roll_control
    
    def _mix_joints(self, joint_chain1, joint_chain2):
        
        count = len(joint_chain1)
        
        self.ik_chain = []
        
        joints_attach_1 = []
        joints_attach_2 = []
        target_joints = []
        
        for inc in range(0, count):
            
            for inc2 in range(0, count):
                if joint_chain1[inc].startswith(self.joints[inc2]):
                    
                    joints_attach_1.append(joint_chain1[inc])
                    joints_attach_2.append(joint_chain2[inc])
                    target_joints.append(self.joints[inc2])
                    
                    constraint = cmds.parentConstraint(joint_chain1[inc], joint_chain2[inc], self.joints[inc2])[0]
                    
                    constraint_editor = util.ConstraintEditor()
                    constraint_editor.create_switch(self.roll_control.get(), self.ik_attribute, constraint)
                    
                    self.ik_chain.append(joint_chain1[inc])
                    self.fk_chain.append(joint_chain2[inc])
                    
        util.AttachJoints(joints_attach_1, target_joints).create()
        util.AttachJoints(joints_attach_2, target_joints).create()
        
        cmds.connectAttr('%s.%s' % (self.roll_control.get(), self.ik_attribute), '%s.switch' % target_joints[0] )
                 
    def _create_ik_fk_attribute(self):
        
        util.create_title(self.roll_control.get(), 'IK_FK')
        ik_fk = util.MayaNumberVariable(self.ik_attribute)
        ik_fk.set_variable_type(ik_fk.TYPE_DOUBLE)
        ik_fk.set_min_value(0)
        ik_fk.set_max_value(1)
        
        if self.add_hik:
            ik_fk.set_max_value(2)
            
        ik_fk.create(self.roll_control.get())
        
                    
    def set_create_roll_controls(self, bool_value):
        
        self.create_roll_controls = bool_value
        
    def set_attribute_control(self, control_name):
        self.attribute_control = control_name
    
    def set_control_shape(self, shape_name):
        self.control_shape = shape_name
    
    def set_add_hik(self, bool_value):
        self.add_hik = bool_value
        if bool_value:
            self.ik_attribute = 'ikFkHik'
    
    def set_forward_roll_axis(self, axis_letter):
        self.forward_roll_axis = axis_letter
        
    def set_side_roll_axis(self, axis_letter):
        self.side_roll_axis = axis_letter
        
    def set_top_roll_axis(self, axis_letter):
        self.top_roll_axis = axis_letter
    
    def set_right_side_fix(self, bool_value):
        self.right_side_fix = bool_value
    
    def create(self):
        super(RollRig, self).create()
        
        joint_chain1 = self.duplicate_joints()
        joint_chain2 = self.duplicate_joints()
        
        self._create_roll_control(self.joints[0])
        
        self._create_ik_fk_attribute()
        
        self._mix_joints(joint_chain1, joint_chain2)
        
        
        util.create_title(self._get_attribute_control(), 'FOOT_PIVOTS')
                
        if self.create_roll_controls:
            bool_var = util.MayaNumberVariable('controlVisibility')
            bool_var.set_variable_type(bool_var.TYPE_BOOL)
            bool_var.create(self._get_attribute_control())
        
    
class FootRollRig(RollRig):
    
    def __init__(self, description, side):
        super(FootRollRig, self).__init__(description, side)
        
        self.defined_joints = []
        self.toe_rotate_as_locator = False
        self.mirror_yaw = False
        self.main_control_follow = None
    
    def _define_joints(self):
        
        self.ankle_index = 0
        self.heel_index = 1
        self.ball_index = 2
        self.toe_index = 3
        self.yawIn_index = 4
        self.yawOut_index = 5
        
        self.ankle = self.ik_chain[self.ankle_index]
        self.heel = self.ik_chain[self.heel_index]
        self.ball = self.ik_chain[self.ball_index]
        self.toe = self.ik_chain[self.toe_index]
        self.yawIn = self.ik_chain[self.yawIn_index]
        
        self.yawOut = self.ik_chain[self.yawOut_index]
        
    def _create_ik_handle(self, name, start_joint, end_joint):
        
        name = self._get_name(name)
        
        ik_handle = util.IkHandle(name)
        ik_handle.set_solver(ik_handle.solver_sc)
        ik_handle.set_start_joint(start_joint)
        ik_handle.set_end_joint(end_joint)
        return ik_handle.create()

    def _create_ik(self):
    
        self.ankle_handle = self._create_ik_handle( 'ankle', self.ankle, self.ball)
        self.ball_handle = self._create_ik_handle( 'ball', self.ball, self.toe)
        
        cmds.parent( self.ankle_handle, self.setup_group )
        cmds.parent( self.ball_handle, self.setup_group )
        
    def _create_toe_rotate_control(self):
        if not self.toe_rotate_as_locator:
            control = self._create_control( 'TOE_ROTATE', True)
            control.hide_translate_attributes()
            control.hide_scale_attributes()
            control.hide_visibility_attribute()
            control.set_curve_type('circle')
            xform_group = control.create_xform()
            control = control.get()
        
        if self.toe_rotate_as_locator:
            control = cmds.spaceLocator(n = self._get_name('locator', 'toe_rotate'))[0]
            xform_group = util.create_xform_group(control)
            attribute_control = self._get_attribute_control()
            
            cmds.addAttr(attribute_control, ln = 'toeRotate', at = 'double', k = True)  
            cmds.connectAttr('%s.toeRotate' % attribute_control, '%s.rotate%s' % (control, self.forward_roll_axis))  
            
        
        match = util.MatchSpace(self.ball, xform_group)
        match.translation_rotation()
        
        cmds.parent(xform_group, self.control_group)
        
        return control, xform_group
    
    def _create_toe_fk_rotate_control(self):
        control = self._create_control( 'TOE_FK_ROTATE')
        control.hide_translate_attributes()
        control.hide_scale_attributes()
        control.hide_visibility_attribute()
        
        xform_group = control.create_xform()
        
        match = util.MatchSpace(self.ball, xform_group)
        match.translation_rotation()
        
        cmds.parent(xform_group, self.control_group)
        
        cmds.parentConstraint(control.get(), self.fk_chain[self.ball_index])
        
        return control, xform_group        
    
    def _create_roll_attributes(self):
        
        attribute_control = self._get_attribute_control()
        
        cmds.addAttr(attribute_control, ln = 'ballRoll', at = 'double', k = True)
        cmds.addAttr(attribute_control, ln = 'toeRoll', at = 'double', k = True)
        cmds.addAttr(attribute_control, ln = 'heelRoll', at = 'double', k = True)
        cmds.addAttr(attribute_control, ln = 'yawRoll', at = 'double', k = True)
    
    def _create_yawout_roll(self, parent):
        
        control, xform, driver = self._create_pivot_control(self.yawOut, 'yawOut')

        cmds.parent(xform, parent)
        
        attribute_control = self._get_attribute_control()
        
        final_value = 10
        if self.mirror_yaw and self.side == 'R':
            final_value = -10
            
        final_other_value = -45
        if self.mirror_yaw and self.side == 'R':
            final_other_value = 45
        
        
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.side_roll_axis),cd = '%s.yawRoll' % attribute_control, driverValue = 0, value = 0, itt = 'spline', ott = 'spline')
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.side_roll_axis),cd = '%s.yawRoll' % attribute_control, driverValue = final_value, value = final_other_value, itt = 'spline', ott = 'spline')
        
        if self.mirror_yaw and self.side == 'R':
            cmds.setInfinity('%s.rotate%s' % (driver, self.side_roll_axis), preInfinite = 'linear')
        else:
            cmds.setInfinity('%s.rotate%s' % (driver, self.side_roll_axis), postInfinite = 'linear')
                
        return control
        
    def _create_yawin_roll(self, parent):
        
        control, xform, driver = self._create_pivot_control(self.yawIn, 'yawIn')

        cmds.parent(xform, parent)
        
        attribute_control = self._get_attribute_control()
        
        final_value = -10
        if self.mirror_yaw and self.side == 'R':
            final_value = 10

        final_other_value = 45
        if self.mirror_yaw and self.side == 'R':
            final_other_value = -45
        
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.side_roll_axis),cd = '%s.yawRoll' % attribute_control, driverValue = 0, value = 0, itt = 'spline', ott = 'spline')
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.side_roll_axis),cd = '%s.yawRoll' % attribute_control, driverValue = final_value, value = final_other_value, itt = 'spline', ott = 'spline')
        
        if self.mirror_yaw and self.side == 'R':
            cmds.setInfinity('%s.rotate%s' % (driver, self.side_roll_axis), postInfinite = 'linear')
        else:
            cmds.setInfinity('%s.rotate%s' % (driver, self.side_roll_axis), preInfinite = 'linear')    
        
                
        return control
    
    def _create_ball_roll(self, parent):
        
        control, xform, driver = self._create_pivot_control(self.ball, 'ball')
        control = util.Control(control)
        control.scale_shape(2,2,2)
        control = control.get()
        
        cmds.parent(xform, parent)
        
        attribute_control = self._get_attribute_control()
        
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.forward_roll_axis),cd = '%s.ballRoll' % attribute_control, driverValue = 0, value = 0, itt = 'spline', ott = 'spline')        
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.forward_roll_axis),cd = '%s.ballRoll' % attribute_control, driverValue = 10, value = 45, itt = 'spline', ott = 'spline')
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.forward_roll_axis),cd = '%s.ballRoll' % attribute_control, driverValue = -10, value = -45, itt = 'spline', ott = 'spline')
        #cmds.setDrivenKeyframe('%s.rotateX' % driver,cd = '%s.ballRoll' % attribute_control, driverValue = 20, value = 0, itt = 'spline', ott = 'spline')
        cmds.setInfinity('%s.rotate%s' % (driver, self.forward_roll_axis), postInfinite = 'linear')
        cmds.setInfinity('%s.rotate%s' % (driver, self.forward_roll_axis), preInfinite = 'linear')
        
        return control
    
    def _create_toe_roll(self, parent):
        
        control, xform, driver = self._create_pivot_control(self.toe, 'toe')
        
        cmds.parent(xform, parent)
        
        attribute_control = self._get_attribute_control()
        
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.forward_roll_axis),cd = '%s.toeRoll' % attribute_control, driverValue = 0, value = 0, itt = 'spline', ott = 'spline' )
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.forward_roll_axis),cd = '%s.toeRoll' % attribute_control, driverValue = 10, value = 45, itt = 'spline', ott = 'spline')
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.forward_roll_axis),cd = '%s.toeRoll' % attribute_control, driverValue = -10, value = -45, itt = 'spline', ott = 'spline')
        
        cmds.setInfinity('%s.rotate%s' % (driver, self.forward_roll_axis), postInfinite = 'linear')
        cmds.setInfinity('%s.rotate%s' % (driver, self.forward_roll_axis), preInfinite = 'linear')
        
        return control
    
    def _create_heel_roll(self, parent):
        control, xform, driver = self._create_pivot_control(self.heel, 'heel')
        
        cmds.parent(xform, parent)
        
        attribute_control = self._get_attribute_control()
        
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.forward_roll_axis),cd = '%s.heelRoll' % attribute_control, driverValue = 0, value = 0, itt = 'spline', ott = 'spline')
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.forward_roll_axis),cd = '%s.heelRoll' % attribute_control, driverValue = -10, value = -45, itt = 'spline', ott = 'spline')
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.forward_roll_axis),cd = '%s.heelRoll' % attribute_control, driverValue = 10, value = 45, itt = 'spline', ott = 'spline')
        cmds.setInfinity('%s.rotate%s' % (driver, self.forward_roll_axis), preInfinite = 'linear')
        cmds.setInfinity('%s.rotate%s' % (driver, self.forward_roll_axis), postInfinite = 'linear')
        
        return control
    
    def _create_pivot(self, name, transform, parent):
        
        pivot_group, pivot_xform = self._create_pivot_group(transform, name)
        cmds.parent(pivot_xform, parent)
        
        return pivot_group
        
    def _create_pivot_groups(self):

        toe_control, toe_control_xform = self._create_toe_rotate_control()
        toe_fk_control, toe_fk_control_xform = self._create_toe_fk_rotate_control()
        
        ball_pivot = self._create_pivot('ball', self.ball, self.control_group)
        toe_pivot = self._create_pivot('toe', self.toe, ball_pivot)
        heel_pivot = self._create_pivot('heel', self.heel, toe_pivot)
        
        toe_roll = self._create_toe_roll(heel_pivot)
        heel_roll = self._create_heel_roll(toe_roll)
        yawout_roll = self._create_yawout_roll(heel_roll)
        yawin_roll = self._create_yawin_roll(yawout_roll)
        ball_roll = self._create_ball_roll(yawin_roll)
        
        self._create_ik()
        
        cmds.parent(toe_control_xform, yawin_roll)
        #cmds.parent(toe_fk_control_xform, self.control_group)
        
        #cmds.parentConstraint(ball_roll, self.roll_control_xform, mo = True)
        if not self.main_control_follow:
            util.create_follow_group(ball_roll, self.roll_control_xform)
        if self.main_control_follow:
            util.create_follow_group(self.main_control_follow, self.roll_control_xform)
        
        cmds.parentConstraint(toe_control, self.ball_handle, mo = True)
        cmds.parentConstraint(ball_roll, self.ankle_handle, mo = True)
        
        
        return [ball_pivot, toe_fk_control_xform]
        
    def set_toe_rotate_as_locator(self, bool_value):
        self.toe_rotate_as_locator = bool_value
          
    def set_mirror_yaw(self, bool_value):
        self.mirror_yaw = bool_value
        
    def set_main_control_follow(self, transform):
        self.main_control_follow = transform
                    
    def create(self):
        super(FootRollRig,self).create()
        
        self._define_joints()
        
        self._create_roll_attributes()
        
        ball_pivot, toe_fk_control_xform = self._create_pivot_groups()
        
        util.connect_equal_condition('%s.%s' % (self.roll_control.get(), self.ik_attribute), '%s.visibility' % toe_fk_control_xform, 1)
        #cmds.connectAttr('%s.%s' % (self.roll_control.get(), self.ik_attribute), '%s.visibility' % toe_fk_control_xform)
        util.connect_equal_condition('%s.%s' % (self.roll_control.get(), self.ik_attribute), '%s.visibility' % ball_pivot, 0)
        #connect_reverse('%s.%s' % (self.roll_control.get(), self.ik_attribute), '%s.visibility' % ball_pivot)
                
#---Face Rig

        
        
class EyeRig(JointRig):
    def __init__(self, description, side):
        super(EyeRig, self).__init__(description, side)
        self.local_parent = None
        self.parent = None
        
        self.eye_control_move = ['Z', 1]
        self.extra_control = False
        self.rotate_value = 25
        self.limit = 1
        self.skip_ik = False
        
    def _create_ik(self):

        duplicate_hierarchy = util.DuplicateHierarchy( self.joints[0] )
        
        duplicate_hierarchy.stop_at(self.joints[-1])
        duplicate_hierarchy.replace('joint', 'ik')
        
        self.ik_chain = duplicate_hierarchy.create()
        
        cmds.parent(self.ik_chain[0], self.setup_group)
        """
        if self.extra_control:
            duplicate_hierarchy = util.DuplicateHierarchy( self.joints[0] )
        
            duplicate_hierarchy.stop_at(self.joints[-1])
            duplicate_hierarchy.replace('joint', 'extra_ik')
            self.extra_ik_chain = duplicate_hierarchy.create()
            cmds.parent(self.extra_ik_chain[0], self.setup_group)
        """
        
        if not self.skip_ik:
            ik = util.IkHandle(self.description)
            ik.set_start_joint(self.ik_chain[0])
            ik.set_end_joint(self.ik_chain[1])
            handle = ik.create()
            
            cmds.parent(handle, self.setup_group)
        
            return handle
    
    def _create_eye_control(self, handle = None):
        
        control = None
        
        if not self.skip_ik:
            group1 = cmds.group(em = True, n = self._get_name('group', 'aim'))
            group2 = cmds.group(em = True, n = self._get_name('group', 'aim'))
            
            cmds.parent(group2, group1)
            cmds.parent(group1, self.setup_group)
            
            util.MatchSpace(self.joints[0], group1).translation_rotation()
            
            xform = util.create_xform_group(group1)
            
            util.connect_rotate(self.ik_chain[0], group1)
            
            if not self.extra_control:
                cmds.orientConstraint(group2, self.joints[0])
            
            control =self._create_control()
            control.hide_scale_attributes()
            control = control.get()
            
            match = util.MatchSpace(self.joints[1], control)
            match.translation_rotation()
            
            cmds.parent(control, self.control_group)
            
            xform = util.create_xform_group(control)
            local_group, local_xform = util.constrain_local(control, handle)
            cmds.parent(local_xform, self.setup_group)

            if self.local_parent:
                cmds.parent(local_xform, self.local_parent)
                
            if self.parent:
                cmds.parent(xform, self.parent)

        if self.skip_ik:
            group1 = cmds.group(em = True, n = self._get_name('group', 'aim'))
            #group2 = cmds.group(em = True, n = self._get_name('group', 'aim'))
            
            #cmds.parent(group2, group1)
            cmds.parent(group1, self.setup_group)
            
            
            
            util.MatchSpace(self.joints[0], group1).translation_rotation()
            
            xform = util.create_xform_group(group1)
            
            cmds.orientConstraint(group1, self.joints[0])
        
        if self.extra_control:
            
            parent_group = cmds.group(em = True, n = util.inc_name(self._get_name('group', 'extra')))
            aim_group = cmds.group(em = True, n = util.inc_name(self._get_name('group', 'aim_extra')))
            
            util.MatchSpace(self.joints[0], aim_group).translation_rotation()
            util.MatchSpace(self.joints[0], parent_group).translation_rotation()
            
            xform_parent_group = util.create_xform_group(parent_group)
            xform_aim_group = util.create_xform_group(aim_group)
            
            cmds.parent(xform_aim_group, group1)
            
            util.connect_rotate(group1, parent_group)
            #cmds.orientConstraint(group2, parent_group, mo = True)
            cmds.parent(xform_parent_group, self.setup_group)
            
            #util.connect_rotate(aim_group, self.joints[0])
            cmds.orientConstraint(aim_group, self.joints[0])
            
            control2 = self._create_control(sub = True)
            control2.hide_scale_and_visibility_attributes()
            control2 = control2.get()
        
            match = util.MatchSpace(self.joints[0], control2)
            match.translation_rotation()
        
            axis = self.eye_control_move[0]
            axis_value = self.eye_control_move[1]
                        
            if axis == 'X':
                cmds.move(axis_value, 0,0 , control2, os = True, relative = True)
                util.connect_multiply('%s.translateZ' % control2, '%s.rotateY' % aim_group, -self.rotate_value )
                util.connect_multiply('%s.translateY' % control2, '%s.rotateZ' % aim_group, self.rotate_value )
            if axis == 'Y':
                cmds.move(0,axis_value, 0, control2, os = True, relative = True)
                util.connect_multiply('%s.translateZ' % control2, '%s.rotateX' % aim_group, -self.rotate_value )
                util.connect_multiply('%s.translateY' % control2, '%s.rotateZ' % aim_group, self.rotate_value )
            if axis == 'Z':
                cmds.move(0,0,axis_value, control2, os = True, relative = True)
                util.connect_multiply('%s.translateX' % control2, '%s.rotateY' % aim_group, self.rotate_value )
                util.connect_multiply('%s.translateY' % control2, '%s.rotateX' % aim_group, -self.rotate_value )
            
            xform2 = util.create_xform_group(control2)            
            cmds.parent(xform2, parent_group)
            cmds.parent(xform_parent_group, self.control_group)
            
            
            
            if axis == 'X':
                cmds.transformLimits(control2,  tx =  (0, 0), etx = (1,1) )
            if axis == 'Y':
                cmds.transformLimits(control2,  ty =  (0, 0), ety = (1,1) )
            if axis == 'Z':
                cmds.transformLimits(control2,  tz =  (0, 0), etz = (1,1) )
            
        return control
    
    def set_parent(self, parent):
        self.parent = parent
    
    def set_local_parent(self, local_parent):
        self.local_parent = local_parent 
    
    def set_extra_control(self, axis, value, rotate_value = 25, limit = 1):
        
        self.eye_control_move = [axis, value]
        self.extra_control = True
        self.rotate_value = rotate_value
    
    def set_skip_ik_control(self, bool_value):
        self.skip_ik = bool_value
        
    
    def create(self):
        
        handle = None
        
        if not self.skip_ik:
            handle = self._create_ik()
        
        control = self._create_eye_control(handle)
        
        if self.skip_ik:
            return
        
        locator = cmds.spaceLocator(n = 'locator_%s' % self._get_name())[0]
        
        
        
        match = util.MatchSpace(self.joints[0], locator)
        match.translation_rotation()
        
        cmds.parent(locator, self.control_group)
        
        line = util.RiggedLine(locator, control, self._get_name())        
        cmds.parent( line.create(), self.control_group)
        
        
        cmds.setAttr('%s.translateX' % locator, l = True)
        cmds.setAttr('%s.translateY' % locator, l = True)
        cmds.setAttr('%s.translateZ' % locator, l = True)
        cmds.setAttr('%s.rotateX' % locator, l = True)
        cmds.setAttr('%s.rotateY' % locator, l = True)
        cmds.setAttr('%s.rotateZ' % locator, l = True)
        cmds.hide(locator)
        
class JawRig(FkLocalRig):
    def __init__(self, description, side):
        super(JawRig, self).__init__(description, side)
        self.jaw_slide_offset = .1
        self.jaw_slide_attribute = True
    
    def _attach(self, source_transform, target_transform):
        
        local_group, local_xform = super(JawRig, self)._attach(source_transform, target_transform)
        
        control = self.controls[-1]
                
        live_control = util.Control(control)
        live_control.rotate_shape(0, 0, 90)
        
        
        var = util.MayaNumberVariable('autoSlide')
        var.set_variable_type(var.TYPE_DOUBLE)
        var.set_value(self.jaw_slide_offset)
        var.set_keyable(self.jaw_slide_attribute)
        var.create(control)
        
        driver = util.create_xform_group(control, 'driver')
        driver_local = util.create_xform_group(local_group, 'driver')
        
        multi = util.connect_multiply('%s.rotateX' % control, '%s.translateZ' % driver)
        cmds.connectAttr('%s.outputX' % multi, '%s.translateZ' % driver_local)
        var.connect_out('%s.input2X' % multi)
        
        return local_group, local_xform  
    
    def set_jaw_slide_offset(self, value):
        self.jaw_slide_offset = value
        
    def set_create_jaw_slide_attribute(self, bool_value):
        self.jaw_slide_attribute = bool_value
        
