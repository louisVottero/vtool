# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

import os
import string

import traceback
from functools import wraps

import vtool.util
import vtool.util_file

import api

in_maya = vtool.util.is_in_maya()

if in_maya:

    import maya.cmds as cmds
    import maya.mel as mel
    import maya.OpenMaya as OpenMaya
    import maya.OpenMayaUI as OpenMayaUI
    
undo_chunk_active = False
current_progress_bar = None
    
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
    This class is intended to find a name that doesn't clash with other names in the Maya scene.
    It will increment the last number in the name. 
    If no number is found it will append a 1 to the end of the name.
    """
    
    def __init__(self, test_string):
        super(FindUniqueName, self).__init__(test_string)
        
        self.work_on_last_number = True
    
    def _get_scope_list(self):
        
        
        if cmds.namespace(exists = self.increment_string):
            return [self.increment_string]
        
        if cmds.objExists(self.increment_string):
            return [self.increment_string]
        
        if not cmds.objExists(self.increment_string):
            if not cmds.namespace(exists = self.increment_string):
                return []
        
        
    
    def _format_string(self, number):
        
        if number == 0:
            number = 1
            self.increment_string = '%s_%s' % (self.test_string, number)
        
        if number > 1:
            if self.work_on_last_number:
                self.increment_string = vtool.util.increment_last_number(self.increment_string)
            if not self.work_on_last_number:
                self.increment_string = vtool.util.increment_first_number(self.increment_string)
    
    def _get_number(self):
        
        if self.work_on_last_number:
            number = vtool.util.get_last_number(self.test_string)
        if not self.work_on_last_number:
            number = vtool.util.get_first_number(self.test_string) 
        
        if number == None:
            return 0
        
        return number
    
    def get_last_number(self, bool_value):
        self.work_on_last_number = bool_value

class TrackNodes(object):
    """
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
            
        Returns:
            None
        """
        self.node_type = node_type
        
        if self.node_type:
            self.nodes = cmds.ls(type = node_type, l = True)
        if not self.node_type:
            self.nodes = cmds.ls(l = True)
        
    def get_delta(self):
        """
        Get the new nodes in the Maya scene created after load() was executed.
        The load() node_type variable is stored in the class and used when getting the delta.
            
        Returns:
            list: list of new nodes.
        """
        if self.node_type:
            current_nodes = cmds.ls(type = self.node_type, l = True)
        if not self.node_type:
            current_nodes = cmds.ls(l = True)
            
            
        #new_set = set(self.nodes).difference(current_nodes)            
        new_set = set(current_nodes).difference(self.nodes)
        
        return list(new_set)
       
class ProgressBar(object):
    """
    Manipulate the maya progress bar.
    
    Args:
        title (str): The name of the progress bar.
        count (int): The number of items to iterate in the progress bar.
    """
    
    inc_value = 0
    
    def __init__(self, title = '', count = None, begin = True):
        
        self.progress_ui = None
        self._orig_tool_context = None
        
        if is_batch():
            self.title = title
            self.count = count
            
            message = '%s count: %s' % (title, count)
            self.status_string = ''
            vtool.util.show(message)
            return
        
        if not is_batch():
            
            
            self.progress_ui = get_progress_bar()
                  
            if begin: 
                #check if not cancelled completely because of bug
                self.__class__.inc_value = 0
                self.end()
                
                
            if not title:
                title = cmds.progressBar(self.progress_ui, q = True, status  = True)
            
            if not count:
                count = cmds.progressBar( self.progress_ui, q = True, maxValue = True)
             
            cmds.progressBar( self.progress_ui,
                                    edit=True,
                                    beginProgress=begin,
                                    isInterruptable=True,
                                    status = title,
                                    maxValue= count )
            
            
        self._orig_tool_context = get_tool()
        set_tool_to_select()    
        
        global current_progress_bar 
        current_progress_bar = self
        
    
    def set_count(self, int_value):
        if self.progress_ui:
            cmds.progressBar( self.progress_ui, edit = True, maxValue = int_value )
        else:
            self.count = int_value
    
    def get_count(self):
        if self.progress_ui:
            return cmds.progressBar( self.progress_ui, q = True, maxValue = True)
        else:
            return self.count
        
    def get_current_inc(self):
        return self.__class__.inc_value
        #return cmds.progressBar( self.progress_ui, q = True, step = True)
        
    def inc(self, inc = 1):
        """
        Set the current increment.
        """
        if is_batch():
            return
        
        self.__class__.inc_value += inc
        
        cmds.progressBar(self.progress_ui, edit=True, step=inc)
        
    
    def next(self):
        
        if is_batch():
            return
        
        self.__class__.inc_value += 1
        
        cmds.progressBar(self.progress_ui, edit=True, step=1)
        
            
    def end(self):
        """
        End the progress bar.
        """
        
        if is_batch():
            return
        
        if cmds.progressBar(self.progress_ui, query = True, isCancelled = True):
            cmds.progressBar( self.progress_ui,
                                        edit=True,
                                        beginProgress=True)
        
        cmds.progressBar(self.progress_ui, edit=True, ep = True)
        if self._orig_tool_context:
            set_tool(self._orig_tool_context)        
        
    def status(self, status_string):
        """
        Set that status string of the progress bar.
        """
        if is_batch():
            self.status_string = status_string
            #vtool.util.show(status_string)
            return
        
        cmds.progressBar(self.progress_ui, edit=True, status = status_string)
        
    def break_signaled(self):
        """
        break the progress bar loop so that it stops and disappears.
        """
        
        run = eval(vtool.util.get_env('VETALA_RUN'))
        stop = eval(vtool.util.get_env('VETALA_STOP'))
        
        if is_batch():
            return False
        
        if run == True:
            
            if stop == True:
                vtool.util.show('VETALA_STOP is True')
                self.end()
                return True
        
        break_progress = cmds.progressBar(self.progress_ui, query=True, isCancelled=True )
        
        if break_progress:
            self.end()
            
            if run == True:
                vtool.util.set_env('VETALA_STOP', True)            
            return True
        
        return False
    
def get_current_camera():
    camera = api.get_current_camera()
    
    return camera

def set_current_camera(camera_name):
    api.set_current_camera(camera_name)

class StoreDisplaySettings(object):
    
    def __init__(self):
        
        self.style = None
        self.setting_id = None
        self.view = OpenMayaUI.M3dView.active3dView()
    
    def store(self):
        
        self.setting_id = self.view.objectDisplay()
        self.style = self.view.displayStyle()
        
    def restore(self):
        
        self.view.setObjectDisplay(self.setting_id)
        self.view.setDisplayStyle(self.style)

class ManageNodeEditors():
    
    def __init__(self):
        
        node_editors = get_node_editors()
        
        self.node_editors = node_editors
        
        self._additive_state_dict = {}
        
        for editor in self.node_editors:
            current_value = cmds.nodeEditor(editor, q = True, ann = True)
            self._additive_state_dict[editor] = current_value
            
    def turn_off_add_new_nodes(self):
        
        for editor in self.node_editors:
            cmds.nodeEditor(editor, e = True, ann = False)
            
    def restore_add_new_nodes(self):
        
        for editor in self.node_editors:
            if editor in self._additive_state_dict:
                cmds.nodeEditor(editor, e = True, ann = self._additive_state_dict[editor])


             
def undo_off(function):
    @wraps(function)
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
                    
                # do not remove
                vtool.util.error( traceback.format_exc() )
            
            if current_progress_bar:
                current_progress_bar.end()
                current_progress_bar = None
                
            raise(RuntimeError)
        

        
        if undo_state:          
            cmds.undoInfo( state = True )
        
        return return_value
        
    return wrapper

def undo_chunk(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        
        
        
        global undo_chunk_active
        global current_progress_bar
        
        if not in_maya:
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
            
                # do not remove
                vtool.util.error( traceback.format_exc() )

            if current_progress_bar:
                current_progress_bar.end()
                current_progress_bar = None
            
            raise(RuntimeError)


            
        if not closed:
            if undo_chunk_active:
                cmds.undoInfo(closeChunk = True)
                
                undo_chunk_active = False

        
        return return_value
                     
    return wrapper

def viewport_off( function ):

    @wraps(function)
    def wrap( *args, **kwargs ):
        if not in_maya:
            return
        if not cmds.ogs(q = True, pause = True):
            cmds.ogs(pause = True)
        try:
            return function( *args, **kwargs )
        except Exception:
            raise
        finally:
            if cmds.ogs(q = True, pause = True):
                cmds.ogs(pause = True)
 
    return wrap

def is_batch():
    """
    Returns: 
        bool: True if Maya is in batch mode.
    """
    
    
    return cmds.about(batch = True)

def is_transform(node):
    """
    Is the node a transform.
    
    Args:
        node (str): The name of the node to test.
    
    Returns:
        bool
    """
    
    if not cmds.objExists(node):
        return False
    
    if cmds.objectType(node, isAType = 'transform'):
        return True
    
    return False

def is_a_shape(node):
    """
    Test whether the node is a shape.
    
    Args:
        node (str): The name of a node.
        
    Returns:
        bool
    """
    if cmds.objectType(node, isAType = 'shape'):
        return True
    
    return False
    
def is_referenced(node):
    """
    Args:
        node (str): Name of a node in maya. Check to see if it is referenced.
        
    Returns:
        bool
    """
    
    if not node:
        return False
    
    if not cmds.objExists(node):
        return False
    
    is_node_referenced = cmds.referenceQuery(node, isNodeReferenced = True)
    
    return is_node_referenced

def is_empty(node):

    if is_referenced(node):
        return False

    if is_transform(node):
        relatives = cmds.listRelatives(node)
        
        if relatives:
            return False
    
    attrs = cmds.listAttr(node, ud = True, k = True)
    
    if attrs:
        return False
    
    default_nodes = ['defaultLightSet', 'defaultObjectSet', 'initialShadingGroup', 'uiConfigurationScriptNode', 'sceneConfigurationScriptNode']
    if node in default_nodes:
        return False
    
    connections = cmds.listConnections(node)
    
    if connections != ['defaultRenderGlobals']:
    
        if connections:
            return False
    
    
    
    
    
    return True

def is_undeletable(node):
    
    try: #might fail in earlier versions of maya
        nodes = cmds.ls(undeletable = True)
        
        if node in nodes:
            return True
    except:
        return False
    
        
        
    return False

def is_unique(name):
    
    scope = cmds.ls(name)
    
    count = len(scope)
    
    if count > 1:
        return False
    
    if count == 1:
        return True
    
    return True

def is_namespace(namespace):
    
    if cmds.namespace(exists = namespace):
        return True
    
    return False

def inc_name(name, inc_last_number = True):
    """
    Finds a unique name by adding a number to the end.
    
    Args:
        name (str): Name to start from. 
    
    Returns:
        str: Modified name, number added if not unique..
    """
    
    if not cmds.objExists(name) and not cmds.namespace(exists = name):
        return name
    
    unique = FindUniqueName(name)
    unique.get_last_number(inc_last_number)
    return unique.get()


def prefix_name(node, prefix, name, separator = '_'):
    """
    Convenience to quickly rename a Maya node.
    
    Args:
        node (str): Name of a node in maya to rename.
        prefix (str)
        name (str)
        separator (str)
        
    Returns:
        str: prefix + separator + name
    
    """
    new_name = cmds.rename(node, '%s%s%s' % (prefix,separator, name))
    
    return new_name

def get_node_name(node_type, description):
    
    return inc_name('%s_%s' % (node_type, description))

def create_node(node_type, description):
    
    name = get_node_name(node_type, description)
    new_name =  cmds.createNode(node_type, n = name)
    
    return new_name
    
def rename_node(node, description):
    
    node_type = cmds.nodeType(node)
    node_name = get_node_name(node_type, description)
    new_name = cmds.rename(node, node_name)
    
    return new_name
    

def prefix_hierarchy(top_group, prefix):
    """
    Prefix all the names in a hierarchy.
    
    Args:
        top_group (str): Name of the top node of a hierarchy.
        prefix (str): Prefix to add in front of top_group and all children.
        
    Returns:
        list: The renamed hierarchy including top_group.
    """
    
    relatives = cmds.listRelatives(top_group, ad = True, f = True)
     
    relatives.append(top_group)
    
    renamed = []
    
    prefix = prefix.strip()
    
    for relative in relatives:

        short_name = get_basename(relative)
        
        new_name = cmds.rename(relative, '%s_%s' % (prefix, short_name))
        renamed.append(new_name)
    
    renamed.reverse()
    
    return renamed
    
def pad_number(name):
    """
    Add a number to a name.
    """
    
    number = vtool.util.get_last_number(name)
    
    if number == None:
        number = 0
    
    number_string = str(number)
    
    index = name.rfind(number_string)

    if number < 10:
        number_string = number_string.zfill(2)
        
    new_name =  name[0:index] + number_string + name[index+1:]
    renamed = cmds.rename(name, new_name)
    
    return renamed

        
def get_outliner_sets():
    """
    Get the sets found in the outliner.
    
    Returns:
        list: List of sets in the outliner.
    """
    
    sets = cmds.ls(type = 'objectSet')
                
    top_sets = []
        
    for object_set in sets:
        if object_set == 'defaultObjectSet' or object_set == 'defaultLightSet':
            continue
        
        if cmds.sets(object_set, q = True, r = True):
            continue
        
        top_sets.append(object_set)
    return top_sets

def delete_outliner_sets():
    """
    Delete objectSets that usually appear in the outliner
    """
    
    cmds.delete(get_outliner_sets())
    

def get_top_dag_nodes(exclude_cameras = True, namespace = None):
    """
    Get transforms that sit at the very top of the hierarchy.
    
    Returns:
        list
    """
    
    top_transforms = cmds.ls(assemblies = True)
    
    if exclude_cameras:
        cameras = ['persp', 'top', 'front', 'side']
                
        for camera in cameras:
            try:
                top_transforms.remove(camera)
            except:
                pass
    
    if namespace:
        
        found = []
        
        for transform in top_transforms:
            if transform.startswith(namespace + ':'):
                found.append(transform)
    
        top_transforms = found
    
    return top_transforms 

def get_top_dag_nodes_in_list(list_of_transforms):
    """
    Given a list of transforms, return only the ones at the top of the hierarchy
    """
    
            
    found = []
    
    for transform in list_of_transforms:
        long_name = cmds.ls(transform, l = True)
        
        if long_name:
            if long_name[0].count('|') == 1:
                found.append(transform)
    
    return found    
    

def get_first_shape(transform):
    """
    returns first active shape
    """
    
    shapes = get_shapes(transform)
    
    for shape in shapes:
        
        if not cmds.getAttr('%s.intermediateObject'):
            return shape

    
def get_shapes(transform, shape_type = None, no_intermediate = False):
    """
    Get all the shapes under a transform.
    
    Args:
        transform (str): The name of a transform.
        
    Returns:
        list: The names of shapes under the transform
    """
    transforms = vtool.util.convert_to_sequence(transform)
    
    found = []
    
    for transform in transforms:
        if is_a_shape(transform):
            parent = cmds.listRelatives(transform, p = True, f = True)
            shapes_list = cmds.listRelatives(parent, s = True, f = True, ni = no_intermediate)
        
            if shapes_list:
                found += shapes_list
        
            if found:
                continue
        
        
        
        if shape_type:
            shape_type_list = cmds.listRelatives(transform, s = True, f = True, type = shape_type, ni = no_intermediate)
            if shape_type_list:
                found += shape_type_list
        if not shape_type:
            none_shape_type_list = cmds.listRelatives(transform, s = True, f = True, ni = no_intermediate)
            if none_shape_type_list:
                found += none_shape_type_list
            
    if found:
        return found


def get_shape_node_type(node):
    
    shapes = get_shapes(node)
    
    if shapes:
        return cmds.nodeType(shapes[0])

def get_node_types(nodes, return_shape_type = True):
    """
    Get the maya node types for the nodes supplied.
    
    Returns:
        dict: dict[node_type_name] node dict of matching nodes
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
     
