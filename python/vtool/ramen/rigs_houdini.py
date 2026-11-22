# Copyright (C) 2025 Louis Vottero louis.vot@gmail.com    All rights reserved.

from collections.abc import Collection
from dataclasses import dataclass, field

from . import rigs
from . import util as ramen_util

from .. import houdini_lib

from vtool import util
from vtool import util_math

in_houdini = util.in_houdini

if in_houdini:
    import hou
    import apex


@dataclass
class ControlData:
    node_id: int
    network_id: int
    xform: hou.Matrix4 = field(default_factory=hou.Matrix4)
    rest_xform: hou.Matrix4 = field(default_factory=hou.Matrix4)


class ControlTracker:

    def __init__(self):
        self._controls: dict[str, ControlData] = {}

    def track(self,
              name: str,
              node_id: int,
              parent_id: int,
              xform: hou.Matrix4,
              rest_xform: hou.Matrix4) -> ControlData:

        data = ControlData(node_id, parent_id, xform, rest_xform)

        self._controls[name] = data

        return data

    def get(self, name: str) -> ControlData | None:
        return self._controls.get(name)


control_tracker = ControlTracker()


class HoudiniUtilRig(rigs.PlatformUtilRig):

    def __init__(self):
        super(HoudiniUtilRig, self).__init__()

        self.character_node = None
        self.graph = None
        self.edit_graph_instance = None
        self.apex = None
        self.apex_input = None
        self.apex_output = None
        self.sub_input = None
        self.sub_output = None
        self.sub_apex = None
        self.sub_apex_node = None
        self.apex_point_transform = None
        self.control_names = []
        self._parm_values = {}
        self._attribute_offset = 0
        self._attribute_out_offset = 0
        self._y_offset = 30
        self._spacing = 3
        self._attribute_node = {}

    def _get_sub_apex_name(self):
        rig_name = 'vetala_%s_1' % self.__class__.__name__
        rig_name = rig_name.replace('Houdini', '')

        matching_nodes = self.apex.matchNodes(rig_name)
        while matching_nodes:
            rig_name = util.increment_last_number(rig_name)
            matching_nodes = self.apex.matchNodes(rig_name)

        return rig_name

    def _init_apex(self):
        sub_graph, apex_graph = houdini_lib.graph.build_character_sub_graph_for_apex(self.character_node, 'ramen_apeux')

        houdini_lib.graph.current.network = sub_graph
        houdini_lib.graph.current.apex_node = apex_graph

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

            self.sub_input, self.sub_output = houdini_lib.graph.initialize_input_output(self.sub_apex)

            self._add_in_string('uuid', uuid)
            self._initialize_attributes()

            self._init_sub_apex_parent_and_controls()

            self._sub_apex_node = self._get_sub_apex(uuid)

    def _init_sub_apex_parent_and_controls(self):
        if not 'parent' in self._attribute_node:
            return

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

        value, attr_type = super(HoudiniUtilRig, self)._initialize_node_attribute(attribute_name)

        if attr_type == rigs.AttrType.STRING:
            self._add_in_string(attribute_name, value[0])
        if attr_type == rigs.AttrType.BOOL:
            self._add_in_bool(attribute_name, value)

    def _initialize_input(self, attribute_name):

        value, attr_type = super(HoudiniUtilRig, self)._initialize_input(attribute_name)

        if attr_type == rigs.AttrType.TRANSFORM:
            self._add_in_transform(attribute_name, value)

        if attr_type == rigs.AttrType.BOOL:
            self._add_in_bool(attribute_name, value)

        if attr_type == rigs.AttrType.VECTOR:
            self._add_in_vector(attribute_name, value)

        if attr_type == rigs.AttrType.COLOR:
            self._add_in_vector(attribute_name, value)

    def _initialize_output(self, attribute_name):

        value, attr_type = super(HoudiniUtilRig, self)._initialize_output(attribute_name)

        if attr_type == rigs.AttrType.TRANSFORM:
            self._add_out_transform(attribute_name, value)

    def _place_in_node(self, node_index: int) -> None:
        self.sub_apex.setNodePosition(node_index, hou.Vector3(self._spacing, self._y_offset + self._attribute_offset, 0))

    def _place_out_node(self, node_index: int) -> None:
        out_position = self.sub_apex.nodePosition(self.sub_output)
        out_position[0] = out_position.x() - self._spacing
        out_position[1] = out_position.y() + self._y_offset + self._attribute_out_offset

        self.sub_apex.setNodePosition(node_index, out_position)

    def _wire_in_value(self, node_index: int, name: str) -> None:
        value_port = self.sub_apex.getPort(node_index, 'parm')
        port_in = self.sub_apex.addGraphInput(self.sub_input, name)
        self.sub_apex.addWire(port_in, value_port)

    def _wire_out_value(self, node_index: int, name: str) -> None:
        value_port = self.sub_apex.getPort(node_index, 'value')
        port_out = self.sub_apex.addGraphOutput(self.sub_output, name)
        self.sub_apex.addWire(value_port, port_out)

    def _add_in_string(self, attribute_name, value):

        value_node = self.sub_apex.addNode('%s_value' % attribute_name, 'Value<String>')
        self._place_in_node(value_node)
        self._wire_in_value(value_node, attribute_name)

        self._parm_values[attribute_name] = value
        self._attribute_node[attribute_name] = value_node
        self._attribute_offset += 1.5

    def _add_in_bool(self, attribute_name: str, value):

        value_node = self.sub_apex.addNode('%s_value' % attribute_name, 'Value<Bool>')
        self._place_in_node(value_node)
        self._wire_in_value(value_node, attribute_name)

        self._parm_values[attribute_name] = value
        self._attribute_node[attribute_name] = value_node
        self._attribute_offset += 1.5

    def _add_in_vector(self, attribute_name: str, value):
        value_node = self.sub_apex.addNode('%s_value' % attribute_name, 'Value<Vector3>')
        self._place_in_node(value_node)
        self._wire_in_value(value_node, attribute_name)

        if value:
            value = value[0]
            if len(value) == 4:
                value = value[:-1]
            out_value = hou.Vector3(*value)
        else:
            out_value = hou.Vector3()

        # if attribute_name == 'shape_scale':
        #    out_value *= 100

        self._parm_values[attribute_name] = out_value
        self._attribute_node[attribute_name] = value_node
        self._attribute_offset += 1.5

    def _add_in_transform(self, attribute_name: str, value):

        value_node = self.sub_apex.addNode('%s_value' % attribute_name, 'Value<Matrix4Array>')
        self._place_in_node(value_node)
        self._wire_in_value(value_node, attribute_name)

        # self._parm_values[attribute_name] = value
        self._attribute_node[attribute_name] = value_node
        self._attribute_offset += 1.5

    def _add_out_transform(self, attribute_name: str, value):

        value_node = self.sub_apex.addNode('%s_value' % attribute_name, 'Value<Matrix4Array>')
        self._place_out_node(value_node)
        self._wire_out_value(value_node, attribute_name)

        # self._parm_values[attribute_name] = value
        self._attribute_node[attribute_name] = value_node
        self._attribute_offset += 1.5

    def _get_sub_apex(self, uuid):
        if not self.edit_graph_instance:
            return

        if hasattr(self.apex, 'allNodes'):
            node_count = len(list(self.apex.allNodes()))
        else:
            node_count = houdini_lib.graph.get_apex_node_count(self.edit_graph_instance)

        for node in range(node_count):
            node_parms = self.apex.getNodeParms(node)

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
                new_input = self.apex.addGraphInput(self.apex_input, input_port_name)
                self.apex.addWire(new_input, input_port)

        output_ports = self.apex.getOutputPorts(self.sub_apex_node)

        for output_port in output_ports:

            output_port_name = self.apex.portName(output_port)

            if output_port_name in {'next', 'controls', 'sub_controls'}:
                continue

            point_transform_in = self.apex.getPort(self.apex_point_transform, 'transforms')

            sub_port = self.apex.addSubPort(point_transform_in, output_port_name)
            self.apex.addWire(output_port, sub_port)

    def _set_parm_values(self):
        parm_dict = self.sub_apex.getParmDict()

        for parm_key in self._parm_values:
            parm_value = self._parm_values[parm_key]

            if parm_value is None:
                continue

            parm_dict[parm_key] = parm_value

        self.apex.setNodeParms(self.sub_apex_node, parm_dict)

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

        sub_apex_name = self._get_sub_apex_name()
        self.sub_apex_node = self.apex.addSubnet(sub_apex_name, self.sub_apex)

        self._set_parm_values()

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

        self.character_node = houdini_lib.graph.current.character_import

        if not self.character_node:
            return

        util.show(f'\tLoading character node: {self.character_node}')

        if not self.apex_input or not self.apex_output:
            self._init_apex()

        houdini_lib.graph.update_apex_graph(self.edit_graph_instance, self.apex)


