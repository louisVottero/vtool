# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

global type_QT

import util
import util_file
import threading
import string
import re
import random


try:
    from PySide import QtCore, QtGui
    
    shiboken_broken = False
    
    try:
        from shiboken import wrapInstance
    except:
        try:
            from PySide.shiboken import wrapInstance
        except:
            shiboken_broken = True
        
    if not shiboken_broken:
        type_QT = 'pyside'
        util.show('using pyside')
        
    if shiboken_broken:
        type_QT = None
    
except:
    type_QT = None

if not type_QT == 'pyside':
    try:
        import PyQt4
        from PyQt4 import QtGui, QtCore, Qt, uic
        import sip
        type_QT = 'pyqt'
        
        util.show('using pyQT')
        
    except:
        type_QT = None
    

def is_pyqt():
    global type_QT
    if type_QT == 'pyqt':
        return True
    return False
    
def is_pyside():
    global type_QT
    if type_QT == 'pyside':
        return True
    return False

def build_qt_application(*argv):
    application = QtGui.QApplication(*argv)
    return application

def create_signal(*arg_list):
        
    if is_pyqt():
        return QtCore.pyqtSignal(*arg_list)
    if is_pyside():
        return QtCore.Signal(*arg_list)

class BasicGraphicsView(QtGui.QGraphicsView):
    
    def __init__(self):
        
        super(BasicGraphicsView, self).__init__()
                
        self.scene = QtGui.QGraphicsScene()
        #self.scene.set
        
        button = QtGui.QGraphicsRectItem(20,20,20,20)
        
        button.setFlags(QtGui.QGraphicsItem.ItemIsMovable)
        button.setFlags(QtGui.QGraphicsItem.ItemIsSelectable)
        
        graphic = QtGui.QGraphicsPixmapItem()
        
        
        self.scene.addItem(button)
        
        self.setScene(self.scene)

class BasicWindow(QtGui.QMainWindow):
    
    title = 'BasicWindow'

    def __init__(self, parent = None):
        super(BasicWindow, self).__init__(parent)
        
        self.setWindowTitle(self.title)
        self.setObjectName(self.title)
        
        main_widget = QtGui.QWidget()
        
        self.main_layout = self._define_main_layout()
        
        util.show('Main layout: %s' % self.main_layout)
        
        main_widget.setLayout(self.main_layout)
        
        self.setCentralWidget( main_widget )
        
        self.main_layout.expandingDirections()
        self.main_layout.setContentsMargins(1,1,1,1)
        self.main_layout.setSpacing(2)
        
        self._build_widgets()
        
    def _define_main_layout(self):
        return QtGui.QVBoxLayout()
    
    def _build_widgets(self):
        return
       
class DirectoryWindow(BasicWindow):
    
    def __init__(self, parent = None):
        
        self.directory = None
        
        super(DirectoryWindow, self).__init__(parent)
        
    def set_directory(self, directory):
        self.directory = directory
       
class BasicWidget(QtGui.QWidget):

    def __init__(self, parent = None):
        super(BasicWidget, self).__init__(parent)
        
        self.main_layout = self._define_main_layout() 
        self.main_layout.setContentsMargins(2,2,2,2)
        self.main_layout.setSpacing(2)
        
        self.setLayout(self.main_layout)
        
        self._build_widgets()

    def _define_main_layout(self):
        layout = QtGui.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)
        return layout
        
    def _build_widgets(self):
        pass
    
class BasicDialog(QtGui.QDialog):
    
    def __init__(self, parent = None):
        super(BasicDialog, self).__init__(parent)
        
        self.main_layout = self._define_main_layout() 
        self.main_layout.setContentsMargins(2,2,2,2)
        self.main_layout.setSpacing(2)
        
        self.setLayout(self.main_layout)
        
        self._build_widgets()  
            
    def _define_main_layout(self):
        layout = QtGui.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)
        return layout

    def _build_widgets(self):
        pass
       
        
class BasicDockWidget(QtGui.QDockWidget):
    def __init__(self, parent = None):
        super(BasicWidget, self).__init__()
        
        self.main_layout = self._define_main_layout() 
        self.main_layout.setContentsMargins(2,2,2,2)
        self.main_layout.setSpacing(2)
        
        self.setLayout(self.main_layout)
        
        self._build_widgets()

    def _define_main_layout(self):
        layout = QtGui.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)
        return layout
        
    def _build_widgets(self):
        pass

        
class DirectoryWidget(BasicWidget):
    def __init__(self, parent = None):
        
        self.directory = None
        self.last_directory = None
        
        super(DirectoryWidget, self).__init__()
        
        
        
    def set_directory(self, directory):
        
        self.last_directory = self.directory
        self.directory = directory
     
    
       
