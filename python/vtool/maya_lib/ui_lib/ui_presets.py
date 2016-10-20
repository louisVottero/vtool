# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

from vtool.maya_lib import ui_core
from vtool.maya_lib import attr

from vtool import qt_ui
from vtool import util

if qt_ui.is_pyqt():
    from PyQt4 import QtCore, Qt, uic
    from PyQt4.QtGui import *
if qt_ui.is_pyside():
        from PySide import QtCore
        from PySide.QtGui import *
if qt_ui.is_pyside2():
        from PySide2 import QtCore
        from PySide2.QtGui import *
        from PySide2.QtWidgets import *

import maya.cmds as cmds

class Presets(qt_ui.BasicWidget):
    
    title = 'PRESET'
    
    def __init__(self):
        self.settings = []
        
        if not cmds.objExists('presets'):
            cmds.group(em = True, n = 'presets')
        
        super(Presets, self).__init__()
        

            
        
        
        
    def _build_widgets(self):
        
        tabs = qt_ui.NewItemTabWidget()
        
        self.tabs = tabs
        
        self.main_layout.addWidget(tabs)
        
        preset_settings = Preset_Settings()
        
        preset_settings.export_needed.connect(self.export)
        
        tabs.addTab(preset_settings, 'Preset')
        self.settings.append(preset_settings)
        self.export()
        tabs.addTab(QWidget(), '+')
        tabs.tab_add.connect(self._tab_add)
        
        tabs.tab_closed.connect(self._close_tab)
        tabs.tab_renamed.connect(self._rename_tab)
        
    def _add_tab(self):
        settings = Preset_Settings()
        settings.export_needed.connect(self.export)
        self.tabs.addTab(settings, 'Preset')
        self.settings.append(settings)
        self.export()
        
        
    def _tab_add(self, index):
        
        self._add_tab()
        
        
    def _rename_tab(self, current_index):
        
        self.export()
    
    def _close_tab(self, current_index):
        
        self.settings.pop(current_index)
        self.export()
        
    def export(self):
        
        print 'export data!!!', self.settings
        
        tab_count = self.tabs.count()
        
        data = []
        
        
        
        for inc in range(0, tab_count):
            
            tab_title = self.tabs.tabText(inc)
            
            if tab_title == '+':
                continue
            
            tab_widget = self.tabs.widget(inc)
            
            sub_data = []
            
            if tab_widget:
                tab_data = tab_widget.get_data()
                sub_data = [tab_title, tab_data]
            
            data.append(sub_data)
            
        
        store = attr.StoreData('presets')
        store.set_data( str(data) )
        
        
class Preset_Settings(qt_ui.BasicWidget):
    
    export_needed = qt_ui.create_signal()
    
    def _define_main_layout(self):
        return QHBoxLayout()
    
    def _build_widgets(self):
        
        layout1 = QVBoxLayout()
        layout2 = QVBoxLayout()
        
        self.preset_settings = SettingTree()
        self.preset_settings.export_needed.connect(self._export_needed)
        self.preset_nodes = NodeTree()
        
        self.preset_nodes.hide()
        
        layout1.addWidget(self.preset_settings)
        layout2.addWidget(self.preset_nodes)
        
        self.load_attr_button = QPushButton('Update Attributes')
        self.load_attr_button.hide()
        
        layout2.addWidget(self.load_attr_button)
        
        self.preset_settings.setHeaderLabel('Setting')
        self.preset_nodes.setHeaderLabel('Nodes')
        
        self.main_layout.addLayout(layout1)
        self.main_layout.addLayout(layout2)
        
        self.preset_settings.itemSelectionChanged.connect(self._preset_select_change)
        self.preset_settings.itemClicked.connect(self._preset_clicked)
        self.preset_settings.item_renamed.connect(self._item_renamed)
        
        self.load_attr_button.clicked.connect(self._load_attributes)
        
        self.preset_attributes = {}
        
    def _export_needed(self):
        
        self.export_needed.emit()
        
    def _item_renamed(self, old_name, new_name):
        
        print old_name, new_name, self.preset_attributes
        
        if not self.preset_attributes.has_key(old_name):
            self.export_needed.emit()
            return
        
        stored_value = self.preset_attributes[old_name]
        self.preset_attributes.pop(old_name)
        
        
        
        self.preset_attributes[new_name] = stored_value
        
        print 'about to export after rename'
        
        self.export_needed.emit()
        
    def _preset_clicked(self, item, column):
        
        print 'item clicked!'
        
        items = self.preset_settings.selectedItems()
        current_item = items[0]
        
        if self.preset_attributes:
            
            current_text = current_item.text(0)
            
            print current_text
            
            if self.preset_attributes.has_key(current_text):
                attribute_values = self.preset_attributes[current_text]
                
                print attribute_values
                
                for values in attribute_values:
                    node = values[0]
                    attributes = values[1]
                    print node, attributes
                    attr.set_attribute_values(node, attributes)
        
    def _preset_select_change(self):
        
        print 'preset selection change!'
        
        items = self.preset_settings.selectedItems()
        
        if not items:
            self.preset_nodes.hide()
            self.load_attr_button.hide()
            
        if items:
            self.preset_nodes.show()
            self.load_attr_button.show()
        
        
    
    def _load_attributes(self):
        
        items = self.preset_settings.selectedItems()
        
        if not items:
            return
        
        current_item = items[0]
        current_name = current_item.text(0)
        
        self.preset_attributes[current_name] = []

        node_count = self.preset_nodes.topLevelItemCount()
        
        print 'node count', node_count
        
        for inc2 in range(0, node_count):
            
            print 'inc!',inc2
            
            node_item = self.preset_nodes.topLevelItem(inc2)
            
            print node_item
            
            node_name = node_item.text(0)
            
            attribute_values = attr.get_attribute_values(node_name)
            
            self.preset_attributes[current_name] += [[node_name, attribute_values]]
            
            print 'presets!!!', self.preset_attributes
            
        self.export_needed.emit()
            
    def get_data(self):
        
        preset_count = self.preset_settings.topLevelItemCount() 
        
        presets = []
        
        for inc in range(0, preset_count):
            
            
            
            item = self.preset_settings.topLevelItem(inc)
            
            preset_name = item.text(0)
            
            print 'getting preset data', preset_name, self.preset_attributes
            
            preset_data = []
            
            if self.preset_attributes.has_key(preset_name):
                preset_data = self.preset_attributes[preset_name]
            
            presets += [[preset_name, preset_data]]
    
        return presets
    
