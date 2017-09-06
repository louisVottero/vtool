# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

import string
import random

#import util
import api
import vtool.util
from vtool.maya_lib.space import get_xform_group

if vtool.util.is_in_maya():
    import maya.cmds as cmds
    
import core
import attr
import space
import anim
import curve
import geo
import deform
import rigs_util
import fx
    

#--- rigs

class Rig(object):
    
    "Base class for rigs."
    
    side_left = 'L'
    side_right = 'R'
    side_center = 'C'
    
    def __init__(self, description, side = None):
        
        cmds.refresh()
        
        self.description = description
        self.side = side
        
        self.control_parent = None
        self.setup_parent = None
        
        self._create_default_groups()
        self._delete_setup = False
        
        self.control_shape = 'circle'
        self.sub_control_shape = None
        
        self.control_color = None
        self.sub_control_color = None
        
        self.control_size = 1
        self.sub_control_size = 0.8
        self.control_offset_axis = None
        
        self.controls = []
        self.sub_controls = []
        self.control_dict = {}
        
        self.sub_visibility = False
        self._connect_sub_vis_attr = None
        
    def __del__(self):
        
        if cmds.objExists(self.setup_group):
            
            if core.is_empty(self.setup_group):
                parent = cmds.listRelatives(self.setup_group, p = True)
                
                if not parent:
                    
                    class_name = self.__class__.__name__
                    
                    vtool.util.warning('Empyt setup group in class: %s with description %s %s.' % (class_name, self.description, self.side))
    
    
    def _create_group(self,  prefix = None, description = None):
        
        rig_group_name = self._get_name(prefix, description)
        
        group = cmds.group(em = True, n = core.inc_name(rig_group_name))
        
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
        
        if not group or not custom_parent:
            return
        
        if not cmds.objExists(group):
            return
        if not cmds.objExists(custom_parent):
            vtool.util.warning('%s does not exist to be a parent.' % custom_parent)
            return
        
        parent = cmds.listRelatives(group, p = True)
        if parent:
            if custom_parent == parent[0]:
                return
        
        try:    
            
            cmds.parent(group, custom_parent)
        except:
            pass
        
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
        
        if self.side:
            name_list = [prefix,self.description, description, '1', self.side]
        if not self.side:
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
        
        control_name = core.inc_name(control_name)
        
        return control_name
        
    def _create_control(self, description = None, sub = False, curve_type = None):
        
        control = rigs_util.Control( self._get_control_name(description, sub) )
        
        if curve_type:
            control.set_curve_type(curve_type)
        
        side = self.side
        
        if not side:
            side = 'C'
        
        control.color( attr.get_color_of_side( side , sub)  )
        
        if self.control_color >=0 and not sub:
            control.color( self.control_color )
            
        if self.sub_control_color >= 0 and sub:
            
            control.color( self.sub_control_color )
            
        control.hide_visibility_attribute()
        
        if self.control_shape and not curve_type:
            
            control.set_curve_type(self.control_shape)
            
            if sub:
                if self.sub_control_shape:
                    control.set_curve_type(self.sub_control_shape)
            
        
        if not sub:
            
            control.scale_shape(self.control_size, 
                                self.control_size, 
                                self.control_size)
            
        if sub:
            
            size = self.control_size * self.sub_control_size
            
            control.scale_shape(size, 
                                size, 
                                size)
        
        if not sub:
            self.controls.append(control.get())
        
        if sub:
            self.sub_controls.append(control.get())
        
        if self.control_offset_axis:
            
            if self.control_offset_axis == 'x':
                control.rotate_shape(90, 0, 0)
                
            if self.control_offset_axis == 'y':
                control.rotate_shape(0, 90, 0)
                
            if self.control_offset_axis == 'z':
                control.rotate_shape(0, 0, 90)
                
            if self.control_offset_axis == '-x':
                control.rotate_shape(-90, 0, 0)
                
            if self.control_offset_axis == '-y':
                control.rotate_shape(0, -90, 0)
                
            if self.control_offset_axis == '-z':
                control.rotate_shape(0, 0, -90)
                
        self.control_dict[control.get()] = {}
        
        return control
    
    def _connect_sub_visibility(self, control_and_attr, sub_control):
        
        shapes = cmds.listRelatives(sub_control, shapes = True)
            
        for shape in shapes:
            
            attr.connect_visibility(control_and_attr, shape, self.sub_visibility)
            
            if self._connect_sub_vis_attr:
                
                if not cmds.objExists(self._connect_sub_vis_attr):
                    node = core.get_basename(self._connect_sub_vis_attr, remove_attribute = True)
                    attribute = attr.get_attribute_name(self._connect_sub_vis_attr)
                    
                    cmds.addAttr(node, ln = attribute, at = 'bool', k = True, dv = self.sub_visibility)
                
                if not attr.is_connected(control_and_attr):
                    cmds.connectAttr(self._connect_sub_vis_attr, control_and_attr)
                
    
    def set_control_shape(self, shape_name):
        """
        Sets the look of the controls, based on predifined names.
        """
        
        self.control_shape = shape_name
        
    def set_sub_control_shape(self, shape_name):
        """
        Sets the look of the curve for the sub controls.
        
        """
        
        self.sub_control_shape = shape_name
    
    def set_control_color(self, color):
        """
        Set the color of the control based on an integer value. 
        """
        
        self.control_color = color
        
    def set_sub_control_color(self, color):
        """
        Set the color of sub controls.
        """
        
        self.sub_control_color = color
        
    def set_control_size(self, float_value):
        """
        Sets the default size of the control curve.
        """
        
        self.control_size = float_value
        
    def set_sub_control_size(self, float_value):
        """
        Sets the default size of the sub control curve.
        """
        
        self.sub_control_size = float_value
        
    
                
    def set_control_parent(self, parent_transform):
        """
        Sets the parent of the control group for this rig.
        This usually should get run after create.
        """
        
        self.control_parent = parent_transform
        
        self._parent_custom_default_group(self.control_group, self.control_parent)
        
    def set_setup_parent(self, parent_transform):
        """
        Sets the parent of the setup group for this rig.
        This usually should get run after create.
        """
        
        
        self.setup_parent = parent_transform
        
        self._parent_custom_default_group(self.setup_group, self.setup_parent)
        
    def set_control_offset_axis(self, axis_letter):
        """
        This sets the axis that the control curve cvs will offset to. This happens by rotating the control in 90 degrees on the axi.
        This is good for lining up the control cvs to a different axis than its default. 
        
        Args:
            axis_letter (str): The letter of the axis to offste the control cvs around. 'x', 'y' or 'z'
        
        """
        self.control_offset_axis = axis_letter.lower()
        
    def set_sub_visibility(self, bool_value):
        """
        This controls wether sub controls are visible by default after building the rig.
        
        Args:
            bool_value (bool)
        """
        self.sub_visibility = bool_value
    
    def connect_sub_visibility(self, attr_name):
        """
        This connects the subVisibility attribute to the specified attribute.  Good when centralizing the sub control visibility. 
        """
        self._connect_sub_vis_attr = attr_name
    
    def get_controls(self, title):
        """
        Get entries for every control. 
        For example, title could be "xform".  It would return all the xform nodes.
        """
        
        entries = []
        
        for control in self.controls:
            if self.control_dict[control].has_key(title):
                entries.append(self.control_dict[control][title])
        
        return entries
        
    def get_sub_controls(self, title):
        """
        Get entries for every sub control. 
        For example, title could be "xform".  It would return all the xform nodes.
        """
        
        
        entries = []
        
        for control in self.sub_controls:
            if self.control_dict[control].has_key(title):
                entries.append(self.control_dict[control][title])
        
        return entries
        
    def create(self):
        """
        Create the rig.  Set commands must be set before running this.
        """
        
        vtool.util.show('Creating rig: %s, description: %s, side: %s' % (self.__class__.__name__, self.description, self.side))
        self._parent_default_groups()
        if self._delete_setup:
            self.delete_setup()
        
    def delete_setup(self):
        
        
        
        if cmds.objExists(self.setup_group):
        
            if core.is_empty(self.setup_group):
                parent = cmds.listRelatives(self.setup_group, p = True)
                
                if parent:
                    vtool.util.warning('Setup group was parented. Skipping deletion.')
                
                if not parent:
                    cmds.delete(self.setup_group)
                    return
            if core.is_empty(self.setup_group) and self._delete_setup:
                    vtool.util.warning('Setup group is not empty. Skipping deletion.')
        
        if not cmds.objExists(self.setup_group) and self._delete_setup:
            vtool.util.warning('Setup group does not exist. Skipping deletion.')
        
        if self._delete_setup:
            vtool.util.warning('Could not delete setup group. rig: %s side: %s of class: %s' % (self.description, self.side, self.__class__.__name__ ))
        
        self._delete_setup = True
        
class JointRig(Rig):
    """
    Joint rig class adds attaching buffer chain functionality.
    Also the ability to specify a joint chain for a rig.
    
    """
    
    def __init__(self, description, side=None):
        super(JointRig, self).__init__(description, side)
        
        self.joints = []
        
        self.attach_joints = True
        self.auto_control_visibility = True
        
    def _attach_joints(self, source_chain, target_chain):
        
        if not self.attach_joints:
            return
        
        space.AttachJoints(source_chain, target_chain).create()
        
        if cmds.objExists('%s.switch' % target_chain[0]):
            switch = rigs_util.RigSwitch(target_chain[0])
            
            weight_count = switch.get_weight_count()
            
            if weight_count > 0:
                if self.auto_control_visibility:
                    switch.add_groups_to_index((weight_count-1), self.control_group)
                switch.create()
                
        
        
    
    def _check_joints(self, joints):
        
        for joint in joints:
            if cmds.nodeType(joint) == 'joint':
                continue
            
            if cmds.nodeType(joint) == 'transform':
                continue
            
            vtool.util.show('%s is not a joint or transform. %s may not build properly.' % (joint, self.__class__.__name__))        
    
    def set_joints(self, joints):
        """
        Set the joints that the rig should work on.
        
        Args:
            joints (list): Joints by name.
        """
        
        
        if type(joints) != list:
            self.joints = [joints]
            
            self._check_joints(self.joints)
            
            return
        
        self.joints = joints
        
        self._check_joints(self.joints)

    def set_attach_joints(self, bool_value):
        """
        Turn off/on joint attaching.
        
        Args:
            bool_value (bool): Wether to attach joints.
        """
        
        self.attach_joints = bool_value
        
    def set_auto_switch_visibility(self, bool_value):
        """
        When attaching more than one joint chain. 
        This will attach the control group visibility to the switch attribute on the first joint. 
        """

        self.auto_control_visibility = bool_value
        
class BufferRig(JointRig):
    """
    Extends JointRig with ability to create buffer chains.
    The buffer chain creates a duplicate chain for attaching the setup to the main chain.
    This allows multiple rigs to be attached to the main chain.
    """
    
    
    def __init__(self, name, side=None):
        super(BufferRig, self).__init__(name, side)
        
        self.create_buffer_joints = False
        self.build_hierarchy = False
    
    def _duplicate_joints(self):
        
        if self.create_buffer_joints:
            if not self.build_hierarchy:
            
                duplicate_hierarchy = space.DuplicateHierarchy( self.joints[0] )
                
                duplicate_hierarchy.stop_at(self.joints[-1])
                duplicate_hierarchy.only_these(self.joints)
                duplicate_hierarchy.replace('joint', 'buffer')
                
                self.buffer_joints = duplicate_hierarchy.create()
                
            if self.build_hierarchy:
                
                build_hierarchy = space.BuildHierarchy()
                build_hierarchy.set_transforms(self.joints)
                build_hierarchy.set_replace('joint', 'buffer')
                self.buffer_joints = build_hierarchy.create()
    
            cmds.parent(self.buffer_joints[0], self.setup_group)

        if not self.create_buffer_joints:
            self.buffer_joints = self.joints
        
        return self.buffer_joints
    
    def _create_before_attach_joints(self):
        return
    
    def set_build_hierarchy(self, bool_value):
        
        self.build_hierarchy = bool_value
    
    def set_buffer(self, bool_value):
        """
        Turn off/on the creation of a buffer chain.  
        
        Args:
            bool_value (bool): Wehter to create the buffer chain.
        """
        
        self.create_buffer_joints = bool_value
    
    def create(self):
        super(BufferRig, self).create()
        
        self._duplicate_joints()
        
        self._create_before_attach_joints()
        
        if self.create_buffer_joints:
            self._attach_joints(self.buffer_joints, self.joints)
        
    def delete_setup(self):
        
        if self.create_buffer_joints:
            vtool.util.warning('Skipping setup group deletion. The buffer is set to True and duplicate joints need to be stored under the setup.')
            return
        
        super(BufferRig, self).delete_setup()
        

class CurveRig(Rig):
    """
        A rig class that accepts curves instead of joints as the base structure.
    """
    
    def __init__(self, description, side=None):
        super(CurveRig, self).__init__(description, side)
        
        self.curves = None
    
    def set_curve(self, curve_list):
        """
        Set the curve to rig with.
        
        Args:
            curve_list (str): The name of a curve.
        """
        self.curves = vtool.util.convert_to_sequence(curve_list)

class PolyPlaneRig(Rig):
    """
        A rig class that accepts curves instead of joints as the base structure.
    """
    
    def __init__(self, description, side=None):
        super(PolyPlaneRig, self).__init__(description, side)
        
        self.poly_plane = None
    
    def set_poly_plane(self, poly_plane):
        """
        Set the curve to rig with.
        
        Args:
            curve_list (str): The name of a curve.
        """
        self.poly_plane = poly_plane

class SurfaceRig(Rig):
    """
        A rig class that accepts curves instead of joints as the base structure.
    """
    
    def __init__(self, description, side=None):
        super(SurfaceRig, self).__init__(description, side)
        
        self.curves = None
    
    def set_surface(self, surface_list):
        """
        Set the curve to rig with.
        
        Args:
            curve_list (str): The name of a curve.
        """
        self.surfaces = vtool.util.convert_to_sequence(surface_list)


#--- Rigs

class SparseRig(JointRig):
    """
    This class create controls on joints. The controls are not interconnected.
    For example Fk rig, the controls have a parent/child hierarchy. Sparse rig does not have any hierarchy.
    This is good for a pile of leaves or tweakers on a body.
    """
    
    def __init__(self, description, side = None):
        super(SparseRig, self).__init__(description, side)
        
        self.control_shape = 'cube'
        self.is_scalable = False
        self.respect_side = False
        self.respect_side_tolerance = 0.001
        self.match_scale = False
        
        self.use_joint_controls = False
        self.use_joint_controls_scale_compensate = False
        
        self.xform_rotate = None
        self.xform_scale = None
        
        self.control_to_pivot = False
        self.follow_parent = False
        self.control_compensate = False
        self.run_function = None
        
    def _convert_to_joints(self):
        
        for inc in range(0, len(self.controls)):
            
            control = self.controls[inc]
            
            control = rigs_util.Control(control)
            control.set_to_joint(scale_compensate= self.use_joint_controls_scale_compensate)
        
    
        
    def set_scalable(self, bool_value):
        """
        Turn off/on the ability for controls to scale the joints.
        
        Args:
            bool_value (bool): Wether to open the scale attributes of the controls.
        """
        
        self.is_scalable = bool_value
        
    def set_respect_side(self, bool_value, tolerance = 0.001):
        """
        Respecting side will change the color of controls based on their position along the X coordinate.
        Less than x will be red. Greater than x will be blue.
        Inside the center axis will be yellow.
        This will also change the naming of the control. 
        The end suffix letter will change to L, R or C depending on where it is in space.
        
        Args:
            bool_value (bool): Wether to have the control respect side by changing name and color.
            tolerance (float): The value a control needs to be away from the center before it has a side.
        """
        
        self.respect_side = bool_value
        self.respect_side_tolerance = tolerance
    
    def set_match_scale(self, bool_value):
        """
        Match the size of the control to the scale of the joint.
        
        Args:
            bool_value (bool): Wether to match the control to the scale of the joint.
        """
        
        self.match_scale = bool_value

    def set_use_joint_controls(self, bool_value, scale_compensate = False):
        
        self.use_joint_controls = bool_value
        self.use_joint_controls_scale_compensate = scale_compensate
        
    def set_xform_values(self, rotate = [0,180, 0], scale = [1,1,-1]):
        """
        This is good for mirroring control behavior
        """
        
        self.xform_rotate = rotate
        self.xform_scale = scale
        
    def set_control_to_pivot(self, bool_value):
        """
        This will build the control at the pivot point of the joint or transform supplied with set_joints()
        """
        self.control_to_pivot = bool_value
        
    def set_follow_parent(self, bool_value):
        
        self.follow_parent = bool_value
        
    def set_control_compensate(self, bool_value):
        """
        This feeds the translation of the control into a group above using a negative offset.
        Good if the control is attached to a mesh that it affects usings a rivet.
        """
        self.control_compensate = bool_value
        
    def set_run_after_increment(self, function):
        """
        function will get passed the current control and current transform.
        """
        
        self.run_function = function
        
    def create(self):
        
        super(SparseRig, self).create()
        
        inc = 0
        self.current_inc = 0
        
        for joint in self.joints:
            
            control = self._create_control()
        
            control_name = control.get()
        
            
            xform = space.create_xform_group(control.get())
            driver = space.create_xform_group(control.get(), 'driver')
            
            if self.control_compensate:
                offset = space.create_xform_group(control_name, 'offset')
                
                attr.connect_translate_multiply(control_name, offset, -1)
            
            match = space.MatchSpace(joint, xform)
                
            if not self.control_to_pivot:    
                match.translation_rotation()
            if self.control_to_pivot:    
                match.translation_to_rotate_pivot()
            
            match.scale()
            
            if self.respect_side:
                side = control.color_respect_side(center_tolerance = self.respect_side_tolerance)
            
                if side != 'C':
                    
                    control_data = self.control_dict[control_name]
                    self.control_dict.pop(control_name)
                    
                    if control_name[-1].isalpha():
                        control_name = cmds.rename(control_name, core.inc_name( control_name[0:-1] + side) )
                    else:
                        control_name = cmds.rename(control_name, core.inc_name( control_name + '1_' + side) )
                        
                    control = rigs_util.Control(control_name)
                    
                    self.control_dict[control_name] = control_data
                    
                    self.controls[-1] = control_name
                    
            
            
            if self.match_scale:
                const = cmds.scaleConstraint(joint, xform)
                cmds.delete(const)
            
            if self.attach_joints:
                cmds.parentConstraint(control_name, joint)

            if self.is_scalable:
                scale_constraint = cmds.scaleConstraint(control.get(), joint)[0]
                space.scale_constraint_to_local(scale_constraint)
            if not self.is_scalable:
                control.hide_scale_attributes()
            
            cmds.parent(xform, self.control_group)
            
            self.control_dict[control_name]['xform'] = xform
            self.control_dict[control_name]['driver'] = driver
            
            if self.follow_parent:
                parent = cmds.listRelatives(joint, p = True)
                
                if parent:
                    space.create_follow_group(parent[0], xform)

            if self.run_function:
                self.run_function(self.controls[self.current_inc], self.joints[self.current_inc])    
            
            inc += 1
            self.current_inc = inc
                        
        if self.use_joint_controls:
            self._convert_to_joints()


class SparseLocalRig(SparseRig):
    """
    A sparse rig that does that connects controls locally.
    This is important for cases where the controls when parented need to move serparetly from the rig.
    For example if the setup deformation blendshapes in before a skin cluster.
    """
    def __init__(self, description, side = None):
        super(SparseLocalRig, self).__init__(description, side)
        
        self.local_constraint = True
        self.local_parent = None
        self.local_xform = None
        self.connect_xform = False
        self._read_locators = False

    def _create_read_locators(self):
            
        if not self._read_locators:
            return
        
        group = cmds.group(em = True, n = core.inc_name(self._get_name('group', 'read_locator')))
        cmds.parent(group, self.setup_group)
        
        for joint in self.joints:
            loc = cmds.spaceLocator(n = core.inc_name(self._get_name('locator', 'read')))[0]
            
            cmds.pointConstraint(joint, loc)
            
            xform = space.create_xform_group(loc)
            
            cmds.parent(xform, group)

    def set_local_constraint(self, bool_value):
        self.local_constraint = bool_value
        
    def set_local_parent(self, local_parent):
        self.local_parent = local_parent
        
    def set_connect_local_xform(self, bool_value):
        
        self.connect_xform = bool_value

    def set_create_position_read_locators(self, bool_value):
        """
        Good to hookup of blendshapes to the translation.
        """
        
        self._read_locators = bool_value

    def create(self):
        
        super(SparseRig, self).create()
        
        if self._read_locators:
            self._create_read_locators()
        
        
        self.local_xform = cmds.group(em = True, n = 'localParent_%s' % self._get_name())
        cmds.parent(self.local_xform, self.setup_group)
        
        self.current_inc = 0
        inc = 0
        
        for joint in self.joints:
            
            control = self._create_control()
            
            control_name = control.get()
            
            xform = space.create_xform_group(control.get())
            driver = space.create_xform_group(control.get(), 'driver')

            if self.control_compensate:
                offset = space.create_xform_group(control_name, 'offset')
            
                attr.connect_translate_multiply(control_name, offset, -1)
            
            match = space.MatchSpace(joint, xform)
            
            if not self.control_to_pivot:
                
                match.translation_rotation()
            if self.control_to_pivot:    
                match.translation_to_rotate_pivot()
            
            match.scale()
            
            if self.respect_side:
                side = control.color_respect_side(center_tolerance = self.respect_side_tolerance)
            
                if side != 'C':
                    
                    control_data = self.control_dict[control_name]
                    self.control_dict.pop(control_name)
                    
                    if control_name[-1].isalpha():
                        control_name = cmds.rename(control_name, core.inc_name( control_name[0:-1] + side) )
                    else:
                        control_name = cmds.rename(control_name, core.inc_name( control_name[0:-1] + '1_' + side) )
                    
                    self.control_dict[control_name] = control_data
                    
                    control = rigs_util.Control(control_name)
                    
                    self.controls[-1] = control_name
                    
            if not self.local_constraint:
                if not self.attach_joints:
                    xform_joint = space.create_xform_group(joint)
                    
                    if self.local_parent:
                        cmds.parent(xform_joint, self.local_xform)
                    
                    attr.connect_translate(control.get(), joint)
                    attr.connect_rotate(control.get(), joint)
                    
                    attr.connect_translate(driver, joint)
                    attr.connect_rotate(driver, joint)
            
            if self.local_constraint:
                if self.attach_joints:
                    local_group, local_xform = space.constrain_local(control.get(), joint, use_duplicate = True, scale_connect = self.is_scalable)
                
                    if self.local_xform:
                        cmds.parent(local_xform, self.local_xform)
                    
                    local_driver = space.create_xform_group(local_group, 'driver')
                    
                    attr.connect_translate(driver, local_driver)
                    attr.connect_rotate(driver, local_driver)
                    attr.connect_scale(driver, local_driver)
                
                
                    if self.connect_xform:
                        attr.connect_transforms(xform, local_xform)
                
                    if not self.local_xform:
                        cmds.parent(local_xform, self.setup_group)
                
            if not self.attach_joints:
                attr.connect_scale(control.get(), joint)
            
            cmds.parent(xform, self.control_group)

            if self.run_function:
                self.run_function(self.controls[self.current_inc], self.joints[self.current_inc])
                    
            self.current_inc = inc
            inc += 1

            
        if self.local_parent:
            space.create_follow_group(self.local_parent, self.local_xform)
            
        self.control_dict[control_name]['xform'] = xform
        self.control_dict[control_name]['driver'] = driver
        
        if self.use_joint_controls:
            self._convert_to_joints()
            

            
            
class ControlRig(Rig):
    """
    Convenience for creating controls to hold blendshape sliders.
    """
    def __init__(self, name, side=None):
        super(ControlRig, self).__init__(name,side)
        
        self.transforms = None
        self.control_count = 1
        self.control_shape_types = {}
        self.control_descriptions = {}
        self.only_translate = False
        self.no_channels = False
    
    def set_transforms(self, transforms):
        """
        Set transforms where controls should be created.
        """
        self.transforms = transforms
        
    def set_control_count_per_transform(self, int_value):
        """
        Set the number of controls per transform.
        """
        self.control_count = int_value
    
    def set_control_shape(self, index, shape_name):
        """
        Set the control shape at the index. 
        Corresponds to set_control_count_per_transform.
        """
        self.control_shape_types[index] = shape_name
    
    def set_control_description(self, index, description):
        """
        Set the description of the control at the index.
        Corresponds to set_control_count_per_transform.
        """
        self.control_descriptions[index] = description
    
    def set_only_translate_channels(self, bool_value):
        self.only_translate = bool_value
        
    def set_no_channels(self, bool_value):
        self.no_channels = bool_value
    
    def create(self):
        
        if not self.transforms:
            self.transforms = [None]
        
        self.transforms = vtool.util.convert_to_sequence(self.transforms)
        
        for transform in self.transforms:
            for inc in range(0, self.control_count):
                
                description = None
                if inc in self.control_descriptions:
                    description = self.control_descriptions[inc]
                
                control = self._create_control(description)
                
                if transform:
                    space.MatchSpace(transform, control.get()).translation_rotation()
                
                if inc in self.control_shape_types:
                    control.set_curve_type(self.control_shape_types[inc])
                
                control.scale_shape(self.control_size, self.control_size, self.control_size)
                
                xform = space.create_xform_group(control.get())    
                cmds.parent(xform, self.control_group)     
                
                if self.only_translate:
                    control.hide_scale_attributes()
                    control.hide_rotate_attributes()
                    
                if self.no_channels:
                    control.hide_attributes()           
                
class GroundRig(JointRig):
    """
    Create a ground and sub controls
    """
    def __init__(self, name, side=None):
        super(GroundRig, self).__init__(name, side)
        
        self.control_shape = 'square_point'
        self.control_size = 1
        self.sub_control_size = .9
        self.scalable = False

    def set_joints(self, joints = None):
        super(GroundRig, self).set_joints(joints)
        
    def set_control_size(self, float_value):
        super(GroundRig, self).set_control_size(float_value * 40)
    
    def set_scalable(self, bool_value):
        self.scalable = bool_value
    
    def create(self):
        
        super(GroundRig, self).create()
        
        
        scale = self.sub_control_size
        last_control = None
        
        controls = []
        
        first_control = None
        
        for inc in range(0, 3):
            
            if inc == 0:
                control = self._create_control()
                
                cmds.parent(control.get(), self.control_group)
                
                first_control = control.get()
                
            if inc > 0:
                control = self._create_control(sub =  True)

                self._connect_sub_visibility('%s.subVisibility' % first_control, control.get())
                    
                
                
            controls.append(control.get())
            
            if inc > 1:
                control.scale_shape(scale, scale, scale)
                scale*=0.9   
            
            if last_control:
                cmds.parent(control.get(), last_control)
            
            last_control = control.get()
            
            
            if not self.scalable:
                control.hide_scale_and_visibility_attributes()
            if self.scalable:
                control.hide_visibility_attribute()
                
        
        if self.joints and self.description != 'ground':
            xform = space.create_xform_group(controls[0])
            space.MatchSpace(self.joints[0], xform).translation_rotation()
        
        if self.joints:   
            if self.attach_joints:
                cmds.parentConstraint(control.get(), self.joints[0])
                if self.scalable:
                    cmds.scaleConstraint(control.get(), self.joints[0])
        

#--- FK

