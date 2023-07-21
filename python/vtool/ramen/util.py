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
        path = unreal_lib.util.get_skeletal_mesh()
        unreal.log(filter_text)
        unreal.log(path)
    return joints