# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.



import sys

import string
import re
import traceback

import vtool.util
import api
import curve




if vtool.util.is_in_maya():
    import maya.cmds as cmds
    import maya.mel as mel
    
    import maya.OpenMaya as OpenMaya

vtool.util.warning('This module: vtool.maya_lib.util, is deprecated. It should no longer be used.')
 
undo_chunk_active = False
current_progress_bar = None

#--- decorators

def undo_off(function):
    """
    Maya sometimes has operations that generate a huge undo stack and use lots of memory.
    This is meant to handle turning off the undo temporarily for the duration of a function.
    
    Arg
        function: Pass in the instance of the fucntion to wrap.
    """
    
    def wrapper(*args, **kwargs):
        
        global current_progress_bar
        
        if not vtool.util.is_in_maya():
            return
        return_value = None
        
        undo_state = cmds.undoInfo(state = True, q = True)
        
        if undo_state:
            cmds.undoInfo(state = False)
        
        try:
            return_value = function(*args, **kwargs)
        except:
            
            if undo_state:
                cmds.undoInfo( state = True )
                
            raise(RuntimeError)
        
            if current_progress_bar:
                current_progress_bar.end()
                current_progress_bar = None
        
        if undo_state:          
            cmds.undoInfo( state = True )
        
        return return_value
        
    return wrapper

def undo_chunk(function):
    """
    Maya sometimes has operations that generate a huge undo stack and use lots of memory.
    This is meant to handle creating one undo chunk for a function that has many small operations.
    
    Arg
        function: Pass in the instance of the fucntion to wrap.
    """
    
    def wrapper(*args, **kwargs):
        
        global undo_chunk_active
        global current_progress_bar
        
        if not vtool.util.is_in_maya():
            return
    
        undo_state = cmds.undoInfo(state = True, q = True)
        
        return_value = None
        
        closed = True
        
        if not undo_chunk_active and undo_state:
            cmds.undoInfo(openChunk = True)
                        
            undo_chunk_active = True
            closed = False
        
        try:
            return_value = function(*args, **kwargs)
        except:
            
            if undo_chunk_active:
                cmds.undoInfo(closeChunk = True)
                
                closed = True
                
                undo_chunk_active = False
            
            raise(RuntimeError)

            if current_progress_bar:
                current_progress_bar.end()
                current_progress_bar = None
            
        if not closed:
            if undo_chunk_active:
                cmds.undoInfo(closeChunk = True)
                
                undo_chunk_active = False

        
        return return_value
                     
    return wrapper

#--- classes

class ScriptEditorRead(object):
    """
    Not currently being used. This takes control of the script editor.  Led to Maya crashing frequently.
    """
    
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
    Not currently being used. This is the callback function that gets called when Maya wants to show something in the script editor output.
    It will take the msg and output it to the terminal rather than the Maya Script Editor.
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

class FindUniqueName(vtool.util.FindUniqueString):
    """
    core!!!
    This class is intended to find a name that doesn't clash with other names in the Maya scene.
    It will increment the last number in the name. 
    If no number is found it will append a 1 to the end of the name.
    """
    
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

class TrackNodes(object):
    """
    core!!!
    This helps track new nodes that get added to a scene after a function runs.
    
    Usage:
    track_nodes = TrackNodes()
    track_nodes.load()
    my_function()
    new_nodes = track_nodes.get_delta()
    """
    def __init__(self):
        self.nodes = None
        self.node_type = None
        self.delta = None
        
    def load(self, node_type = None):
        """
            node_type corresponds to the maya node type. 
            For example, you can give node_type the string "animCurve" to load only keyframes.
            When after running get_delta(), the delta will only contain keyframes.
            
        Args:
            node_type (str): Maya named type, ie animCurve, transform, joint, etc
            
        Return
            None
        """
        self.node_type = node_type
        
        if self.node_type:
            self.nodes = cmds.ls(type = node_type)
        if not self.node_type:
            self.nodes = cmds.ls()
        
    def get_delta(self):
        """
        Get the new nodes in the Maya scene created after load() was executed.
        The load() node_type variable is stored in the class and used when getting the delta.
            
        Return
            (list) : list of new nodes.
        """
        if self.node_type:
            current_nodes = cmds.ls(type = self.node_type)
        if not self.node_type:
            current_nodes = cmds.ls()
            
        new_set = set(current_nodes).difference(self.nodes)
        
        
        return list(new_set)
        
class ProgressBar(object):
    """
    core!!!
    Manipulate the maya progress bar.
    
    Args:
        title (str): The name of the progress bar.
        count (int): The number of items to iterate in the progress bar.
    """
    
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
        
        global current_progress_bar 
        current_progress_bar = self
    
    def inc(self, inc = 1):
        """
        Set the current increment.
        """
        if is_batch():
            return
        
        cmds.progressBar(self.progress_ui, edit=True, step=inc)
        
            
    def end(self):
        """
        End the progress bar.
        """
        if is_batch():
            return
        
        cmds.progressBar(self.progress_ui, edit=True, ep = True)
        
    def status(self, status_string):
        """
        Set that status string of the progress bar.
        """
        if is_batch():
            return
        
        cmds.progressBar(self.progress_ui, edit=True, status = status_string)
        
    def break_signaled(self):
        """
        break the progress bar loop so that it stops and disappears.
        """
        if is_batch():
            return True
        
        break_progress = cmds.progressBar(self.progress_ui, query=True, isCancelled=True )

        if break_progress:
            self.end()
            return True
        
        return False
    


        
#--- variables attributes

class MayaVariable(vtool.util.Variable):
    """
    Convenience class for dealing with Maya attributes.
    """
    
    
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
            if not self.variable_type == 'message':
                
                    cmds.setAttr(self._get_node_and_variable(), self.value )

            if self.variable_type == 'message':
                if self.value:
                    connect_message(self.value, self.node, self.name)
            
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
            return self.keyable
        
        return cmds.getAttr(self._get_node_and_variable(), k = True)

    def _get_value(self):
        if not self.exists():
            return
        
        if self.variable_type == 'message':
            return get_attribute_input(self._get_node_and_variable(), node_only = True)
        
        if not self.variable_type == 'message':
            return cmds.getAttr(self._get_node_and_variable())

    def _update_states(self):
        
        self._set_keyable_state()
        self._set_lock_state()
        self._set_value()

    def exists(self):
        """
        Return
            (bool):
        """
        return cmds.objExists(self._get_node_and_variable())

    #--- set
    def set_name(self, name):
        """
        Set the name of the variable.
        
        Args:
            name (str)
            
        """
        var_name = self._get_node_and_variable()
        
        if cmds.objExists(var_name):
            cmds.renameAttr(var_name, name)
            
        super(MayaVariable, self).set_name(name)
        
        var_name = self._get_node_and_variable()
    
    def set_value(self, value):
        """
        Set the value of the variable.
        
        Args:
            value
            
        """
        super(MayaVariable, self).set_value(value)
        self._set_value()
        
    def set_locked(self, bool_value):
        """
        Set the lock state of the variable.
        
        Args:
            bool_value (bool)
            
        """
        self.locked = bool_value
        self._set_lock_state()
        
    def set_keyable(self, bool_value):
        """
        Set the keyable state of the variable.
        
        Args:
            bool_value (bool)
            
        """
        
        self.keyable = bool_value
        self._set_keyable_state()

    def set_variable_type(self, name):
        """
        Set the variable type, check Maya documentation.
        """
        
        self.variable_type = name

    def set_node(self, name):
        """
        Set the node where the variable should live.
        
        Args:
            name (str)
            
        """
        self.node = name

    #--- get

    def get_value(self):
        """
        Get the variables value.
        
        Return
            value
        """
        return self._get_value()
        
    def get_name(self, name_only = False):
        """
        Get the name of the variable.
        
        Args:
            name_only (bool): If True just the variable name is returned. If False the node and variable are returned: "node.variable".
        """
        
        if self.node and not name_only:
            return self._get_node_and_variable()
        if not self.node or name_only:
            return self.name

    def get_dict(self):
        """
        Get a dictionary that represents the state of the variable.
        
        Return
            (dict)
        """
        
        var_dict = {}
        
        var_dict['value'] = self._get_value()
        var_dict['type'] = self.variable_type
        var_dict['key'] = self._get_keyable_state()
        var_dict['lock'] = self._get_lock_state()
        
        return var_dict
    
    def set_dict(self, var_dict):
        """
        Set a dictionary that describes the variable. See get_dict.
        
        Args:
            var_dict (dict): A dictionary created from get_dict.
            
        """
        value = var_dict['value']
        self.set_value(value)
        
        type_value = var_dict['type']
        self.set_variable_type(type_value)
        
        keyable = var_dict['key']
        self.set_keyable(keyable)
        
        lock = var_dict['lock']
        self.set_locked(lock)
    
    def create(self, node = None):
        """
        Create the variable on the node.
        
        Args:
            node (str): The node for the variable.  If not set, set_node should be set.
            
        """
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
        """
        Delete the variable on the node.
        
        Args:
            node (str): The node for the variable.  If not set, set_node should be set.
            
        """
        if node:
            self.node = node
        
        #theses lines might cause bugs   
        self.locked = False
        self._set_lock_state()
        #------
            
        cmds.deleteAttr(self.node, at = self.name)
        
    def load(self):
        """
        Refresh the internal values.
        """
        self.value = self._get_value()
        self.locked = self._get_lock_state()
        self.keyable = self._get_keyable_state()
        
    def connect_in(self, attribute):
        """
        Connect the attribute into this variable.
        
        Args:
            attribute (str): 'node.attribute'
        
        """
        cmds.connectAttr(attribute, self._get_node_and_variable())
        
    def connect_out(self, attribute):
        """
        Connect from the variable into the attribute.
        
        Args:
            attribute (str): 'node.attribute'
        
        """
        cmds.connectAttr(self._get_node_and_variable(), attribute)
        
class MayaNumberVariable(MayaVariable):
    """
    Convenience class for dealing with Maya numeric attributes.
    """
    
    
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
        """
        Args:
            value (float): Minimum value constraint
        
        """
        self.min_value = value
        self._set_min_state()
    
    def set_max_value(self, value):
        """
        Args:
            value (float): Maximum value constraint
        
        """
        
        self.max_value = value
        self._set_max_state()
        
    def load(self):
        """
        Refresh the internal values.
        """
        super(MayaNumberVariable, self).load()
        
        self._get_min_state()
        self._get_max_state()
        
class MayaEnumVariable(MayaVariable):
    """
    Convenience class for dealing with Maya enum attributes.
    """
    
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

    

    def _set_enum_state(self, set_value = True):
        
        if not self.exists():
            return
        
        enum_name = string.join(self.enum_names, ':')
                
        if not enum_name:
            return
        
        value = self.get_value()
        
        cmds.addAttr(self._get_node_and_variable(), edit = True, enumName = enum_name)
        
        if set_value:
            self.set_value(value)
    
    def _set_value(self):
        if not self.enum_names:
            return
        
        self._set_enum_state(set_value = False)
        super(MayaEnumVariable, self)._set_value()
    
    def set_enum_names(self, name_list):
        """
        Args:
            name_list (list): List of strings to define the enum.
        """
        self.enum_names = name_list
        
        self._set_enum_state()

class MayaStringVariable(MayaVariable):
    """
    Convenience class for dealing with Maya string attributes.
    """
    
    def __init__(self, name):
        super(MayaStringVariable, self).__init__(name)
        self.variable_type = 'string'
        self.value = ''
    
class Attributes(object):
    """
    Still testing. Convenience class for dealing with groups of attributes.
    Currently only works on bool, long, short, float, double
    """
    numeric_attributes = ['bool', 'long', 'short', 'float', 'double']
    
    def __init__(self, node):
        
        self.node = node
        
        self.variables = []
        self.attribute_dict = {}
        
        
    def _get_variable_instance(self, name, var_type):
                
        var = MayaVariable(name)
        
        if var_type in self.numeric_attributes:
            var = MayaNumberVariable(name)
            
        if var_type == 'enum':
            var = MayaEnumVariable(name)
            
        if var_type == 'string':
            var = MayaStringVariable(name)
        
        var.set_variable_type(var_type)
        var.set_node(self.node)    
        
        return var
        
    def _retrieve_attribute(self, attribute_name):
        
        node_and_attribute = '%s.%s' % (self.node, attribute_name)
        
        if not cmds.objExists(node_and_attribute):
            return
        
        var_type = cmds.getAttr(node_and_attribute, type = True)
        
        var = self._get_variable_instance(attribute_name, var_type)
        var.set_node(self.node)
        
        return var
        
    def _store_attributes(self):
        custom_attributes = cmds.listAttr(self.node, ud = True)
        
        self.variables = []
        
        for attribute in custom_attributes:
            
            var = self._retrieve_attribute(attribute)    
        
            var_dict = var.get_dict()    
            
            self.attribute_dict[attribute] = var_dict
            
            self.variables.append(var)
            
        return self.variables
    
    def _retrieve_attributes(self):
        
        variables = self._store_attributes()
        return variables    
    
    def delete_all(self, retrieve = False):
        """
        Delete all loaded variables on a node.
        """
        variables = []
        
        if retrieve or not self.variables:
            
            variables = self._retrieve_attributes()
        if not retrieve and self.variables:
            variables = self.variables
        
        for var in variables:
            
            var.delete()
        
    def create_all(self):
        
        for var in self.variables:
            
            var.create()
        
    def delete(self, name):
        
        self.delete_all()
        
        variables = []
        
        for variable in self.variables:
            
            if variable.name == name:
                continue
        
            variables.append(variable)        
            variable.create()
            
        self.variables = variables
            
    def create(self, name, var_type, index = None):
        
        self.delete_all()
        
        var_count = len(self.variables)
        
        remove_var = None
        
        for var in self.variables:
            if var.name == name:
                remove_var = var
                break
                            
        if remove_var:
            remove_index = self.variables.index(remove_var)
            self.variables.pop(remove_index)
            
        var = self._get_variable_instance(name, var_type)
                
        if index > var_count:
            index = None
        
        if index != None:
            self.variables.insert(index, var)
        if index == None:
            self.variables.append(var)
                
        self.create_all()
    
    def get_variables(self):
        self._store_attributes()
        
        return self.variables
    
    def get_variable(self, attribute_name):
        
        self._store_attributes()
        
        return self._retrieve_attribute(attribute_name)
    
    def rename_variable(self, old_name, new_name):
        
        if not self.node:
            return
        
        var = self.get_variable(old_name)
        
        if not var:
            vtool.util.warning('Could not rename attribute, %s.%s.' % (self.node, old_name))
            return
        
        var.set_name(new_name)
        
        
        self._store_attributes()
        
        connections = Connections(self.node)
        connections.disconnect()
        
        self.delete_all()
        self.create_all()
        
        connections.connect()
        
    
#--- rig

class BoundingBox(vtool.util.BoundingBox):
    """
    space!!!
    """
    def __init__(self, thing):
        
        self.thing = thing
        
        xmin, ymin, zmin, xmax, ymax, zmax = cmds.exactWorldBoundingBox(self.thing)
        
        super(BoundingBox, self).__init__([xmin, ymin, zmin], 
                                          [xmax, ymax, zmax])
          
class OrientJointAttributes(object):
    """
    attr!!!
    Creates attributes on a node that can then be used with OrientAttributes
    """
    def __init__(self, joint = None):
        self.joint = joint
        self.attributes = []
        self.title = None
        
        if joint:
            self._create_attributes()
    
    def _create_attributes(self):
        
        self.title = MayaEnumVariable('Orient_Info'.upper())
        self.title.create(self.joint)
        
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
        
        if self.title:
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
        """
        Set a joint to create attributes on.
        
        Args:
            joint (str): The name of the joint.
        """
        self.joint = joint
        
        self._create_attributes()
    
    def get_values(self):
        """
        Get the orient settings in a dictionary.
        
        Return
            (dict)
        """
        value_dict = {}
        
        for attr in self.attributes:
            value_dict[attr.get_name(True)] = attr.get_value()
            
        return value_dict
    
    def set_default_values(self):
        """
        Reset the attributes to default.
        """
        self._set_default_values()

    def delete(self):
        """
        Delete the attributes off of the joint set with set_joint.
        """
        self._delete_attributes()
          
class OrientJoint(object):
    """
    space!!!
    This will orient the joint using the attributes created with OrientJointAttributes.
    """
    
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
        
        parent = cmds.listRelatives(self.joint, p = True, f = True)
        
        if parent:
            self.parent = parent[0]
            
            grand_parent = cmds.listRelatives(self.parent, p = True, f = True)
            
            if grand_parent:
                self.grand_parent = grand_parent[0]
                
        children = cmds.listRelatives(self.joint, f = True)
        
        if children:
            self.child = children[0]
            
            grand_children = cmds.listRelatives(self.child, f = True)
            
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
                
                vtool.util.warning('Could not orient %s fully with current triangle plane settings.' % self.joint)
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
        children = cmds.listRelatives(self.joint, f = True)
        
        if children:
            
            children = cmds.parent(children, w = True)
        
        cmds.makeIdentity(self.joint, apply = True, r = True, s = True)
        
        if children:
            cmds.parent(children, self.joint)
        
      
    def set_aim_vector(self, vector_list):
        """
        Args:
            vector_list (list): [0,0,0] vector that defines what axis should aim.  
            If joint should aim with X axis then vector should be [1,0,0].  If joint should aim with Y axis then [0,1,0], etc.
            If up needs to be opposite of X axis then vector should be [-1,0,0].
        """
        self.aim_vector = vector_list
        
    def set_up_vector(self, vector_list):
        """
        Args:
            vector_list (list): [0,0,0] vector that defines what axis should aim up.  
            If joint should aim up with X axis then vector should be [1,0,0].  If joint should aim up with Y axis then [0,1,0], etc.
            If up needs to be opposite of X axis then vector should be [-1,0,0].
        """
        self.up_vector = vector_list
        
    def set_world_up_vector(self, vector_list):
        """
        Args:
            vector_list (list): [0,0,0] vector that defines what world up axis be.  
            If world should aim up with X axis then vector should be [1,0,0].  If world should aim up with Y axis then [0,1,0], etc.
            If up needs to be opposite of X axis then vector should be [-1,0,0].
        """
        self.world_up_vector = vector_list
        
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
        """
        self.aim_up_at = self._get_aim_up_at(int_value)
        
    def set_aim_up_at_object(self, name):
        self.aim_up_at = self._get_local_group(name)
        
        self.up_space_type = 'objectrotation'
        self.world_up_vector = [0,1,0]
        
    def run(self):
        
        
        self._freeze()
                
        self._get_relatives()
        self._pin()
        
        try:
            cmds.setAttr('%s.rotateAxisX' % self.joint, 0)
            cmds.setAttr('%s.rotateAxisY' % self.joint, 0)
            cmds.setAttr('%s.rotateAxisZ' % self.joint, 0)
        except:
            vtool.util.show('Could not zero out rotateAxis on %s. This may cause rig errors.' % self.joint)
        
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
    """
    space!!!
    This allows you to pin a transform so that its parent and child are not affected by any edits.
    """
    def __init__(self, xform_name):
        self.xform = xform_name
        self.delete_later = []

    def pin(self):
        """
        Create the pin constraints on parent and children.
        """
        parent = cmds.listRelatives(self.xform, p = True, f = True)
        
        if parent:
            
            parent = parent[0]
            
            
            pin = cmds.duplicate(parent, po = True, n = inc_name('pin1'))[0]
            
            try:
                cmds.parent(pin, w = True)
            except:
                pass
            
            #pin = cmds.group(em = True, n = 'pin1')    
            #MatchSpace(parent, pin).translation_rotation()
            
            constraint = cmds.parentConstraint(pin, parent, mo = True)[0]
            self.delete_later.append(constraint)
            self.delete_later.append(pin)
        
        children = cmds.listRelatives(self.xform, f = True)
        
        if not children:
            return
        
        for child in children:
            
            pin = cmds.duplicate(child, po = True, n = inc_name('pin1'))[0]
            
            try:
                cmds.parent(pin, w = True)
            except:
                pass
            
            constraint = cmds.parentConstraint(pin, child, mo = True)[0]
            self.delete_later.append(constraint)
            self.delete_later.append(pin)
            
    def unpin(self):
        """
        Remove the pin. This should be run after pin.
        """
        if self.delete_later:
            cmds.delete(self.delete_later)
        
    def get_pin_nodes(self):
        """
        Return
            (list): List of nodes involved in the pinning. Ususally includes constraints and empty groups.
        """
        return self.delete_later
    
class MayaNode(object):
    """
    attr!!!
    """
    def __init__(self, name = None):
        
        self.node = None
        
        self._create_node(name)
        
    def _create_node(self, name):
        pass
        
class MultiplyDivideNode(MayaNode):
    """
    attr!!!
    """
    
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
    """
    space!!!
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
        cmds.xform(self.target_transform, rp = scale_pivot_vector, ws = True)
        
    def translation(self):
        """
        Match just the translation
        """
        self._set_translation()
        
    def rotation(self):
        """
        Match just the rotation
        """
        self._set_rotation()
        
    def translation_rotation(self):
        """
        Match translation and rotation.
        """
                
        self._set_scale_pivot()
        self._set_rotate_pivot()
        
        self._set_translation()
        
        self._set_rotation()
        
    def translation_to_rotate_pivot(self):
        """
        Match translation of target to the rotate_pivot of source.
        """
        
        translate_vector = self._get_rotate_pivot()
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

