# Copyright (C) 2016 Louis Vottero louis.vot@gmail.com    All rights reserved.

import os
import sys

def main():
    
    filepath = __file__
    
    process_path = os.path.dirname(filepath)
    vetala_path = os.path.dirname(process_path)
    source_path = os.path.dirname(vetala_path)
    
    sys.path.append(source_path)
    
    env = os.environ.copy()
    
    #importing from vetala resets all the paths
    import vtool.util
    
    os.environ = env
    
    process_path = vtool.util.get_env('VETALA_CURRENT_PROCESS')
    
    if vtool.util.is_in_maya():
        import maya.standalone
        maya.standalone.initialize( name='python' )

    if vtool.util.is_in_maya():
        
        if process_path:
            
            from vtool.process_manager import process
            process_inst = process.Process()
            
            process_inst.set_directory(process_path)
            try:
                process_inst.run()
            except:
                pass
            
            process_inst.save_data('build', 'Generated from batch.')
            
        else:
            print 'Could not get current process.'
    
    import time
    time.sleep(10)
    
if __name__ == '__main__':
    main()
