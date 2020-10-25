import string

import maya.cmds as cmds

from vtool.maya_lib import api as api_old
from vtool.maya_lib import attr
from vtool.maya_lib import core
from vtool import util



def zero_out(transform):

    matrix1 = cmds.getAttr('%s.matrix' % transform)
    matrix2 = cmds.getAttr('%s.offsetParentMatrix' % transform)
    
    offset_matrix = api_old.multiply_matrix(matrix1, matrix2)
    
    cmds.setAttr('%s.offsetParentMatrix' % transform, offset_matrix, type = 'matrix')
            
    cmds.xform(transform, t = [0,0,0], ro = [0,0,0], s = [1,1,1], shear = [0,0,0])
    
    if cmds.nodeType(transform) == 'joint':
        cmds.setAttr('%s.jointOrientX' % transform, 0)        
        cmds.setAttr('%s.jointOrientY' % transform, 0)
        cmds.setAttr('%s.jointOrientZ' % transform, 0)
    
def empty_attach(transform_target):
    
    blend_matrix = cmds.createNode('blendMatrix')
    
    
    input_attr = attr.get_attribute_input('%s.offsetParentMatrix' % transform_target)

    if input_attr:
        input_node_type = cmds.nodeType(input_attr)
        
        if not input_node_type == 'blendMatrix':
            cmds.connectAttr(input_attr, '%s.target[0].targetMatrix' % blend_matrix)
        
        if input_node_type == 'blendMatrix':
            blend_matrix = core.get_basename(input_attr, remove_namespace = False, remove_attribute = True)
    
    cmds.connectAttr('%s.outputMatrix' % blend_matrix, '%s.offsetParentMatrix' % transform_target, f = True)
            
    next_slot = attr.get_available_slot('%s.target' % blend_matrix )
    
    matrix = api_old.get_identity_matrix()
    cmds.setAttr('%s.target[%s].targetMatrix' % (blend_matrix, next_slot), matrix, type = 'matrix')
    
    return blend_matrix
    
def attach(transform_source, transform_target):
    
    offset_parent_matrix_not_working = ['ikHandle']
    offset = True
    
    node_type_target = cmds.nodeType(transform_target)
    
    if node_type_target in offset_parent_matrix_not_working:
        offset = False
    
    mult_matrix = cmds.createNode('multMatrix', n = 'multMatrix_%s' % transform_target)
    
    inverse_matrix = cmds.getAttr('%s.inverseMatrix' % transform_target)
    cmds.setAttr('%s.matrixIn[0]' % mult_matrix, inverse_matrix, type = 'matrix')
    
    cmds.connectAttr('%s.worldMatrix' % transform_source, '%s.matrixIn[1]' % mult_matrix)
    parent = cmds.listRelatives(transform_target, p = True)
    if parent:
        cmds.connectAttr('%s.worldInverseMatrix' % parent[0], '%s.matrixIn[2]' % mult_matrix)
    
    #zero_out(transform_target)
    
    
    input_attr = attr.get_attribute_input('%s.offsetParentMatrix' % transform_target)
    
    if not input_attr:
        if offset:
            cmds.connectAttr('%s.matrixSum' % mult_matrix, '%s.offsetParentMatrix' % transform_target)
        if not offset:
            decompose = cmds.createNode('decomposeMatrix')
            cmds.connectAttr('%s.matrixSum' % mult_matrix, '%s.inputMatrix' % decompose)
            
            zero_out(transform_target)
            
            cmds.connectAttr('%s.outputTranslateX' % decompose, '%s.translateX' % transform_target)
            cmds.connectAttr('%s.outputTranslateY' % decompose, '%s.translateY' % transform_target)
            cmds.connectAttr('%s.outputTranslateZ' % decompose, '%s.translateZ' % transform_target)
            """
            if node_type_target != 'ikHandle':
                cmds.connectAttr('%s.outputRotateX' % decompose, '%s.rotateX' % transform_target)
                cmds.connectAttr('%s.outputRotateY' % decompose, '%s.rotateY' % transform_target)
                cmds.connectAttr('%s.outputRotateZ' % decompose, '%s.rotateZ' % transform_target)    
                
                cmds.connectAttr('%s.outputScaleX' % decompose, '%s.scaleX' % transform_target)
                cmds.connectAttr('%s.outputScaleY' % decompose, '%s.scaleY' % transform_target)
                cmds.connectAttr('%s.outputScaleZ' % decompose, '%s.scaleZ' % transform_target)    

                cmds.connectAttr('%s.outputShearX' % decompose, '%s.shearX' % transform_target)
                cmds.connectAttr('%s.outputShearY' % decompose, '%s.shearY' % transform_target)
                cmds.connectAttr('%s.outputShearZ' % decompose, '%s.shearZ' % transform_target)
            """ 
            
    blend_matrix = None
    if input_attr:
        
        input_node_type = cmds.nodeType(input_attr)
        
        if not input_node_type == 'blendMatrix':
            blend_matrix = cmds.createNode('blendMatrix')
            cmds.connectAttr('%s.outputMatrix' % blend_matrix, '%s.offsetParentMatrix' % transform_target, f = True)
            cmds.connectAttr(input_attr, '%s.target[0].targetMatrix' % blend_matrix)
        
        if input_node_type == 'blendMatrix':
            blend_matrix = core.get_basename(input_attr, remove_namespace = False, remove_attribute = True)
            
        
        next_slot = attr.get_available_slot('%s.target' % blend_matrix )
        cmds.connectAttr('%s.matrixSum' % mult_matrix, '%s.target[%s].targetMatrix' % (blend_matrix, next_slot))
    
    
    return [mult_matrix, blend_matrix]
       
