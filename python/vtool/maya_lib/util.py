# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

import sys

import string
import re
import traceback

import maya.OpenMaya as OpenMaya
import maya.cmds as cmds
import maya.mel as mel

import vtool.util

import curve

#--- decorators

def undo_off(function):
    def wrapper(*args, **kwargs):
        
        if not vtool.util.is_in_maya():
            return
        return_value = None
                
        cmds.undoInfo(state = False)
        
        try:
            function(*args, **kwargs)
        except RuntimeError:
            
            cmds.undoInfo(state = True)
            vtool.util.show(traceback.format_exc)
                    
        cmds.undoInfo(state = True)
        
        return return_value
        
    return wrapper

def undo_chunk(function):
    def wrapper(*args, **kwargs):
        
        if not vtool.util.is_in_maya():
            return
        return_value = None
        
        cmds.undoInfo(openChunk = True)
        
        try:
            return_value = function(*args, **kwargs)
        except RuntimeError:
            
            cmds.undoInfo(closeChunk = True)
            vtool.util.show(traceback.format_exc)
            
        cmds.undoInfo(closeChunk = True)
        
        return return_value
                     
    return wrapper

def is_batch():
    return cmds.about(batch = True)


class ScriptEditorRead(object):
    
    def __init__(self):
        
        self.CALLBACK_ID = None
        self.read_value = ()
    
    def start(self):
        '''
        Begin writing to terminal.
        '''
    
        if self.CALLBACK_ID is None:
            self.CALLBACK_ID = OpenMaya.MCommandMessage.addCommandOutputFilterCallback(read_script)
        
    def end(self):
        '''
        Stop writing to terminal
        '''
    
        if not self.CALLBACK_ID is None:
            OpenMaya.MMessage.removeCallback(self.CALLBACK_ID)
            self.CALLBACK_ID = None
            
        global script_editor_value
        script_editor_value = []
        
script_editor_value = []
        
def read_script(msg, msgType, filterOutput, clientData):
    '''
    This is the callback function that gets called when Maya wants to print something.
    It will take the msg and output it to the terminal rather than the Maya Script Editor
    '''
    OpenMaya.MScriptUtil.setBool(filterOutput, True)
    
    global script_editor_value
    
    value = str(msg)
    
    if value == '\n':
        return
    
    script_editor_value.append( value )


#--- variables

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
   
class TransformFunction(MayaFunction):
    
    def _define_api_object(self, mobject):
        return OpenMaya.MFnTransform
    
    
    
    
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
        self.joints = []
            
    
    def _create_regular_ik(self):
        self.ik_handle = cmds.ikHandle( name = inc_name(self.name),
                                       startJoint = self.start_joint,
                                       endEffector = self.end_joint,
                                       sol = self.solver_type )[0]
                                       
    def _create_spline_ik(self):
        
        if self.curve:
            
            self.ik_handle = cmds.ikHandle(name = inc_name(self.name),
                                           startJoint = self.start_joint,
                                           endEffector = self.end_joint,
                                           sol = self.solver_type,
                                           curve = self.curve, ccv = False, pcv = False)[0]
        if not self.curve:
            
            self.ik_handle = cmds.ikHandle(name = inc_name(self.name),
                                           startJoint = self.start_joint,
                                           endEffector = self.end_joint,
                                           sol = self.solver_type,
                                           scv = False)
            
            self.curve = self.ik_handle[2]
            self.curve = cmds.rename(self.curve, inc_name('curve_%s' % self.name))
            
            self.ik_handle = self.ik_handle[0]
                                           
        
    def set_start_joint(self, joint):
        self.start_joint = joint
        
    def set_end_joint(self, joint):
        self.end_joint = joint
        
    def set_joints(self, joints_list):
        self.start_joint = joints_list[0]
        self.end_joint = joints_list[-1]
        self.joints = joints_list
        
    def set_curve(self, curve):
        self.curve = curve
        
    def set_solver(self, type_name):
        self.solver_type = type_name
    
    def create(self):
        
        if not self.start_joint or not self.end_joint:
            return
        
        if not self.curve and not self.solver_type == self.solver_spline:
            self._create_regular_ik()
        
        if self.curve or self.solver_type == self.solver_spline:
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
        self.per_joint_stretch = True
    
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
            if not self.per_joint_stretch:
                stretch_offset.set_keyable(False)
            
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
    
    def set_per_joint_stretch(self, bool_value):
        self.per_joint_stretch = bool_value
    
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

