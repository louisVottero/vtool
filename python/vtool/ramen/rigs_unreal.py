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
    if unreal_node is None:
        return
    return unreal_node.get_node_path()


class UnrealUtil(rigs.PlatformUtilRig):

    def __init__(self):
        super(UnrealUtil, self).__init__()

        self.layer = 0

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

        self.library_functions = {}
        self._cached_library_function_names = ['vetalaLib_Control',
                                               'vetalaLib_ControlSub',
                                               'vetalaLib_GetJointDescription',
                                               'vetalaLib_GetParent',
                                               'vetalaLib_GetItem',
                                               'vetalaLib_ConstructName',
                                               'vetalaLib_WheelRotate',
                                               'vetalaLib_SwitchMode',
                                               'vetalaLib_rigLayerSolve',
                                               'vetalaLib_findBoneAimAxis',
                                               'vetalaLib_findPoleAxis',
                                               'vetalaLib_MirrorTransform',
                                               'vetalaLib_ZeroOutTransform',
                                               'vetalaLib_Parent'
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
            return True
        if not found:
            return False

    def _init_rig_use_attributes(self):

        self.function_controller.add_exposed_pin('uuid', unreal.RigVMPinDirection.INPUT, 'FString', 'None', '')

    def _init_rig_function(self):
        if not self.graph:
            return

        self.function = self.controller.add_function_to_library(self._function_name, True, unreal.Vector2D(0, 0))
        self.function_controller = self.graph.get_controller_by_name(n(self.function))

        self._init_rig_use_attributes()

        self._initialize_attributes()

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

        self._fix_control_node()
        self._fix_parent_node()

    def _fix_control_node(self):
        control_node = self.library_functions['vetalaLib_Control']

        controller = self.graph.get_controller_by_name(n(control_node))

        nodes = controller.get_graph().get_nodes()

        nodes_to_check = ['vetalaLib_ConstructName',
                          'vetalaLib_ControlSub',
                          'vetalaLib_Control',
                          'vetalaLib_MirrorTransform']
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

                    controller.add_link('DISPATCH_RigDispatch_SetMetadata.ExecuteContext', 'VariableNode_5.ExecuteContext')
                    controller.add_link('VariableNode_5.ExecuteContext', 'Return.ExecuteContext')
                    # controller.add_link('DISPATCH_RigVMDispatch_If.Result', 'vetalaLib_ConstructName.Number')

                    controller.add_link('DISPATCH_RigDispatch_SetMetadata.ExecuteContext', 'VariableNode_5.ExecuteContext')
                    controller.add_link('VariableNode_5.ExecuteContext', 'Return.ExecuteContext')

                if check == 'vetalaLib_ControlSub':
                    node = controller.add_function_reference_node(function, unreal.Vector2D(2100, 100), n(function))
                    controller.add_link('SpawnControl.Item', f'{n(node)}.control')
                    controller.add_link('SpawnControl.ExecuteContext', f'{n(node)}.ExecuteContext')
                    controller.add_link('VariableNode_4.Value', f'{n(node)}.sub_count')

                    controller.add_link(f'{n(node)}.ExecuteContext', 'Return.ExecuteContext')
                    controller.add_link(f'{n(node)}.LastSubControl', 'Return.Last Control')

                if check == 'vetalaLib_MirrorTransform':
                    controller.add_function_reference_node(self.library.find_function('vetalaLib_MirrorTransform'), unreal.Vector2D(750, -700), 'vetalaLib_MirrorTransform')
                    controller.add_link('DISPATCH_RigVMDispatch_If_2.Result', 'vetalaLib_MirrorTransform.Transform')
                    controller.add_link('vetalaLib_MirrorTransform.MirrorTransform', 'DISPATCH_RigVMDispatch_If_3.True')

    def _fix_parent_node(self):

        parent_node = self.library_functions['vetalaLib_Parent']

        controller = self.graph.get_controller_by_name(n(parent_node))

        nodes = controller.get_graph().get_nodes()

        nodes_to_check = ['vetalaLib_ZeroOutTransform']

        for check in nodes_to_check:
            found = False
            for node in nodes:
                if node.get_node_title() == check:
                    found = True

            if not found:
                function = self.library_functions[check]

                if check == 'vetalaLib_ZeroOutTransform':
                    zero_out = controller.add_function_reference_node(function, unreal.Vector2D(560, 0), n(function))

                    graph.add_link('SetDefaultParent', 'ExecuteContext', zero_out, 'ExecuteContext', controller)
                    graph.add_link(zero_out, 'ExecuteContext', 'Return', 'ExecuteContext', controller)
                    controller.add_link('Entry.Child', 'vetalaLib_ZeroOutTransform.Argument')

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

    def _add_transform_array_in(self, name, value):
        transform_pin = self.function_controller.add_exposed_pin(name, unreal.RigVMPinDirection.INPUT,
                                                                 'TArray<FRigElementKey>',
                                                                 '/Script/ControlRig.RigElementKey', '')

        # self.function_controller.insert_array_pin('%s.%s' % (self.function.get_name(),transform_pin), -1, '')

    def _add_vector_array_in(self, name, value):
        pin = self.function_controller.add_exposed_pin(name, unreal.RigVMPinDirection.INPUT, 'TArray<FVector>',
                                                       '/Script/CoreUObject.Vector', '()')

    def _add_transform_array_out(self, name):
        transform_pin = self.function_controller.add_exposed_pin(name, unreal.RigVMPinDirection.OUTPUT,
                                                                 'TArray<FRigElementKey>',
                                                                 '/Script/ControlRig.RigElementKey', '')
        # self.function_controller.insert_array_pin('%s.%s' % (self.function.get_name(),transform_pin), -1, '')

    def _initialize_input(self, name):

        value, attr_type = super(UnrealUtil, self)._initialize_input(name)

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
            self._add_transform_array_in(name, value)

        if attr_type == rigs.AttrType.VECTOR:
            self._add_vector_array_in(name, value)

    def _initialize_node_attribute(self, name):
        value, attr_type = super(UnrealUtil, self)._initialize_node_attribute(name)

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
            self._add_transform_array_in(name, value)

        if attr_type == rigs.AttrType.VECTOR:
            self._add_vector_array_in(name, value)

    def _initialize_output(self, name):
        value, attr_type = super(UnrealUtil, self)._initialize_output(name)

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

        self.construct_controller.set_pin_default_value('%s.uuid' % function_node.get_node_path(), self.rig.uuid, False)

    def _add_forward_node_to_graph(self):

        controller = self.forward_controller

        function_node = controller.add_function_reference_node(self.function, unreal.Vector2D(100, 100),
                                                               self.function.get_node_path())
        self.forward_node = function_node

        controller.set_pin_default_value(f'{n(function_node)}.uuid', self.rig.uuid, False)

    def _add_backward_node_to_graph(self):

        controller = self.backward_controller

        function_node = controller.add_function_reference_node(self.function, unreal.Vector2D(100, 100),
                                                               self.function.get_node_path())
        self.backward_node = function_node

        controller.set_pin_default_value(f'{n(function_node)}.uuid', self.rig.uuid, False)

    def add_library_node(self, name, controller, x, y):
        node = self.library_functions[name]
        added_node = controller.add_function_reference_node(node,
                                                         unreal.Vector2D(x, y),
                                                         n(node))

        return added_node

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
        if not self.construct_node or not n(self.construct_node):
            self.build()
            return

        construct_pin = f'{n(self.construct_node)}.{name}'
        forward_pin = f'{n(self.forward_node)}.{name}'
        backward_pin = f'{n(self.backward_node)}.{name}'
        controllers = [self.construct_controller, self.forward_controller, self.backward_controller]
        pins = [construct_pin, forward_pin, backward_pin]

        value, value_type = self.rig.attr.get(name, True)

        if custom_value:
            value = custom_value

        if value_type == rigs.AttrType.INT:
            value = str(value[0])
            for controller, pin in zip(controllers, pins):
                controller.set_pin_default_value(pin, value, False)

        if value_type == rigs.AttrType.BOOL:
            value = str(value)
            if value == '1':
                value = 'true'
            if value == '0':
                value = 'false'

            for controller, pin in zip(controllers, pins):
                controller.set_pin_default_value(pin, value, False)

        if value_type == rigs.AttrType.NUMBER:
            value = str(value[0])
            for controller, pin in zip(controllers, pins):
                controller.set_pin_default_value(pin, value, False)

        if value_type == rigs.AttrType.STRING:
            if value is None:
                value = ''
            else:
                value = value[0]

            self.construct_controller.set_pin_default_value('%s.%s' % (n(self.construct_node), name), value, False)

        if value_type == rigs.AttrType.COLOR:
            self._reset_array(name, value)

            if not value:
                return

            for controller, pin in zip(controllers, pins):
                for inc, color in enumerate(value):
                    controller.set_array_pin_size(pin, len(value))
                    self.construct_controller.set_pin_default_value(f'{pin}.{inc}.R', str(color[0]), True)
                    self.construct_controller.set_pin_default_value(f'{pin}.{inc}.G', str(color[1]), True)
                    self.construct_controller.set_pin_default_value(f'{pin}.{inc}.B', str(color[2]), True)
                    self.construct_controller.set_pin_default_value(f'{pin}.{inc}.A', str(color[3]), True)

        if value_type == rigs.AttrType.TRANSFORM:
            if not util.is_iterable(value):
                return

            self._reset_array(name, value)
            if not value:
                return

            elements = self.graph.hierarchy.get_all_keys()
            type_map = {
                        unreal.RigElementType.BONE: 'Bone',
                        unreal.RigElementType.CONTROL: 'Control',
                        unreal.RigElementType.NULL: 'Null'
                        }

            found = [[str(element.name), type_map.get(element.type, '')] for element in elements if str(element.name) in value]

            for controller, pin in zip(controllers, pins):
                controller.set_array_pin_size(pin, len(found))
                for inc, (name, type_name) in enumerate(found):
                    if not type_name:
                        continue
                    controller.set_pin_default_value(f'{pin}.{inc}.Type', type_name, False)
                    controller.set_pin_default_value(f'{pin}.{inc}.Name', name, False)

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

    def _create_control(self, controller, x=0, y=0):
        control_node = self.library_functions['vetalaLib_Control']
        control = controller.add_function_reference_node(control_node,
                                                         unreal.Vector2D(x, y),
                                                         n(control_node))

        controller.add_link('Entry.color', f'{n(control)}.color')

        controller.add_link('Entry.shape', f'{n(control)}.shape')
        controller.add_link('Entry.description', f'{n(control)}.description')
        controller.add_link('Entry.side', f'{n(control)}.side')
        controller.add_link('Entry.restrain_numbering', f'{n(control)}.restrain_numbering')

        if self.rig.attr.exists('joint_token'):
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

    def _build_function_graph(self):
        return

    def select_node(self):

        controllers = self.get_controllers()
        nodes = self.get_nodes()

        for node, controller in zip(nodes, controllers):
            if node:
                controller.select_node(node)

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

    def set_layer(self, int_value):
        return

    def remove_connections(self):

        nodes = (self.construct_node, self.forward_node, self.backward_node)
        controllers = self.get_controllers()

        for node, controller in zip(nodes, controllers):
            graph.break_all_links_to_node(node, controller)

    def is_valid(self):
        if self.rig.state == rigs.RigState.CREATED:
            if not self.forward_node or not self.construct_node or not self.backward_node:
                return False
        if self.rig.state == rigs.RigState.LOADED:
            if not self.graph:
                return False

        return True

    def is_built(self):
        if not self.graph:
            return False
        try:
            if self.forward_node is None or self.construct_node is None or self.backward_node is None:
                self.forward_node = None
                self.construct_node = None
                self.backward_node = None
                return False
            elif self.forward_node.get_graph() is None or self.construct_node.get_graph() is None or self.backward_node.get_graph() is None:
                self.forward_node = None
                self.construct_node = None
                self.backward_node = None
                return False
            else:
                return True
        except:
            return False

    def get_controllers(self):
        return [self.construct_controller, self.forward_controller, self.backward_controller]

    def get_nodes(self):
        return [self.construct_node, self.forward_node, self.backward_node]

    def get_graph_start_nodes(self):

        if not self.forward_controller:
            return

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
        super(UnrealUtil, self).load()

        if not self.graph:

            self.graph = unreal_lib.graph.get_current_control_rig()

            if not self.graph:
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
        super(UnrealUtil, self).build()

        if not in_unreal:
            return

        if not self.graph:
            util.warning('No control rig for Unreal rig')
            return

        graph.open_undo('build')

        if not self.is_built():

            self._init_graph()
            self._init_library()

            found = self._get_existing_rig_function()

            if not found:
                self._init_rig_function()
                self._build_function_graph()

            if not self.construct_node:
                self._add_construct_node_to_graph()

            if not self.forward_node:
                self._add_forward_node_to_graph()

            if not self.backward_node:
                self._add_backward_node_to_graph()

            if not self.construct_node:
                util.warning('No construct function for Unreal rig')
                graph.close_undo('build')
                return

        self.rig.state = rigs.RigState.CREATED

        for name in self.rig.attr.node:
            self._set_attr_on_function(name)
        for name in self.rig.attr.inputs:
            self._set_attr_on_function(name)

        graph.close_undo('build')

    def unbuild(self):
        super(UnrealUtil, self).unbuild()

    def delete(self):
        super(UnrealUtil, self).delete()
        if not self.graph:
            return

        if not self.construct_node:
            self.load()

        super(UnrealUtilRig, self).unbuild()

        if self.construct_node:
            self.construct_controller.remove_node_by_name(n(self.construct_node))
            self.construct_node = None

        if self.forward_node:
            self.forward_controller.remove_node_by_name(n(self.forward_node))
            self.forward_node = None

        if self.backward_node:
            self.backward_controller.remove_node_by_name(n(self.backward_node))
            self.backward_node = None

        self.rig.state = rigs.RigState.LOADED


class UnrealUtilRig(UnrealUtil):

    def set_layer(self, int_value):
        self.layer = int_value
        if self.is_built():
            controllers = self.get_controllers()
            nodes = self.get_nodes()

            for node, controller in zip(nodes, controllers):
                controller.set_pin_default_value(f'{n(node)}.layer', str(int_value), False)

    def _init_rig_use_attributes(self):
        super(UnrealUtilRig, self)._init_rig_use_attributes()

        self.function_controller.add_exposed_pin('mode', unreal.RigVMPinDirection.INPUT, 'int32', 'None', '')
        self.function_controller.add_exposed_pin('layer', unreal.RigVMPinDirection.INPUT, 'int32', 'None', '')
        self.function_controller.add_exposed_pin('switch', unreal.RigVMPinDirection.INPUT, 'int32', 'None', '')

    def _add_forward_node_to_graph(self):
        super(UnrealUtilRig, self)._add_forward_node_to_graph()

        self.forward_controller.set_pin_default_value(f'{n(self.forward_node)}.mode', '1', False)

    def _add_backward_node_to_graph(self):
        super(UnrealUtilRig, self)._add_backward_node_to_graph()

        self.backward_controller.set_pin_default_value(f'{n(self.backward_node)}.mode', '2', False)

    def _build_function_graph(self):
        if not self.graph:
            return

        self._build_solve_switches()
        self._build_function_construct_graph()
        self._build_function_forward_graph()
        self._build_function_backward_graph()

    def _build_solve_switches(self):
        controller = self.function_controller

        controller.add_local_variable_from_object_path('control_layer', 'FName',
                                                                     '', '')

        mode = controller.add_template_node('DISPATCH_RigVMDispatch_SwitchInt32(in Index)',
                                                            unreal.Vector2D(225, -160),
                                                            'DISPATCH_RigVMDispatch_SwitchInt32')
        controller.insert_array_pin(f'{n(mode)}.Cases', -1, '')
        controller.insert_array_pin(f'{n(mode)}.Cases', -1, '')

        switch_node = self.library_functions['vetalaLib_SwitchMode']
        switch = controller.add_function_reference_node(switch_node,
                                                        unreal.Vector2D(0, -30),
                                                        n(switch_node))

        graph.add_link('Entry', 'mode', switch, 'mode', controller)
        graph.add_link('Entry', 'layer', switch, 'layer', controller)
        graph.add_link('Entry', 'switch', switch, 'switch', controller)
        graph.add_link('Entry', 'joints', switch, 'joints', controller)

        graph.add_link(switch, 'Result', mode, 'Index', controller)

        concat = controller.add_template_node('Concat::Execute(in A,in B,out Result)', unreal.Vector2D(-250, -200), 'Concat')
        control_layer = controller.add_variable_node('control_layer', 'FName', None, False, '', unreal.Vector2D(-50, -180), 'VariableNode')
        graph.add_link(concat, 'Result', control_layer, 'Value', controller)

        int_to_name = controller.add_template_node('Int to Name::Execute(in Number,in PaddedSize,out Result)', unreal.Vector2D(-400, -200), 'Int to Name')
        graph.add_link(int_to_name, 'Result', concat, 'B', controller)
        graph.add_link('Entry', 'layer', int_to_name, 'Number', controller)
        controller.set_pin_default_value(f'{n(concat)}.A', 'Control_', False)

        graph.add_link('Entry', 'ExecuteContext', control_layer, 'ExecuteContext', controller)
        graph.add_link(control_layer, 'ExecuteContext', switch, 'ExecuteContext', controller)
        graph.add_link(switch, 'ExecuteContext', mode, 'ExecuteContext', controller)

        graph.add_link(mode, 'Completed', 'Return', 'ExecuteContext', controller)

        controller.set_node_position_by_name('Return', unreal.Vector2D(4000, 0))
        self.mode = mode

    def _build_function_construct_graph(self):
        return

    def _build_function_forward_graph(self):
        return

    def _build_function_backward_graph(self):
        return


class UnrealFkRig(UnrealUtilRig):

    def _build_function_construct_graph(self):
        controller = self.function_controller

        for_each = controller.add_template_node(
            'DISPATCH_RigVMDispatch_ArrayIterator(in Array,out Element,out Index,out Count,out Ratio)',
            unreal.Vector2D(1500, -1250), 'DISPATCH_RigVMDispatch_ArrayIterator')

        controller.add_link(f'{n(self.mode)}.Cases.0', f'{n(for_each)}.ExecuteContext')

        controller.add_link('Entry.joints', f'{n(for_each)}.Array')

        control = self._create_control(controller, 2500, -1300)

        parent_node = self.library_functions['vetalaLib_GetParent']
        parent = controller.add_function_reference_node(parent_node, unreal.Vector2D(1880, -1450), n(parent_node))

        control_layer = controller.add_variable_node('control_layer', 'FName', None, True, '', unreal.Vector2D(1830, -1150), 'VariableNode')
        graph.add_link(control_layer, 'Value', parent, 'control_layer', controller)

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
        graph.add_link(control_layer, 'Value', meta_data, 'Name', controller)
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
        controller = self.function_controller

        for_each = controller.add_template_node(
            'DISPATCH_RigVMDispatch_ArrayIterator(in Array,out Element,out Index,out Count,out Ratio)',
            unreal.Vector2D(850, 250), 'DISPATCH_RigVMDispatch_ArrayIterator')
        controller.add_link(f'{n(self.mode)}.Cases.1', f'{n(for_each)}.ExecuteContext')
        controller.add_link('Entry.joints', '%s.Array' % (for_each.get_node_path()))

        meta_data = controller.add_template_node(
            'DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in Default,out Value,out Found)',
            unreal.Vector2D(1250, 350), 'DISPATCH_RigDispatch_GetMetadata')
        controller.set_pin_default_value('%s.Name' % meta_data.get_node_path(), 'Control', False)
        controller.add_link('%s.Element' % for_each.get_node_path(),
                                          '%s.Item' % meta_data.get_node_path())

        control_layer = controller.add_variable_node('control_layer', 'FName', None, True, '', unreal.Vector2D(1050, 400), 'VariableNode')
        graph.add_link(control_layer, 'Value', meta_data, 'Name', controller)

        get_transform = controller.add_unit_node_from_struct_path(
            '/Script/ControlRig.RigUnit_GetTransform', 'Execute', unreal.Vector2D(1550, 350), 'GetTransform')
        controller.add_link('%s.Value' % meta_data.get_node_path(),
                                          '%s.Item' % get_transform.get_node_path())
        set_transform = controller.add_template_node(
            'Set Transform::Execute(in Item,in Space,in bInitial,in Value,in Weight,in bPropagateToChildren)',
            unreal.Vector2D(2000, 250), 'Set Transform')

        controller.add_link('%s.Transform' % get_transform.get_node_path(),
                                          '%s.Value' % set_transform.get_node_path())
        controller.add_link('%s.Element' % for_each.get_node_path(),
                                          '%s.Item' % set_transform.get_node_path())

        controller.add_link('%s.ExecuteContext' % for_each.get_node_path(),
                                          '%s.ExecuteContext' % set_transform.get_node_path())

        rig_layer_solve_node = self.library_functions['vetalaLib_rigLayerSolve']
        rig_layer_solve = controller.add_function_reference_node(rig_layer_solve_node, unreal.Vector2D(2500, 250), n(rig_layer_solve_node))
        graph.add_link(for_each, 'Completed', rig_layer_solve, 'ExecuteContext', controller)
        graph.add_link('Entry', 'joints', rig_layer_solve, 'Joints', controller)

        current_locals = locals()
        nodes = unreal_lib.graph.filter_nodes(current_locals.values())
        node = unreal_lib.graph.comment_nodes(nodes, controller, 'Forward Solve')

        nodes.append(node)
        unreal_lib.graph.move_nodes(500, 0, nodes, controller)

    def _build_function_backward_graph(self):
        controller = self.function_controller

        for_each = controller.add_template_node(
            'DISPATCH_RigVMDispatch_ArrayIterator(in Array,out Element,out Index,out Count,out Ratio)',
            unreal.Vector2D(850, 1250), 'DISPATCH_RigVMDispatch_ArrayIterator')
        controller.add_link(f'{n(self.mode)}.Cases.2', f'{n(for_each)}.ExecuteContext')
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

        control_layer = controller.add_variable_node('control_layer', 'FName', None, True, '', unreal.Vector2D(1050, 1400), 'VariableNode')
        graph.add_link(control_layer, 'Value', meta_data, 'Name', controller)

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

    def _build_controls(self, controller):

        for_each = controller.add_template_node(
            'DISPATCH_RigVMDispatch_ArrayIterator(in Array,out Element,out Index,out Count,out Ratio)',
            unreal.Vector2D(1500, -1250), 'DISPATCH_RigVMDispatch_ArrayIterator')

        controller.add_link(f'{n(self.mode)}.Cases.0', f'{n(for_each)}.ExecuteContext')

        controller.add_link('Entry.joints', f'{n(for_each)}.Array')

        control = self._create_control(controller, 2500, -1300)

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

        control_layer = controller.add_variable_node('control_layer', 'FName', None, True, '', unreal.Vector2D(1780, -1150), 'VariableNode')
        graph.add_link(control_layer, 'Value', parent, 'control_layer', controller)
        graph.add_link(control_layer, 'Value', meta_data, 'Name', controller)

        index_equals = controller.add_template_node('DISPATCH_RigVMDispatch_CoreEquals(in A,in B,out Result)',
                                                    unreal.Vector2D(1700, -1450), 'DISPATCH_RigVMDispatch_CoreEquals')
        controller.add_link(f'{n(for_each)}.Index', f'{n(index_equals)}.A')
        controller.add_link(f'{n(index_equals)}.Result', f'{n(parent)}.is_top_joint')
        controller.add_link(f'{n(for_each)}.Element', f'{n(parent)}.joint')
        controller.add_link('Entry.parent', f'{n(parent)}.default_parent')
        controller.add_link(f'{n(parent)}.Result', f'{n(control)}.parent')

        description = controller.add_variable_node('description', 'FString', None, True, '',
                                                   unreal.Vector2D(1500, -600), 'VariableNode_description')
        use_joint_name = controller.add_variable_node('use_joint_name', 'FString', None, True, '',
                                                      unreal.Vector2D(1500, -500), 'VariableNode_use_joint_name')
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

        world = controller.add_variable_node('world', 'bool', None, True, '', unreal.Vector2D(2000, -400), 'VariableNode')
        mirror = controller.add_variable_node('mirror', 'bool', None, True, '', unreal.Vector2D(2000, -300), 'VariableNode')

        graph.add_link(world, 'Value', control, 'world', controller)
        graph.add_link(mirror, 'Value', control, 'mirror', controller)

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

        self._for_each = for_each
        self._control = control

        current_locals = locals()
        nodes = unreal_lib.graph.filter_nodes(current_locals.values())

        return nodes

    def _build_pole_vector_control(self, controller):

        for_each = self._for_each
        control = self._control

        get_controls = self.function_controller.add_variable_node_from_object_path('local_controls', 'FRigElementKey',
                                                                                    '/Script/ControlRig.RigElementKey',
                                                                                    True, '()',
                                                                                    unreal.Vector2D(3100, -450),
                                                                                    'VariableNode_get_controls')

        pole_vector_shape = controller.add_variable_node('pole_vector_shape', 'FString', None, True, '',
                                                         unreal.Vector2D(3100, -1025), 'VariableNode_pole_vector_shape')

        pole_shape_string = controller.add_template_node('DISPATCH_RigDispatch_FromString(in String,out Result)', unreal.Vector2D(3300, -1000), 'DISPATCH_RigDispatch')

        pole_shape_exists = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_ShapeExists', 'Execute', unreal.Vector2D(3500, -1000), 'ShapeExists')
        if_shape_exists = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(3500, -1200), 'DISPATCH_RigVMDispatch_If_2')

        pole_shape_setting = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchySetShapeSettings', 'Execute', unreal.Vector2D(3700, -1100), 'HierarchySetShapeSettings')
        pole_parent = self.library_functions['vetalaLib_Parent']
        pole_parent = controller.add_function_reference_node(pole_parent, unreal.Vector2D(4100, -1000), n(pole_parent))

        btm_ik_parent = self.library_functions['vetalaLib_Parent']
        btm_ik_parent = controller.add_function_reference_node(btm_ik_parent, unreal.Vector2D(4400, -800),
                                                                   n(btm_ik_parent))

        color = controller.add_variable_node_from_object_path('color', 'TArray<FLinearColor>', '/Script/CoreUObject.LinearColor', True, '()', unreal.Vector2D(3100, -950), 'VariableNode_color')

        at_color = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(3400, -900), 'DISPATCH_RigVMDispatch_ArrayGetAtIndex_color')
        at_control_0 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(3400, -650), 'DISPATCH_RigVMDispatch_control_0')
        at_control_1 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(3400, -550), 'DISPATCH_RigVMDispatch_control_1')
        at_control_2 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(3400, -450), 'DISPATCH_RigVMDispatch_control_2')
        controller.set_pin_default_value(f'{n(at_control_0)}.Index', '0', False)
        controller.set_pin_default_value(f'{n(at_control_1)}.Index', '1', False)
        controller.set_pin_default_value(f'{n(at_control_2)}.Index', '2', False)

        scale = controller.add_variable_node_from_object_path('shape_scale', 'TArray<FVector>', '/Script/CoreUObject.Vector', True, '()', unreal.Vector2D(2700, -1100), 'VariableNode_shape_scale')
        scale_at = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(2850, -1100), 'DISPATCH_RigVMDispatch_ArrayGetAtIndex')
        scale_mult = controller.add_template_node('Multiply::Execute(in A,in B,out Result)', unreal.Vector2D(3000, -1100), 'Multiply')

        graph.add_link(get_controls, 'Value', 'Return', 'controls', controller)

        graph.add_link(for_each, 'Completed', pole_shape_setting, 'ExecuteContext', controller)
        graph.add_link(pole_vector_shape, 'Value', pole_shape_string, 'String', controller)
        graph.add_link(pole_shape_string, 'Result', pole_shape_exists, 'ShapeName', controller)
        graph.add_link(pole_shape_exists, 'Result', if_shape_exists, 'Condition', controller)
        graph.add_link(if_shape_exists, 'Result', pole_shape_setting, 'Settings.Name', controller)

        graph.add_link(pole_shape_string, 'Result', if_shape_exists, 'True', controller)
        controller.set_pin_default_value(f'{n(if_shape_exists)}.False', 'Sphere_Solid', False)

        graph.add_link(color, 'Value', at_color, 'Array', controller)
        graph.add_link(at_color, 'Element', pole_shape_setting, 'Settings.Color', controller)

        graph.add_link(scale, 'Value', scale_at, 'Array', controller)
        graph.add_link(scale_at, 'Element', scale_mult, 'A', controller)

        controller.set_pin_default_value(f'{n(scale_mult)}.B.X', '0.333', False)
        controller.set_pin_default_value(f'{n(scale_mult)}.B.Y', '0.333', False)
        controller.set_pin_default_value(f'{n(scale_mult)}.B.Z', '0.333', False)

        graph.add_link(scale_mult, 'Result', pole_shape_setting, 'Settings.Transform.Scale3D', controller)

        graph.add_link(get_controls, 'Value', at_control_0, 'Array', controller)
        graph.add_link(get_controls, 'Value', at_control_1, 'Array', controller)
        graph.add_link(get_controls, 'Value', at_control_2, 'Array', controller)

        graph.add_link(at_control_1, 'Element', pole_shape_setting, 'Item', controller)
        graph.add_link(at_control_1, 'Element', pole_parent, 'Child', controller)
        graph.add_link(at_control_2, 'Element', btm_ik_parent, 'Child', controller)

        graph.add_link(at_control_0, 'Element', pole_parent, 'Parent', controller)
        graph.add_link(at_control_0, 'Element', btm_ik_parent, 'Parent', controller)

        graph.add_link(pole_shape_setting, 'ExecuteContext', pole_parent, 'ExecuteContext', controller)
        graph.add_link(pole_parent, 'ExecuteContext', btm_ik_parent, 'ExecuteContext', controller)

        joints = controller.add_variable_node('joints', 'FString', None, True, '',
                                                   unreal.Vector2D(3500, -1400), 'VariableNode_joints')

        at_joint_0 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(3800, -1450), 'DISPATCH_RigVMDispatch_joint_0')
        at_joint_1 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(3800, -1350), 'DISPATCH_RigVMDispatch_joint_1')
        at_joint_2 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(3800, -1250), 'DISPATCH_RigVMDispatch_joint_2')
        controller.set_pin_default_value(f'{n(at_joint_0)}.Index', '0', False)
        controller.set_pin_default_value(f'{n(at_joint_1)}.Index', '1', False)
        controller.set_pin_default_value(f'{n(at_joint_2)}.Index', '2', False)
        graph.add_link(joints, 'Value', at_joint_0, 'Array', controller)
        graph.add_link(joints, 'Value', at_joint_1, 'Array', controller)
        graph.add_link(joints, 'Value', at_joint_2, 'Array', controller)

        pole_offset = controller.add_variable_node('pole_vector_offset', 'float', None, True, '', unreal.Vector2D(4400, -1250), 'VariableNode_pole_offset')
        calc_pole = controller.add_external_function_reference_node('/ControlRig/StandardFunctionLibrary/StandardFunctionLibrary.StandardFunctionLibrary_C', 'ComputePoleVector', unreal.Vector2D(5000, -1400), 'ComputePoleVector')
        transform_pole = controller.add_template_node('Set Transform::Execute(in Item,in Space,in bInitial,in Value,in Weight,in bPropagateToChildren)', unreal.Vector2D(5600, -1200), 'Set Transform')

        controller.set_pin_default_value(f'{n(calc_pole)}.Draw Transform', 'false', False)
        controller.set_pin_default_value(f'{n(transform_pole)}.bInitial', 'true', False)

        graph.add_link(at_joint_0, 'Element', calc_pole, 'Bone A', controller)
        graph.add_link(at_joint_1, 'Element', calc_pole, 'Bone B', controller)
        graph.add_link(at_joint_2, 'Element', calc_pole, 'Bone C', controller)

        graph.add_link(pole_offset, 'Value', calc_pole, 'OffsetFactor', controller)

        graph.add_link(calc_pole, 'Transform.Translation', transform_pole, 'Value', controller)

        graph.add_link(btm_ik_parent, 'ExecuteContext', calc_pole, 'ExecuteContext', controller)
        graph.add_link(calc_pole, 'ExecuteContext', transform_pole, 'ExecuteContext', controller)

        graph.add_link(at_control_1, 'Element', transform_pole, 'Item', controller)

        inc_greater = controller.add_template_node('Greater::Execute(in A,in B,out Result)', unreal.Vector2D(600, -1300), 'Greater')
        if_inc_greater = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(800, -1200), 'DISPATCH_RigVMDispatch_If')

        graph.add_link(for_each, 'Index', inc_greater, 'A', controller)
        controller.set_pin_default_value(f'{n(inc_greater)}.B', '1', False)

        graph.add_link(inc_greater, 'Result', if_inc_greater, 'Condition', controller)
        graph.add_link('Entry', 'sub_count', if_inc_greater, 'True', controller)
        graph.add_link(if_inc_greater, 'Result', control, 'sub_count', controller)

        current_locals = locals()
        nodes = unreal_lib.graph.filter_nodes(current_locals.values())

        return nodes

    def _build_function_construct_graph(self):
        controller = self.function_controller

        nodes = self._build_controls(controller)

        nodes += self._build_pole_vector_control(controller)

        nodes = list(set(nodes))

        node = unreal_lib.graph.comment_nodes(nodes, controller, 'Construction')
        nodes.append(node)
        unreal_lib.graph.move_nodes(500, -2000, nodes, controller)

    def _build_function_forward_graph(self):

        controller = self.function_controller

        at_joint_0 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(700, 350), 'DISPATCH_RigVMDispatch_joint_0')
        at_joint_1 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(700, 550), 'DISPATCH_RigVMDispatch_joint_1')
        at_joint_2 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(700, 750), 'DISPATCH_RigVMDispatch_joint_2')

        controller.set_pin_default_value(f'{n(at_joint_0)}.Index', '0', False)
        controller.set_pin_default_value(f'{n(at_joint_1)}.Index', '1', False)
        controller.set_pin_default_value(f'{n(at_joint_2)}.Index', '2', False)

        meta_1 = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in Default,out Value,out Found)', unreal.Vector2D(1000, 400), 'DISPATCH_RigDispatch_GetMetadata_1')
        meta_2 = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in Default,out Value,out Found)', unreal.Vector2D(1000, 600), 'DISPATCH_RigDispatch_GetMetadata_2')

        control_layer = controller.add_variable_node('control_layer', 'FName', None, True, '', unreal.Vector2D(800, 850), 'VariableNode')
        graph.add_link(control_layer, 'Value', meta_1, 'Name', controller)
        graph.add_link(control_layer, 'Value', meta_2, 'Name', controller)

        ik = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_TwoBoneIKSimplePerItem', 'Execute', unreal.Vector2D(2500, 500), 'TwoBoneIKSimplePerItem_1')

        controller.set_pin_expansion(f'{n(ik)}.EffectorItem', False)
        controller.set_pin_expansion(f'{n(ik)}.ItemB', False)
        controller.set_pin_expansion(f'{n(ik)}.ItemA', False)

        graph.add_link('Entry', 'joints', at_joint_0, 'Array', controller)
        graph.add_link('Entry', 'joints', at_joint_1, 'Array', controller)
        graph.add_link('Entry', 'joints', at_joint_2, 'Array', controller)

        graph.add_link(at_joint_0, 'Element', ik, 'ItemA', controller)
        graph.add_link(at_joint_1, 'Element', ik, 'ItemB', controller)
        graph.add_link(at_joint_2, 'Element', ik, 'EffectorItem', controller)

        graph.add_link(at_joint_1, 'Element', meta_1, 'Item', controller)
        graph.add_link(at_joint_2, 'Element', meta_2, 'Item', controller)

        controller.set_pin_default_value(f'{n(meta_1)}.Name', 'Control', False)
        controller.set_pin_default_value(f'{n(meta_2)}.Name', 'Control', False)

        get_pole_transform = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetTransform', 'Execute', unreal.Vector2D(1700, 500), 'GetTransform')

        graph.add_link(meta_1, 'Value', get_pole_transform, 'Item', controller)
        graph.add_link(get_pole_transform, 'Transform.Translation.', ik, 'PoleVector', controller)

        controller.set_pin_default_value(f'{n(ik)}.SecondaryAxis.X', '0.000000', False)
        controller.set_pin_default_value(f'{n(ik)}.SecondaryAxis.Y', '0.000000', False)
        controller.set_pin_default_value(f'{n(ik)}.SecondaryAxis.Z', '0.000000', False)

        bone_aim = self.library_functions['vetalaLib_findBoneAimAxis']
        controller.add_function_reference_node(bone_aim, unreal.Vector2D(1700, 100), n(bone_aim))

        graph.add_link(self.mode, 'Cases.1', bone_aim, 'ExecuteContext', controller)

        graph.add_link(at_joint_0, 'Element', bone_aim, 'Bone', controller)
        graph.add_link(bone_aim, 'Result', ik, 'PrimaryAxis', controller)

        draw_line = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_DebugLineNoSpace', 'Execute', unreal.Vector2D(2750, 100), 'RigVMFunction_DebugLineNoSpace')
        get_elbow_transform = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetTransform', 'Execute', unreal.Vector2D(1400, 500), 'GetTransform')

        graph.add_link(bone_aim, 'ExecuteContext', ik, 'ExecuteContext', controller)
        graph.add_link(ik, 'ExecuteContext', draw_line, 'ExecuteContext', controller)

        graph.add_link(at_joint_1, 'Element', get_elbow_transform, 'Item', controller)
        graph.add_link(get_elbow_transform, 'Transform.Translation', draw_line, 'A', controller)
        graph.add_link(get_pole_transform, 'Transform.Translation', draw_line, 'B', controller)

        controller.set_pin_default_value(f'{n(draw_line)}.Color.R', '0.05', False)
        controller.set_pin_default_value(f'{n(draw_line)}.Color.G', '0.05', False)
        controller.set_pin_default_value(f'{n(draw_line)}.Color.B', '0.05', False)

        project_parent = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_ProjectTransformToNewParent', 'Execute', unreal.Vector2D(1300, 800), 'ProjectTransformToNewParent')

        graph.add_link(at_joint_2, 'Element', project_parent, 'Child', controller)
        graph.add_link(meta_2, 'Value', project_parent, 'OldParent', controller)
        graph.add_link(meta_2, 'Value', project_parent, 'NewParent', controller)
        graph.add_link(project_parent, 'Transform', ik, 'Effector', controller)

        rig_layer_solve_node = self.library_functions['vetalaLib_rigLayerSolve']
        rig_layer_solve = controller.add_function_reference_node(rig_layer_solve_node, unreal.Vector2D(3000, 500), n(rig_layer_solve_node))
        graph.add_link(draw_line, 'ExecuteContext', rig_layer_solve, 'ExecuteContext', controller)
        graph.add_link('Entry', 'joints', rig_layer_solve, 'Joints', controller)

        current_locals = locals()
        nodes = unreal_lib.graph.filter_nodes(current_locals.values())
        node = unreal_lib.graph.comment_nodes(nodes, controller, 'Forward Solve')

        nodes.append(node)
        unreal_lib.graph.move_nodes(500, 0, nodes, controller)

    def _build_function_backward_graph(self):
        return


