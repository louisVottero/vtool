# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

from random import uniform

import vtool.util
import vtool.util_math
import api


if vtool.util.is_in_maya():
    import maya.cmds as cmds
    import maya.mel as mel
    import maya.api.OpenMaya as om
    
import core
import space
import attr

RENDER_DEFAULT_CAST_SHADOWS = True
RENDER_DEFAULT_RECEIVE_SHADOWS = True
RENDER_DEFAULT_HOLD_OUT = False
RENDER_DEFAULT_MOTION_BLUR = True
RENDER_DEFAULT_PRIMARY_VISIBILITY = True
RENDER_DEFAULT_SMOOTH_SHADING = True
RENDER_DEFAULT_VISIBLE_IN_REFLECTIONS = True
RENDER_DEFAULT_VISIBLE_IN_REFRACTIONS = True
RENDER_DEFAULT_DOUBLE_SIDED = True
RENDER_DEFAULT_OPPOSITE = False

def get_object(name):
    
    if not name or not cmds.objExists(name):
        return
    
    selection_list = om.MSelectionList()
    selection_list.add(name)
    
    if cmds.objectType(name, isAType = 'transform') or cmds.objectType(name, isAType = 'shape'):
        return selection_list.getDagPath(0)    
    
    return selection_list.getDependNode(0)

class MeshTopologyCheck(object):
    
    def __init__(self, mesh1, mesh2):
        
        self.set_first_mesh(mesh1)
        self.set_second_mesh(mesh2)

        
    def set_first_mesh(self, mesh):
        self.mesh1 = get_mesh_shape(mesh,0)
        self.mesh1_function = None
        self.mesh1_vert_count = None
        self.mesh1_edge_count = None
        self.mesh1_face_count = None

        self.mesh1_function = api.MeshFunction(self.mesh1)
        self.mesh1_vert_count = self.mesh1_function.get_number_of_vertices()
        self.mesh1_edge_count = self.mesh1_function.get_number_of_edges()
        self.mesh1_face_count = self.mesh1_function.get_number_of_faces()

    def set_second_mesh(self, mesh):
        self.mesh2 = get_mesh_shape(mesh,0)
        self.mesh2_vert_count = None
        self.mesh2_edge_count = None
        self.mesh2_face_count = None
        
        self.mesh2_function = api.MeshFunction(self.mesh2)
        self.mesh2_vert_count = self.mesh2_function.get_number_of_vertices()
        self.mesh2_edge_count = self.mesh2_function.get_number_of_edges()
        self.mesh2_face_count = self.mesh2_function.get_number_of_faces()
    
    def check_vert_count(self):
        
        if self.mesh1_vert_count == self.mesh2_vert_count:
            return True
        
        return False
    
    def check_edge_count(self):

        if self.mesh1_edge_count == self.mesh2_edge_count:
            return True
        
        return False
    
    def check_face_count(self):
        
        if self.mesh1_face_count == self.mesh2_face_count:
            return True
        
        return False    
    
    def check_vert_face_count(self):
    
        if not self.check_face_count():
            return False
    
        if not self.check_vert_count():
            return False
        
        return True
    
    def check_vert_edge_face_count(self):
        
        if not self.check_face_count():
            return False
        
        if not self.check_vert_count():
            return False
        
        if not self.check_edge_count():
            return False
            
        return True

    def check_first_face_verts(self):
        
        face1 = face_to_vertex('%s.f[0]' % self.mesh1)
        face2 = face_to_vertex('%s.f[0]' % self.mesh2)
        
        vertex_indices1 = get_vertex_indices(face1)
        vertex_indices2 = get_vertex_indices(face2)
        
        if not vertex_indices1 == vertex_indices2:
            return False
        else:
            return True
        
    def check_last_face_verts(self):
        
        faces1 = get_faces(self.mesh1)
        faces2 = get_faces(self.mesh2)
        
        faces1 = face_to_vertex(faces1[-1])
        faces2 = face_to_vertex(faces2[-1])
        
        vertex_indices1 = get_vertex_indices(faces1)
        vertex_indices2 = get_vertex_indices(faces2)
        
        if not vertex_indices1 == vertex_indices2:
            return False
        else:
            return True
    
    def check_face_order(self):
        
        faces1 = get_faces(self.mesh1)
        faces2 = get_faces(self.mesh2)
        
        faces1 = get_face_indices(faces1)
        faces2 = get_face_indices(faces2)
        
        if not faces1 == faces2:
            return False
        else:
            return True


class Rivet(object):
    def __init__(self, name):
        self.surface = None
        self.edges = []
        
        self.name = name  
        
        self.aim_constraint = None
        
        self.uv = [0.5,0.5]
        
        self.create_joint = False
        self.surface_created = False
        
        self.percentOn = True
        self._local = False
        
        self._use_transform = False
        self._mesh_in = None
        
    def _create_surface(self):
        
        
        mesh = self.edges[0].split('.')[0]
        shape = get_mesh_shape(mesh)
        
        edge_index_1 = vtool.util.get_last_number(self.edges[0])
        edge_index_2 = vtool.util.get_last_number(self.edges[1])
        
        vert_iterator = api.IterateEdges(shape)
        vert_ids = vert_iterator.get_connected_vertices(edge_index_1)
        
        edge_to_curve_1 = cmds.createNode('polyEdgeToCurve', n = core.inc_name('rivetCurve1_%s' % self.name))
        cmds.setAttr('%s.inputComponents' % edge_to_curve_1, 2,'vtx[%s]' % vert_ids[0], 'vtx[%s]' % vert_ids[1], type='componentList')
        
        vert_iterator = api.IterateEdges(shape)
        vert_ids = vert_iterator.get_connected_vertices(edge_index_2)
        
        edge_to_curve_2 = cmds.createNode('polyEdgeToCurve', n = core.inc_name('rivetCurve2_%s' % self.name))
        
        cmds.setAttr('%s.inputComponents' % edge_to_curve_2, 2,'vtx[%s]' % vert_ids[0], 'vtx[%s]' % vert_ids[1], type='componentList')
        
        world_matrix_hook = False
        if not self._mesh_in:
            self._mesh_in = '%s.outMesh' % mesh
            world_matrix_hook = True
        
        
        cmds.connectAttr(self._mesh_in, '%s.inputPolymesh' % edge_to_curve_1)
        cmds.connectAttr(self._mesh_in, '%s.inputPolymesh' % edge_to_curve_2)
        
        if world_matrix_hook:
            cmds.connectAttr('%s.worldMatrix' % mesh, '%s.inputMat' % edge_to_curve_1)
            cmds.connectAttr('%s.worldMatrix' % mesh, '%s.inputMat' % edge_to_curve_2)
        
        loft = cmds.createNode('loft', n = core.inc_name('rivetLoft_%s' % self.name))
        cmds.setAttr('%s.ic' % loft, s = 2)
        cmds.setAttr('%s.u' % loft, True)
        cmds.setAttr('%s.rsn' % loft, True)
        cmds.setAttr('%s.degree' % loft, 1)
        cmds.setAttr('%s.autoReverse' % loft, 0)
        
        cmds.connectAttr('%s.oc' % edge_to_curve_1, '%s.ic[0]' % loft)
        cmds.connectAttr('%s.oc' % edge_to_curve_2, '%s.ic[1]' % loft)
                
        self.surface = loft
        self.surface_created = True
                
        
    def _create_rivet(self):
        if not self._use_transform:
            if not self.create_joint:
                self.rivet = cmds.spaceLocator(n = core.inc_name('rivet_%s' % self.name))[0]
                
            if self.create_joint:
                cmds.select(cl = True)
                self.rivet = cmds.joint(n = core.inc_name('joint_%s' % self.name))
        if self._use_transform:
            self.rivet = self.name
        
    def _create_point_on_surface(self):
        self.point_on_surface = cmds.createNode('pointOnSurfaceInfo', n = core.inc_name('pointOnSurface_%s' % self.surface ))
        
        cmds.setAttr('%s.turnOnPercentage' % self.point_on_surface, self.percentOn)
        
        cmds.setAttr('%s.parameterU' % self.point_on_surface, self.uv[0])
        cmds.setAttr('%s.parameterV' % self.point_on_surface, self.uv[1])
        
        
    
    def _create_aim_constraint(self):
        self.aim_constraint = cmds.createNode('aimConstraint', n = core.inc_name('aimConstraint_%s' % self.surface))
        cmds.setAttr('%s.aimVector' % self.aim_constraint, 0,1,0, type = 'double3' )
        cmds.setAttr('%s.upVector' % self.aim_constraint, 0,0,1, type = 'double3')
        
    def _connect(self):
        
        if cmds.objExists('%s.worldSpace' % self.surface):
            if not self._local:
                cmds.connectAttr('%s.worldSpace' % self.surface, '%s.inputSurface' % self.point_on_surface)
            if self._local:
                cmds.connectAttr('%s.local' % self.surface, '%s.inputSurface' % self.point_on_surface)
                
        if cmds.objExists('%s.outputSurface' % self.surface):
            cmds.connectAttr('%s.outputSurface' % self.surface, '%s.inputSurface' % self.point_on_surface)
        
        cmds.connectAttr('%s.position' % self.point_on_surface, '%s.translate' % self.rivet)
        cmds.connectAttr('%s.normal' % self.point_on_surface, '%s.target[0].targetTranslate' % self.aim_constraint )
        cmds.connectAttr('%s.tangentV' % self.point_on_surface, '%s.worldUpVector' % self.aim_constraint)
        
        cmds.connectAttr('%s.constraintRotateX' % self.aim_constraint, '%s.rotateX' % self.rivet)
        cmds.connectAttr('%s.constraintRotateY' % self.aim_constraint, '%s.rotateY' % self.rivet)
        cmds.connectAttr('%s.constraintRotateZ' % self.aim_constraint, '%s.rotateZ' % self.rivet)
        
    def _get_angle(self, surface, flip):
        
        if flip:
            cmds.setAttr('%s.reverse[0]' % self.surface, 1)
        if not flip:
            cmds.setAttr('%s.reverse[0]' % self.surface, 0)
            
        parent_surface = cmds.listRelatives(surface, p = True)[0]
        
        vector1 = cmds.xform('%s.cv[0][0]' % parent_surface, q = True, ws = True, t = True)
        vector2 = cmds.xform('%s.cv[0][1]' % parent_surface, q = True, ws = True, t = True)
        position = cmds.xform(self.rivet, q = True, ws = True, t = True)
        
        vectorA = vtool.util.Vector(vector1[0], vector1[1], vector1[2])
        vectorB = vtool.util.Vector(vector2[0], vector2[1], vector2[2])
        vectorPos = vtool.util.Vector(position[0], position[1], position[2])
        
        vector1 = vectorA - vectorPos
        vector2 = vectorB - vectorPos
        
        vector1 = vector1.get_vector()
        vector2 = vector2.get_vector()
        
        angle = cmds.angleBetween( vector1 = vector1, vector2 = vector2 )[-1]
        return angle

    def _correct_bow_tie(self):
        
        surface = cmds.createNode('nurbsSurface')
        
        cmds.connectAttr('%s.outputSurface' % self.surface, '%s.create' % surface)
        
        angle1 = self._get_angle(surface, flip = False)
        angle2 = self._get_angle(surface, flip = True)
        
        if angle1 < angle2:
            cmds.setAttr('%s.reverse[0]' % self.surface, 0)
        if angle1 > angle2:
            cmds.setAttr('%s.reverse[0]' % self.surface, 1)
        
        parent_surface = cmds.listRelatives(surface, p = True)[0]    
        cmds.delete(parent_surface)
        
    def set_surface(self, surface, u, v):
        self.surface = surface
        self.uv = [u,v]
    
    def set_create_joint(self, bool_value):
        self.create_joint = bool_value
                
    def set_edges(self, edges):
        self.edges = edges
        
    def set_percent_on(self, bool_value):
        self.percentOn = bool_value
        
    def set_local(self, bool_value):
        self._local = bool_value
    
    def set_use_transform(self, bool_value):
        self._use_transform = bool_value
        
    def set_mesh_in(self, mesh_out_attribute):
        self._mesh_in = mesh_out_attribute
        
    def create(self):
        
        if not self.surface and self.edges:
            self._create_surface()
            
        self._create_rivet()
        self._create_point_on_surface()
        self._create_aim_constraint()
        self._connect()
        
        cmds.parent(self.aim_constraint, self.rivet)

        if self.surface_created:
            self._correct_bow_tie()
        
        return self.rivet

#--- is

def is_a_mesh(node):
    """
    Test whether the node is a mesh or has a shape that is a mesh.
    
    Args:
        node (str): The name of a node.
        
    Returns:
        bool
    """
    if cmds.objExists('%s.vtx[0]' % node):
        return True
    
    return False

def is_a_surface(node):
    """
    Test whether the node is a surface or has a shape that is a surface.
    
    Args:
        node (str): The name of a node.
        
    Returns:
        bool
    """
    if cmds.objExists('%s.cv[0][0]' % node):
        return True
    
    return False

def is_a_curve(node):
    """
    Test whether the node is a curve or has a shape that is a curve.
    
    Args:
        node (str): The name of a node.
        
    Returns:
        bool
    """
    if cmds.objExists('%s.cv[0]' % node) and not cmds.objExists('%s.cv[0][0]' % node):
        return True
    
    return False




def is_mesh_compatible(mesh1, mesh2):
    """
    Check the two meshes to see if they have the same vert, edge and face count.
    """
    check = MeshTopologyCheck(mesh1, mesh2)
    check_value = check.check_vert_edge_face_count()
    
    if not check_value:
        return False
    
    
    check_value = check.check_first_face_verts()
    
    if not check_value:
        return False
    
    check_value = check.check_last_face_verts()
    
    if not check_value:
        return False
    
    return check_value

def is_mesh_blend_compatible(mesh1, mesh2):
    """
    Check the two meshes to see if they have the same vert, edge and face count.
    """
    #check = MeshTopologyCheck(mesh1, mesh2)
    #return check.check_vert_face_count()
    return is_mesh_compatible(mesh1, mesh2)

def is_mesh_position_same(mesh1, mesh2, tolerance = .00001, check_compatible= True):
    """
    Check the positions of the vertices on the two meshes to see if they have the same positions within the tolerance.
    """
    
    if check_compatible:
        if not is_mesh_compatible(mesh1, mesh2):
            vtool.util.warning('Skipping vert position compare. %s and %s are not compatible.' % (mesh1, mesh2))
            return False
    
    mobject1 = get_object(mesh1)
    mobject2 = get_object(mesh2)
    
    iter1 = om.MItMeshVertex(mobject1)
    iter2 = om.MItMeshVertex(mobject2)
    
    while not iter1.isDone():
        
        if iter1.position != iter2.position:
            return False
        
        iter1.next()
        iter2.next()
    
    return True

def is_cv_count_same(source_curve, target_curve):
    """
    Check if the cv count is the shame
    
    Args:
        source_curve (str): The name of the source curve
        target_curve (str): The name of the target curve
        
    Returns:
        bool
    """
    source_length = len(cmds.ls('%s.cv[*]' % source_curve, flatten = True))
    target_length = len(cmds.ls('%s.cv[*]' % target_curve, flatten = True))
    
    if not source_length == target_length:
        return False
    
    return True

