# Copyright (C) 2016 Louis Vottero louis.vot@gmail.com    All rights reserved.

from vtool import qt_ui, qt
from vtool import util
from vtool.process_manager import process
from vtool import util_file

from vtool import logger
log = logger.get_logger(__name__)

class ProcessSettings(qt_ui.BasicWidget):
    
    def __init__(self):
        
        self.directory = None
        
        super(ProcessSettings, self).__init__()
        
        self.setContentsMargins(1,1,1,1)
        
    def set_directory(self, directory):
        
        log.debug('Set process setting widget directory %s' % self.directory)
        
        self.directory = directory
        self.name_widget.set_directory(self.directory)
    
    def set_active(self, bool_value):
        
        self.name_widget.set_active(bool_value)
    
    def _build_widgets(self):
        
        self.name_widget = qt_ui.DefineControlNameWidget(self.directory)
        self.name_widget.collapse_group()
        
        self.main_layout.addWidget(self.name_widget)
        
        self.main_layout.setAlignment(qt.QtCore.Qt.AlignTop)
        