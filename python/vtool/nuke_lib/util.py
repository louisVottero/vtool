# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

import nuke

"""
import sys
sys.path.append('C:/Users/louis/Dropbox/code/python')

import vtool.nuke_lib.util as util
reload(util)

util.create_color_breakout()
"""

def create_nuke_read(filepath, name, start = 0, end = 0):

    node = nuke.nodes.Read(file = filepath)
    node.setName(name)
    
    node['first'].setValue(start)
    node['last'].setValue(end)
    node['origfirst'].setValue(start)
    node['origlast'].setValue(end)
    node['format'].setValue('HD')    
    
    return node
  
def create_nuke_write(filepath, name):
    
    node = nuke.nodes.Write(file = filepath)
    node.setName(name)
    node['file'].setValue(filepath)
    
    
    return node

def create_color_breakout():

    selected_node = nuke.selectedNode()
    selected_node_name = selected_node.name()
    if selected_node_name.startswith('Read'):
        description = selected_node_name[5:]

    reformat = create_node('Reformat', selected_node)
    offset(0, 200, reformat)

    dot_main = create_node('Dot', reformat)
    offset(0, 100, dot_main)
    
    last_parent = dot_main
    
    passes = ['materialID', 'multimatte', 'velocity', 'normals']
    
    for inc in range(0, 4):
        shuffle = create_shuffle(passes[inc], last_parent)
        
        dot = add_dot_offset(shuffle, 200, 0)
                
        last_parent = dot
        
    shuffle = create_shuffle('specular', dot_main)
    
    spec_dot = add_dot_offset(shuffle, 0, 600)
    
    last_merge = specular_pass(shuffle)
    first_merge = last_merge
    
    left_shuffles = ['reflect', 'ao', 'lighting', 'GI']
    right_shuffles = ['matteShadow','fallOff','refract','yDepth', 'zDepth']

    last_parent = spec_dot

    for inc in range(0, len(left_shuffles)):
        shuffle = create_shuffle(left_shuffles[inc], last_parent)
        
        dot = add_dot_offset(shuffle, -400, 0)
        
        if left_shuffles[inc] == 'reflect':
            merge = reflect_pass(shuffle)
        if left_shuffles[inc] == 'ao':
            merge = ao_pass(shuffle)
        if left_shuffles[inc] == 'lighting':
            merge = lighting_pass(shuffle)
        if left_shuffles[inc] == 'GI':
            merge = lighting_pass(shuffle)
            merge = convert(merge, 'Dot')
        
            
        last_merge.setInput(1, merge)
        last_merge = merge
                    
        last_parent = dot
    
    last_parent = spec_dot
    last_merge = first_merge
    
    for inc in range(0, len(right_shuffles)):
        shuffle = create_shuffle(right_shuffles[inc], last_parent)
        
        dot = add_dot_offset(shuffle, 400, 0)
               
        if right_shuffles[inc] == 'matteShadow':
            merge = matteShadow_pass(shuffle)
            
        if right_shuffles[inc] == 'fallOff':
            merge = fallOff_pass(shuffle)
        if right_shuffles[inc] == 'refract':
            merge = refract_pass(shuffle)
        if right_shuffles[inc] == 'yDepth':
            merge = ydepth_pass(shuffle)
        if right_shuffles[inc] == 'zDepth':
            merge = zdepth_pass(shuffle)
        
        if merge:    
            merge.setInput(1, last_merge)
            last_merge = merge
        
        last_parent = dot
        
    
    
def create_node(node_type, parent = None):
    
    node = eval('nuke.nodes.%s()' % node_type)
     
    if parent:
        match_space(parent, node)
        node.setInput(0, parent)
    
    
    return node

def create_shuffle(in_pass, parent = None):
    shuffle = create_node('Shuffle', parent)
    
    shuffle['postage_stamp'].setValue(1)
    shuffle['in'].setValue(in_pass)
    shuffle['label'].setValue(in_pass)
    
    return shuffle
      
def add_dot_offset(child, offset_x, offset_y):
    
    parent = child.input(0)
        
    dot = create_node('Dot', parent)
    offset(offset_x, offset_y, dot)
    
    match_space(dot, child)
    offset(0, 100, child)
    child.setInput(0, dot)
    
    
    
    return dot

def align_x(source_node, target_node):
    
    x = source_node.xpos()
        
    width = source_node.screenWidth()
        
    center_x = x + width/2
    
    tx = target_node.xpos()
    
    other_width = target_node.screenWidth()
    
    target_node.setXpos( center_x - other_width/2)    

def align_y(source_node, target_node):
    
    y = source_node.ypos()
    
    height = source_node.screenHeight()
    
    center_y = y + height/2
    
    ty = target_node.ypos()
    
    other_height = target_node.screenHeight()
    
    print ty, other_height
    
    y_value = center_y - (other_height/2)
    
    target_node.setYpos( y_value )

def match_space(source_node, target_node):
    
    x = source_node.xpos()
    y = source_node.ypos()
    
    width = source_node.screenWidth()
    height = source_node.screenHeight()
    
    center_x = x + width/2
    center_y = y + height/2
    
    tx = target_node.xpos()
    ty = target_node.ypos()
    
    other_width = target_node.screenWidth()
    other_height = target_node.screenHeight()
    
    target_node.setXpos( center_x - other_width/2)
    target_node.setYpos( center_y - other_height/2)
    
def offset(x_offset, y_offset, node):
    
    x = node.xpos()
    y = node.ypos()
    
    node.setXpos(x_offset + x)
    node.setYpos(y_offset + y)

