# Copyright (C) 2022 Louis Vottero louis.vot@gmail.com    All rights reserved.

from __future__ import absolute_import

import string
import re

from .. import util

if util.is_in_maya():
    import maya.cmds as cmds
    
from . import core
from . import attr
from . import deform
from . import anim
from . import geo
from . import api

class BlendShape(object):
    """
    Convenience for working with blendshapes.
    
    Args:
        blendshape_name (str): The name of the blendshape to work on. 
    """
    
    def __init__(self, blendshape_name = None):
        self.blendshape = blendshape_name
        
        self.meshes = []
        self.targets = {}
        self.target_list = []
        self.weight_indices = []
        
        #if self.blendshape:
        #    self.set(blendshape_name)
            
        self.mesh_index = 0
        
        self.prune_compare_mesh = None
        self.prune_distance = -1
        
        
    def _store_meshes(self, force = False):
        if not self.blendshape:
            return
        

        if not self.meshes or force:
            meshes = cmds.deformer(self.blendshape, q = True, geometry = True)
            self.meshes = meshes
        
    def _store_targets(self):
        
        if not self.blendshape:
            
            return
        
        target_attrs = []
        
        if cmds.objExists(self._get_input_target(0)):
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
        self.target_list.append(name)
        self.weight_indices.append(index)
        
        self.weight_indices.sort()

    def _get_target_attr(self, name):
        return '%s.%s' % (self.blendshape, name)

    def _get_weight(self, name):
        
        name = name.replace(' ', '_')
        
        if not self.targets:
            self._store_targets()
        
        target_index = None
                
        if name in self.targets:
            target_index = self.targets[name].index
        
        if target_index == None:
            return
        
        return '%s.weight[%s]' % (self.blendshape, target_index)

    def _get_weights(self, target_name = None, mesh_index = 0):
        
        if not self.meshes:
            self._store_meshes()
        
        mesh = self.meshes[mesh_index]
                        
        vertex_count = core.get_component_count(mesh)
        
        if not target_name:
            attribute = self._get_input_target_base_weights_attribute(mesh_index)
        
        if target_name:
            attribute = self._get_input_target_group_weights_attribute(target_name, mesh_index)
        
        weights = []
        
        for inc in range(0, vertex_count):
            weight = cmds.getAttr('%s[%s]' % (attribute, inc))
            
            weights.append(weight)
            
        return weights      

    def _get_input_target(self, mesh_index = 0):
        
        attribute = [self.blendshape,
                     'inputTarget[%s]' % mesh_index]
        
        attribute = '.'.join(attribute)
        return attribute

    def _get_input_target_base_weights_attribute(self, mesh_index = 0):
        input_attribute = self._get_input_target(mesh_index)
        
        attribute = [input_attribute,
                     'baseWeights']
        
        attribute = '.'.join(attribute)
        
        return attribute

    def _get_input_target_group(self, name, mesh_index = 0):
        
        if not self.targets:
            self._store_targets()
        
        if not name in self.targets:
            return
        
        target_index = self.targets[name].index
    
        input_attribute = self._get_input_target(mesh_index)
        
        attribute = [input_attribute,
                     'inputTargetGroup[%s]' % target_index]
        
        attribute = '.'.join(attribute)
        return attribute
    
    def _get_input_target_group_weights_attribute(self, name, mesh_index = 0):
        input_attribute = self._get_input_target_group(name, mesh_index)
        
        attribute = [input_attribute,
                     'targetWeights']
        
        attribute = '.'.join(attribute)
        
        return attribute        
    
    def _get_mesh_input_for_target(self, name, inbetween = 1):
        
        name = core.get_basename(name, remove_namespace = True)
        
        if not self.targets:
            self._store_targets()
        
        target_index = self.targets[name].index
        
        value = inbetween * 1000 + 5000
        
        attribute = [self.blendshape,
                     'inputTarget[%s]' % self.mesh_index,
                     'inputTargetGroup[%s]' % target_index,
                     'inputTargetItem[%s]' % value,
                     'inputGeomTarget']
        
        attribute = '.'.join(attribute)
        
        return attribute
        
    def _get_next_index(self):
        
        if self.weight_indices:
            return ( self.weight_indices[-1] + 1 )
        if not self.weight_indices:
            return 0

    def _disconnect_targets(self):
        
        if not self.targets:
            self._store_targets()
        
        for target in self.targets:
            self._disconnect_target(target)
            
    def _disconnect_target(self, name):
        
        if not self.targets:
            self._store_targets()
        
        target_attr = self._get_target_attr(name)
        
        connection = attr.get_attribute_input(target_attr)
        
        if not connection:
            return
        
        cmds.disconnectAttr(connection, target_attr)
        
        self.targets[name].connection = connection
    
    def _zero_target_weights(self):
        
        if not self.targets:
            self._store_targets()
        
        for target in self.targets:
            attr = self._get_target_attr(target)
            value = cmds.getAttr(attr)
            
            self.set_weight(target, 0)

            self.targets[target].value = value  
        
    def _restore_target_weights(self):
        
        if not self.targets:
            self._store_targets()
        
        for target in self.targets:
            self.set_weight(target, self.targets[target].value )
        
    def _restore_connections(self):
            
        if not self.targets:
            self._store_targets()
                
        for target in self.targets:
            
            connection = self.targets[target].connection
            
            if not connection:
                continue
            
            cmds.connectAttr(connection, self._get_target_attr(target)) 

    @core.undo_off
    def _connect_target(self, target_mesh, blend_input):
        
        temp_target = None
        
        if self.prune_compare_mesh and self.prune_distance > -1:
            target_mesh = self._get_pruned_target(target_mesh)
            temp_target = target_mesh

        cmds.connectAttr( '%s.outMesh' % target_mesh, blend_input)
        
        if temp_target:
            cmds.delete(temp_target)

    def _maya_add_target(self, target_mesh, name, inbetween = 1):
        
        temp_target = None
        if self.prune_compare_mesh and self.prune_distance > -1:
            target_mesh = self._get_pruned_target(target_mesh)
            temp_target = target_mesh

        index_value = self.targets[name].index
        self._store_meshes()

        if inbetween == 1:
            cmds.blendShape( self.blendshape, edit=True, t=(self.meshes[self.mesh_index], index_value, target_mesh, 1.0), tc = False)
        else:
            cmds.blendShape( self.blendshape, edit=True, ib = True, t=(self.meshes[self.mesh_index], index_value, target_mesh, inbetween), tc = False)

        if temp_target:
            cmds.delete(temp_target)
        
    def _get_pruned_target(self, target_mesh):
        found = False
        
        temp_target = cmds.duplicate(target_mesh)[0]
        
        if geo.is_mesh_compatible(target_mesh, self.prune_compare_mesh):
            
            target_object = api.nodename_to_mobject(target_mesh)
            target_fn = api.MeshFunction(target_object)
            target_positions = target_fn.get_vertex_positions()
            
            compare_object = api.nodename_to_mobject(self.prune_compare_mesh)
            compare_fn = api.MeshFunction(compare_object)
            compare_positions = compare_fn.get_vertex_positions()
            
            target_vtx_count = len(target_positions)
            
            bar = core.ProgressBar('pruning verts on %s' % core.get_basename(target_mesh), target_vtx_count)
            
            positions = target_positions
            
            for inc in range(0, target_vtx_count):
                
                
                target_pos = target_positions[inc]
                compare_pos = compare_positions[inc]
                
                compare_x = False
                compare_y = False
                compare_z = False
                
                if target_pos[0] == compare_pos[0]:
                    compare_x = True
                if target_pos[1] == compare_pos[1]:
                    compare_y = True
                if target_pos[2] == compare_pos[2]:
                    compare_z = True
                
                if compare_x and compare_y and compare_z:
                    continue
                
                x_offset = 0
                y_offset = 0
                z_offset = 0
                
                if not compare_x:
                    x_offset = abs(target_pos[0] - compare_pos[0])
                if not compare_y:
                    y_offset = abs(target_pos[1] - compare_pos[1])
                if not compare_z:
                    z_offset = abs(target_pos[2] - compare_pos[2])
                
                if x_offset == 0 and y_offset == 0 and z_offset == 0:
                    continue
                
                if x_offset > self.prune_distance:
                    continue
                if y_offset > self.prune_distance:
                    continue
                if z_offset > self.prune_distance:
                    continue
                
                positions[inc] = compare_pos
                
                found = True
                
                bar.next()
                
                if util.break_signaled():
                    break
                
                if bar.break_signaled():
                    break
                
            bar.end()
    
        if found:
            target_object = api.nodename_to_mobject(temp_target)
            target_fn = api.MeshFunction(target_object)
            target_fn.set_vertex_positions(positions)
            
            target_mesh = temp_target

            return target_mesh

    #--- blendshape deformer

    def create(self, mesh):
        """
        Create an empty blendshape on the mesh.
        
        Args:
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
        
        return blendshape

    def rename(self, name):
        """
        Rename the blendshape.
        
        Args:
            name (str): The ne name of the blendshape.
        """
        self.blendshape = cmds.rename(self.blendshape, name)
        self.set(self.blendshape)

    def set_envelope(self, value):
        """
        Set the envelope value of the blendshape node.
        
        Args:
            value (float)
        """
        
        cmds.setAttr('%s.envelope' % self.blendshape, value)
    
    def set(self, blendshape_name):
        """
        Set the name of the blendshape to work on.
        
        Args:
            blendshape_name (str): The name of a blendshape.
        """
        
        self.blendshape = blendshape_name
        
        self._store_targets()
        self._store_meshes()
        
    def set_mesh_index(self, index):
        self.mesh_index = index
        
    def set_prune_distance(self, distance, comparison_mesh):
        
        self.prune_compare_mesh = comparison_mesh
        self.prune_distance = distance
        
    def get_mesh_index(self, mesh):
        """
        Wip
        """
        geo = cmds.blendshape(self.blendshape, q = True, geometry = True)
        
    def get_mesh_count(self):
        meshes = cmds.deformer(self.blendshape, q = True, geometry = True)
        self.meshes = meshes
        
        return len(meshes)
        
    #--- target

    def is_target(self, name):
        """
        Check if name is a target on the blendshape.
        
        Args:
            name (str): The name of a target.
        """
        
        if not self.targets:
            self._store_targets()
        
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
        if not self.targets:
            self._store_targets()
        
        return list(self.target_list)
        
    @core.undo_chunk
    def create_target(self, name, mesh = None, inbetween = 1):
        """
        Add a target to the blendshape.
        
        Args:
            name (str): The name for the new target.
            mesh (str): The mesh to use as the target. If None, the target weight attribute will be created only.
            inbetween (float): The inbetween value. 0.5 will have the target activate when the weight is set to 0.5.
        """
        
        name = name.replace(' ', '_')
        
        if not self.is_target(name):
            
            current_index = self._get_next_index()
            
            nice_name = core.get_basename(name, remove_namespace = True)
            self._store_target(nice_name, current_index)
            
            

            #mesh_input = self._get_mesh_input_for_target(nice_name, inbetween)
            
            if mesh and cmds.objExists(mesh):
                self._maya_add_target(mesh, nice_name, inbetween)
                #self._connect_target(mesh, mesh_input)
            
            attr_name = core.get_basename(name)
            
            if not cmds.objExists('%s.%s' % (self.blendshape, name)):
                
                cmds.setAttr('%s.weight[%s]' % (self.blendshape, current_index), 1)
                if not cmds.objExists('%s.%s' % (self.blendshape, attr_name)):
                    cmds.aliasAttr(attr_name, '%s.weight[%s]' % (self.blendshape, current_index))
                cmds.setAttr('%s.weight[%s]' % (self.blendshape, current_index), 0)
            
            attr = '%s.%s' % (self.blendshape, attr_name)
            return attr
            
        if self.is_target(name):            
            util.show('Could not add target %s, it already exist.' % name)
       
    
    def insert_target(self, name, mesh, index):
        """
        Not implemented.
        """
        pass
           
    
    def replace_target(self, name, mesh, leave_connected = False):
        """
        Replace the mesh at the target.
        
        Args:
            name (str): The name of a target on the blendshape.
            mesh (str): The mesh to connect to the target.
        """
        
        if not mesh or not cmds.objExists(mesh):
            return
                
        name = name.replace(' ', '_')
        
        if self.is_target(name):
            
            mesh_input = self._get_mesh_input_for_target(name)
            current_input = attr.get_attribute_input(mesh_input)
            
            if not cmds.isConnected('%s.outMesh' % mesh, mesh_input):
                
                if current_input:
                    attr.disconnect_attribute(mesh_input)
                
                self._connect_target(mesh, mesh_input)
                #cmds.connectAttr('%s.outMesh' % mesh, mesh_input)
                
                if not leave_connected:
                    cmds.disconnectAttr('%s.outMesh' % mesh, mesh_input)
            else:
                if not leave_connected:
                    cmds.disconnectAttr('%s.outMesh' % mesh, mesh_input)
                
        if not self.is_target(name):
            util.show('Could not replace target %s, it does not exist' % name)
        
    def remove_target(self, name):
        """
        Remove the named target.
        
        Args:
            name (str): The name of a target on the blendshape.
        """
        
        if not self.targets:
            self._store_targets()
        
        target_group = self._get_input_target_group(name)
        if target_group and cmds.objExists(target_group):
            cmds.removeMultiInstance(target_group, b = True)
        weight_attr = self._get_weight(name)
        if weight_attr and cmds.objExists(weight_attr):
            cmds.removeMultiInstance(weight_attr, b = True)
        
        if name in self.targets:
            self.weight_indices.remove( self.targets[name].index )
            self.targets.pop(name)
        
        if name in self.target_list:
            self.target_list.remove(name)
        
        blend_attr = '%s.%s' % (self.blendshape, name)
        if cmds.objExists(blend_attr):
            cmds.aliasAttr(blend_attr, rm = True)
        else:
            util.warning('%s not in targets' % name)
        
        self.weight_indices.sort()
    
    def get_target_attr_input(self, name):
        
        target_name = self._get_target_attr(name)
        input_attr = attr.get_attribute_input(target_name)
        
        return input_attr
    
    def get_target_attr_output(self, name):
        
        target_name = self._get_target_attr(name)
        
        output_attrs = attr.get_attribute_outputs(target_name)
        
        return output_attrs
    
    def get_target_input(self, name, inbetween = 1):
        
        return self._get_mesh_input_for_target(name, inbetween)
       
    
       
    def disconnect_target(self, name, inbetween = 1):
        """
        Disconnect a target on the blendshape.
        
        Args:
            name (str): The name of a target on the blendshape.
            inbetween (float): 0-1 value of an inbetween to disconnect.
        """
        target = self._get_mesh_input_for_target(name, inbetween)
        
        attr.disconnect_attribute(target)
    
    def connect_target_attr(self, name, input_attr = None, output_attrs = []):
        
        basename = core.get_basename(name)
        
        target_attr = self._get_target_attr(basename)
        
        if input_attr:
            cmds.connectAttr(input_attr, target_attr)
        
        if output_attrs:
            for output_attr in output_attrs:
                attr.disconnect_attribute(output_attr)
                cmds.connectAttr(target_attr, output_attr)
                
    def rename_target(self, old_name, new_name):
        """
        Rename a target on the blendshape.
        
        Args:
            old_name (str): The current name of the target.
            new_name (str): The new name to give the target.
        """
        if not self.targets:
            self._store_targets()
        
        if not old_name in self.targets:
            return old_name
        
        if new_name in self.targets:
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
        
        Args:
            name (str): The name of a target.
            value (float):  The weight value to recreate the target it.
            mesh (float): The mesh to duplicate. This can be a mesh that doesn't have the blendshape in its deformation stack.
            
        Returns: 
            str: The name of the recreated target.
        """
        
        name = core.get_basename(name, remove_namespace = True)
        
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
        
        Args:
            mesh (float): The mesh to duplicate. This can be a mesh that doesn't have the blendshape in its deformation stack.
            
        Returns: 
            str: The name of the recreated target.
        """
    
        self._disconnect_targets()
        self._zero_target_weights()
        
        
        meshes = []
        
        if not self.targets:
            self._store_targets()
        
        for target in self.targets:
            new_name = core.inc_name(target)
            
            self.set_weight(target, 1)
                    
            output_attribute = '%s.outputGeometry[%s]' % (self.blendshape, self.mesh_index)
            
            if not mesh:
                mesh = cmds.deformer(self.blendshape, q = True, geometry = True)[0]
            
            if mesh:
                
                
                new_mesh = geo.create_shape_from_shape(mesh, new_name)
                
                #new_mesh = cmds.duplicate(mesh, name = new_name)[0]
                
                #cmds.connectAttr(output_attribute, '%s.inMesh' % new_mesh)
                #cmds.disconnectAttr(output_attribute, '%s.inMesh' % new_mesh)
                
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
        
        Args:
            name (str): The name of a target.
            value (float): The value to set the target to.
        """
        if self.is_target(name):
            
            attribute_name = self._get_target_attr(name)
            
            if not cmds.getAttr(attribute_name, l = True) and not attr.is_connected(attribute_name):
                
                cmds.setAttr(attribute_name, value)
    
    def set_post_deformation_mode(self, name, value):
        
        attribute = self._get_input_target_group(name)
        
        attribute = '.'.join([attribute, 'postDeformersMode'])
        
        cmds.setAttr(attribute, value)
    
    def connect_target_matrix(self, name, matrix_attribute):
        
        attribute = self._get_input_target_group(name)
        attribute = '.'.join([attribute, 'targetMatrix'])
        
        cmds.connectAttr(matrix_attribute, attribute, f = True)
    
    def set_weights(self, weights, target_name = None, mesh_index = 0):
        """
        Set the vertex weights on the blendshape. If no taget name is specified than the base weights are changed.
        
        Args:
            weights (list): A list of weight values. If a float is given, the float will be converted into a list of the same float with a count equal to the number of vertices.
            target_name (str): The name of the target.  If no target given, return the overall weights for the blendshape. 
            mesh_index (int): The index of the mesh in the blendshape. If the blendshape is affecting multiple meshes. Usually index is 0.
        """
        
        weights = util.convert_to_sequence(weights)
        weight_count = len(weights)
        
        if weight_count == 1:
        
            if not self.meshes:
                self._store_meshes()
        
            mesh = self.meshes[mesh_index]
            
            vertex_count  = core.get_component_count(mesh)
            
            weights = weights * vertex_count
        
        attribute = None
        
        if target_name == None:
            
            attribute = self._get_input_target_base_weights_attribute(mesh_index)
        
        if target_name:
            
            attribute = self._get_input_target_group_weights_attribute(target_name, mesh_index)
        
        try:
            set_attr = attribute + '[0:%s]' % (len(weights)-1)
            cmds.setAttr(set_attr, *weights, size =len(weights))
            
        except:
            #then its probably base weights
            for inc in range(weight_count):
                attribute_name = attribute + '[%s]' % inc
                
                cmds.setAttr(attribute_name, weights[inc])
        
        
        """
        #not sure which is faster, this or api, might try plug array in the future
        plug = api.get_plug(attribute)
        
        for inc in range(weight_count):
            plug.elementByLogicalIndex(inc).setFloat(weights[inc])
        """
        
    def get_weights(self, target_name = None, mesh_index = 0 ):
        
        if not self.meshes:
            self._store_meshes()
        
        mesh = self.meshes[mesh_index]
        
        vertex_count  = core.get_component_count(mesh)
        
        
        if target_name == None:
        
            weights = []
        
            for inc in range(0, vertex_count):    
                attribute = self._get_input_target_base_weights_attribute(mesh_index)
                
                weight = cmds.getAttr('%s[%s]' % (attribute, inc))
                weights.append(weight)
            
        if target_name:
            
            weights = []
            
            for inc in range(0, vertex_count):
                attribute = self._get_input_target_group_weights_attribute(target_name, mesh_index)
                
                weight = cmds.getAttr('%s[%s]' % (attribute, inc))
                weights.append(weight)
            
        return weights
        
    def set_invert_weights(self, target_name = None, mesh_index = 0):
        """
        Invert the blendshape weights at the target. If no target given, the base weights are inverted.
        
        Args:
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
    Convenience for editing blendshape combos. 
    """
    
    vetala_type = 'ShapeComboManager'
    
    def __init__(self):
        
        
        self.setup_group = None
        self.setup_prefix = 'shapeCombo'
        
        self.home = 'home'
        self.blendshape = {}
        self.blendshaped_meshes_list = []
        self._prune_distance = -1
    
    def _get_mesh(self):
        
        mesh = attr.get_attribute_input( '%s.mesh' % self.setup_group, node_only = True )
        
        if not mesh:
            return
        
        return mesh
    
    def _get_list_in_nice_names(self, things):
        
        new_list = []
        
        for thing in things:
            new_name = core.get_basename(thing, remove_namespace = True)
            new_list.append(new_name)
        
        return new_list
    
    def _get_sub_meshes(self):
        mesh = self._get_mesh()
        
        meshes = core.get_shapes_in_hierarchy(mesh, 'mesh')
        
        return meshes
        
    def _get_home_mesh(self):
        if not cmds.objExists('%s.home' % self.setup_group):
            return
        
        mesh = attr.get_attribute_input( '%s.home' % self.setup_group, node_only = True )
        
        if not mesh:
            return
        
        return mesh
        
    def _get_home_dict(self):
        
        base = self._get_mesh()
        home = self._get_home_mesh()
        
        if not base or not cmds.objExists(base):
            util.warning('No base mesh found')
            return
        
        if not home or not cmds.objExists(home):
            util.warning('No home mesh found')
            return
        
        meshes = core.get_shapes_in_hierarchy(base, 'mesh')
        
        home_meshes = core.get_shapes_in_hierarchy(home, 'mesh')
        
        
        
        
        if len(meshes) != len(home_meshes):
            util.warning('Base mesh does not match home mesh!')
        
        home_dict = {}
        
        if len(meshes) == len(home_meshes):
            for inc in range(0, len(meshes)):
                
                home_dict[meshes[inc]] = home_meshes[inc]
                
        return home_dict
         
    def _get_blendshape(self):
        
        base = self._get_mesh()
        
        if not base:
            return
        
        meshes = self._get_sub_meshes()
        
        blendshape_dict = {}
        blendshaped_meshes_list = []
        home_dict = self._get_home_dict()
        
        if not home_dict:
            return
        
        for mesh in meshes:
            
            
            blendshape = deform.find_deformer_by_type(mesh, 'blendShape')

            if not blendshape:
                return
            
            blendshaped_meshes_list.append(mesh)
            
            blend_inst = BlendShape(blendshape)
            
            blendshape_dict[mesh] = blend_inst
            
            if self._prune_distance > -1:
                blend_inst.set_prune_distance(self._prune_distance, home_dict[mesh])
            

        
        self.blendshape = blendshape_dict
        self.blendshaped_meshes_list = blendshaped_meshes_list
        
        return self.blendshape
        
    def _create_home(self, home_mesh):
        home = self._get_home_mesh()
        
        if home:
            cmds.delete(home)
            
        
        meshes = core.get_shapes_in_hierarchy(home_mesh, 'mesh')
        
        for mesh in meshes:
            
            env_history = deform.EnvelopeHistory(mesh)
            env_history.turn_off()
        
        self.home = cmds.duplicate(home_mesh, n = 'home_%s' % core.get_basename(home_mesh, remove_namespace = True))[0]
        
        for mesh in meshes:
            env_history.turn_on(True)
        
        new_meshes = core.get_shapes_in_hierarchy(self.home, return_parent = True, skip_first_relative=True)
        
        if new_meshes:
            for mesh in new_meshes:
                
                cmds.rename(mesh, 'home_' + core.get_basename(mesh, remove_namespace=True))
        
        
        cmds.parent(self.home, self.setup_group)
        attr.connect_message(self.home, self.setup_group, 'home')
        cmds.hide(self.home)
        
    def _create_blendshape(self):
        
        mesh = self._get_mesh()
        
        if not mesh:
            return
        
        children = core.get_shapes_in_hierarchy(mesh, 'mesh')
        
        for child in children:
            found = deform.find_deformer_by_type(child, 'blendShape')
            
            blendshape = BlendShape()
            
            if found:
                blendshape.set_targets_to_zero()
                return
            
            parent = cmds.listRelatives(child, p = True, f = True)[0]
            
            blendshape.create(parent)
            
            blendshape.rename('blendshape_%s' % core.get_basename(parent, remove_namespace = True))
    
    def _is_variable(self, target):
        if cmds.objExists('%s.%s' % (self.setup_group, target)):
            return True
        
        return False
    
    def _is_target(self, name):
        
        for key in self.blendshape:
            blend_inst = self.blendshape[key]
            
            if blend_inst.is_target(name):
                return True
            
            break
        
        return False
        
    
    def _get_variable_name(self, target):
        
        return '%s.%s' % (self.setup_group, target)
                    
    def _get_variable(self, target):
        attributes = attr.Attributes(self.setup_group)
        
        var = attributes.get_variable(target)
        
        return var
    
    def _add_variable(self, shape, negative = False):
        
        
        shape = core.get_basename(shape, remove_namespace = True)
        
        if self.is_inbetween(shape):
            inbetween_parent = self.get_inbetween_parent(shape)
            if inbetween_parent:
                shape = inbetween_parent
        
        if negative:
            negative_parent = self.get_negative_parent(shape)
            if negative_parent:
                shape = negative_parent
        
        var = attr.MayaNumberVariable(shape)
        
        if not negative:
            var.set_min_value(0)
        if negative:
            var.set_min_value(-1)
            
        var.set_max_value(1)
        
        if not var.exists(True):
            
            var.set_variable_type('float')
            var.create(self.setup_group)
            
        
    def _get_combo_delta(self, corrective_mesh, combo, home, blendshape_inst):
        
        temp_targets = []
        
        sub_value = 1
                
        shapes = self.get_shapes_in_combo(combo, include_combos=True)
        
        for shape in shapes:
            if self._is_target(shape):
                
                new_shape = blendshape_inst.recreate_target(shape)
                temp_targets.append(new_shape)
                
                between_value = util.get_trailing_number(shape, as_string = False, number_count = 2)
                
                if between_value:
                    sub_value *= (between_value * 0.01)
        
        delta = deform.get_blendshape_delta(home, temp_targets, corrective_mesh, replace = False)
        
        cmds.delete(temp_targets)
        
        return delta
                
    def _find_manager_for_mesh(self, mesh):
        
        managers = attr.get_vetala_nodes('ShapeComboManager')
        
        for manager in managers:
            
            found_mesh = attr.get_attribute_input('%s.mesh' % manager, node_only = True)
            
            if found_mesh == mesh:
                return manager
            
    def _remove_target_keyframe(self, shape_name, blendshape):
            
        attribute = '%s.%s' % (blendshape, shape_name)
        
        keyframe = anim.get_keyframe(attribute)
        
        if keyframe:
            cmds.delete(keyframe)
            
    def _get_target_keyframe(self, shape_name, blendshape):
        
        attribute = '%s.%s' % (blendshape, shape_name)
        
        keyframe = anim.get_keyframe(attribute)
        
        if keyframe:
            return keyframe
            
    def _setup_shape_connections(self, name):
        
        
        
        name = core.get_basename(name, remove_namespace = True)
        
        blendshape_dict = self._get_blendshape()
        
        if not blendshape_dict:
            return
        
        shape_keyframe = None
        inbetween_keyframe = None
        parent_inbetween_keframe = None
        
        for key in blendshape_dict:
            
            blend_inst = blendshape_dict[key]
            blendshape = blend_inst.blendshape
            
            blend_attr = '%s.%s' % (blendshape, name)
    
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
                    
            self._remove_target_keyframe(name, blendshape)
            
            if not inbetweens:
                value = 1
                value = value*negative_value
                
                infinite_value = True
                
                if has_negative:
                    infinite_value = 'post_only'
                if negative_parent:
                    infinite_value = 'pre_only'
                
                if shape_keyframe:
                    cmds.connectAttr('%s.output' % shape_keyframe, blend_attr)
                
                if not shape_keyframe:
                    shape_keyframe = anim.quick_driven_key(setup_attr, blend_attr, [0,value], [0,1], tangent_type = 'clamped', infinite = infinite_value)
                
                    if negative_parent:
                        
                        keyframe = self._get_target_keyframe(negative_parent, blendshape)
                        
                        if keyframe:
                            key = api.KeyframeFunction(keyframe)
                            key.set_pre_infinity(key.constant)
                        
                
                
            if inbetweens:
                
                values, value_dict = self.get_inbetween_values(name, inbetweens)
                
                last_control_value = 0
                
                value_count = len(values)
                
                first_value = None
                
                if inbetween_keyframe:
                    cmds.connectAttr('%s.output' % inbetween_keyframe, blend_attr)
                
                if not inbetween_keyframe:
                    for inc in range(0, value_count):
                        
                        inbetween = value_dict[values[inc]]
                        
                        blend_attr = '%s.%s' % (blendshape, inbetween)
                        
                        self._remove_target_keyframe(inbetween, blendshape)
                        
                        control_value = values[inc] *.01 * negative_value
                        
                        if inc == 0:
                            
                            pre_value = 'pre_only'
                            
                            if not has_negative:
                                pre_value = False
                            if negative_parent:
                                pre_value = False
                            
                            inbetween_keyframe = anim.quick_driven_key(setup_attr, blend_attr, [last_control_value, control_value], [0, 1], tangent_type='linear', infinite = pre_value)
                            first_value = last_control_value
                            second_value = control_value
                        
                        if inc > 0:
                            inbetween_keyframe = anim.quick_driven_key(setup_attr, blend_attr, [last_control_value, control_value], [0, 1], tangent_type= 'linear')
                            
                        
                        if value_count > inc+1:
        
                            future_control_value = values[inc+1] *.01 * negative_value
                            inbetween_keyframe = anim.quick_driven_key(setup_attr, blend_attr, [control_value, future_control_value], [1, 0], tangent_type= 'linear')
        
                        last_control_value = control_value
                    
                    value = 1*negative_value
                    
                    inbetween_keyframe = anim.quick_driven_key(setup_attr, blend_attr, [control_value, value], [1, 0], tangent_type= 'linear', infinite = False)
                    
                    if first_value == 0:
                        if not has_negative and not negative_parent:
                            cmds.keyTangent( blendshape, edit=True, float = (first_value,first_value) , attribute= inbetween, absolute = True, itt = 'clamped', ott = 'linear' )
                            cmds.keyTangent( blendshape, edit=True, float = (second_value,second_value) , attribute= inbetween, absolute = True, itt = 'linear', ott = 'linear' )
                            
                #switching to parent shape
                blend_attr = '%s.%s' % (blendshape, name)

                if parent_inbetween_keframe:
                    cmds.connectAttr('%s.output' % parent_inbetween_keframe, blend_attr)
                
                if not parent_inbetween_keframe:
                
                    if not negative_parent:
                        parent_inbetween_keframe = anim.quick_driven_key(setup_attr, blend_attr, [control_value, value], [0, 1], tangent_type = 'linear', infinite = 'post_only')
                        cmds.keyTangent( blendshape, edit=True, float = (value, value) , absolute = True, attribute= name, itt = 'linear', ott = 'clamped', lock = False, ox = 1, oy = 1)
                        
                    if negative_parent:
                        parent_inbetween_keframe = anim.quick_driven_key(setup_attr, blend_attr, [control_value, value], [0, 1], tangent_type = 'linear', infinite = 'pre_only')
                        cmds.keyTangent( blendshape, edit=True, float = (value, value) , absolute = True, attribute= name, itt = 'clamped', ott = 'linear', lock = False, ix = 1, iy = -1 )
                
    
       
    def _setup_combo_connections(self, combo, skip_update_others = False):
        
        for key in self.blendshape:
            
            blend_inst = self.blendshape[key]
            blendshape = blend_inst.blendshape
        
            self._remove_combo_multiplies(combo, blendshape)
            
            last_multiply = None
            
            sub_shapes = self.get_shapes_in_combo(combo, include_combos=False)
            
            inbetween_combo_parent = self.get_inbetween_combo_parent(combo)
            
            target_combo = '%s.%s' % (blendshape, combo)
            
            if not cmds.objExists(target_combo):
                continue
            
            if not inbetween_combo_parent:
                
                for sub_shape in sub_shapes:
                    
                    
                    source = '%s.%s' % (blendshape , sub_shape)
                    
                    if not cmds.objExists(source):
                        continue
                    
                    if not last_multiply:
                        multiply = attr.connect_multiply(source, target_combo, 1)
                        
                    if last_multiply:
                        multiply = attr.connect_multiply(source, '%s.input2X' % last_multiply, 1)
                    

                    self._handle_special_case_combo(sub_shape, multiply)
                        
                        
                    
                    last_multiply = multiply
                    
                    
            if inbetween_combo_parent:

                for sub_shape in sub_shapes:
                    
                    source = '%s.%s' % (blendshape, sub_shape)
                    
                    
                    if not cmds.objExists(source):
                        continue
                    
                    if not last_multiply:
                        multiply = attr.connect_multiply(source, target_combo, 1)
                        
                    if last_multiply:
                        multiply = attr.connect_multiply(source, '%s.input2X' % last_multiply, 1)
                        
                    multiply = cmds.rename(multiply, core.inc_name('multiply_combo_%s_1' % combo))
                    
                    last_multiply = multiply
                
                self._handle_special_case_parent_combo(inbetween_combo_parent, blendshape)

    def _handle_special_case_parent_combo(self, combo, blendshape):
        
        multiplies = self._get_combo_multiplies(combo, blendshape)
        
        if not multiplies:
            return
        
        for multiply in multiplies:
            input_node = attr.get_attribute_input('%s.input1X' % multiply, node_only = True)
            
            if input_node:
                if cmds.nodeType(input_node).find('animCurve') > -1:
                    values = cmds.keyframe(input_node,q = True, vc = True)
                    
                    input_node_attr = attr.get_attribute_input('%s.input' % input_node)
                    
                    shape = attr.get_attribute_name(input_node_attr)
                    
                    if values[-1] == -1:
                        
                        shape = self.get_negative_name(shape)
                        
                    
                    if cmds.objExists(input_node):
                        cmds.delete(input_node)
                    
                    cmds.connectAttr('%s.%s' % (blendshape, shape), '%s.input1X' % multiply)
        
    
    def _handle_special_case_combo(self, shape, multiply):
        """
        handle combo with shapes that have inbetweens but no the combo has no combo inbetweens
        """
        if self.is_inbetween(shape):
            return
        
        inbetweens = self.get_inbetweens(shape)
        
        if not inbetweens:
            return
        
        offset = 1
        
        negative_parent = self.get_negative_parent(shape)
        if negative_parent:
            shape = negative_parent
            offset = -1
            
        attr.disconnect_attribute('%s.input1X' % multiply)
        
        anim.quick_driven_key('%s.%s' % (self.setup_group, shape), '%s.input1X' % multiply, [0, offset], [0,1])

    def _get_combo_multiplies(self, combo, blendshape):
        
        input_node = attr.get_attribute_input('%s.%s' % (blendshape, combo), node_only = True)
        
        if not input_node:
            return
        
        mult_nodes = [input_node]
        
        while input_node:
            
            if cmds.nodeType(input_node) == 'multiplyDivide':
                input_node = attr.get_attribute_input('%s.input2X' % input_node, node_only = True)
                mult_nodes.append(input_node)
                
            
            if not cmds.nodeType(input_node) == 'multiplyDivide':
                input_node = None
            
        return mult_nodes
        

    def _remove_combo_multiplies(self, combo, blendshape):
        
        mult_nodes = self._get_combo_multiplies(combo, blendshape)
        
        if not mult_nodes:
            return
        
        for node in mult_nodes:
            if node and cmds.objExists(node):
                cmds.delete(node)
                
    
        
    def _rename_shape_negative(self, old_name, new_name):
        
        negative = self.get_negative_name(old_name)
        new_negative = self.get_negative_name(new_name)
        
        for key in self.blendshape:
            blend_inst = self.blendshape[key]
            
            if blend_inst.is_target(new_negative):
                
                if blend_inst.is_target(negative):
                    blend_inst.remove_target(negative)
            
            if not blend_inst.is_target(new_negative):
                
                if blend_inst.is_target(negative):
                    blend_inst.rename_target(negative, new_negative)
    
    def _rename_shape_inbetweens(self, old_name, new_name):
        inbetweens = self.get_inbetweens(old_name)
        
        for inbetween in inbetweens:
            
            value = self.get_inbetween_value(inbetween)
            
            if value:
                
                for key in self.blendshape:
                    blend_inst = self.blendshape[key]
                    blend_inst.rename_target(inbetween, new_name + str(value)) 
                
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
                    
            new_combo_name = '_'.join(combo_name)
            
            for key in self.blendshape:
                blend_inst = self.blendshape[key]
                blend_inst.rename_target(combo, new_combo_name)
                
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
                    
                    if not inbetween_parent in value_dict:
                        value_dict[inbetween_parent] = []
                    
                    if inbetween_parent:
                        
                        value = self.get_inbetween_value(shape)
                        
                        if not value in value_dict[inbetween_parent]:
                            value_dict[inbetween_parent].append(value)
        
        for key in value_dict:
            value_dict[key].sort()
                        
        return value_dict
    
    def _load_blendshape(self):
        shapes = self.get_shapes()
        combos = self.get_combos()
        
        shapes = shapes+combos
        
        shapes, combos, inbetweens = self.get_shape_and_combo_lists(shapes)
        
        
        if shapes:
            
            bar = core.ProgressBar('Loading shapes', len(shapes))
            
            for shape in shapes:
                
                bar.status('Loading shape: %s' % shape)
                
                if not attr.is_connected(self._get_variable(shape)):
                    self._add_shape_variable_and_connections(shape)
                
                bar.next()
            bar.end()
            
        if inbetweens:
            bar = core.ProgressBar('Loading inbetweens', len(shapes))
                
            for shape in inbetweens:
                bar.status('Loading inbetween: %s' % shape)
                
                if not attr.is_connected(self._get_variable(shape)):
                    self._add_shape_variable_and_connections(shape, add_variable = False)
                
                bar.next()
                
            bar.end()
        
        if combos:
            
            bar = core.ProgressBar('Loading combos', len(combos))
            
            for combo in combos:
                bar.status('Loading combo: %s' % combo)
                
                if not attr.is_connected(self._get_variable(combo)):
                    self._setup_combo_connections(combo)
            
                bar.next()
                
            bar.end()
            
        
    def _add_shape_variable_and_connections(self, name, add_variable = True):

        name = core.get_basename(name, remove_namespace = True)
        #name can be a group of meshes
        
        if self._is_target(name):
        
            if add_variable:
                self._add_variable(name, self.is_negative(name))
                
            self._setup_shape_connections(name)
    
    
    def is_shape_combo_manager(self, group):
        
        is_shape_combo_manager(group)
    
    @core.undo_chunk
    def create(self, base):
        
        manager = self._find_manager_for_mesh(base)
        
        if manager:
            status = self.load(manager)
            
            if not status:
                util.warning('Error loading manager: %s     Creating new one.  Please delete %s.' % (manager, manager))
            
            if status:
                return
        
        name = self.setup_prefix + '_' + base

        self.setup_group = cmds.group(em = True, n = core.inc_name(name))
        
        attr.hide_keyable_attributes(self.setup_group)
        attr.create_vetala_type(self.setup_group, self.vetala_type)
        
        self._create_home(base)
        attr.disconnect_attribute('%s.mesh' % self.setup_group)
        attr.connect_message(base, self.setup_group, 'mesh')
        
        self._create_blendshape()
        
        self._load_blendshape()
        
        return self.setup_group
        
    def load(self, manager_group, sync = True):
        
        if is_shape_combo_manager(manager_group):
            self.setup_group = manager_group
            
        if sync:
            blendshape = self._get_blendshape()
            
            if blendshape == None:
                return False
            self._load_blendshape()
        
        cmds.select(self.setup_group)
        
        return True
        
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
    
    @core.undo_off
    def add_meshes(self, meshes, preserve_combos = False, preserve_inbetweens = False, delete_shape_on_add = False):
        
        meshes = util.convert_to_sequence(meshes)
        
        shapes, combos, inbetweens = self.get_shape_and_combo_lists(meshes)
        
        home = self._get_home_mesh()
        base_mesh = self._get_mesh()
        
        util.show('Adding shapes.')
        
        for shape in shapes:
            
            if shape == base_mesh:
                util.warning('Cannot add base into the system.')
                continue
            
            if shape == home:
                util.warning('Cannot add home into the system.')
                continue
            
            self.add_shape(shape, preserve_combos = preserve_combos, preserve_inbetweens=preserve_inbetweens)
            
            if delete_shape_on_add:
                if cmds.objExists(shape):
                    cmds.delete(shape)
                    cmds.flushUndo()
            
        
        util.show('Adding inbetweens.')
        
        for inbetween in inbetweens:
            
            inbetween_nice_name = core.get_basename(inbetween, remove_namespace = True)
            
            last_number = util.get_trailing_number(inbetween_nice_name, as_string = True, number_count = 2)
            
            if not last_number:
                continue
            
            if inbetween == base_mesh:
                util.warning('Cannot add base mesh into the system.')
                continue
            
            if inbetween == home:
                util.warning('Cannot add home mesh into the system.')
                continue
            
            self.add_shape(inbetween, preserve_combos = preserve_combos, preserve_inbetweens = preserve_inbetweens)
            
            if delete_shape_on_add:
                if cmds.objExists(inbetween):
                    cmds.delete(inbetween)
        
        util.show('Adding combos.')
        
        for combo in combos:
            
            if combo == base_mesh:
                util.warning('Cannot add base mesh into the system.')
                continue
            
            if combo == home:
                util.warning('Cannot add home mesh into the system.')
                continue
            
            for mesh in meshes:
                if mesh == combo:
                    self.add_combo(mesh)
                    
                    if delete_shape_on_add:
                        if cmds.objExists(mesh):
                            cmds.delete(mesh)
                    
          
        return shapes, combos, inbetweens
    
    @core.undo_off
    def recreate_all(self):
        
        self.zero_out()
        
        mesh = self._get_mesh()
        
        targets_gr = cmds.group(em = True, n = core.inc_name('targets_%s_gr' % mesh))
        
        shapes = self.get_shapes()
        combos = self.get_combos()
        
        progress = core.ProgressBar('Recreate shapes', len(shapes))
        
        for shape in shapes:
            
            if self.is_negative(shape):
                continue
            
            if self.is_inbetween(shape):
                continue
            
            #if base has sub shapes then mesh count would be greater than 1
            mesh_count = len(self.blendshaped_meshes_list)
            shape_group = None
            for inc in range(0,mesh_count):
                
                mesh = self.blendshaped_meshes_list[inc]
                mesh_parent = cmds.listRelatives(mesh, p = True, f = True)[0]
                mesh_nice_name = core.get_basename(mesh_parent, remove_namespace = True)
                
                blend_inst = self.blendshape[mesh]
                new_shape = blend_inst.recreate_target(shape)
                
                if mesh_count > 1:
                    
                    if not shape_group:
                        shape_group = cmds.group(em = True, n = 'temp' + new_shape)
                        
                    cmds.parent(new_shape, shape_group)
                    cmds.rename(new_shape, mesh_nice_name)
            
            if shape_group:
                shape_group = cmds.rename(shape_group, shape)
                new_shape = shape_group
                
            
            shape_inbetweens = self.get_inbetweens(shape)
            
            negative = self.get_negative_name(shape)
            
            if self.is_negative(negative):
                shape_inbetweens.append(negative)
                negative_inbetweens = self.get_inbetweens(negative)
                if negative_inbetweens:
                    shape_inbetweens += negative_inbetweens
                
            
            new_inbetweens = []
            shape_gr = new_shape
            
            for inbetween in shape_inbetweens:
                
                mesh_count = len(self.blendshaped_meshes_list)
                shape_group = None
                for inc in range(0,mesh_count):
                    
                    mesh = self.blendshaped_meshes_list[inc]
                    mesh_parent = cmds.listRelatives(mesh, p = True, f = True)[0]
                    mesh_nice_name = core.get_basename(mesh_parent, remove_namespace = True)
                    
                    blend_inst = self.blendshape[mesh]
                    
                    inbetween_shape = blend_inst.recreate_target(inbetween)
                    
                    if mesh_count > 1:
                        
                        if not shape_group:
                            shape_group = cmds.group(em = True, n = 'temp' + new_shape)
                            
                        cmds.parent(inbetween_shape, shape_group)
                        cmds.rename(inbetween_shape, mesh_nice_name)
                
                if shape_group:
                    shape_group = cmds.rename(shape_group, inbetween)
                    inbetween_shape = shape_group
                        
                new_inbetweens.append(inbetween_shape)
            
            if new_inbetweens:
                
                shape_gr = cmds.group(em = True, n = '%s_gr' % shape)
                
                for inc in range(0, len(shape_inbetweens)):
                    
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

            progress.next()
            if util.break_signaled():
                break
                    
            if progress.break_signaled():
                break
        progress.end()
        
        
        
        if combos:
            combos_gr = cmds.group(em = True, n = 'combos_gr')
        
            progress = core.ProgressBar('Recreate combos', len(combos))
            
            for combo in combos:
                
                new_combo = self.recreate_shape(combo)
                cmds.parent(new_combo, combos_gr)
            
                progress.next()
                if util.break_signaled():
                    break
                        
                if progress.break_signaled():
                    break

            progress.end()
                
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
    
    def get_all_shape_names(self):
        
        shapes = self.get_shapes()
        
                
            
        combos = self.get_combos()
        
        shapes = shapes + combos
        
        return shapes
    
    def set_tag(self, tag_name, tag_value, append = True):
        
        tag_value = util.convert_to_sequence(tag_value)
        
        tag_value = list(dict.fromkeys(tag_value))
        
        store = attr.StoreData(self.setup_group)
        
        data_dict = store.eval_data()
        
        if not data_dict:
            data_dict = {}
        
        if type(data_dict) == list:
            raise
        
        if not tag_name in data_dict:
            data_dict[tag_name] = []
        
        if append:
            new_tag_value = data_dict[tag_name] + tag_value
            tag_value = list(dict.fromkeys(new_tag_value))
        
        data_dict[tag_name] = tag_value
        
        store.set_data(data_dict)
        
    def set_tag_dictionary(self, dictionary = {}):
        
        store = attr.StoreData(self.setup_group)
        
        store.eval_data()
        store.set_data(dictionary)
        
    def get_tag(self, tag_name):
        
        tag_name = str(tag_name)
        
        store = attr.StoreData(self.setup_group)
        
        data_dict = store.eval_data()
        
        if not data_dict:
            return
        
        if tag_name in data_dict:
            data_list = data_dict[tag_name]
            data_list = list(dict.fromkeys(data_list))
            return data_list
    
    def get_tags(self):
        store = attr.StoreData(self.setup_group)
        
        data_dict = store.eval_data()
        
        if not data_dict:
            return
        
        #cleanup needed incase of duplicates
        for key in data_dict:
            data_list = data_dict[key]
            data_list = list(dict.fromkeys(data_list))
            data_dict[key] = data_list
            store.set_data(data_dict)
        
        return list(data_dict.keys())
        
    
    def get_tags_from_shape(self, shape):
        
        store = attr.StoreData(self.setup_group)
        
        data_dict = store.eval_data()
        
        if not data_dict:
            return
        
        found = []
        
        for key in data_dict:
            shapes = self.get_tag(key)
            
            shapes = util.convert_to_sequence(shapes)
            
            if shape in shapes:
                found.append(key)
            
        return found
        
    def get_tag_shapes(self, tag_name):
        
        tag_name = str(tag_name)
        
        store = attr.StoreData(self.setup_group)
        
        data_dict = store.eval_data()
        
        if not data_dict:
            return
        
        if not tag_name in data_dict:
            return
        
        shapes = self.get_tag(tag_name)
        
        return shapes
        
    def remove_tag(self, tag_name):
        
        store = attr.StoreData(self.setup_group)
        data_dict = store.eval_data()
        
        if not data_dict:
            return
        
        shapes = self.get_tag(tag_name)
        
        if tag_name in data_dict:
            data_dict.pop(tag_name)
        
        store.set_data(data_dict)
        
        return shapes
        
    def remove_tag_shapes(self, tag_name, shapes):
        
        shapes = util.convert_to_sequence(shapes)
        
        store = attr.StoreData(self.setup_group)
        
        data_dict = store.eval_data()
        
        if not data_dict:
            return
        
        if not tag_name in data_dict:
            return
        
        tag_shapes = self.get_tag(tag_name)
        result_shapes = list(tag_shapes)
        
        for tag_shape in tag_shapes:
            #this could use a pythong set instead
            for shape in shapes:
                if tag_shape == shape:
                    result_shapes.remove(shape)
        
        if result_shapes:
            self.set_tag(tag_name, result_shapes, append = False)
        if not result_shapes:
            data_dict.pop(tag_name)
            store.set_data(data_dict)
            
        
    #--- shapes
    

    
    @core.undo_chunk
    def add_shape(self, name, mesh = None, preserve_combos = False, preserve_inbetweens = False):
        
        name_orig = name
        name = core.get_basename(name, remove_namespace = True)
        
        is_negative = False
        
        home_dict = self._get_home_dict()
        
        if not mesh:
            mesh = name_orig
        
        if mesh == self._get_mesh():
            mesh = name_orig
        
        if not preserve_inbetweens:
            
            inbetweens = self.get_inbetweens(name)
            
            if inbetweens:
                orig_shape = self.recreate_shape(name)
                orig_shape = cmds.rename(orig_shape, 'orig_%s' % orig_shape)
                
                mesh_count = len(self.blendshaped_meshes_list)
                
                for inc in range(0,mesh_count):
                    
                    base_mesh = self.blendshaped_meshes_list[inc]
                    
                    home = home_dict[base_mesh]
                    
                    home = cmds.listRelatives(home, p = True)[0]
                    
                    delta = deform.get_blendshape_delta(home, orig_shape, mesh, replace = False)
                    
                    for inbetween in inbetweens:
                        
                        temp_home = cmds.duplicate(home)[0]
                        
                        inbetween_value = self.get_inbetween_value(inbetween)
                        
                        inbetween_mesh = self.blendshape[base_mesh].recreate_target(inbetween)
                        
                        deform.quick_blendshape(delta, temp_home, inbetween_value*.01)
                        deform.quick_blendshape(inbetween_mesh, temp_home, 1)
                        
                        self.blendshape[base_mesh].replace_target(inbetween, temp_home)
                        
                        cmds.delete([temp_home, inbetween_mesh])
                    
                    cmds.delete(delta)
                    
                cmds.delete(orig_shape)
        
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

        
        
        blendshape = self._get_blendshape()
        
        if not blendshape:
            util.warning('No blendshape.')
            return
        
        target_meshes = core.get_shapes_in_hierarchy(mesh, 'mesh')
        
        for inc in range(0, len(self.blendshaped_meshes_list)):
            
            blend_inst = blendshape[self.blendshaped_meshes_list[inc]]
            target_mesh = target_meshes[inc]
            
            mesh_is_home = False
            
            for key in home_dict:
                home_mesh = home_dict[key]
                
                if key == home_mesh:
                    mesh_is_home = True
                    
            if mesh_is_home:
                continue
            
            is_target = blend_inst.is_target(name)
            
            if is_target:
                blend_inst.replace_target(name, target_mesh)
            if not is_target:
                
                blend_inst.create_target(name, target_mesh)
                blend_inst.disconnect_target(name)
            
        if self.is_inbetween(name):
            inbetween_parent = self.get_inbetween_parent(name)
            shape = inbetween_parent
            
            negative_parent = self.get_negative_parent(shape)
            
            if negative_parent:
                shape = negative_parent
            
        if negative_parent:
            is_negative = True
        
        if not self.is_inbetween(name) and not self.is_combo(name):
            self._add_variable(shape, is_negative)
    
        self._setup_shape_connections(name)
        
        if preserve_combos:
        
            if not combos:
                return
            
            for combo in combos:
                
                self.add_combo(combo, preserve_these[combo])
                cmds.delete(preserve_these[combo])
        
        

                    
    def turn_on_shape(self, name, value = 1):
        
        name = core.get_basename(name)
        
        last_number = util.get_trailing_number(name, as_string = True, number_count = 2)
        
        if last_number:
            
            first_part = name[:-2]
            
            for key in self.blendshape:
                
                blend_inst = self.blendshape[key]
                
                if blend_inst.is_target(first_part):
                    
                    last_number_value = int(last_number)
                    value = last_number_value * .01 * value
                    
                    self.set_shape_weight(first_part, value)
                    
                    name = first_part
                    
                #don't need to test all the meshes, just the first one will do
                break
                        
        if not last_number:
            self.set_shape_weight(name, 1 * value)
            
        return name
    
    def set_shape_weight(self, name, value):
        
        value = value
        
        for key in self.blendshape:
        
            blend_inst = self.blendshape[key]
        
            if not blend_inst.is_target(name):
                return
            
            #don't need to test all the meshes, just the first one will do
            break
        
        if name.count('_') > 0:
            return
        
        negative_parent = self.get_negative_parent(name)
        
        if negative_parent:
            value *= -1
            name = negative_parent
        
        if not cmds.objExists(self.setup_group):
            util.warning('%s does not exist. Could not set %s attribute.' % (self.setup_group, name))
            return
        
        if value < 0:
            
            var = attr.MayaNumberVariable(name)
            var.set_min_value(-1)
            var.set_max_value(1)
            var.create(self.setup_group)
        
        if cmds.objExists('%s.%s' % (self.setup_group, name)):
            cmds.setAttr('%s.%s' % (self.setup_group, name), value)
        if not cmds.objExists('%s.%s' % (self.setup_group, name)):    
            util.warning('Could not turn on shape %s' % name)
    
    def set_prune_distance(self, distance):
        self._prune_distance = distance
    
    def get_mesh(self):
        return self._get_mesh()
    
    def get_shapes(self):
        
        blendshape = self._get_blendshape()
        
        if not blendshape:
            return []
        
        
        for key in blendshape:
            
            blend_inst = blendshape[key]
            
            found = []
            
            for target in blend_inst.get_target_names():
                
                split_target = target.split('_')
                
                if split_target and len(split_target) == 1:
                    found.append(target)
            
            found.sort()
            
            #only need one shape list, meshes should have the same shapes
            return found
    
    def recreate_shape(self, name, from_shape_combo_channels = False):
        
        target = self.turn_on_shape(name)
        
        if from_shape_combo_channels:
            target = cmds.duplicate(self._get_mesh())[0]
            
        if not from_shape_combo_channels:
        
            shape_group = None
            mesh_count = len(self.blendshaped_meshes_list)
            home_dict = self._get_home_dict()
            
            for inc in range(0, mesh_count):
                
                mesh = self.blendshaped_meshes_list[inc]
                blend_inst = self.blendshape[mesh]
                
                if name.count('_') < 1:
                    
                    if blend_inst.is_target(target):
                        target = blend_inst.recreate_target(target, -1)
                        
                    if not cmds.objExists(target):
                        target = cmds.duplicate(mesh)[0]
                        
                if name.count('_') > 0:
                    
                    sub_shapes = self.get_shapes_in_combo(name, include_combos = True)
                    sub_shapes.append(name)
                    
                    new_combo = cmds.duplicate(home_dict[mesh])[0]
                    
                    new_shapes = []
                    
                    for shape in sub_shapes:
                        
                        if not blend_inst.is_target(shape):
                            continue
                        
                        new_shape = blend_inst.recreate_target(shape)
                        
                        deform.quick_blendshape(new_shape, new_combo)
                        new_shapes.append(new_shape)
                        
                    cmds.delete(new_combo, ch = True)
                    cmds.delete(new_shapes)
                    
                    if mesh_count == 1:
                        new_combo = cmds.rename(new_combo, name)
                    
                    
                    cmds.showHidden(new_combo)
                    target = new_combo
                
                if mesh_count > 1:
                    
                    
                    if not shape_group:
                        shape_group = cmds.group(em = True, n = 'temp_%s' % name)
                        shape_group = '|%s' % shape_group
                        
                    target = cmds.parent(target, shape_group)[0]
                    mesh_nice_name = core.get_basename(cmds.listRelatives(mesh, p = True)[0], remove_namespace = True)
                    
                    cmds.rename(target, mesh_nice_name)
                    
                    
                    
                    target = shape_group
            
        
        if target != name:
            target = cmds.rename(target, name )
            if not target.startswith('|'):
                target = '|%s' % target
            
        parent = cmds.listRelatives(target, p = True)
        if parent:
            target = cmds.parent(target, w = True)[0]
            
        if cmds.objExists(target):
            attr.unlock_attributes(target)
            
        return target
            
    def rename_shape(self, old_name, new_name):
        
        mesh_count = len(self.blendshaped_meshes_list)
        
        name = None
        
        for inc in range(0, mesh_count):
        
            mesh = self.blendshaped_meshes_list[inc]
            blend_inst = self.blendshape[mesh]
        
            if blend_inst.is_target(new_name):
                continue
        
            self._rename_shape_inbetweens(old_name, new_name)
            self._rename_shape_negative(old_name, new_name)
            self._rename_shape_combos(old_name, new_name)
            
            name = blend_inst.rename_target(old_name, new_name)
            
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
        
        if name == None:
            util.warning('Could not find shape named %s to rename.' % old_name)
        
        return name
        
    def remove_shape(self, name):
        
        delete_attr = True

        inbetween_parent = self.get_inbetween_parent(name)
        
        if not inbetween_parent:
        
            inbetweens = self.get_inbetweens(name)
            if inbetweens:
                for inbetween in inbetweens:
                    
                    for key in self.blendshape:
                        blend_inst = self.blendshape[key]
                        blend_inst.remove_target(inbetween)
                    
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
            
        for key in self.blendshape:
            blend_inst = self.blendshape[key]
            
            target = '%s.%s' % (blend_inst, name)
            
            input_node = attr.get_attribute_input(target, node_only=True)
            
            if input_node and input_node != self.setup_group:
                cmds.delete(input_node)
            
            blend_inst.remove_target(name)
        
        if inbetween_parent:
            self._setup_shape_connections(inbetween_parent)
        
        if not self.is_inbetween(name) and delete_attr:
            attr_name = self.setup_group + '.' + attr_shape
            if cmds.objExists(attr_name):
                cmds.deleteAttr( attr_name )
            
        
        combos = self.get_associated_combos(name)
        
        for combo in combos:
            self.remove_combo(combo)
        
    def key_shapes(self, start_frame = 0):
        
        shapes = self.get_shapes()
        
        offset = start_frame
        
        for shape in shapes:
            
            offset_next = 10
            negative = False
            
            if self.has_negative(shape):
                negative = True
                offset_next = 30
            
            cmds.setKeyframe( self.setup_group, t=offset, at=shape, v=0 )
            cmds.setKeyframe( self.setup_group, t=offset+10, at=shape, v=1 )
            
            if not negative:
                cmds.setKeyframe( self.setup_group, t=offset+20, at=shape, v=0 )
                
            if negative:
                cmds.setKeyframe( self.setup_group, t=offset+20, at=shape, v=0 )
                cmds.setKeyframe( self.setup_group, t=offset+30, at=shape, v=-1 )
                cmds.setKeyframe( self.setup_group, t=offset+40, at=shape, v=0 )
            
            
            offset += offset_next
        
    #---  combos
    
    def is_combo(self, name):
        
        if name.count('_') > 1:
            return True
        
        return False
    
    def is_combo_valid(self, name, return_invalid_shapes = False):
        
        shapes = self.get_shapes_in_combo(name)
        
        found = []
        
        for shape in shapes:
            if not self._is_target(shape):
                if not return_invalid_shapes:
                    return False
                found.append(shape)
                
        if found and return_invalid_shapes:
            return found
        
        
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
        
        
        
        result = self.is_combo_valid(nice_name, return_invalid_shapes = True)
        
        if type(result) == list:
            util.warning('Could not add combo %s, targets missing: %s' % (name,result))
            return
        
        
        
        home = self._get_mesh()
        
        if home == mesh:
            return
        
        blendshape = self._get_blendshape()
        
        if not blendshape:
            util.warning('No blendshape.')
            return
        
        combo_meshes = core.get_shapes_in_hierarchy(mesh, shape_type = 'mesh')
        
        home_dict = self._get_home_dict()
        
        for inc in range(0, len(self.blendshaped_meshes_list)):
            
            base_mesh = self.blendshaped_meshes_list[inc]
            
            blend_inst = self.blendshape[base_mesh]
            
            home = home_dict[base_mesh]
            
            combo_mesh = combo_meshes[inc]
            
            delta = self._get_combo_delta(combo_mesh, nice_name, home, blend_inst)
            
            if blend_inst.is_target(nice_name):
                blend_inst.replace_target(nice_name, delta)
            
            if not blend_inst.is_target(nice_name):
                blend_inst.create_target(nice_name, delta)
            
            cmds.delete(delta)
        
        self._setup_combo_connections(nice_name)
        
    def recreate_combo(self, name, from_shape_combo_channels = False):
        
        shape = self.recreate_shape(name, from_shape_combo_channels)
        
        return shape
        
    def remove_combo(self, name):
        
        inbetween_combo_parent = self.get_inbetween_combo_parent(name)
        
        if inbetween_combo_parent and self._is_target(inbetween_combo_parent):
            self._setup_combo_connections(name)
            
        inbetweens = self.get_inbetween_combos(name)
        
        if inbetweens:
            for inbetween in inbetweens:
                self._setup_combo_connections(inbetween, skip_update_others = True) 
        
        for key in self.blendshape:
            blend_inst = self.blendshape[key]
            
            blend_inst.remove_target(name)
            self._remove_combo_multiplies(name, blend_inst.blendshape)
    
    def get_combos(self):
        
        blendshape = self._get_blendshape()
        
        if not blendshape:
            return []
        
        found = []
        
        for key in blendshape:
            
            blend_inst = blendshape[key]
            
            for target in blend_inst.get_target_names():
                
                split_target = target.split('_')
                
                if split_target and len(split_target) > 1:
                    found.append(target)
                
            found.sort()
            
            #all meshes should have the same shape.    
            return found
        
    def find_possible_combos(self, shapes):
        
        return util.find_possible_combos(shapes)
    
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
        
        shapes = util.convert_to_sequence(shapes)
        
        combos = self.get_combos()
        
        found_combos = []
        
        for shape in shapes:
                        
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
        
        parent = '_'.join(parents)
        
        if passed:
            return parent
        
    def get_shape_and_combo_lists(self, meshes):
        
        shapes = []
        combos = []
        inbetweens = []
        
        underscore_count = {}
        inbetween_underscore_count = {}
        
        meshes.sort()
        
        nice_name_meshes = self._get_list_in_nice_names(meshes)
        
        for mesh in meshes:
            
            nice_name = core.get_basename(mesh, remove_namespace = True)
            
            if nice_name.count('_') == 0:
                
                inbetween_parent = self.get_inbetween_parent(nice_name)
                
                if inbetween_parent:
                    
                    if inbetween_parent in nice_name_meshes or self._is_target(inbetween_parent):
                        inbetweens.append(mesh)
                
                if not inbetween_parent:
                    shapes.append(mesh)
                    
                continue
            
            split_shape = nice_name.split('_')
                
            if len(split_shape) > 1:
                
                underscore_number = mesh.count('_')
                
                inbetween = False
                
                for split_name in split_shape:
                    
                    if self.is_inbetween(split_name, check_exists=False):
                        inbetween = True
                        break
                
                if inbetween:
                    
                    if not underscore_number in inbetween_underscore_count:
                        inbetween_underscore_count[underscore_number] = []
                        
                    inbetween_underscore_count[underscore_number].append(mesh)
                    
                if not inbetween:
                    
                    if not underscore_number in underscore_count:
                        underscore_count[underscore_number] = []
                        
                    underscore_count[underscore_number].append(mesh)
        
        combo_keys = list(underscore_count.keys())
        combo_keys.sort()
        
        inbetween_combo_keys = list(inbetween_underscore_count.keys())
        inbetween_combo_keys.sort()
        
        for key in combo_keys:
            combos += underscore_count[key]
            
        for key in inbetween_combo_keys:
            combos += inbetween_underscore_count[key]
        
        return shapes, combos, inbetweens
    
    #--- negatives
    
    def is_negative(self, shape, parent_shape = None):
        
        inbetween_parent = self.get_inbetween_parent(shape)
        
        if inbetween_parent:
            shape = inbetween_parent
        
        if parent_shape:
            if not shape[:-1] == parent_shape:
                return False
        
        if not self._is_target(shape):
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
        
        if self._is_target( (shape + 'N') ):
            return True
        
        return False
    
    #--- inbetweens
    
    def is_inbetween(self, shape, parent_shape = None, check_exists = True):
        
        last_number = util.get_trailing_number(shape, as_string = True, number_count=2)
        
        if not last_number:
            return False
        
        if not len(last_number) >= 2:
            return False
        
        first_part = shape[:-2]
        
        if check_exists:
            if self._is_target(first_part):
                
                if parent_shape:
                    if parent_shape == first_part:
                        return True 
                    if not parent_shape == first_part:
                        return False
                
                return True
        
        if not check_exists:
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
        
        last_number = util.get_trailing_number(inbetween, as_string = True, number_count= 2)
        
        if not last_number:
            return
        
        if not len(last_number) >= 2:
            return
        
        first_part = inbetween[:-2]
        
        return first_part
        
    def get_inbetween_value(self, shape):
        
        number_str = util.get_trailing_number(shape, as_string = True, number_count = 2)
        
        if not number_str:
            return
        
        value = int(number_str)
            
        #value = int(number_str[-2:])
        
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

