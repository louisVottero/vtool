from . import rigs
from .. import houdini_lib


class HoudiniUtilRig(rigs.PlatformUtilRig):

    def __init__(self):
        super(HoudiniUtilRig, self).__init__()

        self.character_node = None

    def load(self):
        super(HoudiniUtilRig, self).load()

        self.character_node = houdini_lib.graph.character_import


class HoudiniFkRig(HoudiniUtilRig):
    pass
