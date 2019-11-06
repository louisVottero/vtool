# Copyright (C) 2016 Louis Vottero louis.vot@gmail.com    All rights reserved.

import os
import sys
import time
import traceback

def main():
    
    
    
    print '\n\n\n\n\n------- VETALA BATCH ---------------------------------------------------------------------------------------------------------------------\n\n'
    
    try:
        import maya.standalone
        maya.standalone.initialize( name='python' )
    except:
        status = traceback.format_exc()
        print status
        
        print '\n\nMaya standalone failed'
    
    source_path = os.environ['VETALA_PATH']
    source_path = os.path.dirname(source_path)
    
    sys.path.insert(0, source_path)
    
    print '\nUsing Vetala Path', source_path
    print 'Using Pyton Version', sys.version
    
    env = os.environ.copy()
    
    #importing from vetala resets all the paths
    import vtool.util
    import vtool.util_file
    
    os.environ = env
    
    process_path = vtool.util.get_env('VETALA_CURRENT_PROCESS')
    settings = vtool.util.get_env('VETALA_SETTINGS')
    
    if settings:
        settings_inst = vtool.util_file.SettingsFile()
        settings_inst.set_directory(settings)
        
        codes = settings_inst.get('code_directory')
        if codes:
            for code in codes:
                vtool.util.show('Adding code path: %s' % code)
                sys.path.append(code)
    
    


    if vtool.util.is_in_maya():
        print 'Using Maya %s\n\n' % vtool.util.get_maya_version()
        if vtool.util.get_maya_version() >= 2017:
            import maya.cmds as cmds
            try:
                cmds.loadPlugin('mtoa')
            except:
                pass
        
    if process_path:
        
        from vtool.process_manager import process
        process_inst = process.Process()
        
        process_inst.set_directory(process_path)
        try:
            process_inst.run()
        except:
            vtool.util.error( traceback.format_exc() )
        
        
        
        vtool.util.show('Batch finished.\n\n')
        
        comment = 'Batch build'
        saved = process_inst.save_data('build', comment)
        
        if not saved:
            vtool.util.show('Unable to save contents!!')
            
    else:
        vtool.util.show('Could not get current process.  Batch finished, nothing processed.')

    vtool.util.show('\n\nAll done, please close console.')
    
    while True:
        time.sleep(1)
    
    print '\n\n------- END OF VETALA BATCH ----------------------------------------------------------\n\n\n\n\n'
    
if __name__ == '__main__':
    main()
