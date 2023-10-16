from . import rigs_base

from vtool import util
from vtool import util_file

in_unreal = util.in_unreal

if in_unreal:
    from .. import unreal_lib
    import unreal
#--- Unreal
class UnrealUtilRig(rigs_base.PlatformUtilRig):
    
    def __init__(self):
        super(UnrealUtilRig, self).__init__()
        
        self.construct_controller = None
        self.construct_node = None
        
        self.forward_controller = None
        self.forward_node = None
        
        self.backward_controller = None
        self.backward_function_node = None
        
        self.graph = None
        self.library = None
        self.controller = None
        self.forward_controller = None
        self.construct_controller = None
        self.backward_controller = None

        self.construct_node = None
        self.forward_node = None
        self.backward_function_node = None
        
        self._attribute_cache = None
        self.library_functions = {}
        self._cached_library_function_names = ['vetala_Control', 
                                               'vetala_GetJointDescription', 
                                               'vetala_ConstructName']
    
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
    
    def _add_transform_array_out(self, name):
        transform_pin = self.function_controller.add_exposed_pin(name, unreal.RigVMPinDirection.OUTPUT, 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', '')
        #self.function_controller.insert_array_pin('%s.%s' % (self.function.get_name(),transform_pin), -1, '')
        
    def _initialize_inputs(self):
        
        inputs = self.rig.attr.inputs
        for name in inputs:
            value, attr_type = self.rig.attr._in_attributes_dict[name]
            
            if attr_type == AttrType.INT:
                self._add_int_in(name, value)
            
            if attr_type == AttrType.BOOL:
                self._add_bool_in(name, value)
            
            if attr_type == AttrType.COLOR:
                self._add_color_array_in(name, value)
                
            if attr_type == AttrType.STRING:
                if value is None:
                    value = ''
                self.function_controller.add_exposed_pin(name, unreal.RigVMPinDirection.INPUT, 'FString', 'None', value)
                
            if attr_type == AttrType.TRANSFORM:
                self._add_transform_array_in(name)
        
    def _initialize_node_attributes(self):
        
        self.function_controller.add_exposed_pin('uuid', unreal.RigVMPinDirection.INPUT, 'FString', 'None', '')
        self.function_controller.add_exposed_pin('mode', unreal.RigVMPinDirection.INPUT, 'int32', 'None', '')
        
        node_attrs = self.rig.attr.node
        for name in node_attrs:
            value, attr_type = self.rig.attr._node_attributes_dict[name]
            
            if attr_type == AttrType.INT:
                self._add_int_in(name, value)
            
            if attr_type == AttrType.BOOL:
                self._add_bool_in(name, value)
            
            if attr_type == AttrType.COLOR:
                self._add_color_array_in(name, value)
                
            if attr_type == AttrType.STRING:
                if value is None:
                    value = ''
                self.function_controller.add_exposed_pin(name, unreal.RigVMPinDirection.INPUT, 'FString', 'None', value)
                
            if attr_type == AttrType.TRANSFORM:
                self._add_transform_array_in(name)
                
    def _initialize_outputs(self):
        #function_library = self.graph.get_controller_by_name('RigVMFunctionLibrary')
        
        outputs = self.rig.attr.outputs
        for name in outputs:
            
            value, attr_type = self.rig.attr._out_attributes_dict[name]
            
            if attr_type == AttrType.COLOR:
                self._add_color_array_out(name, value)
                
            if attr_type == AttrType.STRING:
                if value is None:
                    value = ''
                self.function_controller.add_exposed_pin(name, unreal.RigVMPinDirection.OUTPUT, 'FString', 'None', value)
                
            if attr_type == AttrType.TRANSFORM:
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
        function_node = self.forward_controller.add_function_reference_node(self.function, unreal.Vector2D(100, 100), self.function.get_node_path())
        self.forward_node = function_node
        
        self.forward_controller.set_pin_default_value('%s.mode' % function_node.get_node_path(), '1', False)
        
        last_forward = unreal_lib.util.get_last_execute_node(self.forward_controller.get_graph())
        if not last_forward:
            self.forward_controller.add_link('BeginExecution.ExecuteContext', '%s.ExecuteContext' % (function_node.get_node_path()))
        else:
            self.forward_controller.add_link('%s.ExecuteContext' % _name(last_forward), '%s.ExecuteContext' % (function_node.get_node_path()))
        self.forward_controller.set_pin_default_value('%s.uuid' % _name(function_node), self.rig.uuid, False)

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
        
        if value_type == AttrType.INT:
            value = str(value)
            self.construct_controller.set_pin_default_value('%s.%s' % (_name(self.construct_node), name), value, False)
            self.forward_controller.set_pin_default_value('%s.%s' % (_name(self.construct_node), name), value, False)
        
        if value_type == AttrType.BOOL:
            value = str(value)
            value = value.lower()
            self.construct_controller.set_pin_default_value('%s.%s' % (_name(self.construct_node), name), value, False)
            self.forward_controller.set_pin_default_value('%s.%s' % (_name(self.construct_node), name), value, False)
        
        if value_type == AttrType.STRING:
            if value is None:
                value = ''
            self.construct_controller.set_pin_default_value('%s.%s' % (_name(self.construct_node), name), value, False)
            self.forward_controller.set_pin_default_value('%s.%s' % (_name(self.forward_node), name), value, False)
        
        if value_type == AttrType.COLOR:
            self._reset_array(name)
            color = value[0]
            
            self.construct_controller.insert_array_pin('%s.%s' % (_name(self.construct_node), name), -1, '')
            self.construct_controller.set_pin_default_value('%s.%s.0.R' % (_name(self.construct_node), name), str(color[0]), True)
            self.construct_controller.set_pin_default_value('%s.%s.0.G' % (self.construct_node.get_node_path(),name), str(color[1]), True)
            self.construct_controller.set_pin_default_value('%s.%s.0.B' % (self.construct_node.get_node_path(),name), str(color[2]), True)
            
        if value_type == AttrType.TRANSFORM:
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
    def curve_shape(self):
        return self.rig.attr.get('curve_shape')
    
    @curve_shape.setter
    def curve_shape(self, str_curve_shape):
        
        if not str_curve_shape:
            str_curve_shape = 'Default'
        
        self.rig.attr.set('curve_shape', str_curve_shape)
        
        self._function_set_attr('curve_shape')

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
        if not self.backward_function_node:
            self.backward_function_node = self._get_function_node(self.backward_controller)
        
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
            self.construct_controller.remove_node_by_name(self.construct_node.get_node_path())
        
        if self.forward_node:
            self.forward_controller.remove_node_by_name(self.forward_node.get_node_path())
            
        if self.backward_function_node:
            self.backward_controller.remove_node_by_name(self.backward_function_node.get_node_path())

class UnrealFkRig(UnrealUtilRig):
    

    
    def _build_function_graph(self):
        super(UnrealFkRig, self)._build_function_graph()
        if not self.graph:
            return
        
        switch = self.function_controller.add_template_node('DISPATCH_RigVMDispatch_SwitchInt32(in Index)', unreal.Vector2D(225, -160), 'DISPATCH_RigVMDispatch_SwitchInt32')
        self.function_controller.add_link('Entry.ExecuteContext', '%s.ExecuteContext' % switch.get_node_path())
        self.function_controller.add_link('Entry.mode', '%s.Index' % switch.get_node_path())
        self.function_controller.add_link('%s.Completed' % (switch.get_node_path()), 'Return.ExecuteContext')
        
        self.function_controller.add_link('%s.ExecuteContext' % _name(switch), 'Return.ExecuteContext')
        
        self.switch = switch
        
        
        self._build_function_construct_graph()
        self._build_function_forward_graph()
        self._build_function_backward_graph()
        
    def _build_function_construct_graph(self):
        controller = self.function_controller
        
        for_each = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayIterator(in Array,out Element,out Index,out Count,out Ratio)', unreal.Vector2D(300, 150), 'DISPATCH_RigVMDispatch_ArrayIterator')
        
        controller.add_link('%s.Cases.0' % self.switch.get_node_path(), '%s.ExecuteContext' % (for_each.get_node_path()))
                
        controller.add_link('Entry.joints', '%s.Array' % (for_each.get_node_path()))
        
        control_node = self.library_functions['vetala_Control']
        
        control = self.function_controller.add_function_reference_node(control_node, unreal.Vector2D(1070, 160), _name(control_node))
        
        controller.add_link('Entry.color', f'{_name(control)}.color')
        controller.add_link('Entry.sub_color', f'{_name(control)}.sub_color')
        controller.add_link('Entry.curve_shape', f'{_name(control)}.curve_shape')
        controller.add_link('Entry.description', f'{_name(control)}.description')
        controller.add_link('Entry.side', f'{_name(control)}.side')
        controller.add_link('Entry.restrain_numbering', f'{_name(control)}.restrain_numbering')
        controller.add_link('Entry.sub_count', f'{_name(control)}.sub_count')
        controller.add_link('Entry.joint_token', f'{_name(control)}.joint_token')
        
        controller.add_link(f'{_name(for_each)}.Index', f'{_name(control)}.increment')
        controller.add_link(f'{_name(for_each)}.Element', f'{_name(control)}.driven')
        
        controller.add_link(f'{_name(for_each)}.ExecuteContext', f'{_name(control)}.ExecuteContext')
        
        meta_data = self.function_controller.add_template_node('DISPATCH_RigDispatch_SetMetadata(in Item,in Name,in Value,out Success)', unreal.Vector2D(1500, 300), 'DISPATCH_RigDispatch_SetMetadata')
        self.function_controller.add_link(f'{_name(control)}.ExecuteContext', f'{_name(meta_data)}.ExecuteContext')
        self.function_controller.add_link('%s.Element' % for_each.get_node_path(), '%s.Item' % meta_data.get_node_path())
        self.function_controller.set_pin_default_value('DISPATCH_RigDispatch_SetMetadata.Name', 'Control', False)
        self.function_controller.add_link(f'{_name(control)}.Item', f'{_name(meta_data)}.Value')
        
        parent = self.function_controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyGetParent', 'Execute', unreal.Vector2D(1000, 700), 'HierarchyGetParent')
        self.function_controller.add_link('%s.Element' % for_each.get_node_path(), '%s.Child' % parent.get_node_path())
        parent_data = self.function_controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in Default,out Value,out Found)', unreal.Vector2D(1250, 750), 'DISPATCH_RigDispatch_GetMetadata_1')
        self.function_controller.add_link('%s.Parent' % parent.get_node_path(), '%s.Item' % parent_data.get_node_path())
        self.function_controller.set_pin_default_value('%s.Name' % parent_data.get_node_path(), 'Control', False)
        
        
        parent_equals = self.function_controller.add_template_node('DISPATCH_RigVMDispatch_CoreEquals(in A,in B,out Result)', unreal.Vector2D(700, 50), 'DISPATCH_RigVMDispatch_CoreEquals')
        parent_if = self.function_controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(900, 50), 'DISPATCH_RigVMDispatch_If')
        
        self.function_controller.add_link(f'{_name(parent_if)}.Result', f'{_name(control)}.parent')
        
        self.function_controller.add_link('%s.Index' % for_each.get_node_path(), '%s.A' % parent_equals.get_node_path())
        self.function_controller.add_link('%s.Result' % parent_equals.get_node_path(), '%s.Condition' % parent_if.get_node_path())
        
        get_parent_index = self.function_controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(530, 64), 'DISPATCH_RigVMDispatch_ArrayGetAtIndex_1')
        
        num = self.function_controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetNum(in Array,out Num)', unreal.Vector2D(-700, -70), 'DISPATCH_RigVMDispatch_ArrayGetNum')
        greater = self.function_controller.add_template_node('Greater::Execute(in A,in B,out Result)', unreal.Vector2D(-450, -30), 'Greater')
        if_parent = self.function_controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(-635.098583, 67.131332), 'DISPATCH_RigVMDispatch_If_2')
        
        self.function_controller.add_link('Entry.parent', '%s.True' % _name(if_parent))
        
        self.function_controller.insert_array_pin('%s.False' % _name(if_parent), -1, '')
        self.function_controller.set_pin_default_value('%s.False.0.Type' % _name(if_parent), 'Bone', False)
        
        self.function_controller.add_link('Entry.parent', '%s.Array' % _name(num))
        self.function_controller.add_link('%s.Num' % _name(num), '%s.A' % _name(greater))
        self.function_controller.add_link('%s.Result' % _name(greater), '%s.Condition' % _name(if_parent))
        self.function_controller.add_link('%s.Result' % _name(if_parent), '%s.Array' % _name(get_parent_index))
        
        self.function_controller.set_pin_default_value('%s.Index' % get_parent_index.get_node_path(), '-1', False)
        self.function_controller.add_link('%s.Element' % get_parent_index.get_node_path(), '%s.True' % parent_if.get_node_path())
        
        self.function_controller.add_link('%s.Value' % parent_data.get_node_path(), '%s.False' % parent_if.get_node_path())
        self.function_controller.add_link(f'{_name(parent_if)}.Result', f'{_name(control)}.parent')
        
        self.function_controller.add_local_variable_from_object_path('local_controls', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', '')
        
        add_control = self.function_controller.add_template_node('DISPATCH_RigVMDispatch_ArrayAdd(io Array,in Element,out Index)', unreal.Vector2D(1980, 500), 'DISPATCH_RigVMDispatch_ArrayAdd')
        self.function_controller.add_link(f'{_name(control)}.Item', f'{_name(add_control)}.Element')
        self.function_controller.add_link('%s.ExecuteContext' % _name(meta_data), '%s.ExecuteContext' % _name(add_control))
        
        variable_node = self.function_controller.add_variable_node_from_object_path('local_controls', 'FRigElementKey', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(1680, 450), 'VariableNode')
        self.function_controller.add_link('%s.Value' % _name(variable_node), '%s.Array' % _name(add_control))
        
        self.function_controller.set_node_position_by_name('Return', unreal.Vector2D(2350, 0))
        self.function_controller.add_link('%s.Value' % _name(variable_node), 'Return.controls')
        
        

    def _build_function_forward_graph(self):
        
        for_each = self.function_controller.add_template_node('DISPATCH_RigVMDispatch_ArrayIterator(in Array,out Element,out Index,out Count,out Ratio)', unreal.Vector2D(700, -300), 'DISPATCH_RigVMDispatch_ArrayIterator')
        self.function_controller.add_link('%s.Cases.1' % self.switch.get_node_path(), '%s.ExecuteContext' % (for_each.get_node_path()))
        self.function_controller.add_link('Entry.joints', '%s.Array' % (for_each.get_node_path()))
        
        meta_data = self.function_controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in Default,out Value,out Found)', unreal.Vector2D(975.532734, -167.022334), 'DISPATCH_RigDispatch_GetMetadata')
        self.function_controller.set_pin_default_value('%s.Name' % meta_data.get_node_path(), 'Control', False)
        self.function_controller.add_link('%s.Element' % for_each.get_node_path(), '%s.Item' % meta_data.get_node_path())
        
        get_transform = self.function_controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetTransform', 'Execute', unreal.Vector2D(1311.532734, -95.022334), 'GetTransform')
        self.function_controller.add_link('%s.Value' % meta_data.get_node_path(), '%s.Item' % get_transform.get_node_path())
        set_transform = self.function_controller.add_template_node('Set Transform::Execute(in Item,in Space,in bInitial,in Value,in Weight,in bPropagateToChildren)', unreal.Vector2D(1765.247019, -174.772082), 'Set Transform')
        
        self.function_controller.add_link('%s.Transform' % get_transform.get_node_path(), '%s.Value' % set_transform.get_node_path())
        self.function_controller.add_link('%s.Element' % for_each.get_node_path(), '%s.Item' % set_transform.get_node_path())
        
        self.function_controller.add_link('%s.ExecuteContext' % for_each.get_node_path(), '%s.ExecuteContext' % set_transform.get_node_path())
