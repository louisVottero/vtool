Intro
=====

Welcome to the Vetala Api.

Vetala has many helpful python modules to rig characters and setup rebuilding.

-------------------------------------------------

vtool
=====

-------------------------------------------------

.. toctree::
    :maxdepth: 1
    
    util <../vtool_util>

.. code-block:: python

    from vtool import util
    
Utilities for simplifying python and math scripts.

-------------------------------------------------

.. toctree::
    :maxdepth: 1
    
    util_file <../vtool_util_file>
    
.. code-block:: python

    from vtool import util_file
    
Utilities for simplifying file creation, writing and reading.

-------------------------------------------------
    
.. toctree::
    :maxdepth: 1
    
    data <../vtool_data>
    
.. code-block:: python

    from vtool import data
    
Utility for data export/import.

-------------------------------------------------

vtool.process_manager
=====================

-------------------------------------------------

.. toctree::
	:maxdepth: 1
	
	process <../vtool_process_manager_process>
	
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

.. toctree::
    :maxdepth: 1
    
    util <../vtool_maya_lib_util>
    
.. code-block:: python

    from vtool.maya_lib import util
   
.. warning::
   
	Deprecated. vtool.maya_lib.util will no longer be supported.

-------------------------------------------------

.. toctree::
    :maxdepth: 1
    
    rigs <../vtool_maya_lib_rigs>
    
.. code-block:: python

    from vtool.maya_lib import rigs
	
Rig classes

-------------------------------------------------

.. toctree::
    :maxdepth: 1
    
    rigs_util <../vtool_maya_lib_rigs>
    
.. code-block:: python

    from vtool.maya_lib import rigs_util
	
Rig utilities

-------------------------------------------------

.. toctree::
    :maxdepth: 1
    
    core <../vtool_maya_lib_core>
    
.. code-block:: python

    from vtool.maya_lib import core
	
Utilities for dealing with maya tasks.

-------------------------------------------------

.. toctree::
    :maxdepth: 1
    
    attr <../vtool_maya_lib_attr>
    
.. code-block:: python

    from vtool.maya_lib import attr
	
Utilities for dealing with maya attributes and connections.


-------------------------------------------------

.. toctree::
    :maxdepth: 1
    
    space <../vtool_maya_lib_space>
    
.. code-block:: python

    from vtool.maya_lib import space
	
Utilities for dealing with maya constraints and transformations.

-------------------------------------------------

.. toctree::
    :maxdepth: 1
    
    geo <../vtool_maya_lib_geo>
    
.. code-block:: python

    from vtool.maya_lib import geo
	
Utilities for dealing with and creating maya geometry.

-------------------------------------------------

.. toctree::
    :maxdepth: 1
    
    deform <../vtool_maya_lib_deform>
    
.. code-block:: python

    from vtool.maya_lib import deform
	
Utilities for dealing with and creating maya deformers.

-------------------------------------------------

.. toctree::
    :maxdepth: 1
    
    shade <../vtool_maya_lib_shade>
    
.. code-block:: python

    from vtool.maya_lib import shade
	
Utilities for dealing with and creating maya shaders.

-------------------------------------------------

.. toctree::
    :maxdepth: 1
    
    fx <../vtool_maya_lib_fx>
    
.. code-block:: python

    from vtool.maya_lib import fx
	
Utilities for dealing with and creating maya ncloth and nhair.

-------------------------------------------------

.. toctree::
    :maxdepth: 1
    
    blendshape <../vtool_maya_lib_blendshape>
    
.. code-block:: python

    from vtool.maya_lib import blendshape
	
Utilities for dealing with maya blendshapes.

-------------------------------------------------

.. toctree::
    :maxdepth: 1
    
    corrective <../vtool_maya_lib_corrective>
    
.. code-block:: python

    from vtool.maya_lib import corrective
	
Utilities for Vetala maya correctives.