# Copyright (C) 2024 Louis Vottero louis.vot@gmail.com    All rights reserved.

import sys

import unreal

from .. import qt
from ..process_manager import ui_process_manager

app = None
if not qt.QApplication.instance():
    app = qt.QApplication(sys.argv)


def process_manager():
    window = ui_process_manager.ProcessManagerWindow()
    window.show()

    unreal.parent_external_window_to_slate(window.winId())
