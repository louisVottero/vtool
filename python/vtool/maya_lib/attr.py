# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

import re
import string
import colorsys
import random

import vtool.util

in_maya = vtool.util.is_in_maya()

if in_maya:
    import maya.cmds as cmds
    
import core
    
#do not import anim module here.
    

    
class Connections(object):
    """
    Convenience for dealing with connections.  Connection mapping gets stored in the class.
    
    Args:
        node (str): The name of the node with connections.
    """
    def __init__(self, node):
        
        self.node = node
        
        self.inputs = []
        self.outputs = []
        self.input_count = 0
        self.output_count = 0
        
        self._store_connections()
        
    def _get_outputs(self):
        outputs = cmds.listConnections(self.node, 
                            connections = True, 
                            destination = True, 
                            source = False,
                            plugs = True,
                            skipConversionNodes = True)  
        
        if outputs: 
            return outputs
        
        if not outputs:
            return []
    
        
    def _get_inputs(self):
        inputs = cmds.listConnections(self.node,
                             connections = True,
                             destination = False,
                             source = True,
                             plugs = True,
                             skipConversionNodes = True)
        
        if inputs:
            inputs.reverse()
            
            return inputs
        
        if not inputs:
            return []
        
    def _store_output_connections(self, outputs):
        
        output_values = []
        
        for inc in range(0, len(outputs), 2):
            split = outputs[inc].split('.')
            
            output_attribute = string.join(split[1:], '.')
            
            split_input = outputs[inc+1].split('.')
            
            node = split_input[0]
            node_attribute = string.join(split_input[1:], '.')
            
            output_values.append([output_attribute, node, node_attribute])
            
        self.outputs = output_values
        
    def _store_input_connections(self, inputs):
        
        #stores [source connection, destination_node, destination_node_attribute]
        
        input_values = []
        
        for inc in range(0, len(inputs), 2):
            split = inputs[inc+1].split('.')
            
            input_attribute = string.join(split[1:], '.')
            
            split_input = inputs[inc].split('.')
            
            node = split_input[0]
            node_attribute = string.join(split_input[1:], '.')
            
            input_values.append([input_attribute, node, node_attribute])
            
        self.inputs = input_values
        
    def _store_connections(self):
        
        self.inputs = []
        self.outputs = []
        
        inputs = self._get_inputs()
        outputs = self._get_outputs()
        
        if inputs:
            self._store_input_connections(inputs)
        if outputs:
            self._store_output_connections(outputs)
            
        self.connections = inputs + outputs
        
        self.input_count = self._get_input_count()
        self.output_count = self._get_output_count()
        
    def _get_in_source(self, inc):
        return '%s.%s' % (self.node, self.inputs[inc][0])
    
    def _get_in_target(self, inc):
        return '%s.%s' % (self.inputs[inc][1], self.inputs[inc][2])
    
    def _get_out_source(self, inc):
        return '%s.%s' % (self.outputs[inc][1], self.outputs[inc][2])
    
    def _get_out_target(self, inc):
        return'%s.%s' % (self.node, self.outputs[inc][0])
    
    def _get_input_count(self):
        return len(self.inputs)
    
    def _get_output_count(self):
        return len(self.outputs)
            
    def disconnect(self):
        """
        Disconnect all connections.
        """
        for inc in range(0, len(self.connections), 2):
            # needs to unlock the attribute first
            
            
            
            if cmds.isConnected(self.connections[inc], self.connections[inc+1], ignoreUnitConversion = True):
                
                lock_state = cmds.getAttr(self.connections[inc+1], l = True)
            
                if lock_state == True:
                    cmds.setAttr(self.connections[inc+1], l = False)
                
                cmds.disconnectAttr(self.connections[inc], self.connections[inc+1])
            
                if lock_state == True:
                    cmds.setAttr(self.connections[inc+1], l = True)    
                
            
    
    def connect(self):
        """
        This is meant to be run after disconnect(). This will reconnect all the stored connections.
        """
        for inc in range(0, len(self.connections), 2):
            
            if not cmds.objExists(self.connections[inc]):
                continue
            
            if not cmds.objExists(self.connections[inc+1]):
                continue
            
            if not cmds.isConnected(self.connections[inc], self.connections[inc+1], ignoreUnitConversion = True):
                
                lock_state = cmds.getAttr(self.connections[inc+1], l = True)
            
                if lock_state == True:
                    cmds.setAttr(self.connections[inc+1], l = False)
                
                cmds.connectAttr(self.connections[inc], self.connections[inc+1])
                
                if lock_state == True:
                    cmds.setAttr(self.connections[inc+1], l = True)
                
    def refresh(self):
        """
        Refresh the stored connections
        """
        self._store_connections()
                
    def get(self):
        """
        Get the stored connections.  Input and Output connections in a list.
        List is orderd as [[output, intput], ...], the output is whatever connects in, whether it be the node output into something or something inputing into the node.
        """
        return self.connections
    
    def get_input_at_inc(self, inc):
        """
        Get connection that inputs into the node at index.
        
        Args:
            inc (int): The index of the connection.
        """
        return self.inputs[inc]
    
    def get_output_at_inc(self, inc):
        """
        Get connection that the node outputs into at index.
        
        Args:
            inc (int): The index of the connection.
        """
        return self.outputs[inc]
    
    def get_connection_inputs(self, connected_node):
        """
        Get connections that input into the node. List is [[external_output, node_input], ...]
        
        Args:
            connected_node (str): The name of a connected node to filter with. Only inputs into the node will be returned.
        """
        found = []
        
        for inc in range(0, len(self.inputs)):
            
            test = self.inputs[inc]
            
            node = test[1]
            
            if node == connected_node:
                
                input_value = '%s.%s' % (self.node, test[0])
                output_value = '%s.%s' % (node, test[2])
                found.append([output_value, input_value])
                
        return found
    
    def get_connection_outputs(self, connected_node):
        """
        Get connections that the node outputs into. List is [[node_output, external_input], ...]
        
        
        Args:
            connected_node (str): The name of a connected node to filter with. Only inputs from that node will be returned.
            
        Retrun 
            list: [[node_output, external_input], ...]
        """
        
        found = []
        
        for inc in range(0, len(self.outputs)):
            
            test = self.outputs[inc]
            
            node = test[1]

            if node == connected_node:
                
                output_value = '%s.%s' % (self.node, test[0])
                input_value = '%s.%s' % (node, test[2])
                found.append([output_value, input_value])
                
        return found        
    
    def get_inputs_of_type(self, node_type):
        """
        Get nodes of node_type that connect into the node.
        
        Args:
            node_type (str): Maya node type.
            
        Returns:
            list: The names of connected nodes matching node_type. 
        """
        found = []
        
        for inc in range(0, self.input_count):
            node = self.inputs[inc][1]
            
            if cmds.nodeType(node).startswith(node_type):
                found.append(node)
                
        return found
        
    def get_outputs_of_type(self, node_type):
        """
        Get all nodes of node_type that output from the node. 
        
        Args:
            node_type (str): Maya node type.
            
        Returns:
            list: The names of connected nodes matching node_type. 
        """
        found = []
        
        for inc in range(0, self.output_count):
            node = self.outputs[inc][1]
            
            if cmds.nodeType(node).startswith(node_type):
                found.append(node)
                
        return found
    
    def get_outputs(self):
        """
        Get all the connections that output from the node
        
        Returns:
            list: [[node_output, external_input], ... ]
        """
        return self._get_outputs()
        
    def get_inputs(self):
        """
        get all connections that input into the node.
        
        Returns:
            list: [[external_output, node_input], ... ]
        """
        return self._get_inputs()
    
class TransferConnections(object):
    
    def transfer_keyable(self, source_node, target_node, prefix = None, disconnect_source = False):
        """
        Create the keyable attributes on the target node found on source_node.
        
        Args:
            prefix (str): The prefix to give. This is good when transfering more than once. This will help get rid of clashing attributes.
        """    
        source_connections = Connections(source_node)
        
        outputs = source_connections.get_inputs()
        
        for inc in range(0, len(outputs), 2):
            
            output_attr = outputs[inc] 
            input_attr = outputs[inc+1]

            if not cmds.getAttr(input_attr, k = True):
                    continue
            
            if input_attr.find('[') > -1:
                continue
            
            new_var = get_variable_instance(input_attr)
            
            if prefix:
                create_title(target_node, prefix)
                
                new_var.set_name('%s_%s' % (prefix, new_var.name))
            
            if not new_var:
                continue 
            
            new_var.set_node(target_node)
            new_var.create()
            new_var.connect_in(output_attr)
            
            if disconnect_source:
                disconnect_attribute(input_attr)
            
class LockState(object):
    """
    This saves the lock state, so that an attribute lock state can be reset after editing.
    
    Args:
        attribute (str): "node.attribute"
    """
    def __init__(self, attribute):
        
        self.lock_state = cmds.getAttr(attribute, l = True)
        self.attribute = attribute
        
    def unlock(self):
        """
        Unlock the attribute.
        """
        try:
            cmds.setAttr( self.attribute, l = False)
        except:
            pass
        
    def lock(self):
        """
        Lock the attribute.
        """
        try:
            cmds.setAttr( self.attribute, l = True)
        except:
            pass
        
    def restore_initial(self):
        """
        Restore the initial lock state.
        """
        try:
            cmds.setAttr( self.attribute, l = self.lock_state)
        except:
            pass

class LockNodeState(LockState):
    """
    This saves the lock state of the node, so that all attributes lock state can be reset after editing.
    
    Args:
        attribute (str): "node.attribute"
    """
    def __init__(self, node):
        
        self.node = node
        self.attributes = cmds.listAttr(node)
        
        self.lock_state = {}
        
        for attribute in self.attributes:
            try:
                self.lock_state[attribute] = cmds.getAttr('%s.%s' % (node, attribute), l = True)
            except:
                pass
        
    def unlock(self):
        """
        Unlock the attribute.
        """
        
        for attribute in self.attributes:
            try:
                attribute_name = '%s.%s' % (self.node, attribute)
                cmds.setAttr( attribute_name, l = False)
            except:
                pass
        
    def lock(self):
        """
        Lock the attribute.
        """
        for attribute in self.attributes:
            try:
                attribute_name = '%s.%s' % (self.node, attribute)
                cmds.setAttr( attribute_name, l = True)
            except:
                pass
        
    def restore_initial(self):
        """
        Restore the initial lock state.
        """
        
        for attribute in self.attributes:
            try:
                attribute_name = '%s.%s' % (self.node, attribute)
                cmds.setAttr( attribute_name, l = self.lock_state[attribute])
            except:
                pass

class LockTransformState(LockNodeState):
    def __init__(self, node):
        
        self.lock_state = {}
        self.attributes = []
        self.node = node
        
        for attribute in ['translate','rotate','scale']:
            for axis in ['X','Y','Z']:
                attribute_name = attribute + axis
                self.attributes.append(attribute_name)
                self.lock_state[attribute_name] = cmds.getAttr('%s.%s' % (node, attribute_name), l = True)
                
        
        

