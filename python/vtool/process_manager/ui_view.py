# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

import string
import traceback
import filecmp

from vtool import util
from vtool import util_file
from vtool import qt_ui, qt

import process

from vtool import logger
from __builtin__ import False
log = logger.get_logger(__name__) 

class ViewProcessWidget(qt_ui.EditFileTreeWidget):
    
    description = 'Process'
    
    copy_done = qt_ui.create_signal()
    path_filter_change = qt_ui.create_signal(object)
    name_filter_change = qt_ui.create_signal(object)
    
    def __init__(self):
        
        self.settings = None
        
        super(ViewProcessWidget, self).__init__()
        
        policy = self.sizePolicy()
        policy.setHorizontalPolicy(policy.Minimum)
        policy.setHorizontalStretch(0)
        self.setSizePolicy(policy)
        
        self.filter_widget.sub_path_changed.connect(self._update_sub_path_filter)
        self.filter_widget.name_filter_changed.connect(self._update_name_filter_setting)
       
    def _edit_click(self, bool_value):
        super(ViewProcessWidget, self)._edit_click(bool_value)
        
        self.tree_widget.edit_state = bool_value
        
    def _define_tree_widget(self):
        
        
        tree_widget = ProcessTreeWidget() 
        
        tree_widget.copy_special_process.connect(self._copy_match)
        tree_widget.copy_process.connect(self._copy_done)
        
        return tree_widget
        
    def _build_widgets(self):
        super(ViewProcessWidget, self)._build_widgets()
        
        self.copy_widget = None
    
    def _copy_done(self):
        self.copy_done.emit()
    
    def _copy_match(self, process_name = None, directory = None, show_others = True):
        
        copy_widget = CopyWidget(show_others = show_others)
        self.copy_widget = copy_widget
                
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
        
        current_path = util_file.join_path(directory, current_process)
        
        permission = util_file.get_permission(current_path)
        if not permission:
            util.warning('Could not get permission: %s' % directory)
            return
        
        if not util_file.exists(current_path):
            util.warning('Could not get a directory.  set sub path filter may be set wrong.')
            return
        
        copy_widget.show()
        
        copy_widget.set_process(current_process, directory)
        
        self.setFocus()
        
        if not process_name:
            #then it must be using the found current process
            items = self.tree_widget.selectedItems()
            self.tree_widget.scrollToItem(items[0], self.tree_widget.PositionAtCenter)
        
        self.copy_done.emit()
        
    def copy_match(self, process_name, directory, show_others = True):
        
        self._copy_match(process_name, directory, show_others)
        
        target_process = None
        
        items = self.tree_widget.selectedItems()
        if items:
            target_item = items[0]
            target_process = target_item.get_process()            
        if not items:
            target_item = None
            process_directory = util.get_env('VETALA_CURRENT_PROCESS')
            
            target_process = process.Process()
            target_process.set_directory(process_directory)
        
        if not target_process:
            return
        
        other_path = target_process.get_path()
        
        permission = util_file.get_permission(other_path)
        if not permission:
            util.warning('Could not get permission: %s' % other_path)
            return
        
        basename = util_file.get_basename(other_path)
        dir_path = util_file.get_dirname(other_path)
        
        self.copy_widget.set_other_process(basename, dir_path)
    
    def _get_filter_name(self, name):
        filter_value = self.filter_widget.get_sub_path_filter()
        test_name = filter_value + '/' + name
        test_path = util_file.join_path(self.directory, test_name)
        if util_file.is_dir(test_path):
            name = test_name
            
        return name
        
    
    def _item_selection_changed(self):
        
        name, item = super(ViewProcessWidget, self)._item_selection_changed()
        
        if not name:
            return
                
        name = self.tree_widget._get_parent_path(item)
        
        if name:
            name = self._get_filter_name(name)
        
        if self.copy_widget:
            self.copy_widget.set_other_process(name, self.directory)
    
    def _initialize_project_settings(self):
        
        process.initialize_project_settings(self.directory, self.settings)
        
    def _get_project_setting(self, name):
        
        value = process.get_project_setting(name, self.directory, self.settings)
        return value
    
    def _set_project_setting(self, name, value):
        
        process.set_project_setting(name, value, self.directory, self.settings)   
    
    def _update_sub_path_filter(self, value):
        
        self.filter_widget.repaint()
        
        test_dir = self.directory
        
        if value != None:
            if value:
                test_dir = util_file.join_path(self.directory, value)
        
        if not util_file.is_dir(test_dir):
            self.filter_widget.set_sub_path_warning(True)
        else: 
            self.filter_widget.set_sub_path_warning(False)
        self.filter_widget.repaint()
        self._set_project_setting('process sub path filter', value)
        
        self.path_filter_change.emit(value)
    
    def _update_name_filter_setting(self, value):
        
        log.info('Setting name filter: %s' % value)
        
        self._set_project_setting('process name filter', value)
        
    def get_current_process(self):
        
        items = self.tree_widget.selectedItems()
        if not items:
            return
        
        item = items[0]
        
        name = item.get_name()
        
        name =  self.tree_widget._get_parent_path(name)
                
        name = self._get_filter_name(name)
        
        return name
    
    def clear_sub_path_filter(self):
        self.filter_widget.clear_sub_path_filter()
        
    def clear_name_filter(self):
        self.filter_widget.clear_name_filter()
        
    
    def set_directory(self, directory, sub=False):
        
        if not directory:
            return
        
        self.directory = directory
        
        settings_directory = util.get_env('VETALA_SETTINGS')
        
        
        if self.settings:
            self.settings.set_directory(settings_directory)
        
        #this was the old way, but looks like just setting directory is better
        #settings_inst = util_file.SettingsFile()
        #settings_inst.set_directory(settings_directory)
        #self.set_settings(settings_inst)
        
        self.set_settings(self.settings)
        
        sub_path = self.filter_widget.get_sub_path_filter()
        name = self.filter_widget.get_name_filter()
                
        super(ViewProcessWidget,self).set_directory(directory, sub_path = sub_path, name_filter = name)
        
        
    def set_settings(self, settings):
        
        self.tree_widget.repaint()
        
        self.settings = settings
        
        self.tree_widget.set_settings(settings)
        
        if not self.settings.has_setting('project settings'):
            return
        
        name_filter = self._get_project_setting('process name filter')
        sub_path_filter = self._get_project_setting('process sub path filter')
        
        self.filter_widget.update_tree = False
        self.filter_widget.sub_path_filter.clear()
        self.filter_widget.filter_names.clear()
        self.filter_widget.update_tree = True
        
        self.filter_widget.set_emit_changes(False)
         
        if sub_path_filter:
            
            test_path = util_file.join_path(self.directory, sub_path_filter)
            
            if not util_file.is_dir(test_path):
                self.filter_widget.set_sub_path_warning(True)
            
            self.filter_widget.set_sub_path_filter(sub_path_filter)
            self.path_filter_change.emit(sub_path_filter)
        if name_filter:
            self.filter_widget.set_name_filter(name_filter) 

