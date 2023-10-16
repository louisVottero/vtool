from . import rigs

from vtool import util
from vtool import util_file

from vtool.maya_lib import core  
from vtool.maya_lib import curve

in_maya = util.in_maya

if in_maya:
    import maya.cmds as cmds
    
    from ..maya_lib import attr
    from ..maya_lib import space as space_old
    from ..maya_lib2 import space

curve_data = curve.CurveDataInfo()
curve_data.set_active_library('default_curves')

class Control(object):
    
    
    
    def __init__(self, name):

        self._use_joint = False

        self.name = ''
        self.shape = ''
        self.tag = True
        self.shapes = []
        
        self._shape = 'circle'
        
        self.name = name
        
        self.uuid = None
        
        if cmds.objExists(self.name):
            curve_type = cmds.getAttr('%s.curveType' % self.name)
            self.uuid = cmds.ls(self.name, uuid = True)[0]
            self._shape = curve_type
        
        if not cmds.objExists(self.name):
            self._create()

    def __repr__(self):
        return self.name
    
    #def __str__(self):
    #    return self.name

    def _get_components(self):
        
        if not self.shapes:
            self.shapes = core.get_shapes(str(self))
            
        return core.get_components_from_shapes(self.shapes)        

    def _create(self):
        
        self.name = cmds.group(em = True, n = self.name)
        
        self.uuid = cmds.ls(self.name, uuid = True)[0]
        
        if self._shape:
            self._create_curve()
        if self.tag:
            try:
                cmds.controller(self.name)
            except:
                pass
            
        
        
    def _create_curve(self):
        
        shapes = core.get_shapes(self.name)
        color = None
        if shapes:
            color = attr.get_color_rgb(shapes[0], as_float = True)
        
        curve_data.set_shape_to_curve(self.name, self._shape)
        
        if color:
            self.shapes = core.get_shapes(self.name)
            attr.set_color_rgb(self.shapes, *color)
            
        self.scale_shape(2, 2, 2)
    
    @classmethod
    def get_shapes(cls):
        
        return curve_data.get_curve_names()
    
    @property
    def shape(self):
        return self._shape
        
    @shape.setter
    def shape(self, str_shape):
        
        if not str_shape:
            return
        self._shape = str_shape
        self._create_curve()  
        
        
    @property
    def color(self):
        return self._color
    
    @color.setter
    def color(self, rgb):
        
        if not rgb:
            return
        
        self._color = rgb
        
        self.shapes = core.get_shapes(self.name)
        
        attr.set_color_rgb(self.shapes, rgb[0],rgb[1],rgb[2])

    @property
    def use_joint(self):
        return self._use_joint
    
    @use_joint.setter
    def use_joint(self, bool_value):
        self._use_joint = bool_value
        
        cmds.select(cl = True)
        joint = cmds.joint()
        
        match = space_old.MatchSpace(self.name, joint)
        match.translation_rotation()
        match.scale()
        
        shapes = core.get_shapes(self.name)
        
        for shape in shapes:
            cmds.parent(shape, joint, s = True, r = True)
        
        cmds.delete(self.name)
        self.name = cmds.rename(joint, self.name)
        
        self.shapes = core.get_shapes(self.name)
        
      
    def rotate_shape(self,x,y,z):
        """
        Rotate the shape curve cvs in object space
        
        Args:
            x (float)
            y (float)
            z (float)
        """
        components = self._get_components()
        
        if components:
            cmds.rotate(x,y,z, components, relative = True)  

    def scale_shape(self, x,y,z):
        components = self._get_components()
        
        if components:
            cmds.scale(x,y,z, components, relative = True)

