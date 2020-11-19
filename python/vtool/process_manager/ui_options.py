# Copyright (C) 2016 Louis Vottero louis.vot@gmail.com    All rights reserved.

import string

from vtool import qt_ui, qt
from vtool.process_manager import ui_code
from vtool import util
from vtool import util_file

import vtool.process_manager.process as process_module

from vtool import logger
log = logger.get_logger(__name__) 

class ProcessOptionsWidget(qt_ui.BasicWidget):
    
    edit_mode_change = qt_ui.create_signal(object)
    
    def __init__(self):
        self.directory = None
        self.process_inst = None
        
        super(ProcessOptionsWidget, self).__init__()
        
        policy = self.sizePolicy()
        policy.setHorizontalPolicy(policy.Expanding)
        policy.setVerticalPolicy(policy.Expanding)
        self.main_layout.setContentsMargins(0,0,0,0)
        self.setSizePolicy(policy)
        
    def _build_widgets(self):
        
        button_layout = qt.QHBoxLayout()
        
        self.edit_mode_button = qt.QPushButton('Edit')
        self.edit_mode_button.setCheckable(True)
        self.edit_mode_button.setMaximumWidth(100)
        self.edit_mode_button.setMaximumHeight(20)
        self.edit_mode_button.setMaximumWidth(40)
        
        
        self.option_scroll = ProcessOptionScroll()
        self.option_palette = ProcessOptionPalette()
        self.option_scroll.setWidget(self.option_palette)
        
        self.edit_options = EditOptions()
        self.edit_options.setVisible(False)
        
        self.edit_options.move_up.clicked.connect(self.move_up)
        self.edit_options.move_dn.clicked.connect(self.move_dn)
        self.edit_options.remove.clicked.connect(self.remove)
        
        self.edit_mode_button.toggled.connect(self._edit_click)
        
        history_widget = self._create_history_widget()
        
        button_layout.addWidget(history_widget)
        button_layout.addSpacing(10)
        button_layout.addWidget(self.edit_mode_button, alignment = qt.QtCore.Qt.AlignRight)
        
        self.main_layout.addWidget(self.option_scroll)
        self.main_layout.addWidget(self.edit_options)
        self.main_layout.addLayout(button_layout)
    
    def _create_history_widget(self):
        
        history_widget = qt_ui.CompactHistoryWidget()
        history_widget.set_auto_accept(True)
        history_widget.back_socket.connect(self._set_current_option_history)
        history_widget.forward_socket.connect(self._set_current_option_history)
        history_widget.load_default_socket.connect(self._load_option_default)
        history_widget.accept_socket.connect(self._accept_changes)
        
        #self.option_palette.value_change.connect(history_widget.set_at_end)
        
        self.history_widget = history_widget
        
        if self.process_inst:
            version_history = self.process_inst.get_option_history()
            self.history_widget.set_history(version_history)
        
        return history_widget
    
    def _accept_changes(self):
        
        self.option_palette.save()
    
    def _set_histroy(self):
        if self.process_inst:
            version_history = self.process_inst.get_option_history()
            self.history_widget.set_history(version_history)
    
    def _set_current_option_history(self, version_file):
        
        if version_file == 'current':
            self._load_current_history()
            return
        
        if not self.history_widget:
            return
        
        if version_file:
            self.option_palette.set_options_file(version_file)
            
    def _load_option_default(self, default_version_file):
        
        if not self.history_widget:
            return
        
        if default_version_file:
            self.option_palette.set_options_file(default_version_file)
       
    def _load_current_history(self):
        
        if self.process_inst:
            
            self.option_palette.set_process(self.process_inst)
            
    def _edit_click(self, bool_value):
        
        
        self._edit_activate(bool_value)
        self.edit_mode_change.emit(bool_value)
        
    def _edit_activate(self, bool_value):
        
        self.edit_options.setVisible(bool_value)
        
        ProcessOptionPalette.edit_mode_state = bool_value
        ProcessOption.edit_mode_state = bool_value
        
        self.option_palette.set_activate_edit(bool_value)
        
        if bool_value == False:
            self.option_palette.clear_selection()
    
    def set_directory(self, directory):
        
        if directory == None:
            raise
        
        
        process_inst = process_module.Process()
        process_inst.set_directory(directory)
        
        self.process_inst = process_inst
        
        self._set_histroy()
        
        self.directory = directory
        self.option_palette.set_process(process_inst)
        
    def has_options(self):
        
        if not self.directory:
            return False
        
        return self.option_palette.has_options()
    
    def move_up(self):
        
        widgets = ProcessOptionPalette.current_widgets
        widgets = self.option_palette.sort_widgets( widgets, widgets[0].get_parent())
        
        if not widgets:
            return
        
        for widget in widgets:
            widget.move_up()
    
    def move_dn(self):
        widgets = ProcessOptionPalette.current_widgets
        
        if widgets:
            widgets = self.option_palette.sort_widgets( widgets, widgets[0].get_parent())
        
        if not widgets:
            return
        
        widgets.reverse()
        
        for widget in widgets:
            widget.move_down()
        
    def remove(self):
        
        widgets = ProcessOptionPalette.current_widgets
        widgets = self.option_palette.sort_widgets( widgets, widgets[0].get_parent())
        
        if not widgets:
            return
        
        for widget in widgets:
            widget.remove()

class ProcessOptionScroll(qt.QScrollArea):
    def __init__(self):
        super(ProcessOptionScroll, self).__init__()
        
        self.setWidgetResizable(True)
        self.setMinimumWidth(100)
        self.setFocusPolicy(qt.QtCore.Qt.NoFocus)
    
class EditOptions(qt_ui.BasicWidget):
    
    def __init__(self):
        super(EditOptions, self).__init__()
        
        self.setWindowTitle('Edit Options')
    
    def _define_main_layout(self):
        return qt.QHBoxLayout()
    
    def _build_widgets(self):
        
        self.move_up = qt.QPushButton('Move Up')
        self.move_dn = qt.QPushButton('Move Dn')
        self.remove = qt.QPushButton('Remove')
        
        self.main_layout.addWidget(self.move_up)
        self.main_layout.addWidget(self.move_dn)
        self.main_layout.addWidget(self.remove)
        
        self.setWindowFlags(qt.QtCore.Qt.WindowStaysOnTopHint)
    
        
