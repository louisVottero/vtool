# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

import re
import math
import time
import string
import datetime

#decorators

def try_pass(function):
    def wrapper(*args, **kwargs):
        
        return_value = None
                
        try:
            return_value = function(*args, **kwargs)
        except Exception, e:
            show(e)
                    
        return return_value
                     
    return wrapper

class StopWatch(object):
    def __init__(self):
        self.time = None
    
    def start(self):
        
        show('started timer')
        self.time = time.time()
    
    def end(self):
        seconds = time.time()-self.time
        self.time = None
        
        show('end timer: %s seconds' % seconds)
        

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
        
        self.z = None
        
        if type(x) == list:
            self.x = x[0]
            self.y = x[1]
            self.z = x[2]
            
        if type(x) == float or type(x) == int:
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
            return Vector(self.x-value.x, self.y-value.y, self.z-value.z)
        
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
    
class BoundingBox(object):
    def __init__(self, btm_corner_vector, top_corner_vector):
        
        self._load_bounding_box(btm_corner_vector, top_corner_vector)
        
    def _load_bounding_box(self, btm_corner_vector, top_corner_vector):
        self.min_vector = [btm_corner_vector[0], btm_corner_vector[1], btm_corner_vector[2]]
        self.max_vector = [top_corner_vector[0], top_corner_vector[1], top_corner_vector[2]]
        
        self.opposite_min_vector = [top_corner_vector[0], btm_corner_vector[1], top_corner_vector[2]]
        self.opposite_max_vector = [btm_corner_vector[0], top_corner_vector[1], btm_corner_vector[2]]
        
    def get_center(self):
        return get_midpoint(self.min_vector, self.max_vector)
        
    def get_ymax_center(self):
        return get_midpoint(self.max_vector, self.opposite_max_vector)
        
    def get_ymin_center(self):
        return get_midpoint(self.min_vector, self.opposite_min_vector)

class Variable(object):
    
    def __init__(self, name = 'empty' ):
        self.name = name
        self.value = 0
        self.node = None
    
    def set_node(self, node_name):
        self.node = node_name
    
    def set_name(self, name):
        self.name = name
    
    def set_value(self, value):
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
    
    def set_padding(self, int):
        self.padding = int
    
    def get(self):
        return self._search()

class Hierarchy(object):
    
    def __init__(self, top_of_hierarchy):
        self.top_of_hierarchy = top_of_hierarchy
        self.generations = []
        self.branches = []
        
        self._get_hierarchy()
    
    def _get_hierarachy(self):
        self.generations =[]
        self.branches = []
    
    def create_branch(self, name):
        
        branch = Branch(name)
        self.branches.append(branch)
        
        return branch
    
    def get_generation(self, inc):
        pass
    


class Branch(object):
    
    def __init__(self, name):
        self.name = name
        self.parent = ''
        self.children = []        
        
    def add_child(self, branch):
        self.children.append(branch)
    
    def set_children(self, branch_list):
        self.children = branch_list
        
    def set_parent(self, branch):
        self.parent = branch
        

#def hard_light_two_percents(percent1, percent2):
#    
#    value = percent1 < 128 ? ( 2 * percent2 * percent1 ) / 255 
#                 : 255 - ( ( 2 * ( 255 - percent2 ) * ( 255 - percent1 ) ) / 255


def is_in_maya():
    try:
        import maya.cmds as cmds
        return True
    except:
        return False
    
def is_in_nuke():
    try:
        import nuke
        return True
    except:
        return False

def fade_sine(percent_value):
    
    input = math.pi * percent_value
    
    return math.sin(input)

def fade_sigmoid(percent_value):
    
    if percent_value == 0:
        return 0
    
    if percent_value == 1:
        return 1
    
    input = percent_value * 10 + 1
    
    return ( 2 / (1 + (math.e**(-0.70258*input)) ) ) -1 
    

