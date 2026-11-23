from vtool import util
from . import rigs

in_blender = util.in_blender

if in_blender:
    import bpy


class BlenderUtilRig(rigs.PlatformUtilRig):

    def build(self):
        super().build()

        if not in_blender:
            return

        self._build_rig()

    def _build_rig(self):
        return


class BlenderFkRig(BlenderUtilRig):

    def _build_rig(self):
        print('blender fk rig')
        joints = self.rig.attr.get('joints')

        if not joints:
            return
        use_joint_name = self.rig.attr.get('use_joint_name')
        hierarchy = self.rig.attr.get('hierarchy')

        print(joints)
