# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.
import sys
import re
import math
import time
import string
import datetime
import traceback
import platform
import os
import base64
import __builtin__
from HTMLParser import HTMLParser

temp_log = ''
last_temp_log = ''

def get_custom(name, default = ''):
    
    try:
        from vtool import __custom__
    except:
        return default
    
    value = None
    
    exec( "value = __custom__.%s" % name )
    
    if not value:
        return default
    
    return value

class VetalaHTMLParser(HTMLParser):

    def __init__(self):
        HTMLParser.__init__(self)
        
        self._in_body = False
        self.all_body_data = []
    
    def handle_starttag(self, tag, attrs):
        if tag == 'body':
            self._in_body = True
        
    def handle_endtag(self, tag):
        if tag == 'body':
            self._in_body = False
    
    def handle_data(self, data):
        
        data = data.strip()
        
        if not data:
            return
        
        if self._in_body:
            
            self.all_body_data.append(data.strip())
            
    def get_body_data(self):
        return self.all_body_data

class ControlName(object):
    
    CONTROL_ALIAS = 'Control Alias'
    DESCRIPTION = 'Description'
    NUMBER = 'Number'
    SIDE = 'Side'
    
    def __init__(self):
        
        self.control_alias = 'CNT'
        self.center_alias = 'C'
        self.left_alias = 'L'
        self.right_alias = 'R'
        
        self.control_order = [self.CONTROL_ALIAS, self.DESCRIPTION, self.NUMBER, self.SIDE]
        
        self.control_uppercase = True
        
        self._control_number = True
        
    def set_control_alias(self, alias):
        self.control_alias = str(alias)
        
    def set_left_alias(self, alias):    
        self.left_alias = str(alias)
    
    def set_right_alias(self, alias):
        self.right_alias = str(alias)

    def set_center_alias(self, alias):
        self.center_alias = str(alias)
        
    def set_uppercase(self, bool_value):
        self.control_uppercase = bool_value

    def set_control_order(self, list_value):
        self.control_order = list_value
        
    def set_number_in_control_name(self, bool_value):
        self._control_number = bool_value
        
    def get_name(self, description, side = None):
        
        found = []
        
        if not self.control_order:
            return
        
        for name in self.control_order:
            
            if name == self.CONTROL_ALIAS:
                found.append( self.control_alias )
            if name == self.DESCRIPTION:
                found.append(description)
            if name == self.NUMBER and self._control_number == True:
                found.append(str(1))
            if name == self.SIDE:
                
                if is_left(side):
                    found.append(self.left_alias)
                    continue
                if is_right(side):
                    found.append(self.right_alias)
                    continue
                if is_center(side):
                    found.append(self.center_alias)
                    continue
        
        full_name = string.join(found, '_')
        
        if self.control_uppercase:
            full_name = full_name.upper()
        
        return full_name

def get_code_builtins():
    
    builtins = {'show':show, 
                'warning':warning}
    
    if in_maya:
        maya_builtins = {'cmds':cmds,
                    'mc':cmds,
                    'pymel':pymel,
                    'pm':pymel}
    
        for builtin in maya_builtins:
            builtins[builtin] = maya_builtins[builtin]
    
    return builtins

def reset_code_builtins(builtins = None):
    if not builtins:
        builtins = get_code_builtins()
    
    for builtin in builtins:
        
        try:
            exec('del(__builtin__.%s)' % builtin)
        except:
            pass
    
def setup_code_builtins(builtins = None):
    if not builtins:
        builtins = get_code_builtins()
        
    for builtin in builtins:
        
        try:
            exec('del(__builtin__.%s)' % builtin)
        except:
            pass
        
        builtin_value = builtins[builtin]
        
        exec('__builtin__.%s = builtin_value' % builtin)

def initialize_env(name):
    """
    Initialize a new environment variable.
    If the variable already exists, does nothing, no environment variable is initialized.
    
    Args:
        name (str): Name of the new environment variable.
    """
    if not os.environ.has_key(name):
        os.environ[name] = ''

def set_env(name, value):
    """
    Set the value of an environment variable.
    
    Args:
        name (str): Name of the environment variable to set.
        value (str): If a number is supplied it will automatically be converted to str.
    """
    
    
    if os.environ.has_key(name):
        
        value = str(value)
        
        size = sys.getsizeof(value)
        if size > 32767:
            value = value[:30000]
            value = 'truncated... ' + value 
        os.environ[name] = value
        
        
def get_env(name):
    """
    Get the value of an environment variable.
    
    Args:
        name (str): Name of an environment variable.
        
    Returns
        str:
    """
    if os.environ.has_key(name):
        return os.environ[name]

def append_env(name, value):
    """
    Append string value to the end of the environment variable
    """
    
    env_value = get_env(name)
    
    try:
        env_value += str(value)
    except:
        pass 
    
    set_env(name, env_value)
    
def start_temp_log():
    
    set_env('VETALA_KEEP_TEMP_LOG', 'True')
    global temp_log
    temp_log = ''

def record_temp_log(value):
    
    global temp_log
    
    if get_env('VETALA_KEEP_TEMP_LOG') == 'True':
        value = value.replace('\t', '  ')
        temp_log += value
        
def end_temp_log():
    
    global temp_log
    global last_temp_log
    
    set_env('VETALA_KEEP_TEMP_LOG', 'False')
    value = temp_log
    if value:
        last_temp_log = temp_log
        
    
        temp_log = ''
    
    return value

def get_last_temp_log():
    
    global last_temp_log
    return last_temp_log
    

def add_to_PYTHONPATH(path):
    """
    Add a path to the python path, only if it isn't present in the python path.
    
    Args:
        path (str): The path to add to the python path.
    """
    if not path:
        return
    
    if not path in sys.path:
        sys.path.append(path)

def profiler_event(frame, event, arg, indent = [0]):
    if event == "call":
        indent[0] += 2
        print "-" * indent[0] + "> ", event, frame.f_code.co_name
    elif event == "return":
        print "<" + ("-" * indent[0]) + " ", event, frame.f_code.co_name
        indent[0] -= 2
    
    return profiler_event

def activate_profiler():
    """
    Activating the profiler will give extremely detailed information about what functions are running and in what order.
    """
    sys.setprofile(profiler_event)

#decorators
def try_pass(function):
    """
    Try a function and if it fails pass.  Used as a decorator.
    Usage:
    @try_pass
    def myFunction():
        do_something
    """
    def wrapper(*args, **kwargs):
        
        return_value = None
                
        try:
            return_value = function(*args, **kwargs)
        except:
            error(traceback.format_exc())
                    
        return return_value
                     
    return wrapper