class FkRig(BufferRig):
    """
    This is a great simple setup for appendages like fingers or arms.
    """
    
    def __init__(self, name, side=None):
        super(FkRig, self).__init__(name, side)
        self.last_control = ''
        self.control = ''
        
        self.current_xform_group = ''
        self.control_size = 3
        self.sub_control_size = .9
        
        self.transform_list = []
        self.drivers = []
        self.current_increment = None
        
        self.parent = None
        
        self.connect_to_driver = None
        self.match_to_rotation = True
        
        self.create_sub_controls = False
        self.nice_sub_naming = False
        self.use_joint_controls = False
        self.use_joint_controls_scale_compensate = False
        
        self.hide_sub_translates = True

        self.skip_controls = []
        self.offset_rotation = []
        self.inc_offset_rotation = {}
        

    def _create_control(self, sub = False):
        
        control = super(FkRig, self)._create_control(sub = sub)
        
        if not sub:
            self.last_control = self.control
            self.control = control
        
        if len(self.controls) == 1:
            cmds.parent(control.get(), self.control_group)
        
        self._set_control_attributes(control)
                
        xform = space.create_xform_group(control.get())
        driver = space.create_xform_group(control.get(), 'driver')
        
        if not sub:
            self.current_xform_group = xform
            
        self.control_dict[control.get()]['xform'] = xform
        self.control_dict[control.get()]['driver'] = driver
        
        if not sub:
            self.drivers.append(driver)
        
        if self.create_sub_controls and not sub:
            
            subs = []
            
            for inc in range(0,2):

                if inc == 0:
                    sub_control = super(FkRig, self)._create_control(sub =  True, curve_type = self.sub_control_shape)
                    
                if inc == 1:
                    if not self.nice_sub_naming:
                        sub_control = super(FkRig, self)._create_control(description = 'sub', sub =  True, curve_type = self.sub_control_shape)
                    if self.nice_sub_naming:
                        sub_control = super(FkRig, self)._create_control( sub =  True)
                        
                    sub_control.scale_shape(0.9, 0.9, 0.9)
                
                if self.hide_sub_translates:
                    sub_control.hide_translate_attributes()
                    
                sub_control.hide_scale_and_visibility_attributes()
                
                space.MatchSpace(control.get(), sub_control.get()).translation_rotation()
                
                self._connect_sub_visibility('%s.subVisibility' % control.get(), sub_control.get())
                
                subs.append(sub_control.get())
                
                if inc == 0:
                    cmds.parent(sub_control.get(), control.get())
                if inc == 1:
                    cmds.parent(sub_control.get(), self.sub_controls[-2])
                
            self.control_dict[control.get()]['subs'] = subs
                
        return control
    
    def _set_control_attributes(self, control):
        
        control.hide_scale_attributes()
    
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
        
        match = space.MatchSpace(current_transform, self.control_dict[control]['xform'])
        
        if self.match_to_rotation:
            match.translation_rotation()
            
        if not self.match_to_rotation:
            match.translation()
            
        match.scale()
        
            
    def _first_increment(self, control, current_transform):
        
        self._attach(control, current_transform)
    
    def _last_increment(self, control, current_transform):
        return
    
    def _increment_greater_than_zero(self, control, current_transform):
        
        self._attach(control, current_transform)
        
        if not self.create_sub_controls:
            
            if self.last_control:
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
        
        found_to_skip = []
        
        if self.skip_controls:
            for increment in self.skip_controls:
                
                found_transform = None
                
                try:
                    found_transform = transforms[increment]
                except:
                    pass
                
                if found_transform:
                    found_to_skip.append(found_transform)
        
        self.current_increment = 0
        
        for inc in range(0, len(transforms)):
            
            if transforms[inc] in found_to_skip:
                self.current_increment += 1
                continue
            
            self.current_increment = inc
            
            control = self._create_control()
            control = control.get()
            
            self._edit_at_increment(control, transforms)
            
            
    def _attach(self, control, target_transform):
        
        if not self.attach_joints:
            return
        
        if self.create_sub_controls:
            control = self.control_dict[control]['subs'][-1]
        
        xform = None
        
        if self.control_dict[control].has_key('xform'):
            xform = self.control_dict[control]['xform']
        
        if xform:
            if self.offset_rotation:
                
                cmds.xform(xform, ro = self.offset_rotation, r = True, os = True)
                
            if self.current_increment in self.inc_offset_rotation:
                offset_rotation = self.inc_offset_rotation[self.current_increment]
                cmds.xform(xform,  ro = offset_rotation, r = True, os = True )
        
        cmds.parentConstraint(control, target_transform, mo = True)
        
    def _convert_to_joints(self):
        for inc in range(0, len(self.controls)):
            
            control = self.controls[inc]
            
            control = rigs_util.Control(control)
            control.set_to_joint(scale_compensate= self.use_joint_controls_scale_compensate)
                
    def set_parent(self, parent):
        #CBB this needs to be replaced with self.set_control_parent
        
        self.parent = parent
        
    def set_match_to_rotation(self, bool_value):
        """
        Wether to match control to closest joint orientation or not. If not just match to translate. Control stays oriented to world.
        Default is True.   This is only used in Fk rigs not FkCurve rigs.
        """
        self.match_to_rotation = bool_value
    
    def get_drivers(self):
        """
        Get the driver groups above the controls.
        """
        
        drivers = self.get_control_entries('driver')
            
        return drivers
    
    def set_use_joint_controls(self, bool_value, scale_compensate = False):
        """
        Wether to make the controls have a joint as their base transform node.
        """
        self.use_joint_controls = bool_value
        self.use_joint_controls_scale_compensate = scale_compensate
    
    def set_create_sub_controls(self, bool_value):
        """
        Wether each fk control should have sub controls.
        """
        self.create_sub_controls = bool_value
        
    def set_skip_controls(self, increment_list):
        """
        Set which increments are skipped. 
        
        Args:
            increment_list (list): A list of integers. [0] will skip the first increment, [0,1] will skip the first 2 increments. 
        """
        
        self.skip_controls = increment_list
            
    def set_hide_sub_translates(self, bool_value):
        
        self.hide_sub_translates = bool_value
            
    def set_nice_sub_control_naming(self, bool_value):
        """
        Nice sub control naming just increments the number of the name of the next sub control.
        So insteado of CNT_SUB_THING_1_C and CNT_SUB_THING_SUB_1_C as the names, names are:
        CNT_SUB_THING_1_C and CNT_SUB_THING_2_C  
        This may not be desirable in every case.
        """
        
        self.nice_sub_naming = bool_value
        
    def set_offset_rotation(self, value_list):
        """
        This will offset the controls by the rotation vector. Ex. [0,90,0] will rotate the xform group of the control 90 degrees on the Y axis.
        """
        self.offset_rotation = value_list
        
    def set_offset_rotation_at_inc(self, inc, value_list):
        """
        This will offset the controls by the rotation vector. Ex. [0,90,0] will rotate the xform group of the control 90 degrees on the Y axis.
        Inc starts at 0. 0 is the first control.
        """
        self.inc_offset_rotation[inc] = value_list
        
    def create(self):
        
        super(FkRig, self).create()
        
        self._loop(self.buffer_joints)
        
        if self.parent:
            cmds.parent(self.control_group, self.parent)
            
        if self.use_joint_controls:
            self._convert_to_joints()
        
class FkLocalRig(FkRig):
    """
    Same as FkRig but joints get connected in instead of constrained. 
    This allows the controls as a group to move separately from the joints.
    """
    def __init__(self, name, side=None):
        super(FkLocalRig, self).__init__(name, side)
        
        self.local_parent = None
        self.main_local_parent = None
        self.local_xform = None
        self.rig_scale = False
        self.connect_driver = False
        self.connect_xform = False
        
    def _attach(self, source_transform, target_transform):
        
        if not self.attach_joints:
            return
        
        local_group, local_xform = space.constrain_local(source_transform, target_transform, scale_connect = self.rig_scale)
        
        
        if not self.local_parent:
            self.local_xform = local_xform
            cmds.parent(local_xform, self.setup_group)
        
        if self.local_parent:
            follow = space.create_follow_group(self.local_parent, local_xform)
            cmds.parent(follow, self.control_group)
        
        if self.connect_driver:
            driver = space.create_xform_group(local_group, 'driver')
            
            orig_driver = self.control_dict[source_transform]['driver']
            attr.connect_transforms(orig_driver, driver)
            
        if self.connect_xform:
            orig_xform = self.control_dict[source_transform]['xform']
            attr.connect_transforms(orig_xform, local_xform)
        
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
        """
        Set whether the fk setup should be scalable at each control.
        """
        self.rig_scale = bool_value
        
    def set_scalable(self, bool_value):
        """
        Set whether the fk setup should be scalable at each control.
        """
        self.rig_scale = bool_value
    
    def set_connect_local_driver(self, bool_value):
        self.connect_driver = bool_value
        
    def set_connect_local_xform(self, bool_value):
        
        self.connect_xform = bool_value
    
    def set_local_parent(self, local_parent):
        self.main_local_parent = local_parent 
    
    def create(self):
        super(FkLocalRig, self).create()
        
        if self.main_local_parent:
            space.create_follow_group(self.main_local_parent, self.local_xform)
            
class FkScaleRig(FkRig): 
    """
    This extends FkRig so that it can be scalable at each control.
    """
      
    def __init__(self, name, side=None): 
        super(FkScaleRig, self).__init__(name, side) 
        self.last_control = '' 
        self.control = '' 
        self.controls = [] 
        self.current_xform_group = '' 
          
    def _create_scale_offset(self, control, target_transform):
        
        scale_offset = cmds.group(em = True, n = core.inc_name('scaleOffset_%s' % target_transform))
        offset_scale_offset = cmds.group(em = True, n = core.inc_name('offset_scaleOffset_%s' % target_transform))
        
        space.MatchSpace(control, offset_scale_offset).translation_rotation()
        space.MatchSpace(target_transform, scale_offset).translation_rotation()
        
        cmds.parent(scale_offset, offset_scale_offset)
        
        space.create_xform_group(scale_offset)
        
        attr.connect_scale(control, offset_scale_offset)
        cmds.scaleConstraint(scale_offset, target_transform)
        
        cmds.parent(offset_scale_offset, self.setup_group)
        parent = cmds.listRelatives(target_transform, p = True)
        if parent:
            cmds.parent(offset_scale_offset, parent[0])
          
    def _attach(self, control, target_transform):
        
        if not self.attach_joints:
            return
        
        if self.create_sub_controls:
            control = self.control_dict[control]['subs'][-1]
        
        xform = None
        
        if self.control_dict[control].has_key('xform'):
            xform = self.control_dict[control]['xform']
        
        if xform:
            was_offset = False
            
            if self.offset_rotation:
                cmds.xform(xform, ro = self.offset_rotation, r = True, os = True)
                self._create_scale_offset(control, target_transform)
                was_offset = True
                
            if self.current_increment in self.inc_offset_rotation:
                offset_rotation = self.inc_offset_rotation[self.current_increment]
                cmds.xform(xform,  ro = offset_rotation, r = True, os = True )
                self._create_scale_offset(control, target_transform)
                was_offset = True
                
            if not was_offset:
                attr.connect_scale(control, target_transform)
        
        if vtool.util.get_maya_version() >= 2015:  
            cmds.parentConstraint(control, target_transform, mo = True)
        
        if vtool.util.get_maya_version() <= 2014:
            cmds.pointConstraint(control, target_transform, mo = True)
            cmds.orientConstraint(control, target_transform, mo = True) 
            #attr.connect_rotate(control, target_transform)
             
        
    def _create_control(self, sub = False): 
        control = super(FkScaleRig, self)._create_control(sub) 
  
        self._set_control_attributes(control) 
        
        return self.control
  
    def _set_control_attributes(self, control):
        super(FkScaleRig, self)._set_control_attributes(control)
                
        control.show_scale_attributes()
        cmds.setAttr( '%s.overrideEnabled' % control.get() , 1 ) 
          
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
        
        attr.connect_scale(control, current_transform) 
      
    def _increment_greater_than_zero(self, control, current_transform): 

        cmds.select(cl = True) 
          
        name = self._get_name('jointFk') 
          
        buffer_joint = cmds.joint(n = core.inc_name( name ) ) 
          
        cmds.setAttr('%s.overrideEnabled' % buffer_joint, 1) 
        cmds.setAttr('%s.overrideDisplayType' % buffer_joint, 1) 
          
        cmds.setAttr('%s.radius' % buffer_joint, 0) 
          
        if not self.create_sub_controls:
            if self.last_control:
                cmds.connectAttr('%s.scale' % self.last_control.get(), '%s.inverseScale' % buffer_joint)
        
        match = space.MatchSpace(control, buffer_joint) 
        match.translation_rotation() 
          
        cmds.makeIdentity(buffer_joint, apply = True, r = True) 
        
        self._attach(control, current_transform)
        
        cmds.parent(self.current_xform_group, buffer_joint) 
          
        if not self.create_sub_controls:
            if self.last_control:
                cmds.parent(buffer_joint, self.last_control.get())
        if self.create_sub_controls: 
            last_control = self.control_dict[self.last_control.get()]['subs'][-1]
            cmds.parent(buffer_joint, last_control)
            
class FkCurlNoScaleRig(FkRig):
    """
    This extends FkRig with the ability to have a curl attribute. Good for fingers.
    """
    def __init__(self, description, side=None):
        super(FkCurlNoScaleRig, self).__init__(description, side)
        
        self.attribute_control = None
        self.attribute_name =None
        self.curl_axis = 'Z'
        self.skip_increments = []
        
        self.title_description = None
        
        
    def _create_control(self, sub = False):
        
        control = super(FkCurlNoScaleRig, self)._create_control(sub)
        
        if self.curl_axis == None:
            
            return control
        
        if sub:
            return control
        
        if not self.attribute_control:
            self.attribute_control = control.get()
            
        title = 'CURL'
        if self.title_description:
            title = 'CURL_%s' % self.title_description
            
        if not cmds.objExists('%s.%s' % (self.attribute_control, title)):
            title = attr.MayaEnumVariable(title)
            title.create(self.attribute_control)
        
        driver = space.create_xform_group(control.get(), 'driver2')
        self.control_dict[control.get()]['driver2'] = driver
        
        other_driver = self.drivers[-1]
        self.drivers[-1] = [other_driver, driver]
        
        if self.curl_axis != 'All':
            self._attach_curl_axis(driver)
            
        if self.curl_axis == 'All':
            all_axis = ['x','y','z']
            
            for axis in all_axis:
                self._attach_curl_axis(driver, axis)
                
        return control
    
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
            
        curl_variable = attr.MayaNumberVariable(var_name)
        curl_variable.set_variable_type(curl_variable.TYPE_DOUBLE)
        curl_variable.create(self.attribute_control)
        
        curl_variable.connect_out('%s.rotate%s' % (driver, curl_axis))
        
        if self.current_increment and self.create_buffer_joints:
            
            current_transform = self.transform_list[self.current_increment]
            attr.connect_rotate(driver, current_transform)
    
    def set_curl_axis(self, axis_letter):
        """
        Set the axis that the curl should rotate on.
        
        Args:
            axis_letter (str): 'X','Y','Z'
        """
        self.curl_axis = axis_letter.capitalize()
    
    def set_curl_description(self, description):
        """
        The attribute name for the curl slider.
        
        Args:
            attribute_name (str): The name of the curl slider attribute.
        """
        self.curl_description = description
    
    def set_attribute_control(self, control_name):
        """
        Set the control that the curl slider should live on.
        
        Args:
            control_name (str): The name of a control.
        """
        self.attribute_control = control_name
        
    def set_attribute_name(self, attribute_name):
        """
        The attribute name for the curl slider.
        
        Args:
            attribute_name (str): The name of the curl slider attribute.
        """
        
        self.attribute_name = attribute_name
        
    def set_title_description(self, description):
        
        self.title_description = description
        
    def set_skip_increments(self, increments):
        """
        You can skip increments so they don't get affected by the curl.
        Each increment corresponds to a joint set in set_joints
        
        Args:
            increments (list): Eg. [0], will not add curl to the control on the first joint.
        """
        self.skip_increments = increments
        
class FkCurlRig(FkScaleRig):
    
    def __init__(self, description, side=None):
        super(FkCurlRig, self).__init__(description, side)
        
        self.attribute_control = None
        self.curl_axis = 'Z'
        self.curl_description = self.description
        self.skip_increments = []
        self.title = 'CURL'
        
    def _create_control(self, sub = False):
        control = super(FkCurlRig, self)._create_control(sub)
        
        if sub:
            return control
        
        if not self.attribute_control:
            self.attribute_control = control.get()
            
        attr.create_title(self.attribute_control, self.title)
        
        driver = space.create_xform_group(control.get(), 'driver2')
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
            
        curl_variable = attr.MayaNumberVariable(var_name)
        curl_variable.set_variable_type(curl_variable.TYPE_DOUBLE)
        curl_variable.create(self.attribute_control)
        
        curl_variable.connect_out('%s.rotate%s' % (driver, curl_axis))
        
    def set_curl_axis(self, axis_letter):
        """
        Set the axis that the curl should rotate on.
        
        Args:
            axis_letter (str): 'X','Y','Z'
        """
        self.curl_axis = axis_letter.capitalize()
    
    def set_curl_description(self, description):
        """
        The attribute name for the curl slider.
        
        Args:
            attribute_name (str): The name of the curl slider attribute.
        """
        self.curl_description = description
        
    def set_skip_increments(self, increments):
        """
        You can skip increments so they don't get affected by the curl.
        Each increment corresponds to a joint set in set_joints
        
        Args:
            increments (list): Eg. [0], will not add curl to the control on the first joint.
        """        
        self.skip_increments = increments
        
    def set_curl_skip_incrment(self, increments):
        
        self.set_skip_increments(increments)
    
    def set_attribute_control(self, control_name):
        """
        Set the control that the curl slider should live on.
        
        Args:
            control_name (str): The name of a control.
        """
        self.attribute_control = control_name
        
    def set_attribute_name(self, attribute_name):
        """
        The attribute name for the curl slider.
        
        Args:
            attribute_name (str): The name of the curl slider attribute.
        """
        
        self.attribute_name = attribute_name
        
    def set_curl_title(self, name):
        self.title = name.upper()
        
class SplineRibbonBaseRig(JointRig):
    
    def __init__(self, description, side=None):
        
        super(SplineRibbonBaseRig, self).__init__(description, side)
        
        self.orig_curve = None
        self.curve = None
        
        self.control_count = 2
        self.span_count = 2
        self.stretchy = True
        self.advanced_twist = True
        self.stretch_on_off = False
        self.ik_curve = None
        self.wire_hires = False
        self.last_pivot_top_value = False
        self.fix_x_axis = False
        self.ribbon = False
        self.ribbon_offset = 1
        self.ribbon_offset_axis = 'Y'
        self.closest_y = False
        self.stretch_axis = 'X'
        self.stretch_attribute_control = None
        
        self.follicle_ribbon = False
        
        self.create_ribbon_buffer_group = False
        
    def _create_curve(self, span_count):
        
        if not self.curve:
            
            name = self._get_name()
            
            self.orig_curve = geo.transforms_to_curve(self.joints, self.span_count, name)
            cmds.setAttr('%s.inheritsTransform' % self.orig_curve, 0)
        
            self.curve = cmds.duplicate(self.orig_curve)[0]
        
            cmds.rebuildCurve(self.curve, 
                              spans = span_count ,
                              rpo = True,  
                              rt = 0, 
                              end = 1, 
                              kr = False, 
                              kcp = False, 
                              kep = True,  
                              kt = False,
                              d = 3)
        
            name = self.orig_curve
            self.orig_curve = cmds.rename(self.orig_curve, core.inc_name('orig_curve'))
            self.curve = cmds.rename(self.curve, name)
            cmds.parent(self.orig_curve, self.setup_group)
            
            cmds.parent(self.curve, self.setup_group)
            
    def _create_surface(self, span_count):
        
        self.surface = geo.transforms_to_nurb_surface(self.joints, self._get_name(), spans = span_count, offset_amount = self.ribbon_offset, offset_axis = self.ribbon_offset_axis)
        cmds.setAttr('%s.inheritsTransform' % self.surface, 0)
        cmds.parent(self.surface, self.setup_group)
    
    def _create_clusters(self):
        
        if self.ribbon:
            cluster_surface = deform.ClusterSurface(self.surface, self.description)
        if not self.ribbon:
            cluster_surface = deform.ClusterCurve(self.curve, self.description)
        
        if self.last_pivot_top_value:
            last_pivot_end = True
        if not self.last_pivot_top_value:
            last_pivot_end = False
        
        cluster_surface.set_first_cluster_pivot_at_start(True)
        cluster_surface.set_last_cluster_pivot_at_end(last_pivot_end)
        cluster_surface.set_join_ends(True)
        cluster_surface.create()
        
        self.clusters = cluster_surface.handles
        cluster_group = self._create_setup_group('clusters')
        cmds.parent(self.clusters, cluster_group)
        
        return self.clusters
        
    def _create_geo(self, span_count):
        
        if self.ribbon:
            self._create_surface(span_count)
            
        if not self.ribbon:
            
            self._create_curve(span_count)
    
    def _attach_to_geo(self):
        if not self.attach_joints:
            return
        
        if self.ribbon:
            
            group_name = 'rivets'
            
            if self.follicle_ribbon:
                group_name = 'follicles'
            
            rivet_group = self._create_setup_group(group_name)
        
            for joint in self.buffer_joints:
                
                buffer_group = None
                
                if self.create_ribbon_buffer_group:
                    buffer_group = cmds.group(em = True, n = 'ribbonBuffer_%s' % joint)
                    xform = space.create_xform_group(buffer_group)
                    
                    space.MatchSpace(joint, xform).translation_rotation()
                
                if not buffer_group:
                    if not self.follicle_ribbon:
                        rivet = geo.attach_to_surface(joint, self.surface)
                        cmds.setAttr('%s.inheritsTransform' % rivet, 0)
                        cmds.parent(rivet, rivet_group)
                    
                    if self.follicle_ribbon:
                        
                        follicle = geo.follicle_to_surface(joint, self.surface, constrain = True)
                        cmds.setAttr('%s.inheritsTransform' % follicle, 0)
                        cmds.parent(follicle, rivet_group)
                        
                if buffer_group:
                    if not self.follicle_ribbon:
                        
                        rivet = geo.attach_to_surface(xform, self.surface, constrain = False)
                        cmds.setAttr('%s.inheritsTransform' % rivet, 0)
                        cmds.parentConstraint(buffer_group, joint, mo = True)
                        cmds.parent(rivet, rivet_group)
                    
                    if self.follicle_ribbon:
                        
                        follicle = geo.follicle_to_surface(xform, self.surface, constrain = False)
                        cmds.setAttr('%s.inheritsTransform' % follicle, 0)
                        cmds.parentConstraint(buffer_group, joint, mo = True)
                        cmds.parent(follicle, rivet_group)
                    
        
        if not self.ribbon:
            self._create_spline_ik()
        
    def _wire_hires(self, curve):
        
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

    def _setup_stretchy(self, control):
        
        if not self.attach_joints:
            return
        
        if self.stretchy:    
            
            if self.stretch_attribute_control:
                control = self.stretch_attribute_control
            
            attr.create_title(control, 'STRETCH')
            
            rigs_util.create_spline_ik_stretch(self.ik_curve, self.buffer_joints[:-1], control, self.stretch_on_off, self.stretch_axis)
    
        
                
    def _create_spline_ik(self):
        
        self._wire_hires(self.curve)
        
        if self.buffer_joints:
            joints = self.buffer_joints
        if not self.buffer_joints:
            joints = self.joints
            
        if self.fix_x_axis:
            duplicate_hierarchy = space.DuplicateHierarchy( joints[0] )
        
            duplicate_hierarchy.stop_at(self.joints[-1])
            
            prefix = 'joint'
            if self.create_buffer_joints:
                prefix = 'buffer'
            
            duplicate_hierarchy.replace(prefix, 'xFix')
            x_joints = duplicate_hierarchy.create()
            cmds.parent(x_joints[0], self.setup_group)
            
            #working here to add auto fix to joint orientation.
            
            for inc in range(0, len(x_joints)):
                
                orient = attr.OrientJointAttributes(x_joints[inc])
                orient.delete()
                
                orient = space.OrientJoint(x_joints[inc])
                
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
        
        start_joint = joints[0]
        end_joint = joints[-1]
        
        handle = space.IkHandle(self._get_name())
        handle.set_solver(handle.solver_spline)
        handle.set_start_joint(start_joint)
        handle.set_end_joint(end_joint)
        handle.set_curve(self.ik_curve)
        handle = handle.create()
        
        self.ik_handle = handle

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
            
            match = space.MatchSpace(self.buffer_joints[0], start_locator)
            match.translation_rotation()
            
            match = space.MatchSpace(self.buffer_joints[-1], end_locator)
            match.translation_rotation()
                        
            cmds.setAttr('%s.dTwistControlEnable' % self.ik_handle, 1)
            cmds.setAttr('%s.dWorldUpType' % self.ik_handle, 4)
            cmds.connectAttr('%s.worldMatrix' % start_locator, '%s.dWorldUpMatrix' % self.ik_handle)
            cmds.connectAttr('%s.worldMatrix' % end_locator, '%s.dWorldUpMatrixEnd' % self.ik_handle)
            

            
    def set_advanced_twist(self, bool_value):
        """
        Wether to use spline ik top btm advanced twist.
        """
        self.advanced_twist = bool_value

    def set_stretchy(self, bool_value):
        """
        Wether the joints should stretch to match the spline ik.
        """
        self.stretchy = bool_value
        
    def set_stretch_on_off(self, bool_value):
        """
        Wether to add a stretch on/off attribute. 
        This allows the animator to turn the stretchy effect off over time.
        """
        self.stretch_on_off = bool_value
    
    def set_stretch_axis(self, axis_letter):
        """
        Set the axis that the joints should stretch on.
        """
        self.stretch_axis = axis_letter
        
    def set_stretch_attribute_control(self, node_name):
        self.stretch_attribute_control = node_name
    
    def set_curve(self, curve):
        """
        Set the curve that the controls should move and the joints should follow.
        """
        self.curve = curve
        
    def set_ribbon(self, bool_value):
        """
        By default the whole setup uses a spline ik. This will cause the setup to use a nurbs surface.
        If this is on, stretch options are ignored.
        """
        self.ribbon = bool_value
        
    def set_ribbon_offset(self, float_value):
        """
        Set the width of the ribbon.
        """
        self.ribbon_offset = float_value
        
    def set_ribbon_offset_axis(self, axis_letter):
        """
        Set which axis the ribbon width is offset on.
        
        Args:
            axis_letter (str): 'X','Y' or 'Z' 
        """
        self.ribbon_offset_axis = axis_letter
        
    def set_ribbon_follicle(self, bool_value):
        self.follicle_ribbon = bool_value
        
    def set_ribbon_buffer_group(self, bool_value):
        self.create_ribbon_buffer_group = bool_value
        
    def set_last_pivot_top(self, bool_value):
        """
        Set the last pivot on the curve to the top of the curve.
        """
        self.last_pivot_top_value = bool_value
    
    def set_fix_x_axis(self, bool_value):
        """
        This will create a duplicate chain for the spline ik, that has the x axis pointing down the joint.
        The new joint chain moves with the controls, and constrains the regular joint chain.
        """
        self.fix_x_axis = bool_value
        
    def set_closest_y(self, bool_value):
        """
        Wether to turn on Maya's closest y option, which can solve flipping in some cases.
        """
        self.closest_y = bool_value

