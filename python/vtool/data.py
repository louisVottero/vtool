# Copyright (C) 2024 Louis Vottero louis.vot@gmail.com    All rights reserved.

from __future__ import absolute_import

import json
import traceback
import threading
import os

from . import util, util_file, usd

if util.in_maya:
    import maya.cmds as cmds
    import maya.mel as mel
    from . import maya_lib
elif util.in_houdini:
    import hou
    from . import houdini_lib
elif util.in_unreal:
    from . import unreal_lib
from vtool import util_shotgun

from vtool import logger

log = logger.get_logger(__name__)


class DataManager(object):
    """
    Manages data types
    """

    def __init__(self):
        self.available_data = [MayaAsciiFileData(),
                               MayaBinaryFileData(),
                               MayaShotgunFileData(),
                               ScriptManifestData(),
                               ScriptPythonData(),
                               ControlCvData(),
                               ControlColorData(),
                               MayaControlAttributeData(),
                               MayaControlRotateOrderData(),
                               SkinWeightData(),
                               DeformerWeightData(),
                               BlendshapeWeightData(),
                               PoseData(),
                               MayaAttributeData(),
                               AnimationData(),
                               ControlAnimationData(),
                               MayaShadersData(),
                               PlatformData(),
                               FbxData(),
                               UsdData(),
                               HoudiniFileData(),
                               HoudiniNodeData(),
                               UnrealFileData(),
                               UnrealGraphData()
                               ]

    def get_available_types(self):
        types = [data.get_type() for data in self.available_data]
        return types

    def get_type_instance(self, data_type):
        return next((data for data in self.available_data if data.is_type_match(data_type)), None)


class DataFolder(object):
    """
    A folder with a json file for tracking data
    """

    def __init__(self, name, filepath):

        new_path = util_file.join_path(filepath, name)
        self.filepath = util_file.get_dirname(new_path)
        self.name = util_file.get_basename(new_path)
        self.folder_path = None

        self.data_type = None

        test_path = util_file.join_path(self.filepath, self.name)

        is_folder = util_file.is_dir(test_path)

        if is_folder:
            self.folder_path = test_path
        else:
            self._create_folder()

        self.settings = None

    def _load_folder(self):

        self._load_settings()

        needs_default = False
        if not self.settings.has_setting('name'):
            needs_default = True

        if not needs_default and not self.settings.has_setting('data_type'):
            needs_default = True

        if needs_default:
            self._set_default_settings()

    def _set_settings_path(self, folder):
        if not self.settings:
            self._load_folder()

        self.settings.set_directory(folder, 'data.json')

    def _load_settings(self):
        self.settings = util_file.SettingsFile()
        self._set_settings_path(self.folder_path)

    def _set_default_settings(self):

        self._load_settings()

        self.settings.set('name', self.name)

        data_type = self.settings.get('data_type')

        self.data_type = data_type

    def _create_folder(self):
        if not self.name and not self.filepath:
            return
        path = util_file.create_dir(self.name, self.filepath)
        self.folder_path = path
        self._set_default_settings()

    def _set_name(self, name):
        """

        Args:
            name (str):
        """
        if not self.settings:
            self._load_folder()

        self.name = name
        self.settings.set('name', self.name)

    def get_data_type(self):

        log.debug('Get data type')

        if self.settings:
            self.settings.reload()
        if not self.settings:
            log.debug('No settings, loading...')
            self._load_folder()

        return self.settings.get('data_type')

    def set_data_type(self, data_type):

        if not self.settings:
            self._load_folder()

        self.data_type = data_type
        if data_type:
            self.settings.set('data_type', str(data_type))

    def get_sub_folder(self, name=None):
        if name:
            folder = name
        else:
            if not self.settings:
                self._load_folder()
            folder = self.settings.get('sub_folder')

        if self.folder_path:
            if not util_file.is_dir(util_file.join_path(self.folder_path, '.sub/%s' % folder)):
                return

        return folder

    def get_current_sub_folder(self):
        folder = self.get_sub_folder()
        return folder

    def set_sub_folder(self, name):
        """

        Args:
            name (str):
        """
        if not name:
            self.set_sub_folder_to_default()

        if not self.settings:
            self._load_folder()

        self.settings.set('sub_folder', name)

        sub_folder = util_file.join_path(self.folder_path, '.sub/%s' % name)

        util_file.create_dir(sub_folder)

        if self.data_type:
            self.settings.set('data_type', str(self.data_type))

    def set_sub_folder_to_default(self):

        if not self.settings:
            self._load_folder()

        self.settings.set('sub_folder', '')

    def get_folder_data_instance(self):
        """
        This gets the data instance for this data.  Data instance is the class that works on the data in this directory.
        """

        if not self.settings:
            self._load_folder()

        if not self.name:
            return

        data_type = self.settings.get('data_type')
        if not data_type:
            data_type = self.data_type

        if data_type is None:
            test_file = util_file.join_path(self.folder_path, '%s.py' % self.name)

            if util_file.is_file(test_file):
                data_type = 'script.python'
                self.settings.set('data_type', data_type)

        if not data_type:
            return

        data_manager = DataManager()
        instance = data_manager.get_type_instance(data_type)

        if instance:
            instance.set_directory(self.folder_path)
            instance.set_name(self.name)

        return instance

    def rename(self, new_name):

        basename = util_file.get_basename(new_name)

        top_folder = util_file.rename(self.folder_path, new_name)

        orig_path = self.folder_path
        self.folder_path = top_folder

        if not top_folder:
            return

        instance = self.get_folder_data_instance()

        if instance:
            folder = instance.rename(basename)

            if not folder:
                util_file.rename(top_folder, orig_path)
                self.folder_path = orig_path

        self._set_settings_path(top_folder)
        self._set_name(basename)

        return self.folder_path

    def delete(self):

        name = util_file.get_basename(self.folder_path)
        directory = util_file.get_dirname(self.folder_path)

        util_file.delete_dir(name, directory)


class DataFile(object):

    def __init__(self, name, directory):

        self.filepath = util_file.create_file(name, directory)

        self.name = util_file.get_basename(self.filepath)
        self.directory = util_file.get_dirname(self.filepath)

    def _get_folder(self):

        name = util_file.get_basename_no_extension(self.name)

        dirpath = util_file.join_path(self.directory, name)

        return dirpath

    def _create_folder(self):

        name = util_file.get_basename_no_extension(self.name)

        folder = util_file.create_dir(name, self.directory)
        return folder

    def _rename_folder(self, new_name):
        """

        Args:
            new_name (str):

        Returns:

        """
        dirpath = self._get_folder()

        if not util_file.is_dir(dirpath):
            return

        new_name = util_file.get_basename_no_extension(new_name)

        if util_file.is_dir(dirpath):
            util_file.rename(dirpath, new_name)

    def _create_version_folder(self):

        self.version_path = util_file.create_dir('.versions', self.directory)

    def version_file(self, comment):
        """

        Args:
            comment (str):
        """
        self._create_version_folder()
        version_file = util_file.VersionFile(self.filepath)
        version_file.set_version_folder(self.version_path)
        version_file.set_version_folder_name('.%s' % self.name)
        version_file.set_version_name(self.name)
        version_file.save(comment)

    def add_child(self, filepath):
        """

        Args:
            filepath (str):

        Returns:

        """
        folder = self._create_folder()

        child_name = util_file.get_basename(filepath)
        new_child_path = util_file.join_path(folder, child_name)

        util_file.move(filepath, new_child_path)

        path_name = util_file.join_path(self.name, child_name)

        return self.directory, path_name

    def delete(self):

        folder = self._get_folder()

        if folder:
            util_file.delete_dir(self.name, self.directory)

        if util_file.is_file(self.filepath):
            util_file.delete_file(self.name, self.directory)

    def rename(self, new_name):
        """

        Args:
            new_name (str):

        Returns:

        """
        filepath = util_file.rename(self.filepath, new_name)

        if not filepath:
            return

        self._rename_folder(new_name)

        self.name = new_name
        self.directory = util_file.get_dirname(filepath)
        self.filepath = filepath

        return self.filepath


class Data(object):

    def __init__(self, name=None):
        self.data_type = self._data_type()
        self.data_extension = self._data_extension()

        self.name = name

        if not name:
            self.name = self._data_name()

    def _data_name(self):
        return 'data'

    def _data_type(self):
        return None

    def set_name(self, name):
        self.name = name

    def is_type_match(self, data_type):
        return data_type == self.data_type

    def get_type(self):
        return self.data_type


class FileData(Data):

    def __init__(self, name=None):
        super(FileData, self).__init__(name)
        self.filepath = None
        self.directory = None
        self.settings = util_file.SettingsFile()
        self.file = None
        self._sub_folder = None
        self._temp_sub_folder = None

    def _data_extension(self):
        return 'data'

    def _get_file_name(self):
        name = self.name
        if self.data_extension:
            return '%s.%s' % (name, self.data_extension)
        else:
            return name

    def set_directory(self, directory):

        log.info('Set FileData directory %s', directory)

        self.directory = directory
        self.settings.set_directory(self.directory, 'data.json')
        self.name = self.settings.get('name')

        self.get_sub_folder()

        if self.data_extension:
            self.filepath = util_file.join_path(directory, '%s.%s' % (self.name, self.data_extension))
        else:
            self.filepath = util_file.join_path(directory, self.name)

    def get_file(self):
        """
        This will get the data file taking into account the currently set sub folder
        """
        directory = self.directory

        filename = self._get_file_name()

        sub_folder = self._sub_folder
        if not sub_folder and self._temp_sub_folder:
            sub_folder = self._temp_sub_folder

        if sub_folder:
            directory = util_file.join_path(self.directory, '.sub/%s' % sub_folder)

        filepath = util_file.join_path(directory, filename)

        return filepath

    def get_file_direct(self, sub_folder=None):
        """
        This will get the data file and optionally the sub folder if a name is given.

        Args:
            sub_folder (str):
        """

        directory = self.directory

        filename = self._get_file_name()

        if sub_folder:
            directory = util_file.join_path(self.directory, '.sub/%s' % sub_folder)

        filepath = util_file.join_path(directory, filename)

        return filepath

    def get_folder(self):

        directory = self.directory

        return directory

    def get_sub_folder(self):

        folder_name = self.settings.get('sub_folder')

        if folder_name:
            self._sub_folder = folder_name

        if not folder_name or folder_name == '-top folder-':
            if self._temp_sub_folder:
                folder_name = self._temp_sub_folder
            else:
                self.set_sub_folder('')
                return

        log.debug('Get sub folder %s' % folder_name)

        if self.directory and not util_file.is_dir(util_file.join_path(self.directory, '.sub/%s' % folder_name)):
            self.set_sub_folder('')
            return

        return folder_name

    def set_temp_sub_folder(self, folder_name):
        self._temp_sub_folder = folder_name

    def set_sub_folder(self, folder_name):

        self._sub_folder = folder_name

        if not folder_name:
            self.settings.set('sub_folder', '')
            return

        sub_folder = util_file.join_path(self.directory, '.sub/%s' % folder_name)

        if util_file.is_dir(sub_folder):
            self.settings.set('sub_folder', folder_name)

    def create(self):
        name = self.name

        self.file = util_file.create_file('%s.%s' % (name, self.data_extension), self.directory)

    def rename(self, new_name):

        old_name = self.name

        if old_name == new_name:
            return True

        old_filepath = util_file.join_path(self.directory, '%s.%s' % (old_name, self.data_extension))

        self.set_name(new_name)

        found = util_file.is_file(old_filepath) or util_file.is_dir(old_filepath)
        if found:
            util_file.rename(old_filepath, self._get_file_name())
            return self._get_file_name()

        if not found:
            return True


class ScriptData(FileData):

    def __init__(self, name=None):
        super(ScriptData, self).__init__(name)
        self.lines = None

    def save(self, lines, comment=None):

        log.info('Data saving code')

        filepath = util_file.join_path(self.directory, self._get_file_name())

        util_file.write_lines(filepath, lines)

        version = util_file.VersionFile(filepath)
        version.save(comment)

    def set_lines(self, lines):
        self.lines = lines

    def create(self):
        super(ScriptData, self).create()

        filename = self.get_file()

        if not hasattr(self, 'lines'):
            return

        if self.lines and filename:
            util_file.write_lines(filename, self.lines)


class ScriptManifestData(ScriptData):

    def _data_type(self):
        return 'script.manifest'


class ScriptPythonData(ScriptData):

    def _data_type(self):
        return 'script.python'

    def _data_extension(self):
        return 'py'

    def open(self):
        lines = ''
        return lines


class ScriptMelData(ScriptData):

    def _data_type(self):
        return 'script.mel'

    def _data_extension(self):
        return 'mel'


class CustomData(FileData):

    def import_data(self):
        pass

    def export_data(self):
        pass


class MayaCustomData(CustomData):

    def _center_view(self):
        # cmds.select(cl = True)

        maya_lib.core.auto_focus_view()


