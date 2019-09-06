# Copyright (C) 2019 Louis Vottero louis.vot@gmail.com    All rights reserved.

from vtool import qt, qt_ui
from vtool import util_file

import process
import ui_view

from vtool import logger
log = logger.get_logger(__name__)

class ProcessMaintenance(qt_ui.BasicWidget):
    
    def __init__(self):
        
        self.directory = None
        
        super(ProcessMaintenance, self).__init__()
        
        self.setContentsMargins(1,1,1,1)
        
    def set_directory(self, directory):
        
        log.debug('Set process setting widget directory %s' % self.directory)
        
        self.directory = directory
        self.backup_group.set_directory(self.directory)
        self.version_group.set_directory(self.directory)
    
    def set_active(self, bool_value):
        
        self.name_widget.set_active(bool_value)
    
    def _build_widgets(self):
                
        self.backup_group = BackupGroup()
        self.backup_group.collapse_group()
        
        self.version_group = VersionsGroup()
        self.version_group.collapse_group()
        
        self.main_layout.addWidget(self.backup_group)
        self.main_layout.addWidget(self.version_group)
        
        self.main_layout.setAlignment(qt.QtCore.Qt.AlignTop)
        

class BackupGroup(qt_ui.Group):
    
    def __init__(self, name = 'Backup'):
        super(BackupGroup, self).__init__(name)
        
        self.directory = None
        
        
    def _build_widgets(self):
        
        self.backup_history = BackupProcessFileWidget()
        
        self.backup_dir = qt.QLabel('Backup Directory:')
        
        self.main_layout.addWidget(self.backup_dir)
        self.main_layout.addWidget(self.backup_history)
    
    def set_directory(self, directory):
        
        if not directory:
            return
        
        self.directory = directory
        backup = self.backup_history.set_directory(directory)
        
        self.backup_dir.setText('Backup Directory: %s' % backup)
        

class VersionsGroup(qt_ui.Group):
    
    def __init__(self, name = 'Versions'):
        super(VersionsGroup, self).__init__(name)
        
        self.directory = None
        
    def _build_widgets(self):
        
        help_label = qt.QLabel('This utility helps remove old versions.\n After a process is finished, this can help save memory.\n  Be careful not to delete needed data.')
        
        self.prune_versions_widget = PruneVersionsWidget()
        
        self.main_layout.addWidget(help_label)
        self.main_layout.addWidget(self.prune_versions_widget)
    
    def set_directory(self, directory):
        
        if not directory:
            return
        
        self.directory = directory
        
        self.prune_versions_widget.set_directory(directory)
        
class PruneVersionsWidget(qt_ui.BasicWidget):
    
    def _define_main_layout(self):
        return qt.QVBoxLayout()
    
    def _build_widgets(self):
        
        
        self.data_tree = ui_view.DataTree()
        self.code_tree = ui_view.CodeTree()
        
        self._fill_headers('Data', self.data_tree)
        self._fill_headers('Code', self.code_tree)
        
        self._reset()
        
        self.main_layout.addWidget(self.data_tree)
        self.main_layout.addWidget(self.code_tree)
        
        
    
    def _fill_headers(self, name, tree_widget):
        
        tree_widget.setHeaderLabels([name, 'Version Count', 'Size'])
        
    def _reset(self):
        self._reset_states(self.data_tree)
        self._reset_states(self.code_tree)
        
    def _reset_states(self, tree):
        
        root = tree.invisibleRootItem()
        
        self._reset_item_children(1, root)
        self._reset_item_children(2, root)
    
    def _reset_item_children(self, column, item):
        
        child_count = item.childCount()
        
        for inc in range(0, child_count):
            
            child_item = item.child(inc)
            
            self._reset_column(column, child_item)
            
            self._reset_item_children(column, child_item)
     
    def _reset_column(self, column, item):
        
        item.setText(column, (' ' * 10) + '-')
        
        item.setBackground(column, item.background(0))
    
    def _load(self):

        self.data_tree.populate()
        self.code_tree.populate()

    def _populate_items(self, data_type, item = None):
        
        if data_type == 'data':
            tree_widget = self.data_tree
        if data_type == 'code':
            tree_widget = self.code_tree
        
        if not item:
            item = tree_widget.invisibleRootItem()
        
        if not item:
            return
        
        child_count = item.childCount()
        
        for inc in range(0, child_count):
            
            child_item = item.child(inc)
            
            name = child_item.text(0)
            
            if not name:
                continue
            
            folder = None
            
            if data_type == 'data':
                
                folder = self.process_inst.get_data_folder(name)
            
            if data_type == 'code':
                folder = self.process_inst.get_code_folder(name)
                
            if not folder:
                continue
                
            version_inst = util_file.VersionFile(folder)
            count = version_inst.get_count()
            size = util_file.get_folder_size(folder, round_value = 2)
            
            child_item.setText(1, str(count))
            child_item.setText(2, str(size))
            
            self._populate_items(data_type, child_item)

    def set_directory(self, directory):
        
        if not directory:
            return
        
        self.directory = directory
        
        process_inst = process.Process()
        process_inst.set_directory(directory)
        
        self.process_inst = process_inst
        
        self.data_tree.set_process(self.process_inst)
        self.code_tree.set_process(self.process_inst)
        
        self._load()
        
        self._populate_items('data')
        self._populate_items('code')
        
class BackupProcessFileWidget(qt_ui.BackupWidget):
    def _define_save_widget(self):
        return BackupProcessWidget()
    
    def _define_history_widget(self):
        return BackupProcessHistoryWidget()
    
    def set_directory(self, directory):
        super(BackupProcessFileWidget, self).set_directory(directory)
        
        if not directory:
            return
        
        log.debug('Backup history widget process path: %s' % directory)
        
        process_inst = process.Process()
        process_inst.set_directory(directory)
        
        backup_directory = process_inst.get_backup_path()
        
        log.debug('Backup history widget path: %s' % backup_directory)
        
        self.set_history_directory(backup_directory)
        
        if backup_directory == ( directory + '/.backup' ):
            backup_directory = 'local'
        
        return backup_directory
        
class BackupProcessWidget(qt_ui.DirectoryWidget):    
    
    file_changed = qt.create_signal()
    
    def _build_widgets(self):
        
        self.save_button = qt.QPushButton('Backup Process')
        
        self.save_button.setMaximumWidth(125)
        self.save_button.setMinimumWidth(qt_ui._save_button_minimum)
        
        self.save_button.setSizePolicy(qt.QSizePolicy.Minimum, qt.QSizePolicy.Fixed)
        
        self.save_button.clicked.connect(self._save)
        
        self.main_layout.addWidget(self.save_button)
        
        self.main_layout.setAlignment(qt.QtCore.Qt.AlignTop)
        
    def _save(self):
        
        process.backup_process(self.directory)
        self.file_changed.emit()
        
class BackupProcessHistoryWidget(qt_ui.HistoryFileWidget):
    
    def _build_widgets(self):
        super(BackupProcessHistoryWidget, self)._build_widgets()
        
        self.open_button.hide()
        