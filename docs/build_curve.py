import util
import os
import sys

sys.path.append('./python')


def get_curve_image_dir():
    dir = util.get_doc_directory

    image_dir = os.path.join(dir, 'docs')


def get_curve_names():

    from vtool.maya_lib import curve

    curve_info = curve.CurveDataInfo()
    curve_info.set_active_library('default_curves')
    names = curve_info.get_curve_names()

    return names


def create_curve_rst():

    curve_names = get_curve_names()

    dir = util.get_doc_directory()
    image_dir = os.path.join(dir, 'custom/curve_images')
    rst_dir = os.path.join(dir, 'custom/curve_info.rst')

    files = os.listdir(image_dir)

    lines = []

    lines.append('Curves')
    lines.append('=' * len('Curves'))
    lines.append(' ')
    lines.append('The names of these curves can be used when calling a rig class to set the curve shape.')
    lines.append('')
    lines.append('.. code-block:: python')
    lines.append('')
    lines.append('    from vtool.maya_lib import rigs')
    lines.append(' ')
    lines.append('    rig = rigs.FkRig("test", "C")')
    lines.append('    rig.set_control_shape("square")')
    lines.append(' ')

    image_curves = []
    no_image_curves = []

    for curve_name in curve_names:

        print('adding curve:', curve_name)

        found = False

        for filename in files:
            if filename.startswith(curve_name):
                image_curves.append(curve_name)
                found = True
                break

        if not found:
            no_image_curves.append(curve_name)

    lines.append('-----------------------------')
    lines.append(' ')

    lines.append('.. rubric:: Curves with no example image')
    lines.append(' ')

    for curve in no_image_curves:
        lines.append('.. rubric:: %s' % curve)
        lines.append(' ')

    lines.append('-----------------------------')
    lines.append(' ')
    lines.append('.. rubric:: Curves with example image')

    for curve in image_curves:

        lines.append('.. figure:: curve_images/%s.jpg' % curve)
        lines.append(' ')
        lines.append('    %s' % curve)
        lines.append(' ')

    util.write_lines(rst_dir, lines)
