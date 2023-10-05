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

def _name(unreal_node):
    return unreal_node.get_node_path()

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
        
        if cmds.objExists(self.name):
            curve_type = cmds.getAttr('%s.curveType' % self.name)
            self.uuid = cmds.ls(self.name, uuid = True)[0]
            self._curve_shape = curve_type
        
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
        
        if hasattr(self, 'rig_util'):
            if hasattr(self.rig_util, attribute_name):
                return getattr(self.rig_util. attribute_name)
        
        return getattr(self, attribute_name)
    
    def set_attr(self, attribute_name, value):
        if hasattr(self, 'rig_util'):
            if hasattr(self.rig_util, attribute_name):
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
        return MayaUtilRig()
    
    def _unreal_rig(self):
        return UnrealUtilRig()
        
    def _init_values(self):
        #property values
        
        self.use_control_numbering = False
        #self._curve_shape = self.__class__.curve_shape
        
    def _init_variables(self):
        
        self.attr.add_in('Eval IN', [], AttrType.EVALUATION)
        self.attr.add_in('joints', [], AttrType.TRANSFORM)
        
        
        self.attr.add_in('parent', None, AttrType.TRANSFORM)
        
        self.attr.add_to_node('description', self.__class__.rig_description, AttrType.STRING)
        self.attr.add_to_node('Joint Token', 'joint', AttrType.STRING)
        self.attr.add_to_node('Use Joint Name', False, AttrType.BOOL)
        self.attr.add_to_node('side', None, AttrType.STRING)
        
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
                    if hasattr(self.rig_util, input_entry_name):
                        setattr(self.rig_util, input_entry, value)
                    else:
                        self.attr.set(input_entry, value)
                        self.create()
                        
                    
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
    
    def _maya_rig(self):
        return MayaFkRig()
    
    def _unreal_rig(self):
        return UnrealFkRig()
    
    
    
    
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
        #util.show('\t\tPre Build Rig: %s' % self.__class__.__name__)
        return

    def _post_build(self):
        #util.show('\t\tPost Build Rig: %s' % self.__class__.__name__)
        return

    def set_rig_class(self, rig_class_instance):
        self.rig = rig_class_instance
    
    def load(self):
        util.show('\t\tLoad Rig: %s %s' % (self.__class__.__name__, self.rig.uuid))
        pass
    
    def build(self):
        util.show('\t\tBuild Rig: %s' % self.__class__.__name__)
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
    def curve_shape(self):
        return self.rig.attr.get('curve_shape')
    
    @curve_shape.setter
    def curve_shape(self, str_curve_shape):
        
        if not str_curve_shape:
            str_curve_shape = 'circle'
        
        self.rig.attr.set('curve_shape', str_curve_shape)
        
        if not self._controls:
            return
        
        if not self.rig.joints:
            return
        
        for joint, control in zip(self.rig.joints, self._controls):
            control.curve_shape = self.rig.curve_shape
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
        control_name = control_name.replace('__', '_')
        
        control = Control( control_name )
        
        control.curve_shape = self.rig.curve_shape
        
        attr.append_multi_message(self.set, 'control', str(control))
        self._controls.append(control)
        
        #self._parent_controls(self.rig.attr.get('parent'))
        
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
            control.color = self.rig.color[0]
            
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
        
        rotate_cvs = True
        
        if len(joints) == 1:
            rotate_cvs = False
        
        use_joint_name = self.rig.attr.get('Use Joint Name')
        joint_token = self.rig.attr.get('Joint Token')
        
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
        