def get_basename(name, remove_namespace = True, remove_attribute = False):
    """
    Get the basename in a hierarchy name.
    If top|model|face is supplied, face will be returned.
    """
    
    split_name = name.split('|')
    
    
    basename = split_name[-1]
    
    if remove_attribute:
        basename_split = basename.split('.')
        basename = basename_split[0]
        return basename
    
    if remove_namespace:
        split_basename = basename.split(':')
        return split_basename[-1]
    
    
    
    return split_name[-1]

def get_namespace(name):
    
    namespace = name.rpartition(':')[0]
    return namespace

def get_dg_nodes():
    
    nodes = cmds.ls(dep = True)
    
    return nodes

def remove_namespace_from_string(name):
    
    sub_name = name.split(':')
        
    new_name = ''
        
    if sub_name:
        new_name = sub_name[-1]
        
    return new_name

def get_characters():
    
    namespaces = cmds.namespaceInfo(lon = True)
    
    found = []
    
    check_for_groups = ['controls', 'model', 'geo', 'setup', 'DO_NOT_TOUCH', 'rig']
    
    for namespace in namespaces:
        
        for group in check_for_groups:
        
            if cmds.objExists(namespace + ':' + group):
                if not namespace in found:
                    found.append(namespace)
            
            
    return found

def delete_unknown_nodes():
    """
    This will find all unknown nodes. Unlock and delete them.
    """
    
    unknown = cmds.ls(type = 'unknown')

    deleted = []
    
    for node in unknown:
        if cmds.objExists(node):
            cmds.lockNode(node, lock = False)
            cmds.delete(node)
            
            deleted.append(node)
            
    vtool.util.show('Deleted unknowns: %s' % deleted)

