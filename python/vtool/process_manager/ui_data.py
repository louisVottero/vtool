# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

import string

import vtool.qt_ui
import vtool.util_file
import vtool.data
import vtool.util
import process

if vtool.qt_ui.is_pyqt():
    from PyQt4 import QtGui, QtCore, Qt, uic
if vtool.qt_ui.is_pyside():
    from PySide import QtCore, QtGui


class DataProcessWidget(vtool.qt_ui.DirectoryWidget):
    
    data_created = vtool.qt_ui.create_signal(object)
    
    def __init__(self):
        
        self.data_widget = None
        self.last_directory = None
        
        super(DataProcessWidget, self).__init__()
        
        self.setMouseTracking(True)
        self.data_widget.setMouseTracking(True)
          
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
        
        splitter.setSizes([1,1])
        self.splitter = splitter
        
        self.label = QtGui.QLabel('-')
        
        self.file_widget = QtGui.QWidget()
        self.file_widget.hide()
        
        self.main_layout.addWidget(self.label, alignment = QtCore.Qt.AlignCenter)
        self.main_layout.addWidget(self.file_widget)
        
    def mouse_move(self, event):
        
        cursor = self.cursor()
        point = cursor.pos()
        width = self.width()
        
        x_value = point.x()
        
        if x_value >= width * .8:
            self.splitter.setSizes([1,1])
        if x_value < width * .8:
            self.splitter.setSizes([1,1])
        
    def _refresh_data(self, data_name):
        self.data_widget._load_data(new_data = data_name)
        
        self.data_created.emit(data_name)
        
    def _data_item_selection_changed(self):
        
        items = self.data_widget.selectedItems()
        
        item = None
        
        if items:
            item = items[0]
            
        if item:
            
            process_tool = process.Process()
            process_tool.set_directory(self.directory)
            is_data = process_tool.is_data_folder(item.text(0))
            
            if is_data:
                
                data_type = process_tool.get_data_type(item.text(0))
                
                keys = file_widgets.keys()
                
                for key in keys:
                    
                    if key == data_type:
                        
                        if self.file_widget:
                            self.file_widget.close()
                            self.file_widget.deleteLater()
                            del self.file_widget
                            self.file_widget = None
                            
                        
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
                self.file_widget.hide()
                self.file_widget.deleteLater()
                self.file_widget = None
                
    def _update_file_widget(self, directory):
        
        if not directory:
            return
        
        self.file_widget.set_directory(directory)
        
        basename = vtool.util_file.get_basename(directory)
        
        self.label.setText(basename)
                
    def set_directory(self, directory):
        super(DataProcessWidget, self).set_directory(directory)

        if directory == self.last_directory:
            return

        self.data_widget.set_directory(directory)
        
        self.datatype_widget.set_directory( directory )
        
        self.last_directory = directory
        