def match_point_position( source_mesh, target_mesh):
    """
    Source and target must have the same topology.
    """
    
    mesh1_fn = api.IterateGeometry(source_mesh)
    point1 = mesh1_fn.get_points_as_list()
    
    target_object = api.nodename_to_mobject(target_mesh)
    target_fn = api.MeshFunction(target_object)
    target_fn.set_vertex_positions(point1)





def match_cv_position( source_curve, target_curve ):
    """
    Match cv positions.
    
    Args:
        source_curve (str)
        target_curve (str)
        
    """
    source_cvs = cmds.ls('%s.cv[*]' % source_curve, flatten = True)
    target_cvs = cmds.ls('%s.cv[*]' % target_curve, flatten = True)
    
    for inc in range(0, len(source_cvs)):
        
        pos = cmds.xform(source_cvs[inc], q= True, t = True, ws = True)
        cmds.xform(target_cvs[inc], t = pos, ws = True)
        
def rotate_shape(transform, x,y,z):
    """
    Looks at the shape node and finds components, then rotations using the x,y,z values
    """  
      
    shapes = core.get_shapes(transform)
        
    components = core.get_components_from_shapes(shapes)  
        
    if components:
        cmds.rotate(x,y,z, components, relative = True)

#--- get

def get_position_different(mesh1, mesh2, tolerance = 0.00001):
    """
    Get a list of vertex indices that do not match.
    """
    mesh1_fn = api.IterateGeometry(mesh1)
    point1 = mesh1_fn.get_points_as_list()
    
    mesh2_fn = api.IterateGeometry(mesh2)
    point2 = mesh2_fn.get_points_as_list()
    
    mismatches = []
    
    for inc in xrange(0, len(point1)):
        
        for sub_inc in xrange(0,3):
            if not vtool.util.is_the_same_number(point1[inc][sub_inc], point2[inc][sub_inc], tolerance):
                mismatches.append(inc)
                break

    return mismatches

def get_position_assymetrical(mesh1, mirror_axis = 'x', tolerance = 0.00001):
    """
    find assymetrical points on a mesh.  
    
    mirros axis currently doesn't work.  Its always checking on x
    """
    mesh1_fn = api.IterateGeometry(mesh1)
    points = mesh1_fn.get_points_as_list()
    test_points = list(points)
    
    point_count = len(points)
    
    not_found = []
    
    for inc in xrange(0, point_count):
        
        source_point = points[inc]
        
        if vtool.util.is_the_same_number(source_point[0], 0):
            continue
            
        test_point_count = len(test_points)
        
        found = False
        
        for sub_inc in xrange(0, test_point_count):
            
            test_point = test_points[sub_inc]
            
            if source_point[0] > 0 and test_point[0] > 0:
                continue
            
            if source_point[0] < 0 and test_point[0] < 0:
                continue
            
            if vtool.util.is_the_same_number(source_point[0], (test_point[0] * -1), tolerance):
                if vtool.util.is_the_same_number(source_point[1], test_point[1]):
                    if vtool.util.is_the_same_number(source_point[2], test_point[2]):
                        found = True
                        test_points.pop(sub_inc)
                        break
            
        if not found:
            not_found.append(inc)
            
    return not_found

def get_thing_from_component(component, component_name = 'vtx'):
    """
    Given a component, return the shape associated.
    """
    thing = None
    
    if component.find('.%s' % component_name) > -1:
        split_selected = component.split('.%s' % component_name)
        if split_selected > 1:
            thing = split_selected[0]
            
            return thing
    
    return thing


    

def get_curve_from_cv(cv):
    """
    Given a single cv, get the corresponding curve
    """
    return get_thing_from_component(cv, 'cv')
    



def get_meshes_in_list(list_of_things):
    """
    Given a list of DG nodes, return any transform that has a mesh shape node.
    """
    found = []
    
    if not list_of_things:
        return
    
    for thing in list_of_things:
        if cmds.nodeType(thing) == 'mesh':
            found_mesh = cmds.listRelatives(thing, p = True)
            if found_mesh:
                found.append(found_mesh[0])
            
        if cmds.nodeType(thing) == 'transform':
            
            shapes = get_mesh_shape(thing)
            if shapes:
                found.append(thing)
     
    return found   

def get_curves_in_list(list_of_things):     
    """
    Given a list of DG nodes, return any transform that has a curve shape node.
    """
    found = []
    
    for thing in list_of_things:
        if cmds.nodeType(thing) == 'nurbsCurve':
            found_mesh = cmds.listRelatives(thing, p = True)[0]
            found.append(found_mesh)
            
        if cmds.nodeType(thing) == 'transform':
            
            shapes = get_curve_shape(thing)
            if shapes:
                found.append(thing)
     
    return found  


def get_surfaces_in_list(list_of_things):     
    """
    Given a list of DG nodes, return any transform that has a surface shape node.
    """
    found = []
    
    for thing in list_of_things:
        if cmds.nodeType(thing) == 'nurbsSurface':
            found_mesh = cmds.listRelatives(thing, p = True)
            found.append(found_mesh)
            
        if cmds.nodeType(thing) == 'transform':
            
            
            shapes = get_surface_shape(thing)
            if shapes:
                found.append(thing)
     
    return found    

def get_selected_edges():
    """
    Returns:
        list: Any edges in the selection list.
    """
    selection = cmds.ls(sl = True, flatten = True)
    found = get_edges_in_list(selection)
    
    return found

def get_selected_meshes():
    """
    Returns:
        list: Any meshes in the selection list.
    """
    selection = cmds.ls(sl = True)
    
    found = get_meshes_in_list(selection)
    return found

def get_selected_curves():
    """
    Returns:
        list: Any curves in the selection list.
    """
    selection = cmds.ls(sl = True)
    found = get_curves_in_list(selection)
    return found

def get_selected_surfaces():
    """
    Returns:
        list: Any surfaces in the selection list.
    """
    selection = cmds.ls(sl = True)
    found = get_surfaces_in_list(selection)
    return found

def get_mesh_shape(mesh, shape_index = 0):
    """
    Get the first mesh shape, or one based in the index.
    
    Args:
        mesh (str): The name of a mesh.
        shape_index (int): Usually zero, but can be given 1 or 2, etc up to the number of shapes - 1. 
        The shape at the index will be returned.
        
    Returns:
        str: The name of the shape. If no mesh shapes then returns None.
    """
    if mesh.find('.vtx'):
        mesh = mesh.split('.')[0]
            
    if cmds.nodeType(mesh) == 'mesh':    
        mesh = cmds.listRelatives(mesh, p = True, f = True)[0]
        
    shapes = core.get_shapes(mesh)
    if not shapes:
        return
    
    if not cmds.nodeType(shapes[0]) == 'mesh':
        return
    
    shape_count = len(shapes)
    
    if shape_index < shape_count:
        return shapes[0]
    
    if shape_index > shape_count:
        cmds.warning('%s does not have a shape count up to %s' % shape_index)
        
    return shapes[shape_index]

def get_curve_shape(curve, shape_index = 0):
    """
    Get the shape for a curve transform
    
    Args:
        curve (str): The name of a transform above nurbsCurve shapes
        shape_index (int): The index of the shape. 
    """
    if curve.find('.vtx'):
        curve = curve.split('.')[0]
    
    if cmds.nodeType(curve) == 'nurbsCurve':
        
        curve = cmds.listRelatives(curve, p = True)[0]
        
    shapes = core.get_shapes(curve)
    if not shapes:
        return
    
    if not cmds.nodeType(shapes[0]) == 'nurbsCurve':
        return
    
    shape_count = len(shapes)
    
    if shape_index < shape_count:
        return shapes[0]
    
    if shape_index > shape_count:
        cmds.warning('%s does not have a shape count up to %s' % shape_index)
        
    return shapes[shape_index]

def get_surface_shape(surface, shape_index = 0):
    """
    Get the shape for a surface transform
    
    Args:
        surface (str): The name of a transform above nurbsSurface shapes
        shape_index (int): The index of the shape. 
    """
    if surface.find('.vtx'):
        surface = surface.split('.')[0]
    
    if cmds.nodeType(surface) == 'nurbsSurface':
        
        surface = cmds.listRelatives(surface, p = True)[0]
        
    shapes = core.get_shapes(surface)
    if not shapes:
        return
    
    if not cmds.nodeType(shapes[0]) == 'nurbsSurface':
        return
    
    shape_count = len(shapes)
    
    if shape_index < shape_count:
        return shapes[0]
    
    if shape_index > shape_count:
        cmds.warning('%s does not have a shape count up to %s' % shape_index)
        
    return shapes[shape_index]

def get_of_type_in_hierarchy(transform, node_type):
    """
    Get nodes of type in a hierarchy.
    
    Args:
        transform (str): The name of a transform.
        node_type (str): The node type to search for.
        
    Returns:
        list: Nodes that match node_type in the hierarchy below transform.  
        If a shape matches, the transform above the shape will be added.
    """
    relatives = cmds.listRelatives(transform, ad = True, type = node_type, f = True, shapes = False)
    
    
    found = []
    
    for relative in relatives:
        if cmds.objectType(relative, isa = 'shape'):
            parent = cmds.listRelatives(relative, f = True, p = True)[0]
            
            if parent:
                
                if not parent in found:
                    found.append(parent)
                
        if not cmds.objectType(relative, isa = 'shape'):
            found.append(relative)
            
    return found

def get_matching_geo(source_list, target_list):
    """
    Searches for matches to the source list.  Only one geo can match each source.  
    Checkes topology first, then naming.
    Returns a list with [[source, target],[source,target]]
    
    This can be used to match geo in hierarchies that are different.  Not super predictable though.
    """
    
    source_dict = {}
    found_source_dict = {}
    
    for source in source_list:
        
        if not is_a_mesh(source):
            continue
        
        source_dict[source] = []
        
        for target in target_list:
            
            if not is_a_mesh(target):
                continue
            
            if is_mesh_compatible(source, target):
                
                source_dict[source].append(target)
                
    for source in source_dict:
        
        matches = source_dict[source]
        
        for match in matches:
            if source == match:
                found_source_dict[source] = match
                break
            
            source_base = core.get_basename(source, remove_namespace = True)
            match_base = core.get_basename(match, remove_namespace= True)
            
            if source_base == match_base:
                found_source_dict[source] = match
                break
                
    found = []
                
    for source in source_list:
        match = found_source_dict[source]
        
        found.append(source, match)
                
                
#--- edge

def edge_to_vertex(edges):
    """
    Return the vertices that are part of the edges.
    
    Args:
        edges (list): A list of edges (by name).  eg. ['mesh_name.e[0]'] 
    
    Returns:
        list: The names of vertices on an edge. eg. ['mesh_name.vtx[0]']
    
    """
    
    edges = cmds.ls(edges, flatten = True)
    
    verts = []
    
    mesh = edges[0].split('.')
    mesh = mesh[0]
    
    for edge in edges:
        
        info = cmds.polyInfo(edge, edgeToVertex = True)
        info = info[0]
        info = info.split()
        
        vert1 = info[2]
        vert2 = info[3]
        
        if not vert1 in verts:
            verts.append('%s.vtx[%s]' % (mesh, vert1))
            
        if not vert2 in verts:
            verts.append('%s.vtx[%s]' % (mesh, vert2))
    
    return verts

def get_edges_in_list(list_of_things):
    """
    Given a list of name strings, return anything that is an edge
    """
    found = []
    
    for thing in list_of_things:
        if cmds.nodeType(thing) == 'mesh':
            if thing.find('.e[') > 0:
                found.append(thing)
                
    return found 

def edge_to_mesh(edge):
    """
    This will find the mesh that corresponds to the edge
    """
        
    mesh = None
    
    if edge.find('.e[') > -1:
        split_selected = edge.split('.e[')
        if split_selected > 1:
            mesh = split_selected[0]
            
            return mesh    
    
def get_edge_path(edges = []):
    """
    Given a list of edges, return the edge path.
    
    Args:
        edges (list): A list of edges (by name) along a path.  eg. ['node_name.e[0]'] 
    
    Returns:
        list: The names of edges in the edge path.
    """
    
    cmds.select(cl = True)
    cmds.polySelectSp(edges, loop = True )
    
    return cmds.ls(sl = True, l = True)

def get_edge_names_from_indices(mesh, indices):
    """
    Given a list of edge indices and a mesh, this will return a list of edge names. 
    The names are built in a way that cmds.select can select them.
    """
    found = []
    
    for index in indices:
        
        name = '%s.e[%s]' % (mesh, index)
        found.append(name)
    return found

def expand_selected_edge_loop():
    """
    Select edges and then expand the selection on the edge loop.
    """
    edges = get_selected_edges()
    
    found_new_edges = []
    
    for edge in edges:
        
        mesh, edge = edge.split('.')
        
        edge_id = vtool.util.get_last_number(edge)
        
        new_edges = expand_edge_loop(mesh, edge_id)
        
        if new_edges:
            found_new_edges += new_edges
    
    for edge in found_new_edges:
        cmds.select('%s.e[%s]' % (mesh, edge), add = True)
    
    

def expand_edge_loop(mesh, edge_id):
    """
    Expands a edge loop.  Can be great for working with eyes and other circular geometry
    """
    iter_edges = api.IterateEdges(mesh)
    
    connected_faces = iter_edges.get_connected_faces(edge_id)
    connected_edges = iter_edges.get_connected_edges(edge_id)
    
    face_edges = []
    
    for face_id in connected_faces:
        
        iter_faces = api.IteratePolygonFaces(mesh)
        face_edges += iter_faces.get_edges(face_id)
        
    edge_set = set(connected_edges)
    face_edge_set = set(face_edges)
    
    good_edges = edge_set.difference(face_edge_set)
    
    good_edges = list(good_edges)
    
    return good_edges


def multi_expand_loop(mesh, edges, expand_loops):
    """
    This will expand the loop multiple times.  
    This is good for starting from a single edge and expanding it into a section of an edge loop.
    This is good when you want to simplify user input for finding a portion of an edge loop
    Good for areas with circular topology like eyes
    """
    edges = vtool.util.convert_to_sequence(edges)
    
    for _ in range(0, expand_loops):
        
        found_edges = []
        
        for edge_id in edges:
            
            new_edges = expand_edge_loop(mesh, edge_id)
            
            if new_edges:
                found_edges += new_edges
        
        edges += found_edges
        
        filter_dict = {el:0 for el in edges}
        edges = filter_dict.keys()
    
    return edges
        

def edges_to_curve(edges, description = None):
    """
    Given a list of edges create a curve.
    
    Args:
        edges (list): List of edge names, eg ['mesh_name.e[0]']
        description (str): The description to give the new curve. Name = 'curve_(description)'
        
    Returns:
        str: The name of the curve.
    """
    
    if not description:
        description = get_mesh_from_edge(edges[0])
        
    cmds.select(edges)

    curve =  cmds.polyToCurve(form = 2, degree = 3 )[0]
    
    curve = cmds.rename(curve, core.inc_name('curve_%s' % description))
    
    return curve

def get_mesh_from_edge(edge):
    """
    Given an edge name, find the corresponding mesh
    """
    return get_thing_from_component(edge, 'e')
    

#--- vertex

