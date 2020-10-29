# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

import traceback
import string

import vtool.qt_ui
import vtool.util_file
import vtool.data
import vtool.util
import process

from vtool import qt



from vtool import logger
log = logger.get_logger(__name__) 

class DataProcessWidget(vtool.qt_ui.DirectoryWidget):
    
    data_created = vtool.qt_ui.create_signal(object)
    
    def __init__(self):
        
        self.sidebar = True
        self.settings = vtool.util_file.get_vetala_settings_inst()
        
        if self.settings.has_setting('side bar visible'):
            self.sidebar = self.settings.get('side bar visible')
        
        self.data_tree_widget = None
        self.data_label = None
        super(DataProcessWidget, self).__init__()
        
        self.setMouseTracking(True)
        self.data_tree_widget.setMouseTracking(True)
        
          
    def _define_main_layout(self):
        return qt.QVBoxLayout()
                
    def _build_widgets(self):
        
        splitter = qt.QSplitter()
        
        self.data_tree_widget = DataTreeWidget()
        self.data_tree_widget.itemSelectionChanged.connect(self._data_item_selection_changed)
        self.data_tree_widget.active_folder_changed.connect(self._update_file_widget)
        self.data_tree_widget.data_added.connect(self._add_data)
        
        if self.sidebar:
            self.datatype_widget = DataTypeWidget()
            self.datatype_widget.data_added.connect(self._add_data)
        
        splitter.setSizePolicy(qt.QSizePolicy.Expanding, qt.QSizePolicy.Expanding)   
        self.main_layout.addWidget(splitter, stretch = 1)
                
        splitter.addWidget(self.data_tree_widget)
        if self.sidebar:
            splitter.addWidget(self.datatype_widget)
        
        splitter.setSizes([1,1])
        self.splitter = splitter
        
        self.label = qt.QLabel('-')
        font = self.label.font()
        font.setBold(True)
        font.setPixelSize(12)
        self.label.setMinimumHeight(30)
        self.label.setFont(font)
        self.label.show()
        
        self.data_widget = DataWidget()
        self.data_widget.hide()
        
        self.data_widget.data_updated.connect(self._data_updated)
        self.data_widget.copy_to_top.connect(self._copy_to_top)
        self.data_widget.copy_from_top.connect(self._copy_from_top)
        
        self.data_widget.open_sub_folder.connect(self._open_sub_folder)
        
        
        self.main_layout.addWidget(self.label, alignment = qt.QtCore.Qt.AlignCenter)
        self.main_layout.addWidget(self.data_widget)
        
    def _data_updated(self):
        item = self.data_tree_widget.currentItem()
        
        if not item:
            return
        
        self.data_tree_widget.update_item(item)
        self._set_title()
        
    def _copy_to_top(self):
        
        folder_name = self.data_widget.list.get_selected_item()
        
        process_inst = process.Process()
        process_inst.set_directory(self.directory)
        
        data_name = self.data_tree_widget.current_name
        
        process_inst.copy_sub_folder_to_data(folder_name, data_name)
        
    def _copy_from_top(self):
        
        folder_name = self.data_widget.list.get_selected_item()
        
        process_inst = process.Process()
        process_inst.set_directory(self.directory)
        
        data_name = self.data_tree_widget.current_name
        
        process_inst.copy_data_to_sub_folder(data_name, folder_name)
        
    def _open_sub_folder(self):
        
        folder_name = self.data_widget.list.get_selected_item()
        data_name = self.data_tree_widget.current_name
        
        
        
        process_inst = process.Process()
        
        if not process_inst.has_sub_folder(data_name, folder_name):
            folder_name = None
        
        process_inst.set_directory(self.directory)
        process_inst.open_data(data_name, folder_name)
        
    def _set_title(self, title = None):
        
        if title == None:
            title = self.data_label
        
        if title == None:
            return
            
        name = None
        
        if self.data_widget.list:
            name = self.data_widget.list.get_selected_item()
        
        if name == '-top folder-':
            name = None
        
        if name:
            self.label.setText(title + '                 sub folder:   ' + name)
            
            self.label.show()
        else:
            self.label.setText(title)
            self.label.show()
        
        self.data_label = title
        
    def mouse_move(self, event):
        
        cursor = self.cursor()
        point = cursor.pos()
        width = self.width()
        
        x_value = point.x()
        
        if x_value >= width * .8:
            self.splitter.setSizes([1,1])
        if x_value < width * .8:
            self.splitter.setSizes([1,1])
        
    def _add_data(self, data_name):
        
        self._refresh_data(data_name)
        
        self.data_tree_widget._rename_data()
        self.data_widget.show()
        
    def _refresh_data(self, data_name):
        self.data_tree_widget._load_data(new_data = data_name)
        
        self.data_created.emit(data_name)
        
    def _data_item_selection_changed(self):
        
        self.data_widget.hide()
        
        items = self.data_tree_widget.selectedItems()
        
        item = None
        
        if items:
            if len(items) == 1:
                item = items[0]
            
        if item and not type(item) == str:
            
            item_name = str(item.text(0))
            
            process_tool = process.Process()
            process_tool.set_directory(self.directory)
            process_tool.cache_data_type_read(item_name)
            
            try:
                is_data = process_tool.is_data_folder(item_name)
                
                if is_data:
                    
                    data_type = process_tool.get_data_type(item_name)
                    
                    keys = file_widgets.keys()
                    
                    for key in keys:
                        if key == data_type:
                            widget = file_widgets[key]()
                            
                            if hasattr(widget, 'add_tool_tabs'):
                                widget.add_tool_tabs()
                                
                            path_to_data = vtool.util_file.join_path(process_tool.get_data_path(), item_name  )
                            self.data_widget.add_file_widget(widget, path_to_data)
                            self.data_widget.show()
                            if self.data_widget.list:
                                self.data_widget.list.set_directory(path_to_data)
                                self.data_widget.list.select_current_sub_folder()
                            self._set_title( item_name ) 
                            self.label.show()
                            
                            break
                            
                if not is_data:
                    item = None
            except:
                status = traceback.format_exc()
                vtool.util.error(status)
                  
            process_tool.delete_cache_data_type_read(item_name)
          
        if not item:
            if not self.data_widget.file_widget:
                return
                
            self.data_widget.remove_file_widget()
            self._set_title('-')
            
    def _update_file_widget(self, directory):
        
        if not directory:
            return
        
        self.data_widget.set_directory(directory)
        
        basename = vtool.util_file.get_basename(directory)
        
        self._set_title(basename)
        
                
    def set_directory(self, directory):
        super(DataProcessWidget, self).set_directory(directory)

        log.info('Setting data directory')

        self.data_tree_widget.set_directory(directory)
        self.data_widget.set_directory(directory)
        
        if self.sidebar:
            self.datatype_widget.set_directory( directory )
        
    def clear_data(self):
        self.set_directory('')

