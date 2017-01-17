# Copyright (C) 2017 Louis Vottero louis.vot@gmail.com    All rights reserved.

from vtool import qt_ui, qt
from vtool import util
from vtool.maya_lib import core



import maya.cmds as cmds


class CheckView(qt_ui.BasicWidget):
    
    title_name = ''
    
    
    def _define_main_layout(self):
        return qt.QHBoxLayout()
    
    def _build_widgets(self):
    
        self.setWindowTitle('Check Manager')
        
        self.setWindowFlags(self.windowFlags() ^ qt.QtCore.Qt.WindowContextHelpButtonHint | qt.QtCore.Qt.WindowStaysOnTopHint)
        
        buttons = qt.QVBoxLayout()
        view = qt.QVBoxLayout()
        
        self.main_layout.addLayout(buttons)
        self.main_layout.addLayout(view)
        
        self.check_buttons = qt.QVBoxLayout()
        self.check_buttons.setAlignment(qt.QtCore.Qt.AlignBottom)
        
        self.title = qt.QLabel(self.title_name, alignment = qt.QtCore.Qt.AlignTop) 
        self.title.setMinimumWidth(235)
        
        
        buttons.addWidget(self.title)
        buttons.addLayout(self.check_buttons)
        
        self.list_label = qt.QLabel()
        self.list_label.hide()
        
        self.list = qt.QListWidget()
        self.list.addItem('None')
        self.list.setDisabled(True)
        
        self.list.itemSelectionChanged.connect(self._selection_change)
        
        view.addSpacing(5)
        view.addWidget(self.list_label)
        view.addSpacing(5)
        view.addWidget(self.list)
        
        
        
    def _add_check(self, check_ui):
        
        self.check_buttons.addWidget(check_ui, alignment = qt.QtCore.Qt.AlignBottom)
        check_ui.checked.connect(self._update_list)
        
    def _update_list(self, check_list, check_name):
        
        self.list.clear()
        self.list.setEnabled(True)
        
        if check_list:
            for name in check_list:
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
        
        for item in items:
            found.append(str(item.text()))
            
        cmds.select(found)
    
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
        fix_palette.setColor(qt.QPalette.Button, qt.QColor(qt.QtCore.Qt.red))
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
        
        if self._has_fix() and self.check_list:
            
            self.button.setAutoFillBackground(False)
            self.button.setPalette(self.orig_palette);
            self.button.update()
            
            
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
    
