# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

import maya.cmds as cmds
import maya.utils


from maya.app.general.mayaMixin import MayaQWidgetBaseMixin, MayaQWidgetDockableMixin

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
    
    if ToolManager._last_instance:
        ToolManager._last_instance.add_dock(window, window.title)
    
    if not ToolManager._last_instance:
        ui_core.create_window(window)


ui_core.new_tool_signal.signal.connect(load_into_tool_manager) 

def add_tool_tab(window):
    
    if ToolManager._last_instance:
        ToolManager._last_instance.add_tab(window, window.title)
    
    if not ToolManager._last_instance:
        ui_core.create_window(window)    


def process_manager():
    
    window = ui_rig.process_manager()
    
    add_tool_tab(window)
    
def pose_manager(shot_sculpt_only = False):
    
    window = ui_rig.pose_manager(shot_sculpt_only)
    
    add_tool_tab(window)

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
    
    util.set_env('VETALA_SETTINGS', process.get_default_directory())
        
    manager = ToolManager(name)
    manager.set_directory(directory)
    manager.show()
    #funct = lambda : ui_core.create_window(manager)
    
    #maya.utils.executeDeferred(funct)
    
    return manager




def process_manager(directory = None):
    
    window = ui_rig.process_manager()
    
    if ToolManager._last_instance:
        
        ToolManager._last_instance.add_tab(window, title = util.get_custom('vetala_name', 'VETALA'))
    
    if not ToolManager._last_instance:
        funct = lambda : ui_core.create_window(window)
        maya.utils.executeDeferred(funct)
    
    if directory:
        window.set_code_directory(directory)
    
    return window


#class ToolManager(ui_core.MayaDockMixin, qt_ui.BasicWidget):
class ToolManager(ui_core.MayaDockMixin,qt.QWidget):
    title = (util.get_custom('vetala_name', 'VETALA') + ' HUB')
    _last_instance = None
    
    def __init__(self,name = None):
        
        self.__class__._last_instance = self
        
        if name:
            self.title = name
        
        self.default_docks = []
        self.docks = []
        
        super(ToolManager, self).__init__()
        
        self.setWindowTitle(self.title)
        
        self.main_layout = qt.QVBoxLayout()
        self.setLayout(self.main_layout)
        self._build_widgets()
        
        
    def _build_widgets(self):

        self.main_layout.setAlignment(qt.QtCore.Qt.AlignTop)
        
        header_layout = qt.QHBoxLayout()
        
        version = qt.QLabel('%s' % util_file.get_vetala_version())
        version.setMaximumHeight(30)
        
        header_layout.addWidget(version)
        
        self.main_layout.addLayout(header_layout)
        
        self.dock_window = Dock()
        
        self.main_layout.addWidget(self.dock_window)
        
        self.rigging_widget = ui_rig.RigManager()
        
        self.add_tab(self.rigging_widget, 'RIG')

    def add_tab(self, widget, name):
        
        self.add_dock(widget, name)
        
    def add_dock(self, widget , name):
        
        self.dock_window.add_dock(widget, name)
        
    def set_directory(self, directory):
        
        #super(ToolManager, self).set_directory(directory)
        
        self.rigging_widget.set_directory(directory)
        
        
class Dock(ui_core.MayaBasicMixin,qt_ui.BasicWindow):
    
    def __init__(self, name = None):
        
        self.docks = []
        
        self.connect_tab_change = True
        
        super(Dock, self).__init__()
        
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
        self.setDockOptions( self.AllowTabbedDocks)
        #self.setDockOptions( self.AnimatedDocks | self.AllowTabbedDocks)
        
    def _tab_changed(self, index):
        
        pass
        """
        if not self.tab_change_hide_show:
            return
        
        docks = self._get_dock_widgets()
        
        docks[index].hide()
        docks[index].show()
        """
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
        
        #tab_bar = self._get_tab_bar()
        
        """
        if tab_bar:
            if self.connect_tab_change:
                tab_bar.currentChanged.connect(self._tab_changed)
                self.connect_tab_change = False
        """
        return dock_widget

    
    

        
        