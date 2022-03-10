# Copyright (C) 2022 Louis Vottero louis.vot@gmail.com    All rights reserved.

from __future__ import absolute_import

import string
import math

from .. import util, util_math

if util.is_in_maya():
    import maya.cmds as cmds

from . import api
from . import core
from . import attr
from . import space
from . import anim
from . import curve
from . import geo
from . import deform

from vtool import logger
log = logger.get_logger(__name__) 

class Control(object):
    """
    Convenience for creating controls
    
    Args:
        name (str): The name of a control that exists or that should be created.
    """
    
    def __init__(self, name, tag = True):
        
        self.control = name
        self.curve_type = None
        
        if not cmds.objExists(self.control):
            self._create(tag)
            
        self.shapes = core.get_shapes(self.control)
        
        if not self.shapes:
            util.warning('%s has no shapes' % self.control)
            
        
            
    def _create(self, tag = True):
        
        self.control = cmds.circle(ch = False, n = self.control, normal = [1,0,0])[0]
        
        if self.curve_type:
            self.set_curve_type(self.curve_type)
        
        if tag:
            try:
                cmds.controller(self.control)
            except:
                pass
        
    def _get_components(self):
        
        self.shapes = core.get_shapes(self.control)
        
        return core.get_components_from_shapes(self.shapes)
        
    def set_curve_type(self, type_name):
        """
        Set the curve type. The type of shape the curve should have.
        
        Args:
        
            type_name (str): eg. 'circle', 'square', 'cube', 'pin_round' 
        """
        
        shapes = core.get_shapes(self.control)
        color =attr.get_color(shapes[0], as_float = True)
        
        curve_data = curve.CurveDataInfo()
        curve_data.set_active_library('default_curves')
        curve_data.set_shape_to_curve(self.control, type_name)
        
        self.shapes = core.get_shapes(self.control)
        
        if type(color) == list:
            attr.set_color_rgb(self.shapes, *color)
        else:
            attr.set_color(self.shapes, color)
    
    def set_curve_as_text(self, text):
        
        shapes = core.get_shapes(self.control)
        
        color = attr.get_color(shapes[0])
        
        curve.set_shapes_as_text_curves(self.control, text)
        
        self.shapes = core.get_shapes(self.control)
        
        attr.set_color(self.shapes, color)
    
    def set_to_joint(self, joint = None, scale_compensate = False):
        """
        Set the control to have a joint as its main transform type.
        
        Args:
            joint (str): The name of a joint to use. If none joint will be created automatically.
            scale_compensate (bool): Whether to connect scale of parent to inverseScale of joint. 
            This causes the group above the joint to be able to change scale value without affecting the control's look. 
        """
        
        
        cmds.select(cl = True)
        name = self.get()
        
        joint_given = True
        temp_parent = None
        
        if not joint:
            joint = cmds.joint()
            
            cmds.delete(cmds.parentConstraint(name, joint))
            cmds.delete(cmds.scaleConstraint(name, joint))
            #space.MatchSpace(name, joint).translation_rotation() 
            
            buffer_group = cmds.group(em = True, n = core.inc_name('temp_%s' % joint ))
            
            cmds.parent(buffer_group, self.control)
            cmds.parent(joint, buffer_group)
            cmds.makeIdentity(buffer_group, t = True, r = True, s = True, jo = True, apply = True)
            
            cmds.parent(joint, w = True)
            
            temp_parent = cmds.listRelatives(joint, p = True)
            
            cmds.delete(buffer_group)
                
            joint_given = False
        
        shapes = core.get_shapes(self.control, shape_type = 'nurbsCurve')
        
        for shape in shapes:
            cmds.parent(shape, joint, r = True, s = True)
        
        if not joint_given:
            
            parent = cmds.listRelatives(name, p = True)
            
            if parent:
                cmds.parent(joint, parent)
                if temp_parent:
                    cmds.delete(temp_parent)
                cmds.makeIdentity(joint, r = True, s = True, apply = True)
                
            space.transfer_relatives(name, joint)
            
            if scale_compensate:
                parent = cmds.listRelatives(joint, p = True)
                if parent:
                    cmds.connectAttr('%s.scale' % parent[0], '%s.inverseScale' % joint)
            
        if joint_given:
            space.transfer_relatives(name, joint, reparent = False)
        
        transfer = attr.TransferVariables()
        transfer.transfer_control(name, joint)
        attr.transfer_output_connections(name, joint)
        
        cmds.setAttr('%s.radius' % joint, l = True, k = False, cb = False)
        cmds.setAttr('%s.drawStyle' % joint, 2)
            
        curve_type_value = ''
            
        if cmds.objExists('%s.curveType' % name):
            curve_type_value = cmds.getAttr('%s.curveType' % name)    
        
        cmds.delete(name)
        
        if not joint_given:
            joint = cmds.rename(joint, name)
        
        self.control = joint
        
        if joint_given:
            core.rename_shapes(self.control)
            
        var = attr.MayaStringVariable('curveType')
        var.create(joint)
        var.set_value(curve_type_value)
        
    def translate_shape(self, x,y,z):
        """
        Translate the shape curve cvs in object space.
        
        Args:
            x (float)
            y (float)
            z (float)
        """
        components = self._get_components()
        
        if components:
            cmds.move(x,y,z, components, relative = True, os = True, wd = True)
        
    def rotate_shape(self, x,y,z):
        """
        Rotate the shape curve cvs in object space
        
        Args:
            x (float)
            y (float)
            z (float)
        """
        components = self._get_components()
        
        if components:
            cmds.rotate(x,y,z, components, relative = True)
            
    def scale_shape(self, x,y,z, use_pivot = True):
        """
        Scale the shape curve cvs relative to the current scale.
        
        Args:
            x (float)
            y (float)
            z (float)
            use_pivot (bool)
        """
        
        components = self._get_components()
        
        if use_pivot:
            pivot = cmds.xform( self.control, q = True, rp = True, ws = True)
        if not use_pivot:
            shapes = core.get_shapes(self.control, shape_type = 'nurbsCurve')
            components = core.get_components_from_shapes(shapes)
            
            bounding = space.BoundingBox(components)
            pivot = bounding.get_center()
        
        if components:
            cmds.scale(x,y,z, components, pivot = pivot, r = True)

    def color(self, value):
        """
        Set the color of the curve.
        
        Args:
            value (int): This corresponds to Maya's color override value.
        """
        shapes = core.get_shapes(self.control)
        
        if type(value) == list or type(value) == tuple:
            attr.set_color_rgb(shapes, *value)
        else:
            attr.set_color(shapes, value)
    
    def color_rgb(self, r=0,g=0,b=0):
        """
        Maya 2015 and above.
        Set to zero by default.
        Max value is 1.0.
        """
        
        shapes = core.get_shapes(self.control)
        
        attr.set_color_rgb(shapes, r,g,b)
    
    def get_color(self):
        
        shapes = core.get_shapes(self.control)
        
        color = attr.get_color(shapes[0], as_float = True)
        
        if type(color) != list:
            color = attr.color_to_rgb(color)
        
        return color
        
    
    def set_color_hue(self, value):
        color = self.get_color()
        color = attr.set_color_hue(color, value)
        self.color_rgb(*color)
    
    def set_color_saturation(self, value):
        color = self.get_color()
        color = attr.set_color_saturation(color, value)
        self.color_rgb(*color)
    
    def set_color_value(self, value):
        
        color = self.get_color()
        color = attr.set_color_value(color, value)
        self.color_rgb(*color)
    
    def show_rotate_attributes(self):
        """
        Unlock and set keyable the control's rotate attributes.
        """
        cmds.setAttr('%s.rotateX' % self.control, l = False, k = True)
        cmds.setAttr('%s.rotateY' % self.control, l = False, k = True)
        cmds.setAttr('%s.rotateZ' % self.control, l = False, k = True)
        
    def show_scale_attributes(self):
        """
        Unlock and set keyable the control's scale attributes.
        """
        cmds.setAttr('%s.scaleX' % self.control, l = False, k = True)
        cmds.setAttr('%s.scaleY' % self.control, l = False, k = True)
        cmds.setAttr('%s.scaleZ' % self.control, l = False, k = True)
    
    def hide_attributes(self, attributes = None):
        """
        Lock and hide the given attributes on the control. If no attributes given, hide translate, rotate, scale and visibility.
        
        Args:
            
            attributes (list): List of attributes, eg. ['translateX', 'translateY']
        """
        if attributes:
            attr.hide_attributes(self.control, attributes)
            
        if not attributes:
            self.hide_translate_attributes()
            self.hide_rotate_attributes()
            self.hide_scale_and_visibility_attributes()
        
    def hide_translate_attributes(self):
        """
        Lock and hide the translate attributes on the control.
        """
        
        attr.hide_attributes(self.control, ['translateX',
                                     'translateY',
                                     'translateZ'])
        
    def hide_rotate_attributes(self):
        """
        Lock and hide the rotate attributes on the control.
        """
        attr.hide_rotate(self.control)
        
    def hide_scale_attributes(self):
        """
        Lock and hide the scale attributes on the control.
        """
        attr.hide_attributes(self.control, ['scaleX',
                                     'scaleY',
                                     'scaleZ'])
        
    def hide_visibility_attribute(self):
        """
        Lock and hide the visibility attribute on the control.
        """
        attr.hide_attributes(self.control, ['visibility'])
    
    def hide_scale_and_visibility_attributes(self):
        """
        Lock and hide the visibility and scale attributes on the control.
        """
        self.hide_scale_attributes()
        self.hide_visibility_attribute()
    
    def hide_keyable_attributes(self):
        """
        Lock and hide all keyable attributes on the control.
        """
        attr.hide_keyable_attributes(self.control)
        
    def rotate_order(self, xyz_order):
        """
        Set the rotate order on a control.
        """
        
        if type(xyz_order) == int:
            value = xyz_order
        else:
            value = 0
            
            if xyz_order == 'xyz':
                value = 0
            if xyz_order == 'yzx':
                value = 1
            if xyz_order == 'zxy':
                value = 2
            if xyz_order == 'xzy':
                value = 3
            if xyz_order == 'yxz':
                value = 4
            if xyz_order == 'zyx':
                value = 5
            
        
        cmds.setAttr('%s.rotateOrder' % self.control, value)
    
    def color_respect_side(self, sub = False, center_tolerance = 0.001, offset = 0):
        """
        Look at the position of a control, and color it according to its side on left, right or center.
        
        Args:
            sub (bool): Wether to set the color to sub colors.
            center_tolerance (float): The distance the control can be from the center before its considered left or right.
            
        Returns:
            str: The side the control is on in a letter. Can be 'L','R' or 'C'
        """
        position = cmds.xform(self.control, q = True, ws = True, t = True)
        
        if position[0] > offset:
            color_value = attr.get_color_of_side('L', sub)
            side = 'L'

        if position[0] < offset:
            color_value = attr.get_color_of_side('R', sub)
            side = 'R'
            
        if position[0] < (center_tolerance + offset) and position[0] > ((center_tolerance * -1) + offset):
            color_value = attr.get_color_of_side('C', sub)
            side = 'C'
            
        self.color(color_value)
        
        return side
            
    def get(self):
        """
        Returns:
            str: The name of the control.
        """
        return self.control
    
    def get_xform_group(self, name = 'xform'):
        """
        This returns an xform group above the control.
        
        Args:
            name (str): The prefix name supplied when creating the xform group.  Usually xform or driver.
            
        """
        
        return space.get_xform_group(self.control, name)
    
    def create_xform(self, prefix = 'xform'):
        """
        Create an xform above the control.
        
        Returns:
            str: The name of the xform group.
        """
        
        xform = space.create_xform_group(self.control, prefix)
        
        return xform
        
    def rename(self, new_name):
        """
        Give the control a new name.
        
        Args:
            
            name (str): The new name.
        """
        
        new_name = core.inc_name(new_name)
        
        rename_message_groups(self.control, new_name)
        
        new_name = cmds.rename(self.control, new_name)
        
        constraints = cmds.listRelatives( new_name, type = 'constraint')
        
        if constraints:
            for constraint in constraints:
                new_constraint = constraint.replace(self.control, new_name)
                cmds.rename(constraint, new_constraint)
        
        
        
        self.control = new_name
        core.rename_shapes(self.control)
        
        return self.control
        
    def delete_shapes(self):
        """
        Delete the shapes beneath the control.
        """
        self.shapes = core.get_shapes(self.control)
        
        cmds.delete(self.shapes)
        self.shapes = []
        
    def copy_shapes(self, transform):
        
        if not core.has_shape_of_type(transform, 'nurbsCurve'):
            return
        
        orig_shapes = core.get_shapes(self.control, shape_type='nurbsCurve')
        
        temp = cmds.duplicate(transform)[0]
        
        cmds.parent(temp, self.control)
        cmds.makeIdentity(temp, apply = True, t = True, r = True, s = True)
        
        shapes = core.get_shapes(temp, shape_type='nurbsCurve')
        
        color = None
        
        colors = {}
        
        if shapes:
            
            inc = 0
            
            for shape in shapes:
                
                if inc < len(orig_shapes) and inc < len(shapes):
                    
                    color = attr.get_color(orig_shapes[inc])
                
                colors[shape] = color
                
                if color:
                    if type(color) != list:
                        attr.set_color(shape, color)
                    if type(color) == list:
                        attr.set_color_rgb(shape, color[0], color[1], color[2])
               
                cmds.parent(shape, self.control, r = True, shape = True)
                        
                inc += 1
        
        cmds.delete(orig_shapes)        
        cmds.delete(temp)
        
        core.rename_shapes(self.control)

    def fix_sub_control_shapes(self):
        
        fix_sub_controls(self.control)

class ControlGroup(object):
    
    def __init__(self, control_group):
        self.control_group = control_group
        
        self.controls = []
        self.sub_controls = []
        self.joints = []
        self.all_controls = []
        self.dict = {}
        self._get_dict_data()
    
    def _get_dict_data(self):
        control_group = self.control_group
        
        found_dict = get_important_info(control_group)
        
        self.load_data(found_dict)
    
    def load_data(self, attr_dict):
        
        self.dict = attr_dict
        
        for key in attr_dict:
            
            value = attr_dict[key]
            
            exec('self.%s = "%s"' % (key, value))
    