class SimpleFkCurveRig(FkCurlNoScaleRig, SplineRibbonBaseRig):
    def __init__(self, name, side=None):
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
        self.control_xform_relative = True
        self.last_pivot_top_value = False
        self.fix_x_axis = False
        self.skip_first_control = False
        self.ribbon = False
        self.ribbon_offset = 1
        self.ribbon_offset_axis = 'Y'
        self.create_follows = True
        self.create_btm_follow = False
        self.closest_y = False
        self.stretch_axis = 'X'
        self.sub_control_size = .8
        self.sub_visibility = 1
    
    def _create_sub_control(self):
            
        sub_control = self._create_control( sub = True)

        return sub_control

    def _first_increment(self, control, current_transform):
        
        self.first_control = control

        if self.skip_first_control:
            control = rigs_util.Control(control)
            control.delete_shapes()
            
            rename_control = rigs_util.Control(self.controls[-1])
            rename_control.rename(self.first_control.replace('CNT_', 'ctrl_'))
            self.first_control = rename_control.control
            
            self.controls[-1] = rename_control.control

        if self.sub_controls:
            self.top_sub_control = self.sub_controls[0]
            
            if self.skip_first_control:
                control = rigs_util.Control(self.sub_controls[0])
                control.delete_shapes()
                self.top_sub_control = cmds.rename(self.top_sub_control, self.top_sub_control.replace('CNT_', 'ctrl_'))
                self.sub_controls[0] = self.top_sub_control
    
    def _increment_greater_than_zero(self, control, current_transform):
        
        cmds.parent(self.current_xform_group, self.controls[-2])    

    def _last_increment(self, control, current_transform):
        
        if not self.sub_controls:
            return
        
        if self.create_follows:
            
            space.create_follow_fade(self.controls[-1], self.sub_drivers[:-1])
            space.create_follow_fade(self.sub_controls[-1], self.sub_drivers[:-1])
            space.create_follow_fade(self.sub_controls[0], self.sub_drivers[1:])
            space.create_follow_fade(self.sub_drivers[0], self.sub_drivers[1:])
        
        top_driver = self.drivers[-1]
        
        if self.create_follows:
            if not type(top_driver) == list:
                space.create_follow_fade(self.drivers[-1], self.sub_drivers[:-1])
                
        if self.create_follows:
            if self.create_btm_follow:
                space.create_follow_fade(self.controls[0], self.sub_drivers[1:])
            
    def _all_increments(self, control, current_transform):
        
        match = space.MatchSpace(self.clusters[self.current_increment], self.current_xform_group)
        match.translation_to_rotate_pivot()
        
        if self.orient_controls_to_joints:
            
            if not self.orient_joint:
                joint = self._get_closest_joint()
            if self.orient_joint:
                joint = self.orient_joint
                
            match = space.MatchSpace(joint, self.current_xform_group)
            match.rotation()
        
        if self.sub_control_on:
            
            sub_control = self._create_sub_control()
            sub_control_object = sub_control
            sub_control = sub_control.get()
            

        
            xform_sub_control = self.control_dict[sub_control]['xform']

            match = space.MatchSpace(control, xform_sub_control)
            match.translation_rotation()
            
            self.sub_drivers.append( self.control_dict[sub_control]['driver'])
            
            cmds.parent(xform_sub_control, self.control.get())
            
            self._connect_sub_visibility('%s.subVisibility' % control, sub_control)
            
                
            sub_control_object.hide_scale_and_visibility_attributes()
            

        
        increment = self.current_increment+1
        
        if increment in self.control_xform:
            vector = self.control_xform[increment]
            cmds.move(vector[0], vector[1],vector[2], self.current_xform_group, r = self.control_xform_relative)
        
        if self.sub_control_on:
            cmds.parentConstraint(sub_control, self.clusters[self.current_increment], mo = True)
        
        if not self.sub_control_on:
            cmds.parentConstraint(control, self.clusters[self.current_increment], mo = True)
        
        #cmds.parent(self.current_xform_group, self.control_group)
        
    def _get_closest_joint(self):
        
        current_cluster = self.clusters[self.current_increment]
        
        return space.get_closest_transform(current_cluster, self.buffer_joints)
    
    def _loop(self, transforms):
        
        super(SimpleFkCurveRig, self)._loop(self.clusters)
        
    def _create_before_attach_joints(self):
        super(SimpleFkCurveRig, self)._create_before_attach_joints()
        
        self._attach_to_geo()
        
    def _attach_ik_spline_to_controls(self):
        
        if self.advanced_twist:
            if hasattr(self, 'top_sub_control'):
                cmds.parent(self.start_locator, self.sub_controls[0])
                
            if not hasattr(self, 'top_sub_control'):
                if not self.sub_controls:
                    cmds.parent(self.start_locator, self.controls[0])
                if self.sub_controls:
                    cmds.parent(self.start_locator, self.sub_controls[0])
                
            if self.sub_controls:
                cmds.parent(self.end_locator, self.sub_controls[-1])
            if not self.sub_controls:
                cmds.parent(self.end_locator, self.controls[-1])
                
        if not self.advanced_twist and self.buffer_joints != self.joints:
            
            follow = space.create_follow_group(self.controls[0], self.buffer_joints[0])
            cmds.parent(follow, self.setup_group)
            
        if not self.advanced_twist:
            var = attr.MayaNumberVariable('twist')
            var.set_variable_type(var.TYPE_DOUBLE)
            var.create(self.controls[0])
            var.connect_out('%s.twist' % self.ik_handle)
    
    def set_control_xform(self, vector, inc, relative = True):
        """
        This allows a control to be moved while its being created. 
        This way all the clusters and everything are still functioning properly.
        
        Args:
            vector [list]: Eg [0,0,0], the amount to move the control, relative to its regular position.
            inc [int]: The increment of the control. An increment of 1 would move the first control.
        """
        self.control_xform[inc] = vector
        self.control_xform_relative = relative
    
    def set_orient_joint(self, joint):
        """
        Set a joint to match the orientation of the controls to.
        
        Args:
            joint (str): The name of a joint.
        """
        self.orient_joint = joint
    
    def set_match_to_rotation(self):
        """
        Not used in FkCurve Rigs. Use set_orient_controls_to_joints instead.
        """
        pass
    
    def set_orient_controls_to_joints(self, bool_value):
        """
        Wether to match the control's orientation to the nearest joint.
        """
        self.orient_controls_to_joints = bool_value
    
    def set_control_count(self, int_value, span_count = None, wire_hires = False):
        """
        Set the number of controls.
        Wire hires is good for having the joints follow a well defined curve while maintaining a small amount of controls.
        
        Args:
            int_value (int): The number of controls.
            span_count (int): The number of spans on the curve.
            wire_hires (bool): Wether to wire deform the hires to the control Curve. If span count doesn't match the control count.
            
        """
        
        if int_value == 0 or int_value < 2:
            int_value = 2
            
        self.control_count = int_value
        
        if not span_count:
            self.span_count = self.control_count
            
        if span_count:
            self.span_count = span_count
            self.wire_hires = wire_hires
            
    
    def set_sub_control(self, bool_value):
        """
        Wether to create sub controls.
        """
        
        self.sub_control_on = bool_value
    
    def set_skip_first_control(self, bool_value):
        """
        This allows the setup to not have the first control.
        """
        self.skip_first_control = bool_value
        
    def set_create_follows(self, bool_value):
        """
        By default the first and last controls fade influence up the sub controls of the setup.
        By setting this to False, the top and btm controls will no longer affect mid sub controls.
        """
        self.create_follows = bool_value
        
    def set_create_bottom_follow(self, bool_value):
        """
        This will cause the last control in the spine to have a follow fade on sub controls up the length of the spine.
        If set_create_follows is set to False this will be ignored.
        """
        
        self.create_btm_follow = bool_value
        
    def create(self):
        
        self._create_geo( self.control_count - 1 )
        self._create_clusters()
        
        super(SimpleFkCurveRig, self).create()
        
        #self._attach_to_geo()
        
        if not self.ribbon:
            self._setup_stretchy(self.controls[-1])
            self._attach_ik_spline_to_controls()
        """
        if not self.ribbon:
            self._create_spline_ik()
            self._setup_stretchy()
            
        if self.ribbon:
            self._create_ribbon()
        
        cmds.delete(self.orig_curve) 
        """
    
class FkCurveRig(SimpleFkCurveRig):
    """
    This extends SimpleFkCurveRig. This is usually used for spine setups.
    """
    def __init__(self, name, side=None):
        super(FkCurveRig, self).__init__(name, side)
        
        self.aim_end_vectors = False
        
    def _create_aims(self, clusters):
        
        control1 = self.sub_controls[0]
        control2 = self.sub_controls[-1]
        
        cluster1 = clusters[0]
        cluster2 = clusters[-1]
        
        cmds.delete( cmds.listRelatives(cluster1, ad = True, type = 'constraint') )
        cmds.delete( cmds.listRelatives(cluster2, ad = True, type = 'constraint') )
        
        aim1 = cmds.group(em = True, n = core.inc_name('aimCluster_%s_1' % self._get_name()))
        aim2 = cmds.group(em = True, n = core.inc_name('aimCluster_%s_2' % self._get_name()))
        
        xform_aim1 = space.create_xform_group(aim1)
        xform_aim2 = space.create_xform_group(aim2)
        
        space.MatchSpace(control1, xform_aim1).translation()
        space.MatchSpace(control2, xform_aim2).translation()
        
        cmds.parentConstraint(control1, xform_aim1,  mo = True)
        cmds.parentConstraint(control2, xform_aim2,  mo = True)
        
        mid_control_id = len(self.sub_controls)/2
        
        cmds.aimConstraint(self.sub_controls[mid_control_id], aim1, wuo = self.controls[0], wut = 'objectrotation')
        cmds.aimConstraint(self.sub_controls[mid_control_id], aim2, wuo = self.controls[-1], wut = 'objectrotation')

        cmds.parent(cluster1, aim1)
        cmds.parent(cluster2, aim2)
        
        cmds.parent(xform_aim1, xform_aim2, self.setup_group)
    
    def set_aim_end_vectors(self, bool_value):
        """
        Wether the first and last clusters should aim at the mid controls 
        """
        self.aim_end_vectors = bool_value
        

        
    def create(self):
        super(FkCurveRig, self).create()
        
        if self.aim_end_vectors:    
            if not self.ribbon:
                self._create_aims(self.clusters)
            if self.ribbon:
                self._create_aims(self.ribbon_clusters)

class FkCurveLocalRig(FkCurveRig):
    
    def __init__(self, description, side=None):
        super(FkCurveLocalRig, self).__init__(description, side)
        
        self.last_local_group = None
        self.last_local_xform = None
        self.local_parent = None     
        self.sub_local_controls = []
        
    def _all_increments(self, control, current_transform):
        
        match = space.MatchSpace(self.clusters[self.current_increment], self.current_xform_group)
        match.translation_to_rotate_pivot()
        
        if self.orient_controls_to_joints:
            
            closest_joint = self._get_closest_joint()
            
            match = space.MatchSpace(closest_joint, self.current_xform_group)
            match.rotation()
        
        if self.sub_control_on:
            
            sub_control = rigs_util.Control( self._get_control_name(sub = True) )
        
            sub_control.color( attr.get_color_of_side( self.side , True)  )
            
            if self.control_shape:
                sub_control.set_curve_type(self.control_shape)
            
            sub_control_object = sub_control
            sub_control = sub_control.get()
            
            match = space.MatchSpace(control, sub_control)
            match.translation_rotation()
        
            xform_sub_control = space.create_xform_group(sub_control)
            self.sub_drivers.append( space.create_xform_group(sub_control, 'driver') )
            
            local_group, local_xform = space.constrain_local(sub_control, self.clusters[self.current_increment])
            
            self.sub_local_controls.append( local_group )
            
            #cmds.parent(local_xform, self.setup_group)
            
            control_local_group, control_local_xform = space.constrain_local(control, local_xform)
            
            if self.control_dict[self.control.get()].has_key('driver2'):
                control_driver = self.control_dict[self.control.get()]['driver2']
            
                driver = space.create_xform_group( control_local_group, 'driver')
                attr.connect_rotate(control_driver, driver)
            
            
            cmds.parent(control_local_xform, self.setup_group)
            
            cmds.parent(local_xform, control_local_group)
            
            if self.last_local_group:
                cmds.parent(control_local_xform, self.last_local_group)
            
            self.last_local_group = control_local_group
            self.last_local_xform = control_local_xform
            
            cmds.parent(xform_sub_control, self.control.get())
            self.sub_controls.append(sub_control)
            
            sub_vis = attr.MayaNumberVariable('subVisibility')
            sub_vis.set_variable_type(sub_vis.TYPE_BOOL)
            sub_vis.create(control)
            sub_vis.connect_out('%sShape.visibility' % sub_control)
            
            sub_control_object.hide_scale_and_visibility_attributes()
            
        if not self.sub_control_on:
            
            space.constrain_local(control, self.clusters[self.current_increment])
        
        #cmds.parent(self.current_xform_group, self.control_group)
        
    def _first_increment(self, control, current_transform):
        super(FkCurveLocalRig, self)._first_increment(control, current_transform)
        
        if self.local_parent:
            cmds.parent(self.last_local_xform, self.local_parent)
    
    def _create_spline_ik(self):
        
        self._wire_hires(self.curve)
        #self._create_ik_curve(self.curve)
        
        children = cmds.listRelatives(self.buffer_joints[-1], c = True)
        
        if children:
            cmds.parent(children, w = True)
        
        handle = space.IkHandle(self._get_name())
        handle.set_solver(handle.solver_spline)
        handle.set_curve(self.curve)
        handle.set_start_joint(self.buffer_joints[0])
        handle.set_end_joint(self.buffer_joints[-1])
        handle = handle.create()
        
        self.ik_handle = handle
        
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
            
            match = space.MatchSpace(self.buffer_joints[0], start_locator)
            match.translation_rotation()
            
            match = space.MatchSpace(self.buffer_joints[-1], end_locator)
            match.translation_rotation()
            
            
            cmds.setAttr('%s.dTwistControlEnable' % handle, 1)
            cmds.setAttr('%s.dWorldUpType' % handle, 4)
            cmds.connectAttr('%s.worldMatrix' % start_locator, '%s.dWorldUpMatrix' % handle)
            cmds.connectAttr('%s.worldMatrix' % end_locator, '%s.dWorldUpMatrixEnd' % handle)
            
    def _attach_ik_spline_to_controls(self):
        
        if self.advanced_twist:
            if hasattr(self, 'top_sub_control'):
                cmds.parent(self.start_locator, self.sub_local_controls[0])
                
            if not hasattr(self, 'top_sub_control'):
                cmds.parent(self.start_locator, self.sub_local_controls[0])
                
            
            cmds.parent(self.end_locator, self.sub_local_controls[-1])
            
        if not self.advanced_twist:
            
            space.create_local_follow_group(self.controls[0], self.buffer_joints[0])
            #util.constrain_local(self.controls[0], self.buffer_joints[0])
            
            var = attr.MayaNumberVariable('twist')
            var.set_variable_type(var.TYPE_DOUBLE)
            var.create(self.controls[0])
            var.connect_out('%s.twist' % self.ik_handle)
            
    def set_local_parent(self, parent):
        self.local_parent = parent

    def create(self):
        super(FkCurveLocalRig, self).create()
        """
        if not self.ribbon:
            self._create_spline_ik()
            self._setup_stretchy()
            
        if self.ribbon:
            surface = geo.transforms_to_nurb_surface(self.buffer_joints, self._get_name(), spans = self.control_count-1, offset_amount = self.ribbon_offset, offset_axis = self.ribbon_offset_axis)
            
            cmds.setAttr('%s.inheritsTransform' % surface, 0)
            
            cluster_surface = deform.ClusterSurface(surface, self._get_name())
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
                rivet = geo.attach_to_surface(joint, surface)
                cmds.setAttr('%s.inheritsTransform' % rivet, 0)
                cmds.parent(rivet, self.setup_group)
        
        cmds.delete(self.orig_curve) 
        """



class IkSplineNubRig(BufferRig):
    """
    This is used for the tweaker setup.
    """
    
    
    def __init__(self, description, side=None):
        
        super(IkSplineNubRig, self).__init__(description, side)
        
        self.end_with_locator = False
        self.top_guide = None
        self.btm_guide = None
        
        self.bool_create_middle_control = True
        
        self.right_side_fix = True
        self.right_side_fix_axis = 'x'
        
        self.negate_right_scale = False
        
        self.control_shape = 'pin'
        
        self.control_orient = None
        
    def _duplicate_joints(self):
        
        if self.create_buffer_joints:
            duplicate_hierarchy = space.DuplicateHierarchy( self.joints[0] )
            
            duplicate_hierarchy.stop_at(self.joints[-1])
            duplicate_hierarchy.replace('joint', 'buffer')
            
            self.buffer_joints = duplicate_hierarchy.create()
    
            cmds.parent(self.buffer_joints[0], self.setup_group)

        if not self.create_buffer_joints:
            self.buffer_joints = self.joints
        
        return self.buffer_joints

    def _create_twist_group(self, top_control, top_handle, top_guide):
        
        name = self._get_name()
        
        twist_guide_group = cmds.group(em = True, n = core.inc_name('guideSetup_%s' % name))
        cmds.hide(twist_guide_group)
        
        cmds.parent([top_guide, top_handle], twist_guide_group)
        
        cmds.parent(twist_guide_group, self.setup_group)
        
        cmds.parentConstraint(top_control, twist_guide_group,mo = True)
        
        self.end_locator = True
        
    def _create_joint_line(self, rp = False):
    
        name = self._get_name()
    
        position_top = cmds.xform(self.buffer_joints[0], q = True, t = True, ws = True)
        position_btm = cmds.xform(self.buffer_joints[-1], q = True, t = True, ws = True)
    
        cmds.select(cl = True)
        guide_top = cmds.joint( p = position_top, n = core.inc_name('topTwist_%s' % name) )
        
        cmds.select(cl = True)
        guide_btm = cmds.joint( p = position_btm, n = core.inc_name('btmTwist_%s' % name) )
        
        space.MatchSpace(self.buffer_joints[0], guide_top).rotation()
        
        cmds.makeIdentity(guide_top, r = True, apply = True)
        
        cmds.parent(guide_btm, guide_top)
        
        cmds.makeIdentity(guide_btm, r = True, jo = True, apply = True)
        
        handle = space.IkHandle(name)
        if not rp:
            handle.set_solver(handle.solver_sc)
        if rp:
            handle.set_solver(handle.solver_rp)
        handle.set_start_joint(guide_top)
        handle.set_end_joint(guide_btm)
        
        handle = handle.create()
        
        if not rp:
            cmds.setAttr('%s.poleVectorX' % handle, 0)
            cmds.setAttr('%s.poleVectorY' % handle, 0)
            cmds.setAttr('%s.poleVectorZ' % handle, 0)
        
        return guide_top, handle
    
    def _create_spline(self, follow, btm_constrain, mid_constrain):
        
        name = self._get_name()
        
        ik_handle = None
        
        spline_setup_group = cmds.group( em = True, n = core.inc_name('splineSetup_%s' % name))
        cmds.hide(spline_setup_group)
        cluster_group = cmds.group( em = True, n = core.inc_name('clusterSetup_%s' % name))
        
        #do not do this way unless heavily tested first
        """
        handle = util.IkHandle(name)
        handle.set_solver(handle.solver_spline)
        handle.set_start_joint(self.buffer_joints[0])
        handle.set_end_joint(self.buffer_joints[-1])
        
        ik_handle = handle.create()
        curve = handle.curve
        
        ik_handle = cmds.rename(ik_handle, core.inc_name('handle_spline_%s' % name))
        """
        
        
        #here
        ik_handle, effector, curve = cmds.ikHandle(sj = self.buffer_joints[0], 
                                                ee = self.buffer_joints[-1], 
                                                sol = 'ikSplineSolver', 
                                                pcv = False, 
                                                name = core.inc_name('handle_spline_%s' % name))
        #to here  could be replaced some day
        
        cmds.setAttr('%s.inheritsTransform' % curve, 0)
        
        curve = cmds.rename(curve, core.inc_name('curve_%s' % name) )
        effector = cmds.rename(effector, core.inc_name('effector_%s' % name))
        
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
        
        rigs_util.create_spline_ik_stretch(curve, self.buffer_joints[:-1], control)
    
    def _create_top_control(self):
        
        if not self.end_with_locator:
            control = self._create_control('top', curve_type= self.control_shape)
        if self.end_with_locator:
            control = self._create_control(curve_type = self.control_shape)
                        
        control.hide_scale_and_visibility_attributes()
        
        xform = space.create_xform_group(control.get())
        
        orient_transform = self.control_orient
        
        if not orient_transform:
            orient_transform = self.joints[0]
        
        space.MatchSpace(orient_transform, xform).translation()
        space.MatchSpace(orient_transform, xform).rotation()
        
        self._fix_right_side_orient(xform)
        
        if self.negate_right_scale and self.side == 'R':
            cmds.setAttr('%s.scaleX' % xform, -1)
            cmds.setAttr('%s.scaleY' % xform, -1)
            cmds.setAttr('%s.scaleZ' % xform, -1)  
        
        return control.get(), xform
    
    def _create_btm_control(self):
        control = self._create_control('btm', curve_type=self.control_shape)
        control.hide_scale_and_visibility_attributes()
        
        xform = space.create_xform_group(control.get())
        
        orient_translate = self.joints[-1]
        orient_rotate = self.control_orient
                
        if not orient_rotate:
            orient_rotate = self.joints[0]
        
        space.MatchSpace(orient_translate, xform).translation()
        space.MatchSpace(orient_rotate, xform).rotation()
        
        self._fix_right_side_orient(xform)
        
        if self.negate_right_scale and self.side == 'R':
            cmds.setAttr('%s.scaleX' % xform, -1)
            cmds.setAttr('%s.scaleY' % xform, -1)
            cmds.setAttr('%s.scaleZ' % xform, -1)   
        
        return control.get(), xform
    
    def _create_btm_sub_control(self):
        control = self._create_control('btm', sub = True)
        control.scale_shape(.5, .5, .5)
        control.hide_scale_and_visibility_attributes()
        
        xform = space.create_xform_group(control.get())
        
        orient_translate = self.joints[-1]
        orient_rotate = self.control_orient
        
        if not orient_rotate:
            orient_rotate = self.joints[0]
        
        space.MatchSpace(orient_translate, xform).translation()
        space.MatchSpace(orient_rotate, xform).rotation()
        
        
        self._fix_right_side_orient(xform)
        
        if self.negate_right_scale and self.side == 'R':
            cmds.setAttr('%s.scaleX' % xform, -1)
            cmds.setAttr('%s.scaleY' % xform, -1)
            cmds.setAttr('%s.scaleZ' % xform, -1)   
        
        return control.get(), xform
        
    def _create_mid_control(self):
        
        if self.bool_create_middle_control:
            control = self._create_control('mid', sub = True)
            control.scale_shape(.5, .5, .5)
            control.hide_scale_and_visibility_attributes()
            
            
            control = control.get()
        
        if not self.bool_create_middle_control:
            mid_locator = cmds.spaceLocator(n = core.inc_name(self._get_name('locator', 'mid')))[0]
            control = mid_locator
            cmds.hide(mid_locator)
        
        xform = space.create_xform_group(control)
        
        orient_transform = self.control_orient
        
        if not orient_transform:
            orient_transform = self.joints[0]
        
        space.MatchSpace(orient_transform, xform).translation_rotation()
        
        self._fix_right_side_orient(xform)
        
        if self.negate_right_scale and self.side == 'R':
            cmds.setAttr('%s.scaleX' % xform, -1)
            cmds.setAttr('%s.scaleY' % xform, -1)
            cmds.setAttr('%s.scaleZ' % xform, -1)      
        
        return control, xform
    
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
        
  
    
    def set_end_with_locator(self, bool_value):
        """
        Wether the end effector control should be a locator instead.
        """
        self.end_with_locator = True
    
    def set_guide_top_btm(self, top_guide, btm_guide):
        """
        Set the parents for the top and btm guide controls.
        """
        self.top_guide = top_guide
        self.btm_guide = btm_guide
    
    def set_control_shape(self, name):
        self.control_shape = name
    
    def set_create_middle_control(self, bool_value):
        """
        Wether to create the elbow control.
        """
        self.bool_create_middle_control = bool_value
    
    def set_right_side_fix(self, bool_value, axis):
        """
        Wether to compensate for the right side joint orientation.
        """
        self.right_side_fix = bool_value
        self.right_side_fix_axis = axis
    
    def set_control_orient(self, transform):
        """
        Set the orientation of the top and btm control based on the transform.
        
        Args:
            transform (str): The name of a transform.
        """
        
        self.control_orient = transform
    
    def set_negate_right_scale(self, bool_value):
        
        self.negate_right_scale = bool_value
    
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
            
            btm_control = cmds.spaceLocator(n = core.inc_name('locator_%s' % self._get_name()))[0]
            btm_xform = btm_control
            sub_btm_control = btm_control
            cmds.hide(btm_control)
            
            orient_translate = self.joints[-1]
            orient_rotate = self.control_orient
                    
            if not orient_rotate:
                orient_rotate = self.joints[0]
            
            space.MatchSpace(orient_translate, btm_control).translation()
            space.MatchSpace(orient_rotate, btm_control).rotation()
            
            self._fix_right_side_orient(btm_control)
            
            if self.negate_right_scale and self.side == 'R':
                cmds.setAttr('%s.scaleX' % btm_control, -1)
                cmds.setAttr('%s.scaleY' % btm_control, -1)
                cmds.setAttr('%s.scaleZ' % btm_control, -1)   
            

        
        
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
        
        space.create_follow_group(top_joint, mid_xform, use_duplicate = True)
        cmds.pointConstraint(top_control, sub_btm_control, mid_xform)
        
        spline_handle, curve = self._create_spline(top_joint, sub_btm_control, mid_control)
        
        self._setup_stretchy(curve, top_control)
        
        space.create_follow_group(top_control, top_joint)
        space.create_follow_group(sub_btm_control, sub_handle)
        
        top_twist = cmds.group(em = True, n = 'topTwist_%s' % spline_handle)
        btm_twist = cmds.group(em = True, n = 'btmTwist_%s' % spline_handle)
        
        space.MatchSpace(self.buffer_joints[0], top_twist).translation_rotation()
        
        space.MatchSpace(self.buffer_joints[-1], btm_twist).translation()
        space.MatchSpace(self.buffer_joints[0], btm_twist).rotation()
        
        
        
                
        cmds.setAttr('%s.dTwistControlEnable' % spline_handle, 1)
        cmds.setAttr('%s.dWorldUpType' % spline_handle, 4)
        
        cmds.connectAttr('%s.worldMatrix' % top_twist, '%s.dWorldUpMatrix' % spline_handle)
        cmds.connectAttr('%s.worldMatrix' % btm_twist, '%s.dWorldUpMatrixEnd' % spline_handle)
                
        cmds.parent(top_twist, top_control)
        #cmds.parent(btm_twist, sub_btm_control)
        
        cmds.pointConstraint(sub_btm_control, handle, mo = True)
        space.create_xform_group(handle)
        space.create_xform_group(sub_handle)
        
        cmds.parent(btm_xform, top_control)
        
        
        
        if self.top_guide:
            cmds.parentConstraint(self.top_guide, top_xform, mo =  True)
        
        if self.btm_guide:
            cmds.parent(btm_xform, self.btm_guide)
            
        cmds.parent(btm_twist, sub_joint)


