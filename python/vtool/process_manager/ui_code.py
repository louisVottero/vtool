# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

import subprocess

import vtool.qt_ui
import vtool.util_file
import vtool.util

#vtool.util.activate_profiler()

import ui_data
import process

from vtool import qt_ui
from vtool import util_file

if vtool.qt_ui.is_pyqt():
    from PyQt4 import QtGui, QtCore, Qt, uic
if vtool.qt_ui.is_pyside():
    from PySide import QtCore, QtGui
    
class CodeProcessWidget(vtool.qt_ui.DirectoryWidget):
    """
    The main widget for code editing.
    """
    
    def __init__(self):
        super(CodeProcessWidget, self).__init__()
        
        self.sizes = self.splitter.sizes()
    
    def _build_widgets(self):
        
        self.splitter = QtGui.QSplitter()
        self.main_layout.addWidget(self.splitter)
        
        self.code_widget = CodeWidget()
        self.script_widget = ScriptWidget()
        
        self.code_widget.collapse.connect(self._close_splitter)
        self.script_widget.script_open.connect(self._code_change)
        self.script_widget.script_open_external.connect(self._open_external)
        self.script_widget.script_focus.connect(self._script_focus)
        self.script_widget.script_rename.connect(self._script_rename)
        self.script_widget.script_remove.connect(self._script_remove)
        
        self.splitter.addWidget(self.script_widget)
        self.splitter.addWidget(self.code_widget)
        
        self.restrain_move = True
        self.skip_move = False
        
        width = self.splitter.width()
        self.splitter.moveSplitter(width, 1)
        
        self.splitter.splitterMoved.connect(self._splitter_moved)
        self.settings = None
                
    def _splitter_moved(self, pos, index):
        
        if self.restrain_move:
            if not self.skip_move:
                self.skip_move = True
                width = self.splitter.width()
                self.splitter.moveSplitter(width,1)
                return
                
            if self.skip_move:
                self.skip_move = False
                return
            
        self.sizes = self.splitter.sizes()
        
    def _define_main_layout(self):
        return QtGui.QVBoxLayout()
        
    def _close_splitter(self):
        
        if not self.code_widget.code_edit.has_tabs():
        
            self.code_widget.set_code_path(None)
            self.restrain_move = True
            width = self.splitter.width()
            self.splitter.moveSplitter(width,1)
        
    def _script_focus(self, code_path):
        
        self.code_widget.code_edit.show_window(code_path)
        
    def _code_change(self, code, open_in_window = False):
        
        if not code:
            
            self._close_splitter()
            
            return
        
        if not open_in_window:
            if self.restrain_move == True:
                self.restrain_move = False
                width = self.splitter.width()
                
                section = width/3
                
                self.splitter.setSizes([section, section])
            
        if not code:
            return
            
        process_tool = process.Process()
        process_tool.set_directory(self.directory)
        
        split_code = code.split('.')
        
        path = process_tool.get_code_folder(split_code[0])

        code_file = vtool.util_file.join_path(path, code)
        
        self.code_widget.set_code_path(code_file, open_in_window)
        
        if not open_in_window:
            if self.sizes[1] != 0:
                self.splitter.setSizes(self.sizes)
        
    def _open_external(self, code):

        if not code:
            return

        process_tool = process.Process()
        process_tool.set_directory(self.directory)
        
        split_code = code.split('.')
        
        path = process_tool.get_code_folder(split_code[0])

        code_file = vtool.util_file.join_path(path, code)
        
        external_editor = self.settings.get('external_editor')
        
        if external_editor:
            p = subprocess.Popen([external_editor, code_file])
        
        if not external_editor:
            util_file.open_browser(code_file)
             
    def _script_rename(self, old_filepath, filepath):
        
        self.code_widget.code_edit.rename_tab(old_filepath, filepath)
        
        self.code_widget.set_code_path(filepath)
        
    def _script_remove(self, filepath):
        
        self.code_widget.code_edit.close_tab(filepath)
        
        if not self.code_widget.code_edit.has_tabs():
            self._close_splitter()
         
    def set_directory(self, directory, sync_code = False):
        super(CodeProcessWidget, self).set_directory(directory)
        
        self.script_widget.set_directory(directory, sync_code)
        
        self._close_splitter()
        
    def set_code_directory(self, directory):
        self.code_directory = directory
        
    def reset_process_script_state(self):
        self.script_widget.reset_process_script_state()
        
    def set_process_script_state(self, directory, state):
        self.script_widget.set_process_script_state(directory, state)
        
    def refresh_manifest(self):
        self.script_widget.code_manifest_tree.refresh()
        
    def set_external_code_library(self, code_directory):
        self.script_widget.set_external_code_library(code_directory)
        
    def set_settings(self, settings):
        
        self.settings = settings
            
        
