# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

import vtool.util

if vtool.util.is_in_maya():
    import maya.cmds as cmds
    
    import maya.OpenMaya as OpenMaya
    import maya.OpenMayaAnim as OpenMayaAnim
    import maya.OpenMayaUI as OpenMayaUI
    
allow_save = False
    
def start_check_after_save(function):
    
    try:
        #function should accept arguments, clientData
        id = OpenMaya.MSceneMessage.addCallback(OpenMaya.MSceneMessage.kAfterSave, function)
    except:
        pass
    
#--- old api

def attribute_to_plug(attribute_name):
    plug = OpenMaya.MPlug()
    selection = OpenMaya.MSelectionList()
    selection.add(attribute_name)
    selection.getPlug(0, plug)

    return plug

def nodename_to_mobject(object_name):
    """
    Initialize an MObject of the named node.
    """
    
    if not cmds.objExists(object_name):
        return
    
    selection_list = SelectionList()
    selection_list.create_by_name(object_name)
        
    if cmds.objectType(object_name, isAType = 'transform') or cmds.objectType(object_name, isAType = 'shape'):
        return selection_list.get_deg_path(0)
    
    return selection_list.get_at_index(0) 

def create_mesh_from_mesh(mesh, target_transform):
    """
    Create a mesh from the shape node of another mesh, without duplicating.
    
    Args:
        mesh (str): The name of a mesh.
        target_transform (str): The transform where the newly created mesh should live.
    """
    mesh_fn = OpenMaya.MFnMesh()
    shape = nodename_to_mobject(mesh)

    transform = nodename_to_mobject(target_transform)
    mesh_fn.copy(shape.node(), transform.node())

def duplicate(node):
    """
    Api duplicate. Faster than cmds.duplicate, but no undo in python script.
    """
    dag_node = DagNode(node)
    value = dag_node.duplicate()
    return value
    
def get_3D_position_from_x_y():
    pass
    #omui.M3dView().active3dView().viewToWorld(int(vpX)     , int(vpY), pos, direction)

def get_current_camera():
    
    camera = OpenMaya.MDagPath()
    
    OpenMayaUI.M3dView().active3dView().getCamera(camera)
    
    return camera.fullPathName()
    

class ApiObject(object):
    """
    A wrapper object for MObjects.
    """
    
    def __init__(self):
        self.api_object = self._define_api_object()
        
    def __call__(self):
        return self.api_object
        
    def _define_api_object(self):
        return 
        
    def get_api_object(self):
        return self.api_object
        
    def get(self):
        return

class MayaObject(ApiObject):
    """
    Wrapper for Api MObject
    """
    
    def __init__(self, mobject = None):

        if type(mobject) == str or type(mobject) == unicode:
            mobject = nodename_to_mobject(mobject)
            self.api_object = self._define_api_object(mobject)
        
        if mobject:
            self.api_object = self._define_api_object(mobject)
            
        if not mobject:
            self.api_object = OpenMaya.MObject()
            
        self.mobject = mobject

    def _define_api_object(self, mobject):
        return mobject 
    
    def set_node_as_mobject(self, node_name):
        """
        set the MObject from a node name.
        
        Args:
            node_name (str): The name of a node.
        """
        mobject = nodename_to_mobject(node_name)
            
        self.api_object = self._define_api_object(mobject)
        
    
class MayaIterator(MayaObject):
    pass
    
class MayaFunction(MayaObject):
    pass

class DoubleArray(ApiObject):
    def _define_api_object(self):
        return OpenMaya.MDoubleArray()
    
    def get(self):
        numbers = []
        
        length = self.api_object.length()
        
        for inc in xrange(0, length):
            numbers.append( self.api_object[inc] )
        
        return numbers

class PointArray(ApiObject):
    def _define_api_object(self):
        return OpenMaya.MPointArray()
    
    def get(self):
        values = []
        length = self.api_object.length()
        
        for inc in xrange(0, length):
            point = OpenMaya.MPoint()
            
            point = self.api_object[inc]
            
            part = [point.x,point.y,point.z]
            
            values.append(part)
            
        return values
    
    def set(self, positions):
        
        for inc in range(0, len(positions)):
            self.api_object.set(inc, positions[inc][0], positions[inc][1], positions[inc][2])
            
    def length(self):
        return self.api_object.length()

