# Copyright (C) 2024 Louis Vottero louis.vot@gmail.com    All rights reserved.

from __future__ import absolute_import

import math

from .. import util
from .. import util_math

if util.is_in_maya():
    import maya.cmds as cmds

    import maya.OpenMaya as OpenMaya
    import maya.OpenMayaAnim as OpenMayaAnim
    import maya.OpenMayaUI as OpenMayaUI

    import maya.api.OpenMaya as om
    import maya.api.OpenMayaAnim as omAnim

allow_save = False

after_save_callback = None


def exists(name):
    sel = OpenMaya.MSelectionList()

    try:
        sel.add(name)
        return True
    except RuntimeError:
        return False


def start_check_after_save(function):
    global after_save_callback

    if after_save_callback is not None:
        try:
            OpenMaya.MSceneMessage.removeCallback(after_save_callback)
        except:
            pass

    try:
        # function should accept arguments, clientData
        callback_id = OpenMaya.MSceneMessage.addCallback(OpenMaya.MSceneMessage.kAfterSave, function)
        after_save_callback = callback_id
    except:
        pass


def remove_check_after_save():
    global after_save_callback

    if after_save_callback:
        OpenMaya.MSceneMessage.removeCallback(after_save_callback)

# --- old api


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

    if not exists(object_name):
        return

    selection_list = SelectionList()
    selection_list.create_by_name(object_name)

    if cmds.objectType(object_name, isAType='transform') or cmds.objectType(object_name, isAType='shape'):
        return selection_list.get_deg_path(0)

    return selection_list.get_at_index(0)


def create_mesh_from_mesh(mesh, target_transform):
    """
    Create a mesh from the shape node of another mesh, without duplicating.

    Args:
        mesh (str): The name of a mesh.
        target_transform (str): The transform where the newly created mesh should live.
    """

    mesh = get_object(mesh)
    transform = get_object(target_transform)

    mesh_fn = om.MFnMesh()

    result = mesh_fn.copy(mesh.node(), transform.node())

    return get_object_name(result)


def duplicate(node):
    """
    Api duplicate. Faster than cmds.duplicate, but no undo in python script.
    """
    dag_node = DagNode(node)
    value = dag_node.duplicate()
    return value


def get_current_camera():
    camera = OpenMaya.MDagPath()

    OpenMayaUI.M3dView().active3dView().getCamera(camera)

    return camera.fullPathName()


def set_current_camera(camera_name):
    view = OpenMayaUI.M3dView.active3dView()

    if cmds.nodeType(camera_name) == 'transform':
        shapes = cmds.listRelatives(camera_name, shapes=True)

        if shapes and cmds.nodeType(shapes[0]) == 'camera':
            camera_name = shapes[0]

    mobject = nodename_to_mobject(camera_name)

    cam = OpenMaya.MDagPath(mobject)

    view.setCamera(cam)

    cmds.refresh()


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

    def __init__(self, mobject=None):

        if util.is_str(mobject):
            mobject = nodename_to_mobject(mobject)

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

        for inc in range(0, length):
            numbers.append(self.api_object[inc])

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

            part = [point.x, point.y, point.z]

            values.append(part)

        return values

    def set(self, positions):

        for inc in range(0, len(positions)):
            self.api_object.set(inc, positions[inc][0], positions[inc][1], positions[inc][2])

    def length(self):
        return self.api_object.length()


class Point(ApiObject):

    def __init__(self, x=0, y=0, z=0, w=1):
        self.api_object = self._define_api_object(x, y, z, w)

    def _define_api_object(self, x, y, z, w):
        return OpenMaya.MPoint(x, y, z, w)

    def get(self):
        return [self.api_object.x, self.api_object.y, self.api_object.z, self.api_object.w]

    def get_as_vector(self):
        return [self.api_object.x, self.api_object.y, self.api_object.z]


class FloatPoint(ApiObject):

    def __init__(self, x=0, y=0, z=0, w=1):
        self.api_object = self._define_api_object(x, y, z, w)

    def _define_api_object(self, x, y, z, w):
        return OpenMaya.MFloatPoint(x, y, z, w)

    def get(self):
        return [self.api_object.x, self.api_object.y, self.api_object.z, self.api_object.w]

    def get_as_vector(self):
        return [self.api_object.x, self.api_object.y, self.api_object.z]


