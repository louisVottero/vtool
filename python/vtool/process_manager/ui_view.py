# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

import string

from vtool import util
from vtool import util_file
from vtool import qt_ui, qt

import process




class ViewProcessWidget(qt_ui.EditFileTreeWidget):
    
    description = 'Process'
    
    copy_done = qt_ui.create_signal()
    
    def __init__(self):
        

            
        self.settings = None
        
        super(ViewProcessWidget, self).__init__()
        
        policy = self.sizePolicy()
        
        #policy.setHorizontalPolicy(policy.Maximum)
        policy.setHorizontalStretch(0)
        self.setSizePolicy(policy)
        
        #self.setMinimumWidth(200)
        
        
    def _define_tree_widget(self):
        return ProcessTreeWidget()
    
    def _define_manager_widget(self):
        
        tree_manager = ManageProcessTreeWidget()
        
        tree_manager.copy_done.connect(self._copy_done)
        
        return tree_manager
    
    def _copy_done(self):
        self.copy_done.emit()
    
    def _item_selection_changed(self):
        
        name, item = super(ViewProcessWidget, self)._item_selection_changed()
        
        if not name:
            return
                
        name = self.tree_widget._get_parent_path(item)
        
        
        self.manager_widget.copy_widget.set_other_process(name, self.directory)
    
    def get_current_process(self):
        return self.tree_widget.current_name
    
    def clear_sub_path_filter(self):
        self.filter_widget.clear_sub_path_filter()
        
    def set_settings(self, settings):
        self.settings = settings
        
        self.tree_widget.set_settings(settings)
         
class ManageProcessTreeWidget(qt_ui.ManageTreeWidget):
    
    copy_done = qt_ui.create_signal()
    
    def __init__(self):
        super(ManageProcessTreeWidget, self).__init__()
        
        self.directory = None
        
    def _define_main_layout(self):
        return qt.QVBoxLayout()
    
    def _build_widgets(self):
        
        copy_widget = CopyWidget()
        self.copy_widget = copy_widget

    def _add_branch(self):
        
        self.tree_widget.add_process('')
      
    def _add_top_branch(self):
        
        self.tree_widget.add_process(None)
        
    def _copy_match(self, process_name = None, directory = None):
        
        copy_widget = self.copy_widget 
                
        copy_widget.pasted.connect(self._copy_done)
        copy_widget.canceled.connect(self._copy_done)
        
        if not process_name:
        
            current_process = self.get_current_process()
            
            if not current_process:
                return
            
        if process_name:
            current_process = process_name
        
        if not directory:
            directory = self.directory
        
        copy_widget.show()
        copy_widget.set_process(current_process, directory)
        
        self.setFocus()
        
        if not process_name:
            #then it must be using the found current process
            items = self.tree_widget.selectedItems()
            self.tree_widget.scrollToItem(items[0])
        
        self.copy_done.emit()
        
    def _copy_done(self):
        
        self.copy_done.emit()
        
    def copy_match(self, process_name, directory):
        
        self._copy_match(process_name, directory)
        
        target_process = None
        
        items = self.tree_widget.selectedItems()
        if items:
            target_item = items[0]
            target_process = target_item.get_process()            
        if not items:
            target_item = None
        
        if not target_process:
            return
                
        name = target_process.get_name()
        directory = target_process.directory
        
        self.copy_widget.set_other_process(name, directory)
        
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
        self.tree_widget.copy_special_process.connect(self._copy_match)
        self.tree_widget.copy_process.connect(self._copy_done)
        
        