class Control(object):
    """
    space!!!
    Convenience for creating controls
    
    Args:
        name (str): The name of a control that exists or that should be created.
    """
    
    def __init__(self, name):
        
        self.control = name
        self.curve_type = None
        
        if not cmds.objExists(self.control):
            self._create()
            
        self.shapes = get_shapes(self.control)
        
        if not self.shapes:
            vtool.util.warning('%s has no shapes' % self.control)
            
    def _create(self):
        
        self.control = cmds.circle(ch = False, n = self.control, normal = [1,0,0])[0]
        
        if self.curve_type:
            self.set_curve_type(self.curve_type)
        
    def _get_components(self):
        
        self.shapes = get_shapes(self.control)
        
        return get_components_from_shapes(self.shapes)
        
    def set_curve_type(self, type_name):
        """
        Set the curve type. The type of shape the curve should have.
        
        Args:
        
            type_name (str): eg. 'circle', 'square', 'cube', 'pin_round' 
        """
        
        curve_data = curve.CurveDataInfo()
        curve_data.set_active_library('default_curves')
        curve_data.set_shape_to_curve(self.control, type_name)
        
        self.shapes = get_shapes(self.control)
    
    def set_to_joint(self, joint = None):
        """
        Set the control to have a joint as its main transform type.
        
        Args:
            joint (str): The name of a joint to use. If none joint will be created automatically.
        """
        cmds.setAttr('%s.radius' % joint, l = True, k = False, cb = False)
        
        cmds.select(cl = True)
        name = self.get()
        
        joint_given = True
        
        if not joint:
            joint = cmds.joint()
            MatchSpace(name, joint).translation_rotation()
            joint_given = False
        
        shapes = self.shapes
        
        for shape in shapes:
            cmds.parent(shape, joint, r = True, s = True)
        
        if not joint_given:
            transfer_relatives(name, joint, reparent = True)
            cmds.rename(joint, name)
            
        if joint_given:
            transfer_relatives(name, joint, reparent = False)
            
            
        
        
        cmds.setAttr('%s.drawStyle' % joint, 2)
            
        curve_type_value = ''
            
        if cmds.objExists('%s.curveType' % name):
            curve_type_value = cmds.getAttr('%s.curveType' % name)    
        
        cmds.delete(name)
        
        self.control = joint
        
        if joint_given:
            rename_shapes(self.control)
            
        var = MayaStringVariable('curveType')
        var.create(joint)
        var.set_value(curve_type_value)
        
        
        
    def translate_shape(self, x,y,z):
        """
        Translate the shape curve cvs in object space.
        
        Args:
            x (float)
            y (float)
            z (float)
        """
        components = self._get_components()
        
        if components:
            cmds.move(x,y,z, components, relative = True, os = True)
        
    def rotate_shape(self, x,y,z):
        """
        Rotate the shape curve cvs in object space
        
        Args:
            x (float)
            y (float)
            z (float)
        """
        components = self._get_components()
        
        if components:
            cmds.rotate(x,y,z, components, relative = True)
            
    def scale_shape(self, x,y,z):
        """
        Scale the shape curve cvs relative to the current scale.
        
        Args:
            x (float)
            y (float)
            z (float)
        """
        components = self._get_components()
        
        pivot = cmds.xform( self.control, q = True, rp = True, ws = True)
        
        if components:
            cmds.scale(x,y,z, components, p = pivot, r = True)

    def color(self, value):
        """
        Set the color of the curve.
        
        Args:
            value (int): This corresponds to Maya's color override value.
        """
        shapes = get_shapes(self.control)
        
        set_color(shapes, value)
    
    def show_rotate_attributes(self):
        """
        Unlock and set keyable the control's rotate attributes.
        """
        cmds.setAttr('%s.rotateX' % self.control, l = False, k = True)
        cmds.setAttr('%s.rotateY' % self.control, l = False, k = True)
        cmds.setAttr('%s.rotateZ' % self.control, l = False, k = True)
        
    def show_scale_attributes(self):
        """
        Unlock and set keyable the control's scale attributes.
        """
        cmds.setAttr('%s.scaleX' % self.control, l = False, k = True)
        cmds.setAttr('%s.scaleY' % self.control, l = False, k = True)
        cmds.setAttr('%s.scaleZ' % self.control, l = False, k = True)
    
    def hide_attributes(self, attributes):
        """
        Lock and hide the given attributes on the control.
        
        Args:
            
            attributes (list): List of attributes, eg. ['translateX', 'translateY']
        """
        hide_attributes(self.control, attributes)
        
    def hide_translate_attributes(self):
        """
        Lock and hide the translate attributes on the control.
        """
        
        hide_attributes(self.control, ['translateX',
                                     'translateY',
                                     'translateZ'])
        
    def hide_rotate_attributes(self):
        """
        Lock and hide the rotate attributes on the control.
        """
        hide_attributes(self.control, ['rotateX',
                                     'rotateY',
                                     'rotateZ'])
        
    def hide_scale_attributes(self):
        """
        Lock and hide the scale attributes on the control.
        """
        hide_attributes(self.control, ['scaleX',
                                     'scaleY',
                                     'scaleZ'])
        
    def hide_visibility_attribute(self):
        """
        Lock and hide the visibility attribute on the control.
        """
        hide_attributes(self.control, ['visibility'])
    
    def hide_scale_and_visibility_attributes(self):
        """
        Lock and hide the visibility and scale attributes on the control.
        """
        self.hide_scale_attributes()
        self.hide_visibility_attribute()
    
    def hide_keyable_attributes(self):
        """
        Lock and hide all keyable attributes on the control.
        """
        hide_keyable_attributes(self.control)
        
    def rotate_order(self, xyz_order_string):
        """
        Set the rotate order on a control.
        """
        cmds.setAttr('%s.rotateOrder' % self.node, xyz_order_string)
    
    def color_respect_side(self, sub = False, center_tolerance = 0.001):
        """
        Look at the position of a control, and color it according to its side on left, right or center.
        
        Args:
            sub (bool): Wether to set the color to sub colors.
            center_tolerance (float): The distance the control can be from the center before its considered left or right.
            
        Return
            str: The side the control is on in a letter. Can be 'L','R' or 'C'
        """
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
        """
        Return
            str: The name of the control.
        """
        return self.control
    
    def create_xform(self):
        """
        Create an xform above the control.
        
        Return
            str: The name of the xform group.
        """
        xform = create_xform_group(self.control)
        
        return xform
        
    def rename(self, new_name):
        """
        Give the control a new name.
        
        Args:
            
            name (str): The new name.
        """
        new_name = cmds.rename(self.control, inc_name(new_name))
        self.control = new_name

    def delete_shapes(self):
        """
        Delete the shapes beneath the control.
        """
        self.shapes = get_shapes(self.control)
        
        cmds.delete(self.shapes)
        self.shapes = []
        
class IkHandle(object):
    """
    space!!!
    """
    
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
        ik_handle, effector = cmds.ikHandle( name = inc_name(self.name),
                                       startJoint = self.start_joint,
                                       endEffector = self.end_joint,
                                       sol = self.solver_type )
                           
        cmds.rename(effector, 'effector_%s' % ik_handle)
        self.ik_handle = ik_handle
        
    def _create_spline_ik(self):
        
        if self.curve:
            
            ik_handle = cmds.ikHandle(name = inc_name(self.name),
                                           startJoint = self.start_joint,
                                           endEffector = self.end_joint,
                                           sol = self.solver_type,
                                           curve = self.curve, ccv = False, pcv = False)
            
            cmds.rename(ik_handle[1], 'effector_%s' % ik_handle[0])
            self.ik_handle = ik_handle[0]
            
        if not self.curve:
            
            ik_handle = cmds.ikHandle(name = inc_name(self.name),
                                           startJoint = self.start_joint,
                                           endEffector = self.end_joint,
                                           sol = self.solver_type,
                                           scv = False,
                                           pcv = False)
            
            cmds.rename(ik_handle[1], 'effector_%s' % ik_handle[0])
            self.ik_handle = ik_handle[0]
            
            self.curve = ik_handle[2]
            self.curve = cmds.rename(self.curve, inc_name('curve_%s' % self.name))
            
            self.ik_handle = ik_handle[0]
        

        
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
    
    def set_full_name(self, fullname):
        self.name = fullname
    
    def create(self):
        
        if not self.start_joint or not self.end_joint:
            return
        
        if not self.curve and not self.solver_type == self.solver_spline:
            self._create_regular_ik()
        
        if self.curve or self.solver_type == self.solver_spline:
            self._create_spline_ik()

        
        return self.ik_handle