class DataWidget(vtool.qt_ui.BasicWidget):
    
    copy_to_top = qt.create_signal()
    copy_from_top = qt.create_signal()
    
    data_updated = vtool.qt_ui.create_signal()
    
    open_sub_folder = vtool.qt_ui.create_signal()
    
    def __init__(self,parent = None, scroll = False):
        self.file_widget = None
        super(DataWidget, self).__init__(parent, scroll)
        
        self.setMinimumHeight(100)
        self.directory = None
    
    def _define_main_layout(self):
        return vtool.qt.QHBoxLayout()
        
    def _build_widgets(self):
        
        self.list = None
        
        self.file_widget = vtool.qt_ui.BasicWidget()
        self.main_layout.addWidget(self.file_widget)
        
    def _data_updated(self):
        self.data_updated.emit()
        
    def _set_file_widget_directory(self, directory):
        
        if not self.file_widget:
            return
        
        folder = directory
        if not directory:
            folder = self.directory
        
        if hasattr(self.file_widget, 'set_directory'):
            self.file_widget.set_directory(folder)
        
        
    def _remove_widget(self, widget):
        
        widget.close()
        widget.deleteLater()
        del widget
        
    def _copy_to_top(self):
        self.copy_to_top.emit()
        
    
    def _copy_from_top(self):
        self.copy_from_top.emit()
        
        
    def _open_sub_folder(self):
        self.open_sub_folder.emit()
        
    def remove_file_widget(self):
        if not self.file_widget:
            return
        
        self._remove_widget(self.file_widget)
        
        self.file_widget = None
    
    def remove_list_widget(self):
        if not self.list:
            return
        
        self._remove_widget(self.list)
        
        self.list = None
    
    def add_list(self):
        if not self.list:
            self.list = SubFolders()
            self.list.copy_to_top_signal.connect(self._copy_to_top)
            self.list.copy_from_top_signal.connect(self._copy_from_top)
            self.list.setMaximumWidth(160)
            
            policy = self.list.sizePolicy()
            
            policy.setHorizontalPolicy(policy.Minimum)
            policy.setVerticalPolicy(policy.Minimum)
            
            #policy.setHorizontalStretch(0)
        
            self.list.setSizePolicy(policy)
            
            self.list.list.itemDoubleClicked.connect(self._open_sub_folder)
            
            self.main_layout.insertWidget(0, self.list)
            
            self.list.item_update.connect(self._set_file_widget_directory)
    
    def add_file_widget(self, widget, directory = None):
        
        self.remove_file_widget()
        
        self.main_layout.addWidget(widget)
        self.file_widget = widget
        if directory:
            self._set_file_widget_directory(directory)
        
        if widget.is_link_widget():
            self.remove_list_widget()
        if not widget.is_link_widget():
            self.add_list()
        
        if hasattr(self.file_widget, 'data_updated'):
            self.file_widget.data_updated.connect(self._data_updated)
    
    def set_directory(self, directory):
        
        self.directory = directory
        
        if self.list:
            self.list.set_directory(directory)
        self._set_file_widget_directory(directory)
        

class SubFolders(vtool.qt_ui.AddRemoveDirectoryList):
    
    copy_to_top_signal = qt.create_signal()
    copy_from_top_signal = qt.create_signal()
    
    def __init__(self, parent = None, scroll = False):
        super(SubFolders, self).__init__(parent, scroll)
        
        self.list.setWhatsThis('The sub folder list.\n'
                          '\n'
                          'An example of when to use this is to organize your maya files.\n'
                          'Create a Ascii File data. Add sub folders for wip, temp, blendshape_wip, etc.'
                          'Your files will appear neat and organized in this menu.\n\n'
                          'The selected sub folder is persistant.\n' 
                          'This means that data loading in scripts will come from the sub folder if selected in the ui.\n'
                          'This can be useful when working on Skin Weights.\n'  
                          'Create a wip sub folder in your skin weights. Do right-click - Copy from Top Folder to this.\n'
                          'Work on your weights, and your rig will build using the currently seleted wip sub folder.\n'
                          'When done, right click on the sub folder and select  Copy this to Top Folder and select -top folder-\n'
                          'Your rig will now build with the -top folder- weights.\n\n'
                          'Another use for this is to store an inventory of poses.\n'
                          'Create a control value data.\n'
                          'Pose your character, each time create a new sub folder.\n'
                          'Double click on a sub folder to load it and easily bring back your poses.\n')
    
    def _define_defaults(self):
        return ['-top folder-']
    
    def _item_menu(self, position):
        
        
        item = self.list.itemAt(position)
        
        if item:
            name = str(item.text())
            
            if name in self._define_defaults():
                self.copy_to_top.setVisible(False)
                self.copy_from_top.setVisible(False)
                return
            
            self.copy_to_top.setVisible(True)
            self.copy_from_top.setVisible(True)
            
        if not item:
            self.copy_to_top.setVisible(False)
            self.copy_from_top.setVisible(False)
        
        super(SubFolders, self)._item_menu(position)
        
        
    def _create_context_menu(self):
        super(SubFolders, self)._create_context_menu()
        
        self.context_menu.addSeparator() 
        self.copy_to_top = self.context_menu.addAction('Copy this to Top Folder')
        self.copy_from_top = self.context_menu.addAction('Copy from Top Folder to this')
        self.copy_to_top.triggered.connect(self._copy_to_top)
        self.copy_from_top.triggered.connect(self._copy_from_top)
        

    def _copy_to_top(self):
        self.copy_to_top_signal.emit()
    
    def _copy_from_top(self):
        self.copy_from_top_signal.emit()

