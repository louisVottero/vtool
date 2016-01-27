# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

import re
import string

import vtool.util

if vtool.util.is_in_maya():
    import maya.cmds as cmds
    import maya.mel as mel
    
import core
import attr
import deform

#--- Nucleus

def create_nucleus(name = None):
    """
    Create a nucleus node.
    I've had cases where Maya insists on creating nucleus1 instead of using the last created nucleus.  This can be fixed by restarting Maya.
    
    Args
        name (str): The description for the nucleus. Final name = 'nucleus_(name)'. If no name given, name = 'nucleus'.
    
    Return 
        str: name of the nucleus.
    """
    if name:
        name = 'nucleus_%s' % name
    if not name:
        name = 'nucleus'
        
    nucleus = cmds.createNode('nucleus', name = name)
    mel.eval('global string $gActiveNucleusNode;$gActiveNucleusNode = "%s";' % nucleus)
    cmds.connectAttr('time1.outTime', '%s.currentTime' % nucleus)
    
    cmds.setAttr('%s.spaceScale' % nucleus, 0.01)
    
    return nucleus
    
#--- Hair

def create_hair_system(name = None, nucleus = None):
    """
    Create a hair system.  
    
    Args
        name (str): The description for the hair system. Final name = 'hairSystem_(name)'. If no name given, name = 'hairSystem'.  
        nucleus (str): The name of a nucleus node to attach to the hairSystem.
        
    Return
        list: [hair system, hair system shape] 
    """
    if name:
        name = 'hairSystem_%s' % name
    if not name:
        name = 'hairSystem'
    
    hair_system_shape = cmds.createNode('hairSystem')
    hair_system = cmds.listRelatives(hair_system_shape, p = True)
    
    hair_system = cmds.rename(hair_system, core.inc_name(name) )
    hair_system_shape = cmds.listRelatives(hair_system, shapes = True)[0]
    
    cmds.connectAttr('time1.outTime', '%s.currentTime' % hair_system_shape)
    
    if nucleus:
        connect_hair_to_nucleus(hair_system, nucleus)
    
    return hair_system, hair_system_shape

def connect_hair_to_nucleus(hair_system, nucleus):
    """
    Connect a hair system to a nucleus.
    
    Args
        hair_system (str): The name of a hair system.
        nucleus (str): The name of a nucleus node.
    """
    hair_system_shape = cmds.listRelatives(hair_system, shapes = True)[0]
    
    cmds.connectAttr('%s.startFrame' % nucleus, '%s.startFrame' % hair_system_shape)
    
    indices = attr.get_indices('%s.inputActive' % nucleus)
    
    if indices:
        current_index = indices[-1] + 1
    
    if not indices:
        current_index = 0
    
    cmds.connectAttr('%s.currentState' % hair_system_shape, '%s.inputActive[%s]' % (nucleus, current_index))
        
    cmds.connectAttr('%s.startState' % hair_system_shape, '%s.inputActiveStart[%s]' % (nucleus, current_index))
    cmds.connectAttr('%s.outputObjects[%s]' % (nucleus, current_index), '%s.nextState' % hair_system_shape)
    
    cmds.setAttr('%s.active' % hair_system_shape, 1)
    
    cmds.refresh()

def create_follicle(name = None, hair_system = None):
    """
    Create a follicle.
    
    Args 
        name (str): The description for the hair system. Final name = 'follicle_(name)'. If no name given, name = 'follicle'.
        hair_system (str): The name of a hair system to connect to.
        
    Return
        list: [follicle name, follicle shape name]
    """
    
    if name:
        name = 'follicle_%s' % name
    if not name:
        name = 'follicle'
    
    follicle_shape = cmds.createNode('follicle')
    follicle = cmds.listRelatives(follicle_shape, p = True)
    
    follicle = cmds.rename(follicle, core.inc_name(name))
    follicle_shape = cmds.listRelatives(follicle, shapes = True)[0]
    
    cmds.setAttr('%s.startDirection' % follicle_shape, 1)
    cmds.setAttr('%s.restPose' % follicle_shape, 1)
    cmds.setAttr('%s.degree' % follicle_shape, 3)
    
    if hair_system:
        connect_follicle_to_hair(follicle, hair_system)
            
    return follicle, follicle_shape    
        
