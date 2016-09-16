# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

import re
import string
import traceback

import vtool.util
import api

if vtool.util.is_in_maya():
    import maya.cmds as cmds
    import maya.mel as mel
    
import core
import attr
import space
import geo
import anim

class XformTransfer(object):
    """
    Wrap deform joints from one mesh to another.
    """
    def __init__(self, ):
        
        self.source_mesh = None
        self.target_mesh = None
        self.particles = None
        
    def _match_particles(self, scope):        
        
        xforms = []
        for transform in self.scope:
            
            position = cmds.xform(transform, q = True, ws = True, t = True)
            
            xforms.append(position)
        
        self.particles = cmds.particle(p = xforms)[0]
            
    def _wrap_particles(self):
        if self.particles and self.source_mesh:
            
            cmds.select([self.particles,self.source_mesh],replace = True)
            mel.eval('source performCreateWrap.mel; performCreateWrap 0;')
            
            wrap = find_deformer_by_type(self.particles, 'wrap')
            
            cmds.setAttr('%s.exclusiveBind' % wrap, 0)
            cmds.setAttr('%s.autoWeightThreshold' % wrap, 0)
            cmds.setAttr('%s.maxDistance' % wrap, 0)
            cmds.setAttr('%s.falloffMode' % wrap, 0)
    
    def _blend_to_target(self):
        cmds.blendShape(self.target_mesh, self.source_mesh, weight = [0,1], origin = 'world')        
            
    def _move_to_target(self):
        for inc in xrange(0, len(self.scope)):
            position = cmds.pointPosition('%s.pt[%s]' % (self.particles,inc))
            transform = self.scope[inc]
            
            if cmds.nodeType(transform) == 'joint':
                cmds.move(position[0], position[1],position[2], '%s.scalePivot' % transform, '%s.rotatePivot' % transform, a = True)
                
            if not cmds.nodeType(transform) == 'joint' and cmds.nodeType(transform) == 'transform':
                cmds.move(position[0], position[1],position[2], transform, a = True)
                        
    def _cleanup(self):
        cmds.delete([self.particles,self.source_mesh])
            
    def store_relative_scope(self, parent):    
        """
        Set all transforms under parent.
        
        Args:
            parent (str): The name of a parent transform.
        """
        self.scope = cmds.listRelatives(parent, allDescendents = True, type = 'transform')
        self.scope.append(parent)
        
    def set_scope(self, scope):
        """
        Set the transforms to work on.
        
        Args:
            scope (list): Names of transforms.
        """
        self.scope = scope
            
    def set_source_mesh(self, name):
        """
        Source mesh must match point order of target mesh.
        """
        self.source_mesh = name
        
    def set_target_mesh(self, name):
        """
        Target mesh must match point order of source mesh.
        """
        self.target_mesh = name
        
    def run(self):
        if not self.scope:
            return
        
        if not cmds.objExists(self.source_mesh):
            return
    
        if not cmds.objExists(self.target_mesh):
            return
            
        self.source_mesh = cmds.duplicate(self.source_mesh)[0]
        self._match_particles(self.scope)
        self._wrap_particles()
        self._blend_to_target()
        self._move_to_target()
        self._cleanup()

class ClusterObject(object):
    """
    Convenience class for clustering objects.
    """
    def __init__(self, geometry, name):
        self.geometry = geometry
        self.join_ends = False
        self.name = name
        self.cvs = []
        self.cv_count = 0
        self.clusters = []
        self.handles = []
        
    def _create_cluster(self, cvs):
        return create_cluster(cvs, self.name)
        
    def get_cluster_list(self):
        """
        Returns:
            list: The names of cluster deformers.
        """
        return self.clusters
    
    def get_cluster_handle_list(self):
        """
        Returns:
            list: The name of cluster handles.
        """
        return  self.handles
        
    def create(self):
        """
        Create the clusters.
        """
        self._create()

class ClusterSurface(ClusterObject):
    """
    Convenience for clustering a surface.
    """
    def __init__(self, geometry, name):
        super(ClusterSurface, self).__init__(geometry, name)
        
        self.join_ends = False
        self.join_both_ends = False
        self.first_cluster_pivot_at_start = True
        self.last_cluster_pivot_at_end = True
        
        self.maya_type = None
        
        if core.has_shape_of_type(self.geometry, 'nurbsCurve'):
            self.maya_type = 'nurbsCurve'
        if core.has_shape_of_type(self.geometry, 'nurbsSurface'):
            self.maya_type = 'nurbsSurface'
            
        self.cluster_u = True
    
    def _create_start_and_end_clusters(self):
        
        start_cvs = None
        end_cvs = None
        start_position = None
        end_position = None
        
        if self.maya_type == 'nurbsCurve':
            
            start_cvs = '%s.cv[0:1]' % self.geometry
            end_cvs = '%s.cv[%s:%s]' % (self.geometry,self.cv_count-2, self.cv_count-1)
            
            start_position = cmds.xform('%s.cv[0]' % self.geometry, q = True, ws = True, t = True)
            end_position = cmds.xform('%s.cv[%s]' % (self.geometry,self.cv_count-1), q = True, ws = True, t = True)
            
            
        if self.maya_type == 'nurbsSurface':
        
            if self.cluster_u:
                cv_count_u = len(cmds.ls('%s.cv[*][0]' % self.geometry, flatten = True))
                index1 = '[0:*][0:1]'
                index2 = '[0:*][%s:%s]' % (self.cv_count-2, self.cv_count-1)
                index3 = '[%s][0]' % (cv_count_u - 1)
                index4 = '[0][%s]' % (self.cv_count-1)
                index5 = '[%s][%s]' % (cv_count_u, self.cv_count-1) 
            if not self.cluster_u:
                cv_count_v = len(cmds.ls('%s.cv[0][*]' % self.geometry, flatten = True))
                index1 = '[0:1][0:*]'
                index2 = '[%s:%s][0:*]' % (self.cv_count-2, self.cv_count-1)
                index3 = '[0][%s]' % (cv_count_v - 1)
                index4 = '[%s][0]' % (self.cv_count-1)
                index5 = '[%s][%s]' % (self.cv_count-1,cv_count_v)                
            
            
            start_cvs = '%s.cv%s' % (self.geometry, index1)
            end_cvs = '%s.cv%s' % (self.geometry,index2)
            
            p1 = cmds.xform('%s.cv[0][0]' % self.geometry, q = True, ws = True, t = True)
            p2 = cmds.xform('%s.cv%s' % (self.geometry, index3), q = True, ws = True, t = True)
            
            start_position = vtool.util.get_midpoint(p1, p2)
            
            p1 = cmds.xform('%s.cv%s' % (self.geometry, index4), q = True, ws = True, t = True)
            p2 = cmds.xform('%s.cv%s' % (self.geometry, index5), q = True, ws = True, t = True)
            
            end_position = vtool.util.get_midpoint(p1, p2)
        
        cluster, handle = self._create_cluster(start_cvs)
        
        self.clusters.append(cluster)
        self.handles.append(handle)
        
        if self.first_cluster_pivot_at_start:
            cmds.xform(handle, ws = True, rp = start_position, sp = start_position)
        
        last_cluster, last_handle = self._create_cluster(end_cvs)
        
        if self.last_cluster_pivot_at_end:
            cmds.xform(last_handle, ws = True, rp = end_position, sp = end_position)

        
        return last_cluster, last_handle
    
    def _create_start_and_end_joined_cluster(self):
        
        start_cvs = None
        end_cvs = None
        
        if self.maya_type == 'nurbsCurve':
            start_cvs = '%s.cv[0:1]' % self.geometry
            end_cvs = '%s.cv[%s:%s]' % (self.geometry,self.cv_count-2, self.cv_count-1)
            
        if self.maya_type == 'nurbsSurface':
            
            if self.cluster_u:
                index1 = '[0:*][0]'
                index2 = '[0:*][%s]' % (self.cv_count-1)

            if not self.cluster_u:
                index1 = '[0][0:*]'
                index2 = '[%s][0:*]' % (self.cv_count-1)
            
            start_cvs = '%s.cv%s' % (self.geometry, index1)
            end_cvs = '%s.cv%s' % (self.geometry, index2)
        
        cmds.select([start_cvs, end_cvs])
        cvs = cmds.ls(sl = True)
            
        cluster, handle = self._create_cluster(cvs)
        self.clusters.append(cluster)
        self.handles.append(handle)
        
    def _create(self):
        
        self.cvs = cmds.ls('%s.cv[*]' % self.geometry, flatten = True)
        
        if self.maya_type == 'nurbsCurve':
            self.cv_count = len(self.cvs)
        if self.maya_type == 'nurbsSurface':
            
            if self.cluster_u:
                index = '[0][*]'
            if not self.cluster_u:
                index = '[*][0]'
                            
            self.cv_count = len(cmds.ls('%s.cv%s' % (self.geometry, index), flatten = True))
        
        start_inc = 0
        
        cv_count = self.cv_count
        
        if self.join_ends:
            
            if not self.join_both_ends:
                
                last_cluster, last_handle = self._create_start_and_end_clusters()
            
            if self.join_both_ends:
                
                self._create_start_and_end_joined_cluster()
                
            cv_count = len(self.cvs[2:self.cv_count])
            start_inc = 2
            
        for inc in xrange(start_inc, cv_count):
            
            if self.maya_type == 'nurbsCurve':
                cv = '%s.cv[%s]' % (self.geometry, inc)
            if self.maya_type == 'nurbsSurface':
                
                if self.cluster_u:
                    index = '[*][%s]' % inc
                if not self.cluster_u:
                    index = '[%s][*]' % inc
                
                cv = '%s.cv%s' % (self.geometry, index)
            
            cluster, handle = self._create_cluster( cv )
            
            self.clusters.append(cluster)
            self.handles.append(handle)
        
        if self.join_ends and not self.join_both_ends:
            self.clusters.append(last_cluster)
            self.handles.append(last_handle)
        
        
        return self.clusters
    
    def set_join_ends(self, bool_value):
        """
        Clusters on the ends of the surface take up 2 cvs.
        
         Args:
            bool_value (bool): Wether 2 cvs at the start have one cluster, and 2 cvs on the end have one cluster.
        """
        self.join_ends = bool_value
        
    def set_join_both_ends(self, bool_value):
        """
        Clusters on the ends of the surface are joined together.
        
        Args:
            bool_value (bool): Wether to join the ends of the surface.
        """
        self.join_both_ends = bool_value
        
    def set_last_cluster_pivot_at_end(self, bool_value):
        """
        Set the last cluster pivot to the end of the curve.
        """
        
        self.last_cluster_pivot_at_end = bool_value

    def set_first_cluster_pivot_at_start(self, bool_value):
        """
        Set the last cluster pivot to the end of the curve.
        """
        
        self.first_cluster_pivot_at_start = bool_value
        
    def set_cluster_u(self, bool_value):
        """
        Args:
            bool_value (bool): Wether to cluster the u instead of the v spans.
        """
        self.cluster_u = bool_value
    

class ClusterCurve(ClusterSurface):
    """
    Convenience for clustering a curve. 
    """
    def _create_start_and_end_clusters(self):
        cluster, handle = self._create_cluster('%s.cv[0:1]' % self.geometry)
        
        self.clusters.append(cluster)
        self.handles.append(handle)
        
        position = cmds.xform('%s.cv[0]' % self.geometry, q = True, ws = True, t = True)
        cmds.xform(handle, ws = True, rp = position, sp = position)
        
        last_cluster, last_handle = self._create_cluster('%s.cv[%s:%s]' % (self.geometry,self.cv_count-2, self.cv_count-1) )
        
        position = cmds.xform('%s.cv[%s]' % (self.geometry,self.cv_count-1), q = True, ws = True, t = True)
        cmds.xform(last_handle, ws = True, rp = position, sp = position)
        
        return last_cluster, last_handle
        
    def _create(self):
        
        
        self.cvs = cmds.ls('%s.cv[*]' % self.geometry, flatten = True)
        
        self.cv_count = len(self.cvs)
        
        start_inc = 0
        
        cv_count = self.cv_count
        
        if self.join_ends:
            last_cluster, last_handle = self._create_start_and_end_clusters()
            
            cv_count = len(self.cvs[2:self.cv_count])
            start_inc = 2
            
        for inc in xrange(start_inc, cv_count):
            cluster, handle = self._create_cluster( '%s.cv[%s]' % (self.geometry, inc) )
            
            self.clusters.append(cluster)
            self.handles.append(handle)
    
        if self.join_ends:
            self.clusters.append(last_cluster)
            self.handles.append(last_handle)
        
        return self.clusters
    
    def set_cluster_u(self, bool_value):
        """
        Not available on curves.
        """
        
        vtool.util.warning('Can not set cluster u, there is only one direction for spans on a curve. To many teenage girls there was only One Direction for their musical tastes.')