class SettingTree(QTreeWidget):
    
    item_renamed = qt_ui.create_signal(object, object)
    export_needed = qt_ui.create_signal()
    
    def __init__(self):
        
        self.preset_attributes = {}
        super(SettingTree, self).__init__()
        
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._item_menu)
        
        
        
        self._create_context_menu()

        
    def _item_menu(self, position):
        
        self.context_menu.exec_(self.viewport().mapToGlobal(position))
        
    def _get_existing_items(self):        
        existing_items = []
        
        top_count = self.topLevelItemCount()
        
        for inc in range(0, top_count):
            item = self.topLevelItem(inc)
            existing_items.append(item.text(0))
            
        return existing_items
        
    def _create_context_menu(self):
        
        self.context_menu = QMenu()
        
        self.new_action = self.context_menu.addAction('New')
        self.rename_action = self.context_menu.addAction('Rename')
        self.remove_action = self.context_menu.addAction('Remove')
        
        self.new_action.triggered.connect(self.add_item)
        self.rename_action.triggered.connect(self.rename_item)
        self.remove_action.triggered.connect(self.remove_item)
        
    def _inc_name(self, name):
        
        existing = self._get_existing_items()
        
        inc = 1
        
        while name in existing:
            
            name = util.increment_last_number(name)
            
            inc += 1
            
        return name
        
    def add_item(self):
        
        item = QTreeWidgetItem()
        item.setText(0, self._inc_name('Preset'))
        item.setSizeHint(0, QtCore.QSize(100, 18))
        self.addTopLevelItem(item)
        self.preset_attributes[str(item.text(0))] = []
        self.setCurrentItem(item)
        
        self.rename_item(False)
        self.export_needed.emit()
        
        
    def rename_item(self, inc_name = True):
        
        item = self.currentItem()
        
        if not item:
            return
        
        name = item.text(0)        
        new_name = qt_ui.get_new_name('New Name', self, name)
        
        if inc_name:
            
            existing = self._get_existing_items()
            
            inc = 1
            
            while new_name in existing:
                
                self._inc_name(new_name)
                
                inc += 1
            
        item.setText(0, new_name)
        self.item_renamed.emit(name, new_name)
        
    def remove_item(self):
        
        current_item = self.currentItem()
        index = self.indexFromItem(current_item)
        self.takeTopLevelItem(index.row())
        self.export_needed.emit()

class NodeTree(QTreeWidget):
    
    def __init__(self):
        super(NodeTree, self).__init__()
        
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._item_menu)
        
        self._create_context_menu()
        
    def _item_menu(self, position):
        
        self.context_menu.exec_(self.viewport().mapToGlobal(position))
        
    def _create_context_menu(self):
        
        self.context_menu = QMenu()
        
        self.set_action = self.context_menu.addAction('Set Node(s)')
        self.remove_action = self.context_menu.addAction('Remove')
        
        self.set_action.triggered.connect(self._set_nodes)
        self.remove_action.triggered.connect(self._remove_nodes)
        
    def _set_nodes(self):
        
        selection = cmds.ls(sl = True)
        
        top_count = self.topLevelItemCount()
        
        existing_items = []
        
        for inc in range(0, top_count):
            item = self.topLevelItem(inc)
            existing_items.append(item.text(0))
        
        for thing in selection:
            
            if thing in existing_items:
                continue
            
            item = QTreeWidgetItem()
            
            item.setText(0, thing)
            
            self.addTopLevelItem(item)
        
        items = self.selectedItems()
        
        for item in items:
            
            print item.text(0)
    
    def _remove_nodes(self):
        
        items = self.selectedItems()
        
        for item in items:
            index = self.indexFromItem(item)
            self.takeTopLevelItem(index.row())
        
        