import sys

from .. import qt
from ..process_manager import ui_process_manager

import bpy


class SimpleFlowStyleWindow(qt.QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Non-Blocking PySide6 in Blender")
        self.setWindowFlags(self.windowFlags() | qt.QtCore.Qt.WindowStaysOnTopHint)
        layout = qt.QVBoxLayout(self)
        btn = qt.QPushButton("Add Cube in Blender")
        btn.clicked.connect(lambda: bpy.ops.mesh.primitive_cube_add())
        layout.addWidget(btn)


def pump_qt_events():
    app = qt.QApplication.instance()
    if app:
        app.processEvents()
    return 0.01  # Run again in 10ms


# 1. Initialize QApplication safely
app = qt.QApplication.instance() or qt.QApplication(sys.argv)
app.setQuitOnLastWindowClosed(False)

# 2. Register the non-blocking timer
if not bpy.app.timers.is_registered(pump_qt_events):
    bpy.app.timers.register(pump_qt_events, persistent=True)


def process_manager():
    window = ui_process_manager.ProcessManagerWindow()
    window.show()

