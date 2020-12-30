# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

from __future__ import absolute_import

import sys

from vtool import qt_ui

from vtool import util

from vtool.process_manager import ui_process_manager


def main(directory = None):
    
    window = None
    
    from vtool import logger
    logger.setup_logging(level = 'DEBUG')
    
    if not util.is_in_maya():
        window = ui_process_manager.ProcessManagerWindow()  
        #window.set_directory('c:/test', load_as_project=True) 
        window.show()
        
        return window
        
    if util.is_in_maya():
        from vtool.maya_lib import ui
        ui.process_manager()
        
if __name__ == '__main__':
    
    APP = qt_ui.build_qt_application(sys.argv)
    
    window = main()
    
    sys.exit(APP.exec_())