def is_a_vertex(node):
    """
    Checks if the node is a vertex
    """
    if cmds.objExists(node) and node.find('.vtx[') > -1:
        return True
    
    return False

def get_vertices(mesh):
    """
    Get the vertices of a mesh.
    
    Returns
        list
    """
    mesh = get_mesh_shape(mesh)
    
    meshes = core.get_shapes(mesh, 'mesh', no_intermediate=True)
    
    found = []
    
    for mesh in meshes:
        
        verts = cmds.ls('%s.vtx[*]' % mesh, flatten = True)
        
        if verts:
            found += verts
    
    return found

def get_vertex_indices(list_of_vertex_names):
    """
    Given a list of vertex names (that are selectable using cmds.select) 
    return the list of vert index numbers.
    Useful when iterating quickly or working with api that takes an id instead of a name.
    """
    list_of_vertex_names = vtool.util.convert_to_sequence(list_of_vertex_names)
    
    vertex_indices = []
    
    for vertex in list_of_vertex_names:
        
        index = int(vertex[vertex.find("[")+1:vertex.find("]")]) 
        
        vertex_indices.append(index)
        
    return vertex_indices

def get_vertex_names_from_indices(mesh, indices):
    """
    Given a list of vertex indices and a mesh, this will return a list of vertex names. 
    The names are built in a way that cmds.select can select them.
    """
    found = []
    
    for index in indices:
        
        name = '%s.vtx[%s]' % (mesh, index)
        found.append(name)
    return found

def get_mesh_from_vertex(vertex):
    """
    Given a vertex name return the corresponding mesh
    """
    return get_thing_from_component(vertex, 'vtx')

def get_vertex_shells(mesh):
    """
    Given a mesh that has multiple disconnected vertex islands, this will return the vertex islands
    format is
    [[vertex1,vertex2,vertex3],[vertex4,vertex5,vertex6]]
    This can be really useful in tandem with average_vertex_weights on things like buttons that have been combined into one mesh
    """
    result =  api.get_vertex_islands(mesh)
    
    found = []
    
    for r in result:
        found.append( get_vertex_names_from_indices(mesh, r) )
    
    return found

#--- face

def get_faces(mesh):
    """
    Get the faces of a mesh.
    
    Returns:
        list
    """
    mesh = get_mesh_shape(mesh)
    
    meshes = core.get_shapes(mesh, 'mesh', no_intermediate=True)
    
    found = []
    
    for mesh in meshes:
        
        faces = cmds.ls('%s.f[*]' % mesh, flatten = True)
        
        if faces:
            found += faces
    
    return found

def get_face_indices(list_of_face_names):
    """
    Given a list of face names (that are selectable using cmds.select) 
    return the list of face index numbers.
    Useful when iterating quickly or working with api that takes an id instead of a name.
    """
    list_of_face_names = vtool.util.convert_to_sequence(list_of_face_names)
    
    indices = []
    
    for face in list_of_face_names:
        
        index = int(face[face.find("[")+1:face.find("]")]) 
        
        indices.append(index)
        
    return indices

def get_face_names_from_indices(mesh, indices):
    """
    Given a list of face indices and a mesh, this will return a list of face names. 
    The names are built in a way that cmds.select can select them.
    """
    found = []
    
    for index in indices:
        
        name = '%s.f[%s]' % (mesh, index)
        found.append(name)
    return found

def get_mesh_from_face(face):
    """
    Given a  face name return the corresponding mesh
    """
    
    return get_thing_from_component(face, 'f')
    

def face_to_vertex(faces):
    """
    Gets the vertices in a list of faces
    can pass in a single face or a list of faces
    """
    faces = cmds.ls(faces, flatten = True)
    
    verts = []
    
    mesh = faces[0].split('.')
    mesh = mesh[0]
    
    for face in faces:
        
        info = cmds.polyInfo(face, faceToVertex = True)
        info = info[0]
        info = info.split()
        
        sub_verts = info[2:]
        
        for sub_vert in sub_verts:
            if not sub_vert in verts:
                verts.append('%s.vtx[%s]' % (mesh, sub_vert))
                
    return verts

def get_triangles(mesh):
    """
    Get the triangles of a mesh.
    
    Returns:
        list
    """
    mesh = get_mesh_shape(mesh)
    
    meshes = core.get_shapes(mesh, 'mesh', no_intermediate=True)
    
    found = []
    
    for mesh in meshes:
        mesh_fn = api.MeshFunction(mesh)
        
        triangles = mesh_fn.get_triangle_ids()
        
        faces = convert_indices_to_mesh_faces(triangles, mesh)
        
        if faces:
            found += faces
    
    return found

def get_non_triangle_non_quad(mesh):
    """
    Get faces that are neither quads or triangles.
    
    Returns:
        list
    """
    mesh = get_mesh_shape(mesh)
    
    meshes = core.get_shapes(mesh, 'mesh')
    
    found = []
    
    for mesh in meshes:
        mesh_fn = api.MeshFunction(mesh)
        
        ids = mesh_fn.get_non_tri_quad_ids()
        
        faces = convert_indices_to_mesh_faces(ids, mesh)
        
        if faces:
            found += faces
    
    return found

def get_face_center(mesh, face_id):
    """
    Get the center position of a face.
    
    Args:
        mesh (str): The name of a mesh.
        face_id: The index of a face component.
        
    Returns:
        list: eg [0,0,0] The vector of the center of the face.
    """
    mesh = get_mesh_shape(mesh)

    face_iter = api.IteratePolygonFaces(mesh)
    
    center = face_iter.get_center(face_id)
    
    return center
    
def get_face_centers(mesh):
    """
    Returns: a list of face center positions.
    
    Args:
        mesh (str): The name of a mesh.
        
    Returns:
        list: A list of lists.  eg. [[0,0,0],[0,0,0]]  Each sub list is the face center vector.
    """
    mesh = get_mesh_shape(mesh)
    
    face_iter = api.IteratePolygonFaces(mesh)
    
    return face_iter.get_face_center_vectors()

def faces_to_new_mesh(faces, name = 'new_mesh_from_faces'):
    """
    Given a list of a faces, this will break off a duplicate of the faces.
    Usefull when copying weights onto simple geo before copying into back onto complex geo.
    Might also be useful for create controls from meshes sections
    Also for creating proxy meshes
    """
    faces = cmds.ls(faces, flatten = True)
    
    indices = get_face_indices(faces)
    
    mesh = get_mesh_from_face(faces[0])
    
    new_mesh = cmds.duplicate(mesh, n = name)[0]
    
    new_face_indices = range(len(cmds.ls('%s.f[*]' % new_mesh, flatten = True)))
    
    for index in indices:
        new_face_indices.remove(index)
    
    faces = get_face_names_from_indices(new_mesh, new_face_indices)
    cmds.delete(faces)
    
    if cmds.objExists(new_mesh):
        return new_mesh
    
def get_render_stats(node_name):
    """
    Get the render stat values from a node
    
    Args
        node_name (str)
    
    Returns:
        list
    """
    render_stats = ['castsShadows',
                    'receiveShadows',
                    'holdOut',
                    'motionBlur',
                    'primaryVisibility',
                    'smoothShading',
                    'visibleInReflections',
                    'visibleInRefractions',
                    'doubleSided',
                    'opposite',
                    ]
    
    render_list = []
    
    for stat in render_stats:
        attr = '%s.%s' % (node_name, stat)
        
        if cmds.objExists(attr):
            value = cmds.getAttr(attr)
            
            render_list.append( [stat, value])
    
    return render_list

def get_intersection_on_mesh(mesh, ray_source_vector, ray_direction_vector ):
    """
    Given a ray vector with source and direction, find the closest intersection on a mesh.
    
    Args:
        mesh (str): The name of the mesh to intersect with.
        ray_source_vector (list): eg. [0,0,0], the source of the ray as a vector.
        ray_directrion_vector (list): eg [0,0,0], The end point of the ray that starts at ray_source_vector.
        
    Returns:
        list: eg [0,0,0] the place where the ray intersects with the mesh.
        
    """
    mesh_fn = api.MeshFunction(mesh)
    
    intersection = mesh_fn.get_closest_intersection(ray_source_vector, ray_direction_vector)
    
    return intersection
    
def get_closest_uv_on_mesh(mesh, three_value_list):
    """
    Find the closest uv on a mesh given a vector.
    
    Args:
        mesh (str): The name of the mesh with uvs.
        three_value_list (list): eg. [0,0,0], the position vector from which to find the closest uv.
        
    Returns:
        uv: The uv of that is closest to three_value_list
    """
    
    mesh = api.MeshFunction(mesh)
    found = mesh.get_uv_at_point(three_value_list)
    
    return found

def get_uv_on_mesh_at_curve_base(mesh, curve):
    """
    Looks for the closest uv on mesh at the base of the curve
    """
    
    cvs = cmds.ls('%s.cv[*]' % curve, flatten = True)
    
    cv = cvs[0]
    
    cv_position = cmds.xform(cv, q = True, t = True, ws = True)
    closest_position = get_closest_position_on_mesh(mesh, cv_position)
    
    u,v = get_closest_uv_on_mesh(mesh, closest_position)
    
    return u,v

def get_closest_uv_on_mesh_at_curve(mesh, curve, samples = 50):
    """
    Looks at the curve and tries to find the closest uv on mesh where the curve intersects or has its nearest point
    """
    temp_curve = cmds.duplicate(curve)[0]
    rebuild_curve(temp_curve, samples, degree = 1)
    
    cvs = cmds.ls('%s.cv[*]' % temp_curve, flatten = True)
    
    closest_distance = None
    closest_position = None
    out_closest_position = None
    last_cv_position = None
    
    for cv in cvs:
        
        cv_position = cmds.pointPosition(cv, w = True)
        closest_position = get_closest_position_on_mesh(mesh, cv_position)
        distance = vtool.util_math.get_distance_before_sqrt(cv_position, closest_position)
        
        if closest_distance and last_cv_position:
            if closest_distance < distance:
                out_closest_position = last_cv_position
                break
                
        
        if not closest_distance:
            
            closest_distance = distance
            out_closest_position = cv_position
        
        if distance < closest_distance:
            
            closest_distance = distance
            out_closest_position = cv_position
            
        if distance < 0.0001:
            
            closest_distance = distance
            out_closest_position = cv_position
            break
        
        last_cv_position = cv_position
    
    cmds.delete(temp_curve)
    
    u,v = get_closest_uv_on_mesh(mesh, out_closest_position)
    
    return u,v


    
def get_axis_intersect_on_mesh(mesh, transform, rotate_axis = 'Z', opposite_axis = 'X', accuracy = 100, angle_range = 180):
    """
    This will find the closest intersection on a mesh by rotating incrementally on a rotate axis.
    
    Args:
        mesh (str): The name of a mesh.
        transform (str): The name of a transform.
        rotate_axis (str): 'X', 'Y', 'Z' axis of the transform to rotate.
        opposite_axis (str): 'X', 'Y', 'Z' The axis of the transform to point at the mesh while rotating. Should not be the same axis as rotate axis.
        accuracy (int): The number of increments in the angle range.
        angle_range (float): How far to rotate along the rotate_axis.
    
    
    Returns:
        list: eg. [0,0,0] The vector of the clostest intersection
    """
    closest = None
    found = None
    
    dup = cmds.duplicate(transform, po = True)[0]
    
    space1 = cmds.xform(dup, q = True, t = True)
    
    inc_value = (angle_range*1.0)/accuracy
        
    if rotate_axis == 'X':
        rotate_value = [inc_value,0,0]
    if rotate_axis == 'Y':
        rotate_value = [0,inc_value,0]
    if rotate_axis == 'Z':
        rotate_value = [0,0,inc_value]

    if opposite_axis == 'X':
        axis_vector = [1,0,0]
    if opposite_axis == 'Y':
        axis_vector = [0,1,0]
    if opposite_axis == 'Z':
        axis_vector = [0,0,1]
                
    for inc in range(0, accuracy+1):
        
        space2 = space.get_axis_vector(dup, axis_vector)
        
        cmds.rotate(rotate_value[0], rotate_value[1], rotate_value[2], dup, r = True)
        
        mesh_api = api.MeshFunction(mesh)    
        intersect = mesh_api.get_closest_intersection(space1, space2)
        
        distance = vtool.util.get_distance(space1, list(intersect))
        
        if closest == None:
            closest = distance
            found = intersect
        
        if distance < closest:
            closest = distance
            found = intersect
        
    cmds.delete(dup)
            
    return found
    
def get_closest_parameter_on_curve(curve, three_value_list):
    """
    Find the closest parameter value on the curve given a vector.
    
    Args:
        curve (str): The name of a curve.
        three_value_list (list): eg. [0,0,0] The vector from which to search for closest parameter
        
    Returns:
        float: The closest parameter.
    """
    curve_shapes = core.get_shapes(curve)
    
    if curve_shapes:
        curve = curve_shapes[0]
    
    curve = api.NurbsCurveFunction(curve)
        
    newPoint = curve.get_closest_position( three_value_list )
    
    return curve.get_parameter_at_position(newPoint)

def get_closest_parameter_on_surface(surface, vector):
    """
    Find the closest parameter value on the surface given a vector.
    
    Args:
        surface (str): The name of the surface.
        vector (list): eg [0,0,0] The position from which to check for closest parameter on surface. 
    
    Returns:
        list: [0,0] The parameter coordinates of the closest point on the surface.
    """
    shapes = core.get_shapes(surface)
    
    if shapes:
        surface = shapes[0]
    
    surface = api.NurbsSurfaceFunction(surface)
        
    uv = surface.get_closest_parameter(vector)
    
    uv = list(uv)
    
    if uv[0] == 0:
        uv[0] = 0.001
    
    if uv[1] == 0:
        uv[1] = 0.001
    
    return uv

def get_closest_position_on_surface_at_parameter(surface, param_u, param_v):
    """
    Given a surface and a u and v parameter return a position
    """
    shapes = core.get_shapes(surface)
    
    if shapes:
        surface = shapes[0]
        
    surface = api.NurbsSurfaceFunction(surface)
    
    return surface.get_position_from_parameter(param_u, param_v)

def get_closest_position_on_surface(surface, vector):
    """
    Given a surface and a position (3 value list), return the a 3 value list that represents the closest position on the surface
    """
    shapes = core.get_shapes(surface)
    
    if shapes:
        surface = shapes[0]
        
    surface = api.NurbsSurfaceFunction(surface)
    
    param = surface.get_closest_parameter(vector)
    return surface.get_position_from_parameter(*param)
    

def get_closest_normal_on_surface(surface, vector):
    """
    Given a surface and a position (3 value list), return the a 3 value list that represents the closest normal on the surface
    Can be useful when orienting controls cvs or other things to a surface
    """
    shapes = core.get_shapes(surface)
    
    if shapes:
        surface = shapes[0]
    
    surface = api.NurbsSurfaceFunction(surface)
    return surface.get_closest_normal(vector)
    

def get_closest_position_on_mesh(mesh, three_value_list):
    """
    Get the closes position on a mesh from the given point.
    
    Args:
        mesh (str): The name of a mesh.
        three_value_list (list): The position to search from.
    
    Returns:
        list: The value list, the position on the mesh that's closest.
    """
    mesh_fn = api.MeshFunction(mesh)
    
    position = mesh_fn.get_closest_position(three_value_list)
    
    return position

