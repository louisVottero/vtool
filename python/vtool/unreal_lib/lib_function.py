# Copyright (C) 2025 Louis Vottero louis.vot@gmail.com    All rights reserved.

from . import graph
import unreal


class VetalaLib(object):

    def __init__(self):
        pass

    def Control(self, controller, library):

        controller.add_local_variable_from_object_path('last_description', 'FString', '', '')

        entry = 'Entry'
        controller.add_exposed_pin('increment', unreal.RigVMPinDirection.INPUT, 'int32', 'None', '0')
        controller.add_exposed_pin('parent', unreal.RigVMPinDirection.INPUT, 'FRigElementKey', '/Script/ControlRig.RigElementKey', '(Type=None,Name="None")')
        controller.add_exposed_pin('driven', unreal.RigVMPinDirection.INPUT, 'FRigElementKey', '/Script/ControlRig.RigElementKey', '(Type=None,Name="None")')
        controller.add_exposed_pin('description', unreal.RigVMPinDirection.INPUT, 'FString', 'None', '')
        controller.add_exposed_pin('side', unreal.RigVMPinDirection.INPUT, 'FString', 'None', '')
        controller.add_exposed_pin('joint_token', unreal.RigVMPinDirection.INPUT, 'FString', 'None', '')
        controller.add_exposed_pin('sub_count', unreal.RigVMPinDirection.INPUT, 'int32', 'None', '0')
        controller.add_exposed_pin('restrain_numbering', unreal.RigVMPinDirection.INPUT, 'bool', 'None', 'false')
        controller.add_exposed_pin('shape', unreal.RigVMPinDirection.INPUT, 'FString', 'None', '')
        controller.add_exposed_pin('color', unreal.RigVMPinDirection.INPUT, 'TArray<FLinearColor>', '/Script/CoreUObject.LinearColor', '((R=0,G=0,B=0,A=0.000000))')
        controller.add_exposed_pin('sub_color', unreal.RigVMPinDirection.INPUT, 'TArray<FLinearColor>', '/Script/CoreUObject.LinearColor', '((R=0,G=0,B=0,A=0.000000))')
        controller.add_exposed_pin('translate', unreal.RigVMPinDirection.INPUT, 'TArray<FVector>', '/Script/CoreUObject.Vector', '()')
        controller.add_exposed_pin('rotate', unreal.RigVMPinDirection.INPUT, 'TArray<FVector>', '/Script/CoreUObject.Vector', '()')
        controller.add_exposed_pin('scale', unreal.RigVMPinDirection.INPUT, 'TArray<FVector>', '/Script/CoreUObject.Vector', '()')
        controller.add_exposed_pin('world', unreal.RigVMPinDirection.INPUT, 'bool', 'None', '')
        controller.add_exposed_pin('mirror', unreal.RigVMPinDirection.INPUT, 'bool', 'None', '')
        return1 = 'Return'
        controller.add_exposed_pin('Last Control', unreal.RigVMPinDirection.OUTPUT, 'FRigElementKey', '/Script/ControlRig.RigElementKey', '(Type=None,Name="None")')
        controller.add_exposed_pin('Control', unreal.RigVMPinDirection.OUTPUT, 'FRigElementKey', '/Script/ControlRig.RigElementKey', '(Type=None,Name="None")')
        controller.add_exposed_pin('Sub Controls', unreal.RigVMPinDirection.OUTPUT, 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', '()')
        spawn_transform_control = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_HierarchyAddControlTransform', 'Execute', unreal.Vector2D(992.0, -16.0), 'Spawn Transform Control')
        get_description = controller.add_variable_node('description', 'FString', None, True, '', unreal.Vector2D(-284.0, 1008.0), 'Get description')
        get_restrain_numbering = controller.add_variable_node('restrain_numbering', 'bool', None, True, '', unreal.Vector2D(-348.0, 1168.0), 'Get restrain_numbering')
        get_increment = controller.add_variable_node('increment', 'int32', None, True, '', unreal.Vector2D(-416.0, 1488.0), 'Get increment')
        get_side = controller.add_variable_node('side', 'FString', None, True, '', unreal.Vector2D(-284.0, 1088.0), 'Get side')
        at = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(176.0, 64.0), 'At')
        from_euler = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathQuaternionFromEuler', 'Execute', unreal.Vector2D(64.0, 592.0), 'From Euler')
        from_string = controller.add_template_node('DISPATCH_RigDispatch_FromString(in String,out Result)', unreal.Vector2D(64.0, 192.0), 'From String')
        at1 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(1712.0, 384.0), 'At')
        get_sub_count = controller.add_variable_node('sub_count', 'int32', None, True, '', unreal.Vector2D(1712.0, 272.0), 'Get sub_count')
        at2 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(608.0, 512.0), 'At')
        at3 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(-128.0, 592.0), 'At')
        at4 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)', unreal.Vector2D(608.0, 624.0), 'At')
        set_item_array_metadata = controller.add_template_node('DISPATCH_RigDispatch_SetMetadata(in Item,in Name,in NameSpace,in Value,out Success)', unreal.Vector2D(2432.0, -208.0), 'Set Item Array Metadata')
        set_last_description = controller.add_variable_node('last_description', 'FString', None, False, '', unreal.Vector2D(3616.0, -208.0), 'Set last_description')
        greater = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathIntGreater', 'Execute', unreal.Vector2D(32.0, 1440.0), 'Greater')
        get_description1 = controller.add_variable_node('description', 'FString', None, True, '', unreal.Vector2D(3440.0, -64.0), 'Get description')
        get_last_description = controller.add_variable_node('last_description', 'FString', None, True, '', unreal.Vector2D(-240.0, 1696.0), 'Get last_description')
        and1 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathBoolAnd', 'Execute', unreal.Vector2D(336.0, 1520.0), 'And')
        if1 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(512.0, 1520.0), 'If')
        equals = controller.add_template_node('DISPATCH_RigVMDispatch_CoreEquals(in A,in B,out Result)', unreal.Vector2D(32.0, 1584.0), 'Equals')
        make_relative = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathTransformMakeRelative', 'Execute', unreal.Vector2D(800.0, -336.0), 'Make Relative')
        get_transform = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetTransform', 'Execute', unreal.Vector2D(-144.0, -352.0), 'Get Transform')
        get_transform1 = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_GetTransform', 'Execute', unreal.Vector2D(176.0, -560.0), 'Get Transform')
        if2 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(512.0, -592.0), 'If')
        if3 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(1104.0, -528.0), 'If')
        shape_exists = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_ShapeExists', 'Execute', unreal.Vector2D(208.0, 336.0), 'Shape Exists')
        if4 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(688.0, 224.0), 'If')
        not_equals = controller.add_template_node('DISPATCH_RigVMDispatch_CoreNotEquals(in A,in B,out Result)', unreal.Vector2D(288.0, 192.0), 'Not Equals')
        and2 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_MathBoolAnd', 'Execute', unreal.Vector2D(464.0, 304.0), 'And')
        for_each = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayIterator(in Array,out Element,out Index,out Count,out Ratio)', unreal.Vector2D(2720.0, -208.0), 'For Each')
        set_item_metadata = controller.add_template_node('DISPATCH_RigDispatch_SetMetadata(in Item,in Name,in NameSpace,in Value,out Success)', unreal.Vector2D(2960.0, -208.0), 'Set Item Metadata')
        vetala_lib_construct_name = controller.add_function_reference_node(library.find_function('vetalaLib_ConstructName'), unreal.Vector2D(300.0, 800.0), 'vetalaLib_ConstructName')
        vetala_lib_control_sub = controller.add_function_reference_node(library.find_function('vetalaLib_ControlSub'), unreal.Vector2D(2100.0, 100.0), 'vetalaLib_ControlSub')
        vetala_lib_mirror_transform = controller.add_function_reference_node(library.find_function('vetalaLib_MirrorTransform'), unreal.Vector2D(750.0, -700.0), 'vetalaLib_MirrorTransform')
        item_exists = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_ItemExists', 'Execute', unreal.Vector2D(160.0, -112.0), 'Item Exists')
        if5 = controller.add_template_node('DISPATCH_RigVMDispatch_If(in Condition,in True,in False,out Result)', unreal.Vector2D(496.0, -208.0), 'If')

        graph.add_link(entry, 'ExecuteContext', spawn_transform_control, 'ExecuteContext', controller)
        graph.add_link(set_last_description, 'ExecuteContext', return1, 'ExecuteContext', controller)
        graph.add_link(spawn_transform_control, 'ExecuteContext', vetala_lib_control_sub, 'ExecuteContext', controller)
        graph.add_link(vetala_lib_control_sub, 'ExecuteContext', set_item_array_metadata, 'ExecuteContext', controller)
        graph.add_link(set_item_array_metadata, 'ExecuteContext', for_each, 'ExecuteContext', controller)
        graph.add_link(for_each, 'Completed', set_last_description, 'ExecuteContext', controller)
        graph.add_link(for_each, 'ExecuteContext', set_item_metadata, 'ExecuteContext', controller)
        graph.add_link(entry, 'parent', spawn_transform_control, 'Parent', controller)
        graph.add_link(entry, 'parent', get_transform, 'Item', controller)
        graph.add_link(entry, 'parent', item_exists, 'Item', controller)
        graph.add_link(entry, 'driven', get_transform1, 'Item', controller)
        graph.add_link(entry, 'shape', from_string, 'String', controller)
        graph.add_link(entry, 'color', at, 'Array', controller)
        graph.add_link(entry, 'sub_color', at1, 'Array', controller)
        graph.add_link(entry, 'translate', at2, 'Array', controller)
        graph.add_link(entry, 'rotate', at3, 'Array', controller)
        graph.add_link(entry, 'scale', at4, 'Array', controller)
        graph.add_link(entry, 'world', if2, 'Condition', controller)
        graph.add_link(entry, 'mirror', if3, 'Condition', controller)
        graph.add_link(vetala_lib_control_sub, 'LastSubControl', return1, 'Last Control', controller)
        graph.add_link(spawn_transform_control, 'Item', return1, 'Control', controller)
        graph.add_link(vetala_lib_construct_name, 'Result', spawn_transform_control, 'Name', controller)
        graph.add_link(spawn_transform_control, 'Item', set_item_array_metadata, 'Item', controller)
        graph.add_link(spawn_transform_control, 'Item', set_item_metadata, 'Value', controller)
        graph.add_link(spawn_transform_control, 'Item', vetala_lib_control_sub, 'control', controller)
        graph.add_link(make_relative, 'Local', spawn_transform_control, 'OffsetTransform', controller)
        graph.add_link(get_description, 'Value', equals, 'A', controller)
        graph.add_link(get_description, 'Value', vetala_lib_construct_name, 'Description', controller)
        graph.add_link(get_restrain_numbering, 'Value', vetala_lib_construct_name, 'RestrainNumbering', controller)
        graph.add_link(get_increment, 'Value', greater, 'A', controller)
        graph.add_link(get_increment, 'Value', if1, 'True', controller)
        graph.add_link(get_increment, 'Value', vetala_lib_construct_name, 'Number', controller)
        graph.add_link(get_side, 'Value', vetala_lib_construct_name, 'Side', controller)
        graph.add_link(at3, 'Element', from_euler, 'Euler', controller)
        graph.add_link(from_string, 'Result', shape_exists, 'ShapeName', controller)
        graph.add_link(from_string, 'Result', if4, 'True', controller)
        graph.add_link(from_string, 'Result', not_equals, 'A', controller)
        graph.add_link(at1, 'Element', vetala_lib_control_sub, 'color', controller)
        graph.add_link(get_sub_count, 'Value', vetala_lib_control_sub, 'sub_count', controller)
        graph.add_link(vetala_lib_control_sub, 'SubControls', set_item_array_metadata, 'Value', controller)
        graph.add_link(get_description1, 'Value', set_last_description, 'Value', controller)
        graph.add_link(greater, 'Result', and1, 'A', controller)
        graph.add_link(get_last_description, 'Value', equals, 'B', controller)
        graph.add_link(equals, 'Result', and1, 'B', controller)
        graph.add_link(and1, 'Result', if1, 'Condition', controller)
        graph.add_link(if3, 'Result', make_relative, 'Global', controller)
        graph.add_link(if5, 'Result', make_relative, 'Parent', controller)
        graph.add_link(get_transform, 'Transform', if5, 'True', controller)
        graph.add_link(get_transform1, 'Transform', if2, 'False', controller)
        graph.add_link(if2, 'Result', if3, 'False', controller)
        graph.add_link(if2, 'Result', vetala_lib_mirror_transform, 'Transform', controller)
        graph.add_link(vetala_lib_mirror_transform, 'MirrorTransform', if3, 'True', controller)
        graph.add_link(shape_exists, 'Result', and2, 'B', controller)
        graph.add_link(and2, 'Result', if4, 'Condition', controller)
        graph.add_link(not_equals, 'Result', and2, 'A', controller)
        graph.add_link(vetala_lib_control_sub, 'SubControls', for_each, 'Array', controller)
        graph.add_link(for_each, 'Element', set_item_metadata, 'Item', controller)
        graph.add_link(item_exists, 'Exists', if5, 'Condition', controller)
        graph.add_link(get_transform1, 'Transform.Translation', if2, 'True.Translation', controller)
        graph.add_link(if4, 'Result', spawn_transform_control, 'Settings.Shape.Name', controller)
        graph.add_link(at, 'Element', spawn_transform_control, 'Settings.Shape.Color', controller)
        graph.add_link(from_euler, 'Result', spawn_transform_control, 'Settings.Shape.Transform.Rotation', controller)
        graph.add_link(at2, 'Element', spawn_transform_control, 'Settings.Shape.Transform.Translation', controller)
        graph.add_link(at4, 'Element', spawn_transform_control, 'Settings.Shape.Transform.Scale3D', controller)

        graph.set_pin(spawn_transform_control, 'OffsetSpace', 'LocalSpace', controller)
        graph.set_pin(spawn_transform_control, 'InitialValue', '(Rotation=(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=1.000000,Y=1.000000,Z=1.000000))', controller)
        graph.set_pin(spawn_transform_control, 'Settings', '(InitialSpace=LocalSpace,Shape=(bVisible=True,Name="Circle_Thin",Color=(R=1.000000,G=0.000000,B=0.000000,A=1.000000),Transform=(Rotation=(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=1.000000,Y=1.000000,Z=1.000000))),Proxy=(bIsProxy=False,ShapeVisibility=BasedOnSelection),FilteredChannels=(),DisplayName="None",bUsePreferredRotationOrder=False,PreferredRotationOrder=YZX,Limits=(LimitTranslationX=(bMinimum=False,bMaximum=False),LimitTranslationY=(bMinimum=False,bMaximum=False),LimitTranslationZ=(bMinimum=False,bMaximum=False),LimitPitch=(bMinimum=False,bMaximum=False),LimitYaw=(bMinimum=False,bMaximum=False),LimitRoll=(bMinimum=False,bMaximum=False),LimitScaleX=(bMinimum=False,bMaximum=False),LimitScaleY=(bMinimum=False,bMaximum=False),LimitScaleZ=(bMinimum=False,bMaximum=False),MinValue=(Location=(X=-100.000000,Y=-100.000000,Z=-100.000000),Rotation=(Pitch=-180.000000,Yaw=-180.000000,Roll=-180.000000),Scale=(X=0.000000,Y=0.000000,Z=0.000000)),MaxValue=(Location=(X=100.000000,Y=100.000000,Z=100.000000),Rotation=(Pitch=180.000000,Yaw=180.000000,Roll=180.000000),Scale=(X=10.000000,Y=10.000000,Z=10.000000)),bDrawLimits=True))', controller)
        graph.set_pin(at, 'Index', '0', controller)
        graph.set_pin(from_euler, 'RotationOrder', 'XZY', controller)
        graph.set_pin(at1, 'Index', '0', controller)
        graph.set_pin(at2, 'Index', '0', controller)
        graph.set_pin(at3, 'Index', '0', controller)
        graph.set_pin(at4, 'Index', '0', controller)
        graph.set_pin(set_item_array_metadata, 'Name', 'Sub', controller)
        graph.set_pin(set_item_array_metadata, 'NameSpace', 'Self', controller)
        graph.set_pin(greater, 'B', '0', controller)
        graph.set_pin(if1, 'False', '0', controller)
        graph.set_pin(get_transform, 'Space', 'GlobalSpace', controller)
        graph.set_pin(get_transform, 'bInitial', 'False', controller)
        graph.set_pin(get_transform1, 'Space', 'GlobalSpace', controller)
        graph.set_pin(get_transform1, 'bInitial', 'False', controller)
        graph.set_pin(if2, 'True', '(Rotation=(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=1.000000,Y=1.000000,Z=1.000000))', controller)
        graph.set_pin(if4, 'False', 'Circle_Thin', controller)
        graph.set_pin(not_equals, 'B', 'Default', controller)
        graph.set_pin(set_item_metadata, 'Name', 'main', controller)
        graph.set_pin(set_item_metadata, 'NameSpace', 'Self', controller)
        graph.set_pin(vetala_lib_mirror_transform, 'Axis', '(X=1.000000,Y=0.000000,Z=0.000000)', controller)
        graph.set_pin(if5, 'False', '(Rotation=(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=1.000000,Y=1.000000,Z=1.000000))', controller)

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

    def IndexToItems(self, controller, library):

        controller.add_local_variable_from_object_path('local_items',
                                                       'TArray<FRigElementKey>',
                                                       '/Script/ControlRig.RigElementKey',
                                                       '')

        get_local_items = controller.add_variable_node_from_object_path('local_items', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', True, '()', unreal.Vector2D(-16.0, -336.0), 'Get local_items')
        entry = 'Entry'
        controller.add_exposed_pin('Index', unreal.RigVMPinDirection.INPUT, 'TArray<int32>', 'None', '()')
        controller.add_exposed_pin('Items', unreal.RigVMPinDirection.INPUT, 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', '()')
        return1 = 'Return'
        controller.add_exposed_pin('Result', unreal.RigVMPinDirection.OUTPUT, 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', '()')
        for_each = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayIterator(in Array,out Element,out Index,out Count,out Ratio)', unreal.Vector2D(272.0, 0.0), 'For Each')
        vetala_lib_get_item = controller.add_function_reference_node(library.find_function('vetalaLib_GetItem'), unreal.Vector2D(-80.0, 304.0), 'vetalaLib_GetItem')
        add = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayAdd(io Array,in Element,out Index)', unreal.Vector2D(832.0, 304.0), 'Add')
        set_local_items = controller.add_variable_node_from_object_path('local_items', 'TArray<FRigElementKey>', '/Script/ControlRig.RigElementKey', False, '()', unreal.Vector2D(1120.0, 304.0), 'Set local_items')
        branch = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_ControlFlowBranch', 'Execute', unreal.Vector2D(480.0, 304.0), 'Branch')
        item_exists = controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_ItemExists', 'Execute', unreal.Vector2D(176.0, 304.0), 'Item Exists')
        reset = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayReset(io Array)', unreal.Vector2D(160.0, -128.0), 'Reset')

        graph.add_link(entry, 'ExecuteContext', reset, 'ExecuteContext', controller)
        graph.add_link(for_each, 'Completed', return1, 'ExecuteContext', controller)
        graph.add_link(reset, 'ExecuteContext', for_each, 'ExecuteContext', controller)
        graph.add_link(for_each, 'ExecuteContext', branch, 'ExecuteContext', controller)
        graph.add_link(branch, 'True', add, 'ExecuteContext', controller)
        graph.add_link(add, 'ExecuteContext', set_local_items, 'ExecuteContext', controller)
        graph.add_link(get_local_items, 'Value', reset, 'Array', controller)
        graph.add_link(get_local_items, 'Value', add, 'Array', controller)
        graph.add_link(get_local_items, 'Value', return1, 'Result', controller)
        graph.add_link(entry, 'Index', for_each, 'Array', controller)
        graph.add_link(entry, 'Items', vetala_lib_get_item, 'Array', controller)
        graph.add_link(for_each, 'Element', vetala_lib_get_item, 'index', controller)
        graph.add_link(vetala_lib_get_item, 'Element', add, 'Element', controller)
        graph.add_link(vetala_lib_get_item, 'Element', item_exists, 'Item', controller)
        graph.add_link(add, 'Array', set_local_items, 'Value', controller)
        graph.add_link(item_exists, 'Exists', branch, 'Condition', controller)

    def StringToIndex(self, controller, library):

        controller.add_local_variable_from_object_path('local_index',
                                                       'TArray<int32>',
                                                       '',
                                                       '')

        entry = 'Entry'
        controller.add_exposed_pin('string', unreal.RigVMPinDirection.INPUT, 'FString', 'None', '')
        return1 = 'Return'
        controller.add_exposed_pin('index', unreal.RigVMPinDirection.OUTPUT, 'TArray<int32>', 'None', '()')
        split = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_StringSplit', 'Execute', unreal.Vector2D(-272.0, 176.0), 'Split')
        for_each = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayIterator(in Array,out Element,out Index,out Count,out Ratio)', unreal.Vector2D(192.0, 0.0), 'For Each')
        add = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayAdd(io Array,in Element,out Index)', unreal.Vector2D(576.0, 192.0), 'Add')
        from_string = controller.add_template_node('DISPATCH_RigDispatch_FromString(in String,out Result)', unreal.Vector2D(272.0, 320.0), 'From String')
        num = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayGetNum(in Array,out Num)', unreal.Vector2D(-352.0, -128.0), 'Num')
        equals = controller.add_template_node('DISPATCH_RigVMDispatch_CoreEquals(in A,in B,out Result)', unreal.Vector2D(-160.0, -128.0), 'Equals')
        branch = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_ControlFlowBranch', 'Execute', unreal.Vector2D(320.0, -240.0), 'Branch')
        length = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_StringLength', 'Execute', unreal.Vector2D(-608.0, -464.0), 'Length')
        equals1 = controller.add_template_node('DISPATCH_RigVMDispatch_CoreEquals(in A,in B,out Result)', unreal.Vector2D(-352.0, -464.0), 'Equals')
        branch1 = controller.add_unit_node_from_struct_path('/Script/RigVM.RigVMFunction_ControlFlowBranch', 'Execute', unreal.Vector2D(64.0, -464.0), 'Branch')
        from_string1 = controller.add_template_node('DISPATCH_RigDispatch_FromString(in String,out Result)', unreal.Vector2D(544.0, -272.0), 'From String')
        add1 = controller.add_template_node('DISPATCH_RigVMDispatch_ArrayAdd(io Array,in Element,out Index)', unreal.Vector2D(720.0, -448.0), 'Add')
        get_local_index = controller.add_variable_node('local_index', 'TArray<int32>', None, True, '()', unreal.Vector2D(400.0, 224.0), 'Get local_index')
        get_local_index1 = controller.add_variable_node('local_index', 'TArray<int32>', None, True, '()', unreal.Vector2D(432.0, -448.0), 'Get local_index')
        set_local_index = controller.add_variable_node('local_index', 'TArray<int32>', None, False, '()', unreal.Vector2D(944.0, -448.0), 'Set local_index')
        set_local_index1 = controller.add_variable_node('local_index', 'TArray<int32>', None, False, '()', unreal.Vector2D(800.0, 192.0), 'Set local_index')
        get_local_index2 = controller.add_variable_node('local_index', 'TArray<int32>', None, True, '()', unreal.Vector2D(896.0, 48.0), 'Get local_index')

        graph.add_link(entry, 'ExecuteContext', branch1, 'ExecuteContext', controller)
        graph.add_link(branch1, 'Completed', return1, 'ExecuteContext', controller)
        graph.add_link(branch, 'False', for_each, 'ExecuteContext', controller)
        graph.add_link(for_each, 'ExecuteContext', add, 'ExecuteContext', controller)
        graph.add_link(add, 'ExecuteContext', set_local_index1, 'ExecuteContext', controller)
        graph.add_link(add, 'Array', set_local_index1, 'Value', controller)
        graph.add_link(branch1, 'False', branch, 'ExecuteContext', controller)
        graph.add_link(branch, 'True', add1, 'ExecuteContext', controller)
        graph.add_link(add1, 'ExecuteContext', set_local_index, 'ExecuteContext', controller)
        graph.add_link(entry, 'string', split, 'Value', controller)
        graph.add_link(entry, 'string', length, 'Value', controller)
        graph.add_link(entry, 'string', from_string1, 'String', controller)
        graph.add_link(get_local_index2, 'Value', return1, 'index', controller)
        graph.add_link(split, 'Result', for_each, 'Array', controller)
        graph.add_link(split, 'Result', num, 'Array', controller)
        graph.add_link(for_each, 'Element', from_string, 'String', controller)
        graph.add_link(get_local_index, 'Value', add, 'Array', controller)

        graph.add_link(from_string, 'Result', add, 'Element', controller)
        graph.add_link(num, 'Num', equals, 'A', controller)
        graph.add_link(equals, 'Result', branch, 'Condition', controller)
        graph.add_link(length, 'Length', equals1, 'A', controller)
        graph.add_link(equals1, 'Result', branch1, 'Condition', controller)
        graph.add_link(from_string1, 'Result', add1, 'Element', controller)
        graph.add_link(get_local_index1, 'Value', add1, 'Array', controller)
        graph.add_link(add1, 'Array', set_local_index, 'Value', controller)

        graph.set_pin(split, 'Separator', ' ', controller)
        graph.set_pin(equals, 'B', '0', controller)
        graph.set_pin(equals1, 'B', '0', controller)