class ConstraintEditor(object):
    """
    space!!!
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
    """
    attr!!!
    """
    
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
    """
    rigs
    """
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
        self.vector = False
        self.extra_joint = None
        self.damp_name = 'dampen'
    
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
        
        if self.vector:
            cmds.connectAttr('%s.translate' % top_locator, '%s.point1' % distance_between)
            cmds.connectAttr('%s.translate' % btm_locator, '%s.point2' % distance_between)
        
        if not self.vector:
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
        
        self.divide_distance = multiply.node
        
        return multiply.node

    def _create_offsets(self, divide_distance, distance_node):
        stretch_offsets = []
        
        plus_total_offset = cmds.createNode('plusMinusAverage', n = inc_name('plusMinusAverage_total_offset_%s' % self.name))
        self.plus_total_offset = plus_total_offset
        
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
        
        self.stretch_offsets = stretch_offsets
        
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

        dampen = MayaNumberVariable(self.damp_name)
        dampen.set_node(self.attribute_node)
        dampen.set_variable_type(dampen.TYPE_DOUBLE)
        dampen.set_min_value(0)
        dampen.set_max_value(1)
        dampen.create()
        
        remap = cmds.createNode( "remapValue" , n = "%s_remapValue_%s" % (self.damp_name, self.name) )
        cmds.setAttr("%s.value[2].value_Position" % remap, 0.4);
        cmds.setAttr("%s.value[2].value_FloatValue" % remap, 0.666);
        cmds.setAttr("%s.value[2].value_Interp" % remap, 3)
    
        cmds.setAttr("%s.value[3].value_Position" % remap, 0.7);
        cmds.setAttr("%s.value[3].value_FloatValue" % remap, 0.9166);
        cmds.setAttr("%s.value[3].value_Interp" % remap, 1)
    
        multi = cmds.createNode ( "multiplyDivide", n = "%s_offset_%s" % (self.damp_name, self.name))
        add_double = cmds.createNode( "addDoubleLinear", n = "%s_addDouble_%s" % (self.damp_name, self.name))

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
        
    def _add_joint(self, joint):
        
        inc = len(self.stretch_offsets) + 1
        
        var_name = 'offset%s' % (inc)
            
        multiply = connect_multiply('%s.outputX' % self.divide_distance, '%s.scale%s' % (joint, self.scale_axis), 1)
            
            
        offset_variable = MayaNumberVariable(var_name )
        offset_variable.set_variable_type(offset_variable.TYPE_DOUBLE)
        offset_variable.set_node(multiply)
            
            
        offset_variable.create()
        offset_variable.set_value(1)
        offset_variable.set_min_value(0.1)
        offset_variable.connect_out('%s.input2X' % multiply)
        offset_variable.connect_out('%s.input1D[%s]' % (self.plus_total_offset, inc))
        
        
        stretch_offset = MayaNumberVariable('stretch_%s' % (inc))
        stretch_offset.set_node(self.attribute_node)
        stretch_offset.set_variable_type(stretch_offset.TYPE_DOUBLE)
        
        if not self.per_joint_stretch:
            stretch_offset.set_keyable(False)
        
        stretch_offset.create()
        
        stretch_offset.set_value(1)
        stretch_offset.set_min_value(0.1)
        
        stretch_offset.connect_out('%s.offset%s' % (multiply, inc) )   
        
        child_joint = cmds.listRelatives(joint, type = 'joint')
        
        if child_joint:
            distance =  get_distance(joint, child_joint[0])
            
            length = cmds.getAttr('%s.input1X' % self.orig_distance)
            length+=distance
            
            cmds.setAttr('%s.input1X' % self.orig_distance, length)
    
        
    def set_joints(self, joints):
        self.joints = joints
        
    def set_node_for_attributes(self, node_name):
        self.attribute_node = node_name
    
    def set_scale_axis(self, axis_letter):
        self.scale_axis = axis_letter.capitalize()
    
    def set_distance_offset(self, attribute):
        self.distance_offset_attribute = attribute
    
    def set_vector_instead_of_matrix(self, bool_value):
        self.vector = bool_value
    
    def set_add_dampen(self, bool_value, damp_name = None):
        self.add_dampen = bool_value
        
        if damp_name:
            self.damp_name = damp_name
    
    def set_simple(self, bool_value):
        self.simple = bool_value
    
    def set_description(self, string_value):
        self.name = '%s_%s' % (self.name, string_value)
    
    def set_per_joint_stretch(self, bool_value):
        self.per_joint_stretch = bool_value
    
    def set_extra_joint(self, joint):
        self.extra_joint = joint
    
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
                
                if self.extra_joint:
                    self._add_joint(self.extra_joint)
                
                if self.add_dampen:
                    self._create_dampen(stretch_distance, ['%s.firstTerm' % stretch_condition,
                                                           '%s.colorIfTrueR' % stretch_condition,
                                                           '%s.color2R' % stretch_on_off,
                                                           '%s.input2X' % divide_distance])
                
            if self.distance_offset_attribute:
                self._create_other_distance_offset(distance_offset)
                
        
                
        return top_locator, btm_locator
    
    
            
        
    
#--- Misc Rig



        
  

class RiggedLine(object):
    """
    rigs
    """
    def __init__(self, top_transform, btm_transform, name):
        self.name = name
        self.top = top_transform
        self.btm = btm_transform
        self.local = False
        self.extra_joint = None
    
    def _build_top_group(self):
        
        self.top_group = cmds.group(em = True, n = 'guideLineGroup_%s' % self.name)
        cmds.setAttr('%s.inheritsTransform' % self.top_group, 0)
    
    def _create_curve(self):
        self.curve = cmds.curve(d = 1, p = [(0, 0, 0),(0,0,0)], k = [0, 1], n = inc_name('guideLine_%s' % self.name))
        cmds.delete(self.curve, ch = True)
        
        
        shapes = get_shapes(self.curve)
        cmds.rename(shapes[0], '%sShape' % self.curve)
        
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
    """
    deform!!!
    """
    
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
    """
    deform!!!
    """
    def __init__(self, geometry, name):
        super(ClusterSurface, self).__init__(geometry, name)
        
        self.join_ends = False
        self.join_both_ends = False
        
        self.maya_type = None
        
        if has_shape_of_type(self.geometry, 'nurbsCurve'):
            self.maya_type = 'nurbsCurve'
        if has_shape_of_type(self.geometry, 'nurbsSurface'):
            self.maya_type = 'nurbsSurface'
            
        self.cluster_u = True
    
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
        
            if self.cluster_u:
                cv_count_u = len(cmds.ls('%s.cv[*][0]' % self.geometry, flatten = True))
                index1 = '[0:*][0:1]'
                index2 = '[0:*][%s:%s]' % (self.cv_count-2, self.cv_count-1)
                index3 = '[%s][0]' % (cv_count_u - 1)
                index4 = '[0][%s]' % (self.cv_count-1)
                index5 = '[%s][%s]' % (cv_count_u, self.cv_count-1) 
            if not self.cluster_u:
                cv_count_v = len(cmds.ls('%s.cv[0][*]' % self.geometry, flatten = True))
                index1 = '[0:1][0:*]'
                index2 = '[%s:%s][0:*]' % (self.cv_count-2, self.cv_count-1)
                index3 = '[0][%s]' % (cv_count_v - 1)
                index4 = '[%s][0]' % (self.cv_count-1)
                index5 = '[%s][%s]' % (self.cv_count-1,cv_count_v)                
            
            
            start_cvs = '%s.cv%s' % (self.geometry, index1)
            end_cvs = '%s.cv%s' % (self.geometry,index2)
            #end_cvs = '%s.cv[0:1][%s:%s]' % (self.geometry,self.cv_count-2, self.cv_count-1)
            
            p1 = cmds.xform('%s.cv[0][0]' % self.geometry, q = True, ws = True, t = True)
            p2 = cmds.xform('%s.cv%s' % (self.geometry, index3), q = True, ws = True, t = True)
            
            start_position = vtool.util.get_midpoint(p1, p2)
            
            p1 = cmds.xform('%s.cv%s' % (self.geometry, index4), q = True, ws = True, t = True)
            p2 = cmds.xform('%s.cv%s' % (self.geometry, index5), q = True, ws = True, t = True)
            
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
        
        if self.maya_type == 'nurbsCurve':
            start_cvs = '%s.cv[0:1]' % self.geometry
            end_cvs = '%s.cv[%s:%s]' % (self.geometry,self.cv_count-2, self.cv_count-1)
            
        if self.maya_type == 'nurbsSurface':
            
            if self.cluster_u:
                index1 = '[0:*][0]'
                index2 = '[0:*][%s]' % (self.cv_count-1)

            if not self.cluster_u:
                index1 = '[0][0:*]'
                index2 = '[%s][0:*]' % (self.cv_count-1)
            
            start_cvs = '%s.cv%s' % (self.geometry, index1)
            end_cvs = '%s.cv%s' % (self.geometry, index2)
            #end_cvs = '%s.cv[0:1][%s:%s]' % (self.geometry,self.cv_count-2, self.cv_count-1)
        
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
            
            if self.cluster_u:
                index = '[0][*]'
            if not self.cluster_u:
                index = '[*][0]'
                            
            self.cv_count = len(cmds.ls('%s.cv%s' % (self.geometry, index), flatten = True))
        
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
                
                if self.cluster_u:
                    index = '[*][%s]' % inc
                if not self.cluster_u:
                    index = '[%s][*]' % inc
                
                cv = '%s.cv%s' % (self.geometry, index)
            
            cluster, handle = self._create_cluster( cv )
            
            self.clusters.append(cluster)
            self.handles.append(handle)
    
        if self.join_ends and not self.join_both_ends:
            self.clusters.append(last_cluster)
            self.handles.append(last_handle)
        
        return self.clusters
    
    def set_join_ends(self, bool_value):
        
        self.join_ends = bool_value
        
    def set_join_both_ends(self, bool_value):
        self.join_both_ends = bool_value
        
    def set_cluster_u(self, bool_value):
        self.cluster_u = bool_value
    

class ClusterCurve(ClusterSurface):
    """
    deform!!!
    """
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
    
    """
    geo!!!
    """
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
        
        edge_to_curve_1 = cmds.createNode('polyEdgeToCurve', n = inc_name('rivetCurve1_%s' % self.name))
        cmds.setAttr('%s.inputComponents' % edge_to_curve_1, 2,'vtx[%s]' % vert_ids[0], 'vtx[%s]' % vert_ids[1], type='componentList')
        
        vert_iterator = api.IterateEdges(shape)
        vert_ids = vert_iterator.get_connected_vertices(edge_index_2)
        
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
    """
    space
    """
    def __init__(self, source_joints, target_joints):
        self.source_joints = source_joints
        self.target_joints = target_joints
    
    def _hook_scale_constraint(self, node):
        
        constraint_editor = ConstraintEditor()
        scale_constraint = constraint_editor.get_constraint(node, constraint_editor.constraint_scale)
        
        if not scale_constraint:
            return
        
        scale_constraint_to_world(scale_constraint)
        
    def _unhook_scale_constraint(self, scale_constraint):
        
        scale_constraint_to_local(scale_constraint)
        
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
    
    def __init__(self, node = None):
        super(StoreControlData, self).__init__(node)
        
        self.controls = []
        
        self.side_replace = ['_L', '_R', 'end']
    
    def _get_single_control_data(self, control):
        
        if not control:
            return
    
        attributes = cmds.listAttr(control, k = True)
            
        if not attributes:
            return
        
        attribute_data = {}
        
        for attribute in attributes:
            
            attribute_name = '%s.%s' % (control, attribute)
            
            if not cmds.objExists(attribute_name):
                continue
            
            if cmds.getAttr(attribute_name, type = True) == 'message':
                continue

            if cmds.getAttr(attribute_name, type = True) == 'string':
                continue
            
            value = cmds.getAttr(attribute_name)
            attribute_data[attribute] = value 
        
        return attribute_data

    
    def _get_control_data(self):
        
        controls = []
        
        if self.controls:
            controls = self.controls
        
        if not self.controls:
            controls = get_controls()
        
        control_data = {}
        
        for control in controls:
            
            if cmds.objExists('%s.POSE' % control):
                continue
            
            attribute_data = self._get_single_control_data(control)
            
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
    
    def _set_control_data_in_dict(self, control, attribute_data):
        
        data = self.eval_data(return_only=True)
        
        if data:
            data[control] = attribute_data
        
            self.set_data(data)
    
    
    def _set_control_data(self, control, data):
        for attribute in data:
            
            attribute_name = control + '.' + attribute
            
            """ removed for speed
            if not cmds.objExists(attribute_name):
                continue
            
            if cmds.getAttr(attribute_name, lock = True):
                continue
            
            connection = get_attribute_input(attribute_name)
            
            if connection:
                if cmds.nodeType(connection).find('animCurve') == -1:
                    continue
            """
            try:
                cmds.setAttr(attribute_name, data[attribute] )  
            except:
                pass
                #cmds.warning('Could not set %s.' % attribute_name)     
        
    def _find_other_side(self, control):
        
        pattern_string, replace_string, position_string = self.side_replace
            
        start, end = vtool.util.find_special(pattern_string, control, position_string)
        
        if start == None:
            return
        
        other_control = vtool.util.replace_string(control, replace_string, start, end)
            
        return other_control
        
    def remove_data(self, control):
        
        data = self.get_data()
        
        if data:
            
            data = eval(data)
        

        if data.has_key(control):
            data.pop(control)
        
        self.set_data(data)
        
    def remove_pose_control_data(self):
        
        data = self.get_data()
        
        if data:
            data = eval(data)

        found_keys = []

        for key in data:
            if cmds.objExists('%s.POSE' % key):
                found_keys.append(key)
                
        for key in found_keys:
            data.pop(key)
            
        self.set_data(data)
                    
    def set_data(self, data= None):
        
        self.data.set_locked(False)
        
        if data == None:
            data = self._get_control_data()
        
        super(StoreControlData, self).set_data(data)   
        self.data.set_locked(True)
    
    def set_control_data_attribute(self, control, data = None):
        
        if not data:
            data = self._get_single_control_data(control)
        
        if data:
            
            self._set_control_data_in_dict(control, data)
        if not data:
            vtool.util.warning('Error setting data for %s' % control )
        
    
        
    def set_controls(self, controls):
        
        self.controls = controls
    
    def set_side_replace(self, replace_string, pattern_string, position_string):
        #position can be 'start', 'end', 'first', or 'inside'
        
        self.side_replace = [replace_string, pattern_string, position_string]
        
    def eval_data(self, return_only = False):
        
        data = super(StoreControlData, self).eval_data()
        
        if return_only:
            return data
        
        if not data:
            return
        
        
        for control in data:
            
            if cmds.objExists('%s.POSE' % control):
                continue
       
            attribute_data = data[control]
            self._set_control_data(control, attribute_data)
            
        return data
            
    def eval_mirror_data(self):  
        data_list = self.eval_data()
            
        for control in data_list:
            
            other_control = self._find_other_side(control)
            
            if not other_control or cmds.objExists(other_control):
                continue
            
            if cmds.objExists('%s.ikFk' % control):

                value = cmds.getAttr('%s.ikFk' % control)
                other_value = cmds.getAttr('%s.ikFk' % other_control)
                cmds.setAttr('%s.ikFk' % control, other_value)
                cmds.setAttr('%s.ikFk' % other_control, value)
            
            if not self._has_transform_value(control):
                continue 
            
            #if not control.endswith('_L'):
            #    continue               
            
            temp_group = cmds.duplicate(control, n = 'temp_%s' % control, po = True)[0]
            
            MatchSpace(control, temp_group).translation_rotation()
            parent_group = cmds.group(em = True)
            cmds.parent(temp_group, parent_group)
            
            cmds.setAttr('%s.scaleX' % parent_group, -1)
            
            orig_value_x = cmds.getAttr('%s.rotateX' % control)
            orig_value_y = cmds.getAttr('%s.rotateY' % control)
            orig_value_z = cmds.getAttr('%s.rotateZ' % control)
            
            zero_xform_channels(control)
            
            const1 = cmds.pointConstraint(temp_group, other_control)[0]
            const2 = cmds.orientConstraint(temp_group, other_control)[0]
            
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
                
                if cmds.objExists('%s.POSE' % control):
                    continue
                
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
            transform = self.scope[inc]
            
            if cmds.nodeType(transform) == 'joint':
                cmds.move(position[0], position[1],position[2], '%s.scalePivot' % transform, '%s.rotatePivot' % transform, a = True)
                
            if not cmds.nodeType(transform) == 'joint' and cmds.nodeType(transform) == 'transform':
                cmds.move(position[0], position[1],position[2], transform, a = True)
                        
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
    """
    attributes!!!
    """
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
            # needs to unlock the attribute first
            
            
            
            if cmds.isConnected(self.connections[inc], self.connections[inc+1], ignoreUnitConversion = True):
                
                lock_state = cmds.getAttr(self.connections[inc+1], l = True)
            
                if lock_state == True:
                    cmds.setAttr(self.connections[inc+1], l = False)
                
                cmds.disconnectAttr(self.connections[inc], self.connections[inc+1])
            
                if lock_state == True:
                    cmds.setAttr(self.connections[inc+1], l = True)    
                
            
    
    def connect(self):
        for inc in range(0, len(self.connections), 2):
            if not cmds.isConnected(self.connections[inc], self.connections[inc+1], ignoreUnitConversion = True):
                
                lock_state = cmds.getAttr(self.connections[inc+1], l = True)
            
                if lock_state == True:
                    cmds.setAttr(self.connections[inc+1], l = False)
                
                cmds.connectAttr(self.connections[inc], self.connections[inc+1])
                
                if lock_state == True:
                    cmds.setAttr(self.connections[inc+1], l = True)
                
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
        

        
#--- deformation

class SplitMeshTarget(object):
    """
    deform!!!
    """
    def __init__(self, target_mesh):
        self.target_mesh = target_mesh
        self.weighted_mesh = None
        self.base_mesh = None
        self.split_parts = []
    
    def set_weight_joint(self, joint, suffix = None, prefix = None, split_name = True):
        self.split_parts.append([joint, None, suffix, prefix, None, split_name])
        
    def set_weight_insert_index(self, joint, insert_index, insert_name, split_name = True):
        
        self.split_parts.append([joint, None,None,None, [insert_index, insert_name], split_name])
    
    def set_weight_joint_replace_end(self, joint, replace, split_name = True):
        self.split_parts.append([joint, replace, None, None, None, split_name])
    
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
            replace = part[1]
            suffix = part[2]
            prefix = part[3]
            split_index = part[4]
            
            if not split_index:
                split_index = [0,'']
            
            split_name_option = part[5]
            
            new_target = cmds.duplicate(self.base_mesh)[0]
            
            target_name = self.target_mesh
            
            if self.target_mesh.endswith('N'):
                target_name = self.target_mesh[:-1]
                
            new_name = target_name
                
            if replace:
                
                new_name = re.sub(replace[0], replace[1], new_name)
                
            if suffix:
                new_name = '%s%s' % (new_name, suffix)
            if prefix:
                new_name = '%s%s' % (prefix, new_name)
            
            if self.target_mesh.endswith('N'):
                new_name += 'N'
            
            if split_name_option:
                
                split_name = self.target_mesh.split('_')
                
                if len(split_name) > 1:
                    new_names = []
                    
                    inc = 0
                    
                    for name in split_name:
                        
                        sub_name = name
                        if name.endswith('N'):
                            sub_name = name[:-1]
                        
                        sub_new_name = sub_name
                        
                        if suffix:
                            sub_new_name = '%s%s' % (sub_new_name, suffix)
                        if prefix:
                            sub_new_name = '%s%s' % (prefix, sub_new_name)
                        
                        if name.endswith('N'):
                            sub_new_name += 'N'
                            
                        if split_index and split_index[0] == inc:
                            new_names.append(split_index[1])
                            
                        new_names.append(sub_new_name)
                        
                        inc += 1
                        
                    new_name = string.join(new_names, '_')
            
            
            
            if not split_name_option:
                
                new_name = new_name[:split_index[0]] + split_index[1] + new_name[split_index[0]:]
            
            new_target = cmds.rename(new_target, new_name)    
            
            blendshape_node = cmds.blendShape(self.target_mesh, new_target, w = [0,1])[0]
            
            
            
            target_index = get_index_at_skin_influence(joint, skin_cluster)
            
            if target_index == None:
                vtool.util.warning('Joint %s is not in skinCluster %s' % (joint, skin_cluster))
                cmds.delete(new_target, ch = True)
                continue
                       
            if not skin_weights.has_key(target_index):
                vtool.util.warning('Joint %s not in skinCluster %s.' % (joint, skin_cluster))
                cmds.delete(new_target, ch = True)
                continue
                
            weights = skin_weights[target_index]
            
            import blendshape
            blend = blendshape.BlendShape(blendshape_node)
            blend.set_weights(weights, self.target_mesh)
            
            cmds.delete(new_target, ch = True)
            
            
            
            current_parent = cmds.listRelatives(new_target, p = True)
            
            if current_parent:
                current_parent = current_parent[0]
            
            if parent and current_parent:
                if parent != current_parent:
                    cmds.parent(new_target, parent)
                
            targets.append(new_target)
        
        return targets
            
            
class TransferWeight(object):
    """
    deform!!!
    """
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
            
            if not cmds.objExists(joint):
                continue
            
            if not joint in influences:
                cmds.skinCluster(self.skin_cluster, e = True, ai = joint, wt = 0.0, nw = 1)
        
    @undo_off
    def transfer_joint_to_joint(self, source_joints, destination_joints, source_mesh = None, percent =1):
        
        #vtool.util.show('Start: %s transfer joint to joint.' % self.mesh)
        
        if not self.skin_cluster:
            vtool.util.show('No skinCluster found on %s. Could not transfer.' % self.mesh)
            return
        
        if not destination_joints:
            vtool.util.warning('Destination joints do not exist.')
            return
            
        if not source_joints:
            vtool.util.warning('Source joints do not exist.')
            return
        
        if not source_mesh:
            source_mesh = self.mesh
        
        source_skin_cluster = self._get_skin_cluster(source_mesh)
        source_value_map = get_skin_weights(source_skin_cluster)
        destination_value_map = get_skin_weights(self.skin_cluster)
        
        joint_map = {}
        destination_joint_map = {}
        
        for joint in source_joints:
            if not cmds.objExists(joint):
                vtool.util.warning('%s does not exist.' % joint)
                continue
                        
            index = get_index_at_skin_influence(joint,source_skin_cluster)
            joint_map[index] = joint
            
        for joint in destination_joints:
            if not cmds.objExists(joint):
                vtool.util.warning('%s does not exist.' % joint)
                continue
            
            index = get_index_at_skin_influence(joint,self.skin_cluster)
            destination_joint_map[index] = joint
        
        verts = cmds.ls('%s.vtx[*]' % source_mesh, flatten = True)
                            
        weighted_verts = []
        
        for influence_index in joint_map:
            
            if influence_index == None:
                continue
            
            for vert_index in range(0, len(verts)):
                
                int_vert_index = int(vtool.util.get_last_number(verts[vert_index]))
                
                if not source_value_map.has_key(influence_index):
                    continue
                
                value = source_value_map[influence_index][int_vert_index]
                
                if value > 0.001:
                    weighted_verts.append(int_vert_index)
        
        self._add_joints_to_skin(source_joints)
        
        lock_joints(self.skin_cluster, destination_joints)
        
        vert_count = len(weighted_verts)
        
        if not vert_count:
            vtool.util.warning('Found no weights for specified influences on %s.' % source_skin_cluster)
            return
        
        bar = ProgressBar('transfer weight', vert_count)
        
        inc = 1
        
        for vert_index in weighted_verts:
            vert_name = '%s.vtx[%s]' % (self.mesh, vert_index)
        
            destination_value = 0
        
            for influence_index in destination_joint_map:
                
                if influence_index == None:
                    continue
                destination_value += destination_value_map[influence_index][vert_index]
            
            segments = []
            
            for influence_index in joint_map:
                
                if influence_index == None:
                    continue   
                
                joint = joint_map[influence_index]
                
                if not source_value_map.has_key(influence_index):
                    continue 
                
                value = source_value_map[influence_index][vert_index]
                value *= destination_value
                value *= percent
                
                segments.append((joint, value))
              
            if segments:
                cmds.skinPercent(self.skin_cluster, vert_name, r = False, transformValue = segments)

            bar.inc()
            
            bar.status('transfer weight: %s of %s' % (inc, vert_count))
            
            if bar.break_signaled():
                break
            
            inc += 1
            
        cmds.skinPercent(self.skin_cluster, self.vertices, normalize = True) 
        
        vtool.util.show('Done: %s transfer joint to joint.' % self.mesh)
        
        bar.end()
         
    @undo_off  
    def transfer_joints_to_new_joints(self, joints, new_joints, falloff = 1, power = 4, weight_percent_change = 1):
        
        #vtool.util.show('Start: %s transfer joints to new joints.' % self.mesh)
        
        if not self.skin_cluster:
            vtool.util.warning('No skinCluster found on %s. Could not transfer.' % self.mesh)
            return
        
        joints = vtool.util.convert_to_sequence(joints)
        new_joints = vtool.util.convert_to_sequence(new_joints)
        
        if not new_joints:
            vtool.util.warning('Destination joints do not exists.')
            return
            
        if not joints:
            vtool.util.warning('Source joints do not exist.')
            return
        
        if not self.skin_cluster or not self.mesh:
            return
        
        lock_joints(self.skin_cluster, joints)
        
        self._add_joints_to_skin(new_joints)
        
        value_map = get_skin_weights(self.skin_cluster)
        influence_values = {}
        
        source_joint_weights = []
        
        for joint in joints:
            
            if not cmds.objExists(joint):
                vtool.util.warning('%s does not exist.' % joint)
                continue
            
            index = get_index_at_skin_influence(joint,self.skin_cluster)
            
            if index == None:
                continue
            
            if not value_map.has_key(index):
                continue
            
            influence_values[index] = value_map[index]
            source_joint_weights.append(value_map[index])
            
        if not source_joint_weights:
            vtool.util.warning('Found no weights for specified influences on %s.' % self.skin_cluster)
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
            vtool.util.warning('Found no weights for specified influences on %s.' % self.skin_cluster)
            return
        
        bar = ProgressBar('transfer weight', len(weighted_verts))
        
        inc = 1
        
        new_joint_count = len(new_joints)
        joint_count = len(joints)
        
        for vert_index in weighted_verts:
            
            vert_name = '%s.vtx[%s]' % (self.mesh, vert_index)
            
            
            distances = get_distances(new_joints, vert_name)
            
            if not distances:
                vtool.util.show('Error: No distances found. Check your target joints.')
                bar.end()
                return
            
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
            
            if vert_index == 940:
                
                value = 0
                
                total_value = 0
                
                for segment in segments:
                    total_value += segment[1]
                    
            
            cmds.skinPercent(self.skin_cluster, vert_name, r = False, transformValue = segments)
            
            bar.inc()
            
            bar.status('transfer weight: %s of %s' % (inc, len(weighted_verts)))
            
            if bar.break_signaled():
                break
            
            inc += 1
          
        cmds.skinPercent(self.skin_cluster, self.vertices, normalize = True) 
        bar.end()
        vtool.util.show('Done: %s transfer joints to new joints.' % self.mesh)
                
class MayaWrap(object):
    """
    deform!!!
    """
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
        
        basename = get_basename(self.mesh, True)
        
        self.wrap = cmds.deformer(self.mesh, type = 'wrap', n = 'wrap_%s' % basename)[0]
        cmds.setAttr('%s.exclusiveBind' % self.wrap, 1)
        return self.wrap                 
    
    def _add_driver_meshes(self):
        inc = 0
        
        for mesh in self.driver_meshes:
            self._connect_driver_mesh(mesh, inc)
            inc+=1
        
    def _connect_driver_mesh(self, mesh, inc):
        
        base = cmds.duplicate(mesh, n = 'wrapBase_%s' % mesh)[0]
        
        rename_shapes(base)
        
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
            shapes = cmds.listRelatives(relative, s = True, f = True)
            
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

 
class EnvelopeHistory(object):
    """
    deform!!!
    """
    def __init__(self, transform):
        
        self.transform = transform
        
        self.envelope_values = {}
        self.envelope_connection = {}
        
        self.history = self._get_envelope_history()
        
        
        
    def _get_history(self):
        
        history = get_history(self.transform)
        
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
 
    def turn_off_referenced(self):
        
        for history in self.history:
            
            if not is_referenced(history):
                continue
            
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
   
class LockState(object):
    """
    attributes!!!
    """
    def __init__(self, attribute):
        
        self.lock_state = cmds.getAttr(attribute, l = True)
        self.attribute = attribute
        
    def unlock(self):
        cmds.setAttr( self.attribute, l = False)
        
    def lock(self):
        cmds.setAttr( self.attribute, l = True)
        
    def restore_initial(self):
        
        cmds.setAttr( self.attribute, l = self.lock_state)
   
#--- definitions core

def is_batch():
    """
    Return 
        (bool): True if Maya is in batch mode.
    """
    
    return cmds.about(batch = True)

def is_referenced(node):
    """
    Args:
        node (str): Name of a node in maya. Check to see if it is referenced.
        
    Return
        (bool)
    """
    if not cmds.objExists(node):
        return False
    
    is_node_referenced = cmds.referenceQuery(node, isNodeReferenced = True)
    
    return is_node_referenced

def is_a_shape(node):
    """
    Test whether the node is a shape.
    
    Args:
        node (str): The name of a node.
        
    Return
        bool
    """
    if cmds.objectType(node, isAType = 'shape'):
        return True
    
    return False

def inc_name(name):
    """
    Finds a unique name by adding a number to the end.
    
    Args:
        name (str): Name to start from. 
    
    Return
        (str): Modified name, number added if not unique..
    """
    
    unique = FindUniqueName(name)
    return unique.get()

def prefix_name(node, prefix, name, separator = '_'):
    """
    Convenience to quickly rename a Maya node.
    
    Args:
        node (str): Name of a node in maya to rename.
        prefix (str)
        name (str)
        separator (str)
        
    Return
        (str): prefix + separator + name
    
    """
    new_name = cmds.rename(node, '%s%s%s' % (prefix,separator, name))
    
    return new_name

def prefix_hierarchy(top_group, prefix):
    """
    Prefix all the names in a hierarchy.
    
    Args:
        top_group (str): Name of the top node of a hierarchy.
        prefix (str): Prefix to add in front of top_group and all children.
        
    Return
        (list): The renamed hierarchy including top_group.
    """
    
    relatives = cmds.listRelatives(top_group, ad = True)
     
    relatives.append(top_group)
    
    renamed = []
    
    for relative in relatives:

        new_name = cmds.rename(relative, '%s_%s' % (prefix, relative))
        renamed.append(new_name)
    
    renamed.reverse()
    
    return renamed
    
def pad_number(name):
    """
    Add a number to a name.
    """
    
    number = vtool.util.get_last_number(name)
    
    number_string = str(number)
    
    index = name.rfind(number_string)

    if number < 10:
        number_string = number_string.zfill(2)
        
    new_name =  name[0:index] + number_string + name[index+1:]
    renamed = cmds.rename(name, new_name)
    
    return renamed



def get_shapes(transform):
    """
    Get all the shapes under a transform.
    
    Args:
        transform (str): The name of a transform.
        
    Return
        list: The names of shapes under the transform
    """
    if is_a_shape(transform):
        parent = cmds.listRelatives(transform, p = True, f = True)
        return cmds.listRelatives(parent, s = True, f = True)
    
    return cmds.listRelatives(transform, s = True, f = True)
    
def get_node_types(nodes, return_shape_type = True):
    """
    Get the maya node types for the nodes supplied.
    
    Return
        (dict[node_type_name]): node dict of matching nodes
    """
    
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
     
def get_basename(name, remove_namespace = True):
    """
    Get the basename in a hierarchy name.
    If top|model|face is supplied, face will be returned.
    """
    
    split_name = name.split('|')
    
    basename = split_name[-1]
    
    if remove_namespace:
        split_basename = basename.split(':')
        return split_basename[-1]
    
    return split_name[-1]

def get_visible_hud_displays():
    """
    Get viewport hud displays.
    
    Return
        (list):  List of names of heads up displays.
    """    
    
    found = []
        
    displays = cmds.headsUpDisplay(q = True, lh = True)
        
    for display in displays:
        visible = cmds.headsUpDisplay(display, q = True, vis = True)
        
        if visible:
            found.append(display)
        
    return found

def set_hud_visibility(bool_value, displays = None):
    """
    Set the viewport hud display visibility.
    
    Args:
        bool_value (bool): True turns visiliblity on, False turns it off.
        displays (list): List of heads up displays by name.
    """
    
    if not displays:
        displays = cmds.headsUpDisplay(q = True, lh = True) 
    
    for display in displays:
        cmds.headsUpDisplay(display, e = True, vis = bool_value)

def set_hud_lines(lines, name):
    """
    Set the viewport hud text for the named hud.
    
    Args:
        lines (list): Each entry in the list is a new text line in the display.
        name (str): The name of the heads up display to work on.
    
    """
    
    inc = 0
    for line in lines:

        hud_name = '%s%s' % (name, inc)
    
        if cmds.headsUpDisplay(hud_name, ex = True):
            cmds.headsUpDisplay(hud_name, remove = True)
        
            
        cmds.headsUpDisplay( hud_name, section = 1, block = inc, blockSize = 'large', labelFontSize = "large", dataFontSize = 'large')
        cmds.headsUpDisplay( hud_name, edit = True, label = line)
        
        inc += 1

    
def show_channel_box():
    """
    Makes the channel box visible.
    """
    
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
    """
    Playblast the viewport to the given filename path.
    
    Args:
        filename (str): This should be the path to a quicktime .mov file.
    """
    
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
    """
    Get the current audio node. Important when getting sound in a playblast.
    
    Return
        (str): Name of the audio node.
    """
    
    play_slider = mel.eval('global string $gPlayBackSlider; string $goo = $gPlayBackSlider')
    
    return cmds.timeControl(play_slider, q = True, s = True)

def delete_unknown_nodes():
    """
    This will find all unknown nodes. Unlock and delete them.
    """
    
    unknown = cmds.ls(type = 'unknown')

    for node in unknown:
        if cmds.objExists(node):
            cmds.lockNode(node, lock = False)
            cmds.delete(node)

#--- shading

def apply_shading_engine(shader_name, mesh):
    """
    Adds the named shading engine to the mesh.
    
    Args:
        shader_name (str): Name of an existing shader in maya.
        mesh (str):  Name of a mesh to add the shader to.
    
    """
    
    
    
    cmds.sets(mesh, e = True, forceElement = shader_name)
    
def get_shading_engine_geo(shader_name):
    """
    Non implemented
    """
    pass

def get_shading_engines(shader_name):
    """
    Get the shading engines attached to a shader.  
    Maya allows one shader to be attached to more than one engine. 
    Most of the time it is probably just attached to one.
    
    Args:
        shader_name (str): The name of the shader.
        
    Return
        (list): A list of attached shading engines by name.
    """
    outputs = get_outputs('%s.outColor' % shader_name, node_only = True)
    
    found = []
    
    for output in outputs:
        if cmds.nodeType(output) == 'shadingEngine':
            found.append(output)
            
    return found

def apply_shader(shader_name, mesh):
    """
    Args:
        shader_name (str): The name of a shader.
        mesh (str): The name of the mesh to apply the shader to.
        
    """
    
    engines = get_shading_engines(shader_name)
    
    if engines:
        cmds.sets( mesh, e = True, forceElement = engines[0])
    
def apply_new_shader(mesh, type_of_shader = 'blinn', name = ''):
    """
    Create a new shader to be applied to the named mesh.
    
    Args:
        mesh (str): The name of the mesh to apply the shader to.
        type_of_shader (str): This corresponds to Maya shader types.  Eg. blinn, lambert, etc.
        name (str): The name to give the shader. If not name given a name will be made up using the type_of_shader.
        
    Return
        (str): The name of the new shader.
    """
    
    
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



def apply_transparent_lambert(mesh):
    """
    Convenience to hide geo via shader.
    
    Args:
        mesh (str): Name of the mesh to apply the shader to.
    """
    
    
    name = 'transparent_lambert'
    
    if not cmds.objExists(name):
        lambert = apply_new_shader(mesh, 'lambert', name)
        
        cmds.setAttr('%s.transparencyR' % lambert, 1)
        cmds.setAttr('%s.transparencyG' % lambert, 1)
        cmds.setAttr('%s.transparencyB' % lambert, 1)
        
    if cmds.objExists(name):
        apply_shader(name, mesh)
        
    
    

def create_display_layer(name, nodes):
    """
    Create a display layer containing the supplied nodes.
    
    Args:
        name (str): The name to give the display layer.
        nodes (str): The nodes that should be in the display layer.
        
    """
    layer = cmds.createDisplayLayer( name = name )
    cmds.editDisplayLayerMembers( layer, nodes, noRecurse = True)
    cmds.setAttr( '%s.displayType' % layer, 2 )

def delete_display_layers():
    """
    Deletes all display layers.
        
    
    """
    layers = cmds.ls('displayLayer')
    
    for layer in layers:
        cmds.delete(layer)

#--- ui core

def add_to_isolate_select(nodes):
    """
    Add the specified nodes into every viewport's isolate select. 
    This will only work on viewports that have isolate select turned on.
    Use when nodes are not being evaluated because isolate select causes them to be invisible.
    
    Args:
        nodes (list): The nodes to add to isolate select.
    """
    
    if is_batch():
        return
    
    nodes = vtool.util.convert_to_sequence(nodes)
    
    model_panels = get_model_panels()
    
    for panel in model_panels:
        if cmds.isolateSelect(panel, q = True, state = True):
            for node in nodes: 
                cmds.isolateSelect(panel, addDagObject = node)
                
            #cmds.isolateSelect(panel, update = True)
            
def get_model_panels():
    """
    Good to use when editing viewports. 
    """
    return cmds.getPanel(type = 'modelPanel')
    

#--- space

def is_transform(node):
    """
    Is the node a transform.
    
    Args:
        node (str): The name of the node to test.
    
    Return
        (bool)
    """
    
    if not cmds.objExists(node):
        return False
    
    if cmds.objectType(node, isAType = 'transform'):
        return True
    
    return False


def get_closest_transform(source_transform, targets):
    """
    Given the list of target transforms, find the closest to the source transform.
    
    Args:
        source_transform (str): The name of the transform to test distance to.
        targets (list): List of targets to test distance against.
        
    Return
        (str): The name of the target in targets that is closest to source_transform.
    """
    
    least_distant = 1000000.0
    closest_target = None
    
    for target in targets:
        
        distance = get_distance(source_transform, target)
        
        if distance < least_distant:
            least_distant = distance
            closest_target = target
            
    return closest_target 

def get_distance(source, target):
    """
    Get the distance between the source transform and the target transform.
    
    Args:
        source (str): The name of a transform.
        target (str): The name of a transform.
    
    Return 
        (float): The distance between source and target transform.
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
    
    return vtool.util.get_distance(vector1, vector2)

