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


def unreal_control_rig_to_python(vtool_custom=False):

    control_rig = get_current_control_rig()

    models = control_rig.get_all_models()

    if not models:
        util.warning('No models found for control rig: %s' % control_rig)

    # model_dict = {}
    python_lines = []
    for model in [models[0]]:

        model_graph_name = model.get_graph_name()
        if not vtool_custom:
            python_lines.append("import unreal")
            python_lines.append("control_rig = unreal.ControlRigBlueprint.get_currently_open_rig_blueprints()[0]")
            python_lines.append("controller = control_rig.get_controller_by_name('%s')" % model_graph_name)
            python_lines.append("library = control_rig.get_local_function_library()")

        nodes = model.get_nodes()

        result_lines = nodes_to_python(nodes, vtool_custom)
        if result_lines:
            python_lines += result_lines

    return python_lines


def selected_nodes_to_python(vtool_custom=False):

    # control_rig = get_current_control_rig()

    selected_nodes = get_selected_nodes(as_string=False)

    python_lines = []
    for key in selected_nodes:
        # model_inst = get_model_inst(key)

        # controller = get_graph_model_controller(model_inst, control_rig)
        nodes = selected_nodes[key]

        result_lines = nodes_to_python(nodes, vtool_custom)
        if result_lines:
            python_lines += result_lines

    python_text = "\n".join(python_lines)
    util.copy_to_clipboard(python_text)
    return python_lines


def nodes_to_python(node_instances, vtool_custom=False):
    variables = set()
    python_lines = []
    all_python_values = []
    all_python_array_size_lines = []
    all_links = []
    var_dict = {}

    for node_inst in node_instances:

        title = node_inst.get_node_title()
        var = node_title_to_var_name(title)
        while var in variables:
            var = util.increment_last_number(var, 1)
        variables.add(var)

        python_text = node_to_python(node_inst, var, vtool_custom)

        if python_text:
            python_lines.append(python_text)

        add_values = True
        if type(node_inst) == unreal.RigVMVariableNode:
            add_values = False
        if add_values:
            python_value_lines, python_array_size_lines = node_pin_default_values_to_python(node_inst, var, vtool_custom)
            if python_value_lines:
                all_python_values += python_value_lines
            if python_array_size_lines:
                all_python_array_size_lines += python_array_size_lines

        links = node_links_to_python(node_inst, var, vtool_custom)
        all_links += links

        var_dict[var] = node_inst

    edited_links = []

    for link in all_links:

        found_one = False
        for key in var_dict:
            node_inst = var_dict[key]
            node_name = node_inst.get_node_path()
            if vtool_custom:
                test_text = '\'' + node_name + '\''
            else:
                test_text = (node_name + '.')

            if link.find(test_text) > -1:
                found_one = True
                if vtool_custom:
                    split_link = link.split(',')
                    split_link[0] = split_link[0].replace('\'' + node_name + '\'', key, 1)
                    split_link[2] = split_link[2].replace('\'' + node_name + '\'', key, 1)
                    link = ','.join(split_link)
                    # link = link.replace('\'' + node_name + '\'', key, 1)
                else:
                    link = link.replace('\'' + node_name, r"f'{%s.get_node_path()}" % key, 1)
                edited_links.append(link)
                break

        if not found_one:
            edited_links.append(link)

    edited_links.sort()
    found = []
    for edit_link in edited_links:
        if edit_link not in found:
            found.append(edit_link)

    target_count_dict = {}
    for link in found:
        split_link = link.split(',')
        target_count = split_link[-2].count('.')

        if not target_count in target_count_dict:
            target_count_dict[target_count] = []
        target_count_dict[target_count].append(link)

    count_keys = list(target_count_dict.keys())
    count_keys.sort()
    found = []
    for key in count_keys:
        count_links = target_count_dict[key]
        if count_links:
            found += count_links

    python_lines.append('')
    python_lines += all_python_array_size_lines
    python_lines.append('')
    python_lines += found
    python_lines.append('')
    python_lines += all_python_values
    # edited_links = list(set(edited_links))

    return python_lines


