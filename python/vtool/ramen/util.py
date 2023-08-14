from .. import util
from .. import unreal_lib

if util.in_maya:
    import maya.cmds as cmds
    
if util.in_unreal:
    import unreal
    
if util.in_houdini:
    import hou

def get_joints(filter_text):
    found = []
    if util.in_maya:
        found = cmds.ls(filter_text, type = 'joint')
    if util.in_unreal:
        rig = unreal_lib.util.current_control_rig
        
        if not rig:
            util.warning('No Unreal control rig set to work on.')
            return
        
        bones = unreal_lib.space.get_bones(rig)
        
        for bone in bones:
            text = str(bone.name)
            
            find = util.find_special(filter_text, text, 'first')
            if not find == (None,None):
                found.append(text)
            
    return found