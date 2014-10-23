# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

import vtool.qt_ui
import vtool.util_file
import vtool.data
import process

if vtool.qt_ui.is_pyqt():
    from PyQt4 import QtGui, QtCore, Qt, uic
if vtool.qt_ui.is_pyside():
    from PySide import QtCore, QtGui

class DataProcessWidget(vtool.qt_ui.DirectoryWidget):
    
    data_created = vtool.qt_ui.create_signal(object)
    
    def __init__(self):
        
        self.data_widget = None
        
        super(DataProcessWidget, self).__init__()
          
    def _define_main_layout(self):
        return QtGui.QVBoxLayout()
                
    def _build_widgets(self):
        
        splitter = QtGui.QSplitter()
        
        self.data_widget = DataTreeWidget()
        self.data_widget.itemSelectionChanged.connect(self._data_item_selection_changed)
        self.data_widget.active_folder_changed.connect(self._update_file_widget)
        
        self.datatype_widget = DataTypeWidget()
        self.datatype_widget.data_added.connect(self._refresh_data)
        
        splitter.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)   
        self.main_layout.addWidget(splitter, stretch = 1)
                
        splitter.addWidget(self.data_widget)
        splitter.addWidget(self.datatype_widget)
        
        splitter.setSizes([400, 200])
        
        self.label = QtGui.QLabel('-')
        
        self.file_widget = QtGui.QWidget()
        self.file_widget.hide()
        
        self.main_layout.addWidget(self.label, alignment = QtCore.Qt.AlignCenter)
        self.main_layout.addWidget(self.file_widget)
        
    def _refresh_data(self, data_name):
        self.data_widget._load_data()
        
        self.data_created.emit(data_name)
        
    def _data_item_selection_changed(self):
        
        item = self.data_widget.currentItem()
        items = self.data_widget.selectedItems()
        
        if items:
            item = items[0]
            
        if item:
            
            process_tool = process.Process()
            process_tool.set_directory(self.directory)
            is_data = process_tool.is_data_folder(item.text(0))
            
            if is_data:
                
                data_type = process_tool.get_data_type(item.text(0))
                
                for key in file_widgets:
                    
                    if key == data_type:
                        
                        if self.file_widget:
                            self.file_widget.deleteLater()
                        
                        self.file_widget = file_widgets[key]()
                        
                        path_to_data = vtool.util_file.join_path(process_tool.get_data_path(), str( item.text(0) ) )
                           
                        self.file_widget.set_directory(path_to_data)
                        self.main_layout.addWidget(self.file_widget)
                        self.label.setText( str( item.text(0)) )
            if not is_data:
                item = None
            
        if not item:
            if not self.file_widget:
                return
                                    
            if self.file_widget:
                self.file_widget.deleteLater()
                self.file_widget = None
                
    def _update_file_widget(self, directory):
        
        if not directory:
            return
        
        self.file_widget.set_directory(directory)
                
    def set_directory(self, directory):
        super(DataProcessWidget, self).set_directory(directory)

        self.data_widget.set_directory(directory)
        
        self.data_widget.refresh()
        
        self.datatype_widget.set_directory( directory )
        