def node_to_python(node_inst, var_name='', vtool_custom=False):

    python_text = None
    library = get_local_function_library()
    position = node_inst.get_position()
    color = node_inst.get_node_color()
    title = node_inst.get_node_title()

    if not var_name:
        var_name = node_title_to_var_name(title)

    if type(node_inst) == unreal.RigVMUnitNode:
        split_struct = str(node_inst.get_script_struct()).split()

        if len(split_struct) > 1:
            path = split_struct[1]

        python_text = r"%s = controller.add_unit_node_from_struct_path(%s, 'Execute', unreal.Vector2D(%s, %s), '%s')" % (var_name,
                                                                                            path, position.x, position.y, title)
    elif type(node_inst) == unreal.RigVMVariableNode:

        variable_name = node_inst.get_variable_name()
        cpp_type = node_inst.get_cpp_type()
        cpp_type_object = node_inst.get_cpp_type_object()
        is_getter = node_inst.is_getter()

        if cpp_type_object:
            cpp_type_object = r"'%s'" % cpp_type_object.get_path_name()

        default_value = ''

        if cpp_type.startswith('TArray'):
            default_value = '()'

        function = 'add_variable_node'
        if cpp_type_object and cpp_type_object.find('/') > -1:
            function = 'add_variable_node_from_object_path'

        python_text = r"%s = controller.%s('%s','%s',%s,%s,'%s', unreal.Vector2D(%s, %s), '%s')" % (var_name,
                                                            function, variable_name, cpp_type, cpp_type_object, is_getter, default_value, position.x, position.y, title)

    elif type(node_inst) == unreal.RigVMDispatchNode:
        notation = str(node_inst.get_notation())

        python_text = r"%s = controller.add_template_node('%s', unreal.Vector2D(%s, %s), '%s')" % (var_name, notation, position.x, position.y, title)
    elif type(node_inst) == unreal.RigVMRerouteNode:

        pins = node_inst.get_all_pins_recursively()

        cpp_type = pins[0].get_cpp_type()
        cpp_type_object = pins[0].get_cpp_type_object().get_full_name()

        python_text = r"%s = controller.add_free_reroute_node(%s, %s, is_constant = True, custom_widget_name ='', default_value='', position=[%s, %s], node_name='', setup_undo_redo=True)" % (var_name,
                                                                    cpp_type, cpp_type_object, position.x, position.y)
    elif type(node_inst) == unreal.RigVMCommentNode:
        size = node_inst.get_size()
        comment = node_inst.get_comment_text()
        python_text = r"%s = controller.add_comment_node('%s', unreal.Vector2D(%s, %s), unreal.Vector2D(%s, %s), unreal.LinearColor(%s,%s,%s,%s), 'EdGraphNode_Comment')" % (var_name,
                                                         comment, position.x, position.y, size.x, size.y, color.r, color.b, color.g, color.a)

    elif type(node_inst) == unreal.RigVMFunctionEntryNode:
        # entry node
        pass
    elif type(node_inst) == unreal.RigVMFunctionReturnNode:
        # return node
        pass

    elif type(node_inst) == unreal.RigVMFunctionReferenceNode or type(node_inst) == unreal.RigVMCollapseNode:

        full_name = node_inst.get_full_name()

        functions = library.get_functions()

        library.find_function_for_node(node_inst)
        split_path = full_name.split('.')
        class_name = split_path[-1]

        found = False
        for function in functions:
            function_name = function.get_name()
            if class_name == function_name:
                found = True

        if not found:
            class_name = class_name.split('_')
            found = [name for name in class_name if len(name) != 1]
            class_name = '_'.join(found)

        # library=control_rig_inst.get_local_function_library()
        # need to add library at the beginning

        if class_name == 'vetalaLib_Control' and vtool_custom:
            python_text = r"%s = self._create_control(controller, %s, %s)" % (var_name, position.x, position.y)
        else:
            python_text = r"%s = controller.add_function_reference_node(library.find_function('%s'), unreal.Vector2D(%s, %s), '%s')" % (var_name,
                                                              class_name, position.x, position.y, class_name)

    else:
        util.warning('Skipping node: %s' % node_inst)

    return python_text


