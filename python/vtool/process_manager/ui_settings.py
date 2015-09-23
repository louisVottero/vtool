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
        self.settings = None
    
    def _define_main_layout(self):
        layout = QtGui.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)
        return layout 
    
    def _build_widgets(self):
        
        self.project_directory_widget = ProjectDirectoryWidget()
        self.project_directory_widget.set_label('Project Directory')
        self.project_directory_widget.directory_changed.connect(self._project_directory_changed)
        
        self.history_list = self.project_directory_widget.project_list
                             
        self.code_directory_widget = CodeDirectoryWidget()
        self.code_directory_widget.directory_changed.connect(self._code_directory_changed)

        self.editor_directory_widget = ExternalEditorWidget()
        self.editor_directory_widget.set_label('External Editor')

        self.main_layout.addWidget(self.project_directory_widget)
        self.main_layout.addWidget(self.code_directory_widget)
        self.main_layout.addWidget(self.editor_directory_widget)

    def _project_directory_changed(self, project):
        
        self.project_directory_changed.emit(project)
        
    def _code_directory_changed(self, code_directory):
        self.code_directory_changed.emit(code_directory)
      
    """ 
    def _history_item_selected(self):
        
        item = self.history_list.currentItem()
        if not item:
            return
        
        directory = item.text()
        
        self.set_project_directory(directory)
    """
    
    def get_project_directory(self):
        return self.project_directory_widget.get_directory()
        
    def set_project_directory(self, directory, history = None):
        self.project_directory_widget.set_directory(directory, history)
        

    def set_code_directory(self, directory):
        if directory:
            self.code_directory_widget.set_directory(directory)
            
    def set_history(self, directory, history):
        self.project_directory_widget.set_directory(directory, history)
        
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
            
    def set_settings(self, settings):
        self.settings = settings
        self.project_directory_widget.set_settings(settings)
        self.editor_directory_widget.set_settings(settings)
        
class ExternalEditorWidget(qt_ui.GetDirectoryWidget):
    
    def __init__(self, parent = None):
           
        super(ExternalEditorWidget, self).__init__(parent)
        
        self.settings = None
        
    def _browser(self):
        
        filename = qt_ui.get_file(self.get_directory() , self)
        
        filename = util_file.fix_slashes(filename)
        
        if filename and util_file.is_file(filename):
            self.directory_edit.setText(filename)
            self.directory_changed.emit(filename)
            self.settings.set('external_editor', str(filename))
    
    
    
    def set_settings(self, settings):
        
        self.settings = settings
        
        filename = self.settings.get('external_editor')
        
        if util_file.is_file(str(filename)):
            self.set_directory_text(filename)
            
   
class ProjectDirectoryWidget(qt_ui.GetDirectoryWidget):
    
    def __init__(self, parent = None):
        self.project_list = None
    
        super(ProjectDirectoryWidget, self).__init__(parent)
        
        self.settings = None
    
    def _define_main_layout(self):
        return QtGui.QVBoxLayout()
    
    def _build_widgets(self):
    
        file_layout = QtGui.QHBoxLayout()
    
        self.directory_label = QtGui.QLabel('directory')

        self.project_label = QtGui.QLabel('Project Libraries')
        
        directory_browse = QtGui.QPushButton('Browse')
        directory_browse.setMaximumWidth(100)
        
        directory_browse.clicked.connect(self._browser)

        file_layout.addWidget(self.directory_label)
        file_layout.addWidget(directory_browse)
        
        self.project_list = ProjectList()
        self.project_list.setAlternatingRowColors(True)
        self.project_list.setSelectionMode(self.project_list.NoSelection)
        self.project_list.directories_changed.connect(self._send_directories)
        self.project_list.itemClicked.connect(self._project_item_selected)
        
        self.main_layout.addSpacing(5)
        self.main_layout.addWidget(self.project_label)
        self.main_layout.addWidget(self.project_list)
        self.main_layout.addLayout(file_layout)
        
        self.main_layout.addSpacing(15)
        
    def _project_item_selected(self):
        
        item = self.project_list.currentItem()
        
        if not item:
            return
        
        directory = [item.text(0), item.text(1)]
        
        self.set_directory(directory)
        
        self.directory_changed.emit(directory)

    def _text_changed(self, directory):
         
        if type(directory) != list:
            directory = ['', directory]
        
        if not util_file.is_dir(directory[1]):
            
            return
        
        found = self.project_list.get_directories()
        
        if directory in found:    
            return
        
        if found:
            found.insert(0, directory)
            
        if not found:
            found = directory 
        
        self.directory_changed.emit(directory)
        
        self.set_label(directory[1])
        
        #self.project_list.refresh_project_list(directory, found)
        
    def _send_directories(self, directory):

        self.directory_changed.emit(directory)
        
        self.directory_label.setText(directory)

    
    def _browser(self):
        
        filename = qt_ui.get_folder('C:/', self)
        
        if not filename:
            return
        
        filename = util_file.fix_slashes(filename)
        
        found = self.project_list.get_directories()
        
        if filename in found:    
            return
        
        if found:
            found.insert(0, filename)
            
        if not found:
            found = [filename] 
        
        if filename and util_file.is_dir(filename):
            self._text_changed(filename)
            
            self.project_list.refresh_project_list(filename, found)
            
    def set_directory(self, directory, history = None):
        
        if type(directory) != list:
            directory = ['', directory]
        
        self.set_label(directory[1])
        
        if history:
            self.project_list.refresh_project_list(directory, history)
            
    def set_settings(self, settings):
        
        self.settings = settings
        self.project_list.set_settings(settings)

