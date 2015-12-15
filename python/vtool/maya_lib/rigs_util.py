# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

import string

#import util
import api
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

class Control(object):
    """
    Convenience for creating controls
    
    Args
        name (str): The name of a control that exists or that should be created.
    """
    
    def __init__(self, name):
        
        self.control = name
        self.curve_type = None
        
        if not cmds.objExists(self.control):
            self._create()
            
        self.shapes = core.get_shapes(self.control)
        
        if not self.shapes:
            vtool.util.warning('%s has no shapes' % self.control)
            
    def _create(self):
        
        self.control = cmds.circle(ch = False, n = self.control, normal = [1,0,0])[0]
        
        if self.curve_type:
            self.set_curve_type(self.curve_type)
        
    def _get_components(self):
        
        self.shapes = core.get_shapes(self.control)
        
        return core.get_components_from_shapes(self.shapes)
        
    def set_curve_type(self, type_name):
        """
        Set the curve type. The type of shape the curve should have.
        
        Args
        
            type_name (str): eg. 'circle', 'square', 'cube', 'pin_round' 
        """
        
        curve_data = curve.CurveDataInfo()
        curve_data.set_active_library('default_curves')
        curve_data.set_shape_to_curve(self.control, type_name)
        
        self.shapes = core.get_shapes(self.control)
    
    def set_to_joint(self, joint = None, scale_compensate = False):
        """
        Set the control to have a joint as its main transform type.
        
        Args
            joint (str): The name of a joint to use. If none joint will be created automatically.
            scale_compensate (bool): Whether to connect scale of parent to inverseScale of joint. 
            This causes the group above the joint to be able to change scale value without affecting the control's look. 
        """
        
        
        cmds.select(cl = True)
        name = self.get()
        
        joint_given = True
        
        if not joint:
            joint = cmds.joint()
            
            cmds.delete(cmds.parentConstraint(name, joint))
            cmds.delete(cmds.scaleConstraint(name, joint))
            #space.MatchSpace(name, joint).translation_rotation()
            joint_given = False
        
        shapes = self.shapes
        
        for shape in shapes:
            cmds.parent(shape, joint, r = True, s = True)
        
        if not joint_given:
            
            parent = cmds.listRelatives(name, p = True)
            
            if parent:
                cmds.parent(joint, parent)
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
        
        Args
            x (float)
            y (float)
            z (float)
        """
        components = self._get_components()
        
        if components:
            cmds.move(x,y,z, components, relative = True, os = True)
        
    def rotate_shape(self, x,y,z):
        """
        Rotate the shape curve cvs in object space
        
        Args
            x (float)
            y (float)
            z (float)
        """
        components = self._get_components()
        
        if components:
            cmds.rotate(x,y,z, components, relative = True)
            
    def scale_shape(self, x,y,z):
        """
        Scale the shape curve cvs relative to the current scale.
        
        Args
            x (float)
            y (float)
            z (float)
        """
        components = self._get_components()
        
        pivot = cmds.xform( self.control, q = True, rp = True, ws = True)
        
        if components:
            cmds.scale(x,y,z, components, p = pivot, r = True)

    def color(self, value):
        """
        Set the color of the curve.
        
        Args
            value (int): This corresponds to Maya's color override value.
        """
        shapes = core.get_shapes(self.control)
        
        attr.set_color(shapes, value)
    
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
    
    def hide_attributes(self, attributes):
        """
        Lock and hide the given attributes on the control.
        
        Args
            
            attributes (list): List of attributes, eg. ['translateX', 'translateY']
        """
        attr.hide_attributes(self.control, attributes)
        
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
        attr.hide_attributes(self.control, ['rotateX',
                                     'rotateY',
                                     'rotateZ'])
        
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
        
    def rotate_order(self, xyz_order_string):
        """
        Set the rotate order on a control.
        """
        cmds.setAttr('%s.rotateOrder' % self.node, xyz_order_string)
    
    def color_respect_side(self, sub = False, center_tolerance = 0.001):
        """
        Look at the position of a control, and color it according to its side on left, right or center.
        
        Args
            sub (bool): Wether to set the color to sub colors.
            center_tolerance (float): The distance the control can be from the center before its considered left or right.
            
        Return
            str: The side the control is on in a letter. Can be 'L','R' or 'C'
        """
        position = cmds.xform(self.control, q = True, ws = True, t = True)
        
        if position[0] > 0:
            color_value = attr.get_color_of_side('L', sub)
            side = 'L'

        if position[0] < 0:
            color_value = attr.get_color_of_side('R', sub)
            side = 'R'
            
        if position[0] < center_tolerance and position[0] > center_tolerance*-1:
            color_value = attr.get_color_of_side('C', sub)
            side = 'C'
            
        self.color(color_value)
        
        return side
            
    def get(self):
        """
        Return
            str: The name of the control.
        """
        return self.control
    
    def get_xform_group(self, name):
        """
        This returns an xform group above the control.
        
        Args
            name (str): The prefix name supplied when creating the xform group.  Usually xform or driver.
            
        """
        
        return space.get_xform_group(self.control, name)
    
    def create_xform(self):
        """
        Create an xform above the control.
        
        Return
            str: The name of the xform group.
        """
        xform = space.create_xform_group(self.control)
        
        return xform
        
    def rename(self, new_name):
        """
        Give the control a new name.
        
        Args
            
            name (str): The new name.
        """
        new_name = cmds.rename(self.control, core.inc_name(new_name))
        self.control = new_name

    def delete_shapes(self):
        """
        Delete the shapes beneath the control.
        """
        self.shapes = core.get_shapes(self.control)
        
        cmds.delete(self.shapes)
        self.shapes = []
        
class StoreControlData(attr.StoreData):
    
    def __init__(self, node = None):
        super(StoreControlData, self).__init__(node)
        
        self.controls = []
        
        self.side_replace = ['_L', '_R', 'end']
        
    def _get_single_control_data(self, control):
        
        if not control:
            return
    
        attributes = cmds.listAttr(control, k = True)
            
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
            
        
    def _find_other_side(self, control):
        
        pattern_string, replace_string, position_string = self.side_replace
            
        start, end = vtool.util.find_special(pattern_string, control, position_string)
        
        if start == None:
            return
        
        other_control = vtool.util.replace_string(control, replace_string, start, end)
            
        return other_control
        
    def remove_data(self, control):
        
        data = self.get_data()
        
        if data:
            
            data = eval(data)
        

        if data.has_key(control):
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
    
    def set_control_data_attribute(self, control, data = None):
        
        if not data:
            data = self._get_single_control_data(control)
        
        if data:
            
            self._set_control_data_in_dict(control, data)
        if not data:
            vtool.util.warning('Error setting data for %s' % control )
        
    
        
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
        
        
        for control in data:
            
            if cmds.objExists('%s.POSE' % control):
                continue
       
            attribute_data = data[control]
            self._set_control_data(control, attribute_data)
            
        return data
            
    def eval_mirror_data(self):  
        data_list = self.eval_data()
            
        for control in data_list:
            
            other_control = self._find_other_side(control)
            
            if not other_control or cmds.objExists(other_control):
                continue
            
            if cmds.objExists('%s.ikFk' % control):

                value = cmds.getAttr('%s.ikFk' % control)
                other_value = cmds.getAttr('%s.ikFk' % other_control)
                cmds.setAttr('%s.ikFk' % control, other_value)
                cmds.setAttr('%s.ikFk' % other_control, value)
            
            if not self._has_transform_value(control):
                continue 
            
            #if not control.endswith('_L'):
            #    continue               
            
            temp_group = cmds.duplicate(control, n = 'temp_%s' % control, po = True)[0]
            
            space.MatchSpace(control, temp_group).translation_rotation()
            parent_group = cmds.group(em = True)
            cmds.parent(temp_group, parent_group)
            
            cmds.setAttr('%s.scaleX' % parent_group, -1)
            
            orig_value_x = cmds.getAttr('%s.rotateX' % control)
            orig_value_y = cmds.getAttr('%s.rotateY' % control)
            orig_value_z = cmds.getAttr('%s.rotateZ' % control)
            
            attr.zero_xform_channels(control)
            
            const1 = cmds.pointConstraint(temp_group, other_control)[0]
            const2 = cmds.orientConstraint(temp_group, other_control)[0]
            
            value_x = cmds.getAttr('%s.rotateX' % other_control)
            value_y = cmds.getAttr('%s.rotateY' % other_control)
            value_z = cmds.getAttr('%s.rotateZ' % other_control)
            
            cmds.delete([const1, const2])
            
            if abs(value_x) - abs(orig_value_x) > 0.01 or abs(value_y) - abs(orig_value_y) > 0.01 or abs(value_z) - abs(orig_value_z) > 0.01:
                
                cmds.setAttr('%s.rotateX' % other_control, orig_value_x)
                cmds.setAttr('%s.rotateY' % other_control, -1*orig_value_y)
                cmds.setAttr('%s.rotateZ' % other_control, -1*orig_value_z)
                            
    def eval_multi_transform_data(self, data_list):
        
        controls = {}
        
        for data in data_list:
            
            last_temp_group = None
            
            for control in data:
                
                if cmds.objExists('%s.POSE' % control):
                    continue
                
                if not self._has_transform_value(control):
                    continue
                
                if not controls.has_key(control):
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
        self.add_dampen = False
        self.stretch_offsets = []
        self.distance_offset = None
        self.scale_axis = 'X'
        self.name = 'stretch'
        self.simple = False
        self.per_joint_stretch = True
        self.vector = False
        self.extra_joint = None
        self.damp_name = 'dampen'
    
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
            offset_variable.set_value(1)
            offset_variable.set_min_value(0.1)
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
        
        title = attr.MayaEnumVariable('STRETCH')
        title.create(self.attribute_node)
        title.set_locked(True)
        
        stretch_on_off_var = attr.MayaNumberVariable('autoStretch')
        stretch_on_off_var.set_node(self.attribute_node)
        stretch_on_off_var.set_variable_type(stretch_on_off_var.TYPE_DOUBLE)
        stretch_on_off_var.set_min_value(0)
        stretch_on_off_var.set_max_value(1)
        
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
            
            stretch_offset.set_value(1)
            stretch_offset.set_min_value(0.1)
            
            stretch_offset.connect_out('%s.offset%s' % (stretch_offsets[inc], inc+1) )
    
    def _create_other_distance_offset(self, distance_offset):
        
        multiply = attr.MultiplyDivideNode('distanceOffset_%s' % self.name)
        
        plug = '%s.input2X' % distance_offset
        
        input_to_plug = attr.get_attribute_input('%s.input2X' % distance_offset)
        
        multiply.input1X_in(input_to_plug)
        multiply.input2X_in(self.distance_offset_attribute)
        multiply.outputX_out(plug)
        
    def _create_dampen(self, distance_node, plugs):
        
        min_length = space.get_distance(self.joints[0], self.joints[-1])
        #max_length = self._get_length()

        dampen = attr.MayaNumberVariable(self.damp_name)
        dampen.set_node(self.attribute_node)
        dampen.set_variable_type(dampen.TYPE_DOUBLE)
        dampen.set_min_value(0)
        dampen.set_max_value(1)
        dampen.create()
        
        remap = cmds.createNode( "remapValue" , n = "%s_remapValue_%s" % (self.damp_name, self.name) )
        cmds.setAttr("%s.value[2].value_Position" % remap, 0.4);
        cmds.setAttr("%s.value[2].value_FloatValue" % remap, 0.666);
        cmds.setAttr("%s.value[2].value_Interp" % remap, 3)
    
        cmds.setAttr("%s.value[3].value_Position" % remap, 0.7);
        cmds.setAttr("%s.value[3].value_FloatValue" % remap, 0.9166);
        cmds.setAttr("%s.value[3].value_Interp" % remap, 1)
    
        multi = cmds.createNode ( "multiplyDivide", n = "%s_offset_%s" % (self.damp_name, self.name))
        add_double = cmds.createNode( "addDoubleLinear", n = "%s_addDouble_%s" % (self.damp_name, self.name))

        dampen.connect_out('%s.input2X' % multi)
        
        cmds.connectAttr('%s.outputX' % self.orig_distance, '%s.input1X' % multi)
        
        cmds.connectAttr("%s.outputX" % multi, "%s.input1" % add_double)
        
        cmds.connectAttr('%s.outputX' % self.orig_distance, '%s.input2' % add_double)
        
        cmds.connectAttr("%s.output" % add_double, "%s.inputMax" % remap)
    
        cmds.connectAttr('%s.outputX' % self.orig_distance, '%s.outputMax' % remap)
        
        cmds.setAttr("%s.inputMin" % remap, min_length)
        cmds.setAttr("%s.outputMin" % remap, min_length)
        
        cmds.connectAttr( "%s.distance" % distance_node, "%s.inputValue" % remap)
        
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
        self.add_dampen = bool_value
        
        if damp_name:
            self.damp_name = damp_name
    
    def set_simple(self, bool_value):
        self.simple = bool_value
    
    def set_description(self, string_value):
        self.name = '%s_%s' % (self.name, string_value)
    
    def set_per_joint_stretch(self, bool_value):
        self.per_joint_stretch = bool_value
    
    def set_extra_joint(self, joint):
        self.extra_joint = joint
    
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
                
                if self.add_dampen:
                    self._create_dampen(stretch_distance, ['%s.firstTerm' % stretch_condition,
                                                           '%s.colorIfTrueR' % stretch_condition,
                                                           '%s.color2R' % stretch_on_off,
                                                           '%s.input2X' % divide_distance])
                
            if self.distance_offset_attribute:
                self._create_other_distance_offset(distance_offset)
                
        
                
        return top_locator, btm_locator


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
    
    Args
        switch_joint (str): The name of a buffer joint with switch attribute.
    """
    def __init__(self, switch_joint):
        
        self.switch_joint = switch_joint
        
        if not cmds.objExists('%s.switch' % switch_joint):
            vtool.util.warning('%s is most like not a buffer joint with switch attribute.' % switch_joint)

        self.groups = {}
        
        weight_count = self.get_weight_count()
        
        if not weight_count:
            vtool.util.warning('%s has no weights.' % weight_count)
        
        for inc in range(0, weight_count):
            self.groups[inc] = None
        
        self.control_name = None
        self.attribute_name = 'switch'

    def get_weight_count(self):
        
        edit_constraint = space.ConstraintEditor()
        constraint = edit_constraint.get_constraint(self.switch_joint, 'parentConstraint')
        
        weight_count = edit_constraint.get_weight_count(constraint)
        
        return weight_count

    def add_groups_to_index(self, index, groups):
        """
        A switch joint is meant to switch visibility between rigs.
        By adding groups you define what their visibility is when the switch attribute changes.
        An index of 0 means the groups will be visibile when the switch is at 0, but invisible when the switch is at 1.
        
        Args
            index (int): The index on the switch. Needs to be an integer value even though switch is a float.
            groups (list): The list of groups that should be have visibility attached to the index.
        """
        
        groups = vtool.util.convert_to_sequence(groups)
        
        if not self.switch_joint or not cmds.objExists(self.switch_joint):
            vtool.util.warning('Switch joint %s does not exist' % self.switch_joint)
            return
        
        weight_count = self.get_weight_count()
        
        if weight_count < ( index + 1 ):
            vtool.util.warning('Adding groups to index %s is undefined. %s.witch does not have that many inputs.' % (index, self.switch_joint))
        
        self.groups[index] = groups
        
    def set_attribute_control(self, transform):
        """
        Set where the switch attribute should live.
        
        Args
            transform (str): The name of a transform
        """
        
        self.control_name = transform
        
    def set_attribute_name(self, attribute_name):
        """
        Set the name of the switch attribute on the attribute_control.
        
        Args
            attribute_name (str): The name for the attribute.
        """
        
        self.attribute_name = attribute_name
        
    def create(self):
        
        if self.control_name and cmds.objExists(self.control_name):
            
            weight_count = self.get_weight_count()
            
            
            var = attr.MayaNumberVariable(self.attribute_name)
               
            var.set_min_value(0)
            var.set_max_value( (weight_count - 1) ) 
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



