# Copyright (C) 2024 Louis Vottero louis.vot@gmail.com    All rights reserved.

namespace = ''
name = ''
version = ''
command = ''
auto_run = False
# above can be replaced with file read/write and submitted to deadline

import maya.cmds as cmds
import os
import sys


def create_dir(directory):
    if not os.path.isdir(directory):
        os.mkdir(directory)

    return directory


def get_cache_node(namespace=None):
    model_groups = ['model', 'geo']

    found = None

    for model_group in model_groups:

        test_group = None
        if namespace:
            test_group = '%s:master|%s:%s' % (namespace, namespace, model_group)
        else:
            test_group = 'master|%s' % model_group

        if cmds.objExists(test_group):
            found = test_group
            break

    return found


def get_cache_dir():
    maya_scene_path = os.path.abspath(cmds.file(query=True, sn=True))

    cache_dir = os.path.join(os.path.dirname(maya_scene_path), "cache")

    create_dir(cache_dir)

    cache_dir = os.path.join(cache_dir, "alembic")

    create_dir(cache_dir)

    return cache_dir


def get_output_dir(node, dir_name):
    output_name = None
    if namespace:
        output_name = namespace
    else:
        output_name = name

    output_dir = os.path.join(dir_name, output_name)
    create_dir(output_dir)

    return output_name, output_dir


def cache(cache_namespace=None):
    if not cache_namespace:
        cache_namespace = namespace
    else:
        global namespace
        namespace = cache_namespace

    node = get_cache_node(cache_namespace)
    cache_dir = get_cache_dir()

    output_name, output_dir = get_output_dir(node, cache_dir)

    cache_path = None
    if version:
        pad_version = str('{0:03d}'.format(int(version)))
        cache_path = os.path.join(output_dir, (output_name + '.' + pad_version)) + '.abc'
    else:
        cache_path = os.path.join(output_dir, output_name) + '.abc'

    if not cmds.pluginInfo('AbcExport', query=True, loaded=True):
        cmds.loadPlugin('AbcExport')

    if command:
        exec(command)
    else:
        cmds.AbcExport(j="-frameRange %s %s -stripNamespaces -uvWrite -worldSpace"
                         " -writeVisibility -dataFormat ogawa -root %s -file %s" % (0, 100, node, cache_path))


# run cache
if auto_run:
    cache()