def node_pin_default_values_to_python(node_inst, var_name, vtool_custom=False):
    pins = node_inst.get_all_pins_recursively()

    python_array_size_lines = []
    python_value_lines = []

    for pin in pins:
        pin_name = pin.get_name()

        if pin.is_array():
            array_size = pin.get_array_size()
            if array_size > 0:
                python_array_size_lines.append("controller.set_array_pin_size(f'{n(%s)}.%s', %s)" % (var_name, pin_name, array_size))

    for pin in pins:
        if pin.is_execute_context():
            continue
        if pin.get_parent_pin():
            continue
        if pin.get_links():
            continue
        pin_name = pin.get_name()
        value = pin.get_default_value()

        if value == '':
            continue
        if value == '()':
            continue
        if value == 'None':
            continue
        if value.startswith('(Type=None'):
            continue
        if value.startswith('(Key=(Type=None'):
            continue
        if pin.get_direction() == unreal.RigVMPinDirection.OUTPUT:
            continue

        # controller.set_pin_default_value('DISPATCH_RigDispatch_SetMetadata.Name', 'Control', False)
        if vtool_custom:
            python_value_lines.append("controller.set_pin_default_value(f'{n(%s)}.%s', '%s', False)" % (var_name, pin_name, value))
        else:
            python_value_lines.append("controller.set_pin_default_value(f'{%s.get_node_path()}.%s', '%s', False)" % (var_name, pin_name, value))

    return python_value_lines, python_array_size_lines


def node_links_to_python(node_inst, var_name, vtool_custom=False):
    pins = node_inst.get_all_pins_recursively()

    links = []

    for pin in pins:
        source_pins = pin.get_linked_source_pins()

        for source_pin in source_pins:
            source_node = source_pin.get_node()

            source_path = source_pin.get_pin_path().split('.')
            source_path = '.'.join(source_path[1:])

            target_path = pin.get_pin_path().split('.')
            target_path = '.'.join(target_path[1:])

            if vtool_custom:
                python_text = r"graph.add_link('%s','%s',%s,'%s',controller)" % (source_node.get_node_path(), source_path, var_name, target_path)
            else:
                python_text = r"controller.add_link('%s.%s',f'{%s.get_node_path()}.%s')" % (source_node.get_node_path(), source_path, var_name, target_path)
            links.append(python_text)

        target_pins = pin.get_linked_target_pins()

        for target_pin in target_pins:
            target_node = target_pin.get_node()

            source_path = pin.get_pin_path().split('.')
            source_path = '.'.join(source_path[1:])

            target_path = target_pin.get_pin_path().split('.')
            target_path = '.'.join(target_path[1:])

            if vtool_custom:
                python_text = r"graph.add_link(%s,'%s','%s','%s',controller)" % (var_name, source_path, target_node.get_node_path(), target_path)
            else:
                python_text = r"controller.add_link(f'{%s.get_node_path()}.%s','%s.%s')" % (var_name, source_path, target_node.get_node_path(), target_path)
            links.append(python_text)

    return links


def get_local_function_library():

    control_rig_inst = get_current_control_rig()

    library = control_rig_inst.get_local_function_library()

    return library


def parse_to_python(parse_objects, controller):

    parse_objects = util.convert_to_sequence(parse_objects)

    python_lines = []

    for parse_object in parse_objects:
        class_name = parse_object['class']
        name = parse_object['name']

        if not class_name:
            # probably a pin value
            pass

        elif class_name.endswith('Node'):
            if class_name == '/Script/RigVMDeveloper.RigVMFunctionEntryNode':
                # entry node
                pass
            elif class_name == '/Script/RigVMDeveloper.RigVMFunctionReturnNode':
                # return node
                pass
            else:
                python_text = node_class_to_python(parse_object, controller)
                python_lines.append(python_text)

        elif class_name == "/Script/RigVMDeveloper.RigVMLink":
            # connection
            python_text = node_link_to_python(parse_object, controller)
            python_lines.append(python_text)
        else:
            pass
            # most likely RigVMPin info

        # import json
        # print(json.dumps(parse_object, indent=4))

    return python_lines


def node_title_to_var_name(node_title):
    node_title = util.camel_to_underscore(node_title)
    node_title = node_title.replace(' ', '_')
    node_title = node_title.replace('__', '_')
    node_title = re.sub(r"\s*\([^)]*\)", "", node_title)
    node_title = node_title.lower()

    return node_title


