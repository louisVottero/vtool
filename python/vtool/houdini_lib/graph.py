# Copyright (C) 2025 Louis Vottero louis.vot@gmail.com    All rights reserved.

from vtool import util

character_import = None
current_network = None
current_apex_node = None
current_apex = None

if util.in_houdini:
    import hou
    import apex


def set_current_character_import(node):

    global character_import

    character_import = node.path()

    util.show('Set current character to %s' % character_import)


def set_current_network(network):
    global current_network
    current_network = network


def set_current_apex_node(edit_graph):
    global current_apex_node
    current_apex_node = edit_graph


def reset_current_character_import(name=''):
    character_node = hou.node(character_import)

    if not character_node:

        util.warning('No houdini character import to work with.')
        return

    button = character_node.parm('reload')
    button.pressButton()


def initialize_input_output(apex_graph):

    input_nodes = apex_graph.matchNodes('input')
    output_nodes = apex_graph.matchNodes('output')
    if input_nodes and output_nodes:
        return input_nodes[0], output_nodes[0]

    input_id = apex_graph.addNode('input', '__parms__')
    output_id = apex_graph.addNode('output', '__output__')

    position = hou.Vector3(20, 0, 0)
    apex_graph.setNodePosition(output_id, position)

    return input_id, output_id


def add_bone_deform(apex_graph):

    base_shp = apex_graph.addGraphInput(0, 'Base.shp')
    base_skel = apex_graph.addGraphInput(0, 'Base.skel')

    out_base_shp = apex_graph.addGraphOutput(1, 'Base.shp')
    out_base_skel = apex_graph.addGraphOutput(1, 'Base.skel')

    point_transform = apex_graph.addNode('point_transform', 'skel::SetPointTransforms')
    apex_graph.setNodePosition(point_transform, hou.Vector3(16, -2, 0))
    point_skel_in = apex_graph.getPort(point_transform, "geo[in]")
    point_skel_out = apex_graph.getPort(point_transform, "geo[out]")

    bone_deform = apex_graph.addNode('bone_deform', 'sop::bonedeform')
    apex_graph.setNodePosition(bone_deform, hou.Vector3(18, -1, 0))
    bone_shp_in = apex_graph.getPort(bone_deform, "geoinput0")
    bone_skel_in = apex_graph.getPort(bone_deform, "geoinput1")
    bone_skel_pose_in = apex_graph.getPort(bone_deform, "geoinput2")
    bone_shp_out = apex_graph.getPort(bone_deform, "geo[out]")

    rest = apex_graph.addNode('rest', 'Value<Geometry>')
    apex_graph.setNodePosition(rest, hou.Vector3(14, -2, 0))
    rest_parm = apex_graph.getPort(rest, 'parm')
    rest_value = apex_graph.getPort(rest, 'value')

    apex_graph.addWire(base_shp, bone_shp_in)
    apex_graph.addWire(base_skel, bone_skel_in)
    apex_graph.addWire(point_skel_out, bone_skel_pose_in)

    apex_graph.addWire(base_skel, rest_parm)
    apex_graph.addWire(rest_value, point_skel_in)

    apex_graph.addWire(bone_shp_out, out_base_shp)
    apex_graph.addWire(point_skel_out, out_base_skel)

    return bone_deform, point_transform


def get_apex_graph(edit_graph_instance, parm='stash'):

    global current_apex

    if current_apex:
        if current_apex_node:
            if current_apex_node.name() == edit_graph_instance.name():
                return current_apex

    geo = edit_graph_instance.parm(parm).eval()

    if not geo:
        geo = hou.Geometry()

    graph = apex.Graph(geo)

    current_apex = graph
    return graph


def update_apex_graph(edit_graph_instance, apex_graph, parm='stash'):
    geo = hou.Geometry()
    apex_graph.writeToGeometry(geo)
    geo.incrementAllDataIds()  # not sure why this is needed
    edit_graph_instance.parm(parm).set(geo)


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
        if current_apex_node:
            edit_graph = current_apex_node
        else:
            edit_graph = sub_graph.node('editgraph1')
    else:
        sub_graph = current_graph.createNode('subnet', name)
        position[1] -= 2
        sub_graph.setPosition(position)

        sub_graph.setInput(0, character_node, 0)
        sub_graph.setInput(1, character_node, 1)

        edit_graph = sub_graph.createNode('apex::editgraph')
        pack_folder = sub_graph.createNode('packfolder')
        configure_controls = sub_graph.createNode('apex::configurecontrols')
        edit_graph.setPosition(hou.Vector2(2.5, 0))
        pack_folder.setPosition(hou.Vector2(0, -1))
        configure_controls.setPosition(hou.Vector2(0, -2))

        pack_folder.setInput(1, sub_graph.indirectInputs()[0])
        pack_folder.setInput(2, sub_graph.indirectInputs()[1])
        pack_folder.setInput(3, edit_graph)

        configure_controls.setInput(0, pack_folder)

        button = pack_folder.parm('reloadnames')
        button.pressButton()

        pack_folder.parm('name1').set('Base')
        pack_folder.parm('type1').set('shp')

        pack_folder.parm('name2').set('Base')
        pack_folder.parm('type2').set('skel')

        pack_folder.parm('name3').set('Base')
        pack_folder.parm('type3').set('rig')

    return sub_graph, edit_graph


def get_apex_node_count(apex_sop_node):
    points = apex_sop_node.geometry().points()
    return len(points)


def get_apex_controls():

    if not current_apex:
        return

    geometry = current_apex_node.geometry(1)
    portname = geometry.findVertexAttrib('portname')
    portnames = list(portname.strings())

    found = {}

    for name in portnames:
        if name.startswith('control_'):
            found[name[8:-2]] = None

    return list(found.keys())


def get_joints(filter_list):

    if not character_import:
        return []

    character_inst = hou.node(character_import)

    geometry = character_inst.geometry(1)
    name = geometry.findPointAttrib('name')
    bones = list(name.strings())

    found = []
    for filter_text in filter_list:
        matching = util.unix_match(filter_text, bones)
        if len(matching) > 1:
            matching = util.sort_string_integer(matching)
        if matching:
            found += matching

    return found


def get_joint_matrix(joint_name):

    if not character_import:
        return

    character_inst = hou.node(character_import)

    geometry = character_inst.geometry(1)
    name = geometry.findPointAttrib('name')
    bones = list(name.strings())

    points = geometry.points()

    matrix = None

    for inc in range(len(bones)):
        bone = bones[inc]
        if bone == joint_name:
            position = points[inc].position()
            rotation = points[inc].attribValue('transform')

            matrix = hou.Matrix4((
                                    rotation[0], rotation[1], rotation[2], 0.0,
                                    rotation[3], rotation[4], rotation[5], 0.0,
                                    rotation[6], rotation[7], rotation[8], 0.0,
                                    position[0], position[1], position[2], 1.0
                                ))

            break

    return matrix

