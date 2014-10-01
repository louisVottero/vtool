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
               
    def _define_tree_widget(self):
        return ProcessTreeWidget()
    
    def _define_manager_widget(self):
        return ManageProcessTreeWidget()
    
    def _item_clicked(self, name, item):
        super(ViewProcessWidget, self)._item_clicked(name, item)
        self.manager_widget.copy_widget.set_other_process(name, self.directory)
                        
    def get_process_item(self, name):
        return self.tree_widget.get_process_item(name)
    
    def get_current_process(self):
        return self.tree_widget.current_name
    
    def clear_sub_path_filter(self):
        self.filter_widget.clear_sub_path_filter()
         
class ManageProcessTreeWidget(qt_ui.ManageTreeWidget):
    
    def __init__(self):
        super(ManageProcessTreeWidget, self).__init__()
        
        self.directory = None
    
    def _define_main_layout(self):
        return QtGui.QHBoxLayout()
    
    def _build_widgets(self):
                        
        add_branch = QtGui.QPushButton('Add')
        add_branch.clicked.connect(self._add_branch)
        
        self.copy_button = QtGui.QPushButton('Copy')
        self.copy_button.clicked.connect(self._copy)
                
        self.copy_widget = CopyWidget()
        self.copy_widget.hide()
        
        self.copy_widget.pasted.connect(self._copy_done)
        self.copy_widget.canceled.connect(self._copy_done)
            
        self.main_layout.addWidget(add_branch)
        self.main_layout.addWidget(self.copy_button)
        self.main_layout.addWidget(self.copy_widget)
    
    def _add_branch(self):
        self.tree_widget.add_process('')
      
    def _copy(self):
            
        if self.copy_widget.isHidden():
            self.copy_widget.show()
        
        current_process = self.get_current_process()
        
        if not current_process:
            return
        
        self.copy_widget.show()
        self.copy_widget.set_process(current_process, self.directory)
        
        self.copy_button.setDisabled(True)
        self.setFocus()      
        
    def _copy_done(self):
        self.copy_widget.hide()
        self.copy_button.setEnabled(True)
        
    def get_current_process(self):
        return self.tree_widget.current_name
    
    def set_directory(self, directory):
        self.directory = directory
        
        
class ProcessTreeWidget(qt_ui.FileTreeWidget):
        
    def __init__(self):
        
        super(ProcessTreeWidget, self).__init__()
                
        self.setColumnWidth(0, 250)
                
        #self.setDragEnabled(True)
        #self.setAcceptDrops(True)
        self.setTabKeyNavigation(True)
        
        
    def _define_header(self):
        return ['name', 'size', 'date', 'options']  
    
    def _emit_item_click(self, item):
        self.current_name = item.get_name()
        self.item_clicked.emit(self.current_name, item)
                
    def _item_selection_changed(self):
        
        if self.last_item and self.current_item:
            if self.current_item.get_name() == self.last_item.get_name():
                return
        
        super(ProcessTreeWidget, self)._item_selection_changed()
               
    def _edit_finish(self, item):

        item = super(ProcessTreeWidget, self)._edit_finish(item)
        item.setExpanded(False)
        
    def _item_renamed(self, item):
        path = self.get_item_path_string(item)
        state = item.rename(path)
        return state
        
    def _get_process_paths(self):
        return process.find_processes(self.directory)
        
    def _load_processes(self, process_paths):
        
        current_item_name = ''
        
        if self.current_item:
            current_item_name = self.current_item.text(0)
            self.current_item = None
        
        self.clear()
        
        current_item = None
        
        for process_path in process_paths:
            item = self._add_process_item(process_path)
            
            if item.text(0) == current_item_name:
                current_item = item
                
        self.current_item = current_item
                
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
        
    def _add_process_items(self, item, path):
        
        parts = process.find_processes(path)
                
        pass_item = None
                
        for part in parts:
            last_item = self._add_process_item(part, item)
            if last_item:
                pass_item = last_item
            
        if pass_item:
            self.scrollToItem(pass_item,hint = QtGui.QAbstractItemView.PositionAtCenter)
            
        self.resizeColumnToContents(0)
        
    def _add_process_item(self, name, parent_item = None):
        
        expand_to = False
        
        current_item = self.current_item
        
        if not parent_item and current_item:
            parent_item = current_item
            expand_to = True
        
        if parent_item:
            
            item_path = self.get_item_path_string(parent_item)
            
            name = string.join([item_path, name], '/')
            
            if self._child_exists(name, parent_item):
                return
        
        item = ProcessItem(self.directory, name)
        
        if not parent_item:
            self.addTopLevelItem(item)
            
        if parent_item:
            parent_item.addChild(item)
            if expand_to:
                self.expandItem(parent_item)
        
        if item.has_parts():
            QtGui.QTreeWidgetItem(item)
        
        
        
        return item
     
    def _add_sub_items(self, item):
        
        self._delete_children(item)
        
        process_name = item.get_name()
        
        path = util_file.join_path(self.directory, process_name)
        
        self._add_process_items(item, path)

        

        
    def refresh(self):
        
        process_paths = self._get_process_paths()
        
        self._load_processes(process_paths)
        
        if self.current_item:
            self.current_item.setSelected(False)
        
        self.current_item = None
        self.last_item = None
        
    def add_process(self, name):
        
        current_item = self.current_item
        
        if not name:
            path = self.directory
            
            if current_item:
                path = self.get_item_path_string(current_item)
                
                if path:
                    path = util_file.join_path(self.directory, path)
                
            name = process.get_unused_process_name(path)
        
        self._add_process_item(name)
        
    def get_process_item(self, name):
        
        iterator = QtGui.QTreeWidgetItemIterator(self)
        
        while iterator:
            if iterator.text(0) == name:
                return iterator.value()
            
            ++iterator
            
        
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
        #return self.process.process_name
            
class ProcessItem(qt_ui.TreeWidgetItem):
    
    #directory_changed = QtCore.pyqtSignal(object) 
    
    def __init__(self, directory, name):
        super(ProcessItem, self).__init__()
        
        self.process = None
        
        self._add_process(directory, name)
        
        self.detail = False
        
        self.setSizeHint(0, QtCore.QSize(100,30))
        
        
    def _define_widget(self):
        return ProcessItemWidget()
        
    def _define_column(self):
        return 0
        
    def _add_process(self, directory, name):
        self.process = process.Process(name)
        self.process.set_directory(directory)
        
        split_name = name.split('/')
        
        self.setText(0, split_name[-1])
        self.process.create()
        
    def rename(self, name):
        
        return self.process.rename(name)
                
    def set_directory(self, directory):
        self.process.set_directory(directory)
                
    def get_path(self):
        return self.process.get_path()
    
    def get_name(self):
        return self.process.process_name
    
    def has_parts(self):
        if self.process.get_sub_processes():
            return True
        
        return False
    
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
        
        items = self.data_list.selectedItems()
        
        
        
        for item in items:
            
            print 'pasting items', item.text()
            process.copy_process_data( self.process, self.other_process, item.text())
    
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
        
        
        
        