def create_distance_scale(xform1, xform2, axis = 'X', offset = 1):
    """
    Create a stretch effect on a transform by changing the scale when the distance changes between xform1 and xform2.
    
    Args
        xform1 (str): The name of a transform.
        xform2 (str): The name of a transform.
        axis (str): "X", "Y", "Z" The axis to attach the stretch effect to.
        offset (float): Add an offset to the value.
        
    Return
        ([locator1, locator2]): The names of the two locators used to calculate distance.
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
    
    Args
        curve (str): The name of a curve.
        joint_count (int): The number of joints to create.
        description (str): The description to give the joints.
        attach (bool): Wether to attach the joints to the curve.
        create_controls (bool): Wether to create controls on the joints.
        
    Return
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
        
        cmds.addAttr(joint, ln = 'param', at = 'double', dv = param)
        
        if joints:
            cmds.joint(joints[-1], 
                       e = True, 
                       zso = True, 
                       oj = "xyz", 
                       sao = "yup")
        
        if attach:
            
            attach_node = geo.attach_to_curve( joint, curve, parameter = param )
            cmds.parent(joint, group)
        
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

            offset = vtool.util.fade_sine(percent)
            
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
    
    Args
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
            
            arc_value = vtool.util.fade_sine(percent)
            
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

def create_simple_spline_ik_stretch(curve, joints):
    """
    Stretch joints on curve. Joints must be attached to a spline ik. This is a much simpler setup than create_spline_ik_stretch.
    
    Args
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

        cmds.connectAttr(attribute, '%s.scaleY' % joint)
        
        percent += segment