def rename_shapes(transform):
    """
    Rename all the shapes under a transform. 
    Renames them to match the name of the transform.
    
    Args:
        transform (str): The name of a transform.
    """
    
    shapes = get_shapes(transform)
    
    if not shapes:
        return
    
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

def get_shapes_in_hierarchy(transform, shape_type = '', return_parent = False, skip_first_relative = False):
    """
    Get all the shapes in the child hierarchy excluding intermediates.
    This is good when calculating bounding box of a group.
    
    Args:
        transform (str): The name of a transform.
        
    Returns:
        list: The list of shape nodes.
    """
    
    if not cmds.objExists(transform):
        vtool.util.warning('%s does not exist. Could not get hierarchy' % transform)
        return
    
    hierarchy = [transform]
    
    relatives = cmds.listRelatives(transform, ad = True, type = 'transform', f = True)
    
    if relatives:
        hierarchy += relatives
    
    shapes = []
    
    if skip_first_relative:
        hierarchy = hierarchy[1:]
    
    for child in hierarchy:
        
        found_shapes = get_shapes(child, shape_type)
        sifted_shapes = []
        
        if not found_shapes:
            continue
        
        for found_shape in found_shapes:
            
            if cmds.getAttr('%s.intermediateObject' % found_shape):
                continue
            
            if return_parent:
                found_shape = child
            sifted_shapes.append( found_shape )
            
        if sifted_shapes:
            shapes += sifted_shapes
    
    return shapes


