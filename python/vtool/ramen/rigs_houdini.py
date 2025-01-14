# Copyright (C) 2025 Louis Vottero louis.vot@gmail.com    All rights reserved.

from . import rigs
from . import util as ramen_util

from .. import houdini_lib

from vtool import util

in_houdini = util.in_houdini

if in_houdini:
    import hou
    import apex


class HoudiniUtilRig(rigs.PlatformUtilRig):

    def __init__(self):
        super(HoudiniUtilRig, self).__init__()

        self.character_node = None
        self.graph = None
        self.edit_graph_instance = None
        self.apex = None
        self.apex_input = None
        self.apex_output = None
        self.sub_apex = None
        self.sub_apex_node = None
        self.apex_point_transform = None
        self.control_names = []

    def _get_sub_apex_name(self):
        rig_name = 'vetala_%s_1' % self.__class__.__name__
        rig_name = rig_name.replace('Houdini', '')

        matching_nodes = self.apex.matchNodes(rig_name)
        while matching_nodes:
            rig_name = util.increment_last_number(rig_name)
            matching_nodes = self.apex.matchNodes(rig_name)

        return rig_name

    def _init_apex(self):
        sub_graph, apex_graph = houdini_lib.graph.build_character_sub_graph_for_apex(self.character_node, 'ramen_apex')

        houdini_lib.graph.set_current_network(sub_graph)
        houdini_lib.graph.set_current_apex_node(apex_graph)

        self.graph = sub_graph
        self.edit_graph_instance = apex_graph

        self.apex = houdini_lib.graph.get_apex_graph(self.edit_graph_instance)

        self.apex_input, self.apex_output = houdini_lib.graph.initialize_input_output(self.apex)

        bone_deform_nodes = self.apex.matchNodes('bone_deform')
        if bone_deform_nodes:
            point_transform = self.apex.matchNodes('point_transform')
            self.apex_point_transform = point_transform[0]
        else:
            bone_deform, point_transform = houdini_lib.graph.add_bone_deform(self.apex)
            self.apex_point_transform = point_transform

    def _init_sub_apex(self):

        uuid = self.rig.uuid

        self.sub_apex_node = self._get_sub_apex(uuid)

        node_name = ''
        if self.sub_apex_node:
            node_name = self.apex.getNodeName(self.sub_apex_node)

        if node_name:
            self.sub_apex = apex.Graph(node_name)
        else:
            self.sub_apex = apex.Graph()

        self.sub_apex_input, self.sub_apex_output = houdini_lib.graph.initialize_input_output(self.sub_apex)

        uuid_value = self.sub_apex.addNode('UUID_value', 'Value<String>')
        self.sub_apex.setNodePosition(uuid_value, hou.Vector3(2, 2, 0))

        uuid_value_port = self.sub_apex.getPort(uuid_value, 'parm')
        uuid_in = self.sub_apex.addGraphInput(0, 'uuid')

        self.sub_apex.addWire(uuid_in, uuid_value_port)

    def _get_sub_apex(self, uuid):

        if not self.edit_graph_instance:
            return

        node_count = houdini_lib.graph.get_apex_node_count(self.edit_graph_instance)

        for node in range(node_count):
            node_parms = self.apex.getNodeParms(node)

            # _apex.Dict hs no function get...
            node_uuid = node_parms.getValue('uuid')

            if node_uuid == uuid:
                return node

    def _inc_control_name(self, control_name, increment_last_number):

        if not control_name in self.control_names:
            return control_name
        inc = 0
        while(control_name in self.control_names):

            if increment_last_number:
                control_name = util.increment_last_number(control_name)
            else:
                control_name = util.increment_first_number(control_name)

            inc += 1

            if inc > 5000:
                break

        return control_name

    def _build_graph(self):
        return

    def _post_build_graph(self):

        input_ports = self.apex.getInputPorts(self.sub_apex_node)

        for input_port in input_ports:

            input_port_name = self.apex.portName(input_port)

            if input_port_name.startswith('control_'):
                new_input = self.apex.addGraphInput(input_port, input_port_name)
                self.apex.addWire(new_input, input_port)

        output_ports = self.apex.getOutputPorts(self.sub_apex_node)

        for output_port in output_ports:

            output_port_name = self.apex.portName(output_port)

            if output_port_name == 'next':
                continue

            point_transform_in = self.apex.getPort(self.apex_point_transform, 'transforms')

            sub_port = self.apex.addSubPort(point_transform_in, output_port_name)
            self.apex.addWire(output_port, sub_port)

    def is_valid(self):
        if self.rig.state == rigs.RigState.CREATED:
            if not self.apex:
                return False
        if self.rig.state == rigs.RigState.LOADED:
            if not self.sub_apex_node:
                return False

        return True

    def set_node_position(self, position_x, position_y):
        node_vector = hou.Vector3(position_x, position_y, 0)

        self.apex.setNodePosition(self.sub_apex_node, node_vector)

        houdini_lib.graph.update_apex_graph(self.edit_graph_instance, self.apex)

    def build(self):
        super(HoudiniUtilRig, self).build()

        uuid = self.rig.uuid

        controls = houdini_lib.graph.get_apex_controls()
        self.control_names = controls

        if not in_houdini:
            return

        if not self.graph:
            util.warning('No houdini sub graph initialized')
            return
        if not self.apex:
            util.warning('No apex graph initialized')
            return
        # if not self.sub_apex:
        #    util.warning('No sub apex graph initialized')
        #    return

        if not self.sub_apex:
            self._init_sub_apex()

        self._build_graph()

        parm_dict = self.sub_apex.getParmDict()
        parm_dict['uuid'] = uuid

        sub_apex_name = self._get_sub_apex_name()
        self.sub_apex_node = self.apex.addSubnet(sub_apex_name, self.sub_apex)

        self.apex.setNodeParms(self.sub_apex_node, parm_dict)
        self.apex.setNodePosition(self.sub_apex_node, hou.Vector3(5, 0, 0))

        self._post_build_graph()

        houdini_lib.graph.update_apex_graph(self.edit_graph_instance, self.apex)

    def unbuild(self):
        super(HoudiniUtilRig, self).unbuild()

        uuid = self.rig.uuid
        node_name = None

        if self.sub_apex_node:
            node_name = self.apex.nodeName(self.sub_apex_node)

        if not node_name:
            sub_apex = self._get_sub_apex(uuid)

            if sub_apex:
                node_name = self.apex.nodeName(sub_apex)

        if node_name:
            self.apex.removeNode(node_name)
            self.sub_apex_node = None

        houdini_lib.graph.update_apex_graph(self.edit_graph_instance, self.apex)

    def delete(self):
        super(HoudiniUtilRig, self).delete()

        self.unbuild()

        self.sub_apex = None

        houdini_lib.graph.update_apex_graph(self.edit_graph_instance, self.apex)

    def load(self):
        super(HoudiniUtilRig, self).load()

        self.character_node = houdini_lib.graph.character_import

        if not self.character_node:
            return

        util.show('\tLoading character node: %s' % houdini_lib.graph.character_import)

        if not self.apex_input or not self.apex_output:
            self._init_apex()

        houdini_lib.graph.update_apex_graph(self.edit_graph_instance, self.apex)


