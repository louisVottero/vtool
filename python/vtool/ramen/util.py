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


def get_joints(filter_text, exclude_text=''):

    filter_text = filter_text.replace(',', ' ')
    split_filter = filter_text.split()

    exclude_text = exclude_text.replace(',', ' ')
    split_exclude = exclude_text.split()

    found = []
    exclude_found = None

    if util.in_maya:
        found = get_joints_maya(split_filter)
        exclude_found = get_joints_maya(split_exclude)

    if util.in_unreal:
        found = get_joints_unreal(split_filter)
        exclude_found = get_joints_unreal(split_exclude)

    result = list(OrderedDict.fromkeys(found))

    if exclude_found:
        found = []
        for thing in result:
            if thing not in exclude_found:
                found.append(thing)
        result = found

    return result


def get_joints_maya(filter_list):
    found = []

    for filter_text in filter_list:
        found += cmds.ls(filter_text, type='joint')

    return found


def get_joints_unreal(filter_list):

    found = []

    rig = unreal_lib.graph.get_current_control_rig()

    if not rig:
        rig = unreal_lib.graph.get_current_control_rig()
    if not rig:
        util.warning('No Unreal control rig set to work on.')
        return

    bones = unreal_lib.space.get_bones(rig, return_names=True)

    for filter_text in filter_list:
        matching = util.unix_match(filter_text, bones)
        if len(matching) > 1:
            matching = util.sort_string_integer(matching)
        if matching:
            found += matching

    return found


def get_sub_controls(control):

    if util.in_maya:
        return attr.get_multi_message(control, 'sub')