def get_closest_normal_on_mesh(mesh, three_value_list):
    """
    Given a mesh and a position (3 value list), return the a 3 value list that represents the closest normal on the mesh
    Can be useful when orienting controls cvs or other things to a surface
    """
    mesh_fn = api.MeshFunction(mesh)
    
    normal = mesh_fn.get_closest_normal(three_value_list)
    
    return normal

def get_closest_position_on_curve(curve, three_value_list):
    """
    Given a vector, find the closest position on a curve.
    
    Args:
        curve (str): The name of a curve.
        three_value_list (list): eg [0,0,0] a vector find the closest position from.
        
    Returns:
        list: eg [0,0,0] The closest position on the curve as vector.
    """
    
    curve_shapes = core.get_shapes(curve)
    
    if curve_shapes:
        curve = curve_shapes[0]
    
    curve = api.NurbsCurveFunction(curve)
        
    return curve.get_closest_position( three_value_list )

def get_parameter_from_curve_length(curve, length_value):
    
    """
    Find the parameter value given the length section of a curve.
    
    Args:
        curve (str): The name of a curve.
        length_value (float): The length along a curve.
        
    Returns:
        float: The parameter value at the length.
    """
    
    curve_shapes = core.get_shapes(curve)
    
    if curve_shapes:
        curve = curve_shapes[0]
        
    curve = api.NurbsCurveFunction(curve)
    
    return curve.get_parameter_at_length(length_value)

def get_curve_length_from_parameter(curve, parameter_value):
    """
    Given a parameter return the curve length to that parameter.
    
    """
    
    arc_node = cmds.arcLengthDimension( '%s.u[%s]' % (curve, parameter_value))
    
    length = cmds.getAttr('%s.arcLength' % arc_node)
    
    parent = cmds.listRelatives(arc_node, p = True)
    if parent:
        cmds.delete(parent[0])
    
    return length

def get_point_from_curve_parameter(curve, parameter):
    """
    Find a position on a curve by giving a parameter value.
    
    Args:
        curve (str): The name of a curve.
        parameter (float): The parameter value on a curve.
        
    Returns: 
        list: [0,0,0] the vector found at the parameter on the curve.
    """
    return cmds.pointOnCurve(curve, pr = parameter, ch = False)

def get_curve_position_from_parameter(curve, parameter):
    """
    Find a position on a curve by giving a parameter value.
    
    Args:
        curve (str): The name of a curve.
        parameter (float): The parameter value on a curve.
        
    Returns: 
        list: [0,0,0] the vector found at the parameter on the curve.
    """
    position = get_point_from_curve_parameter(curve, parameter)
    
    return position

def get_point_from_surface_parameter(surface, u_value, v_value):
    """
    Given a u and v value find the closest position on the surface.
    """
    surface_fn = api.NurbsSurfaceFunction(surface)
    position = surface_fn.get_position_from_parameter(u_value, v_value)
    
    return position

def get_occluded_faces(mesh, within_distance = 1, skip_with_area_greater_than = -1):
    """
    Find all the faces occluded by other faces. Good for finding internal geometry.
    """
    iter_face = api.IteratePolygonFaces(mesh)
    mesh_fn = api.MeshFunction(mesh)
    
    occluded_faces = []
    
    def get_face_hit_id(mesh_fn, source_vector, normal_vector):
        
        source_normal = vtool.util.vector_add(source_vector, normal_vector)
        face_id = mesh_fn.get_closest_intersection_face(source_normal, source_vector)
        
        return face_id
    
    while not iter_face.is_done():
    
        index = iter_face.index()
        
        skip_face = False
        
        if skip_with_area_greater_than > 0:
            area = iter_face.get_area()
            if area > skip_with_area_greater_than:
                skip_face = True
        
        if skip_face:
            iter_face.next()
            continue
        
        center = iter_face.get_center()
        
        normal = iter_face.get_normal()
        normal = vtool.util.vector_multiply(normal, within_distance)
        
        tangent = [0,0,0]
        
        found_space = False
        
        for inc in range(0, 5):
            
            if inc == 0:
                
                face_id = get_face_hit_id(mesh_fn, center, normal)
                
            
            if inc == 1:
                if normal[0] < 0.000001 and normal[0] > -0.000001 and normal[2] < 0.000001 and normal[2] > -0.000001:
                    tangent = [1,.1,0]
                else:
                    tangent = vtool.util.vector_cross(normal, [0,1,0])
                    tangent = vtool.util.get_inbetween_vector(tangent, normal, .1)
                
                tangent = vtool.util.vector_multiply(tangent, within_distance)
                
                face_id = get_face_hit_id(mesh_fn, center, tangent)
            
            if inc == 2:
                
                if normal[0] < 0.000001 and normal[0] > -0.000001 and normal[2] < 0.000001 and normal[2] > -0.000001:
                    neg_tangent = [-1,.1,0]
                    
                else:
                    
                    neg_tangent = vtool.util.vector_cross(normal, [0,-1,0])
                    neg_tangent = vtool.util.get_inbetween_vector(neg_tangent, normal, .1)
                
                neg_tangent = vtool.util.vector_multiply(neg_tangent, within_distance)
                
                face_id = get_face_hit_id(mesh_fn, center, neg_tangent)
            
            if inc == 3:
                if normal[0] < 0.000001 and normal[0] > -0.000001 and normal[2] < 0.000001 and normal[2] > -0.000001:
                    binormal = [0,.1,1]
                else:
                    
                    binormal = vtool.util.vector_cross(normal, tangent)
                    binormal = vtool.util.get_inbetween_vector(binormal, normal, .1)
                    
                binormal = vtool.util.vector_multiply(binormal, within_distance)
                    
                face_id = get_face_hit_id(mesh_fn, center, binormal)
                
            if inc == 4:
                if normal[0] < 0.000001 and normal[0] > -0.000001 and normal[2] < 0.000001 and normal[2] > -0.000001:
                    neg_binormal = [0,.1,-1]
                else:
                    
                    neg_binormal = vtool.util.vector_cross(normal, neg_tangent)
                    neg_binormal = vtool.util.get_inbetween_vector(neg_binormal, normal, .1)
                    
                neg_binormal = vtool.util.vector_multiply(neg_binormal, within_distance)
                    
                face_id = get_face_hit_id(mesh_fn, center, neg_binormal)
            
            
            
            if face_id == index:
                found_space = True
                break
        
        if found_space:
            iter_face.next()
            continue
        
        face = '%s.f[%s]' % (mesh, iter_face.index())
        occluded_faces.append(face)
        
        iter_face.next()
        
    return occluded_faces

def get_vertex_normal(vert_name):
    """
    Get the position of a normal of a vertex.
    
    Args:
        vert_name (str): The name of a vertex.
    
    Returns: 
        list: eg [0,0,0] The vector where the normal points.
    """
    normal = cmds.polyNormalPerVertex(vert_name, q = True, normalXYZ = True)
    normal = normal[:3]
    return vtool.util.Vector(normal)

def get_y_intersection(curve, vector):
    """
    Given a vector in space, find out the closest intersection on the y axis to the curve. This is usefull for eye blink setups.
    
    Args:
        curve (str): The name of a curve that could represent the btm eyelid.
        vector (vector list): A list that looks like [0,0,0] that could represent a position on the top eyelid.
        
    Returns:
        float: The parameter position on the curve.
    """
    
    duplicate_curve = cmds.duplicate(curve)
    curve_line = cmds.curve( p=[(vector[0], vector[1]-100000, vector[2]), 
                                (vector[0],vector[1]+100000, vector[2]) ], d = 1 )
    
    parameter = cmds.curveIntersect(duplicate_curve, curve_line, ud = True, d = [0, 0, 1])
    
    if parameter:
        parameter = parameter.split()
        
        parameter = float(parameter[0])
        
    if not parameter:
        parameter =  get_closest_parameter_on_curve(curve, vector)
        
    cmds.delete(duplicate_curve, curve_line)
    
    return parameter

def check_render_stats_are_default(node_name):
    """
    check for nodes with non default render stats
    
    returns:
        list:
    """
    
    stats = get_render_stats(node_name)
    
    for inc in range(0, len(stats)):
        
        stat = stats[inc][0]
        value = stats[inc][1]
        
        if stat == 'castsShadows':
            if not value == RENDER_DEFAULT_CAST_SHADOWS:
                return False
        if stat == 'receiveShadows':
            if not value == RENDER_DEFAULT_RECEIVE_SHADOWS:
                return False
        if stat == 'holdOut':
            if not value == RENDER_DEFAULT_HOLD_OUT:
                return False
        if stat == 'motionBlur':
            if not value == RENDER_DEFAULT_MOTION_BLUR:
                return False
        if stat == 'primaryVisibility':
            if not value == RENDER_DEFAULT_PRIMARY_VISIBILITY:
                return False
        if stat == 'smoothShading':
            if not value == RENDER_DEFAULT_SMOOTH_SHADING:
                return False   
        if stat == 'visibleInReflections':
            if not value == RENDER_DEFAULT_VISIBLE_IN_REFLECTIONS:
                return False    
        if stat == 'visibleInRefractions':
            if not value == RENDER_DEFAULT_VISIBLE_IN_REFRACTIONS:
                return False
        if stat == 'doubleSided':
            if not value == RENDER_DEFAULT_DOUBLE_SIDED:
                return False
        if stat == 'opposite':
            if not value == RENDER_DEFAULT_OPPOSITE:
                return False
            
    return True


def set_default_render_stats(node_name):
    """
    check for nodes with non default render stats
    
    returns:
        list:
    """
    
    stats = get_render_stats(node_name)
    
    for inc in range(0, len(stats)):
        
        stat = stats[inc][0]
        attr = ('%s.%s' % (node_name, stat))
        
        if stat == 'castsShadows':
            cmds.setAttr(attr, RENDER_DEFAULT_CAST_SHADOWS)
            
        if stat == 'receiveShadows':
            cmds.setAttr(attr, RENDER_DEFAULT_RECEIVE_SHADOWS)
            
        if stat == 'holdOut':
            cmds.setAttr(attr, RENDER_DEFAULT_HOLD_OUT)
            
        if stat == 'motionBlur':
            cmds.setAttr(attr, RENDER_DEFAULT_MOTION_BLUR)
            
        if stat == 'primaryVisibility':
            cmds.setAttr(attr, RENDER_DEFAULT_PRIMARY_VISIBILITY)
            
        if stat == 'smoothShading':
            cmds.setAttr(attr, RENDER_DEFAULT_SMOOTH_SHADING)
            
        if stat == 'visibleInReflections':
            cmds.setAttr(attr, RENDER_DEFAULT_VISIBLE_IN_REFLECTIONS)
                
        if stat == 'visibleInRefractions':
            cmds.setAttr(attr, RENDER_DEFAULT_VISIBLE_IN_REFRACTIONS)
            
        if stat == 'doubleSided':
            cmds.setAttr(attr, RENDER_DEFAULT_DOUBLE_SIDED)
            
        if stat == 'opposite':
            cmds.setAttr(attr, RENDER_DEFAULT_OPPOSITE)
            

def set_render_stats_double_sided_default(node_name):
    """
    Set renders stats on a node to be double sided on and opposite off.
    """
    stats = get_render_stats(node_name)
    
    for inc in range(0, len(stats)):
        
        stat = stats[inc][0]
        attr = ('%s.%s' % (node_name, stat))
        
        if stat == 'doubleSided':
            cmds.setAttr(attr, RENDER_DEFAULT_DOUBLE_SIDED)
            
        if stat == 'opposite':
            cmds.setAttr(attr, RENDER_DEFAULT_OPPOSITE)

def create_curve_from_mesh_border(mesh, offset = 0.1, name = None):
    """
    Create a curve from the border of a mesh.  Good for creating controls on feathers.
    """
    cmds.select(cl = True)
    
    work_mesh = cmds.duplicate(mesh)[0]
    
    
    
    cmds.polySelect(work_mesh, eb = True)
    
    cmds.polyMoveEdge(ch = False, random = 0, localCenter = 0, lty = offset)
    
    orig_curve = cmds.polyToCurve( form = 2, degree = 1)[0]
    
    curve = cmds.rename(orig_curve, core.inc_name('curve_%s' % mesh))
    
    if name:
        curve = cmds.rename(curve, core.inc_name(name))
        
    cmds.delete(work_mesh)
        
    return curve

def create_curve_from_edge_loop(edge, offset = 0.1, name = None):
    """
    Create a curve from the border of a mesh.  Good for creating controls on feathers.
    """
    cmds.select(cl = True)
    
    mesh = edge_to_mesh(edge)
    work_mesh = cmds.duplicate(mesh)[0]
    
    work_edge = edge.replace(mesh, work_mesh)
    cmds.select(cl = True)
    cmds.select(work_edge)
    mel.eval('SelectEdgeLoopSp')
    #cmds.polySelect(edge, elb = True)
    
    cmds.polyMoveEdge(ch = False, random = 0, localCenter = 0, ltz = offset)
    
    orig_curve = cmds.polyToCurve( form = 2, degree = 1)[0]
    
    curve = cmds.rename(orig_curve, core.inc_name('curve_form_edge_1'))
    
    if name:
        curve = cmds.rename(curve, core.inc_name(name))
        
    cmds.delete(work_mesh)
        
    return curve
    
 
def create_two_transforms_curve(transform1, transform2, name = ''):
    """
    Create a curve between two transforms.
    """
    if not name:
        name = '%s_to_%s_curve' % (transform1, transform2)
    
    pos1 = cmds.xform(transform1, q = True, ws = True, t = True)
    pos2 = cmds.xform(transform2, q = True, ws = True, t = True)
    
    curve = cmds.curve(d = 1, p = [pos1,pos2], name = name)
    
    return curve

def create_two_transforms_mesh_strip(transform1, transform2, offset_axis = 'X', u_spans = 10, v_spans = 3):
    """
    Create a mesh between two transforms.  Not that useful.
    """
    curve = create_two_transforms_curve(transform1, transform2)
    
    if type(offset_axis) == type(str):
        offset_axis.upper()
    
    if offset_axis == 'X':
        
        axis_vector = [1,0,0]
    if offset_axis == 'Y':
        axis_vector = [0,1,0]
    if offset_axis == 'Z':
        axis_vector = [0,0,1]
    
    dup1 = cmds.duplicate(curve)
    cmds.xform(dup1, os = True, t = [axis_vector[0]*-1, axis_vector[1]*-1, axis_vector[2]*-1])
    
    dup2 = cmds.duplicate(curve)
    cmds.xform(dup2, os = True, t = axis_vector)
    
    
    
    loft = cmds.loft(dup1, dup2, ch = True, u = True, c = 0, ar = 1, d = 3, ss = 10, rn = 0, po = 1, rsn = True)
    
    surface = loft[0]
    
    input_value = attr.get_attribute_input('%s.inMesh' % surface, node_only=True)
    
    if input_value:
        cmds.setAttr('%s.format' % input_value, 2)
        cmds.setAttr('%s.uType' % input_value, 1)
        cmds.setAttr('%s.vType' % input_value, 1)
        cmds.setAttr('%s.uNumber' % input_value, u_spans)
        cmds.setAttr('%s.vNumber' % input_value, v_spans)
        cmds.setAttr('%s.polygonType' % input_value, 1)
        cmds.setAttr('%s.chordHeightRatio' % input_value, 0.1)
        cmds.setAttr('%s.useChordHeight' % input_value, False)
        cmds.setAttr('%s.chordHeight' % input_value, .2)
        
        
        cmds.delete(surface, ch = True)
    
    new_name = cmds.rename(surface, '%s_to_%s_mesh' % (transform1, transform2))
    
    cmds.delete(dup1, dup2, curve)
    
    pos = cmds.xform(transform1, q = True, ws = True, t = True)
    
    cmds.xform(new_name, rp = pos, sp = pos)
    
    return new_name
    