class ProcessTreeWidget(qt_ui.FileTreeWidget):
    
    new_process = qt_ui.create_signal()
    new_top_process = qt_ui.create_signal()  
    copy_process = qt_ui.create_signal()
    copy_special_process = qt_ui.create_signal()
    process_deleted = qt_ui.create_signal()
    item_renamed = qt_ui.create_signal(object)
    show_options = qt_ui.create_signal()
    show_notes = qt_ui.create_signal()
    show_templates = qt_ui.create_signal()
    show_settings = qt_ui.create_signal()
    show_maintenance = qt_ui.create_signal()
    selection_changed = qt_ui.create_signal()
    
    
    def __init__(self, checkable = True):
        
        self.progress_bar = None
        self.top_is_process = False
        self._handle_selection_change = True
        
        self.checkable = checkable
        self.deactivate_modifiers = True
        
        self.settings = None
        self.shift_activate = False
        
        
        super(ProcessTreeWidget, self).__init__()
        
        self.setVerticalScrollMode(self.ScrollPerPixel)
        
        
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
        
        self.context_menu = qt.QMenu()
        self._create_context_menu()
        
        self.paste_item = None
                
                
        self.setSelectionBehavior(self.SelectItems)
        self.setSelectionMode(self.SingleSelection)
        
        self.dragged_item = None
                
        self.setAlternatingRowColors(True)
        
        self.current_folder = None
        
        self.itemSelectionChanged.connect(self._selection_changed)
        
        self.disable_right_click = False
        
        if self.checkable:
            if util.is_in_maya():
                
                directory = util_file.get_vetala_directory()
                icon_on = util_file.join_path(directory, 'icons/plus.png')
                icon_off = util_file.join_path(directory, 'icons/minus_alt.png')
                                
                lines = 'QTreeView::indicator:unchecked {image: url(%s);}' % icon_off
                lines += ' QTreeView::indicator:checked {image: url(%s);}' % icon_on

                self.setStyleSheet( lines) 

        self.setWhatsThis('The view process list.\n'
                          '\n'
                          'This view lists processes found in the project.\n'  
                          'To set a project go to the settings (gear) tab.\n'
                          'Clicking on a process will load it into the Data and Code tabs as well as make its options visible.\n' 
                          'To edit processes you need to turn on the edit button on the bottom right of this widget.\n'
                          'Turning on edit will also provide ways of creating new processes. It will also turn on drag and drop to reorder processes.\n'
                          '\n'
                          'Folders\n'
                          '\n'
                          'Grey entries are regular folders and not processes.\n'
                          'Vetala lists folders as a convenience.\n'
                          'To Convert a folder to process, right click on it in edit mode and select: Convert Folder to Process\n'
                          
        )

    def keyPressEvent(self, event):
        
        if event.key() == qt.QtCore.Qt.Key_Shift:
            self.shift_activate = True
    
    def keyReleaseEvent(self, event):
        if event.key() == qt.QtCore.Qt.Key_Shift:
            
            self.shift_activate = False

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
        
        old_directory = self.dragged_item.directory
        old_name_full = self.dragged_item.get_name()
        old_name = util_file.get_basename(old_name_full)
        
        test_name = self._inc_name(self.dragged_item, old_name)
        self.dragged_item.setText(0, test_name)
        
        if self.checkable:  
            
            flags = qt.QtCore.Qt.ItemIsDragEnabled | qt.QtCore.Qt.ItemIsSelectable | qt.QtCore.Qt.ItemIsDropEnabled | qt.QtCore.Qt.ItemIsUserCheckable
        else:
            flags = self.dragged_item.setFlags(qt.QtCore.Qt.ItemIsDragEnabled | qt.QtCore.Qt.ItemIsSelectable | qt.QtCore.Qt.ItemIsDropEnabled )
              
        if entered_name:
            
            self.dragged_item.setFlags( flags )
            
            if self.checkable:
                self.dragged_item.setCheckState(0, qt.QtCore.Qt.Unchecked)
            message = 'Parent %s under %s?' % (old_name, entered_name)
        
        if not entered_name:
            
            if self.checkable:
                self.dragged_item.setData(0, qt.QtCore.Qt.CheckStateRole, None)
                
            self.dragged_item.setFlags(flags)
            self.dragged_item.setDisabled(True)
            
            message = 'Unparent %s?' % old_name
        
        
        
        move_result = qt_ui.get_permission( message , self)
        
        if not move_result:
            entered_item.removeChild(self.dragged_item)
            if self.drag_parent:
                self.drag_parent.addChild(self.dragged_item)
            self.dragged_item.setDisabled(False)
            self.dragged_item.setText(0,old_name)
            self.dragged_item.setSelected(True)
            return
            
        self.dragged_item.setDisabled(False)
        
        
        
        old_path = self.dragged_item.get_path()
        
        self.dragged_item.set_directory(directory)
        
        #new_name = self._inc_name(self.dragged_item, old_name)
        new_name = self.dragged_item.text(0)
        
        self.dragged_item.setText(0, new_name)
        if entered_name:
            new_name = util_file.join_path(entered_name, new_name)
            
        self.dragged_item.set_name(new_name)
        
        new_path = util_file.join_path(directory, new_name)
        
        move_worked = util_file.move(old_path, new_path)

        if move_worked:
            self.dragged_item.setSelected(True)

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
            self.setCurrentItem(self.invisibleRootItem())
        
        if event.button() == qt.QtCore.Qt.RightButton:
            return
        
        if model_index.column() == 0 and item:
            super(ProcessTreeWidget, self).mouseMoveEvent(event)
        
    def mousePressEvent(self, event):
        
        item = self.itemAt(event.pos())
        
        if self.deactivate_modifiers:
            modifiers = qt.QApplication.keyboardModifiers()
            #if modifiers == qt.QtCore.Qt.ShiftModifier:
            #    return
            if modifiers == qt.QtCore.Qt.ControlModifier:
                return
            if modifiers == (qt.QtCore.Qt.ControlModifier | qt.QtCore.Qt.ShiftModifier):
                return
            
            if modifiers == qt.QtCore.Qt.AltModifier:
                position = self.mapToGlobal(self.rect().topLeft())
                qt.QWhatsThis.showText(position, self.whatsThis())
                return
        
        parent = self.invisibleRootItem()
        
        if item:

            if item.parent():
                parent = item.parent()
        else:
            self.setCurrentItem(self.invisibleRootItem())
            return
            
        self.drag_parent = parent
        
        self.dragged_item = item
        
        super(ProcessTreeWidget, self).mousePressEvent(event)
    
    
    def _item_expanded(self, item):
    
        super(ProcessTreeWidget, self)._item_expanded(item)
        
        if self.shift_activate:
            child_count = item.childCount()
            
            for inc in range(0, child_count):
                
                children = self._get_ancestors(item.child(inc))
                item.child(inc).setExpanded(True)
                
                for child in children:
                    child.setExpanded(True)
    
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

    def _set_item_menu_vis(self, position):
        
        
        
        item = self.itemAt(position)
        is_folder = True
                
        if not item:
            self.clearSelection()
            self.setCurrentItem(self.invisibleRootItem())
        else:
            if hasattr(item, 'is_folder'):
                is_folder = item.is_folder()
        
        if self.top_is_process:
            item = True
            is_folder = False
        
        if item and not is_folder:
            if self.edit_state:
                self.new_process_action.setVisible(True)
                self.new_top_level_action.setVisible(True)
                self.rename_action.setVisible(True)
                self.duplicate_action.setVisible(True)
                self.remove_action.setVisible(True)
                self.copy_action.setVisible(True)
                self.copy_special_action.setVisible(True)
                self.edit_mode_message.setVisible(False)
            else:
                self.new_process_action.setVisible(False)
                self.new_top_level_action.setVisible(False)
                self.rename_action.setVisible(False)
                self.duplicate_action.setVisible(False)
                self.remove_action.setVisible(False)
                self.copy_action.setVisible(False)
                self.copy_special_action.setVisible(False)
                self.edit_mode_message.setVisible(True)
            
            
            self.show_options_action.setVisible(True)
            self.convert_folder.setVisible(False)
            self.show_notes_action.setVisible(True)
            self.show_options_action.setVisible(True)
            self.show_settings_action.setVisible(True)
            self.show_templates_action.setVisible(True)
            self.show_maintenance_action.setVisible(True)
        
        if item and is_folder:
            self.current_folder = item
            
            if self.edit_state:
                self.convert_folder.setVisible(True)
                self.new_top_level_action.setVisible(True)
                self.new_process_action.setVisible(True)
                self.edit_mode_message.setVisible(False)
            else:
                self.convert_folder.setVisible(False)
                self.new_top_level_action.setVisible(False)
                self.new_process_action.setVisible(False)
                self.edit_mode_message.setVisible(True)
            
            self.rename_action.setVisible(False)
            self.duplicate_action.setVisible(False)
            self.copy_action.setVisible(False)
            self.copy_special_action.setVisible(False)
            self.remove_action.setVisible(False)
            self.show_options_action.setVisible(False)
            
            self.show_notes_action.setVisible(False)
            self.show_options_action.setVisible(False)
            self.show_settings_action.setVisible(False)
            self.show_templates_action.setVisible(False)
            self.show_maintenance_action.setVisible(False)
        
        if not item:
            if self.edit_state:
                self.new_top_level_action.setVisible(True)
                self.edit_mode_message.setVisible(False)
            else:
                self.new_top_level_action.setVisible(False)
                self.edit_mode_message.setVisible(True)
                
            self.new_process_action.setVisible(False)
            self.rename_action.setVisible(False)
            self.duplicate_action.setVisible(False)
            self.remove_action.setVisible(False)
                
            self.copy_action.setVisible(False)
            self.copy_special_action.setVisible(False)
            
            #self.show_options_action.setVisible(False)
            self.convert_folder.setVisible(False)

            self.show_notes_action.setVisible(False)
            self.show_options_action.setVisible(False)
            self.show_settings_action.setVisible(False)
            self.show_templates_action.setVisible(False)
            self.show_maintenance_action.setVisible(False)

        copied = util.get_env('VETALA_COPIED_PROCESS')
        
        if copied:
            process_inst = process.Process()
            process_inst.set_directory(copied)
            name = process_inst.get_name()
            
            self.paste_action.setText('Paste: %s' % name)
            self.merge_action.setText('Merge In: %s' % name)
            self.merge_with_sub_action.setText('Merge With Sub Folders: %s' % name)
            self.paste_action.setVisible(True)
            self.merge_action.setVisible(True)
            self.merge_with_sub_action.setVisible(True)

    def _item_menu(self, position):
        
        if self.disable_right_click:
            return
        
        self.current_folder = None
        
        self._set_item_menu_vis(position)
        
        self.context_menu.exec_(self.viewport().mapToGlobal(position))
        
        
    
    def _selection_changed(self):
        
        if self._handle_selection_change:
            self.selection_changed.emit()
            
    def _create_context_menu(self):
        
        
        
        self.edit_mode_message = self.context_menu.addAction('Turn on Edit mode (at the bottom of the view) to access more commands.')
        self.edit_mode_message.setVisible(False)
        
        self.new_process_action = self.context_menu.addAction('New Process')
        self.new_top_level_action = self.context_menu.addAction('New Top Level Process')
        self.context_menu.addSeparator()
        self.convert_folder = self.context_menu.addAction('Convert Folder to Process')
        self.convert_folder.setVisible(False)
        self.context_menu.addSeparator()
        self.context_menu.addSeparator()
        self.rename_action = self.context_menu.addAction('Rename')
        self.duplicate_action = self.context_menu.addAction('Duplicate')
        self.copy_action = self.context_menu.addAction('Copy')
        self.paste_action = self.context_menu.addAction('Paste')
        self.merge_action = self.context_menu.addAction('Merge')
        self.merge_with_sub_action = self.context_menu.addAction('Merge With Sub Folders')
        self.paste_action.setVisible(False)
        self.merge_action.setVisible(False)
        self.merge_with_sub_action.setVisible(False)
        self.copy_special_action = self.context_menu.addAction('Copy Match')
        self.remove_action = self.context_menu.addAction('Delete')
        self.context_menu.addSeparator()
        self.show_options_action = self.context_menu.addAction('Show Options')
        self.show_notes_action = self.context_menu.addAction('Show Notes')
        self.show_templates_action = self.context_menu.addAction('Show Templates')
        self.show_settings_action = self.context_menu.addAction('Show Settings')
        self.show_maintenance_action = self.context_menu.addAction('Show Maintenance')
        self.context_menu.addSeparator()
        browse_action = self.context_menu.addAction('Browse')
        refresh_action = self.context_menu.addAction('Refresh')
        
        self.new_top_level_action.triggered.connect(self._new_top_process)
        self.new_process_action.triggered.connect(self._new_process)
        self.convert_folder.triggered.connect(self._convert_folder)
        
        browse_action.triggered.connect(self._browse)
        refresh_action.triggered.connect(self.refresh)
        self.rename_action.triggered.connect(self._rename_process)
        self.duplicate_action.triggered.connect(self._duplicate_process)
        self.copy_action.triggered.connect(self._copy_process)
        self.paste_action.triggered.connect(self.paste_process)
        self.merge_action.triggered.connect(self.merge_process)
        self.merge_with_sub_action.triggered.connect(self.merge_with_sub_process)
        self.copy_special_action.triggered.connect(self._copy_special_process)
        self.remove_action.triggered.connect(self._remove_current_item)
        self.show_options_action.triggered.connect(self._show_options)
        self.show_notes_action.triggered.connect(self._show_notes)
        self.show_templates_action.triggered.connect(self._show_templates)
        self.show_settings_action.triggered.connect(self._show_settings)
        self.show_maintenance_action.triggered.connect(self._show_maintenance)
        
        
        
    def _show_options(self):
        self.show_options.emit()
        
    def _show_notes(self):
        self.show_notes.emit()
        
    def _show_templates(self):
        self.show_templates.emit()
    
    def _show_settings(self):
        self.show_settings.emit()
    
    def _show_maintenance(self):
        self.show_maintenance.emit()
        
    def _new_process(self):
        self.add_process('')
    
    def _convert_folder(self):
        self.convert_current_process()
    
    def _new_top_process(self):
        self.add_process(None)
        
    def _inc_name(self, item, new_name):
        parent = item.parent()
        if not parent:
            parent = self.invisibleRootItem()
        
        sibling_count = parent.childCount()
        
        name_inc = 1
        
        found_one = False
        
        for inc in range(0, sibling_count):
            
            child_item = parent.child(inc)
            
            if child_item.text(0) == new_name:
                
                if not found_one:
                    found_one = True
                    continue
                
                new_name = util.increment_last_number(new_name)
                
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
        
        if new_name == old_name:
            util.warning('Item not renamed. New name matches old name.')
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
        
        item.get_process().get_path()
        
        self.paste_item = item
        #path = self._get_parent_path(item)
        name = item.get_name()
        
        util.set_env('VETALA_COPIED_PROCESS', item.get_path())
        
        self.paste_action.setText('Paste: %s' % name)
        self.merge_action.setText('Merge In: %s' % name)
        self.merge_with_sub_action.setText('Merge With Sub Folders: %s' % name)
        self.paste_action.setVisible(True)
        self.merge_action.setVisible(True)
        self.merge_with_sub_action.setVisible(True)
        
    def _duplicate_process(self):
        
        items = self.selectedItems()
        if not items:
            return
        
        item = items[0]
        
        source_process = item.get_process()
        target_process = item.get_parent_process()
        
        target_item = item.parent()
        
        if not target_process:
            target_process = process.Process()
            target_process.set_directory(self.directory)
            target_item = self.invisibleRootItem()
        
        
        
        new_process = process.copy_process(source_process, target_process)
        
        if not new_process:
            return
        
        new_item = self._add_process_item(new_process.get_name(), target_item)
        
        self.setCurrentItem(new_item)    
        new_item.setSelected(True)
        self.scrollToItem(new_item, self.PositionAtCenter)
        
    def _copy_special_process(self):
        self.copy_special_process.emit()
        
    def _remove_current_item(self):
        self.delete_process()
        self.process_deleted.emit()
        
    def _define_header(self):
        return ['name']  
    
    def _edit_finish(self, item):
        #if self.edit_state:
        item = super(ProcessTreeWidget, self)._edit_finish(item)  
        #self.item_renamed.emit(item)
        
    def _item_rename_valid(self, old_name, item):
        
        state = super(ProcessTreeWidget, self)._item_rename_valid(old_name, item)
        
        if state == False:
            return state
        
        if state == True:
            name = self._get_parent_path(item)
            path = util_file.join_path(self.directory, name)
            
            if util_file.is_dir(path, case_sensitive=True):
                return False
            
            return True
        
        return False
        
    def _item_renamed(self, item):
        
        path = self.get_item_path_string(item)
        state = item.rename(path)
        
        if state == True:
            item.setExpanded(False)
        
        return state
        
    def _item_clicked(self, item, column):
        super(ProcessTreeWidget, self)._item_clicked(item, column)
        
        
        
        #self.selection_changed.emit()
        
    def _item_remove(self, item):
        parent_item = item.parent()
        
        if parent_item:
            parent_item.removeChild(item)
            
        if not parent_item:
            index = self.indexOfTopLevelItem(item)
            self.takeTopLevelItem(index)
            self.clearSelection()
            self.setCurrentItem(self.invisibleRootItem())
        
    
        
    
    def _get_parent_path(self, item):
        
        parents = self.get_tree_item_path(item)
        parent_names = self.get_tree_item_names(parents)
        
        if not parent_names:
            return item
        
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

    def _get_project_setting(self, name):
        log.info('Get project setting: %s' % name)
        settings_inst = None
        
        if not self.settings:
            settings_directory = util.get_env('VETALA_SETTINGS')
        
            settings_inst = util_file.SettingsFile()
            settings_inst.set_directory(settings_directory)
        else:
            settings_inst = self.settings
        
        settings_inst.reload()
        
        value = process.get_project_setting(name, self.project_dir, settings_inst)
        return value
        

    def _goto_settings_process(self):
        
        goto_process = self._get_project_setting('process')
        
        log.info('Goto settings process: %s' % goto_process)
        
        if not goto_process:
            return
        
        path_filter = self._get_project_setting('process sub path filter')
        
        directory = self.project_dir
        name = goto_process
        
        if path_filter:
            directory = util_file.join_path(directory, path_filter)
        
        found = False
        found_item = None
        
        iterator = qt.QTreeWidgetItemIterator(self)
        
        if self.progress_bar:
            self.progress_bar.show()
            self.progress_bar.reset()
            self.progress_bar.setRange(0,0)
            #self.progress_bar.setRange(0, self.topLevelItemCount())
        
        while iterator.value():
            
            if not found:
                
                item = iterator.value()
                
                if hasattr(item, 'directory') and hasattr(item, 'name'):
                    
                    util_file.get_common_path(directory, item.directory)
                    
                    if item.directory == directory:
                        
                        if name.startswith(item.name):
                            
                            index = self.indexFromItem(item)
                            self.setExpanded(index, True)
                            self.scrollToItem(item, self.PositionAtCenter)
                            
                            try:
                                self.update()
                            except:
                                #updated not working in Maya 2017 for some reason
                                pass
                        
                        if str(name) == str(item.name):                    
                            found_item = item
                            found = True
                            self.scrollToItem(found_item, self.PositionAtCenter)
                            self.setCurrentItem(found_item)            
                            self.setItemSelected(found_item, True)
                            
                            try:
                                self.update()
                            except:
                                #updated not working in Maya 2017 for some reason
                                pass
                            # I could leave the iterator here but I don't because it could crash Maya.
                            #something to do with using QTreeWidgetItemIterator
                            #still the case July 3rd,2020
                        
                        
            iterator.next()
        
        if self.progress_bar:
            self.progress_bar.reset()
            self.progress_bar.hide()
            
        
        #if found_item:    
            #found_item.setSelected(True)
        #    self.scrollToItem(found_item, self.PositionAtCenter)
        #    self.setCurrentItem(found_item)            
        #    self.setItemSelected(found_item, True)
            

    def _load_processes(self, process_paths, folders = []):

        self.clear()
        
        if self.top_is_process:
            pass
        
        if self.progress_bar:
            self.progress_bar.show()
            self.progress_bar.reset()
            self.progress_bar.setRange(0, len(process_paths))
            inc = 0
        
        for process_path in process_paths:
            if self.progress_bar:
                self.progress_bar.setValue(inc)
                inc += 1
            self._add_process_item(process_path, find_parent_path=False)
            
        if self.progress_bar:
            self.progress_bar.reset()
            self.progress_bar.setRange(0, len(folders))
            inc = 0    
        
        try:
            self.update()
        except:
            pass
        for folder in folders:
            if self.progress_bar:
                self.progress_bar.setValue(inc)
                inc += 1
            
            self._add_process_item(folder, folder=True, find_parent_path=False)#create = True, folder = True)
        try:
            self.update()
        except:
            pass
        
        if self.progress_bar:
            self.progress_bar.reset()
            self.progress_bar.hide()

    def _add_process_items(self, item, path):
        
        parts, folders = process.find_processes(path, return_also_non_process_list=True)
        
        self.directory
        sub_path = util_file.remove_common_path_simple(self.directory, path)
        
        if self.progress_bar:
            self.progress_bar.show()
            self.progress_bar.reset()
            self.progress_bar.setRange(0, len(parts))
            inc = 0
        
        #self.setUpdatesEnabled(False)
        for part in parts:
            
            if self.progress_bar:
                self.progress_bar.setValue(inc)
                inc += 1
            
            if sub_path:
                part = util_file.join_path(sub_path, part)
                self._add_process_item(part, item, find_parent_path = False)
            if not sub_path:
                self._add_process_item(part, item, find_parent_path = False)

        if self.progress_bar:
            self.progress_bar.reset()
            self.progress_bar.setRange(0, len(folders))
            inc = 0
        
        try:
            self.update()
        except:
            pass
        
        for folder in folders:
            
            if self.progress_bar:
                self.progress_bar.setValue(inc)
                inc += 1
            
            if sub_path:
                folder = util_file.join_path(sub_path, folder)
                self._add_process_item(folder, item, create = False, find_parent_path = False, folder = True)
            if not sub_path:
                self._add_process_item(folder, item, create = False, find_parent_path = False, folder = True)
        
        try:         
            self.update()
        except:
            pass
        
        if self.progress_bar:
            self.progress_bar.reset()
            self.progress_bar.hide()
            
        
    def _add_process_item(self, name, parent_item = None, create = False, find_parent_path = True, folder = False):
        
        log.info('Adding process item: %s' % name)
        
        if name.find('/') > -1:
            find_parent_path = False
            
        expand_to = False
        
        items = self.selectedItems()
        
        current_item = None
        
        if items:
            current_item = items[0]
        
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
        
        if folder:
            item.set_folder(True)
        
        if create:
            item.create()
        
        is_child = False
        if parent_item or self.top_is_process:
            is_child = True
        
        if is_child and not folder:
            process_path = util_file.join_path(self.directory, name)
            enable = process.is_process_enabled(process_path)
            #enable = process_inst.is_enabled()
            if not enable and self.checkable:
                item.setCheckState(0, qt.QtCore.Qt.Unchecked )
            if enable and self.checkable:
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
        if item.has_parts():# and not folder:    
            qt.QTreeWidgetItem(item)

        if self._name_filter: 
            filter_name = str(self._name_filter)
            filter_name = filter_name.strip()
            if name.find(filter_name) == -1:
                self.setItemHidden(item, True)
        
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
        #not sure about this. If its good usability to have the parent selected when children collapsed
        items = self.selectedItems()
        
        current_item = None
        
        if items:
            current_item = items[0]
        
        if self._has_item_parent(current_item, item):
            self.setCurrentItem(item)
            self.setItemSelected(item, True)
    
    
    
    def _add_sub_items(self, item):
        
        log.debug('Add sub items')
        
        self._delete_children(item)
        
        path = ''
        
        if hasattr(item, 'get_name'):
            process_name = item.get_name()
            path = util_file.join_path(self.directory, process_name)
        
        self._handle_selection_change = False
        
        try:
            self._add_process_items(item, path)
        except:
            util.error(traceback.format_exc())
        
        self._handle_selection_change = True
        
    def _browse(self):
        
        path = self.directory
        
        if self.current_folder:
            parent_path = self._get_parent_path(self.current_folder)
            path = util_file.join_path(self.directory, parent_path)
            
        if not self.current_folder:
            items = self.selectedItems()
            
            if items:
                process = items[0].get_process()
                path = process.get_path()
        
        if path:
            util_file.open_browser(path)

    def refresh(self):
        
        processes, folders = process.find_processes(self.directory, return_also_non_process_list=True)
        
        #this can be slow when there are many processes at the top level, and it checks if each process has sub process.
        self._load_processes(processes, folders)
        
        self.current_item = None
        self.last_item = None
        
        self._goto_settings_process()
        
    def add_process(self, name):
        
        items = self.selectedItems()
        
        current_item = None
        
        if items:
            current_item = items[0]
        
        parent_item = None
        
        if not util_file.get_permission(self.directory):
            util.warning('Could not get permission in directory: %s' % self.directory)
        
        if name == '':
            path = self.directory
            
            if current_item:
                path = self.get_item_path_string(current_item)
                
                if path:
                    path = util_file.join_path(self.directory, path)
                
            if not util_file.get_permission(path):
                util.warning('Could not get permission in directory: %s' % path)
                return
                
            name = process.get_unused_process_name(path)
        
        parent_is_root = False
        
        if name == None:
            
            name = process.get_unused_process_name(self.directory)
            parent_item = self.invisibleRootItem()
            parent_is_root = True
        
        item = self._add_process_item(name, parent_item = parent_item, create = True)
        
        self.setCurrentItem(item)
        self.setItemSelected(item, True)
        if parent_is_root:
            self.scrollToItem(item, self.PositionAtCenter)
            
        parent_item = item.parent()
        
        if not util_file.is_dir(item.get_path()):
            self._item_remove(item)
            util.warning('Could not create process')
        else:
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
            self.setCurrentItem(self.invisibleRootItem())

    def paste_process(self, source_process = None):
        
        #these were needed to remove the paste option.
        #self.paste_action.setVisible(False)
        #self.paste_item = None
        
        if not source_process:
            
            copied = util.get_env('VETALA_COPIED_PROCESS')
            
            if copied:
                source_process = process.Process()
                source_process.set_directory(copied)
            else:
                return
        
        target_process = None
        
        items = self.selectedItems()
        
        target_item = None
        
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
        
        new_item = self._add_process_item(new_process.get_name(), target_item)
        
        #before here the item should expand. 
        #However if the item wasn't expanded already it won't select properly the new_item
        #this makes the next 3 lines seem to not do anything... not sure what qt is doing here.
        
        self.clearSelection()
        self.setCurrentItem(self.invisibleRootItem())
        new_item.setSelected(True)
        self.scrollToItem(new_item, self.PositionAtCenter)
        
            
        self.copy_process.emit()
        
        #if target_process.get_path() == self.directory:
        #    self.refresh()
        
    def merge_process(self, source_process = None, sub_process_merge = False):
        
        self.paste_action.setVisible(False)
        
        if not source_process:
            if not self.paste_item:
                return
            
            source_process = self.paste_item.get_process()
            
        source_process_name = source_process.get_name()
        
        merge_permission = qt_ui.get_permission('Are you sure you want to merge in %s?' % source_process_name)
        
        if not merge_permission:
            return
        
        target_process = None
        
        target_item = None
        
        items = self.selectedItems()
        if items:
            target_item = items[0]
            target_process = target_item.get_process()            
        if not items:
            target_item = None
        
        if not target_process:
            return 
        
        process.copy_process_into(source_process, target_process, merge_sub_folders  = sub_process_merge)
        
        if target_item:
            
            target_item.setExpanded(False)
            
            if target_process.get_sub_processes():
                
                temp_item = qt.QTreeWidgetItem()
                target_item.addChild(temp_item)
        
        self.copy_process.emit()
    
    def merge_with_sub_process(self, source_process = None):
        
        self.merge_process(source_process, sub_process_merge = True)
    
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
    
    def set_deactivate_modifiers(self, bool_value):
        
        self.deactivate_modifiers = bool_value
    
    def set_directory(self, directory, refresh=True, sub_path = '', name_filter = ''):
        
        self.project_dir = directory
        self.sub_path = sub_path
        
        if sub_path:
            directory = util_file.join_path(directory, self.sub_path)
        
        super(ProcessTreeWidget, self).set_directory(directory, refresh=refresh, name_filter = name_filter)
        
        
    
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
        
        self.setSizeHint(0, qt.QtCore.QSize(40,18))
        
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
                process.set_enabled(False)
                #process.set_setting('enable', False)
            if value == 2:
                process.set_enabled(True)
                #process.set_setting('enable', True)
        
    def _get_process(self):
        
        if self.process:
            
            if self.process.process_name == self.name and self.process.directory == self.directory:
                return self.process
        
        process_instance = process.Process(self.name)
        process_instance.set_directory(self.directory)
        
        self.process = process_instance
        
        return process_instance
        
    def _get_parent_process(self):
        
        process_instance = self._get_process()
        parent_process = process_instance.get_parent_process()
        
        return parent_process
        
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
    
    def get_parent_process(self):
        return self._get_parent_process()
        
    def get_path(self):
        
        process_instance = self._get_process()
        
        return process_instance.get_path()
    
    def get_name(self):
        
        process_instance = self._get_process()
        
        return process_instance.process_name
    
    def has_parts(self):
        
        process_path = util_file.join_path(self.directory, self.name)

        processes, folders = process.find_processes(process_path, return_also_non_process_list = True, stop_at_one = True)
        
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
            
            self.setForeground(0, qt.QtCore.Qt.darkGray)
            
        if not bool_value:
            self.setIcon(0, qt.QIcon())
            flags = qt.QtCore.Qt.ItemIsDragEnabled | qt.QtCore.Qt.ItemIsSelectable | qt.QtCore.Qt.ItemIsDropEnabled | qt.QtCore.Qt.ItemIsUserCheckable
            self.setFlags( flags )
            self.setCheckState(0, qt.QtCore.Qt.Unchecked)
            self.setDisabled(False)
            
            self.setData(0, qt.QtCore.Qt.ForegroundRole, None)
            
        
    def is_folder(self):
        return self._folder
    
