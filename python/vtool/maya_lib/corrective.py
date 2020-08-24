# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

import string

import vtool.util
from vtool.maya_lib import anim

if vtool.util.is_in_maya():
    import maya.cmds as cmds
    #import util
import core
import blendshape
import attr
import space
import geo
import deform
import shade
import rigs_util

def get_pose_instance(pose_name, pose_group = 'pose_gr'):
    """
    Get a pose instance from the pose name.
    
    Args:
        pose_name (str): The name of a pose.
    
    Returns:
        object: The instance of the pose at the pose type.
    """
    
    if not cmds.objExists(pose_name):
        return
    
    if cmds.objExists('%s.type' % pose_name):
        pose_type = cmds.getAttr('%s.type' % pose_name)
        
    if not cmds.objExists('%s.type' % pose_name):
        pose_type = 'cone'

    pose = corrective_type[pose_type]()
    pose.set_pose_group(pose_group)
    pose.set_pose(pose_name)
    
    return pose
    
class PoseManager(object):
    """
    Convenience for working with poses.
    """
    def __init__(self):
        self.poses = []
        self._namespace = None
        
        self.pose_group = 'pose_gr'
        self.detached_attributes = {}
        self.sub_detached_dict = {}

    def _check_pose_group(self):
        
        if not self.pose_group:
            return
        
        if not cmds.objExists(self.pose_group):
            
            selection = cmds.ls(sl = True)
            
            self.pose_group = cmds.group(em = True, n = self.pose_group)
        
            data = rigs_util.StoreControlData(self.pose_group)
            data.set_data()
            
            if selection:
                cmds.select(selection)
    
    def is_pose(self, name):
        """
        Check if name matches the name of a pose.
        
        Args:
            name (str): Check if the node at name is a pose.
            
        Returns:
            bool
        """
        if PoseBase().is_a_pose(name):
            return True
        
        return False
    
    def is_pose_mesh_in_sculpt(self, index, pose_name):
        
        pose = self.get_pose_instance(pose_name)
        
        if hasattr(pose, 'is_mesh_visibile'):
            pose.is_mesh_in_sculpt(index)
        
        
    def get_pose_instance(self, pose_name):
        """
        Get the instance of a pose. 
        
        Args:
            pose_name (str): The name of a pose.
            
        Returns:
            object: The instance of the pose at the pose type.
        """
        
        namespace = core.get_namespace(self.pose_group)
        
        if namespace:
            
            
            
            if not pose_name.startswith(namespace):
                pose_name = '%s:%s' % (namespace, pose_name)
        
        pose = get_pose_instance(pose_name, self.pose_group)
        
        return pose
                        
    def get_poses(self, all_descendents = False):
        """
        Get the poses under the pose_gr
        
        Returns:
            list: The names of poses.
        """
        self._check_pose_group()
        
        if not self.pose_group:
            return
        namespace = core.get_namespace(self.pose_group)
        
        relatives = cmds.listRelatives(self.pose_group, ad = all_descendents)
        
        poses = []
        
        if not relatives:
            return
        
        end_poses = []
        
        for relative in relatives:
            if self.is_pose(relative):
                
                #this is because in some cases cmds.listRelatives was not returning namespace.  Possibly a refresh issue.
                if namespace: 
                    if not relative.startswith(namespace):
                        relative = '%s:%s' % (namespace, relative)
                
                pose_type = cmds.getAttr('%s.type' % relative)
                
                if pose_type == 'combo':
                    end_poses.append(relative)
                else:
                    poses.append(relative)
        
        if end_poses:            
            poses = poses + end_poses
        
        return poses
        
    def get_pose_control(self, name):
        """
        Get the control of a pose.
        
        Args:
            name (str): The name of a pose.
            
        Returns:
            str: The name of the pose.
        """
        pose = self.get_pose_instance(name)
        
        control = pose.pose_control
        
        return control
    
    def get_pose_type(self, name):
        
        pose = self.get_pose_instance(name)
        pose_type = pose.get_type()
        
        return pose_type
    
    def set_namespace(self, namespace):
        self._namespace = namespace
        
        pose_group = '%s:%s' % (namespace, 'pose_gr')
        
        if not cmds.objExists(pose_group):
            self.pose_group = cmds.rename( self.pose_group, pose_group )
        else:
            self.pose_group = pose_group
        
        #self.pose_group = cmds.rename( self.pose_group, '%s:%s' % (namespace, self.pose_group))
        
        rels = cmds.listRelatives(self.pose_group, ad = True)
        
        for rel in rels:
            
            nicename = core.get_basename(rel, remove_namespace = True)
            
            pose_name = '%s:%s' % (self._namespace, nicename)
            
            if not cmds.objExists(pose_name):
            
                cmds.rename(rel, '%s:%s' % (self._namespace, nicename))

        #cmds.refresh()
    
    def set_pose_group(self, pose_gr_name):
        """
        Set the pose group to work with.
        
        Args:
            pose_gr_name (str): The name of a pose group.
        """
        self.pose_group = pose_gr_name
    
    def set_weights_to_zero(self):
        """
        Set all poses in the pose_gr to zero.
        """

        poses = self.get_poses()
        
        if not poses:
            return
        
        for pose_name in poses:
                
            input_value = attr.get_attribute_input('%s.weight' % pose_name)
            if not input_value:
                if cmds.objExists('%s.weight' % pose_name):
                    cmds.setAttr('%s.weight' % pose_name, 0)
    
    
    def set_default_pose(self):
        """
        Set the default control pose. This is the control pose the rig should revert to by default.
        """
        self._check_pose_group()
        
        store = rigs_util.StoreControlData(self.pose_group)
        store.set_data()
        
    def set_pose_to_default(self):
        """
        Set the control pose to the default pose.
        This is handy for resetting control positions after going to a pose.
        """
        self._check_pose_group()
        
        store = rigs_util.StoreControlData(self.pose_group)
        if self._namespace:
            store.set_namesapce(self._namespace)
        store.eval_data()
        
        self.set_weights_to_zero()
        
    
    def set_pose(self, pose):
        """
        Set the control pose to the current pose.
        This is handy for returning a character to the pose it was sculpted in.
        
        Args:
            pose (str): The name of a pose.
        """
        pose_instance = self.get_pose_instance(pose)
        
        if pose_instance:
            pose_instance.goto_pose()
        else:
            vtool.util.warning('%s not found' % pose)
        
    def set_pose_data(self, pose):
        """
        Set the pose data from the control values. 
        This is handy for making sure a character can get back into pose before sculpting it.
        
        Args:
            pose (str): The name of a pose.
        """
        store = rigs_util.StoreControlData(pose)
        store.set_data()
        
    def set_poses(self, pose_list):
        """
        Not in use.  This was the beginning of a combo system.
        It proved difficult to extrapulate a combo pose from multiple poses.
        
        Args:
            pose_list (list): A list of pose names.
        """
        data_list = []
        
        for pose_name in pose_list:
            
            store = rigs_util.StoreControlData(pose_name)

            data_list.append( store.eval_data(True) )
            
        store = rigs_util.StoreControlData().eval_multi_transform_data(data_list)
    
    def create_pose(self, pose_type, name = None):
        """
        Create a pose.
        
        Args:
            pose_type (str): The name of a pose type.
            name (str): The name for the pose.
            
        Returns:
            str: The name of the new pose.
        """
        pose = None
        
        self._check_pose_group()
        
        if pose_type == 'cone':
            pose = self.create_cone_pose(name)
        if pose_type == 'no reader':
            pose = self.create_no_reader_pose(name)
        if pose_type == 'combo':
            pose = self.create_combo_pose(name)
        if pose_type == 'timeline':
            pose = self.create_timeline_pose(name)
        if pose_type == 'group':
            pose = self.create_group_pose(name)
            
        return pose
            
    @core.undo_chunk
    def create_cone_pose(self, name = None):
        """
        Create a cone pose. 
        
        Args:
            name (str): The name for the pose.
            
        Returns:
            str: The name of the pose.
        """
        selection = cmds.ls(sl = True, l = True)
        
        if not selection:
            return
        
        if not cmds.nodeType(selection[0]) == 'joint' or not len(selection):
            return
        
        if not name:
            joint = selection[0].split('|')
            joint = joint[-1]
            
            name = 'pose_%s' % joint
        
        pose = PoseCone(selection[0], name)
        pose.set_pose_group(self.pose_group)
        pose_control = pose.create()
        
        self.pose_control = pose_control
        
        return pose_control

    @core.undo_chunk
    def create_no_reader_pose(self, name = None):
        """
        Create a no reader pose. 
        
        Args:
            name (str): The name for the pose.
            
        Returns:
            str: The name of the pose.
        """
        if not name:
            name = core.inc_name('pose_no_reader_1')
        
        pose = PoseNoReader(name)
        pose.set_pose_group(self.pose_group)
        pose_control = pose.create()
        
        self.pose_control = pose_control
        
        return pose_control
    
    def create_combo_pose(self, name = None):
        """
        Create a combo pose. 
        
        Args:
            name (str): The name for the pose.
            
        Returns:
            str: The name of the pose.
        """
        
        if not name:
            name = core.inc_name('pose_combo_1')
        
        pose = PoseCombo(name)
        pose.set_pose_group(self.pose_group)
        pose_control = pose.create()
        
        self.pose_control = pose_control
        
        return pose_control
    
    @core.undo_chunk
    def create_timeline_pose(self, name = None):
        """
        Create a no timeline pose. 
        
        Args:
            name (str): The name for the pose.
            
        Returns:
            str: The name of the pose.
        """
        current_time = str(cmds.currentTime(q = True))
        time_number_strings = current_time.split('.')
        
        seconds_name = time_number_strings[0]
        sub_seconds_name = time_number_strings[1]
        
        time_name = seconds_name.rjust(4, '0') + '_' + sub_seconds_name.rjust(2, '0')
        
        if not name:
            name = core.inc_name('pose_timeline_%s_1' % time_name)
        
        pose = PoseTimeline(name)
        pose.set_pose_group(self.pose_group)
        pose_control = pose.create()
        
        self.pose_control = pose_control
        
        return pose_control
    
    def create_group_pose(self, name = None):
        """
        Create a group pose. 
        
        Args:
            name (str): The name for the pose.
            
        Returns:
            str: The name of the pose.
        """
        if not name:
            name = core.inc_name('pose_group_1')
        
        pose = PoseGroup(name)
        pose.set_pose_group(self.pose_group)
        pose_control = pose.create()
        
        self.pose_control = pose_control
        
        return pose_control
    
    @core.undo_chunk
    def reset_pose(self, pose_name):
        
        pose = self.get_pose_instance(pose_name)
        pose.reset_target_meshes()
        
    @core.undo_chunk
    def update_pose_meshes(self, pose_name, only_not_in_sculpt = False):
        
        pose = self.get_pose_instance(pose_name)
        pose.update_target_meshes(only_not_in_sculpt)
        
    @core.undo_chunk
    def update_pose(self, pose_name):
        
        control = self.get_pose_control(pose_name)
        self.set_pose_data(control)
        
        instance = self.get_pose_instance(pose_name)
        
        if hasattr(instance, 'rematch_cone_to_joint'):
            instance.goto_pose()
            instance.rematch_cone_to_joint()
            
    @core.undo_chunk
    def revert_pose_vertex(self, pose_name):
        
        instance = self.get_pose_instance(pose_name)
        instance.revert_selected_verts()
    
    @core.undo_chunk
    def rename_pose(self, pose_name, new_name):
        pose = self.get_pose_instance(pose_name)
        return pose.rename(new_name)
    
    @core.undo_chunk
    def add_mesh_to_pose(self, pose_name, meshes = None):
        
        #bandaid fix. Seems like this should be more proceedural instead of just naming the group
        if cmds.objExists('pose_gr'):
            core.add_to_isolate_select('pose_gr')
        
        selection = None

        if not meshes == None:
            selection = cmds.ls(sl = True, l = True)
        if meshes:
            selection = meshes
        
        pose = self.get_pose_instance(pose_name)
        
        added_meshes = []
        
        if selection:
            for sel in selection:
                
                shape = geo.get_mesh_shape(sel)
                
                if shape:
                    pose.add_mesh(sel)
                    added_meshes.append(sel)
                    
        return added_meshes
    
    def visibility_off(self, pose_name):
        """
        Change the visibility of the pose meshes.
        
        Args:
            pose_name (str): The name of a pose.
        """
        pose = self.get_pose_instance(pose_name)
        
        pose_type = cmds.getAttr('%s.type' % pose_name)
        
        if pose_type == 'group':
            return
        
        count = pose.get_mesh_count()
        
        for inc in xrange(0, count):
            mesh = pose.get_mesh(inc)
            pose.visibility_off(mesh, view_only = True)
        
        
    def toggle_visibility(self, target_mesh, pose_name, view_only = False):
        """
        Toggle the visibility of the sculpt mesh.
        
        Args:
            target_mesh (str): The name of a mesh affected by the pose.
            pose_name (str): The name of a pose.
            view_only (bool): Wether to calculate its delta when turning visibility off, or just turn visibility off.
        """
        
        
        if target_mesh == None:
            return
        
        pose = self.get_pose_instance(pose_name)
        
        index = pose.get_target_mesh_index(target_mesh)
        
        
        
        pose.toggle_vis(index, view_only)
    
    @core.undo_chunk
    def delete_pose(self, name):
        """
        Delete a pose by name.
        
        Args:
            name (str): The name of a pose.
        """
        pose = self.get_pose_instance(name)
        pose.delete()
        
    def detach_poses(self):
        """
        Detach poses from the pose_gr and the rig.
        
        """
        poses = self.get_poses()
        
        detached_attributes = {}
        
        for pose_name in poses:
            
            pose = self.get_pose_instance(pose_name)
            detached = pose.detach()
            
            if detached:
                detached_attributes[pose_name] = detached
                
                if pose.sub_detach_dict:
                    self.sub_detached_dict[pose_name] = pose.sub_detach_dict 
        
        self.detached_attributes = detached_attributes
        
    def attach_poses(self, poses = None, namespace = None):
        """
        Attach poses to the pose_gr and the rig.
        """
        
        if not poses:
            poses = self.get_poses()
        
        for pose_name in poses:
            
            pose = self.get_pose_instance(pose_name)
            
            detached = None
            
            if self.detached_attributes:
                if self.detached_attributes.has_key(pose_name):
                    detached = self.detached_attributes[pose_name]
            
            pose.attach(detached)
            
            for pose_name in self.sub_detached_dict:
                sub_poses = self.sub_detached_dict[pose_name]
                
                for key in sub_poses:
                    pose = key
                    attributes = sub_poses[key]
                    
                    sub_pose = self.get_pose_instance(pose)
                    
                    sub_pose.attach(attributes)
        
        self.set_pose_to_default()
            
    def create_pose_blends(self, poses = None):
        """
        Refresh the deltas on poses. By default do it to all poses under the pose_gr.
        
        Args:
            poses (args): The names of poses.
        """
        if not poses:
            poses = self.get_poses()
        if poses:
            vtool.util.convert_to_sequence(poses)
        
        count = len(poses)

        progress = core.ProgressBar('adding poses ... ', count)
        
        for inc in xrange(count):
            
            pose_name = poses[inc]
            
            if vtool.util.break_signaled():
                break
                                
            if progress.break_signaled():
                break
            
            progress.status('adding pose %s' % pose_name)

            
            
            pose = self.get_pose_instance(pose_name)
            
            pose.set_pose(pose_name)
            pose.create_all_blends()
            
            pose_type = '%s.type' % pose.pose_control
            

                
            if not cmds.objExists(pose_type):
                #this is a patch fix to work with really old poses
                #old poses were only of type cone
                cmds.addAttr(pose.pose_control, ln = 'type', dt = 'string')
                cmds.setAttr('%s.type' % pose.pose_control, 'cone', type = 'string')
                pose_type = 'cone'

            if cmds.objExists(pose_type):
                pose_type = cmds.getAttr(pose_type)
            
            if pose_type == 'no reader':
                pose.set_weight(0)
            
            

            
            progress.inc()
            
            
        progress.end()
    
    def mirror_pose(self, name):
        """
        Mirror a pose to a corresponding R side pose.
        
        For example
            If pose name = pose_arm_L, there must be a corresponding pose_arm_R.
            The pose at pose_arm_R must be a mirrored pose of pose_arm_L.
            
        Args:
            name (str): The name of a left side pose.
        
        """
        pose = self.get_pose_instance(name)
        mirror = None
        if hasattr(pose, 'mirror'):
            mirror = pose.mirror()
        
        return mirror
    
    def mirror_all(self):
        
        poses = self.get_poses(all_descendents = True)
        
        if not poses:
            return
        
        found = []
        
        bar = core.ProgressBar('Mirror poses', len(poses))
        
        for pose in poses:
            
            if pose in found:
                continue 
            
            other = space.find_transform_right_side(pose, check_if_exists=False)
            if other:
                bar.status('Mirror pose: %s' % pose)
                vtool.util.show('Mirror pose: %s' % pose )
                mirror = self.mirror_pose(pose)
                cmds.refresh()
                if mirror:
                    found.append(mirror)
            
            if bar.break_signaled():
                break
            bar.next()
            
        bar.end()
        
        return found
    
    def reconnect_all(self):
        poses = self.get_poses(all_descendents = True)
        
        if not poses:
            return
        
        found = []
        
        for pose in poses:
            pose_inst = self.get_pose_instance(pose)
            
            if hasattr(pose_inst, 'reconnect_blends'):
                worked = pose_inst.reconnect_blends()
                if worked:
                    found.append(pose)
        
        return found
                