def is_stopped():
    if get_env('VETALA_STOP') == 'True':
        return True
        
    return False

#--- query

def is_in_maya():
    """
    Check to see if scope is in Maya.
    
    Returns:
        bool:
    """
    try:
        import maya.cmds as cmds
        return True
    except:
        return False

in_maya = False

if is_in_maya():
    in_maya = True
    import maya.cmds as cmds
    import pymel.all as pymel

def has_shotgun_api():
    """
    Check if the shotgun api is available.
    
    Returns:
        bool:
    """
    try:
        import shotgun_api3
        return True
    except:
        return False
    
def has_shotgun_tank():
    """
    Check if the shotgun tank api is available.
    
    Returns:
        bool:
    """
    try:
        #import tank
        import sgtk
        return True
    except:
        return False
        
        


def get_current_maya_location():
    """
    Get where maya is currently running from.
    """
    location = ''
    
    if os.environ.has_key('MAYA_LOCATION'):
        location = os.environ['MAYA_LOCATION']
    
    return location

def is_in_nuke():
    """
    Check to see if scope is in Nuke
    
    Returns:
        bool:
    """
    try:
        import nuke
        return True
    except:
        return False

def is_linux():
    """
    Check to see if running in linux
    
    Returns:
        bool:
    """
    if platform.system() == 'Linux':
        return True
    
    return False
    
def is_windows():
    """
    Check to see if running in windows
    
    Returns:
        bool:
    """
    
    if platform.system() == 'Windows':
        return True
    
    return False

def get_maya_version():
    """
    Get the version of maya that the scope is running in.
    
    Returns:
        int: The date of the Maya version.
    """
    
    if is_in_maya():
        import maya.cmds as cmds
        
        try:
            version = cmds.about(v = True)
            split_version = version.split()
            version = int(split_version[0])
            return version
        except:
            show('Could not get maya version.')

    if not is_in_maya():
        return None

def break_signaled():
    """
    Check to see if Vetala break was signalled.
    
    Returns:
        bool:
    """
    if get_env('VETALA_RUN') == 'True':
        if get_env('VETALA_STOP') == 'True':
            return True

    return False

class StopWatch(object):
    """
    Utility to check how long a command takes to run.
    """
    
    running = 0
    watch_list = []
    
    def __del__(self):
        pass
        #self.end()
    
    def __init__(self):
        self.time = None
        self.feedback = True
        self.description = ''
        self.round = 2
        self.enable = True
    
    def start(self, description = '', feedback = True):
        
        if not self.enable:
            return
        
        self.__class__.running += 1
        self.running = self.__class__.running - 1
        
        self.description = description
        self.feedback = feedback
        
        if feedback:
            tabs = '\t' * self.running
            show('%sStarted timer:' % tabs, description)
        
        self.time = time.time()
        
        self.__class__.watch_list.append( [description, self.time] )   
    
    def end(self):
        
        if not self.enable:
            return
        
        self.description, self.time = self.__class__.watch_list[self.running]
        
        if not self.time:
            if self.running > 0:
                self.__class__.running -= 1
                self.running -= 1
            return
        
        seconds = time.time()-self.time
        self.time = None
        
        seconds = round(seconds, self.round)
        minutes = None
        
        if seconds > 60:
            minutes, seconds = divmod(seconds, 60)
            seconds = round(seconds,self.round)
            minutes = int(minutes)
            
        
        if self.feedback:
            tabs = '\t' * self.running
        
            if minutes == None:
                show('%sIt took %s: %s seconds' % (tabs, self.description, seconds))
            if minutes != None:
                if minutes > 1:
                    show('%sIt took %s: %s minutes, %s seconds' % (tabs, self.description,minutes, seconds))
                if minutes == 1:
                    show('%sIt took %s: %s minute, %s seconds' % (tabs, self.description,minutes, seconds))
        
        self.__class__.watch_list.pop()
        
        if self.running > 0:
            self.running -= 1
        
        self.__class__.running -= 1
            
        
        return minutes, seconds
    
    def stop(self):
        if not self.enable:
            return
        return self.end()

    

#--- math

class VectorBase(object):
    pass

class Vector2D(object):
    def __init__(self,x=1.0,y=1.0):
        self.x = None
        self.y = None
        
        if type(x) == list or type(x) == tuple:
            self.x = x[0]
            self.y = x[1]
            
        if type(x) == float or type(x) == int:
            self.x = x
            self.y = y

        self.magnitude = None

    def _add(self, value):
        if type(value) == float or type(value) == int:
            return Vector2D(self.x + value, self.y + value)
        
        if type(self) == type(value):
            return Vector2D(value.x+self.x, value.y+self.y)
        
        if type(value) == list:
            return Vector2D(self.x + value[0],self.y + value[1])
        
    def _sub(self, value):
        if type(value) == float or type(value) == int:
            return Vector2D(self.x - value, self.y - value)
        
        if type(self) == type(value):            
            return Vector2D(self.x-value.x, self.y-value.y)
        
        if type(value) == list:
            return Vector2D(self.x - value[0],self.y - value[1])
        
    def _rsub(self, value):
        if type(value) == float or type(value) == int:
            return Vector2D(value - self.x, value - self.y - value)
        
        if type(self) == type(value):
            return Vector2D(value.x-self.x, value.y-self.y)
        
        if type(value) == list:
            return Vector2D(value[0]-self.x,value[1]-self.y)
    
    def _mult(self,value):        
        if type(value) == float or type(value) == int:
            return Vector2D(self.x * value, self.y * value)
        
        if type(self) == type(value):
            return Vector2D(value.x*self.x, value.y*self.y)
        
        if type(value) == list:
            return Vector2D(self.x * value[0],self.y * value[1])

    def _divide(self,value):        
        if type(value) == float or type(value) == int:
            return Vector2D(self.x / value, self.y / value)
        
        if type(self) == type(value):
            return Vector2D(value.x / self.x, value.y / self.y)
        
        if type(value) == list:
            return Vector2D(self.x / value[0],self.y / value[1])
                
    def __add__(self, value):
        return self._add(value)
        
    def __radd__(self, value):
        return self._add(value)
            
    def __sub__(self, value):
        return self._sub(value)
        
    def __rsub__(self, value):
        return self._sub(value)
        
    def __mul__(self, value):
        return self._mult(value)
        
    def __rmul__(self, value):
        return self._mult(value)
            
    def __call__(self):
        return [self.x,self.y]
    
    def __div__(self, value):
        return self._divide(value)
    
    def _reset_data(self):
        self.magnitude = None
    
    def normalize(self, in_place = False):
        if not self.magnitude:
            self.get_magnitute()
        
        vector = self._divide(self.magnitude)
        
        if in_place:
            self.x = vector.x
            self.y = vector.y
            self._reset_data()
        
        if not in_place:
            return vector
    
    def get_vector(self):
        return [self.x,self.y]
    
    def get_magnitude(self):
        self.magnitude = math.sqrt( (self.x * self.x) + (self.y * self.y) ) 
        return self.magnitude
    
    def get_distance(self, x = 0.0, y = 0.0):
        other = Vector2D(x, y)
        
        offset = self - other
        
        return offset.get_magnitude()

