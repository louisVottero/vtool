# Copyright (C) 2024 Louis Vottero louis.vot@gmail.com    All rights reserved.

from vtool import util

# this is a buffer module.  This makes QT load nicely and dynamically between different versions.

QWIDGETSIZE_MAX = (1 << 24) - 1
maya_version = util.get_maya_version()

type_QT = None
qt_imports = ['PyQt4', 'PySide', 'PySide2', 'PySide6']

for qt_import in qt_imports:
    if util.try_import(qt_import):
        type_QT = qt_import
        break

util.show('Using QT: %s' % type_QT)


def is_pyqt():
    return type_QT == 'PyQt4'


def is_pyside():
    return type_QT == 'PySide'


def is_pyside2():
    return type_QT == 'PySide2'


def is_pyside6():
    return type_QT == 'PySide6'


if is_pyqt():
    from PyQt4 import QtCore, Qt, uic
    from PyQt4.QtGui import *

if is_pyside():
    from PySide import QtCore, QtGui
    from PySide.QtGui import *
    from PySide.QtCore import Qt

if is_pyside2():

    from PySide2 import QtCore
    from PySide2.QtGui import *
    from PySide2.QtWidgets import *
    from PySide2.QtCore import Qt

    QItemSelection = QtCore.QItemSelection
    QItemSelectionModel = QtCore.QItemSelectionModel
    try:
        QStringListModel = QtCore.QStringListModel
    except:
        pass
    if maya_version >= 2020:
        import shiboken2
        qApp = shiboken2.wrapInstance(shiboken2.getCppPointer(QApplication.instance())[0], QApplication)

if is_pyside6():
    from PySide6 import QtCore
    from PySide6.QtGui import *
    from PySide6.QtWidgets import *
    from PySide6.QtCore import Qt

    QItemSelection = QtCore.QItemSelection
    QItemSelectionModel = QtCore.QItemSelectionModel
    try:
        QStringListModel = QtCore.QStringListModel
    except:
        pass


def is_batch():
    if not QApplication.activeWindow():
        return True

    return False


def create_signal(*arg_list):
    if is_pyqt():
        return QtCore.pyqtSignal(*arg_list)
    elif is_pyside() or is_pyside2() or is_pyside6():
        return QtCore.Signal(*arg_list)

