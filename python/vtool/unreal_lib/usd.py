# Copyright (C) 2024 Louis Vottero louis.vot@gmail.com    All rights reserved.

from .. import util, util_file

import os
import unreal
from .. import unreal_lib


def import_file(filepath, content_path=None, create_control_rig=True):

    filename = util_file.get_basename_no_extension(filepath)
    content_path = content_path

    if not content_path:
        project_path = os.environ.get('VETALA_PROJECT_PATH')

        folder_path = util_file.remove_common_path_simple(project_path, filepath)
        dirname = util_file.get_dirname(folder_path)
        if dirname:
            index = dirname.find('/.data')
            if index > -1:
                dirname = dirname[:index]
        else:
            dirname = None

        content_path = '/Game/Vetala'

        if dirname:
            content_path = util_file.join_path('/Game/Vetala', dirname)

    if not content_path.startswith('/'):
        content_path = '/' + content_path

    if not content_path.startswith('/Game'):
        content_path = util_file.join_path('/Game', content_path)

    game_dir = unreal.Paths.project_content_dir()
    game_dir = util_file.get_dirname(game_dir)
    full_content_path = util_file.join_path(game_dir, content_path)
    util_file.create_dir(full_content_path)

    options = unreal.UsdStageImportOptions()
    options.import_actors = True
    options.import_at_specific_time_code = False
    options.import_geometry = True
    options.import_skeletal_animations = False
    options.import_level_sequences = False
    options.import_materials = True
    options.kinds_to_collapse = 0

    pass_file = filepath
    temp_file = None
    if not filepath.endswith('.usd'):
        temp_file = util_file.copy_file(filepath, filepath + '.usd')
        pass_file = temp_file

    filename = filename.replace('.', '_')
    asset_path = util_file.join_path(content_path, filename)

    found = []
    found_control_rig = None
    found_skeletal_mesh = None
    preview_mesh = None
    preview_file = None
    control_rig = None

    asset_paths = unreal.EditorAssetLibrary.list_assets(asset_path, recursive=True)
    for path in asset_paths:

        package_name = path.split('.')
        package_name = package_name[0]

        if unreal_lib.core.is_control_rig(package_name) and not found_control_rig:
            found_control_rig = package_name
            control_rig = unreal_lib.core.get_skeletal_mesh_object(found_control_rig)
            # if not unreal_lib.graph.current_control_rig:
            unreal_lib.graph.set_current_control_rig(control_rig)
            # sunreal_lib.graph.current_control_rig = control_rig
            preview_mesh = control_rig.get_preview_mesh()
            asset_import_data = preview_mesh.get_editor_property('asset_import_data')
            preview_file = asset_import_data.get_first_filename()
            break

    if not preview_mesh or preview_file != pass_file:
        task = unreal.AssetImportTask()
        task.set_editor_property('save', True)
        task.set_editor_property('filename', pass_file)
        task.set_editor_property('destination_path', content_path)
        task.set_editor_property('destination_name', filename)
        task.set_editor_property('automated', True)
        task.set_editor_property('options', options)
        task.set_editor_property('replace_existing', True)

        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        asset_tools.import_asset_tasks([task])

    asset_paths = unreal.EditorAssetLibrary.list_assets(asset_path, recursive=True)
    for path in asset_paths:

        package_name = path.split('.')
        package_name = package_name[0]
        util.show('found package:', package_name)
        found.append(package_name)

        if unreal_lib.core.is_skeletal_mesh(package_name):
            found_skeletal_mesh = package_name

    if create_control_rig:
        mesh = None
        if found_skeletal_mesh:
            mesh = unreal_lib.core.get_skeletal_mesh_object(found_skeletal_mesh)
            if mesh and not found_control_rig:
                control_rig = unreal_lib.graph.create_control_rig_from_skeletal_mesh(mesh)
                found_skeletal_mesh = mesh.get_outer().get_name()
                found_control_rig = control_rig.get_outer().get_name()
                found.append(found_control_rig)

    if control_rig:
        unreal_lib.graph.set_current_control_rig(control_rig)
        if mesh:
            control_rig.set_preview_mesh(mesh)

    if temp_file:
        util_file.delete_file(temp_file)

    return found


def export_file(filepath, selection=[]):

    selected_assets = unreal.EditorUtilityLibrary.get_selected_assets_of_class(unreal.SkeletalMesh)
    if not selected_assets:
        util.warning('Please select at skeletal mesh before exporting')

    skeletal_mesh = selected_assets[0]

    export_task = unreal.AssetExportTask()
    export_task.object = skeletal_mesh
    export_task.filename = filepath
    export_task.automated = True
    export_task.replace_identical = True
    export_task.prompt = False

    export_task.exporter = unreal.SkeletalMeshExporterUsd()

    export_options = unreal.SkeletalMeshExporterUSDOptions()

    stage_options = unreal.UsdStageOptions()
    stage_options.up_axis = unreal.UsdUpAxis.Y_AXIS
    export_options.stage_options = stage_options

    export_task.options = export_options

    unreal.Exporter.run_asset_export_task(export_task)