#--- Rig Class Placeholders

#These are only for backwards compatibility. 
#They should not be used within this module!!!
#new classes built after this change will not be added to this list
import rigs
reload(rigs)

Rig = rigs.Rig
JointRig = rigs.JointRig
BufferRig = rigs.BufferRig
SparseRig = rigs.SparseRig
SparseLocalRig = rigs.SparseLocalRig
ControlRig = rigs.ControlRig
GroundRig = rigs.GroundRig
FkRig = rigs.FkRig
FkLocalRig = rigs.FkLocalRig
FkScaleRig = rigs.FkScaleRig
FkCurlNoScaleRig = rigs.FkCurlNoScaleRig
FkCurlRig = rigs.FkCurlRig
SimpleFkCurveRig = rigs.SimpleFkCurveRig
FkCurveRig = rigs.FkCurveRig
FkCurveLocalRig = rigs.FkCurveLocalRig
NeckRig = rigs.NeckRig
IkSplineNubRig = rigs.IkSplineNubRig
IkAppendageRig = rigs.IkAppendageRig
RopeRig = rigs.RopeRig
TweakCurveRig = rigs.TweakCurveRig
IkLegRig = rigs.IkLegRig
RollRig = rigs.RollRig
FootRollRig = rigs.FootRollRig
EyeRig = rigs.EyeRig
JawRig = rigs.JawRig
      
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
        
        self.right_side_fix = True
        self.right_side_fix_axis = 'x'
        
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
        #rig.set_control_orient(self.start_joint)
        rig.set_buffer(False)
        rig.set_right_side_fix(self.right_side_fix, self.right_side_fix_axis)
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
    
    def set_right_side_fix(self, bool_value, axis = 'x'):
        self.right_side_fix = bool_value
        self.right_side_fix_axis = axis

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
        #cmds.setAttr('%s.interpType' % parent_constraint, 2)
        
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
    
            #temp_group = cmds.group(em = True, n = inc_name('temp_%s' % control))
            temp_group = cmds.duplicate(control, n = 'temp_%s' % control, po = True)[0]
            
            MatchSpace(control, temp_group).translation_rotation()
            parent_group = cmds.group(em = True)
            cmds.parent(temp_group, parent_group)
            
            cmds.setAttr('%s.scaleX' % parent_group, -1)
            
            #temp_xform = create_xform_group(temp_group, use_duplicate = True)
            
            orig_value_x = cmds.getAttr('%s.rotateX' % control)
            orig_value_y = cmds.getAttr('%s.rotateY' % control)
            orig_value_z = cmds.getAttr('%s.rotateZ' % control)
            
            zero_xform_channels(control)
            
            const1 = cmds.pointConstraint(temp_group, other_control)[0]
            const2 = cmds.orientConstraint(temp_group, other_control)[0]
            #const = cmds.parentConstraint(temp_group, other_control)
            
            value_x = cmds.getAttr('%s.rotateX' % other_control)
            value_y = cmds.getAttr('%s.rotateY' % other_control)
            value_z = cmds.getAttr('%s.rotateZ' % other_control)
            
            cmds.delete([const1, const2])
            
            if abs(value_x) - abs(orig_value_x) > 0.01 or abs(value_y) - abs(orig_value_y) > 0.01 or abs(value_z) - abs(orig_value_z) > 0.01:
                
                cmds.setAttr('%s.rotateX' % other_control, orig_value_x)
                cmds.setAttr('%s.rotateY' % other_control, -1*orig_value_y)
                cmds.setAttr('%s.rotateZ' % other_control, -1*orig_value_z)
                            
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
        
        self.controls = [top_control.control, btm_control.control]
        self.xforms = [xform_top_control, xform_btm_control]
        
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
        
    @undo_chunk
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
            
            self.mesh = mesh[0].split('.')[0]


        skin_deformer = self._get_skin_cluster(self.mesh)
        
        self.skin_cluster= None
        
        if skin_deformer:
            self.skin_cluster = skin_deformer
        
    def _get_skin_cluster(self, mesh):
        
        skin_deformer = find_deformer_by_type(mesh, 'skinCluster')
        
        return skin_deformer

    def _add_joints_to_skin(self, joints):
        
        influences = get_influences_on_skin(self.skin_cluster)
        
        for joint in joints:
            if not joint in influences:
                cmds.skinCluster(self.skin_cluster, e = True, ai = joint, wt = 0.0, nw = 1)
        
    @undo_off
    def transfer_joint_to_joint(self, source_joints, destination_joints, source_mesh = None, percent =1):
        
        if not self.skin_cluster:
            vtool.util.show('No skinCluster found on %s. Could not transfer.' % self.mesh)
            return
        
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
        
        if not vert_count:
            return
        
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
            
        cmds.skinPercent(self.skin_cluster, self.vertices, normalize = True) 
        
        bar.end()
         
    @undo_off  
    def transfer_joints_to_new_joints(self, joints, new_joints, falloff = 1, power = 4, weight_percent_change = 1):
        
        if not self.skin_cluster:
            vtool.util.show('No skinCluster found on %s. Could not transfer.' % self.mesh)
            return
        
        joints = vtool.util.convert_to_sequence(joints)
        new_joints = vtool.util.convert_to_sequence(new_joints)
        
        if not self.skin_cluster or not self.mesh:
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
            
        if not source_joint_weights:
            return
            
        verts = self.vertices
        
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
        
        if not weighted_verts:
            return
        
        bar = ProgressBar('transfer weight', len(weighted_verts))
        
        inc = 1
        
        new_joint_count = len(new_joints)
        joint_count = len(joints)
        
        for vert_index in weighted_verts:
            
            vert_name = '%s.vtx[%s]' % (self.mesh, vert_index)
            
            distances = get_distances(new_joints, vert_name)
            
            found_weight = False
            
            joint_weight = {}    
            
            for inc2 in range(0, len(distances)):
                if distances[inc2] <= 0.001:
                    joint_weight[new_joints[inc2]] = 1
                    found_weight = True
                    break
                          
            if not found_weight:
            
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
          
        cmds.skinPercent(self.skin_cluster, self.vertices, normalize = True) 
            
        bar.end()
                
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
        
    def set_pose_data(self, pose):
        store = StoreControlData(pose)
        store.set_data()
        
    def set_poses(self, pose_list):
        
        data_list = []
        
        for pose_name in pose_list:
            
            store = StoreControlData(pose_name)

            data_list.append( store.eval_data(True) )
            
        store = StoreControlData().eval_multi_transform_data(data_list)
    
    @undo_chunk
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
    
    @undo_chunk
    def reset_pose(self, pose_name):
        
        pose = PoseControl()
        pose.set_pose(pose_name)
        pose.reset_target_meshes()
    
    @undo_chunk
    def rename_pose(self, pose_name, new_name):
        pose = BasePoseControl()
        pose.set_pose(pose_name)
        return pose.rename(new_name)
    
    def create_combo(self, pose_list, name):
        
        combo = ComboControl(pose_list, name)
        combo.create()
    
    @undo_chunk
    def add_mesh_to_pose(self, pose_name, meshes = None):

        selection = None

        if not meshes == None:
            selection = cmds.ls(sl = True, l = True)
        if meshes:
            selection = meshes
        
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
    
    @undo_chunk
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
        
    @undo_chunk    
    def create_pose_blends(self, pose_name = None):
        
        if pose_name:
            pose = PoseControl()
            pose.set_pose(pose_name)
            pose.create_all_blends()
            return
        
        poses = self.get_poses()
        count = len(poses)

        progress = ProgressBar('adding poses ... ', count)
    
        for inc in range(count) :
            
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
        
        if not cmds.objExists(self.pose_control):
            return
        
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
        
        if not self.pose_control:
            return
        
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
        
    @undo_chunk
    def reset_target_meshes(self):
        
        count = self._get_mesh_count()
        
        for inc in range(0, count):
            
            deformed_mesh = self.get_mesh(inc)
            original_mesh = self.get_target_mesh(deformed_mesh)
            
            cmds.delete(deformed_mesh, ch = True)
            
            blendshape = self._get_blendshape(original_mesh)
            
            blend = BlendShape()
                    
            if blendshape:
                blend.set(blendshape)
                
            blend.set_envelope(0)    
            
            temp_dup = cmds.duplicate(original_mesh)[0]
            
            #using blendshape because of something that looks like a bug in Maya 2015
            temp_blend = quick_blendshape(temp_dup, deformed_mesh)
            
            cmds.delete(temp_blend, ch = True)
            cmds.delete(temp_dup)
            
            blend.set_envelope(1)  
            
        self.create_blend()  
        
       
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