class Point(ApiObject):
    def __init__(self, x = 0, y = 0, z = 0, w = 1):
        self.api_object = self._define_api_object(x,y,z,w)
        
    def _define_api_object(self, x, y, z, w):
        return OpenMaya.MPoint(x,y,z,w)
            
    def get(self):
        return [self.api_object.x, self.api_object.y, self.api_object.z, self.api_object.w]
    
class SelectionList(ApiObject):
    def _define_api_object(self):
        return OpenMaya.MSelectionList()
        
    def create_by_name(self, name):
        
        try:
            self.api_object.add(name)
        except:
            cmds.warning('Could not add %s into selection list' % name)
            return
        
    def get_at_index(self, index = 0):
        
        mobject = MayaObject()
        
        try:
            self.api_object.getDependNode(0, mobject())
            return mobject()
        except:
            cmds.warning('Could not get mobject at index %s' % index)
            return
        
    def get_deg_path(self, index):
        
        nodeDagPath = OpenMaya.MDagPath()
        self.api_object.getDagPath(0, nodeDagPath)
        
        return nodeDagPath
   
class TransformFunction(MayaFunction):
    
    def _define_api_object(self, mobject):
        return OpenMaya.MFnTransform(mobject)
    
    def get_transformation_matrix(self):
        
        return self.api_object.transformation()
    
    def get_matrix(self):
        
        transform_matrix = self.get_transformation_matrix()
        return transform_matrix.asMatrix()
    
    def get_vector_matrix_product(self, vector):
        
        vector_api = OpenMaya.MVector()
        vector_api.x = vector[0]
        vector_api.y = vector[1]
        vector_api.z = vector[2]
        
        space = OpenMaya.MSpace.kWorld
        orig_vector = self.api_object.getTranslation(space)
        
        vector_api *= self.get_matrix()
        
        vector_api += orig_vector
        
        return vector_api.x, vector_api.y, vector_api.z
    
