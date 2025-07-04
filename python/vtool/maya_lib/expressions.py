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


def initialize_spring_script(transform):

    if not cmds.objExists('%s.enable' % transform):
        cmds.addAttr(transform, ln='enable', min=0, max=1, dv=1, k=True)

    attributes = (
    ('enable', 'float'),
    ('startFrame', 'float'),
    ('mass', 'float'),
    ('stiffness', 'float'),
    ('damping', 'float'),
    ('velocity', 'vector'),
    ('position', 'vector'),
    ('lastPosition', 'vector'),
    )

    for attribute in attributes:
        name, attr_type = attribute
        number = attr.MayaNumberVariable(name)
        if attr_type == 'vector':
            number.set_variable_type('double3')
            number.set_keyable(False)
            number.set_channel_box(False)

        number.create(transform)

    cmds.setAttr('%s.stiffness' % transform, .1)
    cmds.setAttr('%s.damping' % transform, .1)
    cmds.setAttr('%s.mass' % transform, 1)
    cmds.setAttr('%s.startFrame' % transform, 1)

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

$target_position = <<CTRL.translateX, CTRL.translateY, CTRL.translateZ>>;

$current_position = <<CTRL.positionX, CTRL.positionY, CTRL.positionZ>>;
$velocity = <<CTRL.velocityX, CTRL.velocityY, CTRL.velocityZ>>;
$last_position = <<CTRL.lastPositionX, CTRL.lastPositionY, CTRL.lastPositionZ>>;



if (frame <= $start_frame) {
    $current_position = $target_position;
    $velocity = <<0,0,0>>;
}
if ($enable == 0) {

    $current_position = $target_position;
    $velocity = <<0,0,0>>;
}
else
{
    if ($velocity == <<0, 0, 0>> && $last_position == <<0, 0, 0>>) {
        $current_position = $target_position;
        $velocity = <<0, 0, 0>>;
    }

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
CTRL.positionX = $current_position.x;
CTRL.positionY = $current_position.y;
CTRL.positionZ = $current_position.z;

CTRL.velocityX = $velocity.x;
CTRL.velocityY = $velocity.y;
CTRL.velocityZ = $velocity.z;
CTRL.lastPositionX = $target_position.x;
CTRL.lastPositionY = $target_position.y;
CTRL.lastPositionZ = $target_position.z;
"""

    spring_script = spring_script.replace('CTRL', transform)
    return spring_script