class SplitMeshTarget(object):
    """
    Split a mesh target edits based on skin weighting.
    The target will be reverted back to the base mesh based on weight of the defined joints on weight mesh.
    Good for splitting blendshape targets.
    
    Usage
    
        split = SplitMeshTarget('smile')
        split.set_base_mesh('home_mesh')
        split.set_weight_mesh('weight_mesh')
        split.set_weight_joint( 'joint_weight_L', suffix = 'L')
        split.set_weight_joint( 'joint_weight_R', suffix = 'R')
        split.create()
        
        result = smileL and smileR meshes.
        
    Args:
        target_mesh (str): The name of a target mesh, eg. smile.
    """
    def __init__(self, target_mesh):
        self.target_mesh = target_mesh
        self.weighted_mesh = None
        self.base_mesh = None
        self.split_parts = []
        self.skip_target_rename = []
        
    def _get_center_fade_weights(self, mesh, other_mesh, fade_distance, positive):
        
        verts = cmds.ls('%s.vtx[*]' % mesh, flatten = True)
        
        values = []
        
        fade_distance = fade_distance/2.0
        inc = 0
        for vert in verts:
            """
            space_source = cmds.xform('%s.vtx[%s]' % (mesh,inc), q = True, t = True, )
            space_other = cmds.xform('%s.vtx[%s]' % (other_mesh,inc), q = True, t = True, )
            
            found_difference = False
            
            for inc in range(0, 3):
                if abs(space_source[inc])-abs(space_other[inc]) < 0.0001:
                    found_difference = True
                    break
               
            if not found_difference:
                values.append(1.0)
                continue
            """
            
            if fade_distance == 0:
                values.append(1.0)
                continue
            
            
            if fade_distance != 0:
                vert_position = cmds.xform(vert, q = True, ws = True, t = True)
                
                fade_distance = float(fade_distance)
                
                value = vert_position[0]/fade_distance
                
                if value > 1:
                    value = 1
                if value < -1:
                    value = -1
                
                if positive:
                    
                    if value >= 0:
                        value = vtool.util.set_percent_range(value, 0.5, 1)
                    
                    if value < 0:
                        value = abs(value)
                        value = vtool.util.set_percent_range(value, 0.5, 0)
                        
                if not positive:

                    if value >= 0:
                        value = vtool.util.set_percent_range(value, 0.5, 0)
                    
                    if value < 0:
                        value = abs(value)
                        value = vtool.util.set_percent_range(value, 0.5, 1)
                        
            inc += 1
            
            values.append(value)
            
        
        return values
    
    def _get_joint_weights(self, joint):
        skin_cluster = find_deformer_by_type(self.weighted_mesh, 'skinCluster')
        
        if not skin_cluster:
            return

        weights = get_skin_influence_weights(joint, skin_cluster)
        
        if weights == None:
            vtool.util.warning('Joint %s is not in skinCluster %s' % (joint, skin_cluster))
            return []
        
        return weights
    
    def set_weight_joint(self, joint, suffix = None, prefix = None, split_name = True):
        """
        Set the a joint to split the shape. Must be skinned to the weight mesh
        
        Args:
            joint (str): The name of the joint to take weighting from. Must be affecting weight mesh.
            suffix (str): Add string to the end of the target mesh name.
            prefix (str): Add string to the beginning of the target mesh name.
            split_name (bool): Wether to split the name based on "_" and add the suffix and prefix at each part. 
            eg. 'smile_cheekPuff' would become 'smileL_cheekPuffL' if suffix = 'L'
        """
        
        self.split_parts.append([joint, None, suffix, prefix, None, split_name, [None,None]])
        
    def set_weight_insert_index(self, joint, insert_index, insert_name, split_name = True):
        """
        Insert a string for the new target shape name.
        Needs to be tested!!
        
        Args:
            joint (str): The name of the joint to take weighting from. Must be affecting weight mesh.
            insert_index (int): The index on the string where the insert_name should be inserted.
            insert_name (str): The string to insert at insert_index.
            split_name (bool): Wether to split the name based on "_" and add the insert_name at  the insert_index.  
        """
        self.split_parts.append([joint, None,None,None, [insert_index, insert_name], split_name, [None,None]])
    
    def set_weight_joint_replace_end(self, joint, replace, split_name = True):
        """
        Replace the string at the end of the target name when splitting.
        Needs to be tested!!
        
        Args:
            joint (str): The name of the joint to take weighting from. Must be affecting weight mesh.
            replace (str): The string to replace the end with.
            split_name (bool): Weither to split the name based on "_"..  
        """
        
        self.split_parts.append([joint, replace, None, None, None, split_name, [None,None]])
        
    def set_weight_joint_insert_at_first_camel(self, joint, insert_value, split_name = True):
        
        self.split_parts.append([joint, insert_value, None, None, 'camel_start', split_name, [None, None]])

    def set_center_fade(self, fade_distance, positive,  suffix = None, prefix = None, split_name = True):
        """
        Args:
            fade_distance (float): The distance from the center that the target should fade off.
            positive (bool): Weither the fade off should start at positive or at negative.
            
        """
        self.split_parts.append([None, None, suffix, prefix, None, split_name, [fade_distance, positive]])
    
    def set_weighted_mesh(self, weighted_mesh):
        """
        Set the weight mesh, the mesh that the weight joints are affecting through a skin cluster.
        
        Args:
            weighted_mesh (str): The name of a mesh with a skin cluster.
        """
        self.weighted_mesh = weighted_mesh
        
    def set_skip_target_rename(self, list_of_targets):
        self.skip_target_rename = list_of_targets
    
    def set_base_mesh(self, base_mesh):
        """
        Set the base mesh. The target mesh will revert back to base mesh based on skin weighting.
        This is the mesh with points at their default positions.
        
        Args:
            base_mesh (str): The name of a mesh.
        """
        self.base_mesh = base_mesh
    
    def create(self):
        """
        Create the splits.
        
        Returns:
            list: The names of the new targets.
        """
        
        import blendshape
        
        
        if not core.is_unique(self.target_mesh):
            vtool.util.warning('%s target is not unique. Target not split.' % self.target_mesh)
            return
        
        if not self.base_mesh or not cmds.objExists(self.base_mesh):
            vtool.util.warning('%s base mesh does not exist to split off of.' % self.base_mesh)
            return
        
        
            
        
        if not self.target_mesh or not cmds.objExists(self.target_mesh):
            vtool.util.warning('%s target does not exist for splitting' % self.target_mesh)

        parent = cmds.listRelatives( self.target_mesh, p = True )
        if parent:
            parent = parent[0]

        targets = []
        
        vtool.util.show('Splitting target: %s' % self.target_mesh)
        
        
        bar = core.ProgressBar('Splitting target: %s' % self.target_mesh, (len(self.split_parts)+1) )
        
        for part in self.split_parts:
                        
            joint = part[0]
            replace = part[1]
            suffix = part[2]
            prefix = part[3]
            split_index = part[4]
            split_name_option = part[5]
            center_fade, positive_negative = part[6]
            
            if center_fade == None and not self.weighted_mesh:
                vtool.util.warning('Splitting with joints specified, but no weighted mesh specified.')
                continue
            
            if not split_index:
                split_index = [0,'']
            
            new_target = cmds.duplicate(self.base_mesh)[0]
            
            target_name = self.target_mesh
            
            if self.target_mesh.endswith('N'):
                target_name = self.target_mesh[:-1]
                
            last_number = vtool.util.get_trailing_number(target_name, as_string = True, number_count = 2)
            
            if last_number:
                target_name = target_name[:-2]
                
            new_name = target_name
                
            if replace and type(replace) == list:
                
                new_name = re.sub(replace[0], replace[1], new_name)
                
            if suffix:
                new_name = '%s%s' % (new_name, suffix)
            if prefix:
                new_name = '%s%s' % (prefix, new_name)
            
            if last_number:
                new_name += last_number
            
            if self.target_mesh.endswith('N'):
                new_name += 'N'
            
            if split_name_option:
                
                split_name = self.target_mesh.split('_')
                
                if len(split_name) < 2:
                    split_name = [self.target_mesh] 
                
                new_names = []
                
                for name in split_name:
                    
                    if name in self.skip_target_rename:
                        
                        new_names.append(name)
                        
                    if not name in self.skip_target_rename:
                        sub_name = name
                        if name.endswith('N'):
                            sub_name = name[:-1]
                        
                        last_number = vtool.util.get_trailing_number(sub_name, as_string = True, number_count = 2)
                        
                        if last_number:
                            sub_name = sub_name[:-2]
                        
                        sub_new_name = sub_name
                        
                        if suffix:
                            sub_new_name = '%s%s' % (sub_new_name, suffix)
                        if prefix:
                            sub_new_name = '%s%s' % (prefix, sub_new_name)
                        
                        if last_number:
                            sub_new_name += last_number 
                        
                        if name.endswith('N'):
                            sub_new_name += 'N'
                        
                        if split_index == 'camel_start':
                            
                            search = re.search('[A-Z]', sub_new_name)
                            
                            if search:
                                camel_insert_index = search.start(0)
                                sub_new_name = sub_new_name[:camel_insert_index] + replace + sub_new_name[camel_insert_index:]
                                
                            if not search:
                                sub_new_name = sub_new_name + replace
                                
                        new_names.append(sub_new_name)
                        
                new_name = string.join(new_names, '_')
            
            if not split_name_option:
                
                if type(split_index) == list:
                    new_name = new_name[:split_index[0]] + split_index[1] + new_name[split_index[0]:]
                
                if split_index == 'camel_start':
                    search = re.search('[A-Z]', new_name)
                            
                    if search:
                        camel_insert_index = search.start(0)
                        new_name = new_name[:camel_insert_index] + replace + new_name[camel_insert_index:]
                        
                    if not search:
                        sub_new_name = sub_new_name + replace
            
            new_target = cmds.rename(new_target, new_name)    
            
            weights = []
            
            if center_fade != None:
                
                weights = self._get_center_fade_weights(self.base_mesh, self.target_mesh, center_fade, positive_negative)
                
            if center_fade == None:
                
                weights = self._get_joint_weights(joint)
                
            if not weights:
                continue
            
            blendshape_node = cmds.blendShape(self.target_mesh, new_target, w = [0,1])[0]
            blend = blendshape.BlendShape(blendshape_node)
            blend.set_weights(weights)
            
            cmds.delete(new_target, ch = True)
        
            current_parent = cmds.listRelatives(new_target, p = True)
        
            if current_parent:
                current_parent = current_parent[0]
        
            if parent and current_parent:
                if parent != current_parent:
                    cmds.parent(new_target, parent)
            
            targets.append(new_target)
            
            if vtool.util.break_signaled():
                break
            
            if bar.break_signaled():
                break
            
            bar.inc()
                
        bar.end()
        
        return targets
            
            
class TransferWeight(object):
    """
    Transfer weight has functions for dealing with moving weight from joints to other joints.
    
    Args:
        mesh (str): The name of the mesh that is skinned with joints.
    """
    def __init__(self, mesh):
        self.mesh = mesh

        self.vertices = []
        
        if type(mesh) == str or type(mesh) == unicode:        
            self.vertices = cmds.ls('%s.vtx[*]' % self.mesh, flatten = True)
        
        if type(mesh) == list:
            self.vertices = mesh
            
            self.mesh = mesh[0].split('.')[0]
            
        skin_deformer = self._get_skin_cluster(self.mesh)
        
        self.skin_cluster= None
        
        if skin_deformer:
            self.skin_cluster = skin_deformer
            
        
    def _get_skin_cluster(self, mesh):
        
        skin_deformer = find_deformer_by_type(mesh, 'skinCluster')
        
        return skin_deformer

    def _add_joints_to_skin(self, joints):
        
        influences = get_influences_on_skin(self.skin_cluster)
        
        for joint in joints:
            
            if not cmds.objExists(joint):
                continue
            
            if not joint in influences:
                cmds.skinCluster(self.skin_cluster, e = True, ai = joint, wt = 0.0, nw = 1)
        
    @core.undo_off
    def transfer_joint_to_joint(self, source_joints, destination_joints, source_mesh = None, percent =1):
        """
        Transfer the weights from source_joints into the weighting of destination_joints. 
        For example if I transfer joint_nose into joint_head, joint_head will lose its weights where joint_nose has overlapping weights. 
        Source joints will take over the weighting of destination_joints.  Source mesh must match the mesh TransferWeight(mesh).
        
        Args:
            source_joints (list): Joint names.
            destination_joints (list): Joint names.
            source_mesh (str): The name of the mesh were source_joints are weighted.  If None, algorithms assumes weighting is coming from the main mesh.
            percent (float): 0-1 value.  If value is 0.5, only 50% of source_joints weighting will be added to destination_joints weighting.
        """
        
        source_joints = vtool.util.convert_to_sequence(source_joints)
        destination_joints = vtool.util.convert_to_sequence(destination_joints)
        
        if vtool.util.get_env('VETALA_RUN') == 'True':
            if vtool.util.get_env('VETALA_STOP') == 'True':
                return
        
        if not self.skin_cluster:
            vtool.util.show('No skinCluster found on %s. Could not transfer.' % self.mesh)
            return
        
        if not destination_joints:
            vtool.util.warning('Destination joints do not exist.')
            return
            
        if not source_joints:
            vtool.util.warning('Source joints do not exist.')
            return
        
        if not source_mesh:
            source_mesh = self.mesh
            
        verts_source_mesh = []
            
        if source_mesh:
            verts_mesh = cmds.ls('%s.vtx[*]' % self.mesh, flatten = True)
            verts_source_mesh = cmds.ls('%s.vtx[*]' % source_mesh, flatten = True)    
            
            if len(verts_mesh) != len(verts_source_mesh):
                vtool.util.warning('%s and %s have different vert counts. Can not transfer weights.' % (self.mesh, source_mesh))
                return
        
        source_skin_cluster = self._get_skin_cluster(source_mesh)
        source_value_map = get_skin_weights(source_skin_cluster)
        destination_value_map = get_skin_weights(self.skin_cluster)
        
        self._add_joints_to_skin(destination_joints)
        
        joint_map = get_joint_index_map(source_joints, source_skin_cluster)
        destination_joint_map = get_joint_index_map(destination_joints, self.skin_cluster)
                            
        weighted_verts = []
        
        for influence_index in joint_map:
            
            if influence_index == None:
                continue
            
            for vert_index in range(0, len(verts_source_mesh)):
                
                int_vert_index = int(vtool.util.get_last_number(verts_source_mesh[vert_index]))
                
                if not source_value_map.has_key(influence_index):
                    continue
                
                value = source_value_map[influence_index][int_vert_index]
                
                if value > 0.0001:
                    if not int_vert_index in weighted_verts:
                        weighted_verts.append(int_vert_index)
        
        self._add_joints_to_skin(source_joints)
        
        lock_joint_weights(self.skin_cluster, destination_joints)
        
        vert_count = len(weighted_verts)
        
        if not vert_count:
            vtool.util.warning('Found no weights for specified influences on %s.' % source_skin_cluster)
            return
        
        bar = core.ProgressBar('transfer weight', vert_count)
        
        inc = 1
        
        for vert_index in weighted_verts:
            
            vert_name = '%s.vtx[%s]' % (self.mesh, vert_index)
        
            destination_value = 0
        
            for influence_index in destination_joint_map:
                
                if influence_index == None:
                    continue
                
                if destination_value_map.has_key(influence_index):
                    destination_value += destination_value_map[influence_index][vert_index]
                if not destination_value_map.has_key(influence_index):
                    destination_value += 0.0
            
            segments = []
            
            for influence_index in joint_map:
                
                if influence_index == None:
                    continue   
                
                joint = joint_map[influence_index]
                
                if not source_value_map.has_key(influence_index):
                    continue 
                
                value = source_value_map[influence_index][vert_index]
                value *= destination_value
                value *= percent
                
                if value > 1:
                    value = 1
                
                if value == 0:
                    continue
                
                segments.append((joint, value))
                
            if segments:
                cmds.skinPercent(self.skin_cluster, vert_name, r = False, transformValue = segments)

            bar.inc()
            
            bar.status('transfer new weight: %s of %s' % (inc, vert_count))
            
            if vtool.util.break_signaled():
                break
                        
            if bar.break_signaled():
                break
            
            inc += 1
            
        cmds.skinPercent(self.skin_cluster, self.vertices, normalize = True) 
        
        vtool.util.show('Done: %s transfer joint to joint.' % self.mesh)
        
        bar.end()
         
    @core.undo_off  
    def transfer_joints_to_new_joints(self, joints, new_joints, falloff = 1, power = 4, weight_percent_change = 1):
        """
        Transfer the weights from joints onto new_joints which have no weighting.
        For example, joint_arm could move its weights onto [joint_arm_tweak1, joint_arm_tweak2, joint_arm_tweak3]
        Weighting is assigned based on distance.
        
        Args:
            joints (list): Joint names to take weighting from.
            destination_joints (list): Joint names to add weighting to.
            falloff (float): The distance a vertex has to be from the joint before it has no priority.
            power (int): The power to multiply the distance by. It amplifies the distnace, so that if something is closer it has a higher value, and if something is further it has a lower value exponentially.
            weight_percent_change (float): 0-1 value.  If value is 0.5, only 50% of source_joints weighting will be added to destination_joints weighting.
        """
        joints = vtool.util.convert_to_sequence(joints)
        new_joints = vtool.util.convert_to_sequence(new_joints)
        
        if vtool.util.get_env('VETALA_RUN') == 'True':
            if vtool.util.get_env('VETALA_STOP') == 'True':
                return
        
        if not self.skin_cluster:
            vtool.util.warning('No skinCluster found on %s. Could not transfer.' % self.mesh)
            return
        
        joints = vtool.util.convert_to_sequence(joints)
        new_joints = vtool.util.convert_to_sequence(new_joints)
        
        if not new_joints:
            vtool.util.warning('Destination joints do not exist.')
            return
            
        if not joints:
            vtool.util.warning('Source joints do not exist.')
            return
        
        if not self.skin_cluster or not self.mesh:
            vtool.util.warning('No skin cluster or mesh supplied.')
            return
        
        lock_joint_weights(self.skin_cluster, joints)
        
        value_map = get_skin_weights(self.skin_cluster)
        influence_values = {}
        
        source_joint_weights = []
        influence_index_order = []
        
        for joint in joints:
            
            if not cmds.objExists(joint):
                vtool.util.warning('%s does not exist.' % joint)
                continue
            
            index = get_index_at_skin_influence(joint,self.skin_cluster)
            
            if index == None:
                continue
            
            if not value_map.has_key(index):
                continue
            
            influence_values[index] = value_map[index]
            source_joint_weights.append(value_map[index])
            influence_index_order.append(index)
            
        if not source_joint_weights:
            vtool.util.warning('Found no weights for specified influences on %s.' % self.skin_cluster)
            return
            
        verts = self.vertices
        
        weighted_verts = []
        weights = {}
        
        for influence_index in influence_index_order:
            
            for vert_index in xrange(0, len(verts)):
                
                int_vert_index = vtool.util.get_last_number(verts[vert_index])
                
                value = influence_values[influence_index][int_vert_index]
                
                if value > 0:
                    if not int_vert_index in weighted_verts:
                        weighted_verts.append(int_vert_index)
                    
                    if int_vert_index in weights:
                        weights[int_vert_index] += value
                        
                    if not int_vert_index in weights:
                        weights[int_vert_index] = value
        
        if not weighted_verts:
            vtool.util.warning('Found no weights for specified influences on %s.' % self.skin_cluster)
            return
        
        bar = core.ProgressBar('transfer weight', len(weighted_verts))
        
        inc = 1
        
        new_joint_count = len(new_joints)
        joint_count = len(joints)
        
        self._add_joints_to_skin(new_joints)
        joint_ids = get_skin_influences(self.skin_cluster, return_dict = True)
        
        cmds.setAttr('%s.normalizeWeights' % self.skin_cluster, 0)
        
        for vert_index in weighted_verts:
                    
            vert_name = '%s.vtx[%s]' % (self.mesh, vert_index)
            
            distances = space.get_distances(new_joints, vert_name)
            
            if not distances:
                vtool.util.warning('No distances found. Check your target joints.')
                bar.end()
                return
            
            found_weight = False
            
            joint_weight = {}
            
            """
            #check if the distance is almost zero on a new influence
            for distance_id in xrange(0, len(distances)):
                if distances[distance_id] <= 0.001:
                    joint_weight[new_joints[distance_id]] = 1
                    found_weight = True
                    break
            """
                       
            if not found_weight:
            
                smallest_distance = distances[0]
                distances_in_range = []
                
                for joint_index in xrange(0, new_joint_count):
                    if distances[joint_index] < smallest_distance:
                        smallest_distance = distances[joint_index]
                
                longest_distance = -1
                
                distances_away = []
                
                for joint_index in xrange(0, new_joint_count):
    
                    distance_away = distances[joint_index] - smallest_distance
                    
                    distances_away.append(distance_away)
                    
                    if distance_away > falloff:
                        continue
                    
                    distances_in_range.append(joint_index)
                    
                    if distances[joint_index] > longest_distance:
                        longest_distance = distances[joint_index]
                    
                total = 0.0
                
                inverted_distances = {}
                
                for joint_index in distances_in_range:
                    distance = distances_away[joint_index]
                    
                    distance_weight = distance/falloff
                        
                    inverted_distance = 1 - distance_weight
                    
                    inverted_distance = inverted_distance**power
                    
                    inverted_distances[joint_index] = inverted_distance
                    
                    total += inverted_distance
                
                for distance_inc in distances_in_range:
                    weight = inverted_distances[distance_inc]/total
                    joint_weight[new_joints[distance_inc]] = weight
            
            weight_value = weights[vert_index]
            
            for joint in joint_weight:
                
                joint_value = joint_weight[joint]
                value = weight_value * joint_value * weight_percent_change
                
                joint_index = joint_ids[joint]

                cmds.setAttr('%s.weightList[%s].weights[%s]' % (self.skin_cluster, vert_index, joint_index), value)
            
            if source_joint_weights:
                for joint_index in xrange(0, joint_count):
                    
                    if joint_index > len(source_joint_weights) - 1:
                        break
                    
                    change = 1 - weight_percent_change
                    
                    
                    value = source_joint_weights[joint_index]
                    value = value[vert_index] * change
                    
                    joint_id = influence_index_order[joint_index]
                    
                    cmds.setAttr('%s.weightList[%s].weights[%s]' % (self.skin_cluster, vert_index, joint_id), value)
            
            if not source_joint_weights:
                vtool.util.warning('No weighting on source joints.')
                            
            for joint_index in xrange(0, joint_count):
                change = 1 - weight_percent_change
                
                if joint_index > len(source_joint_weights) - 1:
                        break
                
                value = source_joint_weights[joint_index]
                value = value[vert_index] * change
                
                joint_id = influence_index_order[joint_index]
                
                cmds.setAttr('%s.weightList[%s].weights[%s]' % (self.skin_cluster, vert_index, joint_id), value)

            bar.inc()
            
            bar.status('transfer weight: %s of %s' % (inc, len(weighted_verts)))
            
            if vtool.util.break_signaled():
                break
            
            if bar.break_signaled():
                break
            
            inc += 1
        
        cmds.setAttr('%s.normalizeWeights' % self.skin_cluster, 1)
        
        bar.end()
        vtool.util.show('Done: %s transfer %s to %s.' % (self.mesh, joints, new_joints))
        
         
