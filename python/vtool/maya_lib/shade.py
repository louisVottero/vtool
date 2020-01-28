# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

import vtool.util
import vtool.util_file
import api

if vtool.util.is_in_maya():
    import maya.cmds as cmds
    
import core
import attr

def apply_shading_engine(shader_name, mesh):
    """
    Adds the named shading engine to the mesh.
    
    Args:
        shader_name (str): Name of an existing shader in maya.
        mesh (str):  Name of a mesh to add the shader to.
    
    """
    
    cmds.sets(mesh, e = True, forceElement = shader_name)
    
def get_shading_engine_geo(shader_name):
    """
    Given a shading engine, get the members
    """
    members = cmds.sets(shader_name, q = True)
    return members



def get_shading_engines(shader_name = None):
    """
    Get the shading engines attached to a shader.  
    Maya allows one shader to be attached to more than one engine. 
    Most of the time it is probably just attached to one.
    
    Args:
        shader_name (str): The name of the shader.
        
    Returns:
        list: A list of attached shading engines by name.
    """
    if shader_name:
        outputs = attr.get_outputs('%s.outColor' % shader_name, node_only = True)
        
        found = []
        
        for output in outputs:
            if cmds.nodeType(output) == 'shadingEngine':
                found.append(output)
                
        return found
    
    if not shader_name:
        return cmds.ls(type = 'shadingEngine')

def get_shading_engines_by_geo(geo):
    
    if not core.is_a_shape(geo):
        shapes = cmds.listRelatives(geo, children = True, shapes = True, f = True)
    if core.is_a_shape(geo):
        shapes = [geo]
    
    engines = []
    
    if not shapes:
        return engines
    
    for shape in shapes:
        
        sub_engines = cmds.listConnections(shape, type = 'shadingEngine') 
        
        if sub_engines:
            engines += sub_engines
    
    found = []
    
    for engine in engines:
        if not engine in found:
            found.append(engine)
    
    return found
    
def get_materials():
    materials = cmds.ls(mat = True)
    
    return materials
    
def has_shading_engine(geo):
    
    engines = get_shading_engines_by_geo(geo)
    
    if engines:
        return True
    
    if not engines:
        return False

def get_shader_info(geo):
    
    shaders = get_shading_engines_by_geo(geo)
    
    shader_dict = {}
    
    if core.is_a_shape(geo):
        geo = cmds.listRelatives(geo, p = True)[0]
    
    for shader in shaders:
        members = cmds.sets(shader, q = True)
    
    
        found_members = []
        
        for member in members:
            if member.startswith(geo):
                found_members.append(member) 
    
        shader_dict[shader] = found_members

    shader_dict['.shader.order'] = shaders
    
    return shader_dict

def set_shader_info(geo, shader_dict):
    
    
    
    shaders = shader_dict.keys()
    
    if shader_dict.has_key('.shader.order'):
        shaders = shader_dict['.shader.order']
    
    for shader in shaders:
        
        if not cmds.objExists(shader):
            continue
        
        shader_geo = shader_dict[shader]
        
        found_meshes = {}
        
        for mesh in shader_geo:
            
            split_mesh = mesh.split('.')
            
            if not found_meshes.has_key(geo):
                geo_name = cmds.ls('%s.f[*]' % geo, flatten = False)
                found_meshes[geo] = geo_name
            
            if len(split_mesh) > 1:
                
                found_meshes[geo].append( '%s.%s' % (geo, split_mesh[1]) )
        
        for key in found_meshes:
            
            cmds.sets( found_meshes[key], e = True, forceElement = shader)
            
            
def remove_shaders(geo):
    
    shaders = get_shading_engines_by_geo(geo)
    
    for shader in shaders:
        cmds.sets(geo, e = True, remove = shader)
    
