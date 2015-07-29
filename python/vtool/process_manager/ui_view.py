# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

import string

from vtool import util_file
from vtool import qt_ui

import process

if qt_ui.is_pyqt():
    from PyQt4 import QtGui, QtCore, Qt, uic
if qt_ui.is_pyside():
    from PySide import QtCore, QtGui

class ViewProcessWidget(qt_ui.EditFileTreeWidget):
    
    description = 'Process'
    
    sync_code = qt_ui.create_signal()
    
               
    def __init__(self):
        
        self.settings = None
        
        super(ViewProcessWidget, self).__init__()
        
    def _define_tree_widget(self):
        return ProcessTreeWidget()
    
    def _define_manager_widget(self):
        
        tree_manager = ManageProcessTreeWidget()
        
        tree_manager.sync_code.connect(self._sync_code)
        
        return tree_manager
    
    def _sync_code(self):
        self.sync_code.emit()
    
    def _item_selection_changed(self):
        
        name, item = super(ViewProcessWidget, self)._item_selection_changed()
        
        if not name:
            return
                
        name = self.tree_widget._get_parent_path(item)
        
        self.manager_widget.copy_widget.set_other_process(name, self.directory)
                        
    def get_process_item(self, name):
        return self.tree_widget.get_process_item(name)
    
    def get_current_process(self):
        return self.tree_widget.current_name
    
    def clear_sub_path_filter(self):
        self.filter_widget.clear_sub_path_filter()
        
    def set_settings(self, settings):
        self.settings = settings
        
        self.tree_widget.set_settings(settings)
         
class ManageProcessTreeWidget(qt_ui.ManageTreeWidget):
    
    sync_code = qt_ui.create_signal()
    
    def __init__(self):
        super(ManageProcessTreeWidget, self).__init__()
        
        self.directory = None
        
    
    def _define_main_layout(self):
        return QtGui.QVBoxLayout()
    
    def _build_widgets(self):

        self.copy_widget = CopyWidget()
        self.copy_widget.hide()
        
        self.copy_widget.pasted.connect(self._copy_done)
        self.copy_widget.canceled.connect(self._copy_done)
        
        self.main_layout.addWidget(self.copy_widget)

    def _add_branch(self):
        
        self.tree_widget.add_process('')
      
    def _add_top_branch(self):
        
        self.tree_widget.add_process(None)
      
    def _copy(self):
        
        current_process = self.get_current_process()
        
        if not current_process:
            return
            
        if self.copy_widget.isHidden():
            self.copy_widget.show()
            
        if not current_process:
            return
        
        self.copy_widget.show()
        self.copy_widget.set_process(current_process, self.directory)
        
        self.setFocus()  
        
        items = self.tree_widget.selectedItems()
        
        self.tree_widget.scrollToItem(items[0])
        
        self.sync_code.emit()
        
    def _copy_done(self):
        self.copy_widget.hide()
        
    def get_current_process(self):
        
        items = self.tree_widget.selectedItems()
        if not items:
            return
        
        parent_path = self.tree_widget._get_parent_path(items[0])
        
        return parent_path
    
    def set_directory(self, directory):
        self.directory = directory
        
    def set_tree_widget(self, tree_widget):
        self.tree_widget = tree_widget
        
        self.tree_widget.new_process.connect(self._add_branch)
        self.tree_widget.new_top_process.connect(self._add_top_branch)
        self.tree_widget.copy_special_process.connect(self._copy)
        
        
