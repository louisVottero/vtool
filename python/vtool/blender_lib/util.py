from .. import util

import bpy


def get_joints(filter_list):
    bones = [bone.name
             for obj in bpy.context.scene.objects if obj.type == 'ARMATURE'
             for bone in obj.data.bones
             ]

    found = []
    for filter_text in filter_list:
        matching = util.unix_match(filter_text, bones)
        if len(matching) > 1:
            matching = util.sort_string_integer(matching)
        if matching:
            found += matching
    print('found', found)
    return found