class TreeWidget(QtGui.QTreeWidget):
    
    def __init__(self):
        super(TreeWidget, self).__init__()

        self.title_text_index = 0

        self.itemExpanded.connect(self._item_expanded)

        self.setExpandsOnDoubleClick(False)
        
        version = util.get_maya_version()
        if version < 2016:
            self.setAlternatingRowColors(True)
            
        self.setSortingEnabled(True)
        
        self.sortByColumn(self.title_text_index, QtCore.Qt.AscendingOrder)
        
        self.itemActivated.connect(self._item_activated)
        self.itemChanged.connect(self._item_changed)
        self.itemSelectionChanged.connect(self._item_selection_changed)
        self.itemClicked.connect(self._item_clicked)
        
        self.text_edit = True
        self.edit_state = None
        self.old_name = None
        
        self.last_item = None
        self.current_item = None
        self.current_name = None
        
        if util.is_in_nuke():
            self.setAlternatingRowColors(False)
                
        if not util.is_in_maya() and not util.is_in_nuke():
            palette = QtGui.QPalette()
            palette.setColor(palette.Highlight, QtCore.Qt.gray)
            self.setPalette(palette)
    
    def _define_item(self):
        return QtGui.QTreeWidgetItem()
    
    def _define_item_size(self):
        return 
        
    def _clear_selection(self):
        
        self.clearSelection()
        self.current_item = None
        
        if self.edit_state:
            self._edit_finish(self.last_item)
            
    def _item_clicked(self, item, column):
        
        self.last_item = self.current_item
        
        self.current_item = self.currentItem()

        if not item or column != self.title_text_index:
            if self.last_item:
                self._clear_selection()

    def mousePressEvent(self, event):
        super(TreeWidget, self).mousePressEvent(event)
        
        item = self.itemAt(event.x(), event.y())
                
        if not item:
            self._clear_selection()
                          
    def _item_selection_changed(self):
        
        item_list = self.selectedItems()
        
        current_item = None
        
        if item_list:
            current_item = item_list[0]
        
        if current_item:
            self.current_name = current_item.text(self.title_text_index)
        
        if self.edit_state:
            self._edit_finish(self.edit_state)
    
        if not current_item:        
            self._emit_item_click(current_item)
        
    def _emit_item_click(self, item):
        
        if item:
            name = item.text(self.title_text_index)
        if not item:
            name = ''
                        
        self.itemClicked.emit(item, 0)      
            
    def _item_changed(self, current_item, previous_item):
        
        if self.edit_state:
            self._edit_finish(previous_item)                      
        
    def _item_activated(self, item):
        
        if not self.edit_state:
            
            if self.text_edit:
                self._edit_start(item)
            return
                
        if self.edit_state:
            self._edit_finish(self.edit_state)
            
            return
            
    def _item_expanded(self, item):
        self._add_sub_items(item) 
        #self.resizeColumnToContents(self.title_text_index)
        
    def _edit_start(self, item):
        
        self.old_name = str(item.text(self.title_text_index))
        
        #close is needed
        self.closePersistentEditor(item, self.title_text_index)
        
        self.openPersistentEditor(item, self.title_text_index)
        
        self.edit_state = item
        
        return
        
    
    def _edit_finish(self, item):
        
        if not hasattr(self.edit_state, 'text'):
            return
        
        self.edit_state = None
               
        
        if type(item) == int:
            return self.current_item
        
        self.closePersistentEditor(item, self.title_text_index)
        
        state = self._item_rename_valid(self.old_name, item)
        
        if not state:
            item.setText(self.title_text_index, self.old_name ) 
            return item
            
        if state:
        
            state = self._item_renamed(item)
            
            if not state:
                item.setText( self.title_text_index, self.old_name  )
         
            return item
                
        return item
    
    def _item_rename_valid(self, old_name, item):
        
        new_name = item.text(self.title_text_index)
        
        if not new_name:
            return False
        
        if self._already_exists(item):
            return False
        
        if old_name == new_name:
            return False
        if old_name != new_name:
            return True
    
    def _already_exists(self, item, parent = None):    
        
        name = item.text(0)
        parent = item.parent()
        
        if not parent:
        
            skip_index = self.indexFromItem(item)
            skip_index = skip_index.row()
        
        
            for inc in range(0, self.topLevelItemCount() ):
                
                if skip_index == inc:
                    continue
                
                other_name = self.topLevelItem(inc).text(0)
                other_name = str(other_name)
                                
                if name == other_name:
                    return True
        
        if parent:
            
            skip_index = parent.indexOfChild(item)
            
            for inc in range( 0, parent.childCount() ):
                
                if inc == skip_index:
                    continue
                
                other_name = parent.child(inc).text(0)
                other_name = str(other_name)
                
                if name == other_name:
                    return True
                
            
        return False
    
    
    
    def _item_renamed(self, item):
        return False

    def _delete_children(self, item):
        self.delete_tree_item_children(item)
        
    def _add_sub_items(self, item):
        pass
        
    def addTopLevelItem(self, item):
        
        super(TreeWidget, self).addTopLevelItem(item)
        
        if hasattr(item, 'widget'):
            if hasattr(item, 'column'):
                self.setItemWidget(item, item.column, item.widget)
                
            if not hasattr(item, 'column'):
                self.setItemWidget(item, 0, item.widget)
                
    def insertTopLevelItem(self, index, item):
        super(TreeWidget, self).insertTopLevelItem(index, item)
        
        if hasattr(item, 'widget'):
            if hasattr(item, 'column'):
                self.setItemWidget(item, item.column, item.widget)
                
            if not hasattr(item, 'column'):
                self.setItemWidget(item, 0, item.widget)
           
    def unhide_items(self):
            
        for inc in range( 0, self.topLevelItemCount() ):
            item = self.topLevelItem(inc)
            self.setItemHidden(item, False)

    def filter_names(self, string):
        
        self.unhide_items()
                        
        for inc in range( 0, self.topLevelItemCount() ):
                
            item = self.topLevelItem(inc)
            text = str( item.text(self.title_text_index) )
            
            string = str(string)
            
            if not text.startswith(string) and not text.startswith(string.upper()):
                
                self.setItemHidden(item, True)  
            
    def get_tree_item_path(self, tree_item):
                
        parent_items = []
        parent_items.append(tree_item)
        
        if not tree_item:
            return
        
        
        try:
            #when selecting an item in the tree and refreshing it will throw this error:
            #wrapped C/C++ object of type ProcessItem has been deleted
            parent_item = tree_item.parent()
        except:
            parent_item = None
        
        while parent_item:
            parent_items.append(parent_item)
            
            parent_item = parent_item.parent()
            
        return parent_items
    
    def get_tree_item_names(self, tree_items):
        
        item_names = []
        
        if not tree_items:
            return item_names
        
        for tree_item in tree_items:
            name = self.get_tree_item_name(tree_item)
            if name:
                item_names.append(name)    
            
        return item_names
    
    def get_tree_item_name(self, tree_item):
        try:
            #when selecting an item in the tree and refreshing it will throw this error:
            #wrapped C/C++ object of type ProcessItem has been deleted
            count = QtGui.QTreeWidgetItem.columnCount( tree_item )
        except:
            count = 0
            
        name = []
            
        for inc in range(0, count):
                
            name.append( str( tree_item.text(inc) ) )
            
        return name
    
    def get_item_path_string(self, item):
        
        parents = self.get_tree_item_path(item)
        parent_names = self.get_tree_item_names(parents)
        
        
        
        names = []
        
        if not parent_names:
            return
        
        if len(parent_names) == 1 and not parent_names[0]:
            return
        
        for name in parent_names:
            names.append(name[0])
        
        names.reverse()
        
        path = string.join(names, '/')
        
        return path
    
    def delete_tree_item_children(self, tree_item):
        count = tree_item.childCount()
        
        if count <= 0:
            return
        
        children = tree_item.takeChildren()
            
        for child in children:
            del(child)
            
    def get_tree_item_children(self, tree_item):
        count = tree_item.childCount()
        
        items = []
        
        for inc in range(0, count):
            items.append( tree_item.child(inc) )
        
        return items
    
    def set_text_edit(self, bool_value):
        self.text_edit = bool_value
        
class TreeWidgetItem(QtGui.QTreeWidgetItem):
    
    def __init__(self, parent = None):
        self.widget = self._define_widget()
        if self.widget:
            self.widget.item = self
                
        self.column = self._define_column()
        
        super(TreeWidgetItem, self).__init__(parent)
        
        
    def _define_widget(self):
        return
    
    def _define_column(self):
        return 0
        
     
class TreeItemWidget(BasicWidget):
        
    def __init__(self, parent = None):
        self.label = None
        
        super(TreeItemWidget, self).__init__(parent)
        
    def _define_main_layout(self):
        return QtGui.QHBoxLayout()
    
    def _build_widgets(self):
        self.label = QtGui.QLabel()
        
        self.main_layout.addWidget(self.label)
    
    def set_text(self, text):
        self.label.setText(text)
        
    def get_text(self):
        return self.label.text()
        
class TreeItemFileWidget(TreeItemWidget):
    pass
        
class FileTreeWidget(TreeWidget):
    
    refreshed = create_signal()
    
    def __init__(self):
        self.directory = None
        
        super(FileTreeWidget, self).__init__()
        
        self.setHeaderLabels(self._define_header())
    
    def _define_new_branch_name(self):
        return 'new_folder'  
        
    def _define_header(self):
        return ['name','size','date']

    def _define_item(self):
        return QtGui.QTreeWidgetItem()
    
    def _define_exclude_extensions(self):
        return

    def _get_files(self, directory = None):
        
        if not directory:
            directory = self.directory
            
        return util_file.get_files_and_folders(directory)
    
    def _load_files(self, files):
        self.clear()
        
        self._add_items(files)
        
    def _add_items(self, files, parent = None):
        
        for filename in files:
            if parent:
                self._add_item(filename, parent)
            if not parent:
                self._add_item(filename)

    def _add_item(self, filename, parent = None):
        
        exclude = self._define_exclude_extensions()
        
        if exclude:
            split_name = filename.split('.')
            extension = split_name[-1]
    
            if extension in exclude:
                return
        
        item = self._define_item()
        
        size = self._define_item_size()
        if size:
            size = QtCore.QSize(*size)
            
            item.setSizeHint(self.title_text_index, size)
        path_name = filename
        
        if parent:
            parent_path = self.get_item_path_string(parent)
            path_name = '%s/%s' % (parent_path, filename)
            
        
        path = util_file.join_path(self.directory, path_name)
        
        sub_files = util_file.get_files_and_folders(path)
                
        item.setText(self.title_text_index, filename)
        
        if util_file.is_file(path):
            size = util_file.get_filesize(path)
            date = util_file.get_last_modified_date(path)
            
            item.setText(self.title_text_index+1, str(size))
            item.setText(self.title_text_index+2, str(date))
        
        if sub_files:
            
            
            exclude_extensions = self._define_exclude_extensions()
            exclude_count = 0
        
            if exclude_extensions:
                for file in sub_files:
                    for exclude in exclude_extensions:
                        if file.endswith(exclude):
                            exclude_count += 1
                            break
            
            if exclude_count != len(sub_files):
                QtGui.QTreeWidgetItem(item)
            
        if not parent:
            self.addTopLevelItem(item)
        if parent:
            parent.addChild(item)
            
        return item
        
    def _add_sub_items(self, item):
        
        self._delete_children(item)
                
        path_string = self.get_item_path_string(item)
        
        path = util_file.join_path(self.directory, path_string)
        
        files = self._get_files(path)
        
        self._add_items(files, item)
        
            
    def create_branch(self, name = None):
        
        current_item = self.current_item
        
        if current_item:
            path = self.get_item_path_string(self.current_item)
            path = util_file.join_path(self.directory, path)
            
            if util_file.is_file(path):
                path = util_file.get_dirname(path)
                current_item = self.current_item.parent()
            
        if not current_item:
            path = self.directory
                
        folder = util_file.FolderEditor(path)
        
        if not name:
            name = self._define_new_branch_name()
            
        folder.create(name)
        
        if current_item:
            self._add_sub_items(current_item)
            self.setItemExpanded(current_item, True)
            
        if not current_item:
            self.refresh()
            
    def delete_branch(self):
        item = self.current_item
        path = self.get_item_directory(item)
        
        name = util_file.get_basename(path)
        directory = util_file.get_dirname(path)
        
        if util_file.is_dir(path):
            util_file.delete_dir(name, directory)
        if util_file.is_file(path):
            util_file.delete_file(name, directory)
            if path.endswith('.py'):
                util_file.delete_file((name+'c'), directory)
        
        index = self.indexOfTopLevelItem(item)
        
        parent = item.parent()
        if parent:
            parent.removeChild(item)
        if not parent:
            self.takeTopLevelItem(index)

    def refresh(self):
        files = self._get_files()
        
        if not files:
            self.clear()
            return
        
        self._load_files(files)
        self.refreshed.emit()

    def get_item_directory(self, item):
        
        path_string = self.get_item_path_string(item)
        
        return util_file.join_path(self.directory, path_string)

    def set_directory(self, directory):
        
        self.directory = directory
        self.refresh()
        
