from vtool import util
from vtool import util_file
from ..process_manager import process
if util.in_unreal:
    import unreal

def create_static_mesh_asset(asset_name, package_path):
    # Create a new Static Mesh object
    static_mesh_factory = unreal.EditorStaticMeshFactoryNew()
    new_static_mesh = unreal.AssetToolsHelpers.get_asset_tools().create_asset(asset_name, package_path, unreal.ControlRig, static_mesh_factory)

    # Save the new asset
    unreal.AssetToolsHelpers.get_asset_tools().save_asset(new_static_mesh)

    # Return the newly created Static Mesh object
    return new_static_mesh

def is_skeletal_mesh(filepath):
    asset_data = unreal.EditorAssetLibrary.find_asset_data(filepath)

    if asset_data:
        return asset_data.asset_class == unreal.SkeletalMesh

    return False

def set_skeletal_mesh(filepath):
    util.set_env('VETALA_CURRENT_PROCESS_SKELETAL_MESH', filepath)
    
def get_skeletal_mesh():
    path = util.get_env('VETALA_CURRENT_PROCESS_SKELETAL_MESH')
    return path
    
def get_unreal_content_process_path():
    project_path  = util.get_env('VETALA_PROJECT_PATH')
    process_path = util_file.get_current_vetala_process_path()
    
    rel_path = util_file.remove_common_path_simple(project_path, process_path)
    
    content_path = util_file.join_path('/Game/Vetala', rel_path)
    
    return content_path

