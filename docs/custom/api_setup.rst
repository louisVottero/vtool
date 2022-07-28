API Setup
---------

PYTHONPATH
==========

In Maya you can access the Vetala vtool modules by appending the Vetala install path to your PYTHONPATH.

.. code-block:: python

    import sys
    sys.path.append( 'C:/Program Files (x86)/Vetala' )

.. note::
    
    Notice the direction of the slashes in the filepath.
    
After adding Vetala path to the PYTHONPATH you can begin to import modules.
Here is an example:

.. code-block:: python

    from vtool import util
    #now call something from util.
    util.show('Hellow World.')
    
If you want to launch Vetala UI, you just have to run the following.

.. code-block:: python

    from vtool.maya_lib import ui
    ui.tool_manager()

    
userSetup.py
============

If you've added the following lines to your userSetup.py file:

.. code-block:: python

    code_directory = 'C:/Program Files (x86)/Vetala' #<-- change only this path, make sure to include quotes. 


    #Please don't change any of the following unless you know how it works.
    import sys
    sys.path.append(code_directory)

    import maya.utils
    import maya.cmds as cmds

    def run_tools_ui(code_directory):
        

        from vtool.maya_lib import ui
        ui.tool_manager(directory = code_directory)

    maya.utils.executeDeferred(run_tools_ui, '')
    
Then accessing the api is simple. 
You don't have to add the install directory to the PYTHONPATH. You can skip the sys.path.append code. 
 Also the Vetala UI should have launched automatically.