class DataTreeWidget(vtool.qt_ui.FileTreeWidget):
    
    active_folder_changed = vtool.qt_ui.create_signal(object)
    
    def __init__(self):     
        super(DataTreeWidget, self).__init__()
        
        self.text_edit = False
        
        self.directory = None
        
        policy = self.sizePolicy()
        
        policy.setHorizontalPolicy(policy.Maximum)
        policy.setHorizontalStretch(1)
        
        self.setSizePolicy(policy)
        
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
        
        self.rename_action = self.context_menu.addAction('Rename')
        self.remove_action = self.context_menu.addAction('Delete')
        self.context_menu.addSeparator()
        self.browse_action = self.context_menu.addAction('Browse')
        self.refresh_action = self.context_menu.addAction('Refresh')
        
        self.rename_action.triggered.connect(self._rename_data)
        self.browse_action.triggered.connect(self._browse_current_item)
        self.remove_action.triggered.connect(self._remove_current_item)
        self.refresh_action.triggered.connect(self.refresh)    
    
    def mouseDoubleClickEvent(self, event):
        self._browse_current_item()
        
    def _rename_data(self):
        items = self.selectedItems()
        
        if not items:
            return
        
        item = items[0]
        
        old_name = item.text(0)
        
        old_name = old_name.split('/')[-1]
        
        new_name = vtool.qt_ui.get_new_name('New Name', self, old_name)
        
        for inc in range(0, self.topLevelItemCount()):
            top_item = self.topLevelItem(inc)
            if new_name == top_item.text(0):
                return
        
        if not new_name:
            return
                
        item.setText(0, new_name)
        
        was_renamed = self._item_renamed(item, old_name)
        
        if not was_renamed:
            item.setText(0, old_name)
    
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
        return ['Name','Type']
        
    def _item_renamed(self, item, old_name):
        
        if type(item) == int:
            return
        
        name = item.text(0)
        
        process_tool = process.Process()
        process_tool.set_directory(self.directory)
        new_path = process_tool.rename_data(old_name, name)
        
        if not new_path:
            return False
        
        self.active_folder_changed.emit(new_path)
        
        return True
        
    def _load_data(self, preserve_selected = True, new_data = None):

        self.clear()

        process_tool = process.Process()
        process_tool.set_directory(self.directory)
        
        folders = process_tool.get_data_folders()
        
        if not folders:
            return
        
        select_item = None
        
        for foldername in folders:
            
            item = QtGui.QTreeWidgetItem()
            item.setText(0, foldername)
            
            data_type = process_tool.get_data_type(foldername)
            
            item.setText(1, data_type)
            
            item.folder = foldername
            item.setSizeHint(0, QtCore.QSize(100,25))
            self.addTopLevelItem(item)
            
            if foldername == new_data:
                select_item = item
        
        if select_item:
            self.setItemSelected(select_item, True)
            self.setCurrentItem(select_item)
        
    def get_item_path_string(self, item):
        
        parents = self.get_tree_item_path(item)
        parent_names = self.get_tree_item_names(parents)
        
        names = []
        
        if not parent_names:
            return
        
        for name in parent_names:
            names.append(name[0])
        
        names.insert(1, '.data')
        
        names.reverse()
        
        path = string.join(names, '/')
        
        return path
                
    def refresh(self):
        self._load_data()
        
class DataTreeItem(vtool.qt_ui.TreeWidgetItem):
    pass

class DataItemWidget(vtool.qt_ui.TreeItemWidget):
    def __init__(self):
        super(DataItemWidget, self).__init__()
        
class DataTypeWidget(vtool.qt_ui.BasicWidget):
    
    data_added = vtool.qt_ui.create_signal(object)
        
    def __init__(self):
        
        self.data_manager = vtool.data.DataManager()
        self.directory = None
        
        super(DataTypeWidget, self).__init__()
        
        self.main_layout.setSpacing(3)
        
        policy = self.sizePolicy()
        
        policy.setHorizontalPolicy(policy.MinimumExpanding)
        policy.setHorizontalStretch(0)
        
        self.setSizePolicy(policy)
        self.setMinimumWidth(140)
        self.setMaximumWidth(140)
        
    def sizeHint(self):
        
        return QtCore.QSize(0,20)
                
    def _build_widgets(self):
        self.data_type_tree_widget = DataTypeTreeWidget()
        
        add_button = QtGui.QPushButton('Add')
        add_button.setMaximumWidth(100)
        add_button.clicked.connect(self._add )
        
        add_button.setDisabled(True)
        self.add_button = add_button
        
        self.main_layout.addWidget(self.data_type_tree_widget)
        self.main_layout.addWidget(add_button)
        
        self._load_data_types()
        
        self.data_type_tree_widget.itemSelectionChanged.connect(self._enable_add)
        
        self.data_type_tree_widget.doubleClicked.connect(self._add)
        
    def _enable_add(self):
        
        items = self.data_type_tree_widget.selectedItems()
        
        if items:
            
            if items[0].text(0) == 'Maya':
                self.add_button.setDisabled(True)
                return
            
            self.add_button.setEnabled(True)
        
        if not items:
            self.add_button.setDisabled(True)
        
    def _load_data_types(self):
        
        data_types = self.data_manager.get_available_types()
        
        for data_type in data_types:
            
            self.data_type_tree_widget.add_data_type(data_type)
            
        count = self.data_type_tree_widget.topLevelItemCount()
        
        for inc in range(0, count):
            
            item = self.data_type_tree_widget.topLevelItem(inc)
            
            if str(item.text(0)) == 'Maya' and vtool.util.is_in_maya():
                item.setExpanded(True)
            
    def _add(self):
                
        data_type = self.data_type_tree_widget.get_data_type()
        data_group = self.data_type_tree_widget.get_data_group()
        
        data_group = data_group.lower()
        
        if not data_type or not data_group:
            return
        
        data_type = data_group + '.' + data_type
        manager = vtool.data.DataManager()
        data_instance = manager.get_type_instance(data_type)
        data_name = data_instance._data_name()
        
        process_tool = process.Process()
        process_tool.set_directory(self.directory)
        data_path = process_tool.create_data(data_name, data_type)
        
        data_name = vtool.util_file.get_basename(data_path)
        
        self.data_added.emit(data_name)
        
    def set_directory(self, filepath):
        self.directory = filepath
    