class RemapAttributesToAttribute(object):
    """
    Create a slider switch between multiple attributes.
    This is useful for setting up switches like ikFk.
    This will create the switch attribute if it doesn't already exist.
    
    Args:
        node (str): The name of a node.
        attribute (str): The attribute which should do the switching.
        
    """
    
    def __init__(self, node, attribute):
        
        self.node_attribute = '%s.%s' % (node, attribute)
        self.node = node
        self.attribute = attribute
        self.attributes = []
        
        self.keyable = True
        
        
    def _create_attribute(self):
        
        attribute_count = len(self.attributes)
        
        if attribute_count == None:
            attribute_count = 0
        
        #if attribute_count == 1:
        #    attribute_count + 1
        
        
        
        if cmds.objExists(self.node_attribute):
            
            
            
            variable = MayaNumberVariable(self.attribute)
            variable.set_node(self.node)
            variable.set_min_value(0)
        
            if attribute_count < 1:
                max_value = 0
            else:
                max_value = attribute_count-1
            
            if max_value < variable.get_max_value():
                max_value = variable.get_max_value()
            
            
            
            variable.set_max_value(max_value)
            variable.create()
            return
        
        variable = MayaNumberVariable(self.attribute)
        variable.set_variable_type(variable.TYPE_DOUBLE)
        variable.set_node(self.node)
        variable.set_min_value(0)
        
        if attribute_count < 1:
            max_value = 0
        else:
            max_value = attribute_count-1
        
        if max_value < variable.get_max_value():
            max_value = variable.get_max_value()
                
        variable.set_max_value(max_value)
        variable.set_keyable(self.keyable)
        variable.create()

    def set_keyable(self, bool_value):
        """
        Whether the switch attribute should be keyable. 
        This only works if the attribute doesn't exist prior to create()
        """
        
        self.keyable = bool_value
      
    def create_attributes(self, node, attributes):
        """
        Add attributes to be mapped. Saved in a list for create()
        
        Args:
            node (str): The name of the node where the attributes live.
            attributes (list): The names of attributes on the node to map to the switch.
        """
        for attribute in attributes:
            self.create_attribute(node, attribute)
          
    def create_attribute(self, node, attribute):
        """
        Add an attribute to be mapped. Saved in a list for create()
        
        Args:
            node (str): The name of the node where the attributes live.
            attributes (list): The name of an attribute on the node to map to the switch.
        """
        self.attributes.append( [node, attribute] )
                
    def create(self): 
        """
        Create the switch.
        """       
        
        self._create_attribute()
        
        length = len(self.attributes)
        
        if length <= 1:
            return
        
        for inc in range(0,length):
            
            node = self.attributes[inc][0]
            attribute = self.attributes[inc][1]
            
            input_min = inc - 1
            input_max = inc + 1
            
            if input_min < 0:
                input_min = 0
                
            if input_max > (length-1):
                input_max = (length-1)
            
            input_node = get_attribute_input(attribute)
                
            if input_node:
                if cmds.nodeType(input_node) == 'remapValue':
                    split_name = input_node.split('.')
                    
                    remap = split_name[0]
                    
                if cmds.nodeType(input_node) != 'remapValue':
                    input_node = None
               
            attribute_nice = attribute.replace('[', '_')
            attribute_nice = attribute_nice.replace(']', '')
            attribute_nice = attribute_nice.replace('.', '_')
                                        
            if not input_node: 
                remap = cmds.createNode('remapValue', n = 'remapValue_%s' % attribute_nice)
            
            test_max = cmds.getAttr('%s.inputMax' % remap)
            
            if test_max > input_max:
                input_max = test_max
            
            cmds.setAttr('%s.inputMin' % remap, input_min)
            cmds.setAttr('%s.inputMax' % remap, input_max)
            
            if inc == 0:
                cmds.setAttr('%s.value[0].value_FloatValue' % remap, 1)
                cmds.setAttr('%s.value[0].value_Position' % remap, 0)
                cmds.setAttr('%s.value[0].value_Interp' % remap, 1)
                cmds.setAttr('%s.value[1].value_FloatValue' % remap, 0)
                cmds.setAttr('%s.value[1].value_Position' % remap, 1)
                cmds.setAttr('%s.value[1].value_Interp' % remap, 1)
            
            if inc == (length-1):
                cmds.setAttr('%s.value[0].value_FloatValue' % remap, 0)
                cmds.setAttr('%s.value[0].value_Position' % remap, 0)
                cmds.setAttr('%s.value[0].value_Interp' % remap, 1)
                cmds.setAttr('%s.value[1].value_FloatValue' % remap, 1)
                cmds.setAttr('%s.value[1].value_Position' % remap, 1)
                cmds.setAttr('%s.value[1].value_Interp' % remap, 1)
            
            if inc != 0 and inc != (length-1):
                for inc2 in range(0,3):
                    if inc2 == 0:
                        position = 0
                        value = 0
                    if inc2 == 1:
                        position = 0.5
                        value = 1
                    if inc2 == 2:
                        position = 1
                        value = 0
                        
                    cmds.setAttr('%s.value[%s].value_FloatValue' % (remap,inc2), value)
                    cmds.setAttr('%s.value[%s].value_Position' % (remap,inc2), position)
                    cmds.setAttr('%s.value[%s].value_Interp' % (remap,inc2), 1)    
            
            
            
            disconnect_attribute('%s.%s' % (node,attribute)) 
            cmds.connectAttr('%s.outValue' % remap, '%s.%s' % (node,attribute))
                                    
            disconnect_attribute('%s.inputValue' % remap)
            cmds.connectAttr(self.node_attribute,'%s.inputValue' % remap)
            
class OrientJointAttributes(object):
    """
    Creates attributes on a node that can then be used with OrientAttributes
    """
    def __init__(self, joint = None):
        self.joint = joint
        self.attributes = []
        self.title = None
        
        if joint:
            self._create_attributes()
    
    def _create_attributes(self):
        
        self.title = MayaEnumVariable('ORIENT_INFO')
        self.title.create(self.joint)
        
        attr = self._create_axis_attribute('aimAxis')
        self.attributes.append(attr)
        
        attr = self._create_axis_attribute('upAxis')
        self.attributes.append(attr)
        
        attr = self._create_axis_attribute('worldUpAxis')
        self.attributes.append(attr)
    
        enum = MayaEnumVariable('aimAt')
        enum.set_enum_names(['world_X', 
                             'world_Y', 
                             'world_Z', 
                             'child',
                             'parent',
                             'local_parent'])
        enum.set_locked(False)
        enum.create(self.joint)
        
        
        self.attributes.append(enum)
        
        enum = MayaEnumVariable('aimUpAt')
        enum.set_enum_names(['world',
                             'parent_rotate',
                             'child_position',
                             'parent_position',
                             'triangle_plane',
                             '2nd_child_position',
                             'surface'])
        
        enum.set_locked(False)
        enum.create(self.joint)
        
        self.attributes.append(enum)
        
        attr = self._create_triangle_attribute('triangleTop')
        self.attributes.append(attr)
        
        attr = self._create_triangle_attribute('triangleMid')
        self.attributes.append(attr)
        
        attr = self._create_triangle_attribute('triangleBtm')
        self.attributes.append(attr)
        
        attr = MayaEnumVariable('invertScale')
        attr.set_enum_names(['none',
                             'X',
                             'Y',
                             'Z',
                             'XY',
                             'XZ',
                             'YZ',
                             'XYZ'])
        attr.set_locked(False)
        attr.create(self.joint)
        self.attributes.append(attr)
        
        
        attr = MayaNumberVariable('active')
        attr.set_variable_type('bool')
        attr.set_keyable(True)
        attr.create(self.joint)
        attr.set_value(1)
        self.attributes.append(attr)
        
        attr = MayaStringVariable('surface')
        attr.create(self.joint)
        self.attributes.append(attr)
        
        

    def _delete_attributes(self):
        
        if self.title:
            self.title.delete()
        
        for attribute in self.attributes:
            attribute.delete()
            
    def _create_axis_attribute(self, name):
        enum = MayaEnumVariable(name)
        enum.set_enum_names(['X','Y','Z','-X','-Y','-Z','none'])
        enum.set_locked(False)
        enum.create(self.joint)
        
        return enum
        
    def _create_triangle_attribute(self, name):
        enum = MayaEnumVariable(name)
        enum.set_enum_names(['grand_parent', 'parent', 'self', 'child', 'grand_child'])
        enum.set_locked(False)
        enum.create(self.joint)
        
        return enum
    
    def _set_default_values(self, context_senstive = False):
        
        if not context_senstive:
            self.attributes[0].set_value(0)
            self.attributes[1].set_value(1)
            self.attributes[2].set_value(1)
            self.attributes[3].set_value(3)
            self.attributes[4].set_value(0)
            self.attributes[5].set_value(1)
            self.attributes[6].set_value(2)
            self.attributes[7].set_value(3)
            self.attributes[8].set_value(0)
            self.attributes[9].set_value(1)
            return
        
        
        children = None
        
        if self.joint:
            children = cmds.listRelatives(self.joint, type = 'joint')
            parent = cmds.listRelatives(self.joint, type = 'joint', p = True)
        
            
        if self.joint and children:
            self.attributes[0].set_value(0)
            self.attributes[1].set_value(1)
            self.attributes[2].set_value(1)
            self.attributes[3].set_value(3)
            self.attributes[4].set_value(0)
            self.attributes[5].set_value(1)
            self.attributes[6].set_value(2)
            self.attributes[7].set_value(3)
            self.attributes[8].set_value(0)
            self.attributes[9].set_value(1)
        elif self.joint and not children and not parent:
            self.attributes[0].set_value(0)
            self.attributes[1].set_value(1)
            self.attributes[2].set_value(1)
            self.attributes[3].set_value(0)
            self.attributes[4].set_value(0)
            self.attributes[5].set_value(1)
            self.attributes[6].set_value(2)
            self.attributes[7].set_value(3)
            self.attributes[8].set_value(0)
            self.attributes[9].set_value(1)
        else:
            self.attributes[0].set_value(0)
            self.attributes[1].set_value(1)
            self.attributes[2].set_value(1)
            self.attributes[3].set_value(5)
            self.attributes[4].set_value(1)
            self.attributes[5].set_value(1)
            self.attributes[6].set_value(2)
            self.attributes[7].set_value(3)
            self.attributes[8].set_value(0)
            self.attributes[9].set_value(1)
    
    def set_joint(self, joint):
        """
        Set a joint to create attributes on.
        
        Args:
            joint (str): The name of the joint.
        """
        self.joint = joint
        
        self._create_attributes()
    
    def get_values(self):
        """
        Get the orient settings in a dictionary.
        
        Returns:
            dict
        """
        value_dict = {}
        
        for attr in self.attributes:
            value_dict[attr.get_name(True)] = attr.get_value()
            
        return value_dict
    
    def set_values(self, value_dict):
        
        for attr in self.attributes:
            attr.set_value(value_dict[attr.get_name(True)])
    
    def set_default_values(self, context_sensitive = False):
        """
        Reset the attributes to default.
        """
        self._set_default_values(context_sensitive)


    def delete(self):
        """
        Delete the attributes off of the joint set with set_joint.
        """
        self._delete_attributes()
        

def get_variable_instance(attribute):
    """
    Get a variable instance for the attribute.
    
    Args:
        attribute (str): node.attribute name
    
    Returns:
        object: The instance of a corresponding variable.
    """
    
    node, attr = get_node_and_attribute(attribute)
    
    var_type = None
    
    try:
        var_type = cmds.getAttr(attribute, type = True)
    except:
        return
        
    if not var_type:
        return
    
    var = get_variable_instance_of_type(attr, var_type)
    var.set_node( node )
    var.load()
    
    return var
    
def get_variable_instance_of_type(name, var_type):
                
    var = MayaVariable(name)
    
    if var_type in var.numeric_attributes:
        var = MayaNumberVariable(name)
        
    if var_type == 'bool':
        var = MayaVariable(name)
        
    if var_type == 'enum':
        var = MayaEnumVariable(name)
        
    if var_type == 'string':
        var = MayaStringVariable(name)
    
    var.set_variable_type(var_type)
    
    
    return var
    

    
#--- variables
class MayaVariable(vtool.util.Variable):
    """
    Convenience class for dealing with Maya attributes.
    """
    
    
    TYPE_BOOL = 'bool'
    TYPE_LONG = 'long'
    TYPE_SHORT = 'short'
    TYPE_ENUM = 'enum'
    TYPE_FLOAT = 'float'
    TYPE_DOUBLE = 'double'
    TYPE_STRING = 'string'
    TYPE_MESSAGE = 'message'
    
    numeric_attributes = ['bool', 'long', 'short', 'float', 'double']
    
    def __init__(self, name ):
        super(MayaVariable, self).__init__(name)
        self.variable_type = 'short'
        self.keyable = True
        self.channelbox = None
        self.locked = False
        self.attr_exists = False
        self._node_and_attr = ''
        
    def _command_create_start(self):
        return 'cmds.addAttr(self.node,'
    
    def _command_create_mid(self):
        
        flags = ['longName = self.name']
        
        return flags
    
    def _command_create_end(self):
        data_type = self._get_variable_data_type()
        return '%s = self.variable_type)' %  data_type

    def _create_attribute(self, exists = False):
        
        if exists:
            return
        
        start_command = self._command_create_start()
        mid_command = string.join(self._command_create_mid(), ', ')
        end_command = self._command_create_end()
        
        command = '%s %s, %s' % (start_command,
                                mid_command,
                                end_command)
         
        eval( command )
    
    #--- _set
    
    def _set_lock_state(self):
        if not self.exists():
            return
        
        try:
            cmds.setAttr(self._get_node_and_variable(), l = self.locked)
        except:
            #faster not to check. 
            pass
    
    def _set_keyable_state(self):

        if not self.exists():
            return

        cmds.setAttr(self._get_node_and_variable(), k = self.keyable)       

    def _set_channel_box_state(self):
        
        if self.channelbox == None:
            return
        
        if not self.exists():
            return
        
        cmds.setAttr(self._get_node_and_variable(), cb = self.channelbox)   

    def _set_value(self):
                
        locked_state = self._get_lock_state()
        
        self.set_locked(False)
        
        if self._get_variable_data_type() == 'attributeType':
            if not self.variable_type == 'message':
                try:
                    cmds.setAttr(self._get_node_and_variable(), self.value )
                except:
                    #this was added in a case where the value was trying to set to one, but the max value was 0
                    pass

            if self.variable_type == 'message':
                if self.value:
                    connect_message(self.value, self.node, self.name)
            
        if self._get_variable_data_type() == 'dataType':
            if self.value != None:
                cmds.setAttr(self._get_node_and_variable(), self.value, type = self.variable_type )
        
        self.set_locked(locked_state)
    
    #--- _get
    
    def _get_variable_data_type(self):
        return core.maya_data_mappings[self.variable_type]
    
    def _get_node_and_variable(self):
        
        if not self.node:
            return
        if not self.name:
            return
        
        if not self._node_and_attr:
            self._node_and_attr = self.node + '.' + self.name
        
        return self._node_and_attr
        
    def _get_lock_state(self):
        if not self.exists():
            return self.locked
        
        return cmds.getAttr(self._get_node_and_variable(), l = True)
        
    def _get_keyable_state(self):
        if not self.exists():
            return self.keyable
        
        return cmds.getAttr(self._get_node_and_variable(), k = True)

    def _get_value(self):
        if not self.exists():
            return
        
        if self.variable_type == 'message':
            return get_attribute_input(self._get_node_and_variable(), node_only = True)
        
        if not self.variable_type == 'message':
            return cmds.getAttr(self._get_node_and_variable())

    def _update_states(self):
        
        self._set_keyable_state()
        self._set_channel_box_state()
        self._set_lock_state()

    def exists(self, force = False):
        """
        Returns:
            bool
        """
        
        if not self.node:
            return False
        
        if not self.name:
            return False
        
        if self.attr_exists and not force:
            return True
        
        self.attr_exists = cmds.objExists(self._get_node_and_variable())
        
        return self.attr_exists
    
    def is_numeric(self):
        
        if self.variable_type in self.numeric_attributes:
            return True
        
        return False 

    #--- set
    def set_name(self, name):
        """
        Set the name of the variable.
        
        Args:
            name (str)
            
        """
        var_name = self._get_node_and_variable()
        
        if cmds.objExists(var_name):
            cmds.renameAttr(var_name, name)
            
        super(MayaVariable, self).set_name(name)
        
        var_name = self._get_node_and_variable()
        
        self._node_and_attr = ''
    
    def set_value(self, value):
        """
        Set the value of the variable.
        
        Args:
            value
            
        """
        
        super(MayaVariable, self).set_value(value)
        try:
            self._set_value()
        except:
            pass
        
    def set_locked(self, bool_value):
        """
        Set the lock state of the variable.
        
        Args:
            bool_value (bool)
            
        """
        self.locked = bool_value
        self._set_lock_state()
        
    def set_keyable(self, bool_value):
        """
        Set the keyable state of the variable.
        
        Args:
            bool_value (bool)
            
        """
        
        self.keyable = bool_value
        self._set_keyable_state()

    def set_channel_box(self, bool_value):
        
        self.channelbox = bool_value
        self._set_channel_box_state()

    def set_variable_type(self, name):
        """
        Set the variable type, check Maya documentation.
        """
        
        self.variable_type = name

    def set_node(self, name):
        """
        Set the node where the variable should live.
        
        Args:
            name (str)
            
        """
        self.node = name
        
        self.exists(force = True)

    #--- get

    def get_value(self):
        """
        Get the variables value.
        
        Returns:
            value
        """
        return self._get_value()
        
    def get_name(self, name_only = False):
        """
        Get the name of the variable.
        
        Args:
            name_only (bool): If True just the variable name is returned. If False the node and variable are returned: "node.variable".
        """
        
        if self.node and not name_only:
            return self._get_node_and_variable()
        if not self.node or name_only:
            return self.name

    def get_dict(self):
        """
        Get a dictionary that represents the state of the variable.
        
        Returns:
            dict
        """
        
        var_dict = {}
        
        var_dict['value'] = self._get_value()
        var_dict['type'] = self.variable_type
        var_dict['key'] = self._get_keyable_state()
        var_dict['lock'] = self._get_lock_state()
        
        return var_dict
    
    def set_dict(self, var_dict):
        """
        Set a dictionary that describes the variable. See get_dict.
        
        Args:
            var_dict (dict): A dictionary created from get_dict.
            
        """
        value = var_dict['value']
        self.set_value(value)
        
        type_value = var_dict['type']
        self.set_variable_type(type_value)
        
        keyable = var_dict['key']
        self.set_keyable(keyable)
        
        lock = var_dict['lock']
        self.set_locked(lock)
    
    def create(self, node = None):
        """
        Create the variable on the node.
        
        Args:
            node (str): The node for the variable.  If not set, set_node should be set.
            
        """
        if node:
            self.node = node
        
        value = self.value
                
        if self.exists(force = True):
            if value != None:
                value = self.get_value()

        self._create_attribute(exists = self.attr_exists)
        self._update_states()
               
        if value != None:
            self.set_value( value )
        
    def delete(self, node = None):
        """
        Delete the variable on the node.
        
        Args:
            node (str): The node for the variable.  If not set, set_node should be set.
            
        """
        if node:
            self.node = node
        
        #theses lines might cause bugs
        try:
            cmds.setAttr(self._get_node_and_variable(), l = False)   
        except:
            pass
        #------
            
        cmds.deleteAttr(self.node, at = self.name)
        self.attr_exists = False
        self._node_and_attr = ''
        
    def load(self):
        """
        Refresh the internal values.
        """
        self.value = self._get_value()
        self.locked = self._get_lock_state()
        self.keyable = self._get_keyable_state()
        
    def connect_in(self, attribute):
        """
        Connect the attribute into this variable.
        
        Args:
            attribute (str): 'node.attribute'
        
        """
        cmds.connectAttr(attribute, self._get_node_and_variable())
        
    def connect_out(self, attribute):
        """
        Connect from the variable into the attribute.
        
        Args:
            attribute (str): 'node.attribute'
        
        """
        cmds.connectAttr(self._get_node_and_variable(), attribute)
        
