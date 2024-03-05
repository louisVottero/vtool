
# Setup

# 1 Add the lines below to your Maya userSetup.py. It should be found in user/Documents/maya/scripts.
# 2 If it's not there, then add this file (userSetup.py) to that directory.
import sys
# update this path to the directory where vtool lives on your system
sys.path.append('path/to/vtool/python/')

# Important! run the following lines in Maya after to launch vtool.
# After the Maya workspace handles loading the window/tab when Maya reopens.
#
# from vtool.maya_lib import ui
# ui.tool_manager(name = 'VETALA HUB', directory = '')
