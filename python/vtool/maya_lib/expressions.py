# Copyright (C) 2024 Louis Vottero louis.vot@gmail.com    All rights reserved.

import maya.cmds as cmds
from vtool.maya_lib import attr


def create_expression(name='', script=''):

    expression = cmds.createNode('expression', n=name)

    cmds.setAttr('%s.expression' % expression, script, type='string')

    return expression


def initialize_wheel_script(transform):

    attributes = (
    ('initialPosition', 'vector'),
    ('position', 'vector'),
    ('lastPosition', 'vector'),
    ('target', 'vector'),
    ('targetAxis', 'vector'),
    ('spinAxis', 'vector'),
    ('enable', 'float'),
    ('diameter', 'float'),
    ('rotateMultiply', 'float'),
    ('spin', 'vector')
    )

    for attribute in attributes:
        name, attr_type = attribute
        number = attr.MayaNumberVariable(name)
        if attr_type == 'vector':
            number.set_variable_type('double3')
            number.set_keyable(False)
            number.set_channel_box(False)

        number.create(transform)

    cmds.setAttr('%s.enable' % transform, 0)
    cmds.addAttr('%s.enable' % transform, e=True, minValue=0, maxValue=1)
    cmds.setAttr('%s.rotateMultiply' % transform, 1)
    cmds.setAttr('%s.diameter' % transform, 1)
    cmds.addAttr('%s.diameter' % transform, e=True, minValue=0)
    cmds.setAttr('%s.targetAxisZ' % transform, 1)
    cmds.setAttr('%s.spinAxisX' % transform, 1)
    cmds.setAttr('%s.spinX' % transform, cb=True)
    cmds.setAttr('%s.spinY' % transform, cb=True)
    cmds.setAttr('%s.spinZ' % transform, cb=True)

    decompose = cmds.createNode('decomposeMatrix', n='decomposeMatrix_%s_expression' % transform)

    cmds.connectAttr('%s.worldMatrix[0]' % transform, '%s.inputMatrix' % decompose)
    cmds.connectAttr('%s.outputTranslateX' % decompose, '%s.positionX' % transform)
    cmds.connectAttr('%s.outputTranslateY' % decompose, '%s.positionY' % transform)
    cmds.connectAttr('%s.outputTranslateZ' % decompose, '%s.positionZ' % transform)

    vector_product = cmds.createNode('vectorProduct', n='vectorProduct_%s_expression' % transform)
    cmds.connectAttr('%s.targetAxisX' % transform, '%s.input1X' % vector_product)
    cmds.connectAttr('%s.targetAxisY' % transform, '%s.input1Y' % vector_product)
    cmds.connectAttr('%s.targetAxisZ' % transform, '%s.input1Z' % vector_product)
    cmds.setAttr('%s.operation' % vector_product, 4)
    cmds.connectAttr('%s.worldMatrix[0]' % transform, '%s.matrix' % vector_product)
    cmds.connectAttr('%s.outputX' % vector_product, '%s.targetX' % transform)
    cmds.connectAttr('%s.outputY' % vector_product, '%s.targetY' % transform)
    cmds.connectAttr('%s.outputZ' % vector_product, '%s.targetZ' % transform)

    wheel_script = """
float $enable = CTRL.enable;

vector $position = <<CTRL.positionX, CTRL.positionY, CTRL.positionZ>>;
vector $last_position = <<CTRL.lastPositionX,CTRL.lastPositionY,CTRL.lastPositionZ>>;

if ($enable > 0) {


    vector $target = <<CTRL.targetX, CTRL.targetY, CTRL.targetZ>>;

    vector $init_position = <<CTRL.initialPositionX, CTRL.initialPositionY,CTRL.initialPositionZ>>;
    vector $spin_axis = <<CTRL.spinAxisX, CTRL.spinAxisY,CTRL.spinAxisZ>>;

    vector $delta_position = $position - $init_position;
    vector $velocity = $position - $last_position;
    vector $vector = $target - $position;

    float $rotate_multiply = CTRL.rotateMultiply;

    float $magnitude = mag($velocity);
    if ($magnitude != 0) $velocity = $velocity/$magnitude;

    float $dot = dot($velocity, $vector);

    float $diameter = CTRL.diameter;
    float $pi = 3.14159;
    float $circumference = $pi * $diameter;

    float $rotation = $dot * ($magnitude/$circumference) * 360;
    $rotation *= $enable * $rotate_multiply;

    CTRL.spinX += $rotation * $spin_axis.x;
    CTRL.spinY += $rotation * $spin_axis.y;
    CTRL.spinZ += $rotation * $spin_axis.z;


};

CTRL.lastPositionX = $position.x;
CTRL.lastPositionY = $position.y;
CTRL.lastPositionZ = $position.z;
"""

    wheel_script = wheel_script.replace('CTRL', transform)
    return wheel_script


