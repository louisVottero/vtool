# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

from alembic import Abc
from alembic import AbcGeom

def get_top_in(alembic_file):
    
    cache_in = Abc.IArchive(str(alembic_file))
    top_cache_in = cache_in.getTop()
    
    return top_cache_in

def get_in_alembic(alembic_object, alembic_type_hint = None):
    """
    alembic_type_hint can be:
    "polyMesh"
    "nurbsCurve"
    """
    
    meta_data = alembic_object.getMetaData()
    
    obj_type = None
    
    if alembic_type_hint == 'polyMesh':
        obj_type = AbcGeom.IPolyMesh
        
    if alembic_type_hint == 'nurbsCurve':
        obj_type = AbcGeom.ICurves
        
    found = []
    appended = False
    if obj_type and obj_type.matches(meta_data):

        found.append(alembic_object)
        
        appended = True
    
    if not appended and alembic_type_hint == None:
        found.append(alembic_object)
    
    for child in alembic_object.children:
        found += get_in_alembic(child, alembic_type_hint)
    
    if found:
        return found
    
    return []



def get_all_instances(alembic_instance, alembic_type_hint = None):
    
    found = get_in_alembic(alembic_instance, alembic_type_hint)
    return found
    
def find_in_alembic(alembic_instance, name):
    
    children = get_in_alembic(alembic_instance, alembic_type_hint = None)
    
    for child in children:
        if child.getName() == name:
            return child
def is_constant(alembic_instance):
    
    sub_obj = False
    
    meta_data = alembic_instance.getMetaData()
    
    if AbcGeom.IPolyMesh.matches(meta_data):
        sub_obj = AbcGeom.IPolyMesh(alembic_instance, Abc.WrapExistingFlag.kWrapExisting)
        sub_obj = sub_obj.getSchema()
    
    if sub_obj:
        return sub_obj.isConstant()