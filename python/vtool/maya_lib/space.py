# Copyright (C) 2022 Louis Vottero louis.vot@gmail.com    All rights reserved.

from __future__ import absolute_import

import traceback
import random
import math

from .. import util
from . import api
from . import core
from . import attr
from .. import util_math

if util.in_maya:
    import maya.cmds as cmds
    import maya.api.OpenMaya as om
    core.load_plugin('matrixNodes')
    core.load_plugin('quatNodes')

#do not import geo

class VertexOctree(object):
        
    def _get_bounding_box(self, mesh):
        bounding_box = cmds.exactWorldBoundingBox(mesh)
        center = cmds.objectCenter(mesh, gl = True)
                
        large_value = -1
                
        inc = 0
                
        for box_value in bounding_box:
            
            value = box_value - center[inc]
            
            if value > 0:
                if value > large_value:
                    large_value = value
                        
            inc += 1
            if inc >= 3:
                inc = 0
        
        max_value = [large_value] * 3
        min_value = [large_value*-1] * 3
        
        max_value = [max_value[0] + center[0],max_value[1] + center[1],max_value[2] + center[2]]
        min_value = [min_value[0] + center[0],min_value[1] + center[1],min_value[2] + center[2]]
                
        return min_value + max_value + center
                    
    def create(self, mesh):
        bounding_box = self._get_bounding_box(mesh)
        
        self.top_node = VertexOctreeNode(bounding_box)
        
        mesh_fn = api.IterateGeometry(mesh)
        points = mesh_fn.get_points_as_list()
        
        for inc in range(0, len(points)):
            vertex_position = points[inc]
            self.add_vertex('%s.vtx[%s]' % (mesh, inc), vertex_position)
            
        self.top_node.sort_mesh_vertex()        
            
    def add_vertex(self, vertex_name, vertex_position):    
        self.top_node.add_vertex(vertex_name, vertex_position)
        
                
class VertexOctreeNode(object):
    
    def __init__(self, boundingBoxData):
        self.min = boundingBoxData[0:3]
        self.max = boundingBoxData[3:6]
        self.center = boundingBoxData[6:9]
        self.children = []
        self.parent = None
        self.verts = []
        self.child_verts = []
        
    def _snap_to_bounding_box(self, vector):
        new_vector = list(vector)
        
        min_value = self.min
        max_value = self.max
        
        for inc in range(0,3):
            if vector[inc] < min_value[inc]:
                new_vector[inc] = min_value[inc]
            if vector[inc] > max_value[inc]:
                new_vector[inc] = max_value[inc]
                
        return new_vector
            
        
    def _is_vector_in_range(self, min_value, max_value, vector):
        
        for inc in range(0,3):
        
            if vector[inc] < min_value[inc] or vector[inc] > max_value[inc]:
                return False
          
        return True
        
    def _get_verts_in_range(self, min_value, max_value):
        found = []
        
        if self.verts:
            for vertex in self.verts:
                vector = vertex[1] 
                
                if self._is_vector_in_range(min_value, max_value, vector):
                    
                    found_vert = False
                    for child_vert in self.child_verts:
                    
                        if vertex[0] == child_vert:
                            found_vert = True
                            break
                        
                    if not found_vert:
                        found.append(vertex)        
        
        return found
        
    def _create_child(self, min_value, max_value, verts):
        
        mid_point = util_math.get_midpoint(min_value, max_value)
        
        bounding_box = min_value + max_value + mid_point
        
        self.children.append( VertexOctreeNode(bounding_box) )
                               
        for vertex in verts:            
            self.children[-1].add_vertex(vertex[0], vertex[1])
            self.child_verts.append(vertex[0])
            
        if len(self.child_verts) == 1:
            if self.child_verts[0][0] == 'body_C.vtx[7916]':
                goo = self.createCube()
                cmds.rename(goo, 'panzy')
    
    def create_cube(self):
        cube = cmds.polyCube(ch = 0)[0]
        min_value = self.min
        max_value = self.max
                
        cmds.move(min_value[0], min_value[1], min_value[2], '%s.vtx[0]' % cube , ws = True)
        cmds.move(min_value[0], min_value[1], max_value[2], '%s.vtx[1]' % cube , ws = True )
        cmds.move(min_value[0], max_value[1], min_value[2], '%s.vtx[2]' % cube , ws = True)
        cmds.move(min_value[0], max_value[1], max_value[2], '%s.vtx[3]' % cube , ws = True)
        cmds.move(max_value[0], max_value[1], min_value[2], '%s.vtx[4]' % cube , ws = True)
        cmds.move(max_value[0], max_value[1], max_value[2], '%s.vtx[5]' % cube , ws = True)        
        cmds.move(max_value[0], min_value[1], min_value[2], '%s.vtx[6]' % cube , ws = True)
        cmds.move(max_value[0], min_value[1], max_value[2], '%s.vtx[7]' % cube , ws = True)
        
        
        return cube
        #cluster = cmds.cluster( self.get_verts() )
        #cmds.parent(cluster[1], cube)
        
    def subdivide(self):
                
        top_row1 = self.center + self.max
        
        top_row2 = [self.min[0], self.center[1], self.center[2], 
                   self.center[0], self.max[1], self.max[2]]
        
        top_row3 = [self.min[0], self.center[1], self.min[2], 
                   self.center[0], self.max[1], self.center[2]]
                   
        top_row4 = [self.center[0], self.center[1], self.min[2], 
                   self.max[0], self.max[1], self.center[2]]
                   
        btm_row1 = self.min + self.center
        
        btm_row2 = [self.center[0], self.min[1], self.min[2],
                   self.max[0], self.center[1], self.center[2]]
        
        btm_row3 = [self.min[0], self.min[1], self.center[2],
                   self.center[0], self.center[1], self.max[2]]
        
        btm_row4 = [self.center[0], self.min[1], self.center[2],
                   self.max[0], self.center[1], self.max[2]]
        
        boundings = []
        boundings.append(top_row1)
        boundings.append(top_row2)
        boundings.append(top_row3)
        boundings.append(top_row4)
        boundings.append(btm_row1)
        boundings.append(btm_row2)
        boundings.append(btm_row3)
        boundings.append(btm_row4)
                
        for bounding in boundings:
        
            min_value = bounding[0:3]
            max_value = bounding[3:6]
            
            verts = self._get_verts_in_range(min_value, max_value)
            
            if verts:
                self._create_child(bounding[0:3],bounding[3:6], verts)      
        
    def set_parent(self, parent_octree):
        self.parent = parent_octree
        
    def get_verts(self):
        found = []
        
        for vert in self.verts:
            found.append(vert[0])
            
        return found
    
    def add_vertex(self, vertex_name, vertex_position):
        self.verts.append([vertex_name, vertex_position])
    
    def has_verts(self):
        if self.verts:
            return True
        
        if not self.verts:
            return False
        
    def vert_count(self):
        return len( self.verts )
        
    def has_children(self):
        if self.children:
            return True
        
        if not self.children:
            return False
        
    def find_closest_child(self, three_number_list):
        
        closest_distance = 1000000000000000000000000000000
        found_child = None
        
        if self.has_children():
            for child in self.children:
                if self._is_vector_in_range(child.min, child.max, three_number_list):
                    return child
                    
                if child.has_children():
                    distance = util_math.get_distance(child.center, three_number_list)            
                
                    if distance < 0.001:
                        return child
                
                    if distance < closest_distance:
                        closest_distance = distance
                    
                        found_child = child
                    
        return found_child
        
    def find_closest_vertex(self, three_number_list):
        if self.vert_count() == 1:
            return self
        
        child = None
        inc = 0
        last_found = self
        vector = self._snap_to_bounding_box(three_number_list)
        
        while not child:
            
            if last_found == None:
                break
            
            child = last_found.find_closest_child(vector)
            
            if not child:
                break
            
            if child:
                last_found = child
                child = None
            
            if inc > 100:
                break
            
            inc += 1
            
        return last_found.verts[0][0]
      
    def sort_mesh_vertex(self):
        
        if self.has_verts():
            self.subdivide()
            
            if self.vert_count() > 1:
                for child in self.children:
                    child.sort_mesh_vertex()

class PinXform(object):
    """
    This allows you to pin a transform so that its parent and child are not affected by any edits.
    """
    def __init__(self, xform_name):
        self.xform = xform_name
        self.delete_later = []
        self.lock_state = {}

    def pin(self, children = None):
        """
        Create the pin constraints on parent and children.
        """
        
        self.lock_state = {}
        
        """
        parent = cmds.listRelatives(self.xform, p = True, f = True, type = 'transform')
        if parent:
            
            parent = parent[0]
            
            
            pin = cmds.duplicate(parent, po = True, n = core.inc_name('pin1'))[0]
            
            pin_parent = cmds.listRelatives(pin, p = True)
            
            if pin_parent:
                cmds.parent(pin, w = True)
            
            constraint = cmds.parentConstraint(pin, parent, mo = True)[0]
            self.delete_later.append(constraint)
            self.delete_later.append(pin)
        """
        if not children:
            children = cmds.listRelatives(self.xform, f = True, type = 'transform')
        
        if not children:
            return
        
        for child in children:
            
            if not core.is_transform(child):
                continue
            
            pin = cmds.duplicate(child, po = True, n = core.inc_name('pin1'))[0]
            
            try:
                cmds.parent(pin, w = True)
            except:
                pass
            
            lock_state_inst = attr.LockTransformState(child)
            self.lock_state[child] = lock_state_inst
            lock_state_inst.unlock()
            
            constraint = cmds.parentConstraint(pin, child, mo = True)[0]
            self.delete_later.append(constraint)
            self.delete_later.append(pin)
            
            parent = cmds.listRelatives(pin, p = True, f = True)
            if parent:
                self.delete_later.append(parent[0])
                
            
    def unpin(self):
        """
        Remove the pin. This should be run after pin.
        """
        if self.delete_later:
            cmds.delete(self.delete_later)
            
            for lock_state in self.lock_state:
                self.lock_state[lock_state].restore_initial()
                
        
    def get_pin_nodes(self):
        """
        Returns:
            list: List of nodes involved in the pinning. Ususally includes constraints and empty groups.
        """
        return self.delete_later

class MatchSpace(object):
    """
    Used to match transformation between two transform node.
    Can be used as follows:
    MatchSpace('transform1', 'transform2').translation_rotation()
    
    Args:
        
        source_transform (str): The name of a transform.
        target_transform (str): The name of a transform.
        
    
    """
    
    def __init__(self, source_transform, target_transform):
        self.source_transform = source_transform
        self.target_transform = target_transform
    
    def _get_translation(self):
        return cmds.xform(self.source_transform, q = True, t = True, ws = True)
    
    def _get_rotation(self):
        return cmds.xform(self.source_transform, q = True, ro = True, ws = True)
    
    def _get_rotate_pivot(self):
        return cmds.xform(self.source_transform, q = True, rp = True, os = True)
    
    def _get_scale_pivot(self):
        return cmds.xform(self.source_transform, q = True, sp = True, os = True)
    
    def _get_world_rotate_pivot(self):
        return cmds.xform(self.source_transform, q = True, rp = True, ws = True)
    
    def _get_world_scale_pivot(self):
        return cmds.xform(self.source_transform, q = True, sp = True, ws = True)
    
    def _set_translation(self, translate_vector = []):
        if not translate_vector:
            translate_vector = self._get_translation()
            
        cmds.xform(self.target_transform, t = translate_vector, ws = True)
    
    def _set_rotation(self, rotation_vector = []):
        if not rotation_vector:
            rotation_vector = self._get_rotation()
            
        cmds.xform(self.target_transform, ro = rotation_vector, ws = True)
        
    def _set_rotate_pivot(self, rotate_pivot_vector = []):
        if not rotate_pivot_vector:
            rotate_pivot_vector = self._get_rotate_pivot()
        cmds.xform(self.target_transform, rp = rotate_pivot_vector, os = True)
        
    def _set_world_rotate_pivot(self, rotate_pivot_vector = []):
        if not rotate_pivot_vector:
            rotate_pivot_vector = self._get_world_rotate_pivot()
        cmds.xform(self.target_transform, rp = rotate_pivot_vector, ws = True)
        
    def _set_scale_pivot(self, scale_pivot_vector = []):
        if not scale_pivot_vector:
            scale_pivot_vector = self._get_scale_pivot()
        cmds.xform(self.target_transform, sp = scale_pivot_vector, os = True)
    
    def _set_world_scale_pivot(self, scale_pivot_vector = []):
        if not scale_pivot_vector:
            scale_pivot_vector = self._get_world_scale_pivot()
        cmds.xform(self.target_transform, sp = scale_pivot_vector, ws = True)
        
    def translation(self):
        """
        Match just the translation
        """
        
        self._set_translation()
        self._set_scale_pivot()
        self._set_rotate_pivot()
        
        
        
    def rotation(self):
        """
        Match just the rotation
        """
        self._set_rotation()
        
    def translation_rotation(self):
        """
        Match translation and rotation.
        """
        
        self._set_translation()
                
        self._set_scale_pivot()
        self._set_rotate_pivot()
        
        
        
        self._set_rotation()
        
    def translation_to_rotate_pivot(self):
        """
        Match translation of target to the rotate_pivot of source.
        """
        
        translate_vector = self._get_world_rotate_pivot()
        self._set_translation(translate_vector)
        
    def rotate_scale_pivot_to_translation(self):
        """
        Match the rotate and scale pivot of target to the translation of source.
        """
        position = self._get_translation()
        
        cmds.move(position[0], 
                  position[1],
                  position[2], 
                  '%s.scalePivot' % self.target_transform, 
                  '%s.rotatePivot' % self.target_transform, 
                  a = True)
        
    def pivots(self):
        """
        Match the pivots of target to the source.
        """
        self._set_rotate_pivot()
        self._set_scale_pivot()
        
    def world_pivots(self):
        """
        Like pivots, but match in world space.
        """
        self._set_world_rotate_pivot()
        self._set_world_scale_pivot()
        
    def scale(self):
        
        
        scale_x = cmds.getAttr('%s.scaleX' % self.source_transform)
        scale_y = cmds.getAttr('%s.scaleY' % self.source_transform)
        scale_z = cmds.getAttr('%s.scaleZ' % self.source_transform)
        
        cmds.setAttr('%s.scaleX' % self.target_transform, scale_x)
        cmds.setAttr('%s.scaleY' % self.target_transform, scale_y)
        cmds.setAttr('%s.scaleZ' % self.target_transform, scale_z)

class ConstraintEditor(object):
    """
    Convenience class for editing constraints.
    """
    constraint_parent = 'parentConstraint'
    constraint_point = 'pointConstraint'
    constraint_orient = 'orientConstraint'
    constraint_scale = 'scaleConstraint'
    constraint_aim = 'aimConstraint'
    
    editable_constraints = ['parentConstraint',
                            'pointConstraint',
                            'orientConstraint',
                            'scaleConstraint',
                            'aimConstraint'
                            ]
    
    def __init__(self):
        self._set_to_last = False
    
    def _get_constraint_type(self, constraint):
        return cmds.nodeType(constraint)
        
    def has_constraint(self, transform):
        
        for constraint in self.editable_constraints:
            const = self.get_constraint(transform, constraint)
            if const:
                return True
            
        return False
        
    def get_weight_names(self, constraint):
        #CBB
        
        constraint_type = self._get_constraint_type(constraint)
        
        if constraint_type == 'scaleConstraint':
        
            found_attributes = []
                
            weights = cmds.ls('%s.target[*]' % constraint)
            
            attributes = cmds.listAttr(constraint, k = True)
                        
            for attribute in attributes:
                for inc in range(0, len(weights)):
                    if attribute.endswith('W%i' % inc):
                        found_attributes.append(attribute)
                        break
            
            return found_attributes
        
        return eval('cmds.%s("%s", query = True, weightAliasList = True, )' % (constraint_type, constraint))

    def get_weight_count(self, constraint):
        """
        Get the number of inputs weights (transforms) feeding int the constraint.
        
        Args:
            constraint (str): The name of a constraint.
        """
        return len(cmds.ls('%s.target[*]' % constraint))
    
    def get_constraint(self, transform, constraint_type):
        """
        Find a constraint on the transform.
        
        Args:
            transform (str): The name of a transform that is constrained.
            constraint_type (str): The type of constraint to search for. Eg. parentConstraint, orientConstraint, pointConstraint, etc.
            
        Retrun 
            str: The name of the constraint.
        """
        
        constraint = eval('cmds.%s("%s", query = True)' % (constraint_type, transform) )
        
        return constraint
    
    def get_transform(self, constraint):
        """
        Get the transform that the constraint is constraining.
        
        Args:
            constraint (str): The name of the constraint.
        
        Returns:
            str: The name of the transform that is being constrained.
        """
        transform = attr.get_attribute_input('%s.constraintParentInverseMatrix' % constraint)
        
        if not transform:
            return
        
        new_thing = transform.split('.')
        return new_thing[0]
    
    def get_targets(self, constraint):
        """
        Get the transforms influencing the constraint.
        
        Args:
            constraint (str): The name of the constraint.
            
        Returns:
            list: The names of the transforms affecting the constraint.
        """
        transform = self.get_transform(constraint)
        constraint_type = self._get_constraint_type(constraint)
        
        return eval('cmds.%s("%s", query = True, targetList = True)' % (constraint_type,
                                                                        transform) )
        
    def remove_target(self, target, constraint):
        """
        Remove a target from a constraint. 
        This only works if the constraint has all its original connections intact.
        
        Args:
            target (str): The name of the transform target to remove.
            constraint (str): The name of a constraint that has target affecting it.
            
        """
        transform = self.get_transform(constraint)
        constraint_type = self._get_constraint_type(constraint)
        
        return eval('cmds.%s("%s", "%s", remove = True)' % (constraint_type,
                                                            target, 
                                                            transform) )
        
    def set_interpolation(self, int_value, constraint):
        """
        Set the interpolation type of the constraint.
        
        Args:
            int_value (int): index of the interpolation type.
            constraint (str): The name of a constraint. Probably "parentConstraint" or "orientConstraint".
        """
        
        cmds.setAttr('%s.interpType' % constraint, int_value)

    def set_auto_use_last_number(self, bool_value):
        self._set_to_last = bool_value

    def create_title(self, node, constraint, title_name = 'FOLLOW'):
        """
        This will create a title enum attribute based on the targets feeding into a constraint.
        The enum will have the name of the transforms affecting the constraint.
        
        Args:
            node (str): The name of the node to add the title to.
            constraint (str): The name of a constraint. Should be affected by multipe transforms.
            title_name (str): The name to give the title attribute.
        
        """
        
        targets = self.get_targets(constraint)
        
        inc = 0
        
        names = []
        
        for target in targets:
            name = target
            
            if target.startswith('follower_'):
                parent = cmds.listRelatives(target, p = True)
                if parent:
                    parent = parent[0]
                    if parent.startswith('CNT_'):
                        name = parent
        
            name = '%s %s' % (inc, name)
            
            names.append(name)
            inc += 1
        
        attr.create_title(node, title_name, names)
        
        
    def create_switch(self, node, attribute, constraint):
        """
        Create a switch over all the target weights.
        
        Args:
            node (str): The name of the node to add the switch attribute to.
            attribute (str): The name to give the switch attribute.
            constraint (str): The name of the constraint with multiple weight target transforms affecting it.
        """
        
        attributes = self.get_weight_names(constraint)
        
        remap = attr.RemapAttributesToAttribute(node, attribute)
        remap.create_attributes(constraint, attributes)
        remap.create()
        
        if self._set_to_last:
            cmds.setAttr('%s.%s' % (node, attribute), (len(attributes)-1))
        
    def delete_constraints(self, transform, constraint_type = 'None'):
        
        if not constraint_type:
            for constraint_type in self.editable_constraints:
                constraint = self.get_constraint(transform, constraint_type)
                if constraint:
                    cmds.delete(constraint)
        
        if constraint_type:
            constraint = self.get_constraint(transform, constraint_type)
            if constraint:
                cmds.delete(constraint)
        