class PoseGroup(object):
    """
    This pose is a group to parent poses under.
    """
    def __init__(self, description = 'pose'):
        
        self.pose_control = None

        if description:
            description = description.replace(' ', '_')
            
        self.description = description
        
        self.pose_gr = 'pose_gr'
        self.create_blends_went_to_pose = False
        
        self.sub_detach_dict = {}
    
    def _pose_type(self):
        return 'group'    

    def _create_top_group(self):
        top_group = self.pose_gr
                
        if not cmds.objExists(top_group):
            top_group = cmds.group(em = True, name = top_group)
            

        return top_group

    def _set_description(self, description):    
        cmds.setAttr('%s.description' % self.pose_control, description, type = 'string' )
        self.description = description
        
    def _get_name(self):
        return core.inc_name(self.description) 
    
    def _get_sub_poses(self):
        manager = PoseManager()
        manager.set_pose_group(self.pose_control)
        children = manager.get_poses()
        
        return children
    
    def _create_pose_control(self):
        
        pose_control = cmds.group(em = True, n = self._get_name())
        attr.hide_keyable_attributes(pose_control)
        
        self.pose_control = pose_control
        
        self._create_attributes(pose_control)
        
        return pose_control
        
    def _create_attributes(self, pose_control):
        title = attr.MayaEnumVariable('POSE')
        title.create(pose_control)  
        
        pose_type = attr.MayaStringVariable('type')
        pose_type.set_value(self._pose_type())
        pose_type.set_locked(True)
        pose_type.create(pose_control)
        
        cmds.addAttr(pose_control, ln = 'description', dt = 'string')
        cmds.setAttr('%s.description' % pose_control, self.description, type = 'string')
    
    #--- pose
    def is_a_pose(self, node):
        """
        Check if the named node is a pose.
        
        Args:
            node (str): The name of a node.
        """
        if cmds.objExists('%s.POSE' % node ):    
            return True
        
        return False
    
    def has_a_mesh(self):
        return False
    
    def get_type(self):
        
        pose_type = None
        
        if cmds.objExists('%s.type' % self.pose_control):
        
            pose_type = cmds.getAttr('%s.type' % self.pose_control)
            
        return pose_type

    def set_pose_group(self, pose_group_name):
        """
        Set the pose group to work with.
        The pose group is pose_gr by default and is setu automatically.
        
        Args:
            pose_group_name (str): The name of a pose group.
        """
        self.pose_gr = pose_group_name
    
    def set_pose(self, pose_name):
        """
        Set the pose that the instance should work on.
        
        Args:
            pose_name (str): The name of a pose.
        """
        
        if not pose_name:
            return
        
        if not cmds.objExists(pose_name):
            self.description = pose_name
        
        if not cmds.objExists('%s.description' % pose_name):
            return
        
        self.description = cmds.getAttr('%s.description' % pose_name)
        self.pose_control = pose_name
        
    def goto_pose(self):
        """
        Goto the pose.  
        This is important so the character can back into the same pose it was sculpted at.
        """
        
        if self.pose_control:
        
            store = rigs_util.StoreControlData(self.pose_control)
            namespace = core.get_namespace(self.pose_control)
            store.set_namesapce(namespace)
            store.eval_data()
            
            self.create_blends_went_to_pose = True
            
            
    def rename(self, description):
        """
        Rename the pose.
        
        Args:
            description (str): The new name for the pose.
            
        Returns:
            str: The new name.
        """
        description = vtool.util.clean_name_string(description)
        description = core.inc_name(description)
        self._set_description(description)
            
        self.pose_control = cmds.rename(self.pose_control, self._get_name())
           
        return self.pose_control
            
    def create(self):
        """
        Create the pose.
        
        Returns:
            str: The new name.
        """
        #top_group = self._create_top_group()
        
        pose_control = self._create_pose_control()
        self.pose_control = pose_control
        
        cmds.parent(pose_control, self.pose_gr)
        
        store = rigs_util.StoreControlData(pose_control)
        store.set_data()
        
        return pose_control
    
    def create_all_blends(self):
        """
        Create all the blends in a pose. 
        This refreshes the deltas.
        """
        self.create_sub_poses()
        
    def create_blend(self, mesh_index = None, goto_pose = True, sub_poses = True):
        """
        Create the blend. This will refresh the delta.
        
        Args:
            mesh_index (int): Work with the mesh at the index. Pose needs to be affecting at least one mesh.
            goto_pose (bool): Wether to go to the pose. 
            sub_poses (bool): Wether to create blend for sub poses as well.
        """
        if goto_pose:
            self.goto_pose()
        
        if sub_poses:
            self.create_sub_poses()
            
    def create_sub_poses(self, mesh = None):
        """
        Create the blends and refresh deltas for the sub poses in a pose.
        
        Args:
            mesh (int): Work with the mesh at the index. Pose needs to be affecting at least one mesh.
        """
        children = self._get_sub_poses()
        
        if children:
            
            for child in children:
                
                child_instance = get_pose_instance(child)
                
                if mesh:
                    sub_mesh_index = self.get_target_mesh_index(mesh)
                    child_instance.create_blend(sub_mesh_index, goto_pose = True)
                    
                if not mesh:
                    
                    sub_meshes = child_instance.get_target_meshes()
                    for sub_mesh in sub_meshes:
                        index = child_instance.get_target_mesh_index(sub_mesh)
                        child_instance.create_blend(index, goto_pose = True)
            
                if mesh:
                    if hasattr(child_instance, 'get_target_mesh_index'):
                        mesh_index = child_instance.get_target_mesh_index(mesh)
                        self.create_blend(mesh_index, True, False)
    
    def delete(self):
        """
        Delete the pose.
        """
        cmds.delete(self.pose_control)
        
    def select(self):
        """
        Select the pose.
        """
        cmds.select(self.pose_control)
        
        store = rigs_util.StoreControlData(self.pose_control)
        store.eval_data()
        
    def attach(self, outputs = None):
        """
        Attach the pose. 
        Attaching and detaching help with export/import.
        
        Args:
            outputs (list) 
        """
        
        
        
        self.attach_sub_poses(outputs)
    
    def detach(self):
        """
        Detach the pose. 
        Attaching and detaching help with export/import.
        """
        detach_dict = self.detach_sub_poses()
        
        if detach_dict:
            self.sub_detach_dict = detach_dict
        
        
        
        return detach_dict
        
    def detach_sub_poses(self):
        """
        Detach the sub poses.
        Attaching and detaching help with export/import.
        """
        children = self._get_sub_poses()
        
        if not children:
            return
        
        detach_dict = {}
        
        for child in children:    
            child_instance= get_pose_instance(child)
            detached = child_instance.detach()
            
            detach_dict[child_instance.pose_control] = detached
            
        return detach_dict
    
    def attach_sub_poses(self, outputs):
        """
        Attach the sub poses.
        Attaching and detaching help with export/import.
        """
        children = self._get_sub_poses()
        
        if not children:
            return
        
        for child in children:
            
            detached = None
            
            if type(outputs) == dict:
                if outputs.has_key(child):
                    detached = outputs[child]
            
            child_instance= get_pose_instance(child)
            child_instance.attach(detached)
        
    def mirror(self):
        """
        Mirror the pose.
        """
        pass
        