class EditFileTreeWidget(DirectoryWidget):
    
    description = 'EditTree'
    
    item_clicked = create_signal(object, object)
    
    
    def __init__(self, parent = None):        
        
        self.tree_widget = None
        
        
        
        super(EditFileTreeWidget, self).__init__(parent)
        
        self.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum) 
        
    def _define_tree_widget(self):
        return FileTreeWidget()
    
    def _define_manager_widget(self):
        return ManageTreeWidget()
    
    def _define_filter_widget(self):
        return FilterTreeWidget()
        
    def _build_widgets(self):
        
        
        self.tree_widget = self._define_tree_widget()   
        
        self.tree_widget.itemClicked.connect(self._item_selection_changed)
        
          
        self.manager_widget = self._define_manager_widget()
        self.manager_widget.set_tree_widget(self.tree_widget)
        
        self.filter_widget = self._define_filter_widget()
        
        self.filter_widget.set_tree_widget(self.tree_widget)
        self.filter_widget.set_directory(self.directory)
        
        
        self.main_layout.addWidget(self.tree_widget)
        self.main_layout.addWidget(self.filter_widget)
               
        
        self.main_layout.addWidget(self.manager_widget)
        
        
    """
    def _item_clicked(self, item, column):
        
        if not item:
            name = ''
        
        if item:
            name = item.text(column)
        
        self.item_clicked.emit(name, item)
    """
        
    def _item_selection_changed(self):
               
        items = self.tree_widget.selectedItems()
        
        name = None
        item = None
        
        if items:
            item = items[0]
            name = item.text(0)
        
            self.item_clicked.emit(name, item)
            
        return name, item

    def get_current_item(self):
        return self.tree_widget.current_item
    
    def get_current_item_name(self):
        return self.tree_widget.current_name
    
    def get_current_item_directory(self):
        item = self.get_current_item()
        return self.tree_widget.get_item_directory(item)

    def refresh(self):
        self.tree_widget.refresh()
    
    def set_directory(self, directory, sub = False):
        super(EditFileTreeWidget, self).set_directory(directory)
        
        if not sub:
            self.directory = directory
            
        self.tree_widget.set_directory(directory)
        self.filter_widget.set_directory(directory)
        
        if hasattr(self.manager_widget, 'set_directory'):
            self.manager_widget.set_directory(directory)
       
class ManageTreeWidget(BasicWidget):
        
    def __init__(self):
        
        self.tree_widget = None
        
        super(ManageTreeWidget,self).__init__()
    
    def set_tree_widget(self, tree_widget):
        self.tree_widget = tree_widget
       
class FilterTreeWidget( DirectoryWidget ):
    
    def __init__(self):
        
        self.tree_widget = None
        
        super(FilterTreeWidget, self).__init__()
    
    def _define_main_layout(self):
        return QtGui.QHBoxLayout()
    
    def _build_widgets(self): 
        self.filter_names = QtGui.QLineEdit()
        self.filter_names.setPlaceholderText('filter names')
        self.sub_path_filter = QtGui.QLineEdit()
        self.sub_path_filter.setPlaceholderText('set sub path')
        self.sub_path_filter.textChanged.connect(self._sub_path_filter_changed)
        
        self.filter_names.textChanged.connect(self._filter_names)
                
        self.main_layout.addWidget(self.filter_names)
        self.main_layout.addWidget(self.sub_path_filter)
        
    def _filter_names(self, text):
        
        self.tree_widget.filter_names(text)
        self.skip_name_filter = False
        
    def _sub_path_filter_changed(self):
        current_text = str( self.sub_path_filter.text() )
        current_text = current_text.strip()
        
        if not current_text:
            self.set_directory(self.directory)
            self.tree_widget.set_directory(self.directory)
            
            text = self.filter_names.text()
            self._filter_names(text)    
            
            return
            
        sub_dir = util_file.join_path(self.directory, current_text)
        if not sub_dir:
            
            return
        
        if util_file.is_dir(sub_dir):
            self.tree_widget.set_directory(sub_dir)
            
            text = self.filter_names.text()
            self._filter_names(text)    
                    
    def clear_sub_path_filter(self):
        self.sub_path_filter.setText('')
            
    def set_tree_widget(self, tree_widget):
        self.tree_widget = tree_widget
        
    
        
class FileManagerWidget(DirectoryWidget):
    
    def __init__(self, parent = None):
        super(FileManagerWidget, self).__init__(parent)
        
        self.data_class = self._define_data_class()
        self.save_widget.set_data_class(self.data_class)
        self.history_widget.set_data_class(self.data_class)
        
        self.history_attached = False
        
    def _define_main_layout(self):
        return QtGui.QHBoxLayout()
        
    def _define_data_class(self):
        return
    
    def _define_main_tab_name(self):
        return 'Data File'
    
    def _build_widgets(self):
        
        self.tab_widget = QtGui.QTabWidget()
        
        self.main_tab_name = self._define_main_tab_name()
        self.version_tab_name = 'Version'
                
        self.save_widget = self._define_save_widget()
        
        self.save_widget.file_changed.connect(self._file_changed)
                
        self.tab_widget.addTab(self.save_widget, self.main_tab_name)
        self._add_history_widget()
        self.tab_widget.currentChanged.connect(self._tab_changed)
                
        self.main_layout.addWidget(self.tab_widget)
        
        self.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.MinimumExpanding)

    def _add_history_widget(self):
        self.history_buffer_widget = BasicWidget()
        
        self.history_widget = self._define_history_widget()
        self.history_widget.file_changed.connect(self._file_changed)
        
        
        self.tab_widget.addTab(self.history_buffer_widget, self.version_tab_name)
        
        self.history_widget.hide()
        
    def _define_save_widget(self):
        return SaveFileWidget()
        
    def _define_history_widget(self):
        return HistoryFileWidget()
        
    def _tab_changed(self):
                                
        if self.tab_widget.currentIndex() == 0:
            
            self.history_widget.hide()
            self.history_widget.refresh()
            
            self.save_widget.set_directory(self.directory)
            
            if self.history_attached:
                self.history_buffer_widget.main_layout.removeWidget(self.history_widget)
            
            self.history_attached = False
                
        if self.tab_widget.currentIndex() == 1:
            self.update_history()
                        
    def _file_changed(self):
        
        if not util_file.is_dir(self.directory):     
            return
        
        self._activate_history_tab()
        
    def _activate_history_tab(self):
        
        if not self.directory:
            return
        
        version_tool = util_file.VersionFile(self.directory)    
        files = version_tool.get_versions()
        
        if files:
            self.tab_widget.setTabEnabled(1, True)
        if not files:
            self.tab_widget.setTabEnabled(1, False) 
        
    def update_history(self):
        self.history_buffer_widget.main_layout.addWidget(self.history_widget)
            
        self.history_widget.show()
        self.history_widget.set_directory(self.directory)
        self.history_widget.refresh()
        self.history_attached = True
        
        self._activate_history_tab()
        
    def set_directory(self, directory):
        super(FileManagerWidget, self).set_directory(directory)
        
        if self.tab_widget.currentIndex() == 0:
            self.save_widget.set_directory(directory)
        
        if self.tab_widget.currentIndex() == 1:
            self.history_widget.set_directory(directory)
        
        if self.data_class:
            self.data_class.set_directory(directory)
            
        self._file_changed()
        
        
