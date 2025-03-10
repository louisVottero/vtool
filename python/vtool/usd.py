# Copyright (C) 2024 Louis Vottero louis.vot@gmail.com    All rights reserved.

from . import util

usd = None

if util.in_houdini:
    from .houdini_lib import usd
if util.in_maya:
    from .maya_lib import usd
if util.in_unreal:
    from .unreal_lib import usd


def import_file(filepath):
    if not usd:
        return
    result = usd.import_file(filepath)

    return result


def export_file(filepath, selection=[]):

    if not usd:
        return

    result = usd.export_file(filepath, selection)

    return result
