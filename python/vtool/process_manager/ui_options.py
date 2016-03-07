# Copyright (C) 2016 Louis Vottero louis.vot@gmail.com    All rights reserved.

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
        
        self.option_palette.set_directory(directory)
        
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
        
    def _build_widgets(self):
        self.child_layout = QtGui.QVBoxLayout()
        
        self.main_layout.addLayout(self.child_layout)
        self.main_layout.addSpacing(30)
        
    def _get_widget_names(self):
        
        item_count = self.child_layout.count()
        found = []
        for inc in range(0, item_count):
            
            item = self.child_layout.itemAt(inc)
            widget = item.widget()
            label = widget.get_name()
            found.append(label)
            
        return found
        
    def _get_unique_name(self, name):
        
        found = self._get_widget_names()
        while name in found:
            name = util.increment_last_number(name)
            
        return name
    
    def _save_setting(self):
        
        self._update_settings()
        
    def _get_parent_path(self, widget):
        
        parent = widget.get_parent()
        
        if parent:
            parent_path = ''
            
            while parent:
            
                name = parent.get_name()
                parent_path += '%s.' % name  
                
                parent = parent.get_parent()
        
        if not parent:
            if hasattr(widget, 'child_layout'):
                parent_path = '.'
        
        return parent_path
        
    def _update_settings(self, clear = True):
        
        if self.supress_update:
            return
        
        if clear:
            self.process_inst.clear_options()
        
        item_count = self.child_layout.count()
        
        for inc in range(0, item_count):
            
            item = self.child_layout.itemAt(inc)
            widget = item.widget()
            
            parent_path = self._get_parent_path(widget)
            
            name = widget.get_name()
            
            if parent_path:
                name = parent_path + name
            
            value = widget.get_value()
            
            self.process_inst.add_option(name, value, None)
        
    def create_right_click(self, ):
        
        self.add_string = QtGui.QAction(self)
        self.add_string.setText('Add String')
        self.add_string.triggered.connect(self.add_string_option)
        
        add_number = QtGui.QAction(self)
        add_number.setText('Add Number')
        add_number.triggered.connect(self.add_number_option)
        
        self.add_group_action = QtGui.QAction(self)
        self.add_group_action.setText('Add Group')
        self.add_group_action.triggered.connect(self.add_group)
        
        self.add_title_action = QtGui.QAction(self)
        self.add_title_action.setText('Add Title')
        self.add_title_action.triggered.connect(self.add_title)
        
        self.addAction(self.add_string)
        self.addAction(add_number)
        self.addAction(self.add_group_action)
        self.addAction(self.add_title_action)
        
    def clear_widgets(self):
        
        item_count = self.child_layout.count()
        
        for inc in range(item_count, -1, -1):
            
            item = self.child_layout.itemAt(inc)
            
            if item:
                widget = item.widget()
                self.child_layout.removeWidget(widget)
                widget.deleteLater()
            
        
    def add_group(self, name = 'group'):
        
        if type(name) == bool:
            name = 'group'
        
        name = self._get_unique_name(name)
        
        group = ProcessOptionGroup(name)
        self.child_layout.addWidget(group)
        
        group.process_inst = self.process_inst
        self._update_settings(True)
        
        
    def add_title(self, name = 'title', group = None):
        
        if type(name) == bool:
            name = 'title'
        
        name = self._get_unique_name(name)
        
        title = ProcessTitle(name)
        self.child_layout.addWidget(title)
        
        self._update_settings(False)
        
    def add_number_option(self, name = 'number', value = 0, group = None):
        
        if type(name) == bool:
            name = 'number'
        
        name = self._get_unique_name(name)
        
        number_option = ProcessOptionNumber(name)
        number_option.set_value(value)
        self.child_layout.addWidget(number_option)
        
        number_option.update_values.connect(self._update_settings)
        
        self._update_settings(False)
        
    def add_string_option(self, name = 'string', value = '', group = None):
        
        if type(name) == bool:
            name = 'string'
        
        name = self._get_unique_name(name)
        
        string_option = ProcessOptionText(name)
        string_option.set_value(value)
        
        self.child_layout.addWidget(string_option)
        
        string_option.update_values.connect(self._update_settings)
        
        self._update_settings(False)
        
    def set_directory(self, directory):
        
        if not directory:
            self.directory = None
            self.process_inst = None
            
        
        if directory:
            
            process_inst = process.Process()
            process_inst.set_directory(directory)
            
            self.process_inst = process_inst
                        
            options = process_inst.get_options()
            
            self.clear_widgets()
            
            if not options:
                return
            
            self.setHidden(True)
            self.setUpdatesEnabled(False)
            
            self.supress_update = True
            
            for option in options:
                
                period_count = option[0].count('.')
                
                if period_count >= 1:
                    sub_name = option[0].split('.')
                    self.add_group(sub_name[-1])
                    
                
                if type(option[1]) == str:
                    self.add_string_option(option[0], option[1], None)
                    
                if type(option[1]) == float:
                    self.add_number_option(option[0], option[1], None)
                    
                
                    
            
            self.setVisible(True)    
            self.setUpdatesEnabled(True)
            
            self.supress_update = False
        
class ProcessOptionGroup(ProcessOptionPalette):
    
    def __init__(self, name):
        
        self.name = name
        
        super(ProcessOptionGroup, self).__init__()
        self.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum))
        self.main_layout.setContentsMargins(0,0,0,5)
        
    def _get_widget_names(self):
        
        item_count = self.child_layout.count()
        found = []
        for inc in range(0, item_count):
            
            item = self.child_layout.itemAt(inc)
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
        
        return self.group.parent()
        
    def move_up(self):
        
        parent = self.parent()
        layout = parent.child_layout
        index = layout.indexOf(self)
        
        if index == 0:
            return
        
        index = index - 1
        
        parent.child_layout.removeWidget(self)
        layout.insertWidget(index, self)
        
    def move_down(self):
        
        parent = self.parent()
        layout = parent.child_layout
        index = layout.indexOf(self)
        
        if index == (layout.count() - 1):
            return
        
        index = index + 1
        
        parent.child_layout.removeWidget(self)
        layout.insertWidget(index, self)
        
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
        
    def remove(self):
        parent = self.parent()
        
        parent.child_layout.removeWidget(self)
        self.deleteLater()
        
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
        
        self.parent()
        
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
    
    def _define_option_widget(self):
        return QtGui.QLabel(self.name)
    
    def get_name(self):
        
        name = self.option_widget.text()
        return name
    
    def set_name(self, name):
        
        self.option_widget.setText(name)
        
class ProcessOptionText(ProcessOption):
    
    def _define_option_widget(self):
        return qt_ui.GetString(self.name)
        
    def _setup_value_change(self):
        
        self.option_widget.text_changed.connect(self._value_change)
        
    def set_value(self, value):
        self.option_widget.set_text(value)
        
    def get_value(self):
        
        return str(self.option_widget.get_text())
        
class ProcessOptionNumber(ProcessOption):
    def _define_option_widget(self):
        return qt_ui.GetNumber(self.name)

    def _setup_value_change(self):
        self.option_widget.valueChanged.connect(self._value_change)
    
    def set_value(self, value):
        self.option_widget.set_value(value)
        
    def get_value(self):
        return self.option_widget.get_value()