class DataTypeTreeWidget(QtGui.QTreeWidget):
    
    def __init__(self):
        
        super(DataTypeTreeWidget, self).__init__()
        self.setHeaderHidden(True)
        self.setHeaderLabels(['Data Type'])
        self.setIndentation(10)
        
    def _find_group(self, groupname):
        for inc in range(0, self.topLevelItemCount() ):
                
            item = self.topLevelItem(inc)
            
            text = str( item.text(0) )
                
            if text == groupname:
                return item       

    def _add_data_item(self, data_type, parent):
        
        
        
        item = QtGui.QTreeWidgetItem(parent)
        item.setText(0, data_type)
        item.setSizeHint(0, QtCore.QSize(100, 20))
        #self.addTopLevelItem(item)
        
        return item
        
    def add_data_type(self, data_type):
        
        split_type = data_type.split('.')
        
        group_type = split_type[0].capitalize()
        
        
        if split_type[0].startswith('script'):
            return
        
        group_item = self._find_group(group_type)
        
        if not group_item:
            item = QtGui.QTreeWidgetItem()
            item.setText(0, group_type)
            item.setSizeHint(0, QtCore.QSize(100, 25))
            self.addTopLevelItem(item)    
            group_item = item
        
        new_item = self._add_data_item(split_type[1], group_item)
        
        return new_item
        
    
    def get_data_type(self):
        
        item = self.currentItem()
        return item.text(0)
    
    def get_data_group(self):
        item = self.currentItem()
        parent = item.parent()
        if parent:
            return str(parent.text(0))

#--- data widgets

class DataFileWidget(vtool.qt_ui.FileManagerWidget):
    
    def set_directory(self, directory):
        
        super(DataFileWidget, self).set_directory(directory)
        
        parent_path = vtool.util_file.get_dirname(directory)
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
    
    def _create_button(self, name):
        
        button = QtGui.QPushButton(name)
        button.setMaximumWidth(120)
        
        return button
    
    def _build_widgets(self):
            
        import_button = self._create_button('Import')
        import_button.clicked.connect(self._import_data)
        
        export_button = self._create_button('Export')
        export_button.clicked.connect(self._export_data)
        
        self.main_layout.addWidget(export_button) 
        self.main_layout.addWidget(import_button) 
        
    def _export_data(self):
        
        comment = vtool.qt_ui.get_comment(self)
        if comment == None:
            return
        
        self.data_class.export_data(comment)
        self.file_changed.emit()
        
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
        
        if comment == None or comment == False:
            comment = vtool.qt_ui.get_comment(self, title = 'Save %s' % self.data_class.name)
        
        if comment == None:
            return
        
        text = self.text_widget.toPlainText()
        lines= vtool.util_file.get_text_lines(text)
        
        self.data_class.save(lines,comment)
        
        self.file_changed.emit()
        
        self.text_widget.load_modification_date()
        self.text_widget.save_done.emit(True)
        self.text_widget.document().setModified(False)

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
    
    def _define_option_widget(self):
        return ControlCvOptionFileWidget()
    
    def _define_main_tab_name(self):
        return 'Control Cvs'