def insert(node1, node2, insert_node):
    
    insert_node.setInput(0, node1)
    node2.setInput(0, insert_node)
    
    match_space(node1, insert_node)
    
def convert(node, node_type):
    
    input_count = node.inputs()

    new_node = create_node(node_type)
    
    for inc in range(0, input_count):
        
        input_node = node.input(inc)
        
        new_node.setInput(inc, input_node)
        
        match_space(node, new_node)
        
        dependencies = node.dependencies()
        
        nuke.delete(node)
        
        for depend in dependencies:
            depend.connectInput(0, new_node)
            
    return new_node
            
            
        
    
    
    
#--- pass breakouts
        
def specular_pass(shuffle):
    
    pass_name = shuffle['in'].value()
    
    Merge = create_node('Merge', shuffle)
    Merge['label'].setValue(pass_name)
    offset(0, 1000, Merge)
    
    Unpremult = create_node('Unpremult')
    insert(shuffle, Merge, Unpremult)
    offset(0, 100, Unpremult)
    
    Multiply = create_node('Multiply')
    insert(Unpremult, Merge, Multiply)
    offset(0, 700, Multiply)
    Multiply['value'].setValue( 0.54 )
    
    Clamp = create_node('Clamp')
    insert(Unpremult, Multiply, Clamp)
    offset(0, 100, Clamp)    
    
    return Merge
    
def reflect_pass(shuffle):
    
    pass_name = shuffle['in'].value()
    
    Merge = create_node('Merge', shuffle)
    Merge['label'].setValue(pass_name)
    offset(0, 1000, Merge)
    
    Unpremult = create_node('Unpremult')
    insert(shuffle, Merge, Unpremult)
    offset(0, 100, Unpremult)
    
    grade = create_node('Grade')
    insert(Unpremult, Merge, grade)
    offset(0,400, grade)
    return Merge

def ao_pass(shuffle):
    
    pass_name = shuffle['in'].value()
    
    Merge = create_node('Merge', shuffle)
    Merge['label'].setValue(pass_name)
    offset(0, 1000, Merge)
    
    invert = create_node('Invert')
    insert(shuffle, Merge, invert)
    offset(0, 500, invert)
    
    multiply = create_node('Multiply')
    insert(invert, Merge, multiply)
    offset(0,400, multiply)
    
    multiply['value'].setValue(1.58)
    
    return Merge

def lighting_pass(shuffle):
    
    pass_name = shuffle['in'].value()
    
    Merge = create_node('Merge', shuffle)
    Merge['label'].setValue(pass_name)
    offset(0, 1000, Merge)
    
    unpremult = create_node('Unpremult')
    insert(shuffle, Merge, unpremult)
    offset(0, 100, unpremult)
    
    grade = create_node('Grade')
    insert(unpremult, Merge, grade)
    offset(0,400, grade)
    
    return Merge

def matteShadow_pass(shuffle):
    
    pass_name = shuffle['in'].value()
    
    grade = create_node('Grade', shuffle)
    grade['label'].setValue(pass_name)
    offset(0, 1000, grade)
    
    shuffle2 = create_node('Shuffle')
    insert(shuffle, grade, shuffle2)
    offset(0, 100, shuffle2) 
    
    return grade

def fallOff_pass(shuffle):
    
    pass_name = shuffle['in'].value()
    
    dot_parent = shuffle.input(0)
    dot_grand_parent = dot_parent.input(0)
    
    grade = create_node('Grade', shuffle)
    grade['label'].setValue(pass_name)
    offset(0, 1000, grade)
    
    dot = create_node('Dot')
    insert(dot_grand_parent, dot_parent, dot)
    offset(200, 0, dot)
    
    copy = create_node('Copy')
    insert(shuffle, grade, copy)
    offset(0, 100, copy)
    
    dot2 = create_node('Dot', dot)    
    copy.setInput(1, dot2)
    offset(0,206, dot2)
    
    
    merge = create_node('Merge', copy)
    insert(copy, grade, merge)
    offset(0, 400, merge)
    
    shuffle2 = create_node('Shuffle', dot2)
    offset(0, 300, shuffle2)
    align_y(merge, shuffle2)
    
    merge.setInput(1, shuffle2)
        
    return grade

def refract_pass(shuffle):
    
    pass_name = shuffle['in'].value()
    
    merge = create_node('Merge', shuffle)
    merge['label'].setValue(pass_name)
    offset(0, 1000, merge)
    
    glow = create_node('Glow')
    insert(shuffle, merge, glow)
    offset(0, 100, glow) 
    
    return merge
    
def ydepth_pass(shuffle):
    
    pass_name = shuffle['in'].value()
    
    dot = create_node('Dot', shuffle)
    dot['label'].setValue(pass_name)
    offset(0, 1300, dot)
    
    transform = create_node('Transform')
    insert(shuffle, dot, transform)
    offset(0, 100, transform)
    
    grade = create_node('Grade')
    insert(transform, dot, grade)
    offset(0, 400, grade)
    
def zdepth_pass(shuffle):
    
    pass_name = shuffle['in'].value()
    
    dot_parent = shuffle.input(0)
    dot_grand_parent = dot_parent.input(0)
    
    dot_parent.setXpos(dot_parent.xpos() + 200)
    shuffle.setXpos(shuffle.xpos() + 200)
    
    grade = create_node('Grade', shuffle)
    offset(0, 100, grade)
    
    dot = create_node('Dot', dot_grand_parent)
    offset(400, 0, dot)
    
    dot_parent.setInput(0, dot)
    
    shuffle = create_node('Shuffle', dot)
    shuffle['label'].setValue(pass_name)
    offset(0, 1100, shuffle)
    
    
    
    return shuffle
    
    