# Copyright (C) 2024 Louis Vottero louis.vot@gmail.com    All rights reserved.

import copy

from . import rigs

from vtool import util
from vtool import util_file

in_unreal = util.in_unreal

if in_unreal:
    import unreal
    from .. import unreal_lib
    from ..unreal_lib import graph


def n(unreal_node):
    """
    returns the node path
    """
    if not in_unreal:
        return
    return unreal_node.get_node_path()


class UnrealUtilRig(rigs.PlatformUtilRig):

    def __init__(self):
        super(UnrealUtilRig, self).__init__()

        self.function = None
        self._function_name = self._get_function_name()

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
                                               'vetalaLib_GetParent',
                                               'vetalaLib_GetItem',
                                               'vetalaLib_ConstructName',
                                               'vetalaLib_WheelRotate',
                                               ]

    def _init_graph(self):
        if not self.graph:
            return

        unreal_lib.graph.add_forward_solve()

        self.function_node = None

        if self.construct_controller is None:
            self.construct_controller = None

        if self.construct_controller:
            if not self.construct_controller.get_graph():
                self.construct_controller = None

        if not self.construct_controller:

            model = unreal_lib.graph.add_construct_graph()
            self.construct_controller = self.graph.get_controller_by_name(model.get_graph_name())
            self.construct_node = None
            self._attribute_cache = None

        if self.backward_controller is None:
            self.backward_controller = None
        if self.backward_controller:
            if not self.backward_controller.get_graph():
                self.backward_controller = None

        if not self.backward_controller:
            model = unreal_lib.graph.add_backward_graph()
            self.backward_controller = self.graph.get_controller_by_name(model.get_graph_name())
            self.backward_node = None

        self.function_library = self.graph.get_controller_by_name('RigVMFunctionLibrary')

    def _get_function_name(self):
        rig_name = 'vetala_%s' % self.__class__.__name__
        rig_name = rig_name.replace('Unreal', '')
        return rig_name

    def _get_existing_rig_function(self):
        found = self.controller.get_graph().find_function(self._function_name)
        if found:
            self.function = found
            self.function_controller = self.graph.get_controller_by_name(n(self.function))

    def _init_rig_function(self):
        if not self.graph:
            return

        self._get_existing_rig_function()
        if self.function:
            return

        self.function = self.controller.add_function_to_library(self._function_name, True, unreal.Vector2D(0, 0))
        self.function_controller = self.graph.get_controller_by_name(n(self.function))

        self.function_controller.add_exposed_pin('uuid', unreal.RigVMPinDirection.INPUT, 'FString', 'None', '')
        self.function_controller.add_exposed_pin('mode', unreal.RigVMPinDirection.INPUT, 'int32', 'None', '')

        attribute_names = self.rig.get_all_attributes()
        for attr_name in attribute_names:

            ins = self.rig.get_ins()
            outs = self.rig.get_outs()
            items = self.rig.get_node_attributes()

            if attr_name in items:
                self._initialize_node_attribute(attr_name)
            if attr_name in ins:
                self._initialize_input(attr_name)
            if attr_name in outs:
                self._initialize_output(attr_name)

        self._build_function_graph()

    def _init_library(self):
        if not self.graph:
            return

        controller = self.function_library

        library_path = unreal_lib.core.get_custom_library_path()

        missing = False

        for name in self._cached_library_function_names:

            function = controller.get_graph().find_function(name)
            if function:
                self.library_functions[name] = function
            else:
                missing = True

        if not missing:
            return

        util.show('Init Library')
        self.library_functions = {}
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
            if function not in functions_before:
                name = function.get_node_path()

                if name not in new_function_names:
                    controller.remove_function_from_library(name)

        control_node = self.library_functions['vetalaLib_Control']

        controller = self.graph.get_controller_by_name(n(control_node))

        nodes = controller.get_graph().get_nodes()

        nodes_to_check = ['vetalaLib_ConstructName',
                          'vetalaLib_ControlSub',
                          'vetalaLib_Control']
        for check in nodes_to_check:
            found = False
            for node in nodes:
                if node.get_node_title() == check:
                    found = True

            if not found:
                function = self.library_functions[check]

                if check == 'vetalaLib_ConstructName':
                    node = controller.add_function_reference_node(function, unreal.Vector2D(300, 800), n(function))
                    controller.add_link('VariableNode.Value', f'{n(node)}.Description')
                    controller.add_link('VariableNode_3.Value', f'{n(node)}.Side')
                    controller.add_link('VariableNode_1.Value', f'{n(node)}.RestrainNumbering')
                    controller.add_link('VariableNode_2.Value', f'{n(node)}.Number')
                    controller.add_link(f'{n(node)}.Result', 'SpawnControl.Name')

                if check == 'vetalaLib_Control':
                    controller.add_link('DISPATCH_RigVMDispatch_ArrayGetAtIndex_1.Element', 'vetalaLib_ControlSub.color')
                    controller.add_link('vetalaLib_ControlSub.ExecuteContext', 'DISPATCH_RigDispatch_SetMetadata.ExecuteContext')
                    controller.add_link('DISPATCH_RigDispatch_SetMetadata.ExecuteContext', 'Return.ExecuteContext')
                    controller.add_link('vetalaLib_ControlSub.SubControls', 'DISPATCH_RigDispatch_SetMetadata.Value')

                if check == 'vetalaLib_ControlSub':
                    node = controller.add_function_reference_node(function, unreal.Vector2D(2100, 100), n(function))
                    controller.add_link('SpawnControl.Item', f'{n(node)}.control')
                    controller.add_link('SpawnControl.ExecuteContext', f'{n(node)}.ExecuteContext')
                    controller.add_link('VariableNode_4.Value', f'{n(node)}.sub_count')

                    controller.add_link(f'{n(node)}.ExecuteContext', 'Return.ExecuteContext')
                    controller.add_link(f'{n(node)}.LastSubControl', 'Return.Last Control')

    def _add_bool_in(self, name, value):
        value = str(value)
        value = value.lower()

        self.function_controller.add_exposed_pin(name, unreal.RigVMPinDirection.INPUT, 'bool', 'None', value)

    def _add_int_in(self, name, value):
        value = str(value)

        self.function_controller.add_exposed_pin(name, unreal.RigVMPinDirection.INPUT, 'int32', 'None', value)

    def _add_number_in(self, name, value):
        value = str(value)

        self.function_controller.add_exposed_pin(name, unreal.RigVMPinDirection.INPUT, 'float', 'None', value)

    def _add_color_array_in(self, name, value):

        color = value[0]

        if not isinstance(color, list):
            color = value

        color_pin = self.function_controller.add_exposed_pin(name, unreal.RigVMPinDirection.INPUT,
                                                             'TArray<FLinearColor>', '/Script/CoreUObject.LinearColor',
                                                             '')

        f_name = self.function.get_name()
        self.function_library.insert_array_pin(f'{f_name}.{color_pin}', -1, '')
        self.function_library.set_pin_default_value(f'{f_name}.{color_pin}.0.R', str(color[0]), False)
        self.function_library.set_pin_default_value(f'{f_name}.{color_pin}.0.G', str(color[1]), False)
        self.function_library.set_pin_default_value(f'{f_name}.{color_pin}.0.B', str(color[2]), False)

    def _add_color_array_out(self, name, value):

        color = value[0]

        color_pin = self.function_controller.add_exposed_pin(name, unreal.RigVMPinDirection.OUTPUT,
                                                             'TArray<FLinearColor>', '/Script/CoreUObject.LinearColor',
                                                             '')

        f_name = self.function.get_name()
        self.function_library.insert_array_pin(f'{f_name}.{color_pin}', -1, '')
        self.function_library.set_pin_default_value(f'{f_name}.{color_pin}.0.R', str(color[0]), False)
        self.function_library.set_pin_default_value(f'{f_name}.{color_pin}.0.G', str(color[1]), False)
        self.function_library.set_pin_default_value(f'{f_name}.{color_pin}.0.B', str(color[2]), False)

    def _add_transform_array_in(self, name):
        transform_pin = self.function_controller.add_exposed_pin(name, unreal.RigVMPinDirection.INPUT,
                                                                 'TArray<FRigElementKey>',
                                                                 '/Script/ControlRig.RigElementKey', '')

        # self.function_controller.insert_array_pin('%s.%s' % (self.function.get_name(),transform_pin), -1, '')

    def _add_vector_array_in(self, name):
        pin = self.function_controller.add_exposed_pin(name, unreal.RigVMPinDirection.INPUT, 'TArray<FVector>',
                                                       '/Script/CoreUObject.Vector', '()')

    def _add_transform_array_out(self, name):
        transform_pin = self.function_controller.add_exposed_pin(name, unreal.RigVMPinDirection.OUTPUT,
                                                                 'TArray<FRigElementKey>',
                                                                 '/Script/ControlRig.RigElementKey', '')
        # self.function_controller.insert_array_pin('%s.%s' % (self.function.get_name(),transform_pin), -1, '')

    def _initialize_input(self, name):

        value, attr_type = self.rig.attr._in_attributes_dict[name]

        if attr_type == rigs.AttrType.INT:
            self._add_int_in(name, value)

        if attr_type == rigs.AttrType.BOOL:
            self._add_bool_in(name, value)

        if attr_type == rigs.AttrType.NUMBER:
            self._add_number_in(name, value)

        if attr_type == rigs.AttrType.COLOR:
            self._add_color_array_in(name, value)

        if attr_type == rigs.AttrType.STRING:
            if not value:
                value = ['']
            value = value[0]
            self.function_controller.add_exposed_pin(name, unreal.RigVMPinDirection.INPUT, 'FString', 'None', value)

        if attr_type == rigs.AttrType.TRANSFORM:
            self._add_transform_array_in(name)

        if attr_type == rigs.AttrType.VECTOR:
            self._add_vector_array_in(name)

    def _initialize_node_attribute(self, name):

        value, attr_type = self.rig.attr._node_attributes_dict[name]

        if attr_type == rigs.AttrType.INT:
            self._add_int_in(name, value)

        if attr_type == rigs.AttrType.BOOL:
            self._add_bool_in(name, value)

        if attr_type == rigs.AttrType.NUMBER:
            self._add_number_in(name, value)

        if attr_type == rigs.AttrType.COLOR:
            self._add_color_array_in(name, value)

        if attr_type == rigs.AttrType.STRING:
            if value is None:
                value = ['']
            self.function_controller.add_exposed_pin(name, unreal.RigVMPinDirection.INPUT, 'FString', 'None', value[0])

        if attr_type == rigs.AttrType.TRANSFORM:
            self._add_transform_array_in(name)

        if attr_type == rigs.AttrType.VECTOR:
            self._add_vector_array_in(name)

    def _initialize_output(self, name):

        value, attr_type = self.rig.attr._out_attributes_dict[name]

        if attr_type == rigs.AttrType.COLOR:
            self._add_color_array_out(name, value)

        if attr_type == rigs.AttrType.STRING:
            if value is None:
                value = ''
            self.function_controller.add_exposed_pin(name, unreal.RigVMPinDirection.OUTPUT, 'FString', 'None',
                                                     value)

        if attr_type == rigs.AttrType.TRANSFORM:
            self._add_transform_array_out(name)

    def _get_function_node(self, function_controller):

        if not function_controller:
            return

        nodes = function_controller.get_graph().get_nodes()

        if not nodes:
            return

        for node in nodes:

            pin = function_controller.get_graph().find_pin('%s.uuid' % n(node))
            if pin:
                node_uuid = pin.get_default_value()
                if node_uuid == self.rig.uuid:
                    return node

    def _add_construct_node_to_graph(self):
        function_node = self.construct_controller.add_function_reference_node(self.function, unreal.Vector2D(100, 100),
                                                                              n(self.function))
        self.construct_node = function_node

        last_construct = unreal_lib.graph.get_last_execute_node(self.construct_controller.get_graph())
        if last_construct:
            self.construct_controller.add_link('%s.ExecuteContext' % last_construct.get_node_path(),
                                               '%s.ExecuteContext' % (function_node.get_node_path()))
        else:
            self.construct_controller.add_link('PrepareForExecution.ExecuteContext',
                                               '%s.ExecuteContext' % (function_node.get_node_path()))
        self.construct_controller.set_pin_default_value('%s.uuid' % function_node.get_node_path(), self.rig.uuid, False)

    def _add_forward_node_to_graph(self):

        controller = self.forward_controller

        function_node = controller.add_function_reference_node(self.function, unreal.Vector2D(100, 100),
                                                               self.function.get_node_path())
        self.forward_node = function_node

        controller.set_pin_default_value(f'{n(function_node)}.mode', '1', False)

        last_forward = unreal_lib.graph.get_last_execute_node(controller.get_graph())
        if last_forward:
            self.forward_controller.add_link(f'{n(last_forward)}.ExecuteContext',
                                             f'{n(function_node)}.ExecuteContext')
        else:
            if controller.get_graph().find_node('RigUnit_BeginExecution'):
                controller.add_link('RigUnit_BeginExecution.ExecuteContext', f'{n(function_node)}.ExecuteContext')
            else:
                controller.add_link('BeginExecution.ExecuteContext', f'{n(function_node)}.ExecuteContext')
        self.forward_controller.set_pin_default_value(f'{n(function_node)}.uuid', self.rig.uuid, False)

    def _add_backward_node_to_graph(self):

        controller = self.backward_controller

        function_node = controller.add_function_reference_node(self.function, unreal.Vector2D(100, 100),
                                                               self.function.get_node_path())
        self.backward_node = function_node

        controller.set_pin_default_value(f'{n(function_node)}.mode', '2', False)

        last_backward = unreal_lib.graph.get_last_execute_node(controller.get_graph())
        if last_backward:
            controller.add_link(f'{n(last_backward)}.ExecuteContext', f'{n(function_node)}.ExecuteContext')
        else:
            controller.add_link('InverseExecution.ExecuteContext', f'{n(function_node)}.ExecuteContext')

        controller.set_pin_default_value(f'{n(function_node)}.uuid', self.rig.uuid, False)

    def _reset_array(self, name, value):

        graph = self.construct_controller.get_graph()
        pin = graph.find_pin('%s.%s' % (n(self.construct_node), name))

        array_size = pin.get_array_size()

        if array_size == 0:
                return

        if value:
            if array_size == len(value):
                return

        self.construct_controller.clear_array_pin('%s.%s' % (n(self.construct_node), name))
        self.forward_controller.clear_array_pin('%s.%s' % (n(self.forward_node), name))
        self.backward_controller.clear_array_pin('%s.%s' % (n(self.backward_node), name))

        self.construct_controller.set_pin_default_value('%s.%s' % (self.construct_node.get_node_path(), name),
                                                        '()',
                                                        True)
        self.forward_controller.set_pin_default_value('%s.%s' % (self.forward_node.get_node_path(), name), '()', True)
        self.backward_controller.set_pin_default_value('%s.%s' % (self.backward_node.get_node_path(), name), '()', True)

    def _add_array_entry(self, name, value):
        pass

    def _set_attr_on_function(self, name, custom_value=None):

        if not self.construct_controller:
            return
        if not self.forward_controller:
            return

        if not self.construct_node:
            self.build()
            return

        value, value_type = self.rig.attr.get(name, True)

        if custom_value:
            value = custom_value

        if self._attribute_cache:
            if value == self._attribute_cache.get(name):
                return
            else:
                self._attribute_cache.set(name, value)

        util.show('\t\tSet Unreal Function %s Pin %s %s: %s' % (self.__class__.__name__, name, value_type, value))

        if value_type == rigs.AttrType.INT:
            value = str(value[0])
            self.construct_controller.set_pin_default_value('%s.%s' % (n(self.construct_node), name), value, False)

        if value_type == rigs.AttrType.BOOL:
            value = str(value)
            if value == '1':
                value = 'true'
            if value == '0':
                value = 'false'
            self.construct_controller.set_pin_default_value('%s.%s' % (n(self.construct_node), name), value, False)

        if value_type == rigs.AttrType.NUMBER:
            value = str(value[0])
            self.construct_controller.set_pin_default_value('%s.%s' % (n(self.construct_node), name), value, False)
            self.forward_controller.set_pin_default_value('%s.%s' % (n(self.construct_node), name), value, False)

        if value_type == rigs.AttrType.STRING:
            if value is None:
                value = ''
            else:
                value = value[0]

            self.construct_controller.set_pin_default_value('%s.%s' % (n(self.construct_node), name), value, False)

        if value_type == rigs.AttrType.COLOR:
            if value:
                self._reset_array(name, value)
                for inc, color in enumerate(value):
                    pin_name = f'{n(self.construct_node)}.{name}'
                    self.construct_controller.insert_array_pin(pin_name, -1, '')
                    self.construct_controller.set_pin_default_value(f'{pin_name}.{inc}.R', str(color[0]), True)
                    self.construct_controller.set_pin_default_value(f'{pin_name}.{inc}.G', str(color[1]), True)
                    self.construct_controller.set_pin_default_value(f'{pin_name}.{inc}.B', str(color[2]), True)
                    self.construct_controller.set_pin_default_value(f'{pin_name}.{inc}.A', str(color[3]), True)

        construct_pin = f'{n(self.construct_node)}.{name}'
        forward_pin = f'{n(self.forward_node)}.{name}'
        backward_pin = f'{n(self.backward_node)}.{name}'
        controllers = [self.construct_controller, self.forward_controller, self.backward_controller]
        pins = [construct_pin, forward_pin, backward_pin]

        if value_type == rigs.AttrType.TRANSFORM:
            self._reset_array(name, value)

            if not value:
                return

            for controller, pin in zip(controllers, pins):
                controller.set_array_pin_size(pin, len(value))
                for inc, joint in enumerate(value):
                    controller.set_pin_default_value(f'{pin}.{inc}.Type', 'Bone', False)
                    controller.set_pin_default_value(f'{pin}.{inc}.Name', joint, False)

        if value_type == rigs.AttrType.VECTOR:
            self._reset_array(name, value)

            if not value:
                return
            for controller, pin in zip(controllers, pins):
                controller.set_array_pin_size(pin, len(value))
                for inc, vector in enumerate(value):
                    controller.set_pin_default_value(f'{pin}.{inc}.X', str(vector[0]), False)
                    controller.set_pin_default_value(f'{pin}.{inc}.Z', str(vector[1]), False)
                    controller.set_pin_default_value(f'{pin}.{inc}.Y', str(vector[2]), False)

    def _create_control(self, controller):
        control_node = self.library_functions['vetalaLib_Control']
        control = controller.add_function_reference_node(control_node,
                                                         unreal.Vector2D(2500, -1300),
                                                         n(control_node))

        controller.add_link('Entry.color', f'{n(control)}.color')

        controller.add_link('Entry.shape', f'{n(control)}.shape')
        controller.add_link('Entry.description', f'{n(control)}.description')
        controller.add_link('Entry.side', f'{n(control)}.side')
        controller.add_link('Entry.restrain_numbering', f'{n(control)}.restrain_numbering')

        controller.add_link('Entry.joint_token', f'{n(control)}.joint_token')
        controller.add_link('Entry.shape_translate', f'{n(control)}.translate')
        controller.add_link('Entry.shape_rotate', f'{n(control)}.rotate')
        controller.add_link('Entry.shape_scale', f'{n(control)}.scale')

        graph = controller.get_graph()

        if graph.find_pin('Entry.sub_count'):
            controller.add_link('Entry.sub_count', f'{n(control)}.sub_count')
        if graph.find_pin('Entry.sub_color'):
            controller.add_link('Entry.sub_color', f'{n(control)}.sub_color')

        return control

    def _build_solve_switch(self):
        controller = self.function_controller

        switch = self.function_controller.add_template_node('DISPATCH_RigVMDispatch_SwitchInt32(in Index)',
                                                            unreal.Vector2D(225, -160),
                                                            'DISPATCH_RigVMDispatch_SwitchInt32')
        self.function_controller.insert_array_pin(f'{n(switch)}.Cases', -1, '')
        graph.add_link('Entry', 'ExecuteContext', switch, 'ExecuteContext', controller)
        graph.add_link('Entry', 'mode', switch, 'Index', controller)
        graph.add_link(switch, 'Completed', 'Return', 'ExecuteContext', controller)

        self.function_controller.set_node_position_by_name('Return', unreal.Vector2D(4000, 0))
        self.switch = switch

    def _build_function_construct_graph(self):
        return

    def _build_function_forward_graph(self):
        return

    def _build_function_backward_graph(self):
        return

    def _build_function_graph(self):

        if not self.graph:
            return

        self._build_solve_switch()
        self._build_function_construct_graph()
        self._build_function_forward_graph()
        self._build_function_backward_graph()

    def set_node_position(self, position_x, position_y):

        if self.construct_node:
            self.construct_controller.set_node_position_by_name(n(self.construct_node),
                                                                unreal.Vector2D(position_x, position_y))
        if self.forward_node:
            self.forward_controller.set_node_position_by_name(n(self.forward_node),
                                                              unreal.Vector2D(position_x, position_y))
        if self.backward_node:
            self.backward_controller.set_node_position_by_name(n(self.backward_node),
                                                               unreal.Vector2D(position_x, position_y))

    def is_valid(self):
        if self.rig.state == rigs.RigState.CREATED:
            if not self.forward_node or not self.construct_node or not self.backward_node:
                return False
        if self.rig.state == rigs.RigState.LOADED:
            if not self.graph:
                return False

        return True

    def is_built(self):
        if self.forward_node and self.construct_node and self.backward_node:
            return True

    def get_controllers(self):
        return [self.construct_controller, self.forward_controller, self.backward_controller]

    def get_graph_start_nodes(self):

        forward_start = 'BeginExecution'

        if not self.forward_controller.get_graph().find_node('BeginExecution'):
            forward_start = 'RigUnit_BeginExecution'

        return ['PrepareForExecution', forward_start, 'InverseExecution']

    def name(self):
        # the name is the same for construct, forward and backward. The controller for the graph is what changes.
        return n(self.construct_node)

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

        self._set_attr_on_function('shape')

    def load(self):
        super(UnrealUtilRig, self).load()

        if not self.graph:

            self.graph = unreal_lib.graph.get_current_control_rig()

            if not self.graph:
                control_rigs = unreal.ControlRigBlueprint.get_currently_open_rig_blueprints()
                if not control_rigs:
                    return
                unreal_lib.graph.current_control_rig = control_rigs[0]
                self.graph = control_rigs[0]

            if not self.graph:  # TODO: Refactor this is really messy, we are checking for a value potentially modifying it and checking its state again in the next block.
                util.warning('No control rig set, cannot load.')
                return

        if not self.library:
            self.library = self.graph.get_local_function_library()
        if not self.controller:
            self.controller = self.graph.get_controller(self.library)

        if not self.forward_controller:
            self.forward_controller = unreal_lib.graph.get_forward_controller(self.graph)

        if not self.construct_controller:
            self.construct_controller = unreal_lib.graph.get_construct_controller(self.graph)

        if not self.backward_controller:
            self.backward_controller = unreal_lib.graph.get_backward_controller(self.graph)

        if not self.construct_controller:
            util.warning('No construction graph found.')
            return

        self.construct_node = self._get_function_node(self.construct_controller)
        self.forward_node = self._get_function_node(self.forward_controller)
        self.backward_node = self._get_function_node(self.backward_controller)

        if self.is_built():
            self.rig.state = rigs.RigState.CREATED

        if self.construct_controller:
            self.rig.dirty = False

        self._get_existing_rig_function()

    def build(self):
        super(UnrealUtilRig, self).build()

        if not in_unreal:
            return

        if not self.graph:
            util.warning('No control rig for Unreal rig')
            return
        # function_node = self.construct_controller.get_graph().find_node(self.function.get_node_path())

        graph.open_undo('build')
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
            self._set_attr_on_function(name)

        for name in self.rig.attr.inputs:
            self._set_attr_on_function(name)

        if self.is_built():
            self.rig.state = rigs.RigState.CREATED

        self._attribute_cache = copy.deepcopy(self.rig.attr)

        graph.close_undo('build')

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
            self.construct_controller.remove_node_by_name(n(self.construct_node))

        if self.forward_node:
            self.forward_controller.remove_node_by_name(n(self.forward_node))

        if self.backward_node:
            self.backward_controller.remove_node_by_name(n(self.backward_node))

        self.rig.state = rigs.RigState.LOADED


