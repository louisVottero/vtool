from vtool.maya_lib import util
import vtool.util

import maya.cmds as cmds

class Control( util.Control ):
    
    def __init__(self, control_name):
        
        super(Control, self).__init__(control_name)
        
        if not cmds.objExists('%s.ClientAnimCtrl' % self.control):
            cmds.addAttr(self.control, ln = 'ClientAnimCtrl', at = 'bool', dv = 1, k = False)
            cmds.setAttr('%s.ClientAnimCtrl' % self.control, l = True)

def find_root_group():
    top_nodes = util.get_top_dag_nodes(exclude_cameras = True)
    
    for node in top_nodes:
        if node.startswith('root_'):
            return node

def get_name(description1, description2 = '', side = 'C'):
        
    if side == 'L' or side == 'R':
        name = '%s_%s%s' % (side, description1, description2)
        
    if side == 'C':
        name = '%s%s' % (description1, description2)
            
    return name

def create_attr_separator(node, title = '____________________'):

    var = util.MayaEnumVariable(title)
    var.set_enum_names([' '])
    
    var.create(node)
    
def create_space_group(transform, name = None):
    
    if not name:
        name = '%s_space' % transform
    
    group = cmds.group(em = True, n = name)
    
    util.MatchSpace(transform, group).translation_rotation()
    
    parent = cmds.listRelatives(transform, p = True)
    
    if parent:
        cmds.parent(group, parent)
        
    cmds.parent(transform, group)
    
    return group

def create_match_group(transform, name):
    
    group = cmds.group(em = True, n = name)
    
    util.MatchSpace(transform, group).translation_rotation()
    
    parent = cmds.listRelatives(transform, p = True)
    
    if parent:
        cmds.parent(group, parent)
    
    return group

def create_position_group(transforms, target_transform):
    
    transforms = vtool.util.convert_to_sequence(transforms)
    
    for transform in transforms:
        name = target_transform.replace('space', 'pos')
        
        pos = cmds.group(em = True, n = util.inc_name(name))
    
        util.MatchSpace(target_transform, pos).translation_rotation()
        cmds.parent(pos, transform)
        cmds.parentConstraint(pos, target_transform)

def create_control( name, shape = 'circle'):
    
    control = Control(name)
    control.set_curve_type(shape)
    control.hide_visibility_attribute()
    control.hide_scale_attributes()
    
    return control

def create_fk_control(transform, name, shape):
    
    control = create_control( name, shape )
    
    space = create_space_group(control.get())
    control.hide_scale_attributes()
    
    util.MatchSpace(transform, space).translation_rotation()
    
    return control, space

def create_joint_control(joint, shape = 'circle'):
    
    control = Control('temp_control1')
    control.set_curve_type(shape)
    control.set_to_joint(joint)
    control.hide_visibility_attribute()
    
    attrs = util.OrientJointAttributes(joint)
    attrs.delete()
    
    return control

def create_follow_switches(source_transforms, target_transform, constraint_type = 'parent', values = []):
    
    inc = 0
    
    for transform in source_transforms:
        
        follower = cmds.group(em = True, n = util.inc_name('%s_pos' % transform))
        
        util.MatchSpace(target_transform, follower).translation_rotation()
        
        cmds.parent(follower, transform)
        
        if constraint_type == 'parent':
            constraint = cmds.parentConstraint(follower, target_transform)
        if constraint_type == 'point':
            constraint = cmds.pointConstraint(follower, target_transform)
        if constraint_type == 'orient':
            constraint = cmds.orientConstraint(follower, target_transform)
            
        constraint = constraint[0]
        
        print inc
        
        constraint_attr = '%s.%sW%s' % (constraint,
                                        follower,
                                        inc)
        
        cmds.addAttr(target_transform, ln = transform, min = 0, max = 1, k = True)
        
        attribute_name = '%s.%s' % (target_transform, transform)
        
        cmds.connectAttr(attribute_name,  constraint_attr)
        
        if inc < len(values):
            cmds.setAttr(attribute_name, values[inc])
        
        inc += 1
    
def create_space_switch():
    pass

def add_length(control, offset_joint):
    
    length = util.MayaNumberVariable('length')
    length.set_min_value(0)
    length.set_value(10)
    length.create(control)
    
    offset_joint_value = cmds.getAttr('%s.translateX' % offset_joint)
    offset_value = offset_joint_value/10.0
    
    lock = util.LockState('%s.translateX' % offset_joint)
    lock.unlock()
    
    multiply = util.connect_multiply('%s.length' % control, '%s.translateX' % offset_joint, offset_value)
    
    multiply = cmds.rename(multiply, '%s_multiply' % control)
    
    blend = cmds.createNode('blendTwoAttr', n = '%s_switch_blender' % control)
    
    cmds.connectAttr('%s.outputX' % multiply, '%s.input[0]' % blend)
    
    util.disconnect_attribute('%s.translateX' % offset_joint)
    cmds.connectAttr('%s.output' % blend, '%s.translateX' % offset_joint)
    
    lock.restore_initial()
    

def set_color_to_side(control, side, sub = False):
    
    control = Control(control)
    
    if side == 'L':
        color = 6
    
    if side == 'R':
        color = 13
    
    if side == 'C':
        color = 17

    if sub:
    
        if side == 'L':
            color = 18
        
        if side == 'R':
            color = 20
        
        if side == 'C':
            color =  21
    
    control.color(color)
    
    def set_joints(self, joints):
        
        joints = vtool.util.convert_to_sequence(joints)
        self.joints = joints
    
def create_stretchy_spline_ik(curve, side, description1, description2):
    
    length_node = cmds.arclen(curve, ch = True, n = get_name(description1, '%sIkCurveInfo' % description2, side))
    length = cmds.getAttr('%s.arcLength' % length_node)
    
    multi_factor = cmds.createNode('multiplyDivide', n = get_name(description1, '_%sScaleFactor_multi' % description2, side))
    multi_normal = cmds.createNode('multiplyDivide', n = get_name(description1, '_%sScaleNormalize_multi' % description2, side))
    multi_stretch = cmds.createNode('multiplyDivide', n = get_name(description1, '_%sAutoStretch_multi' % description2, side))
    multi_length = cmds.createNode('multiplyDivide', n = get_name(description1, '_%sJointLength_multi' % description2, side))
    
    cmds.setAttr('%s.operation' % multi_normal, 2)
    cmds.setAttr('%s.input2X' % multi_normal, length)
    
    cmds.connectAttr('%s.arcLength' % length_node, '%s.input1X' % multi_factor)
    cmds.connectAttr('%s.outputX' % multi_factor, '%s.input1X' % multi_normal)
    cmds.connectAttr('%s.outputX' % multi_normal, '%s.input1X' % multi_stretch)
    cmds.connectAttr('%s.outputX' % multi_stretch, '%s.input1X' % multi_length)
    
    return multi_length
    
class Rig(object):
    
    def __init__(self, description, side):
        
        self.joints = []
        self.locators = []
        
        self.description = description
        self.side = side
        
        if not cmds.objExists('DoNotTouch'):
            cmds.group(em = True, n = 'DoNotTouch')
        
        name = self._get_name('_all')
        
        self.main_group = name
        
        if not cmds.objExists(name):
            self.main_group = cmds.group(em = True, n = name)
        
    def _get_name(self, description = ''):
        name = get_name(self.description, description, self.side)
        """
        if self.side == 'L' or self.side == 'R':
            name = '%s_%s%s' % (self.side, self.description, description)
                
        if self.side == 'C':
            name = '%s%s' % (self.description, description)
        """ 
        return name
    
    def set_joints(self, joints):
        
        self.joints = vtool.util.convert_to_sequence(joints)
        
    def set_locators(self, locators):
        self.locators = vtool.util.convert_to_sequence(locators)
        
#--- Body