class Matrix(ApiObject):

    def __init__(self, matrix_list=None):
        if matrix_list is None:
            matrix_list = []
        self.api_object = self._define_api_object(matrix_list)

    def _define_api_object(self, matrix_list=None):
        if matrix_list is None:
            matrix_list = []
        matrix = OpenMaya.MMatrix()

        if matrix_list:
            OpenMaya.MScriptUtil.createMatrixFromList(matrix_list, matrix)

        return matrix

    def set_matrix_from_list(self, matrix_list):
        OpenMaya.MScriptUtil.createMatrixFromList(matrix_list, self.api_object)


class Quaternion(ApiObject):

    def __init__(self, angle=None, vector=None):

        if vector is None:
            vector = []
        self.api_object = self._define_api_object(angle, vector)

    def _define_api_object(self, angle=None, vector=None):

        if vector is None:
            vector = []
        angle = math.radians(angle)

        if angle and vector:
            api_vector = OpenMaya.MVector()
            api_vector.x = vector[0]
            api_vector.y = vector[1]
            api_vector.z = vector[2]

            return OpenMaya.MQuaternion(angle, api_vector)

        if not angle and vector:
            return OpenMaya.MQuaternion()

    def rotation(self):

        rot = self.api_object.asEulerRotation()

        rotation = [math.degrees(rot[0]), math.degrees(rot[1]), math.degrees(rot[2])]

        return rotation


class TransformationMatrix(ApiObject):

    def __init__(self, matrix):
        self.api_object = self._define_api_object(matrix)

    def _define_api_object(self, matrix=None):
        tmatrix = None
        if matrix:
            tmatrix = OpenMaya.MTransformationMatrix(matrix)

        if not matrix:
            tmatrix = OpenMaya.MTransformationMatrix()

        return tmatrix

    def translation(self, open_maya_space=None):
        space = None
        if not open_maya_space:
            space = OpenMaya.MSpace.kWorld
        if open_maya_space:
            space = open_maya_space

        translation = self.api_object.getTranslation(space)

        return [translation[0], translation[1], translation[2]]

    def rotation(self):

        rotation = self.api_object.rotation().asEulerRotation()
        return [math.degrees(rotation[0]), math.degrees(rotation[1]), math.degrees(rotation[2])]


class SelectionList(ApiObject):

    def _define_api_object(self):
        return OpenMaya.MSelectionList()

    def create_by_name(self, name):

        try:
            self.api_object.add(name)
        except:
            cmds.warning('Could not add %s into selection list' % name)
            return

    def get_at_index(self, index=0):

        mobject = MayaObject()

        try:
            self.api_object.getDependNode(0, mobject())
            return mobject()
        except:
            cmds.warning('Could not get mobject at index %s' % index)
            return

    def get_deg_path(self, index):
        node_dag_path = OpenMaya.MDagPath()
        self.api_object.getDagPath(0, node_dag_path)
        return node_dag_path


class TransformFunction(MayaFunction):

    def _define_api_object(self, mobject):
        return OpenMaya.MFnTransform(mobject)

    def get_transformation_matrix(self):
        return self.api_object.transformation()

    def get_matrix(self):
        transform_matrix = self.get_transformation_matrix()
        return transform_matrix.asMatrix()

    def get_vector_matrix_product(self, vector):
        """
        Not working as expected, need to work on it.
        """
        util.warning('get_vector_matrix_product does not work... yet')
        vector_api = OpenMaya.MVector()
        vector_api.x = vector[0]
        vector_api.y = vector[1]
        vector_api.z = vector[2]

        space = OpenMaya.MSpace.kWorld
        orig_vector = self.api_object.getTranslation(space)

        vector_api *= self.get_matrix()

        vector_api += orig_vector

        return vector_api.x, vector_api.y, vector_api.z