class UnrealSplineIkRig(UnrealUtilRig):

    def _build_function_construct_graph(self):

        controller = self.function_controller

        controller.add_local_variable_from_object_path('spline_controls',
                                                       'TArray<FRigElementKey>',
                                                       '/Script/ControlRig.RigElementKey', '')

        controller.add_local_variable_from_object_path('last_control', 'FRigElementKey', '/Script/ControlRig.RigElementKey', '')

        spline = controller.add_external_function_reference_node('/ControlRigSpline/SplineFunctionLibrary/SplineFunctionLibrary.SplineFunctionLibrary_C',
                                                        'SplineFromItems', unreal.Vector2D(1800, -2500),
                                                        'SplineFromItems')

        get_joints = controller.add_variable_node_from_object_path('joints', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()',
                                                                   unreal.Vector2D(1300, -760), 'VariableNode_joints')

        get_spline_controls = controller.add_variable_node_from_object_path('spline_controls', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()',
                                                                            unreal.Vector2D(1300, -2080), 'VariableNode_spline_controls')

        get_control_count = controller.add_variable_node('control_count', 'int32', None, True, '', unreal.Vector2D(1300, -1800), 'VariableNode_control_count')

        get_hierarchy = controller.add_variable_node('hierarchy', 'bool', None, True, '', unreal.Vector2D(1300, -1660), 'VariableNode_hierarchy')

        get_parent = controller.add_variable_node_from_object_path('parent', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()',
                                                                   unreal.Vector2D(1300, -1360), 'VariableNode_parent')

        get_last_control = controller.add_variable_node_from_object_path('last_control', 'FRigElementKey', '/Script/ControlRig.RigElementKey', True, '(Type=None,Name="None")',
                                                                         unreal.Vector2D(1300.039335, -1500), 'VariableNode_last_control')

        controller.add_link(f'{n(self.mode)}.Cases.0', f'{n(spline)}.ExecuteContext')
        controller.add_link(f'{n(get_joints)}.Value', f'{n(spline)}.Items')

        reset = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayReset(io Array)',
                                                unreal.Vector2D(2200, -2100),
                                                'DISPATCH_RigVMDispatch_ArrayReset')

        for_loop = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_ForLoopCount', 'Execute',
                                                             unreal.Vector2D(2500, -2000), 'RigVMFunction_ForLoopCount')

        controller.add_link(f'{n(spline)}.ExecuteContext', f'{n(reset)}.ExecuteContext')
        controller.add_link(f'{n(get_spline_controls)}.Value', f'{n(reset)}.Array')
        controller.add_link(f'{n(reset)}.ExecuteContext', f'{n(for_loop)}.ExecuteContext')

        control_count_greater = controller.add_template_node('Greater::Execute(in A,in B,out Result)',
                                                             unreal.Vector2D(1950, -1900), 'Greater')

        condition_count = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)',
                                                       unreal.Vector2D(2200, -1800), 'DISPATCH_RigVMDispatch_If')

        controller.add_link(f'{n(get_control_count)}.Value', f'{n(control_count_greater)}.A')
        controller.add_link(f'{n(get_control_count)}.Value', f'{n(condition_count)}.True')
        controller.add_link(f'{n(control_count_greater)}.Result', f'{n(condition_count)}.Condition')
        controller.add_link(f'{n(condition_count)}.Result', f'{n(for_loop)}.Count')

        controller.set_pin_default_value(f'{n(control_count_greater)}.B', '3', False)
        controller.set_pin_default_value(f'{n(condition_count)}.False', '4', False)

        parent_count = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetNum(in Array,out Num)',
                                                    unreal.Vector2D(2000, -1500), 'DISPATCH_RigVMDispatch_ArrayGetNum')
        parent_greater = controller.add_template_node('Greater::Execute(in A,in B,out Result)',
                                                      unreal.Vector2D(2200, -1500), 'Greater_parent')
        condition_parent = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)',
                                                        unreal.Vector2D(2500, -1400), 'DISPATCH_RigVMDispatch_If_parent')
        at_parent = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)',
                                                 unreal.Vector2D(2000, -1400), 'DISPATCH_RigVMDispatch_ArrayGetAtIndex_6')

        graph.add_link(get_parent, 'Value', parent_count, 'Array', controller)
        graph.add_link(get_parent, 'Value', at_parent, 'Array', controller)
        graph.add_link(parent_count, 'Num', parent_greater, 'A', controller)
        graph.add_link(parent_greater, 'Result', condition_parent, 'Condition', controller)
        graph.add_link(at_parent, 'Element', condition_parent, 'True', controller)

        index_equals = controller.add_template_node('DISPATCH_RigVMDispatch_CoreEquals(in A,in B,out Result)',
                                                    unreal.Vector2D(2700, -1800), 'DISPATCH_RigVMDispatch_CoreEquals')
        condition_first_inc = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)',
                                                           unreal.Vector2D(2900, -1650), 'DISPATCH_RigVMDispatch_If_first_inc')
        condition_hierarchy = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)',
                                                           unreal.Vector2D(3100, -1500), 'DISPATCH_RigVMDispatch_If_hierarchy')

        graph.add_link(for_loop, 'Index', index_equals, 'A', controller)
        graph.add_link(index_equals, 'Result', condition_first_inc, 'Condition', controller)
        graph.add_link(condition_first_inc, 'Condition', condition_hierarchy, 'True', controller)

        graph.add_link(get_last_control, 'Value', condition_first_inc, 'False', controller)
        graph.add_link(condition_parent, 'Result', condition_first_inc, 'True', controller)
        graph.add_link(condition_parent, 'Result', condition_hierarchy, 'False', controller)
        graph.add_link(get_hierarchy, 'Value', condition_hierarchy, 'Condition', controller)

        spline_u = controller.add_unit_node_from_struct_path('/Script/ControlRigSpline.RigUnit_PositionFromControlRigSpline', 'Execute',
                                                             unreal.Vector2D(3000, -2100), 'PositionFromControlRigSpline')

        make_transform = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathTransformMake', 'Execute',
                                                                   unreal.Vector2D(3300, -2100), 'RigVMFunction_MathTransformMake')

        null = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyAddNull', 'Execute',
                                                         unreal.Vector2D(3700, -2100), 'HierarchyAddNull')

        control = self._create_control(controller, 4600, -1850)

        graph.add_link(spline, 'Spline', spline_u, 'Spline', controller)
        graph.add_link(for_loop, 'Ratio', spline_u, 'U', controller)
        graph.add_link(spline_u, 'Position', make_transform, 'Translation', controller)
        graph.add_link(make_transform, 'Result', null, 'Transform', controller)
        graph.add_link(for_loop, 'ExecuteContext', null, 'ExecuteContext', controller)
        graph.add_link(null, 'ExecuteContext', control, 'ExecuteContext', controller)
        graph.add_link(null, 'Item', control, 'driven', controller)
        graph.add_link(for_loop, 'Index', control, 'increment', controller)
        graph.add_link(condition_hierarchy, 'Result', control, 'parent', controller)
        graph.add_link(condition_first_inc, 'Result', condition_hierarchy, 'True', controller)

        null_parent = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_SetDefaultParent', 'Execute', unreal.Vector2D(5000, -2300), 'SetDefaultParent')
        set_last_control = controller.add_variable_node_from_object_path('last_control', 'FRigElementKey', '/Script/ControlRig.RigElementKey', False, '(Type=None,Name="None")',
                                                                         unreal.Vector2D(5400, -1700), 'VariableNode_set_last_control')
        get_spline_controls = controller.add_variable_node_from_object_path('spline_controls', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()',
                                                                            unreal.Vector2D(5400, -1400), 'VariableNode_spline_controls')

        at_joint = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)',
                                                unreal.Vector2D(5400, -760), 'DISPATCH_RigVMDispatch_ArrayGetAtIndex_first_joint')
        add = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayAdd(io Array,in Element,out Index)',
                                           unreal.Vector2D(6000, -1400), 'DISPATCH_RigVMDispatch_ArrayAdd')
        set_meta = controller.add_template_node('DISPATCH_RigDispatch_SetMetadata(in Item,in Name,in Value,out Success)',
                                                unreal.Vector2D(6500, -1100), 'DISPATCH_RigDispatch_SetMetadata')
        at_control = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)',
                                                  unreal.Vector2D(6800, -1400), 'DISPATCH_RigVMDispatch_ArrayGetAtIndex_first_control')

        attr_bool = graph.add_animation_channel(controller, 'stretch', 7100, -1100)
        # attr_bool = controller.add_template_node('SpawnAnimationChannel::Execute(in InitialValue,in MinimumValue,in MaximumValue,in Parent,in Name,out Item)',
        #                                         unreal.Vector2D(7100, -1100), 'SpawnAnimationChannel')

        graph.add_link(control, 'ExecuteContext', null_parent, 'ExecuteContext', controller)
        graph.add_link(null, 'Item', null_parent, 'Child', controller)
        graph.add_link(control, 'Control', null_parent, 'Parent', controller)
        graph.add_link(null_parent, 'ExecuteContext', set_last_control, 'ExecuteContext', controller)
        graph.add_link(control, 'Control', set_last_control, 'Value', controller)
        graph.add_link(set_last_control, 'ExecuteContext', add, 'ExecuteContext', controller)
        graph.add_link(control, 'Control', add, 'Element', controller)
        graph.add_link(get_joints, 'Value', at_joint, 'Array', controller)
        graph.add_link(at_joint, 'Element', set_meta, 'Item', controller)
        graph.add_link(for_loop, 'Completed', set_meta, 'ExecuteContext', controller)
        graph.add_link(get_spline_controls, 'Value', add, 'Array', controller)
        graph.add_link(add, 'Array', set_meta, 'Value', controller)
        graph.add_link(add, 'Array', at_control, 'Array', controller)
        graph.add_link(at_control, 'Element', attr_bool, 'Parent', controller)
        graph.add_link(set_meta, 'ExecuteContext', attr_bool, 'ExecuteContext', controller)

        controller.resolve_wild_card_pin(f'{n(attr_bool)}.InitialValue', 'bool', unreal.Name())

        controller.set_pin_default_value(f'{n(set_meta)}.Name', 'controls', False)
        controller.set_pin_default_value(f'{n(attr_bool)}.InitialValue', 'true', False)

        current_locals = locals()
        nodes = unreal_lib.graph.filter_nodes(current_locals.values())
        node = unreal_lib.graph.comment_nodes(nodes, controller, 'Construction')

        nodes.append(node)
        unreal_lib.graph.move_nodes(1000, -3000, nodes, controller)

    def _build_function_forward_graph(self):
        controller = self.function_controller

        get_joints = controller.add_variable_node_from_object_path('joints', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()',
                                                                   unreal.Vector2D(700, 400), 'VariableNode_forward_joints')

        spline_ik = controller.add_external_function_reference_node('/ControlRigSpline/SplineFunctionLibrary/SplineFunctionLibrary.SplineFunctionLibrary_C', 'SplineIK',
                                                                    unreal.Vector2D(2500, 400), 'SplineIK')

        at_joint = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)',
                                                unreal.Vector2D(800, 700), 'DISPATCH_RigVMDispatch_ArrayGetAtIndex_forward_first_joint')

        at_meta_control = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)',
                                                       unreal.Vector2D(1300, 700), 'DISPATCH_RigVMDispatch_ArrayGetAtIndex_first_meta_control')

        get_meta = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in Default,out Value,out Found)',
                                                unreal.Vector2D(1000, 700), 'DISPATCH_RigDispatch_GetMetadata')
        controller.set_pin_default_value(f'{n(get_meta)}.Name', 'controls', False)
        graph.add_link(get_joints, 'Value', get_meta, 'Default', controller)
        graph.break_link(get_joints, 'Value', get_meta, 'Default', controller)

        get_bool = controller.add_template_node('GetAnimationChannel::Execute(out Value,in Control,in Channel,in bInitial)',
                                                unreal.Vector2D(1600, 700), 'GetAnimationChannel')

        graph.add_link(get_joints, 'Value', spline_ik, 'Bones', controller)
        graph.add_link(get_joints, 'Value', at_joint, 'Array', controller)
        graph.add_link(at_joint, 'Element', get_meta, 'Item', controller)
        graph.add_link(get_meta, 'Value', at_meta_control, 'Array', controller)
        graph.add_link(at_meta_control, 'Element.Name', get_bool, 'Control', controller)
        graph.add_link(get_bool, 'Value', spline_ik, 'Stretch', controller)

        controller.set_pin_default_value(f'{n(get_bool)}.Channel', 'stretch', False)

        reset = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayReset(io Array)',
                                            unreal.Vector2D(800, 900), 'DISPATCH_RigVMDispatch_ArrayReset_sub_controls')

        graph.add_link(get_joints, 'Value', reset, 'Array', controller)
        graph.break_link(get_joints, 'Value', reset, 'Array', controller)

        for_each = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayIterator(in Array,out Element,out Index,out Count,out Ratio)',
                                                unreal.Vector2D(1200, 900), 'DISPATCH_RigVMDispatch_ArrayIterator')

        add = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayAdd(io Array,in Element,out Index)',
                                           unreal.Vector2D(1900, 900), 'DISPATCH_RigVMDispatch_ArrayAdd_sub_controls')

        get_meta_sub = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in Default,out Value,out Found)',
                                                unreal.Vector2D(1400, 1100), 'DISPATCH_RigDispatch_GetMetadata_sub')
        controller.set_pin_default_value(f'{n(get_meta_sub)}.Name', 'Sub', False)
        graph.add_link(get_joints, 'Value', get_meta_sub, 'Default', controller)
        graph.break_link(get_joints, 'Value', get_meta_sub, 'Default', controller)

        sub_count = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetNum(in Array,out Num)', unreal.Vector2D(1400, 1300), 'DISPATCH_RigVMDispatch_ArrayGetNum')

        sub_greater = controller.add_template_node('Greater::Execute(in A,in B,out Result)',
                                                    unreal.Vector2D(1600, 1300), 'Greater_sub')
        at_sub = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)',
                                              unreal.Vector2D(1700, 1100), 'DISPATCH_RigVMDispatch_ArrayGetAtIndex_first_meta_control')
        condition_sub = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)',
                                                    unreal.Vector2D(1800, 1300), 'DISPATCH_RigVMDispatch_If_sub')

        get_aim = controller.add_variable_node_from_object_path('aim_axis', 'TArray<FVector>', '/Script/CoreUObject.Vector', True, '()',
                                                                unreal.Vector2D(2100, 600), 'VariableNode_forward_joints')
        at_aim = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)',
                                              unreal.Vector2D(2250, 600), 'DISPATCH_RigVMDispatch_ArrayGetAtIndex_aim')
        get_up = controller.add_variable_node_from_object_path('up_axis', 'TArray<FVector>', '/Script/CoreUObject.Vector', True, '()',
                                                                unreal.Vector2D(2100, 700), 'VariableNode_forward_joints')
        at_up = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)',
                                              unreal.Vector2D(2250, 700), 'DISPATCH_RigVMDispatch_ArrayGetAtIndex_up')

        graph.add_link(self.mode, 'Cases.1', reset, 'ExecuteContext', controller)
        graph.add_link(reset, 'ExecuteContext', for_each, 'ExecuteContext', controller)
        graph.add_link(for_each, 'ExecuteContext', add, 'ExecuteContext', controller)
        graph.add_link(for_each, 'Completed', spline_ik, 'ExecuteContext', controller)

        graph.add_link(get_meta, 'Value', for_each, 'Array', controller)

        graph.add_link(reset, 'Array', add, 'Array', controller)
        graph.add_link(for_each, 'Element', get_meta_sub, 'Item', controller)

        graph.add_link(get_meta_sub, 'Value', at_sub, 'Array', controller)
        graph.add_link(get_meta_sub, 'Value', sub_count, 'Array', controller)
        graph.add_link(sub_count, 'Num', sub_greater, 'A', controller)
        graph.add_link(sub_greater, 'Result', condition_sub, 'Condition', controller)
        graph.add_link(at_sub, 'Element', condition_sub, 'True', controller)
        graph.add_link(for_each, 'Element', condition_sub, 'False', controller)
        graph.add_link(condition_sub, 'Result', add, 'Element', controller)

        graph.add_link(add, 'Array', spline_ik, 'Controls', controller)

        graph.add_link(get_aim, 'Value', at_aim, 'Array', controller)
        graph.add_link(at_aim, 'Element', spline_ik, 'Primary Axis', controller)

        graph.add_link(get_up, 'Value', at_up, 'Array', controller)
        graph.add_link(at_up, 'Element', spline_ik, 'Up Axis', controller)

        controller.set_pin_default_value(f'{n(at_sub)}.Index', '-1', False)

        controller.add_exposed_pin('Secondary Spline Direction', unreal.RigVMPinDirection.INPUT, 'FVector', '/Script/CoreUObject.Vector', '(X=0.000000,Y=5.0,Z=0.000000)')
        graph.add_link('Entry', 'Secondary Spline Direction', spline_ik, 'Secondary Spline Direction', controller)

        current_locals = locals()
        nodes = unreal_lib.graph.filter_nodes(current_locals.values())
        node = unreal_lib.graph.comment_nodes(nodes, controller, 'Forward Solve')

        nodes.append(node)
        unreal_lib.graph.move_nodes(500, 0, nodes, controller)

    def _build_function_backward_graph(self):
        return