class IkHandle(object):
    """
    Convenience for creating ik handles.
    
    Args:
        name (str): The description to give the node. Name = 'ikHandle_(name)'.
    """
    
    solver_rp = 'ikRPsolver'
    solver_sc = 'ikSCsolver'
    solver_spline = 'ikSplineSolver'
    solver_spring = 'ikSpringSolver'
    
    def __init__(self, name):
        
        self.name = name
        
        if not name:
            self.name = core.inc_name('ikHandle')
        
        if not name.startswith('ikHandle'):
            self.name = core.inc_name('ikHandle_%s' % name)
        
        
            
        self.start_joint = None
        self.end_joint = None
        self.solver_type = self.solver_sc
        self.curve = None
        
        self.ik_handle = None
        self.joints = []
            
    
    def _create_regular_ik(self):
        ik_handle, effector = cmds.ikHandle( name = core.inc_name(self.name),
                                       startJoint = self.start_joint,
                                       endEffector = self.end_joint,
                                       sol = self.solver_type )
                           
        cmds.rename(effector, core.inc_name('effector_%s' % ik_handle))
        self.ik_handle = ik_handle
        
    def _create_spline_ik(self):
        
        if self.curve:
            
            ik_handle = cmds.ikHandle(name = core.inc_name(self.name),
                                           startJoint = self.start_joint,
                                           endEffector = self.end_joint,
                                           sol = self.solver_type,
                                           curve = self.curve, ccv = False, pcv = False)
            
            cmds.rename(ik_handle[1], 'effector_%s' % ik_handle[0])
            self.ik_handle = ik_handle[0]
            
        if not self.curve:
            
            ik_handle = cmds.ikHandle(name = core.inc_name(self.name),
                                           startJoint = self.start_joint,
                                           endEffector = self.end_joint,
                                           sol = self.solver_type,
                                           scv = False,
                                           pcv = False)
            
            cmds.rename(ik_handle[1], 'effector_%s' % ik_handle[0])
            self.ik_handle = ik_handle[0]
            
            self.curve = ik_handle[2]
            self.curve = cmds.rename(self.curve, core.inc_name('curve_%s' % self.name))
            
            self.ik_handle = ik_handle[0]
        

        
    def set_start_joint(self, joint):
        """
        Set start joint for the ik handle.
        
        Args:
            joint (str): The name of the start joint.
        """
        self.start_joint = joint
        
    def set_end_joint(self, joint):
        """
        Set end joint for the ik handle.
        
        Args:
            joint (str): The name of the end joint.
        """
        self.end_joint = joint
        
    def set_joints(self, joints_list):
        """
        Set the joints for the ik handle.
        start joint becomes the first entry.
        end joint beomces the las entry.
        
        Args:
            joints_list (list): A list of joints.
        """
        self.start_joint = joints_list[0]
        self.end_joint = joints_list[-1]
        self.joints = joints_list
        
    def set_curve(self, curve):
        """
        Set the curve for spline ik.
        
        Args:
            curve (str): The name of the curve.
        """
        self.curve = curve
        
    def set_solver(self, type_name):
        """
        Set the solver type.
        
        solver types:
        'ikRPsolver'
        'ikSCsolver'
        'ikSplineSolver'
        'ikSpringSolver'
        
        Args:
            type_name (str): The name of the solver type.
        """
        if type_name == 'ikSpringSolver':
            import maya.mel as mel
            mel.eval("ikSpringSolver")
        self.solver_type = type_name
    
    def set_full_name(self, fullname):
        """
        Set the full name for the ik handle, no prefixing or formatting added.
        """
        self.name = fullname
    
    def create(self):
        """
        Create the ik handle.
        
        Returns:
            str: The name of the ik handle.
        """
        
        
        if not self.start_joint or not self.end_joint:
            return
        
        if not self.curve and not self.solver_type == self.solver_spline:
            self._create_regular_ik()
        
        if self.curve or self.solver_type == self.solver_spline:
            self.solver_type = self.solver_spline
            self._create_spline_ik()

        
        return self.ik_handle

class OrientJoint(object):
    """
    This will orient the joint using the attributes created with OrientJointAttributes.
    """
    
    def __init__(self, joint_name, children = []):
        
        self.joint = joint_name
        self.joint_nice = core.get_basename(joint_name)
        
        #self.orient_values = None
        self.aim_vector = [1,0,0]
        self.up_vector = [0,1,0]
        self.world_up_vector = [0,1,0]
        
        self._custom_aim_vector = False
        self._custom_up_vector = False
        self._custom_world_up_vector = False
        
        self.aim_at = 3
        self.aim_up_at = 0
        
        self.children = children
        self.child = None
        self.child2 = None
        self.grand_child = None
        self.parent = None
        self.grand_parent = None
        
        self.surface = None
        
        self.invert_scale = None
        
        self.delete_later =[]
        self.world_up_vector = self._get_vector_from_axis(1)
        self.up_space_type = 'vector'
        
        self._get_relatives()
        self.orient_values = self._get_values()
        if self.orient_values and 'invertScale' in self.orient_values:
            self.invert_scale = self.orient_values['invertScale']
        
    def _get_has_scale(self):
        
        self._has_scale = False
        
        if cmds.getAttr('%s.scaleX' % self.joint) != 1:
            self._has_scale = True
            return
        if cmds.getAttr('%s.scaleY' % self.joint) != 1:
            self._has_scale = True
            return
        if cmds.getAttr('%s.scaleZ' % self.joint) != 1:
            self._has_scale = True
            return
        
        if self.orient_values and self.orient_values['invertScale'] > 0:
            if not self.has_grand_child:
                self._has_scale = True
                return
        
        
    def _unparent(self):
        if not self.children:
            self.children = cmds.listRelatives(self.joint, f = True, type = 'transform')
            
        if self.children:
            
            if self._has_scale:
                self.children = cmds.parent(self.children, w = True, r = True)
            else:
                self.children = cmds.parent(self.children, w = True)
            
            
            for child in self.children:
                parent = cmds.listRelatives(child, p = True, f = True)
                if parent:
                    parent = parent[0]
                    self.delete_later.append(parent)
                        
        """
        self.parent_children = cmds.listRelatives(self.parent, f = True, type = 'transform')
        self.parent_children = cmds.parent(self.parent_children, w = True)
        
        for child in self.parent_children:
            
            test_parent = core.get_basename(child, remove_namespace = False, remove_attribute = False)
            test_joint = core.get_basename(self.joint, remove_namespace = False, remove_attribute = False)
            
            if test_parent == test_joint:
                self.joint = child
        """
        
    def _parent(self):
        
        if self.children:
            
            cmds.parent(self.children, self.joint)
        
        
    def _update_locator_scale(self, locator):
        
        if cmds.objExists('%s.localScale' % locator):
            radius = cmds.getAttr('%s.radius' % self.joint)
            cmds.setAttr('%s.localScaleX' % locator, radius)
            cmds.setAttr('%s.localScaleY' % locator, radius)
            cmds.setAttr('%s.localScaleZ' % locator, radius)
        
    def _get_surface(self):
        
        try:
            self.surface = cmds.getAttr('%s.surface' % self.joint)
        except:
            pass
        
    def _get_relatives(self):
        
        parent = cmds.listRelatives(self.joint, p = True, f = True)
        
        if parent:
            self.parent = parent[0]
            
            grand_parent = cmds.listRelatives(self.parent, p = True, f = True)
            
            if grand_parent:
                self.grand_parent = grand_parent[0]
        
        
        if not self.children:
            self.children = cmds.listRelatives(self.joint, f = True, type = 'transform')
        
        if self.children:
            rels = cmds.listRelatives(self.joint, ad = True, f = True, type = 'transform')
            self.all_children = rels
            
    def _get_children_special_cases(self):
        
        if not self.children:
            return
        
        self.child = self.children[0]
        if len(self.children) > 1:
            self.child2 = self.children[1]
        
        grand_children = cmds.listRelatives(self.child, f = True, type = 'transform')
        
        if grand_children:
            self.grand_child = grand_children[0]
    
    def _get_vector_from_axis(self, index):
        vectors = [[1,0,0],
                   [0,1,0],
                   [0,0,1],
                   [-1,0,0],
                   [0,-1,0],
                   [0,0,-1],
                   [0,0,0]]
        
        return vectors[index]
        
    def _get_aim_at(self, index):
        
        if index < 3:
            world_aim = cmds.group(em = True, n = 'world_aim')
            MatchSpace(self.joint, world_aim).translation()
            
            if index == 0:
                cmds.move(1,0,0, world_aim, r = True)
            if index == 1:
                cmds.move(0,1,0, world_aim, r = True)
            if index == 2:
                cmds.move(0,0,1, world_aim, r = True)
                
            self.delete_later.append( world_aim )
            return world_aim
            
        if index == 3:
            
            child_aim = None
            
            if self.child and cmds.objExists(self.child):
                self._update_locator_scale(self.child)
                child_aim = self._get_position_group(self.child)
            
            if not self.child:
                util.warning('Orient is set to aim at child, but %s has no child.' % self.joint_nice)
            
            return child_aim
            
        if index == 4:
            parent_aim = self._get_position_group(self.parent)
            return parent_aim

        if index == 5:
            aim = self._get_local_group(self.parent)
            return aim
        
    def _get_aim_up_at(self, index):
        
        if index == 1:
            self.up_space_type = 'objectrotation'
            return self._get_local_group(self.parent)
        
        if index == 2:
            
            child_group = None
            
            if self.child and cmds.objExists(self.child):
                self._update_locator_scale(self.child)
                child_group = self._get_position_group(self.child)
                self.up_space_type = 'object'
                
            if not self.child or not cmds.objExists(self.child):
                util.warning('Child specified as up in orient attributes but %s has no child.' % self.joint_nice)
                
            
            return child_group
        
        if index == 3:
            
            parent_group = self._get_position_group(self.parent)
            self.up_space_type = 'object'
            return parent_group
        
        if index == 4:
            top = self._get_triangle_group(self.orient_values['triangleTop'])
            mid = self._get_triangle_group(self.orient_values['triangleMid'])
            btm = self._get_triangle_group(self.orient_values['triangleBtm'])
            
            if not top or not mid or not btm:
                
                util.warning('Could not orient %s fully with current triangle plane settings.' % self.joint_nice)
                return
            
            plane_group = get_group_in_plane(top, mid, btm)
            cmds.move(0,10,0, plane_group, r =True, os = True)
            self.delete_later.append(plane_group)
            self.up_space_type = 'object'
            return plane_group
        
        if index == 5:
            
            child_group = None
            
            if self.child2 and cmds.objExists(self.child2):
                self._update_locator_scale(self.child2)
                child_group = self._get_position_group(self.child2)
                self.up_space_type = 'object'
            
            if not self.child2 or not cmds.objExists(self.child2):
                util.warning('Child 2 specified as up in orient attributes but %s has no 2nd child.' % self.joint_nice)
            return child_group
        
        if index == 6:
            
            self._get_surface()
            
            space_group = None
                        
            if not self.surface:
                util.warning('Asked to orient to surface, but no surface given.')
                return space_group
                
            self.up_space_type = 'object'
            
            space_group = self._get_position_group(self.joint)
            space_group_xform = cmds.xform(space_group, q = True, t = True, ws = True)
            
            if core.has_shape_of_type(self.surface, 'mesh'):
                mesh_fn = api.MeshFunction(self.surface)
                normal = mesh_fn.get_closest_normal(space_group_xform, True)
                cmds.xform(space_group, ws = True, t = normal)
            if core.has_shape_of_type(self.surface, 'nurbsSurface'):
                surface_fn = api.NurbsSurfaceFunction(self.surface)
                
                normal = surface_fn.get_closest_normal(space_group_xform, True)
                cmds.xform(space_group, ws = True, t = normal)
                
        
            return space_group
            
    def _get_local_group(self, transform):
        
        local_up_group = cmds.group(em = True, n = 'local_up_%s' % transform)
        
        MatchSpace(transform, local_up_group).rotation()
        MatchSpace(self.joint, local_up_group).translation()
        
        cmds.move(1,0,0, local_up_group, relative = True, objectSpace = True)
        
        self.delete_later.append(local_up_group)
        
        return local_up_group
    
    def _get_position_group(self, transform):
        position_group = cmds.group(em = True, n = 'position_group')
        
        MatchSpace(transform, position_group).translation_to_rotate_pivot()
        
        self.delete_later.append(position_group)
        
        return position_group
        
    def _get_triangle_group(self, index):
        transform = None
        
        if index == 0:
            transform = self.grand_parent
        if index == 1:
            transform = self.parent
        if index == 2:
            transform = self.joint
        if index == 3:
            transform = self.child
        if index == 4:
            transform = self.grand_child
            
        if not transform:
            return
                
        return self._get_position_group(transform)
              
    def _create_aim(self):
        
        if not self.aim_at:
            return
        
        if not self.aim_up_at:
            
            aim = cmds.aimConstraint(self.aim_at, 
                                     self.joint, 
                                     aimVector = self.aim_vector, 
                                     upVector = self.up_vector,
                                     worldUpVector = self.world_up_vector,
                                     worldUpType = self.up_space_type)[0]
                                     
        if self.aim_up_at:
            aim = cmds.aimConstraint(self.aim_at, 
                                     self.joint, 
                                     aimVector = self.aim_vector, 
                                     upVector = self.up_vector,
                                     worldUpObject = self.aim_up_at,
                                     worldUpVector = self.world_up_vector,
                                     worldUpType = self.up_space_type)[0] 
        
        self.delete_later.append(aim)
        
    def _get_values(self):
        
        if not cmds.objExists('%s.ORIENT_INFO' % self.joint):
            return
        
        orient_attributes = attr.OrientJointAttributes(self.joint)
        return orient_attributes.get_values()
        
    def _cleanup(self):
        if self.delete_later:
            cmds.delete(self.delete_later)
        
        self.delete_later = []

    def _pin(self):
        
        if not self.children:
            return
        
        pin = PinXform(self.joint)
        if self.invert_scale:
            pin.pin(self.all_children)
        else:
            pin.pin(self.children)
        
        nodes = pin.get_pin_nodes()
        if nodes:
            self.delete_later += nodes
    
    def _freeze(self, scale = True):
        
        if scale:
            if is_rotate_scale_default(self.joint):
                return
        else:
            if is_rotate_default(self.joint):
                return
        """
        if not self.children:
            self.children = cmds.listRelatives(self.joint, f = True, type = 'transform')
            
        children = None
            
        if self.children:
            children = cmds.parent(self.children, w = True)
        """
        try:
            cmds.makeIdentity(self.joint, apply = True, r = True, s = scale)
        except:
            util.error(traceback.format_exc())
            basename = core.get_basename(self.joint)
            util.warning('Could not freeze %s when trying to orient.' % basename)

        """
        if children:
            cmds.parent(children, self.joint)
        """
    def _invert_scale(self):
        
        cmds.setAttr('%s.scaleX' % self.joint, 1)
        cmds.setAttr('%s.scaleY' % self.joint, 1)
        cmds.setAttr('%s.scaleZ' % self.joint, 1)
        
        
        if self.orient_values:
            invert_scale = self.orient_values['invertScale']
        else:
            invert_scale = self.invert_scale
        
        if invert_scale == 0:
            return
        
        #if self.children:
        #    util.warning('Orient Joints inverted scale only permitted on joints with no children. Skipping scale change on %s' % core.get_basename(self.joint))
        #    return
        
        if invert_scale == 1:
            cmds.setAttr('%s.scaleX' % self.joint, -1)
            return
        if invert_scale == 2:
            cmds.setAttr('%s.scaleY' % self.joint, -1)
            return
        if invert_scale == 3:
            cmds.setAttr('%s.scaleZ' % self.joint, -1)
            return
        if invert_scale == 4:
            cmds.setAttr('%s.scaleX' % self.joint, -1)
            cmds.setAttr('%s.scaleY' % self.joint, -1)
            return
        if invert_scale == 5:
            cmds.setAttr('%s.scaleX' % self.joint, -1)
            cmds.setAttr('%s.scaleZ' % self.joint, -1)
            return
        if invert_scale == 6:
            cmds.setAttr('%s.scaleY' % self.joint, -1)
            cmds.setAttr('%s.scaleZ' % self.joint, -1)
            return
        if invert_scale == 7:
            cmds.setAttr('%s.scaleX' % self.joint, -1)
            cmds.setAttr('%s.scaleY' % self.joint, -1)
            cmds.setAttr('%s.scaleZ' % self.joint, -1)
            return
            
    def set_aim_vector(self, vector_list):
        """
        Args:
            vector_list (list): [0,0,0] vector that defines what axis should aim.  
            If joint should aim with X axis then vector should be [1,0,0].  If joint should aim with Y axis then [0,1,0], etc.
            If up needs to be opposite of X axis then vector should be [-1,0,0].
        """
        self.aim_vector = vector_list
        self._custom_aim_vector = True
        
    def set_up_vector(self, vector_list):
        """
        Args:
            vector_list (list): [0,0,0] vector that defines what axis should aim up.  
            If joint should aim up with X axis then vector should be [1,0,0].  If joint should aim up with Y axis then [0,1,0], etc.
            If up needs to be opposite of X axis then vector should be [-1,0,0].
        """
        self.up_vector = vector_list
        self._custom_up_vector = True
        
    def set_world_up_vector(self, vector_list):
        """
        Args:
            vector_list (list): [0,0,0] vector that defines what world up axis be.  
            If world should aim up with X axis then vector should be [1,0,0].  If world should aim up with Y axis then [0,1,0], etc.
            If up needs to be opposite of X axis then vector should be [-1,0,0].
        """
        self.world_up_vector = vector_list
        self._custom_world_up_vector = True
        
    def set_aim_at(self, int_value):
        """
        Set how the joint aims.
        
        Args:
            int_value (int): 0 aim at world X, 
                                1 aim at world Y, 
                                2 aim at world Z, 
                                3 aim at immediate child. 
                                4 aim at immediate parent. 
                                5 aim at local parent, which is like aiming at the parent and then reversing direction.
        """
        self.aim_at = self._get_aim_at(int_value)
        
    def set_aim_up_at(self, int_value):
        """
        Set how the joint aims up.
        
        Args:
            int_value (int):  0 world,
                                1 parent rotate,
                                2 child position,
                                3 parent position,
                                4 triangle plane, which need to be configured to see which joints in the hierarchy it calculates with.
                                5 child 2
                                6 surface
        """
        self.aim_up_at = self._get_aim_up_at(int_value)
        
        
    def set_surface(self, surface_name):
        
        self.surface = surface_name
        
        self.set_aim_up_at(6)
        if cmds.objExists('%s.surface' % self.joint):
            try:
                cmds.setAttr('%s.surface' % self.joint, surface_name, type = 'string')
            except:
                pass
        
    def set_aim_up_at_object(self, name):
        self.aim_up_at = self._get_local_group(name)
        
        self.up_space_type = 'objectrotation'
        self.world_up_vector = [0,1,0]
    
    def set_invert_scale(self, axis_letters):
        self.invert_scale = axis_letters
    
    #@core.viewport_off
    def run(self):
        self._get_relatives()
        
        self.orient_values = self._get_values()
        
        self.has_grand_child = False
        if self.children:
            self.has_grand_child = cmds.listRelatives(self.children[0], f = True, type = 'transform')
        
        self._get_has_scale()
        
        
        
        #if self._has_scale:
        
        
        #self._unparent()
        
        self._get_children_special_cases()
        
        self._freeze(scale = True)
        self._pin()        
        
        #self._pin()
        
        util.show('Orienting %s' % core.get_basename(self.joint))
        
        try:
            cmds.setAttr('%s.rotateAxisX' % self.joint, 0)
            cmds.setAttr('%s.rotateAxisY' % self.joint, 0)
            cmds.setAttr('%s.rotateAxisZ' % self.joint, 0)
        except:
            util.show('Could not zero out rotateAxis on %s. This may cause rig errors.' % self.joint_nice)
        
        
        
        if self.orient_values:
        
            if not self._custom_aim_vector:
                self.aim_vector = self._get_vector_from_axis( self.orient_values['aimAxis'] )
            if not self._custom_up_vector:
                self.up_vector = self._get_vector_from_axis(self.orient_values['upAxis'])
            if not self._custom_world_up_vector:
                self.world_up_vector = self._get_vector_from_axis( self.orient_values['worldUpAxis'])
            
            self.aim_at = self._get_aim_at(self.orient_values['aimAt'])
            self.aim_up_at = self._get_aim_up_at(self.orient_values['aimUpAt'])
        
        if not self.orient_values:
                        
            if type(self.aim_at) == int:
                self.aim_at = self._get_aim_at(self.aim_at)
            
            if type(self.aim_up_at) == int: 
                self.aim_up_at = self._get_aim_up_at(self.aim_up_at)
        
        self._create_aim()
        
        #self._freeze(scale = False)
        
        #self._parent()
        
        if self.invert_scale:
            #if not self.has_grand_child:
                self._invert_scale()
            #else:
            #    util.warning('Inverse scale has issues with orienting chains with more than just one child. Skipping for joint: %s' % self.joint_nice)
                
        
        self._cleanup()
        
        self._freeze(scale = False)    
        
        if self.invert_scale:
            if self.child and not self.has_grand_child:
                cmds.makeIdentity(self.child, r = True, jo = True, s = True, apply = True)
        
        

