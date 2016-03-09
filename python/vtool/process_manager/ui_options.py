# Copyright (C) 2016 Louis Vottero louis.vot@gmail.com    All rights reserved.

import string

from vtool import qt_ui
from vtool import util

from vtool.process_manager import process

if qt_ui.is_pyqt():
    from PyQt4 import QtGui, QtCore, Qt, uic
if qt_ui.is_pyside():
    from PySide import QtCore, QtGui

class ProcessOptionsWidget(qt_ui.BasicWidget):
    
    def __init__(self):
        super(ProcessOptionsWidget, self).__init__()
        
        policy = self.sizePolicy()
        policy.setHorizontalPolicy(policy.Expanding)
        policy.setVerticalPolicy(policy.Expanding)
        
        self.setSizePolicy(policy)
        
        self.directory = None        
        
    def _build_widgets(self):
        
        title = QtGui.QLabel('  Options')
        
        self.option_palette = ProcessOptionPalette()
        
        self.main_layout.addWidget(title)
        self.main_layout.addWidget(self.option_palette)
        
    def set_directory(self, directory):
        self.directory = directory
        self.option_palette.set_directory(directory)
        
    def has_options(self):
        
        if not self.directory:
        
            return False
        
        return self.option_palette.has_options()
        
        
class ProcessOptionPalette(qt_ui.BasicWidget):
    
    def __init__(self):
        super(ProcessOptionPalette, self).__init__()
        
        self.main_layout.setContentsMargins(0,10,0,0)
        self.main_layout.setSpacing(1)
        self.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding))
        
        self.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.create_right_click()
        
        self.directory = None
        self.process_inst = None
        
        self.supress_update = False
        self.central_palette = self
        
    def _build_widgets(self):
        self.child_layout = QtGui.QVBoxLayout()
        
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
                self.add_group(name, widget)
            
            if type(option[1]) == str:
                
                self.add_string_option(name, option[1], widget)
                
            if type(option[1]) == float:
                self.add_number_option(name, option[1], widget)
                
            if type(option[1]) == int:
                self.add_integer_option(name, option[1], widget)
                
            if type(option[1]) == bool:
                self.add_boolean_option(name, option[1], widget)
                
            if option[1] == None and not is_group:
                self.add_title(name, widget)
                
        
        self.setVisible(True)    
        self.setUpdatesEnabled(True)
        self.supress_update = False
        
    def _handle_parenting(self, widget, parent):
        
        if not parent:
            self.child_layout.addWidget(widget)
            if hasattr(widget, 'update_values'):
                widget.update_values.connect(self._write_options)
        if parent:
            parent.child_layout.addWidget(widget)
            if hasattr(widget, 'update_values'):
                widget.update_values.connect(parent._write_options)
        
    def create_right_click(self, ):
        
        self.add_string = QtGui.QAction(self)
        self.add_string.setText('Add String')
        self.add_string.triggered.connect(self.add_string_option)
        
        add_number = QtGui.QAction(self)
        add_number.setText('Add Number')
        add_number.triggered.connect(self.add_number_option)
        
        add_integer = QtGui.QAction(self)
        add_integer.setText('Add Integer')
        add_integer.triggered.connect(self.add_integer_option)
        
        add_boolean = QtGui.QAction(self)
        add_boolean.setText('Add Boolean')
        add_boolean.triggered.connect(self.add_boolean_option)
        
        
        self.add_group_action = QtGui.QAction(self)
        self.add_group_action.setText('Add Group')
        self.add_group_action.triggered.connect(self.add_group)
        
        self.add_title_action = QtGui.QAction(self)
        self.add_title_action.setText('Add Title')
        self.add_title_action.triggered.connect(self.add_title)
        
        self.addAction(self.add_string)
        self.addAction(add_number)
        self.addAction(add_integer)
        self.addAction(add_boolean)
        self.addAction(self.add_group_action)
        self.addAction(self.add_title_action)
        
    def has_options(self):
        if not self.directory:
            
            return False
        
        return self.process_inst.has_options()
        
    def clear_widgets(self):
        
        item_count = self.child_layout.count()
        
        for inc in range(item_count, -1, -1):
            
            item = self.child_layout.itemAt(inc)
            
            if item:
                widget = item.widget()
                self.child_layout.removeWidget(widget)
                widget.deleteLater()
            
    def add_group(self, name = 'group', parent = None):
        
        if type(name) == bool:
            name = 'group'
        
        name = self._get_unique_name(name, parent)
        
        group = ProcessOptionGroup(name)
        
        self._handle_parenting(group, parent)
        
        group.process_inst = self.process_inst
        self._write_options(False)
        
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
            
        
        if directory:
            
            self.directory = directory
            
            process_inst = process.Process()
            process_inst.set_directory(directory)
            
            self.process_inst = process_inst
                        
            options = process_inst.get_options()
            
            self._load_widgets(options)
            
            