class CodeWidget(vtool.qt_ui.BasicWidget):
    
    collapse = vtool.qt_ui.create_signal()
    
    def __init__(self, parent= None):
        super(CodeWidget, self).__init__(parent)
        
        policy = self.sizePolicy()
        
        policy.setHorizontalPolicy(policy.Minimum)
        policy.setHorizontalStretch(2)
        
        self.setSizePolicy(policy)
               
        self.directory = None
        
        
    def _build_widgets(self):
        
        self.code_edit = vtool.qt_ui.CodeEditTabs()
        self.code_edit.hide()
        
        self.code_edit.tabChanged.connect(self._tab_changed)
        
        self.code_edit.no_tabs.connect(self._collapse)
        
        self.save_file = ui_data.ScriptFileWidget()       
        
        self.code_edit.save.connect( self._code_saved )
        self.code_edit.multi_save.connect(self._multi_save)
        
        self.main_layout.addWidget(self.code_edit, stretch = 1)
        self.main_layout.addWidget(self.save_file, stretch = 0)
        
        self.alt_layout = QtGui.QVBoxLayout()
        
        self.save_file.hide()
        
    def _tab_changed(self, widget):
        filepath = vtool.util_file.get_dirname(widget.filepath)
        
        
        
        self.save_file.set_directory(filepath)
        self.save_file.set_text_widget(widget.text_edit)
    
    def _collapse(self):
        self.collapse.emit()
        
    def _load_file_text(self, path, open_in_window):
        
        if not open_in_window:
            self.code_edit.add_tab(path)
            
        if open_in_window:
            self.code_edit.add_floating_tab(path)
                  
    def _code_saved(self, code_edit_widget):
        
        if not code_edit_widget:
            return
        
        filepath = vtool.util_file.get_dirname(code_edit_widget.filepath)
        
        self.save_file.set_directory(filepath)
        self.save_file.set_text_widget(code_edit_widget)
        
        self.save_file.save_widget._save()
        
    
        
    def _multi_save(self, widgets, note):
        
        if not widgets:
            return
            
        #comment = vtool.qt_ui.get_comment(self, '- %s -\nScripts not saved.\nSave scripts?' % note)
        
        #if comment == None:
        #    print 'no comment!!!!'
            #return
        comment = 'auto save'
        
        for widget in widgets:
                        
            self.save_file.set_text_widget(widget)
            
            folder_path = vtool.util_file.get_dirname(widget.filepath)
            
            self.save_file.set_directory(folder_path)
            self.save_file.save_widget._save(comment)
                    
    def set_code_path(self, path, open_in_window = False):
        
        if not path:
            self.save_file.hide()
            self.code_edit.hide()
            return
        
        folder_path = vtool.util_file.get_dirname(path)
        
        self.directory = path
        
        self.save_file.set_directory(folder_path)
        
        self._load_file_text(path, open_in_window)
        
        if path:
            self.save_file.show()
            self.code_edit.show()
            
        
class ScriptWidget(vtool.qt_ui.DirectoryWidget):
    
    script_open = vtool.qt_ui.create_signal(object, object)
    script_open_external = vtool.qt_ui.create_signal(object)
    script_focus = vtool.qt_ui.create_signal(object)
    script_rename = vtool.qt_ui.create_signal(object, object)
    script_remove = vtool.qt_ui.create_signal(object)
        
    def __init__(self):
        super(ScriptWidget, self).__init__()
        
        policy = self.sizePolicy()
        
        policy.setHorizontalPolicy(policy.Maximum)
        policy.setHorizontalStretch(0)
        
        self.setSizePolicy(policy)
        
        self.exteranl_code_libarary = None
        
    def _define_main_layout(self):
        return QtGui.QVBoxLayout()
        
    def _build_widgets(self):
        
        self.code_manifest_tree = CodeManifestTree()
        
        buttons_layout = QtGui.QHBoxLayout()
                
        self.code_manifest_tree.item_renamed.connect(self._rename)
        self.code_manifest_tree.script_open.connect(self._script_open)
        self.code_manifest_tree.script_open_external.connect(self._script_open_external)
        self.code_manifest_tree.script_focus.connect(self._script_focus)
        self.code_manifest_tree.item_removed.connect(self._remove_code)
                
        self.main_layout.addWidget(self.code_manifest_tree)
        
        self.main_layout.addLayout(buttons_layout)
    
        
    def _script_open(self, item, open_in_window):
        
        if self.code_manifest_tree.handle_selection_change:
        
            code_folder = self._get_current_code()
            self.script_open.emit(code_folder, open_in_window)
            
    def _script_open_external(self):
        
        if self.code_manifest_tree.handle_selection_change:
            code_folder = self._get_current_code()
            self.script_open_external.emit(code_folder)
    
    def _script_focus(self, code_name):
        
        if self.code_manifest_tree.handle_selection_change:
            
            code_folder = self._get_current_code()
            self.script_focus.emit(code_folder)
            
    def _get_current_code(self, item = None):
        
        if not item:
            item = self.code_manifest_tree.selectedItems()
            if item:
                item = item[0]
        
        if not item:
            return
        
        name = item.text(0)
        
        path = self.code_manifest_tree._get_item_path(item)
        
        if path:
            name = util_file.join_path(path, name)
        
        return name
        
    def _run_code(self):
        
        self.code_manifest_tree.run_current_item(self.exteranl_code_libarary)
            
    def _create_code(self):
        
        process_tool = process.Process()
        process_tool.set_directory(self.directory)
        
        code_path = process_tool.create_code('code', 'script.python', inc_name = True)
        
        name = vtool.util_file.get_basename(code_path)
        
        item = self.code_manifest_tree._add_item(name, False)
        
        self.code_manifest_tree.scrollToItem(item)
        
    def _create_import_code(self):
        
        process_tool = process.Process()
        process_tool.set_directory(self.directory)
        
        folders = process_tool.get_data_folders()
        
        picked = vtool.qt_ui.get_pick(folders, 'Pick the data to import.', self)
        
        process_tool.create_code('import_%s' % picked, import_data = picked)
        self.code_manifest_tree._add_item('import_%s.py' % picked, False)
        
    def _remove_code(self, filepath):
        
        self.script_remove.emit(filepath)
        
    def _rename(self, old_filepath, filepath):
        
        self.script_rename.emit(old_filepath, filepath)
        
        
    def set_directory(self, directory, sync_code = False):
        super(ScriptWidget, self).set_directory(directory)
        
        if not sync_code:
            if self.directory == self.last_directory:
                return
        
        self.code_manifest_tree.set_directory(directory)
        
    def reset_process_script_state(self):
        self.code_manifest_tree.reset_process_script_state()
        
    def set_process_script_state(self, directory, state):
        self.code_manifest_tree.set_process_script_state(directory, state)
        
    def set_external_code_library(self, code_directory):
        self.exteranl_code_libarary = code_directory
    

