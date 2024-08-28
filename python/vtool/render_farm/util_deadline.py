# Copyright (C) 2024 Louis Vottero louis.vot@gmail.com    All rights reserved.

from __future__ import print_function
from __future__ import absolute_import

import sys
import subprocess
import os

from .. import util_file
from .. import util

# ---- Deadline


class DeadlineJob(object):

    def __init__(self):
        self._plugin_info_dict = {}
        self._job_info_dict = {
            'ChunkSize': 1,
            'InitialStatus': 'Active',
            'ConcurrentTasks': 1,
            'Priority': 100,
            'MachineLimit': 0}
        # 'IncludeEnvironment':'true'}
        self._output_path = ''
        self._scene_file_path = ''
        self._deadline_path = ''
        self._job_parents = []
        self._vtool_settings = None
        self._orig_drive = None
        self._remap_drive = None
        self._current_process = os.environ.get('VETALA_CURRENT_PROCESS')

    def _dict_to_deadline(self, dict_value):

        keys = list(dict_value.keys())
        keys.sort()

        txt = ''

        for key in keys:
            txt += '%s=%s\n' % (key, dict_value[key])

        return txt

    def _create_files(self):

        job_info = util_file.create_file('deadline_job_info.txt', self._output_path)
        text = self._dict_to_deadline(self._job_info_dict)
        util_file.write_replace(job_info, text)

        plugin_info = util_file.create_file('deadline_plugin_info.txt', self._output_path)
        text = self._dict_to_deadline(self._plugin_info_dict)
        util_file.write_replace(plugin_info, text)

        return [job_info, plugin_info]

    def _remap_drive_path(self, path):

        if not self._vtool_settings:
            self._vtool_settings = util_file.get_vetala_settings_inst()

            if not self._orig_drive:
                self._orig_drive = self._vtool_settings.get('deadline_orig_path_drive')
            if not self._remap_drive:
                self._remap_drive = self._vtool_settings.get('deadline_remap_path_drive')

        new_path = path

        if self._remap_drive and self._orig_drive:

            if path.startswith(self._orig_drive):
                new_path = self._remap_drive + new_path[len(self._orig_drive):]

        return new_path

    def set_job_info(self, dict_value=None):
        if dict_value is None:
            dict_value = {}
        self._job_info_dict.update(dict_value)

    def set_plugin_info(self, dict_value=None):
        if dict_value is None:
            dict_value = {}
        self._plugin_info_dict.update(dict_value)

    def set_task_info(self, pool, group, priority):

        dict_value = {
            'Pool': pool,
            'Group': group,
            'Priority': priority}

        self._job_info_dict.update(dict_value)

    def set_task_description(self, name, department, comment):
        dict_value = {
            'Name': name,
            'Department': department,
            'Comment': comment
        }

        self._job_info_dict.update(dict_value)

    def set_scene_file_path(self, scene_file_path):

        new_scene_file = self._remap_drive_path(scene_file_path)

        self._plugin_info_dict.update({'SceneFile': new_scene_file})
        self._scene_file_path = new_scene_file

    def set_output_path(self, output_path):
        self._output_path = output_path

    def set_deadline_path(self, deadline_path):

        self._deadline_path = deadline_path

    def set_parent_jobs(self, parents):

        util.convert_to_sequence(parents)

        job_string = ''
        for parent in parents:
            if parent == parents[-1]:
                job_string += str(parent)
            else:
                job_string += '%s,' % parent

        self._job_info_dict['JobDependencies'] = job_string

    def set_job_setting(self, setting_name, setting_string):

        self._job_info_dict[setting_name] = setting_string

    def set_plugin_setting(self, setting_name, setting_string):

        self._plugin_info_dict[setting_name] = setting_string

    def set_current_process(self, process_directory):
        self._current_process = process_directory

    def submit(self):

        deadline_command = self._deadline_path
        job_info, plugin_info = self._create_files()

        command = '{deadline_command} "{job_info}" "{plugin_info}"'.format(**vars())

        process = subprocess.Popen(command, stdout=subprocess.PIPE)

        if sys.version_info.major < 3:
            lines = iter(process.stdout.readline, b"")
        else:
            lines = process.stdout.read()

        for line in lines:
            if line.find('JobID') > -1:
                split_line = line.split('=')
                job_id = split_line[-1]
                job_id = job_id.rstrip('\n')
                job_id = job_id.rstrip('\r')
            util.show(line)
        sys.stdout.flush()

        return job_id


class MayaJob(DeadlineJob):

    def __init__(self):
        super(MayaJob, self).__init__()

        import maya.cmds as cmds

        settings = util_file.get_vetala_settings_inst()
        vtool_path = settings.get('deadline_vtool_directory')
        vtool_current = self._current_process

        vtool_deadline_file = util_file.get_process_deadline_file()

        paths = [vtool_path, vtool_current, vtool_deadline_file]
        updated_paths = []

        for path in paths:
            new_path = path
            new_path = self._remap_drive_path(new_path)

            updated_paths.append(new_path)

        vtool_path, vtool_current, vtool_deadline_file = updated_paths

        job_info_dict = {

            'Plugin': 'MayaBatch',
            'EnvironmentKeyValue0': 'PYTHONPATH=' + os.environ.get('PYTHONPATH'),
            'EnvironmentKeyValue1': 'VETALA_CURRENT_PROCESS=' + vtool_current,
            'EnvironmentKeyValue2': 'VETALA_CURRENT_PATH=' + vtool_path
        }

        self._job_info_dict.update(job_info_dict)

        plugin_info_dict = {
            'Version': cmds.about(version=True),
            'ScriptJob': 'true',
            'ScriptFilename': vtool_deadline_file
        }

        self._plugin_info_dict.update(plugin_info_dict)

    def set_current_process(self, process_directory):
        super(MayaJob, self).set_current_process(process_directory)

        remapped_dir = self._remap_drive_path(process_directory)

        self._job_info_dict['EnvironmentKeyValue1'] = 'VETALA_CURRENT_PROCESS=' + remapped_dir

    def set_script_path(self, script_path):
        pass