class AutoWeight2D(object):
    
    def __init__(self, mesh):
        self.mesh = mesh
        self.joints = []
        self.verts = []
        self.joint_vectors_2D = []
        self.vertex_vectors_2D = []
        
        self.multiplier_weights = []
        self.zero_weights = True
        
        self.orientation_transform = None
        
        self.orig_mesh = None
        self.orig_joints = None
        self.offset_group = None
        
        self.fade_cosine = False
        self.fade_smoothstep = False
        
        self.min_max = None
        
        self.prune_weights = []
        self.auto_joint_order = True
        
    def _create_offset_group(self):
        
        duplicate_mesh = cmds.duplicate(self.mesh)[0]
        
        attr.unlock_attributes(duplicate_mesh)
        
        self.offset_group = cmds.group(em = True, n = core.inc_name('offset_%s' % self.mesh))
            
        space.MatchSpace(self.orientation_transform, self.offset_group).translation_rotation()
        
        cmds.parent(duplicate_mesh, self.offset_group)
        
        duplicate_joints = []
        
        for joint in self.joints:
            dup_joint = cmds.duplicate(joint)[0]
            cmds.parent(dup_joint, self.offset_group)
            duplicate_joints.append(dup_joint)
            
        cmds.setAttr('%s.rotateX' % self.offset_group, 0)
        cmds.setAttr('%s.rotateY' % self.offset_group, 0)
        cmds.setAttr('%s.rotateZ' % self.offset_group, 0)
        
        self.orig_mesh = self.mesh
        self.orig_joints = self.joints
        self.orig_verts = []
        
        self.mesh = duplicate_mesh
        self.joints = duplicate_joints
        self.auto_joint_order = True
        
    def _store_verts(self):
        
        self.orig_verts = cmds.ls('%s.vtx[*]' % self.orig_mesh, flatten = True)   
        self.verts = cmds.ls('%s.vtx[*]' % self.mesh, flatten = True)
    
    def _get_joint_index(self, joint):
        for inc in xrange(0, len(self.joints)):
            if self.joints[inc] == joint:
                return inc
            
    def _store_vertex_vectors(self):
        self.vertex_vectors_2D = []
        
        for vert in self.verts:
            position = cmds.xform(vert, q = True, ws = True, t = True)
            position_vector_2D = vtool.util.Vector2D(position[0], position[2])
            
            self.vertex_vectors_2D.append(position_vector_2D)
                
    def _store_joint_vectors(self):
        
        self.joint_vectors_2D = []
        
        for joint in self.joints:
            
            position = cmds.xform(joint, q = True, ws = True, t = True)
            
            position = [position[0], 0.0]
            
            self.joint_vectors_2D.append(position)
            
        if not self.auto_joint_order:
            return
        
        other_list = list(self.joint_vectors_2D)
        other_list.reverse()
        
        last_position = None
        change = False
        
        for inc in xrange(0, len(other_list)):
            
            
            
            if not last_position:
                last_position = other_list[inc]
                continue
            
            if last_position:
                value1 = other_list[inc][0]
                value2 = last_position[0]
                
                if value1 > 0 and value1 > value2:
                    change = True
                    other_list[inc][0] = last_position[0] - 0.001
                    
                
                if value1 < 0 and value1 < value2:
                    change = True
                    other_list[inc][0] = last_position[0] + 0.001
                    
            
            last_position = other_list[inc]
        
        
        
        if change:
            
            other_list.reverse()
            self.joint_vectors_2D = other_list
    
    def _get_adjacent(self, joint):
        
        joint_index = self._get_joint_index(joint)
        
        joint_count = len(self.joints)
        
        if joint_index == 0:
            return [1]
        
        if joint_index == joint_count-1:
            return [joint_index-1]
        
        return [joint_index+1, joint_index-1]

    def _skin(self):
        
        joints = self.orig_joints
        mesh = self.orig_mesh
        
        skin = find_deformer_by_type(mesh, 'skinCluster')
        
        if skin and self.zero_weights:
            set_skin_weights_to_zero(skin)
        
        if not skin:
            skin = cmds.skinCluster(mesh, joints[0], tsb = True)[0]
            joints = joints[1:]
            set_skin_weights_to_zero(skin)
            self.zero_weights = True
        
        for joint in joints:
            
            try:
                cmds.skinCluster(skin, e = True, ai = joint, wt = 0.0)
            except:
                pass
            
        return skin
        
    def _weight_verts(self, skin):
        
        mesh = self.orig_mesh
        
        vert_count = len(self.verts)
        
        progress = core.ProgressBar('weighting %s:' % mesh, vert_count)
        
        for inc in xrange(0, vert_count):
            
            joint_weights = self._get_vert_weight(inc)
            
            if joint_weights:
                
                cmds.skinPercent(skin, self.orig_verts[inc], r = False, 
                                                                transformValue = joint_weights, 
                                                                normalize = False, 
                                                                zeroRemainingInfluences = self.zero_weights)
                
            progress.inc()
            progress.status('weighting %s: vert %s' % (mesh, inc))
            
            if vtool.util.break_signaled():
                break
            
            if progress.break_signaled():
                break
        
        progress.end()
            
    def _get_vert_weight(self, vert_index):
        
        if self.prune_weights:
            if self.prune_weights[vert_index] <= 0.0:
                return
        
        if not self.multiplier_weights:
            multiplier = 1
            
        if self.multiplier_weights:
            multiplier = self.multiplier_weights[vert_index]
            
            if multiplier == 0 or multiplier < 0.0001:
                return
        
        vertex_vector = self.vertex_vectors_2D[vert_index]
                
        joint_weights = []
        joint_count = len(self.joints)
        weight_total = 0
        
        old_multiplier = multiplier
        multiplier = 1
        
        for inc in xrange(0, joint_count):
            
            if inc == joint_count-1:
                break
            
            start_vector = vtool.util.Vector2D( self.joint_vectors_2D[inc] )
            end_vector = vtool.util.Vector2D( self.joint_vectors_2D[inc+1])
            
            percent = vtool.util.closest_percent_on_line_2D(start_vector, end_vector, vertex_vector, False)
            
            joint = self.orig_joints[inc]
            next_joint = self.orig_joints[inc+1]
            
            if percent <= 0:
                weight_total+=1.0
                if not weight_total > 1:
                    joint_weights.append([joint, (1.0*multiplier)])
                continue
                    
            if percent >= 1 and inc == joint_count-2:
                weight_total += 1.0
                if not weight_total > 1:
                    joint_weights.append([next_joint, (1.0*multiplier)])
                continue
            
            if percent > 1 or percent < 0:
                continue
            
            if self.fade_cosine:
                percent = vtool.util.fade_cosine(percent)
            if self.fade_smoothstep:
                percent = vtool.util.fade_smoothstep(percent)
            
            weight_total += 1.0-percent
            if not weight_total > 1:
                joint_weights.append([joint, ((1.0-percent)*multiplier)])
                
            weight_total += percent
            if not weight_total > 1:
                joint_weights.append([next_joint, percent*multiplier])
        
        if self.multiplier_weights:
            new_weights = []
            
            for joint in joint_weights:
                weight = joint[1]
                
                value = weight * old_multiplier
                
                new_weights.append( [joint[0], value] )
            
            joint_weights = new_weights
            
        return joint_weights
                
    def set_joints(self, joints):
        self.joints = joints
        
    def set_mesh(self, mesh):
        self.mesh = mesh
        
    def set_multiplier_weights(self, weights):
        self.multiplier_weights = weights
        
    def set_skip_zero_weights(self, weights):
        self.prune_weights = weights
        
    def set_weights_to_zero(self, bool_value):
        self.zero_weights = bool_value
        
    def set_auto_joint_order(self, bool_value):
        self.auto_joint_order = bool_value
        
    def set_orientation_transform(self, transform):
        """
        Transform to use to define the orientation of joints.
        """
        self.orientation_transform = transform
        
    def set_fade_cosine(self, bool_value):
        self.fade_smoothstep = False
        self.fade_cosine = bool_value
        
    def set_fade_smoothstep(self, bool_value):
        
        self.fade_cosine = False
        self.fade_smoothstep = bool_value
        
    def run(self):
        if not self.joints:
            return
        
        self.orig_mesh = self.mesh
        self.orig_joints = self.joints
        
        if self.orientation_transform:
            self._create_offset_group()
            
        self._store_verts()
        
        self._store_vertex_vectors()
        self._store_joint_vectors()
        skin = self._skin()
        
        self._weight_verts(skin)
        
        cmds.delete(self.offset_group)

class ComboControlShape(object):

    def __init__(self, shape):
        
        self.shape = shape
        self.targets = []
        self.control_positions = []
        self.base_mesh = None
        self.blendshape = None
        
    def add_target(self, target_name):
        self.targets.append(target_name)

    def add_control_position(self, control_attribute, value):
        self.control_positions.append([control_attribute, value])

    def set_blendshape(self, blendshape):
        self.blendshape = blendshape
        
    def set_base_mesh(self, base_mesh):
        self.base_mesh = base_mesh

    def create(self):
        
        for position in self.control_positions:
            cmds.setAttr(position[0],position[1])
        
        chad_extract_shape(self.base_mesh, self.shape, replace = True)
        
        if not self.blendshape:
            self.blendshape = find_deformer_by_type(self.base_mesh, 'blendShape', return_all = False)
        
        quick_blendshape(self.shape, self.base_mesh, blendshape=self.blendshape)
        
        inc = 0
        
        last_multiply = None
        
        for target in self.targets:
            
            if not last_multiply:
                multiply = attr.connect_multiply('%s.%s' % (self.blendshape, target), '%s.%s' % (self.blendshape, self.shape))
            
            if inc == 1:
                if last_multiply:
                    cmds.connectAttr('%s.%s' % (self.blendshape, target), '%s.input2X' % last_multiply)
                    
            if inc > 1:
                if last_multiply:
                    
                    last_multiply = attr.connect_multiply('%s.%s' % (self.blendshape, target), '%s.input2X' % last_multiply)
                
            last_multiply = multiply
            
            inc += 1
            
        for position in self.control_positions:
            cmds.setAttr(position[0],0)
    