class CodeManifestTree(vtool.qt_ui.FileTreeWidget):
    
    item_renamed = vtool.qt_ui.create_signal(object, object)
    script_open = vtool.qt_ui.create_signal(object, object)
    script_open_external = vtool.qt_ui.create_signal()
    script_focus = vtool.qt_ui.create_signal(object)
    item_removed = vtool.qt_ui.create_signal(object)

    def __init__(self):
        
        super(CodeManifestTree, self).__init__()
        
        self.title_text_index = 0
        
        self.setSortingEnabled(False)
        
        #self.setIndentation(False)
        
        self.setBackgroundRole(QtGui.QPalette.Light)
        
        self.setSelectionMode(self.ExtendedSelection)
        
        self.setDragDropMode(self.InternalMove)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)  
        self.setDropIndicatorShown(True) 
        self.setAutoScroll(True)
        
        self.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.invisibleRootItem().setFlags(QtCore.Qt.ItemIsDropEnabled) 
        
        self.dragged_item = None
        self.handle_selection_change = True
        
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._item_menu)
        
        self.future_rename = False
        
        self.new_actions = []
        self.edit_actions = []
        
        self._create_context_menu()
        
        header = self.header()
        
        self.checkbox = QtGui.QCheckBox(header)
        self.checkbox.stateChanged.connect(self._set_all_checked)
        
        self.update_checkbox = True
        
        self.hierarchy = True
        #new
        self.dragged_item = None
        #new
        
        #if vtool.util.is_in_maya():
        
        #    self.setStyleSheet("QTreeView::indicator:unchecked { background:black; }"
        #                        "QTreeView::indicator:checked { background:white; }")
        
        
        #self.setStyleSheet("QTreeView::indicator:unchecked {image: url(icons/check_off.png);}"
        #                   "QTreeView::indicator:checked {image: url(icons/check_on.png);}")
        
        #self.setAutoFillBackground(False)
        #self.setAlternatingRowColors(False)
        
        self.allow_manifest_update = True
        
        if vtool.util.is_in_maya():
            palette = self.palette()
            
            palette.setColor(QtGui.QPalette.Base, QtGui.QColor(60,60,60,255) )
            palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(70,70,70,255) )
        
            self.setPalette(palette)
        
    def resizeEvent(self, event = None):
        super(CodeManifestTree, self).resizeEvent(event)
        
        self.checkbox.setGeometry(QtCore.QRect(3, 2, 16, 17))
        
    def mouseDoubleClickEvent(self, event):
        
        items = self.selectedItems()
        if items:
            item = items[0]
        
            self.script_open.emit(item, False)
    
    def mousePressEvent(self, event):
        
        
        self.handle_selection_change = True
        
        #new
        item = self.itemAt(event.pos())
        
        parent = self.invisibleRootItem()
        
        if item:
            if item.parent():
                parent = item.parent()
        
        self.drag_parent = parent
        
        self.dragged_item = item
        
        super(CodeManifestTree, self).mousePressEvent(event)
        #new
        #self.script_focus.emit( str(item.text(0)) )
    
    """
    def dragMoveEvent(self, event):
        super(CodeManifestTree, self).dragMoveEvent(event)    
        
        self.handle_selection_change = False
        
        self.dragged_item = self.currentItem()
    """
    
    def _get_entered_item(self, event):
        
        position = event.pos()
        entered_item = self.itemAt(position)
        
        if not entered_item:
            entered_item = self.invisibleRootItem()
            
        return entered_item
        
    
    def _insert_drop(self, event):
        print 'insert!'
        entered_item = self._get_entered_item(event)
        entered_parent = entered_item.parent()
        
        from_list = event.source()
            
        insert_inc = 0
        
        remove_items = []
        
        for item in from_list.selectedItems():
            
            
            
            children = item.takeChildren()
            
            filename = item.get_text()
            state = item.get_state()
            new_item = self._create_item(filename, state)
            
            for child in children:
                new_item.addChild(child)
            
            parent = item.parent()
            
            if not parent:
                parent = self.invisibleRootItem()
            
            remove_items.append([item, parent])
            
            insert_row = self.indexFromItem(entered_item, column=0).row()
            
            if self.dropIndicatorPosition == self.BelowItem:
                insert_row += 1
                insert_row = insert_row + insert_inc
                
            if not entered_parent:
                
                if insert_row == -1:
                    insert_row = self.topLevelItemCount()
                
                self.insertTopLevelItem(insert_row, new_item)
                
            if entered_parent:
                
                entered_parent.insertChild(insert_row, new_item)
                
            insert_inc += 1
            
        for item in remove_items:
            
            item[1].removeChild(item[0])
            
    def _add_drop(self, event):
        print 'add!'
        entered_item = self._get_entered_item(event)
        entered_parent = entered_item.parent()
        
        if not entered_parent:
            entered_parent = self.invisibleRootItem()
                
        from_list = event.source()
        
        remove_items = []
        
        for item in from_list.selectedItems():
            parent = item.parent()
            
            if not parent:
                parent = self.invisibleRootItem()
                
            remove_items.append([item, parent])
                
            children = item.takeChildren()
            
            old_path = self._get_item_path(item)
            
            
            name = item.get_text()
            
            state = item.get_state()
            
            entered_item.setExpanded(True)
            
            item = self._create_item(name, state)
            
            for child in children:
                item.addChild(child)
            
            entered_item.addChild(item)
            entered_item.setExpanded(True)
            
            
            
            name = name.split('.')[0]
            
            new_name = self._get_new_drop_name(item)
            
            print '##', new_name, name
            
            if new_name != name:
                
                basename = util_file.get_basename(new_name)
                item.set_text(basename + '.py')
            
            old_name = name
            
            if old_path:
                old_name = util_file.join_path(old_path, name)
            
            self._handle_item_reparent(old_name, new_name)
            
        for item in remove_items:
            
            item[1].removeChild(item[0])
            
    def _get_new_drop_name(self, item):
        
        name = item.get_text()
        name = name.split('.')[0]
        
        new_path = self._get_item_path(item)
        
        new_name = name
        
        if new_path:
            new_name = util_file.join_path(new_path, name)
        
        inc = vtool.util.get_last_number(new_name)
        
        while self._name_clash(new_name):
            
            inc += 1
            
            new_name = vtool.util.replace_last_number(new_name, str(inc)) 
            
            if inc >= 1000:
                return
            
        return new_name
            
    def _handle_item_reparent(self, old_name, new_name):
        
        if old_name == new_name:
            return
        
        process_tool = process.Process()
        process_tool.set_directory(self.directory)
        
        process_tool.rename_code(old_name, new_name)
        
    def _get_item_path(self, item):
        
        parent = item.parent()
        parent_path = ''
        
        while parent:
            
            parent_name = parent.text(0)
            
            split_name = parent_name.split('.')
            parent_name = split_name[0]
            
            if parent_path:
                parent_path = util_file.join_path(parent_name, parent_path)
                
            if not parent_path:
                parent_path = parent_name
                
            parent = parent.parent()
        
        return parent_path
            
    def dropEvent(self, event):
        print 'drop', '---------------------------------------'
        is_dropped = self.is_item_dropped(event, strict = True)
        
        #removing this lines triggers the new behavior that is still being developed
        if not self.hierarchy:
            is_dropped = False
        
        if not is_dropped:
            
            self._insert_drop(event)
        #new
        if is_dropped:
            
            self._add_drop(event)
        
        event.accept()    
        self._update_manifest()
        
    def _item_expanded(self, item):
        return
        #self._add_sub_items(item) 
        
        #self.resizeColumnToContents(self.title_text_index)
                
    def _set_all_checked(self, int):
        
        if not self.update_checkbox:
            return
        
        if int == 2:
            state = QtCore.Qt.Checked
        if int == 0:
            state = QtCore.Qt.Unchecked
        
        count = self.topLevelItemCount()
        
        for inc in range(0, count):
            item = self.topLevelItem(inc)
            
            item.setCheckState(0, state)
        
    def _create_context_menu(self):
        self.context_menu = QtGui.QMenu()
        
        new_python = self.context_menu.addAction('New Python Code')
        new_data_import = self.context_menu.addAction('New Data Import')
        
        self.new_actions = [new_python, new_data_import]
        
        self.context_menu.addSeparator()
        
        self.run_action = self.context_menu.addAction('Run')
        rename_action = self.context_menu.addAction(self.tr('Rename'))
        delete_action = self.context_menu.addAction('Delete')
        
        self.context_menu.addSeparator()
        new_window_action = self.context_menu.addAction('Open In New Window')
        external_window_action = self.context_menu.addAction('Open In External')
        browse_action = self.context_menu.addAction('Browse')
        refresh_action = self.context_menu.addAction('Refresh')
        
        self.edit_actions = [self.run_action, rename_action, delete_action]
        
        
        new_python.triggered.connect(self.create_python_code)
        new_data_import.triggered.connect(self.create_import_code)
        
        self.run_action.triggered.connect(self.run_current_item)
        rename_action.triggered.connect(self._activate_rename)
        delete_action.triggered.connect(self.remove_current_item)
        
        new_window_action.triggered.connect(self._open_in_new_window)
        external_window_action.triggered.connect(self._open_in_external)
        browse_action.triggered.connect(self._browse_to_code)
        refresh_action.triggered.connect(self._refresh_action)
    
    def _item_menu(self, position):
        
        items = self.selectedItems()
        
        item = None
                
        if items:
            item = items[0]
        
        if item:
            
            self._edit_actions_visible(True)
            
        if not item:
            
            self._edit_actions_visible(False)
            
        if len(items) > 1:
            self._edit_actions_visible(False)
            self.run_action.setVisible(True)
            
        self.context_menu.exec_(self.viewport().mapToGlobal(position))
            
    def _edit_actions_visible(self, bool_value):
        
        for action in self.edit_actions:
            
            action.setVisible(bool_value)
        
    def _refresh_action(self):
        self.refresh(sync = True)
        
    def _activate_rename(self):
        
        items = self.selectedItems()
        if not items:
            return
        
        item = items[0]
        
        self.old_name = str(item.get_text())
        
        new_name = qt_ui.get_new_name('New Name', self, self.old_name)
        
        if not new_name:
            return
        
        self._rename_item(item, new_name)
        
    def _open_in_new_window(self):
        
        items = self.selectedItems()
        item = items[0]
        
        self.script_open.emit(item, True)
        
    def _open_in_external(self):
        
        self.script_open_external.emit()
        
    def _browse_to_code(self):
        items = self.selectedItems()
        
        process_tool = process.Process()
        process_tool.set_directory(self.directory)
        
        if items:
        
            item = items[0]
    
            code_name = item.get_text()
            code_name = code_name.split('.')[0]
            
            code_path = process_tool.get_code_folder(code_name)
            
            util_file.open_browser(code_path)
            
        if not items:
            
            code_path = process_tool.get_code_path()
            
            util_file.open_browser(code_path)
            
    def _define_header(self):
        return ['       Manifest']
    
    def _edit_finish(self, item):
        super(CodeManifestTree, self)._edit_finish(item)
        
        if type(item) == int:
            
            return
        
        name = str(item.get_text)
        
        if name == 'manifest':
            item.set_text(self.old_name)
            return
        
        if name.find('.'):
            split_name = name.split('.')
            name = split_name[0]
        
        self._rename_item(item, name)
        
    def _name_clash(self, name):
        
        process_tool = process.Process()
        process_tool.set_directory(self.directory)
        
        folders = process_tool.get_code_folders()
        
        for folder in folders:
            
            other_name = folder
            
            if name == other_name:
                return True
            
        return False
        
        """
        for inc in range(0, self.topLevelItemCount()):    
            
            other_name = self.topLevelItem(inc).get_text()
            other_name = str(other_name)
            
            if other_name.find('.'):
                other_name = other_name.split('.')
                other_name = other_name[0]
            
            if name == other_name:
                return True
            
        return False
        """
    def _rename_item(self, item, new_name):
        
        print 'rename item', new_name
        
        new_name = str(new_name)
        
        path = self._get_item_path(item)
        
        if new_name.find('.'):
            new_name = new_name.split('.')
            new_name = new_name[0]
            
            if path:
                new_name = util_file.join_path(path, new_name)
        
        if self.old_name.find('.'):
            split_old_name = self.old_name.split('.')
            old_name = split_old_name[0]
        
            if path:
                old_name = util_file.join_path(path, old_name)

        #pre_new_name = new_name
        inc = vtool.util.get_last_number(new_name)
        
        print 'last number!', inc
        
        while self._name_clash(new_name):
            
            inc += 1
            
            new_name = vtool.util.replace_last_number(new_name, str(inc))
            
            if inc >= 1000:
                return
           
        if old_name == new_name:
            return
         
        process_tool = process.Process()
        process_tool.set_directory(self.directory)
        
        old_filepath = process_tool.get_code_file(old_name)
        print 'renaming item!!!',  old_name, new_name
        file_name = process_tool.rename_code(old_name, new_name)
                
        new_file_name = file_name.split('.')[0]
        
        print 'after rename!', file_name
        
        filepath = process_tool.get_code_file(new_file_name)
        
        item.set_text(util_file.get_basename(file_name))
        
        self.item_renamed.emit(old_filepath, filepath)
        
        self._update_manifest()
    
    def _define_item(self):
        return ManifestItem()
        
    def _setup_item(self, item, state):
        
        if not state:
            item.setCheckState(0, QtCore.Qt.Unchecked)
        if state:
            item.setCheckState(0, QtCore.Qt.Checked)
        
        if not self.hierarchy:
            #dont remove this comment.  You can make an item not be drop enabled by giving it every flag except drop enabled.
            item.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsEditable|QtCore.Qt.ItemIsEnabled|QtCore.Qt.ItemIsDragEnabled|QtCore.Qt.ItemIsUserCheckable)
        
        if self.hierarchy:
            #this allows for dropping
            item.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsEditable|QtCore.Qt.ItemIsEnabled|QtCore.Qt.ItemIsDragEnabled|QtCore.Qt.ItemIsUserCheckable|QtCore.Qt.ItemIsDropEnabled)
            #item.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsEditable|QtCore.Qt.ItemIsEnabled|QtCore.Qt.ItemIsDragEnabled|QtCore.Qt.ItemIsUserCheckable|QtCore.Qt.ItemIsDropEnabled)
        
        #setData in the item is an issue. If this isn't happening then the manifest will update every time the check state changes by the program.
        #this avoids it updating while it is being set by the program.
        if hasattr(item, 'handle_manifest'):
            item.handle_manifest = True
        #item.tree = self
        
        
    def _create_item(self, filename, state = False):
        
        item = self._define_item()
        
        item.set_text(filename)
        
        self._setup_item(item, state)
        
        return item
        
    def _add_item(self, filename, state):
        
        if filename.count('/') > 0:
            basename = util_file.get_basename(filename)
            
            item = super(CodeManifestTree, self)._add_item(basename, parent = False)
            
        if filename.count('/') == 0:
            item = super(CodeManifestTree,self)._add_item(filename)
        
        self._setup_item(item, state)
        
        return item
    
    def _add_items(self, files, item = None):
        
        scripts, states, parents = files
        
        script_count = len(scripts)
        
        found_false = False
        
        built_parents = {}
        
        for inc in range(0, script_count):
            
            script_name = scripts[inc].split('.')[0]
            
            
            
            item = self._add_item(scripts[inc], states[inc])
            
            if parents.has_key(script_name):
                built_parents[script_name] = item
            
            dirname = util_file.get_dirname(scripts[inc])
            
            if parents.has_key(dirname) and built_parents.has_key(dirname):
                
                current_parent = built_parents[dirname]
                
                current_parent.addChild(item)
            
            if not states[inc]:
                found_false = True
            
        self.update_checkbox = False
            
        if not found_false:
            self.checkbox.setChecked(True)
        if found_false:
            self.checkbox.setChecked(False)
            
        self.update_checkbox = True
        
    def _add_sub_items(self, item):
        
        item_path = self._get_item_path(item)
        
        process_tool = process.Process()
        process_tool.set_directory(self.directory)
        
        
        
    
    def _get_files(self, path = None):
        
        process_tool = process.Process()
        process_tool.set_directory(self.directory)
        
        scripts, states = process_tool.get_manifest()
        
        code_folders = process_tool.get_code_folders()
        
        found_scripts = []
        found_states = []
        parents = {}
        
        for inc in range(0, len(scripts)):
            
            name = scripts[inc].split('.')[0]
            
            if not name in code_folders:
                continue
            
            code_path = process_tool.get_code_file(name)
            
            if not code_path or not util_file.is_file(code_path):
                continue
            
            if name.count('/') > 0:
                dirname = util_file.get_dirname(name)
                parents[dirname] = scripts[inc]
            
            found_scripts.append(scripts[inc])
            found_states.append(states[inc])
                   
        return [found_scripts, found_states, parents]

    def _get_item_by_name(self, name):
        item_count = self.topLevelItemCount()
        
        for inc in range(0, item_count):
            
            item = self.topLevelItem(inc)
            
            if item.get_text() == name:
                return item

    def _get_all_items(self):
        
        item_count = self.topLevelItemCount()    
        items = []
        
        for inc in range(0, item_count):
            
            item = self.topLevelItem(inc)
            
            ancestors = self._get_ancestors(item)
            
            items.append(item)
            
            if ancestors:
                items += ancestors
                
        return items
                
    def _get_ancestors(self, item):
        
        child_count = item.childCount()
        
        items = []
        
        for inc in range(0, child_count):
            
            child = item.child(inc)
            
            children = self._get_ancestors(child)
            
            items.append(child)
            if children:
                items += children
        
        return items

    def _update_manifest(self):
        
        if not self.allow_manifest_update:
            return
        
        print 'update manifest -----------------------------------------------'
        process_tool = process.Process()
        process_tool.set_directory(self.directory)
        
        scripts = []
        states = []
        
        #Could not user item iterator because it updates setData which updates the manifest, 
        #which causes the manifest to be updated too much.
        #it = QtGui.QTreeWidgetItemIterator(self)
        #while it:
            #item = it.value()
            #items.append(item)
        

        items = self._get_all_items()
        
        for item in items:
            
            name = item.get_text()
            path = self._get_item_path(item)
            
            if path:
                name = util_file.join_path(path, name)
            
            state = item.checkState(0)
            if state == 0:
                state = False
            
            if state == 2:
                state = True
            
            print name,state
                
            scripts.append(name)
            states.append(state)
            
        process_tool.set_manifest(scripts, states)
        
    def _sync_manifest(self):
        print 'sync manifest ------------------------------'
        process_tool = process.Process()
        process_tool.set_directory(self.directory)
        
        process_tool.sync_manifest()
        
    def _run_item(self, item, process_tool):
        
        item.set_state(2)
        
        name = item.get_text()
        name = name.split('.')
        name = name[0]
        
        path = self._get_item_path(item)
        
        if path:
            name = util_file.join_path(path, name)
        
        code_file = process_tool.get_code_file(name)
        
        status = process_tool.run_script(code_file, False)
        
        if status == 'Success':
            item.set_state(1)
        if not status == 'Success':
            item.set_state(0)
            
            vtool.util.show(status) 
            
        self.scrollToItem(item)       

    def refresh(self, sync = False):
        
        if sync:
            self._sync_manifest()
        
        self.allow_manifest_update = False
        super(CodeManifestTree, self).refresh()
        self.allow_manifest_update = True

    def reset_process_script_state(self):
        item_count = self.topLevelItemCount()
        
        for inc in range(0, item_count):
            item = self.topLevelItem(inc)
            item.set_state(-1)

    def set_process_script_state(self, directory, state):
        
        script_name = vtool.util_file.get_basename(directory)
        
        item = self._get_item_by_name(script_name)
        
        if not util_file.is_file(directory):
            
            index = self.indexFromItem(item)
            self.takeTopLevelItem(index.row())
            return


        item.set_state(state)
        
        if state > -1:
            self.scrollToItem(item)
        
        
    def create_python_code(self):
        process_tool = process.Process()
        process_tool.set_directory(self.directory)
        
        code_path = process_tool.create_code('code', 'script.python', inc_name = True)
        
        name = vtool.util_file.get_basename(code_path)
        
        item = self._add_item(name, False)
        
        self.scrollToItem(item)
        self.setItemSelected(item, True)
        
    def create_import_code(self):
        process_tool = process.Process()
        process_tool.set_directory(self.directory)
        
        folders = process_tool.get_data_folders()
        
        picked = vtool.qt_ui.get_pick(folders, 'Pick the data to import.', self)
        
        if not picked:
            return
        
        process_tool.create_code('import_%s' % picked, import_data = picked)
        self._add_item('import_%s.py' % picked, False)
        
    def run_current_item(self, external_code_library = None):
        
        print 'run current'
        
        items = self.selectedItems()
        
        for item in items:
            print item.text(0)
        
        """
        item_count = self.topLevelItemCount()
        for inc in range(0, item_count):
            top_item = self.topLevelItem(inc)
            top_item.set_state(-1)
        """
        
        if len(items) > 1:
            
            if vtool.util.is_in_maya():
                
                value = qt_ui.get_permission('Start a new scene?', self)
                if value:
                    
                    import maya.cmds as cmds
                    
                    cmds.file(new = True, f = True)
    
                if value == None:
                    return

        process_tool = process.Process()
        process_tool.set_directory(self.directory)
        
        if external_code_library:
            process_tool.set_external_code_library(external_code_library)
            
        for item in items:
            self._run_item(item, process_tool)
        

        
    def remove_current_item(self):
        
        items = self.selectedItems()
        item = items[0]
        
        name = item.get_text()
        name = name.split('.')
        name = name[0]
        
        path = self._get_item_path(item)
        
        if path:
            name = util_file.join_path(path, name)
        
        delete_state = vtool.qt_ui.get_permission('Delete %s?' % name)
        
        process_tool = process.Process()
        process_tool.set_directory(self.directory)
        
        filepath = process_tool.get_code_file(name)
        
        if delete_state:
        
            index = self.indexFromItem(item)
            
            parent = item.parent()
            
            if parent:
                parent.removeChild(item)
            if not parent:
                self.takeTopLevelItem(index.row())
            
            process_tool.delete_code(name)
            
            self._update_manifest()
                
        self.item_removed.emit(filepath)
        