class HoudiniFkRig(HoudiniUtilRig):

    def _build_graph(self):

        joints = self.rig.attr.get('joints')

        offset = 0

        sub = False

        for joint in joints:

            matrix = houdini_lib.graph.get_joint_matrix(joint)

            joint_description = self.get_joint_description(joint)
            control_name = self.get_control_name(joint_description, sub=False)

            control_name = self._inc_control_name(control_name, not sub)

            self.control_names.append(control_name)

            transform = self.sub_apex.addNode(control_name, 'TransformObject')
            self.sub_apex.setNodePosition(transform, hou.Vector3(2 + offset, -2 - offset, 0))

            parms = self.sub_apex.getNodeParms(transform)
            parms['restlocal'] = matrix
            self.sub_apex.setNodeParms(transform, parms)

            transform_t_in = self.sub_apex.getPort(transform, 't[in]')
            transform_r_in = self.sub_apex.getPort(transform, 'r[in]')
            transform_s_in = self.sub_apex.getPort(transform, 's[in]')

            transform_xform = self.sub_apex.getPort(transform, 'xform[out]')

            sub_input_t = self.sub_apex.addGraphInput(0, 'control_%s_t' % control_name)
            sub_input_r = self.sub_apex.addGraphInput(0, 'control_%s_r' % control_name)
            sub_input_s = self.sub_apex.addGraphInput(0, 'control_%s_s' % control_name)

            self.sub_apex.addWire(sub_input_t, transform_t_in)
            self.sub_apex.addWire(sub_input_r, transform_r_in)
            self.sub_apex.addWire(sub_input_s, transform_s_in)

            joint_out = self.sub_apex.addGraphOutput(1, joint)

            self.sub_apex.addWire(transform_xform, joint_out)

            offset += 2