def get_midpoint( source, target):
    vector1 = cmds.xform(source, 
                         query = True, 
                         worldSpace = True, 
                         rp = True)
    
    
    vector2 = cmds.xform(target, 
                            query = True, 
                            worldSpace = True, 
                            rp = True)
    
    return vtool.util.get_midpoint(vector1, vector2)

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

def create_follow_group(source_transform, target_transform, prefix = 'follow', follow_scale = False):
    
    parent = cmds.listRelatives(target_transform, p = True)
    
    name = '%s_%s' % (prefix, target_transform)
    
    follow_group = cmds.group( em = True, n = inc_name(name) )
    
    match = MatchSpace(source_transform, follow_group)
    match.translation_rotation()
    
    cmds.parentConstraint(source_transform, follow_group, mo = True)
    
    cmds.parent(target_transform, follow_group)    
    
    if parent:
        cmds.parent(follow_group, parent)
        
    if follow_scale:
        connect_scale(source_transform, follow_group)
        
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
    
    if orient_only:
        connect_rotate(source_transform, follow_group)
    
    #value = cmds.getAttr('%s.rotateOrder' % source_transform)
    #cmds.setAttr('%s.rotateOrder' % follow_group, value)
    
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

def create_multi_follow(source_list, target_transform, node = None, constraint_type = 'parentConstraint', attribute_name = 'follow', value = None):
    
    if node == None:
        node = target_transform
    
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
    
    if value == None:
        value = (len(source_list)-1)
        
    cmds.setAttr('%s.%s' % (node, attribute_name), value)
    
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