class StoreControlData(attr.StoreData):
    
    def __init__(self, node = None):
        super(StoreControlData, self).__init__(node)
        
        self.controls = []
        
        self.side_replace = ['_L', '_R', 'end']
        
        self._namespace = None
        
    def _get_single_control_data(self, control):
        
        if not control:
            return
    
        attributes = cmds.listAttr(control, k = True)
            
        if not attributes:
            attributes = []
            
        sub_attributes = {}
        
        shapes = core.get_shapes(control, no_intermediate = True)
        
        if shapes:
            for shape in shapes:
                sub_attribute = cmds.listAttr(shape, k = True)
                
                if sub_attribute:
                
                    for sub in sub_attribute:
                        sub_attributes[sub] = None
            
        if sub_attributes:
            attributes += list(sub_attributes.keys())
            
        if not attributes:
            return
        
        attribute_data = {}
        
        for attribute in attributes:
            
            attribute_name = '%s.%s' % (control, attribute)
            
            if not cmds.objExists(attribute_name):
                continue
            
            if cmds.getAttr(attribute_name, type = True) == 'message':
                continue

            if cmds.getAttr(attribute_name, type = True) == 'string':
                continue
            
            value = cmds.getAttr(attribute_name)
            attribute_data[attribute] = value 
                    
        return attribute_data

    
    def _get_control_data(self):
        
        controls = []
        
        if self.controls:
            controls = self.controls
        
        if not self.controls:
            controls = get_controls()
        
        control_data = {}
        
        for control in controls:
            
            if cmds.objExists('%s.POSE' % control):
                continue
            
            attribute_data = self._get_single_control_data(control)
            
            if attribute_data:
                control_data[control] = attribute_data
                        
        return control_data
        
    def _has_transform_value(self, control):
        attributes = ['translate', 'rotate']
        axis = ['X','Y','Z']
        
        for attribute in attributes:
            for a in axis:
                
                attribute_name = '%s.%s%s' % (control, attribute, a) 
                
                if not cmds.objExists(attribute_name):
                    return False
                
                value = cmds.getAttr(attribute_name)
                
                if abs(value) > 0.01:
                    return True
    
    def _get_constraint_type(self, control):
        
        translate = True
        rotate = True
        
        #attributes = ['translate', 'rotate']
        axis = ['X','Y','Z']
        
        
        for a in axis:
            attribute_name = '%s.translate%s' % (control, a)
            
            if cmds.getAttr(attribute_name, l = True):
                translate = False
                break

        for a in axis:
            attribute_name = '%s.rotate%s' % (control, a)
            
            if cmds.getAttr(attribute_name, l = True):
                rotate = False
                break
            
        if translate and rotate:
            return 'parent'
         
        if translate:
            return 'point'
         
        if rotate:
            return 'orient'
    
    def _set_control_data_in_dict(self, control, attribute_data):
        
        data = self.eval_data(return_only=True)
        
        if data:
            data[control] = attribute_data
        
            self.set_data(data)
    
    
    def _set_control_data(self, control, data):
        
        for attribute in data:
            
            attribute_name = control + '.' + attribute
                        
            try:
                cmds.setAttr(attribute_name, data[attribute] )
            except:
                pass
          
        
    def _find_other_side(self, control, side):
        
        other_control = None
        
        if side == 'L':
            other_control = space.find_transform_right_side(control)
        
        if side == 'R':
            other_control = space.find_transform_left_side(control)
        
        return other_control
        
    def remove_data(self, control):
        
        data = self.get_data()
        
        if data:
            
            data = eval(data)
        

        if control in data:
            data.pop(control)
            
        self.set_data(data)
        
    def remove_pose_control_data(self):

        data = self.get_data()
        
        if data:
            data = eval(data)

        found_keys = []

        for key in data:
            if cmds.objExists('%s.POSE' % key):
                found_keys.append(key)
                
        for key in found_keys:
            data.pop(key)
            
        self.set_data(data)
                    
    def set_data(self, data= None):
        
        self.data.set_locked(False)
        
        if data == None:
            data = self._get_control_data()
        
        super(StoreControlData, self).set_data(data)   
        self.data.set_locked(True)
    
    def set_namesapce(self, namespace):
        self._namespace = namespace
    
    def set_control_data_attribute(self, control, data = None):

        if not data:
            data = self._get_single_control_data(control)
        
        if data:
            
            self._set_control_data_in_dict(control, data)
        if not data:
            util.warning('Error setting data for %s' % control )
        
    
        
    def set_controls(self, controls):
        
        self.controls = controls
    
    def set_side_replace(self, replace_string, pattern_string, position_string):
        #position can be 'start', 'end', 'first', or 'inside'
        
        self.side_replace = [replace_string, pattern_string, position_string]
        
        
        
    def eval_data(self, return_only = False):
        
        data = super(StoreControlData, self).eval_data()
        
        if return_only:
            return data
        
        if not data:
            return
        
        missing_controls = []
        
        for control in data:
            
            attribute_data = data[control]
            
            if self._namespace:
                
                base_control = core.get_basename(control, remove_namespace = True)
                
                namespace_name = self._namespace + ':' + base_control
                
                control = namespace_name
                
            
            
            if cmds.objExists('%s.POSE' % control):
                continue
            if not cmds.objExists(control):
                missing_controls.append(control)
       
            
            self._set_control_data(control, attribute_data)
        
        if missing_controls:
            util.warning('%s is trying to set values on the following controls which are absent from the scene.\n %s' % (self.node, missing_controls)) 
            
        return data
            
    def eval_mirror_data(self, side = 'L'):
          
        data_list = self.eval_data(return_only=True)
        
        for control in data_list:
            
            other_control = self._find_other_side(control, side)
            
            if not other_control or not cmds.objExists(other_control):
                continue
            
            if cmds.objExists('%s.ikFk' % control):

                value = cmds.getAttr('%s.ikFk' % control)
                other_value = cmds.getAttr('%s.ikFk' % other_control)
                cmds.setAttr('%s.ikFk' % control, other_value)
                cmds.setAttr('%s.ikFk' % other_control, value)
            
            if not self._has_transform_value(control):
                continue 
            
            temp_group = cmds.duplicate(control, n = 'temp_%s' % control, po = True)[0]
            attr.unlock_attributes(temp_group, only_keyable=True)
            
            space.MatchSpace(control, temp_group).translation_rotation()
            parent_group = cmds.group(em = True)
            cmds.parent(temp_group, parent_group)
            
            cmds.setAttr('%s.scaleX' % parent_group, -1)
            
            attr.zero_xform_channels(control)
            
            try:
                const1 = cmds.pointConstraint(temp_group, other_control)[0]
                cmds.delete(const1)
            except:
                pass
            
            try:
                const2 = cmds.orientConstraint(temp_group, other_control)[0]
                cmds.delete(const2)
            except:
                pass
            
            cmds.delete([temp_group, parent_group])
            
            
    def eval_multi_transform_data(self, data_list):
        
        controls = {}
        
        for data in data_list:
            
            last_temp_group = None
            
            for control in data:
                
                if cmds.objExists('%s.POSE' % control):
                    continue
                
                if not self._has_transform_value(control):
                    continue
                
                if not control in controls:
                    controls[control] = []

                temp_group = cmds.group(em = True, n = core.inc_name('temp_%s' % control))
                
                if not len(controls[control]):
                    space.MatchSpace(control, temp_group).translation_rotation()
                
                if len( controls[control] ):
                    last_temp_group = controls[control][-1]
                    
                    cmds.parent(temp_group, last_temp_group)
                
                    self._set_control_data(temp_group, data[control])
                                  
                controls[control].append(temp_group)
        
        for control in controls:
            
            
            constraint_type = self._get_constraint_type(control)
            
            if constraint_type == 'parent':
                cmds.delete( cmds.parentConstraint(controls[control][-1], control, mo = False) )
            if constraint_type == 'point':
                cmds.delete( cmds.pointConstraint(controls[control][-1], control, mo = False) )
            if constraint_type == 'orient':
                cmds.delete( cmds.orientConstraint(controls[control][-1], control, mo = False) )
                
            cmds.delete(controls[control][0])



class StretchyChain:
    """
    rigs
    """
    def __init__(self):
        self.side = 'C'
        self.inputs = []
        self.attribute_node = None
        self.distance_offset_attribute = None
        self.add_damp = False
        self.stretch_offsets = []
        self.distance_offset = None
        self.scale_axis = 'X'
        self.name = 'stretch'
        self.simple = False
        self.per_joint_stretch = True
        self.vector = False
        self.extra_joint = None
        self.damp_name = 'dampen'
        self.scale_offset = 1
        self.attribute_name = 'autoStretch'
        self._defulat_value = 0
        self._create_title = True
        self.stretch_condition = None
    
    def _get_joint_count(self):
        return len(self.joints)
    
    def _get_length(self):
        length = 0
        
        joint_count = self._get_joint_count()
        
        for inc in range(0, joint_count):
            if inc+1 == joint_count:
                break
            
            current_joint = self.joints[inc]
            next_joint = self.joints[inc+1]
            
            distance =  space.get_distance(current_joint, next_joint)
            
            length += distance
            
        return length
    
    def _build_stretch_locators(self):
        
        top_distance_locator = cmds.group(empty = True, n = core.inc_name('locator_topDistance_%s' % self.name))
        match = space.MatchSpace(self.joints[0], top_distance_locator)
        match.translation_rotation()
        
        btm_distance_locator = cmds.group(empty = True, n = core.inc_name('locator_btmDistance_%s' % self.name))
        match = space.MatchSpace(self.joints[-1], btm_distance_locator)
        match.translation_rotation()
        
        if not self.attribute_node:
            self.attribute_node = top_distance_locator
        
        return top_distance_locator, btm_distance_locator
    
    def _create_stretch_condition(self):
        
        total_length = self._get_length()
        
        condition = cmds.createNode("condition", n = core.inc_name("condition_%s" % self.name))
        cmds.setAttr("%s.operation" % condition, 2)
        cmds.setAttr("%s.firstTerm" % condition, total_length)
        cmds.setAttr("%s.colorIfTrueR" % condition, total_length)
        
        self.stretch_condition = condition
        
        return condition

    def _create_distance_offset(self, stretch_condition = None):
        
        multiply = attr.MultiplyDivideNode('offset_%s' % self.name)
        multiply.set_operation(2)
        multiply.set_input2(1,1,1)
        
        if stretch_condition:
            multiply.outputX_out('%s.secondTerm' % stretch_condition)
            multiply.outputX_out('%s.colorIfFalseR' % stretch_condition)
        
        return multiply.node

    def _create_stretch_distance(self, top_locator, btm_locator, distance_offset):
        
        distance_between = cmds.createNode('distanceBetween', 
                                           n = core.inc_name('distanceBetween_%s' % self.name) )
        
        if self.vector:
            cmds.connectAttr('%s.translate' % top_locator, '%s.point1' % distance_between)
            cmds.connectAttr('%s.translate' % btm_locator, '%s.point2' % distance_between)
        
        if not self.vector:
            cmds.connectAttr('%s.worldMatrix' % top_locator, 
                             '%s.inMatrix1' % distance_between)
            
            cmds.connectAttr('%s.worldMatrix' % btm_locator, 
                             '%s.inMatrix2' % distance_between)
        
        cmds.connectAttr('%s.distance' % distance_between, '%s.input1X' % distance_offset)
        
        return distance_between
        
        
    def _create_stretch_on_off(self, stretch_condition):
        
        blend = cmds.createNode('blendColors', n = core.inc_name('blendColors_%s' % self.name))
        cmds.setAttr('%s.color2R' % blend, self._get_length() )
        cmds.setAttr('%s.blender' % blend, 1)
        cmds.connectAttr('%s.outColorR' % stretch_condition, '%s.color1R' % blend)
        
        return blend

    def _create_divide_distance(self, stretch_condition = None, stretch_on_off = None):
        
        multiply = attr.MultiplyDivideNode('distance_%s' % self.name)
        
        multiply.set_operation(2)
        multiply.set_input2(self._get_length(),1,1)
        
        if stretch_condition:
            if stretch_on_off:
                multiply.input1X_in('%s.outputR' % stretch_on_off)
            if not stretch_on_off:
                multiply.input1X_in('%s.outColorR' % stretch_condition)
        if not stretch_condition:
            pass
        
        self.divide_distance = multiply.node
        
        return multiply.node

    def _create_offsets(self, divide_distance, distance_node):
        stretch_offsets = []
        
        plus_total_offset = cmds.createNode('plusMinusAverage', n = core.inc_name('plusMinusAverage_total_offset_%s' % self.name))
        self.plus_total_offset = plus_total_offset
        
        cmds.setAttr('%s.operation' % plus_total_offset, 3)
        
        for inc in range(0, self._get_joint_count()-1 ):
            
            var_name = 'offset%s' % (inc + 1)
            
            multiply = attr.connect_multiply('%s.outputX' % divide_distance, '%s.scale%s' % (self.joints[inc], self.scale_axis), 1)
            
            
            offset_variable = attr.MayaNumberVariable(var_name )
            offset_variable.set_variable_type(offset_variable.TYPE_DOUBLE)
            offset_variable.set_node(multiply)
            

                
                
            
            offset_variable.create()
            offset_variable.set_value(self.scale_offset)
            offset_variable.set_min_value(0.1)
            
            if self.scale_offset != 1:
                
                offset_multiply = cmds.createNode('multiplyDivide', n = 'multiplyDivide_scaleOffset')
                offset_variable.connect_out('%s.input1X' % offset_multiply)
                
                offset_value = 1.0/self.scale_offset
                
                cmds.setAttr('%s.input2X' % offset_multiply, offset_value)
                
                cmds.connectAttr('%s.outputX' % offset_multiply, '%s.input2X' % multiply)
                cmds.connectAttr('%s.outputX' % offset_multiply, '%s.input1D[%s]' % (plus_total_offset, inc+1))
                                

            if self.scale_offset == 1:
                offset_variable.connect_out('%s.input2X' % multiply)
                offset_variable.connect_out('%s.input1D[%s]' % (plus_total_offset, inc+1))
            
            stretch_offsets.append(multiply)
        
        multiply = cmds.createNode('multiplyDivide', n = core.inc_name('multiplyDivide_orig_distance_%s' % self.name))
        
        self.orig_distance = multiply
        
        length = self._get_length()
        cmds.setAttr('%s.input1X' % multiply, length)
        cmds.connectAttr('%s.output1D' % plus_total_offset, '%s.input2X' % multiply)
        
        self.stretch_offsets = stretch_offsets
        
        return stretch_offsets
        
    def _connect_scales(self):
        for inc in range(0,len(self.joints)-1):
            cmds.connectAttr('%s.output%s' % (self.divide_distance, self.scale_axis), '%s.scale%s' % (self.joints[inc], self.scale_axis))
        
    def _create_attributes(self, stretch_on_off):
        
        if self._create_title:
            attr.create_title(self.attribute_node,'STRETCH')
        
        stretch_on_off_var = attr.MayaNumberVariable(self.attribute_name)
        stretch_on_off_var.set_node(self.attribute_node)
        stretch_on_off_var.set_variable_type(stretch_on_off_var.TYPE_DOUBLE)
        stretch_on_off_var.set_min_value(0)
        stretch_on_off_var.set_max_value(1)
        stretch_on_off_var.set_value(self._defulat_value)
        stretch_on_off_var.create()
        
        stretch_on_off_var.connect_out('%s.blender' % stretch_on_off)
        
    def _create_offset_attributes(self, stretch_offsets):
        
        for inc in range(0, len(stretch_offsets)):
            
            stretch_offset = attr.MayaNumberVariable('stretch_%s' % (inc+1))
            stretch_offset.set_node(self.attribute_node)
            stretch_offset.set_variable_type(stretch_offset.TYPE_DOUBLE)
            if not self.per_joint_stretch:
                stretch_offset.set_keyable(False)
            
            stretch_offset.create()
            
            stretch_offset.set_value(self.scale_offset)
            stretch_offset.set_min_value(0.1)
            
            stretch_offset.connect_out('%s.offset%s' % (stretch_offsets[inc], inc+1) )
    
    def _create_other_distance_offset(self, distance_offset):
        
        multiply = attr.MultiplyDivideNode('distanceOffset_%s' % self.name)
        
        plug = '%s.input2X' % distance_offset
        
        input_to_plug = attr.get_attribute_input('%s.input2X' % distance_offset)
        
        multiply.input1X_in(input_to_plug)
        multiply.input2X_in(self.distance_offset_attribute)
        multiply.outputX_out(plug)
        
    def _create_damp(self, distance_offset, plugs):
        
        min_length = space.get_distance(self.joints[0], self.joints[-1])
        #max_length = self._get_length()
            
        damp = attr.MayaNumberVariable(self.damp_name)
        damp.set_node(self.attribute_node)
        damp.set_variable_type(damp.TYPE_DOUBLE)
        damp.set_min_value(0)
        damp.set_max_value(1)
        damp.create()
        
        remap = cmds.createNode( "remapValue" , n = "%s_remapValue_%s" % (self.damp_name, self.name) )
        cmds.setAttr("%s.value[2].value_Position" % remap, 0.4);
        cmds.setAttr("%s.value[2].value_FloatValue" % remap, 0.666);
        cmds.setAttr("%s.value[2].value_Interp" % remap, 3)
    
        cmds.setAttr("%s.value[3].value_Position" % remap, 0.7);
        cmds.setAttr("%s.value[3].value_FloatValue" % remap, 0.9166);
        cmds.setAttr("%s.value[3].value_Interp" % remap, 1)
    
        multi = cmds.createNode ( "multiplyDivide", n = "%s_offset_%s" % (self.damp_name, self.name))
        add_double = cmds.createNode( "addDoubleLinear", n = "%s_addDouble_%s" % (self.damp_name, self.name))

        damp.connect_out('%s.input2X' % multi)
        
        cmds.connectAttr('%s.outputX' % self.orig_distance, '%s.input1X' % multi)
        
        cmds.connectAttr("%s.outputX" % multi, "%s.input1" % add_double)
        
        cmds.connectAttr('%s.outputX' % self.orig_distance, '%s.input2' % add_double)
        
        cmds.connectAttr("%s.output" % add_double, "%s.inputMax" % remap)
    
        cmds.connectAttr('%s.outputX' % self.orig_distance, '%s.outputMax' % remap)
        
        cmds.setAttr("%s.inputMin" % remap, min_length)
        cmds.setAttr("%s.outputMin" % remap, min_length)
        
        cmds.connectAttr( "%s.outputX" % distance_offset, "%s.inputValue" % remap)
        
        for plug in plugs:
                cmds.connectAttr( "%s.outValue" % remap, plug)
        
    def _add_joint(self, joint):
        
        inc = len(self.stretch_offsets) + 1
        
        var_name = 'offset%s' % (inc)
            
        multiply = attr.connect_multiply('%s.outputX' % self.divide_distance, '%s.scale%s' % (joint, self.scale_axis), 1)
            
            
        offset_variable = attr.MayaNumberVariable(var_name )
        offset_variable.set_variable_type(offset_variable.TYPE_DOUBLE)
        offset_variable.set_node(multiply)
            
            
        offset_variable.create()
        offset_variable.set_value(1)
        offset_variable.set_min_value(0.1)
        offset_variable.connect_out('%s.input2X' % multiply)
        offset_variable.connect_out('%s.input1D[%s]' % (self.plus_total_offset, inc))
        
        
        stretch_offset = attr.MayaNumberVariable('stretch_%s' % (inc))
        stretch_offset.set_node(self.attribute_node)
        stretch_offset.set_variable_type(stretch_offset.TYPE_DOUBLE)
        
        if not self.per_joint_stretch:
            stretch_offset.set_keyable(False)
        
        stretch_offset.create()
        
        stretch_offset.set_value(1)
        stretch_offset.set_min_value(0.1)
        
        stretch_offset.connect_out('%s.offset%s' % (multiply, inc) )   
        
        child_joint = cmds.listRelatives(joint, type = 'joint')
        
        if child_joint:
            distance =  space.get_distance(joint, child_joint[0])
            
            length = cmds.getAttr('%s.input1X' % self.orig_distance)
            length+=distance
            
            cmds.setAttr('%s.input1X' % self.orig_distance, length)
    
        
    def set_joints(self, joints):
        self.joints = joints
        
    def set_node_for_attributes(self, node_name):
        self.attribute_node = node_name
    
    def set_scale_axis(self, axis_letter):
        self.scale_axis = axis_letter.capitalize()
    
    def set_distance_offset(self, attribute):
        self.distance_offset_attribute = attribute
    
    def set_vector_instead_of_matrix(self, bool_value):
        self.vector = bool_value
    
    def set_add_dampen(self, bool_value, damp_name = None):
        self.set_add_damp(bool_value, damp_name)
        
    def set_add_damp(self, bool_value, damp_name = None):
        self.add_damp = bool_value
        
        if damp_name:
            self.damp_name = damp_name
            
    def set_simple(self, bool_value):
        self.simple = bool_value
    
    def set_description(self, string_value):
        self.name = '%s_%s' % (self.name, string_value)
    
    def set_per_joint_stretch(self, bool_value):
        self.per_joint_stretch = bool_value
    
    def set_scale_attribute_offset(self, value):
        self.scale_offset = value
    
    def set_extra_joint(self, joint):
        self.extra_joint = joint
    
    def set_attribute_name(self, attribute_name):
        self.attribute_name = attribute_name
    
    def set_default_value(self, value):
        self._defulat_value = value
    
    def set_create_title(self, bool_value):
        self._create_title = bool_value
    
    def create(self):
        
        
        top_locator, btm_locator = self._build_stretch_locators()
        
        if self.simple:
            
            for joint in self.joints[:-1]:
                distance_offset = self._create_distance_offset()
                
                stretch_distance = self._create_stretch_distance(top_locator, 
                                              btm_locator, 
                                              distance_offset)
                                
                divide_distance = self._create_divide_distance()
                
                cmds.connectAttr('%s.outputX' % distance_offset, '%s.input1X' % divide_distance)
                
                cmds.connectAttr('%s.outputX' % divide_distance, '%s.scale%s' % (joint, self.scale_axis))
        
        if not self.simple:
        
            stretch_condition = self._create_stretch_condition()
            
            distance_offset = self._create_distance_offset( stretch_condition )
            
            stretch_distance = self._create_stretch_distance(top_locator, 
                                          btm_locator, 
                                          distance_offset)
            
            stretch_on_off = self._create_stretch_on_off( stretch_condition )
            
            divide_distance = self._create_divide_distance( stretch_condition, 
                                                            stretch_on_off )
            
            stretch_offsets = self._create_offsets( divide_distance, stretch_distance)
            
            if self.attribute_node:
                self._create_attributes(stretch_on_off)
                self._create_offset_attributes(stretch_offsets)
                
                if self.extra_joint:
                    self._add_joint(self.extra_joint)
                
                if self.add_damp:
                    self._create_damp(distance_offset, ['%s.firstTerm' % stretch_condition,
                                                           '%s.colorIfTrueR' % stretch_condition,
                                                           '%s.color2R' % stretch_on_off,
                                                           '%s.input2X' % divide_distance])
                
            if self.distance_offset_attribute:
                self._create_other_distance_offset(distance_offset)
                
        
                
        return top_locator, btm_locator