class ProcessTreeWidget(qt_ui.FileTreeWidget):
    
    new_process = qt_ui.create_signal()
    new_top_process = qt_ui.create_signal()  
    copy_process = qt_ui.create_signal()
    copy_special_process = qt_ui.create_signal()
    process_deleted = qt_ui.create_signal()
    item_renamed = qt_ui.create_signal(object)
    show_options = qt_ui.create_signal()
    show_templates = qt_ui.create_signal()
    selection_changed = qt_ui.create_signal()
    
    def __init__(self):
        
        self.settings = None
        
        super(ProcessTreeWidget, self).__init__()
        
        
        self.text_edit = False
        
        self.setDragDropMode(self.InternalMove)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)   
        self.setDropIndicatorShown(True) 
        
        
        self.setTabKeyNavigation(True)
        self.setHeaderHidden(True)
        self.activation_fix = True
        
        self.setContextMenuPolicy(qt.QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._item_menu)
        
        self._create_context_menu()
        self.paste_item = None
                
                
        self.setSelectionBehavior(self.SelectItems)
        
        self.dragged_item = None
        
        #self.setMinimumWidth(00)
        
        self.setAlternatingRowColors(True)
        
        self.current_folder = None
        
        if util.is_in_maya():
            
            directory = util_file.get_vetala_directory()
            icon_on = util_file.join_path(directory, 'icons/plus.png')
            icon_off = util_file.join_path(directory, 'icons/minus_alt.png')
            
            icon_folder = util_file.join_path(directory, 'icons/folder.png')
            icon_folder_open = util_file.join_path(directory, 'icons/folder_open.png')
            
            
            lines = 'QTreeView::indicator:unchecked {image: url(%s);}' % icon_off
            lines += ' QTreeView::indicator:checked {image: url(%s);}' % icon_on
            
            #lines += ' QTreeView::branch:open {image: url(%s);}' % icon_folder_open
            #lines += ' QTreeView::branch:closed:has-children {image: url(%s);}' % icon_folder
            
            #lines += ' QTreeWidget::branch:closed:has-children:has-siblings, QTreeWidget::branch:closed:has-children:!has-siblings {image: url(%s);}' % icon_folder
            #lines += ' QTreeWidget::branch:opened:has-children:has-siblings, QTreeWidget::branch:opened:has-children:!has-siblings {image: url(%s);}' % icon_folder_open
            
            self.setStyleSheet( lines)
    """
    def drawRow(self, painter, option, index):
        
        if util.is_in_maya():
            brush = qt.QBrush( qt.QColor(70,70,70))
            painter.fillRect( option.rect, brush)
        
        #painter.restore()
        
        super(ProcessTreeWidget, self).drawRow(painter, option, index)
    """
    def dropEvent(self, event):
        
        directory = self.directory
        
        position = event.pos()
        index = self.indexAt(position)
        
        entered_item = self.itemAt(position)
        entered_name = None
        
        if entered_item:
            
            directory = entered_item.directory
            entered_name = entered_item.get_name()
        
        if not entered_item:
            entered_item = self.invisibleRootItem()
            entered_name = None
        
        is_dropped = self.is_item_dropped(event)
            
        super(ProcessTreeWidget, self).dropEvent(event)
        
        if not is_dropped:
            if entered_item:
                
                if entered_item.parent():
                    parent_item = entered_item.parent()
                    
                if not entered_item.parent():
                    parent_item = self.invisibleRootItem()
                    
                if not self.drag_parent is parent_item:
                    
                    index = entered_item.indexOfChild(self.dragged_item)
                    child = entered_item.takeChild(index)
                    parent_item.addChild(child)
                    
                    entered_item = parent_item
                    
                    if parent_item is self.invisibleRootItem():
                        entered_name = None
                    if not parent_item is self.invisibleRootItem():
                        entered_name = entered_item.get_name()
                        
        if entered_item:
            entered_item.setExpanded(True)

            entered_item.addChild(self.dragged_item)

        self.dragged_item.setDisabled(True)
        
        if entered_item is self.drag_parent:
            self.dragged_item.setDisabled(False)
            return
        
        if entered_name:
            message = 'Parent %s under %s?' % (self.dragged_item.get_name(), entered_name)
        if not entered_name:
            message = 'Unparent %s?' % self.dragged_item.get_name()
        
        move_result = qt_ui.get_permission( message , self)
        
        if not move_result:
            entered_item.removeChild(self.dragged_item)
            if self.drag_parent:
                self.drag_parent.addChild(self.dragged_item)
            self.dragged_item.setDisabled(False)
            return
            
        self.dragged_item.setDisabled(False)
        
        old_directory = self.dragged_item.directory
        old_name_full = self.dragged_item.get_name()
        old_name = util_file.get_basename(old_name_full)
        
        old_path = self.dragged_item.get_path()
        
        self.dragged_item.set_directory(directory)
        
        new_name = self._inc_name(self.dragged_item, old_name)
        
        self.dragged_item.setText(0, new_name)
        if entered_name:
            new_name = util_file.join_path(entered_name, new_name)
            
        self.dragged_item.set_name(new_name)
        
        new_path = util_file.join_path(directory, new_name)
        
        move_worked = util_file.move(old_path, new_path)

        if not move_worked:
            self.dragged_item.set_name(old_name_full)
            old_name = util_file.get_basename(old_name_full)
            self.dragged_item.setText(0, old_name)
            self.dragged_item.set_directory(old_directory)
            
            entered_item.removeChild(self.dragged_item)
            if self.drag_parent:
                self.drag_parent.addChild(self.dragged_item)                
    
    def mouseDoubleClickEvent(self, event):
        
        position = event.pos()
        index = self.indexAt(position)
        
        self.doubleClicked.emit(index)
    
    def mouseMoveEvent(self, event):
        model_index =  self.indexAt(event.pos())
        
        item = self.itemAt(event.pos())
        
        if not item or model_index.column() == 1:
            self.clearSelection()
        
        if event.button() == qt.QtCore.Qt.RightButton:
            return
        
        if model_index.column() == 0 and item:
            super(ProcessTreeWidget, self).mouseMoveEvent(event)
        
    def mousePressEvent(self, event):
        
        item = self.itemAt(event.pos())
        
        parent = self.invisibleRootItem()
        
        if item:
            if item.parent():
                parent = item.parent()
        
        self.drag_parent = parent
        
        self.dragged_item = item
        
        super(ProcessTreeWidget, self).mousePressEvent(event)

    def _item_menu(self, position):
        
        self.current_folder = None
        
        item = self.itemAt(position)
            
        if item and not item.is_folder():
            self.new_process_action.setVisible(True)
            self.new_top_level_action.setVisible(True)
            self.rename_action.setVisible(True)
            self.copy_action.setVisible(True)
            self.copy_special_action.setVisible(True)
            self.remove_action.setVisible(True)
            self.show_options_action.setVisible(True)
            self.convert_folder.setVisible(False)
        
        if item and item.is_folder():
            self.current_folder = item
            self.convert_folder.setVisible(True)
            self.new_top_level_action.setVisible(True)
            self.new_process_action.setVisible(False)
            self.rename_action.setVisible(False)
            self.copy_action.setVisible(False)
            self.copy_special_action.setVisible(False)
            self.remove_action.setVisible(False)
            self.show_options_action.setVisible(False)
        
        if not item:
            self.new_top_level_action.setVisible(True)
            self.new_process_action.setVisible(False)
            self.rename_action.setVisible(False)
            self.copy_action.setVisible(False)
            self.copy_special_action.setVisible(False)
            self.remove_action.setVisible(False)
            self.show_options_action.setVisible(False)
            self.convert_folder.setVisible(False)
        
        self.context_menu.exec_(self.viewport().mapToGlobal(position))
        
    def visualItemRect(self, item):
        pass
        
    def _create_context_menu(self):
        
        self.context_menu = qt.QMenu()
        
        self.new_process_action = self.context_menu.addAction('New Process')
        self.new_top_level_action = self.context_menu.addAction('New Top Level Process')
        self.context_menu.addSeparator()
        self.convert_folder = self.context_menu.addAction('Convert Folder to Process')
        
        self.context_menu.addSeparator()
        self.context_menu.addSeparator()
        self.rename_action = self.context_menu.addAction('Rename')
        self.copy_action = self.context_menu.addAction('Copy')
        self.paste_action = self.context_menu.addAction('Paste')
        self.merge_action = self.context_menu.addAction('Merge')
        self.paste_action.setVisible(False)
        self.merge_action.setVisible(False)
        self.copy_special_action = self.context_menu.addAction('Copy Match')
        self.remove_action = self.context_menu.addAction('Delete')
        self.context_menu.addSeparator()
        self.show_options_action = self.context_menu.addAction('Show Options')
        self.show_templates_action = self.context_menu.addAction('Show Templates')
        self.context_menu.addSeparator()
        browse_action = self.context_menu.addAction('Browse')
        refresh_action = self.context_menu.addAction('Refresh')
        
        
        self.new_top_level_action.triggered.connect(self._new_top_process)
        self.new_process_action.triggered.connect(self._new_process)
        self.convert_folder.triggered.connect(self._convert_folder)
        
        browse_action.triggered.connect(self._browse)
        refresh_action.triggered.connect(self.refresh)
        self.rename_action.triggered.connect(self._rename_process)
        self.copy_action.triggered.connect(self._copy_process)
        self.paste_action.triggered.connect(self.paste_process)
        self.merge_action.triggered.connect(self.merge_process)
        self.copy_special_action.triggered.connect(self._copy_special_process)
        self.remove_action.triggered.connect(self._remove_current_item)
        self.show_options_action.triggered.connect(self._show_options)
        self.show_templates_action.triggered.connect(self._show_templates)
        
    def _show_options(self):
        self.show_options.emit()
        
    def _show_templates(self):
        self.show_templates.emit()
        
    def _new_process(self):
        self.new_process.emit()
    
    def _convert_folder(self):
        self.convert_current_process()
    
    def _new_top_process(self):
        self.new_top_process.emit()
    
    def _inc_name(self, item, new_name):
        parent = item.parent()
        if not parent:
            parent = self.invisibleRootItem()
        
        siblingCount = parent.childCount()
        
        name_inc = 1
        pre_inc_name = new_name
        
        for inc in range(0, siblingCount):
            
            child_item = parent.child(inc)
            
            if child_item.matches(item):
                continue
            
            if child_item.text(0) == new_name:
                new_name = pre_inc_name + str(name_inc)
                name_inc += 1
        
        return new_name
    
    def _rename_process(self, item = None):
        

        
        if not item:
            items = self.selectedItems()
        
            if not items:
                return
        
            item = items[0]
        
        old_name = item.get_name()
        
        old_name = old_name.split('/')[-1]
        
        new_name = qt_ui.get_new_name('New Name', self, old_name)
        
        if not new_name:
            return
        
        new_name = self._inc_name(item, new_name)
        
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
        self.merge_action.setVisible(True)
        
        self.paste_item = item
        
        path = self._get_parent_path(item)
        
        self.paste_action.setText('Paste: %s' % path)
        self.merge_action.setText('Merge With: %s' % path)
        

        
    def _copy_special_process(self):
        self.copy_special_process.emit()
        
    def _remove_current_item(self):
        self.delete_process()
        self.process_deleted.emit()
        
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
        
        
    def _load_processes(self, process_paths, folders = []):

        self.clear()
        
        for process_path in process_paths:
            
            self._add_process_item(process_path)
            
        for folder in folders:
            self._add_process_item(folder, create = True, folder = True)
    
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
        
        iterator = qt.QTreeWidgetItemIterator(self)
        
        
        while iterator.value():
            item = iterator.value()
            
            if hasattr(item, 'directory') and hasattr(item, 'name'):
            
                if item.directory == settings_process[1]:
                    
                    if settings_process[0].startswith(item.name):
                        index = self.indexFromItem(item)
                        self.setExpanded(index, True)
                        
                    if settings_process[0] == item.name:
                        
                        self.setCurrentItem(item)
                        item.setSelected(True)
                        # I could leave the iterator here but I don't because it could crash Maya.
                    
            iterator += 1
    
    def _add_process_items(self, item, path):
        
        parts, folders = process.find_processes(path, return_also_non_process_list=True)
        
        self.directory
        sub_path = util_file.remove_common_path_simple(self.directory, path)
        
        self.setUpdatesEnabled(False)
        for part in parts:
            
            if sub_path:
                part = util_file.join_path(sub_path, part)
                self._add_process_item(part, item, find_parent_path = False)
            if not sub_path:
                self._add_process_item(part, item)
                
        for folder in folders:
            if sub_path:
                self._add_process_item(folder, item, create = True, find_parent_path = False, folder = True)
            if not sub_path:
                self._add_process_item(folder, item, create = True, folder = True)
                
        self.setUpdatesEnabled(True)
        
    def _add_process_item(self, name, parent_item = None, create = False, find_parent_path = True, folder = False):
        
        expand_to = False
        
        current_item = self.currentItem()
        
        if not parent_item and current_item:
            parent_item = current_item
            expand_to = True
        
        if find_parent_path:
            if parent_item:
                
                item_path = self.get_item_path_string(parent_item)
                
                if item_path:
                    name = string.join([item_path, name], '/')
                
                    if self._child_exists(name, parent_item):
                        return
                    
                if not item_path:
                    parent_item = None
        
        item = ProcessItem(self.directory, name)
        
        if not folder:
            process_inst = process.Process(name)
            process_inst.set_directory(self.directory)
        if folder:
            item.set_folder(True)
        
        
        if create:
            item.create()

        if parent_item and not folder:
            enable = process_inst.get_setting('enable')
            if not enable:
                item.setCheckState(0, qt.QtCore.Qt.Unchecked )
            if enable:
                item.setCheckState(0, qt.QtCore.Qt.Checked )
        
        if not parent_item:
            self.addTopLevelItem(item)
        
        if parent_item:
            
            if expand_to:
                self._auto_add_sub_items = False
                self.expandItem(parent_item)
                self._auto_add_sub_items = True
            parent_item.addChild(item)
            
        #has parts takes time because it needs to check children folders
        if item.has_parts() and not folder:
            qt.QTreeWidgetItem(item)
        
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
        
        path = ''
        
        if hasattr(item, 'get_name'):
            process_name = item.get_name()
            path = util_file.join_path(self.directory, process_name)
        
        self._add_process_items(item, path)
        
    def _browse(self):
        
        
        if self.current_folder:
            parent_path = self._get_parent_path(self.current_folder)
            path = util_file.join_path(self.directory, parent_path)
            
        if not self.current_folder:
            current_item = self.currentItem()
            process = current_item.get_process()
            path = process.get_path()
        
        util_file.open_browser(path)

    def refresh(self):
        
        
        
        self.clearSelection()
        
        processes, folders = process.find_processes(self.directory, return_also_non_process_list=True)
        
        #this can be slow when there are many processes at the top level, and it checks if each process has sub process.
        self._load_processes(processes, folders)
        
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
        
        self.setCurrentItem(item)
        self.setItemSelected(item, True)
        
        parent_item = item.parent()
        
        self._rename_process(item)
        
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

    def paste_process(self, source_process = None):
        
        self.paste_action.setVisible(False)
        
        if not source_process:
            
            if not self.paste_item:
                return
            
            source_process = self.paste_item.get_process()
        
        target_process = None
        
        items = self.selectedItems()
        if items:
            target_item = items[0]
            target_process = target_item.get_process()            
        if not items:
            target_item = None
        
        if not target_process:
            target_process = process.Process()
            target_process.set_directory(self.directory)
            target_item = None 
        
        new_process = process.copy_process(source_process, target_process)
        
        if not new_process:
            return
        
        self.paste_item = None
        
        new_item = self._add_process_item(new_process.get_name(), target_item)
        
        if target_process:
            if target_item:
                self.collapseItem(target_item)
                self.expandItem(target_item)
            
        if not target_process:
            self.scrollToItem(new_item)
            
        self.copy_process.emit()
        
    def merge_process(self, source_process = None):
        
        self.paste_action.setVisible(False)
        
        if not source_process:
            if not self.paste_item:
                return
            
            source_process = self.paste_item.get_process()
            
        source_process_name = source_process.get_name()
        
        qt_ui.get_permission('Are you sure you want to merge in %s?' % source_process_name)
            
        target_process = None
        
        items = self.selectedItems()
        if items:
            target_item = items[0]
            target_process = target_item.get_process()            
        if not items:
            target_item = None
        
        if not target_process:
            return 
        
        process.copy_process_into(source_process, target_process)
        
        if target_item:
            
            target_item.setExpanded(False)
            
            if source_process.get_sub_processes():
                
                temp_item = qt.QTreeWidgetItem()
                target_item.addChild(temp_item)
        
        self.copy_process.emit()
    
    def convert_current_process(self):
        
        
        current_item = self.current_folder
            
        if not current_item:
            return
        
        parent_path = self._get_parent_path(current_item)

        convert_permission = qt_ui.get_permission('Convert %s to process?' % parent_path, self)
        
        if not convert_permission:
            return
            
        process_instance = process.Process(parent_path)
        process_instance.set_directory(self.directory)
        process_instance.create()
        
        current_item.set_folder(False)
        
        if current_item.has_parts():
            qt.QTreeWidgetItem(current_item)
    
    def set_settings(self, settings):
        
        self.settings = settings
      

        
        