class BoundingBox(util_math.BoundingBox):
    """
    Convenience for dealing with bounding boxes.
    
    Args:
        thing (str): The name of a transform in maya. Bounding box info is automatically loaded from the transform.
    """
    def __init__(self, thing, ignore_invisible = False):
        
        self.thing = thing
        
        xmin, ymin, zmin, xmax, ymax, zmax = cmds.exactWorldBoundingBox(self.thing, ii = ignore_invisible)
        
        super(BoundingBox, self).__init__([xmin, ymin, zmin], 
                                          [xmax, ymax, zmax])
        

class AttachJoints(object):
    """
    Attach a chain of joints to a matching chain.
    parentConstraint and scaleConstraint are used to make the attachment.
    """
    attach_type_constraint = 0
    attach_type_matrix = 1
    
    def __init__(self, source_joints, target_joints):
        self.source_joints = source_joints
        self.target_joints = target_joints
        self._attach_type = 0
    
    def _hook_scale_constraint(self, node):
        
        constraint_editor = ConstraintEditor()
        scale_constraint = constraint_editor.get_constraint(node, constraint_editor.constraint_scale)
        
        if not scale_constraint:
            return
        
        scale_constraint_to_world(scale_constraint)
        
    def _unhook_scale_constraint(self, scale_constraint):
        
        scale_constraint_to_local(scale_constraint)
        
    def _attach_joint(self, source_joint, target_joint):
        
        if self._attach_type == 0:
            self._hook_scale_constraint(target_joint)
            
            parent_constraint = cmds.parentConstraint(source_joint, target_joint, mo = True)[0]
            
            cmds.setAttr('%s.interpType' % parent_constraint, 2)
            
            scale_constraint = cmds.scaleConstraint(source_joint, target_joint)[0]
            
            constraint_editor = ConstraintEditor()
            constraint_editor.set_auto_use_last_number(True)
            constraint_editor.create_switch(self.target_joints[0], 'switch', parent_constraint)
            constraint_editor.create_switch(self.target_joints[0], 'switch', scale_constraint)
            
            self._unhook_scale_constraint(scale_constraint)
            
        if self._attach_type == 1:
            
            switches = SpaceSwitch().get_space_switches(target_joint)
            
            if switches:
                
                SpaceSwitch().add_source(source_joint, target_joint, switches[0])
                SpaceSwitch().create_switch(self.target_joints[0], 'switch', switches[0])
                
                
            if not switches:
                switch = SpaceSwitch(source_joint, target_joint)
                switch.set_use_weight(True)
                switch_node = switch.create()
                switch.create_switch(self.target_joints[0], 'switch', switch_node)
                        
    def _attach_joints(self, source_chain, target_chain):
        
        for inc in range( 0, len(source_chain) ):
            self._attach_joint(source_chain[inc], target_chain[inc] )
            
    def set_source_and_target_joints(self, source_joints, target_joints):
        """
        Args:
            source_joints (list): A list of joint names that should move the target.
            target_joints (list): A list of joints names that should be moved by the source.
        """
        self.source_joints = source_joints
        self.target_joints = target_joints
    
    def set_attach_type(self, attach_type):
        
        self._attach_type = attach_type
        
    def create(self):
        """
        Create the attachments.
        """
        self._attach_joints(self.source_joints, self.target_joints)

class DuplicateHierarchy(object):
    """
    Duplicate the hierachy of a transform.
    
    Args:
        transform (str): The name of a transform with child hierarchy.
    """
    def __init__(self, transform):
        
        self.top_transform = transform

        self.duplicates = []
        
        self.replace_old = None
        self.replace_new = None
        
        self.stop = False
        self.stop_at_transform = None
        
        self.only_these_transforms = None
        self._only_joints = False
        
        self._remove_user_attrs = True
        self._prefix = ''
        self._suffix = ''
        
            
    def _get_children(self, transform):
        children = cmds.listRelatives(transform, children = True, path = True, type = 'transform', f = True)
        found = []
        
        if children:
            for child in children:
                if cmds.nodeType(child).find('Constraint') > -1:
                    continue
        
                if self._only_joints:
                    if not cmds.nodeType(child) == 'joint':
                        continue
                    
                found.append(child)
        
        return found
        
    def _duplicate(self, transform):
        
        new_name = transform
        new_name = core.get_basename(new_name)
        
        if self.replace_old and self.replace_new:
            new_name = new_name.replace(self.replace_old, self.replace_new)
            
        if self._prefix:
            new_name = self._prefix + new_name
        if self._suffix:
            new_name = new_name + self._suffix
        
        duplicate = cmds.duplicate(transform, po = True)[0]
        
        if self._remove_user_attrs:
            attr.remove_user_defined(duplicate)
        
        duplicate = cmds.rename(duplicate, core.inc_name(new_name))
        
        self.duplicates.append( duplicate )
        
        return duplicate
    
    def _duplicate_hierarchy(self, transform, parent = None):
        
        base_transform = core.get_basename(transform)
        
        if base_transform == self.stop_at_transform:
            self.stop = True
        
        if self.stop:
            return
        
        top_duplicate = self._duplicate(transform)
        
        children = self._get_children(transform)
        
        if children:
            duplicate = None
            duplicates = []
            
            for child in children:
                
                child_basename = core.get_basename(child)
                
                if self.only_these_transforms and not child_basename in self.only_these_transforms:
                    
                    sub_children = self._get_children(child)
                    
                    if sub_children:
                        
                        for sub_child in sub_children:
                            
                            sub_child_basename = core.get_basename(sub_child)
                            
                            if not sub_child_basename in self.only_these_transforms:
                                continue
                            
                            duplicate = self._duplicate_hierarchy(sub_child, parent )
                            
                            if not duplicate:
                                continue
                            
                            duplicates.append(duplicate)
                        
                    continue
                
                duplicate = self._duplicate_hierarchy(child)
                
                if not duplicate:
                    break
                
                duplicates.append(duplicate)
                
                if cmds.nodeType(parent) == 'joint' and cmds.nodeType(duplicate) == 'joint':
                    
                    if cmds.isConnected('%s.scale' % transform, '%s.inverseScale' % duplicate):
                        cmds.disconnectAttr('%s.scale' % transform, '%s.inverseScale' % duplicate)
                        cmds.connectAttr('%s.scale' % parent, '%s.inverseScale' % duplicate)
                    
            if duplicates:
                cmds.parent(duplicates, top_duplicate)
        
        return top_duplicate
    
    def only_these(self, list_of_transforms):
        """
        Only duplicate transforms in list_of_transforms.
        
        Args:
            list_of_transforms (list): Names of transforms in the hierarchy.
        """
        self.only_these_transforms = list_of_transforms
    
    def only_joints(self, bool_value):
        self._only_joints = bool_value
    
    def stop_at(self, transform):
        """
        The transform at which to stop the duplication.
        
        Args:
            transform (str): The name of the transform.
        """
        relative = cmds.listRelatives(transform, type = 'transform')
        
        if relative:
            self.stop_at_transform = relative[0]
        
    def add_prefix(self, prefix):
        self._prefix = prefix
        
    def add_suffix(self, suffix):
        self._suffix = suffix
        
    def replace(self, old, new):
        """
        Replace the naming in the duplicate.
        
        Args:
            old (str): String in the duplicate name to replace.
            new (str): String in the duplicate to replace with.
        """
        self.replace_old = old
        self.replace_new = new
    
    def remove_user_attrs_on_duplicate(self, bool_value):
        self._remove_user_attrs = bool_value
    
    def create(self):
        """
        Create the duplicate hierarchy.
        """
        core.refresh()
        self._duplicate_hierarchy(self.top_transform)
        
        return self.duplicates

class BuildHierarchy(object):
    
    def __init__(self):
        self.transforms = []
        self.replace_old = None
        self.replace_new = None
    
    def _build_hierarchy(self):
        
        new_joints = []
        last_transform = None
        
        for transform in self.transforms:
            cmds.select(cl = True)
            joint = cmds.joint()
            
            name = transform
            if self.replace_old and self.replace_new:
                name = name.replace(self.replace_old, self.replace_new)
            
            joint = cmds.rename(joint, core.inc_name(name))
            
            MatchSpace(transform, joint).translation_rotation()
            MatchSpace(transform, joint).world_pivots()
            cmds.makeIdentity(joint, r = True, apply = True)
            
            new_joints.append(joint)
            
            if last_transform:
                cmds.parent(joint, last_transform)
                
            last_transform = joint
            
        return new_joints
    
    def set_transforms(self, transform_list):
        
        self.transforms = transform_list
        
    def set_replace(self, old, new):
        self.replace_old = old
        self.replace_new = new
        
    def create(self):
        new_joints = self._build_hierarchy()
        return new_joints
    
class OverDriveTranslation(object):
    
    def __init__(self, transform, driver):
        self.transform = transform
        self.driver = driver
        
        self.x_values = [1,1]
        self.y_value = [1,1]
        self.z_values = [1,1]
    
    def _create_nodes(self, description):
        
        clamp = cmds.createNode('clamp', n = core.inc_name('clamp_%s_%s' % (description, self.transform)))
        multi = cmds.createNode('multiplyDivide', n = core.inc_name('multiplyDivide_%s_%s' % (description,self.transform)))
        
        cmds.connectAttr('%s.translateX' % self.transform, '%s.inputR' % clamp)
        cmds.connectAttr('%s.translateY' % self.transform, '%s.inputG' % clamp)
        cmds.connectAttr('%s.translateZ' % self.transform, '%s.inputB' % clamp)
        cmds.connectAttr('%s.outputR' % clamp, '%s.input1X' % multi)
        cmds.connectAttr('%s.outputG' % clamp, '%s.input1Y' % multi)
        cmds.connectAttr('%s.outputB' % clamp, '%s.input1Z' % multi)
        
        return clamp, multi
        
    def _fix_value(self, value):
        
        value = abs(value) - 1.00
        
        return value
        
    def set_x(self, positive_x, negative_x):
        
        positive_x = self._fix_value(positive_x)
        negative_x = self._fix_value(negative_x)
        
        self.x_values = [positive_x, negative_x]
    
    def set_y(self, positive_y, negative_y):
        
        positive_y = self._fix_value(positive_y)
        negative_y = self._fix_value(negative_y)
        
        self.y_values = [positive_y, negative_y]
    
    def set_z(self, positive_z, negative_z):
        
        positive_z = self._fix_value(positive_z)
        negative_z = self._fix_value(negative_z)
        
        self.z_values = [positive_z, negative_z]
    
    def create(self):
        
        clamp_pos, multi_pos = self._create_nodes('pos')
        clamp_neg, multi_neg = self._create_nodes('neg')
        
        cmds.setAttr('%s.maxR' % clamp_pos, 10000)
        cmds.setAttr('%s.maxG' % clamp_pos, 10000)
        cmds.setAttr('%s.maxB' % clamp_pos, 10000)
        
        cmds.setAttr('%s.minR' % clamp_neg, -10000)
        cmds.setAttr('%s.minG' % clamp_neg, -10000)
        cmds.setAttr('%s.minB' % clamp_neg, -10000)
        
        cmds.setAttr('%s.input2X' % multi_pos, self.x_values[0])
        cmds.setAttr('%s.input2Y' % multi_pos, self.y_values[0])
        cmds.setAttr('%s.input2Z' % multi_pos, self.z_values[0])
        
        cmds.setAttr('%s.input2X' % multi_neg, self.x_values[1])
        cmds.setAttr('%s.input2Y' % multi_neg, self.y_values[1])
        cmds.setAttr('%s.input2Z' % multi_neg, self.z_values[1])
        
        plus = cmds.createNode('plusMinusAverage', n = core.inc_name('plusOverDrive_%s' % self.transform))
        
        cmds.connectAttr('%s.outputX' % multi_pos, '%s.input3D[0].input3Dx' % plus)
        cmds.connectAttr('%s.outputY' % multi_pos, '%s.input3D[0].input3Dy' % plus)
        cmds.connectAttr('%s.outputZ' % multi_pos, '%s.input3D[0].input3Dz' % plus)
        
        cmds.connectAttr('%s.outputX' % multi_neg, '%s.input3D[1].input3Dx' % plus)
        cmds.connectAttr('%s.outputY' % multi_neg, '%s.input3D[1].input3Dy' % plus)
        cmds.connectAttr('%s.outputZ' % multi_neg, '%s.input3D[1].input3Dz' % plus)      
        
        cmds.connectAttr('%s.output3Dx' % plus, '%s.translateX' % self.driver)
        cmds.connectAttr('%s.output3Dy' % plus, '%s.translateY' % self.driver)
        cmds.connectAttr('%s.output3Dz' % plus, '%s.translateZ' % self.driver) 
        
class TranslateSpaceScale(object):
    
    def __init__(self):
        
        self.x_space = []
        self.y_space = []
        self.z_space = []
        
        self.source = None
        self.target = None
        
    def set_x_space(self, positive_distance, negative_distance):
        
        self.x_space = [positive_distance, negative_distance]
        
    def set_y_space(self, positive_distance, negative_distance):
        
        self.y_space = [positive_distance, negative_distance]
        
    def set_z_space(self, positive_distance, negative_distance):
        
        self.z_space = [positive_distance, negative_distance]
        
    def set_source_translate(self, source):
        self.source = source
        
    def set_target_scale(self, target):
        self.target = target
        
    def create(self):
        
        if not self.source or not self.target:
            return
        
        if self.x_space:
        
            current_value = cmds.getAttr('%s.scaleX' % self.target)
            negate = current_value/abs(current_value)
            
            condition = attr.connect_equal_condition('%s.translateX' % self.source, '%s.scaleX' % self.target, 0)
            cmds.setAttr('%s.operation' % condition, 3)
            
            cmds.setAttr('%s.colorIfTrueR' % condition, self.x_space[0] * negate)
            cmds.setAttr('%s.colorIfFalseR' % condition, self.x_space[1] * negate)
            
        if self.y_space:
            
            current_value = cmds.getAttr('%s.scaleY' % self.target)
            negate = current_value/abs(current_value)
            
            condition = attr.connect_equal_condition('%s.translateY' % self.source, '%s.scaleY' % self.target, 0)
            cmds.setAttr('%s.operation' % condition, 3)
            
            cmds.setAttr('%s.colorIfTrueR' % condition, self.y_space[0] * negate)
            cmds.setAttr('%s.colorIfFalseR' % condition, self.y_space[1] * negate)
        
        if self.z_space:
            
            current_value = cmds.getAttr('%s.scaleZ' % self.target)
            negate = current_value/abs(current_value)
            
            condition = attr.connect_equal_condition('%s.translateZ' % self.source, '%s.scaleZ' % self.target, 0)
            cmds.setAttr('%s.operation' % condition, 3)
            
            cmds.setAttr('%s.colorIfTrueR' % condition, self.z_space[0] * negate)
            cmds.setAttr('%s.colorIfFalseR' % condition, self.z_space[1] * negate) 

class MatrixConstraintNodes(object):

    def __init__(self, source_transform, target_transform = None):
        
        self.connect_translate = True
        self.connect_rotate = True
        self.connect_scale = True
        
        self.source = util.convert_to_sequence(source_transform)
        self.target = target_transform
        
        self._decompose = True
        
        if target_transform:
            self.description = target_transform
        else:
            self.description = 'Constraint' 

        self.node_decompose_matrix = None
        
    def _create_decompose(self):
        
        if self._decompose:
            decom = core.create_node('decomposeMatrix', self.description)
            self.node_decompose_matrix = decom
            
    def _connect_decompose(self, matrix_attribute):
        
        cmds.connectAttr(matrix_attribute, '%s.inputMatrix' % self.node_decompose_matrix)    
        
        if self.connect_translate:
            cmds.connectAttr('%s.outputTranslate' % self.node_decompose_matrix, '%s.translate' % self.target)
        if self.connect_rotate:
            if cmds.nodeType(self.target) == 'joint':
                #self._create_joint_offset()
                cmds.connectAttr('%s.outputRotate' % self.node_decompose_matrix, '%s.jointOrient' % self.target)        
            else:
                cmds.connectAttr('%s.outputRotate' % self.node_decompose_matrix, '%s.rotate' % self.target)
        if self.connect_scale:
            cmds.connectAttr('%s.outputScale' % self.node_decompose_matrix, '%s.scale' % self.target)
            
    def _create_joint_offset(self):
        
        euler_to_quat = core.create_node('eulerToQuat', self.description)
        quat_invert = core.create_node('quatInvert', self.description)
        quat_prod = core.create_node('quatProd', self.description)
        self.joint_orient_quat_to_euler = core.create_node('quatToEuler', self.description)
        
        cmds.connectAttr('%s.jointOrient' % self.target, '%s.inputRotate' % euler_to_quat)
        cmds.connectAttr('%s.outputQuat' % euler_to_quat, '%s.inputQuat' % quat_invert)
        
        cmds.connectAttr('%s.outputQuat' % self.node_decompose_matrix, '%s.input1Quat' % quat_prod)
        cmds.connectAttr('%s.outputQuat' % quat_invert, '%s.input2Quat' % quat_prod)
        cmds.connectAttr('%s.outputQuat' % quat_prod, '%s.inputQuat' % self.joint_orient_quat_to_euler)
        
        cmds.connectAttr('%s.outputRotate' % self.joint_orient_quat_to_euler, '%s.rotate' % self.target)
        

    def set_description(self, description):
        self.description = description
        
    def set_decompose(self, bool_value):
        self._decompose = bool_value
        
    def set_connect_translate(self, bool_value):
        self.connect_translate = bool_value
    
    def set_connect_rotate(self, bool_value):
        self.connect_rotate = bool_value
    
    def set_connect_scale(self, bool_value):
        self.connect_scale = bool_value
        
    def create(self):
        
        self._create_decompose()

class MatrixConstraint(MatrixConstraintNodes):
    
    def __init__(self, source_transform, target_transform = None):
        
        super(MatrixConstraint, self).__init__(source_transform = source_transform, target_transform = target_transform)
        
        self.main_source = self.source[0]
        
        self.node_multiply_matrix = None
        
        self._use_target_parent_matrix = False
        
        self._maintain_offset = True
        
    def _create_matrix_constraint(self):
        
        
        
        mult = core.create_node('multMatrix', self.description)
        self.node_multiply_matrix = mult
        
        cmds.aliasAttr('jointOrientMatrix', '%s.matrixIn[0]' % mult)
        cmds.aliasAttr('offsetMatrix', '%s.matrixIn[1]' % mult)
        cmds.aliasAttr('targetMatrix', '%s.matrixIn[2]' % mult)
        cmds.aliasAttr('parentMatrix', '%s.matrixIn[3]' % mult)
        
        cmds.connectAttr('%s.worldMatrix' % self.main_source, '%s.targetMatrix' % mult)
        
        if not self.target:
            return
            
        target_matrix = cmds.getAttr('%s.worldMatrix' % self.target)
        
        if self._maintain_offset:
            source_inverse_matrix = cmds.getAttr('%s.worldInverseMatrix' % self.main_source)
        
            offset = api.multiply_matrix(target_matrix, source_inverse_matrix)
            
            cmds.setAttr('%s.offsetMatrix' % mult, offset, type = 'matrix')
        
        if self._use_target_parent_matrix:
            parent = cmds.listRelatives(self.target, p = True)
            if parent:
                cmds.connectAttr('%s.inverseMatrix' % parent[0], '%s.parentMatrix' % mult)
        else:
            cmds.connectAttr('%s.parentInverseMatrix' % self.target, '%s.parentMatrix' % mult)
        
        if self.node_decompose_matrix:
            self._connect_decompose('%s.matrixSum' % mult)
    
    def set_use_target_parent_matrix(self, bool_value):
        
        self._use_target_parent_matrix = bool_value
    
    def set_maintain_offset(self, bool_value):
        self._maintain_offset = bool_value
        
    def create(self):
        super(MatrixConstraint, self).create()
        self._create_matrix_constraint()
        
