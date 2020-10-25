import string

from vtool import util
from vtool import util_file

in_maya = util.is_in_maya()

#moved here for decorators
from vtool.maya_lib import core  
from vtool.maya_lib import curve

if in_maya:
    import maya.cmds as cmds

      
    from vtool.maya_lib import attr
    from vtool.maya_lib2 import space
    import vtool.maya_lib.space as space_old


curve_data = curve.CurveDataInfo()
curve_data.set_active_library('default_curves')

class Control(object):
    
    
    
    def __init__(self, name):

        self._use_joint = False

        self.name = ''
        self.curve_shape = ''
        self.tag = True
        self.shapes = []
        
        self._curve_shape = 'circle'
        
        self.name = name
        
        self.uuid = None
        
        
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
        
        if self._curve_shape:
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
        
        curve_data.set_shape_to_curve(self.name, self._curve_shape)
        
        if color:
            self.shapes = core.get_shapes(self.name)
            attr.set_color_rgb(self.shapes, *color)
    
    @classmethod
    def get_curve_shapes(cls):
        
        return curve_data.get_curve_names()
    
    @property
    def curve_shape(self):
        return self._curve_shape
        
    @curve_shape.setter
    def curve_shape(self, str_curve_shape):
        
        if not str_curve_shape:
            return
        self._curve_shape = str_curve_shape
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


        
    

class AttrType(object):
    
    BOOL = 1
    STRING = 2
    TRANSFORM = 3
    COLOR = 4
    
class Attr(object):
    
    def __init__(self):
        
        self._in_attributes = []
        self._in_attributes_dict = {}
        
        self._out_attributes = []
        self._out_attributes_dict = {}
        
        self._node_attributes = []
        self._node_attributes_dict = {}
        
        self._dependency = {}
        
    def add_in(self, name, value, data_type):
        
        self._in_attributes.append(name)
        self._in_attributes_dict[name] = [value,data_type]
    
    def add_out(self, name, value, data_type):
        
        self._out_attributes.append(name)
        self._out_attributes_dict[name] = [value,data_type]
      
    def add_to_node(self, name, value, data_type):
        
        self._node_attributes.append(name)
        self._node_attributes_dict[name] = [value, data_type]
        
    def add_update(self, source_name, target_name):
        
        if not source_name in self._dependency:
            self._dependency[source_name] = []
        
        if not target_name in self._dependency[source_name]:
            self._dependency[source_name].append(target_name)
    
    @property
    def inputs(self):
        return self._in_attributes
    
    @property
    def outputs(self):
        return self._out_attributes
    
    @property
    def node(self):
        return self._node_attributes
    
    def get_data_for_export(self):
        
        data = {}
        
        data['in'] = [self._in_attributes, self._in_attributes_dict]
        data['out'] = [self._out_attributes, self._out_attributes_dict]
        data['node'] = [self._node_attributes, self._node_attributes_dict]
        data['dependency'] = self._dependency
        
        return data
    
    def set_data_from_export(self, data_dict):
        
        self._node_attributes, self._node_attributes_dict = data_dict['node']
        self._in_attributes, self._in_attributes_dict = data_dict['in']
        self._out_attributes, self._out_attributes_dict = data_dict['out']
        self._dependency = data_dict['dependency']
        
