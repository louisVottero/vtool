# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

import vtool.util
import api

if vtool.util.is_in_maya():
    import maya.cmds as cmds
    
import core
import attr

def bake_to_animation(nodes, min_time = None, max_time = None):
    """
    bake the animation with nice settings that fix flipping
    """
    if not min_time or not max_time:
        min_time, max_time = get_min_max_time()
    
    
    cmds.bakeResults( nodes, simulation = True,
                      t = (min_time, max_time),
                      sampleBy = 1,
                      oversamplingRate = 1,
                      disableImplicitControl = True,
                      preserveOutsideKeys = True,
                      sparseAnimCurveBake = False,
                      removeBakedAttributeFromLayer = False,
                      removeBakedAnimFromLayer = True,
                      bakeOnOverrideLayer = False,
                      minimizeRotation = True,
                      controlPoints = False,
                      shape = False)
    
    cmds.filterCurve(nodes)

def get_min_max_time():
    
    min_value = cmds.playbackOptions(query = True, minTime = True)
    max_value = cmds.playbackOptions(query = True, maxTime = True)    
    
    return min_value,max_value

def set_min_max_time(min_value, max_value):
    
    cmds.playbackOptions(minTime = min_value)
    cmds.playbackOptions(maxTime = max_value)    

def playblast(filename):
    """
    Playblast the viewport to the given filename path.
    
    Args:
        filename (str): This should be the path to a quicktime .mov file.
    """
    
    min_value, max_value = get_min_max_time()
    #min = cmds.playbackOptions(query = True, minTime = True)
    #max = cmds.playbackOptions(query = True, maxTime = True)
    
    sound = core.get_current_audio_node()
    
    frames = []
    
    for inc in range(int(min_value), int((max_value+2)) ):
        frames.append(inc)
    
    if sound:
        cmds.playblast(frame = frames,
                   format = 'qt', 
                   percent = 100, 
                   sound = sound,
                   viewer = True, 
                   showOrnaments = True, 
                   offScreen = True, 
                   compression = 'MPEG4-4 Video', 
                   widthHeight = [1280, 720], 
                   filename = filename, 
                   clearCache = True, 
                   forceOverwrite = True)
        
    if not sound:
        cmds.playblast(frame = frames,
                   format = 'qt', 
                   percent = 100,
                   viewer = True, 
                   showOrnaments = True, 
                   offScreen = True, 
                   compression = 'MPEG4-4 Video', 
                   widthHeight = [1280, 720], 
                   filename = filename, 
                   clearCache = True, 
                   forceOverwrite = True)

def quick_driven_key(source, target, source_values, target_values, infinite = False, tangent_type = 'linear'):
    """
    A convenience for create set driven key frames.
    
    Args:
        source (str): node.attribute to drive target.
        target (str): node.attribute to be driven by source.
        source_values (list): A list of values at the source.
        target_values (list): A list of values at the target.
        infinite (bool): The bool attribute. 
        
    """
    
    #this is a slow way to find the keyframe...
    track_nodes = core.TrackNodes()
    track_nodes.load('animCurve')
    
    if not type(tangent_type) == list:
        tangent_type = [tangent_type, tangent_type] 
    
    for inc in range(0, len(source_values)):
          
        cmds.setDrivenKeyframe(target,cd = source, driverValue = source_values[inc], value = target_values[inc], itt = tangent_type[0], ott = tangent_type[1])
    
    keys = track_nodes.get_delta()
    
    if not keys:
        return
    
    keyframe = keys[0]
    
    function = api.KeyframeFunction(keyframe)
    
    if infinite:
        function.set_pre_infinity(function.linear)
        function.set_post_infinity(function.linear)
         
    if infinite == 'post_only':
        
        function.set_post_infinity(function.linear)
        function.set_pre_infinity(function.constant)    
        
    if infinite == 'pre_only':
            
        function.set_pre_infinity(function.linear)
        function.set_post_infinity(function.constant)
    
    return keyframe

def get_keyframe(node_and_attribute):
    """
    Given an node.attribute return input keyframe
    """
    connection = attr.get_attribute_input(node_and_attribute, True)
    
    if connection:
        
        node_type = cmds.nodeType(connection)
    
        if node_type.find('animCurve') > -1:
            return connection
    
def get_input_keyframes(node, node_only = True):
    """
    Get all keyframes that input into the node.
    
    Args
        node (str): The name of a node to check for keyframes.
        node_only (bool): Whether to return just the keyframe name, or also the keyframe.output attribute.
        
    Return
        list: All of the keyframes connected to the node.
    """
    inputs = attr.get_inputs(node, node_only)

    found = []
    
    if not inputs:
        return found
    
    for input_value in inputs:
        if cmds.nodeType(input_value).startswith('animCurve'):
            found.append(input_value)
            
    return found        

def get_output_keyframes(node):
    """
    Get all keyframes that output from the node.
    
    Args:
        node (str): The name of a node to check for keyframes.
        
    Return
        list: All of the keyframes that the node connects into.
    """    
    
    outputs = attr.get_outputs(node)
    
    found = []
    
    if not outputs:
        return found
    
    for output in outputs:
        
        if cmds.nodeType(output).startswith('animCurve'):
            found.append(output)
            
    return found

def set_infiinity(keyframe, pre = False, post = False):
    """
    Given a keframe set the in and out infinity to linear.
    
    Args:
        keyframe (str): The name of a keyframe.
        pre (bool): Whether to set pre inifinity to linear.
        post (bool): Whether to set post infinity to linear.
        
    Return
        str: The name of the keyframe.
    """
    
    function = api.KeyframeFunction(keyframe)
    
    if post:
        function.set_post_infinity(function.linear)    
        
    if pre:
        function.set_pre_infinity(function.linear)
        
    return keyframe