class DataTreeWidget(vtool.qt_ui.FileTreeWidget):
    
    active_folder_changed = vtool.qt_ui.create_signal(object)
    data_added = vtool.qt_ui.create_signal(object)
    
    def __init__(self):     
        super(DataTreeWidget, self).__init__()
        
        if vtool.qt_ui.is_pyside():
            self.header().setResizeMode(0, qt.QHeaderView.Stretch)
            self.header().setResizeMode(1, qt.QHeaderView.Stretch)
        if vtool.qt_ui.is_pyside2():
            self.header().setSectionResizeMode(0, qt.QHeaderView.Stretch)
            self.header().setSectionResizeMode(1, qt.QHeaderView.Stretch)
        self.header().setStretchLastSection(False)
        
        self.text_edit = False
        
        self.directory = None
        
        self.setColumnWidth(0, 140)
        self.setColumnWidth(1, 110)
        self.setColumnWidth(2, 100)
        #removed because data update slow
        #self.setColumnWidth(3, 50)
        
        self.setContextMenuPolicy(qt.QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._item_menu)
        
        self._create_context_menu()
        
        self.setAlternatingRowColors(True)
        
        self.setIndentation(2)
        
        self.setWhatsThis('The data list.\n'
                          '\n'
                          'This view shows the data in the current process.\n'
                          'Right click on empty space to create or browse the data in the file system.\n'
                          'Right click on data to create, rename and delete.\n'
                          'There is also the right click option to browse.Use this to see how data lives on the file system.\n'
                          'Double click on data to see the data in the file system.\n'
                          'Also right-click refresh will sync this view with what is currently in the file system.')
    
    def resizeEvent(self, event):
        super(DataTreeWidget, self).resizeEvent(event)

    def _item_menu(self, position):
        
        item = self.itemAt(position)
            
        if item:
            self.rename_action.setVisible(True)
            self.remove_action.setVisible(True)
        if not item:
            self.rename_action.setVisible(False)
            self.remove_action.setVisible(False)
        self.context_menu.exec_(self.viewport().mapToGlobal(position))
        
    def _create_context_menu(self):
        
        self.context_menu = qt.QMenu()
        
        data_types = vtool.data.DataManager().get_available_types()
        
        top_menus = {}
        menu_inst = None
        for data_type in data_types:
            
            split_data = data_type.split('.')
            menu_name = split_data[0]
            if menu_name == 'script':
                continue
            
            nice_name = data_name_map[data_type]
            
            if not top_menus.has_key(menu_name):
                menu_inst = self.context_menu.addMenu(menu_name.capitalize())
                top_menus[menu_name] = menu_inst
            else:
                menu_inst = top_menus[menu_name]
            
            menu_inst.addAction(nice_name)
            
        if menu_inst:
            menu_inst.triggered.connect(self._create_data)
            #action.triggered.connect(self._create_data)
        
        self.context_menu.addSeparator()
        
        self.rename_action = self.context_menu.addAction('Rename')
        self.remove_action = self.context_menu.addAction('Delete')
        self.context_menu.addSeparator()
        self.browse_action = self.context_menu.addAction('Browse')
        self.refresh_action = self.context_menu.addAction('Refresh')
        
        self.rename_action.triggered.connect(self._rename_data)
        self.browse_action.triggered.connect(self._browse_current_item)
        self.remove_action.triggered.connect(self._remove_current_item)
        self.refresh_action.triggered.connect(self.refresh)    
    
    def _create_data(self, data):
        
        data_type = str(data.text())
        data_group = 'maya'        
        
        if not data_type or not data_group:
            return
        
        data_type = data_name_map.keys()[data_name_map.values().index(data_type)] 
        
        manager = vtool.data.DataManager()
        data_instance = manager.get_type_instance(data_type)
        data_name = data_instance._data_name()
        
        process_tool = process.Process()
        process_tool.set_directory(self.directory)
        
        data_path = process_tool.create_data(data_name, data_type)
        
        data_name = vtool.util_file.get_basename(data_path)
        
        self.data_added.emit(data_name)
    
    
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
        
        
        
        index = self.indexOfTopLevelItem(items[0])
        self.takeTopLevelItem(index)
        
        #this needs to happend after the item is taken away or else data gets corrupted
        process_tool = process.Process()
        process_tool.set_directory(self.directory)
        process_tool.delete_data(name)
    
    def _define_header(self):
        #data size update removed because very slow
        #return ['Name','Folder', 'Type','Size']
        return ['Name','Type', 'Folder']
    
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
        
        log.info('Loading data files %s' % folders)
        
        if not folders:
            return
        
        select_item = None
        
        for foldername in folders:
            
            item = qt.QTreeWidgetItem()
            item.setText(0, foldername)
            
            sub_folder, data_type = process_tool.get_data_current_sub_folder_and_type(foldername)
            
            if not data_name_map.has_key(data_type):
                vtool.util.warning('Data folder %s has no data type.' % foldername)
                nice_name = '-non vetala folder-'
                item.setDisabled(True)
            else:
                nice_name = data_name_map[data_type]
            
            group = ''
            
            if data_type:
                group = data_type.split('.')[0]
            
            group = group.capitalize()
            
            item.setText(1, nice_name)
            item.setText(2, sub_folder)
            
            item.folder = foldername
            
            self.addTopLevelItem(item)
            
            if foldername == new_data:
                select_item = item
        
        if select_item:
            self.setItemSelected(select_item, True)
            self.setCurrentItem(select_item)
        
    def update_file_size(self, item):
        return 
        #process_tool = process.Process()
        #process_tool.set_directory(self.directory)
        
        #data_dir = process_tool.get_data_path()
        
        #size_thread = DataSizeThread()
        
        #folder = str(item.text(0))
        #size_thread.run(data_dir, folder, item)
        
    def update_item(self, item):
        
        process_tool = process.Process()
        process_tool.set_directory(self.directory)
        
        #data_dir = process_tool.get_data_path()
        
        #size_thread = DataSizeThread()
        
        folder = str(item.text(0))
        #size_thread.run(data_dir, folder, item)
        
        sub = process_tool.get_data_current_sub_folder(folder)
        item.setText(2, sub)
        
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

class DataSizeThread(qt.QtCore.QThread):
    def __init__(self, parent = None):
        super(DataSizeThread, self).__init__(parent)
        
    def run(self, data_path, data_name, item):
        """
        """
        pass
        #was too slow
        #data_folder = vtool.util_file.join_path(data_path, data_name)
        #size = vtool.util_file.get_folder_size(data_folder, skip_names=['.version','.sub'])
        
        #item.setText(3, str(size) )
        
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
        
        policy.setHorizontalPolicy(policy.Expanding)
        policy.setHorizontalStretch(0)
        
        self.setSizePolicy(policy)
        self.setMinimumWidth(150)
        self.setMaximumWidth(170)
        
        
        
    def sizeHint(self):
        
        return qt.QtCore.QSize(0,50)
                
    def _build_widgets(self):
        self.data_type_tree_widget = DataTypeTreeWidget()
        
        add_button = vtool.qt_ui.BasicButton('Add')
        add_button.setWhatsThis('This button will add the selected data type to the process.\n'
                                'You can add each data type more than once. Eg. You can have multiple skin weight data.\n')
        #add_button = qt.QPushButton('Add')
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
    