class IkFkAppendageRig( Rig ):
    
    def __init__(self, description, side):
        super(IkFkAppendageRig, self).__init__(description, side)
        
        self.mid_attribute_name = 'elbow'
        self.state_attribute_name = None
        
    def _create_joint_control(self, joint, shape = 'circle'):
        
        control = create_joint_control(joint, shape)

        set_color_to_side(control.get(), self.side)
        
        control.hide_scale_and_visibility_attributes()
        
        return control
    
    def _create_main_fk_controls(self):
        
        top = self._create_joint_control(self.joints[0], 'cube')
        mid = self._create_joint_control(self.joints[1], 'cube')
        end = self._create_joint_control(self.joints[2])
        
        mid.translate_shape(0.5, 0, 0)
        
        add_length(top.get(), mid.get())
        add_length(mid.get(), end.get())
        
        end.rotate_shape(90, 0, 0)
        
        group = create_space_group(top.get(), '%s_up%s_space' % (self.side, self.description.capitalize()))
        
        cmds.parent(self.bendy_up_joints[0], group)
        
        cmds.parent(group, self.top_orient_control.get())
        
        self.top_fk_control = top
        self.mid_fk_control = mid
        self.btm_fk_control = end
        
        cmds.parent(self.bendy_lo_joints[0], self.mid_fk_control.get())
    
    def _create_top_orient(self):
        
        name = self._get_name('Orient_ctrl')
        control = create_control(name, 'pin_four_corner')
        control.scale_shape(.7, .7, .7)
        control.hide_translate_attributes()
        
        space_group = create_space_group(control.get())
        
        util.MatchSpace(self.joints[0], space_group).translation()
        
        cmds.parent(space_group, self.main_group)
        
        if self.side == 'R':
            cmds.setAttr('%s.rotateX' % space_group, 180)
        
        self.top_orient_control = control
        self.top_orient_space = space_group
        
        #control.color(7)
        set_color_to_side(control.get(), self.side)
        
        
    def _create_top_orient_ik(self):
        
        joint_top_orient = util.duplicate_joint_section(self.joints[0], self._get_name('UpFk_aimJoint'))
        cmds.parent(joint_top_orient[0], self.top_orient_control.get())
        
        self.top_aim_joint = joint_top_orient[0]
    
        handle = util.IkHandle('temp')
        handle.set_start_joint(joint_top_orient[0])
        handle.set_end_joint(joint_top_orient[1])
        handle.set_solver(handle.solver_sc)
        
        ik_name = self._get_name('_aimIkHandle')
        handle.set_full_name(ik_name)
        handle.create()
        
        cmds.hide(handle.ik_handle)
        
        cmds.parent(handle.ik_handle, self.main_group)
        cmds.pointConstraint(self.joints[1], handle.ik_handle)
        
    def _create_main_ik_control(self):
        
        control = create_control(self._get_name('Ik_ctrl'))
        control.hide_scale_attributes()
        util.MatchSpace(self.joints[2], control.get()).translation_rotation()
        spacer = create_space_group(control.get())
        cmds.parent(spacer, self.main_group)
        self.main_ik_control = control
        self.main_ik_control_space = spacer
        set_color_to_side(self.main_ik_control.get(), self.side)
        
    def _create_pole_vector_control(self):
        
        control = create_control(self._get_name('Upv_ctrl'), 'cube_locator')
        control.scale_shape(.5, .5, .5)
        control.hide_scale_attributes()
        self.pole_control = control.get()
        util.MatchSpace(self.joints[1], control.get()).translation_rotation()
        spacer = create_space_group(control.get())
        cmds.parent(spacer, self.main_group)
        
        position = util.get_polevector(self.joints[0], self.joints[1], self.joints[2], .5)
        cmds.xform(spacer, t = position)
        
        set_color_to_side(control.get(), self.side)
    
    def _create_ik_handle(self):
        
        handle = util.IkHandle('temp')
        handle.set_start_joint(self.joints[0])
        handle.set_end_joint(self.joints[2])
        handle.set_solver(handle.solver_rp)
        
        ik_name = self._get_name('_ikHandle')
        handle.set_full_name(ik_name)
        handle.create()
        
        cmds.hide(handle.ik_handle)
        
        ik_group_name = ik_name + '_grp'
        
        group = create_match_group(self.joints[2], ik_group_name)
        
        self.ik_handle_group = group
        self.ik_handle = handle.ik_handle
        cmds.parent(handle.ik_handle, group)
        cmds.parent(group, self.main_group)
        
        cmds.parentConstraint(self.main_ik_control.get(), group)[0]
        
        self._create_state_switch(self.ik_handle)
    
        self._constraint_pole_vector()
    
    def _create_state_switch(self, ik_handle):
        name = self._get_name('state_clamp')
        clamp = cmds.createNode('clamp', n = name)
        
        cmds.connectAttr('%s.%s' % (self.top_orient_control.get(), self.state_attribute_name),
                        '%s.inputR' % clamp)
        
        cmds.connectAttr('%s.outputR' % clamp, '%s.ikBlend' % ik_handle)
        
        cmds.setAttr('%s.maxR' % clamp, 1)
        
        util.connect_multiply('%s.ikBlend' % ik_handle, 
                              '%s.visibility' % self.main_ik_control.get(), 1)
        
        name = self._get_name('IkVis_reverse')
        reverse = cmds.createNode('reverse', n = name)
        
        cmds.connectAttr('%s.ikBlend' % ik_handle, '%s.inputX' % reverse)
        
        controls = [self.top_fk_control, self.mid_fk_control, self.btm_fk_control]
        
        for control in controls:
            cmds.connectAttr('%s.outputX' % reverse, '%sShape.visibility' % control.get() )
            
        pole_parent = cmds.listRelatives(self.pole_control, p = True)[0]
        cmds.connectAttr('%s.ikBlend' % ik_handle, '%s.visibility' % pole_parent)
        
    def _constraint_pole_vector(self):
        
        cmds.poleVectorConstraint(self.pole_control, self.ik_handle)
        
    def _create_ik_fk_attribute(self):
        
        attribute_name = '%sState' % self.description
        var = util.MayaEnumVariable(attribute_name)
        var.set_enum_names(['fk','ik'])
        var.set_locked(False)
        var.create(self.top_orient_control.get())
        
        self.state_attribute_name = attribute_name

    def _get_joint_blend_switch(self, joint):
        
        input_value = util.get_attribute_input('%s.translateX' % joint, node_only = True)
        
        if input_value:
            if cmds.nodeType(input_value) == 'blendTwoAttr':
                return input_value

    def _create_stretchy(self):
        
        self._create_stretchy_attributes(self.main_ik_control.get())
        
        distance_clamp, distance_multi = self._create_stretchy_distance(self.main_ik_control.get())
        
        stretch_plus, ratio_plus = self._create_stretchy_attribute_offset(self.main_ik_control.get())
        
        cmds.connectAttr('%s.output1D' % stretch_plus, '%s.minR' % distance_clamp)
        cmds.connectAttr('%s.output2Dx' % ratio_plus, '%s.input1X' % distance_multi)
        cmds.connectAttr('%s.output2Dy' % ratio_plus, '%s.input1Y' % distance_multi)
        
    def _create_stretchy_distance(self, attribute_control):

        locator1 = cmds.spaceLocator(n = '%s_pos' % self.top_fk_control.get())[0]
        locator2 = cmds.spaceLocator(n = '%s_pos' % self.btm_fk_control.get())[0]
        locator3 = cmds.spaceLocator(n = '%s_pos' % self.pole_control)[0]
        
        cmds.hide(locator1, locator2, locator3)
        
        util.MatchSpace(self.joints[0], locator1).translation_rotation()
        util.MatchSpace(self.joints[2], locator2).translation_rotation()
        util.MatchSpace(self.pole_control, locator3).translation_rotation()
        
        cmds.parent(locator1, self.top_orient_space)
        cmds.parent(locator2, self.ik_handle_group)
        cmds.parent(locator3, self.pole_control)
        
        distance = cmds.createNode('distanceBetween', n = self._get_name('_distance'))
        distance_up_arm = cmds.createNode('distanceBetween', n = self._get_name('ToUpV_distance'))
        distance_lo_arm = cmds.createNode('distanceBetween', n = self._get_name('ToLoV_distance'))
        
        cmds.connectAttr('%s.worldPosition[0]' % locator1, '%s.point1' % distance)
        cmds.connectAttr('%s.worldPosition[0]' % locator2, '%s.point2' % distance)
        
        cmds.connectAttr('%s.worldPosition[0]' % locator1, '%s.point1' % distance_up_arm)
        cmds.connectAttr('%s.worldPosition[0]' % locator3, '%s.point2' % distance_up_arm)
        
        cmds.connectAttr('%s.worldPosition[0]' % locator3, '%s.point1' % distance_lo_arm)
        cmds.connectAttr('%s.worldPosition[0]' % locator2, '%s.point2' % distance_lo_arm)
        
        clamp = cmds.createNode('clamp', n = self._get_name('Distance_clamp'))
        
        multiply = util.connect_multiply('%s.distance' % distance, '%s.inputR' % clamp, 1)
        multiply = cmds.rename(multiply, self._get_name('Ik_distance_normalize'))
        
        distance_value = cmds.getAttr('%s.distance' % distance)
        
        cmds.setAttr('%s.minR' % clamp, distance_value)
        cmds.setAttr('%s.maxR' % clamp, (distance_value * 100))
        
        multi = cmds.createNode('multiplyDivide', n = self._get_name('StretchyFinal_multi'))
        
        cmds.connectAttr('%s.outputR' % clamp, '%s.input2X' % multi)
        cmds.connectAttr('%s.outputR' % clamp, '%s.input2Y' % multi)
        
        up_blend = cmds.createNode('blendTwoAttr', n = '%s_up%s_ikLength_blend' % (self.side, self.description.capitalize()))
        cmds.connectAttr('%s.outputX' % multi, '%s.input[0]' % up_blend)
        #cmds.connectAttr('%s.outputX' % multiply, '%s.input[1]' % up_blend)
        cmds.connectAttr('%s.%sLock' % (attribute_control,self.mid_attribute_name), '%s.attributesBlender' % up_blend)
        mult_up = util.connect_multiply('%s.distance' % distance_up_arm, '%s.input[1]' % up_blend, 1)
        mult_up = cmds.rename(mult_up, self._get_name('ToUpv_distance_normalize'))
        
        up_joint_blend = self._get_joint_blend_switch(self.joints[1])
        cmds.connectAttr('%s.output' % up_blend, '%s.input[1]' % up_joint_blend)
        cmds.connectAttr('%s.ikBlend' % self.ik_handle, '%s.attributesBlender' % up_joint_blend)
        
        lo_blend = cmds.createNode('blendTwoAttr', n = '%s_lo%s_ikLength_blend' % (self.side, self.description.capitalize()))
        cmds.connectAttr('%s.outputY' % multi, '%s.input[0]' % lo_blend)
        #cmds.connectAttr('%s.outputX' % multiply, '%s.input[1]' % lo_blend)
        cmds.connectAttr('%s.%sLock' % (attribute_control,self.mid_attribute_name), '%s.attributesBlender' % lo_blend)
        mult_lo = util.connect_multiply('%s.distance' % distance_lo_arm, '%s.input[1]' % lo_blend, 1)
        mult_lo = cmds.rename(mult_lo, self._get_name('ToLov_distance_normalize'))
        
        lo_joint_blend = self._get_joint_blend_switch(self.joints[2])
        cmds.connectAttr('%s.output' % lo_blend, '%s.input[1]' % lo_joint_blend)
        cmds.connectAttr('%s.ikBlend' % self.ik_handle, '%s.attributesBlender' % lo_joint_blend)
        
        return clamp, multi
    """
    def _create_elbow_distance(self):

        locator1 = cmds.spaceLocator(n = '%s_pos' % self.top_fk_control.get())[0]
        locator2 = cmds.spaceLocator(n = '%s_pos' % self.btm_fk_control.get())[0]
        
        util.MatchSpace(self.joints[0], locator1).translation_rotation()
        util.MatchSpace(self.joints[2], locator2).translation_rotation()
        
        cmds.parent(locator1, self.top_orient_space)
        cmds.parent(locator2, self.ik_handle_group)
        
        distance = cmds.createNode('distanceBetween', n = self._get_name('_distance'))
    """
    def _create_stretchy_attribute_offset(self, attribute_control):
        
        length1 = abs(cmds.getAttr('%s.translateX' % self.joints[1]))
        length2 = abs(cmds.getAttr('%s.translateX' % self.joints[2]))
        
        total_distance = length1 + length2
        
        ratio1 = length1/total_distance
        ratio2 = length2/total_distance
        
        if self.side == 'R':
            ratio1 = -1 * ratio1
            ratio2 = -1 * ratio2
        
        stretch_plus = cmds.createNode('plusMinusAverage', n = self._get_name('Stretchy_plus'))
        ratio_plus = cmds.createNode('plusMinusAverage', n = self._get_name('Ratio_plus'))
        
        multi = util.connect_multiply('%s.stretchy' % attribute_control, '%s.input1D[0]' % stretch_plus, total_distance * 0.1)
        multi = cmds.rename(multi, self._get_name('Stretchy_multi'))
        
        cmds.setAttr('%s.input1D[1]' % stretch_plus, total_distance)
        
        sub_ratio1 = -0.05
        sub_ratio2 = 0.05
        
        if self.side == 'R':
            sub_ratio1 = 0.05
            sub_ratio2 = -0.05
            
        multi = util.connect_multiply('%s.ratio' % attribute_control, '%s.input2D[0].input2Dx' % ratio_plus, sub_ratio1)
        multi = cmds.rename(multi, self._get_name('Ratio_multi'))
        
        cmds.connectAttr('%s.ratio' % attribute_control, '%s.input1Y' % multi)
        cmds.connectAttr('%s.outputY' % multi, '%s.input2D[0].input2Dy' % ratio_plus)
        cmds.setAttr('%s.input2Y' % multi, sub_ratio2)
        
        cmds.setAttr('%s.input2D[1].input2Dx' % ratio_plus, ratio1)
        cmds.setAttr('%s.input2D[1].input2Dy' % ratio_plus, ratio2)
        
        return stretch_plus, ratio_plus
        
    def _create_stretchy_attributes(self, node):

        create_attr_separator(node)

        var = util.MayaNumberVariable('stretchy')
        var.set_min_value(-10)
        var.set_max_value(200)
        var.create(node)
        
        var = util.MayaNumberVariable('ratio')
        var.set_min_value(-10)
        var.set_max_value(10)
        var.create(node)

        var = util.MayaNumberVariable('%sLock' % self.mid_attribute_name)
        var.set_min_value(0)
        var.set_max_value(1)
        var.create(node)  
        
    def _create_stretchy_spline_ik(self, curve, description):
        
        length_node = cmds.arclen(curve, ch = True, n = self._get_name('%sIkCurveInfo' % description))
        length = cmds.getAttr('%s.arcLength' % length_node)
        
        multi_factor = cmds.createNode('multiplyDivide', n = self._get_name('_%sScaleFactor_multi' % description))
        multi_normal = cmds.createNode('multiplyDivide', n = self._get_name('_%sScaleNormalize_multi' % description))
        multi_stretch = cmds.createNode('multiplyDivide', n = self._get_name('_%sAutoStretch_multi' % description))
        multi_length = cmds.createNode('multiplyDivide', n = self._get_name('_%sJointLength_multi' % description))
        
        cmds.setAttr('%s.operation' % multi_normal, 2)
        cmds.setAttr('%s.input2X' % multi_normal, length)
        #cmds.setAttr('%s.input2X' % multi_length, joint_length)
        
        cmds.connectAttr('%s.arcLength' % length_node, '%s.input1X' % multi_factor)
        cmds.connectAttr('%s.outputX' % multi_factor, '%s.input1X' % multi_normal)
        cmds.connectAttr('%s.outputX' % multi_normal, '%s.input1X' % multi_stretch)
        cmds.connectAttr('%s.outputX' % multi_stretch, '%s.input1X' % multi_length)
        
        return multi_length
        
        
    def _create_bendy_chain(self):
        
        joint1 = util.duplicate_joint_section(self.joints[0], '%s_up%s0_joint' % (self.side, self.description))
        
        joint2 = util.duplicate_joint_section(self.joints[1], '%s_lo%s0_joint' % (self.side, self.description))
        
        if self.side == 'R':
            
            orient = util.OrientJointAttributes(joint1[0])
            orient.delete()
            orient = util.OrientJoint(joint1[0])
            orient.set_aim_at(3)
            orient.set_aim_up_at(0)
            orient.set_up_vector([0,-1,0])
            orient.run()
            cmds.makeIdentity(joint1[1], apply = True, jo = True)
            
            orient = util.OrientJointAttributes(joint2[0])
            orient.delete()
            orient = util.OrientJoint(joint2[0])
            orient.set_aim_at(3)
            orient.set_up_vector([0,-1,0])
            orient.set_aim_up_at(0)
            orient.run()
            cmds.makeIdentity(joint2[1], apply = True, jo = True)
        
        cmds.parent(joint1[0], joint2[0], self.main_group)
        
        joints_up = util.subdivide_joint(joint1[0], joint1[1], 3)
        joints_lo = util.subdivide_joint(joint2[0], joint2[1], 3)
        
        joints_up.insert(0, joint1[0])
        joints_up.append(joint1[1])
        
        joints_lo.insert(0, joint2[0])
        joints_lo.append(joint2[1])
        
        self.bendy_up_joints = []
        self.bendy_lo_joints = []
        
        for inc in range(0, 5):
            
            new_name = cmds.rename(joints_up[inc], '%s_up%s%s_joint' % (self.side, self.description, inc))
            
            self.bendy_up_joints.append(new_name)
            
            new_name = cmds.rename(joints_lo[inc], '%s_lo%s%s_joint' % (self.side, self.description, inc))
            self.bendy_lo_joints.append(new_name)
            
    def _create_bendy_mid_control(self):
        
        control = create_control(self._get_name('_mid_ctrl'),'cube')
        control.scale_shape(.3, 1.5, 1.5)
        space = create_space_group(control.get())
        
        util.MatchSpace(self.joints[1], space).translation_rotation()
        
        cmds.parent(space, self.mid_fk_control.get())
        
        set_color_to_side(control.get(), self.side)
        
        return control
        
    def _create_bendy_control(self, prefix, top_joint, btm_joint):
        
        control = create_control('%s_%s%s_midCtrl' % (self.side, prefix, self.description))
        space = create_space_group(control.get())
        
        midpoint = util.get_midpoint(top_joint, btm_joint)
        
        
        util.MatchSpace(top_joint, space).rotation()
        
        
        cmds.xform(space, t = midpoint)
        
        check_joints = []
        if prefix == 'lo':
            check_joints = self.bendy_lo_joints
        if prefix == 'up':
            check_joints = self.bendy_up_joints
        
        closest_joint = util.get_closest_transform(space, check_joints)
        util.MatchSpace(closest_joint, space).rotation()
        
        control.rotate_shape(0, 0, 90)
        
        set_color_to_side(control.get(), self.side, sub = True)
        
        
        
        return control, space
        
    def _locator_group(self, description):
        
        top_loc = cmds.spaceLocator(n = util.inc_name(self._get_name('_%sCtrl1' % description)))[0]
        edit_loc = cmds.group(em = True, n = util.inc_name(self._get_name('_%sEditV1' % description)))
        end_loc = cmds.spaceLocator(n = util.inc_name(self._get_name('_%sV1' % description)))[0]
            
        cmds.hide(top_loc, end_loc)
            
        cmds.parent(end_loc, edit_loc)
        cmds.parent(edit_loc, top_loc)
        
        return top_loc, edit_loc, end_loc
            
    def _create_bendy_ik(self, joints, curve, description):
        
        ik_handle = util.IkHandle(self._get_name(description))
        ik_handle.set_solver(ik_handle.solver_spline)
        ik_handle.set_joints(joints)
        ik_handle.set_curve(curve)
        ik_handle.create()
        
        cmds.hide(ik_handle.ik_handle)
        
        cmds.parent(ik_handle.ik_handle, 'DoNotTouch')
        
        return ik_handle.ik_handle
        
        
    def _create_bendy_curve(self, joints, description):
        
        curve = util.transforms_to_curve(joints, 2, 'temp')
        
        curve = cmds.rename(curve, self._get_name(description))
        
        cmds.rebuildCurve(curve, ch = False, rpo = True, rt = 0, end = 1, kr = 0, kcp = 0, kep = 1, kt = 0, s = 1, d = 2)
        cmds.delete('%s.cv[2]' % curve)
        mid_value = util.get_midpoint(joints[0], joints[-1])
        
        cmds.xform('%s.cv[1]' % curve, t = mid_value)
        
        cmds.parent(curve, 'DoNotTouch')
        
        cmds.hide(curve)
        
        return curve
       
    def _create_bendy_guide_joints(self):
        
        #up
        cmds.select(cl = True)
        joint0 = cmds.joint(n = '%s_up%s0_ctrl' % (self.side, self.description))
        util.MatchSpace(self.joints[0], joint0).translation_rotation()
        cmds.makeIdentity(joint0, apply = True, r = True)
        
        cmds.select(cl = True)
        joint1 = cmds.joint(n = '%s_up%s1_ctrl' % (self.side, self.description))
        util.MatchSpace(self.joints[0], joint1).translation_rotation()
        cmds.makeIdentity(joint1, apply = True, r = True)
        
        midpoint = util.get_midpoint(self.joints[0], self.joints[1])
        cmds.xform(joint1, t = midpoint)
        
        cmds.select(cl = True)
        joint2 = cmds.joint(n = '%s_up%s2_ctrl' % (self.side, self.description))
        util.MatchSpace(self.joints[1], joint2).translation_rotation()
        cmds.makeIdentity(joint2, apply = True, r = True)
        
        self.bendy_up_guide_joints = [joint0,joint1,joint2]
        
        #lo
        cmds.select(cl = True)
        joint0 = cmds.joint(n = '%s_lo%s0_ctrl' % (self.side, self.description))
        util.MatchSpace(self.joints[1], joint0).translation_rotation()
        cmds.makeIdentity(joint0, apply = True, r = True)
        
        cmds.select(cl = True)
        joint1 = cmds.joint(n = '%s_lo%s1_ctrl' % (self.side, self.description))
        util.MatchSpace(self.joints[1], joint1).translation_rotation()
        cmds.makeIdentity(joint1, apply = True, r = True)
        
        midpoint = util.get_midpoint(self.joints[1], self.joints[2])
        cmds.xform(joint1, t = midpoint)
        
        cmds.select(cl = True)
        joint2 = cmds.joint(n = '%s_lo%s2_ctrl' % (self.side, self.description))
        util.MatchSpace(self.joints[2], joint2).translation_rotation()
        cmds.makeIdentity(joint2, apply = True, r = True)
        
        self.bendy_lo_guide_joints = [joint0,joint1,joint2]
        
    def _attach_bendy_ends(self, ik, top_parent, btm_parent):
        
        top, top_edit, top_end = self._locator_group('up')
        
        util.MatchSpace(top_parent, top).translation_rotation()
        cmds.parent(top, top_parent)
        
        cmds.connectAttr('%s.worldMatrix' % top_end, '%s.dWorldUpMatrix' % ik)
        
        btm, btm_edit, btm_end = self._locator_group('lo')
        
        util.MatchSpace(btm_parent, btm).translation_rotation()
        util.MatchSpace(btm_parent, btm).translation_rotation()
        cmds.parent(btm, btm_parent)
        
        cmds.connectAttr('%s.worldMatrix' % btm_end, '%s.dWorldUpMatrixEnd' % ik)
        
        cmds.setAttr('%s.dTwistControlEnable' % ik, 1)
        cmds.setAttr('%s.dWorldUpType' % ik, 4)
        
        return top, btm, top_edit, btm_edit
        
    def _create_fk(self):
        
        self._create_main_fk_controls()
    
    def _create_ik(self):
        
        self._create_main_ik_control()
        self._create_pole_vector_control()
        self._create_ik_handle()
        self._create_stretchy() 
           
    def _create_bendy(self):
        
        mid_control = self._create_bendy_mid_control()
        
        up_control, up_space = self._create_bendy_control('up', self.joints[0], self.joints[1])
        lo_control, lo_space = self._create_bendy_control('lo', self.joints[1], self.joints[2])
        
        self._create_bendy_guide_joints()
        
        cmds.parent(up_space, self.top_aim_joint)
        cmds.parent(lo_space, self.joints[1])
        
        curve_up = self._create_bendy_curve(self.bendy_up_joints, '_upIkCurve')
        up_ik = self._create_bendy_ik(self.bendy_up_joints, curve_up, '_upIkCurve')
        
        curve_lo = self._create_bendy_curve(self.bendy_lo_joints, '_loIkCurve')
        lo_ik = self._create_bendy_ik(self.bendy_lo_joints, curve_lo, '_loIkCurve')
        
        self.up_ik = up_ik
        self.lo_ik = lo_ik
        
        cmds.skinCluster(self.bendy_up_guide_joints, curve_up)
        cmds.skinCluster(self.bendy_lo_guide_joints, curve_lo)
        
        top_loc, btm_loc, top_edit, btm_edit = self._attach_bendy_ends(up_ik, self.top_aim_joint, mid_control.get())
        cmds.parent(self.bendy_up_guide_joints[0], top_loc)
        cmds.parent(self.bendy_up_guide_joints[2], btm_loc)
        cmds.pointConstraint(top_loc, btm_loc, up_space)
        
        self.up_edits = [top_edit, btm_edit]
        
        cmds.aimConstraint(btm_loc, up_space, wuo = top_loc, wut = 'objectrotation')
        
        top_loc, btm_loc, top_edit, btm_edit = self._attach_bendy_ends(lo_ik, mid_control.get(), self.joints[2])
        cmds.parent(self.bendy_lo_guide_joints[0], top_loc)
        cmds.parent(self.bendy_lo_guide_joints[2], btm_loc)
        cmds.pointConstraint(top_loc, btm_loc, lo_space)
        
        self.lo_edits = [top_edit, btm_edit]
        
        #up_vector = [0,1,0]
        #if self.side == 'R':
        #    up_vector = [0,-1,0]
        
        cmds.aimConstraint(btm_loc, lo_space, wuo = top_loc, wut = 'objectrotation')
        
        cmds.parent(self.bendy_up_guide_joints[1], up_control.get())
        cmds.parent(self.bendy_lo_guide_joints[1], lo_control.get())
        
        multi = create_stretchy_spline_ik(curve_up, self.side, self.description, 'up')
        
        joint_length = cmds.getAttr('%s.translateX' % self.bendy_up_joints[1])
        cmds.setAttr('%s.input2X' % multi, joint_length)
        for joint in self.bendy_up_joints[1:]:
            cmds.connectAttr('%s.outputX' % multi, '%s.translateX' % joint)
        
        multi = create_stretchy_spline_ik(curve_lo, self.side, self.description, 'lo')
        
        joint_length = cmds.getAttr('%s.translateX' % self.bendy_lo_joints[1])
        cmds.setAttr('%s.input2X' % multi, joint_length)
        for joint in self.bendy_lo_joints[1:]:
            cmds.connectAttr('%s.outputX' % multi, '%s.translateX' % joint)
    
    def _create_twist_correct(self):
        
        
        cmds.addAttr( self.top_orient_control.get(), ln = 'twistCorrectUp', min = 0, max = 1, k = True)
        cmds.addAttr( self.top_orient_control.get(), ln = 'twistCorrectLo', min = 0, max = 1, k = True)
        
        multi_up =util.connect_multiply('%s.twistCorrectUp' % self.top_orient_control.get(), 
                              '%s.rotateX' % self.up_edits[1],
                              90)
        
        cmds.setAttr('%s.input2Y' % multi_up, -90)
        cmds.connectAttr('%s.outputY' % multi_up, '%s.twist' % self.up_ik)
        
        #cmds.connectAttr('%s.')
        
        multi_lo = util.connect_multiply('%s.twistCorrectLo' % self.top_orient_control.get(), 
                              '%s.rotateX' % self.lo_edits[0], 
                              90)
    
        cmds.connectAttr('%s.outputX' % multi_lo, '%s.rotateX' % self.lo_edits[1])
        cmds.setAttr('%s.input2Y' % multi_lo, -90)
        cmds.connectAttr('%s.outputY' % multi_lo, '%s.twist' % self.lo_ik)
    
    
    def set_mid_attribute_name(self, name):
        self.mid_attribute_name = name
    
    def create(self):
        
        self._create_bendy_chain()
        
        self._create_top_orient()
        self._create_top_orient_ik()
        self._create_ik_fk_attribute()
        
        self._create_fk()
        self._create_ik()
        self._create_bendy()
        self._create_twist_correct()
        
        self.top_fk_control.hide_translate_attributes()
        self.mid_fk_control.hide_translate_attributes()
        self.btm_fk_control.hide_translate_attributes()
        
