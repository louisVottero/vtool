# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

import os

import util
import vtool.util_file


import maya.cmds as cmds
import maya.mel as mel


current_path = os.path.split(__file__)[0]

class CurveToData(object):
    
    def __init__(self, curve):
        
        curve_shape = self._get_shape(curve)
        
        if not curve_shape:
            util.warning('%s is not a nurbs curve.' % curve_shape)
            return 
        
        self.curve = curve_shape
        self.curve_mobject = util.nodename_to_mobject(self.curve)
        self.curve_function = util.NurbsCurveFunction(self.curve_mobject)
        
    def _get_shape(self, curve):
        curve_shape = None
        
        if not cmds.nodeType(curve) == 'nurbsCurve':
            shapes = cmds.listRelatives(curve, s = True)
            
            if shapes:
                
                if cmds.nodeType(shapes[0]) == 'nurbsCurve':
                    curve_shape = shapes[0]

                    
        if cmds.nodeType(curve) == 'nurbsCurve':
            curve_shape = curve
        
        
        
        return curve_shape
    
    def get_degree(self):
        return self.curve_function.get_degree()
        
    def get_knots(self):
        return self.curve_function.get_knot_values()
        
    def get_cvs(self):
        cvs = self.curve_function.get_cv_positions()
        
        returnValue = []
        
        for cv in cvs:
            returnValue.append(cv[0])
            returnValue.append(cv[1])
            returnValue.append(cv[2])
            
        return returnValue
    
    def get_cv_count(self):
        return self.curve_function.get_cv_count()
    
    def get_span_count(self):
        return self.curve_function.get_span_count()
    
    def get_form(self):
        return (self.curve_function.get_form()-1)
    
    def create_curve_array(self):
        
        nurbs_curve_array = []
        
        knots = self.get_knots()
        cvs = self.get_cvs()
        
        nurbs_curve_array.append(self.get_degree())
        nurbs_curve_array.append(self.get_span_count())
        nurbs_curve_array.append(self.get_form())
        nurbs_curve_array.append(0)
        nurbs_curve_array.append(3)
        nurbs_curve_array.append(len(knots))
        nurbs_curve_array += knots
        nurbs_curve_array.append(self.get_cv_count())
        nurbs_curve_array += cvs
        
        return nurbs_curve_array
    
    def create_curve_array_mel(self):
        data = self.create_curve_array()
        mel_curve_data = ''
        
        for nurbs_data in data:
            mel_curve_data += ' %s' % str(nurbs_data);
            
        return mel_curve_data

def set_nurbs_data(curve, curve_data_array):
    #errors at position 7
    cmds.setAttr('%s.cc' % curve, *curve_data_array, type = 'nurbsCurve')
    
def set_nurbs_data_mel(curveShape, mel_curve_data):
    mel.eval('setAttr "%s.cc" -type "nurbsCurve" %s' % (curveShape,mel_curve_data))
    
