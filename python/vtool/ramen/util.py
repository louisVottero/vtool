# Copyright (C) 2024 Louis Vottero louis.vot@gmail.com    All rights reserved.
from collections import OrderedDict
import functools
import uuid

from .. import util
from .. import util_file

in_maya = util.in_maya
in_unreal = util.in_unreal
in_houdini = util.in_houdini
in_blender = util.in_blender

if in_maya:
    import maya.cmds as cmds
    from .. maya_lib import attr
    from .. maya_lib import core

if in_unreal:
    import unreal
    from .. import unreal_lib

if in_houdini:
    import hou
    from .. import houdini_lib

if in_blender:
    import bpy
    from .. import blender_lib


def decorator_undo(title=''):

    def decorator(func):

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if util.in_unreal:
                unreal_lib.graph.undo_bracket.open(title)
            try:
                return func(*args, **kwargs)
            finally:
                if util.in_unreal:
                    unreal_lib.graph.undo_bracket.close(title)

        return wrapper

    return decorator


def decorator_auto_compile_off(func):

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        track_id = uuid.uuid4()
        if util.in_unreal:
            unreal_lib.graph.auto_compile.set_state(False, track_id)
        try:
            return func(*args, **kwargs)
        finally:
            if util.in_unreal:
                unreal_lib.graph.auto_compile.set_state(True, track_id)

    return wrapper


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

    if util.in_blender:
        found = get_joints_blender(split_filter)
        exclude_found = get_joints_blender(split_exclude)

    if not found:
        return []

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

    found = houdini_lib.graph.get_joints(filter_list)
    return found


def get_joints_blender(filter_list):

    found = blender_lib.util.get_bones(filter_list)
    return found


def get_sub_controls(control):

    if util.in_maya:
        return attr.get_multi_message(control, 'sub')


def get_control_name(description1=None, description2=None, side=None, sub=False, numbering=True):

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

    if sub:
        control_name = control_name.replace('CNT_', 'CNT_SUB_1_')

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


def get_uniform_shape_names():
    names = ['Circle_Thin', 'Circle_Thick', 'Circle_Solid',
             'Square_Thin', 'Square_Thick', 'Square_Solid',
             'Sphere_Thin', 'Sphere_Thick', 'Sphere_Solid',
             'Cube_Thin', 'Cube_Thick', 'Cube_Solid']

    return names

