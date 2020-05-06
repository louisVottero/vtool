
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

def was_floating(label):
    settings = util_file.get_vetala_settings_inst()
    floating =  settings.get('%s floating' % label)
    
    return floating

def floating_changed(label, floating):
        
    settings = util_file.get_vetala_settings_inst()
        
    floating_value = True    
    if not floating:
        floating_value = False
            
    settings.set('%s floating' % label, floating_value)

def tab_changed(label, tab_name):

    settings = util_file.get_vetala_settings_inst()
            
    settings.set('%s tab' % label, tab_name)

def get_stored_tab(label):
    settings = util_file.get_vetala_settings_inst()        
    tab = settings.get('%s tab' % label)
    
    return tab
    
def get_adjacent_tab(widget):
    
    parent = widget.parent()
    if parent:
        while parent:
            parent = parent.parent()
            
            if not parent:
                break
            
            class_name = parent.__class__.__name__
            
            if class_name == 'QTabWidget':
                
                tab_count = parent.count()
                
                if tab_count > 0:
                    return str(parent.tabText(tab_count-1))

def get_widget_from_tab_name(tab_name):
    
    main_window = get_maya_window()
    
    tabs = main_window.findChildren(qt.QTabWidget)
    
    for tab in tabs:
        tab_count = tab.count()
        
        for inc in range(0, tab_count):
            tab_text =  str(tab.tabText(inc))
            if tab_text == tab_name:
                return tab

workspace_control_map = {
    'Attribute Editor':'AttributeEditor',
    'Modeling Toolkit':'NEXDockControl', 
    'Channel Box / Layer Editor':'ChannelBoxLayerEditor',
    'Tool Settings':'ToolSettings',
    'Outliner':'Outliner'
}
        
def add_tab(source_control, tab_name):
    
    workspace_control = mel.eval('getUIComponentDockControl("%s", false)' % tab_name)
    
    if cmds.workspaceControl(source_control, q = True, ex = True) and workspace_control:
        
        util.show('Loading %s into tab %s' % (source_control, tab_name))
        
        cmds.workspaceControl(source_control, e = True, tabToControl = (workspace_control, 100))

def delete_workspace_control(name):
    
    if cmds.workspaceControl(name, q=True, exists=True):
        
        cmds.workspaceControl(name,e=True, close=True)
        cmds.deleteUI(name,control=True)    

class MayaDockMixin(MayaQWidgetDockableMixin):
    
    def floatingChanged(self, is_floating):
        
        adjacent_tab = get_adjacent_tab(self)
         
        ui_name = self.title
        
        is_floating = int(is_floating)
        
        floating_changed(ui_name,is_floating)
        
        if not is_floating and adjacent_tab:
            
            tab_changed(ui_name, adjacent_tab)
    
    def show(self, *args, **kwargs):
        
        floating = was_floating(self.title)
        
        super(MayaDockMixin, self).show(dockable = True, floating = floating, area = 'right')
        
            
class MayaBasicMixin(MayaQWidgetBaseMixin):
    pass

class MayaWidgetMixin(MayaDockMixin, qt_ui.BasicWidget):
    pass

class MayaWindowMixin(MayaDockMixin, qt_ui.BasicWindow):
    pass

class MayaDirectoryWindowMixin(MayaDockMixin, qt_ui.DirectoryWindow):
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
        #self.setAllowedAreas(qt.QtCore.Qt.TopDockWidgetArea)
        