class ControlCvData(MayaCustomData):
    """
    maya.control_cvs
    Exports/Imports cv positions on controls.
    All control cvs will be exported regardless of selection.
    All control cvs will be imported regardless of selection.
    """

    def _data_name(self):
        return 'control_cvs'

    def _data_type(self):
        return 'maya.control_cvs'

    def _initialize_library(self, filename=None):
        if filename:
            directory = util_file.get_dirname(filename)
            name = util_file.get_basename(filename)
        else:
            path = self.get_file()
            directory = util_file.get_dirname(path)
            name = self.name

        library = maya_lib.curve.CurveDataInfo()
        library.set_directory(directory)

        if filename:
            library.set_active_library(name, skip_extension=True)
        else:
            library.set_active_library(name)

        return library

    def import_data(self, filename=None, selection=None):

        if not util.in_maya:
            return

        if selection is None:
            selection = []
        library = self._initialize_library(filename)

        if selection:
            controls = [thing for thing in selection if maya_lib.core.has_shape_of_type(thing, 'nurbsCurve')]
        else:
            controls = library.get_curve_names()

        for control in controls:

            if not maya_lib.core.exists(control):
                maya_lib.core.print_warning('Import cv positions missing: %s' % control)
                continue

            shapes = maya_lib.core.get_shapes(control)

            if not shapes:
                continue

            library.set_shape_to_curve(control, control, True, z_up_compensate=False)

        self._center_view()

        maya_lib.core.print_help('Imported %s data.' % self.name)

    def export_data(self, comment, selection=None):

        if selection is None:
            selection = []
        library = self._initialize_library()

        if selection:
            controls = [thing for thing in selection if maya_lib.core.has_shape_of_type(thing, 'nurbsCurve')]
        if not selection:
            controls = maya_lib.rigs_util.get_controls()

            if not controls:
                util.warning('No controls found to export.')
                return

        for control in controls:
            library.add_curve(control)

        filepath = library.write_data_to_file()

        version = util_file.VersionFile(filepath)
        version.save(comment)

        maya_lib.core.print_help('Exported %s data.' % self.name)

    def get_curves(self, filename=None):

        library = self._initialize_library(filename)
        library.set_active_library(self.name)

        curves = library.get_curve_names()

        return curves

    def remove_curve(self, curve_name, filename=None):

        curve_list = util.convert_to_sequence(curve_name)

        library = self._initialize_library(filename)
        library.set_active_library(self.name)

        for curve in curve_list:
            library.remove_curve(curve)

        library.write_data_to_file()

        return True


class ControlColorData(MayaCustomData):

    def _data_name(self):
        return 'control_colors'

    def _data_type(self):
        return 'maya.control_colors'

    def _data_extension(self):
        return 'data'

    def _get_data(self, filename):
        """

        Args:
            filename (str):

        Returns:

        """
        lines = util_file.get_file_lines(filename)

        all_control_dict = {}

        for split_line in filter(lambda x: len(x) == 2, map(lambda x: x.split('='), lines)):

            color_dict = eval(split_line[1])
            control = split_line[0].strip()
            all_control_dict[control] = color_dict

        return all_control_dict

    def _get_color_dict(self, curve):

        if not maya_lib.core.exists(curve):
            return

        sub_colors = []
        main_color = None

        if cmds.getAttr('%s.overrideEnabled' % curve):
            main_color = cmds.getAttr('%s.overrideColor' % curve)
            if maya_lib.core.exists('%s.overrideColorRGB' % curve):
                curve_rgb = cmds.getAttr('%s.overrideColorRGB' % curve)
                curve_rgb_state = cmds.getAttr('%s.overrideRGBColors' % curve)
                main_color = [main_color, curve_rgb, curve_rgb_state]

        shapes = maya_lib.core.get_shapes(curve)
        one_passed = False
        if shapes:
            for shape in shapes:
                if cmds.getAttr('%s.overrideEnabled' % shape):
                    one_passed = True

                curve_color = cmds.getAttr('%s.overrideColor' % shape)
                if maya_lib.core.exists('%s.overrideColorRGB' % shape):
                    curve_rgb = cmds.getAttr('%s.overrideColorRGB' % shape)
                    curve_rgb_state = cmds.getAttr('%s.overrideRGBColors' % shape)
                    sub_colors.append([curve_color, curve_rgb, curve_rgb_state])
                else:
                    sub_colors.append(curve_color)
        if not one_passed and main_color is None:
            return

        return {'main': main_color, 'sub': sub_colors}

    def _store_all_dict(self, all_dict, filename, comment):

        keys = list(all_dict.keys())
        keys.sort()

        lines = ['%s = %s' % (key, all_dict[key]) for key in keys]
        util_file.write_lines(filename, lines)
        version = util_file.VersionFile(filename)
        version.save(comment)

    def _set_color_dict(self, curve, color_dict):  # TODO: This beast needs to be broken apart.

        if not maya_lib.core.exists(curve):
            return

        main_color = color_dict['main']
        sub_color = color_dict['sub']

        try:
            if main_color and main_color > 0:

                current_color = cmds.getAttr('%s.overrideColor' % curve)

                if not current_color == main_color:

                    cmds.setAttr('%s.overrideEnabled' % curve, 1)

                    if main_color:
                        if not isinstance(main_color, list):
                            cmds.setAttr('%s.overrideColor' % curve, main_color)
                        if isinstance(main_color, list):
                            cmds.setAttr('%s.overrideColor' % curve, main_color[0])
                            cmds.setAttr('%s.overrideRGBColors' % curve, main_color[2])
                            if len(main_color[1]) == 1:
                                cmds.setAttr('%s.overrideColorRGB' % curve, *main_color[1][0])
                            if len(main_color[1]) > 1:
                                cmds.setAttr('%s.overrideColorRGB' % curve, *main_color[1])

                        if main_color[2]:
                            util.show('%s color of RGB %s' % (maya_lib.core.get_basename(curve), main_color[1][0]))
                        else:
                            util.show('%s color of Index %s' % (maya_lib.core.get_basename(curve), main_color[0]))
            if sub_color:
                shapes = maya_lib.core.get_shapes(curve)
                for inc, shape in enumerate(shapes):
                    sub_current_color = cmds.getAttr('%s.overrideColor' % shape)
                    if sub_current_color == sub_color[inc]:
                        continue

                    if sub_color[inc] == 0:
                        continue

                    cmds.setAttr('%s.overrideEnabled' % shape, 1)

                    if inc < len(sub_color):
                        if not isinstance(sub_color[inc], list):
                            cmds.setAttr('%s.overrideColor' % shape, sub_color[inc])
                        if isinstance(sub_color[inc], list):
                            cmds.setAttr('%s.overrideColor' % shape, sub_color[inc][0])
                            cmds.setAttr('%s.overrideRGBColors' % shape, sub_color[inc][2])
                            if len(sub_color[inc][1]) == 1:
                                cmds.setAttr('%s.overrideColorRGB' % shape, *sub_color[inc][1][0])
                            if len(sub_color[inc][1]) > 1:
                                cmds.setAttr('%s.overrideColorRGB' % shape, *sub_color[inc][1])
                        if sub_color[inc][2]:
                            util.show('%s color of RGB %s' % (maya_lib.core.get_basename(shape), sub_color[inc][1][0]))
                        else:
                            util.show('%s color of Index %s' % (maya_lib.core.get_basename(shape), sub_color[inc][0]))
        except:
            util.error(traceback.format_exc())
            util.show('Error applying color to %s.' % curve)

    def get_file(self):

        directory = self.directory

        filename = self._get_file_name()

        if self._sub_folder:
            directory = util_file.join_path(self.directory, '.sub/%s' % self._sub_folder)

        filepath = util_file.create_file(filename, directory)

        return filepath

    def export_data(self, comment, selection=None):
        """

        Args:
            comment (str):
            selection:

        Returns:

        """

        if selection is None:
            selection = []
        filepath = self.get_file()

        if not filepath:
            return

        orig_controls = self._get_data(filepath)

        if selection:
            controls = [thing for thing in selection if maya_lib.core.get_shapes(thing)]
        else:
            controls = maya_lib.rigs_util.get_controls()

        if not controls:
            util.warning('No controls found to export colors.')
            return

        for control in controls:
            color_dict = self._get_color_dict(control)
            if color_dict:
                orig_controls[control] = color_dict

        self._store_all_dict(orig_controls, filepath, comment)

        maya_lib.core.print_help('Exported %s data.' % self.name)

    def import_data(self, filename=None, selection=None):

        if selection is None:
            selection = []
        if not filename:
            filename = self.get_file()

        all_control_dict = self._get_data(filename)

        for control in all_control_dict:
            if selection and maya_lib.core.get_basename(control) not in selection:
                continue
            self._set_color_dict(control, all_control_dict[control])

    def remove_curve(self, curve_name, filename=None):

        if not filename:
            filename = self.get_file()

        curve_list = util.convert_to_sequence(curve_name)

        curve_dict = self._get_data(filename)

        for curve in filter(lambda x: x in curve_dict, curve_list):
            curve_dict.pop(curve)

        self._store_all_dict(curve_dict, filename, comment='removed curves')

        return True

    def get_curves(self, filename=None):
        if not filename:
            filename = self.get_file()

        curve_dict = self._get_data(filename)

        keys = list(curve_dict.keys())
        keys.sort()

        return keys