class MeshFunction(MayaFunction):
    
    def _define_api_object(self, mobject):
        return OpenMaya.MFnMesh(mobject)
    
    def get_vertex_positions(self):
        
        point_array = PointArray()
        
        self.api_object.getPoints(point_array.api_object, OpenMaya.MSpace.kWorld)

        return point_array.get()
    
    def set_vertex_positions(self, positions):
        
        point_array = PointArray()
        for pos in positions:
            point_array.api_object.append(*pos)
        
        
        self.api_object.setPoints(point_array.api_object, OpenMaya.MSpace.kWorld)
    
    def get_uv_at_point(self, vector):
    
        api_space = OpenMaya.MSpace.kWorld
    
        point = Point(vector[0],vector[1],vector[2])
        
        uv = OpenMaya.MScriptUtil()
        uvPtr = uv.asFloat2Ptr()
        
        self.api_object.getUVAtPoint(point.get_api_object(), uvPtr, api_space)
        
        u = OpenMaya.MScriptUtil.getFloat2ArrayItem(uvPtr, 0, 0)
        v = OpenMaya.MScriptUtil.getFloat2ArrayItem(uvPtr, 0, 1)
        
        return u,v
    
    def get_point_at_uv(self, u_value = 0, v_value = 0):
        """
            Not implemented
        """
        
            
        point = Point(0.0,0.0,0.0)
        point = point.get_api_object()
        
        
        util = OpenMaya.MScriptUtil()
        util.createFromList([float(u_value), float(v_value)], 2)
        uv = util.asFloat2Ptr()
        
        #point = None
        #uv = None
        # need to get the polygon id...
        polygon_id = 0
        self.api_object.getPointAtUV(polygon_id, point, uv, OpenMaya.MSpace.kWorld)
    
    def get_closest_face(self, vector):
        
        pointA = OpenMaya.MPoint(vector[0], vector[1], vector[2])
        pointB = OpenMaya.MPoint()
        space = OpenMaya.MSpace.kWorld
         
        util = OpenMaya.MScriptUtil()
        #util.createFromInt(0)
        idPointer = util.asIntPtr()
         
        self.api_object.getClosestPoint(pointA, pointB, space, idPointer)  
        idx = OpenMaya.MScriptUtil(idPointer).asInt()
               
        
        return idx
    
    def get_closest_position(self, source_vector):
    
        new_point = OpenMaya.MPoint()
    
        point_base = OpenMaya.MPoint()
        point_base.x = source_vector[0]
        point_base.y = source_vector[1]
        point_base.z = source_vector[2]
        
        accelerator = self.api_object.autoUniformGridParams()
        space = OpenMaya.MSpace.kWorld
                        
        self.api_object.getClosestPoint(point_base,new_point,space, None, accelerator )
        
        return [new_point.x, new_point.y, new_point.z]
        
    def get_closest_intersection(self, source_vector, direction_vector):
        
        point_base = OpenMaya.MFloatPoint()
        point_base.x = source_vector[0]
        point_base.y = source_vector[1]
        point_base.z = source_vector[2]
        
        float_base = OpenMaya.MFloatVector()
        float_base.x = source_vector[0]
        float_base.y = source_vector[1]
        float_base.z = source_vector[2]
        
        point_direction = OpenMaya.MFloatVector()
        point_direction.x = direction_vector[0]
        point_direction.y = direction_vector[1]
        point_direction.z = direction_vector[2]
        
        point_direction = point_direction - float_base
        
        accelerator = self.api_object.autoUniformGridParams()
        space = OpenMaya.MSpace.kWorld
        
        
        hit_point = OpenMaya.MFloatPoint()
        
        hit_double = OpenMaya.MScriptUtil()   
        hit_param_ptr = hit_double.asFloatPtr()
               
        hit_face = OpenMaya.MScriptUtil()
        hit_face_ptr = hit_face.asIntPtr()
        
        hit_triangle = OpenMaya.MScriptUtil()
        hit_triangle_ptr = hit_triangle.asIntPtr()
        
        hit_bary1 = OpenMaya.MScriptUtil()   
        hit_bary1_ptr = hit_bary1.asFloatPtr()
        
        hit_bary2 = OpenMaya.MScriptUtil()   
        hit_bary2_ptr = hit_bary2.asFloatPtr()
                        
        self.api_object.closestIntersection(point_base, point_direction, None, None, False, space, 100000, False, accelerator, 
                                            hit_point, hit_param_ptr, hit_face_ptr, hit_triangle_ptr,
                                            hit_bary1_ptr, hit_bary2_ptr)
        
        return [hit_point.x, hit_point.y, hit_point.z]
   
    def refresh_mesh(self):
        
        self.api_object.updateSurface()
        
    def copy(self, source_mesh, transform):
        
        mesh_object = nodename_to_mobject(source_mesh)
        
        self.api_object.copy(mesh_object, transform)
        
    def get_number_of_vertices(self):
        
        return self.api_object.numVertices()
        
    
    def get_number_of_edges(self):
        
        return self.api_object.numEdges()
    
    def get_number_of_faces(self):
        
        return self.api_object.numPolygons()
    
    def get_number_of_uvs(self):
        
        return self.api_object.nunUVs()
    
    def get_number_of_triangles(self):
        
        triangles, triangle_verts = OpenMaya.MIntArray(), OpenMaya.MIntArray()
        
        self.api_object.getTriangles(triangles, triangle_verts)
        
        count = 0
        
        for triangle in triangles:
            if triangle == 1:
                count += 1
                
        return count
    
    def get_triangle_ids(self):
        
        triangles, triangle_verts = OpenMaya.MIntArray(), OpenMaya.MIntArray()
        
        self.api_object.getTriangles(triangles, triangle_verts)
        
        id_list = []
        
        for inc in range(0, len(triangles)):
            if triangles[inc] == 1:
                id_list.append(inc)
                
        return id_list
    
    def get_quad_ids(self):
        
        triangles, triangle_verts = OpenMaya.MIntArray(), OpenMaya.MIntArray()
        
        self.api_object.getTriangles(triangles, triangle_verts)
        
        id_list = []
        
        for inc in range(0, len(triangles)):
            if triangles[inc] == 2:
                id_list.append(inc)
                
        return id_list
    
    def get_non_tri_quad_ids(self):
    
        triangles, triangle_verts = OpenMaya.MIntArray(), OpenMaya.MIntArray()
        
        self.api_object.getTriangles(triangles, triangle_verts)
        
        id_list = []
        
        for inc in range(0, len(triangles)):
            if triangles[inc] > 2:
                id_list.append(inc)
                
        return id_list
    
