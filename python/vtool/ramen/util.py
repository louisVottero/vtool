from .. import util
from .. import unreal_lib

if util.in_maya:
    import maya.cmds as cmds
    
if util.in_unreal:
    import unreal
    
if util.in_houdini:
    import hou

def get_joints(filter_text):
    joints = []
    if util.in_maya:
        joints = cmds.ls(filter_text, type = 'joint')
    if util.in_unreal:
        rig = unreal_lib.util.current_control_rig
        print('rig!!!', rig)
        if not rig:
            util.warning('Control unreal control rig set to work on.')
        unreal.log(filter_text)
        
    return joints