# Copyright (C) 2022 Louis Vottero louis.vot@gmail.com    All rights reserved.

from __future__ import absolute_import

import os

#import util  do not import util, curve is used in util
from . import api
from .. import util, util_file

if util.is_in_maya():
    import maya.cmds as cmds
    import maya.mel as mel

current_path = os.path.split(__file__)[0]

try:
    
    custom_curve_path = util.get_custom('custom_curve_path', '')
    
    if custom_curve_path:
        if util_file.is_dir(custom_curve_path):
            curve_data = util_file.join_path(custom_curve_path, 'curve_data')
            util_file.create_dir(curve_data)
            util.show('Using custom curve directory: %s' % custom_curve_path)
            current_path = custom_curve_path
except:
    util.warning('Could not load custom curves')


class CurveToData(object):
    """
    Convenience for dealing with curve data.
    """
    
    def __init__(self, curve):
        
        curve_shapes = self._get_shapes(curve)
        
        self.curves = []
        self.curve_mobjects = []
        self.curve_functions = []
        
        for curve_shape in curve_shapes:
            
            if not curve_shape:
                util.warning('%s is not a nurbs curve.' % curve_shape)
                continue 
            
            self.curves.append(curve_shape)
            self.curve_mobjects.append( api.nodename_to_mobject(curve_shape) )
            self.curve_functions.append( api.NurbsCurveFunction( self.curve_mobjects[-1] ))
        
    def _get_shapes(self, curve):
        
        curves = util.convert_to_sequence(curve)
        
        curve_shapes = []
        
        for curve in curves:
                
            if not cmds.nodeType(curve) == 'nurbsCurve':
                shapes = cmds.listRelatives(curve, s = True, f  = True)
                
                if shapes:
                    
                    for shape in shapes:
                        if cmds.nodeType(shape) == 'nurbsCurve':
                            if not cmds.getAttr('%s.intermediateObject' % shape):
                                curve_shapes.append( shape )
        
        return curve_shapes
    
    def get_degree(self, index = 0):
        """
        Get the degree of the curve.
        
        Args:
            index (int): The shape index. 0 for first shape, 1 for the second shape, etc...
            
        Returns:
            int: The number of degrees.
        """
        return self.curve_functions[index].get_degree()
        
    def get_knots(self, index = 0):
        """
        Get the degree of the curve.
        
        Args:
            index (int): The shape index. 0 for first shape, 1 for the second shape, etc...
            
        Returns:
            int: The number of degrees.
        """
        return self.curve_functions[index].get_knot_values()
        
    def get_cvs(self, index = 0):
        cvs = self.curve_functions[index].get_cv_positions()
        
        returnValue = []
        
        for cv in cvs:
            returnValue.append(cv[0])
            returnValue.append(cv[1])
            returnValue.append(cv[2])
            
        return returnValue
    
    def get_cv_count(self, index = 0):
        return self.curve_functions[index].get_cv_count()
    
    def get_span_count(self, index = 0):
        return self.curve_functions[index].get_span_count()
    
    def get_form(self, index = 0):
        return (self.curve_functions[index].get_form()-1)
    
    def create_curve_list(self):
        
        curve_arrays = []
        
        for inc in range(0, len(self.curves)):
            nurbs_curve_array = []
            
            knots = self.get_knots(inc)
            cvs = self.get_cvs(inc)
            
            nurbs_curve_array.append(self.get_degree(inc))
            nurbs_curve_array.append(self.get_span_count(inc))
            nurbs_curve_array.append(self.get_form(inc))
            nurbs_curve_array.append(0)
            nurbs_curve_array.append(3)
            nurbs_curve_array.append(len(knots))
            nurbs_curve_array += knots
            nurbs_curve_array.append(self.get_cv_count(inc))
            nurbs_curve_array += cvs
            
            curve_arrays.append( nurbs_curve_array )
        
        return curve_arrays
    
    def create_mel_list(self):
        curve_arrays = self.create_curve_list()
        
        mel_curve_data_list = []
        for curve_array in curve_arrays:
            mel_curve_data = ''
            
            for nurbs_data in curve_array:
                mel_curve_data += ' %s' % str(nurbs_data)
                
            mel_curve_data_list.append(mel_curve_data)
            
        return mel_curve_data_list

def set_nurbs_data(curve, curve_data_array):
    #errors at position 7
    cmds.setAttr('%s.cc' % curve, *curve_data_array, type = 'nurbsCurve')

def get_nurbs_data_mel(curve):
    
    curve_inst = CurveToData(curve)
    return curve_inst.create_mel_list()