class CopyWidget(qt_ui.BasicWidget):
    
    canceled = qt_ui.create_signal()
    pasted = qt_ui.create_signal()
    
    def __init__(self, parent = None, show_others = True):
        
        self.process = None
        self.other_process = None
        self.other_processes = []
        self._show_others_create = show_others
        
        super(CopyWidget, self).__init__(parent)
        self.setWindowTitle('Copy Match')
        self.setWindowFlags(qt.QtCore.Qt.WindowStaysOnTopHint)
        self.setMinimumWidth(500)
        
        alpha = 50
        
        if util.is_in_maya():
            alpha = 100
        
        self.yes_brush = qt.QBrush()
        self.yes_brush.setColor(qt_ui.yes_color)
        self.yes_brush.setStyle(qt.QtCore.Qt.SolidPattern)
    
        self.no_brush = qt.QBrush()
        self.no_brush.setColor(qt_ui.no_color)
        self.no_brush.setStyle(qt.QtCore.Qt.SolidPattern)
        
        self.update_on_select = True
    
    def _build_widgets(self):
        
        self.tabs = qt.QTabWidget()
        
        self.data_list = DataTree()
        self.code_list = CodeTree()
        self.option_list = ProcessInfoTree()
        self.settings_list = ProcessInfoTree()
        
        
        v_side_bar = qt.QVBoxLayout()
        
        if self._show_others_create:
            self.show_view = qt.QPushButton('Show Others') 
            self.show_view.clicked.connect(self._show_others)
        
        load_button = qt.QPushButton('Compare')
        self.view = ProcessTreeWidget(checkable = False)
        self.view.set_deactivate_modifiers(False)
        
        v_side_bar.addWidget(self.view)
        v_side_bar.addWidget(load_button)
        
        self.side_bar = qt.QWidget()
        self.side_bar.setLayout(v_side_bar)
        self.side_bar.hide()
        self.side_bar.setMaximumWidth(250)
        
        
        load_button.clicked.connect(self._load_other)
        
        
        self.view.disable_right_click = True
        
        self._update_view = False
        self._skip_selection_change = False
        
        self.view.selection_changed.connect(self._process_selection_changed)
        self.view.setSelectionMode(self.view.ContiguousSelection)
        
        self.view.setDragEnabled(False)
        
        
        
        self.code_list.itemSelectionChanged.connect(self._code_selected)
        
        self.tabs.addTab(self.data_list, 'Data')
        self.tabs.addTab(self.code_list, 'Code')
        self.tabs.addTab(self.option_list, 'Options')
        self.tabs.addTab(self.settings_list, 'Settings')
        
        h_main_layout = qt.QHBoxLayout()
        
        h_main_layout.addWidget(self.tabs)
        h_main_layout.addWidget(self.side_bar)
        
        h_layout = qt.QHBoxLayout()
        
        self.paste_button = qt.QPushButton('Paste')
        self.paste_button.setDisabled(True)
        self.paste_button.clicked.connect(self._paste)
        cancel = qt.QPushButton('Cancel')
        
        self.paste_button.clicked.connect(self.pasted)
        cancel.clicked.connect(self._cancelled)
        
        h_layout.addWidget(self.paste_button)
        h_layout.addWidget(cancel)
        if self._show_others_create:
            h_layout.addWidget(self.show_view)
        
        self.progress_bar = qt.QProgressBar()
        self.progress_bar.hide()
        
        self.main_layout.addLayout(h_main_layout)
        
        self.main_layout.addWidget(self.progress_bar)
        self.main_layout.addLayout(h_layout)
        
    def _process_selection_changed(self):
        
        if self._skip_selection_change:
            return
        
        if not self._update_view:
            return
        
        items = self.view.selectedItems()
        
        process_name = self.process.get_name()
        
        deselect = []
        
        self.other_processes = []
        for item in items:
            name =  item.get_name()
            
            project_path = self.view.directory
            
            if name.startswith('/'):
                name = name[1:]
            
            if process_name.startswith('/'):
                process_name = process_name[1:]
            
            if process_name == name:
                
                deselect.append(item)
                continue
            
            other_process_inst = process.Process(name)
            other_process_inst.set_directory(project_path)
            
            self.other_processes.append(other_process_inst)
            
        self._skip_selection_change = True
        for item in deselect:
            item.setSelected(False)
        self._skip_selection_change = False
        
    
    def _show_others(self):
        
        if self.side_bar.isVisible():
            self._update_view = True
            self.side_bar.hide()
            self.show_view.setText('Show Others')
            return 
        
        if not self.side_bar.isVisible():
            self._update_view = True
            self.view.set_directory(self.process.directory)
            self.side_bar.show()
            self.show_view.setText('Hide Others')
            return
        
    def _load_other(self):
        
        self.populate_other()
        
    def _code_selected(self):
        
        if not self.update_on_select:
            return
        
        selected = self.code_list.selectedItems()
        
        if not selected:
            return
        
        self.update_on_select = False
        
        for item in selected:
            
            parent_item = item.parent()
            
            while parent_item:
                columns =  parent_item.columnCount()
                
                found = False
                
                for inc in range(1, columns+1):
                    parent_text = parent_item.text(inc)
                    if parent_text.find('-') > -1:
                        found = True
                        break
                
                if found:
                    if not parent_item.isSelected():
                        parent_item.setSelected(True)
                    
                parent_item = parent_item.parent()
        
        self.update_on_select = True
        

        
    def _get_long_name(self, item):
        
        current_item = item
        append_name = ''
        name = item.text(0)
        
        while current_item.parent():
            
            parent_item = current_item.parent()
            append_name = parent_item.text(0)
            
            name = append_name + '/' + name
            
            current_item = parent_item
        
        return name
    
    def _get_option_long_name(self, item):
        
        long_name = self._get_long_name(item)
        
        long_name = long_name.replace('/', '.')
        
        if hasattr(item, 'group'):
            if item.group:
                long_name += '.'
        
        return long_name
        
    def _cancelled(self):
        self.close()
        self.canceled.emit()
        
    def _populate_lists(self):
        
        self.progress_bar.reset()
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 4)
        
        current_tab = self.tabs.currentIndex()
        
        self.clear_lists()
        
        self.populate_data_list()
        self.progress_bar.setValue(1)
        
        self.populate_code_list()
        self.progress_bar.setValue(2)
        
        self.populate_option_list()
        self.progress_bar.setValue(3)
        
        self.populate_settings_list()
        self.progress_bar.setValue(4)
        
        self.tabs.setCurrentIndex(current_tab)
        
        
        self.progress_bar.setVisible(False)

    def _fill_headers(self, list_inst):
        
        name = self.process.get_name()
                
        list_inst.setHeaderLabels([name, 'Target'])

        others = []
        
        if not self.other_processes:
            return
                
        other_process_count = len(self.other_processes)

        for inc in range(0, other_process_count):
    
            other_process = self.other_processes[inc]
    
            others.append(other_process.get_name())
            
            list_inst.header().showSection(inc+1)
            
        labels = [name]
        labels += others
        
        list_inst.setHeaderLabels(labels)
        
        header_count = list_inst.header().count()
        
        if (header_count-1) > other_process_count:
        
            for inc in range(other_process_count+1, header_count):
                
                list_inst.header().hideSection(inc)
    

    def _fill_all_headers(self):
        
        self._fill_headers(self.data_list)
        self._fill_headers(self.code_list)
        self._fill_headers(self.settings_list)
        self._fill_headers(self.option_list)
                            
    def _set_item_state(self, item, value, column):
        
        if value:
            item.setText(column, 'Match')
            item.setBackground(column, self.yes_brush)
        
        if not value:
            item.setText(column, 'No Match')
            item.setBackground(column, self.no_brush)
        
        self.repaint()
            
    def _compare_data(self, other_process, data_name, sub_folder = None):
        
        source_data = self.process.get_data_instance(data_name)
        target_data = other_process.get_data_instance(data_name)
        
        if not source_data:
            return
        
        if not target_data:
            return
        
        source_file = source_data.get_file_direct(sub_folder = sub_folder)
        target_file = target_data.get_file_direct(sub_folder = sub_folder)
        
        orig_target_file = target_file
        
        if not target_file:
            return
        
        if not util_file.is_file(target_file):
            target_file = None
        
        same_content = False
        
        same = False
        
        if util_file.is_file(source_file) and target_file:
            
            same = filecmp.cmp(source_file, target_file)
            
        else:
            try:
                compare = filecmp.dircmp(source_file, orig_target_file)
                same = True
                
                if compare.subdirs:
                    for dir_inst in compare.subdirs:
                        if not compare.subdirs[dir_inst].diff_files:
                            same = True
                        else:
                            same = False
                            break
            except:
                if source_file:
                    if not orig_target_file:
                        same = False
                    else:
                        if not util_file.exists(source_file) and not util_file.exists(orig_target_file):
                            return True
                    
            
            
                
        return same   

    def _compare_code_children(self, item, column, other_process_inst, parent_name = None):
        
        if not parent_name:
            parent_name = item.text(0)
        
        for inc_child in range(0, item.childCount()):
            
            child_item = item.child(inc_child)
            
                
            child_name = child_item.text(0)
            
            long_name = parent_name + '/' + child_name
            
            if not other_process_inst.is_code_folder(long_name):
                continue
            
            source_folder = self.process.get_code_file(long_name)
            target_folder = other_process_inst.get_code_file(long_name)
            
            same = False
            
            if source_folder != None and target_folder != None:
                same = filecmp.cmp(source_folder, target_folder)          
            #same = util_file.is_same_text_content(source_folder, target_folder)
            
            self._set_item_state(child_item, same, column)  
            
            self._compare_code_children(child_item, column, other_process_inst, long_name)
    
    def _compare_setting(self, process,other_process, long_name):
        
        value = process.get_setting(long_name)
        other_value = other_process.get_setting(long_name)
        
        if value == other_value:
            return True
        
        return False
          
    def _compare_option(self, process,other_process, long_name):
        
        value = process.get_unformatted_option(long_name)
        other_value = other_process.get_unformatted_option(long_name)
        
        if value == other_value:
            return True
        
        return False

    def _compare_option_children(self, item, column, other_process_inst, parent_name = None):
        
        if item.childCount() == 0:
            
            return
        
        if not parent_name:
            parent_name = item.text(0)
            parent_name += '.'
        
        for inc_child in range(0, item.childCount()):
            
            child_item = item.child(inc_child)
            
            child_name = child_item.text(0)
            
            long_name = parent_name + child_name
            
            if child_item.childCount() > 0:
                long_name += '.'
            
            if not other_process_inst.has_option(long_name):
                continue
            
            same = self._compare_option(self.process, other_process_inst, long_name)
            
            self._set_item_state(child_item, same, column)  
            
            self._compare_option_children(child_item, column, other_process_inst, long_name)  
            
    def _paste(self):
        
        self.progress_bar.setVisible(True)
        
        current_tab = self.tabs.currentIndex()
        
        
        if current_tab == 0:
        
            if self.data_list.selectedItems():
                self._paste_data()
            
        if current_tab == 1:
            if self.code_list.selectedItems():    
                self._paste_code()
            
        if current_tab == 2:
            if self.option_list.selectedItems():
                self._paste_options()
            
        if current_tab == 3:
            if self.settings_list.selectedItems():
                self._paste_settings()
        
        
        self.progress_bar.hide()
        
    def _paste_data(self):
        
        data_items = self.data_list.selectedItems()
        
        if not data_items:
            return
        
        inc = 0
        
        self.tabs.setCurrentIndex(0)
        
        self.progress_bar.reset()
        self.progress_bar.setRange(0, len(data_items))
        self.progress_bar.setValue(inc)
        
        for item in data_items:
            
            parent_item = item.parent()
            
            if parent_item:
                name = str(parent_item.text(0))
                folder_name = str(item.text(0))
            else:
                name = str(item.text(0))
                folder_name = ''
            
            for inc2 in range(0, len(self.other_processes)):
                
                other_process_inst = self.other_processes[inc2]
                
                process.copy_process_data( self.process, other_process_inst, name, sub_folder = folder_name)
            
                same = self._compare_data(other_process_inst, name, folder_name)
                
                self._set_item_state(item, same, inc2+1)
            
            self.progress_bar.setValue(inc)
            
            inc += 1
            
    def _paste_code(self):
        
        code_items = self.code_list.selectedItems()
    
        if not code_items:
            return
    
        self.tabs.setCurrentIndex(1)
    
        found = []
        item_dict = {}
        
        manifest = ''
        
        for item in code_items:
            
            name = self._get_long_name(item)
            
            if not name:
                continue
            
            if name == 'manifest':
                manifest = name
                item_dict[manifest] = item
                continue
            
            found.append(name)
            item_dict[name] = item

        self.progress_bar.reset()
        self.progress_bar.setRange(0, len(found))
            
        inc = 0
        
        if found:
            found_count = []
            
            for thing in found:
                found_count.append( thing.count('/') )
            
            sort = util.QuickSort(found_count)
            sort.set_follower_list(found)
            found_count, found = sort.run()
            
            #manifest needs to be added at the end so it gets synced
        if manifest:
            found.append(manifest)
        
        other_process = None
        states_to_set = []
        
        for inc2 in range(0, len(self.other_processes)):
            
            other_process = self.other_processes[inc2]
            
            for name in found:    
                
                process.copy_process_code( self.process, other_process, name)
                
                previous_script =  self.process.get_previous_script(name)
                
                if previous_script and other_process.has_script(previous_script[0]):
                    other_process.insert_manifest_below(name, previous_script[0], previous_script[1])
                else:
                    state = self.process.get_script_state(name)
                    states_to_set.append([name,state])
                
                source_folder = self.process.get_code_file(name)
                target_folder = other_process.get_code_file(name)
                
                same = util_file.is_same_text_content(source_folder, target_folder)
                item = item_dict[name]
                self._set_item_state(item, same, inc2+1)
            
            if other_process:
                other_process.sync_manifest()
                for setting in states_to_set:
                    other_process.set_script_state(setting[0], setting[1])
            self.progress_bar.setValue(inc)
            inc += 1
        
        
    def _paste_settings(self):
        
        setting_items = self.settings_list.selectedItems()
        
        if not setting_items:
            return
        
        self.tabs.setCurrentIndex(3)
        
        inc = 0
        
        self.progress_bar.reset()
        self.progress_bar.setRange(0, len(setting_items))
        
        for item in setting_items:
            name = str(item.text(0))
            
            value = self.process.get_setting(name)
            
            for inc2 in range(0, len(self.other_processes)):
                
                other_process = self.other_processes[inc2]
                
                other_process.set_setting(name, value)
            
                match = self._compare_setting(self.process, other_process, name)
                self._set_item_state(item, match, inc2+1)
            
            self.progress_bar.setValue(inc)
            inc+=1
    
    def _paste_options(self):
        
        option_items = self.option_list.selectedItems()
        
        if not option_items:
            return
        
        self.tabs.setCurrentIndex(2)
        
        inc = 0
        
        self.progress_bar.reset()
        self.progress_bar.setRange(0, len(option_items))
        
        option_items = self._sort_option_items(option_items)
        
        for item in option_items:            
            
            long_name = self._get_option_long_name(item)
            
            value = self.process.get_unformatted_option(long_name)
            
            for inc2 in range(0, len(self.other_processes)):
                
                other_process = self.other_processes[inc2]
                
                other_process.set_option(long_name, value)
                
                match = self._compare_option(self.process, other_process, long_name)
                self._set_item_state(item, match, inc2+1)
            
            self.progress_bar.setValue(inc)
            inc+=1
    
    def _sort_option_names(self, option_names):
        
        parents = []
        children = []
        
        for option in option_names:
            
            if option.find('.') > -1 and not option.endswith('.'):
                children.append(option)
            else:
                parents.append(option)
            
        options = parents + children 
        
        return options  
    
    def _sort_option_items(self, option_items):
        
        option_names = []
        option_item_dict = {}
        
        for option_item in option_items:
            item_name = self._get_option_long_name(option_item)
            option_names.append(item_name)
            option_item_dict[item_name] = option_item
            
        options = self._sort_option_names(option_names)
        
        found = []
        
        for name in options:
            found.append(option_item_dict[name])
        
        return found     
    
    def _sort_process_options(self, options):
        
        options_dict = {}
        option_names = []
        
        for option in options:
            option_names.append(option[0])
            options_dict[option[0]] = option
            
        option_names = self._sort_option_names(option_names)
        
        found = []
        
        for option_name in option_names:
            found.append(options_dict[option_name])
            
        return found
          
    def _reset_states(self, tree, column = 1):
        
        root = tree.invisibleRootItem()
        
        self._reset_item_children(column, root)
        
    
    def _reset_item_children(self, column, item):
        
        child_count = item.childCount()
        
        for inc in range(0, child_count):
            
            child_item = item.child(inc)
            
            self._reset_compare_columns(column, child_item)
            
            self._reset_item_children(column, child_item)
        

  
    def _reset_compare_columns(self, column, item):
        
        item.setText(column, (' ' * 10) + '-')
        
        item.setBackground(column, item.background(0))
            
    def clear_lists(self):
        
        self.data_list.clear()
        self.code_list.clear()
        self.option_list.clear()
        self.settings_list.clear()
        

    def reset_list_compare(self):
        
        self._reset_states(self.data_list)
        self._reset_states(self.code_list)
        self._reset_states(self.settings_list)

    def populate_list(self, column, list_widget, data):
        
        for sub_data in data:
            
            list_widget.add_item(column, sub_data)

    def populate_code_list(self):
             
        self.tabs.setCurrentIndex(1)
        
        self.code_list.set_process(self.process)
        self.code_list.populate()
        
    def populate_data_list(self):
        
        self.tabs.setCurrentIndex(0)
        
        self.data_list.set_process(self.process)
        self.data_list.populate()
    
    def populate_settings_list(self):
        
        self.tabs.setCurrentIndex(3)
        
        settings_inst = self.process.get_settings_inst()
                
        column = 0
        
        list_widget = self.settings_list
        
        settings_list = settings_inst.get_settings()
        
        for setting in settings_list:
            
            list_widget.add_item(column, setting[0])
        
        
        if not settings_list:
            list_widget.add_item(column, 'No Settings')    


            
    def populate_option_list(self):
        
        self.tabs.setCurrentIndex(2)
        
        options = self.process.get_options()
        
        column = 0
        
        list_widget = self.option_list
        
        options = self._sort_process_options(options)
        
        parent_items = {}
        for option in options:
            
            option_name = option[0]
            
            parent_item = None
            
            split_name = option_name.split('.')
            item_name = split_name[-1]
            
            if not item_name:
                item_name = split_name[-2]
            
            if option_name.find('.') > -1:
                
                if option_name.endswith('.'):
                    split_name = split_name[:-1]
                
                parent = string.join(split_name[:-1], '.')
                parent += '.'
                
                if parent_items.has_key(parent):
                    
                    parent_item = parent_items[parent]
                    
            item = list_widget.add_item(column, item_name, parent_item)
            
            item.group = False
            
            test_option = None
            
            if type(option[1]) == list and len(option[1]) > 1:
                test_option = option[1][1]
            
            if option_name.endswith('.') and not parent_items.has_key(option_name):
                if test_option != 'reference.group':
                    parent_items[option_name] = item
                
                item.group = True
            
        
        if not options:
            list_widget.add_item(column, 'No Options')                
    
    
    def populate_other(self):
        
        self._fill_all_headers()
        
        other_count = len(self.other_processes)
        
        current_tab = self.tabs.currentIndex()
        
        populators = [self.populate_other_data, 
                      self.populate_other_code, 
                      self.populate_other_options, 
                      self.populate_other_settings]
        
        for populator in populators:
            for inc in range(0, other_count):
                
                other_process_inst = self.other_processes[inc]
                
                path = other_process_inst.get_path()
                
                if not util_file.get_permission(path):
                    continue
                
                populator(inc+1, other_process_inst)
                #self.populate_other_data(inc+1, other_process_inst)
                #self.populate_other_code(inc+1, other_process_inst)
                #self.populate_other_options(inc+1, other_process_inst)
                #self.populate_other_settings(inc+1, other_process_inst)
        
        self.paste_button.setEnabled(True)
        
        self.tabs.setCurrentIndex(current_tab)
        
    def populate_other_data(self, column, other_process_inst):
        
        self.tabs.setCurrentIndex(0)
        
        self._reset_states(self.data_list, column)
        
        data = other_process_inst.get_data_folders()
        
        list_widget = self.data_list
        
        count = list_widget.topLevelItemCount()
        
        self.progress_bar.reset()
        self.progress_bar.setVisible(True)
        
        self.progress_bar.setValue(0)
        self.progress_bar.setRange(0, count)
        
        for inc in range(0, count):
            
            self.progress_bar.setValue(inc)
            
            item = list_widget.topLevelItem(inc)
            
            for sub_data in data:
                
                if item.text(0) == sub_data:
                    
                    same = self._compare_data(other_process_inst, sub_data)
                    
                    self._set_item_state(item, same, column)
                    
                    other_sub_folders = other_process_inst.get_data_sub_folder_names(sub_data)
                    
                    for inc_child in range(0, item.childCount()):
                        
                        child_item = item.child(inc_child)
                        
                        sub_folder = child_item.text(0)
                        
                        for other_sub_folder in other_sub_folders:
                            
                            if other_sub_folder == sub_folder:
                                
                                same = self._compare_data(other_process_inst, sub_data, child_item.text(0))
                                self._set_item_state(child_item, same, column)    
                    
                    model_index = list_widget.indexFromItem(item, column=0)
                    list_widget.scrollTo(model_index)   
        
        self.progress_bar.setVisible(False)
         
    def populate_other_code(self, column, other_process_inst):
        
        self.tabs.setCurrentIndex(1)
        
        self._reset_states(self.code_list, column)
        
        code_names = other_process_inst.get_code_names()
                
        list_widget = self.code_list
        
        count = list_widget.topLevelItemCount()
        
        self.progress_bar.setValue(0)
        self.progress_bar.setRange(0, count)
        
        for inc in range(0, count):
            
            self.progress_bar.setValue(inc)
            
            item = list_widget.topLevelItem(inc)
            
            for code_name in code_names:
                
                long_name = self._get_long_name(item)
                
                if long_name == code_name:
                    
                    source_file = self.process.get_code_file(code_name)
                    target_file = other_process_inst.get_code_file(code_name)
                                        
                    if util_file.is_file(target_file) and util_file.is_file(source_file):
                        same = util_file.is_same_text_content(source_file, target_file)
                    else:
                        same = False
                    self._set_item_state(item,same, column)
                    self._compare_code_children(item, column, other_process_inst)
                        
    def populate_other_settings(self, column, other_process_inst):
        
        self.tabs.setCurrentIndex(2)
        
        settings_inst = self.process.get_settings_inst()
        
        other_settings_inst = other_process_inst.get_settings_inst()
        other_settings = other_settings_inst.get_settings()
        
        self._reset_states(self.settings_list, column)
        
        list_widget = self.settings_list
        
        count = list_widget.topLevelItemCount()
        
        self.progress_bar.setValue(0)
        self.progress_bar.setRange(0, count)
                
        for inc in range(0, count):
        
            self.progress_bar.setValue(inc)
            
            item = list_widget.topLevelItem(inc)
            
            if str(item.text(0)) == 'No Settings':
                return
            
            for other_setting in other_settings:
                
                setting_name = item.text(0)
                
                if setting_name == other_setting[0]:
                    
                    value = settings_inst.get(setting_name)
                    other_value = other_settings_inst.get(setting_name)
                    
                    match = False
                    
                    if value == other_value:
                        match = True
                    
                    self._set_item_state(item, match, column)
    
    def populate_other_options(self, column, other_process_inst):
        
        self.tabs.setCurrentIndex(2)
        
        other_options = other_process_inst.get_options()
        
        self._reset_states(self.option_list, column)
        
        list_widget = self.option_list
        
        count = list_widget.topLevelItemCount()
        
        self.progress_bar.setValue(0)
        self.progress_bar.setRange(0, count)
        
        for inc in range(0, count):
        
            self.progress_bar.setValue(inc)
            
            item = list_widget.topLevelItem(inc)
            
            option_name = str(item.text(0))
            
            if option_name == 'No Options':
                return
            
            option_long_name = self._get_option_long_name(item)
            
            for other_option in other_options:
                
                if option_long_name == other_option[0]:
                    
                    match = self._compare_option(self.process, other_process_inst, option_name)
                    
                    self._set_item_state(item, match, column)
                    
                    self._compare_option_children(item, column, other_process_inst)


    def set_process(self, process_name, process_directory):
        
        process_inst = process.Process(process_name)
        process_inst.set_directory(process_directory)
        
        self.process = process_inst
                
        self._populate_lists()
                
        self._fill_all_headers()
        
        
        
    def set_other_process(self, process_name, process_directory):
        
        
        
        if not self.process:
            return
        
        if not self.isVisible():
            return
        
        self.progress_bar.reset()
        self.progress_bar.setVisible(True)
        
        process_inst = process.Process(process_name)
        process_inst.set_directory(process_directory)
        
        self.other_processes = [process_inst]
                
        self.load_compare()
        
        
    def load_compare(self):
        
        current_tab_index = self.tabs.currentIndex()
        
        if not self.other_processes:
            return
        
        self.populate_other()

        self.progress_bar.setVisible(False)
        
        self.tabs.setCurrentIndex(current_tab_index)
        
