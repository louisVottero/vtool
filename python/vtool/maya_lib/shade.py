# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

import vtool.util
import api

if vtool.util.is_in_maya():
    import maya.cmds as cmds
    
import core
import attr

def apply_shading_engine(shader_name, mesh):
    """
    Adds the named shading engine to the mesh.
    
    Args
        shader_name (str): Name of an existing shader in maya.
        mesh (str):  Name of a mesh to add the shader to.
    
    """
    
    cmds.sets(mesh, e = True, forceElement = shader_name)
    
def get_shading_engine_geo(shader_name):
    """
    Non implemented
    """
    pass


def get_shading_engines(shader_name):
    """
    Get the shading engines attached to a shader.  
    Maya allows one shader to be attached to more than one engine. 
    Most of the time it is probably just attached to one.
    
    Args
        shader_name (str): The name of the shader.
        
    Return
        (list): A list of attached shading engines by name.
    """
    outputs = attr.get_outputs('%s.outColor' % shader_name, node_only = True)
    
    found = []
    
    for output in outputs:
        if cmds.nodeType(output) == 'shadingEngine':
            found.append(output)
            
    return found

def get_shading_engines_by_geo(geo):
    
    shapes = cmds.listRelatives(geo, children = True, shapes = True)
    
    engines = []
    
    if not shapes:
        return engines
    
    for shape in shapes:
        
        sub_engines = cmds.listConnections(shape, type = 'shadingEngine') 
        
        if sub_engines:
            engines += sub_engines
            
    return engines
    
def has_shading_engine(geo):
    
    engines = get_shading_engines_by_geo(geo)
    
    if engines:
        return True
    
    if not engines:
        return False

def apply_shader(shader_name, mesh):
    """
    Args
        shader_name (str): The name of a shader.
        mesh (str): The name of the mesh to apply the shader to.
        
    """
    
    engines = get_shading_engines(shader_name)
    
    if engines:
        cmds.sets( mesh, e = True, forceElement = engines[0])
    
def apply_new_shader(mesh, type_of_shader = 'blinn', name = ''):
    """
    Create a new shader to be applied to the named mesh.
    
    Args
        mesh (str): The name of the mesh to apply the shader to.
        type_of_shader (str): This corresponds to Maya shader types.  Eg. blinn, lambert, etc.
        name (str): The name to give the shader. If not name given a name will be made up using the type_of_shader.
        
    Return
        (str): The name of the new shader.
    """
    
    
    if name:
        if not cmds.objExists(name):
            material = cmds.shadingNode(type_of_shader, asShader = True, n = name)
        if cmds.objExists(name):
            material = name
    if not name:
        material = cmds.shadingNode(type_of_shader, asShader = True)
    
    shader_set = cmds.sets( renderable = True, 
                    noSurfaceShader = True, 
                    empty = True, 
                    n = '%sSG' % material)
    
    cmds.sets( mesh, e = True, forceElement = shader_set)
    
    cmds.defaultNavigation(connectToExisting = True, 
                           source = material, 
                           destination = shader_set)
    
    #shape = get_mesh_shape(mesh)
    
    return material



def apply_transparent_lambert(mesh):
    """
    Convenience to hide geo via shader.
    
    Args
        mesh (str): Name of the mesh to apply the shader to.
    """
    
    
    name = 'transparent_lambert'
    
    if not cmds.objExists(name):
        lambert = apply_new_shader(mesh, 'lambert', name)
        
        cmds.setAttr('%s.transparencyR' % lambert, 1)
        cmds.setAttr('%s.transparencyG' % lambert, 1)
        cmds.setAttr('%s.transparencyB' % lambert, 1)
        
    if cmds.objExists(name):
        apply_shader(name, mesh)
        
def create_ramp_texture_node(name):
    
    ramp = cmds.createNode('ramp', n = name)

    return ramp

