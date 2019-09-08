# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

import maya.cmds as cmds
import maya.utils


from maya.app.general.mayaMixin import MayaQWidgetBaseMixin, MayaQWidgetDockableMixin
from maya import OpenMayaUI as omui

from vtool import qt_ui, qt
from vtool import util, util_file

from vtool.maya_lib.ui_lib import ui_fx
from vtool.maya_lib.ui_lib import ui_rig
from vtool.maya_lib.ui_lib import ui_anim
from vtool.maya_lib.ui_lib import ui_model
import ui_core

from vtool.process_manager import process


import core
import attr
import space
import geo
import deform
import rigs_util

    
def load_into_tool_manager(window):
    
    ui_core.delete_workspace_control(window.title + 'WorkspaceControl')
    
    if ToolManager._last_instance:
        parent_name = ToolManager._last_instance.parent().objectName()
        
        if parent_name.find('WorkspaceControl') > -1:
            window.show()
            window_name = window.parent().objectName()
            
            cmds.workspaceControl(window_name, e = True, tabToControl = (parent_name,100) )        
            
    if not ToolManager._last_instance:
        ui_core.create_window(window)


ui_core.new_tool_signal.signal.connect(load_into_tool_manager) 

def add_tool_tab(window):
    
    #if ToolManager._last_instance:
    #    ToolManager._last_instance.add_tab(window, window.title)
    
    if not ToolManager._last_instance:
        ui_core.create_window(window)    


def pose_manager(shot_sculpt_only = False):
    
    window = ui_rig.pose_manager(shot_sculpt_only)
    
    load_into_tool_manager(window)
    
    #add_tool_tab(window)

def shape_combo():
    
    window = ui_rig.shape_combo()
    
    load_into_tool_manager(window)
    
    """
    if ToolManager._last_instance:
        ToolManager._last_instance.add_tab(window, window.title)
    
    if not ToolManager._last_instance:
        ui_core.create_window(window)
    """
def picker():
    
    window = ui_rig.picker()
    
    if ToolManager._last_instance:
        ToolManager._last_instance.add_tab(window, window.title)
    
    if not ToolManager._last_instance:
        ui_core.create_window(window)

def tool_manager(name = None, directory = None):
    
    print 'here!'
    
    ui_core.delete_workspace_control(ToolManager.title + 'WorkspaceControl')
    
    manager = ToolManager(name)
    manager.show(dockable = True, uiScript = 'tool_manager(restore = True)')
    
    if directory:
        manager.set_directory(directory)
        
    return manager
    """
    if restore:
        print 'restoring!'
        restored_control = omui.MQtUtil.getCurrentParent()
        
        mixin_ptr = omui.MQtUtil.findControl(manager.objectName())
        omui.MQtUtil.addWidgetToMayaLayout(long(mixin_ptr), long(restored_control))
    #else:
    """




def process_manager(directory = None):
    
    
    window = ui_rig.ProcessMayaWindow._last_instance
    """
    if not window:
        window = ui_rig.process_manager()
    
    
    
    #add_tool_tab(window)
    """
    if directory:
        window.set_code_directory(directory)
    
    return window
    


class ToolManager(ui_core.MayaDirectoryWindowMixin):
#class ToolManager(ui_core.MayaDockMixin, qt_ui.BasicWidget):
#class ToolManager(ui_core.MayaDockMixin,qt.QWidget):
    title = (util.get_custom('vetala_name', 'VETALA') + ' HUB')
    #_last_instance = None
    
    def __init__(self,name = None):
        
        #self.__class__._last_instance = self
        
        if name:
            self.title = name
        
        self.default_docks = []
        self.docks = []
        
        super(ToolManager, self).__init__()
        
        self.setWindowTitle(self.title)
        
        #self.main_layout = qt.QVBoxLayout()
        #self.setLayout(self.main_layout)
        #self._build_widgets()
        
        
    def _build_widgets(self):

        self.main_layout.setAlignment(qt.QtCore.Qt.AlignTop)
        
        header_layout = qt.QHBoxLayout()
        
        version = qt.QLabel('%s' % util_file.get_vetala_version())
        version.setMaximumHeight(30)
        
        header_layout.addWidget(version)
        
        self.main_layout.addLayout(header_layout)
        
        #self.dock_window = Dock()
        
        #self.main_layout.addWidget(self.dock_window)
        
        self.rigging_widget = ui_rig.RigManager()
        self.main_layout.addWidget(self.rigging_widget)
        #self.add_tab(self.rigging_widget, 'RIG')

    def add_tab(self, widget, name):
        
        self.add_dock(widget, name)
        
    def add_dock(self, widget , name):
        self.dock_window.add_dock(widget, name)
        
    def set_directory(self, directory):
        
        super(ToolManager, self).set_directory(directory)
        
        self.rigging_widget.set_directory(directory)
        
        
class Dock(ui_core.MayaBasicMixin,qt_ui.BasicWindow):
    
    def __init__(self, name = None):
        
        self.docks = []
        
        super(Dock, self).__init__()
        
        
    def _get_dock_widgets(self):
        
        children = self.children()
        
        found = []
        
        for child in children:
            
            if isinstance(child, qt.QDockWidget):
                found.append(child)
                
        return found
        
    def _build_widgets(self):
        
        self.main_widget.setSizePolicy(qt.QSizePolicy.Minimum, qt.QSizePolicy.Minimum)
        self.centralWidget().hide()
        
        self.setTabPosition(qt.QtCore.Qt.TopDockWidgetArea, qt.QTabWidget.West)
        self.setDockOptions( self.AllowTabbedDocks)
        
    def add_dock(self, widget , name):
        
        docks = self._get_dock_widgets()
        
        for dock in docks:
            if dock.windowTitle() == name:
                dock.deleteLater()
                dock.close()
        
        old_parent = widget.parent()
        old_parent_name = None
        if old_parent:
            old_parent_name = old_parent.objectName()
            
        dock_widget = ui_core.MayaDockWidget(self)
        dock_widget.setWindowTitle(name)
        dock_widget.setWidget(widget)
        
        parent = dock_widget.parent()
        print parent.objectName()
        print dock_widget.objectName()
        
        if old_parent_name and old_parent_name.find('Mixin') > -1:
            old_parent.close()
            cmds.deleteUI(old_parent_name)
        
        self.addDockWidget(qt.QtCore.Qt.TopDockWidgetArea, dock_widget)
        
        if docks:
            self.tabifyDockWidget( docks[-1], dock_widget)
        
        dock_widget.show()
        dock_widget.raise_()
        
        return dock_widget 