def create_spline_ik_stretch(curve, joints, node_for_attribute = None, create_stretch_on_off = False, create_bulge = True):
    
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
        
        if create_bulge:
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

def create_distance_scale(xform1, xform2, axis = 'X', offset = 1):
    
    locator1 = cmds.spaceLocator(n = inc_name('locatorDistance_%s' % xform1))[0]
    
    MatchSpace(xform1, locator1).translation()
    
    locator2 = cmds.spaceLocator(n = inc_name('locatorDistance_%s' % xform2))[0]
    MatchSpace(xform2, locator2).translation()
    
    distance = cmds.createNode('distanceBetween', n = inc_name('distanceBetween_%s' % xform1))
    
    multiply = cmds.createNode('multiplyDivide', n = inc_name('multiplyDivide_%s' % xform1))
    
    cmds.connectAttr('%s.worldMatrix' % locator1, '%s.inMatrix1' % distance)
    cmds.connectAttr('%s.worldMatrix' % locator2, '%s.inMatrix2' % distance)
    
    distance_value = cmds.getAttr('%s.distance' % distance)
    
    """
    if condition != None:
    
        distance_offset = distance_value
        
        if type(condition) == float:
            distance_offset = distance_value * condition
        
        condition = cmds.createNode('condition', n = inc_name('condition_%s' % xform1))
        
        cmds.setAttr('%s.operation' % condition, 2)
        
        cmds.connectAttr('%s.distance' % distance, '%s.firstTerm' % condition)
        cmds.setAttr('%s.secondTerm' % condition, distance_offset)
        
        cmds.connectAttr('%s.distance' % distance, '%s.colorIfFalseR' % condition)
        cmds.setAttr('%s.colorIfTrueR' % condition, distance_offset)
        
        cmds.connectAttr('%s.outColorR' % condition, '%s.input1X' % multiply)
    
    
    if condition == None:
        
    """
    
    if offset != 1:
        quick_driven_key('%s.distance' %distance, '%s.input1X' % multiply, [distance_value, distance_value*2], [distance_value, distance_value*2*offset], infinite = True)
    
    if offset == 1:
        cmds.connectAttr('%s.distance' % distance, '%s.input1X' % multiply)
    
    cmds.setAttr('%s.input2X' % multiply, distance_value)
    cmds.setAttr('%s.operation' % multiply, 2)
        
    cmds.connectAttr('%s.outputX' % multiply, '%s.scale%s' % (xform1, axis))
        
    return locator1, locator2
    
    
    