def set_nurbs_data_mel(curve, mel_curve_data, z_up_compensate = True):
    
    match_shapes_to_data(curve, mel_curve_data)
    
    current_unit = cmds.currentUnit( q = True)
    cmds.currentUnit(linear='cm')
    
    shapes = get_shapes(curve)
    
    util.convert_to_sequence(mel_curve_data)
    
    data_count = len(mel_curve_data)
    
    create_input = get_attribute_input('%s.create' % curve)
    
    if create_input:
        
        util.warning('%s has history.  Disconnecting create attribute on curve. This will allow cv position change.' % curve)
        cmds.disconnectAttr(create_input, '%s.create' % curve)
    
    for inc in range(0, data_count):
            
        attribute = '%s.cc' % shapes[inc]
        
        if inc < data_count:
            mel.eval('setAttr "%s" -type "nurbsCurve" %s' % (attribute, mel_curve_data[inc]))
    
    cmds.currentUnit(linear = current_unit)
    
    if z_up_compensate:
        if cmds.upAxis(q = True, ax = True) == 'z':
            cvs = '%s.cv[*]' % curve
            cmds.rotate(90,0,0, cvs, relative = True)
    
class CurveDataInfo(object):
    
    curve_data_path = util_file.join_path(current_path, 'curve_data')
        
    def __init__(self):
        
        self.libraries = {}
        self._load_libraries()
        
        self.library_curves = {}
        self._initialize_library_curve()
        
        self.active_library = None
        
        
    def _load_libraries(self):
        files = os.listdir(self.curve_data_path)
        
        for filename in files:
            if filename.endswith('.data'):
                split_file = filename.split('.')
                
                self.libraries[split_file[0]] = filename
                
    def _initialize_library_curve(self):
        names = self.get_library_names()
        for name in names:
            self.library_curves[name] = {}       
    
    def _get_curve_data(self, curve_name, curve_library):
        
        curve_dict = self.library_curves[curve_library]
        
        if not curve_name in curve_dict:
            util.warning('%s is not in the curve library %s.' % (curve_name, curve_library))
            
            return None, None
        
        return curve_dict[curve_name]
    
    def _get_curve_parent(self, curve):
        
        parent = curve
        
        if cmds.objExists(curve):
            if cmds.nodeType(curve) == 'nurbsCurve':
                parent = cmds.listRelatives(curve, parent = True)[0]
            if not cmds.nodeType(curve) == 'nurbsCurve':
                parent = curve
            
        
            
        return parent
    
    def _get_mel_data_list(self, curve):
        curveData = CurveToData(curve)
        mel_data_list = curveData.create_mel_list()
        
        return mel_data_list
    
    def _get_curve_type(self, maya_curve):
    
        curve_type_value = None
        
        curve_attr = '%s.curveType' % maya_curve
        
        if cmds.objExists(curve_attr):
            curve_type_value = cmds.getAttr(curve_attr)
    
        return curve_type_value
    
    def _is_curve_of_type(self, existing_curve, type_curve):
        
        mel_data_list, original_curve_type = self._get_curve_data(type_curve, self.active_library)

        if not mel_data_list:
            return False
    
        curve_type_value = self._get_curve_type(existing_curve)
        
        if not original_curve_type:
            return True
        
        if curve_type_value:
            if curve_type_value != original_curve_type:
                return False
            
        return True
    
    """
    def _match_shapes_to_data(self, curve, data_list):
        
        shapes = get_shapes(curve)
                
        if not shapes:
            return
        
        shape_color = None
        
        if len(shapes):
            shape_color = cmds.getAttr('%s.overrideColor' % shapes[0])
            shape_color_enabled = cmds.getAttr('%s.overrideEnabled' % shapes[0])
        
        found = []
        
        for shape in shapes:
            if cmds.nodeType(shape) == 'nurbsCurve':                    
                found.append(shape)
        
        if len(found) > len(data_list):
            cmds.delete(found[ len(data_list): ])
            
        if len(found) < len(data_list):
            
            current_index = len(found)
            
            for inc in range(current_index, len(data_list)):
                
                curve_shape = cmds.createNode('nurbsCurve')
                #maybe curve_shape = cmds.createNode('nurbsCurve', parent = curve, n = '%sShape' % curve)
                
                if shape_color != None and shape_color_enabled:
                    cmds.setAttr('%s.overrideEnabled' % curve_shape, 1)
                    cmds.setAttr('%s.overrideColor' % curve_shape, shape_color)
                
                parent = cmds.listRelatives(curve_shape, parent = True)[0]
                
                cmds.parent(curve_shape, curve, r = True, s = True)
                
                cmds.delete(parent)
    """
    
    def _set_curve_type(self, curve, curve_type_value):
        
        create_curve_type_attribute(curve, curve_type_value)

        
    
    def set_directory(self, directorypath):
        self.curve_data_path = directorypath
        self.libraries = {}
        self._load_libraries()
        self.library_curves = {}
        self._initialize_library_curve()
    
    def set_active_library(self, library_name, skip_extension = False):
        
        if not skip_extension:
            filename = '%s.data' % library_name
        if skip_extension:
            filename = library_name
          
        path = util_file.create_file(filename, self.curve_data_path)
        self.active_library = library_name
        self.library_curves[library_name] = {}
        if skip_extension:
            self.load_data_file(path)
        if not skip_extension:
            self.load_data_file()
     
    def load_data_file(self, path = None):
        
        if not self.active_library:
            util.warning('Must set active library before running this function.')
            return
        
        if not path:
            path = util_file.join_path(self.curve_data_path, '%s.data' % self.active_library)
        
        last_line_curve = False
        curve_name = ''
        curve_data = ''
        curve_type = ''
        
        data_lines = util_file.get_file_lines(path)
        
        curve_data_lines = []
        
        for line in data_lines:
            
            if line.startswith('->'):
                
                if curve_data_lines:
                    
                    self.library_curves[self.active_library][curve_name] = [curve_data_lines, curve_type]
                    curve_type = ''
                    curve_name = ''
                    curve_data = ''
                    
                line_split = line.split()
                
                curve_name = line_split[1]
                
                if len(line_split) > 2:
                    
                    curve_type = line_split[2]
                    
                    if not curve_type:
                        curve_type = ''
                        
                curve_name = curve_name.strip()
                last_line_curve = True
                curve_data_lines = []
                                
            if not line.startswith('->') and last_line_curve:
                
                line = line.strip()
                if line:
                    curve_data = line
                    curve_data = curve_data.strip()
                    curve_data_lines.append(curve_data) 
                    
         
        if curve_data_lines:
            self.library_curves[self.active_library][curve_name] = [curve_data_lines, curve_type] 
                
    def write_data_to_file(self):
        if not self.active_library:
            util.warning('Must set active library before running this function.')
            return
        
        path = util_file.join_path(self.curve_data_path, '%s.data' % self.active_library)
        
        current_library = self.library_curves[self.active_library]
        
        lines = []
        
        curves = list(current_library.keys())
        curves.sort()
        
        for curve in curves:
            
            curve_data_lines, curve_type = current_library[curve]
            
            if not curve_type:
                if cmds.objExists('%s.curveType' % curve):
                    curve_type = cmds.getAttr('%s.curveType' % curve)

            if curve != curve_type:
                lines.append('-> %s %s' % (curve, curve_type))
            if curve == curve_type:
                lines.append('-> %s' % curve)
                
            for curve_data in curve_data_lines:
                lines.append('%s' % curve_data)
        
        util_file.write_lines(path, lines)
        
        return path
        
    def get_library_names(self):
        return self.libraries.keys()
    
    def get_curve_names(self):
        if not self.active_library:
            util.warning('Must set active library before running this function.')
            return
        
        return list(self.library_curves[self.active_library].keys())
        
    def set_shape_to_curve(self, curve, curve_in_library, check_curve = False, add_curve_type_attribute = True,z_up_compensate = True):
        
        if not self.active_library:
            util.warning('Must set active library before running this function.')
            return
        
        mel_data_list, original_curve_type = self._get_curve_data(curve_in_library, self.active_library)
        
        if not mel_data_list:
            return
        
        curve_type_value = self._get_curve_type(curve)
        
        if not curve_type_value or not cmds.objExists(curve_type_value):
            curve_type_value = curve_in_library

        if check_curve:
        
            is_curve = self._is_curve_of_type(curve, curve_in_library)
            
            if not is_curve:
                return
        
        if mel_data_list:
            
            set_nurbs_data_mel(curve, mel_data_list, z_up_compensate=z_up_compensate)
            
        rename_shapes(curve)
        
        if add_curve_type_attribute:
            self._set_curve_type(curve, curve_type_value)
        

        
    def add_curve(self, curve, library_name = None):
        
        if not curve:
            
            return
        
        if library_name:
            self.set_active_library(library_name)
        
        if not library_name:
            
            library_name = self.active_library
            
            if not self.active_library:
                util.warning('Must set active library before running this function.')
                return
        
        mel_data_list = self._get_mel_data_list(curve)
        
        curve_type = curve
        
        if cmds.objExists('%s.curveType' % curve):  
            curve_type = cmds.getAttr('%s.curveType' % curve)
            
        transform = self._get_curve_parent(curve)
               
        if library_name:
            self.library_curves[library_name][transform] = [mel_data_list, curve_type]
            
    def remove_curve(self, curve, library_name = None):
        if not curve:
            
            return
        
        if not library_name:
            
            library_name = self.active_library
            
            if not self.active_library:
                util.warning('Must set active library before running this function.')
                return
                    
        transform = self._get_curve_parent(curve)
        
        if library_name in self.library_curves:
            
            if transform in self.library_curves[library_name]:
            
                self.library_curves[library_name].pop(transform)
                
                return True
            
        
    def create_curve(self, curve_name):
        if not self.active_library:
            util.warning('Must set active library before running this function.')
            return
        
        curve_shape = cmds.createNode('nurbsCurve')
        
        parent = cmds.listRelatives(curve_shape, parent = True)[0]
        parent = cmds.rename( parent, curve_name )
        
        self.set_shape_to_curve(parent, curve_name)

        return parent
        
    def create_curves(self):
        if not self.active_library:
            util.warning('Must set active library before running this function.')
            return
        
        curves_dict = self.library_curves[self.active_library]
        
        keys = list(curves_dict.keys())
        
        keys.sort()
        
        for key in keys:
            self.create_curve(key)