class ProcessOptionPalette(qt_ui.BasicWidget):
    
    widget_to_copy = None
    current_widgets = []
    last_widget = None
    edit_mode = qt_ui.create_signal(object)
    edit_mode_state = False
    value_change = qt_ui.create_signal()
    
    def __init__(self):
        super(ProcessOptionPalette, self).__init__()
        
        self.main_layout.setContentsMargins(1,1,1,0)
        self.main_layout.setSpacing(1)
        self.setSizePolicy(qt.QSizePolicy(qt.QSizePolicy.MinimumExpanding, qt.QSizePolicy.MinimumExpanding))
        
        self.directory = None
        self.process_inst = None
        
        self.supress_update = False
        self.central_palette = self
        
        self.widget_to_copy = None
        
        self.setContextMenuPolicy(qt.QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._item_menu)
        
        self._create_context_menu()
        
        self.disable_auto_expand = False
        self.has_first_group = False
        
        self._auto_rename = True
        
        self.top_parent = self
        if not hasattr(self, 'ref_path'):
            self.ref_path = None
        
    def _item_menu(self, position):
        
        widget = self.childAt(position)
        
        if self._is_child_of_ref_widget(widget):
            return
        
        if not ProcessOptionPalette.edit_mode_state:
            return
        
        if ProcessOptionPalette.widget_to_copy:
            self.paste_action.setVisible(True)
        
        self.menu.exec_(self.mapToGlobal(position))
        
    def _create_context_menu(self):
        
        self.menu = qt.QMenu()
        
        create_menu = self.menu.addMenu('Create')
        create_menu.setTitle('Add Options')
        create_menu.setTearOffEnabled(True)
        
        add_title = create_menu.addAction('Add Title')
        add_title.triggered.connect(self.add_title)
        
        add_note = create_menu.addAction('Add Note')
        add_note.triggered.connect(self.add_note)
        
        self.add_string = create_menu.addAction('Add String')
        self.add_string.triggered.connect(self.add_string_option)
        
        add_number = create_menu.addAction('Add Number')
        add_number.triggered.connect(self.add_number_option)
        
        add_integer = create_menu.addAction('Add Integer')
        add_integer.triggered.connect(self.add_integer_option)
        
        add_boolean = create_menu.addAction('Add Boolean')
        add_boolean.triggered.connect(self.add_boolean_option)
        
        add_dictionary = create_menu.addAction('Add Dictionary')
        add_dictionary.triggered.connect(self.add_dictionary)
        
        add_group = create_menu.addAction('Add Group')
        add_group.triggered.connect(self.add_group)
        
        add_ref_group = create_menu.addAction('Add Reference Group')
        add_ref_group.triggered.connect(self.add_ref_group)
        
        add_script = create_menu.addAction('Add Script')
        add_script.triggered.connect(self.add_script)
        
        self.create_separator = self.menu.addSeparator()
        
        self.copy_action = self.menu.addAction('Copy')
        self.copy_action.triggered.connect(self._copy_widget)
        self.copy_action.setVisible(False)
        
        self.paste_action = self.menu.addAction('Paste')
        self.paste_action.setVisible(False)
        self.paste_action.triggered.connect(self._paste_widget)
        
        self.menu.addSeparator()
        
        clear_action = self.menu.addAction('Clear')
        clear_action.triggered.connect(self._clear_action)

    def _build_widgets(self):
        self.child_layout = qt.QVBoxLayout()
        
        self.main_layout.addLayout(self.child_layout)
        self.main_layout.addSpacing(30)
        
    def _get_widget_names(self, parent = None):
        
        if not parent:
            scope = self
            
        if parent:
            scope = parent
        
        item_count = scope.child_layout.count()
        found = []
        for inc in range(0, item_count):
            
            item = scope.child_layout.itemAt(inc)
            widget = item.widget()
            label = widget.get_name()
            found.append(label)
            
        return found
        
    def _find_widget(self, name):
        
        group_name = None
        
        split_name = name.split('.')
        
        if name.find('.') > -1:
            if name.endswith('.'):
                return self._find_group_widget(name)
        
            
            
            group_name = string.join(split_name[:-1], '.')
            #group_name = group_name + '.'
            
        scope = self
        
        if group_name:
            scope = self._find_group_widget(group_name)
        
        if not scope:
            return
        
        item_count = scope.child_layout.count()
        
        test_name = split_name[-1]
        
        for inc in range(0, item_count):
            item = scope.child_layout.itemAt(inc)
            widget =  item.widget()
            
            if widget.name == test_name:
                return widget
            
    
    def _find_group_widget(self, name, find_last = False):
        
        item_count = self.child_layout.count()
        
        split_name = name.split('.')
        
        sub_widget = None
        found = False
        
        for name in split_name:
            
            if not sub_widget:
                sub_widget = self
            
            if not find_last:
                found = False  
                     
            item_count = sub_widget.child_layout.count()
            
            for inc in range(0, item_count):
                
                item = sub_widget.child_layout.itemAt(inc)
                
                if item:
                    
                    widget = item.widget()
                    
                    widget_type = type(widget)
                    
                    if widget_type == ProcessOptionGroup or widget_type == ProcessReferenceGroup:
                        label = widget.get_name()
                        if label == name:
                            sub_widget = widget
                            found = True
                            break
                    
                if not item:
                    break
                
            if not found:
                return
        
        return sub_widget
                
        
    def _get_unique_name(self, name, parent = None):
        
        found = self._get_widget_names(parent)
        while name in found:
            name = util.increment_last_number(name)
            
        return name
        
    def _get_path(self, widget):
        
        parent = widget.get_parent()
        
        path = ''
        
        parents = []
        
        if parent:
            
            sub_parent = parent
            
            while sub_parent:
                
                if sub_parent.__class__ == ProcessOptionPalette:
                    break
                
                name = sub_parent.get_name()
                  
                parents.append(name)
                sub_parent = sub_parent.get_parent()
        
        parents.reverse()
        
        for sub_parent in parents:
            path += '%s.' % sub_parent
        
        if hasattr(widget, 'child_layout'):
            path = path + widget.get_name() + '.'
        if not hasattr(widget, 'child_layout'):
            path = path + widget.get_name()
        
        return path
    
    def _is_child_of_ref_widget(self, widget):
        
        if not widget:
            return False
        
        parent = widget.parent()
        
        if widget.__class__ == ProcessReferenceGroup:
            return False
        
        if widget.__class__ == OptionGroup and parent.__class__ == ProcessReferenceGroup:
            return False
        
        if parent:
            
            sub_parent = parent
            
            while sub_parent:
                
                if sub_parent.__class__ == ProcessReferenceGroup:
                    return True
                
                sub_parent = sub_parent.parent()
                
                  
        else:
            return False
        
    def _find_palette(self, widget):
        
        if widget.__class__ == ProcessOptionPalette:
            return widget
        
        parent = widget.get_parent()
        
        if not parent:
            return
        
        while parent.__class__ != ProcessOptionPalette:
            
            parent = parent.get_parent()
        
        return parent
        
    def _write_widget_options(self, widget):
        
        if not widget:
            return
        
        item_count = widget.child_layout.count()
        
        for inc in range(0, item_count):
            
            item = widget.child_layout.itemAt(inc)
            
            if item:
                sub_widget = item.widget()
                
                sub_widget_type = sub_widget._define_type()
                
                name = self._get_path(sub_widget)
                
                value = sub_widget.get_value()
                
                self.process_inst.add_option(name, value, None, sub_widget_type)
                
                if hasattr(sub_widget, 'child_layout'):
                    self._write_widget_options(sub_widget)
        
    def _write_options(self, clear = True):
        
        if self.supress_update:
            log.debug('supress write options')
            return
        
        if clear == True:
            self._write_all()
        
        if clear == False:
            
            this_widget = self
            
            item_count = this_widget.child_layout.count()
            
            for inc in range(0, item_count):
                
                item = self.child_layout.itemAt(inc)
                widget = item.widget()
                
                widget_type = widget.option_type
                
                name = self._get_path(widget)
                
                value = widget.get_value()
                
                self.process_inst.add_option(name, value, None, widget_type)
            
            if type(self) == ProcessReferenceGroup:
                
                name = self._get_path(self)
                value = self.get_value()
                
                self.process_inst.add_option(name, value, True, self.option_type)
        
        self.value_change.emit()
        
        log.info('Finished writing options')
            
    def _write_all(self):
        
        self.process_inst.clear_options()
        palette = self._find_palette(self)
        
        self._write_widget_options(palette)
                    
    def _load_widgets(self, options):
        log.info('Load Option Widgets!!')
        self.clear_widgets()
        
        if not options:
            return
        
        self.setHidden(True)
        self.setUpdatesEnabled(False)
        
        
        self.disable_auto_expand = True
        
        self._auto_rename = False
        
        reference_groups = []
        reference_widgets = []
        reference_dict = {}
        
        for option in options:
        
            self.supress_update = True
            
            option_type = None
            
            if type(option[1]) == list:
                value = option[1][0]
                try:
                    option_type = option[1][1]
                except:
                    option_type = None
            else:
                value = option[1]
                
            split_name = option[0].split('.')
            
            name = option[0]
            
            is_child_of_ref = False
            current_reference_widget = None
            
            for ref_group in reference_groups:
                                
                if name.find(ref_group) > -1:
                    is_child_of_ref = True
                    current_reference_widget = reference_dict[ref_group]
                    break
            
            if is_child_of_ref:
                
                widget = None
                
                if not name.endswith('.'):
                
                    widget = self._find_widget(name)
                    
                    if widget:
                        
                        widget.ref_path = current_reference_widget.ref_path    
                        
                        if not type(widget) == ProcessOptionGroup and not type(widget) == ProcessReferenceGroup:
                        
                            if not type(widget) == ProcessScript and not type(widget) == ProcessNote:
                                widget.set_value(value)
                                if hasattr(widget, 'option_type'):
                                    self.process_inst.add_option(name, value, None, widget.option_type)  
                    
                    else:
                        log.info('Could not find matching widget for %s' % name)
                    continue
        
                if name.endswith('.'):
                
                    widget = self._find_group_widget(name, find_last=True)
                    
                    if type(widget) == ProcessOptionGroup:
                        
                        widget.ref_path = current_reference_widget.ref_path
                        
                        if value:
                            widget.expand_group()
                        if not value:
                            widget.collapse_group()
                    
                    if hasattr(widget, 'option_type'):
                        self.process_inst.add_option(name, value, None, widget.option_type)
                            
                    continue
                
        
            log.info('Adding option: %s' % name )
            
            
            if split_name[-1] == '':
                search_group = string.join(split_name[:-2], '.')
                name = split_name[-2]
            if not split_name[-1] == '':
                search_group = string.join(split_name[:-1], '.')
                name = split_name[-1]
                
            widget = self._find_group_widget(search_group)
            
            if not widget:
                widget = self
            
            is_group = False
            
            if split_name[-1] == '' or split_name[-1] == u'':
                
                is_group = True
                
                parent_name = string.join(split_name[:-1], '.')
                
                group = self._find_group_widget(parent_name)
                
                
                
                if not group:
                    
                    if option_type == None:
                        self.add_group(name, value, widget)
                    if option_type == 'reference.group':
                        
                        path_to_process, _ = get_reference_option_info(value[1], self.process_inst)
                        
                        ref_widget = self.add_ref_group(name, value, widget, ref_path = path_to_process)
                        
                        reference_groups.append(name)
                        reference_widgets.append(ref_widget)
                        reference_dict[name] = ref_widget
                        
            if len(split_name) > 1 and split_name[-1] != '':
                
                search_group = string.join(split_name[:-2], '.')
                after_search_group = string.join(split_name[:-1], '.')
                group_name = split_name[-2]
                
                group_widget = self._find_group_widget(search_group)
                
                widget = self._find_group_widget(after_search_group)
                
                if not widget:
                    self.add_group(group_name, value, group_widget)
                    widget = self._find_group_widget(after_search_group)
                    is_group = True
            
            if is_group:
                log.debug('Option is a group')
            
            sub_widget = None
            
            if not option_type and not is_group:
                
                if type(value) == str or type(value) == unicode:
                    log.info('string' )
                    sub_widget = self.add_string_option(name, value, widget)
                    
                if type(value) == float:
                    log.info('float' )
                    sub_widget = self.add_number_option(name, value, widget)
                    
                if type(option[1]) == int:
                    log.info('int' )
                    sub_widget = self.add_integer_option(name, value, widget)
                    
                if type(option[1]) == bool:
                    log.info('bool' )
                    sub_widget = self.add_boolean_option(name, value, widget)
                    
                if type(option[1]) == dict:
                    log.info('dict' )
                    sub_widget = self.add_dictionary(name, [value,[]], widget)
                    
                if option[1] == None:
                    log.info('title' )
                    sub_widget = self.add_title(name, widget)
                    
            if option_type == 'note':
                self.add_note(name, value, widget)
                    
            if option_type == 'script':
                log.info('script' )
                self.add_script(name, value, widget)
                
            if option_type == 'dictionary':
                log.info('dictionary' )
                sub_widget = self.add_dictionary(name, value, widget)
            
            if sub_widget:
                
                if hasattr(widget, 'ref_path'):
                    if self.ref_path:
                        if hasattr(widget, 'option_type'):
                            name = self._get_path(sub_widget)
                            
                            log.info('sub ref %s %s %s' % (name, value, sub_widget.option_type))
                            self.process_inst.add_option(name, value, None, sub_widget.option_type)
                
        self.disable_auto_expand = False
        self.setVisible(True)    
        self.setUpdatesEnabled(True)
        self.supress_update = False
        self._auto_rename = True
        log.info('Done  -    Load Option Widgets!!')
    
    def _handle_parenting(self, widget, parent):
        
        widget.widget_clicked.connect(self.update_current_widget)
        
        if self.top_parent:
            widget.top_parent = self.top_parent
        
        if not type(widget) == ProcessOptionGroup and not type(widget) == ProcessReferenceGroup:
            widget.set_process(self.process_inst)            
        if type(widget) == ProcessOptionGroup or type(widget) == ProcessReferenceGroup:
            widget.process_inst = self.process_inst
            
        if not parent:
            self.child_layout.addWidget(widget)
            if hasattr(widget, 'update_values'):
                widget.update_values.connect(self._write_options)
        
        if parent:
            parent.child_layout.addWidget(widget)
            if hasattr(widget, 'update_values'):
                widget.update_values.connect(parent._write_options)
                                
        if self._auto_rename:
            widget.rename()
            
        if not parent:
            parent = self
        
        if hasattr(widget, 'set_edit'):
            parent.edit_mode.connect(widget.set_edit)
            
        if self.ref_path:
            widget.ref_path = self.ref_path
        
    def _fill_background(self, widget):
        palette = widget.palette()
        
        if not util.is_in_maya():
            palette.setColor(widget.backgroundRole(), qt.QtCore.Qt.gray)
        
        if util.is_in_maya():
            palette.setColor(widget.backgroundRole(), qt.QColor(115, 194, 251, 150))
        widget.setAutoFillBackground(True)
        widget.setPalette(palette)
    
    def _unfill_background(self, widget):
        
        palette = widget.palette()
        palette.setColor(widget.backgroundRole(), widget.orig_background_color)
        widget.setAutoFillBackground(False)    
        widget.setPalette(palette)
    
    def _deselect_children(self, widget):
        
        children = widget.get_children()
        
        for child in children:
            self.deselect_widget(child)
        
        
    def _activate_edit_mode(self):
        
        self.edit_mode_state = True
        self.edit_mode.emit(True)
        
        if hasattr(self, 'edit_action'):
            self.edit_action.setVisible(False)
            self.disable_edit_action.setVisible(True)
        
    def _clear_action(self):
        
        if self.__class__ == ProcessOptionPalette:
            name = 'the palette?'
        if not self.__class__ == ProcessOptionPalette:
            
            name = 'group: %s?' % self.get_name()
        
        permission = qt_ui.get_permission('Clear all the widgets in %s' % name, self)
        
        if permission == True:
            self.clear_widgets()
            self._write_options(clear = True)
            
    def _copy_widget(self):
        
        ProcessOptionPalette.widget_to_copy = self
        
    def _paste_widget(self):
        
        self.paste_action.setVisible(False)
        
        widget_to_copy = ProcessOptionPalette.widget_to_copy
        
        if not widget_to_copy:
            return
        
        if widget_to_copy.option_type == 'group':
            widget_to_copy.copy_to(self)
            
        else:
            parent = widget_to_copy.get_parent()
            widget_to_copy.copy_to(parent)
    
    def update_current_widget(self, widget = None):
        
        if ProcessOptionPalette.edit_mode_state == False:
            return
        
        if widget:
        
            if self.is_selected(widget):
                self.deselect_widget(widget)
                return
            
            if not self.is_selected(widget):
                self.select_widget(widget)
                return
        
    def sort_widgets(self, widgets, parent, return_out_of_scope = False):
        
        if not hasattr(parent, 'child_layout'):
            return
        
        item_count = parent.child_layout.count()
        found = []
        
        for inc in range(0, item_count):
            
            item = parent.child_layout.itemAt(inc)
            
            if item:
                widget = item.widget()
                
                for sub_widget in widgets:
                    if sub_widget == widget:

                        found.append(widget)
                        
        if return_out_of_scope:
            
            other_found = []
            
            for sub_widget in widgets:
                if not sub_widget in found:
                    other_found.append(sub_widget)
        
            
            found = other_found
        
        return found
        
        pass
        

        
    def is_selected(self, widget):
        
        if widget in ProcessOptionPalette.current_widgets:
            return True
        
        return False
        
    def get_parent(self):
        
        parent = self.parent()
        
        if not parent:
            return
            
        grand_parent = parent.parent()
    
        if hasattr(grand_parent, 'group'):
            parent = grand_parent
        
        if not hasattr(parent, 'child_layout'):
            return
    
        if parent.__class__ == ProcessOptionPalette:
            return parent
    
        return parent
    
    def get_widget_names(self, parent = None):
        
        return self._get_widget_names(parent)
        
    
    def select_widget(self, widget):
        
        if hasattr(widget, 'child_layout'):
            self._deselect_children(widget)
            
        
        parent = widget.get_parent()
        
        if not parent:
            #get palette
            parent = widget.parent()
        
        out_of_scope = None
        
        if parent:
            out_of_scope = self.sort_widgets(ProcessOptionPalette.current_widgets, 
                                             parent, 
                                             return_out_of_scope = True)
            
        if out_of_scope:
            for sub_widget in out_of_scope:
                self.deselect_widget(sub_widget)
            
        ProcessOptionPalette.current_widgets.append(widget)
        self._fill_background(widget)
        
    def deselect_widget(self, widget):
        
        if not self.is_selected(widget):
            return
        
        widget_index = ProcessOptionPalette.current_widgets.index(widget)
        
        ProcessOptionPalette.current_widgets.pop(widget_index)
        self._unfill_background(widget)
        
    def clear_selection(self):
        
        for widget in ProcessOptionPalette.current_widgets:
            self._unfill_background(widget)
            
        ProcessOptionPalette.current_widgets = []
        
    def has_options(self):
        if not self.directory:
            
            return False
        
        return self.process_inst.has_options()
        
    def clear_widgets(self):
        
        self.has_first_group = False
        
        item_count = self.child_layout.count()
        
        for inc in range(item_count, -1, -1):
            
            item = self.child_layout.itemAt(inc)
            
            if item:
                widget = item.widget()
                self.child_layout.removeWidget(widget)
                widget.deleteLater()
                
        ProcessOptionPalette.current_widgets = []
            
    def add_group(self, name = 'group', value = True, parent = None):
        
        if type(name) == bool:
            name = 'group'
        
        name = self._get_unique_name(name, parent)
        
        group = ProcessOptionGroup(name)
        group.set_expanded(value)
        
        if self.__class__ == ProcessOptionGroup or parent.__class__ == ProcessOptionGroup:
            if util.is_in_maya():
                group.group.set_inset_dark()
        
        if parent.__class__ == ProcessReferenceGroup:
            if util.is_in_maya():
                group.group.set_reference_color()
        
        self._handle_parenting(group, parent)
        
        group.process_inst = self.process_inst
        self._write_options(False)           
            
        self.has_first_group = True
        
        return group
    
    def add_ref_group(self, name = 'reference group', value = True, parent = None, ref_path = ''):
        
        if type(name) == bool:
            name = 'reference group'
        
        name = self._get_unique_name(name, parent)
        
        group = ProcessReferenceGroup(name, ref_path)
        self._handle_parenting(group, parent)
        
        group.process_inst = self.process_inst
        
        value = util.convert_to_sequence(value)
        
        
        if len(value) > 1:
            group.set_script_text(value[1])
            #group.script_widget.set_text(value[1])
            #group.update_referenced_widgets()
   
        path, _ = group.get_reference_info()
        if path:
            group.ref_path = path     
        
        group.set_expanded(value[0])
        
        if self.__class__ == ProcessReferenceGroup or parent.__class__ == ProcessReferenceGroup:
            if util.is_in_maya():
                group.group.set_inset_dark()
        
        self._write_options(False)           
            
            
            
        self.has_first_group = True
        return group        
    
    def add_script(self, name = 'script', value = '',  parent = None):
        
        if type(name) == bool:
            name = 'script'
        
        name = self._get_unique_name(name, parent)
        
        button = ProcessScript(name)
        
        button.set_value(value)
        
        self._handle_parenting(button, parent)
        
        self._write_options(False)
        
        return button
    
    def add_dictionary(self, name = 'dictionary', value = [{},[]], parent = None):
        
        if type(name) == bool:
            name = 'dictionary'
            
        if type(value) == type(dict):
            
            keys = dict.keys()
            if keys:
                keys.sort()
            
            value = [dict, keys]
            
        name = self._get_unique_name(name, parent)
        
        button = ProcessOptionDictionary(name)
        
        button.set_value(value)
        
        self._handle_parenting(button, parent)
        
        self._write_options(False)
        
        return button
        
        
    def add_title(self, name = 'title', parent = None):
        
        if type(name) == bool:
            name = 'title'
        
        name = self._get_unique_name(name, parent)
        
        title = ProcessTitle(name)
        
        self._handle_parenting(title, parent)
        
        self._write_options(False)
        
        return title
    
    def add_note(self, name = 'note', value = '', parent = None):
        if type(name) == bool:
            name = 'note'
        
        name = self._get_unique_name(name, parent)
        
        note = ProcessNote(name)
        note.set_value(value)
        
        self._handle_parenting(note, parent)
        
        self._write_options(False)
        
        return note
        
        
    def add_number_option(self, name = 'number', value = 0, parent = None):
        
        if type(name) == bool:
            name = 'number'
        
        name = self._get_unique_name(name, parent)
        
        number_option = ProcessOptionNumber(name)
        number_option.set_value(value)
        
        self._handle_parenting(number_option, parent)
        
        self._write_options(False)
        
        return number_option
        
    def add_integer_option(self, name = 'integer', value = 0, parent = None):
        
        if type(name)== bool:
            name = 'integer'
            
        name = self._get_unique_name(name, parent)
        
        option = ProcessOptionInteger(name)
        option.set_value(value)
        
        self._handle_parenting(option, parent)
        
        self._write_options(False)
        
        return option
        
    def add_boolean_option(self, name = 'boolean', value = False, parent = None):
        
        if type(name)== bool:
            name = 'boolean'
            
        name = self._get_unique_name(name, parent)
        
        option = ProcessOptionBoolean(name)
        
        option.set_value(value)
        
        self._handle_parenting(option, parent)
        
        self._write_options(False)
        
        return option
        
    def add_string_option(self, name = 'string', value = '', parent = None):
        
        if type(name) == bool:
            name = 'string'
        
        name = self._get_unique_name(name, parent)
        
        string_option = ProcessOptionText(name)
        string_option.set_value(value)
        
        self._handle_parenting(string_option, parent)
        
        self._write_options(False)
        
        return string_option
        
    def set_process(self, process_inst):
        
        log.info('setting process in option ui')
        
        if not process_inst:
            self.directory = None
            self.process_inst = None
            
            self.clear_widgets()
        
        if process_inst:
            
            self.directory = process_inst.directory
            
            self.process_inst = process_inst
                        
            options = process_inst.get_options()
            
            self._load_widgets(options)
    
    def set_options_file(self, options_filename):
        
        log.info('setting option file')
        
        path = util_file.get_dirname(options_filename)
        filename = util_file.get_basename(options_filename)
        
        util_file.copy_file(options_filename, util_file.join_path(path, 'version.json'))
        options = util_file.SettingsFile()
            
        options.set_directory(path, filename)
        
        option_settings = options.get_settings()
        
        self._load_widgets(option_settings)

    def get_children(self):
        
        item_count = self.child_layout.count()
        found = []
        for inc in range(0, item_count):
            
            item = self.child_layout.itemAt(inc)
            widget = item.widget()
            found.append(widget)
           
        return found
    
    def set_activate_edit(self, bool_value):
        self.edit_mode_state = bool_value
        
        self.edit_mode.emit(bool_value)
        
    def set_edit(self, bool_value):
        
        self.edit_mode.emit(bool_value)
        

    def save(self):
        self._write_options(clear=False)

    def refresh(self):

        log.info('Refresh Options')

        if type(self) == ProcessReferenceGroup:
            self.update_referenced_widgets()
            
            return

        self.process_inst._load_options()
        options = self.process_inst.get_options()
        self._load_widgets(options)