def create_mesh_from_bounding_box(min_vector, max_vector, name):
    """
    Given a min and max vector create a mesh cube.
    """
    cube = cmds.polyCube(ch = 0)[0]
    cmds.rename(cube, name)
            
    cmds.move(min_vector[0], min_vector[1], min_vector[2], '%s.vtx[0]' % cube , ws = True)
    cmds.move(min_vector[0], min_vector[1], max_vector[2], '%s.vtx[1]' % cube , ws = True )
    cmds.move(min_vector[0], max_vector[1], min_vector[2], '%s.vtx[2]' % cube , ws = True)
    cmds.move(min_vector[0], max_vector[1], max_vector[2], '%s.vtx[3]' % cube , ws = True)
    cmds.move(max_vector[0], max_vector[1], min_vector[2], '%s.vtx[4]' % cube , ws = True)
    cmds.move(max_vector[0], max_vector[1], max_vector[2], '%s.vtx[5]' % cube , ws = True)
    cmds.move(max_vector[0], min_vector[1], min_vector[2], '%s.vtx[6]' % cube , ws = True)
    cmds.move(max_vector[0], min_vector[1], max_vector[2], '%s.vtx[7]' % cube , ws = True)
    
    return cube

def create_shape_from_shape(shape, name = 'new_shape'):
    """
    Duplication in maya can get slow in reference files. 
    This will create a shape and match it to the given shape without using Maya's duplicate command.
    
    Args:
        shape (str): The name of a shape to match to.
        name (str): The name of the new shape.
    
    Returns:
        The name of the transform above the new shape.
    """
    
    if cmds.nodeType(shape) == 'transform':
        shapes = core.get_shapes(shape)
        if shapes:
            shape = shapes[0]
    
    parent = cmds.listRelatives(shape, p = True, f = True)
    
    transform = cmds.group(em = True)
    transform = cmds.ls(transform, l = True)[0]
    
    api.create_mesh_from_mesh(shape, transform)
    mesh = transform
    
    core.add_to_isolate_select([mesh])
    
    mesh = cmds.rename(mesh, core.inc_name(name))
    shapes = core.get_shapes(mesh, 'mesh')
    
    if shapes:
        cmds.rename(shapes[0], mesh + 'Shape')
    
    if parent:
        space.MatchSpace(parent[0], mesh).translation_rotation()
        
    return mesh
    

def create_texture_reference_object(mesh):
    """
    Good for working with Yeti
    """
    shape = get_mesh_shape(mesh, 0)
    
    name = core.get_basename(mesh, remove_namespace = True)
    
    new_mesh = create_shape_from_shape(shape, '%s_reference' % name)
    
    shapes = core.get_shapes(new_mesh, 'mesh')
    
    cmds.connectAttr('%s.message' % shapes[0], '%s.referenceObject' % mesh)
    
    cmds.setAttr( '%s.template' % shapes[0],  True )
    return new_mesh

def create_joint_u_strip_on_surface(surface, u_count, description, u_offset = 0, attach = True):
    """
    Create joints that go along the u direction of a surface.
    """
    u_percent = 0
    
    u_joints =[]
    
    if u_count:
        u_segment = 1.00/(u_count)
    
    if u_count:
        for inc in range(0, u_count+1):
                        
            follicle = create_surface_follicle(surface, description, uv = [u_percent, u_offset])
            cmds.select(cl = True)
            joint = cmds.joint(n = core.inc_name('joint_%s' % description) )
            
            space.MatchSpace(follicle, joint).translation()
            cmds.parent(joint, follicle)
            cmds.makeIdentity(apply = True, jo = True)
            
            if not attach:
                cmds.parent(joint, w = True)
                cmds.delete(follicle)
            
            u_joints.append(joint)
            
            u_percent += u_segment
            
    return u_joints

def create_joint_v_strip_on_surface(surface, v_count, description, v_offset = 0, attach = True):
    """
    Create joints that go along the v direction of a surface.
    """
    v_percent = 0
    
    v_joints =[]

    if v_count:
        v_segment = 1.00/(v_count)

    if v_count:
        for inc in range(0, v_count+1):
            
            follicle = create_surface_follicle(surface, description, uv = [v_offset, v_percent])
            cmds.select(cl = True)
            joint = cmds.joint(n = core.inc_name('joint_%s' % description) )
            
            space.MatchSpace(follicle, joint).translation()
            cmds.parent(joint, follicle)
            space.zero_out_transform_channels(joint)
            #space.MatchSpace(follicle, joint).translation_rotation()
            cmds.makeIdentity(apply = True, jo = True)
            
            if not attach:
                cmds.parent(joint, w = True)
                cmds.delete(follicle)
            
            v_joints.append(joint)
            
            v_percent += v_segment

    
    return v_joints

def create_locators_on_curve(curve, count, description, attach = True):
    """
    Create locators on curve that do not aim at child.
    
    Args:
        curve (str): The name of a curve.
        count (int): The number of joints to create.
        description (str): The description to give the joints.
        attach (bool): Wether to attach the joints to the curve.
        create_controls (bool): Wether to create controls on the joints.
        
    Returns:
        list: [ joints, group, control_group ] joints is a list of joinst, group is the main group for the joints, control_group is the main group above the controls. 
        If create_controls = False then control_group = None
        
    """
    
    cmds.select(cl = True)
    
    total_length = cmds.arclen(curve)
    
    part_length = total_length/(count-1)
    current_length = 0
    
    locators = []
    
    cmds.select(cl = True)
    
    percent = 0
    
    segment = 1.00/count
    
    for inc in range(0, count):
        
        param = get_parameter_from_curve_length(curve, current_length)
        
        position = get_point_from_curve_parameter(curve, param)
        if attach:
            cmds.select(cl = True)
            
        locator = cmds.spaceLocator(n = core.inc_name('locator_%s' % description) )
        
        cmds.xform(locator, ws = True, t = position)
        
        cmds.addAttr(locator, ln = 'param', at = 'double', dv = param)
        
        if attach:
            attach_to_curve( locator, curve, parameter = param )
        
        current_length += part_length
                 
        locators.append(locator)
    
        percent += segment
    
    return locators
@core.undo_chunk
def create_joints_on_curve(curve, joint_count, description, attach = True):
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
    
    cmds.select(cl = True)
    
    total_length = cmds.arclen(curve)
    
    part_length = total_length/(joint_count-1)
    current_length = 0
    
    joints = []
    
    cmds.select(cl = True)
    
    percent = 0
    
    segment = 1.00/joint_count
    
    for inc in range(0, joint_count):
        
        param = get_parameter_from_curve_length(curve, current_length)
        
        position = get_point_from_curve_parameter(curve, param)
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
            attach_to_curve( joint, curve, parameter = param )
        
        current_length += part_length
                 
        joints.append(joint)
    
        percent += segment
    
    return joints

def create_joints_on_cvs(curve, parented = True):
    """
    Given a curve, create a joint at each cv.  Joints are parented under the last joint created at the previous cv.
    """
    
    cvs = cmds.ls('%s.cv[*]' % curve, flatten = True)
    
    cmds.select(cl = True)
    
    joints = []
    
    inc = 0
    last_joint = None
    for cv in cvs:
        
        position = cmds.pointPosition(cv)
        
        if not parented:
            cmds.select(cl = True)
        
        joint = cmds.joint(n = core.inc_name('joint_%s' % (curve)), p = position)

        joints.append(joint)

        
        if last_joint and parented:
            cmds.joint(last_joint, e = True, zso = True, oj = 'xyz', sao = 'yup')

        last_joint = joint
        
        inc += 1
    
    return joints
    

def create_joints_on_faces(mesh, faces = [], follow = True, name = None):
    """
    Create joints on the given faces.
    
    Args:
        mesh (str): The name of a mesh.
        faces (list): A list of face ids to create joints on.
        follow (bool): Wether the joints should follow.
        name (str): The name to applied to created nodes
        
    Returns: 
        list: Either the list of created joints, or if follow = True then [joints, follicles] 
    """
    mesh = get_mesh_shape(mesh)
    
    centers = []
    face_ids = []
     
    if faces:
        for face in faces:
            
            if type(face) == str or type(face) == unicode:
                sub_faces = cmds.ls(face, flatten = True)
                
                
                
                for sub_face in sub_faces:
                    id_value = vtool.util.get_last_number(sub_face)
                    
                    face_ids.append(id_value) 
        
        if type(face) == int:
            face_ids.append(face)
           
    if face_ids:
        centers = []
        
        for face_id in face_ids:
            
            center = get_face_center(mesh, face_id)
            centers.append(center)
    
    if not face_ids:
        centers = get_face_centers(mesh)
    
    
    joints = []
    follicles = []
    
    for center in centers:
        cmds.select(cl = True)
        
        if not name:
            name = 'joint_mesh_1'
        
        joint = cmds.joint(p = center, n = core.inc_name(name))
        joints.append(joint)
        
        if follow:
            follicle = attach_to_mesh(joint, mesh, hide_shape = True, constrain = False, rotate_pivot = True)
            
            follicles.append(follicle)
    
    if follicles:
        return joints, follicles
    if not follicles:
        return joints


def create_empty_follicle(description, uv = [0,0]):
    """
    Create a follicle
    
    Args:
        description (str): The description of the follicle.
        uv (list): eg. [0,0]
        
    Returns:
        str: The name of the created follicle.
    """

    follicleShape = cmds.createNode('follicle')
    cmds.hide(follicleShape)
    
    follicle = cmds.listRelatives(follicleShape, p = True)[0]
    
    cmds.setAttr('%s.inheritsTransform' % follicle, 0)
    
    if not description:
        follicle = cmds.rename(follicle, core.inc_name('follicle_1'))
    if description:
        follicle = cmds.rename(follicle, core.inc_name('follicle_%s' % description))
    
    cmds.setAttr('%s.parameterU' % follicle, uv[0])
    cmds.setAttr('%s.parameterV' % follicle, uv[1])
    
    return follicle   

def create_mesh_follicle(mesh, description = None, uv = [0,0]):
    """
    Create a follicle on a mesh
    
    Args:
        mesh (str): The name of the mesh to attach to.
        description (str): The description of the follicle.
        uv (list): eg. [0,0] This corresponds to the uvs of the mesh.
        
    Returns:
        str: The name of the created follicle.
    """

    
    follicle = create_empty_follicle(description, uv)
    
    shape = cmds.listRelatives(follicle, shapes = True)[0]
        
    cmds.connectAttr('%s.outMesh' % mesh, '%s.inputMesh' % follicle)
    cmds.connectAttr('%s.worldMatrix' % mesh, '%s.inputWorldMatrix' % follicle)
    
    cmds.connectAttr('%s.outTranslate' % shape, '%s.translate' % follicle)
    cmds.connectAttr('%s.outRotate' % shape, '%s.rotate' % follicle)
    
    return follicle
    
def create_surface_follicle(surface, description = None, uv = [0,0]):
    """
    Create a follicle on a surface
    
    Args:
        surface (str): The name of the surface to attach to.
        description (str): The description of the follicle.
        uv (list): eg. [0,0] This corresponds to the uvs of the mesh.
        
    Returns:
        str: The name of the created follicle.
    """    
    
    follicle = create_empty_follicle(description, uv)
    
    shape = cmds.listRelatives(follicle, shapes = True)[0]
        
    cmds.connectAttr('%s.local' % surface, '%s.inputSurface' % follicle)
    cmds.connectAttr('%s.worldMatrix' % surface, '%s.inputWorldMatrix' % follicle)
    
    cmds.connectAttr('%s.outTranslate' % shape, '%s.translate' % follicle)
    cmds.connectAttr('%s.outRotate' % shape, '%s.rotate' % follicle)
    
    return follicle

@core.undo_chunk
def create_oriented_joints_on_curve(curve, count = 20, description = None, attach = False):
    """
    Create joints on curve that are oriented to aim at child.
    
    Args:
        curve (str): The name of a curve
        count (int): The number of joints.
        description (str): The description to give the joints.
        rig (bool): Wether to rig the joints to the curve.
        
    Returns:
        list: The names of the joints created. If rig = True, than return [joints, ik_handle] 
    """
    if not description:
        description = 'curve'
    
    if count < 2:
        return
    
    length = cmds.arclen(curve, ch = False)
    cmds.select(cl = True)
    start_joint = cmds.joint(n = 'joint_%sStart' % description)
    
    end_joint = cmds.joint(p = [length,0,0], n = 'joint_%sEnd' % description)
    
    if count > 3:
        count = count -2
    
    joints = space.subdivide_joint(start_joint, end_joint, count, 'joint', description)
    
    joints.insert(0, start_joint)
    joints.append(end_joint)
    
    new_joint = []
    
    for joint in joints:
        new_joint.append( cmds.rename(joint, core.inc_name('joint_%s_1' % curve)) )
    
    ik = space.IkHandle(curve)
    ik.set_start_joint(new_joint[0])
    ik.set_end_joint(new_joint[-1])
    ik.set_solver(ik.solver_spline)
    ik.set_curve(curve)
    
    ik_handle = ik.create()
    cmds.setAttr( '%s.dTwistControlEnable' % ik_handle, 1)
    cmds.refresh()
    if not attach:
        cmds.delete(ik_handle)
        cmds.makeIdentity(new_joint[0], apply = True, r = True)
    
    return new_joint

