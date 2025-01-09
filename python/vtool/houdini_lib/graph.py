# Copyright (C) 2025 Louis Vottero louis.vot@gmail.com    All rights reserved.

from vtool import util

character_import = None
current_network = None
current_apex = None

if util.in_houdini:
    import hou
    import apex


def set_current_character_import(node):

    global character_import

    character_import = node.path()

    util.show('Set current character to %s' % character_import)


def set_current_network(network):
    global current_network
    current_network = network


def set_current_apex(edit_graph):
    global current_apex
    current_apex = edit_graph


def reset_current_character_import(name=''):
    character_node = hou.node(character_import)

    if not character_node:

        util.warning('No houdini character import to work with.')
        return

    button = character_node.parm('reload')
    button.pressButton()


def initialize_input_output(apex_graph):

    input_nodes = apex_graph.matchNodes('input')
    output_nodes = apex_graph.matchNodes('output')
    if input_nodes and output_nodes:
        return input_nodes[0], output_nodes[0]

    input_id = apex_graph.addNode('input', '__parms__')
    output_id = apex_graph.addNode('output', '__output__')

    position = hou.Vector3(20, 0, 0)
    apex_graph.setNodePosition(output_id, position)

    return input_id, output_id


def add_bone_deform(apex_graph):

    base_shp = apex_graph.addGraphInput(0, 'Base.shp')
    base_skel = apex_graph.addGraphInput(0, 'Base.skel')

    out_base_shp = apex_graph.addGraphOutput(1, 'Base.shp')
    out_base_skel = apex_graph.addGraphOutput(1, 'Base.skel')

    point_transform = apex_graph.addNode('point_transform', 'skel::SetPointTransforms')
    apex_graph.setNodePosition(point_transform, hou.Vector3(16, -2, 0))
    point_skel_in = apex_graph.getPort(point_transform, "geo[in]")
    point_skel_out = apex_graph.getPort(point_transform, "geo[out]")

    bone_deform = apex_graph.addNode('bone_deform', 'sop::bonedeform')
    apex_graph.setNodePosition(bone_deform, hou.Vector3(18, -1, 0))
    bone_shp_in = apex_graph.getPort(bone_deform, "geoinput0")
    bone_skel_in = apex_graph.getPort(bone_deform, "geoinput1")
    bone_skel_pose_in = apex_graph.getPort(bone_deform, "geoinput2")
    bone_shp_out = apex_graph.getPort(bone_deform, "geo[out]")

    rest = apex_graph.addNode('rest', 'Value<Geometry>')
    apex_graph.setNodePosition(rest, hou.Vector3(14, -2, 0))
    rest_parm = apex_graph.getPort(rest, 'parm')
    rest_value = apex_graph.getPort(rest, 'value')

    apex_graph.addWire(base_shp, bone_shp_in)
    apex_graph.addWire(base_skel, bone_skel_in)
    apex_graph.addWire(point_skel_out, bone_skel_pose_in)

    apex_graph.addWire(base_skel, rest_parm)
    apex_graph.addWire(rest_value, point_skel_in)

    apex_graph.addWire(bone_shp_out, out_base_shp)
    apex_graph.addWire(point_skel_out, out_base_skel)


def get_apex_graph(edit_graph_instance, parm='stash'):
    geo = edit_graph_instance.parm(parm).eval()
    if not geo:
        geo = hou.Geometry()
    graph = apex.Graph(geo)
    print(graph)

    return graph


def update_apex_graph(edit_graph_instance, apex_graph, parm='stash'):
    geo = hou.Geometry()
    apex_graph.writeToGeometry(geo)
    geo.incrementAllDataIds()  # not sure why this is needed
    edit_graph_instance.parm(parm).set(geo)


