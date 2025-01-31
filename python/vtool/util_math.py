# Copyright (C) 2024 Louis Vottero louis.vot@gmail.com    All rights reserved.

from __future__ import print_function
from __future__ import absolute_import

import math


def clampf(minimum, x, maximum):
    """
    Clamps a number between a minimum and maximum provided value.

    :param minimum: float or int type minimum lower bound
    :param x: value that on wants to clamp between a supplied min or maximum value.
    :param maximum: float or int type maximum upper bound
    :return: float or int type clamped value
    """
    return max(minimum, min(x, maximum))


class VectorBase(object):
    pass


class Vector2D(object):

    def __init__(self, x=1.0, y=1.0):
        self.x = None
        self.y = None

        if isinstance(x, (list, tuple)):
            self.x = x[0]
            self.y = x[1]
        elif isinstance(x, (float, int)):
            self.x = x
            self.y = y

        self.magnitude = None

    def _add(self, value):
        if isinstance(value, (float, int)):
            return Vector2D(self.x + value, self.y + value)
        elif type(self) is type(value):
            return Vector2D(value.x + self.x, value.y + self.y)
        elif isinstance(value, (list, tuple)):
            return Vector2D(self.x + value[0], self.y + value[1])

    def _sub(self, value):
        if isinstance(value, (float, int)):
            return Vector2D(self.x - value, self.y - value)
        elif type(self) is type(value):
            return Vector2D(self.x - value.x, self.y - value.y)
        elif isinstance(value, (list, tuple)):
            return Vector2D(self.x - value[0], self.y - value[1])

    def _rsub(self, value):
        if isinstance(value, (float, int)):
            return Vector2D(value - self.x, value - self.y - value)
        elif type(self) is type(value):
            return Vector2D(value.x - self.x, value.y - self.y)
        elif isinstance(value, (list, tuple)):
            return Vector2D(value[0] - self.x, value[1] - self.y)

    def _mult(self, value):
        if isinstance(value, (float, int)):
            return Vector2D(self.x * value, self.y * value)
        elif type(self) is type(value):
            return Vector2D(value.x * self.x, value.y * self.y)
        elif isinstance(value, (list, tuple)):
            return Vector2D(self.x * value[0], self.y * value[1])

    def _divide(self, value):
        if isinstance(value, (float, int)):
            return Vector2D(self.x / value, self.y / value)
        elif type(self) is type(value):
            return Vector2D(value.x / self.x, value.y / self.y)
        elif isinstance(value, (list, tuple)):
            return Vector2D(self.x / value[0], self.y / value[1])

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
        return [self.x, self.y]

    def __div__(self, value):
        return self._divide(value)

    def _reset_data(self):
        self.magnitude = None

    def normalize(self, in_place=False):
        if not self.magnitude:
            self.get_magnitude()
        vector = self._divide(self.magnitude)
        if in_place:
            self.x = vector.x
            self.y = vector.y
            self._reset_data()
        else:
            return vector

    def get_vector(self):
        return [self.x, self.y]

    def get_magnitude(self):
        self.magnitude = math.sqrt((self.x * self.x) + (self.y * self.y))
        return self.magnitude

    def get_distance(self, x=0.0, y=0.0):
        other = Vector2D(x, y)
        offset = self - other
        return offset.get_magnitude()


