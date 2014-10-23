# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.


from vtool import qt_ui
from vtool import util_file
from vtool import util

if qt_ui.is_pyqt():
    from PyQt4 import QtGui, QtCore, Qt, uic
if qt_ui.is_pyside():
    from PySide import QtCore, QtGui
    
    
class SettingsWidget(qt_ui.BasicWidget):
    
    project_directory_changed = qt_ui.create_signal(object)
    code_directory_changed = qt_ui.create_signal(object)
    
    def __init__(self):
        super(SettingsWidget, self).__init__()
        
        self.project_history = []
        self.code_directories = []
    
    def _define_main_layout(self):
        layout = QtGui.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)
        return layout 
    
    def _build_widgets(self):
        
        self.project_directory_widget = qt_ui.GetDirectoryWidget()
        self.project_directory_widget.set_label('Project Directory')
        self.project_directory_widget.directory_changed.connect(self._project_directory_changed)
        
        history_label = QtGui.QLabel('Previous Projects')
        self.history_list = QtGui.QListWidget()
        self.history_list.setAlternatingRowColors(True)
        self.history_list.itemClicked.connect(self._history_item_selected)
        self.history_list.setSelectionMode(self.history_list.NoSelection)
                                
        self.code_directory_widget = CodeDirectoryWidget()
        self.code_directory_widget.set_label('Add Code Directory')
        self.code_directory_widget.directory_changed.connect(self._code_directory_changed)

        self.main_layout.addSpacing(5)
        self.main_layout.addWidget(history_label)
        self.main_layout.addWidget(self.history_list)
        self.main_layout.addWidget(self.project_directory_widget)
        self.main_layout.addSpacing(15)
        
        self.main_layout.addWidget(self.code_directory_widget)

    def _project_directory_changed(self, project):
        self.project_directory_changed.emit(project)
        
    def _code_directory_changed(self, code_directory):
        self.code_directory_changed.emit(code_directory)
        
    def _history_item_selected(self):
        item = self.history_list.currentItem()
        if not item:
            return
        
        directory = item.text()
        self.set_project_directory(directory)
        
    def get_project_directory(self):
        return self.project_directory_widget.get_directory()
        
    def set_project_directory(self, directory):
        self.project_directory_widget.set_directory(directory)

    def set_code_directory(self, directory):
        if directory:
            self.code_directory_widget.set_directory(directory)
            
    def set_history(self, project_list):
        
        self.project_history = project_list
        
        self.history_list.clear()
        
        items = []
        
        for history in self.project_history:
            item = QtGui.QListWidgetItem()
            item.setText(history)
            item.setSizeHint(QtCore.QSize(30, 40))
            
            items.append(item)
            self.history_list.addItem(item)
        
        #self.history_list.addItems(items)
        
        self.history_list.clearSelection()
        
    def set_code_list(self, code_directories):
        
        self.code_directories = code_directories
        self.code_list.clear()
        
        items = []
        
        for code in self.code_directories:
            item = QtGui.QListWidgetItem()
            item.setText(code)
            item.setSizeHint(QtCore.QSize(30, 40))
            
            items.append(item)
            self.code.addItem(item)
        
class CodeDirectoryWidget(qt_ui.GetDirectoryWidget):
    
    def __init__(self, parent = None):
        
        self.code_list = None
        self.label = 'directory'
        
        super(CodeDirectoryWidget, self).__init__(parent)
    
    def _define_main_layout(self):
        return QtGui.QVBoxLayout()
    
    def _build_widgets(self):
    
        file_layout = QtGui.QHBoxLayout()
    
        self.directory_label = QtGui.QLabel('directory')
        self.directory_label.setMinimumWidth(100)
        self.directory_label.setMaximumWidth(100)
        
        directory_browse = QtGui.QPushButton('Browse')
        directory_browse.setMaximumWidth(100)
        
        directory_browse.clicked.connect(self._browser)
        
        file_layout.addWidget(self.directory_label)
        file_layout.addWidget(directory_browse)
        
        code_label = QtGui.QLabel('Code Libraries')
        
        self.code_list = CodeList()
        self.code_list.setAlternatingRowColors(True)
        self.code_list.setSelectionMode(self.code_list.NoSelection)
        self.code_list.directories_changed.connect(self._send_directories)
        
        self.main_layout.addSpacing(5)
        self.main_layout.addWidget(code_label)
        self.main_layout.addWidget(self.code_list)
        self.main_layout.addLayout(file_layout)
        self.main_layout.addSpacing(15)
                
    def _text_changed(self, directory):
                
        directory = str(directory)
                
        if not util_file.is_dir(directory):
            return
        
        found = self.code_list.get_directories()
        
        if directory in found:
            return
        
        if found:
            found.insert(0, directory)
            
        if not found:
            found = [directory] 
                
        self.directory_changed.emit(found)
        
        self.code_list.refresh_code_list(found)
        
    def _send_directories(self, directories):
        self.directory_changed.emit(directories)

    
    def _browser(self):
        
        filename = qt_ui.get_file('C:/', self)
        
        filename = util_file.fix_slashes(filename)
        
        if filename and util_file.is_dir(filename):
            self._text_changed(filename)
    
    def set_directory(self, directory):
        
        directory = util.convert_to_sequence(directory)
        
        self.last_directory = self.directory
        self.directory = directory      
        
        self.code_list.refresh_code_list(directory)
        
        
class CodeList(QtGui.QListWidget):
    
    directories_changed = qt_ui.create_signal(object)
    
    def __init__(self):
        super(CodeList, self).__init__()
        
        self.setAlternatingRowColors(True)
        self.setSelectionMode(self.NoSelection)

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._item_menu)
        
        self._create_context_menu()
        
    def _item_menu(self, position):
        
        item = self.itemAt(position)
        
        if item:
            
            self.context_menu.exec_(self.viewport().mapToGlobal(position))
        
    def _create_context_menu(self):
        
        self.context_menu = QtGui.QMenu()
        
        remove_action = self.context_menu.addAction('Remove')
        
        remove_action.triggered.connect(self.remove_current_item)
        
    def remove_current_item(self, position):
        
        index = self.currentIndex()
        self.takeItem(index.row())
        
        self.directories_changed.emit(self.get_directories())
        
    def refresh_code_list(self, directories):
        
        self.clear()
    
        for directory in directories:
            self.addItem(directory)
            
            
    def get_directories(self):
        
        code_count = self.count()
        
        found = []
        
        if code_count:
            
            for inc in range(0, code_count):
            
                item = self.item(inc)
                if item:
                    found.append(str(item.text()))
            
        return found
        