
from __future__ import print_function
from __future__ import absolute_import

from . import ui_nodes

from vtool import qt, qt_ui, util

class MainWindow(qt_ui.BasicWindow):
    
    title = 'Ramen'
    tab_plus = ' + '
    
    def _build_widgets(self):
        
        self.__tab_changed_add = True
        
        self.tab_widget = qt.QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.main_layout.addWidget(self.tab_widget)
        
        self.empty_extra_tab = qt.QWidget()
        
        self.tab_widget.addTab(self.empty_extra_tab,self.tab_plus)
        self._add_tab()
        
        self.tab_widget.tabBar().setTabButton(0, qt.QTabBar.RightSide, None)
        self.tab_widget.tabBar().setTabButton(1, qt.QTabBar.RightSide, None)
        
        self.tab_widget.currentChanged.connect(self._tab_changed)
        self.tab_widget.tabCloseRequested.connect(self._tab_close)
    
    def sizeHint(self):
        width = 150
        height = 25
        width = util.scale_dpi(width)
        height = util.scale_dpi(height)
        return qt.QtCore.QSize(width, height)
    
    def _add_tab(self):
        
        nodes = ui_nodes.NodeDirectoryWindow()
        count = self.tab_widget.count()
        self.tab_widget.insertTab(count-1, nodes, 'Graph %s' % count)
        self.tab_widget.setCurrentIndex(count-1)
    
    def _tab_changed(self, index):
        if self.__tab_changed_add:
            
            count = self.tab_widget.count()
            if index == count-1 and self.tab_widget.tabText(count-1) == self.tab_plus:
                self._add_tab()
        else:
            self.__tab_changed_add = True
            
    def _tab_close(self, index):
        
        self.tab_widget.setCurrentIndex(index - 1)
        self.tab_widget.removeTab(index)
        
    def set_directory(self, directory):
        
        count = self.tab_widget.count()
        
        for inc in range(0, count):
            widget = self.tab_widget.widget(inc)
            if hasattr(widget, 'set_directory'):
                widget.set_directory(directory)
        
            