class SpaceSwitch(MatrixConstraintNodes):
    
    def __init__(self, sources = [], target = None):
        
        super(SpaceSwitch, self).__init__(sources, target)
                
        self.node_weight_add_matrix = None
        self.node_choice = None
        self._input_attribute = None
        self._weight_attributes = []
        
        self._use_weight = False
        self._switch_names = []
        self._attribute_node = target
        self._attribute_name = 'switch'
        self._maintain_offset = True
        
        self._create_title = True
        self._title_name = None
        
    def _add_source(self, source, switch_node):

        matrix = MatrixConstraint(source, self.target)
        matrix.set_maintain_offset(self._maintain_offset)
        matrix.set_decompose(False)
        
        node_type = cmds.nodeType(switch_node)
        
        matrix_node = None
        
        if node_type == 'wtAddMatrix':
            inc = attr.get_available_slot('%s.wtMatrix' % switch_node)
        
            matrix.set_description('%s_%s' % (inc+1, self.description))
            matrix.set_use_target_parent_matrix(False)
            matrix.create()
            matrix_node = matrix.node_multiply_matrix
            
            
            cmds.connectAttr('%s.matrixSum' % matrix_node, '%s.wtMatrix[%s].matrixIn' % (switch_node, inc))
            
            weight_attr = 'wtMatrix[%s].weightIn' % inc
            self._weight_attributes.append(weight_attr)
            
        if node_type == 'choice':
            inc = attr.get_available_slot('%s.input' % switch_node)
            
            matrix.set_description('%s_%s' % (inc+1, self.description))
            matrix.set_use_target_parent_matrix(False)
            matrix.create()
            matrix_node = matrix.node_multiply_matrix
            
            cmds.connectAttr('%s.matrixSum' % matrix_node, '%s.input[%s]' % (self.node_choice, inc))    
            
    
    def _create_space_switch(self):
        
        switch_node = None
        
        if self._use_weight:
            self.node_weight_add_matrix = core.create_node('wtAddMatrix', self.description)    
            matrix_attribute = '%s.matrixSum' % self.node_weight_add_matrix
            switch_node = self.node_weight_add_matrix
        else:
            self.node_choice = core.create_node('choice', self.description)
            matrix_attribute = '%s.output' % self.node_choice
            switch_node = self.node_choice
        
        if switch_node:
            for source in self.source:
                self._add_source(source, switch_node)
        
        if self.node_decompose_matrix:
            self._connect_decompose(matrix_attribute)
        
        return switch_node
        """    
        if self._input_attribute:
            
            if self._use_weight:
                
                node, attribute = attr.get_node_and_attribute(self._input_attribute)
                
                remap = attr.RemapAttributesToAttribute(node, attribute)
                remap.create_attributes(self.node_weight_add_matrix, self._weight_attributes)
                remap.create()
            
            else:
                
                if not self._switch_names:
                    switch_names = []
                    
                    inc = 1
                    for source in self.source:
                        switch_name = '%s_%s' % (inc, source)
                        switch_names.append(switch_name)
                        inc += 1
                else:
                    switch_names = self._switch_names
                            
                switch_string = ':'.join(switch_names)
                    
                if not cmds.objExists(self._input_attribute):
                    node, attribute = attr.get_node_and_attribute(self._input_attribute)
                    cmds.addAttr(node, ln = attribute, at = 'enum', enumName = switch_string, k = True)
                    
                cmds.connectAttr(self._input_attribute, '%s.selector' % self.node_choice)
        """
        
           

    def get_space_switches(self, target):
        
        attrs = ['translate','rotate','scale']
        #axis = ['X','Y','Z']
        
        found = []
        
        for attr_name in attrs:
            
            attribute = attr_name
            
            node_and_attribute = '%s.%s' % (target,attribute)
            input_value = attr.get_attribute_input(node_and_attribute, node_only=True)
            
            if input_value:
                
                if cmds.nodeType(input_value) == 'decomposeMatrix':
                    found.append(input_value)
                    break
    
        selector_dict = {}
        
        for thing in found:
            input_value = attr.get_attribute_input('%s.inputMatrix' % thing, node_only=True)
            if cmds.nodeType(input_value) == 'choice':
                selector_dict[input_value] = None 
            if cmds.nodeType(input_value) == 'wtAddMatrix':
                selector_dict[input_value] = None
            
        found = []
                
        for key in selector_dict:
            found.append(key)
            
        return found        
    
    def get_source(self, switch_node):
        
        found = []
        
        if cmds.nodeType(switch_node) == 'choice':
            indices = attr.get_indices('%s.input' % switch_node)
            
            for index in indices:
                input_attr = '%s.input[%s]' % (switch_node, index)
                
                matrix_sum = attr.get_attribute_input(input_attr, node_only = True)
                
                matrix_attr = '%s.targetMatrix' % matrix_sum
                
                if cmds.objExists(matrix_attr):
                    transform = attr.get_attribute_input(matrix_attr, node_only = True)
                    found.append(transform)
        
        if cmds.nodeType(switch_node) == 'wtAddMatrix':
            
            indices = attr.get_indices('%s.wtMatrix' % switch_node)
                        
            for index in indices:
                input_attr = '%s.wtMatrix[%s].matrixIn' % (switch_node, index)
                
                matrix_sum = attr.get_attribute_input(input_attr, node_only = True)
                
                matrix_attr = '%s.targetMatrix' % matrix_sum
                
                if cmds.objExists(matrix_attr):
                    
                    transform = attr.get_attribute_input(matrix_attr, node_only = True)
                    found.append(transform)
        
        return found
    
    def add_source(self, source_transform, target_transform, switch_node):
        self.description = target_transform
        self.target = target_transform
        self._add_source(source_transform, switch_node)
        
    def set_use_weight(self, bool_value):
        self._use_weight = bool_value
        
    def set_input_attribute(self, node, attribute, switch_names = []):
        self._attribute_node = node
        self._attribute_name = attribute
        self._switch_names = switch_names
        
    def set_maintain_offset(self, bool_value):
        self._maintain_offset = bool_value
        
    def create_title(self, bool_value, title_name = None):
        self._create_title = True
        self._title_name = title_name
        
    def create(self, create_switch = False):
        super(SpaceSwitch, self).create()
        switch_node = self._create_space_switch()
        
        if create_switch:
            
            self.create_switch(self._attribute_node, self._attribute_name, switch_node)
        
        return switch_node
        
    def create_switch(self, node, attribute, switch_node = None):
        """
        Create a switch over all the target weights.
        
        Args:
            node (str): The name of the node to add the switch attribute to.
            attribute (str): The name to give the switch attribute.
            switch_node (str): Either the choice or wtAddMatrix node of the setup. Use get_space_switches to find them
        """
        
        if self._create_title:
            if not self._title_name:
                attr.create_title(node,'SPACE')
            if self._title_name:
                attr.create_title(node,self._title_name)
                
        if cmds.nodeType(switch_node) == 'choice':
            
            sources = self.get_source(switch_node)
            
            if not self._switch_names:
                switch_names = []
                
                for source in sources:
                    #switch_name = '%s %s' % (inc, source)
                    switch_name = source
                    switch_names.append(switch_name)
                    
            else:
                switch_names = self._switch_names
            
            variable = attr.MayaEnumVariable(attribute)
            variable.set_node(node)
            variable.set_keyable(True)
            variable.create(node)
            variable.set_enum_names(switch_names)
            variable.set_locked(False)
            variable.set_value( (len(switch_names)-1) )
            variable.connect_out('%s.selector' % switch_node)
            
            
            
        if cmds.nodeType(switch_node) == 'wtAddMatrix':
            
            indices = attr.get_indices('%s.wtMatrix' % switch_node)
            
            attributes = []
            
            for index in indices:
                attributes.append('wtMatrix[%s].weightIn' % index)
            
            remap = attr.RemapAttributesToAttribute(node, attribute)
            remap.create_attributes(switch_node, attributes)
            remap.create()
            
            if len(attributes) > 1:
                try:
                    cmds.setAttr('%s.%s' % (node, attribute), (len(attributes)-1))
                except:
                    pass
            
            if len(attributes) == 1:
                cmds.setAttr('%s.wtMatrix[0].weightIn' % switch_node, 1)

class SpaceSwitchPairBlend(object):
    
    def __init__(self, source1, source2, target):
        
        self.source1 = source1
        self.source2 = source2
        self.target = target
        
        self.description = None
        self._attribute_node = target
        self._attribute_name = 'offOn'
        self._attribute = self._attribute_node + '.' + self._attribute_name
        
        
    def _build_attribute(self):
        
        if not cmds.objExists(self._attribute):
            cmds.addAttr(self._attribute_node, ln = self._attribute_name, min = 0, max = 1, k = True)
        
    def connect_linear(self, attribute_name):
        
        blend = core.create_node('blendColors', self.description)
        
        cmds.connectAttr('%s.%sX' % (self.source2, attribute_name), '%s.color1R' % blend)
        cmds.connectAttr('%s.%sY' % (self.source2, attribute_name), '%s.color1G' % blend)
        cmds.connectAttr('%s.%sZ' % (self.source2, attribute_name), '%s.color1B' % blend)
        
        cmds.connectAttr('%s.%sX' % (self.source1, attribute_name), '%s.color2R' % blend)
        cmds.connectAttr('%s.%sY' % (self.source1, attribute_name), '%s.color2G' % blend)
        cmds.connectAttr('%s.%sZ' % (self.source1, attribute_name), '%s.color2B' % blend)
        
        cmds.connectAttr('%s.outputR' % blend, '%s.%sX' % (self.target,attribute_name))
        cmds.connectAttr('%s.outputG' % blend, '%s.%sY' % (self.target,attribute_name))
        cmds.connectAttr('%s.outputB' % blend, '%s.%sZ' % (self.target,attribute_name))
        
        if self._attribute:
            cmds.connectAttr(self._attribute, '%s.blender' % blend)
        
    def connect_pair_blend(self):
        
        blend = core.create_node('pairBlend', self.description)
        
        cmds.connectAttr('%s.translateX' % self.source1, '%s.inTranslateX1' % blend)
        cmds.connectAttr('%s.translateY' % self.source1, '%s.inTranslateY1' % blend)
        cmds.connectAttr('%s.translateZ' % self.source1, '%s.inTranslateZ1' % blend)
        cmds.connectAttr('%s.translateX' % self.source2, '%s.inTranslateX2' % blend)   
        cmds.connectAttr('%s.translateY' % self.source2, '%s.inTranslateY2' % blend)
        cmds.connectAttr('%s.translateZ' % self.source2, '%s.inTranslateZ2' % blend)
        
        cmds.connectAttr('%s.rotateX' % self.source1, '%s.inRotateX1' % blend)
        cmds.connectAttr('%s.rotateY' % self.source1, '%s.inRotateY1' % blend)
        cmds.connectAttr('%s.rotateZ' % self.source1, '%s.inRotateZ1' % blend)
        cmds.connectAttr('%s.rotateX' % self.source2, '%s.inRotateX2' % blend)   
        cmds.connectAttr('%s.rotateY' % self.source2, '%s.inRotateY2' % blend)
        cmds.connectAttr('%s.rotateZ' % self.source2, '%s.inRotateZ2' % blend)
        
        cmds.connectAttr('%s.outTranslateX' % blend, '%s.translateX' % self.target)
        cmds.connectAttr('%s.outTranslateY' % blend, '%s.translateY' % self.target)
        cmds.connectAttr('%s.outTranslateZ' % blend, '%s.translateZ' % self.target)
        
        cmds.connectAttr('%s.outRotateX' % blend, '%s.rotateX' % self.target)
        cmds.connectAttr('%s.outRotateY' % blend, '%s.rotateY' % self.target)
        cmds.connectAttr('%s.outRotateZ' % blend, '%s.rotateZ' % self.target)
        
        cmds.setAttr('%s.rotInterpolation' % blend, 1)
        
        if self._attribute:
            cmds.connectAttr(self._attribute, '%s.weight' % blend)
        
    def set_description(self, description):
        self.description = description
    
    def set_attribute_control(self, node, attribute_name):
        
        self._attribute_node = node
        self._attribute_name = attribute_name
        self._attribute = node + '.' + attribute_name
    
    def create(self):
        
        self._build_attribute()
        
        self.connect_pair_blend()
        self.connect_linear('scale')

def has_constraint(transform):
    """
    Find out if a constraint is affecting the transform.
    
    Args:
        transform (str): The name of a transform.
    """
    editor = ConstraintEditor()
    return editor.has_constraint(transform)
    
def delete_constraints(transform, constraint_type = None):
    """
    Delete constraints on transform.
    """
    editor = ConstraintEditor()
    editor.delete_constraints(transform, constraint_type)
    
    
def is_transform_default(transform):
    """
    Check if a transform has the default values (identity matrix).
    
    For example:
    
    transate = [0,0,0]
    
    rotate = [0,0,0]
    
    scale = [1,1,1]
    
    Returns:
        bool
    """
    attributes = ['translate', 'rotate']
    
    for attribute in attributes:
        
        for axis in ['X','Y','Z']:
            value = cmds.getAttr('%s.%s%s' % (transform, attribute, axis)) 
            if value < -0.00001 or value > 0.00001:
                return False
            
    for axis in ['X','Y','Z']:
        if cmds.getAttr('%s.scale%s' % (transform, axis)) != 1:
            return False
    
    return True

def is_rotate_default(transform):
    
    attributes = ['rotate']
    
    for attribute in attributes:
        
        for axis in ['X','Y','Z']:
            value = cmds.getAttr('%s.%s%s' % (transform, attribute, axis)) 
            if value < -0.00001 or value > 0.00001:
                return False
            
    return True
        
def is_rotate_scale_default(transform):
    
    attributes = ['rotate']
    
    for attribute in attributes:
        
        for axis in ['X','Y','Z']:
            value = cmds.getAttr('%s.%s%s' % (transform, attribute, axis)) 
            if value < -0.00001 or value > 0.00001:
                return False
            
    for axis in ['X','Y','Z']:
        if cmds.getAttr('%s.scale%s' % (transform, axis)) != 1:
            return False
    
    return True

def get_non_default_transforms(transforms = None):
    """
    Get transforms in the scene that don't have default values.
    
    Returns:
        list
    """
    if not transforms:
        transforms = cmds.ls(type = 'transform')
    
    found = []
    
    for transform in transforms:
        
        
        
        if cmds.nodeType(transform) == 'joint':
            continue
        if core.has_shape_of_type(transform, 'camera'):
            continue
        if cmds.nodeType(transform) == 'aimConstraint':
            continue
        if cmds.nodeType(transform) =='pointConstraint':
            continue
        if cmds.nodeType(transform) == 'orientConstraint':
            continue
        if cmds.nodeType(transform) == 'parentConstraint':
            continue
        if cmds.nodeType(transform) == 'ikHandle':
            continue
        
        if not is_transform_default(transform):
            found.append(transform)
            
    return found
    
def zero_out_transform_channels(transform):
    """
    Zero out the translate and rotate on a transform.
    """
    
    transforms = util.convert_to_sequence(transform)
    
    
    for thing in transforms:
        cmds.setAttr('%s.translateX' % thing, 0)
        cmds.setAttr('%s.translateY' % thing, 0)
        cmds.setAttr('%s.translateZ' % thing, 0)
        cmds.setAttr('%s.rotateX' % thing, 0)
        cmds.setAttr('%s.rotateY' % thing, 0)
        cmds.setAttr('%s.rotateZ' % thing, 0)
    
def zero_out_pivot(transform):
    
    cmds.xform(transform, ws = True, rp = [0,0,0])
    cmds.xform(transform, ws = True, sp = [0,0,0])

def get_hierarchy_path(top_transform, btm_transform):
    """
    Gets relatives in the hierarchy between top_transform and btm_transform
    
    Args:
        top_transform (str): The name of the top transform.
        btm_transform (str): The name of the btm transform. Needs to be a child of top_transform.
    """
    
    parent = cmds.listRelatives(btm_transform, p = True)
    if parent:
        parent = parent[0]
            
    path = []
    path.append(btm_transform)
    
    parent_found = False
    
    while parent:
        
        path.append(parent)
        
        if parent_found:
            break
        
        parent = cmds.listRelatives(parent, p = True)
        
        
        
        if parent:
            parent = parent[0]
            
        if parent == top_transform:
            parent_found = True
    
    if not parent_found:
        return
    
    if parent_found:
        path.reverse()
        return path

def get_bounding_box_size(transform):
    """
    Get the size of the bounding box.
    
    Returns:
        float
    """
    components = core.get_components_in_hierarchy(transform)
    
    if components:
        transform = components
        
    bounding_box = BoundingBox(transform)
    
    return bounding_box.get_size()

def get_center(transform):
    """
    Get the center of a selection. Selection can be component or transform.
    
    Args:
        transform (str): Name of a node in maya.
    
    Returns: 
        vector list:  The center vector, eg [0,0,0]
    """
    
    list = util.convert_to_sequence(transform)
    
    components = []
    
    for thing in list:
        if cmds.nodeType(transform) == 'transform' or cmds.nodeType(transform) == 'joint':
            sub_components = core.get_components_in_hierarchy(transform)
            if sub_components and type(sub_components) == list:
                components += sub_components
        
        if thing.find('.') > -1:
            components.append(thing)
        
    
    
    if components:
        transform = components
        
    bounding_box = BoundingBox(transform)
    return bounding_box.get_center()

def get_btm_center(transform):
    """
    Get the bottom center of a selection. Selection can be component or transform.
    
    Args:
        transform (str): Name of a node in maya.
    
    Returns: 
        vector list: The btrm center vector, eg [0,0,0]
    """
    
    components = core.get_components_in_hierarchy(transform)
    
    if components:
        transform = components
        
    
    
    bounding_box = BoundingBox(transform)
    return bounding_box.get_ymin_center()

def get_top_center(transform):
    """
    Get the top center of a selection. Selection can be component or transform.
    
    Args:
        transform (str): Name of a node in maya.
    
    Returns: 
        vector list: The top center vector, eg [0,0,0]
    """
    
    components = core.get_components_in_hierarchy(transform)
    
    if components:
        transform = components
        
    bounding_box = BoundingBox(transform)
    return bounding_box.get_ymax_center()

def get_longest_aligned_vectors(transform):
    """
    When auto placing joints, this can help allign them to the mesh. 
    If the model is not square it, the two vectors will be aligned to longest length of the model.
    """
    
    components = core.get_components_in_hierarchy(transform)
    
    if components:
        transform = components
        
    bounding_box = BoundingBox(transform)
    return bounding_box.get_longest_two_axis_vectors()
    



def get_closest_transform(source_transform, targets):
    """
    Given the list of target transforms, find the closest to the source transform.
    
    Args:
        source_transform (str): The name of the transform to test distance to.
        targets (list): List of targets to test distance against.
        
    Returns:
        str: The name of the target in targets that is closest to source_transform.
    """
    
    least_distant = 1000000.0
    closest_target = None
    
    for target in targets:
        
        distance = get_distance(source_transform, target)
        
        if distance < least_distant:
            least_distant = distance
            closest_target = target
            
    return closest_target 

def get_middle_transform(transform_list):
    """
    Given a list of transforms, find the middle index. If the list is even, then find the midpoint between the middle two indices.
    
    Args:
        transform_list (list): A list of transforms in order. Transforms should make a hierarchy or a sequence, where the order of the list matches the order in space.
    
    Returns: 
        list: [x,y,z] the midpoint.
    """
    
    
    count = len(transform_list)
    division = count/2
    
    if count == 0:
        return
    
    if (division + division) == count:
        midpoint = get_midpoint(transform_list[division-1], transform_list[division])
    
    if (division + division) != count:
        midpoint = cmds.xform(transform_list[division], q = True, t = True, ws = True)
    
    return midpoint
    

def get_distance(source, target):
    """
    Get the distance between the source transform and the target transform.
    
    Args:
        source (str): The name of a transform.
        target (str): The name of a transform.
    
    Returns: 
        float: The distance between source and target transform.
    """
    #CBB
    
    vector1 = cmds.xform(source, 
                         query = True, 
                         worldSpace = True, 
                         rp = True)
    
    vector2 = None
    

    if cmds.nodeType(target) == 'mesh':
        vector2 = cmds.xform(target, 
                             query = True, 
                             worldSpace = True, 
                             t = True)
        
    if not vector2:    
        vector2 = cmds.xform(target, 
                             query = True, 
                             worldSpace = True, 
                             rp = True)
    
    return api.get_distance(vector1, vector2)



def get_chain_length(list_of_joints_in_chain):
    
    joints = list_of_joints_in_chain
    
    length = 0
    
    joint_count = len(joints)
    
    for inc in range(0, joint_count):
        if inc+1 == joint_count:
            break
        
        current_joint = joints[inc]
        next_joint = joints[inc+1]
        
        distance =  get_distance(current_joint, next_joint)
        
        length += distance
        
    return length