class DataTypeTreeWidget(qt.QTreeWidget):
    
    def __init__(self):
        
        super(DataTypeTreeWidget, self).__init__()
        self.setHeaderHidden(True)
        self.setHeaderLabels(['Data Type'])
        self.setIndentation(10)
        
        self.setWhatsThis('Data Type List\n\n'
                          'This list shows data available to the process.\n'
                          'Clicking add at the bottom will add the data to the process for editing.\n'
                          'Data can also be added using the right click menu in the data view.\n'
                          'This menu can be disabled in the settings, at which point the right click menu could be used exclusively for adding data\n'
                          
                          )

    def mousePressEvent(self, event):
        
        modifiers = qt.QApplication.keyboardModifiers()
        
        if modifiers == qt.QtCore.Qt.AltModifier:
            position = self.mapToGlobal(self.rect().topLeft())
            qt.QWhatsThis.showText(position, self.whatsThis())
            return
        
        
        super(DataTypeTreeWidget, self).mousePressEvent(event)
   
    def _find_group(self, groupname):
        for inc in range(0, self.topLevelItemCount() ):
                
            item = self.topLevelItem(inc)
            
            text = str( item.text(0) )
                
            if text == groupname:
                return item       

    def _add_data_item(self, data_type, parent):
        
        item = qt.QTreeWidgetItem(parent)
        item.setText(0, data_type)
        #item.setSizeHint(0, qt.QtCore.QSize(100, 20))
        
        #self.addTopLevelItem(item)
        
        return item
        
    def add_data_type(self, data_type):
        
        split_type = data_type.split('.')
        
        nice_name = split_type[1]
        
        if data_name_map.has_key(data_type):
            nice_name = data_name_map[data_type]
        
        group_type = split_type[0].capitalize()
        
        
        if split_type[0].startswith('script'):
            return
        
        group_item = self._find_group(group_type)
        
        if not group_item:
            item = qt.QTreeWidgetItem()
            item.setText(0, group_type)
            #item.setSizeHint(0, qt.QtCore.QSize(100, 25))
            
            self.addTopLevelItem(item)    
            group_item = item
        
        
        
        new_item = self._add_data_item(nice_name, group_item)
        new_item.data_type = data_type
        
        return new_item
        
    
    def get_data_type(self):
        
        item = self.currentItem()
        if hasattr(item, 'data_type'):
            return item.data_type
    
    def get_data_group(self):
        item = self.currentItem()
        parent = item.parent()
        if parent:
            return str(parent.text(0))

#--- data widgets

class DataLinkWidget(vtool.qt_ui.BasicWidget):
    
    
    
    def __init__(self):
        
        self.data_class = self._define_data_class()
        
        super(DataLinkWidget, self).__init__()
        
        self.directory = None
        
    def _build_widgets(self):
        super(DataLinkWidget, self)._build_widgets()
        

    
    def _define_main_tab_name(self):
        return 'data link'
    
    def _define_data_class(self):
        return None
    
    def is_link_widget(self):
        return True
    
    def set_directory(self, directory):
        if self.data_class:
            self.data_class.set_directory(directory)
        self.directory = directory
    