class UnrealFkRig(UnrealUtilRig):

    def _build_function_construct_graph(self):
        controller = self.function_controller

        for_each = controller.add_template_node(
            'DISPATCH_RigVMDispatch_ArrayIterator(in Array,out Element,out Index,out Count,out Ratio)',
            unreal.Vector2D(1500, -1250), 'DISPATCH_RigVMDispatch_ArrayIterator')

        controller.add_link(f'{n(self.switch)}.Cases.0', f'{n(for_each)}.ExecuteContext')

        controller.add_link('Entry.joints', f'{n(for_each)}.Array')

        control = self._create_control(controller)

        parent_node = self.library_functions['vetalaLib_GetParent']
        parent = controller.add_function_reference_node(parent_node, unreal.Vector2D(1880, -1450), n(parent_node))

        joint_description_node = self.library_functions['vetalaLib_GetJointDescription']
        joint_description = controller.add_function_reference_node(joint_description_node, unreal.Vector2D(1900, -1000),
                                                                   n(joint_description_node))

        controller.add_link(f'{n(for_each)}.Index', f'{n(control)}.increment')
        controller.add_link(f'{n(for_each)}.Element', f'{n(control)}.driven')

        controller.add_link(f'{n(for_each)}.ExecuteContext', f'{n(control)}.ExecuteContext')

        meta_data = controller.add_template_node(
            'DISPATCH_RigDispatch_SetMetadata(in Item,in Name,in Value,out Success)', unreal.Vector2D(3000, -1450),
            'DISPATCH_RigDispatch_SetMetadata')
        controller.add_link(f'{n(control)}.ExecuteContext', f'{n(meta_data)}.ExecuteContext')
        controller.add_link(f'{n(for_each)}.Element', f'{n(meta_data)}.Item')
        controller.set_pin_default_value('DISPATCH_RigDispatch_SetMetadata.Name', 'Control', False)
        controller.add_link(f'{n(control)}.Last Control', f'{n(meta_data)}.Value')

        index_equals = controller.add_template_node('DISPATCH_RigVMDispatch_CoreEquals(in A,in B,out Result)',
                                                    unreal.Vector2D(1800, -1450), 'DISPATCH_RigVMDispatch_CoreEquals')
        controller.add_link(f'{n(for_each)}.Index', f'{n(index_equals)}.A')
        controller.add_link(f'{n(index_equals)}.Result', f'{n(parent)}.is_top_joint')
        controller.add_link(f'{n(for_each)}.Element', f'{n(parent)}.joint')
        controller.add_link('Entry.parent', f'{n(parent)}.default_parent')
        controller.add_link('Entry.hierarchy', f'{n(parent)}.in_hierarchy')
        controller.add_link(f'{n(parent)}.Result', f'{n(control)}.parent')

        description = controller.add_variable_node('description', 'FString', None, True, '',
                                                   unreal.Vector2D(1500, -600), 'VariableNode_description')
        use_joint_name = controller.add_variable_node('use_joint_name', 'FString', None, True, '',
                                                      unreal.Vector2D(1500, -600), 'VariableNode_use_joint_name')
        joint_token = controller.add_variable_node('joint_token', 'FString', None, True, '',
                                                   unreal.Vector2D(1500, -1000), 'VariableNode_joint_token')
        description_if = self.function_controller.add_template_node(
            'DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(2250, -700),
            'DISPATCH_RigVMDispatch_If')

        controller.add_link(f'{n(for_each)}.ExecuteContext', f'{n(joint_description)}.ExecuteContext')
        controller.add_link(f'{n(for_each)}.Element', f'{n(joint_description)}.joint')
        controller.add_link(f'{n(joint_token)}.Value', f'{n(joint_description)}.joint_token')
        controller.add_link(f'{n(description)}.Value', f'{n(joint_description)}.description')
        controller.add_link(f'{n(joint_description)}.ExecuteContext', f'{n(control)}.ExecuteContext')

        controller.add_link(f'{n(use_joint_name)}.Value', f'{n(description_if)}.Condition')
        controller.add_link(f'{n(joint_description)}.Result', f'{n(description_if)}.True')
        controller.add_link(f'{n(description)}.Value', f'{n(description_if)}.False')
        controller.add_link(f'{n(description_if)}.Result', f'{n(control)}.description')

        self.function_controller.add_local_variable_from_object_path('local_controls', 'TArray<FRigElementKey>',
                                                                     '/Script/ControlRig.RigElementKey', '')

        add_control = self.function_controller.add_template_node(
            'DISPATCH_RigVMDispatch_ArrayAdd(io Array,in Element,out Index)', unreal.Vector2D(2800, -900),
            'DISPATCH_RigVMDispatch_ArrayAdd')
        self.function_controller.add_link(f'{n(control)}.Control', f'{n(add_control)}.Element')
        self.function_controller.add_link(f'{n(meta_data)}.ExecuteContext', f'{n(add_control)}.ExecuteContext')

        variable_node = self.function_controller.add_variable_node_from_object_path('local_controls', 'FRigElementKey',
                                                                                    '/Script/ControlRig.RigElementKey',
                                                                                    True, '()',
                                                                                    unreal.Vector2D(2700, -700),
                                                                                    'VariableNode')
        self.function_controller.add_link(f'{n(variable_node)}.Value', f'{n(add_control)}.Array')

        self.function_controller.add_link(f'{n(variable_node)}.Value', 'Return.controls')

        current_locals = locals()
        nodes = unreal_lib.graph.filter_nodes(current_locals.values())
        node = unreal_lib.graph.comment_nodes(nodes, controller, 'Construction')

        nodes.append(node)
        unreal_lib.graph.move_nodes(500, -2000, nodes, controller)

    def _build_function_forward_graph(self):
        for_each = self.function_controller.add_template_node(
            'DISPATCH_RigVMDispatch_ArrayIterator(in Array,out Element,out Index,out Count,out Ratio)',
            unreal.Vector2D(850, 250), 'DISPATCH_RigVMDispatch_ArrayIterator')
        self.function_controller.add_link(f'{n(self.switch)}.Cases.1', f'{n(for_each)}.ExecuteContext')
        self.function_controller.add_link('Entry.joints', '%s.Array' % (for_each.get_node_path()))

        meta_data = self.function_controller.add_template_node(
            'DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in Default,out Value,out Found)',
            unreal.Vector2D(1250, 350), 'DISPATCH_RigDispatch_GetMetadata')
        self.function_controller.set_pin_default_value('%s.Name' % meta_data.get_node_path(), 'Control', False)
        self.function_controller.add_link('%s.Element' % for_each.get_node_path(),
                                          '%s.Item' % meta_data.get_node_path())

        get_transform = self.function_controller.add_unit_node_from_struct_path(
            '/Script/ControlRig.RigUnit_GetTransform', 'Execute', unreal.Vector2D(1550, 350), 'GetTransform')
        self.function_controller.add_link('%s.Value' % meta_data.get_node_path(),
                                          '%s.Item' % get_transform.get_node_path())
        set_transform = self.function_controller.add_template_node(
            'Set Transform::Execute(in Item,in Space,in bInitial,in Value,in Weight,in bPropagateToChildren)',
            unreal.Vector2D(2000, 250), 'Set Transform')

        self.function_controller.add_link('%s.Transform' % get_transform.get_node_path(),
                                          '%s.Value' % set_transform.get_node_path())
        self.function_controller.add_link('%s.Element' % for_each.get_node_path(),
                                          '%s.Item' % set_transform.get_node_path())

        self.function_controller.add_link('%s.ExecuteContext' % for_each.get_node_path(),
                                          '%s.ExecuteContext' % set_transform.get_node_path())

        current_locals = locals()
        nodes = unreal_lib.graph.filter_nodes(current_locals.values())
        node = unreal_lib.graph.comment_nodes(nodes, self.function_controller, 'Forward Solve')

        nodes.append(node)
        unreal_lib.graph.move_nodes(500, 0, nodes, self.function_controller)

    def _build_function_backward_graph(self):
        controller = self.function_controller
        for_each = controller.add_template_node(
            'DISPATCH_RigVMDispatch_ArrayIterator(in Array,out Element,out Index,out Count,out Ratio)',
            unreal.Vector2D(850, 1250), 'DISPATCH_RigVMDispatch_ArrayIterator')
        controller.add_link(f'{n(self.switch)}.Cases.2', f'{n(for_each)}.ExecuteContext')
        controller.add_link('Entry.joints', f'{n(for_each)}.Array')

        set_transform = self.function_controller.add_template_node(
            'Set Transform::Execute(in Item,in Space,in bInitial,in Value,in Weight,in bPropagateToChildren)',
            unreal.Vector2D(2000, 1250), 'Set Transform')

        meta_data = self.function_controller.add_template_node(
            'DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in Default,out Value,out Found)',
            unreal.Vector2D(1250, 1350), 'DISPATCH_RigDispatch_GetMetadata')
        self.function_controller.set_pin_default_value('%s.Name' % meta_data.get_node_path(), 'Control', False)
        # self.function_controller.add_link('%s.Element' % for_each.get_node_path(), '%s.Item' % meta_data.get_node_path())

        self.function_controller.add_link(f'{n(meta_data)}.Value', f'{n(set_transform)}.Item')

        get_transform = self.function_controller.add_unit_node_from_struct_path(
            '/Script/ControlRig.RigUnit_GetTransform', 'Execute', unreal.Vector2D(1550, 1350), 'GetTransform')
        self.function_controller.add_link(f'{n(for_each)}.Element', f'{n(get_transform)}.Item')

        self.function_controller.add_link('%s.Transform' % get_transform.get_node_path(),
                                          '%s.Value' % set_transform.get_node_path())

        self.function_controller.add_link('%s.ExecuteContext' % for_each.get_node_path(),
                                          '%s.ExecuteContext' % set_transform.get_node_path())

        current_locals = locals()
        nodes = unreal_lib.graph.filter_nodes(current_locals.values())
        node = unreal_lib.graph.comment_nodes(nodes, self.function_controller, 'Backward Solve')

        nodes.append(node)
        unreal_lib.graph.move_nodes(500, 1000, nodes, self.function_controller)