class Vector(object):
    def __init__(self,x=1.0,y=1.0,z=1.0):
        
        self.x = None
        self.y = None
        self.z = None
        
        x_test = x
                
        if type(x_test) == list or type(x_test) == tuple:
            
            self.x = x[0]
            self.y = x[1]
            self.z = x[2]
            
        if type(x_test) == float or type(x_test) == int:
            self.x = x
            self.y = y
            self.z = z
        
    def _add(self, value):
        if type(value) == float or type(value) == int:
            return Vector(self.x + value, self.y + value, self.z + value)
        
        if type(self) == type(value):
            return Vector(value.x+self.x, value.y+self.y, value.z+self.z)
        
        if type(value) == list:
            return Vector(self.x + value[0],self.y + value[1],self.z + value[2])
        
    def _sub(self, value):
        if type(value) == float or type(value) == int:
            return Vector(self.x - value, self.y - value, self.z - value)
        
        if type(self) == type(value):
            return Vector(self.x - value.x, self.y - value.y, self.z - value.z)
        
        if type(value) == list:
            return Vector(self.x - value[0],self.y - value[1],self.z - value[2])
        
    def _rsub(self, value):
        if type(value) == float or type(value) == int:
            return Vector(value - self.x, value - self.y - value, value - self.z)
        
        if type(self) == type(value):
            return Vector(value.x-self.x, value.y-self.y, value.z-self.z)
        
        if type(value) == list:
            return Vector(value[0]-self.x,value[1]-self.y ,value[2]-self.z)
    
    def _mult(self,value):        
        if type(value) == float or type(value) == int:
            return Vector(self.x * value, self.y * value, self.z * value)
        
        if type(self) == type(value):
            return Vector(value.x*self.x, value.y*self.y, value.z*self.z)
        
        if type(value) == list:
            return Vector(self.x * value[0],self.y * value[1],self.z * value[2])
                
    def __add__(self, value):
        return self._add(value)
        
    def __radd__(self, value):
        return self._add(value)
            
    def __sub__(self, value):
        return self._sub(value)
        
    def __rsub__(self, value):
        return self._sub(value)
        
    def __mul__(self, value):
        return self._mult(value)
        
    def __rmul__(self, value):
        return self._mult(value)
            
    def __call__(self):
        return [self.x,self.y,self.z]
    
    def get_vector(self):
        return [self.x,self.y,self.z]
    
    def list(self):
        return self.get_vector()
    
class BoundingBox(object):
    """
    Convenience for dealing with bounding boxes
    
    Args:
        btm_corner_vector (list): [0,0,0] vector of bounding box's btm corner.
        top_corner_vector (list): [0,0,0] vector of bounding box's top corner.
    """
    
    def __init__(self, btm_corner_vector, top_corner_vector):
        
        self._load_bounding_box(btm_corner_vector, top_corner_vector)
        
    def _load_bounding_box(self, btm_corner_vector, top_corner_vector):
        self.min_vector = [btm_corner_vector[0], btm_corner_vector[1], btm_corner_vector[2]]
        self.max_vector = [top_corner_vector[0], top_corner_vector[1], top_corner_vector[2]]
        
        self.opposite_x_min_vector = [btm_corner_vector[0], top_corner_vector[1], top_corner_vector[2]]
        self.opposite_x_max_vector = [top_corner_vector[0], btm_corner_vector[1], btm_corner_vector[2]]
        
        self.opposite_y_min_vector = [top_corner_vector[0], btm_corner_vector[1], top_corner_vector[2]]
        self.opposite_y_max_vector = [btm_corner_vector[0], top_corner_vector[1], btm_corner_vector[2]]
        
        self.opposite_z_min_vector = [top_corner_vector[0], top_corner_vector[1], btm_corner_vector[2]]
        self.opposite_z_max_vector = [btm_corner_vector[0], btm_corner_vector[1], top_corner_vector[2]]
        
    def get_center(self):
        """
        Get the center of the bounding box in a vector.
        
        Returns:
            list: [0,0,0] vector
        """
        return get_midpoint(self.min_vector, self.max_vector)
    
    def get_xmin_center(self):
        return get_midpoint(self.min_vector, self.opposite_x_min_vector)
    
    def get_xmax_center(self):
        return get_midpoint(self.max_vector, self.opposite_x_max_vector)
    
    def get_ymax_center(self):
        """
        Get the top center of the bounding box in a vector.
        
        Returns:
            list: [0,0,0] vector
        """
        return get_midpoint(self.max_vector, self.opposite_y_max_vector)
        
    def get_ymin_center(self):
        """
        Get the btm center of the bounding box in a vector.
        
        Returns:
            list: [0,0,0] vector
        """
        return get_midpoint(self.min_vector, self.opposite_y_min_vector)
    
    def get_zmin_center(self):
        return get_midpoint(self.min_vector, self.opposite_z_min_vector)
    
    def get_zmax_center(self):
        return get_midpoint(self.max_vector, self.opposite_z_max_vector)
    
    def get_longest_two_axis_vectors(self):
        """
        get the two longest vectors of a single axis
        This can help when automatically placing joints
        """
        
        x_values = self.get_xmax_center(), self.get_xmin_center()
        xdistance = get_distance(x_values[0], x_values[1])
        
        y_values = self.get_ymax_center(), self.get_ymin_center()
        ydistance = get_distance(y_values[0], y_values[1])
        
        z_values = self.get_zmax_center(), self.get_zmin_center()
        zdistance = get_distance(z_values[0], z_values[1])
        
        distances = {'x':xdistance,'y':ydistance,'z':zdistance}
        
        greatest = 0
        axis = None
        
        for key in distances:
            
            distance = distances[key]
            
            if distance > greatest:
                greatest = distance
                axis = key
        
        if axis:
            if axis == 'x':
                return x_values 
            if axis == 'y':
                return y_values
            if axis == 'z':
                return z_values
            
    def get_size(self):
        
        return get_distance(self.min_vector, self.max_vector)
    
    def get_size_no_y(self):
        
        min_vector = (self.min_vector[0],0,self.min_vector[2])
        max_vector = (self.max_vector[0],0,self.max_vector[2])
        
        return get_distance(min_vector, max_vector)
    

