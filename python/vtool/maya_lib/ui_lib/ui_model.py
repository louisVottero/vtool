# Copyright (C) 2016 Louis Vottero louis.vot@gmail.com    All rights reserved.

import maya.cmds as cmds

from vtool import qt_ui,qt
    
from vtool.maya_lib import geo, space, core

class ModelManager(qt_ui.BasicWidget):
    def _build_widgets(self):
        
        self.main_layout.setContentsMargins(20,20,20,20)
        
        grow_edge_loop = qt.QPushButton('Grow Edge Loop')
        grow_edge_loop.setMaximumWidth(100)
        
        grow_edge_loop.clicked.connect(self._grow_edge_loop)
        
        select_internal_faces = SelectInternalFaces()
        select_internal_faces.collapse_group()
        
        randomize_points = RandomizePoints()
        randomize_points.collapse_group()
        randomize_transforms = RandomizeTransform()
        randomize_transforms.collapse_group()
        
        self.main_layout.addWidget(grow_edge_loop)
        self.main_layout.addSpacing(5)
        self.main_layout.addWidget(select_internal_faces)
        self.main_layout.addSpacing(5)
        self.main_layout.addWidget(randomize_points)
        self.main_layout.addSpacing(5)
        self.main_layout.addWidget(randomize_transforms)
        
    @core.undo_chunk
    def _grow_edge_loop(self):
        
        geo.expand_selected_edge_loop()
        
    @core.undo_chunk
    def _select_internal_faces(self):
        
        selection = cmds.ls(sl = True, l = True)
        
        if geo.is_a_mesh(selection[0]):
            geo.get_occluded_faces(selection[0], 10000)
            
class RandomizePoints(qt_ui.Group):
    def __init__(self):
        
        name = 'Randomize Points'
        super(RandomizePoints, self).__init__(name)
        
    def _build_widgets(self):
        
        self.min = qt_ui.GetNumber('Min Change')
        self.max = qt_ui.GetNumber('Max Change')
        
        self.min.set_value(-.1)
        self.max.set_value(.1)
        
        self.main_layout.addWidget(self.min)
        self.main_layout.addWidget(self.max)
        
        run = qt.QPushButton('Run')
        run.clicked.connect(self._run)
        self.main_layout.addWidget(run)
        
    @core.undo_chunk
    def _run(self):
        
        selection = cmds.ls(sl = True, flatten = True)
        
        geo.randomize_mesh_vertices(selection, self.min.get_value(), self.max.get_value())
        
class RandomizeTransform(qt_ui.Group):
    
    def __init__(self):
        
        name = 'Randomize Transform of Selection'
        super(RandomizeTransform, self).__init__(name)
        
    def _build_widgets(self):
        
        
        
        self.tx = qt_ui.GetNumber('translateX')
        self.ty = qt_ui.GetNumber('translateY')
        self.tz = qt_ui.GetNumber('translateZ')
        
        self.tx.set_value(.1)
        self.ty.set_value(.1)
        self.tz.set_value(.1)
        
        self.rx = qt_ui.GetNumber('rotateX')
        self.ry = qt_ui.GetNumber('rotateY')
        self.rz = qt_ui.GetNumber('rotateZ')
        
        self.rx.set_value(1)
        self.ry.set_value(1)
        self.rz.set_value(1)
        
        self.sx = qt_ui.GetNumber('scaleX')
        self.sy = qt_ui.GetNumber('scaleY')
        self.sz = qt_ui.GetNumber('scaleZ')
        
        self.sx.set_value(.1)
        self.sy.set_value(.1)
        self.sz.set_value(.1)
        
        self.main_layout.addWidget(self.tx)
        self.main_layout.addWidget(self.ty)
        self.main_layout.addWidget(self.tz)
        
        self.main_layout.addWidget(self.rx)
        self.main_layout.addWidget(self.ry)
        self.main_layout.addWidget(self.rz)
        
        self.main_layout.addWidget(self.sx)
        self.main_layout.addWidget(self.sy)
        self.main_layout.addWidget(self.sz)
        
        run = qt.QPushButton('Run')
        run.clicked.connect(self._run)
        self.main_layout.addWidget(run)
        
    @core.undo_chunk
    def _run(self):
        
        selection = cmds.ls(sl = True, flatten = True)
        
        transforms = []
        
        for thing in selection:
            if cmds.nodeType(thing) == 'transform':
                
                if core.has_shape_of_type(thing, 'mesh'):
                    transforms.append(thing)
                if core.has_shape_of_type(thing, 'nurbsSurface'):
                    transforms.append(thing)
                if core.has_shape_of_type(thing, 'nurbsCurve'):
                    transforms.append(thing)
                
                    
        space.randomize([self.tx.get_value(), self.ty.get_value(), self.tz.get_value()], 
                        [self.rx.get_value(), self.ry.get_value(), self.rz.get_value()],
                        [self.sx.get_value(), self.sy.get_value(), self.sz.get_value()],
                        transforms)
        
                    
                
            
class SelectInternalFaces(qt_ui.Group):
    
    def __init__(self):
        
        name = 'Select Internal Faces'
        super(SelectInternalFaces, self).__init__(name)
        
    def _build_widgets(self):
        
        
        int_distance = qt_ui.GetInteger('Occlusion distance')
        int_distance.set_value(10000)
        
        int_area = qt_ui.GetInteger('Area great than exclude')
        int_area.set_value(-1)
        
        self.int_distance = int_distance
        self.int_area = int_area
        
        button = qt.QPushButton('Select')
        button.clicked.connect(self._select_internal)
        
        
        self.main_layout.addWidget(int_distance)
        self.main_layout.addWidget(int_area)
        self.main_layout.addWidget(button)
    
    def _select_internal(self):
        
        selection = cmds.ls(sl = True, l = True)
        
        distance = self.int_distance.get_value()
        area = self.int_area.get_value()
        
        if geo.is_a_mesh(selection[0]):
            
            faces = geo.get_occluded_faces(selection[0], distance, area)
            cmds.select(faces)