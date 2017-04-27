# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

import maya.cmds as cmds
import maya.utils


from vtool import qt_ui, qt
from vtool import util_file

from vtool.maya_lib.ui_lib import ui_fx
from vtool.maya_lib.ui_lib import ui_rig
from vtool.maya_lib.ui_lib import ui_anim
from vtool.maya_lib.ui_lib import ui_model
import ui_core



import core
import attr
import space
import geo
import deform
import rigs_util

    
def load_into_tool_manager(window):
    
    if ToolManager._last_instance:
        ToolManager._last_instance.add_dock(window, window.title)
    
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
    
        self.default_docks = []
        self.docks = []
        
        super(ToolManager, self).__init__()
        
    def _build_widgets(self):

        self.setMinimumWidth(300)
        
        self.main_widget.setSizePolicy(qt.QSizePolicy.Minimum, qt.QSizePolicy.Minimum)
        
        self.main_layout.setAlignment(qt.QtCore.Qt.AlignTop)
        
        header_layout = qt.QHBoxLayout()
        
        version = qt.QLabel('%s' % util_file.get_vetala_version())
        version.setMaximumHeight(30)
        
        header_layout.addWidget(version)
        
        self.main_layout.addLayout(header_layout)
        
        self.dock_window = DockWindow()
        
        self.main_layout.addWidget(self.dock_window)
        
        #self.modeling_widget = ui_model.ModelManager()
        self.rigging_widget = ui_rig.RigManager()
        #self.animation_widget = ui_anim.AnimationManager()
        ##self.shot_widget = qt.QWidget()
        #self.fx_widget = ui_fx.FxManager()
        
        #self.add_tab(self.modeling_widget, 'MODEL')
        self.add_tab(self.rigging_widget, 'RIG')
        #self.add_tab(self.animation_widget, 'ANIMATE')
        #self.add_tab(self.fx_widget, 'FX')
        
        self.default_docks[0].raise_()
        
        #this was one when there was a model dock before rig
        #self.default_docks[1].raise_()
        
    def _get_tab_bar(self):
        return self.dock_window._get_tab_bar()
        
    def _tab_moved(self, from_index, to_index):
        
        self.dock_window.tabifyDockWidget(self.docks[from_index], self.docks[to_index])
        return
        
    def _add_default_tabs(self):
        
        for dock in self.default_docks:
            try:
                dock.close()
            except:
                pass
            
        self.default_docks = []
        
        self.add_tab(self.modeling_widget, 'MODEL')
        self.add_tab(self.rigging_widget, 'RIG')
        self.add_tab(self.animation_widget, 'ANIMATE')
        self.add_tab(self.fx_widget, 'FX')
        
        
    def _close_tab(self, index):
        
        self.tab_widget.removeTab(index)
        
    def add_tab(self, widget, name):
        
        dock = self.add_dock(widget, name)
        
        dock.setFeatures(dock.DockWidgetMovable| dock.DockWidgetFloatable)
        self.default_docks.append(dock)
        
    def add_dock(self, widget , name):
        
        dock = self.dock_window.add_dock(widget, name)
        
        return dock
        
    def set_directory(self, directory):
        
        super(ToolManager, self).set_directory(directory)
        self.rigging_widget.set_directory(directory)
        
class DockWindow(qt_ui.BasicWindow):
    
    def __init__(self, name = None):
        
        self.docks = []
        
        self.connect_tab_change = True
        
        super(DockWindow, self).__init__()
        
        self.tab_change_hide_show = True
        
        
        
    def _get_tab_bar(self):
        
        children = self.children()
        
        for child in children:
            
            if isinstance(child, qt.QTabBar):
                return child
        
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
        self.setDockOptions( self.AnimatedDocks | self.AllowTabbedDocks)
        #self.setSizePolicy(qt.QSizePolicy.Maximum, qt.QSizePolicy.Maximum)
        
    def _tab_changed(self, index):
        
        if not self.tab_change_hide_show:
            return
        
        docks = self._get_dock_widgets()
        
        docks[index].hide()
        docks[index].show()
        
    def add_dock(self, widget , name):
        
        docks = self._get_dock_widgets()
            
        for dock in docks:
            if dock.windowTitle() == name:
                dock.deleteLater()
                dock.close()
        
        dock_widget = DockWidget(name, self)
        dock_widget.setWidget(widget)
        
        self.addDockWidget(qt.QtCore.Qt.TopDockWidgetArea, dock_widget)
        
        if docks:
            self.tabifyDockWidget( docks[-1], dock_widget)
        
        dock_widget.show()
        dock_widget.raise_()
        
        tab_bar = self._get_tab_bar()
        
        if tab_bar:
            if self.connect_tab_change:
                tab_bar.currentChanged.connect(self._tab_changed)
                self.connect_tab_change = False
        
        return dock_widget

    
    
class DockWidget(qt.QDockWidget):
    
    def __init__(self, name, parent):
        super(DockWidget, self).__init__(name, parent)
        
        self.setSizePolicy(qt.QSizePolicy.Minimum, qt.QSizePolicy.Minimum)
        self.setAllowedAreas(qt.QtCore.Qt.TopDockWidgetArea)
        
        