class ArmRig( IkFkAppendageRig ):
    
    def __init__(self, description, side):
        super(ArmRig, self).__init__(description, side)
        
    def _create_ik_hand(self):
        
        handle = util.IkHandle('temp')
        handle.set_start_joint(self.joints[2])
        handle.set_end_joint(self.joints[3])
        handle.set_solver(handle.solver_rp)
        
        ik_name = self._get_name('HandFk_ikHandle')
        handle.set_full_name(ik_name)
        handle.create()
        
        self.hand_ik = handle.ik_handle
        
        cmds.hide(handle.ik_handle)
        
        cmds.parent(self.hand_ik, self.ik_handle_group)
        cmds.connectAttr('%s.ikBlend' % self.ik_handle, '%s.ikBlend' % self.hand_ik)

    def _create_ik(self):
        
        self._create_main_ik_control()
        self._create_pole_vector_control()
        self._create_ik_handle()
        self._create_ik_hand()
        self._create_stretchy() 

    def _create_main_ik_controls(self):
        
        super(ArmRig, self)._create_main_ik_controls()
        
        if self.side == 'R':
            locator = cmds.spaceLocator(n = util.inc_name(self._get_name('temp')))[0]
            space = create_space_group(locator)
            
            util.MatchSpace(self.joints[2], space).translation_rotation()
            
            cmds.setAttr('%s.rotateX' % locator, -180)
            
            util.MatchSpace(locator, self.main_ik_control_space).translation_rotation()
            
            cmds.delete(space)
            
        self._zero_out_ik_controls()
            
    def _zero_out_ik_controls(self):
        x = cmds.getAttr('%s.rotateX' % self.main_ik_control_space)
        y = cmds.getAttr('%s.rotateY' % self.main_ik_control_space)
        z = cmds.getAttr('%s.rotateZ' % self.main_ik_control_space)
        
        cmds.setAttr('%s.rotateX' % self.main_ik_control.get(), x)
        cmds.setAttr('%s.rotateY' % self.main_ik_control.get(), y)
        cmds.setAttr('%s.rotateZ' % self.main_ik_control.get(), z)
        
        cmds.setAttr('%s.rotateX' % self.main_ik_control_space, 0)
        cmds.setAttr('%s.rotateY' % self.main_ik_control_space, 0)
        cmds.setAttr('%s.rotateZ' % self.main_ik_control_space, 0)
                
