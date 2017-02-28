from vtool import util

#this is a buffer module.  This makes QT load nicely and dynamically between different versions.

QWIDGETSIZE_MAX = (1 << 24) - 1

type_QT = None

try:
    
    try:
        from PySide import QtCore
        from PySide.QtGui import *
        
        type_QT = 'pyside'
        util.show('using PySide')
        
    except:
        from PySide2 import QtCore
        from PySide2.QtGui import *
        from PySide2.QtWidgets import *
        
        type_QT = 'pyside2'
        util.show('using PySide2')
except:
    type_QT = None
    
if type_QT == None:
    try:
        from PyQt4 import QtCore, Qt, uic
        from PyQt4.QtGui import *
        type_QT = 'pyqt'
        
        util.show('using pyQT')
        
    except:
        type_QT = None
    

def is_pyqt():
    global type_QT
    if type_QT == 'pyqt':
        return True
    return False
    
def is_pyside():
    global type_QT
    if type_QT == 'pyside':
        return True
    return False

def is_pyside2():
    global type_QT
    if type_QT == 'pyside2':
        return True
    return False

if is_pyqt():
    from PyQt4 import QtCore, Qt, uic
    from PyQt4.QtGui import *
    
if is_pyside():
    from PySide import QtCore
    from PySide.QtGui import *
    
if is_pyside2():
    from PySide2 import QtCore
    from PySide2.QtGui import *
    from PySide2.QtWidgets import *
    
    QItemSelection = QtCore.QItemSelection
    QItemSelectionModel = QtCore.QItemSelectionModel
    