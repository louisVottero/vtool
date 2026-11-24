from .. import util

from contextlib import contextmanager
from functools import wraps
from collections.abc import Iterable

if util.in_blender:
    import bpy


def get_view_3d_override():
    if (
        bpy.context.window
        and bpy.context.area
        and bpy.context.area.type == 'VIEW_3D'
        and bpy.context.region
        and bpy.context.region.type == 'WINDOW'
    ):
        return {}

    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                region = next(
                    (r for r in area.regions if r.type == 'WINDOW'), None
                )
                override = {
                    'window': window,
                    'screen': window.screen,
                    'area': area,
                }
                if region:
                    override['region'] = region
                return override

    return {}


@contextmanager
def view_3d_context():
    """Context manager to safely run bpy.ops from external Qt/PySide UIs or batch mode."""
    override = get_view_3d_override()
    if override and hasattr(bpy.context, 'temp_override'):
        with bpy.context.temp_override(**override):
            yield
    else:
        yield


def with_view_3d_context(func):
    """Decorator to wrap an entire function in a valid 3D Viewport context."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        with view_3d_context():
            return func(*args, **kwargs)

    return wrapper


def get_objects(names: str | Iterable[str]) -> list:
    if isinstance(names, str):
        names = [names]
    found = [obj for name in names if (obj := bpy.data.objects.get(name)) is not None]
    return found


def get_bone_objects(names: str | Iterable[str]) -> list:
    if isinstance(names, str):
        names = [names]
    target_names = set(names)

    return [
        (obj, bone)
        for obj in bpy.data.objects
        if obj.type == 'ARMATURE'
        for bone in obj.data.bones
        if bone.name in target_names
    ]


def get_bones(filter_list):
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