class MayaNumberVariable(MayaVariable):
    """
    Convenience class for dealing with Maya numeric attributes.
    """
    
    
    def __init__(self, name):
        super(MayaNumberVariable, self).__init__(name)
        
        self.min_value = None
        self.max_value = None
        
        self.variable_type = 'double'
        
    def _update_states(self):
        
        self._set_min_state()
        self._set_max_state()
        
        super(MayaNumberVariable, self)._update_states()
        
    
    #--- _set
    
    def _set_min_state(self):
        if not self.exists():
            return
        
        if not self.min_value:
            if cmds.attributeQuery(self.name, node = self.node, minExists = True ):
                cmds.addAttr(self._get_node_and_variable(), edit = True, hasMinValue = False)
            
        
        if self.min_value != None:
            
            cmds.addAttr(self._get_node_and_variable(), edit = True, hasMinValue = True)
            cmds.addAttr(self._get_node_and_variable(), edit = True, minValue = self.min_value)
        
    def _set_max_state(self):
        
        if not self.exists():
            return
        
        if not self.max_value:
            if cmds.attributeQuery(self.name, node = self.node, maxExists = True ):
                cmds.addAttr(self._get_node_and_variable(), edit = True, hasMaxValue = False)
        
        if self.max_value != None:
            
            cmds.addAttr(self._get_node_and_variable(), edit = True, hasMaxValue = True)
            cmds.addAttr(self._get_node_and_variable(), edit = True, maxValue = self.max_value)
        
    #--- _get
        
    def _get_min_state(self):
        if not self.exists():
            return
        
        #this is like this because of scale attribute.  Not sure how to query if a double has ability for min and max.
        try:
            return cmds.attributeQuery(self.name, node = self.node, minimum = True)[0]
        except:
            return

    def _get_max_state(self):
        if not self.exists():
            return
        
        #this is like this because of scale attribute.  Not sure how to query if a double has ability for min and max.
        try:
            return cmds.attributeQuery(self.name, node = self.node, maximum = True)[0]
        except:
            return
        
    def get_max_value(self):
        return self._get_max_state()
        
    def set_min_value(self, value):
        """
        Args:
            value (float): Minimum value constraint
        
        """
        self.min_value = value
        self._set_min_state()
    
    def set_max_value(self, value):
        """
        Args:
            value (float): Maximum value constraint
        
        """
        
        self.max_value = value
        self._set_max_state()
        
    def load(self):
        """
        Refresh the internal values.
        """
        super(MayaNumberVariable, self).load()
        
        self.min_value = self._get_min_state()
        self.max_value = self._get_max_state()
        
class MayaEnumVariable(MayaVariable):
    """
    Convenience class for dealing with Maya enum attributes.
    """
    
    def __init__(self, name):                
        super(MayaEnumVariable, self).__init__(name)
        
        self.variable_type = 'enum'
        self.enum_names = ['----------']
        self.set_locked(True)
       
    def _command_create_mid(self):
        
        enum_name = string.join(self.enum_names, '|')
        
        flags= super(MayaEnumVariable, self)._command_create_mid()
        flags.append('enumName = "%s"' % enum_name)
        
        return flags

    def _update_states(self):
        super(MayaEnumVariable, self)._update_states()
        
        self._set_enum_state()

    

    def _set_enum_state(self, set_value = True):
        
        if not self.exists():
            return
        
        enum_name = string.join(self.enum_names, ':')
                
        if not enum_name:
            return
        
        value = self.get_value()
        
        cmds.addAttr(self._get_node_and_variable(), edit = True, enumName = enum_name)
        
        if set_value:
            self.set_value(value)
    
    def _set_value(self):
        if not self.enum_names:
            return
        
        self._set_enum_state(set_value = False)
        try:
            super(MayaEnumVariable, self)._set_value()
        except:
            pass
    
    def set_enum_names(self, name_list):
        """
        Args:
            name_list (list): List of strings to define the enum.
        """
        self.enum_names = name_list
        
        self._set_enum_state()

class MayaStringVariable(MayaVariable):
    """
    Convenience class for dealing with Maya string attributes.
    """
    
    def __init__(self, name):
        super(MayaStringVariable, self).__init__(name)
        self.variable_type = 'string'
        self.value = ''

class StoreData(object):
    def __init__(self, node = None):
        self.node = node
        
        if not node:
            return
        
        if not cmds.objExists(node):
            return
        
        if not node:
            return
        
        self._setup_node(node)
        
    def _setup_node(self, node):
        
        self.data = MayaStringVariable('DATA')
        self.data.set_node(self.node)
        
        if not cmds.objExists('%s.DATA' % node):
            self.data.create(node)
            
    def set_node(self, node):
        self.node = node
        self._setup_node(node)
        
    def set_data(self, data):
        if not self.node:
            return
        if not cmds.objExists(self.node):
            return
        
        str_value = str(data)
        
        self.data.set_value(str_value)
        
    def get_data(self):
        if not self.node:
            return
        if not cmds.objExists(self.node):
            return
        return self.data.get_value()
    
    def eval_data(self):
        
        if not self.node:
            return
        
        if not cmds.objExists(self.node):
            return
        data = self.get_data()
        
        if data:
            return eval(data)

class Attributes(object):
    """
    Still testing. Convenience class for dealing with groups of attributes.
    Currently only works on bool, long, short, float, double
    
    Args:
        node (str): The name of the node where the attributes live.
    """
    numeric_attributes = ['bool', 'long', 'short', 'float', 'double']
    
    def __init__(self, node):
        
        self.node = node
        
        self.variables = []
        self.attribute_dict = {}
        
        
    def _get_variable_instance(self, name, var_type):
                
        var = MayaVariable(name)
        
        if var_type in self.numeric_attributes:
            var = MayaNumberVariable(name)
            
        if var_type == 'enum':
            var = MayaEnumVariable(name)
            
        if var_type == 'string':
            var = MayaStringVariable(name)
        
        var.set_variable_type(var_type)
        var.set_node(self.node)    
        
        return var
        
    def _retrieve_attribute(self, attribute_name):
        
        node_and_attribute = '%s.%s' % (self.node, attribute_name)
        
        if not cmds.objExists(node_and_attribute):
            return
        
        var_type = cmds.getAttr(node_and_attribute, type = True)
        
        var = self._get_variable_instance(attribute_name, var_type)
        var.set_node(self.node)
        var.load()
        
        return var
        
    def _store_attributes(self):
        custom_attributes = cmds.listAttr(self.node, ud = True)
        
        self.variables = []
        
        for attribute in custom_attributes:
            
            var = self._retrieve_attribute(attribute)    
        
            var_dict = var.get_dict()    
            
            self.attribute_dict[attribute] = var_dict
            
            self.variables.append(var)
            
        return self.variables
    
    def _retrieve_attributes(self):
        
        variables = self._store_attributes()
        return variables    
    
    def delete_all(self, retrieve = False):
        """
        Delete all loaded variables on a node.
        """
        variables = []
        
        if retrieve or not self.variables:
            
            variables = self._retrieve_attributes()
        if not retrieve and self.variables:
            variables = self.variables
        
        for var in variables:
            
            var.delete()
        
    def create_all(self):
        """
        Meant to be used after delete_all to restore the attributes.
        """
        for var in self.variables:
            
            var.create()
        
    def delete(self, name):
        """
        delete the attribute by name
        
        Args:
            name (str): The name of an attribute on the node.
        """
        connections = Connections(self.node)
        connections.disconnect()
        
        
        self.delete_all()
        
        variables = []
        
        for variable in self.variables:
            
            if variable.name == name:
                continue
        
            variables.append(variable)        
            variable.create()
            
        self.variables = variables
        
        connections.connect()
            
    def create(self, name, var_type, index = None):
        """
        Create an attribute on the node. This refreshes all the attributes.
        
        Args:
            name (str): The name of the attribute.
            var_type (str): The type of variable.
            index (int): The index where the attribute should be created. 0 would make it the first attribute.
        """
        connections = Connections(self.node)
        connections.disconnect()
        
        self.delete_all()
        
        var_count = len(self.variables)
        
        remove_var = None
        
        for var in self.variables:
            if var.name == name:
                remove_var = var
                break
                            
        if remove_var:
            remove_index = self.variables.index(remove_var)
            self.variables.pop(remove_index)
            
        var = self._get_variable_instance(name, var_type)
                
        if index > var_count:
            index = None
        
        if index != None:
            self.variables.insert(index, var)
        if index == None:
            self.variables.append(var)
                
        self.create_all()
        
        connections.connect()
    
    def get_variables(self):
        """
        Get the variables initialized to the var class
        
        Returns:
            list: A list of var classes initalized to work on variables on the node.
        """
        self._store_attributes()
        
        return self.variables
    
    def get_variable(self, attribute_name):
        """
        Get a variable by name initialized to the var class.
        
        Args:
            attribute_name (str): The name of a variable on the node.
            
        Returns:
            object: An instance of the var class.
        """
        self._store_attributes()
        
        return self._retrieve_attribute(attribute_name)
    
    def rename_variable(self, old_name, new_name):
        """
        Rename a variable. 
        This will work in such a way that the variables are all reset.
        
        Args:
            old_name (str): The old name of the variable.
            new_name (str): The new name of the variable.
        """
        if not self.node:
            return
        
        var = self.get_variable(old_name)
        
        if not var:
            vtool.util.warning('Could not rename attribute, %s.%s.' % (self.node, old_name))
            return
        
        var.set_name(new_name)
        
        self._store_attributes()
        
        connections = Connections(self.node)
        connections.disconnect()
        
        self.delete_all()
        self.create_all()
        
        connections.connect()

class TransferVariables():
    def __init__(self):
        pass
    
    def transfer_control(self, source, target):
        
        attrs = []
        
        transform_names = ['translate', 'rotate','scale']
        
        for transform_name in transform_names:
            for axis in ['X','Y','Z']:
                attr_name = transform_name + axis
                attrs.append(attr_name)
        
        attrs.append('visibility')
        
        ud_attrs = cmds.listAttr(source, ud = True)
        
        if ud_attrs:
            attrs = attrs + ud_attrs
        
        for attr in attrs:
            
            var_name = source + '.' + attr 
        
            new_var = get_variable_instance(var_name)
            
            if not new_var:
                continue 
            
            new_var.set_node(target)
            new_var.create()