class StretchyElbowLock(object):

    def __init__(self, three_joints, three_controls):
        """
        Create an elbow lock stretchy on the three joints
        
        Args:
            three_joints (list): For example the arm, elbow and wrist joint.  Can be any 3 joints though
            three_controls (list): For example the top arm control, the pole vector control and the btm control.  Controls should transforms that correspond to an ik setup.
        """
        self.joints = three_joints
        self.controls = three_controls
        self.axis_letter = 'X'
    
        self.attribute_control = three_controls[-1]
        self.lock_attribute_control = three_controls[1]
        
        self.description = 'rig'
        
        self._use_translate = False
        self._value = 0
        
        self._distance_full = None
        
        self._top_aim_transform = None
        
        self.soft_locator = None
        self._do_create_soft_ik = False
    
    def _build_locs(self):
        self.top_loc = cmds.spaceLocator(n = 'distanceLocator_top_%s' % self.description)[0]
        self.btm_loc = cmds.spaceLocator(n = 'distanceLocator_btm_%s' % self.description)[0]
        
        cmds.parent(self.top_loc, self.controls[0])
        attr.zero_xform_channels(self.top_loc)
        
        cmds.parent(self.btm_loc, self.controls[-1])
        attr.zero_xform_channels(self.btm_loc)
        
        cmds.hide(self.top_loc, self.btm_loc)
        
        self.stretch_locators = [self.top_loc, self.btm_loc]
    
    def _duplicate_joints(self):
        
        dup_hier = space.DuplicateHierarchy(self.joints[0])
        dup_hier.only_these(self.joints)
        duplicates = dup_hier.create()
        
        found = []
        
        for dup, orig in zip(duplicates, self.joints):
            new = cmds.rename(dup, 'default_%s' % orig)
            found.append(new)
            
        cmds.hide(found[0])
            
        self.dup_joints = found
    
    def _create_distance(self, transform1, transform2):
        
        distance_node = cmds.createNode('distanceBetween')
        
        cmds.connectAttr('%s.worldMatrix' % transform1, '%s.inMatrix1' % distance_node)
        cmds.connectAttr('%s.worldMatrix' % transform2, '%s.inMatrix2' % distance_node)
        
        return distance_node       
        
    def _connect_double_linear(self, attribute1, attribute2, input_attribute = None):
        
        add_double_linear = cmds.createNode('addDoubleLinear')
        
        cmds.connectAttr(attribute1, '%s.input1' % add_double_linear)
        cmds.connectAttr(attribute2, '%s.input2' % add_double_linear)
        
        if input_attribute:
            cmds.connectAttr('%s.output' % add_double_linear, input_attribute)
        
        return add_double_linear
    
    
    
    def _multiply_divide(self, attribute1, attribute2, input_attribute = None):
        
        mult = cmds.createNode('multiplyDivide')
        
        cmds.connectAttr(attribute1, '%s.input1X' % mult)
        cmds.connectAttr(attribute2, '%s.input2X' % mult)
        
        if input_attribute:
            cmds.connectAttr('%s.outputX' % mult, input_attribute)
    
        return mult
    
    def _condition(self, color_if_true_attribute, first_term_attribute, second_term_attribute):
        
        condition = cmds.createNode('condition')
        
        cmds.connectAttr(color_if_true_attribute, '%s.colorIfTrueR' % condition)
        cmds.connectAttr(first_term_attribute, '%s.firstTerm' % condition)
        cmds.connectAttr(second_term_attribute, '%s.secondTerm' % condition)
        
        return condition
    
    def _blendTwoAttr(self, attribute1, attribute2, input_attribute = None):
        
        blend_two = cmds.createNode('blendTwoAttr')
        
        cmds.connectAttr(attribute1, '%s.input[0]' % blend_two)
        cmds.connectAttr(attribute2, '%s.input[1]' % blend_two)
        
        if input_attribute:
            cmds.connectAttr('%s.output' % blend_two, input_attribute)
        
        return blend_two
    
    def _add_attribute(self, node, attribute_name, default = 0):
        attr.create_title(node, 'STRETCH')
        cmds.addAttr(node, ln = attribute_name, k = True, dv = default)
        
    def _rename(self, old_name, new_name):
        
        return cmds.rename(old_name, core.inc_name('%s_%s_%s' % (cmds.nodeType(old_name), new_name, self.description)))
        
    def set_stretch_axis(self, axis_letter):
        
        self.axis_letter = axis_letter.upper()
    
    def set_lock_attribute_control(self, name_of_a_control):
        
        self.lock_attribute_control = name_of_a_control
        
    def set_attribute_control(self, name_of_a_control):
        self.attribute_control = name_of_a_control
        
    def set_description(self, description):
        self.description = description
        
    def set_use_translate_for_stretch(self, bool_value):
        self._use_translate = bool_value
        
    def set_use_this_overall_distance_node(self, distance_node):
        self._distance_full = distance_node
        
    def set_default_value(self, value):
        self._value = value
        
    def set_top_aim_transform(self, transform):
        self._top_aim_transform = transform
    
    def set_parent(self, transform):
        self._parent = transform
    
    def set_create_soft_ik(self, bool_value):
        
        self._do_create_soft_ik = bool_value
        
    def create(self):
        
        self._build_locs()
        
        attribute_control = self.attribute_control
        lock_control = self.lock_attribute_control
        
        if not attribute_control:
            attribute_control = self.controls[-1]
        
        self._add_attribute(lock_control, 'lock')
        cmds.addAttr('%s.lock' % lock_control, e=True, minValue = 0, maxValue = 1, hasMinValue = True, hasMaxValue = True)
        self._add_attribute(attribute_control, 'stretch', self._value)
        cmds.addAttr('%s.stretch' % attribute_control, e=True, minValue = 0, maxValue = 1, hasMinValue = True, hasMaxValue = True)
        self._add_attribute(attribute_control, 'nudge')
        
        # joint distance
        self._duplicate_joints()
        
        distance1 = self._create_distance(self.dup_joints[0], self.dup_joints[1])
        distance2 = self._create_distance(self.dup_joints[1], self.dup_joints[2])
        
        default_distance_double_linear = self._connect_double_linear('%s.distance' % distance1, '%s.distance' % distance2)
        
        distance1 = self._rename(distance1, 'defaultTop')
        distance2 = self._rename(distance2, 'defaultBtm')
        
        
        # control distance
        if not self._distance_full:
            distance_full = self._create_distance(self.top_loc, self.btm_loc)
        else:
            distance_full = self._distance_full
            
        distance_top = self._create_distance(self.controls[0], self.controls[1])
        distance_btm = self._create_distance(self.controls[1], self.controls[-1])
        
        distance_full = self._rename(distance_full, 'full')
        distance_top = self._rename(distance_top, 'top')
        distance_btm = self._rename(distance_btm, 'btm')        
        
        mult = self._multiply_divide('%s.distance' %  distance_full, '%s.output' % default_distance_double_linear)
        cmds.setAttr('%s.operation' % mult, 2)
        
        mult = self._rename(mult, 'stretch')
        
        condition = self._condition('%s.outputX' % mult, '%s.distance' % distance_full, '%s.output' % default_distance_double_linear)
        cmds.setAttr('%s.operation' % condition, 2)
        
        condition = self._rename(condition, 'stretch')
        
        blend_two_stretch = cmds.createNode('blendTwoAttr')
        
        blend_two_stretch = self._rename(blend_two_stretch, 'stretch')
        
        cmds.setAttr('%s.input[0]' % blend_two_stretch, 1)
        cmds.connectAttr('%s.outColorR' % condition, '%s.input[1]' % blend_two_stretch)
        cmds.connectAttr('%s.stretch' % attribute_control, '%s.attributesBlender' % blend_two_stretch)
        
        nudge_offset = cmds.createNode('multDoubleLinear')
        nudge_offset = self._rename(nudge_offset, 'nudgeOffset')
        
        cmds.connectAttr('%s.nudge' % attribute_control, '%s.input1' % nudge_offset)
        cmds.setAttr('%s.input2' % nudge_offset, 0.001)
        
        nudge_double_linear = self._connect_double_linear('%s.output' % blend_two_stretch, '%s.output' % nudge_offset)
        nudge_double_linear = self._rename(nudge_double_linear, 'nudge')
        
        mult_lock = self._multiply_divide('%s.distance' % distance_top, '%s.distance' % distance1)
        mult_lock = self._rename(mult_lock, 'lock')
        cmds.setAttr('%s.operation' % mult_lock, 2)
        
        cmds.connectAttr('%s.distance' % distance_btm, '%s.input1Y' % mult_lock)
        cmds.connectAttr('%s.distance' % distance2, '%s.input2Y' % mult_lock)
        
        top_lock_blend = self._blendTwoAttr('%s.output' % nudge_double_linear,
                                            '%s.outputX' % mult_lock)
        top_lock_blend = self._rename(top_lock_blend, 'lockTop')
        
        cmds.connectAttr('%s.lock' % lock_control, '%s.attributesBlender' % top_lock_blend)
        
        btm_lock_blend = self._blendTwoAttr('%s.output' % nudge_double_linear,
                                            '%s.outputY' % mult_lock)
        btm_lock_blend = self._rename(btm_lock_blend, 'lockBtm')
 
        cmds.connectAttr('%s.lock' % lock_control, '%s.attributesBlender' % btm_lock_blend)
 
        top_mult = cmds.createNode('multDoubleLinear')
        top_mult = self._rename(top_mult, 'top')
        cmds.connectAttr('%s.output' % top_lock_blend, '%s.input2' % top_mult)
        
        if self._use_translate:
            cmds.setAttr('%s.input1' % top_mult, cmds.getAttr('%s.translate%s' % (self.joints[1], self.axis_letter)))
            cmds.connectAttr('%s.output' % top_mult, '%s.translate%s' % (self.joints[1], self.axis_letter))
        else:
            cmds.setAttr('%s.input1' % top_mult, 1)
            cmds.connectAttr('%s.output' % top_mult, '%s.scale%s' % (self.joints[0], self.axis_letter))
        
        btm_mult = cmds.createNode('multDoubleLinear')
        btm_mult = self._rename(btm_mult, 'btm')
        cmds.connectAttr('%s.output' % btm_lock_blend, '%s.input2' % btm_mult)
        
        if self._use_translate:
            cmds.setAttr('%s.input1' % btm_mult, cmds.getAttr('%s.translate%s' % (self.joints[2], self.axis_letter)))
            cmds.connectAttr('%s.output' % btm_mult, '%s.translate%s' % (self.joints[2], self.axis_letter))
        else:    
            cmds.setAttr('%s.input1' % btm_mult, 1)
            cmds.connectAttr('%s.output' % btm_mult, '%s.scale%s' % (self.joints[1], self.axis_letter))
        
        if self._do_create_soft_ik:
            soft = SoftIk(self.joints)
            soft.set_attribute_control(self.attribute_control)
            soft.set_control_distance_attribute('%s.distance' % distance_full)
            soft.set_default_distance_attribute('%s.output' % default_distance_double_linear)
            soft.set_description(self.description)
            soft.set_top_aim_transform(self._top_aim_transform)
            soft.set_btm_control(self.controls[-1])
            soft.set_ik_locator_parent(self._parent)
            soft_loc = soft.create()
            
            self.soft_locator = soft_loc
            

class SoftIk(object):
    
    def __init__(self, joints):
        
        self._joints = joints
        self._attribute_control = None
        self._control_distance_attribute = None
        self._top_aim_transform = None
        self._btm_control = None
        self._attribute_name = 'softBuffer'
        self._nice_attribute_name = 'soft'
    
    def _rename(self, old_name, new_name):
        
        return cmds.rename(old_name, core.inc_name('%s_%s_%s' % (cmds.nodeType(old_name), new_name, self.description)))
    
    def _build_soft_graph(self):
        
        
        
        chain_distance = space.get_chain_length(self._joints)
        #control_distance = space.get_distance(self._joints[0], self._joints[-1])
        
        subtract_soft = cmds.createNode('plusMinusAverage')
        subtract_soft = self._rename(subtract_soft, 'subtractSoft')
        
        self._create_attributes(subtract_soft)
        soft_attr = subtract_soft + '.' + self._attribute_name
        
        cmds.setAttr('%s.operation' % subtract_soft, 2)
        if not self._default_distance_attribute:
            cmds.setAttr('%s.input1D[0]' % subtract_soft, chain_distance)
        else:
            cmds.connectAttr(self._default_distance_attribute, '%s.input1D[0]' % subtract_soft)
        cmds.connectAttr(soft_attr, '%s.input1D[1]' % subtract_soft)
        
        subtract_soft_total = cmds.createNode('plusMinusAverage')
        subtract_soft_total = self._rename(subtract_soft_total, 'subtractSoftTotal')
        cmds.setAttr('%s.operation' % subtract_soft_total, 2)
        
        cmds.connectAttr(self._control_distance_attribute, '%s.input1D[0]' % subtract_soft_total)
        cmds.connectAttr('%s.output1D' % subtract_soft, '%s.input1D[1]' % subtract_soft_total)
        
        divide_soft = cmds.createNode('multiplyDivide')
        divide_soft = self._rename(divide_soft, 'divideSoft')
        
        cmds.setAttr('%s.operation' % divide_soft, 2)
        cmds.connectAttr('%s.output1D' % subtract_soft_total, '%s.input1X' % divide_soft)
        cmds.connectAttr(soft_attr, '%s.input2X' % divide_soft)
        
        negate = cmds.createNode('multiplyDivide')
        negate = self._rename(negate, 'negateSoft')
        
        cmds.setAttr('%s.input1X' % negate, -1)
        cmds.connectAttr('%s.outputX' % divide_soft, '%s.input2X' % negate)
        
        power_soft = cmds.createNode('multiplyDivide')
        power_soft = self._rename(power_soft, 'powerSoft')
        
        exp_value = math.exp(1)
        
        cmds.setAttr('%s.operation' % power_soft, 3)
        cmds.setAttr('%s.input1X' % power_soft, exp_value)
        cmds.connectAttr('%s.outputX' % negate, '%s.input2X' % power_soft)
        
        power_mult_soft = cmds.createNode('multiplyDivide')
        power_mult_soft = self._rename(power_mult_soft, 'powerMultSoft')
        
        cmds.connectAttr(soft_attr, '%s.input1X' % power_mult_soft)
        cmds.connectAttr('%s.outputX' % power_soft, '%s.input2X' % power_mult_soft)
        
        subtract_end_soft = cmds.createNode('plusMinusAverage')
        subtract_end_soft = self._rename(subtract_end_soft, 'subtractEndSoft')
        
        cmds.setAttr('%s.operation' % subtract_end_soft, 2)
        if not self._default_distance_attribute:
            cmds.setAttr('%s.input1D[0]' % subtract_end_soft, chain_distance)
        else:
            cmds.connectAttr(self._default_distance_attribute, '%s.input1D[0]' % subtract_end_soft)
        cmds.connectAttr('%s.outputX' % power_mult_soft, '%s.input1D[1]' % subtract_end_soft)
        
        inside_condition = cmds.createNode('condition')
        inside_condition = self._rename(inside_condition, 'insideSoft')
        
        cmds.connectAttr(self._control_distance_attribute, '%s.firstTerm' % inside_condition)
        cmds.connectAttr('%s.output1D' % subtract_soft, '%s.secondTerm' % inside_condition)
        cmds.setAttr('%s.operation' % inside_condition, 2)
        cmds.connectAttr('%s.output1D' % subtract_end_soft, '%s.colorIfTrueR' % inside_condition)
        cmds.connectAttr(self._control_distance_attribute, '%s.colorIfFalseR' % inside_condition)
        
        #need to connect into locator now
        
        locator = cmds.spaceLocator(n='locator_%s' % self.description)[0]
        
        space.MatchSpace(self._joints[-1], locator).translation_rotation()
        
        #cmds.parent(locator, self._joints[0])
        
        if self._ik_locator_parent:
            cmds.parent(locator, self._ik_locator_parent)
        
        if self._top_aim_transform:
            #cmds.parent(locator, self._top_aim_transform)
            follow = space.create_follow_group(self._top_aim_transform, locator)
            attr.zero_xform_channels(locator)
            cmds.setAttr('%s.inheritsTransform' % follow, 0)
            
            #cmds.makeIdentity(locator, t = True, r = True, apply = True)
        
        cmds.connectAttr('%s.outColorR' % inside_condition, '%s.translateX' % locator)
        
        if self._btm_control:    
            group = cmds.group(em = True, n = 'softOnOff_%s' % self.description)
            constraint = cmds.pointConstraint([locator, self._btm_control], group)[0]
            constraint_edit = space.ConstraintEditor()
            
            constraint_edit.create_switch(self._attribute_control, 'stretch', constraint)
            locator = group
        
        return locator
        
    def _create_attributes(self, soft_buffer_node):
        
        attribute = self._add_attribute(soft_buffer_node, self._attribute_name)
        nice_attribute = self._add_attribute(self._attribute_control, self._nice_attribute_name, 0)
        anim.quick_driven_key(nice_attribute, attribute, [0,1], [0.001, 1], infinite = True)
        
        cmds.setAttr(attribute, k = False)
        cmds.addAttr(nice_attribute, e=True, minValue = 0, maxValue = 2, hasMinValue = True, hasMaxValue = True)
        
    def _add_attribute(self, node, attribute_name, default = 0):
        #attr.create_title(node, 'SOFT')
        cmds.addAttr(node, ln = attribute_name, k = True, dv = default)
        
        return '%s.%s' % (node, attribute_name)
        
            
    def set_attribute_control(self, control_name, attribute_name = None):
        self._attribute_control = control_name
        if attribute_name:
            self._nice_attribute_name = attribute_name  
        
    def set_control_distance_attribute(self, control_distance_attribute):
        self._control_distance_attribute = control_distance_attribute
    
    def set_default_distance_attribute(self, default_distance_attribute):
        self._default_distance_attribute = default_distance_attribute
    
    def set_top_aim_transform(self, transform):
        self._top_aim_transform = transform
    
    def set_ik_locator_parent(self, transform):
        self._ik_locator_parent = transform
    
    def set_btm_control(self, control_name):
        self._btm_control = control_name
    
    def set_description(self, description):
        self.description = description
    
    def create(self):
        
        locator = self._build_soft_graph()
        
        return locator

