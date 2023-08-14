# Copyright (C) 2022 Louis Vottero louis.vot@gmail.com    All rights reserved.

from .. import logger
log = logger.get_logger(__name__)

import string

#moved here for decorators
from vtool.maya_lib import core  
from vtool.maya_lib import curve

from vtool import util

in_maya = util.in_maya
in_unreal = util.in_unreal

if in_maya:
    import maya.cmds as cmds

      
    from ..maya_lib import attr
    from ..maya_lib import space as space_old
    from ..maya_lib2 import space
    

if in_unreal:
    from .. import unreal_lib
    import unreal

from vtool import util
from vtool import util_file

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
    
    EVALUATION = 0
    ANY = 1
    BOOL = 2
    STRING = 3
    TRANSFORM = 4
    COLOR = 5

class RigType(object):
    FK = 0
    IK = 1

"""
class Attribute(object):

    name = None
    value = None
    data_type = None

    def __init__(self):
        
        self.name = None
        self.value = None
        self.data_type = None
"""    
class Attributes(object):
    
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
    
    def exists(self, name):
        if name in self._in_attributes_dict:
            return True
        if name in self._out_attributes_dict:
            return True
        if name in self._node_attributes_dict:
            return True
        
        return False
        
    def set(self, name, value):
        
        if name in self._in_attributes_dict:
            self._in_attributes_dict[name][0] = value
        if name in self._out_attributes_dict:
            self._out_attributes_dict[name][0] = value
        if name in self._node_attributes_dict:
            self._node_attributes_dict[name][0] = value
    
    def get(self, name):
        if name in self._in_attributes_dict:
            return self._in_attributes_dict[name][0]
        if name in self._out_attributes_dict:
            return self._out_attributes_dict[name][0]
        if name in self._node_attributes_dict:
            return self._node_attributes_dict[name][0]
        
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

class Base(object):
    def __init__(self):
        self._init_attribute()
        
        
        
        self._init_values()
        
        self._init_variables()
        
        self.dirty = True

    def _init_attribute(self):
        self.attr = Attributes()

    def _init_values(self):
        pass
    
    def _init_variables(self):
        pass

    def get_ins(self):
        return self.attr.inputs
    
    def get_outs(self):
        return self.attr.outputs  
    
    def get_in(self, name):
        return self.attr._in_attributes_dict[name]
        
    def get_out(self, name):
        return self.attr._out_attributes_dict[name]
    
    def get_node_attributes(self):
        return self.attr._node_attributes
    
    def get_node_attribute(self, name):
        return self.attr._node_attributes_dict[name]
    
    def get_attr_dependency(self):
        return self.attr._dependency        
    
    def get_attr(self, attribute_name):
        return getattr(self, attribute_name)
    
    def set_attr(self, attribute_name, value):
        
        setattr(self, attribute_name, value)
    
    def get_data(self):
        
        for name in self.get_ins():
            value, data_type = self.attr._in_attributes_dict[name]
            
            value = getattr(self, name)
            self.attr._in_attributes_dict[name] = [value, data_type]
        
        for name in self.get_outs():
            value, data_type = self.attr._out_attributes_dict[name]
            
            value = getattr(self, name)
            self.attr._out_attributes_dict[name] = [value, data_type]
        
        return self.attr.get_data_for_export()
    
    def set_data(self, data_dict):
        
        self.attr.set_data_from_export(data_dict)
        
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
    def uuid(self):
        return self._uuid
    
    @uuid.setter
    def uuid(self, uuid):
        self._uuid = uuid
        