def connect_follicle_to_hair(follicle, hair_system):
    """
    Connect a follicle to a hair system
    
    Args
        follicle (str): The name of a follicle.
        hair_system (str): The name of a hair system.
    """
    
    
    indices = attr.get_indices('%s.inputHair' % hair_system)
    
    if indices:
        current_index = indices[-1] + 1
    
    if not indices:
        current_index = 0
    
    cmds.connectAttr('%s.outHair' % follicle, '%s.inputHair[%s]' % (hair_system, current_index))
    indices = attr.get_indices('%s.inputHair' % hair_system)
    
    cmds.connectAttr('%s.outputHair[%s]' % (hair_system, current_index), '%s.currentPosition' % follicle)
    
    cmds.refresh()
    
def add_follicle_to_curve(curve, hair_system = None, switch_control = None, attribute_name = 'dynamic'):
    """
    Add a follicle to a curve. Good for attaching to a spline ik, to make it dynamic.
    It will make a duplicate of the curve so that the dynamics of the follicle can be switched on/off.
    
    Args
        curve (str): The name of a curve.
        hair_system(str): The name of a hair system, that the created follicle should attach to.
        switch_control (str): The name of the control to add the switch attribute to.
        attribute_name (str): The name of the attribute on switch_control.
        
    Return
        str: The name of the follicle.
        
    """
    parent = cmds.listRelatives(curve, p = True)
    
    follicle, follicle_shape = create_follicle(curve, hair_system)
    
    cmds.connectAttr('%s.worldMatrix' % curve, '%s.startPositionMatrix' % follicle_shape)
    cmds.connectAttr('%s.local' % curve, '%s.startPosition' % follicle_shape)
    
    new_curve_shape = cmds.createNode('nurbsCurve')
    new_curve = cmds.listRelatives(new_curve_shape, p = True)
    
    new_curve = cmds.rename(new_curve, core.inc_name('curve_%s' % follicle))
    new_curve_shape = cmds.listRelatives(new_curve, shapes = True)[0]
    
    cmds.setAttr('%s.inheritsTransform' % new_curve, 0)
    
    cmds.parent(curve, new_curve, follicle)
    cmds.hide(curve)
    
    cmds.connectAttr('%s.outCurve' % follicle, '%s.create' % new_curve)
    
    blend_curve= cmds.duplicate(new_curve, n = 'blend_%s' % curve)[0]
    
    outputs = attr.get_attribute_outputs('%s.worldSpace' % curve)
    
    if outputs:
        for output in outputs:
            cmds.connectAttr('%s.worldSpace' % blend_curve, output, f = True)
    
    if parent:
        cmds.parent(follicle, parent)
    
    blendshape_node = cmds.blendShape(curve, new_curve, blend_curve, w = [0,1],n = 'blendShape_%s' % follicle)[0]
    
    if switch_control:
        
        
        
        remap = attr.RemapAttributesToAttribute(switch_control, attribute_name)
        remap.create_attributes(blendshape_node, [curve, new_curve])
        remap.create()
        """
        variable = MayaNumberVariable('attract')
        variable.set_variable_type(variable.TYPE_FLOAT)
        variable.set_node(switch_control)
        variable.set_min_value(0)
        variable.set_max_value(1)
        variable.set_keyable(True)
        variable.create()
    
        variable.connect_out('%s.inputAttract' % follicle)
        """
    return follicle

    
#--- Cloth

def add_passive_collider_to_mesh(mesh):
    """
    Make mesh into a passive collider.
    
    Args
        mesh (str)
        
    Return
        list: List of nodes in the passive collider.
    """
    cmds.select(mesh, r = True)
    nodes = mel.eval('makeCollideNCloth;')
    
    parent = cmds.listRelatives(nodes[0], p = True)
    parent = cmds.rename(parent, 'passive_%s' % mesh)
    
    return [parent]
    