def delete_all():
    
    mats = get_materials()
    engines = get_shading_engines()
    
    engines.remove('initialParticleSE')
    engines.remove('initialShadingGroup')
    mats.remove('lambert1')
    mats.remove('particleCloud1')
    
    if mats:
        cmds.delete(mats)
    if engines:
        cmds.delete(engines)

def reset():
    
    delete_all()
    apply_shader('lambert1', cmds.ls(type = 'mesh'))

def apply_shader(shader_name, mesh):
    """
    Args:
        shader_name (str): The name of a shader.
        mesh (str): The name of the mesh to apply the shader to.
        
    """
    
    mesh = vtool.util.convert_to_sequence(mesh)
    
    engines = get_shading_engines(shader_name)
        
    if engines:
    
        for m in mesh:
                parent = cmds.listRelatives(m, p = True)
                if not cmds.sets(parent, isMember = engines[0]):
                #if not cmds.sets(engines[0], isMember = m):
                    cmds.sets( parent, e = True, forceElement = engines[0])
                
def apply_new_shader(mesh, type_of_shader = 'blinn', name = ''):
    """
    Create a new shader to be applied to the named mesh.
    
    Args:
        mesh (str): The name of the mesh to apply the shader to.
        type_of_shader (str): This corresponds to Maya shader types.  Eg. blinn, lambert, etc.
        name (str): The name to give the shader. If not name given a name will be made up using the type_of_shader.
        
    Returns:
        str: The name of the new shader.
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
    
    Args:
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
        
def create_texture_ramp(name):
    
    ramp = cmds.createNode('ramp', n = name)

    return ramp

def create_texture_file(name, filepath = ''):
    
    file_node = cmds.createNode('file', n = name)
    
    if filepath:
        
        vtool.util_file.fix_slashes(filepath)
        
        cmds.setAttr('%s.fileTextureName' % file_node, filepath, type = 'string')
    
    return file_node
    

def add_2d_placement(texture_node, name = ''):
    
    node = None
    
    if name:
        node = cmds.createNode('place2dTexture', name = name)
    if not name:
        node = cmds.createNode('place2dTexture')
    
    if not node:
        return
    
    cmds.connectAttr('%s.outUV' % node, '%s.uvCoord' % texture_node)
    cmds.connectAttr('%s.outUvFilterSize' % node, '%s.uvFilterSize' % texture_node)
    cmds.connectAttr('%s.vertexCameraOne' % node, '%s.vertexCameraOne' % texture_node)
    cmds.connectAttr('%s.vertexUvOne' % node, '%s.vertexUvOne' % texture_node)
    cmds.connectAttr('%s.vertexUvTwo' % node, '%s.vertexUvTwo' % texture_node)
    cmds.connectAttr('%s.vertexUvThree' % node, '%s.vertexUvThree' % texture_node)
    cmds.connectAttr('%s.coverage' % node, '%s.coverage' % texture_node)
    cmds.connectAttr('%s.mirrorU' % node, '%s.mirrorU' % texture_node)
    cmds.connectAttr('%s.mirrorV' % node, '%s.mirrorV' % texture_node)
    cmds.connectAttr('%s.noiseUV' % node, '%s.noiseUV' % texture_node)
    cmds.connectAttr('%s.offset' % node, '%s.offset' % texture_node)
    cmds.connectAttr('%s.repeatUV' % node, '%s.repeatUV' % texture_node)
    cmds.connectAttr('%s.rotateFrame' % node, '%s.rotateFrame' % texture_node)
    cmds.connectAttr('%s.rotateUV' % node, '%s.rotateUV' % texture_node)
    cmds.connectAttr('%s.stagger' % node, '%s.stagger' % texture_node)
    cmds.connectAttr('%s.translateFrame' % node, '%s.translateFrame' % texture_node)
    cmds.connectAttr('%s.wrapU' % node, '%s.wrapU' % texture_node)
    cmds.connectAttr('%s.wrapV' % node, '%s.wrapV' % texture_node)
    
    return node

