from __future__ import absolute_import

import maya.OpenMayaMPx as OpenMayaMPx
import maya.OpenMaya as OpenMaya
import math

API_VERSION = OpenMaya.MGlobal.apiVersion()


class cvShapeInverter(OpenMayaMPx.MPxDeformerNode):
    kPluginNodeName = "cvShapeInverter"
    kPluginNodeId = OpenMaya.MTypeId(0x00115805)
    aMatrix = OpenMaya.MObject()
    aCorrectiveGeo = OpenMaya.MObject()
    aDeformedPoints = OpenMaya.MObject()
    aActivate = OpenMaya.MObject()

    def __init__(self):
        OpenMayaMPx.MPxDeformerNode.__init__(self)
        self.__initialized = False
        self.__matrices = []
        self.__deformedPoints = OpenMaya.MPointArray()

    def deform(self, data, itGeo, localToWorldMatrix, geomIndex):

        run = data.inputValue(cvShapeInverter.aActivate).asBool()
        if not run:
            return 0
            # return OpenMaya.MStatus.kSuccess

        # Read the matrices
        if not self.__initialized:

            if API_VERSION < 201600:
                input_attribute = OpenMayaMPx.cvar.MPxDeformerNode_input
                input_geom = OpenMayaMPx.cvar.MPxDeformerNode_inputGeom
            else:
                input_attribute = OpenMayaMPx.cvar.MPxGeometryFilter_input
                input_geom = OpenMayaMPx.cvar.MPxGeometryFilter_inputGeom

            h_input = data.outputArrayValue(input_attribute)
            h_input.jumpToElement(geomIndex)
            o_input_geom = h_input.outputValue().child(input_geom).asMesh()
            fn_input_mesh = OpenMaya.MFnMesh(o_input_geom)
            num_vertices = fn_input_mesh.numVertices()

            h_matrix = data.inputArrayValue(cvShapeInverter.aMatrix)
            for i in range(num_vertices):
                self.jumpToElement(h_matrix, i)
                self.__matrices.append(h_matrix.inputValue().asMatrix())

            o_deformed_points = data.inputValue(cvShapeInverter.aDeformedPoints).data()
            fn_data = OpenMaya.MFnPointArrayData(o_deformed_points)
            fn_data.copyTo(self.__deformedPoints)
            self.__initialized = True

        # Get the corrective mesh
        o_mesh = data.inputValue(cvShapeInverter.aCorrectiveGeo).asMesh()
        fn_mesh = OpenMaya.MFnMesh(o_mesh)
        corrective_points = OpenMaya.MPointArray()
        fn_mesh.getPoints(corrective_points)

        # Perform the inversion calculation
        while not itGeo.isDone():
            index = itGeo.index()

            if corrective_points[index] == self.__deformedPoints[index]:
                continue

            delta = corrective_points[index] - self.__deformedPoints[index]

            if (math.fabs(delta.x) < 0.001
                    and math.fabs(delta.y) < 0.001
                    and math.fabs(delta.z) < 0.001):
                itGeo.next()
                continue

            offset = delta * self.__matrices[index]
            pt = itGeo.position() + offset
            itGeo.setPosition(pt)
            itGeo.next()

        return 0
        # return OpenMaya.MStatus.kSuccess

    def jumpToElement(self, hArray, index):
        """@brief Jumps an array handle to a logical index and uses the builder if necessary.

        @param[in/out] hArray MArrayDataHandle to jump.
        @param[in] index Logical index.
        """
        try:
            hArray.jumpToElement(index)
        except:
            builder = hArray.builder()
            builder.addElement(index)
            hArray.set(builder)
            hArray.jumpToElement(index)


def creator():
    return OpenMayaMPx.asMPxPtr(cvShapeInverter())


def initialize():
    m_attr = OpenMaya.MFnMatrixAttribute()
    t_attr = OpenMaya.MFnTypedAttribute()
    n_attr = OpenMaya.MFnNumericAttribute()

    if API_VERSION < 201600:
        output_geom = OpenMayaMPx.cvar.MPxDeformerNode_outputGeom
    else:
        # MPxGeometryFilter is parent to MPXDeformerNode, was not exposed prior to maya 2016
        output_geom = OpenMayaMPx.cvar.MPxGeometryFilter_outputGeom

    cvShapeInverter.aActivate = n_attr.create('activate', 'activate', OpenMaya.MFnNumericData.kBoolean)
    cvShapeInverter.addAttribute(cvShapeInverter.aActivate)
    cvShapeInverter.attributeAffects(cvShapeInverter.aActivate, output_geom)

    cvShapeInverter.aCorrectiveGeo = t_attr.create('correctiveMesh', 'cm', OpenMaya.MFnData.kMesh)
    cvShapeInverter.addAttribute(cvShapeInverter.aCorrectiveGeo)
    cvShapeInverter.attributeAffects(cvShapeInverter.aCorrectiveGeo, output_geom)

    cvShapeInverter.aDeformedPoints = t_attr.create('deformedPoints', 'dp', OpenMaya.MFnData.kPointArray)
    cvShapeInverter.addAttribute(cvShapeInverter.aDeformedPoints)

    cvShapeInverter.aMatrix = m_attr.create('inversionMatrix', 'im')
    m_attr.setArray(True)
    m_attr.setUsesArrayDataBuilder(True)
    cvShapeInverter.addAttribute(cvShapeInverter.aMatrix)


def initializePlugin(mobject):
    plugin = OpenMayaMPx.MFnPlugin(mobject)
    plugin.registerNode(cvShapeInverter.kPluginNodeName,
                        cvShapeInverter.kPluginNodeId,
                        creator,
                        initialize,
                        OpenMayaMPx.MPxNode.kDeformerNode)


def uninitializePlugin(mobject):
    plugin = OpenMayaMPx.MFnPlugin(mobject)
    plugin.deregisterNode(cvShapeInverter.kPluginNodeId)