class MayaShotgunLinkWidget(DataLinkWidget):
    def _define_main_tab_name(self):
        return 'Maya Shotgun Link'
    
    def _create_button(self, name):
        
        button = qt.QPushButton(name)
        
        button.setMaximumWidth(150)
        button.setMinimumWidth(100)
        
        return button
    
    def _build_widgets(self):
        super(MayaShotgunLinkWidget, self)._build_widgets()
        
        h_layout = qt.QHBoxLayout()
        
        projects = self.data_class.get_projects()
        
        self.combo_project = qt.QComboBox()
        
        for project in projects:
            self.combo_project.addItem(project)
        
        self.combo_asset_type = qt.QComboBox()
        
        self.assets = self.data_class.get_assets(self.combo_project.itemText(0))
        
        if self.assets:
            keys = self.assets.keys()
            keys.sort()
        
            for key in keys:
                if key:
                    self.combo_asset_type.addItem(key)
        
        self.combo_asset = qt.QComboBox()
        
        current_text = self.combo_asset_type.currentText()
        
        assets = self.assets[current_text]
        
        if current_text:
            assets = self.assets[current_text]
        
            if assets:
                assets.sort()
                for asset in assets:
                    self.combo_asset.addItem(asset)
        
        steps = self.data_class.get_asset_steps()
        
        self.combo_asset_step = qt.QComboBox()
        #self.combo_asset_step.setMaximumWidth(160)
        
        self.update_current_changed = True
        
        for step in steps:
            self.combo_asset_step.addItem(step[0])
        
        self.combo_task = qt.QComboBox()
        
        tasks = self.data_class.get_asset_tasks(self.combo_project.currentText(), 
                                                self.combo_asset_step.currentText(), 
                                                self.combo_asset_type.currentText(), 
                                                self.combo_asset.currentText())
        
        for task in tasks:
            self.combo_task.addItem(task[0])
        
        self.asset_is_name = qt.QCheckBox('Asset is Custom Name')
        
        v_layout1 = qt.QVBoxLayout()
        v_layout2 = qt.QVBoxLayout()
        v_layout3 = qt.QVBoxLayout()
        
        self.warning = qt.QLabel('No Shotgun Found!')
        
        self.main_layout.addWidget(self.warning)
        
        self.warning.hide()
        
        v_layout1.addWidget(qt.QLabel('Project'))
        v_layout1.addWidget(self.combo_project)
        v_layout1.addWidget(qt.QLabel('Step'))
        v_layout1.addWidget(self.combo_asset_step)
        
        v_layout2.addWidget(qt.QLabel('Type'))
        v_layout2.addWidget(self.combo_asset_type)
        v_layout2.addWidget(qt.QLabel('Task'))
        v_layout2.addWidget(self.combo_task)
        
        #v_layout3.setAlignment(qt.QtCore.Qt.AlignTop)
        
        v_layout3.addWidget(qt.QLabel('Name'))
        v_layout3.addWidget(self.combo_asset)
        v_layout3.addWidget(qt.QLabel('Custom Name'))
        self.custom_line = qt.QLineEdit()
        v_layout3.addWidget(self.custom_line)
        
        
        h_layout.addLayout(v_layout1,1)
        h_layout.addLayout(v_layout2,1)
        h_layout.addLayout(v_layout3,1)
        
        
        
        
        self.main_layout.addLayout(h_layout)
        
        self.main_layout.addWidget(self.asset_is_name)
        
        self.combo_project.currentIndexChanged.connect(self._project_current_changed)
        self.combo_asset_type.currentIndexChanged.connect(self._asset_type_current_changed)
        self.combo_asset.currentIndexChanged.connect(self._asset_current_changed)
        self.combo_asset_step.currentIndexChanged.connect(self._asset_step_current_changed)
        self.combo_task.currentIndexChanged.connect(self._write_out_state)
        self.custom_line.textChanged.connect(self._write_out_state)
        self.asset_is_name.stateChanged.connect(self._write_out_state)
        
        self._build_save_widget()
        
        if not self.data_class.has_api():
            self.warning.show()
    
    def _build_save_widget(self):
        
        h_layout = qt.QHBoxLayout()
        v_layout1 = qt.QVBoxLayout()
        v_layout2 = qt.QVBoxLayout()
        
        self.save_button = self._create_button('Save')
        
        self.save_button.setMinimumHeight(50)
        
        #export_button = self._create_button('Export')
        self.open_button = self._create_button('Open')
        self.import_button = self._create_button('Import')
        self.reference_button = self._create_button('Reference')
        
        self.save_button.clicked.connect( self._save_file )
        #export_button.clicked.connect( self._export_file )
        self.open_button.clicked.connect( self._open_file )
        self.import_button.clicked.connect( self._import_file )
        self.reference_button.clicked.connect( self._reference_file )
        
        v_layout1.addWidget(self.save_button)
        #v_layout1.addWidget(export_button)
        
        v_layout2. addWidget(self.open_button)
        v_layout2.addWidget(self.import_button)
        v_layout2.addWidget(self.reference_button)
        
        h_layout.addLayout(v_layout1)
        h_layout.addStretch(20)
        
        h_layout.addLayout(v_layout2)
        h_layout.addStretch(40)
        
        self.main_layout.addSpacing(10)
        self.main_layout.addLayout(h_layout)
        
        self.main_layout.setAlignment(qt.QtCore.Qt.AlignTop)
    
    def _write_out_state(self):
        
        project = str(self.combo_project.currentText())
        asset_type = str(self.combo_asset_type.currentText())
        asset = str(self.combo_asset.currentText())
        step = str(self.combo_asset_step.currentText())
        task = str(self.combo_task.currentText())
        custom = str(self.custom_line.text())
        asset_is_name = str(self.asset_is_name.isChecked())
        
        self.data_class.write_state(project, asset_type, asset, step, task, custom, asset_is_name)
    
    def _read_state(self):
        
        self.update_current_changed = False
        
        project, asset_type, asset, step, task, custom, asset_is_name = self.data_class.read_state()
        
        if project:
            project_index = self.combo_project.findText(project)
            if project_index != None:
                self.combo_project.setCurrentIndex(project_index)
            
        if asset_type:
            asset_type_index = self.combo_asset_type.findText(asset_type)
            if asset_type_index != None:
                self.combo_asset_type.setCurrentIndex(asset_type_index)
            
        if asset:
            asset_index = self.combo_asset.findText(asset)
            if asset_index != None:
                self.combo_asset.setCurrentIndex(asset_index)
            
        if step:
            step_index = self.combo_asset_step.findText(step)
            if step_index != None:
                self.combo_asset_step.setCurrentIndex(step_index)
        
        if task:
            task_index = self.combo_task.findText(task)
            if task_index != None:
                self.combo_task.setCurrentIndex(task_index)
                
        if custom:
            self.custom_line.setText(custom)
        
        if asset_is_name:
            bool_value = eval(asset_is_name)
            if bool_value:
                self.asset_is_name.setChecked()
        
        self.update_current_changed = True
    
    def _open_file(self):
        
        self.data_class.open()
    
    def _import_file(self):
        self.data_class.import_data()
        
    def _save_file(self):
        
        permission = vtool.qt_ui.get_permission('Save to Shotgun as next work version?', self)
        
        if permission:
            self.data_class.save()

    def _reference_file(self):
        
        self.data_class.reference()
    
    def _project_current_changed(self):
        
        project = self.combo_project.currentText()
        
        self.assets = self.data_class.get_assets(project)
        
        self.combo_asset_type.clear()
        self.combo_asset.clear()
        
        keys = self.assets.keys()
        keys.sort()
        
        for key in keys:
            self.combo_asset_type.addItem(key)
        
        current_text = self.combo_asset_type.currentText()
        if self.assets.has_key(current_text):
            assets = self.assets[current_text]
            
            assets.sort()
            
            for asset in assets:
                self.combo_asset.addItem(asset)
                
        self._write_out_state()
    
    def _asset_type_current_changed(self):
        self.combo_asset.clear()
        
        current_text = self.combo_asset_type.currentText()
        if self.assets.has_key(current_text):
        
            assets = self.assets[current_text]
            assets.sort()
        
            for asset in assets:
                self.combo_asset.addItem(asset)
                
        
    
    def _asset_current_changed(self):
        
        self._load_tasks()
        
        self._write_out_state()
        
    def _asset_step_current_changed(self):
        
        self._load_tasks()
        
        self._write_out_state()
        
    def _load_tasks(self):
        
        self.combo_task.clear()
        
        project = self.combo_project.currentText()
        asset_step = self.combo_asset_step.currentText()
        asset_type = self.combo_asset_type.currentText()
        asset = self.combo_asset.currentText()
        
        tasks = self.data_class.get_asset_tasks(project, asset_step, asset_type, asset)
        
        for task in tasks:
            self.combo_task.addItem(task[0])
        
    def _define_data_class(self):
        return vtool.data.MayaShotgunFileData()
    
    def set_directory(self, directory):
        super(MayaShotgunLinkWidget, self).set_directory(directory)
        
        self._read_state()
        
        if self.data_class.has_api():
            self.warning.hide()
            
            self.combo_asset.setEnabled(True)
            self.combo_asset_step.setEnabled(True)
            self.combo_asset_type.setEnabled(True)
            self.combo_project.setEnabled(True)
            self.combo_task.setEnabled(True)
            
            self.save_button.setEnabled(True)
            self.open_button.setEnabled(True)
            self.import_button.setEnabled(True)
            self.reference_button.setEnabled(True)
            
        if not self.data_class.has_api():
            self.warning.show()
            self.save_button.setDisabled(True)
            self.open_button.setDisabled(True)
            self.import_button.setDisabled(True)
            self.reference_button.setDisabled(True)
            
            self.combo_asset.setEnabled(False)
            self.combo_asset_step.setEnabled(False)
            self.combo_asset_type.setEnabled(False)
            self.combo_project.setEnabled(False)
            self.combo_task.setEnabled(False)