class JointFunction(MayaFunction):

    def _define_api_object(self, mobject):
        return OpenMayaAnim.MFnIkJoint(mobject)

    def get_orient_matrix(self, as_list=False):

        quat = OpenMaya.MQuaternion()
        self.api_object.getOrientation(quat)
        matrix = quat.asMatrix()

        if not as_list:
            return matrix

        if as_list:

            found = []

            for inc in range(0, 4):
                for inc2 in range(0, 4):
                    found.append(matrix(inc, inc2))

            return found

    def get_inverse_orient_matrix(self, as_list=False):

        matrix = self.get_orient_matrix()
        matrix = matrix.inverse()

        if not as_list:
            return matrix

        if as_list:

            found = []

            for inc in range(0, 4):
                for inc2 in range(0, 4):
                    found.append(matrix(inc, inc2))

            return found


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

        point = Point(vector[0], vector[1], vector[2])

        uv = OpenMaya.MScriptUtil()
        uv_ptr = uv.asFloat2Ptr()

        self.api_object.getUVAtPoint(point.get_api_object(), uv_ptr, api_space)

        u = OpenMaya.MScriptUtil.getFloat2ArrayItem(uv_ptr, 0, 0)
        v = OpenMaya.MScriptUtil.getFloat2ArrayItem(uv_ptr, 0, 1)

        return u, v

    def get_closest_face(self, vector):

        point_a = OpenMaya.MPoint(vector[0], vector[1], vector[2])
        point_b = OpenMaya.MPoint()
        space = OpenMaya.MSpace.kWorld

        m_script_util = OpenMaya.MScriptUtil()
        id_pointer = m_script_util.asIntPtr()

        self.api_object.getClosestPoint(point_a, point_b, space, id_pointer)
        idx = OpenMaya.MScriptUtil(id_pointer).asInt()

        return idx

    def get_closest_position(self, source_vector):

        new_point = OpenMaya.MPoint()

        point_base = OpenMaya.MPoint()
        point_base.x = source_vector[0]
        point_base.y = source_vector[1]
        point_base.z = source_vector[2]

        accelerator = self.api_object.autoUniformGridParams()
        space = OpenMaya.MSpace.kWorld

        self.api_object.getClosestPoint(point_base, new_point, space, None, accelerator)

        return [new_point.x, new_point.y, new_point.z]

    def get_closest_normal(self, source_vector, at_source_position=False):
        """
        source_vector is the position to find the normal closest at_source_position just means to add that
            source_vector to the normal vector, so it is returned relative to the source vector
        """
        new_point = OpenMaya.MVector()

        point_base = OpenMaya.MPoint()
        point_base.x = source_vector[0]
        point_base.y = source_vector[1]
        point_base.z = source_vector[2]

        accelerator = self.api_object.autoUniformGridParams()
        space = OpenMaya.MSpace.kWorld

        self.api_object.getClosestNormal(point_base, new_point, space, None, accelerator)

        if not at_source_position:
            return [new_point.x, new_point.y, new_point.z]
        if at_source_position:
            position = util_math.vector_add(source_vector, new_point)
            return position

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

        self.api_object.closestIntersection(point_base, point_direction, None, None, False, space, 100000, False,
                                            accelerator,
                                            hit_point, hit_param_ptr, hit_face_ptr, hit_triangle_ptr,
                                            hit_bary1_ptr, hit_bary2_ptr)

        return [hit_point.x, hit_point.y, hit_point.z]

    def get_closest_intersection_face(self, source_vector, direction_vector, max_distance=10000):

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

        self.api_object.closestIntersection(point_base, point_direction, None, None, False, space, max_distance, False,
                                            accelerator,
                                            hit_point, hit_param_ptr, hit_face_ptr, hit_triangle_ptr,
                                            hit_bary1_ptr, hit_bary2_ptr)

        face_index = OpenMaya.MScriptUtil.getInt(hit_face_ptr)
        return face_index

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


class MeshIntersector(MayaFunction):

    def _define_api_object(self, mobject):
        intersector = OpenMaya.MMeshIntersector()
        matrix = mobject.inclusiveMatrix()
        node = mobject.node()

        intersector.create(node, matrix)

        return intersector

    def get_closest_point_barycentric(self, source_vector):
        point = Point(source_vector[0], source_vector[1], source_vector[2])

        point_info = OpenMaya.MPointOnMesh()
        u_util = OpenMaya.MScriptUtil(0.0)
        u_ptr = u_util.asFloatPtr()
        v_util = OpenMaya.MScriptUtil(0.0)
        v_ptr = v_util.asFloatPtr()

        point_info.getBarycentricCoords(u_ptr, v_ptr)
        self.api_object.getClosestPoint(point.api_object, point_info)
        point_info.getBarycentricCoords(u_ptr, v_ptr)

        u = u_util.getFloat(u_ptr)
        v = u_util.getFloat(v_ptr)
        triangle_id = point_info.triangleIndex()
        face_id = point_info.faceIndex()

        return u, v, face_id, triangle_id