class MultiJointShape(object):
    
    def __init__(self, shape):
        
        self.shape = shape
        self.joints = []
        
        self.control_values = []
        self.start_control_values = []
        self.off_control_values = []
        
        self.base_mesh = None
        self.skinned_mesh = None
        
        self.locators = []
        self.hook_to_empty_group = False
        self.hook_to_empty_group_name = None
        self.create_hookup = True
        self.weight_joints = []
        
        self.read_axis = 'Y'
        self.only_locator = None
        self.delta = True
        self.weight_joints = None
        
    def _create_locators(self):
        
        locators = []
     
        parent = cmds.listRelatives(self.joints[0], p = True)
        if parent:
            parent = parent[0]
     
        for joint in self.joints:
            
            if cmds.objExists('%s.blend_locator' % joint):
                locator = attr.get_attribute_input('%s.blend_locator' % joint, node_only = True)
            
            if not cmds.objExists('%s.blend_locator' % joint): 
                
                locator = cmds.spaceLocator(n = 'locator_%s' % joint)[0]
                
                attr.connect_message(locator, joint, 'blend_locator')
                
                cmds.pointConstraint(joint, locator)
                
                xform = space.create_xform_group(locator)
                
                cmds.parent(xform, parent)
                
            locators.append(locator)
        self.locators = locators
        
        if self.only_locator != None:
            
            use_locators = []
            
            for locator in self.locators:
                use_locators.append(self.locators[self.only_locator])
        
            self.locators = use_locators
            
    def _turn_controls_on(self):
        
        for control_group in self.control_values:
            cmds.setAttr( control_group[0], control_group[1] )
            
    
    def _turn_controls_off(self):
        
        for control_group in self.control_values:
            cmds.setAttr( control_group[0], 0 )
    
    def _turn_off_controls_on(self):
        
        for control_group in self.off_control_values:
            cmds.setAttr( control_group[0], control_group[1] )
            
    def _turn_off_controls_off(self):
        for control_group in self.off_control_values:
            cmds.setAttr( control_group[0], 0 )
            
    def _turn_start_controls_on(self):
        
        for control_group in self.start_control_values:
            cmds.setAttr( control_group[0], control_group[1] )
            
    def _turn_start_controls_off(self):
        
        for control_group in self.start_control_values:
            cmds.setAttr( control_group[0], 0 )
        
    def set_joints(self, joints):
        
        self.joints = joints
    
    def set_weight_joints(self, joints):
        self.weight_joints = joints
    
    def set_create_hookup(self, bool_value):
        self.create_hookup = bool_value
    
    def set_target_mesh(self, base_mesh):
        self.base_mesh = base_mesh
        
    def set_skin_mesh(self, skinned_mesh):
        self.skinned_mesh = skinned_mesh
        
    def add_control_value(self, control_attribute, value):
        
        self.control_values.append([control_attribute, value])
        
    def add_control_off_value(self, control_attribute, value):
        
        self.off_control_values.append([control_attribute, value])
        
    def add_control_start_value(self, control_attribute, value):
        self.start_control_values.append([control_attribute, value])
        
    def set_hook_to_empty_group(self, bool_value, name = None):
        self.hook_to_empty_group_name = name
        self.hook_to_empty_group = bool_value
        
    def set_read_axis(self, axis_letter):
        
        self.read_axis = axis_letter.upper()
        
    def set_use_only_locator(self, at_inc = 0):
        
        self.only_locator = at_inc
        
    def set_delta(self, bool_value):
        self.delta = bool_value
        
    def create(self):
        
        if not self.joints:
            self.create_hookup = False
        
        if self.create_hookup:
            self._create_locators()
        
        self._turn_controls_on() 
        
        if self.delta:
            new_brow_geo = chad_extract_shape(self.base_mesh, self.shape)
            
        if not self.delta:
            new_brow_geo = cmds.duplicate(self.shape)[0]
            
        cmds.delete(self.shape)
        
        new_brow_geo = cmds.rename(new_brow_geo, self.shape)
     
        joint_values = {}
        off_joint_values = {}    
        start_joint_values = {}
     
        for locator in self.locators:
            value = cmds.getAttr('%s.translate%s' % (locator, self.read_axis))
            joint_values[locator] = value
        
        self._turn_controls_off()
        
        if self.off_control_values:
            self._turn_off_controls_on()
            
            for locator in self.locators:
                value = cmds.getAttr('%s.translate%s' % (locator, self.read_axis))
                off_joint_values[locator] = value
                
            self._turn_controls_off()
            
        if self.start_control_values:
            self._turn_start_controls_on()
            
            for locator in self.locators:
                value = cmds.getAttr('%s.translate%s' % (locator, self.read_axis))
                start_joint_values[locator] = value
                
            self._turn_start_controls_off()
        
        
        split = SplitMeshTarget(new_brow_geo)
        split.set_weighted_mesh(self.skinned_mesh)
        
        inc = 1
     
        weight_joints = self.joints
        
        if self.weight_joints:
            weight_joints = self.weight_joints
            
        for joint in weight_joints:
            
            split.set_weight_joint_insert_at_first_camel(joint, str(inc), True)
            
            inc += 1
     
        split.set_base_mesh(self.base_mesh)
        splits = split.create()
        
        inc = 0
    
        if self.create_hookup:
            for split in splits:
                inbetween = False
                
                value = joint_values[self.locators[inc]]
                
                off_value = None
                start_value = None
                
                if off_joint_values and self.create_hookup:
                    off_value = off_joint_values[self.locators[inc]]
                    
                if start_joint_values and self.create_hookup:
                    
                    start_value = start_joint_values[self.locators[inc]]
                
                if not self.hook_to_empty_group:
                    blendshape = quick_blendshape(split, self.base_mesh)
                    
                hookup_attribute = split
                    
                number = vtool.util.get_trailing_number(split, number_count=2)
                if number:
                    inbetween = True
                    hookup_attribute = split[:-2]
                    between_value = (number * 0.01)
                    
                if self.hook_to_empty_group:
                    
                    if not self.hook_to_empty_group_name:
                        group = 'hookup_multi_%s' % self.base_mesh
                    if self.hook_to_empty_group_name:
                        group = self.hook_to_empty_group_name
                    
                    if not cmds.objExists(group):
                        group = cmds.group(em = True, n = group)
                        attr.hide_keyable_attributes(group)
                    
                    if not cmds.objExists('%s.%s' % (group, hookup_attribute)): 
                        cmds.addAttr(group, ln = hookup_attribute, k = True, at = 'double')
                
                    blendshape = group
                
                if not inbetween:
                    
                    pass_off_value = value
                    pass_start_value = 0
                    dest_off_value = 1
                    
                    
                    if off_value != None:
                        pass_off_value = off_value
                        dest_off_value = 0
                        
                    if start_value != None:
                        pass_start_value = start_value
                    
                    anim.quick_driven_key('%s.translate%s' % (self.locators[inc], self.read_axis),
                                            '%s.%s' % (blendshape, hookup_attribute),
                                            [pass_start_value, value, pass_off_value], 
                                            [0, 1, dest_off_value])        
                    
                    """
                    if off_value:
                        anim.quick_driven_key('%s.translate%s' % (self.locators[inc], self.read_axis),
                                                '%s.%s' % (blendshape, hookup_attribute),
                                                [0, value, off_value], 
                                                [0, 1, 0])
                    """
                    
                if inbetween:
                    
                    anim.quick_driven_key('%s.translate%s' % (self.locators[inc], self.read_axis),
                                                '%s.%s' % (blendshape, hookup_attribute),
                                                [value], 
                                                [between_value])
                inc+=1
    
        
        if not self.hook_to_empty_group and self.create_hookup:
            cmds.delete(splits)
        cmds.delete(new_brow_geo)
        
        return splits

                    
class MayaWrap(object):
    """
    Convenience for making maya wraps.
    
    Args:
        mesh (str): The name of a mesh that should get wrapped.
    """
    def __init__(self, mesh):
        
        self.mesh = mesh
        self.meshes = []
        self.driver_meshes = []
        self.wrap = ''
        self.base_meshes = []
        self.base_parent = None
        
        self._set_mesh_to_wrap(mesh, 'mesh')
        self._set_mesh_to_wrap(mesh, 'lattice')
        self._set_mesh_to_wrap(mesh, 'nurbsCurve')
        self._set_mesh_to_wrap(mesh, 'nurbsSurface')
    
    def _create_wrap(self):
        
        basename = core.get_basename(self.mesh, True)
        
        self.wrap = cmds.deformer(self.mesh, type = 'wrap', n = 'wrap_%s' % basename)[0]
        cmds.setAttr('%s.exclusiveBind' % self.wrap, 1)
        cmds.setAttr('%s.maxDistance' % self.wrap, 1)
        return self.wrap                 
    
    def _add_driver_meshes(self):
        inc = 0
        
        for mesh in self.driver_meshes:
            self._connect_driver_mesh(mesh, inc)
            inc+=1
        
    def _connect_driver_mesh(self, mesh, inc):
        
        base = cmds.duplicate(mesh, n = 'wrapBase_%s' % mesh)[0]
        
        core.rename_shapes(base)
        
        if self.base_parent:
            cmds.parent(base, self.base_parent)
        
        self.base_meshes.append(base)
        cmds.hide(base)
        
        if geo.is_a_mesh(mesh):
            cmds.connectAttr( '%s.worldMesh' % mesh, '%s.driverPoints[%s]' % (self.wrap, inc) )
            cmds.connectAttr( '%s.worldMesh' % base, '%s.basePoints[%s]' % (self.wrap, inc) )
            
            
            if not cmds.objExists('%s.dropoff' % mesh):
                cmds.addAttr(mesh, at = 'short', sn = 'dr', ln = 'dropoff', dv = 10, min = 1, k = True)
                
            if not cmds.objExists('%s.inflType' % mesh):
                cmds.addAttr(mesh, at = 'short', sn = 'ift', ln = 'inflType', dv = 2, min = 1, max = 2, k = True )
                
            if not cmds.objExists('%s.smoothness' % mesh):    
                cmds.addAttr(mesh, at = 'short', sn = 'smt', ln = 'smoothness', dv = 0.0, min = 0.0, k = True)
                
            cmds.connectAttr('%s.dropoff' % mesh, '%s.dropoff[%s]' % (self.wrap, inc) )
            cmds.connectAttr('%s.inflType' % mesh, '%s.inflType[%s]' % (self.wrap, inc) )
            cmds.connectAttr('%s.smoothness' % mesh, '%s.smoothness[%s]' % (self.wrap, inc) )
                
        if geo.is_a_surface(mesh):
            cmds.connectAttr( '%s.worldSpace' % mesh, '%s.driverPoints[%s]' % (self.wrap, inc) )
            cmds.connectAttr( '%s.worldSpace' % base, '%s.basePoints[%s]' % (self.wrap, inc) )
        
            
            if not cmds.objExists('%s.dropoff' % mesh):
                cmds.addAttr(mesh, at = 'short', sn = 'dr', ln = 'dropoff', dv = 10, min = 1, k = True)
                
            if not cmds.objExists('%s.wrapSamples' % mesh):
                cmds.addAttr(mesh, at = 'short', sn = 'dr', ln = 'wrapSamples', dv = 0, min = 1, k = True)
                
            cmds.connectAttr('%s.dropoff' % mesh, '%s.dropoff[%s]' % (self.wrap, inc) )
            cmds.connectAttr('%s.wrapSamples' % mesh, '%s.nurbsSamples[%s]' % (self.wrap, inc) )
        
        
        if not cmds.isConnected('%s.worldMatrix' % self.mesh, '%s.geomMatrix' % (self.wrap)):
            cmds.connectAttr('%s.worldMatrix' % self.mesh, '%s.geomMatrix' % (self.wrap))
                        
    def _set_mesh_to_wrap(self, mesh, geo_type = 'mesh'):
        
        shapes = cmds.listRelatives(mesh, s = True, f = True)
        
        if shapes and cmds.nodeType(shapes[0]) == geo_type:
            self.meshes.append(mesh)
                
        relatives = cmds.listRelatives(mesh, ad = True, f = True)
                    
        for relative in relatives:
            
            shapes = cmds.listRelatives(relative, s = True, f = True)
            
            if shapes and cmds.nodeType(shapes[0]) == geo_type:
                self.meshes.append(relative)

                
    def set_driver_meshes(self, meshes = []):
        """
        Set the meshes to drive the wrap. If more than 1 exclusive bind won't work properly.
        Currently polgyons and nurbSurfaces work.
        
        Args:
            meshes (list): List of meshes and nurbSurfaces to influence the wrap. 
        """
        if meshes:
            
            meshes = vtool.util.convert_to_sequence(meshes)
            
            self.driver_meshes = meshes
    
    def set_base_parent(self, name):
        """
        Set the parent for the base meshes created.
        """
        self.base_parent = name
    
    def create(self):
        """
        Create the wrap.
        """
        
        if not self.meshes:
            
            return
        
        wraps = []
        
        for mesh in self.meshes:
            self.mesh = mesh
            
            wrap = self._create_wrap()
                        
            wraps.append(wrap)
            
            self._add_driver_meshes()

                
        if len(self.driver_meshes) > 1:
            cmds.setAttr('%s.exclusiveBind' % self.wrap, 0)

        return wraps

 
class EnvelopeHistory(object):
    """
    Convenience for turning on/off deformation history on a node.
    
    Args:
        transform (str): The name of a transform.
    """
    def __init__(self, transform):
        
        self.transform = transform
        
        self.envelope_values = {}
        self.envelope_connection = {}
        
        self.history = self._get_envelope_history()
        
    def _get_history(self):
        
        history = get_history(self.transform)
        
        return history
        
    def _get_envelope_history(self):
        
        self.envelope_values = {}
        
        history = self._get_history()
        
        found = []
        
        if not history:
            return found
        
        for thing in history:
            if cmds.objExists('%s.envelope' % thing):
                found.append(thing)
                
                value = cmds.getAttr('%s.envelope' % thing)
                
                self.envelope_values[thing] = value
                
                connected = attr.get_attribute_input('%s.envelope' % thing)
                
                self.envelope_connection[thing] = connected
                
        return found
    
    def turn_off(self):
        """
        Turn off all the history found.
        """
        
        for history in self.history:
            
            connection = self.envelope_connection[history]
            
            if connection:
                cmds.disconnectAttr(connection, '%s.envelope' % history)
                
            cmds.setAttr('%s.envelope' % history, 0)
 
    def turn_off_referenced(self):
        """
        Turn off only history that is referenced. Not history that was created after referencing.
        """
        for history in self.history:
            
            if not core.is_referenced(history):
                continue
            
            connection = self.envelope_connection[history]
            
            if connection:
                cmds.disconnectAttr(connection, '%s.envelope' % history)
                
            cmds.setAttr('%s.envelope' % history, 0)
            
    def turn_off_exclude(self, deformer_types):
        """
        Turn off all but the deformer types specified.
        """
        set_envelopes(self.transform, 0, deformer_types)
        
    def turn_on(self, respect_initial_state = False):
        """
        Turn on all the history found.
        """
        for history in self.history:
            
            if respect_initial_state:
                value = self.envelope_values[history]
            if not respect_initial_state:
                value = 1
            
            cmds.setAttr('%s.envelope' % history, value)
            
            connection = self.envelope_connection[history]
            if connection:
                cmds.connectAttr(connection, '%s.envelope' % history)

def cluster_curve(curve, description, join_ends = False, join_start_end = False, last_pivot_end = False):
    """
    Create clusters on the cvs of a curve.
    joint_start_end, the cv at the start and end of the curve will be joined.
    join_ends, the 2 start cvs will have one cluster, the 2 end cvs will have one cluster.
    
    Args:
        curve (str): The name of a curve.
        description (str): The description to give the clusters.
        join_ends (bool): Wether to joint the 2 start cvs under one cluster, and the two end cvs under another cluster.
        joint_start_end (bool): Wether to join the start and end cvs under one cluster.
        last_pivot_end (bool): Wether to put the pivot of the last cluster at the end of the curve.
        
    Returns:
        list: [cluster_handle, cluster_handle, ...]
    """
    
    clusters = []
    
    cvs = cmds.ls('%s.cv[*]' % curve, flatten = True)
    
    cv_count = len(cvs)
    
    start_inc = 0
    
    if join_ends and not join_start_end:
        cluster = cmds.cluster('%s.cv[0:1]' % curve, n = core.inc_name(description))[1]
        position = cmds.xform('%s.cv[0]' % curve, q = True, ws = True, t = True)
        cmds.xform(cluster, ws = True, rp = position, sp = position)
        clusters.append(cluster)
        
        last_cluster = cmds.cluster('%s.cv[%s:%s]' % (curve,cv_count-2, cv_count-1), n = core.inc_name(description))[1]
        
        if not last_pivot_end:
            position = cmds.xform('%s.cv[%s]' % (curve,cv_count-2), q = True, ws = True, t = True)
        if last_pivot_end:
            position = cmds.xform('%s.cv[%s]' % (curve,cv_count-1), q = True, ws = True, t = True)
            
        cmds.xform(last_cluster, ws = True, rp = position, sp = position)
            
        
        start_inc = 2
        
        cvs = cvs[2:cv_count-2]
        cv_count = len(cvs)+2
        
    if join_start_end:
        joined_cvs = ['%s.cv[0:1]' % curve,'%s.cv[%s:%s]' % (curve, cv_count-2, cv_count-1)]
        
        cluster = cmds.cluster(joined_cvs, n = core.inc_name(description))[1]
        position = cmds.xform('%s.cv[0]' % curve, q = True, ws = True, t = True)
        cmds.xform(cluster, ws = True, rp = position, sp = position)
        clusters.append(cluster)
        
        start_inc = 2
        
        cvs = cvs[2:cv_count-2]
        cv_count = len(cvs)+2
    
    for inc in xrange(start_inc, cv_count):
        cluster = cmds.cluster( '%s.cv[%s]' % (curve, inc), n = core.inc_name(description) )[1]
        clusters.append(cluster)
    
    if join_ends and not join_start_end:
        clusters.append(last_cluster)
    
    return clusters

def create_cluster(points, name):
    """
    Create a cluster on a bunch of points.
    
    Args::
        points (list): The names of points to cluster.
        name (str): The description of the cluster.
        
    Returns:
        list: [cluster, handle]
    """
    cluster, handle = cmds.cluster(points, n = core.inc_name('cluster_%s' % name))
    
    return cluster, handle