class UnrealIkRig(UnrealUtilRig):

    def _build_function_construct_graph(self):
        return

    def _build_function_forward_graph(self):
        return

    def _build_function_backward_graph(self):
        return


class UnrealSplineIkRig(UnrealUtilRig):

    def _build_function_construct_graph(self):
        controller = self.function_controller

        for_each = controller.add_template_node(
            'DISPATCH_RigVMDispatch_ArrayIterator(in Array,out Element,out Index,out Count,out Ratio)',
            unreal.Vector2D(1500, -1250), 'DISPATCH_RigVMDispatch_ArrayIterator')

        controller.add_link(f'{n(self.switch)}.Cases.0', f'{n(for_each)}.ExecuteContext')

        controller.add_link('Entry.joints', f'{n(for_each)}.Array')

        control = self._create_control(controller)

        parent_node = self.library_functions['vetalaLib_GetParent']
        parent = controller.add_function_reference_node(parent_node, unreal.Vector2D(1880, -1450), n(parent_node))

        joint_description_node = self.library_functions['vetalaLib_GetJointDescription']
        joint_description = controller.add_function_reference_node(joint_description_node, unreal.Vector2D(1900, -1000),
                                                                   n(joint_description_node))

        controller.add_link(f'{n(for_each)}.Index', f'{n(control)}.increment')
        controller.add_link(f'{n(for_each)}.Element', f'{n(control)}.driven')

        controller.add_link(f'{n(for_each)}.ExecuteContext', f'{n(control)}.ExecuteContext')

        meta_data = controller.add_template_node(
            'DISPATCH_RigDispatch_SetMetadata(in Item,in Name,in Value,out Success)', unreal.Vector2D(3000, -1450),
            'DISPATCH_RigDispatch_SetMetadata')
        controller.add_link(f'{n(control)}.ExecuteContext', f'{n(meta_data)}.ExecuteContext')
        controller.add_link(f'{n(for_each)}.Element', f'{n(meta_data)}.Item')
        controller.set_pin_default_value('DISPATCH_RigDispatch_SetMetadata.Name', 'Control', False)
        controller.add_link(f'{n(control)}.Last Control', f'{n(meta_data)}.Value')

        index_equals = controller.add_template_node('DISPATCH_RigVMDispatch_CoreEquals(in A,in B,out Result)',
                                                    unreal.Vector2D(1800, -1450), 'DISPATCH_RigVMDispatch_CoreEquals')
        controller.add_link(f'{n(for_each)}.Index', f'{n(index_equals)}.A')
        controller.add_link(f'{n(index_equals)}.Result', f'{n(parent)}.is_top_joint')
        controller.add_link(f'{n(for_each)}.Element', f'{n(parent)}.joint')
        controller.add_link('Entry.parent', f'{n(parent)}.default_parent')
        controller.add_link('Entry.hierarchy', f'{n(parent)}.in_hierarchy')
        controller.add_link(f'{n(parent)}.Result', f'{n(control)}.parent')

        description = controller.add_variable_node('description', 'FString', None, True, '',
                                                   unreal.Vector2D(1500, -600), 'VariableNode_description')
        # use_joint_name = controller.add_variable_node('use_joint_name', 'FString', None, True, '',
        #                                              unreal.Vector2D(1500, -600), 'VariableNode_use_joint_name')
        joint_token = controller.add_variable_node('joint_token', 'FString', None, True, '',
                                                   unreal.Vector2D(1500, -1000), 'VariableNode_joint_token')
        description_if = self.function_controller.add_template_node(
            'DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(2250, -700),
            'DISPATCH_RigVMDispatch_If')

        controller.add_link(f'{n(for_each)}.ExecuteContext', f'{n(joint_description)}.ExecuteContext')
        controller.add_link(f'{n(for_each)}.Element', f'{n(joint_description)}.joint')
        controller.add_link(f'{n(joint_token)}.Value', f'{n(joint_description)}.joint_token')
        controller.add_link(f'{n(description)}.Value', f'{n(joint_description)}.description')
        controller.add_link(f'{n(joint_description)}.ExecuteContext', f'{n(control)}.ExecuteContext')

        # controller.add_link(f'{n(use_joint_name)}.Value', f'{n(description_if)}.Condition')
        controller.add_link(f'{n(joint_description)}.Result', f'{n(description_if)}.True')
        controller.add_link(f'{n(description)}.Value', f'{n(description_if)}.False')
        controller.add_link(f'{n(description_if)}.Result', f'{n(control)}.description')

        self.function_controller.add_local_variable_from_object_path('local_controls', 'TArray<FRigElementKey>',
                                                                     '/Script/ControlRig.RigElementKey', '')

        add_control = self.function_controller.add_template_node(
            'DISPATCH_RigVMDispatch_ArrayAdd(io Array,in Element,out Index)', unreal.Vector2D(2800, -900),
            'DISPATCH_RigVMDispatch_ArrayAdd')
        self.function_controller.add_link(f'{n(control)}.Control', f'{n(add_control)}.Element')
        self.function_controller.add_link(f'{n(meta_data)}.ExecuteContext', f'{n(add_control)}.ExecuteContext')

        variable_node = self.function_controller.add_variable_node_from_object_path('local_controls', 'FRigElementKey',
                                                                                    '/Script/ControlRig.RigElementKey',
                                                                                    True, '()',
                                                                                    unreal.Vector2D(2700, -700),
                                                                                    'VariableNode')
        self.function_controller.add_link(f'{n(variable_node)}.Value', f'{n(add_control)}.Array')

        self.function_controller.add_link(f'{n(variable_node)}.Value', 'Return.controls')

        current_locals = locals()
        nodes = unreal_lib.graph.filter_nodes(current_locals.values())
        node = unreal_lib.graph.comment_nodes(nodes, controller, 'Construction')

        nodes.append(node)
        unreal_lib.graph.move_nodes(500, -2000, nodes, controller)

    def _build_function_forward_graph(self):
        return

    def _build_function_backward_graph(self):
        return