class Rig(object):
    
    def __init__(self):
        
        self._attribute = Attr()
        self._set = None
        self.uuid = None
        
        #property values
        self._joints = []
        self._controls = []
        self._color = [1,0.5,0]
        self._sub_color = [.75,0.4,0]
        self._description = 'move'
        self._curve_shape = 'circle'
        self._parent = None
        self._side = None
        #self._curve_shape = self.__class__.curve_shape
        
        #internal variables
        self._blend_matrix_nodes = []
        self._mult_matrix_nodes = []
        self._nodes = []
        
        self._attribute.add_in('joints', self._joints, AttrType.TRANSFORM)
        self._attribute.add_in('parent', self._controls, AttrType.TRANSFORM)
        self._attribute.add_to_node('description', self._description, AttrType.STRING)
        self._attribute.add_in('curve_shape', self._curve_shape, AttrType.STRING)
        self._attribute.add_in('color', self._color, AttrType.COLOR)
        self._attribute.add_in('sub_color', self._color, AttrType.COLOR)
        
        self._attribute.add_out('controls', self.controls, AttrType.TRANSFORM)
        
        self._attribute.add_update('joints', 'controls')
        
        
        
        #properties
        """
        self.joints = None
        self.controls = None
        self.description = None
        self.side = None
        
        self.color = None
        self.sub_color = None
        self.curve_shape = 'square'
        """
        self.use_control_numbering = False
        
        
    def _create_rig_set(self):
        self._set = cmds.createNode('objectSet', n = 'rig_%s' % self._get_name())
        attr.create_vetala_type(self._set, 'Rig2')
        
        cmds.addAttr(self._set,ln='parent',at='message')
        attr.create_multi_message(self._set, 'child')
        attr.create_multi_message(self._set, 'joint')
        attr.create_multi_message(self._set, 'control')
        
        self.uuid = cmds.ls(self._set, uuid = True)[0]
    
    def _attach(self):
        
        if self._blend_matrix_nodes:
            space.blend_matrix_switch(self._blend_matrix_nodes, 'switch', attribute_node = self._joints[0])
    
    def _get_name(self, prefix = None, description = None, sub = False):
        
        name_list = [prefix,self._description, description, '1', self._side]
            
        filtered_name_list = []
        
        for name in name_list:
            if name:
                filtered_name_list.append(str(name))
        
        name = string.join(filtered_name_list, '_')
        
        return name
    
    def _get_control_name(self, description = None, sub = False):
        
        control_name_inst = util_file.ControlNameFromSettingsFile()
        
        if sub == False and len(self._joints) == 1:
            control_name_inst.set_number_in_control_name(self.use_control_numbering)
        
        if description:
            description = self._description + '_' + description
        else:
            description = self._description
        
        if sub == True:
            description = 'sub_%s' % description
        
        control_name = control_name_inst.get_name(description)#, self.side)
            
        return control_name
    
    def _create_control(self, description = None, sub = False):
        
        control_name = core.inc_name(  self._get_control_name(description, sub)  )
        
        control = Control( control_name )
        
        control.curve_shape = self._curve_shape
        
        attr.append_multi_message(self._set, 'control', str(control))
        self._controls.append(control)
        
        
        """
        side = self.side
        
        if not side:
            side = 'C'
        """
        #if not self._set_sub_control_color_only:
        #    control.color( attr.get_color_of_side( side , sub)  )
        #if self._set_sub_control_color_only:
        #    control.color( attr.get_color_of_side( side, True )  )
        
        if not sub:
            control.color = self._color
            
        #if self.sub_control_color >= 0 and sub:   
        #    control.color( self.sub_control_color )
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
    
    def _delete_things_in_list(self, list_value):
        
        if not list_value:
            del list_value[:]
            #list_value = []
            return
        
        for thing in list_value:
            
            if hasattr(thing, 'name'):
                thing = thing.name
            
            if thing and cmds.objExists(thing):
                cmds.delete(thing)
        
        del list_value[:]    
        #list_value = []
            
    def _delete_rig(self):
        
        if in_maya and self._set and cmds.objExists(self._set):
            
            attr.clear_multi(self._set, 'joint')
            attr.clear_multi(self._set, 'control')
            
            core.delete_set_contents(self._set)
            
        
        self._controls = []
        self._mult_matrix_nodes = []
        self._blend_matrix_nodes = []
        self._nodes = []
        
        
        
        """
        self._delete_things_in_list(self._mult_matrix_nodes)
        self._delete_things_in_list(self._blend_matrix_nodes)
        self._delete_things_in_list(self._nodes)
        self._delete_things_in_list(self._controls)
        """
    
    def _add_to_set(self, nodes):
        
        cmds.sets(nodes, add = self._set)
        
    def _create_rig(self):
        
        self._create_controls()
        self._attach()
    
    def _create(self):
        
        if not in_maya:
            return
        
        if not self._set or not cmds.objExists(self._set):
            self._create_rig_set()
            
        self._create_rig()
        
        found = []
        
        found += self._controls            
        found += self._nodes
        found += self._blend_matrix_nodes
        found += self._mult_matrix_nodes
        self._add_to_set(found)
        
        self._parent_controls()
    
    def _create_controls(self):
        pass
    
    def _parent_controls(self):
        
        if not self._controls:
                return
        
        top_control = self._controls[0]
        
        if self._parent:
            
            parent = util.convert_to_sequence(self._parent)
            self._parent = parent[-1]
            
            cmds.parent(top_control, self._parent)
            
        if not self._parent:
            try:
                cmds.parent(top_control, w = True)
            except:
                pass
    
    def _set_curve_shape(self, str_curve_shape):
        self._curve_shape = str_curve_shape
        
        if not self._controls:
            return
        
        for control in self._controls:
            control.curve_shape = self._curve_shape
            
    
    def _rotate_cvs_to_axis(self, control_inst, joint):
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
        
    def get_ins(self):
        return self._attribute._in_attributes
    
    def get_outs(self):
        return self._attribute._out_attributes  
    
    def get_in(self, name):
        return self._attribute._in_attributes_dict[name]
        
    def get_out(self, name):
        return self._attribute._out_attributes_dict[name]
    
    def get_node_attributes(self):
        return self._attribute._node_attributes
    
    def get_node_attribute(self, name):
        return self._attribute._node_attributes_dict[name]
    
    def get_attr_dependency(self):
        return self._attribute._dependency        
    
    def get_attr(self, attribute_name):
        return getattr(self, attribute_name)
    
    def set_attr(self, attribute_name, value):
        
        setattr(self, attribute_name, value)
    
    def get_data(self):
        
        for name in self.get_ins():
            value, data_type = self._attribute._in_attributes_dict[name]
            
            value = getattr(self, name)
            self._attribute._in_attributes_dict[name] = [value, data_type]
        
        for name in self.get_outs():
            value, data_type = self._attribute._out_attributes_dict[name]
            
            value = getattr(self, name)
            self._attribute._out_attributes_dict[name] = [value, data_type]
        
        return self._attribute.get_data_for_export()
    
    def set_data(self, data_dict):
        
        self._attribute.set_data_from_export(data_dict)
        
        for name in self.get_ins():
            
            value, _ = self.get_in(name)
            private_attribute = '_' + name
            
            if hasattr(self, private_attribute):
                setattr(self, private_attribute, value)
        
        for name in self.get_outs():
            
            value, _ = self.get_out(name)
            private_attribute = '_' + name
            
            if hasattr(self, private_attribute):
                setattr(self, private_attribute, value)
    
    @property
    def joints(self):
        return self._joints
    
    @joints.setter
    @core.undo_chunk
    def joints(self, joint_list):
        joint_list = util.convert_to_sequence(joint_list)
        
        self._joints = joint_list

        self._delete_rig()
        
        if self._joints:
            self._create()
            
            attr.fill_multi_message(self._set, 'joint', self._joints)
            
        if not self._joints:
            
            if not self._joints:
                util.warning('No joints set to rig')
    
    @property
    def parent(self):
        return self._parent
    
    @parent.setter
    def parent(self, parent):
        
        self._parent = parent
        self._parent_controls()
        
        if self._parent:
            cmds.connectAttr('%s.message' % self._parent, '%s.parent' % self._set)
        
    
    @property
    def controls(self):
        return self._controls
    
    @controls.setter
    def controls(self, control_list):
        control_list = util.convert_to_sequence(control_list)
        self._controls = control_list
        
    @property
    def curve_shape(self):
        return self._curve_shape
        
    @curve_shape.setter
    def curve_shape(self, str_curve_shape):
        
        if str_curve_shape:
            self._set_curve_shape(str_curve_shape)
        
    @property
    def color(self):
        return self._color
    
    @color.setter
    def color(self, color):
        self._color = color
        
        for control in self._controls:
            
            control.color = color

    @property
    def sub_color(self):
        return self._sub_color
    
    @sub_color.setter
    def sub_color(self, color):
        self._sub_color = color

    def delete(self):
        
        self.joints = []
        if in_maya:
            cmds.delete( self._set )
            