class ProcessInfoTree(qt.QTreeWidget):
    
    def __init__(self):
        
        self.process = None
        
        super(ProcessInfoTree, self).__init__()
        
        self.setHeaderLabels(['Source'])
        header = self.header()
        if qt.is_pyside() or qt.is_pyqt():
            header.setResizeMode(qt.QHeaderView.ResizeToContents)
        if qt.is_pyside2():
            header.setSectionResizeMode(qt.QHeaderView.ResizeToContents)
        
        self.setSelectionMode(self.ExtendedSelection)
        
        item_delegate = qt_ui.SelectTreeItemDelegate()
        self.setItemDelegate(item_delegate)
        
        
    def add_item(self, column, name, parent = None):
        
        item = qt.QTreeWidgetItem(parent)
        
        item.setText(column, name)
        
        
        column_count = self.columnCount()
        
        if column_count > 1:
            
            for inc in range(1, column_count):
                item.setText(inc, (' ' * 10) + '-')
        
        self.addTopLevelItem(item)
        
        
        if parent:
            parent.setExpanded(True)
        return item
    
    def populate(self):
        pass
    
    def set_process(self, process_inst):
        self.process = process_inst

class VersionInfoTree(qt.QTreeWidget):

    def __init__(self):
        
        self.process = None
        
        super(VersionInfoTree, self).__init__()
        
        self.setContextMenuPolicy(qt.QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._item_menu)
        
        self.context_menu = qt.QMenu()
        self._create_context_menu()
        
    def _item_menu(self, position):
        
        self.current_folder = None
        
        self.context_menu.exec_(self.viewport().mapToGlobal(position))
                                
    def _create_context_menu(self):
        
        self.remove_all = self.context_menu.addAction('Remove all but last version')
        self.remove_all_but_10 = self.context_menu.addAction('Remove all but last 10 versions')

        self.remove_all.triggered.connect(self._remove_all)
        self.remove_all_but_10.triggered.connect(self._remove_all_but_10)

    def _remove(self, keep = 1):
        
        if hasattr(self, 'tree_type'):
            tree_type = self.tree_type
        
        items = self.selectedItems()
        
        for item in items:
        
            name = item.text(0)
            
            if tree_type == 'data':
                
                parent_item = item.parent()
                
                sub_folder = None
                if parent_item:
                    sub_folder = name
                    name = parent_item.text(0)
                    
                self.process.remove_data_versions(name, sub_folder, keep = keep)
                
            if tree_type == 'code':
                
                parent_item = item.parent()
                
                while parent_item:
                    
                    parent_name = parent_item.text(0) 
                    name = util_file.join_path(parent_name, name)
                    
                    parent_item = parent_item.parent()
                
                self.process.remove_code_versions(name, keep = keep)
                    
                
        self.populate()
                
    def _remove_all(self):
        
        
        self._remove()
    
    def _remove_all_but_10(self):
        self._remove(10)

    def _set_version_info(self, item, folder):
        version_inst = util_file.VersionFile(folder)
        count = version_inst.get_count()
        size = util_file.get_folder_size(folder, round_value = 3)
        
        item.setText(1, str(count))
        item.setText(2, str(size))


