"""
Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    
 
This file is part of vtool project.
 
vtool project can not be copied and/or distributed without the express permission of Louis Vottero
"""

import sys

import util
import qt_ui

def main(directory = None):
    
    window = None
    
    if not util.is_in_maya():
        window = qt_ui.BasicGraphicsView()
           
        window.show()
        return window
    
    if util.is_in_maya():
        window = qt_ui.BasicGraphicsView()
           
        window.show()
        return window  

if __name__ == '__main__':
    
    APP = qt_ui.build_qt_application(sys.argv)
    
    WINDOW = main()
    
    sys.exit(APP.exec_())