class SkinWeightData(MayaCustomData):
    """
        maya.skin_weights
        Export skin cluster weights on selected geo.
        Import available skin cluster weights for geo, or only the weights on selected geo.
    """

    def __init__(self, name=None):
        super(SkinWeightData, self).__init__(name)

        self.add_at_front = False

    def _data_name(self):
        return 'weights_skinCluster'

    def _data_extension(self):
        return ''

    def _data_type(self):
        return 'maya.skin_weights'

    def get_file(self, inc=0):
        filepath = super(SkinWeightData, self).get_file()
        if filepath and inc > 0:
            filepath += str(inc + 1)
        return filepath

    def get_existing(self):
        """
        This gets all exported skin clusters for this weight data. Supports up to 4 for now.
        """
        filepath = self.get_file()
        found = []

        for inc in range(0, 4):

            test_filepath = filepath if inc == 0 else '%s%d' % (filepath, inc + 1)

            if util_file.exists(test_filepath):
                found.append(test_filepath)

        return found

    def _get_influences(self, folder_path):

        util.show('Getting weight data from disk')
        files = []

        try:
            files = util_file.get_files(folder_path)
        except:
            return

        found_single_file_weights = any(filter(lambda x: x == 'all.skin.weights', files))
        influences = [filename for filename in files if filename.endswith('.weights') and filename != 'all.skin.weights']

        info_file = util_file.join_path(folder_path, 'influence.info')

        if not util_file.is_file(info_file):
            return

        influence_dict = {}
        for line_dict in map(eval, filter(None, util_file.get_file_lines(info_file))):
            influence_dict.update(line_dict)

        threads = []
        weights_dict = {}

        single_file = False

        if self.settings.has_setting('single file'):
            single_file = self.settings.get('single file')

        if found_single_file_weights and influences:
            util.warning('Found single file weights, but export told not to use it.')
        if not single_file and found_single_file_weights and not influences:
            single_file = True
            util.warning('Import skin weights told not to use single file.'
                         ' There is no exported individual joint weights.  Using single file instead.')

        if single_file and found_single_file_weights:
            path = util_file.join_path(folder_path, 'all.skin.weights')
            for split_line in map(lambda x: x.split('='), util_file.get_file_lines(path)):
                weights_dict[split_line[0]] = eval(split_line[1])

        if influences and single_file and not found_single_file_weights:
            util.warning('Import skin weights told to use single file. There is no single file weights exported.'
                         ' Using individual joint weights instead.')

        if not influences and not weights_dict:
            util.warning('Found no single file weights or individual influence weights.'
                         ' It appears the skin weights were not exported.')
            return

        if not weights_dict:
            for influence in influences:

                try:
                    read_thread = ReadWeightFileThread(influence_dict, folder_path, influence)
                    threads.append(read_thread)
                    read_thread.start()
                except:
                    util.error(traceback.format_exc())
                    util.show('Errors with %s weight file.' % influence)

            for thread in threads:
                thread.join()
        else:
            for influence in influence_dict:
                influence_dict[influence]['weights'] = weights_dict[influence]

        return influence_dict

    def _test_shape(self, mesh, shape_types):
        return any(map(lambda x: maya_lib.core.has_shape_of_type(mesh, x), shape_types))

    def _export_ref_obj(self, mesh, data_path):
        maya_lib.core.load_plugin('objExport')

        # export mesh
        value = maya_lib.deform.get_skin_envelope(mesh)
        maya_lib.deform.set_skin_envelope(mesh, 0)

        cmds.select(mesh)
        mesh_path = '%s/mesh.obj' % data_path

        orig_path = cmds.file(q=True, loc=True)

        cmds.file(rename=mesh_path)
        cmds.file(force=True,
                  options="groups=0;ptgroups=0;materials=0;smoothing=0;normals=0",
                  typ="OBJexport",
                  pr=False,
                  es=True)

        maya_lib.deform.set_skin_envelope(mesh, value)

        cmds.file(rename=orig_path)

    def _import_ref_obj(self, data_path):
        """

        Args:
            data_path (str):

        Returns:

        """
        mesh_path = "%s/mesh.obj" % data_path

        if not util_file.is_file(mesh_path):
            return

        track = maya_lib.core.TrackNodes()
        track.load('mesh')
        cmds.file(mesh_path,
                  i=True,
                  type="OBJ",
                  ignoreVersion=True,
                  options="mo=1")
        delta = track.get_delta()
        if delta:
            # delta should be a single mesh
            parent = cmds.listRelatives(delta, p=True)
            delta = parent[0]

        return delta

    def _folder_name_to_mesh_name(self, name):
        name = maya_lib.core.folder_name_to_maya_name(name)

        return name

    def _mesh_name_to_folder_name(self, name):
        name = maya_lib.core.maya_name_to_folder_name(name)

        return name

    def _import_maya_data(self, filepath=None, selection=None):

        if selection is None:
            selection = []
        if filepath:
            paths = [filepath]
        else:
            paths = self.get_existing()

        # TODO: This really needs to be broken apart.
        for path_inc, path in enumerate(paths):
            util_file.get_permission(path)

            folders = None
            if selection:
                folders = selection
            mesh_dict = {}
            found_meshes = {}
            skip_search = False
            if len(selection) == 1:
                found = []
                folders = util_file.get_folders(path)

                thing = selection[0]
                split_thing = thing.split('|')

                data_name = self._mesh_name_to_folder_name(thing)

                for folder in folders:
                    if data_name == folder:
                        found_meshes[thing] = None
                        mesh_dict[folder] = thing
                        skip_search = True
                        break

                if not skip_search:
                    for folder in folders:
                        mesh_name = self._folder_name_to_mesh_name(folder)
                        if mesh_name.endswith(split_thing[-1]):
                            mesh = thing
                            found_meshes[mesh] = None
                            mesh_dict[folder] = mesh
                            skip_search = True
                            break

            if not selection:
                folders = util_file.get_folders(path)

            if not folders:
                util.warning('No mesh folders found in skin data.')
                return
            if not skip_search:
                # dealing with conventions for referenced

                mesh_name = {}

                for folder in folders:
                    mesh = self._folder_name_to_mesh_name(folder)
                    mesh_name[folder] = mesh

                    if not maya_lib.core.exists(mesh):
                        mesh = maya_lib.core.get_basename(mesh)

                        if not maya_lib.core.exists(mesh):
                            search_meshes = cmds.ls('*:%s' % mesh, type='transform')

                            if search_meshes:
                                mesh = search_meshes[0]

                        if not maya_lib.core.exists(mesh):
                            util.show('Stripped namespace and fullpath from mesh name and could not find it.')
                            util.warning('Skipping skinCluster weights import on: %s. It does not exist.' % mesh)
                            continue

                # check if a mesh is already accounted for.
                for folder in folders:

                    mesh = mesh_name[folder]

                    found = cmds.ls(mesh)
                    if found and len(found) > 1:
                        found_meshes[mesh] = None
                        mesh_dict[folder] = mesh
                        util.warning('Multiple meshes found for %s' % mesh)
                        continue

                    if found and len(found) == 1:
                        mesh = found[0]
                        skip = False
                        for found_mesh in found_meshes:
                            if found_mesh.endswith(mesh):
                                skip = True
                                break

                        if not skip:
                            found_meshes[mesh] = None
                            mesh_dict[folder] = mesh

                # dealing with non unique named geo
                for folder in folders:

                    mesh = mesh_name[folder]

                    if folder not in mesh_dict:

                        meshes = cmds.ls(mesh, l=True)

                        for mesh in filter(lambda x: x not in found_meshes, meshes):
                            found_meshes[mesh] = None
                            mesh_dict[folder] = mesh

            mesh_count = len(list(mesh_dict.keys()))
            progress_ui = maya_lib.core.ProgressBar('Importing skin weights on:', mesh_count)
            self._progress_ui = progress_ui

            keys = list(mesh_dict.keys())
            key_count = len(keys)

            results = []

            for inc in range(0, key_count):

                current_key = keys[inc]

                mesh = mesh_dict[current_key]
                meshes = cmds.ls(mesh)

                skip_with_weights = False

                if len(meshes) > 1:
                    maya_lib.core.print_warning('Non unique %s. Applying skin weights to all matching names' % mesh)

                    skip_with_weights = True

                    # progress_ui.inc()
                    # continue
                else:
                    meshes = [mesh]

                nicename = maya_lib.core.get_basename(mesh)
                progress_ui.status('Importing skin weights on: %s    - initializing' % nicename)
                folder_path = util_file.join_path(path, current_key)

                first = True
                if path_inc > 0:
                    first = False

                for mesh in meshes:

                    skin_cluster = maya_lib.deform.find_deformer_by_type(mesh, 'skinCluster')
                    if skip_with_weights and skin_cluster:
                        continue

                    result = self.import_skin_weights(folder_path, mesh, first=first)

                    if not result:
                        maya_lib.core.print_warning('Import %s data failed on %s' % (self.name, mesh))
                    results.append(result)

                if not (inc + 1) >= key_count:
                    next_key = keys[inc + 1]
                    next_mesh = mesh_dict[next_key]
                    nicename = maya_lib.core.get_basename(next_mesh)
                    progress_ui.status('Importing skin weights on: %s    - initializing' % nicename)

                progress_ui.inc()

                if util.break_signaled():
                    break

                if progress_ui.break_signaled():
                    break

            progress_ui.end()

            if len(results) == 1:
                if not results[0]:
                    return
            maya_lib.core.print_help('Imported %s data' % self.name)

        self._center_view()

    def set_long_names(self, bool_value):
        self.settings.set('long names', bool_value)

    def set_blend_weights(self, bool_value):
        self.settings.set('blend weights', bool_value)

    def set_version_up(self, bool_value):
        self.settings.set('version up', bool_value)

    def set_single_file(self, bool_value):
        self.settings.set('single file', bool_value)

    def set_add_at_front(self, bool_value):
        self.settings.set('add at front of deformation statck', bool_value)
        self.add_at_front = bool_value

    def import_skin_weights(self, directory, mesh, first=True):  # TODO: This beast needs to be broken apart.

        add_at_front = self.settings.get('add at front of deformation statck')

        nicename = maya_lib.core.get_basename(mesh)
        short_name = cmds.ls(mesh)
        if short_name:
            short_name = short_name[0]

        util.show('Importing skin weights on %s at path %s' % (short_name, directory))

        skin_cluster = maya_lib.deform.find_deformer_by_type(mesh, 'skinCluster', return_all=True)

        if not util_file.is_dir(directory):

            mesh_name = util_file.get_basename(directory)

            mesh_name = self._mesh_name_to_folder_name(mesh_name)

            base_path = util_file.get_dirname(directory)
            directory = util_file.join_path(base_path, mesh_name)

            if not util_file.is_dir(directory):
                maya_lib.core.print_warning('Could not find weights for %s' % mesh)
                return False

        skin_attribute_dict = {}
        blend_value = None
        compatible_mesh = True
        ran_mesh_check = False

        file_path = util_file.join_path(directory, 'settings.info')

        shape_types = ['mesh', 'nurbsSurface', 'nurbsCurve', 'lattice']
        shape_is_good = self._test_shape(mesh, shape_types)

        if not shape_is_good:
            util.warning('%s does not have a supported shape node.'
                         ' Currently supported nodes include: %s.' % (short_name, shape_types))
            return False

        if util_file.is_file(file_path):
            lines = util_file.get_file_lines(file_path)
            for line_list in map(eval, filter(None, map(lambda x: x.strip(), lines))):
                attr_name = line_list[0]
                value = line_list[1]

                if attr_name == 'blendWeights':
                    blend_value = value

                elif attr_name == 'mesh info':

                    check = maya_lib.geo.MeshTopologyCheck(mesh)
                    check.mesh2_vert_count = value[0]
                    check.mesh2_edge_count = value[1]
                    check.mesh2_face_count = value[2]

                    if not check.check_vert_edge_face_count():
                        compatible_mesh = False
                    if not check.check_first_face_verts(value[3]):
                        compatible_mesh = False
                    if not check.check_last_face_verts(value[4]):
                        compatible_mesh = False

                    ran_mesh_check = True

                else:

                    skin_attribute_dict[attr_name] = value

        self._progress_ui.status('Importing skin weights on: %s    - getting influences' % nicename)

        influence_dict = self._get_influences(directory)

        self._progress_ui.status('Importing skin weights on: %s    - got influences' % nicename)
        if not influence_dict:
            return False

        influences = list(influence_dict.keys())

        if not influences:
            return False

        transfer_mesh = None

        import_obj = True
        if ran_mesh_check and compatible_mesh:
            import_obj = False

        if maya_lib.core.has_shape_of_type(mesh, 'mesh'):

            if import_obj:

                util.show('Importing reference')
                orig_mesh = self._import_ref_obj(directory)
                self._progress_ui.status('Importing skin weights on: %s    - imported reference mesh' % nicename)

                if orig_mesh:

                    if not ran_mesh_check:
                        mesh_match = maya_lib.geo.is_mesh_compatible(orig_mesh, mesh)

                        if not mesh_match:
                            transfer_mesh = mesh
                            mesh = orig_mesh
                        if mesh_match:
                            util.show('Imported reference matches')
                            cmds.delete(orig_mesh)

                    else:
                        transfer_mesh = mesh
                        mesh = orig_mesh

        influences.sort()

        non_unique_influences = []

        for influence in influences:

            maya_influence = cmds.ls(influence)
            if len(maya_influence) > 1:
                non_unique_influences.append(influence)

        if non_unique_influences:
            util.warning('Non unique influences:', non_unique_influences)
            return False

        add_joints = []
        remove_entries = []
        self._progress_ui.status('Importing skin weights on: %s    - adding influences' % nicename)
        for influence in influences:

            joints = cmds.ls(influence, l=True)

            if isinstance(joints, list) and len(joints) > 1:
                add_joints.append(joints[0])

                conflicting_count = len(joints)

                util.warning('Found %s joints with name %s.'
                             ' Using only the first one. %s' % (conflicting_count, influence, joints[0]))
                remove_entries.append(influence)
                influence = joints[0]

            if not maya_lib.core.exists(influence):
                cmds.select(cl=True)
                cmds.joint(n=influence, p=influence_dict[influence]['position'])

        for entry in remove_entries:
            influences.remove(entry)

        influences += add_joints

        if first and skin_cluster and not add_at_front:
            cmds.delete(skin_cluster)

        self._progress_ui.status('Importing skin weights on: %s    - start import skin weights' % nicename)

        nurbs_types = ('nurbsCurve', 'nurbsSurface')
        new_way = not any(map(lambda x: maya_lib.core.has_shape_of_type(mesh, x), nurbs_types))

        if new_way:
            add = False
            if not first:
                add = True
            if add_at_front:
                add = True

            skin_inst = maya_lib.deform.SkinCluster(mesh, add=add)

            for influence in influences:
                skin_inst.add_influence(influence)
            skin_cluster = skin_inst.get_skin()

            weights_found = []
            influences_found = []

            # prep skin import data
            import maya.api.OpenMaya as OM
            weight_array = OM.MDoubleArray()

            for influence in influences:

                if influence not in influence_dict or 'weights' not in influence_dict[influence]:
                    util.warning('Weights missing for influence %s' % influence)
                    continue

                weights_found.append(influence_dict[influence]['weights'])
                influences_found.append(influence)

            for inc in range(0, len(weights_found[0])):

                for inc2 in range(0, len(influences_found)):

                    weight = weights_found[inc2][inc]

                    if isinstance(weight, int):
                        weight = float(weight)
                    weight_array.append(weight)

            if len(weights_found) == len(influences_found):
                maya_lib.api.set_skin_weights(skin_cluster, weight_array, 0)

        if not new_way:

            mesh_description = nicename
            skin_cluster = cmds.skinCluster(influences,
                                            mesh,
                                            tsb=True,
                                            n=maya_lib.core.inc_name('skin_%s' % mesh_description)
                                            )[0]

            cmds.setAttr('%s.normalizeWeights' % skin_cluster, 0)

            maya_lib.deform.set_skin_weights_to_zero(skin_cluster)

            influence_index_dict = maya_lib.deform.get_skin_influences(skin_cluster, return_dict=True)

            progress_ui = maya_lib.core.ProgressBar('import skin', len(list(influence_dict.keys())))

            for influence in influences:
                orig_influence = influence
                if influence.count('|') > 1:
                    split_influence = influence.split('|')
                    if len(split_influence) > 1:
                        influence = split_influence[-1]

                message = 'importing skin mesh: %s,  influence: %s' % (short_name, influence)

                progress_ui.status(message)

                if 'weights' not in influence_dict[orig_influence]:
                    util.warning('Weights missing for influence %s' % influence)
                    return

                weights = influence_dict[orig_influence]['weights']

                if influence not in influence_index_dict:
                    continue

                index = influence_index_dict[influence]

                attr = '%s.weightList[*].weights[%s]' % (skin_cluster, index)

                for inc in range(0, len(weights)):

                    weight = float(weights[inc])

                    if weight == 0 or weight < 0.0001:
                        continue

                    attr = '%s.weightList[%s].weights[%s]' % (skin_cluster, inc, index)

                    cmds.setAttr(attr, weight)

                progress_ui.inc()

                if util.break_signaled():
                    break

                if progress_ui.break_signaled():
                    break

            progress_ui.end()

        cmds.skinCluster(skin_cluster, edit=True, normalizeWeights=1)
        cmds.skinCluster(skin_cluster, edit=True, forceNormalizeWeights=True)

        if blend_value is not None:
            maya_lib.deform.set_skin_blend_weights(skin_cluster, blend_value)
        if skin_attribute_dict:
            for attribute_name in skin_attribute_dict:
                skin_attribute_name = skin_cluster + '.' + attribute_name
                if maya_lib.core.exists(skin_attribute_name):
                    value = max(0, skin_attribute_dict[attribute_name])
                    cmds.setAttr(skin_attribute_name, value)

        self._progress_ui.status('Importing skin weights on: %s    - imported skin weights' % nicename)

        if transfer_mesh:
            self._progress_ui.status('Importing skin weights on: %s    - transferring skin weights' % nicename)
            util.show('Mesh topology mismatch. Transferring weights.')

            maya_lib.deform.skin_mesh_from_mesh(mesh, transfer_mesh, layer=True)
            cmds.delete(mesh)
            util.show('Done Transferring weights.')
            self._progress_ui.status('Importing skin weights on: %s    - transferred skin weights' % nicename)

        util.show('Imported skinCluster weights: %s' % short_name)

        return True

    @util.stop_watch_wrapper
    def import_data(self, filepath=None, selection=None):
        if selection is None:
            selection = []
        if util.is_in_maya():
            cmds.undoInfo(state=False)
            self._import_maya_data(filepath, selection)
        cmds.undoInfo(state=True)

    def export_data(self, comment, selection=None, single_file=False, version_up=True, blend_weights=True,
                    long_names=False):  # TODO: This needs to be broken apart as well.

        if selection is None:
            selection = []
        watch = util.StopWatch()
        watch.start('SkinWeightData.export_data', feedback=False)
        watch.feedback = True

        if selection is None:
            watch.end()
            util.warning('Nothing selected to export skin weights.'
                         ' Please select a mesh, curve, nurb surface or lattice with skin weights.')
            return

        if not selection:
            meshes = maya_lib.core.get_transforms_with_shape_of_type('mesh')
            curves = maya_lib.core.get_transforms_with_shape_of_type('nurbsCurve')
            surfaces = maya_lib.core.get_transforms_with_shape_of_type('nurbsSurface')
            lattices = maya_lib.core.get_transforms_with_shape_of_type('lattice')

            selection = meshes + curves + surfaces + lattices
            util.warning('Exporting skin clusters on meshes, nurbsCurves, nurbsSurfaces and lattices')

        found_one = False

        progress = maya_lib.core.ProgressBar('Exporting skin weights on:', len(selection))

        for thing in selection:

            if not thing:
                continue

            if not long_names:
                thing = cmds.ls(thing)[0]
            if long_names:
                thing = cmds.ls(thing, l=True)[0]

            progress.status('Exporting skin weights on %s ' % (maya_lib.core.get_basename(thing)))

            if maya_lib.core.is_a_shape(thing):
                if not long_names:
                    thing = cmds.listRelatives(thing, p=True)[0]
                if long_names:
                    thing = cmds.listRelatives(thing, p=True, f=True)[0]

            thing_filename = self._mesh_name_to_folder_name(thing)

            util.show('Exporting weights on: %s' % thing)

            skins = maya_lib.deform.find_deformer_by_type(thing, 'skinCluster', return_all=True)

            if not skins:
                util.warning('Skin export failed. No skinCluster found on %s.' % thing)
            else:
                start = 0
                for inc, skin in enumerate(skins, start):
                    path = self.get_file(inc)
                    found_one = True

                    geo_path = util_file.join_path(path, thing_filename)

                    if util_file.is_dir(geo_path, case_sensitive=True):
                        files = util_file.get_files(geo_path)

                        for filename in files:
                            util_file.delete_file(filename, geo_path)

                    else:
                        geo_path = util_file.create_dir(thing_filename, path)

                    if not geo_path:
                        util.error('Please check!'
                                   ' Unable to create skin weights directory: %s in %s' % (thing_filename, path))
                        continue

                    weights = maya_lib.deform.get_skin_weights(skin)

                    info_file = util_file.create_file('influence.info', geo_path)
                    settings_file = util_file.create_file('settings.info', geo_path)

                    info_lines = []
                    settings_lines = []
                    weights_dict = {}

                    for influence in weights:

                        if influence is None or influence == 'None':
                            continue

                        weight_list = weights[influence]

                        if not weight_list:
                            continue

                        if not single_file:
                            thread = LoadWeightFileThread()

                            influence_line = thread.run(influence, skin, weights[influence], geo_path)
                        else:
                            influence_name = maya_lib.deform.get_skin_influence_at_index(influence, skin)
                            sub_weights = weights[influence]

                            if not influence_name or not maya_lib.core.exists(influence_name):
                                continue

                            weights_dict[influence_name] = sub_weights

                            influence_position = cmds.xform(influence_name, q=True, ws=True, t=True)
                            influence_line = "{'%s' : {'position' : %s}}" % (influence_name, str(influence_position))

                        if influence_line:
                            info_lines.append(influence_line)

                    if single_file:
                        filepath = util_file.create_file('all.skin.weights', geo_path)

                        lines = ['%s=%s' % (key, str(weights_dict[key])) for key in weights_dict]
                        util_file.write_lines(filepath, lines)

                    util_file.write_lines(info_file, info_lines)

                    blend_weights_attr = '%s.blendWeights' % skin

                    if maya_lib.core.has_shape_of_type(thing, 'mesh'):
                        self._export_ref_obj(thing, geo_path)

                        verts, edges, faces = maya_lib.geo.get_vert_edge_face_count(thing)
                        verts1 = maya_lib.geo.get_face_vert_indices(thing, 0)
                        verts2 = maya_lib.geo.get_face_vert_indices(thing, -1)

                        settings_lines.append("['mesh info', %s]" % [verts, edges, faces, verts1, verts2])

                    if maya_lib.core.exists(blend_weights_attr) and blend_weights:
                        maya_lib.core.print_help('Exporting %s blend weights'
                                                 ' (for dual quaternion)' % maya_lib.core.get_basename(thing))

                        blend_weights = maya_lib.deform.get_skin_blend_weights(skin)

                        settings_lines.append("['blendWeights', %s]" % blend_weights)

                    export_attrs = ['skinningMethod', 'maintainMaxInfluences', 'maxInfluences']
                    for attribute_name in export_attrs:

                        attribute_path = '%s.%s' % (skin, attribute_name)

                        if not maya_lib.core.exists(attribute_path):
                            continue

                        attribute_value = max(0, cmds.getAttr(attribute_path))
                        settings_lines.append("['%s', %s]" % (attribute_name, attribute_value))

                    util_file.write_lines(settings_file, settings_lines)

                    mesh_folder = util_file.get_basename(geo_path)
                    deformer_folder = util_file.get_basename(util_file.get_dirname(geo_path))

                    util.show('Skin weights exported to folder: %s/%s' % (deformer_folder, mesh_folder))

            if progress.break_signaled():
                progress.end()
                break

            progress.next()

        if not found_one:
            progress.end()
            watch.end()
            util.warning('No skin weights found on selected.'
                         ' Please select a mesh, curve, nurb surface or lattice with skin weights.')

            return

        if found_one:
            maya_lib.core.print_help('skin weights exported.')

        if version_up:
            util_file.get_permission(path)
            version = util_file.VersionFile(path)
            version.save(comment)

        progress.end()
        watch.end()

    def get_skin_meshes(self):

        filepath = self.get_file()
        path = util_file.join_path(util_file.get_dirname(filepath), self.name)

        meshes = None

        if util_file.is_dir(path):
            meshes = util_file.get_folders(path)

        return meshes

    def remove_mesh(self, mesh):
        """

        Args:
            mesh (str):

        Returns:

        """
        filepath = self.get_file()
        path = util_file.join_path(util_file.get_dirname(filepath), self.name)

        util_file.delete_dir(mesh, path)

        test_path = util_file.join_path(path, mesh)

        return not util_file.is_dir(test_path)

    def delete_skin_clusters(self):

        scope = cmds.ls(type='skinCluster')
        cmds.delete(scope)

    def rename(self, new_name):
        old_name = self.name
        super(SkinWeightData, self).rename(new_name)

        if old_name == new_name:
            return True

        folders = util_file.get_folders(self.directory)

        for folder in folders:
            if folder.startswith('.'):
                continue

            new_folder = folder.replace(old_name, new_name)

            if new_folder == new_name:
                continue

            old_path = util_file.join_path(self.directory, folder)
            new_path = util_file.join_path(self.directory, new_folder)

            util_file.rename(old_path, new_path)

        return True


