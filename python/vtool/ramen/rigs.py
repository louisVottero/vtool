# Copyright (C) 2024 Louis Vottero louis.vot@gmail.com    All rights reserved.

from . import util as ramen_util

from vtool import util

in_maya = util.in_maya
in_unreal = util.in_unreal
in_houdini = util.in_houdini


class AttrType(object):
    EVALUATION = 0
    ANY = 1
    BOOL = 2
    INT = 3
    NUMBER = 4
    STRING = 5
    TITLE = 6
    COLOR = 7
    VECTOR = 8
    MATRIX = 9
    TRANSFORM = 10


class RigType(object):
    FK = 0
    IK = 1
    UTIL = 2
    SPLINEIK = 3
    WHEEL = 10


class RigState(object):
    INITIALIZED = 0
    LOADED = 1
    CREATED = 2


class Attributes(object):

    def __init__(self):
        self._all_attributes = []
        self._in_attributes = []
        self._in_attributes_dict = {}

        self._out_attributes = []
        self._out_attributes_dict = {}

        self._node_attributes = []
        self._node_attributes_dict = {}

        self._dependency = {}

    def add_in(self, name, value, data_type):
        self._in_attributes.append(name)
        self._in_attributes_dict[name] = [value, data_type]
        self._all_attributes.append(name)

    def add_out(self, name, value, data_type):
        self._out_attributes.append(name)
        self._out_attributes_dict[name] = [value, data_type]
        self._all_attributes.append(name)

    def add_to_node(self, name, value, data_type):
        self._node_attributes.append(name)
        self._node_attributes_dict[name] = [value, data_type]
        self._all_attributes.append(name)

    def add_update(self, source_name, target_name):

        if source_name not in self._dependency:
            self._dependency[source_name] = []

        if target_name not in self._dependency[source_name]:
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
            # util.show('\t\tSet node value %s: %s' % (name, value))
            self._node_attributes_dict[name][0] = value
        if name in self._in_attributes_dict:
            # util.show('\t\tSet input %s: %s' % (name, value))
            self._in_attributes_dict[name][0] = value
        if name in self._out_attributes_dict:
            # util.show('\t\tSet output %s: %s' % (name, value))
            self._out_attributes_dict[name][0] = value

    def get(self, name, include_type=False):
        value = None
        if name in self._in_attributes_dict:
            value = self._in_attributes_dict[name]
        if name in self._out_attributes_dict:
            value = self._out_attributes_dict[name]
        if name in self._node_attributes_dict:
            value = self._node_attributes_dict[name]

        if value == None:
            return

        if not include_type:
            return value[0]
        else:
            return value

    def get_dependency(self, name):
        return self._dependency[name]

    def get_all(self):
        return self.inputs + self.outputs + self.node

    def get_data_for_export(self):

        data = {'in': [self._in_attributes, self._in_attributes_dict],
                'out': [self._out_attributes, self._out_attributes_dict],
                'node': [self._node_attributes, self._node_attributes_dict],
                'dependency': self._dependency}

        return data

    def set_data_from_export(self, data_dict):

        self._node_attributes, self._node_attributes_dict = data_dict['node']
        self._in_attributes, self._in_attributes_dict = data_dict['in']
        self._out_attributes, self._out_attributes_dict = data_dict['out']
        self._dependency = data_dict['dependency']


class Base(object):

    def __init__(self):
        self._uuid = None
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

    def get_all_attributes(self):
        return self.attr._all_attributes

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

    def get_any(self, name):
        if name in self.attr._in_attributes_dict:
            return self.attr._in_attributes_dict[name]
        if name in self.attr._node_attributes_dict:
            return self.attr._node_attributes_dict[name]

    def get_attr_dependency(self):
        return self.attr._dependency

    def get_attr(self, attribute_name):

        if hasattr(self, 'rig_util'):
            if hasattr(self.rig_util, attribute_name):
                return getattr(self.rig_util, attribute_name)

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

    def load(self):
        if self.state == RigState.LOADED:
            return
        util.show('\tLoad Rig %s %s' % (self.__class__.__name__, self.uuid))

    def is_valid(self):
        return True

    def has_rig_util(self):
        return False