class NurbsSurfaceFunction(MayaFunction):

    def _define_api_object(self, mobject):
        return OpenMaya.MFnNurbsSurface(mobject)

    def get_closest_parameter(self, vector):

        point = Point(vector[0],
                      vector[1],
                      vector[2])

        u = OpenMaya.MScriptUtil()
        u_ptr = u.asDoublePtr()
        OpenMaya.MScriptUtil.setDouble(u_ptr, 0.0)

        v = OpenMaya.MScriptUtil()
        v_ptr = v.asDoublePtr()
        OpenMaya.MScriptUtil.setDouble(v_ptr, 0.0)

        space = OpenMaya.MSpace.kObject

        self.api_object.closestPoint(point.get_api_object(), 0, u_ptr, v_ptr, 0, 0.00001, space)

        u = OpenMaya.MScriptUtil.getDouble(u_ptr)
        v = OpenMaya.MScriptUtil.getDouble(v_ptr)

        return u, v

    def get_closest_normal(self, source_vector, at_source_position=False):

        space = OpenMaya.MSpace.kWorld

        uv = self.get_closest_parameter(source_vector)

        mvector = self.api_object.normal(uv[0], uv[1], space)

        vector = [mvector.x, mvector.y, mvector.z]

        if not at_source_position:
            return vector
        if at_source_position:
            position = util_math.vector_add(source_vector, vector)
            return position

    def get_position_from_parameter(self, u_value, v_value):

        point = Point()

        space = OpenMaya.MSpace.kWorld

        self.api_object.getPointAtParam(u_value, v_value, point.api_object, space)

        return point.get_as_vector()


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

        self.api_object.getCVs(point)

        found = []

        for inc in range(0, point.length()):
            x = point[inc][0]
            y = point[inc][1]
            z = point[inc][2]

            found.append([x, y, z])

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

        self.api_object.getKnots(knots.get_api_object())

        return knots.get()

    def get_position_at_parameter(self, param):
        point = Point()

        self.api_object.getPointAtParam(param, point.get_api_object())
        return point.get()[0:3]

    def get_closest_position(self, three_value_list):
        point = Point(three_value_list[0],
                      three_value_list[1],
                      three_value_list[2])

        point = self.api_object.closestPoint(point.get_api_object(), None, 0.0000001, OpenMaya.MSpace.kWorld)

        return [point.x, point.y, point.z]

    def get_parameter_at_position(self, three_value_list):
        u = OpenMaya.MScriptUtil()
        u_ptr = u.asDoublePtr()
        OpenMaya.MScriptUtil.setDouble(u_ptr, 0.0)

        space = OpenMaya.MSpace.kWorld

        three_value_list = self.get_closest_position(three_value_list)

        point = Point(three_value_list[0],
                      three_value_list[1],
                      three_value_list[2])

        self.api_object.getParamAtPoint(point.get_api_object(), u_ptr, space)

        return OpenMaya.MScriptUtil.getDouble(u_ptr)

    def get_parameter_at_length(self, double):
        return self.api_object.findParamFromLength(double)


