# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

from random import uniform

import vtool.util
import api


if vtool.util.is_in_maya():
    import maya.cmds as cmds
    
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
        
    
    def check_vert_edge_face_count(self):
        
        if not self.check_face_count():
            return False
        
        if not self.check_vert_count():
            return False
        
        if not self.check_edge_count():
            return False
            
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
        
        
        cmds.connectAttr('%s.worldMatrix' % mesh, '%s.inputMat' % edge_to_curve_1)
        cmds.connectAttr('%s.outMesh' % mesh, '%s.inputPolymesh' % edge_to_curve_1)
        
        cmds.connectAttr('%s.worldMatrix' % mesh, '%s.inputMat' % edge_to_curve_2)
        cmds.connectAttr('%s.outMesh' % mesh, '%s.inputPolymesh' % edge_to_curve_2)
        
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
        if not self.create_joint:
            self.rivet = cmds.spaceLocator(n = core.inc_name('rivet_%s' % self.name))[0]
            
        if self.create_joint:
            cmds.select(cl = True)
            self.rivet = cmds.joint(n = core.inc_name('joint_%s' % self.name))
        
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
            cmds.connectAttr('%s.worldSpace' % self.surface, '%s.inputSurface' % self.point_on_surface)
        
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
    
    if cmds.objExists('%s.cv[0]' % node) and not cmds.objExists('%s.cv[0][0]' % node):
        return True
    
    return False

def is_mesh_compatible(mesh1, mesh2):
    """
    Check the two meshes to see if they have the same vert, edge and face count.
    """
    check = MeshTopologyCheck(mesh1, mesh2)
    return check.check_vert_edge_face_count()

def is_mesh_position_same(mesh1, mesh2, tolerance = .00001):
    """
    Check the positions of the vertices on the two meshes to see if they have the same positions within the tolerance.
    """
    
    if not is_mesh_compatible(mesh1, mesh2):
        vtool.util.warning('Skipping vert position compare. %s and %s are not compatible.' % (mesh1, mesh2))
        return False
    
    mesh1_fn = api.IterateGeometry(mesh1)
    point1 = mesh1_fn.get_points_as_list()
    
    mesh2_fn = api.IterateGeometry(mesh2)
    point2 = mesh2_fn.get_points_as_list()
    
    for inc in xrange(0, len(point1)):
        
        for sub_inc in xrange(0,3):
            if (abs(point1[inc][sub_inc] - point2[inc][sub_inc]) > tolerance):
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

def get_edges_in_list(list_of_things):
    
    found = []
    
    for thing in list_of_things:
        if cmds.nodeType(thing) == 'mesh':
            if thing.find('.e[') > 0:
                found.append(thing)
                
    return found 

def get_meshes_in_list(list_of_things):
    
    found = []
    
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

def match_cv_position( source_curve, target_curve ):
    
    source_cvs = cmds.ls('%s.cv[*]' % source_curve, flatten = True)
    target_cvs = cmds.ls('%s.cv[*]' % target_curve, flatten = True)
    
    for inc in range(0, len(source_cvs)):
        
        pos = cmds.xform(source_cvs[inc], q= True, t = True, ws = True)
        cmds.xform(target_cvs[inc], t = pos, ws = True)
        
def is_cv_count_same(source_curve, target_curve):
    
    source_length = len(cmds.ls('%s.cv[*]' % source_curve, flatten = True))
    target_length = len(cmds.ls('%s.cv[*]' % target_curve, flatten = True))
    
    if not source_length == target_length:
        return False
    
    return True

def get_curves_in_list(list_of_things):     

    found = []
    
    for thing in list_of_things:
        if cmds.nodeType(thing) == 'nurbsCurve':
            found_mesh = cmds.listRelatives(thing, p = True)
            found.append(found_mesh)
            
        if cmds.nodeType(thing) == 'transform':
            
            
            shapes = get_curve_shape(thing)
            if shapes:
                found.append(thing)
     
    return found  


def get_surfaces_in_list(list_of_things):     

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
    
    selection = cmds.ls(sl = True)
    found = get_curves_in_list(selection)
    return found

def get_selected_surfaces():
    
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
    relatives = cmds.listRelatives(transform, ad = True, type = node_type, f = True)
    
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

def get_vertices(mesh):
    
    mesh = get_mesh_shape(mesh)
    
    meshes = core.get_shapes(mesh, 'mesh', no_intermediate=True)
    
    found = []
    
    for mesh in meshes:
        
        verts = cmds.ls('%s.vtx[*]' % mesh)
        
        if verts:
            found += verts
    
    return found