class RiggedLine(object):
    """
    rigs
    """
    def __init__(self, top_transform, btm_transform, name):
        self.name = name
        self.top = top_transform
        self.btm = btm_transform
        self.local = False
        self.extra_joint = None
    
    def _build_top_group(self):
        
        self.top_group = cmds.group(em = True, n = 'guideLineGroup_%s' % self.name)
        cmds.setAttr('%s.inheritsTransform' % self.top_group, 0)
    
    def _create_curve(self):
        self.curve = cmds.curve(d = 1, p = [(0, 0, 0),(0,0,0)], k = [0, 1], n = core.inc_name('guideLine_%s' % self.name))
        cmds.delete(self.curve, ch = True)
        
        
        shapes = core.get_shapes(self.curve)
        new_name = cmds.rename(shapes[0], '%sShape' % self.curve)
        
        cmds.setAttr('%s.template' % self.curve, 1)
        
        cmds.parent(self.curve, self.top_group)
    
    def _create_cluster(self, curve, cv):
        cluster, transform = cmds.cluster('%s.cv[%s]' % (self.curve,cv))
        transform = cmds.rename(transform, core.inc_name('guideLine_cluster_%s' % self.name))
        cluster = cmds.rename('%sCluster' % transform, core.inc_name('cluster_guideline_%s' % self.name) )
        cmds.hide(transform)

        cmds.parent(transform, self.top_group)
        
        return [cluster, transform]
        
    def _match_clusters(self):
        
        match = space.MatchSpace(self.top, self.cluster1[1])
        match.translation_to_rotate_pivot()
        
        match = space.MatchSpace(self.btm, self.cluster2[1])
        match.translation_to_rotate_pivot()
    
    def _create_clusters(self):
        self.cluster1 = self._create_cluster(self.curve, 0)
        self.cluster2 = self._create_cluster(self.curve, 1)
    
    def _constrain_clusters(self):
        
        if self.local:
            #CBB
            offset1 = cmds.group(em = True, n = 'xform_%s' % self.cluster1[1])
            offset2 = cmds.group(em = True, n = 'xform_%s' % self.cluster2[1])
            
            cmds.parent(offset1, offset2, self.top_group)

            cmds.parent(self.cluster1[1], offset1)
            cmds.parent(self.cluster2[1], offset2)
            
            match = space.MatchSpace(self.top, offset1)
            match.translation()
            
            match = space.MatchSpace(self.btm, offset2)
            match.translation()
            
            space.constrain_local(self.top, offset1)
            space.constrain_local(self.btm, offset2)
            
        if not self.local:
            cmds.pointConstraint(self.top, self.cluster1[1])
            cmds.pointConstraint(self.btm, self.cluster2[1])
    

    def set_local(self, bool_value):
        self.local = bool_value
    

    
    def create(self):
        
        self._build_top_group()
        
        self._create_curve()
        self._create_clusters()
        self._match_clusters()
        self._constrain_clusters()
        
        return self.top_group

class RigSwitch(object):
    """
    Create a switch between different rigs on a buffer joint.
    
    Args:
        switch_joint (str): The name of a buffer joint with switch attribute.
    """
    def __init__(self, switch_joint):
        
        self.switch_joint = switch_joint
        
        if not cmds.objExists('%s.switch' % switch_joint):
            util.warning('%s is most likely not a buffer joint with switch attribute.' % switch_joint)

        self.groups = {}
        
        weight_count = self.get_weight_count()
        
        if not weight_count:
            util.warning('%s has no weights.' % weight_count)
        
        for inc in range(0, weight_count):
            self.groups[inc] = None
        
        self.control_name = None
        self.attribute_name = 'switch'

    def get_weight_count(self):
        
        edit_constraint = space.ConstraintEditor()
        constraint = edit_constraint.get_constraint(self.switch_joint, 'parentConstraint')
        
        if constraint:
            weight_count = edit_constraint.get_weight_count(constraint)
        else:
            switch_nodes = space.SpaceSwitch().get_space_switches(self.switch_joint)
            
            if switch_nodes:
                sources = space.SpaceSwitch().get_source(switch_nodes[0])
                
                weight_count = len(sources)
        
        return weight_count

    def add_groups_to_index(self, index, groups):
        """
        A switch joint is meant to switch visibility between rigs.
        By adding groups you define what their visibility is when the switch attribute changes.
        An index of 0 means the groups will be visibile when the switch is at 0, but invisible when the switch is at 1.
        
        Args:
            index (int): The index on the switch. Needs to be an integer value even though switch is a float.
            groups (list): The list of groups that should be have visibility attached to the index.
        """
        
        groups = util.convert_to_sequence(groups)
        
        if not self.switch_joint or not cmds.objExists(self.switch_joint):
            util.warning('Switch joint %s does not exist' % self.switch_joint)
            return
        
        weight_count = self.get_weight_count()
        
        if weight_count < ( index + 1 ):
            util.warning('Adding groups to index %s is undefined. %s.witch does not have that many inputs.' % (index, self.switch_joint))
        
        self.groups[index] = groups
        
    def set_attribute_control(self, transform):
        """
        Set where the switch attribute should live.
        
        Args:
            transform (str): The name of a transform
        """
        
        self.control_name = transform
        
    def set_attribute_name(self, attribute_name):
        """
        Set the name of the switch attribute on the attribute_control.
        
        Args:
            attribute_name (str): The name for the attribute.
        """
        
        self.attribute_name = attribute_name
        
    def create(self):
        
        if self.control_name and cmds.objExists(self.control_name):
            
            weight_count = self.get_weight_count()
            
            
            var = attr.MayaNumberVariable(self.attribute_name)
               
            var.set_min_value(0)
            
            max_value = weight_count -1
            var_max_value = var.get_max_value()
            
            if var_max_value != None:
                if max_value < var_max_value:
                    max_value = var_max_value
            
            var.set_max_value( max_value ) 
            var.set_keyable(True) 
            var.create(self.control_name)    
            
            attribute_name = var.get_name()
            cmds.connectAttr(attribute_name, '%s.switch' % self.switch_joint) 
        
        if not self.control_name or not cmds.objExists(self.control_name):
            attribute_name = '%s.switch' % self.switch_joint
        
        for key in self.groups.keys():
            
            groups = self.groups[key]
            
            if not groups:
                continue
            
            for group in groups:
                attr.connect_equal_condition(attribute_name, '%s.visibility' % group, key) 
        
class MirrorControlKeyframes():
    def __init__(self, node):
        self.node = node
        
    def _get_output_keyframes(self):
        
        found = anim.get_output_keyframes(self.node)
                
        return found
         
    def _map_connections(self, connections):
        new_connections = []
        
        if not connections:
            return new_connections
        
        for connection in connections:
            node, attribute = connection.split('.')
            
            new_node = node
            
            new_node = space.find_transform_left_side(node, check_if_exists = True)
            if not new_node:
                new_node = space.find_transform_right_side(node, check_if_exists = True)   
               
            new_connections.append('%s.%s' % (new_node, attribute))
                
        return new_connections

                
    def mirror_outputs(self, fix_translates = False):
        
        found_keyframes = self._get_output_keyframes()
        
        for keyframe in found_keyframes:
            
            util.show('Working to mirror keyframe: %s' % keyframe)
            
            cmds.dgeval(keyframe)
            new_keyframe = cmds.duplicate(keyframe)[0]
            
            connections = attr.Connections(keyframe)
            outputs = connections.get_outputs()
            inputs = connections.get_inputs()
            
            mapped_output = self._map_connections(outputs)
            mapped_input = self._map_connections(inputs)
            
            if not mapped_output:
                cmds.delete(new_keyframe)
                util.warning('Keyframe %s has no outputs to mirror. Skipping' % keyframe)
                continue
            
            for inc in range(0, len(mapped_output), 2):
                
                output = mapped_output[inc]
                split_output = output.split('.')
                new_output = '%s.%s' % (new_keyframe, split_output[1])

                do_fix_translates = False

                if mapped_output[inc+1].find('.translate') > -1 and fix_translates:
                    do_fix_translates = True
                
                no_output = True
                
                if cmds.objExists(mapped_output[inc+1]) and not attr.get_inputs(mapped_output[inc+1]):
                    
                    if not do_fix_translates:
                        try:
                            cmds.connectAttr(new_output, mapped_output[inc+1], f = True)
                        except:
                            util.warning('Could not connect %s into %s' % (new_output, mapped_output[inc+1]))
                    if do_fix_translates:
                        
                        attr.connect_multiply(new_output, mapped_output[inc+1], -1)
                    
                    no_output = False
            
                if attr.get_inputs(mapped_output[inc+1]):
                    util.warning('Could not output mirrored keyframe into %s. An input already exists for that attribute.' % mapped_output[inc+1] )
            
            if no_output:
                cmds.delete(new_keyframe)
                continue
            
            for inc in range(0, len(mapped_input), 2):
                
                input_connection = mapped_input[inc+1]
                split_input = input_connection.split('.')
                new_input = '%s.%s' % (new_keyframe, split_input[1])
                
                cmds.connectAttr(mapped_input[inc], new_input, f = True)

class TwistRibbon(object):
    
    def __init__(self, joint, end_transform = None):
        """
        Takes a joint.  
        If no end_transform given, the code will take the first child of the joint as the end of the ribbon.
        """
        self.joints = []
        self.rivets = []
        self.control_xforms = []
        self.rivet_gr = None
        self.surface = None
        self.top_locator = None
        self.btm_locator = None
        self.joint_count = 5
        self.group = None
        self._joint = joint
        self._end_transform = end_transform
        self._description = 'section'
        self._offset_axis = 'Y'
        self._attach_directly = False
        self._top_parent = None
        self._btm_parent = None
        self._top_constraint = None
        self._top_constraint_type = None
        self._btm_constraint = None
        self._btm_constraint_type = None
        self._btm_twist_fix = False
        self._top_twist_fix = False
        self._dual_quat = False
        self._ribbon_offset = 1
        self._rounded = False
        
    def _create_top_twister_joint(self):
        
        joint1, joint2, ik = space.create_pole_chain(self.top_locator, self.btm_locator, 'twist_topFix_%s' % self._description, space.IkHandle.solver_rp)
        cmds.hide(joint1, joint2)
        
        self.top_ik = ik
        
        xform = space.create_xform_group(joint1)
        cmds.parent( xform, self.top_locator)
        cmds.parent(self.top_joint, joint1)    
        
        cmds.parent( ik, self.btm_locator)
        cmds.hide(joint1, ik)


    def _create_btm_twister_joint(self):
        joint1, joint2, ik = space.create_pole_chain(self.btm_locator, self.top_locator, 'twist_btmFix_%s' % self._description, space.IkHandle.solver_rp)
        cmds.hide(joint1, joint2)
        
        self.btm_ik = ik
        
        xform = space.create_xform_group(joint1)
        cmds.parent( xform, self.btm_locator)
        cmds.parent(self.btm_joint, joint1)    
        
        cmds.parent( ik, self.top_locator)
        
        cmds.hide(joint1, ik)
     
    def set_description(self, description):
        self._description = description
        
    def set_joint_count(self, int_value):
        self.joint_count = int_value 
        
    def set_joints(self, joint_list):
        self.joints = joint_list
        
    def set_ribbon_offset_axis(self, axis_letter):
        self._offset_axis = axis_letter
        
    def set_attach_directly(self, bool_value):
        self._attach_directly = bool_value
        
    def set_top_parent(self, transform):
        self._top_parent = transform
        
    def set_btm_parent(self, transform):
        self._btm_parent = transform
        
    def set_top_constraint(self, transform, constraint_type = 'parentConstraint'):
        self._top_constraint = transform
        self._top_constraint_type = constraint_type
    
    def set_btm_constraint(self, transform, constraint_type = 'parentConstraint'):
        self._btm_constraint = transform
        self._btm_constraint_type = constraint_type
        
    def set_top_twist_fix(self, bool_value):
        self._top_twist_fix = bool_value
        
    def set_btm_twist_fix(self, bool_value):
        self._btm_twist_fix = bool_value
    
    def set_dual_quaternion(self, bool_value, turn_twist_fix_on = True):
        self._dual_quat = bool_value
        if turn_twist_fix_on:
            self._top_twist_fix = True
            self._btm_twist_fix = True

    def set_ribbon_offset(self, value):
        self._ribbon_offset = value
        
    def set_rounded(self, bool_value):
        self._rounded = bool_value

    def create(self):
        
        top_loc = cmds.spaceLocator(n = core.inc_name('locator_twistRibbonTop_%s' % self._description))[0]
        btm_loc = cmds.spaceLocator(n = core.inc_name('locator_twistRibbonBtm_%s' % self._description))[0]
        
        if not self._end_transform:
            children = cmds.listRelatives(self._joint, type = 'joint')
            if not children:
                util.warning('No child found for %s. Could not create strip' % self._joint)
                return
            temp_group = children[0]
        if self._end_transform:
            temp_group = self._end_transform
        ribbon_gr = cmds.group(em = True, n = core.inc_name('twistRibbon_%s' % self._description))
        self.group = ribbon_gr
        
        spans = -1
        if self._rounded:
            spans = 1
        
        self.surface = geo.transforms_to_nurb_surface([self._joint, temp_group], description = self._description, spans = spans,offset_axis=self._offset_axis, offset_amount = self._ribbon_offset)
        if self._dual_quat:
            cmds.rebuildSurface(self.surface, ch = False,
                                            rpo = 1,
                                            rt = 0,
                                            end = 1,
                                            kr = 0,
                                            kcp = 0,
                                            kc = 0,
                                            su = 1,
                                            du = 1,
                                            sv = 2,
                                            dv = 3,
                                            tol = 0.01,
                                            fr = 0,
                                            dir = 2 )
            
        
        cmds.parent(self.surface, ribbon_gr)
        if not self.joints:
            self.joints = geo.nurb_surface_v_to_transforms(self.surface, self._description, count=self.joint_count)
            cmds.parent(self.joints, ribbon_gr)
        
        max_u = cmds.getAttr('%s.minMaxRangeU' % self.surface)[0][1]
        u_value = max_u/2.0
        curve, curve_node = cmds.duplicateCurve(self.surface + '.u[' + str(u_value) + ']', ch = True, rn = 0, local = 0, r = True, n = core.inc_name('liveCurve_%s' % self._description))
        curve_node = cmds.rename(curve_node, core.inc_name('curveFromSurface_%s' % self._description))
        self.surface_stretch_curve = curve
        self.surface_stretch_curve_node = curve_node
        cmds.parent(curve, ribbon_gr)
        
        rivet_gr = cmds.group(em = True, n = core.inc_name('twistRibbon_rivets_%s' % self._description))
        self.rivet_gr = rivet_gr
        cmds.parent(rivet_gr, ribbon_gr)
        
        self.control_xforms = []
        
        for joint in self.joints:
            
            cmds.delete( cmds.orientConstraint(self._joint, joint)) 
            cmds.makeIdentity(joint, apply = True, r = True)
            
            
            rivet = geo.attach_to_surface(joint, self.surface, constrain=self._attach_directly)
            
            rel = cmds.listRelatives(rivet, type = 'transform')
            
            if rel:
                self.control_xforms.append(rel[1])
            
            shapes = core.get_shapes(rivet)
            cmds.hide(shapes)
            cmds.parent(rivet, rivet_gr)
            
            self.rivets.append(rivet)
        
        
        skin_surface = deform.SkinJointSurface(self.surface, self._description)
        if self._rounded:
            skin_surface.set_join_ends(True)
        skin_surface.set_joint_u(True)
        skin_surface.create()
        
        joints = skin_surface.get_joint_list()
        
        if self._dual_quat:
            cmds.delete(joints[1:-1])
            joints = [joints[0], joints[-1]]
        if not self._dual_quat:
            cmds.setAttr('%s.skinningMethod' % skin_surface.skin_cluster, 0)
            
        self.top_joint = joints[0]
        self.btm_joint = joints[1]
        
        space.MatchSpace(joints[0], top_loc).translation_to_rotate_pivot()
        space.MatchSpace(joints[1], btm_loc).translation_to_rotate_pivot()
        
        cmds.parent(joints[0], top_loc)
        cmds.parent(joints[-1], btm_loc)
        
        skin = skin_surface.get_skin()
        cmds.skinPercent( skin, self.surface, normalize=True )
        
        cmds.hide(joints)
        
        self.top_locator = top_loc
        self.btm_locator = btm_loc
        
        if self._top_parent and cmds.objExists(self._top_parent):
            cmds.parent(self.top_locator, self._top_parent)
        if self._btm_parent and cmds.objExists(self._btm_parent):
            cmds.parent(self.btm_locator, self._btm_parent)
        
        if self._top_constraint and cmds.objExists(self._top_constraint):
            eval('cmds.%s(%s,%s,mo = True)' % (self._top_constraint_type, self._top_constraint, top_loc))
        
        if self._btm_constraint and cmds.objExists(self._btm_constraint):
            eval('cmds.%s(%s,%s,mo = True)' % (self._btm_constraint_type, self._btm_constraint, btm_loc))
        
        if self._top_twist_fix:
            self._create_top_twister_joint()
        if self._btm_twist_fix:
            self._create_btm_twister_joint()
        
        return [top_loc, btm_loc]

