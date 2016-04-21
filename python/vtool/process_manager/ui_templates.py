# Copyright (C) 2016 Louis Vottero louis.vot@gmail.com    All rights reserved.

import ui_view
from vtool import qt_ui

if qt_ui.is_pyqt():
    from PyQt4 import QtGui, QtCore, Qt, uic
if qt_ui.is_pyside():
    from PySide import QtCore, QtGui

class TemplateWidget(qt_ui.BasicWidget):
    
    current_changed = qt_ui.create_signal()
    add_template = qt_ui.create_signal(object, object)
    merge_template = qt_ui.create_signal(object, object)
    
    def _build_widgets(self):
        
        title_layout = QtGui.QHBoxLayout()
        
        title_label = QtGui.QLabel('Template Source')
        
        self.template_combo = QtGui.QComboBox()
        self.template_combo.currentIndexChanged.connect(self._change)
        
        title_layout.addWidget(title_label)
        title_layout.addWidget(self.template_combo)
        
        self.template_tree = TemplateTree()
        
        self.template_tree.add_template.connect(self._add_template)
        self.template_tree.merge_template.connect(self._merge_template)
        
        self.main_layout.addSpacing(10)
        self.main_layout.addLayout(title_layout)
        self.main_layout.addSpacing(10)
        self.main_layout.addWidget(self.template_tree)
        
        self.template_dict = {}
        self.handle_current_change = True
        self.active = False
        self.current = None
        self.template_list = None
        
    def _add_template(self, process_name, directory):
        
        self.add_template.emit(process_name, directory)
        
    def _merge_template(self, process_name, directory):
        self.merge_template.emit(process_name, directory)
        
    def _change(self, index):
        
        if not self.handle_current_change:
            return
        
        name = self.template_combo.currentText()
        name = str(name)
        
        directory = str(self.template_dict[name])
        
        if self.active:
            self.template_tree.set_directory(directory, refresh = True)
        
        current_name = name
        if name == directory:
            current_name = ''
        
        self.settings.set('template_directory', [current_name, directory])
        self.current_changed.emit()
        
    def set_templates(self, template_list):
        
        self.template_list = template_list
        
        if not self.active:
            return
        
        self.handle_current_change = False
        self.template_dict = {}
        self.template_combo.clear()
        
        current_directory = self.settings.get('template_directory')
        
        inc = 0
        current_inc = 0
        
        for template in template_list:
            
            if not type(template) == list:
                template = [None, template]
                
            name = template[0]
            directory = template[1]
            
            if not name:
                name = directory
            
            self.template_combo.addItem(name)
                
            directory = str(directory)
                
            self.template_dict[name] = directory
        
            if current_directory == directory:
                current_inc = inc
        
            inc += 1
            
        
        self.template_combo.setCurrentIndex(current_inc)
        
        self.handle_current_change = True
            
    def set_current(self, name):
        
        
        self.handle_current_change = True
        
        self.current = name
        
        count = self.template_combo.count()
        
        for inc in range(0, count):
            
            text = self.template_combo.itemText(inc)
            
            text = str(text)
            
            if text == name:
                if self.active:
                    if self.template_combo.currentIndex() != inc:
                        self.handle_current_change = False
                        self.template_combo.setCurrentIndex(inc)
                        self.handle_current_change = True
                    if self.template_combo.currentIndex() == inc:
                        self.template_tree.set_directory(self.template_dict[name], refresh = True)
                    
                return
    
    def set_settings(self, settings):
        self.settings = settings
        
    def set_active(self, active_state):
        self.active = active_state
        
        if active_state:
            self.set_templates(self.template_list)
            self.set_current(self.current)
            
                
class TemplateTree(ui_view.ProcessTreeWidget):
    
    add_template = qt_ui.create_signal(object, object)
    merge_template = qt_ui.create_signal(object, object)
    
    def __init__(self):
        super(TemplateTree, self).__init__()
        
        self.setDragEnabled(False)
    
    def _item_menu(self, position):
                
        self.context_menu.exec_(self.viewport().mapToGlobal(position))
        
    def _create_context_menu(self):
        
        self.context_menu = QtGui.QMenu()
        
        copy = self.context_menu.addAction('Paste under Current Process')
        copy.triggered.connect(self._add_template)
        
        merge = self.context_menu.addAction('Merge into Current Process')
        merge.triggered.connect(self._merge_template)
        
    def _get_item_parent_path(self):
        items = self.selectedItems()
        if not items:
            return
        
        parent_path = self._get_parent_path(items[0])
        
        return parent_path
        
    def _add_template(self):
        
        parent_path = self._get_item_parent_path()
        
        self.add_template.emit(parent_path, self.directory)
        
    def _merge_template(self):
        
        parent_path = self._get_item_parent_path()
        
        self.merge_template.emit(parent_path, self.directory)