class IkAppendageRig(BufferRig):
    """
    This is usually used for arms or legs.
    """
    
    def __init__(self, description, side=None):
        super(IkAppendageRig, self).__init__(description, side)
        
        self.create_twist = True
        self.create_stretchy = True
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
        self.pole_follow_transform = []
        self.pole_angle_joints = []
        self.top_control_right_side_fix = True
        self.stretch_axis = 'X'
        self.control_offset_axis = None
        self.negate_right_scale = False
        #dampen for legacy...
        self.damp_name = 'dampen'
        
        self.stretch_scale_attribute_offset = 1
        
    
    def _attach_ik_joints(self, source_chain, target_chain):
        
        for inc in range( 0, len(source_chain) ):
            source = source_chain[inc]
            target = target_chain[inc]
            
            cmds.parentConstraint(source, target)
            attr.connect_scale(source, target)
            
    def _duplicate_joints(self):
        
        super(IkAppendageRig, self)._duplicate_joints()
        
        duplicate = space.DuplicateHierarchy(self.joints[0])
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
        
        ik_handle = space.IkHandle( self._get_name() )
        
        ik_handle.set_start_joint( self.ik_chain[0] )
        ik_handle.set_end_joint( buffer_joint )
        ik_handle.set_solver(ik_handle.solver_rp)
        self.ik_handle = ik_handle.create()
        
        xform_ik_handle = space.create_xform_group(self.ik_handle)
        cmds.parent(xform_ik_handle, self.setup_group)
        
        cmds.hide(xform_ik_handle)
        
    def _create_top_control(self):
        
        if not self.top_as_locator:
            control = self._create_control(description = 'top')
            control.hide_scale_and_visibility_attributes()

            self.top_control = control.get()
            
        if self.top_as_locator:
            self.top_control = cmds.spaceLocator(n = 'locator_%s' % self._get_name())[0]
        
        return self.top_control
    
    def _xform_top_control(self, control):
        
        match = space.MatchSpace(self.ik_chain[0], control)
        match.translation_rotation()
        
        self._fix_right_side_orient(control)
        
        xform_group = space.create_xform_group(control)
        
        if self.negate_right_scale and self.side == 'R':
            
            cmds.setAttr('%s.scaleX' % xform_group, -1)
            cmds.setAttr('%s.scaleY' % xform_group, -1)
            cmds.setAttr('%s.scaleZ' % xform_group, -1)
        
        cmds.parentConstraint(control, self.ik_chain[0], mo = True)
        
        
        
        cmds.parent(xform_group, self.control_group)
    
    def _create_btm_control(self):
        
        control = self._create_control(description = 'btm')
        control.hide_scale_and_visibility_attributes()

        self.btm_control = control.get()
        
        self._fix_right_side_orient( control.get() )
        
        if self.create_sub_control:
            sub_control = self._create_control('BTM', sub = True)
            
            sub_control.hide_scale_and_visibility_attributes()
            
            xform_group = space.create_xform_group( sub_control.get() )
            
            self.sub_control = sub_control.get()
        
            cmds.parent(xform_group, control.get())
            
            self._connect_sub_visibility('%s.subVisibility' % self.btm_control, self.sub_control)
        
        return control.get()
    
    def _fix_right_side_orient(self, control):
        
        
        if not self.right_side_fix:
            return
    
        if not self.side == 'R':
            return
        
        
        
        xform_locator = cmds.spaceLocator()[0]
        
        match = space.MatchSpace(control, xform_locator)
        match.translation_rotation()
        
        spacer = space.create_xform_group(xform_locator)
        
        cmds.setAttr('%s.rotateY' % xform_locator, 180)
        cmds.setAttr('%s.rotateZ' % xform_locator, 180)
        
        match = space.MatchSpace(xform_locator, control)
        match.translation_rotation()
        
        cmds.delete(spacer)
        
    def _xform_btm_control(self, control):
        
        if self.match_btm_to_joint:
            space.MatchSpace(self.ik_chain[-1], control).translation_rotation()
            
        if not self.match_btm_to_joint:
            space.MatchSpace(self.ik_chain[-1], control).translation()
        
        self._fix_right_side_orient(control)
        
        xform_group = space.create_xform_group(control)
        drv_group = space.create_xform_group(control, 'driver')
        
        
        
        if self.negate_right_scale and self.side == 'R':
            
            cmds.setAttr('%s.scaleX' % xform_group, -1)
            cmds.setAttr('%s.scaleY' % xform_group, -1)
            cmds.setAttr('%s.scaleZ' % xform_group, -1)
        
        ik_handle_parent = cmds.listRelatives(self.ik_handle, p = True)[0]
        
        if self.sub_control:
            cmds.parent(ik_handle_parent, self.sub_control)
        if not self.sub_control:
            cmds.parent(ik_handle_parent, control)
        
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
        
        #local_group = self._create_group('IkLocal')
        local_group = cmds.duplicate(control, po = True, n = self._get_name('IkLocal'))[0]
        attr.remove_user_defined(local_group)
        shapes = cmds.listRelatives(local_group)
        if shapes:
            cmds.delete(shapes)
        
        
        world_group = self._create_group('IkWorld')
        match = space.MatchSpace(control, world_group)
        match.translation()
            
        if not self.right_side_fix and self.side == 'R':
            cmds.rotate(180,0,0, world_group)
            
            if cmds.getAttr('%s.scaleZ' % xform_group) < 0:
                #vtool.util.show( 'here setting scaleZ!')
                cmds.setAttr('%s.scaleZ' % world_group, -1)
                #cmds.duplicate(world_group)
        
        world_xform_group = space.create_xform_group(world_group)
        cmds.parent([local_group,world_xform_group], xform_group)
        
        cmds.orientConstraint(local_group, driver_group)
        cmds.orientConstraint(world_group, driver_group)
        
        constraint = space.ConstraintEditor()
        
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
        
        ik_handle = space.IkHandle(description)
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
            
            match = space.MatchSpace(self.sub_control, offset_locator)
            match.translation_rotation()
            
        if not self.sub_control:
            offset_locator = cmds.spaceLocator(n = 'offset_%s' % self.btm_control)[0]
            cmds.parent(offset_locator, self.btm_control)
            
            match = space.MatchSpace(self.btm_control, offset_locator)
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
        
        control = self._create_control('POLE', curve_type = 'cube')
        control.hide_scale_and_visibility_attributes()
        self.poleControl = control.get()
        
        attr.create_title(self.btm_control, 'POLE_VECTOR')
        
        pole_vis = attr.MayaNumberVariable('poleVisibility')
        pole_vis.set_variable_type(pole_vis.TYPE_BOOL)
        pole_vis.create(self.btm_control)
        
        twist_var = attr.MayaNumberVariable('twist')
        twist_var.create(self.btm_control)
        
        if self.side == 'L':
            twist_var.connect_out('%s.twist' % self.ik_handle)
            
        if self.side == 'R':
            attr.connect_multiply('%s.twist' % self.btm_control, '%s.twist' % self.ik_handle, -1)
        
        pole_joints = self._get_pole_joints()
        
        position = space.get_polevector( pole_joints[0], pole_joints[1], pole_joints[2], self.pole_offset )
        cmds.move(position[0], position[1], position[2], control.get())
        
        cmds.poleVectorConstraint(control.get(), self.ik_handle)
        
        xform_group = space.create_xform_group( control.get() )
        
        follow_group = None
        
        if self.create_twist:
            
            
            pole_locator = self._create_pole_follow()
            
            follow_group = space.create_follow_group(pole_locator, xform_group)
            xform_group = space.create_xform_group( control.get() )
            
            constraint = cmds.parentConstraint(self.twist_guide, follow_group, mo = True)[0]
            constraint_editor = space.ConstraintEditor()
            constraint_editor.create_switch(self.btm_control, 'autoTwist', constraint)
            cmds.setAttr('%s.autoTwist' % self.btm_control, 0)
            
        
        if not self.create_twist:
            if self.pole_follow_transform:
                follow_group = space.create_follow_group(self.pole_follow_transform, xform_group)
                
            
            if not self.pole_follow_transform:
                follow_group = xform_group
        
        if follow_group:
            cmds.parent(follow_group,  self.control_group )
        
        name = self._get_name()
        
        rig_line = rigs_util.RiggedLine(pole_joints[1], control.get(), name).create()
        cmds.parent(rig_line, self.control_group)
        
        pole_vis.connect_out('%s.visibility' % xform_group)
        pole_vis.connect_out('%s.visibility' % rig_line)
        
        self.pole_vector_xform = xform_group
        
    def _create_pole_follow(self):
        
        self.pole_follow_transform = vtool.util.convert_to_sequence(self.pole_follow_transform)
            
        pole_locator = cmds.spaceLocator(n = self._get_name('locator', 'pole'))[0]
        
        space.MatchSpace(self.poleControl, pole_locator).translation_rotation()
        cmds.parent(pole_locator, self.setup_group)
        
        self.pole_follow_transform.append(self.top_control)
        
        if len(self.pole_follow_transform) == 1:
            space.create_follow_group(self.pole_follow_transform[0], pole_locator)
        if len(self.pole_follow_transform) > 1:
            space.create_multi_follow(self.pole_follow_transform, pole_locator, self.poleControl, value = 0)
        
        return pole_locator
        
    def _create_stretchy(self, top_transform, btm_transform, control):
        stretchy = rigs_util.StretchyChain()
        
        stretchy.set_joints(self.ik_chain)
        #dampen should be damp... dampen means wet, damp means diminish
        stretchy.set_add_damp(True, self.damp_name)
        stretchy.set_node_for_attributes(control)
        stretchy.set_description(self._get_name())
        stretchy.set_scale_axis(self.stretch_axis)
        stretchy.set_scale_attribute_offset(self.stretch_scale_attribute_offset)
        
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
        """
        Wether to add an auto twist setup.
        """
        self.create_twist = bool_value
    
    def set_create_stretchy(self, bool_value):
        """
        Wether to add a stretchy setup.
        """
        self.create_stretchy = bool_value
    
    def set_stretch_axis(self, axis_letter):
        """
        What axis the stretch should scale on.
        
        Args:
            axis_letter (str): 'X','Y','Z'
        """
        self.stretch_axis = axis_letter
    
    def set_pole_offset(self, value):
        """
        Get the amount that the polevector control should offset from the elbow.
        
        Args:
            value (float)
        """
        self.pole_offset = value
    
    def set_pole_angle_joints(self, joints):
        """
        Set which joints the pole angle is calculated from.
        
        Args:
            joints (list): A list of of 3 joints that form a triangle. 
        """
        self.pole_angle_joints = joints
    
    def set_right_side_fix(self, bool_value):
        """
        Wether to compensate for right side orientation.
        """
        self.right_side_fix = bool_value
    
    def set_negate_right_scale(self, bool_value):
        """
        This will negate the scale of the right side making it better mirrored for cycles.
        """
        
        self.negate_right_scale = bool_value
    
    def set_orient_constrain(self, bool_value):
        """
        Wether the end effector control should orient constrain the ik handle.
        Default is True.
        """
        self.orient_constrain = bool_value
        
    def set_curve_type(self, curve_name):
        self.curve_type = curve_name
    
    def set_create_sub_control(self, bool_value):
        self.create_sub_control = bool_value
    
    def set_create_world_switch(self, bool_value):
        """
        Wether to create a world switch on the end effector control. 
        This can be used to have the end effector control orient to world if the character is in a-pose.
        """
        self.create_world_switch = bool_value
    
    def set_top_control_as_locator(self, bool_value):
        """
        Instead of a control curve for the top control, make it a locator.
        """
        self.top_as_locator = bool_value
    
    def set_match_btm_to_joint(self, bool_value):
        """
        Wether to match orientation of the end effector control to the btm joint, or just translation.
        Default is True.
        """
        self.match_btm_to_joint = bool_value
        
    def set_create_top_control(self, bool_value):
        """
        Wether to create a top control.
        """
        self.create_top_control = bool_value
    
    def set_pole_follow_transform(self, transform):
        """
        Set a transform for the pole to follow with a on/off switch on the pole control.
        
        Args:
            transform (str): The name of a transform.s
        """
        self.pole_follow_transform = transform
        
    def set_control_offset_axis(self, axis):
        """
        This will rotate the control shape cvs 90 on the axis, helping it to align better with different joint orientations.
        """
        axis = axis.lower()
        self.control_offset_axis = axis
    
    def set_damp_name(self, name):
        self.damp_name = name
    
    def set_stretch_scale_attribute_offset(self, value):
        self.stretch_scale_attribute_offset = value
    
    def _create_before_attach_joints(self):
        super(IkAppendageRig, self)._create_before_attach_joints()
        
        self._create_ik_handle()
        
        if self.create_top_control:
            top_control = self._create_top_control()
        if not self.create_top_control:
            top_control = cmds.spaceLocator(n = 'locator_top_%s' % self._get_name())[0]
            self.top_control = top_control
            space.MatchSpace(self.joints[0], top_control).translation_rotation()
            
        self._xform_top_control(top_control)
        
        btm_control = self._create_btm_control()
        self._xform_btm_control(btm_control)
        
        if self.create_twist:
            self._create_twist_joint(top_control)
        
        
        self._create_pole_vector()
        
        if self.create_stretchy:
            if self.sub_control:
                self._create_stretchy(top_control, self.sub_control, btm_control)
            if not self.sub_control:
                self._create_stretchy(top_control, self.btm_control, btm_control)
        
        
            
class TweakCurveRig(BufferRig):
    """
    TweakCurveRig is good for belts or straps that need to be riveted to a surface.
    """
    
    
    def __init__(self, name, side=None):
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
        
        self.follicle_ribbon = False
        
        
    
    def _create_control(self, sub = False):
        
        control = super(TweakCurveRig, self)._create_control(sub = sub)
        
        control.hide_scale_and_visibility_attributes()
        
        return control.get()
    
    def _create_ik_guide(self):
        
        if not self.use_ribbon:
            if not self.surface:
            
                name = self._get_name()
                
                self.surface = geo.transforms_to_curve(self.buffer_joints, self.control_count, name)
                
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
                surface = geo.transforms_to_nurb_surface(self.buffer_joints, self._get_name(self.description), spans = -1, offset_axis = self.ribbon_offset_axis, offset_amount = self.ribbon_offset)
                cmds.rebuildSurface(surface, ch = True, rpo = True, rt =  False,  end = True, kr = 0, kcp = 0, kc = 0, su = 1, du = 1, sv = self.control_count-1, dv = 3, fr = 0, dir = True)
        
                self.surface = surface
                
                cmds.parent(self.surface, self.setup_group)
    
    def _cluster(self, description):
        
        
        cluster_curve = deform.ClusterSurface(self.surface, self._get_name(description))
        cluster_curve.set_join_ends(True)
        cluster_curve.set_join_both_ends(self.join_both_ends)
        cluster_curve.create()
        
        self.cluster_handles = cluster_curve.handles
        self.cluster_deformers = cluster_curve.clusters
        
        
        return cluster_curve.get_cluster_handle_list()
        
    def set_control_count(self, int_value):
        
        self.control_count = int_value
        
    def set_use_ribbon(self, bool_value):
        self.use_ribbon = bool_value
        
    def set_ribbon(self, bool_value):
        self.use_ribbon = bool_value
    
    def set_ribbon_follicle(self, bool_value):
        self.follicle_ribbon = bool_value
        
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
            
            xform = space.create_xform_group(control)
            space.create_xform_group(control, 'driver')
            
            space.MatchSpace(cluster, xform).translation_to_rotate_pivot()
            
            if self.orient_controls_to_joints:
            
                if not self.orient_joint:
                    joint = space.get_closest_transform(cluster, self.buffer_joints)            
                    
                if self.orient_joint:
                    joint = self.orient_joint
                
                space.MatchSpace(joint, xform).translation_rotation()
            
            cmds.parentConstraint(control, cluster, mo = True)
            
            cmds.parent(xform, self.control_group)
        
        if core.has_shape_of_type(self.surface, 'nurbsCurve'):
            self.maya_type = 'nurbsCurve'
        if core.has_shape_of_type(self.surface, 'nurbsSurface'):
            self.maya_type = 'nurbsSurface'
            
        if self.attach_joints:
            for joint in self.buffer_joints:
                
                if self.maya_type == 'nurbsSurface':
                    if not self.follicle_ribbon:
                        rivet = geo.attach_to_surface(joint, self.surface)
                        cmds.parent(rivet, self.setup_group)
                    if self.follicle_ribbon:
                        follicle = geo.follicle_to_surface(joint, self.surface, constrain = True)
                        cmds.parent(follicle, self.setup_group)
                    
                if self.maya_type == 'nurbsCurve':
                    geo.attach_to_curve(joint, self.surface)
                    cmds.orientConstraint(self.control_group, joint)
                        
class RopeRig(CurveRig):

    def __init__(self, name, side=None):
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
        
        cluster_curve = deform.ClusterCurve(curve, self._get_name(description))
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

            curveObject = api.nodename_to_mobject(cmds.listRelatives(curve, s = True)[0])
            curve_object = api.NurbsCurveFunction(curveObject)
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
            
            control_group = cmds.group(em = True, n = core.inc_name('controls_%s' % (self._get_name(description))))
            setup_group = cmds.group(em = True, n = core.inc_name('setup_%s' % (self._get_name(description))))
            
            cmds.parent(control_group, self.control_group)
            cmds.parent(setup_group, self.setup_group)
            
            inc2 = 0
            
            for cluster in clusters:
                
                if description:
                    control = self._create_control(description)
                if not description:
                    control = self._create_control()
                
                if not alt_color:
                    if not self.control_color:
                        control.color(attr.get_color_of_side(self.side))
                    if self.control_color:
                        control.color = self.control_color    
                if alt_color:
                    control.color(attr.get_color_of_side(self.side, sub_color = True))
                
                space.MatchSpace(cluster, control.get()).translation_to_rotate_pivot()
                
                offset_cluster = cmds.group(em = True, n = 'offset_%s' % cluster)
                space.MatchSpace(cluster, offset_cluster).translation_to_rotate_pivot()
                
                xform_cluster = space.create_xform_group(cluster)
                
                cmds.parent(xform_cluster, offset_cluster)
                cmds.parent(offset_cluster, setup_group)
                
                xform_offset = space.create_xform_group(offset_cluster)
                
                
                control.scale_shape(scale, scale, scale) 
                
                
                xform = space.create_xform_group(control.get())
                attr.connect_translate(control.get(), cluster)
                
                control.hide_scale_attributes()
                
                if last_curve:
                    geo.attach_to_curve(xform, last_curve)
                    geo.attach_to_curve(xform_offset, last_curve)
                    
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
        self.negate_right_scale = False
        
        self.up_object = None
        self.up_axis = None
        
        self.control_parent = None
        self.setup_parent = None
        
        self.control_size = None
        
        self.orient_to_first_transform = False
        
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
        
    def set_control_size(self, size_value):
        self.control_size = size_value 
        
    def set_prefix(self, prefix):
        self.prefix = prefix
        
    def set_add_sub_joints(self, bool_value):
        self.add_sub_joints = bool_value
        
    def set_up_object(self, name):
        self.up_object = name
        
    def set_up_axis(self, axis_name):
        self.up_axis = axis_name.upper()
        
    def set_control_parent(self, name):
        self.control_parent = name
        
        if cmds.objExists(self.control_group) and cmds.objExists(name):
            cmds.parent(self.control_group, name)
        
    def set_setup_parent(self, name):
        self.setup_parent = name
        
        if cmds.objExists(self.setup_group) and cmds.objExists(name):
            cmds.parent(self.setup_group, name)
        
    def create(self):
        
        parent_joints = False
        
        if not self.joints:
            parent_joints = True
            joints = space.subdivide_joint(self.start_joint, 
                                     self.end_joint, 
                                     self.count, self.prefix, 
                                     '%s_1_%s' % (self.name,self.side), True)
            
                
            for joint in joints[:-1]:
                orient = space.OrientJoint(joint)
                
                if not self.up_object:
                    self.up_object = self.start_joint
                
                up_vector = None
                
                if self.up_axis:
                    
                    if self.up_axis == 'X':
                        up_vector = [1,0,0]
                    if self.up_axis == 'Y':
                        up_vector = [0,1,0]
                    if self.up_axis == 'Z':
                        up_vector = [0,0,1]
                    if self.up_axis == 'None':
                        up_vector = [0,0,0]
                
                orient.set_aim_up_at_object(self.up_object)
                
                if up_vector:
                    orient.set_world_up_vector(up_vector)
                    
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
        rig.set_negate_right_scale(self.negate_right_scale)
        if self.orient_to_first_transform:
            rig.set_control_orient(self.start_joint)
        rig.set_buffer(False)
        rig.set_right_side_fix(self.right_side_fix, self.right_side_fix_axis)
        
        if self.control_size:
            rig.set_control_size(self.control_size)
            
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
        
        if self.control_parent:
            try:
                cmds.parent(self.control_group, self.control_parent)
            except:
                pass
            
        if self.setup_parent:
            try:
                cmds.parent(self.setup_group, self.setup_parent)
            except:
                pass

        
    def get_control_group(self):
        return self.control_group
    
    def get_setup_group(self):
        return self.setup_group
    
    
    def get_joints(self):
        return self.joints
    
    def set_right_side_fix(self, bool_value, axis = 'x'):
        self.right_side_fix = bool_value
        self.right_side_fix_axis = axis

    def set_negate_right_scale(self, bool_value):
        self.negate_right_scale = bool_value
           
    def set_orient_to_first_transform(self, bool_value):
        
        self.orient_to_first_transform = bool_value
                          
#---Body Rig