def add_passive_collider_to_duplicate_mesh(mesh):
    duplicate = cmds.duplicate(mesh, n = 'collide_%s' % mesh )[0]
    
    cmds.parent(duplicate, w = True)
    
    nodes = add_passive_collider_to_mesh(duplicate)
    cmds.setAttr('%s.thickness' % nodes[0], .02)
    nodes.append(duplicate)
    
    cmds.blendShape(mesh, duplicate, w = [0,1], n = 'blendShape_collide_%s' % mesh)
    
    return nodes 

def add_nCloth_to_mesh(mesh):
    cmds.select(mesh, r = True)
    
    nodes = mel.eval('createNCloth 0;')
    
    parent = cmds.listRelatives(nodes[0], p = True)
    parent = cmds.rename(parent, 'nCloth_%s' % mesh)
    
    cmds.setAttr('%s.thickness' % parent, 0.02)
    
    return [parent]

def nConstrain_to_mesh(verts, mesh, name = None, force_passive = False,):
    """
    
    Constrain an ncloth to a passive collider.
    
    Args
        verts (list): The list of verts to constrain on an nCloth mesh.
        mesh (str): The name of a mesh to constrain to.
        force_passive (bool): Wether to make mesh into a passive collider.
    """
    
    nodes1 = []
    
    if force_passive:
        nodes1 = add_passive_collider_to_mesh(mesh)
        cmds.setAttr('%s.collide' % nodes1[0], 0)
    
    cmds.select(cl = True)
    
    cmds.select(verts, mesh)
    nodes = mel.eval('createNConstraint pointToSurface 0;')
    
    if name:
        
        parent = cmds.listRelatives(nodes[0], p = True)[0]
        nodes = cmds.rename(parent, 'dynamicConstraint_%s' % name)
        nodes = vtool.util.convert_to_sequence(nodes)
    
    return nodes + nodes1

def create_cloth_input_meshes(deform_mesh, cloth_mesh, parent, attribute):
    
    final = cmds.duplicate(deform_mesh)[0]
    final = cmds.rename(final, 'temp')
    
    clothwrap = cmds.duplicate(deform_mesh)[0]
    
    deform_mesh_orig = deform_mesh
    deform_mesh = core.prefix_hierarchy(deform_mesh, 'deform')[0]
    
    clothwrap = cmds.rename(clothwrap, deform_mesh)
    
    clothwrap = core.prefix_hierarchy(clothwrap, 'clothwrap')[0]    

    final = cmds.rename(final, deform_mesh_orig)

    deform_mesh = deform_mesh.split('|')[-1]
    clothwrap = clothwrap.split('|')[-1]
    
    deform.create_wrap(deform_mesh, cloth_mesh)
    deform.create_wrap(cloth_mesh, clothwrap)
    
    blend = cmds.blendShape(deform_mesh, clothwrap, final, w = [0,1], n = 'blendShape_nClothFinal')[0]
    
    attr.connect_equal_condition(attribute, '%s.%s' % (blend, deform_mesh), 0)
    attr.connect_equal_condition(attribute, '%s.%s' % (blend, clothwrap), 1)
    
    cmds.parent(deform_mesh , clothwrap, parent )
    
    nodes = add_nCloth_to_mesh(cloth_mesh)
    
    return nodes

#--- cMuscle

class CMuscle(object):
    def __init__(self, muscle):
        self.muscle = muscle
        self.description = None
        
        if not cmds.objExists('%s.description' % self.muscle):
            cmds.addAttr(self.muscle, ln = 'description', dt = 'maya_util')
        
    def _get_control_data_indices(self):
        muscle_creator = self._get_muscle_creator()
        return attr.get_indices('%s.controlData' % muscle_creator)
    
    def _get_attach_data_indices(self):
        muscle_creator = self._get_muscle_creator()
        return attr.get_indices('%s.attachData' % muscle_creator)
            
    def _get_parent(self):
        rels = cmds.listRelatives(self.muscle, p = True)
        return rels[0]
        
    def _get_muscle_creator(self):
        return attr.get_attribute_input('%s.create' % self.muscle, True)
        
    def _get_muscle_shapes(self):
        
        shapes = core.get_shapes(self.muscle)
        
        deformer = None
        nurbs = None
        