def initialize_spring_script(transform, attribute_control=None):

    if not cmds.objExists('%s.enable' % transform):
        cmds.addAttr(transform, ln='enable', min=0, max=1, dv=1, k=True)

    keyables = (
    ('enable', 'float'),
    ('startFrame', 'float'),
    ('mass', 'float'),
    ('stiffness', 'float'),
    ('damping', 'float')
    )
    attributes = (
    ('velocity', 'vector'),
    ('position', 'vector'),
    ('lastPosition', 'vector'),
    ('outWorldPosition', 'vector'),
    ('outPosition', 'vector'),
    ('outMatrix', 'matrix')
    )

    if not attribute_control:
        attribute_control = transform

    attr.create_title(attribute_control, 'SPRING')

    for attribute in attributes:
        name, attr_type = attribute
        number = attr.MayaNumberVariable(name)
        if attr_type == 'vector':
            number.set_variable_type('double3')
            number.set_keyable(False)
            number.set_channel_box(False)
        if attr_type == 'matrix':
            number.set_variable_type('matrix')

        number.create(transform)

    for keyable in keyables:
        name, attr_type = keyable
        number = attr.MayaNumberVariable(name)
        number.create(attribute_control)

    cmds.setAttr('%s.stiffness' % attribute_control, .1)
    cmds.setAttr('%s.damping' % attribute_control, .1)
    cmds.setAttr('%s.mass' % attribute_control, 1)
    cmds.setAttr('%s.startFrame' % attribute_control, 1)

    decompose = cmds.createNode('decomposeMatrix', n='decomposeMatrix_%s_expression' % transform)

    cmds.connectAttr('%s.worldMatrix[0]' % transform, '%s.inputMatrix' % decompose)
    cmds.connectAttr('%s.outputTranslateX' % decompose, '%s.positionX' % transform)
    cmds.connectAttr('%s.outputTranslateY' % decompose, '%s.positionY' % transform)
    cmds.connectAttr('%s.outputTranslateZ' % decompose, '%s.positionZ' % transform)

    vector_product = cmds.createNode('vectorProduct', n='vectorProduct_%s_expression' % transform)
    cmds.connectAttr('%s.outWorldPositionX' % transform, '%s.input1X' % vector_product)
    cmds.connectAttr('%s.outWorldPositionY' % transform, '%s.input1Y' % vector_product)
    cmds.connectAttr('%s.outWorldPositionZ' % transform, '%s.input1Z' % vector_product)
    cmds.setAttr('%s.operation' % vector_product, 4)
    cmds.connectAttr('%s.parentInverseMatrix[0]' % transform, '%s.matrix' % vector_product)
    cmds.connectAttr('%s.outputX' % vector_product, '%s.outPositionX' % transform)
    cmds.connectAttr('%s.outputY' % vector_product, '%s.outPositionY' % transform)
    cmds.connectAttr('%s.outputZ' % vector_product, '%s.outPositionZ' % transform)

    compose = cmds.createNode('composeMatrix', n='composeMatrix_%s_expression' % transform)
    cmds.connectAttr('%s.outputX' % vector_product, '%s.inputTranslateX' % compose)
    cmds.connectAttr('%s.outputY' % vector_product, '%s.inputTranslateY' % compose)
    cmds.connectAttr('%s.outputZ' % vector_product, '%s.inputTranslateZ' % compose)

    cmds.connectAttr('%s.outputMatrix' % compose, '%s.outMatrix' % transform)

    spring_script = """

float $enable = CTRL.enable;
float $stiffness = CTRL.stiffness;
float $damping = CTRL.damping;
float $mass = CTRL.mass;
float $start_frame = CTRL.startFrame;
vector $target_position;
vector $current_position;
vector $velocity;
vector $acceleration;

$target_position = <<XFORM.positionX, XFORM.positionY, XFORM.positionZ>>;

$current_position = <<XFORM.outWorldPositionX, XFORM.outWorldPositionY, XFORM.outWorldPositionZ>>;
$velocity = <<XFORM.velocityX, XFORM.velocityY, XFORM.velocityZ>>;
$last_position = <<XFORM.lastPositionX, XFORM.lastPositionY, XFORM.lastPositionZ>>;



if (frame <= $start_frame || $enable == 0) {
    $current_position = $target_position;
    $velocity = <<0,0,0>>;
}
else
{
    vector $displacement = $current_position - $target_position;
    vector $spring_force = -$stiffness * $displacement;

    vector $damping_force = -$damping * $velocity;

    vector $total_force = $spring_force + $damping_force;

    $acceleration = $total_force / $mass;

    $velocity = $velocity + $acceleration;

    $current_position = $current_position + $velocity;

    if ($enable < 1)
    {
        $current_position = $target_position + ($current_position - $target_position) * $enable;
    }

}
XFORM.outWorldPositionX = $current_position.x;
XFORM.outWorldPositionY = $current_position.y;
XFORM.outWorldPositionZ = $current_position.z;

XFORM.velocityX = $velocity.x;
XFORM.velocityY = $velocity.y;
XFORM.velocityZ = $velocity.z;
XFORM.lastPositionX = $target_position.x;
XFORM.lastPositionY = $target_position.y;
XFORM.lastPositionZ = $target_position.z;
"""

    spring_script = spring_script.replace('CTRL', attribute_control)
    spring_script = spring_script.replace('XFORM', transform)
    return spring_script