class DataFileWidget(vtool.qt_ui.FileManagerWidget):
    
    def is_link_widget(self):
        return False
    
    def set_sub_folder(self, folder_name):
        #be careful to also update MayaFileWidget
        
        if not self.data_class:
            return
        
        self.data_class.set_sub_folder(folder_name)
    
    def set_directory(self, directory):
        
        super(DataFileWidget, self).set_directory(directory)
        
        parent_path = vtool.util_file.get_dirname(directory)
        name = vtool.util_file.get_basename(directory)
        
        data_folder = vtool.data.DataFolder(name, parent_path)
                        
        instance = data_folder.get_folder_data_instance()
        
        self.data_class = instance
        
        self.save_widget.set_directory(directory)
        self.save_widget.set_data_class(instance)
        
        self.history_widget.set_directory(directory)
        self.history_widget.set_data_class(instance)
                

class MayaDataFileWidget(DataFileWidget):

    def _define_main_tab_name(self):
        return 'data file'
    
    def _define_import_help(self):
        return 'No help'
    
    def _define_export_help(self):
        return 'No help'
    
    def _define_save_widget(self):
        data_inst = MayaDataSaveFileWidget()
        
        data_inst.set_import_help(self._define_import_help())
        data_inst.set_export_help(self._define_export_help())
        
        return data_inst
        
    def _define_history_widget(self):
        return MayaDataHistoryFileWidget()
    
    
    
class MayaDataSaveFileWidget(vtool.qt_ui.SaveFileWidget):
    
    def __init__(self, parent = None):
        self._import_help = 'No help'
        self._export_help = 'No help'
        super(MayaDataSaveFileWidget, self).__init__(parent)
        
        
    def _create_button(self, name):
        
        button = vtool.qt_ui.BasicButton(name)
        button.setMaximumWidth(120)
        
        return button
    
    def _build_widgets(self):
            
        import_button = self._create_button('Import')
        import_button.clicked.connect(self._import_data)
        import_button.setWhatsThis(self._import_help)
        
        export_button = self._create_button('Export')
        export_button.clicked.connect(self._export_data)
        export_button.setWhatsThis(self._export_help)
        
        self.import_button = import_button
        self.export_button = export_button
        
        self.main_layout.addWidget(export_button) 
        self.main_layout.addWidget(import_button) 
        
    def _export_data(self):
        
        comment = vtool.qt_ui.get_comment(self)
        if comment == None:
            return
        
        self.data_class.export_data(comment)
        self.file_changed.emit()
        
    def _import_data(self):
        
        if not vtool.util_file.exists(self.data_class.get_file()):
            
            vtool.qt_ui.warning('No data to import.', self)
            return
        
        self.data_class.import_data()
        
    def set_import_help(self, text):
        self._import_help = text
        self.import_button.setWhatsThis(text)

    def set_export_help(self, text):
        self._export_help = text
        self.export_button.setWhatsThis(text)        
        
class MayaDataHistoryFileWidget(vtool.qt_ui.HistoryFileWidget):
    
    def _open_version(self):
        
        items = self.version_list.selectedItems()
        
        item = None
        if items:
            item = items[0]
        
        if not item:
            vtool.util.warning('No version selected')
            return
        
        version = int(item.text(0))
        
        version_tool = vtool.util_file.VersionFile(self.directory)
        version_file = version_tool.get_version_path(version)
        
        vtool.util.show('Loading version: %s' % version_file)
        
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
        
        save_button = qt.QPushButton('Save')
        save_button.clicked.connect(self._save_button)
        save_button.setMaximumWidth(100)
        
        self.main_layout.addWidget(save_button)    

    def _save_button(self):
        self._save(force_popup=True)

    def _save(self, comment = None, parent = None, force_popup = False):
        
        log.info('UI Saving code')
        
        if not parent:
            parent = self
        
        """
        if not self.text_widget.is_modified():
            vtool.qt_ui.warning('No changes to save.', self)
            return
        """
        text = self.text_widget.toPlainText()
        
        settings = vtool.util_file.get_vetala_settings_inst()
        
        popup_save = True
        
        if not force_popup:
            
            if settings.has_setting('code popup save'):
                popup_save = settings.get('code popup save')
        
        if popup_save:
            if comment == None or comment == False:
                comment = vtool.qt_ui.get_comment(parent, title = 'Save %s' % self.data_class.name)
            
            if comment == None:
                return
        if not popup_save:
            comment = 'code update'
        
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
        
        items = self.version_list.selectedItems()
        
        item = None
        if items:
            item = items[0]
        
        if not item:
            vtool.util.warning('No version selected')
            return
        
        version = int(item.text(0))
        
        version_tool = vtool.util_file.VersionFile(self.directory)
        version_file = version_tool.get_version_path(version)
        
        in_file = qt.QtCore.QFile(version_file)
        
        if in_file.open(qt.QtCore.QFile.ReadOnly | qt.QtCore.QFile.Text):
            text = in_file.readAll()
            
            text = str(text)
            
            self.text_widget.setPlainText(text)
            
    def set_text_widget(self, text_widget):
        self.text_widget = text_widget
    
class ControlCvFileWidget(MayaDataFileWidget):
    def _define_io_tip(self):
        return """This will export/import control cv positions.
    Controls are discovered automatically, no need to select them."""
    
    def _build_widgets(self):
        super(ControlCvFileWidget, self)._build_widgets()
        
        if vtool.util.is_in_maya():
            from vtool.maya_lib.ui_lib import ui_rig        
            self.add_tab(ui_rig.ControlWidget(), 'Tools')
    
    def _define_import_help(self):
        return 'Tries to import control cv positions from exported data. If the control no longer exists it will print a warning.'
    
    def _define_export_help(self):
        return 'Automatically finds the controls in the scene and exports their cv positions relative to the transformation matrix.  Meaning you can pose the character and still export cvs without worrying.'
    
    
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
        
        data_options_layout = qt.QVBoxLayout()
                
        list_widget = qt.QListWidget()
        list_widget.setSizePolicy(qt.QSizePolicy.MinimumExpanding,qt.QSizePolicy.MinimumExpanding)
        #list_widget.setMaximumHeight(100)
        list_widget.setSelectionMode(list_widget.ExtendedSelection)
        list_widget.setSortingEnabled(True)
        self.list_widget = list_widget
        
        self.filter_names = qt.QLineEdit()
        self.filter_names.setPlaceholderText('Filter Names')
        self.filter_names.textChanged.connect(self._filter_names)
        
        remove_button = qt.QPushButton(self._define_remove_button())
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
            item = qt.QListWidgetItem(curve)
            self.curve_list.addItem(item)
    
class ControlColorFileWidget(MayaDataFileWidget):
    def _define_data_class(self):
        return vtool.data.ControlColorData()
    
    def _define_io_tip(self):
        return """This will export/import control colors.
    Controls are discovered automatically, no need to select them."""
    
    def _define_option_widget(self):
        return ControlColorOptionFileWidget()
    
    def _define_main_tab_name(self):
        return 'Control Color'
    