class IkFkSwitch(object):
    """
    Not implemented, but would be nice to have the ik/fk switch behavior on any set. This class would help add it.
    """
    def __init__(self, fk_controls, ik_controls):
        pass
    
    def set_fk(self, fk_controls, fk_joints):
        pass
    
    def set_ik(self, ik_controls, ik_joints):
        pass
    
    def create(self):
        pass

def rename_control(old_name, new_name):
    
    new_name = Control(old_name).rename(new_name)
    
    return new_name

def rename_message_groups(search_name, replace_name):
    
    message_attrs = attr.get_message_attributes(search_name)
    
    if message_attrs:
    
        for attr_name in message_attrs:

            attr_node = '%s.%s' % (search_name, attr_name)
            
            if attr_name.startswith('group'):
                
                node = attr.get_attribute_input(attr_node, True)
                
                if node.find(search_name) > -1:
                    new_node = node.replace(search_name, replace_name)
                    
                    rename_message_groups(node, new_node)

                    constraints = cmds.listRelatives( node, type = 'constraint')
                    
                    if constraints:
                        
                        for constraint in constraints:
                            new_constraint = constraint.replace(node, new_node)
                            
                            cmds.rename(constraint, new_constraint)
                    
                    cmds.rename(node, new_node) 
          
def create_joint_buffer(joint, connect_inverse = True):
    
    fix_joint = cmds.joint(n = 'bufferFix_%s' % joint)
    cmds.setAttr('%s.drawStyle' % fix_joint, 2)
    space.MatchSpace(joint, fix_joint).translation_rotation()
    cmds.makeIdentity(fix_joint, apply = True, r = True)
    
    parent = cmds.listRelatives(joint, p = True, f = True)
    
    if parent:
        parent = parent[0]
        cmds.parent(fix_joint, parent)
        
        if connect_inverse:
            if not cmds.isConnected('%s.scale' % parent, '%s.inverseScale' % fix_joint):
                cmds.connectAttr('%s.scale' % parent, '%s.inverseScale' % fix_joint)
    
        
    cmds.parent(joint, fix_joint)
    
    return fix_joint
    
def create_distance_reader(xform1, xform2, on_distance = 1, off_distance = -1, negative_value = False):
    """
    Create a distance reader between 2 transforms.  
    The command will create an attribute from 0 to one. 
    0 when the distance is greater than off_distance. 
    1 when the distance is less than on_distance.
    -1 off distance uses the current distance between xform1 and xform2 as the off_distance.
    where on distance tells when to activate based on distance, the negative_value activates at -1 when the value goes the other way.
    
    
    Returns:
        str: distance node name
    """
    
    distance = cmds.createNode('distanceBetween', n = core.inc_name('distanceBetween_%s' % xform1))
    
    cmds.connectAttr('%s.worldMatrix' % xform1, '%s.inMatrix1' % distance)
    cmds.connectAttr('%s.worldMatrix' % xform2, '%s.inMatrix2' % distance)
    
    distance_value = cmds.getAttr('%s.distance' % distance)
    
    cmds.addAttr(distance, ln = 'currentDistance', k = True)
    cmds.addAttr(distance, ln = 'activate', min = 0, max = 1, dv = 0, k = True)
    
    if off_distance < 0:
        off_distance = distance_value
    
    cmds.connectAttr('%s.distance' % distance, '%s.currentDistance' % distance)
    
    if not negative_value:
        anim.quick_driven_key('%s.distance' % distance, '%s.activate' % distance, [off_distance, on_distance], [0,1], infinite = True, tangent_type = 'linear')
    if negative_value:
        neg_value = (off_distance - on_distance) + off_distance

        anim.quick_driven_key('%s.distance' % distance, '%s.activate' % distance, [neg_value, off_distance, on_distance], [-1, 0,1], infinite = True, tangent_type = 'linear')
        
    return distance

def create_distance_scale(xform1, xform2, axis = 'X', offset = 1):
    """
    Create a stretch effect on a transform by changing the scale when the distance changes between xform1 and xform2.
    
    Args:
        xform1 (str): The name of a transform.
        xform2 (str): The name of a transform.
        axis (str): "X", "Y", "Z" The axis to attach the stretch effect to.
        offset (float): Add an offset to the value.
        
    Returns:
        tuple: (locator1, locator2) The names of the two locators used to calculate distance.
    """
    locator1 = cmds.spaceLocator(n = core.inc_name('locatorDistance_%s' % xform1))[0]
    
    space.MatchSpace(xform1, locator1).translation()
    
    locator2 = cmds.spaceLocator(n = core.inc_name('locatorDistance_%s' % xform2))[0]
    space.MatchSpace(xform2, locator2).translation()
    
    distance = cmds.createNode('distanceBetween', n = core.inc_name('distanceBetween_%s' % xform1))
    
    multiply = cmds.createNode('multiplyDivide', n = core.inc_name('multiplyDivide_%s' % xform1))
    
    cmds.connectAttr('%s.worldMatrix' % locator1, '%s.inMatrix1' % distance)
    cmds.connectAttr('%s.worldMatrix' % locator2, '%s.inMatrix2' % distance)
    
    distance_value = cmds.getAttr('%s.distance' % distance)
    
    if offset != 1:
        anim.quick_driven_key('%s.distance' %distance, '%s.input1X' % multiply, [distance_value, distance_value*2], [distance_value, distance_value*2*offset], infinite = True)
    
    if offset == 1:
        cmds.connectAttr('%s.distance' % distance, '%s.input1X' % multiply)
    
    cmds.setAttr('%s.input2X' % multiply, distance_value)
    cmds.setAttr('%s.operation' % multiply, 2)
        
    cmds.connectAttr('%s.outputX' % multiply, '%s.scale%s' % (xform1, axis))
        
    return locator1, locator2

def create_sparse_joints_on_curve(curve, joint_count, description):
    """
    Create joints on a curve that are evenly spaced and not in hierarchy.
    """
    
    cmds.select(cl = True)
    
    total_length = cmds.arclen(curve)
    
    part_length = total_length/(joint_count-1)
    current_length = 0
    
    joints = []
    
    
    
    percent = 0
    
    segment = 1.00/joint_count
    
    for inc in range(0, joint_count):
        
        param = geo.get_parameter_from_curve_length(curve, current_length)
        
        position = geo.get_point_from_curve_parameter(curve, param)
        
        cmds.select(cl = True)  
        joint = cmds.joint(p = position, n = core.inc_name('joint_%s' % description) )
        
        cmds.addAttr(joint, ln = 'param', at = 'double', dv = param)
        
        if joints:
            cmds.joint(joints[-1], 
                       e = True, 
                       zso = True, 
                       oj = "xyz", 
                       sao = "yup")
        
        
        current_length += part_length
            
        joints.append(joint)
    
        percent += segment

    return joints

@core.undo_chunk
def create_joints_on_curve(curve, joint_count, description, attach = True, create_controls = False):
    """
    Create joints on curve that do not aim at child.
    
    Args:
        curve (str): The name of a curve.
        joint_count (int): The number of joints to create.
        description (str): The description to give the joints.
        attach (bool): Wether to attach the joints to the curve.
        create_controls (bool): Wether to create controls on the joints.
        
    Returns:
        list: [ joints, group, control_group ] joints is a list of joinst, group is the main group for the joints, control_group is the main group above the controls. 
        If create_controls = False then control_group = None
        
    """
    group = cmds.group(em = True, n = core.inc_name('joints_%s' % curve))
    control_group = None
    
    if create_controls:
        control_group = cmds.group(em = True, n = core.inc_name('controls_%s' % curve))
        cmds.addAttr(control_group, ln = 'twist', k = True)
        cmds.addAttr(control_group, ln = 'offsetScale', min = -1, dv = 0, k = True)
    
    cmds.select(cl = True)
    
    total_length = cmds.arclen(curve)
    
    part_length = total_length/(joint_count-1)
    current_length = 0
    
    joints = []
    
    cmds.select(cl = True)
    
    percent = 0
    
    segment = 1.00/joint_count
    
    for inc in range(0, joint_count):
        
        param = geo.get_parameter_from_curve_length(curve, current_length)
        
        position = geo.get_point_from_curve_parameter(curve, param)
        if attach:
            cmds.select(cl = True)
            
        joint = cmds.joint(p = position, n = core.inc_name('joint_%s' % description) )
        
        cmds.addAttr(joint, ln = 'param', at = 'double', dv = param, k = True)
        
        if joints:
            cmds.joint(joints[-1], 
                       e = True, 
                       zso = True, 
                       oj = "xyz", 
                       sao = "yup")
        
        if attach:
            
            attach_node = geo.attach_to_curve( joint, curve, parameter = param )
            cmds.parent(joint, group)
            
            cmds.connectAttr('%s.param' % joint, '%s.parameter' % attach_node)
        
        current_length += part_length
        
        if create_controls:
            control = Control(core.inc_name('CNT_TWEAKER_%s' % description.upper()))
            control.set_curve_type('pin')
            control.rotate_shape(90, 0, 0)
            control.hide_visibility_attribute()
            
            control_name = control.get()  
            
            parameter_value = cmds.getAttr('%s.parameter' % attach_node)
            
            percent_var = attr.MayaNumberVariable('percent')
            percent_var.set_min_value(0)
            percent_var.set_max_value(10)
            percent_var.set_value(parameter_value*10)
            percent_var.create(control_name)
            
            attr.connect_multiply(percent_var.get_name(), '%s.parameter' % attach_node, 0.1)
            
            xform = space.create_xform_group(control_name)

            cmds.connectAttr('%s.positionX' % attach_node, '%s.translateX'  % xform)
            cmds.connectAttr('%s.positionY' % attach_node, '%s.translateY'  % xform)
            cmds.connectAttr('%s.positionZ' % attach_node, '%s.translateZ'  % xform)
            
            
            
            side = control.color_respect_side(True, 0.1)
            
            if side != 'C':
                control_name = cmds.rename(control_name, core.inc_name(control_name[0:-3] + '1_%s' % side))
            
            attr.connect_translate(control_name, joint)
            attr.connect_rotate(control_name, joint)

            offset = util.fade_sine(percent)
            
            attr.connect_multiply('%s.twist' % control_group, '%s.rotateX' % joint, offset)

            plus = cmds.createNode('plusMinusAverage', n = 'plus_%s' % control_group)
            cmds.setAttr('%s.input1D[0]' % plus, 1)
            
            attr.connect_multiply('%s.offsetScale' % control_group, '%s.input1D[1]' % plus, offset, plus = False)
            
            multiply = attr.MultiplyDivideNode(control_group)
            
            multiply.input1X_in('%s.output1D' % plus)
            multiply.input1Y_in('%s.output1D' % plus)
            multiply.input1Z_in('%s.output1D' % plus)
            
            multiply.input2X_in('%s.scaleX' % control_name)
            multiply.input2Y_in('%s.scaleY' % control_name)
            multiply.input2Z_in('%s.scaleZ' % control_name)
            

            multiply.outputX_out('%s.scaleX' % joint)
            multiply.outputY_out('%s.scaleY' % joint)
            multiply.outputZ_out('%s.scaleZ' % joint)

            cmds.parent(xform, control_group)
            
        joints.append(joint)
    
        percent += segment
    
    
    
    if not attach:
        cmds.parent(joints[0], group)
    
    
    
    return joints, group, control_group


def create_spline_ik_stretch(curve, joints, node_for_attribute = None, create_stretch_on_off = False, create_bulge = True, scale_axis = 'X'):
    """
    Makes the joints stretch on the curve. 
    Joints must be on a spline ik that is attached to the curve.
    
    Args:
        curve (str): The name of the curve that joints are attached to via spline ik.
        joints (list): List of joints attached to spline ik.
        node_for_attribute (str): The name of the node to create the attributes on.
        create_stretch_on_off (bool): Wether to create extra attributes to slide the stretch value on/off.
        create_bulge (bool): Wether to add bulging to the other axis that are not the scale axis.
        scale_axis (str): 'X', 'Y', or 'Z', the axis that the joints stretch on.
    """
    scale_axis = scale_axis.capitalize()
    
    arclen_node = cmds.arclen(curve, ch = True, n = core.inc_name('curveInfo_%s' % curve))
    
    arclen_node = cmds.rename(arclen_node, core.inc_name('curveInfo_%s' % curve))
    
    multiply_scale_offset = cmds.createNode('multiplyDivide', n = core.inc_name('multiplyDivide_offset_%s' % arclen_node))
    cmds.setAttr('%s.operation' % multiply_scale_offset, 2 )
    
    multiply = cmds.createNode('multiplyDivide', n = core.inc_name('multiplyDivide_%s' % arclen_node))
    
    cmds.connectAttr('%s.arcLength' % arclen_node, '%s.input1X' % multiply_scale_offset)
    
    cmds.connectAttr('%s.outputX' % multiply_scale_offset, '%s.input1X' % multiply)
    
    cmds.setAttr('%s.input2X' % multiply, cmds.getAttr('%s.arcLength' % arclen_node))
    cmds.setAttr('%s.operation' % multiply, 2)
    
    joint_count = len(joints)
    
    segment = 1.00/joint_count
    
    percent = 0
    
    for joint in joints:
        
        attribute = '%s.outputX' % multiply
             
        if create_stretch_on_off and node_for_attribute:
            
            var = attr.MayaNumberVariable('stretchOnOff')
            var.set_min_value(0)
            var.set_max_value(1)
            var.set_keyable(True)
            var.create(node_for_attribute)
        
            blend = cmds.createNode('blendColors', n = 'blendColors_stretchOnOff_%s' % curve)
    
            cmds.connectAttr(attribute, '%s.color1R' % blend)
            cmds.setAttr('%s.color2R' % blend, 1)
            
            cmds.connectAttr('%s.outputR' % blend, '%s.scale%s' % (joint, scale_axis))
            
            cmds.connectAttr('%s.stretchOnOff' % node_for_attribute, '%s.blender' % blend)
            
        if not create_stretch_on_off:
            cmds.connectAttr(attribute, '%s.scale%s' % (joint, scale_axis))
        
        if create_bulge:
            #bulge cbb
            plus = cmds.createNode('plusMinusAverage', n = 'plusMinusAverage_scale_%s' % joint)
            
            cmds.addAttr(plus, ln = 'scaleOffset', dv = 1, k = True)
            cmds.addAttr(plus, ln = 'bulge', dv = 1, k = True)
            
            arc_value = util.fade_sine(percent)
            
            attr.connect_multiply('%s.outputX' % multiply_scale_offset, '%s.bulge' % plus, arc_value)
            
            attr.connect_plus('%s.scaleOffset' % plus, '%s.input1D[0]' % plus)
            attr.connect_plus('%s.bulge' % plus, '%s.input1D[1]' % plus)
            
            scale_value = cmds.getAttr('%s.output1D' % plus)
            
            multiply_offset = cmds.createNode('multiplyDivide', n = 'multiply_%s' % joint)
            cmds.setAttr('%s.operation' % multiply_offset, 2)
            cmds.setAttr('%s.input1X' % multiply_offset, scale_value)
        
            cmds.connectAttr('%s.output1D' % plus, '%s.input2X' % multiply_offset)
        
            blend = cmds.createNode('blendColors', n = 'blendColors_%s' % joint)
        
            attribute = '%s.outputR' % blend
            
            if node_for_attribute:
                cmds.connectAttr('%s.outputX' % multiply_offset, '%s.color1R' % blend)
            
                cmds.setAttr('%s.color2R' % blend, 1)
                
                var = attr.MayaNumberVariable('stretchyBulge')
                var.set_min_value(0)
                var.set_max_value(10)
                var.set_keyable(True)
                var.create(node_for_attribute)
                
                attr.connect_multiply('%s.stretchyBulge' % node_for_attribute, 
                                 '%s.blender' % blend, 0.1)
                
            if not node_for_attribute:
                attribute = '%s.outputX' % multiply_offset
    
            if scale_axis == 'X':
                cmds.connectAttr(attribute, '%s.scaleY' % joint)
                cmds.connectAttr(attribute, '%s.scaleZ' % joint)
            if scale_axis == 'Y':
                cmds.connectAttr(attribute, '%s.scaleX' % joint)
                cmds.connectAttr(attribute, '%s.scaleZ' % joint)
            if scale_axis == 'Z':
                cmds.connectAttr(attribute, '%s.scaleX' % joint)
                cmds.connectAttr(attribute, '%s.scaleY' % joint)
        
        percent += segment