def has_shape_of_type(node, maya_type):
    """
    Test whether the node has a shape of the supplied type.
    
    Args:
        node (str): The name of a node.
        maya_type (str): Can be a mesh, nurbsCurve, or any maya shape type. 
        
    Returns:
        bool
    """
    test = None
    
    if not cmds.objExists(node):
        return False
    
    if cmds.objectType(node, isAType = 'shape'):
        test = node
        
    if not cmds.objectType(node, isAType = 'shape'):
        shapes = get_shapes(node)
        
        if shapes:
            
            test = shapes[0]
        
    if test:
        if maya_type == cmds.nodeType(test):
            
            return True
        
def get_orig_nodes(parent = None):
    """
    Get all the orig nodes in a scene, or just the ones under the parent.
    """
    shapes = None
    
    if not parent:
        shapes = cmds.ls(type = 'shape', l = True)
    if parent:
        shapes = cmds.listRelatives(parent, shapes = True, f = True)
    
    if not shapes:
        return
    
    found = []
    
    for shape in shapes:
        
        if is_referenced(shape):
            continue
        
        if cmds.getAttr('%s.intermediateObject' % shape):
            found.append(shape)
            
    return found

def get_active_orig_node(transform):
    
    origs = get_orig_nodes(transform)
    
    for orig in origs:
        connections = cmds.listConnections(orig)
        
        if connections:
            return orig

def get_component_count(transform):
    """
    Get the number of components under a transform. 
    This does not include hierarchy.
    
    Args:
        transform (str): The name of a transform.
    
    Returns:
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
        
    Returns:
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
        
    Returns:
        list: The name of all components under transform, eg verts, cvs, etc.
    """
    
    shapes = get_shapes_in_hierarchy(transform)
    
    return get_components_from_shapes(shapes)

