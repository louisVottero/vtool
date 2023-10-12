# Copyright (C) 2022 Louis Vottero louis.vot@gmail.com    All rights reserved.

import copy
from .. import logger
log = logger.get_logger(__name__)

import string

from vtool import util
from vtool import util_file

in_maya = util.in_maya
in_unreal = util.in_unreal

if in_maya:
    import maya.cmds as cmds

    from vtool.maya_lib import core  
    from vtool.maya_lib import curve


    from ..maya_lib import attr
    from ..maya_lib import space as space_old
    from ..maya_lib2 import space
    

if in_unreal:
    from .. import unreal_lib
    import unreal



def _name(unreal_node):
    if not in_unreal:
        return
    return unreal_node.get_node_path()

      


        
    

class AttrType(object):
    
    EVALUATION = 0
    ANY = 1
    BOOL = 2
    INT = 3
    NUMBER = 4
    STRING = 5
    TRANSFORM = 6
    COLOR = 7
    VECTOR = 8
    

class RigType(object):
    FK = 0
    IK = 1

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
        
        if name in self._node_attributes_dict:
            util.show('\t\tSet node value %s: %s' % (name,value))
            self._node_attributes_dict[name][0] = value
        if name in self._in_attributes_dict:
            util.show('\t\tSet input %s: %s' % (name,value))
            self._in_attributes_dict[name][0] = value
        if name in self._out_attributes_dict:
            util.show('\t\tSet output %s: %s' % (name,value))
            self._out_attributes_dict[name][0] = value
        
    
    def get(self, name, include_type = False):
        if name in self._in_attributes_dict:
            value = self._in_attributes_dict[name]
        if name in self._out_attributes_dict:
            value = self._out_attributes_dict[name]
        if name in self._node_attributes_dict:
            value =  self._node_attributes_dict[name]
        
        if not include_type:
            return value[0]
        else:
            return value
        
    def get_dependency(self, name):
        return self._dependency[name]
        
    def get_all(self):
        return self.inputs + self.outputs + self.node
        
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
        
        self._init_variables()
        self._setup_variables()
        
        self.dirty = True

    def _init_attribute(self):
        self.attr = Attributes()

    def _init_variables(self):
        pass

    def _setup_variables(self):
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
        
        if hasattr(self, 'rig_util'):
            if hasattr(self.rig_util, attribute_name):
                return getattr(self.rig_util. attribute_name)
        
        return getattr(self, attribute_name)
    
    def set_attr(self, attribute_name, value):
        
        if hasattr(self, 'rig_util'):
            if hasattr(self.rig_util, attribute_name):
                self.attr.set(attribute_name, value)
                setattr(self.rig_util, attribute_name, value)
                return
        
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
    rig_description = 'rig'
    
    def __init__(self):
        self._initialize_rig()
        super(Rig, self).__init__()

    def _initialize_rig(self):
        
        self.rig_util = None
        
        if in_maya:
            self.rig_util = self._maya_rig()
        
        if in_unreal:
            self.rig_util = self._unreal_rig()
        
        if self.rig_util:
            self.rig_util.set_rig_class(self)

    def _maya_rig(self):
        from . import rigs_maya
        return rigs_maya.MayaUtilRig()
    
    def _unreal_rig(self):
        from . import rigs_unreal
        return rigs_unreal.UnrealUtilRig()
    
    def _init_variables(self):
        
        self.attr.add_in('Eval IN', [], AttrType.EVALUATION)
        self.attr.add_in('joints', [], AttrType.TRANSFORM)
        
        
        self.attr.add_in('parent', None, AttrType.TRANSFORM)
        
        self.attr.add_to_node('description', self.__class__.rig_description, AttrType.STRING)
        self.attr.add_to_node('side', None, AttrType.STRING)
        self.attr.add_to_node('joint_token', 'joint', AttrType.STRING)
        self.attr.add_to_node('sub_count', 0, AttrType.INT)
        self.attr.add_to_node('restrain_numbering', False, AttrType.BOOL)
        self.attr.add_to_node('control_size', [[1.0,1.0,1.0]], AttrType.VECTOR)
        self.attr.add_to_node('control_translate_offset', [[0.0,0.0,0.0]], AttrType.VECTOR)
        self.attr.add_to_node('control_rotate_offset', [[0.0,0.0,0.0]], AttrType.VECTOR)
        
        
        
        curve_shape = 'circle'
        if in_unreal:
            curve_shape = 'Circle_Thick'
        self.attr.add_in('curve_shape', curve_shape, AttrType.STRING)
        
        self.attr.add_in('color', [[1,0.5,0]], AttrType.COLOR)
        self.attr.add_in('sub_color', [[.75,0.4,0]], AttrType.COLOR)
        
        self.attr.add_out('controls', [], AttrType.TRANSFORM)
        self.attr.add_out('Eval OUT', [], AttrType.EVALUATION)
        
        self.attr.add_update('joints', 'controls')
        self.attr.add_update('description', 'controls')
    
    def _setup_variables(self):
        for input_entry in (self.attr.inputs + self.attr.node + self.attr.outputs):
            input_entry_name = input_entry.replace(' ', '_')
            
            def make_getter(input_entry):
                input_entry_name = input_entry.replace(' ', '_')
                def getter(self):
                    
                    
                    if hasattr(self.rig_util, input_entry_name):
                        return getattr(self.rig_util, input_entry)
                    else:
                        return self.attr.get(input_entry)
                return getter
            
            def make_setter(input_entry):
                input_entry_name = input_entry.replace(' ', '_')
                def setter(self, value):
                    self.attr.set(input_entry_name, value)
                    
                    if not hasattr(self.rig_util, input_entry_name):
                        self.create()
                    
                        if in_unreal:
                            self.rig_util._function_set_attr(input_entry_name, value)
                        
                    if hasattr(self.rig_util, input_entry_name):
                        setattr(self.rig_util, input_entry, value)
                    
                return setter
            
            setattr(self.__class__, input_entry_name, property(make_getter(input_entry), make_setter(input_entry)))
            
    def _get_name(self, prefix = None, description = None, sub = False):
        
        name_list = [prefix,self.description, description, '1', self.side]
            
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
        
        if self.rig_util:
            self.rig_util.unbuild()

    def _create_rig(self):
        
        if self.rig_util:
            controls = self.rig_util.build()
        
            self.attr.set('controls', controls)
    
    def _create(self):
        util.show('\t\tInit %s' % self.__class__.__name__)

        self._create_rig()

    def load(self):
        
        if self.rig_util:
            self.rig_util.load()
        util.show('\tLoad Rig %s %s' % (self.__class__.__name__, self.uuid))
        #self._initialize_rig()

    def create(self):
        
        self.dirty = False
        util.show('\tCreating Rig %s \t%s' % (self.__class__.__name__, self.uuid))
        
        if self.rig_util:
            self.rig_util.load()
        
        self._unbuild_rig()
        
        self._create()
        
        if in_maya and self.rig_util:
            if self.joints:
                attr.fill_multi_message(self.rig_util.set, 'joint', self.joints)

    def delete(self):
        util.show('\tDeleting Rig %s' % self.__class__.__name__)
        if self.rig_util:
            self.rig_util.delete()

class Fk(Rig):
    
    rig_type = RigType.FK
    rig_description = 'fk'
    
    def _init_variables(self):
        super(Fk, self)._init_variables()
        
        self.attr.add_to_node('hierarchy', True, AttrType.BOOL)
        self.attr.add_to_node('use_joint_name', False, AttrType.BOOL)
        
    
    def _maya_rig(self):
        from . import rigs_maya
        return rigs_maya.MayaFkRig()
    
    def _unreal_rig(self):
        from . import rigs_unreal
        return rigs_unreal.UnrealFkRig()
    
    
    
    
class Ik(Rig):      
    
    rig_type = RigType.IK
    rig_description = 'iks'
    
    def _init_values(self):
        super(Ik, self)._init_values()
        self._description = self.__class__.rig_description
    
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

def remove_rigs():
    
    rigs = attr.get_vetala_nodes('Rig2')
    
    for rig in rigs:
        
        rig_class = cmds.getAttr('%s.rigType' % rig)
        
        rig_inst = eval('%s("%s")' % (rig_class, rig))
        
        rig_inst.delete()
    
    