def create_cluster_bindpre(cluster, handle):
    """
    Create a bind pre matrix for the cluster.  
    This is good if for treating a cluster like a lattice.  
    Lattices have a base. If the base and the lattice move together the lattice has no effect.
    Likewise if you move the bind pre transform and the cluster handle together the cluster does not deform the mesh.
    Only when you move the cluster handle without the bind pre.
    
    Args:
        cluster (str): The name of a cluster deformer.
        handle (str): The handle for the cluster deformer in cluster 
        
    Returns:
        str: The bindpre group name.
    """
    
    bindpre = cmds.duplicate(handle, n = 'bindPre_%s' % handle)[0]
    shapes = core.get_shapes(bindpre)
    if shapes:
        cmds.delete(shapes)
    
    cmds.connectAttr('%s.worldInverseMatrix' % bindpre, '%s.bindPreMatrix' % cluster)
    
    return bindpre

def create_lattice(points, description, divisions = (3,3,3), falloff = (2,2,2)):
    """
    Convenience for creating a lattice.
    
    Args:
        points (list): List of points, meshes to deform.
        description (str): The description to give the lattice.
        divisions (tuple): eg (3,3,3) The number of divisions to give the lattice on each axis.
        falloff (tuple): eg (2,2,2) The falloff to give each axis.
        
    Returns:
        list: ffd, lattice, base
    """
    
    
    ffd, lattice, base = cmds.lattice(points, 
                                      divisions = divisions, 
                                      objectCentered = True, 
                                      ldv = falloff, n = 'ffd_%s' % description)
    
    return ffd, lattice, base
    
    

def get_history(geometry):
    """
    Get the history of the geometry. This will not search too deep.
    
    Args:
        geometry (str): The name of the geometry
        
    Returns:
        list: A list of deformers in the deformation history.
    """
    
    scope = cmds.listHistory(geometry, pdo = True)
    
    found = []
    
    if not scope:
        return
    
    for thing in scope:
        
        inherited = cmds.nodeType(thing, inherited = True )
        
        if 'geometryFilter' in inherited:
            found.append(thing)
            
        if cmds.objectType(thing, isa = "shape") and not cmds.nodeType(thing) == 'lattice':
            
            return found
            
        
    if not found:
        return None
    
    return found

def find_deformer_by_type(mesh, deformer_type, return_all = False):
    """
    Given a mesh find a deformer with deformer_type in the history.
    
    Args:
        mesh (str): The name of a mesh.
        deformer_type (str): Corresponds to maya deformer type, eg. skinCluster, blendShape
        return_all (bool): Wether to return all the deformers found of the specified type, or just the first one.
        
    Returns:
        list: The names of deformers of type found in the history.
    """
    
    found = []
    
    history = get_history(mesh)
    
    if history:
    
        for thing in history:
            if thing:
                if cmds.nodeType(thing) == deformer_type:
                    if not return_all:
                        return thing
                    
                    found.append(thing)
            
    if not found:
        return None
        
    return found

def set_envelopes(mesh, value, exclude_type = []):
    
    history = get_history(mesh)
    
    if not history:
        return
    
    for node in history:
        
        skip_current = False
        
        for skip in exclude_type:
            if skip == cmds.nodeType(node):
                skip_current = True
                break
            
        if skip_current:
            continue
        
        try:
            cmds.setAttr('%s.envelope' % node, value)
        except:
            pass

#--- skin

def get_influences_on_skin(skin_deformer, short_name = True):
    """
    Get the names of the skin influences in the skin cluster.
    
    Args:
        skin_deformer (str)
        
    Returns:
        list: influences found in the skin cluster
    """
    
    skin = api.SkinClusterFunction()
    skin.set_node_as_mobject(skin_deformer)
    influences = skin.get_influence_names(short_name = short_name)

    return influences

def get_non_zero_influences(skin_deformer):
    """
    Get influences that have weight in the skin cluster.
    
    Args:
        skin_deformer (str)
        
    Returns:
        list: influences found in the skin cluster that have influence.
        
    """
    
    influences = cmds.skinCluster(skin_deformer, q = True, wi = True)
    
    return influences
    
def get_index_at_skin_influence(influence, skin_deformer):
    """
    Given an influence name, find at what index it connects to the skin cluster. 
    This corresponds to the matrix attribute. eg. skin_deformer.matrix[0] is the connection of the first influence.
    
    Args:
        influence (str): The name of an influence.
        skin_deformer (str): The name of a skin_deformer affected by influence.
        
    Returns:
        int: The index of the influence. 
    """
    #this is actually faster than the api call. 
    
    connections = cmds.listConnections('%s.worldMatrix' % influence, p = True, s = True)
    
    if not connections:
        return
    
    good_connection = None
    
    for connection in connections:
        if connection.startswith(skin_deformer):
            good_connection = connection
            break
    
    if good_connection == None:
        return
    
    search = vtool.util.search_last_number(good_connection)
    found_string = search.group()
    
    index = None
    
    if found_string:
        index = int(found_string)
    
    return index
    
        
def get_skin_influence_at_index(index, skin_deformer):
    """
    Find which influence connect to the skin cluster at the index.
    This corresponds to the matrix attribute. eg. skin_deformer.matrix[0] is the connection of the first influence.
    
    Args:
        index (int): The index of an influence.
        skin_deformer (str): The name of the skin cluster to check the index.
        
    Returns:
        str: The name of the influence at the index.
        
    """
    
    influence_slot = '%s.matrix[%s]' % (skin_deformer, index) 
    
    connection = attr.get_attribute_input( influence_slot )
    
    if connection:
        connection = connection.split('.')
        return connection[0]    

def get_skin_influence_indices(skin_deformer):
    """
    Get the indices of the connected influences.
    This corresponds to the matrix attribute. eg. skin_deformer.matrix[0] is the connection of the first influence.
    
    Args:
        skin_deformer (str): The name of a skin cluster.
    
    Returns:
        list: The list of indices.
    """
    
    skin = api.SkinClusterFunction()
    skin.set_node_as_mobject(skin_deformer)
    
    indices = skin.get_influence_indices()
    
    return indices

def get_skin_influences(skin_deformer, return_dict = False):
    """
    Get the influences connected to the skin cluster.
    Return a dictionary with the keys being the name of the influences.
    The value at the key the index where the influence connects to the skin cluster.
    
    Args:
        skin_deformer (str): The name of a skin cluster.
        return_dict (bool): Wether to return a dictionary.
        
    Returns:
        list, dict: A list of influences in the skin cluster. If return_dict = True, return dict[influence] = index
    """
    
    skin = api.SkinClusterFunction()
    skin.set_node_as_mobject(skin_deformer)
    
    influence_dict, influences = skin.get_influence_dict(short_name = True)
    
    if return_dict == False:
        return influences
    if return_dict == True:
        return influence_dict
    """   
    indices = get_skin_influence_indices(skin_deformer)
    
    if not return_dict:
        found_influences = []
    if return_dict:
        found_influences = {}
    
    for index in indices:
        influence = get_skin_influence_at_index(index, skin_deformer)
        
        if not return_dict:
            found_influences.append(influence)
        if return_dict:
            found_influences[influence] = index
    """ 
    

def get_meshes_skinned_to_joint(joint):
    """
    Get all meshses that are skinned to the specified joint.
    
    Args:
        joint (str): The name of a joint.
        
    Returns:
        list: The skin clusters affected by joint.
    """
    skins = cmds.ls(type = 'skinCluster')
    
    found = []
    
    for skin in skins:
        influences = get_skin_influences(skin)
        
        if joint in influences:
            geo = cmds.deformer(skin, q = True, geometry = True)
            
            geo_parent = cmds.listRelatives(geo, p = True)
            
            found += geo_parent
        
    return found
    
    
def get_skin_weights(skin_deformer):
    """
    Get the skin weights for the skin cluster.
    Return a dictionary where the key is the influence, 
    and the value is the a list of weights at the influence.
    
    Args:
        skin_deformer (str): The name of a skin deformer.
        
    Returns:
        dict: dict[influence_index] = weight values corresponding to point order.
    """
    
    skin = api.SkinClusterFunction()
    skin.set_node_as_mobject(skin_deformer)
    
    value_map = skin.get_skin_weights_dict()
    
    return value_map


def get_skin_influence_weights(influence_name, skin_deformer):
    """
    This is good to use if you just need to query one influence in a skin cluster.
    If you need to query many influences than use get_skin_weights.
    """
    
    influence_index = get_index_at_skin_influence(influence_name, skin_deformer)
    
    if influence_index == None:
        return
    
    skin = api.nodename_to_mobject(skin_deformer)
    skinFn = api.SkinClusterFunction(skin)
    
    weights_dict = skinFn.get_skin_weights_dict()
    
    if weights_dict.has_key(influence_index):
        weights = weights_dict[influence_index]
        
    if not weights_dict.has_key(influence_index):
        indices = attr.get_indices('%s.weightList' % skin_deformer)
        index_count = len(indices)
        weights = [0] * index_count
    
    return weights

def get_skin_blend_weights(skin_deformer):
    """
    Get the blendWeight values on the skin cluster.
    
    Args:
        skin_deformer (str): The name of a skin deformer.
    
    Returns:
        list: The blend weight values corresponding to point order.
    """
    indices = attr.get_indices('%s.weightList' % skin_deformer)
    
    blend_weights_attr = '%s.blendWeights' % skin_deformer
    blend_weights = attr.get_indices(blend_weights_attr)
    blend_weight_dict = {}
        
    if blend_weights:
    
        for blend_weight in blend_weights:
            blend_weight_dict[blend_weight] = cmds.getAttr('%s.blendWeights[%s]' % (skin_deformer, blend_weight))
    
    
    values = []
    
    for inc in xrange(0, len(indices)):
        
        if inc in blend_weight_dict:
            
            value = blend_weight_dict[inc]
            if type(value) == type(0.0):
                if value < 0.000001:
                    value = 0.0
            if type(value) != type(0.0):
                value = 0.0
            if value != value:
                value = 0.0
            
            values.append( value )
            continue
                    
        if not inc in blend_weight_dict:
            values.append( 0.0 )
            continue

    return values

def set_skin_blend_weights(skin_deformer, weights):
    """
    Set the blendWeights on the skin cluster given a list of weights.
    
    Args:
        skin_deformer (str): The name of a skin deformer.
        weights (list): A list of weight values corresponding to point order.
    """
    indices = attr.get_indices('%s.weightList' % skin_deformer)
    
    new_weights = []
    
    for weight in weights:
        if weight != weight:
            weight = 0.0
            
        new_weights.append(weight)
    
    for inc in xrange(0, len(indices)):
        if cmds.objExists('%s.blendWeights[%s]' % (skin_deformer, inc)):
            try:
                cmds.setAttr('%s.blendWeights[%s]' % (skin_deformer, inc), weights[inc])
            except:
                pass
        

def set_skin_weights_to_zero(skin_deformer):
    """
    Set all the weights on the mesh to zero.
    
    Args:
        skin_deformer (str): The name of a skin deformer.
    
    """
    
    weights = cmds.ls('%s.weightList[*]' % skin_deformer)
        
    for weight in weights:
            
        weight_attributes = cmds.listAttr('%s.weights' % (weight), multi = True)
            
        if not weight_attributes:
            continue
        
        for weight_attribute in weight_attributes:
            cmds.setAttr('%s.%s' % (skin_deformer, weight_attribute), 0)

def get_joint_index_map(joints, skin_cluster):
    
    joint_map = {}
    
    for joint in joints:
        if not cmds.objExists(joint):
            vtool.util.warning('%s does not exist.' % joint)
            continue
                    
        index = get_index_at_skin_influence(joint, skin_cluster)
        
        joint_map[index] = joint    
        
    return joint_map

#--- deformers

def invert_weights(weights):
    
    new_weights = []
    
    for weight in weights:
        
        new_weight = 1.00-weight
        
        new_weights.append(new_weight)
        
    return new_weights

def set_vert_weights_to_zero(vert_index, skin_deformer, joint = None):
    """
    Set the weights at the given point index to zero.
    
    Args:
        vert_index (int): The index of a vert.
        skin_deformer (str): The name of a skin deformer.
        joint (str): The name of a joint that is influencing the vert. If not joint given all the influences for the vert will be zeroed out.
    """
    
    
    influences = cmds.listAttr('%s.weightList[ %s ].weights' % (skin_deformer, vert_index), multi = True )
    
    index = None
    
    if joint:
        index = get_index_at_skin_influence(joint, skin_deformer)
    
    if not index:
        for influence in influences:
            cmds.setAttr('%s.%s' % (skin_deformer, influence), 0.0)
            
    if index:
        cmds.setAttr('%s.%s' % (skin_deformer, index), 0.0)   

def set_deformer_weights(weights, deformer, index = 0):
    """
    Set the deformer weights. Good for cluster and wire deformers. 
    
    Args:
        weights (list): A list of weight values that should correspond to point order.
        deformer (str): The name of a deformer. eg. cluster or wire.
        index (int): The geometry index to set weights on. By default it will work on the first mesh.
    """
    
    for inc in xrange(0, len(weights) ):    
        cmds.setAttr('%s.weightList[%s].weights[%s]' % (deformer, index, inc), weights[inc])
        
def get_deformer_weights(deformer, index = 0):
    """
    Get the weights on a deformer. In point order.
    
    Args:
        deformer (str): The name of a deformer.
        index (int): The index of the meshes attached. 
    
    Returns:
        list: The weight values in point order.
        
    """
    
    meshes = cmds.deformer(deformer, q = True, g = True)
    
    try:
        mesh = meshes[index]
        vtool.util.warning('index "%s" out of range of deformed meshes.' % index)
    except:
        return
    
    indices = cmds.ls('%s.vtx[*]' % mesh, flatten = True)
            
    weights = []
    
    for inc in xrange(0, len(indices)):
        weights.append( cmds.getAttr('%s.weightList[%s].weights[%s]' % (deformer, index, inc)) )
    
    return weights

def set_wire_weights(weights, wire_deformer, index = 0):
    """
    Set the wire weights given a list of weights that corresponds to point order.
    
    Args:
        weights (list): A list of weight values corresponding to point order.
        wire_deformer (str): The name of a wire deformer.
        index (int): The index of the mesh to work on. By default it will work on the first mesh.
    """
    #might need refresh 
    
    set_deformer_weights(weights, wire_deformer, index)


def get_wire_weights(wire_deformer, index = 0):
    """
    Get the weights on a wire deformer. In point order.
    
    Args:
        wire_deformer (str): The name of a deformer.
        index (int): The index of the meshes attached. 
    
    Returns:
        list: The weight values in point order.
        
    """
    
    get_deformer_weights(wire_deformer, index)

def get_cluster_weights(cluster_deformer, index = 0):
    """
    Get the weights on a cluster deformer. In point order.
    
    Args:
        cluster_deformer (str): The name of a deformer.
        index (int): The index of the meshes attached. 
    
    Returns:
        list: The weight values in point order.
        
    """
    
    return get_deformer_weights(cluster_deformer, index)

def get_blendshape_weights(blendshape_deformer, mesh, index = -1):
    """
    Not implemented
    """
    pass

def invert_blendshape_weight(blendshape_deformer, index = -1):
    """
    Not implemented
    """
    pass

def get_intermediate_object(transform):
    """
    Get the intermediate object in the list of shape nodes under transform.
    
    Args:
        transform (str): The name of a transform.
    """
    shapes = cmds.listRelatives(transform, s = True, f = True)
    
    return shapes[-1]
    
def set_all_weights_on_wire(wire_deformer, weight, slot = 0):
    """
    Set all the weights on a wire deformer.
    
    Args:
        wire_deformer (str): The name of a wire deformer.
        weight (float): The weight value to assign the weights of a wire deformer.
        slot (int): The index of the deformed mesh. Usually 0.
    
    """
    
    meshes = cmds.deformer(wire_deformer, q = True, g = True)
    
    try:
        mesh = meshes[slot]
    except:
        mesh = None
    
    if not mesh:
        indices = attr.get_indices('%s.weightList[%s]' % (wire_deformer,slot))
    if mesh:
        indices = cmds.ls('%s.vtx[*]' % mesh, flatten = True)    
    
    for inc in xrange(0, len(indices) ):
        cmds.setAttr('%s.weightList[%s].weights[%s]' % (wire_deformer, slot, inc), weight)

