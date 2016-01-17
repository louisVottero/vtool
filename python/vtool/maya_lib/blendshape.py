# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

import string

import vtool.util

if vtool.util.is_in_maya():
    import maya.cmds as cmds
    
import core
import attr
import deform
    
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
        
        if self.targets.has_key(name):
            target_index = self.targets[name].index
        
        return '%s.weight[%s]' % (self.blendshape, target_index)

    def _get_weights(self, target_name, mesh_index):
        mesh = self.meshes[mesh_index]
                        
        vertex_count = core.get_component_count(mesh)
        
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
        print 'blendshape created!', blendshape
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
        
    #--- target

    def is_target(self, name):
        """
        Check if name is a target on the blendshape.
        
        Args
            name (str): The name of a target.
        """
        if name in self.targets:
            return True
        
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
            
            if not cmds.objExists('%s.%s' % (self.blendshape, name)):
                cmds.setAttr('%s.weight[%s]' % (self.blendshape, current_index), 1)
                cmds.aliasAttr(name, '%s.weight[%s]' % (self.blendshape, current_index))
                cmds.setAttr('%s.weight[%s]' % (self.blendshape, current_index), 0)
            
            attr = '%s.%s' % (self.blendshape, name)
            return attr
            
        if self.is_target(name):            
            vtool.util.show('Could not add target %s, it already exist.' % name)
       
    
    def insert_target(self, name, mesh, index):
        """
        Not implemented.
        """
        pass
           
    
    def replace_target(self, name, mesh):
        """
        Replace the mesh at the target.
        
        Args
            name (str): The name of a target on the blendshape.
            mesh (str): The mesh to connect to the target.
        """
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
        """
        Remove the named target.
        
        Args
            name (str): The name of a target on the blendshape.
        """
        
        target_group = self._get_input_target_group(name)
        
        weight_attr = self._get_weight(name)
        
        cmds.removeMultiInstance(target_group, b = True)
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
            target_name (str): The name of the target.
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
    
    
    
class BlendShapeTarget(object):
    """
    Convenience for storing target information.
    """
    def __init__(self, name, index):
        self.name = name
        self.index = index
        self.connection = None
        self.value = 0
        
        