class SkinClusterFunction(MayaFunction):

    def _define_api_object(self, mobject):
        return OpenMayaAnim.MFnSkinCluster(mobject)

    def get_influence_dag_paths(self):

        path_array = OpenMaya.MDagPathArray()

        self.api_object.influenceObjects(path_array)

        return path_array

    def get_influence_names(self, short_name=False):

        influence_dag_paths = self.get_influence_dag_paths()

        influence_names = []

        for x in range(influence_dag_paths.length()):
            influence_path_name = None
            if not short_name:
                influence_path_name = influence_dag_paths[x].fullPathName()
            if short_name:
                influence_path_name = influence_dag_paths[x].partialPathName()
            influence_names.append(influence_path_name)

        return influence_names

    def get_influence_indices(self):

        influence_dag_paths = self.get_influence_dag_paths()

        influence_ids = []

        for x in range(influence_dag_paths.length()):
            influence_id = int(self.api_object.indexForInfluenceObject(influence_dag_paths[x]))
            influence_ids.append(influence_id)

        return influence_ids

    def get_influence_dict(self, short_name=False):

        influence_dag_paths = self.get_influence_dag_paths()

        influence_ids = {}
        influence_names = []

        for x in range(influence_dag_paths.length()):

            influence_path = influence_dag_paths[x]
            influence_path_name = None
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

        for vertex_id in range(vert_count):

            weights_plug.selectAncestorLogicalIndex(vertex_id, weight_list_attr)

            weights_plug.getExistingArrayAttributeIndices(weight_influence_ids)

            influence_plug = OpenMaya.MPlug(weights_plug)

            for influence_id in weight_influence_ids:

                influence_plug.selectAncestorLogicalIndex(influence_id, weights_attr)

                if influence_id not in weights:
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

        point_count = points.length()

        found = [None] * point_count

        for inc in range(point_count):
            point = points[inc]

            value = (point.x, point.y, point.z)

            found[inc] = value

        return found

    def get_points_as_flat_list(self):
        points = self.get_points()

        point_count = points.length()

        found = [None] * (point_count * 3)

        for inc in range(point_count):
            point = points[inc]
            sub_inc = inc * 3
            found[sub_inc] = point.x
            found[sub_inc + 1] = point.y
            found[sub_inc + 2] = point.z

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

    def is_done(self):
        return self.api_object.isDone()

    def index(self):
        return self.api_object.index()

    def next(self):
        self.api_object.next()

    def reset(self):
        self.api_object.reset()

    def count(self):
        count = self.api_object.count()
        return count

    def get_area(self, face_id=None):

        script_util = OpenMaya.MScriptUtil()
        area_ptr = script_util.asDoublePtr()
        OpenMaya.MScriptUtil.setDouble(area_ptr, 0.0)

        if face_id is not None:
            script_util = OpenMaya.MScriptUtil()
            prev = script_util.asIntPtr()
            self.api_object.setIndex(face_id, prev)

        self.api_object.getArea(area_ptr)

        area_value = OpenMaya.MScriptUtil.getDouble(area_ptr)

        return area_value

    def get_face_center_vectors(self):
        center_vectors = []

        for _ in range(0, self.api_object.count()):
            point = self.api_object.center()

            center_vectors.append([point.x, point.y, point.z])

            self.api_object.next()

        self.api_object.reset()

        return center_vectors

    def get_closest_face(self, vector):

        closest_distance = None
        closest_face = None

        while not self.api_object.isDone():
            center = self.api_object.center()

            distance = util_math.get_distance(vector, [center.x, center.y, center.z])

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

    def get_center(self, face_id=None):

        space = OpenMaya.MSpace.kWorld

        if face_id is not None:
            script_util = OpenMaya.MScriptUtil()
            prev = script_util.asIntPtr()

            self.api_object.setIndex(face_id, prev)

        point = self.api_object.center(space)

        return point.x, point.y, point.z

    def get_normal(self, face_id=None):

        if face_id is not None:
            script_util = OpenMaya.MScriptUtil()
            prev = script_util.asIntPtr()
            self.api_object.setIndex(face_id, prev)

        space = OpenMaya.MSpace.kWorld

        vector = OpenMaya.MVector()

        self.api_object.getNormal(vector, space)

        return vector.x, vector.y, vector.z

    def get_normal_tangent(self, face_id=None):
        # Not Implemented
        if face_id:
            script_util = OpenMaya.MScriptUtil()
            prev = script_util.asIntPtr()

            self.api_object.setIndex(face_id, prev)

        space = OpenMaya.MSpace.kWorld

        normal_vector = OpenMaya.MVector()
        position_vector = OpenMaya.MVector()

        position = self.api_object.center(space)
        self.api_object.getNormal(normal_vector, space)

        position_vector.x = 0
        position_vector.y = 0
        position_vector.z = 0

        tangent = position_vector * normal_vector


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

# --- API 2


def get_object(name):
    if not name or not exists(name):
        return

    selection_list = om.MSelectionList()
    selection_list.add(name)

    if cmds.objectType(name, isAType='transform') or cmds.objectType(name, isAType='shape'):
        return selection_list.getDagPath(0)

    return selection_list.getDependNode(0)


def get_object_name(mobject):
    dag_path = om.MDagPath()
    path = dag_path.getAPathTo(mobject)
    return path.partialPathName()