class NurbsSurfaceFunction(MayaFunction):
    def _define_api_object(self, mobject):
        return OpenMaya.MFnNurbsSurface(mobject)
            
    def get_closest_parameter(self, vector):
        
        point = Point( vector[0],
                       vector[1],
                       vector[2] )
                
        u = OpenMaya.MScriptUtil()   
        uPtr = u.asDoublePtr()
        OpenMaya.MScriptUtil.setDouble(uPtr, 0.0)
        
        v = OpenMaya.MScriptUtil()   
        vPtr = v.asDoublePtr()
        OpenMaya.MScriptUtil.setDouble(vPtr, 0.0)
                
        space = OpenMaya.MSpace.kObject
        
        self.api_object.closestPoint(point.get_api_object(), 0, uPtr, vPtr, 0, 0.00001, space)
        
        
        
        u = OpenMaya.MScriptUtil.getDouble(uPtr)
        v = OpenMaya.MScriptUtil.getDouble(vPtr)
        
        return u,v
            
class NurbsCurveFunction(MayaFunction):
    def _define_api_object(self, mobject):
        return OpenMaya.MFnNurbsCurve(mobject)
            
    def get_degree(self):
        return self.api_object.degree()
    
    def get_cv_count(self):
        return self.api_object.numCVs()
        
    def get_cv_positions(self):
        point = PointArray()
        point = point.get_api_object()
        
        self.api_object.getCVs( point )
        
        found = []
        
        for inc in xrange(0, point.length()):
        
            x = point[inc][0]
            y = point[inc][1]
            z = point[inc][2]
            
            found.append([x,y,z])
        
        return found
    
    def set_cv_positions(self, positions):
        
        point_array = PointArray()
        point_array.set(positions)
        
        self.api_object.setCVs(point_array)
        
    def get_form(self):
        return self.api_object.form()
    
    def get_knot_count(self):
        return self.api_object.numKnots()
    
    def get_span_count(self):
        return self.api_object.numSpans()
    
    def get_knot_values(self):
        knots = DoubleArray()
        
        self.api_object.getKnots( knots.get_api_object() )
        
        return knots.get()

    def get_position_at_parameter(self, param):
        
        point = Point()
        
        self.api_object.getPointAtParam(param, point.get_api_object() )
        return point.get()[0:3]

    def get_closest_position(self, three_value_list):
        
        point = Point( three_value_list[0],
                       three_value_list[1],
                       three_value_list[2] )
        
        point = self.api_object.closestPoint(point.get_api_object(), None, 0.0000001, OpenMaya.MSpace.kWorld)
                
        return [point.x,point.y,point.z]
    
    def get_parameter_at_position(self, three_value_list):
        
             
        
        u = OpenMaya.MScriptUtil()   
        uPtr = u.asDoublePtr()
        OpenMaya.MScriptUtil.setDouble(uPtr, 0.0)
        
        #space = OpenMaya.MSpace.kObject
        space = OpenMaya.MSpace.kWorld
        
        #self.api_object.getParamAtPoint(point.get_api_object(), uPtr, 0.00001, space )
                        
        three_value_list = self.get_closest_position(three_value_list)
        
        point = Point(three_value_list[0],
                      three_value_list[1],
                      three_value_list[2])
        
        self.api_object.getParamAtPoint(point.get_api_object(), uPtr, space )
        
        return OpenMaya.MScriptUtil.getDouble(uPtr)
    
    def get_parameter_at_length(self, double):
        return self.api_object.findParamFromLength(double)
    