class ProcessOptionGroup(ProcessOptionPalette):
    
    update_values = qt_ui.create_signal(object)
    widget_clicked = qt_ui.create_signal(object)
    
    def __init__(self, name):
        
        self.name = name
        
        super(ProcessOptionGroup, self).__init__()
        self.setSizePolicy(qt.QSizePolicy(qt.QSizePolicy.Minimum, qt.QSizePolicy.Minimum))
        self.main_layout.setContentsMargins(1,0,1,1)
        
        if hasattr(self, 'copy_action'):
            self.copy_action.setVisible(True)
            
        self.supress_select = False
        
        self.orig_background_color = self.palette().color(self.backgroundRole())
        
        self.option_type = self._define_type()
        
    def mousePressEvent(self, event):
        
        super(ProcessOptionGroup, self).mousePressEvent(event)
        
        if not event.button() == qt.QtCore.Qt.LeftButton:
            return
        
        half = self.width()/2
        
        if event.y() > 25 and event.x() > (half - 50) and event.x() < (half + 50):
            return
        
        parent = self.get_parent()
        if parent:
            parent.supress_select = True
        
        if self.supress_select == True:
            self.supress_select = False
            return
        
        self.widget_clicked.emit(self)
        
        self._define_type()
        
    def _define_type(self):
        return 'group'
        
    def _get_widget_names(self, parent = None):
        
        if parent:
            scope = parent
            
        if not parent:
            scope = self
        
        item_count = scope.child_layout.count()
        found = []
        for inc in range(0, item_count):
            
            item = scope.child_layout.itemAt(inc)
            widget = item.widget()
            label = widget.get_name()
            found.append(label)
           
        return found
        
        
    def _build_widgets(self):
        main_group_layout = qt.QVBoxLayout()
        
        main_group_layout.setContentsMargins(0,0,0,0)
        main_group_layout.setSpacing(1)
        
        self.group = OptionGroup(self.name)
        
        self.child_layout = self.group.child_layout
        
        self.group.expand.connect(self._expand_updated)
        
        self.main_layout.addSpacing(10)
        self.main_layout.addWidget(self.group)
        
    def _expand_updated(self, value):
        
        
        self.update_values.emit(False)
        
    def _create_context_menu(self):
        
        super(ProcessOptionGroup, self)._create_context_menu()
        
        rename = qt.QAction('Rename', self)
        rename.triggered.connect(self.rename)
        
        remove = qt.QAction('Remove', self)
        remove.triggered.connect(self.remove)
        
        self.menu.insertAction(self.copy_action, rename)
        self.menu.insertAction(self.copy_action, remove)
        
    def _copy(self):
        self.copy_widget.emit(self)
        
    def _paste(self):
        self.paste_widget.emit()
        
        
        
    def move_up(self):
        
        parent = self.parent()
        layout = parent.child_layout
        index = layout.indexOf(self)
        
        if index == 0:
            return
        
        index = index - 1
        
        parent.child_layout.removeWidget(self)
        layout.insertWidget(index, self)
        
        self._write_all()
        
    def move_down(self):
        
        parent = self.parent()
        layout = parent.child_layout
        index = layout.indexOf(self)
        
        if index == (layout.count() - 1):
            return
        
        index = index + 1
        
        parent.child_layout.removeWidget(self)
        layout.insertWidget(index, self)
        
        self._write_all()
        
    def rename(self):
        
        found = self._get_widget_names()
        
        title = self.group.title()
        
        new_name =  qt_ui.get_new_name('Rename group', self, title)
        
        if new_name == title:
            return
        
        if new_name == None:
            return
        
        while new_name in found:
            new_name = util.increment_last_number(new_name)
            
        self.group.setTitle(new_name)
        self._write_all()
        
    def remove(self):
        
        parent = self.parent()
        
        if self in ProcessOptionPalette.current_widgets:
            
            remove_index = ProcessOptionPalette.current_widgets.index(self)
            ProcessOptionPalette.current_widgets.pop(remove_index)
        
        parent.child_layout.removeWidget(self)
        self.deleteLater()
        self._write_all()
        
    def collapse_group(self):
        self.group.collapse_group()
        
    def expand_group(self):
        self.group.expand_group()
        
    def get_name(self):
        return self.group.title()
    
    def set_name(self, name):
        
        self.group.setTitle(name)
        
    def get_value(self):
        expanded = self.group.expanded
        return expanded
    
    def set_expanded(self, bool_value):
        if bool_value:
            self.expand_group()
        else:
            self.collapse_group()
            
        
    
    def copy_to(self, parent):
        
        parent._auto_rename = False
        group = parent.add_group(self.get_name(), parent)
        parent._auto_rename = True
        
        children = self.get_children()
        
        for child in children:
            
            if child == group:
                continue
            
            child.copy_to(group)
       
