# Copyright (C) 2024 Louis Vottero louis.vot@gmail.com    All rights reserved.

from . import graph as unreal_graph

from .. import util

if util.in_unreal:
    import unreal


def get_bones(control_rig=None, return_names=False):
    rig = None
    if control_rig:
        rig = control_rig
    else:
        rig = unreal_graph.get_current_control_rig()
    if not rig:
        util.warning('No control rig found')
        return

    elements = rig.hierarchy.get_all_keys()

    found = []

    for element in elements:

        if element.type == unreal.RigElementType.BONE:
            if return_names:
                element = str(element.name)
                found.append(element)
            else:

                found.append(element)

    return found
