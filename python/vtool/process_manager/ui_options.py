# Copyright (C) 2016 Louis Vottero louis.vot@gmail.com    All rights reserved.

import string

from vtool import qt_ui, qt
from vtool import util

from vtool.process_manager import process


class ProcessOptionsWidget(qt_ui.BasicWidget):
    
    toggle_alignment = qt_ui.create_signal()
    
    def __init__(self):
        super(ProcessOptionsWidget, self).__init__()
        
        policy = self.sizePolicy()
        policy.setHorizontalPolicy(policy.Expanding)
        policy.setVerticalPolicy(policy.Expanding)
        self.main_layout.setContentsMargins(1,1,1,1)
        self.setSizePolicy(policy)
        
        self.directory = None
        

    def _build_widgets(self):
        
        button_layout = qt.QHBoxLayout()
        
        self.orientation_button = qt.QPushButton('Toggle Alignment')
        self.orientation_button.setMaximumWidth(100)
        self.orientation_button.setMaximumHeight(20)
        self.orientation_button.setMaximumWidth(120)
        self.orientation_button.clicked.connect(self._emit_alignment_toggle)
        
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
        
        
        
        button_layout.addWidget(self.orientation_button, alignment = qt.QtCore.Qt.AlignLeft)
        button_layout.addWidget(self.edit_mode_button, alignment = qt.QtCore.Qt.AlignRight)
        
        self.main_layout.addLayout(button_layout)
        self.main_layout.addWidget(self.option_scroll)
        self.main_layout.addWidget(self.edit_options)
    
    def _edit_click(self, bool_value):
        
        
        self._edit_activate(bool_value)
        
    
        
    def _edit_activate(self, bool_value):
        
        self.edit_options.setVisible(bool_value)
        ProcessOptionPalette.edit_mode_state = bool_value
        ProcessOption.edit_mode_state = bool_value
        
        if bool_value == False:
            self.option_palette.clear_selection()
    
    def _emit_alignment_toggle(self):
        self.toggle_alignment.emit()
        
    def set_directory(self, directory):
        
        if directory == None:
            raise
        
        self.directory = directory
        self.option_palette.set_directory(directory)
        
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
        self.setMinimumWidth(300)
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
    
    def __init__(self):
        super(ProcessOptionPalette, self).__init__()
        
        self.main_layout.setContentsMargins(1,1,1,0)
        self.main_layout.setSpacing(1)
        self.setSizePolicy(qt.QSizePolicy(qt.QSizePolicy.Expanding, qt.QSizePolicy.Expanding))
        
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
        
    def _item_menu(self, position):
        
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
        
        self.add_string = create_menu.addAction('Add String')
        self.add_string.triggered.connect(self.add_string_option)
        
        add_number = create_menu.addAction('Add Number')
        add_number.triggered.connect(self.add_number_option)
        
        add_integer = create_menu.addAction('Add Integer')
        add_integer.triggered.connect(self.add_integer_option)
        
        add_boolean = create_menu.addAction('Add Boolean')
        add_boolean.triggered.connect(self.add_boolean_option)
        
        add_group = create_menu.addAction('Add Group')
        add_group.triggered.connect(self.add_group)
        
        
        add_title = create_menu.addAction('Add Title')
        add_title.triggered.connect(self.add_title)
        
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
    
    def _find_group_widget(self, name):
        
        item_count = self.child_layout.count()
        found = []
        
        split_name = name.split('.')
        
        sub_widget = None
        
        for name in split_name:
            
            if not sub_widget:
                sub_widget = self
            
            found = False
            
            item_count = sub_widget.child_layout.count()
            
            for inc in range(0, item_count):
                
                item = sub_widget.child_layout.itemAt(inc)
                
                if item:
                    
                    widget = item.widget()
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
                
        
    def _get_unique_name(self, name, parent):
        
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
                
                name = self._get_path(sub_widget)
                
                value = sub_widget.get_value()
                
                self.process_inst.add_option(name, value, None)
                
                if hasattr(sub_widget, 'child_layout'):
                    self._write_widget_options(sub_widget)
        
    def _write_options(self, clear = True):
        
        if self.supress_update:
            return
        
        if clear == True:
            self._write_all()
            
        if clear == False:
            
            item_count = self.child_layout.count()
            
            for inc in range(0, item_count):
                
                item = self.child_layout.itemAt(inc)
                widget = item.widget()
                
                name = self._get_path(widget)
                
                value = widget.get_value()
                
                self.process_inst.add_option(name, value, None)
            
    def _write_all(self):
        
        self.process_inst.clear_options()
        palette = self._find_palette(self)
        
        self._write_widget_options(palette)
                    
    def _load_widgets(self, options):
        
        self.clear_widgets()
        
        if not options:
            return
        
        self.setHidden(True)
        self.setUpdatesEnabled(False)
        self.supress_update = True
        
        self.disable_auto_expand = True
        
        for option in options:
            
            split_name = option[0].split('.')
            
            name = option[0]
            
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
            
            if split_name[-1] == '':
                is_group = True
                
                parent_name = string.join(split_name[:-1], '.')
                
                group = self._find_group_widget(parent_name)
                
                if not group:
                    
                    self.add_group(name, widget)
            
            if len(split_name) > 1 and split_name[-1] != '':
                
                search_group = string.join(split_name[:-2], '.')
                after_search_group = string.join(split_name[:-1], '.')
                group_name = split_name[-2]
                
                group_widget = self._find_group_widget(search_group)
                
                widget = self._find_group_widget(after_search_group)
                
                if not widget:
                    self.add_group(group_name, group_widget)
                    widget = self._find_group_widget(after_search_group)
                
            if type(option[1]) == str:
                self.add_string_option(name, str(option[1]), widget)
                
            if type(option[1]) == float:
                self.add_number_option(name, option[1], widget)
                
            if type(option[1]) == int:
                self.add_integer_option(name, option[1], widget)
                
            if type(option[1]) == bool:
                self.add_boolean_option(name, option[1], widget)
                
            if option[1] == None and not is_group:
                self.add_title(name, widget)
                
        self.disable_auto_expand = False
        self.setVisible(True)    
        self.setUpdatesEnabled(True)
        self.supress_update = False
        
    def _handle_parenting(self, widget, parent):
        
        widget.widget_clicked.connect(self.update_current_widget)
        widget.edit_mode.connect(self._activate_edit_mode)
        
        if not parent:
            self.child_layout.addWidget(widget)
            if hasattr(widget, 'update_values'):
                widget.update_values.connect(self._write_options)
                
                if hasattr(self, 'expand_group'):
                    if not self.disable_auto_expand:
                        self.expand_group()
                    
        
        if parent:
            parent.child_layout.addWidget(widget)
            if hasattr(widget, 'update_values'):
                widget.update_values.connect(parent._write_options)
                
                if hasattr(parent, 'expand_group'):
                    if not self.disable_auto_expand:
                        parent.expand_group()
        
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
        
    def _deselect_children(self, widget):
        
        children = widget.get_children()
        
        for child in children:
            self.deselect_widget(child)
        
        
    def _activate_edit_mode(self):
        
        self.edit_mode_state = True
        self.edit_mode.emit(True)
        
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
        
        if widget_to_copy.option_type == 'group':
            widget_to_copy.copy_to(self)
        
    def is_selected(self, widget):
        
        if widget in ProcessOptionPalette.current_widgets:
            return True
        
        return False
        
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
            
    def add_group(self, name = 'group', parent = None):
        
        if type(name) == bool:
            name = 'group'
        
        name = self._get_unique_name(name, parent)
        
        group = ProcessOptionGroup(name)
        if self.__class__ == ProcessOptionGroup or parent.__class__ == ProcessOptionGroup:
            if util.is_in_maya():
                group.group.set_inset_dark()
        
        self._handle_parenting(group, parent)
        
        group.process_inst = self.process_inst
        self._write_options(False)
        
        if not self.has_first_group:
            group.expand_group()
        
        if parent.__class__ == ProcessOptionPalette and self.has_first_group == True:
            group.collapse_group()
            
            
        self.has_first_group = True
            
        return group
        
    def add_title(self, name = 'title', parent = None):
        
        if type(name) == bool:
            name = 'title'
        
        name = self._get_unique_name(name, parent)
        
        title = ProcessTitle(name)
        
        self._handle_parenting(title, parent)
        
        self._write_options(False)
        
    def add_number_option(self, name = 'number', value = 0, parent = None):
        
        if type(name) == bool:
            name = 'number'
        
        name = self._get_unique_name(name, parent)
        
        number_option = ProcessOptionNumber(name)
        number_option.set_value(value)
        
        self._handle_parenting(number_option, parent)
        
        self._write_options(False)
        
    def add_integer_option(self, name = 'integer', value = 0, parent = None):
        
        if type(name)== bool:
            name = 'integer'
            
        name = self._get_unique_name(name, parent)
        
        option = ProcessOptionInteger(name)
        option.set_value(value)
        
        self._handle_parenting(option, parent)
        
        self._write_options(False)
        
    def add_boolean_option(self, name = 'boolean', value = False, parent = None):
        
        if type(name)== bool:
            name = 'boolean'
            
        name = self._get_unique_name(name, parent)
        
        option = ProcessOptionBoolean(name)
        
        option.set_value(value)
        
        self._handle_parenting(option, parent)
        
        self._write_options(False)
        
    def add_string_option(self, name = 'string', value = '', parent = None):
        
        if type(name) == bool:
            name = 'string'
        
        name = self._get_unique_name(name, parent)
        
        string_option = ProcessOptionText(name)
        string_option.set_value(value)
        
        self._handle_parenting(string_option, parent)
        
        self._write_options(False)
        
    def set_directory(self, directory):
        
        if not directory:
            self.directory = None
            self.process_inst = None
            
            self.clear_widgets()
            
        if directory:
            
            self.directory = directory
            
            process_inst = process.Process()
            process_inst.set_directory(directory)
            
            self.process_inst = process_inst
                        
            options = process_inst.get_options()
            
            self._load_widgets(options)
            

    def get_children(self):
        
        item_count = self.child_layout.count()
        found = []
        for inc in range(0, item_count):
            
            item = self.child_layout.itemAt(inc)
            widget = item.widget()
            found.append(widget)
           
        return found
    


