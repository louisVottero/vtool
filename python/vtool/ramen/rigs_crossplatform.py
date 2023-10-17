# Copyright (C) 2022 Louis Vottero louis.vot@gmail.com    All rights reserved.

from .. import logger
log = logger.get_logger(__name__)

from . import rigs

from vtool import util

in_maya = util.in_maya
in_unreal = util.in_unreal

class Fk(rigs.Rig):
    
    rig_type = rigs.RigType.FK
    rig_description = 'fk'
    
    def _init_variables(self):
        super(Fk, self)._init_variables()
        
        self.attr.add_to_node('FK', '', rigs.AttrType.TITLE)
        self.attr.add_to_node('hierarchy', True, rigs.AttrType.BOOL)
        self.attr.add_to_node('use_joint_name', False, rigs.AttrType.BOOL)
        
    
    def _maya_rig(self):
        from . import rigs_maya
        return rigs_maya.MayaFkRig()
    
    def _unreal_rig(self):
        from . import rigs_unreal
        return rigs_unreal.UnrealFkRig()
    
class Ik(rigs.Rig):
    
    rig_type = rigs.RigType.FK
    rig_description = 'ik'
    
    def _init_variables(self):
        super(Ik, self)._init_variables()
        
        self.attr.add_to_node('IK', '', rigs.AttrType.TITLE)
        #self.attr.add_to_node('hierarchy', True, rigs.AttrType.BOOL)
        #self.attr.add_to_node('use_joint_name', False, rigs.AttrType.BOOL)
        
    
    def _maya_rig(self):
        from . import rigs_maya
        return rigs_maya.MayaIkRig()
    
    def _unreal_rig(self):
        from . import rigs_unreal
        return rigs_unreal.UnrealIkRig()
    
    
"""    
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
"""
"""
def remove_rigs():
    
    rigs = attr.get_vetala_nodes('Rig2')
    
    for rig in rigs:
        
        rig_class = cmds.getAttr('%s.rigType' % rig)
        
        rig_inst = eval('%s("%s")' % (rig_class, rig))
        
        rig_inst.delete()
    
"""