def set_wire_weights_from_skin_influence(wire_deformer, weighted_mesh, influence):
    """
    Set the wire weights from a skinned joint.
    
    Args:
        wire_deformer (str): The name of a wire deformer.
        weighted_mesh (str): The name of a skinned mesh.
        influence (str): The name of an influence.
        
    """
    
    skin_cluster = find_deformer_by_type(weighted_mesh, 'skinCluster')
    index = get_index_at_skin_influence(influence, skin_cluster)
    
    if index == None:
        vtool.util.show('No influence %s on skin %s.' % (influence, skin_cluster))
        return
    
    weights = get_skin_weights(skin_cluster)
    
    weight = weights[index]
    
    set_wire_weights(weight, wire_deformer)
    

def prune_wire_weights(deformer, value = 0.0001):
    """
    Removes weights that fall below value.
    
    Args:
        deformer (str): The name of a deformer.
        value (float): The value below which verts get removed from wire deformer.
    """
    
    meshes = cmds.deformer(deformer, q = True, g = True)
    
    try:
        mesh = meshes[0]
    except:
        mesh = None
    
    verts = cmds.ls('%s.vtx[*]' % mesh, flatten = True)
    
    found_verts = []
    
    for inc in xrange(0, len(verts)):
        weight_value = cmds.getAttr('%s.weightList[%s].weights[%s]' % (deformer, 0, inc))
        
        if weight_value < value:
            found_verts.append('%s.vtx[%s]' % (mesh, inc))
    
    cmds.sets(found_verts, rm = '%sSet' % deformer  )
    

def map_influence_on_verts(verts, skin_deformer):
    """
    Given a list of verts, get which influences have the most weight.
    
    Args:
        verts (list): The index of vertices on the mesh to get weights from.
        skin_deformer (str): The name of a skin cluster.
        
    Returns:
        dict: dict[influence_index] = value
    
    """
    
    value_map = {}
    
    for vert in verts:
        vert_index = int(vert)
        
        influences = cmds.listAttr('%s.weightList[%s].weights' % (skin_deformer, vert_index), multi = True )
        
        influence_count = len(influences)
        min_value = 1.0/influence_count
        top_value = 1.0 - min_value
                
        found_value = [None, 0]
                            
        for influence in influences:
            influence_index = re.findall('\d+', influence)[1]
            value = cmds.getAttr('%s.%s' % (skin_deformer, influence))

            if influence_count == 1:
                found_value = [influence_index, value]
                break

            if value < min_value:
                continue
            
            if value == 0:
                continue
            
            if value >= top_value:
                found_value = [influence_index, value]
                break
                                                
            if value >= found_value[1]:
                found_value = [influence_index, value]
        
        influence_index, value = found_value
                    
        if not value_map.has_key(influence_index):
            value_map[influence_index] = value
    
        if value_map.has_key(influence_index):
            value_map[influence_index] += value

    return value_map

def get_faces_at_skin_influence(mesh, skin_deformer):
    """
    Args:
        mesh (str): The name of a mesh affected by skin_deformer.
        skin_deformer (str): The name of a skin deformer.
        
    Returns:
        dict: dict[influence_index] = [face ids]
    """
    scope = cmds.ls('%s.f[*]' % mesh, flatten = True)
    
    index_face_map = {}
    
    inc = 0
    
    for face in scope:
            
        inc += 1
           
        verts = cmds.polyInfo(face, fv = True)
        verts = verts[0].split()
        verts = verts[2:]
        
        value_map = map_influence_on_verts(verts, skin_deformer)
        
        good_index = None
        last_value = 0
        
        for index in value_map:
            value = value_map[index]
            
            if value > last_value:
                good_index = index
                last_value = value
                                
        if not index_face_map.has_key(good_index):
            index_face_map[good_index] = []
            
        index_face_map[good_index].append(face)
        
    return index_face_map

@core.undo_chunk
def split_mesh_at_skin(mesh, skin_deformer = None, vis_attribute = None, constrain = False):
    """
    Split a mesh into smaller sections based on skin deformer weights.
    
    Args:
        mesh (str): The name of a mesh.
        skin_deformer (str): The name of a skin deformer.
        vs_attribute (str): The name of a visibility attribute to connect to. eg. 'node_name.sectionVisibility'
        constrain (bool): Wether to constrain the sections or parent them.
        
    Returns:
        str: If constrain = True, the name of the group above the sections. Otherwise return none.
    """
    
    if constrain:
        group = cmds.group(em = True, n = core.inc_name('split_%s' % mesh))
    
    if not skin_deformer:
        skin_deformer =  find_deformer_by_type(mesh, 'skinCluster')
    
    index_face_map = get_faces_at_skin_influence(mesh, skin_deformer)

    cmds.hide(mesh)
    
    main_duplicate = cmds.duplicate(mesh)[0]
    attr.unlock_attributes(main_duplicate)
    
    #clean shapes
    shapes = cmds.listRelatives(main_duplicate, shapes = True)
    cmds.delete(shapes[1:])
        
    for key in index_face_map:
        
        duplicate_mesh = cmds.duplicate(main_duplicate)[0]
        
        scope = cmds.ls('%s.f[*]' % duplicate_mesh, flatten = True)
        cmds.select(scope, r = True)
        
        faces = []
        
        for face in index_face_map[key]:
            face_name = face.replace(mesh, duplicate_mesh)
            faces.append(face_name)
        
        cmds.select(faces, d = True)
        cmds.delete()
        
        influence = get_skin_influence_at_index(key, skin_deformer)
        
        if not constrain:
            cmds.parent(duplicate_mesh, influence)
        if constrain:
            follow = space.create_follow_group(influence, duplicate_mesh)
            attr.connect_scale(influence, follow)
            #cmds.parentConstraint(influence, duplicate_mesh, mo = True)
            cmds.parent(follow, group)
        
        if vis_attribute:
            cmds.connectAttr(vis_attribute, '%s.visibility' % duplicate_mesh)
    
    cmds.showHidden(mesh)
    
    if constrain:
        return group
 
def add_joint_bindpre(skin, joint, description = None):
    """
    Add a bind pre locator to the bindPreMatrix of the skin.
    
    Args:
        skin (str): The name of a skin cluster to add bind pre to.
        joint (str): The name of the joint to match bind pre to.
        description(str): The description of the bind pre.
        
    Returns:
        str: The name of the bind pre locator.
        
    """
    
    if not description:
        description = joint
    
    bindPre_locator = cmds.spaceLocator(n = core.inc_name('locator_%s' % description))[0]
    
    index = get_index_at_skin_influence(joint, skin)
    
    match = space.MatchSpace(joint, bindPre_locator)
    match.translation_rotation()
    
    cmds.connectAttr('%s.worldInverseMatrix' % bindPre_locator, '%s.bindPreMatrix[%s]' % (skin, index))
    
    return bindPre_locator
    
def convert_wire_deformer_to_skin(wire_deformer, description, joint_count = 10, delete_wire = True, skin = True, falloff = 1, create_controls = True):
    """
    Meant to take a wire deformer and turn it into a skinned joint chain.
    
    Args:
        wire_deformer (str): The name of a wire deformer.
        description (str): The description to give the setup
        joint_count (int): The number of joints to create. Higher number better resembles the effect of a wire deformer, but gets slow fast.
        delete_wire (bool): Wether to delete the original wire deformer.
        skin (bool): Wether to calculate and skin the bones to mimic the wire deformer.
        falloff (float): Corresponds to the wire distance value.
        create_controls (bool): Wether to create controls on the joints.
         
    Returns:
        list: [convert_group, control_group, zero_verts] Zero verts are the verts that were not affected by the wire conversion.
    """
    vtool.util.show('converting %s' % wire_deformer)
    
    convert_group = cmds.group(em = True, n = core.inc_name('convertWire_%s' % description))
    bindPre_locator_group = cmds.group(em = True, n = core.inc_name('convertWire_bindPre_%s' % description))
    
    cmds.parent(bindPre_locator_group, convert_group)
    
    cmds.hide(bindPre_locator_group)
    
    curve = attr.get_attribute_input('%s.deformedWire[0]' % wire_deformer, node_only = True)
    
    curve = cmds.listRelatives(curve, p = True)[0]
    
    base_curve = attr.get_attribute_input('%s.baseWire[0]' % wire_deformer, node_only= True)
    base_curve = cmds.listRelatives(base_curve, p = True)[0]
    
    
    joints, joints_group, control_group = geo.create_joints_on_curve(curve, joint_count, description, create_controls = create_controls)
    
    meshes = cmds.deformer(wire_deformer, q = True, geometry = True)
    if not meshes:
        return
    
    inc = 0
    
    for mesh in meshes:
        zero_verts = []
        
        if not skin:
            skin_cluster = find_deformer_by_type(mesh, 'skinCluster')
            
            if not skin_cluster:
                cmds.select(cl = True)
                base_joint = cmds.joint(n = 'joint_%s' % wire_deformer)
            
                skin_cluster = cmds.skinCluster(base_joint, mesh, tsb = True)[0]
            
                cmds.parent(base_joint, convert_group)
            
            for joint in joints:
                found_skin = find_deformer_by_type(mesh, 'skinCluster')
                
                cmds.skinCluster(skin_cluster, e = True, ai = joint, wt = 0.0, nw = 1)     
                bindPre_locator = add_joint_bindpre(found_skin, joint, description)
                cmds.parent(bindPre_locator, bindPre_locator_group)
                
                parameter = cmds.getAttr('%s.param' % joint)
                geo.attach_to_curve(bindPre_locator, base_curve, True, parameter) 
                
        if skin:
            verts = cmds.ls('%s.vtx[*]' % mesh, flatten = True)
            
            wire_weights = get_wire_weights(wire_deformer, inc)
            
            weighted_verts = []
            weights = {}
            verts_inc = {}
            
            for inc in xrange(0, len(wire_weights)):
                if wire_weights[inc] > 0:
                    weighted_verts.append(verts[inc])
                    weights[verts[inc]] = wire_weights[inc]
                    verts_inc[verts[inc]] = inc
            
            skin_cluster = find_deformer_by_type(mesh, 'skinCluster')
            
            base_joint = None
            
            if not skin_cluster:
                cmds.select(cl = True)
                base_joint = cmds.joint(n = 'joint_%s' % wire_deformer)
                
                skin_cluster = cmds.skinCluster(base_joint, mesh, tsb = True)[0]
                
                cmds.parent(base_joint, convert_group)
                
            if skin_cluster and not base_joint:
                base_joint = get_skin_influence_at_index(0, skin_cluster)
            
            distance_falloff = falloff
            
            for joint in joints:
                
                cmds.skinCluster(skin_cluster, e = True, ai = joint, wt = 0.0, nw = 1)     
                bindPre_locator = add_joint_bindpre(skin_cluster, joint, description)
                cmds.parent(bindPre_locator, bindPre_locator_group)
                
                parameter = cmds.getAttr('%s.param' % joint)
                geo.attach_to_curve(bindPre_locator, base_curve, True, parameter)
            
            
            for vert in weighted_verts:
                
                if weights[vert] < 0.0001:
                        continue
                
                distances = space.get_distances(joints, vert)
                
                joint_count = len(joints)
                
                smallest_distance = distances[0]
                distances_in_range = []
                smallest_distance_inc = 0
                
                for inc in xrange(0, joint_count):
                    if distances[inc] < smallest_distance:
                        smallest_distance_inc = inc
                        smallest_distance = distances[inc]
                
                distance_falloff = smallest_distance*1.3
                if distance_falloff < falloff:
                    distance_falloff = falloff
                
                for inc in xrange(0, joint_count):

                    if distances[inc] <= distance_falloff:
                        distances_in_range.append(inc)

                if smallest_distance >= distance_falloff or not distances_in_range:
                    
                    weight_value = weights[vert]
                    
                    cmds.skinPercent(skin_cluster, vert, r = False, transformValue = [joints[smallest_distance_inc], weight_value])

                    continue

                if smallest_distance <= distance_falloff or distances_in_range:

                    total = 0.0
                    
                    joint_weight = {}
                    
                    inverted_distances = {}
                    
                    for distance_inc in distances_in_range:
                        distance = distances[distance_inc]
                        
                        distance_weight = distance/distance_falloff
                        distance_weight = vtool.util.fade_sigmoid(distance_weight)
                        
                        inverted_distance = distance_falloff - distance*distance_weight*distance_weight
                        
                        inverted_distances[distance_inc] = inverted_distance
                        
                    for inverted_distance in inverted_distances:
                        total += inverted_distances[inverted_distance]
                        
                    for distance_inc in distances_in_range:
                        weight = inverted_distances[distance_inc]/total
                        
                        joint_weight[joints[distance_inc]] = weight
                    
                    weight_value = weights[vert]
                    
                    segments = []
                    
                    for joint in joint_weight:
                        joint_value = joint_weight[joint]
                        value = weight_value*joint_value
                        
                        segments.append( (joint, value) )
                    
                    cmds.skinPercent(skin_cluster, vert, r = False, transformValue = segments)    
                        
                            
            for joint in joints:
                
                cmds.skinCluster(skin_cluster,e=True,inf=joint,lw = True)
        
        inc += 1
    
    cmds.setAttr('%s.envelope' % wire_deformer, 0)
    
    if delete_wire:
        attr.disconnect_attribute('%s.baseWire[0]' % wire_deformer)
        cmds.delete(wire_deformer)
        
    cmds.parent(joints_group, convert_group)
    
    cmds.hide(convert_group)
    
    return convert_group, control_group, zero_verts



def convert_wire_to_skinned_joints(wire_deformer, description, joint_count = 10, falloff = 1):
    """
    Convert a wire deformer to skinned joints
    
    Args:
        wire_deformer (str): The name of a wire deformer.
        description (str): The description to give the setup.
        joint_count (int): The number of joints to create. Higher number better resembles the effect of a wire deformer, but gets slow fast.
        falloff (float): Corresponds to the wire distance value.
        
    Returns:
        str: The top group above the joints.
    """
    
    vtool.util.show('converting %s' % wire_deformer)
    
    convert_group = cmds.group(em = True, n = core.inc_name('convertWire_%s' % description))
    
    curve = attr.get_attribute_input('%s.deformedWire[0]' % wire_deformer, node_only = True)
    curve = cmds.listRelatives(curve, p = True)[0]
    
    
    joints = geo.create_oriented_joints_on_curve(curve, count = joint_count)
    
    meshes = cmds.deformer(wire_deformer, q = True, geometry = True)
    if not meshes:
        return
    
    inc = 0
    
    for mesh in meshes:
        
        skin = True                 
        if skin:
            verts = cmds.ls('%s.vtx[*]' % mesh, flatten = True)
            
            wire_weights = get_wire_weights(wire_deformer, inc)
            
            weighted_verts = []
            weights = {}
            verts_inc = {}
            
            for inc in xrange(0, len(wire_weights)):
                if wire_weights[inc] > 0:
                    weighted_verts.append(verts[inc])
                    weights[verts[inc]] = wire_weights[inc]
                    verts_inc[verts[inc]] = inc
            
            skin_cluster = find_deformer_by_type(mesh, 'skinCluster')
            
            base_joint = None
            
            if not skin_cluster:
                cmds.select(cl = True)
                base_joint = cmds.joint(n = 'joint_%s' % wire_deformer)
                
                skin_cluster = cmds.skinCluster(base_joint, mesh, tsb = True)[0]
                
                cmds.parent(base_joint, convert_group)
                
            if skin_cluster and not base_joint:
                base_joint = get_skin_influence_at_index(0, skin_cluster)
            
            distance_falloff = falloff
            
            for joint in joints:
                
                cmds.skinCluster(skin_cluster, e = True, ai = joint, wt = 0.0, nw = 1)     
            
            for vert in weighted_verts:
                
                if weights[vert] < 0.0001:
                        continue
                
                distances = space.get_distances(joints, vert)
                            
                joint_count = len(joints)
                
                smallest_distance = distances[0]
                distances_in_range = []
                smallest_distance_inc = 0
                
                for inc in xrange(0, joint_count):
                    if distances[inc] < smallest_distance:
                        smallest_distance_inc = inc
                        smallest_distance = distances[inc]
                
                distance_falloff = smallest_distance*1.3
                if distance_falloff < falloff:
                    distance_falloff = falloff
                
                for inc in xrange(0, joint_count):

                    if distances[inc] <= distance_falloff:
                        distances_in_range.append(inc)

                if smallest_distance >= distance_falloff or not distances_in_range:
                    
                    weight_value = weights[vert]

                    cmds.skinPercent(skin_cluster, vert, r = False, transformValue = [joints[smallest_distance_inc], weight_value])

                    continue

                if smallest_distance <= distance_falloff or distances_in_range:

                    total = 0.0
                    
                    joint_weight = {}
                    
                    inverted_distances = {}
                    
                    for distance_inc in distances_in_range:
                        distance = distances[distance_inc]
                        
                        distance_weight = distance/distance_falloff
                        distance_weight = vtool.util.fade_sigmoid(distance_weight)
                        
                        inverted_distance = distance_falloff - distance*distance_weight*distance_weight
                        
                        inverted_distances[distance_inc] = inverted_distance
                        
                    for inverted_distance in inverted_distances:
                        total += inverted_distances[inverted_distance]
                        
                    for distance_inc in distances_in_range:
                        weight = inverted_distances[distance_inc]/total
                        
                        joint_weight[joints[distance_inc]] = weight
                    
                    weight_value = weights[vert]
                    
                    segments = []
                    
                    for joint in joint_weight:
                        joint_value = joint_weight[joint]
                        value = weight_value*joint_value
                        
                        segments.append( (joint, value) )
                    
                    cmds.skinPercent(skin_cluster, vert, r = False, transformValue = segments)    
                                                
            for joint in joints:
                
                cmds.skinCluster(skin_cluster,e=True,inf=joint,lw = True)
        
        inc += 1
    
    cmds.setAttr('%s.envelope' % wire_deformer, 0)
        
    cmds.hide(convert_group)
    
    return convert_group
        