class ProcessOptionGroup(ProcessOptionPalette):
    
    def __init__(self, name):
        
        self.name = name
        
        super(ProcessOptionGroup, self).__init__()
        self.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum))
        self.main_layout.setContentsMargins(0,0,0,5)
        
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
        
    def create_right_click(self):
        super(ProcessOptionGroup, self).create_right_click()
        
        move_up = QtGui.QAction(self)
        move_up.setText('Move Up')
        move_up.triggered.connect(self.move_up)
        
        move_dn = QtGui.QAction(self)
        move_dn.setText('Move Down')
        move_dn.triggered.connect(self.move_down)
        
        rename = QtGui.QAction(self)
        rename.setText('Rename')
        rename.triggered.connect(self.rename)

        remove = QtGui.QAction(self)
        remove.setText('Remove')
        remove.triggered.connect(self.remove)
        
        separator = QtGui.QAction(self)
        separator.setSeparator(True)
        
        self.insertAction(self.add_string, move_up)
        self.insertAction(self.add_string, move_dn)
        self.insertAction(self.add_string, rename)
        self.insertAction(self.add_string, remove)
        self.insertAction(self.add_string, separator)
        
    def _build_widgets(self):
        main_group_layout = QtGui.QVBoxLayout()
        
        main_group_layout.setContentsMargins(0,0,0,0)
        
        self.child_layout = QtGui.QVBoxLayout()
        self.child_layout.setContentsMargins(5,10,5,10)
        
        self.child_layout.setSpacing(0)
        
        main_group_layout.addLayout(self.child_layout)
        main_group_layout.addSpacing(10)
        
        self.group = QtGui.QGroupBox(self.name)
        self.group.setLayout(main_group_layout)
        
        self.group.child_layout = self.child_layout
        
        self.main_layout.addWidget(self.group)
        
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
        
        parent.child_layout.removeWidget(self)
        self.deleteLater()
        self._write_all()
        
    def get_name(self):
        return self.group.title()
    
    def set_name(self, name):
        
        self.group.setTitle(name)
        
    def get_value(self):
        return None
        
class ProcessOption(qt_ui.BasicWidget):
    
    update_values = qt_ui.create_signal(object)
    
    def __init__(self, name):
        super(ProcessOption, self).__init__()
        
        self.name = name
        
        self.option_widget = self._define_option_widget()
        if self.option_widget:
            self.main_layout.addWidget(self.option_widget)
        self.main_layout.setContentsMargins(0,0,0,0)
        
        self.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.create_right_click()
        
        self._setup_value_change()
        
    def _define_main_layout(self):
        return QtGui.QHBoxLayout()
        
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
            return
        
        return parent
        
    def create_right_click(self):
        
        move_up = QtGui.QAction(self)
        move_up.setText('Move Up')
        move_up.triggered.connect(self.move_up)
        self.addAction(move_up)
        
        move_dn = QtGui.QAction(self)
        move_dn.setText('Move Down')
        move_dn.triggered.connect(self.move_down)
        self.addAction(move_dn)
        
        rename = QtGui.QAction(self)
        rename.setText('Rename')
        rename.triggered.connect(self._rename)
        self.addAction(rename)
        
        remove = QtGui.QAction(self)
        remove.setText('Remove')
        remove.triggered.connect(self.remove)
        self.addAction(remove)
        
    def remove(self):
        parent = self.parent()
        
        parent.child_layout.removeWidget(self)
        self.deleteLater()
        
        self.update_values.emit(True)
        
    def move_up(self):
        
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
        
class ProcessTitle(ProcessOption):
    
    def __init__(self, name):
        super(ProcessTitle, self).__init__(name)

        self.main_layout.setContentsMargins(0,5,0,10)
        
    def _define_option_widget(self):
        return QtGui.QLabel(self.name)
    
    def get_name(self):
        
        name = self.option_widget.text()
        return name
    
    def set_name(self, name):
        
        self.option_widget.setText(name)
        
class ProcessOptionText(ProcessOption):
    
    def __init__(self, name):
        super(ProcessOptionText, self).__init__(name)
    
        insert_button = QtGui.QPushButton('<')
        insert_button.setMaximumWidth(20)
        insert_button.clicked.connect(self._insert)
        self.main_layout.addWidget(insert_button)
        
    def _define_option_widget(self):
        return qt_ui.GetString(self.name)
        
    def _insert(self):
        
        if util.is_in_maya():
            import maya.cmds as cmds
            
            selection = cmds.ls(sl = True)
            
            if len(selection) > 1:
                selection = self._remove_unicode(selection)
                selection = str(selection)
            
            if len(selection) == 1:
                selection = str(selection[0])
                
            self.set_value(selection)
            
        
    def _setup_value_change(self):
        
        self.option_widget.text_changed.connect(self._value_change)
        
    def _remove_unicode(self, list_or_tuple):
            new_list = []
            for sub in list_or_tuple:
                new_list.append(str(sub))
                
            return new_list
        
    def set_value(self, value):
        value = str(value)
        self.option_widget.set_text(value)
        
    def get_value(self):
        
        value = self.option_widget.get_text()
        
        pass_value = None
        
        new_value = None
        
        try:
            new_value = eval(value)
        except:
            pass
        
        if new_value:
            value = new_value
        
        if type(value) == list or type(value) == tuple:
            pass_value = self._remove_unicode(value)
        elif type(value) == dict:
            pass_value = value
        else:
            pass_value = str(value)    
        
        print pass_value, type(pass_value)
        
        return pass_value 
        
class ProcessOptionNumber(ProcessOption):
    def _define_option_widget(self):
        
        return qt_ui.GetNumber(self.name)

    def _setup_value_change(self):
        self.option_widget.valueChanged.connect(self._value_change)
    
    def set_value(self, value):
        self.option_widget.set_value(value)
        
    def get_value(self):

        
        return self.option_widget.get_value()
    
class ProcessOptionInteger(ProcessOptionNumber):
    def _define_option_widget(self):
        
        return qt_ui.GetInteger(self.name)
    
class ProcessOptionBoolean(ProcessOptionNumber):
    
    def __init__(self, name):
        super(ProcessOptionBoolean, self).__init__(name)

        self.main_layout.setContentsMargins(0,5,0,5)
    
    def _define_option_widget(self):
        return qt_ui.GetBoolean(self.name)
    
