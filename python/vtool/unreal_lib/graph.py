# Copyright (C) 2024 Louis Vottero louis.vot@gmail.com    All rights reserved.

from vtool import util
from vtool import util_math

if util.in_unreal:
    import unreal

current_control_rig = None


def n(unreal_node):
    if type(unreal_node) == str:
        return unreal_node
    else:
        return unreal_node.get_node_path()


class UnrealTextDataObject(list):

    def __init__(self):
        self.sub_objects = []

    def text(self, include_sub_text=False):

        text_lines = self

        if include_sub_text:
            sub_text = self.sub_text()
            text_lines.insert(1, sub_text)

        return '\n'.join(text_lines)

    def sub_text(self):
        sub_texts = []

        sub_text = ''

        for sub_object in self.sub_objects:

            sub_text_current = sub_object.text()
            sub_texts.append(sub_text_current)

        if sub_texts:
            sub_text = '\n'.join(sub_texts)

        return sub_text

    def _sub_run(self, controller):
        if not self.sub_objects:
            return
        for sub_object in self.sub_objects:
            sub_object.run(controller)

    def get_object_header_data(self):

        header = self[0]
        split_header = header.split()

        header_dict = {}

        for entry in split_header:
            if entry.find('=') == -1:
                continue

            split_entry = entry.split('=')

            value = split_entry[1]
            value = value.strip('"')

            header_dict[split_entry[0]] = value

        return header_dict

    def run(self, controller=None):

        header = self.get_object_header_data()
        util.show('Import: %s' % header['Name'])

        skip = False

        if not controller:
            current_control_rig = get_current_control_rig()
            controller = current_control_rig.get_controller()

        if not controller:
            return
        """
        if 'Class' in header:
            header_class = header['Class']
            
            
            current_control_rig = None
            
            if not controller:
                current_control_rig = get_current_control_rig()
                controller = current_control_rig.get_controller()
            
            header_checks = ['RigVMUnitNode','RigVMCollapseNode', 'RigVMFunctionEntryNode']
            
            for header_check in header_checks: 
                if header_class.find(header_check) > -1:
                    
                    if not current_control_rig:
                        current_control_rig = get_current_control_rig()
                    
                    
                    models = current_control_rig.get_all_models()
                    for model in models:
                        print('model', model.get_graph_name(), header['Name'])
                        if model.get_graph_name() == header['Name']:
                            print('found match!', header['Name'])
                            skip = True
        
        else:
        """
        """
        name = header['Name']
        node = controller.get_graph().find_node(name)
        if node:
            skip = True
        
        if skip:
            self._sub_run(controller)
            
            return
        """
        # self._sub_run(controller)

        text = self.text(include_sub_text=False)

        result = None

        try:
            result = controller.import_nodes_from_text(text)
        except:
            util.warning('Failed ruN')

        self._sub_run(controller)


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


def get_current_control_rig():

    control_rig_controller = current_control_rig

    if control_rig_controller:
        control_rig_controller.set_auto_vm_recompile(True)
        return control_rig_controller
    else:
        control_rigs = unreal.ControlRigBlueprint.get_currently_open_rig_blueprints()
        if not control_rigs:
            return

        return control_rigs[0]


def get_graph_model_controller(model, main_graph=None):

    if not main_graph:
        main_graph = current_control_rig

    model_name = model.get_node_path()
    model_name = model_name.replace(':', '')
    model_control = main_graph.get_controller_by_name(model_name)

    return model_control


def get_last_execute_node(graph):

    found = None
    for node in graph.get_nodes():
        execute_context = node.find_pin('ExecuteContext')
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


def create_control_rig_from_skeletal_mesh(skeletal_mesh_object):
    factory = unreal.ControlRigBlueprintFactory
    rig = factory.create_control_rig_from_skeletal_mesh_or_skeleton(selected_object=skeletal_mesh_object)

    global current_control_rig
    current_control_rig = rig

    add_construct_graph()
    add_forward_solve()
    add_backward_graph()

    return rig


def add_forward_solve():

    current_control_rig = get_current_control_rig()
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
    try:
        controller.add_link(f'{n(source_node)}.{source_attribute}', f'{n(target_node)}.{target_attribute}')
    except:
        controller.break_all_links(f'{n(source_node)}.{source_attribute}', True)
        controller.break_all_links(f'{n(source_node)}.{source_attribute}', False)
        controller.add_link(f'{n(source_node)}.{source_attribute}', f'{n(target_node)}.{target_attribute}')


def add_animation_channel(controller, name):

    version = util.get_unreal_version()
    if version[0] <= 5 and version[1] <= 3:
        channel = controller.add_template_node('SpawnAnimationChannel::Execute(in InitialValue,in MinimumValue,in MaximumValue,in Parent,in Name,out Item)', unreal.Vector2D(3500, -800), 'SpawnAnimationChannel')

    if version[0] <= 5 and version[1] >= 4:
        channel = controller.add_template_node('SpawnAnimationChannel::Execute(in InitialValue,in MinimumValue,in MaximumValue,in LimitsEnabled,in Parent,in Name,out Item)', unreal.Vector2D(3500, -800), 'SpawnAnimationChannel')

    controller.set_pin_default_value(f'{n(channel)}.Name', name, False)

    return channel
