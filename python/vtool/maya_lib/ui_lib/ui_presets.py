# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

from vtool.maya_lib import ui_core
from vtool.maya_lib import attr

from vtool import qt_ui, qt

from vtool import util

import maya.cmds as cmds

class Presets(qt_ui.BasicWidget):
    
    title = 'PRESET'
    
    def __init__(self):
        self.settings = []
        
        super(Presets, self).__init__()
        
        ui_core.new_scene_signal.signal.connect(self._load)
        #ui_core.open_scene_signal.signal.connect(self._load)
        ui_core.read_scene_signal.signal.connect(self._load)
        
        self.main_layout.setContentsMargins(10,10,10,10)
        
        self._load()
        
        
        
    def _load(self):
        self.no_export = True
        
        preset_group = 'presets'
        
        self.settings = []
        
        self.tabs.close_tabs()
        
        if cmds.objExists(preset_group):
                
            store = attr.StoreData(preset_group)
            data = store.eval_data()
            
            if data:
                
            
                for tab in data:
                    tab_name = tab[0]
                    tab_settings = tab[1]
                    
                    preset_settings = Preset_Settings()
                    preset_settings.export_needed.connect(self.export)
                    self.tabs.addTab(preset_settings, tab_name)
                    
                    self.settings.append(preset_settings)
                    
                    for settings in tab_settings:
                        preset_settings.add_item(settings[0], settings[1])
                        
                        if settings[1]:
                            nodes = []
                            
                            for setting in settings[1]:
                            
                                nodes.append(setting[0])
                        
                            if nodes:
                                preset_settings.preset_nodes.set_nodes(nodes)
                                
                self.tabs.addTab(qt.QWidget(), '+')
            
            if not data:
                self._add_default_tabs()
        
        if not cmds.objExists(preset_group):
            cmds.group(em = True, n = 'presets')
            self._add_default_tabs()
            
        
        self.no_export = False
        
    def _add_default_tabs(self):
        preset_settings = Preset_Settings()
        
        self.tabs.addTab(preset_settings, 'Preset')
        self.settings.append(preset_settings)
        preset_settings.export_needed.connect(self.export)
        self.tabs.addTab(qt.QWidget(), '+')
        
    def _build_widgets(self):
        
        
        
        tabs = qt_ui.NewItemTabWidget()
        
        self.tabs = tabs
        
        self.main_layout.addWidget(tabs)
        
        tabs.tab_add.connect(self._tab_add)
        
        tabs.tab_closed.connect(self._close_tab)
        tabs.tab_renamed.connect(self._rename_tab)
        
        
        
    def _add_tab(self, name = None):
        
        if not name:
            name = 'Preset'
        
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
        
        if self.settings:
            self.settings.pop(current_index)
            
        self.export()
        
    def export(self):
        
        if self.no_export:
            return
        
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
        return qt.QHBoxLayout()
    
    def _build_widgets(self):
        
        layout1 = qt.QVBoxLayout()
        layout2 = qt.QVBoxLayout()
        
        self.preset_settings = SettingTree()
        self.preset_settings.export_needed.connect(self._export_needed)
        self.preset_nodes = NodeTree()
        
        self.preset_nodes.hide()
        
        self.load_attr_button = qt.QPushButton('Update Attributes')
        self.load_attr_button.setDisabled(True)
        self.load_attr_button.setMaximumWidth(100)
        
        
        
        layout1.addWidget(self.preset_settings)
        layout2.addWidget(self.preset_nodes)
        
        layout1.addSpacing(20)
        
        layout1.addWidget(self.load_attr_button)
        
        layout1.addSpacing(20)
        
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
        
        if not self.preset_attributes.has_key(old_name):
            self.export_needed.emit()
            return
        
        stored_value = self.preset_attributes[old_name]
        self.preset_attributes.pop(old_name)
        
        self.preset_attributes[new_name] = stored_value
        
        self.export_needed.emit()
        
    def _load_item(self,item):
        
        if self.preset_attributes:
            
            current_text = item.text(0)
            
            if self.preset_attributes.has_key(current_text):
                attribute_values = self.preset_attributes[current_text]
                
                for values in attribute_values:
                    node = values[0]
                    attributes = values[1]
                    
                    attr.set_attribute_values(node, attributes)
                    
                    
    def _preset_clicked(self, item, column):
        
        items = self.preset_settings.selectedItems()
        current_item = items[0]
        
        self._load_item(current_item)
        
    def _preset_select_change(self):
        
        items = self.preset_settings.selectedItems()
        
        if not items:
            self.preset_nodes.hide()
            self.load_attr_button.setDisabled(True)
            
        if items:
            self.preset_nodes.show()
            self.load_attr_button.setEnabled(True)
        
        self._load_item(items[0])
    
    def _load_attributes(self):
        
        items = self.preset_settings.selectedItems()
        
        if not items:
            return
        
        current_item = items[0]
        current_name = current_item.text(0)
        
        self.preset_attributes[current_name] = []

        node_count = self.preset_nodes.topLevelItemCount()
        
        for inc2 in range(0, node_count):
            
            node_item = self.preset_nodes.topLevelItem(inc2)
            
            node_name = node_item.text(0)
            
            attribute_values = attr.get_attribute_values(node_name, keyable_only=False)
            
            self.preset_attributes[current_name] += [[node_name, attribute_values]]
            
            
        self.export_needed.emit()
            
    def get_data(self):
        
        preset_count = self.preset_settings.topLevelItemCount() 
        
        presets = []
        
        for inc in range(0, preset_count):
            
            item = self.preset_settings.topLevelItem(inc)
            
            preset_name = item.text(0)
            
            preset_data = []
            
            if self.preset_attributes.has_key(preset_name):
                preset_data = self.preset_attributes[preset_name]
            
            presets += [[preset_name, preset_data]]
    
        return presets
    
    def add_item(self, name, data = []):
        
        self.preset_settings.add_item(name = name, rename = False)
        self.preset_attributes[name] = data
    
