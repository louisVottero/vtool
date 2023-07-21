
from __future__ import print_function
from __future__ import absolute_import

from . import ui_nodes
from ...process_manager import process

from vtool import qt, qt_ui, util, util_file

class MainWindow(qt_ui.BasicWindow):
    
    title = 'Ramen'
    tab_plus = ' + '
    
    def _build_widgets(self):
        self._auto_delete_graph_files = True
        self.directory = None
        self.__tab_changed_add = True
        
        self.tab_widget = qt.QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.main_layout.addWidget(self.tab_widget)
        
        self.file_widget = RamenFileWidget()
        self.file_widget.save_widget.save.connect(self._save)
        self.file_widget.save_widget.open.connect(self._open)
        
        self.main_layout.addWidget(self.file_widget, alignment = qt.QtCore.Qt.AlignBottom)
        
        self._init_tabs()
        
        self.tab_widget.currentChanged.connect(self._tab_changed)
        self.tab_widget.tabCloseRequested.connect(self._tab_close)
    
    def _init_tabs(self):
        self.empty_extra_tab = qt.QWidget()
        
        self.tab_widget.addTab(self.empty_extra_tab,self.tab_plus)
        
        self.tab_button = self.tab_widget.tabBar().tabButton(0, qt.QTabBar.RightSide)
        
        self.tab_widget.tabBar().setTabButton(0, qt.QTabBar.RightSide, None)
        self.tab_widget.tabBar().setTabButton(1, qt.QTabBar.RightSide, None)
        
    
    def sizeHint(self):
        width = 150
        height = 25
        width = util.scale_dpi(width)
        height = util.scale_dpi(height)
        return qt.QtCore.QSize(width, height)
    
    def _tab_exists(self, name):
        count = self.tab_widget.count()
        for inc in range(count, -1, -1):
            tab_text = self.tab_widget.tabText(inc)
            
            if tab_text == name:
                return True
        return False
    
    def _get_next_tab_name(self):
        count = self.tab_widget.count()
        name = 'graph%s' % count
        accum = count
        
        while self._tab_exists(name):
            accum += 1
            name = 'graph%s' % accum
        
        return name
    
    def _add_tab(self, name = None):
        
        nodes = ui_nodes.NodeDirectoryWindow()
        count = self.tab_widget.count()
        if not name:
            name = self._get_next_tab_name()
            
        self.tab_widget.insertTab(count-1, nodes, name)
        self.tab_widget.setCurrentIndex(count-1)
        self.tab_widget.widget(count-1)
        
        return nodes
    
    def _tab_changed(self, index):
        if self.__tab_changed_add:
            
            count = self.tab_widget.count()
            if index == count-1 and self.tab_widget.tabText(count-1) == self.tab_plus:
                self._add_tab()
        else:
            self.__tab_changed_add = True
        
    def _tab_close(self, index):
        
        if index > 0:
            self.tab_widget.setCurrentIndex(index - 1)
        
        if self._auto_delete_graph_files:
            widget = self.tab_widget.widget(index)
            
            if widget and hasattr(widget, 'directory'):
                
                directory = widget.directory

                util_file.delete_dir(directory)
        
        self.tab_widget.removeTab(index)
    
    def _close_tabs(self):
        
        self._auto_delete_graph_files = False
        
        count = self.tab_widget.count()
        for inc in range(count, -1, -1):
            self._tab_close(inc)
        
        self._init_tabs()
        
        self._auto_delete_graph_files = True
        
    def _save(self):
        count = self.tab_widget.count()
        
        for inc in range(0, count):
            widget = self.tab_widget.widget(inc)
            if hasattr(widget, 'main_view'):
                widget.main_view.save()
    
    def _open(self):
        count = self.tab_widget.count()
                
        for inc in range(0, count):
            widget = self.tab_widget.widget(inc)
            if hasattr(widget, 'main_view'):
                widget.main_view.open()
        
    def _set_directory(self):
        process_path = util.get_env('VETALA_CURRENT_PROCESS')
        
        directory = None
        
        if process_path:
            process_inst = process.Process()
            process_inst.set_directory(process_path)
            ramen_path = process_inst.get_ramen_path()
        
            directory = ramen_path
        
        if directory:
            directory = util_file.join_path(directory, 'graphs')
        
        if not directory:
            return
        
        self.directory = directory
        
    def _sync_tabs_to_folders(self):
        folders = util_file.get_folders(self.directory)
        
        if not folders:
            node_widget = self.tab_widget.widget(0)
            full_path = util_file.join_path(self.directory, 'graph1')
            node_widget.set_directory(full_path)
            return
        folders.sort()
        
        for folder in folders:
            if not folder == 'graph1':
                node_widget = self._add_tab(folder)
            else:
                node_widget = self.tab_widget.widget(0)
            
            if hasattr(node_widget, 'set_directory'):
                full_path = util_file.join_path(self.directory, folder)
                node_widget.set_directory(full_path)
        
    def set_directory(self, directory):
        
        self._set_directory()
        
        self._close_tabs()
        
        self._sync_tabs_to_folders()

class RamenFileWidget(qt_ui.FileManagerWidget):
    
    def _define_main_tab_name(self):
        return 'JSON'

class TabCloseButton(qt.QPushButton):
    def __init__(self, text = 'X', parent = None):
        super(TabCloseButton, self).__init__(text, parent)
        