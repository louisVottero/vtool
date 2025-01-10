# Copyright (C) 2024 Louis Vottero louis.vot@gmail.com    All rights reserved.
from collections import OrderedDict

from .. import util
from .. import util_file

if util.in_maya:
    import maya.cmds as cmds
    from .. maya_lib import attr

if util.in_unreal:
    import unreal
    from .. import unreal_lib

if util.in_houdini:
    import hou
    from .. import houdini_lib


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

    if util.in_houdini:
        found = get_joints_houdini(split_filter)
        exclude_found = get_joints_houdini(split_exclude)

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


def get_joints_houdini(filter_list):

    character_import = houdini_lib.graph.character_import

    if not character_import:
        return

    character_inst = hou.node(character_import)

    geometry = character_inst.geometry(1)
    name = geometry.findPointAttrib('name')
    bones = list(name.strings())

    found = []
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


def get_control_name(description1=None, description2=None, side=None, sub=False, numbering=True):

    if not sub:
        control_name_inst = util_file.ControlNameFromSettingsFile()
        control_name_inst.set_use_side_alias(False)

        control_name_inst.set_number_in_control_name(numbering)

        if side:
            side = side[0]

        description = None

        if description2:
            description = description1 + '_' + description2
        else:
            description = description1

        control_name = control_name_inst.get_name(description, side)
    else:
        control_name = description.replace('CNT_', 'CNT_SUB_1_')

    return control_name


def get_joint_description(joint_name, joint_token):

    if joint_token:
        description = joint_name
        description = description.replace(joint_token, '')
        description = util.replace_last_number(description, '')
        description = description.lstrip('_')
        description = description.rstrip('_')
    else:
        description = joint_name

    return description