class DataTreeWidget(vtool.qt_ui.FileTreeWidget):
    
    active_folder_changed = vtool.qt_ui.create_signal(object)
    
    def __init__(self):     
        super(DataTreeWidget, self).__init__()
        
        self.directory = None
        
        self.setColumnWidth(0, 150)
        self.setColumnWidth(1, 150)
        
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._item_menu)
        
        self._create_context_menu()
        
    def _item_menu(self, position):
        
        item = self.itemAt(position)
            
        if item:
            self.remove_action.setVisible(True)
        if not item:
            self.remove_action.setVisible(False)
        self.context_menu.exec_(self.viewport().mapToGlobal(position))
        
    def _create_context_menu(self):
        
        self.context_menu = QtGui.QMenu()
        
        self.browse_action = self.context_menu.addAction('Browse')
        self.refresh_action = self.context_menu.addAction('Refresh')
        self.context_menu.addSeparator()
        self.remove_action = self.context_menu.addAction('Delete')

        self.browse_action.triggered.connect(self._browse_current_item)
        self.remove_action.triggered.connect(self._remove_current_item)
        self.refresh_action.triggered.connect(self.refresh)    
    
    def _browse_current_item(self):
        
        items = self.selectedItems()
        
        if not items:
            vtool.util_file.open_browser(self.directory)
            return
        
        
        
        item = items[0]
        
        directory = self.get_item_directory(item)
        
        vtool.util_file.open_browser(directory)
    
    def _remove_current_item(self):
        
        items = self.selectedItems()
        
        if not items:
            return
        
        name = items[0].text(0)
        
        delete_permission = vtool.qt_ui.get_permission('Delete %s' % name, self)
        
        if not delete_permission:
            return
        
        process_tool = process.Process()
        process_tool.set_directory(self.directory)
        process_tool.delete_data(name)
        
        index = self.indexOfTopLevelItem(items[0])
        
        self.takeTopLevelItem(index)
        
    
    def _define_header(self):
        return ['name','type','size','date']
    
    def _edit_finish(self, item):
        super(DataTreeWidget, self)._edit_finish(item)
        
        if type(item) == int:
            return
        
        name = item.text(0)
        
        old_name = item.folder
        
        process_tool = process.Process()
        process_tool.set_directory(self.directory)
        new_path = process_tool.rename_data(old_name, name)
        
        self.active_folder_changed.emit(new_path)
        
    def _load_data(self, preserve_selected = True):

        self.clear()

        process_tool = process.Process()
        process_tool.set_directory(self.directory)
        
        folders = process_tool.get_data_folders()
        
        if not folders:
            return
        
        for foldername in folders:
            
            item = QtGui.QTreeWidgetItem()
            item.setText(0, foldername)
            
            data_type = process_tool.get_data_type(foldername)
            
            item.setText(1, data_type)
            
            item.folder = foldername
            item.setSizeHint(0, QtCore.QSize(100,30))
            self.addTopLevelItem(item)
            
        self.itemSelectionChanged.emit()
    
    def get_item_path_string(self, item):
        
        parents = self.get_tree_item_path(item)
        parent_names = self.get_tree_item_names(parents)
        
        names = []
        
        if not parent_names:
            return
        
        for name in parent_names:
            names.append(name[0])
        
        names.insert(1, '_data')
        
        names.reverse()
        import string
        path = string.join(names, '/')
        
        return path
                
    def refresh(self):
        self._load_data()
        
class DataTreeItem(vtool.qt_ui.TreeWidgetItem):
    pass

class DataItemWidget(vtool.qt_ui.TreeItemWidget):
    def __init__(self):
        super(DataItemWidget, self).__init__()
        
class DataTypeWidget(QtGui.QWidget):
    
    data_added = vtool.qt_ui.create_signal(object)
        
    def __init__(self):
        super(DataTypeWidget, self).__init__()
        
        self.main_layout = QtGui.QVBoxLayout()
        self.setLayout(self.main_layout)
        
        self.data_manager = vtool.data.DataManager()
        self.main_layout.setContentsMargins(2,2,2,2)
        self.main_layout.setSpacing(3)
        self._add_widgets()
        
        self.directory = None
                
    def _add_widgets(self):
        self.data_type_tree_widget = DataTypeTreeWidget()
        
        add_button = QtGui.QPushButton('Add')
        add_button.clicked.connect(self._add )
        
        self.main_layout.addWidget(self.data_type_tree_widget)
        self.main_layout.addWidget(add_button)
        
        self._load_data_types()
        
    def _load_data_types(self):
        
        data_types = self.data_manager.get_available_types()
        
        for data_type in data_types:
            
            self.data_type_tree_widget.add_data_type(data_type)
            
    def _add(self):
                
        data_type = self.data_type_tree_widget.get_data_type()
        data_group = self.data_type_tree_widget.get_data_group()
        
        if not data_type or not data_group:
            return
        
        data_type = data_group + '.' + data_type
        manager = vtool.data.DataManager()
        data_instance = manager.get_type_instance(data_type)
        data_name = data_instance._data_name()
        
        process_tool = process.Process()
        process_tool.set_directory(self.directory)
        process_tool.create_data(data_name, data_type)
        
        self.data_added.emit(data_name)
        
    def set_directory(self, filepath):
        self.directory = filepath
    
class DataTypeTreeWidget(QtGui.QTreeWidget):
    
    def __init__(self):
        
        super(DataTypeTreeWidget, self).__init__()
        self.setHeaderLabels(['data type'])
        
    def _find_group(self, groupname):
        for inc in range(0, self.topLevelItemCount() ):
                
            item = self.topLevelItem(inc)
            
            text = str( item.text(0) )
                
            if text == groupname:
                return item       

    def _add_data_item(self, data_type, parent):
        
        item = QtGui.QTreeWidgetItem(parent)
        item.setText(0, data_type)
        
        self.addTopLevelItem(item)
        
    def add_data_type(self, data_type):
        
        split_type = data_type.split('.')
        
        if split_type[0].startswith('script'):
            return
        
        group_item = self._find_group(split_type[0])
        
        if not group_item:
            item = QtGui.QTreeWidgetItem()
            item.setText(0, split_type[0])
            self.addTopLevelItem(item)
            group_item = item
        
        self._add_data_item(split_type[1], group_item)
    
    def get_data_type(self):
        
        item = self.currentItem()
        return item.text(0)
    
    def get_data_group(self):
        item = self.currentItem()
        parent = item.parent()
        if parent:
            return parent.text(0)