class BlendshapeManager(object):
    """
    WIP. Convenience for editing blendshape combos. 
    """
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
        
        mesh = attr.get_attribute_input( '%s.group_mesh' % self.setup_group, node_only = True )
        
        if not mesh:
            return
        
        return mesh
    
    def _get_home_mesh(self):
        if not cmds.objExists('%s.group_home' % self.setup_group):
            return
        
        mesh = attr.get_attribute_input( '%s.group_home' % self.setup_group, node_only = True )
        
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
        print 'create blendshape!'
        mesh = self._get_mesh()
        
        print 'mesh', mesh
        
        if not mesh:
            return
        
        found = deform.find_deformer_by_type(mesh, 'blendShape')
        
        print 'found', found
        
        if found:
            return
        
        print 'about to create blendshape'
        
        blendshape = BlendShape()
        blendshape.create(mesh)
        
        blendshape.rename('blendshape_%s' % mesh)
        
    def _create_home(self, mesh):
        home = self._get_home_mesh()
        
        print 'create home', home
        
        if home:
            return
        
        if not cmds.objExists(self.home):
            self.home = cmds.duplicate(mesh, n = 'home')[0]
            cmds.parent(self.home, self.setup_group)
            attr.connect_message(self.home, self.setup_group, 'home')
            
            cmds.hide(self.home)
            
    def _get_variable_name(self, target):
        
        return '%s.%s' % (self.setup_group, target)
                    
    def _get_variable(self, target):
        attributes = attr.Attributes(self.setup_group)
        
        var = attributes.get_variable(target)
        
        return var
    
    def _get_combo_delta(self, corrective_mesh, shapes, home):
        
        temp_targets = []
        
        for shape in shapes:
            new_shape = self.blendshape.recreate_target(shape)
            temp_targets.append(new_shape)
        
        print home, temp_targets, corrective_mesh
        
        delta = deform.get_blendshape_delta(home, temp_targets, corrective_mesh, replace = False)
        
        cmds.delete(temp_targets)
        
        return delta
        
                        
    def setup(self, start_mesh = None):
        print 'setup'
        if not cmds.objExists(self.setup_group):
            self.setup_group = cmds.group(em = True, n = self.setup_group)
        
            attr.hide_keyable_attributes(self.setup_group)
        
        test_home = attr.get_attribute_input('%s.group_mesh' % self.setup_group, node_only = True)
        
        print 'test home', test_home
        
        if start_mesh and not test_home:
            print 'here in setup'
            self._create_home(start_mesh)
            attr.connect_message(start_mesh, self.setup_group, 'mesh')
            
        self._create_blendshape()
        
    def zero_out(self):
        
        if not self.setup_group:
            return 
        
        attributes = attr.Attributes(self.setup_group)
        variables = attributes.get_variables()
        
        for variable in variables:
            variable.set_value(0)
    
    #--- shapes
      
    def add_shape(self, name, mesh = None):
        
        if not mesh:
            mesh = name
        
        home = self._get_mesh()
        
        if home == mesh:
            return
        
        blendshape = self._get_blendshape()
        
        if not blendshape:
            vtool.util.warning('No blendshape.')
            return
        
        if blendshape.is_target(name):
            blendshape.replace_target(name, mesh)
            return
        
        blendshape.create_target(name, mesh)
        
        var = attr.MayaNumberVariable(name)
        var.set_min_value(0)
        var.set_max_value(10)
        var.set_variable_type('float')
        var.create(self.setup_group)
                    
        multiply = attr.connect_multiply('%s.%s' % (self.setup_group, name), '%s.%s' % (blendshape.blendshape, name))
        cmds.rename(multiply, core.inc_name('multiply_shape_combo_1'))
        
    
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
        
        attributes = attr.Attributes(self.setup_group)
        attributes.rename_variable(old_name, new_name)
        
        return name
        
    def remove_shape(self, name):
        
        target = '%s.%s' % (self.blendshape.blendshape, name)
        
        input_node = attr.get_attribute_input(target, node_only=True)
        
        if input_node and input_node != self.setup_group:
            cmds.delete(input_node)
        
        self.blendshape.remove_target(name)
        
        cmds.deleteAttr( '%s.%s' % (self.setup_group,name) )
        
    
    
    #---  combos
    
    def add_combo(self, name, mesh = None):
        print 'add combo!!!', name, mesh
        if not mesh:
            mesh = name
          
        home = self._get_mesh()
        
        if home == mesh:
            print 'home is mesh'
            return
        
        blendshape = self._get_blendshape()
        
        if not blendshape:
            vtool.util.warning('No blendshape.')
            print 'no blendshape!'
            return
        
        home = self._get_home_mesh()
        
        shapes = self.get_shapes_in_combo(name)
        delta = self._get_combo_delta(mesh, shapes, home)
        
        if blendshape.is_target(name):
            blendshape.replace_target(name, delta)
        
        if not blendshape.is_target(name):
            blendshape.create_target(name, delta)
        
        print 'delta', delta
        
        cmds.delete(delta)
        
        if not attr.get_attribute_input('%s.%s' % (blendshape.blendshape, name)):
            
            last_multiply = None
            
            for shape in shapes:
                
                if not last_multiply:
                    multiply = attr.connect_multiply('%s.%s' % (blendshape.blendshape, shape), '%s.%s' % (blendshape.blendshape, name), 1)
                    
                if last_multiply:
                    multiply = attr.connect_multiply('%s.%s' % (blendshape.blendshape, shape), '%s.input2X' % last_multiply, 1)
                
                multiply = cmds.rename(multiply, core.inc_name('multiply_shape_combo_1'))
                
                last_multiply = multiply
        
    
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
    
    
        
