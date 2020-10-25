# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

import sys

import qt_ui

import util

from vtool.ramen.ui_lib import ui_nodes


def main(directory = None):
    
    window = None
    
    import logger
    logger.setup_logging(level = 'DEBUG')
    
    if not util.is_in_maya():
        window = ui_nodes.NodeWindow()  
        #window.set_directory('c:/test', load_as_project=True) 
        window.show()
        
        return window
        
    if util.is_in_maya():
        import maya_lib.ui
        maya_lib.ui.process_manager()
        
    

if __name__ == '__main__':
    
    APP = qt_ui.build_qt_application(sys.argv)
    
    window = main()
    
    sys.exit(APP.exec_())