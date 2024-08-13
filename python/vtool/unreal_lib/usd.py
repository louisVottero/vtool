# Copyright (C) 2024 Louis Vottero louis.vot@gmail.com    All rights reserved.

from .. import util, util_file

import os
import unreal
from .. import unreal_lib


def import_file(filepath):
    project_path = os.environ.get('VETALA_PROJECT_PATH')

    filename = util_file.get_basename_no_extension(filepath)
    folder_path = util_file.remove_common_path_simple(project_path, filepath)
    dirname = util_file.get_dirname(folder_path)
    index = dirname.find('/.data')
    if index > -1:
        dirname = dirname[:index]

    content_path = util_file.join_path('/Game/Vetala', dirname)
    game_dir = unreal.Paths.project_content_dir()
    full_content_path = util_file.join_path(game_dir, 'Vetala')
    full_content_path = util_file.join_path(full_content_path, dirname)
    util_file.create_dir(full_content_path)

    options = unreal.UsdStageImportOptions()
    options.import_actors = True
    options.import_geometry = True
    options.import_skeletal_animations = True
    options.import_level_sequences = True
    options.import_materials = True

    task = unreal.AssetImportTask()
    task.set_editor_property('save', True)
    task.set_editor_property('filename', filepath)
    task.set_editor_property('destination_path', content_path)
    task.set_editor_property('destination_name', filename)
    task.set_editor_property('automated', True)
    task.set_editor_property('options', options)
    task.set_editor_property('replace_existing', True)

    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    asset_tools.import_asset_tasks([task])

    asset_paths = unreal.EditorAssetLibrary.list_assets(content_path, recursive=True)

    util.show(len(asset_paths))

    asset_path = util_file.join_path(content_path, filename)

    unreal.EditorAssetLibrary.save_directory(asset_path, recursive=True, only_if_is_dirty=True)

    found = []
    found_control_rig = None
    found_skeletal_mesh = None
    for asset_path in asset_paths:

        package_name = asset_path.split('.')
        package_name = package_name[0]
        full_path = unreal.Paths.convert_relative_path_to_full(asset_path)
        full_path = full_path.replace('/Game/', '')
        full_path = util_file.join_path(game_dir, full_path)
        # util.show(full_path)
        util.show(package_name)
        found.append(package_name)

        if unreal_lib.core.is_skeletal_mesh(package_name):
            found_skeletal_mesh = package_name

        if unreal_lib.core.is_control_rig(package_name):
            found_control_rig = package_name

    mesh = None
    if found_skeletal_mesh:
        mesh = unreal_lib.core.get_skeletal_mesh_object(found_skeletal_mesh)
    if found_control_rig:
        rig = unreal_lib.core.get_skeletal_mesh_object(found_control_rig)
    if not found_control_rig and found_skeletal_mesh:
        rig = unreal_lib.graph.create_control_rig_from_skeletal_mesh(mesh)
        found_skeletal_mesh = mesh.get_outer().get_name()
        found_control_rig = rig.get_outer().get_name()
        unreal.EditorAssetLibrary.save_asset(found_control_rig, only_if_is_dirty=True)

    if rig:
        unreal_lib.graph.current_control_rig = rig

    return found
