import bpy


def import_file(filepath):
    print(filepath)
    result = bpy.ops.wm.usd_import(filepath=filepath)
    return result


def export_file(filepath, selection=[]):
    result = None
    return result
