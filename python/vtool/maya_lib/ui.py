# Copyright (C) 2022 Louis Vottero louis.vot@gmail.com    All rights reserved.

from __future__ import absolute_import

from .. import qt_ui, qt
from .. import util, util_file

if util.is_in_maya():
    import maya.cmds as cmds

from .ui_lib import ui_rig
from . import ui_core

def load_into_tool_manager(window):
    """
    if ToolManager._last_instance:
        parent_name = ToolManager._last_instance.parent().objectName()
        
        if parent_name.find('WorkspaceControl') > -1:
            window.show()
            window_name = window.parent().objectName()
            
            cmds.workspaceControl(window_name, e = True, tabToControl = (parent_name,-1))#, uiScript = command, li = False, retain = False)
    """
    if not ToolManager._last_instance:
        window.show()
        #window_name = window.parent().objectName()
        
        #cmds.workspaceControl(window_name, e = True)#, tabToControl = (parent_name,-1))#, uiScript = command, li = False, retain = False)
       
    if hasattr(window, 'initialize_settings'):
        window.show()
        window.initialize_settings()
    
def pose_manager(shot_sculpt_only = False):
    
    window = ui_rig.pose_manager(shot_sculpt_only)
    
    load_into_tool_manager(window)
    
def shape_combo():
    
    window = ui_rig.shape_combo()
    
    load_into_tool_manager(window)
    
    
def picker():
    
    window = ui_rig.picker()
    
    if ToolManager._last_instance:
        ToolManager._last_instance.add_tab(window, window.title)
    

def tool_manager(name = None, directory = None):
    """
    This command launches the Vetala Hub UI that hosts many different UIs
    """
    
    title = ToolManager.title
    if name:
        title = name
    workspace_name =title + 'WorkspaceControl'
    
    ui_core.delete_workspace_control(workspace_name)
    
    manager = ToolManager(name)
    
    if not ui_core.was_floating(manager.title):
        tab_name = ui_core.get_stored_tab(manager.title)
        manager.show()
        ui_core.add_tab(workspace_name, tab_name)
    else:
        manager.show()
        
    if directory:
        manager.set_directory(directory)
        
    return manager

def process_manager(directory = None):
    """
    This command launches the process manager which lists processes, their data and code. 
    """
    ui_core.delete_workspace_control(ui_rig.ProcessMayaWindow.title + 'WorkspaceControl')
    window = ui_rig.ProcessMayaWindow(load_settings=True)
    
    if directory:
        window.set_directory(directory)
    
    window.show()
    
    return window

def process_manager_settings():
    ui_core.delete_workspace_control(ui_rig.ProcessMayaSettingsWindow.title + 'WorkspaceControl')
    window = ui_rig.ProcessMayaSettingsWindow()

    window.show()
    
    return window

def ramen():
    
    ui_core.delete_workspace_control(ui_rig.RamenMayaWindow.title + 'WorkspaceControl')
    window = ui_rig.RamenMayaWindow()   
    window.show()
    return window

def script_manager(directory):
    """
    This command launches a script manager ui which can be used for sharing scripts in a team. 
    """
    ui_core.delete_workspace_control(ui_rig.ScriptMayaWindow.title + 'WorkspaceControl')
    window = ui_rig.ScriptMayaWindow()
       
    window.set_directory(directory)
    window.show()
    return window

class ToolManager(ui_core.MayaDirectoryWindowMixin):
#class ToolManager(ui_core.MayaDockMixin, qt_ui.BasicWidget):
#class ToolManager(ui_core.MayaDockMixin,qt.QWidget):
    title = (util.get_custom('vetala_name', 'VETALA') + ' HUB')
    #_last_instance = None
    
    def __init__(self,name = None):
        
        if name:
            ToolManager.title = name
            self.title = name
        
        self.default_docks = []
        self.docks = []
        
        super(ToolManager, self).__init__()
        
        self.setWindowTitle(self.title)
        
        ui_core.new_tool_signal.signal.connect(load_into_tool_manager)
        
    def _build_widgets(self):

        self.main_layout.setAlignment(qt.QtCore.Qt.AlignTop)
        
        header_layout = qt.QHBoxLayout()
        
        version = qt.QLabel('%s' % util_file.get_vetala_version())
        version.setMaximumHeight(30)
        
        header_layout.addWidget(version)
        
        self.main_layout.addLayout(header_layout)
        
        self.rigging_widget = ui_rig.RigManager()
        self.main_layout.addWidget(self.rigging_widget)
        
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
        
        if old_parent_name and old_parent_name.find('Mixin') > -1:
            old_parent.close()
            cmds.deleteUI(old_parent_name)
        
        self.addDockWidget(qt.QtCore.Qt.TopDockWidgetArea, dock_widget)
        
        if docks:
            self.tabifyDockWidget( docks[-1], dock_widget)
        
        dock_widget.show()
        dock_widget.raise_()
        
        return dock_widget 
    
    