class DataTree(ProcessInfoTree):
    
    tree_type = 'data'
    
    def __init__(self):
        super(DataTree, self).__init__()
        
        self.setSortingEnabled(True)
        
        header = self.header()
        header.setSortIndicator(0,qt.QtCore.Qt.AscendingOrder)
        self.setHeader(header)
        
    def populate(self):
        
        self.clear()
        column = 0   
        data_folders = self.process.get_data_folders()
        
        if not data_folders:
            return 
        
        data_folders.sort()
        
        for sub_data in data_folders:
            
            data_item = self.add_item(column, sub_data)
            
            folders = self.process.get_data_sub_folder_names(sub_data)
            
            for folder in folders:
                self.add_item(column, folder, data_item)
                
                

class DataVersionTree(ProcessInfoTree, VersionInfoTree):
    
    tree_type = 'data'
    
    def populate(self):
            
            self.clear()
            column = 0   
            data_folders = self.process.get_data_folders()
            
            if not data_folders:
                return 
            
            data_folders.sort()
            
            for sub_data in data_folders:
                
                data_item = self.add_item(column, sub_data)
                
                
                data_folder = self.process.get_data_folder(sub_data)
                
                self._set_version_info(data_item, data_folder)
                
                folders = self.process.get_data_sub_folder_names(sub_data)
                
                for folder in folders:
                    sub_item = self.add_item(column, folder, data_item)
                    
                    data_folder = self.process.get_data_folder(sub_data, folder)
                    
                    self._set_version_info(sub_item, data_folder)