class PoseBase(PoseGroup):
    """
    Base class for poses that sculpt meshes.
    """
    def __init__(self, description = 'pose'):
        super(PoseBase, self).__init__(description)
        
        self.scale = 1
        
        self.blend_input = None
        
        self.left_right = True
        self.pose_gr = 'pose_gr'
        
        self.disconnected_attributes = None
    
    def _pose_type(self):
        return 'base'
        
    def _refresh_meshes(self):
        
        meshes = self._get_corrective_meshes()
        
        for mesh in meshes:
            target_mesh = self._get_mesh_target(mesh)
            
            if not target_mesh or not cmds.objExists(target_mesh):
                continue
            
            if target_mesh:
                
                cmds.setAttr('%s.inheritsTransform' % mesh, 1)
                attr.unlock_attributes(mesh, only_keyable=True)
                
                const = cmds.parentConstraint(target_mesh, mesh)
                cmds.delete(const)
                
    def _refresh_pose_control(self):
        
        if not self.pose_control:
            return
        
        if not cmds.objExists(self.pose_control):
            return
        
        shapes = cmds.listRelatives(self.pose_control, s = True)
        cmds.showHidden( shapes )
        
        if not cmds.objExists('%s.enable' % self.pose_control):
            
            cmds.addAttr(self.pose_control, ln = 'enable', at = 'double', k = True, dv = 1, min = 0, max = 1)    
            self._multiply_weight()

    def _rename_nodes(self):
        
        nodes = self._get_connected_nodes()
        
        for node in nodes:
            
            node_type = cmds.nodeType(node)
            
            if node_type == 'transform':
                shape = geo.get_mesh_shape(node)
                
                if shape:
                    node_type = cmds.nodeType(shape)
            
            cmds.rename(node, core.inc_name('%s_%s' % (node_type, self.description)))

    def _create_node(self, maya_node_type, description = None):
        
        if not description:
            name = core.inc_name('%s_%s' % (maya_node_type, self.description))
            
        if description:
            name = core.inc_name('%s_%s_%s' % (maya_node_type, description, self.description))
        
        node = cmds.createNode(maya_node_type, n = name)
        
        messages = self._get_message_attributes()
        
        found = []
        
        for message in messages:
            if message.startswith(maya_node_type):
                found.append(message)
                
        inc = len(found) + 1
        
        self._connect_node(node, maya_node_type, inc)
        
        return node
        
    def _connect_node(self, node, maya_node_type, inc = 1):
        attribute = '%s%s' % (maya_node_type, inc)
        
        if not cmds.objExists('%s.%s' % (self.pose_control, attribute)):
            cmds.addAttr(self.pose_control, ln = attribute, at = 'message' )
            
        if not cmds.isConnected('%s.message' % node, '%s.%s' % (self.pose_control, attribute)):
            cmds.connectAttr('%s.message' % node, '%s.%s' % (self.pose_control, attribute))
    
    def _set_string_node(self, node, maya_node_type, inc = 1):
        attribute = '%s%s' % (maya_node_type, inc)
        
        if not cmds.objExists('%s.%s' % (self.pose_control, attribute)):
            cmds.addAttr(self.pose_control, ln = attribute, dt = 'string' )
            
        cmds.setAttr('%s.%s' % (self.pose_control, attribute), node, type = 'string')
            
    def _connect_mesh(self, mesh):
        
        index = self.get_mesh_index(mesh)
        
        if index != None:
            return
        
        empty_index = self._get_empty_mesh_message_index()
        
        self._connect_node(mesh, 'mesh', empty_index)
        
    def _multiply_weight(self):
        pass

    def _get_string_attribute_with_prefix(self, prefix):
        if not self.pose_control:
            return []
        
        attributes = cmds.listAttr(self.pose_control, ud = True)
        
        strings = []
        
        for attribute in attributes:
            if attribute.startswith(prefix):
                node_and_attribute = '%s.%s' % (self.pose_control, attribute)
            
                if cmds.getAttr(node_and_attribute, type = True) == 'string':
                    strings.append(attribute)
                
        return strings
    
    def _get_named_string_attribute(self, name):
        
        node = cmds.getAttr('%s.%s' % (self.pose_control, name))
        
        return node
    
    def _get_named_message_attribute(self, name):
        
        node = attr.get_attribute_input('%s.%s' % (self.pose_control, name), True)
        
        return node
        
    
        
    def _get_message_attribute_with_prefix(self, prefix):
        if not self.pose_control:
            return []
        
        attributes = cmds.listAttr(self.pose_control, ud = True)
        
        messages = []
        
        for attribute in attributes:
            if attribute.startswith(prefix):
                node_and_attribute = '%s.%s' % (self.pose_control, attribute)
            
                if cmds.getAttr(node_and_attribute, type = True) == 'message':
                    messages.append(attribute)
                
        return messages
        
    def _get_mesh_message_attributes(self):
        
        return self._get_message_attribute_with_prefix('mesh')
        
    def _get_empty_mesh_message_index(self):
        messages = self._get_mesh_message_attributes()
        
        inc = 1
        for message in messages:
            
            message_input = attr.get_attribute_input('%s.%s' % (self.pose_control, message))
            
            if not message_input:
                break
            
            inc+=1
        
        return inc
    
    def _get_mesh_count(self):
        
        attrs = self._get_mesh_message_attributes()
        
        return len(attrs)
        
    def _get_corrective_meshes(self):
        
        found = []
        
        for inc in xrange(0, self._get_mesh_count()):
            mesh = self.get_mesh(inc)
            found.append(mesh)
            
        return found
        
    def _check_if_mesh_connected(self, name):
        
        for inc in xrange(0, self._get_mesh_count()):
            
            mesh = self.get_mesh(inc)
            
            target = self._get_mesh_target(mesh)
            if target == name:
                return True
        
        return False
    
    def _check_if_mesh_is_child(self, mesh):
        children = cmds.listRelatives(self.pose_control, f = True)
        
        if not children:
            return False
        
        for child in children:
            if child == mesh:
                return True
        
        return False
    
    def _hide_meshes(self):
        
        children = cmds.listRelatives(self.pose_control, f = True, type = 'transform')
        
        if not children:
            return
        
        for child in children:
            if geo.is_a_mesh(child):
                self._set_visibility(child, False)
        
        
    def _show_meshes(self):
        
        children = cmds.listRelatives(self.pose_control, f = True, type = 'transform')
        
        if not children:
            return
        
        for child in children:
            if geo.is_a_mesh(child):
                self._set_visibility(child, True)
        
    def _get_mesh_target(self, mesh):
        if not mesh:
            return None
        
        target_mesh = cmds.getAttr('%s.mesh_pose_source' % mesh)
        
        if not cmds.objExists(target_mesh):
            target = core.get_basename(target_mesh)
            
            if cmds.objExists(target):
                target_mesh = target

        return target_mesh
        
    def _get_message_attributes(self):
        
        attributes = cmds.listAttr(self.pose_control, ud = True)
        
        messages = []
        
        for attribute in attributes:
            node_and_attribute = '%s.%s' % (self.pose_control, attribute)
            
            if cmds.getAttr(node_and_attribute, type = True) == 'message':
                messages.append(attribute)
                
        return messages
    
    def _get_connected_nodes(self):
        
        attributes = self._get_message_attributes()
        
        nodes = []
        
        for attribute in attributes:
            connected = attr.get_attribute_input('%s.%s' % (self.pose_control, attribute), node_only = True)
            
            if connected:
                nodes.append(connected)
                
        return nodes

    def _get_mirror_pose_instance(self):
        
        other_pose = self._replace_side(self.pose_control)
        self.left_right = True
        
        
        if not other_pose:
            other_pose = self._replace_side(self.pose_control, False)
            self.left_right = False
            
        if cmds.objExists(other_pose):
            self.other_pose_exists = True
            
        pose = None
        
        if self._pose_type() == 'cone':
            
            pose = PoseCone()
            
            
        if self._pose_type() == 'no reader':
            
            pose = PoseNoReader()
            
        if self._pose_type() == 'combo':
            pose = PoseCombo()
                       
        other_pose_instance = pose
        other_pose_instance.set_pose(other_pose)
        
        return other_pose_instance

    def _create_pose_control(self):
        
        control = rigs_util.Control(self._get_name(), tag = False)
        control.set_curve_type('cube')
        control.hide_scale_and_visibility_attributes()
        pose_control = control.get()
        
        self.pose_control = pose_control
        
        self._create_attributes(pose_control)
        
        return self.pose_control

    def _create_attributes(self, control):
        
        super(PoseBase, self)._create_attributes(control)
        
        cmds.addAttr(control, ln = 'control_scale', at = 'float', dv = 1)
        
        cmds.addAttr(control, ln = 'enable', at = 'double', k = True, dv = 1, min = 0, max = 1)
        cmds.addAttr(control, ln = 'weight', at = 'double', k = True, dv = 0)
        
    def _create_mirror_mesh(self, target_mesh):
        
        other_mesh = target_mesh
        split_name = target_mesh.split('|')
        
        if not other_mesh:
            return None, None
        
        if not cmds.objExists(other_mesh):
            return None, None
        
        other_mesh_duplicate = cmds.duplicate(other_mesh, n = 'duplicate_corrective_temp_%s' % split_name[-1])[0]
        
        other_target_mesh = self._replace_side(split_name[-1], self.left_right)
        
        if not other_target_mesh or not cmds.objExists(other_target_mesh):
            if other_target_mesh:    
                vtool.util.warning('Could not find %s to mirror to!\nUsing %s as other mesh, which may cause errors!' % (other_target_mesh, target_mesh) )
            other_target_mesh = target_mesh
        
        deform.set_envelopes(target_mesh, 0)
        deform.set_envelopes(other_target_mesh, 0)
        
        other_target_name = core.get_basename(other_target_mesh)
            
        other_target_mesh_duplicate = cmds.duplicate(other_target_mesh, n = other_target_name)[0]
        home = cmds.duplicate(target_mesh, n = 'home')[0]
        
        deform.set_envelopes(target_mesh, 1)
        deform.set_envelopes(other_target_mesh, 1)
        
        mirror_group = cmds.group(em = True, n = core.inc_name('corretive_mirror_group'))
        
        attr.unlock_attributes(home)
        attr.unlock_attributes(other_mesh_duplicate)
        
        cmds.parent(home, mirror_group)
        cmds.parent(other_mesh_duplicate, mirror_group)
        
        #may need to do z or y axis eventually
        cmds.setAttr('%s.scaleX' % mirror_group, -1)
        
        deform.create_wrap(home, other_target_mesh_duplicate)
        
        cmds.blendShape(other_mesh_duplicate, home, foc = True, w = [0, 1])
        
        cmds.delete(other_target_mesh_duplicate, ch = True)               
        cmds.delete(mirror_group, other_mesh_duplicate)
        
        return other_target_mesh, other_target_mesh_duplicate

    def _delete_connected_nodes(self):
        nodes = self._get_connected_nodes()
        if nodes:
            cmds.delete(nodes)

    def _create_shader(self, mesh):
        
        shader_name = 'pose_blinn'
        
        shader_name = shade.apply_new_shader(mesh, type_of_shader = 'blinn', name = shader_name)
            
        cmds.setAttr('%s.color' % shader_name, 0.4, 0.6, 0.4, type = 'double3' )
        cmds.setAttr('%s.specularColor' % shader_name, 0.3, 0.3, 0.3, type = 'double3' )
        cmds.setAttr('%s.eccentricity' % shader_name, .3 )

    def _get_blendshape(self, mesh):
        
        return deform.find_deformer_by_type(mesh, 'blendShape')
        

    def _get_current_mesh(self, mesh_index):
        mesh = None
        
        if mesh_index == None:
            return
            #mesh = self.get_mesh(self.mesh_index)
        if mesh_index != None:
            mesh = self.get_mesh(mesh_index)
            
        if not mesh:
            return
        
        return mesh
    
    def _update_inbetween(self):
        poses = PoseManager().get_poses()
        
        weights = []
        
        for pose in poses:
            pose_instance = PoseManager().get_pose_instance(pose)
            weight = pose_instance.get_inbetween_weight()
            
            weights.append(weight)
    
        for pose in poses:
            pass
    
    def _replace_side(self, string_value, left_right = True):
        
        if string_value == None:
            return
        
        split_value = string_value.split('|')
        
        split_value.reverse()
        
        fixed = []
        
        for value in split_value:
                    
            other = ''
            
            if left_right:
                
                start, end = vtool.util.find_special('lf_', value, 'first')
                
                if start != None:
                    other = vtool.util.replace_string(value, 'rt_', start, end)
                    
                if not other:
                    start,end = vtool.util.find_special('l_', value, 'first')
                
                    if start != None:
                        other = vtool.util.replace_string(value, 'r_', start, end)
                    
                if not other:
                    start, end = vtool.util.find_special('_L_', value, 'last')
                    
                    if start != None:
                        other = vtool.util.replace_string(value, '_R_', start, end)
                    
                if not other:
                    start, end = vtool.util.find_special('L', value, 'end')
                    
                    if start != None:
                        other = vtool.util.replace_string(value, 'R', start, end)
                    
            if not left_right:
                
                start, end = vtool.util.find_special('rt_', value, 'first')
                
                if start != None:
                    other = vtool.util.replace_string(value, 'lf_', start, end)
                
                if not other:
                    start,end = vtool.util.find_special('r_', value, 'first')
                
                    if start != None:
                        other = vtool.util.replace_string(value, 'l_', start, end)
                
                if not other:
                    start, end = vtool.util.find_special('_R_', value, 'last')
                    
                    if start != None:
                        other = vtool.util.replace_string(value, '_L_', start, end)
                
                if not other:
                    start, end = vtool.util.find_special('R', value, 'end')
                    
                    if start != None:
                        other = vtool.util.replace_string(value, 'L', start, end)
                
            fixed.append(other)
            
        if len(fixed) == 1:
            
            return fixed[0]
        
        
        fixed.reverse()
        
        fixed = string.join(fixed, '|')
        
        return fixed
    
    def _set_visibility(self, node, bool_value):
        
        if bool_value:
            
            try:
                cmds.setAttr('%s.lodVisibility' % node, 1)
                cmds.setAttr('%s.visibility' % node, 1)
            except:
                pass
                #vtool.util.show( 'Could not set visibility on %s.' % node )
    
        if not bool_value:
            try:
                cmds.setAttr('%s.lodVisibility' % node, 0)
                cmds.setAttr('%s.visibility' % node, 0)    
            except:
                pass
                #vtool.util.show( 'Could not set visibility on %s.' % node )
    
    def _initialize_blendshape_node(self, target_mesh):
        
        blend = blendshape.BlendShape()
        
        blendshape_node = self._get_blendshape(target_mesh)
        
        referenced = False
        
        if blendshape_node:
            referenced = core.is_referenced(blendshape_node)
                
        if blendshape_node and not referenced:
            blend.set(blendshape_node)
        
        if not blendshape_node or referenced:
            blend.create(target_mesh)
          
        if referenced:
            
            skin_cluster = deform.find_deformer_by_type(target_mesh, 'skinCluster')
            
            if skin_cluster:
                try:
                    cmds.reorderDeformers(skin_cluster, blend.blendshape, target_mesh)
                    
                except:
                    pass
                
            if not skin_cluster:
                cmds.reorderDeformers(blend.blendshape, blendshape_node, target_mesh)
            
            
        return blend
    

    
    #--- pose
    
    def set_pose(self, pose_name):
        """
        Set the pose that the instance should work on.
        
        Args:
            pose_name (str): The name of a pose.
        """
        
        super(PoseBase, self).set_pose(pose_name)
        
        if self.pose_control == pose_name:
            self._refresh_pose_control()
            self._refresh_meshes()
    
    def rename(self, description):
        """
        Rename the pose and the target on the blendshape.
        
        Args:
            description (str): The new name for the pose.
            
        Returns:
            str: The new name.
        """
        
        old_description = vtool.util.clean_name_string( self.description )
        
        super(PoseBase, self).rename(description)
        
        meshes = self.get_target_meshes()
        
        for mesh in meshes:
            blendshape_node = self._get_blendshape(mesh)
            
            if blendshape_node:
                blend = blendshape.BlendShape(blendshape_node)        
                blend.rename_target(old_description, self.description)
        
        self._rename_nodes()
        
        return self.pose_control
       
    def delete(self):
        """
        Delete the pose and pose related nodes.
        """
        self.delete_blend_input()
        self._delete_connected_nodes()
        
        super(PoseBase, self).delete()
        
    #--- mesh
      
    def has_a_mesh(self):
        """
        Check if the pose has a mesh.
        
        Returns:
            bool: Wether the pose has a mesh or not.
        """
        if self._get_mesh_message_attributes():
            return True
        
        return False
        
    
        
    def add_mesh(self, mesh, toggle_vis = True):
        """
        Add a mesh to the pose.
        
        Args:
            mesh (str): The name of a mesh.
            toggle_vis (bool): Wether to toggle the meshes visibility.
            
        Returns:
            str: Returns: the name of the created pose mesh for sculpting. Return False if failed. 
        """
        
        mesh = cmds.ls(mesh, l = True)
        
        if not mesh:
            return
        
        if len(mesh) >= 1:
            mesh = mesh[0]
        
        if mesh.find('.vtx'):
            mesh = mesh.split('.')[0]
            
        if not geo.get_mesh_shape(mesh):
            return False
        
        if self._check_if_mesh_connected(mesh):
            return False
        
        if self._check_if_mesh_is_child(mesh):
            return False
        
        target_meshes = self.get_target_meshes()
        
        if mesh in target_meshes:
            
            index = self.get_target_mesh_index(mesh)
            return self.get_mesh(index)
        
        deform.set_envelopes(mesh, 0, ['skinCluster', 'blendShape', 'cluster'])
        
        pose_mesh = cmds.duplicate(mesh, n = core.inc_name('mesh_%s_1' % self.pose_control))[0]
        
        deform.set_envelopes(mesh, 1)
        
        self._create_shader(pose_mesh)
        
        attr.unlock_attributes(pose_mesh)
        
        cmds.parent(pose_mesh, self.pose_control)
        
        self._connect_mesh(pose_mesh)
        
        string_var = attr.MayaStringVariable('mesh_pose_source')
        string_var.create(pose_mesh)
        string_var.set_value(mesh)
        
        if toggle_vis:
            index = self.get_target_mesh_index(mesh)
            
            self.toggle_vis(index)
        
        return pose_mesh
    
    def remove_mesh(self, mesh):
        """
        Remove a mesh from the pose.
        
        Args:
            mesh (str): The name of a mesh affected by the pose.
        """
        index = self.get_target_mesh_index(mesh)
        mesh = self.get_mesh(index)
        
        self.visibility_off(mesh)
        
        if index == None:
            return

        if mesh == None:
            return
        
        if mesh and cmds.objExists(mesh):        
            blend_name = self.get_blendshape(index)
            
            if blend_name:
                
                nicename = core.get_basename(self.pose_control, remove_namespace=True)
                
                blend = blendshape.BlendShape(blend_name)
                blend.remove_target(nicename)
        
        attributes = self._get_mesh_message_attributes()
        attribute = attributes[index]
        
        cmds.delete(mesh)
        attr.disconnect_attribute(attribute)
        
        
    
    def get_mesh(self, index):
        """
        Get the sculpt mesh at the index. Sculpt mesh is the mesh used to generate the delta.
        
        Args:
            index (int): The index of a sculpt mesh.
            
        Returns:
            str: The name of the sculpt mesh at the index.
        """
        if index == None:
            
            return
        
        mesh_attributes = self._get_mesh_message_attributes()
        
        if not mesh_attributes:
            return
        
        if index > (len(mesh_attributes)-1):
            return
            
        mesh = attr.get_attribute_input('%s.%s' % (self.pose_control, mesh_attributes[index]), True)
                
        return mesh

    def get_mesh_count(self):
        """
        Get the number of meshes the pose affects.
        
        Returns:
            int
        """
        attrs = self._get_mesh_message_attributes()
        
        if attrs:
            return len(attrs)
    
        return 0
    
    def get_target_meshes(self):
        """
        Get the meshes affected by the pose.
        
        Returns:
            list: A list of the names of meshes.
        """
        meshes = []
        
        for inc in xrange(0, self._get_mesh_count()):
            mesh = self.get_mesh(inc)
            
            mesh = self.get_target_mesh(mesh)
            
            meshes.append(mesh)
            
        return meshes
        
    def get_sculpt_mesh(self, target_mesh):
        
        index = self.get_target_mesh_index(target_mesh)
        
        return self.get_mesh(index)
        
        
        
        
    def get_target_mesh(self, mesh):
        """
        Get the mesh that the sculpt mesh affects.
        
        Args:
            mesh (str): The name of a mesh affected by the pose.
            
        Returns:
            str: The name of a mesh.
        """
        long_name = None
        
        if cmds.objExists('%s.mesh_pose_source' % mesh):
            target_mesh = cmds.getAttr('%s.mesh_pose_source' % mesh)
            
            namespace = core.get_namespace(self.pose_control)
            if namespace:
                
                basename = core.get_basename(target_mesh, remove_namespace = True)
                
                target_mesh = '%s:%s' % (namespace, basename) 
                
                if cmds.objExists(target_mesh):
                    return target_mesh
                else:
                    return None
            
            long_name = target_mesh
            
            if cmds.objExists(target_mesh):
                long_name = cmds.ls(target_mesh, l = True)[0]
                
                if long_name != target_mesh:
                    cmds.setAttr('%s.mesh_pose_source' % mesh, long_name, type = 'string')
            
            if not cmds.objExists(long_name):
                
                target_mesh = core.get_basename(long_name)
                
                if cmds.objExists(target_mesh):
                
                    long_name = cmds.ls(target_mesh, l = True)[0]
                
                    cmds.setAttr('%s.mesh_pose_source' % mesh, long_name, type = 'string')
                    
                if not cmds.objExists(target_mesh):
                    long_name = target_mesh
        
        return long_name
        
    def get_target_mesh_index(self, target_mesh):
        """
        Get the index of a target mesh. Target meshes are the meshes that have the delta applied to them.
        
        Args:
            target_mesh (str): The name of a target mesh.
            
        Returns:
            int: The index of the mesh. 
        """
        
        target_meshes = self.get_target_meshes()
        
        longname_target_mesh = cmds.ls(target_mesh, l = True)
        
        if longname_target_mesh: 
            target_mesh = longname_target_mesh[0]
            if self.pose_control:
                namespace = core.get_namespace(self.pose_control)
                if namespace:
                    
                    basename = core.get_basename(target_mesh, remove_namespace = True)
                    
                    target_mesh = '%s:%s' % (namespace, basename) 
            
        inc = 0
        
        for target_mesh_test in target_meshes:
            
            if target_mesh == target_mesh_test:
                return inc
            
            inc += 1
    
    def get_mesh_index(self, mesh):
        """
        Get the index of a sculpt mesh.
        
        Args:
            mesh (str): The name of a sculpt mesh.
        """
        
        attributes = self._get_mesh_message_attributes()
        
        inc = 0
        
        for attribute in attributes:
        
            stored_mesh = self._get_named_message_attribute(attribute)
            
            if stored_mesh == mesh:
                return inc
            
            inc += 1
        
    @core.undo_chunk
    def reset_target_meshes(self):
        """
        Reset target meshes on a pose, so that they have no corrective delta.
        """
        count = self._get_mesh_count()
        
        for inc in xrange(0, count):
            
            deformed_mesh = self.get_mesh(inc)
            original_mesh = self.get_target_mesh(deformed_mesh)
            
            cmds.delete(deformed_mesh, ch = True)
            
            blendshape_node = self._get_blendshape(original_mesh)
            
            blend = blendshape.BlendShape()
                    
            if blendshape_node:
                blend.set(blendshape_node)
                
            blend.set_envelope(0)    
            
            temp_dup = cmds.duplicate(original_mesh)[0]
            
            #using blendshape because of something that looks like a bug in Maya 2015
            temp_blend = deform.quick_blendshape(temp_dup, deformed_mesh)
            
            cmds.delete(temp_blend, ch = True)
            cmds.delete(temp_dup)
            
            blend.set_envelope(1)
            
            self.create_blend(inc)
            
    def update_target_meshes(self, only_not_in_sculpt = False):
        
        count = self._get_mesh_count()
        
        for inc in xrange(0, count):
            
            if self.is_mesh_in_sculpt(inc) and only_not_in_sculpt:
                continue
            
            deformed_mesh = self.get_mesh(inc)
            original_mesh = self.get_target_mesh(deformed_mesh)
            
            if not deformed_mesh:
                continue
            if not original_mesh:
                continue
            
            if geo.is_mesh_position_same(deformed_mesh, original_mesh, 0.0001):
                continue
            
            cmds.delete(deformed_mesh, ch = True)
            
            envelope = deform.EnvelopeHistory(original_mesh)
            envelope.turn_off_exclude(['skinCluster', 'blendShape', 'cluster'])
            
            deform.quick_blendshape(original_mesh, deformed_mesh)
            
            
            cmds.delete(deformed_mesh, ch = True)
            
            index = self.get_mesh_index(deformed_mesh)
            
            self.create_blend(index, goto_pose = False, sub_poses = True)
            
            envelope.turn_on(respect_initial_state = True)
            
            
            
    def revert_selected_verts(self):
        
        selection = cmds.ls(sl = True, flatten = True, l = True)
        
        envelopes = {}
        sculpts = []
        
        for thing in selection:
            
            if thing.find('.vtx') > -1:
                
                mesh = thing.split('.')[0]
                
                target_mesh =  self.get_target_mesh(mesh)
                sculpt_index = self.get_target_mesh_index(mesh)
                
                if target_mesh:
                    #should arrive here if a sculpt mesh is selected
                    sculpt_index = self.get_target_mesh_index(target_mesh)
                    sculpt_mesh = self.get_mesh(sculpt_index)
                    
                if not target_mesh and sculpt_index != None:
                    #should arrive here if a target mesh is selected
                    sculpt_mesh = self.get_mesh(sculpt_index)
                    target_mesh = self.get_target_mesh(sculpt_mesh)
                
                if not envelopes.has_key(target_mesh):
                    envelope = deform.EnvelopeHistory(target_mesh)
                    envelope.turn_off_exclude(['skinCluster'])
                    envelopes[target_mesh] = envelope
                
                vtx_index = vtool.util.get_last_number(thing)
                
                pos = cmds.xform('%s.vtx[%s]' % (target_mesh, vtx_index), q = True, ws = True, t = True)
                pos_sculpt = cmds.xform('%s.vtx[%s]' % (sculpt_mesh, vtx_index), q = True, ws = True, t = True)
                
                same = False
                
                if pos[0] == pos_sculpt[0]:
                    if pos[1] == pos_sculpt[1]:
                        if pos[2] == pos_sculpt[2]:
                            same = True
                
                if not same:
                    cmds.xform('%s.vtx[%s]' % (sculpt_mesh, vtx_index), ws = True, t = pos)
                
                if not sculpt_index in sculpts:
                    sculpts.append(sculpt_index)
                
        if envelopes:
            for key in envelopes:
                envelope = envelopes[key]
                envelope.turn_on(respect_initial_state = True) 
                    
        if sculpts:
            for after_sculpt in sculpts:
                self.create_blend(after_sculpt, False, sub_poses = True)
    
    def is_mesh_in_sculpt(self, index):
        
        sculpt_mesh = self.get_mesh(index)
        target_mesh = self.get_target_mesh(sculpt_mesh)
        
        
        if target_mesh:
            secondary_vis = cmds.getAttr('%s.lodVisibility' % target_mesh)
        
            if secondary_vis:
                return False
        
            if not secondary_vis:
                return True
        
        return False
    
    def visibility_off(self, mesh, view_only = False):
        """
        Turn the sculpt mesh visibility off.
        
        Args:
            mesh (str): The name of the mesh afftected by the pose. Its corresponding sculpt mesh will have its visibility turned off.
            vew_only (bool): Wether to just change the view, or recalculate the delta.
        """
        
        if not mesh:
            return
        
        self._set_visibility(mesh, 0)
        
        target_mesh = self.get_target_mesh(mesh)
        
        if target_mesh and cmds.objExists(target_mesh):
            self._set_visibility(target_mesh, 1)
            
        
        
        if not view_only and cmds.objExists(target_mesh):
            
            if geo.is_mesh_position_same(target_mesh, mesh, 0.0001):
                return
            
            index = self.get_mesh_index(mesh)
            
            self.create_blend(index)
        
    def visibility_on(self, mesh):
        """
        Turn sculpt visibility on.
        
        Args:
            mesh (str): The name of a mesh affected by the pose. Its corresponding sculpt mesh will have its visibility turned on.
        """
        
        if not mesh:
            return
        
        engines = shade.get_shading_engines_by_geo(mesh)
        
        if not engines:
            self._create_shader(mesh)
        
        self._set_visibility(mesh, 1)
        
        target_mesh = self.get_target_mesh(mesh) 
        
        if target_mesh and cmds.objExists(target_mesh):
            
            self._set_visibility(target_mesh, 0)
            
            if not core.is_batch():
                core.add_to_isolate_select(mesh)
        
    def toggle_vis(self, mesh_index, view_only = False):
        """
        Toggle the visibility of a sculpt mesh.
        
        Args:
            mesh_index (int): The index of a sculpt mesh.
            view_only (bool): Wether to just change visibility, or refresh the delta when visibility is turned off.
        """
        
        if mesh_index == None:
            return
        
        mesh = self.get_mesh(mesh_index)
        target_mesh = self.get_target_mesh(mesh)
        
        if target_mesh and mesh:
            if cmds.objExists(target_mesh):
                if cmds.getAttr('%s.lodVisibility' % target_mesh) == 1:
                    if cmds.getAttr('%s.lodVisibility' % mesh) == 1:
                        self._set_visibility(target_mesh, 0)
                
                        return    
            
        if mesh:
            if cmds.getAttr('%s.lodVisibility' % mesh) == 1:
                self.visibility_off(mesh, view_only)
                return
            
            if cmds.getAttr('%s.lodVisibility' % mesh) == 0:
                self.visibility_on(mesh)
                return
        
    #--- blend
        
    def create_all_blends(self):
        """
        Create all the blends in a pose. 
        This refreshes the deltas.
        """
        
        count = self._get_mesh_count()
        
        pose = True
        
        for inc in xrange(0, count):
            
            if self.create_blends_went_to_pose:
                pose = False
                
            self.create_blend(inc, goto_pose = pose)
                
        self.create_blends_went_to_pose = False
    
    def create_blend(self, mesh_index, goto_pose = True, sub_poses = True):
        """
        Create the blend. This will refresh the delta.
        
        Args:
            mesh_index (int): Work with the mesh at the index. Pose needs to be affecting at least one mesh.
            goto_pose (bool): Wether to go to the pose. 
            sub_poses (bool): Wether to create blend for sub poses as well.
        """
        
        mesh = self._get_current_mesh(mesh_index)
        
        if not mesh:
            return
        
        manager = PoseManager()
        manager.set_weights_to_zero()
        
        target_mesh = self.get_target_mesh(mesh)
        
        envelope = deform.EnvelopeHistory(target_mesh)
        envelope.turn_off_exclude(['skinCluster', 'blendShape', 'cluster'])
        
        sub_pass_mesh = target_mesh
        
        if not target_mesh:
            RuntimeError('Mesh index %s, has no target mesh' % mesh_index)
            return
        
        if goto_pose:
            self.goto_pose()
        
        self.disconnect_blend(mesh_index)
                
        blend = self._initialize_blendshape_node(target_mesh)
        
        nicename = core.get_basename(self.pose_control, remove_namespace = True)
        
        blend.set_weight(nicename, 0)
        
                
        offset = deform.chad_extract_shape(target_mesh, mesh)
        
        
        
        
        blend.set_weight(nicename, 1)
        
        if blend.is_target(nicename):
            blend.replace_target(nicename, offset)
        
        if not blend.is_target(nicename):
            blend.create_target(nicename, offset)
        
        self.connect_blend(mesh_index)
                
        if not cmds.isConnected('%s.weight' % self.pose_control, '%s.%s' % (blend.blendshape, nicename)):
            cmds.connectAttr('%s.weight' % self.pose_control, '%s.%s' % (blend.blendshape, nicename))
        
        
        cmds.delete(offset)
        
        
        if sub_poses:
            self.create_sub_poses(sub_pass_mesh)
            
        envelope.turn_on()
        
        
    def detach_sub_poses(self):
        """
        Detach the sub poses.
        Attaching and detaching help with export/import.
        """
        manager = PoseManager()
        manager.set_pose_group(self.pose_control)
        children = manager.get_poses()
        
        if not children:
            return
        
        detached_attributes = {}
        
        for child in children:
        
            child_instance= manager.get_pose_instance(child)
            detached = child_instance.detach()
            
            detached_attributes[child] = detached
            
        return detached_attributes
            
    def attach_sub_poses(self, outputs):
        """
        Attach the sub poses.
        Attaching and detaching help with export/import.
        """
        manager = PoseManager()
        manager.set_pose_group(self.pose_control)
        children = manager.get_poses()
        
        if not children:
            return
        
        for child in children:
            
            detached = None
            
            if type(outputs) == dict:
                if outputs.has_key(child):
                    detached = outputs[child]
            
            child_instance= manager.get_pose_instance(child)
            child_instance.attach(detached)
    
    def reconnect_blends(self):
        meshes = self.get_target_meshes()
        if not meshes:
            return 
        
        worked = False
        
        for inc in range(0,len(meshes)):
            connect_worked = self.connect_blend(inc)
            if not worked and connect_worked:
                worked = True
            
        return worked
    
    def connect_blend(self, mesh_index = None):
        """
        Connect pose to the blendshape.
        
        Args:
            mesh_index (int): Work with the mesh at the index. 
        """
        mesh = None
        
        if mesh_index == None:
            return
        
        if mesh_index != None:
            mesh = self.get_mesh(mesh_index)
        
        if not mesh:
            return
        
        blend = blendshape.BlendShape()
        
        target_mesh = self.get_target_mesh(mesh)
        
        blendshape_node = self._get_blendshape(target_mesh)
        
        if blendshape_node:
            blend.set(blendshape_node)
        
        nicename = core.get_basename(self.pose_control, remove_namespace = True)
        
        source_attr = self.blend_input
        
        if not source_attr:
            source_attr = '%s.weight' % self.pose_control
        
        if source_attr and blend.is_target(nicename):
            input_attr = '%s.%s' % (blend.blendshape, nicename)
            if not attr.is_connected(input_attr):
                cmds.connectAttr(source_attr, input_attr)
                self.blend_input = None
                return True
            
            
        
        return False
    
    def disconnect_blend(self, mesh_index = None):
        """
        Disconnect pose to the blendshape.
        
        Args:
            mesh_index (int): Work with the mesh at the index. 
        """
        
        mesh = None
        
        if mesh_index == None:
            return
        
        if mesh_index != None:
            mesh = self.get_mesh(mesh_index)
            
        if not mesh:
            return
        
        blend = blendshape.BlendShape()
        
        target_mesh = self.get_target_mesh(mesh)
        
        if not cmds.objExists(target_mesh):
            return
        
        blendshape_node = self._get_blendshape(target_mesh)
        
        if blendshape_node:
            blend.set(blendshape_node)
                
        nicename = core.get_basename(self.pose_control, remove_namespace = True)
                
        desired_attribute = '%s.%s' % (blend.blendshape, nicename)
        
        if not cmds.objExists(desired_attribute):
            return
        
        input_value = attr.get_attribute_input(desired_attribute)
                
        self.blend_input = input_value
                
        if input_value:
            
            attr.disconnect_attribute(desired_attribute)   

    def delete_blend_input(self):
        """
        Delete the connections going into the blendshape.
        """
        
        outputs = attr.get_attribute_outputs('%s.weight' % self.pose_control)
        
        removed_already = False
        
        if outputs:
            for output in outputs:
                
                removed_already = False
                
                if cmds.nodeType(output) == 'multiplyDivide':
                    
                    node = output.split('.')
                
                    found = None
                    
                    if len(node) == 2:
                        node = node[0]
                        found = node
                    
                    if found:
                        
                        output_value = attr.get_attribute_outputs('%s.outputX' % found)
                        
                        if output_value and len(output_value) == 1:
                            output = output_value[0]
                        
                        if output_value and len(output_value) > 1:
                            for this_output in output_value:
                
                                split_output = this_output.split('.')
                                
                                blend = blendshape.BlendShape(split_output[0])
                
                                blend.remove_target(split_output[1])            
                    
                                removed_already = True
                
                if cmds.nodeType(output) == 'blendShape' and not removed_already:
                    
                    split_output = output.split('.')
                    
                    blend = blendshape.BlendShape(split_output[0])
                    
                    blend.remove_target(split_output[1])
        
    def get_blendshape(self, mesh_index = None):
        """
        Get the blendshape.
        
        Args:
            mesh_index (int): Work with the mesh at the index. 
        """
        mesh = None
        
        if mesh_index == None:
            return
            
        if mesh_index != None:
            mesh = self.get_mesh(mesh_index)
            
        if not mesh:
            return
        
        target_mesh = self.get_target_mesh(mesh)
        
        if not target_mesh or not cmds.objExists(target_mesh):
            return
        
        blendshape_node = self._get_blendshape(target_mesh)
        
        return blendshape_node
        
    #--- attributes
    
    def disconnect_weight_outputs(self):
        """
        Disconnect outputs from the pose.weight attribute.
        """
        
        self.disconnected_attributes = None
        
        outputs = attr.get_attribute_outputs('%s.weight' % self.pose_control)
        
        if not outputs:
            return
        
        for output in outputs:
            
            node = output.split('.')[0]
            
            if cmds.nodeType(node) == 'multiplyDivide' and cmds.isConnected('%s.enable' % self.pose_control, '%s.input2X' % node):
                continue
            
            attr.disconnect_attribute(output)
        
        return outputs
        
    def reconnect_weight_outputs(self, outputs):
        """
        Connect outputs from pose.weight attr.
        """
        if not outputs:
            return
        
        for attribute in outputs:
            
            if not cmds.objExists(attribute):
                continue
            
            input_value = attr.get_attribute_input(attribute)
            
            if not input_value:
                cmds.connectAttr('%s.weight' % self.pose_control, attribute)
                
    def set_enable(self, value):
        cmds.setAttr('%s.enable' % self.pose_control, value)
                