class CurveDataInfo():
    
    curve_data_path = vtool.util_file.join_path(current_path, 'curve_data')
        
    def __init__(self):
        
        self.libraries = {}
        self._load_libraries()
        
        self.library_curves = {}
        self._initialize_library_curve()
        
        self.active_library = None
        
        
    def _load_libraries(self):
        files = os.listdir(self.curve_data_path)
        
        for file in files:
            if file.endswith('.data'):
                split_file = file.split('.')
                
                self.libraries[split_file[0]] = file
                
    def _initialize_library_curve(self):
        names = self.get_library_names()
        for name in names:
            self.library_curves[name] = {}       
    
    def _get_curve_data(self, curve_name, curve_library):
        
        curve_dict = self.library_curves[curve_library]
        
        if not curve_dict.has_key(curve_name):
            util.warning('%s is not in the curve library %s.' % (curve_name, curve_library))
            return
        
        return curve_dict[curve_name]
    
    def _get_curve_parent(self, curve):
        
        parent = None
        
        if cmds.nodeType(curve) == 'nurbsCurve':
            parent = cmds.listRelatives(curve, parent = True)[0]
        if not cmds.nodeType(curve) == 'nurbsCurve':
            parent = curve
            
        return parent
    
    def _get_mel_data(self, curve):
        curveData = CurveToData(curve)
        mel_data = curveData.create_curve_array_mel()
        
        return mel_data
    
    def set_directory(self, directorypath):
        self.curve_data_path = directorypath
        self.libraries = {}
        self._load_libraries()
        self.library_curves = {}
        self._initialize_library_curve()
    
    def set_active_library(self, library_name):
        
        vtool.util_file.create_file('%s.data' % library_name, self.curve_data_path)
        self.active_library = library_name
        self.library_curves[library_name] = {}
        self.load_data_file()
     
    def load_data_file(self, path = None):
        
        if not self.active_library:
            util.warning('Must set active library before running this function.')
            return
        
        if not path:
            path = vtool.util_file.join_path(self.curve_data_path, '%s.data' % self.active_library)
        
        
        
        last_line_curve = False
        curve_name = ''
        curve_data = ''
        
        readfile = vtool.util_file.ReadFile(path)
        data_lines = readfile.read()
        
        for line in data_lines:
            
            if line.startswith('->'):
                line_split = line.split('->')
                curve_name = line_split[1]
                last_line_curve = True
                                
            if not line.startswith('->') and last_line_curve:
                
                curve_data = line
                    
            if curve_name and curve_data:
                curve_name = curve_name.strip()
                curve_data = curve_data.strip()
                    
                self.library_curves[self.active_library][curve_name] = curve_data
                curve_name = ''
                curve_data = ''
        
                
    def write_data_to_file(self):
        if not self.active_library:
            util.warning('Must set active library before running this function.')
            return
        
        path = vtool.util_file.join_path(self.curve_data_path, '%s.data' % self.active_library)
        
        writefile = vtool.util_file.WriteFile(path)
        
        current_library = self.library_curves[self.active_library]
        
        lines = []
        
        for curve in current_library:
            data_string = current_library[curve]
            lines.append('-> %s' % curve)
            lines.append('%s' % data_string)
          
        writefile.write(lines)
        
        return path
        
    def get_library_names(self):
        return self.libraries.keys()
    
    def get_curve_names(self):
        if not self.active_library:
            util.warning('Must set active library before running this function.')
            return
        
        return self.libraryCurves[self.active_library].keys()
        
    def set_shape_to_curve(self, curve, curve_name, checkCurve = False):
        if not self.active_library:
            util.warning('Must set active library before running this function.')
            return
        
        mel_data = self._get_curve_data(curve_name, self.active_library)
        
        if checkCurve and mel_data:
            split_mel_data = mel_data.split()
            
            curve_data = CurveToData(curve)
            original_curve_data =  curve_data.create_curve_array_mel()
            
            split_original_curve_data = original_curve_data.split()
            
            if len(split_mel_data) != len(split_original_curve_data):
                util.warning('Curve data does not match stored data. Skipping %s' % curve) 
                return        
        
        if mel_data:
            set_nurbs_data_mel(curve, mel_data)
        
    def add_curve_to_library(self, curve, library_name):
        
        mel_data = self._get_mel_data(curve)
        
        transform = self._get_curve_parent(curve)
        
        self.library_curves[library_name][transform] = mel_data
        
    def add_curve(self, curve):
        if not self.active_library:
            util.warning('Must set active library before running this function.')
            return
        
        mel_data = self._get_mel_data(curve)
        
        transform = self._get_curve_parent(curve)
                    
        if self.active_library:
            self.library_curves[self.active_library][transform] = mel_data
        
    def create_curve(self, curve_name):
        if not self.active_library:
            util.warning('Must set active library before running this function.')
            return
        
        curve_shape = cmds.createNode('nurbsCurve')
        
        parent = cmds.listRelatives(curve_shape, parent = True)[0]
        
        self.set_shape_to_curve(curve_shape, curve_name)
        parent = cmds.rename( parent, curve_name )
        
        return parent
        
    def create_curves(self):
        if not self.active_library:
            #do not remove print
            print 'Must set active library before running this function.'
            return
        
        curves_dict = self.library_curves[self.active_library]
        
        for curve in curves_dict:
            self.create_curve(curve)    