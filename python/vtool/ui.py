from .. import util

def process_manager():
    if util.in_houdini:
        ui = None
        from ..houdini_lib import ui
        ui.process_manager()
        
    if util.in_maya:
        ui = None
        from ..maya_lib import ui
        ui.tool_manager()
        
    if util.in_unreal:
        ui = None
        from ..unreal_lib import ui
        ui.process_manager()
        