class Rig(Base):
    
    rig_type = -1
    description = 'rig'
    
    def __init__(self):
        super(Rig, self).__init__()
        
        self._description = self.__class__.description
        
        
        #internal variables
        
    def _maya_rig(self):
        return MayaUtilRig()
    
    def _unreal_rig(self):
        return UnrealUtilRig()
        
    def _init_values(self):
        #property values
        self._joints = []
        self._controls = []
        self._color = [1,0.5,0]
        self._sub_color = [.75,0.4,0]
        self._description = 'move'
        self._curve_shape = 'circle'
        self._parent = None
        self._side = None
        
        self.use_control_numbering = False
        #self._curve_shape = self.__class__.curve_shape
        
    def _init_variables(self):
        
        self.attr.add_in('Eval', [], AttrType.EVALUATION)
        self.attr.add_in('joints', self._joints, AttrType.TRANSFORM)
        self.attr.add_in('parent', self._controls, AttrType.TRANSFORM)
        self.attr.add_to_node('description', self._description, AttrType.STRING)
        self.attr.add_in('curve_shape', self._curve_shape, AttrType.STRING)
        self.attr.add_in('color', self._color, AttrType.COLOR)
        self.attr.add_in('sub_color', self._color, AttrType.COLOR)
        
        self.attr.add_out('controls', self.controls, AttrType.TRANSFORM)
        self.attr.add_out('Eval', [], AttrType.EVALUATION)
        
        self.attr.add_update('joints', 'controls')
        self.attr.add_update('description', 'controls')
        
    
    

    
    def _get_name(self, prefix = None, description = None, sub = False):
        
        name_list = [prefix,self._description, description, '1', self._side]
            
        filtered_name_list = []
        
        for name in name_list:
            if name:
                filtered_name_list.append(str(name))
        
        name = '_'.join(filtered_name_list)
        
        return name
    
    
    

    
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
            
    def _unbuild_rig(self):
        
        self.rig_util.unbuild()
            
        
        

    def _create_rig_maya(self):
        
        self._attach()
        

        
    def _create_rig_unreal(self):
        log.info('Running rig unreal')
        
        
    def _initialize_rig(self):
        util.show('Loading Rig %s' % self.__class__.__name__)
        if in_maya:
            self.rig_util = self._maya_rig()
            
            #self._create_rig_maya()
        
        if in_unreal:
            self.rig_util = self._unreal_rig()
            
            #self._create_rig_unreal()
            
        self.rig_util.set_rig_class(self)
        
        self.rig_util.load()
        #self.rig_util.create()
    
    def _create_rig(self):
        
        self.rig_util.build()
        
        if in_maya:
            self._create_rig_maya()
            
        if in_unreal:
            self._create_rig_unreal()
    
    def _create(self):
        util.show('Creating Rig Init %s' % self.__class__.__name__)

        self._create_rig()

        self._parent_controls()
    
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
            
    

    @property
    def joints(self):
        self._joints = self.attr.get('joints')
        return self._joints
    
    @joints.setter
    @core.undo_chunk
    def joints(self, joint_list):
        
        if joint_list:
            joint_list = util.convert_to_sequence(joint_list)
            self.attr.set('joints', joint_list)
            self._joints = joint_list
            self.create()
            
        if not joint_list:
            self._unbuild_rig()
            self.attr.set('joints', [])
            self._joints = []
            
            util.warning('No joints set to rig')
    
    @property
    def parent(self):
        return self._parent
    
    @parent.setter
    def parent(self, parent):
        
        self._parent = parent
        self._parent_controls()
        
        if self._parent:
            cmds.connectAttr('%s.message' % self._parent, '%s.parent' % self.rig_util.set)
        
    
    @property
    def description(self):
        return self.attr.get('description')
    
    @description.setter
    def description(self, value):
        self.attr.set('description', value)
    
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

    def load(self):
        util.show('Load Rig %s' % self.__class__.__name__)
        self._initialize_rig()

    def create(self):
        util.show('Creating Rig %s' % self.__class__.__name__)
        
        self.rig_util.load()
        
        self._unbuild_rig()
        
        self._create()
        
        
        if in_maya:
            if self.joints:
                attr.fill_multi_message(self.rig_util.set, 'joint', self._joints)

    def delete(self):
        util.show('Deleting Rig %s' % self.__class__.__name__)
        self.rig_util.delete()