class MayaNode(object):
    """
    Not fully implemented. 
    Meant to be a convenience class for dealing with maya nodes.
    """
    def __init__(self, name = None):
        
        self.node = None
        
        self._create_node(name)
        
    def _create_node(self, name):
        pass
    
class MultiplyDivideNode(MayaNode):
    """
    Convenience class for dealing with multiply divide nodes.
    
    Args:
        name (str): The description to give the node. Name = 'multiplyDivide_(name)'.
     """
    
    def __init__(self, name = None):
        
        if not name.startswith('multiplyDivide'):
            name = core.inc_name('multiplyDivide_%s' % name)
        
        super(MultiplyDivideNode, self).__init__(name)
        
    def _create_node(self, name):
        self.node = cmds.createNode('multiplyDivide', name = name)
        cmds.setAttr('%s.input2X' % self.node, 1)
        cmds.setAttr('%s.input2Y' % self.node, 1)
        cmds.setAttr('%s.input2Z' % self.node, 1)
        
    def set_operation(self, value):
        """
        Set the operation.
        0 = no operation
        1 = multiply
        2 = divide
        3 = power
        
        default = 1
        
        Args:
            value (int): The operation index.
        """
        cmds.setAttr('%s.operation' % self.node, value)
    
    def set_input1(self, valueX = None, valueY = None, valueZ = None):
        """
        Set the intput1 values
        
        Args:
            valueX (float)
            valueY (float)
            valueZ (float)
        """
        if valueX != None:
            cmds.setAttr('%s.input1X' % self.node, valueX)
            
        if valueY != None:
            cmds.setAttr('%s.input1Y' % self.node, valueY)
            
        if valueZ != None:
            cmds.setAttr('%s.input1Z' % self.node, valueZ)
        
    def set_input2(self, valueX = None, valueY = None, valueZ = None):
        """
        Set the intput2 values
        
        Args:
            valueX (float)
            valueY (float)
            valueZ (float)
        """
        if valueX != None:
            cmds.setAttr('%s.input2X' % self.node, valueX)
            
        if valueY != None:
            cmds.setAttr('%s.input2Y' % self.node, valueY)
            
        if valueZ != None:
            cmds.setAttr('%s.input2Z' % self.node, valueZ)
            
    def input1X_in(self, attribute):
        """
        Connect into input1X.
        
        Args:
            attribute (str): The node.attribute to connect in.
        """
        cmds.connectAttr(attribute, '%s.input1X' % self.node)
    
    def input1Y_in(self, attribute):
        """
        Connect into input1Y.
        
        Args:
            attribute (str): The node.attribute to connect in.
        """
        
        cmds.connectAttr(attribute, '%s.input1Y' % self.node)
        
    def input1Z_in(self, attribute):
        """
        Connect into input1Z.
        
        Args:
            attribute (str): The node.attribute to connect in.
        """
        
        cmds.connectAttr(attribute, '%s.input1Z' % self.node)
    
    def input2X_in(self, attribute):
        """
        Connect into input2X.
        
        Args:
            attribute (str): The node.attribute to connect in.
        """
        
        cmds.connectAttr(attribute, '%s.input2X' % self.node)
    
    def input2Y_in(self, attribute):
        """
        Connect into input2Y.
        
        Args:
            attribute (str): The node.attribute to connect in.
        """
        
        cmds.connectAttr(attribute, '%s.input2Y' % self.node)
        
    def input2Z_in(self, attribute):
        """
        Connect into input2Z.
        
        Args:
            attribute (str): The node.attribute to connect in.
        """
        
        cmds.connectAttr(attribute, '%s.input2Z' % self.node)
        
    def outputX_out(self, attribute):
        """
        Connect out from outputX.
        
        Args:
            attribute (str): The node.attribute to connect out into.
        """
        
        connect_plus('%s.outputX' % self.node, attribute)
    
    def outputY_out(self, attribute):
        """
        Connect out from outputY.
        
        Args:
            attribute (str): The node.attribute to connect out into.
        """
        connect_plus('%s.outputY' % self.node, attribute)
        
    def outputZ_out(self, attribute):
        """
        Connect out from outputZ.
        
        Args:
            attribute (str): The node.attribute to connect out into.
        """
        
        connect_plus('%s.outputZ' % self.node, attribute)
            
def is_attribute(node_dot_attribute):
    """
    Check if what is passed is an attribute.
    
    Returns:
        bool
    """
    if not cmds.objExists(node_dot_attribute):
        return False
    
    split = node_dot_attribute.split('.')
    
    if len(split) == 1:
        return False
    
    if len(split) > 1 and not split[1]:
        return False
    
    return True
        
def is_attribute_numeric(node_dot_attribute):
    """
    Check if the attribute exists and is numeric.
    
    Returns:
        bool
    """
    if not is_attribute(node_dot_attribute):
        return False
    
    attr_type = cmds.getAttr(node_dot_attribute, type = True)
    
    numeric_types = ['bool',
                     'float',
                     'double',
                     'long',
                     'short',
                     'doubleLinear',
                     'doubleAngle',
                     'enum']
    
    if attr_type in numeric_types:
        return True
    
def is_translate_rotate_connected(transform, ignore_keyframe = False):
    """
    Check if translate and rotate attributes are connected.
    
    Args:
        transform (str): The name of a transform.
        
    Returns:
        bool
    """
    main_attr = ['translate', 'rotate']
    sub_attr = ['X','Y','Z']
    
    for attr in main_attr:
        
        for sub in sub_attr:
            
            name = transform + '.' + attr + sub
            
            input_value = get_attribute_input(name)
            
            if not input_value:
                return
            
            if ignore_keyframe:
                if cmds.nodeType(input_value).find('animCurve') > -1:
                    return False
            
            if input_value:
                return True
        
    return False


def is_connected(node_and_attribute):
    
    if not node_and_attribute:
        return False
    
    input_value = get_attribute_input(node_and_attribute)
    
    if input_value:
        return True
    
    return False

def is_locked(node_and_attribute):
    
    if cmds.getAttr(node_and_attribute, l = True):
        return True
    
    return False

def is_keyed(node_and_attribute):
    input_value = get_attribute_input(node_and_attribute)
    
    if cmds.nodeType(input_value).find('animCurve') > -1:
        return True
    
    return False


def get_node_and_attribute(attribute):
    """
    Split a name between its node and its attribute.
    
    Args:
        attribute (str): attribute name, node.attribute.
        
    Returns:
        list: [node_name, attribute]
    """
    
    split_attribute = attribute.split('.')
            
    if not split_attribute:
        return None, None
    
    node = split_attribute[0]
    
    attr = string.join(split_attribute[1:], '.')
    
    return node, attr

def get_inputs(node, node_only = True):
    """
    Get all the inputs into the specified node.
    
    Args:
        node (str): The name of a node.
        node_only (str): Whether to return the node name or the node name + the attribute eg. 'node_name.attribute'
    
    Returns:
        list: The inputs.
    """
    
    if node_only:
        plugs = False
    if not node_only:
        plugs = True

    return cmds.listConnections(node,
                         connections = False,
                         destination = False,
                         source = True,
                         plugs = plugs,
                         skipConversionNodes = True
                         )

    
def get_outputs(node, node_only = True):
    """
    Get all the outputs from the specified node.
        
    Args:
        node (str): The name of a node.
        node_only (str): Whether to return the node name or the node name + the attribute eg. 'node_name.attribute'
    
    Returns:
        list: The outputs.
    """    
    
    if node_only:
        plugs = False
    if not node_only:
        plugs = True
    
    return cmds.listConnections(node, 
                                connections = plugs, 
                                destination = True, 
                                source = False,
                                plugs = plugs,
                                skipConversionNodes = True)    

def get_attribute_name(node_and_attribute):
    """
    For a string node.attribute, return the attribute portion
    """
    
    split = node_and_attribute.split('.')
    
    attribute = ''
    
    if split and len(split) > 1:
        attribute = string.join(split[1:], '.')
    
    return attribute

def get_attribute_input(node_and_attribute, node_only = False):
    """
    Get the input into the specified attribute.
    
    Args:
        node_and_attribute (str): The node_name.attribute name to find an input into.
        node_only (str): Whether to return the node name or the node name + the attribute eg. 'node_name.attribute'
        
    Returns:
        str: The attribute that inputs into node_and_attribute
    """
    connections = []
    
    if cmds.objExists(node_and_attribute):
        
        
        connections = cmds.listConnections(node_and_attribute, 
                                           plugs = True, 
                                           connections = False, 
                                           destination = False, 
                                           source = True,
                                           skipConversionNodes = True)
        if connections:
            if not node_only:
                return connections[0]
            if node_only:
                return connections[0].split('.')[0]
                
        
def get_attribute_outputs(node_and_attribute, node_only = False):
    """
    Get the outputs from the specified attribute.
    
    Args:
        node_and_attribute (str): The node_name.attribute name to find outputs.
        node_only (str): Whether to return the node name or the node name + the attribute eg. 'node_name.attribute'
        
    Returns:
        str: The nodes that node_and_attribute connect into.
    """    
    if cmds.objExists(node_and_attribute):
        
        plug = True
        if node_only:
            plug = False
        
        return cmds.listConnections(node_and_attribute, 
                                    plugs = plug, 
                                    connections = False, 
                                    destination = True, 
                                    source = False,
                                    skipConversionNodes = True)

def transfer_attribute_values(source_node, target_node, keyable_only = True):
    
    attrs = cmds.listAttr(source_node, k = keyable_only)
    
    for attr in attrs:
        
        try:
            value = cmds.getAttr('%s.%s' % (source_node, attr))
        except:
            continue
        
        try:
            cmds.setAttr('%s.%s' % (target_node, attr), value)
        except:
            pass
    
    
def get_attribute_values(node, keyable_only = True):
    
    attrs = cmds.listAttr(node, k = keyable_only, v = True)
    
    values = {}
    
    for attr in attrs:
        
        try:
            value = cmds.getAttr('%s.%s' % (node, attr))
            
            values[attr] = value
        except:
            continue
        
    return values
        
def set_attribute_values(node, values):
    
    
    for attr in values:
        
        value = values[attr]
        
        try:
            cmds.setAttr('%s.%s' % (node, attr), value)
        except:
            pass


def transfer_variables():
    """
    Not done
    """
    pass

def transfer_output_connections(source_node, target_node):
    """
    Transfer output connections from source_node to target_node.
    
    Args:
        source_node (str): The node to take output connections from.
        target_node (str): The node to transfer output connections to.
    """
    
    outputs = get_outputs(source_node, node_only = False)
    
    if not outputs:
        return
    
    for inc in range(0, len(outputs), 2):
        new_attr = outputs[inc].replace(source_node, target_node)
        
        
        cmds.disconnectAttr(outputs[inc], outputs[inc+1])
        try:
            cmds.connectAttr(new_attr, outputs[inc+1], f = True)
        except:
            vtool.util.warning('Could not connect %s to %s' % (new_attr, outputs[inc+1]))




def set_nonkeyable(node, attributes):
    """
    
    Args:
        node (str): The name of a node
        attributes (list) or (str):  The name of attributes or an attribute to set nonkeyable
    
    """
    
    attributes = vtool.util.convert_to_sequence(attributes)
    
    for attribute in attributes:
        name = '%s.%s' % (node, attribute)
        cmds.setAttr(name, k = False, cb = True)
        if cmds.getAttr(name, type = True) == 'double3':
            
            attributes.append('%sX' % attribute)
            attributes.append('%sY' % attribute)
            attributes.append('%sZ' % attribute)

def hide_attributes(node, attributes):
    """
    Lock and hide the attributes specified in attributes.
    This has been tested on individual attributes like translateX, not attributes like translate.
    
    Args:
        node (str): The name of a node.
        attributes (list): A list of attributes on node to lock and hide. Just the name of the attribute.
    """
    
    attributes = vtool.util.convert_to_sequence(attributes)
    
    for attribute in attributes:
        
        current_attribute = ['%s.%s' % (node, attribute)]
        
        if cmds.getAttr(current_attribute, type = True) == 'double3':
            current_attribute = []
            current_attribute.append('%s.%sX' % (node,attribute))
            current_attribute.append('%s.%sY' % (node,attribute))
            current_attribute.append('%s.%sZ' % (node,attribute))
            
        for sub_attribute in current_attribute:
            cmds.setAttr(sub_attribute, l = True, k = False, cb = False)
        
        
def hide_keyable_attributes(node):
    """
    Lock and hide keyable attributes on node.
    
    Args:
        node (str) The name of a node.
    """
    
    attributes = cmds.listAttr(node, k = True)
    
    if attributes:
        hide_attributes(node, attributes)
    
    if cmds.getAttr('%s.rotateOrder' % node, cb = True):
        hide_rotate_order(node)
 
def hide_translate(node):

    hide_attributes(node,'translate') 
 
def hide_rotate(node):
    
    hide_attributes(node,'rotate')
    hide_attributes(node, 'rotateOrder')

def hide_scale(node):
    
    hide_attributes(node,'scale')

def hide_visibility(node):
  
    hide_attributes(node,'visibility')
  