def create_simple_spline_ik_stretch(curve, joints, stretch_axis = 'Y'):
    """
    Stretch joints on curve. Joints must be attached to a spline ik. This is a much simpler setup than create_spline_ik_stretch.
    
    Args:
        curve (str): The name of the curve that joints are attached to via spline ik.
        joints (list): List of joints attached to spline ik.
    """
    arclen_node = cmds.arclen(curve, ch = True, n = core.inc_name('curveInfo_%s' % curve))
    
    arclen_node = cmds.rename(arclen_node, core.inc_name('curveInfo_%s' % curve))
    
    multiply_scale_offset = cmds.createNode('multiplyDivide', n = core.inc_name('multiplyDivide_offset_%s' % arclen_node))
    cmds.setAttr('%s.operation' % multiply_scale_offset, 2 )
    
    multiply = cmds.createNode('multiplyDivide', n = core.inc_name('multiplyDivide_%s' % arclen_node))
    
    cmds.connectAttr('%s.arcLength' % arclen_node, '%s.input1X' % multiply_scale_offset)
    
    cmds.connectAttr('%s.outputX' % multiply_scale_offset, '%s.input1X' % multiply)
    
    cmds.setAttr('%s.input2X' % multiply, cmds.getAttr('%s.arcLength' % arclen_node))
    cmds.setAttr('%s.operation' % multiply, 2)
    
    joint_count = len(joints)
    
    segment = 1.00/joint_count
    
    percent = 0
    
    for joint in joints:
        
        attribute = '%s.outputX' % multiply

        cmds.connectAttr(attribute, '%s.scale%s' % (joint, stretch_axis))
        
        percent += segment

def create_bulge_chain(joints, control, max_value = 15):
    """
    Adds scaling to a joint chain that mimics a cartoony water bulge moving along a tube.
    
    Args:
        joints (list): List of joints that the bulge effect should move along.
        control (str): Name of the control to put the bulge slider on.
        max_value (float): The maximum value of the slider.
    """
    
    control_and_attribute = '%s.bulge' % control
    
    if not cmds.objExists(control_and_attribute):
        var = attr.MayaNumberVariable('bulge')
        var.set_variable_type(var.TYPE_DOUBLE)
        var.set_min_value(0)
        var.set_max_value(max_value)
        var.create(control)
        
    attributes = ['Y','Z']
    
    joint_count = len(joints)
    
    offset = 10.00/ joint_count
    
    initial_driver_value = 0
    default_scale_value = 1
    scale_value = 2
    
    inc = 0
    
    for joint in joints:
        for attr in attributes:
            
            cmds.setDrivenKeyframe('%s.scale%s' % (joint, attr), 
                                   cd = control_and_attribute, 
                                   driverValue = initial_driver_value, 
                                   value = default_scale_value, 
                                   itt = 'linear', 
                                   ott = 'linear' )
            
            cmds.setDrivenKeyframe('%s.scale%s' % (joint, attr), 
                                   cd = control_and_attribute, 
                                   driverValue = initial_driver_value + offset*3, 
                                   value = scale_value,
                                   itt = 'linear', 
                                   ott = 'linear' )            
            
            cmds.setDrivenKeyframe('%s.scale%s' % (joint, attr), 
                                   cd = control_and_attribute, 
                                   driverValue = initial_driver_value + (offset*6), 
                                   value = default_scale_value, 
                                   itt = 'linear', 
                                   ott = 'linear' )
            
        inc += 1
        initial_driver_value += offset
        
def create_distance_falloff(source_transform, source_local_vector = [1,0,0], target_world_vector = [1,0,0], description = 'falloff'):
    """
    Under development.
    """
    
    distance_between = cmds.createNode('distanceBetween', 
                                        n = core.inc_name('distanceBetween_%s' % description) )
    
    cmds.addAttr(distance_between,ln = 'falloff', at = 'double', k = True)
        
    follow_locator = cmds.spaceLocator(n = 'follow_%s' % distance_between)[0]
    match = space.MatchSpace(source_transform, follow_locator)
    match.translation_rotation()
    cmds.parent(follow_locator, source_transform)
    cmds.move(source_local_vector[0], source_local_vector[1], source_local_vector[2], follow_locator, r = True, os = True)
    
    attr.set_color(follow_locator, 6)
    
    target_locator = cmds.spaceLocator(n = 'target_%s' % distance_between)[0]
    match = space.MatchSpace(source_transform, target_locator)
    match.translation_rotation()
    
    attr.set_color(target_locator, 13)

    parent = cmds.listRelatives(source_transform, p = True)
    
    if parent:
        parent = parent[0]
        cmds.parent(target_locator, parent)
    
    cmds.move(target_world_vector[0], target_world_vector[1], target_world_vector[2], target_locator, r = True, ws = True)
    
    cmds.parent(follow_locator, target_locator)
    
    cmds.parentConstraint(source_transform, follow_locator, mo = True)
        
    cmds.connectAttr('%s.worldMatrix' % follow_locator, 
                     '%s.inMatrix1' % distance_between)
        
    cmds.connectAttr('%s.worldMatrix' % target_locator, 
                     '%s.inMatrix2' % distance_between)
    
    distance_value = cmds.getAttr('%s.distance' % distance_between)
    
    driver = '%s.distance' % distance_between
    driven = '%s.falloff' % distance_between
     
    cmds.setDrivenKeyframe(driven,
                           cd = driver, 
                           driverValue = distance_value, 
                           value = 0, 
                           itt = 'linear', 
                           ott = 'linear')

    cmds.setDrivenKeyframe(driven,
                           cd = driver,  
                           driverValue = 0, 
                           value = 1, 
                           itt = 'linear', 
                           ott = 'linear')  
    
    return distance_between    

def create_attribute_lag(source, attribute, targets):
    """
    Add lag to the targets based on a source attribute. A lag attribute will also be added to source to turn the effect on and off. 
    If you are animating the rotation of a control inputs are as follows:
    
    create_attribute_lag( 'CNT_FIN_1_L', 'rotateY', ['driver_CNT_FIN_2_L, 'driver_CNT_FIN_3_L', 'driver_CNT_FIN_4_L'] )
    
    Args:
        source (str): The node where the attribute lives. Also a lag attribute will be created here.
        attribute (str): The attribute to lag. Sometimes can be rotateX, rotateY or rotateZ.
        targets (list): A list of targets to connect the lag into. The attribute arg will be used as the attribute to connect into on each target.
    """
    
    var = attr.MayaNumberVariable('lag')
    var.set_value(0)
    var.set_min_value(0)
    var.set_max_value(1)
    var.create(source)
    
    frame_cache = cmds.createNode('frameCache', n = 'frameCache_%s_%s' % (source, attribute) )
    
    cmds.connectAttr('%s.%s' % (source, attribute), '%s.stream' % frame_cache)
    
    target_count = len(targets)
    
    for inc in range(0, target_count):
        
        cmds.createNode('blendColors')
        blend = attr.connect_blend('%s.past[%s]' % (frame_cache, inc+1), 
                              '%s.%s' % (source,attribute),
                              '%s.%s' % (targets[inc], attribute))
        
        attr.connect_plus('%s.lag' % source, '%s.blender' % blend)
        
def create_attribute_spread(control, transforms, name = 'spread', axis = 'Y', invert = False, create_driver = False):
    """
    Given a list of transforms, create a spread attribute which will cause them to rotate apart.
    
    Args:
        control (str): The name of a control where the spread attribute should be created.
        transforms (list): A list of transforms that should spread apart by rotation.
        name (str): The name of the attribute to create.
        axis (str): Can be 'X','Y','Z'
        invert (bool): Wether to invert the spread behavior so it can mirror.
        create_driver (bool): Wether to create a driver group above the transform.
    """
    
    found = []
    
    for transform in transforms:
        if transform and cmds.objExists(transform):
            found.append(transform)
    
    if not found:
        util.warning('No transforms found to spead.')
        return
    
    variable = '%s.%s' % (control, name)
    
    transforms = found
    
    count = len(transforms)
    
    section = 2.00/(count-1)
    
    spread_offset = 1.00
    
    if not cmds.objExists('%s.SPREAD' % control):
        title = attr.MayaEnumVariable('SPREAD')
        title.create(control)
        
    if not cmds.objExists(variable):    
        spread = attr.MayaNumberVariable(name)
        spread.create(control)
        
    
    for transform in transforms:
        
        if create_driver:
            transform = space.create_xform_group(transform, 'spread')
        
        if invert:
            spread_offset_value = -1 * spread_offset
        if not invert:
            spread_offset_value = spread_offset
        
        attr.connect_multiply(variable, '%s.rotate%s' % (transform, axis), spread_offset_value)
                
        spread_offset -= section
        
        
        
def create_attribute_spread_translate(control, transforms, name = 'spread', axis = 'Z', invert = False):
    """
    Given a list of transforms, create a spread attribute which will cause them to translate apart.
    This is good for fingers that are rigged with ik handles.
    
    Args:
        control (str): The name of a control where the spread attribute should be created.
        transforms (list): A list of transforms that should spread apart by translation.
        name (str): The name of the attribute to create.
        axis (str): Can be 'X','Y','Z'
        invert (bool): Wether to invert the spread behavior so it can mirror.
    """
    
    variable = '%s.%s' % (control, name)
    
    count = len(transforms)
    
    section = 2.00/(count-1)
    
    spread_offset = 1.00
    
    if invert == True:
        spread_offset = -1.00
    
    
    if not cmds.objExists('%s.SPREAD' % control):
        title = attr.MayaEnumVariable('SPREAD')
        title.create(control)
        
    if not cmds.objExists(variable):    
        spread = attr.MayaNumberVariable(name)
        spread.create(control)
        
    
    for transform in transforms:
        attr.connect_multiply(variable, '%s.translate%s' % (transform, axis), spread_offset)
        
        if invert == False:        
            spread_offset -= section
        if invert == True:
            spread_offset += section    
        
def create_offset_sequence(attribute, target_transforms, target_attributes):
    """
    Create an offset where target_transforms lag behind the attribute.
    """
    #split = attribute.split('.')
    
    count = len(target_transforms)
    inc = 0
    section = 1.00/count
    offset = 0
    
    anim_curve = cmds.createNode('animCurveTU', n = 'animCurveTU_%s' % attribute.replace('.','_'))
    #cmds.connectAttr(attribute, '%s.input' % anim_curve)
    
    for transform in target_transforms:
        frame_cache = cmds.createNode('frameCache', n = 'frameCache_%s' % transform)
        
        cmds.setAttr('%s.varyTime' % frame_cache, inc)
        
        
        cmds.connectAttr('%s.output' % anim_curve, '%s.stream' % frame_cache)
        
        cmds.setKeyframe( frame_cache, attribute='stream', t= inc )
        
        for target_attribute in target_attributes:
            cmds.connectAttr('%s.varying' % frame_cache, 
                             '%s.%s' % (transform, target_attribute))
        
        
        inc += 1
        offset += section


def is_control(transform):
    
    is_control = False
    
    maybe_control = False 
    
    
    if transform.endswith('_CON'):
        maybe_control = True

    if transform.startswith('CNT_'):
        maybe_control = True
                
    if cmds.objExists('%s.control' % transform):
        return True
    
    if cmds.objExists('%s.tag' % transform):
        
        value = cmds.getAttr('%s.tag' % transform)
            
        if value:
            maybe_control = True
        
    if cmds.objExists('%s.curveType' % transform):
            if maybe_control:
                
                if not core.has_shape_of_type(transform, 'nurbsCurve'):
                    return False
                
                return True
        
    if maybe_control:
        if core.has_shape_of_type(transform, 'nurbsCurve') or core.has_shape_of_type(transform, 'nurbsSurface'):
            return True
        
          
        

def get_controls(namespace = ''):
    """
    Get the controls in a scene.
    
    It follows these rules
    
    First check if a transform starts with "CNT_"
    Second check if a transform has a an attribute named control.
    Third check if a transform has an attribute named tag and is a nurbsCurve, and that tag has a value.
    Fourth check if a transform has an attribute called curveType.
    
    If it matches any of these conditions it is considered a control.
    
    Returns:
        list: List of control names.
    """
    
    name = '*'
    if namespace:
        name = '%s:*' % namespace
    
    transforms = cmds.ls(name, type = 'transform')
    joints = cmds.ls(name, type = 'joint')
    
    if joints:
        transforms += joints
    
    found = []
    found_with_value = []
    
    
    for transform_node in transforms:
        
        if cmds.objExists('%s.POSE' % transform_node):
            continue
        
        transform = core.remove_namespace_from_string(transform_node)
        
        if transform.startswith('CNT_'):
            found.append(transform_node)
            continue
        
        
        #temprorary until I change the prefix behavior
        if transform.startswith('xform_'):
            continue        
        if transform.startswith('driver_'):
            continue
        if transform.startswith('follow_'):
            continue
        if transform.startswith('offset_'):
            continue
        if transform.find('driver_') > -1:
            continue
        
       
        if transform.endswith('_CON'):
            found.append(transform_node)
            continue
        
        if transform.endswith('_Ctrl'):
            found.append(transform_node)
            continue
        
        if cmds.objExists('%s.control' % transform_node):
            found.append(transform_node)
            continue
        
        if cmds.objExists('%s.tag' % transform_node):
            
            if core.has_shape_of_type(transform_node, 'nurbsCurve'):
                
                
                found.append(transform_node)
                value = cmds.getAttr('%s.tag' % transform_node)
                
                if value:
                    found_with_value.append(transform_node)
            
            continue
        
        if cmds.objExists('%s.curveType' % transform_node):
            found.append(transform_node)
            continue
    
    if found_with_value:
        found = found_with_value
        
    return found
    
def select_controls(namespace = ''):
    
    controls = get_controls(namespace)
    cmds.select(controls)
    
def key_controls(namespace = ''):
    
    controls = get_controls(namespace)
    cmds.setKeyframe(controls, shape = 0, controlPoints = 0, hierarchy = 'none', breakdown = 0)
    
@core.undo_chunk
def mirror_control(control):
    """
    Find the right side control of a left side control, and mirror the control cvs.
    
    It follows these rules:
    It will only match if the corresponding right side name exists.
    
    Replace _L with _R at the end of a control name.
    Replace L_ with R_ at the start of a control name.
    Replace lf with rt inside the control name
    """
    if not control:
        return
    
    shapes = core.get_shapes(control)
    
    if not shapes:
        return
    
    shape = shapes[0]
    
    if not cmds.objExists('%s.cc' % shape):
        return
    
    other_control = space.find_transform_right_side(control)
    
    if not other_control or not cmds.objExists(other_control):
        return
                    
    other_shapes = core.get_shapes(other_control)
    if not other_shapes:
        return
    
    for inc in range(0,len(shapes)):
        shape = shapes[inc]
        other_shape = other_shapes[inc]
        
        if not cmds.objExists('%s.cc' % other_shape):
            return
        
        cvs = cmds.ls('%s.cv[*]' % shape, flatten = True)
        other_cvs = cmds.ls('%s.cv[*]' % other_shape, flatten = True)
        
        if len(cvs) != len(other_cvs):
            return
        
        for inc in range(0, len(cvs)):
            position = cmds.pointPosition(cvs[inc], world = True)
            
            x_value = position[0] * -1
                 
            cmds.move(x_value, position[1], position[2], other_cvs[inc], worldSpace = True)
            
    return other_control

@core.undo_chunk
def mirror_controls():
    """
    Mirror cv positions of all controls in the scene. 
    See get_controls() and mirror_control() for rules. 
    """
    #selection = cmds.ls(sl = True)
    
    controls = get_controls()
    
    found = []
    
    """
    if selection:
        for selection in selection:
            if selection in controls:
                found.append(selection)
    
    if not selection or not found:
        found = controls
    """
    
    found = controls
    
    mirrored_controls = []
    
    for control in found:
        
        if control in mirrored_controls:
            continue
        
        other_control = mirror_control(control)
        
        mirrored_controls.append(other_control)
        

def mirror_mesh_to_matching_mesh(left_mesh, right_mesh):
    """
    given 2 meshes under different transforms
    using the positions from left mesh, 
    calculate the right position and set the verts on the right mesh.
    """
    verts = cmds.ls('%s.vtx[*]' % left_mesh, flatten = True)
    vert_count = len(verts)
    
    transform_pos = cmds.xform(left_mesh, q = True, ws = True, t = True)
    
    new_pos = transform_pos
    new_pos[0] = (new_pos[0] * -1)
    
    cmds.xform(right_mesh, ws = True, t = new_pos)
    
    
    other_verts = cmds.ls('%s.vtx[*]' % right_mesh, flatten = True)
    
    compatible = geo.is_mesh_compatible(left_mesh, right_mesh)
    if not compatible:
        cmds.warning('left and right mesh not compatible')
        return
    
    for inc in range(0, vert_count):
        
        position = cmds.xform(verts[inc], q = True, ws = True, t = True)
        
        new_position = list(position)
        new_position[0] = (position[0] * -1)
        
        cmds.xform(other_verts[inc], ws = True, t = new_position)

def mirror_curve(prefix = None):
    """
    Mirror curves in a scene if the end in _L and _R
    """
    
    curves = None
    
    if prefix:
        curves = cmds.ls('%s*' % prefix, type = 'transform')
    if not prefix:
        found = []
        
        curve_shapes = cmds.ls(type = 'nurbsCurve')
        
        for shape in curve_shapes:
            parent = cmds.listRelatives(shape, type = 'transform', p = True)[0]
            
            if not parent in found:
                found.append(parent)
        
        if found:
            curves =   found
    
    if not curves:
        return
    
    for curve in curves:
        if curve.endswith('_R'):
            continue
        
        other_curve = None
        
        if curve.endswith('_L'):
            other_curve = curve[:-1] + 'R'
        
        cvs = cmds.ls('%s.cv[*]' % curve, flatten = True)
        
        if not other_curve:
            
            cv_count = len(cvs)
            
            for inc in range(0, cv_count):
                
                cv = '%s.cv[%s]' % (curve, inc)
                other_cv = '%s.cv[%s]' % (curve, cv_count-(inc+1))
                
                position = cmds.xform(cv, q = True, ws = True, t = True)
                
                new_position = list(position)
                
                new_position[0] = position[0] * -1
                
                cmds.xform(other_cv, ws = True, t = new_position)
                
                if inc == cv_count:
                    break
        
        if other_curve:
            
            transform_pos = cmds.xform(curve, q = True, ws = True, t = True)
            
            new_pos = transform_pos
            new_pos[0] = (new_pos[0] * -1)
            
            cmds.xform(other_curve, ws = True, t = new_pos)
            
            other_cvs = cmds.ls('%s.cv[*]' % other_curve, flatten = True)
            
            if len(cvs) != len(other_cvs):
                continue
            
            for inc in range(0, len(cvs)):
                
                position = cmds.xform(cvs[inc], q = True, ws = True, t = True)
                
                new_position = list(position)
                new_position[0] = (position[0] * -1)
                
                cmds.xform(other_cvs[inc], ws = True, t = new_position)
    