class OptionGroup(qt.QFrame):
    
    expand = qt_ui.create_signal(object)
    
    def __init__(self, name):
        super(OptionGroup, self).__init__()
        
        self.close_height = 28
        if util.get_maya_version() < 2016:
            self.setFrameStyle(self.Panel | self.Raised)
        if util.get_maya_version() > 2015:    
            self.setFrameStyle(self.NoFrame)
            
        self.layout = qt.QVBoxLayout()
        self.child_layout = qt.QVBoxLayout()
        self.child_layout.setContentsMargins(0,2,0,3)
        self.child_layout.setSpacing(0)
        
        self.setLayout(self.layout)
        
        self.header_layout = qt.QVBoxLayout()
        
        top_header_layout = qt.QHBoxLayout()
        
        self.label = qt.QLabel(name)
        self.label.setMinimumHeight(15)
        
        self.label_expand = qt.QLabel('--')
        
        self.label_expand.setMinimumHeight(15)
        
        top_header_layout.addWidget(self.label)
        top_header_layout.addSpacing(5)
        top_header_layout.addWidget(self.label_expand)
        
        self.header_layout.addLayout(top_header_layout)
        
        self.setMinimumHeight(self.close_height)
        
        self.layout.addLayout(self.header_layout)
        self.layout.addSpacing(4)
        self.layout.addLayout(self.child_layout)
        
        self.background_shade = 80
    
        if util.is_in_maya():
            palette = self.palette()    
            palette.setColor(self.backgroundRole(), qt.QColor(80,80,80))
            self.setAutoFillBackground(True)
            self.setPalette(palette)
            
        self.expanded = True
        
    def mousePressEvent(self, event):
        
        super(OptionGroup, self).mousePressEvent(event)
        
        if not event.button() == qt.QtCore.Qt.LeftButton:
            return
        
        half = self.width()/2
        
        if event.y() < 30 and event.x() > (half - 50) and event.x() < (half + 50):
            
            height = self.height()
            
            if height == self.close_height:
                self.expand_group()
                self.expand.emit(False)
                return
                    
            if height >= self.close_height:
                self.collapse_group()
                self.expand.emit(False)
                return
           
    def collapse_group(self):
        
        self.setVisible(False)
        self.setMaximumHeight(self.close_height)
        self.label_expand.setText('+')
        self.setVisible(True)
        
        self.expanded = False
        
        
    def expand_group(self):
        
        self.setVisible(False)
        self.setFixedSize(qt_ui.QWIDGETSIZE_MAX, qt_ui.QWIDGETSIZE_MAX)
        self.label_expand.setText('--')
        self.setVisible(True)
        
        self.expanded = True
        
        
           
    def title(self):
        return self.label.text() 
        
    def setTitle(self, string_value):
        self.label.setText(string_value)
        
    def set_inset_dark(self):
        
        value = self.background_shade
        value -= 15
        if util.get_maya_version() < 2016:    
            self.setFrameStyle(self.Panel | self.Sunken)
        
        palette = self.palette()    
        palette.setColor(self.backgroundRole(), qt.QColor(value,value,value))
        self.setAutoFillBackground(True)
        self.setPalette(palette)

    def set_reference_color(self):
        
        value = 80
        
        if util.get_maya_version() < 2016:    
            self.setFrameStyle(self.Panel | self.Sunken)
        
        palette = self.palette()    
        palette.setColor(self.backgroundRole(), qt.QColor(value*.9,value*.9,value*.9))
        self.setAutoFillBackground(True)
        self.setPalette(palette)



