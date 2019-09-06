
import traceback

from vtool import qt_ui, qt
from vtool import util
from vtool import util_file

import maya.OpenMayaUI as OpenMayaUI
import maya.cmds as cmds
import maya.mel as mel
import maya.utils

from maya.app.general.mayaMixin import MayaQWidgetBaseMixin, MayaQWidgetDockableMixin


#--- signals
class new_scene_object(qt.QtCore.QObject):
    signal = qt_ui.create_signal()

class open_scene_object(qt.QtCore.QObject):
    signal = qt_ui.create_signal()
    
class read_scene_object(qt.QtCore.QObject):
    signal = qt_ui.create_signal()
    
class new_tool_object(qt.QtCore.QObject):
    signal = qt_ui.create_signal(object)
    
new_scene_signal = new_scene_object()
open_scene_signal = open_scene_object()
read_scene_signal = read_scene_object()
new_tool_signal = new_tool_object() 

def emit_new_scene_signal():
    new_scene_signal.signal.emit()

def emit_open_scene_signal():
    open_scene_signal.signal.emit()
    
def emit_read_scene_signal():
    read_scene_signal.signal.emit()
    
def emit_new_tool_signal(window):
    new_tool_signal.signal.emit(window)

#--- script jobs
job_new_scene = None
job_open_scene = None
job_read_scene = None

def create_scene_script_jobs():
    
    global job_new_scene
    global job_open_scene
    global job_read_scene
    
    job_new_scene = cmds.scriptJob( event = ['NewSceneOpened', 'from vtool.maya_lib import ui_core;ui_core.emit_new_scene_signal();print "V:\t\tEmit new scene."'], protected = False)
    job_open_scene = cmds.scriptJob( event = ['SceneOpened', 'from vtool.maya_lib import ui_core;ui_core.emit_open_scene_signal();print "V:\t\tEmit open scene."'], protected = False)
    job_read_scene = cmds.scriptJob( ct = ['readingFile', 'from vtool.maya_lib import ui_core;ui_core.emit_read_scene_signal();print "V:\t\tEmit reading scene."'], protected = False)

create_scene_script_jobs()
  
def delete_scene_script_jobs():
    
    global job_new_scene
    global job_open_scene
    global job_read_scene
    
    cmds.scriptJob(kill = job_new_scene)
    cmds.scriptJob(kill = job_open_scene)
    cmds.scriptJob(kill = job_read_scene)

#--- ui 

def get_maya_window():
    
    if qt_ui.is_pyqt():
        import sip
        #Get the maya main window as a QMainWindow instance
        ptr = OpenMayaUI.MQtUtil.mainWindow()
        return sip.wrapinstance(long(ptr), qt.QtCore.QObject)
    
    if qt_ui.is_pyside():
        try:
            from shiboken import wrapInstance
        except:
            from PySide.shiboken import wrapInstance
    
    if qt_ui.is_pyside2():
        from shiboken2 import wrapInstance
             
    maya_window_ptr = OpenMayaUI.MQtUtil.mainWindow()
    return wrapInstance(long(maya_window_ptr), qt.QWidget)

def create_window(ui, dock_area = 'right'): 
    
    #this was needed to have the ui predictably load.
    mel.eval('updateRendererUI;')
    
    ui_name = str(ui.objectName())
    
    old_parent = ui.parent()
    old_parent_name = None
    if old_parent:
        old_parent_name = old_parent.objectName()
    
    util.show('Creating dock window.', ui_name)
    
    window = MayaWidgetMixin()
    window.main_layout.addWidget(ui)
    window.setWindowTitle(ui_name)
    
    
    if old_parent_name and old_parent_name.find('Mixin') > -1:
        old_parent.close()
        cmds.deleteUI(old_parent_name)
    
        
    allowed_areas = ['right', 'left']
    
    window.setDockableParameters(dockable=True, 
                                    floating=None, 
                                    area=dock_area, 
                                    allowedArea=allowed_areas, 
                                    width=None, 
                                    widthSizingProperty=None, 
                                    minWidth=None, 
                                    height=None, 
                                    heightSizingProperty=None, 
                                    x=None, 
                                    y=None, 
                                    retain=True, 
                                    plugins=None, 
                                    controls=None, 
                                    uiScript=None, 
                                    closeCallback=None)
    
    window.show()
    """
    try:
        dock = DockControlWrapper()
        dock.set_dock_name(dock_name)
        dock.set_label(ui_name)
        dock.set_dock_area(dock_area)
        dock.set_allowed_areas(allowed_areas)
        dock.create()
        #cmds.dockControl(dock_name,aa=allowed_areas, a = dock_area, content=ui_name, label=ui_name,  fl = False, visible = True, fcc = self._floating_changed)
        ui.show()
    
    except:
        #do not remove
        util.warning('%s window failed to load. Maya may need to finish loading.' % ui_name)
        util.error( traceback.format_exc() )
    """