class SpineRig(BufferRig, SplineRibbonBaseRig):
    
    def __init__(self, description, side=None):
        
        super(SpineRig, self).__init__(description, side)
        
        self.tweak_control_count = 2
        self.control_count = 1
        self.forward_fk = True
        self.btm_pivot = None
        self.top_pivot = None
        self.fk_pivots = []
        self.control_size = 1
        self.sub_control_size = .9
        
        self.top_hold_locator = None
        self.btm_hold_locator = None

        self.btm_color = None
        self.btm_curve_type = None
        self.top_color = None
        self.top_curve_type = None
        
        self.fk_color = None
        self.fk_curve_type = None
        self.sub_fk_count = 2
        self.sub_fk_color = None
        
        self.tweak_color = None
        self.tweak_curve_type = None

        self.orient_controls_to_joints = False
        
        self.create_buffer_joints = True
        self.stretch_on_off = True
        self.create_single_fk_follows = True
        self.create_sub_fk_controls = False
        self.create_sub_bottom_controls = False
        self.create_sub_top_controls = False

        self.hold_btm = True
        
        self.evenly_space_cvs = True
        
        self.sub_controls_dict = {}
        
    def _attach_joints(self, source_chain, target_chain):
        
        if not self.attach_joints:
            return
        
        self.top_hold_locator = cmds.spaceLocator(n = self._get_name('locator', 'holdTop'))[0]
        
        cmds.hide(self.top_hold_locator)
        
        space.MatchSpace(source_chain[-1], self.top_hold_locator).translation_rotation()
        
        parent = cmds.listRelatives(target_chain[0], p = True)
        
        if parent:
            cmds.parent(target_chain[-1], parent)
            xform = space.create_xform_group(target_chain[-1])
            space.create_xform_group(target_chain[-1], 'buffer')
            cmds.reorder(xform, r = -1)
        
        temp_source = list(source_chain)
        temp_source[-1] = self.top_hold_locator
        
        if self.hold_btm:
        
            self.btm_hold_locator = cmds.spaceLocator(n = self._get_name('locator', 'holdBtm'))[0]
            cmds.hide(self.btm_hold_locator)
            space.MatchSpace(source_chain[0], self.btm_hold_locator).translation_rotation()
            temp_source[0] = self.btm_hold_locator
        
        space.AttachJoints(temp_source, target_chain).create()
        
        if cmds.objExists('%s.switch' % target_chain[0]):
            switch = rigs_util.RigSwitch(target_chain[0])
            
            weight_count = switch.get_weight_count()
            
            if weight_count > 0:
                if self.auto_control_visibility:
                    switch.add_groups_to_index((weight_count-1), self.control_group)
                switch.create()
        
    def _create_before_attach_joints(self):
        super(SpineRig, self)._create_before_attach_joints()
        
        self._attach_to_geo()
        
        
    def _create_curve(self, span_count):
        
        if not self.curve:
            
            name = self._get_name()
            
            self.orig_curve = geo.transforms_to_curve(self.joints, span_count, name)
            cmds.setAttr('%s.inheritsTransform' % self.orig_curve, 0)
        
            self.curve = cmds.duplicate(self.orig_curve)[0]
            
            cmds.rebuildCurve(self.curve, 
                              spans = (span_count),
                              rpo = True,  
                              rt = 0, 
                              end = 1, 
                              kr = False, 
                              kcp = False, 
                              kep = True,  
                              kt = True,
                              d = 2)
        
            if self.evenly_space_cvs:
                geo.evenly_position_curve_cvs(self.curve, match_curve = self.orig_curve)
            
            
            name = self.orig_curve
            
            self.orig_curve = cmds.rename(self.orig_curve, core.inc_name('orig_curve'))
            self.curve = cmds.rename(self.curve, name)
            cmds.parent(self.orig_curve, self.setup_group)
            
            cmds.parent(self.curve, self.setup_group)         
        
    def _create_clusters(self):
        
        if self.ribbon:
            cluster_surface = deform.ClusterSurface(self.surface, self.description)
        if not self.ribbon:
            cluster_surface = deform.ClusterCurve(self.curve, self.description)
            
        cluster_surface.set_join_ends(False)
        cluster_surface.create()
        
        self.clusters = cluster_surface.handles
        cluster_group = self._create_setup_group('clusters')
        cmds.parent(self.clusters, cluster_group)
        
        return self.clusters
        
    def _wire_hires(self, curve):
        
        self.ik_curve = curve

        
    def _attach_to_geo(self):
        if not self.attach_joints:
            return
        
        if self.ribbon:
            rivet_group = self._create_setup_group('rivets')
        
            for joint in self.buffer_joints:
                rivet = geo.attach_to_surface(joint, self.surface)
                cmds.setAttr('%s.inheritsTransform' % rivet, 0)
                cmds.parent(rivet, rivet_group)
        
        if not self.ribbon:
            self._create_spline_ik()
    
    def _orient_to_closest_joint(self, xform):
        
        if not self.orient_controls_to_joints:
            return
        
        orient_joint = space.get_closest_transform(xform, self.buffer_joints)
        space.MatchSpace(orient_joint, xform).rotation()
    
    def _create_btm_control(self):
        
        control = self._create_control(curve_type = self.btm_curve_type)
        control.hide_scale_attributes()
        control.scale_shape(1.4,1.4,1.4)
        
        if self.btm_color != None:
            control.color(self.btm_color)
        
        control = control.control
        
        if self.create_sub_bottom_controls:
            self._create_sub_controls(control, None, self.btm_curve_type)
        
        xform = space.create_xform_group(control)
        space.MatchSpace(self.joints[0], xform).translation()
        
        if self.btm_pivot:
            self._set_pivot_vector(xform, self.btm_pivot)
        
        self._orient_to_closest_joint(xform)
        
        cmds.parent(xform, self.control_group)
        
        self.btm_control = control
        
    def _create_top_control(self):
        
        control = self._create_control(curve_type = self.top_curve_type)
        control.hide_scale_attributes()
        control.scale_shape(1.4,1.4,1.4)
        
        if self.top_color != None:
            control.color(self.top_color)
        
        control = control.control
        
        if self.create_sub_top_controls:
            self._create_sub_controls(control, None, self.top_curve_type)
        
        xform = space.create_xform_group(control)
        
        space.MatchSpace(self.joints[-1], xform).translation()
        
        if self.top_pivot:
            self._set_pivot_vector(xform, self.top_pivot)
            
        self._orient_to_closest_joint(xform)
        
        cmds.parent(xform, self.control_group)
        
        self.top_control = control
                
    def _create_tweak_controls(self):
        
        group = self._create_control_group('tweak')
        
        follow = 0
        
        sub_follow = 1.0/(len(self.clusters) - 2)
        
        self.tweak_controls = []
        
        for cluster in self.clusters:
            
            control = self._create_control(sub = True, curve_type = self.tweak_curve_type)
            
            control.hide_scale_attributes()
            
            if self.tweak_color != None:
                control.color(self.tweak_color)
            
            control = control.control
            
            xform = space.create_xform_group(control)

            space.MatchSpace(cluster, xform).translation_to_rotate_pivot()
            
            self._orient_to_closest_joint(xform)
            
            cmds.parentConstraint(control, cluster)
                        
            if follow > 1:
                follow = 1
            
            cmds.parent(xform, group)
            
            top_control = self.top_control
            btm_control = self.btm_control
            
            if top_control in self.sub_controls_dict:
                top_control = self.sub_controls_dict[top_control][-1]
            
            if btm_control in self.sub_controls_dict:
                btm_control = self.sub_controls_dict[btm_control][-1]
            
            if cluster != self.clusters[0] and cluster != self.clusters[-1]:
                space.create_multi_follow([btm_control, top_control], xform, control, attribute_name = 'follow', value = follow)
                
            if cluster == self.clusters[0]:
                cmds.parent(xform, btm_control)
            if cluster == self.clusters[-1]:
                cmds.parent(xform, top_control)
                
            self.tweak_controls.append(control)
            
            
            self._connect_sub_visibility('%s.tweakVisibility' % self.top_control, control)
            
            follow += sub_follow
        
    def _create_sub_controls(self, control, description, curve_type):
            
        subs = []
                
        for inc in range(0,self.sub_fk_count):
            
            number = vtool.util.get_last_number(control)
            
            if not description:
                description = number
            
            sub_control = self._create_control(sub =  True, description = description, curve_type = curve_type)
            
            attr.connect_message(sub_control, control, 'group_sub')
            
            if inc == 1:    
                sub_control.scale_shape(0.9, 0.9, 0.9)
                
            if self.sub_fk_color:
                sub_control.color(self.sub_fk_color)
                                    
            sub_control.hide_scale_and_visibility_attributes()
            
            space.MatchSpace(control, sub_control.get()).translation_rotation()
            
            self._connect_sub_visibility('%s.subVisibility' % control, sub_control.get())
            
            if not subs:
                cmds.parent(sub_control.get(), control)
            if subs:
                cmds.parent(sub_control.get(), subs[-1])
                
            subs.append(sub_control.get())
            
        self.sub_controls_dict[control] = subs    
        
            
    def _create_fk_controls(self):
        
        group = self._create_control_group('fk')
        
        if not self.control_count:
            return
        
        xforms = []
        controls = []
        
        for inc in range(0, self.control_count):
            
            control = self._create_control(description = 'mid', curve_type = self.fk_curve_type)
            control.hide_scale_attributes()
            
            if self.fk_color != None:
                control.color(self.fk_color)          
            
            control = control.control
            
            xform = space.create_xform_group(control)
            
            xforms.append(xform)
            controls.append(control)
            
            cmds.parent(xform, group)
            
            shapes = cmds.listRelatives(control, shapes = True)
            
            for shape in shapes:
                attr.connect_visibility('%s.fkVisibility' % self.top_control, shape, 1)    

            if self.create_sub_fk_controls:
        
                self._create_sub_controls(control, 'mid_%s' % (inc+1), self.fk_curve_type)
                
                    
        self._snap_transforms_to_curve(xforms, self.curve)
        
        pivot_count = len(self.fk_pivots)
        xform_count = len(xforms)
        
        for inc in range(0, pivot_count):
            
            if inc > xform_count - 1:
                break
            
            transform = xforms[inc]
            
            self._set_pivot_vector(transform, self.fk_pivots[inc])
            
        if self.forward_fk == False:
            xforms.reverse()
            controls.reverse()
        
        last_control = None
        
        for inc in range(0, len(controls)):
            
            xform = xforms[inc]
            control = controls[inc]
            
            self._orient_to_closest_joint(xform)
            
            if last_control:
                if not self.sub_controls_dict:
                    cmds.parent(xform, last_control)
                if self.sub_controls_dict:
                    cmds.parent(xform, self.sub_controls_dict[last_control][-1])
                    
            last_control = control
        
        if self.forward_fk == True:
            top_xform = space.get_xform_group(self.top_control)
        if self.forward_fk == False:
            top_xform = space.get_xform_group(self.btm_control)
            
        if not self.sub_controls_dict:
            cmds.parent(top_xform, last_control)
        if self.sub_controls_dict:
            cmds.parent(top_xform, self.sub_controls_dict[last_control][-1])
        
        self.fk_controls = controls
        
    def _create_mid_follow(self):
        
        if not self.create_single_fk_follows:
            return
        
        if self.control_count == 1:
            
            if self.forward_fk == False:
                value1 = 0
                value2 = 1
            if self.forward_fk == True:
                value1 = 1
                value2 = 0
            
            fk_control = self.controls[-1]
            if self.sub_controls_dict:
                fk_control = self.sub_controls_dict[fk_control][-1]
            
            space.create_multi_follow([self.control_group, fk_control], space.get_xform_group(self.top_control), self.top_control, value = value1 )
            space.create_multi_follow([self.control_group, fk_control], space.get_xform_group(self.btm_control), self.btm_control, value = value2 )
        
    def _snap_transforms_to_curve(self, transforms, curve):
        
        count = len(transforms) + 2
            
        total_length = cmds.arclen(curve)
        
        part_length = total_length/(count-1)
        
        if count-1 == 0:
            part_length = 0
            
        current_length = part_length
        
        temp_curve = cmds.duplicate(curve)[0]
        
        for inc in range(0, count-2):
            
            param = geo.get_parameter_from_curve_length(temp_curve, current_length)
            position = geo.get_point_from_curve_parameter(temp_curve, param)
            
            transform = transforms[inc]
            
            if cmds.nodeType(transform) == 'joint':
                
                cmds.move(position[0], position[1], position[2], '%s.scalePivot' % transform, 
                                                                '%s.rotatePivot' % transform, a = True)            
            
            if not cmds.nodeType(transform) == 'joint':
                cmds.xform(transform, ws = True, t = position)
            
            current_length += part_length  
        
        cmds.delete(temp_curve)
        
    def _set_pivot_vector(self, transform, value):
        list_value = vtool.util.convert_to_sequence(value)
        
        if len(list_value) == 3:
            vector_value = list_value
            cmds.xform(transform, os = True, t = vector_value, r = True)
    
        if len(list_value) == 1:
            if cmds.nodeType(list_value[0]) == 'transform' or cmds.nodeType(list_value[0]) == 'joint':
                vector_value = cmds.xform(list_value[0], q = True, t = True, ws = True)
                cmds.xform(transform, ws = True, t = vector_value)
            
    def set_tweak_control_count(self, control_count):
        """
        Set the number of sub controls
        """
        
        if control_count < 1:
            control_count = 1
            
        self.tweak_control_count = control_count
    
    def set_tweak_control_shape(self, curve_type):    
        self.tweak_curve_type
        
    def set_tweak_control_color(self, color_value):
        self.tweak_color = color_value
        
    def set_bottom_pivot(self, value):

        self.btm_pivot = value
    
    def set_bottom_control_shape(self, curve_type):
        self.btm_curve_type = curve_type
        
    def set_bottom_control_color(self, color_value):
        self.bottom_color = color_value
    
    def set_create_bottom_sub_controls(self, bool_value):
        self.create_sub_bottom_controls = bool_value
    
    def set_top_pivot(self, value):
        
        self.top_pivot = value        
        
    def set_top_control_shape(self, curve_type):
        self.top_curve_type = curve_type
        
    def set_top_control_color(self, color_value):
        self.top_color = color_value

    def set_create_top_sub_controls(self, bool_value):
        self.create_sub_top_controls = bool_value

    def set_fk_control_count(self, control_count):
        """
        Set the number of fk controls.
        """
        if control_count < 0:
            control_count = 0
        
        self.control_count = control_count
        
    def set_fk_control_one_sub(self, bool_value):
        
        if bool_value:
            self.sub_fk_count = 1
            
    def set_fk_control_sub_color(self, number):
        
        self.sub_fk_color = number
        
    def set_fk_pivots(self, values):
        
        list_values = vtool.util.convert_to_sequence(values)
            
        self.fk_pivots = list_values
    
    def set_fk_forward(self, bool_value):
        self.forward_fk = bool_value
        
    def set_fk_control_shape(self, curve_type):
        
        self.fk_curve_type = curve_type
        
    def set_fk_control_color(self, color_value):
        self.fk_color = color_value
    
    def set_fk_single_control_follow(self, bool_value):
        self.create_single_fk_follows = bool_value
    
    def set_create_fk_sub_controls(self, bool_value):
        
        self.create_sub_fk_controls = bool_value
    
    def set_orient_controls_to_joints(self, bool_value):
        
        self.orient_controls_to_joints = bool_value
    
    def set_hold_bottom_joint(self, bool_value):
        
        self.hold_btm = bool_value
    
    def set_evenly_space_cvs(self, bool_value):
        self.evenly_space_cvs = bool_value
    
    def create(self):
        
        self._create_geo(self.tweak_control_count)
        
        if self.ribbon:
            geo = self.surface
        if not self.ribbon:
            geo = self.curve
        
        self._create_clusters()
        
        super(SpineRig, self).create()
        
        self._create_btm_control()
        self._create_top_control()
        
        self._create_tweak_controls()
        self._create_fk_controls()
        
        self._create_mid_follow()
        
        cmds.parent(self.end_locator, self.tweak_controls[-1])
        cmds.parent(self.start_locator, self.tweak_controls[0])
        
        self._setup_stretchy(self.top_control)
        
        if self.stretch_on_off:
            cmds.setAttr('%s.stretchOnOff' % self.top_control, 1)
        
        if self.top_hold_locator:
            cmds.parent(self.top_hold_locator, self.top_control)
            
            if self.stretch_on_off:
                space.create_multi_follow([self.buffer_joints[-1], self.tweak_controls[-1]], self.top_hold_locator, constraint_type = 'pointConstraint')
                cmds.orientConstraint(self.tweak_controls[-1], self.top_hold_locator, mo = True)
                cmds.connectAttr('%s.stretchOnOff' % self.top_control, '%s.follow' % self.top_hold_locator)
            
            if not self.stretch_on_off:
                cmds.parentConstraint(self.tweak_controls[-1], self.top_hold_locator, mo = True)
            
        if self.btm_hold_locator:
            cmds.parent(self.btm_hold_locator, self.btm_control)
            
            if self.stretch_on_off:
                space.create_multi_follow([self.buffer_joints[0], self.tweak_controls[0]], self.btm_hold_locator, constraint_type = 'pointConstraint')
                cmds.orientConstraint(self.tweak_controls[0], self.btm_hold_locator, mo = True)
                cmds.connectAttr('%s.stretchOnOff' % self.top_control, '%s.follow' % self.btm_hold_locator)
                
            if not self.stretch_on_off:
                cmds.parentConstraint(self.tweak_controls[0], self.btm_hold_locator, mo = True)
        
    def get_tweak_controls(self):
        
        return self.tweak_controls
    
    def get_fk_controls(self):
        
        return self.fk_controls
    
    def get_top_and_btm_controls(self):
        
        return [self.top_control, self.btm_control]
            
class NeckRig(FkCurveRig):
    def __init__(self, description, side=None):
        super(NeckRig, self).__init__(description,side)
        
    def _first_increment(self, control, current_transform):
        self.first_control = control

class IkLegRig(IkAppendageRig):
    
    def __init__(self, description, side=None):
        
        super(IkLegRig, self).__init__(description,side)
    
    def _fix_right_side_orient(self, control, axis = 'yz'):
        
        
        
        if not self.right_side_fix:
            return
    
        if not self.side == 'R':
            return
        
        xform_locator = cmds.spaceLocator()[0]
        
        match = space.MatchSpace(control, xform_locator)
        match.translation_rotation()
        
        spacer = space.create_xform_group(xform_locator)
        
        for letter in axis:
        
            cmds.setAttr('%s.rotate%s' % (xform_locator, letter.upper()), 180)
        
        match = space.MatchSpace(xform_locator, control)
        match.translation_rotation()
        
        cmds.delete(spacer)
           
    def _xform_top_control(self, control):
        
        match = space.MatchSpace(self.ik_chain[0], control)
        match.translation_rotation()
        
        self._fix_right_side_orient(control, 'z')
        
        cmds.parentConstraint(control, self.ik_chain[0], mo = True)
        
        xform_group = space.create_xform_group(control)
        
        cmds.parent(xform_group, self.control_group)
            
    def _create_pole_vector(self):
        
        control = self._create_control('POLE', curve_type = 'cube')
        control.hide_scale_and_visibility_attributes()
        self.poleControl = control.get()
        
        attr.create_title(self.btm_control, 'POLE_VECTOR')
                
        pole_vis = attr.MayaNumberVariable('poleVisibility')
        pole_vis.set_variable_type(pole_vis.TYPE_BOOL)
        pole_vis.create(self.btm_control)
        
        twist_var = attr.MayaNumberVariable('twist')
        twist_var.create(self.btm_control)
        
        if self.side == 'L':
            twist_var.connect_out('%s.twist' % self.ik_handle)
            
        if self.side == 'R':
            attr.connect_multiply('%s.twist' % self.btm_control, '%s.twist' % self.ik_handle, -1)
            #connect_reverse('%s.twist' % self.btm_control, '%s.twist' % self.ik_handle)
            
        pole_joints = self._get_pole_joints()
        
        position = space.get_polevector( pole_joints[0], pole_joints[1], pole_joints[2], self.pole_offset )
        cmds.move(position[0], position[1], position[2], control.get())

        match = space.MatchSpace(self.btm_control, control.get())
        match.rotation()
        
        cmds.poleVectorConstraint(control.get(), self.ik_handle)
        
        xform_group = space.create_xform_group( control.get() )
        
        if self.create_twist:
            
            follow_group = space.create_follow_group(self.top_control, xform_group)
            constraint = cmds.parentConstraint(self.twist_guide, follow_group, mo = True)[0]
            
            constraint_editor = space.ConstraintEditor()
            constraint_editor.create_switch(self.btm_control, 'autoTwist', constraint)
            cmds.setAttr('%s.autoTwist' % self.btm_control, 1)
            
            twist_offset = attr.MayaNumberVariable('autoTwistOffset')
            twist_offset.create(self.btm_control)
            
            if self.side == 'L':
                twist_offset.connect_out('%s.rotateY' % self.offset_pole_locator)
            if self.side == 'R':
                attr.connect_multiply('%s.autoTwistOffset' % self.btm_control, 
                                '%s.rotateY' % self.offset_pole_locator, -1)
        
        if not self.create_twist:
            follow_group = space.create_follow_group(self.top_control, xform_group)
        
        cmds.parent(follow_group,  self.control_group )
        
        name = self._get_name()
        
        rig_line = rigs_util.RiggedLine(pole_joints[1], control.get(), name).create()
        cmds.parent(rig_line, self.control_group)
        
        pole_vis.connect_out('%s.visibility' % xform_group)
        pole_vis.connect_out('%s.visibility' % rig_line) 
    

class IkFrontLegRig(IkAppendageRig):
    
    
    def __init__(self, description, side=None):
        super(IkFrontLegRig, self).__init__(description, side)
        
        self.right_side_fix = False
    
    def _create_top_control(self):
        
        self.top_control = super(IkFrontLegRig, self)._create_top_control()
        
        if not core.has_shape_of_type(self.top_control, 'spaceLocator'):
            control = rigs_util.Control(self.top_control)
            control.rotate_shape(0, 0, 90)
    
        return self.top_control
    
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
        
        control = self._create_control('POLE', curve_type='cube')
        control.hide_scale_and_visibility_attributes()
        self.poleControl = control.get()
        
        attr.create_title(self.btm_control, 'POLE_VECTOR')
        
        pole_vis = attr.MayaNumberVariable('poleVisibility')
        pole_vis.set_variable_type(pole_vis.TYPE_BOOL)
        
        if self.sub_visibility:
            pole_vis.set_value(1)
        
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
            
            if not self.pole_follow_transform:
                cmds.parentConstraint(self.twist_guide, xform_group, mo = True)[0]
            if self.pole_follow_transform:
                sequence = vtool.util.convert_to_sequence(self.pole_follow_transform)
                sequence.append(self.twist_guide)
                
                space.create_multi_follow_direct(sequence, xform_group, self.poleControl)
            
            follow_group = xform_group
            
            #constraint_editor = util.ConstraintEditor()
            
            
            space.create_multi_follow([self.off_offset_locator, self.offset_locator], self.twist_guide_ik, self.btm_control, attribute_name = 'autoTwist', value = 0)
                        
        
        
        if not self.create_twist:
            if self.pole_follow_transform:
                follow_group = space.create_follow_group(self.pole_follow_transform, xform_group)
                
            
            if not self.pole_follow_transform:
                follow_group = xform_group
        
        if follow_group:
            cmds.parent(follow_group,  self.control_group )
        
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
        stretchy.set_scale_axis(self.stretch_axis)
        stretchy.set_scale_attribute_offset(self.stretch_scale_attribute_offset)
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
        
    def _create_before_attach_joints(self):
        super(IkFrontLegRig, self)._create_before_attach_joints()
        
        cmds.setAttr('%s.translateY' % self.pole_vector_xform, 0)
        
        ik_xform = cmds.listRelatives(self.ik_handle, p = True)
        cmds.parent(ik_xform, self.offset_locator)
        

class IkScapulaRig(BufferRig):
    
    def __init__(self, description, side=None):
        
        self.control_shape = 'square'
        
        super(IkScapulaRig, self).__init__(description, side)
        
        self.control_offset = 10
        
        self.create_rotate_control = False
        self.ik_joints = None
        
        self.negate_right_scale = False
        
        self.offset_axis = 'X'
        self.rotate_control = None
        
    def _duplicate_scapula(self):
        
        duplicate = space.DuplicateHierarchy(self.joints[0])
        duplicate.stop_at(self.joints[-1])
        duplicate.replace('joint', 'ik')
        joints = duplicate.create()
        
        self.ik_joints = joints
        cmds.parent(self.ik_joints[0], self.setup_group)
        
        
    
    def _create_top_control(self):
        control = self._create_control()
        control.hide_scale_and_visibility_attributes()
        
        self._offset_control(control)
        
        cmds.parent(control.get(), self.control_group)
        
        xform = space.create_xform_group(control.get())
        

        if self.side == 'R':

            if self.negate_right_scale:
                cmds.setAttr('%s.scaleZ' % xform, -1)
                cmds.setAttr('%s.rotateY' % xform, 180)
                
        return control.get()
    
    def _create_shoulder_control(self):
        
        control = self._create_control()
        control.hide_scale_and_visibility_attributes()
        
        ik_joints = self.joints
        
        if self.ik_joints:
            ik_joints = self.ik_joints
        
        cmds.parent(control.get(), self.control_group)
        
        space.MatchSpace(self.joints[0], control.get()).translation()
        
        xform = space.create_xform_group(control.get())
        
        space.create_xform_group(control.get(), 'driver')
        
        if self.side == 'R':
            
            if self.negate_right_scale:
                cmds.setAttr('%s.scaleZ' % xform, -1)
                cmds.setAttr('%s.rotateY' % xform, 180)
                
        cmds.parentConstraint(control.get(), ik_joints[0], mo = True)
        
        self.shoulder_control = control.get()
        
        return control.get()
    
    def _offset_control(self, control ):
        
        offset = cmds.group(em = True)
        match = space.MatchSpace(self.joints[-1], offset)
        match.translation_rotation()
        
        if self.offset_axis == 'X':
            vector = [self.control_offset, 0,0] 
        if self.offset_axis == 'Y':
            vector = [0, self.control_offset, 0]
        if self.offset_axis == 'Z':
            vector = [0,0, self.control_offset]
        
        cmds.move(vector[0],vector[1],vector[2] , offset, os = True, wd = True, r = True)
        
        match = space.MatchSpace(offset, control.get())
        match.translation()
        
        cmds.delete(offset)
        
    def _create_ik(self, control):
        
        ik_joints = self.joints
        
        if self.ik_joints:
            ik_joints = self.ik_joints
        
        handle = space.IkHandle(self._get_name())
        handle.set_start_joint(ik_joints[0])
        handle.set_end_joint(ik_joints[-1])
        handle.set_solver(handle.solver_sc)
        handle = handle.create()
        
        #cmds.pointConstraint(control, handle)
        
        xform = space.create_xform_group(handle)
        
        cmds.parent(xform, control)
        cmds.hide(handle)
        
    def _create_rotate_control(self):
        
        control = self._create_control('rotate')
        control.hide_scale_and_visibility_attributes()
        
        cmds.parent(control.get(), self.control_group)
        
        space.MatchSpace(self.joints[0], control.get()).translation_rotation()
        self.xform_rotate = space.create_xform_group(control.get())
        
        space.create_xform_group(control.get(), 'driver')
        
        
        self.rotate_control = control.get()
        
        
    def set_control_offset(self, value):
        self.control_offset = value
    
    def set_create_rotate_control(self, bool_value):
        self.create_rotate_control = bool_value
    
    def set_negate_right_scale(self, bool_value):
        self.negate_right_scale = bool_value
    
    def set_offset_axis(self, axis_letter):
        
        axis_letter = axis_letter.upper()
        
        self.offset_axis = axis_letter
    
    def create(self):
        super(IkScapulaRig, self).create()
        
        if self.create_rotate_control:
            self._duplicate_scapula()
        
        
        control = self._create_top_control()
        self._create_shoulder_control()
        
        self._create_ik(control)
        
        rig_line = rigs_util.RiggedLine(control, self.joints[-1], self._get_name()).create()
        cmds.parent(rig_line, self.control_group)
        
        attr.create_title(self.shoulder_control, 'Scapula')
        
        cmds.addAttr(self.shoulder_control, ln = 'aimVisibility', at = 'bool', k = True)
        
        
        if self.create_rotate_control:
            
            self._create_rotate_control()
        
        cmds.connectAttr('%s.aimVisibility' % self.shoulder_control, '%s.visibility' % rig_line)
        cmds.connectAttr('%s.aimVisibility' % self.shoulder_control, '%sShape.visibility' % control)
        
        if self.create_rotate_control:
            cmds.parent(self.xform_rotate, self.shoulder_control)
            space.create_follow_group( self.ik_joints[0], self.xform_rotate, use_duplicate = True)
            #cmds.parent(follow, self.shoulder_control)
            
            
        if self.negate_right_scale and self.side == 'R':
            
            cmds.setAttr('%s.scaleX' % self.xform_rotate, -1)
            cmds.setAttr('%s.scaleY' % self.xform_rotate, -1)
            cmds.setAttr('%s.scaleZ' % self.xform_rotate, -1)
        
        
        if self.rotate_control:
            cmds.parentConstraint(self.rotate_control, self.joints[0],mo = True)
        
class IkBackLegRig(IkFrontLegRig):
    
    def __init__(self, description, side=None):
        super(IkBackLegRig, self).__init__(description, side)
        
        self.offset_control_to_locator = False
        self.right_side_fix = False
        self._offset_ankle_axis = 'Z'
    
    def _duplicate_joints(self):
        
        super(IkBackLegRig, self)._duplicate_joints()
        
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
            
            cmds.connectAttr('%s.scale%s' % (self.ik_chain[inc],self.stretch_axis), 
                             '%s.scale%s' % (self.offset_chain[inc], self.stretch_axis))
        
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
        
        cmds.connectAttr('%s.scale%s' % (self.offset_chain[-2], self.stretch_axis), '%s.scale%s' % (self.lower_offset_chain[0], self.stretch_axis))
        
        cmds.delete(self.offset_chain[-1])
        self.offset_chain.pop(-1)
        
        cmds.orientConstraint(self.lower_offset_chain[0], self.offset_chain[-1])
        

    def _get_pole_joints(self):
        
        if not self.pole_angle_joints:
        
            return [self.ik_chain[0], self.ik_chain[1], self.ik_chain[2]]
            
        return self.pole_angle_joints
                
        
    def _create_offset_control(self):

        if not self.offset_control_to_locator:
            control = self._create_control(description = 'offset', curve_type='square')
            control.hide_scale_and_visibility_attributes()
            control.scale_shape(2, 2, 2)
            
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
        
        offset.connect_out('%s.rotate%s' % (driver_group, self._offset_ankle_axis))
        
        follow_group = space.create_follow_group(self.ik_chain[-2], xform_group)
        
        scale_constraint = cmds.scaleConstraint(self.ik_chain[-2], follow_group)[0]
        space.scale_constraint_to_local(scale_constraint)
        
        if not self.negate_right_scale:
            cmds.parent(follow_group, self.top_control)
        if self.negate_right_scale:
            xform = space.create_xform_group(follow_group)
            cmds.parent(xform, self.top_control)
        
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
    
    def set_offset_ankle_axis(self, axis_letter):
        axis_letter = axis_letter.capitalize()
        self._offset_ankle_axis = axis_letter
    
    def _create_before_attach_joints(self):
        super(IkBackLegRig, self)._create_before_attach_joints()
        
        self._create_offset_control()
        
        self._rig_offset_chain()
        

    
class RollRig(JointRig):
    
    def __init__(self, description, side=None):
        super(RollRig, self).__init__(description, side)
        
        self.create_roll_controls = True
        self.attribute_control = None
        self.attribute_control_shape = 'square'
        
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
        
        duplicate = space.DuplicateHierarchy(self.joints[0])
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
        
        match = space.MatchSpace(source_transform, group)
        match.translation_rotation()
        
        xform_group = space.create_xform_group(group)
        
        attribute_control = self._get_attribute_control()
        
        cmds.addAttr(attribute_control, ln = '%sPivot' % description, at = 'double', k = True)
        
        
        cmds.connectAttr('%s.%sPivot' % (attribute_control, description), '%s.rotateY' % group)
        
        if self.right_side_fix and self.side == 'R':
            
            attr.insert_multiply('%s.rotateY' % group, -1) 
        
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
            control = cmds.group(em = True, n = core.inc_name(name))
        
        xform_group = space.create_xform_group(control)
        driver_group = space.create_xform_group(control, 'driver')
        
        match = space.MatchSpace(source_transform, xform_group)
        match.translation_rotation()
        
        if self.create_roll_controls:
            
            control_object.hide_scale_attributes()
            control_object.hide_translate_attributes()
            control_object.hide_visibility_attribute()
            
        if self.create_roll_controls:
            
            cmds.connectAttr('%s.controlVisibility' % self._get_attribute_control(), '%sShape.visibility' % control)
        
        return control, xform_group, driver_group
    
    def _create_roll_control(self, transform):
        
        roll_control = self._create_control('roll', curve_type= self.attribute_control_shape) 
        
        self.roll_control = roll_control
        
        roll_control.scale_shape(.8,.8,.8)
        
        xform_group = space.create_xform_group(roll_control.get())
        
        roll_control.hide_keyable_attributes()
        
        match = space.MatchSpace( transform, xform_group )
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
                    
                    constraint_editor = space.ConstraintEditor()
                    constraint_editor.create_switch(self.roll_control.get(), self.ik_attribute, constraint)
                    
                    self.ik_chain.append(joint_chain1[inc])
                    self.fk_chain.append(joint_chain2[inc])
                    
        space.AttachJoints(joints_attach_1, target_joints).create()
        space.AttachJoints(joints_attach_2, target_joints).create()
        
        cmds.connectAttr('%s.%s' % (self.roll_control.get(), self.ik_attribute), '%s.switch' % target_joints[0] )
                 
    def _create_ik_fk_attribute(self):
        
        attr.create_title(self.roll_control.get(), 'IK_FK')
        ik_fk = attr.MayaNumberVariable(self.ik_attribute)
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
    
    def set_attribute_control_shape(self, shape_name):
        self.attribute_control_shape = shape_name
    
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
        
        
        attr.create_title(self._get_attribute_control(), 'FOOT_PIVOTS')
                
        if self.create_roll_controls:
            bool_var = attr.MayaNumberVariable('controlVisibility')
            bool_var.set_variable_type(bool_var.TYPE_BOOL)
            bool_var.create(self._get_attribute_control())
            bool_var.set_value(self.sub_visibility)
        
    
class FootRollRig(RollRig):
    
    def __init__(self, description, side=None):
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
        
        ik_handle = space.IkHandle(name)
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
            control = self._create_control( 'TOE_ROTATE', True, curve_type= 'circle')
            control.hide_translate_attributes()
            control.hide_scale_attributes()
            control.hide_visibility_attribute()
            xform_group = control.create_xform()
            control = control.get()
        
        if self.toe_rotate_as_locator:
            control = cmds.spaceLocator(n = self._get_name('locator', 'toe_rotate'))[0]
            xform_group = space.create_xform_group(control)
            attribute_control = self._get_attribute_control()
            
            cmds.addAttr(attribute_control, ln = 'toeRotate', at = 'double', k = True)  
            cmds.connectAttr('%s.toeRotate' % attribute_control, '%s.rotate%s' % (control, self.forward_roll_axis))  
            
        
        match = space.MatchSpace(self.ball, xform_group)
        match.translation_rotation()
        
        cmds.parent(xform_group, self.control_group)
        
        return control, xform_group
    
    def _create_toe_fk_rotate_control(self):
        control = self._create_control( 'TOE_FK_ROTATE')
        control.hide_translate_attributes()
        control.hide_scale_attributes()
        control.hide_visibility_attribute()
        
        xform_group = control.create_xform()
        
        match = space.MatchSpace(self.ball, xform_group)
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
        control = rigs_util.Control(control)
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
        
        cmds.parent(toe_control_xform, yawout_roll)
        #cmds.parent(toe_fk_control_xform, self.control_group)
        
        #cmds.parentConstraint(ball_roll, self.roll_control_xform, mo = True)
        if not self.main_control_follow:
            space.create_follow_group(ball_roll, self.roll_control_xform)
        if self.main_control_follow:
            space.create_follow_group(self.main_control_follow, self.roll_control_xform)
        
        cmds.parentConstraint(toe_control, self.ball_handle, mo = True)
        cmds.parentConstraint(ball_roll, self.ankle_handle, mo = True)
        
        
        return [ball_pivot, toe_fk_control_xform]
        
    def set_toe_rotate_as_locator(self, bool_value):
        """
        Whether the toe rotate should be a locator instead of a control.
        An attribute will be created on the main control to rotate the toe.
        """
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
        
        attr.connect_equal_condition('%s.%s' % (self.roll_control.get(), self.ik_attribute), '%s.visibility' % toe_fk_control_xform, 1)
        #cmds.connectAttr('%s.%s' % (self.roll_control.get(), self.ik_attribute), '%s.visibility' % toe_fk_control_xform)
        attr.connect_equal_condition('%s.%s' % (self.roll_control.get(), self.ik_attribute), '%s.visibility' % ball_pivot, 0)
        #connect_reverse('%s.%s' % (self.roll_control.get(), self.ik_attribute), '%s.visibility' % ball_pivot)
              
