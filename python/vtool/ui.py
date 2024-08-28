# Copyright (C) 2024 Louis Vottero louis.vot@gmail.com    All rights reserved.

from . import util

if util.in_houdini:
    from .houdini_lib import ui
elif util.in_maya:
    from .maya_lib import ui
elif util.in_unreal:
    from .unreal_lib import ui


def process_manager():
    if util.in_houdini:
        ui.process_manager()
    elif util.in_maya:
        ui.tool_manager()
    elif util.in_unreal:
        ui.process_manager()