def transfer_joint_weight_to_joint(source_joint, target_joint, mesh = None):
    """
    Transfer the weight from one joint to another.  Does it for all vertices affected by source_joint in mesh.
    
    Args:
        source_joint (str): The name of a joint to take weights from.
        target_joint (str): The name of a joint to transfer weights to.
        mesh (str): The mesh to work with.
    """
    
    if mesh:
        meshes = vtool.util.convert_to_sequence(mesh)
    if not mesh:
        meshes = get_meshes_skinned_to_joint(source_joint)
    
    if not meshes:
        return
    
    
    
    for mesh in meshes:
    
        skin_deformer = find_deformer_by_type(mesh, 'skinCluster')
        
        influences = get_influences_on_skin(skin_deformer)
        
        if not target_joint in influences:
            cmds.skinCluster(skin_deformer, e = True, ai = target_joint, wt = 0.0, nw = 1)  
        
        index = get_index_at_skin_influence(source_joint, skin_deformer)
        
        if not index:
            cmds.warning( 'could not find index for %s on mesh %s' % (source_joint, mesh) )
            return
        
        other_index = get_index_at_skin_influence(target_joint, skin_deformer)
        
        weights = get_skin_weights(skin_deformer)
        
        cmds.setAttr('%s.normalizeWeights' % skin_deformer, 0)
        
        index_weights = weights[index]
        
        other_index_weights = None
        
        if other_index in weights:
            other_index_weights = weights[other_index]
        
        weight_count = len(index_weights)
        
        for inc in xrange(0,weight_count):
            
            if index_weights[inc] == 0:
                continue
            
            if other_index_weights == None:
                weight_value = index_weights[inc]
            
            if not other_index_weights == None:
                weight_value = index_weights[inc] + other_index_weights[inc]
            
            cmds.setAttr('%s.weightList[ %s ].weights[%s]' % (skin_deformer, inc, other_index), weight_value)
            cmds.setAttr('%s.weightList[ %s ].weights[%s]' % (skin_deformer, inc, index), 0)
        
        cmds.setAttr('%s.normalizeWeights' % skin_deformer, 1)
        cmds.skinCluster(skin_deformer, edit = True, forceNormalizeWeights = True)

def transfer_weight_from_joint_to_parent(joint, mesh):
    """
    Transfer the weight from child joint to parent joint.  Does it for all vertices affected by child joint in mesh.
    If no parent joint, then do nothing.
    
    Args:
        joint (str): The name of a joint to take weights from.
        mesh (str): The mesh to work with.
        
    """    
    parent_joint = cmds.listRelatives(joint, type = 'joint', p = True)
    
    if parent_joint:
        parent_joint = parent_joint[0]
        
    if not parent_joint:
        return
    
    transfer_joint_weight_to_joint(joint, parent_joint, mesh)
   
def transfer_cluster_weight_to_joint(cluster, joint, mesh):
    """
    Given the weights of a cluster, transfer them to a joint.
    
    """
    skin = find_deformer_by_type(mesh, 'skinCluster')
    
    weights = get_cluster_weights(cluster)
    
    for inc in xrange(0, len(weights)):
        
        vert = '%s.vtx[%s]' % (mesh, inc)
        
        cmds.skinPercent(skin, vert, r = False, transformValue = [joint, weights[inc]])
    
def transfer_joint_weight_to_blendshape(blendshape_node, joint, mesh, index = 0, target = -1):
    """
    Transfer the weight of a joint on a skincluster to a blendshape target weight.
    
    Args:
        blendshape_node (str): The name of a blendshape node.
        joint (str): The name of a joint influencing mesh.
        mesh (str): The name of a mesh that has joint has a skin influence.
        index (int): Is the index of the blendshaped mesh. Usually 0. Can be 1 or more if blendshape_node affects more than one mesh.
        target (int): If target is -1, than affect the base weights of the blendshapes... which affects all targets. If target = 0 or greater, then affect the weights of the target at that index.
    """
    skin = find_deformer_by_type(mesh, 'skinCluster')
    weights = get_skin_weights(skin)
    
    influence_index = get_index_at_skin_influence(joint, skin)
    
    weight_values = weights[influence_index]
    
    inc = 0
    
    if target == -1:
        for weight in weight_values:
            cmds.setAttr('%s.inputTarget[%s].baseWeights[%s]' % (blendshape_node, index, inc), weight)
            inc += 1
            
    if target >= 0:
        for weight in weight_values:
            cmds.setAttr('%s.inputTarget[%s].inputTargetGroup[%s].targetWeights[%s]' % (blendshape_node, index, target, inc), weight)
            inc += 1
    
def add_missing_influences(skin1, skin2):
    """
    Make sure used influences in skin1 are added to skin2. 
    When transfering skin weights this can be handy.
    
    Args:
        skin1 (str): The name of a skin cluster.
        skin2 (str): The name of a skin cluster.
    """

    influences1 = get_non_zero_influences(skin1)
    influences2 = get_non_zero_influences(skin2)
    
    for influence1 in influences1:
        
        if not influence1 in influences2:
            cmds.skinCluster(skin2, edit = True, ai = influence1, wt = 0.0, nw = 1)
    
@core.undo_chunk   
def skin_mesh_from_mesh(source_mesh, target_mesh, exclude_joints = [], include_joints = [], uv_space = False):
    ''' 
    This skins a mesh based on the skinning of another mesh.  
    Source mesh must be skinned.  The target mesh will be skinned with the joints in the source.
    The skinning from the source mesh will be projected onto the target mesh.
    exlude_joints = joints to exclude from the target's skin cluster.
    include_joints = only include the specified joints. 
    If exlude_joints, only exclude_joints in include_joints will be excluded.
    
    Args:
        source_mesh (str): The name of a mesh.
        target_mesh (str): The name of a mesh.
        exlude_joints (list): Exclude the named joints from the skin cluster.
        include_joints (list): Include the named joint from the skin cluster.
        uv_space (bool): Wether to copy the skin weights in uv space rather than point space.
    '''
    
    vtool.util.show('skinning %s' % target_mesh)
    
    skin = find_deformer_by_type(source_mesh, 'skinCluster')
    
    if not skin:
        cmds.warning('%s has no skin. Nothing to copy.' % source_mesh)
        return
    
    other_skin = find_deformer_by_type(target_mesh, 'skinCluster')
    
    if other_skin:
        cmds.warning('%s already has a skin cluster. Deleteing existing.' % target_mesh)
        cmds.delete(other_skin)
        other_skin = None
    
    influences = get_non_zero_influences(skin)
    
    for exclude in exclude_joints:
        if exclude in influences:
            influences.remove(exclude)
    
    if include_joints:
        found = []
        for include in include_joints:
            if include in influences:
                found.append(include)
        
        influences = found
    
    if not other_skin:  
        skin_name = core.get_basename(target_mesh)
        other_skin = cmds.skinCluster(influences, target_mesh, tsb=True, n = core.inc_name('skin_%s' % skin_name))[0]
      
    if other_skin:
        if not uv_space:
            cmds.copySkinWeights(ss = skin, 
                                 ds = other_skin, 
                                 noMirror = True, 
                                 surfaceAssociation = 'closestPoint', 
                                 influenceAssociation = ['name'], 
                                 normalize = True)
        
        if uv_space:
            cmds.copySkinWeights(ss = skin, 
                                 ds = other_skin, 
                                 noMirror = True, 
                                 surfaceAssociation = 'closestPoint', 
                                 influenceAssociation = ['name'],
                                 uvSpace = ['map1','map1'], 
                                 normalize = True)

def skin_group_from_mesh(source_mesh, group, include_joints = [], exclude_joints = []):
    ''' 
    This skins a group of meshes based on the skinning of the source mesh.  
    Source mesh must be skinned.  The target group will be skinned with the joints in the source.
    The skinning from the source mesh will be projected onto the meshes in the group.
    exlude_joints = joints to exclude from the target's skin cluster.
    include_joints = only include the specified joints. 
    If exlude_joints, only exclude_joints in include_joints will be excluded.
    
    
    Args:
        source_mesh (str): The name of a mesh.
        group (str): The name of a group.
        exlude_joints (list): Exclude the named joints from the skin cluster.
        include_joints (list): Include the named joint from the skin cluster.
    '''
    
    
    old_selection = cmds.ls(sl = True)
    
    cmds.select(cl = True)
    cmds.select(group)
    cmds.refresh()
    
    relatives = cmds.listRelatives(group, ad = True, type = 'transform')
    relatives.append(group)
    
    for relative in relatives:
        
        shape = geo.get_mesh_shape(relative)
        
        if shape and cmds.nodeType(shape) == 'mesh':
            skin_mesh_from_mesh(source_mesh, relative, include_joints = include_joints, exclude_joints = exclude_joints)
            
    if old_selection:
        cmds.select(old_selection)

    
def skin_lattice_from_mesh(source_mesh, target, divisions = [10,10,10], falloff = [2,2,2], name = None, include_joints = [], exclude_joints = []):
    ''' 
    This skins a lattice based on the skinning of the source mesh.
    The lattice is generated automatically around the target mesh using divisions and falloff parameters.  
    Source mesh must be skinned.  The target lattice will be skinned with the joints in the source.
    The skinning from the source mesh will be projected onto the target lattice.
    exlude_joints = joints to exclude from the target's skin cluster.
    include_joints = only include the specified joints. 
    If exlude_joints, only exclude_joints in include_joints will be excluded.
    
    Args:
        source_mesh (str): The name of a mesh.
        target (str): The name of a group or mesh.
        divisions (list): eg [10,10,10] the divisions of the lattice.
        falloff (list): eg [2,2,2] the falloff of the divisions of the lattice.
        name (str): The description to give the lattice.
        exlude_joints (list): Exclude the named joints from the skin cluster.
        include_joints (list): Include the named joint from the skin cluster.
    '''
    
    group = cmds.group(em = True, n = 'lattice_%s_gr' % target)
    
    if not name:
        name = target
    
    ffd, lattice, base = cmds.lattice(target, 
                                      divisions = divisions, 
                                      objectCentered = True, 
                                      ldv = falloff, n = 'lattice_%s' % name)
    
    cmds.parent(lattice, base, group)
    cmds.hide(group)
    
    skin_mesh_from_mesh(source_mesh, lattice, exclude_joints = exclude_joints, include_joints = include_joints)
    
    return group

def skin_curve_from_mesh(source_mesh, target, include_joints = [], exclude_joints = []):
    ''' 
    This skins a curve based on the skinning of the source mesh.  
    Source mesh must be skinned.  The target curve will be skinned with the joints in the source.
    The skinning from the source mesh will be projected onto the curve.
    exlude_joints = joints to exclude from the target's skin cluster.
    include_joints = only include the specified joints. 
    If exlude_joints, only exclude_joints in include_joints will be excluded.
    
    Args:
    
        source_mesh (str): The name of a mesh.
        target (str): The name of a curve.
        exlude_joints (list): Exclude the named joints from the skin cluster.
        include_joints (list): Include the named joint from the skin cluster.
    '''
    
    skin_mesh_from_mesh(source_mesh, target, exclude_joints = exclude_joints, include_joints = include_joints)

def skin_group(joints, group):
    """
    Skin all the meshes in a group to the specified joints.  
    Good for attaching the face geo to the head joint.
    
    Args:
        joints (list): A list of joints to skin to.
        group (str): The group to skin.
    """
    rels = cmds.listRelatives(group, ad = True, f = True)
    
    for rel in rels:
        
        name = rel.split('|')[-1]
        
        try:
            cmds.skinCluster(joints, rel, tsb = True, n = 'skin_%s' % name)
        except:
            pass
            

def lock_joint_weights(skin_cluster, skip_joints = None):
    """
    Lock the joints in the skin cluster except joints in skip_joints
    
    Args:
        skin_cluster (str): The name of a skin cluster.
        skip_joints (list): The names of the joints to skip.
    """
    influences = get_influences_on_skin(skin_cluster)
        
    if skip_joints:
        for influence in influences:
            cmds.skinCluster( skin_cluster, e= True, inf= influence, lw = False )
        
    for influence in influences:
        
        lock = True
          
        for joint in skip_joints:
            if joint == influence:
                lock = False
                break
            
        if lock:
            cmds.skinCluster( skin_cluster, e= True, inf= influence, lw = True )    

def get_closest_verts_to_joints(joints, verts):
    """
    Get the closest vertices to a joint.
    
    Args:
        joints (list): A list of joints.
        verts (list): A list of vertices.
    
    Returns: 
        dict: dict[joint] = vertex list
    """

    distance_dict = {}

    for joint in joints:
        
        joint_pos = cmds.xform(joint, q = True, ws = True, t = True)
        
        for vert in verts:
            
            if not vert in distance_dict:
                distance_dict[vert] = [10000000000000000000, None]
            
            pos = cmds.xform(vert, q = True, ws = True, t = True)
            
            distance = vtool.util.get_distance(joint_pos, pos)
            
            if distance < distance_dict[vert][0]:
                distance_dict[vert][0] = distance
                distance_dict[vert][1] = joint
    
    joint_map = {}
    
    for key in distance_dict:
        
        joint = distance_dict[key][1]
        
        if not joint in joint_map:
            joint_map[joint] = []
            
        joint_map[joint].append(key)
        
    return joint_map    

def create_wrap(source_mesh, target_mesh):
    """
    Create an Maya exclusive bind wrap. 
    Source_mesh drives target_mesh.
    
    Args:
        source_mesh (str): The mesh to influence target_mesh. This can be a list of meshes.
        target_mesh (str): Mesh to be deformed by source_mesh.
        
    Returns:
        list: A list of base meshes.
    """
    
    source_mesh = vtool.util.convert_to_sequence(source_mesh)
    
    wrap = MayaWrap(target_mesh)
    wrap.set_driver_meshes(source_mesh)
    
    wrap.create()
    
    return wrap.base_meshes

"""
def exclusive_bind_wrap(source_mesh, target_mesh):
    wrap = MayaWrap(target_mesh)
    
    source_mesh = vtool.util.convert_to_sequence(source_mesh)
    
    wrap.set_driver_meshes(source_mesh)
        
    wraps = wrap.create()
    
    return wraps
"""
    