def get_triangles(mesh):
    
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
    
def get_render_stats(node_name):
    
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
    stats = get_render_stats(node_name)
    
    for inc in range(0, len(stats)):
        
        stat = stats[inc][0]
        attr = ('%s.%s' % (node_name, stat))
        
        if stat == 'doubleSided':
            cmds.setAttr(attr, RENDER_DEFAULT_DOUBLE_SIDED)
            
        if stat == 'opposite':
            cmds.setAttr(attr, RENDER_DEFAULT_OPPOSITE)

def create_mesh_from_bounding_box(min_vector, max_vector, name):
    
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
    
    shape = get_mesh_shape(mesh, 0)
    
    name = core.get_basename(mesh, remove_namespace = True)
    
    new_mesh = create_shape_from_shape(shape, '%s_reference' % name)
    
    shapes = core.get_shapes(new_mesh, 'mesh')
    
    cmds.connectAttr('%s.message' % shapes[0], '%s.referenceObject' % mesh)
    
    cmds.setAttr( '%s.template' % shapes[0],  True )
    return new_mesh

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
def create_oriented_joints_on_curve(curve, count = 20, description = None):
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
        
    loft = cmds.loft(curve_1, curve_2, n ='nurbsSurface_%s' % description, ss = 1, degree = 1, ch = False)
    
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
        joint_position = cmds.xform(joint, q = True, ws = True, t = True)
        
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
    


def expand_selected_edge_loop():
    
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


    
    
def snap_to_mesh(transform, mesh, face = None):
    
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
    
def attach_to_mesh(transform, mesh, deform = False, priority = None, face = None, point_constrain = False, auto_parent = False, hide_shape= True, inherit_transform = False, local = False, rotate_pivot = False, constrain = True):
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
    rivet = rivet.create()
    
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

    if not constrain:
        cmds.parent(transform, rivet)
        
                    
    if not inherit_transform:
        cmds.setAttr('%s.inheritsTransform' % rivet, 0)
    
    if parent and auto_parent:
        cmds.parent(rivet, parent)
        
        
    if hide_shape:
        cmds.hide('%sShape' % rivet)
        
    
    return rivet

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
    
    if not parameter:
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

def attach_to_motion_path(transform, curve, up_rotate_object = None, constrain = True, local = False):
    
    motion = cmds.createNode('motionPath', n = 'motionPath_%s' % transform )
    
    if up_rotate_object:
        cmds.setAttr('%s.wut' % motion, 2)
        cmds.connectAttr('%s.worldMatrix' % up_rotate_object, '%s.wum' % motion)
    
    
    cmds.setAttr('%s.fractionMode' % motion, True)
    
    position = cmds.xform(transform, q = True, ws = True, t = True)
    
    u_value = get_closest_parameter_on_curve(curve, position)
    u_value = get_curve_length_from_parameter(curve, u_value)
    
    curve_length = cmds.arclen(curve, ch = False)
    
    u_value = u_value/curve_length
    
    cmds.setAttr('%s.uValue' % motion, u_value)
    
    if not local:
        cmds.connectAttr('%s.worldSpace' % curve, '%s.geometryPath' % motion)
    if local:
        cmds.connectAttr('%s.local' % curve, '%s.geometryPath' % motion)
    
    locator = cmds.spaceLocator(n = 'locator_%s' % motion)[0]
    shapes = core.get_shapes(locator)
    if shapes:
        cmds.hide(shapes)
        
    cmds.connectAttr('%s.xCoordinate' % motion, '%s.translateX' % locator)
    cmds.connectAttr('%s.yCoordinate' % motion, '%s.translateY' % locator)
    cmds.connectAttr('%s.zCoordinate' % motion, '%s.translateZ' % locator)
    
    cmds.connectAttr('%s.rotateX' % motion, '%s.rotateX' % locator)
    cmds.connectAttr('%s.rotateY' % motion, '%s.rotateY' % locator)
    cmds.connectAttr('%s.rotateZ' % motion, '%s.rotateZ' % locator)
    
    cmds.connectAttr('%s.rotateOrder' % motion, '%s.rotateOrder' % locator)
    cmds.connectAttr('%s.message' % motion, '%s.specifiedManipLocation' % locator)
    
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
        cmds.parentConstraint(rivet.rivet, transform, mo = True)
    if not constrain:
        cmds.parent(transform, rivet.rivet)
    
    return rivet.rivet


