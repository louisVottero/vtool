# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

import vtool.util


if vtool.util.is_in_maya():
    import maya.cmds as cmds
    import maya.mel as mel
    
from vtool import util_file
    
import core
import attr
import deform
import geo
import space
import anim
import shade

if vtool.util.get_maya_version() > 2014:
    import vtool.util_alembic

#--- Cache



def get_cache_folder(name, dirpath = ''):
    if not dirpath:
        dirpath = cmds.file(q = True, sn = True)
        dirpath = util_file.get_dirname(dirpath)
    
    
    
    folder = util_file.create_dir('cache/%s' % name, dirpath)
    
    return folder
    

def export_maya_cache_group(source_group, dirpath = ''):
    
    
    source_meshes = core.get_shapes_in_hierarchy(source_group, shape_type = 'mesh')
    source_curves = core.get_shapes_in_hierarchy(source_group, shape_type = 'nurbsCurve')
    
    sources = source_meshes + source_curves
    
    core.get_basename(source_group, remove_namespace=True)    
    export_maya_cache(sources, source_group, dirpath)
    
    refresh_maya_caches()

def import_maya_cache_group(target_group, dirpath = '', source_group = None):
    
    target_meshes = core.get_shapes_in_hierarchy(target_group, shape_type = 'mesh')
    target_curves = core.get_shapes_in_hierarchy(target_group, shape_type = 'nurbsCurve')
    
    targets = target_meshes + target_curves
    
    source_group_folder = target_group
    
    if source_group:
        namespace = core.get_namespace(source_group)
        source_group_folder = source_group.replace(':', '_')
     
    import_maya_cache(targets, source_group_folder, dirpath, source_namespace=namespace)
    
def export_maya_cache(geo, name = 'maya_cache', dirpath = ''):
    
    vtool.util.convert_to_sequence(geo)
    
    found_shapes = get_shapes_for_cache(geo)
    
    folder = get_cache_folder('maya_cache', dirpath)
    vtool.util.show('Exporting to: %s' % folder)
    
    min_value, max_value = anim.get_min_max_time()
    
    cmds.cacheFile(f=name,format='OneFile', points = found_shapes, dir = folder, ws = True, sch = True, st = min_value, et = max_value)
    
def import_maya_cache(geo, name = 'maya_cache', dirpath = '', source_namespace = None):
    
    folder = get_cache_folder('maya_cache', dirpath)
    vtool.util.show('Importing from: %s' % folder)
    
    #the geo is stored in channelName. channels is the geo in the cache.
    #channels = cmds.cacheFile(fileName = (folder + '/' + name + '.mcx'), q = True, channelName = True)
    
    geo = vtool.util.convert_to_sequence(geo)
    
    found_shapes = get_shapes_for_cache(geo)
    
    for geo_name in found_shapes:
        
        if geo_name.endswith('Deformed') > -1:
            parent = cmds.listRelatives(geo_name, p = True)
            
            if parent:
                parent = parent[0]
            
            split_parent = parent.split(':')
            
            namespace = split_parent[0]
            
            geo_name = namespace + ':' + geo_name[:-8]
        
        found_history_switch = deform.find_deformer_by_type(geo_name, 'historySwitch')
        
        if found_history_switch:
            continue
        
        nice_geo_name = core.remove_namespace_from_string(geo_name)        
        
        deformer = cmds.deformer(geo_name, type = 'historySwitch', n = ('cacheSwitch_%s' % nice_geo_name))
        
        connection = cmds.listConnections(deformer[0] + '.ip[0].ig', p = True )
        cmds.connectAttr( connection[0], deformer[0] + '.ug[0]')
        cmds.setAttr(deformer[0]+ '.playFromCache', 1)
        cmds.getAttr(deformer[0]+ '.op[0]', silent = True)
        cmds.setAttr(deformer[0]+ '.playFromCache', 0)    
        cmds.disconnectAttr(connection[0],  deformer[0]+ '.ug[0]')    
        
        cmds.setAttr(deformer[0] + '.ihi', 0)
        
        channel_name = geo_name
        
        geo_name = nice_geo_name

        if source_namespace:
            channel_name = source_namespace + ':' + geo_name        
        
        cache_file = cmds.cacheFile( attachFile = True, fileName = name, dir = folder, ia = '%s.inp[0]' % deformer[0], channelName = channel_name)
        
        cmds.connectAttr('%s.inRange' % cache_file, '%s.playFromCache' % deformer[0])
        
        cmds.rename(cache_file, 'cacheFile_%s' % nice_geo_name)
        
        
