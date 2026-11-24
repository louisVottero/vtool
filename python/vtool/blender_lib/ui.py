import sys
import ctypes
import bpy
from . import util
from .. import qt
from ..process_manager import ui_process_manager

_window = None
_win32_timer_proc = None


def _pump_qt():
    app = qt.QApplication.instance()
    if app:
        with util.view_3d_context():
            app.processEvents()
    return 0.016


def _init_qt_loop():
    global _win32_timer_proc
    if sys.platform == "win32":
        if _win32_timer_proc is None:
            TIMERPROC = ctypes.WINFUNCTYPE(None, ctypes.c_void_p, ctypes.c_uint, ctypes.c_size_t, ctypes.c_uint)
            _win32_timer_proc = TIMERPROC(lambda *_: _pump_qt())
            ctypes.windll.user32.SetTimer(None, 0, 16, _win32_timer_proc)
    elif not bpy.app.timers.is_registered(_pump_qt):
        bpy.app.timers.register(_pump_qt, persistent=True)


def process_manager():
    global _window
    if qt.QApplication.instance() is None:
        qt.QApplication.setAttribute(qt.Qt.ApplicationAttribute.AA_DontUseNativeMenuBar, True)
        app = qt.QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)

    _init_qt_loop()

    if _window is None:
        _window = ui_process_manager.ProcessManagerWindow()
        _window.setWindowFlags(qt.Qt.WindowType.Window | qt.Qt.WindowType.WindowStaysOnTopHint)

    _window.show()
    _window.raise_()
    _window.activateWindow()