class ControlCvOptionFileWidget(vtool.qt_ui.OptionFileWidget):
    
    def _define_remove_button(self):
        return 'Delete Curve Cv Data'
    
    def _build_widgets(self):
        super(ControlCvOptionFileWidget, self)._build_widgets()
        
        data_options_layout = QtGui.QVBoxLayout()
                
        list_widget = QtGui.QListWidget()
        list_widget.setSizePolicy(QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Minimum)
        list_widget.setMaximumHeight(100)
        list_widget.setSelectionMode(list_widget.ExtendedSelection)
        list_widget.setSortingEnabled(True)
        self.list_widget = list_widget
        
        self.filter_names = QtGui.QLineEdit()
        self.filter_names.setPlaceholderText('Filter Names')
        self.filter_names.textChanged.connect(self._filter_names)
        
        remove_button = QtGui.QPushButton(self._define_remove_button())
        remove_button.clicked.connect(self._remove_curves)
                
        self.curve_list = list_widget
        
        data_options_layout.addWidget(list_widget)
        data_options_layout.addWidget(self.filter_names)
        data_options_layout.addWidget(remove_button)
    
        self.main_layout.addSpacing(20)
        self.main_layout.addLayout(data_options_layout)
   
    def _unhide_names(self):
        for inc in range(0, self.list_widget.count()):
            item = self.list_widget.item(inc)
            item.setHidden(False)
            
    def _filter_names(self):
        self._unhide_names()
                        
        for inc in range( 0, self.list_widget.count() ):
                
            item = self.list_widget.item(inc)
            text = str( item.text() )
            
            filter_text = self.filter_names.text()
            
            if text.find(filter_text) == -1:
                item.setHidden(True)
                
   
    def _remove_curves(self):
        
        items = self.curve_list.selectedItems()
        
        if not items:
            return
        
        for item in items:
            curve = str(item.text())
            
            removed = self.data_class.remove_curve(curve)
            
            if removed:
                index = self.curve_list.indexFromItem(item)
                
                remove_item = self.curve_list.takeItem(index.row())
                del(remove_item)
    
    def tab_update(self):
        
        self.curve_list.clear()
        
        curves = self.data_class.get_curves()
        
        if not curves:
            return
        
        for curve in curves:
            item = QtGui.QListWidgetItem(curve)
            self.curve_list.addItem(item)
    
class ControlColorFileWidget(MayaDataFileWidget):
    def _define_data_class(self):
        return vtool.data.ControlColorData()
    
    def _define_option_widget(self):
        return ControlColorOptionFileWidget()
    
    def _define_main_tab_name(self):
        return 'Control Color'
    
class ControlColorOptionFileWidget(ControlCvOptionFileWidget):
    
    def _define_remove_button(self):
        return 'Delete Curve Color Data'
    
class SkinWeightFileWidget(MayaDataFileWidget):
    
    def _define_option_widget(self):
        return SkinWeightOptionFileWidget()
        
    def _define_data_class(self):
        return vtool.data.SkinWeightData()
    
    def _define_main_tab_name(self):
        return 'Skin Weights'
    
class SkinWeightOptionFileWidget(vtool.qt_ui.OptionFileWidget):
    
    def _build_widgets(self):
        super(SkinWeightOptionFileWidget, self)._build_widgets()
        
        data_options_layout = QtGui.QVBoxLayout()
                
        list_widget = QtGui.QListWidget()
        list_widget.setSizePolicy(QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Minimum)
        list_widget.setMaximumHeight(100)
        list_widget.setSelectionMode(list_widget.ExtendedSelection)
        list_widget.setSortingEnabled(True)
        self.list_widget = list_widget
        
        self.filter_names = QtGui.QLineEdit()
        self.filter_names.setPlaceholderText('Filter Names')
        self.filter_names.textChanged.connect(self._filter_names)
        
        remove_button = QtGui.QPushButton('Delete Mesh Skin Weights')
        remove_button.clicked.connect(self._remove_meshes)
                
        self.mesh_list = list_widget
        
        data_options_layout.addWidget(list_widget)
        data_options_layout.addWidget(self.filter_names)
        data_options_layout.addWidget(remove_button)
    
        self.main_layout.addSpacing(20)
        self.main_layout.addLayout(data_options_layout)
        
    def _unhide_names(self):
        for inc in range(0, self.list_widget.count()):
            item = self.list_widget.item(inc)
            item.setHidden(False)
            
    def _filter_names(self):
        self._unhide_names()
                        
        for inc in range( 0, self.list_widget.count() ):
                
            item = self.list_widget.item(inc)
            text = str( item.text() )
            
            filter_text = self.filter_names.text()
            
            if text.find(filter_text) == -1:
                item.setHidden(True)
        
    def _remove_meshes(self):
        
        items = self.mesh_list.selectedItems()
        
        if not items:
            return
        
        for item in items:
            folder = str(item.text())
            
            removed = self.data_class.remove_mesh(folder)
            
            if removed:
                index = self.mesh_list.indexFromItem(item)
                
                remove_item = self.mesh_list.takeItem(index.row())
                del(remove_item)
        
        
    def tab_update(self):
        
        self.mesh_list.clear()
        
        meshes = self.data_class.get_skin_meshes()
        
        if not meshes:
            return
        
        for mesh in meshes:
            item = QtGui.QListWidgetItem(mesh)
            self.mesh_list.addItem(item)
      