class LegRig(IkFkAppendageRig):
    
    def _create_main_ik_control(self):
        
        control = create_control('%s_foot_ctrl' % self.side)
        control.hide_scale_attributes()
        util.MatchSpace(self.joints[2], control.get()).translation_rotation()
        spacer = create_space_group(control.get())
        cmds.parent(spacer, self.main_group)
        self.main_ik_control = control
        self.main_ik_control_space = spacer
        set_color_to_side(self.main_ik_control.get(), self.side)
        
        cmds.setAttr('%s.rotateX' % self.main_ik_control_space, 0)
        cmds.setAttr('%s.rotateY' % self.main_ik_control_space, 0)
        cmds.setAttr('%s.rotateZ' % self.main_ik_control_space, 0)
        
    def _create_ik_fk_attribute(self):
        
        attribute_name = '%sState' % self.description
        var = util.MayaEnumVariable(attribute_name)
        var.set_enum_names(['fk','ik', self.mid_attribute_name])
        var.set_locked(False)
        
        var.create(self.top_orient_control.get())
        
        self.state_attribute_name = attribute_name
        
    def _create_pole_vector_control(self):
        
        control = create_control(self._get_name('Upv_ctrl'), 'pyramid')
        control.scale_shape(.5, .5, .5)
        control.rotate_shape(0, 0, 90)
        control.hide_scale_attributes()
        self.pole_control = control.get()
        util.MatchSpace(self.joints[1], control.get()).translation_rotation()
        spacer = create_space_group(control.get())
        cmds.parent(spacer, self.main_group)
        
        position = util.get_polevector(self.joints[0], self.joints[1], self.joints[2], .5)
        cmds.xform(spacer, t = position)
        
        set_color_to_side(control.get(), self.side)
        
    def _create_main_fk_controls(self):
        
        top = self._create_joint_control(self.joints[0], 'cube')
        mid = self._create_joint_control(self.joints[1], 'cube')
        end = self._create_joint_control(self.joints[2], 'cube')
        
        mid.translate_shape(0.5, 0, 0)
        
        add_length(top.get(), mid.get())
        add_length(mid.get(), end.get())
        
        end.rotate_shape(90, 0, 0)
        
        group = create_space_group(top.get(), '%s_up%s_space' % (self.side, self.description.capitalize()))
        
        cmds.parent(self.bendy_up_joints[0], group)
        
        cmds.parent(group, self.top_orient_control.get())
        
        self.top_fk_control = top
        self.mid_fk_control = mid
        self.btm_fk_control = end
        
        cmds.parent(self.bendy_lo_joints[0], self.mid_fk_control.get())
        
    def _create_twist_correct(self):
            
        cmds.addAttr( self.top_orient_control.get(), ln = 'twistCorrectUp', min = 0, max = 1, k = True)
        
        multi_up =util.connect_multiply('%s.twistCorrectUp' % self.top_orient_control.get(), 
                              '%s.rotateX' % self.up_edits[0],
                              90)
        
        cmds.connectAttr('%s.outputX' % multi_up, '%s.rotateX' % self.up_edits[1])
        cmds.setAttr('%s.input2Y' % multi_up, -90)
        cmds.connectAttr('%s.outputY' % multi_up, '%s.roll' % self.up_ik)
    
    def _constraint_pole_vector(self):
        
        locator = cmds.spaceLocator(n = self._get_name('_upV_side') )[0]
        cmds.hide(locator)
        
        util.MatchSpace(self.joints[2], locator).translation()
        
        space = create_space_group(locator)
        edit = create_space_group(locator, name = '%s_edit' % locator)
        
        cmds.parent(space, self.main_ik_control.get())
        
        movement = -5
        
        if self.side == 'R':
            movement = 5
        
        cmds.move(movement, 0, 0, locator, relative = True)
        
        plus = cmds.createNode('plusMinusAverage', n = self._get_name('UpV_ctrl_side_plus'))
        clamp = cmds.createNode('clamp', n = self._get_name('UpV_ctrl_side_clamp'))
        reverse = cmds.createNode('reverse', n = self._get_name('_upV_side_reverse'))
        
        cmds.connectAttr('%s.legState' % self.top_orient_control.get(), '%s.input1D[0]' % plus)
        cmds.setAttr('%s.input1D[1]' % plus, -1)
        cmds.connectAttr('%s.output1D' % plus, '%s.inputR' % clamp)
        
        cmds.connectAttr('%s.outputR' % clamp, '%sShape.visibility' % self.pole_control)
        cmds.connectAttr('%s.outputR' % clamp, '%s.inputX' % reverse)
        
        const = cmds.poleVectorConstraint(self.pole_control, locator, self.ik_handle)[0]
        
        cmds.setAttr('%s.maxR' % clamp, 1)
        cmds.connectAttr('%s.outputR' % clamp, '%s.%sW0' % (const, self.pole_control))
        cmds.connectAttr('%s.outputX' % reverse, '%s.%sW1' % (const, locator))
    
        pole_offset = -90
        if self.side == 'R':
            pole_offset = 90
    
        util.connect_multiply('%s.outputX' % reverse, '%s.twist' % self.ik_handle, pole_offset)
    