def lock_attributes(node, bool_value = True, attributes = None, hide = False):
    """
    lock attributes on a node.
    
    Args:
        node (str): The name of the node.
        bool_value (bool): Whether to lock the attributes.
        attributes (list): A list of attributes to lock on node.
        hide (bool): Whether to lock and hide the attributes.
    """
    if not attributes:
        attributes = cmds.listAttr(node, k = True)
    
    if attributes:
        attributes = vtool.util.convert_to_sequence(attributes)
    
    for attribute in attributes:
        attribute_name = '%s.%s' % (node, attribute)
        
        cmds.setAttr(attribute_name, lock = bool_value)
        
        if hide:
            cmds.setAttr(attribute_name, k = False)
            cmds.setAttr(attribute_name, cb = False)
        
def unlock_attributes(node, attributes = [], only_keyable = False):
    """
    unlock attributes on a node.
    
    Args:
        node (str): The name of the node.
        attributes (list): A list of attributes to lock on node. If none given, unlock any that are locked.
        only_keyable (bool): Whether to unlock only the keyable attributes.
    """
    
    attributes = vtool.util.convert_to_sequence(attributes)
    
    if not attributes:
        if only_keyable == False:
            attrs = cmds.listAttr(node, locked = True)
            
        if only_keyable == True:
            attrs = cmds.listAttr(node, locked = True, k = True)
    
    if attributes:
        attrs = attributes
    
    if attrs:
        for attr in attrs:
            cmds.setAttr('%s.%s' % (node, attr), l = False, k = True, cb = True)
            cmds.setAttr('%s.%s' % (node,attr), k = True)
            

def lock_translate_attributes(node):
    lock_attributes(node, attributes = ['translateX','translateY','translateZ'], hide = True)
    
def lock_rotate_attributes(node):
    lock_attributes(node, attributes = ['rotateX','rotateY','rotateZ'], hide = True)

def lock_scale_attributes(node):
    lock_attributes(node, attributes = ['scaleX','scaleY','scaleZ'], hide = True)

def lock_constraint(constraint):
    """
    This will check if the thing being passed in is a constraint.
    
    And then lock the target offsets which can sometimes get messed up in reference.
    
    """
    if cmds.nodeType(constraint).find('Constraint') > -1 and cmds.objExists('%s.target' % constraint):
        
        target_indices = get_indices('%s.target' % constraint)
        
        attributes = ['Translate', 'Rotate']
        axis = ['X','Y','Z']
        
        for index in target_indices:
            for attribute in attributes:
                for a in axis:
                    
                    attribute_name = 'target[%s].targetOffset%s%s' % (index, attribute, a)
                    
                    if cmds.objExists('%s.%s' % (constraint, attribute_name)):
                        cmds.setAttr('%s.%s' % (constraint, attribute_name), l = True)   


def lock_attributes_for_asset(node):
    
    attrs = cmds.listAttr(node, k = True)
    
    if not attrs:
        return
        
    for a in attrs:
        if a == 'visibility':
            continue
        attr_name = '%s.%s' % (node, a)
        if not cmds.objExists(attr_name):
            continue
        
        input_value = get_attribute_input(attr_name)
        
        if not input_value:
            cmds.setAttr(attr_name, l = True)

def lock_hierarchy(top_transform, exclude_transforms = [], skip_of_type = ['ikHandle', 'joint']):
    
    progress = core.ProgressBar()
    
    scope = cmds.listRelatives(top_transform, ad = True, f = True, shapes = False, ni = True)
    
    scope.append(top_transform)
        
    progress.set_count(len(scope))
    
    for thing in scope:
        
        skip = False
        
        if not cmds.objExists(thing):
            skip = True
        if not skip:
            if core.is_a_shape(thing):
                skip = True
        if not skip:
            if cmds.referenceQuery(thing, isNodeReferenced = True):
                skip = True
        if not skip:
            for transform in exclude_transforms:
                split_thing = thing.split('|')
                if split_thing[-1] == transform:
                    skip = True
        if not skip:
            for skip_thing in skip_of_type:
                if cmds.nodeType(thing) == skip_thing:
                    skip = True
        
        if skip == True:
            progress.inc()
            continue
        
        nice_name = core.get_basename(thing)
        
        progress.status('Locking: %s' % nice_name)
        
        lock_constraint(thing)
        lock_attributes_for_asset(thing)
        
        progress.inc()
        
        if progress.break_signaled():
            break
        
    progress.end()
        
def remove_user_defined(node):
    """
    Removes user defined attributes from a node.
    """
    
    unlock_attributes(node)
    
    attrs = cmds.listAttr(node, ud = True)
    
    if not attrs:
        return
    
    for attr in attrs:
        
        try:
            unlock_attributes(node, attr)
            disconnect_attribute(attr)
            cmds.deleteAttr('%s.%s' % (node, attr))
        except:
            pass

def set_color(nodes, color):
    """
    Set the override color for the nodes in nodes.
    
    Args:
        nodes (list): A list of nodes to change the override color.
        color (int): The color index to set override color to.
    """
    
    nodes = vtool.util.convert_to_sequence(nodes)
    
    for node in nodes:
        
        overrideEnabled = '%s.overrideEnabled' % node
        overrideColor = '%s.overrideColor' % node
        
        if cmds.objExists(overrideEnabled):
            cmds.setAttr(overrideEnabled, 1)
            cmds.setAttr(overrideColor, color)

def set_color_rgb(nodes, r = 0, g = 0, b = 0):
    """
    Maya 2015 and above.
    Set to zero by default.
    Max value is 1.0.
    """
    nodes = vtool.util.convert_to_sequence(nodes)
    
    for node in nodes:
        
        overrideRGB = '%s.overrideRGBColors' % node
        overrideEnabled = '%s.overrideEnabled' % node
        overrideColor = '%s.overrideColorRGB' % node
        
        if cmds.objExists(overrideEnabled) and cmds.objExists(overrideRGB):
            cmds.setAttr(overrideRGB, 1)
            cmds.setAttr(overrideEnabled, 1)
            
            
            cmds.setAttr(overrideColor, r,g,b)
            

def get_color_rgb(node, as_float = False):
    
    color = get_color(node, as_float)
    if type(color) == int:
        color = color_to_rgb(color)
        
    return color
        
def get_color(node, as_float = False):
    
    
    
    if not cmds.objExists('%s.overrideColor' % node):
        return 0
    
    if not cmds.getAttr('%s.overrideRGBColors' % node) or not cmds.objExists('%s.overrideRGBColors' % node): 
        color = cmds.getAttr('%s.overrideColor' % node)
        
        return color
            
    if cmds.getAttr('%s.overrideRGBColors' % node): 
        color = cmds.getAttr('%s.overrideColorRGB' % node)
        
        if type(color) == list:
            if len(color) == 1:
                color = color[0]
        
        if type(color) == tuple:
            color = list(color)
        
        if not as_float:
            color[0] = color[0] * 255
            color[1] = color[1] * 255
            color[2] = color[2] * 255
        
        return color


def get_color_of_side(side = 'C', sub_color = False):
    """
    Get the override color for the given side.
    
    Args:
        side (str): 'L','R', 'C'
        sub_color (bool): Whether to return a sub color.
        
    Returns:
        int: A color index for override color.
    """
    
    if vtool.util.is_left(side):
        side = 'L'
    if vtool.util.is_right(side):
        side = 'R'
    if vtool.util.is_center(side):
        side = 'C'
    
    
    if side == None:
        side = 'C'
    
    if not sub_color:
        
        if side == 'L':
            return 6
        
        if side == 'R':
            return 13
        
        if side == 'C':
            return 17
    
    if sub_color:
    
        if side == 'L':
            return 18
        
        if side == 'R':
            return 20
        
        if side == 'C':
            return 21

def color_to_rgb(color_index):
    if color_index > 0:
        values = cmds.colorIndex(color_index, q = True)
        return values
    
    if color_index == 0:
        values = [0,0,0]
        return values

def get_random_color(seed = 0):
    random.seed(seed)
    value = random.uniform(0,1)
    
    hsv = [value, 1, 1]
    
    return colorsys.hsv_to_rgb(hsv[0], hsv[1], hsv[2])

def set_color_saturation(color_rgb, saturation):
    """
    set the saturation component of hsv
    """
    h,s,v = colorsys.rgb_to_hsv(color_rgb[0],color_rgb[1],color_rgb[2])
    
    s = saturation
    
    r,g,b = colorsys.hsv_to_rgb(h, s, v)
    
    return r,g,b
    
def set_color_value(color_rgb, value):
    """
    set the value component of hsv
    """
    h,s,v = colorsys.rgb_to_hsv(color_rgb[0],color_rgb[1],color_rgb[2])
    
    v = value
    
    r,g,b = colorsys.hsv_to_rgb(h, s, v)
    
    return r,g,b    
    
    
#--- connect

def connect_vector_attribute(source_transform, target_transform, attribute, connect_type = 'plus'):
    """
    Connect an X,Y,Z attribute, eg translate, rotate, scale. 
    
    Args:
        source_transform (str): The name of a transform.
        target_transform (str): The name of a transform.
        attribute (str): eg, translate, rotate, scale.
        connect_type (str): 'plus' or 'multiply'
    
    Returns:
        list: The nodes created.
    """
    axis = ['X','Y','Z']
    
    node = None
    nodes = []
    
    for letter in axis:
        
        source_attribute = '%s.%s%s' % (source_transform, attribute, letter)
        target_attribute = '%s.%s%s' % (target_transform, attribute, letter)
        
        if connect_type == 'plus':
            node = connect_plus(source_attribute,
                                target_attribute)
        
            nodes.append(node)
        
        if connect_type == 'multiply':
            
            if node:
                cmds.connectAttr(source_attribute, '%s.input1%s' % (node,letter))
                cmds.connectAttr('%s.output%s' % (node, letter), target_attribute)
            
            if not node:
                node = connect_multiply(source_attribute,
                                            target_attribute)
                
    if not nodes:
        nodes = node
            
    return nodes
    

def connect_transforms(source_transform, target_transform):
    """
    Connect translate, rotate, scale from souce to target.
    """
    
    connect_translate(source_transform, target_transform)
    connect_rotate(source_transform, target_transform)
    connect_scale(source_transform, target_transform)

def connect_translate(source_transform, target_transform):
    """
    Connect translate attributes
    
    Args:
        source_transform (str): The name of a transform.
        target_transform (str): The name of a transform.
    """
    
    connect_vector_attribute(source_transform, target_transform, 'translate')

def connect_rotate(source_transform, target_transform):
    """
    Connect rotate attributes. This will automatically connect rotateOrder from source to target, if not already connected.
    
    Args:
        source_transform (str): The name of a transform.
        target_transform (str): The name of a transform.
    """
    
    connect_vector_attribute(source_transform, target_transform, 'rotate')
    try:
        cmds.connectAttr('%s.rotateOrder' % source_transform, '%s.rotateOrder' % target_transform)
    except:
        pass
        #vtool.util.show('Could not connect %s.rotateOrder into %s.rotateOrder. This could cause issues if rotate order changed.' % (source_transform, target_transform))
        
    
def connect_scale(source_transform, target_transform):
    """
    Connect scale attributes.
    
    Args:
        source_transform (str): The name of a transform.
        target_transform (str): The name of a transform.
    """
    
    connect_vector_attribute(source_transform, target_transform, 'scale')

def connect_translate_into_pivots(source_transform, target_transform):
    
    cmds.connectAttr('%s.translateX' % source_transform, '%s.rotatePivotX' % target_transform)
    cmds.connectAttr('%s.translateY' % source_transform, '%s.rotatePivotY' % target_transform)
    cmds.connectAttr('%s.translateZ' % source_transform, '%s.rotatePivotZ' % target_transform)

    cmds.connectAttr('%s.translateX' % source_transform, '%s.scalePivotX' % target_transform)
    cmds.connectAttr('%s.translateY' % source_transform, '%s.scalePivotY' % target_transform)
    cmds.connectAttr('%s.translateZ' % source_transform, '%s.scalePivotZ' % target_transform)

def connect_translate_plus(source_transform, target_transform):
    """
    Connect translate attributes. If target_transform already has input connections, reconnect with plusMinusAverage to accomodate both.
    
    Args:
        source_transform (str): The name of a transform.
        target_transform (str): The name of a transform.
        
    Returns:
        str: the name of the plusMinusAverage node.
    """
    plus = cmds.createNode('plusMinusAverage', n = 'plus_%s' % target_transform)
    
    input_x = get_attribute_input('%s.translateX' % target_transform)
    input_y = get_attribute_input('%s.translateY' % target_transform)
    input_z = get_attribute_input('%s.translateZ' % target_transform)
    
    value_x = cmds.getAttr('%s.translateX' % source_transform)
    value_y = cmds.getAttr('%s.translateY' % source_transform)
    value_z = cmds.getAttr('%s.translateZ' % source_transform)
    
    cmds.connectAttr('%s.translateX' % source_transform, '%s.input3D[0].input3Dx' % plus)
    cmds.connectAttr('%s.translateY' % source_transform, '%s.input3D[0].input3Dy' % plus)
    cmds.connectAttr('%s.translateZ' % source_transform, '%s.input3D[0].input3Dz' % plus)
    
    cmds.setAttr('%s.input3D[1].input3Dx' % plus, -1*value_x)
    cmds.setAttr('%s.input3D[1].input3Dy' % plus, -1*value_y)
    cmds.setAttr('%s.input3D[1].input3Dz' % plus, -1*value_z)
    
    disconnect_attribute('%s.translateX' % target_transform)
    disconnect_attribute('%s.translateY' % target_transform)
    disconnect_attribute('%s.translateZ' % target_transform)
    
    cmds.connectAttr('%s.output3Dx' % plus, '%s.translateX' % target_transform)
    cmds.connectAttr('%s.output3Dy' % plus, '%s.translateY' % target_transform)
    cmds.connectAttr('%s.output3Dz' % plus, '%s.translateZ' % target_transform)
    
    if input_x:
        
        cmds.connectAttr(input_x, '%s.input3D[3].input3Dx' % plus)
    if input_y:
        cmds.connectAttr(input_y, '%s.input3D[3].input3Dy' % plus)
    if input_z:
        cmds.connectAttr(input_z, '%s.input3D[3].input3Dz' % plus)
    
    return plus
    
