Installation
============

You need to have Maya for Windows.
Vetala requires Maya 2014 or greater.  Maya 2014 or greater ships with PySide.  Vetala's UI uses PySide to work.  
If you need Vetala in Maya 2011 to 2013 you will need to have PyQt installed with that version of Maya.  If Vetala detects PyQt in Maya 2011 to 2013 it will run.

    1. Run your purchased vetala_setup.exe and chose where you want to install Vetala.
    2. Locate the userSetup.py file in the Vetala/vtool installation directory.
    3. If you don't have a userSetup.py file in your User/Documents/maya/scripts directory,  copy userSetup.py there.
    4. If you do have a userSetup.py file in User/Documents/maya/scripts directory, then merge the userSetup.py in the Vetala/vtool directory with yours.
    5. Change the code_directory variable in userSetup.py to the installation directory of Vetala.

The next time you load Maya, Vetala should load as a right side tab.
Also please come visit the forums, so you can have access to information about bugs and feature requests.
There is a special beta release section of the forum for those who have purchased where updates can be downloaded.