def build_character_sub_graph_for_apex(character_node=None, name=None, refresh=False):

    if not name:
        name = 'setup_apex'

    if character_node:
        character_node = hou.node(character_node)
    else:
        character_node = hou.node(character_import)

    if not character_node:
        return None, None

    position = character_node.position()

    current_graph = character_node.parent()

    sub_graph = current_graph.node(name)

    if refresh:

        button = character_node.parm('reload')
        button.pressButton()

        if sub_graph:
            sub_graph.destroy()
            sub_graph = None

    if sub_graph:
        edit_graph = sub_graph.node('editgraph1')
    else:
        sub_graph = current_graph.createNode('subnet', name)
        position[1] -= 2
        sub_graph.setPosition(position)

        sub_graph.setInput(0, character_node, 0)
        sub_graph.setInput(1, character_node, 1)

        edit_graph = sub_graph.createNode('apex::editgraph')
        pack_folder = sub_graph.createNode('packfolder')
        edit_graph.setPosition(hou.Vector2(2.5, 0))
        pack_folder.setPosition(hou.Vector2(0, -1))

        pack_folder.setInput(1, sub_graph.indirectInputs()[0])
        pack_folder.setInput(2, sub_graph.indirectInputs()[1])
        pack_folder.setInput(3, edit_graph)

        button = pack_folder.parm('reloadnames')
        button.pressButton()

        pack_folder.parm('name1').set('Base')
        pack_folder.parm('type1').set('shp')

        pack_folder.parm('name2').set('Base')
        pack_folder.parm('type2').set('skel')

        pack_folder.parm('name3').set('Base')
        pack_folder.parm('type3').set('rig')

    return sub_graph, edit_graph

