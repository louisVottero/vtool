# Copyright (C) 2017 Louis Vottero louis.vot@gmail.com    All rights reserved.

from vtool import qt_ui, qt
from vtool import util
from vtool.maya_lib import core
from vtool.maya_lib import api
from vtool.maya_lib import geo
from vtool.maya_lib import space
from vtool.maya_lib import rigs_util
from vtool.maya_lib import ui_core

import maya.cmds as cmds


class CheckView(ui_core.MayaWindowMixin):
    
    title_name = 'Check'
    title = 'Check'
        
    
    def _define_main_layout(self):
        return qt.QHBoxLayout()
    
    def _build_widgets(self):
    
        self.setWindowTitle('Check Manager')
        
        self.setWindowFlags(self.windowFlags() ^ qt.QtCore.Qt.WindowContextHelpButtonHint | qt.QtCore.Qt.WindowStaysOnTopHint)
        
        scroll = qt.QScrollArea()
        
        scroll.setWidgetResizable(True)
        scroll_widget = qt_ui.BasicWidget()
        scroll_widget.setSizePolicy(qt.QSizePolicy(qt.QSizePolicy.Expanding, qt.QSizePolicy.Expanding))
        
        view = qt.QVBoxLayout()
        
        
        
        self.check_buttons = qt.QVBoxLayout()
        self.check_buttons.setAlignment(qt.QtCore.Qt.AlignBottom)
        
        self.title_label = qt.QLabel(self.title_name, alignment = qt.QtCore.Qt.AlignTop) 
        self.title_label.setMinimumWidth(235)
        
        scroll_widget.main_layout.addWidget(self.title_label)
        
        scroll_widget.main_layout.addLayout(self.check_buttons)
        
        scroll.setWidget(scroll_widget)
        
        self.main_layout.addWidget(scroll)
        self.main_layout.addLayout(view)
        
        self.list_label = qt.QLabel()
        self.list_label.hide()
        
        self.list = qt.QListWidget()
        self.list.addItem('None')
        self.list.setDisabled(True)
        self.list.setSelectionMode(self.list.ExtendedSelection)
        
        self.list.itemSelectionChanged.connect(self._selection_change)
        
        view.addSpacing(5)
        view.addWidget(self.list_label)
        view.addSpacing(5)
        view.addWidget(self.list)
        
        

        
    def _update_list(self, check_list, check_name):
        
        self.list.clear()
        self.list.setEnabled(True)
        
        self.sub_list = {}
        found_items = []
        
        if check_list:
            for name in check_list:
                
                if name.find('[') > -1:
                
                    split_name = name.split('.')
                    object_name = split_name[0]
                    
                    parent = cmds.listRelatives(object_name, p = True, f = True)[0]
                    
                    if not self.sub_list.has_key(parent):
                        self.sub_list[parent] = []
                        
                    self.sub_list[parent].append(name)
                    
                    #make the parent the main item
                    name = parent
                
                if name.find('[') == -1:
                    
                    if not name in found_items:
                        found_items.append(name)
                        self.list.addItem(name)
                
            self.list_label.show()
            self.list_label.setText(check_name)
            
        if not check_list:
            self.list.addItem('None')
            self.list.setDisabled(True)
            self.list_label.hide()
            
    def _selection_change(self):
        
        items = self.list.selectedItems()
        
        found = []
        
        sub_selection = []
        
        for item in items:
            
            name = str(item.text())
            
            if cmds.objExists(name):
                found.append(name)
            
                if self.sub_list.has_key(name):
                    for thing in self.sub_list[name]:
                        if cmds.objExists(thing):
                            sub_selection.append(thing)
        
        cmds.select(found)
        cmds.select(sub_selection, add = True)
        
        core.auto_focus_view(selection = True)

    def add_title(self, name_str):
        
        self.check_buttons.addSpacing(10)
        self.check_buttons.addWidget(qt.QLabel(name_str))
        

    def add_check(self, check_ui):
        
        self.check_buttons.addWidget(check_ui, alignment = qt.QtCore.Qt.AlignBottom)
        check_ui.checked.connect(self._update_list)
    
