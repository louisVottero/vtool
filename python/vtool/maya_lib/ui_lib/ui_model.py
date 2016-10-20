# Copyright (C) 2016 Louis Vottero louis.vot@gmail.com    All rights reserved.

from vtool import qt_ui

if qt_ui.is_pyqt():
    from PyQt4 import QtCore, Qt, uic
    from PyQt4.QtGui import *
if qt_ui.is_pyside():
    from PySide import QtCore
    from PySide.QtGui import *
if qt_ui.is_pyside2():
    from PySide2 import QtCore
    from PySide2.QtGui import *
    from PySide2.QtWidgets import *