def get_midpoint( source, target):
    """
    Get the midpoint between the source transform and the target transform.
    
    Args:
        source (str): The name of a transform.
        target (str): The name of a transform.
    
    Return 
        (vector list): The midpoint as [0,0,0] vector between source and target transform.
    """
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
    """
    Given a list of source transforms, return a list of distances to the target transform
    
    Args:
        sources (list): The names of a transforms.
        target (str): The name of a transform.
    
    Return 
        (list): The distances betweeen each source and the target.
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
        
    Return 
        (vector list): The triangle plane vector eg. [0,0,0].  This is good for placing the pole vector.
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
        
    Return 
        (vector list): The triangle plane vector eg. [0,0,0].  This is good for placing the pole vector.
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

def  get_center(transform):
    """
    Get the center of a selection. Selection can be component or transform.
    
    Args:
        transform (str): Name of a node in maya.
    
    Return 
        (vector list):  The center vector, eg [0,0,0]
    """
    
    
    components = get_components_in_hierarchy(transform)
    
    if components:
        transform = components
        
    bounding_box = BoundingBox(transform)
    return bounding_box.get_center()

def get_btm_center(transform):
    """
    Get the bottom center of a selection. Selection can be component or transform.
    
    Args:
        transform (str): Name of a node in maya.
    
    Return 
        (vector list): The btrm center vector, eg [0,0,0]
    """
    
    components = get_components_in_hierarchy(transform)
    
    if components:
        transform = components
        
    
    
    bounding_box = BoundingBox(transform)
    return bounding_box.get_ymin_center()

def get_top_center(transform):
    """
    Get the top center of a selection. Selection can be component or transform.
    
    Args:
        transform (str): Name of a node in maya.
    
    Return 
        (vector list): The top center vector, eg [0,0,0]
    """
    
    components = get_components_in_hierarchy(transform)
    
    if components:
        transform = components
        
    
    
    bounding_box = BoundingBox(transform)
    return bounding_box.get_ymax_center()


def get_ordered_distance_and_transform(source_transform, transform_list):
    """
    Returns a list of distances based on how far each transform in transform list is from source_transform.
    Returns a distance dictionary with each distacne key returning the corresponding transform.
    Returns a list with the original distance order has fed in from transform_list.
    
    Args:
        source_transform (str)
        
        transform_list (list)
        
    Return
        (dict)
        
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


def create_follow_fade(source_guide, drivers, skip_lower = 0.0001):
    """
    Create a multiply divide for each transform in drivers with a weight value based on the distance from source_guide.
    
    Args:
        source_guide (str): Name of a transform in maya to calculate distance.
        drivers (list): List of drivers to apply fade to based on distance from source_guide.
        skip_lower (float): The distance below which multiplyDivide fading stops.
        
    Return
        (list) : The list of multiplyDivide nodes.
    
    """
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

def create_match_group(transform, prefix = 'match', use_duplicate = False):
    """
    Create a group that matches a transform.
    Naming = 'match_' + transform
    
    Args:
        transform (str): The transform to match.
        prefix (str): The prefix to add to the matching group.
        use_duplicate (bool):  If True, matching happens by duplication instead of changing transform values.
        
    Return
        (str):  The name of the new group.
    """
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
    
    return xform_group    

def create_xform_group(transform, prefix = 'xform', use_duplicate = False):
    """
    Create a group above a transform that matches transformation of the transform. 
    This is good for zeroing out the values of a transform.
    Naming = 'xform_' + transform
    
    Args:
        transform (str): The transform to match.
        prefix (str): The prefix to add to the matching group.
        use_duplicate (bool):  If True, matching happens by duplication instead of changing transform values.
        
    Return
        (str):  The name of the new group.
    """
    
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
    """
    Create a group above a target_transform that is constrained to the source_transform.
    
    Args:
        source_transform (str): The transform to follow.
        target_transform (str): The transform to make follow.
        prefix (str): The prefix to add to the follow group.
        follow_scale (bool): Wether to add a scale constraint or not.
    
    Return
        (str):  The name of the new group.
    """
    
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
    """
    Create a group above a target_transform that is local constrained to the source_transform.
    This helps when setting up controls that need to be parented but only affect what they constrain when the actual control is moved.  
    
    Args:
        source_transform (str): The transform to follow.
        target_transform (str): The transform to make follow.
        prefix (str): The prefix to add to the follow group.
        orient_only (bool): Wether the local constraint should just be an orient constraint.
    
    Return
        (str):  The name of the new group.
    """
    
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
    
    Return
        (str):  The name of the new group.
    """
    
    if attribute_name == 'follow':
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
        
    if constraint_type == 'orientConstraint':
        constraint = cmds.orientConstraint(locators,  target_transform, mo = True)[0]
    
    constraint_editor = ConstraintEditor()
    
    constraint_editor.create_switch(node, attribute_name, constraint)

    if value == None:
        value = (len(source_list)-1)
    
    cmds.setAttr('%s.%s' % (node, attribute_name), value)
       

def create_multi_follow(source_list, target_transform, node = None, constraint_type = 'parentConstraint', attribute_name = 'follow', value = None):
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
    
    Return
        (str):  The name of the new group.
    """
    if node == None:
        node = target_transform
    
    locators = []
    
    if len(source_list) < 2:
        vtool.util.warning('Can not create multi follow with less than 2 source transforms.')
        return
    
    follow_group = create_xform_group(target_transform, 'follow')
    
    if attribute_name == 'follow':
        var = MayaEnumVariable('FOLLOW')
        var.create(node)    

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
        constraint = cmds.orientConstraint(locators,  follow_group)[0]
    if constraint_type == 'pointConstraint':
        constraint = cmds.pointConstraint(locators,  follow_group, mo = True)[0]
    
    constraint_editor = ConstraintEditor()
    
    constraint_editor.create_switch(node, attribute_name, constraint)
    
    if value == None:
        value = (len(source_list)-1)
        
    cmds.setAttr('%s.%s' % (node, attribute_name), value)
    
    return follow_group


def get_hierarchy(node_name):
    """
    Return the name of the node including the hierarchy in the name using "|".
    This is the full path of the node.
    
    Args:
        node_name (str): A node name.
        
    Return
        (str): The node name with hierarchy included. The full path to the node.
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
        
    Return
        (bool)
    """
    
    long_transform = cmds.ls(transform, l = True)
    
    if not long_transform:
        return
    
    long_transform = long_transform[0]
    
    split_long = long_transform.split('|')
    
    get_basename(parent)
    
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
        
def get_outliner_sets():
    """
    Get the sets found in the outliner.
    
    Return
        (list): List of sets in the outliner.
    """
    
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
    """
    Get transforms that sit at the very top of the hierarchy.
    
    Return
        (list)
    """
    
    top_transforms = cmds.ls(assemblies = True)
    
    cameras = ['persp', 'top', 'front', 'side']
    
    for camera in cameras:
        if camera in top_transforms:
            top_transforms.remove(camera)
     
    return top_transforms 

def create_spline_ik_stretch(curve, joints, node_for_attribute = None, create_stretch_on_off = False, create_bulge = True, scale_axis = 'X'):
    """
    Makes the joints stretch on the curve. 
    Joints must be on a spline ik that is attached to the curve.
    
    Args:
        curve (str): The name of the curve that joints are attached to via spline ik.
        joints (list): List of joints attached to spline ik.
        node_for_attribute (str): The name of the node to create the attributes on.
        create_stretch_on_off (bool): Wether to create extra attributes to slide the stretch value on/off.
        create_bulge (bool): Wether to add bulging to the other axis that are not the scale axis.
        scale_axis (str): 'X', 'Y', or 'Z', the axis that the joints stretch on.
    """
    scale_axis = scale_axis.capitalize()
    
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
            
            cmds.connectAttr('%s.outputR' % blend, '%s.scale%s' % (joint, scale_axis))
            
            cmds.connectAttr('%s.stretchOnOff' % node_for_attribute, '%s.blender' % blend)
            
        if not create_stretch_on_off:
            cmds.connectAttr(attribute, '%s.scale%s' % (joint, scale_axis))
        
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
    
            if scale_axis == 'X':
                cmds.connectAttr(attribute, '%s.scaleY' % joint)
                cmds.connectAttr(attribute, '%s.scaleZ' % joint)
            if scale_axis == 'Y':
                cmds.connectAttr(attribute, '%s.scaleX' % joint)
                cmds.connectAttr(attribute, '%s.scaleZ' % joint)
            if scale_axis == 'Z':
                cmds.connectAttr(attribute, '%s.scaleX' % joint)
                cmds.connectAttr(attribute, '%s.scaleY' % joint)
        
        percent += segment

def create_simple_spline_ik_stretch(curve, joints):
    """
    Stretch joints on curve. Joints must be attached to a spline ik. This is a much simpler setup than create_spline_ik_stretch.
    
    Args:
        curve (str): The name of the curve that joints are attached to via spline ik.
        joints (list): List of joints attached to spline ik.
    """
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

        cmds.connectAttr(attribute, '%s.scaleY' % joint)
        
        percent += segment

def create_bulge_chain(joints, control, max_value = 15):
    """
    Adds scaling to a joint chain that mimics a cartoony water bulge moving along a tube.
    
    Args:
        joints (list): List of joints that the bulge effect should move along.
        control (str): Name of the control to put the bulge slider on.
        max_value (float): The maximum value of the slider.
    """
    
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
    """
    Constrain a target transform to a source transform in a way that allows for setups to remain local to the origin.
    This is good when a control needs to move with the rig, but move something at the origin only when the actually control moves.
    
    Args:
        source_transform (str): The name of a transform.
        target_transform (str): The name of a transform.
        parent (bool): The setup uses a local group to constrain the target_transform. If this is true it will parent the target_transform under the local group.
        scale_connect (bool): Wether to also add a scale constraint.
        constraint (str): The type of constraint to use. Currently supported: parentConstraint, pointConstraint, orientConstraint.
        
    Return
        (str, str) : The local group that constrains the target_transform, and the xform group above the local group.
    """
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
        if constraint == 'orientConstraint':
            cmds.orientConstraint(local_group, target_transform, mo = True)
            
        if scale_connect:
            connect_scale(source_transform, target_transform)
    
    return local_group, xform_group

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
        
    Return
        (list): List of the newly created joints.
        
    """
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
    """
    Under development.
    """
    
    distance_between = cmds.createNode('distanceBetween', 
                                        n = inc_name('distanceBetween_%s' % description) )
    
    cmds.addAttr(distance_between,ln = 'falloff', at = 'double', k = True)
        
    follow_locator = cmds.spaceLocator(n = 'follow_%s' % distance_between)[0]
    match = MatchSpace(source_transform, follow_locator)
    match.translation_rotation()
    cmds.parent(follow_locator, source_transform)
    cmds.move(source_local_vector[0], source_local_vector[1], source_local_vector[2], follow_locator, r = True, os = True)
    
    set_color(follow_locator, 6)
    
    target_locator = cmds.spaceLocator(n = 'target_%s' % distance_between)[0]
    match = MatchSpace(source_transform, target_locator)
    match.translation_rotation()
    
    set_color(target_locator, 13)

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
    """
    Create a stretch effect on a transform by changing the scale when the distance changes between xform1 and xform2.
    
    Args:
        xform1 (str): The name of a transform.
        xform2 (str): The name of a transform.
        axis (str): "X", "Y", "Z" The axis to attach the stretch effect to.
        offset (float): Add an offset to the value.
        
    Return
        ([locator1, locator2]): The names of the two locators used to calculate distance.
    """
    locator1 = cmds.spaceLocator(n = inc_name('locatorDistance_%s' % xform1))[0]
    
    MatchSpace(xform1, locator1).translation()
    
    locator2 = cmds.spaceLocator(n = inc_name('locatorDistance_%s' % xform2))[0]
    MatchSpace(xform2, locator2).translation()
    
    distance = cmds.createNode('distanceBetween', n = inc_name('distanceBetween_%s' % xform1))
    
    multiply = cmds.createNode('multiplyDivide', n = inc_name('multiplyDivide_%s' % xform1))
    
    cmds.connectAttr('%s.worldMatrix' % locator1, '%s.inMatrix1' % distance)
    cmds.connectAttr('%s.worldMatrix' % locator2, '%s.inMatrix2' % distance)
    
    distance_value = cmds.getAttr('%s.distance' % distance)
    
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
    """
    Add orient attributes, used to automatically orient.
    
    Args:
        transform (str): The name of the transform.
    """
    if type(transform) != list:
        transform = [transform]
    
    for thing in transform:
        
        orient = OrientJointAttributes(thing)
        orient.set_default_values()
    
def orient_attributes(scope = None):
    """
    Orient all transforms with attributes added by add_orient_attributes.
    If scope is provided, only orient transforms in the scope that have attributes.
    
    Args:
        scope (list): List of transforms to orient.
    """
    if not scope:
        scope = get_top_dag_nodes()
    
    for transform in scope:
        relatives = cmds.listRelatives(transform, f = True)
        
        if not cmds.objExists('%s.ORIENT_INFO' % transform):
            if relatives:
                orient_attributes(relatives)
                
            continue
        
        if cmds.nodeType(transform) == 'joint' or cmds.nodeType(transform) == 'transform':
            orient = OrientJoint(transform)
            orient.run()
            
            if relatives:
                orient_attributes(relatives)

def find_transform_right_side(transform):
    """
    Try to find the right side of a transform.
    *_L will be converted to *_R 
    if not 
    l_* will be converted to R_*
    if not 
    *lf_* will be converted to *rt_*
    
    Args:
        transform (str): The name of a transform.
        
    Return 
        (str): The name of the right side transform if it exists.
    """
    
    other = ''
    
    if transform.endswith('_L'):
        other = transform.replace('_L', '_R')
        
        if cmds.objExists(other):
            return other
    
    other = ''
        
    if transform.startswith('L_') and not transform.endswith('_R'):
        
        other = transform.replace('L_', 'R_')
        
        if cmds.objExists(other):
            return other 
        
    other = ''
        
    if transform.find('lf_') > -1 and not transform.endswith('_R') and not transform.startswith('L_'):
        other = transform.replace('lf_', 'rt_')
        
        if cmds.objExists(other):
            return other
        
    return ''

def mirror_xform(prefix = None, suffix = None, string_search = None):
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
    transforms = []
    
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
    
    for transform in scope:
        
        other = ''
        other = find_transform_right_side(transform)
        
        if is_translate_rotate_connected(other):
            continue
       
        if cmds.objExists(other):
            
            xform = cmds.xform(transform, q = True, ws = True, t = True)
            
            if cmds.nodeType(other) == 'joint':
                
                radius = cmds.getAttr('%s.radius' % transform)
                
                if not is_referenced(other):
                    var = MayaNumberVariable('radius')
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
                    local_position = cmds.getAttr('%s.localPosition' % transform)[0]
                    
                    cmds.setAttr('%s.localPositionX' % transform, (local_position[0] * -1))
                    cmds.setAttr('%s.localPositionY' % transform, local_position[1])
                    cmds.setAttr('%s.localPositionZ' % transform, local_position[2])
    
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



def get_y_intersection(curve, vector):
    """
    Given a vector in space, find out the closest intersection on the y axis to the curve. This is usefull for eye blink setups.
    
    Args:
        curve (str): The name of a curve that could represent the btm eyelid.
        vector (vector list): A list that looks like [0,0,0] that could represent a position on the top eyelid.
        
    Return
        (float): The parameter position on the curve.
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
    
def get_side(transform, center_tolerance):
    """
    Get the side of a transform based on its position in world space.
    Center tolerance is distance from the center to include as a center transform.
    
    Args:
        transform (str): The name of a transform.
        center_tolerance (float): How close to the center the transform must be before it is considered in the center.
        
    Return
        (str): The side that the transform is on, could be 'L','R' or 'C'.
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

def create_no_twist_aim(source_transform, target_transform, parent):
    """
    Aim target transform at the source transform, trying to rotate only on one axis.
    Constrains the target_transform.
    
    Args:
        source_transform (str): The name of a transform.
        target_transform (str): The name of a transform.
        parent (str): The parent for the setup.
    """
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

def create_pole_chain(top_transform, btm_transform, name):
    """
    Create a two joint chain with an ik handle.
    
    Args:
        top_transform (str): The name of a transform.
        btm_transform (str): The name of a transform.
        name (str): The name to give the new joints.
        
        Return
            (joint1, joint2, ik_pole)
    """
    
    cmds.select(cl =True)
    
    joint1 = cmds.joint(n = inc_name( name ) )
    joint2 = cmds.joint(n = inc_name( name ) )

    MatchSpace(top_transform, joint1).translation()
    MatchSpace(btm_transform, joint2).translation()
    
    cmds.joint(joint1, e = True, oj = 'xyz', secondaryAxisOrient = 'xup', zso = True)
    cmds.makeIdentity(joint2, jo = True, apply = True)

    ik_handle = IkHandle( name )
    
    ik_handle.set_start_joint( joint1 )
    ik_handle.set_end_joint( joint2 )
    ik_handle.set_solver(ik_handle.solver_sc)
    ik_pole = ik_handle.create()

    return joint1, joint2, ik_pole

def scale_constraint_to_local(scale_constraint):
    """
    Scale constraint can work wrong when given the parent matrix.
    Disconnect the parent matrix to remove this behavior.
    Reconnect using scale_constraint_to_world if applying multiple constraints.
    
    Args:
        scale_constraint (str): The name of the scale constraint to work on.
    """
    
    constraint_editor = ConstraintEditor()
        
    weight_count = constraint_editor.get_weight_count(scale_constraint)
    disconnect_attribute('%s.constraintParentInverseMatrix' % scale_constraint)
    
    for inc in range(0, weight_count):
        disconnect_attribute('%s.target[%s].targetParentMatrix' % (scale_constraint, inc))

def scale_constraint_to_world(scale_constraint):
    """
    Works with scale_constraint_to_local.
    
    Args:
        scale_constraint (str): The name of the scale constraint affected by scale_constraint_to_local.
    """
    
    constraint_editor = ConstraintEditor()
    
    weight_count = constraint_editor.get_weight_count(scale_constraint)
    
    node = get_attribute_outputs('%s.constraintScaleX' % scale_constraint, node_only = True)
    
    
    if node:
        cmds.connectAttr('%s.parentInverseMatrix' % node[0], '%s.constraintParentInverseMatrix' % scale_constraint)
    
    for inc in range(0, weight_count):
        
        target = get_attribute_input('%s.target[%s].targetScale' % (scale_constraint, inc), True)
        
        cmds.connectAttr('%s.parentInverseMatrix' % target, '%s.target[%s].targetParentMatrix' % (scale_constraint, inc) )
    
def duplicate_joint_section(joint, name = ''):
    """
    Joint chains ususally have a parent and a child along the chain. 
    This will duplicate one of those sections.  You need only supply the parent joint.
    
    Args:
        joint (str): The name of the joint to duplicate.
        name (str): The name to give the joint section.
        
    Return
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
    
def get_axis_vector(transform, axis_vector):
    """
    Get the vector matrix product.
    If you give it a vector [1,0,0], it will return the transform's x point.
    If you give it a vector [0,1,0], it will return the transform's y point.
    If you give it a vector [0,0,1], it will return the transform's z point.
    
    Args:
        transform (str): The name of a transform. Its matrix will be checked.
        axis_vector (list): A vector. X = [1,0,0], Y = [0,1,0], Z = [0,0,1] 
        
    Return
        list: The result of multiplying the vector by the matrix. Good to get an axis in relation to the matrix.
    """
    t_func = api.TransformFunction(transform)
    new_vector = t_func.get_vector_matrix_product(axis_vector)
    
    return new_vector
    
#--- animation

def quick_driven_key(source, target, source_values, target_values, infinite = False):
    """
    A convenience for create set driven key frames.
    
    Args:
        source (str): node.attribute to drive target.
        target (str): node.attribute to be driven by source.
        source_values (list): A list of values at the source.
        target_values (list): A list of values at the target.
        infinite (bool): The bool attribute. 
        
    """
    track_nodes = TrackNodes()
    track_nodes.load('animCurve')
    
    for inc in range(0, len(source_values)):
          
        cmds.setDrivenKeyframe(target,cd = source, driverValue = source_values[inc], value = target_values[inc], itt = 'spline', ott = 'spline')
    
    keys = track_nodes.get_delta()
    
    if not keys:
        return
    
    keyframe = keys[0]
    
    function = api.KeyframeFunction(keyframe)
    
    if infinite:
        
        function.set_pre_infinity(function.linear)
        function.set_post_infinity(function.linear)
         
    if infinite == 'post_only':
        
        function.set_post_infinity(function.linear)    
        
    if infinite == 'pre_only':
            
        function.set_pre_infinity(function.linear)

    return keyframe

def get_input_keyframes(node, node_only = True):
    """
    Get all keyframes that input into the node.
    
    Args:
        node (str): The name of a node to check for keyframes.
        node_only (bool): Wether to return just the keyframe name, or also the keyframe.output attribute.
        
    Return
        list: All of the keyframes connected to the node.
    """
    inputs = get_inputs(node, node_only)

    found = []
    
    if not inputs:
        return found
    
    for input_value in inputs:
        if cmds.nodeType(input_value).startswith('animCurve'):
            found.append(input_value)
            
    return found        

def get_output_keyframes(node):
    """
    Get all keyframes that output from the node.
    
    Args:
        node (str): The name of a node to check for keyframes.
        
    Return
        list: All of the keyframes that the node connects into.
    """    
    
    outputs = get_outputs(node)
    
    found = []
    
    if not outputs:
        return found
    
    for output in outputs:
        
        if cmds.nodeType(output).startswith('animCurve'):
            found.append(output)
            
    return found

def set_infiinity(keyframe, pre = False, post = False):
    """
    Given a keframe set the in and out infinity to linear.
    
    Args:
        keyframe (str): The name of a keyframe.
        pre (bool): Wether to set pre inifinity to linear.
        post (bool): Wether to set post infinity to linear.
        
    Return
        str: The name of the keyframe.
    """
    
    function = api.KeyframeFunction(keyframe)
    
    if post:
        function.set_post_infinity(function.linear)    
        
    if pre:
        function.set_pre_infinity(function.linear)
        
    return keyframe

#--- geometry



def is_a_mesh(node):
    """
    Test whether the node is a mesh or has a shape that is a mesh.
    
    Args:
        node (str): The name of a node.
        
    Return
        bool
    """
    if cmds.objExists('%s.vtx[0]' % node):
        return True
    
    return False

def has_shape_of_type(node, maya_type):
    """
    Test whether the node has a shape of the supplied type.
    
    Args:
        node (str): The name of a node.
        maya_type (str): Can be a mesh, nurbsCurve, or any maya shape type. 
        
    Return
        bool
    """
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
    """
    Return
        list: Any meshes in the selection list.
    """
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
    """
    Get the first mesh shape, or one based in the index.
    
    Args:
        mesh (str): The name of a mesh.
        shape_index (int): Usually zero, but can be given 1 or 2, etc up to the number of shapes - 1. 
        The shape at the index will be returned.
        
    Return
        str: The name of the shape. If no mesh shapes then returns None.
    """
    if mesh.find('.vtx'):
        mesh = mesh.split('.')[0]
    
    if cmds.nodeType(mesh) == 'mesh':
        
        mesh = cmds.listRelatives(mesh, p = True)[0]
        
    shapes = get_shapes(mesh)
    if not shapes:
        return
    
    if not cmds.nodeType(shapes[0]) == 'mesh':
        return
    
    shape_count = len(shapes)
    
    if shape_index < shape_count:
        return shapes[0]
    
    if shape_index > shape_count:
        cmds.warning('%s does not have a shape count up to %s' % shape_index)
    
