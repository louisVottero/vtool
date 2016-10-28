namespace = ''
name = ''
command = ''
#above can be replaced with file read/write and submitted to deadline

import maya.cmds as cmds
import os
import sys

def create_dir(directory):
    if not os.path.isdir(directory):
        os.mkdir(directory)

def get_yeti_nodes(namespace):
    
    search_string = '*'
    if namespace:
        search_string = '%s:*' % namespace
    
    return cmds.ls(search_string, type="pgYetiMaya")
    
def get_yeti_dir():
    
    maya_scene_path = os.path.abspath(cmds.file(query=True, sn=True))
    
    yeti_dir = os.path.join(os.path.dirname(maya_scene_path), "yeti_cache")
    
    create_dir(yeti_dir)
    
    return yeti_dir

def get_output_dir(cache_name, yeti_node, yeti_dir):
    
    
    parent = cmds.listRelatives(yeti_node, p = True)[0]
    yeti_obj = parent
    yeti_type = yeti_obj
    
    if yeti_obj.find(':'):
        yeti_type = (yeti_obj.split(":"))
        yeti_type = yeti_type[1]
        
    output_name = name + '_' + yeti_type
    output_dir = os.path.join(yeti_dir, output_name)
    create_dir(output_dir)    
    
    return output_name, output_dir

def cache(cache_namespace = None):
    
    if not cache_namespace:
        cache_namespace = namespace
        
    cache_name = 'cache'
    
    
    yeti_nodes = get_yeti_nodes(cache_namespace)
    yeti_dir = get_yeti_dir()
    
    for yeti_node in yeti_nodes:
        
        cmds.setAttr("%s.fileMode" % yeti_node, 0)
        
        output_name, output_dir = get_output_dir(cache_name, yeti_node, yeti_dir)
        
        cache_path = os.path.join(output_dir, output_name) + ".%04d.fur" #needed for command
        
        print 'Caching yeti node: %s   to path: %s' % (yeti_node, cache_path)
        
        if command:
            exec(command)
        if not command:
            cmds.pgYetiCommand(yeti_node, writeCache=cache_path, range=(1, 100), samples=3)
      
#run cache  
cache()