class LoadWeightFileThread(threading.Thread):

    def __init__(self):
        super(LoadWeightFileThread, self).__init__()

    def run(self, influence_index, skin, weights, path):

        influence_name = maya_lib.deform.get_skin_influence_at_index(influence_index, skin)

        if not influence_name or not maya_lib.core.exists(influence_name):
            return

        influence_filename = influence_name.replace(':', '-')
        filepath = util_file.create_file('%s.weights' % influence_filename, path)

        if not filepath:
            filepath = util_file.join_path(path, influence_name)
            util.warning('%s was not created.' % filepath)
            return

        if not util_file.is_file(filepath):
            util.warning('%s is not a valid path.' % filepath)
            return

        util_file.get_permission(filepath)

        util_file.write_lines(filepath, str(weights))

        influence_position = cmds.xform(influence_name, q=True, ws=True, t=True)
        return "{'%s' : {'position' : %s}}" % (influence_name, str(influence_position))


class ReadWeightFileThread(threading.Thread):

    def __init__(self, influence_dict, folder_path, influence):
        super(ReadWeightFileThread, self).__init__()

        self.influence_dict = influence_dict
        self.folder_path = folder_path
        self.influence = influence

    def run(self):

        influence_dict = self.influence_dict
        folder_path = self.folder_path
        influence = self.influence

        file_path = util_file.join_path(folder_path, influence)

        influence = influence.split('.')[0]
        influence = influence.replace('-', ':')

        lines = util_file.get_file_lines(file_path)

        if not lines:
            influence_dict[influence]['weights'] = None
            return influence_dict

        weights = json.loads(lines[0])

        if influence in influence_dict:
            influence_dict[influence]['weights'] = weights

        return influence_dict


class BlendshapeWeightData(MayaCustomData):

    def _data_name(self):
        return 'weights_blendShape'

    def _data_extension(self):
        return ''

    def _data_type(self):
        return 'maya.blend_weights'

    def export_data(self, comment=None, selection=None):

        if selection is None:
            selection = []
        path = self.get_file()

        util_file.create_dir(path)

        meshes = None
        curves = None
        surfaces = None
        if selection:
            meshes = maya_lib.geo.get_selected_meshes(selection)
            curves = maya_lib.geo.get_selected_curves(selection)
            surfaces = maya_lib.geo.get_selected_surfaces(selection)

        meshes += curves + surfaces  # TODO: Refactor, this should likely be within the if scope.

        blendshapes = []
        for mesh in meshes:
            blendshape = maya_lib.deform.find_deformer_by_type(mesh, 'blendShape', return_all=True)
            blendshapes.extend(blendshape)

        if not blendshapes:
            util.warning('No blendshapes to export')
            return

        for blendshape in blendshapes:

            blend = maya_lib.blendshape.BlendShape(blendshape)

            mesh_count = blend.get_mesh_count()
            targets = blend.get_target_names()
            blend_shape_name = maya_lib.core.maya_name_to_folder_name(blendshape)
            blendshape_path = util_file.create_dir(blend_shape_name, path)

            for target in targets:
                target_path = util_file.create_dir(target, blendshape_path)

                for inc in range(mesh_count):
                    weights = blend.get_weights(target, inc)

                    filename = util_file.create_file('mesh_%s.weights' % inc, target_path)
                    util_file.write_lines(filename, [str(weights)])

            for inc in range(mesh_count):
                weights = blend.get_weights(None, inc)

                filename = util_file.create_file('base_%s.weights' % inc, blendshape_path)
                util_file.write_lines(filename, [str(weights)])

        maya_lib.core.print_help('Exported %s data' % self.name)

    def import_data(self):

        path = self.get_file()

        folders = util_file.get_folders(path)

        new_folders = []
        for folder in folders:
            maya_name = maya_lib.core.folder_name_to_maya_name(folder)
            new_folders.append(maya_name)

        for folder in filter(lambda x: maya_lib.core.exists(x) and cmds.nodeType(x) == 'blendShape', new_folders):
            blendshape_name = folder
            blendshape_folder = maya_lib.core.maya_name_to_folder_name(blendshape_name)
            blendshape_path = util_file.join_path(path, blendshape_folder)

            base_files = util_file.get_files_with_extension('weights', blendshape_path)

            for filename in filter(lambda x: x.startswith('base'), base_files):
                filepath = util_file.join_path(blendshape_path, filename)
                lines = util_file.get_file_lines(filepath)

                weights = eval(lines[0])

                index = util.get_last_number(filename)
                blend = maya_lib.blendshape.BlendShape(blendshape_name)
                blend.set_weights(weights, mesh_index=index)

            targets = util_file.get_folders(blendshape_path)

            for target in filter(lambda x: maya_lib.core.exists('%s.%s' % (blendshape_name, x)), targets):
                target_path = util_file.join_path(blendshape_path, target)
                files = util_file.get_files_with_extension('weights', target_path)

                for filename in filter(lambda x: x.startswith('mesh'), files):
                    filepath = util_file.join_path(target_path, filename)
                    lines = util_file.get_file_lines(filepath)

                    weights = eval(lines[0])

                    index = util.get_last_number(filename)
                    blend = maya_lib.blendshape.BlendShape(blendshape_name)
                    blend.set_weights(weights, target, mesh_index=index)

        maya_lib.core.print_help('Imported %s data' % self.name)