def add_curve_to_default(curve_name):
    """
    This will add a curve to the default library.  Future updates of Vetala won't keep these changes.
    """
    
    curve_info = CurveDataInfo()
    
    curve_info.add_curve(curve_name, 'default_curves')
    curve_info.write_data_to_file()

def create_curve_from_default(curve_name):
    
    curve_info = CurveDataInfo()
    curve_info.set_active_library('default_curves')
    curve_info.create_curve(curve_name)

def get_library_shape_names():
    
    curve_info = CurveDataInfo()
    curve_info.set_active_library('default_curves')
    return curve_info.get_curve_names()
            
def get_shapes(transform):
    if is_a_shape(transform):
        parent = cmds.listRelatives(transform, p = True, f = True)
        shapes = cmds.listRelatives(parent, s = True, f = True, ni = True)
    else:
        shapes = cmds.listRelatives(transform, s = True, f = True, ni = True)
        
    found = []
    
    if not shapes:
        return found
    
    for shape in shapes:
        if cmds.nodeType(shape) == 'nurbsCurve':
            found.append(shape)
    
    return found  

def is_a_shape(node):
    if cmds.objectType(node, isAType = 'shape'):
        return True
    
    return False  

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
            
def set_shapes_as_text_curves(transform, text_string):
    
    shapes = get_shapes(transform)
    cmds.delete(shapes)
    
    text = cmds.textCurves(ch = 0, f = "Arial|w400|h-1", t = text_string)
    
    cmds.makeIdentity(text, apply = True, t = True)
    
    transforms = cmds.listRelatives(text, ad = True, type = 'transform')
    
    for text_transform in transforms:
        shapes = get_shapes(text_transform)
        
        if not shapes:
            continue
        
        for shape in shapes:
            cmds.parent(shape, transform, r = True, s = True)
            
    cmds.delete(text)
    
    rename_shapes(transform)
    
