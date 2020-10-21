from vtool import util

#this is a buffer module.  This makes QT load nicely and dynamically between different versions.

QWIDGETSIZE_MAX = (1 << 24) - 1

type_QT = None

try:
    #try pyside and pyside2 first
    #and check if in maya first to make sure maya gets the right pyside
    is_in_maya = util.is_in_maya()
    
    if is_in_maya:
        maya_version = util.get_maya_version()
        
        if maya_version < 2017:
            try:
                from PySide import QtCore
                type_QT = 'pyside'
                
            except:
                type_QT = None
                
        if maya_version >= 2017:
            try:
                from PySide2 import QtCore
                type_QT = 'pyside2'
                
            except:
                type_QT = None
        
    if not is_in_maya:
        try:    
            from PySide2 import QtCore        
            type_QT = 'pyside2'
        except:
            from PySide import QtCore
            type_QT = 'pyside'
            
except:
    type_QT = None
    
if type_QT == None:
    #if no pyside then try pyqt
    try:
        from PyQt4 import QtCore
        type_QT = 'pyqt'
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

    from PyQt4 import Qt, uic
    from PyQt4.QtGui import *
    
if is_pyside():
    
    from PySide.QtGui import *
    from PySide.QtCore import Qt

    util.show('using PySide')

if is_pyside2():
    
    from PySide2.QtGui import *
    from PySide2.QtWidgets import *
    from PySide2.QtCore import Qt
    
    
    QItemSelection = QtCore.QItemSelection
    QItemSelectionModel = QtCore.QItemSelectionModel
    if maya_version >= 2020:
        QStringListModel = QtCore.QStringListModel
        import shiboken2 
        qApp = shiboken2.wrapInstance(shiboken2.getCppPointer(QApplication.instance())[0], QApplication)
    util.show('using PySide2')
    
def create_signal(*arg_list):
    
    if is_pyqt():
        return QtCore.pyqtSignal(*arg_list)
    if is_pyside() or is_pyside2():
        return QtCore.Signal(*arg_list)
    