def get_midpoint( source, target):
    """
    Get the midpoint between the source transform and the target transform.
    
    Args:
        source (str): The name of a transform.
        target (str): The name of a transform.
    
    Returns: 
        vector list: The midpoint as [0,0,0] vector between source and target transform.
    """
    
    if cmds.nodeType(source) == 'transform':
        vector1 = cmds.xform(source, 
                             query = True, 
                             worldSpace = True, 
                             rp = True)
    else:
        vector1 = cmds.xform(source, 
                             query = True, 
                             worldSpace = True, 
                             t = True)
    
    if cmds.nodeType(source) == 'transform':
        vector2 = cmds.xform(target, 
                                query = True, 
                                worldSpace = True, 
                                rp = True)
    else:
        vector2 = cmds.xform(target, 
                                query = True, 
                                worldSpace = True, 
                                t = True)
    
    return util_math.get_midpoint(vector1, vector2)

def get_distances(sources, target):
    """
    Given a list of source transforms, return a list of distances to the target transform
    
    Args:
        sources (list): The names of a transforms.
        target (str): The name of a transform.
    
    Returns: 
        list: The distances betweeen each source and the target.
    """
    
    distances = []
    
    for source in sources:
        
        distance = get_distance(source, target)
        distances.append(distance)
    
    
    return distances
        
def get_polevector(transform1, transform2, transform3, offset = 1):
    #CBB
    """
    Given 3 transforms eg. arm, elbow, wrist.  Return a vector of where the pole vector should be located.
        
    Args:
        transform1 (str): name of a transform in maya. eg. joint_arm.
        transform2 (str): name of a transform in maya. eg. joint_elbow.
        transform3 (str): name of a transform in maya. eg. joint_wrist.
        
    Returns: 
        vector list: The triangle plane vector eg. [0,0,0].  This is good for placing the pole vector.
    """
    
    distance = get_distance(transform1, transform3)
    
    group = get_group_in_plane(transform1, 
                               transform2, 
                               transform3)
    
    cmds.move(0, offset * distance, 0, group, r =True, os = True)
    finalPos = cmds.xform(group, q = True, ws = True, rp = True)

    cmds.delete(group)
    
    return finalPos

def get_group_in_plane(transform1, transform2, transform3):
    """
    Create a group that sits in the triangle plane defined by the 3 transforms.
    
    Args:
        transform1 (str): name of a transform in maya. eg. joint_arm.
        transform2 (str): name of a transform in maya. eg. joint_elbow.
        transform3 (str): name of a transform in maya. eg. joint_wrist.
        
    Returns: 
        vector list: The triangle plane vector eg. [0,0,0].  This is good for placing the pole vector.
    """
    #CBB
    
    pole_group = cmds.group(em=True)
    match = MatchSpace(transform1, pole_group)
    match.translation_rotation()
    
    cmds.aimConstraint(transform3, pole_group, 
                       offset = [0,0,0], 
                       weight = 1, 
                       aimVector = [1,0,0], 
                       upVector = [0,1,0], 
                       worldUpType = "object", 
                       worldUpObject = transform2)
    
    pole_group2 = cmds.group(em = True, n = 'pole_%s' % transform1)
    match = MatchSpace(transform2, pole_group2)
    match.translation_rotation()
    
    cmds.parent(pole_group2, pole_group)
    cmds.makeIdentity(pole_group2, apply = True, t = True, r = True )
    cmds.parent(pole_group2, w = True)
    
    cmds.delete(pole_group)
    
    return pole_group2

def get_ordered_distance_and_transform(source_transform, transform_list):
    """
    Return a list of distances based on how far each transform in transform list is from source_transform.
    Return a distance dictionary with each distacne key returning the corresponding transform.
    Return a list with the original distance order has fed in from transform_list.
    
    Args:
        source_transform (str)
        
        transform_list (list)
        
    Returns:
        dict
        
    """
    
    
    distance_list = []
    distance_dict = {}
    
    for transform in transform_list:
        distance = get_distance(source_transform, transform)
        
        distance_list.append(distance)
        
        if distance in distance_dict:
            distance_dict[distance].append(transform)
        if not distance in distance_dict:
            distance_dict[distance] = [transform]
        
    
    original_distance_order = list(distance_list)
    
    distance_list.sort()
    
    return distance_list, distance_dict, original_distance_order

def get_transform_list_from_distance(source_transform, transform_list):
    """
    Return a list of distances that corresponds to the transform_list. Each transform's distance from source_transform. 
    """
    
    distance_list, distance_dict, original = get_ordered_distance_and_transform(source_transform, transform_list)
    
    found = []
    
    for distance in distance_list:
        found.append(distance_dict[distance][0])
        
    return found

def get_side(transform, center_tolerance):
    """
    Get the side of a transform based on its position in world space.
    Center tolerance is distance from the center to include as a center transform.
    
    Args:
        transform (str): The name of a transform.
        center_tolerance (float): How close to the center the transform must be before it is considered in the center.
        
    Returns:
        str: The side that the transform is on, could be 'L','R' or 'C'.
    """
    if type(transform) == list or type(transform) == tuple:
        position = transform
    
    if not type(transform) == list and not type(transform) == tuple:
        position = cmds.xform(transform, q = True, ws = True, rp = True)
        
    if position[0] > 0:
        side = 'L'

    if position[0] < 0:
        side = 'R'
        
    if position[0] < center_tolerance and position[0] > center_tolerance*-1:
        side = 'C'
            
    return side

def get_axis_vector(transform, axis_vector):
    """
    This currently only works on transforms that have not been frozen.
    It does not work on joints. 
    
    Get the vector matrix product.
    If you give it a vector [1,0,0], it will return the transform's x point.
    If you give it a vector [0,1,0], it will return the transform's y point.
    If you give it a vector [0,0,1], it will return the transform's z point.
    
    Args:
        transform (str): The name of a transform. Its matrix will be checked.
        axis_vector (list): A vector. X = [1,0,0], Y = [0,1,0], Z = [0,0,1] 
        
    Returns:
        list: The result of multiplying the vector by the matrix. Good to get an axis in relation to the matrix.
    """
    
    node = cmds.createNode('vectorProduct')
    group = cmds.group(em = True)
    cmds.connectAttr('%s.worldMatrix' % transform, '%s.matrix' % node)
    cmds.setAttr('%s.input1X' % node, axis_vector[0])
    cmds.setAttr('%s.input1Y' % node, axis_vector[1])
    cmds.setAttr('%s.input1Z' % node, axis_vector[2])
    
    #not working, need to test
    #t_func = api.TransformFunction(transform)
    #new_vector = t_func.get_vector_matrix_product(axis_vector)
    cmds.setAttr( '%s.operation' % node, 4)
    
    
    cmds.connectAttr('%s.output' % node, '%s.translate' % group)
    
    new_vector = cmds.getAttr('%s.translate' % group)[0] 
    
    cmds.delete(node)
    cmds.delete(group)
    
    return new_vector

def get_axis_aimed_at_child(transform):
    
    children = cmds.listRelatives(transform, type = 'joint')
    
    if not children:
        return
    
    pos1 = cmds.xform(transform, q = True, ws = True, t = True)
    pos2 = cmds.xform(children[0], q = True, ws = True, t = True)
    
    pos2 = util_math.vector_sub(pos2, pos1)
    
    all_axis = [[1,0,0], [-1,0,0], [0,1,0], [0,-1,0], [0,0,1], [0,0,-1]]
    
    good_axis = [0,0,0]
    
    current_result = 0
    
    for axis in all_axis:
        axis_vector = get_axis_vector(transform, axis_vector = axis)
        axis_vector = util_math.vector_sub(axis_vector, pos1)
        
        vector1 = util_math.Vector(axis_vector)
        vector2 = util_math.Vector(pos2)
        
        
        result = util_math.get_dot_product(vector1, vector2)
        
        if result > current_result:
            good_axis = axis
            current_result = result
            
    
    return good_axis

def get_axis_letter_aimed_at_child(transform):
    
    vector = get_axis_aimed_at_child(transform)
    return get_vector_axis_letter(vector)

def get_vector_axis_letter(vector):
    
    if vector == [1,0,0]:
        return 'X'
    if vector == [0,1,0]:
        return 'Y'
    if vector == [0,0,1]:
        return 'Z'
    if vector == [-1,0,0]:
        return '-X'
    if vector == [0,-1,0]:
        return '-Y'
    if vector == [0,0,-1]:
        return '-Z'
    
def world_matrix_equivalent(transform1, transform2):
    matrix1 = cmds.getAttr('%s.worldMatrix' % transform1)
    matrix2 = cmds.getAttr('%s.worldMatrix' % transform2)
    
    matrix1 = om.MMatrix(matrix1)
    matrix2 = om.MMatrix(matrix2)
    
    equivalent = matrix1.isEquivalent( matrix2 )
    
    return equivalent

def get_ik_from_joint(joint):
    
    outputs = attr.get_attribute_outputs('%s.message' % joint, True)
    
    iks = []
    
    for output in outputs:
        
        node_type = cmds.nodeType(output)
        
        if node_type == 'ikHandle':
            iks.append(output)
            
    return iks
        
def create_follow_fade(source_guide, drivers, skip_lower = 0.0001):
    """
    Create a multiply divide for each transform in drivers with a weight value based on the distance from source_guide.
    
    Args:
        source_guide (str): Name of a transform in maya to calculate distance.
        drivers (list): List of drivers to apply fade to based on distance from source_guide.
        skip_lower (float): The distance below which multiplyDivide fading stops.
        
    Returns:
        list : The list of multiplyDivide nodes.
    
    """
    distance_list, distance_dict, original_distance_order = get_ordered_distance_and_transform(source_guide, drivers)
    
    multiplies = []
    
    if not distance_list[-1] > 0:
        return multiplies
    
    for distance in original_distance_order:
                
        scaler = 1.0 - (distance/ distance_list[-1]) 
        
        if scaler <= skip_lower:
            continue
        
        multi = attr.MultiplyDivideNode(source_guide)
        
        multi.set_input2(scaler,scaler,scaler)
        
        multi.input1X_in( '%s.translateX' % source_guide )
        multi.input1Y_in( '%s.translateY' % source_guide )
        multi.input1Z_in( '%s.translateZ' % source_guide )
        
        for driver in distance_dict[distance]:
            multi.outputX_out('%s.translateX' % driver)
            multi.outputY_out('%s.translateY' % driver)
            multi.outputZ_out('%s.translateZ' % driver)
            
        multi_dict = {}
        multi_dict['node'] = multi
        multi_dict['source'] = source_guide
        #CBB strange that it passed the last driver...
        multi_dict['target'] = driver
        
        multiplies.append(multi_dict)
        
    return multiplies

#--- space groups

def create_match_group(transform, prefix = 'match', use_duplicate = False):
    """
    Create a group that matches a transform.
    Naming = 'match_' + transform
    
    Args:
        transform (str): The transform to match.
        prefix (str): The prefix to add to the matching group.
        use_duplicate (bool):  If True, matching happens by duplication instead of changing transform values.
        
    Returns:
        str:  The name of the new group.
    """
    parent = cmds.listRelatives(transform, p = True, f = True)
    
    basename = core.get_basename(transform)
    
    name = '%s_%s' % (prefix, basename)
    
    if not use_duplicate:    
        xform_group = cmds.group(em = True, n = core.inc_name( name ))
        match_space = MatchSpace(transform, xform_group)
        match_space.translation_rotation()
        
        if parent:
            cmds.parent(xform_group, parent[0])    
        
    if use_duplicate:
        xform_group = cmds.duplicate(transform, po = True)
        
        attr.remove_user_defined(xform_group)
        
        xform_group = cmds.rename(xform_group, core.inc_name(name))
    
    return xform_group    

def create_xform_group(transform, prefix = 'xform', use_duplicate = False, copy_scale = False):
    """
    Create a group above a transform that matches transformation of the transform. 
    This is good for zeroing out the values of a transform.
    Naming = 'xform_' + transform
    
    Args:
        transform (str): The transform to match.
        prefix (str): The prefix to add to the matching group.
        use_duplicate (bool):  If True, matching happens by duplication instead of changing transform values.
        
    Returns:
        str:  The name of the new group.
    """
    
    parent = cmds.listRelatives(transform, p = True, f = True)
    
    basename = core.get_basename(transform)
    
    if not prefix:
        prefix = 'xform'
    
    name = '%s_%s' % (prefix, basename)
    
    if copy_scale:
        orig_scale = cmds.getAttr('%s.scale' % transform)[0]
        try:
            cmds.setAttr('%s.scaleX' % transform, 1)
            cmds.setAttr('%s.scaleY' % transform, 1)
            cmds.setAttr('%s.scaleZ' % transform, 1)
        except:
            pass
            
    if not use_duplicate:    
        xform_group = cmds.group(em = True, n = core.inc_name( name ))
        match_space = MatchSpace(transform, xform_group)
        match_space.translation_rotation()
        
        if copy_scale: 
            match_space.scale()
        
        
        if parent:
            cmds.parent(xform_group, parent[0])    


        
    
    if use_duplicate:
        #this sometimes doesn't duplicate with values because Maya... :(
        xform_group = cmds.duplicate(transform, po = True)[0]
        
        attr.remove_user_defined(xform_group)
        
        xform_group = cmds.rename(xform_group, core.inc_name(name))

    cmds.parent(transform, xform_group)
    
    if copy_scale:
        
        cmds.setAttr('%s.scaleX' % xform_group, orig_scale[0])
        cmds.setAttr('%s.scaleY' % xform_group, orig_scale[1])
        cmds.setAttr('%s.scaleZ' % xform_group, orig_scale[2])
        
    
    attr.connect_group_with_message(xform_group, transform, prefix)

    return xform_group

def create_follow_group(source_transform, target_transform, prefix = 'follow', follow_scale = False, use_duplicate = False):
    """
    Create a group above a target_transform that is constrained to the source_transform.
    
    Args:
        source_transform (str): The transform to follow.
        target_transform (str): The transform to make follow.
        prefix (str): The prefix to add to the follow group.
        follow_scale (bool): Wether to add a scale constraint or not.
    
    Returns:
        str:  The name of the new group.
    """
    
    parent = cmds.listRelatives(target_transform, p = True, f = True)
    
    target_name = util.convert_to_sequence(target_transform) 
    
    name = '%s_%s' % (prefix, target_name[0])
    
    if not use_duplicate:
        follow_group = cmds.group( em = True, n = core.inc_name(name) )
    if use_duplicate:
        follow_group = cmds.duplicate( target_transform, n = core.inc_name(name), po = True)[0]
        
        attr.remove_user_defined(follow_group)
        
        parent = None
    
    match = MatchSpace(source_transform, follow_group)
    match.translation_rotation()
    
    
    
    if parent:
        cmds.parent(follow_group, parent)
    
    #zero_out_transform_channels(follow_group)
        
    if follow_scale:
        attr.connect_scale(source_transform, follow_group)
    
    cmds.parentConstraint(source_transform, follow_group, mo = True)
    
    cmds.parent(target_transform, follow_group)    
    
    
    return follow_group

def create_local_follow_group(source_transform, target_transform, prefix = 'followLocal', orient_only = False, connect_scale = False):
    """
    Create a group above a target_transform that is local constrained to the source_transform.
    This helps when setting up controls that need to be parented but only affect what they constrain when the actual control is moved.  
    
    Args:
        source_transform (str): The transform to follow.
        target_transform (str): The transform to make follow.
        prefix (str): The prefix to add to the follow group.
        orient_only (bool): Wether the local constraint should just be an orient constraint.
    
    Returns:
        str:  The name of the new group.
    """
    
    parent = cmds.listRelatives(target_transform, p = True)
    
    name = '%s_%s' % (prefix, target_transform)
    
    follow_group = cmds.group( em = True, n = core.inc_name(name) )
    
    #MatchSpace(target_transform, follow_group).translation()
    MatchSpace(source_transform, follow_group).translation_rotation()
    
    xform = create_xform_group(follow_group)
    
    #cmds.parentConstraint(source_transform, follow_group, mo = True)
    
    if not orient_only:
        attr.connect_translate(source_transform, follow_group)
    
    if orient_only or not orient_only:
        attr.connect_rotate(source_transform, follow_group)
    
    if connect_scale:
        attr.connect_scale(source_transform, follow_group)
    
    #value = cmds.getAttr('%s.rotateOrder' % source_transform)
    #cmds.setAttr('%s.rotateOrder' % follow_group, value)
    
    cmds.parent(target_transform, follow_group)
    
    if parent:
        cmds.parent(xform, parent)
        
    return follow_group    

def create_multi_follow_direct(source_list, target_transform, node, constraint_type = 'parentConstraint', attribute_name = 'follow', value = None):
    """
    Create a group above the target that is constrained to multiple transforms. A switch attribute switches their state on/off.
    Direct in this case means the constraints will be added directly on the target_transform.
    
    Args:
        source_list (list): List of transforms that the target should be constrained by.
        target_transform (str): The name of a transform that should follow the transforms in source list.
        node (str): The name of the node to add the switch attribute to.
        constraint_type (str): Corresponds to maya's constraint types. Currently supported: parentConstraint, pointConstraint, orientConstraint.
        attribute_name (str): The name of the switch attribute to add to the node.
        value (float): The value to give the switch attribute on the node.
    
    Returns:
        str:  The name of the new group.
    """
    
    if attribute_name == 'follow':
        var = attr.MayaEnumVariable('FOLLOW')
        var.create(node)
            
    locators = []

    for source in source_list:
        
        locator = cmds.spaceLocator(n = core.inc_name('follower_1_%s' % source, False))[0]
        
        cmds.hide(locator)
        
        match = MatchSpace(target_transform, locator)
        match.translation_rotation()
        
        cmds.parent(locator, source)
        
        locators.append(locator)
    
    if constraint_type == 'parentConstraint':
        constraint = cmds.parentConstraint(locators,  target_transform, mo = True)[0]
        cmds.setAttr('%s.interpType' % constraint, 2)
        
    if constraint_type == 'pointConstraint':
        constraint = cmds.pointConstraint(locators,  target_transform, mo = True)[0]
        
    if constraint_type == 'orientConstraint':
        constraint = cmds.orientConstraint(locators,  target_transform, mo = True)[0]
        cmds.setAttr('%s.interpType' % constraint, 2)
    
    constraint_editor = ConstraintEditor()
    
    constraint_editor.create_switch(node, attribute_name, constraint)

    if value == None:
        value = (len(source_list)-1)
    
    cmds.setAttr('%s.%s' % (node, attribute_name), value)
       

def create_multi_follow(source_list, target_transform, node = None, constraint_type = 'parentConstraint', attribute_name = 'follow', value = None, create_title = True):
    """
    Create a group above the target that is constrained to multiple transforms. A switch attribute switches their state on/off.
    Direct in this case means the constraints will be added directly on the target_transform.
    
    Args:
        source_list (list): List of transforms that the target should be constrained by.
        target_transform (str): The name of a transform that should follow the transforms in source list.
        node (str): The name of the node to add the switch attribute to.
        constraint_type (str): Corresponds to maya's constraint types. Currently supported: parentConstraint, pointConstraint, orientConstraint.
        attribute_name (str): The name of the switch attribute to add to the node.
        value (float): The value to give the switch attribute on the node.
    
    Returns:
        str:  The name of the new group.
    """
    
    if node == None:
        node = target_transform
    
    locators = []
    
    if len(source_list) < 2:
        util.warning('Cannot create multi follow with less than 2 source transforms.')
        return
    
    follow_group = create_xform_group(target_transform, 'follow')
    
    title_name = attribute_name.upper()
    

    for source in source_list:
        
        locator = cmds.spaceLocator(n = core.inc_name('follower_1_%s' % source, False))[0]
        
        cmds.hide(locator)
        
        match = MatchSpace(target_transform, locator)
        match.translation_rotation()
        
        cmds.parent(locator, source)
        
        locators.append(locator)
    
    if constraint_type == 'parentConstraint':
        constraint = cmds.parentConstraint(locators,  follow_group, mo = True)[0]
        cmds.setAttr('%s.interpType' % constraint, 2)
    if constraint_type == 'orientConstraint':
        constraint = cmds.orientConstraint(locators,  follow_group)[0]
        cmds.setAttr('%s.interpType' % constraint, 2)
    if constraint_type == 'pointConstraint':
        constraint = cmds.pointConstraint(locators,  follow_group, mo = True)[0]
    
    constraint_editor = ConstraintEditor()
    
    if create_title:
        constraint_editor.create_title(node, constraint, title_name)
    constraint_editor.create_switch(node, attribute_name, constraint)
    
    if value == None:
        value = (len(source_list)-1)
        
    cmds.setAttr('%s.%s' % (node, attribute_name), value)
    
    return follow_group