def connect_translate_multiply(source_transform, target_transform, value = 1, respect_value = False):
    """
    Connect translate attributes with a multiplyDivide to multiply the effect.
    
    Args:
        source_transform (str): The name of a transform.
        target_transform (str): The name of a transform.
        value (float): The multiply value. Set to 0.5 to translate target half of what source translates.
        repsect_value (bool): If respect value is True, then add a plus minus average to buffer the multiply divide.
        
    Returns:
        str: the name of the multiplyDivide node. If respect value return [multiply, plus]
    """
    
    target_transform_x = '%s.translateX' % target_transform
    target_transform_y = '%s.translateY' % target_transform
    target_transform_z = '%s.translateZ' % target_transform
    
    target_input_x = get_attribute_input(target_transform_x)
    target_input_y = get_attribute_input(target_transform_y)
    target_input_z = get_attribute_input(target_transform_z)
    
    if target_input_x:
        
        if cmds.nodeType(target_input_x) == 'plusMinusAverage':
            plus = target_input_x.split('.')[0]
            indices = get_indices('%s.input3D' % plus)
            indices = indices[-1]
            
            target_transform_x = '%s.input3D[%s].input3Dx' % (plus, indices)
            target_transform_y = '%s.input3D[%s].input3Dy' % (plus, indices)
            target_transform_z = '%s.input3D[%s].input3Dz' % (plus, indices)
            
        if not cmds.nodeType(target_input_x) == 'plusMinusAverage':
            
            plus = cmds.createNode('plusMinusAverage', n = 'plus_%s' % target_transform)
            
            cmds.connectAttr(target_input_x, '%s.input3D[0].input3Dx' % plus)
            cmds.connectAttr(target_input_y, '%s.input3D[0].input3Dy' % plus)
            cmds.connectAttr(target_input_z, '%s.input3D[0].input3Dz' % plus)
            
            disconnect_attribute(target_transform_x)
            disconnect_attribute(target_transform_y)
            disconnect_attribute(target_transform_z)
            
            cmds.connectAttr('%s.output3Dx' % plus, target_transform_x)
            cmds.connectAttr('%s.output3Dy' % plus, target_transform_y)
            cmds.connectAttr('%s.output3Dz' % plus, target_transform_z)
            
            target_transform_x = '%s.input3D[1].input3Dx' % plus
            target_transform_y = '%s.input3D[1].input3Dy' % plus
            target_transform_z = '%s.input3D[1].input3Dz' % plus
    
    multiply = connect_multiply('%s.translateX' % source_transform, target_transform_x, value, plus = False)

    if respect_value:
            plus = cmds.createNode('plusMinusAverage', n = 'plus_%s' % target_transform)
    
            value_x = cmds.getAttr('%s.translateX' % source_transform)
            value_y = cmds.getAttr('%s.translateY' % source_transform)
            value_z = cmds.getAttr('%s.translateZ' % source_transform)
    
            cmds.connectAttr('%s.translateX' % source_transform, '%s.input3D[0].input3Dx' % plus)
            cmds.connectAttr('%s.translateY' % source_transform, '%s.input3D[0].input3Dy' % plus)
            cmds.connectAttr('%s.translateZ' % source_transform, '%s.input3D[0].input3Dz' % plus)
    
            cmds.setAttr('%s.input3D[1].input3Dx' % plus, -1*value_x)
            cmds.setAttr('%s.input3D[1].input3Dy' % plus, -1*value_y)
            cmds.setAttr('%s.input3D[1].input3Dz' % plus, -1*value_z)

            disconnect_attribute('%s.input1X' % multiply)
    
            cmds.connectAttr('%s.output3Dx' % plus, '%s.input1X' % multiply)
            cmds.connectAttr('%s.output3Dy' % plus, '%s.input1Y' % multiply)
            cmds.connectAttr('%s.output3Dz' % plus, '%s.input1Z' % multiply)
    
    if not respect_value:
        cmds.connectAttr('%s.translateY' % source_transform, '%s.input1Y' % multiply)
        cmds.connectAttr('%s.translateZ' % source_transform, '%s.input1Z' % multiply)
                
    cmds.connectAttr('%s.outputY' % multiply, target_transform_y)
    cmds.connectAttr('%s.outputZ' % multiply, target_transform_z)
    
    try:
        cmds.setAttr('%s.input2Y' % multiply, value)
        cmds.setAttr('%s.input2Z' % multiply, value)
    except:
        pass
    
    if not respect_value:
        return multiply
    if respect_value:
        return multiply, plus


def connect_rotate_multiply(source_transform, target_transform, value = 1, respect_value = False):
    """
    Connect rotate attributes with a multiplyDivide to multiply the effect.
    This is dangerous because rotate is not calculated in the same linear way as translate. 
    Probably shouldn't be used because of Quaternion math. Would be better to use a double orient constraint.
    
    Args:
        source_transform (str): The name of a transform.
        target_transform (str): The name of a transform.
        value (float): The multiply value. Set to 0.5 to rotate target half of what source translates.
        repsect_value (bool): If respect value is True, then add a plus minus average to buffer the multiply divide.
        
    Returns:
        str: the name of the multiplyDivide node. If respect value return [multiply, plus]
    """
    
    target_transform_x = '%s.rotateX' % target_transform
    target_transform_y = '%s.rotateY' % target_transform
    target_transform_z = '%s.rotateZ' % target_transform
    
    target_input_x = get_attribute_input(target_transform_x)
    target_input_y = get_attribute_input(target_transform_y)
    target_input_z = get_attribute_input(target_transform_z)
    
    if target_input_x:
        
        if cmds.nodeType(target_input_x) == 'plusMinusAverage':
            plus = target_input_x.split('.')[0]
            indices = get_indices('%s.input3D' % plus)
            indices = indices[-1]
            
            target_transform_x = '%s.input3D[%s].input3Dx' % (plus, indices)
            target_transform_y = '%s.input3D[%s].input3Dy' % (plus, indices)
            target_transform_z = '%s.input3D[%s].input3Dz' % (plus, indices)
            
        if not cmds.nodeType(target_input_x) == 'plusMinusAverage':
            
            plus = cmds.createNode('plusMinusAverage', n = 'plus_%s' % target_transform)
            
            cmds.connectAttr(target_input_x, '%s.input3D[0].input3Dx' % plus)
            cmds.connectAttr(target_input_y, '%s.input3D[0].input3Dy' % plus)
            cmds.connectAttr(target_input_z, '%s.input3D[0].input3Dz' % plus)
            
            disconnect_attribute(target_transform_x)
            disconnect_attribute(target_transform_y)
            disconnect_attribute(target_transform_z)
            
            cmds.connectAttr('%s.output3Dx' % plus, target_transform_x)
            cmds.connectAttr('%s.output3Dy' % plus, target_transform_y)
            cmds.connectAttr('%s.output3Dz' % plus, target_transform_z)
            
            target_transform_x = '%s.input3D[1].input3Dx' % plus
            target_transform_y = '%s.input3D[1].input3Dy' % plus
            target_transform_z = '%s.input3D[1].input3Dz' % plus
    
    multiply = connect_multiply('%s.rotateX' % source_transform, target_transform_x, value, plus = False)

    if respect_value:
            plus = cmds.createNode('plusMinusAverage', n = 'plus_%s' % target_transform)
    
            value_x = cmds.getAttr('%s.rotateX' % source_transform)
            value_y = cmds.getAttr('%s.rotateY' % source_transform)
            value_z = cmds.getAttr('%s.rotateZ' % source_transform)
    
            cmds.connectAttr('%s.rotateX' % source_transform, '%s.input3D[0].input3Dx' % plus)
            cmds.connectAttr('%s.rotateY' % source_transform, '%s.input3D[0].input3Dy' % plus)
            cmds.connectAttr('%s.rotateZ' % source_transform, '%s.input3D[0].input3Dz' % plus)
    
            cmds.setAttr('%s.input3D[1].input3Dx' % plus, -1*value_x)
            cmds.setAttr('%s.input3D[1].input3Dy' % plus, -1*value_y)
            cmds.setAttr('%s.input3D[1].input3Dz' % plus, -1*value_z)

            disconnect_attribute('%s.input1X' % multiply)
    
            cmds.connectAttr('%s.output3Dx' % plus, '%s.input1X' % multiply)
            cmds.connectAttr('%s.output3Dy' % plus, '%s.input1Y' % multiply)
            cmds.connectAttr('%s.output3Dz' % plus, '%s.input1Z' % multiply)
    
    if not respect_value:
        cmds.connectAttr('%s.rotateY' % source_transform, '%s.input1Y' % multiply)
        cmds.connectAttr('%s.rotateZ' % source_transform, '%s.input1Z' % multiply)
                
    cmds.connectAttr('%s.outputY' % multiply, target_transform_y)
    cmds.connectAttr('%s.outputZ' % multiply, target_transform_z)
    
    try:
        cmds.setAttr('%s.input2Y' % multiply, value)
        cmds.setAttr('%s.input2Z' % multiply, value)
    except:
        pass
    
    if not respect_value:
        return multiply
    if respect_value:
        return multiply, plus
    
def connect_scale_multiply(source_transform, target_transform, value = 1, respect_value = False):
    """
    Never use. 
    """
    target_transform_x = '%s.scaleX' % target_transform
    target_transform_y = '%s.scaleY' % target_transform
    target_transform_z = '%s.scaleZ' % target_transform
    
    target_input_x = get_attribute_input(target_transform_x)
    target_input_y = get_attribute_input(target_transform_y)
    target_input_z = get_attribute_input(target_transform_z)
    
    if target_input_x:
        
        if cmds.nodeType(target_input_x) == 'plusMinusAverage':
            plus = target_input_x.split('.')[0]
            indices = get_indices('%s.input3D' % plus)
            indices = indices[-1]
            
            target_transform_x = '%s.input3D[%s].input3Dx' % (plus, indices)
            target_transform_y = '%s.input3D[%s].input3Dy' % (plus, indices)
            target_transform_z = '%s.input3D[%s].input3Dz' % (plus, indices)
            
        if not cmds.nodeType(target_input_x) == 'plusMinusAverage':
            
            plus = cmds.createNode('plusMinusAverage', n = 'plus_%s' % target_transform)
            
            cmds.connectAttr(target_input_x, '%s.input3D[0].input3Dx' % plus)
            cmds.connectAttr(target_input_y, '%s.input3D[0].input3Dy' % plus)
            cmds.connectAttr(target_input_z, '%s.input3D[0].input3Dz' % plus)
            
            disconnect_attribute(target_transform_x)
            disconnect_attribute(target_transform_y)
            disconnect_attribute(target_transform_z)
            
            cmds.connectAttr('%s.output3Dx' % plus, target_transform_x)
            cmds.connectAttr('%s.output3Dy' % plus, target_transform_y)
            cmds.connectAttr('%s.output3Dz' % plus, target_transform_z)
            
            target_transform_x = '%s.input3D[1].input3Dx' % plus
            target_transform_y = '%s.input3D[1].input3Dy' % plus
            target_transform_z = '%s.input3D[1].input3Dz' % plus
    
    multiply = connect_multiply('%s.scaleX' % source_transform, target_transform_x, value, plus = False)

    if respect_value:
            plus = cmds.createNode('plusMinusAverage', n = 'plus_%s' % target_transform)
    
            value_x = cmds.getAttr('%s.scaleX' % source_transform)
            value_y = cmds.getAttr('%s.scaleY' % source_transform)
            value_z = cmds.getAttr('%s.scaleZ' % source_transform)
    
            cmds.connectAttr('%s.scaleX' % source_transform, '%s.input3D[0].input3Dx' % plus)
            cmds.connectAttr('%s.scaleY' % source_transform, '%s.input3D[0].input3Dy' % plus)
            cmds.connectAttr('%s.scaleZ' % source_transform, '%s.input3D[0].input3Dz' % plus)
    
            cmds.setAttr('%s.input3D[1].input3Dx' % plus, -1*value_x)
            cmds.setAttr('%s.input3D[1].input3Dy' % plus, -1*value_y)
            cmds.setAttr('%s.input3D[1].input3Dz' % plus, -1*value_z)

            disconnect_attribute('%s.input1X' % multiply)
    
            cmds.connectAttr('%s.output3Dx' % plus, '%s.input1X' % multiply)
            cmds.connectAttr('%s.output3Dy' % plus, '%s.input1Y' % multiply)
            cmds.connectAttr('%s.output3Dz' % plus, '%s.input1Z' % multiply)
    
    if not respect_value:
        cmds.connectAttr('%s.scaleY' % source_transform, '%s.input1Y' % multiply)
        cmds.connectAttr('%s.scaleZ' % source_transform, '%s.input1Z' % multiply)
                
    cmds.connectAttr('%s.outputY' % multiply, target_transform_y)
    cmds.connectAttr('%s.outputZ' % multiply, target_transform_z)
    
    try:
        cmds.setAttr('%s.input2Y' % multiply, value)
        cmds.setAttr('%s.input2Z' % multiply, value)
    except:
        pass
    
    if not respect_value:
        return multiply
    if respect_value:
        return multiply, plus
    

