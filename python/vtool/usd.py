
from . import util

usd = None

if util.in_houdini:
    from .houdini_lib import usd
if util.in_maya:
    from .maya_lib import usd
if util.in_unreal:
    from .unreal_lib import usd

def import_file(filepath):
    print('import file usd', '..........................................................................................................................')
    result = usd.import_file(filepath)
    print('usd result!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
    print(result)
    return result