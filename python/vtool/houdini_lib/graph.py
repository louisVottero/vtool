from vtool import util

character_import = None

if util.in_houdini:
    import hou
    import apex


def reset_current_character_import(name=''):
    character_node = hou.node(character_import)

    if not character_node:

        util.warning('No houdini character import to work with.')
        return

    button = character_node.parm('reload')
    button.pressButton()


def initialize_input_output(live_graph):

    input_id = live_graph.addNode('input', '__parms__')
    output_id = live_graph.addNode('output', '__output__')

    return input_id, output_id


def get_live_graph(edit_graph_instance, parm='stash'):
    geo = edit_graph_instance.parm(parm).eval()
    if not geo:
        geo = hou.Geometry()
    graph = apex.Graph(geo)

    return graph


def update_live_graph(edit_graph, live_graph, parm='stash'):
    geo = hou.Geometry()
    live_graph.writeToGeometry(geo)
    geo.incrementAllDataIds()  # not sure why this is needed
    edit_graph.parm(parm).set(geo)


def build_character_sub_graph_for_apex(character_node=None, name=None, refresh=False):

    if not name:
        name = 'setup_apex'

    if character_node:
        character_node = hou.node(character_node)
    else:
        character_node = hou.node(character_import)

    if not character_node:
        return None, None

    position = character_node.position()

    current_graph = character_node.parent()

    sub_graph = current_graph.node(name)

    if refresh:

        button = character_node.parm('reload')
        button.pressButton()

        if sub_graph:
            sub_graph.destroy()
            sub_graph = None

    if sub_graph:
        edit_graph = sub_graph.node('editgraph1')
    else:
        sub_graph = current_graph.createNode('subnet', name)
        position[1] -= 2
        sub_graph.setPosition(position)

        sub_graph.setInput(0, character_node, 0)
        sub_graph.setInput(1, character_node, 1)

        edit_graph = sub_graph.createNode('apex::editgraph')
        pack_folder = sub_graph.createNode('packfolder')
        invoke_graph = sub_graph.createNode('apex::invokegraph')
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
