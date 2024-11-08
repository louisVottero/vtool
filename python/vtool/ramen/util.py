# Copyright (C) 2024 Louis Vottero louis.vot@gmail.com    All rights reserved.
from collections import OrderedDict

from .. import util

if util.in_maya:
    import maya.cmds as cmds
    from .. maya_lib import attr

if util.in_unreal:
    import unreal
    from .. import unreal_lib

if util.in_houdini:
    import hou


def get_joints(filter_text):
    found = []
    filter_text = filter_text.replace(',', ' ')
    split_filter = filter_text.split()

    if util.in_maya:
        for split_filter_text in split_filter:
            found += cmds.ls(split_filter_text, type='joint')
    if util.in_unreal:
        rig = unreal_lib.graph.get_current_control_rig()

        if not rig:
            rig = unreal_lib.graph.get_current_control_rig()
        if not rig:
            util.warning('No Unreal control rig set to work on.')
            return

        bones = unreal_lib.space.get_bones(rig, return_names=True)

        for split_filter_text in split_filter:
            matching = util.unix_match(split_filter_text, bones)
            if len(matching) > 1:
                matching = util.sort_string_integer(matching)
            if matching:
                found += matching

    found = list(OrderedDict.fromkeys(found))

    return found


def get_sub_controls(control):

    if util.in_maya:
        return attr.get_multi_message(control, 'sub')
