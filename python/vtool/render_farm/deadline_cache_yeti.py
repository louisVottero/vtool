namespace = ''
name = ''
version = ''
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
    
    cache_dir = os.path.join(os.path.dirname(maya_scene_path), "cache")
    
    create_dir(cache_dir)
    
    cache_dir = os.path.join(cache_dir, "yeti")
    
    create_dir(cache_dir)
    
    return cache_dir

def get_output_dir(yeti_dir):
    
    pass_namespace = namespace
    
    if not namespace:
        pass_namespace = 'default'
        
    output_dir = os.path.join(yeti_dir, pass_namespace)
    create_dir(output_dir)    
    
    return output_dir

def get_file_name(yeti_node):

    parent = cmds.listRelatives(yeti_node, p = True)[0]
    yeti_obj = parent
    yeti_type = yeti_obj
    
    if yeti_obj.find(':') > -1:
        yeti_type = (yeti_obj.split(":"))
        yeti_type = yeti_type[1]    

    output_name = yeti_type    
    
    if version:
        pad_version = str('{0:03d}'.format(int(version)))
        output_name = output_name + '.' + pad_version + '.%04d.fur'
    if not version:
        output_name = output_name + '.%04d.fur'
        
    return output_name

def cache(cache_namespace = None):
    
    if not cache_namespace:
        cache_namespace = namespace
        
    cache_name = 'cache'
    
    yeti_nodes = get_yeti_nodes(cache_namespace)
    yeti_dir = get_yeti_dir()
    
    for yeti_node in yeti_nodes:
        
        cmds.setAttr("%s.fileMode" % yeti_node, 0)
        
        output_dir = get_output_dir(yeti_dir)
        output_name = get_file_name(yeti_node)
        
        
        cache_path = os.path.join(output_dir, output_name)
        
        print 'Caching yeti node: %s   to path: %s' % (yeti_node, cache_path)
        
        if not cmds.pluginInfo('pgYetiMaya', query = True, loaded = True):
            cmds.loadPlugin('pyYetiMaya')
        
        if command:
            exec(command)
        if not command:
            cmds.pgYetiCommand(yeti_node, writeCache=cache_path, range=(1, 100), samples=3)
      
#run cache  
cache()