def create_curve_type_attribute(node, value):
    
    if not cmds.objExists('%s.curveType' % node):
        cmds.addAttr(node, ln = 'curveType', dt = 'string') 

    cmds.setAttr('%s.curveType' % node, l = False)

    if value != None and value != node:
        cmds.setAttr('%s.curveType' % node, value, type = 'string', )
        
    cmds.setAttr('%s.curveType' % node, l = True, k = False) 

def create_nurbs_from_mel(name, mel_data):
    curve_shape = cmds.createNode('nurbsCurve')
    
    parent = cmds.listRelatives(curve_shape, parent = True)[0]
    parent = cmds.rename( parent, name )
    
    set_nurbs_data_mel(parent, mel_data)
    rename_shapes(parent)
    
def match_shapes_to_data(curve, mel_data):
        
        shapes = get_shapes(curve)
                
        if not shapes:
            shapes = []
        
        shape_color = None
        
        if len(shapes):
            shape_color = cmds.getAttr('%s.overrideColor' % shapes[0])
            shape_color_enabled = cmds.getAttr('%s.overrideEnabled' % shapes[0])
        
        found = []
        
        for shape in shapes:
            if cmds.nodeType(shape) == 'nurbsCurve':                    
                found.append(shape)
        
        if len(found) > len(mel_data):
            cmds.delete(found[ len(mel_data): ])
            
        if len(found) < len(mel_data):
            
            current_index = len(found)
            
            for inc in range(current_index, len(mel_data)):
                
                curve_shape = cmds.createNode('nurbsCurve')
                #maybe curve_shape = cmds.createNode('nurbsCurve', parent = curve, n = '%sShape' % curve)
                
                if shape_color != None and shape_color_enabled:
                    cmds.setAttr('%s.overrideEnabled' % curve_shape, 1)
                    cmds.setAttr('%s.overrideColor' % curve_shape, shape_color)
                
                parent = cmds.listRelatives(curve_shape, parent = True)[0]
                
                cmds.parent(curve_shape, curve, r = True, s = True)
                
                cmds.delete(parent)

def rename_shapes(transform):
    
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
        
    