class UnrealWheelRig(UnrealUtilRig):

    def _build_function_construct_graph(self):
        controller = self.function_controller

        control = self._create_control(controller)
        graph.add_link(self.switch, 'Cases.0', control, 'ExecuteContext', controller)

        control_spin = self._create_control(controller)

        graph.add_link(control, 'ExecuteContext', control_spin, 'ExecuteContext', controller)

        controller.set_node_position(control_spin, unreal.Vector2D(2900, -800.000000))

        graph.add_link(control, 'Control', control_spin, 'parent', controller)
        graph.add_link('Entry', 'spin_control_color', control_spin, 'color', controller)

        at_rotate = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(1400, -250), 'DISPATCH_RigVMDispatch_ArrayGetAtIndex')
        add_rotate = controller.add_template_node('Add::Execute(in A,in B,out Result)', unreal.Vector2D(1700, -250), 'Add')
        make_array = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayMake(in Values,out Array)', unreal.Vector2D(1900, -250), 'DISPATCH_RigVMDispatch_ArrayMake')
        controller.add_link(f'{n(make_array)}.Array', f'{n(control)}.rotate')
        controller.add_link(f'{n(make_array)}.Array', f'{n(control_spin)}.rotate')

        controller.add_link('Entry.shape_rotate', f'{n(at_rotate)}.Array')
        controller.add_link(f'{n(at_rotate)}.Element', f'{n(add_rotate)}.B')
        controller.add_link(f'{n(add_rotate)}.Result', f'{n(make_array)}.Values.0')
        controller.set_pin_default_value(f'{n(add_rotate)}.A.Y', '90.000000', False)
        controller.add_link(f'{n(make_array)}.Array', f'{n(control)}.rotate')

        shape_equals = controller.add_template_node('DISPATCH_RigVMDispatch_CoreEquals(in A,in B,out Result)', unreal.Vector2D(450, -550), 'DISPATCH_RigVMDispatch_CoreEquals')
        controller.set_pin_default_value(f'{n(shape_equals)}.B', 'Default', False)
        shape_if = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(600, -550), 'DISPATCH_RigVMDispatch_If')

        controller.add_link('Entry.shape', f'{n(shape_equals)}.A')
        controller.add_link(f'{n(shape_equals)}.Result', f'{n(shape_if)}.Condition')
        controller.add_link('Entry.shape', f'{n(shape_if)}.False')
        controller.set_pin_default_value(f'{n(shape_if)}.True', 'Circle_Thin', False)
        controller.add_link(f'{n(shape_if)}.Result', f'{n(control)}.shape')
        controller.set_pin_default_value(f'{n(shape_equals)}.B', 'Default', False)

        shape_spin_equals = controller.add_template_node('DISPATCH_RigVMDispatch_CoreEquals(in A,in B,out Result)', unreal.Vector2D(450, -750), 'DISPATCH_RigVMDispatch_CoreEquals')
        controller.set_pin_default_value(f'{n(shape_spin_equals)}.B', 'Default', False)
        shape_spin_if = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(600, -750), 'DISPATCH_RigVMDispatch_If')

        controller.add_link('Entry.spin_control_shape', f'{n(shape_spin_equals)}.A')
        controller.add_link(f'{n(shape_spin_equals)}.Result', f'{n(shape_spin_if)}.Condition')
        controller.add_link('Entry.spin_control_shape', f'{n(shape_spin_if)}.False')
        controller.set_pin_default_value(f'{n(shape_spin_if)}.True', 'Arrow4_Solid', False)
        controller.add_link(f'{n(shape_spin_if)}.Result', f'{n(control_spin)}.shape')
        controller.set_pin_default_value(f'{n(shape_spin_equals)}.B', 'Default', False)

        description_join = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_StringJoin', 'Execute', unreal.Vector2D(450, -350), 'RigVMFunction_StringJoin')
        controller.insert_array_pin(f'{n(description_join)}.Values', -1, '')
        controller.insert_array_pin(f'{n(description_join)}.Values', -1, '')
        controller.set_pin_default_value(f'{n(description_join)}.Separator', '_', False)
        graph.add_link('Entry', 'description', description_join, 'Values.0', controller)
        controller.set_pin_default_value(f'{n(description_join)}.Values.1', 'spin', False)

        graph.add_link(description_join, 'Result', control_spin, 'description', controller)

        parent = controller.add_variable_node_from_object_path('parent', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(2000, -1000), 'VariableNode')

        at_parent = self.library_functions['vetalaLib_GetItem']
        at_parent = controller.add_function_reference_node(at_parent,
                                                         unreal.Vector2D(2200, -1000),
                                                         n(at_parent))

        controller.set_pin_default_value(f'{n(at_parent)}.index', '-1', False)

        graph.add_link(parent, 'Value', at_parent, 'Array', controller)
        graph.add_link(at_parent, 'Element', control, 'parent', controller)

        joints = controller.add_variable_node_from_object_path('joints', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(2000, -800), 'VariableNode')

        at_joints = self.library_functions['vetalaLib_GetItem']
        at_joints = controller.add_function_reference_node(at_joints,
                                                         unreal.Vector2D(2200, -800),
                                                         n(at_joints))

        controller.set_pin_default_value(f'{n(at_joints)}.index', '0', False)

        graph.add_link(joints, 'Value', at_joints, 'Array', controller)
        graph.add_link(at_joints, 'Element', control, 'driven', controller)
        graph.add_link(at_joints, 'Element', control_spin, 'driven', controller)

        graph.add_link(joints, 'Value', control_spin, 'driven', controller)

        joint_metadata = controller.add_template_node('DISPATCH_RigDispatch_SetMetadata(in Item,in Name,in Value,out Success)', unreal.Vector2D(3200, -800), 'DISPATCH_RigDispatch_SetMetadata')
        controller.set_pin_default_value(f'{n(joint_metadata)}.Name', 'Control', False)
        graph.add_link(control_spin, 'ExecuteContext', joint_metadata, 'ExecuteContext', controller)
        graph.add_link(control_spin, 'Control', joint_metadata, 'Value', controller)
        graph.add_link(at_joints, 'Element', joint_metadata, 'Item', controller)

        graph.add_link('Entry', 'spin_control_shape', control_spin, 'color', controller)
        channel_diameter = graph.add_animation_channel(controller, 'Diameter')
        graph.add_link(joint_metadata, 'ExecuteContext', channel_diameter, 'ExecuteContext', controller)
        graph.add_link(control, 'Control', channel_diameter, 'Parent', controller)

        controller.resolve_wild_card_pin(f'{n(channel_diameter)}.InitialValue', 'float', unreal.Name())
        controller.set_pin_default_value(f'{n(channel_diameter)}.MaximumValue', '1000000000000.0', False)
        controller.set_pin_default_value(f'{n(channel_diameter)}.InitialValue', '9.888', False)

        channel_enable = graph.add_animation_channel(controller, 'Enable')
        graph.add_link(channel_diameter, 'ExecuteContext', channel_enable, 'ExecuteContext', controller)
        graph.add_link(control, 'Control', channel_enable, 'Parent', controller)

        controller.resolve_wild_card_pin(f'{n(channel_enable)}.InitialValue', 'float', unreal.Name())
        controller.set_pin_default_value(f'{n(channel_enable)}.InitialValue', '1.0', False)

        channel_multiply = graph.add_animation_channel(controller, 'RotateMultiply')
        graph.add_link(channel_enable, 'ExecuteContext', channel_multiply, 'ExecuteContext', controller)
        graph.add_link(control, 'Control', channel_multiply, 'Parent', controller)

        controller.resolve_wild_card_pin(f'{n(channel_multiply)}.InitialValue', 'float', unreal.Name())
        controller.set_pin_default_value(f'{n(channel_multiply)}.InitialValue', '1.0', False)

        wheel_diameter = controller.add_variable_node('wheel_diameter', 'float', None, True, '', unreal.Vector2D(3200, -500), 'VariableNode')
        graph.add_link(wheel_diameter, 'Value', channel_diameter, 'InitialValue', controller)

        current_locals = locals()
        nodes = unreal_lib.graph.filter_nodes(current_locals.values())
        node = unreal_lib.graph.comment_nodes(nodes, controller, 'Construction')

        nodes.append(node)
        unreal_lib.graph.move_nodes(500, -2000, nodes, controller)

    def _build_function_forward_graph(self):
        controller = self.function_controller

        joints = controller.add_variable_node_from_object_path('joints', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(500, 0), 'VariableNode')
        at_joints = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(700, 0), 'DISPATCH_RigVMDispatch_ArrayGetAtIndex')

        graph.add_link(joints, 'Value', at_joints, 'Array', controller)

        meta_data = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in Default,out Value,out Found)', unreal.Vector2D(900, 0), 'DISPATCH_RigDispatch_GetMetadata')
        controller.set_pin_default_value(f'{n(meta_data)}.Name', 'Control', False)
        graph.add_link(at_joints, 'Element', meta_data, 'Item', controller)

        get_parent = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyGetParent', 'Execute', unreal.Vector2D(1200, 0), 'HierarchyGetParent')
        graph.add_link(meta_data, 'Value', get_parent, 'Child', controller)

        get_transform = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetTransform', 'Execute', unreal.Vector2D(1500, 0), 'GetTransform')
        set_transform = controller.add_template_node('Set Transform::Execute(in Item,in Space,in bInitial,in Value,in Weight,in bPropagateToChildren)', unreal.Vector2D(1500, 250), 'Set Transform')

        graph.add_link(meta_data, 'Value', get_transform, 'Item', controller)
        graph.add_link(at_joints, 'Element', set_transform, 'Item', controller)
        graph.add_link(get_transform, 'Transform', set_transform, 'Value', controller)

        graph.add_link(self.switch, 'Cases.1', set_transform, 'ExecuteContext', controller)

        wheel_rotate = self.library_functions['vetalaLib_WheelRotate']
        wheel_rotate = controller.add_function_reference_node(wheel_rotate,
                                                         unreal.Vector2D(1900, 0),
                                                         n(wheel_rotate))

        graph.add_link(set_transform, 'ExecuteContext', wheel_rotate, 'ExecuteContext', controller)
        graph.add_link(meta_data, 'Value', wheel_rotate, 'control_spin', controller)
        graph.add_link(get_parent, 'Parent', wheel_rotate, 'control', controller)

        current_locals = locals()
        nodes = unreal_lib.graph.filter_nodes(current_locals.values())
        node = unreal_lib.graph.comment_nodes(nodes, controller, 'Forward Solve')

        controller.set_pin_default_value(f'{n(wheel_rotate)}.Diameter', '9.888', False)
        controller.set_pin_default_value(f'{n(wheel_rotate)}.Enable', '1.0', False)
        controller.set_pin_default_value(f'{n(wheel_rotate)}.RotateMultiply', '1.0', False)

        at_forward = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(1700, 600), 'DISPATCH_RigVMDispatch_ArrayGetAtIndex')
        at_rotate = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(1700, 600), 'DISPATCH_RigVMDispatch_ArrayGetAtIndex')

        graph.add_link('Entry', 'forward_axis', at_forward, 'Array', controller)
        graph.add_link('Entry', 'rotate_axis', at_rotate, 'Array', controller)

        graph.add_link(at_forward, 'Element', wheel_rotate, 'forwardAxis', controller)
        graph.add_link(at_rotate, 'Element', wheel_rotate, 'rotateAxis', controller)

        channel_enable = controller.add_template_node('GetAnimationChannel::Execute(out Value,in Control,in Channel,in bInitial)', unreal.Vector2D(1200, 250), 'GetAnimationChannel')
        graph.add_link(get_parent, 'Parent.Name', channel_enable, 'Control', controller)
        controller.set_pin_default_value(f'{n(channel_enable)}.Channel', 'Enable', False)
        graph.add_link(channel_enable, 'Value', wheel_rotate, 'Enable', controller)

        channel_multiply = controller.add_template_node('GetAnimationChannel::Execute(out Value,in Control,in Channel,in bInitial)', unreal.Vector2D(1200, 500), 'GetAnimationChannel')
        graph.add_link(get_parent, 'Parent.Name', channel_multiply, 'Control', controller)
        controller.set_pin_default_value(f'{n(channel_multiply)}.Channel', 'RotateMultiply', False)
        graph.add_link(channel_multiply, 'Value', wheel_rotate, 'RotateMultiply', controller)

        channel_diameter = controller.add_template_node('GetAnimationChannel::Execute(out Value,in Control,in Channel,in bInitial)', unreal.Vector2D(1200, 500), 'GetAnimationChannel')
        graph.add_link(get_parent, 'Parent.Name', channel_diameter, 'Control', controller)
        controller.set_pin_default_value(f'{n(channel_diameter)}.Channel', 'Diameter', False)
        graph.add_link(channel_diameter, 'Value', wheel_rotate, 'Diameter', controller)

        nodes.append(node)
        unreal_lib.graph.move_nodes(500, 0, nodes, controller)

    def _build_function_backward_graph(self):
        controller = self.function_controller

        joints = controller.add_variable_node_from_object_path('joints', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(500, 0), 'VariableNode')
        at_joints = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(700, 0), 'DISPATCH_RigVMDispatch_ArrayGetAtIndex')

        graph.add_link(joints, 'Value', at_joints, 'Array', controller)

        meta_data = self.function_controller.add_template_node(
            'DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in Default,out Value,out Found)',
            unreal.Vector2D(900, 0), 'DISPATCH_RigDispatch_GetMetadata')
        controller.set_pin_default_value(f'{n(meta_data)}.Name', 'Control', False)
        graph.add_link(at_joints, 'Element', meta_data, 'Item', controller)

        get_parent = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyGetParent', 'Execute', unreal.Vector2D(1200, 0), 'HierarchyGetParent')
        graph.add_link(meta_data, 'Value', get_parent, 'Child', controller)

        set_channel = controller.add_template_node('SetAnimationChannel::Execute(in Value,in Control,in Channel,in bInitial)', unreal.Vector2D(1600, 0), 'SetAnimationChannel')

        controller.resolve_wild_card_pin(f'{n(set_channel)}.Value', 'float', unreal.Name())
        controller.set_pin_default_value(f'{n(set_channel)}.Channel', 'Enable', False)
        controller.set_pin_default_value(f'{n(set_channel)}.Value', '0.0', False)
        graph.add_link(self.switch, 'Cases.2', set_channel, 'ExecuteContext', controller)
        graph.add_link(get_parent, 'Parent.Name', set_channel, 'Control', controller)

        get_transform = controller.add_unit_node_from_struct_path(
            '/Script/ControlRig.RigUnit_GetTransform', 'Execute', unreal.Vector2D(1600, 300), 'GetTransform')

        set_transform = controller.add_template_node(
            'Set Transform::Execute(in Item,in Space,in bInitial,in Value,in Weight,in bPropagateToChildren)',
            unreal.Vector2D(2000, 0), 'Set Transform')

        set_transform_spin = controller.add_template_node(
            'Set Transform::Execute(in Item,in Space,in bInitial,in Value,in Weight,in bPropagateToChildren)',
            unreal.Vector2D(2000, 300), 'Set Transform')

        graph.add_link(get_parent, 'Parent', set_transform, 'Item', controller)
        graph.add_link(meta_data, 'Value', set_transform_spin, 'Item', controller)

        graph.add_link(at_joints, 'Element', get_transform, 'Item', controller)

        graph.add_link(get_transform, 'Transform', set_transform_spin, 'Value', controller)
        graph.add_link(get_transform, 'Transform', set_transform, 'Value', controller)

        graph.add_link(set_channel, 'ExecuteContext', set_transform, 'ExecuteContext', controller)

        current_locals = locals()
        nodes = unreal_lib.graph.filter_nodes(current_locals.values())
        node = unreal_lib.graph.comment_nodes(nodes, controller, 'Backward Solve')

        nodes.append(node)
        unreal_lib.graph.move_nodes(500, 1000, nodes, controller)