def is_shape_combo_manager( group):
        
    if attr.get_vetala_type(group) == ShapeComboManager.vetala_type:
        return True
    
def get_shape_combo_managers():
    
    transforms = cmds.ls(type = 'transform')
    
    found = []
    
    for transform in transforms:
        if is_shape_combo_manager(transform):
            found.append(transform)
            
    return found

def get_shape_combo_base(shape_combo_group):
    
    mesh = attr.get_attribute_input( '%s.mesh' % shape_combo_group, node_only = True )
    
    if not mesh:
        return
    
    return mesh
    
        
@core.undo_chunk
def recreate_blendshapes(blendshape_mesh = None, follow_mesh = None):
    
    if not blendshape_mesh and not follow_mesh:
        meshes = geo.get_selected_meshes()
        if len(meshes) == 0:
            core.print_help('Please select at least one mesh.')
            return
        blendshape_mesh = meshes[0]
        if len(meshes) > 1:
            follow_mesh = meshes[1:]
    
    follow_mesh = util.convert_to_sequence(follow_mesh)
    
    if follow_mesh == [None]:
        follow_mesh = []
    
    blendshape = deform.find_deformer_by_type(blendshape_mesh, deformer_type = 'blendShape')
    
    if not blendshape:
        core.print_help('No blendshape found on first mesh.')
        return
    
    found_fm = False
    
    if follow_mesh:
        
        
        
        for fm in follow_mesh:
            
            if not fm or not cmds.objExists(fm):
                continue
            
            found_fm = True
            fm_group = cmds.group(em = True, n = 'recreated_shapes_%s' % fm)
            
            wrap = deform.create_wrap(blendshape_mesh, fm)
            
            blend = BlendShape(blendshape)
            shapes = blend.recreate_all(fm)
            shapes.sort()
            cmds.parent(shapes, fm_group)
            
            cmds.delete(wrap)
            
            wrap = deform.find_deformer_by_type(fm, deformer_type = wrap)
            if wrap:
                cmds.delete(wrap)
    if not found_fm:
        group = cmds.group(em = True, n = 'recreated_shapes')
        blend = BlendShape(blendshape)
        shapes = blend.recreate_all()
        
        
        if shapes:
            shapes.sort()
            cmds.parent(shapes, group)
            
        if not shapes:
            cmds.delete(group)