class SaveFileWidget(DirectoryWidget):
    
    file_changed = create_signal()
    
    def __init__(self, parent = None):
        super(SaveFileWidget, self).__init__(parent)
        
        self.data_class = None
        
    def _define_main_layout(self):
        return QtGui.QHBoxLayout()
        
    def _build_widgets(self):
        
        self.save_button = QtGui.QPushButton('Save')
        load_button = QtGui.QPushButton('Open')
        
        self.save_button.clicked.connect(self._save)
        load_button.clicked.connect(self._open)
        
        self.main_layout.addWidget(load_button)
        self.main_layout.addWidget(self.save_button)
        
        
        self.main_layout.setAlignment(QtCore.Qt.AlignTop)

    def _save(self):
        
        self.file_changed.emit()
    
    def _open(self):
        pass

    def set_data_class(self, data_class_instance):
        self.data_class = data_class_instance
        
        if self.directory:
            self.data_class.set_directory(self.directory)
    
    def set_directory(self, directory):
        super(SaveFileWidget, self).set_directory(directory)
        
        if self.data_class:
            self.data_class.set_directory(self.directory)
            
    def set_no_save(self):
        self.save_button.setDisabled(True)
    
class HistoryTreeWidget(FileTreeWidget):
    

    def __init__(self):
        super(HistoryTreeWidget, self).__init__()
        
        if is_pyside():
            self.sortByColumn(0, QtCore.Qt.SortOrder.DescendingOrder)
            
        self.setColumnWidth(0, 70)  
        self.setColumnWidth(1, 150)
        self.setColumnWidth(2, 50)
        self.setColumnWidth(3, 50)
        
        self.padding = 1
    
    def _item_activated(self, item):
        return
        
    def _define_header(self):
        return ['version','comment','size','user','date']
    
    def _get_files(self):

        if self.directory:
            
            version_tool = util_file.VersionFile(self.directory)
            
            files = version_tool.get_versions()
            
            if not files:
                return
            
            if files:
                self.padding = len(str(len(files)))
                return files
    
    def _add_item(self, filename):
        
        split_name = filename.split('.')
        if len(split_name) == 1:
            return
        
        try:
            version_int = int(split_name[-1])
        except:
            return
        
        version_tool = util_file.VersionFile(self.directory)
        version_file = version_tool.get_version_path(version_int)
        comment, user = version_tool.get_version_data(version_int)
        file_size = util_file.get_filesize(version_file)
        file_date = util_file.get_last_modified_date(version_file)
        
        version_str = str(version_int).zfill(self.padding)
        
        item = QtGui.QTreeWidgetItem()
        item.setText(0, version_str)
        item.setText(1, comment)
        item.setText(2, str(file_size))
        item.setText(3, user)
        item.setText(4, file_date)
        
        self.addTopLevelItem(item)
        item.filepath = version_file

class HistoryFileWidget(DirectoryWidget):
    
    file_changed = create_signal()
    
    def _define_main_layout(self):
        return QtGui.QVBoxLayout()
    
    def _define_list(self):
        return HistoryTreeWidget()
    
    def _build_widgets(self):
        
        self.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding,
                           QtGui.QSizePolicy.MinimumExpanding)
        
        self.button_layout = QtGui.QHBoxLayout()
        
        open_button = QtGui.QPushButton('Open')
        open_button.clicked.connect(self._open_version)
        
        open_button.setMaximumWidth(100)
                
        self.button_layout.addWidget(open_button)
        
        self.version_list = self._define_list()
        
        self.main_layout.addWidget(self.version_list)
        self.main_layout.addLayout(self.button_layout)

    def _open_version(self):
        pass
            
    def refresh(self):
        self.version_list.refresh()
                
    def set_data_class(self, data_class_instance):
        self.data_class = data_class_instance
        
        if self.directory:
            self.data_class.set_directory(self.directory)
        
    def set_directory(self, directory):
        
        super(HistoryFileWidget, self).set_directory(directory)
        
        self.version_list.set_directory(directory)    

class GetString(BasicWidget):
    
    text_changed = create_signal(object)
    
    def __init__(self, name, parent = None):
        self.name = name
        super(GetString, self).__init__(parent)
    
    def _define_main_layout(self):
        return QtGui.QHBoxLayout()
            
    def _build_widgets(self):
        
        self.text_entry = QtGui.QLineEdit()
        #self.text_entry.setMaximumWidth(100)
        
        self.label = QtGui.QLabel(self.name)
        self.label.setAlignment(QtCore.Qt.AlignRight)
        self.label.setMinimumWidth(70)
        self._setup_text_widget()
        
        self.main_layout.addWidget(self.label)
        self.main_layout.addWidget(self.text_entry)
        
    def _setup_text_widget(self):
        self.text_entry.textChanged.connect(self._text_changed)
                    
    def _text_changed(self):
        self.text_changed.emit(self.text_entry.text())
        
    def set_text(self, text):
        self.text_entry.setText(text)
        
    def get_text(self):
        return self.text_entry.text()
        
    def set_label(self, label):
        self.label.setText(label)  
        
    def set_password_mode(self, bool_value):
        
        if bool_value:
            self.text_entry.setEchoMode(self.text_entry.Password)
        if not bool_value:
            self.text_entry.setEchoMode(self.text_entry.Normal) 
    
    

class GetDirectoryWidget(DirectoryWidget):
    
    directory_changed = create_signal(object)
    
    def __init__(self, parent = None):
        super(GetDirectoryWidget, self).__init__(parent)
        
        self.label = 'directory'
    
    def _define_main_layout(self):
        return QtGui.QHBoxLayout()
    
    def _build_widgets(self):
        
        self.directory_label = QtGui.QLabel('directory')
        self.directory_label.setMinimumWidth(100)
        self.directory_label.setMaximumWidth(100)
        
        self.directory_edit = QtGui.QLineEdit()
        self.directory_edit.textChanged.connect(self._text_changed)
        directory_browse = QtGui.QPushButton('browse')
        
        directory_browse.clicked.connect(self._browser)
        
        self.main_layout.addWidget(self.directory_label)
        self.main_layout.addWidget(self.directory_edit)
        self.main_layout.addWidget(directory_browse)
        
    def _browser(self):
        
        filename = get_file(self.get_directory() , self)
        
        filename = util_file.fix_slashes(filename)
        
        if filename and util_file.is_dir(filename):
            self.directory_edit.setText(filename)
            self.directory_changed.emit(filename)
        
    def _text_changed(self):
        
        directory = self.get_directory()
        
        if util_file.is_dir(directory):
            self.directory_changed.emit(directory)
        
    def set_label(self, label):
        self.directory_label.setText(label)
        
    def set_directory(self, directory):
        super(GetDirectoryWidget, self).set_directory(directory)
        
        self.directory_edit.setText(directory)
        
    def get_directory(self):
        return self.directory_edit.text()
     
