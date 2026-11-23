import sys

from .. import qt
from ..process_manager import ui_process_manager

import bpy


def pump_qt_events():
    app = qt.QApplication.instance()
    if app:
        app.processEvents()
    return 0.01  # Run again in 10ms


app = qt.QApplication.instance() or qt.QApplication(sys.argv)
app.setQuitOnLastWindowClosed(False)
if not bpy.app.timers.is_registered(pump_qt_events):
    bpy.app.timers.register(pump_qt_events, persistent=True)


def process_manager():
    window = ui_process_manager.ProcessManagerWindow()

    window.setWindowFlag(qt.Qt.WindowType.WindowStaysOnTopHint, True)

    window.show()

