# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

import maya.cmds as cmds

import maya.OpenMaya as OpenMaya
import maya.OpenMayaAnim as OpenMayaAnim

import vtool.util

#--- old api

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


def duplicate(node):
    
    dag_node = DagNode(node)
    dag_node.duplicate()
    
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
        
        for inc in range(0, length):
            numbers.append( self.api_object[inc] )
        
        return numbers

class PointArray(ApiObject):
    def _define_api_object(self):
        return OpenMaya.MPointArray()
    
    def get(self):
        values = []
        length = self.api_object.length()
        
        for inc in range(0, length):
            point = OpenMaya.MPoint()
            
            point = self.api_object[inc]
            
            part = [point.x,point.y,point.z]
            
            values.append(part)
            
        return values

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
    
    def get_uv_at_point(self, vector):
    
        point = Point(vector[0],vector[1],vector[2])
        
        uv = OpenMaya.MScriptUtil()
        uvPtr = uv.asFloat2Ptr()
        
        self.api_object.getUVAtPoint(point.get_api_object(), uvPtr)
        
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
        
        self.api_object.getCVs( point.get_api_object() )
        
        return point.get()
        
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
        
        point = self.api_object.closestPoint(point.get_api_object())
                
        return [point.x,point.y,point.z]
    
    def get_parameter_at_position(self, three_value_list):
        
        point = Point(three_value_list[0],
                      three_value_list[1],
                      three_value_list[2])     
        
        u = OpenMaya.MScriptUtil()   
        uPtr = u.asDoublePtr()
        OpenMaya.MScriptUtil.setDouble(uPtr, 0.0)
        
        space = OpenMaya.MSpace.kObject
        
        self.api_object.getParamAtPoint(point.get_api_object(), uPtr, 0.00001, space )
        
        return OpenMaya.MScriptUtil.getDouble(uPtr)
    
    def get_parameter_at_length(self, double):
        return self.api_object.findParamFromLength(double)

        
class IterateEdges(MayaIterator):
    def _define_api_object(self, mobject):
        return OpenMaya.MItMeshEdge(mobject)
    
    def get_vertices(self, edge_id):
        
        script_util = OpenMaya.MScriptUtil()
        prev = script_util.asIntPtr()
        
        self.api_object.setIndex(edge_id, prev)
        
        vert1_id = self.api_object.index(0)
        vert2_id = self.api_object.index(1)
        
        self.api_object.reset()
        return [vert1_id, vert2_id]
        

class IteratePolygonFaces(MayaIterator):
    
    def _define_api_object(self, mobject):
        return OpenMaya.MItMeshPolygon(mobject)
    
    def get_face_center_vectors(self):
        center_vectors = []
        
        for inc in range(0, self.api_object.count()):
            
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
        