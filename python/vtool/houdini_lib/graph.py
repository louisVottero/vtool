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
    pack_folder = sub_graph.createNode('packfolder', 'ramen_apex_pack')
    invoke_graph = sub_graph.createNode('apex::invokegraph', 'ramen_apex_invoke')
    edit_graph.setPosition(hou.Vector2(-4, -1))
    pack_folder.setPosition(hou.Vector2(0, -1))
    invoke_graph.setPosition(hou.Vector2(0, -2))

    pack_folder.setInput(1, sub_graph.indirectInputs()[0])
    pack_folder.setInput(2, sub_graph.indirectInputs()[1])
    invoke_graph.setInput(0, edit_graph, 0)
    invoke_graph.setInput(1, pack_folder, 0)

    button = pack_folder.parm('reloadnames')
    button.pressButton()

    pack_folder.parm('name1').set('Base')
    pack_folder.parm('type1').set('shp')

    pack_folder.parm('name2').set('Base')
    pack_folder.parm('type2').set('skel')

    return sub_graph, edit_graph


def set_current_character_import(node):

    global character_import

    character_import = node.path()

    util.show('Set current character to %s' % character_import)