def export_alembic(root_node, name, dirpath = None, auto_sub_folders = True, min_value = None, max_value = None):
    
    root_node = vtool.util.convert_to_sequence(root_node)
    
    if not cmds.pluginInfo('AbcExport', query = True, loaded = True):
        cmds.loadPlugin('AbcExport')
    
    if min_value == None or max_value == None:
        min_value, max_value = anim.get_min_max_time()
    
    if auto_sub_folders:
        folder = get_cache_folder('alembic', dirpath)
    if not auto_sub_folders:
        folder = dirpath
        
    vtool.util.show('Exporting %s to %s' % (name, folder))
    
    filename = '%s/%s.abc' % (folder, name)
    
    
    attr_node_str = ''
    visited_attrs = []
    visited_nodes = []
    
    root_node_str = ''
    
    
    for node in root_node:
        
        
        
        
        if not cmds.objExists(node):
            vtool.util.show('Unable to export %s. It does not exist.' % node)
            continue
        
        #get long path to node
        node_test = cmds.ls(node)
        
        if len(node_test) > 1:
            node = node_test[0]
        
        if node in visited_nodes:
            continue
        
        visited_nodes.append(node)
        
        root_node_str += ("-root " + node + ' ')
        
        user_attrs = cmds.listAttr(node, ud = True)
        if user_attrs:
            for attr in user_attrs:
                
                if attr in visited_attrs:
                    continue
                
                attr_node_str += ('-attr ' + attr + ' ')
                visited_attrs.append(attr)
    
    alembic_command = 'AbcExport -j "-frameRange %s %s -stripNamespaces -uvWrite -worldSpace -writeVisibility -dataFormat ogawa %s %s -file %s";' % (min_value, max_value, root_node_str, attr_node_str, filename)
    
    vtool.util.show('Alembic export: %s' % alembic_command)
    
    mel.eval(alembic_command)
    

def import_alembic(root_node, name, dirpath = None, auto_sub_folders = True):
    
    if not cmds.pluginInfo('AbcImport', query = True, loaded = True):
        cmds.loadPlugin('AbcImport')
    
    if auto_sub_folders:
        folder = get_cache_folder('alembic', dirpath)
    if not auto_sub_folders:
        folder = dirpath
        
    vtool.util.show('Importing %s from: %s' % (name, folder))
    
    filename = '%s/%s.abc' % (folder, name)
    
    top_alembic = vtool.util_alembic.get_top_in(filename)
    
    meshes = vtool.util_alembic.get_all_instances(top_alembic, 'polyMesh')
    #curves = vtool.util_alembic.get_all_instances(top_alembic, 'nurbsCurve')
    
    alembic_node = cmds.createNode('AlembicNode')
    cmds.connectAttr('time1.outTime', '%s.time' % alembic_node)
    
    cmds.setAttr('%s.abc_File' % alembic_node, filename, type = 'string')
    
    #mel.eval('AbcImport -connect %s "%s";' % (root_node, filename))
    
    found_shapes = get_shapes_for_cache(root_node)
    found_geo = []
    
    for geo_name in found_shapes:
        
        for inc in range(0, len(meshes)):
            
            mesh_name = meshes[inc].getName()
            base_mesh = core.get_basename(mesh_name, remove_namespace = True)
            
            if vtool.util_alembic.is_constant(meshes[inc]):
                continue
            
            base_geo = core.get_basename(geo_name, remove_namespace = True)
            
            if base_mesh == base_geo:
                
                found_geo.append(geo_name)
    
    shader_info_dict = {}
    for inc in range(len(found_geo)-1, -1,-1):
        
        geo_name = found_geo[inc]
        
        shader_info = shade.get_shader_info(geo_name)
        
        shade.remove_shaders(geo_name)
        
        cmds.connectAttr('%s.outPolyMesh[%s]' % (alembic_node, inc), '%s.inMesh' % geo_name, force = True)
        
        shader_info_dict[geo_name] = shader_info
        
    for geo in shader_info_dict:
        
        
        shade.set_shader_info(geo, shader_info_dict[geo])
        

