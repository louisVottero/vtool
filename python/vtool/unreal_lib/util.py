from vtool import util
from vtool import util_file

if util.in_unreal:
    import unreal

current_control_rig = None

def create_static_mesh_asset(asset_name, package_path):
    # Create a new Static Mesh object
    static_mesh_factory = unreal.EditorStaticMeshFactoryNew()
    new_static_mesh = unreal.AssetToolsHelpers.get_asset_tools().create_asset(asset_name, package_path, unreal.ControlRig, static_mesh_factory)

    # Save the new asset
    unreal.AssetToolsHelpers.get_asset_tools().save_asset(new_static_mesh)

    # Return the newly created Static Mesh object
    return new_static_mesh

def create_control_rig_from_skeletal_mesh(skeletal_mesh_object):
    print('outermost', skeletal_mesh_object.get_outermost())
    factory = unreal.ControlRigBlueprintFactory
    rig = factory.create_control_rig_from_skeletal_mesh_or_skeleton(selected_object = skeletal_mesh_object)
    
    return rig

def is_of_type(filepath, type_name):
    
    asset_data = unreal.EditorAssetLibrary.find_asset_data(filepath)
    print(asset_data)
    if asset_data:
        if asset_data.asset_class_path.asset_name == type_name:
            return True

    return False
def is_skeletal_mesh(filepath):
    
    return is_of_type(filepath, 'SkeletalMesh')

def is_control_rig(filepath):
    
    return is_of_type(filepath, 'ControlRigBlueprint')

def set_skeletal_mesh(filepath):
    util.set_env('VETALA_CURRENT_PROCESS_SKELETAL_MESH', filepath)
    
    
    mesh = get_skeletal_mesh_object(filepath)
    control_rigs = find_associated_control_rigs(mesh)
    
    global current_control_rig
    current_control_rig = control_rigs[0]
    
    #create_control_rig_from_skeletal_mesh(mesh)
    
def get_skeletal_mesh():
    path = util.get_env('VETALA_CURRENT_PROCESS_SKELETAL_MESH')
    return path

def get_skeletal_mesh_object(asset_path):
    mesh = unreal.load_object(name = asset_path, outer = None)
    return mesh

def get_control_rig_object(asset_path):
    rig = unreal.load_object(name = asset_path, outer = None)
    return rig

def find_associated_control_rigs(skeletal_mesh_object):
    
    path = skeletal_mesh_object.get_path_name()
    path = util_file.get_dirname(path)
    
    asset_paths = unreal.EditorAssetLibrary.list_assets(path, recursive = True)
    
    print('assets!!')
    print(asset_paths)
    
    control_rigs = []
    
    for asset_path in asset_paths:
        package_name = asset_path.split('.')
        package_name = package_name[0]
        
        if is_control_rig(package_name):
            control_rigs.append(package_name)
    
    found = [unreal.load_object(name = control_rigs[0], outer = None)]
    
    #not working because mesh and skeletal_mesh_object are different types
    #found = []
    #for control_rig in control_rigs:
    #    rig = unreal.load_object(name = control_rig, outer = None)
    #    mesh = rig.get_preview_mesh()
        
        
        #LogPython: compare
        #LogPython: <Object '/Engine/Transient.SK_asset_1' (0x0000073F14C28200) Class 'SkeletalMesh'>
        #LogPython: <Object '/Game/Vetala/examples/ramen/simple_cross_platform/asset/SkeletalMeshes/SK_asset.SK_asset' (0x0000073F9BFF6400) Class 'SkeletalMesh'>
        #if mesh == skeletal_mesh_object:
        #    found.append(rig)
        
    return found

def get_unreal_content_process_path():
    project_path  = util.get_env('VETALA_PROJECT_PATH')
    process_path = util_file.get_current_vetala_process_path()
    
    rel_path = util_file.remove_common_path_simple(project_path, process_path)
    
    content_path = util_file.join_path('/Game/Vetala', rel_path)
    
    return content_path

def get_last_execute_node(graph):
    
    found = None
    for node in graph.get_nodes():
        execute_context = node.find_pin('ExecuteContext')
        sources = execute_context.get_linked_source_pins()
        targets = execute_context.get_linked_target_pins()
        
        if sources and not targets:
            found = node
    
    print('last execute!!')
    print(found)
    return found


            
    

def get_graph_model_controller(model, main_graph = None):
    
    if not main_graph:
        main_graph = current_control_rig
    
    model_name = model.get_node_path()
    model_name = model_name.replace(':', '')
    model_control = main_graph.get_controller_by_name(model_name)
    
    return model_control

def get_unreal_control_shapes():
    shapes = ['Arrow2',
              'Arrow4', 
              'Arrow', 
              'Box', 
              'Circle', 
              'Diamond', 
              'HalfCircle', 
              'Hexagon', 
              'Octagon', 
              'Pyramid', 
              'QuarterCircle', 
              'RoundedSquare',
              'RoundedTriangle', 
              'Sphere',
              'Square',
              'Star4',
              'Triangle',
              'Wedge']
    
    sub_names = ['Thin','Thick','Solid']
    
    found = []
    
    for shape in shapes:
        for name in sub_names:
            found.append( shape + '_' + name )
    
    defaults = ['None', 'Default']
    
    found = defaults + found
    
    return found 
        