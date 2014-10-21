# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

import sys

import qt_ui

import util
import util_file

import process_manager.ui_process_manager as ui_process_manager



def main(directory = None):
    
    window = None
    
    if not util.is_in_maya():
        window = ui_process_manager.ProcessManagerWindow()   
        window.show()
        return window
        
    if util.is_in_maya():
        import maya_lib.ui
        maya_lib.ui.process_manager()
        
    

if __name__ == '__main__':
    
    
    
    APP = qt_ui.build_qt_application(sys.argv)
    
    WINDOW = main()
    
    sys.exit(APP.exec_())