class SettingTree(qt.QTreeWidget):
    
    item_renamed = qt_ui.create_signal(object, object)
    export_needed = qt_ui.create_signal()
    
    def __init__(self):
        
        
        super(SettingTree, self).__init__()
        
        self.setContextMenuPolicy(qt.QtCore.Qt.CustomContextMenu)
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
        
        self.context_menu = qt.QMenu()
        
        self.new_action = self.context_menu.addAction('New')
        self.rename_action = self.context_menu.addAction('Rename')
        self.remove_action = self.context_menu.addAction('Remove')
        self.context_menu.addSeparator()
        move_up = self.context_menu.addAction('Move Up')
        move_down = self.context_menu.addAction('Move Down')
        
        self.new_action.triggered.connect(self.add_item)
        self.rename_action.triggered.connect(self.rename_item)
        self.remove_action.triggered.connect(self.remove_item)
        
        move_up.triggered.connect(self.move_up)
        move_down.triggered.connect(self.move_down)
        
    def _inc_name(self, name):
        
        existing = self._get_existing_items()
        
        inc = 1
        
        while name in existing:
            
            name = util.increment_last_number(name)
            
            inc += 1
            
        return name
        
    def add_item(self, name = None, rename = True):
        
        if not name:
            name = 'Preset'
        
        item = qt.QTreeWidgetItem()
        item.setText(0, self._inc_name(name))
        item.setSizeHint(0, qt.QtCore.QSize(100, 18))
        self.addTopLevelItem(item)
        
        self.setCurrentItem(item)
        
        if rename:
            self.rename_item(False)
            
        self.export_needed.emit()
        
        
    def rename_item(self, inc_name = True):
        
        item = self.currentItem()
        
        if not item:
            return
        
        name = item.text(0)        
        new_name = qt_ui.get_new_name('New Name', self, name)
        
        if not new_name:
            return
        
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

    def move_up(self):
        
        item = self.currentItem()
        index = self.indexFromItem(item)
        
        index = index.row()
        
        if index < 1:
            return
        
        self.takeTopLevelItem(index)
        self.insertTopLevelItem(index-1, item)
        
        self.setCurrentItem(item)
        
    def move_down(self):

        item = self.currentItem()
        index = self.indexFromItem(item)
        index = index.row()
        
        if index == (self.topLevelItemCount() - 1):
            return
        
        self.takeTopLevelItem(index)
        
        
        
        self.insertTopLevelItem(index + 1, item)
        
        self.setCurrentItem(item)
        
class NodeTree(qt.QTreeWidget):
    
    def __init__(self):
        super(NodeTree, self).__init__()
        
        self.setContextMenuPolicy(qt.QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._item_menu)
        
        self._create_context_menu()
        
        #self.setSelectionMode(self.NoSelection)
        
    def _item_menu(self, position):
        
        item = self.itemAt(position)
        
        self.menu_item = item 
        
        self.context_menu.exec_(self.viewport().mapToGlobal(position))
        
    def _create_context_menu(self):
        
        self.context_menu = qt.QMenu()
        
        self.set_action = self.context_menu.addAction('Set Nodes')
        self.remove_action = self.context_menu.addAction('Remove')
        
        self.set_action.triggered.connect(self.set_nodes)
        self.remove_action.triggered.connect(self._remove_nodes)
        
    def _remove_nodes(self):
        
        items = self.selectedItems()
        
        for item in items:
            index = self.indexFromItem(item)
            self.takeTopLevelItem(index.row())
        
    def set_nodes(self, nodes = []):
        
        if not nodes:
            nodes = cmds.ls(sl = True)
            
        if not nodes:
            return
        
        top_count = self.topLevelItemCount()
        
        existing_items = []
        
        for inc in range(0, top_count):
            item = self.topLevelItem(inc)
            existing_items.append(item.text(0))
        
        for thing in nodes:
            
            if thing in existing_items:
                continue
            
            item = qt.QTreeWidgetItem()
            
            item.setText(0, thing)
            
            self.addTopLevelItem(item)
        