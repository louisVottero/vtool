from . import rigs
from .. import houdini_lib
from vtool import util

if util.in_houdini:
    import hou
    import apex


class HoudiniUtilRig(rigs.PlatformUtilRig):

    def __init__(self):
        super(HoudiniUtilRig, self).__init__()

        self.character_node = None
        self.graph = None
        self.apex = None
        self.apex_input = None
        self.apex_output = None
        self.sub_apex = None

    def _get_sub_apex_name(self):
        rig_name = 'vetala_%s' % self.__class__.__name__
        rig_name = rig_name.replace('Houdini', '')

        return rig_name

    def _init_apex(self):
        sub_graph, apex_graph = houdini_lib.graph.build_character_sub_graph_for_apex(self.character_node, 'ramen_apex')

        houdini_lib.graph.set_current_network(sub_graph)
        houdini_lib.graph.set_current_apex(apex_graph)

        self.graph = sub_graph
        self.edit_graph_node = apex_graph

        self.apex = houdini_lib.graph.get_apex_graph(self.edit_graph_node)

        self.apex_input, self.apex_output = houdini_lib.graph.initialize_input_output(self.apex)

        houdini_lib.graph.add_bone_deform(self.apex)

    def _init_sub_apex(self):
        sub_apex_name = self._get_sub_apex_name()

        self.sub_apex = apex.Graph()

        self.sub_apex_input, self.sub_apex_output = houdini_lib.graph.initialize_input_output(self.sub_apex)

        uuid_value = self.sub_apex.addNode('UUID_value', 'Value<String>')
        self.sub_apex.setNodePosition(uuid_value, hou.Vector3(2, 2, 0))

        uuid_value_port = self.sub_apex.getPort(uuid_value, 'parm')
        uuid_in = self.sub_apex.addGraphInput(0, 'uuid')
        uuid = self.rig.uuid

        self.sub_apex.addWire(uuid_in, uuid_value_port)

        parm_dict = self.sub_apex.getParmDict()

        self.sub_apex_node = self.apex.addSubnet(sub_apex_name, self.sub_apex)

        self.apex.setNodePosition(self.sub_apex_node, hou.Vector3(5, 0, 0))

        node_values = apex.Dict()
        node_values['uuid'] = uuid

        self.apex.setNodeParms(self.sub_apex_node, node_values)

    def load(self):
        super(HoudiniUtilRig, self).load()

        util.show('\tLoading character node: %s' % houdini_lib.graph.character_import)
        self.character_node = houdini_lib.graph.character_import

        if not self.apex_input or not self.apex_output:
            self._init_apex()

        if not self.sub_apex:
            self._init_sub_apex()

        houdini_lib.graph.update_apex_graph(self.edit_graph_node, self.apex)


class HoudiniFkRig(HoudiniUtilRig):
    pass