def import_alembic_geo(name, dirpath = None, auto_sub_folders = True, namespace = None):

    if not cmds.pluginInfo('AbcImport', query = True, loaded = True):
        cmds.loadPlugin('AbcImport')
        
    if auto_sub_folders:
        folder = get_cache_folder('alembic', dirpath)
    if not auto_sub_folders:
        folder = dirpath
        
    vtool.util.show('Importing %s from: %s' % (name, folder))
    
    cache_group = cmds.group(em = True, n = 'cache_%s' % name)
    
    filename = '%s/%s.abc' % (folder, name)
    cmds.select(cache_group, replace = True)
    
    mel.eval('AbcImport -mode "import" -reparent "%s" "%s"' % (cache_group, filename)) 
    
    if namespace:
        if not cmds.namespace(ex = namespace):
            cmds.namespace(add = namespace)
        
        cmds.rename(cache_group, '%s:%s' % (cache_group, namespace))
            
    
    return cache_group

        
def refresh_maya_caches(maya_caches = []):
    
    maya_caches = vtool.util.convert_to_sequence(maya_caches)
    
    if not maya_caches:
        
        maya_caches = cmds.ls(type = 'cacheFile')
    
    for maya_cache in maya_caches:
        
        cache_name = cmds.getAttr('%s.cacheName' % maya_cache)
        cmds.setAttr('%s.cacheName' % maya_cache, '', type = 'string')
        cmds.setAttr('%s.cacheName' % maya_cache, cache_name, type = 'string')        
        
        cmds.setAttr( maya_cache + '.enable', 0)
        cmds.setAttr( maya_cache + '.enable', 1)
        
    
        
def get_shapes_for_cache(geo):
    
    geo = vtool.util.convert_to_sequence(geo)
            
    children = cmds.listRelatives(geo, ad = True, type = 'transform')
    
    found_shapes = []
    
    if children:
        geo += children
    
    for sub_geo in geo:
        
        mesh_shapes = core.get_shapes(sub_geo, shape_type = 'mesh')
        
        curve_shapes = core.get_shapes(sub_geo, shape_type = 'nurbsCurve')
        
        if mesh_shapes == None:
            mesh_shapes = []
        if curve_shapes == None:
            curve_shapes = []
            
        shapes = mesh_shapes + curve_shapes
    
        for shape in shapes:
            if cmds.getAttr('%s.intermediateObject' % shape):
                continue
            
            found_shape = cmds.ls(shape)
            
            if found_shape and not found_shape[0] in found_shapes:
                found_shapes.append(found_shape[0])
            
    return found_shapes

#--- Nucleus

def create_nucleus(name = None):
    """
    Create a nucleus node.
    I've had cases where Maya insists on creating nucleus1 instead of using the last created nucleus.  This can be fixed by restarting Maya.
    
    Args:
        name (str): The description for the nucleus. Final name = 'nucleus_(name)'. If no name given, name = 'nucleus'.
    
    Returns: 
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
    
    Args:
        name (str): The description for the hair system. Final name = 'hairSystem_(name)'. If no name given, name = 'hairSystem'.  
        nucleus (str): The name of a nucleus node to attach to the hairSystem.
        
    Returns:
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
    
    Args:
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
    

def create_follicle(name = None, hair_system = None, uv = []):
    """
    Create a follicle.
    
    Args: 
        name (str): The description for the hair system. Final name = 'follicle_(name)'. If no name given, name = 'follicle'.
        hair_system (str): The name of a hair system to connect to.
        
    Returns:
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
    
    if uv:
        cmds.setAttr('%s.parameterU' % follicle, uv[0])
        cmds.setAttr('%s.parameterV' % follicle, uv[1])
        
    
    if hair_system:
        connect_follicle_to_hair(follicle, hair_system)
    
    cmds.connectAttr('%s.outTranslate' % follicle_shape, '%s.translate' % follicle)
    cmds.connectAttr('%s.outRotate' % follicle_shape, '%s.rotate' % follicle)
    
    return follicle, follicle_shape    
        
def connect_follicle_to_hair(follicle, hair_system):
    """
    Connect a follicle to a hair system
    
    Args:
        follicle (str): The name of a follicle.
        hair_system (str): The name of a hair system.
    """
    
    
    indices = attr.get_indices('%s.inputHair' % hair_system)
    
    if indices:
        current_index = indices[-1] + 1
    
    if not indices:
        current_index = 0
    
    cmds.connectAttr('%s.outHair' % follicle, '%s.inputHair[%s]' % (hair_system, current_index), f = True)
    indices = attr.get_indices('%s.inputHair' % hair_system)
    
    cmds.connectAttr('%s.outputHair[%s]' % (hair_system, current_index), '%s.currentPosition' % follicle, f = True)
    
    