class BaseFootRig(BufferRig):
    def __init__(self, description, side=None):
        super(BaseFootRig, self).__init__(description, side)
        
        self.create_roll_controls = True
        self.attribute_control = None
        
        self.control_shape = 'circle'
        
        self.forward_roll_axis = 'X'
        self.side_roll_axis = 'Z'
        self.top_roll_axis = 'Y'
        
        self.attribute_control_shape = 'square'
        
        self.locators = []
            
    def _get_attribute_control(self):
        if not self.attribute_control:
            return self.roll_control.get()
            
        if self.attribute_control:
            return self.attribute_control        
    
    def _create_pivot_group(self, source_transform, description):
        
        name = self._get_name('pivot', description)
        
        group = cmds.group(em = True, n = name)
        
        space.MatchSpace(source_transform, group).translation()
        space.MatchSpace(self.joints[-1], group).rotation()
        
        xform_group = space.create_xform_group(group)
        
        attribute_control = self._get_attribute_control()
        
        cmds.addAttr(attribute_control, ln = '%sPivot' % description, at = 'double', k = True)
        
        cmds.connectAttr('%s.%sPivot' % (attribute_control, description), '%s.rotateY' % group)
        
        return group, xform_group
    
    def _create_pivot_control(self, source_transform, description, sub = False, no_control = False, scale = 1):
        
        if self.create_roll_controls:
            control = self._create_control(description, sub)
            
            control_object = control
            
            #if sub:
            #    if self.sub_control_shape:
            #        control.set_curve_type(self.sub_control_shape)
                            
            control.scale_shape(scale, scale, scale)
            control = control.get()
        
        if not self.create_roll_controls or no_control:
            name = self._get_name('ctrl', description)
            control = cmds.group(em = True, n = core.inc_name(name))
        
        xform_group = space.create_xform_group(control)
        driver_group = space.create_xform_group(control, 'driver')
        
        space.MatchSpace(source_transform, xform_group).translation()
        space.MatchSpace(self.joints[-1], xform_group).rotation()
        
        if self.create_roll_controls:
            
            control_object.hide_scale_attributes()
            control_object.hide_translate_attributes()
            control_object.hide_visibility_attribute()
            
        if self.create_roll_controls:
            cmds.connectAttr('%s.controlVisibility' % self._get_attribute_control(), '%sShape.visibility' % control)
        
        return control, xform_group, driver_group
    
    def _create_roll_control(self, transform):
        
        roll_control = self._create_control('roll', curve_type = self.attribute_control_shape) 
        
        self.roll_control = roll_control
        
        roll_control.scale_shape(.8,.8,.8)
        
        xform_group = space.create_xform_group(roll_control.get())
        
        roll_control.hide_keyable_attributes()
        
        match = space.MatchSpace( transform, xform_group )
        match.translation_rotation()
        
        cmds.parent(xform_group, self.control_group)
        
        self.roll_control_xform = xform_group 
        
        return roll_control 
    
    def _create_ik_handle(self, name, start_joint, end_joint):
        
        name = self._get_name(name)
        
        ik_handle = space.IkHandle(name)
        ik_handle.set_solver(ik_handle.solver_sc)
        ik_handle.set_start_joint(start_joint)
        ik_handle.set_end_joint(end_joint)
        return ik_handle.create()  
    
    def set_create_roll_controls(self, bool_value):
        
        self.create_roll_controls = bool_value
        
    def set_attribute_control(self, control_name):
        self.attribute_control = control_name
    
    def set_control_shape(self, shape_name):
        self.control_shape = shape_name
    
    def set_attribute_control_shape(self, shape_name):
        self.attribute_control_shape = shape_name
    
    def set_forward_roll_axis(self, axis_letter):
        self.forward_roll_axis = axis_letter
        
    def set_side_roll_axis(self, axis_letter):
        self.side_roll_axis = axis_letter
        
    def set_top_roll_axis(self, axis_letter):
        self.top_roll_axis = axis_letter
    
    def create(self):
        super(BaseFootRig, self).create()
        
        self._create_roll_control(self.joints[0])
        
        attr.create_title(self._get_attribute_control(), 'FOOT_PIVOTS')
                
        if self.create_roll_controls:
            bool_var = attr.MayaNumberVariable('controlVisibility')
            bool_var.set_variable_type(bool_var.TYPE_BOOL)
            bool_var.create(self._get_attribute_control())
            bool_var.set_value(self.sub_visibility)
            
class FootRig(BaseFootRig):
    def __init__(self, description, side=None):
        super(FootRig, self).__init__(description, side)
        
        self.build_hierarchy = True
        
        self.toe_rotate_as_locator = False
        self.mirror_yaw = False
        self.main_control_follow = None
        self.ik_parent = None
        self.ik_leg = None
        
        self.heel = None
        self.yawIn = None
        self.yawOut = None
    
    def _duplicate_joints(self):
        
        super(FootRig, self)._duplicate_joints()
        
        ankle = self.buffer_joints[0]
        
        ankle_base = core.get_basename(ankle)
        ankle_name = ankle_base
        
        if self.create_buffer_joints:
            ankle_name = ankle_base.replace('locator', 'buffer')
            
        if not self.create_buffer_joints:
            ankle_name = ankle_base.replace('locator', 'guide')
            
        joint = cmds.rename(ankle, ankle_name)
        
        self.buffer_joints[0] = joint
            
        if not self.create_buffer_joints:
            self.joints[0] = joint
        
    def _create_ik_chain(self):
        
        duplicate = space.DuplicateHierarchy(self.buffer_joints[0])
        duplicate.only_these(self.buffer_joints)
        
        if not self.create_buffer_joints:
            duplicate.replace('joint', 'guide')
        if self.create_buffer_joints:
            duplicate.replace('buffer', 'guide')
        
        joints = duplicate.create()
        
        parent = cmds.listRelatives(joints[0], p = True)
        
        if parent:
            if parent[0] != self.setup_group:
                cmds.parent(joints[0], self.setup_group)
        
        self.ik_joints = joints
        
        return joints
    
    def _attach_ik_chain(self):

        for inc in range(0, len(self.ik_joints)):
            cmds.parentConstraint(self.ik_joints[inc], self.buffer_joints[inc])
        
    def _create_ik(self):
        
        self.ankle_handle = self._create_ik_handle( 'ankle', self.ankle, self.ball)
        self.ball_handle = self._create_ik_handle( 'ball', self.ball, self.toe)
        
        cmds.parent( self.ankle_handle, self.setup_group )
        cmds.parent( self.ball_handle, self.setup_group )
        
        if self.ik_parent:
            cmds.pointConstraint(self.ik_parent, self.ik_joints[0]) 
        
    def _create_toe_rotate_control(self):
        
        attribute_control = self._get_attribute_control()
        
        cmds.addAttr(attribute_control, ln = 'toeRotate', at = 'double', k = True)  
        
        if not self.toe_rotate_as_locator:
            
            control = self._create_control( 'TOE_ROTATE', True, curve_type = 'circle')
            control.hide_translate_attributes()
            control.hide_scale_attributes()
            control.hide_visibility_attribute()
            control.rotate_shape(90,0,0)
            xform_group = control.create_xform()
            driver = space.create_xform_group(control.get(), 'driver')
            control = control.get()
            
            cmds.connectAttr('%s.toeRotate' % attribute_control, '%s.rotate%s' % (driver, self.forward_roll_axis))  
        
        if self.toe_rotate_as_locator:
            
            control = cmds.spaceLocator(n = self._get_name('locator', 'toe_rotate'))[0]
            xform_group = space.create_xform_group(control)
            
            cmds.connectAttr('%s.toeRotate' % attribute_control, '%s.rotate%s' % (control, self.forward_roll_axis))  
            
        match = space.MatchSpace(self.ball, xform_group)
        match.translation_rotation()
        
        cmds.parent(xform_group, self.control_group)
        
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
        control = rigs_util.Control(control)
        control.scale_shape(2,2,2)
        control = control.get()
        
        cmds.parent(xform, parent)
        
        if self.ik_leg:
            cmds.parent(self.ik_leg, control)
        
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
        
        if not self.main_control_follow:
            space.create_follow_group(ball_roll, self.roll_control_xform)
        if self.main_control_follow:
            space.create_follow_group(self.main_control_follow, self.roll_control_xform)
        
        cmds.parentConstraint(toe_control, self.ball_handle, mo = True)
        cmds.parentConstraint(ball_roll, self.ankle_handle, mo = True)
        
        return ball_pivot
    
    def set_build_hierarchy(self, bool_value):
        
        if not bool_value:
            vtool.util.warning('Foot Roll rig needs to build hierarchy. Setting it True.')
        
        self.build_hierarchy = True

    
    def set_toe_rotate_as_locator(self, bool_value):
        self.toe_rotate_as_locator = bool_value
          
    def set_mirror_yaw(self, bool_value):
        self.mirror_yaw = bool_value
        
    def set_pivot_locator(self, locator_name):
        pass
        
    def set_pivot_locators(self, heel, yaw_in, yaw_out):
        """
        Set the pivots for the foot roll.
        These must be transforms.
        
        Args:
            heel (str): Name of a transform.
            yaw_in (str): Name of a transform.
            yaw_out (str): Name of a transform.
        """
        
        self.heel = heel
        self.yawIn = yaw_in
        self.yawOut = yaw_out
        
    def set_main_control_follow(self, transform):
        self.main_control_follow = transform
        
    def set_ik_parent(self, parent_name):
        self.ik_parent = parent_name
        
    def set_ik_leg(self, ik_group_name):
        
        self.ik_leg =  ik_group_name
                    
    def create(self):
        
        super(FootRig,self).create()
        
        if len(self.joints) < 3:
            vtool.util.warning('Please set three joints. set_joints([joint_ankle, joint_ball, joint_toe])')
            
        if not self.joints[0] or not self.joints[1] or not self.joints[2]:
            vtool.util.warning('Please set_pivot_locators(heel, yaw_in, yaw_out)')
            return
        
        self._create_ik_chain()
        self._attach_ik_chain()
        
        self.ankle = self.ik_joints[0]
        self.ball = self.ik_joints[1]
        self.toe = self.ik_joints[2]
        
        self._create_roll_attributes()
        
        #ball_pivot = self._create_pivot_groups()
        self._create_pivot_groups()
        
class QuadSpineRig(BufferRig):
    
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
        xform = space.create_xform_group(btm_control)
        
        space.create_follow_group(btm_control, self.clusters[0])
        cmds.parent(xform, self.control_group)
        
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
        xform = space.create_xform_group(top_control)
        
        space.create_follow_group(top_control, self.clusters[-1])
        cmds.parent(xform, self.control_group)
        
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
        cmds.parent(xform, self.control_group)
        
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
        super(QuadSpineRig, self).create()
        
        self._create_surface()
        self._create_clusters()
        self._attach_to_surface()

        self._create_controls()
        
class QuadFootRig(FootRig):
    
    def __init__(self, description, side=None):
        super(QuadFootRig, self).__init__(description, side)
        
        self.ball_attrtribute = None
        self.add_bank = True
        self.extra_ball = None
        
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
        
        #attr.connect_reverse('%s.ikFk' % self.roll_control.get(), '%sShape.visibility' % control)
        
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
        
        if self.extra_ball:
            if self.ik_leg:
                cmds.parent(self.ik_leg, control)
        
        return control
    
    def _create_roll_control(self, transform):
        
        roll_control = self._create_control('roll', curve_type = self.attribute_control_shape) 
        
        self.roll_control = roll_control
        
        roll_control.scale_shape(.8,.8,.8)
        
        xform_group = space.create_xform_group(roll_control.get())
        
        roll_control.hide_scale_and_visibility_attributes()
        roll_control.hide_rotate_attributes()
        
        match = space.MatchSpace( transform, xform_group )
        match.translation_rotation()
        
        cmds.parent(xform_group, self.control_group)
        
        self.roll_control_xform = xform_group 
        
        return roll_control
    
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
            
    def _create_ik(self):
        if not self.extra_ball:
            
            self.ankle_handle = self._create_ik_handle( 'ankle', self.ankle, self.ball) 
            cmds.parent( self.ankle_handle, self.setup_group )
            
            self.ball_handle = self._create_ik_handle( 'ball', self.ball, self.toe)
            cmds.parent( self.ball_handle, self.setup_group )
               
        if self.extra_ball:
            self.ankle_handle = self._create_ik_handle( 'ankle', self.ankle, self.extra_ball)
            self.extra_handle = self._create_ik_handle( 'ball', self.extra_ball, self.ball)
            self.ball_handle = self._create_ik_handle( 'ball', self.ball, self.toe)
            
            cmds.parent(self.ankle_handle, self.setup_group)
            cmds.parent(self.extra_handle, self.setup_group)
            cmds.parent(self.ball_handle, self.setup_group)
            
        if self.ik_parent:
            cmds.pointConstraint(self.ik_parent, self.ik_joints[0]) 
        
    def _create_pivot_groups(self):

        toe_control, toe_control_xform = self._create_toe_rotate_control()
        
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
        
        if not self.add_bank:
            cmds.parent(toe_control_xform, yawout_roll)
            
        if self.add_bank:
            
            bankin_roll = self._create_yawin_roll(next_roll, 'bankIn', scale = .5)
            bankout_roll = self._create_yawout_roll(bankin_roll, 'bankOut', scale = .5)
            
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
            
            cmds.parentConstraint(toe_control, self.ball_handle, mo = True)
            
            if not self.add_bank:
                cmds.parentConstraint(ball_roll, self.ankle_handle, mo = True)
                
                cmds.parent(self.ik_leg, ball_roll)
            if self.add_bank:
                cmds.parentConstraint(bankout_roll, self.ankle_handle, mo = True)
                cmds.parent(self.ik_leg, bankout_roll)
                
                space.create_follow_group(yawout_roll, toe_control_xform)
                        
        cmds.parentConstraint(ball_roll, self.roll_control_xform, mo = True)
            
    def set_add_bank(self, bool_value):
        self.add_bank = bool_value
             
    def set_extra_ball(self, joint_name):
        
        self.extra_ball = joint_name
                    
    def create(self):
        
        
        if self.extra_ball:
            self.joints.insert(2, self.extra_ball)
        
        super(FootRig,self).create()
        
        
        
        if len(self.joints) < 3:
            vtool.util.warning('Please set three joints. set_joints([joint_ankle, joint_ball, joint_toe])')
            
        if not self.joints[0] or not self.joints[1] or not self.joints[2]:
            vtool.util.warning('Please set_pivot_locators(heel, yaw_in, yaw_out)')
            return
        
        self._create_ik_chain()
        
        self._attach_ik_chain()
        
        self.ankle = self.ik_joints[0]
        self.ball = self.ik_joints[1]
        self.toe = self.ik_joints[2]
        
        self._create_roll_attributes()
        
        self._create_pivot_groups()
        
#---Face Rig

class EyeLidCurveRig(JointRig):
    """
    Very slow.
    """
    
    def __init__(self, description, side=None):
        
        super(EyeLidCurveRig, self).__init__(description, side)
        
        self.surface = None
        
        self.offset_group = None
        
        self.main_joint_dict = {}
        self.row_joint_dict = {}
        self.main_controls = []
        
        self.orient_transform = None
        self.orient_aim = False
        self.orient_aim_axis = 'Z'
        
        self.invert_y = False
        
        self.follow_multiply = 1
        
        self.control_offset = 0
        self.sub_control_size = 0.5
        
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
        
    def _aim_constraint(self, center_transform, transform_to_aim):
        
        axis = [1,0,0]
        up_vector = [0,1,0]
        
        if self.orient_aim_axis == 'X':
            axis = [-1,0,0]
            up_vector = [0,1,0]
        if self.orient_aim_axis == 'Y':
            axis = [0,1,0]
            up_vector = [0,0,-1]
        if self.orient_aim_axis == 'Z':
            axis = [0,0,-1]
            up_vector = [0,1,0]
        
        cmds.aimConstraint(center_transform, transform_to_aim, aimVector = axis, upVector = up_vector, 
                           wut = 'objectrotation', 
                           wuo = center_transform)
        
    def _create_controls(self):
        
        inc = 0
        
        for cluster in self.clusters:
            
            if self.orient_aim:
                
                parent = cmds.listRelatives(cluster, p = True)
                
                offset = cmds.group(em = True, n = 'offset_%s' % cluster)
                
                if parent:
                    cmds.parent(offset, parent[0])
                
                space.MatchSpace(cluster, offset).translation_to_rotate_pivot()
                space.MatchSpace(self.orient_transform, offset).rotation()
                
                cluster_group = cmds.group(em = True, n = 'buffer_%s' % cluster)
                space.MatchSpace(offset, cluster_group).translation_rotation()
                space.MatchSpace(self.orient_transform, cluster_group).rotation()
                
                cmds.parent(cluster_group, offset)
                cmds.parent(cluster, cluster_group)
                
                cmds.setAttr('%s.inheritsTransform' % offset, 0)
            
            if not self.orient_aim:
                
                cmds.setAttr('%s.inheritsTransform' % cluster, 0)
            
            control = self._create_control()
            control.hide_scale_attributes()
            control.rotate_shape(90, 0, 0)
            
            control.scale_shape(self.control_size, self.control_size, self.control_size)
            control.translate_shape(0, 0, self.control_offset)
            
            self.main_controls.append(control.get())
            
            if self.surface:
                sub_control = self._create_control(sub = True)
                sub_control.hide_scale_attributes()
                
                sub_size = self.sub_control_size * self.control_size
                
                sub_control.scale_shape(sub_size, sub_size, sub_size)
                sub_control.rotate_shape(90, 0, 0)
                sub_control.translate_shape(0, 0, self.control_offset)
            
                cmds.parent(sub_control.get(), control.get())
                
                space.create_xform_group(sub_control.get())
                sub_driver = space.create_xform_group(sub_control.get(), 'driver')
                
                attr.connect_translate(sub_control.get(), self.sub_cluster[inc])
                attr.connect_translate(sub_driver, self.sub_cluster[inc])
                
                cmds.setAttr('%s.inheritsTransform' % self.sub_cluster[inc], 0)
                    
            
            space.MatchSpace(cluster, control.get()).translation_to_rotate_pivot()
            
            if self.orient_transform:
                space.MatchSpace(self.orient_transform, control.get()).rotation()
            
            xform = space.create_xform_group(control.get())
            driver = space.create_xform_group(control.get(), 'driver')
            
            if not self.orient_aim:
                attr.connect_translate(control.get(), cluster)
                attr.connect_translate(driver, cluster)
                
            if self.orient_aim:
                attr.connect_translate(control.get(), cluster_group)
                attr.connect_translate(driver, cluster_group)
            
            cmds.parent(xform, self.control_group)
            
            inc += 1
                
    def _attach_joints_to_curve(self):
        
        for joint in self.joints:
            
            parent = cmds.listRelatives(joint, p = True)[0]
            
            xform = cmds.group(em = True, n = 'xform_%s' % joint)
            space.MatchSpace(joint, xform).translation()
            cmds.parent(xform, parent)
            
            offset = space.create_xform_group(joint, 'offset')
            driver = space.create_xform_group(joint, 'driver')
            
            if self.orient_aim:
                self._aim_constraint(self.orient_transform, joint)
            
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
            

                
    def set_control_offset(self, value):
        
        self.control_offset = value
            
    def set_surface(self, surface_name):
        self.surface = surface_name  
        
    def set_orient(self, transform):
        
        self.orient_transform = transform
        
    def set_orient_aim(self, bool_value, axis = 'Z'):
        
        self.orient_aim_axis = axis
        self.orient_aim = bool_value
        
    def set_follow_multiply(self, value):
        self.follow_multiply = value
        
    def set_invert_y_value(self, bool_value):
        
        self.invert_y = bool_value
        
        
    def create(self):
        super(EyeLidCurveRig, self).create()
        
        if self.orient_transform:
            self.orient_transform = cmds.duplicate(self.orient_transform, n = core.inc_name(self._get_name('orient')), po = True)[0]
            
        
        self._create_curve()
        
        self._cluster_curve()
        
        self._create_controls()
        
        self._attach_joints_to_curve()
            
    def create_fade_row(self, joints, weight, ignore_surface = False):
        
        if len(joints) != len(self.joints):
            cmds.warning('Row joint count and rig joint count do not match.')
  
        for inc in range(0, len(self.joints)):
            """
            groups_created = False
            if self.row_joint_dict.has_key(joints[inc]):
                
                xform = self.row_joint_dict[joints[inc]]['xform']
                offset = self.row_joint_dict[joints[inc]]['offset']
                driver = self.row_joint_dict[joints[inc]]['driver']
            
            if not self.row_joint_dict.has_key(joints[inc]):

                xform = space.create_xform_group(joints[inc])
                offset = space.create_xform_group(joints[inc], 'offset')
                driver = space.create_xform_group(joints[inc], 'driver')
                
                self.row_joint_dict[joints[inc]] = {}
                self.row_joint_dict[joints[inc]]['xform'] = xform
                self.row_joint_dict[joints[inc]]['offset'] = offset
                self.row_joint_dict[joints[inc]]['driver'] = driver
                groups_created = True
            """
            
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
                parent = cmds.listRelatives(joints[inc], parent = True)
                
                xform = cmds.group(em = True, n = 'xform_%s' % joints[inc])
                #xform = space.create_xform_group(joints[inc])
                
                space.MatchSpace(joints[inc], xform).translation()
            
                if parent:
                    cmds.parent(xform, parent[0])
                    
                cmds.parent(joints[inc], xform)
            
            if not offset == 'offset_%s' % joints[inc]:
                offset = space.create_xform_group(joints[inc], 'offset')
                
            if not driver == 'driver_%s' % joints[inc]:
                driver = space.create_xform_group(joints[inc], 'driver')
                
                if self.orient_aim:
                    self._aim_constraint(self.orient_transform, driver)
            
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
        
        value = self.follow_multiply * weight
        
        multiply = attr.connect_translate_multiply(control, parent, value)
        
        if self.invert_y:
            value = cmds.getAttr('%s.input2Y' % multiply)
            value = value * -1
            cmds.setAttr('%s.input2Y' % multiply, value)
            
            control_parent = cmds.listRelatives(control, p = True)
            
            if control_parent:
                if control_parent[0] == 'driver_%s' % control:
                    cmds.setAttr('%s.scaleY' % control_parent[0], -1)
                    
class EyeLidAimRig(JointRig):
    
    def __init__(self, description, side=None):
        super(EyeLidAimRig, self).__init__(description, side)
        
        self.orient_aim_axis = 'Z'
        self.center_locator = None
        self.control_offset = 0
        self.follow_multiply = 1
        
        self.scale_space = 1
        self.use_joint = True
    
    def _aim_constraint(self, transform_to_aim, aim_target):
        
        axis = [1,0,0]
        up_vector = [0,1,0]
        
        if self.orient_aim_axis == 'X':
            axis = [-1,0,0]
            up_vector = [0,1,0]
        if self.orient_aim_axis == 'Y':
            axis = [0,1,0]
            up_vector = [0,0,-1]
        if self.orient_aim_axis == 'Z':
            axis = [0,0,-1]
            up_vector = [0,1,0]
        
        cmds.aimConstraint(aim_target, transform_to_aim, aimVector = axis, upVector = up_vector, 
                           wut = 'objectrotation', 
                           wuo = self.center_locator)
    
    def _create_curve(self):
        
        self.curve = geo.transforms_to_curve(self.joints, 4, self.description)
        
        cmds.parent(self.curve, self.setup_group)
    
    def _attach_to_curve(self, transforms):
        
        for transform in transforms:
            geo.attach_to_curve(transform, self.curve)
    
    def _cluster_curve(self):
        
        self.clusters = deform.cluster_curve(self.curve, self.description)
        
        for cluster in self.clusters:
            cmds.setAttr('%s.inheritsTransform' % cluster, 0)
        
        cmds.parent(self.clusters, self.setup_group)
    
    def _create_controls(self):
        
        inc = 0
        
        local_group = self._create_setup_group('local')
        cmds.setAttr('%s.inheritsTransform' % local_group, 0)
        
        for cluster in self.clusters:
            
            control = self._create_control()
            if self.use_joint:
                control.set_to_joint()
            
            
            control.rotate_shape(90, 0, 0)
            
            control.scale_shape(self.control_size, self.control_size, self.control_size)
            control.translate_shape(0, 0, self.control_offset)
            
            space.MatchSpace(cluster, control.get()).translation_to_rotate_pivot()
            
            
            
            xform = space.create_xform_group(control.get())
            driver = space.create_xform_group(control.get(), 'driver')
            
            if self.center_locator:
                space.MatchSpace(self.center_locator, xform).rotation()
                
                space.MatchSpace(self.center_locator, xform).scale()
            
            current_scale = cmds.getAttr('%s.scale' % xform)[0]
            
            if type(self.scale_space) == list:
            
                
                scale_value = [current_scale[0] * self.scale_space[0],
                               current_scale[1] * self.scale_space[1],
                               current_scale[2] * self.scale_space[2]]
                
                offset_scale = [1,1,1]
                
                if self.scale_space[0] < 0:
                    offset_scale[0] = -1
                
                if self.scale_space[1] < 0:
                    offset_scale[1] = -1
                    
                if self.scale_space[2] < 0:
                    offset_scale[2] = -1
                    
                cmds.scale(scale_value,scale_value, scale_value, xform)    
                cmds.scale(offset_scale[0], offset_scale[1], offset_scale[2], control.control)

            if type(self.scale_space) != list:
                if self.scale_space < 1 or self.scale_space > 1:
                    cmds.scale(self.scale_space*current_scale[0], self.scale_space*current_scale[1], self.scale_space*current_scale[2], xform)

            if self.use_joint:
                cmds.connectAttr('%s.scale' % xform, '%s.inverseScale' % control.control)
            
            local, local_xform = space.constrain_local(control.get(), cluster)
            local_driver = space.create_xform_group(local, 'driver')
            
            attr.connect_scale(xform, local_xform)
            
            attr.connect_translate(driver, local_driver)
            
            cmds.parent(xform, self.control_group)
            cmds.parent(local_xform, local_group)
            
            inc += 1
    
    def set_control_offset(self, value):
        self.control_offset = value
    
    def set_scale_space(self, value):
        self.scale_space = value
    
    def set_use_joint_controls(self, value):
        self.use_joint = value
    
    def set_center_locator(self, locator):
        self.center_locator = locator
    
    def set_follow_multiply(self, value):
        self.follow_multiply = value
    
    def create(self):
        super(EyeLidAimRig, self).create()
        
        if not self.center_locator:
            vtool.util.warning('Please provide a center locator.')
            return
        
        targets = []
        
        for joint in self.joints:
            locator_aim = cmds.spaceLocator(n = core.inc_name('locator_%s' % core.inc_name(self._get_name('aim'))))[0]
            cmds.parent(locator_aim, self.setup_group)
            
            locator_target = cmds.spaceLocator(n = core.inc_name('locator_%s' % self._get_name('target')))[0]
            targets.append(locator_target)
            cmds.parent(locator_target, self.setup_group)
            
            space.MatchSpace(self.center_locator, locator_aim).translation_rotation()
            space.MatchSpace(joint, locator_target).translation()
            space.MatchSpace(self.center_locator, locator_target).rotation()
            
            self._aim_constraint(locator_aim, locator_target)
            
            cmds.parentConstraint(locator_aim, joint, mo = True)
            
        self._create_curve()
        self._attach_to_curve(targets)
        self._cluster_curve()
        self._create_controls()
        
    
        
    def create_control_follow(self, main_control, increment, weight):
        
        
        control = self.controls[increment]
        driver = space.get_xform_group(control, 'driver')
        
        xform = space.get_xform_group(control)
        
        main_xform = space.get_xform_group(main_control)
        
        scale = cmds.getAttr('%s.scale' % xform)[0]
        main_scale = cmds.getAttr('%s.scale' % main_xform)[0]
        
        if main_scale[0] < 0:
            cmds.setAttr('%s.scaleX' % xform, (scale[0] * -1))
        if main_scale[1] < 0:
            cmds.setAttr('%s.scaleY' % xform, (scale[0] * -1))
        if main_scale[2] < 0:
            cmds.setAttr('%s.scaleZ' % xform, (scale[0] * -1))
        
        value = self.follow_multiply * weight
        
        attr.connect_translate_multiply(main_control, driver, value)
        
            
                    