class DockControlWrapper(object):

    def __init__(self):
        
        self._dock_area = 'right'
        self._dock_name = 'dock'
        self._allowed_areas = ['right', 'left']
        self._label = ''

    def _floating_changed(self):
        
        settings_dir = util.get_env('VETALA_SETTINGS')
        
        settings = util_file.SettingsFile()
        
        settings.set_directory(settings_dir)
        
        floating = cmds.dockControl(self._dock_name, floating = True, q = True )
                
        settings.set('%s floating' % self._label, floating)
        
    def _get_was_floating(self):
        settings_dir = util.get_env('VETALA_SETTINGS')
        settings = util_file.SettingsFile()
        settings.set_directory(settings_dir)
        
        settings.has_setting('%s floating' % self._label)
        
        floating =  settings.get('%s floating' % self._label)
                
        return floating
        
    def _exists(self):
        
        if cmds.dockControl(self._dock_name, exists = True):
            return True
        
        return False  

    def set_dock_area(self, dock_area):
        self._dock_area = dock_area
        
    def set_dock_name(self, dock_name):
        self._dock_name = dock_name
        
        
        
    def set_label(self, label):
        self._label = label
    
    def set_allowed_areas(self, areas_list):
        self._allowed_areas = areas_list
        
    def create(self):
        
        floating = False
        
        if self._get_was_floating():
            floating = True
        
        if self._exists():
            cmds.dockControl(self._dock_name, visible = True)
            return
        else:
            cmds.dockControl(self._dock_name,aa=self._allowed_areas, a = self._dock_area, content=self._label, label=self._label,  fl = floating, visible = True, fcc = self._floating_changed)
  
def delete_workspace_control(name):
    
    
    
    if cmds.workspaceControl(name, q=True, exists=True):
        print 'workspace exists, deleting'
        cmds.workspaceControl(name,e=True, close=True)
        cmds.deleteUI(name,control=True)    

class MayaDockMixin(MayaQWidgetDockableMixin):
    def show(self, *args, **kwargs):
        
        #cmds.workspaceControl(workspaceControlName, label=self.windowTitle(), retain=retain, loadImmediately=True, floating=True, initialWidth=width, widthProperty=widthSizingProperty, initialHeight=height, heightProperty=heightSizingProperty, requiredPlugin=plugins, requiredControl=controls)
        
        super(MayaDockMixin, self).show(dockable = True, *args, **kwargs)

class MayaBasicMixin(MayaQWidgetBaseMixin):
    pass

class MayaWidgetMixin(MayaDockMixin, qt_ui.BasicWidget):
    pass

class MayaWindowMixin(MayaDockMixin, qt_ui.BasicWindow):
    pass

class MayaWindow(qt_ui.BasicWindow):
    def __init__(self):
        super(MayaWindow, self).__init__( get_maya_window() )
        
class MayaDirectoryWindow(qt_ui.DirectoryWindow):
    def __init__(self):
        super(MayaDirectoryWindow, self).__init__( get_maya_window() )

class MayaDockWidget(MayaBasicMixin, qt.QDockWidget):
    
    def __init__(self, parent = None, *args, **kwargs):
        super(MayaDockWidget, self).__init__(parent = parent, *args, **kwargs)
        
        #self.setSizePolicy(qt.QSizePolicy.Expanding, qt.QSizePolicy.Expanding)
        self.setAllowedAreas(qt.QtCore.Qt.TopDockWidgetArea)
        