def create_shape_from_shape(shape, name = 'new_shape'):
    """
    Duplication in maya can get slow in reference files. 
    This will create a shape and match it to the given shape without using Maya's duplicate command.
    
    Args:
        shape (str): The name of a shape to match to.
        name (str): The name of the new shape.
    
    Return
        The name of the transform above the new shape.
    """
    parent = cmds.listRelatives(shape, p = True, f = True)
    
    transform = cmds.group(em = True)
    transform = cmds.ls(transform, l = True)[0]
    
    api.create_mesh_from_mesh(shape, transform)
    mesh = transform
    
    add_to_isolate_select([mesh])
    
    mesh = cmds.rename(mesh, inc_name(name))
    
    if parent:
        MatchSpace(parent[0], mesh).translation_rotation()
        
    return mesh
    



def get_of_type_in_hierarchy(transform, node_type):
    """
    Get nodes of type in a hierarchy.
    
    Args:
        transform (str): The name of a transform.
        node_type (str): The node type to search for.
        
    Return
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
              
            

def get_shapes_in_hierarchy(transform):
    """
    Get all the shapes in the child hierarchy excluding intermediates.
    This is good when calculating bounding box of a group.
    
    Args:
        transform (str): The name of a transform.
        
    Return
        list: The list of shape nodes.
    """
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

def rename_shapes(transform):
    """
    Rename all the shapes under a transform. 
    Renames them to match the name of the transform.
    
    Args:
        transform (str): The name of a transform.
    """
    
    shapes = get_shapes(transform)
    
    if shapes:
        cmds.rename(shapes[0], '%sShape' % transform)
        
    if len(shapes) == 1:
        return
    
    if not shapes:
        return
    
    inc = 1
    for shape in shapes[1:]:
        
        cmds.rename(shape, '%sShape%s' % (transform, inc))
        inc += 1

def get_component_count(transform):
    """
    Get the number of components under a transform. 
    This does not include hierarchy.
    
    Args:
        transform (str): The name of a transform.
    
    Return
        int: The number of components under transform, eg. verts, cvs, etc.
    """
    
    components = get_components(transform)
    
    return len( cmds.ls(components[0], flatten = True) )

def get_components(transform):
    """
    Get the name of the components under a transform.  
    This does not include hierarchy.
    
    Args:
        transform (str): The name of a transform.
        
    Return
        list: The name of all components under transform, eg verts, cvs, etc.
    """
    
    shapes = get_shapes(transform)
    
    return get_components_from_shapes(shapes)

def get_components_in_hierarchy(transform):
    """
    Get the components in the hierarchy.
    This includes all transforms with shapes parented under the transform.
    
    Args:
        transform (str): The name of a transform.
        
    Return
        list: The name of all components under transform, eg verts, cvs, etc.
    """
    
    shapes = get_shapes_in_hierarchy(transform)
    
    return get_components_from_shapes(shapes)

def get_components_from_shapes(shapes = None):
    """
    Get the components from the a list of shapes.  Curntly supports cv and vtx components
    
    Args:
        shapes (list): List of shape names.
        
    Return
        list: The components of the supplied shapes.
    """
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
    """
    Given a list of edges, return the edge path.
    
    Args:
        edges (list): A list of edges (by name) along a path.  eg. ['node_name.e[0]'] 
    
    Return
        list: The names of edges in the edge path.
    """
    
    cmds.select(cl = True)
    cmds.polySelectSp(edges, loop = True )
    
    return cmds.ls(sl = True, l = True)

def edge_to_vertex(edges):
    """
    Return the vertices that are part of the edges.
    
    Args:
        edges (list): A list of edges (by name).  eg. ['mesh_name.e[0]'] 
    
    Return
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

def get_face_center(mesh, face_id):
    """
    Get the center position of a face.
    
    Args:
        mesh (str): The name of a mesh.
        face_id: The index of a face component.
        
    Return
        list: eg [0,0,0] The vector of the center of the face.
    """
    mesh = get_mesh_shape(mesh)

    face_iter = api.IteratePolygonFaces(mesh)
    
    center = face_iter.get_center(face_id)
    
    return center
    
def get_face_centers(mesh):
    """
    Return a list of face center positions.
    
    Args:
        mesh (str): The name of a mesh.
        
    Return
        list: A list of lists.  eg. [[0,0,0],[0,0,0]]  Each sub list is the face center vector.
    """
    mesh = get_mesh_shape(mesh)
    
    face_iter = api.IteratePolygonFaces(mesh)
    
    return face_iter.get_face_center_vectors()
    
    


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
        
    Return
        str: The name of the rivet.
    """
    
    parent = None
    if auto_parent:
        parent = cmds.listRelatives(transform, p = True)
    
    shape = get_mesh_shape(mesh)
    
    if rotate_pivot:
        position = cmds.xform(transform, q = True, rp = True, ws = True)
    if not rotate_pivot: 
        position = get_center(transform)
    
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
    """
    Attach the transform to the curve using a point on curve.
    
    Args:
        transform (str): The name of a transform.
        curve (str): The name of a curve
        maintain_offset (bool): Wether to attach to transform and maintain its offset from the curve.
        parameter (float): The parameter on the curve where the transform should attach.
        
    Return
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

def attach_to_surface(transform, surface, u = None, v = None):
    """
    Attach the transform to the surface using a rivet.
    If no u and v value are supplied, the command will try to find the closest position on the surface.
    
    Args:
        transform (str): The name of a transform.
        surface (str): The name of the surface to attach to.
        u (float): The u value to attach to.
        v (float): The v value to attach to. 
        
    Return
        str: The name of the rivet.
    """
    
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
    """
    Attach the source_transform to the closest transform in the list of target_transforms.
    
    Args:
        source_transform (str): The name of a transform to check distance to.
        target_transforms (list): List of transforms. The closest to source_transform will be attached to it.
    """
    closest_transform = get_closest_transform(source_transform, target_transforms)
    
    create_follow_group(closest_transform, source_transform)

def follicle_to_mesh(transform, mesh, u = None, v = None):
    """
    Use a follicle to attach the transform to the mesh.
    If no u and v value are supplied, the command will try to find the closest position on the mesh. 
    
    Args:
        transform (str): The name of a transform to follicle to the mesh.
        mesh (str): The name of a mesh to attach to.
        u (float): The u value to attach to.
        v (float): The v value to attach to. 
        
    Return 
        str: The name of the follicle created.
        
        
    """
    mesh = get_mesh_shape(mesh)
    
    position = cmds.xform(transform, q = True, ws = True, t = True)
    
    uv = u,v
    
    if u == None or v == None:
        uv = get_closest_uv_on_mesh(mesh, position)
        
    follicle = create_mesh_follicle(mesh, transform, uv)   
    
    cmds.parent(transform, follicle)
    
    return follicle

def create_joints_on_faces(mesh, faces = [], follow = True, name = None):
    """
    Create joints on the given faces.
    
    Args:
        mesh (str): The name of a mesh.
        faces (list): A list of face ids to create joints on.
        follow (bool): Wether the joints should follow.
        name (str): The name to applied to created nodes
        
    Return 
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
        
        joint = cmds.joint(p = center, n = inc_name(name))
        joints.append(joint)
        
        if follow:
            follicle = attach_to_mesh(joint, mesh, hide_shape = True, constrain = False, rotate_pivot = True)
            
            
            
            #follicle = follicle_to_mesh(joint, mesh)
            follicles.append(follicle)
            #cmds.makeIdentity(joint, jo = True, apply = True, t = True, r = True, s = True)
    
    if follicles:
        return joints, follicles
    if not follicles:
        return joints
    

def follicle_to_surface(transform, surface, u = None, v = None):
    """
    Follicle the transform to a nurbs surface.
    If no u and v value are supplied, the command will try to find the closest position on the surface. 
    
    Args:
        transform (str): The name of a transform to follicle to the surface.
        mesh (str): The name of a surface to attach to.
        u (float): The u value to attach to.
        v (float): The v value to attach to. 
        
    Return 
        str: The name of the follicle created.
        
    """
    position = cmds.xform(transform, q = True, ws = True, t = True)

    uv = u,v

    if u == None or v == None:
        uv = get_closest_parameter_on_surface(surface, position)   

    follicle = create_surface_follicle(surface, transform, uv)
    
    cmds.parent(transform, follicle)
    
    return follicle

def create_empty_follicle(description, uv = [0,0]):
    """
    Create a follicle
    
    Args:
        description (str): The description of the follicle.
        uv (list): eg. [0,0]
        
    Return
        str: The name of the created follicle.
    """

    follicleShape = cmds.createNode('follicle')
    cmds.hide(follicleShape)
    
    follicle = cmds.listRelatives(follicleShape, p = True)[0]
    
    cmds.setAttr('%s.inheritsTransform' % follicle, 0)
    
    if not description:
        follicle = cmds.rename(follicle, inc_name('follicle_1'))
    if description:
        follicle = cmds.rename(follicle, inc_name('follicle_%s' % description))
    
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
        
    Return
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
        
    Return
        str: The name of the created follicle.
    """    
    
    follicle = create_empty_follicle(description, uv)
    
    shape = cmds.listRelatives(follicle, shapes = True)[0]
        
    cmds.connectAttr('%s.local' % surface, '%s.inputSurface' % follicle)
    cmds.connectAttr('%s.worldMatrix' % surface, '%s.inputWorldMatrix' % follicle)
    
    cmds.connectAttr('%s.outTranslate' % shape, '%s.translate' % follicle)
    cmds.connectAttr('%s.outRotate' % shape, '%s.rotate' % follicle)
    
    return follicle

def transforms_to_nurb_surface(transforms, description, spans = -1, offset_axis = 'Y', offset_amount = 1):
    """
    Create a nurbs surface from a list of joints.  
    Good for creating a nurbs surface that follows a spine or a tail.
    
    Args:
        transforms (list): List of transforms
        description (str): The description of the surface. Eg. 'spine', 'tail'
        spans (int): The number of spans to give the final surface. If -1 the surface will have spans based on the number of transforms.
        offset_axis (str): The axis to offset the surface relative to the transform.  Can be 'X','Y', or 'Z'
        offset_amount (int): The amount the surface offsets from the transforms.
        
    Return
        str: The name of the nurbs surface.
    """
    
    
    transform_positions_1 = []
    transform_positions_2 = []
    
    for transform in transforms:
        
        transform_1 = cmds.group(em = True)
        transform_2 = cmds.group(em = True)
        
        MatchSpace(transform, transform_1).translation_rotation()
        MatchSpace(transform, transform_2).translation_rotation()
        
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

def transforms_to_curve(transforms, spans, description):
    """
    Create a curve from a list of transforms.  Good for create the curve for a spine joint chain or a tail joint chain.
    
    Args:
        transforms (list): A list of transforms to generate the curve from. Their positions will be used to place cvs.
        spans (int): The number of spans the final curve should have.
        description (str): The description to give the curve, eg. 'spine', 'tail'
        
    Return
        str: The name of the curve.
    """
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
    """
    Given a list of transforms, create a joint chain.
    
    Args:
        transforms (list): List of transforms. Their positions will be used to set joint positions.
        name (str): The description to give the joints.
        
    Return
        list: The names of the joints created.
    """
    cmds.select(cl = True)
    
    joints = []
    
    for transform in transforms:
    
        if not name:
            name = transform     
            
        joint = cmds.joint(n = inc_name('joint_%s' % name))
        
        MatchSpace(transform, joint).translation_rotation()
        
        joints.append(joint)
        
    return joints

def transform_to_polygon_plane(transform, size = 1):
    """
    Create a single polygon face from the position and orientation of a transform.
    
    Args:
        transform (str): The name of the transform where the plane should be created.
        size (float): The size of the plane.
        
    Return
        str: The name of the new plane.
    """
    plane = cmds.polyPlane( w = size, h = size, sx = 1, sy = 1, ax = [0, 1, 0], ch = 0)
    
    plane = cmds.rename(plane, inc_name('%s_plane' % transform))
    
    MatchSpace(transform, plane).translation_rotation()
    
    return plane
    
def curve_to_nurb_surface(curve):
    pass
    
def edges_to_curve(edges, description):
    """
    Given a list of edges create a curve.
    
    Args:
        edges (list): List of edge names, eg ['mesh_name.e[0]']
        description (str): The description to give the new curve. Name = 'curve_(description)'
        
    Return
        str: The name of the curve.
    """
    cmds.select(edges)

    curve =  cmds.polyToCurve(form = 2, degree = 3 )[0]
    
    curve = cmds.rename(curve, inc_name('curve_%s' % description))
    
    return curve
    
def get_intersection_on_mesh(mesh, ray_source_vector, ray_direction_vector ):
    """
    Given a ray vector with source and direction, find the closest intersection on a mesh.
    
    Args:
        mesh (str): The name of the mesh to intersect with.
        ray_source_vector (list): eg. [0,0,0], the source of the ray as a vector.
        ray_directrion_vector (list): eg [0,0,0], The end point of the ray that starts at ray_source_vector.
        
    Return
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
        
    Return
        uv: The uv of that is closest to three_value_list
    """
    
    mesh = api.MeshFunction(mesh)
    found = mesh.get_uv_at_point(three_value_list)
    
    return found
    

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
    
    
    Return
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
        
        space2 = get_axis_vector(dup, axis_vector)
        
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
        
    Return
        float: The closest parameter.
    """
    curve_shapes = get_shapes(curve)
    
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
    
    Return
        list: [0,0] The parameter coordinates of the closest point on the surface.
    """
    shapes = get_shapes(surface)
    
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

def get_closest_position_on_curve(curve, three_value_list):
    """
    Given a vector, find the closest position on a curve.
    
    Args:
        curve (str): The name of a curve.
        three_value_list (list): eg [0,0,0] a vector find the closest position from.
        
    Return
        list: eg [0,0,0] The closest position on the curve as vector.
    """
    
    curve_shapes = get_shapes(curve)
    
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
        
    Return
        float: The parameter value at the length.
    """
    
    curve_shapes = get_shapes(curve)
    
    if curve_shapes:
        curve = curve_shapes[0]
        
    curve = api.NurbsCurveFunction(curve)
    
    return curve.get_parameter_at_length(length_value)

def get_point_from_curve_parameter(curve, parameter):
    """
    Find a position on a curve by giving a parameter value.
    
    Args:
        curve (str): The name of a curve.
        parameter (float): The parameter value on a curve.
        
    Return 
        list: [0,0,0] the vector found at the parameter on the curve.
    """
    return cmds.pointOnCurve(curve, pr = parameter, ch = False)

@undo_chunk
def create_oriented_joints_on_curve(curve, count = 20, description = None, rig = False):
    """
    Create joints on curve that are oriented to aim at child.
    
    Args:
        curve (str): The name of a curve
        count (int): The number of joints.
        description (str): The description to give the joints.
        rig (bool): Wether to rig the joints to the curve.
        
    Return
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
    """
    Create joints on curve that do not aim at child.
    
    Args:
        curve (str): The name of a curve.
        joint_count (int): The number of joints to create.
        description (str): The description to give the joints.
        attach (bool): Wether to attach the joints to the curve.
        create_controls (bool): Wether to create controls on the joints.
        
    Return
        list: [ joints, group, control_group ] joints is a list of joinst, group is the main group for the joints, control_group is the main group above the controls. 
        If create_controls = False then control_group = None
        
    """
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
    """
    A ghost chain has the same hierarchy has the supplied transforms.
    It connects into the an xform group above the transform.  
    This allows for setups that follow a nurbs surface, and then work like an fk hierarchy after.
    
    Args:
        transforms (list): A list of transforms.
        
    Return
        list: A list of ghost transforms corresponding to transforms.
    """
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
    """
    Convenience for converting mesh index numbers to maya names. eg [mesh.vtx[0]] if index = [0]
    Args:
        indices (list): A list of indices.
        mesh (str): The name of a mesh.
    Return 
        list: A list of properly named vertices out of a list of indices.
    """
    verts = []
    
    for index in indices:
        verts.append('%s.vtx[%s]' % (mesh, index))
        
    return verts

def get_vertex_normal(vert_name):
    """
    Get the position of a normal of a vertex.
    
    Args:
        vert_name (str): The name of a vertex.
    
    Return 
        list: eg [0,0,0] The vector where the normal points.
    """
    normal = cmds.polyNormalPerVertex(vert_name, q = True, normalXYZ = True)
    normal = normal[:3]
    return vtool.util.Vector(normal)

def add_poly_smooth(mesh):
    """
    create a polySmooth node on the mesh.
    
    Args:
        mesh (str): The name of a mesh.
        
    Return
        str: The name of the poly smooth node.
    """
    return cmds.polySmooth(mesh, mth = 0, dv = 1, bnr = 1, c = 1, kb = 0, khe = 0, kt = 1, kmb = 1, suv = 1, peh = 0, sl = 1, dpe = 1, ps = 0.1, ro = 1, ch = 1)[0]



#---deformation
    


    
    
def cluster_curve(curve, description, join_ends = False, join_start_end = False, last_pivot_end = False):
    """
    Create clusters on the cvs of a curve.
    joint_start_end, the cv at the start and end of the curve will be joined.
    join_ends, the 2 start cvs will have one cluster, the 2 end cvs will have one cluster.
    
    Args:
        curve (str): The name of a curve.
        description (str): The description to give the clusters.
        join_ends (bool): Wether to joint the 2 start cvs under one cluster, and the two end cvs under another cluster.
        joint_start_end (bool): Wether to join the start and end cvs under one cluster.
        last_pivot_end (bool): Wether to put the pivot of the last cluster at the end of the curve.
        
    Return
        list: [cluster_handle, cluster_handle, ...]
    """
    
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
    """
    Create a cluster on a bunch of points.
    
    Args::
        points (list): The names of points to cluster.
        name (str): The description of the cluster.
        
    Return:
        list: [cluster, handle]
    """
    cluster, handle = cmds.cluster(points, n = inc_name('cluster_%s' % name))
    
    return cluster, handle

def create_cluster_bindpre(cluster, handle):
    """
    Create a bind pre matrix for the cluster.  
    This is good if for treating a cluster like a lattice.  
    Lattices have a base. If the base and the lattice move together the lattice has no effect.
    Likewise if you move the bind pre transform and the cluster handle together the cluster does not deform the mesh.
    Only when you move the cluster handle without the bind pre.
    
    Args:
        cluster (str): The name of a cluster deformer.
        handle (str): The handle for the cluster deformer in cluster 
        
    Return
        str: The bindpre group name.
    """
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
    """
    Convenience for creating a lattice.
    
    Args:
        points (list): List of points, meshes to deform.
        description (str): The description to give the lattice.
        divisions (tuple): eg (3,3,3) The number of divisions to give the lattice on each axis.
        falloff (tuple): eg (2,2,2) The falloff to give each axis.
        
    Return
        list: ffd, lattice, base
    """
    
    
    ffd, lattice, base = cmds.lattice(points, 
                                      divisions = divisions, 
                                      objectCentered = True, 
                                      ldv = falloff, n = 'ffd_%s' % description)
    
    return ffd, lattice, base
    
    

def get_history(geometry):
    """
    Get the history of the geometry. This will not search too deep.
    
    Args:
        geometry (str): The name of the geometry
        
    Return
        list: A list of deformers in the deformation history.
    """
    scope = cmds.listHistory(geometry, interestLevel = 1)
    
    found = []
    
    for thing in scope[1:]:
        
        found.append(thing)
            
        if cmds.objectType(thing, isa = "shape") and not cmds.nodeType(thing) == 'lattice':
            return found
        
    if not found:
        return None
    
    return found

def find_deformer_by_type(mesh, deformer_type, return_all = False):
    """
    Given a mesh find a deformer with deformer_type in the history.
    
    Args:
        mesh (str): The name of a mesh.
        deformer_type (str): Corresponds to maya deformer type, eg. skinCluster, blendShape
        return_all (bool): Wether to return all the deformers found of the specified type, or just the first one.
        
    Return
        list: The names of deformers of type found in the history.
    """
    
    scope = cmds.listHistory(mesh, interestLevel = 1)
    
    found = []
    
    history = get_history(mesh)
    
    if history:
    
        for thing in history:
            if cmds.nodeType(thing) == deformer_type:
                if not return_all:
                    return thing
                
                found.append(thing)
            
    if not found:
        return None
        
    return found

def get_influences_on_skin(skin_deformer):
    """
    Get the names of the skin influences in the skin cluster.
    
    Args:
        skin_deformer (str)
        
    Return
        list: influences found in the skin cluster
    """
    indices = get_indices('%s.matrix' % skin_deformer)
       
    influences = []
       
    for index in indices:
        influences.append( get_skin_influence_at_index(index, skin_deformer) )
        
    return influences

def get_non_zero_influences(skin_deformer):
    """
    Get influences that have weight in the skin cluster.
    
    Args:
        skin_deformer (str)
        
    Return
        list: influences found in the skin cluster that have influence.
        
    """
    
    influences = cmds.skinCluster(skin_deformer, q = True, wi = True)
    
    return influences
    
def get_index_at_skin_influence(influence, skin_deformer):
    """
    Given an influence name, find at what index it connects to the skin cluster. 
    This corresponds to the matrix attribute. eg. skin_deformer.matrix[0] is the connection of the first influence.
    
    Args:
        influence (str): The name of an influence.
        skin_deformer (str): The name of a skin_deformer affected by influence.
        
    Return
        int: The index of the influence. 
    """
    indices = get_indices('%s.matrix' % skin_deformer)
          
    for index in indices:
        found_influence = get_skin_influence_at_index(index, skin_deformer)
                
        if influence == found_influence:
            return index
        
def get_skin_influence_at_index(index, skin_deformer):
    """
    Find which influence connect to the skin cluster at the index.
    This corresponds to the matrix attribute. eg. skin_deformer.matrix[0] is the connection of the first influence.
    
    Args:
        index (int): The index of an influence.
        skin_deformer (str): The name of the skin cluster to check the index.
        
    Return
        str: The name of the influence at the index.
        
    """
    
    influence_slot = '%s.matrix[%s]' % (skin_deformer, index) 
    
    connection = get_attribute_input( influence_slot )
    
    if connection:
        connection = connection.split('.')
        return connection[0]    

def get_skin_influence_indices(skin_deformer):
    """
    Get the indices of the connected influences.
    This corresponds to the matrix attribute. eg. skin_deformer.matrix[0] is the connection of the first influence.
    
    Args:
        skin_deformer (str): The name of a skin cluster.
    
    Return
        list: The list of indices.
    """
    
    return get_indices('%s.matrix' % skin_deformer)

def get_skin_influences(skin_deformer, return_dict = False):
    """
    Get the influences connected to the skin cluster.
    Return a dictionary with the keys being the name of the influences.
    The value at the key the index where the influence connects to the skin cluster.
    
    Args:
        skin_deformer (str): The name of a skin cluster.
        return_dict (bool): Wether to return a dictionary.
        
    Return
        list, dict: A list of influences in the skin cluster. If return_dict = True, return dict[influence] = index
    """
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
    """
    Get all meshses that are skinned to the specified joint.
    
    Args:
        joint (str): The name of a joint.
        
    Return
        list: The skin clusters affected by joint.
    """
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
    """
    Get the skin weights for the skin cluster.
    Return a dictionary where the key is the influence, 
    and the value is the a list of weights at the influence.
    
    Args:
        skin_deformer (str): The name of a skin deformer.
        
    Return
        dict: dict[influence] = weight values corresponding to point order.
    """
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