def connect_visibility(attribute_name, target_node, value = 1):
    """
    Connect the visibility into an attribute
    
    Args:
        attribute_name (str): The node.attribute name of an attribute. Does not have to exists. Will be created if doesn't exist.
        target_node (str): The target node to connect attribute_name into.
        value (bool): 0 or 1 whether you want the visibility on or off by default.
    """
    nodes = vtool.util.convert_to_sequence(target_node)
    
    if not cmds.objExists(attribute_name):
        split_name = attribute_name.split('.')
        cmds.addAttr(split_name[0], ln = split_name[1], at = 'bool',dv = value,k = True)
        set_nonkeyable(split_name[0], [split_name[1]])
        
    for thing in nodes: 
        
        if not is_connected('%s.visibility' % thing):
            cmds.connectAttr(attribute_name, '%s.visibility' % thing)
        else:
            vtool.util.warning( attribute_name + ' and ' + thing + '.visibility are already connected')
        
def connect_plus_and_value(source_attribute, target_attribute, value):
    
    target_attribute_name = target_attribute.replace('.', '_')
    
    plus = cmds.createNode('plusMinusAverage', n = 'plusMinusAverage_%s' % target_attribute_name)
    
    cmds.connectAttr( source_attribute , '%s.input1D[0]' % plus)
    
    cmds.setAttr('%s.input1D[1]' % plus, value)
    
    cmds.connectAttr('%s.output1D' % plus, target_attribute, f = True)
    
    
    
    return plus

def connect_plus(source_attribute, target_attribute, respect_value = False):
    """
    Connect source_attribute into target_attribute with a plusMinusAverage inbetween.
    
    Args:
        source_attribute (str): The node.attribute name of an attribute.
        target_attribute (str): The node.attribute name of an attribute.
        respect_value (bool): Whether to edit the input1D list to accomodate for values in the target attribute.
        
    Returns:
        str: The name of the plusMinusAverage node
    """
    
    if cmds.isConnected(source_attribute, target_attribute):
        return
    
    input_attribute = get_attribute_input( target_attribute )
    
    value = cmds.getAttr(target_attribute)
    
    if not input_attribute and not respect_value:
        cmds.connectAttr(source_attribute, target_attribute)
        return

    if input_attribute:
        if cmds.nodeType(input_attribute) == 'plusMinusAverage':
            
            plus = input_attribute.split('.')
            plus = plus[0]
            
            if cmds.getAttr('%s.operation' % plus) == 1:
                
                slot = get_available_slot('%s.input1D' % plus)
                
                cmds.connectAttr(source_attribute, '%s.input1D[%s]' % (plus, slot) )                   
                
                return plus
        

    target_attribute_name = target_attribute.replace('.', '_')
        
    plus = cmds.createNode('plusMinusAverage', n = 'plusMinusAverage_%s' % target_attribute_name)
    
    cmds.connectAttr( source_attribute , '%s.input1D[1]' % plus)
    
    if input_attribute:
        cmds.connectAttr( input_attribute, '%s.input1D[0]' % plus)
        
        new_value = cmds.getAttr(target_attribute) 
        
        if abs(new_value) - abs(value) > 0.01:
            cmds.setAttr('%s.input1D[2]' % plus, value)
        
    if not input_attribute and respect_value:
        cmds.setAttr('%s.input1D[0]' % plus, value)
    
    cmds.connectAttr('%s.output1D' % plus, target_attribute, f = True)
    
    return plus

def connect_plus_new(source_attribute, target_attribute, respect_value = False):
    """
    Not in use. Connect source_attribute into target_attribute with a plusMinusAverage inbetween.
    Tried to make it better, but isn't.
    
    Args:
        source_attribute (str): The node.attribute name of an attribute.
        target_attribute (str): The node.attribute name of an attribute.
        respect_value (bool): Whether to edit the input1D list to accomodate for values in the target attribute.
        
    Returns:
        str: The name of the plusMinusAverage node
    """
    
    if cmds.isConnected(source_attribute, target_attribute):
        return
    
    output_value = 0
    source_value = 0
            
    if respect_value:
        output_value = cmds.getAttr(target_attribute)
        source_value = cmds.getAttr(source_attribute)
        
    input_attribute = get_attribute_input( target_attribute )
    
    if not input_attribute and not respect_value:
        cmds.connectAttr(source_attribute, target_attribute)
        return

    if input_attribute:
        
        if cmds.nodeType(input_attribute) == 'plusMinusAverage':
            
            plus = input_attribute.split('.')
            plus = plus[0]
            
            if cmds.getAttr('%s.operation' % plus) == 1:
                
                slot = get_available_slot('%s.input1D' % plus)
                
                cmds.connectAttr(source_attribute, '%s.input1D[%s]' % (plus, slot) )                   
                
                source_value += cmds.getAttr('%s.input1D[0]' % plus)
                
                if respect_value:
                    new_value = output_value - source_value
                    cmds.setAttr('%s.input1D[0]', new_value)
                
                return plus
        

    target_attribute_name = target_attribute.replace('.', '_')
        
    plus = cmds.createNode('plusMinusAverage', n = 'plusMinusAverage_%s' % target_attribute_name)
    
    cmds.connectAttr( source_attribute , '%s.input1D[1]' % plus)
    
    if respect_value:
        new_value = output_value - source_value
        cmds.setAttr('%s.input1D[0]', new_value)
    
    """
    if input_attribute:
        
        slot = get_available_slot('%s.input1D' % plus)
            
        cmds.connectAttr( input_attribute, '%s.input1D[%s]' % (plus, slot))
        
        new_value = cmds.getAttr(target_attribute) 
        
        if abs(new_value) - abs(value) > 0.01:
            cmds.setAttr('%s.input1D[2]' % plus, value)
        
    if not input_attribute and respect_value:
        cmds.setAttr('%s.input1D[0]' % plus, value)
    """
    
    cmds.connectAttr('%s.output1D' % plus, target_attribute, f = True)
    
    return plus

def connect_multiply(source_attribute, target_attribute, value = 0.1, skip_attach = False, plus= True):
    """
    Connect source_attribute into target_attribute with a multiplyDivide inbetween.
    
    Args:
        source_attribute (str): The node.attribute name of an attribute.
        target_attribute (str): The node.attribute name of an attribute.
        skip_attach (bool): Whether to attach the input into target_attribute (if there is one) into input2X of multiplyDivide.
        plus (bool): Whether to fix input connections in target_attribute to plug into a plusMinusAverage. Therefore not losing their influence on the attribute while still multiplying by the source_attribute.
        
    Returns:
        str: The name of the plusMinusAverage node
    """
    input_attribute = get_attribute_input( target_attribute  )

    lock_state = LockState(target_attribute)
    lock_state.unlock()

    new_name = target_attribute.replace('.', '_')
    new_name = new_name.replace('[', '_')
    new_name = new_name.replace(']', '_')

    source_attr_type = cmds.getAttr(source_attribute, type = True)
    attr_type = cmds.getAttr(target_attribute, type = True)
    
    multi = cmds.createNode('multiplyDivide', n = 'multiplyDivide_%s' % new_name)

    if attr_type == 'double3':
        
        if source_attr_type == 'double3':
            
            cmds.connectAttr(source_attribute, '%s.input1' % multi)
        else:
            cmds.connectAttr(source_attribute, '%s.input1X' % multi)
            cmds.connectAttr(source_attribute, '%s.input1Y' % multi)
            cmds.connectAttr(source_attribute, '%s.input1Z' % multi)
        
        cmds.setAttr('%s.input2X' % multi, value)
        cmds.setAttr('%s.input2Y' % multi, value)
        cmds.setAttr('%s.input2Z' % multi, value)
        
        if input_attribute and not skip_attach:
            cmds.connectAttr(input_attribute, '%s.input2' % multi)
        if plus:
            connect_plus('%s.output' % multi, target_attribute)
        if not plus:
            if not cmds.isConnected('%s.output' % multi, target_attribute):
                cmds.connectAttr('%s.output' % multi, target_attribute, f = True)
        
        
    else:
        cmds.connectAttr(source_attribute, '%s.input1X' % multi)
        
        cmds.setAttr('%s.input2X' % multi, value)
    
        if input_attribute and not skip_attach:
            cmds.connectAttr(input_attribute, '%s.input2X' % multi)
            
        if plus:
            connect_plus('%s.outputX' % multi, target_attribute)
        if not plus:
            if not cmds.isConnected('%s.outputX' % multi, target_attribute):
                cmds.connectAttr('%s.outputX' % multi, target_attribute, f = True)
        
    lock_state.restore_initial()
    
    return multi

def output_multiply(source_attribute, value = 1):
    """
    Insert a multiply from the output of a source attribute into all of the inputs of the source attribute
    """
    
    outputs = get_attribute_outputs(source_attribute, node_only =  False)
    
    multiply = None
    
    for output_attr in outputs:
        lock = LockState(output_attr)
        lock.unlock()
        if multiply:
            cmds.connectAttr('%s.outputX' % multiply, output_attr, f = True)
        
        if not multiply:
            
            multiply = insert_multiply(output_attr, value)
            multiply = cmds.rename(multiply, 'multiply_%s' % core.get_basename(source_attribute))
        
        lock.restore_initial()
        
    return multiply
    

def insert_multiply(target_attribute, value = 0.1):
    """
    Insert a multiply divide into the input attribute of target_attribute.
    
    Args:
        target_attribute (str): The node.attribute name of an attribute.
        value (float): The float value to multiply the target_attribute by.
        
    Returns:
        str: The new multiply divide.
    """
    
    new_name = target_attribute.replace('.', '_')
    new_name = new_name.replace('[', '_')
    new_name = new_name.replace(']', '_')
    
    input_attr = get_attribute_input(target_attribute)
    
    multi = cmds.createNode('multiplyDivide', n = 'multiplyDivide_%s' % new_name) 
    
    if input_attr:
        disconnect_attribute(target_attribute)
        cmds.connectAttr(input_attr, '%s.input1X' % multi)
        
    cmds.connectAttr('%s.outputX' % multi, target_attribute)
    
    cmds.setAttr('%s.input2X' % multi, value)
    
    return multi

def insert_blend(target_attribute, value = 1):
    """
    Insert a multiply divide into the input attribute of target_attribute.
    
    Args:
        target_attribute (str): The node.attribute name of an attribute.
        value (float): The float value to blend the target_attribute by.
        
    Returns:
        str: The new blend node
    """
    
    new_name = target_attribute.replace('.', '_')
    new_name = new_name.replace('[', '_')
    new_name = new_name.replace(']', '_')
    
    input_attr = get_attribute_input(target_attribute)
    
    blend = cmds.createNode('blendColors', n = 'blendColors_%s' % new_name) 
    
    if input_attr:
        disconnect_attribute(target_attribute)
        cmds.connectAttr(input_attr, '%s.color1R' % blend)
        
    cmds.connectAttr('%s.outputR' % blend, target_attribute)
    
    cmds.setAttr('%s.color2R' % blend, value)
    
    return blend


def connect_blend(source_attribute1, source_attribute2, target_attribute, value = 0.5 ):
    """
    Connect source 1 and source 2 into the target_attribute with and blendColors node.
    
    Args:
        source_attribute1 (str): The node.attribute name of an attribute.
        source_attribute2 (str): The node.attribute name of an attribute.
        target_attribute (str): The node.attribute name of an attribute.
        value (float): The amount to blend the 2 attributes.
        
    Returns:
        str: The name of the blendColors node
    """
    
    source_attr_name = source_attribute1.replace('.', '_')
    
    blend = cmds.createNode('blendColors', n = 'blendColors_%s' % source_attr_name)
    
    cmds.connectAttr(source_attribute1, '%s.color1R' % blend)
    cmds.connectAttr(source_attribute2, '%s.color2R' % blend)
    
    input_attr = get_attribute_input('%s.outputR' % blend)
    
    if input_attr:
        connect_plus()
        
    if not input_attr:
        cmds.connectAttr('%s.outputR' % blend, target_attribute)
    
    cmds.setAttr('%s.blender' % blend, value)
    
    return blend

def connect_reverse(source_attribute, target_attribute):
    """
    Connect source_attribute into target_attribute with a reverse node inbetween.
    
    Args:
        source_attribute (str): The node.attribute name of an attribute.
        target_attribute (str): The node.attribute name of an attribute.
        
    Returns:
        str: The name of the reverse node
    """
    reverse = cmds.createNode('reverse', n = 'reverse_%s' % source_attribute)
    
    cmds.connectAttr(source_attribute, '%s.inputX' % reverse)
    connect_plus('%s.outputX' % reverse, target_attribute)
    
    return reverse

def connect_equal_condition(source_attribute, target_attribute, equal_value):
    """
    Connect source_attribute into target_attribute with a condition node inbetween.
    
    Args:
        source_attribute (str): The node.attribute name of an attribute.
        target_attribute (str): The node.attribute name of an attribute.
        equal_value (float): The value the condition should be equal to, in order to pass 1. 0 otherwise.
        Good when hooking up enums to visibility.
        
    Returns:
        str: The name of the condition node
    """
    source_attribute_name = source_attribute.replace('.', '_')
    condition = cmds.createNode('condition', n = 'condition_%s' % source_attribute_name)
    
    cmds.connectAttr(source_attribute, '%s.firstTerm' % condition)
    cmds.setAttr('%s.secondTerm' % condition, equal_value)
    
    cmds.setAttr('%s.colorIfTrueR' % condition, 1)
    cmds.setAttr('%s.colorIfFalseR' % condition, 0)
    
    connect_plus('%s.outColorR' % condition, target_attribute)
    
    return condition