#--- data widgets

class DataFileWidget(vtool.qt_ui.FileManagerWidget):
    def set_directory(self, directory):
        super(DataFileWidget, self).set_directory(directory)
        
        parent_path = vtool.util_file.get_parent_path(directory)
        name = vtool.util_file.get_basename(directory)
        
        data_folder = vtool.data.DataFolder(name, parent_path)
        
        instance = data_folder.get_folder_data_instance()
        
        self.save_widget.set_directory(directory)
        self.save_widget.set_data_class(instance)
        
        self.history_widget.set_directory(directory)
        self.history_widget.set_data_class(instance)

class MayaDataFileWidget(DataFileWidget):

    def _define_main_tab_name(self):
        return 'data file'
    
    def _define_save_widget(self):
        return MayaDataSaveFileWidget()
        
    def _define_history_widget(self):
        return MayaDataHistoryFileWidget()
    
class MayaDataSaveFileWidget(vtool.qt_ui.SaveFileWidget):
    
    def _build_widgets(self):
            
        import_button = QtGui.QPushButton('Import')
        import_button.clicked.connect(self._import_data)
        
        export_button = QtGui.QPushButton('Export')
        export_button.clicked.connect(self._export_data)
        
        self.main_layout.addWidget(export_button) 
        self.main_layout.addWidget(import_button) 
        
    def _export_data(self):
        comment = vtool.qt_ui.get_comment(self)
        if comment == None:
            return
        self.data_class.export_data(comment)
        
    def _import_data(self):
        self.data_class.import_data()
        
class MayaDataHistoryFileWidget(vtool.qt_ui.HistoryFileWidget):
    
    def _open_version(self):
        item = self.version_list.currentItem()
        
        version = int(item.text(0))
        
        version_tool = vtool.util_file.VersionFile(self.directory)
        version_file = version_tool.get_version_path(version)
            
        self.data_class.import_data(version_file)

class ScriptFileWidget(DataFileWidget):
    def __init__(self, parent = None):
        super(ScriptFileWidget, self).__init__(parent)
        self.text_widget = None
    
    def _define_data_class(self):
        return vtool.data.ScriptData()
            
    def _define_main_tab_name(self):
        return 'Script'

    def _define_save_widget(self):
        return ScriptSaveFileWidget()

    def _define_history_widget(self):
        return ScriptHistoryFileWidget()
        
    def set_text_widget(self, widget):
        self.text_widget = widget
        
        self.save_widget.set_text_widget(widget)
        self.history_widget.set_text_widget(widget)   

class ScriptSaveFileWidget(vtool.qt_ui.SaveFileWidget):
    def __init__(self, parent = None):
        super(ScriptSaveFileWidget, self).__init__(parent)
        
        self.text_widget = None
    
    def _build_widgets(self):
            
        save_button = QtGui.QPushButton('Save')
        save_button.clicked.connect(self._save)
        save_button.setMaximumWidth(100)
        
        self.main_layout.addWidget(save_button)    

    def _save(self, comment = None):
        
        print 'save!', comment, self.text_widget.titlename
        
        
        if comment == None or comment == False:
            comment = vtool.qt_ui.get_comment(self, title = 'Save %s' % self.data_class.name)
        
        if comment == None:
            return
        
        text = self.text_widget.toPlainText()
        lines= vtool.util_file.get_text_lines(text)
        
        self.data_class.save(lines,comment)
        
        self.file_changed.emit()

    def set_text_widget(self, text_widget):
        self.text_widget = text_widget

class ScriptHistoryFileWidget(vtool.qt_ui.HistoryFileWidget):
    
    def _open_version(self):
        
        item = self.version_list.currentItem()
        
        if not item:
            return
        
        version = int(item.text(0))
        
        
        version_tool = vtool.util_file.VersionFile(self.directory)
        version_file = version_tool.get_version_path(version)
        
        in_file = QtCore.QFile(version_file)
        
        if in_file.open(QtCore.QFile.ReadOnly | QtCore.QFile.Text):
            text = in_file.readAll()
            
            text = str(text)
            
            self.text_widget.setPlainText(text)
            
    def set_text_widget(self, text_widget):
        self.text_widget = text_widget
    
class ControlCvFileWidget(MayaDataFileWidget):
    def _define_data_class(self):
        return vtool.data.ControlCvData()
    
    def _define_main_tab_name(self):
        return 'Control Cvs'
        