class UnrealGetTransform(UnrealUtilRig):

    def _build_function_graph(self):

        if not self.graph:
            return

        controller = self.function_controller

        count = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetNum(in Array,out Num)', unreal.Vector2D(-80, 100), 'DISPATCH_RigVMDispatch_ArrayGetNum')
        greater = controller.add_template_node('Greater::Execute(in A,in B,out Result)', unreal.Vector2D(150, 80), 'Greater')
        ifnode = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(450, 150), 'DISPATCH_RigVMDispatch_If')

        graph.add_link('Entry', 'transforms', count, 'Array', controller)
        graph.add_link(count, 'Num', greater, 'A', controller)
        controller.set_pin_default_value(f'{n(greater)}.B', '0', False)
        graph.add_link(greater, 'Result', ifnode, 'Condition', controller)

        at_data = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)',
                                                   unreal.Vector2D(-160, 240), 'DISPATCH_RigVMDispatch_ArrayGetAtIndex')

        make_array = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayMake(in Values,out Array)', unreal.Vector2D(0, 0), 'DISPATCH_RigVMDispatch_ArrayMake')

        graph.add_link('Entry', 'transforms', at_data, 'Array', controller)

        graph.add_link(at_data, 'Element', make_array, 'Values.0', controller)

        graph.add_link('Entry', 'index', at_data, 'Index', controller)

        graph.add_link(make_array, 'Array', ifnode, 'True', controller)
        graph.add_link(ifnode, 'Result', 'Return', 'transform', controller)

        graph.add_link('Entry', 'ExecuteContext', 'Return', 'ExecuteContext', controller)