def get_plug(attribute_name):
    selection = om.MSelectionList()
    selection.add(attribute_name)
    plug = selection.getPlug(0)

    return plug


def get_mesh_points(name):
    mobject = get_object(name)

    meshfn = om.MFnMesh(mobject)
    points = meshfn.getPoints()

    return points


def get_distance(three_value_list1, three_value_list2):
    vector1 = three_value_list1
    vector2 = three_value_list2

    mp1 = om.MPoint(vector1[0], vector1[1], vector1[2])
    mp2 = om.MPoint(vector2[0], vector2[1], vector2[2])

    return mp1.distanceTo(mp2)


def get_triangle_ids(mesh, face_id, triangle_id):
    mobject = get_object(mesh)

    mit_mesh_polygon = om.MItMeshPolygon(mobject)

    mit_mesh_polygon.setIndex(face_id)
    point_array, int_array = mit_mesh_polygon.getTriangle(triangle_id)

    return int_array


def get_border_edges(mesh):
    mobject = get_object(mesh)
    iterator = om.MItMeshEdge(mobject)

    found = []

    while not iterator.isDone():

        if iterator.onBoundary():
            found.append(iterator.index())

        iterator.next()

    return found


def get_skin_weights_dict(skin_cluster, vert_ids=None):
    if vert_ids is None:
        vert_ids = []
    mobject = get_object(skin_cluster)

    mf_skin = omAnim.MFnSkinCluster(mobject)

    weight_list_plug = mf_skin.findPlug('weightList', 0)
    weights_plug = mf_skin.findPlug('weights', 0)
    weight_list_attr = weight_list_plug.attribute()
    weights_attr = weights_plug.attribute()
    weight_influence_ids = om.MIntArray()

    weights = {}

    vert_count = weight_list_plug.numElements()

    if not vert_ids:
        vert_ids = list(range(vert_count))

    for vertex_id in vert_ids:

        weights_plug.selectAncestorLogicalIndex(vertex_id, weight_list_attr)

        weight_influence_ids = weights_plug.getExistingArrayAttributeIndices()

        influence_plug = om.MPlug(weights_plug)

        for influence_id in weight_influence_ids:

            influence_plug.selectAncestorLogicalIndex(influence_id, weights_attr)

            if influence_id not in weights:
                weights[influence_id] = [0] * vert_count

            try:
                value = influence_plug.asDouble()
                weights[influence_id][vertex_id] = value

            except KeyError:
                # assumes a removed influence
                pass

    return weights


def get_identity_matrix():
    return om.MMatrix()


def multiply_matrix(matrix1, matrix2):
    """
    matrix1 and matrix2 are just the list of numbers of a 4x4 matrix.
        This can be had with cmds.getAttr("transform.worldMatrix" or something)
    """
    mat1 = om.MMatrix(matrix1)
    mat2 = om.MMatrix(matrix2)

    return mat1 * mat2


def get_inverse_matrix():
    pass


def get_joint_orient_matrix(joint):
    api_joint = get_object(joint)

    quat = om.MQuaternion()
    fn_joint = omAnim.MFnIkJoint(api_joint)

    fn_joint.getOrientation(quat)
    quat_matrix = quat.asMatrix()

    return quat_matrix


def get_scale_from_matrix(matrix):
    mat = om.MMatrix(matrix)

    tmat = om.MTransformationMatrix(mat)

    return tmat.scale(1)


def get_face_vertices(mesh, index):
    api_object = get_object(mesh)

    iter_face_fn = om.MItMeshPolygon(api_object)

    iter_face_fn.setIndex(index)
    verts = iter_face_fn.getConnectedVertices()

    return verts


def get_surrounding_vertex_indices(mesh, index):
    api_object = get_object(mesh)

    iter_vertex_fn = om.MItMeshVertex(api_object)
    iter_face_fn = om.MItMeshPolygon(api_object)

    iter_vertex_fn.setIndex(index)

    found_verts = {}

    faces = iter_vertex_fn.getConnectedFaces()

    for face in faces:
        iter_face_fn.setIndex(face)
        verts = iter_face_fn.getConnectedVertices()

        for vert in verts:
            found_verts[vert] = None

    return list(found_verts.keys())