class SkinWeightFileWidget(MayaDataFileWidget):
    def _define_data_class(self):
        return vtool.data.SkinWeightData()
    
    def _define_main_tab_name(self):
        return 'Skin Weights' 
      
class AnimationFileWidget(MayaDataFileWidget):
    
    def _define_data_class(self):
        return vtool.data.AnimationData()
    
    def _define_main_tab_name(self):
        return 'Animation Keyframes'
        
class AtomFileWidget(MayaDataFileWidget):
    
    def _define_data_class(self):
        return vtool.data.AtomData()
    
    def _define_main_tab_name(self):
        return 'ATOM file'
        
class PoseFileWidget(MayaDataFileWidget):
    def _define_data_class(self):
        return vtool.data.PoseData()
    
    def _define_main_tab_name(self):
        return 'Pose Targets'
        
class MayaShadersFileWidget(MayaDataFileWidget):
    
    def _define_data_class(self):
        return vtool.data.MayaShadersData()

    def _define_main_tab_name(self):
        return 'Maya Shaders'
    
class MayaAttributesFileWidget(MayaDataFileWidget):
    def _define_data_class(self):
        return vtool.data.MayaAttributeData()

    def _define_main_tab_name(self):
        return 'Maya Attributes'
        

class MayaFileWidget(vtool.qt_ui.FileManagerWidget):
    
    def _define_main_tab_name(self):
        return 'Maya File'
    
    def _define_save_widget(self):
        return MayaSaveFileWidget()
    
    def _define_history_widget(self):
        return MayaHistoryFileWidget()
    
class MayaAsciiFileWidget(MayaFileWidget):
    
    def _define_main_tab_name(self):
        return 'Maya Ascii File'
    
    def _define_data_class(self):
        return vtool.data.MayaAsciiFileData()

class MayaBinaryFileWidget(MayaFileWidget):
    def _define_main_tab_name(self):
        return 'Maya Binary File'

    def _define_data_class(self):
        return vtool.data.MayaBinaryFileData()
        
class MayaSaveFileWidget(vtool.qt_ui.SaveFileWidget):
    
    
    def _build_widgets(self):
        save_button = QtGui.QPushButton('Save')
        export_button = QtGui.QPushButton('Export')
        open_button = QtGui.QPushButton('Open')
        import_button = QtGui.QPushButton('Import')
        
        save_button.clicked.connect( self._save_file )
        export_button.clicked.connect( self._export_file )
        open_button.clicked.connect( self._open_file )
        import_button.clicked.connect( self._import_file )
        
        self.main_layout.addWidget(save_button)
        self.main_layout.addWidget(export_button)
        self.main_layout.addWidget(open_button)
        self.main_layout.addWidget(import_button)
        
        
        self.main_layout.setAlignment(QtCore.Qt.AlignTop)
        
    
    def _save_file(self):
        comment = vtool.qt_ui.get_comment(self)
        
        if comment == None:
            return
        
        self.data_class.save(comment)
        
    def _export_file(self):
        comment = vtool.qt_ui.get_comment(self)
        
        if comment == None:
            return
        
        self.data_class.export_data(comment)
        
    def _open_file(self):
        self.data_class.open()
        
    def _import_file(self):
        self.data_class.import_data()
        
        
class MayaHistoryFileWidget(vtool.qt_ui.HistoryFileWidget):
    def _build_widgets(self):
        super(MayaHistoryFileWidget, self)._build_widgets()
        import_button = QtGui.QPushButton('Import')
        self.button_layout.addWidget(import_button)
        
        import_button.clicked.connect(self._import_version)
        
    def _open_version(self):
        
        item = self.version_list.currentItem()
        
        version = int(item.text(0))
        
        version_tool = vtool.util_file.VersionFile(self.directory)
        version_file = version_tool.get_version_path(version)
        
        maya_file = vtool.data.MayaFileData()
        maya_file.open(version_file)
        
    def _import_version(self):
        item = self.version_list.currentItem()
        
        version = int(item.text(0))
        
        version_tool = vtool.util_file.VersionFile(self.directory)
        version_file = version_tool.get_version_path(version)
        
        maya_file = vtool.data.MayaFileData()
        maya_file.import_data(version_file)  


        
file_widgets = { 'maya.binary' : MayaBinaryFileWidget,
                 'maya.ascii' : MayaAsciiFileWidget,
                 'maya.control_cvs' : ControlCvFileWidget,
                 'maya.skin_weights' : SkinWeightFileWidget,
                 'maya.atom' :  AtomFileWidget,
                 'maya.shaders' : MayaShadersFileWidget,
                 'maya.attributes' : MayaAttributesFileWidget,
                 'maya.pose' : PoseFileWidget,
                 'maya.animation': AnimationFileWidget,}