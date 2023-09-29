from vtool import util
from vtool import util_file

if util.in_unreal:
    import unreal

current_control_rig = None

class UnrealTextDataObject(list):
    
    def __init__(self):
        self.sub_objects = []
        
    def text(self):
        
        text_lines = self
        
        sub_texts = []
        
        for sub_object in self.sub_objects:
            
            sub_text_current = sub_object.text()
            sub_texts.append(sub_text_current)
        
        if sub_texts:
            sub_text = '\n'.join(sub_texts)
            text_lines.insert(1, sub_text)
        
        
        return '\n'.join(text_lines)
        
        
    def run(self, controller = None):
        
        
        text = self.text()
        
        if not controller:
            current_control_rig = get_current_control_rig()
            controller = current_control_rig.get_controller()
        
        #print(text)
        
        result = controller.import_nodes_from_text(text)
        

class UnrealExportTextData(object):
    
    def __init__(self):
        
        self.filepath = None
        self.lines = []
        self.objects = []
        
    def _get_text_lines(self, filepath):
        
        lines = util_file.get_file_lines(filepath)
        return lines
        
    def _deep_iterate(self, list_value):
        lines = []
        for item in list_value:
            
            print('item', item)
            if isinstance(item, list):
                sub_lines = self._deep_iterate(item)
                lines += sub_lines
            else:
                lines.append(item)
            
        
        return lines
        
    def _parse_lines(self, lines):
        
        self.objects = []
        object_history = []
        
        depth = 0
        
        for line in lines:
            if not line:
                continue
            if line.lstrip().startswith('Begin Object Class=') or line.lstrip().startswith('Begin Object Name='):
                unreal_object = UnrealTextDataObject()
                unreal_object.append(line)
                #unreal_object.sub_objects.append(UnrealTextDataObject())
                
                object_history.append(unreal_object)
                
                depth += 1
                
            elif(line.lstrip() == 'End Object'):
                
                if depth > 0:
                    
                    object_history[(depth-1)].append(line)
                    
                    if depth == 1:
                        self.objects.append(object_history[0])
                        object_history = []
                    
                    elif len(object_history) > 1:
                        object_history[(depth-2)].sub_objects.append(object_history[depth-1])
                        object_history.pop(-1)
                    
                    depth -= 1
                
            else:
                object_history[(depth-1)].append(line)
        
        #for text_data in self.objects:
        #    text_data.run()
        
        #lines = self._deep_iterate(self.objects)
        #for line in lines:
        #    print(line)
        
    def load_file(self, filepath):
        
        self.filepath = filepath
        
        self.lines = self._get_text_lines(filepath)
        self._parse_lines(self.lines)

def create_static_mesh_asset(asset_name, package_path):
    # Create a new Static Mesh object
    static_mesh_factory = unreal.EditorStaticMeshFactoryNew()
    new_static_mesh = unreal.AssetToolsHelpers.get_asset_tools().create_asset(asset_name, package_path, unreal.ControlRig, static_mesh_factory)

    # Save the new asset
    unreal.AssetToolsHelpers.get_asset_tools().save_asset(new_static_mesh)

    # Return the newly created Static Mesh object
    return new_static_mesh

def create_control_rig_from_skeletal_mesh(skeletal_mesh_object):
    factory = unreal.ControlRigBlueprintFactory
    rig = factory.create_control_rig_from_skeletal_mesh_or_skeleton(selected_object = skeletal_mesh_object)
    
    return rig

def is_of_type(filepath, type_name):
    
    asset_data = unreal.EditorAssetLibrary.find_asset_data(filepath)
    
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

def get_current_control_rig():
    
    control_rig_controller = current_control_rig
    print('current control rig', control_rig_controller)
    if not control_rig_controller:
        control_rigs = unreal.ControlRigBlueprint.get_currently_open_rig_blueprints()
        if not control_rigs:
            return
        
        return control_rigs[0]
    else:
        return control_rig_controller
    
def add_construct_graph():
    current_control_rig = get_current_control_rig()
    current_model = None
    for model in current_control_rig.get_all_models():
        model_name = model.get_graph_name()
        
        if model_name.find('Construction Event Graph') > -1:
            current_model = model
        
    if not current_model:
        construct_model = current_control_rig.add_model('Construction Event Graph')
        current_model = construct_model
    
        print(current_model, type(current_model))
        model_control = current_control_rig.get_controller_by_name(current_model.get_graph_name())
        
        model_control.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_PrepareForExecution', 'Execute', unreal.Vector2D(0, 0), 'PrepareForExecution')
        
    return current_model

def add_backward_graph():
    print('add backward')
    current_control_rig = get_current_control_rig()
    current_model = None
    for model in current_control_rig.get_all_models():
        model_name = model.get_graph_name()
        print('model name', model_name)
        if model_name.find('Backward Solve Graph') > -1:
            print('here loading current model')
            current_model = model
        
    if not current_model:
        construct_model = current_control_rig.add_model('Backward Solve Graph')
        current_model = construct_model
    
        model_control = current_control_rig.get_controller_by_name(current_model.get_graph_name())
        
        model_control.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_InverseExecution', 'Execute', unreal.Vector2D(0, 0), 'InverseExecution')
    
    return current_model