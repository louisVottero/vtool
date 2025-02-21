# Copyright (C) 2024 Louis Vottero louis.vot@gmail.com    All rights reserved.

from vtool import util, unreal_lib
from vtool import util_math
from vtool import util_file

if util.in_unreal:
    import unreal

current_control_rig = None
undo_open = False

import re
from collections import defaultdict


def n(unreal_node):
    if type(unreal_node) == str:
        return unreal_node
    else:
        return unreal_node.get_node_path()


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
                # unreal_object.sub_objects.append(UnrealTextDataObject())

                object_history.append(unreal_object)

                depth += 1

            elif line.lstrip() == 'End Object':

                if depth > 0:

                    object_history[(depth - 1)].append(line)

                    if depth == 1:
                        self.objects.append(object_history[0])
                        object_history = []

                    elif len(object_history) > 1:
                        object_history[(depth - 2)].sub_objects.append(object_history[depth - 1])
                        object_history.pop(-1)

                    depth -= 1

            else:
                object_history[(depth - 1)].append(line)

        # for text_data in self.objects:
        #    text_data.run()

        # lines = self._deep_iterate(self.objects)
        # for line in lines:
        #    print(line)

    def load_file(self, filepath):

        self.filepath = filepath

        self.lines = self._get_text_lines(filepath)
        self._parse_lines(self.lines)

        return self.objects


def unreal_control_rig_to_python():

    control_rig = get_current_control_rig()

    models = control_rig.get_all_models()

    model_dict = {}

    for model in models:

        model_name = model.get_name()

        controller = control_rig.get_controller_by_name(model_name)
        nodes = model.get_nodes()

        node_names = [node.get_node_path() for node in nodes]

        print('Model:', model_name, 'with nodes:', len(nodes))

        model_dict[model] = []

        node_text = controller.export_nodes_to_text(node_names)
        objects = parse_export_text(node_text)

        for thing in objects:
            print('\t\tNode: %s' % thing['name'])


def parse_to_python(parse_object):
    pass
    # import json
    # print(json.dumps(objects, indent=4))


def parse_export_text(export_text):
    objects = []
    stack = []

    begin_pattern = re.compile(r'^(?P<indent>\s*)Begin Object(?: Class=(?P<class>\S+))? Name="(?P<name>\S+)" ExportPath="(?P<path>[^"]+)"')
    end_pattern = re.compile(r'^(?P<indent>\s*)End Object')
    property_pattern = re.compile(r'^(?P<indent>\s*)(?P<key>[\w]+)=(?P<value>.+)')

    for line in export_text.splitlines():
        begin_match = begin_pattern.match(line)
        end_match = end_pattern.match(line)
        property_match = property_pattern.match(line)
        if begin_match:

            indent = len(begin_match.group("indent"))
            new_obj = begin_match.groupdict()
            new_obj.pop("indent")  # Remove indent key
            new_obj["properties"] = {}
            new_obj["children"] = []

            while stack and stack[-1]["indent"] >= indent:
                stack.pop()

            new_obj["indent"] = indent
            if stack:
                stack[-1]["children"].append(new_obj)
            else:
                objects.append(new_obj)
            stack.append(new_obj)

        elif end_match:

            indent = len(end_match.group("indent"))
            while stack and stack[-1]["indent"] >= indent:
                stack.pop()

        elif property_match:
            key, value = property_match.group("key"), property_match.group("value").strip('"')
            indent = len(property_match.group("indent"))
            if stack and stack[-1]["indent"] < indent:
                stack[-1]["properties"][key] = value

    # import json
    # print(json.dumps(objects, indent=4))
    return objects


def set_current_control_rig(unreal_control_rig_instance):
    global current_control_rig
    current_control_rig = unreal_control_rig_instance


def get_current_control_rig():

    found = None

    control_rigs = unreal.ControlRigBlueprint.get_currently_open_rig_blueprints()

    if control_rigs:
        found = control_rigs[0]

    if not found:
        found = current_control_rig

    return found


def open_control_rig(control_rig_blueprint_inst=None):

    if not control_rig_blueprint_inst:
        control_rig_blueprint_inst = get_current_control_rig()

    if control_rig_blueprint_inst:
        pass


def get_graph_model_controller(model, main_graph=None):

    if not main_graph:
        main_graph = get_current_control_rig()

    model_name = model.get_node_path()
    model_name = model_name.replace(':', '')
    model_control = main_graph.get_controller_by_name(model_name)

    return model_control


def get_last_execute_node(graph):

    found = None
    for node in graph.get_nodes():
        execute_context = node.find_pin('ExecuteContext')
        if not execute_context:
            continue
        sources = execute_context.get_linked_source_pins()
        targets = execute_context.get_linked_target_pins()

        if sources and not targets:
            found = node

    return found


