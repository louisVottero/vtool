# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

import maya.cmds as cmds
import maya.utils


import vtool.qt_ui

from vtool.maya_lib.ui_lib import ui_fx
from vtool.maya_lib.ui_lib import ui_rig
from vtool.maya_lib.ui_lib import ui_anim
import ui_core



import core
import attr
import space
import geo
import deform
import rigs_util

#import util
if vtool.qt_ui.is_pyqt():
    from PyQt4 import QtCore, Qt, uic
    from PyQt4.QtGui import *
if vtool.qt_ui.is_pyside():
    from PySide import QtCore
    from PySide.QtGui import *
if vtool.qt_ui.is_pyside2():
    from PySide2 import QtCore
    from PySide2.QtGui import *
    from PySide2.QtWidgets import *
    
def load_into_tool_manager(window):
    
    if ToolManager._last_instance:
        ToolManager._last_instance.add_tab(window, window.title)
    
    if not ToolManager._last_instance:
        ui_core.create_window(window)


ui_core.new_tool_signal.signal.connect(load_into_tool_manager) 


    
def pose_manager(shot_sculpt_only = False):
    ui_rig.pose_manager()
    


def shape_combo():
    
    window = ui_rig.shape_combo()
    
    if ToolManager._last_instance:
        ToolManager._last_instance.add_tab(window, window.title)
    
    if not ToolManager._last_instance:
        ui_core.create_window(window)
    
def picker():
    
    window = ui_rig.picker()
    
    if ToolManager._last_instance:
        ToolManager._last_instance.add_tab(window, window.title)
    
    if not ToolManager._last_instance:
        ui_core.create_window(window)
    
def tool_manager(name = None, directory = None):
    
    manager = ToolManager(name)
    manager.set_directory(directory)
    
    funct = lambda : ui_core.create_window(manager)
    
    maya.utils.executeDeferred(funct)
    
    return manager

def process_manager(directory = None):
    
    window = ui_rig.process_manager()
    
    if ToolManager._last_instance:
        ToolManager._last_instance.add_tab(window, 'VETALA')
    
    if not ToolManager._last_instance:
        funct = lambda : ui_core.create_window(window)
        maya.utils.executeDeferred(funct)
    
    if directory:
        window.set_code_directory(directory)
    
    return window


        
        

    
class ToolManager(ui_core.MayaDirectoryWindow):
    title = 'VETALA  HUB'
    
    def __init__(self, name = None):
        if name:
            self.title = name
    
        super(ToolManager, self).__init__()
        
    def _build_widgets(self):
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(self.tab_widget.West)
        
        self.modeling_widget = ModelManager()
        self.rigging_widget = ui_rig.RigManager()
        self.animation_widget = ui_anim.AnimationManager()
        #self.shot_widget = QWidget()
        self.fx_widget = ui_fx.FxManager()
        
        #temporary
        
        self.tab_widget.addTab(self.modeling_widget, 'MODEL')
        self.tab_widget.addTab(self.rigging_widget, 'RIG')
        self.tab_widget.addTab(self.animation_widget, 'ANIMATE')
        self.tab_widget.addTab(self.fx_widget, 'FX')
        
        self.tab_widget.setCurrentIndex(1)
        
        self.tab_widget.setMovable(True)
        self.tab_widget.setTabsClosable(True)
        
        
        
        version = QLabel('%s' % vtool.util_file.get_vetala_version())
        self.main_layout.addWidget(version)
        self.main_layout.addWidget(self.tab_widget)
        
        self.tab_widget.tabBar().tabButton(0, QTabBar.RightSide).hide()
        self.tab_widget.tabBar().tabButton(1, QTabBar.RightSide).hide()
        self.tab_widget.tabBar().tabButton(2, QTabBar.RightSide).hide()
        self.tab_widget.tabBar().tabButton(3, QTabBar.RightSide).hide()
        
        #temporary
        #self.tab_widget.tabBar().tabButton(1, QTabBar.RightSide).hide()
        
        self.tab_widget.tabCloseRequested.connect(self._close_tab)
        
    def _close_tab(self, index):
        
        self.tab_widget.removeTab(index)
        
    def add_tab(self, widget, name):
        
        tab_count = self.tab_widget.count()
        
        for inc in range(0, tab_count):
            tab_title = self.tab_widget.tabText(inc)
            
            if tab_title == name:
                self.tab_widget.removeTab(inc)
                break
                
        self.tab_widget.addTab(widget, name)
        
        tab_count = self.tab_widget.count()
            
        self.tab_widget.setCurrentIndex( (tab_count-1) )
        
    def set_directory(self, directory):
        super(ToolManager, self).set_directory(directory)
        self.rigging_widget.set_directory(directory)
     

        
        
     
class ModelManager(vtool.qt_ui.BasicWidget):
    def _build_widgets(self):
        pass


        



        

        