class ProcessReferenceGroup(ProcessOptionGroup):
    
    def __init__(self, name, ref_path):
        
        self.ref_path = ref_path
        
        super(ProcessReferenceGroup, self).__init__(name)

    def _define_type(self):
        return 'reference.group'

    def _item_menu(self, position):
        
        if not self.__class__.edit_mode_state:
            return
        
        self.menu.exec_(self.mapToGlobal(position))
        
    def _create_context_menu(self):
        
        self.menu = qt.QMenu()

        rename = self.menu.addAction('Rename')
        
        rename.triggered.connect(self.rename)
        
        remove = self.menu.addAction('Remove')
        remove.triggered.connect(self.remove)
    
    def _build_widgets(self):
        super(ProcessReferenceGroup, self)._build_widgets()
        
        script = qt_ui.GetCode('Option Path Script')
        
        self.script_widget = script
        self.set_script_text("#This code allows the reference group to connect to another process\n#In order to connect you need to set the path to the process\n#And you need to give the name of the option group at the process\n#example\n#path = 'D:/project/assets/character_test'\n#option_group = 'test'\n\npath_to_process = ''\noption_group = ''\n\n")

        if self.edit_mode_state == False:
            script.hide()
        
        script.set_completer(ui_code.CodeCompleter)

        self.group.header_layout.addWidget(script)
        
    def _store_script(self):
        self.update_values.emit(False)
        
        log.info('Store Script')
        self.update_referenced_widgets()
        
    def get_reference_info(self):
        script = self.script_widget.get_text()
        
        path_to_process, option_group = get_reference_option_info(script, 
                                                                  self.process_inst)
        
        return path_to_process, option_group
        
    def update_referenced_widgets(self):
        
        log.info('Update Reference widgets')
        
        if not hasattr(self, 'process_inst'):
            return
        
        path_to_process, option_group = self.get_reference_info()
        util_file.fix_slashes(path_to_process)
        
        current_widget_name = self._get_path(self)
        
        process = process_module.Process()
        process.set_directory(path_to_process)
        option_file = process.get_option_file()
        option_file_current = self.process_inst.get_option_file()
            
        settings = util_file.SettingsFile()
        settings_current = util_file.SettingsFile()
        
        name = util_file.get_basename(option_file)
        name_current = util_file.get_basename(option_file_current)
        
        option_path = util_file.get_dirname(option_file)
        option_path_current = util_file.get_dirname(option_file_current)
        
        if not option_path:
            return
        
        settings.set_directory(option_path, name)
        settings_current.set_directory(option_path_current, name_current)
        
        option_groups = []
        all_value = []
        
        if option_group:
            option_groups = util.convert_to_sequence(option_group)
        
            for option_group in option_groups:
                option_group = option_group + '.'

                found = []
                
                for setting in settings.get_settings():
                    
                    if setting == option_group:
                        continue
                    if setting[0].find(option_group) > -1:
                        
                        current_setting_name = current_widget_name + setting[0]
                        setting = self._get_ref_current_value(current_setting_name, setting, settings_current)
                        
                        found.append(setting)
                
                all_value += found
        
        if not option_groups:
            
            settings_current.has_setting
            
            for setting in settings.get_settings():
                
                current_setting_name = current_widget_name + setting[0]
                setting = self._get_ref_current_value(current_setting_name, setting, settings_current)
                
                all_value.append(setting)
        
        self._load_widgets(all_value)
                
        log.info('Finished refresh of reference')
    
    def _get_ref_current_value(self, current_setting_name, setting, settings_current):

        current_value = None
        
        if settings_current.has_setting(current_setting_name):
            skip = False
            
            if type(setting[1]) == list and len(setting[1]) > 1:
                if setting[1][1] == 'script':
                    skip = True
                if setting[1][1] == 'note':
                    skip = True
                
            if not skip:
                current_value = settings_current.get(current_setting_name)
        
        if current_value != None:
            setting[1] = current_value
         
        return setting        

    def set_edit(self, bool_value):
        super(ProcessReferenceGroup, self).set_edit(bool_value)
        
        if bool_value:
            self.script_widget.show()
            self.script_widget.set_minimum()
        else:
            self.script_widget.hide()
            self.main_layout.setContentsMargins(0,2,0,2)
            self._store_script()
        
    def set_script_text(self, text):
        
        self.script_widget.set_text(text)
        
        
        self._store_script()
        
    def get_value(self):
        expanded = self.group.expanded
        
        text = self.script_widget.get_text()
        
        return [expanded, text]        