class SkinClusterFunction(MayaFunction):
    def _define_api_object(self, mobject):
        return OpenMayaAnim.MFnSkinCluster(mobject)

    def get_influence_dag_paths(self):
        
        path_array = OpenMaya.MDagPathArray()
        
        self.api_object.influenceObjects(path_array)
        
        return path_array
    
    def get_influence_names(self, short_name = False):
        
        influence_dag_paths = self.get_influence_dag_paths()
        
        influence_names = []
        
        for x in xrange( influence_dag_paths.length() ):
            
            if not short_name:
                influence_path_name = influence_dag_paths[x].fullPathName()
            if short_name:
                influence_path_name = influence_dag_paths[x].partialPathName()
                
            influence_names.append(influence_path_name)  
            
        return influence_names      
        
    def get_influence_indices(self):

        influence_dag_paths = self.get_influence_dag_paths()
        
        influence_ids = []
        
        for x in xrange( influence_dag_paths.length() ):
            
            influence_id = int(self.api_object.indexForInfluenceObject(influence_dag_paths[x]))
            influence_ids.append(influence_id)  
            
        return influence_ids 
    
    def get_influence_dict(self, short_name = False):
        
        influence_dag_paths = self.get_influence_dag_paths()
        
        influence_ids = {}
        influence_names = []
        
        for x in xrange( influence_dag_paths.length() ):
            
            influence_path = influence_dag_paths[x]
            if not short_name:
                influence_path_name = influence_dag_paths[x].fullPathName()
            if short_name:
                influence_path_name = influence_dag_paths[x].partialPathName()
                
            influence_id = int(self.api_object.indexForInfluenceObject(influence_path))
            influence_ids[influence_path_name] = influence_id
            influence_names.append(influence_path_name)
            
        return influence_ids, influence_names
    
    def get_index_at_influence(self, influence_name):
        
        dag_node = DagNode()
        dag_node.set_node_as_mobject(influence_name)
        dag_path = dag_node.api_object.dagPath()
        
        influence_id = self.api_object.indexForInfluenceObject(dag_path)
        return influence_id
    
    def get_skin_weights_dict(self):
        
        weight_list_plug = self.api_object.findPlug('weightList')
        weights_plug = self.api_object.findPlug('weights')
        weight_list_attr = weight_list_plug.attribute()
        weights_attr = weights_plug.attribute()
        weight_influence_ids = OpenMaya.MIntArray()
        
        weights = {}
        
        vert_count = weight_list_plug.numElements()
        
        for vertex_id in xrange(vert_count):
        
            weights_plug.selectAncestorLogicalIndex(vertex_id, weight_list_attr)
            
            weights_plug.getExistingArrayAttributeIndices(weight_influence_ids)
        
            influence_plug = OpenMaya.MPlug(weights_plug)
            for influence_id in weight_influence_ids:
                
                influence_plug.selectAncestorLogicalIndex(influence_id, weights_attr)
                
                if not influence_id in weights:
                    weights[influence_id] = [0] * vert_count
                
                try:
                    value = influence_plug.asDouble()
                    weights[influence_id][vertex_id] = value
                    
                except KeyError:
                    # assumes a removed influence
                    pass
                
        return weights   

class IterateCurveCV(MayaIterator):
    def _define_api_object(self, mobject):
        return OpenMaya.MItCurveCV 

class IterateGeometry(MayaIterator):
    def _define_api_object(self, mobject):
        return OpenMaya.MItGeometry(mobject)

    def get_points(self):
        
        space = OpenMaya.MSpace.kObject
        points = OpenMaya.MPointArray()
        
        self.api_object.allPositions(points, space)
        return points 
    
    def set_points(self, points):
        space = OpenMaya.MSpace.kObject
        self.api_object.setAllPositions(points, space)
        
    def get_points_as_list(self):
        
        points = self.get_points()
        
        found = []
        
        for inc in xrange(0, points.length()):
        
            x = points[inc][0]
            y = points[inc][1]
            z = points[inc][2]
            
            found.append([x,y,z])
            
            #if inc == 1000:
            #    break
        
        return found
        
