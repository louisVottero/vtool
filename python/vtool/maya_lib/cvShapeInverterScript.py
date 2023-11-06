"""@brief Inverts a shape through the deformation chain
@author Chad Vernon - chadvernon@gmail.com - www.chadvernon.com
"""

from __future__ import absolute_import

import maya.cmds as cmds
import maya.OpenMaya as OpenMaya
import math

from .. import util


def invert(base=None, corrective=None, name=None):
    """@brief Inverts a shape through the deformation chain.

    @param[in] base Deformed base mesh.
    @param[in] corrective Sculpted corrective mesh.
    @param[in] name Name of the generated inverted shape.
    @return The name of the inverted shape.
    """

    if not cmds.pluginInfo('cvShapeInverterDeformer.py', query=True, loaded=True):
        cmds.loadPlugin('cvShapeInverterDeformer.py')

    cmds.undoInfo(openChunk=True)
    if not base or not corrective:
        sel = cmds.ls(sl=True)
        if not sel or len(sel) != 2:
            cmds.undoInfo(closeChunk=True)
            raise RuntimeError('Select base then corrective')
        base, corrective = sel

    # Get points on base mesh
    base_points = getPoints(base)
    num_points = base_points.length()

    # Get points on corrective mesh
    # correctivePoints = getPoints(corrective)

    # Get the intermediate mesh
    shapes = cmds.listRelatives(base, children=True, shapes=True, f=True)

    if not shapes:
        raise RuntimeError('No intermediate shape found for %s.' % base)

    for s in shapes:
        if cmds.getAttr('%s.intermediateObject' % s) and cmds.listConnections('%s.worldMesh' % s,
                                                                              source=False):
            orig_mesh = s
            break
    else:
        cmds.undoInfo(closeChunk=True)
        raise RuntimeError('No intermediate shape found for %s.' % base)

    # Get the component offset axes

    orig_points = getPoints(orig_mesh)
    x_points = OpenMaya.MPointArray(orig_points)
    y_points = OpenMaya.MPointArray(orig_points)
    z_points = OpenMaya.MPointArray(orig_points)

    for i in range(num_points):
        x_points[i].x += 1.0
        y_points[i].y += 1.0
        z_points[i].z += 1.0
    setPoints(orig_mesh, x_points)
    x_points = getPoints(base)
    setPoints(orig_mesh, y_points)
    y_points = getPoints(base)
    setPoints(orig_mesh, z_points)
    z_points = getPoints(base)
    setPoints(orig_mesh, orig_points)

    # Create the mesh to get the inversion deformer
    if not name:
        name = '%s_inverted' % corrective

    base_shape = getShape(base)

    inverted_shape = create_shape_from_shape(base_shape)

    # Delete the unnecessary shapes

    shapes = cmds.listRelatives(inverted_shape, children=True, shapes=True, fullPath=True)

    for s in shapes:
        if cmds.getAttr('%s.intermediateObject' % s):
            cmds.delete(s)

    setPoints(inverted_shape, orig_points)

    # Unlock the transformation attrs
    for attr in 'trs':
        for x in 'xyz':
            cmds.setAttr('%s.%s%s' % (inverted_shape, attr, x), lock=False)

    cmds.setAttr('%s.visibility' % inverted_shape, 1)

    deformer = cmds.deformer(inverted_shape, type='cvShapeInverter')[0]

    # Calculate the inversion matrices

    o_deformer = getMObject(deformer)
    fn_deformer = OpenMaya.MFnDependencyNode(o_deformer)

    plug_matrix = fn_deformer.findPlug('inversionMatrix', False)

    fn_matrix_data = OpenMaya.MFnMatrixData()
    for i in range(num_points):
        matrix = OpenMaya.MMatrix()
        setMatrixRow(matrix, x_points[i] - base_points[i], 0)
        setMatrixRow(matrix, y_points[i] - base_points[i], 1)
        setMatrixRow(matrix, z_points[i] - base_points[i], 2)
        matrix = matrix.inverse()
        o_matrix = fn_matrix_data.create(matrix)

        plug_matrix_element = plug_matrix.elementByLogicalIndex(i)
        plug_matrix_element.setMObject(o_matrix)

    # Store the base points.
    fn_point_data = OpenMaya.MFnPointArrayData()
    o_point_data = fn_point_data.create(base_points)
    plug_deformed_points = fn_deformer.findPlug('deformedPoints', False)
    plug_deformed_points.setMObject(o_point_data)

    cmds.connectAttr('%s.outMesh' % getShape(corrective), '%s.correctiveMesh' % deformer)

    cmds.setAttr('%s.activate' % deformer, True)

    cmds.undoInfo(closeChunk=True)

    split_name = inverted_shape.split(':')
    if len(split_name) > 1:
        inverted_shape = cmds.rename(inverted_shape, split_name[-1])

    return inverted_shape