def make_curve_dynamic(curve, hair_system = None, mesh = None, curve_closest_samples = 10):
    """
    Replace a curve with a dynamic curve in a follicle. Good for attaching to a spline ik, to make it dynamic.
    It will make a duplicate of the curve so that the dynamics of the follicle can be switched on/off.
    
    Args:
        curve (str): The name of a curve.
        hair_system(str): The name of a hair system, that the created follicle should attach to.
        
    Returns:
        str: The name of the follicle.
        
    """
    parent = cmds.listRelatives(curve, p = True)
    
    uv = []
    
    if mesh:
        uv = geo.get_closest_uv_on_mesh_at_curve(mesh, curve, samples = curve_closest_samples)
    
    follicle, follicle_shape = create_follicle(curve, hair_system, uv = uv)
    
    if mesh:
        mesh_shape = geo.get_mesh_shape(mesh, shape_index = 0)
        cmds.connectAttr('%s.worldMatrix' % mesh_shape, '%s.inputWorldMatrix' % follicle_shape )
        cmds.connectAttr('%s.outMesh' % mesh_shape, '%s.inputMesh' % follicle_shape )

    new_curve = cmds.duplicate(curve)[0]
    new_curve = cmds.rename(new_curve, 'input_%s' % curve)
    cmds.hide(new_curve)
    
    if not mesh:
        cmds.setAttr('%s.inheritsTransform' % curve, 0)
    
    cmds.connectAttr('%s.worldMatrix' % new_curve, '%s.startPositionMatrix' % follicle_shape)
    cmds.connectAttr('%s.local' % new_curve, '%s.startPosition' % follicle_shape)
    
    
    cmds.parent(curve, new_curve, follicle)
    
    space.zero_out_pivot(curve)
    cmds.setAttr('%s.inheritsTransform' % curve, 0)
    attr.zero_xform_channels(curve)
    

    cmds.connectAttr('%s.outCurve' % follicle, '%s.create' % curve)
            
    if parent:
        cmds.parent(follicle, parent)
    
    
        
    return follicle

def create_follicle_from_curve(curve, hair_system = None, attach_mesh = None, out_curve_parent = None, dynamic = True):
    
    parent = cmds.listRelatives(curve, p = True)
    
    follicle, follicle_shape = create_follicle(curve, hair_system)
    
    if attach_mesh:
        cmds.connectAttr('%s.outMesh' % attach_mesh, '%s.inputMesh' % follicle_shape)
        cmds.connectAttr('%s.worldMatrix' % attach_mesh, '%s.inputWorldMatrix' % follicle_shape)
        
        #cmds.connectAttr('%s.outTranslate' % follicle_shape, '%s.translate' % follicle )
        #cmds.connectAttr('%s.outRotate' % follicle_shape, '%s.rotate' % follicle )
        
        u,v = geo.get_uv_on_mesh_at_curve_base(attach_mesh, curve)
        
        cmds.setAttr('%s.parameterU' % follicle, u)
        cmds.setAttr('%s.parameterV' % follicle, v)
    
    
    if dynamic:
        start_curve = cmds.duplicate(curve)[0]
        start_curve = cmds.rename(start_curve, 'start_%s' % curve)
        
        sets = cmds.listSets(object = start_curve)
        for set_value in sets:
            cmds.sets(start_curve, remove = set_value)
        
        cmds.connectAttr('%s.worldMatrix' % start_curve, '%s.startPositionMatrix' % follicle_shape)
        cmds.connectAttr('%s.local' % start_curve, '%s.startPosition' % follicle_shape)
            
        new_curve_shape = cmds.createNode('nurbsCurve')
        new_curve = cmds.listRelatives(new_curve_shape, p = True)
        
        new_curve = cmds.rename(new_curve, core.inc_name('curve_%s' % follicle))
        new_curve_shape = cmds.listRelatives(new_curve, shapes = True)[0]
        
        cmds.setAttr('%s.inheritsTransform' % new_curve, 0)
        
        cmds.parent(start_curve, new_curve, follicle)
        cmds.hide(start_curve)
        
        cmds.connectAttr('%s.outCurve' % follicle, '%s.create' % new_curve)
        
                
        if parent:
            cmds.parent(follicle, parent)
            
        if out_curve_parent and cmds.objExists(out_curve_parent):
            new_curve = cmds.rename(new_curve, 'out_%s' % curve)
            cmds.parent(new_curve, out_curve_parent)
            
            space.zero_out_transform_channels(new_curve)
    if not dynamic:
        cmds.parent(curve, follicle)
        
    return follicle

