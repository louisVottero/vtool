# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

import string
import re

import vtool.util
from vtool.util import get_inbetween_vector

if vtool.util.is_in_maya():
    import maya.cmds as cmds
    
import core
import attr
import deform
import anim
import geo
import api
    
#import util

class BlendShape(object):
    """
    Convenience for working with blendshapes.
    
    Args
        blendshape_name (str): The name of the blendshape to work on. 
    """
    def __init__(self, blendshape_name = None):
        self.blendshape = blendshape_name
        
        self.meshes = []
        self.targets = {}
        self.weight_indices = []
        
        if self.blendshape:
            self.set(blendshape_name)
            
        self.mesh_index = 0
        
    def _store_meshes(self):
        if not self.blendshape:
            return
        
        meshes = cmds.deformer(self.blendshape, q = True, geometry = True)
        self.meshes = meshes
        
    def _store_targets(self):
        
        if not self.blendshape:
            
            return
        
        target_attrs = cmds.listAttr(self._get_input_target(0), multi = True)
        
        if not target_attrs:
            return

        alias_index_map = deform.map_blend_target_alias_to_index(self.blendshape)
        
        if not alias_index_map:
            return 
        
        for index in alias_index_map:
            alias = alias_index_map[index]
            
            self._store_target(alias, index)
            
    def _store_target(self, name, index):
        target = BlendShapeTarget(name, index)
        
        self.targets[name] = target
        self.weight_indices.append(index)
        
        self.weight_indices.sort()

    def _get_target_attr(self, name):
        return '%s.%s' % (self.blendshape, name)

    def _get_weight(self, name):
        
        name = name.replace(' ', '_')
        
        target_index = None
                
        if self.targets.has_key(name):
            target_index = self.targets[name].index
        
        if target_index == None:
            return
        
        return '%s.weight[%s]' % (self.blendshape, target_index)

    def _get_weights(self, target_name, mesh_index):
        mesh = self.meshes[mesh_index]
                        
        vertex_count = core.get_component_count(mesh)
        
        attribute = self._get_input_target_group_weights_attribute(target_name, mesh_index)
        
        weights = []
        
        for inc in xrange(0, vertex_count):
            weight = cmds.getAttr('%s[%s]' % (attribute, inc))
            
            weights.append(weight)
            
        return weights      

    def _get_input_target(self, mesh_index = 0):
        
        attribute = [self.blendshape,
                     'inputTarget[%s]' % mesh_index]
        
        attribute = string.join(attribute, '.')
        return attribute

    def _get_input_target_base_weights_attribute(self, mesh_index = 0):
        input_attribute = self._get_input_target(mesh_index)
        
        attribute = [input_attribute,
                     'baseWeights']
        
        attribute = string.join(attribute, '.')
        
        return attribute

    def _get_input_target_group(self, name, mesh_index = 0):
        
        if not self.targets.has_key(name):
            return
        
        target_index = self.targets[name].index
    
        input_attribute = self._get_input_target(mesh_index)
        
        attribute = [input_attribute,
                     'inputTargetGroup[%s]' % target_index]
        
        attribute = string.join(attribute, '.')
        return attribute
    
    def _get_input_target_group_weights_attribute(self, name, mesh_index = 0):
        input_attribute = self._get_input_target_group(name, mesh_index)
        
        attribute = [input_attribute,
                     'targetWeights']
        
        attribute = string.join(attribute, '.')
        
        return attribute        
    
    def _get_mesh_input_for_target(self, name, inbetween = 1):
        
        name = core.get_basename(name, remove_namespace = True)
        
        target_index = self.targets[name].index
        
        value = inbetween * 1000 + 5000
        
        attribute = [self.blendshape,
                     'inputTarget[%s]' % self.mesh_index,
                     'inputTargetGroup[%s]' % target_index,
                     'inputTargetItem[%s]' % value,
                     'inputGeomTarget']
        
        attribute = string.join(attribute, '.')
        
        return attribute
        
    def _get_next_index(self):
        
        if self.weight_indices:
            return ( self.weight_indices[-1] + 1 )
        if not self.weight_indices:
            return 0

    def _disconnect_targets(self):
        for target in self.targets:
            self._disconnect_target(target)
            
    def _disconnect_target(self, name):
        target_attr = self._get_target_attr(name)
        
        connection = attr.get_attribute_input(target_attr)
        
        if not connection:
            return
        
        cmds.disconnectAttr(connection, target_attr)
        
        self.targets[name].connection = connection
    
    def _zero_target_weights(self):
        for target in self.targets:
            attr = self._get_target_attr(target)
            value = cmds.getAttr(attr)
            
            self.set_weight(target, 0)

            self.targets[target].value = value  
        
    def _restore_target_weights(self):
        for target in self.targets:
            self.set_weight(target, self.targets[target].value )
        
    def _restore_connections(self):
        for target in self.targets:
            connection = self.targets[target].connection
            
            if not connection:
                return
            
            cmds.connectAttr(connection, self._get_target_attr(target)) 

    #--- blendshape deformer

    def create(self, mesh):
        """
        Create an empty blendshape on the mesh.
        
        Args
            mesh (str): The name of the mesh.
        """
        blendshape = cmds.deformer(mesh, type = 'blendShape', foc = True)[0]
        
        mesh_name = core.get_basename(mesh)
        
        if not self.blendshape:
            base_mesh_name = core.get_basename(mesh_name, remove_namespace = True)
            new_name = 'blendshape_%s' % base_mesh_name
            self.blendshape = cmds.rename(blendshape, new_name)
        
        self._store_targets()
        self._store_meshes()

    def rename(self, name):
        """
        Rename the blendshape.
        
        Args
            name (str): The ne name of the blendshape.
        """
        self.blendshape = cmds.rename(self.blendshape, name)
        self.set(self.blendshape)

    def set_envelope(self, value):
        """
        Set the envelope value of the blendshape node.
        
        Args
            value (float)
        """
        
        cmds.setAttr('%s.envelope' % self.blendshape, value)
    
    def set(self, blendshape_name):
        """
        Set the name of the blendshape to work on.
        
        Args
            blendshape_name (str): The name of a blendshape.
        """
        self.blendshape = blendshape_name
        self._store_targets()
        self._store_meshes()
        
    def set_mesh_index(self, index):
        self.mesh_index = index
        
    def get_mesh_index(self, mesh):
        
        geo = cmds.blendshape(self.blendshape, q = True, geometry = True)
        
    def get_mesh_count(self):
        meshes = cmds.deformer(self.blendshape, q = True, geometry = True)
        self.meshes = meshes
        
        return len(meshes)
        
    #--- target

    def is_target(self, name):
        """
        Check if name is a target on the blendshape.
        
        Args
            name (str): The name of a target.
        """
        name = core.get_basename(name, remove_namespace = True)
        
        if name in self.targets:
            return True
        
    def is_target_connected(self, name):
        
        attribute = self._get_target_attr(name)
        
        input_value = attr.get_attribute_input(attribute)
        
        if input_value:
            return True
        
        if not input_value:
            return False
        
    def get_target_names(self):
        return self.targets
        
    @core.undo_chunk
    def create_target(self, name, mesh = None, inbetween = 1):
        """
        Add a target to the blendshape.
        
        Args
            name (str): The name for the new target.
            mesh (str): The mesh to use as the target. If None, the target weight attribute will be created only.
            inbetween (float): The inbetween value. 0.5 will have the target activate when the weight is set to 0.5.
        """
        name = name.replace(' ', '_')
        
        if not self.is_target(name):
            
            current_index = self._get_next_index()
            
            self._store_target(name, current_index)
            
            mesh_input = self._get_mesh_input_for_target(name, inbetween)
            
            if mesh and cmds.objExists(mesh):
                cmds.connectAttr( '%s.outMesh' % mesh, mesh_input)
            
            attr_name = core.get_basename(name)
            
            if not cmds.objExists('%s.%s' % (self.blendshape, name)):
                cmds.setAttr('%s.weight[%s]' % (self.blendshape, current_index), 1)
                
                cmds.aliasAttr(attr_name, '%s.weight[%s]' % (self.blendshape, current_index))
                cmds.setAttr('%s.weight[%s]' % (self.blendshape, current_index), 0)
            
            attr = '%s.%s' % (self.blendshape, attr_name)
            return attr
            
        if self.is_target(name):            
            vtool.util.show('Could not add target %s, it already exist.' % name)
       
    
    def insert_target(self, name, mesh, index):
        """
        Not implemented.
        """
        pass
           
    
    def replace_target(self, name, mesh, leave_connected = False):
        """
        Replace the mesh at the target.
        
        Args
            name (str): The name of a target on the blendshape.
            mesh (str): The mesh to connect to the target.
        """
        
        if not cmds.objExists(mesh):
            return
        
        if not mesh:
            return
        
        name = name.replace(' ', '_')
        
        if self.is_target(name):
            
            mesh_input = self._get_mesh_input_for_target(name)
            current_input = attr.get_attribute_input(mesh_input)
            
            if not cmds.isConnected('%s.outMesh' % mesh, mesh_input):
                
                if current_input:
                    attr.disconnect_attribute(mesh_input)
                
                cmds.connectAttr('%s.outMesh' % mesh, mesh_input)
                
                if not leave_connected:
                    cmds.disconnectAttr('%s.outMesh' % mesh, mesh_input)
                
                
        if not self.is_target(name):
            vtool.util.show('Could not replace target %s, it does not exist' % name)
        
    def remove_target(self, name):
        """
        Remove the named target.
        
        Args
            name (str): The name of a target on the blendshape.
        """
        
        target_group = self._get_input_target_group(name)
                
        cmds.removeMultiInstance(target_group, b = True)
        weight_attr = self._get_weight(name)
        if weight_attr:
            cmds.removeMultiInstance(weight_attr, b = True)
        
        self.weight_indices.remove( self.targets[name].index )
        self.targets.pop(name)
        
        cmds.aliasAttr('%s.%s' % (self.blendshape, name), rm = True)
        
        self.weight_indices.sort()
       
    def disconnect_target(self, name, inbetween = 1):
        """
        Disconnect a target on the blendshape.
        
        Args
            name (str): The name of a target on the blendshape.
            inbetween (float): 0-1 value of an inbetween to disconnect.
        """
        target = self._get_mesh_input_for_target(name, inbetween)
        
        attr.disconnect_attribute(target)
       
    def rename_target(self, old_name, new_name):
        """
        Rename a target on the blendshape.
        
        Args
            old_name (str): The current name of the target.
            new_name (str): The new name to give the target.
        """
        if not self.targets.has_key(old_name):
            return old_name
        
        if self.targets.has_key(new_name):
            return old_name
        
        old_name = old_name.replace(' ', '_')
        new_name = new_name.replace(' ', '_')
        
        weight_attr = self._get_weight(old_name)
        index = self.targets[old_name].index
        
        cmds.aliasAttr('%s.%s' % (self.blendshape, old_name), rm = True)
        cmds.aliasAttr(new_name, weight_attr)
        
        self.targets.pop(old_name)
        self._store_target(new_name, index)
        
        return new_name
    
    def recreate_target(self, name, value = 1.0, mesh = None):
        """
        Recreate a target on a new mesh from a blendshape. 
        If you wrap a mesh to the blendshaped mesh, you can specify it with the mesh arg.
        The target will be recreated from the mesh specified.
        
        Args
            name (str): The name of a target.
            value (float):  The weight value to recreate the target it.
            mesh (float): The mesh to duplicate. This can be a mesh that doesn't have the blendshape in its deformation stack.
            
        Return 
            str: The name of the recreated target.
        """
        if not self.is_target(name):
            return
        
        new_name = core.inc_name(name)
        
        if not value == -1:
            self._disconnect_targets()
            self._zero_target_weights()
            self.set_weight(name, value)
        
        output_attribute = '%s.outputGeometry[%s]' % (self.blendshape, self.mesh_index)
        
        if not mesh:
            mesh = cmds.deformer(self.blendshape, q = True, geometry = True)[0]
        
        if mesh:
            new_mesh = cmds.duplicate(mesh, name = new_name)[0]
            
            cmds.connectAttr(output_attribute, '%s.inMesh' % new_mesh)
            cmds.disconnectAttr(output_attribute, '%s.inMesh' % new_mesh)
            
        if not value == -1:
            self._restore_target_weights()
            self._restore_connections()
        
        
        return new_mesh
        
    def recreate_all(self, mesh = None):
        """
        Recreate all the targets on new meshes from the blendshape.
        
        If you wrap a mesh to the blendshaped mesh, you can specify it with the mesh arg.
        The target will be recreated from the mesh specified.
        
        Args
            mesh (float): The mesh to duplicate. This can be a mesh that doesn't have the blendshape in its deformation stack.
            
        Return 
            str: The name of the recreated target.
        """
    
        self._disconnect_targets()
        self._zero_target_weights()
        
        meshes = []
        
        for target in self.targets:
            new_name = core.inc_name(target)
            
            self.set_weight(target, 1)
                    
            output_attribute = '%s.outputGeometry[%s]' % (self.blendshape, self.mesh_index)
            
            if not mesh:
                mesh = cmds.deformer(self.blendshape, q = True, geometry = True)[0]
            
            if mesh:
                new_mesh = cmds.duplicate(mesh, name = new_name)[0]
                
                cmds.connectAttr(output_attribute, '%s.inMesh' % new_mesh)
                cmds.disconnectAttr(output_attribute, '%s.inMesh' % new_mesh)
                
            self.set_weight(target, 0)
                
            meshes.append(new_mesh)
        
        self._restore_connections()
        self._restore_target_weights()
        
        return meshes
    
    def set_targets_to_zero(self):
        """
        Set all the target weights to zero.
        
        """
        self._zero_target_weights()
        
    
    #--- weights
        
    def set_weight(self, name, value):
        """
        Set the weight of a target.
        
        Args
            name (str): The name of a target.
            value (float): The value to set the target to.
        """
        if self.is_target(name):
            
            attribute_name = self._get_target_attr(name)
            
            if not cmds.getAttr(attribute_name, l = True):
                
                cmds.setAttr(attribute_name, value)
    

    
    def set_weights(self, weights, target_name = None, mesh_index = 0):
        """
        Set the vertex weights on the blendshape. If no taget name is specified than the base weights are changed.
        
        Args
            weights (list): A list of weight values. If a float is given, the float will be converted into a list of the same float with a count equal to the number of vertices.
            target_name (str): The name of the target.  If no target given, return the overall weights for the blendshape. 
            mesh_index (int): The index of the mesh in the blendshape. If the blendshape is affecting multiple meshes. Usually index is 0.
        """
        
        mesh = self.meshes[mesh_index]
        
        vertex_count  = core.get_component_count(mesh)
        
        weights = vtool.util.convert_to_sequence(weights)
        
        if len(weights) == 1:
            weights = weights * vertex_count
        
        inc = 0
        
        if target_name == None:
            
            attribute = self._get_input_target_base_weights_attribute(mesh_index)
            
            for weight in weights:     
                cmds.setAttr('%s[%s]' % (attribute, inc), weight)
                inc += 1
                
        if target_name:
            
            attribute = self._get_input_target_group_weights_attribute(target_name, mesh_index)
            
            for weight in weights:
                cmds.setAttr('%s[%s]' % (attribute, inc), weight)
                inc += 1
        
    
        
    def get_weights(self, target_name = None, mesh_index = 0 ):
        
        mesh = self.meshes[mesh_index]
        
        vertex_count  = core.get_component_count(mesh)
        
        
        if target_name == None:
        
            weights = []
        
            for inc in xrange(0, vertex_count):    
                attribute = self._get_input_target_base_weights_attribute(mesh_index)
                
                weight = cmds.getAttr('%s[%s]' % (attribute, inc))
                weights.append(weight)
            
        if target_name:
            
            weights = []
            
            for inc in xrange(0, vertex_count):
                attribute = self._get_input_target_group_weights_attribute(target_name, mesh_index)
                
                weight = cmds.getAttr('%s[%s]' % (attribute, inc))
                weights.append(weight)
            
        return weights
        
    def set_invert_weights(self, target_name = None, mesh_index = 0):
        """
        Invert the blendshape weights at the target. If no target given, the base weights are inverted.
        
        Args
            target_name (str): The name of a target.
            mesh_index (int): The index of the mesh in the blendshape. If the blendshape is affecting multiple meshes. Usually index is 0.
        """
        
        weights = self._get_weights(target_name, mesh_index)
        
        new_weights = []
        
        for weight in weights:
            
            new_weight = 1 - weight
            
            new_weights.append(new_weight)
                    
        self.set_weights(new_weights, target_name, mesh_index)
    
    def disconnect_inputs(self):
        self._disconnect_targets()
    
    def reconnect_inputs(self):
        self._restore_connections()
    