class StickyRig(JointRig):
    
    def __init__(self, description, side=None):
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
        
        self.follow_control_groups = {}
        
        self.top_controls = []
        self.btm_controls = []
        
        self.local = True
        
        self.sticky_control_group = self._create_control_group('sticky')
        
        self.tweaker_space = 1
        
        self.use_joint = True
        
        self._right_side_fix = True
            
        #self.sticky_control_group = cmds.group(em = True, n = core.inc_name(self._get_name('group', 'sticky_controls')))
        #cmds.parent(self.sticky_control_group, self.control_group)
        
        
        
    def _loop_joints(self):
        
        if self.local:
            self.sticky_setup_group = self._create_setup_group('sticky')
        
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
        
        self.top_locator = self._create_locator('top')
        self.mid_top_locator = self._create_locator('mid_top')
        self.mid_btm_locator = self._create_locator('mid_btm')
        self.btm_locator = self._create_locator('btm')
        
        self.control_dict[control_top[0]] = [control_top[1], control_top[2]]
        self.control_dict[control_btm[0]] = [control_btm[1], control_btm[2]]
        
        #space.MatchSpace(top_joint, self.top_locator[1]).translation_rotation()
        #space.MatchSpace(btm_joint, self.btm_locator[1]).translation_rotation()
        space.MatchSpace(top_joint, self.top_locator[1]).translation()
        space.MatchSpace(btm_joint, self.btm_locator[1]).translation()
        
        
        
        midpoint = space.get_midpoint(top_joint, btm_joint)
        
        cmds.xform(self.mid_top_locator[1], t = midpoint, ws = True)
        cmds.xform(self.mid_btm_locator[1], t = midpoint, ws = True)
        
        cmds.parent(self.top_locator[1], self.top_locator_group)
        cmds.parent(self.mid_top_locator[1], self.mid_locator_group)
        cmds.parent(self.mid_btm_locator[1], self.mid_locator_group)
        cmds.parent(self.btm_locator[1], self.btm_locator_group)   

        space.MatchSpace(self.top_locator[0], self.mid_top_locator[0]).translation()
        space.MatchSpace(self.btm_locator[0], self.mid_btm_locator[0]).translation()

        self._create_follow([self.top_locator[0], self.mid_top_locator[0]], control_top[1], top_joint)
        
        control_top_xform = space.get_xform_group(control_top[0])
        
        cmds.addAttr(control_top_xform, ln = 'stick', min = 0, max = 1, k = True)
        
        cmds.connectAttr('%s.stick' % control_top_xform, '%s.stick' % top_joint)
        
        control_btm_xform = space.get_xform_group(control_btm[0])
        
        self._create_follow([self.btm_locator[0], self.mid_btm_locator[0]], control_btm[1], control_btm_xform)
        
        self._create_follow([self.top_locator[0], self.btm_locator[0]], self.mid_top_locator[1], self.mid_top_locator[0])
        self._create_follow([self.top_locator[0], self.btm_locator[0]], self.mid_btm_locator[1], self.mid_btm_locator[0])
        
        cmds.setAttr('%s.stick' % self.mid_top_locator[0], 0.5)
        cmds.setAttr('%s.stick' % self.mid_btm_locator[0], 0.5)
        
    def _create_follow(self, source_list, target, target_control ):
        
        constraint = cmds.parentConstraint(source_list, target, mo = True)[0]
        cmds.setAttr('%s.interpType' % constraint, 2)
        constraint_editor = space.ConstraintEditor()    
        constraint_editor.create_switch(target_control, 'stick', constraint)
        
    def _create_sticky_xform(self, control):
        
        xform = space.create_xform_group(control)
        
        
        cmds.makeIdentity(control, apply = True, r = True)
        
        
        xform_driver = space.create_xform_group(control, 'xform_driver')
        
        
        driver = space.create_xform_group(control, 'driver')
        
        
        
        space.create_xform_group(control, 'xform_space')
        scale = space.create_xform_group(control, 'scale')
        
        pin = space.PinXform(driver)
        pin.pin()
        cmds.xform(xform_driver, ws = True, ro = [0,0,0])
        pin.unpin()
        
        pin = space.PinXform(driver)
        pin.pin()
        cmds.xform(driver, ws = True, ro = [0,0,0])
        pin.unpin()
        
        
        if self.side == 'R' and self._right_side_fix:
            cmds.setAttr('%s.rotateY' % scale, 180)
            cmds.setAttr('%s.scaleZ' % scale, -1)
            
        
        return xform, driver, scale
    
    def _create_sticky_control(self, transform, description):
        
        control = self._create_control(description)
        control.rotate_shape(90,0,0)
        control.scale_shape(.5, .5, .5)
        
        if self.use_joint:
            control.set_to_joint()
        
        control_name = control.get()
        
        space.MatchSpace(transform, control_name).translation_rotation()
        
        control = control_name
        
        xform, driver, scale = self._create_sticky_xform(control)
        cmds.parent(xform, self.sticky_control_group)
        
        if not self._right_side_fix:
            space.MatchSpace(transform, scale).scale()
        
        if not self.local:
            cmds.parentConstraint(control, transform)
            constraint = cmds.scaleConstraint(control, transform)[0]
            space.scale_constraint_to_local(constraint)
            
        if self.local:
            
            locator = cmds.spaceLocator(n = 'locator_%s' % control)[0]
            space.MatchSpace(transform, locator).translation_rotation()
            
            local_xform, local_driver, local_scale = self._create_sticky_xform(locator)
            
            attr.connect_transforms(xform, local_xform)
            attr.connect_transforms(driver, local_driver)
            attr.connect_transforms(scale, local_scale)
            attr.connect_transforms(control, locator)

            cmds.parentConstraint(locator, transform)
            
            cmds.parent(local_xform, self.sticky_setup_group)
            
        if self.tweaker_space < 1 or self.tweaker_space > 1:
                
            if self.use_joint:
                space.connect_inverse_scale(scale, control)
            
            scale_x = cmds.getAttr('%s.scaleX' % scale)
            scale_y = cmds.getAttr('%s.scaleY' % scale)
            scale_z = cmds.getAttr('%s.scaleZ' % scale)
            
            scale_x = self.tweaker_space * (abs(scale_x)/scale_x)
            scale_y = self.tweaker_space * (abs(scale_y)/scale_y)
            scale_z = self.tweaker_space * (abs(scale_z)/scale_z)
            

            
            cmds.setAttr('%s.scaleX' % scale, scale_x)
            cmds.setAttr('%s.scaleY' % scale, scale_y)
            cmds.setAttr('%s.scaleZ' % scale, scale_z)
        
        
        
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
    
    def set_local(self, bool_value):
        
        self.local = bool_value
    
    def set_tweaker_space(self, value):
        
        self.tweaker_space = value
    
    def set_use_joint_controls(self, bool_value):
        self.use_joint = bool_value
    
    def set_right_side_fix(self, bool_value):
        self._right_side_fix = bool_value
    
    def create(self):
        super(StickyRig, self).create()
        
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
            
        xform_left_top_control = space.get_xform_group(left_top_control)
        xform_left_btm_control = space.get_xform_group(left_btm_control)
            
        anim.quick_driven_key('%s.zipL' % attribute_control, '%s.stick' % xform_left_top_control, [start,end], [0,end_value])
        anim.quick_driven_key('%s.zipL' % attribute_control, '%s.stick' % xform_left_btm_control, [start,end], [0,end_value])
                
        if left_over_value:
            
            xform_left_top_control = get_xform_group(left_top_control)
            xform_left_btm_control = get_xform_group(left_btm_control)
            
            anim.quick_driven_key('%s.zipR' % attribute_control, '%s.stick' % xform_left_top_control, [start,end], [0,left_over_value])
            anim.quick_driven_key('%s.zipR' % attribute_control, '%s.stick' % xform_left_btm_control, [start,end], [0,left_over_value])
        
        cmds.setAttr('%s.stick' % xform_left_top_control, lock = True, k = False, cb = True)
        cmds.setAttr('%s.stick' % xform_left_btm_control, lock = True, k = False, cb = True)
        
        right_increment = 1
        
        if len(self.zip_controls[increment]) == 1:
            right_increment = 0
        
        right_top_control = self.zip_controls[increment][right_increment][0]
        right_btm_control = self.zip_controls[increment][right_increment][1]
        
        xform_right_top_control = space.get_xform_group(right_top_control)
        xform_right_btm_control = space.get_xform_group(right_btm_control)
        
        anim.quick_driven_key('%s.zipR' % attribute_control, '%s.stick' % xform_right_top_control, [start,end], [0,end_value])
        anim.quick_driven_key('%s.zipR' % attribute_control, '%s.stick' % xform_right_btm_control, [start,end], [0,end_value])
        
        if left_over_value:
            
            xform_right_top_control = get_xform_group(right_top_control)
            xform_right_btm_control = get_xform_group(right_btm_control)
            
            anim.quick_driven_key('%s.zipL' % attribute_control, '%s.stick' % xform_right_top_control, [start,end], [0,left_over_value])
            anim.quick_driven_key('%s.zipL' % attribute_control, '%s.stick' % xform_right_btm_control, [start,end], [0,left_over_value])

        cmds.setAttr('%s.stick' % xform_right_top_control, lock = True, k = False, cb = True)
        cmds.setAttr('%s.stick' % xform_right_btm_control, lock = True, k = False, cb = True)
        
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
            

            
class StickyFadeRig(StickyRig):       

    def __init__(self, description, side=None):
        super(StickyFadeRig, self).__init__(description, side)
        
        self.corner_offsets = []
        self.sub_corner_offsets = []
        
        self.corner_control_shape = 'square'
        
        self.corner_match = []
        self.corner_xforms = []
        self.corner_controls = []
        
        self.corner_x_space = []
        self.corner_y_space = []
        self.corner_z_space = []
        
        
        

    def _set_corner_space(self, source, target):
        
        space_scale = space.TranslateSpaceScale()
        
        space_scale.set_source_translate(source)
        space_scale.set_target_scale(target)
        
        if self.corner_x_space:
            space_scale.set_x_space(self.corner_x_space[0], self.corner_x_space[1])
        
        if self.corner_y_space:
            space_scale.set_y_space(self.corner_y_space[0], self.corner_y_space[1])
            
        if self.corner_z_space:
            space_scale.set_z_space(self.corner_z_space[0], self.corner_z_space[1])
            
        space_scale.create()
        
    def _create_corner_fades(self):
               
        orig_side = self.side
        
        for side in ['L','R']:
            
            self.side = side
            
            corner_offset = cmds.group(em = True, n = self._get_name('offset', 'corner'))
            #corner_offset_xform = space.create_xform_group(corner_offset)
            
            sub_corner_offset = cmds.duplicate(corner_offset, n = self._get_name('subOffset', 'corner'))[0]
            #cmds.parent(sub_corner_offset, corner_offset_xform)
            
            if side == 'L':
                joint = self.top_joints[0]
            if side == 'R':
                joint = self.top_joints[-1]
                
            control = self._create_control('corner', curve_type = self.corner_control_shape)
            #control.set_curve_type(self.corner_control_shape)
            control.rotate_shape(90,0,0)
            control.hide_rotate_attributes()
            control.hide_scale_attributes()
            
            if self.use_joint:
                control.set_to_joint()
            
            sub_control = self._create_control('corner', sub = True, curve_type=self.corner_control_shape)
            #sub_control.set_curve_type(self.corner_control_shape)
            sub_control.rotate_shape(90,0,0)
            sub_control.scale_shape(.8, .8, .8)
            sub_control.hide_rotate_attributes()
            sub_control.hide_scale_attributes()
            
            if self.use_joint:
                sub_control.set_to_joint()
            
            cmds.parent(sub_control.get(), control.get())
                
            xform = space.create_xform_group(control.get())
            
            space.create_xform_group(control.get(), 'driver')
            
            self.corner_xforms.append(xform)
            self.corner_controls.append(control.get())
            
            #space.MatchSpace(joint, corner_offset_xform).translation()
            if not self.corner_match:
                space.MatchSpace(joint, xform).translation_rotation()
            if self.corner_match:
                
                if side == 'L':
                    corner_match = self.corner_match[0]
                if side == 'R':
                    corner_match = self.corner_match[1]
                    
                match = space.MatchSpace(corner_match, xform)
                match.translation_rotation()
                
                
                const = cmds.scaleConstraint( corner_match, xform)
                cmds.delete(const)
            
            if self.use_joint:
                space.connect_inverse_scale(xform, control.control)
            
            cmds.parent(xform, self.control_group)
            
            self.corner_offsets.append(corner_offset)
            self.sub_corner_offsets.append(sub_corner_offset)
            
            corner_offset_xform = space.create_xform_group(corner_offset)
            
            if not self.local:
                cmds.pointConstraint(control.get(), corner_offset)
                cmds.pointConstraint(sub_control.get(), sub_corner_offset)
                
                cmds.pointConstraint(xform, corner_offset_xform)
                
            if self.local:
                space.MatchSpace(control.get(), corner_offset_xform).translation()
                space.MatchSpace(sub_control.get(), sub_corner_offset).translation()
                
                local, local_xform = space.constrain_local(control.get(), corner_offset)
                
                sub_local, sub_local_xform = space.constrain_local(sub_control.get(), sub_corner_offset)
                
                cmds.parent(sub_local_xform, local)
                attr.connect_scale(xform, local_xform)
                

                
                cmds.parent(local_xform, self.setup_group)
                
                buffer_joint = rigs_util.create_joint_buffer(sub_local, connect_inverse = False)

                space.MatchSpace(xform, sub_local_xform).scale()
                
                cmds.connectAttr('%s.scale' % local_xform, '%s.inverseScale' % buffer_joint)
                
            cmds.parent(corner_offset_xform, self.setup_group)
            cmds.parent(sub_corner_offset, corner_offset_xform)
            
            
        
            self._set_corner_space(control.control, xform)  
        
            
                      
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

    def set_corner_x_space(self, positive, negative):
        self.corner_x_space = [positive, negative]
    
    def set_corner_y_space(self, positive, negative):
        self.corner_y_space = [positive, negative]
    
    def set_corner_z_space(self, positive, negative):
        self.corner_z_space = [positive, negative]



    def create(self):
        super(StickyFadeRig, self).create()
        
        self._create_corner_fades()
        

    def create_follow(self, follow_transform, increment, value, top_follow_transform = None):
        
        value = vtool.util.convert_to_sequence(value)
        
        value1 = value[0]
        
        if len(value) > 1:
            value2 = value[1]
        if len(value) == 1:
            value2 = 1.0-value[0]
        
        if not self.follower_group:
            
            self.follower_group = cmds.group(em = True, n = core.inc_name(self._get_name('group', 'follower')))
            cmds.parent(self.follower_group, self.control_group)
        
        follow_transform = self._create_follow_control_group(follow_transform)
        follow_group = self.follower_group
        
        if top_follow_transform:
            top_follow_transform = self._create_follow_control_group(top_follow_transform)
            
            follow_group = top_follow_transform
        
        if increment != 'corner':
            locators = self.locators[increment]
    
            top_locator1 = locators[0][0][1]
            btm_locator1 = locators[0][1][1]
            
            follow_top = space.create_multi_follow([follow_group, follow_transform], top_locator1, top_locator1, value = value1)
            follow_btm = space.create_multi_follow([follow_group, follow_transform], btm_locator1, btm_locator1, value = value2)        
            
            self._rename_followers(follow_top, 'top')
            self._rename_followers(follow_btm, 'btm')
            
            if len(locators) > 1:
                top_locator2 = locators[1][0][1]
                btm_locator2 = locators[1][1][1]
            
                follow_top = space.create_multi_follow([follow_group, follow_transform], top_locator2, top_locator2, value = value1)
                follow_btm = space.create_multi_follow([follow_group, follow_transform], btm_locator2, btm_locator2, value = value2)
            
                self._rename_followers(follow_top, 'top')
                self._rename_followers(follow_btm, 'btm')
                
        if increment == 'corner':
            
            space.create_multi_follow([follow_group, follow_transform], self.corner_xforms[0], self.corner_xforms[0], value = value1)
            space.create_multi_follow([follow_group, follow_transform], self.corner_xforms[1], self.corner_xforms[1], value = value1)

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
            
        
    """
    def create_corner_locator(self, positive_scale_vector = None, negative_scale_vector = None):
        
        for control in self.corner_controls:
        
            top_xform = space.get_xform_group(control)
            parent = cmds.listRelatives(top_xform, p = True)
            if parent:
                parent = parent
            
            cmds.select(cl = True)
            locator = cmds.joint(n = 'locatorJoint_%s' % control)
            #locator = cmds.spaceLocator(n = 'locator_%s' % control)[0]
            xform = space.create_xform_group(locator)
            cmds.connectAttr('%s.scale' % xform, '%s.inverseScale' % locator)
            
            cmds.delete( cmds.parentConstraint(control, xform) )
            
            if parent:
                cmds.parent(xform, parent)
            
            self.set_corner_x_space(positive_scale_vector[0], negative_scale_vector[0])
            self.set_corner_y_space(positive_scale_vector[1], negative_scale_vector[1])
            self.set_corner_z_space(positive_scale_vector[2], negative_scale_vector[2])
            
            self._set_corner_space(locator, xform)  
            
            cmds.parentConstraint(control, locator)
    """
    
        
class EyeRig(JointRig):
    def __init__(self, description, side=None):
        super(EyeRig, self).__init__(description, side)
        self.local_parent = None
        self.parent = None
        
        self.eye_control_move = ['Z', 1]
        self.extra_control = False
        self.rotate_value = 25
        self.limit = 1
        self.skip_ik = False
        self._create_fk = False
        self._fk_control_shape_offset = 1
        
    def _create_ik(self):

        duplicate_hierarchy = space.DuplicateHierarchy( self.joints[0] )
        
        duplicate_hierarchy.stop_at(self.joints[-1])
        duplicate_hierarchy.replace('joint', 'ik')
        
        self.ik_chain = duplicate_hierarchy.create()
        
        cmds.parent(self.ik_chain[0], self.setup_group)
        
        if not self.skip_ik:
            ik = space.IkHandle(self.description)
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
            
            space.MatchSpace(self.joints[0], group1).translation_rotation()
            
            xform = space.create_xform_group(group1)
            
            attr.connect_rotate(self.ik_chain[0], group1)
            
            if not self.extra_control:
                cmds.orientConstraint(group2, self.joints[0])
            
            control =self._create_control()
            control.hide_scale_attributes()
            control = control.get()
            
            match = space.MatchSpace(self.joints[1], control)
            match.translation_rotation()
            
            cmds.parent(control, self.control_group)
            
            xform = space.create_xform_group(control)
            local_group, local_xform = space.constrain_local(control, handle)
            cmds.parent(local_xform, self.setup_group)

            if self.local_parent:
                cmds.parent(local_xform, self.local_parent)
                
            if self.parent:
                cmds.parent(xform, self.parent)

        if self.skip_ik:
            group1 = cmds.group(em = True, n = self._get_name('group', 'aim'))
            
            cmds.parent(group1, self.setup_group)
            
            
            
            space.MatchSpace(self.joints[0], group1).translation_rotation()
            
            xform = space.create_xform_group(group1)
            
            cmds.orientConstraint(group1, self.joints[0])
        
        
        
        
        if self.extra_control:
            self._rig_extra_control(group1)
        
        if self._create_fk:
            self._rig_fk(group1, group2)
            
        return control
    
    def _rig_fk(self, aim_transform, transform):
        
        control = self._create_control(sub = True)
        
        control.hide_translate_attributes()
        control.hide_scale_and_visibility_attributes()
        
        if self._fk_control_shape:
            control.set_curve_type(self._fk_control_shape)
        
        xform = space.create_xform_group(control.control)
        drive = space.create_xform_group(control.control,'driver')
                
        space.MatchSpace(transform, xform).translation_rotation()
        
        letter = space.get_axis_letter_aimed_at_child(self.joints[0])
        
        offset = self._fk_control_shape_offset
        
        if letter.find('-') > -1:
            offset = self._fk_control_shape_offset * -1 
        
        if letter.find('X') > -1:
            control.translate_shape(offset, 0, 0)
        if letter.find('Y') > -1:
            control.translate_shape(0, offset, 0)
        if letter.find('Z') > -1:
            control.translate_shape(0,0, offset)
        
        attr.connect_rotate(control.control, transform)
        
        cmds.parent(xform, self.control_group)
        
        attr.connect_rotate(aim_transform, drive)
        
        
    
    def _rig_extra_control(self, group1):
        
        parent_group = cmds.group(em = True, n = core.inc_name(self._get_name('group', 'extra')))
        aim_group = cmds.group(em = True, n = core.inc_name(self._get_name('group', 'aim_extra')))
        
        space.MatchSpace(self.joints[0], aim_group).translation_rotation()
        space.MatchSpace(self.joints[0], parent_group).translation_rotation()
        
        xform_parent_group = space.create_xform_group(parent_group)
        xform_aim_group = space.create_xform_group(aim_group)
        
        cmds.parent(xform_aim_group, group1)
        
        attr.connect_rotate(group1, parent_group)
        
        cmds.parent(xform_parent_group, self.setup_group)
        
        cmds.orientConstraint(aim_group, self.joints[0])
        
        control2 = self._create_control(sub = True)
        control2.hide_scale_and_visibility_attributes()
        control2 = control2.get()
    
        match = space.MatchSpace(self.joints[0], control2)
        match.translation_rotation()
    
        axis = self.eye_control_move[0]
        axis_value = self.eye_control_move[1]
                    
        if axis == 'X':
            cmds.move(axis_value, 0,0 , control2, os = True, relative = True)
            attr.connect_multiply('%s.translateZ' % control2, '%s.rotateY' % aim_group, -self.rotate_value )
            attr.connect_multiply('%s.translateY' % control2, '%s.rotateZ' % aim_group, self.rotate_value )
        if axis == 'Y':
            cmds.move(0,axis_value, 0, control2, os = True, relative = True)
            attr.connect_multiply('%s.translateZ' % control2, '%s.rotateX' % aim_group, -self.rotate_value )
            attr.connect_multiply('%s.translateY' % control2, '%s.rotateZ' % aim_group, self.rotate_value )
        if axis == 'Z':
            cmds.move(0,0,axis_value, control2, os = True, relative = True)
            attr.connect_multiply('%s.translateX' % control2, '%s.rotateY' % aim_group, self.rotate_value )
            attr.connect_multiply('%s.translateY' % control2, '%s.rotateX' % aim_group, -self.rotate_value )
        
        xform2 = space.create_xform_group(control2)            
        cmds.parent(xform2, parent_group)
        cmds.parent(xform_parent_group, self.control_group)
        
        if axis == 'X':
            cmds.transformLimits(control2,  tx =  (0, 0), etx = (1,1) )
        if axis == 'Y':
            cmds.transformLimits(control2,  ty =  (0, 0), ety = (1,1) )
        if axis == 'Z':
            cmds.transformLimits(control2,  tz =  (0, 0), etz = (1,1) )

    def set_parent(self, parent):
        self.parent = parent
    
    def set_local_parent(self, local_parent):
        self.local_parent = local_parent 
    
    def set_extra_control(self, axis, value, rotate_value = 25, limit = 1):
        
        self.eye_control_move = [axis, value]
        self.extra_control = True
        self.rotate_value = rotate_value
    
    def set_create_fk_control(self, bool_value, offset_control_shape = 1, control_shape = None):
        self._fk_control_shape = control_shape
        self._fk_control_shape_offset = offset_control_shape
        self._create_fk = bool_value
    
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
        
        
        
        match = space.MatchSpace(self.joints[0], locator)
        match.translation_rotation()
        
        cmds.parent(locator, self.control_group)
        
        line = rigs_util.RiggedLine(locator, control, self._get_name())        
        cmds.parent( line.create(), self.control_group)
        
        
        cmds.setAttr('%s.translateX' % locator, l = True)
        cmds.setAttr('%s.translateY' % locator, l = True)
        cmds.setAttr('%s.translateZ' % locator, l = True)
        cmds.setAttr('%s.rotateX' % locator, l = True)
        cmds.setAttr('%s.rotateY' % locator, l = True)
        cmds.setAttr('%s.rotateZ' % locator, l = True)
        cmds.hide(locator)
        
        
class JawRig(FkLocalRig):
    def __init__(self, description, side = None):
        super(JawRig, self).__init__(description, side)
        self.jaw_slide_offset = .1
        self.jaw_slide_attribute = True
        self.jaw_slide_rotate_axis = 'X'
        self.jaw_slide_translate_axis = 'Z'
        self.follow_world = False
    
    def _attach(self, source_transform, target_transform):
        
        if not self.follow_world:
            local_group, local_xform = super(JawRig, self)._attach(source_transform, target_transform)
        if self.follow_world:
            cmds.parentConstraint(source_transform, target_transform)
        
        control = self.controls[-1]
                
        live_control = rigs_util.Control(control)
        live_control.rotate_shape(0, 0, 90)
        
        
        var = attr.MayaNumberVariable('autoSlide')
        var.set_variable_type(var.TYPE_DOUBLE)
        var.set_value(self.jaw_slide_offset)
        var.set_keyable(self.jaw_slide_attribute)
        var.create(control)
        
        driver = space.create_xform_group(control, 'driver')
        if not self.follow_world:
            driver_local = space.create_xform_group(local_group, 'driver')
            attr.connect_translate(driver, driver_local)
            
        multi = attr.connect_multiply('%s.rotate%s' % (control, self.jaw_slide_rotate_axis), '%s.translate%s' % (driver, self.jaw_slide_translate_axis))
        
        #cmds.connectAttr('%s.outputX' % multi, '%s.translate%s' % (driver_local, self.jaw_slide_translate_axis))
        var.connect_out('%s.input2X' % multi)
        
        if not self.follow_world:
            return local_group, local_xform  
    
    def set_jaw_slide_offset(self, value):
        self.jaw_slide_offset = value
        
    def set_create_jaw_slide_attribute(self, bool_value):
        self.jaw_slide_attribute = bool_value
        
    def set_jaw_slide_rotate_axis(self, axis_letter):
        
        self.jaw_slide_rotate_axis = axis_letter.capitalize()
        
    def set_jaw_slide_translate_axis(self, axis_letter):
        
        self.jaw_slide_translate_axis = axis_letter.capitalize()
        
    def set_follow_world(self, bool_value):
        """
        If you need the rig to not stay at the origin but move with the rig.
        """
        self.follow_world = bool_value
        