class DeformerWeightData(MayaCustomData):
    """
    maya.deform_weights
    Export/Import weights of clusters and wire deformers.
    Will not work if cluster or wire deformer is affecting more than one piece of geo.
    """

    def _data_name(self):
        return 'weights_deformer'

    def _data_extension(self):
        return ''

    def _data_type(self):
        return 'maya.deform_weights'

    def export_data(self, comment=None, selection=None):

        if selection is None:
            selection = []
        path = self.get_file()

        util_file.create_dir(path)
        if selection:
            meshes = maya_lib.geo.get_selected_meshes(selection)
        else:
            meshes = maya_lib.core.get_transforms_with_shape_of_type('mesh')

        if not meshes:
            util.warning('No meshes found in selection with deformers.')
            return

        found_one = False
        visited = []
        for mesh in meshes:

            mesh_vert_count = len(maya_lib.geo.get_vertices(mesh))
            deformers = maya_lib.deform.find_all_deformers(mesh)

            if not deformers:
                util.warning('Did not find a weighted deformer on %s.' % mesh)
                continue

            for deformer in deformers:
                if deformer in visited:
                    found_one = True
                    continue
                if cmds.objectType(deformer, isAType='weightGeometryFilter'):

                    info_lines = []

                    indices = mel.eval('deformer -q -gi %s' % deformer)

                    filepath = util_file.create_file('%s.weights' % deformer, path)

                    if not filepath:
                        return

                    for weights in map(lambda x: maya_lib.deform.get_deformer_weights(deformer, x), indices):
                        all_one = True
                        for weight in weights:
                            if weight < 1.0:
                                all_one = False
                                break

                        if all_one:
                            weights = [1] * mesh_vert_count

                        info_lines.append(weights)

                        found_one = True
                        visited.append(deformer)

                    util_file.write_lines(filepath, info_lines)

                    util_file.get_permission(path)
                    version = util_file.VersionFile(path)
                    version.save(comment)

                    util.show('Exported weights on %s.' % deformer)

        if found_one:
            maya_lib.core.print_help('Exported %s data' % self.name)
        else:
            util.warning('Found no deformers to export weights.')

    def import_data(self, filepath=None):

        if not filepath:
            filepath = self.get_file()

        files = util_file.get_files(filepath)

        if not files:
            util.warning('Found nothing to import.')

        for filename in files:

            folder_path = util_file.join_path(filepath, filename)

            lines = util_file.get_file_lines(folder_path)

            deformer = filename.split('.')[0]

            util.show('Import deformer weights on %s' % deformer)

            if not maya_lib.core.exists(deformer):
                util.warning('%s does not exist. Could not import weights' % deformer)
                continue

            if not lines:
                continue

            geometry_indices = mel.eval('deformer -q -gi %s' % deformer)

            weights_list = []

            if lines:
                for inc, line in enumerate(filter(None, lines)):
                    try:
                        weights = eval(line)
                    except:
                        util.warning('Could not read weights on line %s' % inc)
                        continue
                    weights_list.append(weights)

            for weights_part, index in zip(weights_list, geometry_indices):

                maya_lib.deform.set_deformer_weights(weights_part, deformer, index)

                if not maya_lib.core.exists(deformer):
                    util.warning('Import failed: Deformer %s does not exist.' % deformer)

        maya_lib.core.print_help('Imported %s data' % self.name)


class MayaShadersData(CustomData):
    """
    maya.shaders
    Export/Import shaders.
    This only works for maya shaders. E.g. Blinn, Lambert, etc.
    """
    maya_ascii = 'mayaAscii'

    def _data_type(self):
        return 'maya.shaders'

    def _data_name(self):
        return 'shaders'

    def _data_extension(self):
        return ''

    def _get_info_dict(self, info_lines):
        info_dict = {}

        for shader_dict in map(eval, filter(None, info_lines)):
            for key in shader_dict:
                info_dict[key] = shader_dict[key]
        return info_dict

    def import_data(self, filepath=None, selection=None):  # TODO: This needs to be refactored as well.

        if selection is None:
            selection = []
        if filepath:
            path = filepath
        else:
            path = util_file.join_path(self.directory, self.name)

        files = util_file.get_files_with_extension('ma', path)

        info_file = util_file.join_path(path, 'shader.info')
        info_lines = util_file.get_file_lines(info_file)

        info_dict = {}
        for shader_dict in map(eval, filter(None, info_lines)):
            for key in shader_dict:
                info_dict[key] = shader_dict[key]

        bad_meshes = []

        at_least_one = False

        for filename in files:

            filepath = util_file.join_path(path, filename)

            engine = filename.split('.')[0]

            if engine not in info_dict:
                continue

            orig_engine = engine
            meshes = info_dict[orig_engine]

            if not meshes:
                continue

            if selection:
                found_one = False
                # TODO: Refactor this.
                found = []
                for thing in selection:
                    if maya_lib.core.is_a_shape(thing) and maya_lib.geo.is_a_mesh(thing):
                        mesh = maya_lib.core.get_basename(thing, remove_namespace=False, remove_attribute=True)
                        found.append(mesh)
                    else:
                        if maya_lib.geo.is_a_mesh(thing):
                            shapes = maya_lib.core.get_shapes(thing, 'mesh', no_intermediate=True)
                            for shape in shapes:
                                mesh = maya_lib.core.get_basename(shape, remove_namespace=False, remove_attribute=True)
                                found.append(mesh)

                if found:
                    # TODO: Refactor this.
                    for mesh in meshes:
                        if not found_one:
                            for thing in found:
                                if mesh == thing:
                                    found_one = True
                        if found_one:
                            break

                    if found_one:
                        meshes = found
                if not found_one:
                    continue
                else:
                    at_least_one = True

            found_meshes = {}

            track = maya_lib.core.TrackNodes()
            track.load('shadingEngine')

            util.show('Importing shader: %s' % filename)
            cmds.file(filepath, f=True, i=True, iv=True)

            new_engines = track.get_delta()
            engine = new_engines[0]

            for mesh in meshes:

                if not maya_lib.core.exists(mesh):

                    bad_mesh = mesh
                    if mesh.find('.f['):
                        bad_mesh = maya_lib.geo.get_mesh_from_face(mesh)

                    if bad_mesh not in bad_meshes:
                        util.warning('Could not find %s that %s was assigned to.' % (bad_mesh, engine))
                        bad_meshes.append(bad_mesh)

                    continue

                split_mesh = mesh.split('.')

                if len(split_mesh) > 1:
                    if split_mesh[0] not in found_meshes:
                        found_meshes[split_mesh[0]] = []

                    found_meshes[split_mesh[0]].append(mesh)

                if len(split_mesh) == 1:
                    if mesh not in found_meshes:
                        found_meshes[mesh] = mesh

            for mesh in found_meshes.values():
                all_mesh = cmds.ls(mesh, l=True)

                cmds.sets(all_mesh, e=True, forceElement=engine)

        if not at_least_one and selection:
            util.warning('No shaders found for selection')

    def export_data(self, comment, selection=None):

        if selection is None:
            selection = []
        shaders = cmds.ls(type='shadingEngine')

        path = util_file.join_path(self.directory, self.name)

        if selection:
            if not util_file.is_dir(path):
                util_file.create_dir(path)
            found = []
            for thing in filter(lambda x: maya_lib.geo.is_a_mesh(x), selection):
                mesh_shaders = maya_lib.shade.get_shading_engines_by_geo(thing)
                found.extend(mesh_shaders)

            if found:
                shaders = list(dict.fromkeys(found))
        else:
            util_file.refresh_dir(path, delete_directory=False)

        info_file = util_file.join_path(path, 'shader.info')

        info_dict = {}
        info_lines = []

        if not util_file.is_file(info_file):
            info_file = util_file.create_file('shader.info', path)
        else:
            temp_info_lines = util_file.get_file_lines(info_file)
            info_dict = self._get_info_dict(temp_info_lines)
            util_file.delete_file(info_file)
            info_file = util_file.create_file('shader.info', path)

        skip_shaders = ('initialParticleSE', 'initialShadingGroup')

        if not shaders:
            util.warning('No shaders found to export.')

        for key in filter(lambda x: x not in shaders, info_dict):
            info_lines.append("{'%s' : %s}" % (key, info_dict[key]))

        for shader in filter(lambda x: x not in skip_shaders, shaders):
            members = cmds.sets(shader, q=True)
            if not members:
                continue
            info_lines.append("{'%s' : %s}" % (shader, members))

            filepath = util_file.join_path(path, '%s.ma' % shader)

            if util_file.is_file(filepath):
                util_file.delete_file(util_file.get_basename(filepath), path)

            cmds.file(rename=filepath)

            cmds.select(shader, noExpand=True)

            selection = cmds.ls(sl=True)

            if selection:
                cmds.file(exportSelected=True,
                          prompt=False,
                          force=True,
                          pr=True,
                          type=self.maya_ascii)

        util_file.write_lines(info_file, info_lines)

        version = util_file.VersionFile(path)
        version.save(comment)

        maya_lib.core.print_help('Exported %s data' % self.name)


class AnimationData(MayaCustomData):
    """
    maya.animation
    Export/Import all the keyframes in a scene with their connection info.
    Will export/import blendWeighted as well.
    """

    def __init__(self, name=None):
        super(AnimationData, self).__init__(name)

        self.selection = None
        self.namespace = ''

    def _data_name(self):
        return 'keyframes'

    def _data_type(self):
        return 'maya.animation'

    def _data_extension(self):
        return ''

    def _get_keyframes(self, selection=None):

        if selection is None:
            selection = []
        key_selection = cmds.ls(sl=True, type='animCurve')

        selected_keys = []

        for thing in filter(lambda x: x not in key_selection, selection):
            sub_keys = cmds.keyframe(thing, q=True, name=True)
            if sub_keys:
                selected_keys += sub_keys

        if key_selection:
            selected_keys += key_selection

        if selected_keys:
            self.selection = True
            return selected_keys

        keyframes = cmds.ls(type='animCurve')
        return keyframes

    def _get_blend_weighted(self):
        blend_weighted = cmds.ls(type='blendWeighted')
        return blend_weighted

    def get_file(self):

        test_dir = util_file.join_path(self.directory, 'keyframes')

        if util_file.is_dir(test_dir):
            util_file.rename(test_dir, self._get_file_name())

        return super(AnimationData, self).get_file()

    def set_namespace(self, namespace_str):
        self.namespace = namespace_str

    def export_data(self, comment, selection=None):

        unknown = cmds.ls(type='unknown')

        if unknown:
            util.warning('Could not export keyframes. Unknown nodes found. Please remove unknowns first')
            return

        if selection is None:
            selection = []

        keyframes = self._get_keyframes(selection)
        if not keyframes:
            util.warning('No keyframes found to export.')

        if selection:
            util.warning('Exporting only selected keyframes')

        blend_weighted = self._get_blend_weighted()
        if blend_weighted:
            keyframes = keyframes + blend_weighted

        path = self.get_file()

        util_file.refresh_dir(path)

        info_file = util_file.create_file('animation.info', path)

        info_lines = []

        all_connections = []

        cmds.select(cl=True)

        select_keyframes = []

        for keyframe in keyframes:
            # TODO: Refactor this.
            if maya_lib.core.is_referenced(keyframe):
                continue
            node_type = cmds.nodeType(keyframe)
            if not maya_lib.core.exists(keyframe):
                continue

            inputs = []

            if not node_type == 'blendWeighted':
                inputs = maya_lib.attr.get_attribute_input('%s.input' % keyframe)

            outputs = maya_lib.attr.get_attribute_outputs('%s.output' % keyframe)

            if node_type.find('animCurveT') > -1:
                if not outputs:
                    continue
            if not node_type.find('animCurveT') > -1:
                if not outputs or not inputs:
                    continue

            select_keyframes.append(keyframe)

            connections = maya_lib.attr.Connections(keyframe)
            connections.disconnect()

            all_connections.append(connections)

            info_lines.append("{'%s' : {'output': %s, 'input': '%s'}}" % (keyframe, outputs, inputs))

        if not select_keyframes:
            maya_lib.core.print_warning('No keyframes found to export')
            return

        cmds.select(select_keyframes)

        filepath = util_file.join_path(path, 'keyframes.ma')
        cmds.file(rename=filepath)

        cmds.file(force=True, options='v=0;', typ='mayaAscii', es=True)

        for connection in all_connections:
            connection.connect()

        util_file.write_lines(info_file, info_lines)

        version = util_file.VersionFile(path)
        version.save(comment)

        maya_lib.core.print_help('Exported %s data.' % self.name)

    def import_data(self, filepath=None):  # TODO: This needs to be broken up.

        path = filepath

        if not path:
            path = self.get_file()

        if not util_file.is_dir(path):
            return

        filepath = util_file.join_path(path, 'keyframes.ma')

        if not util_file.is_file(filepath):
            maya_lib.core.print_warning('No keyframe data exported')
            return

        info_file = util_file.join_path(path, 'animation.info')

        if not util_file.is_file(info_file):
            return

        info_lines = util_file.get_file_lines(info_file)

        if not info_lines:
            return

        info_dict = {}

        for keyframe_dict in map(eval, filter(None, info_lines)):
            for key in keyframe_dict:
                if maya_lib.core.exists(key):
                    cmds.delete(key)
                info_dict[key] = keyframe_dict[key]

        cmds.file(filepath, f=True, i=True, iv=True)

        # TODO: Refactor
        for key in info_dict:
            keyframes = info_dict[key]

            outputs = keyframes['output']

            if outputs:
                for output in outputs:

                    if self.namespace:

                        current_namespace = maya_lib.core.get_namespace(output)

                        if current_namespace:
                            output.replace(current_namespace + ':', self.namespace + ':')
                        if not current_namespace:
                            output = self.namespace + ':' + output

                    if not maya_lib.core.exists(output):
                        util.warning('Could not find keyframed: %s' % output)

                        continue

                    locked = cmds.getAttr(output, l=True)
                    if locked:
                        try:
                            cmds.setAttr(output, l=False)
                        except Exception:
                            util.warning('\tCould not unlock %s' % output)

                    try:
                        cmds.connectAttr('%s.output' % key, output)
                    except:
                        util.warning('\tCould not connect %s.output to %s' % (key, output))

                    if locked:
                        try:
                            cmds.setAttr(output, l=True)
                        except Exception:
                            pass

            input_attr = keyframes['input']

            if input_attr:

                if not maya_lib.core.exists(input_attr):
                    continue
                try:
                    cmds.connectAttr(input_attr, '%s.input' % key)
                except:
                    util.warning('\tCould not connect %s to %s.input' % (input_attr, key))

        maya_lib.core.print_help('Imported %s data.' % self.name)

        return list(info_dict.keys())