def get_components_from_shapes(shapes = None):
    """
    Get the components from the a list of shapes.  Curntly supports cv and vtx components
    
    Args:
        shapes (list): List of shape names.
        
    Returns:
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

def create_group(name, parent = None):
    
    if not name:
        return
    
    
    sequence = vtool.util.convert_to_sequence(name)
    parent = vtool.util.convert_to_sequence(parent)
    if parent:
        parent = parent[0]
    
    
    found = []
    
    for sub_name in sequence:
    
        if not cmds.objExists(sub_name):
            
            sub_name = cmds.group(em = True, n = sub_name)
            
        if parent and cmds.objExists(parent):
            
            actual_parent = None
            
            actual_parent = cmds.listRelatives(sub_name, p = True)
            
            if actual_parent:
                actual_parent = actual_parent[0]
            
            if not parent == actual_parent:
                cmds.parent(sub_name, parent)
        
        found.append(sub_name)
        
    return found

def create_display_layer(name, nodes, display_type = 2, recursive_add = False):
    """
    Create a display layer containing the supplied nodes.
    
    Args:
        name (str): The name to give the display layer.
        nodes (str): The nodes that should be in the display layer.
        
    """
    layer = cmds.createDisplayLayer( name = name )
    
    no_recursive = True
    if recursive_add:
        no_recursive = False
    
    cmds.editDisplayLayerMembers( layer, nodes, noRecurse = no_recursive)
    cmds.setAttr( '%s.displayType' % layer, display_type )
    return layer

def delete_display_layers():
    """
    Deletes all display layers.
        
    
    """
    layers = cmds.ls(type = 'displayLayer')
    
    for layer in layers:
        cmds.delete(layer)

def print_help(string_value):
    
    string_value = string_value.replace('\n', '\nV:\t\t')
    
    OpenMaya.MGlobal.displayInfo('V:\t\t' + string_value)
    vtool.util.record_temp_log('\n%s' % string_value)
    
def print_warning(string_value):
    
    string_value = string_value.replace('\n', '\nV:\t\t')
    OpenMaya.MGlobal.displayWarning('V:\t\t' + string_value)
    vtool.util.record_temp_log('\nWarning!:  %s' % string_value)

def print_error(string_value):

    string_value = string_value.replace('\n', '\nV:\t\t')
    OpenMaya.MGlobal.displayError('V:\t\t' + string_value)
    vtool.util.record_temp_log('\nError!:  %s' % string_value)

def delete_set_contents(set_name):
    
    children = cmds.sets(set_name, no = True, q = True)
    
    if children:
        found_dag = []
        found_dg = []     
        for child in children:
            if cmds.nodeType(child) == 'objectSet':
                delete_set_contents(set_name)
            else:
                if cmds.objectType(child, isAType='transform'):
                    found_dag.append(child)
                else:
                    found_dg.append(child)
                
        found = found_dag + found_dg
        cmds.sets(found, remove = set_name)
        cmds.delete(found_dg)
        cmds.delete(found_dag)

def delete_set(set_name):
    #deletes the set and any sub sets
    
    children = cmds.sets(set_name, no = True, q = True)
    
    if children: 
        for child in children:
            if cmds.nodeType(child) == 'objectSet':
                delete_set(set_name)
    
    cmds.delete(set_name)
    

def add_to_set(nodes, set_name):
    
    nodes = vtool.util.convert_to_sequence(nodes)
    
    if not cmds.objExists(set_name):
        object_set = cmds.createNode('objectSet')
        cmds.rename(object_set, set_name)
    
    if not cmds.nodeType(set_name) == 'objectSet':
        print_warning('%s is not an object set. Could not add to it.' % set_name)
        
    cmds.sets(nodes, add = set_name)
    
def get_set_children(set_name):
    #this will get all set children recursively, but only notices children that are not sets
    
    children = cmds.sets(set_name, no = True, q = True)
    if not children:
        return
    found = [] 
    for child in children:
        if cmds.nodeType(child) == 'objectSet':
            sub_children = get_set_children(child)
            if sub_children:
                found += sub_children
        else:
            found.append(child)
    
    return found
    
def load_plugin(plugin_name):
    if not cmds.pluginInfo(plugin_name, query = True, loaded = True):
        vtool.util.show('Loading plugin: %s' % plugin_name)
        cmds.loadPlugin(plugin_name)
        
def remove_non_existent(list_value):
    
    found = []
    
    for thing in list_value:
        if thing and cmds.objExists(thing):
            found.append(thing)
            
    return found

def remove_referenced_in_list(list_value):
    
    found = []
    
    for thing in list_value:
        if not cmds.referenceQuery(thing, isNodeReferenced = True):
            found.append(thing)
    
    return found

def get_hierarchy_by_depth(transforms):
    """
    Gets a hierarchy in order of depth. Least deep first
    """
    
    rels = transforms
        
    rel_count = {}
    
    for rel in rels:
        count = rel.count('|')
        
        if not count in rel_count:
            rel_count[count] = []
        
        rel_count[count].append(rel)
    
    counts = rel_count.keys()
    counts.sort()
        
    rels = []
    for count in counts:
        rel_list = rel_count[count]
        rel_list.reverse
        rels += rel_list
    
    return rels

def get_hierarchy(transform):
    
    rels = cmds.listRelatives(transform, ad = True, type = 'transform')
    
    rels.reverse()
    
    return rels
    
  
#--- file

def get_scene_file(directory = False):
    
    path = cmds.file(q=True, sn=True)
    
    if directory and path:
        path = vtool.util_file.get_dirname(path)
    
    return path
    
def start_new_scene():

    cmds.file(new = True, f = True)
    
    cmds.flushIdleQueue()

def open_file(filepath):
    
    cmds.file(filepath, f = True, o = True)
    auto_focus_view()

def import_file(filepath):
    """
    Import a maya file in a generic vtool way.
    """
    cmds.file(filepath, f = True, i = True, iv = True, pr = True)# rpr = "vetala_clash")#, mergeNamespacesOnClash = True, renameAll = False)
    auto_focus_view()

def save(filepath):
    
    saved = False
    
    vtool.util.show('Saving:  %s' % filepath)
    
    file_type = 'mayaAscii'
    
    if filepath:
    
        if filepath.endswith('.mb'):
            file_type = 'mayaBinary'
        
        try:
            
            cmds.file(rename = filepath)
            cmds.file(save = True, type = file_type)
            
            saved = True
        except:
            status = traceback.format_exc()
            vtool.util.error(status)
            saved = False
        
    if not filepath:
        saved = False
        
    #if saved:
    #    vtool.util.show('Scene Saved')
    
    if not saved:
        
        if not is_batch():
            cmds.confirmDialog(message = 'Warning:\n\n Vetala was unable to save!', button = 'Confirm')
        
        print_error('Scene not saved.  Filepath:  %s' % filepath)
        
        if filepath:
            vtool.util.show('This is a Maya save bug, not necessarily an issue with Vetala.  Try saving "Save As" to the filepath with Maya and you should get a similar error.')
        
        permission = vtool.util_file.get_permission(filepath)
        if not permission:
            print_error('Could not get write permission.')
        
        return False
    
    return saved

#--- reference

def reference_file(filepath, namespace = None):
    """
    Reference a maya file in a generic vtool way.
    
    Args:
        filepath (str): The full path and filename.
        namespace (str): The namespace to add to the nodes in maya.  Default is the name of the file. 
    """
    
    if namespace == None:
        namespace = os.path.basename(filepath)
        split_name = namespace.split('.')
        
        if split_name:
            namespace = string.join(split_name[:-1], '_')
    if namespace == False:
        namespace = ':'
        
    
        
    reference = cmds.file( filepath,
                           reference = True, 
                           gl = True, 
                           mergeNamespacesOnClash = False, 
                           namespace = namespace, 
                           options = "v=0;")
    
    return reference
    
def replace_reference(reference_node, new_path):
    """
    Not tested
    """
    rn_node = cmds.referenceQuery(reference_node, rfn = True)
    
    cmds.file(new_path,loadReference = rn_node)
    
    #file -loadReference "TyrannosaurusRexRN" -type "mayaAscii" -options "v=0;" "N:/projects/dinodana/assets/Character/TyrannosaurusRex/SURF/publish/maya/TyrannosaurusRex.v024.ma";
    
def reload_reference(reference_node):
    
    rn_node = cmds.referenceQuery(reference_node, rfn = True)
    
    filepath = cmds.referenceQuery(rn_node, filename = True)
    
    cmds.file(filepath, loadReference = rn_node) 
    
def get_reference_filepath(reference_node):
    
    if not reference_node:
        return
    
    filepath = cmds.referenceQuery(reference_node, filename = True)
    
    if filepath[-3] == '{' and filepath[-1] == '}':
        filepath = filepath[:-3]
    
    filepath = vtool.util_file.fix_slashes(filepath)
    
    return filepath
    
def get_reference_node_from_namespace(namespace):
    ref_nodes = cmds.ls(type = 'reference')
    for ref_node in ref_nodes: 
        test_namespace =  cmds.referenceQuery(ref_node, namespace = True)
        
        if test_namespace.startswith(':'):
            test_namespace = test_namespace[1:]
        
        if namespace == test_namespace:
            return ref_node
    
    
def remove_reference(reference_node):
    
    namespace = None
    
    if not cmds.objExists(reference_node):
        return
    
    #try getting the namespace
    try:
        namespace = cmds.referenceQuery(reference_node, ns = True)
    except:
        #if you can't get the namespace then something is wrong with the reference node, try deleting.
        cmds.lockNode(reference_node, l = False)
        try:
            cmds.delete(reference_node)
            return
        except:
            vtool.util.warning('Could not remove %s' % reference_node)
        return
    
    #try removing the good way after finding namespace
    try:
        cmds.file( removeReference = True, referenceNode = reference_node)
    except:
        #if it can't be removed the good way with a namespace then something is wrong, try deleting.
        cmds.lockNode(reference_node, l = False)
        try:
            cmds.delete(reference_node)
            return
        except:
            vtool.util.warning('Could not remove %s' % reference_node)
        return
    
    #try to remove the namespace incase it gets left behind.
    try:
        if namespace:
            cmds.namespace(dnc = True, rm = namespace)
    except:
        pass

    
    return

#--- ui

def get_tool():
    return cmds.currentCtx()

def set_tool_to_select():
    
    g_select = mel.eval('$tmp = $gSelect;')
    cmds.setToolTo(g_select)
    
def set_tool(context):
    try:
        cmds.setToolTo(context)
    except:
        vtool.util.warning('Was unable to set context to %s' % context)

def get_progress_bar():
    
    gMainProgressBar = mel.eval('$tmp = $gMainProgressBar');
    return gMainProgressBar

def get_node_editors():
    
    found = []
    
    if is_batch():
        return []
    
    for panel in cmds.getPanel(type='scriptedPanel'):
        if cmds.scriptedPanel(panel, query=True, type=True) == "nodeEditorPanel":
            nodeEditor = panel + "NodeEditorEd"
            found.append(nodeEditor)

    return found

def get_under_cursor(use_qt = True):
    """
    Get what is currently under the cursor using qt or not.
    When not using qt it is more of a hack.
    """
    
    if not use_qt:
        try:
            menu = cmds.popupMenu()
        
            cmds.dagObjectHit(mn = menu)
            
            items = cmds.popupMenu(menu, q = True, ia = True)
            if not items:
                return
            selected_item =  cmds.menuItem(items[0], q = True, l = True)
            
            cmds.deleteUI(menu)
            
            selected_item = selected_item[:-3]
            
            return selected_item
        except:
            return

    if use_qt:
        
        from vtool import qt
        
        pos = qt.QCursor.pos()
        widget = qt.qApp.widgetAt(pos)
        
        if not widget:
            return
        
        relpos = widget.mapFromGlobal(pos)
    
        panel = cmds.getPanel(underPointer=True) or ""
    
        if not "modelPanel" in panel:
            return
    
        return (cmds.hitTest(panel, relpos.x(), relpos.y()) or [None])[0]

def get_visible_hud_displays():
    """
    Get viewport hud displays.
    
    Returns:
        list:  List of names of heads up displays.
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
    
    if vtool.util.get_maya_version() < 2017:
    
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
            
    if vtool.util.get_maya_version() > 2016:
        if 'Channel Box / Layer Editor' in docks:
            index = docks.index('Channel Box / Layer Editor')
            dock = docks[index + 1]
            
            if cmds.workspaceControl(dock, q = True, visible = True):
                cmds.workspaceControl(dock, edit = True, visible = False)
                cmds.workspaceControl(dock, edit = True, visible = True)
        
        index = docks.index('Channel Box')
        dock = docks[index + 1]
                
        if cmds.workspaceControl( dock, q = True, visible = True):
            cmds.workspaceControl(dock, edit = True, visible = False)
            cmds.workspaceControl(dock, edit = True, visible = True)

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