class Vector(object):

    def __init__(self, x=1.0, y=1.0, z=1.0):

        self.x = None
        self.y = None
        self.z = None

        x_test = x
        if isinstance(x_test, list) or isinstance(x_test, tuple):
            self.x = x[0]
            self.y = x[1]
            self.z = x[2]
        elif isinstance(x_test, float) or isinstance(x_test, int):
            self.x = x
            self.y = y
            self.z = z

    def _add(self, value):
        if isinstance(value, float) or isinstance(value, int):
            return Vector(self.x + value, self.y + value, self.z + value)
        elif type(self) is type(value):
            return Vector(value.x + self.x, value.y + self.y, value.z + self.z)
        elif isinstance(value, list):
            return Vector(self.x + value[0], self.y + value[1], self.z + value[2])

    def _sub(self, value):
        if isinstance(value, float) or isinstance(value, int):
            return Vector(self.x - value, self.y - value, self.z - value)
        elif type(self) is type(value):
            return Vector(self.x - value.x, self.y - value.y, self.z - value.z)
        elif isinstance(value, list):
            return Vector(self.x - value[0], self.y - value[1], self.z - value[2])

    def _rsub(self, value):
        if isinstance(value, float) or isinstance(value, int):
            return Vector(value - self.x, value - self.y - value, value - self.z)
        elif type(self) is type(value):
            return Vector(value.x - self.x, value.y - self.y, value.z - self.z)
        elif isinstance(value, list):
            return Vector(value[0] - self.x, value[1] - self.y, value[2] - self.z)

    def _mult(self, value):
        if isinstance(value, float) or isinstance(value, int):
            return Vector(self.x * value, self.y * value, self.z * value)
        elif type(self) is type(value):
            return Vector(value.x * self.x, value.y * self.y, value.z * self.z)
        elif isinstance(value, list):
            return Vector(self.x * value[0], self.y * value[1], self.z * value[2])

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
        return [self.x, self.y, self.z]

    def get_vector(self):
        return [self.x, self.y, self.z]

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

        distances = {'x': xdistance, 'y': ydistance, 'z': zdistance}

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
            elif axis == 'y':
                return y_values
            elif axis == 'z':
                return z_values

    def get_size(self):

        return get_distance(self.min_vector, self.max_vector)

    def get_scale_factor(self):
        return [abs(max_v - min_v) for max_v, min_v in zip(self.max_vector, self.min_vector)]

    def get_size_no_y(self):

        min_vector = (self.min_vector[0], 0, self.min_vector[2])
        max_vector = (self.max_vector[0], 0, self.max_vector[2])

        return get_distance(min_vector, max_vector)

    def is_symmetrical(self, axis='X', tolerance=0.00001):
        found = False
        if axis == 'X' and is_the_same_number(self.min_vector[0], self.max_vector[0] * -1, tolerance):
            found = True
        elif axis == 'Y' and is_the_same_number(self.min_vector[1], self.max_vector[1] * -1, tolerance):
            found = True
        elif axis == 'Z' and is_the_same_number(self.min_vector[2], self.max_vector[2] * -1, tolerance):
            found = True
        return found


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
    elif percent_value == 1:
        return 1

    input_value = percent_value * 10 + 1

    return (2 / (1 + (math.e ** (-0.70258 * input_value)))) - 1


def easeInSine(percent_value):
    t = percent_value
    return math.sin(1.5707963 * t)


def easeInExpo(percent_value):
    t = percent_value
    return (pow(2, 8 * t) - 1) / 255


def easeOutExpo(percent_value, power=2):
    return 1 - pow(power, -8 * percent_value)


def easeOutCirc(percent_value):
    return math.sqrt(percent_value)


def easeOutBack(percent_value):
    return 1 + (- -percent_value) * percent_value * (2.70158 * percent_value + 1.70158)


def easeInOutSine(percent_value):
    t = percent_value
    return 0.5 * (1 + math.sin(math.pi * (t - 0.5)))


def easeInOutQuart(percent_value):
    t = percent_value
    if t < 0.5:
        t *= t
        return 8 * t * t
    else:
        t -= 1
        t *= t
        return 1 - 8 * t * t


def easeInOutExpo(percent_value):
    t = percent_value

    if t < 0.5:
        return (math.pow(2, 16 * t) - 1) / 510
    else:
        return 1 - 0.5 * math.pow(2, -16 * (t - 0.5))


def easeInOutCirc(percent_value):
    t = percent_value
    if t < 0.5:
        return (1 - math.sqrt(1 - 2 * t)) * 0.5
    else:
        return (1 + math.sqrt(2 * t - 1)) * 0.5


def easeInOutBack(percent_value):
    t = percent_value
    if t < 0.5:
        return t * t * (7 * t - 2.5) * 2
    else:
        return 1 + (t - 1) * t * 2 * (7 * t + 2.5)


def set_percent_range(percent_value, new_min, new_max):
    min_value = 0
    max_value = 1

    value = ((new_max - new_min) * (percent_value - min_value) / (max_value - min_value)) + new_min

    return value


def lerp(number1, number2, weight=0.5):
    """
    interpolate between number1 and number2 based on a 0-1 weight value
    """
    return (1 - weight) * number1 + weight * number2


