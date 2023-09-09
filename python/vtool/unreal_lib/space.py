
from . import util as unreal_util

from .. import util

if util.in_unreal:
    import unreal


def get_bones(control_rig = None, return_names = False):
    rig = None
    if not control_rig:
        rig = unreal_util.current_control_rig
    else:
        rig = control_rig
    if not rig:
        util.warning('No control rig found')
        return
    
    elements = rig.hierarchy.get_all_keys()
    
    found = []
    
    for element in elements:
        print(element.name, element.type)
        if element.type == unreal.RigElementType.BONE:
            if return_names:
                element = str(element.name)
                found.append(element)
            else:
                
                found.append(element)
            
    return found
        