def process_joint_weight_to_parent(mesh):
    """
    Sometimes joints have a sub joint added to help hold weighting and help with heat weighting.
    This will do it for all joints with name matching process_ at the beginning on the mesh arg that is skinned. 
    
    Args:
        mesh (str): A mesh skinned to process joints.
    """
    scope = cmds.ls('process_*', type = 'joint')
    
    
    progress = core.ProgressBar('process to parent %s' % mesh, len(scope))
    
    for joint in scope:
        progress.status('process to parent %s: %s' % (mesh, joint))
        
        deform.transfer_weight_from_joint_to_parent(joint, mesh)
        
        progress.inc()
        
        if util.break_signaled():
            break
        
        if progress.break_signaled():
            break
        
    progress.end()
    
    cmds.delete(scope)

@core.undo_chunk
def joint_axis_visibility(bool_value):
    """
    Show/hide the axis orientation of each joint.
    """
    joints = cmds.ls(type = 'joint')
    
    for joint in joints:
        
        cmds.setAttr('%s.displayLocalAxis' % joint, bool_value)



def hook_ik_fk(control, joint, groups = None, attribute = 'ikFk'): 
    """
    Convenience for hooking up ik fk.
    
    Args:
        control (str): The name of the control where the attribute arg should be created.
        joint (str): The joint with the switch attribute. When adding multiple rigs to one joint chain, the first joint will have a switch attribute added.
        groups (list): The ik control group name and the fk control group name.
        attribute (str): The name to give the attribute on the control. Usually 'ikFk'
    """
    if not cmds.objExists('%s.%s' % (control, attribute)): 
        cmds.addAttr(control, ln = attribute, min = 0, max = 1, dv = 0, k = True) 
      
    attribute_ikfk = '%s.%s' % (control, attribute) 
      
    cmds.connectAttr(attribute_ikfk, '%s.switch' % joint) 

    if groups:      
        for inc in range(0, len(groups)): 
            attr.connect_equal_condition(attribute_ikfk, '%s.visibility' % groups[inc], inc)
            
    nodes = attr.get_attribute_outputs('%s.switch' % joint, node_only = False)
    
    
    
    for node in nodes:
    
        good = False
        
        nice_node_name = core.get_basename(node, remove_attribute = True)
        
        if node.find('.visibility') > -1:
            good = True
        
        if cmds.nodeType(node) == 'condition':
            
            nodes = attr.get_attribute_outputs('%s.outColorR' % nice_node_name, node_only = True)
            
            if nodes:
                nice_node_name = nodes[0]
                good = True
                
        if good:
            attr.connect_message(control, nice_node_name, 'switch') 

 
            
       
def fix_fade(target_curve, follow_fade_multiplies):
    """
    This fixes multiplyDivides so that they will multiply by a value that has them match the curve when they move.
    
    For example if eye_lid_locator is multiplyDivided in translate to move with CNT_EYELID. 
    Pass its multiplyDivide node to this function with a curve that matches the btm eye lid.
    The function will find the amount the multiplyDivide.input2X needs to move, 
    so that when CNT_EYELID moves on Y it will match the curvature of target_curve.
    
    Args:
        target_curve (str): The name of the curve to match to.
        follow_fade_multiplies (str): A list of a multiplyDivides.
    """
    multiplies = follow_fade_multiplies

    mid_control = multiplies[0]['source']
    
    control_position = cmds.xform(mid_control, q = True, ws = True, t = True)
    control_position_y = [0, control_position[1], 0]
    
    parameter = geo.get_y_intersection(target_curve, control_position)
    
    control_at_curve_position = cmds.pointOnCurve(target_curve, parameter = parameter)
    control_at_curve_y = [0, control_at_curve_position[1], 0]
    
    total_distance = util.get_distance(control_position_y, control_at_curve_y)
    
    multi_count = len(multiplies)
    
    for inc in range(0, multi_count):
        multi = multiplies[inc]['node']
        driver = multiplies[inc]['target']
        
        driver_position = cmds.xform(driver, q = True, ws = True, t = True)
        driver_position_y = [0, driver_position[1], 0]
        
        
        parameter = geo.get_y_intersection(target_curve, driver_position)
        
        driver_at_curve = cmds.pointOnCurve(target_curve, parameter = parameter)
        driver_at_curve_y = [0, driver_at_curve[1], 0]
        
        driver_distance = util.get_distance(driver_position_y, driver_at_curve_y)
        
        value = (driver_distance/total_distance)
    
        cmds.setAttr('%s.input2Y' % multi, value)
        
@core.undo_chunk
def scale_controls(value):
    things = get_controls()

    if not things:
        return
    
    
    if things:
        for thing in things:
    
            shapes = core.get_shapes(thing)
        
            components = core.get_components_from_shapes(shapes)
            
            pivot = cmds.xform( thing, q = True, rp = True, ws = True)
    
            if components:
                cmds.scale(value, value, value, components, p = pivot, r = True)
                
@core.undo_chunk
def fix_sub_controls(controls = None):
    
    if not controls:
        scope = cmds.ls(sl = True)
        if scope:
            controls = scope
    if not controls:
        return
    
    controls = util.convert_to_sequence(controls)
    
    found = []
    
    for control in controls:
        if not core.has_shape_of_type(control, 'nurbsCurve'):
            continue
        
        if not cmds.objExists('%s.subVisibility' % control):
            continue
        
        outputs = attr.get_attribute_outputs('%s.subVisibility' % control, node_only=True)
        outputs.sort()
        
        scale_offset = .85
        
        if not outputs:
            util.warning('No controls connected to subVisibility. Check that the subVisibility attribute was not edited.')
        
        visited = {}
        
        for output_node in outputs:
            
            if output_node in visited:
                continue
            
            if cmds.nodeType(output_node) == 'nurbsCurve':
                parent = cmds.listRelative(output_node, p = True)[0]
                
                if parent in visited:
                    continue
                
                visited[parent[0]] = None
            else:
                visited[output_node] = None
            
            transform = output_node
            shape = None
            
            if cmds.nodeType(output_node) == 'nurbsCurve':
                
                transform = cmds.listRelative(output_node, p = True)
                shape = output_node
                
            if not shape:
                if not core.has_shape_of_type(transform, 'nurbsCurve'):
                    continue
                
                shapes = core.get_shapes(transform, 'nurbsCurve')
                
            
            control_shapes = core.get_shapes(control)
            
            if len(shapes) != len(control_shapes):
                continue
            
            for inc in range(0, len(control_shapes)):
                
                if not geo.is_cv_count_same(control_shapes[inc], shapes[inc]):
                    continue
                
                geo.match_cv_position(control_shapes[inc], shapes[inc])
                
            
            control_inst = Control(transform)
            control_inst.scale_shape(scale_offset, scale_offset, scale_offset, use_pivot= False)
            found.append(transform)
                
            scale_offset -= .1
            
    cmds.select(found)

def set_control_space(x,y,z, control, compensate_cvs = True):
    
    xform = space.get_xform_group(control)
    
    cmds.setAttr('%s.scaleX' % xform, x)
    cmds.setAttr('%s.scaleY' % xform, y)
    cmds.setAttr('%s.scaleZ' % xform, z)
    
    if compensate_cvs:
        offset_x = 1.0/x
        offset_y = 1.0/y
        offset_z = 1.0/z
        
        control_inst = Control(control)
        control_inst.scale_shape(offset_x, offset_y, offset_z)
    
def mesh_border_to_control_shape(mesh, control, offset = .1):
    
    new_curve = geo.create_curve_from_mesh_border(mesh, offset)
    control_inst = Control(control)
    control_inst.copy_shapes(new_curve)
    
    cmds.delete(new_curve)
    
def edge_loop_to_control_shape(edge, control, offset = .1):
    
    new_curve = geo.create_curve_from_edge_loop(edge, offset)
    control_inst = Control(control)
    control_inst.copy_shapes(new_curve)
    
    cmds.delete(new_curve)

def is_control_group(control_group):
    if cmds.objExists('%s.rigControlGroup' % control_group):
        return True
    return False

def get_control_groups():
    
    found = []
    
    transforms = cmds.ls(type = 'transform')
    for transform in transforms:
        if is_control_group(transform):
            found.append(transform)
    
    return found

def get_important_info(control_group):
    """
    Retruns a dictionary with ud attributes and values
    """
    ud_attrs = cmds.listAttr(control_group, ud = True)

    found_dict = {}
    
    controls = []
    sub_controls = []
    all_controls = []
    joints = []
    
    for attr_name in ud_attrs:
        
        node_and_attr = '%s.%s' % (control_group, attr_name)
        
        found_dict[attr_name] = None
        value = None
        if cmds.getAttr(node_and_attr, type = True) == 'message':
            value = attr.get_message_input(control_group, attr_name)
        else:
            value = cmds.getAttr(node_and_attr)
        
        if attr_name.startswith('control'):
            controls.append(value)
            all_controls.append(value)
        if attr_name.startswith('subControl'):
            sub_controls.append(value)
            if value:
                all_controls.append(value)
        if attr_name.startswith('joint'):
            joints.append(value)
        
        found_dict[attr_name] = value
    
    found_dict['all_controls'] = all_controls
    found_dict['controls'] = controls
    found_dict['sub_controls'] = sub_controls
    found_dict['joints'] = joints
    
    found_dict['hasSwtich'] = has_switch(control_group)
    
    return found_dict

def get_control_group_info(control_group):
    """
    Returns a class with ud attributes and values
    """
    return ControlGroup(control_group)
    

    
def has_switch(control):
    
    group = get_control_group_with_switch(control)
    
    if group:
        return True
    
    return False

def get_control_group_with_switch(control):
    connected = attr.get_attribute_outputs('%s.message' % control, node_only = True)
    parent_connected = attr.get_attribute_input('%s.switchParent' % control, node_only = True)
    
    if parent_connected:
        connected = [parent_connected]
        #this code needs to be revereted in order to do children first then parent
        #if connected:
        #    connected += [parent_connected]
        #if not connected:
        #    connected = [parent_connected]
    
    if not connected:
        return False
    
    for connection in connected:
        if cmds.objExists('%s.joint1' % connection):
            joint1 = attr.get_message_input(connection, 'joint1')
            if cmds.objExists('%s.switch' % joint1):
                return connection
            
    return False


def match_to_joints(control_group, info_dict = {}, auto_key = False):
    
    if not info_dict:
        info_dict = get_important_info(control_group)
    
    controls = info_dict['controls']
    sub_controls = info_dict['sub_controls']
    joints = info_dict['joints']
    rig_type = info_dict['className']
    
    found = []
    
    if rig_type.find('Fk') > -1:
        util.show('Match Fk to Ik')
        for inc in range(0, len(controls)):
            
            control = controls[inc]
            sub_control = sub_controls[inc]
            joint = joints[inc]
            
            if sub_control:
                space.orig_matrix_match(sub_control, joint)
                found.append(sub_control)
            
            space.orig_matrix_match(control, joint)
            found.append(control)
    
    if rig_type.find('IkAppendageRig') > -1:
        util.show('Match Ik to Fk')
        
        for inc in range(0, len(controls)):
            
            control = controls[inc]
            sub_control = sub_controls[inc]
            joint = joints[inc]
            
            space.orig_matrix_match(control, joint)
            found.append(control)
            
            if sub_control:
                space.zero_out_transform_channels(sub_control)
                found.append(sub_control)
    
            if cmds.objExists('%s.autoTwist' % control):
                cmds.setAttr('%s.autoTwist' % control, 0)
    
    if auto_key and found:
        cmds.setKeyframe(found, attribute = ['translateX','translateY','translateZ','rotateX','rotateY','rotateZ','scaleX','scaleY','scaleZ'])
        cmds.select(found)
    
def match_switch_rigs(control_group, auto_key = False):
    
    info_dict = get_important_info(control_group)
    
    joints = info_dict['joints']
    if not joints:
        return
    
    switch = '%s.switch' % joints[0]
    switch = attr.search_for_open_input(switch)
        
    switch_value = cmds.getAttr(switch)
    
    rig1 = attr.get_message_input(joints[0], 'rig1')
    rig2 = attr.get_message_input(joints[0], 'rig2')
    
    if rig1 == control_group:
        rig1_info = info_dict
        rig2_info = get_important_info(rig2)
    else:
        rig1_info = get_important_info(rig1)
        rig2_info = info_dict
        
    if switch_value < 0.1:
        
        match_to_joints(rig2, rig2_info, auto_key)
        cmds.setAttr(switch, 1)
        if auto_key:
            cmds.setKeyframe(switch)
    
    if switch_value > 0.9:
                
        match_to_joints(rig1, rig1_info, auto_key)
        cmds.setAttr(switch, 0)
        if auto_key:
            cmds.setKeyframe(switch)

def match_switch_rigs_over_time(control_group, start_frame, end_frame):
    """
    this will switch to the control group supplied
    if the control_group is rig1 than the switch will be set to rig2 before the match happens.
    """
    
    if start_frame == None:
        return
    
    info_dict = get_important_info(control_group)
    joints = info_dict['joints']
    if not joints:
        return
    
    switch = '%s.switch' % joints[0]
    
    switch = attr.search_for_open_input(switch)
    
    rig1 = attr.get_message_input(joints[0], 'rig1')
    rig2 = attr.get_message_input(joints[0], 'rig2')
    
    current_switch = cmds.getAttr(switch)
    
    if current_switch == 0:
        control_group = rig2
    else:
        control_group = rig1
    
    if rig1 == control_group:
        switch_value = 1
    if rig2 == control_group:
        switch_value = 0
    
    frames = end_frame - start_frame + 1
    current_frame = start_frame
    
    for _ in range(0,frames):
        cmds.currentTime(current_frame)
        cmds.setAttr(switch, switch_value)
        match_switch_rigs(control_group, auto_key = True)
        cmds.setKeyframe(switch)
        current_frame += 1

def get_rigs_from_control_group(control_group):
    
    info_dict = get_important_info(control_group)
    
    joints = info_dict['joints']
    if not joints:
        return
    
    rig1 = attr.get_message_input(joints[0], 'rig1')
    rig2 = attr.get_message_input(joints[0], 'rig2')
    
    return rig1, rig2

def get_rigs_from_control(control):
    
    control_group = get_control_group_with_switch(control)
    
    return get_rigs_from_control_group(control_group)
    
    
def match_switch_rigs_from_control(control, auto_key = False):
    
    group = get_control_group_with_switch(control)
    match_switch_rigs(group, auto_key)

def set_switch_parent(controls, parent_switch):
    """
    Args:
        parent_switch (str): The name of a control group that has a switch (the control group has a switch when its 1 of 2 rigs are on 1 joint chain)
    """
    
    controls = util.convert_to_sequence(controls)
    for control in controls:
        attr.connect_message(parent_switch, control, 'switchParent')


def setup_zip_fade(left_zip_attr, right_zip_attr, fade_attributes, description = 'zip'):
    """
    This may be removed in the future.  This attempts to add zip attribute.  Zip needs to be setup with constraint with weight between source and midpoint.
    """
    for side in 'LR':
        
        if side == 'L':
            node_and_attr = left_zip_attr
            
        if side == 'R':
            node_and_attr = right_zip_attr
        
        if not cmds.objExists(node_and_attr):
            node, attribute = attr.get_node_and_attribute(node_and_attr)
            cmds.addAttr(node, ln = attribute, min = 0, max = 10, k = True)
        
        count = len(fade_attributes)
        
        time_offset = 1.0/(count) 
        if side == 'L':
            time_accum = 0
        if side == 'R':
            time_accum = 1-time_offset
        
        for inc in range(0, count):
            
            target_attr = fade_attributes[inc]
            
            input_node = attr.get_attribute_input(target_attr, node_only = True)
            plus_node = None
            
            if cmds.nodeType(input_node) == 'clamp':
                input_node = attr.get_attribute_input('%s.inputR' % input_node, node_only = True)
                if cmds.nodeType(input_node) == 'plusMinusAverage':
                    plus_node = input_node
                 
            else:
                plus_node = cmds.createNode('plusMinusAverage', n = '%sPlus_%s_%s' % (description, inc+1, side))
                
                zip_clamp = cmds.createNode('clamp',n = '%sClamp_%s_%s' % (description, inc+1, side))
                cmds.setAttr('%s.maxR' % zip_clamp, 1)
                
                cmds.connectAttr('%s.output1D' % plus_node, '%s.inputR' % zip_clamp)
                cmds.connectAttr('%s.outputR' % zip_clamp, target_attr)
            
            slot = attr.get_available_slot('%s.input1D' % plus_node)
            
            target_attr = '%s.input1D[%s]' % (plus_node, slot)
            
            fade_time = util_math.easeInSine(time_accum+time_offset)
            
            log.debug( side, '   ', inc, description, '   ----  ', time_accum, fade_time )
            
            anim.quick_driven_key(node_and_attr, target_attr, [time_accum,(fade_time)], [0,1], tangent_type = 'linear')
            
            if side == 'L':
                time_accum += time_offset
            if side == 'R':
                time_accum -= time_offset
                