class Rig(Base):
    rig_type = -1
    rig_description = 'rig'

    def __init__(self):

        self._initialize_rig()
        super(Rig, self).__init__()

    def __getattribute__(self, item):

        custom_functions = ('load', 'create', 'delete')

        if item in custom_functions:

            result = object.__getattribute__(self, item)

            if item == 'load':
                self.state = RigState.LOADED
            elif item == 'create':
                self.state = RigState.CREATED
            elif item == 'delete':
                self.state = RigState.INITIALIZED

            return result

        else:
            return object.__getattribute__(self, item)

    def _initialize_rig(self):

        self.rig_util = None

        if in_maya:
            self.rig_util = self._maya_rig()

        if in_unreal:
            self.rig_util = self._unreal_rig()

        if in_houdini:
            self.rig_util = self._houdini_rig()

        if self.rig_util:
            self.rig_util.set_rig_class(self)

        self.state = RigState.INITIALIZED

    def _maya_rig(self):
        from . import rigs_maya
        return rigs_maya.MayaUtilRig()

    def _unreal_rig(self):
        from . import rigs_unreal
        return rigs_unreal.UnrealUtilRig()

    def _houdini_rig(self):
        from . import rigs_houdini
        return rigs_houdini.HoudiniUtilRig()

    def _support_sub_controls(self):
        return True

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

                    if hasattr(self.rig_util, input_entry_name):
                        setattr(self.rig_util, input_entry, value)
                    else:
                        self.create()
                        if in_unreal:
                            self.rig_util._set_attr_on_function(input_entry_name, value)

                return setter

            setattr(self.__class__, input_entry_name, property(make_getter(input_entry), make_setter(input_entry)))

    def _init_variables(self):
        pass

    def _get_name(self, prefix=None, description=None, sub=False):

        rig_description = ''
        side = ''

        if self.description:
            rig_description = self.description[0]
        if self.side:
            side = self.side[0]

        name_list = (prefix, rig_description, description, '1', side)

        filtered_name_list = []

        for name in name_list:
            if name:
                filtered_name_list.append(str(name))

        name = '_'.join(filtered_name_list)

        return name

    def _unbuild_rig(self):

        if self.rig_util:
            self.rig_util.unbuild()

    def _create_rig(self):

        if self.rig_util:
            self.rig_util.build()
        if not self.rig_util:
            util.show('\t\tNo platfrom rig set. Could not create rig.')

    def _create(self):
        util.show('\t\tInit %s' % self.__class__.__name__)

        self._create_rig()

    def is_valid(self):
        if not self.has_rig_util():
            return False

        if hasattr(self.rig_util, 'is_valid'):
            return self.rig_util.is_valid()

        return False

    def is_built(self):
        util.show('Is built not implemented')
        return

    def has_rig_util(self):
        if self.rig_util:
            return True

        return False

    def load(self):
        super(Rig, self).load()

        if self.rig_util and not self.rig_util.is_valid():
            self.rig_util.load()

    def create(self):

        if self.state == RigState.CREATED:
            if self.rig_util and self.rig_util.is_built():
                return

        self.dirty = False
        util.show('\tCreating Rig %s \t%s' % (self.__class__.__name__, self.uuid))

        if self.rig_util and not self.rig_util.is_valid():
            self.rig_util.load()

        self._unbuild_rig()
        if self.attr.exists('joints'):
            util.show('\tUsing Joints: %s' % self.attr.get('joints'))
        self._create()

        if self.attr.exists('controls'):
            controls = self.attr.get('controls')
            if controls:
                util.show('\tCreated Controls: %s' % controls)

        self.state = RigState.CREATED

    def delete(self):
        util.show('\tDeleting Rig %s' % self.__class__.__name__)

        if self.rig_util and not self.rig_util.is_valid():
            self.load()

        if self.rig_util:
            self.rig_util.delete()


class RigUtil(Rig):
    pass


class RigJoint(Rig):

    def _init_variables(self):

        self.attr.add_in('Eval IN', [], AttrType.EVALUATION)

        self.attr.add_in('parent', None, AttrType.TRANSFORM)

        self.attr.add_to_node('Name', [''], AttrType.TITLE)
        self.attr.add_in('description', [self.__class__.rig_description], AttrType.STRING)
        self.attr.add_in('side', [''], AttrType.STRING)
        self.attr.add_to_node('restrain_numbering', False, AttrType.BOOL)

        self.attr.add_to_node('Rig Inputs', [''], AttrType.TITLE)
        self.attr.add_in('joints', [], AttrType.TRANSFORM)
        self.attr.add_to_node('joint_token', [''], AttrType.STRING)

        self.attr.add_to_node('Control', [''], AttrType.TITLE)
        self.attr.add_in('color', [[1, 0.5, 0, 1.0]], AttrType.COLOR)
        self.attr.add_in('shape', ['Default'], AttrType.STRING)

        self.attr.add_in('shape_translate', [[0.0, 0.0, 0.0]], AttrType.VECTOR)
        self.attr.add_in('shape_rotate', [[0.0, 0.0, 0.0]], AttrType.VECTOR)
        self.attr.add_in('shape_scale', [[1.0, 1.0, 1.0]], AttrType.VECTOR)

        if self._support_sub_controls():
            self.attr.add_to_node('Sub Control', [''], AttrType.TITLE)
            self.attr.add_to_node('sub_count', [0], AttrType.INT)
            self.attr.add_in('sub_color', [[.55, 0.22, 0, 1.0]], AttrType.COLOR)

        self.attr.add_out('controls', [], AttrType.TRANSFORM)

        self.attr.add_out('Eval OUT', [], AttrType.EVALUATION)

        self.attr.add_update('joints', 'controls')
        self.attr.add_update('description', 'controls')


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
            return object.__getattribute__(self, item)

    def _pre_build(self):
        # util.show('\t\tPre Build Rig: %s' % self.__class__.__name__)
        return

    def _post_build(self):
        # util.show('\t\tPost Build Rig: %s' % self.__class__.__name__)
        return

    def get_control_name(self, description=None, sub=False):

        rig_description = self.rig.attr.get('description')
        if rig_description:
            rig_description = rig_description[0]

        restrain_numbering = self.rig.attr.get('restrain_numbering')
        side = self.rig.attr.get('side')

        control_name = ramen_util.get_control_name(rig_description, description, side, sub, not restrain_numbering)

        control_name = control_name.replace('__', '_')

        return control_name

    def get_joint_description(self, joint_name):
        joint_token = self.rig.attr.get('joint_token')[0]
        ramen_util.get_joint_description(joint_name, joint_token)

    def is_valid(self):
        return False

    def set_rig_class(self, rig_class_instance):
        self.rig = rig_class_instance

    def set_node_position(self, position_x, position_y):
        return

    def load(self):
        util.show('\t\tLoad Platform Rig: %s %s' % (self.__class__.__name__, self.rig.uuid))

    def build(self):
        util.show('\t\tBuild Platform Rig: %s %s' % (self.__class__.__name__, self.rig.uuid))

    def unbuild(self):
        pass

    def is_built(self):
        return

    def delete(self):
        pass