def blend_matrix_switch(blend_matrix_node, attribute_name = 'switch',attribute_names = [], attribute_node = None):
    
    blend_matrix_node = util.convert_to_sequence(blend_matrix_node)
    
    if not blend_matrix_node[0] or not cmds.objExists(blend_matrix_node[0]):
        return
    
    condition_dict = {}
    
    if not attribute_node:
        attribute_node = blend_matrix_node[0]
    
    indices = attr.get_indices('%s.target' % blend_matrix_node[0])
    
    if not len(indices) > 1:
        return
    
    names = []
    for index in indices:
        name = 'switch%s' % (index + 1)
        if index < len(attribute_names)-1:
            name = attribute_names[index]
        names.append(name)
    
    enum_name = string.join(names, ':')
    
    source_attribute = '%s.%s' % (attribute_node, attribute_name)
    
    if not cmds.objExists(source_attribute):
        cmds.addAttr(attribute_node, ln = attribute_name, k = True, at = 'enum', en = 'a:b')
    
    cmds.addAttr(source_attribute, edit = True, en = enum_name)
    
    for node in blend_matrix_node:
        if not node or not cmds.objExists(node):
            continue
    
        indices = attr.get_indices('%s.target' % node)
        
        inc = 0
        
        for index in indices:
            
            input_node = attr.get_attribute_input('%s.target[%s].weight' % (node, index), node_only = True)
            if input_node:
                condition_dict[index] = input_node
            
            if condition_dict.has_key(index):
                condition = condition_dict[index]
            else:
                condition = cmds.createNode('condition')
                cmds.connectAttr(source_attribute, '%s.firstTerm' % condition)
                cmds.setAttr('%s.secondTerm' % condition, inc)
            
                cmds.setAttr('%s.colorIfTrueR' % condition, 1)
                cmds.setAttr('%s.colorIfFalseR' % condition, 0)
                condition_dict[inc] = condition
            
            cmds.connectAttr('%s.outColorR' % condition, '%s.target[%s].weight' % (node, index))
                    
            inc += 1
    