class ProcessItem(qt.QTreeWidgetItem):
    
    def __init__(self, directory, name, parent_item = None):
        super(ProcessItem, self).__init__(parent_item)
        
        self.process = None
        
        self.directory = directory
        self.name = name
        
        split_name = name.split('/')
        
        self.setText(0, split_name[-1])
        
        self.detail = False
        
        self.setSizeHint(0, qt.QtCore.QSize(50,26))
        
        self._folder = False
        
        
    def setData(self, column, role, value):
        super(ProcessItem, self).setData(column, role, value)
        
        process = self._get_process()
        
        if not process:
            return
        
        if hasattr(process, 'filepath') and not process.filepath:
            return
        
        if role == qt.QtCore.Qt.CheckStateRole:
            
            if value == 0:
                process.set_setting('enable', False)
            if value == 2:
                process.set_setting('enable', True)
            

        
        
    def _add_process(self, directory, name):
        
        self.process = process.Process(name)
        self.process.set_directory(directory)
        
        self.process.create()
        
    def _get_process(self):
        
        process_instance = process.Process(self.name)
        process_instance.set_directory(self.directory)
        
        return process_instance
        
    def create(self):
        
        if not self._folder:
            process_instance = self._get_process()
            
            if not process_instance.is_process():
                process_instance.create()    
        
    def rename(self, name):
        
        process_instance = self._get_process()
            
        state = process_instance.rename(name)
        
        if state:
            self.name = name
        
        return state
        
    def setText(self, column, text):
        
        text = '   ' + text 
        super(ProcessItem, self).setText(column, text)
        
    def text(self, column):
        
        text = super(ProcessItem, self).text(column)
        
        text = text.strip()
        return text
        
    def set_name(self, name):
        
        self.name = name
                
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
        
        process_path = util_file.join_path(self.directory, self.name)

        processes, folders = process.find_processes(process_path, return_also_non_process_list = True)
        
        if processes or folders:
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
    
    def set_folder(self, bool_value):
        self._folder = bool_value
        
        if bool_value:
            self.setDisabled(True)
        if not bool_value:
            self.setDisabled(False)
        
    def is_folder(self):
        return self._folder
    