class GetNumber(BasicWidget):
    
    valueChanged = create_signal(object)
    
    def __init__(self, name, parent = None):
        self.name = name
        super(GetNumber, self).__init__(parent)
    
    def _define_main_layout(self):
        return QtGui.QHBoxLayout()
    
    def _define_spin_widget(self):
        return QtGui.QDoubleSpinBox()
    
    def _build_widgets(self):
        self.spin_widget = self._define_spin_widget()
        self.spin_widget.setMaximumWidth(100)
        
        self.label = QtGui.QLabel(self.name)
        self.label.setAlignment(QtCore.Qt.AlignRight)

        self._setup_spin_widget()
        
        self.main_layout.addWidget(self.label)
        self.main_layout.addWidget(self.spin_widget)
        
    def _setup_spin_widget(self):
        
        if hasattr(self.spin_widget, 'CorrectToNearestValue'):
            self.spin_widget.setCorrectionMode(self.spin_widget.CorrectToNearestValue)
            
        if hasattr(self.spin_widget, 'setWrapping'):
            self.spin_widget.setWrapping(False)
            
        self.spin_widget.setMaximum(100000000)
        self.spin_widget.setButtonSymbols(self.spin_widget.NoButtons)
        
        self.spin_widget.valueChanged.connect(self._value_changed)
                    
    def _value_changed(self):
        self.valueChanged.emit(self.spin_widget.value())
        
    def set_value(self, value):
        self.spin_widget.setValue(value)
        
    def set_label(self, label):
        self.label.setText(label)
             
class GetNumberButton(GetNumber):
    
    clicked = create_signal(object)
    
    def _build_widgets(self):   
        super(GetNumberButton, self)._build_widgets()
        
        self.button = QtGui.QPushButton('run')
        self.button.clicked.connect(self._clicked)
        self.button.setMaximumWidth(60)
        
        self.main_layout.addWidget(self.button)
        
    def _clicked(self):
        self.clicked.emit(self.spin_widget.value())
        
class GetIntNumberButton(GetNumberButton):
    def _define_spin_widget(self):
        spin_widget = QtGui.QSpinBox()
        return spin_widget
       
class ProgressBar(QtGui.QProgressBar):
    
    def set_count(self, count):
        
        self.setMinimum(0)
        self.setMaximum(count)
        
    def set_increment(self, int_value):
        self.setValue(int_value)
        
class LoginWidget( BasicWidget ):
    
    login = create_signal(object, object)
    
    def _build_widgets(self):
        
        group_widget = QtGui.QGroupBox('Login')
        group_layout = QtGui.QVBoxLayout()
        group_widget.setLayout(group_layout)
        
        self.login_widget = GetString('User: ')
        self.password_widget = GetString('Password: ')
        self.password_widget.set_password_mode(True)
        
        self.login_state = QtGui.QLabel('Login failed.')
        self.login_state.hide()
        
        login_button = QtGui.QPushButton('Enter')

        login_button.clicked.connect( self._login )
        
        self.password_widget.text_entry.returnPressed.connect(self._login)

        group_layout.addWidget(self.login_widget)
        group_layout.addWidget(self.password_widget)
        group_layout.addWidget(login_button)
        group_layout.addWidget(self.login_state)

        self.main_layout.addWidget(group_widget)
        
        self.group_layout = group_layout

        
    def _login(self):
        
        login = self.login_widget.get_text()
                
        password = self.password_widget.get_text()
        
        self.login.emit(login, password)
        
    def set_login(self, text):
        self.login_widget.set_text(text)
        
    def set_login_failed(self, bool_value):
        if bool_value:
            self.login_state.show()
            
        if not bool_value:
            self.login_state.hide()
        
class CodeEditTabs(BasicWidget):
    
    save = create_signal(object)
    tabChanged = create_signal(object)
    no_tabs = create_signal()
    multi_save = create_signal(object, object)
    
    def __init__(self):
        super(CodeEditTabs, self).__init__()
        
        self.code_tab_map = {}
        
        self.tabs.setMovable(True)
        self.tabs.setTabsClosable(True)
        
        self.tabs.tabCloseRequested.connect(self._close_tab)
        self.tabs.currentChanged.connect(self._tab_changed)
        
        self.previous_widget = None
            
    def _tab_changed(self):
          
        current_widget = self.tabs.currentWidget()
        
        if not current_widget:
            
            if self.previous_widget:
                if self.previous_widget.find_widget:
                    self.previous_widget.find_widget.close()
            
            return
        
        
        
        if self.previous_widget:
            if self.previous_widget.find_widget:
                current_widget.find_widget = self.previous_widget.find_widget    
                self.previous_widget.set_find_widget(current_widget)
                
                
        
        self.previous_widget = current_widget.text_edit
        
        self.tabChanged.emit(current_widget)
    
    def _close_tab(self, index):
        
        title = self.tabs.tabText(index)
        
        self.tabs.removeTab(index)
                
        self.code_tab_map.pop(str(title))
        
        if self.tabs.count() == 0:
            self.no_tabs.emit()
    
    def _save(self, current_widget):
        
        current_widget.document().setModified(False)
        
        self.save.emit(current_widget)
    
    def _build_widgets(self):
        
        self.tabs = CodeTabs()
        
        
        self.main_layout.addWidget(self.tabs)
        
        self.tabs.double_click.connect(self._tab_double_click)
        

        
    def _tab_double_click(self, index):
        
        title = str(self.tabs.tabText(index))
        code_widget = self.code_tab_map[title]
        filepath = code_widget.filepath        
        
        self._close_tab(index)
        
        self.add_floating_tab(filepath)
        
    def set_group(self, group):
        self.group = group
        
    def goto_tab(self, name):
        
        if self.code_tab_map.has_key(name):
        
            widget = self.code_tab_map[name]
                
            self.tabs.setCurrentWidget(widget)
        
    def add_floating_tab(self, filepath):
        
        basename = util_file.get_basename(filepath)
        
        if self.code_tab_map.has_key(basename):
            #do something
            return
        
        code_edit_widget = CodeEdit()
        code_edit_widget.filepath = filepath
        code_edit_widget.add_menu_bar()
        code_edit_widget.set_file(filepath)
        
        code_widget = code_edit_widget.text_edit
        code_widget.titlename = basename
        code_widget.set_file(filepath)
        code_widget.save.connect(self._save)
        
        window = BasicWindow()
        basename = util_file.get_basename(filepath)
        window.setWindowTitle(basename)
        window.main_layout.addWidget(code_edit_widget)
        
        code_widget.window = window
        
        #self.code_tab_map[basename] = code_widget
        
        window.show()
        
    def add_tab(self, filepath):
        
        basename = util_file.get_basename(filepath)
        
        if self.code_tab_map.has_key(basename):
            self.goto_tab(basename)
            return
                
        code_edit_widget = CodeEdit()
        code_edit_widget.filepath = filepath
        #code_edit_widget.set_file(filepath)
        
        code_widget = code_edit_widget.text_edit
        code_widget.set_file(filepath)
        code_widget.titlename = basename
        
        
        code_widget.save.connect(self._save)
        
        
        
        self.code_tab_map[basename] = code_edit_widget
        
        self.tabs.addTab(code_edit_widget, basename)
        
        self.goto_tab(basename)
      
    def save_tabs(self, note):
        
        found = []
        
        for inc in range(0, self.tabs.count()):
            widget = self.tabs.widget(inc)
            
            if widget.text_edit.document().isModified():
                found.append(widget)
                
        self.multi_save.emit(found, note)
        
    def clear(self):
        self.tabs.clear()
        
        self.code_tab_map = {}
      
    def has_tabs(self):
        
        if self.tabs.count():
            return True
        
        return False
    
    def has_tab(self, name):
        
        if self.code_tab_map.has_key(name):
            return True
    
    def get_tab_from_filepath(self, filepath):
        
        for key in self.code_tab_map:
            
            widget = self.code_tab_map[key]
            if widget.filepath == filepath:
                return widget
                
            
    def set_tab_title(self, index, name):
        
        self.tabs.setTabText(index, name)
        
    def rename_tab(self, old_path, new_path):
        
        widget = self.get_tab_from_filepath(old_path)
        
        if widget == None:
            return
        
        index = self.tabs.indexOf(widget)
        
        if index == None:
            return
        
        old_name = util_file.get_basename(old_path)
                
        name = util_file.get_basename(new_path)
        
        self.set_tab_title(index, name)
        
        self.code_tab_map[name] = widget
        
        widget.filepath = new_path
        
class CodeTabs(QtGui.QTabWidget):
    
    double_click = create_signal(object)
    
    def __init__(self):
        super(CodeTabs, self).__init__()
        
        self.code_tab_bar = CodeTabBar()
        
        self.setTabBar( self.code_tab_bar )
        
        self.code_tab_bar.double_click.connect(self._bar_double_click)
    
    def _bar_double_click(self, index):
    
        self.double_click.emit(index)
        
