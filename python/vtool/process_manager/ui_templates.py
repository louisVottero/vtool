# Copyright (C) 2016 Louis Vottero louis.vot@gmail.com    All rights reserved.

import ui_view
from vtool import qt_ui

if qt_ui.is_pyqt():
    from PyQt4 import QtGui, QtCore, Qt, uic
if qt_ui.is_pyside():
    from PySide import QtCore, QtGui

class TemplateWidget(qt_ui.BasicWidget):
    
    def _build_widgets(self):
        
        title_layout = QtGui.QHBoxLayout()
        
        title_label = QtGui.QLabel('Template Source')
        
        self.template_combo = QtGui.QComboBox()
        self.template_combo.currentIndexChanged.connect(self._change)
        
        title_layout.addWidget(title_label)
        title_layout.addWidget(self.template_combo)
        
        self.template_tree = TemplateTree()
        
        self.main_layout.addSpacing(10)
        self.main_layout.addLayout(title_layout)
        self.main_layout.addSpacing(10)
        self.main_layout.addWidget(self.template_tree)
        
        #template_tree.set_directory('N:/proddev/rig_dev/vtool_templates', refresh = True)
        
        self.template_dict = {}
        self.handle_current_change = True
        
    def _change(self, index):
        
        print 'change', self.handle_current_change
        
        if not self.handle_current_change:
            return
        
        name = self.template_combo.currentText()
        name = str(name)
        
        directory = str(self.template_dict[name])
        print name, directory
        
        self.template_tree.set_directory(directory, refresh = True)
        
    def set_templates(self, template_list):
        
        self.handle_current_change = False
        self.template_dict = {}
        self.template_combo.clear()
        
        for template in template_list:
            
            if not type(template) == list:
                template = [None, template]
                
            name = template[0]
            directory = template[1]
            
            if not name:
                name = directory
            
            self.template_combo.addItem(name)
                
            self.template_dict[name] = str(directory)
        
        self.handle_current_change = True
            
    def set_current(self, name):
        
        self.handle_current_change = True
        
        count = self.template_combo.count()
        
        for inc in range(0, count):
            
            text = self.template_combo.itemText(inc)
            
            text = str(text)
            
            print text, name
            
            if text == name:
                
                if self.template_combo.currentIndex() != inc:
                
                    self.template_combo.setCurrentIndex(inc)
                
                if self.template_combo.currentIndex() == inc:
                    self.template_tree.set_directory(self.template_dict[name], refresh = True)
                return
                
class TemplateTree(ui_view.ProcessTreeWidget):
    
    def __init__(self):
        super(TemplateTree, self).__init__()
        
        self.setDragEnabled(False)
    
    def _item_menu(self, position):
                
        self.context_menu.exec_(self.viewport().mapToGlobal(position))
        
    def _create_context_menu(self):
        
        self.context_menu = QtGui.QMenu()
        
        add_into = self.context_menu.addAction('Copy To Current Process')
        add_into.triggered.connect(self._add_template)
        
    def _add_template(self):
        print 'add templates'
        return