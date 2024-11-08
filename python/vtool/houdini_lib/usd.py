# Copyright (C) 2024 Louis Vottero louis.vot@gmail.com    All rights reserved.

from .. import util_file
from .. import util

if util.in_houdini:
    import hou
    from .. import houdini_lib


def import_file(filepath):
    """
    TODO: Fill description.
    Args:
        filepath (str): TODO: Fill description.

    Returns:

    """
    filepath = util_file.fix_slashes(filepath)
    filename = util_file.get_basename_no_extension(filepath)

    project_path = filepath.split('.data')[0]

    if project_path.endswith('/'):
        project_path = project_path[:-1]

    project = util_file.get_basename(project_path)

    obj = hou.node('/obj')
    geo = obj.node(project)
    if not geo:
        geo = obj.createNode('geo', project)

    usd = geo.node('usd_%s' % filename)

    if not usd:
        usd = geo.createNode('kinefx::usdcharacterimport', 'usd_%s' % filename)
        usd.parm('usdsource').set(1)
        usd.parm('usdfile').set(filepath)

    houdini_lib.graph.set_current_character_import(usd)