class CopyWidget(qt_ui.BasicWidget):
    
    canceled = qt_ui.create_signal()
    pasted = qt_ui.create_signal()
    
    def __init__(self):
        
        super(CopyWidget, self).__init__()
        self.setWindowTitle('Copy Match')
        self.setWindowFlags(qt.QtCore.Qt.WindowStaysOnTopHint)
        self.setMinimumWidth(600)
        self.process = None
        
        alpha = 50
        
        if util.is_in_maya():
            alpha = 100
        
        self.yes_brush = qt.QBrush()
        self.yes_brush.setColor(qt.QColor(0,255,0, alpha))
        self.yes_brush.setStyle(qt.QtCore.Qt.SolidPattern)
    
        self.no_brush = qt.QBrush()
        self.no_brush.setColor(qt.QColor(255,0,0, alpha))
        self.no_brush.setStyle(qt.QtCore.Qt.SolidPattern)
        
        self.update_on_select = True
    
    def _build_widgets(self):
        
        self.copy_from = qt.QLabel('Copy from:')
        self.copy_from.setAlignment(qt.QtCore.Qt.AlignCenter)
        
        self.tabs = qt.QTabWidget()
        
        self.data_list = CopyTree()
        self.code_list = CopyTree()
        self.settings_list = CopyTree()
        
        #self.data_list.setMaximumHeight(300)
        #self.code_list.setMaximumHeight(300)
        #self.settings_list.setMaximumHeight(300)
        
        self.data_list.setSortingEnabled(True)
        self.data_list.setSelectionMode(self.data_list.ExtendedSelection)
        self.code_list.setSelectionMode(self.code_list.ExtendedSelection)
        self.settings_list.setSelectionMode(self.settings_list.ExtendedSelection)
        
        self.data_list.setHeaderLabels(['Source', 'Size/Date Match', 'Target'])
        self.code_list.setHeaderLabels(['Source', 'Content Match', 'Target'])
        self.settings_list.setHeaderLabels(['Source', 'Content Match', 'Target'])
        
        self.code_list.itemSelectionChanged.connect(self._code_selected)
        
        self.tabs.addTab(self.data_list, 'Data')
        self.tabs.addTab(self.code_list, 'Code')
        self.tabs.addTab(self.settings_list, 'Settings')
        
        h_layout = qt.QHBoxLayout()
        
        self.paste_button = qt.QPushButton('Paste')
        self.paste_button.setDisabled(True)
        self.paste_button.clicked.connect(self._paste)
        cancel = qt.QPushButton('Cancel')
        
        self.paste_button.clicked.connect(self.pasted)
        cancel.clicked.connect(self._cancelled)
        
        h_layout.addWidget(self.paste_button)
        h_layout.addWidget(cancel)
        
        self.paste_to = qt.QLabel('- Select Process in the View to Match -')
        self.paste_to.setAlignment(qt.QtCore.Qt.AlignCenter)
        
        self.progress_bar = qt.QProgressBar()
        self.progress_bar.hide()
        
        self.main_layout.addWidget(self.copy_from)
        self.main_layout.addWidget(self.tabs)
        self.main_layout.addWidget(self.paste_to)
        self.main_layout.addWidget(self.progress_bar)
        self.main_layout.addLayout(h_layout)
        
    def _code_selected(self):
        
        if not self.update_on_select:
            return
        
        selected = self.code_list.selectedItems()
        
        if not selected:
            return
        
        self.update_on_select = False
        
        if selected:
            first_item = selected[-1]
            first_item.setSelected(False)
            
        
        name = str(first_item.text(0))
        
        split_name = name.split('/')
        
        for inc in range(0, len(split_name)):
            
            sub_name = split_name[:inc]
            sub_name = string.join(sub_name, '/')
            
            for inc2 in range(0, self.code_list.topLevelItemCount()):
                item = self.code_list.topLevelItem(inc2)
                if str(item.text(2)).find('-') == -1:
                    continue
                test_name = item.text(0)
                
                if test_name == sub_name:
                    item.setSelected(True)
        
        first_item.setSelected(True)
        
        self.update_on_select = True
        
    def _cancelled(self):
        self.close()
        self.canceled.emit()
        
    def _populate_lists(self):
        
        self.progress_bar.reset()
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 3)
        
        self.data_list.clear()
        self.code_list.clear()
        self.settings_list.clear()
        
        data_folders = self.process.get_data_folders()
        
        self.populate_list(0, self.data_list, data_folders)
        
        self.progress_bar.setValue(1)
        
        codes, states = self.process.get_manifest()
        #codes = self.process.get_code_files(basename = True)
        code_names = []
        
        for code in codes:
            
            
            code_name = code.split('.')
            
            if not self.process.is_code_folder(code_name[0]):
                continue
            
            if len(code_name) > 1 and code_name[1] == 'py':
                code_names.append(code_name[0])
                
        code_names.insert(0, 'manifest')
        
        self.populate_list(0, self.code_list, code_names)    
        
        self.progress_bar.setValue(2)
        
        setting_names = self.process.get_setting_names()
        
        self.populate_list(0, self.settings_list, setting_names)
        
        self.progress_bar.setValue(3)
        
        self.progress_bar.setVisible(False)
        
    def populate_list(self, column, list_widget, data):
        
        for sub_data in data:
            
            list_widget.add_item(column, sub_data)
            
    def clear_lists(self):
        
        self.data_list.clear()
        self.code_list.clear()
        self.settings_list.clear()
        
    def populate_other_data(self, data):
        
        list_widget = self.data_list
        
        count = list_widget.topLevelItemCount()
        
        self.progress_bar.setValue(0)
        self.progress_bar.setRange(0, count)
        
        
        for inc in range(0, count):
            
            self.progress_bar.setValue(inc)
            
            item = list_widget.topLevelItem(inc)
            
            for sub_data in data:
                
                
                if item.text(0) == sub_data:
                    item.setText(2, (' ' * 10) + sub_data)
                    
                    source_data = self.process.get_data_instance(sub_data)
                    target_data = self.other_process.get_data_instance(sub_data)
                    
                    if not target_data:
                        continue
                    
                    
                    source_file = source_data.get_file()
                    target_file = target_data.get_file()
                    
                    if not target_file:
                        continue
                    
                    
                    same_content = False
                    
                    same = False
                    
                    if util_file.is_file(source_file) and util_file.is_file(target_file):
                        
                        same_content = util_file.is_same_text_content(source_file, target_file)
                        
                        if same_content:
                            same = True  
                        
                    else:
                        

                        same_date = util_file.is_same_date(source_file, target_file)
                        
                        if same_date:
                            same = True
                    
                        if same:
                            source_size = util_file.get_size(source_data.get_file())
                            target_size = util_file.get_size(target_data.get_file())
                        
                            if abs(source_size) - abs(target_size) > 0.01:
                                same = False
                                        
                    if same:
                        
                        item.setText(1, 'Yes')
                        item.setBackground(1, self.yes_brush)
                    
                    if not same:
                        item.setText(1, 'No')
                        item.setBackground(1, self.no_brush)
                        
                    model_index = list_widget.indexFromItem(item, column=0)
                    list_widget.scrollTo(model_index)
        
    def populate_other_code(self, code):
        
        self.tabs.setCurrentIndex(1)
        
        list_widget = self.code_list
        
        count = list_widget.topLevelItemCount()
        
        self.progress_bar.setValue(0)
        self.progress_bar.setRange(0, count)
        
        for inc in range(0, count):
            
            self.progress_bar.setValue(inc)
            
            item = list_widget.topLevelItem(inc)
            
            for sub_data in code:
                
                if item.text(0) == sub_data:
                    item.setText(2, (' ' * 10) + sub_data)
                    
                    source_folder = self.process.get_code_file(sub_data)
                    target_folder = self.other_process.get_code_file(sub_data)
                    
                    source_folder, target_folder
                    
                    match_lines = util_file.is_same_text_content(source_folder, target_folder)
                    
                    if match_lines:
                        item.setText(1, 'Yes')
                        item.setBackground(1, self.yes_brush)
                    if not match_lines:
                        item.setText(1, 'No')
                        item.setBackground(1, self.no_brush)
    
    def populate_other_settings(self, settings):
        
        self.tabs.setCurrentIndex(2)
        
        list_widget = self.settings_list
        
        count = list_widget.topLevelItemCount()
        
        self.progress_bar.setValue(0)
        self.progress_bar.setRange(0, count)
                
        for inc in range(0, count):
        
            self.progress_bar.setValue(inc)
            
            item = list_widget.topLevelItem(inc)

            
            for sub_data in settings:
                
                
                if item.text(0) == sub_data:
                    item.setText(2, (' ' * 10) + sub_data)
                    
                    source = self.process.get_setting_file(sub_data)
                    target = self.other_process.get_setting_file(sub_data)
                    
                    match_lines = util_file.is_same_text_content(source, target)
                    
                    if match_lines:
                        item.setText(1, 'Yes')
                        item.setBackground(1, self.yes_brush)
                    if not match_lines:
                        item.setText(1, 'No')
                        item.setBackground(1, self.no_brush)
    
    def _paste(self):
        
        self.progress_bar.setVisible(True)
        
        self._paste_data()
        self._paste_code()
        self._paste_settings()
        
        self.clear_lists()
        self._populate_lists()
        self.load_compare()
        
        self.progress_bar.hide()
        
    def _paste_data(self):
        
        data_items = self.data_list.selectedItems()
        
        if not data_items:
            return
        
        inc = 0
        
        self.tabs.setCurrentIndex(0)
        
        self.progress_bar.reset()
        self.progress_bar.setRange(0, len(data_items))
        
        
        for item in data_items:
            name = str(item.text(0))
            
            process.copy_process_data( self.process, self.other_process, name)
            self.progress_bar.setValue(inc)
            inc += 1
            
    def _paste_code(self):
        
        code_items = self.code_list.selectedItems()
    
        if not code_items:
            return
    
        self.tabs.setCurrentIndex(1)
    
        found = []
        slash_count_list = []
        
        manifest = ''
        
        for item in code_items:
            name = str(item.text(0))
            
            if not name:
                continue
            
            if name == 'manifest':
                manifest = name
                
            if not name == 'manifest':
                found.append(name)
                slash_count_list.append(name.count('/'))
                
        inc = 0
        
        self.progress_bar.reset()
        self.progress_bar.setRange(0, len(found))
        
        if found:
        
            sort = util.QuickSort(slash_count_list)
            sort.set_follower_list(found)
            slash_count_list, found = sort.run()
        
        if manifest:
            found.append(manifest)
        
        for name in found:
            
            process.copy_process_code( self.process, self.other_process, name)
            self.progress_bar.setValue(inc)
            inc += 1
            
    def _paste_settings(self):
        
        
        
        setting_items = self.settings_list.selectedItems()
        
        if not setting_items:
            return
        
        self.tabs.setCurrentIndex(2)
        
        inc = 0
        
        self.progress_bar.reset()
        self.progress_bar.setRange(0, len(setting_items))
        
        for item in setting_items:
            name = str(item.text(0))
            
            process.copy_process_setting(self.process, self.other_process, name)
            self.progress_bar.setValue(inc)
            inc+=1
    
    def set_process(self, process_name, process_directory):
        
        process_inst = process.Process(process_name)
        process_inst.set_directory(process_directory)
        
        self.process = process_inst
        
        self._populate_lists()
        
        self.copy_from.setText('Copy from:  %s' % process_name)
        
    def set_other_process(self, process_name, process_directory):
        
        
        
        if not self.process:
            return
        
        if not self.isVisible():
            return
        
        if process_name == self.process.get_name():
            self.paste_to.setText('Paste to:')
            self.paste_button.setDisabled(True)
            return
        
        self.progress_bar.reset()
        self.progress_bar.setVisible(True)
        
        process_inst = process.Process(process_name)
        process_inst.set_directory(process_directory)
        
        self.other_process = process_inst
        
        self.paste_to.setText('Paste to:  %s' % process_name)  
        self.paste_button.setEnabled(True)
        
        self.load_compare()
        
    def load_compare(self):
        
        if not self.other_process:
            return

        self.progress_bar.reset()
        self.progress_bar.setVisible(True)
        #self.progress_bar.setRange(0, 3)
        
        data_folders = self.other_process.get_data_folders()
        self.populate_other_data(data_folders)
        
        
        
        self.progress_bar.setValue(1)
        
        codes, states = self.other_process.get_manifest()
        #codes = self.other_process.get_code_files()
        code_names = []
        
        for code in codes:
            
            code_name = code.split('.')
            
            if not self.other_process.is_code_folder(code_name[0]):
                continue
            
            if len(code_name) > 1 and code_name[1] == 'py':
                code_names.append(code_name[0])
        
        code_names.append('manifest')
        
        self.populate_other_code(code_names)
        
        setting_names = self.process.get_setting_names()
        
        self.populate_other_settings(setting_names)
        
        self.progress_bar.setVisible(False)
        
        self.tabs.setCurrentIndex(0)
        