class ProcessTreeWidget(qt_ui.FileTreeWidget):
    
    new_process = qt_ui.create_signal()
    new_top_process = qt_ui.create_signal()    
    copy_special_process = qt_ui.create_signal()
    delete_process = qt_ui.create_signal()
    item_renamed = qt_ui.create_signal(object)
        
    def __init__(self):
        
        self.settings = None
        
        super(ProcessTreeWidget, self).__init__()
                
        self.setColumnWidth(0, 250)
        
        self.setTabKeyNavigation(True)
        self.setHeaderHidden(True)
        self.activation_fix = True
        
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._item_menu)
        
        self._create_context_menu()
        self.paste_item = None
                
        self.setColumnWidth(1, 20)
                
        self.setSelectionBehavior(self.SelectItems)
        
        
    
    def mouseDoubleClickEvent(self, event):
        self.doubleClicked.emit(0)
    
    def mouseMoveEvent(self, event):
        model_index =  self.indexAt(event.pos())
        
        item = self.itemAt(event.pos())
        
        if not item or model_index.column() == 1:
            self.clearSelection()
            
        
        if event.button() == QtCore.Qt.RightButton:
            return
        
        if model_index.column() == 0 and item:
            super(ProcessTreeWidget, self).mouseMoveEvent(event)
        
    def mousePressEvent(self, event):
        
        model_index =  self.indexAt(event.pos())
        
        item = self.itemAt(event.pos())
        
        if not item or model_index.column() == 1:
            self.clearSelection()
        
        if event.button() == QtCore.Qt.RightButton:
            return
        
        if model_index.column() == 0 and item:
            super(ProcessTreeWidget, self).mousePressEvent(event)

    def _item_menu(self, position):
        
        item = self.itemAt(position)
            
        if item:
            self.new_top_level_action.setVisible(True)
            self.rename_action.setVisible(True)
            self.copy_action.setVisible(True)
            self.copy_special_action.setVisible(True)
            self.remove_action.setVisible(True)
        
        if not item:
            self.new_top_level_action.setVisible(False)
            self.rename_action.setVisible(False)
            self.copy_action.setVisible(False)
            self.copy_special_action.setVisible(False)
            self.remove_action.setVisible(False)
        
        self.context_menu.exec_(self.viewport().mapToGlobal(position))
        
    def visualItemRect(self, item):
        pass
        
    def _create_context_menu(self):
        
        self.context_menu = QtGui.QMenu()
        
        new_process_action = self.context_menu.addAction('New Process')
        self.new_top_level_action = self.context_menu.addAction('New Top Level Process')
        
        self.context_menu.addSeparator()
        self.context_menu.addSeparator()
        self.rename_action = self.context_menu.addAction('Rename')
        self.copy_action = self.context_menu.addAction('Copy')
        self.paste_action = self.context_menu.addAction('Paste')
        self.paste_action.setVisible(False)
        self.copy_special_action = self.context_menu.addAction('Copy Special')
        self.remove_action = self.context_menu.addAction('Delete')
        self.context_menu.addSeparator()
        browse_action = self.context_menu.addAction('Browse')
        refresh_action = self.context_menu.addAction('Refresh')
        
        self.new_top_level_action.triggered.connect(self._new_top_process)
        new_process_action.triggered.connect(self._new_process)
        
        browse_action.triggered.connect(self._browse)
        refresh_action.triggered.connect(self.refresh)
        self.rename_action.triggered.connect(self._rename_process)
        self.copy_action.triggered.connect(self._copy_process)
        self.paste_action.triggered.connect(self._paste_process)
        self.copy_special_action.triggered.connect(self._copy_special_process)
        self.remove_action.triggered.connect(self._remove_current_item)
        
    def _new_process(self):
        self.new_process.emit()
    
    def _new_top_process(self):
        self.new_top_process.emit()
    
    def _rename_process(self):
        items = self.selectedItems()
        
        if not items:
            return
        
        item = items[0]
        
        old_name = item.get_name()
        
        old_name = old_name.split('/')[-1]
        
        new_name = qt_ui.get_new_name('New Name', self, old_name)
        
        if not new_name:
            return
        
        item.setText(0, new_name)
        
        if not self._item_rename_valid(old_name, item):
            item.setText(0, old_name)
            return
        
        rename_worked = self._item_renamed(item)
        
        if not rename_worked:
            item.setText(0, old_name)
        
        if rename_worked:
            self.item_renamed.emit(item)
        
    def _copy_process(self):
        
        items = self.selectedItems()
        if not items:
            return
        
        item = items[0]
        
        self.paste_action.setVisible(True)
        self.paste_item = item
        
        path = self._get_parent_path(item)
        
        self.paste_action.setText('Paste process: %s' % path)
        
    def _paste_process(self):
        
        self.paste_action.setVisible(False)
        
        if not self.paste_item:
            return
        
        source_process = self.paste_item.get_process()
        
        target_process = None
        
        items = self.selectedItems()
        if items:
            target_item = items[0]
            target_process = target_item.get_process()            
        if not items:
            target_item = self
        
        
        new_process = process.copy_process(source_process, target_process)
        
        self.paste_item = None
        
        new_item = self._add_process_item(new_process.get_name(), target_item)
        
        if target_process:
            self.collapseItem(target_item)
            self.expandItem(target_item)
            
        if not target_process:
            self.scrollToItem(new_item)
    
    def _copy_special_process(self):
        self.copy_special_process.emit()
        
    def _remove_current_item(self):
        self.delete_process()
        
    def _define_header(self):
        return ['name']  
    
    def _edit_finish(self, item):
    
        item = super(ProcessTreeWidget, self)._edit_finish(item)  
    
        self.item_renamed.emit(item)
        
    def _item_rename_valid(self, old_name, item):
        
        state = super(ProcessTreeWidget, self)._item_rename_valid(old_name, item)

        if state == False:
            return state
        
        if state == True:
            name = self._get_parent_path(item)
            path = util_file.join_path(self.directory, name)
            
            if util_file.is_dir(path):
                return False
            
            return True
        
        return False
        
    def _item_renamed(self, item):
        
        path = self.get_item_path_string(item)
        state = item.rename(path)
        
        if state == True:
            item.setExpanded(False)
        
        return state
        
    def _get_process_paths(self):
        return process.find_processes(self.directory)
        
    def _load_processes(self, process_paths):

        self.clear()
        
        for process_path in process_paths:
            self._add_process_item(process_path)
            
            
            
            
    def _get_parent_path(self, item):
        
        parents = self.get_tree_item_path(item)
        parent_names = self.get_tree_item_names(parents)
        
        names = []
        
        for name in parent_names:
            names.append(name[0])
        
        names.reverse()
        
        path = string.join(names, '/')
        
        return path
        
    def _child_exists(self, child_name, item):
        
        children = self.get_tree_item_children(item)
        
        for child in children:
            if hasattr(child, 'get_name'):
                if child_name == child.get_name():
                    return True
        
        return False

    def _goto_settings_process(self):
        
        if not self.settings:
            return
        
        settings_process = self.settings.get('process')
            
        if not settings_process:
            return
        
        iterator = QtGui.QTreeWidgetItemIterator(self)
        
        while iterator.value():
            item = iterator.value()
            
            if hasattr(item, 'directory') and hasattr(item, 'name'):
            
                if item.directory == settings_process[1]:
                        
                    if settings_process[0].startswith(item.name):
                        index = self.indexFromItem(item)
                        self.setExpanded(index, True)
                        
                    if settings_process[0] == item.name:
                        self.setCurrentItem(item)
                
            iterator += 1

    def _add_process_items(self, item, path):
        
        parts = process.find_processes(path)

        pass_item = None
                
        for part in parts:
            last_item = self._add_process_item(part, item)
            if last_item:
                pass_item = last_item
            
        #if pass_item:
        #    self.scrollToItem(pass_item,hint = QtGui.QAbstractItemView.PositionAtCenter)
            
        
        
    def _add_process_item(self, name, parent_item = None, create = False):
                
        expand_to = False
        
        current_item = self.currentItem()
        
        if not parent_item and current_item:
            parent_item = current_item
            expand_to = True
        
        if parent_item:
            
            item_path = self.get_item_path_string(parent_item)
            
            if item_path:            
                name = string.join([item_path, name], '/')
            
                if self._child_exists(name, parent_item):
                    return
                
            if not item_path:
                parent_item = None
        
        
        item = ProcessItem(self.directory, name)
        
        if create:
            item.create()
        
        if not parent_item:
            self.addTopLevelItem(item)
            
        if parent_item:
            parent_item.addChild(item)
            if expand_to:
                self.expandItem(parent_item)
        
        if item.has_parts():
            QtGui.QTreeWidgetItem(item)
        
       
        
        return item

    def _has_item_parent(self, child_item, parent_item):
        
        if not child_item:
            return
        if not parent_item:
            return
        
        parent = child_item.parent()
        
        if not parent:
            return
        
        if parent_item.matches(parent):
            return True
        
        while parent:
            parent = parent.parent()
        
            if parent_item.matches(parent):
                return True

    def _item_collapsed(self, item):
        
        current_item = self.currentItem()
        
        if self._has_item_parent(current_item, item):
            self.setCurrentItem(item)
        

    def _add_sub_items(self, item):
        
        self._delete_children(item)
        
        process_name = item.get_name()
        
        path = util_file.join_path(self.directory, process_name)
        
        self._add_process_items(item, path)
        
    def _browse(self):
        current_item = self.currentItem()
        process = current_item.get_process()
        
        path = process.get_path()
        util_file.open_browser(path)

    def refresh(self):
        
        self.clearSelection()
                
        process_paths = self._get_process_paths()
        
        self._load_processes(process_paths)
                
        self.current_item = None
        self.last_item = None
        
        self._goto_settings_process()
        
        
        
    def add_process(self, name):
        
        current_item = self.currentItem()
        
        parent_item = None
        
        if name == '':
            path = self.directory
            
            if current_item:
                path = self.get_item_path_string(current_item)
                
                if path:
                    path = util_file.join_path(self.directory, path)
                
            name = process.get_unused_process_name(path)
            
        if name == None:
        
            name = process.get_unused_process_name(self.directory)
            parent_item = self.invisibleRootItem()
        
        item = self._add_process_item(name, parent_item = parent_item, create = True)
        
        if not item.parent():
            self.setCurrentItem(item)
        
    def delete_process(self):
        
        current_item = self.selectedItems()
        
        if current_item:
            current_item = current_item[0]
            
        if not current_item:
            return
        
        parent_path = self._get_parent_path(current_item)

        delete_permission = qt_ui.get_permission('Delete %s?' % parent_path, self)
        
        if not delete_permission:
            return
            
        process_instance = process.Process(parent_path)
        process_instance.set_directory(self.directory)
        process_instance.delete()
        
        parent_item = current_item.parent()
        
        if parent_item:
            parent_item.removeChild(current_item)
            
        if not parent_item:
            
            index = self.indexOfTopLevelItem(current_item)
            
            self.takeTopLevelItem(index)
            self.clearSelection()
        
    def get_process_item(self, name):
        
        iterator = QtGui.QTreeWidgetItemIterator(self)
        
        while iterator.value():
            if iterator.text(0) == name:
                return iterator.value()
            
            iterator += 1
            
    def set_settings(self, settings):
        self.settings = settings
        
        process_settings = self.settings.get('process')
        
        self._goto_settings_process()
        
        """
        if process_settings:
            iterator = QtGui.QTreeWidgetItemIterator(self)
            
            while(iterator.value()):
                
                current_item = iterator.value()
                iterator += 1
                
                if not hasattr(current_item, 'name') or not hasattr(current_item, 'directory'):
                    continue
                
                if not process_settings[1] == current_item.directory:
                    continue
                
                if process_settings[0].startswith(current_item.name):
                    index = self.indexFromItem(current_item)
                    self.setExpanded(index, True)
                
                if current_item.name == process_settings[0]:

                    self.setCurrentItem(current_item)
        """

                
