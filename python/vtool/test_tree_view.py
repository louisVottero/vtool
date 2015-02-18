# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

global type_QT

import sys

import util
import util_file
import threading
import string
import random
import qt_ui

try:
    from PySide import QtCore, QtGui
    try:
        from shiboken import wrapInstance
    except:
        try:
            from PySide.shiboken import wrapInstance
        except:
            pass
    type_QT = 'pyside'
    #do not remove print
    print 'using pyside'
except:
    type_QT = None

if not type_QT == 'pyside':
    try:
        import PyQt4
        from PyQt4 import QtGui, QtCore, Qt, uic
        import sip
        type_QT = 'pyqt'
        #do not remove print
        print 'using pyqt'
        
    except:
        type_QT = None
        pass
    
    
class View(QtGui.QTreeView):
    
    def __init__(self):
        super(View, self).__init__()
        
        dir_model = QtGui.QFileSystemModel()
        dir_model.setRootPath('C:/dev')
        
        #dir_model.setFilter(QtCore.QDir.)
        
        self.setModel(dir_model)
        
        self.setRootIndex(dir_model.setRootPath('C:/dev/assets'))
        
        dir_model.head
        
        
def main():
    
    window = View()
    window.show()
    
    return window
        
if __name__ == '__main__':
    
    APP = qt_ui.build_qt_application(sys.argv)
    
    window = main()
    
    sys.exit(APP.exec_())