def create_bulge_chain(joints, control, max_value = 15):
    """
    Adds scaling to a joint chain that mimics a cartoony water bulge moving along a tube.
    
    Args
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
    
    Args
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
    
    Args
        control (str): The name of a control where the spread attribute should be created.
        transforms (list): A list of transforms that should spread apart by rotation.
        name (str): The name of the attribute to create.
        axis (str): Can be 'X','Y','Z'
        invert (bool): Wether to invert the spread behavior so it can mirror.
        create_driver (bool): Wether to create a driver group above the transform.
    """
    variable = '%s.%s' % (control, name)
    
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
    
    Args
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

def get_controls():
    """
    Get the controls in a scene.
    
    It follows these rules
    
    First check if a transform starts with "CNT_"
    Second check if a transform has a an attribute named control.
    Third check if a transform has an attribute named tag and is a nurbsCurve, and that tag has a value.
    Fourth check if a transform has an attribute called curveType.
    
    If it matches any of these conditions it is considered a control.
    
    Return
        list: List of control names.
    """
    transforms = cmds.ls(type = 'transform')
    joints = cmds.ls(type = 'joint')
    
    if joints:
        transforms += joints
    
    found = []
    found_with_value = []
    
    for transform in transforms:
        if transform.startswith('CNT_'):
            found.append(transform)
            continue
                
        if cmds.objExists('%s.control' % transform):
            found.append(transform)
            continue
        
        if cmds.objExists('%s.tag' % transform):
            
            if core.has_shape_of_type(transform, 'nurbsCurve'):
                
                
                found.append(transform)
                value = cmds.getAttr('%s.tag' % transform)
                
                if value:
                    found_with_value.append(transform)
            
            continue
        
        if cmds.objExists('%s.curveType' % transform):
            found.append(transform)
            continue
    
    if found_with_value:
        found = found_with_value
        
    return found
    
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
    
    other_control = None
    
    if control.endswith('_L') or control.endswith('_R'):
                
        if control.endswith('_L'):
            other_control = control[0:-2] + '_R'
            
        if control.endswith('_R'):
            other_control = control[0:-2] + '_L'
            
    if not other_control:
        if control.startswith('L_'):
            other_control = 'R_' + control[2:]
            
        if control.startswith('R_'):
            other_control = 'L_' + control[2:]
         
    if not other_control:
                
        if control.find('lf') > -1 or control.find('rt') > -1:
            
            if control.find('lf') > -1:
                other_control = control.replace('lf', 'rt')
                
            if control.find('rt') > -1:
                other_control = control.replace('rt', 'lf') 
           
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
    selection = cmds.ls(sl = True)
    
    controls = get_controls()
    
    found = []
    
    if selection:
        for selection in selection:
            if selection in controls:
                found.append(selection)
    
    if not selection or not found:
        found = controls
    
    mirrored_controls = []
    
    for control in found:
        
        if control in mirrored_controls:
            continue
        
        other_control = mirror_control(control)
        
        mirrored_controls.append(other_control)
        

