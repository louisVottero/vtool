# Copyright (C) 2025 Louis Vottero louis.vot@gmail.com    All rights reserved.

from . import graph
import unreal


class VetalaLib(object):

    def __init__(self):
        pass

    def findPoleVector(self, controller, library):

        entry = 'Entry'
        controller.add_exposed_pin('BoneA', unreal.RigVMPinDirection.INPUT, 'FRigElementKey', '/Script/ControlRig.RigElementKey', '()')
        controller.add_exposed_pin('BoneB', unreal.RigVMPinDirection.INPUT, 'FRigElementKey', '/Script/ControlRig.RigElementKey', '()')
        controller.add_exposed_pin('BoneC', unreal.RigVMPinDirection.INPUT, 'FRigElementKey', '/Script/ControlRig.RigElementKey', '()')
        controller.add_exposed_pin('output', unreal.RigVMPinDirection.INPUT, 'double', 'None', '0')
        return1 = 'Return'
        controller.add_exposed_pin('Transform', unreal.RigVMPinDirection.OUTPUT, 'FTransform', '/Script/CoreUObject.Transform', '()')
        get_transform = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetTransform', 'Execute', unreal.Vector2D(448.0, 304.0), 'Get Transform')
        get_transform1 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetTransform', 'Execute', unreal.Vector2D(448.0, 559.0), 'Get Transform')
        get_transform2 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetTransform', 'Execute', unreal.Vector2D(448.0, 815.0), 'Get Transform')
        length = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathVectorLength', 'Execute', unreal.Vector2D(1216.0, 799.0), 'Length')
        subtract = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathVectorSub', 'Execute', unreal.Vector2D(960.0, 879.0), 'Subtract')
        subtract1 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathVectorSub', 'Execute', unreal.Vector2D(960.0, 511.0), 'Subtract')
        dot = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathVectorDot', 'Execute', unreal.Vector2D(1216.0, 687.0), 'Dot')
        divide = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathFloatDiv', 'Execute', unreal.Vector2D(1376.0, 735.0), 'Divide')
        unit = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathVectorUnit', 'Execute', unreal.Vector2D(1488.0, 927.0), 'Unit')
        scale = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathVectorScale', 'Execute', unreal.Vector2D(1679.0, 927.0), 'Scale')
        subtract2 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathVectorSub', 'Execute', unreal.Vector2D(1760.0, 704.0), 'Subtract')
        scale1 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathVectorScale', 'Execute', unreal.Vector2D(2112.0, 752.0), 'Scale')
        add = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathVectorAdd', 'Execute', unreal.Vector2D(2640.0, 192.0), 'Add')
        unit1 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathVectorUnit', 'Execute', unreal.Vector2D(1964.0, 724.0), 'Unit')

        graph.add_link(entry, 'ExecuteContext', return1, 'ExecuteContext', controller)
        graph.add_link(entry, 'BoneA', get_transform, 'Item', controller)
        graph.add_link(entry, 'BoneB', get_transform1, 'Item', controller)
        graph.add_link(entry, 'BoneC', get_transform2, 'Item', controller)
        graph.add_link(entry, 'output', scale1, 'Factor', controller)
        graph.add_link(get_transform, 'Transform.Translation', subtract, 'B', controller)
        graph.add_link(get_transform, 'Transform.Translation', subtract1, 'B', controller)
        graph.add_link(get_transform1, 'Transform.Translation', subtract1, 'A', controller)
        graph.add_link(get_transform1, 'Transform.Translation', add, 'A', controller)
        graph.add_link(get_transform2, 'Transform.Translation', subtract, 'A', controller)
        graph.add_link(subtract, 'Result', length, 'Value', controller)
        graph.add_link(length, 'Result', divide, 'B', controller)
        graph.add_link(subtract, 'Result', unit, 'Value', controller)
        graph.add_link(subtract, 'Result', dot, 'B', controller)
        graph.add_link(subtract1, 'Result', dot, 'A', controller)
        graph.add_link(subtract1, 'Result', subtract2, 'A', controller)
        graph.add_link(dot, 'Result', divide, 'A', controller)
        graph.add_link(divide, 'Result', scale, 'Factor', controller)
        graph.add_link(unit, 'Result', scale, 'Value', controller)
        graph.add_link(scale, 'Result', subtract2, 'B', controller)
        graph.add_link(subtract2, 'Result', unit1, 'Value', controller)
        graph.add_link(unit1, 'Result', scale1, 'Value', controller)
        graph.add_link(scale1, 'Result', add, 'B', controller)
        graph.add_link(add, 'Result', return1, 'Transform.Translation', controller)

        graph.set_pin(return1, 'Transform', '(Rotation=(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=1.000000,Y=1.000000,Z=1.000000))', controller)
        graph.set_pin(get_transform, 'Space', 'GlobalSpace', controller)
        graph.set_pin(get_transform, 'bInitial', 'False', controller)
        graph.set_pin(get_transform1, 'Space', 'GlobalSpace', controller)
        graph.set_pin(get_transform1, 'bInitial', 'False', controller)
        graph.set_pin(get_transform2, 'Space', 'GlobalSpace', controller)
        graph.set_pin(get_transform2, 'bInitial', 'False', controller)
