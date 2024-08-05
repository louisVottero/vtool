# Copyright (C) 2024 Louis Vottero louis.vot@gmail.com    All rights reserved.
from .. import util, util_file
from .ui_lib import ui_nodes
from . import rigs
from vtool.ramen.ui_lib.ui_nodes import handle_unreal_evaluation


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


def run(items):
    orig_items = items
    watch = util.StopWatch()
    watch.start('Ramen Graph')
    util.show('Run Eval ------------------------------')
    visited = {}

    items = {}
    start_eval_items = {}
    eval_items = {}
    start_items = {}

    util.show('Gathering Data ------------------------------')
    for node in orig_items:

        if node.item_type in ui_nodes.register_item:
            node.dirty = True
            uuid = node.uuid
            items[uuid] = node

            inputs = node.rig.get_ins()
            for input_name in inputs:

                if input_name.find('Eval') > -1:

                    if hasattr(node, 'rig_type'):
                        eval_items[uuid] = node
                    else:
                        start_eval_items[uuid] = node
                    break

            if not inputs:
                start_items[uuid] = node

    ui_nodes.uuids = items

    util.show('Running Eval items ------------------------------')

    for uuid in start_eval_items:
        if uuid in visited:
            continue
        node = start_eval_items[uuid]
        if not node:
            continue
        node.run()

        visited[uuid] = None

    for uuid in eval_items:
        if uuid in visited:
            continue
        node = eval_items[uuid]
        if not node:
            continue
        node.run()

        visited[uuid] = None

    util.show('Running Start Items ------------------------------')
    for uuid in start_items:
        if uuid in visited:
            continue
        node = start_items[uuid]
        node.run()

        visited[uuid] = None

    util.show('Running Items ------------------------------')
    for uuid in items:

        if uuid in visited:
            continue

        node = items[uuid]
        node.run()

        visited[uuid] = None

    if util.in_unreal:
        handle_unreal_evaluation(items)

    util.show('Finished Graph')
    watch.end()


def remove():
    rigs.remove_rigs()