def transforms_to_nurb_surface(transforms, description = 'from_transforms', spans = -1, offset_axis = 'Y', offset_amount = 1):
    """
    Create a nurbs surface from a list of joints.  
    Good for creating a nurbs surface that follows a spine or a tail.
    
    Args:
        transforms (list): List of transforms
        description (str): The description of the surface. Eg. 'spine', 'tail'
        spans (int): The number of spans to give the final surface. If -1 the surface will have spans based on the number of transforms.
        offset_axis (str): The axis to offset the surface relative to the transform.  Can be 'X','Y', or 'Z'
        offset_amount (int): The amount the surface offsets from the transforms.
        
    Returns:
        str: The name of the nurbs surface.
    """
    
    
    transform_positions_1 = []
    transform_positions_2 = []
    
    for transform in transforms:
        
        transform_1 = cmds.group(em = True)
        transform_2 = cmds.group(em = True)
        
        space.MatchSpace(transform, transform_1).translation_rotation()
        space.MatchSpace(transform, transform_2).translation_rotation()
        
        vector = vtool.util.get_axis_vector(offset_axis)
        
        cmds.move(vector[0]*offset_amount, 
                  vector[1]*offset_amount, 
                  vector[2]*offset_amount, transform_1, relative = True, os = True)
        
        cmds.move(vector[0]*-offset_amount, 
                  vector[1]*-offset_amount, 
                  vector[2]*-offset_amount, transform_2, relative = True, os = True)
        
        pos_1 = cmds.xform(transform_1, q = True, ws = True, t = True)
        pos_2 = cmds.xform(transform_2, q = True, ws = True, t = True)
        
        transform_positions_1.append(pos_1)
        transform_positions_2.append(pos_2)
        
        cmds.delete(transform_1, transform_2)
    
    curve_1 = cmds.curve(p = transform_positions_1, degree = 1)
    curve_2 = cmds.curve(p = transform_positions_2, degree = 1)  
    
    curves = [curve_1, curve_2]
    
    if not spans == -1:
    
        for curve in curves:
            cmds.rebuildCurve(curve, ch = False, 
                                        rpo = True,  
                                        rt = 0, 
                                        end = 1, 
                                        kr = False, 
                                        kcp = False, 
                                        kep = True,  
                                        kt = False, 
                                        spans = spans, 
                                        degree = 3, 
                                        tol =  0.01)
        
    loft = cmds.loft(curve_1, curve_2, n =core.inc_name('nurbsSurface_%s' % description), ss = 1, degree = 1, ch = False)
    
    #cmds.rebuildSurface(loft,  ch = True, rpo = 1, rt = 0, end = 1, kr = 0, kcp = 0, kc = 0, su = 1, du = 1, sv = spans, dv = 3, fr = 0, dir = 2)
      
    cmds.delete(curve_1, curve_2)
    
    return loft[0]



def transforms_to_curve(transforms, spans = None, description = 'from_transforms'):
    """
    Create a curve from a list of transforms.  Good for create the curve for a spine joint chain or a tail joint chain.
    
    Args:
        transforms (list): A list of transforms to generate the curve from. Their positions will be used to place cvs.
        spans (int): The number of spans the final curve should have.
        description (str): The description to give the curve, eg. 'spine', 'tail'
        
    Returns:
        str: The name of the curve.
    """
    transform_positions = []
        
    for joint in transforms:
        joint_position = cmds.xform(joint, q = True, ws = True, rp = True)
        
        transform_positions.append( joint_position )
    
    curve = cmds.curve(p = transform_positions, degree = 1)
    
    if spans:
        cmds.rebuildCurve(curve, ch = False, 
                                    rpo = True,  
                                    rt = 0, 
                                    end = 1, 
                                    kr = False, 
                                    kcp = False, 
                                    kep = True,  
                                    kt = False, 
                                    spans = spans, 
                                    degree = 3, 
                                    tol =  0.01)
        
    
    curve = cmds.rename( curve, core.inc_name('curve_%s' % description) )
    
    cmds.setAttr('%s.inheritsTransform' % curve, 0)
    
    return curve
    
def transform_to_polygon_plane(transform, size = 1, axis = 'Y'):
    """
    Create a single polygon face from the position and orientation of a transform.
    
    Args:
        transform (str): The name of the transform where the plane should be created.
        size (float): The size of the plane.
        
    Returns:
        str: The name of the new plane.
    """
    
    if type(axis) == type(str):
        axis.upper()
    
    if axis == 'X':
        axis_vector = [1,0,0]
    if axis == 'Y':
        axis_vector = [0,1,0]
    if axis == 'Z':
        axis_vector = [0,0,1]
    
    plane = cmds.polyPlane( w = size, h = size, sx = 1, sy = 1, ax = axis_vector, ch = 0)
    
    plane = cmds.rename(plane, core.inc_name('%s_plane' % transform))
    
    space.MatchSpace(transform, plane).translation_rotation()
    
    return plane

def transforms_to_polygon(transforms, name, size = 1, merge = True, axis = 'Y'):
    """
    Create polygons on each transform.  The mesh is good to rivet to and then deform.
    """
    meshes = []
    
    transforms = vtool.util.convert_to_sequence(transforms)
    
    for transform in transforms:
        mesh = transform_to_polygon_plane(transform, size, axis = axis)
        meshes.append(mesh)
        
    new_mesh = None
        
    if merge:
        if len(transforms) > 1:
            new_mesh = cmds.polyUnite(meshes, ch = False, mergeUVSets = True, name = name)
            new_mesh = new_mesh[0]
            
        if len(transforms) == 1:
            new_mesh = cmds.rename(meshes[0], name)
        cmds.polyLayoutUV(new_mesh, lm = 1)
        
    if new_mesh:
        return new_mesh

def joints_to_meshes(joints):
    
    for joint in joints:
    
        axis = space.get_axis_aimed_at_child(joint)
        child = cmds.listRelatives(joint, type = 'joint')
        dist = 1
        child_count = 0
        accum_dist = 0
        if child:
            children = child
            child_count = len(child)
            child = child[0]
            
            if child_count == 1:
                dist = space.get_distance(joint, child)
            
    
            if child_count > 1:
                for sub_child in children:
                    sub_distance = space.get_distance(joint, sub_child)
                    accum_dist += sub_distance
                accum_dist = accum_dist/child_count
        
        if not axis:
            axis = [0,1,0]
        
        divisor = 4.0
        
        if not accum_dist:
            accum_dist = dist
            divisor = 4.0
            
        
        sphere = cmds.polySphere(r = accum_dist/divisor)
        space.MatchSpace(joint, sphere).translation_rotation()
        
        if child_count == 1:
            cylinder = cmds.polyCylinder(axis = axis, height = dist, r = dist/6.0, sx = 6, sy = 2, sz = 1)
            space.MatchSpace(joint, cylinder).translation_rotation()        
    
            midpoint = space.get_midpoint(joint, child)
            cmds.xform(cylinder, ws = True, t = midpoint) 
            
            space.MatchSpace(joint, cylinder[0]).rotate_scale_pivot_to_translation()


def curve_to_nurb_surface(curve, description, spans = -1, offset_axis = 'X', offset_amount = 1):
    """
    Given a curve, generate a nurbs surface
    """
    curve_1 = cmds.duplicate(curve)[0]
    curve_2 = cmds.duplicate(curve)[0]
    
    offset_axis = offset_axis.upper()
    
    pos_move = vtool.util.get_axis_vector(offset_axis, offset_amount)
    neg_move = vtool.util.get_axis_vector(offset_axis, offset_amount*-1)
            
    
    cmds.move(pos_move[0],pos_move[1],pos_move[2], curve_1)
    cmds.move(neg_move[0],neg_move[1],neg_move[2], curve_2)
    
    curves = [curve_1, curve_2]
    
    if not spans == -1:
    
        for curve in curves:
            cmds.rebuildCurve(curve, ch = False, 
                                        rpo = True,  
                                        rt = 0, 
                                        end = 1, 
                                        kr = False, 
                                        kcp = False, 
                                        kep = True,  
                                        kt = False, 
                                        spans = spans, 
                                        degree = 3, 
                                        tol =  0.01)
        
    loft = cmds.loft(curve_1, curve_2, n =core.inc_name('nurbsSurface_%s' % description), ss = 1, degree = 1, ch = False)
    
    #cmds.rebuildSurface(loft,  ch = True, rpo = 1, rt = 0, end = 1, kr = 0, kcp = 0, kc = 0, su = 1, du = 1, sv = spans, dv = 3, fr = 0, dir = 2)
    spans = cmds.getAttr('%s.spans' % curve_1)
    cmds.rebuildSurface(loft, ch = False, rpo = 1, rt = 0, end = 1, kr = 0, kcp = 0, kc = 0, su = 1, du = 1, sv = spans, dv = 3, tol = 0.01, fr = 0, dir = 2)
    
    cmds.delete(curve_1, curve_2)
    
    return loft[0]
    
def nurb_surface_u_to_transforms(surface, count = 4, value = 0.5, orient_example = None):
    
    max_value_u = cmds.getAttr('%s.maxValueU' % surface)
    max_value_v = cmds.getAttr('%s.maxValueV' % surface)
    
    mid_value = max_value_v*value*1.0
    
    section = max_value_u / (count * 1.0)
    section_value = 0
    
    last_joint = None
    
    joints = []
    
    for inc in range(0, (count+1)):
        
        pos = cmds.pointPosition('%s.uv[%s][%s]' % (surface, section_value, mid_value))
        
        joint = cmds.createNode('joint', n = 'joint_%s_%s' % ((inc + 1), surface))
        cmds.xform(joint, ws = True, t = pos)
        
        if last_joint:
            cmds.parent(joint, last_joint)
            space.orient_x_to_child(last_joint)
        
        joints.append(joint)
        
        section_value += section
        last_joint = joint
        
        if inc == count:
            cmds.makeIdentity(joint, apply = True, jo = True)
    
    return joints
    

def nurb_surface_v_to_transforms(surface, description = '', count = 4, value = 0.5, orient_example = None):
    
    max_value_u = cmds.getAttr('%s.maxValueU' % surface)
    max_value_v = cmds.getAttr('%s.maxValueV' % surface)
    
    mid_value = max_value_u*value *1.
        
    section = max_value_v / (count * 1.0)
    section_value = 0
    
    last_joint = None
    
    joints = []
    
    for inc in range(0, (count+1)):
        
        pos = cmds.pointPosition('%s.uv[%s][%s]' % (surface, mid_value, section_value))
        
        if not description:
            description = surface
        joint = cmds.createNode('joint', n = 'joint_%s_%s' % ((inc + 1), description))
        cmds.xform(joint, ws = True, t = pos)
        
        if last_joint:
            cmds.parent(joint, last_joint)
            space.orient_x_to_child(last_joint)
        
        joints.append(joint)
        
        section_value += section
        last_joint = joint
        
        if inc == count:
            cmds.makeIdentity(joint, apply = True, jo = True)
    
    return joints

def polygon_plane_to_curves(plane, count = 5, u = True, description = ''):
    
    if not description:
        description = plane
    
    if count == 0:
        return
    
    work_plane = cmds.duplicate(plane)[0]
    
    add_poly_smooth(work_plane, divisions = 2)
    cmds.polyToSubdiv(work_plane, ap = 0, ch = False, aut = True,  maxPolyCount = 5000,  maxEdgesPerVert = 32)
    surface = cmds.subdToNurbs(work_plane, ch = False, aut = True,  ot = 0)[0]
    surface = cmds.listRelatives(surface, type = 'transform')[0]

    curves = []

    letter = 'u'
    if not u:
        letter = 'v'
        
    cap_letter = letter.capitalize()
    
    max_value = cmds.getAttr('%s.maxValue%s' % (surface, cap_letter))
    
    count_float = ((count - 1) * 1.0)
    if count_float == 0:
        section = max_value/2.0
    
    if count_float > 0:
        section = max_value / count_float 
    section_value = 0
    
    for inc in range(0, (count)):
        param = '%s.%s[%s]' % (surface, letter, section_value)
        
        duplicate_curve = cmds.duplicateCurve(param, ch = False, rn = 0, local = 0)[0]
        
        curve = cmds.rename(duplicate_curve, core.inc_name('curve_%s' % description))
        curves.append(curve)
        
        section_value += section
    
    cmds.delete(work_plane)
    
    return curves



    
    
def snap_to_mesh(transform, mesh, face = None):
    """
    Snap a transform to the nearest position on the mesh.
    """
    shape = get_mesh_shape(mesh)
    
    if not is_a_mesh(transform):
        rotate_pivot = True
    
    if rotate_pivot:
        position = cmds.xform(transform, q = True, rp = True, ws = True)
    if not rotate_pivot: 
        position = space.get_center(transform)
    
    face_fn = None
    face_id = None
    
    try:
        face_fn = api.IteratePolygonFaces(shape)
        face_id = face_fn.get_closest_face(position)
    except:
        return
    
    if face != None:
        face_id = face
    
    new_position = face_fn.get_center(face_id)
    
    cmds.xform(transform, ws = True, t = new_position)
    
def attach_to_mesh(transform, mesh, deform = False, priority = None, face = None, point_constrain = False, auto_parent = False, hide_shape= True, inherit_transform = False, local = False, rotate_pivot = False, constrain = True, mesh_in = None):
    """
    Be default this will attach the center point of the transform (including hierarchy and shapes) to the mesh.
    Important: If you need to attach to the rotate pivot of the transform make sure to set rotate_pivot = True
    This uses a rivet.
    
    Args:
        transform (str): The name of a transform.
        mesh (str): The name of a mesh.
        deform (bool): Wether to deform into position instead of transform. This will create a cluster.
        priority (str): The name of a transform to attach instead of transform.  Good if you need to attach to something close to transform, but actually want to attach the parent instead.
        face (int): The index of a face on the mesh, to create the rivet on. Good if the algorithm doesn't automatically attach to the best face.
        point_constrain (bool): Wether to attach with just a point constraint.
        auto_parent (bool): Wether to parent the rivet under the same parent as transform.
        hide_shape (bool): Wether to hide the shape of t he rivet locator. Good when parenting the rivet under a control.
        inherit_transform (bool): Wether to have the inheritTransform attribute of the rivet on.
        local (bool): Wether to constrain the transform to the rivet locally.  Such that the rivet can be grouped and the group can move without affecting the transform.
        rotate_pivot (bool): Wether to find the closest face to the rotate pivot of the transform.  If not it will search the center of the transform, including shapes.
        constrain (bool): Wether to parent the transform under the rivet.
        
    Returns:
        str: The name of the rivet.
    """
    
    parent = None
    if auto_parent:
        parent = cmds.listRelatives(transform, p = True)
    
    shape = get_mesh_shape(mesh)
    
    if not is_a_mesh(transform):
        rotate_pivot = True
    
    if rotate_pivot:
        position = cmds.xform(transform, q = True, rp = True, ws = True)
    if not rotate_pivot: 
        position = space.get_center(transform)
    
    if face == None:
        
        try:
            face_fn = api.MeshFunction(shape)
            face_id = face_fn.get_closest_face(position)
        except:
            face_fn = api.IteratePolygonFaces(shape)
            face_id = face_fn.get_closest_face(position)
        
    if face != None:
        face_id = face
    
    face_iter = api.IteratePolygonFaces(shape)
    edges = face_iter.get_edges(face_id)
    
    edge1 = '%s.e[%s]' % (mesh, edges[0])
    edge2 = '%s.e[%s]' % (mesh, edges[2])

    transform = vtool.util.convert_to_sequence(transform)
    
    if not priority:
        priority = transform[0]
    
    rivet = Rivet(priority)
    rivet.set_edges([edge1, edge2])
    rivet.set_mesh_in(mesh_in)
    rivet = rivet.create()
    
    orig_rivet = rivet
    rivet = cmds.group(em = True, n = 'offset_%s' % rivet, p = orig_rivet)
    space.MatchSpace(orig_rivet, rivet).translation_rotation()
    
    
    if deform:

        for thing in transform:
            cluster, handle = cmds.cluster(thing, n = core.inc_name('rivetCluster_%s' % thing))
            cmds.hide(handle)
            cmds.parent(handle, rivet )

    if constrain:
    
        if not deform and not local:
            for thing in transform:
                if not point_constrain:
                    cmds.parentConstraint(rivet, thing, mo = True)
                if point_constrain:
                    cmds.pointConstraint(rivet, thing, mo = True)
                    
        if local and not deform:
            for thing in transform:
                if point_constrain:
                    local, xform = space.constrain_local(rivet, thing, constraint = 'pointConstraint')
                if not point_constrain:
                    local, xform = space.constrain_local(rivet, thing, constraint = 'parentConstraint')
                    
                if auto_parent:
                    cmds.parent(xform, parent)
                    
                attr.connect_transforms(orig_rivet, xform)
                
    if not constrain:
        cmds.parent(transform, rivet)
        
                    
    if not inherit_transform:
        cmds.setAttr('%s.inheritsTransform' % orig_rivet, 0)
    
    if parent and auto_parent:
        cmds.parent(rivet, parent)
        
        
    if hide_shape:
        cmds.hide('%sShape' % orig_rivet)
        
    
    return orig_rivet