class SpineRig( Rig ):
    
    def _create_fk_controls(self):
        
        inc = 0
        
        last_control = None
        first_space = None
        
        self.fk_controls = []
        
        for locator in self.locators:
            
            
            control, space = create_fk_control(locator, util.inc_name('%sFk1_ctrl' % self.description), 'octogon')
            self.fk_controls.append(control)
            
            if inc == 0:
                first_space = space
            
            set_color_to_side(control.get(), self.side)
            
            cmds.delete(locator)

            if last_control:
                cmds.parent(space, last_control.get())
            
            last_control = control
            inc += 1
            
        
        cmds.parent(first_space, self.main_group)    
            
    def _create_spline_ik(self):
        
        self.curve = util.transforms_to_curve(self.joints, 1, util.inc_name(self._get_name('Curve')))
        
        ik_handle = util.IkHandle(self._get_name('Curve'))
        ik_handle.set_solver(ik_handle.solver_spline)
        ik_handle.set_curve(self.curve)
        ik_handle.set_joints(self.joints)
        
        ik_handle.create()
        
        cmds.hide(ik_handle.ik_handle)
        
        cmds.parent(ik_handle.ik_handle, 'DoNotTouch')
        cmds.parent(ik_handle.curve, 'DoNotTouch')
        
        self.curve = ik_handle.curve
        self.ik_spline = ik_handle.ik_handle
        cmds.hide(self.curve)
        
        return ik_handle.ik_handle
        
    def _attach_curve(self):
        
        cvs = cmds.ls('%s.cv[*]' % self.curve, flatten = True)
        
        inc_name = 'lo'
        
        joints = []
        self.bend_spacers = []
        
        for inc in range(0, len(cvs)):
            
            cmds.select(cl = True)
            position = cmds.pointPosition(cvs[inc])
            joint = cmds.joint(n = '%s%s_ctrl_joint' % (self.description, inc))
            joints.append(joint)
            cmds.xform(joint, ws = True, t = position)
            
            if inc > 0 and inc < len(cvs)-1:
                control, space = create_fk_control(joint, 
                                  util.inc_name('%s%s_ctrl' % (inc_name, self.description.capitalize())),
                                  'circle')
                
                set_color_to_side(control.get(), self.side, sub = True)
                
                cmds.parent(joint, control.get())
                cmds.parent(space, self.main_group)
                
                self.bend_spacers.append(space)
                
                if inc_name == 'lo':
                    inc_name = 'up'
        
        cmds.parent(joints[0], self.main_group)
        self.ctrl_joints = joints
        
        return joints
        
    def _skin_curve(self, joints):
        cmds.skinCluster(self.curve, joints, tsb = True)    
        
    def _set_bendy_scale(self):
        multi = create_stretchy_spline_ik(self.curve, self.side, self.description, '')
        
        value = cmds.getAttr('%s.translateX' % self.joints[-1])
        cmds.setAttr('%s.input2X' % multi, value)
        
        for joint in self.joints[1:]:
            cmds.connectAttr('%s.outputX' % multi, '%s.translateX' % joint)
        
    def create(self):
        
        self._create_fk_controls()
        
        self._create_spline_ik()
        
        joints = self._attach_curve()
        self._skin_curve(joints)
        self._set_bendy_scale()
        
        cmds.parent(self.joints[0], self.main_group)
        