class DeformerWeightFileWidget(MayaDataFileWidget):
    def _define_data_class(self):
        return vtool.data.DeformerWeightData()
    
    def _define_main_tab_name(self):
        return 'Deformer Weights'

class BlendShapeWeightFileWidget(MayaDataFileWidget):
    def _define_data_class(self):
        return vtool.data.BlendshapeWeightData()
    
    def _define_main_tab_name(self):
        return 'BlendShape Weights'
      
class AnimationFileWidget(MayaDataFileWidget):
    
    def _define_data_class(self):
        return vtool.data.AnimationData()
    
    def _define_main_tab_name(self):
        return 'Animation Keyframes'
    
class ControlAnimationFileWidget(MayaDataFileWidget):
    def _define_data_class(self):
        return vtool.data.ControlAnimationData()
        
    
    def _define_main_tab_name(self):
        return 'Control Animation Keyframes'
    
        
class AtomFileWidget(MayaDataFileWidget):
    
    def _define_data_class(self):
        return vtool.data.AtomData()
    
    def _define_main_tab_name(self):
        return 'ATOM file'
        
class PoseFileWidget(MayaDataFileWidget):
    
    def _define_save_widget(self):
        return MayaPoseSaveFileWidget()
    
    def _define_data_class(self):
        return vtool.data.PoseData()
    
    def _define_main_tab_name(self):
        return 'Pose Targets'
        
class MayaPoseSaveFileWidget(MayaDataSaveFileWidget):
            
    def _export_data(self):

        comment = ''
        
        self.data_class.export_data(comment)
        self.file_changed.emit()
        
    def _import_data(self):
        
        from vtool.maya_lib import ui
        ui.delete_scene_script_jobs()
        self.data_class.import_data()
        ui.create_scene_script_jobs()

        
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
    
    def _create_button(self, name):
        
        button = QtGui.QPushButton(name)
        
        button.setMaximumWidth(100)
        
        return button
    
    def _build_widgets(self):
        
        save_button = self._create_button('Save')
        
        save_button.setMinimumHeight(50)
        
        export_button = self._create_button('Export')
        open_button = self._create_button('Open')
        import_button = self._create_button('Import')
        reference_button = self._create_button('Reference')
        
        out_box = QtGui.QGroupBox('File Out')
        in_box = QtGui.QGroupBox('File In')
        
        out_box_layout = QtGui.QVBoxLayout()
        in_box_layout = QtGui.QVBoxLayout()
        
        out_box_layout.setContentsMargins(2,2,2,2)
        out_box_layout.setSpacing(2)
        
        in_box_layout.setContentsMargins(2,2,2,2)
        in_box_layout.setSpacing(2)
                
        
        out_box_layout.addWidget(save_button)
        out_box_layout.addWidget(export_button)
        
        in_box_layout.addWidget(open_button)
        in_box_layout.addWidget(import_button)
        in_box_layout.addWidget(reference_button)
        
        out_box.setLayout(out_box_layout)
        in_box.setLayout(in_box_layout)
        
        save_button.clicked.connect( self._save_file )
        export_button.clicked.connect( self._export_file )
        open_button.clicked.connect( self._open_file )
        import_button.clicked.connect( self._import_file )
        reference_button.clicked.connect( self._reference_file )
        
        self.main_layout.addWidget(out_box)
        self.main_layout.addWidget(in_box)
        
        self.main_layout.setAlignment(QtCore.Qt.AlignTop)

    def _skip_mismatch_file(self):
        if vtool.util.is_in_maya():
            
            import maya.cmds as cmds
            current_directory = cmds.file(q = True, expandName = True)
            
            test_directory = vtool.util_file.get_dirname(self.directory)
            
            if current_directory.endswith('unknown') or current_directory.endswith('untitled'):
                return False
            
            if not current_directory.startswith(test_directory):
                result = vtool.qt_ui.get_permission('Root directory different.\nAre you sure you are saving to the right place?', self)
            
                if result:
                    return False
                if not result:
                    return True
            
        return False

    
    def _save_file(self):
        
        if self._skip_mismatch_file():
            return
        
        comment = vtool.qt_ui.get_comment(self)
        
        if comment == None:
            return
        
        self.data_class.save(comment)
        
        self.file_changed.emit()
    
       
    def _export_file(self):
        
        if self._skip_mismatch_file():
            return
        
        comment = vtool.qt_ui.get_comment(self)
        
        if comment == None:
            return
        
        self.data_class.export_data(comment)
        
        self.file_changed.emit()
        
    def _open_file(self):
        
        if vtool.util.is_in_maya():
            import maya.cmds as cmds
            if cmds.file(q = True, mf = True):
                result = vtool.qt_ui.get_permission('Changes not saved. Continue Opening?', self)
                if not result:
                    return
        
        self.data_class.open()
        
    def _import_file(self):
        self.data_class.import_data()
        
    def _reference_file(self):
        self.data_class.maya_reference_data()
        
        