class Fk(Rig):
    
    rig_type = RigType.FK
    description = 'fk'
    
    def _maya_rig(self):
        return MayaFkRig()
    
    def _unreal_rig(self):
        return UnrealFkRig()
    
    def _init_values(self):
        super(Fk, self)._init_values()
        self._description = self.__class__.description
    
    def _set_curve_shape(self, str_curve_shape):
        if not str_curve_shape:
            str_curve_shape = 'circle'
        
        self._curve_shape = str_curve_shape
        
        if not self._controls:
            return
        
        for joint, control in zip(self._joints, self._controls):
            control.curve_shape = self._curve_shape
            self._rotate_cvs_to_axis(control, joint)
    
    
class Ik(Rig):      
    
    rig_type = RigType.IK
    description = 'iks'
    
    def _init_values(self):
        super(Ik, self)._init_values()
        self._description = self.__class__.description
    
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

class PlatformUtilRig(object):

    def __init__(self):
        
        self.rig = None

    def __getattribute__(self, item):

        custom_functions = ['build']
        
        if item in custom_functions:
            
            if item == 'build':
                result = self._pre_build()
                if result == False:
                    return lambda *args: None
            
            result = object.__getattribute__(self, item)
            
            result_values = result()
            
            def results():
                return result_values
        
            if item == 'build':    
                self._post_build()
                
            return results
        
        else:
            
            return object.__getattribute__(self,item)

    def _pre_build(self):
        util.show('Pre Build Rig: %s' % self.__class__.__name__)
        return

    def _post_build(self):
        util.show('Post Build Rig: %s' % self.__class__.__name__)
        return

    def set_rig_class(self, rig_class_instance):
        self.rig = rig_class_instance
    
    def load(self):
        pass
    
    def build(self):
        util.show('Build Rig: %s' % self.__class__.__name__)
        pass
    
    def unbuild(self):
        pass
    
    def delete(self):
        pass

#--- Maya
class MayaUtilRig(PlatformUtilRig):
    
    def __init__(self):
        super(MayaUtilRig, self).__init__()
        
        self.set = None
        
        self._blend_matrix_nodes = []
        self._mult_matrix_nodes = []
        self._nodes = []
    
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
                break

    def _post_build(self):
        super(MayaUtilRig, self)._post_build()
        
        found = []
        found += self._controls            
        found += self._nodes
        found += self._blend_matrix_nodes
        found += self._mult_matrix_nodes
        
        self._add_to_set(found)

    def build(self):
        super(MayaUtilRig, self).build()
        
        self._create_rig_set()
    

    
    def unbuild(self):
        super(MayaUtilRig, self).unbuild()
        
        if self.set and cmds.objExists(self.set):
            attr.clear_multi(self.set, 'joint')
            attr.clear_multi(self.set, 'control')
            
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
        cmds.delete(self.set)
        self.set = None

    def get_control_name(self, description = None, sub = False):
        
        control_name_inst = util_file.ControlNameFromSettingsFile()
        
        if sub == False and len(self.rig.joints) == 1:
            control_name_inst.set_number_in_control_name(self.rig.use_control_numbering)
        
        if description:
            description = self.rig.attr.get('description') + '_' + description
        else:
            description = self.rig.attr.get('description')
        
        if sub == True:
            description = 'sub_%s' % description
        
        control_name = control_name_inst.get_name(description)#, self.side)
            
        return control_name

    def create_control(self, description = None, sub = False):
        
        control_name = core.inc_name(  self.get_control_name(description, sub)  )
        
        control = Control( control_name )
        
        control.curve_shape = self.rig._curve_shape
        
        attr.append_multi_message(self.set, 'control', str(control))
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
            control.color = self.rig._color
            
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
        
        for joint in joints:
            
            control_inst = self.create_control()
            control = str(control_inst)
            
            joint_control[joint]= control
            
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
        
        watch.end()
    
    def build(self):
        super(MayaFkRig, self).build()
        
        self._create_maya_controls()
        self._attach()
        
        
