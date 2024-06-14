from vtool import util

character_import = None

if util.in_houdini:
    import hou


def build_edit_graph(character_node=None):

    if character_node:
        character_node = hou.node(character_node)
    else:
        character_node = hou.node(character_import)

    position = character_node.position()

    current_graph = character_node.parent()
    sub_graph = current_graph.createNode('subnet', 'setup_ramen')
    position[1] -= 2
    sub_graph.setPosition(position)

    sub_graph.setInput(0, character_node, 0)
    sub_graph.setInput(1, character_node, 1)

    edit_graph = sub_graph.createNode('apex::editgraph', 'ramen_apex_edit_graph')

    return sub_graph, edit_graph


def set_current_character_import(node):

    global character_import

    character_import = node.path()

    util.show('Set current character to %s' % character_import)