class FeatherStripRig(CurveRig):
    """
    New feather building class. 
    Try giving it two curves using set_curve(['curve1', 'curve2']) and see what happens.
    This will need an example rig to show how it works. 
    """
    
    def __init__(self, description, side = ''):
        
        super(FeatherStripRig, self).__init__(description, side)
        
        self.curve_controls = []
        
        self.feather_count = 10
        self.feather_joint_sections = 3
        
        self.feather_tilt = 1
        self._feather_lift = 0
        
        self.object_rotation_up = None
        
        self.top_broad_joint = None
        self.btm_broad_joint = None
        
        self.u_spans = 6
        self.v_spans = 3
        
        self.up_parent = None
        
        self.skin_mesh = None
        self.wrap_mesh = None
        
        self.attribute_control = None
        
        self._top_feather_mesh = None
        self._btm_feather_mesh = None
        self._feather_mesh = None
        
        self._feather_width_scale = 1
        self._feather_length_scale = 1
        self._feather_length_random = None
        
        self._distance_falloff = 3
        
        
        self.curve_skin_joints = []
        self._skin_joint_create = []
        self.skin_joints = []

        self.tweak_controls = []
        self.tweak_joints = []
        
        self._internal_skin_curve_joints = True
        
        self._attribute_description = ''
        
        self.color = None
        self.color_flip = False
    
        self._feather_tangent_first_curve = False
    
    def _add_attributes(self):
        
        attribute_control = self._get_attribute_control()
        
        if not cmds.objExists('%s.featherVisibility' % attribute_control):
            cmds.addAttr(attribute_control, ln = 'featherVisibility', at = 'bool', dv = 1, k = True)
        if not cmds.objExists('%s.subVisibility' % attribute_control):
            cmds.addAttr(attribute_control, ln = 'subVisibility', at = 'bool', dv = 0, k = True)
        
        
        if self._attribute_description:
            attr.create_title(attribute_control, 'FEATHER_%s' % self._attribute_description.upper())
        if not self._attribute_description:
            attr.create_title(attribute_control, 'FEATHER')
        
        
        #self._add_attribute('featherVisibility', bool = True)
        #self._add_attribute('subVisibility', bool = True)
        self._add_attribute('liftTop')
        self._add_attribute('liftBtm')
        self._add_attribute('tiltTop')
        self._add_attribute('tiltBtm')
        self._add_attribute('xCurl')
        self._add_attribute('yCurl')
        self._add_attribute('zCurl')
            
        
    
    def _get_attribute_name(self, name):
    
        description = self._attribute_description
        if description:
            description = str(description)
            description = description[0].upper() + description[1:]
            
    
        return name + description
    
    def _get_attribute(self, name):
        """
        returns attribute_control.attribute
        """
        attribute = self._get_attribute_name(name)
        
        control = self._get_attribute_control()
        
        full_name = control + '.' + attribute
        
        return full_name
    
    def _add_attribute(self, name, attribute_control = None, bool = False):
        
        if not attribute_control:
            attribute_control = self._get_attribute_control()
        
        attribute = self._get_attribute_name(name)
        
        if not cmds.objExists('%s.%s' % (attribute_control, attribute)):
            if not bool:
                cmds.addAttr(attribute_control, ln = attribute, k = True, at = 'float')
            if bool:
                cmds.addAttr(attribute_control, ln = attribute, k = True, at = 'bool', dv = 1)
                
                
    def _get_attribute_control(self, ):
        
        control = self.control_group
        
        if self.tweak_controls:
            control = self.tweak_controls[0]
        
        if self.attribute_control:
            control = self.attribute_control
        
        return control
        
    def _create_joint_strips(self):

        strip1_name = self._get_name(description = 'strip')
        strip2_name = self._get_name(description = 'stripEnd')
        
        joints1 = rigs_util.create_joints_on_curve(self.curves[0],self.feather_count,strip1_name)
        joints2 = rigs_util.create_joints_on_curve(self.curves[1],self.feather_count,strip2_name)
    
        joints1_group = joints1[1]
        joints1 = joints1[0]
    
        joints2_group = joints2[1]
        joints2 = joints2[0]
        
        cmds.parent(joints1_group, self.setup_group)
        cmds.parent(joints2_group, self.setup_group)
        
        return joints1, joints2
        
    def _skin_curves(self):
        
        if self.curve_skin_joints and not self._internal_skin_curve_joints:
        
            skin = cmds.skinCluster(self.curve_skin_joints, self.curves[1], tsb = True, dr = self._distance_falloff, n = 'skin_%s' % self.curves[1], rui = True)[0]
            cmds.setAttr('%s.skinningMethod' % skin, 1)
        
        if self.curve_skin_joints and self._internal_skin_curve_joints:
        
            tweak_ends = self.get_tweak_joint_ends()
            skin_ends = self.get_skin_joint_ends()
            
            ends = tweak_ends + skin_ends
        
            skin = cmds.skinCluster(ends, self.curves[1], tsb = True, dr = self._distance_falloff, n = 'skin_%s' % self.curves[1], rui = True)[0]
            cmds.setAttr('%s.skinningMethod' % skin, 1)
        if self.skin_mesh and not self.wrap_mesh:
            deform.skin_mesh_from_mesh(self.skin_mesh, self.curves[0])
            
        if self.wrap_mesh:
            deform.create_wrap(self.wrap_mesh, self.curves[0])
    
    def _create_inc_control(self, geo_name, sub, inc, joint):
        control_inst = self._create_control(description = '%s' % (inc+1), sub = sub)
        
        control = control_inst.control
        
        control_xform = space.create_xform_group(control)
        
        if inc == 0:
            control_inst.scale_shape(2, 2, 2)
        
        if self.side == 'R':
            control_inst.scale_shape(-1, -1, -1)
        
        space.MatchSpace(joint, control_xform).translation_rotation()
                
        
        cmds.parent(joint, control)
        cmds.hide(joint)
        #cmds.parentConstraint(control, joint)
        
        driver3 = None
        
        if inc == 0:
            driver_tilt = space.create_xform_group(control, 'driver_tilt')
            driver3 = space.create_xform_group(control, 'driver3')
        driver2 = space.create_xform_group(control, 'driver2')
        space.create_xform_group(control, 'driver')
        
        if inc == 0:
            cmds.setAttr('%s.rotateX' % driver_tilt, self.feather_tilt)
            if self._feather_lift:
                cmds.setAttr('%s.rotateZ' % driver_tilt, self._feather_lift)
        
        return control, control_xform, driver3, driver2
    
    def _create_curve_joint(self, curve_percent1, curve_percent2, description, invert):
        
        pos1 = cmds.pointOnCurve( self.curves[0], pr=curve_percent1, p=True, top = True)
        pos2 = cmds.pointOnCurve( self.curves[1], pr=curve_percent2, p=True, top = True)
        
        cmds.select(cl = True)
        joint1 = cmds.joint(n = core.inc_name(self._get_name('joint', description)), p = pos1)
        joint2 = cmds.joint(n = core.inc_name(self._get_name('joint', description)), p = pos2)
        
        space.orient_x_to_child(joint1, invert = invert)
        
        return joint1, joint2
        
    def _create_skin_joint(self):
        
        inc = 1
        
        for joint in self._skin_joint_create:
            invert = False
            if self.side == 'R':
                invert = True
            
            joint1, joint2 = self._create_curve_joint(joint[0], joint[1], 'skin%s' % inc, invert)
            
            self.curve_skin_joints.append(joint2)
            
            if joint[2] and cmds.objExists(joint[2]):
                cmds.parentConstraint(joint[2], joint1, mo = True)
            
            self.skin_joints.append([joint1, joint2])
            
            cmds.parent(joint1, self.setup_group)
    
    def _create_curve_control(self):
        
        inc = 1
        
        for curve_control in self.curve_controls:
            
            invert = False
            if self.side == 'R':
                invert = True
            
            joint1, joint2 = self._create_curve_joint(curve_control[0], curve_control[1], 'tweak%s' % inc, invert)
            
            control = self._create_control('tweak', sub = False)
            
            control.scale_shape(15,15,15)
            control.rotate_shape(0,0,-90)
            
            inc+=1
            
            if invert:
                control.scale_shape(-1,-1,-1)
            
            control.hide_scale_and_visibility_attributes()
            
            control = control.control
            xform = space.create_xform_group(control)
            driver = space.create_xform_group(control, 'driver')
            
            space.MatchSpace(joint1, xform).translation_rotation()
            cmds.parentConstraint(control, joint1)
            self.tweak_controls.append(control)
            self.curve_skin_joints.append(joint2)
            self.tweak_joints.append([joint1, joint2])
            
            cmds.parent(joint1, self.setup_group)
            cmds.parent(xform, self.control_group)
    
    def _create_geo(self, joint1, joint2, invert):
        loc1 = cmds.spaceLocator(n = core.inc_name(self._get_name('temp')))[0]
        loc2 = cmds.spaceLocator(n = core.inc_name(self._get_name('temp')))[0]
        
        distance = space.get_distance(joint1, joint2)
        
        if not invert:
            cmds.move(distance, 0, 0, loc2)
        if invert:
            cmds.move((distance*-1), 0, 0, loc2)
        
        geo_name = geo.create_two_transforms_mesh_strip(loc1,loc2,offset_axis='Z', u_spans=self.u_spans, v_spans = self.v_spans)
        nice_geo_name = self._get_name(description = 'geo')
        geo_name = cmds.rename(geo_name, core.inc_name(nice_geo_name))
        
        cmds.polyNormal(geo_name, normalMode = 0, userNormalMode = 0, ch = False)
        
        cmds.delete(loc1, loc2)
        
        return geo_name
    
    def _set_geo_color(self, geo_name):
        
        if self.color:
            
            r = self.color[0]
            g = self.color[1]
            b = self.color[2]
            
            if self.color_flip:
                r = r * .75
                g = g * .75
                b = b * .75
            
            cmds.polyColorPerVertex(geo_name, colorRGB = [r, g, b], cdo = True)
            
            if self.color_flip:
                self.color_flip = False
            else:
                self.color_flip = True
    
            return [r,g,b]
    
    def set_attribute_control(self, transform):
        self.attribute_control = transform
    
    def set_attribute_description(self, description):
        self._attribute_description = description
    
    def set_feather_up_parent(self, parent):
        self.up_parent = parent
    
    def set_feather_u_v_spans(self, u_spans, v_spans):
        
        self.u_spans = u_spans
        self.v_spans = v_spans
    
    def set_feather_count(self, value):
        self.feather_count = value
        
    def set_feather_joint_sections(self, value):
        self.feather_joint_sections = value
    
    def set_feather_tilt(self, value):
        
        self.feather_tilt = value
    
    def set_feather_lift(self, value):
        self._feather_lift = value
    
    def set_feather_tangent_first_curve(self, bool_value):
        self._feather_tangent_first_curve = bool_value
    
    def set_curve_skin_joints(self, joints, distance_falloff = 2):
        
        joints = vtool.util.convert_to_sequence(joints)
        
        self.curve_skin_joints = joints
        
        self._internal_skin_curve_joints = False
        
        self._distance_falloff = distance_falloff
    
    def set_curve_skin_falloff(self, value):
        self._distance_falloff = value
    
    def set_first_curve_skin_mesh(self, mesh):
        
        self.skin_mesh = mesh
        
    def set_first_curve_wrap_mesh(self, mesh):
        self.wrap_mesh = mesh
    
    def set_feather_blend(self, feather_mesh):
        self._feather_mesh = feather_mesh
    
    def set_feather_blend_top_btm(self, top_feather_mesh, btm_feather_mesh):
        self._top_feather_mesh = top_feather_mesh
        self._btm_feather_mesh = btm_feather_mesh
    
    def set_feather_width_scale(self, value):
        self._feather_width_scale = value
        
    def set_feather_length_scale(self, value):
        self._feather_length_scale = value
    
    def set_feather_length_random(self, min_value, max_value):
        self._feather_length_random = [min_value, max_value]
        
    def set_color(self, r,g,b):
        self.color = [r,g,b]
        
    def add_curve_control(self, percent_curve1, percent_curve2):
        self.curve_controls.append([percent_curve1, percent_curve2])
    
    def add_skin_joint(self, percent_curve1, percent_curve2, parent = None):
        self._skin_joint_create.append([percent_curve1,percent_curve2, parent])
    
    def get_tweak_joints(self):
        found = []
        
        for tweak_joint in self.tweak_joints:
            found.append(tweak_joint[0])
            
        return found
            
    def get_tweak_joint_ends(self):
        found =[]
        
        for tweak_joint in self.tweak_joints:
            found.append(tweak_joint[1])
        
        return found
    
    def get_skin_joint_ends(self):
        
        found = []
        
        for skin_joint in self.skin_joints:
            found.append(skin_joint[1])
        
        return found
    
    def create(self):
        super(FeatherStripRig, self).create()
        
        
        
        self._create_skin_joint()
        self._create_curve_control()
        
        
        attribute_control = self._get_attribute_control()
        self._add_attributes()
        
        self._skin_curves()
        
        if not len(self.curves) == 2:
            vtool.util.warning('Feather rig must have exactly two curves')
            return
        
        joints1, joints2 = self._create_joint_strips()
        
        joint_section_name = self._get_name('section')
        
        geo_group = self._create_group('geo')
        self.geo_group = geo_group

        cmds.connectAttr('%s.featherVisibility' % attribute_control, '%s.visibility' % geo_group)
        
        offset_amount = (1.0/(self.feather_count-1))
        offset_accum = 0
        
        color_dict = {}
        
        for inc in range(0, len(joints1)):
            
            cmds.setAttr('%s.inheritsTransform' % joints1[inc], 0)
            
            invert = False
            
            if self.side == 'R':
                invert = True
            
            geo_name = self._create_geo(joints1[inc], joints2[inc], invert)
            color = self._set_geo_color(geo_name)
            color_dict[geo_name] = color
            
            
            aim_group = cmds.group(em = True, n = 'aim_%s' % geo_name)
            
            joints = space.transforms_to_joint_chain([joints1[inc], joints2[inc]],joint_section_name)
            
            space.MatchSpace(joints1[inc], aim_group).translation_rotation()
            cmds.parent(aim_group, joints1[inc])
            
            world_up_vector = [0,1,0]
            point_node = None
            
            
            if not self._feather_tangent_first_curve:
                point_node = attr.get_attribute_input('%s.translateX' % joints2[inc], node_only = True)
            if self._feather_tangent_first_curve:
                point_node = attr.get_attribute_input('%s.translateX' % joints1[inc], node_only = True)
            
            if self.up_parent:
                world_up_vector = [0,0,0]
                point_node = None
                
            
            if not self.up_parent:
                aim_const = cmds.aimConstraint(joints2[inc], aim_group, wu = world_up_vector)[0]
            if self.up_parent:
                object_up = cmds.group(n = core.inc_name(self._get_name('up')), em = True)
                cmds.parent(object_up, self.up_parent)
                aim_const = cmds.aimConstraint(joints2[inc], aim_group, wu = world_up_vector, worldUpObject = self.up_parent, worldUpType = 'objectrotation')[0]
            
            if point_node:
                cmds.connectAttr('%s.tangent' % point_node, '%s.worldUpVector' % aim_const)
                
            space.create_xform_group(aim_group)
            
            cmds.parent(joints[0], aim_group)
            
            space.orient_x_to_child(joints[0], invert = invert)
            cmds.makeIdentity(joints[1], jo = True, apply = True)
            
            scale_offset = self._feather_length_scale
            
            if self._feather_length_random:
                scale_offset = self._feather_length_scale * random.uniform(self._feather_length_random[0], self._feather_length_random[1])
                
            
            if scale_offset != 1:
                cmds.setAttr('%s.scaleX' % joints[0], scale_offset)
                cmds.makeIdentity(joints[0], apply = True, s = True)
            
            scale_amount = cmds.getAttr('%s.translateX' % joints[1])
            scale_amount = scale_amount/4
            
            sub_joints = space.subdivide_joint(joints[0], joints[-1], self.feather_joint_sections)
            
            for sub_joint in sub_joints:
                space.orient_x_to_child(sub_joint, invert = invert)
            
            cmds.parent(joints[0], self.setup_group)
            
            cmds.parent(joints1[inc], self.control_group)
            cmds.setAttr('%s.drawStyle' % joints1[inc], 2)
            
            control_joints = []
            control_joints.append(joints[0])
            control_joints += sub_joints
            control_joints.append(joints[1])
            
            last_control = None
            
            normal_offset_accum = offset_accum
            
            if normal_offset_accum > 1:
                normal_offset_accum = 1 
            
            
            
            offset_accum += offset_amount
            
            controls = []
            control_xforms = []
            
            feather_top_btm_blends = []
            
            for inc2 in range(0, (len(control_joints)-1)):
                
                sub = True
                
                if inc2 == 0:
                    sub = False
                
                joint = control_joints[inc2]
                
                
                
                control, control_xform, driver3, driver2 = self._create_inc_control(geo_name, sub, inc2, joint)
                
                
                
                controls.append(control)
                control_xforms.append(control_xform)
                
                
                
                if inc2 == 0:
                    cmds.connectAttr('%s.featherVisibility' % attribute_control, '%s.visibility' % control_xform)
                    
                    attr.create_title(control, 'FEATHER')
                    
                    cmds.addAttr(control, ln = 'xCurl', k = True, at = 'float')
                    cmds.addAttr(control, ln = 'yCurl', k = True, at = 'float')
                    cmds.addAttr(control, ln = 'zCurl', k = True, at = 'float')
                    
                    cmds.parent(control_xform, aim_group)
                    
                    attr.connect_blend(self._get_attribute('liftBtm'), 
                                       self._get_attribute('liftTop'), 
                                       '%s.rotateZ' % driver3, normal_offset_accum)
                    
                    attr.connect_blend(self._get_attribute('tiltBtm'), 
                                       self._get_attribute('tiltTop'), 
                                       '%s.rotateX' % driver3, normal_offset_accum)
                    
                if inc2 == 1:
                    cmds.connectAttr('%s.subVisibility' % attribute_control, '%s.visibility' % control_xform)
                
                if inc2 != 0:
                                        
                    cmds.connectAttr(self._get_attribute('xCurl'), '%s.rotateX' % control_xform)
                    cmds.connectAttr(self._get_attribute('yCurl'), '%s.rotateY' % control_xform)
                    cmds.connectAttr(self._get_attribute('zCurl'), '%s.rotateZ' % control_xform)
                    
                
                    cmds.connectAttr('%s.xCurl' % controls[0], '%s.rotateX' % driver2)
                    cmds.connectAttr('%s.yCurl' % controls[0], '%s.rotateY' % driver2)
                    cmds.connectAttr('%s.zCurl' % controls[0], '%s.rotateZ' % driver2)
                    
                    
                    
                if last_control:
                    cmds.parent(control_xform, last_control)
                
                if self._top_feather_mesh and self._btm_feather_mesh and inc2 == 0:
                    
                    other_offset_accum = 1 - normal_offset_accum
                    
                    feather_top_btm_blends.append([[self._top_feather_mesh, other_offset_accum],[self._btm_feather_mesh, normal_offset_accum]])
                
                last_control = control
            
            cmds.parent(geo_name, joints[0])
            space.zero_out_transform_channels(geo_name)
            
            cmds.parent(geo_name, w = True)
            
            cmds.setAttr('%s.scaleX' % joints[0], scale_amount)
            
            cmds.parent(geo_name, joints[0])
            cmds.makeIdentity(geo_name, apply = True, t = True, r = True, s = True)
            
            cmds.parent(geo_name, geo_group)
            
            cmds.setAttr('%s.scaleX' % joints[0], 1)
            
            if self.side == 'R':
                
                cmds.setAttr('%s.scaleY' % geo_name, -1)
                cmds.setAttr('%s.scaleZ' % geo_name, 1)
                
            cmds.setAttr('%s.scaleZ' % geo_name, self._feather_width_scale)
            
            cmds.skinCluster(control_joints, geo_name, tsb = True, dr = 4, rui = True, n = 'skin_%s' % geo_name) 
            
            if self._feather_mesh and not self._btm_feather_mesh and not self._top_feather_mesh:
                deform.quick_blendshape(self._feather_mesh, geo_name)
                
            if feather_top_btm_blends:
                for blend in feather_top_btm_blends:
                    deform.quick_blendshape(blend[0][0], geo_name, blend[0][1])
                    deform.quick_blendshape(blend[1][0], geo_name, blend[1][1])
            
            new_curve = geo.create_curve_from_mesh_border(geo_name, -.25)
            control_inst = rigs_util.Control(controls[0])
            control_inst.copy_shapes(new_curve)
            
            
            
            r,g,b = color_dict[geo_name]
            r = r * 1.3
            g = g * 1.3
            b = b * 1.3
            if r > 1:
                r = 1
            if g > 1:
                g = 1
            if b> 1:
                b = 1
            control_inst.color_rgb(r,g,b)
            
            cmds.delete(new_curve)
            
class FeatherOnPlaneRig(PolyPlaneRig):
    def __init__(self, description, side):
        super(FeatherOnPlaneRig, self).__init__(description, side)
        
        self._quill_radius = 0.5
        self._follow_u = True
        self._feather_count = 5
        
        self._nucleus_name = ''
        self._hair_system_name = ''
        self._guide_geo = None
        self._quill_geo_group = None
        
        self._combine_quills = False
        
        self._tilt = 10
        
    def _convert_plane_to_curves(self, plane, count, u):
        
        model_group = self._create_group('model')
        curve_group = self._create_group('curve')
        dynamic_curve_group = self._create_group('dynamicCurves')
        feather_curve_group = self._create_group('featherCurves')
        self._model_group = model_group
        guide_group = self._create_group('guides')
        cmds.parent(guide_group, model_group)
        
        curves = geo.polygon_plane_to_curves(plane, count = count, u = u)
        
        quill_group = self._create_group('quill')
        quill_geo_group = self._create_group('quill_geo')
        cmds.parent(quill_geo_group, model_group)
        quill_dynamic_group = self._create_group('quill_dynamic')
        cmds.parent(quill_group, self.setup_group)
        cmds.parent(quill_dynamic_group, self.setup_group)
        cmds.parent(curves, quill_group)
        cmds.parent(curve_group, model_group)
        cmds.parent(feather_curve_group, curve_group)
        cmds.parent(dynamic_curve_group, curve_group)
    
        quill_ik_group = cmds.group(em = True, n = 'quill_ik_%s' % plane)
        cmds.parent(quill_ik_group, self.setup_group)
    
        feather_groups = []
        
        inc = 1
            
        for curve in curves:
            
            dynamic_curves = self._create_group('dynamicCurves', inc)
            cmds.parent(dynamic_curves, dynamic_curve_group)
        
            cmds.reverseCurve(curve, ch = False, rpo = 1)
            cmds.smoothCurve('%s.cv[*]' % curve, ch = False, rpo = 1, s = 1)
            geo.rebuild_curve(curve,10,degree=3)
            
            quill_geo = geo.create_quill(curve, self._quill_radius, spans = 20)
            
            feather_group = self._create_group('featherCurves', inc)
            cmds.parent(feather_group, feather_curve_group)
            
            
            feather_curves = geo.get_of_type_in_hierarchy('curves','nurbsCurve')
            
            guide_geo = cmds.duplicate('guide_feather_1', n = 'guideGeo_%s' % curve)[0]
            guide_geo_cvs = cmds.ls('%s.vtx[*]' % guide_geo, flatten = True)
            cmds.parent(guide_geo, guide_group)
            
            feather_curves = geo.transfer_from_curve_to_curve('quill_curve', curve, feather_curves, plane, twist = self._tilt)        
            self._guide_geo = geo.transfer_from_curve_to_curve('quill_curve', curve, guide_geo_cvs, plane, twist = self._tilt) 
            
            temp_curves = []
            
            for sub_curve in feather_curves:
                new_name = cmds.rename(sub_curve, core.inc_name(self._get_name('sub_curve', inc)))
                temp_curves.append(new_name)
            
            feather_curves = temp_curves
            
            cmds.makeIdentity(feather_curves, apply=True, t = True, r = True)
            cmds.parent(feather_curves, feather_group)
            dynamic_quill = self._follicle(quill_geo, curve, feather_curves, dynamic_curves, quill_ik_group, inc)
            cmds.parent(dynamic_quill, quill_dynamic_group)
            cmds.parent(quill_geo, quill_geo_group)
            
            inc += 1
        
        self._quill_geo_group = quill_geo_group
        
        
        
    
    def _follicle(self, mesh, quill_curve, curves, dynamic_curve_group, ik_group, inc):
        
        nucleus_quill = 'nucleus_quill'
        nucleus_strand = 'nucleus_strand'
        nucleus_quill_name = 'quill'
        nucleus_strand_name = 'strand'
        
        
        if self._nucleus_name:
            nucleus_quill = 'nucleus_%s_quill' % self._nucleus_name
            nucleus_strand = 'nucleus_%s_strand' % self._nucleus_name 
            nucleus_quill_name = '%s_quill' % self._nucleus_name
            nucleus_strand_name = '%s_strand' % self._nucleus_name
        
        quill_hair_system = 'hairSystem_quill'
        strand_hair_system = 'hairSystem_strands'
        hair_system_quill_name = 'quill'
        hair_system_strand_name = 'strands'
        
        if self._hair_system_name:
            quill_hair_system = 'hairSystem_%s_quill' % self._hair_system_name
            strand_hair_system = 'hairSystem_%s_strands' % self._hair_system_name
            hair_system_quill_name = '%s_quill' % self._hair_system_name
            hair_system_strand_name = '%s_strands' % self._hair_system_name
        
        if not cmds.objExists(nucleus_quill):
            nucleus_quill = fx.create_nucleus(name=nucleus_quill_name)
        if not cmds.objExists(nucleus_strand):
            nucleus_strand = fx.create_nucleus(name=nucleus_strand_name)
        
        if not cmds.objExists(quill_hair_system):
            quill_hair_system = fx.create_hair_system(hair_system_quill_name,nucleus_quill)[0]
        if not cmds.objExists(strand_hair_system):
            strand_hair_system = fx.create_hair_system(hair_system_strand_name,nucleus_strand)[0]
        
        follicle = fx.make_curve_dynamic(quill_curve, quill_hair_system)
        
        
        joints = geo.create_oriented_joints_on_curve(quill_curve,25, description = 'quill', attach = True)
        
        cmds.skinCluster(mesh, joints, tsb = True)
        
        ik = space.get_ik_from_joint(joints[0])
        
        cmds.parent(joints[0], ik_group)
        cmds.parent(ik, ik_group)
    
        quill_output = fx.get_follicle_output_curve(follicle)
        input_curve = fx.get_follicle_input_curve(follicle)
         
        self._rig_curve(input_curve, inc)
        
        quill_output = cmds.rename(quill_output, 'dynamic_%s' % quill_curve)   
        
        for curve in curves:
            follicle = fx.make_curve_dynamic(curve,hair_system=strand_hair_system, mesh= mesh)
            outputs = fx.get_follicle_output_curve(follicle)
    
            cmds.parent(outputs, dynamic_curve_group)
            
            for output in outputs:
                cmds.rename(output, 'dynamic_%s' % curve)                
    
        return quill_output
    
    def _rig_curve(self, curve, inc):
        
        joints = geo.create_joints_on_curve(curve, 4, '%s_%s_1_%s' % (self.description, inc, self.side), attach=False)
        
        invert = False
        if self.side == 'R':
            invert = True
        
        for joint in joints:
            space.orient_x_to_child(joint, invert)
        
        last_control = None    
        for joint in joints:
            if joint == joints[-1]:
                continue
            
            control = self._create_control(description = inc)
            control.rotate_shape(0, 0, 90)
            xform = space.create_xform_group(control.control)
            
            space.MatchSpace(joint, xform).translation_rotation()
            control.control, joint
            cmds.parentConstraint(control.control, joint, mo = True)
            
            if not last_control:
                cmds.parent(xform, self.control_group)
            
            if last_control:
                cmds.parent(xform, last_control)
            
            last_control = control.control
        
        cmds.skinCluster(curve, joints, tsb = True)
        cmds.skinCluster(self._guide_geo, joints, tsb = True)
        cmds.parent(joints[0], self.setup_group)
    
    def _combine_quill_geo(self):
        
        result = cmds.polyUnite(self._quill_geo_group, ch = True, mergeUVSets = 1, name = core.inc_name(self._get_name('quills')))
        cmds.parent(result, self._model_group)
        
        cmds.parent(self._quill_geo_group, self.setup_group)
        
        
    
    def set_nucleus_name(self, name):
        self._nucleus_name = name
        
    def set_hair_system_name(self, name):
        self._hair_system_name = name
    
    def set_follow_u(self, bool_value):
        self._follow_u = bool_value
        
    def set_feather_count(self, int_value):
        self._feather_count = int_value
    
    def set_combine_quills(self, bool_value):
        self._combine_quills = bool_value
        
    def set_tilt(self, float_value):
        self._tilt = float_value
    
    def create(self):
        super(FeatherOnPlaneRig, self).create()
        
        self._convert_plane_to_curves(self.poly_plane, self._feather_count, self._follow_u)
        
        if self._combine_quills:
            self._combine_quill_geo()