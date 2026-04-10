# Copyright (C) 2024 Louis Vottero louis.vot@gmail.com    All rights reserved.
from __future__ import print_function
from __future__ import absolute_import
import os
import shutil

from . import ui_nodes
from .. import eval
from ...process_manager import process

from vtool import qt, qt_ui, util, util_file


class MainWindow(qt_ui.BasicWindow):
    title = 'Ramen'
    tab_plus = ' + '

    def __init__(self):
        super(MainWindow, self).__init__()

    def _build_widgets(self):
        self._auto_delete_graph_files = True
        self.directory = None
        self.__tab_changed_add = True

        self.tab_widget = qt.QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.main_layout.addSpacing(20)
        self.main_layout.addWidget(self.tab_widget)

        layout = qt.QHBoxLayout()

        run = qt.QPushButton('  Run Graph  ')
        run.setSizePolicy(qt.QSizePolicy.Minimum, qt.QSizePolicy.Minimum)

        step = qt.QPushButton(' Step ')
        step.setSizePolicy(qt.QSizePolicy.Minimum, qt.QSizePolicy.Minimum)

        if util.in_unreal:
            clear_library = qt.QPushButton(' Clear Library ')
            clear_library.setSizePolicy(qt.QSizePolicy.Minimum, qt.QSizePolicy.Minimum)

        auto_update_graph = qt_ui.GetCheckBox('Auto Update')
        auto_update_graph.set_state(True)

        self.file_widget = RamenFileWidget(self)
        self.file_widget.save_widget.save.connect(self._save)
        self.file_widget.save_widget.open.connect(self._open)

        layout.addSpacing(10)
        layout.addWidget(run)
        layout.addWidget(step)
        if util.in_unreal:
            layout.addWidget(clear_library)
            clear_library.clicked.connect(self._clear_library)

        layout.addSpacing(10)
        layout.addWidget(auto_update_graph)
        layout.addSpacing(10)
        layout.addWidget(self.file_widget, alignment=qt.QtCore.Qt.AlignBottom)

        self.main_layout.addLayout(layout)

        self._init_tabs()

        self.tab_widget.currentChanged.connect(self._tab_changed)

        self.tab_widget.tabCloseRequested.connect(self._tab_close)
        run.clicked.connect(self._run_graph)
        step.clicked.connect(self._step_graph)
        auto_update_graph.check_changed.connect(self._set_auto_update_graph)

        self._init_tab_context_menu()

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
        if index == 0:
            return

        if self.__tab_changed_add:

            count = self.tab_widget.count()
            if index == count - 1 and self.tab_widget.tabText(count - 1) == self.tab_plus:
                self._add_tab()
                # self._create_folder(name, (count-1))
        else:
            self.__tab_changed_add = True

        name = self.tab_widget.tabText(index)

        directory = util_file.join_path(self.directory, name)
        self.file_widget.set_directory(directory)

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
            eval.run_ui(widget.main_view.base)

    def _step_graph(self):

        index = self.tab_widget.currentIndex()

        util.show('Step Graph %s' % (index + 1))

        widget = self.tab_widget.widget(index)

        if widget.directory:
            eval.step_ui(widget.main_view.base)

    def _clear_library(self):

        if util.in_unreal:
            from ...unreal_lib import graph
            graph.clear_library()

    def _set_auto_update_graph(self, state):

        index = self.tab_widget.currentIndex()

        widget = self.tab_widget.widget(index)

        widget.set_auto_update(state)

    def _save(self, comment=None):
        count = self.tab_widget.count()

        for inc in range(0, count):
            widget = self.tab_widget.widget(inc)
            if hasattr(widget, 'main_view'):
                name = self.tab_widget.tabText(inc)
                self._create_folder(name, inc)

                if comment is None:
                    comment = qt_ui.get_comment(self)

                if comment is None:
                    return

                if comment == 'Auto Save':
                    result = widget.main_view.base.save(comment, force=False)
                else:
                    result = widget.main_view.base.save(comment, force=True)

    def _open(self):
        count = self.tab_widget.count()

        for inc in range(0, count):
            widget = self.tab_widget.widget(inc)
            if hasattr(widget, 'main_view'):
                widget.main_view.base.open()

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

        self.file_widget.directory = directory
        self.directory = directory

    def _sync_tabs_to_folders(self):
        folders = util_file.get_folders(self.directory)

        if not folders:
            node_widget = self.tab_widget.widget(0)

            if not self._tab_exists('graph1'):
                node_widget = self._add_tab('graph1')

            if hasattr(node_widget, 'set_directory'):
                full_path = util_file.join_path(self.directory, 'graph1')
                node_widget.set_directory(full_path)
                node_widget.directory = full_path
            return
        folders.sort()

        for folder in folders:

            node_widget = self._add_tab(folder)

            count = self.tab_widget.count()

            for inc in range(0, count):
                title = self.tab_widget.tabText(inc)
                if title == folder:
                    node_widget = self.tab_widget.widget(inc)
                    break

            if hasattr(node_widget, 'set_directory'):
                full_path = util_file.join_path(self.directory, folder)
                node_widget.set_directory(full_path)

    def _init_tab_context_menu(self):
        """Enable custom context menu on the tab bar."""
        tab_bar = self.tab_widget.tabBar()
        tab_bar.setContextMenuPolicy(qt.QtCore.Qt.CustomContextMenu)
        tab_bar.customContextMenuRequested.connect(self._on_tab_context_menu)

    def _on_tab_context_menu(self, pos):
        """Show context menu for the tab at position `pos` (tab-bar coordinates)."""
        tab_bar = self.tab_widget.tabBar()
        index = tab_bar.tabAt(pos)
        count = self.tab_widget.count()

        # ignore invalid or the 'plus' tab (assumed last)
        if index < 0 or index >= count - 1:
            return

        menu = qt.QMenu(self)

        close_action = None
        if index > 0:
            close_action = menu.addAction('Close Tab')
        # close_others_action = menu.addAction('Close Other Tabs')
        rename_action = menu.addAction('Rename Tab')
        duplicate_action = menu.addAction('Duplicate Tab')
        save_action = menu.addAction('Save Tab')

        action = menu.exec_(tab_bar.mapToGlobal(pos))
        if action is None:
            return

        if action == close_action:
            self._tab_close(index)

        # elif action == close_others_action:

        #    to_close = [i for i in range(0, count - 1) if i != index]

        #    for i in sorted(to_close, reverse=True):
        #        if i == 0:
        #            continue
        #        self._tab_close(i)

        elif action == rename_action:
            self._rename_tab(index)

        elif action == duplicate_action:
            self._duplicate_tab(index)

        elif action == save_action:
            self._save_tab(index)

    def _duplicate_tab(self, index):
        count = self.tab_widget.count()
        # reject invalid, first template tab (0) or the plus tab (last)
        if index < 0 or index >= count - 1:
            return

        src_widget = self.tab_widget.widget(index)
        src_dir = getattr(src_widget, 'directory', None)

        # choose a unique tab/folder name
        base_name = self._get_next_tab_name()
        new_name = base_name
        new_dir = util_file.join_path(self.directory, new_name)

        suffix = 1
        while util_file.exists(new_dir):
            new_name = "%s_%d" % (base_name, suffix)
            new_dir = util_file.join_path(self.directory, new_name)
            suffix += 1

        # create the new widget and insert before the plus tab
        insert_index = count - 1
        new_widget = ui_nodes.NodeDirectoryWindow()
        self.tab_widget.insertTab(insert_index, new_widget, new_name)
        self.tab_widget.setCurrentIndex(insert_index)

        # copy source folder if available, otherwise create empty folder
        try:
            if src_dir and util_file.exists(src_dir):
                shutil.copytree(src_dir, new_dir)
            else:
                util_file.create_dir(new_dir)
        except Exception as exc:
            util.warning('Failed to copy folder for duplication; created empty folder instead')
            if not util_file.exists(new_dir):
                util_file.create_dir(new_dir)

        # set directory on the new widget
        if hasattr(new_widget, 'set_directory'):
            new_widget.set_directory(new_dir)
        new_widget.directory = new_dir

    def _save_tab(self, index):
        widget = self.tab_widget.widget(index)
        if widget and hasattr(widget, 'main_view'):
            # prompt for comment or do auto-save
            comment = qt_ui.get_comment(self)
            if comment is None:
                return
            if comment == 'Auto Save':
                widget.main_view.base.save(comment, force=False)
            else:
                widget.main_view.base.save(comment, force=True)

    def _rename_tab(self, index):
        old_name = self.tab_widget.tabText(index)
        text, ok = qt.QInputDialog.getText(self, 'Rename Tab', 'Name:', qt.QLineEdit.Normal, old_name)
        if ok and text:
            # ensure no duplicate tab names
            if self._tab_exists(text):
                util.warning('Tab name already exists')
            else:
                self.tab_widget.setTabText(index, text)
                # update folder mapping if directory exists
                widget = self.tab_widget.widget(index)
                if hasattr(widget, 'directory') and widget.directory:
                    # new_dir = util_file.join_path(self.directory, text)
                    new_dir = util_file.rename(widget.directory, text)
                    util_file.create_dir(new_dir)
                    widget.set_directory(new_dir)
                    widget.directory = new_dir

    def save(self, comment='Auto Save'):

        self._save(comment)

    def set_directory(self, directory=None):

        self._set_directory(directory)

        self._close_tabs()

        self._sync_tabs_to_folders()

        if self.file_widget.tab_widget.currentIndex() == 1:
            self.file_widget.update_history()


class RamenFileWidget(qt_ui.FileManagerWidget):

    def __init__(self, ramen_widget, parent=None):

        self.ramen_widget = ramen_widget

        super(RamenFileWidget, self).__init__(parent)

    def _define_main_tab_name(self):
        return 'JSON'

    def _define_history_widget(self):
        widget = RamenHistoryFileWidget()
        widget.ramen_widget = self.ramen_widget

        return widget


class RamenHistoryFileWidget(qt_ui.HistoryFileWidget):

    def _open_version(self):

        if not self.ramen_widget:
            return

        items = self.version_list.selectedItems()

        item = None
        if items:
            item = items[0]

        if not item:
            util.warning('No version selected')
            return

        version = int(item.text(0))

        version_tool = util_file.VersionFile(self.directory)
        version_file = version_tool.get_version_path(version)

        current_tab = self.ramen_widget.tab_widget.currentWidget()

        current_tab.main_view_class.open(version_file)


class TabCloseButton(qt.QPushButton):

    def __init__(self, text='X', parent=None):
        super(TabCloseButton, self).__init__(text, parent)
