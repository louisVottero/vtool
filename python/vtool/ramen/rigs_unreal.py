# Copyright (C) 2024 Louis Vottero louis.vot@gmail.com    All rights reserved.

import traceback
import copy

from enum import StrEnum
from . import rigs
from . import util as util_ramen

from vtool import util
from vtool import util_file
from vtool.maya_lib.core import get_uuid
from pip._vendor.resolvelib.providers import AbstractResolver

in_unreal = util.in_unreal

if in_unreal:
    import unreal
    from .. import unreal_lib
    from ..unreal_lib import graph
    from ..unreal_lib import lib_function


class SolveType(StrEnum):
    CONSTRUCT = 'Construct'
    FORWARD = 'Forward'
    BACKWARD = 'Backward'


def n(unreal_node):
    """
    returns the node path
    """
    if not in_unreal:
        return
    if unreal_node is None:
        return
    node_path = None

    try:
        node_path = unreal_node.get_node_path()
    except Exception as e:
        pass

    return node_path


cached_library_function_names = graph.get_vetala_lib_function_names(lib_function.VetalaLib())


class UnrealUtil(rigs.PlatformUtilRig):

    def __init__(self):
        super(UnrealUtil, self).__init__()

        self.layer = 0

        self.allowed_inputs = ['attach', 'joints']

        self.function = None
        self._function_name = self._get_function_name()

        self.solve_dict = {solve: {'function': None,
                                   'function_controller': None,
                                   'function_name': self._get_function_name(solve.value),
                                   'node':None,
                                   'controller':None} for solve in SolveType}

        self.graph = None
        self.library = None
        self.controller = None

        self.library_functions = {}
        self._cached_library_function_names = cached_library_function_names

    def _use_mode(self):
        return False

    def _init_graph(self):
        if not self.graph:
            return

        self._init_solve(SolveType.CONSTRUCT)
        self._init_solve(SolveType.FORWARD)
        self._init_solve(SolveType.BACKWARD)

        self.function_library = self.graph.get_controller_by_name('RigVMFunctionLibrary')

    def _init_solve(self, solve_type:SolveType):

        if solve_type == SolveType.FORWARD:
            self.solve_dict[solve_type]['controller'] = unreal_lib.graph.get_forward_controller(self.graph)
            self.solve_dict[solve_type]['node'] = None

            return

        if not self.solve_dict[solve_type]['controller'] is None:
            self.solve_dict[solve_type]['controller'] = None

        if self.solve_dict[solve_type]['controller']:
            if not self.solve_dict[solve_type]['controller'].get_graph():
                self.solve_dict[solve_type]['controller'] = None

        if not self.solve_dict[solve_type]['controller']:
            if solve_type == SolveType.CONSTRUCT:
                model = unreal_lib.graph.add_construct_graph()
            if solve_type == SolveType.BACKWARD:
                model = unreal_lib.graph.add_backward_graph()

            self.solve_dict[solve_type]['controller'] = self.graph.get_controller_by_name(model.get_graph_name())

        self.solve_dict[solve_type]['node'] = None

    def _get_function_name(self, solve_string=''):
        rig_name = 'vetala_%s' % self.__class__.__name__
        rig_name = rig_name.replace('Unreal', '')
        if solve_string:
            rig_name = f'{rig_name}_{solve_string}'
        return rig_name

    def _load_rig_functions(self):

        for solve in self.solve_dict:
            function_name = self.solve_dict[solve]['function_name']

            found = self.library.find_function(function_name)

            if found:
                self.solve_dict[solve]['function'] = found
                self.solve_dict[solve]['function_controller'] = self.graph.get_controller_by_name(n(found))

    def _init_rig_functions(self):
        found_one = False
        solves = {}

        for solve in self.solve_dict:
            function_name = self.solve_dict[solve]['function_name']
            found = self.controller.get_graph().find_function(function_name)

            if not found:

                function_inst = self.controller.add_function_to_library(function_name, True, unreal.Vector2D(0, 0))
                self.solve_dict[solve]['function'] = function_inst
                controller = self.graph.get_controller_by_name(n(function_inst))
                self.solve_dict[solve]['function_controller'] = controller
                self.function_library.set_node_category(self.solve_dict[solve]['function'], f'Vetala_{solve}_Node')
                self._init_rig_use_attributes(solve)
                self._build_attributes(controller, solve)
                self._build_function_graph(controller, solve)
                solves[solve] = True

        return found_one

    def _init_rig_use_attributes(self, solve):

        self.solve_dict[solve]['function_controller'].add_exposed_pin('uuid', unreal.RigVMPinDirection.INPUT, 'FString', 'None', '')

    def _init_library(self):
        if not self.graph:
            return
        controller = self.function_library
        missing = False
        for name in self._cached_library_function_names:
            function = controller.get_graph().find_function(name)
            if function:
                self.library_functions[name] = function
                controller.set_node_category(function, 'Vetala_Lib')
            else:
                missing = True
        if not missing:
            return

        util.show('Init Library')
        self.library_functions = {}

        function_dict = self._build_function_lib()
        if function_dict:
            self.library_functions.update(function_dict)

    def _build_function_lib(self):

        controller = self.function_library
        library = graph.get_local_function_library()

        vetala_lib = lib_function.VetalaLib()

        function_dict = graph.build_vetala_lib_class(vetala_lib, controller, library)
        return function_dict

    def _function_input_exists(self, name, controller):

        input_arguments = controller.get_graph().get_input_arguments()
        for input_arg in input_arguments:
            if input_arg.name == name:
                return True

        return False

    def _function_output_exists(self, name, controller):

        arguments = controller.get_graph().get_output_arguments()
        for arg in arguments:
            if arg.name == name:
                return True

        return False

    def _add_bool_in(self, name, value, controller):
        if self._function_input_exists(name, controller):
            return

        value = str(value)
        value = value.lower()
        controller.add_exposed_pin(name, unreal.RigVMPinDirection.INPUT, 'bool', 'None', value)

    def _add_int_in(self, name, value, controller):
        if self._function_input_exists(name, controller):
            return

        value = str(value)
        controller.add_exposed_pin(name, unreal.RigVMPinDirection.INPUT, 'int32', 'None', value)

    def _add_number_in(self, name, value, controller):
        if self._function_input_exists(name, controller):
            return

        value = str(value)
        controller.add_exposed_pin(name, unreal.RigVMPinDirection.INPUT, 'float', 'None', value)

    def _add_color_array_in(self, name, value, controller):
        if self._function_input_exists(name, controller):
            return

        color = value[0]

        if not isinstance(color, list):
            color = value

        color_pin = controller.add_exposed_pin(name, unreal.RigVMPinDirection.INPUT,
                                                             'TArray<FLinearColor>', '/Script/CoreUObject.LinearColor',
                                                             '')

        node = controller.get_graph().get_graph_name()

        self.function_library.insert_array_pin(f'{node}.{color_pin}', -1, '')
        self.function_library.set_pin_default_value(f'{node}.{color_pin}.0.R', str(color[0]), False)
        self.function_library.set_pin_default_value(f'{node}.{color_pin}.0.G', str(color[1]), False)
        self.function_library.set_pin_default_value(f'{node}.{color_pin}.0.B', str(color[2]), False)

    def _add_color_array_out(self, name, value, controller):
        if self._function_output_exists(name, controller):
            return

        color = value[0]

        color_pin = controller.add_exposed_pin(name, unreal.RigVMPinDirection.OUTPUT,
                                                             'TArray<FLinearColor>', '/Script/CoreUObject.LinearColor',
                                                             '')

        node = controller.get_graph().get_graph_name()
        self.function_library.insert_array_pin(f'{node}.{color_pin}', -1, '')
        self.function_library.set_pin_default_value(f'{node}.{color_pin}.0.R', str(color[0]), False)
        self.function_library.set_pin_default_value(f'{node}.{color_pin}.0.G', str(color[1]), False)
        self.function_library.set_pin_default_value(f'{node}.{color_pin}.0.B', str(color[2]), False)

    def _add_transform_array_in(self, name, value, controller):
        if self._function_input_exists(name, controller):
            return
        controller.add_exposed_pin(name, unreal.RigVMPinDirection.INPUT,
                                     'TArray<FRigElementKey>',
                                     '/Script/ControlRig.RigElementKey', '')

    def _add_vector_array_in(self, name, value, controller):
        if self._function_input_exists(name, controller):
            return
        controller.add_exposed_pin(name, unreal.RigVMPinDirection.INPUT,
                                   'TArray<FVector>',
                                   '/Script/CoreUObject.Vector', '()')

    def _add_transform_array_out(self, name, controller):
        if self._function_output_exists(name, controller):
            return
        controller.add_exposed_pin(name, unreal.RigVMPinDirection.OUTPUT,
                                     'TArray<FRigElementKey>',
                                     '/Script/ControlRig.RigElementKey', '')

    def _initialize_attributes(self):
        result = super()._initialize_attributes()

        return result

    def _build_attributes(self, controller, solve):

        for name in self.rig.attr.get_all():

            inout_state = self.rig.attr.get_inout_state(name)

            if inout_state == 'in':
                self._build_input(name, controller, solve)
            if inout_state == 'node_attr':
                self._build_node_attribute(name, controller, solve)
            if inout_state == 'out':
                self._build_output(name, controller, solve)

    def _build_input(self, name, controller, solve):

        if solve == SolveType.FORWARD or solve == SolveType.BACKWARD:
            if name not in self.allowed_inputs:
                return

        value, attr_type = self.rig.attr.get(name, True)

        if not controller:
            return

        if attr_type == rigs.AttrType.INT:
            self._add_int_in(name, value, controller)

        if attr_type == rigs.AttrType.BOOL:
            self._add_bool_in(name, value, controller)

        if attr_type == rigs.AttrType.NUMBER:
            self._add_number_in(name, value, controller)

        if attr_type == rigs.AttrType.COLOR:
            self._add_color_array_in(name, value, controller)

        if attr_type == rigs.AttrType.STRING:
            if not value:
                value = ['']
            value = value[0]
            controller.add_exposed_pin(name, unreal.RigVMPinDirection.INPUT, 'FString', 'None', value)

        if attr_type == rigs.AttrType.TRANSFORM:
            self._add_transform_array_in(name, value, controller)

        if attr_type == rigs.AttrType.VECTOR:
            self._add_vector_array_in(name, value, controller)

    def _build_node_attribute(self, name, controller, solve):

        if solve == SolveType.FORWARD or solve == SolveType.BACKWARD:
            if name not in self.allowed_inputs:
                return

        value, attr_type = self.rig.attr.get(name, True)

        if not controller:
            return

        if attr_type == rigs.AttrType.INT:
            self._add_int_in(name, value, controller)

        if attr_type == rigs.AttrType.BOOL:
            self._add_bool_in(name, value, controller)

        if attr_type == rigs.AttrType.NUMBER:
            self._add_number_in(name, value, controller)

        if attr_type == rigs.AttrType.COLOR:
            self._add_color_array_in(name, value, controller)

        if attr_type == rigs.AttrType.STRING:
            if value is None:
                value = ['']
            controller.add_exposed_pin(name, unreal.RigVMPinDirection.INPUT, 'FString', 'None', str(value[0]))

        if attr_type == rigs.AttrType.TRANSFORM:
            self._add_transform_array_in(name, value, controller)

        if attr_type == rigs.AttrType.VECTOR:
            self._add_vector_array_in(name, value, controller)

    def _build_output(self, name, controller, solve):

        value, attr_type = self.rig.attr.get(name, True)

        if not controller:
            return

        if attr_type == rigs.AttrType.COLOR:
            self._add_color_array_out(name, value, controller)

        if attr_type == rigs.AttrType.STRING:
            if value is None:
                value = ''
            controller.add_exposed_pin(name, unreal.RigVMPinDirection.OUTPUT, 'FString', 'None',
                                                     value)

        if attr_type == rigs.AttrType.TRANSFORM:
            self._add_transform_array_out(name, controller)

    def _load_function_nodes(self):
        for solve in self.solve_dict:
            controller = self.solve_dict[solve]['controller']
            node = self._get_graph_node(controller)
            self.solve_dict[solve]['node'] = node

    def _get_graph_node(self, controller):
        if not controller:
            return

        graph = None
        try:
            graph = controller.get_graph()
        except Exception:
            return

        if graph == None:
            return
        nodes = graph.get_nodes()

        if not nodes:
            return

        for node in nodes:
            pin = controller.get_graph().find_pin('%s.uuid' % n(node))
            if pin:
                node_uuid = pin.get_default_value()
                if node_uuid == self.rig.uuid:
                    return node

    def _add_nodes_to_graph(self):
        for solve in self.solve_dict:
            controller = self.solve_dict[solve]['controller']
            function = self.solve_dict[solve]['function']

            node = self.solve_dict[solve]['node']
            if node:
                continue
            node = controller.add_function_reference_node(function, unreal.Vector2D(100, 100),
                                                                              n(function))
            self.solve_dict[solve]['node'] = node
            controller.set_pin_default_value('%s.uuid' % n(node), self.rig.uuid, False)

    def _reset_array(self, name, value):

        for solve in self.solve_dict:
            controller = self.solve_dict[solve]['controller']
            node = self.solve_dict[solve]['node']

            graph = controller.get_graph()
            pin = graph.find_pin('%s.%s' % (n(node), name))

            if not pin:
                return

            array_size = pin.get_array_size()

            if array_size == 0:
                    return

            if value:
                if array_size == len(value):
                    return

            controller.clear_array_pin('%s.%s' % (n(node), name))
            controller.set_pin_default_value('%s.%s' % (node.get_node_path(), name),
                                                            '()',
                                                            True)

    def _add_array_entry(self, name, value):
        pass

    def _set_attr_on_function(self, name, custom_value=None):

        for solve in self.solve_dict:
            if not self.solve_dict[solve]['function_controller']:
                continue

            function_controller = self.solve_dict[solve]['function_controller']
            controller = self.solve_dict[solve]['controller']
            graph = controller.get_graph()
            node = self.solve_dict[solve]['node']

            if not node:
                continue

            pin = f'{n(node)}.{name}'

            if name not in self.allowed_inputs and solve != SolveType.CONSTRUCT:
                continue

            if not self._function_input_exists(name, function_controller):
                # util.warning('Attribute %s should exist but is missing. Node may need to be updated.' % name)
                continue

            value, value_type = self.rig.attr.get(name, True)

            if value_type == rigs.AttrType.TITLE:
                continue

            if custom_value:
                value = custom_value

            if value_type == rigs.AttrType.INT:
                value = str(int(value[0]))
                controller.set_pin_default_value(pin, value, False)

            if value_type == rigs.AttrType.BOOL:
                value = str(value)
                if value == '1':
                    value = 'true'
                if value == '0':
                    value = 'false'
                controller.set_pin_default_value(pin, value, False)

            if value_type == rigs.AttrType.NUMBER:
                value = str(value[0])

                controller.set_pin_default_value(pin, value, False)

            if value_type == rigs.AttrType.STRING:
                if value is None:
                    value = ''
                else:
                    value = value[0]

                controller.set_pin_default_value(pin, str(value), False)

            if value_type == rigs.AttrType.COLOR:
                self._reset_array(name, value)

                if not value:
                    continue

                for inc, color in enumerate(value):
                    controller.set_array_pin_size(pin, len(value))
                    controller.set_pin_default_value(f'{pin}.{inc}.R', str(color[0]), True)
                    controller.set_pin_default_value(f'{pin}.{inc}.G', str(color[1]), True)
                    controller.set_pin_default_value(f'{pin}.{inc}.B', str(color[2]), True)
                    controller.set_pin_default_value(f'{pin}.{inc}.A', str(color[3]), True)

            if value_type == rigs.AttrType.TRANSFORM:
                if not util.is_iterable(value):
                    continue

                self._reset_array(name, value)
                if not value:
                    continue

                elements = self.graph.hierarchy.get_all_keys()
                type_map = {
                            unreal.RigElementType.BONE: 'Bone',
                            unreal.RigElementType.CONTROL: 'Control',
                            unreal.RigElementType.NULL: 'Null'
                            }

                element_map = {str(e.name): e for e in elements}

                found = [
                    [sub_name, type_map.get(element_map[sub_name].type, '')]
                    for sub_name in value
                    if sub_name in element_map
                ]

                controller.set_array_pin_size(pin, len(found))
                for inc, (e_name, type_name) in enumerate(found):
                    if not type_name:
                        continue
                    controller.set_pin_default_value(f'{pin}.{inc}.Type', type_name, False)
                    controller.set_pin_default_value(f'{pin}.{inc}.Name', e_name, False)

            if value_type == rigs.AttrType.VECTOR:
                self._reset_array(name, value)

                if not value:
                    continue

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

    def _build_entry(self, controller, solve):

        return

    def _build_return(self, controller, solve):

        controller.set_node_position_by_name('Return', unreal.Vector2D(5000, 0))

    def _build_function_graph(self, controller, solve):

        if self._use_mode():
            self._build_entry(controller, solve)
            self._build_return(controller, solve)

    def add_library_node(self, name, controller, x, y):
        node = self.library_functions[name]
        added_node = controller.add_function_reference_node(node,
                                                         unreal.Vector2D(x, y),
                                                         n(node))

        return added_node

    def select(self):

        controllers = self.get_controllers()
        nodes = self.get_nodes()

        graph.clear_selection()

        for node, controller in zip(nodes, controllers):
            if node:
                controller.select_node(node)

    def set_node_position(self, position_x, position_y):

        for solve in self.solve_dict:
            node = self.solve_dict[solve]['node']
            controller = self.solve_dict[solve]['controller']
            if node:
                controller.set_node_position_by_name(n(node), unreal.Vector2D(position_x, position_y))

    def remove_connections(self):

        nodes = (self.construct_node, self.forward_node, self.backward_node)
        controllers = self.get_controllers()

        for node, controller in zip(nodes, controllers):
            graph.break_all_links_to_node(node, controller)

    def is_valid(self):
        if self.rig.state == rigs.RigState.CREATED:
            for solve in self.solve_dict:
                if not self.solve_dict[solve]['node']:
                    return False

        if self.rig.state == rigs.RigState.LOADED:
            if not self.graph:
                return False

        return True

    def is_built(self):
        if not self.graph:
            return False
        try:
            found_one = False
            for solve in self.solve_dict:
                if not self.solve_dict[solve]['node']:
                    found_one = True
                elif self.solve_dict[solve]['node'].get_graph() is None:
                    found_one = True

            if found_one:
                for solve in self.solve_dict:
                    self.solve_dict[solve]['node'] = None
                return False

            if not found_one:
                return True
        except:
            return False

    def get_controllers(self):

        return [
        data['controller']
        for data in self.solve_dict.values()
        ]

    def get_nodes(self):
        return [
        data['node']
        for data in self.solve_dict.values()
        ]

    def get_graph_start_nodes(self):

        forward_controller = self.solve_dict[SolveType.FORWARD]['controller']
        if not forward_controller:
            return

        return ['PrepareForExecution', graph.get_forward_start_node(self.graph), 'InverseExecution']

    @property
    def controls(self):
        return

    @controls.setter
    def controls(self, value):
        return

    # @property
    # def parent(self):
    #    return

    # @parent.setter
    # def parent(self, value):
    #    return

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

        if not self.solve_dict[SolveType.CONSTRUCT]['controller']:
            self.solve_dict[SolveType.CONSTRUCT]['controller'] = unreal_lib.graph.get_construct_controller(self.graph)

        if not self.solve_dict[SolveType.FORWARD]['controller']:
            self.solve_dict[SolveType.FORWARD]['controller'] = unreal_lib.graph.get_forward_controller(self.graph)

        if not self.solve_dict[SolveType.BACKWARD]['controller']:
            self.solve_dict[SolveType.BACKWARD]['controller'] = unreal_lib.graph.get_backward_controller(self.graph)

        for solve in self.solve_dict:
            if not self.solve_dict[solve]['controller']:
                util.warning(f'No {solve.value} graph found.')
                return

        self._load_function_nodes()

        if self.is_built():
            self.rig.state = rigs.RigState.CREATED

        if self.solve_dict[SolveType.CONSTRUCT]['controller']:
            self.rig.dirty = False

        self._load_rig_functions()

    @util_ramen.decorator_undo('Build')
    def build(self):
        super(UnrealUtil, self).build()

        if not in_unreal:
            return

        if not self.graph:
            util.warning('No control rig for Unreal rig')
            return

        if self.is_built():
            self.load()
        else:

            self._init_graph()

            self.load()

            self._init_library()

            self._init_rig_functions()

            self._add_nodes_to_graph()

        self.rig.state = rigs.RigState.CREATED

        for name in self.rig.attr.node:
            self._set_attr_on_function(name)
        for name in self.rig.attr.inputs:
            self._set_attr_on_function(name)

    def unbuild(self):
        super(UnrealUtil, self).unbuild()

    def delete(self):
        super(UnrealUtil, self).delete()
        if not self.graph:
            return

        if not self.construct_node:
            self.load()

        super(UnrealUtil, self).unbuild()

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

    def _use_mode(self):
        return True

    def set_layer(self, int_value):
        super(UnrealUtilRig, self).set_layer(int_value)

        if self.is_built():
            controllers = self.get_controllers()
            nodes = self.get_nodes()

            for node, controller in zip(nodes, controllers):
                controller.set_pin_default_value(f'{n(node)}.layer', str(int_value), False)

    def _init_rig_use_attributes(self, solve):
        super(UnrealUtilRig, self)._init_rig_use_attributes(solve)

        self.solve_dict[solve]['function_controller'].add_exposed_pin('layer', unreal.RigVMPinDirection.INPUT, 'int32', 'None', '0')
        # self.function_controller.add_exposed_pin('layer', unreal.RigVMPinDirection.INPUT, 'int32', 'None', '')
        # self.function_controller.add_exposed_pin('switch', unreal.RigVMPinDirection.INPUT, 'int32', 'None', '')

    def _build_entry(self, controller, solve):
        super(UnrealUtilRig, self)._build_entry(controller, solve)

        controller.add_local_variable_from_object_path('local_controls', 'TArray<FRigElementKey>',
                                                         '/Script/ControlRig.RigElementKey', '')

        # controller = self.function_controller

        controller.add_local_variable_from_object_path('control_layer', 'FName',
                                                                     '', '')

        branch = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_ControlFlowBranch',
                                                           'Execute',
                                                           unreal.Vector2D(255, -160), 'Branch')

        layer_state = self.library_functions['vetalaLib_rigLayerState']
        layer_state = controller.add_function_reference_node(layer_state,
                                                        unreal.Vector2D(0, -30),
                                                        n(layer_state))

        graph.add_link('Entry', 'layer', layer_state, 'layer', controller)
        graph.add_link('Entry', 'joints', layer_state, 'joints', controller)

        graph.add_link(layer_state, 'state', branch, 'condition', controller)

        concat = controller.add_template_node('Concat::Execute(in A,in B,out Result)', unreal.Vector2D(-250, -200), 'Concat')
        control_layer = controller.add_variable_node('control_layer', 'FName', None, False, '', unreal.Vector2D(-50, -180), 'VariableNode')
        graph.add_link(concat, 'Result', control_layer, 'Value', controller)

        int_to_name = controller.add_template_node('Int to Name::Execute(in Number,in PaddedSize,out Result)', unreal.Vector2D(-400, -200), 'Int to Name')
        graph.add_link(int_to_name, 'Result', concat, 'B', controller)
        graph.add_link('Entry', 'layer', int_to_name, 'Number', controller)
        controller.set_pin_default_value(f'{n(concat)}.A', 'Control_', False)

        graph.add_link('Entry', 'ExecuteContext', control_layer, 'ExecuteContext', controller)
        graph.add_link(control_layer, 'ExecuteContext', branch, 'ExecuteContext', controller)

        graph.add_link(branch, 'Completed', 'Return', 'ExecuteContext', controller)

        self.layer_state = layer_state
        self.branch_node = branch

    def _build_return(self, controller, solve):
        super(UnrealUtilRig, self)._build_return(controller, solve)

        library = graph.get_local_function_library()

        get_uuid = controller.add_variable_node('uuid', 'FString', None, True, '', unreal.Vector2D(3136.0, -112.0), 'Get uuid')
        get_local_controls = controller.add_variable_node_from_object_path('local_controls', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(3136.0, 32.0), 'Get local_controls')
        get_joints = controller.add_variable_node_from_object_path('joints', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(3136.0, 64), 'Get joints')
        get_layer = controller.add_variable_node('layer', 'int32', None, True, '', unreal.Vector2D(3120.0, 224.0), 'Get layer')

        vetala_lib_output_rig_controls = controller.add_function_reference_node(library.find_function('vetalaLib_OutputRigControls'), unreal.Vector2D(3392.0, -64.0), 'vetalaLib_OutputRigControls')

        graph.add_link(self.branch_node, 'Completed', vetala_lib_output_rig_controls, 'ExecuteContext', controller)

        graph.add_link(get_uuid, 'Value', vetala_lib_output_rig_controls, 'uuid', controller)
        graph.add_link(get_local_controls, 'Value', vetala_lib_output_rig_controls, 'controls', controller)
        graph.add_link(get_joints, 'Value', vetala_lib_output_rig_controls, 'joints', controller)

        graph.add_link(get_layer, 'Value', vetala_lib_output_rig_controls, 'layer', controller)

        graph.add_link(vetala_lib_output_rig_controls, 'out_controls', 'Return', 'controls', controller)
        graph.add_link(vetala_lib_output_rig_controls, 'ExecuteContext', 'Return', 'ExecuteContext', controller)

        graph.add_link(self.layer_state, 'state', vetala_lib_output_rig_controls, 'layer_enabled', controller)

        if solve == SolveType.CONSTRUCT:
            graph.set_pin(vetala_lib_output_rig_controls, 'mode', '0', controller)
        if solve == SolveType.FORWARD:
            graph.set_pin(vetala_lib_output_rig_controls, 'mode', '1', controller)
        if solve == SolveType.BACKWARD:
            graph.set_pin(vetala_lib_output_rig_controls, 'mode', '2', controller)

        controller.set_node_position_by_name('Return', unreal.Vector2D(4000, 0))

        self.output_rig_controls = vetala_lib_output_rig_controls

    def _build_function_graph(self, controller, solve):
        super(UnrealUtilRig, self)._build_function_graph(controller, solve)

        if solve == SolveType.CONSTRUCT:
            self._build_function_construct_graph(controller)

        if solve == SolveType.FORWARD:
            self._build_function_forward_graph(controller)

        if solve == SolveType.BACKWARD:
            self._build_function_backward_graph(controller)

    def _build_function_construct_graph(self):
        return

    def _build_function_forward_graph(self):
        return

    def _build_function_backward_graph(self):
        return


class UnrealFkRig(UnrealUtilRig):

    def _build_function_construct_graph(self, controller):
        library = graph.get_local_function_library()

        for_each = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayIterator(in Array,out Element,out Index,out Count,out Ratio)', unreal.Vector2D(600.0, -1700.0), 'For Each')
        vetala_lib_control = self._create_control(controller, 1600.0, -1750.0)
        vetala_lib_get_parent = controller.add_function_reference_node(library.find_function('vetalaLib_GetParent'), unreal.Vector2D(1072.0, -1888.0), 'vetalaLib_GetParent')
        get_control_layer = controller.add_variable_node('control_layer', 'FName', None, True, '', unreal.Vector2D(930.0, -1600.0), 'Get control_layer')
        vetala_lib_get_joint_description = controller.add_function_reference_node(library.find_function('vetalaLib_GetJointDescription'), unreal.Vector2D(1000.0, -1450.0), 'vetalaLib_GetJointDescription')
        set_item_metadata = controller.add_template_node('DISPATCH_RigDispatch_SetMetadata(in Item,in Name,in NameSpace,in Value,out Success)', unreal.Vector2D(2100.0, -1900.0), 'Set Item Metadata')
        equals = controller.add_template_node('DISPATCH_RigVMDispatch_CoreEquals(in A,in B,out Result)', unreal.Vector2D(900.0, -1900.0), 'Equals')
        get_description = controller.add_variable_node('description', 'FString', None, True, '', unreal.Vector2D(624.0, -1184.0), 'Get description')
        get_use_joint_name = controller.add_variable_node('use_joint_name', 'bool', None, True, '', unreal.Vector2D(600.0, -1050.0), 'Get use_joint_name')
        get_joint_token = controller.add_variable_node('joint_token', 'FString', None, True, '', unreal.Vector2D(600.0, -1450.0), 'Get joint_token')
        if1 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(1350.0, -1150.0), 'If')
        add = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayAdd(io Array,in Element,out Index)', unreal.Vector2D(1900.0, -1350.0), 'Add')
        get_local_controls = controller.add_variable_node_from_object_path('local_controls', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(1800.0, -1150.0), 'Get local_controls')
        get_attach = controller.add_variable_node('attach', 'bool', None, True, '', unreal.Vector2D(1472.0, -1872.0), 'Get attach')
        branch = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_ControlFlowBranch', 'Execute', unreal.Vector2D(1780.4921968269605, -1914.7317030423264), 'Branch')

        graph.add_link(self.branch_node, 'True', for_each, 'ExecuteContext', controller)
        graph.add_link(for_each, 'ExecuteContext', vetala_lib_get_joint_description, 'ExecuteContext', controller)
        graph.add_link(vetala_lib_get_joint_description, 'ExecuteContext', vetala_lib_control, 'ExecuteContext', controller)
        graph.add_link(vetala_lib_control, 'ExecuteContext', branch, 'ExecuteContext', controller)
        graph.add_link(branch, 'True', set_item_metadata, 'ExecuteContext', controller)
        graph.add_link(branch, 'Completed', add, 'ExecuteContext', controller)
        graph.add_link('Entry', 'joints', for_each, 'Array', controller)
        graph.add_link(for_each, 'Element', vetala_lib_control, 'driven', controller)
        graph.add_link(for_each, 'Element', set_item_metadata, 'Item', controller)
        graph.add_link(for_each, 'Element', vetala_lib_get_parent, 'joint', controller)
        graph.add_link(for_each, 'Element', vetala_lib_get_joint_description, 'joint', controller)
        graph.add_link(for_each, 'Index', vetala_lib_control, 'increment', controller)
        graph.add_link(for_each, 'Index', equals, 'A', controller)
        graph.add_link(vetala_lib_get_parent, 'Result', vetala_lib_control, 'parent', controller)
        graph.add_link(if1, 'Result', vetala_lib_control, 'description', controller)
        graph.add_link('Entry', 'side', vetala_lib_control, 'side', controller)
        graph.add_link('Entry', 'joint_token', vetala_lib_control, 'joint_token', controller)
        graph.add_link('Entry', 'sub_count', vetala_lib_control, 'sub_count', controller)
        graph.add_link('Entry', 'restrain_numbering', vetala_lib_control, 'restrain_numbering', controller)
        graph.add_link('Entry', 'shape', vetala_lib_control, 'shape', controller)
        graph.add_link('Entry', 'color', vetala_lib_control, 'color', controller)
        graph.add_link('Entry', 'sub_color', vetala_lib_control, 'sub_color', controller)
        graph.add_link('Entry', 'shape_translate', vetala_lib_control, 'translate', controller)
        graph.add_link('Entry', 'shape_rotate', vetala_lib_control, 'rotate', controller)
        graph.add_link('Entry', 'shape_scale', vetala_lib_control, 'scale', controller)
        graph.add_link(vetala_lib_control, 'Last Control', set_item_metadata, 'Value', controller)
        graph.add_link(vetala_lib_control, 'Control', add, 'Element', controller)
        graph.add_link('Entry', 'parent', vetala_lib_get_parent, 'default_parent', controller)
        graph.add_link(equals, 'Result', vetala_lib_get_parent, 'is_top_joint', controller)
        graph.add_link('Entry', 'hierarchy', vetala_lib_get_parent, 'in_hierarchy', controller)
        graph.add_link(get_control_layer, 'Value', vetala_lib_get_parent, 'control_layer', controller)
        graph.add_link(get_control_layer, 'Value', set_item_metadata, 'Name', controller)
        graph.add_link(get_description, 'Value', vetala_lib_get_joint_description, 'description', controller)
        graph.add_link(get_joint_token, 'Value', vetala_lib_get_joint_description, 'joint_token', controller)
        graph.add_link(vetala_lib_get_joint_description, 'Result', if1, 'True', controller)
        graph.add_link(get_description, 'Value', if1, 'False', controller)
        graph.add_link(get_use_joint_name, 'Value', if1, 'Condition', controller)
        graph.add_link(get_local_controls, 'Value', add, 'Array', controller)

        graph.add_link(get_attach, 'Value', branch, 'Condition', controller)

        graph.set_pin(set_item_metadata, 'NameSpace', 'Self', controller)
        graph.set_pin(equals, 'B', '0', controller)

        current_locals = locals()
        nodes = unreal_lib.graph.filter_nodes(current_locals.values())
        node = unreal_lib.graph.comment_nodes(nodes, controller, 'Construction')

        nodes.append(node)
        unreal_lib.graph.move_nodes(500, -2000, nodes, controller)

    def _build_function_forward_graph(self, controller):

        library = graph.get_local_function_library()

        controller.add_local_variable('has_metadata', cpp_type="bool", cpp_type_object=None, default_value="False")

        for_each = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayIterator(in Array,out Element,out Index,out Count,out Ratio)', unreal.Vector2D(808.0, 100.0), 'For Each')
        get_item_metadata = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(1184.0, 208.0), 'Get Item Metadata')
        get_control_layer = controller.add_variable_node('control_layer', 'FName', None, True, '', unreal.Vector2D(1008.0, 250.0), 'Get control_layer')
        get_transform = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetTransform', 'Execute', unreal.Vector2D(1504.0, 208.0), 'Get Transform')
        set_transform = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_SetTransform', 'Execute', unreal.Vector2D(2032.0, 96.0), 'Set Transform')
        branch = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_ControlFlowBranch', 'Execute', unreal.Vector2D(592.0, 112.0), 'Branch')
        get_children = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_CollectionChildrenArray', 'Execute', unreal.Vector2D(528.0, 496.0), 'Get Children')
        has_metadata = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HasMetadata', 'Execute', unreal.Vector2D(1680.0, 576.0), 'Has Metadata')
        for_each1 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayIterator(in Array,out Element,out Index,out Count,out Ratio)', unreal.Vector2D(1472.0, 512.0), 'For Each')
        set_has_metadata = controller.add_variable_node('has_metadata', 'bool', None, False, '', unreal.Vector2D(992.0, 368.0), 'Set has_metadata')
        set_has_metadata1 = controller.add_variable_node('has_metadata', 'bool', None, False, '', unreal.Vector2D(2080.0, 352.0), 'Set has_metadata')
        get_has_metadata = controller.add_variable_node('has_metadata', 'bool', None, True, '', unreal.Vector2D(1632.0, 416.0), 'Get has_metadata')
        if1 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(1824.0, 368.0), 'If')
        branch1 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_ControlFlowBranch', 'Execute', unreal.Vector2D(1248.0, 400.0), 'Branch')
        num = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetNum(in Array,out Num)', unreal.Vector2D(912.0, 704.0), 'Num')
        greater = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathIntGreater', 'Execute', unreal.Vector2D(1120.0, 688.0), 'Greater')
        branch2 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_ControlFlowBranch', 'Execute', unreal.Vector2D(2016.0, 496.0), 'Branch')

        graph.add_link(branch, 'True', for_each, 'ExecuteContext', controller)
        graph.add_link(for_each, 'ExecuteContext', set_has_metadata, 'ExecuteContext', controller)
        graph.add_link(self.branch_node, 'True', branch, 'ExecuteContext', controller)
        graph.add_link(branch1, 'True', for_each1, 'ExecuteContext', controller)
        graph.add_link(for_each1, 'ExecuteContext', branch2, 'ExecuteContext', controller)
        graph.add_link(set_has_metadata, 'ExecuteContext', branch1, 'ExecuteContext', controller)
        graph.add_link(branch2, 'True', set_has_metadata1, 'ExecuteContext', controller)
        graph.add_link('Entry', 'joints', for_each, 'Array', controller)
        graph.add_link(for_each, 'Element', get_children, 'Parent', controller)
        graph.add_link(for_each, 'Element', get_item_metadata, 'Item', controller)
        graph.add_link(for_each, 'Element', set_transform, 'Item', controller)
        graph.add_link(get_control_layer, 'Value', get_item_metadata, 'Name', controller)
        graph.add_link(get_item_metadata, 'Value', get_transform, 'Item', controller)
        graph.add_link(get_transform, 'Transform', set_transform, 'Value', controller)
        graph.add_link(branch1, 'Completed', set_transform, 'ExecutePin', controller)
        graph.add_link(if1, 'Result', set_transform, 'bPropagateToChildren', controller)
        graph.add_link('Entry', 'attach', branch, 'Condition', controller)
        graph.add_link(get_children, 'Items', for_each1, 'Array', controller)
        graph.add_link(get_children, 'Items', num, 'Array', controller)
        graph.add_link(for_each1, 'Element', has_metadata, 'Item', controller)
        graph.add_link(has_metadata, 'Found', branch2, 'Condition', controller)
        graph.add_link(get_has_metadata, 'Value', if1, 'Condition', controller)
        graph.add_link(greater, 'Result', branch1, 'Condition', controller)
        graph.add_link(num, 'Num', 'Greater', 'A', controller)
        graph.add_link(num, 'Num', greater, 'A', controller)

        graph.set_pin(get_item_metadata, 'NameSpace', 'Self', controller)
        graph.set_pin(get_item_metadata, 'Default', '(Type=Bone,Name="None")', controller)
        graph.set_pin(get_transform, 'Space', 'GlobalSpace', controller)
        graph.set_pin(get_transform, 'bInitial', 'False', controller)
        graph.set_pin(set_transform, 'Space', 'GlobalSpace', controller)
        graph.set_pin(set_transform, 'bInitial', 'False', controller)
        graph.set_pin(set_transform, 'Weight', '1.000000', controller)
        graph.set_pin(get_children, 'bIncludeParent', 'False', controller)
        graph.set_pin(get_children, 'bRecursive', 'False', controller)
        graph.set_pin(get_children, 'bDefaultChildren', 'true', controller)
        graph.set_pin(get_children, 'TypeToSearch', 'Bone', controller)
        graph.set_pin(has_metadata, 'Name', 'Controls_0', controller)
        graph.set_pin(has_metadata, 'Type', 'RigElementKeyArray', controller)
        graph.set_pin(has_metadata, 'NameSpace', 'Self', controller)
        graph.set_pin(if1, 'True', 'false', controller)
        graph.set_pin(if1, 'False', 'true', controller)
        graph.set_pin(set_has_metadata1, 'Value', 'true', controller)
        graph.set_pin(greater, 'B', '0', controller)

        current_locals = locals()
        nodes = unreal_lib.graph.filter_nodes(current_locals.values())
        node = unreal_lib.graph.comment_nodes(nodes, controller, 'Forward Solve')

        nodes.append(node)
        unreal_lib.graph.move_nodes(500, 0, nodes, controller)

    def _build_function_backward_graph(self, controller):

        for_each = controller.add_template_node(
            'DISPATCH_RigVMDispatch_ArrayIterator(in Array,out Element,out Index,out Count,out Ratio)',
            unreal.Vector2D(850, 1250), 'DISPATCH_RigVMDispatch_ArrayIterator')
        controller.add_link(f'{n(self.branch_node)}.True', f'{n(for_each)}.ExecuteContext')
        controller.add_link('Entry.joints', f'{n(for_each)}.Array')

        set_transform = controller.add_template_node(
            'Set Transform::Execute(in Item,in Space,in bInitial,in Value,in Weight,in bPropagateToChildren)',
            unreal.Vector2D(2000, 1250), 'Set Transform')

        meta_data = controller.add_template_node(
            'DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in Default,out Value,out Found)',
            unreal.Vector2D(1250, 1350), 'DISPATCH_RigDispatch_GetMetadata')
        controller.set_pin_default_value('%s.Name' % meta_data.get_node_path(), 'Control', False)
        # self.function_controller.add_link('%s.Element' % for_each.get_node_path(), '%s.Item' % meta_data.get_node_path())

        controller.add_link(f'{n(meta_data)}.Value', f'{n(set_transform)}.Item')

        control_layer = controller.add_variable_node('control_layer', 'FName', None, True, '', unreal.Vector2D(1050, 1400), 'VariableNode')
        graph.add_link(control_layer, 'Value', meta_data, 'Name', controller)

        get_transform = controller.add_unit_node_from_struct_path(
            '/Script/ControlRig.RigUnit_GetTransform', 'Execute', unreal.Vector2D(1550, 1350), 'GetTransform')
        controller.add_link(f'{n(for_each)}.Element', f'{n(get_transform)}.Item')

        controller.add_link('%s.Transform' % get_transform.get_node_path(),
                                          '%s.Value' % set_transform.get_node_path())

        controller.add_link('%s.ExecuteContext' % for_each.get_node_path(),
                                          '%s.ExecuteContext' % set_transform.get_node_path())

        current_locals = locals()
        nodes = unreal_lib.graph.filter_nodes(current_locals.values())
        node = unreal_lib.graph.comment_nodes(nodes, controller, 'Backward Solve')

        nodes.append(node)
        unreal_lib.graph.move_nodes(500, 1000, nodes, controller)


class UnrealIkRig(UnrealUtilRig):

    def _build_controls(self, controller, library):

        get_local_ik = controller.add_variable_node_from_object_path('local_ik', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(6104.0, -1320.0), 'Get local_ik')

        vetala_lib_find_pole_vector = controller.add_function_reference_node(library.find_function('vetalaLib_findPoleVector'), unreal.Vector2D(4704.0, -1580.0), 'vetalaLib_findPoleVector')
        for_each = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayIterator(in Array,out Element,out Index,out Count,out Ratio)', unreal.Vector2D(1412.0, -1676.0), 'For Each')
        vetala_lib_control = self._create_control(controller, 2412.0, -1726.0)
        vetala_lib_get_parent = controller.add_function_reference_node(library.find_function('vetalaLib_GetParent'), unreal.Vector2D(1824.0, -1884.0), 'vetalaLib_GetParent')
        vetala_lib_get_joint_description = controller.add_function_reference_node(library.find_function('vetalaLib_GetJointDescription'), unreal.Vector2D(1912.0, -1560.0), 'vetalaLib_GetJointDescription')
        set_item_metadata = controller.add_template_node('DISPATCH_RigDispatch_SetMetadata(in Item,in Name,in NameSpace,in Value,out Success)', unreal.Vector2D(2912.0, -1876.0), 'Set Item Metadata')
        get_control_layer = controller.add_variable_node('control_layer', 'FName', None, True, '', unreal.Vector2D(1240.0, -1816.0), 'Get control_layer')
        equals = controller.add_template_node('DISPATCH_RigVMDispatch_CoreEquals(in A,in B,out Result)', unreal.Vector2D(1592.0, -1880.0), 'Equals')
        get_description = controller.add_variable_node('description', 'FString', None, True, '', unreal.Vector2D(1752.0, -1068.0), 'Get description')
        get_use_joint_name = controller.add_variable_node('use_joint_name', 'bool', None, True, '', unreal.Vector2D(1752.0, -968.0), 'Get use_joint_name')
        get_joint_token = controller.add_variable_node('joint_token', 'FString', None, True, '', unreal.Vector2D(1412.0, -1426.0), 'Get joint_token')
        if1 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(2162.0, -1126.0), 'If')
        get_world = controller.add_variable_node('world', 'bool', None, True, '', unreal.Vector2D(1160.0, -1272.0), 'Get world')
        get_mirror = controller.add_variable_node('mirror', 'bool', None, True, '', unreal.Vector2D(1160.0, -1172.0), 'Get mirror')
        add = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayAdd(io Array,in Element,out Index)', unreal.Vector2D(3344.0, -1900.0), 'Add')
        get_local_controls = controller.add_variable_node_from_object_path('local_controls', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(2696.0, -1704.0), 'Get local_controls')
        get_local_controls1 = controller.add_variable_node_from_object_path('local_controls', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(3976.0, -888.0), 'Get local_controls')
        get_pole_vector_shape = controller.add_variable_node('pole_vector_shape', 'FString', None, True, '', unreal.Vector2D(3012.0, -1451.0), 'Get pole_vector_shape')
        from_string = controller.add_template_node('DISPATCH_RigDispatch_FromString(in String,out Result)', unreal.Vector2D(3212.0, -1426.0), 'From String')
        shape_exists = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_ShapeExists', 'Execute', unreal.Vector2D(3412.0, -1426.0), 'Shape Exists')
        if2 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(3336.0, -1624.0), 'If')
        set_shape_settings = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchySetShapeSettings', 'Execute', unreal.Vector2D(3612.0, -1526.0), 'Set Shape Settings')
        vetala_lib_parent = controller.add_function_reference_node(library.find_function('vetalaLib_Parent'), unreal.Vector2D(4012.0, -1426.0), 'vetalaLib_Parent')
        vetala_lib_parent1 = controller.add_function_reference_node(library.find_function('vetalaLib_Parent'), unreal.Vector2D(4312.0, -1226.0), 'vetalaLib_Parent')
        get_color = controller.add_variable_node_from_object_path('color', 'TArray<FLinearColor>', '/Script/CoreUObject.LinearColor', True, '()', unreal.Vector2D(3012.0, -1376.0), 'Get color')
        at = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(3312.0, -1326.0), 'At')
        at1 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(3384.0, -1160.0), 'At')
        at2 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(3384.0, -1032.0), 'At')
        at3 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(3384.0, -872.0), 'At')
        get_shape_scale = controller.add_variable_node_from_object_path('shape_scale', 'TArray<FVector>', '/Script/CoreUObject.Vector', True, '()', unreal.Vector2D(2612.0, -1526.0), 'Get shape_scale')
        at4 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(2762.0, -1526.0), 'At')
        multiply = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathVectorMul', 'Execute', unreal.Vector2D(2912.0, -1526.0), 'Multiply')
        get_joints = controller.add_variable_node_from_object_path('joints', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(3784.0, -1688.0), 'Get joints')
        at5 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(4056.0, -1792.0), 'At')
        at6 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(4056.0, -1692.0), 'At')
        at7 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(4056.0, -1592.0), 'At')
        get_pole_vector_offset = controller.add_variable_node('pole_vector_offset', 'float', None, True, '', unreal.Vector2D(4312.0, -1676.0), 'Get pole_vector_offset')
        set_translation = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_SetTranslation', 'Execute', unreal.Vector2D(5112.0, -1528.0), 'Set Translation')
        greater = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathIntGreater', 'Execute', unreal.Vector2D(704.0, -1692.0), 'Greater')
        if3 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(904.0, -1592.0), 'If')
        spawn_null = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyAddNull', 'Execute', unreal.Vector2D(5904.0, -1900.0), 'Spawn Null')
        if4 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(5128.0, -664.0), 'If')
        get_item_array_metadata = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(4664.0, -680.0), 'Get Item Array Metadata')
        vetala_lib_get_item = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(5400.0, -712.0), 'vetalaLib_GetItem')
        get_transform = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetTransform', 'Execute', unreal.Vector2D(5704.0, -1288.0), 'Get Transform')

        add1 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayAdd(io Array,in Element,out Index)', unreal.Vector2D(6264.0, -1608.0), 'Add')
        num = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetNum(in Array,out Num)', unreal.Vector2D(4824.0, -472.0), 'Num')
        greater1 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathIntGreater', 'Execute', unreal.Vector2D(4984.0, -520.0), 'Greater')
        get_joints1 = controller.add_variable_node_from_object_path('joints', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(4976.0, -1068.0), 'Get joints')
        vetala_lib_get_item1 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(6216.0, -1112.0), 'vetalaLib_GetItem')
        set_item_array_metadata = controller.add_template_node('DISPATCH_RigDispatch_SetMetadata(in Item,in Name,in NameSpace,in Value,out Success)', unreal.Vector2D(6688.0, -1756.0), 'Set Item Array Metadata')
        get_local_ik1 = controller.add_variable_node_from_object_path('local_ik', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(3720.0, -392.0), 'Get local_ik')
        spawn_bool_animation_channel = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyAddAnimationChannelBool', 'Execute', unreal.Vector2D(7032.0, -1592.0), 'Spawn Bool Animation Channel')
        spawn_float_animation_channel = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyAddAnimationChannelFloat', 'Execute', unreal.Vector2D(7048.0, -1032.0), 'Spawn Float Animation Channel')
        rig_element_key = controller.add_free_reroute_node('FRigElementKey', unreal.load_object(None, '/Script/ControlRig.RigElementKey').get_name(), is_constant=False, custom_widget_name='', default_value='', position=[6818.0, -1195.0], node_name='', setup_undo_redo=True)
        spawn_float_animation_channel1 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyAddAnimationChannelFloat', 'Execute', unreal.Vector2D(5432.0, -1512.0), 'Spawn Float Animation Channel')
        num1 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetNum(in Array,out Num)', unreal.Vector2D(824.0, -760.0), 'Num')
        equals1 = controller.add_template_node('DISPATCH_RigVMDispatch_CoreEquals(in A,in B,out Result)', unreal.Vector2D(984.0, -568.0), 'Equals')
        branch = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_ControlFlowBranch', 'Execute', unreal.Vector2D(2872.0, -1176.0), 'Branch')
        get_local_controls2 = controller.add_variable_node_from_object_path('local_controls', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(3032.0, -968.0), 'Get local_controls')
        at8 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(4280.0, -888.0), 'At')
        vetala_lib_parent2 = controller.add_function_reference_node(library.find_function('vetalaLib_Parent'), unreal.Vector2D(3256.0, -616.0), 'vetalaLib_Parent')
        branch1 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_ControlFlowBranch', 'Execute', unreal.Vector2D(6776.0, -824.0), 'Branch')
        greater2 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathIntGreater', 'Execute', unreal.Vector2D(920.0, -984.0), 'Greater')
        if5 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(1208.0, -952.0), 'If')
        make_array = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayMake(in Values,out Array)', unreal.Vector2D(1544.0, -712.0), 'Make Array')
        get_joints2 = controller.add_variable_node_from_object_path('joints', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(600.0, -760.0), 'Get joints')
        at9 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(1208.0, -664.0), 'At')
        at10 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(1208.0, -552.0), 'At')
        or1 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathBoolOr', 'Execute', unreal.Vector2D(2560.0, -476.0), 'Or')
        vetala_lib_get_item2 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(5392.0, -556.0), 'vetalaLib_GetItem')
        get_transform1 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetTransform', 'Execute', unreal.Vector2D(5792.0, -924.0), 'Get Transform')
        vetala_lib_get_item3 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(5392.0, -380.0), 'vetalaLib_GetItem')

        controller.set_array_pin_size(f'{n(make_array)}.Values', 2)

        graph.add_link(get_joints2, 'Value', num1, 'Array', controller)
        graph.add_link(get_joints2, 'Value', if5, 'False', controller)
        graph.add_link(get_joints2, 'Value', at9, 'Array', controller)
        graph.add_link(get_joints2, 'Value', at10, 'Array', controller)
        graph.add_link(if4, 'Result', vetala_lib_get_item, 'Array', controller)

        controller.set_array_pin_size(f'{n(if4)}.False', 1)

        graph.add_link(vetala_lib_parent1, 'ExecuteContext', vetala_lib_find_pole_vector, 'ExecuteContext', controller)
        graph.add_link(vetala_lib_find_pole_vector, 'ExecuteContext', set_translation, 'ExecutePin', controller)
        graph.add_link('DISPATCH_RigVMDispatch_SwitchInt32', 'Cases.0', for_each, 'ExecuteContext', controller)
        graph.add_link(for_each, 'ExecuteContext', vetala_lib_get_joint_description, 'ExecuteContext', controller)
        graph.add_link(for_each, 'Completed', branch, 'ExecuteContext', controller)
        graph.add_link(vetala_lib_get_joint_description, 'ExecuteContext', vetala_lib_control, 'ExecuteContext', controller)
        graph.add_link(vetala_lib_control, 'ExecuteContext', set_item_metadata, 'ExecuteContext', controller)
        graph.add_link(set_item_metadata, 'ExecuteContext', add, 'ExecuteContext', controller)
        graph.add_link(set_shape_settings, 'ExecutePin', vetala_lib_parent, 'ExecuteContext', controller)
        graph.add_link(vetala_lib_parent, 'ExecuteContext', vetala_lib_parent1, 'ExecuteContext', controller)
        graph.add_link(spawn_null, 'ExecutePin', add1, 'ExecuteContext', controller)
        graph.add_link(add1, 'ExecuteContext', set_item_array_metadata, 'ExecuteContext', controller)
        graph.add_link(set_item_array_metadata, 'ExecuteContext', spawn_bool_animation_channel, 'ExecutePin', controller)
        graph.add_link(spawn_bool_animation_channel, 'ExecutePin', branch1, 'ExecuteContext', controller)
        graph.add_link(branch, 'True', vetala_lib_parent2, 'ExecuteContext', controller)
        graph.add_link(at5, 'Element', vetala_lib_find_pole_vector, 'BoneA', controller)
        graph.add_link(at6, 'Element', vetala_lib_find_pole_vector, 'BoneB', controller)
        graph.add_link(at7, 'Element', vetala_lib_find_pole_vector, 'BoneC', controller)
        graph.add_link(get_pole_vector_offset, 'Value', vetala_lib_find_pole_vector, 'output', controller)
        graph.add_link(vetala_lib_find_pole_vector, 'Transform.Translation', set_translation, 'Value', controller)
        graph.add_link(if5, 'Result', for_each, 'Array', controller)
        graph.add_link(for_each, 'Element', set_item_metadata, 'Item', controller)
        graph.add_link(for_each, 'Element', vetala_lib_control, 'driven', controller)
        graph.add_link(for_each, 'Element', vetala_lib_get_joint_description, 'joint', controller)
        graph.add_link(for_each, 'Element', vetala_lib_get_parent, 'joint', controller)
        graph.add_link(for_each, 'Index', greater, 'A', controller)
        graph.add_link(for_each, 'Index', vetala_lib_control, 'increment', controller)
        graph.add_link(vetala_lib_get_parent, 'Result', vetala_lib_control, 'parent', controller)
        graph.add_link(if1, 'Result', vetala_lib_control, 'description', controller)
        graph.add_link('Entry', 'side', vetala_lib_control, 'side', controller)
        graph.add_link('Entry', 'joint_token', vetala_lib_control, 'joint_token', controller)
        graph.add_link(if3, 'Result', vetala_lib_control, 'sub_count', controller)
        graph.add_link('Entry', 'restrain_numbering', vetala_lib_control, 'restrain_numbering', controller)
        graph.add_link('Entry', 'shape', vetala_lib_control, 'shape', controller)
        graph.add_link('Entry', 'color', vetala_lib_control, 'color', controller)
        graph.add_link('Entry', 'sub_color', vetala_lib_control, 'sub_color', controller)
        graph.add_link('Entry', 'shape_translate', vetala_lib_control, 'translate', controller)
        graph.add_link('Entry', 'shape_rotate', vetala_lib_control, 'rotate', controller)
        graph.add_link('Entry', 'shape_scale', vetala_lib_control, 'scale', controller)
        graph.add_link(get_world, 'Value', vetala_lib_control, 'world', controller)
        graph.add_link(get_mirror, 'Value', vetala_lib_control, 'mirror', controller)
        graph.add_link(vetala_lib_control, 'Last Control', set_item_metadata, 'Value', controller)
        graph.add_link(vetala_lib_control, 'Control', add, 'Element', controller)
        graph.add_link('Entry', 'parent', vetala_lib_get_parent, 'default_parent', controller)
        graph.add_link(equals, 'Result', vetala_lib_get_parent, 'is_top_joint', controller)
        graph.add_link(get_control_layer, 'Value', vetala_lib_get_parent, 'control_layer', controller)
        graph.add_link(get_description, 'Value', vetala_lib_get_joint_description, 'description', controller)
        graph.add_link(get_joint_token, 'Value', vetala_lib_get_joint_description, 'joint_token', controller)
        graph.add_link(vetala_lib_get_joint_description, 'Result', if1, 'True', controller)
        graph.add_link(get_control_layer, 'Value', set_item_metadata, 'Name', controller)
        graph.add_link('Num_1', 'Num', equals, 'A', controller)
        graph.add_link(get_description, 'Value', if1, 'False', controller)
        graph.add_link(get_use_joint_name, 'Value', if1, 'Condition', controller)
        graph.add_link(get_local_controls, 'Value', add, 'Array', controller)
        graph.add_link(get_local_controls1, 'Value', at8, 'Array', controller)
        graph.add_link(get_local_controls1, 'Value', vetala_lib_get_item2, 'Array', controller)
        graph.add_link(get_pole_vector_shape, 'Value', from_string, 'String', controller)
        graph.add_link(from_string, 'Result', shape_exists, 'ShapeName', controller)
        graph.add_link(from_string, 'Result', if2, 'True', controller)
        graph.add_link(shape_exists, 'Result', if2, 'Condition', controller)
        graph.add_link(branch, 'False', set_shape_settings, 'ExecutePin', controller)
        graph.add_link(at2, 'Element', set_shape_settings, 'Item', controller)
        graph.add_link(at1, 'Element', vetala_lib_parent, 'Parent', controller)
        graph.add_link(at2, 'Element', vetala_lib_parent, 'Child', controller)
        graph.add_link(at1, 'Element', vetala_lib_parent1, 'Parent', controller)
        graph.add_link(at3, 'Element', vetala_lib_parent1, 'Child', controller)
        graph.add_link(get_color, 'Value', at, 'Array', controller)
        graph.add_link(get_local_controls2, 'Value', at1, 'Array', controller)
        graph.add_link(at1, 'Element', vetala_lib_parent2, 'Parent', controller)
        graph.add_link(get_local_controls2, 'Value', at2, 'Array', controller)
        graph.add_link(at2, 'Element', set_translation, 'Item', controller)
        graph.add_link(at2, 'Element', spawn_float_animation_channel1, 'Parent', controller)
        graph.add_link(at2, 'Element', vetala_lib_parent2, 'Child', controller)
        graph.add_link(get_local_controls2, 'Value', at3, 'Array', controller)
        graph.add_link(get_shape_scale, 'Value', at4, 'Array', controller)
        graph.add_link(at4, 'Element', multiply, 'A', controller)
        graph.add_link(get_joints, 'Value', at5, 'Array', controller)
        graph.add_link(get_joints, 'Value', at6, 'Array', controller)
        graph.add_link(get_joints, 'Value', at7, 'Array', controller)
        graph.add_link(set_translation, 'ExecutePin', spawn_float_animation_channel1, 'ExecutePin', controller)
        graph.add_link(greater, 'Result', if3, 'Condition', controller)
        graph.add_link('Entry', 'sub_count', if3, 'True', controller)
        graph.add_link(branch, 'Completed', spawn_null, 'ExecutePin', controller)
        graph.add_link(vetala_lib_get_item, 'Element', spawn_null, 'Parent', controller)
        graph.add_link(spawn_null, 'Item', add1, 'Element', controller)
        graph.add_link(get_transform, 'Transform', spawn_null, 'Transform', controller)
        graph.add_link(greater1, 'Result', if4, 'Condition', controller)
        graph.add_link(get_item_array_metadata, 'Value', if4, 'True', controller)

        graph.add_link(at8, 'Element', get_item_array_metadata, 'Item', controller)
        graph.add_link(get_item_array_metadata, 'Value', num, 'Array', controller)
        graph.add_link(vetala_lib_get_item, 'Element', get_transform, 'Item', controller)
        graph.add_link(get_local_ik, 'Value', add1, 'Array', controller)
        graph.add_link(add1, 'Array', set_item_array_metadata, 'Value', controller)
        graph.add_link(num, 'Num', 'Greater_1', 'A', controller)
        graph.add_link(num, 'Num', greater1, 'A', controller)
        graph.add_link(get_joints1, 'Value', vetala_lib_get_item1, 'Array', controller)
        graph.add_link(get_joints1, 'Value', vetala_lib_get_item3, 'Array', controller)
        graph.add_link(vetala_lib_get_item1, 'Element', set_item_array_metadata, 'Item', controller)
        graph.add_link(get_local_ik1, 'Value', 'Return', 'ik', controller)
        graph.add_link(rig_element_key, 'Value', spawn_bool_animation_channel, 'Parent', controller)
        graph.add_link(branch1, 'False', spawn_float_animation_channel, 'ExecutePin', controller)
        graph.add_link(rig_element_key, 'Value', spawn_float_animation_channel, 'Parent', controller)
        graph.add_link(at8, 'Element', rig_element_key, 'Value', controller)

        graph.add_link(num1, 'Num', equals, 'A', controller)
        graph.add_link(num1, 'Num', 'Greater_2', 'A', controller)
        graph.add_link(num1, 'Num', 'Equals_1', 'A', controller)
        graph.add_link('Num_1', 'Num', equals1, 'A', controller)
        graph.add_link(equals1, 'Result', or1, 'A', controller)
        graph.add_link(or1, 'Result', branch, 'Condition', controller)
        graph.add_link(or1, 'Result', branch1, 'Condition', controller)
        graph.add_link('Num_1', 'Num', greater2, 'A', controller)
        graph.add_link(greater2, 'Result', if5, 'Condition', controller)
        graph.add_link(greater2, 'Result', or1, 'B', controller)
        graph.add_link(make_array, 'Array', if5, 'True', controller)

        graph.add_link(vetala_lib_get_item3, 'Element', get_transform1, 'Item', controller)
        graph.add_link(if2, 'Result', set_shape_settings, 'Settings.Name', controller)
        graph.add_link(at, 'Element', set_shape_settings, 'Settings.Color', controller)
        graph.add_link(at8, 'Element', if4, 'False.0', controller)
        graph.add_link(at9, 'Element', make_array, 'Values.0', controller)
        graph.add_link(at10, 'Element', make_array, 'Values.1', controller)
        graph.add_link(multiply, 'Result', set_shape_settings, 'Settings.Transform.Scale3D', controller)

        graph.set_pin(vetala_lib_control, 'scale_offset', '1', controller)
        graph.set_pin(vetala_lib_get_parent, 'in_hierarchy', 'False', controller)
        graph.set_pin(set_item_metadata, 'NameSpace', 'Self', controller)
        graph.set_pin(equals, 'B', '0', controller)
        graph.set_pin(if2, 'False', 'Sphere_Solid', controller)
        graph.set_pin(set_shape_settings, 'Settings', '(bVisible=True,Name="Default",Color=(R=1.000000,G=0.000000,B=0.000000,A=1.000000),Transform=(Rotation=(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=1.000000,Y=1.000000,Z=1.000000)))', controller)
        graph.set_pin(at, 'Index', '0', controller)
        graph.set_pin(at1, 'Index', '0', controller)
        graph.set_pin(at2, 'Index', '1', controller)
        graph.set_pin(at3, 'Index', '2', controller)
        graph.set_pin(at4, 'Index', '0', controller)
        graph.set_pin(multiply, 'B', '(X=0.333,Y=0.333,Z=0.333)', controller)
        graph.set_pin(at5, 'Index', '0', controller)
        graph.set_pin(at6, 'Index', '1', controller)
        graph.set_pin(at7, 'Index', '2', controller)
        graph.set_pin(set_translation, 'Space', 'GlobalSpace', controller)
        graph.set_pin(set_translation, 'bInitial', 'true', controller)
        graph.set_pin(set_translation, 'Weight', '1.000000', controller)
        graph.set_pin(set_translation, 'bPropagateToChildren', 'True', controller)
        graph.set_pin(greater, 'B', '1', controller)
        graph.set_pin(if3, 'False', '0', controller)
        graph.set_pin(spawn_null, 'Name', 'ik', controller)
        graph.set_pin(spawn_null, 'Space', 'GlobalSpace', controller)
        graph.set_pin(if4, 'False', '((Type=None,Name="None"))', controller)
        graph.set_pin(get_item_array_metadata, 'Name', 'Sub', controller)
        graph.set_pin(get_item_array_metadata, 'NameSpace', 'Self', controller)
        graph.set_pin(vetala_lib_get_item, 'index', '-1', controller)
        graph.set_pin(get_transform, 'Space', 'GlobalSpace', controller)
        graph.set_pin(get_transform, 'bInitial', 'False', controller)
        graph.set_pin(greater1, 'B', '0', controller)
        graph.set_pin(vetala_lib_get_item1, 'index', '-1', controller)
        graph.set_pin(set_item_array_metadata, 'Name', 'ik', controller)
        graph.set_pin(set_item_array_metadata, 'NameSpace', 'Self', controller)
        graph.set_pin(spawn_bool_animation_channel, 'Name', 'stretch', controller)
        graph.set_pin(spawn_bool_animation_channel, 'InitialValue', 'False', controller)
        graph.set_pin(spawn_bool_animation_channel, 'MinimumValue', 'False', controller)
        graph.set_pin(spawn_bool_animation_channel, 'MaximumValue', 'True', controller)
        graph.set_pin(spawn_float_animation_channel, 'Name', 'nudge', controller)
        graph.set_pin(spawn_float_animation_channel, 'InitialValue', '0.000000', controller)
        graph.set_pin(spawn_float_animation_channel, 'MinimumValue', '-500.000000', controller)
        graph.set_pin(spawn_float_animation_channel, 'MaximumValue', '500.000000', controller)
        graph.set_pin(spawn_float_animation_channel, 'LimitsEnabled', '(Enabled=(bMinimum=True,bMaximum=True))', controller)
        graph.set_pin(spawn_float_animation_channel1, 'Name', 'lock', controller)
        graph.set_pin(spawn_float_animation_channel1, 'InitialValue', '0.000000', controller)
        graph.set_pin(spawn_float_animation_channel1, 'MinimumValue', '0.000000', controller)
        graph.set_pin(spawn_float_animation_channel1, 'MaximumValue', '1.000000', controller)
        graph.set_pin(spawn_float_animation_channel1, 'LimitsEnabled', '(Enabled=(bMinimum=True,bMaximum=True))', controller)
        graph.set_pin(equals1, 'B', '2', controller)
        graph.set_pin(at8, 'Index', '-1', controller)
        graph.set_pin(greater2, 'B', '3', controller)
        graph.set_pin(make_array, 'Values', '((Type=None,Name="None"),(Type=None,Name="None"))', controller)
        graph.set_pin(at9, 'Index', '0', controller)
        graph.set_pin(at10, 'Index', '-1', controller)
        graph.set_pin(get_transform1, 'Space', 'GlobalSpace', controller)
        graph.set_pin(get_transform1, 'bInitial', 'False', controller)

        current_locals = locals()
        nodes = unreal_lib.graph.filter_nodes(current_locals.values())

        return nodes

    def _build_function_construct_graph(self):
        controller = self.function_controller
        library = graph.get_local_function_library()

        controller.add_local_variable_from_object_path('local_controls', 'TArray<FRigElementKey>',
                                                                     '/Script/ControlRig.RigElementKey', '')

        controller.add_local_variable_from_object_path('local_ik', 'TArray<FRigElementKey>',
                                                                     '/Script/ControlRig.RigElementKey', '')

        nodes = self._build_controls(controller, library)

        nodes = list(set(nodes))

        node = unreal_lib.graph.comment_nodes(nodes, controller, 'Construction')
        nodes.append(node)
        unreal_lib.graph.move_nodes(500, -2000, nodes, controller)

    def _build_function_forward_graph(self):

        controller = self.function_controller
        library = graph.get_local_function_library()

        set_local_ik = controller.add_variable_node_from_object_path('local_ik', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', False, '()', unreal.Vector2D(4055.418212890625, 1666.9405517578125), 'Set local_ik')
        at = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(704.0, 1472.0), 'At')
        at1 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(728.0, 1726.0), 'At')
        at2 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(760.0, 1976.0), 'At')
        get_item_metadata = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(1024.0, 1616.0), 'Get Item Metadata')
        get_control_layer = controller.add_variable_node('control_layer', 'FName', None, True, '', unreal.Vector2D(672.0, 1640.0), 'Get control_layer')
        basic_ik = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_TwoBoneIKSimplePerItem', 'Execute', unreal.Vector2D(3416.0, 1448.0), 'Basic IK')
        get_transform = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetTransform', 'Execute', unreal.Vector2D(1728.0, 1568.0), 'Get Transform')
        vetala_lib_find_bone_aim_axis = controller.add_function_reference_node(library.find_function('vetalaLib_findBoneAimAxis'), unreal.Vector2D(2616.0, 1288.0), 'vetalaLib_findBoneAimAxis')
        draw_line = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_DebugLineNoSpace', 'Execute', unreal.Vector2D(3816.0, 1608.0), 'Draw Line')
        get_transform1 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetTransform', 'Execute', unreal.Vector2D(1416.0, 1784.0), 'Get Transform')
        project_to_new_parent = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_ProjectTransformToNewParent', 'Execute', unreal.Vector2D(2016.0, 1944.0), 'Project to new Parent')
        vetala_lib_get_item = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(1648.0, 2088.0), 'vetalaLib_GetItem')
        get_item_array_metadata = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(1264.0, 2072.0), 'Get Item Array Metadata')
        vetala_lib_ik_nudge_lock = controller.add_function_reference_node(library.find_function('vetalaLib_IK_NudgeLock'), unreal.Vector2D(2968.0, 1432.0), 'vetalaLib_IK_NudgeLock')
        get_item_metadata1 = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(784.0, 1088.0), 'Get Item Metadata')
        get_bool_channel = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetBoolAnimationChannel', 'Execute', unreal.Vector2D(1608.0, 2232.0), 'Get Bool Channel')
        get_item_metadata2 = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(632.0, 2120.0), 'Get Item Metadata')
        item = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_Item', 'Execute', unreal.Vector2D(1236.0, 2320.0), 'Item')
        get_float_channel = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetFloatAnimationChannel', 'Execute', unreal.Vector2D(1608.0, 2392.0), 'Get Float Channel')
        item1 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_Item', 'Execute', unreal.Vector2D(1224.0, 2456.0), 'Item')
        item2 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_Item', 'Execute', unreal.Vector2D(1752.0, 1400.0), 'Item')
        get_float_channel1 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetFloatAnimationChannel', 'Execute', unreal.Vector2D(2168.0, 1416.0), 'Get Float Channel')
        get_item_metadata3 = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(600.0, 2392.0), 'Get Item Metadata')
        if1 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(1000.0, 2483.0), 'If')
        num = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetNum(in Array,out Num)', unreal.Vector2D(1192.0, 664.0), 'Num')
        branch = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_ControlFlowBranch', 'Execute', unreal.Vector2D(1784.0, 600.0), 'Branch')
        equals = controller.add_template_node('DISPATCH_RigVMDispatch_CoreEquals(in A,in B,out Result)', unreal.Vector2D(1400.0, 664.0), 'Equals')
        basic_fabrik = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_FABRIKItemArray', 'Execute', unreal.Vector2D(4056.0, 648.0), 'Basic FABRIK')
        get_joints = controller.add_variable_node_from_object_path('joints', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(3040.0, 1120.0), 'Get joints')
        vetala_lib_get_item1 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(3432.0, 1016.0), 'vetalaLib_GetItem')
        vetala_lib_get_item2 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(3432.0, 1160.0), 'vetalaLib_GetItem')
        set_transform = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_SetTransform', 'Execute', unreal.Vector2D(2976.0, 720.0), 'Set Transform')
        get_transform2 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetTransform', 'Execute', unreal.Vector2D(2456.0, 728.0), 'Get Transform')
        rotation_constraint = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_RotationConstraintLocalSpaceOffset', 'Execute', unreal.Vector2D(4008.0, 1112.0), 'Rotation Constraint')
        greater = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathIntGreater', 'Execute', unreal.Vector2D(1400.0, 776.0), 'Greater')
        or1 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathBoolOr', 'Execute', unreal.Vector2D(1640.0, 744.0), 'Or')
        vetala_lib_constrain_transform = controller.add_function_reference_node(library.find_function('vetalaLib_ConstrainTransform'), unreal.Vector2D(1296.0, 960.0), 'vetalaLib_ConstrainTransform')

        controller.resolve_wild_card_pin(f'{at.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{at1.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{at2.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{if1.get_node_path()}.Result', 'FRigElementKey', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{num.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{equals.get_node_path()}.A', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{equals.get_node_path()}.B', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{greater.get_node_path()}.A', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{greater.get_node_path()}.B', 'int32', 'None')

        controller.set_array_pin_size(f'{n(vetala_lib_ik_nudge_lock)}.joints', 3)
        controller.set_array_pin_size(f'{n(vetala_lib_ik_nudge_lock)}.controls', 3)
        controller.set_array_pin_size(f'{n(rotation_constraint)}.Parents', 1)

        graph.add_link(draw_line, 'ExecutePin', set_local_ik, 'ExecuteContext', controller)
        graph.add_link(vetala_lib_ik_nudge_lock, 'ExecuteContext', basic_ik, 'ExecutePin', controller)
        graph.add_link(branch, 'False', vetala_lib_find_bone_aim_axis, 'ExecuteContext', controller)
        graph.add_link(vetala_lib_find_bone_aim_axis, 'ExecuteContext', vetala_lib_ik_nudge_lock, 'ExecuteContext', controller)
        graph.add_link(vetala_lib_constrain_transform, 'ExecuteContext', branch, 'ExecuteContext', controller)
        graph.add_link('DISPATCH_RigVMDispatch_SwitchInt32', 'Cases.1', vetala_lib_constrain_transform, 'ExecuteContext', controller)
        graph.add_link(get_item_array_metadata, 'Value', set_local_ik, 'Value', controller)
        graph.add_link('Entry', 'joints', at, 'Array', controller)
        graph.add_link(at, 'Element', basic_ik, 'ItemA', controller)
        graph.add_link(at, 'Element', vetala_lib_find_bone_aim_axis, 'Bone', controller)
        graph.add_link(at, 'Element', get_item_metadata1, 'Item', controller)
        graph.add_link(at, 'Element', vetala_lib_constrain_transform, 'TargetTransform', controller)
        graph.add_link('Entry', 'joints', at1, 'Array', controller)
        graph.add_link(at1, 'Element', basic_ik, 'ItemB', controller)
        graph.add_link(at1, 'Element', get_item_metadata, 'Item', controller)
        graph.add_link(at1, 'Element', get_transform1, 'Item', controller)
        graph.add_link('Entry', 'joints', at2, 'Array', controller)
        graph.add_link(at2, 'Element', basic_ik, 'EffectorItem', controller)
        graph.add_link(at2, 'Element', get_item_array_metadata, 'Item', controller)
        graph.add_link(at2, 'Element', project_to_new_parent, 'Child', controller)
        graph.add_link(at2, 'Element', get_item_metadata2, 'Item', controller)
        graph.add_link(get_control_layer, 'Value', get_item_metadata, 'Name', controller)
        graph.add_link(get_item_metadata, 'Value', get_transform, 'Item', controller)
        graph.add_link(get_item_metadata, 'Value', 'Item_2', 'Item', controller)
        graph.add_link(get_control_layer, 'Value', get_item_metadata1, 'Name', controller)
        graph.add_link(get_control_layer, 'Value', get_item_metadata2, 'Name', controller)
        graph.add_link(basic_ik, 'ExecutePin', draw_line, 'ExecutePin', controller)
        graph.add_link(project_to_new_parent, 'Transform', basic_ik, 'Effector', controller)
        graph.add_link(vetala_lib_find_bone_aim_axis, 'Result', basic_ik, 'PrimaryAxis', controller)
        graph.add_link(get_transform, 'Transform.Translation', basic_ik, 'PoleVector', controller)
        graph.add_link(get_bool_channel, 'Value', basic_ik, 'bEnableStretch', controller)
        graph.add_link(vetala_lib_ik_nudge_lock, 'scale1', basic_ik, 'ItemALength', controller)
        graph.add_link(vetala_lib_ik_nudge_lock, 'scale2', basic_ik, 'ItemBLength', controller)
        graph.add_link(get_transform, 'Transform.Translation', draw_line, 'B', controller)
        graph.add_link(get_transform1, 'Transform.Translation', draw_line, 'A', controller)
        graph.add_link(vetala_lib_get_item, 'Element', project_to_new_parent, 'OldParent', controller)
        graph.add_link(vetala_lib_get_item, 'Element', project_to_new_parent, 'NewParent', controller)
        graph.add_link(project_to_new_parent, 'Transform', basic_fabrik, 'EffectorTransform', controller)
        graph.add_link(get_item_array_metadata, 'Value', vetala_lib_get_item, 'Array', controller)
        graph.add_link(get_float_channel, 'Value', vetala_lib_ik_nudge_lock, 'nudge', controller)
        graph.add_link(get_float_channel1, 'Value', vetala_lib_ik_nudge_lock, 'lock', controller)
        graph.add_link(get_item_metadata1, 'Value', vetala_lib_constrain_transform, 'SourceTransform', controller)
        graph.add_link(get_item_metadata1, 'Value', 'Get Transform_4', 'Item', controller)
        graph.add_link(item, 'Item.Name', get_bool_channel, 'Control', controller)
        graph.add_link(get_bool_channel, 'Value', basic_fabrik, 'bSetEffectorTransform', controller)
        graph.add_link(get_item_metadata2, 'Value', 'Get Item Metadata_3', 'Item', controller)
        graph.add_link(get_item_metadata2, 'Value', if1, 'False', controller)
        graph.add_link('If_5', 'Result', item, 'Item', controller)
        graph.add_link(item1, 'Item.Name', get_float_channel, 'Control', controller)
        graph.add_link('If_5', 'Result', item1, 'Item', controller)
        graph.add_link(get_item_metadata, 'Value', item2, 'Item', controller)
        graph.add_link(item2, 'Item.Name', get_float_channel1, 'Control', controller)
        graph.add_link(get_item_metadata2, 'Value', get_item_metadata3, 'Item', controller)
        graph.add_link(get_item_metadata3, 'Value', if1, 'True', controller)
        graph.add_link(get_item_metadata3, 'Found', if1, 'Condition', controller)
        graph.add_link(if1, 'Result', item, 'Item', controller)
        graph.add_link(if1, 'Result', 'Item_1', 'Item', controller)
        graph.add_link('Entry', 'joints', num, 'Array', controller)
        graph.add_link(num, 'Num', equals, 'A', controller)
        graph.add_link(num, 'Num', greater, 'A', controller)
        graph.add_link(or1, 'Result', branch, 'Condition', controller)
        graph.add_link(branch, 'True', set_transform, 'ExecutePin', controller)
        graph.add_link(equals, 'Result', or1, 'A', controller)
        graph.add_link(set_transform, 'ExecutePin', basic_fabrik, 'ExecutePin', controller)
        graph.add_link(basic_fabrik, 'ExecutePin', rotation_constraint, 'ExecutePin', controller)
        graph.add_link('Entry', 'joints', basic_fabrik, 'Items', controller)
        graph.add_link(get_joints, 'Value', vetala_lib_get_item1, 'Array', controller)
        graph.add_link(get_joints, 'Value', vetala_lib_get_item2, 'Array', controller)
        graph.add_link(vetala_lib_get_item1, 'Element', 'Set Transform', 'Item', controller)
        graph.add_link(vetala_lib_get_item2, 'Element', rotation_constraint, 'Child', controller)
        graph.add_link('vetalaLib_GetItem_5', 'Element', set_transform, 'Item', controller)
        graph.add_link(get_transform2, 'Transform', set_transform, 'Value', controller)
        graph.add_link(get_item_metadata1, 'Value', get_transform2, 'Item', controller)
        graph.add_link(greater, 'Result', or1, 'B', controller)
        graph.add_link(at, 'Element', vetala_lib_ik_nudge_lock, 'joints.0', controller)
        graph.add_link(at1, 'Element', vetala_lib_ik_nudge_lock, 'joints.1', controller)
        graph.add_link(at2, 'Element', vetala_lib_ik_nudge_lock, 'joints.2', controller)
        graph.add_link(get_item_metadata, 'Value', vetala_lib_ik_nudge_lock, 'controls.1', controller)
        graph.add_link(vetala_lib_get_item, 'Element', vetala_lib_ik_nudge_lock, 'controls.2', controller)
        graph.add_link(get_item_metadata1, 'Value', vetala_lib_ik_nudge_lock, 'controls.0', controller)
        graph.add_link(vetala_lib_get_item, 'Element', rotation_constraint, 'Parents.0.Item', controller)

        graph.set_pin(at, 'Index', '0', controller)
        graph.set_pin(at1, 'Index', '1', controller)
        graph.set_pin(at2, 'Index', '-1', controller)
        graph.set_pin(get_item_metadata, 'NameSpace', 'Self', controller)
        graph.set_pin(get_item_metadata, 'Default', '(Type=Bone,Name="None")', controller)
        graph.set_pin(basic_ik, 'SecondaryAxis', '(X=0.000000,Y=0.000000,Z=0.000000)', controller)
        graph.set_pin(basic_ik, 'SecondaryAxisWeight', '1.000000', controller)
        graph.set_pin(basic_ik, 'PoleVectorKind', 'Direction', controller)
        graph.set_pin(basic_ik, 'PoleVectorSpace', '(Type=Bone,Name="None")', controller)
        graph.set_pin(basic_ik, 'StretchStartRatio', '1.000000', controller)
        graph.set_pin(basic_ik, 'StretchMaximumRatio', '10.000000', controller)
        graph.set_pin(basic_ik, 'Weight', '1.000000', controller)
        graph.set_pin(basic_ik, 'bPropagateToChildren', 'True', controller)
        graph.set_pin(basic_ik, 'DebugSettings', '(bEnabled=False,Scale=10.000000,WorldOffset=(Rotation=(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=1.000000,Y=1.000000,Z=1.000000)))', controller)
        graph.set_pin(get_transform, 'Space', 'GlobalSpace', controller)
        graph.set_pin(get_transform, 'bInitial', 'False', controller)
        graph.set_pin(draw_line, 'DebugDrawSettings', '(DepthPriority=SDPG_Foreground,Lifetime=-1.000000)', controller)
        graph.set_pin(draw_line, 'Color', '(R=0.05,G=0.05,B=0.05,A=1.000000)', controller)
        graph.set_pin(draw_line, 'Thickness', '0.000000', controller)
        graph.set_pin(draw_line, 'WorldOffset', '(Rotation=(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=1.000000,Y=1.000000,Z=1.000000))', controller)
        graph.set_pin(draw_line, 'bEnabled', 'True', controller)
        graph.set_pin(get_transform1, 'Space', 'GlobalSpace', controller)
        graph.set_pin(get_transform1, 'bInitial', 'False', controller)
        graph.set_pin(project_to_new_parent, 'bChildInitial', 'True', controller)
        graph.set_pin(project_to_new_parent, 'bOldParentInitial', 'True', controller)
        graph.set_pin(project_to_new_parent, 'bNewParentInitial', 'False', controller)
        graph.set_pin(vetala_lib_get_item, 'index', '-1', controller)
        graph.set_pin(get_item_array_metadata, 'Name', 'ik', controller)
        graph.set_pin(get_item_array_metadata, 'NameSpace', 'Self', controller)
        graph.set_pin(vetala_lib_ik_nudge_lock, 'joints', '((Type=None,Name="None"),(Type=None,Name="None"),(Type=None,Name="None"))', controller)
        graph.set_pin(vetala_lib_ik_nudge_lock, 'controls', '((Type=None,Name="None"),(Type=None,Name="None"),(Type=None,Name="None"))', controller)
        graph.set_pin(get_item_metadata1, 'NameSpace', 'Self', controller)
        graph.set_pin(get_item_metadata1, 'Default', '(Type=Bone,Name="None")', controller)
        graph.set_pin(get_bool_channel, 'Channel', 'stretch', controller)
        graph.set_pin(get_bool_channel, 'bInitial', 'False', controller)
        graph.set_pin(get_item_metadata2, 'NameSpace', 'Self', controller)
        graph.set_pin(get_item_metadata2, 'Default', '(Type=Bone,Name="None")', controller)
        graph.set_pin(get_float_channel, 'Channel', 'nudge', controller)
        graph.set_pin(get_float_channel, 'bInitial', 'False', controller)
        graph.set_pin(get_float_channel1, 'Channel', 'lock', controller)
        graph.set_pin(get_float_channel1, 'bInitial', 'False', controller)
        graph.set_pin(get_item_metadata3, 'Name', 'main', controller)
        graph.set_pin(get_item_metadata3, 'NameSpace', 'Self', controller)
        graph.set_pin(get_item_metadata3, 'Default', '(Type=Bone,Name="None")', controller)
        graph.set_pin(equals, 'B', '2', controller)
        graph.set_pin(basic_fabrik, 'Precision', '0.010000', controller)
        graph.set_pin(basic_fabrik, 'Weight', '1.000000', controller)
        graph.set_pin(basic_fabrik, 'bPropagateToChildren', 'True', controller)
        graph.set_pin(basic_fabrik, 'MaxIterations', '100', controller)
        graph.set_pin(basic_fabrik, 'WorkData', '(CachedEffector=(Key=(Type=None,Name="None"),Index=65535,ContainerVersion=-1))', controller)
        graph.set_pin(vetala_lib_get_item2, 'index', '-1', controller)
        graph.set_pin(set_transform, 'Space', 'GlobalSpace', controller)
        graph.set_pin(set_transform, 'bInitial', 'False', controller)
        graph.set_pin(set_transform, 'Weight', '1.000000', controller)
        graph.set_pin(set_transform, 'bPropagateToChildren', 'True', controller)
        graph.set_pin(get_transform2, 'Space', 'GlobalSpace', controller)
        graph.set_pin(get_transform2, 'bInitial', 'False', controller)
        graph.set_pin(rotation_constraint, 'bMaintainOffset', 'True', controller)
        graph.set_pin(rotation_constraint, 'Filter', '(bX=True,bY=True,bZ=True)', controller)
        graph.set_pin(rotation_constraint, 'Parents', '((Item=(Type=Bone,Name="None"),Weight=1.000000))', controller)
        graph.set_pin(rotation_constraint, 'AdvancedSettings', '(InterpolationType=Average,RotationOrderForFilter=XZY)', controller)
        graph.set_pin(rotation_constraint, 'Weight', '1.000000', controller)
        graph.set_pin(greater, 'B', '3', controller)

        current_locals = locals()
        nodes = unreal_lib.graph.filter_nodes(current_locals.values())
        node = unreal_lib.graph.comment_nodes(nodes, controller, 'Forward Solve')

        nodes.append(node)
        unreal_lib.graph.move_nodes(0, 0, nodes, controller)
        unreal_lib.graph.move_nodes(500, 500, nodes, controller)

    def _build_function_backward_graph(self):
        return


class UnrealSplineIkRig(UnrealUtilRig):

    def _build_function_construct_graph(self):

        controller = self.function_controller
        library = graph.get_local_function_library()

        controller.add_local_variable_from_object_path('spline_controls',
                                                       'TArray<FRigElementKey>',
                                                       '/Script/ControlRig.RigElementKey', '')

        controller.add_local_variable_from_object_path('first_control', 'FRigElementKey', '/Script/ControlRig.RigElementKey', '')
        controller.add_local_variable_from_object_path('last_control', 'FRigElementKey', '/Script/ControlRig.RigElementKey', '')

        spline_from_items = controller.add_external_function_reference_node('/ControlRigSpline/SplineFunctionLibrary/SplineFunctionLibrary.SplineFunctionLibrary_C', 'SplineFromItems', unreal.Vector2D(1600.0, -2900.0), 'SplineFromItems')
        get_joints = controller.add_variable_node_from_object_path('joints', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(1100.0, -1160.0), 'Get joints')
        get_control_count = controller.add_variable_node('control_count', 'int32', None, True, '', unreal.Vector2D(1100.0, -2200.0), 'Get control_count')
        get_hierarchy = controller.add_variable_node('hierarchy', 'bool', None, True, '', unreal.Vector2D(1100.0, -2060.0), 'Get hierarchy')
        get_parent = controller.add_variable_node_from_object_path('parent', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(1100.0, -1760.0), 'Get parent')
        get_last_control = controller.add_variable_node_from_object_path('last_control', 'FRigElementKey', '/Script/ControlRig.RigElementKey', True, '', unreal.Vector2D(1100.0, -1900.0), 'Get last_control')
        for_loop = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_ForLoopCount', 'Execute', unreal.Vector2D(2304.0, -2400.0), 'For Loop')
        greater = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathIntGreater', 'Execute', unreal.Vector2D(1552.0, -2112.0), 'Greater')
        if1 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(1936.0, -2272.0), 'If')
        num = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetNum(in Array,out Num)', unreal.Vector2D(1800.0, -1900.0), 'Num')
        greater1 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathIntGreater', 'Execute', unreal.Vector2D(2000.0, -1900.0), 'Greater')
        if2 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(2224.0, -1808.0), 'If')
        position_from_spline = controller.add_unit_node_from_struct_path('/Script/ControlRigSpline.RigUnit_PositionFromControlRigSpline', 'Execute', unreal.Vector2D(2800.0, -2500.0), 'Position From Spline')
        make_transform = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathTransformMake', 'Execute', unreal.Vector2D(3100.0, -2500.0), 'Make Transform')
        spawn_null = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyAddNull', 'Execute', unreal.Vector2D(3500.0, -2500.0), 'Spawn Null')
        set_default_parent = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_SetDefaultParent', 'Execute', unreal.Vector2D(4736.0, -1696.0), 'Set Default Parent')
        get_spline_controls = controller.add_variable_node_from_object_path('spline_controls', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(5312.0, -1856.0), 'Get spline_controls')
        at = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(5200.0, -1160.0), 'At')
        add = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayAdd(io Array,in Element,out Index)', unreal.Vector2D(5552.0, -1680.0), 'Add')
        set_item_array_metadata = controller.add_template_node('DISPATCH_RigDispatch_SetMetadata(in Item,in Name,in NameSpace,in Value,out Success)', unreal.Vector2D(6128.0, -1488.0), 'Set Item Array Metadata')
        at1 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(6576.0, -1616.0), 'At')
        spawn_bool_animation_channel = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyAddAnimationChannelBool', 'Execute', unreal.Vector2D(6900.0, -1500.0), 'Spawn Bool Animation Channel')
        get_spline_controls1 = controller.add_variable_node_from_object_path('spline_controls', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(5808.0, -1264.0), 'Get spline_controls')
        vetala_lib_get_item = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(1792.0, -1760.0), 'vetalaLib_GetItem')
        vetala_lib_control = self._create_control(controller, 4224.0, -2000.0)
        branch = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_ControlFlowBranch', 'Execute', unreal.Vector2D(4128.0, -2272.0), 'Branch')
        add1 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayAdd(io Array,in Element,out Index)', unreal.Vector2D(5696.0, -2352.0), 'Add')
        set_default_parent1 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_SetDefaultParent', 'Execute', unreal.Vector2D(5248.0, -2656.0), 'Set Default Parent')
        get_spline_controls2 = controller.add_variable_node_from_object_path('spline_controls', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(5456.0, -2272.0), 'Get spline_controls')
        spawn_null1 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyAddNull', 'Execute', unreal.Vector2D(4672.0, -2672.0), 'Spawn Null')
        equals = controller.add_template_node('DISPATCH_RigVMDispatch_CoreEquals(in A,in B,out Result)', unreal.Vector2D(6048.0, -1888.0), 'Equals')
        branch1 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_ControlFlowBranch', 'Execute', unreal.Vector2D(6288.0, -1872.0), 'Branch')
        set_first_control = controller.add_variable_node_from_object_path('first_control', 'FRigElementKey', '/Script/ControlRig.RigElementKey', False, '', unreal.Vector2D(6496.0, -2016.0), 'Set first_control')
        branch2 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_ControlFlowBranch', 'Execute', unreal.Vector2D(6448.0, -2432.0), 'Branch')
        get_first_control = controller.add_variable_node_from_object_path('first_control', 'FRigElementKey', '/Script/ControlRig.RigElementKey', True, '', unreal.Vector2D(6640.0, -2304.0), 'Get first_control')
        set_default_parent2 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_SetDefaultParent', 'Execute', unreal.Vector2D(6880.0, -2432.0), 'Set Default Parent')
        set_last_control = controller.add_variable_node_from_object_path('last_control', 'FRigElementKey', '/Script/ControlRig.RigElementKey', False, '', unreal.Vector2D(7040.0, -1792.0), 'Set last_control')
        if3 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(3904.0, -1680.0), 'If')
        get_last_control1 = controller.add_variable_node_from_object_path('last_control', 'FRigElementKey', '/Script/ControlRig.RigElementKey', True, '', unreal.Vector2D(4304.0, -2672.0), 'Get last_control')
        remap = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathDoubleRemap', 'Execute', unreal.Vector2D(2592.0, -2208.0), 'Remap')
        subtract = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathIntSub', 'Execute', unreal.Vector2D(2256.0, -2144.0), 'Subtract')
        to_float = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathIntToFloat', 'Execute', unreal.Vector2D(2464.0, -2080.0), 'To Float')
        to_int = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathDoubleToInt', 'Execute', unreal.Vector2D(2800.0, -2160.0), 'To Int')
        if4 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(3616.0, -1888.0), 'If')
        set_last_control1 = controller.add_variable_node_from_object_path('last_control', 'FRigElementKey', '/Script/ControlRig.RigElementKey', False, '', unreal.Vector2D(1136.871337890625, -2687.92822265625), 'Set last_control')
        equals1 = controller.add_template_node('DISPATCH_RigVMDispatch_CoreEquals(in A,in B,out Result)', unreal.Vector2D(3104.0, -1728.0), 'Equals')
        equals2 = controller.add_template_node('DISPATCH_RigVMDispatch_CoreEquals(in A,in B,out Result)', unreal.Vector2D(3104.0, -2144.0), 'Equals')
        equals3 = controller.add_template_node('DISPATCH_RigVMDispatch_CoreEquals(in A,in B,out Result)', unreal.Vector2D(3104.0, -2288.0), 'Equals')
        and1 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathBoolAnd', 'Execute', unreal.Vector2D(3584.0, -2144.0), 'And')
        or1 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathBoolOr', 'Execute', unreal.Vector2D(3312.0, -2208.0), 'Or')
        and2 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathBoolAnd', 'Execute', unreal.Vector2D(3376.0, -1728.0), 'And')
        equals4 = controller.add_template_node('DISPATCH_RigVMDispatch_CoreEquals(in A,in B,out Result)', unreal.Vector2D(3104.0, -1888.0), 'Equals')
        get_local_controls = controller.add_variable_node_from_object_path('local_controls', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(5680.0, -1840.0), 'Get local_controls')
        add2 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayAdd(io Array,in Element,out Index)', unreal.Vector2D(5872.0, -1680.0), 'Add')
        get_local_controls1 = controller.add_variable_node_from_object_path('local_controls', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(6304.0, -1632.0), 'Get local_controls')
        get_transform = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetTransform', 'Execute', unreal.Vector2D(4375.7724609375, -2336.9208984375), 'Get Transform')

        controller.resolve_wild_card_pin(f'{greater.get_node_path()}.A', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{greater.get_node_path()}.B', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{if1.get_node_path()}.Result', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{num.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{greater1.get_node_path()}.A', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{greater1.get_node_path()}.B', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{if2.get_node_path()}.Result', 'FRigElementKey', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{at.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{add.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{at1.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{add1.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{equals.get_node_path()}.A', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{equals.get_node_path()}.B', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{if3.get_node_path()}.Result', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{if4.get_node_path()}.Result', 'FRigElementKey', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{equals1.get_node_path()}.A', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{equals1.get_node_path()}.B', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{equals2.get_node_path()}.A', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{equals2.get_node_path()}.B', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{equals3.get_node_path()}.A', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{equals3.get_node_path()}.B', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{equals4.get_node_path()}.A', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{equals4.get_node_path()}.B', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{add2.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')

        graph.add_link(set_last_control1, 'ExecuteContext', spline_from_items, 'ExecuteContext', controller)
        graph.add_link(spline_from_items, 'ExecuteContext', for_loop, 'ExecutePin', controller)
        graph.add_link(for_loop, 'Completed', set_item_array_metadata, 'ExecuteContext', controller)
        graph.add_link(spawn_null, 'ExecutePin', branch, 'ExecuteContext', controller)
        graph.add_link(vetala_lib_control, 'ExecuteContext', set_default_parent, 'ExecutePin', controller)
        graph.add_link(set_default_parent, 'ExecutePin', add, 'ExecuteContext', controller)
        graph.add_link(add, 'ExecuteContext', add2, 'ExecuteContext', controller)
        graph.add_link(set_item_array_metadata, 'ExecuteContext', spawn_bool_animation_channel, 'ExecutePin', controller)
        graph.add_link(branch, 'False', vetala_lib_control, 'ExecuteContext', controller)
        graph.add_link(set_default_parent1, 'ExecutePin', add1, 'ExecuteContext', controller)
        graph.add_link(add1, 'ExecuteContext', branch2, 'ExecuteContext', controller)
        graph.add_link(add2, 'ExecuteContext', branch1, 'ExecuteContext', controller)
        graph.add_link(branch1, 'True', set_first_control, 'ExecuteContext', controller)
        graph.add_link(branch1, 'Completed', set_last_control, 'ExecuteContext', controller)
        graph.add_link('DISPATCH_RigVMDispatch_SwitchInt32', 'Cases.0', set_last_control1, 'ExecuteContext', controller)
        graph.add_link(get_joints, 'Value', spline_from_items, 'Items', controller)
        graph.add_link(spline_from_items, 'Spline', position_from_spline, 'Spline', controller)
        graph.add_link(get_joints, 'Value', at, 'Array', controller)
        graph.add_link(get_control_count, 'Value', greater, 'A', controller)
        graph.add_link(get_control_count, 'Value', if1, 'True', controller)
        graph.add_link(get_control_count, 'Value', equals1, 'A', controller)
        graph.add_link(get_hierarchy, 'Value', if4, 'Condition', controller)
        graph.add_link(get_parent, 'Value', num, 'Array', controller)
        graph.add_link(get_parent, 'Value', vetala_lib_get_item, 'Array', controller)
        graph.add_link(get_last_control, 'Value', if4, 'True', controller)
        graph.add_link(for_loop, 'ExecutePin', spawn_null, 'ExecutePin', controller)
        graph.add_link(if1, 'Result', for_loop, 'Count', controller)
        graph.add_link(for_loop, 'Index', equals, 'A', controller)
        graph.add_link(for_loop, 'Index', equals2, 'A', controller)
        graph.add_link(for_loop, 'Index', equals3, 'A', controller)
        graph.add_link(for_loop, 'Index', equals4, 'A', controller)
        graph.add_link(for_loop, 'Ratio', position_from_spline, 'U', controller)
        graph.add_link(for_loop, 'Ratio', remap, 'Value', controller)
        graph.add_link(greater, 'Result', if1, 'Condition', controller)
        graph.add_link(if1, 'Result', subtract, 'A', controller)
        graph.add_link(num, 'Num', 'Greater_1', 'A', controller)
        graph.add_link(num, 'Num', greater1, 'A', controller)
        graph.add_link(greater1, 'Result', if2, 'Condition', controller)
        graph.add_link(vetala_lib_get_item, 'Element', if2, 'True', controller)
        graph.add_link(if2, 'Result', if4, 'False', controller)
        graph.add_link(if2, 'Result', set_last_control1, 'Value', controller)
        graph.add_link(position_from_spline, 'Position', make_transform, 'Translation', controller)
        graph.add_link(make_transform, 'Result', spawn_null, 'Transform', controller)
        graph.add_link(spawn_null, 'Item', set_default_parent, 'Child', controller)
        graph.add_link(spawn_null, 'Item', vetala_lib_control, 'driven', controller)
        graph.add_link(spawn_null, 'Item', add1, 'Element', controller)
        graph.add_link(spawn_null, 'Item', set_default_parent1, 'Child', controller)
        graph.add_link(spawn_null, 'Item', add, 'Element', controller)
        graph.add_link(spawn_null, 'Item', get_transform, 'Item', controller)
        graph.add_link(vetala_lib_control, 'Control', set_default_parent, 'Parent', controller)
        graph.add_link(get_spline_controls, 'Value', add, 'Array', controller)
        graph.add_link(at, 'Element', set_item_array_metadata, 'Item', controller)
        graph.add_link(get_spline_controls1, 'Value', set_item_array_metadata, 'Value', controller)
        graph.add_link(get_local_controls1, 'Value', at1, 'Array', controller)
        graph.add_link(at1, 'Element', spawn_bool_animation_channel, 'Parent', controller)
        graph.add_link(if3, 'Result', vetala_lib_control, 'increment', controller)
        graph.add_link(if4, 'Result', vetala_lib_control, 'parent', controller)
        graph.add_link('Entry', 'description', vetala_lib_control, 'description', controller)
        graph.add_link('Entry', 'side', vetala_lib_control, 'side', controller)
        graph.add_link('Entry', 'sub_count', vetala_lib_control, 'sub_count', controller)
        graph.add_link('Entry', 'restrain_numbering', vetala_lib_control, 'restrain_numbering', controller)
        graph.add_link('Entry', 'shape', vetala_lib_control, 'shape', controller)
        graph.add_link('Entry', 'color', vetala_lib_control, 'color', controller)
        graph.add_link('Entry', 'sub_color', vetala_lib_control, 'sub_color', controller)
        graph.add_link('Entry', 'shape_translate', vetala_lib_control, 'translate', controller)
        graph.add_link('Entry', 'shape_rotate', vetala_lib_control, 'rotate', controller)
        graph.add_link('Entry', 'shape_scale', vetala_lib_control, 'scale', controller)
        graph.add_link(vetala_lib_control, 'Control', set_first_control, 'Value', controller)
        graph.add_link(vetala_lib_control, 'Control', set_last_control, 'Value', controller)
        graph.add_link(vetala_lib_control, 'Control', add2, 'Element', controller)
        graph.add_link(and1, 'Result', branch, 'Condition', controller)
        graph.add_link(branch, 'True', spawn_null1, 'ExecutePin', controller)
        graph.add_link(get_spline_controls2, 'Value', add1, 'Array', controller)
        graph.add_link(spawn_null1, 'ExecutePin', set_default_parent1, 'ExecutePin', controller)
        graph.add_link(spawn_null1, 'Item', set_default_parent1, 'Parent', controller)
        graph.add_link(get_last_control1, 'Value', spawn_null1, 'Parent', controller)
        graph.add_link(spawn_null1, 'Item', set_default_parent2, 'Child', controller)
        graph.add_link(get_transform, 'Transform', spawn_null1, 'Transform', controller)
        graph.add_link(equals, 'Result', branch1, 'Condition', controller)
        graph.add_link(branch2, 'True', set_default_parent2, 'ExecutePin', controller)
        graph.add_link(get_first_control, 'Value', set_default_parent2, 'Parent', controller)
        graph.add_link(and2, 'Result', if3, 'Condition', controller)
        graph.add_link(to_int, 'Result', if3, 'False', controller)
        graph.add_link(to_float, 'Result', remap, 'TargetMaximum', controller)
        graph.add_link(remap, 'Result', to_int, 'Value', controller)
        graph.add_link(subtract, 'Result', to_float, 'Value', controller)
        graph.add_link(equals1, 'Result', and1, 'B', controller)
        graph.add_link(equals1, 'Result', and2, 'B', controller)
        graph.add_link(equals2, 'Result', or1, 'B', controller)
        graph.add_link(equals3, 'Result', or1, 'A', controller)
        graph.add_link(or1, 'Result', and1, 'A', controller)
        graph.add_link(equals4, 'Result', and2, 'A', controller)
        graph.add_link(get_local_controls, 'Value', add2, 'Array', controller)

        graph.set_pin(spline_from_items, 'Spline Mode', 'Hermite', controller)
        graph.set_pin(spline_from_items, 'Samples Per Segment', '16', controller)
        graph.set_pin(greater, 'B', '3', controller)
        graph.set_pin(if1, 'False', '4', controller)
        graph.set_pin(greater1, 'B', '0', controller)
        graph.set_pin(make_transform, 'Rotation', '(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000)', controller)
        graph.set_pin(make_transform, 'Scale', '(X=1.000000,Y=1.000000,Z=1.000000)', controller)
        graph.set_pin(spawn_null, 'Parent', '(Type=Bone,Name="None")', controller)
        graph.set_pin(spawn_null, 'Name', 'spline_driver', controller)
        graph.set_pin(spawn_null, 'Space', 'GlobalSpace', controller)
        graph.set_pin(at, 'Index', '0', controller)
        graph.set_pin(set_item_array_metadata, 'Name', 'drivers', controller)
        graph.set_pin(set_item_array_metadata, 'NameSpace', 'Self', controller)
        graph.set_pin(at1, 'Index', '0', controller)
        graph.set_pin(spawn_bool_animation_channel, 'Name', 'stretch', controller)
        graph.set_pin(spawn_bool_animation_channel, 'InitialValue', 'False', controller)
        graph.set_pin(spawn_bool_animation_channel, 'MinimumValue', 'False', controller)
        graph.set_pin(spawn_bool_animation_channel, 'MaximumValue', 'True', controller)
        graph.set_pin(vetala_lib_get_item, 'index', '-1', controller)
        graph.set_pin(vetala_lib_control, 'scale_offset', '1', controller)
        graph.set_pin(spawn_null1, 'Name', 'spline_xform', controller)
        graph.set_pin(spawn_null1, 'Space', 'GlobalSpace', controller)
        graph.set_pin(equals, 'B', '3', controller)
        graph.set_pin(branch2, 'Condition', 'False', controller)
        graph.set_pin(if3, 'True', '1', controller)
        graph.set_pin(remap, 'SourceMinimum', '0.000000', controller)
        graph.set_pin(remap, 'SourceMaximum', '1.000000', controller)
        graph.set_pin(remap, 'TargetMinimum', '0.000000', controller)
        graph.set_pin(remap, 'bClamp', 'False', controller)
        graph.set_pin(subtract, 'B', '1', controller)
        graph.set_pin(equals1, 'B', '2', controller)
        graph.set_pin(equals2, 'B', '3', controller)
        graph.set_pin(equals3, 'B', '1', controller)
        graph.set_pin(equals4, 'B', '2', controller)
        graph.set_pin(get_transform, 'Space', 'GlobalSpace', controller)
        graph.set_pin(get_transform, 'bInitial', 'False', controller)

        current_locals = locals()
        nodes = unreal_lib.graph.filter_nodes(current_locals.values())
        node = unreal_lib.graph.comment_nodes(nodes, controller, 'Construction')

        nodes.append(node)
        unreal_lib.graph.move_nodes(0, 0, nodes, controller)
        unreal_lib.graph.move_nodes(1000, -3000, nodes, controller)

    def _build_function_forward_graph(self):
        controller = self.function_controller
        library = graph.get_local_function_library()

        get_joints = controller.add_variable_node_from_object_path('joints', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(800.0, 100.0), 'Get joints')
        spline_ik = controller.add_external_function_reference_node('/ControlRigSpline/SplineFunctionLibrary/SplineFunctionLibrary.SplineFunctionLibrary_C', 'SplineIK', unreal.Vector2D(2600.0, 100.0), 'SplineIK')
        at = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(900.0, 400.0), 'At')
        vetala_lib_get_item = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(1400.0, 400.0), 'vetalaLib_GetItem')
        get_item_array_metadata = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(1100.0, 400.0), 'Get Item Array Metadata')
        get_bool_channel = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetBoolAnimationChannel', 'Execute', unreal.Vector2D(1700.0, 400.0), 'Get Bool Channel')
        reset = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayReset(io Array)', unreal.Vector2D(900.0, 600.0), 'Reset')
        for_each = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayIterator(in Array,out Element,out Index,out Count,out Ratio)', unreal.Vector2D(1300.0, 600.0), 'For Each')
        add = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayAdd(io Array,in Element,out Index)', unreal.Vector2D(2000.0, 600.0), 'Add')
        get_item_array_metadata1 = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(1500.0, 800.0), 'Get Item Array Metadata')
        num = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetNum(in Array,out Num)', unreal.Vector2D(1500.0, 1000.0), 'Num')
        greater = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathIntGreater', 'Execute', unreal.Vector2D(1700.0, 1000.0), 'Greater')
        if1 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(1900.0, 1000.0), 'If')
        vetala_lib_get_item1 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(1792.0, 672.0), 'vetalaLib_GetItem')
        vetala_lib_find_bone_aim_axis = controller.add_function_reference_node(library.find_function('vetalaLib_findBoneAimAxis'), unreal.Vector2D(1952.0, 128.0), 'vetalaLib_findBoneAimAxis')
        vetala_lib_find_pole_axis = controller.add_function_reference_node(library.find_function('vetalaLib_findPoleAxis'), unreal.Vector2D(1952.0, 256.0), 'vetalaLib_findPoleAxis')
        multiply = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathVectorMul', 'Execute', unreal.Vector2D(2320.0, 128.0), 'Multiply')

        graph.add_link(vetala_lib_find_pole_axis, 'ExecuteContext', spline_ik, 'ExecuteContext', controller)
        graph.add_link('DISPATCH_RigVMDispatch_SwitchInt32', 'Cases.1', reset, 'ExecuteContext', controller)
        graph.add_link(reset, 'ExecuteContext', for_each, 'ExecuteContext', controller)
        graph.add_link(for_each, 'ExecuteContext', add, 'ExecuteContext', controller)
        graph.add_link(for_each, 'Completed', vetala_lib_find_bone_aim_axis, 'ExecuteContext', controller)
        graph.add_link(vetala_lib_find_bone_aim_axis, 'ExecuteContext', vetala_lib_find_pole_axis, 'ExecuteContext', controller)
        graph.add_link(get_joints, 'Value', at, 'Array', controller)
        graph.add_link(get_joints, 'Value', spline_ik, 'Bones', controller)
        graph.add_link(get_joints, 'Value', vetala_lib_find_pole_axis, 'Bones', controller)
        graph.add_link(add, 'Array', spline_ik, 'Controls', controller)
        graph.add_link(get_bool_channel, 'Value', spline_ik, 'Stretch', controller)
        graph.add_link(vetala_lib_find_bone_aim_axis, 'Result', spline_ik, 'Primary Axis', controller)
        graph.add_link(vetala_lib_find_pole_axis, 'PoleAxis', spline_ik, 'Up Axis', controller)
        graph.add_link(multiply, 'Result', spline_ik, 'Secondary Spline Direction', controller)
        graph.add_link(at, 'Element', get_item_array_metadata, 'Item', controller)
        graph.add_link(at, 'Element', vetala_lib_find_bone_aim_axis, 'Bone', controller)
        graph.add_link(get_item_array_metadata, 'Value', vetala_lib_get_item, 'Array', controller)
        graph.add_link(vetala_lib_get_item, 'Element.Name', get_bool_channel, 'Control', controller)
        graph.add_link(get_item_array_metadata, 'Value', for_each, 'Array', controller)
        graph.add_link(reset, 'Array', add, 'Array', controller)
        graph.add_link(for_each, 'Element', get_item_array_metadata1, 'Item', controller)
        graph.add_link(for_each, 'Element', if1, 'False', controller)
        graph.add_link(if1, 'Result', add, 'Element', controller)
        graph.add_link(get_item_array_metadata1, 'Value', vetala_lib_get_item1, 'Array', controller)
        graph.add_link(get_item_array_metadata1, 'Value', num, 'Array', controller)
        graph.add_link(num, 'Num', greater, 'A', controller)
        graph.add_link(greater, 'Result', if1, 'Condition', controller)
        graph.add_link(vetala_lib_get_item1, 'Element', if1, 'True', controller)
        graph.add_link(vetala_lib_find_pole_axis, 'PoleAxis', multiply, 'A', controller)

        graph.set_pin(spline_ik, 'Spline Mode', 'BSpline', controller)
        graph.set_pin(spline_ik, 'Samples Per Segment', '16', controller)
        graph.set_pin(at, 'Index', '0', controller)
        graph.set_pin(vetala_lib_get_item, 'index', '0', controller)
        graph.set_pin(get_item_array_metadata, 'Name', 'drivers', controller)
        graph.set_pin(get_item_array_metadata, 'NameSpace', 'Self', controller)
        graph.set_pin(get_bool_channel, 'Channel', 'stretch', controller)
        graph.set_pin(get_bool_channel, 'bInitial', 'False', controller)
        graph.set_pin(get_item_array_metadata1, 'Name', 'Sub', controller)
        graph.set_pin(get_item_array_metadata1, 'NameSpace', 'Self', controller)
        graph.set_pin(greater, 'B', '0', controller)
        graph.set_pin(vetala_lib_get_item1, 'index', '-1', controller)
        graph.set_pin(vetala_lib_find_pole_axis, 'Multiply', '(X=0.000000,Y=0.000000,Z=0.000000)', controller)
        graph.set_pin(multiply, 'B', '(X=5.000000,Y=5.000000,Z=5.000000)', controller)

        current_locals = locals()
        nodes = unreal_lib.graph.filter_nodes(current_locals.values())
        node = unreal_lib.graph.comment_nodes(nodes, controller, 'Forward Solve')

        nodes.append(node)
        unreal_lib.graph.move_nodes(700, 0, nodes, controller)

    def _build_function_backward_graph(self):
        return


class UnrealFootRollRig(UnrealUtilRig):

    def _build_entry(self):
        super(UnrealFootRollRig, self)._build_entry()

        controller = self.function_controller
        controller.set_pin_default_value(f'{n(self.switch_mode)}.joint_index', '1', False)

    def _build_return(self):
        super(UnrealFootRollRig, self)._build_return()

        controller = self.function_controller
        controller.set_pin_default_value(f'{n(self.output_rig_controls)}.control_visibility', 'false', False)

    def _build_function_construct_graph(self):

        controller = self.function_controller
        library = graph.get_local_function_library()

        vetala_lib_control = self._create_control(controller, 6600.0, -2292.0)
        vetala_lib_get_parent = controller.add_function_reference_node(library.find_function('vetalaLib_GetParent'), unreal.Vector2D(1304.0, -2692.0), 'vetalaLib_GetParent')
        set_item_metadata = controller.add_template_node('DISPATCH_RigDispatch_SetMetadata(in Item,in Name,in NameSpace,in Value,out Success)', unreal.Vector2D(9784.0, -2276.0), 'Set Item Metadata')
        get_control_layer = controller.add_variable_node('control_layer', 'FName', None, True, '', unreal.Vector2D(888.0, -2900.0), 'Get control_layer')
        get_description = controller.add_variable_node('description', 'FString', None, True, '', unreal.Vector2D(5160.0, -1956.0), 'Get description')
        add = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayAdd(io Array,in Element,out Index)', unreal.Vector2D(6976.0, -2400.0), 'Add')
        get_local_controls = controller.add_variable_node_from_object_path('local_controls', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(7896.0, -2692.0), 'Get local_controls')
        branch = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_ControlFlowBranch', 'Execute', unreal.Vector2D(1336.0, -2452.0), 'Branch')
        num = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetNum(in Array,out Num)', unreal.Vector2D(728.0, -2468.0), 'Num')
        equals = controller.add_template_node('DISPATCH_RigVMDispatch_CoreEquals(in A,in B,out Result)', unreal.Vector2D(968.0, -2468.0), 'Equals')
        get_joints = controller.add_variable_node_from_object_path('joints', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(600.0, -2756.0), 'Get joints')
        at = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(920.0, -2692.0), 'At')
        vetala_lib_control1 = self._create_control(controller, 3608.0, -2451.0)
        add1 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayAdd(io Array,in Element,out Index)', unreal.Vector2D(4552.0, -2436.0), 'Add')
        at1 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(2840.0, -2708.0), 'At')
        make_array = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayMake(in Values,out Array)', unreal.Vector2D(2696.0, -1844.0), 'Make Array')
        get_transform = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetTransform', 'Execute', unreal.Vector2D(2264.0, -1940.0), 'Get Transform')
        get_heel_pivot = controller.add_variable_node_from_object_path('heel_pivot', 'TArray<FVector>', '/Script/CoreUObject.Vector', True, '()', unreal.Vector2D(1960.0, -1540.0), 'Get heel_pivot')
        get_yaw_in_pivot = controller.add_variable_node_from_object_path('yaw_in_pivot', 'TArray<FVector>', '/Script/CoreUObject.Vector', True, '()', unreal.Vector2D(1960.0, -1348.0), 'Get yaw_in_pivot')
        get_yaw_out_pivot = controller.add_variable_node_from_object_path('yaw_out_pivot', 'TArray<FVector>', '/Script/CoreUObject.Vector', True, '()', unreal.Vector2D(1960.0, -1444.0), 'Get yaw_out_pivot')
        vetala_lib_get_item_vector = controller.add_function_reference_node(library.find_function('vetalaLib_GetItemVector'), unreal.Vector2D(2168.0, -1588.0), 'vetalaLib_GetItemVector')
        vetala_lib_get_item_vector1 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItemVector'), unreal.Vector2D(2168.0, -1436.0), 'vetalaLib_GetItemVector')
        vetala_lib_get_item_vector2 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItemVector'), unreal.Vector2D(2168.0, -1284.0), 'vetalaLib_GetItemVector')
        for_each = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayIterator(in Array,out Element,out Index,out Count,out Ratio)', unreal.Vector2D(2744.0, -2452.0), 'For Each')
        make_array1 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayMake(in Values,out Array)', unreal.Vector2D(2696.0, -1236.0), 'Make Array')
        at2 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(3112.0, -1572.0), 'At')
        get_description1 = controller.add_variable_node('description', 'FString', None, True, '', unreal.Vector2D(2504.0, -2260.0), 'Get description')
        join = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_StringJoin', 'Execute', unreal.Vector2D(2856.0, -2171.0), 'Join')
        get_local_controls1 = controller.add_variable_node_from_object_path('local_controls', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(3096.0, -2708.0), 'Get local_controls')
        at3 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(3432.0, -2708.0), 'At')
        get_local_controls2 = controller.add_variable_node_from_object_path('local_controls', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(4088.0, -2708.0), 'Get local_controls')
        join1 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_StringJoin', 'Execute', unreal.Vector2D(5384.0, -1780.0), 'Join')
        add2 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayAdd(io Array,in Element,out Index)', unreal.Vector2D(2344.0, -2453.0), 'Add')
        get_local_controls3 = controller.add_variable_node_from_object_path('local_controls', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(2216.0, -2724.0), 'Get local_controls')
        get_local_controls4 = controller.add_variable_node_from_object_path('local_controls', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(4472.0, -2708.0), 'Get local_controls')
        at4 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(5400.0, -2676.0), 'At')
        vetala_lib_control2 = self._create_control(controller, 8056.0, -2292.0)
        join2 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_StringJoin', 'Execute', unreal.Vector2D(7080.0, -1796.0), 'Join')
        get_transform1 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetTransform', 'Execute', unreal.Vector2D(8328.0, -2516.0), 'Get Transform')
        set_transform = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_SetTransform', 'Execute', unreal.Vector2D(8984.0, -2276.0), 'Set Transform')
        set_item_metadata1 = controller.add_template_node('DISPATCH_RigDispatch_SetMetadata(in Item,in Name,in NameSpace,in Value,out Success)', unreal.Vector2D(10136.0, -2276.0), 'Set Item Metadata')
        set_item_metadata2 = controller.add_template_node('DISPATCH_RigDispatch_SetMetadata(in Item,in Name,in NameSpace,in Value,out Success)', unreal.Vector2D(5048.0, -2276.0), 'Set Item Metadata')
        get_ik = controller.add_variable_node_from_object_path('ik', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(9616.0, -1712.0), 'Get ik')
        get_joints1 = controller.add_variable_node_from_object_path('joints', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(8584.0, -2692.0), 'Get joints')
        vetala_lib_get_item = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(8936.0, -2468.0), 'vetalaLib_GetItem')
        set_item_array_metadata = controller.add_template_node('DISPATCH_RigDispatch_SetMetadata(in Item,in Name,in NameSpace,in Value,out Success)', unreal.Vector2D(10440.0, -2276.0), 'Set Item Array Metadata')
        add3 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayAdd(io Array,in Element,out Index)', unreal.Vector2D(8376.0, -2276.0), 'Add')
        get_parent = controller.add_variable_node_from_object_path('parent', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(9936.0, -2560.0), 'Get parent')
        get_item_metadata = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(10320.0, -2560.0), 'Get Item Metadata')
        if1 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(10882.0, -2560.0), 'If')
        item_exists = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_ItemExists', 'Execute', unreal.Vector2D(10594.0, -2560.0), 'Item Exists')
        vetala_lib_get_item1 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(10096.0, -2560.0), 'vetalaLib_GetItem')
        spawn_float_animation_channel = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyAddAnimationChannelFloat', 'Execute', unreal.Vector2D(10936.0, -1860.0), 'Spawn Float Animation Channel')
        for_each1 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayIterator(in Array,out Element,out Index,out Count,out Ratio)', unreal.Vector2D(10488.0, -1780.0), 'For Each')
        make_array2 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayMake(in Values,out Array)', unreal.Vector2D(10136.0, -1876.0), 'Make Array')
        double = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathDoubleMake', 'Execute', unreal.Vector2D(10792.0, -1380.0), 'Double')
        set_name_metadata = controller.add_template_node('DISPATCH_RigDispatch_SetMetadata(in Item,in Name,in NameSpace,in Value,out Success)', unreal.Vector2D(11448.0, -1860.0), 'Set Name Metadata')
        set_item_metadata3 = controller.add_template_node('DISPATCH_RigDispatch_SetMetadata(in Item,in Name,in NameSpace,in Value,out Success)', unreal.Vector2D(4648.0, -1828.0), 'Set Item Metadata')
        from_string = controller.add_template_node('DISPATCH_RigDispatch_FromString(in String,out Result)', unreal.Vector2D(3480.0, -1812.0), 'From String')
        get_joints2 = controller.add_variable_node_from_object_path('joints', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(4152.0, -1684.0), 'Get joints')
        vetala_lib_get_item2 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(4364.0, -1668.0), 'vetalaLib_GetItem')
        set_vector_metadata = controller.add_template_node('DISPATCH_RigDispatch_SetMetadata(in Item,in Name,in NameSpace,in Value,out Success)', unreal.Vector2D(4648.0, -1572.0), 'Set Vector Metadata')
        get_forward_axis = controller.add_variable_node_from_object_path('forward_axis', 'TArray<FVector>', '/Script/CoreUObject.Vector', True, '()', unreal.Vector2D(4142.0, -1444.0), 'Get forward_axis')
        vetala_lib_get_item_vector3 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItemVector'), unreal.Vector2D(4344.0, -1444.0), 'vetalaLib_GetItemVector')
        get_up_axis = controller.add_variable_node_from_object_path('up_axis', 'TArray<FVector>', '/Script/CoreUObject.Vector', True, '()', unreal.Vector2D(4152.0, -1252.0), 'Get up_axis')
        vetala_lib_get_item_vector4 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItemVector'), unreal.Vector2D(4344.0, -1252.0), 'vetalaLib_GetItemVector')
        set_vector_metadata1 = controller.add_template_node('DISPATCH_RigDispatch_SetMetadata(in Item,in Name,in NameSpace,in Value,out Success)', unreal.Vector2D(4648.0, -1316.0), 'Set Vector Metadata')
        from_string1 = controller.add_template_node('DISPATCH_RigDispatch_FromString(in String,out Result)', unreal.Vector2D(5624.0, -1908.0), 'From String')
        get_transform2 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetTransform', 'Execute', unreal.Vector2D(5880.0, -2516.0), 'Get Transform')
        from_string2 = controller.add_template_node('DISPATCH_RigDispatch_FromString(in String,out Result)', unreal.Vector2D(7306.0, -1676.0), 'From String')
        vetala_lib_get_item3 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(5736.0, -2804.0), 'vetalaLib_GetItem')
        set_transform1 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_SetTransform', 'Execute', unreal.Vector2D(7656.0, -2276.0), 'Set Transform')
        vetala_lib_get_item4 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(9480.0, -2484.0), 'vetalaLib_GetItem')
        spawn_transform_control = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyAddControlTransform', 'Execute', unreal.Vector2D(1800.0, -2452.0), 'Spawn Transform Control')
        spawn_transform_control1 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyAddControlTransform', 'Execute', unreal.Vector2D(3072.0, -2592.0), 'Spawn Transform Control')
        set_transform2 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_SetTransform', 'Execute', unreal.Vector2D(3973.0, -2432.0), 'Set Transform')
        join3 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_StringJoin', 'Execute', unreal.Vector2D(3056.0, -2080.0), 'Join')
        from_string3 = controller.add_template_node('DISPATCH_RigDispatch_FromString(in String,out Result)', unreal.Vector2D(3288.0, -2132.0), 'From String')
        equals1 = controller.add_template_node('DISPATCH_RigVMDispatch_CoreEquals(in A,in B,out Result)', unreal.Vector2D(10792.0, -1524.0), 'Equals')
        if2 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(11048.0, -1428.0), 'If')
        get_joints3 = controller.add_variable_node_from_object_path('joints', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(5480.0, -2820.0), 'Get joints')
        get_control_layer1 = controller.add_variable_node('control_layer', 'FName', None, True, '', unreal.Vector2D(4906.0, -2069.0), 'Get control_layer')
        get_control_layer2 = controller.add_variable_node('control_layer', 'FName', None, True, '', unreal.Vector2D(9526.0, -2625.0), 'Get control_layer')
        join4 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_StringJoin', 'Execute', unreal.Vector2D(5384.0, -2020.0), 'Join')
        from_string4 = controller.add_template_node('DISPATCH_RigDispatch_FromString(in String,out Result)', unreal.Vector2D(5208.0, -2068.0), 'From String')
        vetala_lib_get_item5 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(4856.0, -2692.0), 'vetalaLib_GetItem')
        equals2 = controller.add_template_node('DISPATCH_RigVMDispatch_CoreEquals(in A,in B,out Result)', unreal.Vector2D(3184.0, -1888.0), 'Equals')
        if3 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(3360.0, -1920.0), 'If')
        cross = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathVectorCross', 'Execute', unreal.Vector2D(5120.0, -1360.0), 'Cross')
        multiply = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathVectorMul', 'Execute', unreal.Vector2D(6128.0, -1664.0), 'Multiply')
        set_shape_transform = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_SetShapeTransform', 'Execute', unreal.Vector2D(6896.0, -2176.0), 'Set Shape Transform')
        from_euler = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathQuaternionFromEuler', 'Execute', unreal.Vector2D(6592.0, -1568.0), 'From Euler')
        get_shape = controller.add_variable_node('shape', 'FString', None, True, '', unreal.Vector2D(7440.0, -1520.0), 'Get shape')
        equals3 = controller.add_template_node('DISPATCH_RigVMDispatch_CoreEquals(in A,in B,out Result)', unreal.Vector2D(7632.0, -1568.0), 'Equals')
        if4 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(7824.0, -1632.0), 'If')
        get_shape_scale = controller.add_variable_node_from_object_path('shape_scale', 'TArray<FVector>', '/Script/CoreUObject.Vector', True, '()', unreal.Vector2D(7280.0, -1424.0), 'Get shape_scale')
        set_shape_transform1 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_SetShapeTransform', 'Execute', unreal.Vector2D(8960.0, -1552.0), 'Set Shape Transform')
        multiply1 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathVectorMul', 'Execute', unreal.Vector2D(7392.0, -1248.0), 'Multiply')
        add4 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathVectorAdd', 'Execute', unreal.Vector2D(7808.0, -1216.0), 'Add')
        multiply2 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathVectorMul', 'Execute', unreal.Vector2D(7792.0, -1472.0), 'Multiply')
        from_euler1 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathQuaternionFromEuler', 'Execute', unreal.Vector2D(8080.0, -1488.0), 'From Euler')
        get_shape_transform = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetShapeTransform', 'Execute', unreal.Vector2D(8256.0, -1600.0), 'Get Shape Transform')
        multiply3 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathTransformMul', 'Execute', unreal.Vector2D(8560.0, -1504.0), 'Multiply')
        get_shape_scale1 = controller.add_variable_node_from_object_path('shape_scale', 'TArray<FVector>', '/Script/CoreUObject.Vector', True, '()', unreal.Vector2D(6816.0, -1856.0), 'Get shape_scale')
        vetala_lib_get_item_vector5 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItemVector'), unreal.Vector2D(6992.0, -1888.0), 'vetalaLib_GetItemVector')
        spawn_transform_control2 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyAddControlTransform', 'Execute', unreal.Vector2D(5456.0, -2272.0), 'Spawn Transform Control')
        spawn_transform_control3 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyAddControlTransform', 'Execute', unreal.Vector2D(5840.0, -2288.0), 'Spawn Transform Control')
        spawn_transform_control4 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyAddControlTransform', 'Execute', unreal.Vector2D(7248.0, -2256.0), 'Spawn Transform Control')

        controller.resolve_wild_card_pin(f'{add.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{num.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{equals.get_node_path()}.A', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{equals.get_node_path()}.B', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{at.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{add1.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{at1.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{make_array.get_node_path()}.Array', 'TArray<FTransform>', '/Script/CoreUObject.Transform')
        controller.resolve_wild_card_pin(f'{for_each.get_node_path()}.Array', 'TArray<FTransform>', '/Script/CoreUObject.Transform')
        controller.resolve_wild_card_pin(f'{make_array1.get_node_path()}.Array', 'TArray<FString>', 'None')
        controller.resolve_wild_card_pin(f'{at2.get_node_path()}.Array', 'TArray<FString>', 'None')
        controller.resolve_wild_card_pin(f'{at3.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{add2.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{at4.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{add3.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{if1.get_node_path()}.Result', 'FRigElementKey', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{for_each1.get_node_path()}.Array', 'TArray<FName>', 'None')
        controller.resolve_wild_card_pin(f'{make_array2.get_node_path()}.Array', 'TArray<FName>', 'None')
        controller.resolve_wild_card_pin(f'{equals1.get_node_path()}.A', 'FName', 'None')
        controller.resolve_wild_card_pin(f'{equals1.get_node_path()}.B', 'FName', 'None')
        controller.resolve_wild_card_pin(f'{if2.get_node_path()}.Result', 'float', 'None')
        controller.resolve_wild_card_pin(f'{equals2.get_node_path()}.A', 'FString', 'None')
        controller.resolve_wild_card_pin(f'{equals2.get_node_path()}.B', 'FString', 'None')
        controller.resolve_wild_card_pin(f'{if3.get_node_path()}.Result', 'FString', 'None')
        controller.resolve_wild_card_pin(f'{equals3.get_node_path()}.A', 'FString', 'None')
        controller.resolve_wild_card_pin(f'{equals3.get_node_path()}.B', 'FString', 'None')
        controller.resolve_wild_card_pin(f'{if4.get_node_path()}.Result', 'FString', 'None')
        controller.resolve_wild_card_pin(f'{add4.get_node_path()}.Result', 'FVector', '/Script/CoreUObject.Vector')

        controller.set_array_pin_size(f'{n(make_array)}.Values', 4)
        controller.set_array_pin_size(f'{n(make_array1)}.Values', 4)
        controller.set_array_pin_size(f'{n(join)}.Values', 2)
        controller.set_array_pin_size(f'{n(join1)}.Values', 2)
        controller.set_array_pin_size(f'{n(join2)}.Values', 2)
        controller.set_array_pin_size(f'{n(make_array2)}.Values', 10)
        controller.set_array_pin_size(f'{n(join3)}.Values', 2)
        controller.set_array_pin_size(f'{n(join4)}.Values', 3)

        graph.add_link(spawn_transform_control3, 'ExecutePin', vetala_lib_control, 'ExecuteContext', controller)
        graph.add_link(vetala_lib_control, 'ExecuteContext', set_shape_transform, 'ExecutePin', controller)
        graph.add_link(set_transform, 'ExecutePin', set_item_metadata, 'ExecuteContext', controller)
        graph.add_link(set_item_metadata, 'ExecuteContext', set_item_metadata1, 'ExecuteContext', controller)
        graph.add_link(set_shape_transform, 'ExecutePin', add, 'ExecuteContext', controller)
        graph.add_link(add, 'ExecuteContext', spawn_transform_control4, 'ExecutePin', controller)
        graph.add_link('DISPATCH_RigVMDispatch_SwitchInt32', 'Cases.0', branch, 'ExecuteContext', controller)
        graph.add_link(spawn_transform_control1, 'ExecutePin', vetala_lib_control1, 'ExecuteContext', controller)
        graph.add_link(vetala_lib_control1, 'ExecuteContext', set_transform2, 'ExecutePin', controller)
        graph.add_link(set_transform2, 'ExecutePin', add1, 'ExecuteContext', controller)
        graph.add_link(add1, 'ExecuteContext', set_item_metadata3, 'ExecuteContext', controller)
        graph.add_link(add2, 'ExecuteContext', for_each, 'ExecuteContext', controller)
        graph.add_link(for_each, 'ExecuteContext', spawn_transform_control1, 'ExecutePin', controller)
        graph.add_link(for_each, 'Completed', set_item_metadata2, 'ExecuteContext', controller)
        graph.add_link(spawn_transform_control, 'ExecutePin', add2, 'ExecuteContext', controller)
        graph.add_link(set_transform1, 'ExecutePin', vetala_lib_control2, 'ExecuteContext', controller)
        graph.add_link(vetala_lib_control2, 'ExecuteContext', set_shape_transform1, 'ExecutePin', controller)
        graph.add_link(add3, 'ExecuteContext', set_transform, 'ExecutePin', controller)
        graph.add_link(set_item_metadata1, 'ExecuteContext', set_item_array_metadata, 'ExecuteContext', controller)
        graph.add_link(set_item_metadata2, 'ExecuteContext', spawn_transform_control2, 'ExecutePin', controller)
        graph.add_link(set_item_array_metadata, 'ExecuteContext', for_each1, 'ExecuteContext', controller)
        graph.add_link(set_shape_transform1, 'ExecutePin', add3, 'ExecuteContext', controller)
        graph.add_link(for_each1, 'ExecuteContext', spawn_float_animation_channel, 'ExecutePin', controller)
        graph.add_link(spawn_float_animation_channel, 'ExecutePin', set_name_metadata, 'ExecuteContext', controller)
        graph.add_link(set_item_metadata3, 'ExecuteContext', set_vector_metadata, 'ExecuteContext', controller)
        graph.add_link(set_vector_metadata, 'ExecuteContext', set_vector_metadata1, 'ExecuteContext', controller)
        graph.add_link(spawn_transform_control3, 'Item', vetala_lib_control, 'parent', controller)
        graph.add_link(vetala_lib_get_item3, 'Element', vetala_lib_control, 'driven', controller)
        graph.add_link(join1, 'Result', vetala_lib_control, 'description', controller)
        graph.add_link('Entry', 'side', vetala_lib_control, 'side', controller)
        graph.add_link('Entry', 'restrain_numbering', vetala_lib_control, 'restrain_numbering', controller)
        graph.add_link('Entry', 'shape', vetala_lib_control, 'shape', controller)
        graph.add_link('Entry', 'color', vetala_lib_control, 'color', controller)
        graph.add_link('Entry', 'sub_color', vetala_lib_control, 'sub_color', controller)
        graph.add_link('Entry', 'shape_translate', vetala_lib_control, 'translate', controller)
        graph.add_link('Entry', 'shape_rotate', vetala_lib_control, 'rotate', controller)
        graph.add_link('Entry', 'shape_scale', vetala_lib_control, 'scale', controller)
        graph.add_link(vetala_lib_control, 'Last Control', add, 'Element', controller)
        graph.add_link(vetala_lib_control, 'Last Control', set_item_metadata, 'Value', controller)
        graph.add_link(vetala_lib_control, 'Last Control', set_name_metadata, 'Item', controller)
        graph.add_link(vetala_lib_control, 'Last Control.Name', set_shape_transform, 'Control', controller)
        graph.add_link(at, 'Element', vetala_lib_get_parent, 'joint', controller)
        graph.add_link('Entry', 'parent', vetala_lib_get_parent, 'default_parent', controller)
        graph.add_link(get_control_layer, 'Value', vetala_lib_get_parent, 'control_layer', controller)
        graph.add_link(vetala_lib_get_parent, 'Result', spawn_transform_control, 'Parent', controller)
        graph.add_link(vetala_lib_get_item4, 'Element', set_item_metadata, 'Item', controller)
        graph.add_link(get_control_layer2, 'Value', set_item_metadata, 'Name', controller)
        graph.add_link(get_local_controls, 'Value', add, 'Array', controller)
        graph.add_link(get_local_controls, 'Value', add3, 'Array', controller)
        graph.add_link(equals, 'Result', branch, 'Condition', controller)
        graph.add_link(branch, 'True', spawn_transform_control, 'ExecutePin', controller)
        graph.add_link('Entry', 'joints', num, 'Array', controller)
        graph.add_link(num, 'Num', 'Equals', 'A', controller)
        graph.add_link(num, 'Num', equals, 'A', controller)
        graph.add_link(get_joints, 'Value', at, 'Array', controller)
        graph.add_link(get_joints, 'Value', at1, 'Array', controller)
        graph.add_link(spawn_transform_control1, 'Item', vetala_lib_control1, 'parent', controller)
        graph.add_link(join, 'Result', vetala_lib_control1, 'description', controller)
        graph.add_link('Entry', 'side', vetala_lib_control1, 'side', controller)
        graph.add_link('Entry', 'restrain_numbering', vetala_lib_control1, 'restrain_numbering', controller)
        graph.add_link(if3, 'Result', vetala_lib_control1, 'shape', controller)
        graph.add_link('Entry', 'color', vetala_lib_control1, 'color', controller)
        graph.add_link('Entry', 'sub_color', vetala_lib_control1, 'sub_color', controller)
        graph.add_link('Entry', 'shape_translate', vetala_lib_control1, 'translate', controller)
        graph.add_link('Entry', 'shape_rotate', vetala_lib_control1, 'rotate', controller)
        graph.add_link('Entry', 'shape_scale', vetala_lib_control1, 'scale', controller)
        graph.add_link(vetala_lib_control1, 'Last Control', add1, 'Element', controller)
        graph.add_link(vetala_lib_control1, 'Last Control', set_item_metadata3, 'Value', controller)
        graph.add_link(vetala_lib_control1, 'Last Control', set_transform2, 'Item', controller)
        graph.add_link(get_local_controls2, 'Value', add1, 'Array', controller)
        graph.add_link(at1, 'Element', get_transform, 'Item', controller)
        graph.add_link(at1, 'Element', set_item_metadata2, 'Item', controller)
        graph.add_link(make_array, 'Array', for_each, 'Array', controller)
        graph.add_link(get_heel_pivot, 'Value', vetala_lib_get_item_vector, 'Vector', controller)
        graph.add_link(get_yaw_in_pivot, 'Value', vetala_lib_get_item_vector2, 'Vector', controller)
        graph.add_link(get_yaw_out_pivot, 'Value', vetala_lib_get_item_vector1, 'Vector', controller)
        graph.add_link(for_each, 'Element', set_transform2, 'Value', controller)
        graph.add_link(for_each, 'Element', spawn_transform_control1, 'OffsetTransform', controller)
        graph.add_link(for_each, 'Index', at2, 'Index', controller)
        graph.add_link(make_array1, 'Array', at2, 'Array', controller)
        graph.add_link(at2, 'Element', from_string, 'String', controller)
        graph.add_link(get_local_controls1, 'Value', at3, 'Array', controller)
        graph.add_link(at3, 'Element', spawn_transform_control1, 'Parent', controller)
        graph.add_link(join1, 'Result', from_string1, 'String', controller)
        graph.add_link(get_local_controls3, 'Value', add2, 'Array', controller)
        graph.add_link(spawn_transform_control, 'Item', add2, 'Element', controller)
        graph.add_link(get_local_controls4, 'Value', at4, 'Array', controller)
        graph.add_link(get_local_controls4, 'Value', vetala_lib_get_item5, 'Array', controller)
        graph.add_link(at4, 'Element', spawn_transform_control2, 'Parent', controller)
        graph.add_link(spawn_transform_control4, 'Item', vetala_lib_control2, 'parent', controller)
        graph.add_link(join2, 'Result', vetala_lib_control2, 'description', controller)
        graph.add_link('Entry', 'side', vetala_lib_control2, 'side', controller)
        graph.add_link('Entry', 'restrain_numbering', vetala_lib_control2, 'restrain_numbering', controller)
        graph.add_link(if4, 'Result', vetala_lib_control2, 'shape', controller)
        graph.add_link('Entry', 'color', vetala_lib_control2, 'color', controller)
        graph.add_link('Entry', 'sub_color', vetala_lib_control2, 'sub_color', controller)
        graph.add_link('Entry', 'shape_translate', vetala_lib_control2, 'translate', controller)
        graph.add_link('Entry', 'shape_rotate', vetala_lib_control2, 'rotate', controller)
        graph.add_link(get_shape_scale, 'Value', vetala_lib_control2, 'scale', controller)
        graph.add_link(vetala_lib_control2, 'Last Control', add3, 'Element', controller)
        graph.add_link(vetala_lib_control2, 'Last Control', set_item_metadata1, 'Value', controller)
        graph.add_link(vetala_lib_control2, 'Last Control', set_transform, 'Item', controller)
        graph.add_link(vetala_lib_control2, 'Last Control.Name', get_shape_transform, 'Control', controller)
        graph.add_link(vetala_lib_control2, 'Last Control.Name', set_shape_transform1, 'Control', controller)
        graph.add_link(join2, 'Result', from_string2, 'String', controller)
        graph.add_link(vetala_lib_get_item3, 'Element', get_transform1, 'Item', controller)
        graph.add_link(get_transform1, 'Transform', set_transform, 'Value', controller)
        graph.add_link(vetala_lib_get_item4, 'Element', set_item_metadata1, 'Item', controller)
        graph.add_link(get_control_layer1, 'Value', set_item_metadata2, 'Name', controller)
        graph.add_link(vetala_lib_get_item5, 'Element', set_item_metadata2, 'Value', controller)
        graph.add_link(get_ik, 'Value', set_item_array_metadata, 'Value', controller)
        graph.add_link(get_joints1, 'Value', vetala_lib_get_item, 'Array', controller)
        graph.add_link(get_joints1, 'Value', vetala_lib_get_item4, 'Array', controller)
        graph.add_link(vetala_lib_get_item, 'Element', set_item_array_metadata, 'Item', controller)
        graph.add_link(get_parent, 'Value', vetala_lib_get_item1, 'Array', controller)
        graph.add_link(vetala_lib_get_item1, 'Element', get_item_metadata, 'Item', controller)
        graph.add_link(get_item_metadata, 'Value', if1, 'True', controller)
        graph.add_link(get_item_metadata, 'Value', item_exists, 'Item', controller)
        graph.add_link(item_exists, 'Exists', if1, 'Condition', controller)
        graph.add_link(vetala_lib_get_item1, 'Element', if1, 'False', controller)
        graph.add_link(if1, 'Result', spawn_float_animation_channel, 'Parent', controller)
        graph.add_link(for_each1, 'Element', spawn_float_animation_channel, 'Name', controller)
        graph.add_link(spawn_float_animation_channel, 'Item.Name', set_name_metadata, 'Value', controller)
        graph.add_link(if2, 'Result', spawn_float_animation_channel, 'InitialValue', controller)
        graph.add_link(make_array2, 'Array', for_each1, 'Array', controller)
        graph.add_link(for_each1, 'Element', set_name_metadata, 'Name', controller)
        graph.add_link(for_each1, 'Element', equals1, 'A', controller)
        graph.add_link(double, 'Value', if2, 'False', controller)
        graph.add_link(vetala_lib_get_item2, 'Element', set_item_metadata3, 'Item', controller)
        graph.add_link(from_string, 'Result', set_item_metadata3, 'Name', controller)
        graph.add_link(get_joints2, 'Value', vetala_lib_get_item2, 'Array', controller)
        graph.add_link(vetala_lib_get_item2, 'Element', set_vector_metadata, 'Item', controller)
        graph.add_link(vetala_lib_get_item2, 'Element', set_vector_metadata1, 'Item', controller)
        graph.add_link(vetala_lib_get_item_vector3, 'Element', set_vector_metadata, 'Value', controller)
        graph.add_link(get_forward_axis, 'Value', vetala_lib_get_item_vector3, 'Vector', controller)
        graph.add_link(vetala_lib_get_item_vector3, 'Element', cross, 'A', controller)
        graph.add_link(vetala_lib_get_item_vector3, 'Element', multiply2, 'B', controller)
        graph.add_link(get_up_axis, 'Value', vetala_lib_get_item_vector4, 'Vector', controller)
        graph.add_link(vetala_lib_get_item_vector4, 'Element', set_vector_metadata1, 'Value', controller)
        graph.add_link(vetala_lib_get_item_vector4, 'Element', cross, 'B', controller)
        graph.add_link(from_string1, 'Result', spawn_transform_control3, 'Name', controller)
        graph.add_link(vetala_lib_get_item3, 'Element', get_transform2, 'Item', controller)
        graph.add_link(get_transform2, 'Transform', set_transform1, 'Value', controller)
        graph.add_link(get_transform2, 'Transform', spawn_transform_control2, 'OffsetTransform', controller)
        graph.add_link(from_string2, 'Result', spawn_transform_control4, 'Name', controller)
        graph.add_link(get_joints3, 'Value', vetala_lib_get_item3, 'Array', controller)
        graph.add_link(spawn_transform_control4, 'ExecutePin', set_transform1, 'ExecutePin', controller)
        graph.add_link(spawn_transform_control4, 'Item', set_transform1, 'Item', controller)
        graph.add_link(from_string3, 'Result', spawn_transform_control1, 'Name', controller)
        graph.add_link(join3, 'Result', from_string3, 'String', controller)
        graph.add_link(equals1, 'Result', if2, 'Condition', controller)
        graph.add_link(join4, 'Result', from_string4, 'String', controller)
        graph.add_link(from_string4, 'Result', spawn_transform_control2, 'Name', controller)
        graph.add_link('Entry', 'shape', equals2, 'A', controller)
        graph.add_link(equals2, 'Result', if3, 'Condition', controller)
        graph.add_link('Entry', 'shape', if3, 'False', controller)
        graph.add_link(cross, 'Result', multiply, 'B', controller)
        graph.add_link(cross, 'Result', multiply1, 'B', controller)
        graph.add_link(multiply, 'Result', from_euler, 'Euler', controller)
        graph.add_link(get_shape, 'Value', equals3, 'A', controller)
        graph.add_link(get_shape, 'Value', if4, 'False', controller)
        graph.add_link(equals3, 'Result', if4, 'Condition', controller)
        graph.add_link(multiply3, 'Result', set_shape_transform1, 'Transform', controller)
        graph.add_link(multiply1, 'Result', add4, 'A', controller)
        graph.add_link(multiply2, 'Result', from_euler1, 'Euler', controller)
        graph.add_link(get_shape_transform, 'Transform', multiply3, 'A', controller)
        graph.add_link(get_shape_scale1, 'Value', vetala_lib_get_item_vector5, 'Vector', controller)
        graph.add_link(spawn_transform_control2, 'ExecutePin', spawn_transform_control3, 'ExecutePin', controller)
        graph.add_link(spawn_transform_control2, 'Item', spawn_transform_control3, 'Parent', controller)
        graph.add_link(spawn_transform_control2, 'Item', spawn_transform_control4, 'Parent', controller)
        graph.add_link(get_description, 'Value', join1, 'Values.0', controller)
        graph.add_link(get_description, 'Value', join2, 'Values.0', controller)
        graph.add_link(get_description, 'Value', join4, 'Values.0', controller)
        graph.add_link(at2, 'Element', join, 'Values.1', controller)
        graph.add_link(get_description1, 'Value', join, 'Values.0', controller)
        graph.add_link(join, 'Result', join3, 'Values.1', controller)
        graph.add_link(from_euler, 'Result', set_shape_transform, 'Transform.Rotation', controller)
        graph.add_link(vetala_lib_get_item_vector5, 'Element', set_shape_transform, 'Transform.Scale3D', controller)
        graph.add_link(add4, 'Result', multiply3, 'B.Scale3D', controller)
        graph.add_link(from_euler1, 'Result', multiply3, 'B.Rotation', controller)
        graph.add_link(get_transform, 'Transform.Rotation', make_array, 'Values.0.Rotation', controller)
        graph.add_link(get_transform, 'Transform.Translation', make_array, 'Values.0.Translation', controller)
        graph.add_link(get_transform, 'Transform.Rotation', make_array, 'Values.1.Rotation', controller)
        graph.add_link(vetala_lib_get_item_vector, 'Element', make_array, 'Values.1.Translation', controller)
        graph.add_link(get_transform, 'Transform.Rotation', make_array, 'Values.2.Rotation', controller)
        graph.add_link(vetala_lib_get_item_vector1, 'Element', make_array, 'Values.2.Translation', controller)
        graph.add_link(get_transform, 'Transform.Rotation', make_array, 'Values.3.Rotation', controller)
        graph.add_link(vetala_lib_get_item_vector2, 'Element', make_array, 'Values.3.Translation', controller)

        graph.set_pin(vetala_lib_control, 'increment', '0', controller)
        graph.set_pin(vetala_lib_control, 'sub_count', '0', controller)
        graph.set_pin(vetala_lib_control, 'scale_offset', '0.400000', controller)
        graph.set_pin(vetala_lib_get_parent, 'in_hierarchy', 'False', controller)
        graph.set_pin(set_item_metadata, 'NameSpace', 'Self', controller)
        graph.set_pin(equals, 'B', '3', controller)
        graph.set_pin(at, 'Index', '0', controller)
        graph.set_pin(vetala_lib_control1, 'increment', '0', controller)
        graph.set_pin(vetala_lib_control1, 'sub_count', '0', controller)
        graph.set_pin(vetala_lib_control1, 'scale_offset', '0.400000', controller)
        graph.set_pin(at1, 'Index', '2', controller)
        graph.set_pin(make_array, 'Values', '((Rotation=(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=1.000000,Y=1.000000,Z=1.000000)),((Rotation=(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=1.000000,Y=1.000000,Z=1.000000)),Rotation=(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=1.000000,Y=1.000000,Z=1.000000)),((Rotation=(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=1.000000,Y=1.000000,Z=1.000000)),Rotation=(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=1.000000,Y=1.000000,Z=1.000000)),((Rotation=(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=1.000000,Y=1.000000,Z=1.000000)),Rotation=(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=1.000000,Y=1.000000,Z=1.000000)))', controller)
        graph.set_pin(get_transform, 'Space', 'GlobalSpace', controller)
        graph.set_pin(get_transform, 'bInitial', 'False', controller)
        graph.set_pin(make_array1, 'Values', '("toe","heel","yaw_out","yaw_in")', controller)
        graph.set_pin(join, 'Values', '("","")', controller)
        graph.set_pin(join, 'Separator', '_', controller)
        graph.set_pin(at3, 'Index', '-1', controller)
        graph.set_pin(join1, 'Values', '("","ball")', controller)
        graph.set_pin(join1, 'Separator', '_', controller)
        graph.set_pin(at4, 'Index', '-1', controller)
        graph.set_pin(vetala_lib_control2, 'increment', '0', controller)
        graph.set_pin(vetala_lib_control2, 'sub_count', '0', controller)
        graph.set_pin(vetala_lib_control2, 'scale_offset', '1.500000', controller)
        graph.set_pin(join2, 'Values', '("","ankle")', controller)
        graph.set_pin(join2, 'Separator', '_', controller)
        graph.set_pin(get_transform1, 'Space', 'GlobalSpace', controller)
        graph.set_pin(get_transform1, 'bInitial', 'False', controller)
        graph.set_pin(set_transform, 'Space', 'GlobalSpace', controller)
        graph.set_pin(set_transform, 'bInitial', 'true', controller)
        graph.set_pin(set_transform, 'Weight', '1.000000', controller)
        graph.set_pin(set_transform, 'bPropagateToChildren', 'True', controller)
        graph.set_pin(set_item_metadata1, 'Name', 'ik', controller)
        graph.set_pin(set_item_metadata1, 'NameSpace', 'Self', controller)
        graph.set_pin(set_item_metadata2, 'NameSpace', 'Self', controller)
        graph.set_pin(set_item_array_metadata, 'Name', 'ik', controller)
        graph.set_pin(set_item_array_metadata, 'NameSpace', 'Self', controller)
        graph.set_pin(get_item_metadata, 'Name', 'main', controller)
        graph.set_pin(get_item_metadata, 'NameSpace', 'Self', controller)
        graph.set_pin(get_item_metadata, 'Default', '(Type=Bone,Name="None")', controller)
        graph.set_pin(vetala_lib_get_item1, 'index', '-1', controller)
        graph.set_pin(spawn_float_animation_channel, 'MinimumValue', '-90.000000', controller)
        graph.set_pin(spawn_float_animation_channel, 'MaximumValue', '90.000000', controller)
        graph.set_pin(spawn_float_animation_channel, 'LimitsEnabled', '(Enabled=(bMinimum=True,bMaximum=True))', controller)
        graph.set_pin(make_array2, 'Values', '("roll","rollOffset","heel","ball","toe","toeRotate","yaw","toePivot","ballPivot","heelPivot")', controller)
        graph.set_pin(set_name_metadata, 'NameSpace', 'Self', controller)
        graph.set_pin(set_item_metadata3, 'NameSpace', 'Self', controller)
        graph.set_pin(vetala_lib_get_item2, 'index', '-1', controller)
        graph.set_pin(set_vector_metadata, 'Name', 'forward_axis', controller)
        graph.set_pin(set_vector_metadata, 'NameSpace', 'Self', controller)
        graph.set_pin(set_vector_metadata1, 'Name', 'up_axis', controller)
        graph.set_pin(set_vector_metadata1, 'NameSpace', 'Self', controller)
        graph.set_pin(get_transform2, 'Space', 'GlobalSpace', controller)
        graph.set_pin(get_transform2, 'bInitial', 'False', controller)
        graph.set_pin(vetala_lib_get_item3, 'index', '1', controller)
        graph.set_pin(set_transform1, 'Space', 'GlobalSpace', controller)
        graph.set_pin(set_transform1, 'bInitial', 'true', controller)
        graph.set_pin(set_transform1, 'Weight', '1.000000', controller)
        graph.set_pin(set_transform1, 'bPropagateToChildren', 'True', controller)
        graph.set_pin(vetala_lib_get_item4, 'index', '1', controller)
        graph.set_pin(spawn_transform_control, 'Name', 'null_foot_roll', controller)
        graph.set_pin(spawn_transform_control, 'OffsetTransform', '(Rotation=(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=1.000000,Y=1.000000,Z=1.000000))', controller)
        graph.set_pin(spawn_transform_control, 'OffsetSpace', 'LocalSpace', controller)
        graph.set_pin(spawn_transform_control, 'InitialValue', '(Rotation=(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=1.000000,Y=1.000000,Z=1.000000))', controller)
        graph.set_pin(spawn_transform_control, 'Settings', '(InitialSpace=LocalSpace,bUsePreferredRotationOrder=False,PreferredRotationOrder=YZX,Limits=(LimitTranslationX=(bMinimum=False,bMaximum=False),LimitTranslationY=(bMinimum=False,bMaximum=False),LimitTranslationZ=(bMinimum=False,bMaximum=False),LimitPitch=(bMinimum=False,bMaximum=False),LimitYaw=(bMinimum=False,bMaximum=False),LimitRoll=(bMinimum=False,bMaximum=False),LimitScaleX=(bMinimum=False,bMaximum=False),LimitScaleY=(bMinimum=False,bMaximum=False),LimitScaleZ=(bMinimum=False,bMaximum=False),MinValue=(Location=(X=-100.000000,Y=-100.000000,Z=-100.000000),Rotation=(Pitch=-180.000000,Yaw=-180.000000,Roll=-180.000000),Scale=(X=0.000000,Y=0.000000,Z=0.000000)),MaxValue=(Location=(X=100.000000,Y=100.000000,Z=100.000000),Rotation=(Pitch=180.000000,Yaw=180.000000,Roll=180.000000),Scale=(X=10.000000,Y=10.000000,Z=10.000000)),bDrawLimits=True),Shape=(bVisible=false,Name="Default",Color=(R=0.020000,G=0.020000,B=0.020000,A=1.000000),Transform=(Rotation=(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=0.050000,Y=0.050000,Z=0.050000))),Proxy=(bIsProxy=true,ShapeVisibility=UserDefined),FilteredChannels=(),DisplayName="None")', controller)
        graph.set_pin(spawn_transform_control1, 'OffsetSpace', 'GlobalSpace', controller)
        graph.set_pin(spawn_transform_control1, 'InitialValue', '(Rotation=(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=1.000000,Y=1.000000,Z=1.000000))', controller)
        graph.set_pin(spawn_transform_control1, 'Settings', '(InitialSpace=LocalSpace,bUsePreferredRotationOrder=False,PreferredRotationOrder=YZX,Limits=(LimitTranslationX=(bMinimum=False,bMaximum=False),LimitTranslationY=(bMinimum=False,bMaximum=False),LimitTranslationZ=(bMinimum=False,bMaximum=False),LimitPitch=(bMinimum=False,bMaximum=False),LimitYaw=(bMinimum=False,bMaximum=False),LimitRoll=(bMinimum=False,bMaximum=False),LimitScaleX=(bMinimum=False,bMaximum=False),LimitScaleY=(bMinimum=False,bMaximum=False),LimitScaleZ=(bMinimum=False,bMaximum=False),MinValue=(Location=(X=-100.000000,Y=-100.000000,Z=-100.000000),Rotation=(Pitch=-180.000000,Yaw=-180.000000,Roll=-180.000000),Scale=(X=0.000000,Y=0.000000,Z=0.000000)),MaxValue=(Location=(X=100.000000,Y=100.000000,Z=100.000000),Rotation=(Pitch=180.000000,Yaw=180.000000,Roll=180.000000),Scale=(X=10.000000,Y=10.000000,Z=10.000000)),bDrawLimits=True),Shape=(bVisible=false,Name="Default",Color=(R=0.020000,G=0.020000,B=0.020000,A=1.000000),Transform=(Rotation=(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=0.050000,Y=0.050000,Z=0.050000))),Proxy=(bIsProxy=true,ShapeVisibility=UserDefined),FilteredChannels=(),DisplayName="None")', controller)
        graph.set_pin(set_transform2, 'Space', 'GlobalSpace', controller)
        graph.set_pin(set_transform2, 'bInitial', 'true', controller)
        graph.set_pin(set_transform2, 'Weight', '1.000000', controller)
        graph.set_pin(set_transform2, 'bPropagateToChildren', 'True', controller)
        graph.set_pin(join3, 'Values', '("null","")', controller)
        graph.set_pin(join3, 'Separator', '_', controller)
        graph.set_pin(equals1, 'B', 'rollOffset', controller)
        graph.set_pin(if2, 'True', '30.000000', controller)
        graph.set_pin(join4, 'Values', '("","ball","pivot")', controller)
        graph.set_pin(join4, 'Separator', '_', controller)
        graph.set_pin(vetala_lib_get_item5, 'index', '1', controller)
        graph.set_pin(equals2, 'B', 'Default', controller)
        graph.set_pin(if3, 'True', 'Circle_Solid', controller)
        graph.set_pin(multiply, 'A', '(X=90.000000,Y=90.000000,Z=90.000000)', controller)
        graph.set_pin(set_shape_transform, 'Transform', '(Rotation=(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=1.000000,Y=1.000000,Z=1.000000))', controller)
        graph.set_pin(from_euler, 'RotationOrder', 'ZYX', controller)
        graph.set_pin(equals3, 'B', 'Default', controller)
        graph.set_pin(if4, 'True', 'Square_Thick', controller)
        graph.set_pin(multiply1, 'A', '(X=1.000000,Y=1.000000,Z=1.000000)', controller)
        graph.set_pin(add4, 'B', '(X=0.250000,Y=0.250000,Z=0.250000)', controller)
        graph.set_pin(multiply2, 'A', '(X=90.000000,Y=90.000000,Z=90.000000)', controller)
        graph.set_pin(from_euler1, 'RotationOrder', 'ZYX', controller)
        graph.set_pin(multiply3, 'B', '(Rotation=(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=1.000000,Y=1.000000,Z=1.000000))', controller)
        graph.set_pin(spawn_transform_control2, 'OffsetSpace', 'GlobalSpace', controller)
        graph.set_pin(spawn_transform_control2, 'InitialValue', '(Rotation=(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=1.000000,Y=1.000000,Z=1.000000))', controller)
        graph.set_pin(spawn_transform_control2, 'Settings', '(InitialSpace=LocalSpace,bUsePreferredRotationOrder=False,PreferredRotationOrder=YZX,Limits=(LimitTranslationX=(bMinimum=False,bMaximum=False),LimitTranslationY=(bMinimum=False,bMaximum=False),LimitTranslationZ=(bMinimum=False,bMaximum=False),LimitPitch=(bMinimum=False,bMaximum=False),LimitYaw=(bMinimum=False,bMaximum=False),LimitRoll=(bMinimum=False,bMaximum=False),LimitScaleX=(bMinimum=False,bMaximum=False),LimitScaleY=(bMinimum=False,bMaximum=False),LimitScaleZ=(bMinimum=False,bMaximum=False),MinValue=(Location=(X=-100.000000,Y=-100.000000,Z=-100.000000),Rotation=(Pitch=-180.000000,Yaw=-180.000000,Roll=-180.000000),Scale=(X=0.000000,Y=0.000000,Z=0.000000)),MaxValue=(Location=(X=100.000000,Y=100.000000,Z=100.000000),Rotation=(Pitch=180.000000,Yaw=180.000000,Roll=180.000000),Scale=(X=10.000000,Y=10.000000,Z=10.000000)),bDrawLimits=True),Shape=(bVisible=false,Name="Default",Color=(R=0.020000,G=0.020000,B=0.020000,A=1.000000),Transform=(Rotation=(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=1.000000,Y=1.000000,Z=1.000000))),Proxy=(bIsProxy=true,ShapeVisibility=BasedOnSelection),FilteredChannels=(),DisplayName="None")', controller)
        graph.set_pin(spawn_transform_control3, 'OffsetTransform', '(Rotation=(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=1.000000,Y=1.000000,Z=1.000000))', controller)
        graph.set_pin(spawn_transform_control3, 'OffsetSpace', 'LocalSpace', controller)
        graph.set_pin(spawn_transform_control3, 'InitialValue', '(Rotation=(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=1.000000,Y=1.000000,Z=1.000000))', controller)
        graph.set_pin(spawn_transform_control3, 'Settings', '(InitialSpace=LocalSpace,bUsePreferredRotationOrder=False,PreferredRotationOrder=YZX,Limits=(LimitTranslationX=(bMinimum=False,bMaximum=False),LimitTranslationY=(bMinimum=False,bMaximum=False),LimitTranslationZ=(bMinimum=False,bMaximum=False),LimitPitch=(bMinimum=False,bMaximum=False),LimitYaw=(bMinimum=False,bMaximum=False),LimitRoll=(bMinimum=False,bMaximum=False),LimitScaleX=(bMinimum=False,bMaximum=False),LimitScaleY=(bMinimum=False,bMaximum=False),LimitScaleZ=(bMinimum=False,bMaximum=False),MinValue=(Location=(X=-100.000000,Y=-100.000000,Z=-100.000000),Rotation=(Pitch=-180.000000,Yaw=-180.000000,Roll=-180.000000),Scale=(X=0.000000,Y=0.000000,Z=0.000000)),MaxValue=(Location=(X=100.000000,Y=100.000000,Z=100.000000),Rotation=(Pitch=180.000000,Yaw=180.000000,Roll=180.000000),Scale=(X=10.000000,Y=10.000000,Z=10.000000)),bDrawLimits=True),Shape=(bVisible=false,Name="Default",Color=(R=0.020000,G=0.020000,B=0.020000,A=1.000000),Transform=(Rotation=(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=1.000000,Y=1.000000,Z=1.000000))),Proxy=(bIsProxy=true,ShapeVisibility=BasedOnSelection),FilteredChannels=(),DisplayName="None")', controller)
        graph.set_pin(spawn_transform_control4, 'OffsetTransform', '(Rotation=(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=1.000000,Y=1.000000,Z=1.000000))', controller)
        graph.set_pin(spawn_transform_control4, 'OffsetSpace', 'LocalSpace', controller)
        graph.set_pin(spawn_transform_control4, 'InitialValue', '(Rotation=(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=1.000000,Y=1.000000,Z=1.000000))', controller)
        graph.set_pin(spawn_transform_control4, 'Settings', '(InitialSpace=LocalSpace,bUsePreferredRotationOrder=False,PreferredRotationOrder=YZX,Limits=(LimitTranslationX=(bMinimum=False,bMaximum=False),LimitTranslationY=(bMinimum=False,bMaximum=False),LimitTranslationZ=(bMinimum=False,bMaximum=False),LimitPitch=(bMinimum=False,bMaximum=False),LimitYaw=(bMinimum=False,bMaximum=False),LimitRoll=(bMinimum=False,bMaximum=False),LimitScaleX=(bMinimum=False,bMaximum=False),LimitScaleY=(bMinimum=False,bMaximum=False),LimitScaleZ=(bMinimum=False,bMaximum=False),MinValue=(Location=(X=-100.000000,Y=-100.000000,Z=-100.000000),Rotation=(Pitch=-180.000000,Yaw=-180.000000,Roll=-180.000000),Scale=(X=0.000000,Y=0.000000,Z=0.000000)),MaxValue=(Location=(X=100.000000,Y=100.000000,Z=100.000000),Rotation=(Pitch=180.000000,Yaw=180.000000,Roll=180.000000),Scale=(X=10.000000,Y=10.000000,Z=10.000000)),bDrawLimits=True),Shape=(bVisible=false,Name="Default",Color=(R=0.020000,G=0.020000,B=0.020000,A=1.000000),Transform=(Rotation=(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=1.000000,Y=1.000000,Z=1.000000))),Proxy=(bIsProxy=true,ShapeVisibility=BasedOnSelection),FilteredChannels=(),DisplayName="None")', controller)

        current_locals = locals()
        nodes = unreal_lib.graph.filter_nodes(current_locals.values())
        node = unreal_lib.graph.comment_nodes(nodes, controller, 'Construction')
        nodes.append(node)
        unreal_lib.graph.move_nodes(500, -3000, nodes, controller)

    def _build_function_forward_graph(self):

        controller = self.function_controller
        library = graph.get_local_function_library()

        vetala_lib_get_item = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(800.0, 800.0), 'vetalaLib_GetItem')
        get_control_layer = controller.add_variable_node('control_layer', 'FName', None, True, '', unreal.Vector2D(1220.0, 2360.0), 'Get control_layer')
        get_item_metadata = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(1876.0, 1664.0), 'Get Item Metadata')
        vetala_lib_get_item1 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(1460.0, 2744.0), 'vetalaLib_GetItem')
        get_item_metadata1 = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(1860.0, 2440.0), 'Get Item Metadata')
        vetala_lib_get_item2 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(1316.0, 2048.0), 'vetalaLib_GetItem')
        basic_fabrik = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_FABRIKItemArray', 'Execute', unreal.Vector2D(4084.0, 1744.0), 'Basic FABRIK')
        make_array = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayMake(in Values,out Array)', unreal.Vector2D(2692.0, 3008.0), 'Make Array')
        basic_fabrik1 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_FABRIKItemArray', 'Execute', unreal.Vector2D(3652.0, 2160.0), 'Basic FABRIK')
        make_array1 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayMake(in Values,out Array)', unreal.Vector2D(2756.0, 1808.0), 'Make Array')
        get_item_metadata2 = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(1860.0, 2200.0), 'Get Item Metadata')
        project_to_new_parent = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_ProjectTransformToNewParent', 'Execute', unreal.Vector2D(2628.0, 2560.0), 'Project to new Parent')
        vetala_lib_get_item3 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(1156.0, 1872.0), 'vetalaLib_GetItem')
        make_array2 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayMake(in Values,out Array)', unreal.Vector2D(4132.0, 2020.0), 'Make Array')
        at = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(4676.0, 2057.0), 'At')
        get_name_metadata = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(4916.0, 2057.0), 'Get Name Metadata')
        get_control_float = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetControlFloat', 'Execute', unreal.Vector2D(5252.0, 2057.0), 'Get Control Float')
        make_array3 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayMake(in Values,out Array)', unreal.Vector2D(4340.0, 1188.0), 'Make Array')
        get_item_metadata3 = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(5300.0, 580.0), 'Get Item Metadata')
        get_joints = controller.add_variable_node_from_object_path('joints', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(3316.0, 1472.0), 'Get joints')
        vetala_lib_get_item4 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(3524.0, 1440.0), 'vetalaLib_GetItem')
        at1 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(4676.0, 580.0), 'At')
        from_string = controller.add_template_node('DISPATCH_RigDispatch_FromString(in String,out Result)', unreal.Vector2D(4875.0, 580.0), 'From String')
        get_vector_metadata = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(6100.0, 1684.0), 'Get Vector Metadata')
        cross = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathVectorCross', 'Execute', unreal.Vector2D(6468.0, 1812.0), 'Cross')
        get_vector_metadata1 = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(6100.0, 1844.0), 'Get Vector Metadata')
        multiply = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathDoubleMul', 'Execute', unreal.Vector2D(5988.0, 2212.0), 'Multiply')
        set_rotation = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_SetRotation', 'Execute', unreal.Vector2D(8580.0, 544.0), 'Set Rotation')
        get_item_metadata4 = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(5300.0, 804.0), 'Get Item Metadata')
        at2 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(4685.0, 804.0), 'At')
        from_string1 = controller.add_template_node('DISPATCH_RigDispatch_FromString(in String,out Result)', unreal.Vector2D(4884.0, 804.0), 'From String')
        get_item_metadata5 = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(5300.0, 1028.0), 'Get Item Metadata')
        at3 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(4685.0, 1028.0), 'At')
        from_string2 = controller.add_template_node('DISPATCH_RigDispatch_FromString(in String,out Result)', unreal.Vector2D(4884.0, 1028.0), 'From String')
        get_item_metadata6 = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(5300.0, 1252.0), 'Get Item Metadata')
        at4 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(4685.0, 1252.0), 'At')
        from_string3 = controller.add_template_node('DISPATCH_RigDispatch_FromString(in String,out Result)', unreal.Vector2D(4884.0, 1252.0), 'From String')
        evaluate_curve = controller.add_unit_node_with_defaults(unreal.load_object(None, '/Script/RigVM.RigVMFunction_AnimEvalRichCurve'), '(Curve=(EditorCurveData=(Keys=((),(Time=0.500000,Value=1.000000),(Time=1.000000)))),SourceMinimum=0.000000,SourceMaximum=1.000000,TargetMinimum=0.000000,TargetMaximum=1.000000)', 'Execute', unreal.Vector2D(6420.0, 2244.0), 'Evaluate Curve')
        from_axis_and_angle = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathQuaternionFromAxisAndAngle', 'Execute', unreal.Vector2D(7268.0, 2084.0), 'From Axis And Angle')
        get_parent = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyGetParent', 'Execute', unreal.Vector2D(6132.0, 612.0), 'Get Parent')
        negate = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathVectorNegate', 'Execute', unreal.Vector2D(6724.0, 1796.0), 'Negate')
        get_parent1 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyGetParent', 'Execute', unreal.Vector2D(6132.0, 1376.0), 'Get Parent')
        set_rotation1 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_SetRotation', 'Execute', unreal.Vector2D(8564.0, 1248.0), 'Set Rotation')
        radians = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathDoubleRad', 'Execute', unreal.Vector2D(7060.0, 2260.0), 'Radians')
        multiply1 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathDoubleMul', 'Execute', unreal.Vector2D(6900.0, 2436.0), 'Multiply')
        get_control_float1 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetControlFloat', 'Execute', unreal.Vector2D(5252.0, 2612.0), 'Get Control Float')
        get_name_metadata1 = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(4916.0, 2601.0), 'Get Name Metadata')
        evaluate_curve1 = controller.add_unit_node_with_defaults(unreal.load_object(None, '/Script/RigVM.RigVMFunction_AnimEvalRichCurve'), '(Curve=(EditorCurveData=(Keys=((),(Time=0.250000),(InterpMode=RCIM_Constant,Time=1.000000,Value=1.000000)))),SourceMinimum=0.000000,SourceMaximum=2.000000,TargetMinimum=0.000000,TargetMaximum=90.000000)', 'Execute', unreal.Vector2D(6420.0, 2692.0), 'Evaluate Curve')
        radians1 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathDoubleRad', 'Execute', unreal.Vector2D(7007.0, 3083.0), 'Radians')
        from_axis_and_angle1 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathQuaternionFromAxisAndAngle', 'Execute', unreal.Vector2D(7268.0, 2836.0), 'From Axis And Angle')
        evaluate_curve2 = controller.add_unit_node_with_defaults(unreal.load_object(None, '/Script/RigVM.RigVMFunction_AnimEvalRichCurve'), '(Curve=(EditorCurveData=(Keys=((),(InterpMode=RCIM_Constant,Time=1.000000,Value=1.000000)))),SourceMinimum=0.000000,SourceMaximum=2.000000,TargetMinimum=0.000000,TargetMaximum=-90.000000)', 'Execute', unreal.Vector2D(6420.0, 3156.0), 'Evaluate Curve')
        multiply2 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathDoubleMul', 'Execute', unreal.Vector2D(5988.0, 2772.0), 'Multiply')
        set_rotation2 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_SetRotation', 'Execute', unreal.Vector2D(8580.0, 768.0), 'Set Rotation')
        get_parent2 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyGetParent', 'Execute', unreal.Vector2D(6132.0, 852.0), 'Get Parent')
        from_axis_and_angle2 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathQuaternionFromAxisAndAngle', 'Execute', unreal.Vector2D(7268.0, 3508.0), 'From Axis And Angle')
        radians2 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathDoubleRad', 'Execute', unreal.Vector2D(7028.0, 3540.0), 'Radians')
        multiply3 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathDoubleMul', 'Execute', unreal.Vector2D(5988.0, 2484.0), 'Multiply')
        at5 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(4692.0, 2938.0), 'At')
        get_name_metadata2 = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(4932.0, 2917.0), 'Get Name Metadata')
        get_control_float2 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetControlFloat', 'Execute', unreal.Vector2D(5268.0, 2928.0), 'Get Control Float')
        from_axis_and_angle3 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathQuaternionFromAxisAndAngle', 'Execute', unreal.Vector2D(7268.0, 3940.0), 'From Axis And Angle')
        multiply4 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathQuaternionMul', 'Execute', unreal.Vector2D(7764.0, 3732.0), 'Multiply')
        at6 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(4644.0, 3231.0), 'At')
        get_name_metadata3 = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(4948.0, 3210.0), 'Get Name Metadata')
        get_control_float3 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetControlFloat', 'Execute', unreal.Vector2D(5284.0, 3221.0), 'Get Control Float')
        from_axis_and_angle4 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathQuaternionFromAxisAndAngle', 'Execute', unreal.Vector2D(7284.0, 4164.0), 'From Axis And Angle')
        multiply5 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathQuaternionMul', 'Execute', unreal.Vector2D(8132.0, 4148.0), 'Multiply')
        rig_element_key = controller.add_free_reroute_node('FRigElementKey', unreal.load_object(None, '/Script/ControlRig.RigElementKey').get_name(), is_constant=False, custom_widget_name='', default_value='', position=[4023.0, 2556.0], node_name='', setup_undo_redo=True)
        at7 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(4676.0, 2500.0), 'At')
        at8 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(4644.0, 3562.0), 'At')
        get_name_metadata4 = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(4948.0, 3541.0), 'Get Name Metadata')
        get_control_float4 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetControlFloat', 'Execute', unreal.Vector2D(5284.0, 3552.0), 'Get Control Float')
        from_axis_and_angle5 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathQuaternionFromAxisAndAngle', 'Execute', unreal.Vector2D(7284.0, 4372.0), 'From Axis And Angle')
        multiply6 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathQuaternionMul', 'Execute', unreal.Vector2D(7793.0, 4388.0), 'Multiply')
        at9 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(4644.0, 3866.0), 'At')
        get_name_metadata5 = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(4948.0, 3845.0), 'Get Name Metadata')
        get_control_float5 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetControlFloat', 'Execute', unreal.Vector2D(5284.0, 3856.0), 'Get Control Float')
        get_parent3 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyGetParent', 'Execute', unreal.Vector2D(6132.0, 1540.0), 'Get Parent')
        set_rotation3 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_SetRotation', 'Execute', unreal.Vector2D(8564.0, 1492.0), 'Set Rotation')
        from_axis_and_angle6 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathQuaternionFromAxisAndAngle', 'Execute', unreal.Vector2D(7268.0, 4596.0), 'From Axis And Angle')
        from_axis_and_angle7 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathQuaternionFromAxisAndAngle', 'Execute', unreal.Vector2D(6708.0, 3972.0), 'From Axis And Angle')
        multiply7 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathQuaternionMul', 'Execute', unreal.Vector2D(8356.0, 4068.0), 'Multiply')
        at10 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(4644.0, 4138.0), 'At')
        get_name_metadata6 = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(4948.0, 4117.0), 'Get Name Metadata')
        get_control_float6 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetControlFloat', 'Execute', unreal.Vector2D(5284.0, 4128.0), 'Get Control Float')
        greater = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathDoubleGreater', 'Execute', unreal.Vector2D(7124.0, 4996.0), 'Greater')
        if1 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(7380.0, 5012.0), 'If')
        from_axis_and_angle8 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathQuaternionFromAxisAndAngle', 'Execute', unreal.Vector2D(7236.0, 5188.0), 'From Axis And Angle')
        negate1 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathVectorNegate', 'Execute', unreal.Vector2D(6484.0, 4324.0), 'Negate')
        from_axis_and_angle9 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathQuaternionFromAxisAndAngle', 'Execute', unreal.Vector2D(7236.0, 5332.0), 'From Axis And Angle')
        if2 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(7284.0, 5540.0), 'If')
        less = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathDoubleLess', 'Execute', unreal.Vector2D(7076.0, 5540.0), 'Less')
        get_parent4 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyGetParent', 'Execute', unreal.Vector2D(6148.0, 1028.0), 'Get Parent')
        get_parent5 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyGetParent', 'Execute', unreal.Vector2D(6148.0, 1156.0), 'Get Parent')
        set_rotation4 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_SetRotation', 'Execute', unreal.Vector2D(8564.0, 1828.0), 'Set Rotation')
        set_rotation5 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_SetRotation', 'Execute', unreal.Vector2D(8548.0, 2116.0), 'Set Rotation')
        multiply8 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathDoubleMul', 'Execute', unreal.Vector2D(6628.0, 5348.0), 'Multiply')
        at11 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(4644.0, 4426.0), 'At')
        get_name_metadata7 = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(4948.0, 4405.0), 'Get Name Metadata')
        get_control_float7 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetControlFloat', 'Execute', unreal.Vector2D(5284.0, 4416.0), 'Get Control Float')
        at12 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(4644.0, 4650.0), 'At')
        get_name_metadata8 = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(4948.0, 4629.0), 'Get Name Metadata')
        get_control_float8 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetControlFloat', 'Execute', unreal.Vector2D(5284.0, 4640.0), 'Get Control Float')
        at13 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(4644.0, 4858.0), 'At')
        get_name_metadata9 = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(4948.0, 4837.0), 'Get Name Metadata')
        get_control_float9 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetControlFloat', 'Execute', unreal.Vector2D(5284.0, 4848.0), 'Get Control Float')
        from_axis_and_angle10 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathQuaternionFromAxisAndAngle', 'Execute', unreal.Vector2D(7268.0, 5796.0), 'From Axis And Angle')
        multiply9 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathQuaternionMul', 'Execute', unreal.Vector2D(8436.0, 4756.0), 'Multiply')
        from_axis_and_angle11 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathQuaternionFromAxisAndAngle', 'Execute', unreal.Vector2D(8532.0, 5856.0), 'From Axis And Angle')
        vector = controller.add_free_reroute_node('FVector', unreal.load_object(None, '/Script/CoreUObject.Vector').get_name(), is_constant=False, custom_widget_name='', default_value='', position=[6436.0, 5940.0], node_name='', setup_undo_redo=True)
        vector1 = controller.add_free_reroute_node('FVector', unreal.load_object(None, '/Script/CoreUObject.Vector').get_name(), is_constant=False, custom_widget_name='', default_value='', position=[6116.0, 4324.0], node_name='', setup_undo_redo=True)
        set_rotation6 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_SetRotation', 'Execute', unreal.Vector2D(8564.0, 1008.0), 'Set Rotation')
        from_axis_and_angle12 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathQuaternionFromAxisAndAngle', 'Execute', unreal.Vector2D(7268.0, 6196.0), 'From Axis And Angle')
        multiply10 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathQuaternionMul', 'Execute', unreal.Vector2D(8324.0, 3780.0), 'Multiply')
        radians3 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathDoubleRad', 'Execute', unreal.Vector2D(5721.0, 3087.0), 'Radians')
        radians4 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathDoubleRad', 'Execute', unreal.Vector2D(5733.0, 3402.0), 'Radians')
        radians5 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathDoubleRad', 'Execute', unreal.Vector2D(5764.0, 3637.0), 'Radians')
        radians6 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathDoubleRad', 'Execute', unreal.Vector2D(5748.0, 3925.0), 'Radians')
        radians7 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathDoubleRad', 'Execute', unreal.Vector2D(5764.0, 4277.0), 'Radians')
        radians8 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathDoubleRad', 'Execute', unreal.Vector2D(5782.0, 4591.0), 'Radians')
        radians9 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathDoubleRad', 'Execute', unreal.Vector2D(5889.0, 4889.0), 'Radians')
        radians10 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathDoubleRad', 'Execute', unreal.Vector2D(5922.0, 5077.0), 'Radians')
        to_integer = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathBoolToInteger', 'Execute', unreal.Vector2D(1604.0, 1104.0), 'To Integer')
        get_parent6 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyGetParent', 'Execute', unreal.Vector2D(6516.0, 1216.0), 'Get Parent')
        branch = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_ControlFlowBranch', 'Execute', unreal.Vector2D(1700.0, 624.0), 'Branch')
        set_transform = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_SetTransform', 'Execute', unreal.Vector2D(2692.0, 640.0), 'Set Transform')
        project_to_new_parent1 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_ProjectTransformToNewParent', 'Execute', unreal.Vector2D(2244.0, 592.0), 'Project to new Parent')
        item_exists = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_ItemExists', 'Execute', unreal.Vector2D(1268.0, 960.0), 'Item Exists')
        vetala_lib_get_item5 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(1188.0, 1248.0), 'vetalaLib_GetItem')
        item_exists1 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_ItemExists', 'Execute', unreal.Vector2D(1476.0, 1200.0), 'Item Exists')
        get_item_metadata7 = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(1716.0, 1360.0), 'Get Item Metadata')
        get_float_channel = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetFloatAnimationChannelFromItem', 'Execute', unreal.Vector2D(2084.0, 1456.0), 'Get Float Channel')
        equals = controller.add_template_node('DISPATCH_RigVMDispatch_CoreEquals(in A,in B,out Result)', unreal.Vector2D(2308.0, 1312.0), 'Equals')
        select = controller.add_template_node('DISPATCH_RigVMDispatch_SelectInt32(in Index,in Values,out Result)', unreal.Vector2D(1940.0, 1056.0), 'Select')
        if3 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(2388.0, 1088.0), 'If')
        project_to_new_parent2 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_ProjectTransformToNewParent', 'Execute', unreal.Vector2D(2932.0, 2128.0), 'Project to new Parent')
        set_transform1 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_SetTransform', 'Execute', unreal.Vector2D(3812.0, 1040.0), 'Set Transform')
        project_to_new_parent3 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_ProjectTransformToNewParent', 'Execute', unreal.Vector2D(2708.0, 1232.0), 'Project to new Parent')
        branch1 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_ControlFlowBranch', 'Execute', unreal.Vector2D(3027.0, 1507.0), 'Branch')
        get_transform = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetTransform', 'Execute', unreal.Vector2D(3332.0, 1056.0), 'Get Transform')
        get_item_array_metadata = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(3204.0, 800.0), 'Get Item Array Metadata')
        remove = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayRemove(io Array,in Index)', unreal.Vector2D(3156.0, 576.0), 'Remove')
        for_each = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayIterator(in Array,out Element,out Index,out Count,out Ratio)', unreal.Vector2D(3892.0, 688.0), 'For Each')
        set_control_visibility = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_SetControlVisibility', 'Execute', unreal.Vector2D(4324.0, 720.0), 'Set Control Visibility')
        item_exists2 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_ItemExists', 'Execute', unreal.Vector2D(3908.0, 528.0), 'Item Exists')
        branch2 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_ControlFlowBranch', 'Execute', unreal.Vector2D(4212.0, 544.0), 'Branch')
        not1 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathBoolNot', 'Execute', unreal.Vector2D(3668.0, 944.0), 'Not')
        remove1 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayRemove(io Array,in Index)', unreal.Vector2D(3412.0, 576.0), 'Remove')

        controller.resolve_wild_card_pin(f'{make_array.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{make_array1.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{make_array2.get_node_path()}.Array', 'TArray<FName>', 'None')
        controller.resolve_wild_card_pin(f'{at.get_node_path()}.Array', 'TArray<FName>', 'None')
        controller.resolve_wild_card_pin(f'{make_array3.get_node_path()}.Array', 'TArray<FString>', 'None')
        controller.resolve_wild_card_pin(f'{at1.get_node_path()}.Array', 'TArray<FString>', 'None')
        controller.resolve_wild_card_pin(f'{at2.get_node_path()}.Array', 'TArray<FString>', 'None')
        controller.resolve_wild_card_pin(f'{at3.get_node_path()}.Array', 'TArray<FString>', 'None')
        controller.resolve_wild_card_pin(f'{at4.get_node_path()}.Array', 'TArray<FString>', 'None')
        controller.resolve_wild_card_pin(f'{at5.get_node_path()}.Array', 'TArray<FName>', 'None')
        controller.resolve_wild_card_pin(f'{at6.get_node_path()}.Array', 'TArray<FName>', 'None')
        controller.resolve_wild_card_pin(f'{at7.get_node_path()}.Array', 'TArray<FName>', 'None')
        controller.resolve_wild_card_pin(f'{at8.get_node_path()}.Array', 'TArray<FName>', 'None')
        controller.resolve_wild_card_pin(f'{at9.get_node_path()}.Array', 'TArray<FName>', 'None')
        controller.resolve_wild_card_pin(f'{at10.get_node_path()}.Array', 'TArray<FName>', 'None')
        controller.resolve_wild_card_pin(f'{greater.get_node_path()}.A', 'double', 'None')
        controller.resolve_wild_card_pin(f'{greater.get_node_path()}.B', 'double', 'None')
        controller.resolve_wild_card_pin(f'{if1.get_node_path()}.Result', 'FQuat', '/Script/CoreUObject.Quat')
        controller.resolve_wild_card_pin(f'{if2.get_node_path()}.Result', 'FQuat', '/Script/CoreUObject.Quat')
        controller.resolve_wild_card_pin(f'{at11.get_node_path()}.Array', 'TArray<FName>', 'None')
        controller.resolve_wild_card_pin(f'{at12.get_node_path()}.Array', 'TArray<FName>', 'None')
        controller.resolve_wild_card_pin(f'{at13.get_node_path()}.Array', 'TArray<FName>', 'None')
        controller.resolve_wild_card_pin(f'{equals.get_node_path()}.A', 'double', 'None')
        controller.resolve_wild_card_pin(f'{equals.get_node_path()}.B', 'double', 'None')
        controller.resolve_wild_card_pin(f'{if3.get_node_path()}.Result', 'bool', 'None')
        controller.resolve_wild_card_pin(f'{remove.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{for_each.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{remove1.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')

        controller.set_array_pin_size(f'{n(make_array)}.Values', 2)
        controller.set_array_pin_size(f'{n(make_array1)}.Values', 2)
        controller.set_array_pin_size(f'{n(make_array2)}.Values', 10)
        controller.set_array_pin_size(f'{n(make_array3)}.Values', 4)
        controller.set_array_pin_size(f'{n(select)}.Values', 2)

        graph.add_link('DISPATCH_RigVMDispatch_SwitchInt32', 'Cases.1', branch, 'ExecuteContext', controller)
        graph.add_link(branch, 'Completed', branch1, 'ExecuteContext', controller)
        graph.add_link(branch1, 'Completed', remove, 'ExecuteContext', controller)
        graph.add_link(remove, 'ExecuteContext', remove1, 'ExecuteContext', controller)
        graph.add_link(remove1, 'ExecuteContext', for_each, 'ExecuteContext', controller)
        graph.add_link(for_each, 'ExecuteContext', branch2, 'ExecuteContext', controller)
        graph.add_link('Entry', 'ik', vetala_lib_get_item, 'Array', controller)
        graph.add_link(vetala_lib_get_item, 'Element', set_transform, 'Item', controller)
        graph.add_link(vetala_lib_get_item, 'Element', project_to_new_parent1, 'Child', controller)
        graph.add_link(vetala_lib_get_item, 'Element', item_exists, 'Item', controller)
        graph.add_link(get_control_layer, 'Value', get_item_metadata1, 'Name', controller)
        graph.add_link(get_control_layer, 'Value', get_item_metadata2, 'Name', controller)
        graph.add_link(vetala_lib_get_item2, 'Element', get_item_metadata, 'Item', controller)
        graph.add_link(get_item_metadata, 'Value', get_parent1, 'Child', controller)
        graph.add_link(get_item_metadata, 'Value', project_to_new_parent1, 'OldParent', controller)
        graph.add_link(get_item_metadata, 'Value', project_to_new_parent1, 'NewParent', controller)
        graph.add_link('Entry', 'joints', vetala_lib_get_item1, 'Array', controller)
        graph.add_link(vetala_lib_get_item1, 'Element', get_item_metadata1, 'Item', controller)
        graph.add_link(vetala_lib_get_item1, 'Element', project_to_new_parent, 'Child', controller)
        graph.add_link(vetala_lib_get_item1, 'Element', project_to_new_parent3, 'Child', controller)
        graph.add_link(get_item_metadata1, 'Value', project_to_new_parent, 'OldParent', controller)
        graph.add_link(get_item_metadata1, 'Value', project_to_new_parent, 'NewParent', controller)
        graph.add_link('Entry', 'joints', vetala_lib_get_item2, 'Array', controller)
        graph.add_link(vetala_lib_get_item2, 'Element', get_item_metadata2, 'Item', controller)
        graph.add_link(vetala_lib_get_item2, 'Element', project_to_new_parent2, 'Child', controller)
        graph.add_link(vetala_lib_get_item2, 'Element', set_transform1, 'Item', controller)
        graph.add_link(basic_fabrik1, 'ExecutePin', basic_fabrik, 'ExecutePin', controller)
        graph.add_link(make_array, 'Array', basic_fabrik, 'Items', controller)
        graph.add_link(project_to_new_parent3, 'Transform', basic_fabrik, 'EffectorTransform', controller)
        graph.add_link(branch1, 'False', basic_fabrik1, 'ExecutePin', controller)
        graph.add_link(make_array1, 'Array', basic_fabrik1, 'Items', controller)
        graph.add_link(project_to_new_parent2, 'Transform', basic_fabrik1, 'EffectorTransform', controller)
        graph.add_link(get_item_metadata2, 'Value', rig_element_key, 'Value', controller)
        graph.add_link(get_item_metadata2, 'Value', project_to_new_parent2, 'OldParent', controller)
        graph.add_link(get_item_metadata2, 'Value', project_to_new_parent2, 'NewParent', controller)
        graph.add_link(get_item_metadata2, 'Value', project_to_new_parent3, 'OldParent', controller)
        graph.add_link(get_item_metadata2, 'Value', project_to_new_parent3, 'NewParent', controller)
        graph.add_link(get_item_metadata2, 'Value', get_transform, 'Item', controller)
        graph.add_link('Entry', 'joints', vetala_lib_get_item3, 'Array', controller)
        graph.add_link(vetala_lib_get_item3, 'Element', get_item_array_metadata, 'Item', controller)
        graph.add_link(make_array2, 'Array', at, 'Array', controller)
        graph.add_link(make_array2, 'Array', at10, 'Array', controller)
        graph.add_link(make_array2, 'Array', at11, 'Array', controller)
        graph.add_link(make_array2, 'Array', at12, 'Array', controller)
        graph.add_link(make_array2, 'Array', at13, 'Array', controller)
        graph.add_link(make_array2, 'Array', at5, 'Array', controller)
        graph.add_link(make_array2, 'Array', at6, 'Array', controller)
        graph.add_link(make_array2, 'Array', at7, 'Array', controller)
        graph.add_link(make_array2, 'Array', at8, 'Array', controller)
        graph.add_link(make_array2, 'Array', at9, 'Array', controller)
        graph.add_link(at, 'Element', get_name_metadata, 'Name', controller)
        graph.add_link(rig_element_key, 'Value', get_name_metadata, 'Item', controller)
        graph.add_link(get_name_metadata, 'Value', get_control_float, 'Control', controller)
        graph.add_link(get_control_float, 'FloatValue', multiply, 'A', controller)
        graph.add_link(get_control_float, 'FloatValue', multiply2, 'A', controller)
        graph.add_link(get_control_float, 'FloatValue', multiply3, 'A', controller)
        graph.add_link(make_array3, 'Array', at1, 'Array', controller)
        graph.add_link(make_array3, 'Array', at2, 'Array', controller)
        graph.add_link(make_array3, 'Array', at3, 'Array', controller)
        graph.add_link(make_array3, 'Array', at4, 'Array', controller)
        graph.add_link(vetala_lib_get_item4, 'Element', get_item_metadata3, 'Item', controller)
        graph.add_link(from_string, 'Result', get_item_metadata3, 'Name', controller)
        graph.add_link(get_item_metadata3, 'Value', get_parent, 'Child', controller)
        graph.add_link(get_joints, 'Value', vetala_lib_get_item4, 'Array', controller)
        graph.add_link(vetala_lib_get_item4, 'Element', get_item_metadata4, 'Item', controller)
        graph.add_link(vetala_lib_get_item4, 'Element', get_item_metadata5, 'Item', controller)
        graph.add_link(vetala_lib_get_item4, 'Element', get_item_metadata6, 'Item', controller)
        graph.add_link(vetala_lib_get_item4, 'Element', get_vector_metadata, 'Item', controller)
        graph.add_link(vetala_lib_get_item4, 'Element', get_vector_metadata1, 'Item', controller)
        graph.add_link(at1, 'Element', from_string, 'String', controller)
        graph.add_link(get_vector_metadata, 'Value', cross, 'A', controller)
        graph.add_link(get_vector_metadata, 'Value', vector1, 'Value', controller)
        graph.add_link(get_vector_metadata1, 'Value', cross, 'B', controller)
        graph.add_link(cross, 'Result', from_axis_and_angle3, 'Axis', controller)
        graph.add_link(cross, 'Result', negate, 'Value', controller)
        graph.add_link(get_vector_metadata1, 'Value', vector, 'Value', controller)
        graph.add_link(multiply, 'Result', evaluate_curve, 'Value', controller)
        graph.add_link(set_rotation, 'ExecutePin', set_rotation2, 'ExecutePin', controller)
        graph.add_link(get_parent, 'Parent', set_rotation, 'Item', controller)
        graph.add_link(multiply9, 'Result', set_rotation, 'Value', controller)
        graph.add_link(from_string1, 'Result', get_item_metadata4, 'Name', controller)
        graph.add_link(get_item_metadata4, 'Value', get_parent2, 'Child', controller)
        graph.add_link(at2, 'Element', from_string1, 'String', controller)
        graph.add_link(from_string2, 'Result', get_item_metadata5, 'Name', controller)
        graph.add_link(get_item_metadata5, 'Value', get_parent4, 'Child', controller)
        graph.add_link(at3, 'Element', from_string2, 'String', controller)
        graph.add_link(from_string3, 'Result', get_item_metadata6, 'Name', controller)
        graph.add_link(get_item_metadata6, 'Value', get_parent5, 'Child', controller)
        graph.add_link(at4, 'Element', from_string3, 'String', controller)
        graph.add_link(evaluate_curve, 'Result', multiply1, 'A', controller)
        graph.add_link(negate, 'Result', from_axis_and_angle, 'Axis', controller)
        graph.add_link(radians, 'Result', from_axis_and_angle, 'Angle', controller)
        graph.add_link(from_axis_and_angle, 'Result', multiply5, 'A', controller)
        graph.add_link(negate, 'Result', from_axis_and_angle1, 'Axis', controller)
        graph.add_link(negate, 'Result', from_axis_and_angle2, 'Axis', controller)
        graph.add_link(negate, 'Result', from_axis_and_angle4, 'Axis', controller)
        graph.add_link(negate, 'Result', from_axis_and_angle5, 'Axis', controller)
        graph.add_link(negate, 'Result', from_axis_and_angle6, 'Axis', controller)
        graph.add_link(get_parent1, 'Parent', get_parent6, 'Child', controller)
        graph.add_link(get_parent1, 'Parent', set_rotation1, 'Item', controller)
        graph.add_link(set_rotation6, 'ExecutePin', set_rotation1, 'ExecutePin', controller)
        graph.add_link(set_rotation1, 'ExecutePin', set_rotation3, 'ExecutePin', controller)
        graph.add_link(multiply7, 'Result', set_rotation1, 'Value', controller)
        graph.add_link(multiply1, 'Result', radians, 'Value', controller)
        graph.add_link(get_control_float1, 'FloatValue', multiply1, 'B', controller)
        graph.add_link(get_name_metadata1, 'Value', get_control_float1, 'Control', controller)
        graph.add_link(rig_element_key, 'Value', get_name_metadata1, 'Item', controller)
        graph.add_link(at7, 'Element', get_name_metadata1, 'Name', controller)
        graph.add_link(multiply3, 'Result', evaluate_curve1, 'Value', controller)
        graph.add_link(evaluate_curve1, 'Result', radians1, 'Value', controller)
        graph.add_link(radians1, 'Result', from_axis_and_angle1, 'Angle', controller)
        graph.add_link(from_axis_and_angle1, 'Result', multiply6, 'A', controller)
        graph.add_link(multiply2, 'Result', evaluate_curve2, 'Value', controller)
        graph.add_link(evaluate_curve2, 'Result', radians2, 'Value', controller)
        graph.add_link(set_rotation2, 'ExecutePin', set_rotation6, 'ExecutePin', controller)
        graph.add_link(get_parent2, 'Parent', set_rotation2, 'Item', controller)
        graph.add_link(multiply10, 'Result', set_rotation2, 'Value', controller)
        graph.add_link(radians2, 'Result', from_axis_and_angle2, 'Angle', controller)
        graph.add_link(from_axis_and_angle2, 'Result', multiply4, 'A', controller)
        graph.add_link(at5, 'Element', get_name_metadata2, 'Name', controller)
        graph.add_link(rig_element_key, 'Value', get_name_metadata2, 'Item', controller)
        graph.add_link(get_name_metadata2, 'Value', get_control_float2, 'Control', controller)
        graph.add_link(get_control_float2, 'FloatValue', radians3, 'Value', controller)
        graph.add_link(radians3, 'Result', from_axis_and_angle3, 'Angle', controller)
        graph.add_link(from_axis_and_angle3, 'Result', multiply4, 'B', controller)
        graph.add_link(multiply4, 'Result', multiply10, 'A', controller)
        graph.add_link(at6, 'Element', get_name_metadata3, 'Name', controller)
        graph.add_link(rig_element_key, 'Value', get_name_metadata3, 'Item', controller)
        graph.add_link(get_name_metadata3, 'Value', get_control_float3, 'Control', controller)
        graph.add_link(get_control_float3, 'FloatValue', radians4, 'Value', controller)
        graph.add_link(radians4, 'Result', from_axis_and_angle4, 'Angle', controller)
        graph.add_link(from_axis_and_angle4, 'Result', multiply5, 'B', controller)
        graph.add_link(multiply5, 'Result', multiply7, 'B', controller)
        graph.add_link(rig_element_key, 'Value', get_name_metadata9, 'Item', controller)
        graph.add_link(rig_element_key, 'Value', get_name_metadata4, 'Item', controller)
        graph.add_link(rig_element_key, 'Value', get_name_metadata5, 'Item', controller)
        graph.add_link(rig_element_key, 'Value', get_name_metadata6, 'Item', controller)
        graph.add_link(rig_element_key, 'Value', get_name_metadata7, 'Item', controller)
        graph.add_link(rig_element_key, 'Value', get_name_metadata8, 'Item', controller)
        graph.add_link(rig_element_key, 'Value', get_parent3, 'Child', controller)
        graph.add_link(at8, 'Element', get_name_metadata4, 'Name', controller)
        graph.add_link(get_name_metadata4, 'Value', get_control_float4, 'Control', controller)
        graph.add_link(get_control_float4, 'FloatValue', radians5, 'Value', controller)
        graph.add_link(radians5, 'Result', from_axis_and_angle5, 'Angle', controller)
        graph.add_link(from_axis_and_angle5, 'Result', multiply6, 'B', controller)
        graph.add_link(multiply6, 'Result', multiply9, 'A', controller)
        graph.add_link(at9, 'Element', get_name_metadata5, 'Name', controller)
        graph.add_link(get_name_metadata5, 'Value', get_control_float5, 'Control', controller)
        graph.add_link(get_control_float5, 'FloatValue', radians6, 'Value', controller)
        graph.add_link(get_parent3, 'Parent', set_rotation3, 'Item', controller)
        graph.add_link(set_rotation3, 'ExecutePin', set_rotation4, 'ExecutePin', controller)
        graph.add_link(from_axis_and_angle6, 'Result', set_rotation3, 'Value', controller)
        graph.add_link(radians6, 'Result', from_axis_and_angle6, 'Angle', controller)
        graph.add_link(vector1, 'Value', from_axis_and_angle7, 'Axis', controller)
        graph.add_link(from_axis_and_angle7, 'Result', multiply7, 'A', controller)
        graph.add_link(at10, 'Element', get_name_metadata6, 'Name', controller)
        graph.add_link(get_name_metadata6, 'Value', get_control_float6, 'Control', controller)
        graph.add_link(get_control_float6, 'FloatValue', radians7, 'Value', controller)
        graph.add_link(radians7, 'Result', greater, 'A', controller)
        graph.add_link(greater, 'Result', if1, 'Condition', controller)
        graph.add_link(from_axis_and_angle8, 'Result', if1, 'True', controller)
        graph.add_link(if1, 'Result', set_rotation4, 'Value', controller)
        graph.add_link(vector1, 'Value', from_axis_and_angle8, 'Axis', controller)
        graph.add_link(radians7, 'Result', from_axis_and_angle8, 'Angle', controller)
        graph.add_link(vector1, 'Value', negate1, 'Value', controller)
        graph.add_link(negate1, 'Result', from_axis_and_angle9, 'Axis', controller)
        graph.add_link(multiply8, 'Result', from_axis_and_angle9, 'Angle', controller)
        graph.add_link(from_axis_and_angle9, 'Result', if2, 'True', controller)
        graph.add_link(less, 'Result', if2, 'Condition', controller)
        graph.add_link(if2, 'Result', set_rotation5, 'Value', controller)
        graph.add_link(radians7, 'Result', less, 'A', controller)
        graph.add_link(get_parent4, 'Parent', set_rotation4, 'Item', controller)
        graph.add_link(get_parent5, 'Parent', set_rotation5, 'Item', controller)
        graph.add_link(set_rotation4, 'ExecutePin', set_rotation5, 'ExecutePin', controller)
        graph.add_link(radians7, 'Result', multiply8, 'A', controller)
        graph.add_link(at11, 'Element', get_name_metadata7, 'Name', controller)
        graph.add_link(get_name_metadata7, 'Value', get_control_float7, 'Control', controller)
        graph.add_link(get_control_float7, 'FloatValue', radians8, 'Value', controller)
        graph.add_link(at12, 'Element', get_name_metadata8, 'Name', controller)
        graph.add_link(get_name_metadata8, 'Value', get_control_float8, 'Control', controller)
        graph.add_link(get_control_float8, 'FloatValue', radians9, 'Value', controller)
        graph.add_link(at13, 'Element', get_name_metadata9, 'Name', controller)
        graph.add_link(get_name_metadata9, 'Value', get_control_float9, 'Control', controller)
        graph.add_link(get_control_float9, 'FloatValue', radians10, 'Value', controller)
        graph.add_link(vector, 'Value', from_axis_and_angle10, 'Axis', controller)
        graph.add_link(radians8, 'Result', from_axis_and_angle10, 'Angle', controller)
        graph.add_link(from_axis_and_angle10, 'Result', multiply9, 'B', controller)
        graph.add_link(vector, 'Value', from_axis_and_angle11, 'Axis', controller)
        graph.add_link(radians9, 'Result', from_axis_and_angle11, 'Angle', controller)
        graph.add_link(from_axis_and_angle11, 'Result', set_rotation6, 'Value', controller)
        graph.add_link(vector, 'Value', from_axis_and_angle12, 'Axis', controller)
        graph.add_link(get_parent6, 'Parent', set_rotation6, 'Item', controller)
        graph.add_link(radians10, 'Result', from_axis_and_angle12, 'Angle', controller)
        graph.add_link(from_axis_and_angle12, 'Result', multiply10, 'B', controller)
        graph.add_link('Entry', 'fk_first', to_integer, 'Value', controller)
        graph.add_link(to_integer, 'Result', select, 'Index', controller)
        graph.add_link(item_exists, 'Exists', branch, 'Condition', controller)
        graph.add_link(branch, 'True', set_transform, 'ExecutePin', controller)
        graph.add_link(project_to_new_parent1, 'Transform', set_transform, 'Value', controller)
        graph.add_link('Entry', 'switch_control', vetala_lib_get_item5, 'Array', controller)
        graph.add_link(vetala_lib_get_item5, 'Element', item_exists1, 'Item', controller)
        graph.add_link(vetala_lib_get_item5, 'Element', get_item_metadata7, 'Item', controller)
        graph.add_link(item_exists1, 'Exists', if3, 'Condition', controller)
        graph.add_link(get_item_metadata7, 'Value', get_float_channel, 'Item', controller)
        graph.add_link(get_float_channel, 'Value', equals, 'B', controller)
        graph.add_link(select, 'Result', equals, 'A', controller)
        graph.add_link(equals, 'Result', if3, 'True', controller)
        graph.add_link(if3, 'Result', branch1, 'Condition', controller)
        graph.add_link(if3, 'Result', not1, 'Value', controller)
        graph.add_link(branch1, 'True', set_transform1, 'ExecutePin', controller)
        graph.add_link(get_transform, 'Transform', set_transform1, 'Value', controller)
        graph.add_link(get_item_array_metadata, 'Value', remove, 'Array', controller)
        graph.add_link(remove, 'Array', remove1, 'Array', controller)
        graph.add_link(remove1, 'Array', for_each, 'Array', controller)
        graph.add_link(for_each, 'Element', set_control_visibility, 'Item', controller)
        graph.add_link(for_each, 'Element', item_exists2, 'Item', controller)
        graph.add_link(branch2, 'True', set_control_visibility, 'ExecutePin', controller)
        graph.add_link(not1, 'Result', set_control_visibility, 'bVisible', controller)
        graph.add_link(item_exists2, 'Exists', branch2, 'Condition', controller)
        graph.add_link(vetala_lib_get_item1, 'Element', make_array, 'Values.1', controller)
        graph.add_link(vetala_lib_get_item2, 'Element', make_array, 'Values.0', controller)
        graph.add_link(vetala_lib_get_item2, 'Element', make_array1, 'Values.1', controller)
        graph.add_link(vetala_lib_get_item3, 'Element', make_array1, 'Values.0', controller)

        graph.set_pin(vetala_lib_get_item, 'index', '-1', controller)
        graph.set_pin(get_item_metadata, 'Name', 'ik', controller)
        graph.set_pin(get_item_metadata, 'NameSpace', 'Self', controller)
        graph.set_pin(get_item_metadata, 'Default', '(Type=Bone,Name="None")', controller)
        graph.set_pin(vetala_lib_get_item1, 'index', '2', controller)
        graph.set_pin(get_item_metadata1, 'NameSpace', 'Self', controller)
        graph.set_pin(get_item_metadata1, 'Default', '(Type=Bone,Name="None")', controller)
        graph.set_pin(vetala_lib_get_item2, 'index', '1', controller)
        graph.set_pin(basic_fabrik, 'Precision', '0.001000', controller)
        graph.set_pin(basic_fabrik, 'Weight', '1.000000', controller)
        graph.set_pin(basic_fabrik, 'bPropagateToChildren', 'True', controller)
        graph.set_pin(basic_fabrik, 'MaxIterations', '60', controller)
        graph.set_pin(basic_fabrik, 'WorkData', '(CachedEffector=(Key=(Type=None,Name="None"),Index=65535,ContainerVersion=-1))', controller)
        graph.set_pin(basic_fabrik, 'bSetEffectorTransform', 'false', controller)
        graph.set_pin(make_array, 'Values', '((Type=None,Name="None"),((),Type=None,Name="None"))', controller)
        graph.set_pin(basic_fabrik1, 'Precision', '0.000100', controller)
        graph.set_pin(basic_fabrik1, 'Weight', '1.000000', controller)
        graph.set_pin(basic_fabrik1, 'bPropagateToChildren', 'True', controller)
        graph.set_pin(basic_fabrik1, 'MaxIterations', '60', controller)
        graph.set_pin(basic_fabrik1, 'WorkData', '(CachedEffector=(Key=(Type=None,Name="None"),Index=65535,ContainerVersion=-1))', controller)
        graph.set_pin(basic_fabrik1, 'bSetEffectorTransform', 'false', controller)
        graph.set_pin(make_array1, 'Values', '((Type=None,Name="None"),((),Type=None,Name="None"))', controller)
        graph.set_pin(get_item_metadata2, 'NameSpace', 'Self', controller)
        graph.set_pin(get_item_metadata2, 'Default', '(Type=Bone,Name="None")', controller)
        graph.set_pin(project_to_new_parent, 'bChildInitial', 'True', controller)
        graph.set_pin(project_to_new_parent, 'bOldParentInitial', 'True', controller)
        graph.set_pin(project_to_new_parent, 'bNewParentInitial', 'False', controller)
        graph.set_pin(make_array2, 'Values', '("roll","rollOffset","heel","ball","toe","toeRotate","yaw","toePivot","ballPivot","heelPivot")', controller)
        graph.set_pin(at, 'Index', '0', controller)
        graph.set_pin(get_name_metadata, 'NameSpace', 'Self', controller)
        graph.set_pin(make_array3, 'Values', '("toe","heel","yaw_out","yaw_in")', controller)
        graph.set_pin(get_item_metadata3, 'NameSpace', 'Self', controller)
        graph.set_pin(get_item_metadata3, 'Default', '(Type=Bone,Name="None")', controller)
        graph.set_pin(vetala_lib_get_item4, 'index', '-1', controller)
        graph.set_pin(at1, 'Index', '0', controller)
        graph.set_pin(get_vector_metadata, 'Name', 'forward_axis', controller)
        graph.set_pin(get_vector_metadata, 'NameSpace', 'Self', controller)
        graph.set_pin(get_vector_metadata, 'Default', '(X=0.000000,Y=0.000000,Z=0.000000)', controller)
        graph.set_pin(get_vector_metadata1, 'Name', 'up_axis', controller)
        graph.set_pin(get_vector_metadata1, 'NameSpace', 'Self', controller)
        graph.set_pin(get_vector_metadata1, 'Default', '(X=0.000000,Y=0.000000,Z=0.000000)', controller)
        graph.set_pin(multiply, 'B', '0.100000', controller)
        graph.set_pin(set_rotation, 'Space', 'LocalSpace', controller)
        graph.set_pin(set_rotation, 'bInitial', 'False', controller)
        graph.set_pin(set_rotation, 'Weight', '1.000000', controller)
        graph.set_pin(set_rotation, 'bPropagateToChildren', 'True', controller)
        graph.set_pin(get_item_metadata4, 'NameSpace', 'Self', controller)
        graph.set_pin(get_item_metadata4, 'Default', '(Type=Bone,Name="None")', controller)
        graph.set_pin(at2, 'Index', '1', controller)
        graph.set_pin(get_item_metadata5, 'NameSpace', 'Self', controller)
        graph.set_pin(get_item_metadata5, 'Default', '(Type=Bone,Name="None")', controller)
        graph.set_pin(at3, 'Index', '2', controller)
        graph.set_pin(get_item_metadata6, 'NameSpace', 'Self', controller)
        graph.set_pin(get_item_metadata6, 'Default', '(Type=Bone,Name="None")', controller)
        graph.set_pin(at4, 'Index', '3', controller)
        graph.set_pin(evaluate_curve, 'Curve', '(EditorCurveData=(Keys=((),(Time=0.500000,Value=1.000000),(Time=1.000000))))', controller)
        graph.set_pin(evaluate_curve, 'SourceMinimum', '0.000000', controller)
        graph.set_pin(evaluate_curve, 'SourceMaximum', '1.000000', controller)
        graph.set_pin(evaluate_curve, 'TargetMinimum', '0.000000', controller)
        graph.set_pin(evaluate_curve, 'TargetMaximum', '1.000000', controller)
        graph.set_pin(get_parent, 'bDefaultParent', 'True', controller)
        graph.set_pin(get_parent1, 'bDefaultParent', 'True', controller)
        graph.set_pin(set_rotation1, 'Space', 'LocalSpace', controller)
        graph.set_pin(set_rotation1, 'bInitial', 'False', controller)
        graph.set_pin(set_rotation1, 'Weight', '1.000000', controller)
        graph.set_pin(set_rotation1, 'bPropagateToChildren', 'True', controller)
        graph.set_pin(get_name_metadata1, 'NameSpace', 'Self', controller)
        graph.set_pin(evaluate_curve1, 'Curve', '(EditorCurveData=(Keys=((),(Time=0.250000),(InterpMode=RCIM_Constant,Time=1.000000,Value=1.000000))))', controller)
        graph.set_pin(evaluate_curve1, 'SourceMinimum', '0.000000', controller)
        graph.set_pin(evaluate_curve1, 'SourceMaximum', '2.000000', controller)
        graph.set_pin(evaluate_curve1, 'TargetMinimum', '0.000000', controller)
        graph.set_pin(evaluate_curve1, 'TargetMaximum', '90.000000', controller)
        graph.set_pin(evaluate_curve2, 'Curve', '(EditorCurveData=(Keys=((),(InterpMode=RCIM_Constant,Time=1.000000,Value=1.000000))))', controller)
        graph.set_pin(evaluate_curve2, 'SourceMinimum', '0.000000', controller)
        graph.set_pin(evaluate_curve2, 'SourceMaximum', '2.000000', controller)
        graph.set_pin(evaluate_curve2, 'TargetMinimum', '0.000000', controller)
        graph.set_pin(evaluate_curve2, 'TargetMaximum', '-90.000000', controller)
        graph.set_pin(multiply2, 'B', '-0.100000', controller)
        graph.set_pin(set_rotation2, 'Space', 'LocalSpace', controller)
        graph.set_pin(set_rotation2, 'bInitial', 'False', controller)
        graph.set_pin(set_rotation2, 'Weight', '1.000000', controller)
        graph.set_pin(set_rotation2, 'bPropagateToChildren', 'True', controller)
        graph.set_pin(get_parent2, 'bDefaultParent', 'True', controller)
        graph.set_pin(multiply3, 'B', '0.100000', controller)
        graph.set_pin(at5, 'Index', '2', controller)
        graph.set_pin(get_name_metadata2, 'NameSpace', 'Self', controller)
        graph.set_pin(at6, 'Index', '3', controller)
        graph.set_pin(get_name_metadata3, 'NameSpace', 'Self', controller)
        graph.set_pin(at7, 'Index', '1', controller)
        graph.set_pin(at8, 'Index', '4', controller)
        graph.set_pin(get_name_metadata4, 'NameSpace', 'Self', controller)
        graph.set_pin(at9, 'Index', '5', controller)
        graph.set_pin(get_name_metadata5, 'NameSpace', 'Self', controller)
        graph.set_pin(get_parent3, 'bDefaultParent', 'True', controller)
        graph.set_pin(set_rotation3, 'Space', 'LocalSpace', controller)
        graph.set_pin(set_rotation3, 'bInitial', 'False', controller)
        graph.set_pin(set_rotation3, 'Weight', '1.000000', controller)
        graph.set_pin(set_rotation3, 'bPropagateToChildren', 'True', controller)
        graph.set_pin(from_axis_and_angle7, 'Angle', '0.000000', controller)
        graph.set_pin(at10, 'Index', '6', controller)
        graph.set_pin(get_name_metadata6, 'NameSpace', 'Self', controller)
        graph.set_pin(greater, 'B', '0.000000', controller)
        graph.set_pin(if1, 'False', '(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000)', controller)
        graph.set_pin(if2, 'False', '(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000)', controller)
        graph.set_pin(less, 'B', '0.000000', controller)
        graph.set_pin(get_parent4, 'bDefaultParent', 'True', controller)
        graph.set_pin(get_parent5, 'bDefaultParent', 'True', controller)
        graph.set_pin(set_rotation4, 'Space', 'LocalSpace', controller)
        graph.set_pin(set_rotation4, 'bInitial', 'False', controller)
        graph.set_pin(set_rotation4, 'Weight', '1.000000', controller)
        graph.set_pin(set_rotation4, 'bPropagateToChildren', 'True', controller)
        graph.set_pin(set_rotation5, 'Space', 'LocalSpace', controller)
        graph.set_pin(set_rotation5, 'bInitial', 'False', controller)
        graph.set_pin(set_rotation5, 'Weight', '1.000000', controller)
        graph.set_pin(set_rotation5, 'bPropagateToChildren', 'True', controller)
        graph.set_pin(multiply8, 'B', '-1.000000', controller)
        graph.set_pin(at11, 'Index', '7', controller)
        graph.set_pin(get_name_metadata7, 'NameSpace', 'Self', controller)
        graph.set_pin(at12, 'Index', '8', controller)
        graph.set_pin(get_name_metadata8, 'NameSpace', 'Self', controller)
        graph.set_pin(at13, 'Index', '9', controller)
        graph.set_pin(get_name_metadata9, 'NameSpace', 'Self', controller)
        graph.set_pin(set_rotation6, 'Space', 'LocalSpace', controller)
        graph.set_pin(set_rotation6, 'bInitial', 'False', controller)
        graph.set_pin(set_rotation6, 'Weight', '1.000000', controller)
        graph.set_pin(set_rotation6, 'bPropagateToChildren', 'True', controller)
        graph.set_pin(get_parent6, 'bDefaultParent', 'True', controller)
        graph.set_pin(set_transform, 'Space', 'GlobalSpace', controller)
        graph.set_pin(set_transform, 'bInitial', 'False', controller)
        graph.set_pin(set_transform, 'Weight', '1.000000', controller)
        graph.set_pin(set_transform, 'bPropagateToChildren', 'True', controller)
        graph.set_pin(project_to_new_parent1, 'bChildInitial', 'True', controller)
        graph.set_pin(project_to_new_parent1, 'bOldParentInitial', 'True', controller)
        graph.set_pin(project_to_new_parent1, 'bNewParentInitial', 'False', controller)
        graph.set_pin(get_item_metadata7, 'Name', 'SwitchChannel', controller)
        graph.set_pin(get_item_metadata7, 'NameSpace', 'Self', controller)
        graph.set_pin(get_item_metadata7, 'Default', '(Type=Bone,Name="None")', controller)
        graph.set_pin(get_float_channel, 'bInitial', 'False', controller)
        graph.set_pin(select, 'Values', '(1.000000,0.000000)', controller)
        graph.set_pin(if3, 'False', 'true', controller)
        graph.set_pin(project_to_new_parent2, 'bChildInitial', 'True', controller)
        graph.set_pin(project_to_new_parent2, 'bOldParentInitial', 'True', controller)
        graph.set_pin(project_to_new_parent2, 'bNewParentInitial', 'False', controller)
        graph.set_pin(set_transform1, 'Space', 'GlobalSpace', controller)
        graph.set_pin(set_transform1, 'bInitial', 'False', controller)
        graph.set_pin(set_transform1, 'Weight', '1.000000', controller)
        graph.set_pin(set_transform1, 'bPropagateToChildren', 'True', controller)
        graph.set_pin(project_to_new_parent3, 'bChildInitial', 'True', controller)
        graph.set_pin(project_to_new_parent3, 'bOldParentInitial', 'True', controller)
        graph.set_pin(project_to_new_parent3, 'bNewParentInitial', 'False', controller)
        graph.set_pin(get_transform, 'Space', 'GlobalSpace', controller)
        graph.set_pin(get_transform, 'bInitial', 'False', controller)
        graph.set_pin(get_item_array_metadata, 'Name', 'Controls_0', controller)
        graph.set_pin(get_item_array_metadata, 'NameSpace', 'Self', controller)
        graph.set_pin(remove, 'Index', '5', controller)
        graph.set_pin(remove1, 'Index', '0', controller)

        current_locals = locals()
        nodes = unreal_lib.graph.filter_nodes(current_locals.values())
        node = unreal_lib.graph.comment_nodes(nodes, controller, 'Forward Solve')
        nodes.append(node)
        unreal_lib.graph.move_nodes(700, 400, nodes, controller)

    def _build_function_backward_graph(self):
        return


class UnrealIkQuadrupedRig(UnrealUtilRig):

    def _build_controls(self, controller, library):

        get_local_controls = controller.add_variable_node_from_object_path('local_controls', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(3024.0, -1596.0), 'Get local_controls')

        vetala_lib_find_pole_vector = controller.add_function_reference_node(library.find_function('vetalaLib_findPoleVector'), unreal.Vector2D(4744.0, -1496.0), 'vetalaLib_findPoleVector')
        for_each = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayIterator(in Array,out Element,out Index,out Count,out Ratio)', unreal.Vector2D(1452.0, -1592.0), 'For Each')
        vetala_lib_control = self._create_control(controller, 2452.0, -1642.0)
        vetala_lib_get_parent = controller.add_function_reference_node(library.find_function('vetalaLib_GetParent'), unreal.Vector2D(1864.0, -1800.0), 'vetalaLib_GetParent')
        vetala_lib_get_joint_description = controller.add_function_reference_node(library.find_function('vetalaLib_GetJointDescription'), unreal.Vector2D(1952.0, -1476.0), 'vetalaLib_GetJointDescription')
        set_item_metadata = controller.add_template_node('DISPATCH_RigDispatch_SetMetadata(in Item,in Name,in NameSpace,in Value,out Success)', unreal.Vector2D(2784.0, -1852.0), 'Set Item Metadata')
        get_control_layer = controller.add_variable_node('control_layer', 'FName', None, True, '', unreal.Vector2D(1280.0, -1732.0), 'Get control_layer')
        equals = controller.add_template_node('DISPATCH_RigVMDispatch_CoreEquals(in A,in B,out Result)', unreal.Vector2D(1632.0, -1796.0), 'Equals')
        get_description = controller.add_variable_node('description', 'FString', None, True, '', unreal.Vector2D(1000.0, -972.0), 'Get description')
        get_use_joint_name = controller.add_variable_node('use_joint_name', 'bool', None, True, '', unreal.Vector2D(1848.0, -988.0), 'Get use_joint_name')
        get_joint_token = controller.add_variable_node('joint_token', 'FString', None, True, '', unreal.Vector2D(1452.0, -1342.0), 'Get joint_token')
        if1 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(2202.0, -1042.0), 'If')
        get_world = controller.add_variable_node('world', 'bool', None, True, '', unreal.Vector2D(1200.0, -1188.0), 'Get world')
        get_mirror = controller.add_variable_node('mirror', 'bool', None, True, '', unreal.Vector2D(1200.0, -1088.0), 'Get mirror')
        add = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayAdd(io Array,in Element,out Index)', unreal.Vector2D(3384.0, -1816.0), 'Add')
        get_pole_vector_shape = controller.add_variable_node('pole_vector_shape', 'FString', None, True, '', unreal.Vector2D(3052.0, -1367.0), 'Get pole_vector_shape')
        from_string = controller.add_template_node('DISPATCH_RigDispatch_FromString(in String,out Result)', unreal.Vector2D(3252.0, -1342.0), 'From String')
        shape_exists = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_ShapeExists', 'Execute', unreal.Vector2D(3452.0, -1342.0), 'Shape Exists')
        if2 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(3376.0, -1540.0), 'If')
        set_shape_settings = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchySetShapeSettings', 'Execute', unreal.Vector2D(3652.0, -1442.0), 'Set Shape Settings')
        vetala_lib_parent = controller.add_function_reference_node(library.find_function('vetalaLib_Parent'), unreal.Vector2D(4052.0, -1342.0), 'vetalaLib_Parent')
        vetala_lib_parent1 = controller.add_function_reference_node(library.find_function('vetalaLib_Parent'), unreal.Vector2D(4352.0, -1142.0), 'vetalaLib_Parent')
        get_color = controller.add_variable_node_from_object_path('color', 'TArray<FLinearColor>', '/Script/CoreUObject.LinearColor', True, '()', unreal.Vector2D(3052.0, -1292.0), 'Get color')
        at = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(3352.0, -1242.0), 'At')
        at1 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(3424.0, -1076.0), 'At')
        at2 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(3424.0, -948.0), 'At')
        at3 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(3432.0, -796.0), 'At')
        get_shape_scale = controller.add_variable_node_from_object_path('shape_scale', 'TArray<FVector>', '/Script/CoreUObject.Vector', True, '()', unreal.Vector2D(2652.0, -1442.0), 'Get shape_scale')
        at4 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(2802.0, -1442.0), 'At')
        multiply = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathVectorMul', 'Execute', unreal.Vector2D(2952.0, -1442.0), 'Multiply')
        get_joints = controller.add_variable_node_from_object_path('joints', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(3824.0, -1604.0), 'Get joints')
        at5 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(4096.0, -1708.0), 'At')
        at6 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(4096.0, -1608.0), 'At')
        at7 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(4096.0, -1508.0), 'At')
        get_pole_vector_offset = controller.add_variable_node('pole_vector_offset', 'float', None, True, '', unreal.Vector2D(4352.0, -1592.0), 'Get pole_vector_offset')
        set_translation = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_SetTranslation', 'Execute', unreal.Vector2D(5152.0, -1444.0), 'Set Translation')
        greater = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathIntGreater', 'Execute', unreal.Vector2D(744.0, -1608.0), 'Greater')
        if3 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(944.0, -1508.0), 'If')
        if4 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(5496.0, -524.0), 'If')
        get_item_array_metadata = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(5032.0, -540.0), 'Get Item Array Metadata')
        vetala_lib_get_item = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(5768.0, -572.0), 'vetalaLib_GetItem')
        get_transform = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetTransform', 'Execute', unreal.Vector2D(5792.0, -1404.0), 'Get Transform')
        get_local_ik = controller.add_variable_node_from_object_path('local_ik', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(6144.0, -1236.0), 'Get local_ik')
        add1 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayAdd(io Array,in Element,out Index)', unreal.Vector2D(6304.0, -1524.0), 'Add')
        num = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetNum(in Array,out Num)', unreal.Vector2D(5192.0, -332.0), 'Num')
        greater1 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathIntGreater', 'Execute', unreal.Vector2D(5352.0, -380.0), 'Greater')
        get_joints1 = controller.add_variable_node_from_object_path('joints', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(5608.0, -972.0), 'Get joints')
        vetala_lib_get_item1 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(6256.0, -1028.0), 'vetalaLib_GetItem')
        set_item_array_metadata = controller.add_template_node('DISPATCH_RigDispatch_SetMetadata(in Item,in Name,in NameSpace,in Value,out Success)', unreal.Vector2D(6576.0, -1548.0), 'Set Item Array Metadata')
        spawn_bool_animation_channel = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyAddAnimationChannelBool', 'Execute', unreal.Vector2D(7072.0, -1508.0), 'Spawn Bool Animation Channel')
        spawn_float_animation_channel = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyAddAnimationChannelFloat', 'Execute', unreal.Vector2D(7088.0, -948.0), 'Spawn Float Animation Channel')
        rig_element_key = controller.add_free_reroute_node('FRigElementKey', unreal.load_object(None, '/Script/ControlRig.RigElementKey').get_name(), is_constant=False, custom_widget_name='', default_value='', position=[6858.0, -1111.0], node_name='', setup_undo_redo=True)
        spawn_float_animation_channel1 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyAddAnimationChannelFloat', 'Execute', unreal.Vector2D(5472.0, -1428.0), 'Spawn Float Animation Channel')
        num1 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetNum(in Array,out Num)', unreal.Vector2D(864.0, -676.0), 'Num')
        equals1 = controller.add_template_node('DISPATCH_RigVMDispatch_CoreEquals(in A,in B,out Result)', unreal.Vector2D(1880.0, -236.0), 'Equals')
        branch = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_ControlFlowBranch', 'Execute', unreal.Vector2D(2912.0, -1092.0), 'Branch')
        get_local_controls1 = controller.add_variable_node_from_object_path('local_controls', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(3072.0, -884.0), 'Get local_controls')
        at8 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(4648.0, -748.0), 'At')
        vetala_lib_parent2 = controller.add_function_reference_node(library.find_function('vetalaLib_Parent'), unreal.Vector2D(3296.0, -532.0), 'vetalaLib_Parent')
        branch1 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_ControlFlowBranch', 'Execute', unreal.Vector2D(6816.0, -740.0), 'Branch')
        make_array = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayMake(in Values,out Array)', unreal.Vector2D(1584.0, -628.0), 'Make Array')
        get_joints2 = controller.add_variable_node_from_object_path('joints', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(600.0, -812.0), 'Get joints')
        at9 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(1256.0, -652.0), 'At')
        at10 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(1256.0, -428.0), 'At')
        or1 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathBoolOr', 'Execute', unreal.Vector2D(2600.0, -300.0), 'Or')
        at11 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(1256.0, -540.0), 'At')
        at12 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(1256.0, -300.0), 'At')
        at13 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(3432.0, -668.0), 'At')
        vetala_lib_parent3 = controller.add_function_reference_node(library.find_function('vetalaLib_Parent'), unreal.Vector2D(4584.0, -1052.0), 'vetalaLib_Parent')
        equals2 = controller.add_template_node('DISPATCH_RigVMDispatch_CoreEquals(in A,in B,out Result)', unreal.Vector2D(1816.0, -892.0), 'Equals')
        if5 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(2040.0, -860.0), 'If')
        concat = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_StringConcat', 'Execute', unreal.Vector2D(1864.0, -716.0), 'Concat')
        if6 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(2264.0, -764.0), 'If')
        equals3 = controller.add_template_node('DISPATCH_RigVMDispatch_CoreEquals(in A,in B,out Result)', unreal.Vector2D(2216.0, -908.0), 'Equals')
        if7 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(2506.583251953125, -779.2752685546875), 'If')
        set_transform = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_SetTransform', 'Execute', unreal.Vector2D(4968.0, -1004.0), 'Set Transform')
        get_transform1 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetTransform', 'Execute', unreal.Vector2D(3960.0, -700.0), 'Get Transform')
        if8 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(2088.0, -588.0), 'If')
        if9 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(2376.0, -588.0), 'If')
        vetala_lib_get_item2 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(5304.0, -732.0), 'vetalaLib_GetItem')
        equals4 = controller.add_template_node('DISPATCH_RigVMDispatch_CoreEquals(in A,in B,out Result)', unreal.Vector2D(774.762939453125, -932.4758911132812), 'Equals')
        branch2 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_ControlFlowBranch', 'Execute', unreal.Vector2D(832.0, -1276.0), 'Branch')
        get_transform2 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetTransform', 'Execute', unreal.Vector2D(5568.0, -812.0), 'Get Transform')
        at14 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(5392.0, -940.0), 'At')
        vetala_lib_parent4 = controller.add_function_reference_node(library.find_function('vetalaLib_Parent'), unreal.Vector2D(7516.99755859375, -1683.9906005859375), 'vetalaLib_Parent')
        spawn_transform_control = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyAddControlTransform', 'Execute', unreal.Vector2D(5872.0, -1840.0), 'Spawn Transform Control')
        spawn_transform_control1 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyAddControlTransform', 'Execute', unreal.Vector2D(7056.0, -1872.0), 'Spawn Transform Control')

        controller.resolve_wild_card_pin(f'{for_each.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{equals.get_node_path()}.A', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{equals.get_node_path()}.B', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{if1.get_node_path()}.Result', 'FString', 'None')
        controller.resolve_wild_card_pin(f'{add.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{if2.get_node_path()}.Result', 'FName', 'None')
        controller.resolve_wild_card_pin(f'{at.get_node_path()}.Array', 'TArray<FLinearColor>', '/Script/CoreUObject.LinearColor')
        controller.resolve_wild_card_pin(f'{at1.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{at2.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{at3.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{at4.get_node_path()}.Array', 'TArray<FVector>', '/Script/CoreUObject.Vector')
        controller.resolve_wild_card_pin(f'{at5.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{at6.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{at7.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{greater.get_node_path()}.A', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{greater.get_node_path()}.B', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{if3.get_node_path()}.Result', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{if4.get_node_path()}.Result', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{add1.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{num.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{greater1.get_node_path()}.A', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{greater1.get_node_path()}.B', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{num1.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{equals1.get_node_path()}.A', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{equals1.get_node_path()}.B', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{at8.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{make_array.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{at9.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{at10.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{at11.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{at12.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{at13.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{equals2.get_node_path()}.A', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{equals2.get_node_path()}.B', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{if5.get_node_path()}.Result', 'FString', 'None')
        controller.resolve_wild_card_pin(f'{concat.get_node_path()}.Result', 'FString', 'None')
        controller.resolve_wild_card_pin(f'{if6.get_node_path()}.Result', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{equals3.get_node_path()}.A', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{equals3.get_node_path()}.B', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{if7.get_node_path()}.Result', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{if8.get_node_path()}.Result', 'FString', 'None')
        controller.resolve_wild_card_pin(f'{if9.get_node_path()}.Result', 'float', 'None')
        controller.resolve_wild_card_pin(f'{equals4.get_node_path()}.A', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{equals4.get_node_path()}.B', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{at14.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')

        controller.set_array_pin_size(f'{n(if4)}.False', 1)
        controller.set_array_pin_size(f'{n(make_array)}.Values', 4)

        graph.add_link(set_transform, 'ExecutePin', vetala_lib_find_pole_vector, 'ExecuteContext', controller)
        graph.add_link(vetala_lib_find_pole_vector, 'ExecuteContext', set_translation, 'ExecutePin', controller)
        graph.add_link(branch2, 'True', for_each, 'ExecuteContext', controller)
        graph.add_link(for_each, 'ExecuteContext', vetala_lib_get_joint_description, 'ExecuteContext', controller)
        graph.add_link(for_each, 'Completed', branch, 'ExecuteContext', controller)
        graph.add_link(vetala_lib_get_joint_description, 'ExecuteContext', vetala_lib_control, 'ExecuteContext', controller)
        graph.add_link(vetala_lib_control, 'ExecuteContext', set_item_metadata, 'ExecuteContext', controller)
        graph.add_link(set_item_metadata, 'ExecuteContext', add, 'ExecuteContext', controller)
        graph.add_link(set_shape_settings, 'ExecutePin', vetala_lib_parent, 'ExecuteContext', controller)
        graph.add_link(vetala_lib_parent, 'ExecuteContext', vetala_lib_parent1, 'ExecuteContext', controller)
        graph.add_link(vetala_lib_parent1, 'ExecuteContext', vetala_lib_parent3, 'ExecuteContext', controller)
        graph.add_link(spawn_transform_control, 'ExecutePin', add1, 'ExecuteContext', controller)
        graph.add_link(add1, 'ExecuteContext', set_item_array_metadata, 'ExecuteContext', controller)
        graph.add_link(set_item_array_metadata, 'ExecuteContext', spawn_transform_control1, 'ExecutePin', controller)
        graph.add_link(vetala_lib_parent4, 'ExecuteContext', spawn_bool_animation_channel, 'ExecutePin', controller)
        graph.add_link(spawn_bool_animation_channel, 'ExecutePin', branch1, 'ExecuteContext', controller)
        graph.add_link(branch, 'True', vetala_lib_parent2, 'ExecuteContext', controller)
        graph.add_link(vetala_lib_parent3, 'ExecuteContext', set_transform, 'ExecutePin', controller)
        graph.add_link('DISPATCH_RigVMDispatch_SwitchInt32', 'Cases.0', branch2, 'ExecuteContext', controller)
        graph.add_link(spawn_transform_control1, 'ExecutePin', vetala_lib_parent4, 'ExecuteContext', controller)
        graph.add_link(get_local_controls, 'Value', add, 'Array', controller)
        graph.add_link(get_local_controls, 'Value', at8, 'Array', controller)
        graph.add_link(get_local_controls, 'Value', vetala_lib_get_item2, 'Array', controller)
        graph.add_link(get_local_controls, 'Value', at14, 'Array', controller)
        graph.add_link(at5, 'Element', vetala_lib_find_pole_vector, 'BoneA', controller)
        graph.add_link(at6, 'Element', vetala_lib_find_pole_vector, 'BoneB', controller)
        graph.add_link(at7, 'Element', vetala_lib_find_pole_vector, 'BoneC', controller)
        graph.add_link(get_pole_vector_offset, 'Value', vetala_lib_find_pole_vector, 'output', controller)
        graph.add_link(vetala_lib_find_pole_vector, 'Transform.Translation', set_translation, 'Value', controller)
        graph.add_link(make_array, 'Array', for_each, 'Array', controller)
        graph.add_link(for_each, 'Element', set_item_metadata, 'Item', controller)
        graph.add_link(for_each, 'Element', vetala_lib_control, 'driven', controller)
        graph.add_link(for_each, 'Element', vetala_lib_get_joint_description, 'joint', controller)
        graph.add_link(for_each, 'Element', vetala_lib_get_parent, 'joint', controller)
        graph.add_link(for_each, 'Index', greater, 'A', controller)
        graph.add_link(for_each, 'Index', equals2, 'A', controller)
        graph.add_link(for_each, 'Index', equals3, 'A', controller)
        graph.add_link(for_each, 'Index', if6, 'False', controller)
        graph.add_link(if7, 'Result', vetala_lib_control, 'increment', controller)
        graph.add_link(vetala_lib_get_parent, 'Result', vetala_lib_control, 'parent', controller)
        graph.add_link(if1, 'Result', vetala_lib_control, 'description', controller)
        graph.add_link('Entry', 'side', vetala_lib_control, 'side', controller)
        graph.add_link('Entry', 'joint_token', vetala_lib_control, 'joint_token', controller)
        graph.add_link(if3, 'Result', vetala_lib_control, 'sub_count', controller)
        graph.add_link('Entry', 'restrain_numbering', vetala_lib_control, 'restrain_numbering', controller)
        graph.add_link(if8, 'Result', vetala_lib_control, 'shape', controller)
        graph.add_link('Entry', 'color', vetala_lib_control, 'color', controller)
        graph.add_link('Entry', 'sub_color', vetala_lib_control, 'sub_color', controller)
        graph.add_link('Entry', 'shape_translate', vetala_lib_control, 'translate', controller)
        graph.add_link('Entry', 'shape_rotate', vetala_lib_control, 'rotate', controller)
        graph.add_link('Entry', 'shape_scale', vetala_lib_control, 'scale', controller)
        graph.add_link(if9, 'Result', vetala_lib_control, 'scale_offset', controller)
        graph.add_link(get_world, 'Value', vetala_lib_control, 'world', controller)
        graph.add_link(get_mirror, 'Value', vetala_lib_control, 'mirror', controller)
        graph.add_link(vetala_lib_control, 'Last Control', set_item_metadata, 'Value', controller)
        graph.add_link(vetala_lib_control, 'Control', add, 'Element', controller)
        graph.add_link('Entry', 'parent', vetala_lib_get_parent, 'default_parent', controller)
        graph.add_link(equals, 'Result', vetala_lib_get_parent, 'is_top_joint', controller)
        graph.add_link(get_control_layer, 'Value', vetala_lib_get_parent, 'control_layer', controller)
        graph.add_link(if5, 'Result', vetala_lib_get_joint_description, 'description', controller)
        graph.add_link(get_joint_token, 'Value', vetala_lib_get_joint_description, 'joint_token', controller)
        graph.add_link(vetala_lib_get_joint_description, 'Result', if1, 'True', controller)
        graph.add_link(get_control_layer, 'Value', set_item_metadata, 'Name', controller)
        graph.add_link('Num_1', 'Num', equals, 'A', controller)
        graph.add_link(get_description, 'Value', if5, 'False', controller)
        graph.add_link(get_description, 'Value', concat, 'A', controller)
        graph.add_link(get_use_joint_name, 'Value', if1, 'Condition', controller)
        graph.add_link(if5, 'Result', if1, 'False', controller)
        graph.add_link(get_pole_vector_shape, 'Value', from_string, 'String', controller)
        graph.add_link(from_string, 'Result', shape_exists, 'ShapeName', controller)
        graph.add_link(from_string, 'Result', if2, 'True', controller)
        graph.add_link(shape_exists, 'Result', if2, 'Condition', controller)
        graph.add_link(branch, 'False', set_shape_settings, 'ExecutePin', controller)
        graph.add_link(at2, 'Element', set_shape_settings, 'Item', controller)
        graph.add_link(at1, 'Element', vetala_lib_parent, 'Parent', controller)
        graph.add_link(at2, 'Element', vetala_lib_parent, 'Child', controller)
        graph.add_link(at1, 'Element', vetala_lib_parent1, 'Parent', controller)
        graph.add_link(at13, 'Element', vetala_lib_parent1, 'Child', controller)
        graph.add_link(get_color, 'Value', at, 'Array', controller)
        graph.add_link(get_local_controls1, 'Value', at1, 'Array', controller)
        graph.add_link(at1, 'Element', vetala_lib_parent2, 'Parent', controller)
        graph.add_link(at1, 'Element', vetala_lib_parent3, 'Parent', controller)
        graph.add_link(get_local_controls1, 'Value', at2, 'Array', controller)
        graph.add_link(at2, 'Element', set_translation, 'Item', controller)
        graph.add_link(at2, 'Element', spawn_float_animation_channel1, 'Parent', controller)
        graph.add_link(at2, 'Element', vetala_lib_parent2, 'Child', controller)
        graph.add_link(get_local_controls1, 'Value', at3, 'Array', controller)
        graph.add_link(at3, 'Element', vetala_lib_parent3, 'Child', controller)
        graph.add_link(at3, 'Element', set_transform, 'Item', controller)
        graph.add_link(get_shape_scale, 'Value', at4, 'Array', controller)
        graph.add_link(at4, 'Element', multiply, 'A', controller)
        graph.add_link(get_joints, 'Value', at5, 'Array', controller)
        graph.add_link(get_joints, 'Value', at6, 'Array', controller)
        graph.add_link(get_joints, 'Value', at7, 'Array', controller)
        graph.add_link(set_translation, 'ExecutePin', spawn_float_animation_channel1, 'ExecutePin', controller)
        graph.add_link(greater, 'Result', if3, 'Condition', controller)
        graph.add_link('Entry', 'sub_count', if3, 'True', controller)
        graph.add_link(greater1, 'Result', if4, 'Condition', controller)
        graph.add_link(get_item_array_metadata, 'Value', if4, 'True', controller)
        graph.add_link(if4, 'Result', vetala_lib_get_item, 'Array', controller)
        graph.add_link(at8, 'Element', get_item_array_metadata, 'Item', controller)
        graph.add_link(get_item_array_metadata, 'Value', num, 'Array', controller)
        graph.add_link(vetala_lib_get_item, 'Element', spawn_transform_control, 'Parent', controller)
        graph.add_link(vetala_lib_get_item1, 'Element', get_transform, 'Item', controller)
        graph.add_link(get_transform, 'Transform', spawn_transform_control, 'InitialValue', controller)
        graph.add_link(get_local_ik, 'Value', add1, 'Array', controller)
        graph.add_link(add1, 'Array', set_item_array_metadata, 'Value', controller)
        graph.add_link(spawn_transform_control, 'Item', add1, 'Element', controller)
        graph.add_link(num, 'Num', 'Greater_1', 'A', controller)
        graph.add_link(num, 'Num', greater1, 'A', controller)
        graph.add_link(get_joints1, 'Value', vetala_lib_get_item1, 'Array', controller)
        graph.add_link(vetala_lib_get_item1, 'Element', set_item_array_metadata, 'Item', controller)
        graph.add_link(rig_element_key, 'Value', spawn_bool_animation_channel, 'Parent', controller)
        graph.add_link(branch1, 'False', spawn_float_animation_channel, 'ExecutePin', controller)
        graph.add_link(rig_element_key, 'Value', spawn_float_animation_channel, 'Parent', controller)
        graph.add_link(at8, 'Element', rig_element_key, 'Value', controller)
        graph.add_link(get_joints2, 'Value', num1, 'Array', controller)
        graph.add_link(num1, 'Num', equals, 'A', controller)
        graph.add_link(num1, 'Num', 'Equals_1', 'A', controller)
        graph.add_link(num1, 'Num', 'Equals_4', 'A', controller)
        graph.add_link('Num_1', 'Num', equals1, 'A', controller)
        graph.add_link(equals1, 'Result', or1, 'A', controller)
        graph.add_link(or1, 'Result', branch, 'Condition', controller)
        graph.add_link(branch, 'Completed', spawn_transform_control, 'ExecutePin', controller)
        graph.add_link(get_local_controls1, 'Value', at13, 'Array', controller)
        graph.add_link(or1, 'Result', branch1, 'Condition', controller)
        graph.add_link(get_joints2, 'Value', at9, 'Array', controller)
        graph.add_link(get_joints2, 'Value', at10, 'Array', controller)
        graph.add_link(get_joints2, 'Value', at11, 'Array', controller)
        graph.add_link(get_joints2, 'Value', at12, 'Array', controller)
        graph.add_link(at13, 'Element', get_transform1, 'Item', controller)
        graph.add_link(equals2, 'Result', if5, 'Condition', controller)
        graph.add_link(equals2, 'Result', if6, 'Condition', controller)
        graph.add_link(equals2, 'Result', if8, 'Condition', controller)
        graph.add_link(equals2, 'Result', if9, 'Condition', controller)
        graph.add_link(concat, 'Result', if5, 'True', controller)
        graph.add_link(if6, 'Result', if7, 'False', controller)
        graph.add_link(equals3, 'Result', if7, 'Condition', controller)
        graph.add_link(get_transform1, 'Transform', set_transform, 'Value', controller)
        graph.add_link(vetala_lib_get_item2, 'Element', get_transform2, 'Item', controller)
        graph.add_link(vetala_lib_get_item2, 'Element', vetala_lib_parent4, 'Child', controller)
        graph.add_link('Num_1', 'Num', equals4, 'A', controller)
        graph.add_link(equals4, 'Result', branch2, 'Condition', controller)
        graph.add_link(get_transform2, 'Transform', spawn_transform_control1, 'InitialValue', controller)
        graph.add_link(at14, 'Element', spawn_transform_control1, 'Parent', controller)
        graph.add_link(spawn_transform_control1, 'Item', vetala_lib_parent4, 'Parent', controller)
        graph.add_link(if2, 'Result', set_shape_settings, 'Settings.Name', controller)
        graph.add_link(at, 'Element', set_shape_settings, 'Settings.Color', controller)
        graph.add_link(at8, 'Element', if4, 'False.0', controller)
        graph.add_link(at9, 'Element', make_array, 'Values.0', controller)
        graph.add_link(at11, 'Element', make_array, 'Values.1', controller)
        graph.add_link(at10, 'Element', make_array, 'Values.2', controller)
        graph.add_link(at12, 'Element', make_array, 'Values.3', controller)
        graph.add_link(multiply, 'Result', set_shape_settings, 'Settings.Transform.Scale3D', controller)

        graph.set_pin(vetala_lib_get_parent, 'in_hierarchy', 'False', controller)
        graph.set_pin(set_item_metadata, 'NameSpace', 'Self', controller)
        graph.set_pin(equals, 'B', '0', controller)
        graph.set_pin(if2, 'False', 'Sphere_Solid', controller)
        graph.set_pin(set_shape_settings, 'Settings', '(bVisible=True,Name="Default",Color=(R=1.000000,G=0.000000,B=0.000000,A=1.000000),Transform=(Rotation=(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=1.000000,Y=1.000000,Z=1.000000)))', controller)
        graph.set_pin(at, 'Index', '0', controller)
        graph.set_pin(at1, 'Index', '0', controller)
        graph.set_pin(at2, 'Index', '1', controller)
        graph.set_pin(at3, 'Index', '2', controller)
        graph.set_pin(at4, 'Index', '0', controller)
        graph.set_pin(multiply, 'B', '(X=0.333,Y=0.333,Z=0.333)', controller)
        graph.set_pin(at5, 'Index', '0', controller)
        graph.set_pin(at6, 'Index', '1', controller)
        graph.set_pin(at7, 'Index', '2', controller)
        graph.set_pin(set_translation, 'Space', 'GlobalSpace', controller)
        graph.set_pin(set_translation, 'bInitial', 'true', controller)
        graph.set_pin(set_translation, 'Weight', '1.000000', controller)
        graph.set_pin(set_translation, 'bPropagateToChildren', 'True', controller)
        graph.set_pin(greater, 'B', '1', controller)
        graph.set_pin(if3, 'False', '0', controller)
        graph.set_pin(if4, 'False', '((Type=None,Name="None"))', controller)
        graph.set_pin(get_item_array_metadata, 'Name', 'Sub', controller)
        graph.set_pin(get_item_array_metadata, 'NameSpace', 'Self', controller)
        graph.set_pin(vetala_lib_get_item, 'index', '-1', controller)
        graph.set_pin(get_transform, 'Space', 'GlobalSpace', controller)
        graph.set_pin(get_transform, 'bInitial', 'False', controller)
        graph.set_pin(greater1, 'B', '0', controller)
        graph.set_pin(vetala_lib_get_item1, 'index', '3', controller)
        graph.set_pin(set_item_array_metadata, 'Name', 'ik', controller)
        graph.set_pin(set_item_array_metadata, 'NameSpace', 'Self', controller)
        graph.set_pin(spawn_bool_animation_channel, 'Name', 'stretch', controller)
        graph.set_pin(spawn_bool_animation_channel, 'InitialValue', 'False', controller)
        graph.set_pin(spawn_bool_animation_channel, 'MinimumValue', 'False', controller)
        graph.set_pin(spawn_bool_animation_channel, 'MaximumValue', 'True', controller)
        graph.set_pin(spawn_float_animation_channel, 'Name', 'nudge', controller)
        graph.set_pin(spawn_float_animation_channel, 'InitialValue', '0.000000', controller)
        graph.set_pin(spawn_float_animation_channel, 'MinimumValue', '-500.000000', controller)
        graph.set_pin(spawn_float_animation_channel, 'MaximumValue', '500.000000', controller)
        graph.set_pin(spawn_float_animation_channel, 'LimitsEnabled', '(Enabled=(bMinimum=True,bMaximum=True))', controller)
        graph.set_pin(spawn_float_animation_channel1, 'Name', 'lock', controller)
        graph.set_pin(spawn_float_animation_channel1, 'InitialValue', '0.000000', controller)
        graph.set_pin(spawn_float_animation_channel1, 'MinimumValue', '0.000000', controller)
        graph.set_pin(spawn_float_animation_channel1, 'MaximumValue', '1.000000', controller)
        graph.set_pin(spawn_float_animation_channel1, 'LimitsEnabled', '(Enabled=(bMinimum=True,bMaximum=True))', controller)
        graph.set_pin(equals1, 'B', '2', controller)
        graph.set_pin(at8, 'Index', '3', controller)
        graph.set_pin(make_array, 'Values', '((Type=None,Name="None"),((),Type=None,Name="None"),((),Type=None,Name="None"),((),Type=None,Name="None"))', controller)
        graph.set_pin(at9, 'Index', '0', controller)
        graph.set_pin(at10, 'Index', '2', controller)
        graph.set_pin(or1, 'B', 'False', controller)
        graph.set_pin(at11, 'Index', '1', controller)
        graph.set_pin(at12, 'Index', '3', controller)
        graph.set_pin(at13, 'Index', '3', controller)
        graph.set_pin(equals2, 'B', '2', controller)
        graph.set_pin(concat, 'B', '_ankle', controller)
        graph.set_pin(if6, 'True', '0', controller)
        graph.set_pin(equals3, 'B', '3', controller)
        graph.set_pin(if7, 'True', '2', controller)
        graph.set_pin(set_transform, 'Space', 'GlobalSpace', controller)
        graph.set_pin(set_transform, 'bInitial', 'true', controller)
        graph.set_pin(set_transform, 'Weight', '1.000000', controller)
        graph.set_pin(set_transform, 'bPropagateToChildren', 'True', controller)
        graph.set_pin(get_transform1, 'Space', 'GlobalSpace', controller)
        graph.set_pin(get_transform1, 'bInitial', 'False', controller)
        graph.set_pin(if8, 'True', 'Square_Solid', controller)
        graph.set_pin(if9, 'True', '0.650000', controller)
        graph.set_pin(if9, 'False', '1.000000', controller)
        graph.set_pin(vetala_lib_get_item2, 'index', '2', controller)
        graph.set_pin(equals4, 'B', '4', controller)
        graph.set_pin(get_transform2, 'Space', 'GlobalSpace', controller)
        graph.set_pin(get_transform2, 'bInitial', 'False', controller)
        graph.set_pin(at14, 'Index', '0', controller)
        graph.set_pin(spawn_transform_control, 'Name', 'ik', controller)
        graph.set_pin(spawn_transform_control, 'OffsetTransform', '(Rotation=(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=1.000000,Y=1.000000,Z=1.000000))', controller)
        graph.set_pin(spawn_transform_control, 'OffsetSpace', 'GlobalSpace', controller)
        graph.set_pin(spawn_transform_control, 'Settings', '(InitialSpace=LocalSpace,bUsePreferredRotationOrder=False,PreferredRotationOrder=YZX,Limits=(LimitTranslationX=(bMinimum=False,bMaximum=False),LimitTranslationY=(bMinimum=False,bMaximum=False),LimitTranslationZ=(bMinimum=False,bMaximum=False),LimitPitch=(bMinimum=False,bMaximum=False),LimitYaw=(bMinimum=False,bMaximum=False),LimitRoll=(bMinimum=False,bMaximum=False),LimitScaleX=(bMinimum=False,bMaximum=False),LimitScaleY=(bMinimum=False,bMaximum=False),LimitScaleZ=(bMinimum=False,bMaximum=False),MinValue=(Location=(X=-100.000000,Y=-100.000000,Z=-100.000000),Rotation=(Pitch=-180.000000,Yaw=-180.000000,Roll=-180.000000),Scale=(X=0.000000,Y=0.000000,Z=0.000000)),MaxValue=(Location=(X=100.000000,Y=100.000000,Z=100.000000),Rotation=(Pitch=180.000000,Yaw=180.000000,Roll=180.000000),Scale=(X=10.000000,Y=10.000000,Z=10.000000)),bDrawLimits=True),Shape=(bVisible=false,Name="Default",Color=(R=1.000000,G=0.000000,B=0.000000,A=1.000000),Transform=(Rotation=(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=0.050000,Y=0.050000,Z=0.050000))),Proxy=(bIsProxy=true,ShapeVisibility=BasedOnSelection),FilteredChannels=(),DisplayName="None")', controller)
        graph.set_pin(spawn_transform_control1, 'Name', 'quad_ik_offset', controller)
        graph.set_pin(spawn_transform_control1, 'OffsetTransform', '(Rotation=(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=1.000000,Y=1.000000,Z=1.000000))', controller)
        graph.set_pin(spawn_transform_control1, 'OffsetSpace', 'LocalSpace', controller)
        graph.set_pin(spawn_transform_control1, 'Settings', '(InitialSpace=LocalSpace,bUsePreferredRotationOrder=False,PreferredRotationOrder=YZX,Limits=(LimitTranslationX=(bMinimum=False,bMaximum=False),LimitTranslationY=(bMinimum=False,bMaximum=False),LimitTranslationZ=(bMinimum=False,bMaximum=False),LimitPitch=(bMinimum=False,bMaximum=False),LimitYaw=(bMinimum=False,bMaximum=False),LimitRoll=(bMinimum=False,bMaximum=False),LimitScaleX=(bMinimum=False,bMaximum=False),LimitScaleY=(bMinimum=False,bMaximum=False),LimitScaleZ=(bMinimum=False,bMaximum=False),MinValue=(Location=(X=-100.000000,Y=-100.000000,Z=-100.000000),Rotation=(Pitch=-180.000000,Yaw=-180.000000,Roll=-180.000000),Scale=(X=0.000000,Y=0.000000,Z=0.000000)),MaxValue=(Location=(X=100.000000,Y=100.000000,Z=100.000000),Rotation=(Pitch=180.000000,Yaw=180.000000,Roll=180.000000),Scale=(X=10.000000,Y=10.000000,Z=10.000000)),bDrawLimits=True),Shape=(bVisible=false,Name="Default",Color=(R=1.000000,G=0.000000,B=0.000000,A=1.000000),Transform=(Rotation=(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=1.000000,Y=1.000000,Z=1.000000))),Proxy=(bIsProxy=true,ShapeVisibility=BasedOnSelection),FilteredChannels=(),DisplayName="None")', controller)

        current_locals = locals()
        nodes = unreal_lib.graph.filter_nodes(current_locals.values())

        return nodes

    def _build_function_construct_graph(self):
        controller = self.function_controller
        library = graph.get_local_function_library()

        controller.add_local_variable_from_object_path('local_controls', 'TArray<FRigElementKey>',
                                                                     '/Script/ControlRig.RigElementKey', '')

        controller.add_local_variable_from_object_path('local_ik', 'TArray<FRigElementKey>',
                                                                     '/Script/ControlRig.RigElementKey', '')

        nodes = self._build_controls(controller, library)

        nodes = list(set(nodes))

        node = unreal_lib.graph.comment_nodes(nodes, controller, 'Construction')
        nodes.append(node)
        unreal_lib.graph.move_nodes(500, -3000, nodes, controller)

    def _build_function_forward_graph(self):

        controller = self.function_controller
        library = graph.get_local_function_library()

        at = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(3648.0, 720.0), 'At')
        at1 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(616.0, 1288.0), 'At')
        at2 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(640.0, 1542.0), 'At')
        at3 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(552.0, 1736.0), 'At')
        get_item_metadata = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(936.0, 1432.0), 'Get Item Metadata')
        get_control_layer = controller.add_variable_node('control_layer', 'FName', None, True, '', unreal.Vector2D(584.0, 1456.0), 'Get control_layer')
        basic_ik = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_TwoBoneIKSimplePerItem', 'Execute', unreal.Vector2D(5040.0, 1824.0), 'Basic IK')
        get_transform = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetTransform', 'Execute', unreal.Vector2D(1712.0, 1392.0), 'Get Transform')
        vetala_lib_find_bone_aim_axis = controller.add_function_reference_node(library.find_function('vetalaLib_findBoneAimAxis'), unreal.Vector2D(2216.0, 792.0), 'vetalaLib_findBoneAimAxis')
        draw_line = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_DebugLineNoSpace', 'Execute', unreal.Vector2D(5536.0, 1984.0), 'Draw Line')
        get_transform1 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetTransform', 'Execute', unreal.Vector2D(1320.0, 1528.0), 'Get Transform')
        project_to_new_parent = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_ProjectTransformToNewParent', 'Execute', unreal.Vector2D(3296.0, 2032.0), 'Project to new Parent')
        vetala_lib_get_item = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(2528.0, 1680.0), 'vetalaLib_GetItem')
        get_item_array_metadata = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(1680.0, 1840.0), 'Get Item Array Metadata')
        vetala_lib_ik_nudge_lock = controller.add_function_reference_node(library.find_function('vetalaLib_IK_NudgeLock'), unreal.Vector2D(2944.0, 928.0), 'vetalaLib_IK_NudgeLock')
        get_item_metadata1 = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(640.0, 864.0), 'Get Item Metadata')
        get_bool_channel = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetBoolAnimationChannel', 'Execute', unreal.Vector2D(1520.0, 2048.0), 'Get Bool Channel')
        get_item_metadata2 = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(520.0, 1992.0), 'Get Item Metadata')
        item = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_Item', 'Execute', unreal.Vector2D(1148.0, 2136.0), 'Item')
        get_float_channel = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetFloatAnimationChannel', 'Execute', unreal.Vector2D(1520.0, 2208.0), 'Get Float Channel')
        item1 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_Item', 'Execute', unreal.Vector2D(1136.0, 2272.0), 'Item')
        item2 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_Item', 'Execute', unreal.Vector2D(1664.0, 1216.0), 'Item')
        get_float_channel1 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetFloatAnimationChannel', 'Execute', unreal.Vector2D(2080.0, 1232.0), 'Get Float Channel')
        get_item_metadata3 = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(512.0, 2208.0), 'Get Item Metadata')
        if1 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(912.0, 2299.0), 'If')
        vetala_lib_constrain_transform = controller.add_function_reference_node(library.find_function('vetalaLib_ConstrainTransform'), unreal.Vector2D(1208.0, 776.0), 'vetalaLib_ConstrainTransform')
        at4 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(304.0, 1808.0), 'At')
        get_metadata = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(888.0, 1912.0), 'Get Metadata')
        get_joints = controller.add_variable_node_from_object_path('joints', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(3264.0, 832.0), 'Get joints')
        get_transform2 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetTransform', 'Execute', unreal.Vector2D(3336.0, 1400.0), 'Get Transform')
        at5 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(3648.0, 832.0), 'At')
        at6 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(3648.0, 944.0), 'At')
        at7 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(3648.0, 1056.0), 'At')
        ccdik = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_CCDIKItemArray', 'Execute', unreal.Vector2D(4176.0, 1424.0), 'CCDIK')
        set_local_ik = controller.add_variable_node_from_object_path('local_ik', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', False, '()', unreal.Vector2D(5984.0, 1920.0), 'Set local_ik')
        set_transform = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_SetTransform', 'Execute', unreal.Vector2D(4760.0, 1432.0), 'Set Transform')
        get_item_array_metadata1 = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(4928.0, 752.0), 'Get Item Array Metadata')
        get_layer = controller.add_variable_node('layer', 'int32', None, True, '', unreal.Vector2D(4096.0, 832.0), 'Get layer')
        to_string = controller.add_template_node('DISPATCH_RigDispatch_ToString(in Value,out Result)', unreal.Vector2D(4272.0, 832.0), 'To String')
        vetala_lib_get_item1 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(5312.0, 720.0), 'vetalaLib_GetItem')
        join = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_StringJoin', 'Execute', unreal.Vector2D(4544.0, 704.0), 'Join')
        concat = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_NameConcat', 'Execute', unreal.Vector2D(4720.0, 816.0), 'Concat')
        from_string = controller.add_template_node('DISPATCH_RigDispatch_FromString(in String,out Result)', unreal.Vector2D(4448.0, 864.0), 'From String')
        get_parent = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyGetParent', 'Execute', unreal.Vector2D(5536.0, 720.0), 'Get Parent')
        project_to_new_parent1 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_ProjectTransformToNewParent', 'Execute', unreal.Vector2D(4488.0, 1048.0), 'Project to new Parent')
        get_local_ik = controller.add_variable_node_from_object_path('local_ik', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(3720.0, 600.0), 'Get local_ik')
        ccdik1 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_CCDIKItemArray', 'Execute', unreal.Vector2D(5576.0, 1448.0), 'CCDIK')
        project_to_new_parent2 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_ProjectTransformToNewParent', 'Execute', unreal.Vector2D(5224.0, 1000.0), 'Project to new Parent')
        set_rotation = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_SetRotation', 'Execute', unreal.Vector2D(6344.0, 1272.0), 'Set Rotation')
        project_to_new_parent3 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_ProjectTransformToNewParent', 'Execute', unreal.Vector2D(5928.0, 1288.0), 'Project to new Parent')

        controller.resolve_wild_card_pin(f'{at.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{at1.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{at2.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{at3.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{if1.get_node_path()}.Result', 'FRigElementKey', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{at4.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{at5.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{at6.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{at7.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{concat.get_node_path()}.Result', 'FName', 'None')

        controller.set_array_pin_size(f'{n(vetala_lib_ik_nudge_lock)}.joints', 3)
        controller.set_array_pin_size(f'{n(vetala_lib_ik_nudge_lock)}.controls', 3)
        controller.set_array_pin_size(f'{n(join)}.Values', 2)
        controller.set_array_pin_size(f'{n(ccdik1)}.Items', 2)

        graph.add_link(vetala_lib_constrain_transform, 'ExecuteContext', vetala_lib_find_bone_aim_axis, 'ExecuteContext', controller)
        graph.add_link(vetala_lib_find_bone_aim_axis, 'ExecuteContext', vetala_lib_ik_nudge_lock, 'ExecuteContext', controller)
        graph.add_link(draw_line, 'ExecutePin', set_local_ik, 'ExecuteContext', controller)
        graph.add_link(vetala_lib_ik_nudge_lock, 'ExecuteContext', ccdik, 'ExecutePin', controller)
        graph.add_link('DISPATCH_RigVMDispatch_SwitchInt32', 'Cases.1', vetala_lib_constrain_transform, 'ExecuteContext', controller)
        graph.add_link(get_joints, 'Value', at, 'Array', controller)
        graph.add_link(at, 'Element', 'Get Item Array Metadata_2', 'Item', controller)
        graph.add_link('Entry', 'joints', at1, 'Array', controller)
        graph.add_link(at1, 'Element', basic_ik, 'ItemA', controller)
        graph.add_link(at1, 'Element', vetala_lib_find_bone_aim_axis, 'Bone', controller)
        graph.add_link(at1, 'Element', get_item_metadata1, 'Item', controller)
        graph.add_link(at1, 'Element', vetala_lib_constrain_transform, 'TargetTransform', controller)
        graph.add_link('Entry', 'joints', at2, 'Array', controller)
        graph.add_link(at2, 'Element', basic_ik, 'ItemB', controller)
        graph.add_link(at2, 'Element', get_item_metadata, 'Item', controller)
        graph.add_link(at2, 'Element', get_transform1, 'Item', controller)
        graph.add_link('Entry', 'joints', at3, 'Array', controller)
        graph.add_link(at3, 'Element', basic_ik, 'EffectorItem', controller)
        graph.add_link(at3, 'Element', 'Get Metadata', 'Item', controller)
        graph.add_link(get_control_layer, 'Value', get_item_metadata, 'Name', controller)
        graph.add_link(get_item_metadata, 'Value', get_transform, 'Item', controller)
        graph.add_link(get_item_metadata, 'Value', 'Item_2', 'Item', controller)
        graph.add_link(get_control_layer, 'Value', get_item_metadata1, 'Name', controller)
        graph.add_link(get_control_layer, 'Value', get_item_metadata2, 'Name', controller)
        graph.add_link(get_control_layer, 'Value', get_metadata, 'Name', controller)
        graph.add_link(set_transform, 'ExecutePin', basic_ik, 'ExecutePin', controller)
        graph.add_link(basic_ik, 'ExecutePin', ccdik1, 'ExecutePin', controller)
        graph.add_link(project_to_new_parent, 'Transform', basic_ik, 'Effector', controller)
        graph.add_link(vetala_lib_find_bone_aim_axis, 'Result', basic_ik, 'PrimaryAxis', controller)
        graph.add_link(get_transform, 'Transform.Translation', basic_ik, 'PoleVector', controller)
        graph.add_link(get_bool_channel, 'Value', basic_ik, 'bEnableStretch', controller)
        graph.add_link(vetala_lib_ik_nudge_lock, 'scale1', basic_ik, 'ItemALength', controller)
        graph.add_link(vetala_lib_ik_nudge_lock, 'scale2', basic_ik, 'ItemBLength', controller)
        graph.add_link(get_transform, 'Transform.Translation', draw_line, 'B', controller)
        graph.add_link(set_rotation, 'ExecutePin', draw_line, 'ExecutePin', controller)
        graph.add_link(get_transform1, 'Transform.Translation', draw_line, 'A', controller)
        graph.add_link(at6, 'Element', project_to_new_parent, 'Child', controller)
        graph.add_link(vetala_lib_get_item1, 'Element', project_to_new_parent, 'OldParent', controller)
        graph.add_link(vetala_lib_get_item1, 'Element', project_to_new_parent, 'NewParent', controller)
        graph.add_link(get_item_array_metadata, 'Value', vetala_lib_get_item, 'Array', controller)
        graph.add_link(vetala_lib_get_item, 'Element', 'Get Transform_5', 'Item', controller)
        graph.add_link(vetala_lib_get_item, 'Element', project_to_new_parent3, 'OldParent', controller)
        graph.add_link(vetala_lib_get_item, 'Element', project_to_new_parent3, 'NewParent', controller)
        graph.add_link('At_19', 'Element', get_item_array_metadata, 'Item', controller)
        graph.add_link(get_item_array_metadata, 'Value', set_local_ik, 'Value', controller)
        graph.add_link(get_float_channel, 'Value', vetala_lib_ik_nudge_lock, 'nudge', controller)
        graph.add_link(get_float_channel1, 'Value', vetala_lib_ik_nudge_lock, 'lock', controller)
        graph.add_link(get_item_metadata1, 'Value', vetala_lib_constrain_transform, 'SourceTransform', controller)
        graph.add_link(item, 'Item.Name', get_bool_channel, 'Control', controller)
        graph.add_link('At_19', 'Element', get_item_metadata2, 'Item', controller)
        graph.add_link(get_item_metadata2, 'Value', if1, 'False', controller)
        graph.add_link('If_9', 'Result', item, 'Item', controller)
        graph.add_link(item1, 'Item.Name', get_float_channel, 'Control', controller)
        graph.add_link('If_9', 'Result', item1, 'Item', controller)
        graph.add_link(get_item_metadata, 'Value', item2, 'Item', controller)
        graph.add_link(item2, 'Item.Name', get_float_channel1, 'Control', controller)
        graph.add_link('At_19', 'Element', get_item_metadata3, 'Item', controller)
        graph.add_link(get_item_metadata3, 'Value', if1, 'True', controller)
        graph.add_link(get_item_metadata3, 'Found', if1, 'Condition', controller)
        graph.add_link(if1, 'Result', item, 'Item', controller)
        graph.add_link(if1, 'Result', 'Item_1', 'Item', controller)
        graph.add_link('Entry', 'joints', at4, 'Array', controller)
        graph.add_link(at4, 'Element', get_item_metadata2, 'Item', controller)
        graph.add_link(at4, 'Element', 'Get Item Metadata_3', 'Item', controller)
        graph.add_link(at4, 'Element', get_item_array_metadata, 'Item', controller)
        graph.add_link(at3, 'Element', get_metadata, 'Item', controller)
        graph.add_link(get_joints, 'Value', at5, 'Array', controller)
        graph.add_link(get_joints, 'Value', at6, 'Array', controller)
        graph.add_link(get_joints, 'Value', at7, 'Array', controller)
        graph.add_link(get_joints, 'Value', ccdik, 'Items', controller)
        graph.add_link(vetala_lib_get_item, 'Element', get_transform2, 'Item', controller)
        graph.add_link(get_transform2, 'Transform', ccdik, 'EffectorTransform', controller)
        graph.add_link(at6, 'Element', project_to_new_parent1, 'NewParent', controller)
        graph.add_link(at6, 'Element', project_to_new_parent1, 'OldParent', controller)
        graph.add_link(at7, 'Element', project_to_new_parent2, 'Child', controller)
        graph.add_link(at7, 'Element', project_to_new_parent3, 'Child', controller)
        graph.add_link(at7, 'Element', 'Set Transform_2', 'Item', controller)
        graph.add_link(ccdik, 'ExecutePin', set_transform, 'ExecutePin', controller)
        graph.add_link('Get Parent', 'Parent', set_transform, 'Item', controller)
        graph.add_link(project_to_new_parent1, 'Transform', set_transform, 'Value', controller)
        graph.add_link(at, 'Element', get_item_array_metadata1, 'Item', controller)
        graph.add_link(concat, 'Result', get_item_array_metadata1, 'Name', controller)
        graph.add_link(get_item_array_metadata1, 'Value', vetala_lib_get_item1, 'Array', controller)
        graph.add_link(get_layer, 'Value', to_string, 'Value', controller)
        graph.add_link(to_string, 'Result', from_string, 'String', controller)
        graph.add_link(vetala_lib_get_item1, 'Element', get_parent, 'Child', controller)
        graph.add_link(from_string, 'Result', concat, 'B', controller)
        graph.add_link(get_parent, 'Parent', 'Set Transform_1', 'Item', controller)
        graph.add_link(get_parent, 'Parent', project_to_new_parent1, 'Child', controller)
        graph.add_link(get_parent, 'Parent', project_to_new_parent2, 'OldParent', controller)
        graph.add_link(get_parent, 'Parent', project_to_new_parent2, 'NewParent', controller)
        graph.add_link(get_local_ik, 'Value', 'Return', 'ik', controller)
        graph.add_link(ccdik1, 'ExecutePin', set_rotation, 'ExecutePin', controller)
        graph.add_link(project_to_new_parent2, 'Transform', ccdik1, 'EffectorTransform', controller)
        graph.add_link('At_22', 'Element', set_rotation, 'Item', controller)
        graph.add_link(project_to_new_parent3, 'Transform.Rotation', set_rotation, 'Value', controller)
        graph.add_link(at1, 'Element', vetala_lib_ik_nudge_lock, 'joints.0', controller)
        graph.add_link(at2, 'Element', vetala_lib_ik_nudge_lock, 'joints.1', controller)
        graph.add_link(at3, 'Element', vetala_lib_ik_nudge_lock, 'joints.2', controller)
        graph.add_link(get_item_metadata, 'Value', vetala_lib_ik_nudge_lock, 'controls.1', controller)
        graph.add_link(vetala_lib_get_item, 'Element', vetala_lib_ik_nudge_lock, 'controls.2', controller)
        graph.add_link(get_item_metadata1, 'Value', vetala_lib_ik_nudge_lock, 'controls.0', controller)
        graph.add_link(at6, 'Element', ccdik1, 'Items.0', controller)
        graph.add_link(at7, 'Element', ccdik1, 'Items.1', controller)
        graph.add_link(to_string, 'Result', join, 'Values.1', controller)

        graph.set_pin(at, 'Index', '0', controller)
        graph.set_pin(at1, 'Index', '0', controller)
        graph.set_pin(at2, 'Index', '1', controller)
        graph.set_pin(at3, 'Index', '2', controller)
        graph.set_pin(get_item_metadata, 'NameSpace', 'Self', controller)
        graph.set_pin(get_item_metadata, 'Default', '(Type=Bone,Name="None")', controller)
        graph.set_pin(basic_ik, 'SecondaryAxis', '(X=0.000000,Y=0.000000,Z=0.000000)', controller)
        graph.set_pin(basic_ik, 'SecondaryAxisWeight', '1.000000', controller)
        graph.set_pin(basic_ik, 'PoleVectorKind', 'Direction', controller)
        graph.set_pin(basic_ik, 'PoleVectorSpace', '(Type=Bone,Name="None")', controller)
        graph.set_pin(basic_ik, 'StretchStartRatio', '1.000000', controller)
        graph.set_pin(basic_ik, 'StretchMaximumRatio', '10.000000', controller)
        graph.set_pin(basic_ik, 'Weight', '1.000000', controller)
        graph.set_pin(basic_ik, 'bPropagateToChildren', 'true', controller)
        graph.set_pin(basic_ik, 'DebugSettings', '(bEnabled=False,Scale=10.000000,WorldOffset=(Rotation=(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=1.000000,Y=1.000000,Z=1.000000)))', controller)
        graph.set_pin(get_transform, 'Space', 'GlobalSpace', controller)
        graph.set_pin(get_transform, 'bInitial', 'False', controller)
        graph.set_pin(draw_line, 'DebugDrawSettings', '(DepthPriority=SDPG_Foreground,Lifetime=-1.000000)', controller)
        graph.set_pin(draw_line, 'Color', '(R=0.05,G=0.05,B=0.05,A=1.000000)', controller)
        graph.set_pin(draw_line, 'Thickness', '0.000000', controller)
        graph.set_pin(draw_line, 'WorldOffset', '(Rotation=(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=1.000000,Y=1.000000,Z=1.000000))', controller)
        graph.set_pin(draw_line, 'bEnabled', 'True', controller)
        graph.set_pin(get_transform1, 'Space', 'GlobalSpace', controller)
        graph.set_pin(get_transform1, 'bInitial', 'False', controller)
        graph.set_pin(project_to_new_parent, 'bChildInitial', 'True', controller)
        graph.set_pin(project_to_new_parent, 'bOldParentInitial', 'True', controller)
        graph.set_pin(project_to_new_parent, 'bNewParentInitial', 'False', controller)
        graph.set_pin(vetala_lib_get_item, 'index', '-1', controller)
        graph.set_pin(get_item_array_metadata, 'Name', 'ik', controller)
        graph.set_pin(get_item_array_metadata, 'NameSpace', 'Self', controller)
        graph.set_pin(vetala_lib_ik_nudge_lock, 'joints', '((Type=None,Name="None"),(Type=None,Name="None"),(Type=None,Name="None"))', controller)
        graph.set_pin(vetala_lib_ik_nudge_lock, 'controls', '((Type=None,Name="None"),(Type=None,Name="None"),(Type=None,Name="None"))', controller)
        graph.set_pin(get_item_metadata1, 'NameSpace', 'Self', controller)
        graph.set_pin(get_item_metadata1, 'Default', '(Type=Bone,Name="None")', controller)
        graph.set_pin(get_bool_channel, 'Channel', 'stretch', controller)
        graph.set_pin(get_bool_channel, 'bInitial', 'False', controller)
        graph.set_pin(get_item_metadata2, 'NameSpace', 'Self', controller)
        graph.set_pin(get_item_metadata2, 'Default', '(Type=Bone,Name="None")', controller)
        graph.set_pin(get_float_channel, 'Channel', 'nudge', controller)
        graph.set_pin(get_float_channel, 'bInitial', 'False', controller)
        graph.set_pin(get_float_channel1, 'Channel', 'lock', controller)
        graph.set_pin(get_float_channel1, 'bInitial', 'False', controller)
        graph.set_pin(get_item_metadata3, 'Name', 'main', controller)
        graph.set_pin(get_item_metadata3, 'NameSpace', 'Self', controller)
        graph.set_pin(get_item_metadata3, 'Default', '(Type=Bone,Name="None")', controller)
        graph.set_pin(at4, 'Index', '-1', controller)
        graph.set_pin(get_metadata, 'NameSpace', 'Self', controller)
        graph.set_pin(get_transform2, 'Space', 'GlobalSpace', controller)
        graph.set_pin(get_transform2, 'bInitial', 'False', controller)
        graph.set_pin(at5, 'Index', '1', controller)
        graph.set_pin(at6, 'Index', '2', controller)
        graph.set_pin(at7, 'Index', '3', controller)
        graph.set_pin(ccdik, 'Precision', '0.000100', controller)
        graph.set_pin(ccdik, 'Weight', '1.000000', controller)
        graph.set_pin(ccdik, 'MaxIterations', '1000', controller)
        graph.set_pin(ccdik, 'bStartFromTail', 'false', controller)
        graph.set_pin(ccdik, 'BaseRotationLimit', '30.000000', controller)
        graph.set_pin(ccdik, 'bPropagateToChildren', 'true', controller)
        graph.set_pin(ccdik, 'WorkData', '(CachedEffector=(Key=(Type=None,Name="None"),Index=65535,ContainerVersion=-1))', controller)
        graph.set_pin(set_transform, 'Space', 'GlobalSpace', controller)
        graph.set_pin(set_transform, 'bInitial', 'False', controller)
        graph.set_pin(set_transform, 'Weight', '1.000000', controller)
        graph.set_pin(set_transform, 'bPropagateToChildren', 'true', controller)
        graph.set_pin(get_item_array_metadata1, 'NameSpace', 'Self', controller)
        graph.set_pin(vetala_lib_get_item1, 'index', '2', controller)
        graph.set_pin(join, 'Values', '("Controls","")', controller)
        graph.set_pin(join, 'Separator', '_', controller)
        graph.set_pin(concat, 'A', 'Controls_', controller)
        graph.set_pin(get_parent, 'bDefaultParent', 'True', controller)
        graph.set_pin(project_to_new_parent1, 'bChildInitial', 'True', controller)
        graph.set_pin(project_to_new_parent1, 'bOldParentInitial', 'True', controller)
        graph.set_pin(project_to_new_parent1, 'bNewParentInitial', 'False', controller)
        graph.set_pin(ccdik1, 'Items', '((Type=None,Name="None"),(Type=None,Name="None"))', controller)
        graph.set_pin(ccdik1, 'Precision', '1.000000', controller)
        graph.set_pin(ccdik1, 'Weight', '1.000000', controller)
        graph.set_pin(ccdik1, 'MaxIterations', '10', controller)
        graph.set_pin(ccdik1, 'bStartFromTail', 'false', controller)
        graph.set_pin(ccdik1, 'BaseRotationLimit', '30.000000', controller)
        graph.set_pin(ccdik1, 'bPropagateToChildren', 'true', controller)
        graph.set_pin(ccdik1, 'WorkData', '(CachedEffector=(Key=(Type=None,Name="None"),Index=65535,ContainerVersion=-1))', controller)
        graph.set_pin(project_to_new_parent2, 'bChildInitial', 'True', controller)
        graph.set_pin(project_to_new_parent2, 'bOldParentInitial', 'True', controller)
        graph.set_pin(project_to_new_parent2, 'bNewParentInitial', 'False', controller)
        graph.set_pin(set_rotation, 'Space', 'GlobalSpace', controller)
        graph.set_pin(set_rotation, 'bInitial', 'False', controller)
        graph.set_pin(set_rotation, 'Weight', '1.000000', controller)
        graph.set_pin(set_rotation, 'bPropagateToChildren', 'True', controller)
        graph.set_pin(project_to_new_parent3, 'bChildInitial', 'True', controller)
        graph.set_pin(project_to_new_parent3, 'bOldParentInitial', 'True', controller)
        graph.set_pin(project_to_new_parent3, 'bNewParentInitial', 'False', controller)

        current_locals = locals()
        nodes = unreal_lib.graph.filter_nodes(current_locals.values())
        node = unreal_lib.graph.comment_nodes(nodes, controller, 'Forward Solve')

        nodes.append(node)
        unreal_lib.graph.move_nodes(0, 0, nodes, controller)
        unreal_lib.graph.move_nodes(500, 500, nodes, controller)

    def _build_function_backward_graph(self):
        return


class UnrealWheelRig(UnrealUtilRig):

    def _build_function_construct_graph(self):
        controller = self.function_controller

        control = self._create_control(controller, 2500, -1300)

        control_spin = self._create_control(controller)

        controller.set_node_position(control_spin, unreal.Vector2D(2900, -800.000000))

        joints = controller.add_variable_node_from_object_path('joints', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(2000, -800), 'VariableNode')

        get_joint_num = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetNum(in Array,out Num)', unreal.Vector2D(1700, -1300), 'DISPATCH_RigVMDispatch_ArrayGetNum')
        joint_num_equals = controller.add_template_node('DISPATCH_RigVMDispatch_CoreEquals(in A,in B,out Result)', unreal.Vector2D(1900, -1300), 'DISPATCH_RigVMDispatch_CoreEquals')
        joint_branch = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_ControlFlowBranch', 'Execute', unreal.Vector2D(2100, -1300), 'RigVMFunction_ControlFlowBranch')

        graph.add_link(self.switch_node, 'Cases.0', joint_branch, 'ExecuteContext', controller)

        graph.add_link(joints, 'Value', get_joint_num, 'Array', controller)
        graph.add_link(get_joint_num, 'Num', joint_num_equals, 'A', controller)
        graph.add_link(joint_num_equals, 'Result', joint_branch, 'Condition', controller)
        graph.add_link(joint_branch, 'False', control, 'ExecuteContext', controller)
        graph.add_link(control, 'ExecuteContext', control_spin, 'ExecuteContext', controller)

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

        graph.add_link(self.switch_node, 'Cases.1', wheel_rotate, 'ExecuteContext', controller)
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
        graph.add_link(self.switch_node, 'Cases.2', set_channel, 'ExecuteContext', controller)
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


class UnrealBendyRig(UnrealUtilRig):

    def _build_function_construct_graph(self):

        controller = self.function_controller
        library = self.library

        controller.add_local_variable_from_object_path('drivers', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', '')

        concat = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_NameConcat', 'Execute', unreal.Vector2D(-250.0, -200.0), 'Concat')
        vetala_lib_control = self._create_control(controller, 1632.0, -1264.0)
        vetala_lib_control1 = self._create_control(controller, 2704.0, -1264.0)
        spawn_null = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyAddNull', 'Execute', unreal.Vector2D(1136.0, -1248.0), 'Spawn Null')
        vetala_lib_get_item = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(912.0, -1456.0), 'vetalaLib_GetItem')
        get_transform = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetTransform', 'Execute', unreal.Vector2D(512.0, -1968.0), 'Get Transform')
        vetala_lib_get_item1 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(96.0, -1952.0), 'vetalaLib_GetItem')
        get_transform1 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetTransform', 'Execute', unreal.Vector2D(512.0, -1728.0), 'Get Transform')
        vetala_lib_get_item2 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(96.0, -1712.0), 'vetalaLib_GetItem')
        spawn_null1 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyAddNull', 'Execute', unreal.Vector2D(2336.0, -1248.0), 'Spawn Null')
        join = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_StringJoin', 'Execute', unreal.Vector2D(832.0, -976.0), 'Join')
        join1 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_StringJoin', 'Execute', unreal.Vector2D(2032.0, -704.0), 'Join')
        set_default_parent = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_SetDefaultParent', 'Execute', unreal.Vector2D(2944.0, -1248.0), 'Set Default Parent')
        set_default_parent1 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_SetDefaultParent', 'Execute', unreal.Vector2D(1888.0, -1248.0), 'Set Default Parent')
        for_loop = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_ForLoopCount', 'Execute', unreal.Vector2D(3648.0, -1376.0), 'For Loop')
        get_control_count = controller.add_variable_node('control_count', 'int32', None, True, '', unreal.Vector2D(3408.0, -1008.0), 'Get control_count')
        add = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathIntAdd', 'Execute', unreal.Vector2D(3616.0, -1104.0), 'Add')
        branch = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_ControlFlowBranch', 'Execute', unreal.Vector2D(4144.0, -1360.0), 'Branch')
        equals = controller.add_template_node('DISPATCH_RigVMDispatch_CoreEquals(in A,in B,out Result)', unreal.Vector2D(3856.0, -1552.0), 'Equals')
        or1 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathBoolOr', 'Execute', unreal.Vector2D(4032.0, -1504.0), 'Or')
        equals1 = controller.add_template_node('DISPATCH_RigVMDispatch_CoreEquals(in A,in B,out Result)', unreal.Vector2D(3856.0, -1440.0), 'Equals')
        subtract = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathIntSub', 'Execute', unreal.Vector2D(3824.89013671875, -1113.45263671875), 'Subtract')
        vetala_lib_control2 = self._create_control(controller, 5200.0, -1344.0)
        spline_from_items = controller.add_external_function_reference_node('/ControlRigSpline/SplineFunctionLibrary/SplineFunctionLibrary.SplineFunctionLibrary_C', 'SplineFromItems', unreal.Vector2D(3168.0, -1664.0), 'SplineFromItems')
        get_joints = controller.add_variable_node_from_object_path('joints', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(2880.0, -1568.0), 'Get joints')
        get_joints1 = controller.add_variable_node_from_object_path('joints', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(0.0, -1264.0), 'Get joints')
        num = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetNum(in Array,out Num)', unreal.Vector2D(272.0, -1264.0), 'Num')
        branch1 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_ControlFlowBranch', 'Execute', unreal.Vector2D(608.0, -1072.0), 'Branch')
        greater = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathIntGreater', 'Execute', unreal.Vector2D(533.29443359375, -1238.46142578125), 'Greater')
        position_from_spline = controller.add_unit_node_from_struct_path('/Script/ControlRigSpline.RigUnit_PositionFromControlRigSpline', 'Execute', unreal.Vector2D(4232.0, -1600.0), 'Position From Spline')
        make_transform = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathTransformMake', 'Execute', unreal.Vector2D(4416.0, -1440.0), 'Make Transform')
        spawn_null2 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyAddNull', 'Execute', unreal.Vector2D(4640.0, -1328.0), 'Spawn Null')
        subtract1 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathIntSub', 'Execute', unreal.Vector2D(4416.0, -1088.0), 'Subtract')
        get_parent = controller.add_variable_node_from_object_path('parent', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(4769.0, -1802.0), 'Get parent')
        vetala_lib_get_item3 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(4944.0, -1744.0), 'vetalaLib_GetItem')
        set_default_parent2 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_SetDefaultParent', 'Execute', unreal.Vector2D(5504.0, -1328.0), 'Set Default Parent')
        set_float_metadata = controller.add_template_node('DISPATCH_RigDispatch_SetMetadata(in Item,in Name,in NameSpace,in Value,out Success)', unreal.Vector2D(5936.0, -1200.0), 'Set Float Metadata')
        get_local_controls = controller.add_variable_node_from_object_path('local_controls', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(6160.0, -1472.0), 'Get local_controls')
        add1 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayAdd(io Array,in Element,out Index)', unreal.Vector2D(6432.0, -1328.0), 'Add')
        get_local_controls1 = controller.add_variable_node_from_object_path('local_controls', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(5536.0, -720.0), 'Get local_controls')
        add2 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayAdd(io Array,in Element,out Index)', unreal.Vector2D(5856.0, -720.0), 'Add')
        get_local_controls2 = controller.add_variable_node_from_object_path('local_controls', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(1952.0, -1536.0), 'Get local_controls')
        add3 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayAdd(io Array,in Element,out Index)', unreal.Vector2D(2144.0, -1456.0), 'Add')
        branch2 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_ControlFlowBranch', 'Execute', unreal.Vector2D(1248.0, -880.0), 'Branch')
        from_string = controller.add_template_node('DISPATCH_RigDispatch_FromString(in String,out Result)', unreal.Vector2D(1296.0, -560.0), 'From String')
        get_top_control = controller.add_variable_node('top_control', 'bool', None, True, '', unreal.Vector2D(925.0342407226562, -716.7176513671875), 'Get top_control')
        if1 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(1747.367431640625, -1458.384521484375), 'If')
        branch3 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_ControlFlowBranch', 'Execute', unreal.Vector2D(2432.0, -816.0), 'Branch')
        get_btm_control = controller.add_variable_node('btm_control', 'bool', None, True, '', unreal.Vector2D(2247.478759765625, -562.0509033203125), 'Get btm_control')
        if2 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(3008.0, -1424.0), 'If')
        spawn_null3 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyAddNull', 'Execute', unreal.Vector2D(2704.0, -640.0), 'Spawn Null')
        from_string1 = controller.add_template_node('DISPATCH_RigDispatch_FromString(in String,out Result)', unreal.Vector2D(2144.0, -432.0), 'From String')
        spawn_null4 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyAddNull', 'Execute', unreal.Vector2D(4640.0, -928.0), 'Spawn Null')
        set_item_array_metadata = controller.add_template_node('DISPATCH_RigDispatch_SetMetadata(in Item,in Name,in NameSpace,in Value,out Success)', unreal.Vector2D(6992.0, -1024.0), 'Set Item Array Metadata')
        add4 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayAdd(io Array,in Element,out Index)', unreal.Vector2D(6736.0, -1328.0), 'Add')
        get_drivers = controller.add_variable_node_from_object_path('drivers', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(6542.47412109375, -1457.364501953125), 'Get drivers')
        get_drivers1 = controller.add_variable_node_from_object_path('drivers', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(6880.0, -704.0), 'Get drivers')
        get_joints2 = controller.add_variable_node_from_object_path('joints', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(6415.8076171875, -633.3643798828125), 'Get joints')
        vetala_lib_get_item4 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(6576.0, -624.0), 'vetalaLib_GetItem')
        reset = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayReset(io Array)', unreal.Vector2D(3698.94921875, -1798.01318359375), 'Reset')
        get_drivers2 = controller.add_variable_node_from_object_path('drivers', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(3251.94921875, -1883.679931640625), 'Get drivers')
        set_item_metadata = controller.add_template_node('DISPATCH_RigDispatch_SetMetadata(in Item,in Name,in NameSpace,in Value,out Success)', unreal.Vector2D(3120.0, -992.0), 'Set Item Metadata')
        set_item_metadata1 = controller.add_template_node('DISPATCH_RigDispatch_SetMetadata(in Item,in Name,in NameSpace,in Value,out Success)', unreal.Vector2D(2000.0, -992.0), 'Set Item Metadata')
        spawn_transform_control = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyAddControlTransform', 'Execute', unreal.Vector2D(1600.0, -624.0), 'Spawn Transform Control')

        controller.resolve_wild_card_pin(f'{concat.get_node_path()}.Result', 'FName', 'None')
        controller.resolve_wild_card_pin(f'{add.get_node_path()}.Result', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{equals.get_node_path()}.A', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{equals.get_node_path()}.B', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{equals1.get_node_path()}.A', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{equals1.get_node_path()}.B', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{num.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{greater.get_node_path()}.A', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{greater.get_node_path()}.B', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{add1.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{add2.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{add3.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{if1.get_node_path()}.Result', 'FRigElementKey', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{if2.get_node_path()}.Result', 'FRigElementKey', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{add4.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')

        controller.set_array_pin_size(f'{n(join)}.Values', 2)
        controller.set_array_pin_size(f'{n(join1)}.Values', 2)

        graph.add_link(branch2, 'True', vetala_lib_control, 'ExecuteContext', controller)
        graph.add_link(branch3, 'True', vetala_lib_control1, 'ExecuteContext', controller)
        graph.add_link(spawn_null, 'ExecutePin', branch2, 'ExecuteContext', controller)
        graph.add_link(add3, 'ExecuteContext', spawn_null1, 'ExecutePin', controller)
        graph.add_link(spawn_null1, 'ExecutePin', branch3, 'ExecuteContext', controller)
        graph.add_link(set_default_parent, 'ExecutePin', set_item_metadata, 'ExecuteContext', controller)
        graph.add_link(set_default_parent1, 'ExecutePin', set_item_metadata1, 'ExecuteContext', controller)
        graph.add_link(reset, 'ExecuteContext', for_loop, 'ExecutePin', controller)
        graph.add_link(for_loop, 'ExecutePin', branch, 'ExecuteContext', controller)
        graph.add_link(for_loop, 'Completed', add2, 'ExecuteContext', controller)
        graph.add_link(spawn_null4, 'ExecutePin', vetala_lib_control2, 'ExecuteContext', controller)
        graph.add_link(vetala_lib_control2, 'ExecuteContext', set_default_parent2, 'ExecutePin', controller)
        graph.add_link(set_item_metadata, 'ExecuteContext', spline_from_items, 'ExecuteContext', controller)
        graph.add_link(spline_from_items, 'ExecuteContext', reset, 'ExecuteContext', controller)
        graph.add_link('DISPATCH_RigVMDispatch_SwitchInt32', 'Cases.0', branch1, 'ExecuteContext', controller)
        graph.add_link(set_default_parent2, 'ExecutePin', set_float_metadata, 'ExecuteContext', controller)
        graph.add_link(set_float_metadata, 'ExecuteContext', add1, 'ExecuteContext', controller)
        graph.add_link(add1, 'ExecuteContext', add4, 'ExecuteContext', controller)
        graph.add_link(add2, 'ExecuteContext', set_item_array_metadata, 'ExecuteContext', controller)
        graph.add_link(set_item_metadata1, 'ExecuteContext', add3, 'ExecuteContext', controller)
        graph.add_link('Int to Name', 'Result', concat, 'B', controller)
        graph.add_link(concat, 'Result', 'VariableNode', 'Value', controller)
        graph.add_link(vetala_lib_get_item, 'Element', vetala_lib_control, 'parent', controller)
        graph.add_link(spawn_null, 'Item', vetala_lib_control, 'driven', controller)
        graph.add_link(join, 'Result', vetala_lib_control, 'description', controller)
        graph.add_link('Entry', 'side', vetala_lib_control, 'side', controller)
        graph.add_link('Entry', 'joint_token', vetala_lib_control, 'joint_token', controller)
        graph.add_link('Entry', 'restrain_numbering', vetala_lib_control, 'restrain_numbering', controller)
        graph.add_link('Entry', 'shape', vetala_lib_control, 'shape', controller)
        graph.add_link('Entry', 'color', vetala_lib_control, 'color', controller)
        graph.add_link('Entry', 'sub_color', vetala_lib_control, 'sub_color', controller)
        graph.add_link('Entry', 'shape_translate', vetala_lib_control, 'translate', controller)
        graph.add_link('Entry', 'shape_rotate', vetala_lib_control, 'rotate', controller)
        graph.add_link('Entry', 'shape_scale', vetala_lib_control, 'scale', controller)
        graph.add_link(vetala_lib_control, 'Control', if1, 'True', controller)
        graph.add_link(vetala_lib_control, 'Control', set_item_metadata1, 'Item', controller)
        graph.add_link(vetala_lib_get_item, 'Element', vetala_lib_control1, 'parent', controller)
        graph.add_link(spawn_null1, 'Item', vetala_lib_control1, 'driven', controller)
        graph.add_link(join1, 'Result', vetala_lib_control1, 'description', controller)
        graph.add_link('Entry', 'side', vetala_lib_control1, 'side', controller)
        graph.add_link('Entry', 'joint_token', vetala_lib_control1, 'joint_token', controller)
        graph.add_link('Entry', 'restrain_numbering', vetala_lib_control1, 'restrain_numbering', controller)
        graph.add_link('Entry', 'shape', vetala_lib_control1, 'shape', controller)
        graph.add_link('Entry', 'color', vetala_lib_control1, 'color', controller)
        graph.add_link('Entry', 'sub_color', vetala_lib_control1, 'sub_color', controller)
        graph.add_link('Entry', 'shape_translate', vetala_lib_control1, 'translate', controller)
        graph.add_link('Entry', 'shape_rotate', vetala_lib_control1, 'rotate', controller)
        graph.add_link('Entry', 'shape_scale', vetala_lib_control1, 'scale', controller)
        graph.add_link(vetala_lib_control1, 'Control', if2, 'True', controller)
        graph.add_link(branch1, 'True', spawn_null, 'ExecutePin', controller)
        graph.add_link(spawn_null, 'Item', set_default_parent1, 'Child', controller)
        graph.add_link(spawn_null, 'Item', set_item_metadata1, 'Value', controller)
        graph.add_link(get_transform, 'Transform', spawn_null, 'Transform', controller)
        graph.add_link('Entry', 'parent', vetala_lib_get_item, 'Array', controller)
        graph.add_link(vetala_lib_get_item, 'Element', spawn_null3, 'Parent', controller)
        graph.add_link(vetala_lib_get_item, 'Element', spawn_transform_control, 'Parent', controller)
        graph.add_link(vetala_lib_get_item1, 'Element', get_transform, 'Item', controller)
        graph.add_link(get_transform, 'Transform.Rotation', make_transform, 'Rotation', controller)
        graph.add_link('Entry', 'joints', vetala_lib_get_item1, 'Array', controller)
        graph.add_link(vetala_lib_get_item2, 'Element', get_transform1, 'Item', controller)
        graph.add_link(get_transform1, 'Transform', spawn_null1, 'Transform', controller)
        graph.add_link(get_transform1, 'Transform', spawn_null3, 'Transform', controller)
        graph.add_link(get_transform1, 'Transform', spawn_transform_control, 'InitialValue', controller)
        graph.add_link('Entry', 'joints', vetala_lib_get_item2, 'Array', controller)
        graph.add_link(spawn_null1, 'Item', set_default_parent, 'Child', controller)
        graph.add_link(spawn_null1, 'Item', set_item_metadata, 'Value', controller)
        graph.add_link(join, 'Result', from_string, 'String', controller)
        graph.add_link(join1, 'Result', from_string1, 'String', controller)
        graph.add_link(branch3, 'Completed', set_default_parent, 'ExecutePin', controller)
        graph.add_link(if2, 'Result', set_default_parent, 'Parent', controller)
        graph.add_link(branch2, 'Completed', set_default_parent1, 'ExecutePin', controller)
        graph.add_link(if1, 'Result', set_default_parent1, 'Parent', controller)
        graph.add_link(add, 'Result', for_loop, 'Count', controller)
        graph.add_link(for_loop, 'Index', equals, 'A', controller)
        graph.add_link(for_loop, 'Index', equals1, 'A', controller)
        graph.add_link(for_loop, 'Index', subtract1, 'A', controller)
        graph.add_link(for_loop, 'Ratio', position_from_spline, 'U', controller)
        graph.add_link(for_loop, 'Ratio', set_float_metadata, 'Value', controller)
        graph.add_link(get_control_count, 'Value', add, 'A', controller)
        graph.add_link(add, 'Result', subtract, 'A', controller)
        graph.add_link(or1, 'Result', branch, 'Condition', controller)
        graph.add_link(branch, 'False', spawn_null2, 'ExecutePin', controller)
        graph.add_link(equals, 'Result', or1, 'A', controller)
        graph.add_link(equals1, 'Result', or1, 'B', controller)
        graph.add_link(subtract, 'Result', equals1, 'B', controller)
        graph.add_link(subtract1, 'Result', vetala_lib_control2, 'increment', controller)
        graph.add_link(spawn_null4, 'Item', vetala_lib_control2, 'parent', controller)
        graph.add_link(spawn_null2, 'Item', vetala_lib_control2, 'driven', controller)
        graph.add_link('Entry', 'description', vetala_lib_control2, 'description', controller)
        graph.add_link('Entry', 'side', vetala_lib_control2, 'side', controller)
        graph.add_link('Entry', 'joint_token', vetala_lib_control2, 'joint_token', controller)
        graph.add_link('Entry', 'restrain_numbering', vetala_lib_control2, 'restrain_numbering', controller)
        graph.add_link('Entry', 'shape', vetala_lib_control2, 'shape', controller)
        graph.add_link('Entry', 'color', vetala_lib_control2, 'color', controller)
        graph.add_link('Entry', 'sub_color', vetala_lib_control2, 'sub_color', controller)
        graph.add_link('Entry', 'shape_translate', vetala_lib_control2, 'translate', controller)
        graph.add_link('Entry', 'shape_rotate', vetala_lib_control2, 'rotate', controller)
        graph.add_link('Entry', 'shape_scale', vetala_lib_control2, 'scale', controller)
        graph.add_link(vetala_lib_control2, 'Control', set_default_parent2, 'Parent', controller)
        graph.add_link(vetala_lib_control2, 'Control', add1, 'Element', controller)
        graph.add_link(get_joints, 'Value', spline_from_items, 'Items', controller)
        graph.add_link(spline_from_items, 'Spline', position_from_spline, 'Spline', controller)
        graph.add_link(get_joints1, 'Value', num, 'Array', controller)
        graph.add_link(num, 'Num', 'Greater', 'A', controller)
        graph.add_link(greater, 'Result', branch1, 'Condition', controller)
        graph.add_link(num, 'Num', greater, 'A', controller)
        graph.add_link(position_from_spline, 'Position', make_transform, 'Translation', controller)
        graph.add_link(make_transform, 'Result', spawn_null2, 'Transform', controller)
        graph.add_link(make_transform, 'Result', spawn_null4, 'Transform', controller)
        graph.add_link(spawn_null2, 'ExecutePin', spawn_null4, 'ExecutePin', controller)
        graph.add_link(spawn_null2, 'Item', set_default_parent2, 'Child', controller)
        graph.add_link(get_parent, 'Value', vetala_lib_get_item3, 'Array', controller)
        graph.add_link(vetala_lib_get_item3, 'Element', spawn_null4, 'Parent', controller)
        graph.add_link(spawn_null4, 'Item', set_float_metadata, 'Item', controller)
        graph.add_link(get_local_controls, 'Value', add1, 'Array', controller)
        graph.add_link(get_local_controls1, 'Value', add2, 'Array', controller)
        graph.add_link(if2, 'Result', add2, 'Element', controller)
        graph.add_link(get_local_controls2, 'Value', add3, 'Array', controller)
        graph.add_link(if1, 'Result', add3, 'Element', controller)
        graph.add_link(get_top_control, 'Value', branch2, 'Condition', controller)
        graph.add_link(branch2, 'False', spawn_transform_control, 'ExecutePin', controller)
        graph.add_link(from_string, 'Result', spawn_transform_control, 'Name', controller)
        graph.add_link(get_top_control, 'Value', if1, 'Condition', controller)
        graph.add_link(spawn_transform_control, 'Item', if1, 'False', controller)
        graph.add_link(get_btm_control, 'Value', branch3, 'Condition', controller)
        graph.add_link(branch3, 'False', spawn_null3, 'ExecutePin', controller)
        graph.add_link(get_btm_control, 'Value', if2, 'Condition', controller)
        graph.add_link(spawn_null3, 'Item', if2, 'False', controller)
        graph.add_link(if2, 'Result', set_item_metadata, 'Item', controller)
        graph.add_link(from_string1, 'Result', spawn_null3, 'Name', controller)
        graph.add_link(spawn_null4, 'Item', add4, 'Element', controller)
        graph.add_link(vetala_lib_get_item4, 'Element', set_item_array_metadata, 'Item', controller)
        graph.add_link(get_drivers1, 'Value', set_item_array_metadata, 'Value', controller)
        graph.add_link(get_drivers, 'Value', add4, 'Array', controller)
        graph.add_link(get_joints2, 'Value', vetala_lib_get_item4, 'Array', controller)
        graph.add_link(get_drivers2, 'Value', reset, 'Array', controller)
        graph.add_link('Entry', 'description', join, 'Values.0', controller)
        graph.add_link('Entry', 'description', join1, 'Values.0', controller)

        graph.set_pin(concat, 'A', 'Control_', controller)
        graph.set_pin(vetala_lib_control, 'increment', '0', controller)
        graph.set_pin(vetala_lib_control, 'sub_count', '0', controller)
        graph.set_pin(vetala_lib_control, 'scale_offset', '1.500000', controller)
        graph.set_pin(vetala_lib_control1, 'increment', '0', controller)
        graph.set_pin(vetala_lib_control1, 'sub_count', '0', controller)
        graph.set_pin(vetala_lib_control1, 'scale_offset', '1.500000', controller)
        graph.set_pin(spawn_null, 'Parent', '(Type=Bone,Name="None")', controller)
        graph.set_pin(spawn_null, 'Name', 'top', controller)
        graph.set_pin(spawn_null, 'Space', 'GlobalSpace', controller)
        graph.set_pin(get_transform, 'Space', 'GlobalSpace', controller)
        graph.set_pin(get_transform, 'bInitial', 'False', controller)
        graph.set_pin(get_transform1, 'Space', 'GlobalSpace', controller)
        graph.set_pin(get_transform1, 'bInitial', 'False', controller)
        graph.set_pin(vetala_lib_get_item2, 'index', '-1', controller)
        graph.set_pin(spawn_null1, 'Parent', '(Type=Bone,Name="None")', controller)
        graph.set_pin(spawn_null1, 'Name', 'btm', controller)
        graph.set_pin(spawn_null1, 'Space', 'GlobalSpace', controller)
        graph.set_pin(join, 'Values', '("","top")', controller)
        graph.set_pin(join, 'Separator', '_', controller)
        graph.set_pin(join1, 'Values', '("","btm")', controller)
        graph.set_pin(join1, 'Separator', '_', controller)
        graph.set_pin(add, 'B', '2', controller)
        graph.set_pin(equals, 'B', '0', controller)
        graph.set_pin(subtract, 'B', '1', controller)
        graph.set_pin(vetala_lib_control2, 'sub_count', '0', controller)
        graph.set_pin(vetala_lib_control2, 'scale_offset', '1', controller)
        graph.set_pin(spline_from_items, 'Spline Mode', 'Hermite', controller)
        graph.set_pin(spline_from_items, 'Samples Per Segment', '16', controller)
        graph.set_pin(greater, 'B', '0', controller)
        graph.set_pin(make_transform, 'Scale', '(X=1.000000,Y=1.000000,Z=1.000000)', controller)
        graph.set_pin(spawn_null2, 'Parent', '(Type=Bone,Name="None")', controller)
        graph.set_pin(spawn_null2, 'Name', 'bend_null', controller)
        graph.set_pin(spawn_null2, 'Space', 'LocalSpace', controller)
        graph.set_pin(subtract1, 'B', '1', controller)
        graph.set_pin(set_float_metadata, 'Name', 'twist_weight', controller)
        graph.set_pin(set_float_metadata, 'NameSpace', 'Self', controller)
        graph.set_pin(spawn_null3, 'Space', 'GlobalSpace', controller)
        graph.set_pin(spawn_null4, 'Name', 'drive_bend', controller)
        graph.set_pin(spawn_null4, 'Space', 'GlobalSpace', controller)
        graph.set_pin(set_item_array_metadata, 'Name', 'drivers', controller)
        graph.set_pin(set_item_array_metadata, 'NameSpace', 'Self', controller)
        graph.set_pin(set_item_metadata, 'Name', 'null', controller)
        graph.set_pin(set_item_metadata, 'NameSpace', 'Self', controller)
        graph.set_pin(set_item_metadata1, 'Name', 'null', controller)
        graph.set_pin(set_item_metadata1, 'NameSpace', 'Self', controller)
        graph.set_pin(spawn_transform_control, 'OffsetTransform', '(Rotation=(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=1.000000,Y=1.000000,Z=1.000000))', controller)
        graph.set_pin(spawn_transform_control, 'OffsetSpace', 'GlobalSpace', controller)
        graph.set_pin(spawn_transform_control, 'Settings', '(InitialSpace=LocalSpace,bUsePreferredRotationOrder=False,PreferredRotationOrder=YZX,Limits=(LimitTranslationX=(bMinimum=False,bMaximum=False),LimitTranslationY=(bMinimum=False,bMaximum=False),LimitTranslationZ=(bMinimum=False,bMaximum=False),LimitPitch=(bMinimum=False,bMaximum=False),LimitYaw=(bMinimum=False,bMaximum=False),LimitRoll=(bMinimum=False,bMaximum=False),LimitScaleX=(bMinimum=False,bMaximum=False),LimitScaleY=(bMinimum=False,bMaximum=False),LimitScaleZ=(bMinimum=False,bMaximum=False),MinValue=(Location=(X=-100.000000,Y=-100.000000,Z=-100.000000),Rotation=(Pitch=-180.000000,Yaw=-180.000000,Roll=-180.000000),Scale=(X=0.000000,Y=0.000000,Z=0.000000)),MaxValue=(Location=(X=100.000000,Y=100.000000,Z=100.000000),Rotation=(Pitch=180.000000,Yaw=180.000000,Roll=180.000000),Scale=(X=10.000000,Y=10.000000,Z=10.000000)),bDrawLimits=True),Shape=(bVisible=false,Name="Default",Color=(R=0.200000,G=0.200000,B=0.200000,A=1.000000),Transform=(Rotation=(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=1.000000,Y=1.000000,Z=1.000000))),Proxy=(bIsProxy=true,ShapeVisibility=BasedOnSelection),FilteredChannels=(),DisplayName="None")', controller)

        current_locals = locals()
        nodes = unreal_lib.graph.filter_nodes(current_locals.values())
        node = unreal_lib.graph.comment_nodes(nodes, controller, 'Construction')
        nodes.append(node)
        unreal_lib.graph.move_nodes(500, -2000, nodes, controller)

    def _build_function_forward_graph(self):

        controller = self.function_controller
        library = self.library

        spline_ik = controller.add_external_function_reference_node('/ControlRigSpline/SplineFunctionLibrary/SplineFunctionLibrary.SplineFunctionLibrary_C', 'SplineIK', unreal.Vector2D(5232.0, 1056.0), 'SplineIK')
        get_joints = controller.add_variable_node_from_object_path('joints', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(1168.0, 1184.0), 'Get joints')
        vetala_lib_get_item = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(1488.0, 1392.0), 'vetalaLib_GetItem')
        num = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetNum(in Array,out Num)', unreal.Vector2D(1404.0, 1199.0), 'Num')
        greater = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathIntGreater', 'Execute', unreal.Vector2D(1584.0, 1184.0), 'Greater')
        branch = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_ControlFlowBranch', 'Execute', unreal.Vector2D(1824.0, 1104.0), 'Branch')
        get_item_array_metadata = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(1248.0, 2128.0), 'Get Item Array Metadata')
        concat = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_NameConcat', 'Execute', unreal.Vector2D(1056.0, 2192.0), 'Concat')
        int_to_name = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathIntToName', 'Execute', unreal.Vector2D(848.0, 2240.0), 'Int to Name')
        vetala_lib_find_bone_aim_axis = controller.add_function_reference_node(library.find_function('vetalaLib_findBoneAimAxis'), unreal.Vector2D(2032.0, 1120.0), 'vetalaLib_findBoneAimAxis')
        cross = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathVectorCross', 'Execute', unreal.Vector2D(4896.0, 1504.0), 'Cross')
        get_item_array_metadata1 = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(1808.0, 1472.0), 'Get Item Array Metadata')
        vetala_lib_get_item1 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(1648.0, 2224.0), 'vetalaLib_GetItem')
        vetala_lib_get_item2 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(1632.0, 2400.0), 'vetalaLib_GetItem')
        get_float_metadata = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(3168.0, 1632.0), 'Get Float Metadata')
        subtract = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathDoubleSub', 'Execute', unreal.Vector2D(3408.0, 1952.0), 'Subtract')
        branch1 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_ControlFlowBranch', 'Execute', unreal.Vector2D(3200.0, 1360.0), 'Branch')
        item_exists = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_ItemExists', 'Execute', unreal.Vector2D(2736.0, 1456.0), 'Item Exists')
        position_constraint = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_PositionConstraintLocalSpaceOffset', 'Execute', unreal.Vector2D(3824.0, 1872.0), 'Position Constraint')
        rotation_constraint = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_RotationConstraintLocalSpaceOffset', 'Execute', unreal.Vector2D(4176.0, 1856.0), 'Rotation Constraint')
        get_item_metadata = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(1792.0, 2048.0), 'Get Item Metadata')
        get_item_metadata1 = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(1872.0, 2704.0), 'Get Item Metadata')
        for_each = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayIterator(in Array,out Element,out Index,out Count,out Ratio)', unreal.Vector2D(2688.0, 1024.0), 'For Each')
        for_each1 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayIterator(in Array,out Element,out Index,out Count,out Ratio)', unreal.Vector2D(6122.0009765625, 1483.7525634765625), 'For Each')
        get_joints1 = controller.add_variable_node_from_object_path('joints', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(5536.0, 1904.0), 'Get joints')
        get_children = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_CollectionChildrenArray', 'Execute', unreal.Vector2D(6448.0, 1760.0), 'Get Children')
        for_each2 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayIterator(in Array,out Element,out Index,out Count,out Ratio)', unreal.Vector2D(6994.0, 1584.0), 'For Each')
        set_transform = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_SetTransform', 'Execute', unreal.Vector2D(8560.0, 1648.0), 'Set Transform')
        project_to_new_parent = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_ProjectTransformToNewParent', 'Execute', unreal.Vector2D(7904.0, 1808.0), 'Project to new Parent')
        find = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayFind(in Array,in Element,out Index,out Success)', unreal.Vector2D(7376.0, 1408.0), 'Find')
        branch2 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_ControlFlowBranch', 'Execute', unreal.Vector2D(7728.0, 1440.0), 'Branch')
        remove = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayRemove(io Array,in Index)', unreal.Vector2D(2672.0, 2864.0), 'Remove')
        remove1 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayRemove(io Array,in Index)', unreal.Vector2D(2864.0, 2864.0), 'Remove')
        insert = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayInsert(io Array,in Index,in Element)', unreal.Vector2D(3072.0, 2864.0), 'Insert')
        add = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayAdd(io Array,in Element,out Index)', unreal.Vector2D(3296.0, 2864.0), 'Add')
        remove2 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayRemove(io Array,in Index)', unreal.Vector2D(5840.0, 1600.0), 'Remove')
        clone = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayClone(in Array,out Clone)', unreal.Vector2D(5712.0, 1792.0), 'Clone')
        aim_constraint = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_AimConstraintLocalSpaceOffset', 'Execute', unreal.Vector2D(2384.0, 1856.0), 'Aim Constraint')
        aim_constraint1 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_AimConstraintLocalSpaceOffset', 'Execute', unreal.Vector2D(2736.0, 1856.0), 'Aim Constraint')
        get_joints2 = controller.add_variable_node_from_object_path('joints', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(1168.0, 1424.0), 'Get joints')
        vetala_lib_find_bone_aim_axis1 = controller.add_function_reference_node(library.find_function('vetalaLib_findBoneAimAxis'), unreal.Vector2D(4448.0, 1360.0), 'vetalaLib_findBoneAimAxis')
        get_joints3 = controller.add_variable_node_from_object_path('joints', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(3952.0, 1216.0), 'Get joints')
        vetala_lib_get_item3 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(4208.0, 1456.0), 'vetalaLib_GetItem')
        get_layer = controller.add_variable_node('layer', 'int32', None, True, '', unreal.Vector2D(688.0, 2272.0), 'Get layer')
        get_joints4 = controller.add_variable_node_from_object_path('joints', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(7118.1787109375, 1406.65283203125), 'Get joints')
        num1 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetNum(in Array,out Num)', unreal.Vector2D(1902.5498046875, 3003.9931640625), 'Num')
        greater1 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathIntGreater', 'Execute', unreal.Vector2D(2135.5498046875, 3035.659912109375), 'Greater')
        branch3 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_ControlFlowBranch', 'Execute', unreal.Vector2D(2466.216552734375, 3007.659912109375), 'Branch')

        controller.resolve_wild_card_pin(f'{num.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{greater.get_node_path()}.A', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{greater.get_node_path()}.B', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{concat.get_node_path()}.Result', 'FName', 'None')
        controller.resolve_wild_card_pin(f'{for_each.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{for_each1.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{for_each2.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{remove.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{remove1.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{add.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{remove2.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{num1.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{greater1.get_node_path()}.A', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{greater1.get_node_path()}.B', 'int32', 'None')

        controller.set_array_pin_size(f'{n(position_constraint)}.Parents', 2)
        controller.set_array_pin_size(f'{n(rotation_constraint)}.Parents', 2)
        controller.set_array_pin_size(f'{n(aim_constraint)}.Parents', 1)
        controller.set_array_pin_size(f'{n(aim_constraint1)}.Parents', 1)

        graph.add_link(vetala_lib_find_bone_aim_axis1, 'ExecuteContext', spline_ik, 'ExecuteContext', controller)
        graph.add_link(spline_ik, 'ExecuteContext', remove2, 'ExecuteContext', controller)
        graph.add_link('DISPATCH_RigVMDispatch_SwitchInt32', 'Cases.1', branch, 'ExecuteContext', controller)
        graph.add_link(branch, 'True', vetala_lib_find_bone_aim_axis, 'ExecuteContext', controller)
        graph.add_link(vetala_lib_find_bone_aim_axis, 'ExecuteContext', aim_constraint, 'ExecutePin', controller)
        graph.add_link(for_each, 'ExecuteContext', branch1, 'ExecuteContext', controller)
        graph.add_link(add, 'ExecuteContext', for_each, 'ExecuteContext', controller)
        graph.add_link(for_each, 'Completed', vetala_lib_find_bone_aim_axis1, 'ExecuteContext', controller)
        graph.add_link(remove2, 'ExecuteContext', for_each1, 'ExecuteContext', controller)
        graph.add_link(for_each1, 'ExecuteContext', for_each2, 'ExecuteContext', controller)
        graph.add_link(for_each2, 'ExecuteContext', branch2, 'ExecuteContext', controller)
        graph.add_link(branch3, 'True', remove, 'ExecuteContext', controller)
        graph.add_link(remove, 'ExecuteContext', remove1, 'ExecuteContext', controller)
        graph.add_link(remove1, 'ExecuteContext', insert, 'ExecuteContext', controller)
        graph.add_link(insert, 'ExecuteContext', add, 'ExecuteContext', controller)
        graph.add_link(aim_constraint1, 'ExecutePin', branch3, 'ExecuteContext', controller)
        graph.add_link(add, 'Array', spline_ik, 'Controls', controller)
        graph.add_link(get_joints3, 'Value', spline_ik, 'Bones', controller)
        graph.add_link(vetala_lib_find_bone_aim_axis1, 'Result', spline_ik, 'Primary Axis', controller)
        graph.add_link(cross, 'Result', spline_ik, 'Up Axis', controller)
        graph.add_link(cross, 'Result', spline_ik, 'Secondary Spline Direction', controller)
        graph.add_link(get_joints, 'Value', num, 'Array', controller)
        graph.add_link(get_joints2, 'Value', vetala_lib_get_item, 'Array', controller)
        graph.add_link(vetala_lib_get_item, 'Element', get_item_array_metadata, 'Item', controller)
        graph.add_link(vetala_lib_get_item, 'Element', vetala_lib_find_bone_aim_axis, 'Bone', controller)
        graph.add_link(vetala_lib_get_item, 'Element', get_item_array_metadata1, 'Item', controller)
        graph.add_link(num, 'Num', greater, 'A', controller)
        graph.add_link(greater, 'Result', branch, 'Condition', controller)
        graph.add_link(concat, 'Result', get_item_array_metadata, 'Name', controller)
        graph.add_link(get_item_array_metadata, 'Value', vetala_lib_get_item1, 'Array', controller)
        graph.add_link(get_item_array_metadata, 'Value', vetala_lib_get_item2, 'Array', controller)
        graph.add_link(get_item_array_metadata, 'Value', remove, 'Array', controller)
        graph.add_link(get_item_array_metadata, 'Value', num1, 'Array', controller)
        graph.add_link(int_to_name, 'Result', concat, 'B', controller)
        graph.add_link(get_layer, 'Value', int_to_name, 'Number', controller)
        graph.add_link(vetala_lib_find_bone_aim_axis, 'Result', aim_constraint, 'AimAxis', controller)
        graph.add_link(vetala_lib_find_bone_aim_axis, 'Result', aim_constraint1, 'AimAxis', controller)
        graph.add_link(vetala_lib_find_bone_aim_axis1, 'Result', cross, 'A', controller)
        graph.add_link(get_item_array_metadata1, 'Value', for_each, 'Array', controller)
        graph.add_link(vetala_lib_get_item1, 'Element', get_item_metadata, 'Item', controller)
        graph.add_link(vetala_lib_get_item2, 'Element', get_item_metadata1, 'Item', controller)
        graph.add_link(for_each, 'Element', get_float_metadata, 'Item', controller)
        graph.add_link(get_float_metadata, 'Value', subtract, 'B', controller)
        graph.add_link(item_exists, 'Exists', branch1, 'Condition', controller)
        graph.add_link(branch1, 'True', position_constraint, 'ExecutePin', controller)
        graph.add_link(for_each, 'Element', item_exists, 'Item', controller)
        graph.add_link(position_constraint, 'ExecutePin', rotation_constraint, 'ExecutePin', controller)
        graph.add_link(for_each, 'Element', position_constraint, 'Child', controller)
        graph.add_link(for_each, 'Element', rotation_constraint, 'Child', controller)
        graph.add_link(get_item_metadata, 'Value', insert, 'Element', controller)
        graph.add_link(get_item_metadata, 'Value', aim_constraint, 'Child', controller)
        graph.add_link(get_item_metadata1, 'Value', add, 'Element', controller)
        graph.add_link(get_item_metadata1, 'Value', aim_constraint1, 'Child', controller)
        graph.add_link(remove2, 'Array', for_each1, 'Array', controller)
        graph.add_link(for_each1, 'Element', get_children, 'Parent', controller)
        graph.add_link(for_each1, 'Element', project_to_new_parent, 'OldParent', controller)
        graph.add_link(for_each1, 'Element', project_to_new_parent, 'NewParent', controller)
        graph.add_link(get_joints1, 'Value', clone, 'Array', controller)
        graph.add_link(get_children, 'Items', for_each2, 'Array', controller)
        graph.add_link(for_each2, 'Element', set_transform, 'Item', controller)
        graph.add_link(for_each2, 'Element', project_to_new_parent, 'Child', controller)
        graph.add_link(for_each2, 'Element', find, 'Element', controller)
        graph.add_link(branch2, 'False', set_transform, 'ExecutePin', controller)
        graph.add_link(project_to_new_parent, 'Transform', set_transform, 'Value', controller)
        graph.add_link(get_joints4, 'Value', find, 'Array', controller)
        graph.add_link(find, 'Success', branch2, 'Condition', controller)
        graph.add_link(remove, 'Array', remove1, 'Array', controller)
        graph.add_link(remove1, 'Array', insert, 'Array', controller)
        graph.add_link(insert, 'Array', add, 'Array', controller)
        graph.add_link(clone, 'Clone', remove2, 'Array', controller)
        graph.add_link(aim_constraint, 'ExecutePin', aim_constraint1, 'ExecutePin', controller)
        graph.add_link(vetala_lib_get_item3, 'Element', vetala_lib_find_bone_aim_axis1, 'Bone', controller)
        graph.add_link(get_joints3, 'Value', vetala_lib_get_item3, 'Array', controller)
        graph.add_link(num1, 'Num', greater1, 'A', controller)
        graph.add_link(greater1, 'Result', branch3, 'Condition', controller)
        graph.add_link(vetala_lib_get_item1, 'Element', aim_constraint, 'WorldUp.Space', controller)
        graph.add_link(vetala_lib_get_item2, 'Element', aim_constraint1, 'WorldUp.Space', controller)
        graph.add_link(vetala_lib_get_item1, 'Element', position_constraint, 'Parents.0.Item', controller)
        graph.add_link(vetala_lib_get_item1, 'Element', aim_constraint1, 'Parents.0.Item', controller)
        graph.add_link(vetala_lib_get_item2, 'Element', position_constraint, 'Parents.1.Item', controller)
        graph.add_link(vetala_lib_get_item2, 'Element', aim_constraint, 'Parents.0.Item', controller)
        graph.add_link(get_float_metadata, 'Value', position_constraint, 'Parents.1.Weight', controller)
        graph.add_link(get_float_metadata, 'Value', rotation_constraint, 'Parents.1.Weight', controller)
        graph.add_link(subtract, 'Result', position_constraint, 'Parents.0.Weight', controller)
        graph.add_link(subtract, 'Result', rotation_constraint, 'Parents.0.Weight', controller)
        graph.add_link(get_item_metadata, 'Value', rotation_constraint, 'Parents.0.Item', controller)
        graph.add_link(get_item_metadata1, 'Value', rotation_constraint, 'Parents.1.Item', controller)

        graph.set_pin(spline_ik, 'debug', 'false', controller)
        graph.set_pin(spline_ik, 'Stretch', 'true', controller)
        graph.set_pin(spline_ik, 'Spline Mode', 'BSpline', controller)
        graph.set_pin(spline_ik, 'Samples Per Segment', '16', controller)
        graph.set_pin(greater, 'B', '0', controller)
        graph.set_pin(get_item_array_metadata, 'NameSpace', 'Self', controller)
        graph.set_pin(concat, 'A', 'Controls_', controller)
        graph.set_pin(int_to_name, 'PaddedSize', '0', controller)
        graph.set_pin(cross, 'B', '(X=0.000000,Y=1.000000,Z=0.000000)', controller)
        graph.set_pin(get_item_array_metadata1, 'Name', 'drivers', controller)
        graph.set_pin(get_item_array_metadata1, 'NameSpace', 'Self', controller)
        graph.set_pin(vetala_lib_get_item2, 'index', '-1', controller)
        graph.set_pin(get_float_metadata, 'Name', 'twist_weight', controller)
        graph.set_pin(get_float_metadata, 'NameSpace', 'Self', controller)
        graph.set_pin(get_float_metadata, 'Default', '0.000000', controller)
        graph.set_pin(subtract, 'A', '1.000000', controller)
        graph.set_pin(position_constraint, 'bMaintainOffset', 'True', controller)
        graph.set_pin(position_constraint, 'Filter', '(bX=True,bY=True,bZ=True)', controller)
        graph.set_pin(position_constraint, 'Parents', '((Item=(Type=Bone,Name="None"),Weight=1.000000),(Item=(Type=Bone,Name="None"),Weight=1.000000))', controller)
        graph.set_pin(position_constraint, 'Weight', '1.000000', controller)
        graph.set_pin(rotation_constraint, 'bMaintainOffset', 'true', controller)
        graph.set_pin(rotation_constraint, 'Filter', '(bX=True,bY=True,bZ=True)', controller)
        graph.set_pin(rotation_constraint, 'Parents', '((Item=(Type=Bone,Name="None"),Weight=1.000000),(Item=(Type=Bone,Name="None"),Weight=1.000000))', controller)
        graph.set_pin(rotation_constraint, 'AdvancedSettings', '(InterpolationType=Average,RotationOrderForFilter=XZY)', controller)
        graph.set_pin(rotation_constraint, 'Weight', '1.000000', controller)
        graph.set_pin(get_item_metadata, 'Name', 'null', controller)
        graph.set_pin(get_item_metadata, 'NameSpace', 'Self', controller)
        graph.set_pin(get_item_metadata, 'Default', '(Type=Bone,Name="None")', controller)
        graph.set_pin(get_item_metadata1, 'Name', 'null', controller)
        graph.set_pin(get_item_metadata1, 'NameSpace', 'Self', controller)
        graph.set_pin(get_item_metadata1, 'Default', '(Type=Bone,Name="None")', controller)
        graph.set_pin(get_children, 'bIncludeParent', 'False', controller)
        graph.set_pin(get_children, 'bRecursive', 'False', controller)
        graph.set_pin(get_children, 'bDefaultChildren', 'True', controller)
        graph.set_pin(get_children, 'TypeToSearch', 'All', controller)
        graph.set_pin(set_transform, 'Space', 'GlobalSpace', controller)
        graph.set_pin(set_transform, 'bInitial', 'False', controller)
        graph.set_pin(set_transform, 'Weight', '1.000000', controller)
        graph.set_pin(set_transform, 'bPropagateToChildren', 'True', controller)
        graph.set_pin(project_to_new_parent, 'bChildInitial', 'True', controller)
        graph.set_pin(project_to_new_parent, 'bOldParentInitial', 'True', controller)
        graph.set_pin(project_to_new_parent, 'bNewParentInitial', 'False', controller)
        graph.set_pin(remove, 'Index', '0', controller)
        graph.set_pin(remove1, 'Index', '-1', controller)
        graph.set_pin(insert, 'Index', '0', controller)
        graph.set_pin(remove2, 'Index', '-1', controller)
        graph.set_pin(aim_constraint, 'bMaintainOffset', 'True', controller)
        graph.set_pin(aim_constraint, 'Filter', '(bX=True,bY=True,bZ=True)', controller)
        graph.set_pin(aim_constraint, 'UpAxis', '(X=0.000000,Y=1.000000,Z=0.000000)', controller)
        graph.set_pin(aim_constraint, 'WorldUp', '(Target=(X=0.000000,Y=1.000000,Z=0.000000),Kind=Location,Space=(Type=None,Name="None"))', controller)
        graph.set_pin(aim_constraint, 'Parents', '((Item=(Type=Bone,Name="None"),Weight=1.000000))', controller)
        graph.set_pin(aim_constraint, 'AdvancedSettings', '(DebugSettings=(bEnabled=False,Scale=10.000000,WorldOffset=(Rotation=(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=1.000000,Y=1.000000,Z=1.000000))),RotationOrderForFilter=XZY)', controller)
        graph.set_pin(aim_constraint, 'Weight', '1.000000', controller)
        graph.set_pin(aim_constraint, 'bIsInitialized', 'False', controller)
        graph.set_pin(aim_constraint1, 'bMaintainOffset', 'True', controller)
        graph.set_pin(aim_constraint1, 'Filter', '(bX=True,bY=True,bZ=True)', controller)
        graph.set_pin(aim_constraint1, 'UpAxis', '(X=0.000000,Y=1.000000,Z=0.000000)', controller)
        graph.set_pin(aim_constraint1, 'WorldUp', '(Target=(X=0.000000,Y=1.000000,Z=0.000000),Kind=Location,Space=(Type=None,Name="None"))', controller)
        graph.set_pin(aim_constraint1, 'Parents', '((Item=(Type=Bone,Name="None"),Weight=1.000000))', controller)
        graph.set_pin(aim_constraint1, 'AdvancedSettings', '(DebugSettings=(bEnabled=False,Scale=10.000000,WorldOffset=(Rotation=(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=1.000000,Y=1.000000,Z=1.000000))),RotationOrderForFilter=XZY)', controller)
        graph.set_pin(aim_constraint1, 'Weight', '1.000000', controller)
        graph.set_pin(aim_constraint1, 'bIsInitialized', 'False', controller)
        graph.set_pin(greater1, 'B', '0', controller)

        current_locals = locals()
        nodes = unreal_lib.graph.filter_nodes(current_locals.values())
        node = unreal_lib.graph.comment_nodes(nodes, controller, 'Forward Solve')
        nodes.append(node)
        unreal_lib.graph.move_nodes(500, 0, nodes, controller)


class UnrealAimMultiAtCurveRig(UnrealUtilRig):

    def _build_function_construct_graph(self):

        controller = self.function_controller
        library = self.library

        controller.add_local_variable_from_object_path('last_control', 'FRigElementKey', '/Script/ControlRig.RigElementKey', '')
        # controller.add_local_variable_from_object_path('local_controls', 'TArray<FRigElementKey>','/Script/ControlRig.RigElementKey', '')
        controller.add_local_variable_from_object_path('aims', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', '')
        controller.add_local_variable_from_object_path('fk_items', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', '')
        controller.add_local_variable_from_object_path('fk_controls', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', '')
        controller.add_local_variable_from_object_path('aim_controls', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', '')

        get_joints = controller.add_variable_node_from_object_path('joints', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(845.4417724609375, -2215.94482421875), 'Get joints')
        num = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetNum(in Array,out Num)', unreal.Vector2D(1008.0, -2224.0), 'Num')
        greater = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathIntGreater', 'Execute', unreal.Vector2D(1216.0, -2240.0), 'Greater')
        branch = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_ControlFlowBranch', 'Execute', unreal.Vector2D(1424.0, -2336.0), 'Branch')
        vetala_lib_get_tops = controller.add_function_reference_node(library.find_function('vetalaLib_GetTops'), unreal.Vector2D(1680.0, -2496.0), 'vetalaLib_GetTops')
        spline_from_items = controller.add_external_function_reference_node('/ControlRigSpline/SplineFunctionLibrary/SplineFunctionLibrary.SplineFunctionLibrary_C', 'SplineFromItems', unreal.Vector2D(3328.0, -2608.0), 'SplineFromItems')
        add = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayAdd(io Array,in Element,out Index)', unreal.Vector2D(6000.0, -2112.0), 'Add')
        draw_spline = controller.add_unit_node_from_struct_path('/Script/ControlRigSpline.RigUnit_DrawControlRigSpline', 'Execute', unreal.Vector2D(3936.0, -2432.0), 'Draw Spline')
        add1 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayAdd(io Array,in Element,out Index)', unreal.Vector2D(4512.0, -3408.0), 'Add')
        for_each = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayIterator(in Array,out Element,out Index,out Count,out Ratio)', unreal.Vector2D(3040.0, -3344.0), 'For Each')
        get_transform = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetTransform', 'Execute', unreal.Vector2D(3232.0, -3072.0), 'Get Transform')
        transform_location = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathTransformTransformVector', 'Execute', unreal.Vector2D(3776.0, -3120.0), 'Transform Location')
        multiply = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathVectorMul', 'Execute', unreal.Vector2D(3600.0, -2928.0), 'Multiply')
        get_local_controls = controller.add_variable_node_from_object_path('local_controls', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(5856.0, -2416.0), 'Get local_controls')
        get_aims = controller.add_variable_node_from_object_path('aims', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(4352.0, -3632.0), 'Get aims')
        spawn_null = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyAddNull', 'Execute', unreal.Vector2D(4128.0, -3392.0), 'Spawn Null')
        vetala_lib_find_bone_aim_axis = controller.add_function_reference_node(library.find_function('vetalaLib_findBoneAimAxis'), unreal.Vector2D(3424.0, -3344.0), 'vetalaLib_findBoneAimAxis')
        for_loop = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_ForLoopCount', 'Execute', unreal.Vector2D(4144.0, -2432.0), 'For Loop')
        position_from_spline = controller.add_unit_node_from_struct_path('/Script/ControlRigSpline.RigUnit_PositionFromControlRigSpline', 'Execute', unreal.Vector2D(4624.0, -2448.0), 'Position From Spline')
        get_aims1 = controller.add_variable_node_from_object_path('aims', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(3008.0, -2464.0), 'Get aims')
        reset = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayReset(io Array)', unreal.Vector2D(2000.0, -2288.0), 'Reset')
        get_aims2 = controller.add_variable_node_from_object_path('aims', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(1867.252685546875, -2091.15185546875), 'Get aims')
        vetala_lib_control = self._create_control(controller, 5440.0, -2112.0)
        spawn_null1 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyAddNull', 'Execute', unreal.Vector2D(4992.0, -2048.0), 'Spawn Null')
        get_parent = controller.add_variable_node_from_object_path('parent', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(2784.0, -2240.0), 'Get parent')
        vetala_lib_get_item = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(2960.0, -2208.0), 'vetalaLib_GetItem')
        set_default_parent = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_SetDefaultParent', 'Execute', unreal.Vector2D(5696.0, -2256.0), 'Set Default Parent')
        get_children = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_CollectionChildrenArray', 'Execute', unreal.Vector2D(5392.0, -3552.0), 'Get Children')
        num1 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetNum(in Array,out Num)', unreal.Vector2D(5744.0, -3552.0), 'Num')
        make_array = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayMake(in Values,out Array)', unreal.Vector2D(5760.0, -3168.0), 'Make Array')
        greater1 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathIntGreater', 'Execute', unreal.Vector2D(5968.0, -3552.0), 'Greater')
        branch1 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_ControlFlowBranch', 'Execute', unreal.Vector2D(6384.0, -3120.0), 'Branch')
        for_each1 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayIterator(in Array,out Element,out Index,out Count,out Ratio)', unreal.Vector2D(6624.0, -3088.0), 'For Each')
        find = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayFind(in Array,in Element,out Index,out Success)', unreal.Vector2D(6944.0, -3072.0), 'Find')
        get_joints1 = controller.add_variable_node_from_object_path('joints', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(6672.0, -3232.0), 'Get joints')
        branch2 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_ControlFlowBranch', 'Execute', unreal.Vector2D(7120.0, -3296.0), 'Branch')
        add2 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayAdd(io Array,in Element,out Index)', unreal.Vector2D(7472.0, -3440.0), 'Add')
        vetala_lib_control1 = self._create_control(controller, 7760.0, -2176.0)
        for_each2 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayIterator(in Array,out Element,out Index,out Count,out Ratio)', unreal.Vector2D(6992.0, -2608.0), 'For Each')
        get_parent1 = controller.add_variable_node_from_object_path('parent', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(6528.0, -2080.0), 'Get parent')
        vetala_lib_get_item1 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(6704.0, -2096.0), 'vetalaLib_GetItem')
        set_fk_items = controller.add_variable_node_from_object_path('fk_items', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', False, '()', unreal.Vector2D(6080.0, -3088.0), 'Set fk_items')
        get_fk_items = controller.add_variable_node_from_object_path('fk_items', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(5344.0, -2944.0), 'Get fk_items')
        reset1 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayReset(io Array)', unreal.Vector2D(5520.0, -2944.0), 'Reset')
        get_fk_items1 = controller.add_variable_node_from_object_path('fk_items', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(7184.0, -3520.0), 'Get fk_items')
        get_fk_items2 = controller.add_variable_node_from_object_path('fk_items', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(6736.0, -2496.0), 'Get fk_items')
        set_last_control = controller.add_variable_node_from_object_path('last_control', 'FRigElementKey', '/Script/ControlRig.RigElementKey', False, '', unreal.Vector2D(9200.0, -2176.0), 'Set last_control')
        get_last_control = controller.add_variable_node_from_object_path('last_control', 'FRigElementKey', '/Script/ControlRig.RigElementKey', True, '', unreal.Vector2D(6672.0, -2272.0), 'Get last_control')
        if1 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(7168.0, -2128.0), 'If')
        item_exists = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_ItemExists', 'Execute', unreal.Vector2D(6880.0, -2256.0), 'Item Exists')
        set_last_control1 = controller.add_variable_node_from_object_path('last_control', 'FRigElementKey', '/Script/ControlRig.RigElementKey', False, '', unreal.Vector2D(5776.0, -2976.0), 'Set last_control')
        get_transform1 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetTransform', 'Execute', unreal.Vector2D(7568.0, -2768.0), 'Get Transform')
        join = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_StringJoin', 'Execute', unreal.Vector2D(8016.0, -2032.0), 'Join')
        from_string = controller.add_template_node('DISPATCH_RigDispatch_FromString(in String,out Result)', unreal.Vector2D(8112.0, -2176.0), 'From String')
        get_description = controller.add_variable_node('description', 'FString', None, True, '', unreal.Vector2D(7008.0, -1968.0), 'Get description')
        spawn_null2 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyAddNull', 'Execute', unreal.Vector2D(8352.0, -2592.0), 'Spawn Null')
        to_string = controller.add_template_node('DISPATCH_RigDispatch_ToString(in Value,out Result)', unreal.Vector2D(8016.0, -1824.0), 'To String')
        set_default_parent1 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_SetDefaultParent', 'Execute', unreal.Vector2D(8848.0, -2576.0), 'Set Default Parent')
        join1 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_StringJoin', 'Execute', unreal.Vector2D(7216.0, -1968.0), 'Join')
        add3 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathIntAdd', 'Execute', unreal.Vector2D(6816.0, -1856.0), 'Add')
        to_string1 = controller.add_template_node('DISPATCH_RigDispatch_ToString(in Value,out Result)', unreal.Vector2D(7008.0, -1872.0), 'To String')
        set_item_array_metadata = controller.add_template_node('DISPATCH_RigDispatch_SetMetadata(in Item,in Name,in NameSpace,in Value,out Success)', unreal.Vector2D(9872.0, -2528.0), 'Set Item Array Metadata')
        get_fk_controls = controller.add_variable_node_from_object_path('fk_controls', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(8880.0, -1936.0), 'Get fk_controls')
        add4 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayAdd(io Array,in Element,out Index)', unreal.Vector2D(9159.689453125, -1905.9383544921875), 'Add')
        get_fk_controls1 = controller.add_variable_node_from_object_path('fk_controls', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(9632.0, -2352.0), 'Get fk_controls')
        reset2 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayReset(io Array)', unreal.Vector2D(3008.0, -3632.0), 'Reset')
        get_fk_controls2 = controller.add_variable_node_from_object_path('fk_controls', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(2800.0, -3760.0), 'Get fk_controls')
        set_item_metadata = controller.add_template_node('DISPATCH_RigDispatch_SetMetadata(in Item,in Name,in NameSpace,in Value,out Success)', unreal.Vector2D(10448.0, -2528.0), 'Set Item Metadata')
        get_aims3 = controller.add_variable_node_from_object_path('aims', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(10032.0, -2240.0), 'Get aims')
        vetala_lib_get_item2 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(10208.0, -2240.0), 'vetalaLib_GetItem')
        set_item_metadata1 = controller.add_template_node('DISPATCH_RigDispatch_SetMetadata(in Item,in Name,in NameSpace,in Value,out Success)', unreal.Vector2D(9498.6982421875, -1882.626708984375), 'Set Item Metadata')
        get_aim_controls = controller.add_variable_node_from_object_path('aim_controls', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(3296.0, -3744.0), 'Get aim_controls')
        reset3 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayReset(io Array)', unreal.Vector2D(3344.0, -3632.0), 'Reset')
        add5 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayAdd(io Array,in Element,out Index)', unreal.Vector2D(6240.0, -2112.0), 'Add')
        get_aim_controls1 = controller.add_variable_node_from_object_path('aim_controls', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(6064.0, -2416.0), 'Get aim_controls')
        vetala_lib_get_item3 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(3600.0, -1872.0), 'vetalaLib_GetItem')
        set_item_array_metadata1 = controller.add_template_node('DISPATCH_RigDispatch_SetMetadata(in Item,in Name,in NameSpace,in Value,out Success)', unreal.Vector2D(4051.0, -1231.0), 'Set Item Array Metadata')
        get_aim_controls2 = controller.add_variable_node_from_object_path('aim_controls', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(3707.0, -1115.0), 'Get aim_controls')
        set_item_array_metadata2 = controller.add_template_node('DISPATCH_RigDispatch_SetMetadata(in Item,in Name,in NameSpace,in Value,out Success)', unreal.Vector2D(4480.0, -1200.0), 'Set Item Array Metadata')
        get_aims4 = controller.add_variable_node_from_object_path('aims', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(4363.0, -795.0), 'Get aims')
        set_item_metadata2 = controller.add_template_node('DISPATCH_RigDispatch_SetMetadata(in Item,in Name,in NameSpace,in Value,out Success)', unreal.Vector2D(9888.0, -1856.0), 'Set Item Metadata')
        branch3 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_ControlFlowBranch', 'Execute', unreal.Vector2D(5968.0, -1904.0), 'Branch')
        equals = controller.add_template_node('DISPATCH_RigVMDispatch_CoreEquals(in A,in B,out Result)', unreal.Vector2D(4347.955078125, -1908.3536376953125), 'Equals')
        equals1 = controller.add_template_node('DISPATCH_RigVMDispatch_CoreEquals(in A,in B,out Result)', unreal.Vector2D(4336.0, -1792.0), 'Equals')
        or1 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathBoolOr', 'Execute', unreal.Vector2D(4528.0, -1840.0), 'Or')
        spawn_scale_float_animation_channel = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyAddAnimationChannelScaleFloat', 'Execute', unreal.Vector2D(5872.0, -1232.0), 'Spawn Scale Float Animation Channel')
        spawn_scale_float_animation_channel1 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyAddAnimationChannelScaleFloat', 'Execute', unreal.Vector2D(6304.0, -1248.0), 'Spawn Scale Float Animation Channel')
        get_offset = controller.add_variable_node('offset', 'double', None, True, '', unreal.Vector2D(3420.820068359375, -2800.2353515625), 'Get offset')
        if2 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(5002.6025390625, -1628.3251953125), 'If')
        spawn_null3 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyAddNull', 'Execute', unreal.Vector2D(8352.0, -2320.0), 'Spawn Null')
        join2 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_StringJoin', 'Execute', unreal.Vector2D(8272.0, -1856.0), 'Join')
        from_string1 = controller.add_template_node('DISPATCH_RigDispatch_FromString(in String,out Result)', unreal.Vector2D(8368.0, -2000.0), 'From String')
        to_string2 = controller.add_template_node('DISPATCH_RigDispatch_ToString(in Value,out Result)', unreal.Vector2D(8272.0, -1648.0), 'To String')
        set_item_metadata3 = controller.add_template_node('DISPATCH_RigDispatch_SetMetadata(in Item,in Name,in NameSpace,in Value,out Success)', unreal.Vector2D(10304.0, -1856.0), 'Set Item Metadata')
        get_top_parents = controller.add_variable_node_from_object_path('top_parents', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(3960.9765625, -4078.4990234375), 'Get top_parents')
        num2 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetNum(in Array,out Num)', unreal.Vector2D(4136.9765625, -4094.4990234375), 'Num')
        greater2 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathIntGreater', 'Execute', unreal.Vector2D(4369.326171500001, -4039.6675414375), 'Greater')
        spline_from_items1 = controller.add_external_function_reference_node('/ControlRigSpline/SplineFunctionLibrary/SplineFunctionLibrary.SplineFunctionLibrary_C', 'SplineFromItems', unreal.Vector2D(4584.9765625, -4430.4990234375), 'SplineFromItems')
        position_from_spline1 = controller.add_unit_node_from_struct_path('/Script/ControlRigSpline.RigUnit_PositionFromControlRigSpline', 'Execute', unreal.Vector2D(4872.9765625, -4142.4990234375), 'Position From Spline')
        make_transform = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathTransformMake', 'Execute', unreal.Vector2D(5176.9765625, -4158.4990234375), 'Make Transform')
        subtract = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathDoubleSub', 'Execute', unreal.Vector2D(4088.9765625, -3934.4990234375), 'Subtract')
        branch4 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_ControlFlowBranch', 'Execute', unreal.Vector2D(4902.90234375, -3660.42431640625), 'Branch')
        spawn_null4 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyAddNull', 'Execute', unreal.Vector2D(5614.4580078125, -3978.44580078125), 'Spawn Null')
        get_parent2 = controller.add_variable_node_from_object_path('parent', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(5173.7421875, -3923.5078125), 'Get parent')
        vetala_lib_get_item4 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(5349.7421875, -3891.5078125), 'vetalaLib_GetItem')
        set_item_metadata4 = controller.add_template_node('DISPATCH_RigDispatch_SetMetadata(in Item,in Name,in NameSpace,in Value,out Success)', unreal.Vector2D(6400.0, -4080.0), 'Set Item Metadata')
        at = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(4640.0, -3952.0), 'At')

        controller.resolve_wild_card_pin(f'{num.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{greater.get_node_path()}.A', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{greater.get_node_path()}.B', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{add.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{add1.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{for_each.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{reset.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{num1.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{make_array.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{greater1.get_node_path()}.A', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{greater1.get_node_path()}.B', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{for_each1.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{add2.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{for_each2.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{reset1.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{if1.get_node_path()}.Result', 'FRigElementKey', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{add3.get_node_path()}.Result', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{add4.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{reset2.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{reset3.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{add5.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{equals.get_node_path()}.A', 'double', 'None')
        controller.resolve_wild_card_pin(f'{equals.get_node_path()}.B', 'double', 'None')
        controller.resolve_wild_card_pin(f'{equals1.get_node_path()}.A', 'double', 'None')
        controller.resolve_wild_card_pin(f'{equals1.get_node_path()}.B', 'double', 'None')
        controller.resolve_wild_card_pin(f'{if2.get_node_path()}.Result', 'float', 'None')
        controller.resolve_wild_card_pin(f'{num2.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{greater2.get_node_path()}.A', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{greater2.get_node_path()}.B', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{at.get_node_path()}.Array', 'TArray<FTransform>', '/Script/CoreUObject.Transform')

        controller.set_array_pin_size(f'{n(make_array)}.Values', 1)
        controller.set_array_pin_size(f'{n(join)}.Values', 2)
        controller.set_array_pin_size(f'{n(join1)}.Values', 2)
        controller.set_array_pin_size(f'{n(join2)}.Values', 2)

        graph.add_link('DISPATCH_RigVMDispatch_SwitchInt32', 'Cases.0', branch, 'ExecuteContext', controller)
        graph.add_link(branch, 'True', vetala_lib_get_tops, 'ExecuteContext', controller)
        graph.add_link(vetala_lib_get_tops, 'ExecuteContext', reset, 'ExecuteContext', controller)
        graph.add_link(for_each, 'Completed', spline_from_items, 'ExecuteContext', controller)
        graph.add_link(spline_from_items, 'ExecuteContext', draw_spline, 'ExecutePin', controller)
        graph.add_link(set_default_parent, 'ExecutePin', add, 'ExecuteContext', controller)
        graph.add_link(add, 'ExecuteContext', add5, 'ExecuteContext', controller)
        graph.add_link(spawn_null, 'ExecutePin', add1, 'ExecuteContext', controller)
        graph.add_link(add1, 'ExecuteContext', branch4, 'ExecuteContext', controller)
        graph.add_link(reset, 'ExecuteContext', for_each, 'ExecuteContext', controller)
        graph.add_link(for_each, 'ExecuteContext', reset2, 'ExecuteContext', controller)
        graph.add_link(vetala_lib_find_bone_aim_axis, 'ExecuteContext', spawn_null, 'ExecutePin', controller)
        graph.add_link(reset3, 'ExecuteContext', vetala_lib_find_bone_aim_axis, 'ExecuteContext', controller)
        graph.add_link(for_loop, 'Completed', set_item_array_metadata1, 'ExecuteContext', controller)
        graph.add_link(spawn_null1, 'ExecutePin', vetala_lib_control, 'ExecuteContext', controller)
        graph.add_link(vetala_lib_control, 'ExecuteContext', set_default_parent, 'ExecutePin', controller)
        graph.add_link(set_fk_items, 'ExecuteContext', branch1, 'ExecuteContext', controller)
        graph.add_link(branch1, 'True', for_each1, 'ExecuteContext', controller)
        graph.add_link(for_each1, 'ExecuteContext', branch2, 'ExecuteContext', controller)
        graph.add_link(for_each1, 'Completed', for_each2, 'ExecuteContext', controller)
        graph.add_link(branch2, 'True', add2, 'ExecuteContext', controller)
        graph.add_link(for_each2, 'ExecuteContext', vetala_lib_control1, 'ExecuteContext', controller)
        graph.add_link(vetala_lib_control1, 'ExecuteContext', spawn_null2, 'ExecutePin', controller)
        graph.add_link(for_each2, 'Completed', set_item_array_metadata, 'ExecuteContext', controller)
        graph.add_link(set_last_control1, 'ExecuteContext', set_fk_items, 'ExecuteContext', controller)
        graph.add_link(branch4, 'Completed', reset1, 'ExecuteContext', controller)
        graph.add_link(reset1, 'ExecuteContext', set_last_control1, 'ExecuteContext', controller)
        graph.add_link(spawn_null3, 'ExecutePin', set_last_control, 'ExecuteContext', controller)
        graph.add_link(set_last_control, 'ExecuteContext', add4, 'ExecuteContext', controller)
        graph.add_link(set_item_array_metadata, 'ExecuteContext', set_item_metadata, 'ExecuteContext', controller)
        graph.add_link(add4, 'ExecuteContext', set_item_metadata1, 'ExecuteContext', controller)
        graph.add_link(reset2, 'ExecuteContext', reset3, 'ExecuteContext', controller)
        graph.add_link(set_item_metadata1, 'ExecuteContext', set_item_metadata2, 'ExecuteContext', controller)
        graph.add_link(add5, 'ExecuteContext', branch3, 'ExecuteContext', controller)
        graph.add_link(set_item_array_metadata1, 'ExecuteContext', set_item_array_metadata2, 'ExecuteContext', controller)
        graph.add_link(set_item_metadata2, 'ExecuteContext', set_item_metadata3, 'ExecuteContext', controller)
        graph.add_link(branch4, 'True', spline_from_items1, 'ExecuteContext', controller)
        graph.add_link(spline_from_items1, 'ExecuteContext', spawn_null4, 'ExecutePin', controller)
        graph.add_link(spawn_null4, 'ExecutePin', set_item_metadata4, 'ExecuteContext', controller)
        graph.add_link(get_joints, 'Value', num, 'Array', controller)
        graph.add_link(get_joints, 'Value', vetala_lib_get_tops, 'bones', controller)
        graph.add_link(num, 'Num', 'Greater', 'A', controller)
        graph.add_link(num, 'Num', greater, 'A', controller)
        graph.add_link(greater, 'Result', branch, 'Condition', controller)
        graph.add_link(vetala_lib_get_tops, 'top_bones', for_each, 'Array', controller)
        graph.add_link(vetala_lib_get_tops, 'top_bones', vetala_lib_get_item3, 'Array', controller)
        graph.add_link(get_aims1, 'Value', spline_from_items, 'Items', controller)
        graph.add_link(spline_from_items, 'Spline', draw_spline, 'Spline', controller)
        graph.add_link(spline_from_items, 'Spline', position_from_spline, 'Spline', controller)
        graph.add_link(get_local_controls, 'Value', add, 'Array', controller)
        graph.add_link(vetala_lib_control, 'Control', add, 'Element', controller)
        graph.add_link(draw_spline, 'ExecutePin', for_loop, 'ExecutePin', controller)
        graph.add_link(get_aims, 'Value', add1, 'Array', controller)
        graph.add_link(spawn_null, 'Item', add1, 'Element', controller)
        graph.add_link(for_each, 'Element', get_transform, 'Item', controller)
        graph.add_link(for_each, 'Element', vetala_lib_find_bone_aim_axis, 'Bone', controller)
        graph.add_link(for_each, 'Element', get_children, 'Parent', controller)
        graph.add_link(for_each, 'Element', set_item_array_metadata, 'Item', controller)
        graph.add_link(for_each, 'Element', set_item_metadata, 'Item', controller)
        graph.add_link(for_each, 'Element', set_item_metadata4, 'Item', controller)
        graph.add_link(for_each, 'Index', add3, 'A', controller)
        graph.add_link(for_each, 'Ratio', subtract, 'B', controller)
        graph.add_link(get_transform, 'Transform', transform_location, 'Transform', controller)
        graph.add_link(multiply, 'Result', transform_location, 'Location', controller)
        graph.add_link(vetala_lib_find_bone_aim_axis, 'Result', multiply, 'A', controller)
        graph.add_link(vetala_lib_get_item, 'Element', spawn_null, 'Parent', controller)
        graph.add_link(for_loop, 'ExecutePin', spawn_null1, 'ExecutePin', controller)
        graph.add_link(for_loop, 'Ratio', position_from_spline, 'U', controller)
        graph.add_link(for_loop, 'Ratio', equals, 'A', controller)
        graph.add_link(for_loop, 'Ratio', equals1, 'A', controller)
        graph.add_link(get_aims2, 'Value', reset, 'Array', controller)
        graph.add_link(vetala_lib_get_item, 'Element', vetala_lib_control, 'parent', controller)
        graph.add_link(spawn_null1, 'Item', vetala_lib_control, 'driven', controller)
        graph.add_link('Entry', 'description', vetala_lib_control, 'description', controller)
        graph.add_link('Entry', 'side', vetala_lib_control, 'side', controller)
        graph.add_link('Entry', 'joint_token', vetala_lib_control, 'joint_token', controller)
        graph.add_link('Entry', 'restrain_numbering', vetala_lib_control, 'restrain_numbering', controller)
        graph.add_link('Entry', 'shape', vetala_lib_control, 'shape', controller)
        graph.add_link('Entry', 'color', vetala_lib_control, 'color', controller)
        graph.add_link('Entry', 'sub_color', vetala_lib_control, 'sub_color', controller)
        graph.add_link('Entry', 'shape_translate', vetala_lib_control, 'translate', controller)
        graph.add_link('Entry', 'shape_rotate', vetala_lib_control, 'rotate', controller)
        graph.add_link('Entry', 'shape_scale', vetala_lib_control, 'scale', controller)
        graph.add_link(if2, 'Result', vetala_lib_control, 'scale_offset', controller)
        graph.add_link(vetala_lib_control, 'Control', set_default_parent, 'Parent', controller)
        graph.add_link(vetala_lib_control, 'Control', spawn_scale_float_animation_channel, 'Parent', controller)
        graph.add_link(vetala_lib_control, 'Control', spawn_scale_float_animation_channel1, 'Parent', controller)
        graph.add_link(vetala_lib_control, 'Control', add5, 'Element', controller)
        graph.add_link(spawn_null1, 'Item', set_default_parent, 'Child', controller)
        graph.add_link(get_parent, 'Value', vetala_lib_get_item, 'Array', controller)
        graph.add_link(get_children, 'Items', num1, 'Array', controller)
        graph.add_link(get_children, 'Items', for_each1, 'Array', controller)
        graph.add_link(num1, 'Num', 'Greater_1', 'A', controller)
        graph.add_link(make_array, 'Array', set_fk_items, 'Value', controller)
        graph.add_link('Num_1', 'Num', greater1, 'A', controller)
        graph.add_link(greater1, 'Result', branch1, 'Condition', controller)
        graph.add_link(for_each1, 'Element', find, 'Element', controller)
        graph.add_link(for_each1, 'Element', add2, 'Element', controller)
        graph.add_link(get_joints1, 'Value', find, 'Array', controller)
        graph.add_link(find, 'Success', branch2, 'Condition', controller)
        graph.add_link(get_fk_items1, 'Value', add2, 'Array', controller)
        graph.add_link(for_each2, 'Index', vetala_lib_control1, 'increment', controller)
        graph.add_link(if1, 'Result', vetala_lib_control1, 'parent', controller)
        graph.add_link(for_each2, 'Element', vetala_lib_control1, 'driven', controller)
        graph.add_link(join1, 'Result', vetala_lib_control1, 'description', controller)
        graph.add_link('Entry', 'side', vetala_lib_control1, 'side', controller)
        graph.add_link('Entry', 'joint_token', vetala_lib_control1, 'joint_token', controller)
        graph.add_link('Entry', 'restrain_numbering', vetala_lib_control1, 'restrain_numbering', controller)
        graph.add_link('Entry', 'shape', vetala_lib_control1, 'shape', controller)
        graph.add_link('Entry', 'color', vetala_lib_control1, 'color', controller)
        graph.add_link('Entry', 'sub_color', vetala_lib_control1, 'sub_color', controller)
        graph.add_link('Entry', 'shape_translate', vetala_lib_control1, 'translate', controller)
        graph.add_link('Entry', 'shape_rotate', vetala_lib_control1, 'rotate', controller)
        graph.add_link('Entry', 'shape_scale', vetala_lib_control1, 'scale', controller)
        graph.add_link(vetala_lib_control1, 'Control', set_last_control, 'Value', controller)
        graph.add_link(vetala_lib_control1, 'Control', set_default_parent1, 'Child', controller)
        graph.add_link(vetala_lib_control1, 'Control', add4, 'Element', controller)
        graph.add_link(vetala_lib_control1, 'Control', set_item_metadata1, 'Item', controller)
        graph.add_link(vetala_lib_control1, 'Control', set_item_metadata2, 'Item', controller)
        graph.add_link(vetala_lib_control1, 'Control', set_item_metadata3, 'Item', controller)
        graph.add_link(vetala_lib_control1, 'Control.Name', to_string, 'Value', controller)
        graph.add_link(vetala_lib_control1, 'Control.Name', to_string2, 'Value', controller)
        graph.add_link(get_fk_items2, 'Value', for_each2, 'Array', controller)
        graph.add_link(for_each2, 'Element', get_transform1, 'Item', controller)
        graph.add_link(for_each2, 'Element', set_item_metadata2, 'Value', controller)
        graph.add_link(get_parent1, 'Value', vetala_lib_get_item1, 'Array', controller)
        graph.add_link(vetala_lib_get_item1, 'Element', if1, 'False', controller)
        graph.add_link(get_fk_items, 'Value', reset1, 'Array', controller)
        graph.add_link(get_last_control, 'Value', item_exists, 'Item', controller)
        graph.add_link(get_last_control, 'Value', if1, 'True', controller)
        graph.add_link(item_exists, 'Exists', if1, 'Condition', controller)
        graph.add_link(if1, 'Result', spawn_null2, 'Parent', controller)
        graph.add_link(if1, 'Result', spawn_null3, 'Parent', controller)
        graph.add_link(get_transform1, 'Transform', spawn_null2, 'Transform', controller)
        graph.add_link(get_transform1, 'Transform', spawn_null3, 'Transform', controller)
        graph.add_link(join, 'Result', from_string, 'String', controller)
        graph.add_link(from_string, 'Result', spawn_null2, 'Name', controller)
        graph.add_link(spawn_null2, 'ExecutePin', set_default_parent1, 'ExecutePin', controller)
        graph.add_link(spawn_null2, 'Item', set_default_parent1, 'Parent', controller)
        graph.add_link(spawn_null2, 'Item', set_item_metadata1, 'Value', controller)
        graph.add_link(set_default_parent1, 'ExecutePin', spawn_null3, 'ExecutePin', controller)
        graph.add_link(add3, 'Result', to_string1, 'Value', controller)
        graph.add_link(get_fk_controls1, 'Value', set_item_array_metadata, 'Value', controller)
        graph.add_link(get_fk_controls, 'Value', add4, 'Array', controller)
        graph.add_link(get_fk_controls2, 'Value', reset2, 'Array', controller)
        graph.add_link(vetala_lib_get_item2, 'Element', set_item_metadata, 'Value', controller)
        graph.add_link(get_aims3, 'Value', vetala_lib_get_item2, 'Array', controller)
        graph.add_link(get_aim_controls, 'Value', reset3, 'Array', controller)
        graph.add_link(get_aim_controls1, 'Value', add5, 'Array', controller)
        graph.add_link(vetala_lib_get_item3, 'Element', set_item_array_metadata1, 'Item', controller)
        graph.add_link(vetala_lib_get_item3, 'Element', set_item_array_metadata2, 'Item', controller)
        graph.add_link(get_aim_controls2, 'Value', set_item_array_metadata1, 'Value', controller)
        graph.add_link(get_aims4, 'Value', set_item_array_metadata2, 'Value', controller)
        graph.add_link(or1, 'Result', branch3, 'Condition', controller)
        graph.add_link(branch3, 'True', spawn_scale_float_animation_channel, 'ExecutePin', controller)
        graph.add_link(equals, 'Result', or1, 'A', controller)
        graph.add_link(equals1, 'Result', or1, 'B', controller)
        graph.add_link(or1, 'Result', if2, 'Condition', controller)
        graph.add_link(spawn_scale_float_animation_channel, 'ExecutePin', spawn_scale_float_animation_channel1, 'ExecutePin', controller)
        graph.add_link(from_string1, 'Result', spawn_null3, 'Name', controller)
        graph.add_link(spawn_null3, 'Item', set_item_metadata3, 'Value', controller)
        graph.add_link(join2, 'Result', from_string1, 'String', controller)
        graph.add_link(get_top_parents, 'Value', num2, 'Array', controller)
        graph.add_link(get_top_parents, 'Value', spline_from_items1, 'Items', controller)
        graph.add_link(num2, 'Num', 'Greater_5', 'A', controller)
        graph.add_link('Num_4', 'Num', greater2, 'A', controller)
        graph.add_link(greater2, 'Result', branch4, 'Condition', controller)
        graph.add_link(spline_from_items1, 'Spline', position_from_spline1, 'Spline', controller)
        graph.add_link(spline_from_items1, 'Transforms', at, 'Array', controller)
        graph.add_link(subtract, 'Result', position_from_spline1, 'U', controller)
        graph.add_link(position_from_spline1, 'Position', make_transform, 'Translation', controller)
        graph.add_link(at, 'Element.Rotation', make_transform, 'Rotation', controller)
        graph.add_link(make_transform, 'Result', spawn_null4, 'Transform', controller)
        graph.add_link(vetala_lib_get_item4, 'Element', spawn_null4, 'Parent', controller)
        graph.add_link(spawn_null4, 'Item', set_item_metadata4, 'Value', controller)
        graph.add_link(get_parent2, 'Value', vetala_lib_get_item4, 'Array', controller)
        graph.add_link(for_each, 'Element', make_array, 'Values.0', controller)
        graph.add_link(transform_location, 'Result', spawn_null, 'Transform.Translation', controller)
        graph.add_link(get_offset, 'Value', multiply, 'B.X', controller)
        graph.add_link(get_offset, 'Value', multiply, 'B.Y', controller)
        graph.add_link(get_offset, 'Value', multiply, 'B.Z', controller)
        graph.add_link(position_from_spline, 'Position', spawn_null1, 'Transform.Translation', controller)
        graph.add_link(to_string, 'Result', join, 'Values.1', controller)
        graph.add_link(get_description, 'Value', join1, 'Values.0', controller)
        graph.add_link(to_string1, 'Result', join1, 'Values.1', controller)
        graph.add_link(to_string2, 'Result', join2, 'Values.1', controller)

        graph.set_pin(greater, 'B', '0', controller)
        graph.set_pin(spline_from_items, 'Spline Mode', 'BSpline', controller)
        graph.set_pin(spline_from_items, 'Samples Per Segment', '16', controller)
        graph.set_pin(draw_spline, 'Color', '(R=1.000000,G=0.000000,B=0.000000,A=1.000000)', controller)
        graph.set_pin(draw_spline, 'Thickness', '0.100000', controller)
        graph.set_pin(draw_spline, 'Detail', '16', controller)
        graph.set_pin(get_transform, 'Space', 'GlobalSpace', controller)
        graph.set_pin(get_transform, 'bInitial', 'False', controller)
        graph.set_pin(multiply, 'B', '(X=8.000000,Y=8.000000,Z=8.000000)', controller)
        graph.set_pin(spawn_null, 'Name', 'aim', controller)
        graph.set_pin(spawn_null, 'Transform', '(Rotation=(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=1.000000,Y=1.000000,Z=1.000000))', controller)
        graph.set_pin(spawn_null, 'Space', 'GlobalSpace', controller)
        graph.set_pin(for_loop, 'Count', '4', controller)
        graph.set_pin(vetala_lib_control, 'increment', '0', controller)
        graph.set_pin(vetala_lib_control, 'sub_count', '0', controller)
        graph.set_pin(spawn_null1, 'Parent', '(Type=Bone,Name="None")', controller)
        graph.set_pin(spawn_null1, 'Name', 'aim_null', controller)
        graph.set_pin(spawn_null1, 'Transform', '(Rotation=(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=1.000000,Y=1.000000,Z=1.000000))', controller)
        graph.set_pin(spawn_null1, 'Space', 'GlobalSpace', controller)
        graph.set_pin(vetala_lib_get_item, 'index', '-1', controller)
        graph.set_pin(get_children, 'bIncludeParent', 'False', controller)
        graph.set_pin(get_children, 'bRecursive', 'true', controller)
        graph.set_pin(get_children, 'bDefaultChildren', 'True', controller)
        graph.set_pin(get_children, 'TypeToSearch', 'Bone', controller)
        graph.set_pin(make_array, 'Values', '((Type=None,Name="None"))', controller)
        graph.set_pin(greater1, 'B', '0', controller)
        graph.set_pin(vetala_lib_control1, 'sub_count', '0', controller)
        graph.set_pin(vetala_lib_control1, 'scale_offset', '1', controller)
        graph.set_pin(vetala_lib_get_item1, 'index', '-1', controller)
        graph.set_pin(get_transform1, 'Space', 'GlobalSpace', controller)
        graph.set_pin(get_transform1, 'bInitial', 'False', controller)
        graph.set_pin(join, 'Values', '("offset","")', controller)
        graph.set_pin(join, 'Separator', '_', controller)
        graph.set_pin(spawn_null2, 'Space', 'GlobalSpace', controller)
        graph.set_pin(join1, 'Values', '("","")', controller)
        graph.set_pin(join1, 'Separator', '_', controller)
        graph.set_pin(add3, 'B', '1', controller)
        graph.set_pin(set_item_array_metadata, 'Name', 'fk_controls', controller)
        graph.set_pin(set_item_array_metadata, 'NameSpace', 'Self', controller)
        graph.set_pin(set_item_metadata, 'Name', 'aim', controller)
        graph.set_pin(set_item_metadata, 'NameSpace', 'Self', controller)
        graph.set_pin(vetala_lib_get_item2, 'index', '-1', controller)
        graph.set_pin(set_item_metadata1, 'Name', 'offset', controller)
        graph.set_pin(set_item_metadata1, 'NameSpace', 'Self', controller)
        graph.set_pin(set_item_array_metadata1, 'Name', 'aim_controls', controller)
        graph.set_pin(set_item_array_metadata1, 'NameSpace', 'Self', controller)
        graph.set_pin(set_item_array_metadata2, 'Name', 'aims', controller)
        graph.set_pin(set_item_array_metadata2, 'NameSpace', 'Self', controller)
        graph.set_pin(set_item_metadata2, 'Name', 'bone', controller)
        graph.set_pin(set_item_metadata2, 'NameSpace', 'Self', controller)
        graph.set_pin(equals, 'B', '0.000000', controller)
        graph.set_pin(equals1, 'B', '1.000000', controller)
        graph.set_pin(spawn_scale_float_animation_channel, 'Name', 'curl', controller)
        graph.set_pin(spawn_scale_float_animation_channel, 'InitialValue', '0.000000', controller)
        graph.set_pin(spawn_scale_float_animation_channel, 'MinimumValue', '-2.000000', controller)
        graph.set_pin(spawn_scale_float_animation_channel, 'MaximumValue', '2.000000', controller)
        graph.set_pin(spawn_scale_float_animation_channel, 'LimitsEnabled', '(Enabled=(bMinimum=True,bMaximum=True))', controller)
        graph.set_pin(spawn_scale_float_animation_channel1, 'Name', 'twist', controller)
        graph.set_pin(spawn_scale_float_animation_channel1, 'InitialValue', '0.000000', controller)
        graph.set_pin(spawn_scale_float_animation_channel1, 'MinimumValue', '-2.000000', controller)
        graph.set_pin(spawn_scale_float_animation_channel1, 'MaximumValue', '2.000000', controller)
        graph.set_pin(spawn_scale_float_animation_channel1, 'LimitsEnabled', '(Enabled=(bMinimum=True,bMaximum=True))', controller)
        graph.set_pin(if2, 'True', '1.500000', controller)
        graph.set_pin(if2, 'False', '1.000000', controller)
        graph.set_pin(spawn_null3, 'Space', 'GlobalSpace', controller)
        graph.set_pin(join2, 'Values', '("up","")', controller)
        graph.set_pin(join2, 'Separator', '_', controller)
        graph.set_pin(set_item_metadata3, 'Name', 'up', controller)
        graph.set_pin(set_item_metadata3, 'NameSpace', 'Self', controller)
        graph.set_pin(greater2, 'B', '0', controller)
        graph.set_pin(spline_from_items1, 'Spline Mode', 'Hermite', controller)
        graph.set_pin(spline_from_items1, 'Samples Per Segment', '16', controller)
        graph.set_pin(make_transform, 'Scale', '(X=1.000000,Y=1.000000,Z=1.000000)', controller)
        graph.set_pin(subtract, 'A', '1.000000', controller)
        graph.set_pin(spawn_null4, 'Name', 'parent_null', controller)
        graph.set_pin(spawn_null4, 'Space', 'GlobalSpace', controller)
        graph.set_pin(vetala_lib_get_item4, 'index', '-1', controller)
        graph.set_pin(set_item_metadata4, 'Name', 'parent_null', controller)
        graph.set_pin(set_item_metadata4, 'NameSpace', 'Self', controller)
        graph.set_pin(at, 'Index', '0', controller)

        current_locals = locals()
        nodes = unreal_lib.graph.filter_nodes(current_locals.values())
        node = unreal_lib.graph.comment_nodes(nodes, controller, 'Construction')
        nodes.append(node)
        unreal_lib.graph.move_nodes(500, -4000, nodes, controller)

    def _build_function_forward_graph(self):

        controller = self.function_controller
        library = self.library

        controller.add_local_variable_from_object_path('invert_2nd_curl', 'bool', '', '')

        get_joints = controller.add_variable_node_from_object_path('joints', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(557.0, 1464.0), 'Get joints')
        num = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetNum(in Array,out Num)', unreal.Vector2D(688.0, 2320.0), 'Num')
        greater = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathIntGreater', 'Execute', unreal.Vector2D(896.0, 2304.0), 'Greater')
        branch = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_ControlFlowBranch', 'Execute', unreal.Vector2D(1104.0, 2208.0), 'Branch')
        vetala_lib_get_tops = controller.add_function_reference_node(library.find_function('vetalaLib_GetTops'), unreal.Vector2D(1360.0, 2048.0), 'vetalaLib_GetTops')
        reset = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayReset(io Array)', unreal.Vector2D(1680.0, 2256.0), 'Reset')
        get_aims = controller.add_variable_node_from_object_path('aims', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(1547.0, 2453.0), 'Get aims')
        for_each = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayIterator(in Array,out Element,out Index,out Count,out Ratio)', unreal.Vector2D(3024.0, 2048.0), 'For Each')
        get_item_metadata = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(3472.0, 2336.0), 'Get Item Metadata')
        vetala_lib_find_bone_aim_axis = controller.add_function_reference_node(library.find_function('vetalaLib_findBoneAimAxis'), unreal.Vector2D(3456.0, 2112.0), 'vetalaLib_findBoneAimAxis')
        branch1 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_ControlFlowBranch', 'Execute', unreal.Vector2D(3792.0, 2048.0), 'Branch')
        get_item_array_metadata = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(3472.0, 2576.0), 'Get Item Array Metadata')
        and1 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathBoolAnd', 'Execute', unreal.Vector2D(3872.0, 2448.0), 'And')
        aim_constraint = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_AimConstraintLocalSpaceOffset', 'Execute', unreal.Vector2D(5376.0, 2032.0), 'Aim Constraint')
        get_item_metadata1 = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(4240.0, 2544.0), 'Get Item Metadata')
        get_item_array_metadata1 = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(1456.0, 2560.0), 'Get Item Array Metadata')
        vetala_lib_get_item = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(1344.0, 2336.0), 'vetalaLib_GetItem')
        branch2 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_ControlFlowBranch', 'Execute', unreal.Vector2D(1824.0, 1632.0), 'Branch')
        spline_from_items = controller.add_external_function_reference_node('/ControlRigSpline/SplineFunctionLibrary/SplineFunctionLibrary.SplineFunctionLibrary_C', 'SplineFromItems', unreal.Vector2D(2080.0, 1824.0), 'SplineFromItems')
        draw_spline = controller.add_unit_node_from_struct_path('/Script/ControlRigSpline.RigUnit_DrawControlRigSpline', 'Execute', unreal.Vector2D(2624.0, 1712.0), 'Draw Spline')
        position_from_spline = controller.add_unit_node_from_struct_path('/Script/ControlRigSpline.RigUnit_PositionFromControlRigSpline', 'Execute', unreal.Vector2D(2192.0, 2848.0), 'Position From Spline')
        get_item_array_metadata2 = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(1456.0, 2816.0), 'Get Item Array Metadata')
        for_each1 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayIterator(in Array,out Element,out Index,out Count,out Ratio)', unreal.Vector2D(2080.0, 2432.0), 'For Each')
        and2 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathBoolAnd', 'Execute', unreal.Vector2D(1744.0, 1920.0), 'And')
        set_transform = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_SetTransform', 'Execute', unreal.Vector2D(2480.0, 2480.0), 'Set Transform')
        make_transform = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathTransformMake', 'Execute', unreal.Vector2D(2464.0, 2832.0), 'Make Transform')
        vetala_lib_get_item1 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(3920.0, 2656.0), 'vetalaLib_GetItem')
        for_each2 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayIterator(in Array,out Element,out Index,out Count,out Ratio)', unreal.Vector2D(5952.0, 2832.0), 'For Each')
        get_item_metadata2 = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(6304.0, 2896.0), 'Get Item Metadata')
        set_transform1 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_SetTransform', 'Execute', unreal.Vector2D(6720.0, 2832.0), 'Set Transform')
        get_transform = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetTransform', 'Execute', unreal.Vector2D(6320.0, 3168.0), 'Get Transform')
        vetala_lib_get_item2 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(2048.0, 3136.0), 'vetalaLib_GetItem')
        multiply = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathDoubleMul', 'Execute', unreal.Vector2D(6176.0, 3984.0), 'Multiply')
        multiply1 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathDoubleMul', 'Execute', unreal.Vector2D(6192.0, 4624.0), 'Multiply')
        greater1 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathIntGreater', 'Execute', unreal.Vector2D(5728.0, 3312.0), 'Greater')
        branch3 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_ControlFlowBranch', 'Execute', unreal.Vector2D(6736.0, 3296.0), 'Branch')
        set_rotation = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_SetRotation', 'Execute', unreal.Vector2D(7280.0, 3696.0), 'Set Rotation')
        from_axis_and_angle = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathQuaternionFromAxisAndAngle', 'Execute', unreal.Vector2D(6464.0, 3856.0), 'From Axis And Angle')
        get_item_metadata3 = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(6368.0, 3440.0), 'Get Item Metadata')
        get_float_channel = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetFloatAnimationChannel', 'Execute', unreal.Vector2D(2752.0, 3072.0), 'Get Float Channel')
        from_string = controller.add_template_node('DISPATCH_RigDispatch_FromString(in String,out Result)', unreal.Vector2D(2528.0, 3184.0), 'From String')
        get_float_channel1 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetFloatAnimationChannel', 'Execute', unreal.Vector2D(2768.0, 4208.0), 'Get Float Channel')
        from_string1 = controller.add_template_node('DISPATCH_RigDispatch_FromString(in String,out Result)', unreal.Vector2D(2544.0, 4320.0), 'From String')
        vetala_lib_get_item3 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(2048.0, 3344.0), 'vetalaLib_GetItem')
        get_float_channel2 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetFloatAnimationChannel', 'Execute', unreal.Vector2D(2736.0, 3344.0), 'Get Float Channel')
        from_string2 = controller.add_template_node('DISPATCH_RigDispatch_FromString(in String,out Result)', unreal.Vector2D(2512.0, 3456.0), 'From String')
        multiply2 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathDoubleMul', 'Execute', unreal.Vector2D(6193.0, 4267.0), 'Multiply')
        subtract = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathDoubleSub', 'Execute', unreal.Vector2D(5664.0, 3920.0), 'Subtract')
        add = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathDoubleAdd', 'Execute', unreal.Vector2D(6383.0, 4154.0), 'Add')
        cross = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathVectorCross', 'Execute', unreal.Vector2D(6208.0, 3744.0), 'Cross')
        get_float_channel3 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetFloatAnimationChannel', 'Execute', unreal.Vector2D(2752.0, 3872.0), 'Get Float Channel')
        from_string3 = controller.add_template_node('DISPATCH_RigDispatch_FromString(in String,out Result)', unreal.Vector2D(2528.0, 3984.0), 'From String')
        multiply3 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathDoubleMul', 'Execute', unreal.Vector2D(6192.0, 4480.0), 'Multiply')
        subtract1 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathDoubleSub', 'Execute', unreal.Vector2D(5696.0, 4464.0), 'Subtract')
        add1 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathDoubleAdd', 'Execute', unreal.Vector2D(6368.0, 4576.0), 'Add')
        from_axis_and_angle1 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathQuaternionFromAxisAndAngle', 'Execute', unreal.Vector2D(6656.0, 4624.0), 'From Axis And Angle')
        multiply4 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathQuaternionMul', 'Execute', unreal.Vector2D(6912.0, 4192.0), 'Multiply')
        get_curl_axis = controller.add_variable_node_from_object_path('curl_axis', 'TArray<FVector>', '/Script/CoreUObject.Vector', True, '()', unreal.Vector2D(5520.0, 3760.0), 'Get curl_axis')
        vetala_lib_get_item_vector = controller.add_function_reference_node(library.find_function('vetalaLib_GetItemVector'), unreal.Vector2D(5712.0, 3760.0), 'vetalaLib_GetItemVector')
        get_top_parents = controller.add_variable_node_from_object_path('top_parents', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(3680.0, 1328.0), 'Get top_parents')
        num1 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetNum(in Array,out Num)', unreal.Vector2D(4096.0, 1456.0), 'Num')
        greater2 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathIntGreater', 'Execute', unreal.Vector2D(4328.0, 1511.0), 'Greater')
        branch4 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_ControlFlowBranch', 'Execute', unreal.Vector2D(4615.0, 1982.0), 'Branch')
        spline_from_items1 = controller.add_external_function_reference_node('/ControlRigSpline/SplineFunctionLibrary/SplineFunctionLibrary.SplineFunctionLibrary_C', 'SplineFromItems', unreal.Vector2D(4544.0, 1120.0), 'SplineFromItems')
        position_from_spline1 = controller.add_unit_node_from_struct_path('/Script/ControlRigSpline.RigUnit_PositionFromControlRigSpline', 'Execute', unreal.Vector2D(5424.0, 912.0), 'Position From Spline')
        make_transform1 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathTransformMake', 'Execute', unreal.Vector2D(5728.0, 896.0), 'Make Transform')
        set_transform2 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_SetTransform', 'Execute', unreal.Vector2D(5744.0, 1104.0), 'Set Transform')
        subtract2 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathDoubleSub', 'Execute', unreal.Vector2D(4048.0, 1616.0), 'Subtract')
        get_item_metadata4 = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(4240.0, 2784.0), 'Get Item Metadata')
        get_item_metadata5 = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(4672.0, 1776.0), 'Get Item Metadata')
        parent_constraint = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_ParentConstraint', 'Execute', unreal.Vector2D(5824.0, 1376.0), 'Parent Constraint')
        interpolate = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathTransformLerp', 'Execute', unreal.Vector2D(5408.0, 1344.0), 'Interpolate')
        at = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(5104.0, 1280.0), 'At')
        at1 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(5104.0, 1424.0), 'At')
        get_invert_2nd_curl = controller.add_variable_node('invert_2nd_curl', 'bool', None, True, '', unreal.Vector2D(5408.0, 4208.0), 'Get invert_2nd_curl')
        if1 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(5600.0, 4208.0), 'If')
        subtract3 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathDoubleSub', 'Execute', unreal.Vector2D(5248.0, 4336.0), 'Subtract')
        multiply5 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathDoubleMul', 'Execute', unreal.Vector2D(5200.0, 4192.0), 'Multiply')
        absolute = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathVectorAbs', 'Execute', unreal.Vector2D(6574.81494140625, 3729.39697265625), 'Absolute')

        controller.resolve_wild_card_pin(f'{num.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{greater.get_node_path()}.A', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{greater.get_node_path()}.B', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{for_each.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{for_each1.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{for_each2.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{greater1.get_node_path()}.A', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{greater1.get_node_path()}.B', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{add.get_node_path()}.Result', 'double', 'None')
        controller.resolve_wild_card_pin(f'{add1.get_node_path()}.Result', 'double', 'None')
        controller.resolve_wild_card_pin(f'{num1.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{greater2.get_node_path()}.A', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{greater2.get_node_path()}.B', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{at.get_node_path()}.Array', 'TArray<FTransform>', '/Script/CoreUObject.Transform')
        controller.resolve_wild_card_pin(f'{at1.get_node_path()}.Array', 'TArray<FTransform>', '/Script/CoreUObject.Transform')
        controller.resolve_wild_card_pin(f'{if1.get_node_path()}.Result', 'float', 'None')

        controller.set_array_pin_size(f'{n(aim_constraint)}.Parents', 1)
        controller.set_array_pin_size(f'{n(parent_constraint)}.Parents', 1)

        graph.add_link('DISPATCH_RigVMDispatch_SwitchInt32', 'Cases.1', branch, 'ExecuteContext', controller)
        graph.add_link(branch, 'True', vetala_lib_get_tops, 'ExecuteContext', controller)
        graph.add_link(vetala_lib_get_tops, 'ExecuteContext', reset, 'ExecuteContext', controller)
        graph.add_link(reset, 'ExecuteContext', branch2, 'ExecuteContext', controller)
        graph.add_link(for_each1, 'Completed', for_each, 'ExecuteContext', controller)
        graph.add_link(for_each, 'ExecuteContext', vetala_lib_find_bone_aim_axis, 'ExecuteContext', controller)
        graph.add_link(vetala_lib_find_bone_aim_axis, 'ExecuteContext', branch1, 'ExecuteContext', controller)
        graph.add_link(branch1, 'True', branch4, 'ExecuteContext', controller)
        graph.add_link(aim_constraint, 'ExecutePin', for_each2, 'ExecuteContext', controller)
        graph.add_link(branch2, 'True', spline_from_items, 'ExecuteContext', controller)
        graph.add_link(spline_from_items, 'ExecuteContext', draw_spline, 'ExecutePin', controller)
        graph.add_link(draw_spline, 'ExecutePin', for_each1, 'ExecuteContext', controller)
        graph.add_link(for_each1, 'ExecuteContext', set_transform, 'ExecutePin', controller)
        graph.add_link(for_each2, 'ExecuteContext', set_transform1, 'ExecutePin', controller)
        graph.add_link(set_transform1, 'ExecutePin', branch3, 'ExecuteContext', controller)
        graph.add_link(branch4, 'True', spline_from_items1, 'ExecuteContext', controller)
        graph.add_link(spline_from_items1, 'ExecuteContext', set_transform2, 'ExecutePin', controller)
        graph.add_link(get_joints, 'Value', num, 'Array', controller)
        graph.add_link(get_joints, 'Value', vetala_lib_get_tops, 'bones', controller)
        graph.add_link(num, 'Num', greater, 'A', controller)
        graph.add_link(greater, 'Result', branch, 'Condition', controller)
        graph.add_link(vetala_lib_get_tops, 'top_bones', for_each, 'Array', controller)
        graph.add_link(vetala_lib_get_tops, 'top_bones', vetala_lib_get_item, 'Array', controller)
        graph.add_link(get_aims, 'Value', reset, 'Array', controller)
        graph.add_link(for_each, 'Element', get_item_metadata, 'Item', controller)
        graph.add_link(for_each, 'Element', vetala_lib_find_bone_aim_axis, 'Bone', controller)
        graph.add_link(for_each, 'Element', get_item_array_metadata, 'Item', controller)
        graph.add_link(for_each, 'Element', get_item_metadata5, 'Item', controller)
        graph.add_link(for_each, 'Ratio', multiply1, 'A', controller)
        graph.add_link(for_each, 'Ratio', subtract, 'B', controller)
        graph.add_link(for_each, 'Ratio', multiply2, 'B', controller)
        graph.add_link(for_each, 'Ratio', subtract1, 'B', controller)
        graph.add_link(for_each, 'Ratio', subtract2, 'B', controller)
        graph.add_link(get_item_metadata, 'Found', and1, 'A', controller)
        graph.add_link(vetala_lib_find_bone_aim_axis, 'Result', cross, 'A', controller)
        graph.add_link(vetala_lib_find_bone_aim_axis, 'Result', from_axis_and_angle1, 'Axis', controller)
        graph.add_link(and1, 'Result', branch1, 'Condition', controller)
        graph.add_link(get_item_array_metadata, 'Value', vetala_lib_get_item1, 'Array', controller)
        graph.add_link(get_item_array_metadata, 'Value', for_each2, 'Array', controller)
        graph.add_link(get_item_array_metadata, 'Found', and1, 'B', controller)
        graph.add_link(branch4, 'Completed', aim_constraint, 'ExecutePin', controller)
        graph.add_link(get_item_metadata1, 'Value', aim_constraint, 'Child', controller)
        graph.add_link(vetala_lib_get_item1, 'Element', get_item_metadata1, 'Item', controller)
        graph.add_link(get_item_metadata1, 'Value', parent_constraint, 'Child', controller)
        graph.add_link(vetala_lib_get_item, 'Element', get_item_array_metadata1, 'Item', controller)
        graph.add_link(get_item_array_metadata1, 'Value', spline_from_items, 'Items', controller)
        graph.add_link(get_item_array_metadata1, 'Value', vetala_lib_get_item2, 'Array', controller)
        graph.add_link(get_item_array_metadata1, 'Value', vetala_lib_get_item3, 'Array', controller)
        graph.add_link(get_item_array_metadata1, 'Found', and2, 'A', controller)
        graph.add_link(vetala_lib_get_item, 'Element', get_item_array_metadata2, 'Item', controller)
        graph.add_link(and2, 'Result', branch2, 'Condition', controller)
        graph.add_link(spline_from_items, 'Spline', draw_spline, 'Spline', controller)
        graph.add_link(spline_from_items, 'Spline', position_from_spline, 'Spline', controller)
        graph.add_link(for_each1, 'Ratio', position_from_spline, 'U', controller)
        graph.add_link(position_from_spline, 'Position', make_transform, 'Translation', controller)
        graph.add_link(get_item_array_metadata2, 'Value', for_each1, 'Array', controller)
        graph.add_link(get_item_array_metadata2, 'Found', and2, 'B', controller)
        graph.add_link(for_each1, 'Element', set_transform, 'Item', controller)
        graph.add_link(make_transform, 'Result', set_transform, 'Value', controller)
        graph.add_link(vetala_lib_get_item1, 'Element', get_item_metadata4, 'Item', controller)
        graph.add_link(for_each2, 'Element', get_item_metadata2, 'Item', controller)
        graph.add_link(for_each2, 'Element', get_transform, 'Item', controller)
        graph.add_link(for_each2, 'Element', get_item_metadata3, 'Item', controller)
        graph.add_link(for_each2, 'Index', greater1, 'A', controller)
        graph.add_link(get_item_metadata2, 'Value', set_transform1, 'Item', controller)
        graph.add_link(get_transform, 'Transform', set_transform1, 'Value', controller)
        graph.add_link(vetala_lib_get_item2, 'Element.Name', get_float_channel, 'Control', controller)
        graph.add_link(vetala_lib_get_item2, 'Element.Name', get_float_channel3, 'Control', controller)
        graph.add_link(subtract, 'Result', multiply, 'A', controller)
        graph.add_link(get_float_channel, 'Value', multiply, 'B', controller)
        graph.add_link(multiply, 'Result', add, 'A', controller)
        graph.add_link(get_float_channel1, 'Value', multiply1, 'B', controller)
        graph.add_link(multiply1, 'Result', add1, 'B', controller)
        graph.add_link(greater1, 'Result', branch3, 'Condition', controller)
        graph.add_link(branch3, 'True', set_rotation, 'ExecutePin', controller)
        graph.add_link(get_item_metadata3, 'Value', set_rotation, 'Item', controller)
        graph.add_link(multiply4, 'Result', set_rotation, 'Value', controller)
        graph.add_link(absolute, 'Result', from_axis_and_angle, 'Axis', controller)
        graph.add_link(add, 'Result', from_axis_and_angle, 'Angle', controller)
        graph.add_link(from_axis_and_angle, 'Result', multiply4, 'A', controller)
        graph.add_link(from_string, 'Result', get_float_channel, 'Channel', controller)
        graph.add_link(vetala_lib_get_item3, 'Element.Name', get_float_channel1, 'Control', controller)
        graph.add_link(from_string1, 'Result', get_float_channel1, 'Channel', controller)
        graph.add_link(vetala_lib_get_item3, 'Element.Name', get_float_channel2, 'Control', controller)
        graph.add_link(from_string2, 'Result', get_float_channel2, 'Channel', controller)
        graph.add_link(get_float_channel2, 'Value', if1, 'False', controller)
        graph.add_link(get_float_channel2, 'Value', subtract3, 'B', controller)
        graph.add_link(get_float_channel2, 'Value', multiply5, 'A', controller)
        graph.add_link(get_float_channel2, 'Value', multiply2, 'A', controller)
        graph.add_link(multiply2, 'Result', add, 'B', controller)
        graph.add_link(vetala_lib_get_item_vector, 'Element', cross, 'B', controller)
        graph.add_link(cross, 'Result', absolute, 'Value', controller)
        graph.add_link(from_string3, 'Result', get_float_channel3, 'Channel', controller)
        graph.add_link(get_float_channel3, 'Value', multiply3, 'B', controller)
        graph.add_link(subtract1, 'Result', multiply3, 'A', controller)
        graph.add_link(multiply3, 'Result', add1, 'A', controller)
        graph.add_link(add1, 'Result', from_axis_and_angle1, 'Angle', controller)
        graph.add_link(from_axis_and_angle1, 'Result', multiply4, 'B', controller)
        graph.add_link(get_curl_axis, 'Value', vetala_lib_get_item_vector, 'Vector', controller)
        graph.add_link(get_top_parents, 'Value', num1, 'Array', controller)
        graph.add_link(get_top_parents, 'Value', spline_from_items1, 'Items', controller)
        graph.add_link(num1, 'Num', greater2, 'A', controller)
        graph.add_link(greater2, 'Result', branch4, 'Condition', controller)
        graph.add_link(spline_from_items1, 'Spline', position_from_spline1, 'Spline', controller)
        graph.add_link(spline_from_items1, 'Transforms', at, 'Array', controller)
        graph.add_link(spline_from_items1, 'Transforms', at1, 'Array', controller)
        graph.add_link(subtract2, 'Result', position_from_spline1, 'U', controller)
        graph.add_link(position_from_spline1, 'Position', make_transform1, 'Translation', controller)
        graph.add_link(interpolate, 'Result.Rotation', make_transform1, 'Rotation', controller)
        graph.add_link(make_transform1, 'Result', set_transform2, 'Value', controller)
        graph.add_link(set_transform2, 'ExecutePin', parent_constraint, 'ExecutePin', controller)
        graph.add_link(get_item_metadata5, 'Value', set_transform2, 'Item', controller)
        graph.add_link(subtract2, 'Result', interpolate, 'T', controller)
        graph.add_link(at, 'Element', interpolate, 'A', controller)
        graph.add_link(at1, 'Element', interpolate, 'B', controller)
        graph.add_link(get_invert_2nd_curl, 'Value', if1, 'Condition', controller)
        graph.add_link(multiply5, 'Result', if1, 'True', controller)
        graph.add_link(get_item_metadata4, 'Value', aim_constraint, 'WorldUp.Space', controller)
        graph.add_link(get_item_metadata, 'Value', aim_constraint, 'Parents.0.Item', controller)
        graph.add_link(get_item_metadata5, 'Value', parent_constraint, 'Parents.0.Item', controller)

        graph.set_pin(greater, 'B', '0', controller)
        graph.set_pin(get_item_metadata, 'Name', 'aim', controller)
        graph.set_pin(get_item_metadata, 'NameSpace', 'Self', controller)
        graph.set_pin(get_item_metadata, 'Default', '(Type=Bone,Name="None")', controller)
        graph.set_pin(get_item_array_metadata, 'Name', 'fk_controls', controller)
        graph.set_pin(get_item_array_metadata, 'NameSpace', 'Self', controller)
        graph.set_pin(aim_constraint, 'bMaintainOffset', 'True', controller)
        graph.set_pin(aim_constraint, 'Filter', '(bX=True,bY=True,bZ=True)', controller)
        graph.set_pin(aim_constraint, 'AimAxis', '(X=1.000000,Y=0.000000,Z=0.000000)', controller)
        graph.set_pin(aim_constraint, 'UpAxis', '(X=0.000000,Y=0.000000,Z=1.000000)', controller)
        graph.set_pin(aim_constraint, 'WorldUp', '(Target=(X=0.000000,Y=0.000000,Z=1.000000),Kind=Location,Space=(Type=None,Name="None"))', controller)
        graph.set_pin(aim_constraint, 'Parents', '((Item=(Type=Bone,Name="None"),Weight=1.000000))', controller)
        graph.set_pin(aim_constraint, 'AdvancedSettings', '(DebugSettings=(bEnabled=False,Scale=10.000000,WorldOffset=(Rotation=(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=1.000000,Y=1.000000,Z=1.000000))),RotationOrderForFilter=XZY)', controller)
        graph.set_pin(aim_constraint, 'Weight', '1.000000', controller)
        graph.set_pin(aim_constraint, 'bIsInitialized', 'False', controller)
        graph.set_pin(get_item_metadata1, 'Name', 'offset', controller)
        graph.set_pin(get_item_metadata1, 'NameSpace', 'Self', controller)
        graph.set_pin(get_item_metadata1, 'Default', '(Type=Bone,Name="None")', controller)
        graph.set_pin(get_item_array_metadata1, 'Name', 'aim_controls', controller)
        graph.set_pin(get_item_array_metadata1, 'NameSpace', 'Self', controller)
        graph.set_pin(spline_from_items, 'Spline Mode', 'BSpline', controller)
        graph.set_pin(spline_from_items, 'Samples Per Segment', '16', controller)
        graph.set_pin(draw_spline, 'Color', '(R=0.050000,G=0.050000,B=0.050000,A=1.000000)', controller)
        graph.set_pin(draw_spline, 'Thickness', '0.050000', controller)
        graph.set_pin(draw_spline, 'Detail', '16', controller)
        graph.set_pin(get_item_array_metadata2, 'Name', 'aims', controller)
        graph.set_pin(get_item_array_metadata2, 'NameSpace', 'Self', controller)
        graph.set_pin(set_transform, 'Space', 'GlobalSpace', controller)
        graph.set_pin(set_transform, 'bInitial', 'False', controller)
        graph.set_pin(set_transform, 'Weight', '1.000000', controller)
        graph.set_pin(set_transform, 'bPropagateToChildren', 'True', controller)
        graph.set_pin(make_transform, 'Rotation', '(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000)', controller)
        graph.set_pin(make_transform, 'Scale', '(X=1.000000,Y=1.000000,Z=1.000000)', controller)
        graph.set_pin(get_item_metadata2, 'Name', 'bone', controller)
        graph.set_pin(get_item_metadata2, 'NameSpace', 'Self', controller)
        graph.set_pin(get_item_metadata2, 'Default', '(Type=Bone,Name="None")', controller)
        graph.set_pin(set_transform1, 'Space', 'GlobalSpace', controller)
        graph.set_pin(set_transform1, 'bInitial', 'False', controller)
        graph.set_pin(set_transform1, 'Weight', '1.000000', controller)
        graph.set_pin(set_transform1, 'bPropagateToChildren', 'True', controller)
        graph.set_pin(get_transform, 'Space', 'GlobalSpace', controller)
        graph.set_pin(get_transform, 'bInitial', 'False', controller)
        graph.set_pin(greater1, 'B', '0', controller)
        graph.set_pin(set_rotation, 'Space', 'LocalSpace', controller)
        graph.set_pin(set_rotation, 'bInitial', 'False', controller)
        graph.set_pin(set_rotation, 'Weight', '1.000000', controller)
        graph.set_pin(set_rotation, 'bPropagateToChildren', 'True', controller)
        graph.set_pin(get_item_metadata3, 'Name', 'offset', controller)
        graph.set_pin(get_item_metadata3, 'NameSpace', 'Self', controller)
        graph.set_pin(get_item_metadata3, 'Default', '(Type=Bone,Name="None")', controller)
        graph.set_pin(get_float_channel, 'bInitial', 'False', controller)
        graph.set_pin(from_string, 'String', 'curl', controller)
        graph.set_pin(get_float_channel1, 'bInitial', 'False', controller)
        graph.set_pin(from_string1, 'String', 'twist', controller)
        graph.set_pin(vetala_lib_get_item3, 'index', '-1', controller)
        graph.set_pin(get_float_channel2, 'bInitial', 'False', controller)
        graph.set_pin(from_string2, 'String', 'curl', controller)
        graph.set_pin(subtract, 'A', '1.000000', controller)
        graph.set_pin(get_float_channel3, 'bInitial', 'False', controller)
        graph.set_pin(from_string3, 'String', 'twist', controller)
        graph.set_pin(subtract1, 'A', '1.000000', controller)
        graph.set_pin(greater2, 'B', '0', controller)
        graph.set_pin(spline_from_items1, 'Spline Mode', 'Hermite', controller)
        graph.set_pin(spline_from_items1, 'Samples Per Segment', '16', controller)
        graph.set_pin(make_transform1, 'Scale', '(X=1.000000,Y=1.000000,Z=1.000000)', controller)
        graph.set_pin(set_transform2, 'Space', 'GlobalSpace', controller)
        graph.set_pin(set_transform2, 'bInitial', 'False', controller)
        graph.set_pin(set_transform2, 'Weight', '1.000000', controller)
        graph.set_pin(set_transform2, 'bPropagateToChildren', 'True', controller)
        graph.set_pin(subtract2, 'A', '1.000000', controller)
        graph.set_pin(get_item_metadata4, 'Name', 'up', controller)
        graph.set_pin(get_item_metadata4, 'NameSpace', 'Self', controller)
        graph.set_pin(get_item_metadata4, 'Default', '(Type=Bone,Name="None")', controller)
        graph.set_pin(get_item_metadata5, 'Name', 'parent_null', controller)
        graph.set_pin(get_item_metadata5, 'NameSpace', 'Self', controller)
        graph.set_pin(get_item_metadata5, 'Default', '(Type=Bone,Name="None")', controller)
        graph.set_pin(parent_constraint, 'bMaintainOffset', 'True', controller)
        graph.set_pin(parent_constraint, 'Filter', '(TranslationFilter=(bX=True,bY=True,bZ=True),RotationFilter=(bX=True,bY=True,bZ=True),ScaleFilter=(bX=True,bY=True,bZ=True))', controller)
        graph.set_pin(parent_constraint, 'Parents', '((Item=(Type=Bone,Name="None"),Weight=1.000000))', controller)
        graph.set_pin(parent_constraint, 'AdvancedSettings', '(InterpolationType=Average,RotationOrderForFilter=XZY)', controller)
        graph.set_pin(parent_constraint, 'Weight', '1.000000', controller)
        graph.set_pin(at, 'Index', '0', controller)
        graph.set_pin(at1, 'Index', '-1', controller)
        graph.set_pin(subtract3, 'A', '1.000000', controller)
        graph.set_pin(multiply5, 'B', '-1.000000', controller)

        current_locals = locals()
        nodes = unreal_lib.graph.filter_nodes(current_locals.values())
        node = unreal_lib.graph.comment_nodes(nodes, controller, 'Forward Solve')
        nodes.append(node)
        unreal_lib.graph.move_nodes(500, 0, nodes, controller)


class UnrealGetTransform(UnrealUtil):

    def _build_function_graph(self):

        if not self.graph:
            return

        controller = self.function_controller

        num = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetNum(in Array,out Num)', unreal.Vector2D(-16.0, 192.0), 'Num')
        greater = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathIntGreater', 'Execute', unreal.Vector2D(176.0, 144.0), 'Greater')
        if1 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(450.0, 150.0), 'If')
        at = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(-160.0, 352.0), 'At')
        make_array = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayMake(in Values,out Array)', unreal.Vector2D(112.0, 368.0), 'Make Array')

        controller.resolve_wild_card_pin(f'{num.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{greater.get_node_path()}.A', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{greater.get_node_path()}.B', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{if1.get_node_path()}.Result', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{at.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{make_array.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')

        controller.set_array_pin_size(f'{n(make_array)}.Values', 1)

        graph.add_link('Entry', 'transforms', num, 'Array', controller)
        graph.add_link(num, 'Num', greater, 'A', controller)
        graph.add_link(greater, 'Result', if1, 'Condition', controller)
        graph.add_link(make_array, 'Array', if1, 'True', controller)
        graph.add_link(if1, 'Result', 'Return', 'transform', controller)
        graph.add_link('Entry', 'transforms', at, 'Array', controller)
        graph.add_link('Entry', 'index', at, 'Index', controller)
        graph.add_link(at, 'Element', make_array, 'Values.0', controller)

        graph.set_pin(greater, 'B', '0', controller)
        graph.set_pin(make_array, 'Values', '((Type=None,Name="None"))', controller)


class UnrealGetTransforms(UnrealUtil):

    def _build_function_graph(self):

        if not self.graph:
            return

        library = graph.get_local_function_library()

        controller = self.function_controller

        vetala_lib_get_item = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(1552.0, 128.0), 'vetalaLib_GetItem')
        vetala_lib_get_item1 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(1550.0, 253.0), 'vetalaLib_GetItem')
        vetala_lib_get_item2 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(1552.0, 384.0), 'vetalaLib_GetItem')
        vetala_lib_get_item3 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(1552.0, 512.0), 'vetalaLib_GetItem')
        vetala_lib_get_item4 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(1552.0, 640.0), 'vetalaLib_GetItem')
        make_array = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayMake(in Values,out Array)', unreal.Vector2D(2064.0, 112.0), 'Make Array')

        controller.set_array_pin_size(f'{n(make_array)}.Values', 5)

        graph.add_link('Entry', 'transforms1', vetala_lib_get_item, 'Array', controller)
        graph.add_link('Entry', 'index1', vetala_lib_get_item, 'index', controller)
        graph.add_link('Entry', 'transforms2', vetala_lib_get_item1, 'Array', controller)
        graph.add_link('Entry', 'index2', vetala_lib_get_item1, 'index', controller)
        graph.add_link('Entry', 'transforms3', vetala_lib_get_item2, 'Array', controller)
        graph.add_link('Entry', 'index3', vetala_lib_get_item2, 'index', controller)
        graph.add_link('Entry', 'transforms4', vetala_lib_get_item3, 'Array', controller)
        graph.add_link('Entry', 'index4', vetala_lib_get_item3, 'index', controller)
        graph.add_link('Entry', 'transforms5', vetala_lib_get_item4, 'Array', controller)
        graph.add_link('Entry', 'index5', vetala_lib_get_item4, 'index', controller)
        graph.add_link(make_array, 'Array', 'Return', 'transforms', controller)
        graph.add_link(make_array, 'Array', 'Print', 'Value', controller)
        graph.add_link(vetala_lib_get_item, 'Element', make_array, 'Values.0', controller)
        graph.add_link(vetala_lib_get_item1, 'Element', make_array, 'Values.1', controller)
        graph.add_link(vetala_lib_get_item2, 'Element', make_array, 'Values.2', controller)
        graph.add_link(vetala_lib_get_item3, 'Element', make_array, 'Values.3', controller)
        graph.add_link(vetala_lib_get_item4, 'Element', make_array, 'Values.4', controller)


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


class UnrealParent(UnrealUtil):

    def _use_mode(self):
        return True

    def _build_function_graph(self):
        super(UnrealParent, self)._build_function_graph()
        if not self.graph:
            return

        controller = self.function_controller
        library = graph.get_local_function_library()

        self.function_controller.add_local_variable_from_object_path('local_children', 'TArray<FRigElementKey>',
                                                                    '/Script/ControlRig.RigElementKey', '')

        entry = 'Entry'
        return1 = 'Return'
        switch = self.switch_node
        split = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_StringSplit', 'Execute', unreal.Vector2D(464.0, 400.0), 'Split')
        for_each = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayIterator(in Array,out Element,out Index,out Count,out Ratio)', unreal.Vector2D(1568.0, 0.0), 'For Each')
        vetala_lib_get_item = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(2032.0, -208.0), 'vetalaLib_GetItem')
        from_string = controller.add_template_node('DISPATCH_RigDispatch_FromString(in String,out Result)', unreal.Vector2D(1856.0, -80.0), 'From String')
        vetala_lib_get_item1 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(2208.0, -640.0), 'vetalaLib_GetItem')
        if1 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(2448.0, 263.0), 'If')
        vetala_lib_parent = controller.add_function_reference_node(library.find_function('vetalaLib_Parent'), unreal.Vector2D(3280.0, 95.0), 'vetalaLib_Parent')
        for_each1 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayIterator(in Array,out Element,out Index,out Count,out Ratio)', unreal.Vector2D(3008.0, 119.0), 'For Each')
        add = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayAdd(io Array,in Element,out Index)', unreal.Vector2D(2736.0, -76.0), 'Add')
        get_local_children = controller.add_variable_node_from_object_path('local_children', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(2448.0, -288.0), 'Get local_children')
        branch = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_ControlFlowBranch', 'Execute', unreal.Vector2D(2480.0, -80.0), 'Branch')
        item_exists = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_ItemExists', 'Execute', unreal.Vector2D(2176.0, 23.0), 'Item Exists')
        get_local_children1 = controller.add_variable_node_from_object_path('local_children', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(2192.0, 528.0), 'Get local_children')
        set_local_children = controller.add_variable_node_from_object_path('local_children', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', False, '()', unreal.Vector2D(2960.0, -97.0), 'Set local_children')
        num = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetNum(in Array,out Num)', unreal.Vector2D(816.0, 256.0), 'Num')
        greater = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathIntGreater', 'Execute', unreal.Vector2D(992.0, 256.0), 'Greater')
        if2 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(1168.0, 528.0), 'If')
        make_array = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayMake(in Values,out Array)', unreal.Vector2D(912.0, 640.0), 'Make Array')
        has_metadata = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HasMetadata', 'Execute', unreal.Vector2D(3456.0, 464.0), 'Has Metadata')
        get_item_metadata = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(4112.0, 400.0), 'Get Item Metadata')
        branch1 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_ControlFlowBranch', 'Execute', unreal.Vector2D(3840.0, 352.0), 'Branch')
        vetala_lib_parent1 = controller.add_function_reference_node(library.find_function('vetalaLib_Parent'), unreal.Vector2D(4240.0, 112.0), 'vetalaLib_Parent')

        controller.set_array_pin_size(f'{n(switch)}.Cases', 4)
        controller.set_array_pin_size(f'{n(make_array)}.Values', 1)

        graph.add_link(entry, 'ExecuteContext', switch, 'ExecuteContext', controller)
        graph.add_link(switch, 'Completed', return1, 'ExecuteContext', controller)
        graph.add_link(switch, 'Cases.0', for_each, 'ExecuteContext', controller)
        graph.add_link(for_each, 'ExecuteContext', branch, 'ExecuteContext', controller)
        graph.add_link(for_each, 'Completed', for_each1, 'ExecuteContext', controller)
        graph.add_link(for_each1, 'ExecuteContext', vetala_lib_parent, 'ExecuteContext', controller)
        graph.add_link(vetala_lib_parent, 'ExecuteContext', branch1, 'ExecuteContext', controller)
        graph.add_link(branch, 'True', add, 'ExecuteContext', controller)
        graph.add_link(add, 'ExecuteContext', set_local_children, 'ExecuteContext', controller)
        graph.add_link(branch1, 'True', vetala_lib_parent1, 'ExecuteContext', controller)
        graph.add_link(entry, 'mode', switch, 'Index', controller)
        graph.add_link(entry, 'parent', vetala_lib_get_item1, 'Array', controller)
        graph.add_link(entry, 'parent_index', vetala_lib_get_item1, 'index', controller)
        graph.add_link(entry, 'children', vetala_lib_get_item, 'Array', controller)
        graph.add_link(entry, 'children', if1, 'True', controller)
        graph.add_link(entry, 'affect_all_children', if1, 'Condition', controller)
        graph.add_link(entry, 'child_indices', split, 'Value', controller)
        graph.add_link(split, 'Result', num, 'Array', controller)
        graph.add_link(split, 'Result', if2, 'True', controller)
        graph.add_link(if2, 'Result', for_each, 'Array', controller)
        graph.add_link(for_each, 'Element', from_string, 'String', controller)
        graph.add_link(vetala_lib_get_item, 'Element', item_exists, 'Item', controller)
        graph.add_link(vetala_lib_get_item, 'Element', add, 'Element', controller)
        graph.add_link(from_string, 'Result', vetala_lib_get_item, 'index', controller)
        graph.add_link(vetala_lib_get_item1, 'Element', vetala_lib_parent, 'Parent', controller)
        graph.add_link(vetala_lib_get_item1, 'Element', vetala_lib_parent1, 'Parent', controller)
        graph.add_link(get_local_children1, 'Value', if1, 'False', controller)
        graph.add_link(if1, 'Result', for_each1, 'Array', controller)
        graph.add_link(for_each1, 'Element', vetala_lib_parent, 'Child', controller)
        graph.add_link(for_each1, 'Element', has_metadata, 'Item', controller)
        graph.add_link(for_each1, 'Element', get_item_metadata, 'Item', controller)
        graph.add_link(get_local_children, 'Value', add, 'Array', controller)
        graph.add_link(add, 'Array', set_local_children, 'Value', controller)
        graph.add_link(item_exists, 'Exists', branch, 'Condition', controller)
        graph.add_link(num, 'Num', 'Greater', 'A', controller)
        graph.add_link(num, 'Num', greater, 'A', controller)
        graph.add_link(greater, 'Result', if2, 'Condition', controller)
        graph.add_link(make_array, 'Array', if2, 'False', controller)
        graph.add_link(has_metadata, 'Found', branch1, 'Condition', controller)
        graph.add_link(get_item_metadata, 'Value', vetala_lib_parent1, 'Child', controller)
        graph.add_link(entry, 'child_indices', make_array, 'Values.0', controller)

        graph.set_pin(split, 'Separator', ' ', controller)
        graph.set_pin(greater, 'B', '1', controller)
        graph.set_pin(make_array, 'Values', '("")', controller)
        graph.set_pin(has_metadata, 'Name', 'anchor', controller)
        graph.set_pin(has_metadata, 'Type', 'RigElementKey', controller)
        graph.set_pin(has_metadata, 'NameSpace', 'Self', controller)
        graph.set_pin(get_item_metadata, 'Name', 'anchor', controller)
        graph.set_pin(get_item_metadata, 'NameSpace', 'Self', controller)
        graph.set_pin(get_item_metadata, 'Default', '(Type=Bone,Name="None")', controller)


class UnrealAnchor(UnrealUtil):

    def _use_mode(self):
        return True

    def _build_function_graph(self):
        super(UnrealAnchor, self)._build_function_graph()
        if not self.graph:
            return

        controller = self.function_controller
        library = graph.get_local_function_library()

        controller.add_local_variable_from_object_path(
            'local_parents',
            'TArray<FConstraintParent>',
            '/Script/ControlRig.ConstraintParent',
            ''
        )

        entry = 'Entry'
        return1 = 'Return'
        switch = self.switch_node

        for_each = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayIterator(in Array,out Element,out Index,out Count,out Ratio)', unreal.Vector2D(1280.0, 960.0), 'For Each')
        vetala_lib_string_to_index = controller.add_function_reference_node(library.find_function('vetalaLib_StringToIndex'), unreal.Vector2D(272.0, 400.0), 'vetalaLib_StringToIndex')
        vetala_lib_index_to_items = controller.add_function_reference_node(library.find_function('vetalaLib_IndexToItems'), unreal.Vector2D(592.0, 432.0), 'vetalaLib_IndexToItems')
        vetala_lib_string_to_index1 = controller.add_function_reference_node(library.find_function('vetalaLib_StringToIndex'), unreal.Vector2D(416.0, 752.0), 'vetalaLib_StringToIndex')
        vetala_lib_index_to_items1 = controller.add_function_reference_node(library.find_function('vetalaLib_IndexToItems'), unreal.Vector2D(720.0, 784.0), 'vetalaLib_IndexToItems')
        for_each1 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayIterator(in Array,out Element,out Index,out Count,out Ratio)', unreal.Vector2D(1104.0, 608.0), 'For Each')
        position_constraint = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_PositionConstraintLocalSpaceOffset', 'Execute', unreal.Vector2D(2832.0, 560.0), 'Position Constraint')
        get_local_parents = controller.add_variable_node_from_object_path('local_parents', 'TArray<FConstraintParent>', '/Script/ControlRig.ConstraintParent', True, '()', unreal.Vector2D(1440.0, 336.0), 'Get local_parents')
        add = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayAdd(io Array,in Element,out Index)', unreal.Vector2D(1616.0, 496.0), 'Add')
        get_local_parents1 = controller.add_variable_node_from_object_path('local_parents', 'TArray<FConstraintParent>', '/Script/ControlRig.ConstraintParent', True, '()', unreal.Vector2D(2432.0, 1232.0), 'Get local_parents')
        parent_constraint = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_ParentConstraint', 'Execute', unreal.Vector2D(3088.0, 1712.0), 'Parent Constraint')
        branch = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_ControlFlowBranch', 'Execute', unreal.Vector2D(1776.0, 928.0), 'Branch')
        get_translate = controller.add_variable_node('translate', 'bool', None, True, '', unreal.Vector2D(2112.0, 1040.0), 'Get translate')
        rotation_constraint = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_RotationConstraintLocalSpaceOffset', 'Execute', unreal.Vector2D(3200.0, 752.0), 'Rotation Constraint')
        scale_constraint = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_ScaleConstraintLocalSpaceOffset', 'Execute', unreal.Vector2D(3648.0, 816.0), 'Scale Constraint')
        vetala_lib_string_to_index2 = controller.add_function_reference_node(library.find_function('vetalaLib_StringToIndex'), unreal.Vector2D(700.0, -351.0), 'vetalaLib_StringToIndex')
        vetala_lib_index_to_items2 = controller.add_function_reference_node(library.find_function('vetalaLib_IndexToItems'), unreal.Vector2D(928.0, -352.0), 'vetalaLib_IndexToItems')
        for_each2 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayIterator(in Array,out Element,out Index,out Count,out Ratio)', unreal.Vector2D(1216.0, -368.0), 'For Each')
        get_parent = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyGetParent', 'Execute', unreal.Vector2D(1504.0, -576.0), 'Get Parent')
        spawn_transform_control = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyAddControlTransform', 'Execute', unreal.Vector2D(1968.0, -976.0), 'Spawn Transform Control')
        get_transform = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetTransform', 'Execute', unreal.Vector2D(1520.0, -288.0), 'Get Transform')
        set_item_metadata = controller.add_template_node('DISPATCH_RigDispatch_SetMetadata(in Item,in Name,in NameSpace,in Value,out Success)', unreal.Vector2D(2528.0, -976.0), 'Set Item Metadata')
        concat = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_NameConcat', 'Execute', unreal.Vector2D(1408.0, -816.0), 'Concat')
        vetala_lib_parent = controller.add_function_reference_node(library.find_function('vetalaLib_Parent'), unreal.Vector2D(2992.0, -976.0), 'vetalaLib_Parent')
        get_item_metadata = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(1776.0, 1456.0), 'Get Item Metadata')
        get_rotate = controller.add_variable_node('rotate', 'bool', None, True, '', unreal.Vector2D(2288.0, 1696.0), 'Get rotate')
        get_scale = controller.add_variable_node('scale', 'bool', None, True, '', unreal.Vector2D(2416.0, 1952.0), 'Get scale')

        controller.resolve_wild_card_pin(f'{for_each.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{for_each1.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{add.get_node_path()}.Array', 'TArray<FConstraintParent>', '/Script/ControlRig.ConstraintParent')
        controller.resolve_wild_card_pin(f'{for_each2.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{concat.get_node_path()}.Result', 'FName', 'None')

        controller.set_array_pin_size(f'{n(switch)}.Cases', 4)

        graph.add_link(switch, 'Completed', return1, 'ExecuteContext', controller)
        graph.add_link('Entry', 'ExecuteContext', switch, 'ExecuteContext', controller)
        graph.add_link(switch, 'Cases.0', vetala_lib_string_to_index2, 'ExecuteContext', controller)
        graph.add_link(switch, 'Cases.1', vetala_lib_string_to_index, 'ExecuteContext', controller)
        graph.add_link(for_each1, 'Completed', for_each, 'ExecuteContext', controller)
        graph.add_link(for_each, 'ExecuteContext', branch, 'ExecuteContext', controller)
        graph.add_link(vetala_lib_string_to_index, 'ExecuteContext', vetala_lib_index_to_items, 'ExecuteContext', controller)
        graph.add_link(vetala_lib_index_to_items, 'ExecuteContext', vetala_lib_string_to_index1, 'ExecuteContext', controller)
        graph.add_link(vetala_lib_string_to_index1, 'ExecuteContext', vetala_lib_index_to_items1, 'ExecuteContext', controller)
        graph.add_link(vetala_lib_index_to_items1, 'ExecuteContext', for_each1, 'ExecuteContext', controller)
        graph.add_link(for_each1, 'ExecuteContext', add, 'ExecuteContext', controller)
        graph.add_link(vetala_lib_string_to_index2, 'ExecuteContext', vetala_lib_index_to_items2, 'ExecuteContext', controller)
        graph.add_link(vetala_lib_index_to_items2, 'ExecuteContext', for_each2, 'ExecuteContext', controller)
        graph.add_link(for_each2, 'ExecuteContext', spawn_transform_control, 'ExecutePin', controller)
        graph.add_link(spawn_transform_control, 'ExecutePin', set_item_metadata, 'ExecuteContext', controller)
        graph.add_link(set_item_metadata, 'ExecuteContext', vetala_lib_parent, 'ExecuteContext', controller)
        graph.add_link('Entry', 'mode', switch, 'Index', controller)
        graph.add_link(vetala_lib_index_to_items1, 'Result', for_each, 'Array', controller)
        graph.add_link(for_each, 'Element', get_item_metadata, 'Item', controller)
        graph.add_link('Entry', 'parent_index', vetala_lib_string_to_index, 'string', controller)
        graph.add_link(vetala_lib_string_to_index, 'index', vetala_lib_index_to_items, 'Index', controller)
        graph.add_link('Entry', 'parent', vetala_lib_index_to_items, 'Items', controller)
        graph.add_link(vetala_lib_index_to_items, 'Result', for_each1, 'Array', controller)
        graph.add_link('Entry', 'child_indices', vetala_lib_string_to_index1, 'string', controller)
        graph.add_link(vetala_lib_string_to_index1, 'index', vetala_lib_index_to_items1, 'Index', controller)
        graph.add_link('Entry', 'children', vetala_lib_index_to_items1, 'Items', controller)
        graph.add_link(branch, 'True', position_constraint, 'ExecutePin', controller)
        graph.add_link(position_constraint, 'ExecutePin', rotation_constraint, 'ExecutePin', controller)
        graph.add_link(get_item_metadata, 'Value', position_constraint, 'Child', controller)
        graph.add_link(get_local_parents1, 'Value', position_constraint, 'Parents', controller)
        graph.add_link(get_local_parents, 'Value', add, 'Array', controller)
        graph.add_link(get_local_parents1, 'Value', scale_constraint, 'Parents', controller)
        graph.add_link(get_local_parents1, 'Value', rotation_constraint, 'Parents', controller)
        graph.add_link(get_local_parents1, 'Value', parent_constraint, 'Parents', controller)
        graph.add_link(branch, 'False', parent_constraint, 'ExecutePin', controller)
        graph.add_link(get_item_metadata, 'Value', parent_constraint, 'Child', controller)
        graph.add_link('Entry', 'use_child_pivot', branch, 'Condition', controller)
        graph.add_link(rotation_constraint, 'ExecutePin', scale_constraint, 'ExecutePin', controller)
        graph.add_link(get_item_metadata, 'Value', rotation_constraint, 'Child', controller)
        graph.add_link(get_item_metadata, 'Value', scale_constraint, 'Child', controller)
        graph.add_link('Entry', 'child_indices', vetala_lib_string_to_index2, 'string', controller)
        graph.add_link(vetala_lib_string_to_index2, 'index', vetala_lib_index_to_items2, 'Index', controller)
        graph.add_link('Entry', 'children', vetala_lib_index_to_items2, 'Items', controller)
        graph.add_link(vetala_lib_index_to_items2, 'Result', for_each2, 'Array', controller)
        graph.add_link(for_each2, 'Element', get_parent, 'Child', controller)
        graph.add_link(for_each2, 'Element', get_transform, 'Item', controller)
        graph.add_link(for_each2, 'Element', set_item_metadata, 'Item', controller)
        graph.add_link(for_each2, 'Element', vetala_lib_parent, 'Child', controller)
        graph.add_link(for_each2, 'Element.Name', concat, 'B', controller)
        graph.add_link(get_parent, 'Parent', spawn_transform_control, 'Parent', controller)
        graph.add_link(concat, 'Result', spawn_transform_control, 'Name', controller)
        graph.add_link(spawn_transform_control, 'Item', set_item_metadata, 'Value', controller)
        graph.add_link(spawn_transform_control, 'Item', vetala_lib_parent, 'Parent', controller)
        graph.add_link(get_transform, 'Transform', spawn_transform_control, 'InitialValue', controller)
        graph.add_link(for_each1, 'Element', add, 'Element.Item', controller)
        graph.add_link(get_translate, 'Value', position_constraint, 'Filter.bX', controller)
        graph.add_link(get_translate, 'Value', position_constraint, 'Filter.bY', controller)
        graph.add_link(get_translate, 'Value', position_constraint, 'Filter.bZ', controller)
        graph.add_link(get_rotate, 'Value', rotation_constraint, 'Filter.bX', controller)
        graph.add_link(get_rotate, 'Value', rotation_constraint, 'Filter.bY', controller)
        graph.add_link(get_rotate, 'Value', rotation_constraint, 'Filter.bZ', controller)
        graph.add_link(get_scale, 'Value', scale_constraint, 'Filter.bX', controller)
        graph.add_link(get_scale, 'Value', scale_constraint, 'Filter.bY', controller)
        graph.add_link(get_scale, 'Value', scale_constraint, 'Filter.bZ', controller)
        graph.add_link(get_translate, 'Value', parent_constraint, 'Filter.TranslationFilter.bX', controller)
        graph.add_link(get_translate, 'Value', parent_constraint, 'Filter.TranslationFilter.bY', controller)
        graph.add_link(get_translate, 'Value', parent_constraint, 'Filter.TranslationFilter.bZ', controller)
        graph.add_link(get_rotate, 'Value', parent_constraint, 'Filter.RotationFilter.bX', controller)
        graph.add_link(get_rotate, 'Value', parent_constraint, 'Filter.RotationFilter.bY', controller)
        graph.add_link(get_rotate, 'Value', parent_constraint, 'Filter.RotationFilter.bZ', controller)
        graph.add_link(get_scale, 'Value', parent_constraint, 'Filter.ScaleFilter.bX', controller)
        graph.add_link(get_scale, 'Value', parent_constraint, 'Filter.ScaleFilter.bY', controller)
        graph.add_link(get_scale, 'Value', parent_constraint, 'Filter.ScaleFilter.bZ', controller)

        graph.set_pin(position_constraint, 'bMaintainOffset', 'True', controller)
        graph.set_pin(position_constraint, 'Filter', '(bX=True,bY=True,bZ=True)', controller)
        graph.set_pin(position_constraint, 'Weight', '1.000000', controller)
        graph.set_pin(add, 'Element', '(Item=(Type=Bone,Name="None"),Weight=1.000000)', controller)
        graph.set_pin(parent_constraint, 'bMaintainOffset', 'True', controller)
        graph.set_pin(parent_constraint, 'Filter', '(TranslationFilter=(bX=True,bY=True,bZ=True),RotationFilter=(bX=True,bY=True,bZ=True),ScaleFilter=(bX=True,bY=True,bZ=True))', controller)
        graph.set_pin(parent_constraint, 'AdvancedSettings', '(InterpolationType=Average,RotationOrderForFilter=XZY)', controller)
        graph.set_pin(parent_constraint, 'Weight', '1.000000', controller)
        graph.set_pin(rotation_constraint, 'bMaintainOffset', 'True', controller)
        graph.set_pin(rotation_constraint, 'Filter', '(bX=True,bY=True,bZ=True)', controller)
        graph.set_pin(rotation_constraint, 'AdvancedSettings', '(InterpolationType=Average,RotationOrderForFilter=XZY)', controller)
        graph.set_pin(rotation_constraint, 'Weight', '1.000000', controller)
        graph.set_pin(scale_constraint, 'bMaintainOffset', 'True', controller)
        graph.set_pin(scale_constraint, 'Filter', '(bX=True,bY=True,bZ=True)', controller)
        graph.set_pin(scale_constraint, 'Weight', '1.000000', controller)
        graph.set_pin(get_parent, 'bDefaultParent', 'True', controller)
        graph.set_pin(spawn_transform_control, 'OffsetTransform', '(Rotation=(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=1.000000,Y=1.000000,Z=1.000000))', controller)
        graph.set_pin(spawn_transform_control, 'OffsetSpace', 'GlobalSpace', controller)
        graph.set_pin(spawn_transform_control, 'Settings', '(InitialSpace=GlobalSpace,bUsePreferredRotationOrder=False,PreferredRotationOrder=YZX,Limits=(LimitTranslationX=(bMinimum=False,bMaximum=False),LimitTranslationY=(bMinimum=False,bMaximum=False),LimitTranslationZ=(bMinimum=False,bMaximum=False),LimitPitch=(bMinimum=False,bMaximum=False),LimitYaw=(bMinimum=False,bMaximum=False),LimitRoll=(bMinimum=False,bMaximum=False),LimitScaleX=(bMinimum=False,bMaximum=False),LimitScaleY=(bMinimum=False,bMaximum=False),LimitScaleZ=(bMinimum=False,bMaximum=False),MinValue=(Location=(X=-100.000000,Y=-100.000000,Z=-100.000000),Rotation=(Pitch=-180.000000,Yaw=-180.000000,Roll=-180.000000),Scale=(X=0.000000,Y=0.000000,Z=0.000000)),MaxValue=(Location=(X=100.000000,Y=100.000000,Z=100.000000),Rotation=(Pitch=180.000000,Yaw=180.000000,Roll=180.000000),Scale=(X=10.000000,Y=10.000000,Z=10.000000)),bDrawLimits=True),Shape=(bVisible=False,Name="Box_Thin",Color=(R=1.000000,G=0.000000,B=0.000000,A=1.000000),Transform=(Rotation=(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=1.000000,Y=1.000000,Z=1.000000))),Proxy=(bIsProxy=True,ShapeVisibility=BasedOnSelection),FilteredChannels=(),DisplayName="None")', controller)
        graph.set_pin(get_transform, 'Space', 'GlobalSpace', controller)
        graph.set_pin(get_transform, 'bInitial', 'False', controller)
        graph.set_pin(set_item_metadata, 'Name', 'anchor', controller)
        graph.set_pin(set_item_metadata, 'NameSpace', 'Self', controller)
        graph.set_pin(concat, 'A', 'anchor_', controller)
        graph.set_pin(get_item_metadata, 'Name', 'anchor', controller)
        graph.set_pin(get_item_metadata, 'NameSpace', 'Self', controller)
        graph.set_pin(get_item_metadata, 'Default', '(Type=Bone,Name="None")', controller)


class UnrealSwitch(UnrealUtil):

    def _use_mode(self):
        return True

    def _build_function_graph(self):
        super(UnrealSwitch, self)._build_function_graph()
        if not self.graph:
            return

        controller = self.function_controller
        library = graph.get_local_function_library()

        self.function_controller.add_local_variable_from_object_path('local_controls', 'TArray<FRigElementKey>',
                                                                    '/Script/ControlRig.RigElementKey', '')

        entry = 'Entry'
        return1 = 'Return'
        switch = self.switch_node

        set_item_metadata = controller.add_template_node('DISPATCH_RigDispatch_SetMetadata(in Item,in Name,in NameSpace,in Value,out Success)', unreal.Vector2D(2883.8681640625, -592.1484375), 'Set Item Metadata')

        if1 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(1040.0, -992.0), 'If')
        vetala_lib_rig_layer_solver = controller.add_function_reference_node(library.find_function('vetalaLib_rigLayerSolver'), unreal.Vector2D(1584.0, 176.0), 'vetalaLib_rigLayerSolver')
        vetala_lib_control = self._create_control(controller, 784.0, -736.0)
        set_item_metadata1 = controller.add_template_node('DISPATCH_RigDispatch_SetMetadata(in Item,in Name,in NameSpace,in Value,out Success)', unreal.Vector2D(1328.0, -752.0), 'Set Item Metadata')
        from_string = controller.add_template_node('DISPATCH_RigDispatch_FromString(in String,out Result)', unreal.Vector2D(1056.0, -560.0), 'From String')
        spawn_scale_float_animation_channel = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyAddAnimationChannelScaleFloat', 'Execute', unreal.Vector2D(1968.0, -768.0), 'Spawn Scale Float Animation Channel')
        from_string1 = controller.add_template_node('DISPATCH_RigDispatch_FromString(in String,out Result)', unreal.Vector2D(576.0, 688.0), 'From String')
        get_item_metadata = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(752.0, 368.0), 'Get Item Metadata')
        get_float_channel = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetFloatAnimationChannel', 'Execute', unreal.Vector2D(1168.0, 496.0), 'Get Float Channel')
        from_string2 = controller.add_template_node('DISPATCH_RigDispatch_FromString(in String,out Result)', unreal.Vector2D(1226.0, -198.0), 'From String')
        from_string3 = controller.add_template_node('DISPATCH_RigDispatch_FromString(in String,out Result)', unreal.Vector2D(432.0, 576.0), 'From String')
        item_exists = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_ItemExists', 'Execute', unreal.Vector2D(1088.0, 240.0), 'Item Exists')
        if2 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(1392.0, 288.0), 'If')
        add = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayAdd(io Array,in Element,out Index)', unreal.Vector2D(2519.0, -627.0), 'Add')
        get_local_controls = controller.add_variable_node_from_object_path('local_controls', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(2152.0, -417.0), 'Get local_controls')
        add1 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayAdd(io Array,in Element,out Index)', unreal.Vector2D(2160.0, 288.0), 'Add')
        branch = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_ControlFlowBranch', 'Execute', unreal.Vector2D(1808.0, 336.0), 'Branch')
        get_local_controls1 = controller.add_variable_node_from_object_path('local_controls', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(1984.0, 496.0), 'Get local_controls')
        equals = controller.add_template_node('DISPATCH_RigVMDispatch_CoreEquals(in A,in B,out Result)', unreal.Vector2D(-32.0, -528.0), 'Equals')
        if3 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(176.0, -544.0), 'If')
        if4 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(192.0, -384.0), 'If')
        vetala_lib_get_item = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(496.0, 368.0), 'vetalaLib_GetItem')
        vetala_lib_get_item1 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(-112.0, -912.0), 'vetalaLib_GetItem')
        vetala_lib_get_item2 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(-112.0, -1072.0), 'vetalaLib_GetItem')
        vetala_lib_get_item3 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(-112.0, -752.0), 'vetalaLib_GetItem')
        item_exists1 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_ItemExists', 'Execute', unreal.Vector2D(464.0, -1104.0), 'Item Exists')
        set_transform = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_SetTransform', 'Execute', unreal.Vector2D(3024.0, 304.0), 'Set Transform')
        vetala_lib_get_item4 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(720.0, 816.0), 'vetalaLib_GetItem')
        item_exists2 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_ItemExists', 'Execute', unreal.Vector2D(1184.0, 944.0), 'Item Exists')
        not1 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathBoolNot', 'Execute', unreal.Vector2D(1664.0, 896.0), 'Not')
        get_transform = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetTransform', 'Execute', unreal.Vector2D(2720.0, 960.0), 'Get Transform')
        branch1 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_ControlFlowBranch', 'Execute', unreal.Vector2D(2432.0, 288.0), 'Branch')
        get_item_metadata1 = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(2704.0, 752.0), 'Get Item Metadata')
        make_array = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayMake(in Values,out Array)', unreal.Vector2D(3776.0, 64.0), 'Make Array')
        get_item_metadata2 = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(3408.0, 64.0), 'Get Item Metadata')
        at = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(3232.0, 64.0), 'At')

        controller.resolve_wild_card_pin(f'{if1.get_node_path()}.Result', 'FRigElementKey', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{if2.get_node_path()}.Result', 'float', 'None')
        controller.resolve_wild_card_pin(f'{add.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{add1.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{equals.get_node_path()}.A', 'FString', 'None')
        controller.resolve_wild_card_pin(f'{equals.get_node_path()}.B', 'FString', 'None')
        controller.resolve_wild_card_pin(f'{if3.get_node_path()}.Result', 'FString', 'None')
        controller.resolve_wild_card_pin(f'{if4.get_node_path()}.Result', 'float', 'None')
        controller.resolve_wild_card_pin(f'{make_array.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{at.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')

        controller.set_array_pin_size(f'{n(switch)}.Cases', 4)
        controller.set_array_pin_size(f'{n(vetala_lib_control)}.sub_color', 1)
        controller.set_array_pin_size(f'{n(make_array)}.Values', 1)

        graph.add_link(entry, 'ExecuteContext', switch, 'ExecuteContext', controller)
        graph.add_link(switch, 'Completed', return1, 'ExecuteContext', controller)
        graph.add_link(add, 'ExecuteContext', set_item_metadata, 'ExecuteContext', controller)
        graph.add_link(switch, 'Cases.0', vetala_lib_control, 'ExecuteContext', controller)
        graph.add_link(switch, 'Cases.1', vetala_lib_rig_layer_solver, 'ExecuteContext', controller)
        graph.add_link(vetala_lib_rig_layer_solver, 'ExecuteContext', branch, 'ExecuteContext', controller)
        graph.add_link(vetala_lib_control, 'ExecuteContext', set_item_metadata1, 'ExecuteContext', controller)
        graph.add_link(set_item_metadata1, 'ExecuteContext', spawn_scale_float_animation_channel, 'ExecutePin', controller)
        graph.add_link(spawn_scale_float_animation_channel, 'ExecutePin', add, 'ExecuteContext', controller)
        graph.add_link(branch, 'True', add1, 'ExecuteContext', controller)
        graph.add_link(add1, 'ExecuteContext', branch1, 'ExecuteContext', controller)
        graph.add_link(entry, 'mode', switch, 'Index', controller)
        graph.add_link(entry, 'parent', vetala_lib_get_item2, 'Array', controller)
        graph.add_link(entry, 'joints', vetala_lib_rig_layer_solver, 'Joints', controller)
        graph.add_link(entry, 'joints', vetala_lib_get_item, 'Array', controller)
        graph.add_link(entry, 'joints', vetala_lib_get_item1, 'Array', controller)
        graph.add_link(entry, 'joints', at, 'Array', controller)
        graph.add_link(entry, 'attribute_control', vetala_lib_get_item3, 'Array', controller)
        graph.add_link(entry, 'attribute_control', vetala_lib_get_item4, 'Array', controller)
        graph.add_link(entry, 'control_index', vetala_lib_get_item3, 'index', controller)
        graph.add_link(entry, 'control_index', vetala_lib_get_item4, 'index', controller)
        graph.add_link(entry, 'description', vetala_lib_control, 'description', controller)
        graph.add_link(entry, 'side', vetala_lib_control, 'side', controller)
        graph.add_link(entry, 'restrain_numbering', vetala_lib_control, 'restrain_numbering', controller)
        graph.add_link(entry, 'attribute_name', from_string1, 'String', controller)
        graph.add_link(entry, 'attribute_name', from_string2, 'String', controller)
        graph.add_link(entry, 'default_value', spawn_scale_float_animation_channel, 'InitialValue', controller)
        graph.add_link(entry, 'color', vetala_lib_control, 'color', controller)
        graph.add_link(entry, 'shape', equals, 'A', controller)
        graph.add_link(entry, 'shape', if3, 'False', controller)
        graph.add_link(entry, 'shape_translate', vetala_lib_control, 'translate', controller)
        graph.add_link(entry, 'shape_rotate', vetala_lib_control, 'rotate', controller)
        graph.add_link(entry, 'shape_scale', vetala_lib_control, 'scale', controller)
        graph.add_link(make_array, 'Array', return1, 'controls', controller)
        graph.add_link(vetala_lib_control, 'Control', set_item_metadata, 'Item', controller)
        graph.add_link(spawn_scale_float_animation_channel, 'Item', set_item_metadata, 'Value', controller)
        graph.add_link(item_exists1, 'Exists', if1, 'Condition', controller)
        graph.add_link(vetala_lib_get_item3, 'Element', if1, 'True', controller)
        graph.add_link(vetala_lib_control, 'Control', if1, 'False', controller)
        graph.add_link(if1, 'Result', set_item_metadata1, 'Value', controller)
        graph.add_link('If_1', 'Result', vetala_lib_rig_layer_solver, 'Switch', controller)
        graph.add_link(vetala_lib_get_item2, 'Element', vetala_lib_control, 'parent', controller)
        graph.add_link(vetala_lib_get_item1, 'Element', vetala_lib_control, 'driven', controller)
        graph.add_link(if3, 'Result', vetala_lib_control, 'shape', controller)
        graph.add_link(if4, 'Result', vetala_lib_control, 'scale_offset', controller)
        graph.add_link(vetala_lib_control, 'Control', spawn_scale_float_animation_channel, 'Parent', controller)
        graph.add_link(vetala_lib_control, 'Control', add, 'Element', controller)
        graph.add_link(vetala_lib_get_item1, 'Element', set_item_metadata1, 'Item', controller)
        graph.add_link(from_string, 'Result', set_item_metadata1, 'Name', controller)
        graph.add_link(from_string2, 'Result', spawn_scale_float_animation_channel, 'Name', controller)
        graph.add_link(from_string1, 'Result', get_float_channel, 'Channel', controller)
        graph.add_link(vetala_lib_get_item, 'Element', get_item_metadata, 'Item', controller)
        graph.add_link(from_string3, 'Result', get_item_metadata, 'Name', controller)
        graph.add_link(get_item_metadata, 'Value', item_exists, 'Item', controller)
        graph.add_link(get_item_metadata, 'Value', add1, 'Element', controller)
        graph.add_link(get_item_metadata, 'Value.Name', get_float_channel, 'Control', controller)
        graph.add_link(get_float_channel, 'Value', if2, 'True', controller)
        graph.add_link(item_exists, 'Exists', if2, 'Condition', controller)
        graph.add_link(item_exists, 'Exists', branch, 'Condition', controller)
        graph.add_link(if2, 'Result', 'vetalaLib_rigLayerSolver', 'Switch', controller)
        graph.add_link(get_local_controls, 'Value', add, 'Array', controller)
        graph.add_link(get_local_controls1, 'Value', add1, 'Array', controller)
        graph.add_link(equals, 'Result', if3, 'Condition', controller)
        graph.add_link(equals, 'Result', if4, 'Condition', controller)
        graph.add_link(vetala_lib_get_item, 'Element', get_transform, 'Item', controller)
        graph.add_link(vetala_lib_get_item, 'Element', get_item_metadata1, 'Item', controller)
        graph.add_link(vetala_lib_get_item3, 'Element', item_exists1, 'Item', controller)
        graph.add_link(branch1, 'True', set_transform, 'ExecutePin', controller)
        graph.add_link(get_item_metadata1, 'Value', set_transform, 'Item', controller)
        graph.add_link(get_transform, 'Transform', set_transform, 'Value', controller)
        graph.add_link(vetala_lib_get_item4, 'Element', item_exists2, 'Item', controller)
        graph.add_link(item_exists2, 'Exists', not1, 'Value', controller)
        graph.add_link(not1, 'Result', branch1, 'Condition', controller)
        graph.add_link(at, 'Element', get_item_metadata2, 'Item', controller)
        graph.add_link(get_item_metadata2, 'Value', make_array, 'Values.0', controller)

        graph.set_pin(set_item_metadata, 'Name', 'SwitchChannel', controller)
        graph.set_pin(set_item_metadata, 'NameSpace', 'Self', controller)
        graph.set_pin(vetala_lib_control, 'increment', '0', controller)
        graph.set_pin(vetala_lib_control, 'sub_count', '0', controller)
        graph.set_pin(vetala_lib_control, 'sub_color', '((R=0,G=0,B=0,A=0.000000))', controller)
        graph.set_pin(set_item_metadata1, 'NameSpace', 'Self', controller)
        graph.set_pin(from_string, 'String', 'SwitchControl', controller)
        graph.set_pin(spawn_scale_float_animation_channel, 'MinimumValue', '0.000000', controller)
        graph.set_pin(spawn_scale_float_animation_channel, 'MaximumValue', '1.000000', controller)
        graph.set_pin(spawn_scale_float_animation_channel, 'LimitsEnabled', '(Enabled=(bMinimum=True,bMaximum=True))', controller)
        graph.set_pin(get_item_metadata, 'NameSpace', 'Self', controller)
        graph.set_pin(get_item_metadata, 'Default', '(Type=Bone,Name="None")', controller)
        graph.set_pin(get_float_channel, 'bInitial', 'False', controller)
        graph.set_pin(get_float_channel, 'CachedChannelHash', '0', controller)
        graph.set_pin(from_string3, 'String', 'SwitchControl', controller)
        graph.set_pin(if2, 'False', '0.000000', controller)
        graph.set_pin(equals, 'B', 'Default', controller)
        graph.set_pin(if3, 'True', 'Star4_Solid', controller)
        graph.set_pin(if4, 'True', '0.25000', controller)
        graph.set_pin(if4, 'False', '1.000000', controller)
        graph.set_pin(vetala_lib_get_item, 'index', '-1', controller)
        graph.set_pin(vetala_lib_get_item1, 'index', '-1', controller)
        graph.set_pin(vetala_lib_get_item2, 'index', '-1', controller)
        graph.set_pin(set_transform, 'Space', 'GlobalSpace', controller)
        graph.set_pin(set_transform, 'bInitial', 'False', controller)
        graph.set_pin(set_transform, 'Weight', '1.000000', controller)
        graph.set_pin(set_transform, 'bPropagateToChildren', 'True', controller)
        graph.set_pin(get_transform, 'Space', 'GlobalSpace', controller)
        graph.set_pin(get_transform, 'bInitial', 'False', controller)
        graph.set_pin(get_item_metadata1, 'Name', 'SwitchControl', controller)
        graph.set_pin(get_item_metadata1, 'NameSpace', 'Self', controller)
        graph.set_pin(get_item_metadata1, 'Default', '(Type=Bone,Name="None")', controller)
        graph.set_pin(make_array, 'Values', '((Type=None,Name="None"))', controller)
        graph.set_pin(get_item_metadata2, 'Name', 'SwitchControl', controller)
        graph.set_pin(get_item_metadata2, 'NameSpace', 'Self', controller)
        graph.set_pin(get_item_metadata2, 'Default', '(Type=Bone,Name="None")', controller)
        graph.set_pin(at, 'Index', '-1', controller)


class UnrealSpaceSwitch(UnrealUtil):

    def _use_mode(self):
        return True

    def _build_function_graph(self):
        super(UnrealSpaceSwitch, self)._build_function_graph()
        if not self.graph:
            return

        controller = self.function_controller
        library = graph.get_local_function_library()

        controller.add_local_variable_from_object_path(
            'local_parents',
            'TArray<FConstraintParent>',
            '/Script/ControlRig.ConstraintParent',
            ''
        )

        controller.add_local_variable_from_object_path(
            'switch_value',
            'int32',
            '',
            ''
        )

        controller.add_local_variable_from_object_path('current_item', 'FRigElementKey', '/Script/ControlRig.RigElementKey', '')

        entry = 'Entry'
        return1 = 'Return'
        switch = self.switch_node

        vetala_lib_string_to_index = controller.add_function_reference_node(library.find_function('vetalaLib_StringToIndex'), unreal.Vector2D(700.0, -351.0), 'vetalaLib_StringToIndex')
        vetala_lib_index_to_items = controller.add_function_reference_node(library.find_function('vetalaLib_IndexToItems'), unreal.Vector2D(928.0, -352.0), 'vetalaLib_IndexToItems')
        for_each = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayIterator(in Array,out Element,out Index,out Count,out Ratio)', unreal.Vector2D(1216.0, -368.0), 'For Each')
        get_parent = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyGetParent', 'Execute', unreal.Vector2D(1504.0, -576.0), 'Get Parent')
        spawn_transform_control = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyAddControlTransform', 'Execute', unreal.Vector2D(1968.0, -976.0), 'Spawn Transform Control')
        get_transform = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetTransform', 'Execute', unreal.Vector2D(1520.0, -288.0), 'Get Transform')
        set_item_metadata = controller.add_template_node('DISPATCH_RigDispatch_SetMetadata(in Item,in Name,in NameSpace,in Value,out Success)', unreal.Vector2D(3008.0, -688.0), 'Set Item Metadata')
        concat = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_NameConcat', 'Execute', unreal.Vector2D(1408.0, -816.0), 'Concat')
        vetala_lib_parent = controller.add_function_reference_node(library.find_function('vetalaLib_Parent'), unreal.Vector2D(3488.0, -832.0), 'vetalaLib_Parent')
        vetala_lib_get_item = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(2080.0, -416.0), 'vetalaLib_GetItem')
        item_exists = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_ItemExists', 'Execute', unreal.Vector2D(2336.0, -432.0), 'Item Exists')
        if1 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(2624.0, -416.0), 'If')
        num = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetNum(in Array,out Num)', unreal.Vector2D(2080.0, -128.0), 'Num')
        if2 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(2880.0, -368.0), 'If')
        get_attribute_control = controller.add_variable_node_from_object_path('attribute_control', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(1872.0, -80.0), 'Get attribute_control')
        equals = controller.add_template_node('DISPATCH_RigVMDispatch_CoreEquals(in A,in B,out Result)', unreal.Vector2D(2368.0, -192.0), 'Equals')
        vetala_lib_get_item1 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(2080.0, -288.0), 'vetalaLib_GetItem')
        spawn_integer_animation_channel = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyAddAnimationChannelInteger', 'Execute', unreal.Vector2D(3728.0, -528.0), 'Spawn Integer Animation Channel')
        replace = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_StringReplace', 'Execute', unreal.Vector2D(2752.0, 32.0), 'Replace')
        from_string = controller.add_template_node('DISPATCH_RigDispatch_FromString(in String,out Result)', unreal.Vector2D(3424.0, -320.0), 'From String')
        num1 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetNum(in Array,out Num)', unreal.Vector2D(3481.66455078125, -118.18206787109375), 'Num')
        get_parent1 = controller.add_variable_node_from_object_path('parent', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(3264.0, -64.0), 'Get parent')
        set_item_metadata1 = controller.add_template_node('DISPATCH_RigDispatch_SetMetadata(in Item,in Name,in NameSpace,in Value,out Success)', unreal.Vector2D(4240.0, -528.0), 'Set Item Metadata')
        equals1 = controller.add_template_node('DISPATCH_RigVMDispatch_CoreEquals(in A,in B,out Result)', unreal.Vector2D(1968.0, 832.0), 'Equals')
        branch = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_ControlFlowBranch', 'Execute', unreal.Vector2D(2192.0, 688.0), 'Branch')
        set_local_parents = controller.add_variable_node_from_object_path('local_parents', 'TArray<FConstraintParent>', '/Script/ControlRig.ConstraintParent', False, '()', unreal.Vector2D(2512.0, 656.0), 'Set local_parents')
        get_parent2 = controller.add_variable_node_from_object_path('parent', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(1264.0, 800.0), 'Get parent')
        concat1 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_StringConcat', 'Execute', unreal.Vector2D(3100.717041015625, -11.86328125), 'Concat')
        concat2 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_StringConcat', 'Execute', unreal.Vector2D(2864.0, -160.0), 'Concat')
        get_switch_value = controller.add_variable_node('switch_value', 'int32', None, True, '', unreal.Vector2D(1744.0, 672.0), 'Get switch_value')
        vetala_lib_string_to_index1 = controller.add_function_reference_node(library.find_function('vetalaLib_StringToIndex'), unreal.Vector2D(240.0, 1008.0), 'vetalaLib_StringToIndex')
        vetala_lib_get_item2 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(-112.0, 1648.0), 'vetalaLib_GetItem')
        item_exists1 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_ItemExists', 'Execute', unreal.Vector2D(144.0, 1632.0), 'Item Exists')
        num2 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetNum(in Array,out Num)', unreal.Vector2D(-112.0, 1936.0), 'Num')
        get_attribute_control1 = controller.add_variable_node_from_object_path('attribute_control', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(-512.0, 1792.0), 'Get attribute_control')
        equals2 = controller.add_template_node('DISPATCH_RigVMDispatch_CoreEquals(in A,in B,out Result)', unreal.Vector2D(176.0, 1872.0), 'Equals')
        vetala_lib_get_item3 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(-112.0, 1776.0), 'vetalaLib_GetItem')
        for_each1 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayIterator(in Array,out Element,out Index,out Count,out Ratio)', unreal.Vector2D(1056.0, 1040.0), 'For Each')
        vetala_lib_index_to_items1 = controller.add_function_reference_node(library.find_function('vetalaLib_IndexToItems'), unreal.Vector2D(496.0, 1024.0), 'vetalaLib_IndexToItems')
        position_constraint = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_PositionConstraintLocalSpaceOffset', 'Execute', unreal.Vector2D(3424.0, 1216.0), 'Position Constraint')
        get_local_parents = controller.add_variable_node_from_object_path('local_parents', 'TArray<FConstraintParent>', '/Script/ControlRig.ConstraintParent', True, '()', unreal.Vector2D(2672.0, 1808.0), 'Get local_parents')
        parent_constraint = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_ParentConstraint', 'Execute', unreal.Vector2D(3936.0, 1824.0), 'Parent Constraint')
        branch1 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_ControlFlowBranch', 'Execute', unreal.Vector2D(2592.0, 1280.0), 'Branch')
        get_translate = controller.add_variable_node('translate', 'bool', None, True, '', unreal.Vector2D(2848.0, 2080.0), 'Get translate')
        rotation_constraint = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_RotationConstraintLocalSpaceOffset', 'Execute', unreal.Vector2D(3824.0, 1312.0), 'Rotation Constraint')
        scale_constraint = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_ScaleConstraintLocalSpaceOffset', 'Execute', unreal.Vector2D(4272.0, 1376.0), 'Scale Constraint')
        get_item_metadata = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(2352.0, 1584.0), 'Get Item Metadata')
        from_string1 = controller.add_template_node('DISPATCH_RigDispatch_FromString(in String,out Result)', unreal.Vector2D(2080.0, 1808.0), 'From String')
        if3 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(432.0, 1648.0), 'If')
        if4 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(688.0, 1696.0), 'If')
        get_item_metadata1 = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(976.0, 1776.0), 'Get Item Metadata')
        get_int_channel = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetIntAnimationChannelFromItem', 'Execute', unreal.Vector2D(1328.0, 1792.0), 'Get Int Channel')
        make_array = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayMake(in Values,out Array)', unreal.Vector2D(2192.0, 912.0), 'Make Array')
        for_each2 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayIterator(in Array,out Element,out Index,out Count,out Ratio)', unreal.Vector2D(1488.0, 768.0), 'For Each')
        get_rotate = controller.add_variable_node('rotate', 'bool', None, True, '', unreal.Vector2D(2848.0, 2176.0), 'Get rotate')
        get_scale = controller.add_variable_node('scale', 'bool', None, True, '', unreal.Vector2D(2848.0, 2272.0), 'Get scale')
        set_switch_value = controller.add_variable_node('switch_value', 'int32', None, False, '', unreal.Vector2D(1360.0, 1120.0), 'Set switch_value')
        set_current_item = controller.add_variable_node_from_object_path('current_item', 'FRigElementKey', '/Script/ControlRig.RigElementKey', False, '', unreal.Vector2D(1360.0, 1280.0), 'Set current_item')
        get_current_item = controller.add_variable_node_from_object_path('current_item', 'FRigElementKey', '/Script/ControlRig.RigElementKey', True, '', unreal.Vector2D(2083.29638671875, 1585.66015625), 'Get current_item')
        get_use_child_pivot = controller.add_variable_node('use_child_pivot', 'bool', None, True, '', unreal.Vector2D(2304.0, 1376.0), 'Get use_child_pivot')

        controller.resolve_wild_card_pin(f'{for_each.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{concat.get_node_path()}.Result', 'FName', 'None')
        controller.resolve_wild_card_pin(f'{if1.get_node_path()}.Result', 'FRigElementKey', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{num.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{if2.get_node_path()}.Result', 'FRigElementKey', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{equals.get_node_path()}.A', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{equals.get_node_path()}.B', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{num1.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{equals1.get_node_path()}.A', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{equals1.get_node_path()}.B', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{concat1.get_node_path()}.Result', 'FString', 'None')
        controller.resolve_wild_card_pin(f'{concat2.get_node_path()}.Result', 'FString', 'None')
        controller.resolve_wild_card_pin(f'{num2.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{equals2.get_node_path()}.A', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{equals2.get_node_path()}.B', 'int32', 'None')
        controller.resolve_wild_card_pin(f'{for_each1.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{if3.get_node_path()}.Result', 'FRigElementKey', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{if4.get_node_path()}.Result', 'FRigElementKey', '/Script/ControlRig.RigElementKey')
        controller.resolve_wild_card_pin(f'{make_array.get_node_path()}.Array', 'TArray<FConstraintParent>', '/Script/ControlRig.ConstraintParent')
        controller.resolve_wild_card_pin(f'{for_each2.get_node_path()}.Array', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey')

        controller.set_array_pin_size(f'{n(make_array)}.Values', 1)

        graph.add_link(switch, 'Completed', return1, 'ExecuteContext', controller)
        graph.add_link(switch, 'Cases.0', vetala_lib_string_to_index, 'ExecuteContext', controller)
        graph.add_link(vetala_lib_string_to_index, 'ExecuteContext', vetala_lib_index_to_items, 'ExecuteContext', controller)
        graph.add_link(vetala_lib_index_to_items, 'ExecuteContext', for_each, 'ExecuteContext', controller)
        graph.add_link(for_each, 'ExecuteContext', spawn_transform_control, 'ExecutePin', controller)
        graph.add_link(spawn_transform_control, 'ExecutePin', set_item_metadata, 'ExecuteContext', controller)
        graph.add_link(set_item_metadata, 'ExecuteContext', vetala_lib_parent, 'ExecuteContext', controller)
        graph.add_link(vetala_lib_parent, 'ExecuteContext', spawn_integer_animation_channel, 'ExecutePin', controller)
        graph.add_link(spawn_integer_animation_channel, 'ExecutePin', set_item_metadata1, 'ExecuteContext', controller)
        graph.add_link(for_each2, 'ExecuteContext', branch, 'ExecuteContext', controller)
        graph.add_link(branch, 'True', set_local_parents, 'ExecuteContext', controller)
        graph.add_link(switch, 'Cases.1', vetala_lib_string_to_index1, 'ExecuteContext', controller)
        graph.add_link(vetala_lib_string_to_index1, 'ExecuteContext', vetala_lib_index_to_items1, 'ExecuteContext', controller)
        graph.add_link(vetala_lib_index_to_items1, 'ExecuteContext', for_each1, 'ExecuteContext', controller)
        graph.add_link(for_each1, 'ExecuteContext', set_current_item, 'ExecuteContext', controller)
        graph.add_link(for_each2, 'Completed', branch1, 'ExecuteContext', controller)
        graph.add_link(set_switch_value, 'ExecuteContext', for_each2, 'ExecuteContext', controller)
        graph.add_link(set_current_item, 'ExecuteContext', set_switch_value, 'ExecuteContext', controller)
        graph.add_link('Entry', 'child_indices', vetala_lib_string_to_index, 'string', controller)
        graph.add_link(vetala_lib_string_to_index, 'index', vetala_lib_index_to_items, 'Index', controller)
        graph.add_link('Entry', 'children', vetala_lib_index_to_items, 'Items', controller)
        graph.add_link(vetala_lib_index_to_items, 'Result', for_each, 'Array', controller)
        graph.add_link(for_each, 'Element', get_parent, 'Child', controller)
        graph.add_link(for_each, 'Element', get_transform, 'Item', controller)
        graph.add_link(for_each, 'Element', set_item_metadata, 'Item', controller)
        graph.add_link(for_each, 'Element', vetala_lib_parent, 'Child', controller)
        graph.add_link(for_each, 'Element', if2, 'True', controller)
        graph.add_link(for_each, 'Element.Name', concat, 'B', controller)
        graph.add_link(for_each, 'Index', vetala_lib_get_item, 'index', controller)
        graph.add_link(get_parent, 'Parent', spawn_transform_control, 'Parent', controller)
        graph.add_link(concat, 'Result', spawn_transform_control, 'Name', controller)
        graph.add_link(spawn_transform_control, 'Item', set_item_metadata, 'Value', controller)
        graph.add_link(spawn_transform_control, 'Item', vetala_lib_parent, 'Parent', controller)
        graph.add_link(get_transform, 'Transform', spawn_transform_control, 'InitialValue', controller)
        graph.add_link(get_attribute_control, 'Value', vetala_lib_get_item, 'Array', controller)
        graph.add_link(vetala_lib_get_item, 'Element', item_exists, 'Item', controller)
        graph.add_link(vetala_lib_get_item, 'Element', if1, 'True', controller)
        graph.add_link(item_exists, 'Exists', if1, 'Condition', controller)
        graph.add_link(vetala_lib_get_item1, 'Element', if1, 'False', controller)
        graph.add_link(if1, 'Result', if2, 'False', controller)
        graph.add_link(get_attribute_control, 'Value', num, 'Array', controller)
        graph.add_link(num, 'Num', 'Equals', 'A', controller)
        graph.add_link(equals, 'Result', if2, 'Condition', controller)
        graph.add_link(if2, 'Result', spawn_integer_animation_channel, 'Parent', controller)
        graph.add_link(if2, 'Result', set_item_metadata1, 'Item', controller)
        graph.add_link(get_attribute_control, 'Value', vetala_lib_get_item1, 'Array', controller)
        graph.add_link(num, 'Num', equals, 'A', controller)
        graph.add_link(from_string, 'Result', spawn_integer_animation_channel, 'Name', controller)
        graph.add_link(spawn_integer_animation_channel, 'Item', set_item_metadata1, 'Value', controller)
        graph.add_link('Entry', 'default_value', spawn_integer_animation_channel, 'InitialValue', controller)
        graph.add_link('Num_1', 'Num', spawn_integer_animation_channel, 'MaximumValue', controller)
        graph.add_link('Entry', 'names', replace, 'Name', controller)
        graph.add_link(replace, 'Result', concat1, 'B', controller)
        graph.add_link(concat1, 'Result', from_string, 'String', controller)
        graph.add_link(get_parent1, 'Value', num1, 'Array', controller)
        graph.add_link(num1, 'Num', 'Spawn Integer Animation Channel', 'MaximumValue', controller)
        graph.add_link(for_each2, 'Index', equals1, 'A', controller)
        graph.add_link(get_switch_value, 'Value', equals1, 'B', controller)
        graph.add_link(equals1, 'Result', branch, 'Condition', controller)
        graph.add_link(make_array, 'Array', set_local_parents, 'Value', controller)
        graph.add_link(get_parent2, 'Value', for_each2, 'Array', controller)
        graph.add_link(concat2, 'Result', concat1, 'A', controller)
        graph.add_link('Entry', 'attribute_name', concat2, 'A', controller)
        graph.add_link('Entry', 'child_indices', vetala_lib_string_to_index1, 'string', controller)
        graph.add_link(vetala_lib_string_to_index1, 'index', vetala_lib_index_to_items1, 'Index', controller)
        graph.add_link(get_attribute_control1, 'Value', vetala_lib_get_item2, 'Array', controller)
        graph.add_link(for_each1, 'Index', vetala_lib_get_item2, 'index', controller)
        graph.add_link(vetala_lib_get_item2, 'Element', item_exists1, 'Item', controller)
        graph.add_link(vetala_lib_get_item2, 'Element', if3, 'True', controller)
        graph.add_link(item_exists1, 'Exists', if3, 'Condition', controller)
        graph.add_link(get_attribute_control1, 'Value', num2, 'Array', controller)
        graph.add_link(num2, 'Num', 'Equals_1', 'A', controller)
        graph.add_link(get_attribute_control1, 'Value', vetala_lib_get_item3, 'Array', controller)
        graph.add_link('Num_2', 'Num', equals2, 'A', controller)
        graph.add_link(equals2, 'Result', if4, 'Condition', controller)
        graph.add_link(vetala_lib_get_item3, 'Element', if3, 'False', controller)
        graph.add_link(vetala_lib_index_to_items1, 'Result', for_each1, 'Array', controller)
        graph.add_link(for_each1, 'Element', if4, 'True', controller)
        graph.add_link(for_each1, 'Element', set_current_item, 'Value', controller)
        graph.add_link('Entry', 'children', vetala_lib_index_to_items1, 'Items', controller)
        graph.add_link(branch1, 'True', position_constraint, 'ExecutePin', controller)
        graph.add_link(position_constraint, 'ExecutePin', rotation_constraint, 'ExecutePin', controller)
        graph.add_link(get_item_metadata, 'Value', position_constraint, 'Child', controller)
        graph.add_link(get_local_parents, 'Value', position_constraint, 'Parents', controller)
        graph.add_link(get_local_parents, 'Value', parent_constraint, 'Parents', controller)
        graph.add_link(get_local_parents, 'Value', rotation_constraint, 'Parents', controller)
        graph.add_link(get_local_parents, 'Value', scale_constraint, 'Parents', controller)
        graph.add_link(branch1, 'False', parent_constraint, 'ExecutePin', controller)
        graph.add_link(get_item_metadata, 'Value', parent_constraint, 'Child', controller)
        graph.add_link(get_use_child_pivot, 'Value', branch1, 'Condition', controller)
        graph.add_link(rotation_constraint, 'ExecutePin', scale_constraint, 'ExecutePin', controller)
        graph.add_link(get_item_metadata, 'Value', rotation_constraint, 'Child', controller)
        graph.add_link(get_item_metadata, 'Value', scale_constraint, 'Child', controller)
        graph.add_link(get_current_item, 'Value', get_item_metadata, 'Item', controller)
        graph.add_link(from_string1, 'Result', get_item_metadata, 'Name', controller)
        graph.add_link(if3, 'Result', if4, 'False', controller)
        graph.add_link(if4, 'Result', get_item_metadata1, 'Item', controller)
        graph.add_link(get_item_metadata1, 'Value', get_int_channel, 'Item', controller)
        graph.add_link(get_int_channel, 'Value', set_switch_value, 'Value', controller)
        graph.add_link(get_translate, 'Value', position_constraint, 'Filter.bX', controller)
        graph.add_link(get_translate, 'Value', position_constraint, 'Filter.bY', controller)
        graph.add_link(get_translate, 'Value', position_constraint, 'Filter.bZ', controller)
        graph.add_link(get_rotate, 'Value', rotation_constraint, 'Filter.bX', controller)
        graph.add_link(get_rotate, 'Value', rotation_constraint, 'Filter.bY', controller)
        graph.add_link(get_rotate, 'Value', rotation_constraint, 'Filter.bZ', controller)
        graph.add_link(get_scale, 'Value', scale_constraint, 'Filter.bX', controller)
        graph.add_link(get_scale, 'Value', scale_constraint, 'Filter.bY', controller)
        graph.add_link(get_scale, 'Value', scale_constraint, 'Filter.bZ', controller)
        graph.add_link(get_translate, 'Value', parent_constraint, 'Filter.TranslationFilter.bX', controller)
        graph.add_link(get_translate, 'Value', parent_constraint, 'Filter.TranslationFilter.bY', controller)
        graph.add_link(get_translate, 'Value', parent_constraint, 'Filter.TranslationFilter.bZ', controller)
        graph.add_link(get_rotate, 'Value', parent_constraint, 'Filter.RotationFilter.bX', controller)
        graph.add_link(get_rotate, 'Value', parent_constraint, 'Filter.RotationFilter.bY', controller)
        graph.add_link(get_rotate, 'Value', parent_constraint, 'Filter.RotationFilter.bZ', controller)
        graph.add_link(get_scale, 'Value', parent_constraint, 'Filter.ScaleFilter.bX', controller)
        graph.add_link(get_scale, 'Value', parent_constraint, 'Filter.ScaleFilter.bY', controller)
        graph.add_link(get_scale, 'Value', parent_constraint, 'Filter.ScaleFilter.bZ', controller)
        graph.add_link(for_each2, 'Element', make_array, 'Values.0.Item', controller)

        graph.set_pin(get_parent, 'bDefaultParent', 'True', controller)
        graph.set_pin(spawn_transform_control, 'OffsetTransform', '(Rotation=(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=1.000000,Y=1.000000,Z=1.000000))', controller)
        graph.set_pin(spawn_transform_control, 'OffsetSpace', 'LocalSpace', controller)
        graph.set_pin(spawn_transform_control, 'Settings', '(InitialSpace=GlobalSpace,bUsePreferredRotationOrder=False,PreferredRotationOrder=YZX,Limits=(LimitTranslationX=(bMinimum=False,bMaximum=False),LimitTranslationY=(bMinimum=False,bMaximum=False),LimitTranslationZ=(bMinimum=False,bMaximum=False),LimitPitch=(bMinimum=False,bMaximum=False),LimitYaw=(bMinimum=False,bMaximum=False),LimitRoll=(bMinimum=False,bMaximum=False),LimitScaleX=(bMinimum=False,bMaximum=False),LimitScaleY=(bMinimum=False,bMaximum=False),LimitScaleZ=(bMinimum=False,bMaximum=False),MinValue=(Location=(X=-100.000000,Y=-100.000000,Z=-100.000000),Rotation=(Pitch=-180.000000,Yaw=-180.000000,Roll=-180.000000),Scale=(X=0.000000,Y=0.000000,Z=0.000000)),MaxValue=(Location=(X=100.000000,Y=100.000000,Z=100.000000),Rotation=(Pitch=180.000000,Yaw=180.000000,Roll=180.000000),Scale=(X=10.000000,Y=10.000000,Z=10.000000)),bDrawLimits=True),Shape=(bVisible=False,Name="Box_Thin",Color=(R=1.000000,G=0.000000,B=0.000000,A=1.000000),Transform=(Rotation=(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=1.000000,Y=1.000000,Z=1.000000))),Proxy=(bIsProxy=True,ShapeVisibility=BasedOnSelection),FilteredChannels=(),DisplayName="None")', controller)
        graph.set_pin(get_transform, 'Space', 'GlobalSpace', controller)
        graph.set_pin(get_transform, 'bInitial', 'False', controller)
        graph.set_pin(set_item_metadata, 'Name', 'anchor', controller)
        graph.set_pin(set_item_metadata, 'NameSpace', 'Self', controller)
        graph.set_pin(concat, 'A', 'anchor_', controller)
        graph.set_pin(equals, 'B', '0', controller)
        graph.set_pin(vetala_lib_get_item1, 'index', '-1', controller)
        graph.set_pin(spawn_integer_animation_channel, 'MinimumValue', '0', controller)
        graph.set_pin(spawn_integer_animation_channel, 'LimitsEnabled', '(Enabled=(bMinimum=True,bMaximum=True))', controller)
        graph.set_pin(replace, 'Old', ',', controller)
        graph.set_pin(replace, 'New', ' ', controller)
        graph.set_pin(set_item_metadata1, 'Name', 'SpaceChannel', controller)
        graph.set_pin(set_item_metadata1, 'NameSpace', 'Self', controller)
        graph.set_pin(concat2, 'B', ' ', controller)
        graph.set_pin(equals2, 'B', '0', controller)
        graph.set_pin(vetala_lib_get_item3, 'index', '-1', controller)
        graph.set_pin(position_constraint, 'bMaintainOffset', 'True', controller)
        graph.set_pin(position_constraint, 'Filter', '(bX=True,bY=True,bZ=True)', controller)
        graph.set_pin(position_constraint, 'Weight', '1.000000', controller)
        graph.set_pin(parent_constraint, 'bMaintainOffset', 'True', controller)
        graph.set_pin(parent_constraint, 'Filter', '(TranslationFilter=(bX=True,bY=True,bZ=True),RotationFilter=(bX=True,bY=True,bZ=True),ScaleFilter=(bX=True,bY=True,bZ=True))', controller)
        graph.set_pin(parent_constraint, 'AdvancedSettings', '(InterpolationType=Average,RotationOrderForFilter=XZY)', controller)
        graph.set_pin(parent_constraint, 'Weight', '1.000000', controller)
        graph.set_pin(rotation_constraint, 'bMaintainOffset', 'True', controller)
        graph.set_pin(rotation_constraint, 'Filter', '(bX=True,bY=True,bZ=True)', controller)
        graph.set_pin(rotation_constraint, 'AdvancedSettings', '(InterpolationType=Average,RotationOrderForFilter=XZY)', controller)
        graph.set_pin(rotation_constraint, 'Weight', '1.000000', controller)
        graph.set_pin(scale_constraint, 'bMaintainOffset', 'True', controller)
        graph.set_pin(scale_constraint, 'Filter', '(bX=True,bY=True,bZ=True)', controller)
        graph.set_pin(scale_constraint, 'Weight', '1.000000', controller)
        graph.set_pin(get_item_metadata, 'NameSpace', 'Self', controller)
        graph.set_pin(get_item_metadata, 'Default', '(Type=Bone,Name="None")', controller)
        graph.set_pin(from_string1, 'String', 'anchor', controller)
        graph.set_pin(get_item_metadata1, 'Name', 'SpaceChannel', controller)
        graph.set_pin(get_item_metadata1, 'NameSpace', 'Self', controller)
        graph.set_pin(get_item_metadata1, 'Default', '(Type=Bone,Name="None")', controller)
        graph.set_pin(get_int_channel, 'bInitial', 'False', controller)
        graph.set_pin(make_array, 'Values', '((Item=(Type=Bone,Name="None"),Weight=1.000000))', controller)