class Variable(object):
    """
    Simple base class for variables on a node.
    
    Args:
        name (str): The name of the variable.
    """
    
    def __init__(self, name = 'empty' ):
        
        self.name = name
        self.value = 0
        self.node = None
    
    def set_node(self, node_name):
        """
        Set the node to work on.
        
        Args:
            node_name (str)
        """
        self.node = node_name
    
    def set_name(self, name):
        """
        Set the name of the variable.
        
        Args:
            name (str): The name to give the variable.
        """
        
        self.name = name
    
    def set_value(self, value):
        """
        Set the value that the variable holds.
        
        Args:
            value
        """
        self.value = value
        
    def create(self, node):
        return
    
    def delete(self, node):
        return

class Part(object):
    
    def __init__(self, name):
        
        self.name = name
        
    def _set_name(self, name):
        
        self.name = name
        
    def create(self):
        pass
    
    def delete(self):
        pass

#def hard_light_two_percents(percent1, percent2):
#    
#    value = percent1 < 128 ? ( 2 * percent2 * percent1 ) / 255 
#                 : 255 - ( ( 2 * ( 255 - percent2 ) * ( 255 - percent1 ) ) / 255

def vector_multiply(vector, value):
    """
    
    Args:
        vector (list): 3 value list
        value (float): value to multiply the vector by
        
    Return:
        list: 3 value list
    """
    result = [vector[0] * value, vector[1] * value, vector[2] * value]
    
    return result

def vector_divide(vector, value):
    """
    
    Args:
        vector (list): 3 value list
        value (float): value to divide the vector by
        
    Return:
        list: 3 value list
    """
    result = [vector[0] / value, vector[1] / value, vector[2] / value]
    
    return result

def vector_magnitude(vector):
    """
    Get the magnitude of a vector.  
    Good to see if there is any distance before doing a full distance calculation.
    
    Args:
        vector (list): 3 value list
        value (float): value to divide the vector by
    
    Return:
        float:
    """    
    magnitude = math.sqrt(vector[0]**2 + vector[1]**2 + vector[2] ** 2)
    
    return magnitude

def vector_add(vector1, vector2):
    """
    Args:
        vector1 (list): 3 value list
        vector2 (list): 3 value list
        
    Return:
        list: 3 value list
    """
    return [ vector1[0] + vector2[0], vector1[1] + vector2[1], vector1[2] + vector2[2] ]

def vector_sub(vector1, vector2):
    """
    Args:
        vector1 (list): 3 value list
        vector2 (list): 3 value list
        
    Return:
        list: 3 value list
    """
    return [ vector1[0] - vector2[0], vector1[1] - vector2[1], vector1[2] - vector2[2] ]

def vector_cross(vector1, vector2, normalize = True):
    """
    Args:
        vector1 (list): 3 value list
        vector2 (list): 3 value list
        normalize (bool): make the result a unit vector that has values from 0 - 1
        
    Return:
        list: 3 value list
    """
    result = [vector1[1]*vector2[2] - vector1[2]*vector2[1],
              vector1[2]*vector2[0] - vector1[0]*vector2[2],
              vector1[0]*vector2[1] - vector1[1]*vector2[0]]

    if normalize == True:
        result = vector_divide(result, vector_magnitude(result))

    return result

def rotate_x_at_origin(vector, value, value_in_radians = False):
    """
    Rotate a vector around its x axis.
    
    Args:
        vector (list): 3 value list
        value (float): amount to rotate
        value_in_radians (bool): If the value is in radians, if not in degrees.
        
    Return:
        list: 3 value list that is the result of the rotation.
    """
    if not value_in_radians:
        value = math.radians(value)
    
    x = vector[0]
    y = ( vector[1]*math.cos(value) ) - ( vector[2]*math.sin(value) )
    z = ( vector[1]*math.sin(value) ) + ( vector[2]*math.cos(value) )
    
    
    return [x,y,z]

def rotate_y_at_origin(vector, value, value_in_radians = False):
    """
    Rotate a vector around its y axis.
    
    Args:
        vector (list): 3 value list
        value (float): amount to rotate
        value_in_radians (bool): If the value is in radians, if not in degrees.
        
    Return:
        list: 3 value list that is the result of the rotation.
    """
    if not value_in_radians:
        value = math.radians(value)
    
    x = ( vector[0]*math.cos(value) ) + ( vector[2]*math.sin(value) )
    y = vector[1]
    z = ( -(vector[0]*math.sin(value)) ) + ( vector[2]*math.cos(value) )
    
    
    return [x,y,z]

def rotate_z_at_origin(vector, value, value_in_radians = False):
    """
    Rotate a vector around its z axis.
    
    Args:
        vector (list): 3 value list
        value (float): amount to rotate
        value_in_radians (bool): If the value is in radians, if not in degrees.
        
    Return:
        list: 3 value list that is the result of the rotation.
    """
    if not value_in_radians:
        value = math.radians(value)
    
    x = ( vector[0]*math.cos(value) ) - ( vector[1]*math.sin(value) )
    y = ( vector[0]*math.sin(value) ) + ( vector[1]*math.cos(value) )
    z = vector[2]
    
    return [x,y,z]

def get_axis_vector(axis_name, offset = 1):
    """
    Convenience. Good for multiplying against a matrix.
    
    Args:
        axis_name (str): 'X' or 'Y' or 'Z'
        
    Returns:
        tuple: vector eg. (1,0,0) for 'X', (0,1,0) for 'Y' and (0,0,1) for 'Z'
    """
    if axis_name == 'X':
        return (offset,0,0)
    
    if axis_name == 'Y':
        return (0,offset,0)
    
    if axis_name == 'Z':
        return (0,0,offset)

def fade_sine(percent_value):
    
    input_value = math.pi * percent_value
    
    return math.sin(input_value)

def fade_cosine(percent_value):
    
    percent_value = math.pi * percent_value
    
    percent_value = (1 - math.cos(percent_value)) * 0.5
    
    return percent_value

def fade_smoothstep(percent_value):
    
    percent_value = percent_value * percent_value * (3 - 2 * percent_value)
    
    return percent_value

def fade_sigmoid(percent_value):
    
    if percent_value == 0:
        return 0
    
    if percent_value == 1:
        return 1
    
    input_value = percent_value * 10 + 1
    
    return ( 2 / (1 + (math.e**(-0.70258*input_value)) ) ) -1 
    
