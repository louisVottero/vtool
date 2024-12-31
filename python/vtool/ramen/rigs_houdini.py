from . import rigs
from .. import houdini_lib
from vtool import util

if util.in_houdini:
    import hou


class HoudiniUtilRig(rigs.PlatformUtilRig):

    def __init__(self):
        super(HoudiniUtilRig, self).__init__()

        self.character_node = None
        self.graph = None
        self.apex = None
        self.apex_input = None
        self.apex_output = None
        self.sub_apex = None

    def _init_apex(self):
        sub_graph, apex_graph = houdini_lib.graph.build_character_sub_graph_for_apex(self.character_node, 'ramen_apex')

        self.graph = sub_graph
        self.edit_graph_node = apex_graph

        self.apex = houdini_lib.graph.get_live_graph(self.edit_graph_node)

        self.apex_input, self.apex_output = houdini_lib.graph.initialize_input_output(self.apex)

    def _init_sub_apex(self):

        self.sub_apex = self.apex.addNode('ramen_rig', '__subnet__')
        self.apex.setNodePosition(self.sub_apex, hou.Vector3(5, 0, 0))

    def load(self):
        super(HoudiniUtilRig, self).load()

        util.show('\tLoading character node: %s' % houdini_lib.graph.character_import)
        self.character_node = houdini_lib.graph.character_import

        if not self.apex_input or not self.apex_output:
            self._init_apex()

        if not self.sub_apex:
            self._init_sub_apex()

        houdini_lib.graph.update_live_graph(self.edit_graph_node, self.apex)


class HoudiniFkRig(HoudiniUtilRig):
    pass