class ProjectList(QtGui.QTreeWidget):

    directories_changed = qt_ui.create_signal(object)

    def __init__(self):
        super(ProjectList, self).__init__()
        
        self.setAlternatingRowColors(True)
        self.setSelectionMode(self.NoSelection)
        self.setHeaderLabels(['name', 'directory'])

        self.setColumnWidth(0, 200)
        
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._item_menu)
        
        self._create_context_menu()
        self.settings = None     
        
    def _item_menu(self, position):
        
        item = self.itemAt(position)
        
        if item:
            self.setCurrentItem(item)
            self.context_menu.exec_(self.viewport().mapToGlobal(position))
        
    def _create_context_menu(self):
        
        self.context_menu = QtGui.QMenu()
        
        name_action = self.context_menu.addAction('Name')
        
        moveup_action = self.context_menu.addAction('Move Up')
        movedown_action = self.context_menu.addAction('Move Down')
        
        remove_action = self.context_menu.addAction('Remove')
        
        remove_action.triggered.connect(self.remove_current_item)
        name_action.triggered.connect(self.name_current_item)
        moveup_action.triggered.connect(self.move_current_item_up)
        movedown_action.triggered.connect(self.move_current_item_down)
        
    def name_current_item(self):
        
        item = self.currentItem()
        
        old_name = item.text(0)
        project_directory = item.text(1)
        
        new_name = qt_ui.get_new_name('Name Project', self, old_name)
        
        item.setText(0, new_name)
        
        if self.settings:
            
            self.settings.set('project_history', self.get_directories())
            self.settings.set('project_directory', [new_name, project_directory])
        
    def move_current_item_up(self):
        
        current_index = self.currentIndex()
        
        if current_index == None:
            return
        
        current_index = current_index.row()
        
        if current_index == 0:
            return
        
        current_item = self.takeTopLevelItem(current_index)
        
        self.insertTopLevelItem( (current_index - 1), current_item)

        self.setCurrentItem(current_item)
        
        name = str( current_item.text(0) )
        directory = str( current_item.text(1) )
        
        if self.settings:
            
            self.settings.set('project_history', self.get_directories())
            self.settings.set('project_directory', [name, directory])
        
    def move_current_item_down(self):
        
        current_index = self.currentIndex()
        
        if current_index == None:
            return
        
        current_index = current_index.row()
        
        count = self.topLevelItemCount()
        
        if current_index == (count-1):
            return
        
        current_item = self.takeTopLevelItem(current_index)
        
        self.insertTopLevelItem( (current_index + 1), current_item)
        
        self.setCurrentItem(current_item)
        
        name = str(current_item.text(0))
        directory = str(current_item.text(1))
        
        if self.settings:
            
            self.settings.set('project_history', self.get_directories())
            self.settings.set('project_directory', [name, directory])
        
    def remove_current_item(self):
        
        index = self.currentIndex()
        
        item = self.topLevelItem(index.row())
        
        self.takeTopLevelItem(index.row())
        
        project = self.settings.get('project_directory')
        
        if project == item.text(1):
            self.directories_changed.emit('')
        
        if self.settings:
            self.settings.set('project_history', self.get_directories())
            self.settings.set('project_directory', '')
        
    def refresh_project_list(self, current, history):
        
        if type(current) != list:
            current = ['', current]
        
        self.clear()
        
        self.project_history = history
        
        items = []
        
        select_item = None
        
        
        for history in self.project_history:
                
            if type(history) != list:
                history = ['', history]
            
            item = QtGui.QTreeWidgetItem()
            item.setText(0, history[0])
            item.setText(1, history[1])
            item.setSizeHint(0, QtCore.QSize(30, 40))
            
            if current[1] == history[1]:
                select_item = item
            
            items.append(item)
            self.addTopLevelItem(item)
        
        self.scrollToItem(select_item)
        self.setCurrentItem(select_item)
        
    def get_directories(self):
        
        project_count = self.topLevelItemCount()
        
        found = []
        
        if project_count:
            
            for inc in range(0, project_count):
            
                item = self.topLevelItem(inc)
                if item:
                    
                    name = item.text(0)
                    directory = item.text(1)
                    
                    found.append([name, directory])
            
        return found
     
    def set_settings(self, settings):
        
        self.settings = settings
        
class CodeDirectoryWidget(qt_ui.GetDirectoryWidget):
    
    def __init__(self, parent = None):
        
        self.code_list = None
        self.label = 'directory'
        
        super(CodeDirectoryWidget, self).__init__(parent)
    
    def _define_main_layout(self):
        return QtGui.QVBoxLayout()
    
    def _build_widgets(self):
    
        file_layout = QtGui.QHBoxLayout()
    
        directory_browse = QtGui.QPushButton('Browse')
        directory_browse.setMaximumWidth(100)
        
        directory_browse.clicked.connect(self._browser)
        
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
        
        filename = qt_ui.get_folder('C:/', self)
        
        if not filename:
            return
        
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
        
    def remove_current_item(self):
        
        index = self.currentIndex()
        self.takeItem(index.row())
        
        self.directories_changed.emit(self.get_directories())
        
    def refresh_code_list(self, directories):
        
        self.clear()
    
        for directory in directories:
            
            name = directory
            
            if not util_file.is_dir(directory):
                name = 'Directory Not Valid!   %s' % directory
            item = QtGui.QListWidgetItem()
            item.setText(name)
            item.setSizeHint(QtCore.QSize(30, 40))
            
            self.addItem(item)
            
            
    def get_directories(self):
        
        code_count = self.count()
        
        found = []
        
        if code_count:
            
            for inc in range(0, code_count):
            
                item = self.item(inc)
                if item:
                    found.append(str(item.text()))
            
        return found
        
