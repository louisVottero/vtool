import maya.cmds as cmds

from vtool.maya_lib import attr

class Picker(object):
    
    def __init__(self, picker_group = None):
        self.picker_group = picker_group
        self.load_picker_group(picker_group)
    
    def load_picker_group(self, picker_group):
        if picker_group:
            self.picker_group = picker_group
    
    def create_picker_group(self):
    
        name = 'picker_gr'
        group = name
        
        self.load_picker_group(group)
        
        if not cmds.objExists(name):
            group = cmds.group(em = True, n = name)
            attr.hide_keyable_attributes(group)
            
        attribute = '%s.DATA' % group
            
        if not cmds.objExists(attribute):
            cmds.addAttr(group, ln = 'DATA', dt = 'string')
            cmds.setAttr('%s.DATA' % group, l = True)
    
        
    
        return group
    
    def set_data(self, view_data):
        
        self.create_picker_group()
        
        attribute = '%s.DATA' % self.picker_group
        
        if cmds.objExists(attribute):
            cmds.setAttr(attribute, l = False)
            cmds.setAttr(attribute, str(view_data), type = 'string')
        
        
        cmds.setAttr(attribute, l = True)
        
    def get_data(self):
        
        if not self.picker_group:
            return
        
        view_data = cmds.getAttr('%s.DATA' % self.picker_group)
        
        if view_data:
            view_data = eval(view_data)
        if not view_data:
            view_data = None
        
        return view_data