@undo_chunk
def add_orient_attributes(transform):
    if type(transform) != list:
        transform = [transform]
    
    for thing in transform:
        
        orient = OrientJointAttributes(thing)
        orient.set_default_values()
    
#@undo_chunk
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
        position = cmds.xform(transform, q = True, ws = True, rp = True)
        
    if position[0] > 0:
        side = 'L'

    if position[0] < 0:
        side = 'R'
        
    if position[0] < center_tolerance and position[0] > center_tolerance*-1:
        side = 'C'
            
    return side

def create_no_twist_aim(source_transform, target_transform, parent):

    top_group = cmds.group(em = True, n = inc_name('no_twist_%s' % source_transform))
    cmds.parent(top_group, parent)
    cmds.pointConstraint(source_transform, top_group)


    #axis aim
    aim = cmds.group(em = True, n = inc_name('aim_%s' % target_transform))
    target = cmds.group(em = True, n = inc_name('target_%s' % target_transform))
        
    MatchSpace(source_transform, aim).translation_rotation()
    MatchSpace(source_transform, target).translation_rotation()
    
    xform_target = create_xform_group(target)
    #cmds.setAttr('%s.translateX' % target, 1)
    cmds.move(1,0,0, target, r = True, os = True)
    
    cmds.parentConstraint(source_transform, target, mo = True)
    
    cmds.aimConstraint(target, aim, wuo = parent, wut = 'objectrotation', wu = [0,0,0])
    
    cmds.parent(aim, xform_target, top_group)
    
    #pin up to axis
    pin_aim = cmds.group(em = True, n = inc_name('aim_pin_%s' % target_transform))
    pin_target = cmds.group(em = True, n = inc_name('target_pin_%s' % target_transform))
    
    MatchSpace(source_transform, pin_aim).translation_rotation()
    MatchSpace(source_transform, pin_target).translation_rotation()
    
    xform_pin_target = create_xform_group(pin_target)
    cmds.move(0,0,1, pin_target, r = True)
    
    cmds.aimConstraint(pin_target, pin_aim, wuo = aim, wut = 'objectrotation')
    
    cmds.parent(xform_pin_target, pin_aim, top_group)
       
    #twist_aim
    #tool_maya.create_follow_group('CNT_SPINE_2_C', 'xform_CNT_TWEAK_ARM_1_%s' % side)
    cmds.pointConstraint(source_transform, target_transform, mo = True)
    
    cmds.parent(pin_aim, aim)
    
    cmds.orientConstraint(pin_aim, target_transform, mo = True)

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

@undo_chunk
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
    

    
    
@undo_chunk
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
        
@undo_chunk
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
    
    return ffd, lattice, base
    
    

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