#--- Unreal
class UnrealUtilRig(PlatformUtilRig):
    
    def __init__(self):
        super(UnrealUtilRig, self).__init__()
        
        self.construct_controller = None
        self.construct_node = None
        
        self.forward_controller = None
        self.forward_node = None
        
        self.backward_controller = None
        self.backward_function_node = None
        
    
    def _init_graph(self):
        if not self.graph:
            return 
        
        #if not self.graph.set_node_selection(['BeginExecution']):
        #    self.forward_node = self.graph.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_BeginExecution', 'Execute', unreal.Vector2D(0, 0), 'BeginExecution')
        
        if not self.construct_controller:
            model = unreal_lib.util.add_construct_graph()
            self.construct_controller = self.graph.get_controller_by_name(model.get_graph_name())
        
        if not self.backward_controller:
            model = unreal_lib.util.add_backward_graph()
            self.backward_controller = self.graph.get_controller_by_name(model.get_graph_name())



    
    def _init_rig_function(self):
        if not self.graph:
            return
        
        rig_name = 'rig_%s' % self.__class__.__name__
        rig_name = rig_name.replace('Unreal', 'Vetala')
        
        found = self.controller.get_graph().find_function(rig_name)
        
        if found:
            
            self.function = found
            function_controller = self.graph.get_controller_by_name(self.function.get_node_path())
            self.function_controller = function_controller
            
        else:
            self.function = self.controller.add_function_to_library(rig_name, True, unreal.Vector2D(0,0))
            self.function_controller = self.graph.get_controller_by_name(self.function.get_node_path())
            self.function_library = self.graph.get_controller_by_name('RigVMFunctionLibrary')
            
            self._initialize_node_attributes()
            self._initialize_inputs()
            self._initialize_outputs()
            
            self._build_function_graph()
        
    def _add_color_array_in(self, name, value):
        
        color = value[0]
        
        color_pin = self.function_controller.add_exposed_pin(name, unreal.RigVMPinDirection.INPUT, 'TArray<FLinearColor>', '/Script/CoreUObject.LinearColor', '')
        self.function_library.insert_array_pin('%s.%s' % (self.function.get_name(), color_pin), -1, '')
        
        self.function_library.set_pin_default_value('%s.%s.0.R' % (self.function.get_name(), color_pin), str(color[0]), False)
        self.function_library.set_pin_default_value('%s.%s.0.G' % (self.function.get_name(), color_pin), str(color[1]), False)
        self.function_library.set_pin_default_value('%s.%s.0.B' % (self.function.get_name(), color_pin), str(color[2]), False)
    
    def _add_color_array_out(self, name, value):
        
        color = value[0]
        
        color_pin = self.function_controller.add_exposed_pin(name, unreal.RigVMPinDirection.OUTPUT, 'TArray<FLinearColor>', '/Script/CoreUObject.LinearColor', '')
        self.function_library.insert_array_pin('%s.%s' % (self.function.get_name(), color_pin), -1, '')
        
        self.function_library.set_pin_default_value('%s.%s.0.R' % (self.function.get_name(), color_pin), str(color[0]), False)
        self.function_library.set_pin_default_value('%s.%s.0.G' % (self.function.get_name(), color_pin), str(color[1]), False)
        self.function_library.set_pin_default_value('%s.%s.0.B' % (self.function.get_name(), color_pin), str(color[2]), False)
    
    def _add_transform_array_in(self, name):
        transform_pin = self.function_controller.add_exposed_pin(name, unreal.RigVMPinDirection.INPUT, 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', '')
        #self.function_controller.insert_array_pin('%s.%s' % (self.function.get_name(),transform_pin), -1, '')
    
    def _add_transform_array_out(self, name):
        transform_pin = self.function_controller.add_exposed_pin(name, unreal.RigVMPinDirection.OUTPUT, 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', '')
        #self.function_controller.insert_array_pin('%s.%s' % (self.function.get_name(),transform_pin), -1, '')
        
    def _initialize_inputs(self):
        
        self.function_controller.add_exposed_pin('uuid', unreal.RigVMPinDirection.INPUT, 'FString', 'None', '')
        self.function_controller.add_exposed_pin('mode', unreal.RigVMPinDirection.INPUT, 'int32', 'None', '')
        
        inputs = self.rig.attr.inputs
        for name in inputs:
            value, attr_type = self.rig.attr._in_attributes_dict[name]
            
            if attr_type == AttrType.COLOR:
                self._add_color_array_in(name, value)
                
            if attr_type == AttrType.STRING:
                if value == None:
                    value = ''
                self.function_controller.add_exposed_pin(name, unreal.RigVMPinDirection.INPUT, 'FString', 'None', value)
                
            if attr_type == AttrType.TRANSFORM:
                self._add_transform_array_in(name)
        
    def _initialize_node_attributes(self):
        
        node_attrs = self.rig.attr.node
        for name in node_attrs:
            value, attr_type = self.rig.attr._node_attributes_dict[name]
            
            if attr_type == AttrType.COLOR:
                self._add_color_array_in(name, value)
                
            if attr_type == AttrType.STRING:
                if value == None:
                    value = ''
                self.function_controller.add_exposed_pin(name, unreal.RigVMPinDirection.INPUT, 'FString', 'None', value)
                
            if attr_type == AttrType.TRANSFORM:
                self._add_transform_array_in(name)
                
    def _initialize_outputs(self):
        #function_library = self.graph.get_controller_by_name('RigVMFunctionLibrary')
        
        outputs = self.rig.attr.outputs
        for name in outputs:
            
            value, attr_type = self.rig.attr._out_attributes_dict[name]
            
            if attr_type == AttrType.COLOR:
                self._add_color_array_out(name, value)
                
            if attr_type == AttrType.STRING:
                if value == None:
                    value = ''
                self.function_controller.add_exposed_pin(name, unreal.RigVMPinDirection.OUTPUT, 'FString', 'None', value)
                
            if attr_type == AttrType.TRANSFORM:
                self._add_transform_array_out(name)

    def _get_function_node(self, function_controller):
        
        if not function_controller:
            return
        
        nodes = function_controller.get_graph().get_nodes()
        
        if not nodes:
            return
            
        for node in nodes:
            
            pin = function_controller.get_graph().find_pin('%s.uuid' % _name(node))
            if pin:
                node_uuid = pin.get_default_value()
                if node_uuid == self.rig.uuid:
                    return node
    
    def _add_construct_node_to_construct_graph(self):
        function_node = self.construct_controller.add_function_reference_node(self.function, unreal.Vector2D(100, 100), _name(self.function))
        self.construct_node = function_node
        
        last_construct = unreal_lib.util.get_last_execute_node(self.construct_controller.get_graph())
        if not last_construct:
            self.construct_controller.add_link('PrepareForExecution.ExecuteContext', '%s.ExecuteContext' % (function_node.get_node_path()))
        else:
            self.construct_controller.add_link('%s.ExecuteContext' % last_construct.get_node_path(), '%s.ExecuteContext' % (function_node.get_node_path()))
        self.construct_controller.set_pin_default_value('%s.uuid' % function_node.get_node_path(), self.rig.uuid, False)
    
    def _add_forward_node_to_construct_graph(self):
        function_node = self.forward_controller.add_function_reference_node(self.function, unreal.Vector2D(100, 100), self.function.get_node_path())
        self.forward_node = function_node
        
        self.forward_controller.set_pin_default_value('%s.mode' % function_node.get_node_path(), '1', False)
        
        last_forward = unreal_lib.util.get_last_execute_node(self.forward_controller.get_graph())
        if not last_forward:
            self.forward_controller.add_link('RigUnit_BeginExecution.ExecuteContext', '%s.ExecuteContext' % (function_node.get_node_path()))
        else:
            self.forward_controller.add_link('%s.ExecuteContext' % _name(last_forward), '%s.ExecuteContext' % (function_node.get_node_path()))
        self.forward_controller.set_pin_default_value('%s.uuid' % _name(function_node), self.rig.uuid, False)

    def _reset_array(self, name):
        self.construct_controller.clear_array_pin('%s.%s' % (_name(self.construct_node), name))
        self.forward_controller.clear_array_pin('%s.%s' % (_name(self.forward_node), name))
        
        self.construct_controller.set_pin_default_value('%s.%s' % (self.construct_node.get_node_path(), name), '()', True)
        self.forward_controller.set_pin_default_value('%s.%s' % (self.forward_node.get_node_path(), name), '()', True)

    def _add_array_entry(self, name, value):
        pass

    def _function_set_attr(self, name, custom_value = None):
        
        value, value_type = self.rig.attr.get(name, True)
        util.show('\t\tSet Unreal Function %s Pin %s %s: %s' % (self.__class__.__name__, name,value_type, value))
        
        if custom_value:
            value = custom_value
        
        if value_type == AttrType.STRING:
            self.construct_controller.set_pin_default_value('%s.%s' % (_name(self.construct_node), name), value, False)
            self.forward_controller.set_pin_default_value('%s.%s' % (_name(self.forward_node), name), value, False)
        
        if value_type == AttrType.COLOR:
            self._reset_array(name)
            color = value[0]
            
            self.construct_controller.insert_array_pin('%s.%s' % (_name(self.construct_node), name), -1, '')
            self.construct_controller.set_pin_default_value('%s.%s.0.R' % (_name(self.construct_node), name), str(color[0]), True)
            self.construct_controller.set_pin_default_value('%s.%s.0.G' % (self.construct_node.get_node_path(),name), str(color[1]), True)
            self.construct_controller.set_pin_default_value('%s.%s.0.B' % (self.construct_node.get_node_path(),name), str(color[2]), True)
            
        if value_type == AttrType.TRANSFORM:
            self._reset_array(name)
            
            if not value:
                return
            
            construct_pin = '%s.%s' % (self.construct_node.get_node_path(), name)
            forward_pin = '%s.%s' % (self.forward_node.get_node_path(), name)
            
            inc = 0
            for joint in value:
                self.construct_controller.insert_array_pin(construct_pin, -1, '')
                self.forward_controller.insert_array_pin(forward_pin, -1, '')
                
                self.construct_controller.set_pin_default_value('%s.%s.Type' % (construct_pin, inc), 'Bone', False)
                self.construct_controller.set_pin_default_value('%s.%s.Name' % (construct_pin, inc), joint, False)
                
                self.forward_controller.set_pin_default_value('%s.%s.Type' % (forward_pin, inc), 'Bone', False)
                self.forward_controller.set_pin_default_value('%s.%s.Name' % (forward_pin, inc), joint, False)
                
                inc+=1

    def _build_function_graph(self):    
        return
    
    def set_node_position(self, position_x, position_y):
        
        if self.construct_node:
            self.construct_controller.set_node_position_by_name(_name(self.construct_node), unreal.Vector2D(position_x, position_y))
        if self.forward_node:
            self.forward_controller.set_node_position_by_name(_name(self.forward_node), unreal.Vector2D(position_x, position_y))
        
    @property
    def controls(self):
        return
        #value = self.construct_controller.get_pin_default_value('%s.%s' % (_name(self. construct_node), 'controls'))
        #return value
        
    
    @controls.setter
    def controls(self, value):
        return
        #if not value:
        #    value = self.construct_controller.get_pin_default_value('%s.%s' % (_name(self. construct_node), 'controls'))
        
        #self.rig.attr.set('controls', value)
    
    @property
    def parent(self):
        return
    
    @parent.setter
    def parent(self, value):
        return
    
    @property
    def joints(self):
        value = self.construct_controller.get_pin_default_value('%s.joints' % _name(self. construct_node))
        return value
    
    @joints.setter
    def joints(self, value):
        self.rig.attr.set('joints', value)
        self._function_set_attr('joints',value)
        
    
    @property
    def description(self):
        return self.rig.attr.get('description')
        
    @description.setter
    def description(self, value):
        self.construct_controller.set_pin_default_value('%s.description' % self.construct_node.get_node_path(), value, False)
        self.forward_controller.set_pin_default_value('%s.description' % self.forward_node.get_node_path(), value, False)
    
    @property
    def side(self):
        return
    
    @side.setter
    def side(self, value):
        return
    
    @property
    def curve_shape(self):
        return self.rig.attr.get('curve_shape')
    
    @curve_shape.setter
    def curve_shape(self, str_curve_shape):
        
        if not str_curve_shape:
            str_curve_shape = 'Default'
        
        self.rig.attr.set('curve_shape', str_curve_shape)
        
        self._function_set_attr('curve_shape')
        
    @property
    def color(self):
        return self.rig.attr.get('color')
    
    @color.setter
    def color(self, value):
        self.rig.attr.set('color', value)
        self._function_set_attr('color')
        
    @property
    def sub_color(self):
        return self.rig.attr.get('sub_color')
    
    @sub_color.setter
    def sub_color(self, value):
        self.rig.attr.set('sub_color', value)
        self._function_set_attr('sub_color')
    
    @property
    def Eval_IN(self):
        return
    
    @property
    def Eval_OUT(self):
        return
        
    
    def load(self):
        super(UnrealUtilRig, self).load()
        
        self.graph = unreal_lib.util.current_control_rig
        
        if not self.graph:
            control_rigs = unreal.ControlRigBlueprint.get_currently_open_rig_blueprints()
            if not control_rigs:
                return
            unreal_lib.util.current_control_rig = control_rigs[0]
            self.graph = control_rigs[0]
            
        if not self.graph:
            util.warning('No control rig set, cannot load.')
            return 
        
        #unreal.AssetEditorSubsystem().open_editor_for_assets([self.graph])
        
        self.library = self.graph.get_local_function_library()
        self.controller = self.graph.get_controller(self.library)
        
        self.forward_controller = self.graph.get_controller_by_name('RigVMModel')
        
        models = self.graph.get_all_models()
        for model in models:
            if _name(model).find('Construction Event Graph') > -1:
                self.construct_controller = unreal_lib.util.get_graph_model_controller(model)
            if _name(model).find('Backwards Solve Graph') > -1:
                self.backward_controller = unreal_lib.util.get_graph_model_controller(model)    
                
        if not self.construct_controller:
            util.warning('No construction graph found.')
            return
        
        self.construct_node = self._get_function_node(self.construct_controller)
        self.forward_node = self._get_function_node(self.forward_controller)
        self.backward_function_node = self._get_function_node(self.backward_controller)
        
        if self.construct_controller:
            self.rig.dirty = False
        
    def build(self):
        super(UnrealUtilRig, self).build()
        
        if not self.graph:
            util.warning('No control rig for Unreal rig')
            return
        #function_node = self.construct_controller.get_graph().find_node(self.function.get_node_path())
        
        self._init_graph()
        self._init_rig_function()
        
        if not self.construct_node:
            self._add_construct_node_to_construct_graph()
            
        if not self.forward_node:
            self._add_forward_node_to_construct_graph()
        
        if not self.construct_node:
            util.warning('No construct function for Unreal rig')
            return
        
        self._function_set_attr('description')
        self._function_set_attr('color')
        self._function_set_attr('joints')
        self._function_set_attr('parent')
        self._function_set_attr('curve_shape')
        
        self.graph.recompile_vm()
        
    def unbuild(self):
        super(UnrealUtilRig, self).unbuild()
        
    def delete(self):
        super(UnrealUtilRig, self).delete()
        if not self.graph:
            return
        
        if not self.construct_node:
            self.load()
        
        super(UnrealUtilRig, self).unbuild()
        
        if self.construct_node:
            self.construct_controller.remove_node_by_name(self.construct_node.get_node_path())
        
        if self.forward_node:
            self.forward_controller.remove_node_by_name(self.forward_node.get_node_path())
            
        if self.backward_function_node:
            self.backward_controller.remove_node_by_name(self.backward_function_node.get_node_path())

class UnrealFkRig(UnrealUtilRig):
    

    
    def _build_function_graph(self):
        super(UnrealFkRig, self)._build_function_graph()
        if not self.graph:
            return
        
        switch = self.function_controller.add_template_node('DISPATCH_RigVMDispatch_SwitchInt32(in Index)', unreal.Vector2D(225, -160), 'DISPATCH_RigVMDispatch_SwitchInt32')
        self.function_controller.add_link('Entry.ExecuteContext', '%s.ExecuteContext' % switch.get_node_path())
        self.function_controller.add_link('Entry.mode', '%s.Index' % switch.get_node_path())
        self.function_controller.add_link('%s.Completed' % (switch.get_node_path()), 'Return.ExecuteContext')
        
        self.function_controller.add_link('%s.ExecuteContext' % _name(switch), 'Return.ExecuteContext')
        
        self.switch = switch
        
        
        self._build_construct_graph()
        self._build_forward_graph()
        self._build_backward_graph()
        
    def _build_construct_graph(self):
        
        for_each = self.function_controller.add_template_node('DISPATCH_RigVMDispatch_ArrayIterator(in Array,out Element,out Index,out Count,out Ratio)', unreal.Vector2D(300, 150), 'DISPATCH_RigVMDispatch_ArrayIterator')
        self.function_controller.add_link('%s.Cases.0' % self.switch.get_node_path(), '%s.ExecuteContext' % (for_each.get_node_path()))
                
        self.function_controller.add_link('Entry.joints', '%s.Array' % (for_each.get_node_path()))
        
        #get_transform = self.function_controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetTransform', 'Execute', unreal.Vector2D(640, 240), 'GetTransform_1')
        get_transform = self.function_controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetRelativeTransformForItem', 'Execute', unreal.Vector2D(640, 240), 'GetRelativeTransformForItem_1')
        
        #self.function_controller.set_pin_default_value('%s.Space' % get_transform.get_node_path(), 'LocalSpace', False)
        
        self.function_controller.add_link('%s.Element' % for_each.get_node_path(), '%s.Child' % get_transform.get_node_path())
        
        spawn_control = self.function_controller.add_template_node('SpawnControl::Execute(in InitialValue,in Settings,in OffsetTransform,in OffsetSpace,in Parent,in Name,out Item)', unreal.Vector2D(1072, 160), 'SpawnControl')
        #spawn_control = self.function_controller.add_template_node('SpawnControl::Execute(in InitialValue,in Settings,in OffsetTransform,in Parent,in Name,out Item)', unreal.Vector2D(1072, 160), 'SpawnControl_1')
        
        self.function_controller.add_link('%s.RelativeTransform' % get_transform.get_node_path(), '%s.OffsetTransform' % spawn_control.get_node_path())
        self.function_controller.add_link('%s.RelativeTransform' % get_transform.get_node_path(), '%s.InitialValue' % spawn_control.get_node_path())
        self.function_controller.break_link('%s.RelativeTransform' % get_transform.get_node_path(), '%s.InitialValue' % spawn_control.get_node_path())
        
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
        self.function_controller.add_link('%s.Element' % for_each.get_node_path(), '%s.Item' % meta_data.get_node_path())
        self.function_controller.set_pin_default_value('DISPATCH_RigDispatch_SetMetadata.Name', 'Control', False)
        self.function_controller.add_link('%s.Item' % spawn_control.get_node_path(), '%s.Value' % meta_data.get_node_path())
        
        parent = self.function_controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyGetParent', 'Execute', unreal.Vector2D(1000, 700), 'HierarchyGetParent')
        self.function_controller.add_link('%s.Element' % for_each.get_node_path(), '%s.Child' % parent.get_node_path())
        parent_data = self.function_controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in Default,out Value,out Found)', unreal.Vector2D(1250, 750), 'DISPATCH_RigDispatch_GetMetadata_1')
        self.function_controller.add_link('%s.Parent' % parent.get_node_path(), '%s.Item' % parent_data.get_node_path())
        self.function_controller.set_pin_default_value('%s.Name' % parent_data.get_node_path(), 'Control', False)
        
        
        parent_equals = self.function_controller.add_template_node('DISPATCH_RigVMDispatch_CoreEquals(in A,in B,out Result)', unreal.Vector2D(700, 50), 'DISPATCH_RigVMDispatch_CoreEquals')
        parent_if = self.function_controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(900, 50), 'DISPATCH_RigVMDispatch_If')
        
        self.function_controller.add_link('%s.Result' % parent_if.get_node_path(), '%s.Parent' % get_transform.get_node_path())
        
        self.function_controller.add_link('%s.Index' % for_each.get_node_path(), '%s.A' % parent_equals.get_node_path())
        self.function_controller.add_link('%s.Result' % parent_equals.get_node_path(), '%s.Condition' % parent_if.get_node_path())
        
        get_parent_index = self.function_controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(530, 64), 'DISPATCH_RigVMDispatch_ArrayGetAtIndex_1')
        
        num = self.function_controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetNum(in Array,out Num)', unreal.Vector2D(-700, -70), 'DISPATCH_RigVMDispatch_ArrayGetNum')
        greater = self.function_controller.add_template_node('Greater::Execute(in A,in B,out Result)', unreal.Vector2D(-450, -30), 'Greater')
        if_parent = self.function_controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(-635.098583, 67.131332), 'DISPATCH_RigVMDispatch_If_2')
        
        self.function_controller.add_link('Entry.parent', '%s.True' % _name(if_parent))
        
        self.function_controller.insert_array_pin('%s.False' % _name(if_parent), -1, '')
        self.function_controller.set_pin_default_value('%s.False.0.Type' % _name(if_parent), 'Bone', False)
        
        self.function_controller.add_link('Entry.parent', '%s.Array' % _name(num))
        self.function_controller.add_link('%s.Num' % _name(num), '%s.A' % _name(greater))
        self.function_controller.add_link('%s.Result' % _name(greater), '%s.Condition' % _name(if_parent))
        self.function_controller.add_link('%s.Result' % _name(if_parent), '%s.Array' % _name(get_parent_index))
        
        
        
        #self.function_controller.add_link('Entry.parent', '%s.Array' % get_parent_index.get_node_path())
        self.function_controller.set_pin_default_value('%s.Index' % get_parent_index.get_node_path(), '-1', False)
        self.function_controller.add_link('%s.Element' % get_parent_index.get_node_path(), '%s.True' % parent_if.get_node_path())
        #self.function_controller.add_link('Entry.parent', '%s.True' % parent_if.get_node_path())
        
        self.function_controller.add_link('%s.Value' % parent_data.get_node_path(), '%s.False' % parent_if.get_node_path())
        self.function_controller.add_link('%s.Result' % parent_if.get_node_path(), '%s.Parent' % spawn_control.get_node_path())
        
        color_at = self.function_controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(400, 400), 'DISPATCH_RigVMDispatch_ArrayGetAtIndex')
        self.function_controller.add_link('Entry.color', '%s.Array' % color_at.get_node_path())
        self.function_controller.add_link('%s.Element' % color_at.get_node_path(), '%s.Settings.Shape.Color' % spawn_control.get_node_path())
        
        #self.function_controller.add_local_variable_from_object_path('local_controls', 'bool', '', '')
        self.function_controller.add_local_variable_from_object_path('local_controls', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', '')
        
        add_control = self.function_controller.add_template_node('DISPATCH_RigVMDispatch_ArrayAdd(io Array,in Element,out Index)', unreal.Vector2D(1980, 500), 'DISPATCH_RigVMDispatch_ArrayAdd')
        self.function_controller.add_link('%s.Item' % _name(spawn_control), '%s.Element' % _name(add_control))
        self.function_controller.add_link('%s.ExecuteContext' % _name(meta_data), '%s.ExecuteContext' % _name(add_control))
        
        variable_node = self.function_controller.add_variable_node_from_object_path('local_controls', 'FRigElementKey', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(1680, 450), 'VariableNode')
        self.function_controller.add_link('%s.Value' % _name(variable_node), '%s.Array' % _name(add_control))
        
        self.function_controller.set_node_position_by_name('Return', unreal.Vector2D(2350.000000, 600.000000))
        
        #self.function_controller.add_link('%s.Array' % _name(add_control), 'Return.controls')
        
        self.function_controller.add_link('%s.Value' % _name(variable_node), 'Return.controls')
        
        curve_shape_from_string = self.function_controller.add_template_node('DISPATCH_RigDispatch_FromString(in String,out Result)', unreal.Vector2D(691.123141, 774.231856), 'DISPATCH_RigDispatch_FromString_1')
        
        self.function_controller.add_link('Entry.curve_shape', '%s.String' % _name(curve_shape_from_string))
        self.function_controller.add_link('%s.Result' % _name(curve_shape_from_string), '%s.Settings.Shape.Name' % _name(spawn_control))

    def _build_forward_graph(self):
        
        for_each = self.function_controller.add_template_node('DISPATCH_RigVMDispatch_ArrayIterator(in Array,out Element,out Index,out Count,out Ratio)', unreal.Vector2D(700, -300), 'DISPATCH_RigVMDispatch_ArrayIterator')
        self.function_controller.add_link('%s.Cases.1' % self.switch.get_node_path(), '%s.ExecuteContext' % (for_each.get_node_path()))
        self.function_controller.add_link('Entry.joints', '%s.Array' % (for_each.get_node_path()))
        
        meta_data = self.function_controller.add_template_node('DISPATCH_RigDispatch_GetMetadata(in Item,in Name,in Default,out Value,out Found)', unreal.Vector2D(975.532734, -167.022334), 'DISPATCH_RigDispatch_GetMetadata')
        self.function_controller.set_pin_default_value('%s.Name' % meta_data.get_node_path(), 'Control', False)
        self.function_controller.add_link('%s.Element' % for_each.get_node_path(), '%s.Item' % meta_data.get_node_path())
        
        get_transform = self.function_controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetTransform', 'Execute', unreal.Vector2D(1311.532734, -95.022334), 'GetTransform')
        self.function_controller.add_link('%s.Value' % meta_data.get_node_path(), '%s.Item' % get_transform.get_node_path())
        set_transform = self.function_controller.add_template_node('Set Transform::Execute(in Item,in Space,in bInitial,in Value,in Weight,in bPropagateToChildren)', unreal.Vector2D(1765.247019, -174.772082), 'Set Transform')
        
        self.function_controller.add_link('%s.Transform' % get_transform.get_node_path(), '%s.Value' % set_transform.get_node_path())
        self.function_controller.add_link('%s.Element' % for_each.get_node_path(), '%s.Item' % set_transform.get_node_path())
        
        self.function_controller.add_link('%s.ExecuteContext' % for_each.get_node_path(), '%s.ExecuteContext' % set_transform.get_node_path())
        
        
        
    def _build_backward_graph(self):
        pass

def remove_rigs():
    
    rigs = attr.get_vetala_nodes('Rig2')
    
    for rig in rigs:
        
        rig_class = cmds.getAttr('%s.rigType' % rig)
        
        rig_inst = eval('%s("%s")' % (rig_class, rig))
        
        rig_inst.delete()
    
    