"""
class Graph(pybind11_builtins.pybind11_object)
 |  Method resolution order:
 |      Graph
 |      pybind11_builtins.pybind11_object
 |      builtins.object
 |  
 |  Methods defined here:
 |  
 |  __copy__(...)
 |      __copy__(self: _apex.Graph) -> _apex.Graph
 |  
 |  __init__(...)
 |      __init__(*args, **kwargs)
 |      Overloaded function.
 |      
 |      1. __init__(self: _apex.Graph) -> None
 |      
 |      2. __init__(self: _apex.Graph, arg0: str) -> None
 |      
 |      3. __init__(self: _apex.Graph, arg0: object) -> None
 |  
 |  addGraphInput(...)
 |      addGraphInput(self: _apex.Graph, arg0: int, arg1: str) -> int
 |  
 |  addGraphOutput(...)
 |      addGraphOutput(self: _apex.Graph, arg0: int, arg1: str) -> int
 |  
 |  addNode(...)
 |      addNode(self: _apex.Graph, arg0: str, arg1: str) -> int
 |  
 |  addNodeToSubnet(...)
 |      addNodeToSubnet(self: _apex.Graph, arg0: int, arg1: str, arg2: str) -> int
 |  
 |  addSubPort(...)
 |      addSubPort(self: _apex.Graph, arg0: int, arg1: str) -> int
 |  
 |  addSubnet(...)
 |      addSubnet(self: _apex.Graph, arg0: str, arg1: _apex.Graph) -> int
 |  
 |  addWire(...)
 |      addWire(*args, **kwargs)
 |      Overloaded function.
 |      
 |      1. addWire(self: _apex.Graph, arg0: int, arg1: int) -> int
 |      
 |      2. addWire(self: _apex.Graph, arg0: int, arg1: str, arg2: int, arg3: str) -> int
 |  
 |  addWires(...)
 |      addWires(self: _apex.Graph, arg0: str, arg1: str) -> List[int]
 |  
 |  buildControlGraph(...)
 |      buildControlGraph(self: _apex.Graph, arg0: str, arg1: str) -> tuple
 |  
 |  buildParmDependencies(...)
 |      buildParmDependencies(self: _apex.Graph) -> None
 |  
 |  buildParmSubgraph(...)
 |      buildParmSubgraph(self: _apex.Graph, arg0: str) -> List[int]
 |  
 |  callbackName(...)
 |      callbackName(self: _apex.Graph, arg0: int) -> str
 |  
 |  compileProgram(...)
 |      compileProgram(self: _apex.Graph) -> None
 |  
 |  connectedPorts(...)
 |      connectedPorts(self: _apex.Graph, portid: int, traverse_subnets: bool = True, ignore_spare: bool = 
False) -> List[int]
 |  
 |  errors(...)
 |      errors(self: _apex.Graph) -> List[str]
 |  
 |  evaluateNodes(...)
 |      evaluateNodes(self: _apex.Graph, arg0: List[int]) -> None
 |  
 |  evaluateOutput(...)
 |      evaluateOutput(self: _apex.Graph, arg0: str) -> object
 |  
 |  evaluateOutputs(...)
 |      evaluateOutputs(*args, **kwargs)
 |      Overloaded function.
 |      
 |      1. evaluateOutputs(self: _apex.Graph, arg0: str) -> _apex.Dict
 |      
 |      2. evaluateOutputs(self: _apex.Graph, arg0: List[int]) -> list
 |  
 |  executeProgram(...)
 |      executeProgram(self: _apex.Graph) -> None
 |  
 |  executionErrors(...)
 |      executionErrors(self: _apex.Graph) -> List[str]
 |  
 |  findGraphInputPort(...)
 |      findGraphInputPort(self: _apex.Graph, arg0: str) -> int
 |  
 |  findGraphOutputPort(...)
 |      findGraphOutputPort(self: _apex.Graph, arg0: str) -> int
 |  
 |  findOrAddPort(...)
 |      findOrAddPort(self: _apex.Graph, arg0: int, arg1: str) -> int
 |  
 |  findPorts(...)
 |      findPorts(self: _apex.Graph, arg0: int, arg1: List[str]) -> List[int]
 |  
 |  freeze(...)
 |      freeze(self: _apex.Graph) -> _apex.Graph
 |  
 |  getConnectedNodes(...)
 |      getConnectedNodes(self: _apex.Graph, arg0: int, arg1: bool, arg2: bool) -> List[int]
 |  
 |  getDefaultParameters(...)
 |      getDefaultParameters(self: _apex.Graph, include_compiled: bool = False) -> _apex.Dict
 |  
 |  getDirtyParameters(...)
 |      getDirtyParameters(self: _apex.Graph) -> List[str]
 |  
 |  getInputPorts(...)
 |      getInputPorts(self: _apex.Graph, arg0: int) -> List[int]
 |  
 |  getNodeOutputData(...)
 |      getNodeOutputData(self: _apex.Graph, arg0: str, arg1: str) -> object
 |  
 |  getNodeParmDependencies(...)
 |      getNodeParmDependencies(self: _apex.Graph, arg0: int) -> List[int]
 |  
 |  getNodeParms(...)
 |      getNodeParms(self: _apex.Graph, arg0: int) -> _apex.Dict
 |  
 |  getNodeProperties(...)
 |      getNodeProperties(self: _apex.Graph, arg0: int) -> _apex.Dict
 |  
 |  getNodesDependingOnParm(...)
 |      getNodesDependingOnParm(self: _apex.Graph, arg0: int) -> List[int]
 |  
 |  getOutputData(...)
 |      getOutputData(self: _apex.Graph, arg0: str) -> object
 |  
 |  getOutputPorts(...)
 |      getOutputPorts(self: _apex.Graph, arg0: int) -> List[int]
 |  
 |  getParmDict(...)
 |      getParmDict(self: _apex.Graph) -> _apex.Dict
 |  
 |  getPort(...)
 |      getPort(self: _apex.Graph, arg0: int, arg1: str) -> int
 |  
 |  getPortData(...)
 |      getPortData(self: _apex.Graph, arg0: int, arg1: bool) -> object
 |  
 |  getPromotedPort(...)
 |      getPromotedPort(self: _apex.Graph, arg0: int, arg1: bool) -> int
 |  
 |  inputPorts(...)
 |      inputPorts(self: _apex.Graph) -> List[int]
 |  
 |  isGraphAsset(...)
 |      isGraphAsset(self: _apex.Graph, arg0: int) -> bool
 |  
 |  isPortInPlace(...)
 |      isPortInPlace(self: _apex.Graph, arg0: int) -> bool
 |  
 |  isPortPromoted(...)
 |      isPortPromoted(self: _apex.Graph, arg0: int, arg1: bool) -> bool
 |  
 |  isValidForGeometry(...)
 |      isValidForGeometry(self: _apex.Graph, arg0: object) -> bool
 |  
 |  layout(...)
 |      layout(self: _apex.Graph) -> None
 |  
 |  linkPort(...)
 |      linkPort(self: _apex.Graph, arg0: int) -> int
 |  
 |  loadFromGeometry(...)
 |      loadFromGeometry(self: _apex.Graph, py_geo: object, essential_only: bool = False) -> bool
 |  
 |  matchNodes(...)
 |      matchNodes(self: _apex.Graph, arg0: str) -> List[int]
 |  
 |  matchPorts(...)
 |      matchPorts(self: _apex.Graph, arg0: str) -> List[int]
 |  
 |  merge(...)
 |      merge(self: _apex.Graph, arg0: _apex.Graph) -> None
 |  
 |  nodeColor(...)
 |      nodeColor(self: _apex.Graph, arg0: int) -> Vector3
 |  
 |  nodeInvocationIndex(...)
 |      nodeInvocationIndex(self: _apex.Graph, arg0: int) -> int
 |  
 |  nodeName(...)
 |      nodeName(self: _apex.Graph, arg0: int) -> str
 |  
 |  nodeParent(...)
 |      nodeParent(self: _apex.Graph, arg0: int) -> int
 |  
 |  nodePath(...)
 |      nodePath(self: _apex.Graph, arg0: int) -> str
 |  
 |  nodePosition(...)
 |      nodePosition(self: _apex.Graph, arg0: int) -> Vector3
 |  
 |  nodeTags(...)
 |      nodeTags(self: _apex.Graph, arg0: int) -> _apex.StringArray
 |  
 |  outerPortIndex(...)
 |      outerPortIndex(self: _apex.Graph, arg0: int) -> int
 |  
 |  outputPorts(...)
 |      outputPorts(self: _apex.Graph) -> List[int]
 |  
 |  packSubGraph(...)
 |      packSubGraph(self: _apex.Graph, arg0: str, arg1: List[int]) -> int
 |  
 |  parameters(...)
 |      parameters(self: _apex.Graph) -> _apex.Dict
 |  
 |  portKind(...)
 |      portKind(self: _apex.Graph, arg0: int) -> apex::APEX_ConnectorType
 |  
 |  portName(...)
 |      portName(self: _apex.Graph, arg0: int) -> str
 |  
 |  portNode(...)
 |      portNode(self: _apex.Graph, arg0: int) -> int
 |  
 |  portPath(...)
 |      portPath(self: _apex.Graph, arg0: int) -> str
 |  
 |  portPaths(...)
 |      portPaths(self: _apex.Graph) -> List[str]
 |  
 |  portTypeName(...)
 |      portTypeName(self: _apex.Graph, arg0: int) -> str
 |  
 |  portWires(...)
 |      portWires(self: _apex.Graph, arg0: int) -> List[int]
 |  
 |  previewDirtyNodes(...)
 |      previewDirtyNodes(self: _apex.Graph) -> List[int]
 |  
 |  promoteInput(...)
 |      promoteInput(self: _apex.Graph, arg0: int, arg1: int, arg2: str) -> int
 |  
 |  promoteOutput(...)
 |      promoteOutput(self: _apex.Graph, arg0: int, arg1: int, arg2: str) -> int
 |  
 |  properties(...)
 |      properties(self: _apex.Graph) -> _apex.Dict
 |  
 |  removeNode(...)
 |      removeNode(self: _apex.Graph, arg0: str) -> None
 |  
 |  removeNodes(...)
 |      removeNodes(self: _apex.Graph, arg0: List[int]) -> None
 |  
 |  removeWire(...)
 |      removeWire(self: _apex.Graph, arg0: int, arg1: bool) -> None
 |  
 |  removeWires(...)
 |      removeWires(self: _apex.Graph, arg0: List[int], arg1: bool) -> None
 |  
 |  resetProgram(...)
 |      resetProgram(self: _apex.Graph) -> None
 |  
 |  resolveTypes(...)
 |      resolveTypes(self: _apex.Graph) -> None
 |  
 |  setDebug(...)
 |      setDebug(self: _apex.Graph, arg0: bool) -> None
 |  
 |  setDefaultParms(...)
 |      setDefaultParms(self: _apex.Graph, parms: _apex.Dict, clear: bool = True) -> None
 |  
 |  setName(...)
 |      setName(self: _apex.Graph, arg0: str) -> None
 |  
 |  setNodeColor(...)
 |      setNodeColor(*args, **kwargs)
 |      Overloaded function.
 |      
 |      1. setNodeColor(self: _apex.Graph, arg0: int, arg1: object) -> None
 |      
 |      2. setNodeColor(self: _apex.Graph, arg0: int, arg1: Vector3) -> None
 |  
 |  setNodeName(...)
 |      setNodeName(self: _apex.Graph, arg0: int, arg1: str) -> None
 |  
 |  setNodeParms(...)
 |      setNodeParms(*args, **kwargs)
 |      Overloaded function.
 |      
 |      1. setNodeParms(self: _apex.Graph, arg0: int, arg1: _apex.Dict) -> None
 |      
 |      2. setNodeParms(self: _apex.Graph, arg0: int, arg1: str, arg2: dict) -> None
 |  
 |  setNodePosition(...)
 |      setNodePosition(self: _apex.Graph, arg0: int, arg1: Vector3) -> None
 |  
 |  setNodeProperties(...)
 |      setNodeProperties(self: _apex.Graph, arg0: int, arg1: _apex.Dict) -> None
 |  
 |  setNodeTag(...)
 |      setNodeTag(self: _apex.Graph, arg0: int, arg1: str) -> None
 |  
 |  setNodeTags(...)
 |      setNodeTags(self: _apex.Graph, arg0: int, arg1: _apex.StringArray, arg2: bool) -> None
 |  
 |  setParametersDirty(...)
 |      setParametersDirty(self: _apex.Graph, arg0: List[str]) -> None
 |  
 |  setParm(...)
 |      setParm(self: _apex.Graph, key: str, py_obj: object, set_default: bool = True) -> None
 |  
 |  setParms(...)
 |      setParms(*args, **kwargs)
 |      Overloaded function.
 |      
 |      1. setParms(self: _apex.Graph, arg0: dict) -> None
 |      
 |      2. setParms(self: _apex.Graph, parms: _apex.Dict, clear: bool = True) -> None
 |  
 |  setPortName(...)
 |      setPortName(self: _apex.Graph, arg0: int, arg1: str) -> None
 |  
 |  setProperties(...)
 |      setProperties(self: _apex.Graph, arg0: _apex.Dict) -> None
 |  
 |  setStrictCompile(...)
 |      setStrictCompile(self: _apex.Graph, arg0: bool) -> None
 |  
 |  signature(...)
 |      signature(self: _apex.Graph) -> apex::APEX_Signature
 |  
 |  sort(...)
 |      sort(self: _apex.Graph, update_position: bool = False, use_compile_sort: bool = False) -> None
 |  
 |  stat(...)
 |      stat(self: _apex.Graph) -> Dict[str, int]
 |  
 |  subGraphForOutput(...)
 |      subGraphForOutput(self: _apex.Graph, arg0: str) -> List[int]
 |  
 |  subPortIndex(...)
 |      subPortIndex(self: _apex.Graph, arg0: int) -> int
 |  
 |  subPorts(...)
 |      subPorts(self: _apex.Graph, arg0: int) -> List[int]
 |  
 |  unpackSubGraph(...)
 |      unpackSubGraph(self: _apex.Graph, arg0: int) -> None
 |  
 |  wirePorts(...)
 |      wirePorts(self: _apex.Graph, arg0: int) -> Tuple[int, int]
 |  
 |  writeToGeometry(...)
 |      writeToGeometry(*args, **kwargs)
 |      Overloaded function.
 |      
 |      1. writeToGeometry(self: _apex.Graph, py_geo: object, output_node_data: bool = False, output_debug:
 bool = False, preserve_generics: bool = False) -> None
 |      
 |      2. writeToGeometry(self: _apex.Graph, arg0: object, arg1: List[int]) -> None
 |  
 |  ----------------------------------------------------------------------
 |  Static methods defined here:
 |  
 |  executeMulti(...) from builtins.PyCapsule
 |      executeMulti(arg0: List[_apex.Graph]) -> None
 |  
 |  ----------------------------------------------------------------------
 |  Data and other attributes defined here:
 |  
 |  Input = <connectorType.Input: 0>
 |  
 |  Output = <connectorType.Output: 1>
 |  
 |  connectorType = <class '_apex.Graph.connectorType'>
 |  
 |  ----------------------------------------------------------------------
 |  Static methods inherited from pybind11_builtins.pybind11_object:
 |  
 |  __new__(*args, **kwargs) from pybind11_builtins.pybind11_type
 |      Create and return a new object.  See help(type) for accurate signature.
"""
