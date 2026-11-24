import bpy
from . import util


@util.with_view_3d_context
def import_file(filepath):
    result = bpy.ops.wm.usd_import(filepath=filepath, scale=1, apply_unit_conversion_scale=False)
    return result


def export_file(filepath, selection=[]):
    result = None
    return result
