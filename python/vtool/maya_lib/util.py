# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

import string
import re
import traceback

import maya.OpenMaya as OpenMaya
import maya.cmds as cmds
import maya.mel as mel

import vtool.util

import curve


def is_batch():
    return cmds.about(batch = True)

MAYA_BINARY = 'mayaBinary'
MAYA_ASCII = 'mayaAscii'

maya_data_mappings = {  
                        'bool' : 'attributeType',
                        'long' : 'attributeType',
                        'long2' : 'attributeType',
                        'long3' : 'attributeType',
                        'short': 'attributeType',
                        'short2' : 'attributeType',
                        'short3' : 'attributeType',
                        'byte' : 'attributeType',
                        'char' : 'attributeType',
                        'enum' : 'attributeType',
                        'float' : 'attributeType',
                        'float2' : 'attributeType',
                        'float3' : 'attributeType',
                        'double' : 'attributeType',
                        'double2' : 'attributeType',
                        'double3' : 'attributeType',
                        'doubleAngle' : 'attributeType',
                        'doubleLinear' : 'attributeType',
                        'doubleArray' : 'dataType',
                        'string' : 'dataType',
                        'stringArray' : 'dataType',
                        'compound' : 'attributeType',
                        'message' : 'attributeType',
                        'time' : 'attributeType',
                        'matrix' : 'dataType',
                        'fltMatrix' : 'attributeType',
                        'reflectanceRGB' : 'dataType',
                        'reflectance' : 'attributeType',
                        'spectrumRGB' : 'dataType',
                        'spectrum' : 'attributeType',
                        'Int32Array' : 'dataType',
                        'vectorArray' : 'dataType',
                        'nurbsCurve' : 'dataType',
                        'nurbsSurface' : 'dataType',
                        'mesh' : 'dataType',
                        'lattice' : 'dataType',
                        'pointArray' : 'dataType'
                        }

#--- classes

class FindUniqueName(vtool.util.FindUniqueString):
    
    def _get_scope_list(self):

        if cmds.objExists(self.increment_string):
            return [self.increment_string]
        
        if not cmds.objExists(self.increment_string):
            return []
    
    def _format_string(self, number):
        
        if number == 0:
            number = 1
            self.increment_string = '%s_%s' % (self.test_string, number)
        
        if number > 1:
            self.increment_string = vtool.util.increment_last_number(self.increment_string)
    
    def _get_number(self):
        number = vtool.util.get_last_number(self.test_string)
        
        return number

#--- api

    
class ApiObject(object):
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
            warning('Could not add %s into selection list' % name)
            return
        
        
    def get_at_index(self, index = 0):
        
        mobject = MayaObject()
        
        try:
            self.api_object.getDependNode(0, mobject())
            return mobject()
        except:
            warning('Could not get mobject at index %s' % index)
            return
    
class MeshFunction(MayaFunction):
    def _define_api_object(self, mobject):
        return OpenMaya.MFnMesh(mobject)
   
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
        
        for inc in range(0, self.api_object.count):
            
            point = self.api_object.center()
            
            center_vectors.append([point.x,point.y,point.z] )
            
            self.api_object.next()
        
        self.api_object.reset()
            
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
        
    
    
#--- variables
class MayaVariable(vtool.util.Variable):

    TYPE_BOOL = 'bool'
    TYPE_LONG = 'long'
    TYPE_SHORT = 'short'
    TYPE_ENUM = 'enum'
    TYPE_FLOAT = 'float'
    TYPE_DOUBLE = 'double'
    TYPE_STRING = 'string'
    TYPE_MESSAGE = 'message'
    
    def __init__(self, name ):
        super(MayaVariable, self).__init__(name)
        self.variable_type = 'short'
        self.keyable = True
        self.locked = False
        
    def _command_create_start(self):
        return 'cmds.addAttr(self.node,'
    
    def _command_create_mid(self):
        
        flags = ['longName = self.name']
        
        return flags
    
    def _command_create_end(self):
        data_type = self._get_variable_data_type()
        return '%s = self.variable_type)' %  data_type

    def _create_attribute(self):
        
        if cmds.objExists(self._get_node_and_variable()):
            return
        
        start_command = self._command_create_start()
        mid_command = string.join(self._command_create_mid(), ', ')
        end_command = self._command_create_end()
        
        command = '%s %s, %s' % (start_command,
                                mid_command,
                                end_command)
         
        eval( command )
    
    #--- _set
    
    def _set_lock_state(self):
        if not self.exists():
            return
        
        cmds.setAttr(self._get_node_and_variable(), l = self.locked)
    
    def _set_keyable_state(self):
        if not self.exists():
            return
        
        cmds.setAttr(self._get_node_and_variable(), k = self.keyable)       

    def _set_value(self):
        if not self.exists():
            return
        
        locked_state = self._get_lock_state()
        
        self.set_locked(False)
        
        if self._get_variable_data_type() == 'attributeType':
            cmds.setAttr(self._get_node_and_variable(), self.value )
            
        if self._get_variable_data_type() == 'dataType':
            
            cmds.setAttr(self._get_node_and_variable(), self.value, type = self.variable_type )
        
        self.set_locked(locked_state)
    
    #--- _get
    
    def _get_variable_data_type(self):
        return maya_data_mappings[self.variable_type]
    
    def _get_node_and_variable(self):
        return '%s.%s' % (self.node, self.name)
    
    def _get_lock_state(self):
        if not self.exists():
            return self.locked
        
        return cmds.getAttr(self._get_node_and_variable(), l = True)
        
    def _get_keyable_state(self):
        if not self.exists():
            return
        
        cmds.getAttr(self._get_node_and_variable(), k = True)

    def _get_value(self):
        if not self.exists():
            return
        return cmds.getAttr(self._get_node_and_variable())

    def _update_states(self):
        self._set_keyable_state()
        self._set_lock_state()
        self._set_value()

    def exists(self):
        return cmds.objExists(self._get_node_and_variable())

    #--- set
    def set_value(self, value):
        super(MayaVariable, self).set_value(value)
        self._set_value()
        
    def set_locked(self, bool_value):
        self.locked = bool_value
        self._set_lock_state()
        
    def set_keyable(self, bool_value):
        self.keyable = bool_value
        self._set_keyable_state()

    def set_variable_type(self, name):
        self.variable_type = name

    def set_node(self, name):
        self.node = name

    #--- get

    def get_value(self):
        return self._get_value()
        
    def get_name(self, name_only = False):
        if self.node and not name_only:
            return self._get_node_and_variable()
        if not self.node or name_only:
            return self.name

    def create(self, node = None):
        if node:
            self.node = node
        
        value = self.value
        exists = False
        
        if self.exists():
            exists = True
            if not value == None:
                value = self.get_value()
        
        self._create_attribute()
        self._update_states()
        
        if exists:            
            self.set_value( value )
        
    def delete(self, node = None):
        if node:
            self.node = node
        
        #theses lines might cause bugs   
        self.locked = False
        self._set_lock_state()
        #------
            
        cmds.deleteAttr(self.node, at = self.name)
        
    def load(self):
        self.value = self._get_value()
        self.locked = self._get_lock_state()
        self.keyable = self._get_keyable_state()
        
    def connect_in(self, attribute):
        cmds.connectAttr(attribute, self._get_node_and_variable())
        
    def connect_out(self, attribute):
        cmds.connectAttr(self._get_node_and_variable(), attribute)
        
class MayaNumberVariable(MayaVariable):
     
    def __init__(self, name):
        super(MayaNumberVariable, self).__init__(name)
        
        self.min_value = None
        self.max_value = None
        
        self.variable_type = 'double'
        
    def _update_states(self):
        super(MayaNumberVariable, self)._update_states()
        
        self._set_min_state()
        self._set_max_state()
    
    #--- _set
    
    def _set_min_state(self):
        if not self.exists():
            return
        
        if not self.min_value:
            if cmds.attributeQuery(self.name, node = self.node, minExists = True ):
                cmds.addAttr(self._get_node_and_variable(), edit = True, hasMinValue = False)
            
        
        if self.min_value != None:
            cmds.addAttr(self._get_node_and_variable(), edit = True, hasMinValue = True)
            cmds.addAttr(self._get_node_and_variable(), edit = True, minValue = self.min_value)
        
    def _set_max_state(self):
        if not self.exists():
            return
        
        if not self.max_value:
            if cmds.attributeQuery(self.name, node = self.node, maxExists = True ):
                cmds.addAttr(self._get_node_and_variable(), edit = True, hasMaxValue = False)
        
        if self.max_value != None:
            
            cmds.addAttr(self._get_node_and_variable(), edit = True, hasMaxValue = True)
            cmds.addAttr(self._get_node_and_variable(), edit = True, maxValue = self.max_value)
        
    #--- _get
        
    def _get_min_state(self):
        if not self.exists():
            return
        
        return cmds.attributeQuery(self.name, node = self.node, minimum = True)

    def _get_max_state(self):
        if not self.exists():
            return
        
        return cmds.attributeQuery(self.name, node = self.node, maximum = True)
        
    def set_min_value(self, value):
        self.min_value = value
        self._set_min_state()
    
    def set_max_value(self, value):
        self.max_value = value
        self._set_max_state()
        
    def load(self):
        
        super(MayaNumberVariable, self).load()
        
        self._get_min_state()
        self._get_max_state()
        
class MayaEnumVariable(MayaVariable):
    def __init__(self, name):                
        super(MayaEnumVariable, self).__init__(name)
        
        self.variable_type = 'enum'
        self.enum_names = ['----------']
        self.set_locked(True)
       
    def _command_create_mid(self):
        
        enum_name = string.join(self.enum_names, '|')
        
        flags= super(MayaEnumVariable, self)._command_create_mid()
        flags.append('enumName = "%s"' % enum_name)
        
        return flags

    def _update_states(self):
        super(MayaEnumVariable, self)._update_states()
        
        self._set_enum_state()

    def _set_enum_state(self):
        
        if not self.exists():
            return
        
        enum_name = string.join(self.enum_names, ':')
                
        if not enum_name:
            return
        
        value = self.get_value()
        
        cmds.addAttr(self._get_node_and_variable(), edit = True, enumName = enum_name)
        
        self.set_value(value)
    
    def set_enum_names(self, name_list):
        self.enum_names = name_list
        
        self._set_enum_state()

class MayaStringVariable(MayaVariable):
    def __init__(self, name):
        super(MayaStringVariable, self).__init__(name)
        self.variable_type = 'string'
        self.value = ''
    
#--- rig

class BoundingBox(vtool.util.BoundingBox):
    def __init__(self, thing):
        
        self.thing = thing
        
        xmin, ymin, zmin, xmax, ymax, zmax = cmds.exactWorldBoundingBox(self.thing)
        
        super(BoundingBox, self).__init__([xmin, ymin, zmin], 
                                          [xmax, ymax, zmax])
          
class OrientJointAttributes(object):
    
    def __init__(self, joint = None):
        self.joint = joint
        self.attributes = []
        self.title = None
        
        if joint:
            self._create_attributes()
    
    def _create_attributes(self):
        
        MayaEnumVariable('Orient_Info'.upper()).create(self.joint)
        
        attr = self._create_axis_attribute('aimAxis')
        self.attributes.append(attr)
        
        attr = self._create_axis_attribute('upAxis')
        self.attributes.append(attr)
        
        attr = self._create_axis_attribute('worldUpAxis')
        self.attributes.append(attr)
    
        enum = MayaEnumVariable('aimAt')
        enum.set_enum_names(['world_X', 
                             'world_Y', 
                             'world_Z', 
                             'child',
                             'parent',
                             'local_parent'])
        enum.set_locked(False)
        enum.create(self.joint)
        
        
        self.attributes.append(enum)
        
        enum = MayaEnumVariable('aimUpAt')
        enum.set_enum_names(['world',
                             'parent_rotate',
                             'child_position',
                             'parent_position',
                             'triangle_plane'])
        
        enum.set_locked(False)
        enum.create(self.joint)
        
        self.attributes.append(enum)
        
        attr = self._create_triangle_attribute('triangleTop')
        self.attributes.append(attr)
        
        attr = self._create_triangle_attribute('triangleMid')
        self.attributes.append(attr)
        
        attr = self._create_triangle_attribute('triangleBtm')
        self.attributes.append(attr)
        

    def _delete_attributes(self):
        
        self.title.delete()
        
        for attribute in self.attributes:
            attribute.delete()
    def _create_axis_attribute(self, name):
        enum = MayaEnumVariable(name)
        enum.set_enum_names(['X','Y','Z','-X','-Y','-Z','none'])
        enum.set_locked(False)
        enum.create(self.joint)
        
        return enum
        
    def _create_triangle_attribute(self, name):
        enum = MayaEnumVariable(name)
        enum.set_enum_names(['grand_parent', 'parent', 'self', 'child', 'grand_child'])
        enum.set_locked(False)
        enum.create(self.joint)
        
        return enum
    
    def _set_default_values(self):
        self.attributes[0].set_value(0)
        self.attributes[1].set_value(1)
        self.attributes[2].set_value(1)
        self.attributes[3].set_value(3)
        self.attributes[4].set_value(0)
        self.attributes[5].set_value(1)
        self.attributes[6].set_value(2)
        self.attributes[7].set_value(3)
    
    def set_joint(self, joint):
        self.joint = joint
        
        self._create_attributes()
    
    def get_values(self):
        
        value_dict = {}
        
        for attr in self.attributes:
            value_dict[attr.get_name(True)] = attr.get_value()
            
        return value_dict
    
    def set_default_values(self):
        self._set_default_values()

    def delete(self):
        self._delete_attributes()
          
class OrientJoint(object):
    
    def __init__(self, joint_name):
        
        self.joint = joint_name
        self.orient_values = None
        self.aim_vector = [1,0,0]
        self.up_vector = [0,1,0]
        self.world_up_vector = [0,1,0]
        
        self.aim_at = 3
        self.aim_up_at = 0
        
        self.child = None
        self.grand_child = None
        self.parent = None
        self.grand_parent = None
        
        self.delete_later =[]
        self.world_up_vector = self._get_vector_from_axis(1)
        self.up_space_type = 'vector'
        
        self._get_relatives()
        
    def _get_relatives(self):
        
        parent = cmds.listRelatives(self.joint, p = True)
        
        if parent:
            self.parent = parent[0]
            
            grand_parent = cmds.listRelatives(self.parent, p = True)
            
            if grand_parent:
                self.grand_parent = grand_parent[0]
                
        children = cmds.listRelatives(self.joint)
        
        if children:
            self.child = children[0]
            
            grand_children = cmds.listRelatives(self.child)
            
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
            child_aim = self._get_position_group(self.child)
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
            child_group = self._get_position_group(self.child)
            self.up_space_type = 'object'
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
                
                warning('Could not orient %s fully with current triangle plane settings.' % self.joint)
                return
            
            plane_group = get_group_in_plane(top, mid, btm)
            cmds.move(0,10,0, plane_group, r =True, os = True)
            self.delete_later.append(plane_group)
            self.up_space_type = 'object'
            return plane_group
        
        if index == 5:
            self.up_space_type = 'none'
            
    def _get_local_group(self, transform):
        
        local_up_group = cmds.group(em = True, n = 'local_up_%s' % transform)
        
        MatchSpace(transform, local_up_group).rotation()
        MatchSpace(self.joint, local_up_group).translation()
        
        cmds.move(1,0,0, local_up_group, relative = True, objectSpace = True)
        
        self.delete_later.append(local_up_group)
        
        return local_up_group
    
    def _get_position_group(self, transform):
        position_group = cmds.group(em = True, n = 'position_group')
        
        MatchSpace(transform, position_group).translation()
        
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
        
        orient_attributes = OrientJointAttributes(self.joint)
        return orient_attributes.get_values()
        
    def _cleanup(self):
        cmds.delete(self.delete_later)

    def _pin(self):
        
        pin = PinXform(self.joint)
        pin.pin()
        
        nodes = pin.get_pin_nodes()
        self.delete_later += nodes
        
    def _freeze(self):
        children = cmds.listRelatives(self.joint)
        
        if children:
            cmds.parent(children, w = True)
        
        cmds.makeIdentity(self.joint, apply = True, r = True, s = True)
        
        if children:
            cmds.parent(children, self.joint)
      
    def set_aim_vector(self, vector_list):
        self.aim_vector = vector_list
        
    def set_up_vector(self, vector_list):
        self.up_vector = vector_list
        
    def set_world_up_vector(self, vector_list):
        self.world_up_vector = vector_list
        
    def set_aim_at(self, int_value):
        self.aim_at = self._get_aim_at(int_value)
        
    def set_aim_up_at(self, int_value):
        self.aim_up_at = self._get_aim_up_at(int_value)
        
    def set_aim_up_at_object(self, name):
        self.aim_up_at = self._get_local_group(name)
        
        self.up_space_type = 'objectrotation'
        self.world_up_vector = [0,1,0]
        
    def run(self):
        
        self._freeze()
        
        self._get_relatives()
        self._pin()
        
        self.orient_values = self._get_values()
        
        if self.orient_values:
        
            self.aim_vector = self._get_vector_from_axis( self.orient_values['aimAxis'] )
            self.up_vector = self._get_vector_from_axis(self.orient_values['upAxis'])
            self.world_up_vector = self._get_vector_from_axis( self.orient_values['worldUpAxis'])
            
            self.aim_at = self._get_aim_at(self.orient_values['aimAt'])
            self.aim_up_at = self._get_aim_up_at(self.orient_values['aimUpAt'])
        
        if not self.orient_values:
                        
            if type(self.aim_at) == int:
                self.aim_at = self._get_aim_at(self.aim_at)
            
            if type(self.aim_up_at) == int: 
                self.aim_up_at = self._get_aim_up_at(self.aim_up_at)
        
        self._create_aim()
        
        self._cleanup()
        self._freeze()
        
class PinXform(object):
    def __init__(self, xform_name):
        self.xform = xform_name
        self.delete_later = []

    def pin(self):
        parent = cmds.listRelatives(self.xform)
        
        if parent:
            parent = parent[0]
            
            pin = cmds.group(em = True, n = 'pin1')
            MatchSpace(parent, pin).translation_rotation()
            constraint = cmds.parentConstraint(pin, parent, mo = True)[0]
            self.delete_later.append(constraint)
            self.delete_later.append(pin)
        
        children = cmds.listRelatives(self.xform)
        
        if not children:
            return
        
        for child in children:
            pin = cmds.group(em = True, n = 'pin1') 
            MatchSpace(child, pin).translation_rotation()
            constraint = cmds.parentConstraint(pin, child, mo = True)[0]
            self.delete_later.append(constraint)
            self.delete_later.append(pin)
            
    def unpin(self):
        if self.delete_later:
            cmds.delete(self.delete_later)
        
    def get_pin_nodes(self):
        return self.delete_later
    
class MayaNode(object):
    
    def __init__(self, name = None):
        
        self.node = None
        
        self._create_node(name)
        
    def _create_node(self, name):
        pass
        
class MultiplyDivideNode(MayaNode):
    
    def __init__(self, name = None):
        
        if not name.startswith('multiplyDivide'):
            name = inc_name('multiplyDivide_%s' % name)
        
        super(MultiplyDivideNode, self).__init__(name)
        
    def _create_node(self, name):
        self.node = cmds.createNode('multiplyDivide', name = name)
        cmds.setAttr('%s.input2X' % self.node, 1)
        cmds.setAttr('%s.input2Y' % self.node, 1)
        cmds.setAttr('%s.input2Z' % self.node, 1)
        
    def set_operation(self, value):
        cmds.setAttr('%s.operation' % self.node, value)
    
    def set_input1(self, valueX = None, valueY = None, valueZ = None):
        
        if valueX != None:
            cmds.setAttr('%s.input1X' % self.node, valueX)
            
        if valueY != None:
            cmds.setAttr('%s.input1Y' % self.node, valueY)
            
        if valueZ != None:
            cmds.setAttr('%s.input1Z' % self.node, valueZ)
        
    def set_input2(self, valueX = None, valueY = None, valueZ = None):
        
        if valueX != None:
            cmds.setAttr('%s.input2X' % self.node, valueX)
            
        if valueY != None:
            cmds.setAttr('%s.input2Y' % self.node, valueY)
            
        if valueZ != None:
            cmds.setAttr('%s.input2Z' % self.node, valueZ)
            
    def input1X_in(self, attribute):
        cmds.connectAttr(attribute, '%s.input1X' % self.node)
    
    def input1Y_in(self, attribute):
        cmds.connectAttr(attribute, '%s.input1Y' % self.node)
        
    def input1Z_in(self, attribute):
        cmds.connectAttr(attribute, '%s.input1Z' % self.node)
    
    def input2X_in(self, attribute):
        cmds.connectAttr(attribute, '%s.input2X' % self.node)
    
    def input2Y_in(self, attribute):
        cmds.connectAttr(attribute, '%s.input2Y' % self.node)
        
    def input2Z_in(self, attribute):
        cmds.connectAttr(attribute, '%s.input2Z' % self.node)
        
    def outputX_out(self, attribute):
        connect_plus('%s.outputX' % self.node, attribute)
    
    def outputY_out(self, attribute):
        connect_plus('%s.outputY' % self.node, attribute)
        
    def outputZ_out(self, attribute):
        connect_plus('%s.outputZ' % self.node, attribute)

class MatchSpace(object):
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
        cmds.xform(self.target_transform, rp = scale_pivot_vector, ws = True)
        
    def translation(self):
        self._set_translation()
        
    def rotation(self):
        self._set_rotation()
        
    def translation_rotation(self):
        
        self._set_scale_pivot()
        self._set_rotate_pivot()
        
        self._set_translation()
            
        self._set_rotation()
        
    def translation_to_rotate_pivot(self):
        translate_vector = self._get_rotate_pivot()
        self._set_translation(translate_vector)
        
    def rotate_scale_pivot_to_translation(self):
        position = self._get_translation()
        
        cmds.move(position[0], 
                  position[1],
                  position[2], 
                  '%s.scalePivot' % self.target_transform, 
                  '%s.rotatePivot' % self.target_transform, 
                  a = True)
        
    def pivots(self):
        self._set_rotate_pivot()
        self._set_scale_pivot()
        
    def world_pivots(self):
        self._set_world_rotate_pivot()
        self._set_world_scale_pivot()

class Control(object):
    
    def __init__(self, name):
        
        self.control = name
        self.curve_type = None
        
        if not cmds.objExists(self.control):
            self._create()
            
        self.shapes = cmds.listRelatives(self.control, shapes = True)
        
        if not self.shapes:
            warning('%s has no shapes' % self.control)
            
    def _create(self):
        self.control = cmds.circle(ch = False, n = self.control, normal = [1,0,0])[0]
        
        if self.curve_type:
            self.set_curve_type(self.curve_type)
        
    def _get_components(self):
        
        return get_components_from_shapes(self.shapes)
        
    def set_curve_type(self, type_name):
        
        curve_data = curve.CurveDataInfo()
        curve_data.set_active_library('default_curves')
        curve_data.set_shape_to_curve(self.control, type_name)
    
    
    def set_to_joint(self):
        
        cmds.select(cl = True)
        name = self.get()
        
        joint = cmds.joint()
        
        MatchSpace(name, joint).translation_rotation()
        
        shapes = self.shapes
        
        for shape in shapes:
            cmds.parent(shape, joint, r = True, s = True)
        
        cmds.setAttr('%s.drawStyle' % joint, 2)
            
        transfer_relatives(name, joint)
            
        cmds.delete(name)
        cmds.rename(joint, name)
        
    def translate_shape(self, x,y,z):
        
        components = self._get_components()
        
        if components:
            cmds.move(x,y,z, components, relative = True)
        
    def rotate_shape(self, x,y,z):
        
        components = self._get_components()
        
        if components:
            cmds.rotate(x,y,z, components, relative = True)
            
    def scale_shape(self, x,y,z):
        
        components = self._get_components()
        if components:
            cmds.scale(x,y,z, components)

    def color(self, value):
        
        set_color(self.shapes, value)
    
    def show_scale_attributes(self):
        
        cmds.setAttr('%s.scaleX' % self.control, l = False, k = True)
        cmds.setAttr('%s.scaleY' % self.control, l = False, k = True)
        cmds.setAttr('%s.scaleZ' % self.control, l = False, k = True)
    
    def hide_attributes(self, attributes):
        hide_attributes(self.control, attributes)
        
    def hide_translate_attributes(self):
        hide_attributes(self.control, ['translateX',
                                     'translateY',
                                     'translateZ'])
        
    def hide_rotate_attributes(self):
        hide_attributes(self.control, ['rotateX',
                                     'rotateY',
                                     'rotateZ'])
        
    def hide_scale_attributes(self):
        hide_attributes(self.control, ['scaleX',
                                     'scaleY',
                                     'scaleZ'])
        
    def hide_visibility_attribute(self):
        hide_attributes(self.control, ['visibility'])
    
    def hide_scale_and_visibility_attributes(self):
        self.hide_scale_attributes()
        self.hide_visibility_attribute()
    
    def hide_keyable_attributes(self):
        hide_keyable_attributes(self.control)
        
    def rotate_order(self, xyz_order_string):
        
        cmds.setAttr('%s.rotateOrder' % self.node, xyz_order_string)
    
    def color_respect_side(self, sub = False, center_tolerance = 0.001):
        
        position = cmds.xform(self.control, q = True, ws = True, t = True)
        
        if position[0] > 0:
            color_value = get_color_of_side('L', sub)
            side = 'L'

        if position[0] < 0:
            color_value = get_color_of_side('R', sub)
            side = 'R'
            
        if position[0] < center_tolerance and position[0] > center_tolerance*-1:
            color_value = get_color_of_side('C', sub)
            side = 'C'
            
        self.color(color_value)
        
        return side
            
    def get(self):
        return self.control
    
    def create_xform(self):
        
        xform = create_xform_group(self.control)
        
        return xform
        
    def rename(self, new_name):
        
        new_name = cmds.rename(self.control, inc_name(new_name))
        self.control = new_name

    def delete_shapes(self):
        cmds.delete(self.shapes)
        self.shapes = []
        
    
    
    

class IkHandle(object):
    
    solver_rp = 'ikRPsolver'
    solver_sc = 'ikSCsolver'
    solver_spline = 'ikSplineSolver'
    solver_spring = 'ikSpringSolver'
    
    def __init__(self, name):
        
        if not name:
            name = inc_name('ikHandle')
        
        if not name.startswith('ikHandle'):
            self.name = 'ikHandle_%s' % name
            
        self.start_joint = None
        self.end_joint = None
        self.solver_type = self.solver_sc
        self.curve = None
        
        self.ik_handle = None
    
    def _create_regular_ik(self):
        self.ik_handle = cmds.ikHandle( name = inc_name(self.name),
                                       startJoint = self.start_joint,
                                       endEffector = self.end_joint,
                                       sol = self.solver_type )[0]
                                       
    def _create_spline_ik(self):
        self.ik_handle = cmds.ikHandle(name = inc_name(self.name),
                                       startJoint = self.start_joint,
                                       endEffector = self.end_joint,
                                       sol = self.solver_type,
                                       curve = self.curve, ccv = False, pcv = False)[0]
        
    def set_start_joint(self, joint):
        self.start_joint = joint
        
    def set_end_joint(self, joint):
        self.end_joint = joint
        
    def set_curve(self, curve):
        self.curve = curve
        
    def set_solver(self, type_name):
        self.solver_type = type_name
    
    def create(self):
        
        if not self.start_joint or not self.end_joint:
            return
        
        if not self.curve:
            self._create_regular_ik()
        
        if self.curve:
            self._create_spline_ik()

        
        return self.ik_handle

class ConstraintEditor():
    
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
    
    def _get_constraint_type(self, constraint):
        return cmds.nodeType(constraint)
        
        
        
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
        return len(cmds.ls('%s.target[*]' % constraint))
    
    def get_constraint(self, transform, constraint_type):
        constraint = eval('cmds.%s("%s", query = True)' % (constraint_type, transform) )
        
        return constraint
    
    def get_transform(self, constraint):
        transform = get_attribute_input('%s.constraintParentInverseMatrix' % constraint)
        
        if not transform:
            return
        
        new_thing = transform.split('.')
        return new_thing[0]
    
    def get_targets(self, constraint):
        
        transform = self.get_transform(constraint)
        constraint_type = self._get_constraint_type(constraint)
        
        return eval('cmds.%s("%s", query = True, targetList = True)' % (constraint_type,
                                                                        transform) )
        
    def remove_target(self, target, constraint):
        
        transform = self.get_transform(constraint)
        constraint_type = self._get_constraint_type(constraint)
        
        return eval('cmds.%s("%s", "%s", remove = True)' % (constraint_type,
                                                            target, 
                                                            transform) )
        
    def set_interpolation(self, int_value, constraint):
        
        cmds.setAttr('%s.interpType' % constraint, int_value)
        
    def create_switch(self, node, attribute, constraint):
        
        
        attributes = self.get_weight_names(constraint)
        
        attribute_count = len(attributes)
        
        if attribute_count <= 1:
            return
        
        if not cmds.objExists('%s.%s' % (node, attribute)):
            variable = MayaNumberVariable(attribute)
            variable.set_variable_type(variable.TYPE_DOUBLE)
            variable.set_node(node)
            variable.set_min_value(0)
            variable.set_max_value(attribute_count-1)
            variable.create()
        
        remap = RemapAttributesToAttribute(node, attribute)
        remap.create_attributes(constraint, attributes)
        remap.create()

class RemapAttributesToAttribute(object):
    #CBB
    
    def __init__(self, node, attribute):
        
        self.attribute = '%s.%s' % (node, attribute)
        self.attributes = []
          
    def create_attributes(self, node, attributes):
        for attribute in attributes:
            self.create_attribute(node, attribute)
          
    def create_attribute(self, node, attribute):
        self.attributes.append( [node, attribute] )
                
    def create(self):        
        length = len(self.attributes)
        
        for inc in range(0,length):
            
            node = self.attributes[inc][0]
            attribute = self.attributes[inc][1]
            
            input_min = inc - 1
            input_max = inc + 1
            
            if input_min < 0:
                input_min = 0
                
            if input_max > (length-1):
                input_max = (length-1)
            
            input_node = get_attribute_input(attribute)
                
            if input_node:
                if cmds.nodeType(input_node) == 'remapValue':
                    split_name = input_node.split('.')
                    
                    remap = split_name[0]
                    
                if cmds.nodeType(input_node) != 'remapValue':
                    input_node = None
                                                
            if not input_node: 
                remap = cmds.createNode('remapValue', n = 'remapValue_%s' % attribute)
            
            cmds.setAttr('%s.inputMin' % remap, input_min)
            cmds.setAttr('%s.inputMax' % remap, input_max)
            
            if inc == 0:
                cmds.setAttr('%s.value[0].value_FloatValue' % remap, 1)
                cmds.setAttr('%s.value[0].value_Position' % remap, 0)
                cmds.setAttr('%s.value[0].value_Interp' % remap, 1)
                cmds.setAttr('%s.value[1].value_FloatValue' % remap, 0)
                cmds.setAttr('%s.value[1].value_Position' % remap, 1)
                cmds.setAttr('%s.value[1].value_Interp' % remap, 1)
            
            if inc == (length-1):
                cmds.setAttr('%s.value[0].value_FloatValue' % remap, 0)
                cmds.setAttr('%s.value[0].value_Position' % remap, 0)
                cmds.setAttr('%s.value[0].value_Interp' % remap, 1)
                cmds.setAttr('%s.value[1].value_FloatValue' % remap, 1)
                cmds.setAttr('%s.value[1].value_Position' % remap, 1)
                cmds.setAttr('%s.value[1].value_Interp' % remap, 1)
            
            if inc != 0 and inc != (length-1):
                for inc2 in range(0,3):
                    if inc2 == 0:
                        position = 0
                        value = 0
                    if inc2 == 1:
                        position = 0.5
                        value = 1
                    if inc2 == 2:
                        position = 1
                        value = 0
                        
                    cmds.setAttr('%s.value[%s].value_FloatValue' % (remap,inc2), value)
                    cmds.setAttr('%s.value[%s].value_Position' % (remap,inc2), position)
                    cmds.setAttr('%s.value[%s].value_Interp' % (remap,inc2), 1)    
                   
            disconnect_attribute('%s.%s' % (node,attribute)) 
            cmds.connectAttr('%s.outValue' % remap, '%s.%s' % (node,attribute))
                                    
            disconnect_attribute('%s.inputValue' % remap)
            cmds.connectAttr(self.attribute,'%s.inputValue' % remap)

                
class DuplicateHierarchy(object):
    def __init__(self, transform):
        
        self.top_transform = transform

        self.duplicates = []
        
        self.replace_old = None
        self.replace_new = None
        
        self.stop = False
        self.stop_at_transform = None
        
        self.only_these_transforms = None
        
        self.prefix_name = None
            
    def _get_children(self, transform):
        return cmds.listRelatives(transform, children = True, type = 'transform')
        
    def _duplicate(self, transform):
        
        new_name = transform
        
        if self.replace_old and self.replace_new:
            new_name = transform.replace(self.replace_old, self.replace_new)
        
        duplicate = cmds.duplicate(transform, po = True)[0]
        
        duplicate = cmds.rename(duplicate, inc_name(new_name))
        
        self.duplicates.append( duplicate )

        return duplicate
    
    def _duplicate_hierarchy(self, transform):
            
            if transform == self.stop_at_transform:
                self.stop = True
            
            if self.stop:
                return
            
            top_duplicate = self._duplicate(transform)
            
            children = self._get_children(transform)
            
            if children:
                duplicate = None
                duplicates = []
                
                for child in children:

                    if self.only_these_transforms and not child in self.only_these_transforms:
                        continue
                    
                    duplicate = self._duplicate_hierarchy(child)
                    
                    if not duplicate:
                        break
                    
                    duplicates.append(duplicate)
                    
                    if cmds.nodeType(top_duplicate) == 'joint' and cmds.nodeType(duplicate) == 'joint':
                        
                        if cmds.isConnected('%s.scale' % transform, '%s.inverseScale' % duplicate):
                            cmds.disconnectAttr('%s.scale' % transform, '%s.inverseScale' % duplicate)
                            cmds.connectAttr('%s.scale' % top_duplicate, '%s.inverseScale' % duplicate)
                        
                if duplicates:
                    cmds.parent(duplicates, top_duplicate)
            
            return top_duplicate
    
    def only_these(self, list_of_transforms):
        self.only_these_transforms = list_of_transforms
        
    def stop_at(self, transform):
        
        relative = cmds.listRelatives(transform, type = 'transform')
        
        if relative:
            self.stop_at_transform = relative[0]
        
    def replace(self, old, new):
        
        self.replace_old = old
        self.replace_new = new
        
    def set_prefix(self, prefix):
        self.prefix_name = prefix
        
    def create(self):
        
        cmds.refresh()
        
        self._duplicate_hierarchy(self.top_transform)
        
        return self.duplicates
 
    
class StretchyChain:
    
    def __init__(self):
        self.side = 'C'
        self.inputs = []
        self.attribute_node = None
        self.distance_offset_attribute = None
        self.add_dampen = False
        self.stretch_offsets = []
        self.distance_offset = None
        self.scale_axis = 'X'
        self.name = 'stretch'
        self.simple = False
    
    def _get_joint_count(self):
        return len(self.joints)
    
    def _get_length(self):
        length = 0
        
        joint_count = self._get_joint_count()
        
        for inc in range(0, joint_count):
            if inc+1 == joint_count:
                break
            
            current_joint = self.joints[inc]
            next_joint = self.joints[inc+1]
            
            distance =  get_distance(current_joint, next_joint)
            
            length += distance
            
        return length
    
    def _build_stretch_locators(self):
        
        top_distance_locator = cmds.group(empty = True, n = inc_name('locator_topDistance_%s' % self.name))
        match = MatchSpace(self.joints[0], top_distance_locator)
        match.translation_rotation()
        
        btm_distance_locator = cmds.group(empty = True, n = inc_name('locator_btmDistance_%s' % self.name))
        match = MatchSpace(self.joints[-1], btm_distance_locator)
        match.translation_rotation()
        
        if not self.attribute_node:
            self.attribute_node = top_distance_locator
        
        return top_distance_locator, btm_distance_locator
    
    def _create_stretch_condition(self):
        
        total_length = self._get_length()
        
        condition = cmds.createNode("condition", n = inc_name("condition_%s" % self.name))
        cmds.setAttr("%s.operation" % condition, 2)
        cmds.setAttr("%s.firstTerm" % condition, total_length)
        cmds.setAttr("%s.colorIfTrueR" % condition, total_length)
        
        return condition

    def _create_distance_offset(self, stretch_condition = None):
        
        multiply = MultiplyDivideNode('offset_%s' % self.name)
        multiply.set_operation(2)
        multiply.set_input2(1,1,1)
        
        if stretch_condition:
            multiply.outputX_out('%s.secondTerm' % stretch_condition)
            multiply.outputX_out('%s.colorIfFalseR' % stretch_condition)
        
        return multiply.node

    def _create_stretch_distance(self, top_locator, btm_locator, distance_offset):
        
        distance_between = cmds.createNode('distanceBetween', 
                                           n = inc_name('distanceBetween_%s' % self.name) )
        
        cmds.connectAttr('%s.worldMatrix' % top_locator, 
                         '%s.inMatrix1' % distance_between)
        
        cmds.connectAttr('%s.worldMatrix' % btm_locator, 
                         '%s.inMatrix2' % distance_between)
        
        cmds.connectAttr('%s.distance' % distance_between, '%s.input1X' % distance_offset)
        
        return distance_between
        
        
    def _create_stretch_on_off(self, stretch_condition):
        
        blend = cmds.createNode('blendColors', n = inc_name('blendColors_%s' % self.name))
        cmds.setAttr('%s.color2R' % blend, self._get_length() )
        cmds.setAttr('%s.blender' % blend, 1)
        cmds.connectAttr('%s.outColorR' % stretch_condition, '%s.color1R' % blend)
        
        return blend

    def _create_divide_distance(self, stretch_condition = None, stretch_on_off = None):
        
        multiply = MultiplyDivideNode('distance_%s' % self.name)
        
        multiply.set_operation(2)
        multiply.set_input2(self._get_length(),1,1)
        
        if stretch_condition:
            if stretch_on_off:
                multiply.input1X_in('%s.outputR' % stretch_on_off)
            if not stretch_on_off:
                multiply.input1X_in('%s.outColorR' % stretch_condition)
        if not stretch_condition:
            pass
        
        return multiply.node

    def _create_offsets(self, divide_distance, distance_node):
        stretch_offsets = []
        
        plus_total_offset = cmds.createNode('plusMinusAverage', n = inc_name('plusMinusAverage_total_offset_%s' % self.name))
        cmds.setAttr('%s.operation' % plus_total_offset, 3)
        
        for inc in range(0, self._get_joint_count()-1 ):
            
            var_name = 'offset%s' % (inc + 1)
            
            multiply = connect_multiply('%s.outputX' % divide_distance, '%s.scale%s' % (self.joints[inc], self.scale_axis), 1)
            
            offset_variable = MayaNumberVariable(var_name )
            offset_variable.set_variable_type(offset_variable.TYPE_DOUBLE)
            offset_variable.set_node(multiply)
            
            offset_variable.create()
            offset_variable.set_value(1)
            offset_variable.set_min_value(0.1)
            offset_variable.connect_out('%s.input2X' % multiply)
            offset_variable.connect_out('%s.input1D[%s]' % (plus_total_offset, inc+1))
            
            stretch_offsets.append(multiply)
        
        multiply = cmds.createNode('multiplyDivide', n = inc_name('multiplyDivide_orig_distance_%s' % self.name))
        self.orig_distance = multiply
        
        length = self._get_length()
        cmds.setAttr('%s.input1X' % multiply, length)
        cmds.connectAttr('%s.output1D' % plus_total_offset, '%s.input2X' % multiply)
        
        return stretch_offsets
        
    def _connect_scales(self):
        for inc in range(0,len(self.joints)-1):
            cmds.connectAttr('%s.output%s' % (self.divide_distance, self.scale_axis), '%s.scale%s' % (self.joints[inc], self.scale_axis))
        
    def _create_attributes(self, stretch_on_off):
        
        title = MayaEnumVariable('STRETCH')
        title.create(self.attribute_node)
        title.set_locked(True)
        
        stretch_on_off_var = MayaNumberVariable('autoStretch')
        stretch_on_off_var.set_node(self.attribute_node)
        stretch_on_off_var.set_variable_type(stretch_on_off_var.TYPE_DOUBLE)
        stretch_on_off_var.set_min_value(0)
        stretch_on_off_var.set_max_value(1)
        
        stretch_on_off_var.create()
        
        stretch_on_off_var.connect_out('%s.blender' % stretch_on_off)
        
    def _create_offset_attributes(self, stretch_offsets):
        
        for inc in range(0, len(stretch_offsets)):
            
            stretch_offset = MayaNumberVariable('stretch_%s' % (inc+1))
            stretch_offset.set_node(self.attribute_node)
            stretch_offset.set_variable_type(stretch_offset.TYPE_DOUBLE)
            
            stretch_offset.create()
            
            stretch_offset.set_value(1)
            stretch_offset.set_min_value(0.1)
            
            stretch_offset.connect_out('%s.offset%s' % (stretch_offsets[inc], inc+1) )
    
    def _create_other_distance_offset(self, distance_offset):
        
        multiply = MultiplyDivideNode('distanceOffset_%s' % self.name)
        
        plug = '%s.input2X' % distance_offset
        
        input_to_plug = get_attribute_input('%s.input2X' % distance_offset)
        
        multiply.input1X_in(input_to_plug)
        multiply.input2X_in(self.distance_offset_attribute)
        multiply.outputX_out(plug)
        
    def _create_dampen(self, distance_node, plugs):
        
        min_length = get_distance(self.joints[0], self.joints[-1])
        #max_length = self._get_length()

        dampen = MayaNumberVariable('dampen')
        dampen.set_node(self.attribute_node)
        dampen.set_variable_type(dampen.TYPE_DOUBLE)
        dampen.set_min_value(0)
        dampen.set_max_value(1)
        dampen.create()
        
        remap = cmds.createNode( "remapValue" , n = "dampen_remapValue_%s" % self.name )
        cmds.setAttr("%s.value[2].value_Position" % remap, 0.4);
        cmds.setAttr("%s.value[2].value_FloatValue" % remap, 0.666);
        cmds.setAttr("%s.value[2].value_Interp" % remap, 3)
    
        cmds.setAttr("%s.value[3].value_Position" % remap, 0.7);
        cmds.setAttr("%s.value[3].value_FloatValue" % remap, 0.9166);
        cmds.setAttr("%s.value[3].value_Interp" % remap, 1)
    
        multi = cmds.createNode ( "multiplyDivide", n = "dampen_offset_%s" % self.name)
        add_double = cmds.createNode( "addDoubleLinear", n = "dampen_addDouble_%s" % self.name)

        dampen.connect_out('%s.input2X' % multi)
        
        cmds.connectAttr('%s.outputX' % self.orig_distance, '%s.input1X' % multi)
        
        cmds.connectAttr("%s.outputX" % multi, "%s.input1" % add_double)
        
        cmds.connectAttr('%s.outputX' % self.orig_distance, '%s.input2' % add_double)
        
        cmds.connectAttr("%s.output" % add_double, "%s.inputMax" % remap)
    
        cmds.connectAttr('%s.outputX' % self.orig_distance, '%s.outputMax' % remap)
        
        cmds.setAttr("%s.inputMin" % remap, min_length)
        cmds.setAttr("%s.outputMin" % remap, min_length)
        
        cmds.connectAttr( "%s.distance" % distance_node, "%s.inputValue" % remap)
        
        for plug in plugs:
                cmds.connectAttr( "%s.outValue" % remap, plug)
        
    def set_joints(self, joints):
        self.joints = joints
        
    def set_node_for_attributes(self, node_name):
        self.attribute_node = node_name
    
    def set_scale_axis(self, axis_letter):
        self.scale_axis = axis_letter.capitalize()
    
    def set_distance_offset(self, attribute):
        self.distance_offset_attribute = attribute
    
    def set_add_dampen(self, bool_value):
        self.add_dampen = bool_value
    
    def set_simple(self, bool_value):
        self.simple = bool_value
    
    def set_description(self, string_value):
        self.name = '%s_%s' % (self.name, string_value)
    
    def create(self):
        
        top_locator, btm_locator = self._build_stretch_locators()
        
        if self.simple:
            
            for joint in self.joints[:-1]:
                distance_offset = self._create_distance_offset()
                
                stretch_distance = self._create_stretch_distance(top_locator, 
                                              btm_locator, 
                                              distance_offset)
                                
                divide_distance = self._create_divide_distance()
                
                cmds.connectAttr('%s.outputX' % distance_offset, '%s.input1X' % divide_distance)
                
                print joint
                cmds.connectAttr('%s.outputX' % divide_distance, '%s.scale%s' % (joint, self.scale_axis))
            
            
        
        if not self.simple:
        
            stretch_condition = self._create_stretch_condition()
            
            distance_offset = self._create_distance_offset( stretch_condition )
            
            stretch_distance = self._create_stretch_distance(top_locator, 
                                          btm_locator, 
                                          distance_offset)
            
            stretch_on_off = self._create_stretch_on_off( stretch_condition )
            
            divide_distance = self._create_divide_distance( stretch_condition, 
                                                            stretch_on_off )
            
            stretch_offsets = self._create_offsets( divide_distance, stretch_distance)
            
            if self.attribute_node:
                self._create_attributes(stretch_on_off)
                self._create_offset_attributes(stretch_offsets)
                
                if self.add_dampen:
                    self._create_dampen(stretch_distance, ['%s.firstTerm' % stretch_condition,
                                                           '%s.colorIfTrueR' % stretch_condition,
                                                           '%s.color2R' % stretch_on_off,
                                                           '%s.input2X' % divide_distance])
                
            if self.distance_offset_attribute:
                self._create_other_distance_offset(distance_offset)
                
        return top_locator, btm_locator

class Rig(object):
    
    side_left = 'L'
    side_right = 'R'
    side_center = 'C'
    
    def __init__(self, description, side):
        self._refresh()
        self.description = description
        self.side = side
        
        self.control_group = self._create_group('controls')
        self.setup_group = self._create_group('setup')
        
        cmds.hide(self.setup_group)
        
        self.control_shape = self._define_control_shape()
        
    def _refresh(self):
        cmds.refresh()
        
    def _define_control_shape(self):
        return 'circle'
        
    def _get_name(self, prefix = None, description = None):
        
        name_list = [prefix,self.description, description, '1', self.side]
        
        filtered_name_list = []
        
        for name in name_list:
            if name:
                filtered_name_list.append(str(name))
        
        name = string.join(filtered_name_list, '_')
        
        return name
        
    def _get_control_name(self, description = None, sub = False):
        
        prefix = 'CNT'
        if sub:
            prefix = 'CNT_SUB'
            
        control_name = self._get_name(prefix, description)
            
        control_name = control_name.upper()
        
        control_name = inc_name(control_name)
        
        return control_name
        
    def _create_control(self, description = None, sub = False):
        
        sub_value = False
        
        if sub:
            sub_value = True
        
        control = Control( self._get_control_name(description, sub_value) )
        
        control.color( get_color_of_side( self.side , sub_value)  )
        control.hide_visibility_attribute()
        control.set_curve_type(self.control_shape)
        
        return control
    
    def _create_group(self,  prefix = None, description = None):
        
        rig_group_name = self._get_name(prefix, description)
        
        group = cmds.group(em = True, n = inc_name(rig_group_name))
        
        return group
        
    def set_control_shape(self, shape_name):
        self.control_shape = shape_name
                
    def create(self):
        pass

class JointRig(Rig):
    def __init__(self, description, side):
        super(JointRig, self).__init__(description, side)
        
        self.joints = []
        
        self.attach_joints = True

    def _hook_scale_constraint(self, node):
        
        constraint_editor = ConstraintEditor()
        scale_constraint = constraint_editor.get_constraint(node, constraint_editor.constraint_scale)
        
        if not scale_constraint:
            return
        
        weight_count = constraint_editor.get_weight_count(scale_constraint)
        
        cmds.connectAttr('%s.parentInverseMatrix' % node, '%s.constraintParentInverseMatrix' % scale_constraint)
        
        for inc in range(0, weight_count):
            
            target = get_attribute_input('%s.target[%s].targetScale' % (scale_constraint, inc), True)
            
            cmds.connectAttr('%s.parentInverseMatrix' % target, '%s.target[%s].targetParentMatrix' % (scale_constraint, inc) )

    def _unhook_scale_constraint(self, scale_constraint):
        constraint_editor = ConstraintEditor()
        
        weight_count = constraint_editor.get_weight_count(scale_constraint)
        disconnect_attribute('%s.constraintParentInverseMatrix' % scale_constraint)
        
        for inc in range(0, weight_count):
            disconnect_attribute('%s.target[%s].targetParentMatrix' % (scale_constraint, inc))

    def _attach_joint(self, source_joint, target_joint):
        if not self.attach_joints:
            return
        self._hook_scale_constraint(target_joint)
        
        parent_constraint = cmds.parentConstraint(source_joint, target_joint, mo = True)[0]
        
        scale_constraint = cmds.scaleConstraint(source_joint, target_joint)[0]
        
        constraint_editor = ConstraintEditor()
        constraint_editor.create_switch(self.joints[0], 'switch', parent_constraint)
        constraint_editor.create_switch(self.joints[0], 'switch', scale_constraint)
        
        self._unhook_scale_constraint(scale_constraint)
        
    def _attach_joints(self, source_chain, target_chain):
        
        if not self.attach_joints:
            return
        
        AttachJoints(source_chain, target_chain).create()
        
        #for inc in range( 0, len(source_chain) ):
        #    self._attach_joint(source_chain[inc], target_chain[inc] )
    
    def set_joints(self, joints):
        
        if type(joints) != list:
            self.joints = [joints]
            return
        
        self.joints = joints

    def set_attach_joints(self, bool_value):
        
        self.attach_joints = bool_value


class CurveRig(Rig):
    def __init__(self, description, side):
        super(CurveRig, self).__init__(description, side)
        
        self.curves = None
    
    def set_curve(self, curve_list):
        
        self.curves = curve_list

class SurfaceFollowCurveRig(CurveRig):
    
    def __init__(self, description, side):
        super(SurfaceFollowCurveRig, self).__init__(description, side)
        
        self.surface = None
        self.join_start_end = False
    
    def _cluster_curve(self):
        
        clusters = cluster_curve(self.curves[0], 'hat', True, join_start_end = self.join_start_end)
        return clusters
    
    def _create_follow_control(self, cluster):
        
        control = self._create_control()
        control.set_curve_type('cube')
        control.hide_rotate_attributes()
        control.hide_scale_attributes()
        
        sub_control = self._create_control(sub = True)
        sub_control.set_curve_type('cube')
        sub_control.scale_shape(.5, .5, .5)
        sub_control.hide_rotate_attributes()
        sub_control.hide_scale_attributes()
        
        match = MatchSpace(cluster, control.get())
        match.translation_to_rotate_pivot()
        
        xform_control = create_xform_group(control.get())
        cmds.parent(sub_control.get(), control.get(), r = True)
        
        local, xform = constrain_local(sub_control.get(), cluster, parent = True)
        
        cmds.parent(cluster, w = True)
        
        driver = create_xform_group(local, 'driver')
        
        connect_translate(control.get(), driver)
        
        cmds.geometryConstraint(self.surface, driver)
        
        cmds.parent(cluster, local)
        
        cmds.parent(xform_control, self.control_group)
        cmds.parent(xform, self.setup_group)
                
    def _create_controls(self, clusters):
        
        for cluster in clusters:
            self._create_follow_control(cluster)
    
    def set_surface(self, surface_name):
        self.surface = surface_name
    
    def set_join_start_end(self, bool_value):
        self.join_start_end = bool_value
    
    def set_locator_only(self):
        pass
    
    def create(self):
        clusters = self._cluster_curve()
        
        self._create_controls(clusters)

class BufferRig(JointRig):
    
    def __init__(self, name, side):
        super(BufferRig, self).__init__(name, side)
        
        self.create_buffer_joints = False
    
    def _duplicate_joints(self):
        
        if self.create_buffer_joints:
            duplicate_hierarchy = DuplicateHierarchy( self.joints[0] )
            
            duplicate_hierarchy.stop_at(self.joints[-1])
            duplicate_hierarchy.replace('joint', 'buffer')
            
            self.buffer_joints = duplicate_hierarchy.create()
    
            cmds.parent(self.buffer_joints[0], self.setup_group)

        if not self.create_buffer_joints:
            self.buffer_joints = self.joints
        
        return self.buffer_joints
        
    def set_buffer(self, bool_value):
        self.create_buffer_joints = bool_value
            
    def create(self):
        super(BufferRig, self).create()
        
        self._duplicate_joints()
        
        if self.create_buffer_joints:
            self._attach_joints(self.buffer_joints, self.joints)

class SparseRig(JointRig):
    
    def __init__(self, description, side):
        super(SparseRig, self).__init__(description, side)
        self.control_shape = 'cube'
        self.is_scalable = False
        self.respect_side = False
        self.respect_side_tolerance = 0.001
        
    def set_control_shape(self, name):
        self.control_shape = name
        
    def set_scalable(self, bool_value):
        self.is_scalable = bool_value
        
    def set_respect_side(self, bool_value, tolerance = 0.001):
        self.respect_side = bool_value
        self.respect_side_tolerance = tolerance
        
    def create(self):
        
        super(SparseRig, self).create()
        
        for joint in self.joints:
            
            
            
            control = self._create_control()
            control.hide_visibility_attribute()
            control.set_curve_type(self.control_shape)
        
            
        
            
            control_name = control.get()
        
            match = MatchSpace(joint, control_name)
            match.translation_rotation()
            
            if self.respect_side:
                side = control.color_respect_side(True, self.respect_side_tolerance)
            
                if side != 'C':
                    control_name = cmds.rename(control_name, inc_name(control_name[0:-1] + side))
                    control = Control(control_name)
                        
            xform = create_xform_group(control.get())
            driver = create_xform_group(control.get(), 'driver')
            
            cmds.parentConstraint(control_name, joint)

            if self.is_scalable:
                cmds.scaleConstraint(control.get(), joint)
            if not self.is_scalable:
                control.hide_scale_attributes()
            
            cmds.parent(xform, self.control_group)

class SparseLocalRig(SparseRig):

    def __init__(self, description, side):
        super(SparseLocalRig, self).__init__(description, side)
        
        self.local_constraint = True
        self.control_to_pivot = False
        self.local_parent = None
        self.local_xform = None
        
        

    def set_local_constraint(self, bool_value):
        self.local_constraint = bool_value

    def set_control_to_pivot(self, bool_value):
        
        self.control_to_pivot = bool_value

    def set_local_parent(self, local_parent):
        self.local_parent = local_parent

    def create(self):
        
        super(SparseRig, self).create()
        
        if self.local_parent:
            self.local_xform = cmds.group(em = True, n = 'localParent_%s' % self._get_name())
            cmds.parent(self.local_xform, self.setup_group)
        
        for joint in self.joints:
            control = self._create_control()
            control.hide_visibility_attribute()
            
            control.set_curve_type(self.control_shape)
            
            control_name = control.get()
            
            if not self.control_to_pivot:
                match = MatchSpace(joint, control_name)
                match.translation_rotation()
            if self.control_to_pivot:
                MatchSpace(joint, control_name).translation_to_rotate_pivot()
            
            if self.respect_side:
                side = control.color_respect_side(True, self.respect_side_tolerance)
            
                if side != 'C':
                    control_name = cmds.rename(control_name, inc_name(control_name[0:-1] + side))
                    control = Control(control_name)
            
            
            xform = create_xform_group(control.get())
            driver = create_xform_group(control.get(), 'driver')
            
            
            
            if not self.local_constraint:
                xform_joint = create_xform_group(joint)
                
                if self.local_parent:
                    cmds.parent(xform_joint, self.local_xform)
                
                connect_translate(control.get(), joint)
                connect_rotate(control.get(), joint)
                
                connect_translate(driver, joint)
                connect_rotate(driver, joint)
            
            if self.local_constraint:
                local_group, local_xform = constrain_local(control.get(), joint)
                
                if self.local_xform:
                    cmds.parent(local_xform, self.local_xform)
                
                local_driver = create_xform_group(local_group, 'driver')
                
                connect_translate(driver, local_driver)
                connect_rotate(driver, local_driver)
                connect_scale(driver, local_driver)
                
                if not self.local_xform:
                    cmds.parent(local_xform, self.setup_group)
                
            connect_scale(control.get(), joint)
            
            
            cmds.parent(xform, self.control_group)
            
        if self.local_parent:
            follow = create_follow_group(self.local_parent, self.local_xform)
            
class ControlRig(Rig):
    
    def __init__(self, name, side):
        super(ControlRig, self).__init__(name,side)
        
        self.transforms = None
        self.control_count = 1
        self.control_shape_types = {}
        self.control_descriptions = {}
    
    def set_transforms(self, transforms):
        self.transforms = transforms
        
    def set_control_count_per_transform(self, int_value):
        self.control_count = int_value
    
    def set_control_shape(self, index, shape_name):
        self.control_shape_types[index] = shape_name
    
    def set_control_description(self, index, description):
        self.control_descriptions[index] = description
    
    def create(self):
        
        for transform in self.transforms:
            for inc in range(0, self.control_count):
                
                description = None
                if inc in self.control_descriptions:
                    description = self.control_descriptions[inc]
                
                control = self._create_control(description)
                
                
                MatchSpace(transform, control.get()).translation_rotation()
                
                if inc in self.control_shape_types:
                    control.set_curve_type(self.control_shape_types[inc])
                
                xform = create_xform_group(control.get())    
                cmds.parent(xform, self.control_group)                
                    
            

class GroundRig(JointRig):
    
    def __init__(self, name, side):
        super(GroundRig, self).__init__(name, side)
        
        self.control_shape = 'square_point'
    
    def create(self):
        super(GroundRig, self).create()
        
        scale = 1
        last_control = None
        
        for inc in range(0, 3):
            if inc == 0:
                control = self._create_control()
                
                control.set_curve_type(self.control_shape)
                
                cmds.parent(control.get(), self.control_group)
                
            
            if inc > 0:
                control = self._create_control(sub =  True)
                control.set_curve_type(self.control_shape)
            
            #control.rotate_shape(0, 0, 90)
                
            control.scale_shape(40*scale, 40*scale, 40*scale)
            
            
            
            if last_control:
                cmds.parent(control.get(), last_control)
            
            last_control = control.get()
            scale*=.9
            
            control.hide_scale_and_visibility_attributes()
        
        if self.joints:   
            cmds.parentConstraint(control.get(), self.joints[0])
        
    def set_joints(self, joints = None):
        super(GroundRig, self).set_joints(joints)
        




class FkRig(BufferRig):
    #CBB
    
    def __init__(self, name, side):
        super(FkRig, self).__init__(name, side)
        self.last_control = ''
        self.control = ''
        self.controls = []
        self.drivers = []
        self.current_xform_group = ''
        self.control_size = 3
        
        self.control_shape = None
        
        self.transform_list = []
        self.current_increment = None
        
        self.use_joints = False
        
        self.parent = None
        
        self.connect_to_driver = None
        self.match_to_rotation = True

    def _create_control(self, sub = False):
        
        self.last_control = self.control
        
        self.control = super(FkRig, self)._create_control(sub = sub)
        
        self.control.scale_shape(self.control_size,self.control_size,self.control_size)

        self.control.hide_scale_and_visibility_attributes()
        
        if self.use_joints:
            self.control.set_to_joint()
        
        self.current_xform_group = create_xform_group(self.control.get())
        driver = create_xform_group(self.control.get(), 'driver')
        
        self.controls.append( self.control )
        self.drivers.append(driver)
        self.control = self.control.get()

        return self.control
    
    def _edit_at_increment(self, control, transform_list):
        self.transform_list = transform_list
        current_transform = transform_list[self.current_increment]
        
        self._all_increments(control, current_transform)
        
        if self.current_increment == 0:
            self._first_increment(control, current_transform)

        if self.current_increment == ((len(transform_list))-1):
            self._last_increment(control, current_transform)
                    
        if self.current_increment > 0:
            self._increment_greater_than_zero(control, current_transform)
   
        if self.current_increment < (len(transform_list)):
            self._increment_less_than_last(control, current_transform)
            
        if self.current_increment < (len(transform_list)) and self.current_increment > 0:
            self._incrment_after_start_before_end(control, current_transform)
            
        if self.current_increment == (len(transform_list)-1) or self.current_increment == 0:
            self._increment_equal_to_start_end(control,current_transform)
    
    
    def _all_increments(self, control, current_transform):
        
        match = MatchSpace(current_transform, self.current_xform_group)
        
        if self.match_to_rotation:
            match.translation_rotation()
            
        if not self.match_to_rotation:
            match.translation()
        
    def _first_increment(self, control, current_transform):
        
        cmds.parent(self.current_xform_group, self.control_group)
        self._attach(control, current_transform)
    
    def _last_increment(self, control, current_transform):
        return
    
    def _increment_greater_than_zero(self, control, current_transform):
        
        self._attach(control, current_transform)
        
        cmds.parent(self.current_xform_group, self.last_control)
    
    def _increment_less_than_last(self, control, current_transform):
        return
    
    def _increment_equal_to_start_end(self, control, current_transform):
        return
    
    def _incrment_after_start_before_end(self, control, current_transform):
        return
    
    def _loop(self, transforms):
        inc = 0
        
        for inc in range(0, len(transforms)):
            
            self.current_increment = inc
            
            control = self._create_control()
            
            self._edit_at_increment(control, transforms)

            inc += 1
    
    def _attach(self, source_transform, target_transform):
        
        cmds.parentConstraint(source_transform, target_transform, mo = True)        

    def set_parent(self, parent):
        self.parent = parent

    
    def set_control_size(self, value):
        self.control_size = value
        
    def set_match_to_rotation(self, bool_value):
        self.match_to_rotation = bool_value
    
    def get_drivers(self):
        return self.drivers
    
    def set_use_joints(self, bool_value):
        
        self.use_joints = bool_value
    
    def create(self):
        super(FkRig, self).create()
        
        self._loop(self.buffer_joints)
        
        if self.parent:
            cmds.parent(self.control_group, self.parent)


class FkLocalRig(FkRig):
    
    def __init__(self, name, side):
        super(FkLocalRig, self).__init__(name, side)
        
        self.local_parent = None
        self.main_local_parent = None
        self.local_xform = None
        self.rig_scale = False
    
    def _attach(self, source_transform, target_transform):
        
        local_group, local_xform = constrain_local(source_transform, target_transform, scale_connect = self.rig_scale)
        
        if not self.local_parent:
            self.local_xform = local_xform
            cmds.parent(local_xform, self.setup_group)
        
        if self.local_parent:
            follow = create_follow_group(self.local_parent, local_xform)
            cmds.parent(follow, self.control_group)
        
        self.local_parent = local_group
        
        
        return local_group, local_xform

    def _create_control(self, sub = False):
        
        self.last_control = self.control
        
        self.control = super(FkRig, self)._create_control(sub = sub)
        self.control.scale_shape(self.control_size,self.control_size,self.control_size)
        
        if not self.rig_scale:
            self.control.hide_scale_and_visibility_attributes()
        
        if self.rig_scale:
            self.control.hide_visibility_attribute()
        
        if self.control_shape:
            self.control.set_curve_type(self.control_shape)
        
        self.current_xform_group = create_xform_group(self.control.get())
        driver = create_xform_group(self.control.get(), 'driver')
        
        self.controls.append( self.control )
        self.drivers.append(driver)
        self.control = self.control.get()
        
        return self.control

    def set_local_parent(self, local_parent):
        self.main_local_parent = local_parent 
    
    def create(self):
        super(FkLocalRig, self).create()
        
        if self.main_local_parent:
            follow = create_follow_group(self.main_local_parent, self.local_xform)
            #cmds.parent(follow, self.control_group)
    
class FkWithSubControlRig(FkRig):
    
    def _create_control(self, sub = False):
        
        self.control = super(FkRig, self)._create_control(sub = sub)
        self.control.scale_shape(self.control_size,self.control_size,self.control_size)
        
        self.control.hide_scale_and_visibility_attributes()
        
        if self.control_shape:
            self.control.set_curve_type(self.control_shape)
        
        self.current_xform_group = create_xform_group(self.control.get())
        driver = create_xform_group(self.control.get(), 'driver')
        
        self.controls.append( self.control )
        self.drivers.append(driver)
        self.control = self.control.get()
        
        sub_control = self._create_sub_control(self.control)
        
        return sub_control
        
    def _create_sub_control(self, parent):
        
        self.last_control = self.control
        
        sub_control = super(FkRig, self)._create_control(sub = True)

        sub_control.scale_shape(self.control_size*0.9,self.control_size*0.9,self.control_size*0.9)
        
        sub_control.hide_scale_and_visibility_attributes()
        
        if self.control_shape:
            sub_control.set_curve_type(self.control_shape)
        
        create_xform_group(self.control)
        create_xform_group(self.control, 'driver')
        
        sub_control = sub_control.get()
        
        connect_visibility('%s.subVisibility' % self.control, '%sShape' % sub_control, 1)
        
        cmds.parent(sub_control, self.control)
        
        return sub_control
    
    
class FkScaleRig(FkRig): 
    #CBB 
      
    def __init__(self, name, side): 
        super(FkScaleRig, self).__init__(name, side) 
        self.last_control = '' 
        self.control = '' 
        self.controls = [] 
        self.current_xform_group = '' 
          
    def _create_control(self, sub = False): 
        super(FkScaleRig, self)._create_control(sub) 
          
        control = Control(self.control) 
  
        control.show_scale_attributes() 
        cmds.setAttr( '%s.overrideEnabled' % control.get() , 1 ) 
          
        if self.control_shape: 
            control.set_curve_type(self.control_shape) 
          
        return self.control 
          
    def _edit_at_increment(self, control, transform_list): 
        self.transform_list = transform_list 
        current_transform = transform_list[self.current_increment] 
          
        self._all_increments(control, current_transform) 
          
        if self.current_increment == 0: 
            self._first_increment(control, current_transform) 
  
        if self.current_increment == ((len(transform_list))-1): 
            self._last_increment(control, current_transform) 
                      
        if self.current_increment > 0: 
            self._increment_greater_than_zero(control, current_transform) 
     
        if self.current_increment < (len(transform_list)): 
            self._increment_less_than_last(control, current_transform) 
              
        if self.current_increment < (len(transform_list)) and self.current_increment > 0: 
            self._incrment_after_start_before_end(control, current_transform) 
              
        if self.current_increment == (len(transform_list)-1) or self.current_increment == 0: 
            self._increment_equal_to_start_end(control,current_transform) 
          
    def _first_increment(self, control, current_transform): 
        super(FkScaleRig, self)._first_increment(control, current_transform) 
          
        connect_scale(control, current_transform) 
      
    def _increment_greater_than_zero(self, control, current_transform): 
          
        cmds.select(cl = True) 
          
        name = self._get_name('jointFk') 
          
        buffer_joint = cmds.joint(n = inc_name( name ) ) 
          
        cmds.setAttr('%s.overrideEnabled' % buffer_joint, 1) 
        cmds.setAttr('%s.overrideDisplayType' % buffer_joint, 1) 
          
        cmds.setAttr('%s.radius' % buffer_joint, 0) 
          
        cmds.connectAttr('%s.scale' % self.last_control, '%s.inverseScale' % buffer_joint) 
          
          
        match = MatchSpace(control, buffer_joint) 
        match.translation_rotation() 
          
        cmds.makeIdentity(buffer_joint, apply = True, r = True) 
          
        #cmds.parentConstraint(control, current_transform)
        
        cmds.pointConstraint(control, current_transform) 
        connect_rotate(control, current_transform) 
           
        drivers = self.drivers[self.current_increment]
        drivers = vtool.util.convert_to_sequence(drivers)
        
        for driver in drivers:
            connect_rotate(driver, current_transform)
        
        connect_scale(control, current_transform) 
          
        cmds.parent(self.current_xform_group, buffer_joint) 
          
        cmds.parent(buffer_joint, self.last_control) 
        
class FkCurlNoScaleRig(FkRig):
    def __init__(self, description, side):
        super(FkCurlNoScaleRig, self).__init__(description, side)
        
        self.attribute_control = None
        self.attribute_name =None
        self.curl_axis = 'Z'
        self.skip_increments = []
        
        
    def _create_control(self, sub = False):
        control = super(FkCurlNoScaleRig, self)._create_control(sub)
        
        if self.curl_axis == None:
            return self.control
        
        if not self.attribute_control:
            self.attribute_control = control
            
        if not cmds.objExists('%s.CURL' % self.attribute_control):
            title = MayaEnumVariable('CURL')
            title.create(self.attribute_control)
        
        driver = create_xform_group(control, 'driver2')
        
        other_driver = self.drivers[-1]
        self.drivers[-1] = [other_driver, driver]
        
        if self.curl_axis != 'All':
            self._attach_curl_axis(driver)
            
        if self.curl_axis == 'All':
            all_axis = ['x','y','z']
            
            for axis in all_axis:
                self._attach_curl_axis(driver, axis)
                
        return self.control    
    
    def _attach_curl_axis(self, driver, axis = None):

        if self.current_increment in self.skip_increments:
            return


        if not self.attribute_name:
            description = self.description
        if self.attribute_name:
            description = self.attribute_name

        if axis == None:
            var_name = '%sCurl' % description
        if axis:
            var_name = '%sCurl%s' % (description, axis.capitalize())
            
        if not axis:
            curl_axis = self.curl_axis
        if axis:
            curl_axis = axis.capitalize()
            
        curl_variable = MayaNumberVariable(var_name)
        curl_variable.set_variable_type(curl_variable.TYPE_DOUBLE)
        curl_variable.create(self.attribute_control)
        
        curl_variable.connect_out('%s.rotate%s' % (driver, curl_axis))
        
        if self.current_increment and self.create_buffer_joints:
            
            current_transform = self.transform_list[self.current_increment]
            connect_rotate(driver, current_transform)
    
    def set_curl_axis(self, axis_letter):
        self.curl_axis = axis_letter.capitalize()
    
    def set_attribute_control(self, control_name):
        self.attribute_control = control_name
        
    def set_attribute_name(self, attribute_name):
        self.attribute_name = attribute_name
        
    def set_skip_increments(self, increments):
        self.skip_increments = increments
        
class FkCurlRig(FkScaleRig):
    
    def __init__(self, description, side):
        super(FkCurlRig, self).__init__(description, side)
        
        self.attribute_control = None
        self.curl_axis = 'Z'
        self.curl_description = self.description
        self.skip_increments = []
        
    def _create_control(self, sub = False):
        control = super(FkCurlRig, self)._create_control(sub)
        
        if not self.attribute_control:
            self.attribute_control = control
            
        if not cmds.objExists('%s.CURL' % self.attribute_control):
            title = MayaEnumVariable('CURL')
            title.create(self.attribute_control)
        
        driver = create_xform_group(control, 'driver2')
        
        other_driver = self.drivers[-1]
        self.drivers[-1] = [other_driver, driver]
        
        if self.curl_axis != 'All':
            self._attach_curl_axis(driver)
            
        if self.curl_axis == 'All':
            all_axis = ['x','y','z']
            
            for axis in all_axis:
                self._attach_curl_axis(driver, axis)
                
        return self.control    
    
    def _attach_curl_axis(self, driver, axis = None):
        
        if self.current_increment in self.skip_increments:
            return
        
        if axis == None:
            var_name = '%sCurl' % self.curl_description
        if axis:
            var_name = '%sCurl%s' % (self.curl_description, axis.capitalize())
            
        if not axis:
            curl_axis = self.curl_axis
        if axis:
            curl_axis = axis.capitalize()
            
        curl_variable = MayaNumberVariable(var_name)
        curl_variable.set_variable_type(curl_variable.TYPE_DOUBLE)
        curl_variable.create(self.attribute_control)
        
        curl_variable.connect_out('%s.rotate%s' % (driver, curl_axis))
        
    def set_curl_axis(self, axis_letter):
        self.curl_axis = axis_letter.capitalize()
    
    def set_curl_description(self, description):
        self.curl_description = description
        
    def set_skip_increments(self, increments):
        
        self.skip_increments = increments
    
    def set_attribute_control(self, control_name):
        self.attribute_control = control_name
    
class SimpleSplineIkRig(BufferRig):
    
    #to be removed, use TweakCurveRig instead.
    
    def __init__(self, name, side):
        super(SimpleSplineIkRig, self).__init__(name, side)
        self.curve = None
        self.cv_count = 10
    
    def _create_curve(self):

        name = self._get_name()
        
        joints = self.buffer_joints
        if not self.buffer_joints:
            joints = self.joints

        if not self.curve:
                
            self.curve = transforms_to_curve(joints, len(joints), name)
            
            name = self._get_name()
            
            cmds.rebuildCurve(self.curve, 
                              spans = self.cv_count,
                              rpo = True,  
                              rt = 0, 
                              end = 1, 
                              kr = False, 
                              kcp = False, 
                              kep = True,  
                              kt = False,
                              d = 3)
            
            self.curve = cmds.rename(self.curve, 'curve_%s' % name)
            
            cmds.parent(self.curve, self.setup_group)
    
    def _create_spline_ik(self):
    
        if self.buffer_joints:
            joints = self.buffer_joints
        if not self.buffer_joints:
            joints = self.joints
            
        children = cmds.listRelatives(joints[-1])
        
        if children:
            cmds.parent(children, w = True)
        
        handle = cmds.ikHandle( sol = 'ikSplineSolver', 
                       ccv = False, 
                       pcv = False , 
                       sj = joints[0], 
                       ee = joints[-1], 
                       c = self.curve, n = 'splineIk_%s' % self._get_name())[0]
        
        if children:
            cmds.parent(children, joints[-1])
            
        cmds.parent(handle, self.setup_group)
            
        if self.buffer_joints != self.joints:
            
            follow = create_follow_group(self.controls[0].get(), self.buffer_joints[0])
            cmds.parent(follow, self.setup_group)
        
        """
        var = MayaNumberVariable('twist')
        var.set_variable_type(var.TYPE_DOUBLE)
        var.create(self.controls[0].get())
        var.connect_out('%s.twist' % handle)
        """
    def set_curve(self, curve):
        self.curve = curve
    
    def set_cv_count(self, count):
        self.cv_count = count 
    
    def create(self):
        super(SimpleSplineIkRig, self).create()
        
        self._create_curve()
        self._create_spline_ik()
   
class SimpleFkCurveRig(FkCurlNoScaleRig):
    def __init__(self, name, side):
        super(SimpleFkCurveRig, self).__init__(name, side)
        self.controls = []
        self.orient_controls_to_joints = False
        self.sub_controls = []
        self.sub_control_on = True
        self.sub_drivers = []
        self.stretchy = True
        self.control_count = 3
        self.advanced_twist = True
        self.stretch_on_off = False
        self.orig_curve = None
        self.curve = None
        self.ik_curve = None
        self.span_count = self.control_count
        self.wire_hires = False
        self.curl_axis = None
        self.orient_joint = None
        self.control_xform = {}
        self.last_pivot_top_value = False
        self.fix_x_axis = False
        self.skip_first_control = False
        self.ribbon = False
        self.ribbon_offset = 1
        self.ribbon_offset_axis = 'Y'
        self.create_follows = True

    def _create_curve(self):
        
        if not self.curve:
        
            name = self._get_name()
            
            self.orig_curve = transforms_to_curve(self.buffer_joints, self.span_count, name)
            self.curve = cmds.duplicate(self.orig_curve)[0]
            
            cmds.rebuildCurve(self.curve, 
                              spans = self.control_count - 1 ,
                              rpo = True,  
                              rt = 0, 
                              end = 1, 
                              kr = False, 
                              kcp = False, 
                              kep = True,  
                              kt = False,
                              d = 3)
            
            name = self.orig_curve
            self.orig_curve = cmds.rename(self.orig_curve, inc_name('orig_curve'))
            self.curve = cmds.rename(self.curve, name)
            
            cmds.parent(self.curve, self.setup_group)
            cmds.parent(self.orig_curve, self.setup_group)
    
    def _create_clusters(self):
        
        name = self._get_name()
        
        if self.last_pivot_top_value:
            last_pivot_end = True
            
        if not self.last_pivot_top_value:
            last_pivot_end = False
        
        cluster_group = cmds.group(em = True, n = inc_name('clusters_%s' % name))
        
        self.clusters = cluster_curve(self.curve, name, True, last_pivot_end = last_pivot_end)
        
        cmds.parent(self.clusters, cluster_group)
        cmds.parent(cluster_group, self.setup_group)
    
    def _create_control(self, sub = False):
        

        control = super(SimpleFkCurveRig, self)._create_control(sub = sub)
        
        control = Control(control)
        control.hide_scale_and_visibility_attributes()

        return control.get()
    
    def _create_sub_control(self):
            
        sub_control = Control( self._get_control_name(sub = True) )
        sub_control.color( get_color_of_side( self.side , True)  )
        
        if self.control_shape:
            sub_control.set_curve_type(self.control_shape)
        
        sub_control.scale_shape(self.control_size * .9, 
                                self.control_size * .9,
                                self.control_size * .9)
        
        return sub_control

    def _first_increment(self, control, current_transform):
        
        self.first_control = control
        

        if self.skip_first_control:
            control = Control(control)
            control.delete_shapes()
            self.controls[-1].rename(self.first_control.replace('CNT_', 'ctrl_'))
            self.first_control = self.controls[-1].get()

        if self.sub_controls:
            self.top_sub_control = self.sub_controls[0]
            
            if self.skip_first_control:
                control = Control(self.sub_controls[0])
                control.delete_shapes()
                self.top_sub_control = cmds.rename(self.top_sub_control, self.top_sub_control.replace('CNT_', 'ctrl_'))
                self.sub_controls[0] = self.top_sub_control
    
    def _increment_greater_than_zero(self, control, current_transform):
        cmds.parent(self.current_xform_group, self.controls[-2].get())    

    def _last_increment(self, control, current_transform):
        
        if self.create_follows:
            
            create_follow_fade(self.controls[-1].get(), self.sub_drivers[:-1])
            create_follow_fade(self.sub_controls[-1], self.sub_drivers[:-1])
            create_follow_fade(self.sub_controls[0], self.sub_drivers[1:])
            create_follow_fade(self.sub_drivers[0], self.sub_drivers[1:])
        
        top_driver = self.drivers[-1]
        
        if self.create_follows:
            if not type(top_driver) == list:
                create_follow_fade(self.drivers[-1], self.sub_drivers[:-1])

    def _all_increments(self, control, current_transform):
        
        match = MatchSpace(self.clusters[self.current_increment], self.current_xform_group)
        match.translation_to_rotate_pivot()
        
        if self.orient_controls_to_joints:
            
            if not self.orient_joint:
                joint = self._get_closest_joint()
            if self.orient_joint:
                joint = self.orient_joint
                
            match = MatchSpace(joint, self.current_xform_group)
            match.rotation()
        
        if self.sub_control_on:
            
            sub_control = self._create_sub_control()
            sub_control_object = sub_control
            sub_control = sub_control.get()
        
            match = MatchSpace(control, sub_control)
            match.translation_rotation()
        
            xform_sub_control = create_xform_group(sub_control)
            self.sub_drivers.append( create_xform_group(sub_control, 'driver') )
            
            cmds.parentConstraint(sub_control, self.clusters[self.current_increment], mo = True)
            
            cmds.parent(xform_sub_control, self.control)
            
            self.sub_controls.append(sub_control)
            
            sub_vis = MayaNumberVariable('subVisibility')
            sub_vis.set_variable_type(sub_vis.TYPE_BOOL)
            sub_vis.create(control)
            sub_vis.connect_out('%sShape.visibility' % sub_control)
                
            sub_control_object.hide_scale_and_visibility_attributes()
            
        if not self.sub_control_on:
            cmds.parentConstraint(control, self.clusters[self.current_increment], mo = True)
        
        increment = self.current_increment+1
        
        if increment in self.control_xform:
            vector = self.control_xform[increment]
            cmds.move(vector[0], vector[1],vector[2], self.current_xform_group, r = True)
        
        cmds.parent(self.current_xform_group, self.control_group)
        
    def _get_closest_joint(self):
        
        current_cluster = self.clusters[self.current_increment]
        
        return get_closest_transform(current_cluster, self.buffer_joints)            
    
    def _setup_stretchy(self):
        if not self.attach_joints:
            return
        
        if self.stretchy:    
            create_spline_ik_stretch(self.ik_curve, self.buffer_joints[:-1], self.controls[-1].get(), self.stretch_on_off)
    
    def _loop(self, transforms):
                
        self._create_curve()
        self._create_clusters()
        
        super(SimpleFkCurveRig, self)._loop(self.clusters)

    def _create_ik_curve(self, curve):
        
        if self.span_count == self.control_count:
            self.ik_curve = curve
            return 
        
        if self.wire_hires:
            
            self.ik_curve = cmds.duplicate(self.orig_curve)[0]
            cmds.setAttr('%s.inheritsTransform' % self.ik_curve, 1)
            self.ik_curve = cmds.rename(self.ik_curve, 'ik_%s' % curve)
            cmds.rebuildCurve(self.ik_curve, 
                              ch = False, 
                              spans = self.span_count,
                              rpo = True,  
                              rt = 0, 
                              end = 1, 
                              kr = False, 
                              kcp = False, 
                              kep = True,  
                              kt = False,
                              d = 3)
            
            wire, base_curve = cmds.wire( self.ik_curve, 
                                          w = curve, 
                                          dds=[(0, 1000000)], 
                                          gw = False, 
                                          n = 'wire_%s' % self.curve)
            
            cmds.setAttr('%sBaseWire.inheritsTransform' % base_curve, 1)
            
            return
            
        if not self.wire_hires:
          
            cmds.rebuildCurve(curve, 
                              ch = True, 
                              spans = self.span_count,
                              rpo = True,  
                              rt = 0, 
                              end = 1, 
                              kr = False, 
                              kcp = False, 
                              kep = True,  
                              kt = False,
                              d = 3)
            
            self.ik_curve = curve
            return

    def _create_ribbon(self):
        pass
        
    def _create_spline_ik(self):
        
        self._create_ik_curve(self.curve)
        
        if self.buffer_joints:
            joints = self.buffer_joints
        if not self.buffer_joints:
            joints = self.joints
            

        if self.fix_x_axis:
            duplicate_hierarchy = DuplicateHierarchy( joints[0] )
        
            duplicate_hierarchy.stop_at(self.joints[-1])
            
            prefix = 'joint'
            if self.create_buffer_joints:
                prefix = 'buffer'
            
            duplicate_hierarchy.replace(prefix, 'xFix')
            x_joints = duplicate_hierarchy.create()
            cmds.parent(x_joints[0], self.setup_group)
            
            #working here to add auto fix to joint orientation.
            
            for inc in range(0, len(x_joints)):
                attributes = OrientJointAttributes(x_joints[inc])
                #attributes.delete()
                
                orient = OrientJoint(x_joints[inc])
                
                aim = 3
                if inc == len(x_joints)-1:
                    aim = 5
                orient.set_aim_at(aim)
                
                aim_up = 0
                if inc > 0:
                    aim_up = 1
                orient.set_aim_up_at(aim_up)
                
                orient.run()
            
            self._attach_joints(x_joints, joints)
            
            joints = x_joints
            self.buffer_joints = x_joints
            
        children = cmds.listRelatives(joints[-1])
        
        if children:
            cmds.parent(children, w = True)
        
        handle = cmds.ikHandle( sol = 'ikSplineSolver', 
                       ccv = False, 
                       pcv = False , 
                       sj = joints[0], 
                       ee = joints[-1], 
                       c = self.ik_curve, n = 'splineIk_%s' % self._get_name())[0]
        
        if children:
            cmds.parent(children, joints[-1])
            
        cmds.parent(handle, self.setup_group)
        
        if self.advanced_twist:
            start_locator = cmds.spaceLocator(n = self._get_name('locatorTwistStart'))[0]
            end_locator = cmds.spaceLocator(n = self._get_name('locatorTwistEnd'))[0]
            
            self.start_locator = start_locator
            self.end_locator = end_locator
            
            cmds.hide(start_locator, end_locator)
            
            match = MatchSpace(self.buffer_joints[0], start_locator)
            match.translation_rotation()
            
            match = MatchSpace(self.buffer_joints[-1], end_locator)
            match.translation_rotation()
                        
            cmds.setAttr('%s.dTwistControlEnable' % handle, 1)
            cmds.setAttr('%s.dWorldUpType' % handle, 4)
            cmds.connectAttr('%s.worldMatrix' % start_locator, '%s.dWorldUpMatrix' % handle)
            cmds.connectAttr('%s.worldMatrix' % end_locator, '%s.dWorldUpMatrixEnd' % handle)
            
            if hasattr(self, 'top_sub_control'):
                cmds.parent(start_locator, self.sub_controls[0])
                
            if not hasattr(self, 'top_sub_control'):
                cmds.parent(start_locator, self.sub_controls[0])
                
            cmds.parent(end_locator, self.sub_controls[-1])
            
        if not self.advanced_twist and self.buffer_joints != self.joints:
            
            follow = create_follow_group(self.controls[0].get(), self.buffer_joints[0])
            cmds.parent(follow, self.setup_group)
            
        if not self.advanced_twist:
            var = MayaNumberVariable('twist')
            var.set_variable_type(var.TYPE_DOUBLE)
            var.create(self.controls[0].get())
            var.connect_out('%s.twist' % handle)
    
    def set_control_xform(self, vector, inc):
        self.control_xform[inc] = vector
    
    def set_orient_joint(self, joint):
        self.orient_joint = joint
    
    def set_orient_controls_to_joints(self, bool_value):
        self.orient_controls_to_joints = bool_value
    
    def set_advanced_twist(self, bool_value):
        self.advanced_twist = bool_value
    
    def set_control_count(self, int_value, span_count = None, wire_hires = False):
        if int_value == 0 or int_value < 2:
            int_value = 2
            
        self.control_count = int_value
        
        if not span_count:
            self.span_count = self.control_count
            
        if span_count:
            self.span_count = span_count
            self.wire_hires = wire_hires
            
    
    def set_sub_control(self, bool_value):
        
        self.sub_control_on = bool_value
    
    def set_stretchy(self, bool_value):
        self.stretchy = bool_value
        
    def set_stretch_on_off(self, bool_value):
        self.stretch_on_off = bool_value
    
    def set_curve(self, curve):
        self.curve = curve
        
    def set_ribbon(self, bool_value):
        self.ribbon = bool_value
        
    def set_ribbon_offset(self, float_value):
        
        self.ribbon_offset = float_value
        
    def set_ribbon_offset_axis(self, axis_letter):
        self.ribbon_offset_axis = axis_letter
        
    def set_last_pivot_top(self, bool_value):
        self.last_pivot_top_value = bool_value
    
    def set_fix_x_axis(self, bool_value):
        self.fix_x_axis = bool_value

    def set_skip_first_control(self, bool_value):
        self.skip_first_control = bool_value
        
    def set_create_follows(self, bool_value):
        self.create_follows = bool_value
        
    def create(self):
        super(SimpleFkCurveRig, self).create()
        
        if not self.ribbon:
            self._create_spline_ik()
            self._setup_stretchy()
            
        if self.ribbon:
            surface = transforms_to_nurb_surface(self.buffer_joints, self._get_name(), spans = self.control_count-1, offset_amount = self.ribbon_offset, offset_axis = self.ribbon_offset_axis)
            
            cmds.setAttr('%s.inheritsTransform' % surface, 0)
            
            cluster_surface = ClusterSurface(surface, self._get_name())
            cluster_surface.set_join_ends(True)
            cluster_surface.create()
            handles = cluster_surface.handles
            
            self.ribbon_clusters = handles
            
            for inc in range(0, len(handles)):
                cmds.parentConstraint(self.sub_controls[inc], handles[inc], mo = True)
                
            cmds.parent(surface, self.setup_group)
            cmds.parent(handles, self.setup_group)
            
            if self.attach_joints:
                for joint in self.buffer_joints:
                    rivet = attach_to_surface(joint, surface)
                    cmds.setAttr('%s.inheritsTransform' % rivet, 0)
                    cmds.parent(rivet, self.setup_group)
        
        cmds.delete(self.orig_curve) 
    
class FkCurveRig(SimpleFkCurveRig):
    
    def __init__(self, name, side):
        super(FkCurveRig, self).__init__(name, side)
        
        
        self.aim_end_vectors = False
        
    def _create_aims(self, clusters):
        
        control1 = self.sub_controls[0]
        control2 = self.sub_controls[-1]
        
        cluster1 = clusters[0]
        cluster2 = clusters[-1]
        
        cmds.delete( cmds.listRelatives(cluster1, ad = True, type = 'constraint') )
        cmds.delete( cmds.listRelatives(cluster2, ad = True, type = 'constraint') )
        
        aim1 = cmds.group(em = True, n = inc_name('aimCluster_%s_1' % self._get_name()))
        aim2 = cmds.group(em = True, n = inc_name('aimCluster_%s_2' % self._get_name()))
        
        xform_aim1 = create_xform_group(aim1)
        xform_aim2 = create_xform_group(aim2)
        
        MatchSpace(control1, xform_aim1).translation()
        MatchSpace(control2, xform_aim2).translation()
        
        cmds.parentConstraint(control1, xform_aim1,  mo = True)
        cmds.parentConstraint(control2, xform_aim2,  mo = True)
        
        mid_control_id = len(self.sub_controls)/2
        
        cmds.aimConstraint(self.sub_controls[mid_control_id], aim1, wuo = self.controls[0].get(), wut = 'objectrotation')
        cmds.aimConstraint(self.sub_controls[mid_control_id], aim2, wuo = self.controls[-1].get(), wut = 'objectrotation')

        cmds.parent(cluster1, aim1)
        cmds.parent(cluster2, aim2)
        
        cmds.parent(xform_aim1, xform_aim2, self.setup_group)
    
    def set_aim_end_vectors(self, bool_value):
        self.aim_end_vectors = bool_value
        
    def create(self):
        super(FkCurveRig, self).create()
        
        if self.aim_end_vectors:    
            if not self.ribbon:
                self._create_aims(self.clusters)
            if self.ribbon:
                self._create_aims(self.ribbon_clusters)

class FkCurveLocalRig(FkCurveRig):
    
    def __init__(self, description, side):
        super(FkCurveLocalRig, self).__init__(description, side)
        
        self.last_local_group = None
        self.last_local_xform = None
        self.local_parent = None     
        self.sub_local_controls = []
        
    def _all_increments(self, control, current_transform):
        
        match = MatchSpace(self.clusters[self.current_increment], self.current_xform_group)
        match.translation_to_rotate_pivot()
        
        if self.orient_controls_to_joints:
            
            closest_joint = self._get_closest_joint()
            
            match = MatchSpace(closest_joint, self.current_xform_group)
            match.rotation()
        
        if self.sub_control_on:
            
            sub_control = Control( self._get_control_name(sub = True) )
        
            sub_control.color( get_color_of_side( self.side , True)  )
            
            sub_control_object = sub_control
            sub_control = sub_control.get()
            
            match = MatchSpace(control, sub_control)
            match.translation_rotation()
        
            xform_sub_control = create_xform_group(sub_control)
            self.sub_drivers.append( create_xform_group(sub_control, 'driver') )
            
            local_group, local_xform = constrain_local(sub_control, self.clusters[self.current_increment])
            
            self.sub_local_controls.append( local_group )
            
            cmds.parent(local_xform, self.setup_group)
            
            control_local_group, control_local_xform = constrain_local(control, local_xform)
            cmds.parent(control_local_xform, self.setup_group)
            
            
            if self.last_local_group:
                cmds.parent(control_local_xform, self.last_local_group)
            
            self.last_local_group = control_local_group
            self.last_local_xform = control_local_xform
            
            cmds.parent(xform_sub_control, self.control)
            self.sub_controls.append(sub_control)
            
            sub_vis = MayaNumberVariable('subVisibility')
            sub_vis.set_variable_type(sub_vis.TYPE_BOOL)
            sub_vis.create(control)
            sub_vis.connect_out('%sShape.visibility' % sub_control)
            
            sub_control_object.hide_scale_and_visibility_attributes()
            
        if not self.sub_control_on:
            
            constrain_local(control, self.clusters[self.current_increment])
        
        cmds.parent(self.current_xform_group, self.control_group)
        
    def _first_increment(self, control, current_transform):
        super(FkCurveLocalRig, self)._first_increment(control, current_transform)
        
        if self.local_parent:
            cmds.parent(self.last_local_xform, self.local_parent)
    
    def _create_spline_ik(self):
        
        self._create_ik_curve(self.curve)
        
        children = cmds.listRelatives(self.buffer_joints[-1], c = True)
        
        if children:
            cmds.parent(children, w = True)
        
        handle = cmds.ikHandle( sol = 'ikSplineSolver', 
                       ccv = False, 
                       pcv = False , 
                       sj = self.buffer_joints[0], 
                       ee = self.buffer_joints[-1], 
                       c = self.curve)[0]
        
        if children:
            cmds.parent(children, self.buffer_joints[-1])
            
        cmds.parent(handle, self.setup_group)
        
        if self.advanced_twist:
            
            start_locator = cmds.spaceLocator(n = self._get_name('locatorTwistStart'))[0]
            end_locator = cmds.spaceLocator(n = self._get_name('locatorTwistEnd'))[0]
            
            self.start_locator = start_locator
            self.end_locator = end_locator
            
            cmds.hide(start_locator, end_locator)
            
            match = MatchSpace(self.buffer_joints[0], start_locator)
            match.translation_rotation()
            
            match = MatchSpace(self.buffer_joints[-1], end_locator)
            match.translation_rotation()
            
            
            cmds.setAttr('%s.dTwistControlEnable' % handle, 1)
            cmds.setAttr('%s.dWorldUpType' % handle, 4)
            cmds.connectAttr('%s.worldMatrix' % start_locator, '%s.dWorldUpMatrix' % handle)
            cmds.connectAttr('%s.worldMatrix' % end_locator, '%s.dWorldUpMatrixEnd' % handle)
            
            if hasattr(self, 'top_sub_control'):
                cmds.parent(start_locator, self.sub_local_controls[0])
                
            if not hasattr(self, 'top_sub_control'):
                cmds.parent(start_locator, self.sub_local_controls[0])
                
            
            cmds.parent(end_locator, self.sub_local_controls[-1])
            
        if not self.advanced_twist:
            
            create_local_follow_group(self.controls[0].get(), self.buffer_joints[0])
            #constrain_local(self.controls[0].get(), self.buffer_joints[0])
            
    def set_local_parent(self, parent):
        self.local_parent = parent

    def create(self):
        super(SimpleFkCurveRig, self).create()
        
        if not self.ribbon:
            self._create_spline_ik()
            self._setup_stretchy()
            
        if self.ribbon:
            surface = transforms_to_nurb_surface(self.buffer_joints, self._get_name(), spans = self.control_count-1, offset_amount = self.ribbon_offset, offset_axis = self.ribbon_offset_axis)
            
            cmds.setAttr('%s.inheritsTransform' % surface, 0)
            
            cluster_surface = ClusterSurface(surface, self._get_name())
            cluster_surface.set_join_ends(True)
            cluster_surface.create()
            handles = cluster_surface.handles
            
            self.ribbon_clusters = handles
            
            for inc in range(0, len(handles)):
                
                cmds.parentConstraint(self.sub_local_controls[inc], handles[inc], mo = True)
                #cmds.parent(handles[inc], self.sub_local_controls[inc])
            
            cmds.parent(surface, self.setup_group)
            cmds.parent(handles, self.setup_group)
            
            for joint in self.buffer_joints:
                rivet = attach_to_surface(joint, surface)
                cmds.setAttr('%s.inheritsTransform' % rivet, 0)
                cmds.parent(rivet, self.setup_group)
        
        cmds.delete(self.orig_curve) 

class PointingFkCurveRig(SimpleFkCurveRig): 
    def _create_curve(self):
        
        if not self.curve:
        
            name = self._get_name()
            
            self.set_control_count(1)
            
            self.curve = transforms_to_curve(self.buffer_joints, self.control_count - 1, name)
            
            self.curve = cmds.rebuildCurve( self.curve, 
                                   constructionHistory = False,
                                   replaceOriginal = True,
                                   rebuildType = 0,
                                   endKnots = 1,
                                   keepRange = 0,
                                   keepControlPoints = 0, 
                                   keepEndPoints = 1, 
                                   keepTangents = 0, 
                                   spans = 1,
                                   degree =3,
                                   name = name)[0]
            
            
            
            cmds.parent(self.curve, self.setup_group)
    
    def _create_clusters(self):
        
        name = self._get_name()
        
        cluster_group = cmds.group(em = True, n = inc_name('clusters_%s' % name))
        
        btm_handle = cmds.cluster('%s.cv[0]' % self.curve, n = name)[1]
        mid_handle = cmds.cluster('%s.cv[1:2]' % self.curve, n = name)[1]
    
        pos = cmds.xform('%s.cv[1]' % self.curve, q = True, ws = True, t = True)
        cmds.xform(mid_handle, ws = True, rp = pos, sp = pos)
    
        top_handle = cmds.cluster('%s.cv[3:4]' % self.curve, n = name)[1]
        
        self.clusters = [btm_handle, mid_handle, top_handle]
        
        cmds.parent(self.clusters, cluster_group)
        cmds.parent(cluster_group, self.setup_group)
    
    def _last_increment(self, control, current_transform):
        pass
    
    def create(self):
        super(PointingFkCurveRig, self).create()
        
        constraint_editor = ConstraintEditor()
        constraint = constraint_editor.get_constraint(self.clusters[-1], 'parentConstraint')
        
        cmds.delete(constraint)
        cmds.parentConstraint(self.controls[-1].get(), self.clusters[-1])
        
        create_local_follow_group(self.sub_controls[-1], self.buffer_joints[-1], orient_only = False)
        cmds.setAttr('%s.subVisibility' % self.controls[-1].get(), 1)
        create_follow_group(self.buffer_joints[-2], 'xform_%s' % self.sub_controls[-1])
        
        cmds.parent(self.end_locator, self.controls[-1].get())

class NeckRig(FkCurveRig):
    def _first_increment(self, control, current_transform):
        
        self.first_control = control
        
        #cmds.parentConstraint(self.first_control, self.clusters[self.current_increment], mo = True)
        
        
        #cmds.parent(self.current_xform_group, self.control_group)



    


class IkSplineNubRig(BufferRig):
    
    def __init__(self, description, side):
        
        
        
        super(IkSplineNubRig, self).__init__(description, side)
        
        self.end_with_locator = False
        self.top_guide = None
        self.btm_guide = None
        
        self.bool_create_middle_control = True
        
        self.control_shape = 'pin'
        
    def _duplicate_joints(self):
        
        if self.create_buffer_joints:
            duplicate_hierarchy = DuplicateHierarchy( self.joints[0] )
            
            duplicate_hierarchy.stop_at(self.joints[-1])
            duplicate_hierarchy.replace('joint', 'buffer')
            
            self.buffer_joints = duplicate_hierarchy.create()
    
            cmds.parent(self.buffer_joints[0], self.setup_group)

        if not self.create_buffer_joints:
            self.buffer_joints = self.joints
        
        return self.buffer_joints
    """
    def _duplicate_joints(self):
        
        duplicate_hierarchy = DuplicateHierarchy( self.joints[0] )
        
        duplicate_hierarchy.stop_at(self.joints[-1])
        duplicate_hierarchy.replace('joint', 'buffer')
        
        self.buffer_joints = duplicate_hierarchy.create()

        cmds.parent(self.buffer_joints[0], self.setup_group)
        
        return self.buffer_joints
    """
    def _create_twist_group(self, top_control, top_handle, top_guide):
        
        name = self._get_name()
        
        twist_guide_group = cmds.group(em = True, n = inc_name('guideSetup_%s' % name))
        cmds.hide(twist_guide_group)
        
        cmds.parent([top_guide, top_handle], twist_guide_group)
        
        cmds.parent(twist_guide_group, self.setup_group)
        
        cmds.parentConstraint(top_control, twist_guide_group,mo = True)
        
        self.end_locator = True
        
    def _create_joint_line(self):
    
        name = self._get_name()
    
        position_top = cmds.xform(self.buffer_joints[0], q = True, t = True, ws = True)
        position_btm = cmds.xform(self.buffer_joints[-1], q = True, t = True, ws = True)
    
        cmds.select(cl = True)
        guide_top = cmds.joint( p = position_top, n = inc_name('topTwist_%s' % name) )
        
        cmds.select(cl = True)
        guide_btm = cmds.joint( p = position_btm, n = inc_name('btmTwist_%s' % name) )
        
        MatchSpace(self.buffer_joints[0], guide_top).rotation()
        
        cmds.makeIdentity(guide_top, r = True, apply = True)
        
        cmds.parent(guide_btm, guide_top)
        
        cmds.makeIdentity(guide_btm, r = True, jo = True, apply = True)
        
        handle = cmds.ikHandle(sj = guide_top, 
                               ee = guide_btm, 
                               solver = 'ikSCsolver', 
                               name = inc_name('handle_%s' % name))[0]
        
        return guide_top, handle
    
    def _create_spline(self, follow, btm_constrain, mid_constrain):
        
        name = self._get_name()
        
        spline_setup_group = cmds.group( em = True, n = inc_name('splineSetup_%s' % name))
        cmds.hide(spline_setup_group)
        cluster_group = cmds.group( em = True, n = inc_name('clusterSetup_%s' % name))
        
        handle, effector, curve = cmds.ikHandle(sj = self.buffer_joints[0], 
                                                ee = self.buffer_joints[-1], 
                                                sol = 'ikSplineSolver', 
                                                pcv = False, 
                                                name = inc_name('handle_spline_%s' % name))
        
        cmds.setAttr('%s.inheritsTransform' % curve, 0)
        
        
        
        curve = cmds.rename(curve, inc_name('curve_%s' % name) )
        
        top_cluster, top_handle = cmds.cluster('%s.cv[0]' % curve, n = 'clusterTop_%s' % name)
        mid_cluster, mid_handle = cmds.cluster('%s.cv[1:2]' % curve, n = 'clusterMid_%s' % name)
        btm_cluster, btm_handle = cmds.cluster('%s.cv[3]' % curve, n = 'clusterBtm_%s' % name)
        
        cmds.parent([top_handle, mid_handle, btm_handle], cluster_group )
        cmds.parent([handle, curve], spline_setup_group)
        cmds.parent(cluster_group, spline_setup_group)
        
        cmds.parent(spline_setup_group, self.setup_group)
        
        cmds.parentConstraint(follow, cluster_group, mo = True)
        
        cmds.pointConstraint(btm_constrain, btm_handle, mo = True)
        cmds.parentConstraint(mid_constrain, mid_handle, mo = True)
        
        
        
        return handle, curve
    
    def _setup_stretchy(self, curve, control):
        
        create_spline_ik_stretch(curve, self.buffer_joints[:-1], control)
    
    def _create_top_control(self):
        
        if not self.end_with_locator:
            control = self._create_control('top')
        if self.end_with_locator:
            control = self._create_control()
            
        control.set_curve_type(self.control_shape)
            
        control.hide_scale_and_visibility_attributes()
        
        xform = create_xform_group(control.get())
        
        match = MatchSpace(self.joints[0], xform)
        match.translation_rotation()
        
        return control.get(), xform
    
    def _create_btm_control(self):
        control = self._create_control('btm')
        control.hide_scale_and_visibility_attributes()
        
        control.set_curve_type(self.control_shape)
        
        xform = create_xform_group(control.get())
        
        match = MatchSpace(self.joints[-1], xform)
        match.translation_rotation()
        
        return control.get(), xform
    
    def _create_btm_sub_control(self):
        control = self._create_control('btm', sub = True)
        control.scale_shape(.5, .5, .5)
        control.hide_scale_and_visibility_attributes()
        
        control.set_curve_type(self.control_shape)
        
        xform = create_xform_group(control.get())
        
        match = MatchSpace(self.joints[-1], xform)
        match.translation_rotation()
        
        return control.get(), xform
        
    def _create_mid_control(self):
        
        if self.bool_create_middle_control:
            control = self._create_control('mid', sub = True)
            control.scale_shape(.5, .5, .5)
            control.hide_scale_and_visibility_attributes()
            
            control.set_curve_type(self.control_shape)
            control = control.get()
        
        if not self.bool_create_middle_control:
            mid_locator = cmds.spaceLocator(n = inc_name(self._get_name('locator', 'mid')))[0]
            control = mid_locator
            cmds.hide(mid_locator)
        
        xform = create_xform_group(control)
        
        match = MatchSpace(self.joints[0], xform)
        match.rotation()
        
        return control, xform
    
    def set_end_with_locator(self, True):
        self.end_with_locator = True
    
    def set_guide_top_btm(self, top_guide, btm_guide):
        self.top_guide = top_guide
        self.btm_guide = btm_guide
    
    def set_control_shape(self, name):
        self.control_shape = name
    
    def set_create_middle_control(self, bool_value):
        
        self.bool_create_middle_control = bool_value
    
    def create(self):
        super(IkSplineNubRig, self).create()
        
        
        top_control, top_xform = self._create_top_control()
        
        self.top_control = top_control
        self.top_xform = top_xform
        
        if not self.end_with_locator:
            btm_control, btm_xform = self._create_btm_control()
            sub_btm_control, sub_btm_xform = self._create_btm_sub_control()
            cmds.parent(sub_btm_xform, btm_control)
            
        if self.end_with_locator:
            
            btm_control = cmds.spaceLocator(n = inc_name('locator_%s' % self._get_name()))[0]
            btm_xform = btm_control
            sub_btm_control = btm_control
            cmds.hide(btm_control)
            
            match = MatchSpace(self.buffer_joints[-1], btm_control)
            match.translation_rotation()
        
        self.btm_control = btm_control
        self.btm_xform = btm_xform
            
        mid_control, mid_xform = self._create_mid_control()
        
        cmds.parent(top_xform, self.control_group)
            
        cmds.parent(mid_xform, top_control)
        
        top_joint, handle = self._create_joint_line()
        sub_joint, sub_handle = self._create_joint_line()
        cmds.parent(sub_joint, top_joint)
        cmds.parent(sub_handle, top_joint)
        
        self._create_twist_group(top_control, handle, top_joint)
        
        create_follow_group(top_joint, mid_xform)
        cmds.pointConstraint(top_control, sub_btm_control, mid_xform)
        
        spline_handle, curve = self._create_spline(top_joint, sub_btm_control, mid_control)
        #cmds.connectAttr( '%s.rotateX' % sub_joint, '%s.twist' % spline_handle)
        
        self._setup_stretchy(curve, top_control)
        
        cmds.parentConstraint(top_control, top_joint, mo = True)
        cmds.parentConstraint(sub_btm_control, sub_handle, mo = True)
        
        top_twist = cmds.group(em = True, n = 'topTwist_%s' % spline_handle)
        btm_twist = cmds.group(em = True, n = 'btmTwist_%s' % spline_handle)
        
        cmds.parent(btm_twist, sub_joint)
        
        match = MatchSpace(self.buffer_joints[0], top_twist)
        match.translation_rotation()
        
        match = MatchSpace(self.buffer_joints[-1], btm_twist)
        match.translation_rotation()
        
        cmds.setAttr('%s.dTwistControlEnable' % spline_handle, 1)
        cmds.setAttr('%s.dWorldUpType' % spline_handle, 4)
        
        cmds.connectAttr('%s.worldMatrix' % top_twist, '%s.dWorldUpMatrix' % spline_handle)
        cmds.connectAttr('%s.worldMatrix' % btm_twist, '%s.dWorldUpMatrixEnd' % spline_handle)
        
        
        cmds.parent(top_twist, top_control)
        #cmds.parent(btm_twist, sub_btm_control)
        
        cmds.pointConstraint(sub_btm_control, handle, mo = True)
        
        cmds.parent(btm_xform, top_control)
        
        if self.top_guide:
            cmds.parentConstraint(self.top_guide, top_xform, mo =  True)
        
        if self.btm_guide:
            cmds.parent(btm_xform, self.btm_guide)


class IkAppendageRig(BufferRig):
    
    def __init__(self, description, side):
        super(IkAppendageRig, self).__init__(description, side)
        
        self.create_twist = True
        self.create_stretchy = False
        self.btm_control = None
        self.offset_pole_locator = None
        self.pole_offset = 3
        self.right_side_fix = True
        self.orient_constrain = True
        self.curve_type = None
        self.create_sub_control = True
        self.sub_control = None
        self.top_as_locator = False
        self.match_btm_to_joint = True
        self.create_world_switch = True
        self.create_top_control = True
        self.pole_angle_joints = []
    
    def _attach_ik_joints(self, source_chain, target_chain):
        
        for inc in range( 0, len(source_chain) ):
            source = source_chain[inc]
            target = target_chain[inc]
            
            cmds.parentConstraint(source, target)
            connect_scale(source, target)
            
    def _duplicate_joints(self):
        
        super(IkAppendageRig, self)._duplicate_joints()
        
        duplicate = DuplicateHierarchy(self.joints[0])
        duplicate.stop_at(self.joints[-1])
        duplicate.replace('joint', 'ik')
        self.ik_chain = duplicate.create()
                
        self._attach_ik_joints(self.ik_chain, self.buffer_joints)
        
        ik_group = self._create_group()
        
        cmds.parent(self.ik_chain[0], ik_group)
        cmds.parent(ik_group, self.setup_group)
    
    def _create_buffer_joint(self):
        
        buffer_joint = cmds.duplicate(self.ik_chain[-1], po = True)[0]
        
        cmds.parent(self.ik_chain[-1], buffer_joint)
        
        if not cmds.isConnected('%s.scale' % buffer_joint, '%s.inverseScale' % self.ik_chain[-1]):
            cmds.connectAttr('%s.scale' % buffer_joint, '%s.inverseScale' % self.ik_chain[-1])
                
        attributes = ['rotateX',
                      'rotateY',
                      'rotateZ',
                      'jointOrientX',
                      'jointOrientY',
                      'jointOrientZ'
                      ]
        
        for attribute in attributes:
            cmds.setAttr('%s.%s' % (self.ik_chain[-1], attribute), 0)
        
        return buffer_joint
        
    def _create_ik_handle(self):
        
        buffer_joint = self._create_buffer_joint()
        
        ik_handle = IkHandle( self._get_name() )
        
        ik_handle.set_start_joint( self.ik_chain[0] )
        ik_handle.set_end_joint( buffer_joint )
        ik_handle.set_solver(ik_handle.solver_rp)
        self.ik_handle = ik_handle.create()
        
        xform_ik_handle = create_xform_group(self.ik_handle)
        cmds.parent(xform_ik_handle, self.setup_group)
        
        cmds.hide(xform_ik_handle)
        
    def _create_top_control(self):
        
        if not self.top_as_locator:
            control = self._create_control(description = 'top')
            control.hide_scale_and_visibility_attributes()
        
            if self.curve_type:
                control.set_curve_type(self.curve_type)
            
                control.scale_shape(2, 2, 2)
        
            self.top_control = control.get()
            
        if self.top_as_locator:
            self.top_control = cmds.spaceLocator(n = 'locator_%s' % self._get_name())[0]
        
        return self.top_control
    
    def _xform_top_control(self, control):
        
        match = MatchSpace(self.ik_chain[0], control)
        match.translation_rotation()
        
        cmds.parentConstraint(control, self.ik_chain[0], mo = True)
        
        xform_group = create_xform_group(control)
        
        cmds.parent(xform_group, self.control_group)
    
    def _create_btm_control(self):
        
        control = self._create_control(description = 'btm')
        control.hide_scale_and_visibility_attributes()
        
        if self.curve_type:
            control.set_curve_type(self.curve_type)
            
        control.scale_shape(2, 2, 2)
        
        self.btm_control = control.get()
        
        self._fix_right_side_orient( control.get() )
        
        if self.create_sub_control:
            sub_control = self._create_control('BTM', sub = True)
            
            sub_control.hide_scale_and_visibility_attributes()
            
            xform_group = create_xform_group( sub_control.get() )
            
            self.sub_control = sub_control.get()
        
            cmds.parent(xform_group, control.get())
            
            connect_visibility('%s.subVisibility' % self.btm_control, '%sShape' % self.sub_control, 1)
        
        return control.get()
    
    def _fix_right_side_orient(self, control):
        
        if not self.right_side_fix:
            return
        
        if not self.side == 'R':
            return
        
        xform_locator = cmds.spaceLocator()[0]
        
        match = MatchSpace(control, xform_locator)
        match.translation_rotation()
        
        spacer = create_xform_group(xform_locator)
        
        cmds.setAttr('%s.rotateY' % xform_locator, 180)
        cmds.setAttr('%s.rotateZ' % xform_locator, 180)
        
        match = MatchSpace(xform_locator, control)
        match.translation_rotation()
        
        cmds.delete(spacer)
        
    def _xform_btm_control(self, control):
        
        if self.match_btm_to_joint:
            match = MatchSpace(self.ik_chain[-1], control)
            match.translation_rotation()
        if not self.match_btm_to_joint:
            MatchSpace(self.ik_chain[-1], control).translation()
        
        self._fix_right_side_orient(control)
        
        ik_handle_parent = cmds.listRelatives(self.ik_handle, p = True)[0]
        
        if self.sub_control:
            cmds.parent(ik_handle_parent, self.sub_control)
        if not self.sub_control:
            cmds.parent(ik_handle_parent, control)
        #cmds.parentConstraint(self.sub_control, ik_handle_parent, mo = True)
        
        xform_group = create_xform_group(control)
        drv_group = create_xform_group(control, 'driver')
        
        if self.create_world_switch:
            self._create_local_to_world_switch(control, xform_group, drv_group)
        
        cmds.parent(xform_group, self.control_group)
        
        if self.orient_constrain:
            
            if self.sub_control:
                cmds.orientConstraint(self.sub_control, self.ik_chain[-1], mo = True)
                
            if not self.sub_control:
                cmds.orientConstraint(control, self.ik_chain[-1], mo = True)
        
    def _create_local_to_world_switch(self, control, xform_group, driver_group):
        
        cmds.addAttr(control, ln = 'world', min = 0, max = 1, dv = 0, at = 'double', k = True)
        
        local_group = self._create_group('IkLocal')
        match = MatchSpace(control, local_group)
        match.translation_rotation()
        
        world_group = self._create_group('IkWorld')
        match = MatchSpace(control, world_group)
        match.translation()
        
        cmds.parent([local_group,world_group], xform_group)
        
        cmds.orientConstraint(local_group, driver_group)
        cmds.orientConstraint(world_group, driver_group)
        
        constraint = ConstraintEditor()
        
        active_constraint = constraint.get_constraint(driver_group, constraint.constraint_orient)
        
        constraint.create_switch(control, 'world', active_constraint)
        
        self.world_group = world_group
        self.local_group = local_group
    
    def _create_top_btm_joint(self, joints, prefix):
        top_position = cmds.xform(joints[0], q = True, t = True, ws = True)
        btm_position = cmds.xform(joints[-1], q = True, t = True, ws = True)
        
        top_name = self._get_name(prefix, 'top')
        btm_name = self._get_name(prefix, 'btm')
        
        cmds.select( cl = True )
        
        top_joint = cmds.joint(p = top_position, n = top_name)
        btm_joint = cmds.joint(p = btm_position, n = btm_name)
        
        cmds.joint(top_joint, e = True, zso = True, oj = 'xyz', sao = 'yup')
        
        return [top_joint, btm_joint]
        
    def _create_twist_ik(self, joints, description):
        
        ik_handle = IkHandle(description)
        ik_handle.set_solver(ik_handle.solver_sc)
        ik_handle.set_start_joint(joints[0])
        ik_handle.set_end_joint(joints[-1])
        return ik_handle.create()
        
    def _create_twist_joint(self, top_control):
        
        top_guide_joint, btm_guide_joint = self._create_top_btm_joint( [self.buffer_joints[-1], self.buffer_joints[0]], 'guide')
        top_guidetwist_joint, btm_guidetwist_joint = self._create_top_btm_joint( [self.buffer_joints[0], self.buffer_joints[-1]], 'guideTwist')
        
        self.twist_guide = top_guidetwist_joint
        
        guide_ik = self._create_twist_ik([top_guide_joint, btm_guide_joint], 'guide')
        twist_guide_ik = self._create_twist_ik([top_guidetwist_joint, btm_guidetwist_joint], 'guideTwist')
        
        cmds.parent(top_guidetwist_joint, top_guide_joint)
        cmds.parent(twist_guide_ik, top_guide_joint)
        
        cmds.parent(top_guide_joint, self.setup_group)
        cmds.parent(guide_ik, self.setup_group)
        
        if self.sub_control:
            cmds.pointConstraint( self.sub_control, top_guide_joint )
        if not self.sub_control:
            cmds.pointConstraint( self.btm_control, top_guide_joint )
            
        cmds.pointConstraint( top_control, guide_ik )
        
        if self.sub_control:
            offset_locator = cmds.spaceLocator(n = 'offset_%s' % self.sub_control)[0]
            cmds.parent(offset_locator, self.sub_control)
            
            match = MatchSpace(self.sub_control, offset_locator)
            match.translation_rotation()
            
        if not self.sub_control:
            offset_locator = cmds.spaceLocator(n = 'offset_%s' % self.btm_control)[0]
            cmds.parent(offset_locator, self.btm_control)
            
            match = MatchSpace(self.btm_control, offset_locator)
            match.translation_rotation()
        
        cmds.hide(offset_locator)
        
        cmds.parentConstraint( offset_locator, twist_guide_ik, mo = True )
        
        self.offset_pole_locator = offset_locator
        
    def _get_pole_joints(self):
        if not self.pole_angle_joints:
            mid_joint_index  = len(self.ik_chain)/2
            mid_joint_index = int(mid_joint_index)
            mid_joint = self.ik_chain[mid_joint_index]
            
            joints = [self.ik_chain[0], mid_joint, self.ik_chain[-1]]
            
            return joints
        
        return self.pole_angle_joints            
        
    def _create_pole_vector(self):
        
        control = self._create_control('POLE')
        control.hide_scale_and_visibility_attributes()
        control.set_curve_type('cube')
        self.poleControl = control.get()
        
        pole_var = MayaEnumVariable('POLE_VECTOR')
        pole_var.create(self.btm_control)
        
        pole_vis = MayaNumberVariable('poleVisibility')
        pole_vis.set_variable_type(pole_vis.TYPE_BOOL)
        pole_vis.create(self.btm_control)
        
        
        twist_var = MayaNumberVariable('twist')
        twist_var.create(self.btm_control)
        
        if self.side == 'L':
            twist_var.connect_out('%s.twist' % self.ik_handle)
            
        if self.side == 'R':
            connect_multiply('%s.twist' % self.btm_control, '%s.twist' % self.ik_handle, -1)
        
        pole_joints = self._get_pole_joints()
        
        position = get_polevector( pole_joints[0], pole_joints[1], pole_joints[2], self.pole_offset )
        cmds.move(position[0], position[1], position[2], control.get())

        cmds.poleVectorConstraint(control.get(), self.ik_handle)
        
        xform_group = create_xform_group( control.get() )
        
        if self.create_twist:
            
            follow_group = create_follow_group(self.top_control, xform_group)
            constraint = cmds.parentConstraint(self.twist_guide, follow_group, mo = True)[0]
            
            constraint_editor = ConstraintEditor()
            constraint_editor.create_switch(self.btm_control, 'autoTwist', constraint)
            cmds.setAttr('%s.autoTwist' % self.btm_control, 0)
        
        if not self.create_twist:
            follow_group = create_follow_group(self.top_control, xform_group)
        
        cmds.parent(follow_group,  self.control_group )
        
        name = self._get_name()
        
        rig_line = RiggedLine(pole_joints[1], control.get(), name).create()
        cmds.parent(rig_line, self.control_group)
        
        pole_vis.connect_out('%s.visibility' % xform_group)
        pole_vis.connect_out('%s.visibility' % rig_line)
        
        self.pole_vector_xform = xform_group

    def _create_stretchy(self, top_transform, btm_transform, control):
        stretchy = StretchyChain()
        stretchy.set_joints(self.ik_chain)
        stretchy.set_add_dampen(True)
        stretchy.set_node_for_attributes(control)
        stretchy.set_description(self._get_name())
        
        top_locator, btm_locator = stretchy.create()
        
        cmds.parent(top_locator, top_transform)
        cmds.parent(btm_locator, btm_transform)
        
    def _create_tweakers(self):
        pass
    
    def set_create_twist(self, bool_value):
        
        self.create_twist = bool_value
    
    def set_create_stretchy(self, bool_value):
        self.create_stretchy = bool_value
    
    def set_pole_offset(self, value):
        self.pole_offset = value
    
    def set_pole_angle_joints(self, joints):
        self.pole_angle_joints = joints
    
    def set_right_side_fix(self, bool_value):
        self.right_side_fix = bool_value
    
    def set_orient_constrain(self, bool_value):
        self.orient_constrain = bool_value
        
    def set_curve_type(self, curve_name):
        self.curve_type = curve_name
    
    def set_create_sub_control(self, bool_value):
        self.create_sub_control = bool_value
    
    def set_create_world_switch(self, bool_value):
        self.create_world_switch = bool_value
    
    def set_top_control_as_locator(self, bool_value):
        self.top_as_locator = bool_value
    
    def set_match_btm_to_joint(self, bool_value):
        self.match_btm_to_joint = bool_value
        
    def set_create_top_control(self, bool_value):
        self.create_top_control = bool_value
    
    def create(self):
        super(IkAppendageRig, self).create()
        
        self._create_ik_handle()
        
        
        if self.create_top_control:
            top_control = self._create_top_control()
        if not self.create_top_control:
            top_control = cmds.spaceLocator(n = 'locator_top_%s' % self._get_name())[0]
            self.top_control = top_control
            MatchSpace(self.joints[0], top_control).translation_rotation()
            
        self._xform_top_control(top_control)
        
        btm_control = self._create_btm_control()
        self._xform_btm_control(btm_control)
        
        if self.create_twist:
            self._create_twist_joint(top_control)
        
        self._create_pole_vector()
        
        if self.sub_control:
            self._create_stretchy(top_control, self.sub_control, btm_control)
        if not self.sub_control:
            self._create_stretchy(top_control, self.btm_control, btm_control)

class RopeRig(CurveRig):

    def __init__(self, name, side):
        super(RopeRig, self).__init__(name, side)
        
        self.subdivision = 0
        
        self._sub_run = False
        
        self._division_value = 2
        self.cluster_deformers = []
        
    def _define_control_shape(self):
        return 'cube'

    def _rebuild_curve(self, curve, spans,inc):
        
        if self._sub_run:
            curve_split = curve.split('_')
            curve_split[-1] = 'sub%s' % (inc+1)
            name = string.join(curve_split, '_')
            
        if not self._sub_run:
            name = '%s_sub%s' % (curve, (inc+1))
        
        rebuilt_curve, node = cmds.rebuildCurve( curve, 
                                           constructionHistory = True,
                                           replaceOriginal = False,
                                           rebuildType = 0,
                                           endKnots = 1,
                                           keepRange = 0,
                                           keepControlPoints = 0, 
                                           keepEndPoints = 1, 
                                           keepTangents = 0, 
                                           spans = spans,
                                           degree =3,
                                           name = name)
        
        
        cmds.delete(rebuilt_curve, ch = True)
        
        return rebuilt_curve, node
        
    def _cluster_curve(self, curve, description):
        
        cluster_curve = ClusterCurve(curve, self._get_name(description))
        cluster_curve.create()
        self.cluster_deformers = cluster_curve.clusters
        
        return cluster_curve.get_cluster_handle_list()
    
    def _subdivide(self):
        
        curves = [self.curves[0]]
        
        last_curve = None
        
        for inc in range(0, self.subdivision):


            if last_curve:
                curve = last_curve
            if not last_curve:
                curve = self.curves[0]

            curveObject = nodename_to_mobject(cmds.listRelatives(curve, s = True)[0])
            curve_object = NurbsCurveFunction(curveObject)
            spans = curve_object.get_span_count()
            
            
            rebuilt_curve, rebuild_node = self._rebuild_curve(curve, spans*self._division_value, inc)
            
            curves.append(rebuilt_curve)
            cmds.parent(rebuilt_curve, self.setup_group)
            last_curve = rebuilt_curve
        
            self._sub_run = True
            
        self._sub_run = False
        return curves


        
    def set_subdivisions(self, int_value):
        
        if int_value < 0:
            int_value = 0
        
        self.subdivision = int_value
        
    def set_division_value(self, int_value):
        if int_value < 2:
            int_value = 2
            
        self._division_value = int_value

    def create(self):

        curves = self._subdivide()
        
        
        scale = 1
        
        scale_section = 1.000/len(curves)
        alt_color = False
        
        description = None
        
        inc = 0
        
        last_curve = None

        for curve in curves:
            if inc > 0:
                description = 'sub%s' % inc
            if inc == 0:
                description = 'main'
            
            clusters = self._cluster_curve(curve, description)
            
            control_group = cmds.group(em = True, n = inc_name('controls_%s' % (self._get_name(description))))
            setup_group = cmds.group(em = True, n = inc_name('setup_%s' % (self._get_name(description))))
            
            cmds.parent(control_group, self.control_group)
            cmds.parent(setup_group, self.setup_group)
            
            inc2 = 0
            
            for cluster in clusters:
                
                if description:
                    control = self._create_control(description)
                if not description:
                    control = self._create_control()
                
                if not alt_color:
                    control.color(get_color_of_side(self.side))    
                if alt_color:
                    control.color(get_color_of_side(self.side, sub_color = True))
                
                MatchSpace(cluster, control.get()).translation_to_rotate_pivot()
                
                offset_cluster = cmds.group(em = True, n = 'offset_%s' % cluster)
                MatchSpace(cluster, offset_cluster).translation_to_rotate_pivot()
                
                xform_cluster = create_xform_group(cluster)
                
                cmds.parent(xform_cluster, offset_cluster)
                cmds.parent(offset_cluster, setup_group)
                
                xform_offset = create_xform_group(offset_cluster)
                
                
                control.scale_shape(scale, scale, scale) 
                
                
                xform = create_xform_group(control.get())
                connect_translate(control.get(), cluster)
                
                control.hide_scale_attributes()
                
                if last_curve:
                    attach_to_curve(xform, last_curve)
                    attach_to_curve(xform_offset, last_curve)
                    
                cmds.parent(xform, control_group)
                    
                    
                
                
                inc2 +=1
                
                
            scale = scale - scale_section
            
            last_curve = curve
            
            inc += 1
            
            if alt_color:
                alt_color = False 
                continue
            
            if not alt_color:
                alt_color = True
            
                
class TweakCurveRig(BufferRig):
    
    def __init__(self, name, side):
        super(TweakCurveRig, self).__init__(name, side)
        
        self.control_count = 4
        self.curve = None
        self.surface = None
        self.use_ribbon = True
        
        self.create_buffer_joints = False
        
        self.orient_controls_to_joints = True
        self.orient_joint = None
        
        self.join_both_ends = False
        
        self.ribbon_offset = 1
        self.ribbon_offset_axis = 'Z'
    
    def _create_control(self, sub = False):
        
        control = super(TweakCurveRig, self)._create_control(sub = sub)
        
        control.hide_scale_and_visibility_attributes()
        
        return control.get()
    
    def _create_ik_guide(self):
        
        if not self.use_ribbon:
            if not self.surface:
            
                name = self._get_name()
                
                self.surface = transforms_to_curve(self.buffer_joints, self.control_count, name)
                
                cmds.rebuildCurve(self.surface, 
                                  spans = self.control_count - 1 ,
                                  rpo = True,  
                                  rt = 0, 
                                  end = 1, 
                                  kr = False, 
                                  kcp = False, 
                                  kep = True,  
                                  kt = False,
                                  d = 3)
                
                
                self.surface = cmds.rename(self.surface, name)
                
                cmds.parent(self.surface, self.setup_group)
                
        
        if self.use_ribbon:
            if not self.surface:
                surface = transforms_to_nurb_surface(self.buffer_joints, self._get_name(self.description), spans = -1, offset_axis = self.ribbon_offset_axis, offset_amount = self.ribbon_offset)
                cmds.rebuildSurface(surface, ch = True, rpo = True, rt =  False,  end = True, kr = 0, kcp = 0, kc = 0, su = 1, du = 1, sv = self.control_count-1, dv = 3, fr = 0, dir = True)
        
                self.surface = surface
                
                cmds.parent(self.surface, self.setup_group)
    
    def _cluster(self, description):
        
        
        cluster_curve = ClusterSurface(self.surface, self._get_name(description))
        cluster_curve.set_join_ends(True)
        cluster_curve.set_join_both_ends(self.join_both_ends)
        cluster_curve.create()
        
        self.cluster_deformers = cluster_curve.clusters
        
        return cluster_curve.get_cluster_handle_list()
        
    def set_control_count(self, int_value):
        
        self.control_count = int_value
        
    def set_use_ribbon(self, bool_value):
        self.use_ribbon = bool_value
        
    def set_ribbon_offset(self, float_value):
        self.ribbon_offset = float_value
       
    def set_ribbon_offset_axis(self, axis_letter):
        self.ribbon_offset_axis = axis_letter
        
    def set_orient_controls_to_joints(self, bool_value):
        self.orient_controls_to_joints = bool_value
        
    def set_join_both_ends(self, bool_value):
        self.join_both_ends = bool_value
        
    def create(self):
        super(TweakCurveRig, self).create()
        
        self._create_ik_guide()
        
        clusters = self._cluster(self.description)
        
        cmds.parent(clusters, self.setup_group)
        
        for cluster in clusters:
            control = self._create_control()
            
            xform = create_xform_group(control)
            create_xform_group(control, 'driver')
            
            MatchSpace(cluster, xform).translation_to_rotate_pivot()
            
            if self.orient_controls_to_joints:
            
                if not self.orient_joint:
                    joint = get_closest_transform(cluster, self.buffer_joints)            
                    
                if self.orient_joint:
                    joint = self.orient_joint
                
                MatchSpace(joint, xform).translation_rotation()
            
            cmds.parentConstraint(control, cluster, mo = True)
            
            cmds.parent(xform, self.control_group)
        
        if has_shape_of_type(self.surface, 'nurbsCurve'):
            self.maya_type = 'nurbsCurve'
        if has_shape_of_type(self.surface, 'nurbsSurface'):
            self.maya_type = 'nurbsSurface'
            
        if self.attach_joints:
            for joint in self.buffer_joints:
                if self.maya_type == 'nurbsSurface':
                    rivet = attach_to_surface(joint, self.surface)
                    cmds.parent(rivet, self.setup_group)
                if self.maya_type == 'nurbsCurve':
                    attach_to_curve(joint, self.surface)
            
             
            
            
        
        
    
        

#---Body Rig



class IkLegRig(IkAppendageRig):
    
    def _fix_right_side_orient(self, control):
        return
    
    def _create_pole_vector(self):
        
        
        
        control = self._create_control('POLE')
        control.hide_scale_and_visibility_attributes()
        control.set_curve_type('cube')
        self.poleControl = control.get()
        
        pole_var = MayaEnumVariable('POLE_VECTOR')
        pole_var.create(self.btm_control)
        
        pole_vis = MayaNumberVariable('poleVisibility')
        pole_vis.set_variable_type(pole_vis.TYPE_BOOL)
        pole_vis.create(self.btm_control)
        
        twist_var = MayaNumberVariable('twist')
        twist_var.create(self.btm_control)
        

        
        if self.side == 'L':
            twist_var.connect_out('%s.twist' % self.ik_handle)
            
        if self.side == 'R':
            connect_multiply('%s.twist' % self.btm_control, '%s.twist' % self.ik_handle, -1)
            #connect_reverse('%s.twist' % self.btm_control, '%s.twist' % self.ik_handle)
            
        pole_joints = self._get_pole_joints()
        
        position = get_polevector( pole_joints[0], pole_joints[1], pole_joints[2], self.pole_offset )
        cmds.move(position[0], position[1], position[2], control.get())

        match = MatchSpace(self.btm_control, control.get())
        match.rotation()
        
        cmds.poleVectorConstraint(control.get(), self.ik_handle)
        
        xform_group = create_xform_group( control.get() )
        
        if self.create_twist:
            
            follow_group = create_follow_group(self.top_control, xform_group)
            constraint = cmds.parentConstraint(self.twist_guide, follow_group, mo = True)[0]
            
            constraint_editor = ConstraintEditor()
            constraint_editor.create_switch(self.btm_control, 'autoTwist', constraint)
            cmds.setAttr('%s.autoTwist' % self.btm_control, 1)
            
            twist_offset = MayaNumberVariable('autoTwistOffset')
            twist_offset.create(self.btm_control)
            
            if self.side == 'L':
                twist_offset.connect_out('%s.rotateY' % self.offset_pole_locator)
            if self.side == 'R':
                connect_multiply('%s.autoTwistOffset' % self.btm_control, 
                                '%s.rotateY' % self.offset_pole_locator, -1)
        
        if not self.create_twist:
            follow_group = create_follow_group(self.top_control, xform_group)
        
        cmds.parent(follow_group,  self.control_group )
        
        name = self._get_name()
        
        rig_line = RiggedLine(pole_joints[1], control.get(), name).create()
        cmds.parent(rig_line, self.control_group)
        
        pole_vis.connect_out('%s.visibility' % xform_group)
        pole_vis.connect_out('%s.visibility' % rig_line) 
    
class IkQuadrupedBackLegRig(IkAppendageRig):
    
    def __init__(self, description, side):
        super(IkQuadrupedBackLegRig, self).__init__(description, side)
        
        self.offset_control_to_locator = False
    
    def _duplicate_joints(self):
        
        super(IkAppendageRig, self)._duplicate_joints()
        
        duplicate = DuplicateHierarchy(self.joints[0])
        duplicate.stop_at(self.joints[-1])
        duplicate.replace('joint', 'ik')
        self.ik_chain = duplicate.create()
        
        ik_group = self._create_group()
        
        cmds.parent(self.ik_chain[0], ik_group)
        cmds.parent(ik_group, self.setup_group)
        
        self._create_offset_chain(ik_group)
        
        for inc in range(0, len(self.offset_chain)):
            
            cmds.parentConstraint(self.offset_chain[inc], self.buffer_joints[inc], mo = True)
            connect_scale(self.offset_chain[inc], self.buffer_joints[inc])
            
            cmds.connectAttr('%s.scaleX' % self.ik_chain[inc], 
                             '%s.scaleX' % self.offset_chain[inc])
        
        cmds.parentConstraint(self.ik_chain[-1], self.buffer_joints[-1], mo = True)
        connect_scale(self.offset_chain[-1], self.buffer_joints[-1])
        
        cmds.parentConstraint(self.ik_chain[0], self.offset_chain[0], mo = True)
    
    def _create_offset_chain(self, parent = None):
        
        if not parent:
            parent = self.setup_group
        
        duplicate = DuplicateHierarchy(self.joints[0])
        duplicate.stop_at(self.joints[-1])
        duplicate.replace('joint', 'offset')        
        self.offset_chain = duplicate.create()
        
        cmds.parent(self.offset_chain[0], parent)
        
        duplicate = DuplicateHierarchy(self.offset_chain[-2])
        duplicate.replace('offset', 'sway')
        self.lower_offset_chain = duplicate.create()
        
        cmds.parent(self.lower_offset_chain[1], self.offset_chain[-2])
        cmds.parent(self.lower_offset_chain[0], self.lower_offset_chain[1])
        cmds.makeIdentity(self.lower_offset_chain, apply = True, t = 1, r = 1, s = 1, n = 0, jointOrient = True)
        cmds.parent(self.lower_offset_chain[1], self.setup_group)
        self.lower_offset_chain.reverse()
        
        cmds.connectAttr('%s.scaleX' % self.offset_chain[-2], '%s.scaleX' % self.lower_offset_chain[0])
        
        cmds.delete(self.offset_chain[-1])
        self.offset_chain.pop(-1)
        
        cmds.orientConstraint(self.lower_offset_chain[0], self.offset_chain[-1])
        
    def _create_offset_control(self):
        
        
        if not self.offset_control_to_locator:
            control = self._create_control(description = 'offset')
            control.hide_scale_and_visibility_attributes()
            control.scale_shape(2, 2, 2)
            control.set_curve_type('square')
            
            self.offset_control = control.get()
            
            match = MatchSpace(self.lower_offset_chain[1], self.offset_control)
            match.rotation()

            match = MatchSpace(self.lower_offset_chain[0], self.offset_control)
            match.translation()
        
        if self.offset_control_to_locator:
            self.offset_control = cmds.spaceLocator(n = 'locator_%s' % self._get_name('offset'))[0]
            
            match = MatchSpace(self.lower_offset_chain[0], self.offset_control)
            match.translation()
            cmds.hide(self.offset_control)
        
        cmds.parentConstraint(self.offset_control, self.lower_offset_chain[0], mo = True)

        xform_group = create_xform_group(self.offset_control)
        driver_group = create_xform_group(self.offset_control, 'driver')
        
        title = MayaEnumVariable('OFFSET_ANKLE')
        title.create(self.btm_control)
        
        offset = MayaNumberVariable('offsetAnkle')
        
        offset.create(self.btm_control)
        offset.connect_out('%s.rotateZ' % driver_group)
        
        follow_group = create_follow_group(self.ik_chain[-2], xform_group)
        
        scale_constraint = cmds.scaleConstraint(self.ik_chain[-2], follow_group)[0]
        self._unhook_scale_constraint(scale_constraint)
        
        cmds.parent(follow_group, self.top_control)
        
        if not self.offset_control_to_locator:
            control.hide_translate_attributes()
        
        return self.offset_control
    
    def _rig_offset_chain(self):
        
        ik_handle = IkHandle( self._get_name('offset_top') )
        
        ik_handle.set_start_joint( self.offset_chain[0] )
        ik_handle.set_end_joint( self.offset_chain[-1] )
        ik_handle.set_solver(ik_handle.solver_rp)
        ik_handle = ik_handle.create()

        cmds.parent(ik_handle, self.lower_offset_chain[-1])

        ik_handle_btm = IkHandle( self._get_name('offset_btm'))
        ik_handle_btm.set_start_joint(self.lower_offset_chain[0])
        ik_handle_btm.set_end_joint(self.lower_offset_chain[-1])
        ik_handle_btm.set_solver(ik_handle_btm.solver_sc)
        ik_handle_btm = ik_handle_btm.create()
        
        follow = create_follow_group( self.offset_control, ik_handle_btm)
        cmds.parent(follow, self.setup_group)
        cmds.hide(ik_handle_btm)
    
    def set_offset_control_to_locator(self, bool_value):
        self.offset_control_to_locator = bool_value
    
    def create(self):
        
        super(IkQuadrupedBackLegRig, self).create()
        
        self._create_offset_control()
        
        self._rig_offset_chain()
        
        cmds.setAttr('%s.translateY' % self.pole_vector_xform, 0)
        

class FkQuadrupedSpineRig(FkCurveRig):
    def __init__(self, name, side):
        super(FkQuadrupedSpineRig, self).__init__(name, side)
        
        self.mid_control_joint = None
        
    
    def _create_sub_control(self):
        
        sub_control = Control( self._get_control_name(sub = True) )
        sub_control.color( get_color_of_side( self.side , True)  )
        if self.control_shape:
            sub_control.set_curve_type(self.control_shape)
        
        sub_control.scale_shape(.75, .75, .75)
        
        if self.current_increment == 0:
            sub_control.set_curve_type('cube')
        
        if self.current_increment == 1:
            other_sub_control = Control( self._get_control_name('reverse', sub = True))
            other_sub_control.color( get_color_of_side( self.side, True ) )
        
            if self.control_shape:
                other_sub_control.set_curve_type(self.control_shape)
            
            other_sub_control.scale_shape(2, 2, 2)
            
            control = self.controls[-1].get()
            other_sub = other_sub_control.get()
            
            if self.mid_control_joint:
                MatchSpace(self.mid_control_joint, other_sub).translation()
                MatchSpace(control, other_sub).rotation()
            
            if not self.mid_control_joint:
                MatchSpace(control, other_sub).translation_rotation()
            
            #cmds.parent(other_sub,  )
            
            xform = create_xform_group(other_sub_control.get())
                
            cmds.parent(xform, self.controls[-2].get())
            parent = cmds.listRelatives(self.sub_controls[-1], p = True)[0]
            xform = cmds.listRelatives(parent, p = True)[0]
            
            other_sub_control.hide_scale_and_visibility_attributes()
            
            cmds.parent(xform, other_sub)
        
        
        if self.current_increment == 2:
            pass
        
        return sub_control
    
    def set_mid_control_joint(self, joint_name):
        self.mid_control_joint = joint_name
    

class IkQuadrupedScapula(BufferRig):
    
    def __init__(self, description, side):
        super(IkQuadrupedScapula, self).__init__(description, side)
        
        self.control_offset = 10
    
    def _create_top_control(self):
        control = self._create_control()
        control.set_curve_type('cube')
        control.hide_scale_and_visibility_attributes()
        
        self._offset_control(control)
        
        cmds.parent(control.get(), self.control_group)
        
        create_xform_group(control.get())
        
        return control.get()
    
    
    
    def _create_shoulder_control(self):
        control = self._create_control()
        control.set_curve_type('cube')
        control.hide_scale_and_visibility_attributes()
        
        cmds.parent(control.get(), self.control_group)
        
        MatchSpace(self.joints[0], control.get()).translation()
        cmds.pointConstraint(control.get(), self.joints[0], mo = True)
        
        create_xform_group(control.get())
        
        return control.get()
    
    def _offset_control(self, control ):
        
        offset = cmds.group(em = True)
        match = MatchSpace(self.joints[-1], offset)
        match.translation_rotation()
        
        cmds.move(self.control_offset, 0,0 , offset, os = True, wd = True, r = True)
        
        match = MatchSpace(offset, control.get())
        match.translation()
        
        cmds.delete(offset)
    
    def _create_ik(self, control):
        
        handle = IkHandle(self._get_name())
        handle.set_start_joint(self.joints[0])
        handle.set_end_joint(self.joints[-1])
        handle = handle.create()
        
        cmds.pointConstraint(control, handle)
        
        cmds.parent(handle, control)
        cmds.hide(handle)
        
    
    def set_control_offset(self, value):
        self.control_offset = value
    
    def create(self):
        
        control = self._create_top_control()
        self._create_shoulder_control()
        
        self._create_ik(control)
        
        rig_line = RiggedLine(control, self.joints[-1], self._get_name()).create()
        cmds.parent(rig_line, self.control_group) 
    
class RollRig(JointRig):
    
    def __init__(self, description, side):
        super(RollRig, self).__init__(description, side)
        
        self.create_roll_controls = True
        self.attribute_control = None
        
        self.ik_chain = []
        self.fk_chain = []
        
        self.add_hik = None
        
        self.ik_attribute = 'ikFk'
        self.control_shape = 'circle'
        
        self.forward_roll_axis = 'X'
        self.side_roll_axis = 'Z'
        self.top_roll_axis = 'Y'
        
    def duplicate_joints(self):
        
        duplicate = DuplicateHierarchy(self.joints[0])
        duplicate.only_these(self.joints)
        joints = duplicate.create()
        
        cmds.parent(joints[0], self.setup_group)
        
        return joints
    
    def _get_attribute_control(self):
        if not self.attribute_control:
            return self.roll_control.get()
            
        if self.attribute_control:
            return self.attribute_control        
    
    def _create_pivot_group(self, source_transform, description):
        
        name = self._get_name('pivot', description)
        
        group = cmds.group(em = True, n = name)
        
        match = MatchSpace(source_transform, group)
        match.translation()
        
        xform_group = create_xform_group(group)
        
        attribute_control = self._get_attribute_control()
        
        cmds.addAttr(attribute_control, ln = '%sPivot' % description, at = 'double', k = True)
        cmds.connectAttr('%s.%sPivot' % (attribute_control, description), '%s.rotateY' % group)
        
        return group, xform_group
    
    def _create_pivot_control(self, source_transform, description, sub = False, no_control = False, scale = 1):
        
        
        if self.create_roll_controls:
            control = self._create_control(description, sub)
            
            control_object = control
            control.set_curve_type(self.control_shape)
            control.scale_shape(scale, scale, scale)
            control = control.get()
        
        if not self.create_roll_controls or no_control:
            name = self._get_name('ctrl', description)
            control = cmds.group(em = True, n = inc_name(name))
        
        xform_group = create_xform_group(control)
        driver_group = create_xform_group(control, 'driver')
        
        match = MatchSpace(source_transform, xform_group)
        match.translation_rotation()
        
        if self.create_roll_controls:
            
            control_object.hide_scale_attributes()
            control_object.hide_translate_attributes()
            control_object.hide_visibility_attribute()
            
        if self.create_roll_controls:
            cmds.connectAttr('%s.controlVisibility' % self._get_attribute_control(), '%sShape.visibility' % control)
        
        return control, xform_group, driver_group
    
    def _create_roll_control(self, transform):
        
        roll_control = self._create_control('roll') 
        roll_control.set_curve_type('square')
        
        self.roll_control = roll_control
        
        roll_control.scale_shape(.8,.8,.8)
        
        xform_group = create_xform_group(roll_control.get())
        
        roll_control.hide_keyable_attributes()
        
        match = MatchSpace( transform, xform_group )
        match.translation_rotation()

        #cmds.parentConstraint(roll_control.get(), transform)
        
        cmds.parent(xform_group, self.control_group)
        
        self.roll_control_xform = xform_group 
        
        return roll_control
    
    def _mix_joints(self, joint_chain1, joint_chain2):
        
        count = len(joint_chain1)
        
        self.ik_chain = []
        
        joints_attach_1 = []
        joints_attach_2 = []
        target_joints = []
        
        for inc in range(0, count):
            
            for inc2 in range(0, count):
                if joint_chain1[inc].startswith(self.joints[inc2]):
                    
                    joints_attach_1.append(joint_chain1[inc])
                    joints_attach_2.append(joint_chain2[inc])
                    target_joints.append(self.joints[inc2])
                    
                    constraint = cmds.parentConstraint(joint_chain1[inc], joint_chain2[inc], self.joints[inc2])[0]
                    
                    constraint_editor = ConstraintEditor()
                    constraint_editor.create_switch(self.roll_control.get(), self.ik_attribute, constraint)
                    
                    self.ik_chain.append(joint_chain1[inc])
                    self.fk_chain.append(joint_chain2[inc])
                    
        AttachJoints(joints_attach_1, target_joints).create()
        AttachJoints(joints_attach_2, target_joints).create()
        
        cmds.connectAttr('%s.%s' % (self.roll_control.get(), self.ik_attribute), '%s.switch' % target_joints[0] )
                    
    def set_create_roll_controls(self, bool_value):
        
        self.create_roll_controls = bool_value
        
    def set_attribute_control(self, control_name):
        self.attribute_control = control_name
    
    def set_control_shape(self, shape_name):
        self.control_shape = shape_name
    
    def set_add_hik(self, bool_value):
        self.add_hik = bool_value
        if bool_value:
            self.ik_attribute = 'ikFkHik'
    
    def set_forward_roll_axis(self, axis_letter):
        self.forward_roll_axis = axis_letter
        
    def set_side_roll_axis(self, axis_letter):
        self.side_roll_axis = axis_letter
        
    def set_top_roll_axis(self, axis_letter):
        self.top_roll_axis = axis_letter
    
    def create(self):
        super(RollRig, self).create()
        
        joint_chain1 = self.duplicate_joints()
        joint_chain2 = self.duplicate_joints()
        
        self._create_roll_control(self.joints[0])
        
        self._mix_joints(joint_chain1, joint_chain2)
        
        
        create_title(self.roll_control.get(), 'IK_FK')
        ik_fk = MayaNumberVariable(self.ik_attribute)
        ik_fk.set_variable_type(ik_fk.TYPE_DOUBLE)
        ik_fk.set_min_value(0)
        ik_fk.set_max_value(1)
        
        if self.add_hik:
            ik_fk.set_max_value(2)
            
        ik_fk.create(self.roll_control.get())
        
        enum_var = MayaEnumVariable('FOOT_PIVOTS')
        enum_var.create(self._get_attribute_control())
        
        if self.create_roll_controls:
            bool_var = MayaNumberVariable('controlVisibility')
            bool_var.set_variable_type(bool_var.TYPE_BOOL)
            bool_var.create(self._get_attribute_control())
        
    
class FootRollRig(RollRig):
    
    def __init__(self, description, side):
        super(FootRollRig, self).__init__(description, side)
        
        self.defined_joints = []
        self.toe_rotate_as_locator = False
        self.mirror_yaw = False
    
    def _define_joints(self):
        self.ankle_index = 0
        self.heel_index = 1
        self.ball_index = 2
        self.toe_index = 3
        self.yawIn_index = 4
        self.yawOut_index = 5
        
        
        self.ankle = self.ik_chain[self.ankle_index]
        self.heel = self.ik_chain[self.heel_index]
        self.ball = self.ik_chain[self.ball_index]
        self.toe = self.ik_chain[self.toe_index]
        self.yawIn = self.ik_chain[self.yawIn_index]
        
        
        self.yawOut = self.ik_chain[self.yawOut_index]

        

    def _create_ik_handle(self, name, start_joint, end_joint):
        
        name = self._get_name(name)
        
        ik_handle = IkHandle(name)
        ik_handle.set_solver(ik_handle.solver_sc)
        ik_handle.set_start_joint(start_joint)
        ik_handle.set_end_joint(end_joint)
        return ik_handle.create()

    def _create_ik(self):
        self.ankle_handle = self._create_ik_handle( 'ankle', self.ankle, self.ball)
        self.ball_handle = self._create_ik_handle( 'ball', self.ball, self.toe)
        
        cmds.parent( self.ankle_handle, self.setup_group )
        cmds.parent( self.ball_handle, self.setup_group )
        
    def _create_toe_rotate_control(self):
        if not self.toe_rotate_as_locator:
            control = self._create_control( 'TOE_ROTATE', True)
            control.hide_translate_attributes()
            control.hide_scale_attributes()
            control.hide_visibility_attribute()
            control.set_curve_type('circle')
            xform_group = control.create_xform()
            control = control.get()
        
        if self.toe_rotate_as_locator:
            control = cmds.spaceLocator(n = self._get_name('locator', 'toe_rotate'))[0]
            xform_group = create_xform_group(control)
            attribute_control = self._get_attribute_control()
            
            cmds.addAttr(attribute_control, ln = 'toeRotate', at = 'double', k = True)  
            cmds.connectAttr('%s.toeRotate' % attribute_control, '%s.rotate%s' % (control, self.forward_roll_axis))  
            
        
        match = MatchSpace(self.ball, xform_group)
        match.translation_rotation()
        
        cmds.parent(xform_group, self.control_group)
        
        return control, xform_group
    
    def _create_toe_fk_rotate_control(self):
        control = self._create_control( 'TOE_FK_ROTATE')
        control.hide_translate_attributes()
        control.hide_scale_attributes()
        control.hide_visibility_attribute()
        
        xform_group = control.create_xform()
        
        match = MatchSpace(self.ball, xform_group)
        match.translation_rotation()
        
        cmds.parent(xform_group, self.control_group)
        
        cmds.parentConstraint(control.get(), self.fk_chain[self.ball_index])
        
        return control, xform_group        
    
    def _create_roll_attributes(self):
        
        attribute_control = self._get_attribute_control()
        
        cmds.addAttr(attribute_control, ln = 'ballRoll', at = 'double', k = True)
        cmds.addAttr(attribute_control, ln = 'toeRoll', at = 'double', k = True)
        cmds.addAttr(attribute_control, ln = 'heelRoll', at = 'double', k = True)
        cmds.addAttr(attribute_control, ln = 'yawRoll', at = 'double', k = True)
    
    def _create_yawout_roll(self, parent):
        
        control, xform, driver = self._create_pivot_control(self.yawOut, 'yawOut')

        cmds.parent(xform, parent)
        
        attribute_control = self._get_attribute_control()
        
        final_value = 10
        if self.mirror_yaw and self.side == 'R':
            final_value = -10
            
        final_other_value = -45
        if self.mirror_yaw and self.side == 'R':
            final_other_value = 45
        
        
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.side_roll_axis),cd = '%s.yawRoll' % attribute_control, driverValue = 0, value = 0, itt = 'spline', ott = 'spline')
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.side_roll_axis),cd = '%s.yawRoll' % attribute_control, driverValue = final_value, value = final_other_value, itt = 'spline', ott = 'spline')
        
        
        
        
        if self.mirror_yaw and self.side == 'R':
            cmds.setInfinity('%s.rotate%s' % (driver, self.side_roll_axis), preInfinite = 'linear')
        else:
            cmds.setInfinity('%s.rotate%s' % (driver, self.side_roll_axis), postInfinite = 'linear')
                
        return control
        
    def _create_yawin_roll(self, parent):
        
        control, xform, driver = self._create_pivot_control(self.yawIn, 'yawIn')

        cmds.parent(xform, parent)
        
        attribute_control = self._get_attribute_control()
        
        final_value = -10
        if self.mirror_yaw and self.side == 'R':
            final_value = 10

        final_other_value = 45
        if self.mirror_yaw and self.side == 'R':
            final_other_value = -45
        
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.side_roll_axis),cd = '%s.yawRoll' % attribute_control, driverValue = 0, value = 0, itt = 'spline', ott = 'spline')
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.side_roll_axis),cd = '%s.yawRoll' % attribute_control, driverValue = final_value, value = final_other_value, itt = 'spline', ott = 'spline')
        
            
        
        if self.mirror_yaw and self.side == 'R':
            cmds.setInfinity('%s.rotate%s' % (driver, self.side_roll_axis), postInfinite = 'linear')
        else:
            cmds.setInfinity('%s.rotate%s' % (driver, self.side_roll_axis), preInfinite = 'linear')    
        
                
        return control
    
    def _create_ball_roll(self, parent):
        
        control, xform, driver = self._create_pivot_control(self.ball, 'ball')
        control = Control(control)
        control.scale_shape(2,2,2)
        control = control.get()
        
        cmds.parent(xform, parent)
        
        attribute_control = self._get_attribute_control()
        
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.forward_roll_axis),cd = '%s.ballRoll' % attribute_control, driverValue = 0, value = 0, itt = 'spline', ott = 'spline')        
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.forward_roll_axis),cd = '%s.ballRoll' % attribute_control, driverValue = 10, value = 45, itt = 'spline', ott = 'spline')
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.forward_roll_axis),cd = '%s.ballRoll' % attribute_control, driverValue = -10, value = -45, itt = 'spline', ott = 'spline')
        #cmds.setDrivenKeyframe('%s.rotateX' % driver,cd = '%s.ballRoll' % attribute_control, driverValue = 20, value = 0, itt = 'spline', ott = 'spline')
        cmds.setInfinity('%s.rotate%s' % (driver, self.forward_roll_axis), postInfinite = 'linear')
        cmds.setInfinity('%s.rotate%s' % (driver, self.forward_roll_axis), preInfinite = 'linear')
        
        return control
    
    def _create_toe_roll(self, parent):
        
        control, xform, driver = self._create_pivot_control(self.toe, 'toe')
        
        cmds.parent(xform, parent)
        
        attribute_control = self._get_attribute_control()
        
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.forward_roll_axis),cd = '%s.toeRoll' % attribute_control, driverValue = 0, value = 0, itt = 'spline', ott = 'spline' )
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.forward_roll_axis),cd = '%s.toeRoll' % attribute_control, driverValue = 10, value = 45, itt = 'spline', ott = 'spline')
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.forward_roll_axis),cd = '%s.toeRoll' % attribute_control, driverValue = -10, value = -45, itt = 'spline', ott = 'spline')
        
        cmds.setInfinity('%s.rotate%s' % (driver, self.forward_roll_axis), postInfinite = 'linear')
        cmds.setInfinity('%s.rotate%s' % (driver, self.forward_roll_axis), preInfinite = 'linear')
        
        return control
    
    def _create_heel_roll(self, parent):
        control, xform, driver = self._create_pivot_control(self.heel, 'heel')
        
        cmds.parent(xform, parent)
        
        attribute_control = self._get_attribute_control()
        
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.forward_roll_axis),cd = '%s.heelRoll' % attribute_control, driverValue = 0, value = 0, itt = 'spline', ott = 'spline')
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.forward_roll_axis),cd = '%s.heelRoll' % attribute_control, driverValue = -10, value = -45, itt = 'spline', ott = 'spline')
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.forward_roll_axis),cd = '%s.heelRoll' % attribute_control, driverValue = 10, value = 45, itt = 'spline', ott = 'spline')
        cmds.setInfinity('%s.rotate%s' % (driver, self.forward_roll_axis), preInfinite = 'linear')
        cmds.setInfinity('%s.rotate%s' % (driver, self.forward_roll_axis), postInfinite = 'linear')
        
        return control
    
    def _create_pivot(self, name, transform, parent):
        
        pivot_group, pivot_xform = self._create_pivot_group(transform, name)
        cmds.parent(pivot_xform, parent)
        
        return pivot_group
        
    def _create_pivot_groups(self):

        toe_control, toe_control_xform = self._create_toe_rotate_control()
        toe_fk_control, toe_fk_control_xform = self._create_toe_fk_rotate_control()
        
        ball_pivot = self._create_pivot('ball', self.ball, self.control_group)
        toe_pivot = self._create_pivot('toe', self.toe, ball_pivot)
        heel_pivot = self._create_pivot('heel', self.heel, toe_pivot)
        
        toe_roll = self._create_toe_roll(heel_pivot)
        heel_roll = self._create_heel_roll(toe_roll)
        yawout_roll = self._create_yawout_roll(heel_roll)
        yawin_roll = self._create_yawin_roll(yawout_roll)
        ball_roll = self._create_ball_roll(yawin_roll)
        
        self._create_ik()
        
        cmds.parent(toe_control_xform, yawin_roll)
        #cmds.parent(toe_fk_control_xform, self.control_group)
        
        cmds.parentConstraint(ball_roll, self.roll_control_xform, mo = True)
        
        cmds.parentConstraint(toe_control, self.ball_handle, mo = True)
        cmds.parentConstraint(ball_roll, self.ankle_handle, mo = True)
        
        return [ball_pivot, toe_fk_control_xform]
        
    def set_toe_rotate_as_locator(self, bool_value):
        self.toe_rotate_as_locator = bool_value
          
    def set_mirror_yaw(self, bool_value):
        self.mirror_yaw = bool_value
                    
    def create(self):
        super(FootRollRig,self).create()
        
        self._define_joints()
        
        self._create_roll_attributes()
        
        ball_pivot, toe_fk_control_xform = self._create_pivot_groups()
        
        connect_equal_condition('%s.%s' % (self.roll_control.get(), self.ik_attribute), '%s.visibility' % toe_fk_control_xform, 1)
        #cmds.connectAttr('%s.%s' % (self.roll_control.get(), self.ik_attribute), '%s.visibility' % toe_fk_control_xform)
        connect_equal_condition('%s.%s' % (self.roll_control.get(), self.ik_attribute), '%s.visibility' % ball_pivot, 0)
        #connect_reverse('%s.%s' % (self.roll_control.get(), self.ik_attribute), '%s.visibility' % ball_pivot)
        

class QuadFootRollRig(FootRollRig):
    
    def __init__(self, description, side):
        super(QuadFootRollRig, self).__init__(description, side)
        
        self.ball_attrtribute = None
    
    def _define_joints(self):
        
        index_list = self.defined_joints
        
        if not index_list:
            index_list = [0,2,1,3,4,5]
        
        self.ankle_index = index_list[0]
        self.heel_index = index_list[1]
        self.ball_index = index_list[2]
        self.toe_index = index_list[3]
        self.yawIn_index = index_list[4]
        self.yawOut_index = index_list[5]
        
        self.ankle = self.ik_chain[self.ankle_index]
        self.heel = self.ik_chain[self.heel_index]
        self.ball = self.ik_chain[self.ball_index]
        self.toe = self.ik_chain[self.toe_index]
        self.yawIn = self.ik_chain[self.yawIn_index]
        self.yawOut = self.ik_chain[self.yawOut_index]
        
    def _create_roll_attributes(self):
        
        attribute_control = self._get_attribute_control()
        
        cmds.addAttr(attribute_control, ln = 'heelRoll', at = 'double', k = True)
        cmds.addAttr(attribute_control, ln = 'ballRoll', at = 'double', k = True)
        cmds.addAttr(attribute_control, ln = 'toeRoll', at = 'double', k = True)
        
        cmds.addAttr(attribute_control, ln = 'yawIn', at = 'double', k = True)
        cmds.addAttr(attribute_control, ln = 'yawOut', at = 'double', k = True)
        
        cmds.addAttr(attribute_control, ln = 'bankIn', at = 'double', k = True)
        cmds.addAttr(attribute_control, ln = 'bankOut', at = 'double', k = True)
        
    def _create_yawout_roll(self, parent, name, scale = 1):
        
        control, xform, driver = self._create_pivot_control(self.yawOut, name, scale = scale)

        cmds.parent(xform, parent)
        
        attribute_control = self._get_attribute_control()
        
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.side_roll_axis),cd = '%s.%s' % (attribute_control, name), driverValue = 0, value = 0, itt = 'spline', ott = 'spline')
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.side_roll_axis),cd = '%s.%s' % (attribute_control, name), driverValue = 10, value = -45, itt = 'spline', ott = 'spline')
        
        cmds.setInfinity('%s.rotate%s' % (driver, self.side_roll_axis), preInfinite = 'linear')
        cmds.setInfinity('%s.rotate%s' % (driver, self.side_roll_axis), postInfinite = 'linear')
                
        return control
        
    def _create_yawin_roll(self, parent, name, scale = 1):
        
        control, xform, driver = self._create_pivot_control(self.yawIn, name, scale = scale)

        cmds.parent(xform, parent)
        
        attribute_control = self._get_attribute_control()
        
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.side_roll_axis),cd = '%s.%s' % (attribute_control, name), driverValue = 0, value = 0, itt = 'spline', ott = 'spline')
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.side_roll_axis),cd = '%s.%s' % (attribute_control, name), driverValue = -10, value = -45, itt = 'spline', ott = 'spline')
        
        cmds.setInfinity('%s.rotate%s' % (driver, self.side_roll_axis), preInfinite = 'linear')
        cmds.setInfinity('%s.rotate%s' % (driver, self.side_roll_axis), postInfinite = 'linear')
                
        return control
        
    def _create_pivot_groups(self):

        
        heel_pivot = self._create_pivot('heel', self.heel, self.control_group)
        ball_pivot = self._create_pivot('ball', self.ball, heel_pivot)
        toe_pivot = self._create_pivot('toe', self.toe, ball_pivot)
        
        toe_roll = self._create_toe_roll(toe_pivot)
        heel_roll = self._create_heel_roll(toe_roll)
        yawin_roll = self._create_yawin_roll(heel_roll, 'yawIn')
        yawout_roll = self._create_yawout_roll(yawin_roll, 'yawOut')
        bankin_roll = self._create_yawin_roll(yawout_roll, 'bankIn')
        bankout_roll = self._create_yawout_roll(bankin_roll, 'bankOut')
        ball_roll = self._create_ball_roll(bankout_roll)
        
        toe_control, toe_control_xform = self._create_toe_rotate_control()
        toe_fk_control, toe_fk_control_xform = self._create_toe_fk_rotate_control()
        
        self._create_ik()
        
        cmds.parent(toe_control_xform, bankout_roll)
        
        follow_toe_control = cmds.group(em = True, n = 'follow_%s' % toe_control)
        MatchSpace(toe_control, follow_toe_control).translation_rotation()
        xform_follow = create_xform_group(follow_toe_control)
        
        cmds.parent(xform_follow, yawout_roll)
        connect_rotate(toe_control, follow_toe_control)
        
        cmds.parentConstraint(ball_roll, self.roll_control_xform, mo = True)
        
        cmds.parentConstraint(toe_control, self.ball_handle, mo = True)
        cmds.parentConstraint(ball_roll, self.ankle_handle, mo = True)
        
        return [ball_pivot, toe_fk_control_xform]
                
    def set_index_order(self,index_list):
        self.defined_joints = index_list  
        

class QuadBackFootRollRig(QuadFootRollRig):
    
    def __init__(self, name, side):
        super(QuadBackFootRollRig, self).__init__(name, side)
        
        self.add_bank = True
    
    def _create_toe_roll(self, parent, name = 'toeRoll', scale = 1):
        
        control, xform, driver = self._create_pivot_control(self.toe, name, scale = scale)
        
        cmds.parent(xform, parent)
        
        attribute_control = self._get_attribute_control()
        
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.forward_roll_axis),cd = '%s.%s' % (attribute_control,name), driverValue = 0, value = 0, itt = 'spline', ott = 'spline' )
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.forward_roll_axis),cd = '%s.%s' % (attribute_control,name), driverValue = 10, value = 45, itt = 'spline', ott = 'spline')
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.forward_roll_axis),cd = '%s.%s' % (attribute_control,name), driverValue = -10, value = -45, itt = 'spline', ott = 'spline')
        
        cmds.setInfinity('%s.rotate%s' % (driver, self.forward_roll_axis), postInfinite = 'linear')
        cmds.setInfinity('%s.rotate%s' % (driver, self.forward_roll_axis), preInfinite = 'linear')
        
        return control
    
    def _create_heel_roll(self, parent, name = 'heelRoll', scale = 1):
        control, xform, driver = self._create_pivot_control(self.heel, name, scale = scale)
        
        cmds.parent(xform, parent)
        
        attribute_control = self._get_attribute_control()
        
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.forward_roll_axis),cd = '%s.%s' % (attribute_control,name), driverValue = 0, value = 0, itt = 'spline', ott = 'spline' )
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.forward_roll_axis),cd = '%s.%s' % (attribute_control,name), driverValue = 10, value = 45, itt = 'spline', ott = 'spline')
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.forward_roll_axis),cd = '%s.%s' % (attribute_control,name), driverValue = -10, value = -45, itt = 'spline', ott = 'spline')
        cmds.setInfinity('%s.rotate%s' % (driver, self.forward_roll_axis), preInfinite = 'linear')
        cmds.setInfinity('%s.rotate%s' % (driver, self.forward_roll_axis), postInfinite = 'linear')
        
        return control
    
    def _create_ball_roll(self, parent):

        control, xform, driver = self._create_pivot_control(self.ball, 'ball')
                
        cmds.parent(xform, parent)
        
        attribute_control = self._get_attribute_control()
        
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.forward_roll_axis),cd = '%s.ballRoll' % attribute_control, driverValue = 0, value = 0, itt = 'spline', ott = 'spline')        
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.forward_roll_axis),cd = '%s.ballRoll' % attribute_control, driverValue = 10, value = 45, itt = 'spline', ott = 'spline')
        cmds.setDrivenKeyframe('%s.rotate%s' % (driver, self.forward_roll_axis),cd = '%s.ballRoll' % attribute_control, driverValue = -10, value = -45, itt = 'spline', ott = 'spline')
        #cmds.setDrivenKeyframe('%s.rotateX' % driver,cd = '%s.ballRoll' % attribute_control, driverValue = 20, value = 0, itt = 'spline', ott = 'spline')
        cmds.setInfinity('%s.rotate%s' % (driver, self.forward_roll_axis), postInfinite = 'linear')
        cmds.setInfinity('%s.rotate%s' % (driver, self.forward_roll_axis), preInfinite = 'linear')
        
        return control
    
    def _create_roll_control(self, transform):
        
        roll_control = self._create_control('roll') 
        roll_control.set_curve_type('square')
        
        self.roll_control = roll_control
        
        roll_control.scale_shape(.8,.8,.8)
        
        xform_group = create_xform_group(roll_control.get())
        
        roll_control.hide_scale_and_visibility_attributes()
        roll_control.hide_rotate_attributes()
        
        
        match = MatchSpace( transform, xform_group )
        match.translation_rotation()

        #cmds.parentConstraint(roll_control.get(), transform)
        
        cmds.parent(xform_group, self.control_group)
        
        self.roll_control_xform = xform_group 
        
        return roll_control
    
    def _define_joints(self):
        
        index_list = self.defined_joints
        
        if not index_list:
            index_list = [0,1,2,3,4,5]
        
        self.ankle_index = index_list[0]
        self.heel_index = index_list[1]
        self.ball_index = index_list[2]
        self.toe_index = index_list[3]
        self.yawIn_index = index_list[4]
        self.yawOut_index = index_list[5]
        
        self.ankle = self.ik_chain[self.ankle_index]
        self.heel = self.ik_chain[self.heel_index]
        self.ball = self.ik_chain[self.ball_index]
        self.toe = self.ik_chain[self.toe_index]
        self.yawIn = self.ik_chain[self.yawIn_index]
        self.yawOut = self.ik_chain[self.yawOut_index]
    
    def _create_roll_attributes(self):
        
        attribute_control = self._get_attribute_control()
        
        create_title(attribute_control, 'roll')
        
        cmds.addAttr(attribute_control, ln = 'ballRoll', at = 'double', k = True)
        cmds.addAttr(attribute_control, ln = 'toeRoll', at = 'double', k = True)
        cmds.addAttr(attribute_control, ln = 'heelRoll', at = 'double', k = True)
        
        cmds.addAttr(attribute_control, ln = 'yawIn', at = 'double', k = True)
        cmds.addAttr(attribute_control, ln = 'yawOut', at = 'double', k = True)
        
        if self.add_bank:
            
            create_title(attribute_control, 'bank')
            
            cmds.addAttr(attribute_control, ln = 'bankIn', at = 'double', k = True)
            cmds.addAttr(attribute_control, ln = 'bankOut', at = 'double', k = True)
        
            cmds.addAttr(attribute_control, ln = 'bankForward', at = 'double', k = True)
            cmds.addAttr(attribute_control, ln = 'bankBack', at = 'double', k = True)
    
    def _create_ik(self):
        self.ankle_handle = self._create_ik_handle( 'ankle', self.ankle, self.toe)
        cmds.parent( self.ankle_handle, self.setup_group )
    
    def _create_pivot_groups(self):

        attribute_control = self._get_attribute_control()

        self._create_ik() 
        
        create_title(attribute_control, 'pivot')
        
        ankle_pivot = self._create_pivot('ankle', self.ankle, self.control_group)
        heel_pivot = self._create_pivot('heel', self.heel, ankle_pivot)
        ball_pivot = self._create_pivot('ball', self.ball, heel_pivot)
        toe_pivot = self._create_pivot('toe', self.toe, ball_pivot)
        
        
        toe_roll = self._create_toe_roll(toe_pivot)
        heel_roll = self._create_heel_roll(toe_roll)
        yawin_roll = self._create_yawin_roll(heel_roll, 'yawIn')
        yawout_roll = self._create_yawout_roll(yawin_roll, 'yawOut')
        ball_roll = self._create_ball_roll(yawout_roll)
        
        if self.add_bank:
            
            bankin_roll = self._create_yawin_roll(ball_roll, 'bankIn', scale = .5)
            bankout_roll = self._create_yawout_roll(bankin_roll, 'bankOut', scale = .5)
            bankforward_roll = self._create_toe_roll(bankout_roll, 'bankForward', scale = .5)
            bankback_roll = self._create_heel_roll(bankforward_roll, 'bankBack', scale = .5)
        
            cmds.parentConstraint(bankback_roll, self.roll_control_xform, mo = True)
            cmds.parentConstraint(bankback_roll, self.ankle_handle, mo = True)
        
        if not self.add_bank:
        
            cmds.parentConstraint(ball_roll, self.roll_control_xform, mo = True)
            cmds.parentConstraint(ball_roll, self.ankle_handle, mo = True)
                    
    def set_add_bank(self, bool_value):
        self.add_bank = bool_value
                    
    def create(self):
        super(FootRollRig,self).create()
        
        self._define_joints()
        
        self._create_roll_attributes()
        
        self._create_pivot_groups()
        
        
#---Face Rig

class FaceFollowCurveRig(CurveRig):
    def __init__(self, description, side):
        super(FaceFollowCurveRig, self).__init__(description, side)
        
        self.controls = []
        self.drivers = []
        self.clusters = []
        self.local_controls = []
        
        self.wire_falloff = 20
        
        self.create_joints = 0
        
        self.mesh = None
        self.create_follow = False

    def _rebuild_curve(self, curve, description = None, spans = 4, delete_cvs = False):
        
        if self.create_follow:
            
            follow_curve, cluster_curve = self._rebuild_with_follow(curve, description, spans, delete_cvs)
            
            return follow_curve, cluster_curve
                
        rebuilt_curve = cmds.rebuildCurve( curve, 
                                                 constructionHistory = False,
                                                 replaceOriginal = False,
                                                 rebuildType = 0,
                                                 endKnots = 1,
                                                 keepRange = 0,
                                                 keepControlPoints = 0, 
                                                 keepEndPoints = 1, 
                                                 keepTangents = 0, 
                                                 spans = spans,
                                                 degree = 3 )[0]
        
        if delete_cvs:
            cvs = cmds.ls('%s.cv[*]' % rebuilt_curve, flatten = True)
            cmds.delete(cvs[1], cvs[-2])
        
        new_curve = cmds.rename(rebuilt_curve, 'curve_%s' % self._get_name(description))
        
        
        cluster_curve = new_curve
        follow_curve = None
        
        cmds.parent(cluster_curve, self.setup_group)
        
        return follow_curve, cluster_curve
        
    def _rebuild_with_follow(self, curve, description, spans, delete_cvs):
        rebuilt_curve, node = cmds.rebuildCurve( curve, 
                                           constructionHistory = True,
                                           replaceOriginal = False,
                                           rebuildType = 0,
                                           endKnots = 1,
                                           keepRange = 0,
                                           keepControlPoints = 0, 
                                           keepEndPoints = 1, 
                                           keepTangents = 0, 
                                           spans = spans,
                                           degree =3)
        
        #cmds.delete('%s.cv[1]' % rebuilt_curve)
        
        if delete_cvs:
            cvs = cmds.ls('%s.cv[*]' % rebuilt_curve, flatten = True)
            cmds.delete(cvs[1], cvs[-2])
        
        new_curve = cmds.duplicate(rebuilt_curve, n = 'curve_%s' % self._get_name(description))[0]
        
        cmds.blendShape(rebuilt_curve, new_curve, w = [0,1])
        
        follow_curve = rebuilt_curve
        cluster_curve = new_curve
        
        cmds.parent(follow_curve, self.setup_group)
        cmds.parent(cluster_curve, self.setup_group)
        
        return follow_curve, cluster_curve

    def _create_inc_control(self, follow_curve, cluster_curve, inc, description = None, center_tolerance = 0.001):
        control = self._create_control(description)
        
        control.rotate_shape(90, 0, 0)
        control.hide_scale_attributes()
        
        cluster, handle = create_cluster('%s.cv[%s]' % (cluster_curve, inc), self._get_name())
        self.clusters.append(handle)
        
        match = MatchSpace(handle, control.get())
        match.translation_to_rotate_pivot()
        
        control_name = control.get()
        

        if description:
        
            side = control.color_respect_side(center_tolerance = center_tolerance)
            
            if side != 'C':
                control_name = cmds.rename(control.get(), inc_name(control.get()[0:-1] + side))
        
        xform = create_xform_group(control_name)
        driver = create_xform_group(control_name, 'driver')
        
        bind_pre = create_cluster_bindpre(cluster, handle)
        
        local_group, xform_group = constrain_local(control_name, handle, parent = True)
        
        local_driver = create_xform_group(local_group, 'driver')
        connect_translate(driver, local_driver)
        connect_translate(xform, xform_group)
        
        cmds.parent(bind_pre, xform_group)
        
        attach_to_curve(xform, follow_curve)
        
        cmds.parent(xform, self.control_group)
        cmds.parent(xform_group, self.setup_group)
        
        self.local_controls.append(local_group)
        self.drivers.append(driver)
        
        return control_name, driver

    def _create_controls(self, follow_curve, cluster_curve, description):
        pass

    def _create_deformation(self, deform_curve, follow_curve):
        
        
        if self.mesh:
            if not self.create_joints:
                for mesh in self.mesh:
                    wire, curve = cmds.wire( self.mesh, w = deform_curve, dds=[(0, self.wire_falloff)], gw = False, n = 'wire_%s' % deform_curve)
        
                    cmds.setAttr('%s.rotation' % wire, 0.1)
        
                cmds.blendShape(follow_curve, '%sBaseWire' % curve, w = [0,1])
                
            if self.create_joints:
                create_joints_on_curve(deform_curve, self.create_joints, self.description, create_controls = False)
                
    def set_wire_falloff(self, value):
        self.wire_falloff = value

    def set_mesh_to_deform(self, mesh):
        self.mesh = mesh
        
        if type(mesh) == type('') or type(mesh) == type(u''):
            self.mesh = [mesh]
            
    def set_create_joints(self, int_value):
        self.create_joints = int_value

    def set_curves(self, top_lip_curve, btm_lip_curve):
        super(MouthCurveRig, self).set_curves([top_lip_curve, btm_lip_curve])
        
    def set_create_follow(self, bool_value):
        self.create_follow = bool_value

class SingleControlFaceCurveRig(FaceFollowCurveRig):
    def __init__(self, description, side):
        super(SingleControlFaceCurveRig, self).__init__(description, side)
        
        self.attach_surface = None
        self.curve_position_percent = 0
        self.shape_name = 'pin'

    def _rebuild_curve(self, curve, description = None, spans = 6):
        
        rebuilt_curve, node = cmds.rebuildCurve( curve, 
                                           constructionHistory = True,
                                           replaceOriginal = False,
                                           rebuildType = 0,
                                           endKnots = 1,
                                           keepRange = 0,
                                           keepControlPoints = 0, 
                                           keepEndPoints = 1, 
                                           keepTangents = 0, 
                                           spans = spans,
                                           degree =3)
        
        new_curve = cmds.duplicate(rebuilt_curve, n = 'curve_%s' % self._get_name(description))[0]
        
        cmds.blendShape(rebuilt_curve, new_curve, w = [0,1])
        
        follow_curve = rebuilt_curve
        cluster_curve = new_curve
        
        cmds.parent(follow_curve, self.setup_group)
        cmds.parent(cluster_curve, self.setup_group)
        
        return follow_curve, cluster_curve        
    
    def _create_control_on_curve(self, follow_curve, percent, sub = False, description = None):
        
        position = cmds.pointOnCurve(follow_curve, top = True, pr = percent)
        
        control = self._create_control(description)
        control.set_curve_type(self.shape_name)
        control.rotate_shape(90, 0, 0)
        control.hide_scale_attributes()
        
        sub_control = None
        
        if sub:
            sub_control = self._create_control(description, True)
            sub_control.set_curve_type('cube')
            sub_control.scale_shape(.8, .8, .8)
            sub_control.hide_scale_attributes()
            
            cmds.parent(sub_control.get(), control.get())
            
            sub_control = sub_control.get()
        
        cmds.move(position[0], position[1], position[2], control.get())
        
        control_name = control.get()
        cmds.parent(control_name, self.control_group)
        
        xform = create_xform_group(control_name)
        driver = create_xform_group(control_name, 'driver')
        
        attach_to_curve(xform, follow_curve)
        
        return control_name, sub_control, driver, xform
    
    def _create_full_control(self, follow_curve, cluster, description = None):
        position = cmds.xform(cluster, q = True, ws = True, rp= True)
        
        control = self._create_control(description)
        control.set_curve_type(self.shape_name)
        control.rotate_shape(90, 0, 0)
        control.hide_scale_attributes()        
    
        cmds.move(position[0], position[1], position[2], control.get())
        
        control_name = control.get()
        cmds.parent(control_name, self.control_group)
        
        xform = create_xform_group(control_name)
        driver = create_xform_group(control_name, 'driver')
        
        attach_to_curve(xform, follow_curve)
        
        return control_name, driver        
    
    def _create_cluster(self, cv_deform, cv_offset, description = None, follow = True):
        
        cluster_group = cmds.group(em = True, n = inc_name(self._get_name(description)))
        cmds.parent(cluster_group, self.setup_group)
        
        cluster, handle = create_cluster(cv_deform, self._get_name(description))
        self.clusters.append(handle)
        
        bind_pre = create_cluster_bindpre(cluster, handle)
        
        #buffer = cmds.group(em = True, n = inc_name('buffer_%s' % handle))
        
        match = MatchSpace(handle, buffer)
        match.translation_to_rotate_pivot()
        
        cmds.parent(handle, buffer)
        cmds.parent(buffer, cluster_group)
        
        xform = create_xform_group(buffer)
        driver3 = create_xform_group(buffer, 'driver3')
        driver2 = create_xform_group(buffer, 'driver2')
        driver1 = create_xform_group(buffer, 'driver1')
        
        if self.attach_surface and follow:
            
            surface_follow = cmds.group(em = True, n = inc_name('surfaceFollow_%s' % handle))
            
            cmds.parent(surface_follow, xform)
        
            match = MatchSpace(handle, surface_follow)
            match.translation_to_rotate_pivot()
            
            cmds.pointConstraint(driver3, surface_follow, mo = True)
            cmds.geometryConstraint(self.attach_surface, surface_follow)
            
            connect_translate(driver3, surface_follow)
            
            cmds.pointConstraint(surface_follow, driver2, mo = True)
        
        cmds.parent(bind_pre, xform)
        
        return xform, driver3, driver1
        
    def _create_full_cluster(self, follow_curve, cluster_curve, offset_curve, description= None, follow = False):
        
        cv_deform = '%s.cv[*]' % (cluster_curve)
        cv_offset = '%s.cv[*]' % (offset_curve)
        
        xform, driver, local_driver = self._create_cluster(cv_deform, cv_offset, description, follow)
        
        
        
        return driver, local_driver, xform
        
        
    def _create_inc_cluster(self, follow_curve, cluster_curve, offset_curve, inc, description = None, follow = True):
        
        cv_deform = '%s.cv[%s]' % (cluster_curve, inc)
        cv_offset = '%s.cv[%s]' % (offset_curve, inc)
        
        xform, driver, local_driver = self._create_cluster(cv_deform, cv_offset, description, follow)
            
        return driver, local_driver
    
    def _create_clusters(self, follow_curve, deform_curve, offset_curve, description = None, follow = True):
        
        cvs = cmds.ls('%s.cv[*]' % deform_curve, flatten = True)
        count = len(cvs)
        
        drivers = []
        local_drivers = []
        
        for inc in range(0, count):
            driver, local_driver = self._create_inc_cluster(follow_curve, deform_curve, offset_curve, inc, description, follow)
            drivers.append(driver)
            local_drivers.append(local_driver)
            
        return drivers, local_drivers
    
    def _create_fade(self, start_control, drivers):
        
        reverse_drivers = list(drivers) 
        reverse_drivers.reverse()
        
        multiply_groups = {}
        
        if start_control:
            multiply_groups['side1'] = create_follow_fade(start_control, drivers, -1)
        
        return multiply_groups
    
    def set_attach_surface(self, surface):
        self.attach_surface = surface
        
    def set_curve_position(self, percent):
        self.curve_position_percent = percent

    def set_curve_shape(self, shape_name):
        self.curve_shape = shape_name

    def create(self):
        
        follow_curve, deform_curve = self._rebuild_curve(self.curves[0])
        
        position = self.curve_position_percent
        if position == -1:
            position = .5
        
        start_control, sub, control_driver, xform_control = self._create_control_on_curve(self.curves[0], position)
        
        if self.curve_position_percent > -1:
            drivers, drivers_local = self._create_clusters(self.curves[0],
                                                           deform_curve,
                                                           follow_curve,
                                                           follow = False)
            
            self._create_fade(start_control, drivers)
            
        if self.curve_position_percent == -1:
            driver, driver_local, xform_cluster = self._create_full_cluster(self.curves[0], 
                                                               deform_curve, 
                                                               follow_curve)
            
            connect_translate(start_control, driver)
            connect_rotate(start_control, driver)
            connect_scale(start_control, driver)
            
            
            connect_translate(control_driver, driver)
            connect_rotate(control_driver, driver)
            #connect_scale(control_driver, driver)
            
            connect_translate(xform_control, xform_cluster)
            
            
            control = Control(start_control)
            control.show_scale_attributes()
            
            
            
        
            
        
        self._create_deformation(deform_curve, follow_curve)    

class SimpleFaceCurveRig(FaceFollowCurveRig):
    def __init__(self, description, side):
        super(SimpleFaceCurveRig, self).__init__(description, side)
        
        self.attach_surface = None
    
    def _rebuild_curve(self, curve, description = None, spans = 6):
        
        rebuilt_curve, node = cmds.rebuildCurve( curve, 
                                           constructionHistory = True,
                                           replaceOriginal = False,
                                           rebuildType = 0,
                                           endKnots = 1,
                                           keepRange = 0,
                                           keepControlPoints = 0, 
                                           keepEndPoints = 1, 
                                           keepTangents = 0, 
                                           spans = spans,
                                           degree =3)
        
        new_curve = cmds.duplicate(rebuilt_curve, n = 'curve_%s' % self._get_name(description))[0]
        
        cmds.blendShape(rebuilt_curve, new_curve, w = [0,1])
        
        follow_curve = rebuilt_curve
        cluster_curve = new_curve
        
        cmds.parent(follow_curve, self.setup_group)
        cmds.parent(cluster_curve, self.setup_group)
        
        return follow_curve, cluster_curve
    
    def _create_control_on_curve(self, follow_curve, percent, sub = True, description = None):
        
        position = cmds.pointOnCurve(follow_curve, top = True, pr = percent)
        
        control = self._create_control(description)
        control.set_curve_type('cube')
        control.hide_scale_attributes()
        
        sub_control = None
        
        if sub:
            sub_control = self._create_control(description, True)
            sub_control.set_curve_type('cube')
            sub_control.scale_shape(.8, .8, .8)
            sub_control.hide_scale_attributes()
            
            cmds.parent(sub_control.get(), control.get())
            
            sub_control = sub_control.get()
        
        cmds.move(position[0], position[1], position[2], control.get())
        
        control_name = control.get()
        cmds.parent(control_name, self.control_group)
        
        xform = create_xform_group(control_name)
        driver = create_xform_group(control_name, 'driver')
        
        attach_to_curve(xform, follow_curve)
        
        return control_name, sub_control, driver
    
    def _create_controls(self, curve, sub = False):
        
        control_dict = {}
        
        start_controls = self._create_control_on_curve(curve, 0, sub = sub)
        start_offset_controls = self._create_control_on_curve(curve, 0.25, sub = sub)
        
        mid_controls = self._create_control_on_curve(curve, 0.5, sub = sub)
        
        end_offset_controls = self._create_control_on_curve(curve,0.75, sub = sub)
        end_controls = self._create_control_on_curve(curve, 1, sub = sub)
        
        control_dict['start'] = start_controls
        control_dict['start_offset'] = start_offset_controls
        
        control_dict['mid'] = mid_controls
        
        control_dict['end_offset'] = end_offset_controls
        control_dict['end'] = end_controls
        
        return control_dict
    
    def _create_cluster(self, cv_deform, cv_offset, description = None, follow = True):
        
        cluster_group = cmds.group(em = True, n = inc_name(self._get_name(description)))
        cmds.parent(cluster_group, self.setup_group)
        
        cluster, handle = create_cluster(cv_deform, self._get_name(description))
        self.clusters.append(handle)
        
        bind_pre = create_cluster_bindpre(cluster, handle)
        
        #buffer = cmds.group(em = True, n = inc_name('buffer_%s' % handle))
        
        match = MatchSpace(handle, buffer)
        match.translation_to_rotate_pivot()
        
        cmds.parent(handle, buffer)
        cmds.parent(buffer, cluster_group)
        
        xform = create_xform_group(buffer)
        driver3 = create_xform_group(buffer, 'driver3')
        driver2 = create_xform_group(buffer, 'driver2')
        driver1 = create_xform_group(buffer, 'driver1')
        
        if self.attach_surface and follow:
            
            surface_follow = cmds.group(em = True, n = inc_name('surfaceFollow_%s' % handle))
            
            cmds.parent(surface_follow, xform)
        
            match = MatchSpace(handle, surface_follow)
            match.translation_to_rotate_pivot()
            
            cmds.pointConstraint(driver3, surface_follow, mo = True)
            cmds.geometryConstraint(self.attach_surface, surface_follow)
            
            connect_translate(driver3, surface_follow)
            
            cmds.pointConstraint(surface_follow, driver2, mo = True)
        
        cmds.parent(bind_pre, xform)
        
        return xform, driver3, driver1
        
    def _create_inc_cluster(self, follow_curve, cluster_curve, offset_curve, inc, description = None, follow = True):
        
        cv_deform = '%s.cv[%s]' % (cluster_curve, inc)
        cv_offset = '%s.cv[%s]' % (offset_curve, inc)
        
        xform, driver, local_driver = self._create_cluster(cv_deform, cv_offset, description, follow)
            
        return driver, local_driver
    
    def _create_clusters(self, follow_curve, deform_curve, offset_curve, description = None, follow = True):
        
        cvs = cmds.ls('%s.cv[*]' % deform_curve, flatten = True)
        count = len(cvs)
        
        drivers = []
        local_drivers = []
        
        for inc in range(0, count):
            driver, local_driver = self._create_inc_cluster(follow_curve, deform_curve, offset_curve, inc, description, follow)
            drivers.append(driver)
            local_drivers.append(local_driver)
            
        return drivers, local_drivers
    
    def _create_fade(self, start_control, mid_control, end_control, start_offset_control, end_offset_control, drivers):
        
        reverse_drivers = list(drivers) 
        reverse_drivers.reverse()
        
        multiply_groups = {}
        
        if start_control:
            multiply_groups['side1'] = create_follow_fade(start_control, drivers, -1)
        if end_control:
            multiply_groups['side2'] = create_follow_fade(end_control, reverse_drivers, -1)
        
        if mid_control:
            multiply_groups['sides'] = create_follow_fade(mid_control, drivers, -1)
            
        if start_offset_control:
            multiply_groups['offset1'] = create_follow_fade(start_offset_control, 
                                                            drivers[0:len(drivers)/2])
        
        if end_offset_control:
            multiply_groups['offset2'] = create_follow_fade(end_offset_control, 
                                                            drivers[len(drivers)/2:])
        
        return multiply_groups
    
    def set_attach_surface(self, surface):
        self.attach_surface = surface
    
    def create(self):
        
        follow_curve, deform_curve = self._rebuild_curve(self.curves[0])
        
        controls = self._create_controls(self.curves[0])
        
        drivers, drivers_local = self._create_clusters(self.curves[0],
                                                       deform_curve,
                                                       follow_curve,
                                                       follow = False)
        
        self._create_fade(controls['start'][0], 
                          controls['mid'][0], 
                          controls['end'][0],
                          controls['start_offset'][0],
                          controls['end_offset'][0],
                          drivers)
        
        self._create_deformation(deform_curve, follow_curve)
        
    
class MouthCurveRig(FaceFollowCurveRig):
    def __init__(self, description):
        super(MouthCurveRig, self).__init__(description, 'C')
        self.center_tolerance = 0.01
        self.control_shape = 'cube'
        self.center_fade = True
        
    def _create_controls(self, follow_curve, cluster_curve, description):
        
        cvs = cmds.ls('%s.cv[*]' % cluster_curve, flatten = True)
        count = len(cvs)
        
        controls = []
        drivers = []
        
        for inc in range(0, count):
        
            control, driver = self._create_inc_control(follow_curve, cluster_curve, inc, description, center_tolerance = self.center_tolerance)
            
            controls.append(control)
            drivers.append(driver)
            
            reverse_inc = (count - inc) -1
            
            if inc != reverse_inc:
                control, driver = self._create_inc_control(follow_curve, cluster_curve,  reverse_inc, description, center_tolerance = self.center_tolerance)
                
                controls.append(control)
                drivers.append(driver)
                
            if inc == reverse_inc:
                break
        
        front_list = drivers[2], drivers[4], drivers[6]
        back_list = drivers[3], drivers[5], drivers[6]
        
        create_follow_fade(controls[0], front_list)
        create_follow_fade(controls[1], back_list)
        
        create_follow_fade(drivers[0], front_list)
        create_follow_fade(drivers[1], back_list)
        
        if self.center_fade:
            create_follow_fade(controls[-1], front_list[:-1])
            create_follow_fade(controls[-1], back_list[:-1])
        
        return controls
        
    def _attach_corners(self, source_control, target_control, local_control, side, local_groups = []):
        
        control = self._create_control('corner', True)
        control.hide_scale_and_visibility_attributes()
        control.set_curve_type(self.control_shape)
        control.hide_rotate_attributes()
        
        control.scale_shape(.8, .8, .8)
        control.rotate_shape(90, 0, 0)
        
        match = MatchSpace(source_control, control.get())
        match.translation_rotation()
        
        control.color_respect_side(True)
        
        control_name = control.get()
        
        if side != 'C':
            control_name = cmds.rename(control_name, inc_name(control_name[0:-1] + side))
        
        cmds.parent(control_name, source_control)
        
        for local_group in local_groups:
            connect_translate(control_name, local_group)
        
        new_name = target_control.replace('CNT_', 'ctrl_')
        new_name = cmds.rename(target_control, new_name)
        cmds.delete( get_shapes( new_name ) )
        
        #cmds.parentConstraint(local_control, new_name)
        driver = cmds.listRelatives(source_control, p = True)[0]
        
        connect_translate(source_control, new_name)
        connect_rotate(source_control, new_name)
        
        connect_translate(driver, new_name)
        connect_rotate(driver, new_name)
        
        #local, xform = constrain_local(source_control, new_name)
        
        #cmds.parent(xform, self.control_group)
        
    def set_center_tolerance(self, tolerance_value = 0.001):
        self.center_tolerance = tolerance_value
        
    def set_center_fade(self, bool_value):
        self.center_fade = bool_value
        
    def create(self):
        super(MouthCurveRig, self).create()

        follow_curve_top, cluster_curve_top = self._rebuild_curve(self.curves[0],'top')
        follow_curve_btm, cluster_curve_btm = self._rebuild_curve(self.curves[1], 'btm')
        
        controls_top = self._create_controls(self.curves[0], cluster_curve_top, 'top')
        controls_btm = self._create_controls(self.curves[1], cluster_curve_btm, 'btm')
        
        self._attach_corners(controls_top[0], controls_btm[0], self.local_controls[0], 'R', [self.local_controls[0], self.local_controls[7]])
        self._attach_corners(controls_top[1], controls_btm[1], self.local_controls[1], 'L', [self.local_controls[1], self.local_controls[8]])
        
        if follow_curve_top:
            self._create_deformation(cluster_curve_top, follow_curve_top)
        if follow_curve_btm:
            self._create_deformation(cluster_curve_btm, follow_curve_btm)
        
        
class CheekCurveRig(FaceFollowCurveRig):
    
    def _create_controls(self, follow_curve, cluster_curve, description = None):
        
        cvs = cmds.ls('%s.cv[*]' % cluster_curve, flatten = True)
        count = len(cvs)
        
        controls = []
        drivers = []
        
        for inc in range(0, count):
            control, driver = self._create_inc_control(follow_curve, cluster_curve, inc,)
            
            controls.append(control)
            drivers.append(driver)
            
        create_follow_fade(controls[2], [ drivers[0], drivers[1], drivers[3], drivers[4]])
        create_follow_fade(drivers[2], [ drivers[0], drivers[1], drivers[3], drivers[4]])
        create_follow_fade(controls[0], [ drivers[1], drivers[2], drivers[3] ])
        create_follow_fade(controls[-1], [ drivers[-2], drivers[-3], drivers[-4] ])
        
        return controls
    
    def create(self):
        super(CheekCurveRig, self).create()
        
        follow_curve_top, cluster_curve_top = self._rebuild_curve(self.curves[0], delete_cvs = True)
        
        self._create_controls(self.curves[0], cluster_curve_top)
        
        self._create_deformation(cluster_curve_top, follow_curve_top)
        

class BrowCurveRig(FaceFollowCurveRig):
    
    def __init__(self,description, side):
        super(BrowCurveRig, self).__init__(description, side)
        
        self.middle_fade = False
    
    def _create_control_on_curve(self, follow_curve, percent, sub = False, description = None):
        
        position = cmds.pointOnCurve(follow_curve, top = True, pr = percent)
        
        control = self._create_control(description)
        control.set_curve_type('square')
        control.rotate_shape(90, 0, 0)
        control.hide_scale_attributes()
        
        sub_control = None
        
        if sub:
            sub_control = self._create_control(description, True)
            sub_control.set_curve_type('cube')
            sub_control.scale_shape(.8, .8, .8)
            sub_control.hide_scale_attributes()
            
            cmds.parent(sub_control.get(), control.get())
            
            sub_control = sub_control.get()
        
        cmds.move(position[0], position[1], position[2], control.get())
        
        control_name = control.get()
        cmds.parent(control_name, self.control_group)
        
        xform = create_xform_group(control_name)
        driver = create_xform_group(control_name, 'driver')
        
        attach_to_curve(xform, follow_curve)
        
        return control_name, sub_control, driver, xform
    
    def _create_controls(self, follow_curve, cluster_curve, description = None):
        
        cvs = cmds.ls('%s.cv[*]' % cluster_curve, flatten = True)
        count = len(cvs)
        
        controls = []
        drivers = []
        
        control, sub, driver, xform = self._create_control_on_curve(follow_curve, 0.5, False, description = 'all')
        controls.append(control)
        drivers.append(driver)
        
        for inc in range(0, count):
            control, driver = self._create_inc_control(follow_curve, cluster_curve, inc,)
            
            if inc == 0:
                sub_control = self._create_control('sub', True)
                sub_control.set_curve_type('cube')
                sub_control.scale_shape(.8,.8,.8)
                sub_control.hide_scale_attributes()
                
                match = MatchSpace(control, sub_control.get())
                match.translation_rotation()
                cmds.parent(sub_control.get(), control)
                
                constraint_editor = ConstraintEditor()
                constraint = constraint_editor.get_constraint(self.clusters[inc], 'pointConstraint')
                cmds.delete(constraint)
                
                local, xform = constrain_local(sub_control.get(), self.clusters[inc])\
                
                cmds.parent(xform, self.local_controls[-1])
                #cmds.pointConstraint(sub_control.get(), self.clusters[inc], mo = True)
            
            controls.append(control)
            drivers.append(driver)
            
        if self.middle_fade:
            create_follow_fade(controls[3], [drivers[1], drivers[2], drivers[4], drivers[5] ])
            
        create_follow_fade(controls[1], drivers[2:] )
        create_follow_fade(controls[-1], drivers[1:-1])
        
        for driver in drivers[1:]:
            connect_translate(controls[0], driver)
        
        return controls
    
    def set_middle_fade(self, bool_value):
        
        self.middle_fade = bool_value
        
    
    def create(self):
        super(BrowCurveRig, self).create()
        
        follow_curve_top, cluster_curve_top = self._rebuild_curve( self.curves[0], delete_cvs = True )
        
        self._create_controls(self.curves[0], cluster_curve_top)
        
        self._create_deformation(cluster_curve_top, follow_curve_top)
          
    
class EyeCurveRig(FaceFollowCurveRig):
    def __init__(self, description, side):
        super(EyeCurveRig, self).__init__(description, side)
        
        self.attach_surface = None
        self.top_eye_goal = None
        self.btm_eye_goal = None
        self.control_shape = 'cube'
        
    def _rebuild_curve(self, curve, description = None, spans = 21):
        
        rebuilt_curve, node = cmds.rebuildCurve( curve, 
                                           constructionHistory = True,
                                           replaceOriginal = False,
                                           rebuildType = 0,
                                           endKnots = 1,
                                           keepRange = 0,
                                           keepControlPoints = 0, 
                                           keepEndPoints = 1, 
                                           keepTangents = 0, 
                                           spans = spans,
                                           degree =3)
        
        new_curve = cmds.duplicate(rebuilt_curve, n = 'curve_%s' % self._get_name(description))[0]
        
        cmds.blendShape(rebuilt_curve, new_curve, w = [0,1])
        
        follow_curve = rebuilt_curve
        cluster_curve = new_curve
        
        cmds.parent(follow_curve, self.setup_group)
        cmds.parent(cluster_curve, self.setup_group)
        
        return follow_curve, cluster_curve
        
    def _create_cluster(self, cv_deform, cv_offset, description, follow = True):
        
        cluster_group = cmds.group(em = True, n = inc_name(self._get_name(description)))
        cmds.parent(cluster_group, self.setup_group)
        
        cluster, handle = create_cluster(cv_deform, self._get_name(description = description))
        self.clusters.append(handle)
        
        bind_pre = create_cluster_bindpre(cluster, handle)
        
        buffer = cmds.group(em = True, n = inc_name('buffer_%s' % handle))
        
        match = MatchSpace(handle, buffer)
        match.translation_to_rotate_pivot()
        
        cmds.parent(handle, buffer)
        cmds.parent(buffer, cluster_group)
        
        xform = create_xform_group(buffer)
        driver3 = create_xform_group(buffer, 'driver3')
        driver2 = create_xform_group(buffer, 'driver2')
        driver1 = create_xform_group(buffer, 'driver1')
        
        if self.attach_surface and follow:
            
            surface_follow = cmds.group(em = True, n = inc_name('surfaceFollow_%s' % handle))
            #surface_follow_offset = cmds.group(em = True, n = inc_name('surfaceFollowOffset_%s' % handle))
            
            cmds.parent(surface_follow, xform)
            #cmds.parent(surface_follow_offset, xform)
        
            match = MatchSpace(handle, surface_follow)
            match.translation_to_rotate_pivot()
            
            #match = MatchSpace(surface_follow, surface_follow_offset)
            #match.translation_rotation()
            
            cmds.pointConstraint(driver3, surface_follow, mo = True)
            cmds.geometryConstraint(self.attach_surface, surface_follow)
            #cmds.geometryConstraint(self.attach_surface, surface_follow_offset)
            
            connect_translate(driver3, surface_follow)
            
            cmds.pointConstraint(surface_follow, driver2, mo = True)
            
            
            #cmds.pointConstraint(xform, surface_follow_offset, mo = True)
        
        cmds.parent(bind_pre, xform)
        
        return xform, driver3, driver1
        
    def _create_inc_cluster(self, follow_curve, cluster_curve, offset_curve, inc, description, follow = True):
        
        cv_deform = '%s.cv[%s]' % (cluster_curve, inc)
        cv_offset = '%s.cv[%s]' % (offset_curve, inc)
        
        xform, driver, local_driver = self._create_cluster(cv_deform, cv_offset, description, follow)
            
        return driver, local_driver

    def _create_follow(self, source_drivers, target_drivers, percent = 0.6):
        
        count = len(source_drivers)
        
        for inc in range(0, count):
            
            connect_multiply('%s.translateX' % source_drivers[inc], '%s.translateX' % target_drivers[inc], percent, True)
            connect_multiply('%s.translateY' % source_drivers[inc], '%s.translateY' % target_drivers[inc], percent, True)
            connect_multiply('%s.translateZ' % source_drivers[inc], '%s.translateZ' % target_drivers[inc], percent, True)

        return
        
    def _create_clusters(self, follow_curve, deform_curve, offset_curve, description, follow = True):
        
        cvs = cmds.ls('%s.cv[*]' % deform_curve, flatten = True)
        count = len(cvs)
        
        drivers = []
        local_drivers = []
        
        for inc in range(0, count):
            driver, local_driver = self._create_inc_cluster(follow_curve, deform_curve, offset_curve, inc, description, follow)
            drivers.append(driver)
            local_drivers.append(local_driver)
            
        return drivers, local_drivers
        
    def _create_control_on_curve(self, follow_curve, percent, sub = True, description = None):
        
        position = cmds.pointOnCurve(follow_curve, top = True, pr = percent)
        
        control = self._create_control(description)
        control.set_curve_type(self.control_shape)
        control.hide_scale_attributes()
        
        sub_control = None
        
        if sub:
            sub_control = self._create_control(description, True)
            sub_control.set_curve_type(self.control_shape)
            sub_control.scale_shape(.8, .8, .8)
            sub_control.hide_scale_attributes()
            
            cmds.parent(sub_control.get(), control.get())
            
            sub_control = sub_control.get()
        
        cmds.move(position[0], position[1], position[2], control.get())
        
        control_name = control.get()
        cmds.parent(control_name, self.control_group)
        
        create_xform_group(control_name)
        driver = create_xform_group(control_name, 'driver')
        
        return control_name, sub_control, driver
        
    def _create_fade(self, start_control, mid_control, end_control, drivers):
        
        reverse_drivers = list(drivers) 
        reverse_drivers.reverse()
        
        multiply_groups = {}
        
        if start_control:
            multiply_groups['side1'] = create_follow_fade(start_control, drivers, -1)
        if end_control:
            multiply_groups['side2'] = create_follow_fade(end_control, reverse_drivers, -1)
        
        if mid_control:
            multiply_groups['sides'] = create_follow_fade(mid_control, drivers, -1)
        
        return multiply_groups
    
    def _get_y_intersection(self, curve, vector):
        
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
       
    def _fix_lid_fade(self, top_curve, btm_curve, multiplies):

        mid_control = multiplies[0]['source']
        
        control_position = cmds.xform(mid_control, q = True, ws = True, t = True)
        control_position_y = [0, control_position[1], 0]
        
        parameter = self._get_y_intersection(btm_curve, control_position)
        
        control_at_curve_position = cmds.pointOnCurve(btm_curve, parameter = parameter)
        control_at_curve_y = [0, control_at_curve_position[1], 0]
        
        total_distance = vtool.util.get_distance(control_position_y, control_at_curve_y)
        
        multi_count = len(multiplies)
        
        
        for inc in range(0, multi_count):
            multi = multiplies[inc]['node']
            driver = multiplies[inc]['target']
            
            driver_position = cmds.xform(driver, q = True, ws = True, t = True)
            driver_position_y = [0, driver_position[1], 0]
            
            parameter = self._get_y_intersection(btm_curve, driver_position)
            
            driver_at_curve = cmds.pointOnCurve(btm_curve, parameter = parameter)
            driver_at_curve_y = [0, driver_at_curve[1], 0]
            
            driver_distance = vtool.util.get_distance(driver_position_y, driver_at_curve_y)
            
            value = (driver_distance/total_distance)
        
            cmds.setAttr('%s.input2Y' % multi, value)

    def _create_controls(self, curve, sub = False):
        
        control_dict = {}
        
        start_controls = self._create_control_on_curve(curve, 0, sub = sub)
        
        mid_controls = self._create_control_on_curve(curve, 0.5, sub = sub)
        
        end_controls = self._create_control_on_curve(curve, 1, sub = sub)
        
        control_dict['start'] = start_controls
        control_dict['mid'] = mid_controls
        control_dict['end'] = end_controls
        
        return control_dict
    
    def set_top_eye_goal(self, curve):
        self.top_eye_goal = curve
    
    def set_btm_eye_goal(self, curve):
        self.btm_eye_goal = curve
    
    def set_attach_surface(self, surface):
        self.attach_surface = surface
    
    def create(self):
        super(EyeCurveRig, self).create()
        
        
        follow_curve_top, deform_curve_top = self._rebuild_curve(self.curves[0], 'top')
            
        follow_curve_btm, deform_curve_btm = self._rebuild_curve(self.curves[1], 'btm')
        
        if cmds.objExists(self.curves[2]):
            follow_curve_mid, deform_curve_mid = self._rebuild_curve(self.curves[2], 'mid')
        
        if cmds.objExists(self.curves[3]):
            follow_curve_top_liner, deform_curve_top_liner = self._rebuild_curve(self.curves[3], 'top_liner')
            
        follow_curve_btm_liner, deform_curve_btm_liner = self._rebuild_curve(self.curves[4], 'btm_liner')
        
        top_control, top_sub_control, top_driver = self._create_control_on_curve(self.curves[0], 0.5)
        
        drivers_top, drivers_local_top = self._create_clusters(self.curves[0], 
                                                               deform_curve_top,
                                                               follow_curve_top,
                                                               'top')
        
        btm_control, btm_sub_control, btm_driver = self._create_control_on_curve(self.curves[1], 0.5)
        corner_control1, corner_sub_control1, corner_driver1 = self._create_control_on_curve(self.curves[0], 0)
        corner_control2, corner_sub_control2, corner_driver2 = self._create_control_on_curve(self.curves[0], 1)
        
        if cmds.objExists(self.curves[3]):
            top_liner_controls = self._create_controls(self.curves[3])
            
        btm_liner_controls = self._create_controls(self.curves[4])
        
        drivers_btm, drivers_local_btm = self._create_clusters(self.curves[1], 
                                                               deform_curve_btm,
                                                               follow_curve_btm,
                                                               'btm')
        
        if cmds.objExists(self.curves[2]):
            drivers_mid, drivers_local_mid = self._create_clusters(self.curves[2],
                                                               deform_curve_mid,
                                                               follow_curve_mid,
                                                               'mid')
        
        if cmds.objExists(self.curves[3]):
            drivers_liner_top, drivers_local_liner_top = self._create_clusters(self.curves[3],
                                                                               deform_curve_top_liner,
                                                                               follow_curve_top_liner,
                                                                               'liner_top',
                                                                               follow = False)
        
        #if cmds.objExists(self.curves[3]):
        drivers_liner_btm, drivers_local_liner_btm = self._create_clusters(self.curves[4],
                                                                           deform_curve_btm_liner,
                                                                           follow_curve_btm_liner,
                                                                           'liner_btm',
                                                                           follow = False)
    
        if cmds.objExists(self.curves[2]):
            self._create_follow(drivers_top, drivers_mid, 0.5)
            self._create_follow(drivers_liner_top, drivers_mid, 0.225)
        
        top_fades = self._create_fade(corner_control1, top_control, corner_control2, drivers_top)
        btm_fades = self._create_fade(corner_control1, btm_control, corner_control2, drivers_btm)

        sub_fades_top = self._create_fade(corner_sub_control1, top_sub_control, corner_sub_control2, drivers_local_top)
        sub_fades_btm = self._create_fade(corner_sub_control1, btm_sub_control, corner_sub_control2, drivers_local_btm)

        if cmds.objExists(self.curves[3]):
            liner_top_fades = self._create_fade(top_liner_controls['start'][0], 
                                                top_liner_controls['mid'][0], 
                                                top_liner_controls['end'][0],
                                                drivers_liner_top)

        liner_btm_fades = self._create_fade(btm_liner_controls['start'][0], 
                                            btm_liner_controls['mid'][0], 
                                            btm_liner_controls['end'][0],
                                            drivers_liner_btm)
        
        if not self.top_eye_goal:
            self.top_eye_goal = deform_curve_btm
            
        if not self.btm_eye_goal:
            self.btm_eye_goal = deform_curve_top
            
            
        self._fix_lid_fade(deform_curve_top, self.top_eye_goal, top_fades['sides'])
        self._fix_lid_fade(deform_curve_top, self.top_eye_goal, sub_fades_top['sides'])
        
        self._fix_lid_fade(deform_curve_btm, self.btm_eye_goal, btm_fades['sides'])
        self._fix_lid_fade(deform_curve_btm, self.btm_eye_goal, sub_fades_btm['sides'])
        
        if cmds.objExists(self.curves[3]):
            self._fix_lid_fade(deform_curve_top_liner, self.top_eye_goal, liner_top_fades['sides'])
            
        self._fix_lid_fade(deform_curve_btm_liner, self.btm_eye_goal, liner_btm_fades['sides'])
        
        self._create_deformation(deform_curve_top, follow_curve_top)
        self._create_deformation(deform_curve_btm, follow_curve_btm)
        
        if cmds.objExists(self.curves[2]):
            self._create_deformation(deform_curve_mid, follow_curve_mid)
        
        if cmds.objExists(self.curves[3]):
            self._create_deformation(deform_curve_top_liner, follow_curve_top_liner)
            
        self._create_deformation(deform_curve_btm_liner, follow_curve_btm_liner)
        
        
class EyeRig(JointRig):
    def __init__(self, description, side):
        super(EyeRig, self).__init__(description, side)
        self.local_parent = None
        self.parent = None
        
        self.eye_control_move = ['Z', 1]
        self.extra_control = False
        self.rotate_value = 25
        self.limit = 1
        self.skip_ik = False
        
    def _create_ik(self):

        duplicate_hierarchy = DuplicateHierarchy( self.joints[0] )
        
        duplicate_hierarchy.stop_at(self.joints[-1])
        duplicate_hierarchy.replace('joint', 'ik')
        
        self.ik_chain = duplicate_hierarchy.create()
        
        cmds.parent(self.ik_chain[0], self.setup_group)
        """
        if self.extra_control:
            duplicate_hierarchy = DuplicateHierarchy( self.joints[0] )
        
            duplicate_hierarchy.stop_at(self.joints[-1])
            duplicate_hierarchy.replace('joint', 'extra_ik')
            self.extra_ik_chain = duplicate_hierarchy.create()
            cmds.parent(self.extra_ik_chain[0], self.setup_group)
        """
        
        if not self.skip_ik:
            ik = IkHandle(self.description)
            ik.set_start_joint(self.ik_chain[0])
            ik.set_end_joint(self.ik_chain[1])
            handle = ik.create()
            
            cmds.parent(handle, self.setup_group)
        
            return handle
    
    def _create_eye_control(self, handle = None):
        
        control = None
        
        if not self.skip_ik:
            group1 = cmds.group(em = True, n = self._get_name('group', 'aim'))
            group2 = cmds.group(em = True, n = self._get_name('group', 'aim'))
            
            
            cmds.parent(group2, group1)
            cmds.parent(group1, self.setup_group)
            
            
            MatchSpace(self.joints[0], group1).translation_rotation()
            
            xform = create_xform_group(group1)
            
            connect_rotate(self.ik_chain[0], group1)
            
            if not self.extra_control:
                cmds.orientConstraint(group2, self.joints[0])
            
            control =self._create_control()
            control.hide_scale_attributes()
            control = control.get()
            
            
            match = MatchSpace(self.joints[1], control)
            match.translation_rotation()
            
            cmds.parent(control, self.control_group)
            
            xform = create_xform_group(control)
            local_group, local_xform = constrain_local(control, handle)
            cmds.parent(local_xform, self.setup_group)

            if self.local_parent:
                cmds.parent(local_xform, self.local_parent)
                
            if self.parent:
                cmds.parent(xform, self.parent)

        if self.skip_ik:
            group1 = cmds.group(em = True, n = self._get_name('group', 'aim'))
            group2 = cmds.group(em = True, n = self._get_name('group', 'aim'))
            
            cmds.parent(group2, group1)
            cmds.parent(group1, self.setup_group)
            
            MatchSpace(self.joints[0], group1).translation_rotation()
            
            xform = create_xform_group(group1)
            
            cmds.orientConstraint(group2, self.joints[0])
        
        if self.extra_control:
            
            parent_group = cmds.group(em = True, n = inc_name(self._get_name('group', 'extra')))
            aim_group = cmds.group(em = True, n = inc_name(self._get_name('group', 'aim_extra')))
            
            MatchSpace(self.joints[0], aim_group).translation_rotation()
            MatchSpace(self.joints[0], parent_group).translation_rotation()
            
            cmds.parent(aim_group, parent_group)
            
            cmds.orientConstraint(group2, parent_group, mo = True)
            cmds.parent(parent_group, self.control_group)
            
            
            
            cmds.orientConstraint(aim_group, self.joints[0])
            
            control2 = self._create_control(sub = True)
            control2.hide_scale_and_visibility_attributes()
            control2 = control2.get()
        
            match = MatchSpace(self.joints[0], control2)
            match.translation_rotation()
            
            
            
            
            
            
        
            axis = self.eye_control_move[0]
            axis_value = self.eye_control_move[1]
                        
            if axis == 'X':
                cmds.move(axis_value, 0,0 , control2, os = True, relative = True)
                connect_multiply('%s.translateZ' % control2, '%s.rotateY' % aim_group, -self.rotate_value )
                connect_multiply('%s.translateY' % control2, '%s.rotateZ' % aim_group, self.rotate_value )
            if axis == 'Y':
                cmds.move(0,axis_value, 0, control2, os = True, relative = True)
                connect_multiply('%s.translateZ' % control2, '%s.rotateX' % aim_group, -self.rotate_value )
                connect_multiply('%s.translateY' % control2, '%s.rotateZ' % aim_group, self.rotate_value )
            if axis == 'Z':
                cmds.move(0,0,axis_value, control2, os = True, relative = True)
                connect_multiply('%s.translateX' % control2, '%s.rotateY' % aim_group, self.rotate_value )
                connect_multiply('%s.translateY' % control2, '%s.rotateX' % aim_group, -self.rotate_value )
            
            xform2 = create_xform_group(control2)            
            cmds.parent(xform2, parent_group)
            
            if axis == 'X':
                cmds.transformLimits(control2,  tx =  (0, 0), etx = (1,1) )
            if axis == 'Y':
                cmds.transformLimits(control2,  ty =  (0, 0), ety = (1,1) )
            if axis == 'Z':
                cmds.transformLimits(control2,  tz =  (0, 0), etz = (1,1) )
            
        return control
    
    def set_parent(self, parent):
        self.parent = parent
    
    def set_local_parent(self, local_parent):
        self.local_parent = local_parent 
    
    def set_extra_control(self, axis, value, rotate_value = 25, limit = 1):
        
        self.eye_control_move = [axis, value]
        self.extra_control = True
        self.rotate_value = rotate_value
    
    def set_skip_ik_control(self, bool_value):
        self.skip_ik = bool_value
        
    
    def create(self):
        
        handle = None
        
        if not self.skip_ik:
            handle = self._create_ik()
        
        control = self._create_eye_control(handle)
        
        if self.skip_ik:
            return
        
        locator = cmds.spaceLocator(n = 'locator_%s' % self._get_name())[0]
        
        
        
        match = MatchSpace(self.joints[0], locator)
        match.translation_rotation()
        
        cmds.parent(locator, self.control_group)
        
        line = RiggedLine(locator, control, self._get_name())        
        cmds.parent( line.create(), self.control_group)
        
        
        cmds.setAttr('%s.translateX' % locator, l = True)
        cmds.setAttr('%s.translateY' % locator, l = True)
        cmds.setAttr('%s.translateZ' % locator, l = True)
        cmds.setAttr('%s.rotateX' % locator, l = True)
        cmds.setAttr('%s.rotateY' % locator, l = True)
        cmds.setAttr('%s.rotateZ' % locator, l = True)
        cmds.hide(locator)
        
class JawRig(FkLocalRig):
    def __init__(self, description, side):
        super(JawRig, self).__init__(description, side)
        self.jaw_slide_offset = .1
        self.jaw_slide_attribute = True
    
    def _attach(self, source_transform, target_transform):
        
        local_group, local_xform = super(JawRig, self)._attach(source_transform, target_transform)
        
        control = self.controls[-1].get()
        live_control = Control(control)
        live_control.rotate_shape(0, 0, 90)
        
        
        var = MayaNumberVariable('autoSlide')
        var.set_variable_type(var.TYPE_DOUBLE)
        var.set_value(self.jaw_slide_offset)
        var.set_keyable(self.jaw_slide_attribute)
        var.create(control)
        
        driver = create_xform_group(control, 'driver')
        driver_local = create_xform_group(local_group, 'driver')
        
        multi = connect_multiply('%s.rotateX' % control, '%s.translateZ' % driver)
        cmds.connectAttr('%s.outputX' % multi, '%s.translateZ' % driver_local)
        var.connect_out('%s.input2X' % multi)
        
        return local_group, local_xform  
    
    def set_jaw_slide_offset(self, value):
        self.jaw_slide_offset = value
        
    def set_create_jaw_slide_attribute(self, bool_value):
        self.jaw_slide_attribute = bool_value
        
   
class CustomCurveRig(BufferRig):
    
    def __init__(self, name, side):
        super(CustomCurveRig, self).__init__(name, side)
        self.locators = []
        self.drivers = []   
        self.control_shape = 'square'
        self.surface = None 
        
    def _create_control_on_curve(self, curve, percent, sub = True, description = None):
        
        position = cmds.pointOnCurve(curve, top = True, pr = percent)
        
        control = self._create_control(description)
        control.set_curve_type(self.control_shape)
        control.hide_scale_attributes()
        
        sub_control = None
        
        if sub:
            sub_control = self._create_control(description, True)
            sub_control.set_curve_type(self.control_shape)
            sub_control.scale_shape(.8, .8, .8)
            sub_control.hide_scale_attributes()
            
            cmds.parent(sub_control.get(), control.get())
            
            sub_control = sub_control.get()
        
        cmds.move(position[0], position[1], position[2], control.get())
        
        control_name = control.get()
        cmds.parent(control_name, self.control_group)
        
        create_xform_group(control_name)
        driver = create_xform_group(control_name, 'driver')
        
        return control_name, sub_control, driver
    
    def _create_locator(self, transform):
        locator = cmds.spaceLocator(n = inc_name('locator_%s' % self._get_name()))[0]
                    
        MatchSpace(transform, locator).translation_rotation()
        xform = create_xform_group(locator)
        driver = create_xform_group(locator, 'driver')
        
        if self.surface:
            cmds.geometryConstraint(self.surface, driver)
        
        return locator, driver, xform
    
    def add_fade_control(self, name, percent, sub = False, target_curve = None, extra_drivers = []):
        
        curve = transforms_to_curve(self.locators, 6, 'temp')
        
        control_name, sub_control_name, driver = self._create_control_on_curve(curve, percent, sub, name)
        
        cmds.delete(curve)
        
        drivers = self.drivers + extra_drivers
        
        multiplies = create_follow_fade(control_name, drivers, -1)
        
        if sub:
            sub_multiplies = create_follow_fade(sub_control_name, self.locators, -1)
        
        
        if target_curve:
            fix_fade(target_curve, multiplies)
            
            if sub:
                fix_fade(target_curve, sub_multiplies)
                
        return multiplies
    
        if sub:
            return multiplies, sub_multiplies
            
    def insert_fade_control(self, control, sub_control = None, target_curve = None):
        multiplies = create_follow_fade(control, self.drivers, -1)
        
        if sub_control:
            sub_multiplies = create_follow_fade(sub_control, self.locators, -1)
        
        if target_curve:
            fix_fade(target_curve, multiplies)
            fix_fade(target_curve, sub_multiplies)
           
    def insert_follows(self, joints, percent = 0.5, create_locator = True):
        
        joint_count = len(joints)
        
        if create_locator:
            locator_group = cmds.group(em = True, n = inc_name('locators_follow_%s' % self._get_name()))
        
        locators = []
        xforms = []
        
        for inc in range(0, joint_count):
            
            if create_locator:
                locator, driver, xform = self._create_locator(joints[inc])
            
            if not create_locator:
                locator = joints[inc]
                driver = cmds.listRelatives(joints[inc], p = True)[0]
            
            all_axis = ['X','Y','Z']
            
            for axis in all_axis:
                connect_multiply('%s.translate%s' % (self.drivers[inc], axis), '%s.translate%s' % (driver, axis), percent, skip_attach = True)
                
                connect_multiply('%s.translate%s' % (self.locators[inc], axis), '%s.translate%s' % (locator, axis), percent, skip_attach = True)
            
            if create_locator:
                cmds.parentConstraint(locator, joints[inc])
                xforms.append(xform)
            
            locators.append(locator)
            
        if create_locator:
            cmds.parent(xforms, locator_group)
            cmds.parent(locator_group, self.setup_group)
            
        return locators
            
    def set_surface(self, surface):
        self.surface = surface
          
    
            
    def create(self):        
        BufferRig.create(self)
        
        locator_group = cmds.group(em = True, n = 'locators_%s' % self._get_name())
        cmds.parent(locator_group, self.setup_group)
        
        for joint in self.joints:
            
            locator, driver, xform = self._create_locator(joint)
            
            self.locators.append(locator)
            self.drivers.append(driver)
            
            cmds.parent(xform, locator_group)
            
            cmds.parentConstraint(locator, joint)
        
class CurveAndSurfaceRig(BufferRig):
    
    def __init__(self, description, side):
        super(CurveAndSurfaceRig, self).__init__(description, side)
        self.span_count = 4
        self.surface = None
        self.clusters = []
        self.control_shape = 'square'
        self.delete_end_cvs = True
        self.respect_side = False
    

        
    def _create_inc_control(self, curve, inc, sub = False, description = None, center_tolerance = 0.001):
        
        control = self._create_control(description, sub = sub)
        
        control.rotate_shape(90, 0, 0)
        control.hide_scale_attributes()
        
        cluster, handle = create_cluster('%s.cv[%s]' % (curve, inc), self._get_name())
        self.clusters.append(handle)
        
        match = MatchSpace(handle, control.get())
        match.translation_to_rotate_pivot()
        
        control_name = control.get()
        
        if self.respect_side:
            side = control.color_respect_side(sub, center_tolerance = center_tolerance)
            
            if side != 'C':
                control_name = cmds.rename(control.get(), inc_name(control.get()[0:-1] + side))
        
        xform = create_xform_group(control_name)
        driver = create_xform_group(control_name, 'driver')
        
        bind_pre = create_cluster_bindpre(cluster, handle)
        
        local_group, xform_group = constrain_local(control_name, handle, parent = True)
        
        local_driver = create_xform_group(local_group, 'driver')
        connect_translate(driver, local_driver)
        connect_translate(xform, xform_group)
        
        cmds.parent(bind_pre, xform_group)
                
        cmds.parent(xform, self.control_group)
        cmds.parent(xform_group, self.setup_group)
        
        return control_name, driver
        
    def _create_inc_sub_control(self, control, curve, inc):
        sub_control = self._create_inc_control(self.no_follow_curve, inc, sub = True)
        sub_control = Control(sub_control[0])
            
        sub_control.scale_shape(.8,.8,.8)
        sub_control.hide_scale_attributes()
        
        match = MatchSpace(control, sub_control.get())
        match.translation_rotation()
        cmds.parent(sub_control.get(), control)
        
    def _create_controls(self, description = None):
        
        cvs1 = cmds.ls('%s.cv[*]' % self.curve, flatten = True)
        count = len(cvs1)
        
        controls = []
        
        for inc in range(0, count):
            
            control, driver = self._create_inc_control(self.curve, inc)
            if self.surface:
                self._create_inc_sub_control(control, self.curve, inc)
            
            if self.respect_side:
                reverse_inc = (count-inc) -1
                
                if inc != reverse_inc:     
                    control, driver = self._create_inc_control(self.curve, reverse_inc)
                    if self.surface:
                        self._create_inc_sub_control(control, self.curve, reverse_inc)    
                
                if inc == reverse_inc:
                    break
                
        return controls               

    def _attach_joints_to_curve(self):
        
        for joint in self.joints:
            
            follow_locator = cmds.spaceLocator(n = 'locatorFollow_%s' % joint)[0]
            locator = cmds.spaceLocator(n = 'locatorNoFollow_%s' % joint)[0]
            
            xform = create_xform_group(locator)
            
            MatchSpace(joint, follow_locator).translation_rotation()
            MatchSpace(joint, locator).translation_rotation()
            
            attach_to_curve(follow_locator, self.curve, maintain_offset = True)
            attach_to_curve(locator, self.no_follow_curve, maintain_offset = True)
            
            if self.surface:
                cmds.geometryConstraint(self.surface, follow_locator)
            
            cmds.parent(xform, follow_locator)
            
            cmds.pointConstraint(locator, joint)
            
            cmds.parent(follow_locator, self.setup_group)
       
    def set_surface(self, surface_name):
        self.surface = surface_name
    
    def set_curve_spans(self, span_count):
        
        self.span_count = span_count
        
    def set_respect_side(self, bool_value):
        self.respect_side = bool_value
        
    def set_delete_end_cvs(self, bool_value):
        self.delete_end_cvs = bool_value
        
    def create(self):
        
        self.curve = transforms_to_curve(self.joints, self.span_count, self.description)
        cmds.parent(self.curve, self.setup_group)
        
        if self.delete_end_cvs:
            cvs = cmds.ls('%s.cv[*]' % self.curve, flatten = True)
            cmds.delete(cvs[1], cvs[-2])
        
        self.no_follow_curve = cmds.duplicate(self.curve)[0]
        
        self._create_controls(self.curve)
        
        self._attach_joints_to_curve()
        
        
        
                
#--- Misc Rig

class ConvertJointToNub(object):

    def __init__(self, name, side = 'C'):
        self.start_joint = None
        self.end_joint = None
        self.count = 10
        self.prefix = 'joint'
        self.name = name
        self.side = side
        
        self.add_mid_control = True
        
        self.joints = []
        self.control_group = None
        self.setup_group = None
        self.control_shape = 'pin_round'
        self.add_sub_joints = False
        
        self.up_object = None
        
    def set_start_joint(self, joint):
        self.start_joint = joint
    
    def set_end_joint(self, joint):
        self.end_joint = joint
        
    def set_joints(self, joints):
        self.joints = joints
        
    def set_create_mid_control(self, bool_value):
        self.add_mid_control = bool_value
        
    def set_joint_count(self, count):
        self.count = count
        
    def set_control_shape(self, shape_type_name):
        self.control_shape = shape_type_name
        
    def set_prefix(self, prefix):
        self.prefix = prefix
        
    def set_add_sub_joints(self, bool_value):
        self.add_sub_joints = bool_value
        
    def set_up_object(self, name):
        self.up_object = name
        
    def create(self):
        
        parent_joints = False
        
        if not self.joints:
            parent_joints = True
            joints = subdivide_joint(self.start_joint, 
                                     self.end_joint, 
                                     self.count, self.prefix, 
                                     '%s_1_%s' % (self.name,self.side), True)
            
            for joint in joints[:-1]:
                orient = OrientJoint(joint)
                
                if not self.up_object:
                    self.up_object = self.start_joint
                    
                orient.set_aim_up_at_object(self.up_object)
                orient.run()
            
            
                
            cmds.makeIdentity(joints[-1], r = True, jo = True, apply = True)
            
            
            self.joints = joints
            
            
        parent_map = {}
            
        if self.add_sub_joints:
            
            new_joints = []
            
            for joint in self.joints:
                duplicate = cmds.duplicate(joint, po = True)
                
                new_name = joint[0].upper() + joint[1:]
                
                new_joint = cmds.rename(joint, 'xform%s' % new_name)
                duplicate = cmds.rename(duplicate, joint)
                cmds.parent(duplicate, w = True)
                
                new_joints.append(new_joint)
                
                parent_map[new_joint] = duplicate
                
            self.joints = new_joints
        
        rig = IkSplineNubRig(self.name, self.side)
        rig.set_joints(self.joints)
        rig.set_end_with_locator(True)
        rig.set_create_middle_control(self.add_mid_control)
        rig.set_control_shape(self.control_shape)
        rig.set_buffer(False)
        rig.create()
        
        self.top_control = rig.top_control
        self.btm_control = rig.btm_control
        self.top_xform = rig.top_xform
        self.btm_xform = rig.btm_xform
        
        if parent_joints:
            cmds.parent(joints[0], rig.setup_group)
        
        if parent_map:
            for joint in parent_map:
                cmds.parent(parent_map[joint], joint)
        
        self.control_group = rig.control_group
        self.setup_group = rig.setup_group
        
    def get_control_group(self):
        return self.control_group
    
    def get_setup_group(self):
        return self.setup_group
    
    def get_joints(self):
        return self.joints

class FinRig(JointRig):
    
    def _create_top_control(self):
        top_control = self._create_control('top')
        top_control.hide_scale_and_visibility_attributes()
        top_control.set_curve_type('cube')
        top_control.scale_shape(2, 2, 2)
        
        top_control = top_control.get()
        
        match = MatchSpace(self.joints[0], top_control)
        match.translation_rotation()
        
        cmds.parent(top_control, self.control_group)
        
        create_xform_group(top_control)
        
        spread = MayaNumberVariable('spread')
        spread.create(top_control)
        
        return top_control
    
    def _create_sub_controls(self, parent):
        
        sub_controls = []
        drivers = []
        
        joint_count = len(self.joints)
        
        section = 2.00/joint_count
        
        spread_offset = 1.00
        
        for joint in self.joints:
    
            sub_control = self._create_control(sub = True)
            sub_control.hide_scale_and_visibility_attributes()
            
            sub_control = sub_control.get()
            
            match = MatchSpace(joint, sub_control)
            match.translation_rotation()
            
            #cmds.parent(sub_control, parent)
            
            xform = create_xform_group(sub_control)
            driver = create_xform_group(sub_control, 'driver')
            
            cmds.parentConstraint(sub_control, joint)
            cmds.scaleConstraint(sub_control, joint)
            
            connect_multiply('%s.spread' % parent, '%s.rotateZ' % driver, spread_offset)
            
            
            connect_plus('%s.translateX' % parent, '%s.translateX' % driver)
            connect_plus('%s.translateY' % parent, '%s.translateY' % driver)
            connect_plus('%s.translateZ' % parent, '%s.translateZ' % driver)
            
            connect_plus('%s.rotateX' % parent, '%s.rotateX' % driver)
            connect_plus('%s.rotateY' % parent, '%s.rotateY' % driver)
            connect_plus('%s.rotateZ' % parent, '%s.rotateZ' % driver)
            
            
            
            sub_controls.append(sub_control)
            drivers.append(driver)
            cmds.parent(xform, self.control_group)
            
            spread_offset -= section
            
        create_attribute_lag(sub_controls[0], 'rotateY',  drivers[1:])
    
    def create(self):
        super(FinRig, self).create()
        
        top_control = self._create_top_control()
        
        self._create_sub_controls(top_control)
        
  

class RiggedLine(object):
    def __init__(self, top_transform, btm_transform, name):
        self.name = name
        self.top = top_transform
        self.btm = btm_transform
        self.local = False
    
    def _build_top_group(self):
        
        self.top_group = cmds.group(em = True, n = 'guideLineGroup_%s' % self.name)
        cmds.setAttr('%s.inheritsTransform' % self.top_group, 0)
    
    def _create_curve(self):
        self.curve = cmds.curve(d = 1, p = [(0, 0, 0),(0,0,0)], k = [0, 1] , n = inc_name('guideLine_%s' % self.name))
        cmds.setAttr('%s.template' % self.curve, 1)
        
        cmds.parent(self.curve, self.top_group)
    
    def _create_cluster(self, curve, cv):
        cluster, transform = cmds.cluster('%s.cv[%s]' % (self.curve,cv))
        transform = cmds.rename(transform, inc_name('guideLine_cluster_%s' % self.name))
        cluster = cmds.rename('%sCluster' % transform, inc_name('cluster_guideline_%s' % self.name) )
        cmds.hide(transform)
        
        cmds.parent(transform, self.top_group)
        
        return [cluster, transform]
        
    def _match_clusters(self):
        
        match = MatchSpace(self.top, self.cluster1[1])
        match.translation_to_rotate_pivot()
        
        match = MatchSpace(self.btm, self.cluster2[1])
        match.translation_to_rotate_pivot()
    
    def _create_clusters(self):
        self.cluster1 = self._create_cluster(self.curve, 0)
        self.cluster2 = self._create_cluster(self.curve, 1)
    
    def _constrain_clusters(self):
        
        if self.local:
            #CBB
            offset1 = cmds.group(em = True, n = 'xform_%s' % self.cluster1[1])
            offset2 = cmds.group(em = True, n = 'xform_%s' % self.cluster2[1])
            
            cmds.parent(offset1, offset2, self.top_group)

            cmds.parent(self.cluster1[1], offset1)
            cmds.parent(self.cluster2[1], offset2)
            
            match = MatchSpace(self.top, offset1)
            match.translation()
            
            match = MatchSpace(self.btm, offset2)
            match.translation()
            
            constrain_local(self.top, offset1)
            constrain_local(self.btm, offset2)
            
        if not self.local:
            cmds.pointConstraint(self.top, self.cluster1[1])
            cmds.pointConstraint(self.btm, self.cluster2[1])
    
    def set_local(self, bool_value):
        self.local = bool_value
        
    
    def create(self):
        
        self._build_top_group()
        
        self._create_curve()
        self._create_clusters()
        self._match_clusters()
        self._constrain_clusters()
        
        return self.top_group

class ClusterObject(object):
    
    def __init__(self, geometry, name):
        self.geometry = geometry
        self.join_ends = False
        self.name = name
        self.cvs = []
        self.cv_count = 0
        self.clusters = []
        self.handles = []
        
    def _create_cluster(self, cvs):
        return create_cluster(cvs, self.name)
        
    def get_cluster_list(self):
        return self.clusters
    
    def get_cluster_handle_list(self):
        return  self.handles
        
    def create(self):
        self._create()

class ClusterSurface(ClusterObject):
    
    def __init__(self, geometry, name):
        super(ClusterSurface, self).__init__(geometry, name)
        
        self.join_ends = False
        self.join_both_ends = False
        
        self.maya_type = None
        
        if has_shape_of_type(self.geometry, 'nurbsCurve'):
            self.maya_type = 'nurbsCurve'
        if has_shape_of_type(self.geometry, 'nurbsSurface'):
            self.maya_type = 'nurbsSurface'
        
    
    def set_join_ends(self, bool_value):
        
        self.join_ends = bool_value
        
    def set_join_both_ends(self, bool_value):
        self.join_both_ends = bool_value
    
    def _create_start_and_end_clusters(self):
        
        start_cvs = None
        end_cvs = None
        start_position = None
        end_position = None
        
        if self.maya_type == 'nurbsCurve':
            
            start_cvs = '%s.cv[0:1]' % self.geometry
            end_cvs = '%s.cv[%s:%s]' % (self.geometry,self.cv_count-2, self.cv_count-1)
            
            start_position = cmds.xform('%s.cv[0]' % self.geometry, q = True, ws = True, t = True)
            end_position = cmds.xform('%s.cv[%s]' % (self.geometry,self.cv_count-1), q = True, ws = True, t = True)
            
            
        if self.maya_type == 'nurbsSurface':
            
            start_cvs = '%s.cv[0:1][0:1]' % self.geometry
            
            end_cvs = '%s.cv[0:1][%s:%s]' % (self.geometry,self.cv_count-2, self.cv_count-1)
            
            p1 = cmds.xform('%s.cv[0][0]' % self.geometry, q = True, ws = True, t = True)
            p2 = cmds.xform('%s.cv[1][0]' % self.geometry, q = True, ws = True, t = True)
            
            start_position = vtool.util.get_midpoint(p1, p2)
            
            p1 = cmds.xform('%s.cv[0][%s]' % (self.geometry, self.cv_count-1), q = True, ws = True, t = True)
            p2 = cmds.xform('%s.cv[1][%s]' % (self.geometry, self.cv_count-1), q = True, ws = True, t = True)
            
            end_position = vtool.util.get_midpoint(p1, p2)
        
        cluster, handle = self._create_cluster(start_cvs)
        
        self.clusters.append(cluster)
        self.handles.append(handle)
        
        cmds.xform(handle, ws = True, rp = start_position, sp = start_position)
        
        last_cluster, last_handle = self._create_cluster(end_cvs)
        
        cmds.xform(last_handle, ws = True, rp = end_position, sp = end_position)

        
        return last_cluster, last_handle
    
    def _create_start_and_end_joined_cluster(self):
        
        start_cvs = None
        end_cvs = None
        
        if self.join_ends:
            if self.maya_type == 'nurbsCurve':
                start_cvs = '%s.cv[0:1]' % self.geometry
                end_cvs = '%s.cv[%s:%s]' % (self.geometry,self.cv_count-2, self.cv_count-1)
                
            if self.maya_type == 'nurbsSurface':
                start_cvs = '%s.cv[0:1][0:1]' % self.geometry
                end_cvs = '%s.cv[0:1][%s:%s]' % (self.geometry,self.cv_count-2, self.cv_count-1)
                
        
                
        cmds.select([start_cvs, end_cvs])
        cvs = cmds.ls(sl = True)
            
        cluster, handle = self._create_cluster(cvs)
        self.clusters.append(cluster)
        self.handles.append(handle)
                
                
    
    def _create(self):
        
        
        
        self.cvs = cmds.ls('%s.cv[*]' % self.geometry, flatten = True)
        
        if self.maya_type == 'nurbsCurve':
            self.cv_count = len(self.cvs)
        if self.maya_type == 'nurbsSurface':
            self.cv_count = len(cmds.ls('%s.cv[0][*]' % self.geometry, flatten = True))
        
        start_inc = 0
        
        cv_count = self.cv_count
        
        if self.join_ends:
            
            
            if not self.join_both_ends:
                
                last_cluster, last_handle = self._create_start_and_end_clusters()
            
            if self.join_both_ends:
                
                
                self._create_start_and_end_joined_cluster()
                
            cv_count = len(self.cvs[2:self.cv_count])
            start_inc = 2
            
        for inc in range(start_inc, cv_count):
            
            if self.maya_type == 'nurbsCurve':
                cv = '%s.cv[%s]' % (self.geometry, inc)
            if self.maya_type == 'nurbsSurface':
                cv = '%s.cv[0:1][%s]' % (self.geometry, inc)
            
            cluster, handle = self._create_cluster( cv )
            
            self.clusters.append(cluster)
            self.handles.append(handle)
    
        if self.join_ends and not self.join_both_ends:
            self.clusters.append(last_cluster)
            self.handles.append(last_handle)
        
        return self.clusters
    

class ClusterCurve(ClusterSurface):
        
    def _create_start_and_end_clusters(self):
        cluster, handle = self._create_cluster('%s.cv[0:1]' % self.geometry)
        
        self.clusters.append(cluster)
        self.handles.append(handle)
        
        position = cmds.xform('%s.cv[0]' % self.geometry, q = True, ws = True, t = True)
        cmds.xform(handle, ws = True, rp = position, sp = position)
        
        last_cluster, last_handle = self._create_cluster('%s.cv[%s:%s]' % (self.geometry,self.cv_count-2, self.cv_count-1) )
        
        position = cmds.xform('%s.cv[%s]' % (self.geometry,self.cv_count-1), q = True, ws = True, t = True)
        cmds.xform(last_handle, ws = True, rp = position, sp = position)
        
        return last_cluster, last_handle
    
    
        
    def _create(self):
        
        
        self.cvs = cmds.ls('%s.cv[*]' % self.geometry, flatten = True)
        
        self.cv_count = len(self.cvs)
        
        start_inc = 0
        
        cv_count = self.cv_count
        
        if self.join_ends:
            last_cluster, last_handle = self._create_start_and_end_clusters()
            
            cv_count = len(self.cvs[2:self.cv_count])
            start_inc = 2
            
        for inc in range(start_inc, cv_count):
            cluster, handle = self._create_cluster( '%s.cv[%s]' % (self.geometry, inc) )
            
            self.clusters.append(cluster)
            self.handles.append(handle)
    
        if self.join_ends:
            self.clusters.append(last_cluster)
            self.handles.append(last_handle)
        
        return self.clusters
    
    
           
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
        
        vert_iterator = IterateEdges(shape)
        vert_ids = vert_iterator.get_vertices(edge_index_1)
        
        edge_to_curve_1 = cmds.createNode('polyEdgeToCurve', n = inc_name('rivetCurve1_%s' % self.name))
        cmds.setAttr('%s.inputComponents' % edge_to_curve_1, 2,'vtx[%s]' % vert_ids[0], 'vtx[%s]' % vert_ids[1], type='componentList')
        
        vert_iterator = IterateEdges(shape)
        vert_ids = vert_iterator.get_vertices(edge_index_2)
        
        edge_to_curve_2 = cmds.createNode('polyEdgeToCurve', n = inc_name('rivetCurve2_%s' % self.name))
        
        cmds.setAttr('%s.inputComponents' % edge_to_curve_2, 2,'vtx[%s]' % vert_ids[0], 'vtx[%s]' % vert_ids[1], type='componentList')
        
        
        cmds.connectAttr('%s.worldMatrix' % mesh, '%s.inputMat' % edge_to_curve_1)
        cmds.connectAttr('%s.outMesh' % mesh, '%s.inputPolymesh' % edge_to_curve_1)
        
        cmds.connectAttr('%s.worldMatrix' % mesh, '%s.inputMat' % edge_to_curve_2)
        cmds.connectAttr('%s.outMesh' % mesh, '%s.inputPolymesh' % edge_to_curve_2)
        
        loft = cmds.createNode('loft', n = inc_name('rivetLoft_%s' % self.name))
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
            self.rivet = cmds.spaceLocator(n = inc_name('rivet_%s' % self.name))[0]
            
        if self.create_joint:
            cmds.select(cl = True)
            self.rivet = cmds.joint(n = inc_name('joint_%s' % self.name))
        
    def _create_point_on_surface(self):
        self.point_on_surface = cmds.createNode('pointOnSurfaceInfo', n = inc_name('pointOnSurface_%s' % self.surface ))
        
        cmds.setAttr('%s.turnOnPercentage' % self.point_on_surface, self.percentOn)
        
        cmds.setAttr('%s.parameterU' % self.point_on_surface, self.uv[0])
        cmds.setAttr('%s.parameterV' % self.point_on_surface, self.uv[1])
        
        
    
    def _create_aim_constraint(self):
        self.aim_constraint = cmds.createNode('aimConstraint', n = inc_name('aimConstraint_%s' % self.surface))
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
    
class AttachJoints(object):
    
    def __init__(self, source_joints, target_joints):
        self.source_joints = source_joints
        self.target_joints = target_joints
    
    def _hook_scale_constraint(self, node):
        
        constraint_editor = ConstraintEditor()
        scale_constraint = constraint_editor.get_constraint(node, constraint_editor.constraint_scale)
        
        if not scale_constraint:
            return
        
        weight_count = constraint_editor.get_weight_count(scale_constraint)
        
        cmds.connectAttr('%s.parentInverseMatrix' % node, '%s.constraintParentInverseMatrix' % scale_constraint)
        
        for inc in range(0, weight_count):
            
            target = get_attribute_input('%s.target[%s].targetScale' % (scale_constraint, inc), True)
            
            cmds.connectAttr('%s.parentInverseMatrix' % target, '%s.target[%s].targetParentMatrix' % (scale_constraint, inc) )

    def _unhook_scale_constraint(self, scale_constraint):
        constraint_editor = ConstraintEditor()
        
        weight_count = constraint_editor.get_weight_count(scale_constraint)
        disconnect_attribute('%s.constraintParentInverseMatrix' % scale_constraint)
        
        for inc in range(0, weight_count):
            disconnect_attribute('%s.target[%s].targetParentMatrix' % (scale_constraint, inc))

    def _attach_joint(self, source_joint, target_joint):
        
        self._hook_scale_constraint(target_joint)
        
        parent_constraint = cmds.parentConstraint(source_joint, target_joint, mo = True)[0]
        
        scale_constraint = cmds.scaleConstraint(source_joint, target_joint)[0]
        
        constraint_editor = ConstraintEditor()
        constraint_editor.create_switch(self.target_joints[0], 'switch', parent_constraint)
        constraint_editor.create_switch(self.target_joints[0], 'switch', scale_constraint)
        
        self._unhook_scale_constraint(scale_constraint)
        
    def _attach_joints(self, source_chain, target_chain):
        
        for inc in range( 0, len(source_chain) ):
            self._attach_joint(source_chain[inc], target_chain[inc] )
    
    def set_source_and_target_joints(self, source_joints, target_joints):
        self.source_joints = source_joints
        self.target_joints = target_joints
    
    def create(self):
        self._attach_joints(self.source_joints, self.target_joints)

class Hierarchy(vtool.util.Hierarchy):
    
    def _get_hierarchy(self):
        
        top_node_long = cmds.ls(self.top_of_hierarchy, l = True)

        generations = [[top_node_long[0]]]
        
        children = self._get_children(self.top_of_hierarchy)
        
        generations.append( children ) 
        inc = 0
        while children:
            
            new_generation = []
            
            for child in children:
                sub_children = self._get_children(child)
                
                if sub_children:
                    new_generation += sub_children
                    
            generations.append( new_generation )
            children = new_generation
            
            inc += 1
            if inc > 100:
                break
            
        self._populate_branches_from_relatives(generations)
        
    def _get_children(self, node):
        types = ['transform', 'joint']
        
        children = []
        
        for node_type in types:
            found = cmds.listRelatives(node, type = node_type, fullPath = True)
            
            if found:
                children += found
            
        return children
            
    def _populate_branches_from_relatives(self, generations):

        
        self.generations = []
        
        for inc in range(0, len(generations)):
            branches = []
            
            for relative in generations[inc]:

                split_relative = relative.split('|')
                split_relative = split_relative[1:]

                name = split_relative[-1]
                
                parent = None
                
                if len(split_relative) >=2:
                    parent = split_relative[-2]
    
                branch = self.create_branch(name)
                branch.set_long_name(relative)
                
                if self.generations:
                    for last_branch in self.generations[-1]:
                        if parent == last_branch.name:
                            branch.set_parent(last_branch)
                            last_branch.add_child(branch)
                            break
    
                branches.append(branch)
            
            self.generations.append(branches)
            
    def create_branch(self, name, parent = None):
        
        branch = Branch(name)
        self.branches.append(branch)
        
        if parent:
            branch.set_parent(parent)
        
        return branch
    
    def prefix(self, prefix):
        reverse_generation = list(self.generations)
        reverse_generation.reverse()
        
        for generation in reverse_generation:
            for branch in generation:
                branch.prefix(prefix)
                
        self.top_of_hierarchy = self.generations[0][0].long_name
            
class Branch(vtool.util.Branch):      
    def __init__(self, name):
        super(Branch, self).__init__(name)
        
        self.long_name = ''

    def _update_name(self, new_name):

        split_name = self.long_name.split('|')
        
        split_name[-1] = new_name
        
        new_long_name = string.join(split_name, '|')
        
        self.long_name = new_long_name
        self.name = new_name
        
        
    def set_long_name(self, long_name):
        self.long_name = long_name
        
    def rename(self, new_name):
        new_name = cmds.rename(self.long_name, new_name)
        self._update_name(new_name)
        
    def prefix(self, prefix):
        new_name = prefix_name(self.long_name, prefix, self.name)
        self._update_name(new_name)
        
    

class StoreData(object):
    def __init__(self, node = None):
        self.node = node
        
        if not node:
            return
        
        self.data = MayaStringVariable('DATA')
        self.data.set_node(self.node)
        
        if not cmds.objExists('%s.DATA' % node):
            self.data.create(node)
        
    def set_data(self, data):
        str_value = str(data)
        
        self.data.set_value(str_value)
        
    def get_data(self):
        
        return self.data.get_value()
    
    def eval_data(self):
        data = self.get_data()
        
        if data:
            return eval(data)
        
class StoreControlData(StoreData):
    
    def _get_control_data(self):
        controls = get_controls()
        
        control_data = {}
        
        for control in controls:
            
            attributes = cmds.listAttr(control, k = True)
            
            if not attributes:
                continue
            
            attribute_data = {}
            
            for attribute in attributes:
                if cmds.objExists('%s.%s' % (control,attribute)):
                    value = cmds.getAttr('%s.%s' % (control, attribute))
                
                    attribute_data[attribute] = value 
            
            if attribute_data:
                control_data[control] = attribute_data
            
        return control_data
        
    def _has_transform_value(self, control):
        attributes = ['translate', 'rotate']
        axis = ['X','Y','Z']
        
        for attribute in attributes:
            for a in axis:
                
                attribute_name = '%s.%s%s' % (control, attribute, a) 
                
                if not cmds.objExists(attribute_name):
                    return False
                
                value = cmds.getAttr(attribute_name)
                
                if abs(value) > 0.01:
                    return True
    
    def _get_constraint_type(self, control):
        
        translate = True
        rotate = True
        
        #attributes = ['translate', 'rotate']
        axis = ['X','Y','Z']
        
        
        for a in axis:
            attribute_name = '%s.translate%s' % (control, a)
            
            if cmds.getAttr(attribute_name, l = True):
                translate = False
                break

        for a in axis:
            attribute_name = '%s.rotate%s' % (control, a)
            
            if cmds.getAttr(attribute_name, l = True):
                rotate = False
                break
            
        if translate and rotate:
            return 'parent'
         
        if translate:
            return 'point'
         
        if rotate:
            return 'orient'
    
    def _set_control_data(self, control, data):
        for attribute in data:
            attribute_name = '%s.%s' % (control, attribute)
            
            if not cmds.objExists(attribute_name):
                continue
            
            if cmds.getAttr(attribute_name, lock = True):
                continue
            
            connection = get_attribute_input(attribute_name)
            
            if connection:
                if cmds.nodeType(connection).find('animCurve') == -1:
                    continue
            
            try:
                cmds.setAttr(attribute_name, data[attribute] )  
                
            except:
                cmds.warning('Could not set %s.' % attribute_name)     
        
    def set_data(self):
        
        self.data.set_locked(False)
        data = self._get_control_data()
        super(StoreControlData, self).set_data(data)   
        self.data.set_locked(True)
            
    def eval_data(self, return_only = False):
        data = super(StoreControlData, self).eval_data()
        
        if return_only:
            return data
        
        if not data:
            return

        for control in data:
            
            attribute_data = data[control]
            
            self._set_control_data(control, attribute_data)
            
        return data
            
    def eval_mirror_data(self):  
        data_list = self.eval_data()
            
        for control in data_list:
            other_control = control[:-1] + 'R'
            
            if not cmds.objExists(other_control):
                continue
            
            if cmds.objExists('%s.ikFk' % control):

                value = cmds.getAttr('%s.ikFk' % control)
                other_value = cmds.getAttr('%s.ikFk' % other_control)
                cmds.setAttr('%s.ikFk' % control, other_value)
                cmds.setAttr('%s.ikFk' % other_control, value)
            
            if not self._has_transform_value(control):
                continue 
            
            if not control.endswith('_L'):
                continue               
    
            temp_group = cmds.group(em = True, n = inc_name('temp_%s' % control))
            
            MatchSpace(control, temp_group).translation_rotation()
            parent_group = cmds.group(em = True)
            cmds.parent(temp_group, parent_group)
            
            cmds.setAttr('%s.scaleX' % parent_group, -1)
            
            temp_xform = create_xform_group(temp_group, use_duplicate = True)
            
            zero_xform_channels(control)
                        
            matrix = cmds.xform(control, q = True, os = True, m = True)
            other_matrix = cmds.xform(other_control, q = True, os = True, m = True )
            
            angle = cmds.angleBetween( er = True, v1 = (matrix[0],matrix[1], matrix[2]), v2 = (other_matrix[0], other_matrix[1], other_matrix[2]) )
            #if angle > 30:
            #    cmds.makeIdentity(parent_group, apply = True, s = True)
             
            const1 = cmds.pointConstraint(temp_group, other_control)[0]
            const2 = cmds.orientConstraint(temp_group, other_control)[0]
            #const = cmds.parentConstraint(temp_group, other_control)
            
            cmds.delete([const1, const2])
            #cmds.delete(const)
            #cmds.delete(parent_group)
            
            
            
    def eval_multi_transform_data(self, data_list):
        
        controls = {}
        
        for data in data_list:
            
            last_temp_group = None
            
            for control in data:
                
                if not self._has_transform_value(control):
                    continue
                
                if not controls.has_key(control):
                    controls[control] = []

                temp_group = cmds.group(em = True, n = inc_name('temp_%s' % control))
                
                if not len(controls[control]):
                    MatchSpace(control, temp_group).translation_rotation()
                
                if len( controls[control] ):
                    last_temp_group = controls[control][-1]
                    
                    cmds.parent(temp_group, last_temp_group)
                
                    self._set_control_data(temp_group, data[control])
                                  
                controls[control].append(temp_group)
        
        
        
        for control in controls:
            
            constraint_type = self._get_constraint_type(control)
            
            if constraint_type == 'parent':
                cmds.delete( cmds.parentConstraint(controls[control][-1], control, mo = False) )
            if constraint_type == 'point':
                cmds.delete( cmds.pointConstraint(controls[control][-1], control, mo = False) )
            if constraint_type == 'orient':
                cmds.delete( cmds.orientConstraint(controls[control][-1], control, mo = False) )
                
            cmds.delete(controls[control][0])

class XformTransfer(object):
    def __init__(self, ):
        
        self.source_mesh = None
        self.target_mesh = None
        self.particles = None
        
    def _match_particles(self, scope):        
        
        xforms = []
        for transform in self.scope:
            
            position = cmds.xform(transform, q = True, ws = True, t = True)
            
            xforms.append(position)
        
        self.particles = cmds.particle(p = xforms)[0]
            
    def _wrap_particles(self):
        if self.particles and self.source_mesh:
            
            cmds.select([self.particles,self.source_mesh],replace = True)
            mel.eval('source performCreateWrap.mel; performCreateWrap 0;')
            
            wrap = find_deformer_by_type(self.particles, 'wrap')
            
            cmds.setAttr('%s.exclusiveBind' % wrap, 0)
            cmds.setAttr('%s.autoWeightThreshold' % wrap, 0)
            cmds.setAttr('%s.maxDistance' % wrap, 0)
            cmds.setAttr('%s.falloffMode' % wrap, 0)
    
    def _blend_to_target(self):
        cmds.blendShape(self.target_mesh, self.source_mesh, weight = [0,1], origin = 'world')        
            
    def _move_to_target(self):
        for inc in range(0, len(self.scope)):
            position = cmds.pointPosition('%s.pt[%s]' % (self.particles,inc))
            joint = self.scope[inc]
            cmds.move(position[0], position[1],position[2], '%s.scalePivot' % joint, '%s.rotatePivot' % joint, a = True)
                        
    def _cleanup(self):
        cmds.delete([self.particles,self.source_mesh])
            
    def store_relative_scope(self, parent):    
        
        self.scope = cmds.listRelatives(parent, allDescendents = True, type = 'transform')
        self.scope.append(parent)
        
    def set_scope(self, scope):
        self.scope = scope
            
    def set_source_mesh(self, name):
        self.source_mesh = name
        
    def set_target_mesh(self, name):
        self.target_mesh = name
        
    def run(self):
        if not self.scope:
            return
        
        if not cmds.objExists(self.source_mesh):
            return
    
        if not cmds.objExists(self.target_mesh):
            return
            
        self.source_mesh = cmds.duplicate(self.source_mesh)[0]
        self._match_particles(self.scope)
        self._wrap_particles()
        self._blend_to_target()
        self._move_to_target()
        self._cleanup()

class Connections(object):
    
    def __init__(self, node):
        
        self.node = node
        
        self.inputs = []
        self.outputs = []
        self.input_count = 0
        self.output_count = 0
        
        self._store_connections()
        
    def _get_outputs(self):
        outputs = cmds.listConnections(self.node, 
                            connections = True, 
                            destination = True, 
                            source = False,
                            plugs = True,
                            skipConversionNodes = True)  
        
        if outputs: 
            return outputs
        
        if not outputs:
            return []
    
        
    def _get_inputs(self):
        inputs = cmds.listConnections(self.node,
                             connections = True,
                             destination = False,
                             source = True,
                             plugs = True,
                             skipConversionNodes = True)
        
        if inputs:
            inputs.reverse()
            
            return inputs
        
        if not inputs:
            return []
        
    def _store_output_connections(self, outputs):
        
        #stores [source connection, destination_node, destination_node_attribute]

        output_values = []
        
        for inc in range(0, len(outputs), 2):
            split = outputs[inc].split('.')
            
            output_attribute = string.join(split[1:], '.')
            
            split_input = outputs[inc+1].split('.')
            
            node = split_input[0]
            node_attribute = string.join(split_input[1:], '.')
            
            output_values.append([output_attribute, node, node_attribute])
            
        self.outputs = output_values
        
    def _store_input_connections(self, inputs):
        
        #stores [source connection, destination_node, destination_node_attribute]
        
        input_values = []
        
        for inc in range(0, len(inputs), 2):
            split = inputs[inc+1].split('.')
            
            input_attribute = string.join(split[1:], '.')
            
            split_input = inputs[inc].split('.')
            
            node = split_input[0]
            node_attribute = string.join(split_input[1:], '.')
            
            input_values.append([input_attribute, node, node_attribute])
            
        self.inputs = input_values
        
    def _store_connections(self):
        
        self.inputs = []
        self.outputs = []
        
        inputs = self._get_inputs()
        outputs = self._get_outputs()
        
        if inputs:
            self._store_input_connections(inputs)
        if outputs:
            self._store_output_connections(outputs)
        
        
        
        self.connections = inputs + outputs
        
        self.input_count = self._get_input_count()
        self.output_count = self._get_output_count()
        
    def _get_in_source(self, inc):
        return '%s.%s' % (self.node, self.inputs[inc][0])
    
    def _get_in_target(self, inc):
        return '%s.%s' % (self.inputs[inc][1], self.inputs[inc][2])
    
    def _get_out_source(self, inc):
        return '%s.%s' % (self.outputs[inc][1], self.outputs[inc][2])
    
    def _get_out_target(self, inc):
        return'%s.%s' % (self.node, self.outputs[inc][0])
    
    def _get_input_count(self):
        return len(self.inputs)
    
    def _get_output_count(self):
        return len(self.outputs)
            
    def disconnect(self):
        
        for inc in range(0, len(self.connections), 2):
            if cmds.isConnected(self.connections[inc], self.connections[inc+1], ignoreUnitConversion = True):
                cmds.disconnectAttr(self.connections[inc], self.connections[inc+1])    
            
    
    def connect(self):
        for inc in range(0, len(self.connections), 2):
            if not cmds.isConnected(self.connections[inc], self.connections[inc+1], ignoreUnitConversion = True):
                cmds.connectAttr(self.connections[inc], self.connections[inc+1])
                
    def refresh(self):
        self._store_connections()
                
    def get(self):
        return self.connections
    
    def get_input_at_inc(self, inc):
        return self.inputs[inc]
    
    def get_output_at_inc(self, inc):
        return self.outputs[inc]
    
    def get_connection_inputs(self, connected_node):
        found = []
        
        for inc in range(0, len(self.inputs), 2):
            test = self.inputs[inc+1]
            
            node = test.split('.')[0]
            
            if node == connected_node:
                found.append(test)
                
        return found
    
    def get_connection_outputs(self, connected_node):
        found = []
        
        for inc in range(0, len(self.outputs), 2):
            
            test = self.outputs[inc]
            node = test.split('.')[0]
            
            if node == connected_node:
                found.append(test)
                
        return found        
    
    def get_inputs_of_type(self, node_type):
        found = []
        
        for inc in range(0, self.input_count):
            node = self.inputs[inc][1]
            
            if cmds.nodeType(node).startswith(node_type):
                found.append(node)
                
        return found
        
    def get_outputs_of_type(self, node_type):
        found = []
        
        for inc in range(0, self.output_count):
            node = self.outputs[inc][1]
            
            if cmds.nodeType(node).startswith(node_type):
                found.append(node)
                
        return found
    
    def get_outputs(self):
        return self._get_outputs()
        
    def get_inputs(self):
        return self._get_inputs()

class MoveConnectedNodes(object):
    def __init__(self, source_node, target_node):
        self.source_node = source_node
        self.target_node = target_node
        
        self.connections = Connections(source_node)
        
        self.node_type = 'transform'
        
    def set_type(self, node_type):
        self.node_type = node_type
        
    def move_outputs(self):
        
        for inc in range(0, self.connections.output_count):
            
            output = self.connections.get_output_at_inc(inc)
            
            if cmds.nodeType(output[1]).startswith(self.node_type):
                cmds.connectAttr('%s.%s' % (self.target_node, output[0]),
                                 '%s.%s' % (output[1], output[2]), f = True)
                cmds.disconnectAttr('%s.%s' % (self.source_node, output[0]),
                                 '%s.%s' % (output[1], output[2]))
        
            
    def move_inputs(self):
        
        for inc in range(0, self.connections.input_count):
            
            input_value = self.connections.get_input_at_inc(inc)
            
            if cmds.nodeType(input_value[1]).startswith(self.node_type):
                cmds.connectAttr('%s.%s' % (input_value[1], input_value[2]),
                                 '%s.%s' % (self.target_node, input_value[0]), f = True) 

                cmds.disconnectAttr('%s.%s' % (input_value[1], input_value[2]),
                                 '%s.%s' % (self.source_node, input_value[0]))
            
        

class MirrorControlKeyframes():
    def __init__(self, node):
        self.node = node
        
    def _get_output_keyframes(self):
        
        
        found = get_output_keyframes(self.node)
                
        return found
         
    def _map_connections(self, connections):
        new_connections = []
        
        if not connections:
            return new_connections
        
        for connection in connections:
            node, attribute = connection.split('.')
            
            new_node = node
            
            if node.endswith('_L'):
                new_node = node[:-2] + '_R' 
                
            if node.endswith('_R'):
                new_node = node[:-2] + '_L'  
               
            new_connections.append('%s.%s' % (new_node, attribute))
                
        return new_connections

                
    def mirror_outputs(self, fix_translates = False):
        
        found_keyframes = self._get_output_keyframes()
        
        for keyframe in found_keyframes:
            
            new_keyframe = cmds.duplicate(keyframe)[0]
        
            connections = Connections(keyframe)
            outputs = connections.get_outputs()
            inputs = connections.get_inputs()
            
            mapped_output = self._map_connections(outputs)
            mapped_input = self._map_connections(inputs)

            for inc in range(0, len(mapped_output), 2):
                
                output = mapped_output[inc]
                split_output = output.split('.')
                new_output = '%s.%s' % (new_keyframe, split_output[1])

                do_fix_translates = False

                if mapped_output[inc+1].find('.translate') > -1 and fix_translates:
                    do_fix_translates = True
                
                if not get_inputs(mapped_output[inc+1]):
                    
                    if not do_fix_translates:
                        cmds.connectAttr(new_output, mapped_output[inc+1])
                    if do_fix_translates:
                        connect_multiply(new_output, mapped_output[inc+1], -1)
                
            for inc in range(0, len(mapped_input), 2):
                
                input_connection = mapped_input[inc+1]
                split_input = input_connection.split('.')
                new_input = '%s.%s' % (new_keyframe, split_input[1])
                
                if not get_inputs(new_input):
                    cmds.connectAttr(mapped_input[inc], new_input)

                    
class StickyTransform(object):
    
    def __init__(self):
        
        self.transform = None
    
    def _create_locators(self):
        
        self.locator1 = cmds.spaceLocator(n = inc_name('locator_%s' % self.transform))[0]
        self.locator2 = cmds.spaceLocator(n = inc_name('locator_%s' % self.transform))[0]
        
        MatchSpace(self.transform, self.locator1).translation_rotation()
        MatchSpace(self.transform, self.locator2).translation_rotation()
        
    def _create_constraints(self):
        
        point_constraint = cmds.pointConstraint(self.locator1, self.locator2, self.transform)
        orient_constraint = cmds.orientConstraint(self.locator1, self.locator2, self.transform)
        
        const_edit = ConstraintEditor()
        const_edit.create_switch(self.transform, 'xformSwitch', point_constraint)
        const_edit.create_switch(self.transform, 'orientSwitch', orient_constraint)
    
    def set_transform(self, transform_name):
        
        self.transform = transform_name
        
    def create(self):
        
        self._create_locators()
        self._create_constraints()
        
class SuspensionRig(BufferRig):
    
    def __init__(self, description, side):
        
        self.sections = []
        self.scale_constrain = None
        
        super(SuspensionRig, self).__init__(description, side)
                    
    def _create_joint_section(self, top_joint, btm_joint):

        ik = IkHandle( self._get_name() )
        
        ik.set_start_joint(top_joint)
        ik.set_end_joint(btm_joint)
        ik.set_solver(ik.solver_sc)
        ik.create()
        
        handle = ik.ik_handle
        
        stretch = StretchyChain()
        stretch.set_simple(True)
        
        stretch.set_joints([top_joint, btm_joint])
        stretch.set_description(self._get_name())        
                
        top_locator, btm_locator = stretch.create()
        
        top_control = self._create_control('top')
        top_control.rotate_shape(0, 0, 90)
        xform_top_control = create_xform_group(top_control.get())
        MatchSpace(top_joint, xform_top_control).translation_rotation()
        
        btm_control = self._create_control('btm')
        btm_control.rotate_shape(0, 0, 90)
        xform_btm_control = create_xform_group(btm_control.get())
        MatchSpace(btm_joint, xform_btm_control).translation_rotation()
        
        
        cmds.parent(xform_top_control, xform_btm_control, self.control_group)
        cmds.parent(top_locator, top_control.get())
        cmds.parent(btm_locator, btm_control.get())
        
        cmds.pointConstraint(top_control.get(), top_joint)
        cmds.parent(handle, btm_control.get())
        
        cmds.hide(handle)
                    
    def create(self):
        
        super(SuspensionRig, self).create()
        
        self._create_joint_section(self.buffer_joints[0], self.buffer_joints[1])
       
        
                
#--- deformation


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

        alias_index_map = map_blend_target_alias_to_index(self.blendshape)
        
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
                        
        vertex_count = get_component_count(mesh)
        
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
        
        connection = get_attribute_input(target_attr)
        
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

    def create(self, mesh):
        
        self.blendshape = cmds.deformer(mesh, type = 'blendShape', foc = True)[0]
        self._store_targets()
        self._store_meshes()

    def is_target(self, name):
        if name in self.targets:
            return True
        
    def create_target(self, name, mesh):
        
        name = name.replace(' ', '_')
        
        if not self.is_target(name):
            
            current_index = self._get_next_index()
            
            self._store_target(name, current_index)
            
            mesh_input = self._get_mesh_input_for_target(name)
              
            
                        
            cmds.connectAttr( '%s.outMesh' % mesh, mesh_input)
            
            cmds.setAttr('%s.weight[%s]' % (self.blendshape, current_index), 1)
            cmds.aliasAttr(name, '%s.weight[%s]' % (self.blendshape, current_index))
            cmds.setAttr('%s.weight[%s]' % (self.blendshape, current_index), 0)
            
            attr = '%s.%s' % (self.blendshape, name)
            return attr
            
        if self.is_target(name):            
            warning('Could not add target %s, it already exist.' % name)
       
    def replace_target(self, name, mesh):
        
        name = name.replace(' ', '_')
        
        if self.is_target(name):
            
            mesh_input = self._get_mesh_input_for_target(name)
            
            if not cmds.isConnected('%s.outMesh' % mesh, mesh_input):
                cmds.connectAttr('%s.outMesh' % mesh, mesh_input)
                cmds.disconnectAttr('%s.outMesh' % mesh, mesh_input)
                
        if not self.is_target(name):
            warning('Could not replace target %s, it does not exist' % name)
        
    def remove_target(self, name):
        target_group = self._get_input_target_group(name)
        weight_attr = self._get_weight(name)
        
        cmds.removeMultiInstance(target_group, b = True)
        cmds.removeMultiInstance(weight_attr, b = True)
        
        self.weight_indices.remove( self.targets[name].index )
        self.targets.pop(name)
        
        cmds.aliasAttr('%s.%s' % (self.blendshape, name), rm = True)
       
    def rename_target(self, old_name, new_name):
        
        old_name = old_name.replace(' ', '_')
        new_name = new_name.replace(' ', '_')
        
        weight_attr = self._get_weight(old_name)
        index = self.targets[old_name].index
        
        
        cmds.aliasAttr('%s.%s' % (self.blendshape, old_name), rm = True)
        cmds.aliasAttr(new_name, weight_attr)
        
        self.targets.pop(old_name)
        self._store_target(new_name, index)
        
    def set_weight(self, name, value):
        if self.is_target(name):
            
            attribute_name = self._get_target_attr(name)
            
            if not cmds.getAttr(attribute_name, l = True):
                cmds.setAttr(attribute_name, value)
    
    def set_weights(self, weights, target_name = None, mesh_index = 0):
        
        mesh = self.meshes[mesh_index]
        
        vertex_count  = get_component_count(mesh)
        
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
    
    def set_envelope(self, value):
        cmds.setAttr('%s.envelope' % self.blendshape, value)
        
    def recreate_target(self, name, value = 1.0, mesh = None):
        if not self.is_target(name):
            return
        
        new_name = inc_name(name)
        
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
            new_name = inc_name(target)
            
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
        
    def set(self, blendshape_name):
        self.blendshape = blendshape_name
        self._store_targets()
        self._store_meshes()
    
class BlendShapeTarget(object):
    def __init__(self, name, index):
        self.name = name
        self.index = index
        self.connection = None
        self.value = 0

class SplitMeshTarget(object):
    
    def __init__(self, target_mesh):
        self.target_mesh = target_mesh
        self.weighted_mesh = None
        self.base_mesh = None
        self.split_parts = []
    
    def set_weight_joint(self, joint, suffix):
        self.split_parts.append([joint, suffix])
    
    def set_weighted_mesh(self, weighted_mesh):
        self.weighted_mesh = weighted_mesh
    
    def set_base_mesh(self, base_mesh):
        self.base_mesh = base_mesh
    
    def create(self):
        
        if not self.weighted_mesh and self.base_mesh:
            return
        
        skin_cluster = find_deformer_by_type(self.weighted_mesh, 'skinCluster')
        
        if not skin_cluster:
            return
        
        skin_weights = get_skin_weights(skin_cluster)

        parent = cmds.listRelatives( self.target_mesh, p = True )
        if parent:
            parent = parent[0]

        targets = []
        
        for part in self.split_parts:
            joint = part[0]
            suffix = part[1]
            
            new_target = cmds.duplicate(self.base_mesh)
            
            split_name = self.target_mesh.split('_')
            
            target_name = self.target_mesh
            
            if self.target_mesh.endswith('N'):
                target_name = self.target_mesh[:-1]
                
            new_name = '%s%s' % (target_name, suffix)
            
            if self.target_mesh.endswith('N'):
                new_name += 'N'
            
            if len(split_name) > 1:
                new_names = []
                
                for name in split_name:
                    
                    sub_name = name
                    if name.endswith('N'):
                        sub_name = name[:-1]
                    sub_new_name = '%s%s' % (sub_name, suffix)
                    
                    if name.endswith('N'):
                        sub_new_name += 'N'
                        
                    new_names.append(sub_new_name)
                    
                new_name = string.join(new_names, '_')
                    
            new_target = cmds.rename(new_target, new_name)    
            
            blendshape = cmds.blendShape(self.target_mesh, new_target, w = [0,1])[0]
            
            target_index = get_index_at_skin_influence(joint, skin_cluster)
            
            weights = skin_weights[target_index]
            
            blend = BlendShape(blendshape)
            blend.set_weights(weights, self.target_mesh)
            
            cmds.delete(new_target, ch = True)
            
            if parent:
                cmds.parent(new_target, parent)
            targets.append(new_target)
          
        return targets
            
            
class TransferWeight(object):
    def __init__(self, mesh):
        self.mesh = mesh

        self.vertices = []
        
        if type(mesh) == str or type(mesh) == unicode:        
            self.vertices = cmds.ls('%s.vtx[*]' % self.mesh, flatten = True)
        
        if type(mesh) == list:
            self.vertices = mesh
            print mesh
            self.mesh = mesh[0].split('.')[0]

        print self.vertices
        print self.mesh

        skin_deformer = self._get_skin_cluster(self.mesh)
        
        print skin_deformer
        
        self.skin_cluster= None
        
        if skin_deformer:
            self.skin_cluster = skin_deformer
        
        
        print self.skin_cluster
        
    def _get_skin_cluster(self, mesh):
        
        skin_deformer = find_deformer_by_type(mesh, 'skinCluster')
        
        return skin_deformer

    def _add_joints_to_skin(self, joints):
        
        influences = get_influences_on_skin(self.skin_cluster)
        
        for joint in joints:
            if not joint in influences:
                cmds.skinCluster(self.skin_cluster, e = True, ai = joint, wt = 0.0, nw = 1)
        
    def transfer_joint_to_joint(self, source_joints, destination_joints, source_mesh = None, percent =1):
        
        cmds.undoInfo(state = False)
        
        source_skin_cluster = self._get_skin_cluster(source_mesh)
        source_value_map = get_skin_weights(source_skin_cluster)
        destination_value_map = get_skin_weights(self.skin_cluster)
        
        joint_map = {}
        destination_joint_map = {}
        
        for joint in source_joints:
            index = get_index_at_skin_influence(joint,source_skin_cluster)
            joint_map[index] = joint
            
        for joint in destination_joints:
            index = get_index_at_skin_influence(joint,self.skin_cluster)
            destination_joint_map[index] = joint
            
        
        verts = self.vertices
                            
        weighted_verts = []
        
        
        for influence_index in joint_map:
            
            if not influence_index:
                continue
            
            for vert_index in range(0, len(verts)):
                
                int_vert_index = int(vtool.util.get_last_number(verts[vert_index]))
                
                value = source_value_map[influence_index][int_vert_index]
                
                if value > 0.001:
                    weighted_verts.append(int_vert_index)
        
        self._add_joints_to_skin(source_joints)
        
        lock_joints(self.skin_cluster, destination_joints)
        
        vert_count = len(weighted_verts)
        
        bar = ProgressBar('transfer weight', vert_count)
        
        inc = 1
        
        for vert_index in weighted_verts:
            vert_name = '%s.vtx[%s]' % (self.mesh, vert_index)
        
            destination_value = 0
        
            for influence_index in destination_joint_map:
                destination_value += destination_value_map[influence_index][vert_index]
            
            segments = []
            
            for influence_index in joint_map:
                
                if not influence_index:
                    continue
                
                joint = joint_map[influence_index]
                value = source_value_map[influence_index][vert_index]
                value *= destination_value
                value *= percent
                
                segments.append((joint, value))
                
            cmds.skinPercent(self.skin_cluster, vert_name, r = False, transformValue = segments)

            bar.inc()
            
            bar.status('transfer weight: %s of %s' % (inc, vert_count))
            
            if bar.break_signaled():
                break
            
            inc += 1
            
        bar.end()
        
        cmds.undoInfo(state = True)
            
    def transfer_joints_to_new_joints(self, joints, new_joints, falloff = 1, power = 4, weight_percent_change = 1):
        
        cmds.undoInfo(state = False)
        
        if not self.skin_cluster or not self.mesh:
            print 'returning here at first catch'
            cmds.undoInfo(state = True)
            return
        
        lock_joints(self.skin_cluster, joints)
        
        self._add_joints_to_skin(new_joints)
        
        value_map = get_skin_weights(self.skin_cluster)
        influence_values = {}
        
        source_joint_weights = []
        
        for joint in joints:
            
            index = get_index_at_skin_influence(joint,self.skin_cluster)
            
            if index == None:
                continue
            
            if not value_map.has_key(index):
                continue
            
            influence_values[index] = value_map[index]
            source_joint_weights.append(value_map[index])
                
        print 'source joint weights', source_joint_weights
                
        if not source_joint_weights:
            cmds.undoInfo(state = True)
            return
            
        verts = self.vertices#cmds.ls('%s.vtx[*]' % self.vertices, flatten = True)
        
        weighted_verts = []
        weights = {}
        
        for influence_index in influence_values:
            
            for vert_index in range(0, len(verts)):
                
                int_vert_index = vtool.util.get_last_number(verts[vert_index])
                
                
                value = influence_values[influence_index][int_vert_index]
                
                
                
                if value > 0.001:
                    if not int_vert_index in weighted_verts:
                        weighted_verts.append(int_vert_index)
                    
                    if int_vert_index in weights:
                        weights[int_vert_index] += value
                        
                    if not int_vert_index in weights:
                        weights[int_vert_index] = value
        
        print 'weighted verts', weighted_verts
        
        if not weighted_verts:
            cmds.undoInfo(state = True)
            return
        
        bar = ProgressBar('transfer weight', len(weighted_verts))
        
        inc = 1
        
        new_joint_count = len(new_joints)
        joint_count = len(joints)
        
        for vert_index in weighted_verts:
            
            vert_name = '%s.vtx[%s]' % (self.mesh, vert_index)
            
            distances = get_distances(new_joints, vert_name)
            
            smallest_distance = distances[0]
            distances_in_range = []
            
            for joint_index in range(0, new_joint_count):
                if distances[joint_index] < smallest_distance:
                    smallest_distance = distances[joint_index]
            
            longest_distance = -1
            total_distance = 0.0
            
            distances_away = []
            
            for joint_index in range(0, new_joint_count):

                distance_away = distances[joint_index] - smallest_distance
                
                distances_away.append(distance_away)
                
                if distance_away > falloff:
                    continue
                
                distances_in_range.append(joint_index)
                
                if distances[joint_index] > longest_distance:
                    longest_distance = distances[joint_index]
                    
                total_distance += distance_away
                
                
            total = 0.0
            
            inverted_distances = {}
            
            for joint_index in distances_in_range:
                distance = distances_away[joint_index]
                
                distance_weight = distance/falloff
                    
                inverted_distance = 1 - distance_weight
                
                inverted_distance = inverted_distance**power
                
                inverted_distances[joint_index] = inverted_distance
                
                total += inverted_distance
            
            joint_weight = {}    
                
            for distance_inc in distances_in_range:
                weight = inverted_distances[distance_inc]/total
                joint_weight[new_joints[distance_inc]] = weight
            
            weight_value = weights[vert_index]
            
            segments = []
            
            for joint in joint_weight:
                
                joint_value = joint_weight[joint]
                value = weight_value*joint_value
                
                segments.append( (joint, value * weight_percent_change) )
                
            for joint_index in range(0, joint_count):
                change = 1 - weight_percent_change
                
                value = source_joint_weights[joint_index]
                
                value = value[vert_index] * change
                
                segments.append((joints[joint_index], value ))
            
            cmds.skinPercent(self.skin_cluster, vert_name, r = False, transformValue = segments)
            
            bar.inc()
            
            bar.status('transfer weight: %s of %s' % (inc, len(weighted_verts)))
            
            if bar.break_signaled():
                break
            
            inc += 1
            
            
        bar.end()
        
        cmds.undoInfo(state = True)
        
    """
    def transfer_joints_into_joint(self, joints, joint, source_mesh):
        
        value_map = get_skin_weights(self.skin_cluster)
        influence_values = {}

        source_joint_weights = []

        for joint in joints:
            
            index = get_index_at_skin_influence(joint,self.skin_cluster)
            
            if index == None:
                continue
            
            if not value_map.has_key(index):
                continue
            
            influence_values[index] = value_map[index]
            source_joint_weights.append( value_map[index] )
            
        if not source_joint_weights:
            cmds.undoInfo(state = True)
            return
    """ 
        
                
        
class MayaWrap(object):
    
    def __init__(self, mesh):
        
        self.mesh = mesh
        self.meshes = []
        self.driver_meshes = []
        self.wrap = ''
        self.base_meshes = []
        self.base_parent = None
        
        self._set_mesh_to_wrap(mesh, 'mesh')
        self._set_mesh_to_wrap(mesh, 'lattice')
        self._set_mesh_to_wrap(mesh, 'nurbsCurve')
        self._set_mesh_to_wrap(mesh, 'nurbsSurface')
    
    def _create_wrap(self):
        
        self.wrap = cmds.deformer(self.mesh, type = 'wrap', n = 'wrap_%s' % self.mesh)[0]
        cmds.setAttr('%s.exclusiveBind' % self.wrap, 1)
        return self.wrap                 
    
    def _add_driver_meshes(self):
        inc = 0
        
        
        
        for mesh in self.driver_meshes:
            self._connect_driver_mesh(mesh, inc)
            inc+=1
        
    def _connect_driver_mesh(self, mesh, inc):
        
        
        base = cmds.duplicate(mesh, n = 'wrapBase_%s' % mesh)[0]
        
        if self.base_parent:
            cmds.parent(base, self.base_parent)
        
        self.base_meshes.append(base)
        cmds.hide(base)
        
        cmds.connectAttr( '%s.worldMesh' % mesh, '%s.driverPoints[%s]' % (self.wrap, inc) )
        cmds.connectAttr( '%s.worldMesh' % base, '%s.basePoints[%s]' % (self.wrap, inc) )
        
        if not cmds.objExists('%s.dropoff' % mesh):
            cmds.addAttr(mesh, at = 'short', sn = 'dr', ln = 'dropoff', dv = 10, min = 1, k = True)
            
        if not cmds.objExists('%s.inflType' % mesh):
            cmds.addAttr(mesh, at = 'short', sn = 'ift', ln = 'inflType', dv = 2, min = 1, max = 2, k = True )
            
        if not cmds.objExists('%s.smoothness' % mesh):    
            cmds.addAttr(mesh, at = 'short', sn = 'smt', ln = 'smoothness', dv = 0.0, min = 0.0, k = True)
            
        #cmds.addAttr(mesh, at = 'short', sn = 'wsm', ln = 'wrapSamples', dv = 10, min = 1)
        
        cmds.connectAttr('%s.dropoff' % mesh, '%s.dropoff[%s]' % (self.wrap, inc) )
        cmds.connectAttr('%s.inflType' % mesh, '%s.inflType[%s]' % (self.wrap, inc) )
        cmds.connectAttr('%s.smoothness' % mesh, '%s.smoothness[%s]' % (self.wrap, inc) )
        
        if not cmds.isConnected('%s.worldMatrix' % self.mesh, '%s.geomMatrix' % (self.wrap)):
            cmds.connectAttr('%s.worldMatrix' % self.mesh, '%s.geomMatrix' % (self.wrap))
                        
    def _set_mesh_to_wrap(self, mesh, geo_type = 'mesh'):
        
        shapes = cmds.listRelatives(mesh, s = True)
        
        if shapes and cmds.nodeType(shapes[0]) == geo_type:
            self.meshes.append(mesh)
                
        relatives = cmds.listRelatives(mesh, ad = True)
                    
        for relative in relatives:
            shapes = cmds.listRelatives(relative, s = True)
            
            if shapes and cmds.nodeType(shapes[0]) == geo_type:
                self.meshes.append(relative)

                
    def set_driver_meshes(self, meshes = []):
        if meshes:
            
            meshes = vtool.util.convert_to_sequence(meshes)
            
            self.driver_meshes = meshes
    
    def set_base_parent(self, name):
        self.base_parent = name
    
    def create(self):
        
        if not self.meshes:
            
            return
        
        wraps = []
        
        for mesh in self.meshes:
            self.mesh = mesh
            
            wrap = self._create_wrap()
                        
            wraps.append(wrap)
            
            self._add_driver_meshes()

                
        if len(self.driver_meshes) > 1:
            cmds.setAttr('%s.exclusiveBind' % self.wrap, 0)

        return wraps

        
class PoseManager(object):
    def __init__(self):
        self.poses = []
        
        self.pose_group = 'pose_gr'

        if not cmds.objExists(self.pose_group):
            
            selection = cmds.ls(sl = True)
            
            self.pose_group = cmds.group(em = True, n = self.pose_group)
        
            data = StoreControlData(self.pose_group)
            data.set_data()
            
            if selection:
                cmds.select(selection)

        
    def get_poses(self):
        relatives = cmds.listRelatives(self.pose_group)
        
        if not relatives:
            return
        
        poses = []
        
        for relative in relatives:
            if self.is_pose(relative):
                poses.append(relative)
                
        return poses
    
    def is_pose(self, name):
        if PoseControl().is_a_pose(name):
            return True
        
        return False
    
    def get_transform(self, name):
        pose = PoseControl()
        pose.set_pose(name)
        transform = pose.get_transform()
        
        return transform
        
    def get_pose_control(self, name):
        
        pose = PoseControl()
        pose.set_pose(name)
        
        control = pose.pose_control
        
        return control
    
    def get_mesh_index(self, name, mesh):
        pose = PoseControl()
        pose.set_pose(name)
        
        mesh_index = pose.get_target_mesh_index(mesh)
        
        if mesh_index != None:
            
            return mesh_index
    
    def set_default_pose(self):
        store = StoreControlData(self.pose_group)
        store.set_data()
        
    def set_pose_to_default(self):
        store = StoreControlData(self.pose_group)
        store.eval_data()
    
    def set_pose(self, pose):
        store = StoreControlData(pose)
        store.eval_data()
        
    def set_poses(self, pose_list):
        
        data_list = []
        
        for pose_name in pose_list:
            
            store = StoreControlData(pose_name)

            data_list.append( store.eval_data(True) )
            
        store = StoreControlData().eval_multi_transform_data(data_list)
    
    def create_pose(self, name = None):
        selection = cmds.ls(sl = True, l = True)
        
        if not selection:
            return
        
        if not cmds.nodeType(selection[0]) == 'joint' or not len(selection):
            return
        
        if not name:
            joint = selection[0].split('|')
            joint = joint[-1]
            
            name = 'pose_%s' % joint
        
        pose = PoseControl(selection[0], name)
        pose_control = pose.create()
        
        self.pose_control = pose_control
        
        return pose_control
    
    def reset_pose(self, pose_name):
        
        pose = PoseControl()
        pose.set_pose(pose_name)
        pose.reset_target_meshes()
    
    def rename_pose(self, pose_name, new_name):
        pose = BasePoseControl()
        pose.set_pose(pose_name)
        return pose.rename(new_name)
    
    def create_combo(self, pose_list, name):
        
        combo = ComboControl(pose_list, name)
        combo.create()
    
    def add_mesh_to_pose(self, pose_name, meshes = None):

        selection = None

        if not meshes == None:
            selection = cmds.ls(sl = True, l = True)
        if meshes:
            selection = meshes
        
        
        
        #added = False
        
        pose = PoseControl()
        pose.set_pose(pose_name)

        if selection:
            for sel in selection:
                
                skin = find_deformer_by_type(sel, 'skinCluster')
                
                shape = get_mesh_shape(sel)
                
                if shape and skin:
                    pose.add_mesh(sel)
                    return True
                    
                if not shape and not skin:
                    return False
        
        if not selection:
            return False
    
    def visibility_off(self, pose_name):
        pose = PoseControl()
        pose.set_pose(pose_name)
        pose.visibility_off(view_only = True)
        
    def toggle_visibility(self, pose_name, view_only = False, mesh_index = 0):
        pose = PoseControl()
        
        pose.set_pose(pose_name)
        pose.set_mesh_index(mesh_index)
        pose.toggle_vis(view_only)
    
    def delete_pose(self, name):
        pose = PoseControl()
        pose.set_pose(name)
        pose.delete()
        
    def detach_poses(self):
        poses = self.get_poses()
        for pose_name in poses:
            
            pose = PoseControl()
            pose.set_pose(pose_name)
            pose.detach()
            
            
    def attach_poses(self):
        poses = self.get_poses()
        
        for pose_name in poses:
            
            pose = PoseControl()
            pose.set_pose(pose_name)
            pose.attach()
            
            
            
    def create_pose_blends(self):
        
        
        
        poses = self.get_poses()
        count = len(poses)

        progress = ProgressBar('adding poses ... ', count)
    
        for inc in range(count) :
            cmds.undoInfo(openChunk = True)
            #cmds.undoInfo(state = False)
            try:
                if progress.break_signaled():
                    break
                
                pose_name = poses[inc]
                pose = PoseControl()
                pose.set_pose(pose_name)
                pose.create_all_blends()
                
                cmds.refresh()
                
                progress.inc()
                progress.status('adding pose %s' % pose_name)
            except Exception:
                RuntimeError( traceback.format_exc() )
                
            
            #cmds.undoInfo(state = True)
            cmds.undoInfo(closeChunk = True)
            
        progress.end()
    
    def mirror_pose(self, name):
        pose = PoseControl()
        pose.set_pose(name)
        mirror = pose.mirror()
        
        return mirror        
        
        

class BasePoseControl(object):
    def __init__(self, description = 'pose'):
        
        self.pose_control = None

        if description:
            description = description.replace(' ', '_')
        
        
        self.description = description
        

        
        
        self.scale = 1
        self.mesh_index = 0
        
    def _refresh_meshes(self):
        

        meshes = self._get_corrective_meshes()
        
        for mesh in meshes:
            target_mesh = self._get_mesh_target(mesh)
            cmds.setAttr('%s.inheritsTransform' % mesh, 0)
            
            const = cmds.parentConstraint(target_mesh, mesh)
            
            cmds.delete(const)
               
            
            
        
    def _refresh_pose_control(self):
        shapes = cmds.listRelatives(self.pose_control, s = True)
        cmds.showHidden( shapes )
        
        if not cmds.objExists('%s.enable' % self.pose_control):
            cmds.addAttr(self.pose_control, ln = 'enable', at = 'double', k = True, dv = 1, min = 0, max = 1)
            multiply = self._get_named_message_attribute('multiplyDivide2')
            
            multiply_offset = self._create_node('multiplyDivide')
        
            cmds.connectAttr('%s.outputX' % multiply, '%s.input1X' % multiply_offset)
            cmds.connectAttr('%s.enable' % self.pose_control, '%s.input2X' % multiply_offset)
        
            cmds.disconnectAttr('%s.outputX' % multiply, '%s.weight' % self.pose_control)
            cmds.connectAttr('%s.outputX' % multiply_offset, '%s.weight' % self.pose_control)
        
    def _create_top_group(self):
        top_group = 'pose_gr'
        
        if not cmds.objExists(top_group):
            top_group = cmds.group(em = True, name = top_group)
            #cmds.parent( top_group, 'setup' )

        return top_group

    def _get_name(self):
        return inc_name(self.description) 
    
    def _set_description(self, description):
        cmds.setAttr('%s.description' % self.pose_control, description, type = 'string' )
        self.description = description

    def _rename_nodes(self):
        
        nodes = self._get_connected_nodes()
        
        for node in nodes:
            node_type = cmds.nodeType(node)
            
            if node_type == 'transform':
                shape = get_mesh_shape(node)
                
                if shape:
                    node_type = cmds.nodeType(shape)
            
            cmds.rename(node, inc_name('%s_%s' % (node_type, self.description)))

    def _create_node(self, maya_node_type):
        node = cmds.createNode(maya_node_type, n = inc_name('%s_%s' % (maya_node_type, self.description)))
        
        messages = self._get_message_attributes()
        
        found = []
        
        for message in messages:
            if message.startswith(maya_node_type):
                found.append(message)
                
        inc = len(found) + 1
        
        self._connect_node(node, maya_node_type, inc)
        
        return node
        
    def _connect_node(self, node, maya_node_type, inc = 1):
        attribute = '%s%s' % (maya_node_type, inc)
        
        cmds.addAttr(self.pose_control, ln = attribute, at = 'message' )
        cmds.connectAttr('%s.message' % node, '%s.%s' % (self.pose_control, attribute))
    
    def _connect_mesh(self, mesh):
        messages = self._get_mesh_message_attributes()
        
        inc = len(messages) + 1
        
        self._connect_node(mesh, 'mesh', inc)

    def _get_named_message_attribute(self, name):
        
        node = get_attribute_input('%s.%s' % (self.pose_control, name), True)
        
        return node
        
    def _get_mesh_message_attributes(self):
        
        attributes = cmds.listAttr(self.pose_control, ud = True)
        
        messages = []
        
        for attribute in attributes:
            if attribute.startswith('mesh'):
                node_and_attribute = '%s.%s' % (self.pose_control, attribute)
            
                if cmds.getAttr(node_and_attribute, type = True) == 'message':
                    messages.append(attribute)
                
        return messages
        
    def _get_mesh_count(self):
        attrs = self._get_mesh_message_attributes()
        
        return len(attrs)
        
    def _get_corrective_meshes(self):
        
        found = []
        
        for inc in range(0, self._get_mesh_count()):
            mesh = self.get_mesh(inc)
            found.append(mesh)
            
        return found
        
        
    def _check_if_mesh_connected(self, name):
        
        for inc in range(0, self._get_mesh_count()):
            
            mesh = self.get_mesh(inc)
            
            target = self._get_mesh_target(mesh)
            if target == name:
                return True
        
        return False
    
    def _check_if_mesh_is_child(self, mesh):
        children = cmds.listRelatives(self.pose_control, f = True)
        
        for child in children:
            if child == mesh:
                return True
            
        return False
    
    def _hide_meshes(self):
        children = cmds.listRelatives(self.pose_control, f = True, type = 'transform')
        cmds.hide(children)
        
    def _get_mesh_target(self, mesh):
        return cmds.getAttr('%s.mesh_pose_source' % mesh)
        
    def _get_message_attributes(self):
        
        attributes = cmds.listAttr(self.pose_control, ud = True)
        
        messages = []
        
        for attribute in attributes:
            node_and_attribute = '%s.%s' % (self.pose_control, attribute)
            
            if cmds.getAttr(node_and_attribute, type = True) == 'message':
                messages.append(attribute)
                
        return messages
    
    def _get_connected_nodes(self):
        
        attributes = self._get_message_attributes()
        
        nodes = []
        
        for attribute in attributes:
            connected = get_attribute_input('%s.%s' % (self.pose_control, attribute), node_only = True)
            
            if connected:
                nodes.append(connected)
                
        return nodes

    def _create_attributes(self, control):
        cmds.addAttr(control, ln = 'description', dt = 'string')
        cmds.setAttr('%s.description' % control, self.description, type = 'string')
        
        cmds.addAttr(control, ln = 'control_scale', at = 'float', dv = 1)
        
        
        title = MayaEnumVariable('POSE')
        title.create(control)  
        
        cmds.addAttr(control, ln = 'enable', at = 'double', k = True, dv = 1, min = 0, max = 1)
        cmds.addAttr(control, ln = 'weight', at = 'double', k = True, dv = 0)
        
        cmds.addAttr(control, ln = 'meshIndex', at = 'short', dv = self.mesh_index)
        cmds.setAttr('%s.meshIndex' % self.pose_control, l = True)


    def _create_pose_control(self):
        
        control = Control(self._get_name())
        control.set_curve_type('pin_point')
        
        control.hide_scale_and_visibility_attributes() 
        
        
        
        pose_control = control.get()
        self.pose_control = control.get()
        
        self._create_attributes(pose_control)
        
        return pose_control
    
    def _delete_connected_nodes(self):
        nodes = self._get_connected_nodes()
        if nodes:
            cmds.delete(nodes)

    def _create_shader(self, mesh):
        shader_name = 'pose_blinn'
            
        shader_name = apply_new_shader(mesh, type_of_shader = 'blinn', name = shader_name)
            
        cmds.setAttr('%s.color' % shader_name, 0.4, 0.6, 0.4, type = 'double3' )
        cmds.setAttr('%s.specularColor' % shader_name, 0.3, 0.3, 0.3, type = 'double3' )
        cmds.setAttr('%s.eccentricity' % shader_name, .3 )

    def _get_blendshape(self, mesh):
        #mesh = self.get_mesh(self.mesh_index)
        #target_mesh = self.get_target_mesh(mesh)
        
        
        
        """
        outputs = get_attribute_outputs('%s.weight' % self.pose_control)
        
        if outputs:
            for output in outputs:
                if cmds.nodeType(output) == 'blendShape':
                    split_output = output.split('.')
                    
                    return split_output[0]
        
        if not outputs:
        """
        return find_deformer_by_type(mesh, 'blendShape')

    def _get_current_mesh(self, mesh_index):
        mesh = None
        
        if mesh_index == None:
            mesh = self.get_mesh(self.mesh_index)
        if mesh_index != None:
            mesh = self.get_mesh(mesh_index)
            
        if not mesh:
            return
        
        return mesh

    def set_pose(self, pose_name):
        
        if not cmds.objExists('%s.description' % pose_name):
            return
        
        self.description = cmds.getAttr('%s.description' % pose_name)
        self.mesh_index = cmds.getAttr('%s.meshIndex' % pose_name)
        
        self.pose_control = pose_name
        
        self._refresh_pose_control()
        self._refresh_meshes()

    def goto_pose(self):
        store = StoreControlData(self.pose_control)
        store.eval_data()
        
    def set_mesh_index(self, index):
        mesh_count = self._get_mesh_count()
        
        if index > mesh_count-1:
            index = 0
            
        cmds.setAttr('%s.meshIndex' % self.pose_control, l = False)
        self.mesh_index = index
        cmds.setAttr('%s.meshIndex' % self.pose_control, index)
        cmds.setAttr('%s.meshIndex' % self.pose_control, l = True)
        
    def add_mesh(self, mesh, toggle_vis = True):
        
        if mesh.find('.vtx'):
            mesh = mesh.split('.')[0]
            
        if not get_mesh_shape(mesh):
            return False
        
        if self._check_if_mesh_connected(mesh):
            return False
        
        if self._check_if_mesh_is_child(mesh):
            return False
        
        pose_mesh = cmds.duplicate(mesh, n = inc_name('mesh_%s_1' % self.pose_control))[0]
        
        self._create_shader(pose_mesh)
        
        unlock_attributes(pose_mesh)
        
        cmds.parent(pose_mesh, self.pose_control)
        
        self._connect_mesh(pose_mesh)
        
        index = self._get_mesh_count()
        
        self.set_mesh_index(index-1)
        
        string_var = MayaStringVariable('mesh_pose_source')
        string_var.create(pose_mesh)
        string_var.set_value(mesh)

        self._hide_meshes()

        if toggle_vis:
            self.toggle_vis()
        
        return pose_mesh
        
    def create_all_blends(self):
        count = self._get_mesh_count()
        
        pose = True
        
        for inc in range(0, count):
            
            if inc > 0:
                pose = False
                
            self.create_blend(goto_pose = pose, mesh_index = inc)
        
    def create_blend(self, goto_pose = True, mesh_index = None):
        
        mesh = self._get_current_mesh(mesh_index)
        
        if not mesh:
            return
            
        target_mesh = self.get_target_mesh(mesh)
        
        if not target_mesh:
            RuntimeError('Mesh index %s, has no target mesh' % mesh_index)
            return
        
        if goto_pose:
            self.goto_pose()
        
        blend = BlendShape()
        
        blendshape = self._get_blendshape(target_mesh)
        
        if blendshape:
            blend.set(blendshape)
        
        if not blendshape:
            blend.create(target_mesh)
        
        #blend.set_envelope(0)
        self.disconnect_blend()
        blend.set_weight(self.pose_control, 0)
        
        offset = chad_extract_shape(target_mesh, mesh)
        
        
        blend.set_weight(self.pose_control, 1)
        self.connect_blend()
        #blend.set_envelope(1)
        
        if blend.is_target(self.pose_control):
            blend.replace_target(self.pose_control, offset)
        
        if not blend.is_target(self.pose_control):
            blend.create_target(self.pose_control, offset)
            
        if not cmds.isConnected('%s.weight' % self.pose_control, '%s.%s' % (blend.blendshape, self.pose_control)):
            cmds.connectAttr('%s.weight' % self.pose_control, '%s.%s' % (blend.blendshape, self.pose_control))
        
        cmds.delete(offset)
        
    def connect_blend(self, mesh_index = None):
        mesh = None
        
        if mesh_index == None:
            mesh = self.get_mesh(self.mesh_index)
        if mesh_index != None:
            mesh = self.get_mesh(mesh_index)
            
        if not mesh:
            return
        
        blend = BlendShape()
        
        target_mesh = self.get_target_mesh(mesh)
        
        blendshape = self._get_blendshape(target_mesh)
        
        if blendshape:
            blend.set(blendshape)
                
        if blend.is_target(self.pose_control):
            if not cmds.isConnected('%s.weight' % self.pose_control, '%s.%s' % (blend.blendshape, self.pose_control)):
                cmds.connectAttr('%s.weight' % self.pose_control, '%s.%s' % (blend.blendshape, self.pose_control))
                
    def disconnect_blend(self, mesh_index = None):
        mesh = None
        
        if mesh_index == None:
            mesh = self.get_mesh(self.mesh_index)
        if mesh_index != None:
            mesh = self.get_mesh(mesh_index)
            
        if not mesh:
            return
        
        blend = BlendShape()
        
        target_mesh = self.get_target_mesh(mesh)
        
        blendshape = self._get_blendshape(target_mesh)
        
        if blendshape:
            blend.set(blendshape)
                
        if blend.is_target(self.pose_control):
            if cmds.isConnected('%s.weight' % self.pose_control, '%s.%s' % (blend.blendshape, self.pose_control)):
                cmds.disconnectAttr('%s.weight' % self.pose_control, '%s.%s' % (blend.blendshape, self.pose_control))
        
    def get_blendshape(self, mesh_index = None):
        
        mesh = None
        
        if mesh_index == None:
            mesh = self.get_mesh(self.mesh_index)
        if mesh_index != None:
            mesh = self.get_mesh(mesh_index)
            
        if not mesh:
            return
        
        target_mesh = self.get_target_mesh(mesh)
        
        blendshape = self._get_blendshape(target_mesh)
        
        return blendshape
        
        
        
    def visibility_off(self, mesh = None, view_only = False):
        
        if not mesh:
            mesh = self.get_mesh(self.mesh_index)
        
        self._create_shader(mesh)
        
        cmds.hide(mesh)

        cmds.showHidden(self.get_target_mesh(mesh))
    
        if not view_only:    
            self.create_blend()
            
        
    def visibility_on(self, mesh):
        if not mesh:
            mesh = self.get_mesh(self.mesh_index)
        
        self._create_shader(mesh)
        
        cmds.showHidden(mesh)
        cmds.hide(self.get_target_mesh(mesh))
            
    def toggle_vis(self, view_only = False):
        mesh = self.get_mesh(self.mesh_index)
        
        if cmds.getAttr('%s.visibility' % mesh) == 1:
            self.visibility_off(mesh, view_only)
            return
        
        if cmds.getAttr('%s.visibility' % mesh) == 0:
            self.visibility_on(mesh)
            return
        
    def get_mesh(self, index):
        
        mesh_attributes = self._get_mesh_message_attributes()
        
        if not mesh_attributes:
            return
        
        mesh = get_attribute_input('%s.%s' % (self.pose_control, mesh_attributes[index]), True)
        
        return mesh
    
    def get_target_meshes(self):
        meshes = []
        
        for inc in range(0, self._get_mesh_count()):
            mesh = self.get_mesh(inc)
            mesh = cmds.getAttr('%s.mesh_pose_source' % mesh)
            meshes.append(mesh)
            
        return meshes
        
    def get_target_mesh(self, mesh):
        if cmds.objExists('%s.mesh_pose_source' % mesh):
            return cmds.getAttr('%s.mesh_pose_source' % mesh)
        
    def get_target_mesh_index(self, mesh):
        
        meshes = self.get_target_meshes()
        
        inc = 0
        
        for target_mesh in meshes:
            if mesh == target_mesh:
                return inc
            
            inc += 1
        
    def reset_target_meshes(self):
        
        count = self._get_mesh_count()
        
        for inc in range(0, count):
            
            deformed_mesh = self.get_mesh(inc)
            original_mesh = self.get_target_mesh(deformed_mesh)
            
            blendshape = self._get_blendshape(original_mesh)
            
            blend = BlendShape()
                    
            if blendshape:
                blend.set(blendshape)
                
            blend.set_envelope(0)    
            
            cmds.connectAttr('%s.outMesh' % original_mesh, '%s.inMesh' % deformed_mesh)
            cmds.refresh()
            cmds.disconnectAttr('%s.outMesh' % original_mesh, '%s.inMesh' % deformed_mesh)
        
            blend.set_envelope(1)    
        
        
    def create(self):
        top_group = self._create_top_group()
        
        pose_control = self._create_pose_control()
        self.pose_control = pose_control
        
        cmds.parent(pose_control, top_group)
        
        store = StoreControlData(pose_control)
        store.set_data()
        
        
        
        return pose_control
        
    def rename(self, description):
        
        meshes = self.get_target_meshes()
        
        old_description = self.description
        
        for mesh in meshes:
            blendshape = self._get_blendshape(mesh)
            
            if blendshape:
                blend = BlendShape(blendshape)
                blend.rename_target(old_description, description)
        
        
        
        self._set_description(description)
        
        self._rename_nodes()
        
        self.pose_control = cmds.rename(self.pose_control, self._get_name())
           
        return self.pose_control
    
    def delete_blend_input(self):
        
        outputs = get_attribute_outputs('%s.weight' % self.pose_control)
        
        if outputs:
            for output in outputs:
                if cmds.nodeType(output) == 'blendShape':
                    split_output = output.split('.')
                    
                    blend = BlendShape(split_output[0])
                    
                    blend.remove_target(split_output[1])
                    
       
    def delete(self):
        
        self.delete_blend_input()
        
        self._delete_connected_nodes()
            
        cmds.delete(self.pose_control)
    
    def select(self):
        cmds.select(self.pose_control)
        
        store = StoreControlData(self.pose_control)
        store.eval_data()
        
    def is_a_pose(self, node):
        if cmds.objExists('%s.POSE' % node ):
            return True
        
        return False
    
    def has_a_mesh(self):
        if self._get_mesh_message_attributes():
            return True
        
        return False

    

      
class PoseControl(BasePoseControl):
    def __init__(self, transform = None, description = 'pose'):
        
        
        
        super(PoseControl, self).__init__(description)
        
        if transform:
            transform = transform.replace(' ', '_')
            
        
        
        self.transform = transform
        
        self.axis = 'X'
    
    def _get_color_for_axis(self):
        if self.axis == 'X':
            return 13
            
        if self.axis == 'Y':
            return 14    
            
        if self.axis == 'Z':
            return 6
    
    def _get_axis_rotation(self):
        if self.axis == 'X':
            return [0,0,-90]
        
        if self.axis == 'Y':
            return [0,0,0]
        
        if self.axis == 'Z':
            return [90,0,0]
          
    def _get_twist_axis(self):
        if self.axis == 'X':
            return [0,1,0]
        
        if self.axis == 'Y':
            return [1,0,0]
        
        if self.axis == 'Z':
            return [1,0,0]
        
    def _get_pose_axis(self):
        if self.axis == 'X':
            return [1,0,0]
        
        if self.axis == 'Y':
            return [0,1,0]
        
        if self.axis == 'Z':
            return [0,0,1]
        
    def _create_pose_control(self):
        pose_control = super(PoseControl, self)._create_pose_control()
         
        self._position_control(pose_control)
        
            
        match = MatchSpace(self.transform, pose_control)
        match.translation_rotation()
        
        parent = cmds.listRelatives(self.transform, p = True)
        
        if parent:
            cmds.parentConstraint(parent[0], pose_control, mo = True)
            cmds.setAttr('%s.parent' % pose_control, parent[0], type = 'string')
        
        return pose_control
        
    def _position_control(self, control):
        control = Control(control)
        
        control.set_curve_type('pin_point')
        
        control.rotate_shape(*self._get_axis_rotation())
        
        scale = self.scale + 5
        control.scale_shape(scale,scale,scale)
        
        control.color( self._get_color_for_axis() )
        
        
    def _set_axis_vectors(self):
        pose_axis = self._get_pose_axis()
        
        self._lock_axis_vector_attributes(False)
        
        cmds.setAttr('%s.axisRotateX' % self.pose_control, pose_axis[0])
        cmds.setAttr('%s.axisRotateY' % self.pose_control, pose_axis[1])
        cmds.setAttr('%s.axisRotateZ' % self.pose_control, pose_axis[2])
        
        twist_axis = self._get_twist_axis()
        

        cmds.setAttr('%s.axisTwistX' % self.pose_control, twist_axis[0])
        cmds.setAttr('%s.axisTwistY' % self.pose_control, twist_axis[1])
        cmds.setAttr('%s.axisTwistZ' % self.pose_control, twist_axis[2])
        
        self._lock_axis_vector_attributes(True)
        

    def _lock_axis_vector_attributes(self, bool_value):
        axis = ['X','Y','Z']
        attributes = ['axisTwist', 'axisRotate']
        
        for a in axis:
            for attribute in attributes:
                cmds.setAttr('%s.%s%s' % (self.pose_control, attribute, a), l = bool_value)
        
        
        
    def _create_attributes(self, control):
        super(PoseControl, self)._create_attributes(control)
        
        
    
        cmds.addAttr(control, ln = 'translation', at = 'double', k = True, dv = 1)
        cmds.addAttr(control, ln = 'rotation', at = 'double', k = True, dv = 1)
        
        cmds.addAttr(control, ln = 'twistOffOn', at = 'double', k = True, dv = 1, min = 0, max = 1)
        cmds.addAttr(control, ln = 'maxDistance', at = 'double', k = True, dv = 1)
        cmds.addAttr(control, ln = 'maxAngle', at = 'double', k = True, dv = 90)
        cmds.addAttr(control, ln = 'maxTwist', at = 'double', k = True, dv = 90)
        
        title = MayaEnumVariable('AXIS_ROTATE')
        title.create(control)
        
        pose_axis = self._get_pose_axis()
        
        cmds.addAttr(control, ln = 'axisRotateX', at = 'double', k = True, dv = pose_axis[0])
        cmds.addAttr(control, ln = 'axisRotateY', at = 'double', k = True, dv = pose_axis[1])
        cmds.addAttr(control, ln = 'axisRotateZ', at = 'double', k = True, dv = pose_axis[2])
        
        title = MayaEnumVariable('AXIS_TWIST')
        title.create(control)
        
        twist_axis = self._get_twist_axis()
        
        cmds.addAttr(control, ln = 'axisTwistX', at = 'double', k = True, dv = twist_axis[0])
        cmds.addAttr(control, ln = 'axisTwistY', at = 'double', k = True, dv = twist_axis[1])
        cmds.addAttr(control, ln = 'axisTwistZ', at = 'double', k = True, dv = twist_axis[2])
        
        cmds.addAttr(control, ln = 'joint', dt = 'string')
        
        cmds.setAttr('%s.joint' % control, self.transform, type = 'string')
        
        cmds.addAttr(control, ln = 'parent', dt = 'string')
        
        
        self._lock_axis_vector_attributes(True)
         
    #--- math nodes 
        
    def _create_distance_between(self):
        distance_between = self._create_node('distanceBetween')
        
        cmds.connectAttr('%s.worldMatrix' % self.pose_control, 
                         '%s.inMatrix1' % distance_between)
            
        cmds.connectAttr('%s.worldMatrix' % self.transform, 
                         '%s.inMatrix2' % distance_between)
        
        return distance_between
        
        
    def _create_multiply_matrix(self, moving_transform, pose_control):
        multiply_matrix = self._create_node('multMatrix')
        
        cmds.connectAttr('%s.worldMatrix' % moving_transform, '%s.matrixIn[0]' % multiply_matrix)
        cmds.connectAttr('%s.worldInverseMatrix' % pose_control, '%s.matrixIn[1]' % multiply_matrix)
        
        return multiply_matrix
        
    def _create_vector_matrix(self, multiply_matrix, vector):
        vector_product = self._create_node('vectorProduct')
        
        cmds.connectAttr('%s.matrixSum' % multiply_matrix, '%s.matrix' % vector_product)
        cmds.setAttr('%s.input1X' % vector_product, vector[0])
        cmds.setAttr('%s.input1Y' % vector_product, vector[1])
        cmds.setAttr('%s.input1Z' % vector_product, vector[2])
        cmds.setAttr('%s.operation' % vector_product, 3)
        
        return vector_product
        
    def _create_angle_between(self, vector_product, vector):
        angle_between = self._create_node('angleBetween')
        
        cmds.connectAttr('%s.outputX' % vector_product, '%s.vector1X' % angle_between)
        cmds.connectAttr('%s.outputY' % vector_product, '%s.vector1Y' % angle_between)
        cmds.connectAttr('%s.outputZ' % vector_product, '%s.vector1Z' % angle_between)
        
        cmds.setAttr('%s.vector2X' % angle_between, vector[0])
        cmds.setAttr('%s.vector2Y' % angle_between, vector[1])
        cmds.setAttr('%s.vector2Z' % angle_between, vector[2])
        
        return angle_between
        
    def _remap_value_angle(self, angle_between):
        remap = self._create_node('remapValue')
        
        cmds.connectAttr('%s.angle' % angle_between, '%s.inputValue' % remap)
        
        cmds.setAttr('%s.value[0].value_Position' % remap, 0)
        cmds.setAttr('%s.value[0].value_FloatValue' % remap, 1)
        
        cmds.setAttr('%s.value[1].value_Position' % remap, 1)
        cmds.setAttr('%s.value[1].value_FloatValue' % remap, 0)
        
        cmds.setAttr('%s.inputMax' % remap, 180)
        
        return remap
    
    def _remap_value_distance(self, distance_between):
        remap = cmds.createNode('remapValue', n = 'remapValue_distance_%s' % self.description)
        
        cmds.connectAttr('%s.distance' % distance_between, '%s.inputValue' % remap)
        
        cmds.setAttr('%s.value[0].value_Position' % remap, 0)
        cmds.setAttr('%s.value[0].value_FloatValue' % remap, 1)
        
        cmds.setAttr('%s.value[1].value_Position' % remap, 1)
        cmds.setAttr('%s.value[1].value_FloatValue' % remap, 0)
        
        cmds.setAttr('%s.inputMax' % remap, 1)
        
        return remap        
        
    def _multiply_remaps(self, remap, remap_twist):
        
        multiply = self._create_node('multiplyDivide')
        
        cmds.connectAttr('%s.outValue' % remap, '%s.input1X' % multiply)
        cmds.connectAttr('%s.outValue' % remap_twist, '%s.input2X' % multiply)
        
        blend = self._create_node('blendColors')
        
        cmds.connectAttr('%s.outputX' % multiply, '%s.color1R' % blend)
        cmds.connectAttr('%s.outValue' % remap, '%s.color2R' % blend)
        
        
        cmds.connectAttr('%s.twistOffOn' % self.pose_control, ' %s.blender' % blend)
        
        return blend
    
    def _create_pose_math_nodes(self, multiply_matrix, axis):
        vector_product = self._create_vector_matrix(multiply_matrix, axis)
        angle_between = self._create_angle_between(vector_product, axis)
        
        if self._get_pose_axis() == axis:
            cmds.connectAttr('%s.axisRotateX' % self.pose_control, '%s.input1X' % vector_product)
            cmds.connectAttr('%s.axisRotateY' % self.pose_control, '%s.input1Y' % vector_product)
            cmds.connectAttr('%s.axisRotateZ' % self.pose_control, '%s.input1Z' % vector_product)
            
            cmds.connectAttr('%s.axisRotateX' % self.pose_control, '%s.vector2X' % angle_between)
            cmds.connectAttr('%s.axisRotateY' % self.pose_control, '%s.vector2Y' % angle_between)
            cmds.connectAttr('%s.axisRotateZ' % self.pose_control, '%s.vector2Z' % angle_between)
            
        if self._get_twist_axis() == axis:
            cmds.connectAttr('%s.axisTwistX' % self.pose_control, '%s.input1X' % vector_product)
            cmds.connectAttr('%s.axisTwistY' % self.pose_control, '%s.input1Y' % vector_product)
            cmds.connectAttr('%s.axisTwistZ' % self.pose_control, '%s.input1Z' % vector_product)
            
            cmds.connectAttr('%s.axisTwistX' % self.pose_control, '%s.vector2X' % angle_between)
            cmds.connectAttr('%s.axisTwistY' % self.pose_control, '%s.vector2Y' % angle_between)
            cmds.connectAttr('%s.axisTwistZ' % self.pose_control, '%s.vector2Z' % angle_between)            
        
        remap = self._remap_value_angle(angle_between)
        
        return remap
        
    def _create_pose_math(self, moving_transform, pose_control):
        multiply_matrix = self._create_multiply_matrix(moving_transform, pose_control)
        
        pose_axis = self._get_pose_axis()
        twist_axis = self._get_twist_axis()
        
        remap = self._create_pose_math_nodes(multiply_matrix, pose_axis)
        remap_twist = self._create_pose_math_nodes(multiply_matrix, twist_axis)
        
        blend = self._multiply_remaps(remap, remap_twist)
        
        cmds.connectAttr('%s.maxAngle' % pose_control, '%s.inputMax' % remap)
        cmds.connectAttr('%s.maxTwist' % pose_control, '%s.inputMax' % remap_twist)
        
        distance = self._create_distance_between()
        remap_distance = self._remap_value_distance(distance)
        
        cmds.connectAttr('%s.maxDistance' % self.pose_control, '%s.inputMax' % remap_distance)
        
        self._key_output('%s.outValue' % remap_distance, '%s.translation' % self.pose_control)
        self._key_output('%s.outputR' % blend, '%s.rotation' % self.pose_control)
        
    def _key_output(self, output_attribute, input_attribute, values = [0,1]):
        
        cmds.setDrivenKeyframe(input_attribute,
                               cd = output_attribute, 
                               driverValue = values[0], 
                               value = 0, 
                               itt = 'linear', 
                               ott = 'linear')
    
        cmds.setDrivenKeyframe(input_attribute,
                               cd = output_attribute,  
                               driverValue = values[1], 
                               value = 1, 
                               itt = 'linear', 
                               ott = 'linear')  
    
    def _multiply_weight(self):
        
        
        
        
        
        multiply = self._create_node('multiplyDivide')
        
        cmds.connectAttr('%s.translation' % self.pose_control, '%s.input1X' % multiply)
        cmds.connectAttr('%s.rotation' % self.pose_control, '%s.input2X' % multiply)
        
        multiply_offset = self._create_node('multiplyDivide')
        
        cmds.connectAttr('%s.outputX' % multiply, '%s.input1X' % multiply_offset)
        cmds.connectAttr('%s.enable' % self.pose_control, '%s.input2X' % multiply_offset)
        
        cmds.connectAttr('%s.outputX' % multiply_offset, '%s.weight' % self.pose_control)


    def _get_parent_constraint(self):
        constraint = ConstraintEditor()
        constraint_node = constraint.get_constraint(self.pose_control, 'parentConstraint')
        
        return constraint_node 
        
    def set_axis(self, axis_name):
        self.axis = axis_name
        self._position_control(self.pose_control)
        
        self._set_axis_vectors()
        
    def get_transform(self):
        matrix = self._get_named_message_attribute('multMatrix1')
        
        transform = get_attribute_input('%s.matrixIn[0]' % matrix, True)
        
        if not transform:
            transform = cmds.getAttr('%s.joint' % self.pose_control)
        
        self.transform = transform
        
        
        
        return transform

    def get_parent(self):
        
        constraint_node = self._get_parent_constraint()
        
        parent = None
        
        if constraint_node:
            constraint = ConstraintEditor()
            targets = constraint.get_targets(constraint_node)
            if targets:
                parent = targets[0]
            
        
        if not parent:
            parent = cmds.getAttr('%s.parent' % self.pose_control)
        
        return parent 
    
    def set_transform(self, transform, set_string_only = False):
        if not cmds.objExists('%s.joint' % self.pose_control):
            cmds.addAttr(self.pose_control, ln = 'joint', dt = 'string')
        
        cmds.setAttr('%s.joint' % self.pose_control, transform, type = 'string')
        
        if not set_string_only:
            matrix = self._get_named_message_attribute('multMatrix1')
            distance = self._get_named_message_attribute('distanceBetween1')
        
            if not cmds.isConnected('%s.worldMatrix' % transform, '%s.matrixIn[0]' % matrix):
                cmds.connectAttr('%s.worldMatrix' % transform, '%s.matrixIn[0]' % matrix)
            if not cmds.isConnected('%s.worldMatrix' % transform, '%s.inMatrix2' % distance):
                cmds.connectAttr('%s.worldMatrix' % transform, '%s.inMatrix2' % distance)
                
    def set_parent(self, parent, set_string_only = False):
        if not cmds.objExists('%s.parent' % self.pose_control):
            cmds.addAttr(self.pose_control, ln = 'parent', dt = 'string')
            
        if not parent:
            parent = ''
        
        cmds.setAttr('%s.parent' % self.pose_control, parent, type = 'string')
    
        if not set_string_only:
            constraint = self._get_parent_constraint()
            cmds.delete(constraint)    
            
            if parent:
                cmds.parentConstraint(parent, self.pose_control, mo = True)
    
    def detach(self):
        
        parent = self.get_parent()
        self.set_parent(parent, True)
        
        transform = self.get_transform()
        self.set_transform(transform, True)
        
        constraint = self._get_parent_constraint()
        if constraint:
            cmds.delete(constraint)
        
        self.delete_blend_input()
            
    def attach(self):
        transform = self.get_transform()
        parent = self.get_parent()
        
        self.set_transform(transform)
        self.set_parent(parent)
    
    def create(self):
        pose_control = super(PoseControl, self).create()
        
        self._create_pose_math(self.transform, pose_control)
        self._multiply_weight()
        
        self.pose_control = pose_control
        
        return pose_control
    
    def visibility_off(self, mesh = None, view_only = False):
        super(PoseControl, self).visibility_off(mesh, view_only)
        
        #if not view_only:
        #    self.mirror()
    
    def mirror(self):
        
        transform = self.get_transform()
        
        description = self.description
        
        if not description:
            self._set_description(self.pose_control)
        
        if description:
            description = description.replace(' ', '_')
        
        other_transform = ''
        
        if transform.endswith('L'):
            other_transform = transform[:-1] + 'R'
        
        if not cmds.objExists(other_transform):
            return
        
        
        other_pose = ''
        other_description = ''
        
        if self.pose_control.endswith('L'):
            other_pose = self.pose_control[:-1] + 'R'
        
        if description.endswith('L'):
            other_description =description[:-1] + 'R'
        
        other_meshes = []
        
        input_meshes = {}

        for inc in range(0, self._get_mesh_count()):
            mesh = self.get_mesh(inc)
            
            other_mesh = cmds.duplicate(mesh)[0]
            
            new_name = mesh.replace('_L', '_R')
            
            other_mesh = cmds.rename(other_mesh, new_name)
            other_meshes.append(other_mesh)
            
            target_mesh = self.get_target_mesh(mesh)
            split_name = target_mesh.split('|')
            other_target_mesh = split_name[-1][:-1] + 'R'
            
            skin = find_deformer_by_type(target_mesh, 'skinCluster')
            blendshape = find_deformer_by_type(target_mesh, 'blendShape')
            
            cmds.setAttr('%s.envelope' % skin, 0)
            cmds.setAttr('%s.envelope' % blendshape, 0)
            
            if not cmds.objExists(other_target_mesh):
                other_target_mesh = target_mesh
                
            other_target_mesh_duplicate = cmds.duplicate(other_target_mesh, n = other_target_mesh)[0]
            
            home = cmds.duplicate(target_mesh, n = 'home')[0]

            mirror_group = cmds.group(em = True)
            cmds.parent(home, mirror_group)
            cmds.parent(other_mesh, mirror_group)
            cmds.setAttr('%s.scaleX' % mirror_group, -1)
            
            create_wrap(home, other_target_mesh_duplicate)
            
            cmds.blendShape(other_mesh, home, foc = True, w = [0, 1])
            
            cmds.delete(other_target_mesh_duplicate, ch = True)
            
            input_meshes[other_target_mesh] = other_target_mesh_duplicate
            
            cmds.delete(mirror_group, other_mesh)
            
        cmds.setAttr('%s.envelope' % skin, 1)
        cmds.setAttr('%s.envelope' % blendshape, 1)
        
        store = StoreControlData(self.pose_control)
        store.eval_mirror_data()
            
        if cmds.objExists(other_pose):
            pose = PoseControl()
            pose.set_pose(other_pose)
        
        if not cmds.objExists(other_pose):
            
            pose = PoseControl(other_transform, other_description)
            pose.create()
        
        anim_translation = get_attribute_input('%s.translation' % self.pose_control, True)
        anim_rotation = get_attribute_input('%s.rotation' % self.pose_control, True)
        
        anim_new_translation = get_attribute_input('%s.translation' % pose.pose_control, True)
        anim_new_rotation = get_attribute_input('%s.rotation' % pose.pose_control, True)
        
        input_new_translation = get_attribute_input('%s.input' % anim_new_translation)
        input_new_rotation = get_attribute_input('%s.input' % anim_new_rotation)
        
        new_trans = cmds.duplicate(anim_translation)[0]
        new_rotate = cmds.duplicate(anim_rotation)[0]
        
        cmds.connectAttr(input_new_translation, '%s.input' % new_trans)
        cmds.connectAttr('%s.output' % new_trans, '%s.translation' % pose.pose_control, f = True) 
        
        cmds.connectAttr(input_new_rotation, '%s.input' % new_rotate)
        cmds.connectAttr('%s.output' % new_rotate, '%s.rotation' % pose.pose_control, f = True)

        cmds.delete(anim_new_translation)
        cmds.delete(anim_new_rotation)
        
        twist_on_value = cmds.getAttr('%s.twistOffOn' % self.pose_control)
        distance_value = cmds.getAttr('%s.maxDistance' % self.pose_control)
        angle_value = cmds.getAttr('%s.maxAngle' % self.pose_control)
        maxTwist_value = cmds.getAttr('%s.maxTwist' % self.pose_control)
        
        cmds.setAttr('%s.twistOffOn' % pose.pose_control, twist_on_value)
        cmds.setAttr('%s.maxDistance' % pose.pose_control, distance_value)
        cmds.setAttr('%s.maxAngle' % pose.pose_control, angle_value)
        cmds.setAttr('%s.maxTwist' % pose.pose_control, maxTwist_value)
        
        inc = 0
        
        for mesh in input_meshes:
            pose.add_mesh(mesh, False)
            input_mesh = pose.get_mesh(inc)
            
            fix_mesh = input_meshes[mesh]
            
            cmds.blendShape(fix_mesh, input_mesh, foc = True, w = [0,1])
            
            pose.create_blend(False)
            
            cmds.delete(input_mesh, ch = True)
            cmds.delete(fix_mesh)
            inc += 1
        
        return pose.pose_control
                

class ComboControl(BasePoseControl):
    def __init__(self, pose_list = None, description = 'combo'):
        super(ComboControl, self).__init__(description)
        
        self.pose_list = pose_list
        
    def _connect_poses(self):
        last_multiply = None
        
        for inc in range(0, len( self.pose_list ) ):
            pose = self.pose_list[inc]
            
            self._connect_node(pose, 'pose', inc)
            
            multiply = self._create_node('multiplyDivide')
            
            cmds.connectAttr('%s.weight' % pose, '%s.input1X' % multiply)
            
            if last_multiply:
                cmds.connectAttr('%s.outputX' % last_multiply, '%s.input2X' % multiply)
    
            last_multiply = multiply 
            
        cmds.connectAttr('%s.outputX' % last_multiply, '%s.weight' % self.pose_control)
       
    def create(self):
        
        super(ComboControl, self).create()
        
        self._connect_poses()
 
class EnvelopeHistory(object):
    
    def __init__(self, transform):
        
        self.transform = transform
        
        self.envelope_values = {}
        self.envelope_connection = {}
        
        self.history = self._get_envelope_history()
        
        
        
    def _get_history(self):
        
        history = cmds.listHistory(self.transform)
        return history
        
    def _get_envelope_history(self):
        
        self.envelope_values = {}
        
        history = self._get_history()
        
        found = []
        
        for thing in history:
            if cmds.objExists('%s.envelope' % thing):
                found.append(thing)
                
                value = cmds.getAttr('%s.envelope' % thing)
                
                self.envelope_values[thing] = value
                
                connected = get_attribute_input('%s.envelope' % thing)
                
                self.envelope_connection[thing] = connected
                
        return found
    
    def turn_off(self):
        
        
        
        for history in self.history:
            
            connection = self.envelope_connection[history]
            
            if connection:
                cmds.disconnectAttr(connection, '%s.envelope' % history)
                
            cmds.setAttr('%s.envelope' % history, 0)
 
    def turn_on(self, respect_initial_state = False):
        for history in self.history:
            
            if respect_initial_state:
                value = self.envelope_values[history]
            if not respect_initial_state:
                value = 1
            
            cmds.setAttr('%s.envelope' % history, value)
            
            connection = self.envelope_connection[history]
            if connection:
                cmds.connectAttr(connection, '%s.envelope' % history)
                
                
#--- definitions

def inc_name(name):
    unique = FindUniqueName(name)
    return unique.get()

def prefix_name(node, prefix, name, separator = '_'):
    new_name = cmds.rename(node, '%s%s%s' % (prefix,separator, name))
    
    return new_name

def pad_number(name):
        
    number = vtool.util.get_last_number(name)
    
    number_string = str(number)
    
    index = name.rfind(number_string)

    if number < 10:
        number_string = number_string.zfill(2)
        
    new_name =  name[0:index] + number_string + name[index+1:]
    renamed = cmds.rename(name, new_name)
    
    return renamed
    

def nodename_to_mobject(object_name):
    
    selection_list = SelectionList()
    selection_list.create_by_name(object_name)
    
    return selection_list.get_at_index(0)

def warning(warning_string):
    pass
    #mglobal = OpenMaya.MGlobal()
    
    #mglobal.displayWarning(warning_string)
    
def get_node_types(nodes, return_shape_type = True):
    
    found_type = {}
    
    for node in nodes:
        node_type = cmds.nodeType(node)
        
        if node_type == 'transform':
            
            if return_shape_type:
                shapes = get_shapes(node)
                
                if shapes:
                    node_type = cmds.nodeType(shapes[0])
        
        if not node_type in found_type:
            found_type[node_type] = []
            
        found_type[node_type].append(node)
        
    return found_type
     
def get_basename(name):
    split_name = name.split('|')
    
    basename = split_name[-1]
    
    return basename

def get_visible_hud_displays():
    found = []
        
    displays = cmds.headsUpDisplay(q = True, lh = True)
        
    for display in displays:
        visible = cmds.headsUpDisplay(display, q = True, vis = True)
        
        if visible:
            found.append(display)
        
    return found

def set_hud_visibility(bool_value, displays = None):
    
    if not displays:
        displays = cmds.headsUpDisplay(q = True, lh = True) 
    
    for display in displays:
        cmds.headsUpDisplay(display, e = True, vis = bool_value)

def set_hud_lines(lines, name):
    
    huds = []
    
    inc = 0
    for line in lines:

        hud_name = '%s%s' % (name, inc)
    
        if cmds.headsUpDisplay(hud_name, ex = True):
            cmds.headsUpDisplay(hud_name, remove = True)
        
            
        cmds.headsUpDisplay( hud_name, section = 1, block = inc, blockSize = 'large', labelFontSize = "large", dataFontSize = 'large')
        cmds.headsUpDisplay( hud_name, edit = True, label = line)
    
        huds.append(hud_name)
        
        inc += 1
    
    return huds
    
def show_channel_box():
    
    docks = mel.eval('global string $gUIComponentDockControlArray[]; string $goo[] = $gUIComponentDockControlArray;')
    
    if 'Channel Box / Layer Editor' in docks:
        index = docks.index('Channel Box / Layer Editor')
        dock = docks[index + 1]
        
        if cmds.dockControl(dock, q = True, visible = True):
            cmds.dockControl(dock, edit = True, visible = False)
            cmds.dockControl(dock, edit = True, visible = True)
        
        index = docks.index('Channel Box')
        dock = docks[index + 1]
            
        if cmds.dockControl(dock, q = True, visible = True):
            cmds.dockControl(dock, edit = True, visible = False)
            cmds.dockControl(dock, edit = True, visible = True)
    
def playblast(filename):
    
    min = cmds.playbackOptions(query = True, minTime = True)
    max = cmds.playbackOptions(query = True, maxTime = True)
    
    sound = get_current_audio_node()
    
    frames = []
    
    for inc in range(int(min), int((max+2)) ):
        frames.append(inc)
    
    if sound:
        cmds.playblast(frame = frames,
                   format = 'qt', 
                   percent = 100, 
                   sound = sound,
                   viewer = True, 
                   showOrnaments = True, 
                   offScreen = True, 
                   compression = 'MPEG4-4 Video', 
                   widthHeight = [1280, 720], 
                   filename = filename, 
                   clearCache = True, 
                   forceOverwrite = True)
        
    if not sound:
        cmds.playblast(frame = frames,
                   format = 'qt', 
                   percent = 100,
                   viewer = True, 
                   showOrnaments = True, 
                   offScreen = True, 
                   compression = 'MPEG4-4 Video', 
                   widthHeight = [1280, 720], 
                   filename = filename, 
                   clearCache = True, 
                   forceOverwrite = True)

def get_current_audio_node():
    
    play_slider = mel.eval('global string $gPlayBackSlider; string $goo = $gPlayBackSlider')
    
    return cmds.timeControl(play_slider, q = True, s = True)

#--- shading

def apply_shading_engine(shader_name, mesh):
    cmds.sets(mesh, e = True, forceElement = shader_name)
    
def get_shading_engine_geo(shader_name):
    pass

def apply_new_shader(mesh, type_of_shader = 'blinn', name = ''):
    
    if name:
        if not cmds.objExists(name):
            material = cmds.shadingNode(type_of_shader, asShader = True, n = name)
        if cmds.objExists(name):
            material = name
    if not name:
        material = cmds.shadingNode(type_of_shader, asShader = True)
    
    shader_set = cmds.sets( renderable = True, 
                    noSurfaceShader = True, 
                    empty = True, 
                    n = '%sSG' % material)
    
    cmds.sets( mesh, e = True, forceElement = shader_set)
    
    cmds.defaultNavigation(connectToExisting = True, 
                           source = material, 
                           destination = shader_set)
    
    #shape = get_mesh_shape(mesh)
    
    return material
    

def create_display_layer(name, nodes):
    
    layer = cmds.createDisplayLayer( name = name )
    cmds.editDisplayLayerMembers( layer, nodes, noRecurse = True)
    cmds.setAttr( '%s.displayType' % layer, 2 )

#--- space

def is_a_transform(node):
    if cmds.objectType(node, isAType = 'transform'):
        return True
    
    return False
    
def get_closest_transform(source_transform, targets):
        
        least_distant = 1000000.0
        closest_target = None
        
        for target in targets:
            
            distance = get_distance(source_transform, target)
            
            if distance < least_distant:
                least_distant = distance
                closest_target = target
                
        return closest_target 

def get_distance(source, target):
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
    
    return vtool.util.get_distance(vector1, vector2)

def get_distances(sources, target):
    
    distances = []
    
    for source in sources:
        
        distance = get_distance(source, target)
        
        distances.append(distance)
    
    return distances
        
def get_polevector(transform1, transform2, transform3, offset = 1):
    #CBB
    
    distance = get_distance(transform1, transform3)
    
    group = get_group_in_plane(transform1, 
                               transform2, 
                               transform3)
    
    cmds.move(0, offset * distance, 0, group, r =True, os = True)
    finalPos = cmds.xform(group, q = True, ws = True, rp = True)

    cmds.delete(group)
    
    return finalPos

def get_group_in_plane(transform1, transform2, transform3):
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

def  get_center(thing):
    
    components = get_components_in_hierarchy(thing)
    
    if components:
        thing = components
        
    
    
    bounding_box = BoundingBox(thing)
    return bounding_box.get_center()

def get_btm_center(thing):
    
    components = get_components_in_hierarchy(thing)
    
    if components:
        thing = components
        
    
    
    bounding_box = BoundingBox(thing)
    return bounding_box.get_ymin_center()

def get_top_center(thing):
    components = get_components_in_hierarchy(thing)
    
    if components:
        thing = components
        
    
    
    bounding_box = BoundingBox(thing)
    return bounding_box.get_ymax_center()


def get_ordered_distance_and_transform(source_transform, transform_list):
    
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
    
    distance_list, distance_dict, original = get_ordered_distance_and_transform(source_transform, transform_list)
    
    found = []
    
    for distance in distance_list:
        found.append(distance_dict[distance][0])
        
    return found

def create_follow_fade(source_guide, drivers, skip_lower = 0.0001):
    
    distance_list, distance_dict, original_distance_order = get_ordered_distance_and_transform(source_guide, drivers)
    
    multiplies = []
    
    if not distance_list[-1] > 0:
        return multiplies
    
    for distance in original_distance_order:
                
        scaler = 1.0 - (distance/ distance_list[-1]) 
        
        if scaler <= skip_lower:
            continue
        
        multi = MultiplyDivideNode(source_guide)
        
        multi.set_input2(scaler,scaler,scaler)
        
        multi.input1X_in( '%s.translateX' % source_guide )
        multi.input1Y_in( '%s.translateY' % source_guide )
        multi.input1Z_in( '%s.translateZ' % source_guide )
        
        for driver in distance_dict[distance]:
            multi.outputX_out('%s.translateX' % driver)
            multi.outputY_out('%s.translateY' % driver)
            multi.outputZ_out('%s.translateZ' % driver)
        
        multi_dict = {}
        multi_dict['node'] = multi.node
        multi_dict['source'] = source_guide
        multi_dict['target'] = driver
        
        multiplies.append(multi_dict)
        
    return multiplies

def create_xform_group(transform, prefix = 'xform', use_duplicate = False):
    
    parent = cmds.listRelatives(transform, p = True, f = True)
    
    basename = get_basename(transform)
    
    name = '%s_%s' % (prefix, basename)
    
    if not use_duplicate:    
        xform_group = cmds.group(em = True, n = inc_name( name ))
        match_space = MatchSpace(transform, xform_group)
        match_space.translation_rotation()
        
        if parent:
            cmds.parent(xform_group, parent[0])    
        
    if use_duplicate:
        xform_group = cmds.duplicate(transform, po = True)
        xform_group = cmds.rename(xform_group, inc_name(name))
    
    cmds.parent(transform, xform_group)

    return xform_group

def create_follow_group(source_transform, target_transform, prefix = 'follow'):
    
    parent = cmds.listRelatives(target_transform, p = True)
    
    name = '%s_%s' % (prefix, target_transform)
    
    follow_group = cmds.group( em = True, n = inc_name(name) )
    
    match = MatchSpace(source_transform, follow_group)
    match.translation_rotation()
    
    cmds.parentConstraint(source_transform, follow_group, mo = True)
    
    cmds.parent(target_transform, follow_group)    
    
    if parent:
        cmds.parent(follow_group, parent)
        
    return follow_group

def create_local_follow_group(source_transform, target_transform, prefix = 'followLocal', orient_only = False):
    
    parent = cmds.listRelatives(target_transform, p = True)
    
    name = '%s_%s' % (prefix, target_transform)
    
    follow_group = cmds.group( em = True, n = inc_name(name) )
    
    #MatchSpace(target_transform, follow_group).translation()
    MatchSpace(source_transform, follow_group).translation_rotation()
    
    xform = create_xform_group(follow_group)
    
    #cmds.parentConstraint(source_transform, follow_group, mo = True)
    
    if not orient_only:
        connect_translate(source_transform, follow_group)
    
    connect_rotate(source_transform, follow_group)
    
    value = cmds.getAttr('%s.rotateOrder' % source_transform)
    cmds.setAttr('%s.rotateOrder' % follow_group, value)
    
    
    cmds.parent(target_transform, follow_group)
    
    if parent:
        cmds.parent(xform, parent)
        
    return follow_group    

def create_multi_follow_direct(source_list, target_transform, node, constraint_type = 'parentConstraint'):
    var = MayaEnumVariable('FOLLOW')
    var.create(node)
    
    locators = []

    for source in source_list:
        
        locator = cmds.spaceLocator(n = inc_name('follower_%s' % source))[0]
        
        cmds.hide(locator)
        
        match = MatchSpace(target_transform, locator)
        match.translation_rotation()
        
        cmds.parent(locator, source)
        
        locators.append(locator)
    
    if constraint_type == 'parentConstraint':
        constraint = cmds.parentConstraint(locators,  target_transform, mo = True)[0]
        
    if constraint_type == 'pointConstraint':
        constraint = cmds.pointConstraint(locators,  target_transform, mo = True)[0]
    
    constraint_editor = ConstraintEditor()
    
    constraint_editor.create_switch(node, 'follow', constraint)
    
    cmds.setAttr('%s.follow' % node, len(source_list)-1)   

def create_multi_follow(source_list, target_transform, node, constraint_type = 'parentConstraint', attribute_name = 'follow'):
    
    var = MayaEnumVariable('FOLLOW')
    var.create(node)
    
    locators = []
    
    follow_group = create_xform_group(target_transform, 'follow')

    for source in source_list:
        
        locator = cmds.spaceLocator(n = inc_name('follower_%s' % source))[0]
        
        cmds.hide(locator)
        
        match = MatchSpace(target_transform, locator)
        match.translation_rotation()
        
        cmds.parent(locator, source)
        
        locators.append(locator)
    
    if constraint_type == 'parentConstraint':
        constraint = cmds.parentConstraint(locators,  follow_group, mo = True)[0]
    if constraint_type == 'orientConstraint':
        constraint = cmds.orientConstraint(locators,  follow_group, mo = True)[0]
    
    
    constraint_editor = ConstraintEditor()
    
    constraint_editor.create_switch(node, attribute_name, constraint)
    
    cmds.setAttr('%s.%s' % (node, attribute_name), len(source_list)-1)
    
    return follow_group


def get_hierarchy(node_name):
    
    parent_path = cmds.listRelatives(node_name, f = True)[0]
    
    if parent_path:
        split_path = cmds.split(parent_path, '|')
    
    if split_path:
        return split_path
        
def transfer_relatives(source_node, target_node):
    parent = cmds.listRelatives(source_node, p = True)
    if parent:
        parent = parent[0]
        
    children = cmds.listRelatives(source_node, c = True)
    
    if children:
        cmds.parent(children, target_node)
    if parent:
        cmds.parent(target_node, parent)
        
def get_outliner_sets():

    sets = cmds.ls(type = 'objectSet')
                
    top_sets = []
        
    for object_set in sets:
        if object_set == 'defaultObjectSet':
            continue
        
        outputs = get_attribute_outputs(object_set)
            
        if not outputs:
            top_sets.append( object_set )
            
            
    return top_sets

def get_top_dag_nodes(exclude_cameras = True):
    top_transforms = cmds.ls(assemblies = True)
    
    cameras = ['persp', 'top', 'front', 'side']
    
    for camera in cameras:
        if camera in top_transforms:
            top_transforms.remove(camera)
     
    return top_transforms 

def create_spline_ik_stretch(curve, joints, node_for_attribute = None, create_stretch_on_off = False):
    
    arclen_node = cmds.arclen(curve, ch = True, n = inc_name('curveInfo_%s' % curve))
    
    
    
    arclen_node = cmds.rename(arclen_node, inc_name('curveInfo_%s' % curve))
    
    multiply_scale_offset = cmds.createNode('multiplyDivide', n = inc_name('multiplyDivide_offset_%s' % arclen_node))
    cmds.setAttr('%s.operation' % multiply_scale_offset, 2 )
    
    multiply = cmds.createNode('multiplyDivide', n = inc_name('multiplyDivide_%s' % arclen_node))
    
    cmds.connectAttr('%s.arcLength' % arclen_node, '%s.input1X' % multiply_scale_offset)
    
    cmds.connectAttr('%s.outputX' % multiply_scale_offset, '%s.input1X' % multiply)
    
    cmds.setAttr('%s.input2X' % multiply, cmds.getAttr('%s.arcLength' % arclen_node))
    cmds.setAttr('%s.operation' % multiply, 2)
    
    joint_count = len(joints)
    
    segment = 1.00/joint_count
    
    percent = 0
    
    for joint in joints:
        
        attribute = '%s.outputX' % multiply
             
        if create_stretch_on_off and node_for_attribute:
            
            attr = MayaNumberVariable('stretchOnOff')
            attr.set_min_value(0)
            attr.set_max_value(1)
            attr.set_keyable(True)
            attr.create(node_for_attribute)
        
            blend = cmds.createNode('blendColors', n = 'blendColors_stretchOnOff_%s' % curve)
    
            cmds.connectAttr(attribute, '%s.color1R' % blend)
            cmds.setAttr('%s.color2R' % blend, 1)
            
            cmds.connectAttr('%s.outputR' % blend, '%s.scaleX' % joint)
            
            cmds.connectAttr('%s.stretchOnOff' % node_for_attribute, '%s.blender' % blend)
            
        if not create_stretch_on_off:
            cmds.connectAttr(attribute, '%s.scaleX' % joint)
        
        #bulge cbb
        plus = cmds.createNode('plusMinusAverage', n = 'plusMinusAverage_scale_%s' % joint)
        
        cmds.addAttr(plus, ln = 'scaleOffset', dv = 1, k = True)
        cmds.addAttr(plus, ln = 'bulge', dv = 1, k = True)
        
        arc_value = vtool.util.fade_sine(percent)
        
        connect_multiply('%s.outputX' % multiply_scale_offset, '%s.bulge' % plus, arc_value)
        
        connect_plus('%s.scaleOffset' % plus, '%s.input1D[0]' % plus)
        connect_plus('%s.bulge' % plus, '%s.input1D[1]' % plus)
        
        scale_value = cmds.getAttr('%s.output1D' % plus)
        
        multiply_offset = cmds.createNode('multiplyDivide', n = 'multiply_%s' % joint)
        cmds.setAttr('%s.operation' % multiply_offset, 2)
        cmds.setAttr('%s.input1X' % multiply_offset, scale_value)
        
        cmds.connectAttr('%s.output1D' % plus, '%s.input2X' % multiply_offset)
        
        blend = cmds.createNode('blendColors', n = 'blendColors_%s' % joint)
        
        attribute = '%s.outputR' % blend
        
        if node_for_attribute:
            cmds.connectAttr('%s.outputX' % multiply_offset, '%s.color1R' % blend)
        
            cmds.setAttr('%s.color2R' % blend, 1)
        
            
            
            attr = MayaNumberVariable('stretchyBulge')
            attr.set_min_value(0)
            attr.set_max_value(10)
            attr.set_keyable(True)
            attr.create(node_for_attribute)
            
            connect_multiply('%s.stretchyBulge' % node_for_attribute, 
                             '%s.blender' % blend, 0.1)
            
            
        if not node_for_attribute:
            attribute = '%s.outputX' % multiply_offset

        cmds.connectAttr(attribute, '%s.scaleY' % joint)
        cmds.connectAttr(attribute, '%s.scaleZ' % joint)
        
        
        percent += segment
        

def create_bulge_chain(joints, control, max_value = 15):
    
    
    control_and_attribute = '%s.bulge' % control
    
    if not cmds.objExists(control_and_attribute):
        attr = MayaNumberVariable('bulge')
        attr.set_variable_type(attr.TYPE_DOUBLE)
        attr.set_min_value(0)
        attr.set_max_value(max_value)
        attr.create(control)
        
    attributes = ['Y','Z']
    
    joint_count = len(joints)
    
    offset = 10.00/ joint_count
    
    
    initial_driver_value = 0
    default_scale_value = 1
    scale_value = 2
    
    inc = 0
    
    for joint in joints:
        for attr in attributes:
            
            cmds.setDrivenKeyframe('%s.scale%s' % (joint, attr), 
                                   cd = control_and_attribute, 
                                   driverValue = initial_driver_value, 
                                   value = default_scale_value, 
                                   itt = 'linear', 
                                   ott = 'linear' )
            
            cmds.setDrivenKeyframe('%s.scale%s' % (joint, attr), 
                                   cd = control_and_attribute, 
                                   driverValue = initial_driver_value + offset*3, 
                                   value = scale_value,
                                   itt = 'linear', 
                                   ott = 'linear' )            
            
            cmds.setDrivenKeyframe('%s.scale%s' % (joint, attr), 
                                   cd = control_and_attribute, 
                                   driverValue = initial_driver_value + (offset*6), 
                                   value = default_scale_value, 
                                   itt = 'linear', 
                                   ott = 'linear' )
            
        inc += 1
        initial_driver_value += offset
    

def constrain_local(source_transform, target_transform, parent = False, scale_connect = False, constraint = 'parentConstraint'):
    
    local_group = cmds.group(em = True, n = inc_name('local_%s' % source_transform))
    
    xform_group = create_xform_group(local_group)
    
    parent_world = cmds.listRelatives(source_transform, p = True)
    
    if parent_world:
        parent_world = parent_world[0]
        
        match = MatchSpace(parent_world, xform_group)
        match.translation_rotation()
        
        
    match = MatchSpace(source_transform, local_group)
    
    match.translation_rotation()
    
    
    
    connect_translate(source_transform, local_group)
    connect_rotate(source_transform, local_group)
    
    if scale_connect:
        connect_scale(source_transform, local_group)
        
    value = cmds.getAttr('%s.rotateOrder' % source_transform)
    cmds.setAttr('%s.rotateOrder' % local_group, value)
    
    if parent:
        cmds.parent(target_transform, local_group)
        
    if not parent:
        if constraint == 'parentConstraint':
            cmds.parentConstraint(local_group, target_transform, mo = True)
        if constraint == 'pointConstraint':
            cmds.pointConstraint(local_group, target_transform, mo = True)
            
        if scale_connect:
            connect_scale(source_transform, target_transform)
    
    return local_group, xform_group

def subdivide_joint(joint1 = None, joint2 = None, count = 1, prefix = 'joint', name = 'sub_1', duplicate = False):
    
    if not joint1 and not joint2:
        selection = cmds.ls(sl = True)
        
        if cmds.nodeType(selection[0]) == 'joint':
            joint1 = selection[0]
        
        if cmds.nodeType(selection[1]) == 'joint':
            joint2 = selection[1]
            
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
        top_joint = cmds.joint(p = vector1, n = inc_name(name), r = radius + 1)
        joints.append(top_joint)
        
        match = MatchSpace(joint1, top_joint)
        match.rotation()
        cmds.makeIdentity(top_joint, apply = True, r = True)
    
    offset = 1.00/(count+1)
    value = offset
    
    last_joint = None
    
    for inc in range(0, count):
        
        position = vtool.util.get_inbetween_vector(vector1, vector2, value)
        
        cmds.select(cl = True)
        joint = cmds.joint( p = position, n = inc_name(name), r = radius)
            
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
        btm_joint = cmds.joint(p = vector2, n = inc_name(name), r = radius + 1)
        joints.append(btm_joint)

        match = MatchSpace(joint1, btm_joint)
        match.rotation()
        cmds.makeIdentity(btm_joint, apply = True, r = True)
    
    cmds.parent(btm_joint, joint)
    
    if not cmds.isConnected('%s.scale' % joint, '%s.inverseScale'  % btm_joint):
            cmds.connectAttr('%s.scale' % joint, '%s.inverseScale'  % btm_joint)
            
    return joints

def create_distance_falloff(source_transform, source_local_vector = [1,0,0], target_world_vector = [1,0,0], description = 'falloff'):
    
    
    distance_between = cmds.createNode('distanceBetween', 
                                        n = inc_name('distanceBetween_%s' % description) )
    
    cmds.addAttr(distance_between,ln = 'falloff', at = 'double', k = True)
        
    follow_locator = cmds.spaceLocator(n = 'follow_%s' % distance_between)[0]
    match = MatchSpace(source_transform, follow_locator)
    match.translation_rotation()
    cmds.parent(follow_locator, source_transform)
    cmds.move(source_local_vector[0], source_local_vector[1], source_local_vector[2], follow_locator, r = True, os = True)
    
    set_color([follow_locator], 6)
    
    target_locator = cmds.spaceLocator(n = 'target_%s' % distance_between)[0]
    match = MatchSpace(source_transform, target_locator)
    match.translation_rotation()
    
    set_color([target_locator], 13)
    
    
    
    parent = cmds.listRelatives(source_transform, p = True)
    
    if parent:
        parent = parent[0]
        cmds.parent(target_locator, parent)
    
    cmds.move(target_world_vector[0], target_world_vector[1], target_world_vector[2], target_locator, r = True, ws = True)
    
    cmds.parent(follow_locator, target_locator)
    
    cmds.parentConstraint(source_transform, follow_locator, mo = True)
        
    cmds.connectAttr('%s.worldMatrix' % follow_locator, 
                     '%s.inMatrix1' % distance_between)
        
    cmds.connectAttr('%s.worldMatrix' % target_locator, 
                     '%s.inMatrix2' % distance_between)
    
    distance_value = cmds.getAttr('%s.distance' % distance_between)
    
    driver = '%s.distance' % distance_between
    driven = '%s.falloff' % distance_between
     
    cmds.setDrivenKeyframe(driven,
                           cd = driver, 
                           driverValue = distance_value, 
                           value = 0, 
                           itt = 'linear', 
                           ott = 'linear')

    cmds.setDrivenKeyframe(driven,
                           cd = driver,  
                           driverValue = 0, 
                           value = 1, 
                           itt = 'linear', 
                           ott = 'linear')  
    
    return distance_between    

def create_distance_scale(xform1, xform2, axis = 'X'):
    
    locator1 = cmds.spaceLocator(n = inc_name('locatorDistance_%s' % xform1))[0]
    print xform1, locator1
    MatchSpace(xform1, locator1).translation()
    
    locator2 = cmds.spaceLocator(n = inc_name('locatorDistance_%s' % xform2))[0]
    MatchSpace(xform2, locator2).translation()
    
    distance = cmds.createNode('distanceBetween', n = inc_name('distanceBetween_%s' % xform1))
    multiply = cmds.createNode('multiplyDivide', n = inc_name('multiplyDivide_%s' % xform1))
    
    cmds.connectAttr('%s.worldMatrix' % locator1, '%s.inMatrix1' % distance)
    cmds.connectAttr('%s.worldMatrix' % locator2, '%s.inMatrix2' % distance)
    
    distance_value = cmds.getAttr('%s.distance' % distance)
    
    cmds.connectAttr('%s.distance' % distance, '%s.input1X' % multiply)
    cmds.setAttr('%s.input2X' % multiply, distance_value)
    cmds.setAttr('%s.operation' % multiply, 2)
    
    cmds.connectAttr('%s.outputX' % multiply, '%s.scale%s' % (xform1, axis))
        
    return locator1, locator2
    
    
    

def add_orient_attributes(transform):
    if type(transform) != list:
        transform = [transform]
    
    for thing in transform:
        
        orient = OrientJointAttributes(thing)
        orient.set_default_values()
    
def orient_attributes(scope = None):
    if not scope:
        scope = get_top_dag_nodes()
    
    for transform in scope:
        relatives = cmds.listRelatives(transform)
        
        if not cmds.objExists('%s.ORIENT_INFO' % transform):
            if relatives:
                orient_attributes(relatives)
                
            continue
        
        if cmds.nodeType(transform) == 'joint' or cmds.nodeType(transform) == 'transform':
            orient = OrientJoint(transform)
            orient.run()
            
            if relatives:
                orient_attributes(relatives)

def mirror_xform(prefix):
    if not prefix:
        return
    
    scope_joints = cmds.ls('%s*' % prefix, type = 'joint')
    scope_transforms = cmds.ls('%s*' % prefix, type = 'transform')
    
    scope = scope_joints + scope_transforms
    
    for transform in scope:
        if not transform.endswith('_L'):
            continue
            
        other= transform.replace('_L', '_R')
       
        if cmds.objExists(other):
            
            xform = cmds.xform(transform, q = True, ws = True, t = True)
            
            if cmds.nodeType(other) == 'joint':
                
                radius = cmds.getAttr('%s.radius' % transform)
                cmds.setAttr('%s.radius' % other, radius)    
                cmds.move((xform[0]*-1), xform[1], xform[2], '%s.scalePivot' % other, 
                                                             '%s.rotatePivot' % other, a = True)
            
            if cmds.nodeType(other) == 'transform':
                cmds.move((xform[0]*-1), xform[1],xform[2], other, a = True)
    
def match_joint_xform(prefix, other_prefix):

    scope = cmds.ls('%s*' % other_prefix, type = 'joint')

    for joint in scope:
        other_joint = joint.replace(other_prefix, prefix)

        if cmds.objExists(other_joint):    
            match = MatchSpace(joint, other_joint)
            match.rotate_scale_pivot_to_translation()

def match_orient(prefix, other_prefix):
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

def get_axis_vector(axis_name):
    
    if axis_name == 'X':
        return (1,0,0)
    
    if axis_name == 'Y':
        return (0,1,0)
    
    if axis_name == 'Z':
        return (0,0,1)

def get_y_intersection(curve, vector):
    
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
    
def get_side(transform, center_tolerance):
    
    if type(transform) == list or type(transform) == tuple:
        position = transform
    
    if not type(transform) == list and not type(transform) == tuple:
        position = cmds.xform(transform, q = True, ws = True, t = True)
        
    if position[0] > 0:
        side = 'L'

    if position[0] < 0:
        side = 'R'
        
    if position[0] < center_tolerance and position[0] > center_tolerance*-1:
        side = 'C'
            
    return side

#--- animation

def get_input_keyframes(node, node_only = True):
    
    inputs = get_inputs(node, node_only)
    
    found = []
    
    for input_value in inputs:
        if cmds.nodeType(input_value).startswith('animCurve'):
            found.append(input_value)
            
    return found        

def get_output_keyframes(node):
        
    outputs = get_outputs(node)
    
    found = []
    
    for output in outputs:
        
        if cmds.nodeType(output).startswith('animCurve'):
            found.append(output)
            
    return found

#--- geometry

def is_a_shape(node):
    if cmds.objectType(node, isAType = 'shape'):
        return True
    
    return False

def has_shape_of_type(node, maya_type):
    
    test = None
    
    if cmds.objectType(node, isAType = 'shape'):
        test = node
        
    if not cmds.objectType(node, isAType = 'shape'):
        shapes = get_shapes(node)
        
        if shapes:
            test = shapes[0]
        
    if test:
        if maya_type == cmds.nodeType(test):
            return True
        

def get_selected_meshes():

    selection = cmds.ls(sl = True)
    
    found = []
    
    for thing in selection:
        if cmds.nodeType(thing) == 'mesh':
            found_mesh = cmds.listRelatives(thing, p = True)
            found.append(found_mesh)
            
        if cmds.nodeType(thing) == 'transform':
            
            shapes = get_mesh_shape(thing)
            if shapes:
                found.append(thing)
                
    return found
        

def get_mesh_shape(mesh, shape_index = 0):
    
    if mesh.find('.vtx'):
        mesh = mesh.split('.')[0]
    
    if cmds.nodeType(mesh) == 'mesh':
        mesh = cmds.listRelatives(p = True)[0]
        
    shapes = get_shapes(mesh)
    if not shapes:
        return
    
    if not cmds.nodeType(shapes[0]) == 'mesh':
        return
    
    shape_count = len(shapes)
    
    if shape_index < shape_count:
        return shapes[0]
    
    if shape_index > shape_count:
        warning('%s does not have a shape count up to %s' % shape_index)
    

def get_shapes(transform):
    if is_a_shape(transform):
        parent = cmds.listRelatives(transform, p = True, f = True)
        return cmds.listRelatives(parent, s = True, f = True)
    
    return cmds.listRelatives(transform, s = True, f = True)

def get_shapes_in_hierarchy(transform):
    
    hierarchy = [transform]
    
    relatives = cmds.listRelatives(transform, ad = True, type = 'transform', f = True)
    
    if relatives:
        hierarchy += relatives
    
    shapes = []
    
    for child in hierarchy:
        
        found_shapes = get_shapes(child)
        sifted_shapes = []
        
        if not found_shapes:
            continue
        
        for found_shape in found_shapes:
            
            if cmds.getAttr('%s.intermediateObject' % found_shape):
                continue
            
            sifted_shapes.append( found_shape )
            
        if sifted_shapes:
            shapes += sifted_shapes
    
    return shapes

def get_component_count(transform):
    components = get_components(transform)
    
    return len( cmds.ls(components[0], flatten = True) )

def get_components(transform):
    
    shapes = get_shapes(transform)
    
    return get_components_from_shapes(shapes)

def get_components_in_hierarchy(transform):
    
    shapes = get_shapes_in_hierarchy(transform)
    
    return get_components_from_shapes(shapes)

def get_components_from_shapes(shapes):
    components = []
    if shapes:
        for shape in shapes:
            
            found_components = None
            
            if cmds.nodeType(shape) == 'nurbsSurface':
                found_components = '%s.cv[*]' % shape
            
            if cmds.nodeType(shape) == 'nurbsCurve':
                found_components = '%s.cv[*]' % shape
            
            if cmds.nodeType(shape) == 'mesh':
                found_components = '%s.vtx[*]' % shape
            
            if found_components:
                components.append( found_components )
            
    return components


     

def get_edge_path(edges = []):
    cmds.select(cl = True)
    cmds.polySelectSp(edges, loop = True )
    
    return cmds.ls(sl = True, l = True)

def edge_to_vertex(edges):
    
    edges = cmds.ls(edges, flatten = True)
    
    verts = []
    
    mesh = edges[0].split('.')
    mesh = mesh[0]
    
    for edge in edges:
        print edge
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
        

def get_slots(attribute):
    
    slots = cmds.listAttr(attribute, multi = True)
        
    found_slots = []
    
    for slot in slots:
        index = re.findall('\d+', slot)
        
        if index:
            found_slots.append(index[-1])
            
    return found_slots

def get_slot_count(attribute):
    slots = get_slots(attribute)
    
    if not slots:
        return 0
    
    return len(slots)

def get_available_slot(attribute):
    
    slots = get_slots(attribute)
    
    if not slots:
        return 0
    
    return int( slots[-1] )+1

def attach_to_mesh(transform, mesh, deform = False, priority = None, face = None, point_constrain = False, auto_parent = False, hide_shape= False, inherit_transform = False, local = False, rotate_pivot = False, constrain = True):
    parent = None
    if auto_parent:
        parent = cmds.listRelatives(transform, p = True)
    
    shape = cmds.listRelatives(mesh, shapes = True)[0]
    
    face_iter = IteratePolygonFaces(shape)
    
    if rotate_pivot:
        position = cmds.xform(transform, q = True, rp = True, ws = True)
    if not rotate_pivot: 
        position = get_center(transform)
    
    if not face:
        face_id = face_iter.get_closest_face(position)
    if face:
        face_id = face
    
    edges = face_iter.get_edges(face_id)
    
    edge1 = '%s.e[%s]' % (mesh, edges[0])
    edge2 = '%s.e[%s]' % (mesh, edges[2])

    if not type(transform) == list:
        transform = [transform]
    
    if not priority:
        priority = transform[0]
    
    rivet = Rivet(priority)
    rivet.set_edges([edge1, edge2])
    rivet = rivet.create()
    
    if deform:

        for thing in transform:
            cluster, handle = cmds.cluster(thing, n = inc_name('rivetCluster_%s' % thing))
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
                    local, xform = constrain_local(rivet, thing, constraint = 'pointConstraint')
                if not point_constrain:
                    local, xform = constrain_local(rivet, thing, constraint = 'parentConstraint')
                    
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

def attach_to_surface(transform, surface, u = None, v = None):
    
    position = cmds.xform(transform, q = True, ws = True, t = True)

    if u == None or v == None:
        uv = get_closest_parameter_on_surface(surface, position)   
        
    rivet = Rivet(transform)
    rivet.set_surface(surface, uv[0], uv[1])
    rivet.set_create_joint(False)
    rivet.set_percent_on(False)
    
    rivet.create()
    
    cmds.parentConstraint(rivet.rivet, transform, mo = True)
    
    return rivet.rivet

def attach_to_closest_transform(source_transform, target_transforms):
    
    closest_transform = get_closest_transform(source_transform, target_transforms)
    
    create_follow_group(closest_transform, source_transform)

def follicle_to_surface(transform, surface, u = None, v = None):
    
    position = cmds.xform(transform, q = True, ws = True, t = True)

    if u == None or v == None:
        uv = get_closest_parameter_on_surface(surface, position)   

    create_surface_follicle(surface, transform, uv)
    
    
def create_surface_follicle(surface, description = None, uv = [0,0]):
    
    follicleShape = cmds.createNode('follicle')
    
    follicle = cmds.listRelatives(follicleShape, p = True)[0]
    
    if not description:
        follicle = cmds.rename(follicle, inc_name('follicle_1'))[0]
    if description:
        follicle = cmds.rename(follicle, inc_name('follicle_%s' % description))
        
    shape = cmds.listRelatives(follicle, shapes = True)[0]
        
    cmds.connectAttr('%s.local' % surface, '%s.inputSurface' % follicle)
    cmds.connectAttr('%s.worldMatrix' % surface, '%s.inputWorldMatrix' % follicle)
    
    cmds.connectAttr('%s.outTranslate' % shape, '%s.translate' % follicle)
    cmds.connectAttr('%s.outRotate' % shape, '%s.rotate' % follicle)
    
    cmds.setAttr('%s.parameterU' % follicle, uv[0])
    cmds.setAttr('%s.parameterV' % follicle, uv[1])
    
    return follicle

def transforms_to_nurb_surface(transforms, description, spans = -1, offset_axis = 'Y', offset_amount = 1):
    
    transform_positions_1 = []
    transform_positions_2 = []
    
    for transform in transforms:
        
        transform_1 = cmds.group(em = True)
        transform_2 = cmds.group(em = True)
        
        MatchSpace(transform, transform_1).translation_rotation()
        MatchSpace(transform, transform_2).translation_rotation()
        
        vector = get_axis_vector(offset_axis)
        
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

def transforms_to_curve(transforms, spans, description):
    transform_positions = []
        
    for joint in transforms:
        joint_position = cmds.xform(joint, q = True, ws = True, t = True)
        
        transform_positions.append( joint_position )
    
    curve = cmds.curve(p = transform_positions, degree = 1)
    
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
    
    curve = cmds.rename( curve, inc_name('curve_%s' % description) )
    
    cmds.setAttr('%s.inheritsTransform' % curve, 0)
    
    return curve
    
def transforms_to_joint_chain(transforms, name = ''):
    
    cmds.select(cl = True)
    
    joints = []
    
    for transform in transforms:
    
        if not name:
            name = transform     
            
        joint = cmds.joint(n = inc_name('joint_%s' % name))
        
        MatchSpace(transform, joint).translation_rotation()
        
        joints.append(joint)
        
    return joints
    
def curve_to_nurb_surface(curve):
    pass
    
def edges_to_curve(edges, description):
    
    cmds.select(edges)
    
    curve =  cmds.polyToCurve(form = 2, degree = 3 )[0]
    
    curve = cmds.rename(curve, inc_name('curve_%s' % description))
    
    return curve
    
def get_closest_parameter_on_curve(curve, three_value_list):
    
    curve_shapes = get_shapes(curve)
    
    if curve_shapes:
        curve = curve_shapes[0]
    
    curveObject = nodename_to_mobject(curve)
    curve = NurbsCurveFunction(curveObject)
        
    newPoint = curve.get_closest_position( three_value_list )
    
    return curve.get_parameter_at_position(newPoint)

def get_closest_parameter_on_surface(surface, vector):
    shapes = get_shapes(surface)
    
    if shapes:
        surface = shapes[0]
    
    surfaceObject = nodename_to_mobject(surface)
    surface = NurbsSurfaceFunction(surfaceObject)
        
    uv = surface.get_closest_parameter(vector)
    
    uv = list(uv)
    
    if uv[0] == 0:
        uv[0] = 0.001
    
    if uv[1] == 0:
        uv[1] = 0.001
    
    return uv

def get_closest_position_on_curve(curve, three_value_list):
    
    curve_shapes = get_shapes(curve)
    
    if curve_shapes:
        curve = curve_shapes[0]
    
    curveObject = nodename_to_mobject(curve)
    curve = NurbsCurveFunction(curveObject)
        
    return curve.get_closest_position( three_value_list )

def get_parameter_from_curve_length(curve, length_value):
    curve_shapes = get_shapes(curve)
    
    if curve_shapes:
        curve = curve_shapes[0]
        
    curveObject = nodename_to_mobject(curve)
    curve = NurbsCurveFunction(curveObject)
    
    return curve.get_parameter_at_length(length_value)

def get_point_from_curve_parameter(curve, parameter):
    
    return cmds.pointOnCurve(curve, pr = parameter, ch = False)

def create_oriented_joints_on_curve(curve, count = 20, description = None, rig = False):
    
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
    
    joints = subdivide_joint(start_joint, end_joint, count, 'joint', description)
    
    joints.insert(0, start_joint)
    joints.append(end_joint)
    
    new_joint = []
    
    for joint in joints:
        new_joint.append( cmds.rename(joint, inc_name('joint_%s_1' % curve)) )
    
    ik = IkHandle(curve)
    ik.set_start_joint(new_joint[0])
    ik.set_end_joint(new_joint[-1])
    ik.set_solver(ik.solver_spline)
    ik.set_curve(curve)
    
    ik_handle = ik.create()
    cmds.refresh()
    cmds.delete(ik_handle)
    
    cmds.makeIdentity(new_joint[0], apply = True, r = True)
    
    ik = IkHandle(curve)
    ik.set_start_joint(new_joint[0])
    ik.set_end_joint(new_joint[-1])
    ik.set_solver(ik.solver_spline)
    ik.set_curve(curve)
    
    ik_handle = ik.create()  
      
    
    if not rig:
        cmds.refresh()
        cmds.delete(ik_handle)
        return new_joint
        
    if rig:
        create_spline_ik_stretch(curve, new_joint, curve, create_stretch_on_off = False)    
        return new_joint, ik_handle
    
    

def create_joints_on_curve(curve, joint_count, description, attach = True, create_controls = False):
    
    group = cmds.group(em = True, n = inc_name('joints_%s' % curve))
    control_group = None
    
    if create_controls:
        control_group = cmds.group(em = True, n = inc_name('controls_%s' % curve))
        cmds.addAttr(control_group, ln = 'twist', k = True)
        cmds.addAttr(control_group, ln = 'offsetScale', min = -1, dv = 0, k = True)
    
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
            
        joint = cmds.joint(p = position, n = inc_name('joint_%s' % description) )
        
        cmds.addAttr(joint, ln = 'param', at = 'double', dv = param)
        
        if joints:
            cmds.joint(joints[-1], 
                       e = True, 
                       zso = True, 
                       oj = "xyz", 
                       sao = "yup")
        
        if attach:
            attach_node = attach_to_curve( joint, curve, parameter = param )
            
            cmds.parent(joint, group)
        
        current_length += part_length
        
        if create_controls:
            control = Control(inc_name('CNT_TWEAKER_%s' % description.upper()))
            control.set_curve_type('pin')
            control.rotate_shape(90, 0, 0)
            control.hide_visibility_attribute()
            
            control_name = control.get()  
            
            parameter_value = cmds.getAttr('%s.parameter' % attach_node)
            
            percent_var = MayaNumberVariable('percent')
            percent_var.set_min_value(0)
            percent_var.set_max_value(10)
            percent_var.set_value(parameter_value*10)
            percent_var.create(control_name)
            
            connect_multiply(percent_var.get_name(), '%s.parameter' % attach_node, 0.1)
            
            xform = create_xform_group(control_name)

            cmds.connectAttr('%s.positionX' % attach_node, '%s.translateX'  % xform)
            cmds.connectAttr('%s.positionY' % attach_node, '%s.translateY'  % xform)
            cmds.connectAttr('%s.positionZ' % attach_node, '%s.translateZ'  % xform)
            
            side = control.color_respect_side(True, 0.1)
            
            if side != 'C':
                control_name = cmds.rename(control_name, inc_name(control_name[0:-3] + '1_%s' % side))
            
            connect_translate(control_name, joint)
            connect_rotate(control_name, joint)

            offset = vtool.util.fade_sine(percent)
            
            multiply = MultiplyDivideNode(control_group)
            
            multiply = MultiplyDivideNode(control_group)
            multiply.input1X_in('%s.twist' % control_group)
            multiply.set_input2(offset)
            multiply.outputX_out('%s.rotateX' % joint)            

            plus = cmds.createNode('plusMinusAverage', n = 'plus_%s' % control_group)
            cmds.setAttr('%s.input1D[0]' % plus, 1)
            
            connect_multiply('%s.offsetScale' % control_group, '%s.input1D[1]' % plus, offset, plus = False)

            multiply = MultiplyDivideNode(control_group)
            
            multiply.input1X_in('%s.output1D' % plus)
            multiply.input1Y_in('%s.output1D' % plus)
            multiply.input1Z_in('%s.output1D' % plus)
            
            multiply.input2X_in('%s.scaleX' % control_name)
            multiply.input2Y_in('%s.scaleY' % control_name)
            multiply.input2Z_in('%s.scaleZ' % control_name)
            
            multiply.outputX_out('%s.scaleX' % joint)
            multiply.outputY_out('%s.scaleY' % joint)
            multiply.outputZ_out('%s.scaleZ' % joint)

            cmds.parent(xform, control_group)
            
        joints.append(joint)
    
        percent += segment
    
    
    
    if not attach:
        cmds.parent(joints[0], group)
    
    
    
    return joints, group, control_group

def create_ghost_chain(transforms):
    
    last_ghost = None
    
    ghosts = []
    
    for transform in transforms:
        ghost = cmds.duplicate(transform, po = True, n = 'ghost_%s' % transform)[0]
        cmds.parent(ghost, w = True)
        
        MatchSpace(transform, ghost).translation_rotation()
        
        xform = create_xform_group(ghost)
        
        target_offset = create_xform_group(transform)
        
        connect_translate(ghost, target_offset)
        connect_rotate(ghost, target_offset)
        
        if last_ghost:
            cmds.parent(xform, last_ghost )
        
        last_ghost = ghost
        
        ghosts.append(ghost)

    return ghosts
        

def snap_joints_to_curve(joints, curve = None, count = 10):
    
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
            joint = cmds.rename(joint, inc_name(joints[-1]))
            
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

def convert_indices_to_mesh_vertices(indices, mesh):
    verts = []
    
    for index in indices:
        verts.append('%s.vtx[%s]' % (mesh, index))
        
    return verts

def get_vertex_normal(vert_name):
    normal = cmds.polyNormalPerVertex(vert_name, q = True, normalXYZ = True)
    normal = normal[:3]
    return vtool.util.Vector(normal)

def add_poly_smooth(mesh):
    
    return cmds.polySmooth(mesh, mth = 0, dv = 1, bnr = 1, c = 1, kb = 0, khe = 0, kt = 1, kmb = 1, suv = 1, peh = 0, sl = 1, dpe = 1, ps = 0.1, ro = 1, ch = 1)[0]
    

#---deformation
    


    
    
def cluster_curve(curve, description, join_ends = False, join_start_end = False, last_pivot_end = False):
    
    clusters = []
    
    cvs = cmds.ls('%s.cv[*]' % curve, flatten = True)
    
    cv_count = len(cvs)
    
    start_inc = 0
    
    if join_ends and not join_start_end:
        cluster = cmds.cluster('%s.cv[0:1]' % curve, n = inc_name(description))[1]
        position = cmds.xform('%s.cv[0]' % curve, q = True, ws = True, t = True)
        cmds.xform(cluster, ws = True, rp = position, sp = position)
        clusters.append(cluster)
        
        last_cluster = cmds.cluster('%s.cv[%s:%s]' % (curve,cv_count-2, cv_count-1), n = inc_name(description))[1]
        
        if not last_pivot_end:
            position = cmds.xform('%s.cv[%s]' % (curve,cv_count-2), q = True, ws = True, t = True)
        if last_pivot_end:
            position = cmds.xform('%s.cv[%s]' % (curve,cv_count-1), q = True, ws = True, t = True)
            
        cmds.xform(last_cluster, ws = True, rp = position, sp = position)
            
        
        start_inc = 2
        
        cvs = cvs[2:cv_count-2]
        cv_count = len(cvs)+2
        
    if join_start_end:
        joined_cvs = ['%s.cv[0:1]' % curve,'%s.cv[%s:%s]' % (curve, cv_count-2, cv_count-1)]
        
        cluster = cmds.cluster(joined_cvs, n = inc_name(description))[1]
        position = cmds.xform('%s.cv[0]' % curve, q = True, ws = True, t = True)
        cmds.xform(cluster, ws = True, rp = position, sp = position)
        clusters.append(cluster)
        
        start_inc = 2
        
        cvs = cvs[2:cv_count-2]
        cv_count = len(cvs)+2
    
    for inc in range(start_inc, cv_count):
        cluster = cmds.cluster( '%s.cv[%s]' % (curve, inc), n = inc_name(description) )[1]
        clusters.append(cluster)
    
    if join_ends and not join_start_end:
        clusters.append(last_cluster)
    
    return clusters

def create_cluster(points, name):
    
    cluster, handle = cmds.cluster(points, n = inc_name('cluster_%s' % name))
    
    return cluster, handle

def create_cluster_bindpre(cluster, handle):
    
    #cluster_parent = cmds.listRelatives(handle, p = True)
    
    bindpre = cmds.duplicate(handle, n = 'bindPre_%s' % handle)[0]
    shapes = get_shapes(bindpre)
    if shapes:
        cmds.delete(shapes)
    
    cmds.connectAttr('%s.worldInverseMatrix' % bindpre, '%s.bindPreMatrix' % cluster)
    
    #if cluster_parent:
        #cmds.parent(bindpre, cluster_parent[0])
    
    return bindpre

def create_lattice(points, description, divisions = (3,3,3), falloff = (2,2,2)):
    
    
    
    ffd, lattice, base = cmds.lattice(points, 
                                      divisions = divisions, 
                                      objectCentered = True, 
                                      ldv = falloff, n = 'ffd_%s' % description)
    
    

def find_deformer_by_type(mesh, deformer_type, return_all = False):
    
    scope = cmds.listHistory(mesh, interestLevel = 1)
    
    found = []
    
    for thing in scope[1:]:
        if cmds.nodeType(thing) == deformer_type:
            if not return_all:
                return thing
            
            found.append(thing)
            
        if cmds.objectType(thing, isa = "shape") and not cmds.nodeType(thing) == 'lattice':
            return found
        
    return found

def get_influences_on_skin(skin_deformer):
    indices = get_indices('%s.matrix' % skin_deformer)
       
    influences = []
       
    for index in indices:
        influences.append( get_skin_influence_at_index(index, skin_deformer) )
        
    return influences

def get_non_zero_influences(skin_deformer):
    influences = cmds.skinCluster(skin_deformer, q = True, wi = True)
    
    return influences
    
def get_index_at_skin_influence(influence, skin_deformer):
    indices = get_indices('%s.matrix' % skin_deformer)
          
    for index in indices:
        found_influence = get_skin_influence_at_index(index, skin_deformer)
                
        if influence == found_influence:
            return index
        
def get_skin_influence_at_index(index, skin_deformer):
    influence_slot = '%s.matrix[%s]' % (skin_deformer, index) 
    
    connection = get_attribute_input( influence_slot )
    
    if connection:
        connection = connection.split('.')
        return connection[0]    

def get_skin_influence_indices(skin_deformer):
    return get_indices('%s.matrix' % skin_deformer)

def get_skin_influences(skin_deformer, return_dict = False):
    indices = get_skin_influence_indices(skin_deformer)
    
    if not return_dict:
        found_influences = []
    if return_dict:
        found_influences = {}
    
    for index in indices:
        influence = get_skin_influence_at_index(index, skin_deformer)
        
        if not return_dict:
            found_influences.append(influence)
        if return_dict:
            found_influences[influence] = index
        
    return found_influences

def get_meshes_skinned_to_joint(joint):
    
    skins = cmds.ls(type = 'skinCluster')
    
    found = []
    
    for skin in skins:
        influences = get_skin_influences(skin)
        
        if joint in influences:
            geo = cmds.deformer(skin, q = True, geometry = True)
            
            geo_parent = cmds.listRelatives(geo, p = True)
            
            found += geo_parent
        
    return found
    
    
def get_skin_weights(skin_deformer):
    value_map = {}
    
    indices = get_indices('%s.weightList' % skin_deformer)
    
    for inc in range(0, len(indices)):
        
        influence_indices = get_indices('%s.weightList[ %s ].weights' % (skin_deformer, inc))
        
        if influence_indices:        
            for influence_index in influence_indices:
                                
                value = cmds.getAttr('%s.weightList[%s].weights[%s]' % (skin_deformer, inc, influence_index))
                
                if value < 0.0001:
                    continue
                
                if not influence_index in value_map:
                    
                    value_map[influence_index] = []
                    
                    for inc2 in range(0, len(indices)):
                        value_map[influence_index].append(0.0)

                if value:
                    value_map[influence_index][inc] = value
                
    return value_map

def set_skin_weights_to_zero(skin_deformer):
    weights = cmds.ls('%s.weightList[*]' % skin_deformer)
        
    for weight in weights:
            
        weight_attributes = cmds.listAttr('%s.weights' % (weight), multi = True)
            
        for weight_attribute in weight_attributes:
            cmds.setAttr('%s.%s' % (skin_deformer, weight_attribute), 0)

def set_vert_weights_to_zero(vert_index, skin_deformer, joint = None):
    
    influences = cmds.listAttr('%s.weightList[ %s ].weights' % (skin_deformer, vert_index), multi = True )
    
    index = None
    
    if joint:
        index = get_index_at_skin_influence(joint, skin_deformer)
    
    if not index:
        for influence in influences:
            cmds.setAttr('%s.%s' % (skin_deformer, influence), 0.0)
            
    if index:
        cmds.setAttr('%s.%s' % (skin_deformer, index), 0.0)   

def set_deformer_weights(weights, deformer, index = 0):
    
    for inc in range(0, len(weights) ):    
        cmds.setAttr('%s.weightList[%s].weights[%s]' % (deformer, index, inc), weights[inc])
    
def set_wire_weights(weights, wire_deformer, index = 0):
    #might need refresh 
    
    set_deformer_weights(weights, wire_deformer, index)
    
def get_deformer_weights(deformer, mesh, index = 0):

    indices = cmds.ls('%s.vtx[*]' % mesh, flatten = True)
        
    weights = []
    
    for inc in range(0, len(indices)):
        weights.append( cmds.getAttr('%s.weightList[%s].weights[%s]' % (deformer, index, inc)) )
    
    return weights

def get_wire_weights(wire_deformer, mesh, index = 0):
    
    get_deformer_weights(wire_deformer, mesh, index)

def get_cluster_weights(cluster_deformer, mesh, index = 0):
    return get_deformer_weights(cluster_deformer, mesh, index)

def get_blendshape_weights(blendshape_deformer, mesh, index = -1):
    pass

def get_intermediate_object(transform):
    
    shapes = cmds.listRelatives(transform, s = True)
    
    return shapes[-1]

def create_mesh_from_shape(shape, name = 'new_mesh'):
    
    parent = cmds.listRelatives(shape, p = True)[0]
    
    new_shape = cmds.createNode('mesh')
    
    mesh = cmds.listRelatives(new_shape, p = True)[0]
    
    cmds.connectAttr('%s.outMesh' % shape, '%s.inMesh' % new_shape)
    
    #cmds.dgdirty(a = True)
    #cmds.hide(new_shape)
    cmds.refresh()
    
    cmds.disconnectAttr('%s.outMesh' % shape, '%s.inMesh' % new_shape)
    
    mesh = cmds.rename(mesh, name)
    
    MatchSpace(parent, mesh).translation_rotation()
    
    
    
    return mesh
    

def invert_blendshape_weight(blendshape_deformer, index = -1):
    pass

def set_all_weights_on_wire(wire_deformer, weight, mesh = None, slot = 0):
    
    if not mesh:
        indices = get_indices('%s.weightList[%s]' % (wire_deformer,slot))
    if mesh:
        indices = cmds.ls('%s.vtx[*]' % mesh, flatten = True)    
    
    for inc in range(0, len(indices) ):
        cmds.setAttr('%s.weightList[%s].weights[%s]' % (wire_deformer, slot, inc), weight)

def set_wire_weights_from_skin_influence(wire_deformer, skin_deformer, influence):
    index = get_index_at_skin_influence(influence, skin_deformer)
    
    if index == None:
        return
    
    weights = get_skin_weights(skin_deformer)
    
    weight = weights[index]
    
    set_wire_weights(weight, wire_deformer)

def prune_wire_weights(deformer, mesh, value = 0.0001):
    
    verts = cmds.ls('%s.vtx[*]' % mesh, flatten = True)
    
    found_verts = []
    
    for inc in range(0, len(verts)):
        weight_value = cmds.getAttr('%s.weightList[%s].weights[%s]' % (deformer, 0, inc))
        
        if weight_value < value:
            found_verts.append('%s.vtx[%s]' % (mesh, inc))
    
    cmds.sets(found_verts, rm = '%sSet' % deformer  )
    

def get_skin_weights_at_verts(verts, skin_deformer):
    value_map = {}
    
    for vert in verts:
        vertIndex = int(vert)
        
        influences = cmds.listAttr('%s.weightList[ %s ].weights' % (skin_deformer, vertIndex), multi = True )
        
        influence_count = len(influences)
        min_value = 1.0/influence_count
        top_value = 1.0 - min_value
                
        found_value = [None, 0]
                            
        for influence in influences:
            index = re.findall('\d+', influence)[1]
            value = cmds.getAttr('%s.%s' % (skin_deformer, influence))

            if influence_count == 1:
                found_value = [index, value]
                break

            if value < min_value:
                continue
            
            if value == 0:
                continue
            
            if value >= top_value:
                found_value = [index, value]
                break
                                                
            if value >= found_value[1]:
                found_value = [index, value]
        
        index, value = found_value
                    
        if not value_map.has_key(index):
            value_map[index] = value
    
        if value_map.has_key(index):
            value_map[index] += value

    return value_map

def get_faces_at_skin_influence(mesh, skin_deformer):
    scope = cmds.ls('%s.f[*]' % mesh, flatten = True)
    
    index_face_map = {}
    
    inc = 0
    
    for face in scope:
            
        inc += 1
           
        verts = cmds.polyInfo(face, fv = True)
        verts = verts[0].split()
        verts = verts[2:]
        
        value_map = get_skin_weights_at_verts(verts, skin_deformer)
        
        good_index = None
        last_value = 0
        
        for index in value_map:
            value = value_map[index]
            
            if value > last_value:
                good_index = index
                last_value = value
                                
        if not index_face_map.has_key(good_index):
            index_face_map[good_index] = []
            
        index_face_map[good_index].append(face)
        
    return index_face_map

def split_mesh_at_skin(mesh, skin_deformer = None, vis_attribute = None, constrain = False):
    
    if constrain:
        group = cmds.group(em = True, n = inc_name('split_%s' % mesh))
    
    if not skin_deformer:
        skin_deformer =  find_deformer_by_type(mesh, 'skinCluster')
    
    index_face_map = get_faces_at_skin_influence(mesh, skin_deformer)

    cmds.undoInfo(state = False)
    cmds.hide(mesh)
    
    main_duplicate = cmds.duplicate(mesh)[0]
    unlock_attributes(main_duplicate)
    #clean shapes
    shapes = cmds.listRelatives(main_duplicate, shapes = True)
    cmds.delete(shapes[1:])
        
    for key in index_face_map:
        
        duplicate_mesh = cmds.duplicate(main_duplicate)[0]
        
        scope = cmds.ls('%s.f[*]' % duplicate_mesh, flatten = True)
        cmds.select(scope, r = True)
        
        faces = []
        
        for face in index_face_map[key]:
            face_name = face.replace(mesh, duplicate_mesh)
            faces.append(face_name)
        
        cmds.select(faces, d = True)
        cmds.delete()
        
        influence = get_skin_influence_at_index(key, skin_deformer)
        
        if not constrain:
            cmds.parent(duplicate_mesh, influence)
        if constrain:
            follow = create_follow_group(influence, duplicate_mesh)
            connect_scale(influence, follow)
            #cmds.parentConstraint(influence, duplicate_mesh, mo = True)
            cmds.parent(follow, group)
        
        if vis_attribute:
            cmds.connectAttr(vis_attribute, '%s.visibility' % duplicate_mesh)
    
    cmds.undoInfo(state = True)
    cmds.showHidden(mesh)
    
    if constrain:
        return group

def transfer_weight(source_joint, target_joints, mesh):
    if not mesh:
        return
    
    skin_deformer = find_deformer_by_type(mesh, 'skinCluster')
    
    if not skin_deformer:
        return
    
    cmds.undoInfo(state = False)
    
    index = get_index_at_skin_influence(source_joint, skin_deformer)
    
    weights = get_skin_weights(skin_deformer)
    
    indices = get_indices('%s.matrix' % skin_deformer)
    last_index = indices[-1]
    
    weights = weights[index]
    weighted_verts = []
    vert_weights = {}
    
    for inc in range(0, len(weights)):
        if weights[inc] > 0:
            
            vert = '%s.vtx[%s]' % (mesh, inc)
            weighted_verts.append( vert )
            vert_weights[vert] = weights[inc]
    
    joint_vert_map = get_closest_verts_to_joints(target_joints, weighted_verts)
    
    influences = get_influences_on_skin(skin_deformer)
    
    for influence in influences:
        if influence != source_joint:
            cmds.skinCluster(skin_deformer, e = True, inf = influence, lw = True)
        if influence == source_joint:
            cmds.skinCluster(skin_deformer, e = True, inf = influence, lw = False)
    
    for joint in target_joints:
        
        if not joint in joint_vert_map:
            continue
        
        cmds.skinCluster(skin_deformer, e = True, ai = joint, wt = 0.0, nw = 1)
        
        verts = joint_vert_map[joint]
        
        inc = 0
        
        for vert in verts:
            
            cmds.skinPercent(skin_deformer, vert, r = True, transformValue = [joint, vert_weights[vert]])
            inc += 1
        
        cmds.skinCluster(skin_deformer,e=True,inf=joint,lw = True)
        
        last_index += 1
        
    cmds.undoInfo(state = True)
    
def add_joint_bindpre(skin, joint, description):
    bindPre_locator = cmds.spaceLocator(n = inc_name('locator_%s' % description))[0]
    #cmds.parent(bindPre_locator, bindPre_locator_group)
    
    index = get_index_at_skin_influence(joint, skin)
    
    match = MatchSpace(joint, bindPre_locator)
    match.translation_rotation()
        
    #attach_to_curve(bindPre_locator, base_curve)
    
    cmds.connectAttr('%s.worldInverseMatrix' % bindPre_locator, '%s.bindPreMatrix[%s]' % (skin, index))
    
    return bindPre_locator

def convert_joint_to_nub(start_joint, end_joint, count, prefix, name, side, mid_control = True):
    #joints = subdivide_joint(start_joint, end_joint, count, prefix, name, True)
    joints = subdivide_joint(start_joint, end_joint, count, prefix, '%s_1_%s' % (name,side), True)
    
    
    rig = IkSplineNubRig(name, side)
    rig.set_joints(joints)
    rig.set_end_with_locator(True)
    rig.set_create_middle_control(mid_control)
    #rig.set_guide_top_btm(start_joint, end_joint)
    rig.create()
    
    cmds.parent(joints[0], rig.setup_group)
    
    return rig.control_group, rig.setup_group
    



def convert_wire_deformer_to_skin(wire_deformer, description, joint_count = 10, delete_wire = True, skin = True, falloff = 1, create_controls = True):
    #do not remove print
    print 'converting %s' % wire_deformer
    
    convert_group = cmds.group(em = True, n = inc_name('convertWire_%s' % description))
    bindPre_locator_group = cmds.group(em = True, n = inc_name('convertWire_bindPre_%s' % description))
    
    cmds.parent(bindPre_locator_group, convert_group)
    
    cmds.hide(bindPre_locator_group)
    
    curve = get_attribute_input('%s.deformedWire[0]' % wire_deformer, node_only = True)
    
    curve = cmds.listRelatives(curve, p = True)[0]
    
    base_curve = get_attribute_input('%s.baseWire[0]' % wire_deformer, node_only= True)
    base_curve = cmds.listRelatives(base_curve, p = True)[0]
    
    
    joints, joints_group, control_group = create_joints_on_curve(curve, joint_count, description, create_controls = create_controls)
    
    meshes = cmds.deformer(wire_deformer, q = True, geometry = True)
    if not meshes:
        return
    
    inc = 0
    
    for mesh in meshes:
        zero_verts = []
        
        if not skin:
            skin_cluster = find_deformer_by_type(mesh, 'skinCluster')
            
            if not skin_cluster:
                cmds.select(cl = True)
                base_joint = cmds.joint(n = 'joint_%s' % wire_deformer)
            
                skin_cluster = cmds.skinCluster(base_joint, mesh, tsb = True)[0]
            
                cmds.parent(base_joint, convert_group)
            
            for joint in joints:
                found_skin = find_deformer_by_type(mesh, 'skinCluster')
                
                cmds.skinCluster(skin_cluster, e = True, ai = joint, wt = 0.0, nw = 1)     
                bindPre_locator = add_joint_bindpre(found_skin, joint, description)
                cmds.parent(bindPre_locator, bindPre_locator_group)
                
                parameter = cmds.getAttr('%s.param' % joint)
                attach_to_curve(bindPre_locator, base_curve, True, parameter) 
                
        if skin:
            verts = cmds.ls('%s.vtx[*]' % mesh, flatten = True)
            
            wire_weights = get_wire_weights(wire_deformer, mesh, inc)
            
            weighted_verts = []
            weights = {}
            verts_inc = {}
            
            for inc in range(0, len(wire_weights)):
                if wire_weights[inc] > 0:
                    weighted_verts.append(verts[inc])
                    weights[verts[inc]] = wire_weights[inc]
                    verts_inc[verts[inc]] = inc
            
            #joint_vert_map = get_closest_verts_to_joints(joints, weighted_verts)
            
            skin_cluster = find_deformer_by_type(mesh, 'skinCluster')
            
            base_joint = None
            
            if not skin_cluster:
                cmds.select(cl = True)
                base_joint = cmds.joint(n = 'joint_%s' % wire_deformer)
                
                skin_cluster = cmds.skinCluster(base_joint, mesh, tsb = True)[0]
                
                cmds.parent(base_joint, convert_group)
                
            if skin_cluster and not base_joint:
                base_joint = get_skin_influence_at_index(0, skin_cluster)
                
            #indices = get_indices('%s.matrix' % skin_cluster)
            #last_index = indices[-1]
            
            distance_falloff = falloff
            
            for joint in joints:
                
                cmds.skinCluster(skin_cluster, e = True, ai = joint, wt = 0.0, nw = 1)     
                bindPre_locator = add_joint_bindpre(skin_cluster, joint, description)
                cmds.parent(bindPre_locator, bindPre_locator_group)
                
                parameter = cmds.getAttr('%s.param' % joint)
                attach_to_curve(bindPre_locator, base_curve, True, parameter)
            
            
            for vert in weighted_verts:
                #vert_inc = verts_inc[vert]
    
                
                if weights[vert] < 0.0001:
                        continue
                
                distances = get_distances(joints, vert)
                
                
                joint_count = len(joints)
                
                smallest_distance = distances[0]
                distances_in_range = []
                smallest_distance_inc = 0
                
                for inc in range(0, joint_count):
                    if distances[inc] < smallest_distance:
                        smallest_distance_inc = inc
                        smallest_distance = distances[inc]
                
                distance_falloff = smallest_distance*1.3
                if distance_falloff < falloff:
                    distance_falloff = falloff
                
                for inc in range(0, joint_count):

                    if distances[inc] <= distance_falloff:
                        distances_in_range.append(inc)

                if smallest_distance >= distance_falloff or not distances_in_range:
                    
                    weight_value = weights[vert]
                    #base_value = 1.00-weight_value

                    cmds.skinPercent(skin_cluster, vert, r = False, transformValue = [joints[smallest_distance_inc], weight_value])

                    continue

                if smallest_distance <= distance_falloff or distances_in_range:

                    total = 0.0
                    
                    joint_weight = {}
                    
                    inverted_distances = {}
                    
                    for distance_inc in distances_in_range:
                        distance = distances[distance_inc]
                        
                        distance_weight = distance/distance_falloff
                        distance_weight = vtool.util.fade_sigmoid(distance_weight)
                        
                        inverted_distance = distance_falloff - distance*distance_weight*distance_weight
                        
                        inverted_distances[distance_inc] = inverted_distance
                        
                    for inverted_distance in inverted_distances:
                        total += inverted_distances[inverted_distance]
                        
                    for distance_inc in distances_in_range:
                        weight = inverted_distances[distance_inc]/total
                        
                        joint_weight[joints[distance_inc]] = weight
                    
                    weight_value = weights[vert]
                    #base_value = 1.00-weight_value
                    
                    segments = []
                    
                    for joint in joint_weight:
                        joint_value = joint_weight[joint]
                        value = weight_value*joint_value
                        
                        segments.append( (joint, value) )
                    
                    cmds.skinPercent(skin_cluster, vert, r = False, transformValue = segments)    
                        
                            
            for joint in joints:
                
                cmds.skinCluster(skin_cluster,e=True,inf=joint,lw = True)
        
        inc += 1
    
    cmds.setAttr('%s.envelope' % wire_deformer, 0)
    
    if delete_wire:
        disconnect_attribute('%s.baseWire[0]' % wire_deformer)
        cmds.delete(wire_deformer)
        
    cmds.parent(joints_group, convert_group)
    
    cmds.hide(convert_group)
    
    return convert_group, control_group, zero_verts



def convert_wire_to_skinned_joints(wire_deformer, description, joint_count = 10, falloff = 1):
    #do not remove print
    print 'converting %s' % wire_deformer
    
    convert_group = cmds.group(em = True, n = inc_name('convertWire_%s' % description))
    
    curve = get_attribute_input('%s.deformedWire[0]' % wire_deformer, node_only = True)
    curve = cmds.listRelatives(curve, p = True)[0]
    
    
    joints = create_oriented_joints_on_curve(curve, count = joint_count, rig = False)
    
    meshes = cmds.deformer(wire_deformer, q = True, geometry = True)
    if not meshes:
        return
    
    inc = 0
    
    for mesh in meshes:
        zero_verts = []
        skin = True
        """
        if not skin:
            skin_cluster = find_deformer_by_type(mesh, 'skinCluster')
            
            if not skin_cluster:
                cmds.select(cl = True)
                base_joint = cmds.joint(n = 'joint_%s' % wire_deformer)
            
                skin_cluster = cmds.skinCluster(base_joint, mesh, tsb = True)[0]
            
                cmds.parent(base_joint, convert_group)
            
            for joint in joints:
                found_skin = find_deformer_by_type(mesh, 'skinCluster')
                
                cmds.skinCluster(skin_cluster, e = True, ai = joint, wt = 0.0, nw = 1)     
        """                     
        if skin:
            verts = cmds.ls('%s.vtx[*]' % mesh, flatten = True)
            
            wire_weights = get_wire_weights(wire_deformer, mesh, inc)
            
            weighted_verts = []
            weights = {}
            verts_inc = {}
            
            for inc in range(0, len(wire_weights)):
                if wire_weights[inc] > 0:
                    weighted_verts.append(verts[inc])
                    weights[verts[inc]] = wire_weights[inc]
                    verts_inc[verts[inc]] = inc
            
            skin_cluster = find_deformer_by_type(mesh, 'skinCluster')
            
            base_joint = None
            
            if not skin_cluster:
                cmds.select(cl = True)
                base_joint = cmds.joint(n = 'joint_%s' % wire_deformer)
                
                skin_cluster = cmds.skinCluster(base_joint, mesh, tsb = True)[0]
                
                cmds.parent(base_joint, convert_group)
                
            if skin_cluster and not base_joint:
                base_joint = get_skin_influence_at_index(0, skin_cluster)
            
            distance_falloff = falloff
            
            for joint in joints:
                
                cmds.skinCluster(skin_cluster, e = True, ai = joint, wt = 0.0, nw = 1)     
            
            for vert in weighted_verts:
                
                if weights[vert] < 0.0001:
                        continue
                
                distances = get_distances(joints, vert)
                            
                joint_count = len(joints)
                
                smallest_distance = distances[0]
                distances_in_range = []
                smallest_distance_inc = 0
                
                for inc in range(0, joint_count):
                    if distances[inc] < smallest_distance:
                        smallest_distance_inc = inc
                        smallest_distance = distances[inc]
                
                distance_falloff = smallest_distance*1.3
                if distance_falloff < falloff:
                    distance_falloff = falloff
                
                for inc in range(0, joint_count):

                    if distances[inc] <= distance_falloff:
                        distances_in_range.append(inc)

                if smallest_distance >= distance_falloff or not distances_in_range:
                    
                    weight_value = weights[vert]

                    cmds.skinPercent(skin_cluster, vert, r = False, transformValue = [joints[smallest_distance_inc], weight_value])

                    continue

                if smallest_distance <= distance_falloff or distances_in_range:

                    total = 0.0
                    
                    joint_weight = {}
                    
                    inverted_distances = {}
                    
                    for distance_inc in distances_in_range:
                        distance = distances[distance_inc]
                        
                        distance_weight = distance/distance_falloff
                        distance_weight = vtool.util.fade_sigmoid(distance_weight)
                        
                        inverted_distance = distance_falloff - distance*distance_weight*distance_weight
                        
                        inverted_distances[distance_inc] = inverted_distance
                        
                    for inverted_distance in inverted_distances:
                        total += inverted_distances[inverted_distance]
                        
                    for distance_inc in distances_in_range:
                        weight = inverted_distances[distance_inc]/total
                        
                        joint_weight[joints[distance_inc]] = weight
                    
                    weight_value = weights[vert]
                    
                    segments = []
                    
                    for joint in joint_weight:
                        joint_value = joint_weight[joint]
                        value = weight_value*joint_value
                        
                        segments.append( (joint, value) )
                    
                    cmds.skinPercent(skin_cluster, vert, r = False, transformValue = segments)    
                                                
            for joint in joints:
                
                cmds.skinCluster(skin_cluster,e=True,inf=joint,lw = True)
        
        inc += 1
    
    cmds.setAttr('%s.envelope' % wire_deformer, 0)
        
    cmds.hide(convert_group)
    
    return convert_group

class WeightFade(object):
    
    def __init__(self, mesh):
        self.mesh = mesh
        self.joints = []
        self.verts = []
        self.joint_vectors_2D = []
        self.vertex_vectors_2D = []
        
        self._store_verts()
        self.multiplier_weights = []
        self.zero_weights = True
        
    def _store_verts(self):
        self.verts = cmds.ls('%s.vtx[*]' % self.mesh, flatten = True)
    
    def _get_joint_index(self, joint):
        for inc in range(0, len(self.joints)):
            if self.joints[inc] == joint:
                return inc
            
    def _store_vertex_vectors(self):
        self.vertex_vectors_2D = []
        self.vertex_vectors_3D = []
        self.vertex_normals = []
        
        for vert in self.verts:
            position = cmds.xform(vert, q = True, ws = True, t = True)
            position_vector_3D = vtool.util.Vector(position)
            position_vector_2D = vtool.util.Vector2D(position[0], position[2])
            
            normal_vector = get_vertex_normal(vert)

            self.vertex_vectors_2D.append(position_vector_2D)
            self.vertex_vectors_3D.append(position_vector_3D)
            self.vertex_normals.append(normal_vector)
                
    def _store_joint_vectors(self):
        
        self.joint_vectors_2D = []
        
        for joint in self.joints:
            position = cmds.xform(joint, q = True, ws = True, t = True)
            
            position = (position[0], position[2])
            
            self.joint_vectors_2D.append(position)
    
    def _get_adjacent(self, joint):
        
        joint_index = self._get_joint_index(joint)
        
        joint_count = len(self.joints)
        
        if joint_index == 0:
            return [1]
        
        if joint_index == joint_count-1:
            return [joint_index-1]
        
        return [joint_index+1, joint_index-1]

    def _skin(self):
        
        skin = find_deformer_by_type(self.mesh, 'skinCluster')
        
        joints = self.joints
        
        if not skin:
            skin = cmds.skinCluster(self.mesh, self.joints[0], tsb = True)[0]
            joints = joints[1:]
        
        if self.zero_weights:
            set_skin_weights_to_zero(skin)
        
        for joint in joints:
            cmds.skinCluster(skin, e = True, ai = joint, wt = 0.0)
            
        return skin
        
    def _weight_verts(self, skin):
        
        vert_count = len(self.verts)
        
        progress = ProgressBar('weighting %s:' % self.mesh, vert_count)
        
        for inc in range(0, vert_count):
            
            
            joint_weights = self._get_vert_weight(inc)

            if joint_weights:
                cmds.skinPercent(skin, self.verts[inc], r = False, transformValue = joint_weights)
            
            progress.inc()
            progress.status('weighting %s: vert %s' % (self.mesh, inc))
            if progress.break_signaled():
                progress.end()
                break
        
        progress.end()
            
    def _get_vert_weight(self, vert_index):
        
        if not self.multiplier_weights:
            multiplier = 1
            
        if self.multiplier_weights:
            multiplier = self.multiplier_weights[vert_index]
            
            if multiplier == 0 or multiplier < 0.0001:
                return
        
        vertex_vector = self.vertex_vectors_2D[vert_index]
        vertex_vector_3D = self.vertex_vectors_3D[vert_index]
        vertex_normal = self.vertex_normals[vert_index]
        
        joint_weights = []
        joint_count = len(self.joints)
        weight_total = 0
        
        for inc in range(0, joint_count):
            
            if inc == joint_count-1:
                break
            
            start_vector = vtool.util.Vector2D( self.joint_vectors_2D[inc] )
            joint_position = cmds.xform(self.joints[inc], q = True, ws = True, t = True)
            joint_vector = vtool.util.Vector(joint_position)
            check_vector = joint_vector - vertex_vector_3D
            
            dot_value = vtool.util.get_dot_product(vertex_normal, check_vector)
            
            if dot_value >= 0:
                continue
            
            joint = self.joints[inc]
            next_joint = self.joints[inc+1]
            
            end_vector = vtool.util.Vector2D( self.joint_vectors_2D[inc+1])
            
            percent = vtool.util.closest_percent_on_line_2D(start_vector, end_vector, vertex_vector, False)
            
            if percent <= 0:
                weight_total+=1.0
                if not weight_total > 1:
                    joint_weights.append([joint, (1.0*multiplier)])
                continue
                    
            if percent >= 1 and inc == joint_count-2:
                weight_total += 1.0
                if not weight_total > 1:
                    joint_weights.append([next_joint, (1.0*multiplier)])
                continue
            
            if percent > 1 or percent < 0:
                continue
            
            weight_total += 1.0-percent
            if not weight_total > 1:
                joint_weights.append([joint, ((1.0-percent)*multiplier)])
                
            weight_total += percent
            if not weight_total > 1:
                joint_weights.append([next_joint, percent*multiplier])
                
        return joint_weights
                
    def set_joints(self, joints):
        self.joints = joints
    
    def set_mesh(self, mesh):
        self.mesh = mesh
        
    def set_multiplier_weights(self, weights):
        self.multiplier_weights = weights
        
    def set_weights_to_zero(self, bool_value):
        self.zero_weights = bool_value
        
        
    def run(self):
        if not self.joints:
            return
        
        self._store_vertex_vectors()
        self._store_joint_vectors()
        skin = self._skin()
        
        self._weight_verts(skin)
        
def transfer_joint_weight_to_joint(source_joint, target_joint, mesh):
    if mesh:
        
        skin_deformer = find_deformer_by_type(mesh, 'skinCluster')
        
        influences = get_influences_on_skin(skin_deformer)
        
        if not target_joint in influences:
            cmds.skinCluster(skin_deformer, e = True, ai = target_joint, wt = 0.0, nw = 1)  
        
        index = get_index_at_skin_influence(source_joint, skin_deformer)
        
        if not index:
            warning( 'could not find index for %s on mesh %s' % (source_joint, mesh) )
            return
        
        other_index = get_index_at_skin_influence(target_joint, skin_deformer)
        
        weights = get_skin_weights(skin_deformer)
        
        cmds.setAttr('%s.normalizeWeights' % skin_deformer, 0)
        
        index_weights = weights[index]
        
        other_index_weights = None
        
        if other_index in weights:
            other_index_weights = weights[other_index]
        
        weight_count = len(index_weights)
        
        for inc in range(0,weight_count):
            
            if index_weights[inc] == 0:
                continue
            
            if other_index_weights == None:
                weight_value = index_weights[inc]
            
            if not other_index_weights == None:
                weight_value = index_weights[inc] + other_index_weights[inc]
            
            cmds.setAttr('%s.weightList[ %s ].weights[%s]' % (skin_deformer, inc, other_index), weight_value)
            cmds.setAttr('%s.weightList[ %s ].weights[%s]' % (skin_deformer, inc, index), 0)
        
        cmds.setAttr('%s.normalizeWeights' % skin_deformer, 1)
        cmds.skinCluster(skin_deformer, edit = True, forceNormalizeWeights = True)

def transfer_weight_from_joint_to_parent(joint, mesh):
    
    parent_joint = cmds.listRelatives(joint, type = 'joint', p = True)
    
    if parent_joint:
        parent_joint = parent_joint[0]
        
    if not parent_joint:
        return
    
    transfer_joint_weight_to_joint(joint, parent_joint, mesh)
   
def transfer_cluster_weight_to_joint(cluster, joint, mesh):
    skin = find_deformer_by_type(mesh, 'skinCluster')
    
    #index = get_index_at_skin_influence(joint, skin)
    
    weights = get_cluster_weights(cluster, mesh)
    
    for inc in range(0, len(weights)):
        
        vert = '%s.vtx[%s]' % (mesh, inc)
        
        cmds.skinPercent(skin, vert, r = False, transformValue = [joint, weights[inc]])
        #cmds.setAttr('%s.weightList[ %s ].weights[%s]' % (skin_deformer, inc, index), weights[inc])
    
def transfer_joint_weight_to_blendshape(blendshape, joint, mesh, index = 0, target = -1):
    
    skin = find_deformer_by_type(mesh, 'skinCluster')
    weights = get_skin_weights(skin)
    
    influence_index = get_index_at_skin_influence(joint, skin)
    
    weight_values = weights[influence_index]
    
    inc = 0
    
    if target == -1:
        for weight in weight_values:
            cmds.setAttr('%s.inputTarget[%s].baseWeights[%s]' % (blendshape, index, inc), weight)
            inc += 1
            
    if target >= 0:
        for weight in weight_values:
            cmds.setAttr('%s.inputTarget[%s].inputTargetGroup[%s].targetWeights[%s]' % (blendshape, index, target, inc), weight)
            inc += 1
    
   
def skin_mesh_from_mesh(source_mesh, target_mesh, exclude_joints = [], include_joints = [], uv_space = False):
    #do not remove print
    print 'skinning %s' % target_mesh
    cmds.undoInfo(state = False)
    skin = find_deformer_by_type(source_mesh, 'skinCluster')
    
    other_skin = find_deformer_by_type(target_mesh, 'skinCluster')
    
    if other_skin:
        warning('%s already has a skin cluster.' % target_mesh)
    
    influences = get_non_zero_influences(skin)
    
    for exclude in exclude_joints:
        if exclude in influences:
            influences.remove(exclude)
    
    if include_joints:
        found = []
        for include in include_joints:
            if include in influences:
                found.append(include)
        
        influences = found
    
    if not other_skin:  
        other_skin = cmds.skinCluster(influences, target_mesh, tsb=True, n = 'skin_%s' % target_mesh)[0]
        
    if other_skin:
        if not uv_space:
            cmds.copySkinWeights(ss = skin, 
                                 ds = other_skin, 
                                 noMirror = True, 
                                 surfaceAssociation = 'closestPoint', 
                                 influenceAssociation = ['closestJoint'], 
                                 normalize = True)
        
        if uv_space:
            cmds.copySkinWeights(ss = skin, 
                                 ds = other_skin, 
                                 noMirror = True, 
                                 surfaceAssociation = 'closestPoint', 
                                 influenceAssociation = ['closestJoint'],
                                 uvSpace = ['map1','map1'], 
                                 normalize = True)
            
    other_influences = cmds.skinCluster(other_skin, query = True, wi = True)
        
    for influence in influences:
        
        if not influence in other_influences:
            try:
                cmds.skinCluster(other_skin, edit = True, ri = influence)
            except:
                warning('Could not remove influence %s on mesh %s' % (influence, target_mesh))
                
    cmds.undoInfo(state = True)
      

def skin_group_from_mesh(source_mesh, group, include_joints = [], exclude_joints = []):
    
    old_selection = cmds.ls(sl = True)
    
    cmds.select(cl = True)
    cmds.select(group)
    cmds.refresh()
    
    relatives = cmds.listRelatives(group, ad = True, type = 'transform')
    relatives.append(group)
    
    for relative in relatives:
        
        shape = get_mesh_shape(relative)
        
        if shape and cmds.nodeType(shape) == 'mesh':
            skin_mesh_from_mesh(source_mesh, relative, include_joints = include_joints, exclude_joints = exclude_joints)
            
    if old_selection:
        cmds.select(old_selection)
    
def skin_lattice_from_mesh(source_mesh, target, divisions = [10,10,10], falloff = [2,2,2], name = None, include_joints = [], exclude_joints = []):
    
    group = cmds.group(em = True, n = 'lattice_%s_gr' % target)
    
    if not name:
        name = target
    
    ffd, lattice, base = cmds.lattice(target, 
                                      divisions = divisions, 
                                      objectCentered = True, 
                                      ldv = falloff, n = 'lattice_%s' % name)
    
    cmds.parent(lattice, base, group)
    cmds.hide(group)
    
    skin_mesh_from_mesh(source_mesh, lattice, exclude_joints = exclude_joints, include_joints = include_joints)
    
    return group

def skin_curve_from_mesh(source_mesh, target, include_joints = [], exclude_joints = []):
    
    skin_mesh_from_mesh(source_mesh, target, exclude_joints = exclude_joints, include_joints = include_joints)


def lock_joints(skin_cluster, skip_joints = None):
    influences = get_influences_on_skin(skin_cluster)
        
        
    if skip_joints:
        for influence in influences:
            cmds.skinCluster( skin_cluster, e= True, inf= influence, lw = False )
        
    for influence in influences:
        
        lock = True
          
        for joint in skip_joints:
            if joint == influence:
                lock = False
                break
            
        if lock:
            cmds.skinCluster( skin_cluster, e= True, inf= influence, lw = True )    

def get_closest_verts_to_joints(joints, verts):

    distance_dict = {}

    for joint in joints:
        
        joint_pos = cmds.xform(joint, q = True, ws = True, t = True)
        
        for vert in verts:
            
            if not vert in distance_dict:
                distance_dict[vert] = [10000000000000000000, None]
            
            pos = cmds.xform(vert, q = True, ws = True, t = True)
            
            distance = vtool.util.get_distance(joint_pos, pos)
            
            if distance < distance_dict[vert][0]:
                distance_dict[vert][0] = distance
                distance_dict[vert][1] = joint
    
    joint_map = {}
    
    for key in distance_dict:
        
        joint = distance_dict[key][1]
        
        if not joint in joint_map:
            joint_map[joint] = []
            
        joint_map[joint].append(key)
        
    return joint_map    

def create_wrap(source_mesh, target_mesh):
    wrap = MayaWrap(target_mesh)
    wrap.set_driver_meshes([source_mesh])
    
    wrap.create()
    
    return wrap.base_meshes
    
def weight_hammer_verts(verts = None, print_info = True):
    
    if verts:
        verts = cmds.ls(verts, flatten = True)
    
    if not verts:
        verts = cmds.ls(sl = True, flatten = True)
    
    count = len(verts)
    inc = 0
    
    cmds.undoInfo(state = False)
    
    for vert in verts:
        cmds.select(cl = True)
        cmds.select(vert)
        
        if print_info:
            #do not remove print
            print inc, 'of', count
        
        mel.eval('weightHammerVerts;')
            
        inc += 1
        
        
    cmds.undoInfo(state = True)

def exclusive_bind_wrap(source_mesh, target_mesh):
    wrap = MayaWrap(target_mesh)
    
    if type(source_mesh) == type(u'') or type(source_mesh) == type(''):
        wrap.set_driver_meshes([source_mesh])
        
    if type(source_mesh) == list:
        wrap.set_driver_meshes(source_mesh)
        
    wraps = wrap.create()
    
    return wraps

def map_blend_target_alias_to_index(blendshape):
    
    aliases = cmds.aliasAttr(blendshape, query = True)
    
    alias_map = {}
    
    if not aliases:
        return
    
    for inc in range(0, len(aliases), 2):
        alias = aliases[inc]
        weight = aliases[inc+1]
        
        index = vtool.util.get_end_number(weight)
        
        alias_map[index] = alias
        
    return alias_map

def map_blend_index_to_target_alias(blendshape):
    aliases = cmds.aliasAttr(blendshape, query = True)
    
    alias_map = {}
    
    if not aliases:
        return
    
    for inc in range(0, len(aliases), 2):
        alias = aliases[inc]
        weight = aliases[inc+1]
        
        index = vtool.util.get_end_number(weight)
        
        alias_map[alias] = index
        
    return alias_map

def get_index_at_alias(alias, blendshape):
    map = map_blend_index_to_target_alias(blendshape)
    
    if alias in map:
        return map[alias]
    
def chad_extract_shape(skin_mesh, corrective):
    
    try:
    
        envelopes = EnvelopeHistory(skin_mesh)
        
        skin = find_deformer_by_type(skin_mesh, 'skinCluster')
        
        if not skin:
            warning('No skin found on %s.' % skin_mesh)
            return
        
        file_name = __file__
        file_name = file_name.replace('util.py', 'cvShapeInverterDeformer.py')
        file_name = file_name.replace('.pyc', '.py')
        
        cmds.loadPlugin( file_name )
        
        import cvShapeInverterScript as correct
        
        envelopes.turn_off()
        cmds.setAttr('%s.envelope' % skin, 1)
        
        offset = correct.invert(skin_mesh, corrective)
        cmds.delete(offset, ch = True)
        
        orig = get_intermediate_object(skin_mesh)
        orig = create_mesh_from_shape(orig, 'home')
        
        envelopes.turn_on(respect_initial_state=True)
        
        cmds.setAttr('%s.envelope' % skin, 0)
        other_delta = cmds.duplicate(skin_mesh)[0]
        
        cmds.setAttr('%s.envelope' % skin, 1)
        
        quick_blendshape(other_delta, orig, -1)
        quick_blendshape(offset, orig, 1)
        
        cmds.select(cl = True)
        
        cmds.delete(orig, ch = True)
        
        cmds.delete(other_delta, offset)
        
        
        cmds.rename(orig, offset)
        
        
        
        return offset

    except Exception:
        RuntimeError( traceback.format_exc() )
        


def create_surface_joints(surface, name, uv_count = [10, 4], offset = 0):
    
    section_u = (1.0-offset*2) / (uv_count[0]-1)
    section_v = (1.0-offset*2) / (uv_count[1]-1)
    section_value_u = 0 + offset
    section_value_v = 0 + offset
    
    top_group = cmds.group(em = True, n = inc_name('rivetJoints_1_%s' % name))
    joints = []
    
    for inc in range(0, uv_count[0]):
        
        for inc2 in range(0, uv_count[1]):
            
            rivet = Rivet(name)
            rivet.set_surface(surface, section_value_u, section_value_v)
            rivet.set_create_joint(True)
            joint = rivet.create()
            cmds.parent(joint, top_group)
            joints.append(joint)
            
            section_value_v += section_v
        
        section_value_v = 0 + offset
            
        section_value_u += section_u
        
        
        
    return top_group, joints
        
    
def quick_blendshape(source_mesh, target_mesh, weight = 1, blendshape = None):
    if not blendshape:
        blendshape = 'blendshape_%s' % target_mesh
    
    if cmds.objExists(blendshape):
        count = cmds.blendShape(blendshape, q= True, weightCount = True)
        cmds.blendShape(blendshape, edit=True, tc = False, t=(target_mesh, count+1, source_mesh, 1.0) )
        cmds.setAttr('%s.%s' % (blendshape, source_mesh), weight)
        
    if not cmds.objExists(blendshape):
        cmds.blendShape(source_mesh, target_mesh, tc = False, weight =[0,weight], n = blendshape, foc = True)
        
    return blendshape 
    


#---attributes

def get_inputs(node, node_only = True):
    
    if node_only:
        plugs = False
    if not node_only:
        plugs = True

    return cmds.listConnections(node,
                         connections = False,
                         destination = False,
                         source = True,
                         plugs = plugs,
                         skipConversionNodes = True
                         )

    
def get_outputs(node, node_only = True):
    
    if node_only:
        plugs = False
    if not node_only:
        plugs = True
    
    return cmds.listConnections(node, 
                                connections = plugs, 
                                destination = True, 
                                source = False,
                                plugs = plugs,
                                skipConversionNodes = True)    

def get_attribute_input(node_and_attribute, node_only = False):
    
    connections = []
    
    if cmds.objExists(node_and_attribute):
        
        connections = cmds.listConnections(node_and_attribute, 
                                           plugs = True, 
                                           connections = False, 
                                           destination = False, 
                                           source = True,
                                           skipConversionNodes = True)
        if connections:
            if not node_only:
                return connections[0]
            if node_only:
                return connections[0].split('.')[0]
                
        
def get_attribute_outputs(node_and_attribute, node_only = False):
    
    if cmds.objExists(node_and_attribute):
        
        plug = True
        if node_only:
            plug = False
        
        return cmds.listConnections(node_and_attribute, 
                                    plugs = plug, 
                                    connections = False, 
                                    destination = True, 
                                    source = False,
                                    skipConversionNodes = True)

def transfer_output_connections(source_node, target_node):
    
    outputs  = cmds.listConnections(source_node, 
                         plugs = True,
                         connections = True,
                         destination = True,
                         source = False)
    
    for inc in range(0, len(outputs), 2):
        new_attr = outputs[inc].replace(source_node, target_node)
        
        cmds.disconnectAttr(outputs[inc], outputs[inc+1])
        cmds.connectAttr(new_attr, outputs[inc+1], f = True)

def set_color(nodes, color):
    
    for node in nodes:
        overrideEnabled = '%s.overrideEnabled' % node
        overrideColor = '%s.overrideColor' % node
        
        if cmds.objExists(overrideEnabled):
            cmds.setAttr(overrideEnabled, 1)
            cmds.setAttr(overrideColor, color)



def hide_attributes(node, attributes):
    
    for attribute in attributes:
        
        current_attribute = '%s.%s' % (node, attribute)
        
        cmds.setAttr(current_attribute, l = True, k = False)
        
def hide_keyable_attributes(node):
    attributes = cmds.listAttr(node, k = True)
        
    hide_attributes(node, attributes)

def get_color_of_side(side = 'C', sub_color = False):
    
    if not sub_color:
        
        if side == 'L':
            return 6
        
        if side == 'R':
            return 13
        
        if side == 'C':
            return 17
    
    if sub_color:
    
        if side == 'L':
            return 18
        
        if side == 'R':
            return 20
        
        if side == 'C':
            return 21

def connect_vector_attribute(source_transform, target_transform, attribute, connect_type = 'plus'):
    
    axis = ['X','Y','Z']
    
    node = None
    nodes = []
    
    for letter in axis:
        
        source_attribute = '%s.%s%s' % (source_transform, attribute, letter)
        target_attribute = '%s.%s%s' % (target_transform, attribute, letter)
        
        if connect_type == 'plus':
            node = connect_plus(source_attribute,
                                target_attribute)
        
            nodes.append(node)
        
        if connect_type == 'multiply':
            
            if node:
                cmds.connectAttr(source_attribute, '%s.input1%s' % (node,letter))
                cmds.connectAttr('%s.output%s' % (node, letter), target_attribute)
            
            if not node:
                node = connect_multiply(source_attribute,
                                            target_attribute)
                
    if not nodes:
        nodes = node
            
    return nodes
    

def connect_translate(source_transform, target_transform):
    
    connect_vector_attribute(source_transform, target_transform, 'translate')

def connect_rotate(source_transform, target_transform):
    
    connect_vector_attribute(source_transform, target_transform, 'rotate')
    
def connect_scale(source_transform, target_transform):
    
    connect_vector_attribute(source_transform, target_transform, 'scale')

def connect_visibility(attribute_name, target_node, value = 1):
    
    nodes = vtool.util.convert_to_sequence(target_node)
    
    if not cmds.objExists(attribute_name):
        split_name = attribute_name.split('.')
        cmds.addAttr(split_name[0], ln = split_name[1], at = 'bool', dv = value,k = True)
        
    for thing in nodes: 
        cmds.connectAttr(attribute_name, '%s.visibility' % thing)

def connect_plus(source_attribute, target_attribute, respect_value = False):
    
    if cmds.isConnected(source_attribute, target_attribute):
        return
    
    input_attribute = get_attribute_input( target_attribute )
    
    value = cmds.getAttr(target_attribute)
    
    if not input_attribute and not respect_value:
        cmds.connectAttr(source_attribute, target_attribute)
        return

    if input_attribute:
        if cmds.nodeType(input_attribute) == 'plusMinusAverage':
            
            plus = input_attribute.split('.')
            plus = plus[0]
            
            if cmds.getAttr('%s.operation' % plus) == 1:
                
                slot = get_available_slot('%s.input1D' % plus)
                
                cmds.connectAttr(source_attribute, '%s.input1D[%s]' % (plus, slot) )                   
                
                return plus
        

    target_attribute_name = target_attribute.replace('.', '_')
        
    plus = cmds.createNode('plusMinusAverage', n = 'plusMinusAverage_%s' % target_attribute_name)
    
    cmds.connectAttr( source_attribute , '%s.input1D[1]' % plus)
    
    if input_attribute:
        cmds.connectAttr( input_attribute, '%s.input1D[0]' % plus)
        
        new_value = cmds.getAttr(target_attribute) 
        
        if abs(new_value) - abs(value) > 0.01:
            cmds.setAttr('%s.input1D[2]' % plus, value)
        
    if not input_attribute and respect_value:
        cmds.setAttr('%s.input1D[0]' % plus, value)
    
    cmds.connectAttr('%s.output1D' % plus, target_attribute, f = True)
    
    return plus

def connect_plus_new(source_attribute, target_attribute, respect_value = False):
    
    if cmds.isConnected(source_attribute, target_attribute):
        return
    
    output_value = 0
    source_value = 0
            
    if respect_value:
        output_value = cmds.getAttr(target_attribute)
        source_value = cmds.getAttr(source_attribute)
        
    input_attribute = get_attribute_input( target_attribute )
    
    if not input_attribute and not respect_value:
        cmds.connectAttr(source_attribute, target_attribute)
        return

    if input_attribute:
        
        if cmds.nodeType(input_attribute) == 'plusMinusAverage':
            
            plus = input_attribute.split('.')
            plus = plus[0]
            
            if cmds.getAttr('%s.operation' % plus) == 1:
                
                slot = get_available_slot('%s.input1D' % plus)
                
                cmds.connectAttr(source_attribute, '%s.input1D[%s]' % (plus, slot) )                   
                
                source_value += cmds.getAttr('%s.input1D[0]' % plus)
                
                if respect_value:
                    new_value = output_value - source_value
                    cmds.setAttr('%s.input1D[0]', new_value)
                
                return plus
        

    target_attribute_name = target_attribute.replace('.', '_')
        
    plus = cmds.createNode('plusMinusAverage', n = 'plusMinusAverage_%s' % target_attribute_name)
    
    cmds.connectAttr( source_attribute , '%s.input1D[1]' % plus)
    
    if respect_value:
        new_value = output_value - source_value
        cmds.setAttr('%s.input1D[0]', new_value)
    
    """
    if input_attribute:
        
        slot = get_available_slot('%s.input1D' % plus)
            
        cmds.connectAttr( input_attribute, '%s.input1D[%s]' % (plus, slot))
        
        new_value = cmds.getAttr(target_attribute) 
        
        if abs(new_value) - abs(value) > 0.01:
            cmds.setAttr('%s.input1D[2]' % plus, value)
        
    if not input_attribute and respect_value:
        cmds.setAttr('%s.input1D[0]' % plus, value)
    """
    
    cmds.connectAttr('%s.output1D' % plus, target_attribute, f = True)
    
    return plus

def connect_multiply(source_attribute, target_attribute, value = 0.1, skip_attach = False, plus= True):
    
    
    input_attribute = get_attribute_input( target_attribute,  )

    new_name = target_attribute.replace('.', '_')
    new_name = new_name.replace('[', '_')
    new_name = new_name.replace(']', '_')

    multi = cmds.createNode('multiplyDivide', n = 'multiplyDivide_%s' % new_name)

    cmds.connectAttr(source_attribute, '%s.input1X' % multi)
    
    cmds.setAttr('%s.input2X' % multi, value)

    if input_attribute and not skip_attach:
        cmds.connectAttr(input_attribute, '%s.input2X' % multi)

    if plus:
        connect_plus('%s.outputX' % multi, target_attribute)
    if not plus:
        if not cmds.isConnected('%s.outputX' % multi, target_attribute):
            cmds.connectAttr('%s.outputX' % multi, target_attribute, f = True)
            
            
    
    
    return multi

def connect_blend(source_attribute1, source_attribute2, target_attribute, value = 0.5 ):
    blend = cmds.createNode('blendColors', n = 'blendColors_%s' % source_attribute1)
    
    cmds.connectAttr(source_attribute1, '%s.color1R' % blend)
    cmds.connectAttr(source_attribute2, '%s.color2R' % blend)
    
    connect_plus('%s.outputR' % blend, target_attribute)
    
    cmds.setAttr('%s.blender' % blend, value)
    
    return blend

def connect_reverse(source_attribute, target_attribute):
    reverse = cmds.createNode('reverse', n = 'reverse_%s' % source_attribute)
    
    cmds.connectAttr(source_attribute, '%s.inputX' % reverse)
    connect_plus('%s.outputX' % reverse, target_attribute)
    
    return reverse

def connect_equal_condition(source_attribute, target_attribute, equal_value):
    
    condition = cmds.createNode('condition', n = 'condition_%s' % source_attribute)
    
    cmds.connectAttr(source_attribute, '%s.firstTerm' % condition)
    cmds.setAttr('%s.secondTerm' % condition, equal_value)
    
    cmds.setAttr('%s.colorIfTrueR' % condition, 1)
    cmds.setAttr('%s.colorIfFalseR' % condition, 0)
    
    connect_plus('%s.outColorR' % condition, target_attribute)
        

        
def disconnect_attribute(attribute):
    
    connection = get_attribute_input(attribute)

    if connection:
        cmds.disconnectAttr(connection, attribute)

def get_indices(attribute):
    multi_attributes = cmds.listAttr(attribute, multi = True)
    
    if not multi_attributes:
        return
    
    indices = {}
    
    for multi_attribute in multi_attributes:
        index = re.findall('\d+', multi_attribute)
        
        if index:
            index = int(index[-1])
            indices[index] = None
        
    indices = indices.keys()
    indices.sort()
        
    return indices

def create_attribute_lag(source, attribute, targets):
    
    var = MayaNumberVariable('lag')
    var.set_value(0)
    var.set_min_value(0)
    var.set_max_value(1)
    var.create(source)
    
    frame_cache = cmds.createNode('frameCache', n = 'frameCache_%s_%s' % (source, attribute) )
    
    cmds.connectAttr('%s.%s' % (source, attribute), '%s.stream' % frame_cache)
    
    target_count = len(targets)
    
    for inc in range(0, target_count):
        
        cmds.createNode('blendColors')
        blend = connect_blend('%s.past[%s]' % (frame_cache, inc+1), 
                              '%s.%s' % (source,attribute),
                              '%s.%s' % (targets[inc], attribute))
        
        connect_plus('%s.lag' % source, '%s.blender' % blend)
        
def create_attribute_spread(control, transforms, name = 'spread', axis = 'Y', invert = False, create_driver = False):

    variable = '%s.%s' % (control, name)
    
    count = len(transforms)
    
    section = 2.00/(count-1)
    
    spread_offset = 1.00
    
    if not cmds.objExists('%s.SPREAD' % control):
        title = MayaEnumVariable('SPREAD')
        title.create(control)
        
    if not cmds.objExists(variable):    
        spread = MayaNumberVariable(name)
        spread.create(control)
        
    
    for transform in transforms:
        
        if create_driver:
            transform = create_xform_group(transform, 'spread')
        
        if invert:
            spread_offset_value = -1 * spread_offset
        if not invert:
            spread_offset_value = spread_offset
        
        connect_multiply(variable, '%s.rotate%s' % (transform, axis), spread_offset_value)
                
        spread_offset -= section
        
        
        
def create_attribute_spread_translate(control, transforms, name = 'spread', axis = 'Z', invert = False):
    variable = '%s.%s' % (control, name)
    
    count = len(transforms)
    
    section = 2.00/(count-1)
    
    spread_offset = 1.00
    
    if invert == True:
        spread_offset = -1.00
    
    
    if not cmds.objExists('%s.SPREAD' % control):
        title = MayaEnumVariable('SPREAD')
        title.create(control)
        
    if not cmds.objExists(variable):    
        spread = MayaNumberVariable(name)
        spread.create(control)
        
    
    for transform in transforms:
        connect_multiply(variable, '%s.translate%s' % (transform, axis), spread_offset)
        
        if invert == False:        
            spread_offset -= section
        if invert == True:
            spread_offset += section    
        
def create_offset_sequence(attribute, target_transforms, target_attributes):
    
    #split = attribute.split('.')
    
    count = len(target_transforms)
    inc = 0
    section = 1.00/count
    offset = 0
    
    anim_curve = cmds.createNode('animCurveTU', n = 'animCurveTU_%s' % attribute.replace('.','_'))
    #cmds.connectAttr(attribute, '%s.input' % anim_curve)
    
    for transform in target_transforms:
        frame_cache = cmds.createNode('frameCache', n = 'frameCache_%s' % transform)
        
        cmds.setAttr('%s.varyTime' % frame_cache, inc)
        
        
        cmds.connectAttr('%s.output' % anim_curve, '%s.stream' % frame_cache)
        
        cmds.setKeyframe( frame_cache, attribute='stream', t= inc )
        
        for target_attribute in target_attributes:
            cmds.connectAttr('%s.varying' % frame_cache, 
                             '%s.%s' % (transform, target_attribute))
        
        
        inc += 1
        offset += section

def create_title(node, name):
    title = MayaEnumVariable(name)
    title.create(node)
  
def lock_attributes(node, bool_value = True, attributes = None, hide = False):
    
    if not attributes:
        attributes = cmds.listAttr(node, k = True)
    
    for attribute in attributes:
        attribute_name = '%s.%s' % (node, attribute)
        
        inputs = get_inputs(attribute_name)
        
        if inputs:
            continue
        
        cmds.setAttr(attribute_name, lock = bool_value)
        
        if hide:
            cmds.setAttr(attribute_name, cb = False)
        
        
def unlock_attributes(node, attributes = [], only_keyable = False):
    
    if not attributes:
        if only_keyable == False:
            attrs = cmds.listAttr(node, locked = True)
            
        if only_keyable == True:
            attrs = cmds.listAttr(node, locked = True, k = True)
    
    if attributes:
        attrs = attributes
    
    if attrs:
        for attr in attrs:
            cmds.setAttr('%s.%s' % (node, attr), l = False)
    
  
def zero_xform_channels(transform):
    
    channels = ['translate',
                'rotate']
    
    other_channels = ['scale']
    
    all_axis = ['X','Y','Z']
    
    for channel in channels:
        for axis in all_axis:
            try:
                cmds.setAttr(transform + '.' + channel + axis, 0)
            except:
                pass
            
    for channel in other_channels:
        for axis in all_axis:
            try:
                cmds.setAttr(transform + '.' + channel + axis, 1)
            except:
                pass
    
  



#---Rig

def get_controls():
    return cmds.ls('CNT_*', type = 'transform')
    
def mirror_control(control):
    
    if not control:
        return
    
    
    shapes = get_shapes(control)
    
    if not shapes:
        return
    
    shape = shapes[0]
    
    if not cmds.objExists('%s.cc' % shape):
        return
    
    if control.endswith('_L') or control.endswith('_R'):
        
        other_control = None
        
        if control.endswith('_L'):
            other_control = control[0:-2] + '_R'
            
        if control.endswith('_R'):
            other_control = control[0:-2] + '_L'
            
        if not cmds.objExists(other_control):
            return
                        
        shapes = get_shapes(other_control)
        
        if not shapes:
            return
        
        other_shape = shapes[0]
        
        if not cmds.objExists('%s.cc' % other_shape):
            return
        
        cvs = cmds.ls('%s.cv[*]' % shape, flatten = True)
        other_cvs = cmds.ls('%s.cv[*]' % other_shape, flatten = True)
        
        if len(cvs) != len(other_cvs):
            return
        
        for inc in range(0, len(cvs)):
            position = cmds.pointPosition(cvs[inc], world = True)
            
            x_value = position[0] * -1
                 
            cmds.move(x_value, position[1], position[2], other_cvs[inc], worldSpace = True)
    
def mirror_controls():
    
    selection = cmds.ls(sl = True)
    
    controls = get_controls()
    
    found = []
    
    if selection:
        for selection in selection:
            if selection in controls:
                found.append(selection)
    
    if not selection or not found:
        found = controls
    
    for control in found:
        mirror_control(control)

def process_joint_weight_to_parent(mesh):
    
    scope = cmds.ls('process_*', type = 'joint')
    
    
    progress = ProgressBar('process to parent %s' % mesh, len(scope))
    
    for joint in scope:
        progress.status('process to parent %s: %s' % (mesh, joint))
        
        transfer_weight_from_joint_to_parent(joint, mesh)
        
        progress.inc()
        if progress.break_signaled():
            break
        
    progress.end()
    
    cmds.delete(scope)

def joint_axis_visibility(bool_value):
    
    joints = cmds.ls(type = 'joint')
    
    for joint in joints:
        
        cmds.setAttr('%s.displayLocalAxis' % joint, bool_value)

def hook_ik_fk(control, joint, groups, attribute = 'ikFk'): 
      
    if not cmds.objExists('%s.%s' % (control, attribute)): 
        cmds.addAttr(control, ln = attribute, min = 0, max = 1, dv = 0, k = True) 
      
    attribute_ikfk = '%s.%s' % (control, attribute) 
      
    cmds.connectAttr(attribute_ikfk, '%s.switch' % joint) 
      
    for inc in range(0, len(groups)): 
        connect_equal_condition(attribute_ikfk, '%s.visibility' % groups[inc], inc) 

            
       
def fix_fade(target_curve, follow_fade_multiplies):

    multiplies = follow_fade_multiplies

    mid_control = multiplies[0]['source']
    
    control_position = cmds.xform(mid_control, q = True, ws = True, t = True)
    control_position_y = [0, control_position[1], 0]
    
    parameter = get_y_intersection(target_curve, control_position)
    
    control_at_curve_position = cmds.pointOnCurve(target_curve, parameter = parameter)
    control_at_curve_y = [0, control_at_curve_position[1], 0]
    
    total_distance = vtool.util.get_distance(control_position_y, control_at_curve_y)
    
    multi_count = len(multiplies)
    
    for inc in range(0, multi_count):
        multi = multiplies[inc]['node']
        driver = multiplies[inc]['target']
        
        driver_position = cmds.xform(driver, q = True, ws = True, t = True)
        driver_position_y = [0, driver_position[1], 0]
        
        
        parameter = get_y_intersection(target_curve, driver_position)
        
        driver_at_curve = cmds.pointOnCurve(target_curve, parameter = parameter)
        driver_at_curve_y = [0, driver_at_curve[1], 0]
        
        driver_distance = vtool.util.get_distance(driver_position_y, driver_at_curve_y)
        
        value = (driver_distance/total_distance)
    
        cmds.setAttr('%s.input2Y' % multi, value)

def create_blend_attribute(source, target, min_value = 0, max_value = 10):
    if not cmds.objExists(source):
        split_source = source.split('.')
        cmds.addAttr(split_source[0], ln = split_source[1], min = min_value, max = max_value, k = True, dv = 0)
        
    multi = connect_multiply(source, target, .1)
    
    return multi
    

def quick_driven_key(source, target, source_values, target_values):
    
    for inc in range(0, len(source_values)):
        
        cmds.setDrivenKeyframe(target,cd = source, driverValue = source_values[inc], value = target_values[inc], itt = 'linear', ott = 'linear')

#--- Nucleus

def create_nucleus(name = None):
    if name:
        name = 'nucleus_%s' % name
    if not name:
        name = 'nucleus'
        
    nucleus = cmds.createNode('nucleus', name = name)
    
    cmds.connectAttr('time1.outTime', '%s.currentTime' % nucleus)
    
    cmds.setAttr('%s.spaceScale' % nucleus, 0.01)
    
    return nucleus
    
#--- Hair

def create_hair_system(name = None, nucleus = None):

    if name:
        name = 'hairSystem_%s' % name
    if not name:
        name = 'hairSystem'
    
    hair_system_shape = cmds.createNode('hairSystem')
    hair_system = cmds.listRelatives(hair_system_shape, p = True)
    
    hair_system = cmds.rename(hair_system, inc_name(name) )
    hair_system_shape = cmds.listRelatives(hair_system, shapes = True)[0]
    
    cmds.connectAttr('time1.outTime', '%s.currentTime' % hair_system_shape)
    
    if nucleus:
        connect_hair_to_nucleus(hair_system, nucleus)
    
    return hair_system, hair_system_shape

def connect_hair_to_nucleus(hair_system, nucleus):
    
    hair_system_shape = cmds.listRelatives(hair_system, shapes = True)[0]
    
    cmds.connectAttr('%s.startFrame' % nucleus, '%s.startFrame' % hair_system_shape)
    
    indices = get_indices('%s.inputActive' % nucleus)
    
    if indices:
        current_index = indices[-1] + 1
    
    if not indices:
        current_index = 0
    
    cmds.connectAttr('%s.currentState' % hair_system_shape, '%s.inputActive[%s]' % (nucleus, current_index))
        
    cmds.connectAttr('%s.startState' % hair_system_shape, '%s.inputActiveStart[%s]' % (nucleus, current_index))
    cmds.connectAttr('%s.outputObjects[%s]' % (nucleus, current_index), '%s.nextState' % hair_system_shape)
    
    cmds.setAttr('%s.active' % hair_system_shape, 1)
    
    cmds.refresh()

def create_follicle(name = None, hair_system = None):
    
    if name:
        name = 'follicle_%s' % name
    if not name:
        name = 'follicle'
    
    follicle_shape = cmds.createNode('follicle')
    follicle = cmds.listRelatives(follicle_shape, p = True)
    
    follicle = cmds.rename(follicle, inc_name(name))
    follicle_shape = cmds.listRelatives(follicle, shapes = True)[0]
    
    cmds.setAttr('%s.startDirection' % follicle_shape, 1)
    cmds.setAttr('%s.restPose' % follicle_shape, 1)
    cmds.setAttr('%s.degree' % follicle_shape, 3)
    
    if hair_system:
        connect_follicle_to_hair(follicle, hair_system)
            
    return follicle, follicle_shape    
        
def connect_follicle_to_hair(follicle, hair_system):
    
    indices = get_indices('%s.inputHair' % hair_system)
    
    if indices:
        current_index = indices[-1] + 1
    
    if not indices:
        current_index = 0
    
    cmds.connectAttr('%s.outHair' % follicle, '%s.inputHair[%s]' % (hair_system, current_index))
    indices = get_indices('%s.inputHair' % hair_system)
    
    cmds.connectAttr('%s.outputHair[%s]' % (hair_system, current_index), '%s.currentPosition' % follicle)
    
    cmds.refresh()
    
def add_follicle_to_curve(curve, hair_system = None, switch_control = None):
    
    parent = cmds.listRelatives(curve, p = True)
    
    follicle, follicle_shape = create_follicle(curve, hair_system)
    
    cmds.connectAttr('%s.worldMatrix' % curve, '%s.startPositionMatrix' % follicle_shape)
    cmds.connectAttr('%s.local' % curve, '%s.startPosition' % follicle_shape)
    
    new_curve_shape = cmds.createNode('nurbsCurve')
    new_curve = cmds.listRelatives(new_curve_shape, p = True)
    
    new_curve = cmds.rename(new_curve, inc_name('curve_%s' % follicle))
    new_curve_shape = cmds.listRelatives(new_curve, shapes = True)[0]
    
    cmds.setAttr('%s.inheritsTransform' % new_curve, 0)
    
    cmds.parent(curve, new_curve, follicle)
    cmds.hide(curve)
    
    cmds.connectAttr('%s.outCurve' % follicle, '%s.create' % new_curve)
    
    blend_curve= cmds.duplicate(new_curve, n = 'blend_%s' % curve)[0]
    
    outputs = get_attribute_outputs('%s.worldSpace' % curve)
    
    for output in outputs:
        cmds.connectAttr('%s.worldSpace' % blend_curve, output, f = True)
    
    if parent:
        cmds.parent(follicle, parent)
    
    if switch_control:
        
        blendshape = cmds.blendShape(curve, new_curve, blend_curve, w = [0,1],n = 'blendShape_%s' % follicle)[0]
        
        if not cmds.objExists('%s.dynamic' % switch_control):
            
            variable = MayaNumberVariable('dynamic')
            variable.set_variable_type(variable.TYPE_DOUBLE)
            variable.set_node(switch_control)
            variable.set_min_value(0)
            variable.set_max_value(1)
            variable.set_keyable(True)
            variable.create()
        
        remap = RemapAttributesToAttribute(switch_control, 'dynamic')
        remap.create_attributes(blendshape, [curve, new_curve])
        remap.create()
        """
        variable = MayaNumberVariable('attract')
        variable.set_variable_type(variable.TYPE_FLOAT)
        variable.set_node(switch_control)
        variable.set_min_value(0)
        variable.set_max_value(1)
        variable.set_keyable(True)
        variable.create()
    
        variable.connect_out('%s.inputAttract' % follicle)
        """
    return follicle

    
#--- Cloth

def add_passive_collider_to_mesh(mesh):
    cmds.select(mesh, r = True)
    nodes = mel.eval('makeCollideNCloth;')
    
    return nodes
    
def add_passive_collider_to_duplicate_mesh(mesh):
    duplicate = cmds.duplicate(mesh, n = 'passiveCollider_%s' % mesh )[0]
    
    cmds.parent(duplicate, w = True)
    
    nodes = add_passive_collider_to_mesh(duplicate)
    cmds.setAttr('%s.thickness' % nodes[0], .02)
    nodes.append(duplicate)
    
    cmds.blendShape(mesh, duplicate, w = [0,1], n = 'blendShape_passiveCollider_%s' % mesh)
    
    return nodes 

def add_nCloth_to_mesh(mesh):
    cmds.select(mesh, r = True)
    
    nodes = mel.eval('createNCloth 0;')
    
    parent = cmds.listRelatives(nodes[0], p = True)
    parent = cmds.rename(parent, 'nCloth_%s' % mesh)
    
    cmds.setAttr('%s.thickness' % parent, 0.02)
    
    return [parent]

def nConstrain_to_mesh(verts, mesh, force_passive = False):
    
    nodes1 = []
    
    if force_passive:
        nodes1 = add_passive_collider_to_mesh(mesh)
        cmds.setAttr('%s.collide' % nodes1[0], 0)
    
    cmds.select(cl = True)
    
    cmds.select(verts, mesh)
    nodes = mel.eval('createNConstraint pointToSurface 0;')
    
    return nodes + nodes1

def create_cloth_input_meshes(deform_mesh, cloth_mesh, parent, attribute):
    
    final = cmds.duplicate(deform_mesh)[0]
    final = cmds.rename(final, 'temp')
    
    clothwrap = cmds.duplicate(deform_mesh)[0]
    
    deform_hier = Hierarchy(deform_mesh)
    deform_hier.prefix('deform')
    
    clothwrap = cmds.rename(clothwrap, deform_mesh)
        
    clothwrap_hier = Hierarchy(clothwrap)
    clothwrap_hier.prefix('clothwrap')

    final = cmds.rename(final, deform_mesh)
    
    deform_mesh = deform_hier.top_of_hierarchy
    clothwrap = clothwrap_hier.top_of_hierarchy

    deform_mesh = deform_mesh.split('|')[-1]
    clothwrap = clothwrap.split('|')[-1]
    
    exclusive_bind_wrap(deform_mesh, cloth_mesh)
    exclusive_bind_wrap(cloth_mesh, clothwrap)
    
    blend = cmds.blendShape(deform_mesh, clothwrap, final, w = [0,1], n = 'blendShape_nClothFinal')[0]
    
    connect_equal_condition(attribute, '%s.%s' % (blend, deform_mesh), 0)
    connect_equal_condition(attribute, '%s.%s' % (blend, clothwrap), 1)
    
    cmds.parent(deform_hier.top_of_hierarchy , clothwrap, parent )
    
    nodes = add_nCloth_to_mesh(cloth_mesh)
    
    return nodes

#--- cMuscle

class CMuscle(object):
    def __init__(self, muscle):
        self.muscle = muscle
        self.description = None
        
        if not cmds.objExists('%s.description' % self.muscle):
            cmds.addAttr(self.muscle, ln = 'description', dt = 'maya_util')
        
    def _get_control_data_indices(self):
        muscle_creator = self._get_muscle_creator()
        return get_indices('%s.controlData' % muscle_creator)
    
    def _get_attach_data_indices(self):
        muscle_creator = self._get_muscle_creator()
        return get_indices('%s.attachData' % muscle_creator)
            
    def _get_parent(self):
        rels = cmds.listRelatives(self.muscle, p = True)
        return rels[0]
        
    def _get_muscle_creator(self):
        return get_attribute_input('%s.create' % self.muscle, True)
        
    def _get_muscle_shapes(self):
        
        shapes = get_shapes(self.muscle)
        
        deformer = None
        nurbs = None
        
        for shape in shapes:
            if cmds.nodeType(shape) == 'cMuscleObject':
                deformer = shape
            if cmds.nodeType(shape) == 'nurbsSurface':
                nurbs = shape
                
        return nurbs, deformer
    
    def _rename_controls(self, name):
        name_upper = name[0].upper() + name[1:]
        indices = self._get_control_data_indices()
        count = len(indices)
        
        muscle_creator = self._get_muscle_creator()
        
        last_xform = None
        
        for inc in range(0, count):
            
            input_value = get_attribute_input('%s.controlData[%s].insertMatrix' % (muscle_creator, inc), True)

            input_drive = cmds.listRelatives(input_value, p = True)[0]
            input_xform = cmds.listRelatives(input_drive, p = True)[0]

            input_stretch = get_attribute_input('%s.controlData[%s].curveSt' % (muscle_creator, inc), True)
            input_squash = get_attribute_input('%s.controlData[%s].curveSq' % (muscle_creator, inc), True)
            input_rest = get_attribute_input('%s.controlData[%s].curveRest' % (muscle_creator, inc), True)

            cmds.delete(input_stretch, input_squash, input_rest, ch = True)

            if inc == 0:
                cmds.rename(input_value, inc_name('startParent_%s' % name))
                
            if inc == count-1:
                cmds.rename(input_value, inc_name('endParent_%s' % name))

            if inc > 0 and inc < count-1:
                input_value = cmds.rename(input_value, inc_name('ctrl_%s_%s' % (inc, name)))
                shape = get_shapes(input_value)
                cmds.rename(shape, '%sShape' % input_value)
                
                input_stretch = cmds.listRelatives(input_stretch, p = True)[0]
                input_squash = cmds.listRelatives(input_squash, p = True)[0]
                input_rest = cmds.listRelatives(input_rest, p = True)[0]
                
                cmds.rename(input_stretch, inc_name('ctrl_%s_stretch%s' % (inc, name_upper)))
                cmds.rename(input_squash, inc_name('ctrl_%s_squash%s' % (inc, name_upper)))
                cmds.rename(input_rest, inc_name('ctrl_%s_rest%s' % (inc, name_upper)))
                
                cmds.rename(input_drive, 'drive_%s' % input_value)
                input_xform = cmds.rename(input_xform, 'xform_%s' % input_value)
                
                last_xform = input_xform
                
        parent = cmds.listRelatives(last_xform, p = True)[0]
        cmds.rename(parent, inc_name('controls_cMuscle%s' % name_upper))
                
    def _rename_attach_controls(self, name):
        indices = self._get_attach_data_indices()
        count = len(indices)
        
        muscle_creator = self._get_muscle_creator()
        last_xform = None
        
        for inc in range(0, count):
            
            name_upper = name[0].upper() + name[1:]

            input_value = get_attribute_input('%s.attachData[%s].attachMatrix' % (muscle_creator, inc), True)

            input_drive = cmds.listRelatives(input_value, p = True)[0]
            input_xform = cmds.listRelatives(input_drive, p = True)[0]
            
            
            
            input_stretch = get_attribute_input('%s.attachData[%s].attachMatrixSt' % (muscle_creator, inc), True)
            input_squash = get_attribute_input('%s.attachData[%s].attachMatrixSq' % (muscle_creator, inc), True)
                        
            input_value = cmds.rename(input_value, inc_name('ctrl_%s_attach%s' % (inc+1, name_upper)))
            cmds.rename(input_stretch, inc_name('ctrl_%s_attachStretch%s' % (inc+1, name_upper)))
            cmds.rename(input_squash, inc_name('ctrl_%s_attachSquash%s' % (inc+1, name_upper)))
            
            cmds.rename(input_drive, 'drive_%s' % input_value)
            input_xform = cmds.rename(input_xform, 'xform_%s' % input_value)
            last_xform = input_xform
            
        parent = cmds.listRelatives(last_xform, p = True)[0]
        cmds.rename(parent, inc_name('attach_cMuscle%s' % name_upper))           
            
    def _rename_locators(self, name):
        
        muscle_creator = self._get_muscle_creator()

        input_start_A = get_attribute_input('%s.startPointA' % muscle_creator, True)
        input_start_B = get_attribute_input('%s.startPointB' % muscle_creator, True)
        input_end_A = get_attribute_input('%s.endPointA' % muscle_creator, True)
        input_end_B = get_attribute_input('%s.endPointB' % muscle_creator, True)
        
        cmds.rename(input_start_A, inc_name('locatorStart1_%s' % name))
        cmds.rename(input_start_B, inc_name('locatorStart2_%s' % name))
        cmds.rename(input_end_A, inc_name('locatorEnd1_%s' % name))
        cmds.rename(input_end_B, inc_name('locatorEnd2_%s' % name))
        
    
    def rename(self, name):
        
        nurbsSurface, muscle_object = self._get_muscle_shapes()
        muscle_creator = self._get_muscle_creator()
        
        self.muscle = cmds.rename(self.muscle, inc_name('cMuscle_%s' % name))
        
        if cmds.objExists(nurbsSurface):
            cmds.rename(nurbsSurface, inc_name('%sShape' % self.muscle))
        
        cmds.rename(muscle_object, inc_name('cMuscleObject_%sShape' % name))
        cmds.rename(muscle_creator, inc_name('cMuscleCreator_%s' % name))
        
        parent = self._get_parent()
        
        cmds.rename(parent, inc_name('cMuscle_%s_grp' % name))
        
        self._rename_controls(name)
        self._rename_attach_controls(name)
        self._rename_locators(name)
        
        self.description = name
        cmds.setAttr('%s.description' % self.muscle, name, type = 'maya_util')
        
    def create_attributes(self, node = None):
        
        if not node:
            node = self.muscle
        
        muscle_creator = self._get_muscle_creator()
        
        description = cmds.getAttr('%s.description' % self.muscle)
        
        title = MayaEnumVariable(description.upper())
        title.create(node)
        
        if node == self.muscle:
            cmds.addAttr(node, ln = 'controlVisibility_%s' % description, at = 'bool', k = True )
            cmds.connectAttr('%s.controlVisibility_%s' % (node, description), '%s.showControls' % muscle_creator)
        
        indices = self._get_attach_data_indices()
        count = len(indices)
        
        attributes = ['jiggle', 'jiggleX', 'jiggleY', 'jiggleZ', 'jiggleImpact', 'jiggleImpactStart', 'jiggleImpactStop', 'cycle', 'rest']
        
        for inc in range(0, count):
            current = inc+1
            
            title_name = 'muscle_section_%s' % (current)
            title_name = title_name.upper()
            
            title = MayaEnumVariable(title_name)
            title.create(node)
            
            control = get_attribute_input('%s.controlData[%s].insertMatrix' % (muscle_creator, current), True)
            
            for attribute in attributes:
                other_attribute = '%s_%s' % (attribute, current) 
            
                attribute_value = cmds.getAttr('%s.%s' % (control, attribute))
                cmds.addAttr(node, ln = other_attribute, at = 'double', k = True, dv = attribute_value)    
            
                cmds.connectAttr('%s.%s' % (node, other_attribute), '%s.%s' % (control, attribute))
            
class ProgressBar(object):
    
    def __init__(self, title, count):
        if is_batch():
            return
        
        gMainProgressBar = mel.eval('$tmp = $gMainProgressBar');
    
        self.progress_ui = cmds.progressBar( gMainProgressBar,
                                        edit=True,
                                        beginProgress=True,
                                        isInterruptable=True,
                                        status= title,
                                        maxValue= count )
    
    def inc(self, inc = 1):
        if is_batch():
            return
        
        cmds.progressBar(self.progress_ui, edit=True, step=inc)
        
            
    def end(self):
        if is_batch():
            return
        
        cmds.progressBar(self.progress_ui, edit=True, ep = True)
        
    def status(self, status_string):
        if is_batch():
            return
        
        cmds.progressBar(self.progress_ui, edit=True, status = status_string)
        
    def break_signaled(self):
        if is_batch():
            return True
        
        break_progress = cmds.progressBar(self.progress_ui, query=True, isCancelled=True )

        if break_progress:
            self.end()
            return True
        
        return False
    