class SimpleItem(qt_ui.TreeWidgetItem):
    
    def __init__(self, name):
        super(SimpleItem, self).__init__()
        
        self.orig_name = name
        name = util_file.get_dirname(name)
        
        self.name = name
        
        self.detail = True
        
        basename = util_file.get_basename(self.orig_name)
        self.setText(0, basename)
        
    def get_name(self):
        return self.name

    def get_detail_name(self):
        return self.orig_name
        
class ProcessDetailItem(qt_ui.TreeWidgetItem):
    
    def __init__(self, directory, name):
        super(ProcessDetailItem, self).__init__()
        
        self.orig_name = name
        name = util_file.get_dirname(name)
        
        self.name = name
        self.process = None
        
        self._add_process(directory, name)
        
        self.detail = True
        
        
    def _add_process(self, directory, name):
        self.process = process.Process(name)
        self.process.set_directory(directory)
        
        split_name = self.orig_name.split('/')
        
        self.setText(0, split_name[-1])
        self.process.create()
        
    def _define_widget(self):
        return ProcessItemWidget()
    
    def get_path(self):
        self.process.get_code_path()
        
    def get_detail_name(self):
        return self.orig_name
    
    def get_name(self):
        return self.name
            
class ProcessItem(qt_ui.TreeWidgetItem):
    
    def __init__(self, directory, name):
        super(ProcessItem, self).__init__()
        
        self.process = None
        
        self.directory = directory
        self.name = name
        
        split_name = name.split('/')
        
        self.setText(0, split_name[-1])
        
        self.detail = False
        
        self.setSizeHint(0, QtCore.QSize(100,30))
        
    def _define_widget(self):
        return ProcessItemWidget()
        
    def _define_column(self):
        return 0
        
    def _add_process(self, directory, name):
        
        
        self.process = process.Process(name)
        self.process.set_directory(directory)
        
        self.process.create()
        
    def _get_process(self):
        
        process_instance = process.Process(self.name)
        process_instance.set_directory(self.directory)
        
        return process_instance
    
        
    def create(self):
        
        process_instance = self._get_process()
        process_instance.create()    
    
        
    def rename(self, name):
        
        process_instance = self._get_process()
            
        state = process_instance.rename(name)
        
        if state:
            self.name = name
        
        return state
                
    def set_directory(self, directory):
        
        self.directory = directory
           
    def get_process(self):
        return self._get_process()
           
    def get_path(self):
        
        process_instance = self._get_process()
        
        return process_instance.get_path()
        
    
    def get_name(self):
        
        process_instance = self._get_process()
        
        return process_instance.process_name
    
    def has_parts(self):
        
        process_instance = self._get_process()
        
        if process_instance.get_sub_processes():
            return True
        
        return False
    
    def matches(self, item):
        
        if not item:
            return False
        
        if not hasattr(item, 'name'):
            return False
        
        if not hasattr(item, 'directory'):
            return False
        
        if item.name == self.name and item.directory == self.directory:
            return True
    