class PoseNoReader(PoseBase):
    """
    This type of pose does not read anything in a rig unless an input is specified.
    """
    def _pose_type(self):
        return 'no reader'
   
    def _create_pose_control(self):
        
        pose_control = cmds.group(em = True, n = self._get_name())
        attr.hide_keyable_attributes(pose_control)
        
        self.pose_control = pose_control
        
        self._create_attributes(pose_control)
        
        return pose_control
    
    def _create_attributes(self, control):
        
        super(PoseNoReader, self)._create_attributes(control)
        pose_input = attr.MayaStringVariable('weightInput')
        pose_input.create(control)
    
    def _multiply_weight(self, destination):

        multiply = self._get_named_message_attribute('multiplyDivide1')
        
        if not multiply:
            multiply = self._create_node('multiplyDivide')
            
            if not cmds.isConnected('%s.weight' % self.pose_control, '%s.input1X' % multiply):
                cmds.connectAttr('%s.weight' % self.pose_control, '%s.input1X' % multiply)
                
            if not cmds.isConnected('%s.enable' % self.pose_control, '%s.input2X' % multiply):
                cmds.connectAttr('%s.enable' % self.pose_control, '%s.input2X' % multiply)
        
        attr.disconnect_attribute(destination)
        cmds.connectAttr('%s.outputX' % multiply, destination)
    
    def _connect_weight_input(self, attribute):
        
        weight_attr = '%s.weight' % self.pose_control
        
        input_attr = attr.get_attribute_input(weight_attr)
        
        if attribute == input_attr:
            return
        
        cmds.connectAttr(attribute, weight_attr)

    def create_blend(self, mesh_index, goto_pose = True, sub_poses = True):
        
        mesh = self._get_current_mesh(mesh_index)
        
        target_mesh = self.get_target_mesh(mesh)
        
        sub_pass_mesh = target_mesh
        
        if not mesh:
            return
        
        manager = PoseManager()
        manager.set_weights_to_zero()
        
        this_index = mesh_index
        
        if mesh_index == None:
            return
        
        old_delta = self._get_named_message_attribute('delta%s' % (this_index + 1))
        if old_delta:
            cmds.delete(old_delta)
        
        target_mesh = self.get_target_mesh(mesh)
                
        if not target_mesh:
            RuntimeError('Mesh index %s, has no target mesh' % mesh_index)
            return
        
        if goto_pose:
            self.goto_pose()
        
        self.disconnect_blend(this_index)
        
        blend = self._initialize_blendshape_node(target_mesh)
        
        nicename = core.get_basename(self.pose_control, remove_namespace = True)
        
        blend.set_weight(nicename, 0)
        
        offset = deform.chad_extract_shape(target_mesh, mesh)
        
        blend.set_weight(nicename, 1)
        
        self.connect_blend(this_index)
        
        if blend.is_target(nicename):
            blend.replace_target(nicename, offset)
        
        if not blend.is_target(nicename):
            blend.create_target(nicename, offset)
                
        blend_attr = '%s.%s' % (blend.blendshape, nicename)
        weight_attr = '%s.weight' % self.pose_control
        input_attr = attr.get_attribute_input(blend_attr)
        
        if input_attr:
            weight_input = attr.get_attribute_input(weight_attr)
            
            if not weight_input:
                
                multiply_node = self._get_named_message_attribute('multiplyDivide1')
                
                pose_input = input_attr.split('.')[0]
                
                if not pose_input == multiply_node:
                    
                    self.set_input(input_attr)
        
        self._multiply_weight(blend_attr)
        
        cmds.delete(offset)
        
        if sub_poses:
            self.create_sub_poses(sub_pass_mesh)
        
    def set_input(self, attribute):
        """
        Set the input into the weightInput of the no reader.
        No readers need to have a connection specified that tells the pose when to turn on.
        
        Args:
            attribute (str): The node.attribute name of a connection to feed into the no reader.
        """
        self.weight_input = attribute
        
        if not cmds.objExists('%s.weightInput' % self.pose_control):
            
            cmds.addAttr(self.pose_control, ln = 'weightInput', dt = 'string')
            
            if not attribute:
                attribute = ''
        
        cmds.setAttr('%s.weightInput' % self.pose_control, attribute, type = 'string')
        
        if not attr.is_attribute_numeric(attribute):
            attr.disconnect_attribute('%s.weight' % self.pose_control)
            return
        
        self._connect_weight_input(attribute)
        
    def get_input(self):
        """
        Get the connection into the weightInput attribute of a no reader.
        No readers need to have a connection specified that tells the pose when to turn on.
        
        Returns:
            str: node.attribute name
        """
        attribute = attr.get_attribute_input('%s.weight' % self.pose_control)
        
        if attribute:
            return attribute
        
        return cmds.getAttr('%s.weightInput' % self.pose_control)

    def attach(self, outputs = None):
        super(PoseNoReader, self).attach(outputs)
        
        attribute = self.get_input()
        self.set_input(attribute)
        
        if outputs:
            self.reconnect_weight_outputs(outputs)
            
        self._hide_meshes()
        
        if self.sub_detach_dict:
            
            for key in self.sub_detach_dict:
                pose = get_pose_instance(key)
                pose.attach(self.sub_detach_dict[pose])
                
            self.sub_detach_dict = {}
        
    def detach(self):    
        super(PoseNoReader, self).detach()
        
        input_value = self.get_input()
        
        outputs = self.disconnect_weight_outputs()
        
        attr.disconnect_attribute('%s.weight' % self.pose_control)
        
        cmds.setAttr('%s.weightInput' % self.pose_control, input_value, type = 'string')
        
        self._show_meshes()
        
        return outputs
        
    def mirror(self):
        """
        Mirror a pose to a corresponding R side pose.
        
        For example
            If self.pose_control = pose_arm_L, there must be a corresponding pose_arm_R.
            The pose at pose_arm_R must be a mirrored pose of pose_arm_L.
        
        """
        self.other_pose_exists = False
        
        other_pose_instance = self._get_mirror_pose_instance()
        
        other_target_meshes = []
        input_meshes = {}

        for inc in xrange(0, self._get_mesh_count()):

            mesh = self.get_mesh(inc)
            target_mesh = self.get_target_mesh(mesh)
            
            if target_mesh == None:
                continue
            
            other_target_mesh, other_target_mesh_duplicate = self._create_mirror_mesh(target_mesh)
            
            if other_target_mesh == None:
                continue
    
            input_meshes[other_target_mesh] = other_target_mesh_duplicate
            other_target_meshes.append(other_target_mesh)
        
        if not self.other_pose_exists:
            store = rigs_util.StoreControlData(self.pose_control)
            
            if self.left_right:
                side = 'L'
            if not self.left_right:
                side = 'R'
            
            store.eval_mirror_data(side)
            
            other_pose_instance.create()
            
        if self.other_pose_exists:
            other_pose_instance.goto_pose()
            
        #cmds.setAttr('%s.weight' % self.pose_control, 0)
        
        for mesh in other_target_meshes:
            index = other_pose_instance.get_target_mesh_index(other_target_mesh)
            
            if index == None:
                other_pose_instance.add_mesh(other_target_mesh, toggle_vis = False)
        
        for mesh in other_target_meshes:
            
            index = other_pose_instance.get_target_mesh_index(mesh)
            if index == None:
                continue
            
            input_mesh = other_pose_instance.get_mesh(index)
            
            if not input_mesh:
                continue
            
            fix_mesh = input_meshes[mesh]
            
            cmds.blendShape(fix_mesh, input_mesh, foc = True, w = [0,1])
            
            other_pose_instance.create_blend(index, False)
            
            cmds.delete(input_mesh, ch = True)
            cmds.delete(fix_mesh)
        
        return other_pose_instance.pose_control
    
    def set_weight(self, value):
        """
        Set the weight attribute of the no reader.
        No readers have connections specified. 
        If no connection is specified and connected, this can set the weight.
        
        Args:
            value (float): The value to set the weight to.
        """
        input_attr = attr.get_attribute_input('%s.weight' % self.pose_control)
        if not input_attr:
            try:
                cmds.setAttr('%s.weight' % self.pose_control, value)
            except:
                pass
        
        manager = PoseManager()
        manager.set_pose_group(self.pose_control)
        children = manager.get_poses()
        
        if children:
            
            for child in children:
                
                child_instance = manager.get_pose_instance(child)
                child_instance.set_weight(value)
                
