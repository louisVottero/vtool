# Copyright (C) 2022 Louis Vottero louis.vot@gmail.com    All rights reserved.

from __future__ import absolute_import
from __future__ import print_function

import sys

from vtool import qt_ui

from vtool import util

from vtool.ramen.ui_lib import ui_nodes


def main(directory = None):
    
    window = None
    
    from vtool import logger
    logger.setup_logging(level = 'DEBUG')
    
    if not util.is_in_maya():
        window = ui_nodes.NodeWindow()  
        #window.set_directory('c:/test', load_as_project=True) 
        window.show()
        
        return window
        
    if util.is_in_maya():
        from vtool.maya_lib import ui
        ui.ramen()
        
    

if __name__ == '__main__':
    
    APP = qt_ui.build_qt_application(sys.argv)
    
    window = main()
    
    sys.exit(APP.exec_())