def node_name_to_var_name(node_name):
    node_name = node_name.replace('RigVMFunction_', '')
    node_name = node_name.replace('DISPATCH_RigVMDispatch_', '')
    node_name = node_name.replace('DISPATCH_RigDispatch_', '')

    new_name = util.camel_to_underscore(node_name)
    new_name.lower()
    new_name = new_name.strip('_')

    return new_name


def function_name_to_node_name(function_name):
    function_name = function_name.replace('FRigUnit_', '')
    function_name = function_name.replace('FRigVMFunction_', '')

    return function_name


def node_link_to_python(parse_object, controller):
    if not parse_object:
        return

    class_name = parse_object['class']
    if not class_name.endswith('Link'):
        util.warning('%s not a link' % class_name)
        return

    link_source = parse_object['properties']['SourcePinPath']
    link_target = parse_object['properties']['TargetPinPath']

    split_source_link = link_source.split('.')
    source_node = node_name_to_var_name(split_source_link[0])
    source_var = '.'.join(split_source_link[1:])

    split_target_link = link_target.split('.')
    target_node = node_name_to_var_name(split_target_link[0])
    target_var = '.'.join(split_target_link[1:])

    python_text = "controller.add_link(f'{%s.get_node_path()}.%s', f'{%s.get_node_path()}.%s')" % (source_node, source_var, target_node, target_var)

    print(python_text)


def node_class_to_python(parse_object, controller):
    if not parse_object:
        return

    class_name = parse_object['class']
    name = parse_object['name']
    var_name = node_name_to_var_name(name)
    if not class_name.endswith('Node'):
        util.warning('%s not a node' % class_name)
        return

    position = parse_object['properties']['Position']
    x, y = util.get_float_numbers(position)

    if 'TemplateNotation' in parse_object['properties']:
        template = parse_object['properties']['TemplateNotation']
        # "(X=272.000000,Y=-224.000000)"
        python_text = r"%s = controller.add_template_node('%s', unreal.Vector2D(%s,%s), '%s')" % (var_name, template, x, y, var_name)
        print(python_text)
    elif 'ResolvedFunctionName' in parse_object['properties']:
        function_name = parse_object['properties']['ResolvedFunctionName']
        function_name = function_name.split('::')[0]
        # if function_name.find('Hierarchy') > -1:
        #    import json
        #    print(json.dumps(parse_object, indent=4))
        # null = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyAddNull', 'Execute',
        #                                                 unreal.Vector2D(3700, -2100), 'HierarchyAddNull')
        python_text = r"%s = controller.add_unit_node_from_struct_path('/Script/RigVM.%s', 'Execute', unreal.Vector2D(%s, %s), '%s')" % (var_name, function_name, x, y, function_name_to_node_name(function_name))
        print(python_text)
    else:
        print('skip     !!!!        ', name, class_name)


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


def get_model_inst(model_name, control_rig_inst=None):

    if not control_rig_inst:
        control_rig_inst = get_current_control_rig()

    models = control_rig_inst.get_all_models()

    for model in models:
        test_model_name = model.get_graph_name()
        if test_model_name == model_name:
            return model


def get_graph_model_controller(model, main_graph=None):

    if not main_graph:
        main_graph = get_current_control_rig()

    model_name = model.get_node_path()
    model_name = model_name.replace(':', '')
    model_name = model_name.replace('FunctionLibrary|', '')
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


def get_selected_nodes(as_string=True):

    control_rig = get_current_control_rig()
    if not control_rig:
        util.warning('No control rig')
        return

    models = control_rig.get_all_models()

    node_name_dict = {}

    for model in models:
        graph_name = model.get_graph_name()
        controller = control_rig.get_controller(model)
        get_selection = True
        nodes = []

        found = []

        if get_selection:
            selected_node_names = controller.get_graph().get_select_nodes()
            found = list(filter(None, map(lambda x: controller.get_graph().find_node(x), selected_node_names)))
        nodes.extend(found)

        if not nodes:
            continue

        if as_string:
            node_names = [node.get_node_path() for node in nodes]
            node_name_dict[graph_name] = node_names
        else:
            node_name_dict[graph_name] = nodes

    return node_name_dict


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
