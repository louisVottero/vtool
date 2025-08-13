import util
import os
import build_curve


def main():

    build_module('util', 'vtool', 'util.py')
    build_module('util_file', 'vtool', 'util_file.py')
    build_module('data', 'vtool', 'data.py')
    build_module('process', 'vtool.process_manager', 'process_manager/process.py')
    build_module('core', 'vtool.maya_lib', 'maya_lib/core.py')
    build_module('attr', 'vtool.maya_lib', 'maya_lib/attr.py')
    build_module('space', 'vtool.maya_lib', 'maya_lib/space.py')
    build_module('geo', 'vtool.maya_lib', 'maya_lib/geo.py')
    build_module('deform', 'vtool.maya_lib', 'maya_lib/deform.py')
    build_module('anim', 'vtool.maya_lib', 'maya_lib/anim.py')
    build_module('shade', 'vtool.maya_lib', 'maya_lib/shade.py')
    build_module('fx', 'vtool.maya_lib', 'maya_lib/fx.py')
    build_module('corrective', 'vtool.maya_lib', 'maya_lib/corrective.py')
    build_module('rigs', 'vtool.maya_lib', 'maya_lib/rigs.py')
    build_module('rigs_util', 'vtool.maya_lib', 'maya_lib/rigs_util.py')
    build_module('blendshape', 'vtool.maya_lib', 'maya_lib/blendshape.py')
    build_module('curve', 'vtool.maya_lib', 'maya_lib/curve.py')
    build_module('api', 'vtool.maya_lib', 'maya_lib/api.py')
    build_module('expressions', 'vtool.maya_lib', 'maya_lib/expressions.py')
    # build_module('ui', 'vtool.maya_lib', 'maya_lib/ui.py')

    build_curve.create_curve_rst()


def build_module(name, sub_path, sub_file_path):

    dir = util.vtool_dir
    docs_dir = util.get_doc_directory()

    filepath = os.path.join(dir, sub_file_path)
    output_path = docs_dir

    write_module = util.WriteModule(filepath)
    write_module.set_base_dir(dir)
    write_module.set_output_dir(output_path)
    write_module.create_module_rst(name, sub_path)


if __name__ == '__main__':
    main()