def get_skin_blend_weights(skin_deformer):
    """
    Get the blendWeight values on the skin cluster.
    
    Args:
        skin_deformer (str): The name of a skin deformer.
    
    Return
        list: The blend weight values corresponding to point order.
    """
    indices = get_indices('%s.weightList' % skin_deformer)
    
    blend_weights_attr = '%s.blendWeights' % skin_deformer
    blend_weights = get_indices(blend_weights_attr)
    blend_weight_dict = {}
        
    if blend_weights:
    
        for blend_weight in blend_weights:
            blend_weight_dict[blend_weight] = cmds.getAttr('%s.blendWeights[%s]' % (skin_deformer, blend_weight))
    
    
    values = []
    
    for inc in range(0, len(indices)):
        
        if inc in blend_weight_dict:
            values.append( blend_weight_dict[inc] )
            continue
                    
        if not inc in blend_weight_dict:
            values.append( 0.0 )
            continue

    return values

def set_skin_blend_weights(skin_deformer, weights):
    """
    Set the blendWeights on the skin cluster given a list of weights.
    
    Args:
        skin_deformer (str): The name of a skin deformer.
        weights (list): A list of weight values corresponding to point order.
    """
    indices = get_indices('%s.weightList' % skin_deformer)
    
    for inc in range(0, len(indices)):
        if cmds.objExists('%s.blendWeights[%s]' % (skin_deformer, inc)):
            try:
                cmds.setAttr('%s.blendWeights[%s]' % (skin_deformer, inc), weights[inc])
            except:
                pass
        

def set_skin_weights_to_zero(skin_deformer):
    """
    Set all the weights on the mesh to zero.
    
    Args:
        skin_deformer (str): The name of a skin deformer.
    
    """
    weights = cmds.ls('%s.weightList[*]' % skin_deformer)
        
    for weight in weights:
            
        weight_attributes = cmds.listAttr('%s.weights' % (weight), multi = True)
            
        for weight_attribute in weight_attributes:
            cmds.setAttr('%s.%s' % (skin_deformer, weight_attribute), 0)

def set_vert_weights_to_zero(vert_index, skin_deformer, joint = None):
    """
    Set the weights at the given point index to zero.
    
    Args:
        vert_index (int): The index of a vert.
        skin_deformer (str): The name of a skin deformer.
        joint (str): The name of a joint that is influencing the vert. If not joint given all the influences for the vert will be zeroed out.
    """
    
    
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
    """
    Set the deformer weights. Good for cluster and wire deformers. 
    
    Args:
        weights (list): A list of weight values that should correspond to point order.
        deformer (str): The name of a deformer. eg. cluster or wire.
        index (int): The geometry index to set weights on. By default it will work on the first mesh.
    """
    
    for inc in range(0, len(weights) ):    
        cmds.setAttr('%s.weightList[%s].weights[%s]' % (deformer, index, inc), weights[inc])
        
def get_deformer_weights(deformer, index = 0):
    """
    Get the weights on a deformer. In point order.
    
    Args:
        deformer (str): The name of a deformer.
        index (int): The index of the meshes attached. 
    
    Return
        list: The weight values in point order.
        
    """
    
    meshes = cmds.deformer(deformer, q = True, g = True)
    
    try:
        mesh = meshes[index]
        vtool.util.warning('index "%s" out of range of deformed meshes.' % index)
    except:
        return
    
    indices = cmds.ls('%s.vtx[*]' % mesh, flatten = True)
            
    weights = []
    
    for inc in range(0, len(indices)):
        weights.append( cmds.getAttr('%s.weightList[%s].weights[%s]' % (deformer, index, inc)) )
    
    return weights

def set_wire_weights(weights, wire_deformer, index = 0):
    """
    Set the wire weights given a list of weights that corresponds to point order.
    
    Args:
        weights (list): A list of weight values corresponding to point order.
        wire_deformer (str): The name of a wire deformer.
        index (int): The index of the mesh to work on. By default it will work on the first mesh.
    """
    #might need refresh 
    
    set_deformer_weights(weights, wire_deformer, index)


def get_wire_weights(wire_deformer, index = 0):
    """
    Get the weights on a wire deformer. In point order.
    
    Args:
        wire_deformer (str): The name of a deformer.
        index (int): The index of the meshes attached. 
    
    Return
        list: The weight values in point order.
        
    """
    
    get_deformer_weights(wire_deformer, index)

def get_cluster_weights(cluster_deformer, index = 0):
    """
    Get the weights on a cluster deformer. In point order.
    
    Args:
        cluster_deformer (str): The name of a deformer.
        index (int): The index of the meshes attached. 
    
    Return
        list: The weight values in point order.
        
    """
    
    return get_deformer_weights(cluster_deformer, index)

def get_blendshape_weights(blendshape_deformer, mesh, index = -1):
    """
    Not implemented
    """
    pass

def invert_blendshape_weight(blendshape_deformer, index = -1):
    """
    Not implemented
    """
    pass

def get_intermediate_object(transform):
    """
    Get the intermediate object in the list of shape nodes under transform.
    
    Args:
        transform (str): The name of a transform.
    """
    shapes = cmds.listRelatives(transform, s = True, f = True)
    
    return shapes[-1]
    
def set_all_weights_on_wire(wire_deformer, weight, slot = 0):
    """
    Set all the weights on a wire deformer.
    
    Args:
        wire_deformer (str): The name of a wire deformer.
        weight (float): The weight value to assign the weights of a wire deformer.
        slot (int): The index of the deformed mesh. Usually 0.
    
    """
    
    meshes = cmds.deformer(wire_deformer, q = True, g = True)
    
    try:
        mesh = meshes[slot]
    except:
        mesh = None
    
    if not mesh:
        indices = get_indices('%s.weightList[%s]' % (wire_deformer,slot))
    if mesh:
        indices = cmds.ls('%s.vtx[*]' % mesh, flatten = True)    
    
    for inc in range(0, len(indices) ):
        cmds.setAttr('%s.weightList[%s].weights[%s]' % (wire_deformer, slot, inc), weight)
        
        
def set_wire_weights_from_skin_influence(wire_deformer, weighted_mesh, influence):
    """
    Set the wire weights from a skinned joint.
    
    Args:
        wire_deformer (str): The name of a wire deformer.
        weighted_mesh (str): The name of a skinned mesh.
        influence (str): The name of an influence.
        
    """
    
    skin_cluster = find_deformer_by_type(weighted_mesh, 'skinCluster')
    index = get_index_at_skin_influence(influence, skin_cluster)
    
    if index == None:
        vtool.util.show('No influence %s on skin %s.' % (influence, skin_cluster))
        return
    
    weights = get_skin_weights(skin_cluster)
    
    weight = weights[index]
    
    set_wire_weights(weight, wire_deformer)
    

def prune_wire_weights(deformer, value = 0.0001):
    """
    Removes weights that fall below value.
    
    Args:
        deformer (str): The name of a deformer.
        value (float): The value below which verts get removed from wire deformer.
    """
    
    meshes = cmds.deformer(deformer, q = True, g = True)
    
    try:
        mesh = meshes[0]
    except:
        mesh = None
    
    verts = cmds.ls('%s.vtx[*]' % mesh, flatten = True)
    
    found_verts = []
    
    for inc in range(0, len(verts)):
        weight_value = cmds.getAttr('%s.weightList[%s].weights[%s]' % (deformer, 0, inc))
        
        if weight_value < value:
            found_verts.append('%s.vtx[%s]' % (mesh, inc))
    
    cmds.sets(found_verts, rm = '%sSet' % deformer  )
    

def map_influence_on_verts(verts, skin_deformer):
    """
    Given a list of verts, get which influences have the most weight.
    
    Args:
        verts (list): The index of vertices on the mesh to get weights from.
        skin_deformer (str): The name of a skin cluster.
        
    Return
        dict: dict[influence_index] = value
    
    """
    
    value_map = {}
    
    for vert in verts:
        vert_index = int(vert)
        
        influences = cmds.listAttr('%s.weightList[%s].weights' % (skin_deformer, vert_index), multi = True )
        
        influence_count = len(influences)
        min_value = 1.0/influence_count
        top_value = 1.0 - min_value
                
        found_value = [None, 0]
                            
        for influence in influences:
            influence_index = re.findall('\d+', influence)[1]
            value = cmds.getAttr('%s.%s' % (skin_deformer, influence))

            if influence_count == 1:
                found_value = [influence_index, value]
                break

            if value < min_value:
                continue
            
            if value == 0:
                continue
            
            if value >= top_value:
                found_value = [influence_index, value]
                break
                                                
            if value >= found_value[1]:
                found_value = [influence_index, value]
        
        influence_index, value = found_value
                    
        if not value_map.has_key(influence_index):
            value_map[influence_index] = value
    
        if value_map.has_key(influence_index):
            value_map[influence_index] += value

    return value_map

def get_faces_at_skin_influence(mesh, skin_deformer):
    """
    Args:
        mesh (str): The name of a mesh affected by skin_deformer.
        skin_deformer (str): The name of a skin deformer.
        
    Return
        dict: dict[influence_index] = [face ids]
    """
    scope = cmds.ls('%s.f[*]' % mesh, flatten = True)
    
    index_face_map = {}
    
    inc = 0
    
    for face in scope:
            
        inc += 1
           
        verts = cmds.polyInfo(face, fv = True)
        verts = verts[0].split()
        verts = verts[2:]
        
        value_map = map_influence_on_verts(verts, skin_deformer)
        
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
    """
    Split a mesh into smaller sections based on skin deformer weights.
    
    Args:
        mesh (str): The name of a mesh.
        skin_deformer (str): The name of a skin deformer.
        vs_attribute (str): The name of a visibility attribute to connect to. eg. 'node_name.sectionVisibility'
        constrain (bool): Wether to constrain the sections or parent them.
        
    Return
        str: If constrain = True, the name of the group above the sections. Otherwise return none.
    """
    
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

"""   
#@undo_chunk
def transfer_weight(source_joint, target_joints, mesh):
"""
    #This is now depricated.  Use TransferWeight class.
    #Transfer weight from the source joint to the target joints.
    
    
    #Args:
    #    source_joint (str): The name of the joint to transfer from.
    #    target_joints (list): A list of joints to transfer to. 
    #    mesh (str): The name of the mesh to work on.
"""
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
"""
 
def add_joint_bindpre(skin, joint, description = None):
    """
    Add a bind pre locator to the bindPreMatrix of the skin.
    
    Args:
        skin (str): The name of a skin cluster to add bind pre to.
        joint (str): The name of the joint to match bind pre to.
        description(str): The description of the bind pre.
        
    Return
        str: The name of the bind pre locator.
        
    """
    
    if not description:
        description = joint
    
    bindPre_locator = cmds.spaceLocator(n = inc_name('locator_%s' % description))[0]
    #cmds.parent(bindPre_locator, bindPre_locator_group)
    
    index = get_index_at_skin_influence(joint, skin)
    
    match = MatchSpace(joint, bindPre_locator)
    match.translation_rotation()
        
    #attach_to_curve(bindPre_locator, base_curve)
    
    cmds.connectAttr('%s.worldInverseMatrix' % bindPre_locator, '%s.bindPreMatrix[%s]' % (skin, index))
    
    return bindPre_locator

"""
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
"""
    
def convert_wire_deformer_to_skin(wire_deformer, description, joint_count = 10, delete_wire = True, skin = True, falloff = 1, create_controls = True):
    """
    Meant to take a wire deformer and turn it into a skinned joint chain.
    
    Args:
        wire_deformer (str): The name of a wire deformer.
        description (str): The description to give the setup
        joint_count (int): The number of joints to create. Higher number better resembles the effect of a wire deformer, but gets slow fast.
        delete_wire (bool): Wether to delete the original wire deformer.
        skin (bool): Wether to calculate and skin the bones to mimic the wire deformer.
        falloff (float): Corresponds to the wire distance value.
        create_controls (bool): Wether to create controls on the joints.
         
    Return
        list: [convert_group, control_group, zero_verts] Zero verts are the verts that were not affected by the wire conversion.
    """
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
            
            wire_weights = get_wire_weights(wire_deformer, inc)
            
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
    """
    Convert a wire deformer to skinned joints
    
    Args:
        wire_deformer (str): The name of a wire deformer.
        description (str): The description to give the setup.
        joint_count (int): The number of joints to create. Higher number better resembles the effect of a wire deformer, but gets slow fast.
        falloff (float): Corresponds to the wire distance value.
        
    Return
        str: The top group above the joints.
    """
    
    vtool.util.show('converting %s' % wire_deformer)
    
    convert_group = cmds.group(em = True, n = inc_name('convertWire_%s' % description))
    
    curve = get_attribute_input('%s.deformedWire[0]' % wire_deformer, node_only = True)
    curve = cmds.listRelatives(curve, p = True)[0]
    
    
    joints = create_oriented_joints_on_curve(curve, count = joint_count)
    
    meshes = cmds.deformer(wire_deformer, q = True, geometry = True)
    if not meshes:
        return
    
    inc = 0
    
    for mesh in meshes:
        zero_verts = []
        skin = True                 
        if skin:
            verts = cmds.ls('%s.vtx[*]' % mesh, flatten = True)
            
            wire_weights = get_wire_weights(wire_deformer, inc)
            
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
    """
    Transfer the weight from one joint to another.  Does it for all vertices affected by source_joint in mesh.
    
    Args:
        source_joint (str): The name of a joint to take weights from.
        target_joint (str): The name of a joint to transfer weights to.
        mesh (str): The mesh to work with.
    """
    if mesh:
        
        skin_deformer = find_deformer_by_type(mesh, 'skinCluster')
        
        influences = get_influences_on_skin(skin_deformer)
        
        if not target_joint in influences:
            cmds.skinCluster(skin_deformer, e = True, ai = target_joint, wt = 0.0, nw = 1)  
        
        index = get_index_at_skin_influence(source_joint, skin_deformer)
        
        if not index:
            cmds.warning( 'could not find index for %s on mesh %s' % (source_joint, mesh) )
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
    """
    Transfer the weight from child joint to parent joint.  Does it for all vertices affected by child joint in mesh.
    If no parent joint, then do nothing.
    
    Args:
        joint (str): The name of a joint to take weights from.
        mesh (str): The mesh to work with.
        
    """    
    parent_joint = cmds.listRelatives(joint, type = 'joint', p = True)
    
    if parent_joint:
        parent_joint = parent_joint[0]
        
    if not parent_joint:
        return
    
    transfer_joint_weight_to_joint(joint, parent_joint, mesh)
   
def transfer_cluster_weight_to_joint(cluster, joint, mesh):
    """
    Given the weights of a cluster, transfer them to a joint.
    
    """
    skin = find_deformer_by_type(mesh, 'skinCluster')
    
    weights = get_cluster_weights(cluster)
    
    for inc in range(0, len(weights)):
        
        vert = '%s.vtx[%s]' % (mesh, inc)
        
        cmds.skinPercent(skin, vert, r = False, transformValue = [joint, weights[inc]])
    
def transfer_joint_weight_to_blendshape(blendshape_node, joint, mesh, index = 0, target = -1):
    """
    Transfer the weight of a joint on a skincluster to a blendshape target weight.
    
    Args:
        blendshape_node (str): The name of a blendshape node.
        joint (str): The name of a joint influencing mesh.
        mesh (str): The name of a mesh that has joint has a skin influence.
        index (int): Is the index of the blendshaped mesh. Usually 0. Can be 1 or more if blendshape_node affects more than one mesh.
        target (int): If target is -1, than affect the base weights of the blendshapes... which affects all targets. If target = 0 or greater, then affect the weights of the target at that index.
    """
    skin = find_deformer_by_type(mesh, 'skinCluster')
    weights = get_skin_weights(skin)
    
    influence_index = get_index_at_skin_influence(joint, skin)
    
    weight_values = weights[influence_index]
    
    inc = 0
    
    if target == -1:
        for weight in weight_values:
            cmds.setAttr('%s.inputTarget[%s].baseWeights[%s]' % (blendshape_node, index, inc), weight)
            inc += 1
            
    if target >= 0:
        for weight in weight_values:
            cmds.setAttr('%s.inputTarget[%s].inputTargetGroup[%s].targetWeights[%s]' % (blendshape_node, index, target, inc), weight)
            inc += 1
    
def add_missing_influences(skin1, skin2):
    """
    Make sure used influences in skin1 are added to skin2. 
    When transfering skin weights this can be handy.
    
    Args:
        skin1 (str): The name of a skin cluster.
        skin2 (str): The name of a skin cluster.
    """

    influences1 = get_non_zero_influences(skin1)
    influences2 = get_non_zero_influences(skin2)
    
    for influence1 in influences1:
        
        if not influence1 in influences2:
            cmds.skinCluster(skin2, edit = True, ai = influence1, wt = 0.0, nw = 1)
    
@undo_chunk   
def skin_mesh_from_mesh(source_mesh, target_mesh, exclude_joints = [], include_joints = [], uv_space = False):
    ''' 
    This skins a mesh based on the skinning of another mesh.  
    Source mesh must be skinned.  The target mesh will be skinned with the joints in the source.
    The skinning from the source mesh will be projected onto the target mesh.
    exlude_joints = joints to exclude from the target's skin cluster.
    include_joints = only include the specified joints. 
    If exlude_joints, only exclude_joints in include_joints will be excluded.
    
    Args:
        source_mesh (str): The name of a mesh.
        target_mesh (str): The name of a mesh.
        exlude_joints (list): Exclude the named joints from the skin cluster.
        include_joints (list): Include the named joint from the skin cluster.
        uv_space (bool): Wether to copy the skin weights in uv space rather than point space.
    '''
    
    vtool.util.show('skinning %s' % target_mesh)
    
    skin = find_deformer_by_type(source_mesh, 'skinCluster')
    
    if not skin:
        cmds.warning('%s has no skin. Nothing to copy.' % source_mesh)
        return
    
    other_skin = find_deformer_by_type(target_mesh, 'skinCluster')
    
    if other_skin:
        cmds.warning('%s already has a skin cluster.' % target_mesh)
    
    
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
        skin_name = get_basename(target_mesh)
        other_skin = cmds.skinCluster(influences, target_mesh, tsb=True, n = inc_name('skin_%s' % skin_name))[0]
        
    if other_skin:
        if not uv_space:
            cmds.copySkinWeights(ss = skin, 
                                 ds = other_skin, 
                                 noMirror = True, 
                                 surfaceAssociation = 'closestPoint', 
                                 influenceAssociation = ['name'], 
                                 normalize = True)
        
        if uv_space:
            cmds.copySkinWeights(ss = skin, 
                                 ds = other_skin, 
                                 noMirror = True, 
                                 surfaceAssociation = 'closestPoint', 
                                 influenceAssociation = ['name'],
                                 uvSpace = ['map1','map1'], 
                                 normalize = True)
            
    other_influences = cmds.skinCluster(other_skin, query = True, wi = True)
        
    for influence in influences:
        
        if not influence in other_influences:
            try:
                cmds.skinCluster(other_skin, edit = True, ri = influence)
            except:
                cmds.warning('Could not remove influence %s on mesh %s' % (influence, target_mesh))
                
    #cmds.undoInfo(state = True)
    

def skin_group_from_mesh(source_mesh, group, include_joints = [], exclude_joints = []):
    ''' 
    This skins a group of meshes based on the skinning of the source mesh.  
    Source mesh must be skinned.  The target group will be skinned with the joints in the source.
    The skinning from the source mesh will be projected onto the meshes in the group.
    exlude_joints = joints to exclude from the target's skin cluster.
    include_joints = only include the specified joints. 
    If exlude_joints, only exclude_joints in include_joints will be excluded.
    
    
    Args:
        source_mesh (str): The name of a mesh.
        group (str): The name of a group.
        exlude_joints (list): Exclude the named joints from the skin cluster.
        include_joints (list): Include the named joint from the skin cluster.
    '''
    
    
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
    ''' 
    This skins a lattice based on the skinning of the source mesh.
    The lattice is generated automatically around the target mesh using divisions and falloff parameters.  
    Source mesh must be skinned.  The target lattice will be skinned with the joints in the source.
    The skinning from the source mesh will be projected onto the target lattice.
    exlude_joints = joints to exclude from the target's skin cluster.
    include_joints = only include the specified joints. 
    If exlude_joints, only exclude_joints in include_joints will be excluded.
    
    Args:
        source_mesh (str): The name of a mesh.
        target (str): The name of a group or mesh.
        divisions (list): eg [10,10,10] the divisions of the lattice.
        falloff (list): eg [2,2,2] the falloff of the divisions of the lattice.
        name (str): The description to give the lattice.
        exlude_joints (list): Exclude the named joints from the skin cluster.
        include_joints (list): Include the named joint from the skin cluster.
    '''
    
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
    ''' 
    This skins a curve based on the skinning of the source mesh.  
    Source mesh must be skinned.  The target curve will be skinned with the joints in the source.
    The skinning from the source mesh will be projected onto the curve.
    exlude_joints = joints to exclude from the target's skin cluster.
    include_joints = only include the specified joints. 
    If exlude_joints, only exclude_joints in include_joints will be excluded.
    
    Args:
    
        source_mesh (str): The name of a mesh.
        target (str): The name of a curve.
        exlude_joints (list): Exclude the named joints from the skin cluster.
        include_joints (list): Include the named joint from the skin cluster.
    '''
    
    skin_mesh_from_mesh(source_mesh, target, exclude_joints = exclude_joints, include_joints = include_joints)

def skin_group(joints, group):
    """
    Skin all the meshes in a group to the specified joints.  
    Good for attaching the face geo to the head joint.
    
    Args:
        joints (list): A list of joints to skin to.
        group (str): The group to skin.
    """
    rels = cmds.listRelatives(group, ad = True, f = True)
    
    for rel in rels:
        
        name = rel.split('|')[-1]
        
        try:
            cmds.skinCluster(joints, rel, tsb = True, n = 'skin_%s' % name)
        except:
            pass
            

def lock_joints(skin_cluster, skip_joints = None):
    """
    Lock the joints in the skin cluster except joints in skip_joints
    
    Args:
        skin_cluster (str): The name of a skin cluster.
        skip_joints (list): The names of the joints to skip.
    """
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
    """
    Get the closest vertices to a joint.
    
    Args:
        joints (list): A list of joints.
        verts (list): A list of vertices.
    
    Return 
        dict: dict[joint] = vertex list
    """

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
    """
    Create an Maya exclusive bind wrap. 
    Source_mesh drives target_mesh.
    
    Args:
        source_mesh (str): The mesh to influence target_mesh. This can be a list of meshes.
        target_mesh (str): Mesh to be deformed by source_mesh.
        
    Return
        list: A list of base meshes.
    """
    
    source_mesh = vtool.util.convert_to_sequence(source_mesh)
    
    wrap = MayaWrap(target_mesh)
    wrap.set_driver_meshes(source_mesh)
    
    wrap.create()
    
    return wrap.base_meshes

"""
def exclusive_bind_wrap(source_mesh, target_mesh):
    wrap = MayaWrap(target_mesh)
    
    source_mesh = vtool.util.convert_to_sequence(source_mesh)
    
    wrap.set_driver_meshes(source_mesh)
        
    wraps = wrap.create()
    
    return wraps
"""
    
