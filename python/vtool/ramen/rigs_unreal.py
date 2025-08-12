# Copyright (C) 2024 Louis Vottero louis.vot@gmail.com    All rights reserved.

import traceback
import copy

from . import rigs
from . import util as util_ramen

from vtool import util
from vtool import util_file
from vtool.maya_lib.core import get_uuid

in_unreal = util.in_unreal

if in_unreal:
    import unreal
    from .. import unreal_lib
    from ..unreal_lib import graph
    from ..unreal_lib import lib_function


def n(unreal_node):
    """
    returns the node path
    """
    if not in_unreal:
        return
    if unreal_node is None:
        return
    return unreal_node.get_node_path()


cached_library_function_names = graph.get_vetala_lib_function_names(lib_function.VetalaLib())


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
        self._cached_library_function_names = cached_library_function_names

    def _use_mode(self):
        return False

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
        if self._use_mode():
            self.function_controller.add_exposed_pin('mode', unreal.RigVMPinDirection.INPUT, 'int32', 'None', '')

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
            self.function_controller.add_exposed_pin(name, unreal.RigVMPinDirection.INPUT, 'FString', 'None', str(value[0]))

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

        if self._use_mode():
            self.forward_controller.set_pin_default_value(f'{n(self.forward_node)}.mode', '1', False)

    def _add_backward_node_to_graph(self):

        controller = self.backward_controller

        function_node = controller.add_function_reference_node(self.function, unreal.Vector2D(100, 100),
                                                               self.function.get_node_path())
        self.backward_node = function_node

        controller.set_pin_default_value(f'{n(function_node)}.uuid', self.rig.uuid, False)

        if self._use_mode():
            self.backward_controller.set_pin_default_value(f'{n(self.backward_node)}.mode', '2', False)

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

            for controller, pin in zip(controllers, pins):
                controller.set_pin_default_value(pin, str(value), False)

        if value_type == rigs.AttrType.COLOR:
            self._reset_array(name, value)

            if not value:
                return

            for controller, pin in zip(controllers, pins):
                for inc, color in enumerate(value):
                    controller.set_array_pin_size(pin, len(value))
                    controller.set_pin_default_value(f'{pin}.{inc}.R', str(color[0]), True)
                    controller.set_pin_default_value(f'{pin}.{inc}.G', str(color[1]), True)
                    controller.set_pin_default_value(f'{pin}.{inc}.B', str(color[2]), True)
                    controller.set_pin_default_value(f'{pin}.{inc}.A', str(color[3]), True)

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

    def _build_entry(self):
        controller = self.function_controller

        mode = controller.add_template_node('DISPATCH_RigVMDispatch_SwitchInt32(in Index)',
                                                            unreal.Vector2D(225, -160),
                                                            'DISPATCH_RigVMDispatch_SwitchInt32')
        controller.insert_array_pin(f'{n(mode)}.Cases', -1, '')
        controller.insert_array_pin(f'{n(mode)}.Cases', -1, '')

        graph.add_link('Entry', 'mode', mode, 'Index', controller)
        graph.add_link('Entry', 'ExecuteContext', mode, 'ExecuteContext', controller)

        graph.add_link(mode, 'Completed', 'Return', 'ExecuteContext', controller)

        controller.set_node_position_by_name('Return', unreal.Vector2D(4000, 0))
        self.mode = mode

    def _build_function_graph(self):

        if self._use_mode():
            self._build_entry()

    def add_library_node(self, name, controller, x, y):
        node = self.library_functions[name]
        added_node = controller.add_function_reference_node(node,
                                                         unreal.Vector2D(x, y),
                                                         n(node))

        return added_node

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

        if self.construct_controller:
            if self.construct_node:
                if not n(self.construct_node):
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

    @util_ramen.decorator_undo('Build')
    def build(self):
        super(UnrealUtil, self).build()

        if not in_unreal:
            return

        if not self.graph:
            util.warning('No control rig for Unreal rig')
            return

        self.load()

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

    def _init_rig_use_attributes(self):
        super(UnrealUtilRig, self)._init_rig_use_attributes()

        self.function_controller.add_exposed_pin('layer', unreal.RigVMPinDirection.INPUT, 'int32', 'None', '')
        self.function_controller.add_exposed_pin('switch', unreal.RigVMPinDirection.INPUT, 'int32', 'None', '')

    def _build_entry(self):

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

        self.mode = mode

    def _build_return(self):
        controller = self.function_controller
        library = graph.get_local_function_library()
        controller.add_local_variable_from_object_path('local_controls', 'TArray<FRigElementKey>',
                                                                     '/Script/ControlRig.RigElementKey', '')

        get_uuid = controller.add_variable_node('uuid', 'FString', None, True, '', unreal.Vector2D(3136.0, -112.0), 'Get uuid')
        get_local_controls = controller.add_variable_node_from_object_path('local_controls', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(3136.0, 32.0), 'Get local_controls')
        vetala_lib_output_rig_controls = controller.add_function_reference_node(library.find_function('vetalaLib_OutputRigControls'), unreal.Vector2D(3392.0, -64.0), 'vetalaLib_OutputRigControls')

        graph.add_link('DISPATCH_RigVMDispatch_SwitchInt32', 'Completed', vetala_lib_output_rig_controls, 'ExecuteContext', controller)

        graph.add_link(get_uuid, 'Value', vetala_lib_output_rig_controls, 'uuid', controller)
        graph.add_link(get_local_controls, 'Value', vetala_lib_output_rig_controls, 'controls', controller)

        graph.add_link(vetala_lib_output_rig_controls, 'out_controls', 'Return', 'controls', controller)
        graph.add_link(vetala_lib_output_rig_controls, 'ExecuteContext', 'Return', 'ExecuteContext', controller)

        controller.set_node_position_by_name('Return', unreal.Vector2D(4000, 0))

    def _build_function_graph(self):
        super(UnrealUtilRig, self)._build_function_graph()

        self._build_return()

        self._build_function_construct_graph()
        self._build_function_forward_graph()
        self._build_function_backward_graph()

    def _build_function_construct_graph(self):
        return

    def _build_function_forward_graph(self):
        return

    def _build_function_backward_graph(self):
        return