def remap_value(value, old_min, old_max, new_min, new_max):
    return new_min + (value - old_min) * (new_max - new_min) / (old_max - old_min)


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
    return math.sqrt((vector_2D[0] * vector_2D[0]) + (vector_2D[1] * vector_2D[1]))


def get_dot_product(vector1, vector2):
    """
    Get the dot product of two vectors.  Good for calculating angles.
    
    Args:
        vector1 (list): e.g. [0,0,0] vector
        vector2 (list): e.g. [0,0,0] vector
        
    Returns:
        float: The dot product between the two vectors.
    """
    return (vector1.x * vector2.x) + (vector1.y * vector2.y) + (vector1.z * vector2.z)


def get_dot_product_2D(vector1_2D, vector2_2D):
    """
    Get the dot product of two 2D vectors.  Good for calculating angles.
    
    Args:
        vector1_2D (list): e.g. [0,0] vector
        vector2_2D (list): e.g. [0,0] vector
        
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

    return total / len(numbers)


def is_the_same_number(number1, number2, tolerance=0.00001):
    if abs(number1 - number2) < tolerance:
        return True

    return False


def line_side(start_vector, end_vector, position_vector):
    """
    Find out what side a position_vector is on given a line defined by start_vector and end_vector.
    
    Args:
        start_vector (list): e.g. [0,0,0] vector\
        end_vector (list): e.g. [0,0,0] vector
        position_vector (list): e.g. [0,0,0] vector
        
    Returns:
        float: If positive it's on one side of the line, if negative its on the other side.
    """

    return ((end_vector.x - start_vector.x) * (position_vector.y - start_vector.y)
            -(end_vector.y - start_vector.y) * (position_vector.x - start_vector.x)) > 0


def closest_percent_on_line_2D(start_vector, end_vector, position_vector, clamp=True):
    """
    Get how far a vector is on a line.  
    If the vector is on start_vector, return 0. 
    If vector is on end vector, return 1. 
    If vector is halfway between start and end return 0.5.
    """
    start_to_position = position_vector - start_vector
    start_to_end = end_vector - start_vector

    start_to_end_value = start_to_end.x * start_to_end.x + start_to_end.y * start_to_end.y
    start_to_position_value = start_to_position.x * start_to_end.x + start_to_position.y * start_to_end.y

    percent = float(start_to_position_value) / float(start_to_end_value)

    if clamp:
        percent = clampf(0.0, percent, 1.0)
    return percent


def closest_point_to_line_2D(start_vector, end_vector, position_vector, clamp=True, return_percent=False):
    start_to_position = position_vector - start_vector
    start_to_end = end_vector - start_vector

    start_to_end_value = start_to_end.x * start_to_end.x + start_to_end.y * start_to_end.y
    other_value = start_to_position.x * start_to_end.x + start_to_position.y * start_to_end.y

    percent = float(other_value) / float(start_to_end_value)

    if clamp:
        percent = clampf(0.0, percent, 1.0)
    closest_vector = start_vector + start_to_end * percent
    if return_percent:
        return closest_vector, percent
    else:
        return closest_vector

# --- 3D


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


def vector_vector_multiply(vector1, vector2):
    return [vector1[0] * vector2[0], vector1[1] * vector2[1]]


def vector_normalize(vector):
    return vector_divide(vector, vector_magnitude(vector))


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

    Return:
        float:
    """
    magnitude = math.sqrt(vector[0] ** 2 + vector[1] ** 2 + vector[2] ** 2)

    return magnitude


def get_distance(vector1, vector2):
    """
    Get the distance between two vectors.
    
    Args:
        vector1 (list): e.g. [0,0,0] vector
        vector2 (list): e.g. [0,0,0] vector
        
    Returns:
        float: The distance between the two vectors.
    """
    vector1 = Vector(vector1)
    vector2 = Vector(vector2)

    vector = vector1 - vector2

    dist = vector()

    return math.sqrt((dist[0] * dist[0]) + (dist[1] * dist[1]) + (dist[2] * dist[2]))


def get_distance_before_sqrt(vector1, vector2):
    vector1 = Vector(vector1)
    vector2 = Vector(vector2)

    vector = vector1 - vector2

    dist = vector()

    value = (dist[0] * dist[0]) + (dist[1] * dist[1]) + (dist[2] * dist[2])
    return value