def wire_mesh(curve, mesh, falloff):
    """
    Create a wire deformer.
    
    Args:
        curve (str): The name of a curve.
        mesh (str): The name of a mesh.
        falloff (float): The falloff of the wire influence.
        
    Return
        list: [wire_deformer, wire_curve]
    """
    wire_deformer, wire_curve = cmds.wire(mesh,  gw = False, w = curve, n = 'wire_%s' % curve, dds = [0, falloff])
    cmds.setAttr('%s.rotation' % wire_deformer, 0)
    
    return wire_deformer, wire_curve
    
def wire_to_mesh(edges, geometry, description, auto_edge_path = True):
    """
    One mesh follows the other via a wire deformer.
    A nurbs curve is generated automatically from the edges provided. 
    
    auto_edge_path = The command will try fill in gaps between edges.
    
    Args:
        edges (list): The edges from the source mesh to build the wire curve from. Eg. ["node_name.e[0]"]
        geometry (list): The target geometry that should follow.
        description (str): The description to give the setup.
        auto_edge_path (bool): Wether to fill in the path between the edges.
        
    Return
        str: The group name for the setup.
    """
    group = cmds.group(em = True, n = inc_name('setup_%s' % description))
    
    if auto_edge_path:
        edge_path = get_edge_path(edges)
    if not auto_edge_path:
        edge_path = cmds.ls(edges, flatten = True)
    
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
    """
    Convenience to use Maya's weight hammer command on many verts individually.
    
    Args:
        verts (list): The names of verts to weigth hammer. If verts = None, currently selected verts will be hammered. 
        
    """
    if is_a_mesh(verts):
        verts = cmds.ls('%s.vtx[*]' % verts, flatten = True)
    
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
            #vtool.util.show(inc, 'of', count)
            #do not remove
            print inc, 'of', count
        
        mel.eval('weightHammerVerts;')
            
        inc += 1
        


def map_blend_target_alias_to_index(blendshape_node):
    """
    Get the aliases for blendshape weight targets and the index of the target.
    
    Args:
        blendshape_node (str): The name of the blendshape.
    
    Return 
        dict: dict[alias] = target index
    """
    
    aliases = cmds.aliasAttr(blendshape_node, query = True)
    
    alias_map = {}
    
    if not aliases:
        return
    
    for inc in range(0, len(aliases), 2):
        alias = aliases[inc]
        weight = aliases[inc+1]
        
        index = vtool.util.get_end_number(weight)
        
        alias_map[index] = alias
        
    return alias_map

def map_blend_index_to_target_alias(blendshape_node):
    """
    Get a map between the target index and its alias name on the blendshape.
    
    Args:
        blendshape_node (str): The name of the blendshape.
    
    Return 
        dict: dict[target index] = weight alias
    """
    
    
    aliases = cmds.aliasAttr(blendshape_node, query = True)
    
    alias_map = {}
    
    if not aliases:
        return
    
    for inc in range(0, len(aliases), 2):
        alias = aliases[inc]
        weight = aliases[inc+1]
        
        index = vtool.util.get_end_number(weight)
        
        alias_map[alias] = index
        
    return alias_map

def get_index_at_alias(alias, blendshape_node):
    """
    Given a blendshape weight alias, get the corresponding target index.
    
    Args:
        alias (str): The name of the weight alias.
    
    Return 
        int: The corresponding target index to the alias.
    """
    
    map_dict = map_blend_index_to_target_alias(blendshape_node)
    
    if alias in map_dict:
        return map_dict[alias]

@undo_chunk
def chad_extract_shape(skin_mesh, corrective, replace = False):
    """
    Get the delta of t he skin cluster and blendshape to the corrective.  
    Requires a skin cluster or blendshape in the deformation stack.
    
    Args:
        skin_mesh (str): The name of the skinned mesh, or blendshaped mesh to extract a delta from.
        corrective (str): The target shape for the skin mesh.  
        replace (bool): Wether to replace the corrective with the delta.
        
    Return
        str: The name of the delta. The delta can be applied to the blendshape before the skin cluster.
    """
    
    try:
        
        envelopes = EnvelopeHistory(skin_mesh)
        
        skin = find_deformer_by_type(skin_mesh, 'skinCluster')
        
        if not cmds.pluginInfo('cvShapeInverterDeformer.py', query=True, loaded=True):
        
            file_name = __file__
            file_name = file_name.replace('util.py', 'cvShapeInverterDeformer.py')
            file_name = file_name.replace('.pyc', '.py')
            
            cmds.loadPlugin( file_name )
        
        import cvShapeInverterScript as correct
        
        envelopes.turn_off()
        
        if skin:
            cmds.setAttr('%s.envelope' % skin, 1)
                
        offset = correct.invert(skin_mesh, corrective)
        
        cmds.delete(offset, ch = True)
        
        orig = get_intermediate_object(skin_mesh)
        
        orig = create_shape_from_shape(orig, 'home')
        
        envelopes.turn_on(respect_initial_state=True)
        envelopes.turn_off_referenced()
        
        if skin:
            cmds.setAttr('%s.envelope' % skin, 0)
        
        skin_shapes = get_shapes(skin_mesh)
        skin_mesh_name = get_basename(skin_mesh, True)
        other_delta = create_shape_from_shape(skin_shapes[0], inc_name(skin_mesh_name))
        
        blendshapes = find_deformer_by_type(skin_mesh, 'blendShape', return_all = True)
        
        if blendshapes:
            for blendshape in blendshapes[1:]:
                cmds.setAttr('%s.envelope' % blendshape, 0)
        
        if skin:
            cmds.setAttr('%s.envelope' % skin, 1)
        
        quick_blendshape(other_delta, orig, -1)
        quick_blendshape(offset, orig, 1)
        
        cmds.select(cl = True)
        
        cmds.delete(orig, ch = True)
        cmds.delete(other_delta)
        cmds.delete(offset)
        
        cmds.rename(orig, offset)
        
        if replace:
            parent = cmds.listRelatives(corrective, p = True)
            cmds.delete(corrective)
            
            offset = cmds.rename(offset, corrective)
            
            if parent:
                cmds.parent(offset, parent)
        
        envelopes.turn_on(respect_initial_state=True)
        
        return offset
        
    except (RuntimeError):
        vtool.util.error( traceback.format_exc() )
        
        
def get_blendshape_delta(orig_mesh, source_meshes, corrective_mesh, replace = True):
    """
    Create a delta following the equation:
    delta = orig_mesh + corrective_mesh - source_meshes
    
    Args:
        orig_mesh (str): The unchanged base mesh.
        source_meshes (list): Name of the mesh that represents where the mesh has moved. Can be a list or a single target. 
        corrective_mesh (str): Name of the mesh where the source mesh needs to move to.
    
    Return 
        (str): name of new delta mesh
    """
    
    sources = vtool.util.convert_to_sequence(source_meshes)
    
    offset = cmds.duplicate(corrective_mesh)[0]
    orig = create_shape_from_shape(orig_mesh, 'home')
    
    for source in sources:
        other_delta = cmds.duplicate(source)[0]
        quick_blendshape(other_delta, orig, -1)
    
    quick_blendshape(offset, orig, 1)
    
    cmds.select(cl = True)
    
    cmds.delete(orig, ch = True)
    
    cmds.delete(other_delta, offset)
    
    corrective = cmds.rename(orig, 'delta_%s' % corrective_mesh)

    if replace:
        parent = cmds.listRelatives(corrective_mesh, p = True)
        cmds.delete(corrective_mesh)
        
        corrective = cmds.rename(corrective, corrective_mesh)
        
        if parent:
            cmds.parent(corrective, parent[0])
    
    return corrective


def create_surface_joints(surface, name, uv_count = [10, 4], offset = 0):
    """
    Create evenly spaced joints on a surface.
    
    Args:
        surface (str): the name of a nurbs surface.
        name(str): = the name to give to nodes created.
        uv_count(list): = number of joints on u and v, eg [10,4]
        offset(float): = the offset from the border.
        
    Return
        list: [top_group, joints] The top group is the group for the joints. The joints is a list of joints by name that were created.
    """
    
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
    """
    Create a blendshape. Add target source_mesh into the target_mesh.
    If target_mesh already has a blendshape, add source_mesh into existing blendshape.
    
    Args:
        blendshape (str): The name of the blendshape to work with.
        target_mesh (str): The name of the target mesh to add into the blendshape.
        weight (float): The value to set the weight of the target to.
        blendshape (str): The name of the blendshape to edit. If None, it will be set to 'blendshape_%s' % target_mesh.
        
    Return
        str: The name of the blendshape node.
    """
    blendshape_node = blendshape
    
    source_mesh_name = source_mesh.split('|')[-1]
    
    bad_blendshape = False
    long_path = None
    
    base_name = get_basename(target_mesh, remove_namespace = True)
    
    if not blendshape_node:
        blendshape_node = 'blendshape_%s' % base_name
    
    if cmds.objExists(blendshape_node):
        
        shapes = cmds.deformer(blendshape_node, q = True, g = True)
        
        target_shapes = get_shapes_in_hierarchy(target_mesh)
        
        if len(shapes) == len(target_shapes):
                        
            long_path = cmds.ls(shapes[0], l = True)[0]
            
            if long_path != target_shapes[0]:
                
                bad_blendshape = True
        
        if len(shapes) != len(target_shapes):
            
            bad_blendshape = True
        
        long_path = None
        
        
        if not bad_blendshape:
            
            bad_blendshape = False
            
            for inc in range(0, len(target_shapes)):
            
                target_shape = target_shapes[inc]
                shape = shapes[inc]
                
                long_path = cmds.ls(shape, l = True)[0]
                
                if not long_path in target_shape:
                    bad_blendshape = True
                    
                    break
        
        if not bad_blendshape:
            count = cmds.blendShape(blendshape_node, q= True, weightCount = True)
            
            cmds.blendShape(blendshape_node, edit=True, tc = False, t=(target_mesh, count+1, source_mesh, 1.0) )
            
            try:
                cmds.setAttr('%s.%s' % (blendshape_node, source_mesh_name), weight)
            except:
                pass
            
            return blendshape_node
       
    if bad_blendshape:
        
        blendshape_node = inc_name(blendshape_node)
        
    if not cmds.objExists(blendshape_node):
        
        cmds.blendShape(source_mesh, target_mesh, tc = False, weight =[0,weight], n = blendshape_node, foc = True)
        
    try:
        cmds.setAttr('%s.%s' % (blendshape_node, source_mesh_name), weight)
    except:
        pass
        
    return blendshape_node
    
def isolate_shape_axis(base, target, axis_list = ['X','Y','Z']):
    """
    Given a base mesh, only take axis movement on the target that is specified in axis_list.
    
    Args:
        base (str): The base mesh that has no targets applied.
        target (str): The target mesh vertices moved to a different position than the base.
        axis_list (list): The axises of movement allowed. If axis_list = ['X'], only vertex movement on x will be present in the result.
    
    Return
        str: A new mesh with verts moving only on the isolated axis.
    """
    
    
    verts = cmds.ls('%s.vtx[*]' % target, flatten = True)
    
    if not verts:
        return
    
    vert_count = len(verts)
    
    axis_name = string.join(axis_list, '_')
    
    new_target = cmds.duplicate(target, n = '%s_%s' % (target, axis_name))[0]
    
    for inc in range(0, vert_count):
        
        base_pos = cmds.xform('%s.vtx[%s]' % (base, inc), q = True, t = True, ws = True)
        target_pos = cmds.xform('%s.vtx[%s]' % (target, inc), q = True, t = True, ws = True)
        
        if (base_pos == target_pos):
            continue
        
        small_x = False
        small_y = False
        small_z = False
        if abs(base_pos[0]-target_pos[0]) < 0.0001:
            small_x = True
        if abs(base_pos[1]-target_pos[1]) < 0.0001:
            small_y = True
        if abs(base_pos[2]-target_pos[2]) < 0.0001:
            small_z = True
            
        if small_x and small_y and small_z:
            continue
            
        if not 'X' in axis_list:
            target_pos[0] = base_pos[0]
        if not 'Y' in axis_list:
            target_pos[1] = base_pos[1]
        if not 'Z' in axis_list:
            target_pos[2] = base_pos[2]
            
        cmds.xform('%s.vtx[%s]' % (new_target, inc), ws = True, t = target_pos)
        
    return new_target
    
def reset_tweak(tweak_node):
    """
    Reset the tweak node in deformation history.
    
    Args:
        tweak_node (str): The name of the tweak node.
    """
    if not cmds.objExists('%s.vlist' % tweak_node):
        return
    
    indices = get_indices('%s.vlist' % tweak_node)
    
    for index in indices:
        try:
            cmds.setAttr('%s.vlist[%s].xVertex' % (tweak_node, index), 0.0)
            cmds.setAttr('%s.vlist[%s].yVertex' % (tweak_node, index), 0.0)
            cmds.setAttr('%s.vlist[%s].zVertex' % (tweak_node, index), 0.0)
        except:
            pass

    return

#--- attributes

def is_attribute(node_dot_attribute):
    """
    Check if what is passed is an attribute.
    
    Return
        bool
    """
    if not cmds.objExists(node_dot_attribute):
        return False
    
    split = node_dot_attribute.split('.')
    
    if len(split) == 1:
        return False
    
    if len(split) > 1 and not split[1]:
        return False
    
    return True
        
def is_attribute_numeric(node_dot_attribute):
    """
    Check if the attribute exists and is numeric.
    
    Return
        bool
    """
    if not is_attribute(node_dot_attribute):
        return False
    
    attr_type = cmds.getAttr(node_dot_attribute, type = True)
    
    numeric_types = ['bool',
                     'float',
                     'double',
                     'long',
                     'short',
                     'doubleLinear',
                     'doubleAngle',
                     'enum']
    
    if attr_type in numeric_types:
        return True
    
def is_translate_rotate_connected(transform):
    """
    Check if translate and rotate attributes are connected.
    
    Args:
        transform (str): The name of a transform.
        
    Return
        bool
    """
    main_attr = ['translate', 'rotate']
    sub_attr = ['X','Y','Z']
    
    for attr in main_attr:
        
        for sub in sub_attr:
            
            name = transform + '.' + attr + sub
            
            input_value = get_attribute_input(name)
            
            if input_value:
                return True
        
    return False

def get_inputs(node, node_only = True):
    """
    Get all the inputs into the specified node.
    
    Args:
        node (str): The name of a node.
        node_only (str): Wether to return the node name or the node name + the attribute eg. 'node_name.attribute'
    
    Return
        list: The inputs.
    """
    
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
    """
    Get all the outputs from the specified node.
        
    Args:
        node (str): The name of a node.
        node_only (str): Wether to return the node name or the node name + the attribute eg. 'node_name.attribute'
    
    Return
        list: The outputs.
    """    
    
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
    """
    Get the input into the specified attribute.
    
    Args:
        node_and_attribute (str): The node_name.attribute name to find an input into.
        node_only (str): Wether to return the node name or the node name + the attribute eg. 'node_name.attribute'
        
    Return
        str: The attribute that inputs into node_and_attribute
    """
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
    """
    Get the outputs from the specified attribute.
    
    Args:
        node_and_attribute (str): The node_name.attribute name to find outputs.
        node_only (str): Wether to return the node name or the node name + the attribute eg. 'node_name.attribute'
        
    Return
        str: The nodes that node_and_attribute connect into.
    """    
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
    """
    Transfer output connections from source_node to target_node.
    
    Args:
        source_node (str): The node to take output connections from.
        target_node (str): The node to transfer output connections to.
    """
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
    """
    Set the override color for the nodes in nodes.
    
    Args:
        nodes (list): A list of nodes to change the override color.
        color (int): The color index to set override color to.
    """
    
    vtool.util.convert_to_sequence(nodes)
    
    for node in nodes:
        
        overrideEnabled = '%s.overrideEnabled' % node
        overrideColor = '%s.overrideColor' % node
        
        if cmds.objExists(overrideEnabled):
            cmds.setAttr(overrideEnabled, 1)
            cmds.setAttr(overrideColor, color)



def hide_attributes(node, attributes):
    """
    Lock and hide the attributes specified in attributes.
    
    Args:
        node (str): The name of a node.
        attributes (list): A list of attributes on node to lock and hide.
    """
    
    for attribute in attributes:
        
        current_attribute = '%s.%s' % (node, attribute)
        
        cmds.setAttr(current_attribute, l = True, k = False)
        
def hide_keyable_attributes(node):
    """
    Lock and hide keyable attributes on node.
    
    Args:
        node (str) The name of a node.
    """
    
    attributes = cmds.listAttr(node, k = True)
        
    hide_attributes(node, attributes)
    
def lock_attributes(node, bool_value = True, attributes = None, hide = False):
    
    if not attributes:
        attributes = cmds.listAttr(node, k = True)
    
    if attributes:
        attributes = vtool.util.convert_to_sequence(attributes)
    
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
    
    attributes = vtool.util.convert_to_sequence(attributes)
    
    if not attributes:
        if only_keyable == False:
            attrs = cmds.listAttr(node, locked = True)
            
        if only_keyable == True:
            attrs = cmds.listAttr(node, locked = True, k = True)
    
    if attributes:
        attrs = attributes
    
    if attrs:
        for attr in attrs:
            cmds.setAttr('%s.%s' % (node, attr), l = False, k = True)

def get_color_of_side(side = 'C', sub_color = False):
    """
    Get the override color for the given side.
    
    Args:
        side (str): 'L','R', 'C'
        sub_color (bool): Wether to return a sub color.
        
    Return
        int: A color index for override color.
    """
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
    """
    Connect an X,Y,Z attribute, eg translate, rotate, scale. 
    
    Args:
        source_transform (str): The name of a transform.
        target_transform (str): The name of a transform.
        attribute (str): eg, translate, rotate, scale.
        connect_type (str): 'plus' or 'multiply'
    
    Return
        list: The nodes created.
    """
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
    """
    Connect translate attributes
    
    Args:
        source_transform (str): The name of a transform.
        target_transform (str): The name of a transform.
    """
    
    connect_vector_attribute(source_transform, target_transform, 'translate')

def connect_rotate(source_transform, target_transform):
    """
    Connect rotate attributes. This will automatically connect rotateOrder from source to target, if not already connected.
    
    Args:
        source_transform (str): The name of a transform.
        target_transform (str): The name of a transform.
    """
    
    connect_vector_attribute(source_transform, target_transform, 'rotate')
    try:
        cmds.connectAttr('%s.rotateOrder' % source_transform, '%s.rotateOrder' % target_transform)
    except:
        pass
        #vtool.util.show('Could not connect %s.rotateOrder into %s.rotateOrder. This could cause issues if rotate order changed.' % (source_transform, target_transform))
        
    
def connect_scale(source_transform, target_transform):
    """
    Connect scale attributes.
    
    Args:
        source_transform (str): The name of a transform.
        target_transform (str): The name of a transform.
    """
    connect_vector_attribute(source_transform, target_transform, 'scale')

def connect_translate_plus(source_transform, target_transform):
    """
    Connect translate attributes. If target_transform already has input connections, reconnect with plusMinusAverage to accomodate both.
    
    Args:
        source_transform (str): The name of a transform.
        target_transform (str): The name of a transform.
        
    Return
        str: the name of the plusMinusAverage node.
    """
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
    
def connect_translate_multiply(source_transform, target_transform, value = 1, respect_value = False):
    """
    Connect translate attributes with a multiplyDivide to multiply the effect.
    
    Args:
        source_transform (str): The name of a transform.
        target_transform (str): The name of a transform.
        value (float): The multiply value. Set to 0.5 to translate target half of what source translates.
        repsect_value (bool): If respect value is True, then add a plus minus average to buffer the multiply divide.
        
    Return
        str: the name of the multiplyDivide node. If respect value return [multiply, plus]
    """
    
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
            indices = indices[-1]
            
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


def connect_rotate_multiply(source_transform, target_transform, value = 1, respect_value = False):
    """
    Connect rotate attributes with a multiplyDivide to multiply the effect.
    This is dangerous because rotate is not calculated in the same linear way as translate. 
    Probably shouldn't be used because of Quaternion math. Would be better to use a double orient constraint.
    
    Args:
        source_transform (str): The name of a transform.
        target_transform (str): The name of a transform.
        value (float): The multiply value. Set to 0.5 to rotate target half of what source translates.
        repsect_value (bool): If respect value is True, then add a plus minus average to buffer the multiply divide.
        
    Return
        str: the name of the multiplyDivide node. If respect value return [multiply, plus]
    """
    
    target_transform_x = '%s.rotateX' % target_transform
    target_transform_y = '%s.rotateY' % target_transform
    target_transform_z = '%s.rotateZ' % target_transform
    
    target_input_x = get_attribute_input(target_transform_x)
    target_input_y = get_attribute_input(target_transform_y)
    target_input_z = get_attribute_input(target_transform_z)
    
    if target_input_x:
        
        if cmds.nodeType(target_input_x) == 'plusMinusAverage':
            plus = target_input_x.split('.')[0]
            indices = get_indices('%s.input3D' % plus)
            indices = indices[-1]
            
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
    
    multiply = connect_multiply('%s.rotateX' % source_transform, target_transform_x, value, plus = False)

    if respect_value:
            plus = cmds.createNode('plusMinusAverage', n = 'plus_%s' % target_transform)
    
            value_x = cmds.getAttr('%s.rotateX' % source_transform)
            value_y = cmds.getAttr('%s.rotateY' % source_transform)
            value_z = cmds.getAttr('%s.rotateZ' % source_transform)
    
            cmds.connectAttr('%s.rotateX' % source_transform, '%s.input3D[0].input3Dx' % plus)
            cmds.connectAttr('%s.rotateY' % source_transform, '%s.input3D[0].input3Dy' % plus)
            cmds.connectAttr('%s.rotateZ' % source_transform, '%s.input3D[0].input3Dz' % plus)
    
            cmds.setAttr('%s.input3D[1].input3Dx' % plus, -1*value_x)
            cmds.setAttr('%s.input3D[1].input3Dy' % plus, -1*value_y)
            cmds.setAttr('%s.input3D[1].input3Dz' % plus, -1*value_z)

            disconnect_attribute('%s.input1X' % multiply)
    
            cmds.connectAttr('%s.output3Dx' % plus, '%s.input1X' % multiply)
            cmds.connectAttr('%s.output3Dy' % plus, '%s.input1Y' % multiply)
            cmds.connectAttr('%s.output3Dz' % plus, '%s.input1Z' % multiply)
    
    if not respect_value:
        cmds.connectAttr('%s.rotateY' % source_transform, '%s.input1Y' % multiply)
        cmds.connectAttr('%s.rotateZ' % source_transform, '%s.input1Z' % multiply)
                
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
    