class ManifestItem(vtool.qt_ui.TreeWidgetItem):
    
    
    
    def __init__(self):
        
        self.handle_manifest = False
        
        super(ManifestItem, self).__init__()
        
        self.setSizeHint(0, QtCore.QSize(10, 30))
        
        #if vtool.util.is_in_maya():
        #    brush = QtGui.QBrush(QtGui.QColor(100,100,100))
        #    self.setBackground(0, brush)
        
        maya_version = vtool.util.get_maya_version()
        
        if maya_version > 2015 or maya_version == 0:
            self.status_icon = self._square_fill_icon(0.6, 0.6, 0.6)
            
        if maya_version < 2016 and maya_version != 0:
            self.status_icon = self._radial_fill_icon(0.6, 0.6, 0.6)
        
        self.setCheckState(0, QtCore.Qt.Unchecked)
        
        
        
    
    def _square_fill_icon(self, r,g,b):
        
        pixmap = QtGui.QPixmap(20, 20)
        pixmap.fill(QtGui.QColor.fromRgbF(r, g, b, 1))
        
        painter = QtGui.QPainter(pixmap)
        painter.fillRect(0, 0, 100, 100, QtGui.QColor.fromRgbF(r, g, b, 1))
        painter.end()
        
        icon = QtGui.QIcon(pixmap)
        
        self.setIcon(0, icon)
        
    
    def _radial_fill_icon(self, r,g,b):
        
        self._square_fill_icon(r, g, b)
        
        
        pixmap = QtGui.QPixmap(20, 20)
        pixmap.fill(QtCore.Qt.transparent)
        gradient = QtGui.QRadialGradient(10, 10, 10)
        gradient.setColorAt(0, QtGui.QColor.fromRgbF(r, g, b, 1))
        gradient.setColorAt(1, QtGui.QColor.fromRgbF(0, 0, 0, 0))
        
        painter = QtGui.QPainter(pixmap)
        painter.fillRect(0, 0, 100, 100, gradient)
        painter.end()
        
        icon = QtGui.QIcon(pixmap)
        
        self.setIcon(0, icon)
        
    def setData(self, column, role, value):
        super(ManifestItem, self).setData(column, role, value)
        
        if role == QtCore.Qt.CheckStateRole:
            
            if self.handle_manifest:
                tree = self.treeWidget()
            
                tree._update_manifest()
            
            #if hasattr(self, 'tree'):
            #    self.tree._update_manifest()
                     
    def set_state(self, state):
        
        
        maya_version = vtool.util.get_maya_version()
        
        
        if maya_version < 2016 and maya_version != 0:
            
            if state == 0:
                self._radial_fill_icon(1.0, 0.0, 0.0)    
            if state == 1:
                self._radial_fill_icon(0.0, 1.0, 0.0)
            if state == -1:
                self._radial_fill_icon(0.6, 0.6, 0.6)
            if state == 2:
                self._radial_fill_icon(1.0, 1.0, 0.0)
        
        if maya_version > 2015 or maya_version == 0:
    
            if state == 0:
                self._square_fill_icon(1.0, 0.0, 0.0)    
            if state == 1:
                self._square_fill_icon(0.0, 1.0, 0.0)
            if state == -1:
                self._square_fill_icon(0.6, 0.6, 0.6)
            if state == 2:
                self._square_fill_icon(1.0, 1.0, 0.0)
    
    def get_state(self):
        return self.checkState(0)
        
    
    def set_text(self, text):
        text = '   ' + text
        
        super(ManifestItem, self).setText(0, text)
        
    def get_text(self):
        text_value = super(ManifestItem, self).text(0)
        return str(text_value).strip()
    
    def text(self, index):
        
        return self.get_text()
    
    def setText(self, index, text):
        return self.set_text(text)
    