class ControlAnimationData(AnimationData):
    """
    maya.control_animation
    Only import/export keframes on controls.
    Good for saving out poses.
    """

    def _data_name(self):
        return 'keyframes_control'

    def _data_type(self):
        return 'maya.control_animation'

    def _get_keyframes(self, selection=None):

        if selection is None:
            selection = []
        if selection:
            controls = [thing for thing in selection if maya_lib.rigs_util.is_control(thing)]
        else:
            controls = maya_lib.rigs_util.get_controls()

        keyframes = []

        for sub_keyframes in filter(None,
                                    map(lambda x: maya_lib.anim.get_input_keyframes(x, node_only=True), controls)):
            keyframes.extend(sub_keyframes)

        return keyframes

    def _get_blend_weighted(self):

        return None


class AtomData(MayaCustomData):
    """
    Not in use.
    """

    def _data_name(self):
        return 'animation'

    def _data_extension(self):
        return 'atom'

    def _data_type(self):
        return 'maya.atom'

    def export_data(self, comment):
        nodes = cmds.ls(type='transform')
        cmds.select(nodes)

        file_name = '%s.%s' % (self.name, self.data_extension)
        file_path = util_file.join_path(self.directory, file_name)

        options = ('precision=8;'
                   'statics=0;'
                   'baked=1;'
                   'sdk=1;'
                   'constraint=0;'
                   'animLayers=1;'
                   'selected=selectedOnly;'
                   'whichRange=1;'
                   'range=1:10;'
                   'hierarchy=none;'
                   'controlPoints=0;'
                   'useChannelBox=1;'
                   'options=keys;'
                   'copyKeyCmd=-animation objects -option keys -hierarchy none -controlPoints 0')

        if not cmds.pluginInfo('atomImportExport', query=True, loaded=True):
            cmds.loadPlugin('atomImportExport.mll')

        mel.eval('vtool -force -options "%s" -typ "atomExport" -es "%s"' % (options, file_path))

        version = util_file.VersionFile(file_path)
        version.save(comment)

    def import_data(self):

        nodes = cmds.ls(type='transform')
        cmds.select(nodes)

        file_name = '%s.%s' % (self.name, self.data_extension)
        file_path = util_file.join_path(self.directory, file_name)

        if not cmds.pluginInfo('atomImportExport', query=True, loaded=True):
            cmds.loadPlugin('atomImportExport.mll')

        options = ';;targetTime=3;option=insert;match=hierarchy;;selected=selectedOnly;search=;replace=;prefix=;suffix=;'

        mel.eval('vtool -import -type "atomImport" -ra true'
                 ' -namespace "test" -options "%s" "%s"' % (options, file_path))

        self._center_view()


class PoseData(MayaCustomData):
    """
    maya.pose
    Export/Import pose correctives.
    """
    maya_binary = 'mayaBinary'
    maya_ascii = 'mayaAscii'

    def _data_name(self):
        return 'correctives'

    def _data_extension(self):
        return ''

    def _data_type(self):
        return 'maya.pose'

    def _save_file(self, filepath):
        cmds.file(rename=filepath)
        # ch     chn     con     exp     sh
        cmds.file(exportSelected=True, prompt=False, force=True, pr=True, ch=False, chn=True, exp=True, con=False,
                  sh=False, stx='never', typ=self.maya_ascii)

    def _import_file(self, filepath):
        if util_file.is_file(filepath):
            util_file.get_permission(filepath)
            cmds.file(filepath, f=True, i=True, iv=True, shd='shadingNetworks')
        else:
            mel.eval('warning "File does not exist"')

    def _filter_inputs(self, inputs):
        for node in filter(lambda x: maya_lib.core.exists(x), inputs):
            if util.get_maya_version() > 2014:
                if cmds.nodeType(node) == 'hyperLayout':
                    if node == 'hyperGraphLayout':
                        continue

                    cmds.delete(node)

    def _get_inputs(self, pose):

        if not pose:
            return []

        sub_inputs = self._get_sub_inputs(pose)

        inputs = maya_lib.attr.get_inputs(pose)
        outputs = maya_lib.attr.get_outputs(pose)

        if inputs:
            inputs.append(pose)
        else:
            inputs = [pose]

        if outputs:
            inputs = inputs + outputs

        if sub_inputs:
            inputs = inputs + sub_inputs

        return inputs

    def _get_sub_inputs(self, pose):

        manager = maya_lib.corrective.PoseManager()
        manager.set_pose_group(pose)

        sub_poses = manager.get_poses()
        inputs = []
        if sub_poses is None:
            return inputs
        for sub_inputs in map(self._get_inputs, sub_poses):
            inputs = inputs + sub_inputs

        return inputs

    def _select_inputs(self, pose):

        inputs = self._get_inputs(pose)

        cmds.select(cl=True)
        cmds.select(inputs, ne=True)

        return inputs

    def export_data(self, comment):
        unknown = cmds.ls(type='unknown')

        if unknown:

            value = cmds.confirmDialog(title='Unknown Nodes!',
                                       message='Unknown nodes usually happen when a plugin that was being used'
                                               ' is not loaded.\nLoad the missing plugin, and the unknown nodes'
                                               ' could become valid.\n\nDelete unknown nodes?\n',
                                       button=['Yes', 'No'], defaultButton='Yes', cancelButton='No', dismissString='No')

            if value == 'Yes':
                maya_lib.core.delete_unknown_nodes()

        dirpath = self.get_file()

        if util_file.is_dir(dirpath):
            util_file.delete_dir(dirpath)

        dir_path = util_file.create_dir(dirpath)

        pose_manager = maya_lib.corrective.PoseManager()
        poses = pose_manager.get_poses()

        if not poses:
            util.warning('Found no poses to export.')
            return

        poses.append('pose_gr')

        pose_manager.set_pose_to_default()
        pose_manager.detach_poses()

        util.show('Exporting these top poses: %s' % poses)

        for pose in poses:

            util.show('----------------------------------------------')
            util.show('Exporting pose: %s' % pose)

            cmds.editDisplayLayerMembers("defaultLayer", pose)

            parent = None
            rels = None

            parent = cmds.listRelatives(pose, p=True)

            if parent:
                cmds.parent(pose, w=True)

            if pose == 'pose_gr':
                rels = cmds.listRelatives(pose)
                cmds.parent(rels, w=True)

            # this is needed for cases where the hyperGraphLayout is connected to the node and other nodes.
            outputs = maya_lib.attr.get_attribute_outputs('%s.message' % pose)

            if outputs:
                for output_value in outputs:
                    cmds.disconnectAttr('%s.message' % pose, output_value)

            inputs = self._select_inputs(pose)

            self._filter_inputs(inputs)

            path = util_file.join_path(dir_path, '%s.ma' % pose)

            try:
                self._save_file(path)
            except:
                util.warning('Could not export pose: %s. Probably because of unknown nodes.' % pose)

            if parent:
                cmds.parent(pose, parent[0])

            if rels:
                cmds.parent(rels, 'pose_gr')

        pose_manager.attach_poses()

        version = util_file.VersionFile(dir_path)
        version.save(comment)

        maya_lib.core.print_help('Exported %s data.' % self.name)

    def import_data(self, namespace=''):

        path = self.get_file()

        util_file.get_permission(path)

        if not path or not util_file.is_dir(path):
            return

        pose_files = util_file.get_files(path)
        if not pose_files:
            return

        poses = []
        end_poses = []

        cmds.renderThumbnailUpdate(False)

        for pose_file in pose_files:

            if os.environ.get('VETALA_RUN') == 'True':
                # stop doesn't get picked up when files are loading.
                if os.environ.get('VETALA_STOP') == 'True':
                    break

            if not pose_file.endswith('.ma') and not pose_file.endswith('.mb'):
                continue

            pose_path = util_file.join_path(path, pose_file)

            if util_file.is_file(pose_path):

                split_name = pose_file.split('.')

                pose = split_name[0]

                if maya_lib.core.exists(pose):
                    cmds.delete(pose)

                if not maya_lib.core.exists(pose):

                    try:
                        self._import_file(pose_path)
                    except:
                        util.warning('Trouble importing %s' % pose_path)

                    if pose != 'pose_gr':
                        pose_type = cmds.getAttr('%s.type' % pose)

                        if pose_type == 'combo':
                            end_poses.append(pose)
                        else:
                            poses.append(pose)

        pose_manager = maya_lib.corrective.PoseManager()
        if namespace:
            pose_manager.set_namespace(namespace)

        if end_poses:
            poses = poses + end_poses

        if maya_lib.core.exists('pose_gr') and poses:
            cmds.parent(poses, 'pose_gr')

        poses = pose_manager.get_poses(all_descendents=True)

        pose_manager.attach_poses(poses)

        pose_manager.create_pose_blends(poses)

        pose_manager.set_pose_to_default()

        maya_lib.core.print_help('Imported %s data.' % self.name)

        cmds.dgdirty(a=True)
        cmds.renderThumbnailUpdate(True)


class MayaAttributeData(MayaCustomData):
    """
    maya.attributes
    Export attribute data on selected nodes.
    Import attribute data on all nodes exported, unless something is selected.
    """

    def __init__(self, name=None):
        super(MayaAttributeData, self).__init__(name)

        self.channel_box_only = False
        self.exclude_shapes = False

    def _data_name(self):
        return 'attributes'

    def _data_type(self):
        return 'maya.attributes'

    def _data_extension(self):
        return ''

    def _get_scope(self, selection=None):

        if selection is None:
            selection = []
        if not selection:
            util.warning('Nothing selected. Please select at least one node to export attributes.')
            return

        return selection

    def _get_attributes(self, node, channel_box_only=False):
        if channel_box_only:
            keyable_attrs = cmds.listAttr(node, scalar=True, m=True, k=True) or []
            channelbox_attrs = cmds.listAttr(node, scalar=True, m=True, channelBox=True) or []
            attributes = list(set(keyable_attrs + channelbox_attrs))
        else:
            attributes = cmds.listAttr(node, scalar=True, m=True, array=True) or []
        removeables = ('dofMask', 'inverseScaleX', 'inverseScaleY', 'inverseScaleZ')
        attributes.sort()
        found = [attribute for attribute in attributes
                 if attribute not in removeables]

        return found

    def _get_shapes(self, node):
        shapes = maya_lib.core.get_shapes(node)
        return shapes

    def _get_shape_attributes(self, shape, channel_box_only=False):

        return self._get_attributes(shape, channel_box_only)

    def import_data(self, filepath=None, selection=None):
        """
        This will import all nodes saved to the data folder.
        You may need to delete folders of nodes you no longer want to import.
        """

        if selection is None:
            selection = []
        path = filepath
        if not path:
            path = self.get_file()

        bad = False

        if selection:
            files = [maya_lib.core.maya_name_to_folder_name(thing) for thing in selection]
        else:
            files = util_file.get_files_with_extension('data', path)

        for filename in files:
            if not filename.endswith('.data'):
                filename = '%s.data' % filename

            filepath = util_file.join_path(path, filename)

            if not util_file.is_file(filepath):
                continue

            node_name = filename.split('.')[0]
            node_name = maya_lib.core.folder_name_to_maya_name(node_name)

            if not maya_lib.core.exists(node_name):
                util.warning('Skipping attribute import for %s. It does not exist.' % node_name)
                bad = True
                continue

            lines = util_file.get_file_lines(filepath)

            for line_list in map(eval, filter(None, lines)):
                attribute = '%s.%s' % (node_name, line_list[0])

                if not maya_lib.core.exists(attribute):
                    util.warning('%s does not exists. Could not set value.' % attribute)
                    bad = True
                    continue

                if maya_lib.attr.is_locked(attribute):
                    continue
                if maya_lib.attr.is_connected(attribute):

                    if not maya_lib.attr.is_keyed(attribute):
                        continue

                if line_list[1] is None:
                    continue

                try:
                    attr_type = cmds.getAttr(attribute, type=True)
                    if attr_type.find('Array') > -1:
                        cmds.setAttr(attribute, line_list[1], type=attr_type)
                    else:
                        cmds.setAttr(attribute, line_list[1])
                except:
                    util.warning('\tCould not set %s to %s.' % (attribute, line_list[1]))

        cmds.select(selection)

        if bad:
            maya_lib.core.print_help('Imported Attributes with some warnings')
        else:
            maya_lib.core.print_help('Imported Attributes')

    def export_data(self, comment, selection=None):
        """
        This will export only the currently selected nodes.
        """

        if selection is None:
            selection = []
        path = self.get_file()
        if not util_file.is_dir(path):
            util_file.create_dir(path)

        scope = self._get_scope(selection)
        if not scope:
            return

        for thing in scope:

            maya_lib.core.print_help('Exporting attributes on %s' % thing)

            filename = maya_lib.core.maya_name_to_folder_name(thing)
            filename = util_file.create_file('%s.data' % filename, path)

            lines = []

            attributes = self._get_attributes(thing, channel_box_only=self.channel_box_only)

            shapes = self._get_shapes(thing)

            if shapes and not self.exclude_shapes:
                shape = shapes[0]
                shape_attributes = self._get_shape_attributes(shape, self.channel_box_only)

                if shape_attributes:
                    new_set = set(attributes).union(shape_attributes)

                    attributes = list(new_set)

            if not attributes:
                continue

            for attribute in attributes:

                attribute_name = '%s.%s' % (thing, attribute)

                try:
                    value = cmds.getAttr(attribute_name)
                except:
                    continue

                lines.append("[ '%s', %s ]" % (attribute, value))

            util_file.write_lines(filename, lines)

        maya_lib.core.print_help('Exported %s data' % self.name)

    def set_channel_box_only(self, channel_box_only):
        """
        Set whether to export only channel box attributes.
        """
        self.channel_box_only = channel_box_only
        self.settings.set('channel box only', channel_box_only)

    def set_exclude_shapes(self, export_shapes):
        """
        Set whether to export shape attributes as well.
        """
        self.exclude_shapes = export_shapes
        self.settings.set('exclude shapes', export_shapes)