class BlendShapeTarget(object):
    """
    Convenience for storing target information.
    """
    def __init__(self, name, index):
        self.name = name
        self.index = index
        self.connection = None
        self.value = 0
        
        
class ShapeComboManager(object):
    """
    WIP. Convenience for editing blendshape combos. 
    """
    def __init__(self):
        
        
        self.setup_group = None
        self.setup_prefix = 'shapeCombo'
        self.vetala_type = 'ShapeComboManager'
        self.home = 'home'
        self.blendshape = None
    
    def _get_mesh(self):
        
        mesh = attr.get_attribute_input( '%s.mesh' % self.setup_group, node_only = True )
        
        if not mesh:
            return
        
        return mesh
    
    def _get_home_mesh(self):
        if not cmds.objExists('%s.home' % self.setup_group):
            return
        
        mesh = attr.get_attribute_input( '%s.home' % self.setup_group, node_only = True )
        
        if not mesh:
            return
        
        return mesh
         
    def _get_blendshape(self):
        
        mesh = self._get_mesh()
        
        if not mesh:
            return
        
        blendshape = deform.find_deformer_by_type(mesh, 'blendShape')
        
        self.blendshape = BlendShape(blendshape)
        
        if not blendshape:
            return None
        
        return self.blendshape
    
    def _create_blendshape(self):
        
        mesh = self._get_mesh()
        
        if not mesh:
            return
        
        found = deform.find_deformer_by_type(mesh, 'blendShape')
        
        blendshape = BlendShape()
        
        if found:
            blendshape.set_targets_to_zero()
            return
        
        
        blendshape.create(mesh)
        
        blendshape.rename('blendshape_%s' % mesh)
        
    def _create_home(self, mesh):
        home = self._get_home_mesh()
        
        if home:
            cmds.delete(home)
            
        env_history = deform.EnvelopeHistory(mesh)
        env_history.turn_off()
            
        self.home = cmds.duplicate(mesh, n = 'home_%s' % mesh)[0]
        
        env_history.turn_on(True)
        
        cmds.parent(self.home, self.setup_group)
        attr.connect_message(self.home, self.setup_group, 'home')
        
        cmds.hide(self.home)
    
    def _is_variable(self, target):
        if cmds.objExists('%s.%s' % (self.setup_group, target)):
            return True
        
        return False
    
    def _get_variable_name(self, target):
        
        return '%s.%s' % (self.setup_group, target)
                    
    def _get_variable(self, target):
        attributes = attr.Attributes(self.setup_group)
        
        var = attributes.get_variable(target)
        
        return var
    
    def _add_variable(self, shape):
        
        shape = core.get_basename(shape, remove_namespace = True)
        
        var = attr.MayaNumberVariable(shape)
        #var.set_min_value(0)
        #var.set_max_value(1)
        
        #if self.is_negative(shape) or self.has_negative(shape):
            #var.set_min_value(-1)
        
        var.set_variable_type('float')
        var.create(self.setup_group)
    
    def _get_combo_delta(self, corrective_mesh, shapes, home):
        
        temp_targets = []
        
        for shape in shapes:
            if self.blendshape.is_target(shape):
                new_shape = self.blendshape.recreate_target(shape)
                temp_targets.append(new_shape)
        
        delta = deform.get_blendshape_delta(home, temp_targets, corrective_mesh, replace = False)
        
        cmds.delete(temp_targets)
        
        return delta
                
    def _find_manager_for_mesh(self, mesh):
        
        managers = attr.get_vetala_nodes('ShapeComboManager')
        
        for manager in managers:
            
            found_mesh = attr.get_attribute_input('%s.mesh' % manager, node_only = True)
            
            if found_mesh == mesh:
                return manager
            
    def _remove_target_keyframe(self, shape_name):
        
        attribute = '%s.%s' % (self.blendshape.blendshape, shape_name)
        
        keyframe = anim.get_keyframe(attribute)
        
        if keyframe:
            cmds.delete(keyframe)
            
    def _get_target_keyframe(self, shape_name):
        
        attribute = '%s.%s' % (self.blendshape.blendshape, shape_name)
        
        keyframe = anim.get_keyframe(attribute)
        
        if keyframe:
            return keyframe
            
    def _setup_shape_connections(self, name):
        
        name = core.get_basename(name, remove_namespace = True)
        
        blendshape = self.blendshape
        
        blend_attr = '%s.%s' % (blendshape.blendshape, name)

        inbetween_parent = self.get_inbetween_parent(name)
        
        if inbetween_parent:
            name = inbetween_parent
        
        has_negative = self.has_negative(name)
        
        setup_name = name
        
        inbetweens = self.get_inbetweens(name)
        
        negative_value = 1
        
        negative_parent = self.get_negative_parent(name)
        if negative_parent:
            
            setup_name = negative_parent
            
            if negative_parent:
                negative_value = -1
                
        setup_attr = '%s.%s' % (self.setup_group, setup_name)
                
        self._remove_target_keyframe(name)
        
        if not inbetweens:
            value = 1
            value = value*negative_value
            
            infinite_value = True
            
            if has_negative:
                infinite_value = 'post_only'
            if negative_parent:
                infinite_value = 'pre_only'
            
            anim.quick_driven_key(setup_attr, blend_attr, [0,value], [0,1], tangent_type = 'clamped', infinite = infinite_value)
            
            if negative_parent:
                
                keyframe = self._get_target_keyframe(negative_parent)
                
                key = api.KeyframeFunction(keyframe)
                key.set_pre_infinity(key.constant)
            
        if inbetweens:
            
            values, value_dict = self.get_inbetween_values(name, inbetweens)
            
            last_control_value = 0
            
            value_count = len(values)
            
            first_value = None
            
            for inc in xrange(0, value_count):
                
                inbetween = value_dict[values[inc]]
                
                blend_attr = '%s.%s' % (blendshape.blendshape, inbetween)
                
                self._remove_target_keyframe(inbetween)
                
                control_value = values[inc] *.01 * negative_value
                
                if inc == 0:
                    
                    pre_value = 'pre_only'
                    
                    if not has_negative:
                        pre_value = False
                    if negative_parent:
                        pre_value = False
                    
                    anim.quick_driven_key(setup_attr, blend_attr, [last_control_value, control_value], [0, 1], tangent_type='linear', infinite = pre_value)
                    first_value = last_control_value
                    second_value = control_value
                
                if inc > 0:
                    anim.quick_driven_key(setup_attr, blend_attr, [last_control_value, control_value], [0, 1], tangent_type= 'linear')
                    
                
                if value_count > inc+1:

                    future_control_value = values[inc+1] *.01 * negative_value
                    anim.quick_driven_key(setup_attr, blend_attr, [control_value, future_control_value], [1, 0], tangent_type= 'linear')

                last_control_value = control_value
            
            value = 1*negative_value
            
            anim.quick_driven_key(setup_attr, blend_attr, [control_value, value], [1, 0], tangent_type= 'linear', infinite = False)
            
            if first_value == 0:
                if not has_negative and not negative_parent:
                    cmds.keyTangent( blendshape.blendshape, edit=True, float = (first_value,first_value) , attribute= inbetween, absolute = True, itt = 'clamped', ott = 'linear' )
                    cmds.keyTangent( blendshape.blendshape, edit=True, float = (second_value,second_value) , attribute= inbetween, absolute = True, itt = 'linear', ott = 'linear' )
            
            #switching to parent shape
            blend_attr = '%s.%s' % (blendshape.blendshape, name)
            
            if not negative_parent:
                anim.quick_driven_key(setup_attr, blend_attr, [control_value, value], [0, 1], tangent_type = 'linear', infinite = 'post_only')
                cmds.keyTangent( blendshape.blendshape, edit=True, float = (value, value) , absolute = True, attribute= name, itt = 'linear', ott = 'clamped', lock = False, ox = 1, oy = 1)
                
            if negative_parent:
                anim.quick_driven_key(setup_attr, blend_attr, [control_value, value], [0, 1], tangent_type = 'linear', infinite = 'pre_only')
                cmds.keyTangent( blendshape.blendshape, edit=True, float = (value, value) , absolute = True, attribute= name, itt = 'clamped', ott = 'linear', lock = False, ix = 1, iy = -1 )    
                
    def _setup_combo_connections(self, combo, skip_update_others = False):
        
        inbetween_combo_parent = self.get_inbetween_combo_parent(combo)
        
        values = None
        
        if inbetween_combo_parent:
            values = self._get_inbetween_combo_value_dict(inbetween_combo_parent)
            
        if not inbetween_combo_parent:
            values = self._get_inbetween_combo_value_dict(combo)
        
        self._remove_combo_multiplies(combo)
        
        shapes = self.get_shapes_in_combo(combo, include_combos=False)
        
        target_combo = '%s.%s' % (self.blendshape.blendshape, combo)
        
        last_multiply = None
        
        for shape in shapes:
            
            negative_offset = 1
            
            if not self.blendshape.is_target(shape):
                continue
            
            orig_shape = shape
            
            inbetween_parent = self.get_inbetween_parent(shape)
            
            if inbetween_parent:
                shape = inbetween_parent
                
            setup_shape = shape
                
            negative_parent = self.get_negative_parent(shape)
            if negative_parent:
                negative_offset = -1
                setup_shape = negative_parent
            
            source = '%s.%s' % (self.setup_group, setup_shape)
            
            if not last_multiply:
                multiply = attr.connect_multiply(source, target_combo, 1)
                
            if last_multiply:
                multiply = attr.connect_multiply(source, '%s.input2X' % last_multiply, 1)
            
            multiply = cmds.rename(multiply, core.inc_name('multiply_combo_%s_1' % combo))
            
            value_list = []
               
            if shape in values:
                value_list = values[shape]
            
            if values:
                
                value = None
                
                if orig_shape:
                    value = self.get_inbetween_value(orig_shape)
                
                before_value = 0
                after_value = 1 * negative_offset
                
                if value:
                    
                    if value in value_list:
                        
                        if not len(value_list) == 1:
                            index = value_list.index(value)
                            
                            if index > 0:
                                before_value = (value_list[index-1] * 0.01 * negative_offset)
                            
                            if index < len(value_list)-1:
                                after_value = (value_list[index+1] * 0.01 * negative_offset)
                    
                    value *= 0.01 * negative_offset
                    attr.disconnect_attribute('%s.input1X' % multiply)
                    
                    anim.quick_driven_key(source, '%s.input1X' % multiply, [before_value,value,after_value], [0,1,0], tangent_type = 'linear')    
                                
                if not value:
                    
                    before_value = 0
                    
                    if value_list:
                        before_value = value_list[-1] * 0.01 * negative_offset
                    
                    attr.disconnect_attribute('%s.input1X' % multiply)
                    anim.quick_driven_key(source, '%s.input1X' % multiply, [before_value, (1 * negative_offset)], [0,1], tangent_type = 'linear')
            
            last_multiply = multiply
            
            if not values:
                attr.disconnect_attribute('%s.input1X' % multiply)
                anim.quick_driven_key(source, '%s.input1X' % multiply, [0, 1], [0,1], tangent_type = 'linear')
                
                if negative_parent:
                    attr.disconnect_attribute('%s.input1X' % multiply)
                    anim.quick_driven_key(source, '%s.input1X' % multiply, [0, -1], [0,1], tangent_type = 'linear')
        
    def _remove_combo_multiplies(self, combo):
        
        input_node = attr.get_attribute_input('%s.%s' % (self.blendshape.blendshape, combo), node_only = True)
        
        if not input_node:
            return
        
        mult_nodes = [input_node]
        
        while input_node:
            
            if cmds.nodeType(input_node) == 'multiplyDivide':
                input_node = attr.get_attribute_input('%s.input2X' % input_node)
                mult_nodes.append(input_node)
                
            
            if not cmds.nodeType(input_node) == 'multiplyDivide':
                input_node = None
            
        cmds.delete(mult_nodes)
                    
    def is_shape_combo_manager(self, group):
        
        if attr.get_vetala_type(group) == self.vetala_type:
            return True
        
    def _rename_shape_negative(self, old_name, new_name):
        
        negative = self.get_negative_name(old_name)
        new_negative = self.get_negative_name(new_name)
        
        if self.blendshape.is_target(new_negative):
            
            if self.blendshape.is_target(negative):
                self.blendshape.remove_target(negative)
        
        if not self.blendshape.is_target(new_negative):
            
            if self.blendshape.is_target(negative):
                self.blendshape.rename_target(negative, new_negative)
    
    def _rename_shape_inbetweens(self, old_name, new_name):
        inbetweens = self.get_inbetweens(old_name)
        
        for inbetween in inbetweens:
            
            value = self.get_inbetween_value(inbetween)
            
            if value:
                self.blendshape.rename_target(inbetween, new_name + str(value)) 
                
    def _rename_shape_combos(self, old_name, new_name):
        
        combos = self.get_combos()
        
        for combo in combos:
            
            combo_name = []
            
            shapes = combo.split('_')
            
            for shape in shapes:
                
                test_name = shape
                
                inbetween_parent = self.get_inbetween_parent(shape)
                
                if inbetween_parent:
                    test_name = inbetween_parent
                
                negative_parent = self.get_negative_parent(test_name)
                
                if negative_parent:
                    test_name = negative_parent
                
                if test_name == old_name:
                    
                    name = shape.replace(old_name, new_name)
                    combo_name.append(name)
                
                if test_name != old_name:
                    combo_name.append(shape)
                    
            new_combo_name = string.join(combo_name, '_')
            
            self.blendshape.rename_target(combo, new_combo_name)
                
    def _get_inbetween_combo_value_dict(self, combo):
        
        inbetween_combo_parent = self.get_inbetween_combo_parent(combo)
        
        if inbetween_combo_parent:
            combo = inbetween_combo_parent
        
        inbetweens = self.get_inbetween_combos(combo)
        
        value_dict = {}
        
        for inbetween in inbetweens:
            
            shapes = inbetween.split('_')
            
            for shape in shapes:
                
                if self.is_inbetween(shape):
                    
                    inbetween_parent = self.get_inbetween_parent(shape)
                    
                    if not value_dict.has_key(inbetween_parent):
                        value_dict[inbetween_parent] = []
                    
                    if inbetween_parent:
                        
                        value = self.get_inbetween_value(shape)
                        
                        if not value in value_dict[inbetween_parent]:
                            value_dict[inbetween_parent].append(value)
        
        for key in value_dict:
            value_dict[key].sort()
                        
        return value_dict
    
    @core.undo_chunk
    def create(self, start_mesh):
        
        manager = self._find_manager_for_mesh(start_mesh)
        
        if manager:
            self.load(manager)
            return
        
        name = self.setup_prefix + '_' + start_mesh

        self.setup_group = cmds.group(em = True, n = core.inc_name(name))
        
        attr.hide_keyable_attributes(self.setup_group)
        attr.create_vetala_type(self.setup_group, self.vetala_type)
        
        self._create_home(start_mesh)
        attr.disconnect_attribute('%s.mesh' % self.setup_group)
        attr.connect_message(start_mesh, self.setup_group, 'mesh')
        
        self._create_blendshape()
        
        shapes = self.get_shapes()
        
        if shapes:
            for shape in shapes:
                self.add_shape(shape)
        
    def load(self, manager_group):
        
        if self.is_shape_combo_manager(manager_group):
            self.setup_group = manager_group
            
        self._get_blendshape()
        
    @core.undo_chunk
    def zero_out(self):
        
        if not self.setup_group or not cmds.objExists(self.setup_group):
            return 
        
        attrs = cmds.listAttr(self.setup_group, ud = True, k = True)
        
        for attr in attrs:
            try:
                cmds.setAttr('%s.%s' % (self.setup_group, attr), 0)
            except:
                pass
    
    @core.undo_chunk
    def add_meshes(self, meshes, preserve = False):
        
        shapes, combos, inbetweens = self.get_shape_and_combo_lists(meshes)
        
        home = self._get_home_mesh()
        base_mesh = self._get_mesh()
        
        for shape in shapes:
            
            if shape == base_mesh:
                vtool.util.warning('Cannot add base mesh into the system.')
                continue
            
            if shape == home:
                vtool.util.warning('Cannot add home mesh into the system.')
                continue
            
            self.add_shape(shape, preserve_combos = preserve)    
            
        for inbetween in inbetweens:
            
            last_number = vtool.util.get_last_number(inbetween)
            
            if not len(str(last_number)) >= 2:
                continue
            
            if inbetween == base_mesh:
                vtool.util.warning('Cannot add base mesh into the system.')
                continue
            
            if inbetween == home:
                vtool.util.warning('Cannot add home mesh into the system.')
                continue
            
            self.add_shape(inbetween)
            
        for combo in combos:
            
            if combo == base_mesh:
                vtool.util.warning('Cannot add base mesh into the system.')
                continue
            
            if combo == home:
                vtool.util.warning('Cannot add home mesh into the system.')
                continue
            
            for mesh in meshes:
                if mesh == combo:
                    self.add_combo(mesh)
                    
        return shapes, combos, inbetweens
    
    @core.undo_chunk
    def recreate_all(self):
        
        self.zero_out()
        
        mesh = self._get_mesh()
        
        targets_gr = cmds.group(em = True, n = core.inc_name('targets_%s_gr' % mesh))
        
        shapes = self.get_shapes()
        combos = self.get_combos()
        
        inbetweens = []
        
        for shape in shapes:
            
            if self.is_negative(shape):
                continue
            
            if self.is_inbetween(shape):
                continue
            
            new_shape = self.blendshape.recreate_target(shape)
            
            shape_inbetweens = self.get_inbetweens(shape)
            inbetweens += shape_inbetweens
            
            negative = self.get_negative_name(shape)
            if self.is_negative(negative):
                shape_inbetweens.append(negative)
            
            new_inbetweens = []
            shape_gr = new_shape
            
            for inbetween in shape_inbetweens:
                sub_shape = self.blendshape.recreate_target(inbetween)
                new_inbetweens.append(sub_shape)
            
            if new_inbetweens:
                
                shape_gr = cmds.group(em = True, n = '%s_gr' % shape)
                
                for inc in xrange(0, len(shape_inbetweens)):
                    
                    new_inbetween = new_inbetweens[inc]
                    
                    new_names = cmds.parent(new_inbetween, shape_gr)
                    if new_names:
                        cmds.rename(new_names[0], shape_inbetweens[inc])
                
                new_names = cmds.parent(new_shape, shape_gr)
                
                if new_names:
                    cmds.rename(new_names[0], shape)
            
            new_names = cmds.parent(shape_gr, targets_gr)
            
            if not new_inbetweens:
                if new_names:
                    cmds.rename(new_names[0], shape)
        
        if combos:
            combos_gr = cmds.group(em = True, n = 'combos_gr')
            
            for combo in combos:
                
                sub_shapes = self.get_shapes_in_combo(combo, include_combos = True)
                sub_shapes.append(combo)
                
                new_combo = cmds.duplicate(self._get_home_mesh())[0]
                new_shapes = []
                
                for shape in sub_shapes:
                    
                    if not self.blendshape.is_target(shape):
                        continue
                    
                    new_shape = self.blendshape.recreate_target(shape)
                    
                    deform.quick_blendshape(new_shape, new_combo)
                    new_shapes.append(new_shape)
                    
                cmds.delete(new_combo, ch = True)
                cmds.delete(new_shapes)
                
                cmds.parent(new_combo, combos_gr)
                
                new_combo = cmds.rename(new_combo, combo)
                
                cmds.showHidden(new_combo)
                
            cmds.parent(combos_gr, targets_gr)
            
        return targets_gr
    
    def get_shapes_in_group(self, group_name):
        
        relatives = cmds.listRelatives(group_name, f = True)
        
        meshes = geo.get_meshes_in_list(relatives)
        
        shapes, combos, inbetweens = [], [], []
        
        for mesh in meshes:
            if self.is_inbetween(mesh):
                inbetweens.append(mesh)
                continue
                
            if self.is_combo(mesh):
                combos.append(mesh)
                continue
            
            shapes.append(mesh)
            
        return shapes, combos, inbetweens
    
    #--- shapes
      
    def add_shape(self, name, mesh = None, preserve_combos = False):
        
        if preserve_combos:
            combos = self.get_associated_combos(name)
            
            preserve_these = {}
            
            for combo in combos:
                new_combo = self.recreate_combo(combo)
                preserve_these[combo] = new_combo
        
        shape = name

        negative_parent = self.get_negative_parent(name)
        
        if negative_parent:
            shape = negative_parent

        if not mesh:
            mesh = name
        
        if mesh == self._get_mesh():
            mesh = name
        
        home = self._get_mesh()
        
        if home == mesh:
            return
        
        blendshape = self._get_blendshape()
        
        if not blendshape:
            vtool.util.warning('No blendshape.')
            return
        
        
        
        is_target = blendshape.is_target(name)
        
        if is_target:
            blendshape.replace_target(name, mesh)
        
        if not is_target:
            blendshape.create_target(name, mesh)
            blendshape.disconnect_target(name)
        
        if self.is_inbetween(name):
            inbetween_parent = self.get_inbetween_parent(name)
            shape = inbetween_parent
            
            negative_parent = self.get_negative_parent(shape)
            
            if negative_parent:
                shape = negative_parent
            
        self._add_variable(shape)
    
        self._setup_shape_connections(name)
        
        if preserve_combos:
            
            if not combos:
                return
            
            for combo in combos:
                self.add_combo(combo, preserve_these[combo])
                cmds.delete(preserve_these[combo])
            
                    
    def turn_on_shape(self, name, value = 1):
        
        last_number = vtool.util.get_last_number(name)
        
        if last_number:
            last_number_str = str(last_number)
            
            if len(last_number_str) >= 2:
                first_part = name[:-2]
                
                if self.blendshape.is_target(first_part):
                    
                    last_number_str = last_number_str[-2:]
                    last_number = int(last_number_str)
                    value = last_number * .01 * value
                    
                    self.set_shape_weight(first_part, value)
                    
                    name = first_part
                        
        if not last_number:
            self.set_shape_weight(name, 1 * value)
            
        return name
            
    def set_shape_weight(self, name, value):
        
        value = value
        
        if not self.blendshape.is_target(name):
            return
        
        if name.count('_') > 0:
            return
        
        negative_parent = self.get_negative_parent(name)
        
        if negative_parent:
            value *= -1
            name = negative_parent
        
        if value < 1:
            
            var = attr.MayaNumberVariable(name)
            #var.set_min_value(-1)
            #var.set_max_value(1)
            var.create(self.setup_group)
        
        
        cmds.setAttr('%s.%s' % (self.setup_group, name), value)
    
    def get_mesh(self):
        return self._get_mesh()
    
    def get_shapes(self):
        
        blendshape = self._get_blendshape()
        
        if not blendshape:
            return []
        
        found = []
        
        for target in blendshape.targets:
            
            split_target = target.split('_')
            
            if split_target and len(split_target) == 1:
                found.append(target)
        
        found.sort()
        
        return found
    
    def recreate_shape(self, name):
        
        target = self.turn_on_shape(name)
        
        if name.count('_') < 1:
            
            if self.blendshape.is_target(target):
                target = self.blendshape.recreate_target(target, -1)
                
            if not cmds.objExists(target):
                target = cmds.duplicate(self._get_mesh())[0]
                
        if name.count('_') > 0:
            target = cmds.duplicate(self._get_mesh())[0]
            
        if target != name:
                target = cmds.rename(target, core.inc_name( name ) )
            
        parent = cmds.listRelatives(target, p = True)
        if parent:
            cmds.parent(target, w = True)
            
        return target
            
    def rename_shape(self, old_name, new_name):
        
        if self.blendshape.is_target(new_name):
            return
        
        self._rename_shape_inbetweens(old_name, new_name)
        self._rename_shape_negative(old_name, new_name)
        self._rename_shape_combos(old_name, new_name)
        
        name = self.blendshape.rename_target(old_name, new_name)
        
        if not self.is_negative(name):
            
            new_attr_name = '%s.%s' % (self.setup_group, old_name)
            
            if cmds.objExists(new_attr_name):
                attributes = attr.Attributes(self.setup_group)
                attributes.rename_variable(old_name, name)
            if not cmds.objExists(new_attr_name):
                self._add_variable(name)
                
            self._setup_shape_connections(name)
            
        if self.is_negative(name):
            
            attributes = attr.Attributes(self.setup_group)
            attributes.delete(old_name)
            
            parent_name = self.get_negative_parent(new_name)
            self.set_shape_weight(parent_name, 0)
            self._setup_shape_connections(name)
        
        
        
        return name
        
    def remove_shape(self, name):
        
        delete_attr = True

        inbetween_parent = self.get_inbetween_parent(name)
        
        if not inbetween_parent:
        
            inbetweens = self.get_inbetweens(name)
            if inbetweens:
                for inbetween in inbetweens:
                    self.blendshape.remove_target(inbetween)
                    
                    combos = self.get_associated_combos(inbetween)
                    
                    for combo in combos:
                        self.remove_combo(combo)
                        
                        
        negative = self.get_negative_name(name)
        
        if self.is_negative(negative):
            delete_attr = False
            
        attr_shape = name
        negative_parent = self.get_negative_parent(name)
        if negative_parent:
            delete_attr = False
            
        target = '%s.%s' % (self.blendshape.blendshape, name)
        
        input_node = attr.get_attribute_input(target, node_only=True)
        
        if input_node and input_node != self.setup_group:
            cmds.delete(input_node)
        
        self.blendshape.remove_target(name)
        
        if inbetween_parent:
            self._setup_shape_connections(inbetween_parent)
        
        if not self.is_inbetween(name) and delete_attr:
            attr_name = self.setup_group + '.' + attr_shape
            if cmds.objExists(attr_name):
                cmds.deleteAttr( attr_name )
            
        combos = self.get_associated_combos(name)
        
        for combo in combos:
            self.remove_combo(combo)
        
    #---  combos
    
    def is_combo(self, name):
        
        if name.count('_') > 1:
            return True
        
        return False
    
    def is_combo_valid(self, name):
        
        shapes = self.get_shapes_in_combo(name)
        
        for shape in shapes:
            if not self.blendshape.is_target(shape):
                return False
        
        return True
    
    def is_combo_inbetween(self, combo):
        
        split_combo = combo.split('_')
                
        for shape in split_combo:
            inbetween_parent = self.get_inbetween_parent(shape)
            
            if inbetween_parent:
                return True
            
        return False
    
    def add_combo(self, name, mesh = None):
        
        if not mesh:
            mesh = name
        
        nice_name = core.get_basename(name, remove_namespace = True)
        
        if not self.is_combo_valid(nice_name):
            vtool.util.warning('Could not add combo %s, a target is missing.' % name)
            return
        
        home = self._get_mesh()
        
        if home == mesh:
            return
        
        blendshape = self._get_blendshape()
        
        if not blendshape:
            vtool.util.warning('No blendshape.')
            return
        
        home = self._get_home_mesh()
        
        shapes = self.get_shapes_in_combo(nice_name, include_combos=True)
        
        delta = self._get_combo_delta(mesh, shapes, home)
        
        if blendshape.is_target(nice_name):
            blendshape.replace_target(nice_name, delta)
        
        if not blendshape.is_target(nice_name):
            blendshape.create_target(nice_name, delta)
        
        
        cmds.delete(delta)
        
        self._setup_combo_connections(nice_name)
        
            
    def recreate_combo(self, name):
    
        shape = self.recreate_shape(name)
        
        return shape
        
    def remove_combo(self, name):
        
        inbetween_combo_parent = self.get_inbetween_combo_parent(name)
        
        if inbetween_combo_parent and self.blendshape.is_target(inbetween_combo_parent):
            self._setup_combo_connections(name)
            
        inbetweens = self.get_inbetween_combos(name)
        
        if inbetweens:
            for inbetween in inbetweens:
                self._setup_combo_connections(inbetween, skip_update_others = True) 
        
        self.blendshape.remove_target(name)
        self._remove_combo_multiplies(name)
    
    def get_combos(self):
        
        blendshape = self._get_blendshape()
        
        if not blendshape:
            return []
        
        found = []
        
        for target in blendshape.targets:
            
            split_target = target.split('_')
            
            if split_target and len(split_target) > 1:
                found.append(target)
            
        return found
        
    def find_possible_combos(self, shapes):
        
        return vtool.util.find_possible_combos(shapes)
    
    def get_shapes_in_combo(self, combo_name, include_combos = False):
        
        shapes = combo_name.split('_')
        
        combos = []
        
        if include_combos:
            combos = self.find_possible_combos(shapes)
            if combo_name in combos:
                combos.remove(combo_name)
            
        possible = shapes + combos
        
        return possible
    
    def get_associated_combos(self, shapes):
        
        shapes = vtool.util.convert_to_sequence(shapes)
        
        combos = self.get_combos()
        
        found_combos = []
        
        for shape in shapes:
        
            if self.is_combo_valid(shape):
                pass
                
            for combo in combos:
                
                split_combo = combo.split('_')
                if shape in split_combo:
                    found_combos.append(combo)
                    
        
                
        return found_combos
    
    def get_inbetween_combos(self, combo):
        
        if self.is_combo_inbetween(combo):
            return
        
        combos = self.get_combos()
        
        found = []
        
        for other_combo in combos:
            
            if other_combo == combo:
                continue
            
            other_combo_inbetween_parent = self.get_inbetween_combo_parent(other_combo)
            
            if other_combo_inbetween_parent:
                found.append(other_combo)
            
        return found
        
    def get_inbetween_combo_parent(self, combo):
        
        split_combo = combo.split('_')
        
        parents = []
        passed = False
        
        for shape in split_combo:
            inbetween_parent = self.get_inbetween_parent(shape)
            
            if inbetween_parent:
                parents.append(inbetween_parent)
                passed = True
            
            if not inbetween_parent:
                parents.append(shape)
        
        parent = string.join(parents, '_')
        
        if passed:
            return parent
        
    def get_shape_and_combo_lists(self, meshes):
        
        shapes = []
        combos = []
        inbetweens = []
        
        for mesh in meshes:
            
            nice_name = core.get_basename(mesh, remove_namespace = True)
            
            split_shape = nice_name.split('_')
            
            if nice_name.count('_') == 0:
                
                inbetween_parent = self.get_inbetween_parent(nice_name)
                
                if inbetween_parent:
                    if inbetween_parent in meshes or self.blendshape.is_target(inbetween_parent):
                        inbetweens.append(mesh)
                
                if not inbetween_parent:
                    shapes.append(mesh)
                
            if len(split_shape) > 1:
                combos.append(mesh)
                
        return shapes, combos, inbetweens
    
    def is_negative(self, shape, parent_shape = None):
        
        inbetween_parent = self.get_inbetween_parent(shape)
        
        if inbetween_parent:
            shape = inbetween_parent
        
        if parent_shape:
            if not shape[:-1] == parent_shape:
                return False
        
        if not self.blendshape.is_target(shape):
            return False
        
        if not shape.endswith('N'):
            return False
        
        if shape.endswith('N'):
            return True
        
    def get_negative_name(self, shape):
        
        negative_name = shape + 'N'
        
        inbetween_parent = self.get_inbetween_parent(shape)
        
        if inbetween_parent:
            number = self.get_inbetween_value(shape)
            shape = inbetween_parent
            
            negative_name = shape + 'N' + str(number)
                        
        return negative_name
        
    def get_negative_parent(self, shape):
        
        parent = None
        
        if not shape:
            return
        
        inbetween_parent = self.get_inbetween_parent(shape)
        
        if inbetween_parent:
            shape = inbetween_parent
            
        if shape.endswith('N'):
            parent = shape[:-1]
            
        return parent
    
    def has_negative(self, shape):
        
        if self.blendshape.is_target( (shape + 'N') ):
            return True
        
        return False
    
    def is_inbetween(self, shape, parent_shape = None):
        
        last_number = vtool.util.get_trailing_number(shape, as_string = True, number_count=2)
        
        if not last_number:
            return False
        
        if not len(last_number) >= 2:
            return False
        
        first_part = shape[:-2]
        
        if self.blendshape.is_target(first_part):
            
            if parent_shape:
                if parent_shape == first_part:
                    return True 
                if not parent_shape == first_part:
                    return False
            
            return True

    def get_inbetweens(self, shape = None):
        
        targets = self.get_shapes()
        
        found = []
        
        for target in targets:
            
            if target.count('_') > 0:
                continue
            
            if self.is_inbetween(target, shape):
                found.append(target)
        
        return found

    def get_inbetween_parent(self, inbetween):
        
        last_number = vtool.util.get_trailing_number(inbetween, as_string = True, number_count= 2)
        
        if not last_number:
            return
        
        if not len(last_number) >= 2:
            return
        
        first_part = inbetween[:-2]
        
        return first_part
        
    def get_inbetween_value(self, shape):
        
        number = vtool.util.get_last_number(shape)
            
        if not number:
            return
        
        number_str = str(number)
        if not len(number_str) >= 2:
            return
            
        value = int(number_str[-2:])
        
        return value
        
    def get_inbetween_values(self, parent_shape, inbetweens):
        
        values = []
        value_dict = {}
        
        for inbetween in inbetweens:
            
            value = self.get_inbetween_value(inbetween)
            
            value_dict[value] = inbetween
            values.append(value)
            
        values.sort()
        
        return values, value_dict
        