class ProcessOption(qt_ui.BasicWidget):
    
    update_values = qt_ui.create_signal(object)
    widget_clicked = qt_ui.create_signal(object)
    #edit_mode = qt_ui.create_signal()
    edit_mode_state = False
    
    def __init__(self, name):
        
        self.process_inst = None
        self.ref_path = None
        
        super(ProcessOption, self).__init__()
        
        self.name = name
        
        self.option_widget = self._define_option_widget()
        if self.option_widget:
            self.main_layout.addWidget(self.option_widget)
        self.main_layout.setContentsMargins(0,0,0,0)
        
        self.setContextMenuPolicy(qt.QtCore.Qt.ActionsContextMenu)
        self.create_right_click()
        
        self._setup_value_change()
        
        self.option_type = self._define_type()
        
        self.orig_background_color = self.palette().color(self.backgroundRole())
        
        self.setContextMenuPolicy(qt.QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._item_menu)
        
    def _item_menu(self, position):
        
        if self.ref_path:
            return
        
        if not self.__class__.edit_mode_state:
            return
        
        self.menu.exec_(self.mapToGlobal(position))
        
    def _create_context_menu(self):
        
        self.menu = qt.QMenu()
        
        self.create_right_click(self.menu)
        
        #rename = self.menu.addAction('Rename')
        #rename.triggered.connect(self._rename)
        
        #remove = self.menu.addAction('Remove')
        #remove.triggered.connect(self.remove)
        
    def mousePressEvent(self, event):
        
        super(ProcessOption, self).mousePressEvent(event)
        
        if not event.button() == qt.QtCore.Qt.LeftButton:
            return
        
        parent = self.get_parent()
        if parent:
            parent.supress_select = True
        self.widget_clicked.emit(self)
        
        
    def _define_type(self):
        return None
        
    def _define_main_layout(self):
        return qt.QHBoxLayout()
        
    def _setup_value_change(self):
        return
        
    def _value_change(self, value):
        self.update_values.emit(False)
        
    def _define_option_widget(self):
        return
        
    def _get_widget_names(self):
        
        parent = self.parent()
        item_count = parent.child_layout.count()
        found = []
        for inc in range(0, item_count):
            
            item = parent.child_layout.itemAt(inc)
            widget = item.widget()
            label = widget.get_name()
            found.append(label)
            
        return found

    def _rename(self):
        
        title = self.get_name() 
        
        new_name =  qt_ui.get_new_name('Rename Group', self, title)
        
        found = self._get_widget_names()
        
        if new_name == title:
            return
        
        if new_name == None:
            return
        
        while new_name in found:
            new_name = util.increment_last_number(new_name)
        
        self.set_name(new_name)
        
        self.update_values.emit(True)
        
    def get_parent(self):
        
        parent = self.parent()
        
        grand_parent = parent.parent()
        
        if hasattr(grand_parent, 'group'):
            parent = grand_parent
        
        if not hasattr(parent, 'child_layout'):
            return
        
        if parent.__class__ == ProcessOptionPalette:
            return parent
        
        return parent
    
    def create_right_click(self):
        self.menu = qt.QMenu()
        move_up = qt.QAction(self)
        move_up.setText('Move Up')
        move_up.triggered.connect(self.move_up)
        self.menu.addAction(move_up)
        
        move_dn = qt.QAction(self)
        move_dn.setText('Move Down')
        move_dn.triggered.connect(self.move_down)
        self.menu.addAction(move_dn)
        
        rename = qt.QAction(self)
        rename.setText('Rename')
        rename.triggered.connect(self._rename)
        self.menu.addAction(rename)
        
        remove = qt.QAction(self)
        remove.setText('Remove')
        remove.triggered.connect(self.remove)
        self.menu.addAction(remove)
        
        copy = qt.QAction(self)
        copy.setText('Copy')
        copy.triggered.connect(self._copy)
        self.menu.addAction(copy)
        
    def _copy(self):
        
        
        ProcessOptionPalette.widget_to_copy = self
            
    
    def rename(self):
        self._rename()
    
    def remove(self):
        parent = self.get_parent()
        
        if self in ProcessOptionPalette.current_widgets:
            
            remove_index = ProcessOptionPalette.current_widgets.index(self)
            ProcessOptionPalette.current_widgets.pop(remove_index)
        
        parent.child_layout.removeWidget(self)
        self.deleteLater()
        
        self.update_values.emit(True)
        
    def move_up(self):
        
        parent = self.get_parent()
        if not parent:
            parent = self.parent()
            
        layout = parent.child_layout
        index = layout.indexOf(self)
        
        if index == 0:
            return
        
        index = index - 1
        
        parent.child_layout.removeWidget(self)
        layout.insertWidget(index, self)
        
        self.update_values.emit(True)
        
    def move_down(self):
        
        parent = self.get_parent()
        if not parent:
            parent = self.parent()
        layout = parent.child_layout
        index = layout.indexOf(self)
        
        if index == (layout.count() - 1):
            return
        
        index = index + 1
        
        parent.child_layout.removeWidget(self)
        layout.insertWidget(index, self)
        
        self.update_values.emit(True)
    
    def get_name(self):
        
        name = self.option_widget.get_label()
        
        return name
    
    def set_name(self, name):
        
        self.option_widget.set_label(name)
        
    def set_value(self, value):
        pass
    
    def get_value(self):
        pass
    
    def copy_to(self, parent):
        
        name = self.get_name()
        value = self.get_value()
        
        name = parent._get_unique_name(name)
    
        new_instance = self.__class__(name)
        
        new_instance.set_value(value)
        
        parent.child_layout.addWidget(new_instance)
        parent.save()
        
    def set_process(self, process_inst):
        self.process_inst = process_inst
    
    def set_edit(self, bool_value):
        self.edit_mode_state = bool_value