class Check(qt_ui.BasicWidget):
    
    check_name = ''
    checked = qt_ui.create_signal(object, object)

    def _define_main_layout(self):
        return qt.QHBoxLayout()
    
    def _build_widgets(self):
        
        self.button = qt.QPushButton(self.check_name)
        self.button.setMinimumWidth(200)
        self.button.setMaximumWidth(200)
        
        self.orig_palette = self.button.palette()
        
        self.fix = qt.QPushButton('Fix')
        self.fix.setMaximumWidth(30)
        self.fix.setMinimumWidth(30)
        fix_palette = self.fix.palette()
        fix_palette.setColor(qt.QPalette.Button, qt.QColor(qt.QtCore.Qt.darkYellow))
        self.fix.setAutoFillBackground(True)
        self.fix.setPalette(fix_palette);
        self.fix.update()
        
        
        self.main_layout.addWidget(self.button, alignment = qt.QtCore.Qt.AlignLeft)
        self.main_layout.addWidget(self.fix)
        
        self.button.clicked.connect(self._run_check)
        self.fix.clicked.connect(self._run_fix)
        
        self.fix.hide()
        
        self.check_list = []
        self.fix_list = []
        
    def _has_fix(self):
        return False
        
    def _fix(self):
        return
        
    def _check(self):
        return []
    
    def _run_check(self):
        
        self.fix.hide()
        
        self.check_list = self._check()
        
        self.checked.emit(self.check_list, self.check_name)
        
        if self.check_list:
            
            self.button.setAutoFillBackground(False)
            palette = self.button.palette()
            palette.setColor(qt.QPalette.Button, qt.QColor(qt.QtCore.Qt.darkRed))
            #self.button.setPalette(self.orig_palette)
            self.button.setPalette(palette)
            self.button.update()
        
            if self._has_fix():
            
                self.fix.show()
            
        if not self.check_list:
            palette = self.button.palette()
            palette.setColor(qt.QPalette.Button, qt.QColor(qt.QtCore.Qt.darkGreen))
            self.button.setAutoFillBackground(True)
            self.button.setPalette(palette);
            self.button.update()
        
    def _run_fix(self):
        
        if not self.fix_list:
            self.fix_list = self.check_list
        
        self._fix()
        
        self._run_check()
        
        self.fix_list = []

class CheckMayaAsset(CheckView):
    
    title_name = 'Check Asset'
    
    def _build_widgets(self):
        super(CheckMayaAsset, self)._build_widgets()
        
        self._add_check(Check_Non_Unique())
        self._add_check(Check_Empty_Groups())
        self._add_check(Check_Empty_Nodes())
        self._add_check(Check_Empty_Intermediate_Objects())
        self._add_check(Check_References())
        

class Check_Non_Default_Transforms(Check):

    check_name = 'Keyable/Visible Transformations'
    
    def _has_fix(self):
        return False
    
    def _check(self):
        
        
        shapes = cmds.ls(type = 'shape')
        found = []
        
        skip_types = ['camera']
        
        for shape in shapes:
            if cmds.nodeType(shape) in skip_types:
                continue
            parent = cmds.listRelatives(shape, p = True)
            if parent:
                parent = parent[0]
                if not core.is_hidden(parent) and not core.is_parent_hidden(parent):
                    found.append(parent)
                
        transforms = space.get_non_default_transforms(found)
        
        return transforms


class Check_Empty_Groups(Check):
    
    check_name = 'Empty Groups'
    
    def _has_fix(self):
        return True
    
    def _check(self):
        
        groups = core.get_empty_groups()
        
        return groups
    
    def _fix(self):
        
        fix_it = qt_ui.get_permission('Delete empty groups?', self)
        
        if not fix_it:
            return
        
        for item in self.fix_list:
            cmds.delete(item)
            
class Check_Empty_Nodes(Check):
    
    check_name = 'Empty Nodes'
    
    def _has_fix(self):
        return True
    
    def _check(self):
        
        nodes = core.get_empty_nodes()
        
        
        
        return nodes
    
    def _fix(self):
        
        fix_it = qt_ui.get_permission('Delete empty nodes?', self)
        if not fix_it:
            return
        
        for item in self.fix_list:
            cmds.delete(item)
            
class Check_Empty_Intermediate_Objects(Check):
    
    check_name = 'Empty Intermediate Objects'
    
    def _has_fix(self):
        return True
    
    def _check(self):
        
        nodes = core.get_empty_orig_nodes()
        
        return nodes
    
    def _fix(self):
        
        fix_it = qt_ui.get_permission('Delete empty intermediate objects?', self)
        if not fix_it:
            return
        
        for item in self.fix_list:
            cmds.delete(item)
            
class Check_References(Check):
    
    check_name = 'References'
    
    def _has_fix(self):
        return True
    
    def _check(self):
        nodes = cmds.ls(type = 'reference')
        
        return nodes
    
    def _fix(self):
        fix_it = qt_ui.get_permission('Remove references?', self)
        if not fix_it:
            return
        
        for item in self.fix_list:
            
            core.remove_reference(item)
            
            
class Check_Non_Unique(Check):
    
    check_name = 'Non Unique Names'
    
    def _has_fix(self):
        return False
    
    def _check(self):
        
        dag_nodes = cmds.ls(type = 'dagNode')
        
        found = []
        
        for dag_node in dag_nodes:
            
            if dag_node.find('|') > -1:
                
                found.append(dag_node)
        
        return found
    
class Check_Triangles(Check):
    
    check_name = 'Triangles'
    
    def _check(self):
        
        meshes = cmds.ls(type = 'mesh', l = True)
        
        found = []
        
        for mesh in meshes:
            
            if cmds.getAttr('%s.intermediateObject' % mesh):
                continue
            
            triangles = geo.get_triangles(mesh)
            found += triangles
            
        return found
        
class Check_NSided(Check):
    
    check_name = 'NSided Greater Than 4'
    
    def _check(self):
        
        meshes = cmds.ls(type = 'mesh', l = True)
        
        found = []
        
        for mesh in meshes:
        
            if cmds.getAttr('%s.intermediateObject' % mesh):
                continue
            
            nsided = geo.get_non_triangle_non_quad(mesh)
            found += nsided
            
        return found