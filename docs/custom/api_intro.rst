Intro
=====

Welcome to the Vetala Api.

Vetala has many helpful python modules to rig characters and setup rebuilding.

-------------------------------------------------

vtool
=====

-------------------------------------------------

.. code-block:: python

    from vtool import util
    
Utilities for simplifying python and math scripts.

-------------------------------------------------
    
.. code-block:: python

    from vtool import util_file
    
Utilities for simplifying file creation, writing and reading.

-------------------------------------------------
    
.. code-block:: python

    from vtool import data
    
Utility for data export/import.

-------------------------------------------------

vtool.process_manager
=====================

-------------------------------------------------
	
.. code-block:: python
	
	from vtool.process_manager import process
	
When running code through Vetala you can access the Process through the process namespace.
The following code calls the import_data function of the Process class for the current process instance.
Any function of the Process class can be called. This makes working in context very easy.

.. code-block:: python
	
	process.import_data('data_name')

-------------------------------------------------
	
vtool.maya_lib
==============

-------------------------------------------------
    
.. code-block:: python

    from vtool.maya_lib import rigs
	
Rig classes

-------------------------------------------------
    
.. code-block:: python

    from vtool.maya_lib import rigs_util
	
Rig utilities

-------------------------------------------------
    
.. code-block:: python

    from vtool.maya_lib import core
	
Utilities for dealing with Maya tasks.

-------------------------------------------------
    
.. code-block:: python

    from vtool.maya_lib import attr
	
Utilities for dealing with Maya attributes and connections.


-------------------------------------------------
    
.. code-block:: python

    from vtool.maya_lib import space
	
Utilities for dealing with Maya constraints and transformations.

-------------------------------------------------
    
.. code-block:: python

    from vtool.maya_lib import geo
	
Utilities for dealing with and creating Maya geometry.

-------------------------------------------------
    
.. code-block:: python

    from vtool.maya_lib import deform
	
Utilities for dealing with and creating Maya deformers.

-------------------------------------------------
    
.. code-block:: python

    from vtool.maya_lib import shade
	
Utilities for dealing with and creating Maya shaders.

-------------------------------------------------
    
.. code-block:: python

    from vtool.maya_lib import fx
	
Utilities for dealing with and creating Maya ncloth and nhair.

-------------------------------------------------
    
.. code-block:: python

    from vtool.maya_lib import blendshape
	
Utilities for dealing with maya blendshapes.

-------------------------------------------------
    
.. code-block:: python

    from vtool.maya_lib import corrective
	
Utilities for Vetala maya correctives.

-------------------------------------------------
    
.. code-block:: python

    from vtool.maya_lib import api
	
Utilities for Maya api.