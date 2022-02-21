# Copyright (C) 2022 Louis Vottero louis.vot@gmail.com    All rights reserved.

from vtool import util
from vtool.process_manager import process

def main():
    
    vetala_dir = util.get_env('VETALA_CURRENT_PROCESS')
    
    process_inst = process.Process()
    process_inst.set_directory(vetala_dir)
    process_inst.run()
    
    comment = 'Deadline Batch build'
    saved = process_inst.save_data('build', comment)
        
    if not saved:
        util.show('Unable to save contents!!')
    
if __name__ == '__main__':
    main()