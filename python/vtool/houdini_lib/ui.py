# Copyright (C) 2024 Louis Vottero louis.vot@gmail.com    All rights reserved.

from ..process_manager import ui_process_manager


def process_manager():
    window = ui_process_manager.ProcessManagerWindow()
    window.show()

    return window