def reset_current_control_rig():
    pass
    # this can cause some bad evals in Unreal
    """
    
    control_rig = get_current_control_rig()
    if not control_rig:
        return
    models = control_rig.get_all_models()
    controller = control_rig.get_controller_by_name('RigVMFunctionLibrary')
    non_remove = ('RigVMFunctionLibrary', 'RigVMModel')

    for model in models:
        model_name = model.get_graph_name()
        if model_name in non_remove:
            continue
        if model_name.startswith('RigVMModel'):
            try:
                control_rig.remove_model(model_name)
            except:
                util.warning('Could not remove: model %s' % model_name)
        else:
            controller.remove_function_from_library(model_name)
    """


def create_control_rig_from_skeletal_mesh(skeletal_mesh_object, name=None):
    factory = unreal.ControlRigBlueprintFactory
    rig = factory.create_control_rig_from_skeletal_mesh_or_skeleton(selected_object=skeletal_mesh_object)

    set_current_control_rig(rig)

    # avoiding this to minimalize errors
    # add_construct_graph()
    # add_forward_solve()
    # add_backward_graph()

    # this doesnt seem to working
    if name:
        orig_path = rig.get_path_name()
        new_path = util_file.get_dirname(orig_path)
        new_path = util_file.join_path(new_path, name)

        editor = unreal.EditorAssetLibrary()
        result = editor.rename(orig_path, new_path)

        if result:
            asset_inst = unreal.load_asset(new_path)
            rig = asset_inst.get_asset()

    return rig


def add_forward_solve():
    current_control_rig = get_current_control_rig()
    if not current_control_rig:
        return
    current_model = None

    for model in current_control_rig.get_all_models():

        model_name = model.get_graph_name()
        if model_name == 'RigVMModel':
            current_model = model

    control = current_control_rig.get_controller_by_name(current_model.get_graph_name())

    nodes = control.get_graph().get_nodes()

    found = False

    for node in nodes:

        if node.get_node_path() == 'BeginExecution':
            found = True
            break
        if node.get_node_path() == 'RigUnit_BeginExecution':
            found = True
            break

    if not found:
        node = control.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_BeginExecution', 'Execute', unreal.Vector2D(0, 0), 'BeginExecution')

    return current_model


def add_construct_graph():
    current_control_rig = get_current_control_rig()
    if not current_control_rig:
        return
    current_model = None

    if not current_control_rig:
        return
    for model in current_control_rig.get_all_models():
        model_name = model.get_graph_name()

        if model_name.find('Construction Event Graph') > -1:
            current_model = model

    if not current_model:
        construct_model = current_control_rig.add_model('Construction Event Graph')
        current_model = construct_model

        model_control = current_control_rig.get_controller_by_name(current_model.get_graph_name())

        model_control.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_PrepareForExecution', 'Execute', unreal.Vector2D(0, 0), 'PrepareForExecution')

    return current_model


def add_backward_graph():
    current_control_rig = get_current_control_rig()
    if not current_control_rig:
        return
    current_model = None
    for model in current_control_rig.get_all_models():
        model_name = model.get_graph_name()
        if model_name.find('Backward Solve Graph') > -1:
            current_model = model

    if not current_model:
        construct_model = current_control_rig.add_model('Backward Solve Graph')
        current_model = construct_model

        model_control = current_control_rig.get_controller_by_name(current_model.get_graph_name())

        model_control.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_InverseExecution', 'Execute', unreal.Vector2D(0, 0), 'InverseExecution')

    return current_model


def get_construct_controller(graph):
    models = graph.get_all_models()

    for model in models:
        if n(model).find('Construction Event Graph') > -1:
            return get_graph_model_controller(model, graph)

    model = add_construct_graph()
    return get_graph_model_controller(model, graph)


def get_forward_controller(graph):
    return graph.get_controller_by_name('RigVMModel')


def get_backward_controller(graph):
    models = graph.get_all_models()

    for model in models:
        if n(model).find('Backward Solve Graph') > -1:
            return get_graph_model_controller(model, graph)

    model = add_backward_graph()
    return get_graph_model_controller(model, graph)


def get_controllers(graph=None):
    if not graph:
        graph = get_current_control_rig()

    if graph:

        construct = get_construct_controller(graph)
        forward = get_forward_controller(graph)
        backward = get_backward_controller(graph)

        return [construct, forward, backward]

    else:
        return []


def reset_undo():
    global undo_open
    undo_open = False


def open_undo(title=''):
    global undo_open
    if undo_open:
        return
    util.show('Open Undo: %s' % title)
    graph = get_current_control_rig()

    if not graph:
        return

    controllers = get_controllers(graph)

    for controller in controllers:
        controller.open_undo_bracket(title)

    undo_open = title


def close_undo(title):
    global undo_open
    if not undo_open:
        return

    if undo_open != title:
        return

    util.show('Close Undo: %s' % undo_open)
    graph = get_current_control_rig()

    if not graph:
        return

    controllers = get_controllers(graph)

    for controller in controllers:
        controller.close_undo_bracket()

    if undo_open:
        undo_open = False


def is_node(node):
    if hasattr(node, 'get_node_index'):
        return True

    return False