def add_follicle_to_curve(curve, hair_system = None, switch_control = None, attribute_name = 'dynamic', blendshape = True, out_curve_parent = None, attach_mesh = None):
    """
    Add a follicle to a curve. Good for attaching to a spline ik, to make it dynamic.
    It will make a duplicate of the curve so that the dynamics of the follicle can be switched on/off.
    
    Args:
        curve (str): The name of a curve.
        hair_system(str): The name of a hair system, that the created follicle should attach to.
        switch_control (str): The name of the control to add the switch attribute to.
        attribute_name (str): The name of the attribute on switch_control.
        
    Returns:
        str: The name of the follicle.
        
    """
    parent = cmds.listRelatives(curve, p = True)
    
    if attach_mesh:
        
        u,v = geo.get_closest_uv_on_mesh_at_curve(attach_mesh, curve)
        follicle, follicle_shape = create_follicle(curve, hair_system, [u,v])
    else:
        follicle, follicle_shape = create_follicle(curve, hair_system, [0,0])
        
    if attach_mesh:
        cmds.connectAttr('%s.outMesh' % attach_mesh, '%s.inputMesh' % follicle_shape)
        cmds.connectAttr('%s.worldMatrix' % attach_mesh, '%s.inputWorldMatrix' % follicle_shape)
        
    cmds.connectAttr('%s.worldMatrix' % curve, '%s.startPositionMatrix' % follicle_shape)
    cmds.connectAttr('%s.local' % curve, '%s.startPosition' % follicle_shape)
        
    new_curve_shape = cmds.createNode('nurbsCurve')
    new_curve = cmds.listRelatives(new_curve_shape, p = True)
    
    new_curve = cmds.rename(new_curve, core.inc_name('curve_%s' % follicle))
    new_curve_shape = cmds.listRelatives(new_curve, shapes = True)[0]
    
    cmds.setAttr('%s.inheritsTransform' % new_curve, 0)
    
    cmds.parent(curve, new_curve, follicle)
    
    cmds.connectAttr('%s.outCurve' % follicle, '%s.create' % new_curve)
    
    if blendshape:
        
        blend_curve= cmds.duplicate(new_curve, n = 'blend_%s' % curve)[0]
        
        outputs = attr.get_attribute_outputs('%s.worldSpace' % curve)
        
        if outputs:
            for output in outputs:
                cmds.connectAttr('%s.worldSpace' % blend_curve, output, f = True)
                
        blendshape_node = cmds.blendShape(curve, new_curve, blend_curve, w = [0,1],n = 'blendShape_%s' % follicle)[0]
        
        if switch_control:
            
            remap = attr.RemapAttributesToAttribute(switch_control, attribute_name)
            remap.create_attributes(blendshape_node, [curve, new_curve])
            remap.create()
    
        space.zero_out_transform_channels(blend_curve)
    
    space.zero_out_transform_channels(new_curve)
    
            
    if parent:
        cmds.parent(follicle, parent)
        
    if out_curve_parent and cmds.objExists(out_curve_parent):
        new_curve = cmds.rename(new_curve, 'out_%s' % curve)
        cmds.parent(new_curve, out_curve_parent)
        
        
    return follicle

def get_follicle_output_curve(follicle):
    
    return attr.get_outputs('%s.outCurve' % follicle, node_only = True)

def get_follicle_input_curve(follicle):
    input_value = attr.get_inputs('%s.startPosition' % follicle, node_only = True)
    
    if input:
        return input_value[0]

