from __future__ import print_function
from __future__ import absolute_import
import os
from . import ui_nodes
from .. import eval
from ...process_manager import process

from vtool import qt, qt_ui, util, util_file


class MainWindow(qt_ui.BasicWindow):
    title = 'Ramen'
    tab_plus = ' + '

    def __init__(self):
        super(MainWindow, self).__init__()

        self._last_directory = None

    def _build_widgets(self):
        self._auto_delete_graph_files = True
        self.directory = None
        self.__tab_changed_add = True

        self.tab_widget = qt.QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.main_layout.addWidget(self.tab_widget)

        layout = qt.QHBoxLayout()

        run = qt.QPushButton('  Run Graph  ')
        run.setSizePolicy(qt.QSizePolicy.Minimum, qt.QSizePolicy.Minimum)

        self.file_widget = RamenFileWidget()
        self.file_widget.save_widget.save.connect(self._save)
        self.file_widget.save_widget.open.connect(self._open)

        layout.addSpacing(10)
        layout.addWidget(run)
        layout.addSpacing(10)
        layout.addWidget(self.file_widget, alignment=qt.QtCore.Qt.AlignBottom)

        self.main_layout.addLayout(layout)

        self._init_tabs()

        self.tab_widget.currentChanged.connect(self._tab_changed)

        self.tab_widget.tabCloseRequested.connect(self._tab_close)
        run.clicked.connect(self._run_graph)

    def _init_tabs(self):
        self.empty_extra_tab = qt.QWidget()

        self.tab_widget.addTab(self.empty_extra_tab, self.tab_plus)

        self.tab_button = self.tab_widget.tabBar().tabButton(0, qt.QTabBar.RightSide)

        self.tab_widget.tabBar().setTabButton(0, qt.QTabBar.RightSide, None)
        self.tab_widget.tabBar().setTabButton(1, qt.QTabBar.RightSide, None)

    def tabInserted(self, index):
        super(MainWindow, self).tabInserted(index)

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

    def _create_folder(self, name, index):

        widget = self.tab_widget.widget(index)

        folder = util_file.join_path(self.directory, name)

        if not util_file.exists(folder):
            folder = util_file.create_dir(folder)

            widget.set_directory(folder)

    def _add_tab(self, name=None):
        node_widget = ui_nodes.NodeDirectoryWindow()
        count = self.tab_widget.count()

        if not name:
            name = self._get_next_tab_name()

        self.tab_widget.insertTab(count - 1, node_widget, name)
        self.tab_widget.setCurrentIndex(count - 1)

        return node_widget

    def _tab_changed(self, index):
        if self.__tab_changed_add:

            count = self.tab_widget.count()
            if index == count - 1 and self.tab_widget.tabText(count - 1) == self.tab_plus:
                name = self._add_tab()
                # self._create_folder(name, (count-1))
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

    def _run_graph(self):

        index = self.tab_widget.currentIndex()

        util.show('Run Graph %s' % (index + 1))

        widget = self.tab_widget.widget(index)

        if widget.directory:
            result = widget.main_view.save()

            eval.run(result)

    def _save(self):
        count = self.tab_widget.count()

        for inc in range(0, count):
            widget = self.tab_widget.widget(inc)
            if hasattr(widget, 'main_view'):
                name = self.tab_widget.tabText(inc)
                self._create_folder(name, inc)
                result = widget.main_view.save()

    def _open(self):
        count = self.tab_widget.count()

        for inc in range(0, count):
            widget = self.tab_widget.widget(inc)
            if hasattr(widget, 'main_view'):
                widget.main_view.open()

    def _set_directory(self, directory=None):

        if not directory:
            process_path = os.environ.get('VETALA_CURRENT_PROCESS')

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
            node_widget.directory = full_path
            return
        folders.sort()

        for folder in folders:
            node_widget = None
            if not folder == 'graph1':
                node_widget = self._add_tab(folder)
            else:
                count = self.tab_widget.count()

                for inc in range(0, count):
                    title = self.tab_widget.tabText(inc)
                    if title == folder:
                        node_widget = self.tab_widget.widget(inc)
                        break

            if hasattr(node_widget, 'set_directory'):
                full_path = util_file.join_path(self.directory, folder)
                node_widget.set_directory(full_path)

    def save(self):
        self._save()

    def set_directory(self, directory=None):

        self._set_directory(directory)

        if self._last_directory:
            if self.directory == self._last_directory:
                return

        self._last_directory = self.directory

        self._close_tabs()

        self._sync_tabs_to_folders()


class RamenFileWidget(qt_ui.FileManagerWidget):

    def _define_main_tab_name(self):
        return 'JSON'


class TabCloseButton(qt.QPushButton):
    def __init__(self, text='X', parent=None):
        super(TabCloseButton, self).__init__(text, parent)