def attach_to_curve(transform, curve, maintain_offset = False, parameter = None):
    """
    Attach the transform to the curve using a point on curve.
    
    Args:
        transform (str): The name of a transform.
        curve (str): The name of a curve
        maintain_offset (bool): Wether to attach to transform and maintain its offset from the curve.
        parameter (float): The parameter on the curve where the transform should attach.
        
    Returns:
        str: The name of the pointOnCurveInfo
    """
    
    position = cmds.xform(transform, q = True, ws = True, rp = True)
    
    if parameter == None:
        parameter = get_closest_parameter_on_curve(curve, position)
        
    curve_info_node = cmds.pointOnCurve(curve, pr = parameter, ch = True)
    
    if not maintain_offset:
    
        cmds.connectAttr('%s.positionX' % curve_info_node, '%s.translateX' % transform)
        cmds.connectAttr('%s.positionY' % curve_info_node, '%s.translateY' % transform)
        cmds.connectAttr('%s.positionZ' % curve_info_node, '%s.translateZ' % transform)
    
    if maintain_offset:
        
        plus = cmds.createNode('plusMinusAverage', n = 'subtract_offset_%s' % transform)
        cmds.setAttr('%s.operation' % plus, 1)
        
        x_value = cmds.getAttr('%s.positionX' % curve_info_node)
        y_value = cmds.getAttr('%s.positionY' % curve_info_node)
        z_value = cmds.getAttr('%s.positionZ' % curve_info_node)
        
        x_value_orig = cmds.getAttr('%s.translateX' % transform)
        y_value_orig = cmds.getAttr('%s.translateY' % transform)
        z_value_orig = cmds.getAttr('%s.translateZ' % transform)
        
        cmds.connectAttr('%s.positionX' % curve_info_node, '%s.input3D[0].input3Dx' % plus)
        cmds.connectAttr('%s.positionY' % curve_info_node, '%s.input3D[0].input3Dy' % plus)
        cmds.connectAttr('%s.positionZ' % curve_info_node, '%s.input3D[0].input3Dz' % plus)
        
        cmds.setAttr('%s.input3D[1].input3Dx' % plus, -x_value )
        cmds.setAttr('%s.input3D[1].input3Dy' % plus, -y_value )
        cmds.setAttr('%s.input3D[1].input3Dz' % plus, -z_value )

        cmds.setAttr('%s.input3D[2].input3Dx' % plus, x_value_orig )
        cmds.setAttr('%s.input3D[2].input3Dy' % plus, y_value_orig )
        cmds.setAttr('%s.input3D[2].input3Dz' % plus, z_value_orig )

        cmds.connectAttr('%s.output3Dx' % plus, '%s.translateX' % transform)
        cmds.connectAttr('%s.output3Dy' % plus, '%s.translateY' % transform)
        cmds.connectAttr('%s.output3Dz' % plus, '%s.translateZ' % transform)
    
    return curve_info_node

def attach_motion_path(curve, name = 'motionPath', u_value = 0, up_rotate_object = None, use_parameter = False, local = False):
    
    motion = cmds.createNode('motionPath', n = name )
    
    if up_rotate_object:
        cmds.setAttr('%s.wut' % motion, 2)
        cmds.connectAttr('%s.worldMatrix' % up_rotate_object, '%s.wum' % motion)
    
    
    if use_parameter:
        cmds.setAttr('%s.fractionMode' % motion, False)
    else:
        cmds.setAttr('%s.fractionMode' % motion, True)
    
    if not use_parameter:
        u_value = get_curve_length_from_parameter(curve, u_value)
        curve_length = cmds.arclen(curve, ch = False)
        u_value = u_value/curve_length
    
    cmds.setAttr('%s.uValue' % motion, u_value)
    
    if not local:
        cmds.connectAttr('%s.worldSpace' % curve, '%s.geometryPath' % motion)
    if local:
        cmds.connectAttr('%s.local' % curve, '%s.geometryPath' % motion)
    
    return motion

def attach_to_motion_path(transform, curve, up_rotate_object = None, constrain = True, local = False, use_parameter = False, u_value = None, direct = False, translate_only = False):
    
    motion = cmds.createNode('motionPath', n = 'motionPath_%s' % transform )
    
    if up_rotate_object:
        cmds.setAttr('%s.wut' % motion, 2)
        cmds.connectAttr('%s.worldMatrix' % up_rotate_object, '%s.wum' % motion)
    
    
    if use_parameter:
        cmds.setAttr('%s.fractionMode' % motion, False)
    else:
        cmds.setAttr('%s.fractionMode' % motion, True)
    
    position = cmds.xform(transform, q = True, ws = True, t = True)
    
    if u_value == None:
        u_value = get_closest_parameter_on_curve(curve, position)
    
    if not use_parameter:
        u_value = get_curve_length_from_parameter(curve, u_value)
        curve_length = cmds.arclen(curve, ch = False)
        u_value = u_value/curve_length
    
    cmds.setAttr('%s.uValue' % motion, u_value)
    
    if not local:
        cmds.connectAttr('%s.worldSpace' % curve, '%s.geometryPath' % motion)
    if local:
        cmds.connectAttr('%s.local' % curve, '%s.geometryPath' % motion)
    
    if not direct:
        locator = cmds.spaceLocator(n = 'locator_%s' % motion)[0]
        shapes = core.get_shapes(locator)
        if shapes:
            cmds.hide(shapes)
    if direct: 
        locator = transform
    cmds.connectAttr('%s.xCoordinate' % motion, '%s.translateX' % locator)
    cmds.connectAttr('%s.yCoordinate' % motion, '%s.translateY' % locator)
    cmds.connectAttr('%s.zCoordinate' % motion, '%s.translateZ' % locator)
    
    if not translate_only:
        cmds.connectAttr('%s.rotateX' % motion, '%s.rotateX' % locator)
        cmds.connectAttr('%s.rotateY' % motion, '%s.rotateY' % locator)
        cmds.connectAttr('%s.rotateZ' % motion, '%s.rotateZ' % locator)
        
        cmds.connectAttr('%s.rotateOrder' % motion, '%s.rotateOrder' % locator)
        cmds.connectAttr('%s.message' % motion, '%s.specifiedManipLocation' % locator)
    
    if not direct:
        if constrain:
            cmds.parentConstraint(locator, transform, mo = True)
        if not constrain:
            current_parent = cmds.listRelatives(transform, p = True)
            
            cmds.parent(transform, locator)
            
            if current_parent:
                cmds.parent(locator, current_parent)
        
    return motion, locator

def attach_to_surface(transform, surface, u = None, v = None, constrain = True):
    """
    Attach the transform to the surface using a rivet.
    If no u and v value are supplied, the command will try to find the closest position on the surface.
    
    Args:
        transform (str): The name of a transform.
        surface (str): The name of the surface to attach to.
        u (float): The u value to attach to.
        v (float): The v value to attach to. 
        
    Returns:
        str: The name of the rivet.
    """
    
    position = cmds.xform(transform, q = True, ws = True, t = True)

    uv = [u,v]

    if u == None or v == None:
        uv = get_closest_parameter_on_surface(surface, position)   
        
    rivet = Rivet(transform)
    rivet.set_surface(surface, uv[0], uv[1])
    rivet.set_create_joint(False)
    rivet.set_percent_on(False)
    
    rivet.create()
    
    if constrain:
        loc = cmds.spaceLocator(n = 'locator_%s' % rivet.rivet)[0]
        
        cmds.parent(loc, rivet.rivet)
        space.MatchSpace(transform, loc).translation_rotation()
        
        cmds.parentConstraint(loc, transform, mo = True)
        
    if not constrain:
        cmds.parent(transform, rivet.rivet)
    
    return rivet.rivet


def follicle_to_mesh(transform, mesh, u = None, v = None, constrain = True, constraint_type = 'parentConstraint', local = False):
    """
    Use a follicle to attach the transform to the mesh.
    If no u and v value are supplied, the command will try to find the closest position on the mesh. 
    
    Args:
        transform (str): The name of a transform to follicle to the mesh.
        mesh (str): The name of a mesh to attach to.
        u (float): The u value to attach to.
        v (float): The v value to attach to. 
        
    Returns: 
        str: The name of the follicle created.
        
        
    """
    if not core.is_a_shape(mesh):
        mesh = get_mesh_shape(mesh)
    
    position = cmds.xform(transform, q = True, ws = True, rp = True)
    
    uv = u,v
    
    if u == None or v == None:
        uv = get_closest_uv_on_mesh(mesh, position)
        
    follicle = create_mesh_follicle(mesh, transform, uv)   
    
    if not constrain:
        cmds.parent(transform, follicle)
    if constrain:
        if not local:
            loc = cmds.spaceLocator(n = 'locator_%s' % follicle)[0]
            
            cmds.parent(loc, follicle)
            space.MatchSpace(transform, loc).translation_rotation()
            
            #cmds.parentConstraint(loc, transform, mo = True)
            
            eval('cmds.%s("%s", "%s", mo = True)' % (constraint_type, loc, transform))
        if local:
            
            space.constrain_local(follicle, transform, constraint = constraint_type)
            
    
    return follicle
    
def follicle_to_surface(transform, surface, u = None, v = None, constrain = False):
    """
    Follicle the transform to a nurbs surface.
    If no u and v value are supplied, the command will try to find the closest position on the surface. 
    
    Args:
        transform (str): The name of a transform to follicle to the surface.
        mesh (str): The name of a surface to attach to.
        u (float): The u value to attach to.
        v (float): The v value to attach to. 
        
    Returns: 
        str: The name of the follicle created.
        
    """
    position = cmds.xform(transform, q = True, ws = True, rp = True)

    uv = u,v

    if u == None or v == None:
        uv = get_closest_parameter_on_surface(surface, position)   

    follicle = create_surface_follicle(surface, transform, uv)
    
    if not constrain:
        cmds.parent(transform, follicle)
    if constrain:
        loc = cmds.spaceLocator(n = 'locator_%s' % follicle)[0]
            
        cmds.parent(loc, follicle)
        space.MatchSpace(transform, loc).translation_rotation()
        
        cmds.parentConstraint(loc, transform, mo = True)
        #cmds.parentConstraint(follicle, transform, mo = True)
    
    return follicle

def cvs_to_transforms(nurbs, type = 'transform'):
    """
    Given a nurbs surface or a curve create a joint or transform at each one. These will be unparented from each other
    """
    cvs = cmds.ls('%s.cv[*]' % nurbs, flatten = True)
    
    transforms = []
    
    
    
    for cv in cvs:
        if type == 'transform':
            transform = cmds.spaceLocator( n = 'transform_%s_1' % nurbs)
        if type == 'joint':
            cmds.select(cl = True)
            transform = cmds.joint( n = 'transform_%s_1' % nurbs) 
        pos = cmds.pointPosition(cv, w = True)
        
        cmds.xform(transform, ws = True, t = pos)
        
        transforms.append(transform)
        
    return transforms           

def rebuild_curve(curve, spans = -1, degree = 3):
    """
    Rebuild a curve with fewer arguments
    """
    
    if spans == -1:
        spans = cmds.getAttr('%s.spans' % curve)
    cmds.rebuildCurve( curve, ch = False,
                       rpo = 1,
                       rt = 0,
                       end = 1,
                       kr = 0, 
                       kcp = 0,
                       kep = 1, 
                       kt = 0,
                       s = spans,
                       d = degree,
                       tol = 0.01)

    return curve

def rebuild_curve_at_distance(curve, min_length, max_length, min_spans = 3, max_spans = 10,):
    """
    Rebuild curves based on their length. Usefull when you have hundreds of curves and you want short curves to have less spans than long.
    """
    length = cmds.arclen(curve, ch = False)
    
    spans = vtool.util_math.remap_value(length, min_length, max_length, min_spans, max_spans)
    
    rebuild_curve(curve, spans, degree = 3)

def evenly_position_curve_cvs(curve, match_curve = None):
    """
    Given a curve, evenly position the cvs along the curve.
    """
    cvs = cmds.ls('%s.cv[*]' % curve, flatten = True)
    
    if not match_curve:
        match_curve = curve
    
    snap_transforms_to_curve(cvs, curve)
        
def snap_transforms_to_curve(transforms, curve):
    """
    Snap the transform to the nearest position on the curve.
    """
    count = len(transforms)
        
    total_length = cmds.arclen(curve)
    
    part_length = total_length/(count-1)
    current_length = 0.0
    
    if count-1 == 0:
        part_length = 0
    
    temp_curve = cmds.duplicate(curve)[0]
    
    for inc in range(0, count):
        
        param = get_parameter_from_curve_length(temp_curve, current_length)
        position = get_point_from_curve_parameter(temp_curve, param)
        
        transform = transforms[inc]
        
        if cmds.nodeType(transform) == 'joint':
            
            cmds.move(position[0], position[1], position[2], '%s.scalePivot' % transform, 
                                                            '%s.rotatePivot' % transform, a = True)            
        
        if not cmds.nodeType(transform) == 'joint':
            cmds.xform(transform, ws = True, t = position)
        
        current_length += part_length  
    
    cmds.delete(temp_curve)
        
@core.undo_chunk
def snap_joints_to_curve(joints, curve = None, count = 10):
    """
    Snap the joints to a curve. 
    If count is greater than the number of joints, than joints will be added along the curve.
    
    Args:
        joints (list): A list of joints to snap to the curve.
        curve (str): The name of a curve. If no curve given a simple curve will be created based on the joints. Helps to smooth out joint positions.
        count (int): The number of joints. if the joints list doesn't have the same number of joints as count, then new joints are created.
        
    """
    if not joints:
        return
    
    delete_after = []
    
    if not curve:
        curve = transforms_to_curve(joints, spans = count, description = 'temp')
        delete_after.append(curve)
        
    joint_count = len(joints)
    
    if joint_count < count and count:
        
        missing_count = count-joint_count
        
        for inc in range(0, missing_count):

            joint = cmds.duplicate(joints[-1])[0]
            joint = cmds.rename(joint, core.inc_name(joints[-1]))
            
            cmds.parent(joint, joints[-1])
            
            joints.append(joint)

    joint_count = len(joints)
    
    if not joint_count:
        return
    
    if count == 0:
        count = joint_count
    
    total_length = cmds.arclen(curve)
    
    part_length = total_length/(count-1)
    current_length = 0.0
    
    if count-1 == 0:
        part_length = 0
    
    for inc in range(0, count):
        param = get_parameter_from_curve_length(curve, current_length)
        position = get_point_from_curve_parameter(curve, param)
        
        cmds.move(position[0], position[1], position[2], '%s.scalePivot' % joints[inc], 
                                                         '%s.rotatePivot' % joints[inc], a = True)
        current_length += part_length  
        
    if delete_after:
        cmds.delete(delete_after)    