def create_joint_sharpen(joint, rotate_axis = 'Z', scale_axis = 'X', offset_axis = 'Y', offset_amount = 1, invert = False, name = None):
    """
    Creates a joint section 
    """
    
    invert_value = 1
    
    if invert:
        invert_value = -1
        offset_amount *= invert_value
    
    if not name:
        name = 'joint_sharpen'
    
    cmds.select(cl = True)
    sharp_joint = cmds.joint(n = core.inc_name(name))
    
    children = cmds.listRelatives(joint, type = 'joint')
    child = children[0]
    
    if not children:
        util.warning('Create joint sharpen needs %s to have a child that is a joint' % joint)
    
    space.MatchSpace(child, sharp_joint).translation_rotation()
    cmds.makeIdentity(sharp_joint, apply = True, r = True)
    
    radius = cmds.getAttr('%s.radius' % joint)
    radius_offset = radius * .1
    cmds.setAttr('%s.radius' % sharp_joint, radius_offset)
    
    cmds.parent(sharp_joint, joint)
    
    offset_amount_neg = 1
    
    if offset_axis.startswith('-'):
        offset_axis = offset_axis[1:]
        offset_amount_neg = -1
        
    
    cmds.setAttr('%s.translate%s' % (sharp_joint, offset_axis), offset_amount * offset_amount_neg)
    
    rotate = 90
    
    if rotate_axis.startswith('-'):
        rotate = -90
        rotate_axis = rotate_axis[1:]
    
    
        
    
    plus = cmds.createNode('plusMinusAverage', n = 'plus_' + sharp_joint)
    
    cmds.setAttr('%s.input3D[0].input3D%s' % (plus,offset_axis.lower()), offset_amount * offset_amount_neg )
    
    cmds.connectAttr('%s.translateX' % child, '%s.input3D[1].input3Dx' % plus)
    cmds.connectAttr('%s.translateY' % child, '%s.input3D[1].input3Dy' % plus)
    cmds.connectAttr('%s.translateZ' % child, '%s.input3D[1].input3Dz' % plus)
    
    cmds.connectAttr('%s.output3Dx' % plus, '%s.translateX' % sharp_joint)
    cmds.connectAttr('%s.output3Dy' % plus, '%s.translateY' % sharp_joint)
    cmds.connectAttr('%s.output3Dz' % plus, '%s.translateZ' % sharp_joint)
    
    translate_input = '%s.input3D[2].input3D%s' % (plus, scale_axis.lower())
    
    anim.quick_driven_key('%s.rotate%s' % (child, rotate_axis), '%s.input3D[2].input3D%s' % (plus, scale_axis.lower()),
                            [-1*rotate, 0, rotate], [-1*invert_value*offset_amount_neg,0, 1*invert_value*offset_amount_neg])
    anim.quick_driven_key('%s.rotate%s' % (child, rotate_axis), '%s.scale%s' % (sharp_joint, scale_axis),
                            [-1*rotate, 0, rotate], [.5, 1, .5])
    
    cmds.setAttr('%s.segmentScaleCompensate' % sharp_joint, 0)
    mult1 = attr.insert_multiply(translate_input, 1)
    #mult2 = attr.insert_multiply('%s.scale%s' % (sharp_joint, scale_axis), 1)
    
    cmds.addAttr(sharp_joint, ln = 'push', k = True, dv = 1)
    cmds.addAttr(sharp_joint, ln = 'sharpenBulge', k = True, dv = 1)
    
    cmds.connectAttr('%s.push' % sharp_joint, '%s.input2X' % mult1)
    #cmds.connectAttr('%s.sharpenBulge' % sharp_joint, '%s.input2X' % mult2)    
    
    return sharp_joint

def get_controls_not_in_control_set(top_group, control_set = None):
    
    
    if not control_set:
        control_set = 'set_controls'
    
    
    
    potential_controls = get_potential_controls(top_group)
    
    if not cmds.objExists(control_set):
        return potential_controls
    
    set_controls = core.get_set_children(control_set)
    
    
    if not set_controls:
        return potential_controls
    
    if not potential_controls:
        return
    
    set_controls = set(set_controls)
    potential_controls = set(potential_controls)
    
    potential_controls.difference_update(set_controls)
    
    potential_controls = list(potential_controls)
    potential_controls.sort()
    
    return potential_controls

def get_potential_top_control(top_group):
    
    util.show('Getting controls')
    controls = get_potential_controls(top_group)
    
    found = []
    util.show('Finding controls without a parent control')
    for control in controls:
        
        long_name = cmds.ls(control, l = True)[0]
        
        has_parent = False
        
        for other_control in controls:
            if control == other_control:
                continue
            
            other_long_name = cmds.ls(other_control, l = True)[0]
            
            if long_name.find(other_long_name) > -1:
                has_parent = True
                break
        
        if not has_parent:
            found.append(control)
    
    if len(found) == 1:
        return found
    
    found2 = []
    util.show('Finding controls without a constraint')
    
    for control in found:
        
        parent = cmds.listRelatives(control, p = True, f = True)
        if parent:
            parent = parent[0]
        
        has_transform_connection = False
        last_parent = parent
        while parent:
            
            
            for attribute in ['translate', 'rotate']:
                
                if attr.get_attribute_input(parent + '.' + attribute, node_only = True):
                    has_transform_connection = True
                    break
                
                for axis in 'XYZ':        
                    attribute_to_test = '%s%s' % (attribute, axis)
                    
                    if attr.get_attribute_input(parent + '.' + attribute_to_test, node_only = True):
                        has_transform_connection = True
                        break
                
                if has_transform_connection:
                    break
            
            if has_transform_connection:
                break            
            
            new_parent = cmds.listRelatives(last_parent, p = True)
            last_parent = parent
            parent = new_parent
            
            if parent:
                parent = parent[0]
        
        if not has_transform_connection:
            found2.append(control)
        
    if not found2:
        return found[0]
    return found2[0]

def get_potential_controls(top_group, namespace = None):
    
    if not cmds.objExists(top_group):
        return
    
    if not namespace:
        namespace = core.get_namespace(top_group)
    
    rels = cmds.listRelatives(top_group, type = 'transform', ad = True, f = True)
    rels.append(top_group)
    
    rel_count = {}
    
    for rel in rels:
        count = rel.count('|')
        
        if not count in rel_count:
            rel_count[count] = []
        
        rel_count[count].append(rel)
    
    counts = list(rel_count.keys())
    counts.sort()
    
    rels = []
    for count in counts:
        rel_list = rel_count[count]
        rel_list.reverse
        rels += rel_list
    
    found = []
    
    
    for rel in rels:
        
        passed = True

        good_shape = is_control_shape_good(rel)
        if not good_shape:
            passed = False
            continue
        
        vis_attr = '%s.visibility' % rel
        
        if not cmds.getAttr(vis_attr):
            if not cmds.listConnections(vis_attr, s = True, d = False, p = True):
                passed = False
                continue
        
        attrs = cmds.listAttr(rel, k = True)
        if not attrs:
            passed = False
            continue
        
        if attrs == [u'visibility']:
            passed = False
            continue
        
        has_channel = False
        
        for attr in attrs:
            if attr == 'visibility':
                continue
            full_name = '%s.%s' % (rel, attr)
            if not cmds.objExists(full_name):
                continue
            if not cmds.getAttr(full_name, l = True) and not cmds.listConnections(full_name, s = True, d = False, p = True):
                has_channel = True
                break
        
        if not has_channel:
            passed = False
            continue
        
        parent_invisible = core.is_parent_hidden(rel)
        
        if parent_invisible:
            passed = False
            continue
        
        if passed:
            found.append(rel)
    
    return found

        


def is_control_shape_good(control):
    shapes = cmds.listRelatives(control, type = 'shape', f = True)
    
    if not shapes:
        return False
    
    possible_control_shape_types = ['mesh', 'nurbsCurve', 'nurbsSurface', 'locator']
    
    passed = True
    
    for shape in shapes:
        this_node_type = cmds.nodeType(shape)
        
        if not this_node_type in possible_control_shape_types:
            passed = False
            break
        
    return passed

def create_matejczyk_compression_hinge(two_rig_joints, three_guide_joints, description, translate_limit = 10):
    """
    If you were connecting this setup to a rig, using the example of an arm rig
    two_rig joints would be the arm and the elbow joints.
    three_guide joints would be a guide for the arm, elbow and wrist.
    These would be offset from the rig joints but arm and wrist guides would be close to the elbow.
    The guide joints need to aim at each other. 
    
    
    """
    
    if not space.is_rotate_default(three_guide_joints[1]):
        util.warning('Please zero out the rotates on %s before creating compression hinge' % three_guide_joints[1])
        return
    
    if not space.is_rotate_default(two_rig_joints[1]):
        util.warning('Please zero out the rotates on %s before creating compression hinge' % three_guide_joints[1])
        return
    
    orig_rot = cmds.getAttr('%s.jointOrient' % two_rig_joints[1])[0]
    
    cmds.setAttr('%s.jointOrient' % three_guide_joints[1] , *[0,0,0])
    cmds.setAttr('%s.jointOrient' % two_rig_joints[1] , *[0,0,0])
    
    xform_group = cmds.group(em = True, n = 'xform_%s' % description)
    top_group = cmds.group(em = True, n = 'offset_%s' % description)
    cmds.parent(top_group, xform_group)
    
    space.MatchSpace(three_guide_joints[1], xform_group).translation_rotation()
    space.MatchSpace(three_guide_joints[1], top_group).translation_rotation()
    
    loc_mid = cmds.spaceLocator(n = 'locator_mid_%s' % description)[0]
    loc_btm = cmds.spaceLocator(n = 'locator_btm_%s' % description)[0]
    
    cmds.parent(loc_mid, xform_group)
    cmds.parent(loc_btm, loc_mid)
    
    space.MatchSpace(three_guide_joints[1], loc_mid).translation_rotation()
    space.MatchSpace(three_guide_joints[2], loc_btm).translation_rotation()
    
    vecProd1 = cmds.createNode('vectorProduct', n = 'vectorProduct_positionNormal_%s' % description)
    vecProd2 = cmds.createNode('vectorProduct', n = 'vectorProduct_normal_%s' % description)
    
    cmds.connectAttr('%s.translateX' % loc_mid, '%s.input1X' % vecProd1)
    cmds.connectAttr('%s.translateY' % loc_mid, '%s.input1Y' % vecProd1)
    cmds.connectAttr('%s.translateZ' % loc_mid, '%s.input1Z' % vecProd1)
    
    cmds.connectAttr('%s.translateX' % loc_btm, '%s.input2X' % vecProd1)
    cmds.connectAttr('%s.translateY' % loc_btm, '%s.input2Y' % vecProd1)
    cmds.connectAttr('%s.translateZ' % loc_btm, '%s.input2Z' % vecProd1)
    
    vec_btm = cmds.getAttr('%s.translate' % loc_btm)[0]
    
    cmds.setAttr('%s.input1' % vecProd2, *vec_btm)
    cmds.connectAttr('%s.translateX' % loc_btm, '%s.input2X' % vecProd2)
    cmds.connectAttr('%s.translateY' % loc_btm, '%s.input2Y' % vecProd2)
    cmds.connectAttr('%s.translateZ' % loc_btm, '%s.input2Z' % vecProd2)
    
    mult_int = cmds.createNode('multiplyDivide', n = 'multiplyDivide_intersection_%s' % description)
    cmds.setAttr('%s.operation' % mult_int, 2)
    
    mult_dist = cmds.createNode('multiplyDivide', n = 'multiplyDivide_distance_%s' % description)
    
    cmds.connectAttr('%s.outputX' % vecProd1, '%s.input1X' % mult_int)
    cmds.connectAttr('%s.outputY' % vecProd1, '%s.input1Y' % mult_int)
    cmds.connectAttr('%s.outputZ' % vecProd1, '%s.input1Z' % mult_int)
    
    cmds.connectAttr('%s.outputX' % vecProd2, '%s.input2X' % mult_int)
    cmds.connectAttr('%s.outputY' % vecProd2, '%s.input2Y' % mult_int)
    cmds.connectAttr('%s.outputZ' % vecProd2, '%s.input2Z' % mult_int)
    
    cmds.setAttr('%s.input1' % mult_dist, *vec_btm)
    cmds.connectAttr('%s.outputX' % mult_int, '%s.input2X' % mult_dist)
    cmds.connectAttr('%s.outputY' % mult_int, '%s.input2Y' % mult_dist)
    cmds.connectAttr('%s.outputZ' % mult_int, '%s.input2Z' % mult_dist)
    
    cmds.connectAttr('%s.outputX' % mult_dist,'%s.translateX' % top_group)
    cmds.connectAttr('%s.outputY' % mult_dist,'%s.translateY' % top_group)
    cmds.connectAttr('%s.outputZ' % mult_dist,'%s.translateZ' % top_group)
    
    cmds.orientConstraint(two_rig_joints[1], three_guide_joints[1])
    
    cmds.setAttr('%s.jointOrient' % two_rig_joints[1] , *orig_rot)
    
    cmds.parentConstraint(two_rig_joints, loc_mid, mo = True, sr = ['x','y','z'])
    cmds.parentConstraint(two_rig_joints, loc_btm, mo = True, sr = ['x','y','z'])
    
    cmds.parentConstraint(top_group, three_guide_joints[0], mo = True)
    cmds.parentConstraint(two_rig_joints[0], xform_group, mo = True)
    
     
    
    cmds.transformLimits(top_group, tx=(-translate_limit, translate_limit), ty=(-translate_limit, translate_limit), tz=(-translate_limit, translate_limit) )
    cmds.transformLimits(top_group, etx=(True, True), ety=(True, True), etz=(True, True ) )
    
    return xform_group

def create_compression_joint(joint, end_parent, description, point_constraint = False):
    """
    joint need to be a joint with a child joint. Child joint is automatically found.
    """
    
    end_joint = cmds.listRelatives(joint, c = True, type = 'joint')
    parent_transform = cmds.listRelatives(joint, p = True)
    
    if end_joint:
        end_joint = end_joint[0]
    
    handle = space.IkHandle(description)
    handle.set_start_joint(joint)
    handle.set_end_joint(end_joint)
    handle.set_solver(handle.solver_sc)
    handle.set_full_name(core.inc_name('ik_%s' % description))
    ik_handle = handle.create()
    
    
    
    group = cmds.group(em = True, n = core.inc_name('setup_%s' % description))
    loc = cmds.spaceLocator(n = core.inc_name('locator_%s' % description))[0]
    loc_end = cmds.spaceLocator(n = core.inc_name('locatorEnd_%s' % description))[0]
    space.MatchSpace(joint, loc).translation_rotation()
    space.MatchSpace(end_joint, loc_end).translation_rotation()
    
    cmds.parent(loc, loc_end, group)
    cmds.parent(ik_handle, loc)
    
    cmds.pointConstraint(parent_transform, loc, mo = True)
    cmds.orientConstraint(parent_transform, loc, mo = True)
    if not point_constraint:
        cmds.parentConstraint(end_parent, loc_end, mo = True)
    else:
        cmds.pointConstraint(end_parent, loc_end, mo = True)
    cmds.pointConstraint(loc_end, ik_handle, mo = True)
    
    distance = cmds.createNode('distanceBetween', n = core.inc_name('distance_%s' % description))
    
    cmds.connectAttr('%s.worldMatrix' % loc, '%s.inMatrix1' % distance)
    cmds.connectAttr('%s.worldMatrix' % loc_end, '%s.inMatrix2' % distance)
    
    axis = space.get_axis_letter_aimed_at_child(joint)
    
    if axis:
        if len(axis) == 2:
            axis = axis[1]
    
    mult = cmds.createNode('multiplyDivide', n = core.inc_name('mult_%s' % description))
    
    mult_scale = cmds.createNode('multiplyDivide', n = core.inc_name('multiplyDivide_scaleOffset_%s' % description))
    
    #cmds.connectAttr('%s.distance' % distance, '%s.input1X' % mult_scale)
    
    distance_value = cmds.getAttr('%s.distance' % distance)
    cmds.connectAttr('%s.distance' % distance, '%s.input1X' % mult)
    cmds.connectAttr('%s.outputX' % mult_scale, '%s.input2X' % mult)
    cmds.setAttr('%s.input1X' % mult_scale, distance_value)
    #cmds.setAttr('%s.input2X' % mult, distance_value)
    cmds.setAttr('%s.operation' % mult, 2)
    
    scale_condition = cmds.createNode('condition', n = core.inc_name('scaleCondition_%s' % description))
    cmds.connectAttr('%s.outputX' % mult, '%s.firstTerm' % scale_condition)
    cmds.setAttr('%s.secondTerm' % scale_condition, 1)
    
    neg_scale_blend = cmds.createNode('blendTwoAttr', n = core.inc_name('negScaleBlend_%s' % description))
    pos_scale_blend = cmds.createNode('blendTwoAttr', n = core.inc_name('poseScaleBlend_%s' % description))

    cmds.setAttr('%s.input[0]' % neg_scale_blend, 1)
    cmds.connectAttr('%s.outputX' % mult, '%s.input[1]' % neg_scale_blend)

    cmds.setAttr('%s.input[0]' % pos_scale_blend, 1)
    cmds.connectAttr('%s.outputX' % mult, '%s.input[1]' % pos_scale_blend)
    
    cmds.connectAttr('%s.output' % neg_scale_blend, '%s.colorIfTrueR' % scale_condition)
    cmds.connectAttr('%s.output' % pos_scale_blend, '%s.colorIfFalseR' % scale_condition)
    
    cmds.connectAttr('%s.outColorR' % scale_condition, '%s.scale%s' % (joint, axis))
    
    if not cmds.objExists('%s.compression' % joint):
        cmds.addAttr(joint, ln = 'compression', min = 0, max = 1, dv = 1, k = True)
    if not cmds.objExists('%s.stretch' % joint):
        cmds.addAttr(joint, ln = 'stretch', min = 0, max = 1, dv = 1, k = True)
    
    cmds.connectAttr('%s.stretch' % joint, '%s.attributesBlender' % neg_scale_blend)
    cmds.connectAttr('%s.compression' % joint, '%s.attributesBlender' % pos_scale_blend)
    
    cmds.hide(group)
    
    return group
    