class UnrealFkRig(UnrealUtilRig):

    def _build_function_construct_graph(self):
        controller = self.function_controller
        library = graph.get_local_function_library()

        controller.add_local_variable_from_object_path('local_controls', 'TArray<FRigElementKey>',
                                                                     '/Script/ControlRig.RigElementKey', '')

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

        graph.add_link('DISPATCH_RigVMDispatch_SwitchInt32', 'Cases.0', for_each, 'ExecuteContext', controller)
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

    def _build_function_forward_graph(self):
        controller = self.function_controller
        library = graph.get_local_function_library()

        for_each = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayIterator(in Array,out Element,out Index,out Count,out Ratio)', unreal.Vector2D(928.0, 96.0), 'For Each')
        get_item_metadata = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(1328.0, 196.0), 'Get Item Metadata')
        get_control_layer = controller.add_variable_node('control_layer', 'FName', None, True, '', unreal.Vector2D(1128.0, 246.0), 'Get control_layer')
        get_transform = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetTransform', 'Execute', unreal.Vector2D(1628.0, 196.0), 'Get Transform')
        set_transform = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_SetTransform', 'Execute', unreal.Vector2D(2078.0, 96.0), 'Set Transform')
        vetala_lib_rig_layer_solve = controller.add_function_reference_node(library.find_function('vetalaLib_rigLayerSolve'), unreal.Vector2D(2578.0, 96.0), 'vetalaLib_rigLayerSolve')
        branch = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_ControlFlowBranch', 'Execute', unreal.Vector2D(720.0, 96.0), 'Branch')

        graph.add_link(branch, 'True', for_each, 'ExecuteContext', controller)
        graph.add_link(for_each, 'ExecuteContext', set_transform, 'ExecuteContext', controller)
        graph.add_link(for_each, 'Completed', vetala_lib_rig_layer_solve, 'ExecuteContext', controller)
        graph.add_link('DISPATCH_RigVMDispatch_SwitchInt32', 'Cases.1', branch, 'ExecuteContext', controller)
        graph.add_link('Entry', 'joints', for_each, 'Array', controller)
        graph.add_link(for_each, 'Element', get_item_metadata, 'Item', controller)
        graph.add_link(for_each, 'Element', set_transform, 'Item', controller)
        graph.add_link(get_control_layer, 'Value', get_item_metadata, 'Name', controller)
        graph.add_link(get_item_metadata, 'Value', get_transform, 'Item', controller)
        graph.add_link(get_transform, 'Transform', set_transform, 'Value', controller)
        graph.add_link('Entry', 'joints', vetala_lib_rig_layer_solve, 'Joints', controller)
        graph.add_link('Entry', 'attach', branch, 'Condition', controller)

        graph.set_pin(get_item_metadata, 'NameSpace', 'Self', controller)
        graph.set_pin(get_item_metadata, 'Default', '(Type=Bone,Name="None")', controller)
        graph.set_pin(get_transform, 'Space', 'GlobalSpace', controller)
        graph.set_pin(get_transform, 'bInitial', 'False', controller)
        graph.set_pin(set_transform, 'Space', 'GlobalSpace', controller)
        graph.set_pin(set_transform, 'bInitial', 'False', controller)
        graph.set_pin(set_transform, 'Weight', '1.000000', controller)
        graph.set_pin(set_transform, 'bPropagateToChildren', 'True', controller)

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

    def _build_controls(self, controller, library):

        vetala_lib_find_pole_vector = controller.add_function_reference_node(library.find_function('vetalaLib_findPoleVector'), unreal.Vector2D(4704.0, -1600.0), 'vetalaLib_findPoleVector')
        for_each = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayIterator(in Array,out Element,out Index,out Count,out Ratio)', unreal.Vector2D(1412.0, -1696.0), 'For Each')
        vetala_lib_control = self._create_control(controller, 2412.0, -1746.0)
        vetala_lib_get_parent = controller.add_function_reference_node(library.find_function('vetalaLib_GetParent'), unreal.Vector2D(1824.0, -1904.0), 'vetalaLib_GetParent')
        vetala_lib_get_joint_description = controller.add_function_reference_node(library.find_function('vetalaLib_GetJointDescription'), unreal.Vector2D(1912.0, -1580.0), 'vetalaLib_GetJointDescription')
        set_item_metadata = controller.add_template_node('DISPATCH_RigDispatch_SetMetadata(in Item,in Name,in NameSpace,in Value,out Success)', unreal.Vector2D(2912.0, -1896.0), 'Set Item Metadata')
        get_control_layer = controller.add_variable_node('control_layer', 'FName', None, True, '', unreal.Vector2D(1240.0, -1836.0), 'Get control_layer')
        equals = controller.add_template_node('DISPATCH_RigVMDispatch_CoreEquals(in A,in B,out Result)', unreal.Vector2D(1592.0, -1900.0), 'Equals')
        get_description = controller.add_variable_node('description', 'FString', None, True, '', unreal.Vector2D(1752.0, -1088.0), 'Get description')
        get_use_joint_name = controller.add_variable_node('use_joint_name', 'bool', None, True, '', unreal.Vector2D(1752.0, -988.0), 'Get use_joint_name')
        get_joint_token = controller.add_variable_node('joint_token', 'FString', None, True, '', unreal.Vector2D(1412.0, -1446.0), 'Get joint_token')
        if1 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(2162.0, -1146.0), 'If')
        get_world = controller.add_variable_node('world', 'bool', None, True, '', unreal.Vector2D(1160.0, -1292.0), 'Get world')
        get_mirror = controller.add_variable_node('mirror', 'bool', None, True, '', unreal.Vector2D(1160.0, -1192.0), 'Get mirror')
        add = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayAdd(io Array,in Element,out Index)', unreal.Vector2D(3344.0, -1920.0), 'Add')
        get_local_controls = controller.add_variable_node_from_object_path('local_controls', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(2696.0, -1724.0), 'Get local_controls')
        get_local_controls1 = controller.add_variable_node_from_object_path('local_controls', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(3976.0, -908.0), 'Get local_controls')
        get_pole_vector_shape = controller.add_variable_node('pole_vector_shape', 'FString', None, True, '', unreal.Vector2D(3012.0, -1471.0), 'Get pole_vector_shape')
        from_string = controller.add_template_node('DISPATCH_RigDispatch_FromString(in String,out Result)', unreal.Vector2D(3212.0, -1446.0), 'From String')
        shape_exists = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_ShapeExists', 'Execute', unreal.Vector2D(3412.0, -1446.0), 'Shape Exists')
        if2 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(3336.0, -1644.0), 'If')
        set_shape_settings = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchySetShapeSettings', 'Execute', unreal.Vector2D(3612.0, -1546.0), 'Set Shape Settings')
        vetala_lib_parent = controller.add_function_reference_node(library.find_function('vetalaLib_Parent'), unreal.Vector2D(4012.0, -1446.0), 'vetalaLib_Parent')
        vetala_lib_parent1 = controller.add_function_reference_node(library.find_function('vetalaLib_Parent'), unreal.Vector2D(4312.0, -1246.0), 'vetalaLib_Parent')
        get_color = controller.add_variable_node_from_object_path('color', 'TArray<FLinearColor>', '/Script/CoreUObject.LinearColor', True, '()', unreal.Vector2D(3012.0, -1396.0), 'Get color')
        at = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(3312.0, -1346.0), 'At')
        at1 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(3384.0, -1180.0), 'At')
        at2 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(3384.0, -1052.0), 'At')
        at3 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(3384.0, -892.0), 'At')
        get_shape_scale = controller.add_variable_node_from_object_path('shape_scale', 'TArray<FVector>', '/Script/CoreUObject.Vector', True, '()', unreal.Vector2D(2612.0, -1546.0), 'Get shape_scale')
        at4 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(2762.0, -1546.0), 'At')
        multiply = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathVectorMul', 'Execute', unreal.Vector2D(2912.0, -1546.0), 'Multiply')
        get_joints = controller.add_variable_node_from_object_path('joints', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(3784.0, -1708.0), 'Get joints')
        at5 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(4056.0, -1812.0), 'At')
        at6 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(4056.0, -1712.0), 'At')
        at7 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(4056.0, -1612.0), 'At')
        get_pole_vector_offset = controller.add_variable_node('pole_vector_offset', 'float', None, True, '', unreal.Vector2D(4312.0, -1696.0), 'Get pole_vector_offset')
        set_translation = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_SetTranslation', 'Execute', unreal.Vector2D(5112.0, -1548.0), 'Set Translation')
        greater = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathIntGreater', 'Execute', unreal.Vector2D(704.0, -1712.0), 'Greater')
        if3 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(904.0, -1612.0), 'If')
        spawn_null = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyAddNull', 'Execute', unreal.Vector2D(5904.0, -1920.0), 'Spawn Null')
        if4 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(5128.0, -684.0), 'If')
        get_item_array_metadata = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(4664.0, -700.0), 'Get Item Array Metadata')
        vetala_lib_get_item = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(5400.0, -732.0), 'vetalaLib_GetItem')
        get_transform = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetTransform', 'Execute', unreal.Vector2D(5704.0, -1308.0), 'Get Transform')
        get_local_ik = controller.add_variable_node_from_object_path('local_ik', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(6104.0, -1340.0), 'Get local_ik')
        add1 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayAdd(io Array,in Element,out Index)', unreal.Vector2D(6264.0, -1628.0), 'Add')
        num = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetNum(in Array,out Num)', unreal.Vector2D(4824.0, -492.0), 'Num')
        greater1 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathIntGreater', 'Execute', unreal.Vector2D(4984.0, -540.0), 'Greater')
        get_joints1 = controller.add_variable_node_from_object_path('joints', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(4976.0, -1088.0), 'Get joints')
        vetala_lib_get_item1 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(6216.0, -1132.0), 'vetalaLib_GetItem')
        set_item_array_metadata = controller.add_template_node('DISPATCH_RigDispatch_SetMetadata(in Item,in Name,in NameSpace,in Value,out Success)', unreal.Vector2D(6688.0, -1776.0), 'Set Item Array Metadata')
        get_local_ik1 = controller.add_variable_node_from_object_path('local_ik', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(3720.0, -412.0), 'Get local_ik')
        spawn_bool_animation_channel = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyAddAnimationChannelBool', 'Execute', unreal.Vector2D(7032.0, -1612.0), 'Spawn Bool Animation Channel')
        spawn_float_animation_channel = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyAddAnimationChannelFloat', 'Execute', unreal.Vector2D(7048.0, -1052.0), 'Spawn Float Animation Channel')
        rig_element_key = controller.add_free_reroute_node('FRigElementKey', unreal.load_object(None, '/Script/ControlRig.RigElementKey').get_name(), is_constant=False, custom_widget_name='', default_value='', position=[6818.0, -1215.0], node_name='', setup_undo_redo=True)
        spawn_float_animation_channel1 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyAddAnimationChannelFloat', 'Execute', unreal.Vector2D(5432.0, -1532.0), 'Spawn Float Animation Channel')
        num1 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetNum(in Array,out Num)', unreal.Vector2D(824.0, -780.0), 'Num')
        equals1 = controller.add_template_node('DISPATCH_RigVMDispatch_CoreEquals(in A,in B,out Result)', unreal.Vector2D(984.0, -588.0), 'Equals')
        branch = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_ControlFlowBranch', 'Execute', unreal.Vector2D(2872.0, -1196.0), 'Branch')
        get_local_controls2 = controller.add_variable_node_from_object_path('local_controls', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(3032.0, -988.0), 'Get local_controls')
        at8 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(4280.0, -908.0), 'At')
        vetala_lib_parent2 = controller.add_function_reference_node(library.find_function('vetalaLib_Parent'), unreal.Vector2D(3256.0, -636.0), 'vetalaLib_Parent')
        branch1 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_ControlFlowBranch', 'Execute', unreal.Vector2D(6776.0, -844.0), 'Branch')
        greater2 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathIntGreater', 'Execute', unreal.Vector2D(920.0, -1004.0), 'Greater')
        if5 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(1208.0, -972.0), 'If')
        make_array = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayMake(in Values,out Array)', unreal.Vector2D(1544.0, -732.0), 'Make Array')
        get_joints2 = controller.add_variable_node_from_object_path('joints', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(600.0, -780.0), 'Get joints')
        at9 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(1208.0, -684.0), 'At')
        at10 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(1208.0, -572.0), 'At')
        or1 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathBoolOr', 'Execute', unreal.Vector2D(2560.0, -496.0), 'Or')
        vetala_lib_get_item2 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(5392.0, -576.0), 'vetalaLib_GetItem')
        spawn_null1 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyAddNull', 'Execute', unreal.Vector2D(5888.0, -1648.0), 'Spawn Null')
        get_transform1 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetTransform', 'Execute', unreal.Vector2D(5792.0, -944.0), 'Get Transform')
        set_item_metadata1 = controller.add_template_node('DISPATCH_RigDispatch_SetMetadata(in Item,in Name,in NameSpace,in Value,out Success)', unreal.Vector2D(6672.0, -1552.0), 'Set Item Metadata')
        vetala_lib_get_item3 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(5392.0, -400.0), 'vetalaLib_GetItem')

        graph.add_link(if4, 'Result', vetala_lib_get_item, 'Array', controller)

        controller.set_array_pin_size(f'{n(if4)}.False', 1)
        controller.set_array_pin_size(f'{n(make_array)}.Values', 2)

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
        graph.add_link(spawn_null1, 'ExecutePin', add1, 'ExecuteContext', controller)
        graph.add_link(add1, 'ExecuteContext', set_item_array_metadata, 'ExecuteContext', controller)
        graph.add_link(set_item_array_metadata, 'ExecuteContext', set_item_metadata1, 'ExecuteContext', controller)
        graph.add_link(set_item_metadata1, 'ExecuteContext', spawn_bool_animation_channel, 'ExecutePin', controller)
        graph.add_link(spawn_bool_animation_channel, 'ExecutePin', branch1, 'ExecuteContext', controller)
        graph.add_link(branch, 'True', vetala_lib_parent2, 'ExecuteContext', controller)
        graph.add_link(at5, 'Element', vetala_lib_find_pole_vector, 'BoneA', controller)
        graph.add_link(at6, 'Element', vetala_lib_find_pole_vector, 'BoneB', controller)
        graph.add_link(at7, 'Element', vetala_lib_find_pole_vector, 'BoneC', controller)
        graph.add_link(get_pole_vector_offset, 'Value', vetala_lib_find_pole_vector, 'output', controller)
        graph.add_link(vetala_lib_find_pole_vector, 'Transform.Translation', set_translation, 'Value', controller)

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
        graph.add_link(spawn_null, 'ExecutePin', spawn_null1, 'ExecutePin', controller)
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
        graph.add_link(get_joints2, 'Value', num1, 'Array', controller)
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
        graph.add_link(get_joints2, 'Value', if5, 'False', controller)
        graph.add_link(make_array, 'Array', if5, 'True', controller)
        graph.add_link(get_joints2, 'Value', at9, 'Array', controller)
        graph.add_link(get_joints2, 'Value', at10, 'Array', controller)
        graph.add_link(vetala_lib_get_item2, 'Element', spawn_null1, 'Parent', controller)
        graph.add_link(vetala_lib_get_item2, 'Element', set_item_metadata1, 'Item', controller)
        graph.add_link(spawn_null1, 'Item', set_item_metadata1, 'Value', controller)
        graph.add_link(get_transform1, 'Transform', spawn_null1, 'Transform', controller)
        graph.add_link(vetala_lib_get_item3, 'Element', get_transform1, 'Item', controller)
        graph.add_link(if2, 'Result', set_shape_settings, 'Settings.Name', controller)
        graph.add_link(at, 'Element', set_shape_settings, 'Settings.Color', controller)
        graph.add_link(at8, 'Element', if4, 'False.0', controller)
        graph.add_link(at9, 'Element', make_array, 'Values.0', controller)
        graph.add_link(at10, 'Element', make_array, 'Values.1', controller)
        graph.add_link(multiply, 'Result', set_shape_settings, 'Settings.Transform.Scale3D', controller)

        graph.add_link(if5, 'Result', for_each, 'Array', controller)

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
        graph.set_pin(spawn_float_animation_channel, 'MinimumValue', '0.000000', controller)
        graph.set_pin(spawn_float_animation_channel, 'MaximumValue', '1.000000', controller)
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
        graph.set_pin(spawn_null1, 'Name', 'top_ik', controller)
        graph.set_pin(spawn_null1, 'Space', 'GlobalSpace', controller)
        graph.set_pin(get_transform1, 'Space', 'GlobalSpace', controller)
        graph.set_pin(get_transform1, 'bInitial', 'False', controller)
        graph.set_pin(set_item_metadata1, 'Name', 'top_ik', controller)
        graph.set_pin(set_item_metadata1, 'NameSpace', 'Self', controller)

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
        vetala_lib_constrain_transform = controller.add_function_reference_node(library.find_function('vetalaLib_ConstrainTransform'), unreal.Vector2D(1440.0, 1008.0), 'vetalaLib_ConstrainTransform')
        get_item_metadata4 = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(1152.0, 1184.0), 'Get Item Metadata')
        set_transform1 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_SetTransform', 'Execute', unreal.Vector2D(1728.0, 912.0), 'Set Transform')
        get_transform4 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetTransform', 'Execute', unreal.Vector2D(1472.0, 1200.0), 'Get Transform')

        controller.set_array_pin_size(f'{n(vetala_lib_ik_nudge_lock)}.joints', 3)
        controller.set_array_pin_size(f'{n(vetala_lib_ik_nudge_lock)}.controls', 3)
        controller.set_array_pin_size(f'{n(rotation_constraint)}.Parents', 1)

        graph.add_link(vetala_lib_ik_nudge_lock, 'ExecuteContext', basic_ik, 'ExecutePin', controller)
        graph.add_link(branch, 'False', vetala_lib_find_bone_aim_axis, 'ExecuteContext', controller)
        graph.add_link(vetala_lib_find_bone_aim_axis, 'ExecuteContext', vetala_lib_ik_nudge_lock, 'ExecuteContext', controller)
        graph.add_link(set_transform1, 'ExecutePin', branch, 'ExecuteContext', controller)
        graph.add_link('Entry', 'joints', at, 'Array', controller)
        graph.add_link(at, 'Element', basic_ik, 'ItemA', controller)
        graph.add_link(at, 'Element', vetala_lib_find_bone_aim_axis, 'Bone', controller)
        graph.add_link(at, 'Element', get_item_metadata1, 'Item', controller)
        graph.add_link(at, 'Element', vetala_lib_constrain_transform, 'TargetTransform', controller)
        graph.add_link(at, 'Element', set_transform1, 'Item', controller)
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
        graph.add_link(get_item_metadata, 'Value', item2, 'Item', controller)
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
        graph.add_link(item, 'Item.Name', get_bool_channel, 'Control', controller)
        graph.add_link(get_bool_channel, 'Value', basic_fabrik, 'bSetEffectorTransform', controller)
        graph.add_link(get_item_metadata2, 'Value', get_item_metadata3, 'Item', controller)
        graph.add_link(get_item_metadata2, 'Value', if1, 'False', controller)
        graph.add_link(if1, 'Result', item, 'Item', controller)
        graph.add_link(item1, 'Item.Name', get_float_channel, 'Control', controller)
        graph.add_link(if1, 'Result', item1, 'Item', controller)
        graph.add_link(item2, 'Item.Name', get_float_channel1, 'Control', controller)
        graph.add_link(get_item_metadata2, 'Value', get_item_metadata3, 'Item', controller)
        graph.add_link(get_item_metadata3, 'Value', if1, 'True', controller)
        graph.add_link(get_item_metadata3, 'Found', if1, 'Condition', controller)
        graph.add_link(if1, 'Result', item, 'Item', controller)
        graph.add_link(if1, 'Result', item1, 'Item', controller)
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
        graph.add_link(vetala_lib_get_item1, 'Element', set_transform, 'Item', controller)
        graph.add_link(vetala_lib_get_item2, 'Element', rotation_constraint, 'Child', controller)
        graph.add_link(vetala_lib_get_item1, 'Element', set_transform, 'Item', controller)
        graph.add_link(get_transform2, 'Transform', set_transform, 'Value', controller)
        graph.add_link(get_item_metadata1, 'Value', get_transform2, 'Item', controller)
        graph.add_link(greater, 'Result', or1, 'B', controller)
        graph.add_link(get_item_metadata1, 'Value', get_item_metadata4, 'Item', controller)
        graph.add_link('DISPATCH_RigVMDispatch_SwitchInt32', 'Cases.1', set_transform1, 'ExecutePin', controller)
        graph.add_link(at, 'Element', set_transform1, 'Item', controller)
        graph.add_link(get_transform4, 'Transform', set_transform1, 'Value', controller)
        graph.add_link(get_item_metadata4, 'Value', get_transform4, 'Item', controller)
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

        graph.set_pin(get_item_metadata4, 'Name', 'top_ik', controller)
        graph.set_pin(get_item_metadata4, 'NameSpace', 'Self', controller)
        graph.set_pin(get_item_metadata4, 'Default', '(Type=Bone,Name="None")', controller)
        graph.set_pin(set_transform1, 'Space', 'GlobalSpace', controller)
        graph.set_pin(set_transform1, 'bInitial', 'False', controller)
        graph.set_pin(set_transform1, 'Weight', '1.000000', controller)
        graph.set_pin(set_transform1, 'bPropagateToChildren', 'True', controller)
        graph.set_pin(get_transform4, 'Space', 'GlobalSpace', controller)
        graph.set_pin(get_transform4, 'bInitial', 'False', controller)

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

        controller.add_local_variable_from_object_path('last_control', 'FRigElementKey', '/Script/ControlRig.RigElementKey', '')

        set_local_controls = controller.add_variable_node_from_object_path('local_controls', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', False, '()', unreal.Vector2D(6688.0, -1344.0), 'Set local_controls')
        spline_from_items = controller.add_external_function_reference_node('/ControlRigSpline/SplineFunctionLibrary/SplineFunctionLibrary.SplineFunctionLibrary_C', 'SplineFromItems', unreal.Vector2D(1600.0, -2900.0), 'SplineFromItems')
        get_joints = controller.add_variable_node_from_object_path('joints', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(1100.0, -1160.0), 'Get joints')
        get_spline_controls = controller.add_variable_node_from_object_path('spline_controls', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(1300.0, -2080.0), 'Get spline_controls')
        get_control_count = controller.add_variable_node('control_count', 'int32', None, True, '', unreal.Vector2D(1100.0, -2200.0), 'Get control_count')
        get_hierarchy = controller.add_variable_node('hierarchy', 'bool', None, True, '', unreal.Vector2D(1100.0, -2060.0), 'Get hierarchy')
        get_parent = controller.add_variable_node_from_object_path('parent', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(1100.0, -1760.0), 'Get parent')
        get_last_control = controller.add_variable_node_from_object_path('last_control', 'FRigElementKey', '/Script/ControlRig.RigElementKey', True, '', unreal.Vector2D(1100.039335, -1900.0), 'Get last_control')
        reset = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayReset(io Array)', unreal.Vector2D(2000.0, -2500.0), 'Reset')
        for_loop = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_ForLoopCount', 'Execute', unreal.Vector2D(2300.0, -2400.0), 'For Loop')
        greater = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathIntGreater', 'Execute', unreal.Vector2D(1750.0, -2300.0), 'Greater')
        if1 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(2000.0, -2200.0), 'If')
        num = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetNum(in Array,out Num)', unreal.Vector2D(1800.0, -1900.0), 'Num')
        greater1 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathIntGreater', 'Execute', unreal.Vector2D(2000.0, -1900.0), 'Greater')
        if2 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(2300.0, -1800.0), 'If')
        equals = controller.add_template_node('DISPATCH_RigVMDispatch_CoreEquals(in A,in B,out Result)', unreal.Vector2D(2500.0, -2200.0), 'Equals')
        if3 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(2700.0, -2050.0), 'If')
        if4 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(2900.0, -1900.0), 'If')
        position_from_spline = controller.add_unit_node_from_struct_path('/Script/ControlRigSpline.RigUnit_PositionFromControlRigSpline', 'Execute', unreal.Vector2D(2800.0, -2500.0), 'Position From Spline')
        make_transform = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathTransformMake', 'Execute', unreal.Vector2D(3100.0, -2500.0), 'Make Transform')
        spawn_null = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyAddNull', 'Execute', unreal.Vector2D(3500.0, -2500.0), 'Spawn Null')
        set_default_parent = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_SetDefaultParent', 'Execute', unreal.Vector2D(4800.0, -2700.0), 'Set Default Parent')
        set_last_control = controller.add_variable_node_from_object_path('last_control', 'FRigElementKey', '/Script/ControlRig.RigElementKey', False, '', unreal.Vector2D(5200.0, -2100.0), 'Set last_control')
        get_spline_controls1 = controller.add_variable_node_from_object_path('spline_controls', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(5280.0, -1888.0), 'Get spline_controls')
        at = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(5200.0, -1160.0), 'At')
        add = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayAdd(io Array,in Element,out Index)', unreal.Vector2D(5800.0, -1800.0), 'Add')
        set_item_array_metadata = controller.add_template_node('DISPATCH_RigDispatch_SetMetadata(in Item,in Name,in NameSpace,in Value,out Success)', unreal.Vector2D(6300.0, -1500.0), 'Set Item Array Metadata')
        at1 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(6600.0, -1800.0), 'At')
        spawn_bool_animation_channel = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyAddAnimationChannelBool', 'Execute', unreal.Vector2D(6900.0, -1500.0), 'Spawn Bool Animation Channel')
        get_spline_controls2 = controller.add_variable_node_from_object_path('spline_controls', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(6144.0, -1120.0), 'Get spline_controls')
        vetala_lib_get_item = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(1792.0, -1760.0), 'vetalaLib_GetItem')
        vetala_lib_control = self._create_control(controller, 4224.0, -2000.0)

        graph.add_link(set_item_array_metadata, 'ExecuteContext', set_local_controls, 'ExecuteContext', controller)
        graph.add_link(set_local_controls, 'ExecuteContext', spawn_bool_animation_channel, 'ExecuteContext', controller)
        graph.add_link('DISPATCH_RigVMDispatch_SwitchInt32', 'Cases.0', spline_from_items, 'ExecuteContext', controller)
        graph.add_link(spline_from_items, 'ExecuteContext', reset, 'ExecuteContext', controller)
        graph.add_link(reset, 'ExecuteContext', for_loop, 'ExecuteContext', controller)
        graph.add_link(for_loop, 'ExecuteContext', spawn_null, 'ExecuteContext', controller)
        graph.add_link(for_loop, 'Completed', set_item_array_metadata, 'ExecuteContext', controller)
        graph.add_link(spawn_null, 'ExecuteContext', vetala_lib_control, 'ExecuteContext', controller)
        graph.add_link(vetala_lib_control, 'ExecuteContext', set_default_parent, 'ExecuteContext', controller)
        graph.add_link(set_default_parent, 'ExecuteContext', set_last_control, 'ExecuteContext', controller)
        graph.add_link(set_last_control, 'ExecuteContext', add, 'ExecuteContext', controller)
        graph.add_link(get_spline_controls2, 'Value', set_local_controls, 'Value', controller)
        graph.add_link(get_joints, 'Value', spline_from_items, 'Items', controller)
        graph.add_link(spline_from_items, 'Spline', position_from_spline, 'Spline', controller)
        graph.add_link(get_joints, 'Value', at, 'Array', controller)
        graph.add_link(get_spline_controls, 'Value', reset, 'Array', controller)
        graph.add_link(get_control_count, 'Value', greater, 'A', controller)
        graph.add_link(get_control_count, 'Value', if1, 'True', controller)
        graph.add_link(get_hierarchy, 'Value', if4, 'Condition', controller)
        graph.add_link(get_parent, 'Value', num, 'Array', controller)
        graph.add_link(get_parent, 'Value', vetala_lib_get_item, 'Array', controller)
        graph.add_link(get_last_control, 'Value', if3, 'False', controller)
        graph.add_link(if1, 'Result', for_loop, 'Count', controller)
        graph.add_link(for_loop, 'Index', equals, 'A', controller)
        graph.add_link(for_loop, 'Index', vetala_lib_control, 'increment', controller)
        graph.add_link(for_loop, 'Ratio', position_from_spline, 'U', controller)
        graph.add_link(greater, 'Result', if1, 'Condition', controller)
        graph.add_link(num, 'Num', 'Greater_1', 'A', controller)
        graph.add_link(num, 'Num', greater1, 'A', controller)
        graph.add_link(greater1, 'Result', if2, 'Condition', controller)
        graph.add_link(vetala_lib_get_item, 'Element', if2, 'True', controller)
        graph.add_link(if2, 'Result', if3, 'True', controller)
        graph.add_link(if2, 'Result', if4, 'False', controller)
        graph.add_link(equals, 'Result', if3, 'Condition', controller)
        graph.add_link(if3, 'Result', if4, 'True', controller)
        graph.add_link(if4, 'Result', vetala_lib_control, 'parent', controller)
        graph.add_link(position_from_spline, 'Position', make_transform, 'Translation', controller)
        graph.add_link(make_transform, 'Result', spawn_null, 'Transform', controller)
        graph.add_link(spawn_null, 'Item', set_default_parent, 'Child', controller)
        graph.add_link(spawn_null, 'Item', vetala_lib_control, 'driven', controller)
        graph.add_link(vetala_lib_control, 'Control', set_default_parent, 'Parent', controller)
        graph.add_link(vetala_lib_control, 'Control', set_last_control, 'Value', controller)
        graph.add_link(get_spline_controls1, 'Value', add, 'Array', controller)
        graph.add_link(at, 'Element', set_item_array_metadata, 'Item', controller)
        graph.add_link(add, 'Array', at1, 'Array', controller)
        graph.add_link(add, 'Array', set_item_array_metadata, 'Value', controller)
        graph.add_link(vetala_lib_control, 'Control', add, 'Element', controller)
        graph.add_link(at1, 'Element', spawn_bool_animation_channel, 'Parent', controller)
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

        graph.set_pin(spline_from_items, 'Spline Mode', 'Hermite', controller)
        graph.set_pin(spline_from_items, 'Samples Per Segment', '16', controller)
        graph.set_pin(greater, 'B', '3', controller)
        graph.set_pin(if1, 'False', '4', controller)
        graph.set_pin(greater1, 'B', '0', controller)
        graph.set_pin(equals, 'B', '0', controller)
        graph.set_pin(make_transform, 'Rotation', '(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000)', controller)
        graph.set_pin(make_transform, 'Scale', '(X=1.000000,Y=1.000000,Z=1.000000)', controller)
        graph.set_pin(spawn_null, 'Parent', '(Type=Bone,Name="None")', controller)
        graph.set_pin(spawn_null, 'Name', 'NewNull', controller)
        graph.set_pin(spawn_null, 'Space', 'LocalSpace', controller)
        graph.set_pin(at, 'Index', '0', controller)
        graph.set_pin(set_item_array_metadata, 'Name', 'controls', controller)
        graph.set_pin(set_item_array_metadata, 'NameSpace', 'Self', controller)
        graph.set_pin(at1, 'Index', '0', controller)
        graph.set_pin(spawn_bool_animation_channel, 'Name', 'stretch', controller)
        graph.set_pin(spawn_bool_animation_channel, 'InitialValue', 'true', controller)
        graph.set_pin(spawn_bool_animation_channel, 'MinimumValue', 'False', controller)
        graph.set_pin(spawn_bool_animation_channel, 'MaximumValue', 'True', controller)
        graph.set_pin(vetala_lib_get_item, 'index', '-1', controller)

        current_locals = locals()
        nodes = unreal_lib.graph.filter_nodes(current_locals.values())
        node = unreal_lib.graph.comment_nodes(nodes, controller, 'Construction')

        nodes.append(node)
        unreal_lib.graph.move_nodes(0, 0, nodes, controller)
        unreal_lib.graph.move_nodes(1000, -3000, nodes, controller)

    def _build_function_forward_graph(self):
        controller = self.function_controller
        library = graph.get_local_function_library()

        controller.add_exposed_pin('Secondary Spline Direction', unreal.RigVMPinDirection.INPUT, 'FVector', '/Script/CoreUObject.Vector', '(X=0.000000,Y=5.0,Z=0.000000)')

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
        graph.set_pin(get_item_array_metadata, 'Name', 'controls', controller)
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

    def _build_function_construct_graph(self):

        controller = self.function_controller
        library = graph.get_local_function_library()
        self.function_controller.add_local_variable_from_object_path('local_controls', 'TArray<FRigElementKey>',
                                                                    '/Script/ControlRig.RigElementKey', '')

        vetala_lib_control = self._create_control(controller, 6704.0, -1392.0)
        vetala_lib_get_parent = controller.add_function_reference_node(library.find_function('vetalaLib_GetParent'), unreal.Vector2D(1408.0, -1792.0), 'vetalaLib_GetParent')
        set_item_metadata = controller.add_template_node('DISPATCH_RigDispatch_SetMetadata(in Item,in Name,in Value,out Success)', unreal.Vector2D(9888.0, -1376.0), 'Set Item Metadata')
        get_control_layer = controller.add_variable_node('control_layer', 'FName', None, True, '', unreal.Vector2D(992.0, -2000.0), 'Get control_layer')
        get_description = controller.add_variable_node('description', 'FString', None, True, '', unreal.Vector2D(5264.0, -1056.0), 'Get description')
        add = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayAdd(io Array,in Element,out Index)', unreal.Vector2D(7056.0, -1376.0), 'Add')
        get_local_controls = controller.add_variable_node_from_object_path('local_controls', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(8000.0, -1792.0), 'Get local_controls')
        branch = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_ControlFlowBranch', 'Execute', unreal.Vector2D(1440.0, -1552.0), 'Branch')
        num = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetNum(in Array,out Num)', unreal.Vector2D(832.0, -1568.0), 'Num')
        equals = controller.add_template_node('DISPATCH_RigVMDispatch_CoreEquals(in A,in B,out Result)', unreal.Vector2D(1072.0, -1568.0), 'Equals')
        get_joints = controller.add_variable_node_from_object_path('joints', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(704.0, -1856.0), 'Get joints')
        at = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(1024.0, -1792.0), 'At')
        vetala_lib_control1 = self._create_control(controller, 3712.0, -1551.0)
        add1 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayAdd(io Array,in Element,out Index)', unreal.Vector2D(4656.0, -1536.0), 'Add')
        at1 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(2944.0, -1808.0), 'At')
        make_array = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayMake(in Values,out Array)', unreal.Vector2D(2800.0, -944.0), 'Make Array')
        get_transform = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetTransform', 'Execute', unreal.Vector2D(2368.0, -1040.0), 'Get Transform')
        get_heel_pivot = controller.add_variable_node_from_object_path('heel_pivot', 'TArray<FVector>', '/Script/CoreUObject.Vector', True, '()', unreal.Vector2D(2064.0, -640.0), 'Get heel_pivot')
        get_yaw_in_pivot = controller.add_variable_node_from_object_path('yaw_in_pivot', 'TArray<FVector>', '/Script/CoreUObject.Vector', True, '()', unreal.Vector2D(2064.0, -448.0), 'Get yaw_in_pivot')
        get_yaw_out_pivot = controller.add_variable_node_from_object_path('yaw_out_pivot', 'TArray<FVector>', '/Script/CoreUObject.Vector', True, '()', unreal.Vector2D(2064.0, -544.0), 'Get yaw_out_pivot')
        vetala_lib_get_item_vector = controller.add_function_reference_node(library.find_function('vetalaLib_GetItemVector'), unreal.Vector2D(2272.0, -688.0), 'vetalaLib_GetItemVector')
        vetala_lib_get_item_vector1 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItemVector'), unreal.Vector2D(2272.0, -536.0), 'vetalaLib_GetItemVector')
        vetala_lib_get_item_vector2 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItemVector'), unreal.Vector2D(2272.0, -384.0), 'vetalaLib_GetItemVector')
        for_each = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayIterator(in Array,out Element,out Index,out Count,out Ratio)', unreal.Vector2D(2848.0, -1552.0), 'For Each')
        make_array1 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayMake(in Values,out Array)', unreal.Vector2D(2800.0, -336.0), 'Make Array')
        at2 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(3216.0, -672.0), 'At')
        get_description1 = controller.add_variable_node('description', 'FString', None, True, '', unreal.Vector2D(2608.0, -1360.0), 'Get description')
        join = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_StringJoin', 'Execute', unreal.Vector2D(2960.0, -1271.0), 'Join')
        get_local_controls1 = controller.add_variable_node_from_object_path('local_controls', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(3200.0, -1808.0), 'Get local_controls')
        at3 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(3536.0, -1808.0), 'At')
        get_local_controls2 = controller.add_variable_node_from_object_path('local_controls', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(4192.0, -1808.0), 'Get local_controls')
        join1 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_StringJoin', 'Execute', unreal.Vector2D(5488.0, -880.0), 'Join')
        add2 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayAdd(io Array,in Element,out Index)', unreal.Vector2D(2448.0, -1553.0), 'Add')
        get_local_controls3 = controller.add_variable_node_from_object_path('local_controls', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(2320.0, -1824.0), 'Get local_controls')
        get_local_controls4 = controller.add_variable_node_from_object_path('local_controls', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(4576.0, -1808.0), 'Get local_controls')
        at4 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(5504.0, -1776.0), 'At')
        vetala_lib_control2 = self._create_control(controller, 8160.0, -1392.0)
        join2 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_StringJoin', 'Execute', unreal.Vector2D(7184.0, -896.0), 'Join')
        get_transform1 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetTransform', 'Execute', unreal.Vector2D(8432.0, -1616.0), 'Get Transform')
        set_transform = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_SetTransform', 'Execute', unreal.Vector2D(9088.0, -1376.0), 'Set Transform')
        set_item_metadata1 = controller.add_template_node('DISPATCH_RigDispatch_SetMetadata(in Item,in Name,in Value,out Success)', unreal.Vector2D(10240.0, -1376.0), 'Set Item Metadata')
        set_item_metadata2 = controller.add_template_node('DISPATCH_RigDispatch_SetMetadata(in Item,in Name,in Value,out Success)', unreal.Vector2D(5152.0, -1376.0), 'Set Item Metadata')
        vetala_lib_get_item_vector3 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItemVector'), unreal.Vector2D(6544.0, -494.0), 'vetalaLib_GetItemVector')
        get_shape_scale = controller.add_variable_node_from_object_path('shape_scale', 'TArray<FVector>', '/Script/CoreUObject.Vector', True, '()', unreal.Vector2D(6352.0, -467.0), 'Get shape_scale')
        multiply = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathVectorMul', 'Execute', unreal.Vector2D(6800.0, -496.0), 'Multiply')
        make_array2 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayMake(in Values,out Array)', unreal.Vector2D(6976.0, -496.0), 'Make Array')
        vetala_lib_get_item_vector4 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItemVector'), unreal.Vector2D(3376.0, -510.0), 'vetalaLib_GetItemVector')
        get_shape_scale1 = controller.add_variable_node_from_object_path('shape_scale', 'TArray<FVector>', '/Script/CoreUObject.Vector', True, '()', unreal.Vector2D(3184.0, -483.0), 'Get shape_scale')
        multiply1 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathVectorMul', 'Execute', unreal.Vector2D(3632.0, -512.0), 'Multiply')
        make_array3 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayMake(in Values,out Array)', unreal.Vector2D(3808.0, -512.0), 'Make Array')
        get_ik = controller.add_variable_node_from_object_path('ik', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(9264.0, -640.0), 'Get ik')
        get_joints1 = controller.add_variable_node_from_object_path('joints', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(8688.0, -1792.0), 'Get joints')
        vetala_lib_get_item = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(9040.0, -1568.0), 'vetalaLib_GetItem')
        set_item_array_metadata = controller.add_template_node('DISPATCH_RigDispatch_SetMetadata(in Item,in Name,in Value,out Success)', unreal.Vector2D(10544.0, -1376.0), 'Set Item Array Metadata')
        add3 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayAdd(io Array,in Element,out Index)', unreal.Vector2D(8480.0, -1376.0), 'Add')
        get_parent = controller.add_variable_node_from_object_path('parent', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(10040.0, -1660.0), 'Get parent')
        get_item_metadata = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in Default,out Value,out Found)', unreal.Vector2D(10424.0, -1660.0), 'Get Item Metadata')
        if1 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(10986.0, -1660.0), 'If')
        item_exists = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_ItemExists', 'Execute', unreal.Vector2D(10698.0, -1660.0), 'Item Exists')
        vetala_lib_get_item1 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(10200.0, -1660.0), 'vetalaLib_GetItem')
        spawn_float_animation_channel = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyAddAnimationChannelFloat', 'Execute', unreal.Vector2D(11040.0, -960.0), 'Spawn Float Animation Channel')
        for_each1 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayIterator(in Array,out Element,out Index,out Count,out Ratio)', unreal.Vector2D(10592.0, -880.0), 'For Each')
        make_array4 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayMake(in Values,out Array)', unreal.Vector2D(10240.0, -976.0), 'Make Array')
        double = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathDoubleMake', 'Execute', unreal.Vector2D(10896.0, -480.0), 'Double')
        set_name_metadata = controller.add_template_node('DISPATCH_RigDispatch_SetMetadata(in Item,in Name,in Value,out Success)', unreal.Vector2D(11552.0, -960.0), 'Set Name Metadata')
        set_item_metadata3 = controller.add_template_node('DISPATCH_RigDispatch_SetMetadata(in Item,in Name,in Value,out Success)', unreal.Vector2D(4752.0, -928.0), 'Set Item Metadata')
        from_string = controller.add_template_node('DISPATCH_RigDispatch_FromString(in String,out Result)', unreal.Vector2D(3584.0, -912.0), 'From String')
        get_joints2 = controller.add_variable_node_from_object_path('joints', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(4256.0, -784.0), 'Get joints')
        vetala_lib_get_item2 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(4468.0, -768.0), 'vetalaLib_GetItem')
        set_vector_metadata = controller.add_template_node('DISPATCH_RigDispatch_SetMetadata(in Item,in Name,in Value,out Success)', unreal.Vector2D(4752.0, -672.0), 'Set Vector Metadata')
        get_forward_axis = controller.add_variable_node_from_object_path('forward_axis', 'TArray<FVector>', '/Script/CoreUObject.Vector', True, '()', unreal.Vector2D(4246.0, -544.0), 'Get forward_axis')
        vetala_lib_get_item_vector5 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItemVector'), unreal.Vector2D(4448.0, -544.0), 'vetalaLib_GetItemVector')
        get_up_axis = controller.add_variable_node_from_object_path('up_axis', 'TArray<FVector>', '/Script/CoreUObject.Vector', True, '()', unreal.Vector2D(4256.0, -352.0), 'Get up_axis')
        vetala_lib_get_item_vector6 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItemVector'), unreal.Vector2D(4448.0, -352.0), 'vetalaLib_GetItemVector')
        set_vector_metadata1 = controller.add_template_node('DISPATCH_RigDispatch_SetMetadata(in Item,in Name,in Value,out Success)', unreal.Vector2D(4752.0, -416.0), 'Set Vector Metadata')
        get_relative_transform = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetRelativeTransformForItem', 'Execute', unreal.Vector2D(8656.0, -1216.0), 'Get Relative Transform')
        from_string1 = controller.add_template_node('DISPATCH_RigDispatch_FromString(in String,out Result)', unreal.Vector2D(2720.0, -1216.0), 'From String')
        spawn_null1 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyAddNull', 'Execute', unreal.Vector2D(5904.0, -1360.0), 'Spawn Null')
        from_string2 = controller.add_template_node('DISPATCH_RigDispatch_FromString(in String,out Result)', unreal.Vector2D(5728.0, -1008.0), 'From String')
        set_transform1 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_SetTransform', 'Execute', unreal.Vector2D(6272.0, -1360.0), 'Set Transform')
        get_transform2 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetTransform', 'Execute', unreal.Vector2D(5984.0, -1616.0), 'Get Transform')
        spawn_null2 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyAddNull', 'Execute', unreal.Vector2D(7344.0, -1376.0), 'Spawn Null')
        from_string3 = controller.add_template_node('DISPATCH_RigDispatch_FromString(in String,out Result)', unreal.Vector2D(7410.0, -776.0), 'From String')
        vetala_lib_get_item3 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(5840.0, -1904.0), 'vetalaLib_GetItem')
        set_transform2 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_SetTransform', 'Execute', unreal.Vector2D(7760.0, -1376.0), 'Set Transform')
        vetala_lib_get_item4 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(9584.0, -1584.0), 'vetalaLib_GetItem')
        spawn_transform_control = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyAddControlTransform', 'Execute', unreal.Vector2D(1904.0, -1552.0), 'Spawn Transform Control')
        spawn_transform_control1 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyAddControlTransform', 'Execute', unreal.Vector2D(3088.0, -1632.0), 'Spawn Transform Control')
        set_transform3 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_SetTransform', 'Execute', unreal.Vector2D(4077.0, -1532.0), 'Set Transform')
        join3 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_StringJoin', 'Execute', unreal.Vector2D(3168.0, -1274.0), 'Join')
        from_string4 = controller.add_template_node('DISPATCH_RigDispatch_FromString(in String,out Result)', unreal.Vector2D(3392.0, -1232.0), 'From String')
        equals1 = controller.add_template_node('DISPATCH_RigVMDispatch_CoreEquals(in A,in B,out Result)', unreal.Vector2D(10896.0, -624.0), 'Equals')
        if2 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(11152.0, -528.0), 'If')
        get_joints3 = controller.add_variable_node_from_object_path('joints', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(5584.0, -1920.0), 'Get joints')
        get_control_layer1 = controller.add_variable_node('control_layer', 'FName', None, True, '', unreal.Vector2D(5010.0, -1169.0), 'Get control_layer')
        get_control_layer2 = controller.add_variable_node('control_layer', 'FName', None, True, '', unreal.Vector2D(9630.0, -1725.0), 'Get control_layer')
        spawn_null3 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyAddNull', 'Execute', unreal.Vector2D(5504.0, -1360.0), 'Spawn Null')
        join4 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_StringJoin', 'Execute', unreal.Vector2D(5488.0, -1120.0), 'Join')
        from_string5 = controller.add_template_node('DISPATCH_RigDispatch_FromString(in String,out Result)', unreal.Vector2D(5312.0, -1168.0), 'From String')
        vetala_lib_get_item5 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(4960.0, -1792.0), 'vetalaLib_GetItem')

        controller.set_array_pin_size(f'{n(vetala_lib_control)}.color', 1)
        controller.set_array_pin_size(f'{n(vetala_lib_control)}.sub_color', 1)
        controller.set_array_pin_size(f'{n(vetala_lib_control1)}.color', 1)
        controller.set_array_pin_size(f'{n(vetala_lib_control1)}.sub_color', 1)
        controller.set_array_pin_size(f'{n(vetala_lib_control1)}.translate', 1)
        controller.set_array_pin_size(f'{n(vetala_lib_control1)}.rotate', 1)
        controller.set_array_pin_size(f'{n(vetala_lib_control1)}.scale', 1)
        controller.set_array_pin_size(f'{n(make_array)}.Values', 4)
        controller.set_array_pin_size(f'{n(make_array1)}.Values', 4)
        controller.set_array_pin_size(f'{n(join)}.Values', 2)
        controller.set_array_pin_size(f'{n(join1)}.Values', 2)
        controller.set_array_pin_size(f'{n(vetala_lib_control2)}.color', 1)
        controller.set_array_pin_size(f'{n(vetala_lib_control2)}.sub_color', 1)
        controller.set_array_pin_size(f'{n(vetala_lib_control2)}.translate', 1)
        controller.set_array_pin_size(f'{n(vetala_lib_control2)}.rotate', 1)
        controller.set_array_pin_size(f'{n(vetala_lib_control2)}.scale', 1)
        controller.set_array_pin_size(f'{n(join2)}.Values', 2)
        controller.set_array_pin_size(f'{n(make_array2)}.Values', 1)
        controller.set_array_pin_size(f'{n(make_array3)}.Values', 1)
        controller.set_array_pin_size(f'{n(make_array4)}.Values', 11)
        controller.set_array_pin_size(f'{n(join3)}.Values', 2)
        controller.set_array_pin_size(f'{n(join4)}.Values', 3)

        graph.add_link('DISPATCH_RigVMDispatch_SwitchInt32', 'Cases.0', branch, 'ExecuteContext', controller)
        graph.add_link('Entry', 'color', vetala_lib_control, 'color', controller)
        graph.add_link('Entry', 'color', vetala_lib_control1, 'color', controller)
        graph.add_link('Entry', 'color', vetala_lib_control2, 'color', controller)
        graph.add_link('Entry', 'joints', num, 'Array', controller)
        graph.add_link('Entry', 'parent', vetala_lib_get_parent, 'default_parent', controller)
        graph.add_link('Entry', 'restrain_numbering', vetala_lib_control, 'restrain_numbering', controller)
        graph.add_link('Entry', 'restrain_numbering', vetala_lib_control1, 'restrain_numbering', controller)
        graph.add_link('Entry', 'restrain_numbering', vetala_lib_control2, 'restrain_numbering', controller)
        graph.add_link('Entry', 'shape', vetala_lib_control, 'shape', controller)
        graph.add_link('Entry', 'shape', vetala_lib_control1, 'shape', controller)
        graph.add_link('Entry', 'shape', vetala_lib_control2, 'shape', controller)
        graph.add_link('Entry', 'shape_rotate', vetala_lib_control, 'rotate', controller)
        graph.add_link('Entry', 'shape_rotate', vetala_lib_control1, 'rotate', controller)
        graph.add_link('Entry', 'shape_rotate', vetala_lib_control2, 'rotate', controller)
        graph.add_link('Entry', 'shape_scale', vetala_lib_control, 'scale', controller)
        graph.add_link('Entry', 'shape_translate', vetala_lib_control, 'translate', controller)
        graph.add_link('Entry', 'shape_translate', vetala_lib_control1, 'translate', controller)
        graph.add_link('Entry', 'shape_translate', vetala_lib_control2, 'translate', controller)
        graph.add_link('Entry', 'side', vetala_lib_control, 'side', controller)
        graph.add_link('Entry', 'side', vetala_lib_control1, 'side', controller)
        graph.add_link('Entry', 'side', vetala_lib_control2, 'side', controller)
        graph.add_link('Entry', 'sub_color', vetala_lib_control, 'sub_color', controller)
        graph.add_link('Entry', 'sub_color', vetala_lib_control1, 'sub_color', controller)
        graph.add_link('Entry', 'sub_color', vetala_lib_control2, 'sub_color', controller)
        graph.add_link(add, 'ExecuteContext', spawn_null2, 'ExecuteContext', controller)
        graph.add_link(add1, 'ExecuteContext', set_item_metadata3, 'ExecuteContext', controller)
        graph.add_link(add2, 'ExecuteContext', for_each, 'ExecuteContext', controller)
        graph.add_link(add3, 'ExecuteContext', set_transform, 'ExecuteContext', controller)
        graph.add_link(at, 'Element', vetala_lib_get_parent, 'joint', controller)
        graph.add_link(at1, 'Element', get_transform, 'Item', controller)
        graph.add_link(at1, 'Element', set_item_metadata2, 'Item', controller)
        graph.add_link(at2, 'Element', from_string, 'String', controller)
        graph.add_link(at3, 'Element', spawn_transform_control1, 'Parent', controller)
        graph.add_link(at4, 'Element', get_relative_transform, 'Parent', controller)
        graph.add_link(at4, 'Element', spawn_null3, 'Parent', controller)

        graph.add_link(branch, 'True', spawn_transform_control, 'ExecuteContext', controller)
        graph.add_link(double, 'Value', if2, 'False', controller)
        graph.add_link(equals, 'Result', branch, 'Condition', controller)
        graph.add_link(equals1, 'Result', if2, 'Condition', controller)

        graph.add_link(for_each, 'Completed', set_item_metadata2, 'ExecuteContext', controller)
        graph.add_link(for_each, 'Element', set_transform3, 'Value', controller)
        graph.add_link(for_each, 'Element', spawn_transform_control1, 'OffsetTransform', controller)
        graph.add_link(for_each, 'ExecuteContext', spawn_transform_control1, 'ExecuteContext', controller)
        graph.add_link(for_each, 'Index', at2, 'Index', controller)
        graph.add_link(for_each1, 'Element', set_name_metadata, 'Name', controller)

        graph.add_link(make_array4, 'Array', for_each1, 'Array', controller)
        graph.add_link(for_each1, 'Element', equals1, 'A', controller)
        graph.add_link(for_each1, 'Element', spawn_float_animation_channel, 'Name', controller)
        graph.add_link(for_each1, 'ExecuteContext', spawn_float_animation_channel, 'ExecuteContext', controller)
        graph.add_link(from_string, 'Result', set_item_metadata3, 'Name', controller)
        graph.add_link(from_string2, 'Result', spawn_null1, 'Name', controller)
        graph.add_link(from_string3, 'Result', spawn_null2, 'Name', controller)
        graph.add_link(from_string4, 'Result', spawn_transform_control1, 'Name', controller)
        graph.add_link(from_string5, 'Result', spawn_null3, 'Name', controller)

        graph.add_link(get_control_layer, 'Value', vetala_lib_get_parent, 'control_layer', controller)
        graph.add_link(get_control_layer1, 'Value', set_item_metadata2, 'Name', controller)
        graph.add_link(get_control_layer2, 'Value', set_item_metadata, 'Name', controller)
        graph.add_link(get_forward_axis, 'Value', vetala_lib_get_item_vector5, 'Vector', controller)
        graph.add_link(get_heel_pivot, 'Value', vetala_lib_get_item_vector, 'Vector', controller)

        graph.add_link(get_ik, 'Value', set_item_array_metadata, 'Value', controller)

        graph.add_link(vetala_lib_get_item1, 'Element', get_item_metadata, 'Item', controller)
        graph.add_link(vetala_lib_get_item1, 'Element', if1, 'False', controller)
        graph.add_link(get_item_metadata, 'Value', if1, 'True', controller)

        graph.add_link(get_item_metadata, 'Value', item_exists, 'Item', controller)

        graph.add_link(get_joints, 'Value', at, 'Array', controller)
        graph.add_link(get_joints, 'Value', at1, 'Array', controller)
        graph.add_link(get_joints1, 'Value', vetala_lib_get_item, 'Array', controller)
        graph.add_link(get_joints1, 'Value', vetala_lib_get_item4, 'Array', controller)
        graph.add_link(get_joints2, 'Value', vetala_lib_get_item2, 'Array', controller)
        graph.add_link(get_joints3, 'Value', vetala_lib_get_item3, 'Array', controller)

        graph.add_link(get_local_controls, 'Value', add, 'Array', controller)
        graph.add_link(get_local_controls, 'Value', add3, 'Array', controller)
        graph.add_link(get_local_controls1, 'Value', at3, 'Array', controller)
        graph.add_link(get_local_controls2, 'Value', add1, 'Array', controller)
        graph.add_link(get_local_controls3, 'Value', add2, 'Array', controller)
        graph.add_link(get_local_controls4, 'Value', at4, 'Array', controller)
        graph.add_link(get_local_controls4, 'Value', vetala_lib_get_item5, 'Array', controller)
        graph.add_link(get_parent, 'Value', vetala_lib_get_item1, 'Array', controller)
        graph.add_link(get_shape_scale, 'Value', vetala_lib_get_item_vector3, 'Vector', controller)
        graph.add_link(get_shape_scale1, 'Value', vetala_lib_get_item_vector4, 'Vector', controller)
        graph.add_link(get_transform1, 'Transform', set_transform, 'Value', controller)
        graph.add_link(get_transform2, 'Transform', set_transform1, 'Value', controller)
        graph.add_link(get_transform2, 'Transform', set_transform2, 'Value', controller)
        graph.add_link(get_transform2, 'Transform', spawn_null3, 'Transform', controller)
        graph.add_link(get_up_axis, 'Value', vetala_lib_get_item_vector6, 'Vector', controller)
        graph.add_link(get_yaw_in_pivot, 'Value', vetala_lib_get_item_vector2, 'Vector', controller)
        graph.add_link(get_yaw_out_pivot, 'Value', vetala_lib_get_item_vector1, 'Vector', controller)
        graph.add_link(if1, 'Result', spawn_float_animation_channel, 'Parent', controller)
        graph.add_link(if2, 'Result', spawn_float_animation_channel, 'InitialValue', controller)
        graph.add_link(item_exists, 'Exists', if1, 'Condition', controller)

        graph.add_link(join, 'Result', from_string1, 'String', controller)
        graph.add_link(join, 'Result', vetala_lib_control1, 'description', controller)
        graph.add_link(join1, 'Result', from_string2, 'String', controller)
        graph.add_link(join1, 'Result', vetala_lib_control, 'description', controller)
        graph.add_link(join2, 'Result', from_string3, 'String', controller)
        graph.add_link(join2, 'Result', vetala_lib_control2, 'description', controller)
        graph.add_link(join3, 'Result', from_string4, 'String', controller)
        graph.add_link(join4, 'Result', from_string5, 'String', controller)

        graph.add_link(make_array, 'Array', for_each, 'Array', controller)
        graph.add_link(make_array1, 'Array', at2, 'Array', controller)
        graph.add_link(make_array2, 'Array', vetala_lib_control2, 'scale', controller)
        graph.add_link(make_array3, 'Array', vetala_lib_control1, 'scale', controller)
        graph.add_link(num, 'Num', 'Equals', 'A', controller)
        graph.add_link(num, 'Num', equals, 'A', controller)
        graph.add_link(set_item_array_metadata, 'ExecuteContext', for_each1, 'ExecuteContext', controller)
        graph.add_link(set_item_metadata, 'ExecuteContext', set_item_metadata1, 'ExecuteContext', controller)
        graph.add_link(set_item_metadata1, 'ExecuteContext', set_item_array_metadata, 'ExecuteContext', controller)
        graph.add_link(set_item_metadata2, 'ExecuteContext', spawn_null3, 'ExecuteContext', controller)
        graph.add_link(set_item_metadata3, 'ExecuteContext', set_vector_metadata, 'ExecuteContext', controller)
        graph.add_link(set_transform, 'ExecuteContext', set_item_metadata, 'ExecuteContext', controller)
        graph.add_link(set_transform1, 'ExecuteContext', vetala_lib_control, 'ExecuteContext', controller)
        graph.add_link(set_transform2, 'ExecuteContext', vetala_lib_control2, 'ExecuteContext', controller)
        graph.add_link(set_transform3, 'ExecuteContext', add1, 'ExecuteContext', controller)
        graph.add_link(set_vector_metadata, 'ExecuteContext', set_vector_metadata1, 'ExecuteContext', controller)
        graph.add_link(spawn_float_animation_channel, 'ExecuteContext', set_name_metadata, 'ExecuteContext', controller)
        graph.add_link(spawn_float_animation_channel, 'Item.Name', set_name_metadata, 'Value', controller)
        graph.add_link(spawn_null1, 'ExecuteContext', set_transform1, 'ExecuteContext', controller)
        graph.add_link(spawn_null1, 'Item', set_transform1, 'Item', controller)
        graph.add_link(spawn_null1, 'Item', vetala_lib_control, 'parent', controller)
        graph.add_link(spawn_null2, 'ExecuteContext', set_transform2, 'ExecuteContext', controller)
        graph.add_link(spawn_null2, 'Item', set_transform2, 'Item', controller)
        graph.add_link(spawn_null2, 'Item', vetala_lib_control2, 'parent', controller)
        graph.add_link(spawn_null3, 'ExecuteContext', spawn_null1, 'ExecuteContext', controller)
        graph.add_link(spawn_null3, 'Item', spawn_null1, 'Parent', controller)
        graph.add_link(spawn_null3, 'Item', spawn_null2, 'Parent', controller)
        graph.add_link(spawn_transform_control, 'ExecuteContext', add2, 'ExecuteContext', controller)
        graph.add_link(spawn_transform_control, 'Item', add2, 'Element', controller)
        graph.add_link(spawn_transform_control1, 'ExecuteContext', vetala_lib_control1, 'ExecuteContext', controller)
        graph.add_link(spawn_transform_control1, 'Item', vetala_lib_control1, 'parent', controller)
        graph.add_link(vetala_lib_control, 'ExecuteContext', add, 'ExecuteContext', controller)
        graph.add_link(vetala_lib_control, 'Last Control', add, 'Element', controller)
        graph.add_link(vetala_lib_control, 'Last Control', set_item_metadata, 'Value', controller)
        graph.add_link(vetala_lib_control, 'Last Control', set_name_metadata, 'Item', controller)
        graph.add_link(vetala_lib_control1, 'ExecuteContext', set_transform3, 'ExecuteContext', controller)
        graph.add_link(vetala_lib_control1, 'Last Control', add1, 'Element', controller)
        graph.add_link(vetala_lib_control1, 'Last Control', set_item_metadata3, 'Value', controller)
        graph.add_link(vetala_lib_control1, 'Last Control', set_transform3, 'Item', controller)
        graph.add_link(vetala_lib_control2, 'ExecuteContext', add3, 'ExecuteContext', controller)
        graph.add_link(vetala_lib_control2, 'Last Control', add3, 'Element', controller)
        graph.add_link(vetala_lib_control2, 'Last Control', get_relative_transform, 'Child', controller)
        graph.add_link(vetala_lib_control2, 'Last Control', set_item_metadata1, 'Value', controller)
        graph.add_link(vetala_lib_control2, 'Last Control', set_transform, 'Item', controller)
        graph.add_link(vetala_lib_get_item, 'Element', set_item_array_metadata, 'Item', controller)

        graph.add_link(vetala_lib_get_item2, 'Element', set_item_metadata3, 'Item', controller)
        graph.add_link(vetala_lib_get_item2, 'Element', set_vector_metadata, 'Item', controller)
        graph.add_link(vetala_lib_get_item2, 'Element', set_vector_metadata1, 'Item', controller)
        graph.add_link(vetala_lib_get_item3, 'Element', get_transform1, 'Item', controller)
        graph.add_link(vetala_lib_get_item3, 'Element', get_transform2, 'Item', controller)
        graph.add_link(vetala_lib_get_item3, 'Element', vetala_lib_control, 'driven', controller)
        graph.add_link(vetala_lib_get_item4, 'Element', set_item_metadata, 'Item', controller)
        graph.add_link(vetala_lib_get_item4, 'Element', set_item_metadata1, 'Item', controller)
        graph.add_link(vetala_lib_get_item5, 'Element', set_item_metadata2, 'Value', controller)
        graph.add_link(vetala_lib_get_item_vector3, 'Element', multiply, 'A', controller)
        graph.add_link(vetala_lib_get_item_vector4, 'Element', multiply1, 'A', controller)
        graph.add_link(vetala_lib_get_item_vector5, 'Element', set_vector_metadata, 'Value', controller)
        graph.add_link(vetala_lib_get_item_vector6, 'Element', set_vector_metadata1, 'Value', controller)
        graph.add_link(vetala_lib_get_parent, 'Result', spawn_transform_control, 'Parent', controller)
        graph.add_link(at2, 'Element', join, 'Values.1', controller)
        graph.add_link(get_description, 'Value', join1, 'Values.0', controller)
        graph.add_link(get_description, 'Value', join2, 'Values.0', controller)
        graph.add_link(get_description, 'Value', join4, 'Values.0', controller)
        graph.add_link(get_description1, 'Value', join, 'Values.0', controller)
        graph.add_link(join, 'Result', join3, 'Values.1', controller)
        graph.add_link(multiply, 'Result', make_array2, 'Values.0', controller)
        graph.add_link(multiply1, 'Result', make_array3, 'Values.0', controller)
        graph.add_link(get_transform, 'Transform.Rotation', make_array, 'Values.0.Rotation', controller)
        graph.add_link(get_transform, 'Transform.Rotation', make_array, 'Values.1.Rotation', controller)
        graph.add_link(get_transform, 'Transform.Rotation', make_array, 'Values.2.Rotation', controller)
        graph.add_link(get_transform, 'Transform.Rotation', make_array, 'Values.3.Rotation', controller)
        graph.add_link(get_transform, 'Transform.Translation', make_array, 'Values.0.Translation', controller)
        graph.add_link(vetala_lib_get_item_vector, 'Element', make_array, 'Values.1.Translation', controller)
        graph.add_link(vetala_lib_get_item_vector1, 'Element', make_array, 'Values.2.Translation', controller)
        graph.add_link(vetala_lib_get_item_vector2, 'Element', make_array, 'Values.3.Translation', controller)

        controller.set_pin_default_value(f'{n(vetala_lib_control)}.increment', '0', False)
        controller.set_pin_default_value(f'{n(vetala_lib_control)}.sub_count', '0', False)
        controller.set_pin_default_value(f'{n(vetala_lib_get_parent)}.in_hierarchy', 'False', False)
        controller.set_pin_default_value(f'{n(equals)}.B', '3', False)
        controller.set_pin_default_value(f'{n(at)}.Index', '0', False)
        controller.set_pin_default_value(f'{n(vetala_lib_control1)}.increment', '0', False)
        controller.set_pin_default_value(f'{n(vetala_lib_control1)}.sub_count', '0', False)
        controller.set_pin_default_value(f'{n(at1)}.Index', '2', False)
        controller.set_pin_default_value(f'{n(make_array)}.Values', '((Rotation=(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=1.000000,Y=1.000000,Z=1.000000)),(Rotation=(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=1.000000,Y=1.000000,Z=1.000000)),(Rotation=(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=1.000000,Y=1.000000,Z=1.000000)),(Rotation=(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=1.000000,Y=1.000000,Z=1.000000)))', False)
        controller.set_pin_default_value(f'{n(get_transform)}.Space', 'GlobalSpace', False)
        controller.set_pin_default_value(f'{n(get_transform)}.bInitial', 'False', False)
        controller.set_pin_default_value(f'{n(make_array1)}.Values', '("toe","heel","yaw_out","yaw_in")', False)
        controller.set_pin_default_value(f'{n(join)}.Values', '("","")', False)
        controller.set_pin_default_value(f'{n(join)}.Separator', '_', False)
        controller.set_pin_default_value(f'{n(at3)}.Index', '-1', False)
        controller.set_pin_default_value(f'{n(join1)}.Values', '("","ball")', False)
        controller.set_pin_default_value(f'{n(join1)}.Separator', '_', False)
        controller.set_pin_default_value(f'{n(at4)}.Index', '-1', False)
        controller.set_pin_default_value(f'{n(vetala_lib_control2)}.increment', '0', False)
        controller.set_pin_default_value(f'{n(vetala_lib_control2)}.sub_count', '0', False)
        controller.set_pin_default_value(f'{n(join2)}.Values', '("","ankle")', False)
        controller.set_pin_default_value(f'{n(join2)}.Separator', '_', False)
        controller.set_pin_default_value(f'{n(get_transform1)}.Space', 'GlobalSpace', False)
        controller.set_pin_default_value(f'{n(get_transform1)}.bInitial', 'False', False)
        controller.set_pin_default_value(f'{n(set_transform)}.Space', 'GlobalSpace', False)
        controller.set_pin_default_value(f'{n(set_transform)}.bInitial', 'true', False)
        controller.set_pin_default_value(f'{n(set_transform)}.Weight', '1.000000', False)
        controller.set_pin_default_value(f'{n(set_transform)}.bPropagateToChildren', 'True', False)
        controller.set_pin_default_value(f'{n(set_item_metadata1)}.Name', 'ik', False)
        controller.set_pin_default_value(f'{n(multiply)}.B', '(X=0.750000,Y=0.750000,Z=0.750000)', False)
        controller.set_pin_default_value(f'{n(make_array2)}.Values', '((X=0.000000,Y=0.000000,Z=0.000000))', False)
        controller.set_pin_default_value(f'{n(multiply1)}.B', '(X=0.200000,Y=0.200000,Z=0.200000)', False)
        controller.set_pin_default_value(f'{n(make_array3)}.Values', '((X=0.000000,Y=0.000000,Z=0.000000))', False)
        controller.set_pin_default_value(f'{n(set_item_array_metadata)}.Name', 'ik', False)
        controller.set_pin_default_value(f'{n(get_item_metadata)}.Name', 'main', False)
        controller.set_pin_default_value(f'{n(get_item_metadata)}.Default', '(Type=Bone,Name="None")', False)
        controller.set_pin_default_value(f'{n(spawn_float_animation_channel)}.MinimumValue', '-90.000000', False)
        controller.set_pin_default_value(f'{n(spawn_float_animation_channel)}.MaximumValue', '90.000000', False)
        controller.set_pin_default_value(f'{n(make_array4)}.Values', '("roll","rollOffset","ankle","heel","ball","toe","toeRotate","yaw","toePivot","ballPivot","heelPivot")', False)
        controller.set_pin_default_value(f'{n(vetala_lib_get_item2)}.index', '-1', False)
        controller.set_pin_default_value(f'{n(set_vector_metadata)}.Name', 'forward_axis', False)
        controller.set_pin_default_value(f'{n(set_vector_metadata1)}.Name', 'up_axis', False)
        controller.set_pin_default_value(f'{n(get_relative_transform)}.bChildInitial', 'False', False)
        controller.set_pin_default_value(f'{n(get_relative_transform)}.bParentInitial', 'False', False)
        controller.set_pin_default_value(f'{n(spawn_null1)}.Transform', '(Rotation=(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=1.000000,Y=1.000000,Z=1.000000))', False)
        controller.set_pin_default_value(f'{n(spawn_null1)}.Space', 'LocalSpace', False)
        controller.set_pin_default_value(f'{n(set_transform1)}.Space', 'GlobalSpace', False)
        controller.set_pin_default_value(f'{n(set_transform1)}.bInitial', 'true', False)
        controller.set_pin_default_value(f'{n(set_transform1)}.Weight', '1.000000', False)
        controller.set_pin_default_value(f'{n(set_transform1)}.bPropagateToChildren', 'True', False)
        controller.set_pin_default_value(f'{n(get_transform2)}.Space', 'GlobalSpace', False)
        controller.set_pin_default_value(f'{n(get_transform2)}.bInitial', 'false', False)
        controller.set_pin_default_value(f'{n(spawn_null2)}.Transform', '(Rotation=(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=1.000000,Y=1.000000,Z=1.000000))', False)
        controller.set_pin_default_value(f'{n(spawn_null2)}.Space', 'LocalSpace', False)
        controller.set_pin_default_value(f'{n(vetala_lib_get_item3)}.index', '1', False)
        controller.set_pin_default_value(f'{n(set_transform2)}.Space', 'GlobalSpace', False)
        controller.set_pin_default_value(f'{n(set_transform2)}.bInitial', 'true', False)
        controller.set_pin_default_value(f'{n(set_transform2)}.Weight', '1.000000', False)
        controller.set_pin_default_value(f'{n(set_transform2)}.bPropagateToChildren', 'True', False)
        controller.set_pin_default_value(f'{n(vetala_lib_get_item4)}.index', '1', False)
        controller.set_pin_default_value(f'{n(spawn_transform_control)}.Name', 'null_foot_roll', False)
        controller.set_pin_default_value(f'{n(spawn_transform_control)}.OffsetTransform', '(Rotation=(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=1.000000,Y=1.000000,Z=1.000000))', False)
        controller.set_pin_default_value(f'{n(spawn_transform_control)}.OffsetSpace', 'LocalSpace', False)
        controller.set_pin_default_value(f'{n(spawn_transform_control)}.InitialValue', '(Rotation=(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=1.000000,Y=1.000000,Z=1.000000))', False)
        controller.set_pin_default_value(f'{n(spawn_transform_control)}.Settings', '(DisplayName="None",InitialSpace=LocalSpace,Shape=(bVisible=true,Name="Default",Color=(R=0.020000,G=0.020000,B=0.020000,A=1.000000),Transform=(Rotation=(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=0.050000,Y=0.050000,Z=0.050000))),Proxy=(bIsProxy=true,ShapeVisibility=BasedOnSelection))', False)
        controller.set_pin_default_value(f'{n(spawn_transform_control1)}.OffsetSpace', 'GlobalSpace', False)
        controller.set_pin_default_value(f'{n(spawn_transform_control1)}.InitialValue', '(Rotation=(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=1.000000,Y=1.000000,Z=1.000000))', False)
        controller.set_pin_default_value(f'{n(spawn_transform_control1)}.Settings', '(DisplayName="None",InitialSpace=LocalSpace,Shape=(bVisible=true,Name="Default",Color=(R=0.020000,G=0.020000,B=0.020000,A=1.000000),Transform=(Rotation=(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=0.050000,Y=0.050000,Z=0.050000))),Proxy=(bIsProxy=true,ShapeVisibility=BasedOnSelection))', False)
        controller.set_pin_default_value(f'{n(set_transform3)}.Space', 'GlobalSpace', False)
        controller.set_pin_default_value(f'{n(set_transform3)}.bInitial', 'true', False)
        controller.set_pin_default_value(f'{n(set_transform3)}.Weight', '1.000000', False)
        controller.set_pin_default_value(f'{n(set_transform3)}.bPropagateToChildren', 'True', False)
        controller.set_pin_default_value(f'{n(join3)}.Values', '("null","")', False)
        controller.set_pin_default_value(f'{n(join3)}.Separator', '_', False)
        controller.set_pin_default_value(f'{n(equals1)}.B', 'rollOffset', False)
        controller.set_pin_default_value(f'{n(if2)}.True', '30.000000', False)
        controller.set_pin_default_value(f'{n(spawn_null3)}.Space', 'GlobalSpace', False)
        controller.set_pin_default_value(f'{n(join4)}.Values', '("","ball","pivot")', False)
        controller.set_pin_default_value(f'{n(join4)}.Separator', '_', False)
        controller.set_pin_default_value(f'{n(vetala_lib_get_item5)}.index', '1', False)
        controller.set_pin_default_value(f'{n(vetala_lib_get_item1)}.index', '-1', False)

        current_locals = locals()
        nodes = unreal_lib.graph.filter_nodes(current_locals.values())
        node = unreal_lib.graph.comment_nodes(nodes, controller, 'Construction')
        nodes.append(node)
        unreal_lib.graph.move_nodes(500, -3000, nodes, controller)

    def _build_function_forward_graph(self):

        controller = self.function_controller
        library = graph.get_local_function_library()

        get_control_layer = controller.add_variable_node('control_layer', 'FName', None, True, '', unreal.Vector2D(1072.0, 1892.0), 'Get control_layer')
        get_item_metadata = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in Default,out Value,out Found)', unreal.Vector2D(1712.0, 1376.0), 'Get Item Metadata')
        set_transform = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_SetTransform', 'Execute', unreal.Vector2D(3264.0, 592.0), 'Set Transform')
        project_to_new_parent = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_ProjectTransformToNewParent', 'Execute', unreal.Vector2D(2864.0, 448.0), 'Project to new Parent')
        get_transform = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetTransform', 'Execute', unreal.Vector2D(2535.0, 1524.0), 'Get Transform')
        vetala_lib_get_item = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(1312.0, 2276.0), 'vetalaLib_GetItem')
        get_item_metadata1 = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in Default,out Value,out Found)', unreal.Vector2D(1712.0, 1972.0), 'Get Item Metadata')
        vetala_lib_get_item1 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(1296.0, 1540.0), 'vetalaLib_GetItem')
        basic_fabrik = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_FABRIKItemArray', 'Execute', unreal.Vector2D(3552.0, 1360.0), 'Basic FABRIK')
        make_array = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayMake(in Values,out Array)', unreal.Vector2D(2566.0, 2260.0), 'Make Array')
        basic_fabrik1 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_FABRIKItemArray', 'Execute', unreal.Vector2D(3088.0, 1328.0), 'Basic FABRIK')
        make_array1 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayMake(in Values,out Array)', unreal.Vector2D(2566.0, 1284.0), 'Make Array')
        get_item_metadata2 = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in Default,out Value,out Found)', unreal.Vector2D(1712.0, 1732.0), 'Get Item Metadata')
        project_to_new_parent1 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_ProjectTransformToNewParent', 'Execute', unreal.Vector2D(2534.0, 1780.0), 'Project to new Parent')
        vetala_lib_get_item2 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(816.0, 1200.0), 'vetalaLib_GetItem')
        item_exists = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_ItemExists', 'Execute', unreal.Vector2D(1584.0, 752.0), 'Item Exists')
        branch = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_ControlFlowBranch', 'Execute', unreal.Vector2D(1968.0, 512.0), 'Branch')
        vetala_lib_get_item3 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(1312.0, 952.0), 'vetalaLib_GetItem')
        get_item_array_metadata = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in Default,out Value,out Found)', unreal.Vector2D(1024.0, 921.0), 'Get Item Array Metadata')
        get_item_metadata3 = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in Default,out Value,out Found)', unreal.Vector2D(1712.0, 1168.0), 'Get Item Metadata')
        make_array2 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayMake(in Values,out Array)', unreal.Vector2D(3984.0, 1552.0), 'Make Array')
        at = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(4528.0, 1589.0), 'At')
        get_name_metadata = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in Default,out Value,out Found)', unreal.Vector2D(4768.0, 1589.0), 'Get Name Metadata')
        get_control_float = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetControlFloat', 'Execute', unreal.Vector2D(5104.0, 1589.0), 'Get Control Float')
        make_array3 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayMake(in Values,out Array)', unreal.Vector2D(4192.0, 720.0), 'Make Array')
        get_item_metadata4 = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in Default,out Value,out Found)', unreal.Vector2D(5152.0, 112.0), 'Get Item Metadata')
        get_joints = controller.add_variable_node_from_object_path('joints', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(4346.0, 1253.0), 'Get joints')
        vetala_lib_get_item4 = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(4522.0, 1253.0), 'vetalaLib_GetItem')
        at1 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(4528.0, 112.0), 'At')
        from_string = controller.add_template_node('DISPATCH_RigDispatch_FromString(in String,out Result)', unreal.Vector2D(4727.0, 112.0), 'From String')
        get_vector_metadata = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in Default,out Value,out Found)', unreal.Vector2D(5952.0, 1216.0), 'Get Vector Metadata')
        cross = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathVectorCross', 'Execute', unreal.Vector2D(6320.0, 1344.0), 'Cross')
        get_vector_metadata1 = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in Default,out Value,out Found)', unreal.Vector2D(5952.0, 1376.0), 'Get Vector Metadata')
        from_axis_and_angle = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathQuaternionFromAxisAndAngle', 'Execute', unreal.Vector2D(6800.0, 1392.0), 'From Axis And Angle')
        multiply = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathDoubleMul', 'Execute', unreal.Vector2D(5840.0, 1744.0), 'Multiply')
        set_rotation = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_SetRotation', 'Execute', unreal.Vector2D(8432.0, 112.0), 'Set Rotation')
        get_item_metadata5 = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in Default,out Value,out Found)', unreal.Vector2D(5152.0, 336.0), 'Get Item Metadata')
        at2 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(4537.0, 336.0), 'At')
        from_string1 = controller.add_template_node('DISPATCH_RigDispatch_FromString(in String,out Result)', unreal.Vector2D(4736.0, 336.0), 'From String')
        get_item_metadata6 = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in Default,out Value,out Found)', unreal.Vector2D(5152.0, 560.0), 'Get Item Metadata')
        at3 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(4537.0, 560.0), 'At')
        from_string2 = controller.add_template_node('DISPATCH_RigDispatch_FromString(in String,out Result)', unreal.Vector2D(4736.0, 560.0), 'From String')
        get_item_metadata7 = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in Default,out Value,out Found)', unreal.Vector2D(5152.0, 784.0), 'Get Item Metadata')
        at4 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(4537.0, 784.0), 'At')
        from_string3 = controller.add_template_node('DISPATCH_RigDispatch_FromString(in String,out Result)', unreal.Vector2D(4736.0, 784.0), 'From String')
        evaluate_curve = controller.add_unit_node_with_defaults(unreal.load_object(None, '/Script/RigVM.RigVMFunction_AnimEvalRichCurve'), '(Value=0.000000,Curve=(EditorCurveData=(Keys=((),(Time=0.500000,Value=1.000000),(Time=1.000000)))),SourceMinimum=0.000000,SourceMaximum=1.000000,TargetMinimum=0.000000,TargetMaximum=1.000000,Result=0.000000)', 'Execute', unreal.Vector2D(6272.0, 1776.0), 'Evaluate Curve')
        from_axis_and_angle1 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathQuaternionFromAxisAndAngle', 'Execute', unreal.Vector2D(7120.0, 1616.0), 'From Axis And Angle')
        get_parent = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyGetParent', 'Execute', unreal.Vector2D(5984.0, 144.0), 'Get Parent')
        negate = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathVectorNegate', 'Execute', unreal.Vector2D(6576.0, 1328.0), 'Negate')
        from_axis_and_angle2 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathQuaternionFromAxisAndAngle', 'Execute', unreal.Vector2D(6800.0, 1216.0), 'From Axis And Angle')
        get_parent1 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyGetParent', 'Execute', unreal.Vector2D(5984.0, 912.0), 'Get Parent')
        set_rotation1 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_SetRotation', 'Execute', unreal.Vector2D(8432.0, 736.0), 'Set Rotation')
        radians = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathDoubleRad', 'Execute', unreal.Vector2D(6912.0, 1792.0), 'Radians')
        multiply1 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathDoubleMul', 'Execute', unreal.Vector2D(6752.0, 1968.0), 'Multiply')
        get_control_float1 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetControlFloat', 'Execute', unreal.Vector2D(5104.0, 2144.0), 'Get Control Float')
        get_name_metadata1 = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in Default,out Value,out Found)', unreal.Vector2D(4768.0, 2133.0), 'Get Name Metadata')
        evaluate_curve1 = controller.add_unit_node_with_defaults(unreal.load_object(None, '/Script/RigVM.RigVMFunction_AnimEvalRichCurve'), '(Value=0.000000,Curve=(EditorCurveData=(Keys=((),(Time=0.250000),(InterpMode=RCIM_Constant,Time=1.000000,Value=1.000000)))),SourceMinimum=0.000000,SourceMaximum=2.000000,TargetMinimum=0.000000,TargetMaximum=90.000000,Result=0.000000)', 'Execute', unreal.Vector2D(6272.0, 2224.0), 'Evaluate Curve')
        radians1 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathDoubleRad', 'Execute', unreal.Vector2D(6859.0, 2615.0), 'Radians')
        from_axis_and_angle3 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathQuaternionFromAxisAndAngle', 'Execute', unreal.Vector2D(7120.0, 2368.0), 'From Axis And Angle')
        evaluate_curve2 = controller.add_unit_node_with_defaults(unreal.load_object(None, '/Script/RigVM.RigVMFunction_AnimEvalRichCurve'), '(Value=0.000000,Curve=(EditorCurveData=(Keys=((),(InterpMode=RCIM_Constant,Time=1.000000,Value=1.000000)))),SourceMinimum=0.000000,SourceMaximum=2.000000,TargetMinimum=0.000000,TargetMaximum=-90.000000,Result=0.000000)', 'Execute', unreal.Vector2D(6272.0, 2688.0), 'Evaluate Curve')
        multiply2 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathDoubleMul', 'Execute', unreal.Vector2D(5840.0, 2304.0), 'Multiply')
        set_rotation2 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_SetRotation', 'Execute', unreal.Vector2D(8432.0, 400.0), 'Set Rotation')
        get_parent2 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyGetParent', 'Execute', unreal.Vector2D(5984.0, 384.0), 'Get Parent')
        from_axis_and_angle4 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathQuaternionFromAxisAndAngle', 'Execute', unreal.Vector2D(7120.0, 3040.0), 'From Axis And Angle')
        radians2 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathDoubleRad', 'Execute', unreal.Vector2D(6880.0, 3072.0), 'Radians')
        multiply3 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathDoubleMul', 'Execute', unreal.Vector2D(5840.0, 2016.0), 'Multiply')
        at5 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(4576.0, 2965.0), 'At')
        get_name_metadata2 = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in Default,out Value,out Found)', unreal.Vector2D(4816.0, 2944.0), 'Get Name Metadata')
        get_control_float2 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetControlFloat', 'Execute', unreal.Vector2D(5152.0, 2955.0), 'Get Control Float')
        from_axis_and_angle5 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathQuaternionFromAxisAndAngle', 'Execute', unreal.Vector2D(7120.0, 3472.0), 'From Axis And Angle')
        multiply4 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathQuaternionMul', 'Execute', unreal.Vector2D(7616.0, 3264.0), 'Multiply')
        at6 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(4528.0, 3258.0), 'At')
        get_name_metadata3 = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in Default,out Value,out Found)', unreal.Vector2D(4832.0, 3237.0), 'Get Name Metadata')
        get_control_float3 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetControlFloat', 'Execute', unreal.Vector2D(5168.0, 3248.0), 'Get Control Float')
        from_axis_and_angle6 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathQuaternionFromAxisAndAngle', 'Execute', unreal.Vector2D(7136.0, 3696.0), 'From Axis And Angle')
        multiply5 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathQuaternionMul', 'Execute', unreal.Vector2D(7984.0, 3680.0), 'Multiply')
        rig_element_key = controller.add_free_reroute_node('FRigElementKey', unreal.load_object(None, '/Script/ControlRig.RigElementKey').get_name(), is_constant=False, custom_widget_name='', default_value='', position=[3875.0, 2088.0], node_name='', setup_undo_redo=True)
        at7 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(4528.0, 2032.0), 'At')
        at8 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(4528.0, 3589.0), 'At')
        get_name_metadata4 = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in Default,out Value,out Found)', unreal.Vector2D(4832.0, 3568.0), 'Get Name Metadata')
        get_control_float4 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetControlFloat', 'Execute', unreal.Vector2D(5168.0, 3579.0), 'Get Control Float')
        from_axis_and_angle7 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathQuaternionFromAxisAndAngle', 'Execute', unreal.Vector2D(7136.0, 3904.0), 'From Axis And Angle')
        multiply6 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathQuaternionMul', 'Execute', unreal.Vector2D(7645.0, 3920.0), 'Multiply')
        at9 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(4528.0, 3893.0), 'At')
        get_name_metadata5 = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in Default,out Value,out Found)', unreal.Vector2D(4832.0, 3872.0), 'Get Name Metadata')
        get_control_float5 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetControlFloat', 'Execute', unreal.Vector2D(5168.0, 3883.0), 'Get Control Float')
        get_parent3 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyGetParent', 'Execute', unreal.Vector2D(5984.0, 1072.0), 'Get Parent')
        set_rotation3 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_SetRotation', 'Execute', unreal.Vector2D(8416.0, 1024.0), 'Set Rotation')
        from_axis_and_angle8 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathQuaternionFromAxisAndAngle', 'Execute', unreal.Vector2D(7120.0, 4128.0), 'From Axis And Angle')
        from_axis_and_angle9 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathQuaternionFromAxisAndAngle', 'Execute', unreal.Vector2D(6560.0, 3504.0), 'From Axis And Angle')
        at10 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(4576.0, 2677.0), 'At')
        get_name_metadata6 = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in Default,out Value,out Found)', unreal.Vector2D(4816.0, 2656.0), 'Get Name Metadata')
        get_control_float6 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetControlFloat', 'Execute', unreal.Vector2D(5152.0, 2667.0), 'Get Control Float')
        multiply7 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathQuaternionMul', 'Execute', unreal.Vector2D(8208.0, 3600.0), 'Multiply')
        execute_context = controller.add_free_reroute_node('FRigVMExecuteContext', unreal.load_object(None, '/Script/RigVM.RigVMExecuteContext').get_name(), is_constant=False, custom_widget_name='', default_value='', position=[4053.0, 1368.0], node_name='', setup_undo_redo=True)
        at11 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(4528.0, 4165.0), 'At')
        get_name_metadata7 = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in Default,out Value,out Found)', unreal.Vector2D(4832.0, 4144.0), 'Get Name Metadata')
        get_control_float7 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetControlFloat', 'Execute', unreal.Vector2D(5168.0, 4155.0), 'Get Control Float')
        greater = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathDoubleGreater', 'Execute', unreal.Vector2D(6976.0, 4528.0), 'Greater')
        if1 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(7232.0, 4544.0), 'If')
        from_axis_and_angle10 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathQuaternionFromAxisAndAngle', 'Execute', unreal.Vector2D(7088.0, 4720.0), 'From Axis And Angle')
        negate1 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathVectorNegate', 'Execute', unreal.Vector2D(6336.0, 3856.0), 'Negate')
        from_axis_and_angle11 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathQuaternionFromAxisAndAngle', 'Execute', unreal.Vector2D(7088.0, 4864.0), 'From Axis And Angle')
        if2 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(7136.0, 5072.0), 'If')
        less = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathDoubleLess', 'Execute', unreal.Vector2D(6928.0, 5072.0), 'Less')
        get_parent4 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyGetParent', 'Execute', unreal.Vector2D(6000.0, 560.0), 'Get Parent')
        get_parent5 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyGetParent', 'Execute', unreal.Vector2D(6000.0, 688.0), 'Get Parent')
        set_rotation4 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_SetRotation', 'Execute', unreal.Vector2D(8416.0, 1360.0), 'Set Rotation')
        set_rotation5 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_SetRotation', 'Execute', unreal.Vector2D(8400.0, 1648.0), 'Set Rotation')
        multiply8 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathDoubleMul', 'Execute', unreal.Vector2D(6480.0, 4880.0), 'Multiply')
        at12 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(4528.0, 4453.0), 'At')
        get_name_metadata8 = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in Default,out Value,out Found)', unreal.Vector2D(4832.0, 4432.0), 'Get Name Metadata')
        get_control_float8 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetControlFloat', 'Execute', unreal.Vector2D(5168.0, 4443.0), 'Get Control Float')
        at13 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(4528.0, 4677.0), 'At')
        get_name_metadata9 = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in Default,out Value,out Found)', unreal.Vector2D(4832.0, 4656.0), 'Get Name Metadata')
        get_control_float9 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetControlFloat', 'Execute', unreal.Vector2D(5168.0, 4667.0), 'Get Control Float')
        at14 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(4528.0, 4885.0), 'At')
        get_name_metadata10 = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in Default,out Value,out Found)', unreal.Vector2D(4832.0, 4864.0), 'Get Name Metadata')
        get_control_float10 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetControlFloat', 'Execute', unreal.Vector2D(5168.0, 4875.0), 'Get Control Float')
        from_axis_and_angle12 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathQuaternionFromAxisAndAngle', 'Execute', unreal.Vector2D(7120.0, 5328.0), 'From Axis And Angle')
        multiply9 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathQuaternionMul', 'Execute', unreal.Vector2D(8288.0, 4288.0), 'Multiply')
        from_axis_and_angle13 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathQuaternionFromAxisAndAngle', 'Execute', unreal.Vector2D(7136.0, 5536.0), 'From Axis And Angle')
        vector = controller.add_free_reroute_node('FVector', unreal.load_object(None, '/Script/CoreUObject.Vector').get_name(), is_constant=False, custom_widget_name='', default_value='', position=[6288.0, 5472.0], node_name='', setup_undo_redo=True)
        vector1 = controller.add_free_reroute_node('FVector', unreal.load_object(None, '/Script/CoreUObject.Vector').get_name(), is_constant=False, custom_widget_name='', default_value='', position=[5968.0, 3856.0], node_name='', setup_undo_redo=True)
        get_parent6 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyGetParent', 'Execute', unreal.Vector2D(6368.0, 896.0), 'Get Parent')
        set_rotation6 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_SetRotation', 'Execute', unreal.Vector2D(8912.0, 528.0), 'Set Rotation')
        from_axis_and_angle14 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathQuaternionFromAxisAndAngle', 'Execute', unreal.Vector2D(7120.0, 5728.0), 'From Axis And Angle')
        multiply10 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathQuaternionMul', 'Execute', unreal.Vector2D(8176.0, 3312.0), 'Multiply')
        radians3 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathDoubleRad', 'Execute', unreal.Vector2D(5605.0, 3114.0), 'Radians')
        radians4 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathDoubleRad', 'Execute', unreal.Vector2D(5588.0, 2908.0), 'Radians')
        radians5 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathDoubleRad', 'Execute', unreal.Vector2D(5617.0, 3429.0), 'Radians')
        radians6 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathDoubleRad', 'Execute', unreal.Vector2D(5648.0, 3664.0), 'Radians')
        radians7 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathDoubleRad', 'Execute', unreal.Vector2D(5632.0, 3952.0), 'Radians')
        radians8 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathDoubleRad', 'Execute', unreal.Vector2D(5648.0, 4304.0), 'Radians')
        radians9 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathDoubleRad', 'Execute', unreal.Vector2D(5666.0, 4618.0), 'Radians')
        radians10 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathDoubleRad', 'Execute', unreal.Vector2D(5773.0, 4916.0), 'Radians')
        radians11 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathDoubleRad', 'Execute', unreal.Vector2D(5806.0, 5104.0), 'Radians')

        controller.set_array_pin_size(f'{n(make_array)}.Values', 2)
        controller.set_array_pin_size(f'{n(make_array1)}.Values', 2)
        controller.set_array_pin_size(f'{n(make_array2)}.Values', 11)
        controller.set_array_pin_size(f'{n(make_array3)}.Values', 4)

        graph.add_link('DISPATCH_RigVMDispatch_SwitchInt32', 'Cases.1', branch, 'ExecuteContext', controller)
        graph.add_link('Entry', 'joints', vetala_lib_get_item, 'Array', controller)
        graph.add_link('Entry', 'joints', vetala_lib_get_item1, 'Array', controller)
        graph.add_link('Entry', 'joints', vetala_lib_get_item2, 'Array', controller)
        graph.add_link(at, 'Element', get_name_metadata, 'Name', controller)
        graph.add_link(at1, 'Element', from_string, 'String', controller)
        graph.add_link(at10, 'Element', get_name_metadata6, 'Name', controller)
        graph.add_link(at11, 'Element', get_name_metadata7, 'Name', controller)
        graph.add_link(at12, 'Element', get_name_metadata8, 'Name', controller)
        graph.add_link(at13, 'Element', get_name_metadata9, 'Name', controller)
        graph.add_link(at14, 'Element', get_name_metadata10, 'Name', controller)
        graph.add_link(at2, 'Element', from_string1, 'String', controller)
        graph.add_link(at3, 'Element', from_string2, 'String', controller)
        graph.add_link(at4, 'Element', from_string3, 'String', controller)
        graph.add_link(at5, 'Element', get_name_metadata2, 'Name', controller)
        graph.add_link(at6, 'Element', get_name_metadata3, 'Name', controller)
        graph.add_link(at7, 'Element', get_name_metadata1, 'Name', controller)
        graph.add_link(at8, 'Element', get_name_metadata4, 'Name', controller)
        graph.add_link(at9, 'Element', get_name_metadata5, 'Name', controller)
        graph.add_link(basic_fabrik, 'ExecuteContext', execute_context, 'Value', controller)
        graph.add_link(basic_fabrik1, 'ExecuteContext', basic_fabrik, 'ExecuteContext', controller)
        graph.add_link(branch, 'Completed', basic_fabrik1, 'ExecuteContext', controller)
        graph.add_link(branch, 'True', set_transform, 'ExecuteContext', controller)
        graph.add_link(cross, 'Result', from_axis_and_angle, 'Axis', controller)
        graph.add_link(cross, 'Result', from_axis_and_angle5, 'Axis', controller)
        graph.add_link(cross, 'Result', negate, 'Value', controller)
        graph.add_link(evaluate_curve, 'Result', multiply1, 'A', controller)
        graph.add_link(evaluate_curve1, 'Result', radians1, 'Value', controller)
        graph.add_link(evaluate_curve2, 'Result', radians2, 'Value', controller)
        graph.add_link(execute_context, 'Value', set_rotation, 'ExecuteContext', controller)
        graph.add_link(from_axis_and_angle1, 'Result', multiply5, 'A', controller)
        graph.add_link(from_axis_and_angle10, 'Result', if1, 'True', controller)
        graph.add_link(from_axis_and_angle11, 'Result', if2, 'True', controller)
        graph.add_link(from_axis_and_angle12, 'Result', multiply9, 'B', controller)
        graph.add_link(from_axis_and_angle13, 'Result', set_rotation6, 'Value', controller)
        graph.add_link(from_axis_and_angle14, 'Result', multiply10, 'B', controller)
        graph.add_link(from_axis_and_angle3, 'Result', multiply6, 'A', controller)
        graph.add_link(from_axis_and_angle4, 'Result', multiply4, 'A', controller)
        graph.add_link(from_axis_and_angle5, 'Result', multiply4, 'B', controller)
        graph.add_link(from_axis_and_angle6, 'Result', multiply5, 'B', controller)
        graph.add_link(from_axis_and_angle7, 'Result', multiply6, 'B', controller)
        graph.add_link(from_axis_and_angle8, 'Result', set_rotation3, 'Value', controller)
        graph.add_link(from_axis_and_angle9, 'Result', multiply7, 'A', controller)
        graph.add_link(from_string, 'Result', get_item_metadata4, 'Name', controller)
        graph.add_link(from_string1, 'Result', get_item_metadata5, 'Name', controller)
        graph.add_link(from_string2, 'Result', get_item_metadata6, 'Name', controller)
        graph.add_link(from_string3, 'Result', get_item_metadata7, 'Name', controller)
        graph.add_link(get_control_float, 'FloatValue', multiply, 'A', controller)
        graph.add_link(get_control_float, 'FloatValue', multiply2, 'A', controller)
        graph.add_link(get_control_float, 'FloatValue', multiply3, 'A', controller)
        graph.add_link(get_control_float1, 'FloatValue', multiply1, 'B', controller)
        graph.add_link(get_control_float10, 'FloatValue', radians11, 'Value', controller)
        graph.add_link(get_control_float2, 'FloatValue', radians3, 'Value', controller)
        graph.add_link(get_control_float3, 'FloatValue', radians5, 'Value', controller)
        graph.add_link(get_control_float4, 'FloatValue', radians6, 'Value', controller)
        graph.add_link(get_control_float5, 'FloatValue', radians7, 'Value', controller)
        graph.add_link(get_control_float6, 'FloatValue', radians4, 'Value', controller)
        graph.add_link(get_control_float7, 'FloatValue', radians8, 'Value', controller)
        graph.add_link(get_control_float8, 'FloatValue', radians9, 'Value', controller)
        graph.add_link(get_control_float9, 'FloatValue', radians10, 'Value', controller)
        graph.add_link(get_control_layer, 'Value', get_item_metadata1, 'Name', controller)
        graph.add_link(get_control_layer, 'Value', get_item_metadata2, 'Name', controller)
        graph.add_link(get_control_layer, 'Value', get_item_metadata3, 'Name', controller)
        graph.add_link(get_item_array_metadata, 'Value', vetala_lib_get_item3, 'Array', controller)
        graph.add_link(get_item_metadata, 'Value', get_parent1, 'Child', controller)
        graph.add_link(get_item_metadata, 'Value', project_to_new_parent, 'NewParent', controller)
        graph.add_link(get_item_metadata, 'Value', project_to_new_parent, 'OldParent', controller)
        graph.add_link(get_item_metadata1, 'Value', project_to_new_parent1, 'Child', controller)
        graph.add_link(get_item_metadata2, 'Value', get_transform, 'Item', controller)
        graph.add_link(get_item_metadata2, 'Value', project_to_new_parent1, 'NewParent', controller)
        graph.add_link(get_item_metadata2, 'Value', project_to_new_parent1, 'OldParent', controller)
        graph.add_link(get_item_metadata2, 'Value', rig_element_key, 'Value', controller)
        graph.add_link(get_item_metadata4, 'Value', get_parent, 'Child', controller)
        graph.add_link(get_item_metadata5, 'Value', get_parent2, 'Child', controller)
        graph.add_link(get_item_metadata6, 'Value', get_parent4, 'Child', controller)
        graph.add_link(get_item_metadata7, 'Value', get_parent5, 'Child', controller)
        graph.add_link(get_joints, 'Value', vetala_lib_get_item4, 'Array', controller)
        graph.add_link(get_name_metadata, 'Value', get_control_float, 'Control', controller)
        graph.add_link(get_name_metadata1, 'Value', get_control_float1, 'Control', controller)
        graph.add_link(get_name_metadata10, 'Value', get_control_float10, 'Control', controller)
        graph.add_link(get_name_metadata2, 'Value', get_control_float2, 'Control', controller)
        graph.add_link(get_name_metadata3, 'Value', get_control_float3, 'Control', controller)
        graph.add_link(get_name_metadata4, 'Value', get_control_float4, 'Control', controller)
        graph.add_link(get_name_metadata5, 'Value', get_control_float5, 'Control', controller)
        graph.add_link(get_name_metadata6, 'Value', get_control_float6, 'Control', controller)
        graph.add_link(get_name_metadata7, 'Value', get_control_float7, 'Control', controller)
        graph.add_link(get_name_metadata8, 'Value', get_control_float8, 'Control', controller)
        graph.add_link(get_name_metadata9, 'Value', get_control_float9, 'Control', controller)
        graph.add_link(get_parent, 'Parent', set_rotation, 'Item', controller)
        graph.add_link(get_parent1, 'Parent', get_parent6, 'Child', controller)
        graph.add_link(get_parent1, 'Parent', set_rotation1, 'Item', controller)
        graph.add_link(get_parent2, 'Parent', set_rotation2, 'Item', controller)
        graph.add_link(get_parent3, 'Parent', set_rotation3, 'Item', controller)
        graph.add_link(get_parent4, 'Parent', set_rotation4, 'Item', controller)
        graph.add_link(get_parent5, 'Parent', set_rotation5, 'Item', controller)
        graph.add_link(get_parent6, 'Parent', set_rotation6, 'Item', controller)
        graph.add_link(get_transform, 'Transform', basic_fabrik1, 'EffectorTransform', controller)
        graph.add_link(get_vector_metadata, 'Value', cross, 'A', controller)
        graph.add_link(get_vector_metadata, 'Value', vector1, 'Value', controller)
        graph.add_link(get_vector_metadata1, 'Value', cross, 'B', controller)
        graph.add_link(get_vector_metadata1, 'Value', vector, 'Value', controller)
        graph.add_link(greater, 'Result', if1, 'Condition', controller)
        graph.add_link(if1, 'Result', set_rotation4, 'Value', controller)
        graph.add_link(if2, 'Result', set_rotation5, 'Value', controller)
        graph.add_link(item_exists, 'Exists', branch, 'Condition', controller)
        graph.add_link(less, 'Result', if2, 'Condition', controller)
        graph.add_link(make_array, 'Array', basic_fabrik, 'Items', controller)
        graph.add_link(make_array1, 'Array', basic_fabrik1, 'Items', controller)
        graph.add_link(make_array2, 'Array', at, 'Array', controller)
        graph.add_link(make_array2, 'Array', at10, 'Array', controller)
        graph.add_link(make_array2, 'Array', at11, 'Array', controller)
        graph.add_link(make_array2, 'Array', at12, 'Array', controller)
        graph.add_link(make_array2, 'Array', at13, 'Array', controller)
        graph.add_link(make_array2, 'Array', at14, 'Array', controller)
        graph.add_link(make_array2, 'Array', at5, 'Array', controller)
        graph.add_link(make_array2, 'Array', at6, 'Array', controller)
        graph.add_link(make_array2, 'Array', at7, 'Array', controller)
        graph.add_link(make_array2, 'Array', at8, 'Array', controller)
        graph.add_link(make_array2, 'Array', at9, 'Array', controller)
        graph.add_link(make_array3, 'Array', at1, 'Array', controller)
        graph.add_link(make_array3, 'Array', at2, 'Array', controller)
        graph.add_link(make_array3, 'Array', at3, 'Array', controller)
        graph.add_link(make_array3, 'Array', at4, 'Array', controller)
        graph.add_link(multiply, 'Result', evaluate_curve, 'Value', controller)
        graph.add_link(multiply, 'Result', from_axis_and_angle, 'Angle', controller)
        graph.add_link(multiply, 'Result', from_axis_and_angle2, 'Angle', controller)
        graph.add_link(multiply1, 'Result', radians, 'Value', controller)
        graph.add_link(multiply10, 'Result', set_rotation2, 'Value', controller)
        graph.add_link(multiply2, 'Result', evaluate_curve2, 'Value', controller)
        graph.add_link(multiply3, 'Result', evaluate_curve1, 'Value', controller)
        graph.add_link(multiply4, 'Result', multiply10, 'A', controller)
        graph.add_link(multiply5, 'Result', multiply7, 'B', controller)
        graph.add_link(multiply6, 'Result', multiply9, 'A', controller)
        graph.add_link(multiply7, 'Result', set_rotation1, 'Value', controller)
        graph.add_link(multiply8, 'Result', from_axis_and_angle11, 'Angle', controller)
        graph.add_link(multiply9, 'Result', set_rotation, 'Value', controller)
        graph.add_link(negate, 'Result', from_axis_and_angle1, 'Axis', controller)
        graph.add_link(negate, 'Result', from_axis_and_angle2, 'Axis', controller)
        graph.add_link(negate, 'Result', from_axis_and_angle3, 'Axis', controller)
        graph.add_link(negate, 'Result', from_axis_and_angle4, 'Axis', controller)
        graph.add_link(negate, 'Result', from_axis_and_angle6, 'Axis', controller)
        graph.add_link(negate, 'Result', from_axis_and_angle7, 'Axis', controller)
        graph.add_link(negate, 'Result', from_axis_and_angle8, 'Axis', controller)
        graph.add_link(negate1, 'Result', from_axis_and_angle11, 'Axis', controller)
        graph.add_link(project_to_new_parent, 'Transform', set_transform, 'Value', controller)
        graph.add_link(project_to_new_parent1, 'Transform', basic_fabrik, 'EffectorTransform', controller)
        graph.add_link(radians, 'Result', from_axis_and_angle1, 'Angle', controller)
        graph.add_link(radians1, 'Result', from_axis_and_angle3, 'Angle', controller)
        graph.add_link(radians10, 'Result', from_axis_and_angle13, 'Angle', controller)
        graph.add_link(radians11, 'Result', from_axis_and_angle14, 'Angle', controller)
        graph.add_link(radians2, 'Result', from_axis_and_angle4, 'Angle', controller)
        graph.add_link(radians3, 'Result', from_axis_and_angle5, 'Angle', controller)
        graph.add_link(radians4, 'Result', from_axis_and_angle9, 'Angle', controller)
        graph.add_link(radians5, 'Result', from_axis_and_angle6, 'Angle', controller)
        graph.add_link(radians6, 'Result', from_axis_and_angle7, 'Angle', controller)
        graph.add_link(radians7, 'Result', from_axis_and_angle8, 'Angle', controller)
        graph.add_link(radians8, 'Result', from_axis_and_angle10, 'Angle', controller)
        graph.add_link(radians8, 'Result', greater, 'A', controller)
        graph.add_link(radians8, 'Result', less, 'A', controller)
        graph.add_link(radians8, 'Result', multiply8, 'A', controller)
        graph.add_link(radians9, 'Result', from_axis_and_angle12, 'Angle', controller)
        graph.add_link(rig_element_key, 'Value', get_name_metadata, 'Item', controller)
        graph.add_link(rig_element_key, 'Value', get_name_metadata1, 'Item', controller)
        graph.add_link(rig_element_key, 'Value', get_name_metadata10, 'Item', controller)
        graph.add_link(rig_element_key, 'Value', get_name_metadata2, 'Item', controller)
        graph.add_link(rig_element_key, 'Value', get_name_metadata3, 'Item', controller)
        graph.add_link(rig_element_key, 'Value', get_name_metadata4, 'Item', controller)
        graph.add_link(rig_element_key, 'Value', get_name_metadata5, 'Item', controller)
        graph.add_link(rig_element_key, 'Value', get_name_metadata6, 'Item', controller)
        graph.add_link(rig_element_key, 'Value', get_name_metadata7, 'Item', controller)
        graph.add_link(rig_element_key, 'Value', get_name_metadata8, 'Item', controller)
        graph.add_link(rig_element_key, 'Value', get_name_metadata9, 'Item', controller)
        graph.add_link(rig_element_key, 'Value', get_parent3, 'Child', controller)
        graph.add_link(set_rotation, 'ExecuteContext', set_rotation2, 'ExecuteContext', controller)
        graph.add_link(set_rotation1, 'ExecuteContext', set_rotation3, 'ExecuteContext', controller)
        graph.add_link(set_rotation2, 'ExecuteContext', set_rotation6, 'ExecuteContext', controller)
        graph.add_link(set_rotation3, 'ExecuteContext', set_rotation4, 'ExecuteContext', controller)
        graph.add_link(set_rotation4, 'ExecuteContext', set_rotation5, 'ExecuteContext', controller)
        graph.add_link(set_rotation6, 'ExecuteContext', set_rotation1, 'ExecuteContext', controller)
        graph.add_link(vector, 'Value', from_axis_and_angle12, 'Axis', controller)
        graph.add_link(vector, 'Value', from_axis_and_angle13, 'Axis', controller)
        graph.add_link(vector, 'Value', from_axis_and_angle14, 'Axis', controller)
        graph.add_link(vector1, 'Value', from_axis_and_angle10, 'Axis', controller)
        graph.add_link(vector1, 'Value', from_axis_and_angle9, 'Axis', controller)
        graph.add_link(vector1, 'Value', negate1, 'Value', controller)
        graph.add_link(vetala_lib_get_item, 'Element', get_item_metadata1, 'Item', controller)
        graph.add_link(vetala_lib_get_item1, 'Element', get_item_metadata, 'Item', controller)
        graph.add_link(vetala_lib_get_item1, 'Element', get_item_metadata2, 'Item', controller)
        graph.add_link(vetala_lib_get_item2, 'Element', get_item_array_metadata, 'Item', controller)
        graph.add_link(vetala_lib_get_item2, 'Element', get_item_metadata3, 'Item', controller)
        graph.add_link(vetala_lib_get_item3, 'Element', item_exists, 'Item', controller)
        graph.add_link(vetala_lib_get_item3, 'Element', project_to_new_parent, 'Child', controller)
        graph.add_link(vetala_lib_get_item3, 'Element', set_transform, 'Item', controller)
        graph.add_link(vetala_lib_get_item4, 'Element', get_item_metadata4, 'Item', controller)
        graph.add_link(vetala_lib_get_item4, 'Element', get_item_metadata5, 'Item', controller)
        graph.add_link(vetala_lib_get_item4, 'Element', get_item_metadata6, 'Item', controller)
        graph.add_link(vetala_lib_get_item4, 'Element', get_item_metadata7, 'Item', controller)
        graph.add_link(vetala_lib_get_item4, 'Element', get_vector_metadata, 'Item', controller)
        graph.add_link(vetala_lib_get_item4, 'Element', get_vector_metadata1, 'Item', controller)
        graph.add_link(vetala_lib_get_item, 'Element', make_array, 'Values.1', controller)
        graph.add_link(vetala_lib_get_item1, 'Element', make_array, 'Values.0', controller)
        graph.add_link(vetala_lib_get_item1, 'Element', make_array1, 'Values.1', controller)
        graph.add_link(vetala_lib_get_item2, 'Element', make_array1, 'Values.0', controller)

        controller.set_pin_default_value(f'{n(get_item_metadata)}.Name', 'ik', False)
        controller.set_pin_default_value(f'{n(get_item_metadata)}.Default', '(Type=Bone,Name="None")', False)
        controller.set_pin_default_value(f'{n(set_transform)}.Space', 'GlobalSpace', False)
        controller.set_pin_default_value(f'{n(set_transform)}.bInitial', 'false', False)
        controller.set_pin_default_value(f'{n(set_transform)}.Weight', '1.000000', False)
        controller.set_pin_default_value(f'{n(set_transform)}.bPropagateToChildren', 'True', False)
        controller.set_pin_default_value(f'{n(project_to_new_parent)}.bChildInitial', 'true', False)
        controller.set_pin_default_value(f'{n(project_to_new_parent)}.bOldParentInitial', 'true', False)
        controller.set_pin_default_value(f'{n(project_to_new_parent)}.bNewParentInitial', 'false', False)
        controller.set_pin_default_value(f'{n(get_transform)}.Space', 'GlobalSpace', False)
        controller.set_pin_default_value(f'{n(get_transform)}.bInitial', 'False', False)
        controller.set_pin_default_value(f'{n(vetala_lib_get_item)}.index', '2', False)
        controller.set_pin_default_value(f'{n(get_item_metadata1)}.Default', '(Type=Bone,Name="None")', False)
        controller.set_pin_default_value(f'{n(vetala_lib_get_item1)}.index', '1', False)
        controller.set_pin_default_value(f'{n(basic_fabrik)}.Precision', '0.010000', False)
        controller.set_pin_default_value(f'{n(basic_fabrik)}.Weight', '1.000000', False)
        controller.set_pin_default_value(f'{n(basic_fabrik)}.bPropagateToChildren', 'true', False)
        controller.set_pin_default_value(f'{n(basic_fabrik)}.MaxIterations', '30', False)
        controller.set_pin_default_value(f'{n(basic_fabrik)}.WorkData', '(CachedEffector=(Key=(Type=None,Name="None"),Index=65535,ContainerVersion=-1))', False)
        controller.set_pin_default_value(f'{n(basic_fabrik)}.bSetEffectorTransform', 'false', False)
        controller.set_pin_default_value(f'{n(make_array)}.Values', '((Type=None,Name="None"),(Type=None,Name="None"))', False)
        controller.set_pin_default_value(f'{n(basic_fabrik1)}.Precision', '0.010000', False)
        controller.set_pin_default_value(f'{n(basic_fabrik1)}.Weight', '1.000000', False)
        controller.set_pin_default_value(f'{n(basic_fabrik1)}.bPropagateToChildren', 'true', False)
        controller.set_pin_default_value(f'{n(basic_fabrik1)}.MaxIterations', '30', False)
        controller.set_pin_default_value(f'{n(basic_fabrik1)}.WorkData', '(CachedEffector=(Key=(Type=None,Name="None"),Index=65535,ContainerVersion=-1))', False)
        controller.set_pin_default_value(f'{n(basic_fabrik1)}.bSetEffectorTransform', 'false', False)
        controller.set_pin_default_value(f'{n(make_array1)}.Values', '((Type=None,Name="None"),(Type=None,Name="None"))', False)
        controller.set_pin_default_value(f'{n(get_item_metadata2)}.Default', '(Type=Bone,Name="None")', False)
        controller.set_pin_default_value(f'{n(project_to_new_parent1)}.bChildInitial', 'True', False)
        controller.set_pin_default_value(f'{n(project_to_new_parent1)}.bOldParentInitial', 'True', False)
        controller.set_pin_default_value(f'{n(project_to_new_parent1)}.bNewParentInitial', 'False', False)
        controller.set_pin_default_value(f'{n(vetala_lib_get_item3)}.index', '-1', False)
        controller.set_pin_default_value(f'{n(get_item_array_metadata)}.Name', 'ik', False)
        controller.set_pin_default_value(f'{n(get_item_metadata3)}.Default', '(Type=Bone,Name="None")', False)
        controller.set_pin_default_value(f'{n(make_array2)}.Values', '("roll","rollOffset","ankle","heel","ball","toe","toeRotate","yaw","toePivot","ballPivot","heelPivot")', False)
        controller.set_pin_default_value(f'{n(at)}.Index', '0', False)
        controller.set_pin_default_value(f'{n(make_array3)}.Values', '("toe","heel","yaw_out","yaw_in")', False)
        controller.set_pin_default_value(f'{n(get_item_metadata4)}.Default', '(Type=Bone,Name="None")', False)
        controller.set_pin_default_value(f'{n(vetala_lib_get_item4)}.index', '-1', False)
        controller.set_pin_default_value(f'{n(at1)}.Index', '0', False)
        controller.set_pin_default_value(f'{n(get_vector_metadata)}.Name', 'forward_axis', False)
        controller.set_pin_default_value(f'{n(get_vector_metadata)}.Default', '(X=0.000000,Y=0.000000,Z=0.000000)', False)
        controller.set_pin_default_value(f'{n(get_vector_metadata1)}.Name', 'up_axis', False)
        controller.set_pin_default_value(f'{n(get_vector_metadata1)}.Default', '(X=0.000000,Y=0.000000,Z=0.000000)', False)
        controller.set_pin_default_value(f'{n(multiply)}.B', '0.100000', False)
        controller.set_pin_default_value(f'{n(set_rotation)}.Space', 'LocalSpace', False)
        controller.set_pin_default_value(f'{n(set_rotation)}.bInitial', 'false', False)
        controller.set_pin_default_value(f'{n(set_rotation)}.Weight', '1.000000', False)
        controller.set_pin_default_value(f'{n(set_rotation)}.bPropagateToChildren', 'true', False)
        controller.set_pin_default_value(f'{n(get_item_metadata5)}.Default', '(Type=Bone,Name="None")', False)
        controller.set_pin_default_value(f'{n(at2)}.Index', '1', False)
        controller.set_pin_default_value(f'{n(get_item_metadata6)}.Default', '(Type=Bone,Name="None")', False)
        controller.set_pin_default_value(f'{n(at3)}.Index', '2', False)
        controller.set_pin_default_value(f'{n(get_item_metadata7)}.Default', '(Type=Bone,Name="None")', False)
        controller.set_pin_default_value(f'{n(at4)}.Index', '3', False)
        controller.set_pin_default_value(f'{n(evaluate_curve)}.Curve', '(EditorCurveData=(Keys=((),(Time=0.500000,Value=1.000000),(Time=1.000000))))', False)
        controller.set_pin_default_value(f'{n(evaluate_curve)}.SourceMinimum', '0.000000', False)
        controller.set_pin_default_value(f'{n(evaluate_curve)}.SourceMaximum', '1.000000', False)
        controller.set_pin_default_value(f'{n(evaluate_curve)}.TargetMinimum', '0.000000', False)
        controller.set_pin_default_value(f'{n(evaluate_curve)}.TargetMaximum', '1.000000', False)
        controller.set_pin_default_value(f'{n(set_rotation1)}.Space', 'LocalSpace', False)
        controller.set_pin_default_value(f'{n(set_rotation1)}.bInitial', 'false', False)
        controller.set_pin_default_value(f'{n(set_rotation1)}.Weight', '1.000000', False)
        controller.set_pin_default_value(f'{n(set_rotation1)}.bPropagateToChildren', 'true', False)
        controller.set_pin_default_value(f'{n(evaluate_curve1)}.Curve', '(EditorCurveData=(Keys=((),(Time=0.250000),(InterpMode=RCIM_Constant,Time=1.000000,Value=1.000000))))', False)
        controller.set_pin_default_value(f'{n(evaluate_curve1)}.SourceMinimum', '0.000000', False)
        controller.set_pin_default_value(f'{n(evaluate_curve1)}.SourceMaximum', '2.000000', False)
        controller.set_pin_default_value(f'{n(evaluate_curve1)}.TargetMinimum', '0.000000', False)
        controller.set_pin_default_value(f'{n(evaluate_curve1)}.TargetMaximum', '90.000000', False)
        controller.set_pin_default_value(f'{n(evaluate_curve2)}.Curve', '(EditorCurveData=(Keys=((),(InterpMode=RCIM_Constant,Time=1.000000,Value=1.000000))))', False)
        controller.set_pin_default_value(f'{n(evaluate_curve2)}.SourceMinimum', '0.000000', False)
        controller.set_pin_default_value(f'{n(evaluate_curve2)}.SourceMaximum', '2.000000', False)
        controller.set_pin_default_value(f'{n(evaluate_curve2)}.TargetMinimum', '0.000000', False)
        controller.set_pin_default_value(f'{n(evaluate_curve2)}.TargetMaximum', '-90.000000', False)
        controller.set_pin_default_value(f'{n(multiply2)}.B', '-0.100000', False)
        controller.set_pin_default_value(f'{n(set_rotation2)}.Space', 'LocalSpace', False)
        controller.set_pin_default_value(f'{n(set_rotation2)}.bInitial', 'false', False)
        controller.set_pin_default_value(f'{n(set_rotation2)}.Weight', '1.000000', False)
        controller.set_pin_default_value(f'{n(set_rotation2)}.bPropagateToChildren', 'true', False)
        controller.set_pin_default_value(f'{n(multiply3)}.B', '0.100000', False)
        controller.set_pin_default_value(f'{n(at5)}.Index', '3', False)
        controller.set_pin_default_value(f'{n(at6)}.Index', '4', False)
        controller.set_pin_default_value(f'{n(at7)}.Index', '1', False)
        controller.set_pin_default_value(f'{n(at8)}.Index', '5', False)
        controller.set_pin_default_value(f'{n(at9)}.Index', '6', False)
        controller.set_pin_default_value(f'{n(set_rotation3)}.Space', 'LocalSpace', False)
        controller.set_pin_default_value(f'{n(set_rotation3)}.bInitial', 'false', False)
        controller.set_pin_default_value(f'{n(set_rotation3)}.Weight', '1.000000', False)
        controller.set_pin_default_value(f'{n(set_rotation3)}.bPropagateToChildren', 'true', False)
        controller.set_pin_default_value(f'{n(at10)}.Index', '2', False)
        controller.set_pin_default_value(f'{n(at11)}.Index', '7', False)
        controller.set_pin_default_value(f'{n(greater)}.B', '0.000000', False)
        controller.set_pin_default_value(f'{n(if1)}.False', '(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000)', False)
        controller.set_pin_default_value(f'{n(if2)}.False', '(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000)', False)
        controller.set_pin_default_value(f'{n(less)}.B', '0.000000', False)
        controller.set_pin_default_value(f'{n(set_rotation4)}.Space', 'LocalSpace', False)
        controller.set_pin_default_value(f'{n(set_rotation4)}.bInitial', 'false', False)
        controller.set_pin_default_value(f'{n(set_rotation4)}.Weight', '1.000000', False)
        controller.set_pin_default_value(f'{n(set_rotation4)}.bPropagateToChildren', 'true', False)
        controller.set_pin_default_value(f'{n(set_rotation5)}.Space', 'LocalSpace', False)
        controller.set_pin_default_value(f'{n(set_rotation5)}.bInitial', 'false', False)
        controller.set_pin_default_value(f'{n(set_rotation5)}.Weight', '1.000000', False)
        controller.set_pin_default_value(f'{n(set_rotation5)}.bPropagateToChildren', 'true', False)
        controller.set_pin_default_value(f'{n(multiply8)}.B', '-1.000000', False)
        controller.set_pin_default_value(f'{n(at12)}.Index', '8', False)
        controller.set_pin_default_value(f'{n(at13)}.Index', '9', False)
        controller.set_pin_default_value(f'{n(at14)}.Index', '10', False)
        controller.set_pin_default_value(f'{n(set_rotation6)}.Space', 'LocalSpace', False)
        controller.set_pin_default_value(f'{n(set_rotation6)}.bInitial', 'false', False)
        controller.set_pin_default_value(f'{n(set_rotation6)}.Weight', '1.000000', False)
        controller.set_pin_default_value(f'{n(set_rotation6)}.bPropagateToChildren', 'true', False)

        current_locals = locals()
        nodes = unreal_lib.graph.filter_nodes(current_locals.values())
        node = unreal_lib.graph.comment_nodes(nodes, controller, 'Forward Solve')
        nodes.append(node)
        unreal_lib.graph.move_nodes(700, 400, nodes, controller)

    def _build_function_backward_graph(self):
        return