class CodeTree(ProcessInfoTree):
    
    tree_type = 'code'
    
    def populate(self):
        self.clear()
        column = 0
        
        code_names = self.process.get_code_names()
        
        items = {}
        
        for code_name in code_names:
            
            split_code_name = code_name.split('/')
            
            long_name = ''
            parent_item = None
            
            for name in split_code_name:
                
                if long_name:
                    long_name += '/%s' % name
                else:
                    long_name = name 
                
                if not items.has_key(long_name):
                    item = self.add_item(column, name, parent_item)
                else:
                    item = items[long_name]
                    
                items[long_name] = item
                parent_item = item
                
                

class CodeVersionTree(ProcessInfoTree, VersionInfoTree):

    tree_type = 'code'
    
    def populate(self):
        self.clear()
        column = 0
        
        code_names = self.process.get_code_names()
        
        items = {}
        
        for code_name in code_names:
            
            split_code_name = code_name.split('/')
            
            long_name = ''
            parent_item = None
            
            for name in split_code_name:
                
                if long_name:
                    long_name += '/%s' % name
                else:
                    long_name = name 
                
                if not items.has_key(long_name):
                    item = self.add_item(column, name, parent_item)
                else:
                    item = items[long_name]
                    
                items[long_name] = item
                parent_item = item
     
                folder = self.process.get_code_folder(long_name)
                
                self._set_version_info(item, folder)

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
        
    
    def index(self, row, column, parent):
        
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
    
    