def vector_add(vector1, vector2):
    """
    Args:
        vector1 (list): 3 value list
        vector2 (list): 3 value list
        
    Return:
        list: 3 value list
    """
    return [vector1[0] + vector2[0], vector1[1] + vector2[1], vector1[2] + vector2[2]]


def vector_sub(vector1, vector2):
    """
    Args:
        vector1 (list): 3 value list
        vector2 (list): 3 value list
        
    Return:
        list: 3 value list
    """
    return [vector1[0] - vector2[0], vector1[1] - vector2[1], vector1[2] - vector2[2]]


def vector_cross(vector1, vector2, normalize=True):
    """
    Args:
        vector1 (list): 3 value list
        vector2 (list): 3 value list
        normalize (bool): make the result a unit vector that has values from 0 to 1
        
    Return:
        list: 3 value list
    """
    result = [vector1[1] * vector2[2] - vector1[2] * vector2[1],
              vector1[2] * vector2[0] - vector1[0] * vector2[2],
              vector1[0] * vector2[1] - vector1[1] * vector2[0]]

    if normalize == True:
        result = vector_divide(result, vector_magnitude(result))

    return result


def vector_dot_product(vector1, vector2):
    # return vector1[0] * vector2[0] + vector1[1] * vector2[1] + vector1[2] * vector2[2]

    return sum(x * y for x, y in zip(vector1, vector2))


def vector_centroid(vectors):

    sum_coordinates = [sum(vector[i] for vector in vectors) for i in range(3)]
    count = len(vectors)

    centroid = tuple(coord / count for coord in sum_coordinates)

    return centroid