def filter_nodes(list_of_instances):
    return [instance for instance in list_of_instances if is_node(instance)]


def get_node_bounding_box(list_of_node_instances):
    min_x = None
    max_x = None

    min_y = None
    max_y = None

    for node in list_of_node_instances:
        if type(node) == unreal.RigVMCollapseNode:
            continue

        position = node.get_position()
        size = node.get_size()

        if min_x == None or position.x < min_x:
            min_x = position.x
        if min_y == None or position.y < min_y:
            min_y = position.y

        position_x = position.x + size.x
        position_y = position.y + size.y

        if max_x == None or position_x > max_x:
            max_x = position_x
        if max_y == None or position_y > max_y:
            max_y = position_y

    min_vector = [min_x, min_y]
    max_vector = [max_x, max_y]
    return min_vector, max_vector


def comment_nodes(list_of_node_instances, controller, name='Graph'):

    color = [1.0, 1.0, 1.0, 1.0]

    if name == 'Construction':
        color = [0.25, 0.0, 0.0, 1.0]
    if name == 'Forward Solve':
        color = [0.0, 0.0, 0.25, 1.0]
    if name == 'Backward Solve':
        color = [0.25, 0.25, 0.0, 1.0]

    min_vector, max_vector = get_node_bounding_box(list_of_node_instances)
    min_vector[0] -= 100
    min_vector[1] -= 100

    size_x = max_vector[0] - min_vector[0] + 300
    size_y = max_vector[1] - min_vector[1] + 300

    node = controller.add_comment_node(name, unreal.Vector2D(min_vector[0], min_vector[1]), unreal.Vector2D(size_x, size_y), unreal.LinearColor(*color), 'EdGraphNode_Comment')

    return node


def move_nodes(position_x, position_y, list_of_node_instances, controller):

    min_vector, max_vector = get_node_bounding_box(list_of_node_instances)

    for node in list_of_node_instances:
        if type(node) == unreal.RigVMCollapseNode:
            continue
        position = node.get_position()

        delta_x = position.x - min_vector[0]
        delta_y = position.y - min_vector[1]

        new_position = [position_x + delta_x, position_y + delta_y]

        controller.set_node_position(node, unreal.Vector2D(*new_position))


def add_link(source_node, source_attribute, target_node, target_attribute, controller):

    if not source_node:
        return

    if not target_node:
        return

    source = f'{n(source_node)}.{source_attribute}'
    target = f'{n(target_node)}.{target_attribute}'

    try:
        controller.add_link(source, target)
    except:
        try:
            controller.break_all_links(source, True)
            controller.break_all_links(source, False)
            controller.add_link(source, target)
        except:
            util.warning(f'Could not connect {source} and {target} using {controller.get_name()}')
            raise


def break_link(source_node, source_attribute, target_node, target_attribute, controller):

    controller.break_link(f'{n(source_node)}.{source_attribute}', f'{n(target_node)}.{target_attribute}')


def break_all_links_to_node(node, controller):

    for pin in node.get_all_pins_recursively():
        pin_path = pin.get_pin_path()

        controller.break_all_links(f'{pin_path}', True)
        controller.break_all_links(f'{pin_path}', False)


def add_animation_channel(controller, name, x=0, y=0):

    version = util.get_unreal_version()
    if version[0] <= 5 and version[1] <= 3:
        channel = controller.add_template_node('SpawnAnimationChannel::Execute(in InitialValue,in MinimumValue,in MaximumValue,in Parent,in Name,out Item)', unreal.Vector2D(x, y), 'SpawnAnimationChannel')

    if version[0] <= 5 and version[1] >= 4:
        channel = controller.add_template_node('SpawnAnimationChannel::Execute(in InitialValue,in MinimumValue,in MaximumValue,in LimitsEnabled,in Parent,in Name,out Item)', unreal.Vector2D(x, y), 'SpawnAnimationChannel')

    controller.set_pin_default_value(f'{n(channel)}.Name', name, False)

    return channel


def compile_control_rig():
    unreal.BlueprintEditorLibrary.compile_blueprint(get_current_control_rig())


def get_controller(graph):
    control_rig = get_current_control_rig()
    if control_rig:
        controller = control_rig.get_controller(graph)

        return controller


def clean_controller(controller, only_ramen=True):
    nodes = controller.get_graph().get_nodes()
    for node in nodes:
        delete = True
        if only_ramen:
            if not node.find_pin('uuid'):
                delete = False

        if delete:
            controller.remove_node(node)


def clear_selection(graph=None):

    controllers = get_controllers(graph)

    for controller in controllers:
        controller.clear_node_selection()


def clean_graph(graph=None, only_ramen=True):

    if graph:
        controllers = [get_controller(graph)]
    if not graph:
        controllers = get_controllers()

    for controller in controllers:
        nodes = controller.get_graph().get_nodes()
        for node in nodes:
            delete = True
            if only_ramen:
                if not node.find_pin('uuid'):
                    delete = False

            if delete:
                controller.remove_node(node)
