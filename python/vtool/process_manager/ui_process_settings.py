# Copyright (C) 2016 Louis Vottero louis.vot@gmail.com    All rights reserved.

from vtool import qt_ui, qt
from vtool import util
from vtool.process_manager import process

class ProcessSettings(qt_ui.BasicWidget):
    
    def __init__(self):
        
        self.directory = None
        
        super(ProcessSettings, self).__init__()
        
        self.setContentsMargins(1,1,1,1)
        
    def set_directory(self, directory):
        self.directory = directory
        self.name_widget.set_directory(self.directory)
        self.management_widget.set_directory(self.directory)
    
    def set_active(self, bool_value):
        
        self.name_widget.set_active(bool_value)
    
    def _build_widgets(self):
        
        self.management_widget = ManagementWidget()
        
        self.name_widget = qt_ui.DefineControlNameWidget(self.directory)
        
        self.management_widget.collapse_group()
        self.name_widget.collapse_group()
        
        self.main_layout.addWidget(self.management_widget)
        self.main_layout.addWidget(self.name_widget)
        
        
class ManagementWidget(qt_ui.Group):
    
    def __init__(self, name = 'Management'):
        super(ManagementWidget, self).__init__(name)
        
        self.directory = None
        
        
    def _build_widgets(self):
        
        backup = qt.QPushButton('Backup This Process')
        prune_version = qt.QPushButton('Prune Old Versions')
        
        backup.clicked.connect(self._backup_process)
        prune_version.clicked.connect(self._prune_versions)
        
        self.main_layout.addWidget(backup)
        self.main_layout.addWidget(prune_version)
        
        
    def _backup_process(self):
        
        if not self.directory:
            return
        
        process_inst = process.Process()
        process_inst.set_directory(self.directory)
        process_inst.backup()
        
    
    def _prune_versions(self):
        
        pass
    
    def set_directory(self, directory):
        
        self.directory = directory
        
        
        