class ProcessOptionGroup(ProcessOptionPalette):
    
    widget_clicked = qt_ui.create_signal(object)
    
    def __init__(self, name):
        
        self.name = name
        
        super(ProcessOptionGroup, self).__init__()
        self.setSizePolicy(qt.QSizePolicy(qt.QSizePolicy.Minimum, qt.QSizePolicy.Minimum))
        self.main_layout.setContentsMargins(1,0,1,1)
        
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
        
        self.main_layout.addSpacing(10)
        self.main_layout.addWidget(self.group)
        
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
        return None
    
    def copy_to(self, parent):
        
        group = parent.add_group(self.get_name(), parent)
        
        children = self.get_children()
        
        for child in children:
            
            if child == group:
                continue
            
            child.copy_to(group)
       
class OptionGroup(qt.QFrame):
    
    def __init__(self, name):
        super(OptionGroup, self).__init__()
        
        self.close_height = 40
        if util.get_maya_version() < 2016:
            self.setFrameStyle(self.Panel | self.Raised)
        if util.get_maya_version() > 2015:    
            self.setFrameStyle(self.NoFrame)
            
        self.layout = qt.QVBoxLayout()
        self.child_layout = qt.QVBoxLayout()
        self.child_layout.setContentsMargins(0,2,0,3)
        self.child_layout.setSpacing(0)
        
        self.setLayout(self.layout)
        
        self.header_layout = qt.QHBoxLayout()
        
        self.label = qt.QLabel(name)
        self.label.setMinimumHeight(15)
        
        self.label_expand = qt.QLabel('--')
        
        self.label_expand.setMinimumHeight(15)
        
        self.header_layout.addWidget(self.label)
        self.header_layout.addSpacing(5)
        self.header_layout.addWidget(self.label_expand)
        
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
        
    def mousePressEvent(self, event):
        
        super(OptionGroup, self).mousePressEvent(event)
        
        if not event.button() == qt.QtCore.Qt.LeftButton:
            return
        
        half = self.width()/2
        
        if event.y() < 25 and event.x() > (half - 50) and event.x() < (half + 50):
            
            height = self.height()
            
            if height == self.close_height:
                self.expand_group()
                return
                    
            if height >= self.close_height:
                self.collapse_group()
                return
            
    def collapse_group(self):
        
        self.setVisible(False)
        self.setMaximumHeight(self.close_height)
        self.label_expand.setText('+')
        self.setVisible(True)
        
        
    def expand_group(self):
        
        self.setVisible(False)
        self.setFixedSize(qt_ui.QWIDGETSIZE_MAX, qt_ui.QWIDGETSIZE_MAX)
        self.label_expand.setText('--')
        self.setVisible(True)
        
           
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
        
