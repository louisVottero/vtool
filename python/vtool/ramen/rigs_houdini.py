from . import rigs
from .. import houdini_lib
from vtool import util


class HoudiniUtilRig(rigs.PlatformUtilRig):

    def __init__(self):
        super(HoudiniUtilRig, self).__init__()

        self.character_node = None
        self.graph = None
        self.apex = None

    def _init_apex(self):
        sub_graph, apex_graph = houdini_lib.graph.build_character_sub_graph_for_apex(self.character_node, 'ramen_apex')

        self.graph = sub_graph
        self.edit_graph_node = apex_graph

        self.apex = houdini_lib.graph.get_live_graph(self.edit_graph_node)

        houdini_lib.graph.initialize_input_output(self.apex)
        houdini_lib.graph.update_live_graph(self.edit_graph_node, self.apex)

    def load(self):
        super(HoudiniUtilRig, self).load()

        util.show('\tLoading character node: %s' % houdini_lib.graph.character_import)
        self.character_node = houdini_lib.graph.character_import

        self._init_apex()


class HoudiniFkRig(HoudiniUtilRig):
    pass