def snap_curve_to_surface(curve, surface, offset = 1):
    """
    Snap curve cvs on a surface.
    """
    shapes = core.get_shapes(curve)
    
    for shape in shapes:
        
        cvs = cmds.ls('%s.cv[*]' % shape, flatten = True)
        
        for cv in cvs:
            
            position = cmds.xform(cv, q = True, ws = True, t = True)
            
            if is_a_mesh(surface):
                mesh_fn = api.MeshFunction(surface)
                closest_point = mesh_fn.get_closest_position(position)
                
                cmds.xform(cv, ws = True, t = closest_point)
    
        cmds.scale(offset,offset,offset, cvs, r = True)
            
def snap_project_curve_to_surface(curve, surface, offset = 1):
    """
    Project curve cvs on a surface
    """
    center = cmds.xform(curve, q = True, ws = True, rp = True)
    shapes = core.get_shapes(curve)
    
    for shape in shapes:
        
        cvs = cmds.ls('%s.cv[*]' % shape, flatten = True)
        
        for cv in cvs:
            
            position = cmds.xform(cv, q = True, ws = True, t = True)
            
            
            if is_a_mesh(surface):
                mesh_fn = api.MeshFunction(surface)
                closest_point = mesh_fn.get_closest_intersection(position, center)
            
                cmds.xform(cv, ws = True, t = closest_point)

        cmds.scale(offset,offset,offset, cvs, r = True)

def convert_indices_to_mesh_vertices(indices, mesh):
    """
    Convenience for converting mesh index numbers to maya names. eg [mesh.vtx[0]] if index = [0]
    Args:
        indices (list): A list of indices.
        mesh (str): The name of a mesh.
    Returns: 
        list: A list of properly named vertices out of a list of indices.
    """
    verts = []
    
    for index in indices:
        verts.append('%s.vtx[%s]' % (mesh, index))
        
    return verts

def convert_indices_to_mesh_faces(indices, mesh):
    """
    Given a list of indices convert them to the names of faces.
    """
    faces = []
    
    for index in indices:
        faces.append('%s.f[%s]' % (mesh, index))
        
    return faces



def add_poly_smooth(mesh, divisions = 1):
    """
    create a polySmooth node on the mesh.
    
    Args:
        mesh (str): The name of a mesh.
        
    Returns:
        str: The name of the poly smooth node.
    """
    if vtool.util.get_maya_version() < 2017:
        poly_smooth = cmds.polySmooth(mesh, mth = 0, dv = divisions, bnr = 1, c = 1, kb = 0, khe = 0, kt = 1, kmb = 1, suv = 1, peh = 0, sl = 1, dpe = 1, ps = 0.1, ro = 1, ch = 1)[0]
    
    if vtool.util.get_maya_version() >= 2017:
        poly_smooth = cmds.polySmooth(mesh, sdt = 2, mth = 0, dv = divisions, bnr = 1, c = 1, kb = 0, khe = 0, kt = 1, kmb = 1, suv = 1, peh = 0, sl = 1, dpe = 1, ps = 0.1, ro = 1, ch = 1)[0]
    
    return poly_smooth

def smooth_preview(mesh, bool_value = True):
    """
    Turn off and on smooth preview.
    """
    if bool_value == True:
        cmds.setAttr('%s.displaySmoothMesh' % mesh, 2)
        
    if bool_value == False:
        cmds.setAttr('%s.displaySmoothMesh' % mesh, 0)
        
def smooth_preview_all(bool_value = True):
    """
    Turn off and on smooth preview on every mesh.
    """
    if core.is_batch():
        return
    
    meshes = cmds.ls(type = 'mesh')
    
    for mesh in meshes:
        
        intermediate = cmds.getAttr('%s.intermediateObject' % mesh)
         
        if intermediate == 0:
            smooth_preview(mesh, bool_value)
            
            
def randomize_mesh_vertices(mesh, range_min = 0.0, range_max = 0.1):
    """
    Randomize the positions of vertices on a mesh.
    """
    vtool.util.convert_to_sequence(mesh)
    
    all_verts = []
    
    for thing in mesh:
        if is_a_mesh(thing):
            verts = get_vertices(mesh)
            all_verts += verts
        if thing.find('.vtx') > -1:
            all_verts.append(thing)
    
    for vert in all_verts:
        cmds.move(uniform(range_min, range_max),uniform(range_min, range_max),uniform(range_min, range_max), vert, r = True)
        
        
def transfer_uvs_from_mesh_to_group(mesh, group):
    """
    currently only works with map1 uv set
    mesh and group need to have the same topology and point position.
    Also this deletes history
    """
    
    if not is_a_mesh(mesh):
        vtool.util.warning('%s is not a mesh. Transfer uvs could not continue' % mesh)
        return
    
    temp_mesh = cmds.duplicate(mesh)[0]
    
    destination_meshes = cmds.polySeparate( temp_mesh )
    
    source_meshes = core.get_shapes_in_hierarchy(group, 'mesh', return_parent = True)
    
    if not source_meshes:
        vtool.util.warning('Found no meshes in group. Transfer uvs could not continue.')
        return
    
    for destination_mesh in destination_meshes:
        
        if not is_a_mesh(destination_mesh):
            continue
        
        destination_count = len(cmds.ls('%s.vtx[*]' % destination_mesh, flatten = True))
        
        found = False
        
        for source_mesh in source_meshes:
            
            source_count = len(cmds.ls('%s.vtx[*]' % source_mesh, flatten = True))
            
            if destination_count == source_count:
                
                pos1 = space.get_center(destination_mesh)
                pos2 = space.get_center(source_mesh)
                
                dist = vtool.util.get_distance(pos1, pos2)
                
                if dist < 0.0001:
                    try:
                        cmds.transferAttributes(destination_mesh, source_mesh, transferPositions =  0, transferNormals = 0, transferUVs = 1, sourceUvSet = "map1", targetUvSet = "map1", transferColors = 0, sampleSpace = 5, sourceUvSpace = "map1",  targetUvSpace = "map1", searchMethod = 3, searchScaleX = -1.0, flipUVs = 0, colorBorders = 1 )
                        cmds.delete(source_mesh, ch = True)
                        vtool.util.show('Transfer worked on %s' % source_mesh )
                        found = True
                    except:
                        pass
                    continue
        
        if not found:
            vtool.util.warning('Found no geometry match for %s' % destination_mesh)
        
    cmds.delete(temp_mesh)

def create_extrude(curve, radius, taper, spans, description = ''):

    curve = cmds.duplicate(curve)[0]
    
    rebuild_curve(curve, spans = spans)
    
    max_value = cmds.getAttr('%s.maxValue' % curve)
    
    circle = cmds.circle( c = [0,0,0], nr = [0, 1, 0], sw = 360, r = radius, d = 3, ut = 0, tol = 1.07639e-007, s = 8, ch = 0)
    cmds.reverseCurve(circle[0], ch = False, rpo = 1)
    
    extrude = cmds.extrude(circle[0],curve, ch = True, rn = False, po = 1, et = 2, ucp = 1, fpt = 1, upn = 1, rotation = 0, scale = 1, rsp = 1, cch = False)
    
    out_surfaces = attr.get_attribute_outputs('%s.outputSurface' % extrude[1], node_only = True)
    for out_surface in out_surfaces:
        cmds.setAttr('%s.format' % out_surface, 3)
    
    extrude = extrude[0]
    extrude = cmds.rename(extrude, 'extrude_%s' % curve)
    
    
    
    wire_deformer, wire_curve = cmds.wire(extrude,  gw = False, w = curve, n = core.inc_name('wire_%s' % curve), dds = [0, 10000])
    if taper:
        cmds.dropoffLocator( 1, 1, wire_deformer, '%s.u[0]' % curve, '%s.u[%s]' % (curve,max_value))
        
        cmds.setAttr('%s.scale[0]' % wire_deformer, taper)
        cmds.setAttr('%s.wireLocatorEnvelope[0]' % wire_deformer, 0)
    
    cmds.delete(extrude, ch = True)
    cmds.delete(curve)
    cmds.delete(circle[0])
    cmds.delete('%sBaseWire' % wire_curve)
    
    occluded = get_occluded_faces(extrude, within_distance = 10000)
    faces = cmds.ls('%s.f[*]' % extrude, flatten = True)
    
    if len(occluded) > (len(faces)/2):
        cmds.polyNormal(extrude, normalMode = 0, userNormalMode = 0, ch = 0)
    
    
    return extrude

def create_quill(curve, radius, taper_tip = True, spans = 10, description = '' ):
    
    curve = cmds.duplicate(curve)[0]
    
    rebuild_curve(curve, spans = spans)
    
    max_value = cmds.getAttr('%s.maxValue' % curve)
    
    circle = cmds.circle( c = [0,0,0], nr = [0, 1, 0], sw = 360, r = radius, d = 3, ut = 0, tol = 1.07639e-007, s = 8, ch = 0)
    cmds.reverseCurve(circle[0], ch = False, rpo = 1)
    
    extrude = cmds.extrude(circle[0],curve, ch = True, rn = False, po = 1, et = 2, ucp = 1, fpt = 1, upn = 1, rotation = 0, scale = 1, rsp = 1, cch = False)
    
    out_surfaces = attr.get_attribute_outputs('%s.outputSurface' % extrude[1], node_only = True)
    for out_surface in out_surfaces:
        cmds.setAttr('%s.format' % out_surface, 3)
    
    extrude = extrude[0]
    extrude = cmds.rename(extrude, 'quill_%s' % curve)
    
    
    
    wire_deformer, wire_curve = cmds.wire(extrude,  gw = False, w = curve, n = core.inc_name('wire_%s' % curve), dds = [0, 10000])
    if taper_tip:
        cmds.dropoffLocator( 1, 1, wire_deformer, '%s.u[0]' % curve,'%s.u[%s]' % (curve, max_value - (max_value/5.0)), '%s.u[%s]' % (curve,max_value))
        
        cmds.setAttr('%s.scale[0]' % wire_deformer, .25)
        cmds.setAttr('%s.wireLocatorEnvelope[0]' % wire_deformer, 0)
        cmds.setAttr('%s.wireLocatorEnvelope[1]' % wire_deformer, 0)
    
    cmds.delete(extrude, ch = True)
    cmds.delete(curve)
    cmds.delete(circle[0])
    cmds.delete('%sBaseWire' % wire_curve)
    
    occluded = get_occluded_faces(extrude, within_distance = 10000)
    faces = cmds.ls('%s.f[*]' % extrude, flatten = True)
    
    if len(occluded) > (len(faces)/2):
        cmds.polyNormal(extrude, normalMode = 0, userNormalMode = 0, ch = 0)
    
    
    return extrude
    
def transfer_from_curve_to_curve(source_curve, destination_curve, transforms, reference_mesh_for_normal = None, twist = 0):
    """
    transforms can be either transform nodes or vertices
    """
    
    
    destination_max = cmds.getAttr('%s.maxValue' % destination_curve)
    
    curves = []
    
    is_component = True
    
    for transform in transforms:
        
        if not transform.find('.vtx[') > -1:
            transform = cmds.duplicate(transform)[0]
            is_component = False
        
        
        
        curves.append(transform)
        
        if not is_component:
            position = cmds.xform(transform, q = True, ws = True, rp = True)
        if is_component:
            position = cmds.xform(transform, q = True, ws = True, t = True)
        if core.has_shape_of_type(transform, 'nurbsCurve'):
            position = cmds.xform('%s.cv[0]' % transform, q = True, ws = True, t = True)
        param = get_closest_parameter_on_curve(source_curve, position)
        source_position = get_curve_position_from_parameter(source_curve, param)
        
        pos_group = cmds.group(em = True)
        cmds.xform(pos_group, ws = True, t = source_position)
        
        cmds.rotate(0,0,twist, transform)
        
        if not is_component:
            cmds.parent(transform, pos_group)
        if is_component:
            cluster = cmds.cluster(transform)
            cmds.parent(cluster, pos_group) 
                
        destination = get_curve_position_from_parameter(destination_curve, param)
        
        cmds.xform(pos_group, ws = True, t = destination)
        
        neg_aim = False
        
        aim_param = param + param/100.0
        if aim_param > destination_max:
            aim_param = destination_max
        if param == destination_max:
            aim_param = param - param/100.0
            neg_aim = True
        aim_direction = [0,0,1]
        if neg_aim:
            aim_direction = [0,0,-1]
        aim_vector = get_curve_position_from_parameter(destination_curve, aim_param)
        
        loc = cmds.spaceLocator()
        cmds.xform(loc, ws = True, t = aim_vector)
        
        destination_base = destination
        
        if core.has_shape_of_type(transform, 'nurbsCurve'):
            destination_base = cmds.xform('%s.cv[0]' % transform, q = True, ws = True, t = True)
        
        normal = get_closest_normal_on_mesh(reference_mesh_for_normal, destination_base)
        loc_normal = cmds.spaceLocator()[0]
        cmds.xform(loc_normal, ws = True, t = normal)
        normal_offset = cmds.group(em = True, n = 'normal')
        cmds.parent(loc_normal, normal_offset)
        cmds.xform(normal_offset, ws = True, t = destination)
        
        
        cmds.aimConstraint(loc, pos_group, aim = aim_direction, upVector = [0,1,0], wuo = loc_normal, worldUpType = 'object')
        
        if is_component:
            mesh = get_mesh_from_vertex(transform)
            if mesh:
                cmds.delete(mesh, ch = True)
        
        if not is_component:
            cmds.parent(transform, w = True)
        cmds.delete(loc)
        cmds.delete(normal_offset)
        if cmds.objExists(pos_group):
            cmds.delete(pos_group)
        
        
    
    return curves

def move_cvs(curves, position, pivot_at_center = False):
    """
    This will move the cvs together and maintain their offset and put them at a world position, not local
    """
    
    curves = vtool.util.convert_to_sequence(curves)
    
    for curve in curves:
        
        if curve.find('.cv[') > -1:
            curve_cvs = curve
            curve = get_curve_from_cv(curve)
        else:
            curve_cvs = '%s.cv[*]' % curve
        
        if core.is_a_shape(curve):
            curve = cmds.listRelatives(curve, p = True)[0]
        
        if pivot_at_center:
            center_position = space.get_center(curve_cvs)
        else:
            center_position = cmds.xform(curve, q = True, ws = True, rp = True)
        
        offset = vtool.util.vector_sub(position, center_position)
        
        cmds.move(offset[0],offset[1],offset[2], curve_cvs, ws = True, r = True)
        
        
def set_geo_color(geo_name, rgb = [1,0,0], flip_color = False):
    """
    Set the color of geo by setting its vetex colors
    """
    rgb = list(rgb)

    if flip_color:
        rgb[0] = rgb[0] * (1 - rgb[0] * 0.5)
        rgb[1] = rgb[1] * (1 - rgb[1] * 0.5)
        rgb[2] = rgb[2] * (1 - rgb[2] * 0.5)
    
    cmds.polyColorPerVertex(geo_name, colorRGB = rgb, cdo = True)
    
    return rgb