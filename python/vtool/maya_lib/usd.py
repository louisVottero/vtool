# Copyright (C) 2024 Louis Vottero louis.vot@gmail.com    All rights reserved.

from . import core

import maya.cmds as cmds


def import_file(filepath):
    core.import_usd_file(filepath)


def export_file(filepath):

    selection = cmds.ls(sl=True)

    core.export_usd_file(filepath, selection=selection)