def get_current_audio_node():
    """
    Get the current audio node. Important when getting sound in a playblast.
    
    Returns:
        str: Name of the audio node.
    """
    
    play_slider = mel.eval('global string $gPlayBackSlider; string $goo = $gPlayBackSlider')
    
    return cmds.timeControl(play_slider, q = True, s = True)

def xray_joints(bool_value = True):
    cmds.modelEditor('modelPanel1', e = True, jointXray = bool_value)
    cmds.modelEditor('modelPanel2', e = True, jointXray = bool_value)
    cmds.modelEditor('modelPanel3', e = True, jointXray = bool_value) 
    cmds.modelEditor('modelPanel4', e = True, jointXray = bool_value)

def display_textures(bool_value = True):
    cmds.modelEditor('modelPanel1', e = True, displayTextures = bool_value)
    cmds.modelEditor('modelPanel2', e = True, displayTextures = bool_value)
    cmds.modelEditor('modelPanel3', e = True, displayTextures = bool_value) 
    cmds.modelEditor('modelPanel4', e = True, displayTextures = bool_value)

def auto_focus_view(selection = False):
    
    if is_batch():
        return
    
    settings_path = vtool.util.get_env('VETALA_SETTINGS')
    settings = vtool.util_file.SettingsFile()
    settings.set_directory(settings_path)
        
    auto_focus = settings.get('auto_focus_scene')
    if not auto_focus:
        vtool.util.show('Auto focus turned off in settings')
        return
    
    try:
        if selection:
            cmds.viewFit(an = True, fitFactor = 1)
        else:
            cmds.viewFit(an = True, fitFactor = 1, all = True)
    except:
        vtool.util.show('Could not center view')

    vtool.util.show('Auto focus')
    fix_camera()