class MayaControlAttributeData(MayaAttributeData):

    def _data_name(self):
        return 'control_values'

    def _data_type(self):
        return 'maya.control_values'

    def _data_extension(self):
        return ''

    def _get_attributes(self, node, channel_box_only=False):
        attributes = cmds.listAttr(node, scalar=True, m=True, k=True)
        return attributes

    def _get_scope(self, selection=None):

        if selection is None:
            selection = []
        if selection:
            controls = [thing for thing in selection if maya_lib.rigs_util.is_control(thing)]
        else:
            controls = maya_lib.rigs_util.get_controls()

        if not controls:
            util.warning('No controls found to export attributes.')
            return

        return controls

    def _get_shapes(self, node):
        return []


class MayaControlRotateOrderData(MayaControlAttributeData):

    def _data_name(self):
        return 'control_rotateOrder'

    def _data_type(self):
        return 'maya.control_rotateorder'

    def _get_attributes(self, node):
        attributes = ['rotateOrder']
        return attributes


class MayaFileData(MayaCustomData):
    maya_binary = 'mayaBinary'
    maya_ascii = 'mayaAscii'
    check_after_save = True

    def _data_name(self):
        return 'maya_file'

    def __init__(self, name=None):
        super(MayaFileData, self).__init__(name)

        self.maya_file_type = self._set_maya_file_type()

        if util.is_in_maya() and not maya_lib.core.is_batch():
            pre_save_initialized = os.environ.get('VETALA_PRE_SAVE_INITIALIZED')
            if pre_save_initialized == 'False':
                maya_lib.api.start_check_after_save(self._check_after_save)
                util.set_env('VETALA_PRE_SAVE_INITIALIZED', 'True')

    def _check_after_save(self, client_data):

        if not self.check_after_save:
            return

        filepath = cmds.file(q=True, sn=True)

        version = util_file.VersionFile(filepath)

        dirpath = util_file.get_dirname(filepath)

        if util_file.VersionFile(dirpath).has_versions():
            comment = 'Automatically versioned up with Maya save.'

            version.save(comment)

            version = version.get_version_numbers()[-1]
            util.set_env('VETALA_SAVE_COMMENT', '')
            maya_lib.core.print_help('version %s saved!' % version)

    def _data_type(self):
        return 'maya.vtool'

    def _set_maya_file_type(self):

        return self.maya_binary

    def _clean_scene(self):

        util.show('Clean Scene')

        maya_lib.core.delete_turtle_nodes()

        if util.get_maya_version() > 2014:
            maya_lib.core.delete_garbage()
            maya_lib.core.remove_unused_plugins()

    def _after_open(self):

        maya_lib.geo.smooth_preview_all(False)
        self._center_view()

        self._load_maya_project_settings()

    def _load_maya_project_settings(self):
        # probably should not dig up to the process like this
        data_dir = util_file.get_dirname(self.directory)
        process_dir = util_file.get_dirname(data_dir)
        settings = util_file.SettingsFile()
        settings.set_directory(process_dir, 'settings.json')

        if settings.get('Maya Use Camera Settings'):

            focal_length = settings.get('Maya Focal Length')
            if not focal_length:
                focal_length = 35
            cmds.setAttr('persp.focalLength', focal_length)

            near = settings.get('Maya Near Clip Plane')
            if not near:
                near = 0.1
            cmds.setAttr('persp.nearClipPlane', near)

            far = settings.get('Maya Far Clip Plane')
            if not far:
                far = 10000
            cmds.setAttr('persp.farClipPlane', far)

    def _prep_scene_for_export(self):
        outliner_sets = maya_lib.core.get_outliner_sets()
        top_nodes = maya_lib.core.get_top_dag_nodes()
        controllers = cmds.ls(type='controller')

        found = [controller for controller in controllers
                 if maya_lib.attr.get_attribute_input('%s.ControllerObject' % controller, node_only=True)]

        to_select = outliner_sets + top_nodes + found

        if not to_select:
            to_select = ['persp', 'side', 'top', 'front']

        cmds.select(to_select, r=True, ne=True)

    def _handle_unknowns(self):

        unknown = cmds.ls(type='unknown')

        if unknown:

            value = cmds.confirmDialog(title='Unknown Nodes!',
                                       message='Unknown nodes usually happen when a plugin that was being used is not loaded.\nLoad the missing plugin, and the unknown nodes could become valid.\n\nDelete unknown nodes?\n',
                                       button=['Yes', 'No'], defaultButton='Yes', cancelButton='No', dismissString='No')

            if value == 'Yes':
                maya_lib.core.delete_unknown_nodes()
            elif value == 'No':
                if self.maya_file_type == self.maya_binary:
                    cmds.warning('\tThis file contains unknown nodes. Try saving as maya ascii instead.')

    def import_data(self, filepath=None):

        if not util.is_in_maya():
            util.warning('Data must be accessed from within maya.')
            return

        import_file = filepath

        if not import_file:

            filepath = self.get_file()

            if not util_file.is_file(filepath):
                return

            import_file = filepath

        track = maya_lib.core.TrackNodes()
        track.load('transform')

        maya_lib.core.import_file(import_file)
        self._after_open()

        transforms = track.get_delta()
        top_transforms = maya_lib.core.get_top_dag_nodes_in_list(transforms)

        return top_transforms

    def open(self, filepath=None):

        if not util.is_in_maya():
            util.warning('Data must be accessed from within maya.')
            return

        open_file = None

        if filepath:
            open_file = filepath

        if not open_file:

            filepath = self.get_file()

            if not util_file.is_file(filepath):
                util.warning('Could not open file: %s' % filepath)
                return

            open_file = filepath

        maya_lib.core.print_help('Opening: %s' % open_file)

        try:
            cmds.file(open_file,
                      f=True,
                      o=True,
                      iv=True,
                      pr=True)

        except:

            util.error(traceback.format_exc())
        self._after_open()

        top_transforms = maya_lib.core.get_top_dag_nodes(exclude_cameras=True)
        return top_transforms

    def save(self, comment):

        if not util.is_in_maya():
            util.warning('Data must be accessed from within maya.')
            return

        if not comment:
            comment = '-'

        util.set_env('VETALA_SAVE_COMMENT', comment)

        filepath = self.get_file()
        if util_file.exists(filepath):
            util_file.get_permission(filepath)

        self._handle_unknowns()

        self._clean_scene()

        # TODO: not sure if this ever gets used?...
        if not filepath.endswith('.mb') and not filepath.endswith('.ma'):

            filepath = cmds.workspace(q=True, rd=True)

            if self.maya_file_type == self.maya_ascii:
                filepath = cmds.fileDialog2(ds=1, fileFilter="Maya Ascii (*.ma)", dir=filepath)
            elif self.maya_file_type == self.maya_binary:
                filepath = cmds.fileDialog2(ds=1, fileFilter="Maya Binary (*.mb)", dir=filepath)

            if filepath:
                filepath = filepath[0]

        # there is an automation that runs when a maya save happens to version up.
        # this will avoid that automation version things up here.
        # versioning up for this save is handled below.
        MayaFileData.check_after_save = False
        saved = maya_lib.core.save(filepath)
        MayaFileData.check_after_save = True

        if saved:
            version = util_file.VersionFile(filepath)
            version.save(comment)

            thumbnail_path = util_file.get_dirname(filepath)
            create_data_thumbnail(thumbnail_path)

            maya_lib.core.print_help('Saved %s data.' % self.name)
            return True

        return False

    def export_data(self, comment, selection=None):

        if not util.is_in_maya():
            util.warning('Data must be accessed from within maya.')
            return

        filepath = self.get_file()

        self._handle_unknowns()

        self._clean_scene()

        cmds.file(rename=filepath)

        thumbnail_selection = False

        if selection:
            selection = maya_lib.core.remove_non_existent(selection)
            cmds.select(selection, r=True)
            thumbnail_selection = True
        else:
            self._prep_scene_for_export()

        try:
            cmds.file(exportSelected=True,
                      prompt=False,
                      force=True,
                      pr=True,
                      ch=True,
                      chn=True,
                      exp=True,
                      con=True,
                      stx='always',
                      type=self.maya_file_type)
        except:

            status = traceback.format_exc()
            util.error(status)

            if not maya_lib.core.is_batch():
                cmds.confirmDialog(message='Warning:\n\n Vetala was unable to export!', button='Confirm')

            permission = util_file.get_permission(filepath)

            if not permission:
                maya_lib.core.print_error('Could not get write permission.')
            return False

        version = util_file.VersionFile(filepath)
        version.save(comment)

        thumbnail_path = util_file.get_dirname(filepath)
        create_data_thumbnail(thumbnail_path, thumbnail_selection)

        maya_lib.core.print_help('Exported %s data.' % self.name)
        return True

    def reference(self, filepath=None):
        self.maya_reference_data(filepath)

    def maya_reference_data(self, filepath=None):

        if not util.is_in_maya():
            util.warning('Data must be accessed from within maya.')
            return

        if not filepath:
            filepath = self.get_file()

        track = maya_lib.core.TrackNodes()
        track.load('transform')

        maya_lib.core.reference_file(filepath)

        transforms = track.get_delta()
        top_transforms = maya_lib.core.get_top_dag_nodes_in_list(transforms)

        return top_transforms

    def set_directory(self, directory):
        super(MayaFileData, self).set_directory(directory)

        self.filepath = util_file.join_path(directory, '%s.%s' % (self.name, self.data_extension))


class MayaBinaryFileData(MayaFileData):

    def _data_type(self):
        return 'maya.binary'

    def _data_extension(self):
        return 'mb'

    def _set_maya_file_type(self):
        return self.maya_binary


class MayaAsciiFileData(MayaFileData):

    def _data_type(self):
        return 'maya.ascii'

    def _data_extension(self):
        return 'ma'

    def _set_maya_file_type(self):
        return self.maya_ascii


class MayaShotgunFileData(MayaFileData):

    def __init__(self, name=None):
        super(MayaShotgunFileData, self).__init__(name)

    def _data_name(self):
        return 'shotgun_link'

    def _data_type(self):
        return 'maya.shotgun'

    def _get_filepath(self, publish_path=False):

        project, asset_type, asset, step, task, custom, asset_is_name = self.read_state()

        if publish_path:
            template = 'Publish Template'
        else:
            template = 'Work Template'

        util.show('Getting Shotgun directory at: project: %s type: %s asset: %s step: %s task: %s custom: %s' % (
            project, asset_type, asset, step, task, custom))
        util.show('Using Vetala setting: %s' % template)

        if publish_path:
            filepath = util_shotgun.get_latest_file(project, asset_type, asset, step, publish_path, task, custom,
                                                    asset_is_name)
        else:
            filepath = util_shotgun.get_next_file(project, asset_type, asset, step, publish_path, task, custom,
                                                  asset_is_name)

        util.show('Vetala got the following directory from Shotgun: %s' % filepath)

        if not filepath:
            util.warning('Vetala had trouble finding a file')

        util.show('Final path Vetala found at Shtogun path: %s' % filepath)

        self.filepath = filepath

    def get_file(self):

        return self.filepath

    def write_state(self, project, asset_type, asset, step, task, custom, asset_is_name):

        if not self.directory:
            return

        filepath = util_file.create_file('shotgun.info', self.directory)

        lines = ['project=%s' % project,
                 'asset_type=%s' % asset_type,
                 'asset=%s' % asset,
                 'step=%s' % step,
                 'task=%s' % task,
                 'custom=%s' % custom,
                 'asset_is_name=%s' % asset_is_name]

        util_file.write_lines(filepath, lines)

    def read_state(self):

        filepath = util_file.join_path(self.directory, 'shotgun.info')

        if not util_file.is_file(filepath):
            return None, None, None, None, None, None, None

        lines = util_file.get_file_lines(filepath)

        found = [None, None, None, None, None, None, None]

        for split_line in map(lambda x: x.split('='), lines):
            if split_line[0] == 'project':
                found[0] = split_line[1]
            elif split_line[0] == 'asset_type':
                found[1] = split_line[1]
            elif split_line[0] == 'asset':
                found[2] = split_line[1]
            elif split_line[0] == 'step':
                found[3] = split_line[1]
            elif split_line[0] == 'task':
                found[4] = split_line[1]
            elif split_line[0] == 'custom':
                found[5] = split_line[1]
            elif split_line[0] == 'asset_is_name':
                found[6] = split_line[1]

        return found

    def reference(self):

        self._get_filepath(publish_path=True)
        super(MayaShotgunFileData, self).maya_reference_data()

    def open(self):

        self._get_filepath(publish_path=True)
        super(MayaShotgunFileData, self).open()

    def import_data(self, filepath=None):
        self._get_filepath(publish_path=True)

        super(MayaShotgunFileData, self).import_data()

    def save(self):

        self._get_filepath(publish_path=False)
        self.filepath = self.get_file()

        if not self.filepath:
            util.warning('Could not save shotgun link. Please save through shotgun ui.')
            return

        util_file.get_permission(self.filepath)

        self._handle_unknowns()

        self._clean_scene()

        filepath = self.filepath

        if not filepath:
            util.warning('Could not save shotgun link. Please save through shotgun ui.')
            return

        util.show('Attempting shotgun save to: %s' % filepath)

        # not sure if this ever gets used?...
        if not filepath.endswith('.mb') and not filepath.endswith('.ma'):

            if not util_file.is_dir(filepath):

                filepath = util_file.get_dirname(filepath)

                if not util_file.is_dir(filepath):
                    filepath = cmds.workspace(q=True, rd=True)

            if self.maya_file_type == self.maya_ascii:
                filepath = cmds.fileDialog2(ds=1, fileFilter="Maya Ascii (*.ma)", dir=filepath)
            elif self.maya_file_type == self.maya_binary:
                filepath = cmds.fileDialog2(ds=1, fileFilter="Maya Binary (*.mb)", dir=filepath)

            if filepath:
                filepath = filepath[0]

        saved = maya_lib.core.save(filepath)

        if saved:
            maya_lib.core.print_help('Saved %s data.' % self.name)
            return True

        return False

    def get_projects(self):
        projects = util_shotgun.get_projects()

        if projects:
            found = [project['name'] for project in projects]
            found.sort()
        else:
            found = ['No projects found']

        return found

    def get_assets(self, project, asset_type=None):
        assets = util_shotgun.get_assets(project, asset_type)

        found = {}

        if assets:
            for asset in assets:
                if asset['sg_asset_type'] not in found:
                    found[asset['sg_asset_type']] = []
                found[asset['sg_asset_type']].append(asset['code'])
        else:
            found['No asset_type'] = ['No assets found']

        return found

    def get_asset_steps(self):
        steps = util_shotgun.get_asset_steps()
        if steps:
            found = [[step['code'], step['short_name']] for step in steps]
        else:
            found = [['No steps found']]

        return found

    def get_asset_tasks(self, project, asset_step, asset_type, asset_name):
        tasks = util_shotgun.get_asset_tasks(project, asset_step, asset_type, asset_name)
        if tasks:
            found = [[task['content']] for task in tasks]
        else:
            found = [['No tasks found']]

        return found

    def has_api(self):
        if not util_shotgun.sg:
            return False
        return True


