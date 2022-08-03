# Copyright (C) 2022 Louis Vottero louis.vot@gmail.com    All rights reserved.

from __future__ import absolute_import

import sys

from vtool import qt_ui

from vtool import util
from vtool import util_file

import script_manager.script_view as script_view



def main(directory = None):
    
    window = None
    
    #if not util.is_in_maya():
    window = script_view.ScriptManagerWidget()   
    window.set_directory('C:/test_script_view')
    window.show()
    return window
        
    #if util.is_in_maya():
    #    import maya_lib.ui
    #    maya_lib.ui.process_manager()
        
    

if __name__ == '__main__':
    
    APP = qt_ui.build_qt_application(sys.argv)
    
    WINDOW = main()
    
    sys.exit(APP.exec_())