class PoseCombo(PoseNoReader):
    def _pose_type(self):
        return 'combo'
        
    def _create_attributes(self, control):
        
        super(PoseNoReader, self)._create_attributes(control)
        #pose_input = attr.MayaStringVariable('weightInput')
        #pose_input.create(control)
    
        
    def _remove_empty_multiply_attributes(self):
        
        attributes = self._get_message_attribute_with_prefix('multiply')
        
        for attribute in attributes:
            input_value = attr.get_attribute_input('%s.%s' % (self.pose_control, attribute))
            
            if not input_value:
                cmds.deleteAttr('%s.%s' % (self.pose_control, attribute))
    
        
    def _get_pose_string_attributes(self):
        
        return self._get_string_attribute_with_prefix('pose')
    
    def _get_empty_pose_string_index(self):
        
        strings = self._get_pose_string_attributes()
        
        inc = 1
        for string in strings:
            
            value = cmds.getAttr('%s.%s' % (self.pose_control, string))
            
            if not value:
                break
            
            inc+=1
        
        return inc
    
    def _connect_pose(self, pose):
        
        index = self.get_pose_index(pose)
        
        if index != None:
            return
        
        empty_index = self._get_empty_pose_string_index()
        
        self._set_string_node(pose, 'pose', empty_index)
    
    def _get_pose_count(self):
        
        attrs = self._get_pose_string_attributes()
        
        return len(attrs)
    
    def _connect_multiplies(self):
        
        poses = self.get_poses()
        
        multiply = None
        
        if len(poses) > 1:
            for pose in poses:
                
                if not pose:
                    continue
                
                namespace = core.get_namespace(self.pose_control)
                if namespace:
                    pose = '%s:%s' % (namespace, pose)
                
                output = '%s.weight' % pose
                
                if not multiply:
                    input_value = '%s.weight' % self.pose_control
                if multiply:
                    input_value = '%s.input2X' % multiply
                
                if cmds.objExists(output):
                    multiply = attr.connect_multiply(output, input_value)
                
            if multiply:
                
                cmds.connectAttr('%s.enable' % self.pose_control, '%s.input2X' % multiply)
        
    def _disconnect_multiplies(self):
        
        multiplies = self._find_multiplies()
        
        if multiplies:
            cmds.delete(multiplies)
            
            
        
    def _find_multiplies(self):
        
        input_value = attr.get_attribute_input('%s.weight' % self.pose_control, node_only = True)
        
        multi = []
        multiplies = []
        
        if cmds.nodeType(input_value) == 'multiplyDivide':
            multi = [input_value]
            
        while multi:
            
            multiplies += multi
            
            new_multi = []
            
            for m in multi:
                input_value = attr.get_attribute_input('%s.input1X' % m, node_only = True)
                if cmds.nodeType(input_value) == 'multiplyDivide':
                    new_multi.append(input_value)
                
                input_value = attr.get_attribute_input('%s.input2X' % m, node_only = True)
                if cmds.nodeType(input_value) == 'multiplyDivide':
                    new_multi.append(input_value)
                    
            if new_multi:
                multi = new_multi
            if not new_multi:
                multi = []
                
        attributes = self._get_message_attribute_with_prefix('multiply')
        
        for attribute in attributes:
            input_attr = attr.get_attribute_input('%s.%s' % (self.pose_control, attribute), node_only = True)
            
            if input_attr:
                inputs = attr.get_inputs(input_attr, node_only = True)
                
                if not inputs:
                    multiplies.append(input_attr)
                    
        return multiplies
        
    def set_input(self, attribute):
        """
        Set the input into the weightInput of the no reader.
        No readers need to have a connection specified that tells the pose when to turn on.
        
        Args:
            attribute (str): The node.attribute name of a connection to feed into the no reader.
        """
        pass

        
    def add_pose(self, pose_name):
        
        self._connect_pose(pose_name)
        
    def get_pose_index(self, pose):
        
        attributes = self._get_pose_string_attributes()
        
        inc = 0
        
        for attribute in attributes:
        
            stored_pose = self._get_named_string_attribute(attribute)
            
            if stored_pose == pose:
                return inc
            
            inc += 1
        
    def remove_pose(self, pose_name):
        
        index = self.get_pose_index(pose_name)
        pose = self.get_pose(index)
        
        if index == None:
            return
        
        if pose != pose_name:
            return
        
        attributes = self._get_pose_string_attributes()
        attribute = attributes[index]
        
        attr.disconnect_attribute('%s.%s' % (self.pose_control, attribute))
        
        self.refresh_multiply_connections()
        
    def get_pose(self, index):
        
        if index == None:
            return
        
        pose_attributes = self._get_pose_string_attributes()
        
        if not pose_attributes:
            return
        
        if index > (len(pose_attributes)-1):
            return
            
        pose = cmds.getAttr('%s.%s' % (self.pose_control, pose_attributes[index]))
        
        return pose
        
    def get_poses(self):
        
        pose_count = self._get_pose_count()
        
        poses = []
        
        for pose_index in range(0, pose_count):
            
            poses.append(self.get_pose(pose_index))
        
        return poses
    
    def refresh_multiply_connections(self):
        
        self._disconnect_multiplies()
        self._connect_multiplies()
        
    def attach(self, outputs = None):
        #super(PoseNoReader, self).attach(outputs)
        
        if outputs:
            self.reconnect_weight_outputs(outputs)
            
        self.refresh_multiply_connections()
            
        self._hide_meshes()
        
        if self.sub_detach_dict:
            
            for key in self.sub_detach_dict:
                pose = get_pose_instance(key)
                pose.attach(self.sub_detach_dict[pose])
                
            self.sub_detach_dict = {}
        
    def detach(self):    
        #super(PoseNoReader, self).detach()
        
        self._disconnect_multiplies()
        
        outputs = self.disconnect_weight_outputs()
        
        self._show_meshes()
        
        return outputs
        
