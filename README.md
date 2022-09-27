# vtool - Vetala Auto Rig

A set of rigging and asset creation scripts.

## Required 
You will need to have a copy of Maya to run Vetala. 
Vetala works with older versions of Maya but is less tested.
Maya 2020 and Maya 2022 are the most tested. 
Vetala will work with Python 2 and 3 in Maya 2022 and 2023

## Getting Started

* Download from git to the path of your chose.
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

## Templates

Currently only wip body process available
https://github.com/louisVottero/vtool_templates

![vetala_pose](https://user-images.githubusercontent.com/2879064/192540512-de055aa0-cdde-4d1d-ad0d-37d22a0e0d3c.png)

## Resources

Documentation: https://vetala-auto-rig.readthedocs.io/en/latest/index.html

Vetala Youtube channel: https://www.youtube.com/channel/UCcZl_ADvTJXd3xAiPg-jVQQ

Join Vetala Discord Server: https://discord.gg/RgkYeKVeFc