def rotate_x_at_origin(vector, value, value_in_radians=False):
    """
    Rotate a vector around its x-axis.
    
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
    y = (vector[1] * math.cos(value)) - (vector[2] * math.sin(value))
    z = (vector[1] * math.sin(value)) + (vector[2] * math.cos(value))

    return [x, y, z]


def rotate_y_at_origin(vector, value, value_in_radians=False):
    """
    Rotate a vector around its y-axis.
    
    Args:
        vector (list): 3 value list
        value (float): amount to rotate
        value_in_radians (bool): If the value is in radians, if not in degrees.
        
    Return:
        list: 3 value list that is the result of the rotation.
    """
    if not value_in_radians:
        value = math.radians(value)

    x = (vector[0] * math.cos(value)) + (vector[2] * math.sin(value))
    y = vector[1]
    z = (-(vector[0] * math.sin(value))) + (vector[2] * math.cos(value))

    return [x, y, z]


def rotate_z_at_origin(vector, value, value_in_radians=False):
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

    x = (vector[0] * math.cos(value)) - (vector[1] * math.sin(value))
    y = (vector[0] * math.sin(value)) + (vector[1] * math.cos(value))
    z = vector[2]

    return [x, y, z]


def axis_angle(vector, axis_vector, angle, angle_in_radians=False):
    if not angle_in_radians:
        angle = math.radians(angle)

    axis_vector = vector_normalize(axis_vector)
    # vector =  vector_normalize(vector)

    part1 = vector_multiply(vector, math.cos(angle))
    part2 = vector_multiply(vector_multiply(axis_vector, vector_dot_product(vector, axis_vector)),
                            (1 - math.cos(angle)))

    part3 = vector_multiply(vector_cross(axis_vector, vector, False), math.sin(angle))

    result = vector_add(part1, part2)
    result = vector_add(result, part3)

    return result


def get_vector_axis_letter(vector):

    if not vector:
        return

    vector = vector_normalize(vector)

    if vector == [1, 0, 0]:
        return 'X'
    if vector == [0, 1, 0]:
        return 'Y'
    if vector == [0, 0, 1]:
        return 'Z'
    if vector == [-1, 0, 0]:
        return '-X'
    if vector == [0, -1, 0]:
        return '-Y'
    if vector == [0, 0, -1]:
        return '-Z'


def get_axis_vector(axis_name, offset=1):
    """
    Convenience. Good for multiplying against a matrix.
    
    Args:
        axis_name (str): 'X' or 'Y' or 'Z'
        offset (int | float): TODO: Fill in the description.
        
    Returns:
        tuple: vector e.g. (1,0,0) for 'X', (0,1,0) for 'Y' and (0,0,1) for 'Z'
    """
    if axis_name == 'X':
        return offset, 0, 0
    elif axis_name == 'Y':
        return 0, offset, 0
    elif axis_name == 'Z':
        return 0, 0, offset


def get_midpoint(vector1, vector2):
    """
    Get the mid-vector between two vectors.
    
    Args:
        vector1 (list): e.g. [0,0,0] vector
        vector2 (list): e.g. [0,0,0] vector
        
    Returns:
        list: e.g. [0,0,0] the midpoint vector between vector1 and vector2
    """
    values = []

    for inc in range(0, 3):
        values.append(get_average([vector1[inc], vector2[inc]]))

    return values


def get_inbetween_vector(vector1, vector2, percent=0.5):
    """
    Get a vector inbetween vector1 and vector2 at the percent
    
    Args:
        vector1 (list): e.g. [0,0,0] vector
        vector2 (list): e.g. [0,0,0] vector
        percent (float): The percent the vector should be between vector1 and vector2. 
        0 percent will be exactly on vector1. 
        1 percent will be exactly on vector2. 
        0.5 percent will be exactly the midpoint between vector1 and vector2.
        
    Returns:
        list: e.g. [0,0,0] the vector that represents the vector at the percentage between vector1 and vector2
    """
    vector1 = Vector(vector1)
    vector2 = Vector(vector2)
    percent = 1 - percent

    vector = ((vector1 - vector2) * percent) + vector2

    return vector()


def get_simple_center_vector(list_of_vectors):
    # needs to be tested

    vector_count = list_of_vectors

    vector_sum = Vector(0.0, 0.0, 0.0)

    for vector in list_of_vectors:
        new_vector = Vector(*vector)

        vector_sum += new_vector

    # TODO: This will cause an error, no division dunder was defined.
    simple_center_vector = vector_sum / vector_count

    return simple_center_vector


def closest_percent_on_line_3D(start_vector, end_vector, position_vector, clamp=True):
    """
    Get how far a vector is on a line.  
    If the vector is on start_vector, return 0. 
    If vector is on end vector, return 1. 
    If vector is halfway between start and end return 0.5.
    """

    start_to_position = position_vector - start_vector
    start_to_end = end_vector - start_vector

    start_to_end_value = (start_to_end.x * start_to_end.x
                          +start_to_end.y * start_to_end.y
                          +start_to_end.z * start_to_end.z)
    start_to_position_value = (start_to_position.x * start_to_end.x
                               +start_to_position.y * start_to_end.y
                               +start_to_position.z * start_to_end.z)

    percent = float(start_to_position_value) / float(start_to_end_value)

    if clamp:
        percent = clampf(0.0, percent, 1.0)
    return percent


def vector_length(vector):
    return math.sqrt(vector_dot_product(vector, vector))


def vector_power(vector, power=2):
    return [vector[0] ** power, vector[1] ** power, vector[2] ** power]


def angle_between(vector1, vector2, in_degrees=False):
    value = math.acos(vector_dot_product(vector1, vector2) / (vector_length(vector1) * vector_length(vector2)))
    if in_degrees:
        value = math.degrees(value)
        return value

    return value


def vector_project(vector_direction, vector_plane):
    dot_plane = float(vector_dot_product(vector_plane, vector_plane))

    dot = float(vector_dot_product(vector_direction, vector_plane))

    result = vector_multiply(vector_plane, (dot / dot_plane))

    return result


def sphere_min_max_vector(position, radius):

    min_vector = [pos - radius for pos in position]
    max_vector = [pos + radius for pos in position]

    return min_vector, max_vector


def vector_in_min_max_vector(vector, min_vector, max_vector):

    for v, min_v, max_v in zip(vector, min_vector, max_vector):
        if not (min_v <= v <= max_v):
            return False
    return True


def mirror_vector(vector, axis='X'):
    """
    Return the mirrored point across the given axis (X, Y, or Z).
    """
    mirrored = list(vector)
    if axis == 'X':
        mirrored[0] = -mirrored[0]
    elif axis == 'Y':
        mirrored[1] = -mirrored[1]
    elif axis == 'Z':
        mirrored[2] = -mirrored[2]
    return tuple(mirrored)


def mirror_matrix(matrix, axis=[1, 0, 0]):
    axis = [-a if a else 1 for a in axis]

    for i in range(0,16,4):
        print(i)
        matrix[i] *= axis[0]
        matrix[i + 1] *= axis[1]
        matrix[i + 2] *= axis[2]

    return matrix