class PoseCone(PoseBase):
    """
    This type of pose reads from a joint or transform, for the defined angle of influence. 
    """
    def __init__(self, transform = None, description = 'pose'):          
        super(PoseCone, self).__init__(description)
        
        if transform:
            transform = transform.replace(' ', '_')
        
        self.transform = transform
        
        self.axis = 'X'
    
    def _pose_type(self):
        return 'cone'
    
    def _get_color_for_axis(self):
        if self.axis == 'X':
            return 13
            
        if self.axis == 'Y':
            return 14    
            
        if self.axis == 'Z':
            return 6
    
    def _get_axis_rotation(self):
        if self.axis == 'X':
            return [0,0,-90]
        
        if self.axis == 'Y':
            return [0,0,0]
        
        if self.axis == 'Z':
            return [90,0,0]
          
    def _get_twist_axis(self):
        if self.axis == 'X':
            return [0,1,0]
        
        if self.axis == 'Y':
            return [1,0,0]
        
        if self.axis == 'Z':
            return [1,0,0]
        
    def _get_pose_axis(self):
        if self.axis == 'X':
            return [1,0,0]
        
        if self.axis == 'Y':
            return [0,1,0]
        
        if self.axis == 'Z':
            return [0,0,1]
        
    def _create_pose_control(self):
        
        pose_control = super(PoseCone, self)._create_pose_control()
        
        self._position_control(pose_control)
        
        if self.transform:
            match = space.MatchSpace(self.transform, pose_control)
            match.translation_rotation()
        
            parent = cmds.listRelatives(self.transform, p = True)
            
            if parent:
                cmds.parentConstraint(parent[0], pose_control, mo = True)
                cmds.setAttr('%s.parent' % pose_control, parent[0], type = 'string')
                
        return pose_control
        
    def _position_control(self, control = None):
        
        if not control:
            control = self.pose_control
        
        control = rigs_util.Control(control)
        
        control.set_curve_type('pin_point')
        
        control.rotate_shape(*self._get_axis_rotation())
        
        scale = self.scale + 5
        control.scale_shape(scale,scale,scale)
        
        control.color( self._get_color_for_axis() )
        
    def _set_axis_vectors(self, pose_axis = None):
        
                
        if not pose_axis:
            pose_axis = self._get_pose_axis()
        
        self._lock_axis_vector_attributes(False)
        
        cmds.setAttr('%s.axisRotateX' % self.pose_control, pose_axis[0])
        cmds.setAttr('%s.axisRotateY' % self.pose_control, pose_axis[1])
        cmds.setAttr('%s.axisRotateZ' % self.pose_control, pose_axis[2])
        
        twist_axis = self._get_twist_axis()
        
        cmds.setAttr('%s.axisTwistX' % self.pose_control, twist_axis[0])
        cmds.setAttr('%s.axisTwistY' % self.pose_control, twist_axis[1])
        cmds.setAttr('%s.axisTwistZ' % self.pose_control, twist_axis[2])
        
        self._lock_axis_vector_attributes(True)
        
    def _lock_axis_vector_attributes(self, bool_value):
        axis = ['X','Y','Z']
        attributes = ['axisTwist', 'axisRotate']
        
        for a in axis:
            for attribute in attributes:
                cmds.setAttr('%s.%s%s' % (self.pose_control, attribute, a), l = bool_value)
        
    def _create_attributes(self, control):
        super(PoseCone, self)._create_attributes(control)
    
        cmds.addAttr(control, ln = 'translation', at = 'double', k = True, dv = 1)
        cmds.addAttr(control, ln = 'rotation', at = 'double', k = True, dv = 1)
        
        cmds.addAttr(control, ln = 'twistOffOn', at = 'double', k = True, dv = 1, min = 0, max = 1)
        cmds.addAttr(control, ln = 'maxDistance', at = 'double', k = True, dv = 1)
        cmds.addAttr(control, ln = 'maxAngle', at = 'double', k = True, dv = 90)
        cmds.addAttr(control, ln = 'maxTwist', at = 'double', k = True, dv = 90)
        
        title = attr.MayaEnumVariable('AXIS_ROTATE')
        title.create(control)
        
        pose_axis = self._get_pose_axis()
        
        cmds.addAttr(control, ln = 'axisRotateX', at = 'double', k = True, dv = pose_axis[0])
        cmds.addAttr(control, ln = 'axisRotateY', at = 'double', k = True, dv = pose_axis[1])
        cmds.addAttr(control, ln = 'axisRotateZ', at = 'double', k = True, dv = pose_axis[2])
        
        title = attr.MayaEnumVariable('AXIS_TWIST')
        title.create(control)
        
        twist_axis = self._get_twist_axis()
        
        cmds.addAttr(control, ln = 'axisTwistX', at = 'double', k = True, dv = twist_axis[0])
        cmds.addAttr(control, ln = 'axisTwistY', at = 'double', k = True, dv = twist_axis[1])
        cmds.addAttr(control, ln = 'axisTwistZ', at = 'double', k = True, dv = twist_axis[2])
        
        cmds.addAttr(control, ln = 'joint', dt = 'string')
        
        if self.transform:
            cmds.setAttr('%s.joint' % control, self.transform, type = 'string')
        
        cmds.addAttr(control, ln = 'parent', dt = 'string')
        
        self._lock_axis_vector_attributes(True)
         
    #--- math nodes 
        
    def _create_distance_between(self):
        distance_between = self._create_node('distanceBetween')
        
        cmds.connectAttr('%s.worldMatrix' % self.pose_control, 
                         '%s.inMatrix1' % distance_between)
            
        if self.transform:
            cmds.connectAttr('%s.worldMatrix' % self.transform, 
                             '%s.inMatrix2' % distance_between)
        
        return distance_between
        
    def _create_multiply_matrix(self, moving_transform, pose_control):
        multiply_matrix = self._create_node('multMatrix')
        
        if moving_transform:
            cmds.connectAttr('%s.worldMatrix' % moving_transform, '%s.matrixIn[0]' % multiply_matrix)
        cmds.connectAttr('%s.worldInverseMatrix' % pose_control, '%s.matrixIn[1]' % multiply_matrix)
        
        return multiply_matrix
        
    def _create_vector_matrix(self, multiply_matrix, vector):
        vector_product = self._create_node('vectorProduct')
        
        cmds.connectAttr('%s.matrixSum' % multiply_matrix, '%s.matrix' % vector_product)
        cmds.setAttr('%s.input1X' % vector_product, vector[0])
        cmds.setAttr('%s.input1Y' % vector_product, vector[1])
        cmds.setAttr('%s.input1Z' % vector_product, vector[2])
        cmds.setAttr('%s.operation' % vector_product, 3)
        
        return vector_product
        
    def _create_angle_between(self, vector_product, vector):
        angle_between = self._create_node('angleBetween')
        
        cmds.connectAttr('%s.outputX' % vector_product, '%s.vector1X' % angle_between)
        cmds.connectAttr('%s.outputY' % vector_product, '%s.vector1Y' % angle_between)
        cmds.connectAttr('%s.outputZ' % vector_product, '%s.vector1Z' % angle_between)
        
        cmds.setAttr('%s.vector2X' % angle_between, vector[0])
        cmds.setAttr('%s.vector2Y' % angle_between, vector[1])
        cmds.setAttr('%s.vector2Z' % angle_between, vector[2])
        
        return angle_between
        
    def _remap_value_angle(self, angle_between):
        remap = self._create_node('remapValue', 'angle')
        
        cmds.connectAttr('%s.angle' % angle_between, '%s.inputValue' % remap)
        
        cmds.setAttr('%s.value[0].value_Position' % remap, 0)
        cmds.setAttr('%s.value[0].value_FloatValue' % remap, 1)
        
        cmds.setAttr('%s.value[1].value_Position' % remap, 1)
        cmds.setAttr('%s.value[1].value_FloatValue' % remap, 0)
        
        cmds.setAttr('%s.inputMax' % remap, 180)
        
        return remap
    
    def _remap_value_distance(self, distance_between):
        
        remap = self._create_node('remapValue', 'distance')
        
        cmds.connectAttr('%s.distance' % distance_between, '%s.inputValue' % remap)
        
        cmds.setAttr('%s.value[0].value_Position' % remap, 0)
        cmds.setAttr('%s.value[0].value_FloatValue' % remap, 1)
        
        cmds.setAttr('%s.value[1].value_Position' % remap, 1)
        cmds.setAttr('%s.value[1].value_FloatValue' % remap, 0)
        
        cmds.setAttr('%s.inputMax' % remap, 1)
        
        return remap        
    
    def _fix_remap_value_distance(self):
        
        input_value = attr.get_attribute_input('%s.translation' % self.pose_control, node_only = True)
        key_input = attr.get_attribute_input('%s.input' % input_value)
        
        if key_input:
            return
                    
        if not cmds.objExists('remapValue3'):
            distance = self._get_named_message_attribute('distanceBetween1')
            
            remap = self._remap_value_distance(distance)
            
            input_value = attr.get_attribute_input('%s.translation' % self.pose_control, node_only = True)
            
            if input_value:
                
                if cmds.nodeType(input_value).startswith('animCurve'):
                    cmds.connectAttr('%s.outValue' % remap, '%s.input' % input_value)
        
    def _multiply_remaps(self, remap, remap_twist):
        
        multiply = self._create_node('multiplyDivide')
        
        cmds.connectAttr('%s.outValue' % remap, '%s.input1X' % multiply)
        cmds.connectAttr('%s.outValue' % remap_twist, '%s.input2X' % multiply)
        
        blend = self._create_node('blendColors')
        
        cmds.connectAttr('%s.outputX' % multiply, '%s.color1R' % blend)
        cmds.connectAttr('%s.outValue' % remap, '%s.color2R' % blend)
        
        
        cmds.connectAttr('%s.twistOffOn' % self.pose_control, ' %s.blender' % blend)
        
        return blend
    
    def _create_pose_math_nodes(self, multiply_matrix, axis):
        vector_product = self._create_vector_matrix(multiply_matrix, axis)
        angle_between = self._create_angle_between(vector_product, axis)
        
        if self._get_pose_axis() == axis:
            cmds.connectAttr('%s.axisRotateX' % self.pose_control, '%s.input1X' % vector_product)
            cmds.connectAttr('%s.axisRotateY' % self.pose_control, '%s.input1Y' % vector_product)
            cmds.connectAttr('%s.axisRotateZ' % self.pose_control, '%s.input1Z' % vector_product)
            
            cmds.connectAttr('%s.axisRotateX' % self.pose_control, '%s.vector2X' % angle_between)
            cmds.connectAttr('%s.axisRotateY' % self.pose_control, '%s.vector2Y' % angle_between)
            cmds.connectAttr('%s.axisRotateZ' % self.pose_control, '%s.vector2Z' % angle_between)
            
        if self._get_twist_axis() == axis:
            cmds.connectAttr('%s.axisTwistX' % self.pose_control, '%s.input1X' % vector_product)
            cmds.connectAttr('%s.axisTwistY' % self.pose_control, '%s.input1Y' % vector_product)
            cmds.connectAttr('%s.axisTwistZ' % self.pose_control, '%s.input1Z' % vector_product)
            
            cmds.connectAttr('%s.axisTwistX' % self.pose_control, '%s.vector2X' % angle_between)
            cmds.connectAttr('%s.axisTwistY' % self.pose_control, '%s.vector2Y' % angle_between)
            cmds.connectAttr('%s.axisTwistZ' % self.pose_control, '%s.vector2Z' % angle_between)            
        
        remap = self._remap_value_angle(angle_between)
        
        return remap
        
    def _create_pose_math(self, moving_transform, pose_control):
        multiply_matrix = self._create_multiply_matrix(moving_transform, pose_control)
        
        pose_axis = self._get_pose_axis()
        twist_axis = self._get_twist_axis()
        
        remap = self._create_pose_math_nodes(multiply_matrix, pose_axis)
        remap_twist = self._create_pose_math_nodes(multiply_matrix, twist_axis)
        
        blend = self._multiply_remaps(remap, remap_twist)
        
        cmds.connectAttr('%s.maxAngle' % pose_control, '%s.inputMax' % remap)
        cmds.connectAttr('%s.maxTwist' % pose_control, '%s.inputMax' % remap_twist)
        
        distance = self._create_distance_between()
        remap_distance = self._remap_value_distance(distance)
        
        cmds.connectAttr('%s.maxDistance' % self.pose_control, '%s.inputMax' % remap_distance)
        
        self._key_output('%s.outValue' % remap_distance, '%s.translation' % self.pose_control)
        self._key_output('%s.outputR' % blend, '%s.rotation' % self.pose_control)
        
    def _key_output(self, output_attribute, input_attribute, values = [0,1]):
        
        cmds.setDrivenKeyframe(input_attribute,
                               cd = output_attribute, 
                               driverValue = values[0], 
                               value = 0, 
                               itt = 'linear', 
                               ott = 'linear')
    
        cmds.setDrivenKeyframe(input_attribute,
                               cd = output_attribute,  
                               driverValue = values[1], 
                               value = 1, 
                               itt = 'linear', 
                               ott = 'linear')  
    
    def _multiply_weight(self):
        
        multiply = self._create_node('multiplyDivide')
        
        cmds.connectAttr('%s.translation' % self.pose_control, '%s.input1X' % multiply)
        cmds.connectAttr('%s.rotation' % self.pose_control, '%s.input2X' % multiply)
        
        multiply_offset = self._create_node('multiplyDivide')
        
        cmds.connectAttr('%s.outputX' % multiply, '%s.input1X' % multiply_offset)
        cmds.connectAttr('%s.enable' % self.pose_control, '%s.input2X' % multiply_offset)
        
        
        input_attr = attr.get_attribute_input('%s.weight' % self.pose_control)
        
        if not input_attr:
            cmds.connectAttr('%s.outputX' % multiply_offset, '%s.weight' % self.pose_control)

    def _get_parent_constraint(self):
        constraint = space.ConstraintEditor()
        constraint_node = constraint.get_constraint(self.pose_control, 'parentConstraint')
        
        return constraint_node 
        
    def set_axis(self, axis_name):
        """
        Set the axis the cone reads from. 'X','Y','Z'.
        """
        self.axis = axis_name
        self._position_control()
        
        self._set_axis_vectors()
        
    def get_transform(self):
        """
        Get the connected/stored transform on a cone.
        
        Returns:
            str: The name of the transform.
        """
        
        matrix = self._get_named_message_attribute('multMatrix1')
        
        transform = attr.get_attribute_input('%s.matrixIn[0]' % matrix, True)
        
        if not transform:
            transform = cmds.getAttr('%s.joint' % self.pose_control)
        
        self.transform = transform
        
        return transform
    
    def set_transform(self, transform, set_string_only = False):
        """
        Cone poses need a transform. 
        This helps them to know when to turn on.
        
        Args:
            transform (str): The name of a transform to move the cone.
            set_string_only (bool): Wether to connect the transform into the pose or just set its attribute on the cone.
        """
        transform = transform.replace(' ', '_')
        
        self.transform = transform
        
        if not self.pose_control or not cmds.objExists(self.pose_control):
            return
        
        if not cmds.objExists('%s.joint' % self.pose_control):
            cmds.addAttr(self.pose_control, ln = 'joint', dt = 'string')
        
        cmds.setAttr('%s.joint' % self.pose_control, transform, type = 'string')
        
        if not set_string_only:
            matrix = self._get_named_message_attribute('multMatrix1')
            distance = self._get_named_message_attribute('distanceBetween1')
        
            if not cmds.isConnected('%s.worldMatrix' % transform, '%s.matrixIn[0]' % matrix):
                cmds.connectAttr('%s.worldMatrix' % transform, '%s.matrixIn[0]' % matrix)
            if not cmds.isConnected('%s.worldMatrix' % transform, '%s.inMatrix2' % distance):
                cmds.connectAttr('%s.worldMatrix' % transform, '%s.inMatrix2' % distance)
                

    def get_parent(self):
        """
        Get the connected/stored parent on a cone.
        
        Returns:
            str: The name of the parent.
        """
        
        constraint_node = self._get_parent_constraint()
        
        parent = None
        
        if constraint_node:
            constraint = space.ConstraintEditor()
            targets = constraint.get_targets(constraint_node)
            if targets:
                parent = targets[0]
        
        if not parent:
            parent = cmds.getAttr('%s.parent' % self.pose_control)
        
        return parent 

    def set_parent(self, parent, set_string_only = False):
        """
        Cone poses need a parent. 
        This helps them to turn on only when their transform moves.
        
        Args:
            parent (str): The name of a transform above the cone.
            set_string_only (bool): Wether to connect the parent into the pose or just set its attribute on the cone.
        """
        
        if not cmds.objExists('%s.parent' % self.pose_control):
            cmds.addAttr(self.pose_control, ln = 'parent', dt = 'string')
            
        if not parent:
            parent = ''
        
        cmds.setAttr('%s.parent' % self.pose_control, parent, type = 'string')
    
        if not set_string_only:
            
            constraint = self._get_parent_constraint()
            
            if constraint:
                cmds.delete(constraint)    
            
            if parent:
                cmds.parentConstraint(parent, self.pose_control, mo = True)
    
    def rematch_cone_to_joint(self):
        
        constraint = self._get_parent_constraint()
        parent = None
        
        if constraint:
            
            const_editor = space.ConstraintEditor()
            parent = const_editor.get_targets(constraint)
            
            cmds.delete(constraint)
            
        transform = self.get_transform()
            
        space.MatchSpace(transform, self.pose_control).translation_rotation()
        
        if parent:
            cmds.parentConstraint(parent, self.pose_control, mo = True)
    
    def detach(self):
        
        self._fix_remap_value_distance()
        
        super(PoseCone, self).detach()
        
        parent = self.get_parent()
        self.set_parent(parent, True)
        
        transform = self.get_transform()
        self.set_transform(transform, True)
        
        constraint = self._get_parent_constraint()
        if constraint:
            cmds.delete(constraint)
        
        outputs = self.disconnect_weight_outputs()
        
        self._show_meshes()
        
        return outputs
        
    def attach(self, outputs = None):
        
        super(PoseCone, self).attach(outputs)
        
        transform = self.get_transform()
        parent = self.get_parent()
        
        self.set_transform(transform)
        self.set_parent(parent)
        
        if outputs:
            self.reconnect_weight_outputs(outputs)
        
        self._fix_remap_value_distance()
        
        self.goto_pose()
        self.rematch_cone_to_joint()
        
        self._hide_meshes()
        
        if self.sub_detach_dict:
            
            for key in self.sub_detach_dict:
                pose = get_pose_instance(key)
                pose.attach(self.sub_detach_dict[pose])
                
            self.sub_detach_dict = {}
            
    def create(self):
        
        pose_control = super(PoseCone, self).create()
        
        self._create_pose_math(self.transform, pose_control)
        self._multiply_weight()
        
        self.pose_control = pose_control
        
        if self.transform:
            axis = space.get_axis_letter_aimed_at_child(self.transform)
            if axis:
                if axis.startswith('-'):
                    axis = axis[1]
                self.set_axis(axis)
        
        return pose_control
    
    def goto_pose(self):
        
        super(PoseCone, self).goto_pose()
        
        transform = self.get_transform()
        
        try:
            constraint = space.ConstraintEditor()
            
            if not constraint.has_constraint(transform):
                space.MatchSpace(self.pose_control, transform).translation_rotation()
                
        except:
            pass
        
        #this is needed or poses don't come in properly when importing
        cmds.dgdirty(a = True)
        #cmds.refresh()
    
    def mirror(self):
        """
        Mirror a pose to a corresponding R side pose.
        
        For example
            If self.pose_control = pose_arm_L, there must be a corresponding pose_arm_R.
            The pose at pose_arm_R must be a mirrored pose of pose_arm_L.
        """
                
        count = self.get_mesh_count()
        
        for inc in xrange(0, count):
            mesh = self.get_mesh(inc)
            self.visibility_off(mesh, view_only = False)
        
        other_pose_instance = self._get_mirror_pose_instance()
        
        other_target_meshes = []
        input_meshes = {}
        
        for inc in xrange(0, self._get_mesh_count()):
            
            mesh = self.get_mesh(inc)
            target_mesh = self.get_target_mesh(mesh)
            
            if target_mesh == None:
                continue
            
            other_target_mesh, other_target_mesh_duplicate = self._create_mirror_mesh(target_mesh)
            
            if not other_target_mesh:
                continue
                
            input_meshes[other_target_mesh] = other_target_mesh_duplicate
            other_target_meshes.append(other_target_mesh)
        
        if not other_pose_instance.pose_control:
            store = rigs_util.StoreControlData(self.pose_control)
            
            if self.left_right:
                side = 'L'
            if not self.left_right:
                side = 'R'
            
            store.eval_mirror_data(side)
            
            transform = self.get_transform()
            other_transform = self._replace_side(transform, self.left_right)
            
            other_pose_instance.set_transform(other_transform)
            other_pose_instance.create()
            
            parent = cmds.listRelatives(self.pose_control, p = True)
            if parent:
                parent = parent[0]
                other_parent = self._replace_side(parent, self.left_right)
                if other_parent and cmds.objExists(other_parent):
                    cmds.parent(other_pose_instance.pose_control, other_parent)
                
            self.other_pose_exists = True
        else:
            other_pose_instance.goto_pose()
        
        twist_on_value = cmds.getAttr('%s.twistOffOn' % self.pose_control)
        distance_value = cmds.getAttr('%s.maxDistance' % self.pose_control)
        angle_value = cmds.getAttr('%s.maxAngle' % self.pose_control)
        maxTwist_value = cmds.getAttr('%s.maxTwist' % self.pose_control)
        
        lock_state = attr.LockNodeState(other_pose_instance.pose_control)
        lock_state.unlock()
        
        cmds.setAttr('%s.twistOffOn' % other_pose_instance.pose_control, twist_on_value)
        cmds.setAttr('%s.maxDistance' % other_pose_instance.pose_control, distance_value)
        cmds.setAttr('%s.maxAngle' % other_pose_instance.pose_control, angle_value)
        cmds.setAttr('%s.maxTwist' % other_pose_instance.pose_control, maxTwist_value)
        
        axis_x = cmds.getAttr('%s.axisRotateX' % self.pose_control)
        axis_y = cmds.getAttr('%s.axisRotateY' % self.pose_control)
        axis_z = cmds.getAttr('%s.axisRotateZ' % self.pose_control)
        axis = [axis_x, axis_y, axis_z]
        
        axis_letter = space.get_vector_axis_letter(axis)
        other_pose_instance.set_axis(axis_letter )
        
        lock_state.restore_initial()
        
        for mesh in other_target_meshes:
            
            index = other_pose_instance.get_target_mesh_index(mesh)
            
            if index == None:
                
                other_pose_instance.add_mesh(mesh, toggle_vis = False)
                
        for mesh in other_target_meshes:
            
            index = other_pose_instance.get_target_mesh_index(mesh)
            
            input_mesh = other_pose_instance.get_mesh(index)
            
            if not input_mesh:
                continue
            
            fix_mesh = input_meshes[mesh]
            
            input_mesh_name = core.get_basename(input_mesh)
            
            cmds.blendShape(fix_mesh, input_mesh, foc = True, w = [0,1], n = 'blendshape_%s' % input_mesh_name)
            
            other_pose_instance.create_blend(index, False)
            
            #turning on inheritsTransform to avoid a warning message.
            cmds.setAttr('%s.inheritsTransform' % input_mesh, 1)
            
            cmds.delete(input_mesh, ch = True)
            cmds.delete(fix_mesh)
            
            self.visibility_off(input_mesh, view_only = True)
        
        return other_pose_instance.pose_control

    

        
    