def convert_to_bone():
    pass
        for shape in shapes:
            if cmds.nodeType(shape) == 'cMuscleObject':
                deformer = shape
            if cmds.nodeType(shape) == 'nurbsSurface':
                nurbs = shape
                
        return nurbs, deformer
    
    def _rename_controls(self, name):
        name_upper = name[0].upper() + name[1:]
        indices = self._get_control_data_indices()
        count = len(indices)
        
        muscle_creator = self._get_muscle_creator()
        
        last_xform = None
        
        for inc in range(0, count):
            
            input_value = attr.get_attribute_input('%s.controlData[%s].insertMatrix' % (muscle_creator, inc), True)

            input_drive = cmds.listRelatives(input_value, p = True)[0]
            input_xform = cmds.listRelatives(input_drive, p = True)[0]

            input_stretch = attr.get_attribute_input('%s.controlData[%s].curveSt' % (muscle_creator, inc), True)
            input_squash = attr.get_attribute_input('%s.controlData[%s].curveSq' % (muscle_creator, inc), True)
            input_rest = attr.get_attribute_input('%s.controlData[%s].curveRest' % (muscle_creator, inc), True)

            cmds.delete(input_stretch, input_squash, input_rest, ch = True)

            if inc == 0:
                cmds.rename(input_value, core.inc_name('startParent_%s' % name))
                
            if inc == count-1:
                cmds.rename(input_value, core.inc_name('endParent_%s' % name))

            if inc > 0 and inc < count-1:
                input_value = cmds.rename(input_value, core.inc_name('ctrl_%s_%s' % (inc, name)))
                shape = core.get_shapes(input_value)
                cmds.rename(shape, '%sShape' % input_value)
                
                input_stretch = cmds.listRelatives(input_stretch, p = True)[0]
                input_squash = cmds.listRelatives(input_squash, p = True)[0]
                input_rest = cmds.listRelatives(input_rest, p = True)[0]
                
                cmds.rename(input_stretch, core.inc_name('ctrl_%s_stretch%s' % (inc, name_upper)))
                cmds.rename(input_squash, core.inc_name('ctrl_%s_squash%s' % (inc, name_upper)))
                cmds.rename(input_rest, core.inc_name('ctrl_%s_rest%s' % (inc, name_upper)))
                
                cmds.rename(input_drive, 'drive_%s' % input_value)
                input_xform = cmds.rename(input_xform, 'xform_%s' % input_value)
                
                last_xform = input_xform
                
        parent = cmds.listRelatives(last_xform, p = True)[0]
        cmds.rename(parent, core.inc_name('controls_cMuscle%s' % name_upper))
                
    def _rename_attach_controls(self, name):
        indices = self._get_attach_data_indices()
        count = len(indices)
        
        muscle_creator = self._get_muscle_creator()
        last_xform = None
        
        for inc in range(0, count):
            
            name_upper = name[0].upper() + name[1:]

            input_value = attr.get_attribute_input('%s.attachData[%s].attachMatrix' % (muscle_creator, inc), True)

            input_drive = cmds.listRelatives(input_value, p = True)[0]
            input_xform = cmds.listRelatives(input_drive, p = True)[0]
            
            
            
            input_stretch = attr.get_attribute_input('%s.attachData[%s].attachMatrixSt' % (muscle_creator, inc), True)
            input_squash = attr.get_attribute_input('%s.attachData[%s].attachMatrixSq' % (muscle_creator, inc), True)
                        
            input_value = cmds.rename(input_value, core.inc_name('ctrl_%s_attach%s' % (inc+1, name_upper)))
            cmds.rename(input_stretch, core.inc_name('ctrl_%s_attachStretch%s' % (inc+1, name_upper)))
            cmds.rename(input_squash, core.inc_name('ctrl_%s_attachSquash%s' % (inc+1, name_upper)))
            
            cmds.rename(input_drive, 'drive_%s' % input_value)
            input_xform = cmds.rename(input_xform, 'xform_%s' % input_value)
            last_xform = input_xform
            
        parent = cmds.listRelatives(last_xform, p = True)[0]
        cmds.rename(parent, core.inc_name('attach_cMuscle%s' % name_upper))           
            
    def _rename_locators(self, name):
        
        muscle_creator = self._get_muscle_creator()

        input_start_A = attr.get_attribute_input('%s.startPointA' % muscle_creator, True)
        input_start_B = attr.get_attribute_input('%s.startPointB' % muscle_creator, True)
        input_end_A = attr.get_attribute_input('%s.endPointA' % muscle_creator, True)
        input_end_B = attr.get_attribute_input('%s.endPointB' % muscle_creator, True)
        
        cmds.rename(input_start_A, core.inc_name('locatorStart1_%s' % name))
        cmds.rename(input_start_B, core.inc_name('locatorStart2_%s' % name))
        cmds.rename(input_end_A, core.inc_name('locatorEnd1_%s' % name))
        cmds.rename(input_end_B, core.inc_name('locatorEnd2_%s' % name))
        
    
    def rename(self, name):
        
        nurbsSurface, muscle_object = self._get_muscle_shapes()
        muscle_creator = self._get_muscle_creator()
        
        self.muscle = cmds.rename(self.muscle, core.inc_name('cMuscle_%s' % name))
        
        if cmds.objExists(nurbsSurface):
            cmds.rename(nurbsSurface, core.inc_name('%sShape' % self.muscle))
        
        cmds.rename(muscle_object, core.inc_name('cMuscleObject_%sShape' % name))
        cmds.rename(muscle_creator, core.inc_name('cMuscleCreator_%s' % name))
        
        parent = self._get_parent()
        
        cmds.rename(parent, core.inc_name('cMuscle_%s_grp' % name))
        
        self._rename_controls(name)
        self._rename_attach_controls(name)
        self._rename_locators(name)
        
        self.description = name
        cmds.setAttr('%s.description' % self.muscle, name, type = 'maya_util')
        
    def create_attributes(self, node = None):
        
        if not node:
            node = self.muscle
        
        muscle_creator = self._get_muscle_creator()
        
        description = cmds.getAttr('%s.description' % self.muscle)
        
        title = attr.MayaEnumVariable(description.upper())
        title.create(node)
        
        if node == self.muscle:
            cmds.addAttr(node, ln = 'controlVisibility_%s' % description, at = 'bool', k = True )
            cmds.connectAttr('%s.controlVisibility_%s' % (node, description), '%s.showControls' % muscle_creator)
        
        indices = self._get_attach_data_indices()
        count = len(indices)
        
        attributes = ['jiggle', 'jiggleX', 'jiggleY', 'jiggleZ', 'jiggleImpact', 'jiggleImpactStart', 'jiggleImpactStop', 'cycle', 'rest']
        
        for inc in range(0, count):
            current = inc+1
            
            title_name = 'muscle_section_%s' % (current)
            title_name = title_name.upper()
            
            title = attr.MayaEnumVariable(title_name)
            title.create(node)
            
            control = attr.get_attribute_input('%s.controlData[%s].insertMatrix' % (muscle_creator, current), True)
            
            for attribute in attributes:
                other_attribute = '%s_%s' % (attribute, current) 
            
                attribute_value = cmds.getAttr('%s.%s' % (control, attribute))
                cmds.addAttr(node, ln = other_attribute, at = 'double', k = True, dv = attribute_value)    
            
                cmds.connectAttr('%s.%s' % (node, other_attribute), '%s.%s' % (control, attribute))
            