class MayaHistoryFileWidget(vtool.qt_ui.HistoryFileWidget):
    def _build_widgets(self):
        
        super(MayaHistoryFileWidget, self)._build_widgets()
        
        import_button = QtGui.QPushButton('Import')
        import_button.setMaximumWidth(100)
        self.button_layout.addWidget(import_button)
        
        import_button.clicked.connect(self._import_version)
        
        reference_button = QtGui.QPushButton('Reference')
        reference_button.setMaximumWidth(100)
        self.button_layout.addWidget(reference_button)
        
        reference_button.clicked.connect(self._reference_version)
        
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
        
    def _reference_version(self):
        
        item = self.version_list.currentItem()
        
        version = int(item.text(0))
        
        version_tool = vtool.util_file.VersionFile(self.directory)
        version_file = version_tool.get_version_path(version)
        
        maya_file = vtool.data.MayaFileData()
        maya_file.maya_reference_data(version_file)

class ProcessBuildDataWidget(MayaFileWidget):
    
    ascii_data = vtool.data.MayaAsciiFileData()
    binary_data = vtool.data.MayaBinaryFileData()
    
    def __init__(self):
        
        self.data_class_type = self.ascii_data
        
        super(ProcessBuildDataWidget,self).__init__()
        
        self.main_layout.setAlignment(QtCore.Qt.AlignBottom)
    
    def _define_main_tab_name(self):
        return 'BUILD'
    
    def _define_data_class(self):
        return self.data_class_type
    
    def _define_save_widget(self):
        return ProcessSaveFileWidget()
    
    def update_data(self, data_directory):
        
        data_folder = vtool.data.DataFolder('build', data_directory)
        
        data_type = data_folder.get_data_type()
        
        if data_type == 'maya.ascii':
            self.set_data_type(self.ascii_data)
        if data_type == 'maya.binary':
            self.set_data_type(self.binary_data)
        
        if data_type == 'None':
            data_folder.set_data_type('maya.ascii')
            self.set_data_type(self.ascii_data)

    def set_data_type(self, data_class):
        
        self.data_class_type = data_class
        self.save_widget.set_data_class(data_class)
    
    
class ProcessSaveFileWidget(MayaSaveFileWidget):
    
    def _build_widgets(self):
        
        save_button = self._create_button('Save')
        save_button.setMinimumWidth(100)
        open_button = self._create_button('Open')
        open_button.setMinimumWidth(100)
        save_button.clicked.connect( self._save_file )
        open_button.clicked.connect( self._open_file )
        
        self.main_layout.setAlignment(QtCore.Qt.AlignLeft)
        self.main_layout.addWidget(save_button)
        self.main_layout.addWidget(open_button)

        
file_widgets = { 'maya.binary' : MayaBinaryFileWidget,
                 'maya.ascii' : MayaAsciiFileWidget,
                 'maya.control_cvs' : ControlCvFileWidget,
                 'maya.control_colors' : ControlColorFileWidget,
                 'maya.skin_weights' : SkinWeightFileWidget,
                 'maya.deform_weights' : DeformerWeightFileWidget,
                 'maya.blend_weights' : BlendShapeWeightFileWidget,
                 'maya.atom' :  AtomFileWidget,
                 'maya.shaders' : MayaShadersFileWidget,
                 'maya.attributes' : MayaAttributesFileWidget,
                 'maya.pose' : PoseFileWidget,
                 'maya.animation': AnimationFileWidget,
                 'maya.control_animation': ControlAnimationFileWidget}