class ClavicleRig( Rig ):
    
    def _create_control(self):
        control, space = create_fk_control(self.locators[0], self._get_name('_ctrl'), 'sphere')
        set_color_to_side(control.get(), self.side)
        
        control.scale_shape(0.4,0.4,0.4)
        control.translate_shape(0,1.5,0)
        
        control.hide_rotate_attributes()
        
        self.control = control
        
        cmds.parent(space, self.main_group)
        cmds.parent(self.joints[0], self.main_group)
        
    def _create_ik(self):
        
        cmds.select(cl = True)
        end_joint = cmds.joint(n = self._get_name('_end_joint'))
        util.MatchSpace(self.locators[0], end_joint).translation()
        
        cmds.parent(end_joint, self.joints[0])
        
        handle = util.IkHandle('temp')
        handle.set_start_joint(self.joints[0])
        handle.set_end_joint(end_joint)
        handle.set_solver(handle.solver_sc)
        
        ik_name = self._get_name('ikHandle')
        handle.set_full_name(ik_name)
        handle.create()
        
        cmds.hide(handle.ik_handle)
        
        cmds.parent(handle.ik_handle, self.control.get())
        
    def create(self):
        self._create_control()
        
        self._create_ik()
        
        cmds.delete(self.locators[0])
        
class HandRig(Rig):
        
    def _create_hand_control(self):
        
        control, space = create_fk_control(self.locators[0], 
                                                '%s_fingers_ctrl' % self.side, 'square')
        
        util.MatchSpace(self.joints[0], space).rotation()
        if self.side == 'R':
            cmds.rotate(0,0,-180, space, r = True)
            
        control.rotate_shape(90,0,0)
        control.scale_shape(.5,.5,.5)
        
        util.hide_keyable_attributes(control.get())
        
        cmds.delete(self.locators[0])
    
        set_color_to_side(control.get(), self.side, sub = True)
        cmds.parent(space, self.main_group)
        
        cmds.parentConstraint(self.joints[0], self.main_group, mo = True)
        
        for locator in self.locators[1:]:
            util.MatchSpace(self.joints[0], locator).rotation()
            cmds.makeIdentity(locator, apply = True, r = True)
        
        self.hand_control = control
        
    def _setup_side_groups(self):
        cmds.parent(self.locators[3], self.locators[1])
        cmds.parent(self.locators[2], self.locators[3])
        
        cmds.parent(self.locators[1], self.main_group)
        
        multi = util.connect_multiply('{}.bend'.format(self.hand_control.get()), '{}.rotateZ'.format(self.locators[2]), 3)
        cmds.setAttr('%s.input2Y' % multi, 3)
        cmds.connectAttr('{}.side'.format(self.hand_control.get()), '{}.rotateX'.format(self.locators[1]))
        cmds.connectAttr('{}.side'.format(self.hand_control.get()), '{}.rotateX'.format(self.locators[3]))

        cmds.transformLimits( self.locators[3], rx = (-360, 0), erx = (0, 1) )
        cmds.transformLimits( self.locators[1], rx = (0, 360), erx = (1, 0) )
        
        
        
    def add_hand_attrs(self, hand_control):
        
        hand_control = self.hand_control.get()
        
        cmds.addAttr(hand_control, ln = 'bend', min = -60, max = 60, k = True)
        cmds.addAttr(hand_control, ln = 'side', min = -60, max = 60, k = True)
        """
        cmds.addAttr(hand_control, ln = 'thumbCurl', k = True)
        cmds.addAttr(hand_control, ln = 'thumbScrunch', k = True)
        cmds.addAttr(hand_control, ln = 'cup', k = True)
        cmds.addAttr(hand_control, ln = 'thumbSpread', k = True)
        cmds.addAttr(hand_control, ln = 'spread', k = True)
        cmds.addAttr(hand_control, ln = 'curl', k = True)
        cmds.addAttr(hand_control, ln = 'scrunch', k = True)
        cmds.addAttr(hand_control, ln = 'relax', k = True)
        cmds.addAttr(hand_control, ln = 'twist', k = True)
        cmds.addAttr(hand_control, ln = 'lean', k = True)
        cmds.addAttr(hand_control, ln = 'midSpread', k = True)
        """
        
        create_attr_separator(hand_control)
        cmds.addAttr(hand_control, ln = 'fkCtrlVis', at = 'bool', dv = 1, k = True)
        cmds.addAttr(hand_control, ln = 'fkIk', at = 'enum', enumName = 'fk:ik', k = True)
        
        
    def create(self):
        
        self.main_group = cmds.rename(self.main_group, self.main_group.replace('all', 'grp'))
        
        util.MatchSpace(self.joints[0], self.main_group).translation_rotation()
        
        self._create_hand_control()
        self.add_hand_attrs(self.hand_control)
        self._setup_side_groups()
