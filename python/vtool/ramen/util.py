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
    split_filter = filter_text.split(',')
    
    if util.in_maya:
        for split_filter_text in split_filter:
            found += cmds.ls(split_filter_text, type = 'joint')
    if util.in_unreal:
        rig = unreal_lib.util.current_control_rig
        
        if not rig:
            util.warning('No Unreal control rig set to work on.')
            return
        
        bones = unreal_lib.space.get_bones(rig, return_names = True)
        
        for split_filter_text in split_filter:
            matching = util.unix_match(split_filter_text, bones)
            if matching:
                found += matching
    
    return found