class ProcessItemWidget(qt_ui.TreeItemWidget):

    def _build_widgets(self):
        super(ProcessItemWidget, self)._build_widgets()
        
class CopyWidget(qt_ui.BasicWidget):
    
    canceled = qt_ui.create_signal()
    pasted = qt_ui.create_signal()
    
    def __init__(self):
        
        super(CopyWidget, self).__init__()
        
        self.process = None
    
    def _build_widgets(self):
        
        self.copy_from = QtGui.QLabel('Copy from:')
        self.copy_from.setAlignment(QtCore.Qt.AlignCenter)
        
        self.tabs = QtGui.QTabWidget()
        
        self.data_list = QtGui.QListWidget()
        self.code_list = QtGui.QListWidget()
        
        self.data_list.setMaximumHeight(300)
        self.code_list.setMaximumHeight(300)
        
        self.data_list.setSortingEnabled(True)
        self.data_list.setSelectionMode(self.data_list.ExtendedSelection)
        self.code_list.setSortingEnabled(True)
        self.code_list.setSelectionMode(self.code_list.ExtendedSelection)
        
        self.tabs.addTab(self.data_list, 'Data')
        self.tabs.addTab(self.code_list, 'Code')
        
        h_layout = QtGui.QHBoxLayout()
        
        self.paste_button = QtGui.QPushButton('Paste')
        self.paste_button.setDisabled(True)
        self.paste_button.clicked.connect(self._paste)
        cancel = QtGui.QPushButton('Cancel')
        
        self.paste_button.clicked.connect(self.pasted)
        cancel.clicked.connect(self.canceled)
        
        h_layout.addWidget(self.paste_button)
        h_layout.addWidget(cancel)
        
        self.paste_to = QtGui.QLabel('Paste to:')
        self.paste_to.setAlignment(QtCore.Qt.AlignCenter)
        
        self.main_layout.addWidget(self.copy_from)
        self.main_layout.addWidget(self.tabs)
        self.main_layout.addWidget(self.paste_to)
        self.main_layout.addLayout(h_layout)
        
    def _populate_lists(self):
        
        self.data_list.clear()
        self.code_list.clear()
        
        data_folders = self.process.get_data_folders()
        
        for folder in data_folders:
            self.data_list.addItem(folder)
        
        code_folders = self.process.get_code_folders()
        
        for folder in code_folders:
            self.code_list.addItem(folder)
            
    def _paste(self):
        
        self._paste_data()
        
        self._paste_code()
        
    def _paste_data(self):
        
        data_items = self.data_list.selectedItems()
        
        if not data_items:
            return
        
        for item in data_items:
            name = item.text()
            
            process.copy_process_data( self.process, self.other_process, name)
            
    def _paste_code(self):
        
        code_items = self.code_list.selectedItems()
    
        if not code_items:
            return
    
        found = []
        
        manifest = ''
    
        for item in code_items:
            name = item.text()
            
            if not name:
                continue
            
            if name == 'manifest':
                manifest = name
                
            if not name == 'manifest':
                found.append(name)
        
        if manifest:        
            found.append(manifest)
        
        for name in found:
            process.copy_process_code( self.process, self.other_process, name)
    
    def set_process(self, process_name, process_directory):
        
        process_inst = process.Process(process_name)
        process_inst.set_directory(process_directory)
        
        self.process = process_inst
        
        self._populate_lists()
        
        self.copy_from.setText('Copy from:  %s' % process_name)
        
    def set_other_process(self, process_name, process_directory):
        
        if not self.process:
            return
        
        if process_name == self.process.get_name():
            self.paste_to.setText('Paste to:')
            self.paste_button.setDisabled(True)
            return
        
        process_inst = process.Process(process_name)
        process_inst.set_directory(process_directory)
        
        self.other_process = process_inst
        
        self.paste_to.setText('Paste to:  %s' % process_name)  
        self.paste_button.setEnabled(True)
        
        
        
        