class PoseTimeline(PoseNoReader):
    """
    This type of pose reads a time on the timeline.
    """

    def _pose_type(self):
        return 'timeline'
    
    def _create_attributes(self, control):
        
        super(PoseTimeline, self)._create_attributes(control)
        
        pose_time = attr.MayaNumberVariable('timePosition')
        
        pose_time.create(control)
        
    def goto_pose(self):
        """
        Go to the time on the timeline where the pose was created.
        """
        current_time = cmds.getAttr('%s.timePosition' % self.pose_control)
        cmds.currentTime(current_time)
        
    def shift_time(self, value):
        
        keyframe = anim.get_keyframe('%s.weight' % self.pose_control)
        
        if not keyframe:
            return
        
        old_value = cmds.getAttr('%s.timePosition' % self.pose_control)
        
        delta = value - old_value
         
        cmds.keyframe( keyframe, e = True, iub = True, r = True, o = 'over', tc = delta)
        cmds.currentTime(value)
        
        cmds.setAttr('%s.timePosition' % self.pose_control, value)
        
    def create(self):
        
        top_group = self._create_top_group()
        
        pose_control = self._create_pose_control()
        self.pose_control = pose_control
        
        cmds.parent(pose_control, top_group)
        
        current_time = cmds.currentTime(q = True)
        
        cmds.setAttr('%s.timePosition' % self.pose_control, current_time)
        
        cmds.setKeyframe('%s.weight' % pose_control, t = current_time, v = 1)
        cmds.setKeyframe('%s.weight' % pose_control, t = (current_time-5), v = 0)
        cmds.setKeyframe('%s.weight' % pose_control, t = (current_time+5), v = 0)
        
        return pose_control
        
        
corrective_type = { 'cone' : PoseCone,
                     'no reader' : PoseNoReader,
                     'timeline' : PoseTimeline,
                     'group' : PoseGroup,
                     'combo' : PoseCombo }