class ProcessScript(ProcessOption):
    
    def __init__(self, name):
        super(ProcessScript, self).__init__(name)

        self.main_layout.setContentsMargins(0,2,0,2)
        self.setSizePolicy(qt.QSizePolicy(qt.QSizePolicy.Minimum, qt.QSizePolicy.Minimum))
        self.main_layout.setAlignment(qt.QtCore.Qt.AlignCenter | qt.QtCore.Qt.AlignTop)
        
    def _define_type(self):
        return 'script'
        
    def _define_option_widget(self):
        
        button = qt_ui.GetCode('option script')
        button.set_label('')
        button.set_use_button(True)
        button.set_button_text(self.name)
        button.set_button_to_first()
        button.button.setMinimumWidth(200)
        #button.text_entry.setMinimumWidth(300)
        button.label.hide()
        button.button.clicked.connect(self.run_script)
        button.set_suppress_button_command(True)
        if self.edit_mode_state == False:
            button.text_entry.hide()
        
        button.set_completer(ui_code.CodeCompleter)
        
        if self.process_inst:
            button.set_process(self.process_inst)
        
        return button
    
    def _setup_value_change(self):
        
        self.option_widget.text_changed.connect(self._value_change)
    
    def get_name(self):
        
        name = self.option_widget.button.text()
        return name
    
    def set_name(self, name):
        
        self.option_widget.set_button_text(name)


        
    def set_value(self, value):
        
        value = str(value)
        self.option_widget.set_process(self.process_inst)
        self.option_widget.set_text(value)
        
    def get_value(self):
        
        value = self.option_widget.get_text()
        
        if not value:
            value = ''
        
        return value
    
    def run_script(self):
        
        value = self.get_value()
        
        if self.ref_path:
            process_inst = process_module.Process()
            process_inst.set_directory(self.ref_path)
            
            process_inst.set_data_override(self.process_inst)
            
            process_inst.run_code_snippet(value)
        else:
            self.process_inst.run_code_snippet(value)
        
        if hasattr(self, 'top_parent'):
            
            self.top_parent.refresh()
            
        
    def set_process(self, process_inst):
        super(ProcessScript, self).set_process(process_inst)
        
        self.option_widget.set_process(process_inst)
                
    def set_edit(self, bool_value):
        super(ProcessScript, self).set_edit(bool_value)
        
        if self.ref_path:
            return
        
        if bool_value:
            self.option_widget.text_entry.show()
            self.main_layout.setContentsMargins(0,2,0,15)
            self.option_widget.set_minimum()
        else:
            self.option_widget.text_entry.hide()
            self.main_layout.setContentsMargins(0,2,0,2)
            
        self.option_widget.set_process(self.process_inst)