class Fk(Rig):
    
    def _set_curve_shape(self, str_curve_shape):
        if not str_curve_shape:
            str_curve_shape = 'circle'
        
        self._curve_shape = str_curve_shape
        
        if not self._controls:
            return
        
        for joint, control in zip(self._joints, self._controls):
            control.curve_shape = self._curve_shape
            self._rotate_cvs_to_axis(control, joint)
    
    def _create_controls(self):
        
        joints = cmds.ls(self._joints, l = True)
        joints = core.get_hierarchy_by_depth(joints)
        
        watch = util.StopWatch()
        watch.round = 2
        
        watch.start('build')
        
        last_joint = None
        joint_control = {}
        
        parenting = {}
        
        for joint in joints:
            
            control_inst = self._create_control()
            control = str(control_inst)
            
            joint_control[joint]= control
            
            self._rotate_cvs_to_axis(control_inst, joint)
            
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
        
        watch.end()
        
class Ik(Rig):      
    
    def _create_ik_chain(self):
        
        joints = cmds.ls(self._joints)
        
        dup_inst = space_old.DuplicateHierarchy(joints[0])
        dup_inst.only_these(joints)
        dup_inst.stop_at(joints[-1])
        self._ik_joints = dup_inst.create()
        
        self._add_to_set(self._ik_joints)
        
    def _create_ik(self):
        
        ik_result = cmds.ikHandle( n='ik', sj=self._ik_joints[0], ee=self._ik_joints[-1], solver = 'ikRPsolver' )
        self._ik_handle = ik_result[0]
        self._nodes += ik_result
        
    def _create_ik_control(self):
        
        joint = self._ik_joints[-1]
        
        control_inst = self._create_control()
        control = str(control_inst)
        
        axis = space_old.get_axis_letter_aimed_at_child(joint)
        if axis:
            if axis == 'X':
                control_inst.rotate_shape(0, 0, 90)
            
            if axis == 'Y':
                pass
                #control_inst.rotate_shape(0, 90, 0)
            
            if axis == 'Z':
                control_inst.rotate_shape(90, 0, 0)
        
        
        cmds.matchTransform(control, joint)
        space.zero_out(control)
        
        space.attach(control, self._ik_handle)
        
        
        
        #mult_matrix, blend_matrix = space.attach(control, joint)
        
        #self._mult_matrix_nodes.append(mult_matrix)
        #self._blend_matrix_nodes.append(blend_matrix)
        
        
    
    def _create_controls(self):
        
        self._create_ik_control()
        
        for joint, ik_joint in zip(self._joints, self._ik_joints):
            
            mult_matrix, blend_matrix = space.attach(ik_joint, joint)
        
            self._mult_matrix_nodes.append(mult_matrix)
            self._blend_matrix_nodes.append(blend_matrix)
     
    def _create_rig(self):
        
        self._create_ik_chain()
        self._create_ik()
        
        super(Ik, self)._create_rig()
        
        