class ContextData(CustomData):

    def _data_name(self):
        return 'context'

    def _data_extension(self):
        return ''

    def _data_type(self):
        return 'agnostic.context'


class HoudiniFileData(CustomData):

    def _data_name(self):
        return 'houdini_file'

    def _data_type(self):
        return 'houdini.file'

    def _data_extension(self):
        return 'hip'

    def save(self, comment=''):

        filepath = self.get_file()
        houdini_lib.core.save(filepath)

    def export_data(self):

        filepath = self.get_file()
        houdini_lib.core.save(filepath)

    def open(self):
        filepath = self.get_file()
        houdini_lib.core.load(filepath)

    def import_data(self):

        filepath = self.get_file()
        houdini_lib.core.merge(filepath)


class HoudiniNodeData(CustomData):

    def _data_name(self):
        return 'houdini_nodes'

    def _data_type(self):
        return 'houdini.node'

    def _data_extension(self):
        return ''

    def export_data(self, comment='', selection=[]):

        filepath = self.get_file()
        houdini_lib.core.export_nodes(filepath, selection)

    def import_data(self, context=None):

        filepath = self.get_file()
        houdini_lib.core.import_nodes(filepath, context)


class UnrealFileData(CustomData):

    def _data_name(self):
        return 'unreal_file'

    def _data_type(self):
        return 'unreal.file'

    def _data_extension(self):
        return 'uasset'


class UnrealGraphData(CustomData):

    def _data_name(self):
        return 'unreal_graph'

    def _data_type(self):
        return 'unreal.graph'

    def _data_extension(self):
        return ''

    def import_data(self, filepath=None):  # TODO: Refactor
        import_file = filepath

        if not import_file:

            filepath = self.get_file()

            if not util_file.is_dir(filepath):
                return

            import_file = filepath

        files = util_file.get_files_with_extension('data', import_file, fullpath=True, filter_text=False)

        current_control_rig = unreal_lib.util.get_current_control_rig()

        unreal_lib.util.add_construct_graph()
        unreal_lib.util.add_forward_solve()
        unreal_lib.util.add_backward_graph()

        models = current_control_rig.get_all_models()

        model_dict = {}

        for model in models:
            model_name = model.get_graph_name()
            model_dict[model_name] = model

        controller_dict = {}

        run_first = []
        run_last = []

        for filepath in files:
            name = util_file.get_basename_no_extension(filepath)

            current_model = None

            if name in model_dict:
                current_model = model_dict[name]
            else:

                if name.find('Backwards Solve Graph') > -1:
                    current_model = unreal_lib.util.add_backward_graph()
                if name.find('Construction Event Graph') > -1:
                    current_model = unreal_lib.util.add_construct_graph()

            controller = None
            if not current_model:
                controller = current_control_rig.get_controller()

            if current_model:
                controller = current_control_rig.get_controller(current_model)

            controller_dict[name] = controller

            run_last_find = ['RigVMFunctionLibrary']

            if name in run_last_find:
                run_last.append(filepath)
            else:
                run_first.append(filepath)

        temp = run_first
        run_first = run_last
        run_last = temp

        # TODO: Refactor to use elif statements.
        ordered_files = None
        if run_last and run_first:
            ordered_files = run_first + run_last
        if run_last and not run_first:
            ordered_files = run_last
        if run_first and not run_last:
            ordered_files = run_first

        for filepath in ordered_files:
            util.show('Importing file: %s' % filepath)

            name = util_file.get_basename_no_extension(filepath)

            text = util_file.get_file_text(filepath)

            if name not in controller_dict:
                continue

            controller = controller_dict[name]

            controller.import_nodes_from_text(text)

    def export_data(self, comment, selection=None):  # TODO: Refactor

        if selection is None:
            selection = []
        path = self.get_file()

        if not util_file.is_dir(path):
            util_file.create_dir(path)
        else:
            files = util_file.get_files(path)
            for filename in files:
                util_file.delete_file(filename, path)

        util_file.create_dir(path)
        current_control_rig = unreal_lib.graph.get_current_control_rig()
        models = current_control_rig.get_all_models()
        text = {}

        if selection:
            for model in models:

                controller = current_control_rig.get_controller(model)
                get_selection = True
                nodes = []

                if model.get_graph_name().find('RigVMFunctionLibrary') > -1:
                    nodes = model.get_nodes()
                    get_selection = False

                found = []

                if get_selection:
                    selected_node_names = controller.get_graph().get_select_nodes()
                    found = list(filter(None, map(lambda x: controller.get_graph().find_node(x), selected_node_names)))
                nodes.extend(found)

                if not nodes:
                    continue

                node_names = [node.get_node_path() for node in nodes]

                current_text = controller.export_nodes_to_text(node_names)
                text[model.get_graph_name()] = current_text
        else:
            for model in models:
                controller = current_control_rig.get_controller(model)
                node_names = [node.get_node_path() for node in model.get_nodes()]

                current_text = controller.export_nodes_to_text(node_names)
                text[model.get_graph_name()] = current_text

        for key in text:
            current_text = text[key]
            data_path = util_file.join_path(path, '%s.data' % key)
            if not util_file.exists(data_path):
                util_file.create_file('%s.data' % key, path)
            util_file.write_lines(data_path, current_text)

        version = util_file.VersionFile(path)
        version.save(comment)


class PlatformData(CustomData):

    def __init__(self, name=None):
        super(PlatformData, self).__init__(name)

        self.custom_data = None
        if util.in_maya:
            self.custom_data = MayaAsciiFileData(name)
        if util.in_houdini:
            self.custom_data = HoudiniFileData(name)
        if util.in_unreal:
            self.custom_data = UnrealFileData(name)

    def _data_name(self):
        return 'platform'

    def _data_type(self):
        return 'agnostic.platform'

    def _data_extension(self):
        if util.in_maya:
            return 'ma'
        if util.in_houdini:
            return 'hip'

        return

    def save(self, *args, **kwargs):
        self.custom_data.save(*args, **kwargs)

    def export_data(self, *args, **kwargs):
        self.custom_data.export_data(*args, **kwargs)

    def open(self, *args, **kwargs):
        self.custom_data.open(*args, **kwargs)

    def import_data(self, *args, **kwargs):
        self.custom_data.import_data(*args, **kwargs)

    def reference (self, *args, **kwargs):
        self.custom_data.reference(*args, **kwargs)

    def set_directory(self, directory):
        super(PlatformData, self).set_directory(directory)

        if self.custom_data:
            self.custom_data.set_directory(self.directory)


class FbxData(CustomData):

    def _data_name(self):
        return 'data'

    def _data_type(self):
        return 'agnostic.fbx'

    def _data_extension(self):
        return 'fbx'

    def _import_maya(self, filepath):
        maya_lib.core.import_fbx_file(filepath)

    def _import_houdini(self, filepath):

        filename = util_file.get_basename_no_extension(filepath)

        filepath = util_file.fix_slashes(filepath)
        project_path = filepath.split('.data')[0]
        if project_path.endswith('/'):
            project_path = project_path[:-1]

        project = util_file.get_basename(project_path)

        obj = hou.node('/obj')
        geo = obj.node(project)
        if not geo:
            geo = obj.createNode('geo', project)

        fbx = geo.createNode('kinefx::fbxcharacterimport', 'fbx_%s' % filename)
        fbx.parm('fbxfile').set(filepath)

    def _export_maya(self, filepath, selection):
        maya_lib.core.export_fbx_file(filepath, selection)

    def import_data(self, filepath=None):
        import_file = filepath

        if not import_file:
            filepath = self.get_file()
            if not util_file.is_file(filepath):
                return

        if util.in_maya:
            self._import_maya(filepath)
        elif util.in_houdini:
            self._import_houdini(filepath)

    def export_data(self, comment, selection=None):

        if selection is None:
            selection = []
        filepath = self.get_file()

        if util.is_in_maya():
            self._export_maya(filepath, selection)

        version = util_file.VersionFile(filepath)
        version.save(comment)


class UsdData(CustomData):

    def _data_name(self):
        return 'data'

    def _data_type(self):
        return 'agnostic.usd'

    def _data_extension(self):
        return 'usd'

    def _export_maya(self, filepath, selection):
        maya_lib.core.export_usd_file(filepath, selection)

    def import_data(self, filepath=None):

        import_file = filepath

        if not import_file:
            filepath = self.get_file()
            if not util_file.is_file(filepath):
                return
        result = usd.import_file(filepath)
        return result

    def export_data(self, comment, selection=[]):
        filepath = self.get_file()

        result = usd.export_file(filepath, selection)
        if result:
            if util.in_maya:
                thumbnail_path = util_file.get_dirname(filepath)
                create_data_thumbnail(thumbnail_path)

        version = util_file.VersionFile(filepath)
        version.save(comment)


def read_ldr_file(filepath):
    lines = util_file.get_file_lines(filepath)

    found = []

    scale = 0.001

    matrix_scale = maya_lib.api.Matrix([scale, 0.0, 0.0, 0.0, 0.0,
                                        scale, 0.0, 0.0, 0.0, 0.0,
                                        scale, 0.0, 0.0, 0.0, 0.0, 1.0])

    for split_line in filter(lambda x: len(x) == 15, map(lambda x: x.split(), lines)):

        color = split_line[1]
        matrix_values = split_line[2:14]
        id_value = split_line[14]

        matrix_list = [float(matrix_values[3]), float(matrix_values[4]), float(matrix_values[5]), 0,
                       float(matrix_values[6]), float(matrix_values[7]), float(matrix_values[8]), 0,
                       float(matrix_values[9]), float(matrix_values[10]), float(matrix_values[11]), 0,
                       float(matrix_values[0]), float(matrix_values[1]), float(matrix_values[2]), 1]

        matrix = maya_lib.api.Matrix(matrix_list)

        matrix_scaled = matrix.api_object * matrix_scale.api_object

        tmatrix = maya_lib.api.TransformationMatrix(matrix_scaled)

        translate = tmatrix.translation()

        translate = [translate[0], translate[1] * -1, translate[2]]
        rotate = tmatrix.rotation()

        id_value = util.get_first_number(id_value)

        found.append([color, translate, rotate, id_value])

    return found


def read_lxfml_file(filepath):
    from xml.etree import cElementTree as tree

    dom = tree.parse(filepath)
    root = dom.getroot()
    scenes = root.findall('Scene')

    found_parts = []

    for models in map(lambda x: x.findall('Model'), scenes):
        for groups in map(lambda x: x.findall('Group'), models):
            for parts in map(lambda x: x.findall('Part'), groups):
                for part in parts:
                    position = [0, 0, 0]
                    angle_vector = [0, 0, 0]

                    id_value = int(part.get('designID'))
                    shader_id = int(part.get('materialID'))

                    position[0] = float(part.get('tx'))
                    position[1] = float(part.get('ty'))
                    position[2] = float(part.get('tz'))

                    angle = float(part.get('angle'))
                    angle_vector[0] = float(part.get('ax'))
                    angle_vector[1] = float(part.get('ay'))
                    angle_vector[2] = float(part.get('az'))

                    rotation = maya_lib.api.Quaternion(angle, angle_vector)
                    rotate = rotation.rotation()

                    found_parts.append((id_value, shader_id, position, rotate))

    return found_parts


def create_data_thumbnail(filepath, highlight_selection=False):

    filepath = util_file.join_path(filepath, 'thumbnail.png')

    maya_lib.core.create_thumbnail(filepath, highlight_selection=highlight_selection)