class ProcessOption(qt_ui.BasicWidget):
    
    update_values = qt_ui.create_signal(object)
    widget_clicked = qt_ui.create_signal(object)
    edit_mode = qt_ui.create_signal()
    edit_mode_state = False
    
    def __init__(self, name):
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
        
        self._create_context_menu()
        
    def _item_menu(self, position):
        
        if not self.__class__.edit_mode_state:
            return
        
        self.menu.exec_(self.mapToGlobal(position))
        
    def _create_context_menu(self):
        
        self.menu = qt.QMenu()
        
        #move_up = self.menu.addAction('Move Up')
        #move_up.triggered.connect(self.move_up)
        
        #move_dn = self.menu.addAction('Move Down')
        #move_dn.triggered.connect(self.move_down)
        
        rename = self.menu.addAction('Rename')
        rename.triggered.connect(self._rename)
        
        remove = self.menu.addAction('Remove')
        remove.triggered.connect(self.remove)
        
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
        
        move_up = qt.QAction(self)
        move_up.setText('Move Up')
        move_up.triggered.connect(self.move_up)
        self.addAction(move_up)
        
        move_dn = qt.QAction(self)
        move_dn.setText('Move Down')
        move_dn.triggered.connect(self.move_down)
        self.addAction(move_dn)
        
        rename = qt.QAction(self)
        rename.setText('Rename')
        rename.triggered.connect(self._rename)
        self.addAction(rename)
        
        remove = qt.QAction(self)
        remove.setText('Remove')
        remove.triggered.connect(self.remove)
        self.addAction(remove)
        
        copy = qt.QAction(self)
        copy.setText('Copy')
        copy.triggered.connect(self._copy)
        self.addAction(copy)
        
    def _copy(self):
        
        ProcessOptionPalette.widget_to_copy = self
        
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
        
        new_instance = self.__class__(name)
        
        new_instance.set_value(value)
        
        parent.child_layout.addWidget(new_instance)
        
class ProcessTitle(ProcessOption):
    
    def __init__(self, name):
        super(ProcessTitle, self).__init__(name)

        self.main_layout.setContentsMargins(0,2,0,2)
        
        self.main_layout.setAlignment(qt.QtCore.Qt.AlignRight)
        
    def _define_type(self):
        return 'title'
        
    def _define_option_widget(self):
        return qt.QLabel(self.name)
    
    def get_name(self):
        
        name = self.option_widget.text()
        return name
    
    def set_name(self, name):
        
        self.option_widget.setText(name)
        
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
    
class ProcessOptionBoolean(ProcessOptionNumber):
    
    def _define_type(self):
        return 'boolean'
    
    def __init__(self, name):
        super(ProcessOptionBoolean, self).__init__(name)

        self.main_layout.setContentsMargins(0,2,0,2)
    
    def _define_option_widget(self):
        return qt_ui.GetBoolean(self.name)
    