class ProcessTitle(ProcessOption):
    
    def __init__(self, name):
        super(ProcessTitle, self).__init__(name)

        self.main_layout.setContentsMargins(0,2,0,2)
        
        self.main_layout.setAlignment(qt.QtCore.Qt.AlignCenter)
        
        
        
        
    def _define_type(self):
        return 'title'
        
        
        
    def _define_option_widget(self):
        
        label = qt.QLabel(self.name)
         
        return label
    
    def get_name(self):
        
        name = self.option_widget.text()
        return name
    
    def set_name(self, name):
        
        self.option_widget.setText(name)


class ProcessNote(ProcessOption):
    
    def __init__(self, name):
        
        self.title = qt.QLabel()
        self.title.setText(name)
        
        super(ProcessNote, self).__init__(name)
        
        self.main_layout.setContentsMargins(0,2,0,2)
        
        self.option_widget.setSizePolicy(qt.QSizePolicy.Minimum, qt.QSizePolicy.Minimum)
        #self.option_widget.setWordWrapMode(qt.QTextOption.NoWrap)
        self.main_layout.insertWidget(0, self.title)
        
        self.setFocusPolicy(qt.QtCore.Qt.NoFocus)
        
    def _define_main_layout(self):
        return qt.QVBoxLayout()
        
    def _define_type(self):
        return 'note'
        
    def _define_option_widget(self):
        text =  qt.QTextEdit()
        
        self.title.setText(self.name)
        #text.setText(self.name)
        
        if self.edit_mode_state:
            text.setReadOnly(False)
        else:
            text.setReadOnly(True)
        
        text.setFrameStyle(text.Plain)
        
        
        return text
        #return qt.QLabel(self.name)
    
    def _setup_value_change(self):
        
        self.option_widget.textChanged.connect(self._value_change)
    
    def _value_change(self):
        text = str(self.get_name())
        super(ProcessNote, self)._value_change(text)
    
        self._text_to_size()
        

    def _text_to_size(self):
        
        
        font = self.option_widget.document().defaultFont()
        font_metrics = qt.QFontMetrics(font)
        
        value =  self.get_value().count('\n')
        count = 1
        if value:
            count = self.get_value().count('\n') + 1
        
        height = font_metrics.height()
        
        self.option_widget.setFixedHeight(height*count+15)#*count)
        
    def get_name(self):
        
        name = str(self.title.text())
        return name
    
    def set_name(self, name):
        
        self.title.setText(name)
        
    def get_value(self):
        text = str(self.option_widget.toPlainText())
        return text
    
    def set_value(self, value):
        
        self.option_widget.setText(str(value))
        self._text_to_size()
        
        
    def set_edit(self, bool_value):
        super(ProcessNote, self).set_edit(bool_value)
        
        if self.ref_path:
            return
        
        if bool_value:
            self.option_widget.setReadOnly(False)
        else:
            self.option_widget.setReadOnly(True)
            
        
class ProcessOptionText(ProcessOption):
    
    def __init__(self, name):
        super(ProcessOptionText, self).__init__(name)
        
        self.option_widget.set_use_button(True)
    
    def _define_type(self):
        return 'text'
        
    def _define_option_widget(self):
        return qt_ui.GetString(self.name)
        
    def _setup_value_change(self):
        
        self.option_widget.text_changed.connect(self._value_change)
        

        
    def set_value(self, value):
        value = str(value)
        self.option_widget.set_text(value)
        
    def get_value(self):
        
        value = self.option_widget.get_text()
        
        if not value:
            value = ''
        
        return value
        
class ProcessOptionNumber(ProcessOption):
    
    def _define_type(self):
        return 'number'
    
    def _define_option_widget(self):
        
        return qt_ui.GetNumber(self.name)

    def _setup_value_change(self):
        self.option_widget.valueChanged.connect(self._value_change)
    
    def set_value(self, value):
        self.option_widget.set_value(value)
        
    def get_value(self):

        
        return self.option_widget.get_value()
    
class ProcessOptionInteger(ProcessOptionNumber):
    
    def _define_type(self):
        return 'integer'
    
    def _define_option_widget(self):
        
        return qt_ui.GetInteger(self.name)
    
class ProcessOptionBoolean(ProcessOption):
    
    def _define_type(self):
        return 'boolean'
    
    def __init__(self, name):
        super(ProcessOptionBoolean, self).__init__(name)

        self.main_layout.setContentsMargins(0,2,0,2)
    
    def _define_option_widget(self):
        return qt_ui.GetBoolean(self.name)

    def _setup_value_change(self):
        self.option_widget.valueChanged.connect(self._value_change)

    def set_value(self, value):
        self.option_widget.set_value(value)
        
    def get_value(self):
        return self.option_widget.get_value()

class ProcessOptionDictionary(ProcessOptionNumber):
    
    def _define_type(self):
        return 'dictionary'
    
    def __init__(self, name):
        super(ProcessOptionDictionary, self).__init__(name)

        self.main_layout.setContentsMargins(0,2,0,2)
    
    def _define_option_widget(self):
        return qt_ui.GetDictionary(self.name)
    
    def _setup_value_change(self):
        self.option_widget.dictionary_widget.dict_changed.connect(self._value_change)    
    
    def get_label(self):
        return self.option_widget.get_label()
 
    def get_value(self):
        
        order = self.option_widget.get_order()
        dictionary = self.option_widget.get_value()
        
        return [dictionary,order]
        
    def set_value(self, dictionary_value):
        
        self.option_widget.set_order(dictionary_value[1])
        self.option_widget.set_value(dictionary_value[0])
        
        
def get_reference_option_info(script, process_inst):
    
    builtins = process_module.get_process_builtins(process_inst)
    
    try: 
        exec(script, globals(), builtins)
    except:
        pass
    
    path_to_process = builtins['path_to_process']
    option_group = builtins['option_group']
    
    return path_to_process, option_group