def regular_expression_search(expression_code, input_string):
    
    regular_expression = re.compile(expression_code)
    return  regular_expression.search(input_string)
                
def get_end_number(input_string):
    
    number = re.findall('\d+', input_string)
    
    if number:
        if type(number) == list:
            number = number[0]
            
        number = int(number)
    
    return number

def search_last_number(input_string):
    
    return regular_expression_search('(\d+)(?=(\D+)?$)', input_string)

def replace_last_number(input_string, replace_string):

    expression = re.compile('(\d+)(?=(\D+)?$)')
    search = expression.search(input_string)

    if not search:
        return
    
    count = len(search.group())
    
    replace_count = len(replace_string)
    
    if replace_count == 1:
        replace_string *= count

    return input_string[:search.start()] + replace_string + input_string[search.end():]

    
    
def get_last_number(input_string):
    
    search = search_last_number(input_string)
    
    if not search:
        return 0
    
    found_string = search.group()
    
    number = 0
    
    if found_string:
        number = int(found_string)
    
    return number

def increment_last_number(input_string):
    
    search = search_last_number(input_string)
    
    new_string = '%s%s%s' % (
                             input_string[ 0 : search.start()], 
                             int(search.group()) + 1,
                             input_string[ search.end():]
                             )
    
    return new_string

def get_distance(vector1, vector2):
    
    vector1 = Vector(vector1)
    vector2 = Vector(vector2)
    
    vector = vector1 - vector2
    
    dist = vector()
    
    return math.sqrt( (dist[0] * dist[0]) + (dist[1] * dist[1]) + (dist[2] * dist[2]) )

def get_distance_2D(vector1_2D, vector2_2D):
    
    dist = vector1_2D[0] - vector2_2D[0], vector1_2D[1] - vector2_2D[1]

    return get_magnitude_2D(dist)    
    
def get_magnitude_2D(vector_2D):
    return math.sqrt( (vector_2D[0] * vector_2D[0]) + (vector_2D[1] * vector_2D[1]) )

def get_dot_product(vector1, vector2):
    return (vector1.x * vector2.x) + (vector1.y * vector2.y) + (vector1.z * vector2.z)

def get_dot_product_2D(vector1_2D, vector2_2D):
    
    return (vector1_2D.x * vector2_2D.x) + (vector1_2D.y * vector2_2D.y)
    
def get_average(numbers):
    
    total = 0.0
    
    for number in numbers:
        total += number
        
    return total/ len(numbers)


def get_midpoint(vector1, vector2):
    
    values = []
    
    for inc in range(0, 3):
        values.append( get_average( [vector1[inc], vector2[inc] ]) )
    
    return values

def get_inbetween_vector(vector1, vector2, percent = 0.5):
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

def convert_to_sequence(variable, sequence_type = list):
    if not type(variable) == sequence_type:
        if sequence_type == list:
            return [variable]
        if sequence_type == tuple:
            return (variable)
    
    return variable

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

def line_side(start_vector, end_vector, position_vector):
    return ((end_vector.x - start_vector.x)*(position_vector.y - start_vector.y) - (end_vector.y - start_vector.y)*(position_vector.x - start_vector.x)) > 0

def closest_percent_on_line_2D(start_vector, end_vector, position_vector, clamp = True):
    
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

def clean_string(string):
    
    if string == '/':
        return '_'
    
    string = string.replace('\\', '_')
    
    return string

def show(*args):
    try:
        if not args:
            return
        
        new_args = []
        
        for arg in args:
            if arg != None:
                new_args.append(arg)
            
        args = new_args
        
        if not args:
            return
        
        string_value = string.join(args)
        
        string_value = string_value.replace('\n', '\t\n')
        if string_value.endswith('\t\n'):
            string_value = string_value[:-2]
        
        #do not remove
        print '\t%s' % string_value
    
    except:
        print 'Could not show %s' % args
        
    

    
    