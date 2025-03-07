# vtool - Vetala Auto Rig

A set of rigging and asset creation scripts.

## Required 
You will need Maya or Unreal or Houdini to run Vetala.  It is also possible to directly from PySide. 
Currently Vetala works best with Maya. Other platforms are really early work in progress.

## Getting Started

* Download from git to the path of your chose.

### Maya

Vetala works with older and newer versions of Maya but is less tested.
Maya 2022 and python2, 2023, 2024, 2025
Python 2 should be working in older versions, but Vetala is currently most tested in python 3.  

* In Maya in Python add the path to the sys.path. 
For example:
```
import sys
sys.path.append('C:/vtool/python')
```
* launch the ui by running the following:
```
from vtool.maya_lib import ui 
ui.tool_manager()
```

### Unreal 
Currently testing in Unreal 5.3 and 5.5
The Unreal implementation is still fairly buggy compared to Maya.  Lots missing and incomplete, could use help testing.

* Install PySide 2 
  * pip install directly to your install of unreal. In a command prompt/shell, e.g.: `"/UE_5.0/Engine/Binaries/ThirdParty/Python/Win64/python.exe" -m pip install PySide2`
  * If you are working at a studio you may need to install pyside separately. If you have python 3.7 installed separate from Unreal, pip install pyside 2 to that python and then source it in your Unreal project. Search for python in your project settings and add your python site packages `/Python/Python39/Lib/site-packages` to the Additional Paths.
* Add your vetala install path to your project python settings. Search for python in your project settings and add the python folder of the vtool package. E.g.: `/dev/git/vtool/python`
* launch the ui by running
```
from vtool import ui 
ui.process_manager()
```


## Templates

https://github.com/louisVottero/vtool_templates

![vetala_pose](https://user-images.githubusercontent.com/2879064/192540512-de055aa0-cdde-4d1d-ad0d-37d22a0e0d3c.png)

## Resources

Documentation: https://vetala-auto-rig.readthedocs.io/en/latest/index.html

Vetala Youtube channel: https://www.youtube.com/channel/UCcZl_ADvTJXd3xAiPg-jVQQ


Join Vetala Discord Server: https://discord.gg/RgkYeKVeFc