@undo_chunk
def split_mesh_at_skin(mesh, skin_deformer = None, vis_attribute = None, constrain = False):
    
    if constrain:
        group = cmds.group(em = True, n = inc_name('split_%s' % mesh))
    
    if not skin_deformer:
        skin_deformer =  find_deformer_by_type(mesh, 'skinCluster')
    
    index_face_map = get_faces_at_skin_influence(mesh, skin_deformer)

    #cmds.undoInfo(state = False)
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
    
    #cmds.undoInfo(state = True)
    cmds.showHidden(mesh)
    
    if constrain:
        return group
    
@undo_chunk
def transfer_weight(source_joint, target_joints, mesh):
    if not mesh:
        return
    
    skin_deformer = find_deformer_by_type(mesh, 'skinCluster')
    
    if not skin_deformer:
        return
    
    #cmds.undoInfo(state = False)
    
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
        
    #cmds.undoInfo(state = True)
    
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
    
    vtool.util.show('converting %s' % wire_deformer)
    
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
    
    vtool.util.show('converting %s' % wire_deformer)
    
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
    
@undo_chunk   
def skin_mesh_from_mesh(source_mesh, target_mesh, exclude_joints = [], include_joints = [], uv_space = False):
    
    vtool.util.show('skinning %s' % target_mesh)
    
    
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
                
    #cmds.undoInfo(state = True)
      

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

def skin_group(joint, group):
    
    rels = cmds.listRelatives(group, ad = True, f = True)
    
    print rels
    
    for rel in rels:
        
        name = rel.split('|')[-1]
        
        try:
            cmds.skinCluster(joint, rel, tsb = True, n = 'skin_%s' % name)
        except:
            pass
            

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
    
def wire_to_mesh(edges, geometry, description):
    
    group = cmds.group(em = True, n = inc_name('setup_%s' % description))
    
    edge_path = get_edge_path(edges)
    
    curve = edges_to_curve(edge_path, description)
    
    cmds.parent(curve, group)
    
    wire_deformer, wire_curve = cmds.wire(geometry,  gw = False, w = curve, n = 'wire_%s' % description)
    
    spans = cmds.getAttr('%s.spans' % curve)
    
    cmds.dropoffLocator( 1, 1, wire_deformer, '%s.u[0]' % curve, '%s.u[%s]' % (curve,spans) )
    
    cmds.addAttr(curve, ln = 'twist', k = True)
    cmds.connectAttr('%s.twist' % curve, '%s.wireLocatorTwist[0]' % wire_deformer)
    cmds.connectAttr('%s.twist' % curve, '%s.wireLocatorTwist[1]' % wire_deformer)
    
    return group
    
    
@undo_chunk
def weight_hammer_verts(verts = None, print_info = True):
    
    if verts:
        verts = cmds.ls(verts, flatten = True)
    
    if not verts:
        verts = cmds.ls(sl = True, flatten = True)
    
    count = len(verts)
    inc = 0
    
    for vert in verts:
        cmds.select(cl = True)
        cmds.select(vert)
        
        if print_info:
            vtool.util.show(inc, 'of', count)
            
        
        mel.eval('weightHammerVerts;')
            
        inc += 1
        

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

@undo_chunk
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
    
    source_mesh_name = source_mesh.split('|')[-1]
    
    if not blendshape:
        blendshape = 'blendshape_%s' % target_mesh
    
    if cmds.objExists(blendshape):
        count = cmds.blendShape(blendshape, q= True, weightCount = True)
        cmds.blendShape(blendshape, edit=True, tc = False, t=(target_mesh, count+1, source_mesh, 1.0) )
        cmds.setAttr('%s.%s' % (blendshape, source_mesh_name), weight)
        
    if not cmds.objExists(blendshape):
        cmds.blendShape(source_mesh, target_mesh, tc = False, weight =[0,weight], n = blendshape, foc = True)
        
    return blendshape 
    