class CodeTabBar(QtGui.QTabBar):
    
    double_click = create_signal(object)
    
    def __init__(self):
        super(CodeTabBar, self).__init__()
        self.setAcceptDrops(True)
    
    def mouseDoubleClickEvent(self, event):
        super(CodeTabBar, self).mouseDoubleClickEvent(event)
        
        index = self.currentIndex()
        
        self.double_click.emit(index)
        
        
class CodeEdit(BasicWidget):
    
    def __init__(self):
        super(CodeEdit, self).__init__()
        
        self.text_edit.cursorPositionChanged.connect(self._cursor_changed)
    
    def _build_widgets(self):
        
        self.text_edit = CodeTextEdit()
        
        self.status_layout = QtGui.QHBoxLayout()
        
        self.status = QtGui.QLabel('Line:')
        
        
        self.status_layout.addWidget(self.status)
        
        
        self.main_layout.addWidget(self.text_edit)
        self.main_layout.addLayout(self.status_layout)
        
    def _build_menu_bar(self):
        
        self.menu_bar = QtGui.QMenuBar()
        
        self.main_layout.insertWidget(0, self.menu_bar)
        
        file_menu = self.menu_bar.addMenu('File')
        save_action = file_menu.addAction('Save')
        
        save_action.triggered.connect(self.text_edit._save)
        
    def _cursor_changed(self):
        
        code_widget = self.text_edit
        text_cursor = code_widget.textCursor()
        #column_number = text_cursor.columnNumber()
        block_number = text_cursor.blockNumber()
        
        self.status.setText('Line: %s' % (block_number+1))
    
    def add_menu_bar(self):
        
        self._build_menu_bar()
        
    def set_file(self, filepath):
        
        self.fullpath = QtGui.QLabel('Fullpath: %s' % filepath )
        self.status_layout.addWidget(self.fullpath)
        
        
