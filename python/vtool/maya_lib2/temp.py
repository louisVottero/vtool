import string

from vtool import util

if util.is_in_maya():
    import maya.cmds as cmds
    from vtool.maya_lib import core
    from vtool.maya_lib import curve
    from vtool.maya_lib import attr    
    from vtool.maya_lib2 import space
    
from vtool import util_file




        

class ControlOld(object):
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
            vtool.util.warning('%s has no shapes' % self.control)
            
        
            
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
        color =attr.get_color(shapes[0])
        
        curve_data = curve.CurveDataInfo()
        curve_data.set_active_library('default_curves')
        curve_data.set_shape_to_curve(self.control, type_name)
        
        self.shapes = core.get_shapes(self.control)
        
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
        
        attr.set_color(shapes, value)
    
    def color_rgb(self, r=0,g=0,b=0):
        """
        Maya 2015 and above.
        Set to zero by default.
        Max value is 1.0.
        """
        
        shapes = core.get_shapes(self.control)
        
        attr.set_color_rgb(shapes, r,g,b)
        
    
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
            
        
        cmds.setAttr('%s.rotateOrder' % self.node, value)
    
    def color_respect_side(self, sub = False, center_tolerance = 0.001):
        """
        Look at the position of a control, and color it according to its side on left, right or center.
        
        Args:
            sub (bool): Wether to set the color to sub colors.
            center_tolerance (float): The distance the control can be from the center before its considered left or right.
            
        Returns:
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
    
    def create_xform(self):
        """
        Create an xform above the control.
        
        Returns:
            str: The name of the xform group.
        """
        xform = space.create_xform_group(self.control)
        
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


                
      

class RigOld(object):
    
    "Base class for rigs."
    
    side_left = 'L'
    side_right = 'R'
    side_center = 'C'
    
    def __init__(self, description, side = None):
        
        self.side = side
        
        self.joints = []
        self.buffer_joints = []
        
        cmds.refresh()
        
        self.description = description
        
        self._control_inst = None
        
        self._set_sub_control_color_only = False
        
        self._handle_side_variations()
        
        self.control_group = None
        self.setup_group = None
        
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
        self._sub_controls_with_buffer = []
        self.control_dict = {}
        
        self.sub_visibility = False
        self._connect_sub_vis_attr = None
        
        self._connect_important = True
        self._connect_important_node = None
        
        self._control_number = True
        self._custom_sets = []
        
        self._switch_parent = None
        self._pick_walk_parent = None
        
    def _post_create(self):

        cmds.addAttr(self.control_group, ln = 'className', dt = 'string')
        
        cmds.setAttr('%s.className' % self.control_group, str(self.__class__.__name__), type = 'string')

        if cmds.objExists(self.setup_group):
            
            if core.is_empty(self.setup_group):
                parent = cmds.listRelatives(self.setup_group, p = True)
                
                if not parent:
                    
                    class_name = self.__class__.__name__
                    
                    vtool.util.warning('Empty setup group in class: %s with description %s %s.' % (class_name, self.description, self.side))
        
        try:
            self._post_create_rotate_order()
        except:
            vtool.util.warning('Could add rotate order to channel box')
        
        if self._connect_important:
            #attr.connect_message(input_node, destination_node, attribute)
            
            vtool.util.show('Connect Important!')
            
            self._post_create_connect('controls', 'control')
            self._post_create_connect('_sub_controls_with_buffer', 'subControl')
            self._post_create_connect('joints', 'joint')
            self._post_create_connect('ik_handle', 'ikHandle')
            
            if self.joints:
                attr.connect_message(self.control_group, self.joints[0], 'rig1')
            
            
        self._post_add_shape_switch()
        
        self._post_store_orig_matrix('controls')
        self._post_store_orig_matrix('_sub_controls_with_buffer')
        self._post_store_orig_matrix('joints')
        
        self._post_add_to_control_set()
        self._post_connect_controller()
        self._post_connect_controls_to_switch_parent()
        
    def _post_add_shape_switch(self):

        if hasattr(self, 'create_buffer_joints'):
            
            if not self.create_buffer_joints:
                return
        else:
            return
        
        if not hasattr(self, '_switch_shape_attribute_name'):
            return
        
        if not self._switch_shape_attribute_name:
            return
        
        shapes = core.get_shapes(self.joints[0], shape_type = 'locator', no_intermediate = True)
        
        name = self._switch_shape_attribute_name
        node_name = 'switch_setting'
        if self._switch_shape_node_name:
            node_name = self._switch_shape_node_name
        if not self._switch_shape_node_name:
            if self._switch_shape_attribute_name:
                node_name = self._switch_shape_attribute_name 
        
        if cmds.objExists(node_name) and core.is_a_shape(node_name):
            shapes = [node_name]
        
        if not shapes:
            locator = cmds.spaceLocator()
            shapes = core.get_shapes(locator, shape_type = 'locator', no_intermediate = True)
            
            cmds.setAttr('%s.localScaleX' % shapes[0], 0)
            cmds.setAttr('%s.localScaleY' % shapes[0], 0)
            cmds.setAttr('%s.localScaleZ' % shapes[0], 0)
            
            attr.hide_attributes(shapes[0], ['localPosition', 'localScale'])
            shapes = cmds.parent(shapes[0],self.joints[0], r = True, s = True)
            cmds.delete(locator)
            shapes[0] = cmds.rename(shapes[0], core.inc_name(node_name))
        
        joint_shape = shapes[0]
            
        if not cmds.objExists('%s.%s' % (joint_shape, name)):
            cmds.addAttr(joint_shape, ln = name, k = True, min = 0)    
        
        if not attr.is_connected('%s.switch' % self.joints[0]):
            cmds.connectAttr('%s.%s' % (joint_shape, name), '%s.switch' % self.joints[0])
        
        max_value = cmds.attributeQuery('switch', max = True, node = self.joints[0])[0]
        
        try:
            test_max = cmds.attributeQuery(name, max = True, node = joint_shape)[0]
        
            if max_value < test_max:
                max_value = test_max
        except:
            pass
        
        cmds.addAttr('%s.%s' % (joint_shape, name), edit = True, maxValue = max_value)      
        
        cmds.setAttr('%s.%s' % (joint_shape, name), max_value)
        
        for control in self.controls:
            
            cmds.parent(shapes[0], control, add = True, s = True)
        
        attr.connect_message(shapes[0], self.control_group, 'switch') 
            
    def _post_create_rotate_order(self):
        
        for control in self.controls:
            test = ['X','Y','Z']
            
            count = 0
            
            for t in test:
                if not attr.is_locked('%s.rotate%s' % (control,t)):
                    count += 1
                    
            if count == 3:
                cmds.setAttr('%s.rotateOrder' % control, cb = True)
                cmds.setAttr('%s.rotateOrder' % control, k = True)
                
    def _post_create_connect(self, inst_attribute, description):
        
        if hasattr(self,inst_attribute):
            
            value = getattr(self, inst_attribute)
            
            if value:
                
                inc = 1
                value = vtool.util.convert_to_sequence(value)
                
                for sub_value in value:
                    attr.connect_message(sub_value, self.control_group, '%s%s' % (description,inc))
                    inc += 1
                
                return value
            
    def _post_store_orig_matrix(self, inst_attribute):
        
        if hasattr(self,inst_attribute):
            
            value = getattr(self, inst_attribute)
            
            if value:
                value = vtool.util.convert_to_sequence(value)
                for sub_value in value:
                    if sub_value:
                        attr.store_world_matrix_to_attribute(sub_value, skip_if_exists=True)
                
                return value
            
    def _post_add_to_control_set(self):
        
        set_name = 'set_controls'
        
        exists = False
        
        if cmds.objExists(set_name) and cmds.nodeType(set_name) == 'objectSet':
            exists = True
            
        if not exists:
            
            sets = cmds.ls('%s*' % set_name, type = 'objectSet')
            
            if sets:
                set_name = sets[0]
                exists = True
            
            if not exists:
                cmds.sets(name = core.inc_name(set_name), empty = True)
        
        parent_set = set_name
        child_set = None
        
        for set_name in self._custom_sets:
            
            if set_name == parent_set:
                continue
            
            custom_set_name = 'set_' + set_name
            
            if not cmds.objExists(custom_set_name):
                custom_set_name = cmds.sets(name = custom_set_name, empty = True)
            
            cmds.sets(custom_set_name, addElement = parent_set)
            
            parent_set = custom_set_name
            
        
        if self.__class__ != Rig:
            child_set = 'set_%s' % self.description
            if self.side:
                child_set = 'set_%s_%s' % (self.description,self.side)
            
            if child_set != parent_set:
                if not cmds.objExists(child_set):
                    cmds.sets(name = child_set, empty = True)
                
                cmds.sets(child_set, add = parent_set)
        
        
        
        if not child_set:
            child_set = parent_set
        
        controls = self.get_all_controls()
        
        for control in controls:
            
            vtool.util.show('Adding %s to control sets' % control)
            cmds.sets(control, e = True, add = child_set)
        
    def _post_connect_controller(self):
        
        controller = attr.get_message_input(self.control_group, 'control1')
        
        if not self._pick_walk_parent:
            parent = cmds.listRelatives(self.control_group, p = True)
            
            if parent:
                parent = parent[0]
            else:
                return
        else:
            parent = self._pick_walk_parent
        
        if controller:
            if not cmds.controller(parent, q = True, isController = True):
                return
                
            if cmds.controller(controller, q = True, isController = True):
                cmds.controller(controller, parent, p = True)
        
    def _post_connect_controls_to_switch_parent(self):
        
        if not self._switch_parent:
            return
        
        controls = self.get_all_controls()
        
        for control in controls:
            attr.connect_message(self._switch_parent, control, 'switchParent')
            
            
    def __getattribute__(self, item):

        custom_functions = ['create']
        
        if item in custom_functions:
            
            result = object.__getattribute__(self, item)
            
            result_values = result()
            
            def results():
                return result_values
        
            if item == 'create':    
                self._post_create()
                
            return results
        
        else:
            
            return object.__getattribute__(self,item)
        

        
    def _handle_side_variations(self):
        
        if vtool.util.is_left(self.side):
            self.side = 'L'
        if vtool.util.is_right(self.side):
            self.side = 'R'
        if vtool.util.is_center(self.side):
            self.side = 'C'
        
    
    
    def _create_group(self,  prefix = None, description = None):
        
        rig_group_name = self._get_name(prefix, description)
        
        group = cmds.group(em = True, n = core.inc_name(rig_group_name))
        
        return group
        
    def _create_default_groups(self):
                        
        self.control_group = self._create_control_group()
        self.setup_group = self._create_setup_group()
        
        self._create_control_group_attributes()
        
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
        
        
        
    def _create_setup_group(self, description = ''):
        
        group = self._create_group('setup', description)
        
        if self.setup_group:
            cmds.parent(group, self.setup_group)
        
        return group
        
    def _create_control_group(self, description = ''):
        
        group = self._create_group('controls', description)
        
        if self.control_group:
            cmds.parent(group, self.control_group)
            
        return group
    
    def _create_control_group_attributes(self):

        cmds.addAttr(self.control_group, ln = 'rigControlGroup', at = 'bool', dv = True)
        cmds.setAttr('%s.rigControlGroup' % self.control_group, l = True)
        
        cmds.addAttr(self.control_group, ln = 'description', dt = 'string')
        cmds.setAttr('%s.description' % self.control_group, self.description, type = 'string', l = True)
        
        cmds.addAttr(self.control_group, ln = 'side', dt = 'string')
        side = self.side
        if not side:
            side = ''
        cmds.setAttr('%s.side' % self.control_group, side, type = 'string', l = True)
    
    def _get_name(self, prefix = None, description = None, sub = False):
        
        name_list = [prefix,self.description, description, '1', self.side]
            
        filtered_name_list = []
        
        for name in name_list:
            if name:
                filtered_name_list.append(str(name))
        
        name = string.join(filtered_name_list, '_')
        
        return name
        
    def _get_control_name(self, description = None, sub = False):
        
        current_process = vtool.util.get_env('VETALA_CURRENT_PROCESS')

        if current_process:
            control_inst = util_file.ControlNameFromSettingsFile(current_process)
            
            if sub == False:
                control_inst.set_number_in_control_name(self._control_number)
            
            self._control_inst = control_inst
            
            if description:
                description = self.description + '_' + description
            else:
                description = self.description
            
            if sub == True:
                description = 'sub_%s' % description
            
            control_name = control_inst.get_name(description, self.side)
            
        if not current_process:
        
            prefix = 'CNT'
            if sub:
                prefix = 'CNT_SUB'
                
            control_name = self._get_name(prefix, description, sub = sub)
                
            control_name = control_name.upper()
            
        control_name = core.inc_name(control_name)
        
        return control_name
        
    def _create_control(self, description = None, sub = False, curve_shape = None):
        
        control = Control( self._get_control_name(description, sub) )
        
        cmds.parent(control.control, self.control_group)
        
        if curve_shape:
            control.set_curve_type(curve_type)
        
        side = self.side
        
        if not side:
            side = 'C'
        
        if not self._set_sub_control_color_only:
            control.color( attr.get_color_of_side( side , sub)  )
        if self._set_sub_control_color_only:
            control.color( attr.get_color_of_side( side, True )  )
        
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
            
            self._sub_controls_with_buffer[-1] = control.get()
        else:
            self._sub_controls_with_buffer.append(None)
            
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
        
    def set_sub_control_color_only(self, bool_value):
        self._set_sub_control_color_only = bool_value
        
    def set_control_size(self, float_value):
        """
        Sets the default size of the control curve.
        """
        
        if float_value == 0:
            vtool.util.warning('Setting control size to zero!')
        
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
        
    def set_switch_parent(self, rig_control_group):
        
        self._switch_parent = rig_control_group
        
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
    
    def set_connect_important(self,bool_value):
        self._connect_important = bool_value
    
    def set_number_in_control_name(self, bool_value):
        
        self._control_number = bool_value
    
    def set_no_last_number(self, bool_value):
        
        if bool_value:
            self._control_number = False
        else:
            self._control_number = True
    
    def set_pick_walk_parent(self, control_name):
        self._pick_walk_parent = control_name
    
    def set_control_set(self, list_of_set_names):
        """
        This will create the sets if they don't already exist.
        This will put all the controls generated under the last set name in the list
        """
        
        self._custom_sets = vtool.util.convert_to_sequence(list_of_set_names)
        
    def connect_sub_visibility(self, attr_name):
        """
        This connects the subVisibility attribute to the specified attribute.  Good when centralizing the sub control visibility. 
        """
        self._connect_sub_vis_attr = attr_name
    
    
    
    def get_all_controls(self):
        
        return self.control_dict.keys()
    
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
        vtool.util.show('\nUsing joints:%s' % self.joints)
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