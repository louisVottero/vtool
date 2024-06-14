from . import rigs
from .. import houdini_lib
from vtool import util


class HoudiniUtilRig(rigs.PlatformUtilRig):

    def __init__(self):
        super(HoudiniUtilRig, self).__init__()

        self.character_node = None

    def load(self):
        super(HoudiniUtilRig, self).load()

        util.show('\tLoading character node: %s' % houdini_lib.graph.character_import)
        self.character_node = houdini_lib.graph.character_import

        houdini_lib.graph.build_edit_graph(self.character_node)


class HoudiniFkRig(HoudiniUtilRig):
    pass