class FingerRig(Rig):
    
    def __init__(self, description, side):
        super(FingerRig, self).__init__(description, side)
        
        self.color = 16
        
        cmds.delete(self.main_group)
        self.main_control = None
        self.spread_value = 25
    
    def _create_slider_control(self):
        if self.main_control:
            control = create_control(self._get_name('_ctrl'), 'square')
            util.MatchSpace(self.main_control, control.get()).translation_rotation()
            slider_space = create_space_group(control.get())
            cmds.parent(slider_space, self.main_control)
            
            control.scale_shape(.05, .05, .4)
            control.rotate_shape(90,0,0)
            #slider_control.translate_shape(0, .6, 0)
            
            if self.description == 'pinky':
                cmds.move(-.22, .52,0, slider_space, r = True, os = True)
                
            if self.description == 'ring':
                cmds.move(-.071, .60,0, slider_space, r = True, os = True)

            if self.description == 'middle':
                cmds.move(.071, .64,0, slider_space, r = True, os = True)
                
            if self.description == 'index':
                cmds.move(.22, .58,0, slider_space, r = True, os = True)
                
            if self.description == 'thumb':
                cmds.move(.5, .1,0, slider_space, r = True, os = True)
                cmds.rotate(0,0,-30, slider_space, r = True, os = True)
            
            set_color_to_side(control.get(), self.side, True)
    
            control.hide_keyable_attributes()
    
            cmds.addAttr(control.get(), ln = 'curl', k = True)
            cmds.addAttr(control.get(), ln = 'scrunch', k = True)
            cmds.addAttr(control.get(), ln = 'spread', k = True)
            cmds.addAttr(control.get(), ln = 'twist', k = True)
            cmds.addAttr(control.get(), ln = 'lean', k = True)
            cmds.addAttr(control.get(), ln = 'bend1', k = True)
            cmds.addAttr(control.get(), ln = 'bend2', k = True)
            cmds.addAttr(control.get(), ln = 'bend3', k = True)
            cmds.addAttr(control.get(), ln = 'bend4', k = True)
            cmds.addAttr(control.get(), ln = 'length', k = True, dv = 10, min = 0, max = 100)
            
            self.slider_control = control
    
    def _create_controls(self):
        
        joint_count = len(self.joints)
        last_control = None

        
        for inc in range(0, joint_count):
            
            joint = self.joints[inc]
            
            new_name = joint.replace('_joint', '_ctrl')
            
            dup = cmds.duplicate(joint, po = True, n = new_name)[0]
            
            if self.main_control:
                vis_attr = '%s.fkCtrlVis' % self.main_control
                if cmds.objExists(vis_attr):
                    cmds.connectAttr(vis_attr, '%s.visibility' % joint)
            
            cmds.parent(dup, joint)
            control = create_joint_control(dup, 'cube')
            control.scale_shape(.1, .1, .2)
            control.translate_shape(0, .2, 0)
            control.color(self.color)
            
            if last_control:
                cmds.parent(joint, last_control)
            last_control = dup
        
            spread_value = self.spread_value
            sub_spread_value = self.spread_value/5
        
            if inc == 0:
                
                util.quick_driven_key('%s.spread' % self.slider_control.get(), 
                                      '%s.rotateY' % control.get(), 
                                      [-10, 0, 10], 
                                      [sub_spread_value,0,(-1*sub_spread_value)], infinite = True)
            
            if inc == 1:
                util.connect_multiply('%s.length' % self.slider_control.get(), '%s.scaleX' % control.get())
                util.quick_driven_key('%s.scrunch' % self.slider_control.get(), 
                                      '%s.rotateZ' % joint , [-10,0,10], [-15,0,60], infinite = True)
                
                util.quick_driven_key('%s.spread' % self.slider_control.get(), 
                                      '%s.rotateY' % control.get(), 
                                      [-10, 0, 10], 
                                      [spread_value,0,(-1*spread_value)], infinite = True)
                
                util.quick_driven_key('%s.twist' % self.slider_control.get(), 
                                      '%s.rotateX' % joint , [-10,0,10], [30,0,-30], infinite = True)
                
            if inc == 2:
                util.quick_driven_key('%s.scrunch' % self.slider_control.get(), 
                                      '%s.rotateZ' % joint , [-10,0,10], [15,0,-106], infinite = True)               
            if inc == 3:
                util.quick_driven_key('%s.scrunch' % self.slider_control.get(), 
                                      '%s.rotateZ' % joint , [-10,0,10], [15,0,-60], infinite = True)
            if inc >=1:
                util.quick_driven_key('%s.curl' % self.slider_control.get(), 
                                      '%s.rotateZ' % joint , [-10,0,10], [9,0,-90], infinite = True)    
                util.quick_driven_key('%s.lean' % self.slider_control.get(), 
                                      '%s.rotateY' % joint , [-10,0,10], [-17,0,17], infinite = True)
            
            util.quick_driven_key('%s.bend%s' % (self.slider_control.get(), (inc+1)),
                                  '%s.rotateZ' % joint, [-40,0,40],[200,0,-200])
            
        
    def set_color(self, color):
        self.color = color
    
    def set_spread_value(self, spread_value):
        self.spread_value = spread_value
    
    def set_main_control(self, main_control):
        self.main_control = main_control
    
    def create(self):
        self._create_slider_control()
        self._create_controls()
        