def set_percent_range(percent_value, new_min, new_max):

    min_value = 0
    max_value = 1

    value = ( (new_max-new_min) * (percent_value-min_value) / (max_value-min_value) ) + new_min
    
    return value

def lerp(number1, number2, weight = 0.5):
    """
    interpolate between number1 and number2 based on a 0-1 weight value
    """
    return (1 - weight) * number1 + weight * number2;

def remap_value(value, old_min, old_max, new_min, new_max):
    
    return new_min + (value - old_min) * (new_max - new_min)/(old_max - old_min )
    

def get_distance(vector1, vector2):
    """
    Get the distance between two vectors.
    
    Args:
        vector1 (list): eg. [0,0,0] vector
        vector2 (list): eg. [0,0,0] vector
        
    Returns:
        float: The distance between the two vectors.
    """
    vector1 = Vector(vector1)
    vector2 = Vector(vector2)
    
    vector = vector1 - vector2
    
    dist = vector()
    
    return math.sqrt( (dist[0] * dist[0]) + (dist[1] * dist[1]) + (dist[2] * dist[2]) )

def get_distance_2D(vector1_2D, vector2_2D):
    """
    Get the distance between two 2D vectors.
    
    Args:
        vector1_2D (list): eg. [0,0] vector
        vector2_2D (list): eg. [0,0] vector
        
    Returns:
        float: The distance between the two 2D vectors.
    """
    dist = vector1_2D[0] - vector2_2D[0], vector1_2D[1] - vector2_2D[1]

    return get_magnitude_2D(dist)    
    
def get_magnitude_2D(vector_2D):
    """
    Args:
        vector_2D (list): eg [0,0] vector
        
    Returns:
        float: The magnitude of the vector.
    """
    return math.sqrt( (vector_2D[0] * vector_2D[0]) + (vector_2D[1] * vector_2D[1]) )

def get_dot_product(vector1, vector2):
    """
    Get the dot product of two vectors.  Good for calculating angles.
    
    Args:
        vector1 (list): eg. [0,0,0] vector
        vector2 (list): eg. [0,0,0] vector
        
    Returns:
        float: The dot product between the two vectors.
    """
    return (vector1.x * vector2.x) + (vector1.y * vector2.y) + (vector1.z * vector2.z)

def get_dot_product_2D(vector1_2D, vector2_2D):
    """
    Get the dot product of two 2D vectors.  Good for calculating angles.
    
    Args:
        vector1_2D (list): eg. [0,0] vector
        vector2_2D (list): eg. [0,0] vector
        
    Returns:
        float: The dot product between the two 2D vectors.
    """
    return (vector1_2D.x * vector2_2D.x) + (vector1_2D.y * vector2_2D.y)
    
def get_average(numbers):
    """
    Args:
        numbers (list): A list of floats.
        
    Returns:
        float: The average of the floats in numbers list.
    """
    
    total = 0.0
    
    for number in numbers:
        total += number
        
    return total/ len(numbers)


def get_midpoint(vector1, vector2):
    """
    Get the mid vector between two vectors.
    
    Args:
        vector1 (list): eg. [0,0,0] vector
        vector2 (list): eg. [0,0,0] vector
        
    Returns:
        list: eg. [0,0,0] the midpoint vector between vector1 and vector2
    """
    values = []
    
    for inc in range(0, 3):
        values.append( get_average( [vector1[inc], vector2[inc] ]) )
    
    return values

def get_inbetween_vector(vector1, vector2, percent = 0.5):
    """
    Get a vector inbetween vector1 and vector2 at the percent
    
    Args:
        vector1 (list): eg. [0,0,0] vector
        vector2 (list): eg. [0,0,0] vector
        percent (float): The percent the vector should be between vector1 and vector2. 
        0 percent will be exactly on vector1. 
        1 percent will be exactly on vector2. 
        0.5 percent will be exactly the midpoint between vector1 and vector2.
        
    Returns:
        list: eg. [0,0,0] the vector that represents the vector at the percentage between vector1 and vector2
    """
    vector1 = Vector(vector1)
    vector2 = Vector(vector2)
    percent = 1 - percent

    vector = ((vector1 - vector2) * percent) + vector2
    
    return vector()

def get_simple_center_vector(list_of_vectors):
    
    #needs to be tested
    
    vector_count = list_of_vectors
    
    vector_sum = Vector(0,0,0)
    
    for vector in list_of_vectors:
        new_vector = Vector(*vector)
        
        vector_sum += new_vector
        
    simple_center_vector = vector_sum/vector_count
    
    return simple_center_vector

def is_the_same_number(number1, number2, tolerance = 0.00001):
    
    if abs(number1 - number2) < tolerance:
        return True
    
    return False



def convert_to_sequence(variable, sequence_type = list):
    """
    Easily convert to a sequence. 
    If variable is already of sequence_type, pass it through.
    If variable is a list and sequence_type is tuple, convert to tuple.
    If variable is a tuple and sequence_type is list, convert to list.
    If variable is not a list or tuple, than create a sequence of sequence type.
    
    Basically insures that a variable is a list or a tuple.
    
    Args:
    
        variable: Any variable.
        sequence_type: Can either be python list or python tuple. Needs to be the type ojbect, which means pass it list or tuple not as a string.
        
    Returns:
        list, tuple: Returns list or tuple depending on the sequence_type.
    """
    
    if type(variable) == sequence_type:
        return variable
        
    if type(variable) == list and sequence_type == tuple:
        variable = tuple(variable)
        return variable
    
    if type(variable) == tuple and sequence_type == list:
        variable = list(variable)
        return variable
        
    
    if type(variable) != sequence_type:
        if not variable and variable != 0:
            if sequence_type == list:
                return []
            if sequence_type == tuple:
                return ()
        else:    
            if sequence_type == list:
                return [variable]
            if sequence_type == tuple:
                return (variable)
    
    return variable

def line_side(start_vector, end_vector, position_vector):
    """
    Find out what side a position_vector is on given a line defined by start_vector and end_vector.
    
    Args:
        start_vector (list): eg. [0,0,0] vector\
        end_vector (list): eg. [0,0,0] vector
        position_vector (list): eg. [0,0,0] vector
        
    Returns:
        float: If positive it's on one side of the line, if negative its on the other side.
    """
    
    return ((end_vector.x - start_vector.x)*(position_vector.y - start_vector.y) - (end_vector.y - start_vector.y)*(position_vector.x - start_vector.x)) > 0