class MayaUtilRig(rigs.PlatformUtilRig):
    
    def __init__(self):
        super(MayaUtilRig, self).__init__()
        
        self.set = None
        self._controls = []
        self._blend_matrix_nodes = []
        self._mult_matrix_nodes = []
        self._nodes = []
    
    def _parent_controls(self, parent):
        
        controls = self.rig.attr.get('controls')
        
        if not controls:
            return
        
        top_control = controls[0]
        
        if not cmds.objExists(top_control):
            return
        
        if parent:
            parent = util.convert_to_sequence(parent)
            parent = parent[-1]
            
            try:
                cmds.parent(top_control, parent)
            except:
                util.warning('Could not parent %s under %s' % (top_control, parent))
        
        else:
            try:
                cmds.parent(top_control, w = True)
            except:
                pass
    
    def _create_rig_set(self):
        
        if not self.set:
            self.set = cmds.createNode('objectSet', n = 'rig_%s' % self.rig._get_name())
            attr.create_vetala_type(self.set, 'Rig2')
            cmds.addAttr(ln = 'rigType', dt = 'string')
            cmds.addAttr(ln = 'ramen_uuid', dt = 'string')
            cmds.setAttr('%s.rigType' % self.set, str(self.rig.__class__.__name__), type = 'string', l = True)
            
            
            cmds.addAttr(self.set,ln='parent',at='message')
            attr.create_multi_message(self.set, 'child')
            attr.create_multi_message(self.set, 'joint')
            attr.create_multi_message(self.set, 'control')
            
            cmds.setAttr('%s.ramen_uuid' % self.set, self.rig.uuid, type = 'string')
    
        
    
    def _add_to_set(self, nodes):
        
        if not self.set:
            return
        cmds.sets(nodes, add = self.set)
        

        #if not self._set or not cmds.objExists(self._set):
        #    self._create_rig_set()
        
    
    def _attach(self):
        if self._blend_matrix_nodes:
            space.blend_matrix_switch(self._blend_matrix_nodes, 'switch', attribute_node = self.rig.joints[0])

    def _get_set_controls(self):
        
        controls = attr.get_multi_message(self.set, 'control')
        
        self._controls = controls
        self.rig.attr.set('controls', controls)
        
        return controls
        
    def _post_build(self):
        super(MayaUtilRig, self)._post_build()
        
        found = []
        found += self._controls            
        found += self._nodes
        found += self._blend_matrix_nodes
        found += self._mult_matrix_nodes
        
        self._add_to_set(found)

    
    @property
    def parent(self):
        return self.rig.attr.get('parent')
    
    @parent.setter
    def parent(self, parent):
        util.show('\t\tSetting parent: %s' % parent)
        self.rig.attr.set('parent', parent)
        
        self._parent_controls(parent)
    
    @property
    def color(self):
        return self.rig.attr.get('color')
    
    @color.setter
    def color(self, color):
        self.rig.attr.set('color', color )
        
        color = color[0]
        
        for control in self._controls:
            control.color = color

    @property
    def sub_color(self):
        return self.rig.attr.get('sub_color')
    
    @sub_color.setter
    def sub_color(self, color):
        self.rig.attr.set('sub_color', color )
        
        if in_maya:
            pass
            #for control in self._sub_controls:
            #    control.color = color
    
    @property
    def shape(self):
        return self.rig.attr.get('shape')
    
    @shape.setter
    def shape(self, str_shape):
        
        if not str_shape:
            str_shape = 'circle'
        
        self.rig.attr.set('shape', str_shape)
        
        if not self._controls:
            return
        
        if not self.rig.joints:
            return
        
        for joint, control in zip(self.rig.joints, self._controls):
            control.shape = self.rig.shape
            self.rotate_cvs_to_axis(control, joint)
            

    def load(self):
        super(MayaUtilRig, self).load()
        
        self.set = None
        sets = cmds.ls(type = 'objectSet')
        
        for set_name in sets:
            if not cmds.objExists('%s.ramen_uuid' % set_name):
                continue
            
            ramen_uuid = cmds.getAttr('%s.ramen_uuid' % set_name)
            
            if ramen_uuid == self.rig.uuid:
                self.set = set_name
                self._get_set_controls()
                break

    def build(self):
        super(MayaUtilRig, self).build()
        
        self._create_rig_set()
        
        joints = self.rig.attr.get('joints')
        if joints:
            attr.fill_multi_message(self.set, 'joint', joints)
    
    def unbuild(self):
        super(MayaUtilRig, self).unbuild()
        
        if self.set and cmds.objExists(self.set):
            
            attr.clear_multi(self.set, 'joint')
            attr.clear_multi(self.set, 'control')
            
            result = core.remove_non_existent(self._mult_matrix_nodes)
            if result:
                cmds.delete(result)
            
            result = core.remove_non_existent(self._blend_matrix_nodes)
            if result:
                cmds.delete(result)    
            
            children = core.get_set_children(self.set)
            
            found = []
            if children:
                for child in children:
                    if not 'dagNode' in cmds.nodeType(child, inherited = True):
                        found.append(child)
            if found:
                cmds.delete(found)
            
            core.delete_set_contents(self.set)
            
        self._controls = []
        self._mult_matrix_nodes = []
        self._blend_matrix_nodes = []
        self._nodes = []
    
    def delete(self):
        super(MayaUtilRig, self).delete()
        
        if not self.set:
            return
        
        self.unbuild()
        if self.set:
            cmds.delete(self.set)
        self.set = None

    def get_control_name(self, description = None, sub = False):
        
        control_name_inst = util_file.ControlNameFromSettingsFile()
        
        #if sub == False and len(self.rig.joints) == 1:
        
        control_name_inst.set_number_in_control_name(not self.rig.attr.get('restrain_numbering'))
        
        if description:
            description = self.rig.attr.get('description') + '_' + description
        else:
            description = self.rig.attr.get('description')
        
        if sub == True:
            description = 'sub_%s' % description
        
        control_name = control_name_inst.get_name(description, self.rig.attr.get('side'))
            
        return control_name

    def create_control(self, description = None, sub = False):
        
        control_name = core.inc_name(  self.get_control_name(description, sub)  )
        control_name = control_name.replace('__', '_')
        
        control = Control( control_name )
        
        control.shape = self.rig.shape
        
        attr.append_multi_message(self.set, 'control', str(control))
        self._controls.append(control)
                
        if not sub:
            control.color = self.rig.color[0]
        
        
        
        """    
        control.hide_visibility_attribute()
        
        if self.control_shape and not self.curve_type:
            
            control.set_curve_type(self.control_shape)
            
            if sub:
                if self.sub_control_shape:
                    control.set_curve_type(self.sub_control_shape)
            
        
        if not sub:
            
            control.scale_shape(self.control_size, 
                                self.control_size, 
                                self.control_size)
            
        if sub:
            
            size = self.control_size * self.sub_control_size
            
            control.scale_shape(size, 
                                size, 
                                size)
        
        if not sub:
            self.controls.append(control.get())
        
        
        
        if sub:
            self.sub_controls.append(control.get())
            
            self._sub_controls_with_buffer[-1] = control.get()
        else:
            self._sub_controls_with_buffer.append(None)
            
        if self.control_offset_axis:
            
            if self.control_offset_axis == 'x':
                control.rotate_shape(90, 0, 0)
                
            if self.control_offset_axis == 'y':
                control.rotate_shape(0, 90, 0)
                
            if self.control_offset_axis == 'z':
                control.rotate_shape(0, 0, 90)
                
            if self.control_offset_axis == '-x':
                control.rotate_shape(-90, 0, 0)
                
            if self.control_offset_axis == '-y':
                control.rotate_shape(0, -90, 0)
                
            if self.control_offset_axis == '-z':
                control.rotate_shape(0, 0, -90)
                
        self.control_dict[control.get()] = {}
        """
        return control

    def rotate_cvs_to_axis(self, control_inst, joint):
        axis = space_old.get_axis_letter_aimed_at_child(joint)
        if axis:
            if axis == 'X':
                control_inst.rotate_shape(0, 0, -90)
            
            if axis == 'Y':
                pass
                #control_inst.rotate_shape(0, 90, 0)
            
            if axis == 'Z':
                control_inst.rotate_shape(90, 0, 0)
            
            if axis == '-X':
                control_inst.rotate_shape(0, 0, 90)
                
            if axis == '-Y':
                pass
                #control_inst.rotate_shape(0, 180, 0)
                
            if axis == '-Z':
                control_inst.rotate_shape(-90, 0, 0)