class HoudiniFkRig(HoudiniUtilRig):

    def _get_control_name(self, joint, sub=False):

        use_joint_name = self.rig.attr.get('use_joint_name')
        joint_description = None

        if use_joint_name:
            joint_description = self.get_joint_description(joint)

        control_name = self.get_control_name(joint_description, sub)
        control_name = self._inc_control_name(control_name, not sub)

        return control_name

    def _build_control(self, control_name, matrix, offset):

        transform = self.sub_apex.addNode(control_name, 'TransformObject')
        self.sub_apex.setNodePosition(transform, hou.Vector3(4 + offset, -2 - offset, 0))

        parms = self.sub_apex.getNodeParms(transform)
        parms['restlocal'] = matrix
        self.sub_apex.setNodeParms(transform, parms)

        transform_t_in = self.sub_apex.getPort(transform, 't[in]')
        transform_r_in = self.sub_apex.getPort(transform, 'r[in]')
        transform_s_in = self.sub_apex.getPort(transform, 's[in]')

        sub_input_t = self.sub_apex.addGraphInput(self.sub_input, 'control_%s_t' % control_name)
        sub_input_r = self.sub_apex.addGraphInput(self.sub_input, 'control_%s_r' % control_name)
        sub_input_s = self.sub_apex.addGraphInput(self.sub_input, 'control_%s_s' % control_name)

        self.sub_apex.addWire(sub_input_t, transform_t_in)
        self.sub_apex.addWire(sub_input_r, transform_r_in)
        self.sub_apex.addWire(sub_input_s, transform_s_in)

        return transform

    def _build_control_shape(self, control_name, transform, offset, scale_offset=1, sub=False):

        shape = self.sub_apex.addNode(f'shape_{control_name}', 'rig::ControlShape')
        self.sub_apex.setNodePosition(shape, hou.Vector3(4 + offset, -5 - offset, 0))

        shape_name = self.rig.attr.get('shape')
        shape_name = 'circle_wires'

        transform_xform = self.sub_apex.getPort(transform, 'xform[out]')
        control_shape_port = self.sub_apex.getPort(shape, 'control')
        self.sub_apex.addWire(transform_xform, control_shape_port)
        self.sub_apex.setNodeParm(shape, 'shapetype', shape_name)

        build_transform = self.sub_apex.addNode(f'shape_read_{control_name}', 'transform::Build')
        self.sub_apex.setNodePosition(build_transform, hou.Vector3(2 + offset, -6 - offset, 0))

        houdini_lib.graph.wire(self._attribute_node['shape_translate'], 'value', build_transform, 't', self.sub_apex)
        houdini_lib.graph.wire(self._attribute_node['shape_rotate'], 'value', build_transform, 'r', self.sub_apex)
        houdini_lib.graph.wire(self._attribute_node['shape_scale'], 'value', build_transform, 's', self.sub_apex)
        if sub:
            houdini_lib.graph.wire(self._attribute_node['sub_color'], 'value', shape, 'color', self.sub_apex)
        else:
            houdini_lib.graph.wire(self._attribute_node['color'], 'value', shape, 'color', self.sub_apex)

        build_transform_offset = self.sub_apex.addNode(f'shape_offset_{control_name}', 'transform::Build')
        self.sub_apex.setNodePosition(build_transform_offset, hou.Vector3(2 + offset, -8 - offset, 0))

        mult = self.sub_apex.addNode(f'shape_mult_{control_name}', 'Multiply<Matrix4>')
        self.sub_apex.setNodePosition(mult, hou.Vector3(4 + offset, -8 - offset, 0))

        houdini_lib.graph.wire(build_transform_offset, 'm', mult, 'a', self.sub_apex)
        houdini_lib.graph.wire(build_transform, 'm', mult, 'b', self.sub_apex)

        parms = self.sub_apex.getNodeParms(build_transform_offset)
        parms['r'] = hou.Vector3(90, 0, 0)
        parms['s'] = hou.Vector3(100 * scale_offset, 100 * scale_offset, 100 * scale_offset)

        self.sub_apex.setNodeParms(build_transform_offset, parms)

        houdini_lib.graph.wire(mult, 'result', shape, 'shapeoffset', self.sub_apex)

    def _build_sub_controls(self, joint, transform, matrix, sub_control_count, offset):

        sub_control_names = []
        sub_transform = None

        if sub_control_count > 0:

            for inc in range(0, sub_control_count):
                control_name = self._get_control_name(joint, sub=True)
                self.control_names.append(control_name)
                sub_control_names.append(control_name)

                weight = float(inc + 1) / sub_control_count
                scale = util_math.lerp(1.0, 0.75, weight)
                offset += 2

                sub_transform = self._build_control(control_name, matrix, offset)
                self._build_control_shape(control_name, sub_transform, offset, scale, sub=True)

                sub_parent_xform_in = self.sub_apex.getPort(sub_transform, 'parent[in]')
                sub_parent_localxform_in = self.sub_apex.getPort(sub_transform, 'parentlocal[in]')

                xform_out = self.sub_apex.getPort(transform, 'xform[out]')
                localxform_out = self.sub_apex.getPort(transform, 'localxform[out]')

                self.sub_apex.addWire(xform_out, sub_parent_xform_in)
                self.sub_apex.addWire(localxform_out, sub_parent_localxform_in)

                control_tracker.track(control_name, sub_transform, -1, matrix, hou.Matrix4(1))

        return sub_transform, sub_control_names, offset

    def _build_graph(self):

        joints = self.rig.attr.get('joints')

        if not joints:
            return

        hierarchy = self.rig.attr.get('hierarchy')
        rig_parent = self.rig.attr.get('parent')
        sub_control_count = self.rig.attr.get('sub_count')[0]

        get_parent = self.sub_apex.matchNodes('get_parent')[0]
        get_parent_value = self.sub_apex.getPort(get_parent, 'value')

        array_build_controls = self.sub_apex.matchNodes('array_build_controls')[0]
        build_controls_in = self.sub_apex.getPort(array_build_controls, 'values')

        offset = 0

        sub = False
        last_transform = None

        controls = []
        parent_matrix = None

        for joint in joints:

            joint_matrix = houdini_lib.graph.get_joint_matrix(joint)
            matrix = joint_matrix

            control_name = self._get_control_name(joint)

            self.control_names.append(control_name)
            controls.append(control_name)

            if rig_parent and not parent_matrix:
                rig_parent = rig_parent[-1]
                parent_data = control_tracker.get(rig_parent)
                if parent_data:
                    parent_matrix = parent_data.xform

            if parent_matrix:
                matrix = matrix * parent_matrix.inverted()

            transform = self._build_control(control_name, matrix, offset)
            self._build_control_shape(control_name, transform, offset)

            parent_xform_in = self.sub_apex.getPort(transform, 'parent[in]')
            parent_localxform_in = self.sub_apex.getPort(transform, 'parentlocal[in]')
            self.sub_apex.addWire(get_parent_value, parent_xform_in)

            sub_transform, sub_control_names, sub_offset = self._build_sub_controls(joint,
                                                                                    transform,
                                                                                    hou.Matrix4(1),
                                                                                    sub_control_count,
                                                                                    offset)

            offset += sub_offset

            out_transform = transform
            if sub_transform:
                out_transform = sub_transform

            if hierarchy:

                if last_transform:
                    last_xform_out = self.sub_apex.getPort(last_transform, 'xform[out]')
                    last_localxform_out = self.sub_apex.getPort(last_transform, 'localxform[out]')

                    self.sub_apex.addWire(last_xform_out, parent_xform_in)
                    self.sub_apex.addWire(last_localxform_out, parent_localxform_in)

                parent_matrix = joint_matrix
                last_transform = out_transform

            transform_xform = self.sub_apex.getPort(out_transform, 'xform[out]')
            joint_out = self.sub_apex.addGraphOutput(self.sub_output, joint)
            self.sub_apex.addWire(transform_xform, joint_out)

            sub_build_controls_in = self.sub_apex.addSubPort(build_controls_in, control_name)
            self.sub_apex.addWire(transform_xform, sub_build_controls_in)

            control_tracker.track(control_name, transform, -1, joint_matrix, matrix)

            offset += 2

        self.rig.attr.set('controls', controls)


class HoudiniWheelRig(HoudiniFkRig):
    pass


class HoudiniGetSubControls(HoudiniUtilRig):

    def _build_graph(self):

        controls = self.rig.attr.get('controls')

        control_value = self._attribute_node['controls']

        value_port = self.sub_apex.getPort(control_value, 'value')
        sub_controls_port = self.sub_apex.addGraphOutput(self.sub_output, 'sub_controls')
        self.sub_apex.addWire(value_port, sub_controls_port)

        self.rig.attr.set('sub_controls', controls)
