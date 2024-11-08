# Copyright (C) 2024 Louis Vottero louis.vot@gmail.com    All rights reserved.

from __future__ import absolute_import

from .. import qt_ui, qt, util_file

from vtool import logger

log = logger.get_logger(__name__)


class ProcessSettings(qt_ui.BasicWidget):

    def __init__(self):
        self.directory = None

        super(ProcessSettings, self).__init__()

        self.setContentsMargins(1, 1, 1, 1)

    def set_directory(self, directory):
        log.debug('Set process setting widget directory %s' % self.directory)

        self.directory = directory
        self.name_widget.set_directory(self.directory)
        self.maya_widget.set_directory(self.directory)

    def set_active(self, bool_value):
        self.name_widget.set_active(bool_value)

    def _build_widgets(self):
        self.name_widget = qt_ui.DefineControlNameWidget(self.directory)
        self.name_widget.collapse_group()
        self.maya_widget = MayaOptions()
        self.maya_widget.collapse_group()

        self.main_layout.addWidget(self.name_widget)
        self.main_layout.addWidget(self.maya_widget)

        self.main_layout.setAlignment(qt.QtCore.Qt.AlignTop)


class MayaOptions(qt_ui.Group):

    def __init__(self):
        self.settings = None
        self._skip_set_value = False
        super(MayaOptions, self).__init__('Maya')

        self.default_focal_length = 35
        self.default_near = 0.1
        self.default_far = 10000

    def _build_widgets(self):

        self.use_camera_settings = qt_ui.GetBoolean('Use Camera Settings')
        self.use_camera_settings.set_value(0)

        self.focal_widget = qt_ui.GetNumber('Focal Length')
        self.focal_widget.set_value(35)
        self.focal_widget.setDisabled(True)

        self.min_widget = qt_ui.GetNumber('Near Clip Plane')
        self.min_widget.set_value(0.01)
        self.min_widget.setDisabled(True)

        self.max_widget = qt_ui.GetNumber('Far Clip Plane')
        self.max_widget.set_value(10000)
        self.max_widget.setDisabled(True)

        self.main_layout.addWidget(self.use_camera_settings)
        self.main_layout.addWidget(self.focal_widget)
        self.main_layout.addWidget(self.min_widget)
        self.main_layout.addWidget(self.max_widget)

        self.main_layout.setAlignment(qt.QtCore.Qt.AlignTop)

        self.focal_widget.valueChanged.connect(lambda value: self._set_setting('Maya Focal Length', value))
        self.min_widget.valueChanged.connect(lambda value: self._set_setting('Maya Near Clip Plane', value))
        self.max_widget.valueChanged.connect(lambda value: self._set_setting('Maya Far Clip Plane', value))
        self.use_camera_settings.valueChanged.connect(self._update_use_camera)

    def _update_use_camera(self):

        value = self.use_camera_settings.get_value()

        if value:
            self.focal_widget.setDisabled(False)
            self.min_widget.setDisabled(False)
            self.max_widget.setDisabled(False)
            self.settings.set('Maya Use Camera Settings', 1)

        else:
            self.focal_widget.setDisabled(True)
            self.min_widget.setDisabled(True)
            self.max_widget.setDisabled(True)
            self.settings.set('Maya Use Camera Settings', 0)

    def set_directory(self, directory):

        self.settings = None

        if not util_file.is_dir(directory):
            return

        settings_inst = util_file.SettingsFile()
        settings_inst.set_directory(directory, 'settings.json')

        self.settings = settings_inst

        self._load_values()

    def _set_setting(self, name, value):
        if self._skip_set_value:
            return

        self.settings.set(name, value)

    def _load_values(self):

        self._skip_set_value = True
        camera_settings = self.settings.get('Maya Use Camera Settings')
        focal = self.settings.get('Maya Focal Length')
        near = self.settings.get('Maya Near Clip Plane')
        far = self.settings.get('Maya Far Clip Plane')

        if camera_settings:
            self.use_camera_settings.set_value(camera_settings)
            self._update_use_camera()
        else:
            self.use_camera_settings.set_value(0)
            self._update_use_camera()
        if focal:
            self.focal_widget.set_value(focal)
        else:
            self.focal_widget.set_value(self.default_focal_length)
        if near:
            self.min_widget.set_value(near)
        else:
            self.min_widget.set_value(self.default_near)
        if far:
            self.max_widget.set_value(far)
        else:
            self.max_widget.set_value(self.default_far)
        self._skip_set_value = False