class MayaFkRig(MayaUtilRig):

    def _create_maya_controls(self):
        joints = cmds.ls(self.rig.joints, l = True)
        joints = core.get_hierarchy_by_depth(joints)
        
        watch = util.StopWatch()
        watch.round = 2
        
        watch.start('build')
        
        last_joint = None
        joint_control = {}
        
        parenting = {}
        
        rotate_cvs = True
        
        if len(joints) == 1:
            rotate_cvs = False
        
        use_joint_name = self.rig.attr.get('use_joint_name')
        joint_token = self.rig.attr.get('joint_token')
        
        for joint in joints:
            
            description = None
            if use_joint_name:
                joint_nice_name = core.get_basename(joint)
                if joint_token:
                    description = joint_nice_name
                    description = description.replace(joint_token, '')
                    description = util.replace_last_number(description, '')
                    description = description.lstrip('_')
                    description = description.rstrip('_')
                    
                else:
                    description = joint_nice_name
            
            control_inst = self.create_control(description = description)
            
            
            control = str(control_inst)
            
            sub_control_count = self.rig.attr.get('sub_count')
            
            joint_control[joint]= control
            
            if rotate_cvs:
                self.rotate_cvs_to_axis(control_inst, joint)
            
            last_control = None
            parent = cmds.listRelatives(joint, p = True, f = True)
            if parent:
                parent = parent[0]
                if parent in joint_control:
                    last_control = joint_control[parent]
            if not parent and last_joint:
                last_control = joint_control[last_joint]
            
            if last_control:
                
                if not last_control in parenting:
                    parenting[last_control] = []
                
                parenting[last_control].append(control)
                
            cmds.matchTransform(control, joint)
            
            nice_joint = core.get_basename(joint)
            mult_matrix, blend_matrix = space.attach(control, nice_joint)
            
            self._mult_matrix_nodes.append(mult_matrix)
            self._blend_matrix_nodes.append(blend_matrix)
            
            last_joint = joint    
        
        for parent in parenting:
            children = parenting[parent]
            
            cmds.parent(children, parent)
        
        for control in self._controls:    
            space.zero_out(control)
        
        self.rig.attr.set('controls', self._controls)
        
        watch.end()
    
    def build(self):
        super(MayaFkRig, self).build()
        
        self._parent_controls([])
        
        self._create_maya_controls()
        self._attach()
        
        self._parent_controls(self.parent)
        
        self.rig.attr.set('controls', self._controls)
        
        return self._controls
    
    