def get_inbetween_parent(inbetween):
    last_number = util.get_trailing_number(inbetween, as_string = True, number_count= 2)
    
    if not last_number:
        return
    
    if not len(last_number) >= 2:
        return
    
    first_part = inbetween[:-2]
    
    return first_part        

def find_possible_combos(shapes):
    
    return util.find_possible_combos(shapes)

def find_increment_value(shape):
    
    return util.get_trailing_number(shape, as_string = True, number_count = 2)

def is_inbetween(shape):
    last_number = util.get_trailing_number(shape, as_string = True, number_count=2)
        
    if not last_number:
        return False
    
    if not len(last_number) >= 2:
        return False
    
    return True

    

def is_negative(shape):
    
    last_letter = util.search_last_letter(shape)
    
    if last_letter == 'N':
        return True
    
    return False


@core.undo_off
def transfer_blendshape_targets(blend_source, blend_target, wrap_mesh = None, wrap_exclude_verts = [], use_delta_mush = False, use_uv = False):
    mesh = None
    
    orig_blend_target = blend_target
    
    if core.has_shape_of_type(blend_source, 'mesh'):
        
        blendshape = deform.find_deformer_by_type(blend_source, 'blendShape', return_all = False)
        
        if blendshape:
            blend_source = blendshape
    
    if core.has_shape_of_type(blend_target, 'mesh'):
        
        blendshape = deform.find_deformer_by_type(blend_target, 'blendShape', return_all = False)
        
        if blendshape:
            blend_target = blendshape
        else:
            blend_target_name = core.get_basename(blend_target)
            blend_target = cmds.deformer(blend_target, type = 'blendShape', foc = True, n = 'blendshape_%s' % blend_target_name)[0]
    
    source_blend_inst = BlendShape(blend_source)
    target_blend_inst = BlendShape(blend_target)
    
    source_targets = source_blend_inst.get_target_names()
    target_targets = target_blend_inst.get_target_names()
    
    progress = core.ProgressBar('Transfering targets...', len(source_targets))
    
    source_base = None
    
    if wrap_mesh == True:
        wrap_mesh = cmds.deformer(blend_target, q = True, geometry = True)
        if wrap_mesh:
            wrap_mesh = cmds.listRelatives(wrap_mesh[0], p = True, f = True)[0]
    
    if wrap_mesh and not mesh:
        mesh = cmds.deformer(blend_source, q = True, geometry = True)
        
        if mesh:
            mesh = cmds.listRelatives(mesh[0], p = True, f = True)[0]
    
    
    to_delete_last = []
    

    
    if mesh and not use_uv:
        orig_geo = deform.get_intermediate_object(mesh)
        if not orig_geo:
            orig_geo = mesh
        source_base = cmds.duplicate(orig_geo, n = 'source_base')[0]
        cmds.parent(source_base, w = True)
        to_delete_last.append(source_base)

    if use_uv:
        temp_uv_mesh = cmds.duplicate(orig_blend_target, n = 'temp_copyDeform')[0]
        temp_source_mesh = cmds.duplicate(mesh, n = 'temp_sourceDeform')[0]
        cmds.transferAttributes( temp_source_mesh, temp_uv_mesh,
                                             transferPositions = True, 
                                             transferNormals = False, 
                                             transferUVs = False, 
                                             transferColors = False, 
                                             sampleSpace = 3, 
                                             searchMethod = 3, 
                                             flipUVs = False, 
                                             colorBorders = True,
                                             )
        
        uv_diff_mesh = cmds.duplicate(temp_uv_mesh, n = 'temp_uv_diff_mesh')[0]
                
        to_delete_last.append(temp_uv_mesh)
        to_delete_last.append(temp_source_mesh)
        to_delete_last.append(uv_diff_mesh)
        wrap_mesh = None
    
    if not mesh:
        wrap_mesh = None
        mesh = cmds.deformer(blend_source, q = True, geometry = True)[0]
    
    for source_target in source_targets:
        to_delete = []
        progress.status('Transfering target: %s' % source_target)
        util.show('Transfering target: %s' % source_target)
        
        source_target_mesh = source_blend_inst.recreate_target(source_target)
        
        if use_uv:
            
            
            temp_target = cmds.duplicate(orig_blend_target, n = 'temp_copyDeform2')[0]
            
            blend = cmds.blendShape(source_target_mesh, temp_source_mesh, tc = False)[0]
            
            cmds.setAttr('%s.%s' % (blend, source_target_mesh), 1)
            
            blend2 = cmds.blendShape([temp_uv_mesh, uv_diff_mesh], temp_target, tc = False)[0]
            cmds.setAttr('%s.%s' % (blend2, temp_uv_mesh), 1)
            cmds.setAttr('%s.%s' % (blend2, uv_diff_mesh), -1)
            
            
            temp_target2 = cmds.duplicate(temp_target, n = 'temp_copyDeform3')[0]
            
            cmds.delete(source_target_mesh)
            cmds.delete(blend,blend2)
            cmds.delete(temp_target)
            source_target_mesh = cmds.rename(temp_target2, source_target_mesh)
            wrap_mesh = False
            
            
        #util.show('Transferring: %s' % source_target)
        
        if wrap_mesh:
            
            new_shape = cmds.duplicate(wrap_mesh, n = 'new_shape')[0]
            
            blend = cmds.blendShape(source_base, source_target_mesh, tc = False)[0]
            
            if use_delta_mush:
                cmds.deltaMush(new_shape)
            
            cmds.setAttr('%s.%s' % (blend, source_base), 1)
            
            wrap_inst = deform.create_wrap(source_target_mesh, new_shape, return_class=True)
            
            if wrap_exclude_verts:
            
                new_verts = []
                
                for vert in wrap_exclude_verts:
                    split_vert = vert.split('.')
                    new_vert = new_shape + '.' + split_vert[-1]
                    new_verts.append(new_vert)
                
                cmds.sets(new_verts, rm = '%sSet' % wrap_inst.wrap)
            
            cmds.setAttr('%s.%s' % (blend, source_base), 0)
            
            #cmds.delete(new_shape, ch = True)
            
            orig_source_mesh = cmds.rename(source_target_mesh, 'temp_source_mesh')
            
            cmds.parent(new_shape, w = True)
            source_target_mesh = cmds.rename(new_shape, source_target)
            
            to_delete += wrap_inst.base_meshes
            to_delete.append(orig_source_mesh)
        
        while source_target_mesh in target_targets:
            source_target_mesh = core.inc_name(source_target_mesh)
        
        test_mesh = mesh
        
        if use_uv:
            test_mesh = cmds.deformer(blend_target, q = True, geometry = True)[0]
        
        if wrap_mesh:
            test_mesh = wrap_mesh
        
        if not geo.is_mesh_position_same(source_target_mesh, test_mesh, check_compatible=False):
            
            target_blend_inst.create_target(source_target_mesh, source_target_mesh)
            
            input_attr = source_blend_inst.get_target_attr_input(source_target)
            output_attrs = source_blend_inst.get_target_attr_output(source_target)
            
            target_blend_inst.connect_target_attr(source_target_mesh, input_attr, output_attrs)
        
        to_delete.append(source_target_mesh)
        cmds.delete(to_delete)
        
        #cmds.delete(source_target_mesh)
        
        if progress.break_signaled():
            progress.end()
            break
        
        progress.inc()
    
    if to_delete_last:
        cmds.delete(to_delete_last)
    progress.end()
    

