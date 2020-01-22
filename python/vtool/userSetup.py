
#Setup

#1 Add the lines below to your Maya userSetup.py. It should be found in user/Documents/maya/scripts.  
#2 If it's not there, then add this file (userSetup.py) to that directory.

#3 code_directory must be set to the directory where you installed Vetala. This can be anywhere you chose. The default path is set below.
code_directory = 'C:/Program Files (x86)/Vetala' #<-- change only this path, make sure to include quotes. 


#Please don't change any of the following unless you know how it works.
import sys
import maya.utils

sys.path.append(code_directory)

def run_tools_ui(directory = None):

    from vtool.maya_lib import ui
    ui.tool_manager(directory = directory)

maya.utils.executeDeferred(run_tools_ui)