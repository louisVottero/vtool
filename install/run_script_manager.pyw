# Copyright (C) 2022 Louis Vottero louis.vot@gmail.com    All rights reserved.

from __future__ import absolute_import

import sys
import os

parent_path = os.path.dirname(__file__)
vtool_path = os.path.dirname(parent_path)
vtool_path = os.path.join(vtool_path, 'python')

sys.path.append(vtool_path)

from vtool import qt_ui
from vtool.script_manager import script_view

def main(directory = None):
    
    window = None
    
    window = script_view.ScriptManagerWidget()   
    window.set_directory('C:/test_script_view')
    window.show()
    return window

if __name__ == '__main__':
    
    APP = qt_ui.build_qt_application(sys.argv)
    
    WINDOW = main()
    
    sys.exit(APP.exec_())
