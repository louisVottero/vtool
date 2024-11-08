# Copyright (C) 2024 Louis Vottero louis.vot@gmail.com    All rights reserved.

import hou
from .. import util
from .. import util_file
import os


def clear():
    hou.hipFile.clear(suppress_save_prompt=True)


def save(filepath):
    hou.hipFile.save(filepath)


def load(filepath):
    hou.hipFile.load(filepath)


def merge(filepath):
    hou.hipFile.merge(filepath)


def export_nodes(path, nodes):

    util_file.refresh_dir(path, delete_directory=False)

    parent = nodes[0].parent()
    parent_path = nodes[0].path()
    parent_path = util_file.get_dirname(parent_path)
    if parent_path.startswith('/'):
        parent_path = parent_path[1:]

    parent_path += '/nodes.cpio'

    filepath = util_file.join_path(path, parent_path)
    folder_path = util_file.get_dirname(filepath)
    folder_path = util_file.create_dir(folder_path)

    parent.saveItemsToFile(nodes, filepath)


def import_nodes(path, context=None):
    # TODO, consider handling the context with a settings file instead of walking the folder and files.
    folders = util_file.get_folders(path, True, skip_dot_prefix=True)
    for folder in folders:
        context_path = '/' + folder

        folder_path = util_file.join_path(path, folder)
        files = util_file.get_files_with_extension('cpio', folder_path, fullpath=True)

        for filepath in files:
            if not context:
                context = hou.node(context_path)
            if context:
                context.loadItemsFromFile(filepath)
            else:
                util.warning('Could not get context for node import. \nPlease select something or recreate the parents that existed when nodes were exported. \nExpected parents %s' % context_path)
