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
        self._parm_values = {}
        self._pass_attributes = ['parent', 'controls']
        self._attribute_offset = 0
        self._attribute_out_offset = 0
        self._attribute_node = {}

        self._pass_attributes

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

        if not self.sub_apex:
            if node_name:
                self.sub_apex = apex.Graph(node_name)
            else:
                self.sub_apex = apex.Graph()

            self.sub_apex_input, self.sub_apex_output = houdini_lib.graph.initialize_input_output(self.sub_apex)

            self._add_in_string('uuid', uuid)
            self._initialize_attributes()

            self._init_sub_apex_parent_and_controls()

    def _init_sub_apex_parent_and_controls(self):
            parent_value_node = self._attribute_node['parent']
            position = self.sub_apex.nodePosition(parent_value_node)
            position[0] += 2
            # position[1] += 2

            parent_default_matrix = hou.Matrix4()
            parent_default_matrix.setToIdentity()

            get_parent = self.sub_apex.addNode('get_parent', 'array::Get<Matrix4>')
            self.sub_apex.setNodePosition(get_parent, position)

            parms = self.sub_apex.getNodeParms(get_parent)
            parms['index'] = -1
            parms['default'] = parent_default_matrix
            self.sub_apex.setNodeParms(get_parent, parms)

            get_parent_in = self.sub_apex.getPort(get_parent, 'array')

            parent_value = self.sub_apex.getPort(parent_value_node, 'value')
            self.sub_apex.addWire(parent_value, get_parent_in)

            control_value_node = self._attribute_node['controls']
            position = self.sub_apex.nodePosition(control_value_node)
            position[0] -= 2
            control_parm = self.sub_apex.getPort(control_value_node, 'parm')

            build_controls = self.sub_apex.addNode('array_build_controls', 'array::Build<Matrix4>')
            self.sub_apex.setNodePosition(build_controls, position)
            build_controls_result = self.sub_apex.getPort(build_controls, 'result')

            self.sub_apex.addWire(build_controls_result, control_parm)

    def _initialize_node_attribute(self, attribute_name):

        if not attribute_name in self._pass_attributes:
            return

        value, attr_type = super(HoudiniUtilRig, self)._initialize_node_attribute(attribute_name)

        if attr_type == rigs.AttrType.STRING:
            self._add_in_string(attribute_name, value[0])
        if attr_type == rigs.AttrType.BOOL:
            self._add_in_bool(attribute_name, value)

    def _initialize_input(self, attribute_name):

        if not attribute_name in self._pass_attributes:
            return

        value, attr_type = super(HoudiniUtilRig, self)._initialize_input(attribute_name)

        if attr_type == rigs.AttrType.TRANSFORM:
            self._add_in_transform(attribute_name, value)

        if attr_type == rigs.AttrType.BOOL:
            self._add_in_bool(attribute_name, value)

    def _initialize_output(self, attribute_name):

        if not attribute_name in self._pass_attributes:
            return

        value, attr_type = super(HoudiniUtilRig, self)._initialize_output(attribute_name)

        if attr_type == rigs.AttrType.TRANSFORM:
            self._add_out_transform(attribute_name, value)

    def _add_in_string(self, attribute_name, value):

        value_node = self.sub_apex.addNode('%s_value' % attribute_name, 'Value<String>')
        self.sub_apex.setNodePosition(value_node, hou.Vector3(2, 2 + self._attribute_offset, 0))

        value_port = self.sub_apex.getPort(value_node, 'parm')
        port_in = self.sub_apex.addGraphInput(0, attribute_name)

        self.sub_apex.addWire(port_in, value_port)
        self._parm_values[attribute_name] = value
        self._attribute_node[attribute_name] = value_node

        self._attribute_offset += 1.5

    def _add_in_bool(self, attribute_name, value):

        value_node = self.sub_apex.addNode('%s_value' % attribute_name, 'Value<Bool>')
        self.sub_apex.setNodePosition(value_node, hou.Vector3(2, 2 + self._attribute_offset, 0))

        value_port = self.sub_apex.getPort(value_node, 'parm')
        port_in = self.sub_apex.addGraphInput(0, attribute_name)

        self.sub_apex.addWire(port_in, value_port)
        self._parm_values[attribute_name] = value
        self._attribute_node[attribute_name] = value_node

        self._attribute_offset += 1.5

    def _add_in_transform(self, attribute_name, value):

        value_node = self.sub_apex.addNode('%s_value' % attribute_name, 'Value<Matrix4Array>')
        self.sub_apex.setNodePosition(value_node, hou.Vector3(2, 2 + self._attribute_offset, 0))

        value_port = self.sub_apex.getPort(value_node, 'parm')
        port_in = self.sub_apex.addGraphInput(0, attribute_name)

        self.sub_apex.addWire(port_in, value_port)
        self._attribute_node[attribute_name] = value_node

        self._attribute_offset += 1.5

    def _add_out_transform(self, attribute_name, value):

        value_node = self.sub_apex.addNode('%s_value' % attribute_name, 'Value<Matrix4Array>')

        out_position = self.sub_apex.nodePosition(1)
        out_position[0] = out_position.x() - 2
        out_position[1] = out_position.y() + 2 + self._attribute_out_offset

        self.sub_apex.setNodePosition(value_node, out_position)

        value_port = self.sub_apex.getPort(value_node, 'value')
        port_out = self.sub_apex.addGraphOutput(1, attribute_name)
        self.sub_apex.addWire(value_port, port_out)
        self._attribute_node[attribute_name] = value_node

        self._attribute_out_offset += -1.5

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

            if output_port_name == 'next' or output_port_name == 'controls':
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

        if not in_houdini:
            return

        controls = houdini_lib.graph.get_apex_controls()
        self.control_names = controls

        if not self.graph:
            util.warning('No houdini sub graph initialized')
            return
        if not self.apex:
            util.warning('No apex graph initialized')
            return

        if not self.sub_apex:
            self._init_sub_apex()

        self._build_graph()

        parm_dict = self.sub_apex.getParmDict()

        for parm_key in self._parm_values:
            parm_value = self._parm_values[parm_key]

            parm_dict[parm_key] = parm_value

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

        if self.sub_apex:
            ports = self.sub_apex.getOutputPorts(0)
            found_nodes = []

            for port in ports:
                port_name = self.sub_apex.portName(port)
                if port_name.startswith('control_'):
                    nodes = self.sub_apex.getConnectedNodes(port, True, True)
                    found_nodes += nodes

            self.sub_apex.removeNodes(list(set(found_nodes)))

        if not self.sub_apex_node is None:
            found_wires = []
            inputs = self.apex.getInputPorts(self.sub_apex_node)
            for input_value in inputs:
                port_name = self.apex.portName(input_value)
                if port_name.startswith('control_'):

                    port_wires = self.apex.portWires(input_value)
                    if port_wires:
                        found_wires += port_wires

            self.apex.removeWires(found_wires, True)

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

        if not joints:
            return
        use_joint_name = self.rig.attr.get('use_joint_name')
        hierarchy = self.rig.attr.get('hierarchy')

        get_parent = self.sub_apex.matchNodes('get_parent')[0]
        get_parent_value = self.sub_apex.getPort(get_parent, 'value')
        parent_matrix = self.sub_apex.getPortData(get_parent_value, False)

        array_build_controls = self.sub_apex.matchNodes('array_build_controls')[0]
        build_controls_in = self.sub_apex.getPort(array_build_controls, 'values')

        offset = 0

        sub = False
        last_transform = None

        for joint in joints:

            matrix = houdini_lib.graph.get_joint_matrix(joint)

            joint_description = None

            if use_joint_name:
                joint_description = self.get_joint_description(joint)

            control_name = self.get_control_name(joint_description, sub=False)

            control_name = self._inc_control_name(control_name, not sub)

            self.control_names.append(control_name)

            transform = self.sub_apex.addNode(control_name, 'TransformObject')
            self.sub_apex.setNodePosition(transform, hou.Vector3(4 + offset, -2 - offset, 0))

            matrix = parent_matrix.inverted() * matrix

            parms = self.sub_apex.getNodeParms(transform)
            parms['restlocal'] = matrix
            self.sub_apex.setNodeParms(transform, parms)

            transform_t_in = self.sub_apex.getPort(transform, 't[in]')
            transform_r_in = self.sub_apex.getPort(transform, 'r[in]')
            transform_s_in = self.sub_apex.getPort(transform, 's[in]')

            transform_xform = self.sub_apex.getPort(transform, 'xform[out]')
            parent_xform_in = self.sub_apex.getPort(transform, 'parent[in]')
            parent_localxform_in = self.sub_apex.getPort(transform, 'parentlocal[in]')

            sub_input_t = self.sub_apex.addGraphInput(0, 'control_%s_t' % control_name)
            sub_input_r = self.sub_apex.addGraphInput(0, 'control_%s_r' % control_name)
            sub_input_s = self.sub_apex.addGraphInput(0, 'control_%s_s' % control_name)

            self.sub_apex.addWire(sub_input_t, transform_t_in)
            self.sub_apex.addWire(sub_input_r, transform_r_in)
            self.sub_apex.addWire(sub_input_s, transform_s_in)

            joint_out = self.sub_apex.addGraphOutput(1, joint)

            self.sub_apex.addWire(transform_xform, joint_out)

            self.sub_apex.addWire(get_parent_value, parent_xform_in)

            sub_build_controls_in = self.sub_apex.addSubPort(build_controls_in, control_name)

            self.sub_apex.addWire(transform_xform, sub_build_controls_in)

            if hierarchy:

                if last_transform:
                    last_xform_out = self.sub_apex.getPort(last_transform, 'xform[out]')
                    last_localxform_out = self.sub_apex.getPort(last_transform, 'localxform[out]')

                    self.sub_apex.addWire(last_xform_out, parent_xform_in)
                    self.sub_apex.addWire(last_localxform_out, parent_localxform_in)

                parent_matrix = self.sub_apex.getPortData(transform_xform, False)
                last_transform = transform

            offset += 2