class ControlColorOptionFileWidget(ControlCvOptionFileWidget):
    
    def _define_remove_button(self):
        return 'Delete Curve Color Data'
    
class SkinWeightFileWidget(MayaDataFileWidget):
    
    def __init__(self):
        super(SkinWeightFileWidget, self).__init__()

        if vtool.util.is_in_maya():
            
            from vtool.maya_lib.ui_lib import ui_rig
            widget = ui_rig.SkinWidget(scroll = True)
            
            self.add_tab(widget, 'Tools')
            #index = self.tab_widget.addTab(ui_rig.SkinWidget(scroll = True), 'Tools')
            #self.tab_widget.widget(index).hide()
        
    def _define_io_tip(self):
        
        tip = """    This will export/import skin weights. 
    To Export you must select a geometry with a skinCluster.
    To import you do not need to have anything selected.
    Weights will import on everything that was exported that can be found.
    However you can import on just the selected geometry as well."""
        
        return tip
        
    
    def _define_option_widget(self):
        return SkinWeightOptionFileWidget()
        
    def _define_data_class(self):
        return vtool.data.SkinWeightData()
    
    def _define_main_tab_name(self):
        return 'Skin Weights'
    
class SkinWeightOptionFileWidget(vtool.qt_ui.OptionFileWidget):
    
    def _build_widgets(self):
        super(SkinWeightOptionFileWidget, self)._build_widgets()
        
        data_options_layout = qt.QVBoxLayout()
                
        list_widget = qt.QListWidget()
        list_widget.setSizePolicy(qt.QSizePolicy.Expanding,qt.QSizePolicy.Expanding)
        #list_widget.setMaximumHeight(100)
        list_widget.setSelectionMode(list_widget.ExtendedSelection)
        list_widget.setSortingEnabled(True)
        self.list_widget = list_widget
        
        self.filter_names = qt.QLineEdit()
        self.filter_names.setPlaceholderText('Filter Names')
        self.filter_names.textChanged.connect(self._filter_names)
        
        remove_button = qt.QPushButton('Delete Mesh Skin Weights')
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
            item = qt.QListWidgetItem(mesh)
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
        
        from vtool.maya_lib import ui_core
        ui_core.delete_scene_script_jobs()
        self.data_class.import_data()
        ui_core.create_scene_script_jobs()

        
class MayaShadersFileWidget(MayaDataFileWidget):
    
    def _define_data_class(self):
        return vtool.data.MayaShadersData()

    def _define_main_tab_name(self):
        return 'Maya Shaders'
    
class MayaAttributesFileWidget(MayaDataFileWidget):
    
    def _build_widgets(self):
        super(MayaAttributesFileWidget, self)._build_widgets()
            
    def _define_data_class(self):
        return vtool.data.MayaAttributeData()

    def _define_main_tab_name(self):
        return 'Maya Attributes'

class MayaControlAttributesFileWidget(MayaDataFileWidget):
    def _define_data_class(self):
        return vtool.data.MayaControlAttributeData()

    def _define_main_tab_name(self):
        return 'Maya Control Values'
                

class MayaControlRotateOrderFileWidget(MayaDataFileWidget):
    def _define_data_class(self):
        return vtool.data.MayaControlRotateOrderData()

    def _define_main_tab_name(self):
        return 'Maya Control RotateOrder'

class MayaFileWidget(vtool.qt_ui.FileManagerWidget):

    def __init__(self, add_tools = False):
        super(MayaFileWidget, self).__init__()

    def _define_main_tab_name(self):
        return 'Maya File'
    
    def _define_save_widget(self):
        return MayaSaveFileWidget()
    
    def _define_history_widget(self):
        return MayaHistoryFileWidget()

    def add_tool_tabs(self):        
        if vtool.util.is_in_maya():
            from vtool.maya_lib.ui_lib import ui_rig
        
            self.add_tab(ui_rig.StructureWidget(), 'Structure')
            self.add_tab(ui_rig.DeformWidget(), 'Deformation')

    def is_link_widget(self):
        return False

    def set_sub_folder(self, folder_name):
        self.data_class.set_sub_folder(folder_name)


    
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
        
        button = vtool.qt_ui.BasicButton(name)
        #button = qt.QPushButton(name)
        
        button.setMaximumWidth(100)
        button.setMinimumWidth(100)
        
        return button
    
    def _build_widgets(self):
        
        h_layout = qt.QHBoxLayout()
        v_layout1 = qt.QVBoxLayout()
        v_layout2 = qt.QVBoxLayout()
        
        save_button = self._create_button('Save')
        save_button.setWhatsThis('Save the current maya scene.')
        
        
        export_button = self._create_button('Export')
        
        export_button.setWhatsThis('Vetala will select the top transforms and sets in the outliner and then export them to a file.')
        
        export_selected_button = self._create_button('Export Selected')
        
        export_selected_button.setWhatsThis('Export the current selection to a file')
        
        open_button = self._create_button('Open')
        
        open_button.setWhatsThis('Open the previously saved file.')
        
        import_button = self._create_button('Import')
        
        import_button.setWhatsThis('Import the previously saved file.')
        
        reference_button = self._create_button('Reference')
        
        reference_button.setWhatsThis('Reference the previously saved file.')
        
        save_button.setMinimumHeight(50)
        open_button.setMinimumHeight(50)
        
        save_button.clicked.connect( self._save_file )
        export_button.clicked.connect( self._export_file )
        export_selected_button.clicked.connect(self._export_file_selected)
        open_button.clicked.connect( self._open_file )
        import_button.clicked.connect( self._import_file )
        reference_button.clicked.connect( self._reference_file )
        
        v_layout1.addWidget(save_button)
        v_layout1.addWidget(export_button)
        v_layout1.addWidget(export_selected_button)
        
        v_layout2. addWidget(open_button)
        v_layout2.addWidget(import_button)
        v_layout2.addWidget(reference_button)
        
        h_layout.addStretch(20)
        h_layout.addLayout(v_layout1)
        h_layout.addStretch(20)
        
        h_layout.addLayout(v_layout2)
        h_layout.addStretch(40)
        
        self.main_layout.setSpacing(2)
        self.main_layout.addLayout(h_layout)
        
        #self.main_layout.setAlignment(qt.QtCore.Qt.AlignTop)
        self.main_layout.setAlignment(qt.QtCore.Qt.AlignCenter)

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
    
    def _export_file_selected(self):
        import maya.cmds as cmds
        selection = cmds.ls(sl = True)
        
        self._export_file(selection)
       
    def _export_file(self, selection = None):
        
        if self._skip_mismatch_file():
            return
        
        comment = vtool.qt_ui.get_comment(self)
        
        if comment == None:
            return
        
        self.data_class.export_data(comment, selection)
        
        self.file_changed.emit()
        
    def _auto_save(self):
        if not vtool.util.is_in_maya():
            return
        
        import maya.cmds as cmds
        
        filepath = cmds.file(q = True, sn = True)
        
        from vtool.maya_lib import core
        saved = core.save(filepath)
        
        return saved
    
    def _open_file(self):
        
        if not vtool.util_file.is_file(self.data_class.get_file()):
            vtool.qt_ui.warning('No data to open. Please save once.', self)
            return
        
        if vtool.util.is_in_maya():
            import maya.cmds as cmds
            if cmds.file(q = True, mf = True):
                
                filepath = cmds.file(q = True, sn = True)
                
                process_path = vtool.util.get_env('VETALA_CURRENT_PROCESS')
                filepath = vtool.util_file.remove_common_path_simple(process_path, filepath)
                
                result = vtool.qt_ui.get_save_permission('Save changes?', self, filepath)
                
                if result:
                    saved = self._auto_save()
                    
                    if not saved:
                        return
                    
                if result == None:
                    return
        
        self.data_class.open()
        
    def _import_file(self):

        if not vtool.util_file.is_file(self.data_class.get_file()):
            vtool.qt_ui.warning('No data to import. Please save once.', self)
            return
        self.data_class.import_data()
        
    def _reference_file(self):
        
        if not vtool.util_file.is_file(self.data_class.get_file()):
            vtool.qt_ui.warning('No data to reference. Please save once.', self)
            return
        self.data_class.maya_reference_data()
        
        