def fix_camera():

    camera_pos = cmds.xform('persp', q = True, ws = True, t = True)
    
    distance = vtool.util.get_distance([0,0,0], camera_pos)
    distance = (distance*10)
    
    try:
        cmds.setAttr('persp.farClipPlane', distance)
    except:
        pass
    
    near = 0.1
    
    if distance > 10000:
        near = (distance/10000) * near

    try:
        cmds.setAttr('persp.nearClipPlane', near)
    except:
        pass
            
#--- garbage

def remove_unused_plugins():
    
    list_cmds = dir(cmds)
    
    if not 'unknownPlugin' in list_cmds:
        return
    
    unknown = cmds.ls(type = 'unknown')
    
    if unknown:
        return
        
    unused = []
    unknown_plugins = cmds.unknownPlugin(query = True, list = True)
    
    if unknown_plugins:
        for unknown_plugin in unknown_plugins:
            try:
                cmds.unknownPlugin(unknown_plugin, remove = True)
            except:
                continue
            unused.append(unknown_plugin)
    
    if unused:   
        vtool.util.show('Removed unused plugins: %s' % unused)

def delete_turtle_nodes():

    plugin_list = cmds.pluginInfo(query = True, pluginsInUse = True)
    
    nodes = []
    
    if plugin_list:
        for plugin in plugin_list:
            
            if plugin[0] == 'Turtle':
                
                turtle_types = ['ilrBakeLayer', 
                                'ilrBakeLayerManager', 
                                'ilrOptionsNode', 
                                'ilrUIOptionsNode']
                
                nodes = delete_nodes_of_type(turtle_types)
                
                break
        
    if nodes:
        vtool.util.show('Removed Turtle nodes: %s' % nodes )