class MayaIkRig(MayaUtilRig):

    def _create_maya_controls(self):
        joints = cmds.ls(self.rig.joints, l = True)
        joints = core.get_hierarchy_by_depth(joints)
        
        watch = util.StopWatch()
        watch.round = 2
        
        watch.start('build')
        
        last_joint = None
        joint_control = {}
        
        parenting = {}
        
        rotate_cvs = True
        
        if len(joints) == 1:
            rotate_cvs = False
        
        use_joint_name = self.rig.attr.get('use_joint_name')
        joint_token = self.rig.attr.get('joint_token')
        
        for joint in joints:
            
            description = None
            if use_joint_name:
                joint_nice_name = core.get_basename(joint)
                if joint_token:
                    description = joint_nice_name
                    description = description.replace(joint_token, '')
                    description = util.replace_last_number(description, '')
                    description = description.lstrip('_')
                    description = description.rstrip('_')
                    
                else:
                    description = joint_nice_name
            
            control_inst = self.create_control(description = description)
            
            
            control = str(control_inst)
            
            sub_control_count = self.rig.attr.get('sub_count')
            
            joint_control[joint]= control
            
            if rotate_cvs:
                self.rotate_cvs_to_axis(control_inst, joint)
            
            last_control = None
            parent = cmds.listRelatives(joint, p = True, f = True)
            if parent:
                parent = parent[0]
                if parent in joint_control:
                    last_control = joint_control[parent]
            if not parent and last_joint:
                last_control = joint_control[last_joint]
            
            if last_control:
                
                if not last_control in parenting:
                    parenting[last_control] = []
                
                parenting[last_control].append(control)
                
            cmds.matchTransform(control, joint)
            
            nice_joint = core.get_basename(joint)
            mult_matrix, blend_matrix = space.attach(control, nice_joint)
            
            self._mult_matrix_nodes.append(mult_matrix)
            self._blend_matrix_nodes.append(blend_matrix)
            
            last_joint = joint    
        
        for parent in parenting:
            children = parenting[parent]
            
            cmds.parent(children, parent)
        
        for control in self._controls:    
            space.zero_out(control)
        
        self.rig.attr.set('controls', self._controls)
        
        watch.end()
    
    def build(self):
        super(MayaFkRig, self).build()
        
        self._parent_controls([])
        
        self._create_maya_controls()
        self._attach()
        
        self._parent_controls(self.parent)
        
        self.rig.attr.set('controls', self._controls)
        
        return self._controls