class UnrealFootRollRig(UnrealUtilRig):

    def _build_controls(self, controller):

        for_each = controller.add_template_node(
            'DISPATCH_RigVMDispatch_ArrayIterator(in Array,out Element,out Index,out Count,out Ratio)',
            unreal.Vector2D(1500, -1250), 'DISPATCH_RigVMDispatch_ArrayIterator')

        controller.add_link(f'{n(self.mode)}.Cases.0', f'{n(for_each)}.ExecuteContext')

        controller.add_link('Entry.joints', f'{n(for_each)}.Array')

        control = self._create_control(controller, 2500, -1300)

        parent_node = self.library_functions['vetalaLib_GetParent']
        parent = controller.add_function_reference_node(parent_node, unreal.Vector2D(1880, -1450), n(parent_node))

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

        control_layer = controller.add_variable_node('control_layer', 'FName', None, True, '', unreal.Vector2D(1780, -1150), 'VariableNode')
        graph.add_link(control_layer, 'Value', parent, 'control_layer', controller)
        graph.add_link(control_layer, 'Value', meta_data, 'Name', controller)

        index_equals = controller.add_template_node('DISPATCH_RigVMDispatch_CoreEquals(in A,in B,out Result)',
                                                    unreal.Vector2D(1700, -1450), 'DISPATCH_RigVMDispatch_CoreEquals')
        controller.add_link(f'{n(for_each)}.Index', f'{n(index_equals)}.A')
        controller.add_link(f'{n(index_equals)}.Result', f'{n(parent)}.is_top_joint')
        controller.add_link(f'{n(for_each)}.Element', f'{n(parent)}.joint')
        controller.add_link('Entry.parent', f'{n(parent)}.default_parent')
        controller.add_link(f'{n(parent)}.Result', f'{n(control)}.parent')

        description = controller.add_variable_node('description', 'FString', None, True, '',
                                                   unreal.Vector2D(1500, -600), 'VariableNode_description')

        graph.add_link(for_each, 'ExecuteContext', control, 'ExecuteContext', controller)
        graph.add_link(description, 'Value', control, 'description', controller)

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

        self._for_each = for_each
        self._control = control

        current_locals = locals()
        nodes = unreal_lib.graph.filter_nodes(current_locals.values())

        return nodes

    def _build_function_construct_graph(self):
        controller = self.function_controller

        nodes = self._build_controls(controller)

        nodes = list(set(nodes))

        node = unreal_lib.graph.comment_nodes(nodes, controller, 'Construction')
        nodes.append(node)
        unreal_lib.graph.move_nodes(500, -2000, nodes, controller)

    def _build_function_forward_graph(self):
        return

    def _build_function_backward_graph(self):
        return