class IterateEdges(MayaIterator):
    def _define_api_object(self, mobject):
        return OpenMaya.MItMeshEdge(mobject)
    
    def set_edge(self, edge_id):
        script_util = OpenMaya.MScriptUtil()
        prev = script_util.asIntPtr()
        
        self.api_object.setIndex(edge_id, prev)
        
        return prev
    
    def get_connected_vertices(self, edge_id):
        
        self.set_edge(edge_id)
        
        vert1_id = self.api_object.index(0)
        vert2_id = self.api_object.index(1)
        
        self.api_object.reset()
        return [vert1_id, vert2_id]
    
    def get_connected_faces(self, edge_id):
        
        self.set_edge(edge_id)
        
        int_array = OpenMaya.MIntArray()
        
        self.api_object.getConnectedFaces(int_array)
        
        return int_array
    
    def get_connected_edges(self, edge_id):
        
        self.set_edge(edge_id)
        
        int_array = OpenMaya.MIntArray()
        
        self.api_object.getConnectedEdges(int_array)
        
        return int_array

class IteratePolygonFaces(MayaIterator):
    
    def _define_api_object(self, mobject):
        return OpenMaya.MItMeshPolygon(mobject)
    
    def get_face_center_vectors(self):
        center_vectors = []
        
        for inc in xrange(0, self.api_object.count()):
            
            point = self.api_object.center()
            
            center_vectors.append([point.x,point.y,point.z] )
            
            self.api_object.next()
        
        self.api_object.reset()
        
        return center_vectors
            
    def get_closest_face(self, vector):
        
        closest_distance = None
        closest_face = None
        
        while not self.api_object.isDone():
            center = self.api_object.center()
            
            distance = vtool.util.get_distance(vector, [center.x,center.y,center.z])
            
            if distance < 0.001:
                closest_face = self.api_object.index()
                self.api_object.reset()
                return closest_face
            
            if distance < closest_distance or not closest_distance:
                closest_distance = distance
                closest_face = self.api_object.index()
                
            self.api_object.next()
        
        self.api_object.reset()
        return closest_face

    def get_edges(self, face_id):
        
        script_util = OpenMaya.MScriptUtil()
        prev = script_util.asIntPtr()
        self.api_object.setIndex(face_id, prev)
        
        int_array = OpenMaya.MIntArray()
        self.api_object.getEdges(int_array)
        
        self.api_object.reset()
        return int_array
    
    def get_center(self, face_id):
        
        #point = OpenMaya.MPoint()
        script_util = OpenMaya.MScriptUtil()
        prev = script_util.asIntPtr()
        
        self.api_object.setIndex(face_id, prev)
        
        point = self.api_object.center()
        
        return point.x, point.y, point.z
    
class KeyframeFunction(MayaFunction):
    
    constant = None
    linear = None
    cycle = None
    cycle_relative = None
    oscillate = None
    
    
    def _define_api_object(self, mobject):
        api_object = OpenMayaAnim.MFnAnimCurve(mobject)
        
        self.constant = api_object.kConstant
        self.linear = api_object.kLinear
        self.cycle = api_object.kCycle
        self.cycle_relative = api_object.kCycleRelative
        self.oscillate = api_object.kOscillate
        
        return api_object
        
    
    def set_post_infinity(self, infinity_type):
        
        self.api_object.setPostInfinityType(infinity_type)
        
    def set_pre_infinity(self, infinity_type):
        
        self.api_object.setPreInfinityType(infinity_type)

class DagNode(MayaFunction):
    
    def _define_api_object(self, mobject):
        
        return OpenMaya.MFnDagNode(mobject)
    
    def duplicate(self):
        
        self.api_object.duplicate()
        
    def get_name(self):
        pass
    
    def get_long_name(self):
        pass
        