def create_ghost_follow_chain(transforms):
    
    last_ghost = None
    
    ghosts = []
    
    parent = cmds.listRelatives(transforms[0], parent = True)
    if parent:
        parent = cmds.duplicate(parent[0], po = True, n = 'ghost_%s' % parent[0])[0]
        cmds.parent(parent, w = True)
        
        attr.remove_user_defined(parent)
        
        last_ghost = parent
    
    for transform in transforms:
        
        ghost = cmds.duplicate(transform, po = True, n = 'ghost_%s' % transform)[0]
        
        attr.remove_user_defined(ghost)
        
        cmds.parent(ghost, w = True)
        
        MatchSpace(transform, ghost).translation_rotation()
        
        attr.connect_translate(transform, ghost)
        attr.connect_rotate(transform, ghost)
        attr.connect_scale(transform, ghost)
        
        if last_ghost:
            cmds.parent(ghost, last_ghost )
        
        last_ghost = ghost
        
        ghosts.append(ghost)

    return ghosts, parent


def create_ghost_chain(transforms, xform_group_prefix = 'ghostDriver'):
    """
    A ghost chain has the same hierarchy has the supplied transforms.
    It connects into the an xform group above the transform.  
    This allows for setups that follow a nurbs surface, and then work like an fk hierarchy after.
    
    Args:
        transforms (list): A list of transforms.
        
    Returns:
        list: A list of ghost transforms corresponding to transforms.
    """
    last_ghost = None
    
    ghosts = []
    
    for transform in transforms:
        ghost = cmds.duplicate(transform, po = True, n = 'ghost_%s' % transform)[0]
        
        attr.remove_user_defined(ghost)
        
        cmds.parent(ghost, w = True)
        
        MatchSpace(transform, ghost).translation_rotation()
        
        xform = create_xform_group(ghost, xform_group_prefix)
        
        target_offset = create_xform_group(transform)
        
        attr.connect_translate(ghost, target_offset)
        attr.connect_rotate(ghost, target_offset)
        
        if last_ghost:
            cmds.parent(xform, last_ghost )
        
        last_ghost = ghost
        
        ghosts.append(ghost)

    return ghosts

def create_pivot_group(source_transform, target_transform, prefix = 'pivot', match_pivot_position_only = True):
    """
    Create a group with pivot at source_tranform above target_transform
    """
    
    group = cmds.group(em = True, n = prefix + '_' + target_transform)
    
    if not match_pivot_position_only:
        MatchSpace(source_transform, group).translation_rotation()
    if match_pivot_position_only:
        MatchSpace(target_transform, group).translation_rotation()
        MatchSpace(source_transform, group).rotate_scale_pivot_to_translation()
    
    parent = cmds.listRelatives(target_transform, p = True)
    if parent:
        parent = parent[0]
    
    cmds.parent(group, parent)
    cmds.parent(target_transform, group)
    
    return group

def create_no_twist_aim(source_transform, target_transform, parent, move_vector = [0,0,1]):
    """
    Aim target transform at the source transform, trying to rotate only on one axis.
    Constrains the target_transform.
    
    Args:
        source_transform (str): The name of a transform.
        target_transform (str): The name of a transform.
        parent (str): The parent for the setup.
    """
    
    
    top_group = cmds.group(em = True, n = core.inc_name('no_twist_%s' % source_transform))
    cmds.parent(top_group, parent)
    cmds.pointConstraint(source_transform, top_group)

    #axis aim
    aim = cmds.group(em = True, n = core.inc_name('aim_%s' % target_transform))
    target = cmds.group(em = True, n = core.inc_name('target_%s' % target_transform))
        
    MatchSpace(source_transform, aim).translation_rotation()
    MatchSpace(source_transform, target).translation_rotation()
    
    xform_target = create_xform_group(target)
    #cmds.setAttr('%s.translateX' % target, 1)
    cmds.move(1,0,0, target, r = True, os = True)
    
    cmds.parentConstraint(source_transform, target, mo = True)
    
    cmds.aimConstraint(target, aim, wuo = parent, wut = 'objectrotation', wu = [0,0,0])
    
    cmds.parent(aim, xform_target, top_group)
    
    #pin up to axis
    pin_aim = cmds.group(em = True, n = core.inc_name('aim_pin_%s' % target_transform))
    pin_target = cmds.group(em = True, n = core.inc_name('target_pin_%s' % target_transform))
    
    MatchSpace(source_transform, pin_aim).translation_rotation()
    MatchSpace(source_transform, pin_target).translation_rotation()
    
    xform_pin_target = create_xform_group(pin_target)
    cmds.move(move_vector[0], move_vector[1], move_vector[2], pin_target, r = True)
    
    cmds.aimConstraint(pin_target, pin_aim, wuo = aim, wut = 'objectrotation')
    
    cmds.parent(xform_pin_target, pin_aim, top_group)
       
    #twist_aim
    #tool_maya.create_follow_group('CNT_SPINE_2_C', 'xform_CNT_TWEAK_ARM_1_%s' % side)
    cmds.pointConstraint(source_transform, target_transform, mo = True)
    
    cmds.parent(pin_aim, aim)
    
    cmds.orientConstraint(pin_aim, target_transform, mo = True)

def create_pole_chain(top_transform, btm_transform, name, solver = IkHandle.solver_sc):
    """
    Create a two joint chain with an ik handle.
    
    Args:
        top_transform (str): The name of a transform.
        btm_transform (str): The name of a transform.
        name (str): The name to give the new joints.
        
    Returns:
        tuple: (joint1, joint2, ik_pole)
    """
    
    cmds.select(cl =True)
    
    joint1 = cmds.joint(n = core.inc_name( name ) )
    joint2 = cmds.joint(n = core.inc_name( name ) )

    MatchSpace(top_transform, joint1).translation()
    MatchSpace(btm_transform, joint2).translation()
    
    cmds.joint(joint1, e = True, oj = 'xyz', secondaryAxisOrient = 'xup', zso = True)
    cmds.makeIdentity(joint2, jo = True, apply = True)

    ik_handle = IkHandle( name )
    
    ik_handle.set_start_joint( joint1 )
    ik_handle.set_end_joint( joint2 )
    ik_handle.set_solver(solver)
    ik_pole = ik_handle.create()
    
    if solver == IkHandle.solver_rp:
        cmds.setAttr('%s.poleVectorX' % ik_pole, 0)
        cmds.setAttr('%s.poleVectorY' % ik_pole, 0)
        cmds.setAttr('%s.poleVectorZ' % ik_pole, 0)

    return joint1, joint2, ik_pole

def create_ik_on_joint(joint, name, solver = IkHandle.solver_sc):
    
    rels = cmds.listRelatives(joint, type = 'joint')
    
    if not rels:
        return
    
    joint2 = rels[0]
    

    ik_handle = IkHandle( name )
    
    ik_handle.set_start_joint( joint )
    ik_handle.set_end_joint( joint2 )
    ik_handle.set_solver(solver)
    ik_pole = ik_handle.create()
    
    if solver == IkHandle.solver_rp:
        cmds.setAttr('%s.poleVectorX' % ik_pole, 0)
        cmds.setAttr('%s.poleVectorY' % ik_pole, 0)
        cmds.setAttr('%s.poleVectorZ' % ik_pole, 0)
        
    return ik_pole
    

def get_xform_group(transform, xform_group_prefix = 'xform'):
    """
    This returns an xform group above the control.
    
    Args:
        name (str): The prefix name supplied when creating the xform group.  Usually xform or driver.
        
    """
    
    attribute_name = 'group_%s' % xform_group_prefix
    
    node_and_attr = '%s.%s' % (transform,attribute_name)
    
    if not cmds.objExists(node_and_attr):
        return
        
    input_node = attr.get_attribute_input(node_and_attr, node_only=True)
        
    return input_node

def get_local_group(transform):
    attribute_name = 'out_local'
    
    node_and_attr = '%s.%s' % (transform,attribute_name)
    
    if not cmds.objExists(node_and_attr):
        return
        
    input_node = attr.get_attribute_input(node_and_attr, node_only=True)
        
    return input_node

def get_hierarchy(node_name):
    """
    Return the name of the node including the hierarchy in the name using "|".
    This is the full path of the node.
    
    Args:
        node_name (str): A node name.
        
    Returns:
        str: The node name with hierarchy included. The full path to the node.
    """
    
    parent_path = cmds.listRelatives(node_name, f = True)[0]
    
    if parent_path:
        split_path = cmds.split(parent_path, '|')
    
    if split_path:
        return split_path
        
def has_parent(transform, parent):
    """
    Check to see if the transform has parent in its parent hierarchy.
    
    Args:
        transform (str): The name of a transform.
        parent (str): The name of a parent transform.
        
    Returns:
        bool
    """
    
    long_transform = cmds.ls(transform, l = True)
    
    if not long_transform:
        return
    
    long_transform = long_transform[0]
    
    split_long = long_transform.split('|')
    
    core.get_basename(parent)
    
    if parent in split_long:
        return True
    
    return False
        
        
def transfer_relatives(source_node, target_node, reparent = False):
    """
    Reparent the children of source_node under target_node.
    If reparent, move the target_node under the parent of the source_node.
    
    Args:
        source_node (str): The name of a transform to take relatives from.
        target_node (str): The name of a transform to transfer relatives to.
        reparent (bool): Wether to reparent target_node under source_node after transfering relatives.
    """
    
    parent = None
    
    if reparent:
        parent = cmds.listRelatives(source_node, p = True)
        if parent:
            parent = parent[0]
        
    children = cmds.listRelatives(source_node, c = True, type = 'transform')

    if children:
        cmds.parent(children, target_node)
    
    
    if parent:
        cmds.parent(target_node, parent)


    

def constrain_local(source_transform, target_transform, parent = False, scale_connect = False, constraint = 'parentConstraint', use_duplicate = False):
    """
    Constrain a target transform to a source transform in a way that allows for setups to remain local to the origin.
    This is good when a control needs to move with the rig, but move something at the origin only when the actually control moves.
    
    Args:
        source_transform (str): The name of a transform.
        target_transform (str): The name of a transform.
        parent (bool): The setup uses a local group to constrain the target_transform. If this is true it will parent the target_transform under the local group.
        scale_connect (bool): Wether to also add a scale constraint.
        constraint (str): The type of constraint to use. Currently supported: parentConstraint, pointConstraint, orientConstraint.
        
    Returns:
        (str, str) : The local group that constrains the target_transform, and the xform group above the local group.
    """
    local_group = None
    
    if use_duplicate:
        local_group = cmds.duplicate(source_transform, n = 'local_%s' % source_transform)[0]
        
        attr.remove_user_defined(local_group)
        
        children = cmds.listRelatives(local_group)
        
        if children:
            cmds.delete(children)
        
        dup_parent = cmds.listRelatives(local_group, p = True)
        
        if dup_parent:
            cmds.parent(local_group, w = True)
        
        
        xform_group = create_xform_group(local_group, use_duplicate = True)
        
                
    
    if not use_duplicate:
        local_group = cmds.group(em = True, n = core.inc_name('local_%s' % source_transform))
        
        MatchSpace(target_transform, local_group).translation_rotation()
        MatchSpace(target_transform, local_group).scale()
        
        if core.has_shape_of_type(source_transform, 'follicle'):
            xform_group = cmds.group(em = True, n = 'xform_%s' % local_group)
            cmds.parent(local_group, xform_group)
        else:
            xform_group = create_xform_group(local_group, copy_scale=True)
        
        parent_world = cmds.listRelatives(source_transform, p = True)
        
        
        #In the past the xform used to get a scale copy of target transform ended with R. 
        #This was stupid
        #Its now changed so that all xforms copy the scale and 
        #if target_transform.endswith('R'):
        #    match = MatchSpace(target_transform, xform_local_group).scale()
        
        if parent_world:
            if not core.has_shape_of_type(source_transform, 'follicle'):
                parent_world = parent_world[0]
                
                match = MatchSpace(parent_world, xform_group)
                match.translation_rotation()
    
    if not local_group:
        return
    

    attr.connect_translate(source_transform, local_group)
    attr.connect_rotate(source_transform, local_group)
    
    if scale_connect:
        attr.connect_scale(source_transform, local_group)
            
    if parent:
        cmds.parent(target_transform, local_group)
    
    
        
    if not parent:
        maintain_offset = True
        equivalent = world_matrix_equivalent(local_group, target_transform)
        if equivalent:
            maintain_offset = False
        if constraint == 'parentConstraint':
            cmds.parentConstraint(local_group, target_transform, mo = maintain_offset)
        if constraint == 'pointConstraint':
            cmds.pointConstraint(local_group, target_transform, mo = maintain_offset)
        if constraint == 'orientConstraint':
            cmds.orientConstraint(local_group, target_transform, mo = maintain_offset)
            
        if scale_connect:
            attr.connect_scale(source_transform, target_transform)
    
    attr.connect_message(local_group, source_transform, 'out_local')
    
    return local_group, xform_group

@core.undo_chunk
def subdivide_joint(joint1 = None, joint2 = None, count = 1, prefix = 'joint', name = 'sub_1', duplicate = False):
    """
    Add evenly spaced joints inbetween joint1 and joint2.
    
    Args:
        joint1 (str): The first joint. If None given, the first selected joint.
        joint2 (str): The second joint. If None given, the second selected joint.
        count (int): The number of joints to add inbetween joint1 and joint2.
        prefix (str): The prefix to add in front of the new joints.
        name (str): The name to give the new joints after the prefix. Name = prefix + '_' + name
        duplicate (bool): Wether to create a duplicate chain.
        
    Returns:
        list: List of the newly created joints.
        
    """
    if not joint1 and not joint2:
        selection = cmds.ls(sl = True)
        
        if cmds.nodeType(selection[0]) == 'joint':
            joint1 = selection[0]
        
        if len(selection) > 1:
            if cmds.nodeType(selection[1]) == 'joint':
                joint2 = selection[1]
            
    if joint1 and not joint2:
        joint_rels = cmds.listRelatives(joint1, type = 'joint')
        
        if joint_rels:
            joint2 = joint_rels[0]
        
        
    if not joint1 or not joint2:
        return
    
    vector1 = cmds.xform(joint1, query = True, worldSpace = True, translation = True)
    vector2 = cmds.xform(joint2, query = True, worldSpace = True, translation = True)
    
    name = '%s_%s' % (prefix, name)
    
    joints = []
    top_joint = joint1
    
    radius = cmds.getAttr('%s.radius' % joint1)
    
    if duplicate:
        cmds.select(cl = True)
        top_joint = cmds.joint(p = vector1, n = core.inc_name(name), r = radius + 1)
        joints.append(top_joint)
        
        match = MatchSpace(joint1, top_joint)
        match.rotation()
        cmds.makeIdentity(top_joint, apply = True, r = True)
    
    offset = 1.00/(count+1)
    value = offset
    
    last_joint = None
        
    for inc in range(0, count):
        
        position = util_math.get_inbetween_vector(vector1, vector2, value)
        
        cmds.select(cl = True)
        joint = cmds.joint( p = position, n = core.inc_name(name), r = radius)
        cmds.setAttr('%s.radius' % joint, radius)
        joints.append(joint)

        value += offset
        
            
        if inc == 0:
            cmds.parent(joint, top_joint)
            cmds.makeIdentity(joint, apply = True, jointOrient = True)
            
        if last_joint:
            cmds.parent(joint, last_joint)
            cmds.makeIdentity(joint, apply = True, jointOrient = True)
            
            if not cmds.isConnected('%s.scale' % last_joint, '%s.inverseScale'  % joint):
                cmds.connectAttr('%s.scale' % last_joint, '%s.inverseScale'  % joint)
            
                
        last_joint = joint            
        
            
    btm_joint = joint2
    
    if duplicate:
        cmds.select(cl = True)
        btm_joint = cmds.joint(p = vector2, n = core.inc_name(name), r = radius + 1)
        joints.append(btm_joint)

        match = MatchSpace(joint1, btm_joint)
        match.rotation()
        cmds.makeIdentity(btm_joint, apply = True, r = True)
    
    cmds.parent(btm_joint, joint)
    
    if not cmds.isConnected('%s.scale' % joint, '%s.inverseScale'  % btm_joint):
            cmds.connectAttr('%s.scale' % joint, '%s.inverseScale'  % btm_joint)
            
    return joints

    
def orient_attributes(scope = None, initialize_progress = True, hierarchy = True):
    """
    Orient all transforms with attributes added by add_orient_attributes.
    If scope is provided, only orient transforms in the scope that have attributes.
    
    Args:
        scope (list): List of transforms to orient.
    """
    
    if not scope:
        scope = core.get_top_dag_nodes()
    
    count = None
    title = ''
    
    if initialize_progress:
        
        watch = util.StopWatch()
        watch.start('Orienting Joints')
        
        count = len(cmds.ls(type = 'joint'))
        title = 'Orient Joints'    
    
    progress_bar = core.ProgressBar(title, count = count, begin = initialize_progress)
    
    oriented = False
    
    for transform in scope:
        
        if cmds.objExists('%s.active' % transform):
            if not cmds.getAttr('%s.active' % transform):
                util.warning('%s has orientation attributes but is not active.  Skipping.' % transform)
                continue
        
        progress_bar.status('Orienting: %s of %s   %s' % (progress_bar.get_current_inc(), progress_bar.get_count(), core.get_basename(transform)))
        progress_bar.next()
        
        relatives = []
        if hierarchy:
            relatives = cmds.listRelatives(transform, f = True, type = 'transform')
        
        if cmds.objExists('%s.ORIENT_INFO' % transform):
            
            if progress_bar.break_signaled():
                watch.end()
                return
            orient = OrientJoint(transform, relatives)
            orient.run()
        
        oriented = True
        
        if relatives:
            orient_attributes(relatives, initialize_progress = False)
        
    if initialize_progress:
        progress_bar.end()
        watch.end()
                
    return oriented

def orient_attributes_all():
    """
    Orient all transforms with attributes added by add_orient_attributes.
    If scope is provided, only orient transforms in the scope that have attributes.
    
    Args:
        scope (list): List of transforms to orient.
    """
    
    scope = cmds.ls(type = 'transform', l = True)
        
    watch = util.StopWatch()
    watch.start('Orienting Joints')
    
    count = len(scope)
    title = 'Orient Joints'    
    
    progress_bar = core.ProgressBar(title, count = count, begin = True)
    
    oriented = False
    
    #sorts the keys by |
    scope.sort(key=lambda x: (-x.count('|'), x))
    scope.reverse()
    
    for transform in scope:
        
        if cmds.objExists('%s.active' % transform):
            if not cmds.getAttr('%s.active' % transform):
                util.warning('%s has orientation attributes but is not active.  Skipping.' % transform)
                continue
        
        progress_bar.status('Orienting: %s of %s   %s' % (progress_bar.get_current_inc(), progress_bar.get_count(), core.get_basename(transform)))
        progress_bar.next()
        
        if cmds.objExists('%s.ORIENT_INFO' % transform):
            
            if progress_bar.break_signaled():
                watch.end()
                return
            orient = OrientJoint(transform)
            orient.run()
        
        oriented = True
        
    
    progress_bar.end()
    watch.end()
                
    return oriented