def get_vert_count(mesh):
    api_object = get_object(mesh)

    count = om.MItMeshVertex(api_object).count()

    return count


def get_connected_verts(mesh, index, iterator=None):
    api_object = get_object(mesh)

    current = None

    if iterator:
        iter_vertex_fn = iterator
    else:
        iter_vertex_fn = om.MItMeshVertex(api_object)

    iter_vertex_fn.setIndex(index)

    found_verts = {}

    verts = iter_vertex_fn.getConnectedVertices()

    for vert in verts:
        found_verts[vert] = None

    if current:
        iterator.setIndex(current)

    return found_verts.keys()


def get_vertex_islands(mesh):
    api_object = get_object(mesh)
    iterator = om.MItMeshVertex(api_object)

    islands = {}
    checked = {}

    while not iterator.isDone():

        found = {}
        current = iterator.index()

        if current in checked:
            iterator.next()
            continue

        verts = iterator.getConnectedVertices()

        while verts:

            sub_found = {}
            sub_verts = []

            for vert in verts:

                if vert not in checked:

                    sub_verts = get_connected_verts(mesh, vert, iterator)

                    for sub_vert in sub_verts:
                        sub_found[sub_vert] = None

                found[vert] = None
                checked[vert] = None

            if sub_verts:
                verts = list(sub_found.keys())
            else:
                verts = None

        islands[current] = found

        iterator.next()

    result = []

    for key in islands:
        result.append(list(islands[key].keys()))

    return result


def get_skin_influence_names(skin_cluster, short_name=False):
    skin_object = get_object(skin_cluster)

    skin = omAnim.MFnSkinCluster(skin_object)

    influence_dag_paths = skin.influenceObjects()

    influence_names = []

    for x in range(len(influence_dag_paths)):

        influence_path_name = None
        if not short_name:
            influence_path_name = influence_dag_paths[x].fullPathName()
        if short_name:
            influence_path_name = influence_dag_paths[x].partialPathName()

        influence_names.append(influence_path_name)

    return influence_names


def get_skin_influence_indices(skin_cluster):
    skin_object = get_object(skin_cluster)

    skin = omAnim.MFnSkinCluster(skin_object)

    influence_dag_paths = skin.influenceObjects()

    influence_ids = []

    for x in range(len(influence_dag_paths)):
        influence_id = int(skin.indexForInfluenceObject(influence_dag_paths[x]))
        influence_ids.append(influence_id)

    return influence_ids


def get_skin_influence_dict(skin_cluster, short_name=False):
    skin_object = get_object(skin_cluster)
    skin = omAnim.MFnSkinCluster(skin_object)

    influence_dag_paths = skin.influenceObjects()

    influence_ids = {}
    influence_names = []

    for x in range(len(influence_dag_paths)):

        influence_path = influence_dag_paths[x]
        influence_path_name = None
        if not short_name:
            influence_path_name = influence_dag_paths[x].fullPathName()
        if short_name:
            influence_path_name = influence_dag_paths[x].partialPathName()

        influence_id = int(skin.indexForInfluenceObject(influence_path))
        influence_ids[influence_path_name] = influence_id
        influence_names.append(influence_path_name)

    return influence_ids, influence_names


def get_vector_rotation(target_vector, start_vector=None, factor=1):
    if start_vector is None:
        start_vector = [1, 0, 0]
    target_vector = om.MVector(*target_vector)
    start_vector = om.MVector(*start_vector)

    quat = om.MQuaternion(start_vector, target_vector, factor)
    rot = quat.asEulerRotation()

    return math.degrees(rot.x), math.degrees(rot.y), math.degrees(rot.z)


def get_geometry_filter(deformer):
    deformer_object = get_object(deformer)

    geo_filter = omAnim.MFnGeometryFilter(deformer_object)

    return geo_filter