def closest_percent_on_line_3D(start_vector, end_vector, position_vector, clamp = True):
    """
    Get how far a vector is on a line.  
    If the vector is on start_vector, return 0. 
    If vector is on end vector, return 1. 
    If vector is half way between start and end return 0.5. 
    """
    
    start_to_position = position_vector - start_vector
    start_to_end = end_vector - start_vector
    
    start_to_end_value = start_to_end.x*start_to_end.x + start_to_end.y*start_to_end.y + start_to_end.z*start_to_end.z
    start_to_position_value = start_to_position.x*start_to_end.x + start_to_position.y*start_to_end.y + start_to_position.z*start_to_end.z
    
    percent = float(start_to_position_value)/float(start_to_end_value)

    

    if clamp:
        
        if percent < 0.0:
            percent = 0.0
        if percent > 1:
            percent = 1.0
            
    return percent

def closest_percent_on_line_2D(start_vector, end_vector, position_vector, clamp = True):
    """
    Get how far a vector is on a line.  
    If the vector is on start_vector, return 0. 
    If vector is on end vector, return 1. 
    If vector is half way between start and end return 0.5. 
    """
    start_to_position = position_vector - start_vector
    start_to_end = end_vector - start_vector
    
    start_to_end_value = start_to_end.x*start_to_end.x + start_to_end.y*start_to_end.y
    start_to_position_value = start_to_position.x*start_to_end.x + start_to_position.y*start_to_end.y
    
    percent = float(start_to_position_value)/float(start_to_end_value)

    if clamp:
        
        if percent < 0.0:
            percent = 0.0
        if percent > 1:
            percent = 1.0
            
    return percent
            
def closest_point_to_line_2D(start_vector, end_vector, position_vector, clamp = True, return_percent = False):
    
    start_to_position = position_vector - start_vector
    start_to_end = end_vector - start_vector
    
    start_to_end_value = start_to_end.x*start_to_end.x + start_to_end.y*start_to_end.y
    other_value = start_to_position.x*start_to_end.x + start_to_position.y*start_to_end.y
    
    percent = float(other_value)/float(start_to_end_value)

    if clamp:
        
        if percent < 0.0:
            percent = 0.0
        if percent > 1:
            percent = 1.0    

    closest_vector = start_vector + start_to_end * percent

    if not return_percent:
        return closest_vector
    if return_percent:
        return closest_vector, percent 

def uv_to_udim(u, v):
    number = int( 1000+(u+1)+(v*10) )
    
    return number

#--- time

def convert_number_to_month(month_int):
    
    months = ['January', 
              'February', 
              'March', 
              'April', 
              'May', 
              'June', 
              'July', 
              'August',
              'September',
              'October',
              'November',
              'December']
    
    month_int -= 1
    
    if month_int < 0 or month_int > 11:
        return
    
    return months[month_int]

def get_current_time(date_and_time = True):
    
    mtime = time.time() 
    
    date_value = datetime.datetime.fromtimestamp(mtime)
    
    hour = str(date_value.hour)
    minute = str(date_value.minute)
    second = date_value.second
    
    second = str( int(second) )
    
    if len(hour) == 1:
        hour = '0'+hour
    if len(minute) == 1:
        minute = '0'+minute
    if len(second) == 1:
        second = second + '0'

    time_value = '%s:%s:%s' % (hour,minute,second)

    if not date_and_time:
        return time_value

    if date_and_time:
        
        year = date_value.year
        month = date_value.month
        day = date_value.day
        return '%s-%s-%s %s' % (year,month,day,time_value)

def get_current_date():
    mtime = time.time() 
    date_value = datetime.datetime.fromtimestamp(mtime)
    year = date_value.year
    month = date_value.month
    day = date_value.day
    
    return '%s-%s-%s' % (year,month,day)

#--- strings

class FindUniqueString(object):
    
    def __init__(self, test_string):
        self.test_string = test_string
        self.increment_string = None
        self.padding = 0
    
    def _get_scope_list(self):
        return []
    
    def _format_string(self, number):
        
        if number == 0:
            number = 1
        
        exp = search_last_number(self.test_string)
        
        if self.padding:
            number = str(number).zfill(self.padding)
        
        if exp:
            
            self.increment_string = '%s%s%s' % (self.test_string[:exp.start()], number, self.test_string[exp.end():])
            
        if not exp:
            split_dot = self.test_string.split('.')
            
            if len(split_dot) > 1:
                split_dot[-2] += str(number)
                
                self.increment_string = string.join(split_dot, '.')
                
            if len(split_dot) == 1:
                self.increment_string = '%s%s' % (self.test_string, number)
    
    def _get_number(self):
        
        return get_end_number(self.test_string)
        
    def _search(self):
        
        number = self._get_number()
        
        self.increment_string = self.test_string
        
        unique = False
        
        while not unique:
            
            scope = self._get_scope_list()
            
            if not scope:
                unique = True
                continue
            
            if not self.increment_string in scope:
                unique = True
                continue
            
            if self.increment_string in scope:
                
                if not number:
                    number = 0
                
                self._format_string(number)
                
                number += 1
                unique = False
                
                continue
            
        return self.increment_string
    
    def set_padding(self, int_value):
        self.padding = int_value
    
    def get(self):
        return self._search()
    
                
def get_first_number(input_string, as_string = False):
    found = re.search('[0-9]+', input_string)
    
    if found:
        number_str = found.group()
        
        if as_string:
            return number_str
        
        number = int(number_str)
        
        return number
        
def get_last_number(input_string):
    
    search = search_last_number(input_string)
    
    if not search:
        return None
    
    found_string = search.group()
    
    number = None
    
    if found_string:
        number = int(found_string)
    
    return number
        
def get_last_letter(input_string):
    
    search = search_last_letter(input_string)
    
    if not search:
        return None
    
    found_string = search.group()
    
    return found_string

def get_end_number(input_string, as_string = False):
    """
    Get the number at the end of a string.
    
    Args:
        input_string (str): The string to search for a number.
    
    Returns:
        int: The number at the end of the string.
    """
    number = re.findall('\d+', input_string)
    
    if number:
        if type(number) == list:
            number = number[0]
            
        if as_string:
            return number
            
        number = int(number)
    
    if number == []:
        number = 1
    
    return number

def get_trailing_number(input_string, as_string = False, number_count = -1):
    """
    Get the number at the very end of a string. If number not at the end of the string return None.
    """
    
    if not input_string:
        return
    
    number = '\d+'
    
    if number_count > 0:
        number = '\d' * number_count
    
    group = re.match('([a-zA-Z_0-9]+)(%s$)' % number, input_string)
    
    if group:
        number = group.group(2)
        
        if as_string:
            return number
        
        if not as_string:
            return int(number)