class UnrealIkQuadrupedRig(UnrealUtilRig):
    pass


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

        graph.add_link(self.mode, 'Cases.0', joint_branch, 'ExecuteContext', controller)

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
        switch = controller.add_template_node('DISPATCH_RigVMDispatch_SwitchInt32(in Index)', unreal.Vector2D(225.0, -160.0), 'Switch')
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
        switch = controller.add_template_node('DISPATCH_RigVMDispatch_SwitchInt32(in Index)', unreal.Vector2D(225.0, -160.0), 'Switch')
        for_each = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayIterator(in Array,out Element,out Index,out Count,out Ratio)', unreal.Vector2D(1072.0, 944.0), 'For Each')
        vetala_lib_string_to_index = controller.add_function_reference_node(library.find_function('vetalaLib_StringToIndex'), unreal.Vector2D(160.0, 400.0), 'vetalaLib_StringToIndex')
        vetala_lib_index_to_items = controller.add_function_reference_node(library.find_function('vetalaLib_IndexToItems'), unreal.Vector2D(384.0, 416.0), 'vetalaLib_IndexToItems')
        vetala_lib_string_to_index1 = controller.add_function_reference_node(library.find_function('vetalaLib_StringToIndex'), unreal.Vector2D(240.0, 1008.0), 'vetalaLib_StringToIndex')
        vetala_lib_index_to_items1 = controller.add_function_reference_node(library.find_function('vetalaLib_IndexToItems'), unreal.Vector2D(496.0, 1024.0), 'vetalaLib_IndexToItems')
        for_each1 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayIterator(in Array,out Element,out Index,out Count,out Ratio)', unreal.Vector2D(736.0, 688.0), 'For Each')
        position_constraint = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_PositionConstraintLocalSpaceOffset', 'Execute', unreal.Vector2D(2096.0, 912.0), 'Position Constraint')
        get_local_parents = controller.add_variable_node_from_object_path('local_parents', 'TArray<FConstraintParent>', '/Script/ControlRig.ConstraintParent', True, '()', unreal.Vector2D(1456.0, 480.0), 'Get local_parents')
        add = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayAdd(io Array,in Element,out Index)', unreal.Vector2D(1632.0, 640.0), 'Add')
        get_local_parents1 = controller.add_variable_node_from_object_path('local_parents', 'TArray<FConstraintParent>', '/Script/ControlRig.ConstraintParent', True, '()', unreal.Vector2D(1392.0, 1360.0), 'Get local_parents')
        parent_constraint = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_ParentConstraint', 'Execute', unreal.Vector2D(2032.0, 1408.0), 'Parent Constraint')
        branch = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_ControlFlowBranch', 'Execute', unreal.Vector2D(1648.0, 976.0), 'Branch')
        get_translate = controller.add_variable_node('translate', 'bool', None, True, '', unreal.Vector2D(1504.0, 1632.0), 'Get translate')
        get_rotate = controller.add_variable_node('rotate', 'bool', None, True, '', unreal.Vector2D(1488.0, 1760.0), 'Get rotate')
        get_scale = controller.add_variable_node('scale', 'bool', None, True, '', unreal.Vector2D(1488.0, 1872.0), 'Get scale')
        rotation_constraint = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_RotationConstraintLocalSpaceOffset', 'Execute', unreal.Vector2D(2496.0, 1008.0), 'Rotation Constraint')
        scale_constraint = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_ScaleConstraintLocalSpaceOffset', 'Execute', unreal.Vector2D(2944.0, 1072.0), 'Scale Constraint')
        vetala_lib_string_to_index2 = controller.add_function_reference_node(library.find_function('vetalaLib_StringToIndex'), unreal.Vector2D(700.0, -351.0), 'vetalaLib_StringToIndex')
        vetala_lib_index_to_items2 = controller.add_function_reference_node(library.find_function('vetalaLib_IndexToItems'), unreal.Vector2D(928.0, -352.0), 'vetalaLib_IndexToItems')
        for_each2 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayIterator(in Array,out Element,out Index,out Count,out Ratio)', unreal.Vector2D(1216.0, -368.0), 'For Each')
        get_parent = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyGetParent', 'Execute', unreal.Vector2D(1504.0, -576.0), 'Get Parent')
        spawn_transform_control = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyAddControlTransform', 'Execute', unreal.Vector2D(1968.0, -976.0), 'Spawn Transform Control')
        get_transform = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetTransform', 'Execute', unreal.Vector2D(1520.0, -288.0), 'Get Transform')
        set_item_metadata = controller.add_template_node('DISPATCH_RigDispatch_SetMetadata(in Item,in Name,in NameSpace,in Value,out Success)', unreal.Vector2D(3008.0, -688.0), 'Set Item Metadata')
        get_item_metadata = controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in NameSpace,in Default,out Value,out Found)', unreal.Vector2D(1056.0, 1280.0), 'Get Item Metadata')
        from_string = controller.add_template_node('DISPATCH_RigDispatch_FromString(in String,out Result)', unreal.Vector2D(768.0, 1360.0), 'From String')
        concat = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_NameConcat', 'Execute', unreal.Vector2D(1408.0, -816.0), 'Concat')
        set_transform = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_SetTransform', 'Execute', unreal.Vector2D(3392.0, 1408.0), 'Set Transform')
        get_transform1 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetTransform', 'Execute', unreal.Vector2D(2848.0, 1632.0), 'Get Transform')

        controller.set_array_pin_size(f'{n(switch)}.Cases', 4)

        graph.add_link(entry, 'ExecuteContext', switch, 'ExecuteContext', controller)
        graph.add_link(switch, 'Completed', return1, 'ExecuteContext', controller)
        graph.add_link(switch, 'Cases.0', vetala_lib_string_to_index2, 'ExecuteContext', controller)
        graph.add_link(switch, 'Cases.1', vetala_lib_string_to_index, 'ExecuteContext', controller)
        graph.add_link(for_each1, 'Completed', for_each, 'ExecuteContext', controller)
        graph.add_link(for_each, 'ExecuteContext', branch, 'ExecuteContext', controller)
        graph.add_link(for_each, 'Completed', set_transform, 'ExecuteContext', controller)
        graph.add_link(vetala_lib_string_to_index, 'ExecuteContext', vetala_lib_index_to_items, 'ExecuteContext', controller)
        graph.add_link(vetala_lib_index_to_items, 'ExecuteContext', vetala_lib_string_to_index1, 'ExecuteContext', controller)
        graph.add_link(vetala_lib_string_to_index1, 'ExecuteContext', vetala_lib_index_to_items1, 'ExecuteContext', controller)
        graph.add_link(vetala_lib_index_to_items1, 'ExecuteContext', for_each1, 'ExecuteContext', controller)
        graph.add_link(for_each1, 'ExecuteContext', add, 'ExecuteContext', controller)
        graph.add_link(branch, 'True', position_constraint, 'ExecuteContext', controller)
        graph.add_link(position_constraint, 'ExecuteContext', rotation_constraint, 'ExecuteContext', controller)
        graph.add_link(branch, 'False', parent_constraint, 'ExecuteContext', controller)
        graph.add_link(rotation_constraint, 'ExecuteContext', scale_constraint, 'ExecuteContext', controller)
        graph.add_link(vetala_lib_string_to_index2, 'ExecuteContext', vetala_lib_index_to_items2, 'ExecuteContext', controller)
        graph.add_link(vetala_lib_index_to_items2, 'ExecuteContext', for_each2, 'ExecuteContext', controller)
        graph.add_link(for_each2, 'ExecuteContext', spawn_transform_control, 'ExecuteContext', controller)
        graph.add_link(spawn_transform_control, 'ExecuteContext', set_item_metadata, 'ExecuteContext', controller)
        graph.add_link(entry, 'mode', switch, 'Index', controller)
        graph.add_link(entry, 'parent', vetala_lib_index_to_items, 'Items', controller)
        graph.add_link(entry, 'parent_index', vetala_lib_string_to_index, 'string', controller)
        graph.add_link(entry, 'children', vetala_lib_index_to_items1, 'Items', controller)
        graph.add_link(entry, 'children', vetala_lib_index_to_items2, 'Items', controller)
        graph.add_link(entry, 'child_indices', vetala_lib_string_to_index1, 'string', controller)
        graph.add_link(entry, 'child_indices', vetala_lib_string_to_index2, 'string', controller)
        graph.add_link(entry, 'use_child_pivot', branch, 'Condition', controller)
        graph.add_link(vetala_lib_index_to_items1, 'Result', for_each, 'Array', controller)
        graph.add_link(for_each, 'Element', get_item_metadata, 'Item', controller)
        graph.add_link(for_each, 'Element', set_transform, 'Item', controller)
        graph.add_link(vetala_lib_string_to_index, 'index', vetala_lib_index_to_items, 'Index', controller)
        graph.add_link(vetala_lib_index_to_items, 'Result', for_each1, 'Array', controller)
        graph.add_link(vetala_lib_string_to_index1, 'index', vetala_lib_index_to_items1, 'Index', controller)
        graph.add_link(get_item_metadata, 'Value', position_constraint, 'Child', controller)
        graph.add_link(get_local_parents1, 'Value', position_constraint, 'Parents', controller)
        graph.add_link(get_local_parents, 'Value', add, 'Array', controller)
        graph.add_link(get_local_parents, 'Value', rotation_constraint, 'Parents', controller)
        graph.add_link(get_local_parents1, 'Value', parent_constraint, 'Parents', controller)
        graph.add_link(get_local_parents1, 'Value', scale_constraint, 'Parents', controller)
        graph.add_link(get_item_metadata, 'Value', parent_constraint, 'Child', controller)
        graph.add_link(get_item_metadata, 'Value', rotation_constraint, 'Child', controller)
        graph.add_link(get_item_metadata, 'Value', scale_constraint, 'Child', controller)
        graph.add_link(vetala_lib_string_to_index2, 'index', vetala_lib_index_to_items2, 'Index', controller)
        graph.add_link(vetala_lib_index_to_items2, 'Result', for_each2, 'Array', controller)
        graph.add_link(for_each2, 'Element', get_parent, 'Child', controller)
        graph.add_link(for_each2, 'Element', get_transform, 'Item', controller)
        graph.add_link(for_each2, 'Element', set_item_metadata, 'Item', controller)
        graph.add_link(for_each2, 'Element.Name', concat, 'B', controller)
        graph.add_link(get_parent, 'Parent', spawn_transform_control, 'Parent', controller)
        graph.add_link(concat, 'Result', spawn_transform_control, 'Name', controller)
        graph.add_link(spawn_transform_control, 'Item', set_item_metadata, 'Value', controller)
        graph.add_link(get_transform, 'Transform', spawn_transform_control, 'InitialValue', controller)
        graph.add_link(from_string, 'Result', get_item_metadata, 'Name', controller)
        graph.add_link(get_item_metadata, 'Value', get_transform1, 'Item', controller)
        graph.add_link(get_transform1, 'Transform', set_transform, 'Value', controller)
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
        graph.set_pin(spawn_transform_control, 'OffsetSpace', 'LocalSpace', controller)
        graph.set_pin(spawn_transform_control, 'Settings', '(InitialSpace=GlobalSpace,bUsePreferredRotationOrder=False,PreferredRotationOrder=YZX,Limits=(LimitTranslationX=(bMinimum=False,bMaximum=False),LimitTranslationY=(bMinimum=False,bMaximum=False),LimitTranslationZ=(bMinimum=False,bMaximum=False),LimitPitch=(bMinimum=False,bMaximum=False),LimitYaw=(bMinimum=False,bMaximum=False),LimitRoll=(bMinimum=False,bMaximum=False),LimitScaleX=(bMinimum=False,bMaximum=False),LimitScaleY=(bMinimum=False,bMaximum=False),LimitScaleZ=(bMinimum=False,bMaximum=False),MinValue=(Location=(X=-100.000000,Y=-100.000000,Z=-100.000000),Rotation=(Pitch=-180.000000,Yaw=-180.000000,Roll=-180.000000),Scale=(X=0.000000,Y=0.000000,Z=0.000000)),MaxValue=(Location=(X=100.000000,Y=100.000000,Z=100.000000),Rotation=(Pitch=180.000000,Yaw=180.000000,Roll=180.000000),Scale=(X=10.000000,Y=10.000000,Z=10.000000)),bDrawLimits=True),Shape=(bVisible=True,Name="Box_Thin",Color=(R=1.000000,G=0.000000,B=0.000000,A=1.000000),Transform=(Rotation=(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=1.000000,Y=1.000000,Z=1.000000))),Proxy=(bIsProxy=true,ShapeVisibility=BasedOnSelection),FilteredChannels=(),DisplayName="None")', controller)
        graph.set_pin(get_transform, 'Space', 'GlobalSpace', controller)
        graph.set_pin(get_transform, 'bInitial', 'False', controller)
        graph.set_pin(set_item_metadata, 'Name', 'anchor', controller)
        graph.set_pin(set_item_metadata, 'NameSpace', 'Self', controller)
        graph.set_pin(get_item_metadata, 'NameSpace', 'Self', controller)
        graph.set_pin(get_item_metadata, 'Default', '(Type=Bone,Name="None")', controller)
        graph.set_pin(from_string, 'String', 'anchor', controller)
        graph.set_pin(concat, 'A', 'anchor_', controller)
        graph.set_pin(set_transform, 'Space', 'GlobalSpace', controller)
        graph.set_pin(set_transform, 'bInitial', 'true', controller)
        graph.set_pin(set_transform, 'Weight', '1.000000', controller)
        graph.set_pin(set_transform, 'bPropagateToChildren', 'True', controller)
        graph.set_pin(get_transform1, 'Space', 'GlobalSpace', controller)
        graph.set_pin(get_transform1, 'bInitial', 'False', controller)