def reset_tweak(tweak_node):
    
    if not cmds.objExists('%s.vlist' % tweak_node):
        return
    indices = get_indices('%s.vlist' % tweak_node)
    
    for index in indices:
        cmds.setAttr('%s.vlist[%s].xVertex' % (tweak_node, index), 0.0)
        cmds.setAttr('%s.vlist[%s].yVertex' % (tweak_node, index), 0.0)
        cmds.setAttr('%s.vlist[%s].zVertex' % (tweak_node, index), 0.0)

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
    try:
        cmds.connectAttr('%s.rotateOrder' % source_transform, '%s.rotateOrder' % target_transform)
    except:
        pass
        #vtool.util.show('Could not connect %s.rotateOrder into %s.rotateOrder. This could cause issues if rotate order changed.' % (source_transform, target_transform))
        
    
def connect_scale(source_transform, target_transform):
    
    connect_vector_attribute(source_transform, target_transform, 'scale')

def connect_translate_plus(source_transform, target_transform):
    
    plus = cmds.createNode('plusMinusAverage', n = 'plus_%s' % target_transform)
    
    input_x = get_attribute_input('%s.translateX' % target_transform)
    input_y = get_attribute_input('%s.translateY' % target_transform)
    input_z = get_attribute_input('%s.translateZ' % target_transform)
    
    value_x = cmds.getAttr('%s.translateX' % source_transform)
    value_y = cmds.getAttr('%s.translateY' % source_transform)
    value_z = cmds.getAttr('%s.translateZ' % source_transform)
    
    current_value_x = cmds.getAttr('%s.translateX' % target_transform)
    current_value_y = cmds.getAttr('%s.translateY' % target_transform)
    current_value_z = cmds.getAttr('%s.translateZ' % target_transform)
    
    cmds.connectAttr('%s.translateX' % source_transform, '%s.input3D[0].input3Dx' % plus)
    cmds.connectAttr('%s.translateY' % source_transform, '%s.input3D[0].input3Dy' % plus)
    cmds.connectAttr('%s.translateZ' % source_transform, '%s.input3D[0].input3Dz' % plus)
    
    cmds.setAttr('%s.input3D[1].input3Dx' % plus, -1*value_x)
    cmds.setAttr('%s.input3D[1].input3Dy' % plus, -1*value_y)
    cmds.setAttr('%s.input3D[1].input3Dz' % plus, -1*value_z)
    
    #cmds.setAttr('%s.input3D[2].input3Dx' % plus, -1*current_value_x)
    #cmds.setAttr('%s.input3D[2].input3Dy' % plus, -1*current_value_y)
    #cmds.setAttr('%s.input3D[2].input3Dz' % plus, -1*current_value_z)
    
    disconnect_attribute('%s.translateX' % target_transform)
    disconnect_attribute('%s.translateY' % target_transform)
    disconnect_attribute('%s.translateZ' % target_transform)
    
    cmds.connectAttr('%s.output3Dx' % plus, '%s.translateX' % target_transform)
    cmds.connectAttr('%s.output3Dy' % plus, '%s.translateY' % target_transform)
    cmds.connectAttr('%s.output3Dz' % plus, '%s.translateZ' % target_transform)
    
    if input_x:
        
        cmds.connectAttr(input_x, '%s.input3D[3].input3Dx' % plus)
    if input_y:
        cmds.connectAttr(input_y, '%s.input3D[3].input3Dy' % plus)
    if input_z:
        cmds.connectAttr(input_z, '%s.input3D[3].input3Dz' % plus)
    
    return plus
    