def search_first_number(input_string):

    
    expression = re.compile('[0-9]+')
    return expression.search( input_string)
    
def search_last_number(input_string):
    """
    Get the last number in a string.
    
    Args:
        input_string (str): The string to search for a number.
    
    Returns:
        int: The last number in the string.
    """
    expression = re.compile('(\d+)(?=(\D+)?$)')
    return expression.search( input_string)


def search_last_letter(input_string):
    """
    Get the last letter in a string.
    
    Args:
        input_string (str): The string to search for a number.
    
    Returns:
        int: The last number in the string.
    """
    
    match = re.findall('[_a-zA-Z]+', input_string)
    if match:
        return match[-1][-1]

def replace_last_number(input_string, replace_string):
    """
    Replace the last number with something.
    
    Args:
        input_string (str): A string to search for the last number.
        replace_string (str): The string to replace the last number with.
        
    Returns:
        str: The new string after replacing.
    """
    
    replace_string = str(replace_string)
    
    expression = re.compile('(\d+)(?=(\D+)?$)')
    search = expression.search(input_string)

    if not search:
        return input_string + replace_string
    
    #count = len(search.group())
    
    #replace_count = len(replace_string)
    
    #if replace_count == 1:
    #    replace_string *= count
    
    #if replace_count:
    return input_string[:search.start()] + replace_string + input_string[search.end():]


def increment_first_number(input_string):
    
    search = search_first_number(input_string)

    if search:
        new_string = '%s%s%s' % (
                                 input_string[ 0 : search.start()], 
                                 int(search.group()) + 1,
                                 input_string[ search.end():]
                                 )
    
    if not search:
        new_string = input_string + '_1'
    
    return new_string

def increment_last_number(input_string):
    """
    Up the value of the last number by 1.
    
    Args:
        input_string (str): The string to search for the last number.
        
    Returns:
        str: The new string after the last number is incremented.
    """
    search = search_last_number(input_string)
    
    if search:
        new_string = '%s%s%s' % (
                                 input_string[ 0 : search.start()], 
                                 int(search.group()) + 1,
                                 input_string[ search.end():]
                                 )
    
    if not search:
        new_string = input_string + '1'
    
    return new_string



def find_special(pattern, string_value, position_string):
    """
    Args:
        pattern (str): A regular expression pattern to search for.
        string_value (str): The string to search in.
        position_string (str): 'start','end','first','last','inside' Where the pattern should search.
        
    Returns:
        tuple: (start_int, end_int) The start and end index of the found pattern. Returns (None,None) if nothing found.
    """
    
    char_count = len(string_value)
    
    found_iter = re.finditer( pattern, string_value)
    
    found = []
    index_start = None
    index_end = None
    
    for item in found_iter:
        found.append(item)
    
    if not found:
        return None, None
        
    if position_string == 'end':
        index_start = found[-1].start()
        index_end = found[-1].end()
        
        if index_end > char_count or index_end < char_count:
            return None, None
        
        return index_start, index_end
        
    if position_string == 'start':
        index_start = found[0].start()
        index_end = found[0].end()
        
        if index_start != 0:
            return None, None

        return index_start, index_end

    if position_string == 'first':
        index_start = found[0].start()
        index_end = found[0].end()
        
        return index_start, index_end
        
    if position_string == 'last':
        index_start = found[-1].start()
        index_end = found[-1].end()
        
        return index_start, index_end
        
    if position_string == 'inside':
        
        for match in found:
            start_index = match.start()
            end_index = match.end()
            
            if start_index == 0:
                continue
            if end_index > char_count:
                continue
            
            break
            
        index_start = start_index
        index_end = end_index
            
        return index_start, index_end

def replace_string(string_value, replace_string, start, end):
    
    first_part = string_value[:start]
    second_part = string_value[end:]
    
    return first_part + replace_string + second_part

def replace_string_at_end(line, string_to_replace, replace_string):
    
    m = re.search('%s$' % string_to_replace, line)
    if not m:
        return
    
    start = m.start(0)
    end = m.end(0)
    
    new_line = line[:start] + replace_string + line[end:]
    
    return new_line

def replace_string_at_start(line, string_to_replace, replace_string):
    
    m = re.search('^%s' % string_to_replace, line)
    if not m:
        return
    
    start = m.start(0)
    end = m.end(0)
    
    new_line = line[:start] + replace_string + line[end:]
    
    return new_line

def clean_file_string(string):
    
    if string == '/':
        return '_'
    
    string = string.replace('\\', '_')
    
    return string

def clean_name_string(string_value, clean_chars = '_', remove_char = '_'):
    
    string_value = re.sub('^[^A-Za-z0-9%s]+' % clean_chars, '', string_value)
    string_value = re.sub('[^A-Za-z0-9%s]+$' % clean_chars, '', string_value)
    string_value = re.sub('[^A-Za-z0-9]', remove_char, string_value)
    
    if not string_value:
        string_value = remove_char
    
    return string_value


def show_list_to_string(*args):

    try:
        if args == None:
            return 'None'
        
        if not args:
            return ''
            
        new_args = []
        
        for arg in args:
            if arg != None:
                new_args.append(str(arg))
            
        args = new_args
        
        if not args:
            return ''
        
        string_value = string.join(args)
        
        string_value = string_value.replace('\n', '\t\n')
        if string_value.endswith('\t\n'):
            string_value = string_value[:-2]
            
        return string_value
    except:
        raise(RuntimeError)

