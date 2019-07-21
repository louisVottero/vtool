# Copyright (C) 2016 Louis Vottero louis.vot@gmail.com    All rights reserved.

from vtool import qt_ui, qt
from vtool import util

class ProcessSettings(qt_ui.BasicWidget):
    
    def __init__(self):
        
        self.directory = None
        
        super(ProcessSettings, self).__init__()
        
        self.setContentsMargins(1,1,1,1)
        
    def set_directory(self, directory):
        self.directory = directory
        self.name_widget.set_directory(self.directory)
    
    def set_active(self, bool_value):
        
        self.name_widget.set_active(bool_value)
    
    def _build_widgets(self):
        
        self.name_widget = qt_ui.DefineControlNameWidget(self.directory)
        
        self.main_layout.addWidget(self.name_widget)