# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

import string

import maya.cmds as cmds
import util
import vtool.util

class BlendShape(object):
    def __init__(self, blendshape_name = None):
        self.blendshape = blendshape_name
        
        self.meshes = []
        self.targets = {}
        self.weight_indices = []
        
        if self.blendshape:
            self.set(blendshape_name)
        
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

        alias_index_map = util.map_blend_target_alias_to_index(self.blendshape)
        
        if not alias_index_map:
            return 
        
        for index in alias_index_map:
            alias = alias_index_map[index]
            
            self._store_target(alias, index)
            
    def _store_target(self, name, index):
        target = BlendShapeTarget(name, index)
        
        self.targets[name] = target
        self.weight_indices.append(index)

    def _get_target_attr(self, name):
        return '%s.%s' % (self.blendshape, name)

    def _get_weight(self, name):
        
        name = name.replace(' ', '_')
        
        target_index = self.targets[name].index
        
        return '%s.weight[%s]' % (self.blendshape, target_index)

    def _get_weights(self, target_name, mesh_index):
        mesh = self.meshes[mesh_index]
                        
        vertex_count = util.get_component_count(mesh)
        
        attribute = self._get_input_target_group_weights_attribute(target_name, mesh_index)
        
        weights = []
        
        for inc in range(0, vertex_count):
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
        target_index = self.targets[name].index
        
        value = inbetween * 1000 + 5000
        
        attribute = [self.blendshape,
                     'inputTarget[0]',
                     'inputTargetGroup[%s]' % target_index,
                     'inputTargetItem[%s]' % value,
                     'inputGeomTarget']
        
        attribute = string.join(attribute, '.')
        
        return attribute
        
    def _get_next_index(self):
        if self.weight_indices:
            return self.weight_indices[-1] + 1
        if not self.weight_indices:
            return 0

    def _disconnect_targets(self):
        for target in self.targets:
            self._disconnect_target(target)
            
    def _disconnect_target(self, name):
        target_attr = self._get_target_attr(name)
        
        connection = util.get_attribute_input(target_attr)
        
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
        
        self.blendshape = cmds.deformer(mesh, type = 'blendShape', foc = True)[0]
        self._store_targets()
        self._store_meshes()

    def rename(self, name):
        self.blendshape = cmds.rename(self.blendshape, name)
        self.set(self.blendshape)

    def set_envelope(self, value):
        cmds.setAttr('%s.envelope' % self.blendshape, value)
    
    def set(self, blendshape_name):
        self.blendshape = blendshape_name
        self._store_targets()
        self._store_meshes()
        
    #--- target

    def is_target(self, name):
        if name in self.targets:
            return True
        
    @util.undo_chunk
    def create_target(self, name, mesh, inbetween = 1):
        
        name = name.replace(' ', '_')
        
        if not self.is_target(name):
            
            current_index = self._get_next_index()
            
            self._store_target(name, current_index)
            
            mesh_input = self._get_mesh_input_for_target(name, inbetween)
            
            cmds.connectAttr( '%s.outMesh' % mesh, mesh_input)
            
            cmds.setAttr('%s.weight[%s]' % (self.blendshape, current_index), 1)
            cmds.aliasAttr(name, '%s.weight[%s]' % (self.blendshape, current_index))
            cmds.setAttr('%s.weight[%s]' % (self.blendshape, current_index), 0)
            
            attr = '%s.%s' % (self.blendshape, name)
            return attr
            
        if self.is_target(name):            
            vtool.util.show('Could not add target %s, it already exist.' % name)
       
    
    def insert_target(self, name, mesh, index):
        
        pass
           
    
    def replace_target(self, name, mesh):
        
        if not mesh:
            return
        
        name = name.replace(' ', '_')
        
        if self.is_target(name):
            
            mesh_input = self._get_mesh_input_for_target(name)
            
            if not cmds.isConnected('%s.outMesh' % mesh, mesh_input):
                cmds.connectAttr('%s.outMesh' % mesh, mesh_input)
                cmds.disconnectAttr('%s.outMesh' % mesh, mesh_input)
                
        if not self.is_target(name):
            vtool.util.show('Could not replace target %s, it does not exist' % name)
        
    def remove_target(self, name):
        
        target_group = self._get_input_target_group(name)
        weight_attr = self._get_weight(name)
        
        cmds.removeMultiInstance(target_group, b = True)
        cmds.removeMultiInstance(weight_attr, b = True)
        
        self.weight_indices.remove( self.targets[name].index )
        self.targets.pop(name)
        
        cmds.aliasAttr('%s.%s' % (self.blendshape, name), rm = True)
       
    def rename_target(self, old_name, new_name):
        
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
        if not self.is_target(name):
            return
        
        new_name = util.inc_name(name)
        
        self._disconnect_targets()
        self._zero_target_weights()
        
        self.set_weight(name, value)
        
        output_attribute = '%s.outputGeometry[0]' % self.blendshape
        
        if not mesh:
            mesh = cmds.deformer(self.blendshape, q = True, geometry = True)[0]
        
        if mesh:
            new_mesh = cmds.duplicate(mesh, name = new_name)[0]
            
            cmds.connectAttr(output_attribute, '%s.inMesh' % new_mesh)
            cmds.disconnectAttr(output_attribute, '%s.inMesh' % new_mesh)

        self._restore_connections()
        self._restore_target_weights()
        
        return new_mesh
        
    def recreate_all(self, mesh = None):
    
        self._disconnect_targets()
        self._zero_target_weights()
        
        meshes = []
        
        for target in self.targets:
            new_name = util.inc_name(target)
            
            self.set_weight(target, 1)
                    
            output_attribute = '%s.outputGeometry[0]' % self.blendshape
            
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
        self._zero_target_weights()
        
    
    #--- weights
        
    def set_weight(self, name, value):
        if self.is_target(name):
            
            attribute_name = self._get_target_attr(name)
            
            if not cmds.getAttr(attribute_name, l = True):
                cmds.setAttr(attribute_name, value)
    
    def set_weights(self, weights, target_name = None, mesh_index = 0):
        
        mesh = self.meshes[mesh_index]
        
        vertex_count  = util.get_component_count(mesh)
        
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
        
    def set_invert_weights(self, target_name = None, mesh_index = 0):
        
        weights = self._get_weights(target_name, mesh_index)
        
        new_weights = []
        
        for weight in weights:
            
            new_weight = 1 - weight
            
            new_weights.append(new_weight)
                    
        self.set_weights(new_weights, target_name, mesh_index)
    
    
    