class FootRig(Rig):
    
    def __init__(self, description, side):
        super(FootRig, self).__init__(description,side)
        
        self.attribute_control = None
    
    def _create_attributes(self, node):
        
        create_attr_separator(node, 'FOOT_ROLL')
        
        cmds.addAttr(node, ln = 'lean', min = -20, max = 20, k = True)
        cmds.addAttr(node, ln = 'side', min = -20, max = 20, k = True)
        cmds.addAttr(node, ln = 'roll', min = -60, max = 60, k = True)
        cmds.addAttr(node, ln = 'tipRoll', min = -60, max = 60, k = True)
        cmds.addAttr(node, ln = 'heelSpin', min = -60, max = 60, k = True)
        cmds.addAttr(node, ln = 'ballSpin', min = -60, max = 60, k = True)
        cmds.addAttr(node, ln = 'toeSpin', min = -60, max = 60, k = True)
        cmds.addAttr(node, ln = 'bank', min = -60, max = 60, k = True)
        cmds.addAttr(node, ln = 'toeTwist', min = -60, max = 60, k = True)
        cmds.addAttr(node, ln = 'toeBend', min = -60, max = 60, k = True)
        cmds.addAttr(node, ln = 'toeFlex', min = -60, max = 60, k = True)
        
    def _create_groups(self):
        
        self.heel_roll = cmds.group(em = True, n = self._get_name('_heelRoll'))
        self.tip_roll = cmds.group(em = True, n = self._get_name('_tipRoll'))
        self.heel_spin = cmds.group(em = True, n = self._get_name('_heelSpin'))
        self.ball_spin = cmds.group(em = True, n = self._get_name('_ballSpin'))
        self.toe_spin = cmds.group(em = True, n = self._get_name('_toeSpin'))
        self.bank_in = cmds.group(em = True, n = self._get_name('_bankIn'))
        self.bank_out = cmds.group(em = True, n = self._get_name('_bankOut'))
        self.toe_roll = cmds.group(em = True, n = self._get_name('_toeRoll'))
        
        self.toe_rotate = cmds.group(em = True, n = self._get_name('_toeRotate'))

        self.groups = [self.heel_roll,
                       self.tip_roll,
                       self.heel_spin,
                       self.ball_spin,
                       self.toe_spin,
                       self.bank_in,
                       self.bank_out,
                       self.toe_roll,
                       self.toe_rotate]
        
    def _position_groups(self):
        
        util.MatchSpace(self.locators[0], self.heel_roll).translation()   
        util.MatchSpace(self.locators[1], self.tip_roll).translation()
        
        position = cmds.xform(self.joints[0], q = True, ws = True, t = True)
        cmds.xform(self.heel_spin, ws = True, t = [position[0], 0, position[2]])
        
        position = cmds.xform(self.joints[1], q = True, ws = True, t = True)
        cmds.xform(self.ball_spin, ws = True, t = [position[0], 0, position[2]])
        
        position = cmds.xform(self.locators[1], q = True, ws = True, t = True)
        cmds.xform(self.toe_spin, ws = True, t = [position[0], 0, position[2]])
        
        util.MatchSpace(self.locators[2], self.bank_in).translation()
        util.MatchSpace(self.locators[3], self.bank_out).translation()
        util.MatchSpace(self.joints[1], self.toe_roll).translation()  
        util.MatchSpace(self.joints[1], self.toe_rotate).translation()
        
    def _parent_pivot_groups(self):
        
        last_group = None
        last_space = None

        cmds.parent(self.groups[0], self.attribute_control)

        for group in self.groups:
            
            space = create_space_group(group)
            if self.side == 'R':
                cmds.rotate(180,0,0, space, r = True)
                
            if last_group:
                cmds.parent(space, last_group)
                
            last_group = group
            last_space = space
        
        cmds.parent(last_space, self.bank_out)

    
    def _connect_groups(self):
        
        util.connect_multiply('%s.roll' % self.attribute_control, 
                              '%s.rotateX' % self.heel_roll, 3)
        
        cmds.transformLimits( self.heel_roll, rx = (-360, 0), erx = (0, 1) )
        
        util.connect_multiply('%s.roll' % self.attribute_control, 
                              '%s.rotateX' % self.toe_roll, 3)
        
        cmds.transformLimits( self.toe_roll, rx = (0, 360), erx = (1, 0) )
        
        util.connect_multiply('%s.tipRoll' % self.attribute_control, '%s.rotateX' % self.tip_roll, 3)
        
        util.connect_multiply('%s.heelSpin' % self.attribute_control, 
                              '%s.rotateY' % self.heel_spin, 3)
        
        util.connect_multiply('%s.ballSpin' % self.attribute_control, 
                              '%s.rotateY' % self.ball_spin, 3)
        
        util.connect_multiply('%s.toeSpin' % self.attribute_control, 
                              '%s.rotateY' % self.toe_spin, 3)

        util.connect_multiply('%s.bank' % self.attribute_control, 
                              '%s.rotateZ' % self.bank_in, 3)
        
        util.connect_multiply('%s.bank' % self.attribute_control, 
                              '%s.rotateZ' % self.bank_out, 3)
        
        cmds.transformLimits( self.bank_out, rz = (-360, 0), erz = (0, 1) )
        cmds.transformLimits( self.bank_in, rz = (0, 360), erz = (1, 0) )
        
        multiply = util.connect_multiply('%s.toeTwist' % self.attribute_control, '%s.rotateX' % self.toe_rotate, 3)
        cmds.setAttr('%s.input2Y' % multiply, 3)
        cmds.setAttr('%s.input2Z' % multiply, 3)
        
        cmds.connectAttr('%s.toeBend' % self.attribute_control, '%s.input1Y' % multiply)
        cmds.connectAttr('%s.outputY' % multiply, '%s.rotateY' % self.toe_rotate)
        
        cmds.connectAttr('%s.toeFlex' % self.attribute_control, '%s.input1Z' % multiply)
        cmds.connectAttr('%s.outputZ' % multiply, '%s.rotateZ' % self.toe_rotate)
    
    def _create_ik(self):
        
        handle = util.IkHandle('temp')
        handle.set_start_joint(self.joints[0])
        handle.set_end_joint(self.joints[1])
        handle.set_solver(handle.solver_sc)
        
        handle.set_full_name('%s_ankleFk_ikHandle' % self.side)
        handle.create()
        
        self.ankle_ik = handle.ik_handle
        
        cmds.parent(self.ankle_ik, self.toe_roll)
        
        handle = util.IkHandle('temp')
        handle.set_start_joint(self.joints[1])
        handle.set_end_joint(self.joints[2])
        handle.set_solver(handle.solver_sc)
        
        handle.set_full_name('%s_toeFk_ikHandle' % self.side)
        handle.create()
        
        self.toe_ik = handle.ik_handle
        
        cmds.parent(self.toe_ik, self.toe_rotate)
        
    def _create_toe_control(self):
        
        control = create_joint_control(self.joints[1], 'cube')
        set_color_to_side(control.get(), self.side)
        
    def set_attribute_control(self, control):
        self.attribute_control = control
        
        
    def create(self):
        
        self._create_toe_control()
        
        if not self.attribute_control:
            return
        
        self._create_attributes(self.attribute_control)
        
        self._create_groups()
        self._position_groups()
        self._parent_pivot_groups()
        
        self._create_ik()
        
        self._connect_groups()

class NeckRig(SpineRig):
    
    def _create_top_neck_locator(self):
        
        self.top_neck_control = cmds.spaceLocator(n = self._get_name('_ctrl2'))[0]
        util.MatchSpace(self.joints[-1], self.top_neck_control).translation()
        cmds.parent(self.top_neck_control, self.main_group)
        
    def _create_joint_section(self):
    
        cmds.parent(self.ctrl_joints[-1], self.ctrl_joints[0])
        
        
        cmds.joint(self.ctrl_joints[0], e = True, zso = True,
                   oj = 'xyz', sao = 'yup')
        
        cmds.makeIdentity(self.ctrl_joints[-1], apply = True, jo = True)
        
        cmds.parent(self.ctrl_joints[0], self.fk_controls[0].get())
        return [self.ctrl_joints[0], self.ctrl_joints[-1]]
    
    def _create_section_ik(self, joint1, joint2):
        
        handle = util.IkHandle('temp_ik')
        handle.set_solver(handle.solver_sc)
        handle.set_full_name('neck0_ctrl_ikHandle')
        handle.set_start_joint(joint1)
        handle.set_end_joint(joint2)
        handle.create()
    
        cmds.parent( handle.ik_handle, self.top_neck_control )
        
    def _create_ik_stretch(self, joint1, joint2):
        
        locator1 = cmds.spaceLocator(n = '%s_pos' % joint1)[0]
        locator2 = cmds.spaceLocator(n = '%s_pos' % joint2)[0]
        
        cmds.hide(locator1, locator2)
        
        util.MatchSpace(joint1, locator1).translation()
        util.MatchSpace(joint2, locator2).translation()
        
        cmds.parent(locator1, self.fk_controls[0].get())
        cmds.parent(locator2, self.top_neck_control)
        
        distance = cmds.createNode('distanceBetween', n = self._get_name('_distance'))
        
        cmds.connectAttr('%s.worldPosition[0]' % locator1, '%s.point1' % distance)
        cmds.connectAttr('%s.worldPosition[0]' % locator2, '%s.point2' % distance)
        
        distance_value = cmds.getAttr('%s.distance' % distance)
        
        multiply_distance = cmds.createNode('multiplyDivide', n = self._get_name('_ctrl_distance_normalize'))
        multiply_length = cmds.createNode('multiplyDivide', n = self._get_name('_ctrl_length_multi'))
        
        cmds.connectAttr('%s.distance' % distance, '%s.input1X' % multiply_distance)
        cmds.connectAttr('%s.outputX' % multiply_distance, '%s.input1X' % multiply_length)
        
        cmds.setAttr('%s.input2X' % multiply_length, distance_value)
        cmds.setAttr('%s.operation' % multiply_length, 2)
        
        cmds.connectAttr('%s.outputX' % multiply_length, '%s.scaleX' % joint1)
        
    def _connect_bend_spacers(self, joint):
        for spacer in self.bend_spacers:
            create_position_group(joint, spacer)
            
    def create(self):
        
        self._create_top_neck_locator()

        self._create_fk_controls()
        
        self._create_spline_ik()
        
        joints = self._attach_curve()
        
        ik_joint1, ik_joint2 = self._create_joint_section()
        
        self._skin_curve(joints)
        self._set_bendy_scale()
        
        cmds.parent(self.joints[0], self.main_group)
        
        self._create_section_ik(ik_joint1, ik_joint2)
        self._create_ik_stretch(ik_joint1, ik_joint2)
        
        self._connect_bend_spacers(ik_joint1)
        
#--- Face

#class JawRig(Rig):
#    pass

class TongueRig(Rig):
    
    def __init__(self, description, side):
        super(TongueRig, self).__init__(description, side)
        
        self.names = ['root', 'base', 'mid', 'tip', 'end']
    
    def _create_curve(self):
        
        self.curve = util.transforms_to_curve(self.joints, 3, self.description)
    
    def _create_clusters(self):
        
        cluster_curve = util.ClusterCurve(self.curve, self.description)
        cluster_curve.create()
        self.clusters = cluster_curve.clusters
    
    def _create_controls(self):
        
        main_group = cmds.group(em = True, n = 'Move_G')
        tongue_group = cmds.group(em = True, n = 'BG_%s_grp' % self.description)
        shift_group = cmds.group(em = True, n = 'BG_%s_jawSift_grp' % self.description)
        
        cmds.parent(shift_group, tongue_group)
        cmds.parent(tongue_group, main_group)
        
        for inc in range(0, len(self.names)):
            
            camel_name = '%s%s' % (self.description, self.names[inc].capitalize())
            
            shape_name = 'circle'
            
            if inc == 0 or inc == len(self.names)-1:
                shape_name = 'cube'
            
            control = create_control('BGCtrl_%sLoc' % camel_name, shape_name)
            
            space = create_space_group(control.get(), 'BG_%s_driven_grp' % camel_name)
            
            
            
            cmds.parent(space, shift_group)
            
    def create(self):
        
        self._create_curve()
        #self._create_clusters()
        self._create_controls()