# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

import re
import string

import vtool.util

if vtool.util.is_in_maya():
    import maya.cmds as cmds
    import maya.mel as mel
    
import core
import attr

#--- Nucleus

def create_nucleus(name = None):
    """
    Create a nucleus node.
    
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
    
    if switch_control:
        
        blendshape_node = cmds.blendShape(curve, new_curve, blend_curve, w = [0,1],n = 'blendShape_%s' % follicle)[0]
        
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
    
    return nodes
    