class MayaHistoryFileWidget(vtool.qt_ui.HistoryFileWidget):
    def _build_widgets(self):
        
        super(MayaHistoryFileWidget, self)._build_widgets()
        
        import_button = qt.QPushButton('Import')
        import_button.setMaximumWidth(100)
        self.button_layout.addWidget(import_button)
        
        import_button.clicked.connect(self._import_version)
        
        reference_button = qt.QPushButton('Reference')
        reference_button.setMaximumWidth(100)
        self.button_layout.addWidget(reference_button)
        
        reference_button.clicked.connect(self._reference_version)
        
    def _open_version(self):
        
        items = self.version_list.selectedItems()
        
        item = None
        if items:
            item = items[0]
        
        if not item:
            vtool.util.warning('No version selected')
            return
        
        version = int(item.text(0))
        
        version_tool = vtool.util_file.VersionFile(self.directory)
        version_file = version_tool.get_version_path(version)
        
        maya_file = vtool.data.MayaFileData()
        maya_file.open(version_file)
        
    def _import_version(self):
        items = self.version_list.selectedItems()
        
        item = None
        if items:
            item = items[0]
        if not item:
            vtool.util.warning('No version selected')
            return
        
        version = int(item.text(0))
        
        version_tool = vtool.util_file.VersionFile(self.directory)
        version_file = version_tool.get_version_path(version)
        
        maya_file = vtool.data.MayaFileData()
        maya_file.import_data(version_file)
        
    def _reference_version(self):
        items = self.version_list.selectedItems()
        
        item = None
        if items:
            item = items[0]
        if not item:
            vtool.util.warning('No version selected')
            return
                            
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
        
        self.main_layout.setAlignment(qt.QtCore.Qt.AlignBottom)
    
    def _define_main_tab_name(self):
        return 'BUILD'
    
    def _define_data_class(self):
        return self.data_class_type
    
    def _define_save_widget(self):
        return ProcessSaveFileWidget()
    
    def update_data(self, data_directory):
        
        log.debug('Update build data folder')
        
        data_folder = vtool.data.DataFolder('build', data_directory)
        
        data_type = data_folder.get_data_type()
        
        if data_type == 'maya.ascii':
            self.set_data_type(self.ascii_data)
        if data_type == 'maya.binary':
            self.set_data_type(self.binary_data)
        if data_type == None:
            data_folder.set_data_type('maya.ascii')
            self.set_data_type(self.ascii_data)
        
        log.debug('Finished updating build data folder')
        
    def set_data_type(self, data_class):
        
        self.data_class_type = data_class
        self.data_class = data_class
        
        self.save_widget.set_data_class(data_class)
    
    
class ProcessSaveFileWidget(MayaSaveFileWidget):
    
    def _build_widgets(self):
        
        save_button = self._create_button('Save')
        save_button.setMinimumWidth(vtool.qt_ui._save_button_minimum)
        open_button = self._create_button('Open')
        open_button.setMinimumWidth(100)
        save_button.clicked.connect( self._save_file )
        open_button.clicked.connect( self._open_file )
        
        self.main_layout.setAlignment(qt.QtCore.Qt.AlignLeft)
        self.main_layout.addWidget(save_button)
        self.main_layout.addWidget(open_button)

data_name_map = {'maya.binary': 'Binary File',
                 'maya.ascii' : 'Ascii File',
                 'maya.shotgun' : 'Shotgun Link',
                 'maya.control_cvs' : 'Control Cv Positions',
                 'maya.control_colors' : 'Control Colors',
                 'maya.skin_weights' : 'Weights Skin Cluster',
                 'maya.deform_weights' : 'Weights Deformer',
                 'maya.blend_weights' : 'Weights Blendshape',
                 'maya.shaders' : 'Shaders',
                 'maya.attributes' : 'Attributes',
                 'maya.control_values' : 'Control Values',
                 'maya.pose' : 'Correctives',
                 'maya.animation' : 'Keyframes',
                 'maya.control_animation' : 'Keyframes Control',
                 'maya.control_rotateorder' : 'Control RotateOrder'
                 }

file_widgets = { 'maya.binary' : MayaBinaryFileWidget,
                 'maya.ascii' : MayaAsciiFileWidget,
                 'maya.shotgun' : MayaShotgunLinkWidget,
                 'maya.control_cvs' : ControlCvFileWidget,
                 'maya.control_colors' : ControlColorFileWidget,
                 'maya.control_rotateorder' : MayaControlRotateOrderFileWidget,
                 'maya.skin_weights' : SkinWeightFileWidget,
                 'maya.deform_weights' : DeformerWeightFileWidget,
                 'maya.blend_weights' : BlendShapeWeightFileWidget,
                 'maya.atom' :  AtomFileWidget,
                 'maya.shaders' : MayaShadersFileWidget,
                 'maya.attributes' : MayaAttributesFileWidget,
                 'maya.control_values' : MayaControlAttributesFileWidget,
                 'maya.pose' : PoseFileWidget,
                 'maya.animation': AnimationFileWidget,
                 'maya.control_animation': ControlAnimationFileWidget}

