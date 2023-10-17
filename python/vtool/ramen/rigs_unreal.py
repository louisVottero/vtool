import copy

from . import rigs

from vtool import util
from vtool import util_file

in_unreal = util.in_unreal

if in_unreal:
    from .. import unreal_lib
    import unreal
    
def _name(unreal_node):
    if not in_unreal:
        return
    return unreal_node.get_node_path()
    
#--- Unreal
class UnrealUtilRig(rigs.PlatformUtilRig):
    
    def __init__(self):
        super(UnrealUtilRig, self).__init__()
        
        self.construct_controller = None
        self.construct_node = None
        
        self.forward_controller = None
        self.forward_node = None
        
        self.backward_controller = None
        self.backward_node = None
        
        self.graph = None
        self.library = None
        self.controller = None
        
        self._attribute_cache = None
        self.library_functions = {}
        self._cached_library_function_names = ['vetalaLib_Control',
                                               'vetalaLib_ControlSub', 
                                               'vetalaLib_GetJointDescription', 
                                               'vetalaLib_ConstructName',
                                               'vetalaLib_GetParent']
    
    def _init_graph(self):
        if not self.graph:
            return 
        
        unreal_lib.util.add_forward_solve()
        
        if not self.construct_controller:
            model = unreal_lib.util.add_construct_graph()
            self.construct_controller = self.graph.get_controller_by_name(model.get_graph_name())
        
        if not self.backward_controller:
            model = unreal_lib.util.add_backward_graph()
            self.backward_controller = self.graph.get_controller_by_name(model.get_graph_name())
    
        self.function_library = self.graph.get_controller_by_name('RigVMFunctionLibrary')
    
    def _init_rig_function(self):
        if not self.graph:
            return
        
        rig_name = 'vetala_%s' % self.__class__.__name__
        rig_name = rig_name.replace('Unreal', '')
        
        found = self.controller.get_graph().find_function(rig_name)
        if found:
            self.function = found
            self.function_controller = self.graph.get_controller_by_name(self.function.get_node_path())
            return
            
        self.function = self.controller.add_function_to_library(rig_name, True, unreal.Vector2D(0,0))
        self.function_controller = self.graph.get_controller_by_name(self.function.get_node_path())
        
        self._initialize_node_attributes()
        self._initialize_inputs()
        self._initialize_outputs()
        
        self._build_function_graph()
    
    def _init_library(self):
        if not self.graph:
            return
        
        util.show('Init Library')
        
        controller = self.function_library
        
        library_path = unreal_lib.util.get_custom_library_path()
        
        #library_files = util_file.get_files_with_extension('data', library_path, fullpath = True)
        
        missing = False
        
        for name in self._cached_library_function_names:
            
            function = controller.get_graph().find_function(name)
            if function:
                self.library_functions[name] = function
            else:
                missing = True
        
        if missing:
            functions_before = controller.get_graph().get_functions()
            
            function_file = util_file.join_path(library_path, 'RigVMFunctionLibrary.data')
            text = util_file.get_file_text(function_file)
            controller.import_nodes_from_text(text)
            
            functions_after = controller.get_graph().get_functions()
            
            new_function_names = []
        
            for name in self._cached_library_function_names:
                if name in self.library_functions:
                    continue
                
                if name == 'RigVMFunctionLibrary':
                    continue
                
                new_function_names.append(name)
                
                self.library_functions[name] = controller.get_graph().find_function(name) 

            for function in functions_after:
                if not function in functions_before:
                    name = function.get_node_path()
                    
                    if not name in new_function_names:
                        controller.remove_function_from_library(name)
                

    
    def _add_bool_in(self, name, value):
        value = str(value)
        value = value.lower()
        
        self.function_controller.add_exposed_pin(name, unreal.RigVMPinDirection.INPUT, 'bool', 'None', value)
        
    def _add_int_in(self, name, value):
        value = str(value)
        
        self.function_controller.add_exposed_pin(name, unreal.RigVMPinDirection.INPUT, 'int32', 'None', value)
        
    def _add_color_array_in(self, name, value):
        
        color = value[0]
        
        color_pin = self.function_controller.add_exposed_pin(name, unreal.RigVMPinDirection.INPUT, 'TArray<FLinearColor>', '/Script/CoreUObject.LinearColor', '')
        self.function_library.insert_array_pin('%s.%s' % (self.function.get_name(), color_pin), -1, '')
        
        self.function_library.set_pin_default_value('%s.%s.0.R' % (self.function.get_name(), color_pin), str(color[0]), False)
        self.function_library.set_pin_default_value('%s.%s.0.G' % (self.function.get_name(), color_pin), str(color[1]), False)
        self.function_library.set_pin_default_value('%s.%s.0.B' % (self.function.get_name(), color_pin), str(color[2]), False)
    
    def _add_color_array_out(self, name, value):
        
        color = value[0]
        
        color_pin = self.function_controller.add_exposed_pin(name, unreal.RigVMPinDirection.OUTPUT, 'TArray<FLinearColor>', '/Script/CoreUObject.LinearColor', '')
        self.function_library.insert_array_pin('%s.%s' % (self.function.get_name(), color_pin), -1, '')
        
        self.function_library.set_pin_default_value('%s.%s.0.R' % (self.function.get_name(), color_pin), str(color[0]), False)
        self.function_library.set_pin_default_value('%s.%s.0.G' % (self.function.get_name(), color_pin), str(color[1]), False)
        self.function_library.set_pin_default_value('%s.%s.0.B' % (self.function.get_name(), color_pin), str(color[2]), False)
    
    def _add_transform_array_in(self, name):
        transform_pin = self.function_controller.add_exposed_pin(name, unreal.RigVMPinDirection.INPUT, 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', '')
        
        
        #self.function_controller.insert_array_pin('%s.%s' % (self.function.get_name(),transform_pin), -1, '')
    
    def _add_vector_array_in(self, name):
        pin = self.function_controller.add_exposed_pin(name, unreal.RigVMPinDirection.INPUT, 'TArray<FVector>', '/Script/CoreUObject.Vector', '()')
    
    def _add_transform_array_out(self, name):
        transform_pin = self.function_controller.add_exposed_pin(name, unreal.RigVMPinDirection.OUTPUT, 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', '')
        #self.function_controller.insert_array_pin('%s.%s' % (self.function.get_name(),transform_pin), -1, '')
        
    def _initialize_inputs(self):
        
        inputs = self.rig.attr.inputs
        for name in inputs:
            value, attr_type = self.rig.attr._in_attributes_dict[name]
            
            if attr_type == rigs.AttrType.INT:
                self._add_int_in(name, value)
            
            if attr_type == rigs.AttrType.BOOL:
                self._add_bool_in(name, value)
            
            if attr_type == rigs.AttrType.COLOR:
                self._add_color_array_in(name, value)
                

            if attr_type == rigs.AttrType.STRING:
                if value is None:

                    value = ''
                self.function_controller.add_exposed_pin(name, unreal.RigVMPinDirection.INPUT, 'FString', 'None', value)
                
            if attr_type == rigs.AttrType.TRANSFORM:
                self._add_transform_array_in(name)
        
            if attr_type == rigs.AttrType.VECTOR:
                self._add_vector_array_in(name)
        
    def _initialize_node_attributes(self):
        
        self.function_controller.add_exposed_pin('uuid', unreal.RigVMPinDirection.INPUT, 'FString', 'None', '')
        self.function_controller.add_exposed_pin('mode', unreal.RigVMPinDirection.INPUT, 'int32', 'None', '')
        
        node_attrs = self.rig.attr.node
        for name in node_attrs:
            value, attr_type = self.rig.attr._node_attributes_dict[name]
            
            if attr_type == rigs.AttrType.INT:
                self._add_int_in(name, value)
            
            if attr_type == rigs.AttrType.BOOL:
                self._add_bool_in(name, value)
            
            if attr_type == rigs.AttrType.COLOR:
                self._add_color_array_in(name, value)
                
            if attr_type == rigs.AttrType.STRING:
                if value is None:

                    value = ''
                self.function_controller.add_exposed_pin(name, unreal.RigVMPinDirection.INPUT, 'FString', 'None', value)
                
            if attr_type == rigs.AttrType.TRANSFORM:
                self._add_transform_array_in(name)
                
            if attr_type == rigs.AttrType.VECTOR:
                self._add_vector_array_in(name)
                
    def _initialize_outputs(self):
        #function_library = self.graph.get_controller_by_name('RigVMFunctionLibrary')
        
        outputs = self.rig.attr.outputs
        for name in outputs:
            
            value, attr_type = self.rig.attr._out_attributes_dict[name]
            
            if attr_type == rigs.AttrType.COLOR:
                self._add_color_array_out(name, value)
                
            if attr_type == rigs.AttrType.STRING:
                if value is None:

                    value = ''
                self.function_controller.add_exposed_pin(name, unreal.RigVMPinDirection.OUTPUT, 'FString', 'None', value)
                
            if attr_type == rigs.AttrType.TRANSFORM:
                self._add_transform_array_out(name)

    def _get_function_node(self, function_controller):
        
        if not function_controller:
            return
        
        nodes = function_controller.get_graph().get_nodes()
        
        if not nodes:
            return
            
        for node in nodes:
            
            pin = function_controller.get_graph().find_pin('%s.uuid' % _name(node))
            if pin:
                node_uuid = pin.get_default_value()
                if node_uuid == self.rig.uuid:
                    return node
    
    def _add_construct_node_to_graph(self):
        function_node = self.construct_controller.add_function_reference_node(self.function, unreal.Vector2D(100, 100), _name(self.function))
        self.construct_node = function_node
        
        last_construct = unreal_lib.util.get_last_execute_node(self.construct_controller.get_graph())
        if not last_construct:
            self.construct_controller.add_link('PrepareForExecution.ExecuteContext', '%s.ExecuteContext' % (function_node.get_node_path()))
        else:
            self.construct_controller.add_link('%s.ExecuteContext' % last_construct.get_node_path(), '%s.ExecuteContext' % (function_node.get_node_path()))
        self.construct_controller.set_pin_default_value('%s.uuid' % function_node.get_node_path(), self.rig.uuid, False)
    
    def _add_forward_node_to_graph(self):
        
        controller = self.forward_controller
        
        function_node = controller.add_function_reference_node(self.function, unreal.Vector2D(100, 100), self.function.get_node_path())
        self.forward_node = function_node
        
        controller.set_pin_default_value(f'{_name(function_node)}.mode', '1', False)
        
        last_forward = unreal_lib.util.get_last_execute_node(controller.get_graph())
        if not last_forward:
            controller.add_link('BeginExecution.ExecuteContext', f'{_name(function_node)}.ExecuteContext')
        else:
            self.forward_controller.add_link(f'{_name(last_forward)}.ExecuteContext', f'{_name(function_node)}.ExecuteContext')
        self.forward_controller.set_pin_default_value(f'{_name(function_node)}.uuid', self.rig.uuid, False)

    def _add_backward_node_to_graph(self):
        
        controller = self.backward_controller
        
        function_node = controller.add_function_reference_node(self.function, unreal.Vector2D(100, 100), self.function.get_node_path())
        self.backward_node = function_node
        
        controller.set_pin_default_value(f'{_name(function_node)}.mode', '2', False)
        
        last_backward = unreal_lib.util.get_last_execute_node(controller.get_graph())
        if not last_backward:
            controller.add_link('InverseExecution.ExecuteContext', f'{_name(function_node)}.ExecuteContext')
        else:
            controller.add_link(f'{_name(last_backward)}.ExecuteContext', f'{_name(function_node)}.ExecuteContext')
        
        controller.set_pin_default_value(f'{_name(function_node)}.uuid', self.rig.uuid, False)

    def _reset_array(self, name):
        self.construct_controller.clear_array_pin('%s.%s' % (_name(self.construct_node), name))
        self.forward_controller.clear_array_pin('%s.%s' % (_name(self.forward_node), name))
        
        self.construct_controller.set_pin_default_value('%s.%s' % (self.construct_node.get_node_path(), name), '()', True)
        self.forward_controller.set_pin_default_value('%s.%s' % (self.forward_node.get_node_path(), name), '()', True)

    def _add_array_entry(self, name, value):
        pass

    def _function_set_attr(self, name, custom_value = None):
        if not self.construct_controller:
            return
        if not self.forward_controller:
            return
        
        value, value_type = self.rig.attr.get(name, True)
        util.show('\t\tSet Unreal Function %s Pin %s %s: %s' % (self.__class__.__name__, name,value_type, value))
        
        if custom_value:
            value = custom_value
        
        if self._attribute_cache:
            if value == self._attribute_cache.get(name):
                return
            else:
                self._attribute_cache.set(name, value)
        
        if value_type == rigs.AttrType.INT:
            value = str(value)
            self.construct_controller.set_pin_default_value('%s.%s' % (_name(self.construct_node), name), value, False)
            self.forward_controller.set_pin_default_value('%s.%s' % (_name(self.construct_node), name), value, False)
        
        if value_type == rigs.AttrType.BOOL:
            value = str(value)  
            value = value.lower()
            self.construct_controller.set_pin_default_value('%s.%s' % (_name(self.construct_node), name), value, False)
            self.forward_controller.set_pin_default_value('%s.%s' % (_name(self.construct_node), name), value, False)
        
        if value_type == rigs.AttrType.STRING:
            if value is None:

                value = ''
            if isinstance(value, list):
                value = value[0]
                
            self.construct_controller.set_pin_default_value('%s.%s' % (_name(self.construct_node), name), value, False)
            self.forward_controller.set_pin_default_value('%s.%s' % (_name(self.forward_node), name), value, False)
        
        if value_type == rigs.AttrType.COLOR:
            self._reset_array(name)
            
            if not isinstance(value[0], list):
                value = [value]
            
            inc = 0
            for color in value:
            
                pin_name = f'{_name(self.construct_node)}.{name}'
            
                self.construct_controller.insert_array_pin(pin_name, -1, '')
                self.construct_controller.set_pin_default_value(f'{pin_name}.{inc}.R', str(color[0]), True)
                self.construct_controller.set_pin_default_value(f'{pin_name}.{inc}.G', str(color[1]), True)
                self.construct_controller.set_pin_default_value(f'{pin_name}.{inc}.B', str(color[2]), True)
                
                inc += 1
            
        if value_type == rigs.AttrType.TRANSFORM:
            self._reset_array(name)
            
            if not value:
                return
            
            construct_pin = '%s.%s' % (self.construct_node.get_node_path(), name)
            forward_pin = '%s.%s' % (self.forward_node.get_node_path(), name)
            
            inc = 0
            for joint in value:
                self.construct_controller.insert_array_pin(construct_pin, -1, '')
                self.forward_controller.insert_array_pin(forward_pin, -1, '')
                
                self.construct_controller.set_pin_default_value('%s.%s.Type' % (construct_pin, inc), 'Bone', False)
                self.construct_controller.set_pin_default_value('%s.%s.Name' % (construct_pin, inc), joint, False)
                
                self.forward_controller.set_pin_default_value('%s.%s.Type' % (forward_pin, inc), 'Bone', False)
                self.forward_controller.set_pin_default_value('%s.%s.Name' % (forward_pin, inc), joint, False)
                
                inc+=1
                
        if value_type == rigs.AttrType.VECTOR:
            self._reset_array(name)
            
            if not value:
                return
            construct_pin = '%s.%s' % (self.construct_node.get_node_path(), name)
            forward_pin = '%s.%s' % (self.forward_node.get_node_path(), name)
            
            if not isinstance(value[0], list):
                value = [value]
            
            inc = 0
            for vector in value:
                self.construct_controller.insert_array_pin(construct_pin, -1, '')
                self.forward_controller.insert_array_pin(forward_pin, -1, '')
                
                self.construct_controller.set_pin_default_value(f'{construct_pin}.{inc}.X', str(vector[0]), False)
                self.construct_controller.set_pin_default_value(f'{construct_pin}.{inc}.Y', str(vector[1]), False)
                self.construct_controller.set_pin_default_value(f'{construct_pin}.{inc}.Z', str(vector[2]), False)
                
                
                inc+=1

    def _build_function_graph(self):    
        return
    
    def _build_function_construct_graph(self):
        return
    
    def _build_function_forward_graph(self):
        return
    
    def _build_function_backward_graph(self):
        return
    
    def set_node_position(self, position_x, position_y):
        
        if self.construct_node:
            self.construct_controller.set_node_position_by_name(_name(self.construct_node), unreal.Vector2D(position_x, position_y))
        if self.forward_node:
            self.forward_controller.set_node_position_by_name(_name(self.forward_node), unreal.Vector2D(position_x, position_y))
        
    @property
    def controls(self):
        return

    @controls.setter
    def controls(self, value):
        return

    
    @property
    def parent(self):
        return
    
    @parent.setter
    def parent(self, value):
        return
    
    @property
    def shape(self):
        return self.rig.attr.get('shape')
    
    @shape.setter
    def shape(self, str_shape):
        
        if not str_shape:
            str_shape = 'Default'
        
        self.rig.attr.set('shape', str_shape)
        
        self._function_set_attr('shape')

    def load(self):
        super(UnrealUtilRig, self).load()
        
        
        if not self.graph:
            
            self.graph = unreal_lib.util.current_control_rig
            
            if not self.graph:
                control_rigs = unreal.ControlRigBlueprint.get_currently_open_rig_blueprints()
                if not control_rigs:
                    return
                unreal_lib.util.current_control_rig = control_rigs[0]
                self.graph = control_rigs[0]
                
            if not self.graph:
                util.warning('No control rig set, cannot load.')
                return 
        
        if not self.library:
            self.library = self.graph.get_local_function_library()
        if not self.controller:
            self.controller = self.graph.get_controller(self.library)
        
        if not self.forward_controller:
            self.forward_controller = self.graph.get_controller_by_name('RigVMModel')
        
        models = self.graph.get_all_models()
        for model in models:
            if not self.construct_controller:
                if _name(model).find('Construction Event Graph') > -1:
                    self.construct_controller = unreal_lib.util.get_graph_model_controller(model)
            if not self.backward_controller:
                if _name(model).find('Backwards Solve Graph') > -1:
                    self.backward_controller = unreal_lib.util.get_graph_model_controller(model)    
                
        if not self.construct_controller:
            util.warning('No construction graph found.')
            return
        
        if not self.construct_node:
            self.construct_node = self._get_function_node(self.construct_controller)
        if not self.forward_node:
            self.forward_node = self._get_function_node(self.forward_controller)
        if not self.backward_node:
            self.backward_node = self._get_function_node(self.backward_controller)
        
        if self.construct_controller:
            self.rig.dirty = False
        
    def build(self):
        super(UnrealUtilRig, self).build()
        
        if not in_unreal:
            return
        
        if not self.graph:
            util.warning('No control rig for Unreal rig')
            return
        #function_node = self.construct_controller.get_graph().find_node(self.function.get_node_path())
        
        self._init_graph()
        self._init_library()
        self._init_rig_function()
        
        
        if not self.construct_node:
            self._add_construct_node_to_graph()
            
        if not self.forward_node:
            self._add_forward_node_to_graph()
            
        if not self.backward_node:
            self._add_backward_node_to_graph()
        
        if not self.construct_node:
            util.warning('No construct function for Unreal rig')
            return
        
        for name in self.rig.attr.node:
            self._function_set_attr(name)
        
        for name in self.rig.attr.inputs:
            self._function_set_attr(name)
        
        self._attribute_cache = copy.deepcopy(self.rig.attr)
        
    def unbuild(self):
        super(UnrealUtilRig, self).unbuild()
        
    def delete(self):
        super(UnrealUtilRig, self).delete()
        if not self.graph:
            return
        
        if not self.construct_node:
            self.load()
        
        super(UnrealUtilRig, self).unbuild()
        
        if self.construct_node:
            self.construct_controller.remove_node_by_name(_name(self.construct_node))
        
        if self.forward_node:
            self.forward_controller.remove_node_by_name(_name(self.forward_node))
            
        if self.backward_node:
            self.backward_controller.remove_node_by_name(_name(self.backward_node))

class UnrealFkRig(UnrealUtilRig):
    

    
    def _build_function_graph(self):
        super(UnrealFkRig, self)._build_function_graph()
        if not self.graph:
            return
        
        switch = self.function_controller.add_template_node('DISPATCH_RigVMDispatch_SwitchInt32(in Index)', unreal.Vector2D(225, -160), 'DISPATCH_RigVMDispatch_SwitchInt32')
        self.function_controller.insert_array_pin(f'{_name(switch)}.Cases', -1, '')
        self.function_controller.add_link('Entry.ExecuteContext', f'{_name(switch)}.ExecuteContext')
        self.function_controller.add_link('Entry.mode', f'{_name(switch)}.Index')
        self.function_controller.add_link(f'{_name(switch)}.Completed', 'Return.ExecuteContext')
        
        self.function_controller.add_link(f'{_name(switch)}.ExecuteContext', 'Return.ExecuteContext')
        
        self.switch = switch
        
        
        self._build_function_construct_graph()
        self._build_function_forward_graph()
        self._build_function_backward_graph()
        
    def _build_function_construct_graph(self):
        controller = self.function_controller
        
        for_each = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayIterator(in Array,out Element,out Index,out Count,out Ratio)', unreal.Vector2D(1500, -1250), 'DISPATCH_RigVMDispatch_ArrayIterator')
        
        controller.add_link(f'{_name(self.switch)}.Cases.0', '%s.ExecuteContext' % (for_each.get_node_path()))
                
        controller.add_link('Entry.joints', '%s.Array' % (for_each.get_node_path()))
        
        control_node = self.library_functions['vetalaLib_Control']
        parent_node = self.library_functions['vetalaLib_GetParent']
        joint_description_node = self.library_functions['vetalaLib_GetJointDescription']
        
        control = controller.add_function_reference_node(control_node, unreal.Vector2D(2500, -1300), _name(control_node))
        parent = controller.add_function_reference_node(parent_node, unreal.Vector2D(1880, -1450), _name(parent_node))
        joint_description = controller.add_function_reference_node(joint_description_node, unreal.Vector2D(1900, -1000), _name(joint_description_node))
        
        controller.add_link('Entry.color', f'{_name(control)}.color')
        controller.add_link('Entry.sub_color', f'{_name(control)}.sub_color')
        controller.add_link('Entry.shape', f'{_name(control)}.shape')
        controller.add_link('Entry.description', f'{_name(control)}.description')
        controller.add_link('Entry.side', f'{_name(control)}.side')
        controller.add_link('Entry.restrain_numbering', f'{_name(control)}.restrain_numbering')
        controller.add_link('Entry.sub_count', f'{_name(control)}.sub_count')
        controller.add_link('Entry.joint_token', f'{_name(control)}.joint_token')
        controller.add_link('Entry.shape_translate', f'{_name(control)}.translate')
        controller.add_link('Entry.shape_rotate', f'{_name(control)}.rotate')
        controller.add_link('Entry.shape_scale', f'{_name(control)}.scale')
        
        controller.add_link(f'{_name(for_each)}.Index', f'{_name(control)}.increment')
        controller.add_link(f'{_name(for_each)}.Element', f'{_name(control)}.driven')
        
        controller.add_link(f'{_name(for_each)}.ExecuteContext', f'{_name(control)}.ExecuteContext')
        
        meta_data = controller.add_template_node('DISPATCH_RigDispatch_SetMetadata(in Item,in Name,in Value,out Success)', unreal.Vector2D(3000, -1450), 'DISPATCH_RigDispatch_SetMetadata')
        controller.add_link(f'{_name(control)}.ExecuteContext', f'{_name(meta_data)}.ExecuteContext')
        controller.add_link(f'{_name(for_each)}.Element', f'{_name(meta_data)}.Item')
        controller.set_pin_default_value('DISPATCH_RigDispatch_SetMetadata.Name', 'Control', False)
        controller.add_link(f'{_name(control)}.Last Control', f'{_name(meta_data)}.Value')
        
        index_equals = controller.add_template_node('DISPATCH_RigVMDispatch_CoreEquals(in A,in B,out Result)', unreal.Vector2D(1800, -1450), 'DISPATCH_RigVMDispatch_CoreEquals')
        controller.add_link(f'{_name(for_each)}.Index', f'{_name(index_equals)}.A')
        controller.add_link(f'{_name(index_equals)}.Result', f'{_name(parent)}.is_top_joint')
        controller.add_link(f'{_name(for_each)}.Element', f'{_name(parent)}.joint')
        controller.add_link('Entry.parent', f'{_name(parent)}.default_parent')
        controller.add_link('Entry.hierarchy', f'{_name(parent)}.in_hierarchy')
        controller.add_link(f'{_name(parent)}.Result', f'{_name(control)}.parent')
        
        description = controller.add_variable_node('description', 'FString', None, True, '', unreal.Vector2D(1500, -600), 'VariableNode_description')
        use_joint_name = controller.add_variable_node('use_joint_name', 'FString', None, True, '', unreal.Vector2D(1500, -600), 'VariableNode_use_joint_name')
        joint_token = controller.add_variable_node('joint_token', 'FString', None, True, '', unreal.Vector2D(1500, -1000), 'VariableNode_joint_token')
        description_if = self.function_controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(2250, -700), 'DISPATCH_RigVMDispatch_If')
        
        controller.add_link(f'{_name(for_each)}.ExecuteContext', f'{_name(joint_description)}.ExecuteContext')
        controller.add_link(f'{_name(for_each)}.Element', f'{_name(joint_description)}.joint')
        controller.add_link(f'{_name(joint_token)}.Value', f'{_name(joint_description)}.joint_token')
        controller.add_link(f'{_name(description)}.Value', f'{_name(joint_description)}.description')
        controller.add_link(f'{_name(joint_description)}.ExecuteContext', f'{_name(control)}.ExecuteContext')
        
        controller.add_link(f'{_name(use_joint_name)}.Value', f'{_name(description_if)}.Condition')
        controller.add_link(f'{_name(joint_description)}.Result', f'{_name(description_if)}.True')
        controller.add_link(f'{_name(description)}.Value', f'{_name(description_if)}.False')
        controller.add_link(f'{_name(description_if)}.Result', f'{_name(control)}.description')
        
        self.function_controller.add_local_variable_from_object_path('local_controls', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', '')
        
        add_control = self.function_controller.add_template_node('DISPATCH_RigVMDispatch_ArrayAdd(io Array,in Element,out Index)', unreal.Vector2D(2800, -900), 'DISPATCH_RigVMDispatch_ArrayAdd')
        self.function_controller.add_link(f'{_name(control)}.Last Control', f'{_name(add_control)}.Element')
        self.function_controller.add_link(f'{_name(meta_data)}.ExecuteContext', f'{_name(add_control)}.ExecuteContext')
        
        variable_node = self.function_controller.add_variable_node_from_object_path('local_controls', 'FRigElementKey', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(2700, -700), 'VariableNode')
        self.function_controller.add_link(f'{_name(variable_node)}.Value', f'{_name(add_control)}.Array')
        
        self.function_controller.set_node_position_by_name('Return', unreal.Vector2D(2350, 0))
        self.function_controller.add_link(f'{_name(variable_node)}.Value', 'Return.controls')
        
        

    def _build_function_forward_graph(self):
        
        for_each = self.function_controller.add_template_node('DISPATCH_RigVMDispatch_ArrayIterator(in Array,out Element,out Index,out Count,out Ratio)', unreal.Vector2D(850, 250), 'DISPATCH_RigVMDispatch_ArrayIterator')
        self.function_controller.add_link(f'{_name(self.switch)}.Cases.1', f'{_name(for_each)}.ExecuteContext')
        self.function_controller.add_link('Entry.joints', '%s.Array' % (for_each.get_node_path()))
        
        meta_data = self.function_controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in Default,out Value,out Found)', unreal.Vector2D(1250, 350), 'DISPATCH_RigDispatch_GetMetadata')
        self.function_controller.set_pin_default_value('%s.Name' % meta_data.get_node_path(), 'Control', False)
        self.function_controller.add_link('%s.Element' % for_each.get_node_path(), '%s.Item' % meta_data.get_node_path())
        
        get_transform = self.function_controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetTransform', 'Execute', unreal.Vector2D(1550, 350), 'GetTransform')
        self.function_controller.add_link('%s.Value' % meta_data.get_node_path(), '%s.Item' % get_transform.get_node_path())
        set_transform = self.function_controller.add_template_node('Set Transform::Execute(in Item,in Space,in bInitial,in Value,in Weight,in bPropagateToChildren)', unreal.Vector2D(2000, 250), 'Set Transform')
        
        self.function_controller.add_link('%s.Transform' % get_transform.get_node_path(), '%s.Value' % set_transform.get_node_path())
        self.function_controller.add_link('%s.Element' % for_each.get_node_path(), '%s.Item' % set_transform.get_node_path())
        
        self.function_controller.add_link('%s.ExecuteContext' % for_each.get_node_path(), '%s.ExecuteContext' % set_transform.get_node_path())
        
    def _build_function_backward_graph(self):
        controller = self.function_controller
        for_each = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayIterator(in Array,out Element,out Index,out Count,out Ratio)', unreal.Vector2D(850, 1250), 'DISPATCH_RigVMDispatch_ArrayIterator')
        controller.add_link(f'{_name(self.switch)}.Cases.2', f'{_name(for_each)}.ExecuteContext')
        controller.add_link('Entry.joints', f'{_name(for_each)}.Array')
        
        set_transform = self.function_controller.add_template_node('Set Transform::Execute(in Item,in Space,in bInitial,in Value,in Weight,in bPropagateToChildren)', unreal.Vector2D(2000, 1250), 'Set Transform')
        
        meta_data = self.function_controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in Default,out Value,out Found)', unreal.Vector2D(1250, 1350), 'DISPATCH_RigDispatch_GetMetadata')
        self.function_controller.set_pin_default_value('%s.Name' % meta_data.get_node_path(), 'Control', False)
        #self.function_controller.add_link('%s.Element' % for_each.get_node_path(), '%s.Item' % meta_data.get_node_path())
        
        self.function_controller.add_link(f'{_name(meta_data)}.Value', f'{_name(set_transform)}.Item')
        
        get_transform = self.function_controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetTransform', 'Execute', unreal.Vector2D(1550, 1350), 'GetTransform')
        self.function_controller.add_link(f'{_name(for_each)}.Element', f'{_name(get_transform)}.Item')
        
        
        self.function_controller.add_link('%s.Transform' % get_transform.get_node_path(), '%s.Value' % set_transform.get_node_path())
        
        self.function_controller.add_link('%s.ExecuteContext' % for_each.get_node_path(), '%s.ExecuteContext' % set_transform.get_node_path())

class UnrealIkRig(UnrealUtilRig):
    
    def _build_function_construct_graph(self):
        return
    
    def _build_function_forward_graph(self):
        return
    
    def _build_function_backward_graph(self):
        return