class CodeTextEdit(QtGui.QPlainTextEdit):
    
    save = create_signal(object)
    
    def __init__(self):
        
        self.filepath = None
        
        super(CodeTextEdit, self).__init__()
        
        self.setFont( QtGui.QFont('Courier', 9)  )
        
        shortcut_save = QtGui.QShortcut(QtGui.QKeySequence(self.tr("Ctrl+s")), self)
        shortcut_save.activated.connect(self._save)
        
        shortcut_find = QtGui.QShortcut(QtGui.QKeySequence(self.tr('Ctrl+f')), self)
        shortcut_find.activated.connect(self._find)
        
        shortcut_goto_line = QtGui.QShortcut(QtGui.QKeySequence(self.tr('Ctrl+l')), self)
        shortcut_goto_line.activated.connect(self._goto_line)
        
        plus_seq = QtGui.QKeySequence( QtCore.Qt.CTRL + QtCore.Qt.Key_Plus)
        equal_seq = QtGui.QKeySequence( QtCore.Qt.CTRL + QtCore.Qt.Key_Equal)
        minus_seq = QtGui.QKeySequence( QtCore.Qt.CTRL + QtCore.Qt.Key_Minus)
        
        shortcut_zoom_in = QtGui.QShortcut(plus_seq, self)
        shortcut_zoom_in.activated.connect(self._zoom_in_text)
        shortcut_zoom_in_other = QtGui.QShortcut(equal_seq, self)
        shortcut_zoom_in_other.activated.connect(self._zoom_in_text)
        shortcut_zoom_out = QtGui.QShortcut(minus_seq, self)
        shortcut_zoom_out.activated.connect(self._zoom_out_text)
        
        self._setup_highlighter()
        
        self.setWordWrapMode(QtGui.QTextOption.NoWrap)
        
        self.last_modified = None
        
        self.skip_focus = False
        
        self.line_numbers = CodeLineNumber(self)
        
        self._update_number_width(0)
        
        self.blockCountChanged.connect(self._update_number_width)
        self.updateRequest.connect(self._update_number_area)
        self.cursorPositionChanged.connect(self._line_number_highlight)
        
        self._line_number_highlight()
        
        self.find_widget = None
    
    def resizeEvent(self, event):
        
        super(CodeTextEdit, self).resizeEvent(event)
        
        rect = self.contentsRect()
        
        new_rect = QtCore.QRect( rect.left(), rect.top(), self._line_number_width(), rect.height() )
        
        self.line_numbers.setGeometry( new_rect )   
    
    def wheelEvent(self, event):
        
        delta = event.delta()
        keys =  event.modifiers()
        
        if keys == QtCore.Qt.CTRL:           
            if delta > 0:
                self._zoom_in_text()
            if delta < 0:
                self._zoom_out_text()
        
        return super(CodeTextEdit, self).wheelEvent(event)
    
    def focusInEvent(self, event):
        
        super(CodeTextEdit, self).focusInEvent(event)
        
        if not self.skip_focus:
            self._update_request()
    
    def _line_number_paint(self, event):
        
        paint = QtGui.QPainter(self.line_numbers)
        
        if not util.is_in_maya():
            paint.fillRect(event.rect(), QtCore.Qt.lightGray)
        
        if util.is_in_maya():
            paint.fillRect(event.rect(), QtCore.Qt.black)
        
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        
        top = int( self.blockBoundingGeometry(block).translated(self.contentOffset()).top() )
        bottom = int( top + self.blockBoundingRect(block).height() )
        
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = block_number + 1
                
                if util.is_in_maya():
                    paint.setPen(QtCore.Qt.lightGray)
                if not util.is_in_maya():
                    paint.setPen(QtCore.Qt.black)
                
                paint.drawText(0, top, self.line_numbers.width(), self.fontMetrics().height(), QtCore.Qt.AlignRight, str(number))
                
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            
            block_number += 1
        
    def _line_number_width(self):
        
        digits = 1
        max_value = max(1, self.blockCount())
        
        while (max_value >= 10):
            max_value /= 10
            digits+=1
        
        space = 1 + self.fontMetrics().width('1') * digits
        
        return space
    
    def _line_number_highlight(self):
        
        extra_selection = QtGui.QTextEdit.ExtraSelection()
        
        selections = [extra_selection]
        
        if not self.isReadOnly():
            selection = QtGui.QTextEdit.ExtraSelection()
            
            if util.is_in_maya():
                line_color = QtGui.QColor(QtCore.Qt.black)
            if not util.is_in_maya():
                line_color = QtGui.QColor(QtCore.Qt.lightGray)
                
            selection.format.setBackground(line_color)
            selection.format.setProperty(QtGui.QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            selections.append(selection)
            
        self.setExtraSelections(selections)
    
    def _update_number_width(self, value = 0):
        
        self.setViewportMargins(self._line_number_width(), 0,0,0)
        
    def _update_number_area(self, rect, y_value):
        
        if y_value:
            self.line_numbers.scroll(0, y_value)
        
        if not y_value:
            self.line_numbers.update(0, rect.y(), self.line_numbers.width(), rect.height())
            
        if rect.contains(self.viewport().rect()):
            self._update_number_width()
        
    def _save(self):
        
        try:
            self.save.emit(self)
        except:
            pass
        
        self.last_modified = util_file.get_last_modified_date(self.filepath)
    
    def _find(self):
        
        find_widget = FindTextWidget(self)
        find_widget.show()
        
        self.find_widget = find_widget
    
    def _goto_line(self):
        
        line = get_comment(self, 'Goto Line', '?')
        
        if not line:
            return
        
        line_number = int(line)
        
        text_cursor = self.textCursor()
        
        block_number = text_cursor.blockNumber()
        
        number = line_number - block_number
        
        if number > 0:
            move_type = text_cursor.NextBlock
            number -= 2
        if number < 0:
            move_type = text_cursor.PreviousBlock
            number = abs(number)
        
        text_cursor.movePosition(move_type, text_cursor.MoveAnchor, (number+1))
        self.setTextCursor(text_cursor)
        
    def _zoom_in_text(self):
        font = self.font()
        
        size = font.pointSize()
        size += 1
        
        font.setPointSize( size )
        self.setFont( QtGui.QFont('Courier', size) )

    def _zoom_out_text(self):
        font = self.font()
                
        size = font.pointSize()
        size -= 1
        
        if size < 0:
            return
        
        font.setPointSize( size )
        self.setFont( QtGui.QFont('Courier', size) )
        
    def _update_request(self):
                
        
        if self.filepath:
            if util_file.is_file(self.filepath):
                last_modified = util_file.get_last_modified_date(self.filepath)
                
                if last_modified != self.last_modified:
                    
                    self.skip_focus = True
                    permission = get_permission('File:\n%s\nhas changed, reload?' % util_file.get_basename(self.filepath), self)
                    
                    if permission:
                        self.set_file(self.filepath)
                        
                    if not permission:
                        self.last_modified = last_modified
                        
                    self.skip_focus = False
                
                    
                
    def _setup_highlighter(self):
        self.highlighter = Highlighter(self.document())
    
    def _remove_tab(self,string_value):
        
        string_section = string_value[0:4]
        
        if string_section == '    ':
            return string_value[4:]
        
        return string_value
        
        
    def _add_tab(self,string_value):
    
        return '    %s' % string_value
    
    def keyPressEvent(self, event):
        
        pass_on = True
    
        if event.key() == QtCore.Qt.Key_Backtab or event.key() == QtCore.Qt.Key_Tab:
            self._handle_tab(event)
            pass_on = False
    
        if pass_on:
            super(CodeTextEdit, self).keyPressEvent(event)
    
    def _handle_tab(self, event):    
        cursor = self.textCursor()
        
        start_position = cursor.anchor()
        end_position = cursor.position()
        
        if start_position > end_position:
            
            temp_position = end_position
            
            end_position = start_position
            start_position = temp_position
        
        if event.key() == QtCore.Qt.Key_Tab:
            
            if not cursor.hasSelection():
                
                self.insertPlainText('    ')
                start_position += 4
                end_position = start_position
            
            if cursor.hasSelection():
                
                cursor.setPosition(start_position)
                cursor.movePosition(QtGui.QTextCursor.StartOfLine)
                cursor.setPosition(end_position,QtGui.QTextCursor.KeepAnchor)
                
                text = cursor.selection()
                text = text.toPlainText()
                
                split_text = text.split('\n')
                
                edited = []
                
                inc = 0
                
                for text_split in split_text:
                        
                    edited.append( self._add_tab(text_split) )
                    if inc == 0:
                        start_position += 4
                        
                    end_position += 4
                    inc+=1
            
                edited_text = string.join(edited, '\n')
                cursor.insertText(edited_text)
                self.setTextCursor(cursor)
                
        if event.key() == QtCore.Qt.Key_Backtab:
            
            if not cursor.hasSelection():
                
                cursor = self.textCursor()
                
                cursor.movePosition(QtGui.QTextCursor.StartOfLine)
                cursor.movePosition(QtGui.QTextCursor.Right, QtGui.QTextCursor.KeepAnchor, 4)
                
                text = cursor.selection()
                text = text.toPlainText()
                
                if text:
                    
                    
                    if text == '    ':
                        
                        cursor.insertText('')
                        self.setTextCursor(cursor)
                        start_position -= 4
                        end_position = start_position
            
            if cursor.hasSelection():
                
                cursor.setPosition(start_position)
                cursor.movePosition(QtGui.QTextCursor.StartOfLine)
                cursor.setPosition(end_position,QtGui.QTextCursor.KeepAnchor)
                cursor.movePosition(QtGui.QTextCursor.EndOfLine, QtGui.QTextCursor.KeepAnchor)
                self.setTextCursor(cursor)
                text = cursor.selection()
                text = str(text.toPlainText())
                
                split_text = text.split('\n')
                
                edited = []
                
                inc = 0
                
                for text_split in split_text:
                    new_string_value = self._remove_tab(text_split)
                    
                    if new_string_value != text_split:
                        if inc == 0:
                            start_position -= 4
                        end_position -=4
                    
                    edited.append( new_string_value )
                    
                    inc += 1
            
                edited_text = string.join(edited, '\n')
            
                cursor.insertText(edited_text)
                self.setTextCursor(cursor)
        
        cursor = self.textCursor()
        cursor.setPosition(start_position)
        cursor.setPosition(end_position,QtGui.QTextCursor.KeepAnchor)
        self.setTextCursor(cursor)
    
    def set_file(self, filepath):
        
        in_file = QtCore.QFile(filepath)
        
        if in_file.open(QtCore.QFile.ReadOnly | QtCore.QFile.Text):
            text = in_file.readAll()
            
            text = str(text)
            
            self.setPlainText(text)
            
            
        self.filepath = filepath
        
        self.last_modified = util_file.get_last_modified_date(self.filepath)
    
    def set_find_widget(self, widget):
        
        self.find_widget.set_widget(widget)
    
    def load_modification_date(self):
        
        self.last_modified = util_file.get_last_modified_date(self.filepath)
      
class FindTextWidget(BasicDialog):
    
    def __init__(self, text_widget):
        self.found_match = False
        
        super(FindTextWidget, self).__init__(parent = text_widget)
        
        self.text_widget = text_widget
        
        self.text_widget.cursorPositionChanged.connect(self._reset_found_match)
        
    def _build_widgets(self):
        super(FindTextWidget, self)._build_widgets()
        
        self.find_string = GetString( 'Find' )
        self.replace_string = GetString( 'Replace' )
        
        h_layout = QtGui.QHBoxLayout()
        h_layout2 = QtGui.QHBoxLayout()
        
        find_button = QtGui.QPushButton('Find')
        replace_button = QtGui.QPushButton('Replace')
        replace_all_button = QtGui.QPushButton('Replace All')
        replace_find_button = QtGui.QPushButton('Replace/Find')
        
        find_button.setMaximumWidth(100)
        replace_button.setMaximumWidth(100)
        
        replace_find_button.setMaximumWidth(100)
        replace_all_button.setMaximumWidth(100)
        
        h_layout.addWidget(find_button)
        h_layout.addWidget(replace_button)
        
        h_layout2.addWidget(replace_find_button)
        h_layout2.addWidget(replace_all_button)
        
        find_button.clicked.connect(self._find)
        replace_button.clicked.connect(self._replace)
        replace_find_button.clicked.connect(self._replace_find)
        replace_all_button.clicked.connect(self._replace_all)
        
        self.main_layout.addWidget(self.find_string)
        self.main_layout.addWidget(self.replace_string)
        self.main_layout.addLayout(h_layout)
        self.main_layout.addLayout(h_layout2)
        
        self.setMaximumHeight(125)
        
    def _reset_found_match(self):
        self.found_match = False
        
    def _get_cursor_index(self):
        
        cursor = self.text_widget.textCursor()
        return cursor.position()
        
    def _move_cursor(self,start,end):
        
        cursor = self.text_widget.textCursor()
        
        cursor.setPosition(start)
        
        cursor.movePosition(QtGui.QTextCursor.Right,QtGui.QTextCursor.KeepAnchor,end - start)
        
        self.text_widget.setTextCursor(cursor)
        
        
    def _find(self):
        
        text = self.text_widget.toPlainText()
        
        find_text = str(self.find_string.get_text())
        
        pattern = re.compile( find_text, 0)

        start = self._get_cursor_index()

        match = pattern.search(text,start)

        if match:
            
            start = match.start()
            end = match.end()
            
            self._move_cursor(start,end)
            self.found_match = True
        if not match:
            self.found_match = False
        
    def _replace(self):
        
        if not self.found_match:
            return
        
        cursor = self.text_widget.textCursor()
    
        cursor.insertText( self.replace_string.get_text() )

        self.text_widget.setTextCursor(cursor)
    
    def _replace_find(self):
        
        self._replace()
        self._find()
        
    def _replace_all(self):
        
        cursor = self.text_widget.textCursor()
        
        cursor.setPosition(0)
        self.text_widget.setTextCursor(cursor)
        
        self._find()
        
        while self.found_match:
            self._replace()
            self._find()
            
    def set_widget(self, widget):
        
        self.found_match = False
        self.text_widget = widget
            

     
class Highlighter(QtGui.QSyntaxHighlighter):
    
    def __init__(self, parent=None):
        super(Highlighter, self).__init__(parent)

        keywordFormat = QtGui.QTextCharFormat()
        if not util.is_in_maya():
            keywordFormat.setForeground(QtGui.QColor(0, 150, 150))
        if util.is_in_maya():
            keywordFormat.setForeground(QtCore.Qt.green)
        
        keywordFormat.setFontWeight(QtGui.QFont.Bold)

        keywordPatterns = ["\\bdef\\b", "\\bclass\\b", "\\bimport\\b","\\breload\\b", '\\bpass\\b','\\breturn\\b']

        self.highlightingRules = [(QtCore.QRegExp(pattern), keywordFormat)
                for pattern in keywordPatterns]

        classFormat = QtGui.QTextCharFormat()
        classFormat.setFontWeight(QtGui.QFont.Bold)
        
        self.highlightingRules.append((QtCore.QRegExp("\\b\.[a-zA-Z_]+\\b(?=\()"),
                classFormat))

        numberFormat = QtGui.QTextCharFormat()
        numberFormat.setForeground(QtCore.Qt.cyan)
        self.highlightingRules.append((QtCore.QRegExp("[0-9]+"), numberFormat))
        
        quotationFormat = QtGui.QTextCharFormat()
        
        quotationFormat.setForeground(QtCore.Qt.darkGreen)
        
        if util.is_in_maya():
            quotationFormat.setForeground(QtGui.QColor(230, 230, 0))
        
        self.highlightingRules.append((QtCore.QRegExp("\'[^\']*\'"),
                quotationFormat))
        self.highlightingRules.append((QtCore.QRegExp("\"[^\"]*\""),
                quotationFormat))
        
        singleLineCommentFormat = QtGui.QTextCharFormat()
        singleLineCommentFormat.setForeground(QtCore.Qt.red)
        self.highlightingRules.append((QtCore.QRegExp("#.*"),
                singleLineCommentFormat))

        self.multiLineCommentFormat = QtGui.QTextCharFormat()
        
        self.multiLineCommentFormat.setForeground(QtCore.Qt.darkGreen)
        
        if util.is_in_maya():
            self.multiLineCommentFormat.setForeground(QtGui.QColor(230, 230, 0))
        
        self.commentStartExpression = QtCore.QRegExp('"""')
        self.commentEndExpression = QtCore.QRegExp('"""')
        
        #self.commentStartExpression2 = QtCore.QRegExp("'''")
        #self.commentEndExpression2 = QtCore.QRegExp("'''")
        
    def highlightRules(self, text):

        for pattern, format in self.highlightingRules:
            expression = QtCore.QRegExp(pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)

        self.setCurrentBlockState(0)
        
    def highlightComments(self, text):
        endIndex = -1

        startIndex = 0
        if self.previousBlockState() != 1:
            startIndex = self.commentStartExpression.indexIn(text)

        while startIndex >= 0:
            endIndex = self.commentEndExpression.indexIn(text, startIndex)
            
            if endIndex == -1 or endIndex == startIndex:
                self.setCurrentBlockState(1)
                commentLength = len(text) - startIndex
                
            else:
                commentLength = endIndex - startIndex + self.commentEndExpression.matchedLength()

            self.setFormat(startIndex, 
                           commentLength,
                           self.multiLineCommentFormat)
            
            startIndex = self.commentStartExpression.indexIn(text,
                                                             startIndex + commentLength);
        
        
    def highlightBlock(self, text):
        
        self.highlightRules(text)
        self.highlightComments(text)
        

class CodeLineNumber(QtGui.QWidget):
    
    def __init__(self, code_editor):
        super(CodeLineNumber, self).__init__()
        
        self.setParent(code_editor)
        
        self.code_editor = code_editor
    
    def sizeHint(self):
        
        return QtCore.QSize(self.code_editor._line_number_width(), 0)
    
    def paintEvent(self, event):
        
        self.code_editor._line_number_paint(event)

#--- Custom Painted Widgets

class TimelineWidget(QtGui.QWidget):

    def __init__(self):
        super(TimelineWidget, self).__init__()
        self.setSizePolicy(QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Expanding)
        self.setMaximumHeight(120)
        self.setMinimumHeight(80)
        self.values = []
        self.skip_random = False
        
    def sizeHint(self):
        return QtCore.QSize(100,80)
       
    def paintEvent(self, e):

        painter = QtGui.QPainter()
        
        painter.begin(self)
                        
        if not self.values and not self.skip_random:
            self._draw_random_lines(painter)
            
        if self.values or self.skip_random:
            self._draw_lines(painter)
            
        self._draw_frame(painter)
            
        painter.end()
        
    def _draw_frame(self, painter):
        
        pen = QtGui.QPen(QtCore.Qt.gray)
        pen.setWidth(2)
        painter.setPen(pen)
        
        height_offset = 20
        
        size = self.size()
        
        width = size.width()
        height = size.height()
        
        section = (width-21.00)/24.00
        accum = 10.00
        
        for inc in range(0, 25):
            
            value = inc
            
            if inc > 12:
                value = inc-12
                
            painter.drawLine(accum, height-(height_offset+1), accum, 30)
            
            sub_accum = accum + (section/2.0)
            
            painter.drawLine(sub_accum, height-(height_offset+1), sub_accum, height-(height_offset+11))
            
            painter.drawText(accum-15, height-(height_offset+12), 30,height-(height_offset+12), QtCore.Qt.AlignCenter, str(value))
            
            accum+=section
        
    def _draw_random_lines(self, painter):
      
        pen = QtGui.QPen(QtCore.Qt.green)
        pen.setWidth(2)
        
        height_offset = 20
        
        painter.setPen(pen)
        
        size = self.size()
        
        for i in range(500):
            x = random.randint(10, size.width()-11)               
            painter.drawLine(x,10,x,size.height()-(height_offset+2))
            
    def _draw_lines(self, painter):
        
        pen = QtGui.QPen(QtCore.Qt.green)
        pen.setWidth(3)
        
        height_offset = 20
        
        painter.setPen(pen)
        
        size = self.size()
        
        if not self.values:
            return
        
        for inc in range(0, len(self.values)):
            
            width = size.width()-21
            
            x_value = (width * self.values[inc]) / 24.00  
                        
            x_value += 10
                         
            painter.drawLine(x_value,10,x_value,size.height()-(height_offset+2))
        
    def set_values(self, value_list):
        self.skip_random = True
        self.values = value_list
        
  
def get_comment(parent = None,text_message = 'add comment', title = 'save'):
    
    comment, ok = QtGui.QInputDialog.getText(parent, title,text_message)
    
    comment = comment.replace('\\', '_')  
    
    if ok:
        return comment
    
def get_file(directory, parent = None):
    fileDialog = QtGui.QFileDialog(parent)
    
    if directory:
        fileDialog.setDirectory(directory)
    
    directory = fileDialog.getExistingDirectory()
    
    return directory

def get_permission(message, parent = None):
    
    message_box = QtGui.QMessageBox(parent)
    
    message = message_box.question(parent, 'Permission', message, message_box.Yes | message_box.No )
    
    if message == message_box.Yes:
        return True
    
    if message == message_box.No:
        return False
    
def get_new_name(message, parent = None, old_name = None):
    
    
    if not old_name:
        comment, ok = QtGui.QInputDialog.getText(parent, 'Rename', message)
    if old_name:
        comment, ok = QtGui.QInputDialog.getText(parent, 'Rename', message, text = old_name)
    
    
    comment = comment.replace('\\', '_')  
    
    if ok:
        return comment
    
def critical(message, parent = None):
    
    message_box = QtGui.QMessageBox(parent)
    
    message_box.critical(parent, 'Critical Error', message)
    
def warning(message, parent = None):
    
    message_box = QtGui.QMessageBox(parent)
    message_box.warning(parent, 'Warning', message)

def about(message, parent = None):
    
    message_box = QtGui.QMessageBox(parent)
    message_box.about(parent, 'About', message)

def get_pick(list, text_message, parent = None):
    
    input_dialog = QtGui.QInputDialog(parent)
    input_dialog.setComboBoxItems(list)
    picked, ok = QtGui.QInputDialog.getItem(parent, 'Pick One', text_message, list)
    
    if ok:
        return picked
    