def wire_mesh(curve, mesh, falloff):
    """
    Create a wire deformer.
    
    Args:
        curve (str): The name of a curve.
        mesh (str): The name of a mesh.
        falloff (float): The falloff of the wire influence.
        
    Returns:
        list: [wire_deformer, wire_curve]
    """
    wire_deformer, wire_curve = cmds.wire(mesh,  gw = False, w = curve, n = 'wire_%s' % curve, dds = [0, falloff])
    cmds.setAttr('%s.rotation' % wire_deformer, 0)
    
    return wire_deformer, wire_curve
    
def wire_to_mesh(edges, geometry, description, auto_edge_path = True):
    """
    One mesh follows the other via a wire deformer.
    A nurbs curve is generated automatically from the edges provided. 
    
    auto_edge_path = The command will try fill in gaps between edges.
    
    Args:
        edges (list): The edges from the source mesh to build the wire curve from. Eg. ["node_name.e[0]"]
        geometry (list): The target geometry that should follow.
        description (str): The description to give the setup.
        auto_edge_path (bool): Wether to fill in the path between the edges.
        
    Returns:
        str: The group name for the setup.
    """
    group = cmds.group(em = True, n = core.inc_name('setup_%s' % description))
    
    if auto_edge_path:
        edge_path = geo.get_edge_path(edges)
    if not auto_edge_path:
        edge_path = cmds.ls(edges, flatten = True)
    
    curve = geo.edges_to_curve(edge_path, description)
    
    cmds.parent(curve, group)
    
    wire_deformer, wire_curve = cmds.wire(geometry,  gw = False, w = curve, n = 'wire_%s' % description)
    
    spans = cmds.getAttr('%s.spans' % curve)
    
    
    cmds.dropoffLocator( 1, 1, wire_deformer, '%s.u[0]' % curve, '%s.u[%s]' % (curve,spans) )
    
    cmds.addAttr(curve, ln = 'twist', k = True)
    cmds.connectAttr('%s.twist' % curve, '%s.wireLocatorTwist[0]' % wire_deformer)
    cmds.connectAttr('%s.twist' % curve, '%s.wireLocatorTwist[1]' % wire_deformer)
    
    return group
    
@core.undo_chunk
def weight_hammer_verts(verts = None, print_info = True):
    """
    Convenience to use Maya's weight hammer command on many verts individually.
    
    Args:
        verts (list): The names of verts to weigth hammer. If verts = None, currently selected verts will be hammered. 
        
    """
    if geo.is_a_mesh(verts):
        verts = cmds.ls('%s.vtx[*]' % verts, flatten = True)
    
    if verts:
        verts = cmds.ls(verts, flatten = True)
    
    if not verts:
        verts = cmds.ls(sl = True, flatten = True)
    
    count = len(verts)
    inc = 0
    
    for vert in verts:
        cmds.select(cl = True)
        cmds.select(vert)
        
        if print_info:
            
            #do not remove
            print inc, 'of', count
        
        mel.eval('weightHammerVerts;')
            
        inc += 1
        


def map_blend_target_alias_to_index(blendshape_node):
    """
    Get the aliases for blendshape weight targets and the index of the target.
    
    Args:
        blendshape_node (str): The name of the blendshape.
    
    Returns: 
        dict: dict[alias] = target index
    """
    
    aliases = cmds.aliasAttr(blendshape_node, query = True)
    
    alias_map = {}
    
    if not aliases:
        return
    
    for inc in range(0, len(aliases), 2):
        alias = aliases[inc]
        weight = aliases[inc+1]
        
        index = vtool.util.get_end_number(weight)
        
        alias_map[index] = alias
        
    return alias_map

def map_blend_index_to_target_alias(blendshape_node):
    """
    Get a map between the target index and its alias name on the blendshape.
    
    Args:
        blendshape_node (str): The name of the blendshape.
    
    Returns: 
        dict: dict[target index] = weight alias
    """
    
    
    aliases = cmds.aliasAttr(blendshape_node, query = True)
    
    alias_map = {}
    
    if not aliases:
        return
    
    for inc in range(0, len(aliases), 2):
        alias = aliases[inc]
        weight = aliases[inc+1]
        
        index = vtool.util.get_end_number(weight)
        
        alias_map[alias] = index
        
    return alias_map

def get_index_at_alias(alias, blendshape_node):
    """
    Given a blendshape weight alias, get the corresponding target index.
    
    Args:
        alias (str): The name of the weight alias.
    
    Returns: 
        int: The corresponding target index to the alias.
    """
    
    map_dict = map_blend_index_to_target_alias(blendshape_node)
    
    if alias in map_dict:
        return map_dict[alias]

@core.undo_chunk
def chad_extract_shape(skin_mesh, corrective, replace = False):
    """
    Get the delta of t he skin cluster and blendshape to the corrective.  
    Requires a skin cluster or blendshape in the deformation stack.
    
    Args:
        skin_mesh (str): The name of the skinned mesh, or blendshaped mesh to extract a delta from.
        corrective (str): The target shape for the skin mesh.  
        replace (bool): Wether to replace the corrective with the delta.
        
    Returns:
        str: The name of the delta. The delta can be applied to the blendshape before the skin cluster.
    """
    
    try:
        
        envelopes = EnvelopeHistory(skin_mesh)
        
        skin = find_deformer_by_type(skin_mesh, 'skinCluster')
        
        maya_version = cmds.about(version = True)
        
        if vtool.util.get_maya_version() < 2017 and maya_version.find('2016 Extension 2') == -1:
            if not cmds.pluginInfo('cvShapeInverterDeformer.py', query=True, loaded=True):
            
                split_name = __name__.split('.')
            
                file_name = __file__
                file_name = file_name.replace('%s.py' % split_name[-1], 'cvShapeInverterDeformer.py')
                file_name = file_name.replace('.pyc', '.py')
                
                cmds.loadPlugin( file_name )
            
            import cvShapeInverterScript as correct
        
        envelopes.turn_off()
        
        if skin:
            cmds.setAttr('%s.envelope' % skin, 1)
        
        if vtool.util.get_maya_version() < 2017 and maya_version.find('2016 Extension 2') == -1:
            offset = correct.invert(skin_mesh, corrective)
            cmds.delete(offset, ch = True)
        if vtool.util.get_maya_version() >= 2017 or maya_version.find('2016 Extension 2') > -1:
            if not cmds.pluginInfo('invertShape', query=True, loaded=True):
                cmds.loadPlugin( 'invertShape' )
            offset = mel.eval('invertShape %s %s' % (skin_mesh, corrective))
        
        orig = get_intermediate_object(skin_mesh)
        
        orig = geo.create_shape_from_shape(orig, 'home')
        
        envelopes.turn_on(respect_initial_state=True)
        envelopes.turn_off_referenced()
        
        envelopes.turn_off_exclude(['blendShape'])
        
        skin_shapes = core.get_shapes(skin_mesh)
        skin_mesh_name = core.get_basename(skin_mesh, True)
        other_delta = geo.create_shape_from_shape(skin_shapes[0], core.inc_name(skin_mesh_name))
        
        if skin:
            cmds.setAttr('%s.envelope' % skin, 1)
        
        quick_blendshape(other_delta, orig, -1)
        quick_blendshape(offset, orig, 1)
        
        cmds.select(cl = True)
        
        cmds.delete(orig, ch = True)
        cmds.delete(other_delta)
        cmds.delete(offset)
        
        cmds.rename(orig, offset)
        
        if replace:
            parent = cmds.listRelatives(corrective, p = True)
            cmds.delete(corrective)
            
            offset = cmds.rename(offset, corrective)
            
            if parent:
                cmds.parent(offset, parent)
        
        envelopes.turn_on(respect_initial_state=True)
        
        reset_tweaks_on_mesh(skin_mesh)
        
        return offset
        
    except (RuntimeError):
        vtool.util.error( traceback.format_exc() )
    
    
def get_blendshape_delta(orig_mesh, source_meshes, corrective_mesh, replace = True):
    """
    Create a delta following the equation:
    delta = orig_mesh + corrective_mesh - source_meshes
    
    Args:
        orig_mesh (str): The unchanged base mesh.
        source_meshes (list): Name of the mesh that represents where the mesh has moved. Can be a list or a single target. 
        corrective_mesh (str): Name of the mesh where the source mesh needs to move to.
    
    Returns: 
        str: name of new delta mesh
    """
    
    sources = vtool.util.convert_to_sequence(source_meshes)
    
    offset = cmds.duplicate(corrective_mesh)[0]
    
    if cmds.nodeType(orig_mesh) == 'transform':
        shapes = core.get_shapes(orig_mesh)
        
        if shapes:
            orig_mesh = shapes[0]
    
    orig = geo.create_shape_from_shape(orig_mesh, 'home')
    new_sources = []
    for source in sources:
        
        other_delta = cmds.duplicate(source)[0]
        quick_blendshape(other_delta, orig, -1)
        new_sources.append(other_delta)
    
    quick_blendshape(offset, orig, 1)
    
    cmds.select(cl = True)
    
    cmds.delete(orig, ch = True)
    cmds.delete(offset)
    cmds.delete(new_sources)
    
    corrective = cmds.rename(orig, 'delta_%s' % corrective_mesh)

    if replace:
        parent = cmds.listRelatives(corrective_mesh, p = True)
        
        cmds.delete(corrective_mesh)
        
        corrective = cmds.rename(corrective, corrective_mesh)
        
        if parent:
            cmds.parent(corrective, parent[0])
    
    return corrective


def create_surface_joints(surface, name, uv_count = [10, 4], offset = 0):
    """
    Create evenly spaced joints on a surface.
    
    Args:
        surface (str): the name of a nurbs surface.
        name(str): = the name to give to nodes created.
        uv_count(list): = number of joints on u and v, eg [10,4]
        offset(float): = the offset from the border.
        
    Returns:
        list: [top_group, joints] The top group is the group for the joints. The joints is a list of joints by name that were created.
    """
    
    section_u = (1.0-offset*2) / (uv_count[0]-1)
    section_v = (1.0-offset*2) / (uv_count[1]-1)
    section_value_u = 0 + offset
    section_value_v = 0 + offset
    
    top_group = cmds.group(em = True, n = core.inc_name('rivetJoints_1_%s' % name))
    joints = []
    
    for inc in xrange(0, uv_count[0]):
        
        for inc2 in xrange(0, uv_count[1]):
            
            rivet = geo.Rivet(name)
            rivet.set_surface(surface, section_value_u, section_value_v)
            rivet.set_create_joint(True)
            joint = rivet.create()
            cmds.parent(joint, top_group)
            joints.append(joint)
            
            section_value_v += section_v
        
        section_value_v = 0 + offset
            
        section_value_u += section_u
        
        
        
    return top_group, joints
        
    
def quick_blendshape(source_mesh, target_mesh, weight = 1, blendshape = None):
    """
    Create a blendshape. Add target source_mesh into the target_mesh.
    If target_mesh already has a blendshape, add source_mesh into existing blendshape.
    
    Args:
        blendshape (str): The name of the blendshape to work with.
        target_mesh (str): The name of the target mesh to add into the blendshape.
        weight (float): The value to set the weight of the target to.
        blendshape (str): The name of the blendshape to edit. If None, it will be set to 'blendshape_%s' % target_mesh.
        
    Returns:
        str: The name of the blendshape node.
    """
    
    blendshape_node = blendshape
    
    source_mesh_name = source_mesh.split('|')[-1]
    
    bad_blendshape = False
    long_path = None
    
    base_name = core.get_basename(target_mesh, remove_namespace = True)
    
    if not blendshape_node:
        blendshape_node = 'blendshape_%s' % base_name
    
    if cmds.objExists(blendshape_node):
        
        shapes = cmds.deformer(blendshape_node, q = True, g = True)
        
        target_shapes = core.get_shapes_in_hierarchy(target_mesh)
        
        if len(shapes) == len(target_shapes):
                        
            long_path = cmds.ls(shapes[0], l = True)[0]
            
            if long_path != target_shapes[0]:
                
                bad_blendshape = True
        
        if len(shapes) != len(target_shapes):
            
            bad_blendshape = True
        
        long_path = None
        
        
        if not bad_blendshape:
            
            bad_blendshape = False
            
            for inc in xrange(len(target_shapes)):
            
                target_shape = target_shapes[inc]
                shape = shapes[inc]
                
                long_path = cmds.ls(shape, l = True)[0]
                
                if not long_path in target_shape:
                    bad_blendshape = True
                    
                    break
        
        if not bad_blendshape:
            count = cmds.blendShape(blendshape_node, q= True, weightCount = True)
            
            cmds.blendShape(blendshape_node, edit=True, tc = False, t=(target_mesh, count+1, source_mesh, 1.0) )
            
            try:
                cmds.setAttr('%s.%s' % (blendshape_node, source_mesh_name), weight)
            except:
                pass
            
            return blendshape_node
       
    if bad_blendshape:
        
        blendshape_node = core.inc_name(blendshape_node)
        
    if not cmds.objExists(blendshape_node):
        
        cmds.blendShape(source_mesh, target_mesh, tc = False, weight =[0,weight], n = blendshape_node, foc = True)
        
    try:
        cmds.setAttr('%s.%s' % (blendshape_node, source_mesh_name), weight)
    except:
        pass
        
    return blendshape_node
    
def isolate_shape_axis(base, target, axis_list = ['X','Y','Z']):
    """
    Given a base mesh, only take axis movement on the target that is specified in axis_list.
    
    Args:
        base (str): The base mesh that has no targets applied.
        target (str): The target mesh vertices moved to a different position than the base.
        axis_list (list): The axises of movement allowed. If axis_list = ['X'], only vertex movement on x will be present in the result.
    
    Returns:
        str: A new mesh with verts moving only on the isolated axis.
    """
    
    
    verts = cmds.ls('%s.vtx[*]' % target, flatten = True)
    
    if not verts:
        return
    
    vert_count = len(verts)
    
    axis_name = string.join(axis_list, '_')
    
    new_target = cmds.duplicate(target, n = '%s_%s' % (target, axis_name))[0]
    
    for inc in xrange(0, vert_count):
        
        base_pos = cmds.xform('%s.vtx[%s]' % (base, inc), q = True, t = True, ws = True)
        target_pos = cmds.xform('%s.vtx[%s]' % (target, inc), q = True, t = True, ws = True)
        
        if (base_pos == target_pos):
            continue
        
        small_x = False
        small_y = False
        small_z = False
        if abs(base_pos[0]-target_pos[0]) < 0.0001:
            small_x = True
        if abs(base_pos[1]-target_pos[1]) < 0.0001:
            small_y = True
        if abs(base_pos[2]-target_pos[2]) < 0.0001:
            small_z = True
            
        if small_x and small_y and small_z:
            continue
            
        if not 'X' in axis_list:
            target_pos[0] = base_pos[0]
        if not 'Y' in axis_list:
            target_pos[1] = base_pos[1]
        if not 'Z' in axis_list:
            target_pos[2] = base_pos[2]
            
        cmds.xform('%s.vtx[%s]' % (new_target, inc), ws = True, t = target_pos)
        
    return new_target
    
def reset_tweak(tweak_node):
    """
    Reset the tweak node in deformation history.
    
    Args:
        tweak_node (str): The name of the tweak node.
    """
    
    if not cmds.objExists('%s.vlist' % tweak_node):
        return
    
    indices = attr.get_indices('%s.vlist' % tweak_node)
    
    for index in indices:
        try:
            sub_indices = attr.get_indices('%s.vlist[%s].vertex' % (tweak_node, index))
            
            if not sub_indices:
                continue
            
            for sub_index in sub_indices:
                cmds.setAttr('%s.vlist[%s].vertex[%s].xVertex' % (tweak_node, index, sub_index), 0.0)
                cmds.setAttr('%s.vlist[%s].vertex[%s].yVertex' % (tweak_node, index, sub_index), 0.0)
                cmds.setAttr('%s.vlist[%s].vertex[%s].zVertex' % (tweak_node, index, sub_index), 0.0)
        except:
            vtool.util.error( traceback.format_exc() )
    return

def reset_tweaks_on_mesh(mesh):
        
    tweaks = find_deformer_by_type(mesh, 'tweak', return_all = True)
    
    for tweak in tweaks:
        reset_tweak(tweak)