def set_follicle_stiffness_based_on_length(follicle, min_length, max_length, min_stiffness, max_stiffness, damp_scale = 1):
    """
    at min_length, max_stiffness will be set
    at max_length min_stiffness will be set
    inbetween is interpolated
    
    stiffness is achieved by setting the input curve attract
    
    """
    curve = get_follicle_input_curve(follicle)
    
    curve_length = cmds.arclen(curve, ch = False)
    
    cmds.setAttr('%s.overrideDynamics' % follicle, 1)
    
    cmds.setAttr('%s.stiffness' % follicle, 1)
    
    cmds.setAttr('%s.damp' % follicle, 0.5)
    
    weight = vtool.util.remap_value(curve_length, min_length, max_length, 0, 1)
    
    if weight < 0:
        weight = 0
        
    if weight > 1:
        weight = 1
    
    stiffness = vtool.util.lerp(min_stiffness, max_stiffness, weight)
    
    stiffness_weight = vtool.util.remap_value(stiffness, min_stiffness, max_stiffness, 0, 1)
    
    stiffness_weight = 1 - stiffness_weight
    
    cmds.setAttr('%s.startCurveAttract' % follicle, 1)
    
    cmds.setAttr('%s.damp' % follicle, stiffness_weight * damp_scale)
    
    
    
    cmds.setAttr('%s.stiffnessScale[0].stiffnessScale_Position' % follicle, 0)
    cmds.setAttr('%s.stiffnessScale[0].stiffnessScale_FloatValue' % follicle, 1)
    
    cmds.setAttr('%s.stiffnessScale[1].stiffnessScale_Position' % follicle, 1)
    cmds.setAttr('%s.stiffnessScale[1].stiffnessScale_FloatValue' % follicle, stiffness_weight)
    
    cmds.setAttr('%s.attractionScale[0].attractionScale_Position' % follicle, 0)
    cmds.setAttr('%s.attractionScale[0].attractionScale_FloatValue' % follicle, stiffness)
    
    cmds.setAttr('%s.attractionScale[1].attractionScale_Position' % follicle, 1)
    cmds.setAttr('%s.attractionScale[1].attractionScale_FloatValue' % follicle, stiffness/(2 - stiffness_weight))
    
    
#--- Cloth

def add_passive_collider_to_mesh(mesh, nucleus = None):
    """
    Make mesh into a passive collider.
    
    Args:
        mesh (str)
        
    Returns:
        list: List of nodes in the passive collider.
    """
    
    cmds.select(mesh, r = True)
    
    if nucleus:
        set_active_nucleus(nucleus)
    
    nodes = mel.eval('makeCollideNCloth;')
    
    parent = cmds.listRelatives(nodes[0], p = True)
    parent = cmds.rename(parent, 'passive_%s' % mesh)
    
    return [parent]
    
def add_passive_collider_to_duplicate_mesh(mesh):
    duplicate = cmds.duplicate(mesh, n = 'collide_%s' % mesh )[0]
    
    try:
        cmds.parent(duplicate, w = True)
    except:
        pass
    
    cmds.blendShape(mesh, duplicate, w = [0,1], n = 'blendShape_collide_%s' % mesh)
    
    move_node = cmds.polyMoveVertex('%s.vtx[*]' % duplicate,  ch = 1)
    cmds.rename(move_node, 'polyMoveVertex_%s' % duplicate)
    cmds.select(cl = True)
    
    nodes = add_passive_collider_to_mesh(duplicate)
    cmds.setAttr('%s.thickness' % nodes[0], .02)
    
    nodes.append(duplicate)
    
    return nodes 

def add_passive_to_nucleus(passive_mesh, nucleus):
    """
    """
    if not core.is_a_shape(passive_mesh):
        passive_mesh = core.get_shapes(passive_mesh, shape_type = 'mesh', no_intermediate = True)
        
        if passive_mesh:
            passive_mesh = passive_mesh[0]
    
    outs = attr.get_outputs(passive_mesh, node_only = True)
    
    if not outs:
        return
    
    for out in outs:
        
        if not core.is_a_shape(out):
            shapes = core.get_shapes(out)
            if shapes:
                out = shapes[0]
        
        if cmds.nodeType(out) == 'nRigid':
            slot = attr.get_available_slot('%s.inputPassive' % nucleus)
            
            cmds.connectAttr('%s.currentState' % out, '%s.inputPassive[%s]' % (nucleus, slot))
            cmds.connectAttr('%s.startState' % out, '%s.inputPassiveStart[%s]' % (nucleus, slot))
            
 
def add_nCloth_to_mesh(mesh, world = False):
    cmds.select(mesh, r = True)
    
    pass_value = 0
    if world:
        pass_value = 1
    
    nodes = mel.eval('createNCloth %s;' % pass_value)
    
    if world == True:
        output_mesh = attr.get_attribute_outputs('%s.outputMesh' % nodes[0], node_only = True)
        world_mesh = cmds.rename(output_mesh, 'world_%s' % mesh)
        parent = cmds.listRelatives(mesh, p = True)
        if parent:
            cmds.parent(world_mesh, parent[0])
        
    
    if not nodes:
        vtool.util.warning('No ncloth created on %s' % mesh)
        return
    parent = cmds.listRelatives(nodes[0], p = True)
    parent = cmds.rename(parent, 'nCloth_%s' % mesh)
    
    cmds.setAttr('%s.thickness' % parent, 0.02)
    
    return [parent]