class BlendShapeTarget(object):
    def __init__(self, name, index):
        self.name = name
        self.index = index
        self.connection = None
        self.value = 0
        
        
class BlendshapeManager(object):
    
    def __init__(self):
        
        self.start_mesh = None
        self.setup_group = 'shape_combo'
        self.home = 'home'
        self.blendshape = None
        
        if cmds.objExists(self.setup_group):
            self.start_mesh = self._get_mesh()
            self._get_blendshape()
            
        if self.start_mesh:
            self.setup(self.start_mesh)

    def _get_mesh(self):
        
        mesh = util.get_attribute_input( '%s.mesh' % self.setup_group, node_only = True )
        
        if not mesh:
            return
        
        return mesh
         
    def _get_blendshape(self):
        mesh = self._get_mesh()
        
        if not mesh:
            return
        
        blendshape = util.find_deformer_by_type(mesh, 'blendShape')
        
        self.blendshape = BlendShape(blendshape)
        
        if not blendshape:
            return None
        
        return self.blendshape
    
    def _create_blendshape(self):
        
        mesh = self._get_mesh()
        
        if not mesh:
            return
        
        found = util.find_deformer_by_type(mesh, 'blendShape')
        
        if found:
            return
        
        blendshape = BlendShape()
        blendshape.create(mesh)
        
        blendshape.rename('blendshape_%s' % mesh)
        
    def _create_home(self, mesh):
        rels = cmds.listRelatives(self.setup_group)
        
        if rels:
            if self.home in rels:
                return
        
        if not cmds.objExists(self.home):
            self.home = cmds.duplicate(mesh, n = 'home')[0]
            cmds.parent(self.home, self.setup_group)
            
            cmds.hide(self.home)
            
    def _get_variable_name(self, target):
        
        return '%s.%s' % (self.setup_group, target)
                    
    def _get_variable(self, target):
        attributes = util.Attributes(self.setup_group)
        
        var = attributes.get_variable(target)
        
        return var
                        
    def setup(self, start_mesh = None):
                        
        if not cmds.objExists(self.setup_group):
            self.setup_group = cmds.group(em = True, n = self.setup_group)
        
            util.hide_keyable_attributes(self.setup_group)
                
        if start_mesh:
            self._create_home(start_mesh)
            util.connect_message(start_mesh, self.setup_group, 'mesh')
            
        self._create_blendshape()
        
    def zero_out(self):
        
        if not self.setup_group:
            return 
        
        attributes = util.Attributes(self.setup_group)
        variables = attributes.get_variables()
        
        for variable in variables:
            variable.set_value(0)
    
    #--- shapes
      
    def add_shape(self, mesh):
        
        home = self._get_mesh()
        
        if home == mesh:
            return
        
        blendshape = self._get_blendshape()
        
        if not blendshape:
            vtool.util.warning('No blendshape.')
            return
        
        if not blendshape.is_target(mesh):
            blendshape.create_target(mesh, mesh)
        
        var = util.MayaNumberVariable(mesh)
        var.set_min_value(0)
        var.set_max_value(10)
        var.set_variable_type('float')
        var.create(self.setup_group)
                    
        util.connect_multiply('%s.%s' % (self.setup_group, mesh), '%s.%s' % (blendshape.blendshape, mesh))
            
        if blendshape.is_target(mesh):
            blendshape.replace_target(mesh, mesh)
    
    def set_shape_weight(self, name, value):
        
        value = value * 10
        
        cmds.setAttr('%s.%s' % (self.setup_group, name), value)
    
    def get_shapes(self):
        
        blendshape = self._get_blendshape()
        
        if not blendshape:
            return []
        
        found = []
        
        for target in blendshape.targets:
            
            split_target = target.split('_')
            
            if split_target and len(split_target) == 1:
                found.append(target)
            
        return found
    
    def rename_shape(self, old_name, new_name):
        
        name = self.blendshape.rename_target(old_name, new_name)
        
        attributes = util.Attributes(self.setup_group)
        attributes.rename_variable(old_name, new_name)
        
        return name
        
    def remove_shape(self, name):
        
        target = '%s.%s' % (self.blendshape.blendshape, name)
        
        input_node = util.get_attribute_input(target, node_only=True)
        
        if input_node and input_node != self.setup_group:
            cmds.delete(input_node)
        
        self.blendshape.remove_target(name)
        
        cmds.deleteAttr( '%s.%s' % (self.setup_group,name) )
    
    #---  combos
    
    def add_combo(self, mesh):
        #will need to get the delta here and do the multiply divide math
        self.add_shape(mesh)
    
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
    
    def get_shapes_in_combo(self, combo_name):
        
        shapes = combo_name.split('_')
        return shapes
    
    def get_shape_and_combo_lists(self, meshes):
        
        shapes = []
        combos = []
        inbetweens = []
        
        #inbetweens still needs to be sorted
        
        for mesh in meshes:
            
            split_shape = mesh.split('_')
            
            if len(split_shape) == 1:
                shapes.append(mesh)
                
            if len(split_shape) > 1:
                combos.append(mesh)
                
        return shapes, combos, inbetweens
    
    
        