#--- Unreal
class UnrealUtilRig(PlatformUtilRig):
    
    def __init__(self):
        super(UnrealUtilRig, self).__init__()
        
        self.construct_graph = None
        self.construct_graph_name = None
        self.function_node = None
        
    
    def _init_graph(self):
        if not self.graph:
            return 
        
        model_control = None
        model_name = None
        
        if not self.construct_graph:
            construct_model = self.graph.add_model('Construction Event Graph')
            model_name = construct_model.get_node_path()
            model_name = model_name.replace(':', '')
        
            model_control = self.graph.get_controller_by_name(model_name)
            model_control.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_PrepareForExecution', 'Execute', unreal.Vector2D(0, 0), 'PrepareForExecution')
        
        if not model_control:
            return
        
        self.construct_graph = model_control
        self.construct_graph_name = model_name
    
    def _init_rig_function(self):
        
        if not self.graph:
            return
        
        rig_name = 'rig_%s' % self.rig.description
        
        found = self.controller.get_graph().find_function(rig_name)
        
        if found:
             
            self.function = found
            function_controller = self.graph.get_controller_by_name(self.function.get_node_path())
            self.function_controller = function_controller
            
        else:
            self.function = self.controller.add_function_to_library('rig_%s' % self.rig.description, True, unreal.Vector2D(0,0))
            
            function_controller = self.graph.get_controller_by_name(self.function.get_node_path())
            self.function_controller = function_controller
        
            self._initialize_inputs()
            self._build_function_graph()
        
    def _initialize_inputs(self):
        
        self.function_controller.add_exposed_pin('uuid', unreal.RigVMPinDirection.INPUT, 'FString', 'None', '')
        self.function_controller.add_exposed_pin('mode', unreal.RigVMPinDirection.INPUT, 'FString', 'None', '')
        
        inputs = self.rig.attr.inputs
        for name in inputs:
            value, attr_type = self.rig.attr._in_attributes_dict[name]
            
            if attr_type == AttrType.COLOR:
                self.function_controller.add_exposed_pin(name, unreal.RigVMPinDirection.INPUT, 'TArray<FLinearColor>', '/Script/CoreUObject.LinearColor', '')
            if attr_type == AttrType.STRING:
                self.function_controller.add_exposed_pin(name, unreal.RigVMPinDirection.INPUT, 'FString', 'None', value)
            if attr_type == AttrType.TRANSFORM:
                if name == 'parent':
                    self.function_controller.add_exposed_pin(name, unreal.RigVMPinDirection.INPUT, 'FRigElementKey', '/Script/ControlRig.RigElementKey', '')
                else:
                    self.function_controller.add_exposed_pin(name, unreal.RigVMPinDirection.INPUT, 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', '')
        
        node_attrs = self.rig.attr.node
        for name in node_attrs:
            value, attr_type = self.rig.attr._node_attributes_dict[name]
            
            if attr_type == AttrType.COLOR:
                self.function_controller.add_exposed_pin(name, unreal.RigVMPinDirection.INPUT, 'TArray<FLinearColor>', '/Script/CoreUObject.LinearColor', '')
            if attr_type == AttrType.STRING:
                self.function_controller.add_exposed_pin(name, unreal.RigVMPinDirection.INPUT, 'FString', 'None', value)
            if attr_type == AttrType.TRANSFORM:
                self.function_controller.add_exposed_pin(name, unreal.RigVMPinDirection.INPUT, 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', '')
                    
    def _build_function_graph(self):
        return
        
    def load(self):
        super(UnrealUtilRig, self).load()
        self.graph = unreal_lib.util.current_control_rig
        
        if not self.graph:
            return 
        
        unreal.AssetEditorSubsystem().open_editor_for_assets([self.graph])
        
        self.library = self.graph.get_local_function_library()
        self.controller = self.graph.get_controller(self.library)
        
        self.forward_graph = self.graph.get_controller_by_name('RigVMModel')
        
        models = self.graph.get_all_models()
        
        construct_model = None
        model_control = None
        found = None
        
        for model in models:
            if model.get_node_path().find('Construction Event Graph') > -1:
                found = model
        
        if found: 
            construct_model = found
            model_name = construct_model.get_node_path()
            model_name = model_name.replace(':', '')
            model_control = self.graph.get_controller_by_name(model_name)
            
            self.construct_graph = model_control
            self.construct_graph_name = model_name
        
        if not self.construct_graph:
            return
        
        nodes = self.construct_graph.get_graph().get_nodes()
        
        for node in nodes:
            
            pin = self.construct_graph.get_graph().find_pin('%s.uuid' % node.get_node_path())
            if pin:
                node_uuid = pin.get_default_value()
                if node_uuid == self.rig.uuid:
                    self.function_node = node
                    break            

    def build(self):
        super(UnrealUtilRig, self).build()
        if not self.graph:
            util.warning('No control rig for Unreal rig')
            return
        #function_node = self.construct_graph.get_graph().find_node(self.function.get_node_path())
        
        self._init_graph()
        self._init_rig_function()
        
        if not self.function_node:
            
            function_node = self.construct_graph.add_function_reference_node(self.function, unreal.Vector2D(100, 100), self.function.get_node_path())
            self.function_node = function_node
            self.construct_graph.add_link('PrepareForExecution.ExecuteContext', '%s.ExecuteContext' % (function_node.get_node_path()))
            self.construct_graph.set_pin_default_value('%s.uuid' % function_node.get_node_path(), self.rig.uuid, False)
        
        if not self.function_node:
            util.warning('No function for Unreal rig')
            return
        
        self.construct_graph.set_pin_default_value('%s.description' % self.function_node.get_node_path(), self.rig.attr.get('description'), False)
        self.construct_graph.set_pin_default_value('%s.joints' % self.function_node.get_node_path(), '()', True)
        
        inc = 0
        for joint in self.rig.joints:
            self.construct_graph.insert_array_pin('%s.joints' % self.function_node.get_node_path(), -1, '')
            self.construct_graph.set_pin_default_value('%s.joints.%s.Type' % (self.function_node.get_node_path(), inc), 'Bone', False)
            self.construct_graph.set_pin_default_value('%s.joints.%s.Name' % (self.function_node.get_node_path(), inc), joint, False)
            inc+=1
            
    def unbuild(self):
        super(UnrealUtilRig, self).unbuild()
        
    def delete(self):
        super(UnrealUtilRig, self).delete()
        if not self.graph:
            return
        
        super(UnrealUtilRig, self).unrig()

class UnrealFkRig(UnrealUtilRig):
    def _build_function_graph(self):
        super(UnrealFkRig, self)._build_function_graph()
        if not self.graph:
            return
        
        self._build_construct_graph()
        self._build_forward_graph()
        self._build_backward_graph()
        
    def _build_construct_graph(self):
        
        for_each = self.function_controller.add_template_node('DISPATCH_RigVMDispatch_ArrayIterator(in Array,out Element,out Index,out Count,out Ratio)', unreal.Vector2D(300, 150), 'DISPATCH_RigVMDispatch_ArrayIterator')
        
        self.function_controller.add_link('Entry.ExecuteContext', '%s.ExecuteContext' % (for_each.get_node_path()))
        self.function_controller.add_link('%s.Completed' % (for_each.get_node_path()), 'Return.ExecuteContext')        
        self.function_controller.add_link('Entry.joints', '%s.Array' % (for_each.get_node_path()))
        
        get_transform = self.function_controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetTransform', 'Execute', unreal.Vector2D(640, 240), 'GetTransform_1')
        self.function_controller.add_link('%s.Element' % for_each.get_node_path(), '%s.Item' % get_transform.get_node_path())
        
        spawn_control = self.function_controller.add_template_node('SpawnControl::Execute(in InitialValue,in Settings,in OffsetTransform,in Parent,in Name,out Item)', unreal.Vector2D(1072, 160), 'SpawnControl_1')
        
        self.function_controller.add_link('%s.Transform' % get_transform.get_node_path(), '%s.InitialValue' % spawn_control.get_node_path())
        
        self.function_controller.set_pin_default_value('%s.Settings.Shape.Name' % spawn_control.get_node_path(), 'Circle_Thin', False)
        
        self.function_controller.add_link('%s.ExecuteContext' % for_each.get_node_path(), '%s.ExecuteContext' % spawn_control.get_node_path())
        
        self.function_controller.set_node_position_by_name('Return', unreal.Vector2D(650, 500))
        
        euler = self.function_controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathQuaternionFromEuler', 'Execute', unreal.Vector2D(900.699942, 553.039171), 'RigVMFunction_MathQuaternionFromEuler')
        self.function_controller.add_link('%s.Result' % euler.get_node_path(), '%s.Settings.Shape.Transform.Rotation' % spawn_control.get_node_path())
        self.function_controller.set_pin_default_value('%s.Euler.Y' % euler.get_node_path(), '90.000000', False)
        
        self.function_controller.set_pin_default_value('%s.Settings.Shape.Transform.Scale3D.X' % spawn_control.get_node_path(), '0.500000', False)
        self.function_controller.set_pin_default_value('%s.Settings.Shape.Transform.Scale3D.Y' % spawn_control.get_node_path(), '0.500000', False)
        self.function_controller.set_pin_default_value('%s.Settings.Shape.Transform.Scale3D.Z' % spawn_control.get_node_path(), '0.500000', False)

        join = self.function_controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_StringJoin', 'Execute', unreal.Vector2D(200, 500.626658), 'RigVMFunction_StringJoin')
        self.function_controller.set_pin_default_value('%s.Separator' % join.get_node_path(), '_', False)
        
        self.function_controller.insert_array_pin('%s.Values' % join.get_node_path(), -1, 'CNT')
        self.function_controller.insert_array_pin('%s.Values' % join.get_node_path(), -1, '')
        self.function_controller.insert_array_pin('%s.Values' % join.get_node_path(), -1, '')
        upper = self.function_controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_StringToUppercase', 'Execute', unreal.Vector2D(-50, 350), 'RigVMFunction_StringToUppercase')
        self.function_controller.add_link('Entry.description', '%s.Value' % upper.get_node_path())
        self.function_controller.add_link('%s.Result' % upper.get_node_path(), '%s.Values.1' % join.get_node_path())
        
        add = self.function_controller.add_template_node('Add::Execute(in A,in B,out Result)', unreal.Vector2D(-150, 450), 'Add')
        self.function_controller.add_link('%s.Index' % for_each.get_node_path(), '%s.A' % add.get_node_path())
        self.function_controller.set_pin_default_value('Add.B', '1', False)
        
        to_string = self.function_controller.add_template_node('DISPATCH_RigDispatch_ToString(in Value,out Result)', unreal.Vector2D(50, 650), 'DISPATCH_RigDispatch_ToString')
        self.function_controller.add_link('%s.Result' % add.get_node_path(), '%s.Value' % to_string.get_node_path())
        self.function_controller.add_link('%s.Result' % to_string.get_node_path(), '%s.Values.2' % join.get_node_path())
        
        from_string = self.function_controller.add_template_node('DISPATCH_RigDispatch_FromString(in String,out Result)', unreal.Vector2D(450, 625), 'DISPATCH_RigDispatch_FromString')
        self.function_controller.add_link('%s.Result' % join.get_node_path(), '%s.String' % from_string.get_node_path())
        self.function_controller.add_link('%s.Result' % from_string.get_node_path(), '%s.Name' % spawn_control.get_node_path())

        meta_data = self.function_controller.add_template_node('DISPATCH_RigDispatch_SetMetadata(in Item,in Name,in Value,out Success)', unreal.Vector2D(1500, 300), 'DISPATCH_RigDispatch_SetMetadata')
        self.function_controller.add_link('%s.ExecuteContext' % spawn_control.get_node_path(), '%s.ExecuteContext' % meta_data.get_node_path())
        self.function_controller.add_link('%s.Item' % spawn_control.get_node_path(), '%s.Item' % meta_data.get_node_path())
        self.function_controller.set_pin_default_value('DISPATCH_RigDispatch_SetMetadata.Name', 'joint', False)
        self.function_controller.add_link('%s.Element' % for_each.get_node_path(), '%s.Value' % meta_data.get_node_path())

    def _build_forward_graph(self):
        pass
    
    def _build_backward_graph(self):
        pass

def remove_rigs():
    
    rigs = attr.get_vetala_nodes('Rig2')
    
    for rig in rigs:
        
        rig_class = cmds.getAttr('%s.rigType' % rig)
        
        rig_inst = eval('%s("%s")' % (rig_class, rig))
        
        rig_inst.delete()
    
    