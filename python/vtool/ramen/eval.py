# Copyright (C) 2024 Louis Vottero louis.vot@gmail.com    All rights reserved.
from . import util as util_ramen
from .. import util, util_file
from .ui_lib import ui_nodes
from . import rigs
from .. import unreal_lib


def run_json(json_file):

    items = []
    connections = []

    json_data = util_file.get_json(json_file)

    for item_dict in json_data:
        item_type = item_dict['type']
        if item_type in ui_nodes.register_item:
            node = ui_nodes.register_item[item_type]()
            node.load(item_dict)
            items.append(node)
        if item_type == 4:
            connections.append(item_dict)

    for connection in connections:
        line_inst = ui_nodes.NodeLine()
        line_inst.load(connection)

    run(items)


def run_ui(node_view):

    items = node_view.items
    run(items)


@util_ramen.decorator_undo('Eval')
def run(items):

    orig_items = items
    watch = util.StopWatch()
    watch.start('Ramen Graph')
    util.show('\n\nRun Eval ------------------------------\n')

    if util.in_unreal:
        unreal_lib.graph.clean_graph()

    visited = {}
    items = {}
    detached_items = {}
    start_eval_items = {}
    eval_items = {}
    start_items = {}

    util.show('Gathering Data ------------------------------')
    for node in orig_items:

        if node.item_type in ui_nodes.register_item:
            node.dirty = True
            uuid = node.uuid
            items[uuid] = node

            # inputs = node.rig.get_ins()
            # outputs = node.rig.get_outs()

            connected_ins = node.get_input_connected_nodes()
            connected_outs = node.get_output_connected_nodes()

            if not connected_ins and not connected_outs:
                detached_items[uuid] = node

    util.show('\nRunning Detached Items ------------------------------\n')
    for uuid in detached_items:
        if uuid in visited:
            continue
        node = detached_items[uuid]
        node.run()

        visited[uuid] = None

    nodes = ui_nodes.get_node_eval_order(orig_items)
    util.show('\nRunning Items ------------------------------\n')
    for node in nodes:
        if node.uuid in visited:
            continue
        node.run()

        visited[node.uuid] = None

    if util.in_unreal:
        ui_nodes.handle_unreal_evaluation(orig_items)

        # unreal_lib.graph.compile_control_rig()

    util.show('\nFinished Graph ------------------------------\n\n')
    watch.end()

# def remove():
#    rigs.remove_rigs()
