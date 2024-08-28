# Copyright (C) 2024 Louis Vottero louis.vot@gmail.com    All rights reserved.

from __future__ import print_function

import os
import sys

print('Using Python Version:\t', sys.version)
vetala_path = os.environ['VETALA_CURRENT_PATH']
if not vetala_path.endswith('/'):
    vetala_path = vetala_path + '/'
vetala_path = os.path.append(vetala_path, 'python')
sys.path.insert(0, vetala_path)
print('Using Vetala Path: ', vetala_path)

from vtool import util
from vtool.process_manager import process


def main():
    vetala_dir = os.environ.get('VETALA_CURRENT_PROCESS')

    process_inst = process.Process()
    process_inst.set_directory(vetala_dir)
    process_inst.run()

    comment = 'Deadline Batch build'
    saved = process_inst.save_data('build', comment)

    if not saved:
        util.show('Unable to save contents!!')


if __name__ == '__main__':
    main()