def auto_generate_orient_attributes(joint, align_forward = 'Z', align_up = 'Y'):
    
    if align_forward == align_up:
        core.print_warning('Align forward axis cannot be the same as align up axis.')
        return
    hier = core.get_hierarchy(joint)
    
    hier.insert(0, joint)
    
    hier_children = {}
    attr_inst = {}
    
    forward_align, up_align = get_orient_attribute_default_alignment(align_forward, align_up)
    if align_forward == 'X':
        forward_orig_align = 0
    if align_forward == 'Y':
        forward_orig_align = 1
    if align_forward == 'Z':
        forward_orig_align = 2        

    for joint in hier:
        long_joint_name = cmds.ls(joint, l = True)[0]

        orient_attr = attr.OrientJointAttributes(joint)
        
        parent = cmds.listRelatives(joint, parent = True, type = 'joint', f = True)
        if parent:
            parent = parent[0]
        children = cmds.listRelatives(joint, type = 'joint', f = True)
        
        attr_inst[long_joint_name] = orient_attr
        
        has_world_up = 1
        last_children = None
        if parent in hier_children:
            last_children = hier_children[parent]
        
        if parent:
            lives_in_parent = 1
            has_world_up = 6
            
            
            if last_children and len(last_children) > 1:
                has_world_up = 1
                lives_in_parent = 0

        else:
            lives_in_parent = 0
        
        if joint == hier[0]:
            lives_in_parent = 0
        
        if not lives_in_parent:
            forward_align, up_align = get_orient_attribute_default_alignment(align_forward, align_up)
            has_world_up = 1        
        
        hier_children[long_joint_name] = children
        
        world = True
        local_parent = False
        
        if children and len(children) == 1:
            world = False
        
        if children and len(children) > 1:
            world = False
            local_parent = True
        
        if not parent:
            world = True
        
        if parent and not children:
            world = False
            local_parent = True
        
        if world:

            orient_attr.attributes[0].set_value(forward_align)
            orient_attr.attributes[1].set_value(up_align)
            orient_attr.attributes[2].set_value(has_world_up)
            orient_attr.attributes[3].set_value(0)
            orient_attr.attributes[4].set_value(lives_in_parent)
            orient_attr.attributes[5].set_value(2)
            orient_attr.attributes[6].set_value(3)
            orient_attr.attributes[7].set_value(4)
            orient_attr.attributes[8].set_value(0)
            orient_attr.attributes[9].set_value(1)
         
        if not world:

            forward_alt_align = get_alt_forward_alignment(align_forward, align_up)

            new_up_align = up_align
            
            if children and lives_in_parent != 1:
                
                #handle up
                vector_joint = cmds.xform(joint, ws = True, q = True, t = True)
                vector_child = cmds.xform(children[0], ws = True, q = True, t = True)
                
                vector_aim = util_math.vector_sub(vector_child,vector_joint)
                vector_aim = util_math.vector_normalize(vector_aim)
                
                up_angle = util_math.angle_between(vector_aim,[0,1,0],in_degrees = True)
                
                switch_up = False
                forward_angle = util_math.angle_between(vector_aim,[0,0,1],in_degrees = True)
                if forward_angle < 60:
                    forward_align = get_alt_forward_alignment(align_forward, align_up)
                    
                    test_align_forward = forward_align
                    if forward_align > 2:
                        test_align_forward -= 3
                    flip = False
                    
                    if up_align == 0 and test_align_forward == 2:
                        flip = True 
                    
                    if up_align == 1 and test_align_forward == 0:
                        flip = True 
                    
                    if up_align == 2 and test_align_forward == 1:
                        flip = True 
                    
                    if flip:
                        if forward_align > 2:
                            forward_align -= 3
                        elif forward_align < 3:
                            forward_align += 3
                
                if forward_angle > 120:
                    forward_align = forward_alt_align
                    
                    test_align_forward = forward_align
                    if forward_align > 2:
                        test_align_forward -= 3
                    flip = False
                    
                    if up_align == 0 and test_align_forward == 1:
                        flip = True 
                    
                    if up_align == 1 and test_align_forward == 2:
                        flip = True 
                    
                    if up_align == 2 and test_align_forward == 0:
                        flip = True
                    
                    if flip:
                        if forward_align > 2:
                            forward_align -= 3
                        elif forward_align < 3:
                            forward_align += 3

                if up_angle <= 50:
                    if forward_align < 3:
                        forward_align += 3
                    elif forward_align > 2:
                        forward_align -= 3
                    temp = up_align
                    up_align = forward_align
                    forward_align = temp
                    
                    switch_up = True
                
                if up_angle >= 130:
                    temp = up_align
                    up_align = forward_align
                    forward_align = temp
                    if temp < 3:
                        forward_align = temp + 3
                    if temp >= 3:
                        forward_align = temp - 3
                    switch_up = True
                
                new_up_align = up_align
                
                if switch_up:
                    has_world_up = 2
                    new_up_align = forward_orig_align
                
            orient_attr.attributes[0].set_value(forward_align)
            orient_attr.attributes[1].set_value(new_up_align)
            orient_attr.attributes[2].set_value(has_world_up)
            orient_attr.attributes[3].set_value(3)
            orient_attr.attributes[4].set_value(lives_in_parent)
            orient_attr.attributes[5].set_value(2)
            orient_attr.attributes[6].set_value(3)
            orient_attr.attributes[7].set_value(4)
            orient_attr.attributes[8].set_value(0)
            orient_attr.attributes[9].set_value(1)
            
            if lives_in_parent:
                orient_attr.attributes[1].set_value(1)
            
            if local_parent:
                
                orient_attr.attributes[0].set_value(0)
                orient_attr.attributes[3].set_value(5)

def get_orient_attribute_default_alignment(forward_axis = 'Z', up_axis = 'Y'):
    
    align = forward_axis + up_axis
    
    foward_align = 0
    up_align = 1
    
    if align == 'XY':
        forward_align = 5
        up_align = 1
    if align == 'XZ':
        forward_align = 1
        up_align = 2
    if align == 'YZ':
        forward_align = 3
        up_align = 2
    if align == 'YX':
        forward_align = 2
        up_align = 0
    if align == 'ZX':
        forward_align = 4
        up_align = 0
    if align == 'ZY':
        forward_align = 0
        up_align = 1
        
    return forward_align, up_align  

def get_alt_forward_alignment(forward_axis = 'Z', up_axis = 'Y'):
    align = forward_axis + up_axis
    
    if align == 'XY':
        return 3
    if align == 'XZ':
        return 0
    if align == 'YZ':
        return 4
    if align == 'YX':
        return 1
    if align == 'ZX':
        return 5
    if align == 'ZY':
        return 2
    
def mirror_orient_attributes():
    pass
    
def add_orient_joint(joint):
    """
    Add orient joint. This will create an up and an aim joint.
    
    Args:
        joint (str): The name of the joint to add the up and the aim to.
    """
    if not cmds.nodeType(joint) == 'joint':
        return
    
    aim_name = 'locator_aim_%s' % joint
    up_name = 'locator_up_%s' % joint
    
    attr.add_orient_attributes(joint)
    
    current_radius = cmds.getAttr('%s.radius' % joint)
    
    cmds.select(cl = True)
    aim_joint = cmds.spaceLocator(n = core.inc_name(aim_name))[0]
    cmds.select(cl = True)
    up_joint = cmds.spaceLocator(n = core.inc_name(up_name))[0]
    
    MatchSpace(joint, aim_joint).translation()
    MatchSpace(joint, up_joint).translation()
    
    cmds.parent(aim_joint, up_joint, joint)
    
    cmds.reorder(up_joint, front = True)
    cmds.reorder(aim_joint, front = True)
    
    cmds.makeIdentity(aim_joint, apply = True, r = True, jo = True)
    cmds.makeIdentity(up_joint, apply = True, r = True, jo = True)
    
    attr.set_color(aim_joint, 18)
    attr.set_color(up_joint, 14)
    
    cmds.move(0.1, 0,0, aim_joint, r = True, os = True)
    cmds.move(0, 0.1,0, up_joint, r = True, os = True)
    
    scale_value = current_radius/2.0
    
    cmds.setAttr('%s.localScaleX' % aim_joint, scale_value)
    cmds.setAttr('%s.localScaleY' % aim_joint, scale_value)
    cmds.setAttr('%s.localScaleZ' % aim_joint, scale_value)
    
    cmds.setAttr('%s.localScaleX' % up_joint, scale_value)
    cmds.setAttr('%s.localScaleY' % up_joint, scale_value)
    cmds.setAttr('%s.localScaleZ' % up_joint, scale_value)
    
    cmds.setAttr('%s.aimUpAt' % joint, 5)
    

def orient_x_to_child_up_to_surface(joint, invert = False, surface = None, neg_aim = False):
    
    aim_value = 1
    if neg_aim:
        aim_value = -1
        
    aim_axis = [aim_value,0,0]
    up_axis = [0,1,0]
    
    if invert:
        aim_axis = [aim_value*-1,0,0]
        up_axis = [0,-1,0]
    
    children = cmds.listRelatives(joint, type = 'transform')
    
    if children:
        
        orient = OrientJoint(joint, children)
        orient.set_surface(surface)
        orient.set_aim_at(3)
        orient.set_aim_up_at(6)
        orient.set_aim_vector(aim_axis)
        orient.set_up_vector(up_axis)
        orient.run()

    if not children:
        cmds.makeIdentity(joint, jo = True, apply = True)
        
def orient_x_to_child(joint, invert = False, neg_aim = False, parent_rotate = False):
    """
    Helper function to quickly orient a joint to its child.
    
    Args:
        joint (str): The name of the joint to orient. Must have a child.
        invert (bool): Wether to mirror the orient for right side.
    """
    aim_value = 1
    if neg_aim:
        aim_value = -1
    
    aim_axis = [aim_value,0,0]
    up_axis = [0,1,0]
    
    if invert:
        aim_axis = [aim_value*-1,0,0]
        up_axis = [0,-1,0]
    
    children = cmds.listRelatives(joint, type = 'transform')
    
    parent = cmds.listRelatives(joint, p = True)
    
    if not parent_rotate:
        parent = None
    
    if children and not parent:
    
        orient = OrientJoint(joint, children)
        orient.set_aim_at(3)
        orient.set_aim_up_at(0)
        orient.set_aim_vector(aim_axis)
        orient.set_up_vector(up_axis)
        orient.run()
    
    if children and parent:
        orient = OrientJoint(joint, children)
        orient.set_aim_at(3)
        orient.set_aim_up_at(1)
        orient.set_aim_vector(aim_axis)
        orient.set_up_vector([0,0,0])
        orient.run()
        
    if not children:
        cmds.makeIdentity(joint, jo = True, apply = True)

def orient_y_to_child(joint, invert = False, neg_aim = False, up_axis = [0,0,1]):
    """
    Helper function to quickly orient a joint to its child.
    
    Args:
        joint (str): The name of the joint to orient. Must have a child.
        invert (bool): Wether to mirror the orient for right side.
    """
    
    aim_value = 1
    if neg_aim:
        aim_value = -1
    
    aim_axis = [0,aim_value,0]
    
    if invert:
        aim_axis = [0,aim_value*-1,0]
        
        values = []
        
        for value in up_axis:
            if value != 0:
                value *= -1
            values.append(value)
        up_axis = values
    
    world_up_axis = [1,0,0]
    
    children = cmds.listRelatives(joint, type = 'transform')
    
    parent = cmds.listRelatives(joint, type = 'joint')
    
    if children:
    
        if not parent:
            orient = OrientJoint(joint, children)
            orient.set_aim_at(3)
            orient.set_aim_up_at(0)
            orient.set_aim_vector(aim_axis)
            orient.set_up_vector(up_axis)
            orient.set_world_up_vector(world_up_axis)
            orient.run()
        if parent:
            
            orient = OrientJoint(joint, children)
            orient.set_aim_at(3)
            orient.set_aim_up_at(1)
            orient.set_aim_vector(aim_axis)
            orient.set_up_vector([0,1,0])
            orient.set_world_up_vector([0,0,0])
            orient.run()
            

    if not children:
        cmds.makeIdentity(joint, jo = True, apply = True)


def orient_z_to_child(joint, invert = False, neg_aim = False):
    """
    Helper function to quickly orient a joint to its child.
    
    Args:
        joint (str): The name of the joint to orient. Must have a child.
        invert (bool): Wether to mirror the orient for right side.
    """
    
    aim_value = 1
    if neg_aim:
        aim_value = -1
    
    aim_axis = [0,0,aim_value]
    up_axis = [0,1,0]
    
    if invert:
        aim_axis = [0,0,aim_value*-1]
        up_axis = [0,-1,0]
    
    children = cmds.listRelatives(joint, type = 'transform')
    
    if children:
    
        orient = OrientJoint(joint, children)
        orient.set_aim_at(3)
        orient.set_aim_up_at(0)
        orient.set_aim_vector(aim_axis)
        orient.set_up_vector(up_axis)
        orient.run()

    if not children:
        cmds.makeIdentity(joint, jo = True, apply = True)


def find_transform_right_side(transform, check_if_exists = True):
    """
    Try to find the right side of a transform.
    *_L will be converted to *_R 
    if not 
    L_* will be converted to R_*
    if not 
    *lf_* will be converted to *rt_*
    
    Args:
        transform (str): The name of a transform.
        
    Returns: 
        str: The name of the right side transform if it exists.
    """
    
    other = ''
    
    if transform.endswith('_L'):
        
        other = util.replace_string_at_end(transform, '_L', '_R')
        
        if cmds.objExists(other) and check_if_exists:
            return other
        
        if not check_if_exists:
            return other
    
    other = ''
    
    if transform.endswith('_l'):
        
        other = util.replace_string_at_end(transform, '_l','_r')
        
        if cmds.objExists(other) and check_if_exists:
            return other
        
        if not check_if_exists:
            return other
    
    other = ''
        
    if transform.startswith('L_') and not transform.endswith('_R'):
        
        other = util.replace_string_at_start(transform, 'L_', 'R_')
        
        if cmds.objExists(other) and check_if_exists:
            return other 
        if not check_if_exists:
            return other
    
    other = ''
    
    if transform.startswith('l_') and not transform.endswith('_R') and not transform.startswith('R_'):
        other = transform = 'r_' + transform[2:]
        
        if cmds.objExists(other) and check_if_exists:
            return other
        if not check_if_exists:
            return other
    
    other = ''
     
    if transform.find('lf_') > -1 and not transform.endswith('_R') and not transform.startswith('R_'):
        other = transform.replace('lf_', 'rt_')
        
        if cmds.objExists(other) and check_if_exists:
            return other
        if not check_if_exists:
            return other
    
    other = ''
    
    if transform.find('Left') > -1:
        other = transform.replace('Left', 'Right')
        if cmds.objExists(other) and check_if_exists:
            return other
        if not check_if_exists:
            return other

    other = ''

    if transform.find('left') > -1:
        other = transform.replace('left', 'right')
        if cmds.objExists(other) and check_if_exists:
            return other
        if not check_if_exists:
            return other
          
    if transform.find('_L_') > -1:
        other = transform.replace('_L_', '_R_')
        if cmds.objExists(other) and check_if_exists:
            return other
        if not check_if_exists:
            return other
    
    other = ''
    
    return ''

def find_transform_left_side(transform,check_if_exists = True):
    """
    Try to find the right side of a transform.
    *_R will be converted to *_L 
    if not 
    R_* will be converted to L_*
    if not 
    *rt_* will be converted to *lf_*
    
    Args:
        transform (str): The name of a transform.
        
    Returns: 
        str: The name of the right side transform if it exists.
    """
    
    other = ''
    
    if transform.endswith('_R'):
        
        other = util.replace_string_at_end(transform, '_R', '_L')
        
        if cmds.objExists(other) and check_if_exists:
            return other
        if not check_if_exists:
            return other

    other = ''
    
    if transform.endswith('_r'):
        
        other = util.replace_string_at_end(transform, '_r','_l')
        
        if cmds.objExists(other) and check_if_exists:
            return other
        
        if not check_if_exists:
            return other
    
    other = ''
        
    if transform.startswith('R_') and not transform.endswith('_L'):
        
        other = util.replace_string_at_start(transform, 'R_', 'L_')
        
        if cmds.objExists(other) and check_if_exists:
            return other 
        if not check_if_exists:
            return other

    other = ''

    if transform.startswith('r_') and not transform.endswith('_L') and not transform.startswith('L_'):
        other = transform.replace('r_', 'l_')
        
        if cmds.objExists(other) and check_if_exists:
            return other
        if not check_if_exists:
            return other
        
    other = ''
    
    if transform.find('rt_') > -1 and not transform.endswith('_L') and not transform.startswith('L_'):
        other = transform.replace('rt_', 'lf_')
        
        if cmds.objExists(other) and check_if_exists:
            return other
        if not check_if_exists:
            return other

    other = ''

    if transform.find('Right') > -1:
        other = transform.replace('Right', 'Left')
        if cmds.objExists(other) and check_if_exists:
            return other
        if not check_if_exists:
            return other

    other = ''

    if transform.find('right') > -1:
        other = transform.replace('right', 'left')
        if cmds.objExists(other) and check_if_exists:
            return other
        if not check_if_exists:
            return other

    return ''



def mirror_toggle(transform, bool_value):
    
    if not cmds.objExists('%s.mirror' % transform):
        cmds.addAttr(transform, ln = 'mirror', at = 'bool', k = True)
    
    cmds.setAttr('%s.mirror' % transform, bool_value)
    

def mirror_xform(prefix = None, suffix = None, string_search = None, create_if_missing = False, transforms = [], left_to_right = True, skip_meshes = True):
    """
    Mirror the positions of all transforms that match the search strings.
    If search strings left at None, search all transforms and joints. 
    
    Args:
        prefix (str): The prefix to search for.
        suffix (str): The suffix to search for.
        string_search (str): Search for a name containing string search.
    """
    
    scope_joints = []
    scope_transforms = []
    
    joints = []
    
    skip_search = False
    
    if transforms:
        skip_search = True
        
        temp_transforms = list(transforms)
        
        transforms = []
        
        for thing in temp_transforms:
            if core.is_referenced(thing):
                continue
            
            node_type = cmds.nodeType(thing)
            
            if node_type == 'joint':
                joints.append(thing)
            if node_type == 'transform':
                transforms.append(thing)
    
    if not skip_search:
        if not prefix and not suffix and not string_search:
            joints = cmds.ls(type ='joint')
            transforms = cmds.ls(type = 'transform')
        
        if prefix:
            joints = cmds.ls('%s*' % prefix, type = 'joint')
            transforms = cmds.ls('%s*' % prefix, type = 'transform')
            
        scope_joints += joints
        scope_transforms += transforms
            
        if suffix:    
            joints = cmds.ls('*%s' % suffix, type = 'joint')
            transforms = cmds.ls('*%s' % suffix, type = 'transform')
    
        scope_joints += joints
        scope_transforms += transforms
            
        if string_search:
            joints = cmds.ls('*%s*' % string_search, type = 'joint')
            transforms = cmds.ls('*%s*' % string_search, type = 'transform')
        
    scope_joints += joints
    scope_transforms += transforms
        
    scope = scope_joints + scope_transforms
    
    if not scope:
        return
    
    other_parents = {}
    fixed = []
    created = False
    
    for transform in scope:
        
        if core.is_referenced(transform):
            continue
        
        if skip_meshes:
            if cmds.objExists('%s.inMesh' % transform):
                continue
        
        #if cmds.objExists('%s.nearClipPlane' % transform):
        #    continue
        
        other = ''
        if left_to_right:
            other = find_transform_right_side(transform, check_if_exists=False)
            
        if not left_to_right:
            other = find_transform_left_side(transform, check_if_exists=False)
            
        
        if not other:
            continue
        
        if transform in fixed:
            continue
        
        if attr.is_translate_rotate_connected(other, ignore_keyframe=True):
            
            continue
        
        shape_type = core.get_shape_node_type(transform)
        
        if not cmds.objExists(other) and create_if_missing:
            
            node_type = cmds.nodeType(transform)
            
            
            if not node_type == 'joint':
                other_node = cmds.createNode(shape_type)
            
                if core.is_a_shape(other_node):
                    other_node = cmds.listRelatives(other_node, p = True, f = True)
                
                    other = cmds.rename(other_node, other)
                    
            if node_type == 'joint':
                other = cmds.duplicate(transform, po = True, n = other)[0]
                
                if shape_type:
                    
                    other_shape = cmds.createNode(shape_type)
                    
                    if core.is_a_shape(other_shape):
                        temp_parent = cmds.listRelatives(other_shape, p = True, f = True)
                        
                    cmds.parent(other_shape, other, r = True, s = True)
                    
                    other_shape = cmds.rename(other_shape, other + 'Shape')
                    cmds.delete(temp_parent)
            
            created = True
            
            parent = cmds.listRelatives(transform, p = True)
            
            if parent:
                if left_to_right:
                    other_parent = find_transform_right_side(parent[0], check_if_exists=False)
                if not left_to_right:
                    other_parent = find_transform_left_side(parent[0], check_if_exists=False)
                    
                if other_parent:
                    other_parents[other] = other_parent
            

        
       
        if cmds.objExists(other):
            
            if cmds.objExists('%s.mirror' % other):
                mirror = cmds.getAttr('%s.mirror' % other)
                if not mirror:
                    util.show('%s was not mirrored because its mirror attribute is set off.' % other)
                    continue
            
            lock_state = attr.LockTransformState(other)
            lock_state.unlock()
            
            xform = cmds.xform(transform, q = True, ws = True, t = True)
        
            if shape_type == 'locator':
                local_position = cmds.getAttr('%s.localPosition' % transform)[0]
                local_scale = cmds.getAttr('%s.localScale' % transform)[0]
                
                cmds.setAttr('%s.localPosition' % other, *local_position, type = 'float3')
                cmds.setAttr('%s.localScale' % other, *local_scale, type = 'float3')
            
            if cmds.nodeType(other) == 'joint':
                
                radius = cmds.getAttr('%s.radius' % transform)
                
                if not core.is_referenced(other):
                    var = attr.MayaNumberVariable('radius')
                    var.set_node(other)
                    var.set_value(radius)
                
                if not cmds.getAttr('%s.radius' % other, l = True):
                    cmds.setAttr('%s.radius' % other, radius)
                    
                cmds.move((xform[0]*-1), xform[1], xform[2], '%s.scalePivot' % other, 
                                                             '%s.rotatePivot' % other, a = True)
                
                
            if cmds.nodeType(other) == 'transform':
                
                pos = [ (xform[0]*-1), xform[1],xform[2] ]
                                
                cmds.xform(other, ws = True, t = pos)
                pivot = cmds.xform(transform, q = True, ws = True, rp = True)
                cmds.move((pivot[0]*-1), pivot[1], pivot[2], '%s.scalePivot' % other, 
                                                             '%s.rotatePivot' % other, a = True)

                if cmds.objExists('%s.localPosition' % transform):
                    fix_locator_shape_position(transform)
                
                if cmds.objExists('%s.localPosition' % other):
                    fix_locator_shape_position(other)

            children = cmds.listRelatives(transform, type = 'transform')
            if not children:
                rotate = cmds.getAttr('%s.rotate' % transform)[0]
                scale = cmds.getAttr('%s.scale' % transform)[0]
                rotate = util.convert_to_sequence(rotate)
                scale = util.convert_to_sequence(scale)
                rotate[1] *= -1
                rotate[2] *= -1
                cmds.setAttr('%s.rotate' % other, *rotate, type = 'float3')
                cmds.setAttr('%s.scale' % other, *scale, type = 'float3')
                
                lock_state.restore_initial()
            
            fixed.append(other)
            
    if create_if_missing:
        for other in list(other_parents.keys()):
            parent = other_parents[other]
            
            if cmds.objExists(parent):
                
                cmds.parent(other, parent)
                
    if not create_if_missing:
        if fixed:
            return True
        if not fixed:
            return False
    if create_if_missing:
        if created:
            return True
        if not created:
            return False