def get_skin_components(skin_cluster, index):
    geo_filter = get_geometry_filter(skin_cluster)

    if util.get_maya_version() < 2022:
        fn_set = om.MFnSet(geo_filter.deformerSet)
        members = fn_set.getMembers(flatten=True)

        dag, component = members.getComponent(index)
        return dag, component

    if util.get_maya_version() > 2020:

        output_object = geo_filter.outputShapeAtIndex(index)

        iterator = om.MItGeometry(output_object)

        dagpath = om.MDagPath()

        if output_object.hasFn(om.MFn.kDagNode):
            dagpath = om.MDagPath.getAPathTo(output_object)
        else:
            return None, None

        api_type = output_object.apiType()

        if api_type == om.MFn.kMesh or api_type == om.MFn.kNurbsCurve:
            count = iterator.exactCount()
            indices = list(range(0, count))
            components = get_components(indices)

        if api_type == om.MFn.kNurbsSurface:

            dagpath = om.MDagPath.getAPathTo(output_object)

            nurbs_name = dagpath.fullPathName()

            cvs = cmds.ls('%s.cv[*][*]' % nurbs_name, flatten=True)

            indices = []

            for cv in cvs:
                numbers = util.get_square_bracket_numbers(cv)
                numbers.reverse()
                indices.append(numbers)

            double_component = om.MFnDoubleIndexedComponent()
            components = double_component.create(om.MFn.kSurfaceCVComponent)
            double_component.addElements(indices)

        if api_type == om.MFn.kLattice:
            dagpath = om.MDagPath.getAPathTo(output_object)

            lattice_name = dagpath.fullPathName()

            pts = cmds.ls('%s.pt[*][*][*]' % lattice_name, flatten=True)

            indices = []

            for pt in pts:
                numbers = util.get_square_bracket_numbers(pt)
                indices.append(numbers)

            triple_component = om.MFnTripleIndexedComponent()
            components = triple_component.create(om.MFn.kLatticeComponent)
            triple_component.addElements(indices)

        return dagpath, components


def get_components(indices):
    fn_comp_verts = om.MFnSingleIndexedComponent()
    components = fn_comp_verts.create(om.MFn.kMeshVertComponent)
    fn_comp_verts.addElements(indices)

    return components


def set_skin_weights(skin_cluster, weights=0, index=0, components=None, influence_array=None):

    skin_object = get_object(skin_cluster)
    dag_path, component = get_skin_components(skin_cluster, index)
    skin_fn = omAnim.MFnSkinCluster(skin_object)

    if isinstance(components, list) or isinstance(components, tuple):
        components = get_components(components)
    if not components:
        components = component

    influence_count = 0

    if influence_array:
        influence_count = len(influence_array)

        int_influence_array = om.MIntArray()

        for inc in range(0, influence_count):
            int_influence_array.append(influence_array[inc])

        influence_array = int_influence_array

    if not influence_array:
        influence_dag_paths = skin_fn.influenceObjects()
        influence_count = len(influence_dag_paths)
        influence_array = om.MIntArray()

        for inc in range(0, influence_count):
            index = skin_fn.indexForInfluenceObject(influence_dag_paths[inc])
            influence_array.append(index)

    weight_array = None
    if type(weights) == type(om.MDoubleArray()):
        weight_array = weights

    if weight_array is None:
        if isinstance(weights, list) or isinstance(weights, tuple):
            weight_array = om.MDoubleArray()
            for weight in weights:
                weight_array.append(weight)

        if not isinstance(weights, list) and not isinstance(weights, tuple):
            weight_array = om.MDoubleArray()

            # TODO: Potential bug here, we are checking the above to determine that it is not a list or a tuple, yet trying to iterate.
            for weight in weights:
                weight_array.append(float(weights))

    skin_fn.setWeights(dag_path, components, influence_array, weight_array, False, False)


def set_skin_blend_weights(skin_cluster, weights, index):
    skin_object = get_object(skin_cluster)
    dag_path, component = get_skin_components(skin_cluster, index)
    skin_fn = omAnim.MFnSkinCluster(skin_object)

    weight_array = None
    if type(weights) == type(om.MDoubleArray()):
        weight_array = weights

    if weight_array is None:
        if isinstance(weights, list) or isinstance(weights, tuple):
            weight_array = om.MDoubleArray()
            for weight in weights:
                weight_array.append(weight)

        if not isinstance(weights, list) and not isinstance(weights, tuple):
            weight_array = om.MDoubleArray()

            for weight in weights:
                weight_array.append(float(weights))

    skin_fn.setBlendWeights(dag_path, component, weight_array)


def set_weights(attr_name, weights):
    plug = get_plug(attr_name)

    for i, weight in enumerate(weights):
        sub_plug = plug.elementByLogicalIndex(i)
        sub_plug.setFloat(weight)