def set_active_nucleus(nucleus_name):
    """
    This sets a global variable that is used by maya to know what nucleus to perform commands on.
    """
    
    mel.eval('global string $gActiveNucleusNode;$gActiveNucleusNode = "%s";' % nucleus_name)

def nConstrain_to_mesh(verts, mesh, name = None, force_passive = False,):
    """
    
    Constrain an ncloth to a passive collider.
    
    Args:
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

def nConstrain_verts(verts, name = None, force_passive= False):

    nodes1 = []
    
    cmds.select(cl = True)
    
    cmds.select(verts)
    nodes = mel.eval('createNConstraint pointToPoint 0;')
    
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
            
def add_muscle_to_mesh(mesh):
     
    mesh_shape = geo.get_mesh_shape(mesh, 0)
    
    if not mesh_shape:
        return
    
    mesh_shape_name = core.get_basename(mesh_shape)
    shape = cmds.createNode('cMuscleObject', n = 'cMuscleObject_%s' % mesh_shape_name, p = mesh)
    cmds.hide(shape)
    
    cmds.connectAttr('%s.worldMatrix' % mesh_shape, '%s.worldMatrixStart' % mesh)
    cmds.connectAttr('%s.worldMesh' % mesh_shape, '%s.meshIn' % shape)
    
    cmds.setAttr('%s.draw' % shape, 0)
    
    cmds.setAttr('%s.localPositionX' % shape, k = False, cb = False)
    cmds.setAttr('%s.localPositionY' % shape, k = False, cb = False)
    cmds.setAttr('%s.localPositionZ' % shape, k = False, cb = False)
    cmds.setAttr('%s.localScaleX' % shape, k = False, cb = False)
    cmds.setAttr('%s.localScaleY' % shape, k = False, cb = False)
    cmds.setAttr('%s.localScaleZ' % shape, k = False, cb = False)
    cmds.setAttr('%s.type' % shape, k = False)
    cmds.setAttr('%s.radius' % shape, k = False)
    cmds.setAttr('%s.length' % shape, k = False)
    cmds.setAttr('%s.capsuleAxis' % shape, k = False)
    cmds.setAttr('%s.userScaleX' % shape, k = False)
    cmds.setAttr('%s.userScaleY' % shape, k = False)
    cmds.setAttr('%s.userScaleZ' % shape, k = False)
    cmds.setAttr('%s.nSeg' % shape, k = False)
    cmds.setAttr('%s.nSides' % shape, k = False)
    
    return shape

def add_mesh_to_keep_out(mesh, keep_out):
    
    shapes = core.get_shapes(mesh, 'cMuscleObject')
    
    if shapes:
        shape = shapes[0]
        
    if not shapes:
        shape = add_muscle_to_mesh(mesh)
    
    cmds.connectAttr('%s.muscleData' % shape, '%s.muscleData[0]' % keep_out)
    
def create_keep_out(collide_transform = None, collide_mesh = None, name = None):
    """
    Collide a transform with a mesh.
    It will generate a locator that can be used to drive an aim or an ik, or a set driven key
    
    Args: 
        collide_transform (str): The transform that should collide with the mesh.  This needs to be a point in space, generally at the edge of the object that needs to collide. 
        collide_mesh (str): The mesh that should collide with collide_transform.
        name (str):  the description to give the nodes generated.

    Returns:
        list: [keep_out_node, keep_out_driven_locator]
    """
    
    
    if not name:
        keep_out = cmds.group(em = True, n = core.inc_name('cMuscleKeepOut_1'))
    if name:
        keep_out = cmds.group(em = True, n = core.inc_name(name))
        
    keep_out_shape = cmds.createNode('cMuscleKeepOut', p = keep_out, n = '%sShape' % keep_out)
    
    cmds.connectAttr('%s.worldMatrix' % keep_out, '%s.worldMatrixAim' % keep_out_shape)
    
    locator = cmds.spaceLocator(n = '%s_driven' % keep_out)[0]
    cmds.connectAttr('%s.outTranslateLocal' % keep_out, '%s.translate' % locator)
    
    cmds.parent(locator, keep_out)
    
    
    if collide_transform and cmds.objExists(collide_transform):
        
        space.MatchSpace(collide_transform, keep_out).translation_rotation()
        space.MatchSpace(collide_transform, keep_out).translation_to_rotate_pivot()
    
    if collide_mesh and cmds.objExists(collide_mesh):
        add_mesh_to_keep_out(collide_mesh, keep_out)
    
    return keep_out, locator
    
#--- Yeti

def get_attached_yeti_nodes(mesh):
    
    outputs = attr.get_attribute_outputs('%s.worldMesh' % mesh, True)
    
    if not outputs:
        return
    
    found = []
    
    for output in outputs:
        
        if core.has_shape_of_type(output, 'pgYetiMaya'):
            found.append(output)

    return found

def create_yeti_texture_reference(mesh):
    
    yeti_nodes = get_attached_yeti_nodes(mesh)
    
    if not yeti_nodes:
        vtool.util.warning('Found no yeti nodes.')
        return
    
    new_mesh = geo.create_texture_reference_object(mesh)
    
    for yeti_node in yeti_nodes:
        
        
        
        shapes = core.get_shapes(yeti_node)
        
        if shapes:
            cmds.connectAttr('%s.worldMesh' % new_mesh, '%s.inputGeometry[1]' % shapes[0])
    
    parent = cmds.listRelatives(yeti_nodes[0], p = True)
    if parent:
        cmds.parent(new_mesh, parent[0])
    
    return new_mesh

def set_yeti_guide_rest(curve):
    cmds.pgYetiCommand(curve, saveGuidesRestPosition = True)

#--- Ziva

def get_ziva_geo_names():
    
    z_geo = cmds.ls(type = 'zGeo')
    
    found = []
    
    for geo in z_geo:
        connection = cmds.listConnections('%s.iNeutralMatrix' % geo)
        if connection:
            found.append(connection[0])
            
    return found

def is_ziva_tissue(mesh):
    cmds.select(mesh)
    zTissue = mel.eval('zQuery -type "zTissue"')
    if zTissue:
        return True
    
    return False
    
def is_ziva_bone(mesh):
    cmds.select(mesh)
    zBone = mel.eval('zQuery -type "zBone"')
    if zBone:
        return True
    
    return False

def rename_ziva_nodes_on_mesh(mesh):
    
    mesh = str(mesh)
    
    history = deform.get_history(mesh)
    
    if not history:
        return
    
    for node in history:
        
        if cmds.nodeType(node) == 'zAttachment':
            source = mel.eval('zQuery -as %s' % node)
            target = mel.eval('zQuery -at %s' % node)
            
            if source and target:
                cmds.rename(node, core.inc_name('zAttachment___%s___into___%s' % (source[0], target[0])))
                continue 
        
        if cmds.nodeType(node) == 'zMaterial':
            cmds.rename(node, core.inc_name('zMaterial___%s' % mesh))
            continue
            
        if cmds.nodeType(node) == 'zFiber':
            cmds.rename(node, core.inc_name('zFiber___%s' % mesh))
            continue
            
        if cmds.nodeType(node) == 'zTet':
            cmds.rename(node, core.inc_name('zTet___%s' % mesh))
            continue
      
    cmds.select(mesh)
    zGeo = mel.eval('zQuery -type "zGeo"')
    cmds.rename(zGeo, core.inc_name('zGeo___%s' % mesh))
    
    
    zTissue = mel.eval('zQuery -type "zTissue"')
    if zTissue:
        cmds.rename(zTissue, core.inc_name('zTissue___%s' % mesh))
    
    zBone = mel.eval('zQuery -type "zBone"')
    if zBone:
        cmds.rename(zBone, core.inc_name('zBone___%s' % mesh))
        
def copy_ziva(source_mesh, target_mesh):
        
    history = deform.get_history(source_mesh)
    
    if is_ziva_tissue(source_mesh):
        cmds.select(target_mesh)
        mel.eval('ziva -t')
        
    if is_ziva_bone(source_mesh):
        cmds.select(target_mesh)
        mel.eval('ziva -b')
    
    if not history:
        return
    
    for node in history:
        if cmds.nodeType(node) == 'zAttachment':
            pass
        
        if cmds.nodeType(node) == 'zMaterial':
            cmds.select(target_mesh)
            mel.eval('ziva -m')
            continue
            
        if cmds.nodeType(node) == 'zFiber':
            cmds.select(target_mesh)
            mel.eval('ziva -f')
            continue
            
        if cmds.nodeType(node) == 'zTet':
            continue
        
    rename_ziva_nodes_on_mesh(target_mesh)
    
def find_empty_attachment_targets():
    pass