def mirror_invert(transform, other = None):
    """
    If transform is joint_lip_L and there is a corresponding joint_lip_R, this will change joint_lip_R to have space that mirrors joint_lip_L.
    """
    
    
    node_type = cmds.nodeType(transform)
    
    if not other:
        other = find_transform_right_side(transform)
    
    if not other:
        return
    
    if not node_type == 'joint':
        dup = cmds.duplicate(transform, po = True)[0]
    if node_type == 'joint':
        cmds.makeIdentity(transform, apply = True, r = True)
        dup = cmds.group(em = True)
    
    match = MatchSpace(transform, dup)
    match.translation_rotation()
    match.scale()
    
    group = cmds.group(em = True)
    
    cmds.parent(dup, group)
    
    cmds.setAttr('%s.rotateY' % group, 180)
    cmds.setAttr('%s.scaleZ' % group, -1)
    
    parent = cmds.listRelatives(other, p = True)
    
    if parent:
        cmds.parent(dup, parent)
    
    if not parent:
        cmds.parent(dup, w = True)
    
    match_all_transform_values(dup, other)
    
    if cmds.nodeType(other) == 'joint':
        cmds.makeIdentity(other, r = True, apply = True)
    
    cmds.delete(group)
    cmds.delete(dup)

def match_all_transform_values(source_transform, target_transform):
    """
    Match transform values from source to target.
    """
    
    attributes = ['translate','rotate','scale']
    axis = ['X','Y','Z']
    
    for attribute in attributes:
        
        for ax in axis:
            
            value = cmds.getAttr('%s.%s%s' % (source_transform, attribute, ax))
            cmds.setAttr('%s.%s%s' % (target_transform, attribute, ax), value)
            
def match_joint_xform(prefix, other_prefix):
    """
    Match the positions of joints with similar names.
    For example, skin_arm_L could be matched to joint_arm_L, if they exists and prefix = skin and other_prefix = joint.
    Args: 
        prefix (str)
        other_prefix (str) 
    """
    scope = cmds.ls('%s*' % other_prefix, type = 'joint')

    for joint in scope:
        other_joint = joint.replace(other_prefix, prefix)

        if cmds.objExists(other_joint):    
            match = MatchSpace(joint, other_joint)
            match.rotate_scale_pivot_to_translation()

def match_orient(prefix, other_prefix):
    """
    Match the orientations of joints with similar names.
    For example, skin_arm_L could be matched to joint_arm_L, if they exists and prefix = skin and other_prefix = joint.
    Args: 
        prefix (str)
        other_prefix (str) 
    """
    scope = cmds.ls('%s*' % prefix, type = 'joint')
    
    for joint in scope:
        other_joint = joint.replace(prefix, other_prefix)

        if cmds.objExists(other_joint): 

            pin = PinXform(joint)
            pin.pin()
            cmds.delete( cmds.orientConstraint(other_joint, joint) )
            pin.unpin()
            cmds.makeIdentity(joint, apply = True, r = True)
            
    for joint in scope:
        other_joint = joint.replace(prefix, other_prefix)
        
        if not cmds.objExists(other_joint):
            cmds.makeIdentity(joint, apply = True, jo = True)

def scale_constraint_to_local(scale_constraint, keep_negative_scale = True):
    """
    Scale constraint can work wrong when given the parent matrix.
    Disconnect the parent matrix to remove this behavior.
    Reconnect using scale_constraint_to_world if applying multiple constraints.
    
    Args:
        scale_constraint (str): The name of the scale constraint to work on.
    """
    
    offset = cmds.getAttr('%s.offset' % scale_constraint)
    
    constraint_editor = ConstraintEditor()
        
    weight_count = constraint_editor.get_weight_count(scale_constraint)
    attr.disconnect_attribute('%s.constraintParentInverseMatrix' % scale_constraint)
    
    
    
    for inc in range(0, weight_count):
        target_attr = '%s.target[%s].targetParentMatrix' % (scale_constraint, inc)
        
        if not keep_negative_scale:
            attr.disconnect_attribute(target_attr)
        
        if keep_negative_scale:
            matrix = cmds.getAttr(target_attr)
            test_mult = attr.get_attribute_input(target_attr, node_only = True)
            
            attr.disconnect_attribute(target_attr)
            
            if not cmds.nodeType(test_mult) == 'multMatrix':
            
                mult = cmds.createNode('multMatrix', n = 'multTarget_%s_%s' % (inc, scale_constraint))
                cmds.setAttr('%s.matrixIn[0]' % mult, *matrix, type = 'matrix')
                cmds.connectAttr('%s.matrixSum' % mult, target_attr)
            
            
    #cmds.setAttr('%s.offset' % scale_constraint, *offset)
    

def scale_constraint_to_world(scale_constraint):
    """
    Works with scale_constraint_to_local.
    
    Args:
        scale_constraint (str): The name of the scale constraint affected by scale_constraint_to_local.
    """
    
    constraint_editor = ConstraintEditor()
    
    weight_count = constraint_editor.get_weight_count(scale_constraint)
    
    node = attr.get_attribute_outputs('%s.constraintScaleX' % scale_constraint, node_only = True)
    
    
    
    if node:
        cmds.connectAttr('%s.parentInverseMatrix' % node[0], '%s.constraintParentInverseMatrix' % scale_constraint)
    
    for inc in range(0, weight_count):
        
        target = attr.get_attribute_input('%s.target[%s].targetScale' % (scale_constraint, inc), True)
        target_attr = '%s.target[%s].targetParentMatrix' % (scale_constraint, inc)
        
        test_mult = attr.get_attribute_input(target_attr, node_only = True)
        if cmds.nodeType(test_mult) == 'multMatrix':
            cmds.delete(test_mult)
        
        cmds.connectAttr('%s.parentInverseMatrix' % target, '%s.target[%s].targetParentMatrix' % (scale_constraint, inc) )
    
def duplicate_joint_section(joint, name = ''):
    """
    Joint chains ususally have a parent and a child along the chain. 
    This will duplicate one of those sections.  You need only supply the parent joint.
    
    Args:
        joint (str): The name of the joint to duplicate.
        name (str): The name to give the joint section.
        
    Returns:
        list: [duplicate, sub duplicate]. If no sub duplicate, then [duplicate, None]
    """
    
    
    rels = cmds.listRelatives(joint, type = 'joint', f = True)
    
    if not rels:
        return
    
    child = rels[0]
    
    if not name:
        name = 'duplicate_%s' % joint
    
    duplicate = cmds.duplicate(joint, po = True, n = name)[0]
    sub_duplicate = None
    
    if child:
        sub_duplicate = cmds.duplicate(child, po = True, n = (name + '_end'))[0] 
        cmds.parent(sub_duplicate, duplicate)
        cmds.makeIdentity(sub_duplicate, jo = True, r = True, apply = True)
        
    if not sub_duplicate:
        return duplicate, None
    if sub_duplicate:
        return duplicate, sub_duplicate   
    


def transforms_to_joint_chain(transforms, name = ''):
    """
    Given a list of transforms, create a joint chain.
    
    Args:
        transforms (list): List of transforms. Their positions will be used to set joint positions.
        name (str): The description to give the joints.
        
    Returns:
        list: The names of the joints created.
    """
    cmds.select(cl = True)
    
    joints = []
    
    for transform in transforms:
        
        if not name:
            name = transform     
            
        joint = cmds.joint(n = core.inc_name('joint_%s' % name))
        
        MatchSpace(transform, joint).translation_rotation()
        
        joints.append(joint)
        
    return joints

def positions_to_joint_chain(positions, name = ''):
    """
    Args:
        positions (list): List of vectors. [[0,0,0],[0,0,0],...]
        name (str): Description to give the joints
    """
    
    cmds.select(cl = True)
    joints = []

    inc = 1

    for position in positions:
        
        if not name:
            name = 'joint_pos_%s' % inc
        
        joint = cmds.joint(n = core.inc_name(name), p = position)
        
        joints.append(joint)
            
        inc += 1
        
    cmds.joint(joints[0],  e = True, zso = True, oj = 'xyz', sao = 'yup')
    
    return joints

def attach_to_closest_transform(source_transform, target_transforms):
    """
    Attach the source_transform to the closest transform in the list of target_transforms.
    
    Args:
        source_transform (str): The name of a transform to check distance to.
        target_transforms (list): List of transforms. The closest to source_transform will be attached to it.
    """
    closest_transform = get_closest_transform(source_transform, target_transforms)
    
    create_follow_group(closest_transform, source_transform)

def set_space_scale(scale_x,scale_y,scale_z, transform):
    
    orig_scale_x = cmds.getAttr('%s.scaleX' % transform)
    orig_scale_y = cmds.getAttr('%s.scaleY' % transform)
    orig_scale_z = cmds.getAttr('%s.scaleZ' % transform)
    
    invert_x = abs(orig_scale_x)/orig_scale_x
    invert_y = abs(orig_scale_y)/orig_scale_y
    invert_z = abs(orig_scale_z)/orig_scale_z
    
    scale_x = scale_x * invert_x
    scale_y = scale_y * invert_y
    scale_z = scale_z * invert_z
    
    cmds.setAttr('%s.scaleX' % transform, scale_x)
    cmds.setAttr('%s.scaleY' % transform, scale_y)
    cmds.setAttr('%s.scaleZ' % transform, scale_z)

def connect_inverse_scale(transform, joint):
    
    orig_scale_x = cmds.getAttr('%s.scaleX' % transform)
    orig_scale_y = cmds.getAttr('%s.scaleY' % transform)
    orig_scale_z = cmds.getAttr('%s.scaleZ' % transform)
    
    invert_x = abs(orig_scale_x)/orig_scale_x
    invert_y = abs(orig_scale_y)/orig_scale_y
    invert_z = abs(orig_scale_z)/orig_scale_z
    
    multiply = cmds.createNode('multiplyDivide', n = 'multiply_inverseScale_%s' % joint)
    
    cmds.connectAttr('%s.scale' % transform, '%s.input1' % multiply)
    cmds.connectAttr('%s.output' % multiply, '%s.inverseScale' % joint)
    
    cmds.setAttr('%s.input2X' % multiply, invert_x)
    cmds.setAttr('%s.input2Y' % multiply, invert_y)
    cmds.setAttr('%s.input2Z' % multiply, invert_z)
    
def randomize(translate = [.1,.1,.1], rotate = [1,1,1], scale = [.1,.1,.1], transforms = None):
    """
    Good for giving subtle randomness to many transforms.
    
    Args
        translate (list): 3 value list. The values work as the amount it can deviate in positive and negative.
        rotate (list): 3 value list. The values work as the amount it can deviate in positive and negative.
        scale (list): 3 value list. How much the scale can deviate from 1.
    """
    
    if transforms:
        sel = transforms
        
    if not transforms:
        sel = cmds.ls(sl = True, type = 'transform')

    for thing in sel:
        
        cmds.move(  random.uniform(-translate[0], translate[0]), 
                    random.uniform(-translate[1], translate[1]), 
                    random.uniform(-translate[2], translate[2]), 
                    thing, 
                    relative = True)
                    
        cmds.rotate(  random.uniform(-rotate[0], rotate[0]), 
                    random.uniform(-rotate[1], rotate[1]), 
                    random.uniform(-rotate[2], rotate[2]), 
                    thing,
                    ocp = True,
                    relative = True)
                    
        scale_x_invert = 1 - scale[0]
        scale_y_invert = 1 - scale[1]
        scale_z_invert = 1 - scale[2]
                    
        cmds.scale(random.uniform(scale_x_invert, (1+scale[0])),
                    random.uniform(scale_y_invert, (1+scale[1])),
                    random.uniform(scale_z_invert, (1+scale[2])))

def fix_locator_shape_position(locator_name):
    
    pivot_pos = cmds.xform(locator_name, q =True, os = True, rp = True)
    
    cmds.setAttr('%s.localPositionX' % locator_name, pivot_pos[0])
    cmds.setAttr('%s.localPositionY' % locator_name, pivot_pos[1])
    cmds.setAttr('%s.localPositionZ' % locator_name, pivot_pos[2])
    
def set_translateX_limit(transform, min_value = None, max_value = None):
    min_bool = 0
    max_bool = 0
    
    if min_value:
        min_bool = 1
    if max_value:
        max_bool = 1
    
    if not min_value:
        min_value = -1
    if not max_value:
        max_value = 1
    
    cmds.transformLimits(transform, tx = [min_value, max_value],etx= [min_bool, max_bool])

def set_translateY_limit(transform, min_value = None, max_value = None):
    min_bool = 0
    max_bool = 0
    
    if min_value:
        min_bool = 1
    if max_value:
        max_bool = 1
    
    if not min_value:
        min_value = -1
    if not max_value:
        max_value = 1
    
    cmds.transformLimits(transform, ty = [min_value, max_value],ety= [min_bool, max_bool])
    
def set_translateZ_limit(transform, min_value = None, max_value = None):
    min_bool = 0
    max_bool = 0
    
    if min_value:
        min_bool = 1
    if max_value:
        max_bool = 1
    
    if not min_value:
        min_value = -1
    if not max_value:
        max_value = 1
    
    cmds.transformLimits(transform, tz = [min_value, max_value],etz= [min_bool, max_bool])

        
        
def set_rotateX_limit(transform, min_value = None, max_value = None):
    
    min_bool = 0
    max_bool = 0
    
    if min_value:
        min_bool = 1
    if max_value:
        max_bool = 1
    
    if not min_value:
        min_value = -45
    if not max_value:
        max_value = 45
    
    cmds.transformLimits(transform, rx = [min_value, max_value],erx= [min_bool, max_bool])
    
def set_rotateY_limit(transform, min_value, max_value):
    
    min_bool = 0
    max_bool = 0
    
    if min_value:
        min_bool = 1
    if max_value:
        max_bool = 1
    
    if not min_value:
        min_value = -45
    if not max_value:
        max_value = 45
    
    cmds.transformLimits(transform, ry = [min_value, max_value],ery= [min_bool, max_bool])
        
def set_rotateZ_limit(transform, min_value, max_value):
    
    min_bool = 0
    max_bool = 0
    
    if min_value:
        min_bool = 1
    if max_value:
        max_bool = 1
    
    if not min_value:
        min_value = -45
    if not max_value:
        max_value = 45
    
    cmds.transformLimits(transform, rz = [min_value, max_value],erz= [min_bool, max_bool])
    
def orig_matrix_match(transform, destination_transform):
    """
    This command is to be used for space switching.
    the transforms need to have origMatrix
    origMatrix is a matrix attribute that should store the original worldMatrix of the transform and destination_transform.
    By doing this it is possible to match any transform to any transform that has origMatrix.  It basically saves out how the two transforms relate spacially.  
    origMatrix needs to be added to the transform before animation/posing happens and before this command runs.
    
    """
    orig_matrix = cmds.getAttr('%s.origMatrix' % transform)
    parent_inverse_matrix = cmds.getAttr('%s.parentInverseMatrix' % transform)
    rotate_order = cmds.getAttr('%s.rotateOrder' % transform)
    
    rotate_pivot = cmds.getAttr('%s.rotatePivot' % transform)[0]
    
    orig_dest_matrix = cmds.getAttr('%s.origMatrix' % destination_transform)
    dest_matrix = cmds.getAttr('%s.worldMatrix' % destination_transform)
    
    om_orig_matrix = om.MMatrix(orig_matrix)
    om_parent_inverse_matrix = om.MMatrix(parent_inverse_matrix)
    om_orig_dest_matrix = om.MMatrix(orig_dest_matrix)
    om_dest_matrix = om.MMatrix(dest_matrix)
    
    tm_orig_matrix = om.MTransformationMatrix(om_orig_matrix)
    v_rotate_pivot = om.MVector(rotate_pivot)
    tm_orig_matrix.translateBy(v_rotate_pivot, om.MSpace.kObject)
    om_orig_matrix = tm_orig_matrix.asMatrix()
    
    tm = om.MTransformationMatrix()
    tm.translateBy(v_rotate_pivot, om.MSpace.kObject)
    pivot_matrix = tm.asMatrix()
    
    new_matrix = om_orig_matrix * om_orig_dest_matrix.inverse() * om_dest_matrix * om_parent_inverse_matrix
    
    new_matrix = new_matrix * pivot_matrix.inverse()
    
    transform_matrix = om.MTransformationMatrix(new_matrix)
    transform_matrix.reorderRotation(rotate_order + 1)
    
    values = transform_matrix.translation(om.MSpace.kWorld)
    try:
        cmds.setAttr('%s.translateX' % transform, values.x)
    except:
        pass
    try:
        cmds.setAttr('%s.translateY' % transform, values.y)
    except:
        pass
    try:
        cmds.setAttr('%s.translateZ' % transform, values.z)
    except:
        pass
    
    values = transform_matrix.rotation()
    try:
        cmds.setAttr('%s.rotateX' % transform, math.degrees(values.x))
    except:
        pass
    try:
        cmds.setAttr('%s.rotateY' % transform, math.degrees(values.y))
    except:
        pass
    try:
        cmds.setAttr('%s.rotateZ' % transform, math.degrees(values.z))
    except:
        pass
    
    values = transform_matrix.scale(om.MSpace.kWorld)
    
    try:
        cmds.setAttr('%s.scaleX' % transform, values[0])
        cmds.setAttr('%s.scaleY' % transform, values[1])
        cmds.setAttr('%s.scaleZ' % transform, values[2])
    except:
        pass

def add_twist_reader(transform, read_axis = 'X'):
    
    read_axis = read_axis.upper()
    
    local_matrix = cmds.createNode('multMatrix', n = 'twistLocalMatrix_%s' % transform)
    
    cmds.connectAttr('%s.worldMatrix[0]' % transform, '%s.matrixIn[0]' % local_matrix)
    cmds.connectAttr('%s.parentInverseMatrix[0]' % transform, '%s.matrixIn[1]' % local_matrix)
    
    local_matrix_offset = cmds.getAttr('%s.inverseMatrix' % transform)
    cmds.setAttr('%s.matrixIn[2]' % local_matrix, *local_matrix_offset, type = 'matrix')
    
    decompose = cmds.createNode('decomposeMatrix', n = 'twistDecompose_%s' % transform)
    
    cmds.connectAttr('%s.matrixSum' % local_matrix, '%s.inputMatrix' % decompose)
    
    normalize = cmds.createNode('quatNormalize', n = 'twistNormalize_%s' % transform)
    
    cmds.connectAttr('%s.outputQuat' % decompose, '%s.inputQuat' % normalize)
    
    euler = cmds.createNode('quatToEuler', n = 'twistEuler_%s' % transform)
    
    cmds.addAttr(transform, ln = 'twist', k = True)
    
    cmds.connectAttr('%s.outputQuat' % normalize, '%s.inputQuat' % euler)
    
    cmds.connectAttr('%s.outputRotate%s' % (euler, read_axis), '%s.twist' % transform)
    
    