def connect_scale_multiply(source_transform, target_transform, value = 1, respect_value = False):
    """
    Never use. 
    """
    target_transform_x = '%s.scaleX' % target_transform
    target_transform_y = '%s.scaleY' % target_transform
    target_transform_z = '%s.scaleZ' % target_transform
    
    target_input_x = get_attribute_input(target_transform_x)
    target_input_y = get_attribute_input(target_transform_y)
    target_input_z = get_attribute_input(target_transform_z)
    
    if target_input_x:
        
        if cmds.nodeType(target_input_x) == 'plusMinusAverage':
            plus = target_input_x.split('.')[0]
            indices = get_indices('%s.input3D' % plus)
            indices = indices[-1]
            
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
    
    multiply = connect_multiply('%s.scaleX' % source_transform, target_transform_x, value, plus = False)

    if respect_value:
            plus = cmds.createNode('plusMinusAverage', n = 'plus_%s' % target_transform)
    
            value_x = cmds.getAttr('%s.scaleX' % source_transform)
            value_y = cmds.getAttr('%s.scaleY' % source_transform)
            value_z = cmds.getAttr('%s.scaleZ' % source_transform)
    
            cmds.connectAttr('%s.scaleX' % source_transform, '%s.input3D[0].input3Dx' % plus)
            cmds.connectAttr('%s.scaleY' % source_transform, '%s.input3D[0].input3Dy' % plus)
            cmds.connectAttr('%s.scaleZ' % source_transform, '%s.input3D[0].input3Dz' % plus)
    
            cmds.setAttr('%s.input3D[1].input3Dx' % plus, -1*value_x)
            cmds.setAttr('%s.input3D[1].input3Dy' % plus, -1*value_y)
            cmds.setAttr('%s.input3D[1].input3Dz' % plus, -1*value_z)

            disconnect_attribute('%s.input1X' % multiply)
    
            cmds.connectAttr('%s.output3Dx' % plus, '%s.input1X' % multiply)
            cmds.connectAttr('%s.output3Dy' % plus, '%s.input1Y' % multiply)
            cmds.connectAttr('%s.output3Dz' % plus, '%s.input1Z' % multiply)
    
    if not respect_value:
        cmds.connectAttr('%s.scaleY' % source_transform, '%s.input1Y' % multiply)
        cmds.connectAttr('%s.scaleZ' % source_transform, '%s.input1Z' % multiply)
                
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
    """
    Connect the visibility into an attribute
    
    Args:
        attribute_name (str): The node.attribute name of an attribute. Does not have to exists. Will be created if doesn't exist.
        target_node (str): The target node to connect attribute_name into.
        value (bool): 0 or 1 whether you want the visibility on or off by default.
    """
    nodes = vtool.util.convert_to_sequence(target_node)
    
    if not cmds.objExists(attribute_name):
        split_name = attribute_name.split('.')
        cmds.addAttr(split_name[0], ln = split_name[1], at = 'bool', dv = value,k = True)
        
    for thing in nodes: 
        
        if not cmds.isConnected(attribute_name, '%s.visibility' % thing):
            cmds.connectAttr(attribute_name, '%s.visibility' % thing)
        if cmds.isConnected(attribute_name, '%s.visibility' % thing):
            vtool.util.warning( attribute_name + ' and ' + thing + '.visibility are already connected')

def connect_plus(source_attribute, target_attribute, respect_value = False):
    """
    Connect source_attribute into target_attribute with a plusMinusAverage inbetween.
    
    Args:
        source_attribute (str): The node.attribute name of an attribute.
        target_attribute (str): The node.attribute name of an attribute.
        respect_value (bool): Wether to edit the input1D list to accomodate for values in the target attribute.
        
    Return
        str: The name of the plusMinusAverage node
    """
    
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
    """
    Not in use. Connect source_attribute into target_attribute with a plusMinusAverage inbetween.
    Tried to make it better, but isn't.
    
    Args:
        source_attribute (str): The node.attribute name of an attribute.
        target_attribute (str): The node.attribute name of an attribute.
        respect_value (bool): Wether to edit the input1D list to accomodate for values in the target attribute.
        
    Return
        str: The name of the plusMinusAverage node
    """
    
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
    """
    Connect source_attribute into target_attribute with a multiplyDivide inbetween.
    
    Args:
        source_attribute (str): The node.attribute name of an attribute.
        target_attribute (str): The node.attribute name of an attribute.
        skip_attach (bool): Wether to attach the input into target_attribute (if there is one) into input2X of multiplyDivide.
        plus (bool): Wether to fix input connections in target_attribute to plug into a plusMinusAverage. Therefore not losing their influence on the attribute while still multiplying by the source_attribute.
        
    Return
        str: The name of the plusMinusAverage node
    """
    input_attribute = get_attribute_input( target_attribute  )

    lock_state = LockState(target_attribute)
    lock_state.unlock()

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
    
    lock_state.restore_initial()
    
    return multi

def insert_multiply(target_attribute, value = 0.1):
    """
    Insert a multiply divide into the input attribute of target_attribute.
    
    Args:
        target_attribute (str): The node.attribute name of an attribute.
        value (float): The float value to multiply the target_attribute by.
        
    Return
        str: The new multiply divide.
    """
    
    new_name = target_attribute.replace('.', '_')
    new_name = new_name.replace('[', '_')
    new_name = new_name.replace(']', '_')
    
    input_attr = get_attribute_input(target_attribute)
    
    multi = cmds.createNode('multiplyDivide', n = 'multiplyDivide_%s' % new_name) 
    
    if input_attr:
        disconnect_attribute(target_attribute)
        cmds.connectAttr(input_attr, '%s.input1X' % multi)
        
    cmds.connectAttr('%s.outputX' % multi, target_attribute)
    
    cmds.setAttr('%s.input2X' % multi, value)
    
    return multi

def connect_blend(source_attribute1, source_attribute2, target_attribute, value = 0.5 ):
    """
    Connect source 1 and source 2 into the target_attribute with and blendColors node.
    
    Args:
        source_attribute1 (str): The node.attribute name of an attribute.
        source_attribute2 (str): The node.attribute name of an attribute.
        target_attribute (str): The node.attribute name of an attribute.
        value (float): The amount to blend the 2 attributes.
        
    Return
        str: The name of the blendColors node
    """
    blend = cmds.createNode('blendColors', n = 'blendColors_%s' % source_attribute1)
    
    cmds.connectAttr(source_attribute1, '%s.color1R' % blend)
    cmds.connectAttr(source_attribute2, '%s.color2R' % blend)
    
    connect_plus('%s.outputR' % blend, target_attribute)
    
    cmds.setAttr('%s.blender' % blend, value)
    
    return blend

def connect_reverse(source_attribute, target_attribute):
    """
    Connect source_attribute into target_attribute with a reverse node inbetween.
    
    Args:
        source_attribute (str): The node.attribute name of an attribute.
        target_attribute (str): The node.attribute name of an attribute.
        
    Return
        str: The name of the reverse node
    """
    reverse = cmds.createNode('reverse', n = 'reverse_%s' % source_attribute)
    
    cmds.connectAttr(source_attribute, '%s.inputX' % reverse)
    connect_plus('%s.outputX' % reverse, target_attribute)
    
    return reverse

def connect_equal_condition(source_attribute, target_attribute, equal_value):
    """
    Connect source_attribute into target_attribute with a condition node inbetween.
    
    Args:
        source_attribute (str): The node.attribute name of an attribute.
        target_attribute (str): The node.attribute name of an attribute.
        equal_value (float): The value the condition should be equal to, in order to pass 1. 0 otherwise.
        Good when hooking up enums to visibility.
        
    Return
        str: The name of the condition node
    """
    condition = cmds.createNode('condition', n = 'condition_%s' % source_attribute)
    
    cmds.connectAttr(source_attribute, '%s.firstTerm' % condition)
    cmds.setAttr('%s.secondTerm' % condition, equal_value)
    
    cmds.setAttr('%s.colorIfTrueR' % condition, 1)
    cmds.setAttr('%s.colorIfFalseR' % condition, 0)
    
    connect_plus('%s.outColorR' % condition, target_attribute)
    
    return condition
        
def connect_message( input_node, destination_node, attribute ):
    """
    Connect the message attribute of input_node into a custom message attribute on destination_node
    
    Args:
        input_node (str): The name of a node.
        destination_node (str): The name of a node.
        attribute (str): The name of the message attribute to create and connect into. If already exists than just connect. 
        
    """
    if not input_node or not cmds.objExists(input_node):
        vtool.util.warning('No input node to connect message.')
        return
        
    if not cmds.objExists('%s.%s' % (destination_node, attribute)):  
        cmds.addAttr(destination_node, ln = attribute, at = 'message' )
        
    if not cmds.isConnected('%s.message' % input_node, '%s.%s' % (destination_node, attribute)):
        cmds.connectAttr('%s.message' % input_node, '%s.%s' % (destination_node, attribute))
    
            
def disconnect_attribute(attribute):
    """
    Disconnect an attribute.  Find its input automatically and disconnect it.
    
    Args:
        attribute (str): The name of an attribute that has a connection.
    """
    connection = get_attribute_input(attribute)
    
    if connection:
        
        cmds.disconnectAttr(connection, attribute)

def get_indices(attribute):
    """
    Get the index values of a multi attribute.
    
    Args:
        attribute (str): The node.attribute name of a multi attribute. Eg. blendShape1.inputTarget
        
    Return
        list: A list of integers that correspond to multi attribute indices.
    """
    
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

def get_slots(attribute):
    """
    attributes!!!
    Given a multi attribute, get all the slots currently made.
    
    Args:
        attribute (str): The node.attribute name of a multi attribute. Eg. blendShape1.inputTarget 
    
    Return
        list: The index of slots that are open.  Indices are returned as str(int)
    """
    slots = cmds.listAttr(attribute, multi = True)
        
    found_slots = []
    
    for slot in slots:
        index = re.findall('\d+', slot)
        
        if index:
            found_slots.append(index[-1])
            
    return found_slots

def get_slot_count(attribute):
    """
    attributes!!!
    Get the number of created slots in a multi attribute.
    
    Args:
        attribute (str): The node.attribute name of a multi attribute. Eg. blendShape1.inputTarget
        
    Return
        int: The number of open slots in the multi attribute
    """
    
    slots = get_slots(attribute)
    
    if not slots:
        return 0
    
    return len(slots)

def get_available_slot(attribute):
    """
    attributes!!!
    Find the next available slot in a multi attribute.
    
    Args:
        attribute (str): The node.attribute name of a multi attribute. Eg. blendShape1.inputTarget
        
    Return
        int: The next empty slot.
    """
    slots = get_slots(attribute)
    
    if not slots:
        return 0
    
    return int( slots[-1] )+1

def create_title(node, name):
    """
    Create a enum title attribute on node
    
    Args:
        node (str): The name of a node
        name (str): The title name.
    """
    title = MayaEnumVariable(name)
    title.create(node)
      
def zero_xform_channels(transform):
    """
    Zero out the translate and rotate. Set scale to 1.
    
    Args:
        transform (str): The name of a transform node.
    """
    
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
    
    return

#---Rig

def create_attribute_lag(source, attribute, targets):
    """
    Add lag to the targets based on a source attribute. A lag attribute will also be added to source to turn the effect on and off. 
    If you are animating the rotation of a control inputs are as follows:
    
    create_attribute_lag( 'CNT_FIN_1_L', 'rotateY', ['driver_CNT_FIN_2_L, 'driver_CNT_FIN_3_L', 'driver_CNT_FIN_4_L'] )
    
    Args:
        source (str): The node where the attribute lives. Also a lag attribute will be created here.
        attribute (str): The attribute to lag. Sometimes can be rotateX, rotateY or rotateZ.
        targets (list): A list of targets to connect the lag into. The attribute arg will be used as the attribute to connect into on each target.
    """
    
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
    """
    Given a list of transforms, create a spread attribute which will cause them to rotate apart.
    
    Args:
        control (str): The name of a control where the spread attribute should be created.
        transforms (list): A list of transforms that should spread apart by rotation.
        name (str): The name of the attribute to create.
        axis (str): Can be 'X','Y','Z'
        invert (bool): Wether to invert the spread behavior so it can mirror.
        create_driver (bool): Wether to create a driver group above the transform.
    """
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
    """
    Given a list of transforms, create a spread attribute which will cause them to translate apart.
    This is good for fingers that are rigged with ik handles.
    
    Args:
        control (str): The name of a control where the spread attribute should be created.
        transforms (list): A list of transforms that should spread apart by translation.
        name (str): The name of the attribute to create.
        axis (str): Can be 'X','Y','Z'
        invert (bool): Wether to invert the spread behavior so it can mirror.
    """
    
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
    """
    Create an offset where target_transforms lag behind the attribute.
    """
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





def get_controls():
    """
    Get the controls in a scene.
    
    It follows these rules
    
    First check if a transform starts with CNT_
    Second check if a transform has a an attribute named control.
    Third check if a transform has an attribute named tag and is a nurbsCurve, and that tag has a value.
    Fourth check if a transform has an attribute called curveType.
    
    If it matches any of these conditions it is considered a control.
    
    Return
        list: List of control names.
    """
    transforms = cmds.ls(type = 'transform')
    joints = cmds.ls(type = 'joint')
    
    if joints:
        transforms += joints
    
    found = []
    found_with_value = []
    
    for transform in transforms:
        if transform.startswith('CNT_'):
            found.append(transform)
            continue
                
        if cmds.objExists('%s.control' % transform):
            found.append(transform)
            continue
        
        if cmds.objExists('%s.tag' % transform):
            
            if has_shape_of_type(transform, 'nurbsCurve'):
                
                
                found.append(transform)
                value = cmds.getAttr('%s.tag' % transform)
                
                if value:
                    found_with_value.append(transform)
            
            continue
        
        if cmds.objExists('%s.curveType' % transform):
            found.append(transform)
            continue
    
    if found_with_value:
        found = found_with_value
        
    return found
    
@undo_chunk
def mirror_control(control):
    """
    Find the right side control of a left side control, and mirror the control cvs.
    
    It follows these rules:
    It will only match if the corresponding right side name exists.
    
    Replace _L with _R at the end of a control name.
    Replace L_ with R_ at the start of a control name.
    Replace lf with rt inside the control name
    """
    if not control:
        return
    
    shapes = get_shapes(control)
    
    if not shapes:
        return
    
    shape = shapes[0]
    
    if not cmds.objExists('%s.cc' % shape):
        return
    
    other_control = None
    
    if control.endswith('_L') or control.endswith('_R'):
                
        if control.endswith('_L'):
            other_control = control[0:-2] + '_R'
            
        if control.endswith('_R'):
            other_control = control[0:-2] + '_L'
            
    if not other_control:
        if control.startswith('L_'):
            other_control = 'R_' + control[2:]
            
        if control.startswith('R_'):
            other_control = 'L_' + control[2:]
         
    if not other_control:
                
        if control.find('lf') > -1 or control.find('rt') > -1:
            
            if control.find('lf') > -1:
                other_control = control.replace('lf', 'rt')
                
            if control.find('rt') > -1:
                other_control = control.replace('rt', 'lf') 
           
    if not other_control or not cmds.objExists(other_control):
        return
                    
    other_shapes = get_shapes(other_control)
    if not other_shapes:
        return
    
    for inc in range(0,len(shapes)):
        shape = shapes[inc]
        other_shape = other_shapes[inc]
        
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
            
    return other_control

@undo_chunk
def mirror_controls():
    """
    Mirror cv positions of all controls in the scene. 
    See get_controls() and mirror_control() for rules. 
    """
    selection = cmds.ls(sl = True)
    
    controls = get_controls()
    
    found = []
    
    if selection:
        for selection in selection:
            if selection in controls:
                found.append(selection)
    
    if not selection or not found:
        found = controls
    
    mirrored_controls = []
    
    for control in found:
        
        if control in mirrored_controls:
            continue
        
        other_control = mirror_control(control)
        
        mirrored_controls.append(other_control)
        

def mirror_curve(prefix):
    """
    Mirror curves in a scene if the end in _L and _R
    """
    
    curves = cmds.ls('%s*' % prefix, type = 'transform')
    
    if not curves:
        return
    
    for curve in curves:
        other_curve = None
        
        if curve.endswith('_L'):
            other_curve = curve[:-1] + 'R'
        
        cvs = cmds.ls('%s.cv[*]' % curve, flatten = True)
            
        if not other_curve:
            
            cv_count = len(cvs)
            
            for inc in range(0, cv_count):
                
                cv = '%s.cv[%s]' % (curve, inc)
                other_cv = '%s.cv[%s]' % (curve, cv_count-(inc+1))
                
                position = cmds.xform(cv, q = True, ws = True, t = True)
                
                new_position = list(position)
                
                new_position[0] = position[0] * -1
                
                cmds.xform(other_cv, ws = True, t = new_position)
                
                if inc == cv_count:
                    break
        
        if other_curve:
        
            other_cvs = cmds.ls('%s.cv[*]' % other_curve, flatten = True)
            
            if len(cvs) != len(other_cvs):
                continue
            
            for inc in range(0, len(cvs)):
                
                position = cmds.xform(cvs[inc], q = True, ws = True, t = True)
                
                new_position = list(position)
                
                new_position[0] = position[0] * -1
                
                
                
                cmds.xform(other_cvs[inc], ws = True, t = new_position)
    
def process_joint_weight_to_parent(mesh):
    """
    Sometimes joints have a sub joint added to help hold weighting and help with heat weighting.
    This will do it for all joints with name matching process_ at the beginning on the mesh arg that is skinned. 
    
    Args:
        mesh (str): A mesh skinned to process joints.
    """
    scope = cmds.ls('process_*', type = 'joint')
    
    
    progress = ProgressBar('process to parent %s' % mesh, len(scope))
    
    for joint in scope:
        progress.status('process to parent %s: %s' % (mesh, joint))
        
        transfer_weight_from_joint_to_parent(joint, mesh)
        
        progress.inc()
        
        if vtool.util.break_signaled():
            break
        
        if progress.break_signaled():
            break
        
    progress.end()
    
    cmds.delete(scope)

@undo_chunk
def joint_axis_visibility(bool_value):
    """
    Show/hide the axis orientation of each joint.
    """
    joints = cmds.ls(type = 'joint')
    
    for joint in joints:
        
        cmds.setAttr('%s.displayLocalAxis' % joint, bool_value)

def hook_ik_fk(control, joint, groups, attribute = 'ikFk'): 
    """
    Convenience for hooking up ik fk.
    
    Args:
        control (str): The name of the control where the attribute arg should be created.
        joint (str): The joint with the switch attribute. When adding multiple rigs to one joint chain, the first joint will have a switch attribute added.
        groups (list): The ik control group name and the fk control group name.
        attribute (str): The name to give the attribute on the control. Usually 'ikFk'
    """
    if not cmds.objExists('%s.%s' % (control, attribute)): 
        cmds.addAttr(control, ln = attribute, min = 0, max = 1, dv = 0, k = True) 
      
    attribute_ikfk = '%s.%s' % (control, attribute) 
      
    cmds.connectAttr(attribute_ikfk, '%s.switch' % joint) 
      
    for inc in range(0, len(groups)): 
        connect_equal_condition(attribute_ikfk, '%s.visibility' % groups[inc], inc) 

            
       
def fix_fade(target_curve, follow_fade_multiplies):
    """
    This fixes multiplyDivides so that they will multiply by a value that has them match the curve when they move.
    
    For example if eye_lid_locator is multiplyDivided in translate to move with CNT_EYELID. 
    Pass its multiplyDivide node to this function with a curve that matches the btm eye lid.
    The function will find the amount the multiplyDivide.input2X needs to move, 
    so that when CNT_EYELID moves on Y it will match the curvature of target_curve.
    
    Args:
        target_curve (str): The name of the curve to match to.
        follow_fade_multiplies (str): A list of a multiplyDivides.
    """
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
  



#--- Nucleus

def create_nucleus(name = None):
    """
    Create a nucleus node.
    
    Args:
        name (str): The description for the nucleus. Final name = 'nucleus_(name)'. If no name given, name = 'nucleus'.
    
    Return 
        str: name of the nucleus.
    """
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
    """
    Create a hair system.  
    
    Args:
        name (str): The description for the hair system. Final name = 'hairSystem_(name)'. If no name given, name = 'hairSystem'.  
        nucleus (str): The name of a nucleus node to attach to the hairSystem.
        
    Return
        list: [hair system, hair system shape] 
    """
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
    """
    Connect a hair system to a nucleus.
    
    Args:
        hair_system (str): The name of a hair system.
        nucleus (str): The name of a nucleus node.
    """
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
    """
    Create a follicle.
    
    Args: 
        name (str): The description for the hair system. Final name = 'follicle_(name)'. If no name given, name = 'follicle'.
        hair_system (str): The name of a hair system to connect to.
        
    Return
        list: [follicle name, follicle shape name]
    """
    
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
    """
    Connect a follicle to a hair system
    
    Args:
        follicle (str): The name of a follicle.
        hair_system (str): The name of a hair system.
    """
    
    
    indices = get_indices('%s.inputHair' % hair_system)
    
    if indices:
        current_index = indices[-1] + 1
    
    if not indices:
        current_index = 0
    
    cmds.connectAttr('%s.outHair' % follicle, '%s.inputHair[%s]' % (hair_system, current_index))
    indices = get_indices('%s.inputHair' % hair_system)
    
    cmds.connectAttr('%s.outputHair[%s]' % (hair_system, current_index), '%s.currentPosition' % follicle)
    
    cmds.refresh()
    
def add_follicle_to_curve(curve, hair_system = None, switch_control = None, attribute_name = 'dynamic'):
    """
    Add a follicle to a curve. Good for attaching to a spline ik, to make it dynamic.
    It will make a duplicate of the curve so that the dynamics of the follicle can be switched on/off.
    
    Args:
        curve (str): The name of a curve.
        hair_system(str): The name of a hair system, that the created follicle should attach to.
        switch_control (str): The name of the control to add the switch attribute to.
        attribute_name (str): The name of the attribute on switch_control.
        
    Return
        str: The name of the follicle.
        
    """
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
    
    if outputs:
        for output in outputs:
            cmds.connectAttr('%s.worldSpace' % blend_curve, output, f = True)
    
    if parent:
        cmds.parent(follicle, parent)
    
    if switch_control:
        
        blendshape_node = cmds.blendShape(curve, new_curve, blend_curve, w = [0,1],n = 'blendShape_%s' % follicle)[0]
        
        if not cmds.objExists('%s.%s' % (switch_control, attribute_name)):
            
            variable = MayaNumberVariable(attribute_name)
            variable.set_variable_type(variable.TYPE_DOUBLE)
            variable.set_node(switch_control)
            variable.set_min_value(0)
            variable.set_max_value(1)
            variable.set_keyable(True)
            variable.create()
        
        remap = RemapAttributesToAttribute(switch_control, attribute_name)
        remap.create_attributes(blendshape_node, [curve, new_curve])
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
    """
    Make mesh into a passive collider.
    
    Args:
        mesh (str)
        
    Return
        list: List of nodes in the passive collider.
    """
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
    
    deform_mesh_orig = deform_mesh
    deform_mesh = prefix_hierarchy(deform_mesh, 'deform')[0]
    
    clothwrap = cmds.rename(clothwrap, deform_mesh)
    
    clothwrap = prefix_hierarchy(clothwrap, 'clothwrap')[0]    

    final = cmds.rename(final, deform_mesh_orig)

    deform_mesh = deform_mesh.split('|')[-1]
    clothwrap = clothwrap.split('|')[-1]
    
    create_wrap(deform_mesh, cloth_mesh)
    create_wrap(cloth_mesh, clothwrap)
    
    blend = cmds.blendShape(deform_mesh, clothwrap, final, w = [0,1], n = 'blendShape_nClothFinal')[0]
    
    connect_equal_condition(attribute, '%s.%s' % (blend, deform_mesh), 0)
    connect_equal_condition(attribute, '%s.%s' % (blend, clothwrap), 1)
    
    cmds.parent(deform_mesh , clothwrap, parent )
    
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
            