def camel_to_underscore(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def show(*args):
    try:
        
        string_value = show_list_to_string(*args)
        log_value = string_value
        
        string_value = string_value.replace('\n', '\nV:\t\t')
        text = 'V:\t\t%s' % string_value
        
        #do not remove 
        print text
        
        record_temp_log('\n%s' % log_value)
    
    except:
        #do not remove
        text = 'V:\t\tCould not show %s' % args
        print text
        record_temp_log('\n%s' % log_value)
        raise(RuntimeError)
        
        
def warning(*args):
    
    try:    
        string_value = show_list_to_string(*args)
        string_value = string_value.replace('\n', '\nV:\t\t')
        
        text = 'V: Warning!\t%s' % string_value
        #do not remove
        if not is_in_maya():
             
            print text 
        if is_in_maya():
            import maya.cmds as cmds
            cmds.warning('V: \t%s' % string_value)
        
        record_temp_log('\nWarning!:  %s' % string_value)
        
    except:
        raise(RuntimeError)
        
def error(*args):
    
    try:    
        string_value = show_list_to_string(*args)
        string_value = string_value.replace('\n', '\nV:\t\t')
        #do not remove
        
        text = 'V: Error!\t%s' % string_value 
        print text
        
        record_temp_log('\n%s' % string_value)
        
    except:
        raise(RuntimeError)
    

#--- rigs

def is_left(side):
    
    patterns = ['L','l','Left','left','lf']
    
    if str(side) in patterns:
        return True
    
def is_right(side):
    
    patterns = ['R','r','Right','right','rt']
    
    if str(side) in patterns:
        return True
    
    
def is_center(side):
    patterns = ['C','c','Center','ct', 'center', 'middle', 'm']
    
    if str(side) in patterns:
        return True
    

def split_side_negative_number(name):
    
    last_number = get_trailing_number(name, as_string = True, number_count = 2)
    
    negative = None
    side = None
    
    if last_number:
        name = name[:-2]
    
    if name.endswith('N'):
        negative = 'N'
        name = name[:-1]
    
    if name.endswith('L') or name.endswith('R'):
        side = name[-1]
        name = name[:-1]
    
    return name, side, negative, last_number 

def find_possible_combos(names, sort = False, one_increment = False):
        
        if not names:
            return []
        
        if sort:
            names.sort() 
        
        if names:         
            name_count = len(names)
            
            found = []
            
            if name_count > 1:
            
                for inc in range(0, name_count):
                    next_inc = inc+1
                    
                    if next_inc < name_count:             
                                            
                        for inc2 in range(next_inc, name_count):
                            first_name = names[inc]
                            second_name = names[inc2]
                            
                            if first_name == '%sN' % second_name:
                                continue
                            
                            if second_name == '%sN' % first_name:
                                continue
                            
                            name_combo = string.join( [names[inc],names[inc2]], '_' )                    
                            found.append(name_combo)
                                                      
                            sub_names = names[inc2:]             
                            
                            if len(sub_names) > 1:
                                found_sub_combos = find_possible_combos(names[inc2:], False, True)                          
                                                                                      
                                for combo in found_sub_combos:
                                    sub_name_combo = string.join( [names[inc], combo], '_')                              
                                    
                                    found.append(sub_name_combo)
                                    
                    if one_increment:
                        return found
                
                return found



#--- sorting


class QuickSort(object):
    """
    Really fast method for sorting.
    """
    def __init__(self, list_of_numbers):
        
        self.list_of_numbers = list_of_numbers
        self.follower_list = []
        
    def _sort(self, list_of_numbers, follower_list = []):
        
        less = []
        equal = []
        greater = []
        
        if follower_list:
            less_follow = []
            equal_follow = []
            greater_follow = []
        
        count = len(list_of_numbers)
    
        if count > 1:
            pivot = list_of_numbers[0]
            
            for inc in xrange(0, count):
                
                value = list_of_numbers[inc]
                if follower_list:
                    follower_value = follower_list[inc]
                
                if value < pivot:
                    less.append(value)
                    if follower_list:
                        less_follow.append(follower_value)
                if value == pivot:
                    equal.append(value)
                    if follower_list:
                        equal_follow.append(follower_value)
                if value > pivot:
                    greater.append(value)
                    if follower_list:
                        greater_follow.append(follower_value)
                    
                    
            
            if not self.follower_list:
                return self._sort(less)+equal+self._sort(greater)  
            if self.follower_list:
                
                less_list_of_numbers, less_follower_list = self._sort(less, less_follow)
                greater_list_of_numbers, greater_follower_list = self._sort(greater, greater_follow)  
                
                list_of_numbers = less_list_of_numbers + equal + greater_list_of_numbers
                follower_list = less_follower_list + equal_follow + greater_follower_list
                
                return list_of_numbers, follower_list
                        
        else:  
            if not self.follower_list:
                return list_of_numbers
            if self.follower_list:
                return list_of_numbers, follower_list
        
    def set_follower_list(self, list_of_anything):
        """
        This list much match the length of the list given when the class was initialized.
        """
        
        self.follower_list = list_of_anything
        
    def run(self):
        """
        If no follower list supplied, return number list sorted: list
        If follower list supplied, return number list and follower list: (list, list)
        """
        
        if not self.list_of_numbers:
            return
        
        if self.follower_list and len(self.follower_list) != len(self.list_of_numbers):
            return
        
        return self._sort(self.list_of_numbers, self.follower_list)
        

def encode(key, clear):
    enc = []
    for i in range(len(clear)):
        key_c = key[i % len(key)]
        enc_c = chr((ord(clear[i]) + ord(key_c)) % 256)
        enc.append(enc_c)
    return base64.urlsafe_b64encode("".join(enc))

def decode(key, enc):
    dec = []
    enc = base64.urlsafe_b64decode(enc)
    for i in range(len(enc)):
        key_c = key[i % len(key)]
        dec_c = chr((256 + ord(enc[i]) - ord(key_c)) % 256)
        dec.append(dec_c)
    return "".join(dec)


def print_python_dir_nicely(python_object):
    
    stuff = dir(python_object)
    
    for thing in stuff:
        exec('print thing, ":", python_object.%s' % thing)

def split_line(line, splitter = ';', quote_symbol = '"'):
    """
    This will split a line, ignoring anything inside quotes
    #re.split(';(?=(?:[^"]*"[^"]*")*[^"]*$)
    """
    
    split_regex = '%s(?=(?:[^%s]*%s[^%s]*%s)*[^%s]*$)' % (splitter, quote_symbol, quote_symbol, quote_symbol, quote_symbol, quote_symbol)
    return re.split(split_regex, line)

def replace_vtool(path_to_vtool):
    """
    Meant to have vtool look at a different path to load
    """
    
    unload_vtool()
    sys.path.insert(0, path_to_vtool)

def unload_vtool():
    """
    Removed currently sourced modules.  
    This allows you to insert a custom path at the start of the sys.path and load vetala from there.
    """
    
    if is_in_maya():
        from vtool.maya_lib import ui_core
        ui_core.delete_scene_script_jobs()
    
    modules = sys.modules

    found = []
    
    module_keys = modules.keys()
    
    for module in module_keys:
        
        if not module in modules:
            continue
        module_inst = modules[module]    
        if not module_inst:
            continue    
        if not hasattr(module_inst, '__file__'):
            continue        
        #module_path = module_inst.__file__
        if module.startswith('vtool'):
            
            found.append(module)
        
    for key in found:
        show('Removing vtool module %s' % key)
        modules.pop(key)