class ManifestItemWidget(vtool.qt_ui.TreeItemWidget):
    
    # no longer in use.
    
    def __init__(self):
        super(ManifestItemWidget, self).__init__()
        
        self.setSizePolicy(QtGui.QSizePolicy(10, 40))
    

    
    def _build_widgets(self):
        
        #check_box.setIcon(QtGui.QIcon())
        self.status_icon = QtGui.QLabel()
        self.status_icon.setMaximumSize(20,20)
        self._radial_fill_icon(0.6, 0.6, 0.6)
        #check_box.setIcon(QtGui.QIcon(pixmap))
        
        self.check_box = QtGui.QCheckBox()
        self.check_box.setCheckState(QtCore.Qt.Checked)
        
        #self.palette = QtGui.QPalette()
        #self.palette.setColor(self.palette.Background, QtGui.QColor(.5,.5,.5))
        
        #self.check_box.setPalette(self.palette)
        
        #self.label = QtGui.QLabel()
        #self.label = QtGui.QLineEdit()
        #self.label.setReadOnly(True)
        
        
        self.main_layout.addWidget(self.status_icon)
        self.main_layout.addSpacing(5)
        self.main_layout.addWidget(self.check_box)
        self.main_layout.addSpacing(5)
        #self.main_layout.addWidget(self.label)
        self.main_layout.setAlignment(QtCore.Qt.AlignLeft)
        
    def set_text(self, text):
        pass
        #self.label.setText(text)
        
    def set_state(self, state):
        
        if state == 0:
            self._radial_fill_icon(1.0, 0.0, 0.0)    
        if state == 1:
            self._radial_fill_icon(0.0, 1.0, 0.0)
        if state == -1:
            self._radial_fill_icon(0.6, 0.6, 0.6)
        if state == 2:
            self._radial_fill_icon(0.0, 1.0, 1.0) 
              
    def get_check_state(self):
        return self.check_box.isChecked()
    
    def set_check_state(self, bool_value):
        
        if bool_value:
            self.check_box.setCheckState(QtCore.Qt.Checked)
        if not bool_value:
            self.check_box.setCheckState(QtCore.Qt.Unchecked)
        
    