class UnrealGetSubControls(UnrealUtilRig):

    def _build_function_graph(self):

        if not self.graph:
            return

        controller = self.function_controller

        control_count = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetNum(in Array,out Num)', unreal.Vector2D(-80, 100), 'DISPATCH_RigVMDispatch_ArrayGetNum')
        greater = controller.add_template_node('Greater::Execute(in A,in B,out Result)', unreal.Vector2D(150, 80), 'Greater')
        ifnode = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(450, 150), 'DISPATCH_RigVMDispatch_If')

        graph.add_link('Entry', 'controls', control_count, 'Array', controller)
        graph.add_link(control_count, 'Num', greater, 'A', controller)

        controller.set_pin_default_value(f'{n(greater)}.B', '0', False)

        graph.add_link(greater, 'Result', ifnode, 'Condition', controller)
        graph.add_link(ifnode, 'Result', 'Return', 'sub_controls', controller)

        at_controls = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)',
                                                   unreal.Vector2D(-160, 240), 'DISPATCH_RigVMDispatch_ArrayGetAtIndex')

        meta_data = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in Default,out Value,out Found)',
                                                unreal.Vector2D(100, 300), 'DISPATCH_RigDispatch_GetMetadata')

        graph.add_link('Entry', 'controls', at_controls, 'Array', controller)
        graph.add_link('Entry', 'control_index', at_controls, 'Index', controller)
        controller.set_pin_default_value(f'{n(meta_data)}.Name', 'Sub', False)
        graph.add_link(at_controls, 'Element', meta_data, 'Item', controller)

        graph.add_link(meta_data, 'Value', ifnode, 'True', controller)

        graph.add_link('Entry', 'ExecuteContext', 'Return', 'ExecuteContext', controller)