def connect_greater_than_condition(source_attribute, target_attribute, greater_than_value):
    """
    Connect source_attribute into target_attribute with a condition node inbetween.
    
    Args:
        source_attribute (str): The node.attribute name of an attribute.
        target_attribute (str): The node.attribute name of an attribute.
        equal_value (float): The value the condition should be equal to, in order to pass 1. 0 otherwise.
        Good when hooking up enums to visibility.
        
    Returns:
        str: The name of the condition node
    """
    source_attribute_name = source_attribute.replace('.', '_')
    condition = cmds.createNode('condition', n = 'condition_%s' % source_attribute_name)
    
    cmds.setAttr('%s.operation' % condition, 2)
    
    cmds.connectAttr(source_attribute, '%s.firstTerm' % condition)
    cmds.setAttr('%s.secondTerm' % condition, greater_than_value)
    
    cmds.setAttr('%s.colorIfTrueR' % condition, 1)
    cmds.setAttr('%s.colorIfFalseR' % condition, 0)
    
    connect_plus('%s.outColorR' % condition, target_attribute)
    
    return condition
        

def connect_less_than_condition(source_attribute, target_attribute, less_than_value):
    """
    Connect source_attribute into target_attribute with a condition node inbetween.
    
    Args:
        source_attribute (str): The node.attribute name of an attribute.
        target_attribute (str): The node.attribute name of an attribute.
        equal_value (float): The value the condition should be equal to, in order to pass 1. 0 otherwise.
        Good when hooking up enums to visibility.
        
    Returns:
        str: The name of the condition node
    """
    source_attribute_name = source_attribute.replace('.', '_')
    condition = cmds.createNode('condition', n = 'condition_%s' % source_attribute_name)
    
    cmds.setAttr('%s.operation' % condition, 4)
    
    cmds.connectAttr(source_attribute, '%s.firstTerm' % condition)
    cmds.setAttr('%s.secondTerm' % condition, less_than_value)
    
    cmds.setAttr('%s.colorIfTrueR' % condition, 1)
    cmds.setAttr('%s.colorIfFalseR' % condition, 0)
    
    connect_plus('%s.outColorR' % condition, target_attribute)
    
    return condition
        

def create_blend_attribute(source, target, min_value = 0, max_value = 10, value = 0):
    """
    Create an attribute to hook into a blendshape.
    
    Args:
        source (str): The node.attr name of an attribute to connect into a blendshape.
        target (str): the blendshape.weight name to connect into.
        
    Returns:
        str: multiplyDivide node.
    """
    if not cmds.objExists(source):
        split_source = source.split('.')
        cmds.addAttr(split_source[0], ln = split_source[1], min = min_value, max = max_value, k = True, dv = value)
        
    multi = connect_multiply(source, target, .1)
    
    return multi
            
def disconnect_attribute(attribute):
    """
    Disconnect an attribute.  Find its input automatically and disconnect it.
    
    Args:
        attribute (str): The name of an attribute that has a connection.
    """
    connection = get_attribute_input(attribute)
    
    if connection:
        
        cmds.disconnectAttr(connection, attribute)

def disconnect_scale(transform_node):
    
    disconnect_attribute('%s.scale' % transform_node)
    disconnect_attribute('%s.scaleX' % transform_node)
    disconnect_attribute('%s.scaleY' % transform_node)
    disconnect_attribute('%s.scaleZ' % transform_node)

def get_indices(attribute):
    """
    Get the index values of a multi attribute.
    
    Args:
        attribute (str): The node.attribute name of a multi attribute. Eg. blendShape1.inputTarget
        
    Returns:
        list: A list of integers that correspond to multi attribute indices.
    """
    
    multi_attributes = cmds.listAttr(attribute, multi = True)
    
    if not multi_attributes:
        return
    
    indices = {}
    
    for multi_attribute in multi_attributes:
        index = re.findall('\d+', multi_attribute)
        
        if index:
            index = int(index[-1])
            indices[index] = None
        
    indices = indices.keys()
    indices.sort()
        
    return indices

def get_available_slot(attribute):
    """
    Find the next available slot in a multi attribute.
    
    Args:
        attribute (str): The node.attribute name of a multi attribute. Eg. blendShape1.inputTarget
        
    Returns:
        int: The next empty slot.
    """
    slots = get_slots(attribute)
    
    if not slots:
        return 0
    
    return int( slots[-1] )+1

def get_slots(attribute):
    """
    Given a multi attribute, get all the slots currently made.
    
    Args:
        attribute (str): The node.attribute name of a multi attribute. Eg. blendShape1.inputTarget 
    
    Returns:
        list: The index of slots that are open.  Indices are returned as str(int)
    """
    slots = cmds.listAttr(attribute, multi = True)
        
    found_slots = []
    
    if not slots:
        return found_slots
    
    for slot in slots:
        index = re.findall('\d+', slot)
        
        if index:
            found_slots.append(index[-1])
            
    return found_slots

def get_slot_count(attribute):
    """
    Get the number of created slots in a multi attribute.
    
    Args:
        attribute (str): The node.attribute name of a multi attribute. Eg. blendShape1.inputTarget
        
    Returns:
        int: The number of open slots in the multi attribute
    """
    
    slots = get_slots(attribute)
    
    if not slots:
        return 0
    
    return len(slots)

def clear_multi(node, attribute_name):
    
    attribute = node + '.' + attribute_name
    
    slots = get_slots(attribute)
    
    for slot in slots:
                
        cmds.removeMultiInstance(attribute + '[%s]' % slot, b = True)

def create_title(node, name, name_list = []):
    """
    Create a enum title attribute on node
    
    Args:
        node (str): The name of a node
        name (str): The title name.
    """
    
    if not cmds.objExists(node):
        vtool.util.warning('%s does not exist to create title on.' % node)
        
    title = MayaEnumVariable(name)
    
    if name_list:
        title.set_enum_names(name_list)
        
    title.create(node)
    
def create_vetala_type(node, value):
    """
    Convenience to tag nodes that are vital to the auto rig.
    """
    
    string_var = MayaStringVariable('vetalaType')
    string_var.set_value(value)
    string_var.set_locked(True)
    string_var.create(node)
    
    return string_var.get_name()

def get_vetala_type(node):
    """
    Get the vetala type of a node.
    """
    string_var = MayaStringVariable('vetalaType')
    string_var.set_node(node)
    value = string_var.get_value()
    
    return value
    
def get_vetala_nodes(vetala_type = None):
    """
    Get vetala nodes in the scene.
    """
    found = []
    
    list_type = None
    
    if vetala_type == 'ShapeComboManager':
        list_type = 'transform'
    
    if not list_type:
        nodes = cmds.ls()
    if list_type:
        nodes = cmds.ls(type = list_type)
    
    for node in nodes:
        found_vetala_type = get_vetala_type(node)
        
        if found_vetala_type:
            if vetala_type:
                if found_vetala_type == vetala_type:
                    found.append(node)
            if not vetala_type:
                found.append(node)
            
    return found
        
      
def has_default_xform_channels(transform, skip_locked = False):

    """
    Zero out the translate and rotate. Set scale to 1.
    
    Args:
        transform (str): The name of a transform node.
    """
    
    channels = ['translate',
                'rotate']
    
    other_channels = ['scale']
    
    all_axis = ['X','Y','Z']
    
    for channel in channels:
        for axis in all_axis:
            
            attr_name = transform + '.' + channel + axis
            
            if skip_locked:
                if is_locked(attr_name):
                    continue
                
            value = cmds.getAttr(attr_name)
            if abs(value) > 0:
                return False
                
            
    for channel in other_channels:
        for axis in all_axis:
            
            attr_name = transform + '.' + channel + axis
            
            if skip_locked:
                if is_locked(attr_name):
                    continue
            
            value = cmds.getAttr(attr_name)
            
            if value != 1:
                return False
    
    return True

    
def zero_xform_channels(transform):
    """
    Zero out the translate and rotate. Set scale to 1.
    
    Args:
        transform (str): The name of a transform node.
    """
    
    channels = ['translate',
                'rotate']
    
    other_channels = ['scale']
    
    all_axis = ['X','Y','Z']
    
    for channel in channels:
        for axis in all_axis:
            try:
                cmds.setAttr(transform + '.' + channel + axis, 0)
            except:
                pass
            
    for channel in other_channels:
        for axis in all_axis:
            try:
                cmds.setAttr(transform + '.' + channel + axis, 1)
            except:
                pass
    
    return

    
@core.undo_chunk
def add_orient_attributes(transform, context_sensitive = False):
    """
    Add orient attributes, used to automatically orient.
    
    Args:
        transform (str): The name of the transform.
    """
    if type(transform) != list:
        transform = [transform]
    
    for thing in transform:
        
        orient = OrientJointAttributes(thing)
        orient.set_default_values(context_sensitive)
        
def remove_orient_attributes(transform):
    if type(transform) != list:
        transform = [transform]
    
    for thing in transform:
        
        orient = OrientJointAttributes(thing)
        orient.delete()
        
def show_rotate_order(transform, value = None):
    
    
    if value == None:
        cmds.setAttr('%s.rotateOrder' % transform, k = True)
    else:
        cmds.setAttr('%s.rotateOrder' % transform, value, k = True, )
        
def hide_rotate_order(transform):
    
    cmds.setAttr('%s.rotateOrder' % transform, k = False, l = False)
    cmds.setAttr('%s.rotateOrder' % transform, cb = False )
        
def add_shape_for_attributes(transforms, shape_name):
    
    transforms = vtool.util.convert_to_sequence(transforms)
    
    locator = None
    
    existed = False
    
    if cmds.objExists(shape_name):
        shape = shape_name
        existed = True
    else:
        locator = cmds.spaceLocator()
        shape = core.get_shapes(locator, shape_type = 'locator', no_intermediate = True)[0]
            
        cmds.setAttr('%s.localScaleX' % shape, 0)
        cmds.setAttr('%s.localScaleY' % shape, 0)
        cmds.setAttr('%s.localScaleZ' % shape, 0)
        hide_attributes(shape, ['localPosition', 'localScale'])
        
        shape = cmds.rename(shape, core.inc_name(shape_name))
        
    
    inc = 0
    
    for transform in transforms:
         
        if inc == 0 and not existed:
            shape = cmds.parent(shape,transform, r = True, s = True)[0]
        else:
            shape = cmds.parent(shape,transform, r = True, s = True,  add = True)[0]
        
        inc += 1
    
    if locator:
        cmds.delete(locator)
        
    return shape

def store_world_matrix_to_attribute(transform, attribute_name = 'origMatrix', skip_if_exists = False):
    
    name = attribute_name 
    
    world_matrix = cmds.getAttr('%s.worldMatrix' % transform)
    
    if cmds.objExists('%s.%s' % (transform, name)):
        if skip_if_exists:
            return
        cmds.setAttr('%s.%s' % (transform, name), l = False)
        cmds.deleteAttr('%s.%s' % (transform, name))
    
    cmds.addAttr(transform, ln = name, at = 'matrix')
    
    cmds.setAttr('%s.%s' % (transform, name), *world_matrix, type = 'matrix', l = True)
    
def search_for_open_input(node_and_attribute):
    inc = 0
    while is_connected(node_and_attribute):
        if inc > 10:
            break
        test_switch = get_attribute_input(node_and_attribute)
        if test_switch:
            if cmds.nodeType(test_switch).find('animCurveT') > -1:
                break
            node_and_attribute = test_switch
        inc += 1
        
    return node_and_attribute

#--- message

def get_message_attributes(node, user_defined = True):
    
    attrs = cmds.listAttr(node, ud = user_defined)
    
    found = []
    
    if attrs:
    
        for attr in attrs:
            
            attr_path = '%s.%s' % (node, attr)
            
            if cmds.getAttr(attr_path, type = True) == 'message':
                found.append(attr)
            
    return found
        
def get_message_input(node, message):
    
    input_value = get_attribute_input('%s.%s' % (node, message), node_only = True)
    
    return input_value
        
def connect_message( input_node, destination_node, attribute ):
    """
    Connect the message attribute of input_node into a custom message attribute on destination_node
    
    Args:
        input_node (str): The name of a node.  If input_node is None then only the attribute is created.
        destination_node (str): The name of a node.
        attribute (str): The name of the message attribute to create and connect into. If already exists than just connect. 
        
    """
    
    current_inc = vtool.util.get_last_number(attribute)
    
    
    if current_inc == None:
        current_inc = 2
    
    test_attribute = attribute
    
    while cmds.objExists('%s.%s' % (destination_node, test_attribute)):
        
        input_value = get_attribute_input('%s.%s' % (destination_node, test_attribute))
        
        if not input_value:
            break
        
        test_attribute = vtool.util.replace_last_number(attribute, str(current_inc))
        #test_attribute = attribute + str(current_inc)
        
        current_inc += 1
        
        if current_inc == 1000:
            break
    
    if not cmds.objExists('%s.%s' % (destination_node, test_attribute)):
        cmds.addAttr(destination_node, ln = test_attribute, at = 'message' )
        
    if input_node:
        if not cmds.objExists(input_node):
            vtool.util.warning('No input node to connect message.')
            return
    
        if not cmds.isConnected('%s.message' % input_node, '%s.%s' % (destination_node, test_attribute)):
            cmds.connectAttr('%s.message' % input_node, '%s.%s' % (destination_node, test_attribute))
    
def connect_group_with_message( input_node, destination_node, attribute ):
    
    if not attribute.startswith('group_'):
    
        attribute_name = 'group_' + attribute
    
    connect_message(input_node, destination_node, attribute_name)
    
def create_multi_message(node, attribute_name):
    
    cmds.addAttr(node,ln=attribute_name,at='message', m=True)
    
def fill_multi_message(node, attribute_name, nodes):
    
    attribute = node + '.' + attribute_name
    
    slot = None
    
    for sub_node in nodes:
        
        if slot == None:
            slot = get_available_slot(attribute)
        else:
            slot += 1
        
        cmds.connectAttr('%s.message' % sub_node, attribute + '[%s]' % slot)
        
def append_multi_message(node, attribute_name, input_node):
    
    attribute = node + '.' + attribute_name
    
    slot = get_available_slot(attribute)
    
    cmds.connectAttr('%s.message' % input_node, attribute + '[%s]' % slot)
    