def delete_nodes_of_type(node_type):
    """
    Delete all the nodes of type. 
    Good for cleaning up scenes.
    
    Args:
        node_type (str): The name of a node type. Eg. hyperView, ilrBakeLayouerManger, etc
        
    """
    
    node_type = vtool.util.convert_to_sequence(node_type)
    
    deleted = []
    
    
    for node_type_name in node_type:
        
        nodes = cmds.ls(type = node_type_name)
        
        for node in nodes:
            
            if node == 'hyperGraphLayout':
                continue
            
            if not cmds.objExists(node):
                continue
            
            cmds.lockNode(node, lock = False)
            cmds.delete(node)
            deleted.append(node)
    
    return deleted

def delete_garbage():
    
    straight_delete_types = []

    if vtool.util.get_maya_version() > 2014:
        #maya 2014 crashes when trying to delete hyperView or hyperLayout nodes in some files.
        straight_delete_types += ['hyperLayout','hyperView']
    
    deleted_nodes = delete_nodes_of_type(straight_delete_types)
    
    check_connection_node_type = ['shadingEngine', 'partition','objectSet']
    
    check_connection_nodes = []
    
    for check_type in check_connection_node_type:
        nodes = cmds.ls(type = check_type)
        
        check_connection_nodes += nodes
    
    garbage_nodes = []
    
    if deleted_nodes:
        garbage_nodes = deleted_nodes
    
    immortals = cmds.ls(ud = True)
    
    for node in check_connection_nodes:
        
        if node in immortals:
            continue
        
        if not node or not cmds.objExists(node):
            continue
        
        if is_empty(node):

            cmds.lockNode(node, lock = False)
            
            try:
                cmds.delete(node)
            except:
                pass
            
            if not cmds.objExists(node):
                garbage_nodes.append(node)
    
    if garbage_nodes:
        vtool.util.show('Deleted Garbage nodes: %s' % garbage_nodes)
    
def delete_empty_orig_nodes():
    
    origs = get_empty_orig_nodes()
    
    for orig in origs:
        cmds.delete(orig)
    
    if origs:
        print_help('Deleted Unused Intermediate Object or Orig nodes: %s' % origs)
    
def delete_empty_nodes():
    
    nodes = get_empty_nodes()
    
    cmds.delete(nodes)
    
    print_help('Deleted Empty (Unconnected) nodes: %s' % nodes)
    
    
#--- empty

def get_empty_groups():
    
    groups = cmds.ls(type = 'transform')
    
    found = []
    
    for group in groups:
        
        if cmds.nodeType(group) == 'joint':
            continue
        
        if is_empty(group):
            found.append(group)
            
    return found

def get_empty_nodes():

    dg_nodes = get_dg_nodes()
    
    found = []
    
    undel_nodes = []
    
    try:
        undel_nodes = cmds.ls(undeletable = True)
                
    except:
        pass
    
    if undel_nodes:
        node_set = set(dg_nodes)
        undel_set = set(undel_nodes)
        
        dg_nodes = list(node_set - undel_set)
    
    for node in dg_nodes:
        
        if is_empty(node):
            found.append(node)
    
    return found

def get_empty_orig_nodes():
    
    origs = get_orig_nodes()
    
    found = []
    
    for orig in origs:
        connections = cmds.listConnections(orig)
        
        if not connections:
            found.append(orig)

    return found

def get_empty_reference_nodes():
    
    references = cmds.ls(type = 'reference')
    
    found = []
    
    for reference in references:
        try:
            cmds.referenceQuery(reference, filename = True)
        except:
            found.append(found)
            
    return found()

def get_non_unique_names():
    dag_nodes = cmds.ls(type = 'dagNode')
        
    found = []
        
    for dag_node in dag_nodes:
        
        if dag_node.find('|') > -1:
            
            found.append(dag_node)
            
    return found

def is_hidden(transform, skip_connected = True, shape = True):
    
    vis_attr = '%s.visibility' % transform
    if cmds.getAttr(vis_attr) == 0:
        if skip_connected and not cmds.listConnections(vis_attr, s = True, d = False, p = True):
            return True
            
        if not skip_connected:
            return True    
    
    if shape:
        shapes = cmds.listRelatives(transform, shapes = True)
        
        if shapes:
            shape_hidden_count = 0
            for sub_shape in shapes:
                if is_hidden(sub_shape, skip_connected, shape = False):
                    shape_hidden_count += 1
            
            if len(shapes) == shape_hidden_count:
                return True
    

    
    return False 

def is_parent_hidden(transform, skip_connected = True):
    """
    Searches the parent hierarchy to find one parent that is hidden.
    """
    parent = cmds.listRelatives(transform, p = True, f = True)
    if parent:
        parent = parent[0]
        
    parent_invisible = False
    while parent:
        hidden = is_hidden(transform, skip_connected)
        
        if hidden:
            parent_invisible = True
            break

        parent = cmds.listRelatives(parent, p = True, f = True)
        if parent:
            parent = parent[0]
            
    return parent_invisible