class CopyTree(qt.QTreeWidget):
    
    def __init__(self):
        super(CopyTree, self).__init__()
        
        self.setHeaderLabels(['Source', 'State', 'Target'])
        header_item = self.headerItem()
        #header_item.setTextAlignment(0, QtCore.Qt.AlignLeft)
        header_item.setTextAlignment(1, qt.QtCore.Qt.AlignHCenter)
        
        self.setColumnWidth(0, 240)
        self.setColumnWidth(1, 100)
        #header_item.setTextAlignment(2, QtCore.Qt.AlignRight)
        
    def add_item(self, column, name):
        
        item = qt.QTreeWidgetItem()
        item.setText(column, name)
        item.setText(1, '-')
        item.setText(2, (' ' * 10) + '-')
        item.setTextAlignment(1, qt.QtCore.Qt.AlignCenter)
        self.addTopLevelItem(item)
        
        return item
        




#--- DEV

class ProcessTreeView(qt.QTreeView):
    
    def __init__(self, directory):
        
        super(ProcessTreeView, self).__init__()
        
        self.directory = directory
        
        self.setModel(ProcessTreeModel(directory))
        #self.setItemDelegate(ProcessTreeDelegate())
        
        
    
class ProcessTreeModel(qt.QtCore.QAbstractListModel):
    
    def __init__(self, directory, parent = None):
        super(ProcessTreeModel, self).__init__(parent)
        
        self.directory = directory
        
        self.root_item = process.Process()
        self.root_item.set_directory(directory)
        
        self.processes = []
        
        #items = process.find_processes(directory)
        
        #self.items = items
    def flags(self, index):
        if not index.isValid():
            return 0

        return qt.QtCore.Qt.ItemIsEditable | qt.QtCore.Qt.ItemIsEnabled | qt.QtCore.Qt.ItemIsSelectable
    
    def parent(self, index):
        
        if not index.isValid():
            return qt.QtCore.QModelIndex()

        child_process = self.getItem(index)
        
        parent_process = child_process.Process.get_parent_process()
        
        if not parent_process:
            return qt.QtCore.QModelIndex()
        
        return self.createIndex(parent_process.get_sub_process_count(), 0, parent_process)
    
    def getItem(self, index):
        
        if index.isValid():
            item = index.internalPointer()
            if item:
                return item

        return self.root_item
    
    def headerData(self, section, orientation, role=qt.QtCore.Qt.DisplayRole):
        if orientation == qt.QtCore.Qt.Horizontal and role == qt.QtCore.Qt.DisplayRole:
            return 'header_test'

        return None
    
    def hasChildren(self, parent):
        
        return True
        """
        print 'has children!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!?'
        
        if not parent.isValid:
            parent_process = self.root_item
        if parent.isValid:
            parent_process = parent.internalPointer()
        
        print parent_process
        
        if parent_process and parent_process.has_sub_parts():
            return True
        
        return False
        """
        
        
    
    def index(self, row, column, parent):
        
        #if not self.hasIndex(row, column, parent):
        #    return qt.QtCore.QModelIndex()
        if not parent.isValid():
            parent_process = self.root_item
        else:
            parent_process = parent.internalPointer()
        
        
        child_process = parent_process.get_sub_process_by_index(row)
        
        if child_process:
            
            self.processes.append(child_process)
            return self.createIndex(row, column, child_process)
        else:
            return qt.QtCore.QModelIndex()
    
    def columnCount(self, parent=qt.QtCore.QModelIndex()):
        #
        return 0
    
    def rowCount(self, parent=qt.QtCore.QModelIndex()):
        
        parent_process = self.getItem(parent)
        
        return parent_process.get_sub_process_count()
    
    def data(self, index, role):
        #returns the data in a way that can be displayed
        
        if not index.isValid():
            
            return None
        
        if role != qt.QtCore.Qt.DisplayRole and role != qt.QtCore.Qt.EditRole:
            
            return None
        #index.row()
        #index.column()
        #index.parent() #hierarchal
        
        if role == qt.QtCore.Qt.DisplayRole:
            
            process_inst = index.internalPointer()
            name = process_inst.get_basename()
            
            return name
        
        
        
        
        #return process_inst.get_basename()
    