def connect_translate_multiply(source_transform, target_transform, value, respect_value = False):
    
    target_transform_x = '%s.translateX' % target_transform
    target_transform_y = '%s.translateY' % target_transform
    target_transform_z = '%s.translateZ' % target_transform
    
    target_input_x = get_attribute_input(target_transform_x)
    target_input_y = get_attribute_input(target_transform_y)
    target_input_z = get_attribute_input(target_transform_z)
    
    if target_input_x:
        
        if cmds.nodeType(target_input_x) == 'plusMinusAverage':
            plus = target_input_x.split('.')[0]
            indices = get_indices('%s.input3D' % plus)
            
            target_transform_x = '%s.input3D[%s].input3Dx' % (plus, indices)
            target_transform_y = '%s.input3D[%s].input3Dy' % (plus, indices)
            target_transform_z = '%s.input3D[%s].input3Dz' % (plus, indices)
            
        if not cmds.nodeType(target_input_x) == 'plusMinusAverage':
            
            plus = cmds.createNode('plusMinusAverage', n = 'plus_%s' % target_transform)
            
            cmds.connectAttr(target_input_x, '%s.input3D[0].input3Dx' % plus)
            cmds.connectAttr(target_input_y, '%s.input3D[0].input3Dy' % plus)
            cmds.connectAttr(target_input_z, '%s.input3D[0].input3Dz' % plus)
            
            disconnect_attribute(target_transform_x)
            disconnect_attribute(target_transform_y)
            disconnect_attribute(target_transform_z)
            
            cmds.connectAttr('%s.output3Dx' % plus, target_transform_x)
            cmds.connectAttr('%s.output3Dy' % plus, target_transform_y)
            cmds.connectAttr('%s.output3Dz' % plus, target_transform_z)
            
            target_transform_x = '%s.input3D[1].input3Dx' % plus
            target_transform_y = '%s.input3D[1].input3Dy' % plus
            target_transform_z = '%s.input3D[1].input3Dz' % plus
    
    multiply = connect_multiply('%s.translateX' % source_transform, target_transform_x, value, plus = False)

    if respect_value:
            plus = cmds.createNode('plusMinusAverage', n = 'plus_%s' % target_transform)
    
            value_x = cmds.getAttr('%s.translateX' % source_transform)
            value_y = cmds.getAttr('%s.translateY' % source_transform)
            value_z = cmds.getAttr('%s.translateZ' % source_transform)
    
            cmds.connectAttr('%s.translateX' % source_transform, '%s.input3D[0].input3Dx' % plus)
            cmds.connectAttr('%s.translateY' % source_transform, '%s.input3D[0].input3Dy' % plus)
            cmds.connectAttr('%s.translateZ' % source_transform, '%s.input3D[0].input3Dz' % plus)
    
            cmds.setAttr('%s.input3D[1].input3Dx' % plus, -1*value_x)
            cmds.setAttr('%s.input3D[1].input3Dy' % plus, -1*value_y)
            cmds.setAttr('%s.input3D[1].input3Dz' % plus, -1*value_z)

            disconnect_attribute('%s.input1X' % multiply)
    
            cmds.connectAttr('%s.output3Dx' % plus, '%s.input1X' % multiply)
            cmds.connectAttr('%s.output3Dy' % plus, '%s.input1Y' % multiply)
            cmds.connectAttr('%s.output3Dz' % plus, '%s.input1Z' % multiply)
    
    if not respect_value:
        cmds.connectAttr('%s.translateY' % source_transform, '%s.input1Y' % multiply)
        cmds.connectAttr('%s.translateZ' % source_transform, '%s.input1Z' % multiply)
                
    cmds.connectAttr('%s.outputY' % multiply, target_transform_y)
    cmds.connectAttr('%s.outputZ' % multiply, target_transform_z)
    
    try:
        cmds.setAttr('%s.input2Y' % multiply, value)
        cmds.setAttr('%s.input2Z' % multiply, value)
    except:
        pass
    
    if not respect_value:
        return multiply
    if respect_value:
        return multiply, plus
    

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
    
    input_attribute = get_attribute_input( target_attribute  )

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
            cmds.setAttr(attribute_name, k = False)
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
    
@undo_chunk
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

@undo_chunk
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

@undo_chunk
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
    

def quick_driven_key(source, target, source_values, target_values, infinite = False):
    
    for inc in range(0, len(source_values)):
        
        cmds.setDrivenKeyframe(target,cd = source, driverValue = source_values[inc], value = target_values[inc], itt = 'spline', ott = 'spline')


    if infinite:
        cmds.setInfinity(target, postInfinite = 'linear', preInfinite = 'linear') 
            
        
        

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
    