def follicle_to_mesh(transform, mesh, u = None, v = None, constrain = False, constraint_type = 'parentConstraint', local = False):
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
    mesh = get_mesh_shape(mesh)
    
    position = cmds.xform(transform, q = True, ws = True, t = True)
    
    uv = u,v
    
    if u == None or v == None:
        uv = get_closest_uv_on_mesh(mesh, position)
        
    follicle = create_mesh_follicle(mesh, transform, uv)   
    
    if not constrain:
        cmds.parent(transform, follicle)
    if constrain:
        if not local:
            eval('cmds.%s("%s", "%s", mo = True)' % (constraint_type, follicle, transform))
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
    position = cmds.xform(transform, q = True, ws = True, t = True)

    uv = u,v

    if u == None or v == None:
        uv = get_closest_parameter_on_surface(surface, position)   

    follicle = create_surface_follicle(surface, transform, uv)
    
    if not constrain:
        cmds.parent(transform, follicle)
    if constrain:
        cmds.parentConstraint(follicle, transform, mo = True)
    
    return follicle


def curve_to_nurb_surface(curve):
    pass
    
def edges_to_curve(edges, description):
    """
    Given a list of edges create a curve.
    
    Args:
        edges (list): List of edge names, eg ['mesh_name.e[0]']
        description (str): The description to give the new curve. Name = 'curve_(description)'
        
    Returns:
        str: The name of the curve.
    """
    cmds.select(edges)

    curve =  cmds.polyToCurve(form = 2, degree = 3 )[0]
    
    curve = cmds.rename(curve, core.inc_name('curve_%s' % description))
    
    return curve
    
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
    
    for cv in cvs:
        
        cv_position = cmds.xform(cv, q = True, t = True, ws = True)
        closest_position = get_closest_position_on_mesh(mesh, cv_position)
        distance = vtool.util.get_distance(cv_position, closest_position)
        
        if not closest_distance:
            
            closest_distance = distance
            closest_position = cv_position
        
        if distance < closest_distance:
            closest_distance = distance
            closest_position = cv_position
            
        if distance == 0.00001:
            break
    
    cmds.delete(temp_curve)
    
    u,v = get_closest_uv_on_mesh(mesh, closest_position)
    
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

def get_closest_position_on_mesh(mesh, three_value_list):
    
    mesh_fn = api.MeshFunction(mesh)
    
    position = mesh_fn.get_closest_position(three_value_list)
    
    return position

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

def rebuild_curve(curve, spans, degree = 3):
    
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
    
def evenly_position_curve_cvs(curve, match_curve = None):
        
    cvs = cmds.ls('%s.cv[*]' % curve, flatten = True)
    
    if not match_curve:
        match_curve = curve
    
    snap_transforms_to_curve(cvs, curve)
        
def snap_transforms_to_curve(transforms, curve):
    
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
    
    faces = []
    
    for index in indices:
        faces.append('%s.f[%s]' % (mesh, index))
        
    return faces

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

def add_poly_smooth(mesh):
    """
    create a polySmooth node on the mesh.
    
    Args:
        mesh (str): The name of a mesh.
        
    Returns:
        str: The name of the poly smooth node.
    """
    poly_smooth = cmds.polySmooth(mesh, mth = 0, dv = 1, bnr = 1, c = 1, kb = 0, khe = 0, kt = 1, kmb = 1, suv = 1, peh = 0, sl = 1, dpe = 1, ps = 0.1, ro = 1, ch = 1)[0]
    
    return poly_smooth

def smooth_preview(mesh, bool_value = True):
    
    if bool_value == True:
        cmds.setAttr('%s.displaySmoothMesh' % mesh, 2)
        
    if bool_value == False:
        cmds.setAttr('%s.displaySmoothMesh' % mesh, 0)
        
def smooth_preview_all(bool_value = True):
    
    if core.is_batch():
        return
    
    meshes = cmds.ls(type = 'mesh')
    
    for mesh in meshes:
        
        intermediate = cmds.getAttr('%s.intermediateObject' % mesh)
         
        if intermediate == 0:
            smooth_preview(mesh, bool_value)
            
            
def randomize_mesh_vertices(mesh, range_min = 0.0, range_max = 0.1):
    #not tested
    verts = get_vertices(mesh)
    
    for vert in verts:
        cmds.move(uniform(range_min, range_max),uniform(range_min, range_max),uniform(range_min, range_max), vert, r = True)
        