class ProcessTreeItem(object):
    def __init__(self, data, parent=None):
        self.parentItem = parent
        self.itemData = data
        self.childItems = []
        
        

    def child(self, row):
        return self.childItems[row]

    def childCount(self):
        return len(self.childItems)

    def childNumber(self):
        if self.parentItem != None:
            return self.parentItem.childItems.index(self)
        return 0

    def columnCount(self):
        return len(self.itemData)

    def data(self, column):
        return self.itemData[column]

    def insertChildren(self, position, count, columns):
        if position < 0 or position > len(self.childItems):
            return False

        for row in range(count):
            data = [None for v in range(columns)]
            item = ProcessTreeItem(data, self)
            self.childItems.insert(position, item)

        return True

    def insertColumns(self, position, columns):
        if position < 0 or position > len(self.itemData):
            return False

        for column in range(columns):
            self.itemData.insert(position, None)

        for child in self.childItems:
            child.insertColumns(position, columns)

        return True

    def parent(self):
        return self.parentItem

    def removeChildren(self, position, count):
        if position < 0 or position + count > len(self.childItems):
            return False

        for row in range(count):
            self.childItems.pop(position)

        return True

    def removeColumns(self, position, columns):
        if position < 0 or position + columns > len(self.itemData):
            return False

        for column in range(columns):
            self.itemData.pop(position)

        for child in self.childItems:
            child.removeColumns(position, columns)

        return True

    def setData(self, column, value):
        if column < 0 or column >= len(self.itemData):
            return False

        self.itemData[column] = value

        return True


class ProcessTreeDelegate(qt.QItemDelegate):
    
    def paint(self, painter, option, index):
        
        #rect = qt.QtCore.QRect(20,20,10,10)
        
        self.drawCheck(painter, option, option.rect, qt.QtCore.Qt.Checked)
        self.drawFocus(painter, option, option.rect)
        painter.drawText(option.rect, 'goobers')
        
        #super(ProcessTreeDelegate, self).paint(painter, option, index)
    
    def sizeHint(self, option, index):
        
        return qt.QtCore.QSize(100,26)
    
    