def getShape(node):
    """@brief Returns a shape node from a given transform or shape.

    @param[in] node Name of the node.
    @return The associated shape node.
    """
    if cmds.nodeType(node) == 'transform':
        shapes = cmds.listRelatives(node, shapes=True, f=True)
        if not shapes:
            raise RuntimeError('%s has no shape' % node)
        return shapes[0]
    elif cmds.nodeType(node) in ['mesh', 'nurbsCurve', 'nurbsSurface']:
        return node


def getMObject(node):
    """@brief Gets the dag path of a node.

    @param[in] node Name of the node.
    @return The dag path of a node.
    """
    selection_list = OpenMaya.MSelectionList()
    selection_list.add(node)
    o_node = OpenMaya.MObject()
    selection_list.getDependNode(0, o_node)
    return o_node


def getDagPath(node):
    """@brief Gets the dag path of a node.

    @param[in] node Name of the node.
    @return The dag path of a node.
    """
    selection_list = OpenMaya.MSelectionList()
    selection_list.add(node)
    path_node = OpenMaya.MDagPath()
    selection_list.getDagPath(0, path_node)
    return path_node


def getPoints(path, space=OpenMaya.MSpace.kObject):
    """@brief Get the control point positions of a geometry node.

    @param[in] path Name or dag path of a node.
    @param[in] space Space to get the points.
    @return The MPointArray of points.
    """
    if util.is_str(path):
        path = getDagPath(getShape(path))
    it_geo = OpenMaya.MItGeometry(path)
    points = OpenMaya.MPointArray()
    it_geo.allPositions(points, space)
    return points


def setPoints(path, points, space=OpenMaya.MSpace.kObject):
    """@brief Set the control points positions of a geometry node.

    @param[in] path Name or dag path of a node.
    @param[in] points MPointArray of points.
    @param[in] space Space to get the points.
    """
    if util.is_str(path):
        path = getDagPath(getShape(path))
    it_geo = OpenMaya.MItGeometry(path)
    it_geo.setAllPositions(points, space)


def setMatrixRow(matrix, newVector, row):
    """@brief Sets a matrix row with an MVector or MPoint.

    @param[in/out] matrix Matrix to set.
    @param[in] newVector Vector to use.
    @param[in] row Row number.
    """
    setMatrixCell(matrix, newVector.x, row, 0)
    setMatrixCell(matrix, newVector.y, row, 1)
    setMatrixCell(matrix, newVector.z, row, 2)


def setMatrixCell(matrix, value, row, column):
    """@brief Sets a matrix cell

    @param[in/out] matrix Matrix to set.
    @param[in] value Value to set cell.
    @param[in] row Row number.
    @param[in] column Column number.
    """
    OpenMaya.MScriptUtil.setDoubleArray(matrix[row], column, value)


def create_shape_from_shape(shape):
    parent = cmds.listRelatives(shape, p=True, f=True)

    transform = cmds.group(em=True)
    transform = cmds.ls(transform, l=True)[0]

    from . import api

    api.create_mesh_from_mesh(shape, transform)

    add_to_isolate_select([transform])

    mesh = transform

    if parent:

        parent = parent[0]

        parent_name = parent.split('|')
        if parent_name:
            parent_name = parent_name[-1]

        mesh = cmds.rename(mesh, '%s_inverted' % parent_name)

        translate = cmds.xform(parent, q=True, ws=True, t=True)
        rotate = cmds.xform(parent, q=True, ws=True, ro=True)

        cmds.xform(mesh, ws=True, t=translate)
        cmds.xform(mesh, ws=True, ro=rotate)

    return mesh


def add_to_isolate_select(nodes):
    """
        Add the specified nodes into every viewport's isolate select. 
        This will only work on viewports that have isolate select turned on.
        Use when nodes are not being evaluated because isolate select causes them to be invisible.
    """

    if is_batch():
        return

    nodes = util.convert_to_sequence(nodes)

    model_panels = get_model_panels()

    for panel in model_panels:
        if cmds.isolateSelect(panel, q=True, state=True):
            for node in nodes:
                cmds.isolateSelect(panel, addDagObject=node)

            # cmds.isolateSelect(panel, update = True)


def is_batch():
    """
    Return True if Maya is in batch mode.
    """

    return cmds.about(batch=True)


def get_model_panels():
    return cmds.getPanel(type='modelPanel')