class UnrealIkQuadurpedRig(UnrealUtilRig):
    pass


class UnrealWheelRig(UnrealUtilRig):

    def _build_function_construct_graph(self):
        controller = self.function_controller

        control = self._create_control(controller, 2500, -1300)
        graph.add_link(self.mode, 'Cases.0', control, 'ExecuteContext', controller)

        control_spin = self._create_control(controller)

        controller.set_node_position(control_spin, unreal.Vector2D(2900, -800.000000))

        joints = controller.add_variable_node_from_object_path('joints', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(2000, -800), 'VariableNode')

        get_joint_num = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetNum(in Array,out Num)', unreal.Vector2D(2500, -800), 'DISPATCH_RigVMDispatch_ArrayGetNum')
        joint_num_equals = controller.add_template_node('DISPATCH_RigVMDispatch_CoreEquals(in A,in B,out Result)', unreal.Vector2D(2600, -800), 'DISPATCH_RigVMDispatch_CoreEquals')
        joint_branch = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_ControlFlowBranch', 'Execute', unreal.Vector2D(2700, -800), 'RigVMFunction_ControlFlowBranch')

        graph.add_link(control, 'ExecuteContext', joint_branch, 'Execute', controller)
        graph.add_link(joints, 'Value', get_joint_num, 'Array', controller)
        graph.add_link(get_joint_num, 'Num', joint_num_equals, 'A', controller)
        graph.add_link(joint_num_equals, 'Result', joint_branch, 'Condition')
        graph.add_link(joint_branch, 'False', control_spin, 'ExecuteContext', controller)

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

        at_parent = self.add_library_node('vetalaLib_GetItem', controller, 2200, -1000)
        controller.set_pin_default_value(f'{n(at_parent)}.index', '-1', False)

        graph.add_link(parent, 'Value', at_parent, 'Array', controller)
        graph.add_link(at_parent, 'Element', control, 'parent', controller)

        at_joints = self.add_library_node('vetalaLib_GetItem', controller, 2200, -800)

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
        channel_diameter = graph.add_animation_channel(controller, 'Diameter', 3500, -1200)
        graph.add_link(joint_metadata, 'ExecuteContext', channel_diameter, 'ExecuteContext', controller)
        graph.add_link(control, 'Control', channel_diameter, 'Parent', controller)

        controller.resolve_wild_card_pin(f'{n(channel_diameter)}.InitialValue', 'float', unreal.Name())
        controller.set_pin_default_value(f'{n(channel_diameter)}.MaximumValue', '1000000000000.0', False)
        controller.set_pin_default_value(f'{n(channel_diameter)}.InitialValue', '9.888', False)

        channel_enable = graph.add_animation_channel(controller, 'Enable', 3500, -1000)
        graph.add_link(channel_diameter, 'ExecuteContext', channel_enable, 'ExecuteContext', controller)
        graph.add_link(control, 'Control', channel_enable, 'Parent', controller)

        controller.resolve_wild_card_pin(f'{n(channel_enable)}.InitialValue', 'float', unreal.Name())
        controller.set_pin_default_value(f'{n(channel_enable)}.InitialValue', '1.0', False)

        channel_multiply = graph.add_animation_channel(controller, 'RotateMultiply', 3500, -800)
        graph.add_link(channel_enable, 'ExecuteContext', channel_multiply, 'ExecuteContext', controller)
        graph.add_link(control, 'Control', channel_multiply, 'Parent', controller)

        controller.resolve_wild_card_pin(f'{n(channel_multiply)}.InitialValue', 'float', unreal.Name())
        controller.set_pin_default_value(f'{n(channel_multiply)}.InitialValue', '1.0', False)

        wheel_diameter = controller.add_variable_node('wheel_diameter', 'float', None, True, '', unreal.Vector2D(3200, -600), 'VariableNode')
        graph.add_link(wheel_diameter, 'Value', channel_diameter, 'InitialValue', controller)

        steer_array = controller.add_variable_node_from_object_path('steer_control', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(3000, -200), 'VariableNode')
        at_steers = self.add_library_node('vetalaLib_GetItem', controller, 3250, -200)
        steer_metadata = controller.add_template_node('DISPATCH_RigDispatch_SetMetadata(in Item,in Name,in Value,out Success)', unreal.Vector2D(3500, -200), 'DISPATCH_RigDispatch_SetMetadata')

        controller.set_pin_default_value(f'{n(steer_metadata)}.Name', 'Steer', False)

        graph.add_link(channel_multiply, 'ExecuteContext', steer_metadata, 'ExecuteContext', controller)
        graph.add_link(control_spin, 'Control', steer_metadata, 'Item', controller)
        graph.add_link(steer_array, 'Value', at_steers, 'Array', controller)
        graph.add_link(at_steers, 'Element', steer_metadata, 'Value', controller)

        current_locals = locals()
        nodes = unreal_lib.graph.filter_nodes(current_locals.values())
        node = unreal_lib.graph.comment_nodes(nodes, controller, 'Construction')

        nodes.append(node)
        unreal_lib.graph.move_nodes(500, -2000, nodes, controller)

    def _build_function_forward_graph(self):
        controller = self.function_controller

        joints = controller.add_variable_node_from_object_path('joints', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(500, 0), 'VariableNode')

        at_joints = self.add_library_node('vetalaLib_GetItem', controller, 700, 0)

        graph.add_link(joints, 'Value', at_joints, 'Array', controller)

        meta_data = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in Default,out Value,out Found)', unreal.Vector2D(900, 0), 'DISPATCH_RigDispatch_GetMetadata')
        controller.set_pin_default_value(f'{n(meta_data)}.Name', 'Control', False)
        graph.add_link(at_joints, 'Element', meta_data, 'Item', controller)

        get_parent = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyGetParent', 'Execute', unreal.Vector2D(1200, 0), 'HierarchyGetParent')
        graph.add_link(meta_data, 'Value', get_parent, 'Child', controller)

        get_transform = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetTransform', 'Execute', unreal.Vector2D(2000, 500), 'GetTransform')
        set_transform = controller.add_template_node('Set Transform::Execute(in Item,in Space,in bInitial,in Value,in Weight,in bPropagateToChildren)', unreal.Vector2D(2500, 300), 'Set Transform')

        graph.add_link(meta_data, 'Value', get_transform, 'Item', controller)
        graph.add_link(at_joints, 'Element', set_transform, 'Item', controller)
        graph.add_link(get_transform, 'Transform', set_transform, 'Value', controller)

        wheel_rotate = self.library_functions['vetalaLib_WheelRotate']
        wheel_rotate = controller.add_function_reference_node(wheel_rotate,
                                                         unreal.Vector2D(1900, 0),
                                                         n(wheel_rotate))

        graph.add_link(self.mode, 'Cases.1', wheel_rotate, 'ExecuteContext', controller)
        graph.add_link(wheel_rotate, 'ExecuteContext', set_transform, 'ExecuteContext', controller)

        graph.add_link(set_transform, 'ExecuteContext', wheel_rotate, 'ExecuteContext', controller)
        graph.add_link(meta_data, 'Value', wheel_rotate, 'control_spin', controller)
        graph.add_link(get_parent, 'Parent', wheel_rotate, 'control', controller)

        controller.set_pin_default_value(f'{n(wheel_rotate)}.Diameter', '9.888', False)
        controller.set_pin_default_value(f'{n(wheel_rotate)}.Enable', '1.0', False)
        controller.set_pin_default_value(f'{n(wheel_rotate)}.RotateMultiply', '1.0', False)

        at_forward = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(1700, 600), 'DISPATCH_RigVMDispatch_ArrayGetAtIndex')
        at_rotate = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(1700, 800), 'DISPATCH_RigVMDispatch_ArrayGetAtIndex')

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

        channel_diameter = controller.add_template_node('GetAnimationChannel::Execute(out Value,in Control,in Channel,in bInitial)', unreal.Vector2D(1200, 750), 'GetAnimationChannel')
        graph.add_link(get_parent, 'Parent.Name', channel_diameter, 'Control', controller)
        controller.set_pin_default_value(f'{n(channel_diameter)}.Channel', 'Diameter', False)
        graph.add_link(channel_diameter, 'Value', wheel_rotate, 'Diameter', controller)

        steer_meta_data = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in Default,out Value,out Found)', unreal.Vector2D(800, 1000), 'DISPATCH_RigDispatch_GetMetadata')
        controller.set_pin_default_value(f'{n(steer_meta_data)}.Name', 'Steer', False)
        get_steer_transform = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetTransform', 'Execute', unreal.Vector2D(1100, 1000), 'GetTransform')
        controller.set_pin_default_value(f'{n(get_steer_transform)}.Space', 'LocalSpace', False)
        at_steer_axis = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(1100, 1300), 'DISPATCH_RigVMDispatch_ArrayGetAtIndex')

        to_euler = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathQuaternionToEuler', 'Execute', unreal.Vector2D(1400, 1000), 'RigVMFunction_MathQuaternionToEuler')
        if_rotate = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(1800, 1200), 'DISPATCH_RigVMDispatch_If')
        axis_multiply = controller.add_template_node('Multiply::Execute(in A,in B,out Result)', unreal.Vector2D(2000, 1000), 'Multiply')
        add_axis1 = controller.add_template_node('Add::Execute(in A,in B,out Result)', unreal.Vector2D(2200, 1000), 'Add')
        add_axis2 = controller.add_template_node('Add::Execute(in A,in B,out Result)', unreal.Vector2D(2400, 1000), 'Add')

        graph.add_link(meta_data, 'Value', steer_meta_data, 'Item', controller)
        graph.add_link(steer_meta_data, 'Value', get_steer_transform, 'Item', controller)
        graph.add_link(get_steer_transform, 'Transform.Rotation', to_euler, 'Value', controller)
        graph.add_link(to_euler, 'Result', if_rotate, 'True', controller)
        graph.add_link(get_steer_transform, 'Transform.Translation', if_rotate, 'False', controller)
        graph.add_link('Entry', 'steer_use_rotate', if_rotate, 'Condition', controller)

        graph.add_link('Entry', 'steer_axis', at_steer_axis, 'Array', controller)
        graph.add_link(at_steer_axis, 'Element', axis_multiply, 'B', controller)
        graph.add_link(if_rotate, 'Result', axis_multiply, 'A', controller)

        graph.add_link(axis_multiply, 'Result.X', add_axis1, 'A', controller)
        graph.add_link(axis_multiply, 'Result.Y', add_axis1, 'B', controller)

        graph.add_link(add_axis1, 'Result', add_axis2, 'A', controller)
        graph.add_link(axis_multiply, 'Result.Z', add_axis2, 'B', controller)

        graph.add_link(add_axis2, 'Result', wheel_rotate, 'steer', controller)

        current_locals = locals()
        nodes = unreal_lib.graph.filter_nodes(current_locals.values())
        node = unreal_lib.graph.comment_nodes(nodes, controller, 'Forward Solve')
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
        graph.add_link(self.mode, 'Cases.2', set_channel, 'ExecuteContext', controller)
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
        unreal_lib.graph.move_nodes(500, 2000, nodes, controller)


class UnrealGetTransform(UnrealUtil):

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


class UnrealGetSubControls(UnrealUtil):

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


class UnrealSwitchRig(UnrealUtil):

    def _build_function_graph(self):

        if not self.graph:
            return

