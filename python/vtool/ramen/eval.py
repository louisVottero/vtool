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
    nodes = ui_nodes.get_node_eval_order(items)

    run(nodes)


def step_ui(node_view):

    increment = node_view.eval_step

    items = node_view.items
    nodes = ui_nodes.get_node_eval_order(items)

    if increment >= len(nodes):
        node_view.eval_step = 0
    else:
        run(nodes, increment)
        increment += 1

    if increment == (len(nodes) - 1):
        node_view.eval_step = 0

    node_view.eval_step = increment


@util_ramen.decorator_undo('Eval')
def run(nodes, increment=-1):

    global step_increment

    watch = util.StopWatch()
    watch.start('Ramen Graph')
    util.show('\n\nRun Eval ------------------------------\n')

    visited = {}

    util.show('\nRunning Items ------------------------------\n')

    if increment == -1:
        if util.in_unreal:
            unreal_lib.graph.clean_graph()

        for node in nodes:
            if node.uuid in visited:
                continue
            node.dirty = True
            node.run()

            visited[node.uuid] = None

        if util.in_unreal:
            ui_nodes.handle_unreal_evaluation(nodes)
    if increment > -1:

        util.show('Increment:', increment, 'of', str(len(nodes)))

        if increment == 0:
            if util.in_unreal:
                unreal_lib.graph.clean_graph()

        node = nodes[increment]
        node.dirty = True
        node.run()
        if node.graphic:
            node.graphic.select()
            node.graphic.focus()

        if util.in_unreal:
            eval_items = nodes[:(increment + 1)]
            util.show(len(eval_items), eval_items)
            ui_nodes.handle_unreal_evaluation(eval_items)

    util.show('\nFinished Graph ------------------------------\n\n')
    watch.end()

# def remove():
#    rigs.remove_rigs()
