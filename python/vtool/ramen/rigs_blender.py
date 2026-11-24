import math

from vtool import util
from . import rigs
from .. import blender_lib

in_blender = util.in_blender

if in_blender:
    import bpy


def get_or_create_circle_widget(name="WGT_fk_circle", radius=0.5, segments=24):
    """Creates (or reuses) a clean edge-only circle mesh object for bone custom shapes."""
    obj = bpy.data.objects.get(name)
    if obj is not None:
        return obj

    # Build circle vertices in the XZ plane (wraps around the bone's Y-axis)
    verts = []
    edges = []
    for i in range(segments):
        angle = (2.0 * math.pi * i) / segments
        verts.append((math.cos(angle) * radius, 0.0, math.sin(angle) * radius))
        edges.append((i, (i + 1) % segments))

    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, edges, [])
    mesh.update()

    obj = bpy.data.objects.new(name, mesh)

    # Put widget in a dedicated hidden collection so it doesn't clutter the scene
    wgt_col = bpy.data.collections.get("Widgets")
    if wgt_col is None:
        wgt_col = bpy.data.collections.new("Widgets")
        bpy.context.scene.collection.children.link(wgt_col)
        wgt_col.hide_viewport = True
        wgt_col.hide_render = True

    wgt_col.objects.link(obj)
    return obj


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

        joint_objects = blender_lib.util.get_bone_objects(joints)

        if not joint_objects:
            return

        armature_obj = joint_objects[0][0]

        arm_data = armature_obj.data

        # Ensure armature is active and switch to EDIT mode
        bpy.context.view_layer.objects.active = armature_obj
        prev_mode = armature_obj.mode
        bpy.ops.object.mode_set(mode='EDIT')

        edit_bones = arm_data.edit_bones
        fk_pairs = []  # (src_bone_name, fk_bone_name)
        prev_fk_edit_bone = None

        prefix = 'fk'
        collection_name = 'Fk Controls'
        shape_obj = get_or_create_circle_widget()
        use_copy_transforms = True

        for src_name in joints:
            src_eb = edit_bones.get(src_name)
            if src_eb is None:
                continue

            base_name = src_name
            fk_name = f"{prefix}{base_name}"

            # Remove existing bone if regenerating
            if fk_name in edit_bones:
                edit_bones.remove(edit_bones[fk_name])

            fk_eb = edit_bones.new(fk_name)
            fk_eb.head = src_eb.head.copy()
            fk_eb.tail = src_eb.tail.copy()
            fk_eb.roll = src_eb.roll
            fk_eb.use_deform = False
            fk_eb.use_connect = False

            # Parent to previous FK bone in chain, or mirror source bone's parent
            if prev_fk_edit_bone is not None:
                fk_eb.parent = prev_fk_edit_bone
            elif src_eb.parent is not None:
                fk_eb.parent = src_eb.parent

            fk_pairs.append((src_name, fk_eb.name))
            prev_fk_edit_bone = fk_eb

        # Switch to POSE mode to assign constraints, custom shapes, and collections
        bpy.ops.object.mode_set(mode='POSE')
        pose_bones = armature_obj.pose.bones

        # Get or create Bone Collection (Blender 4.0+)
        fk_collection = None
        if hasattr(arm_data, "collections"):
            fk_collection = arm_data.collections.get(collection_name) or arm_data.collections.new(collection_name)
            arm_data.show_bone_custom_shapes = True

        created_fk_names = []

        for src_name, fk_name in fk_pairs:
            src_pb = pose_bones[src_name]
            fk_pb = pose_bones[fk_name]
            created_fk_names.append(fk_name)

            # Assign custom shape if provided
            if shape_obj is not None:
                fk_pb.custom_shape = shape_obj

            # Assign to Bone Collection
            if fk_collection is not None:
                fk_collection.assign(fk_pb.bone)

            # Constrain deform bone to follow FK control bone
            con_type = 'COPY_TRANSFORMS' if use_copy_transforms else 'COPY_ROTATION'
            con = src_pb.constraints.new(type=con_type)
            con.name = f"FK_{con_type}"
            con.target = armature_obj
            con.subtarget = fk_name

        # Restore original mode
        bpy.ops.object.mode_set(mode=prev_mode)

        for obj in bpy.data.objects:
            if obj.name.startswith("WGT-"):  # Adjust prefix to match your widget naming
                obj.hide_select = False
                obj.hide_viewport = False

        # Also ensure every collection in the scene allows selection
        for col in bpy.data.collections:
            col.hide_select = False
            col.hide_viewport = False

        return created_fk_names