def mirror_curve(prefix):
    """
    Mirror curves in a scene if the end in _L and _R
    """
    
    curves = cmds.ls('%s*' % prefix, type = 'transform')
    
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
    
    Args
        mesh (str): A mesh skinned to process joints.
    """
    scope = cmds.ls('process_*', type = 'joint')
    
    
    progress = core.ProgressBar('process to parent %s' % mesh, len(scope))
    
    for joint in scope:
        progress.status('process to parent %s: %s' % (mesh, joint))
        
        deform.transfer_weight_from_joint_to_parent(joint, mesh)
        
        progress.inc()
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



def hook_ik_fk(control, joint, groups, attribute = 'ikFk'): 
    """
    Convenience for hooking up ik fk.
    
    Args
        control (str): The name of the control where the attribute arg should be created.
        joint (str): The joint with the switch attribute. When adding multiple rigs to one joint chain, the first joint will have a switch attribute added.
        groups (list): The ik control group name and the fk control group name.
        attribute (str): The name to give the attribute on the control. Usually 'ikFk'
    """
    if not cmds.objExists('%s.%s' % (control, attribute)): 
        cmds.addAttr(control, ln = attribute, min = 0, max = 1, dv = 0, k = True) 
      
    attribute_ikfk = '%s.%s' % (control, attribute) 
      
    cmds.connectAttr(attribute_ikfk, '%s.switch' % joint) 
      
    for inc in range(0, len(groups)): 
        attr.connect_equal_condition(attribute_ikfk, '%s.visibility' % groups[inc], inc) 

            
       
def fix_fade(target_curve, follow_fade_multiplies):
    """
    This fixes multiplyDivides so that they will multiply by a value that has them match the curve when they move.
    
    For example if eye_lid_locator is multiplyDivided in translate to move with CNT_EYELID. 
    Pass its multiplyDivide node to this function with a curve that matches the btm eye lid.
    The function will find the amount the multiplyDivide.input2X needs to move, 
    so that when CNT_EYELID moves on Y it will match the curvature of target_curve.
    
    Args
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
    
    total_distance = vtool.util.get_distance(control_position_y, control_at_curve_y)
    
    multi_count = len(multiplies)
    
    for inc in range(0, multi_count):
        multi = multiplies[inc]['node']
        driver = multiplies[inc]['target']
        
        driver_position = cmds.xform(driver, q = True, ws = True, t = True)
        driver_position_y = [0, driver_position[1], 0]
        
        
        parameter = geo.get_y_intersection(target_curve, driver_position)
        
        driver_at_curve = cmds.pointOnCurve(target_curve, parameter = parameter)
        driver_at_curve_y = [0, driver_at_curve[1], 0]
        
        driver_distance = vtool.util.get_distance(driver_position_y, driver_at_curve_y)
        
        value = (driver_distance/total_distance)
    
        cmds.setAttr('%s.input2Y' % multi, value)

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