def get_nice_names(names):
    new_list = []
    
    for thing in names:
        new_name = core.get_basename(thing, remove_namespace = True)
        new_list.append(new_name)
    
    return new_list

def get_shape_and_combo_lists(targets):
        
        shapes = []
        negatives = []
        inbetweens = []
        combos = []
        
        
        
        underscore_count = {}
        inbetween_underscore_count = {}
        
        targets.sort()
        
        nice_name_meshes = get_nice_names(targets)
        
        for mesh in targets:
            
            
            
            nice_name = core.get_basename(mesh, remove_namespace = True)
            
            
                
            
            if nice_name.count('_') == 0:
                
                inbetween_parent = get_inbetween_parent(nice_name)
                
                if inbetween_parent:
                    
                    if inbetween_parent in nice_name_meshes:
                        inbetweens.append(mesh)
                
                if not inbetween_parent:
            
                    if is_negative(mesh):
                        negatives.append(mesh)
                    else:
                        shapes.append(mesh)
                    
                continue
            
            
            
            split_shape = nice_name.split('_')
                
            if len(split_shape) > 1:
                
                underscore_number = mesh.count('_')
                
                inbetween = False
                
                for split_name in split_shape:
                    
                    if is_inbetween(split_name):
                        inbetween = True
                        break
                
                if inbetween:
                    
                    if not underscore_number in inbetween_underscore_count:
                        inbetween_underscore_count[underscore_number] = []
                        
                    inbetween_underscore_count[underscore_number].append(mesh)
                    
                if not inbetween:
                    
                    if not underscore_number in underscore_count:
                        underscore_count[underscore_number] = []
                        
                    underscore_count[underscore_number].append(mesh)
        
        combo_keys = list(underscore_count.keys())
        combo_keys.sort()
        
        inbetween_combo_keys = list(inbetween_underscore_count.keys())
        inbetween_combo_keys.sort()
        
        for key in combo_keys:
            combos += underscore_count[key]
            
        for key in inbetween_combo_keys:
            combos += inbetween_underscore_count[key]
        
        shapes = shapes + negatives
        
        return shapes, combos, inbetweens   
    