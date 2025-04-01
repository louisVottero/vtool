# Copyright (C) 2024 Louis Vottero louis.vot@gmail.com    All rights reserved.

from __future__ import absolute_import

import subprocess
import re
import threading
import os

from .. import qt_ui, qt
from .. import util_file
from .. import util

from . import ui_data
from . import process

in_maya = False

if util.is_in_maya():
    from ..maya_lib import core

    in_maya = True


class CodeProcessWidget(qt_ui.DirectoryWidget):
    """
    The main widget for code editing.
    """

    code_text_size_changed = qt.create_signal(object)

    def __init__(self):

        self.settings = None
        self.code_directory = None
        self._process_inst = None

        super(CodeProcessWidget, self).__init__()

        self.sizes = self.splitter.sizes()

    def resizeEvent(self, event):
        if self.restrain_move:
            if not self.skip_move:
                self._close_splitter()

        return super(CodeProcessWidget, self).resizeEvent(event)

    def _build_widgets(self):

        self.splitter = qt.QSplitter()
        self.main_layout.addWidget(self.splitter)

        self.script_widget = ScriptWidget()
        self.code_widget = CodeWidget()

        self.script_tree_widget = CodeScriptTree()
        script_tabs = qt.QTabWidget()

        buffer_widget = qt_ui.BasicWidget()
        buffer_widget.main_layout.addSpacing(util.scale_dpi(5))
        buffer_widget.main_layout.addWidget(script_tabs)

        # script_tabs.setTabPosition(qt.QTabWidget.South)

        script_tabs.addTab(self.script_widget, 'Manifest')
        script_tabs.addTab(self.script_tree_widget, 'Scripts')

        self.code_widget.collapse.connect(self._close_splitter)
        self.script_widget.script_open.connect(self._code_change)
        self.script_widget.script_open_external.connect(self._open_external)
        self.script_widget.script_focus.connect(self._script_focus)
        self.script_widget.script_rename.connect(self._script_rename)
        self.script_widget.script_remove.connect(self._script_remove)
        self.script_widget.script_duplicate.connect(self._script_duplicate)
        self.script_widget.script_added.connect(self._script_added)
        self.code_text_size_changed.connect(self.script_widget.script_text_size_change)
        self.script_widget.script_text_size_change.connect(self._code_size_changed)

        self.script_tree_widget.script_open.connect(self._code_change)
        self.script_tree_widget.script_open_external.connect(self._open_external)

        self.splitter.addWidget(buffer_widget)
        self.splitter.addWidget(self.code_widget)

        self.restrain_move = True
        self.skip_move = False

        width = self.splitter.width()
        self.splitter.moveSplitter(width, 1)

        self.splitter.splitterMoved.connect(self._splitter_moved)

        self.settings = None

    def _code_size_changed(self, value):

        self.code_text_size_changed.connect(self.code_widget.code_edit.code_text_size_changed)

    def _splitter_moved(self, pos, index):

        if self.restrain_move:
            if not self.skip_move:
                self.skip_move = True
                width = self.splitter.width()
                self.splitter.moveSplitter(width, 1)
                return

            if self.skip_move:
                self.skip_move = False
                return

        self.sizes = self.splitter.sizes()

    def _define_main_layout(self):
        return qt.QVBoxLayout()

    def _close_splitter(self):

        if not self.code_widget.code_edit.has_tabs():
            self.restrain_move = True
            width = self.splitter.width()
            self.splitter.moveSplitter(width, 1)

            self.code_widget.set_code_path(None)

    def _script_focus(self, code_path):

        if code_path:
            name = code_path + '.py'

            self.code_widget.code_edit.goto_tab(name)
            self.code_widget.code_edit.goto_floating_tab(name)

    def _code_change(self, code, open_in_window=False, open_in_external=False):

        if not code:
            self._close_splitter()
            return

        if not open_in_window and not open_in_external:
            if self.restrain_move == True:
                self.restrain_move = False

            self.splitter.setSizes([util.scale_dpi(20), util.scale_dpi(500)])

        process_tool = process.Process()
        process_tool.set_directory(self.directory)

        if code.startswith('/'):
            code_name = code[1:]
        else:
            code_name = util_file.remove_extension(code)

        code_file = process_tool.get_code_file(code_name)

        if not open_in_external:
            self.code_widget.set_code_path(code_file, open_in_window, name=code)
        if open_in_external:
            self._open_external(code)

        if not open_in_window and not open_in_external:
            if self.sizes[1] != 0:
                self.splitter.setSizes(self.sizes)

    def _open_external(self, code):

        if not code:
            return

        process_tool = process.Process()
        process_tool.set_directory(self.directory)
        code_file = process_tool.get_code_file(code)

        external_editor = self.settings.get('external_editor')
        if not util.is_linux():
            external_editor = util_file.fix_slashes(external_editor)

        if external_editor:
            p = subprocess.Popen([external_editor, code_file])

        if not external_editor:
            util_file.open_browser(code_file)

    def _script_rename(self, old_name, new_name):

        process_data = process.Process()
        process_data.set_directory(self.directory)

        code_folder = process_data.get_code_path()

        old_path = util_file.join_path(code_folder, old_name)
        old_path = util_file.join_path(old_path, '%s.py' % util_file.get_basename(old_name))
        new_path = util_file.join_path(code_folder, new_name)
        new_path = util_file.join_path(new_path, '%s.py' % util_file.get_basename(new_name))

        new_file_name = new_name + '.py'
        old_file_name = old_name + '.py'

        self.code_widget.code_edit.rename_tab(old_path, new_path, old_file_name, new_file_name)

    def _script_remove(self, filepath):

        process_instance = process.Process()
        process_instance.set_directory(self.directory)
        code_name = process_instance.get_code_name_from_path(filepath)

        code_name = code_name + '.py'

        self.code_widget.code_edit.close_tab(code_name)

        if not self.code_widget.code_edit.has_tabs():
            self._close_splitter()

    def _script_duplicate(self):
        pass

    def _script_added(self, item):

        if self.code_widget.code_edit.has_tabs():
            code_folder = self.script_widget._get_current_code(item)
            self._code_change(code_folder, open_in_window=False, open_in_external=False)

    def set_directory(self, directory, sync_code=False):

        super(CodeProcessWidget, self).set_directory(directory)

        self.script_widget.set_directory(directory, sync_code)

        process_path = os.environ.get('VETALA_CURRENT_PROCESS')

        if process_path and directory:
            process_inst = process.Process()
            process_inst.set_directory(process_path)
            self._process_inst = process_inst
            self.code_widget.set_process(process_inst)

            self.script_widget.set_process_inst(self._process_inst)

            code_path = self._process_inst.get_code_path()
            self.script_tree_widget.set_directory(code_path)

        self._close_splitter()

    def set_code_directory(self, directory):
        self.code_directory = directory

    def reset_process_script_state(self):
        self.script_widget.reset_process_script_state()

    def set_process_script_state(self, directory, state):
        self.script_widget.set_process_script_state(directory, state)

    def set_process_script_log(self, directory, log):
        self.script_widget.set_process_script_log(directory, log)

    def refresh_manifest(self):
        self.script_widget.code_manifest_tree.refresh()

    def set_external_code_library(self, code_directory):
        self.script_widget.set_external_code_library(code_directory)

    def set_settings(self, settings):

        self.settings = settings

    def save_code(self):

        self.code_widget.code_edit.save_tabs()

    def close_widgets(self, close_windows=False):

        self.script_widget.code_manifest_tree.clearSelection()

        self.code_widget.code_edit.close_tabs()

        self.set_directory(None, sync_code=False)

        if close_windows:
            self.code_widget.code_edit.close_windows()

        self.script_widget.code_manifest_tree.break_index = None
        self.script_widget.code_manifest_tree.break_item = None

        self.script_widget.code_manifest_tree.start_index = None
        self.script_widget.code_manifest_tree.start_item = None


class CodeWidget(qt_ui.BasicWidget):
    collapse = qt_ui.create_signal()

    def __init__(self, parent=None):

        self._process_inst = None

        super(CodeWidget, self).__init__(parent)

        self.directory = None
        self._current_code_edit = None
        self._current_has_data = False

    def _build_widgets(self):

        self.code_edit = qt_ui.CodeEditTabs()

        completer = CodeCompleter
        completer.process_inst = self._process_inst
        self.completer = completer

        self.code_edit.set_completer(completer)
        self.code_edit.hide()

        self.code_edit.tabChanged.connect(self._tab_changed)

        self.code_edit.no_tabs.connect(self._collapse)

        self.save_file = ui_data.ScriptFileWidget()
        self.save_button = qt_ui.BasicButton('Save')

        self.code_edit.save.connect(self._code_saved)
        self.code_edit.multi_save.connect(self._multi_save)

        self.main_layout.addWidget(self.code_edit, stretch=1)
        self.main_layout.addWidget(self.save_file, stretch=0)
        self.main_layout.addWidget(self.save_button, stretch=0, alignment=qt.QtCore.Qt.AlignCenter)

        self.alt_layout = qt.QVBoxLayout()

        self.save_file.hide()
        self.save_button.hide()

        self.save_button.clicked.connect(self._code_saved)

    def _tab_changed(self, widget):
        self._current_code_edit = widget
        if not widget:
            return

        if widget.filepath:
            filepath = util_file.get_dirname(widget.filepath)

            if util_file.is_dir(filepath):

                data_instance = self.save_file.set_directory(filepath)
                self.save_file.set_text_widget(widget.text_edit)

                if data_instance:
                    self.save_button.hide()
                    self.save_file.show()
                    self._current_has_data = True
                else:
                    self.save_button.show()
                    self.save_file.hide()
                    self._current_has_data = False

            if not util_file.is_dir(filepath):
                self.save_file.hide()

    def _collapse(self):

        self.collapse.emit()

    def _load_file_text(self, path, open_in_window):

        process_data = process.Process()
        process_data.set_directory(path)
        name = process_data.get_code_name_from_path(path)

        if name:
            name = name + '.py'

        else:
            name = util_file.get_basename(path)

        self.completer.name = name

        if not open_in_window:
            tab = self.code_edit.add_tab(path, name)

        if open_in_window:
            floating_tab = self.code_edit.add_floating_tab(path, name)

    def _code_saved(self, code_edit_widget):
        if not self._current_has_data and self._current_code_edit:
            self._current_code_edit.save()
            return

        filepath = util_file.get_dirname(code_edit_widget.filepath)

        self.save_file.set_directory(filepath)
        self.save_file.set_text_widget(code_edit_widget)
        self.save_file.save_widget._save(parent=code_edit_widget)

    def _multi_save(self, widgets, note=None):

        widgets = util.convert_to_sequence(widgets)

        if not widgets:
            return

        comment = 'auto save'

        for widget in widgets:
            self.save_file.set_text_widget(widget)

            folder_path = util_file.get_dirname(widget.filepath)

            util.show('Auto save %s' % folder_path)

            self.save_file.set_directory(folder_path)
            self.save_file.save_widget._save(comment)

    def set_code_path(self, path, open_in_window=False, name=None, load_file=True):

        if not path:
            self.save_file.hide()
            self.code_edit.hide()
            return

        folder_path = util_file.get_dirname(path)

        self.directory = folder_path

        self.save_file.set_directory(folder_path)

        if path:
            self.save_file.show()
            self.code_edit.show()

        if load_file:
            self._load_file_text(path, open_in_window)

    def set_process(self, process_inst):
        self._process_inst = process_inst
        self.code_edit.set_process(self._process_inst)
        self.completer.process_inst = self._process_inst


class CodeCompleter(qt_ui.PythonCompleter):

    def __init__(self):
        super(CodeCompleter, self).__init__()
        self._put_list = None

    def keyPressEvent(self):
        return True

    def _insert_completion(self, completion_string):

        super(CodeCompleter, self)._insert_completion(completion_string)

        # this stops maya from entering edit mode in the outliner, if something is selected
        if util.is_in_maya():
            import maya.cmds as cmds

            cmds.setFocus('modelPanel1')

    def _format_live_function(self, function_instance):
        """
        This was being used to get the functions of an instance for code completion.
        It was being used to get functions from Process class but has been replaced with 
        util_file.get_ast_class_sub_functions
        
        could still be useful in the future.
        """

        function_name = None

        if hasattr(function_instance, 'im_func'):
            args = function_instance.im_func.func_code.co_varnames
            count = function_instance.im_func.func_code.co_argcount

            args_name = ''

            if count:

                if args:
                    args = args[:count]
                    if args[0] == 'self':
                        args = args[1:]

                    args_name = ','.join(args)

            function_name = '%s(%s)' % (function_instance.im_func.func_name, args_name)

        return function_name

    def custom_clear_cache(self, text):

        if text.find('put') == -1:
            self._put_list = []

    def custom_import_load(self, assign_map, module_name, text):

        text = str(text)

        if module_name == 'put':
            found = {}
            if hasattr(self, 'name') and hasattr(self, 'process_inst'):

                check_name = self.name + '/' + util_file.get_basename(self.name)

                scripts = self.process_inst.get_manifest_scripts(basename=False, fast_with_less_checks=True)

                threads = []
                for script in scripts:
                    if script[:-3].endswith(check_name):
                        break
                    thread = threading.Thread(target=get_puts_in_file, args=(script, found))
                    threads.append(thread)
                    thread.start()

                for thread in threads:
                    thread.join()

                put_value = get_put(text)

                if put_value:
                    for value in put_value:
                        found[value] = None

            keys = list(found.keys())
            keys.sort()

            return keys

        if module_name == 'process':
            if assign_map:
                if module_name in assign_map:
                    return []

            process_file = process.__file__

            if process_file.endswith('.pyc'):
                process_file = process_file[:-4] + '.py'

            functions, _ = util_file.get_ast_class_sub_functions(process_file, 'Process')

            return functions

        if module_name == 'cmds' or module_name == 'mc':

            if assign_map:
                if module_name in assign_map:
                    return []

            if util.is_in_maya():
                import maya.cmds as cmds

                functions = dir(cmds)

                return functions

        if module_name == 'pm' or module_name == 'pymel':
            if assign_map:
                if module_name in assign_map:
                    return []
            if util.is_in_maya():
                import pymel.all as pymel

                functions = dir(pymel)
                return functions


def get_put(text):
    puts = []

    find = re.findall('\s*(put.)([a-zA-Z0-9_]*)(?=.*[=])', text)

    if find:
        for f in find:
            puts.append(f[1])

    return puts


def get_puts_in_file(filepath, accum_dict=None):
    if accum_dict is None:
        accum_dict = {}
    check_text = util_file.get_file_text(filepath)

    put_value = get_put(check_text)
    if put_value:
        for value in put_value:
            accum_dict[value] = None

    return accum_dict


class ScriptWidget(qt_ui.DirectoryWidget):
    script_open = qt_ui.create_signal(object, object, object)
    script_open_external = qt_ui.create_signal(object)
    script_focus = qt_ui.create_signal(object)
    script_rename = qt_ui.create_signal(object, object)
    script_remove = qt_ui.create_signal(object)
    script_duplicate = qt_ui.create_signal()
    script_text_size_change = qt.create_signal(object)
    script_added = qt_ui.create_signal(object)

    def __init__(self):

        self._process_inst = None

        super(ScriptWidget, self).__init__()

        self.external_code_library = None

    def _define_main_layout(self):
        return qt.QVBoxLayout()

    def _build_widgets(self):

        self.code_manifest_tree = CodeManifestTree()

        buttons_layout = qt.QHBoxLayout()

        self.code_manifest_tree.item_renamed.connect(self._rename)
        self.code_manifest_tree.script_open.connect(self._script_open)
        self.code_manifest_tree.script_open_external.connect(self._script_open_external)
        self.code_manifest_tree.script_focus.connect(self._script_focus)
        self.code_manifest_tree.item_removed.connect(self._remove_code)
        self.code_manifest_tree.item_duplicated.connect(self._duplicate)
        self.code_manifest_tree.item_added.connect(self._item_added)

        self.edit_mode_button = qt.QPushButton('Drag and Drop')
        self.edit_mode_button.setCheckable(True)
        self.edit_mode_button.setMaximumHeight(util.scale_dpi(20))
        self.edit_mode_button.setMaximumWidth(util.scale_dpi(100))
        self.edit_mode_button.toggled.connect(self._edit_click)

        btm_layout = qt.QHBoxLayout()
        btm_layout.addWidget(self.edit_mode_button, alignment=qt.QtCore.Qt.AlignRight)

        self.main_layout.addWidget(self.code_manifest_tree)
        self.main_layout.addLayout(btm_layout)

        self.main_layout.addLayout(buttons_layout)

    def _edit_click(self, bool_value):

        self.code_manifest_tree.setDragEnabled(bool_value)
        self.code_manifest_tree.setAcceptDrops(bool_value)
        self.code_manifest_tree.setDropIndicatorShown(bool_value)

    def _accept_changes(self):
        self.code_manifest_tree.update_manifest_file()

    def _script_open(self, item, open_in_window, open_external=False):

        if self.code_manifest_tree.handle_selection_change:
            code_folder = self._get_current_code(item)
            self.script_open.emit(code_folder, open_in_window, open_external)

    def _script_open_external(self):

        if self.code_manifest_tree.handle_selection_change:
            code_folder = self._get_current_code()
            self.script_open_external.emit(code_folder)

    def _script_focus(self):

        if self.code_manifest_tree.handle_selection_change:
            code_folder = self._get_current_code()
            self.script_focus.emit(code_folder)

    def _get_current_code(self, item=None):

        if not item:
            item = self.code_manifest_tree.selectedItems()
            if item:
                item = item[0]

        if not item:
            return

        name = util_file.get_basename_no_extension(item.get_text())

        path = self.code_manifest_tree._get_item_path(item)

        if path:
            name = util_file.join_path(path, name)

        return name

    def _run_code(self):

        self.code_manifest_tree.run_current_item(self.external_code_library)

    def _create_code(self):

        process_tool = process.Process()
        process_tool.set_directory(self.directory)

        code_path = process_tool.create_code('code', 'script.python', inc_name=True)

        name = util_file.get_basename(code_path)

        item = self.code_manifest_tree._add_item(name, False)

        self.code_manifest_tree.scrollToItem(item)

    def _create_import_code(self):

        process_tool = process.Process()
        process_tool.set_directory(self.directory)

        folders = process_tool.get_data_folders()

        picked = qt_ui.get_pick(folders, 'Pick the data to import.', self)

        process_tool.create_code('import_%s' % picked, import_data=picked)
        self.code_manifest_tree._add_item('import_%s.py' % picked, False)

    def _remove_code(self, filepath):

        self.script_remove.emit(filepath)

    def _rename(self, old_name, new_name):

        self.script_rename.emit(old_name, new_name)

    def _duplicate(self):

        self.script_duplicate.emit()

    def _item_added(self, item):
        self.script_added.emit(item)

    def set_directory(self, directory, sync_code=False):

        super(ScriptWidget, self).set_directory(directory)

        if not sync_code:
            if self.directory == self.last_directory:
                return

        process_tool = process.Process()
        process_tool.set_directory(directory)

        self.code_manifest_tree.process = process_tool
        self.code_manifest_tree.set_directory(directory)

    def set_process_inst(self, process_inst):

        self._process_inst = process_inst

    def reset_process_script_state(self):
        self.code_manifest_tree.reset_process_script_state()

    def set_process_script_state(self, directory, state):
        self.code_manifest_tree.set_process_script_state(directory, state)

    def set_process_script_log(self, directory, log):
        self.code_manifest_tree.set_process_script_log(directory, log)

    def set_external_code_library(self, code_directory):
        self.external_code_library = code_directory


class CodeManifestTree(qt_ui.FileTreeWidget):
    item_renamed = qt_ui.create_signal(object, object)
    script_open = qt_ui.create_signal(object, object, object)
    script_open_external = qt_ui.create_signal()
    script_focus = qt_ui.create_signal()
    item_removed = qt_ui.create_signal(object)
    item_duplicated = qt_ui.create_signal()
    item_added = qt_ui.create_signal(object)

    def __init__(self):

        super(CodeManifestTree, self).__init__()

        self.drag_parent = None
        self.process = None

        self.title_text_index = 0

        self.setSortingEnabled(False)

        self.setAlternatingRowColors(True)
        if util.in_houdini:
            self.setAlternatingRowColors(False)

        self.edit_state = False

        self.setSelectionMode(qt.QAbstractItemView.ExtendedSelection)

        self.setDragDropMode(qt.QAbstractItemView.InternalMove)
        self.setDragEnabled(False)
        self.setAcceptDrops(False)
        self.setDropIndicatorShown(False)
        self.setAutoScroll(True)

        self.setDefaultDropAction(qt.QtCore.Qt.MoveAction)
        self.invisibleRootItem().setFlags(qt.QtCore.Qt.ItemIsDropEnabled)

        self.dragged_item = None
        self.handle_selection_change = True

        self.setContextMenuPolicy(qt.QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._item_menu)

        self.future_rename = False

        self.new_actions = []
        self.edit_actions = []

        self._create_context_menu()

        header = self.header()

        self.expand_collapse = qt.QPushButton('Collapse')
        self.checkbox = qt.QCheckBox(header)
        self.checkbox.stateChanged.connect(self._set_all_checked)

        self.update_checkbox = True

        self.hierarchy = True
        # new
        self.dragged_item = None
        self.shift_activate = False

        self.allow_manifest_update = True

        self.break_index = None
        self.break_item = None

        self.start_index = None
        self.start_item = None

        if util.is_in_maya():
            directory = util_file.get_vetala_directory()
            icon_on = util_file.join_path(directory, 'icons/box_on.png')
            icon_off = util_file.join_path(directory, 'icons/box_off.png')

            icon_folder = util_file.join_path(directory, 'icons/folder.png')
            icon_folder_open = util_file.join_path(directory, 'icons/folder_open.png')

            lines = 'QTreeWidget::indicator:unchecked {image: url(%s);}' % icon_off
            lines += ' QTreeWidget::indicator:checked {image: url(%s);}' % icon_on

            self.setStyleSheet(lines)

        self.setWhatsThis('Manifest List\n'
                          '\n'
                          'This list helps create a recipe for building your rig.\n'
                          'Here all the scripts you create to build the rig can be organized and run.\n'
                          'Turn on edit mode on the bottom right of this widget to access drag and drop\n'
                          'Double click on a script to open and edit it.\n'
                          '\n'
                          'Right Click menu\n\n'
                          'Hitting the Process button at the bottom of Vetala will run the whole recipe.\n'
                          'To run individual scripts or a group of scripts use the right click menu\n'
                          'The right click menu can also set start and end points.\n')

    def resizeEvent(self, event=None):
        super(CodeManifestTree, self).resizeEvent(event)

        self.checkbox.setGeometry(qt.QtCore.QRect(3, 2, 16, 17))

        return True

    def mouseDoubleClickEvent(self, event):

        item = None

        items = self.selectedItems()
        if items:
            item = items[0]

        if not item:
            return

        settings_file = os.environ.get('VETALA_SETTINGS')

        settings = util_file.SettingsFile()
        settings.set_directory(settings_file)

        double_click_option = settings.get('manifest_double_click')

        if double_click_option:

            if double_click_option == 'open tab':
                self.script_open.emit(item, False, False)
            if double_click_option == 'open new':
                self.script_open.emit(item, True, False)
            if double_click_option == 'open external':
                self.script_open.emit(item, False, True)

            return True

        self.script_open.emit(item, False, False)

        return True

    def mousePressEvent(self, event):

        self.handle_selection_change = True

        item = self.itemAt(event.pos())

        parent = self.invisibleRootItem()
        if item:
            if item.parent():
                parent = item.parent()
        self.drag_parent = parent

        self.dragged_item = item

        super(CodeManifestTree, self).mousePressEvent(event)
        self.script_focus.emit()

        return True

    def keyPressEvent(self, event):

        if event.key() == qt.QtCore.Qt.Key_Shift:
            self.shift_activate = True

        return True

    def keyReleaseEvent(self, event):
        if event.key() == qt.QtCore.Qt.Key_Shift:
            self.shift_activate = False

        if event.key() == qt.QtCore.Qt.Key_R:
            self.run_current_group()

        if event.key() == qt.QtCore.Qt.Key_Delete:
            self.remove_current_item()

        return True

    def dropEvent(self, event):

        is_dropped = self.is_item_dropped(event, strict=True)

        if not self.hierarchy:
            is_dropped = False

        event.accept()

        if not is_dropped:
            self._insert_drop(event)

        if is_dropped:
            self._add_drop(event)

        self._update_manifest()

        return True

    def _get_item_path(self, item):
        """
        get the path to an item from the highest level down. e.g. script/script/script
        """

        parent = item.parent()
        parent_path = ''

        while parent:

            parent_name = parent.text(0)

            split_name = parent_name.split('.')
            parent_name = split_name[0]

            if parent_path:
                parent_path = util_file.join_path(parent_name, parent_path)

            if not parent_path:
                parent_path = parent_name

            parent = parent.parent()

        return parent_path

    def _get_item_path_name(self, item, keep_extension=False):
        """
        get the script name with path, e.g. script/script/script.py
        """

        name = item.text(0)

        if not keep_extension:
            name = util_file.remove_extension(name)

        path = self._get_item_path(item)
        if path:
            name = util_file.join_path(path, name)

        return name

    def _get_item_path_full_name(self, item, keep_extension=False):
        """
        get the script name with path, e.g. script/script/script.py
        """

        name = item.text(0)
        folder_name = util_file.remove_extension(name)

        if not keep_extension:
            name = folder_name

        path = self._get_item_path(item)

        if path:
            path = util_file.join_path(path, folder_name)
        if not path:
            path = folder_name
        name = util_file.join_path(path, name)

    def _get_entered_item(self, event):

        position = event.pos()
        entered_item = self.itemAt(position)

        if not entered_item:
            entered_item = self.invisibleRootItem()

        return entered_item

    def _get_item_by_name(self, name):

        items = self._get_all_items()

        for item in items:

            check_name = item.text(0)

            path = self._get_item_path(item)

            if path:
                check_name = util_file.join_path(path, check_name)

            check_name = self._get_item_path_name(item, keep_extension=True)

            if check_name == name:
                return item

    def _get_all_items(self):

        item_count = self.topLevelItemCount()
        items = []

        for inc in range(0, item_count):

            item = self.topLevelItem(inc)

            ancestors = self._get_ancestors(item)

            items.append(item)

            if ancestors:
                items += ancestors

        return items

    def _get_ancestors(self, item):

        child_count = item.childCount()

        items = []

        for inc in range(0, child_count):

            child = item.child(inc)

            children = self._get_ancestors(child)

            items.append(child)
            if children:
                items += children

        return items

    def _get_files(self, scripts=None, states=None):

        if scripts is None:
            scripts = []
        if states is None:
            states = []
        process_tool = self.process

        if not scripts:
            scripts, states = process_tool.get_manifest()

        if not scripts:
            return

        # this is slow
        code_folders = process_tool.get_code_folders()

        found_scripts = []
        found_states = []

        for inc in range(0, len(scripts)):
            # and each increment is slow

            name = util_file.remove_extension(scripts[inc])

            if name not in code_folders:
                continue

            code_path = process_tool.get_code_file(name)

            if not code_path or not util_file.exists(code_path):
                continue

            found_scripts.append(scripts[inc])
            found_states.append(states[inc])

        return [found_scripts, found_states]

    def _check_has_parent(self, item, list_of_items):
        has_parent = False

        for other_item in list_of_items:
            current_index = self.indexFromItem(item, 0)
            other_index = self.indexFromItem(other_item, 0)

            if current_index == other_index:
                continue

            current_path = self._get_item_path(item)
            other_path = self._get_item_path(other_item)

            if current_path == other_path:
                continue

            if current_path.startswith(other_path):
                has_parent = True
                break

        return has_parent

    def _insert_drop(self, event):

        entered_item = self._get_entered_item(event)
        entered_parent = entered_item.parent()

        if not entered_parent:
            entered_parent = self.invisibleRootItem()

        from_list = event.source()

        insert_inc = 0

        remove_items = []
        moved_items = []
        has_parent_dict = {}

        selected_items = from_list.selectedItems()

        for item in selected_items:
            has_parent_dict[item.text(0)] = self._check_has_parent(item, selected_items)

        for item in selected_items:

            if has_parent_dict[item.text(0)]:
                continue

            children = item.takeChildren()

            filename = item.get_text()
            state = item.get_state()
            new_item = self._create_item(filename, state)

            for child in children:
                new_item.addChild(child)
                child.set_state(-1)

            parent = item.parent()

            if not parent:
                parent = self.invisibleRootItem()

            remove_items.append([item, parent])

            insert_row = self.indexFromItem(entered_item, column=0).row()

            if self.dropIndicatorPosition == self.BelowItem:
                insert_row += 1
                insert_row = insert_row + insert_inc

            if not entered_parent:

                if insert_row == -1:
                    insert_row = self.topLevelItemCount()

                if not entered_item:
                    self.insertTopLevelItem(insert_row, new_item)
                else:
                    if entered_item.text(0) == parent.text(0):

                        entered_item.insertChild(entered_item.childCount() - 1, new_item)
                    else:
                        self.insertTopLevelItem(insert_row, new_item)

            if entered_parent:
                entered_parent.insertChild(insert_row, new_item)

            insert_inc += 1

            entered_parent_name = None
            if entered_parent:
                entered_parent_name = entered_parent.text(0)

            if entered_parent_name != parent.text(0):
                old_name = self._get_item_path_name(item)
                new_name = self._get_item_path_name(new_item)

                moved_items.append([old_name, new_name, new_item])

        for item in remove_items:
            item[1].removeChild(item[0])

        for moved_item in moved_items:
            old_name, new_name, item = moved_item
            self._move_item(old_name, new_name, item)

    def _add_drop(self, event):

        entered_item = self._get_entered_item(event)

        from_list = event.source()

        remove_items = []
        moved_items = []
        has_parent_dict = {}

        selected_items = from_list.selectedItems()

        for item in selected_items:
            has_parent_dict[item.text(0)] = self._check_has_parent(item, selected_items)

        for item in selected_items:

            if has_parent_dict[item.text(0)]:
                continue

            parent = item.parent()

            if not parent:
                parent = self.invisibleRootItem()

            remove_items.append([item, parent])

            children = item.takeChildren()

            name = item.get_text()
            state = item.get_state()

            entered_item.setExpanded(True)

            new_item = self._create_item(name, state)

            for child in children:
                child.set_state(-1)
                new_item.addChild(child)

            entered_item.addChild(new_item)
            entered_item.setExpanded(True)

            old_name = self._get_item_path_name(item)
            new_name = self._get_item_path_name(new_item)

            moved_items.append([old_name, new_name, new_item])

        for item in remove_items:
            item[1].removeChild(item[0])

        for moved_item in moved_items:
            old_name, new_name, item = moved_item

            self._move_item(old_name, new_name, item)

    def _move_item(self, old_name, new_name, item):

        after_name = self._handle_item_reparent(old_name, new_name)

        basename = util_file.get_basename(after_name)
        item.set_text(basename + '.py')

        self.item_renamed.emit(old_name, after_name)

    def _handle_item_reparent(self, old_name, new_name):

        if old_name == new_name:
            return old_name

        process_tool = process.Process()
        process_tool.set_directory(self.directory)

        new_name = process_tool.move_code(old_name, new_name)

        return new_name

    def _item_collapsed(self, item):

        if self.shift_activate:
            child_count = item.childCount()

            for inc in range(0, child_count):

                children = self._get_ancestors(item.child(inc))
                item.child(inc).setExpanded(False)

                for child in children:
                    child.setExpanded(False)

    def _item_expanded(self, item):

        if self.shift_activate:
            child_count = item.childCount()

            for inc in range(0, child_count):

                children = self._get_ancestors(item.child(inc))
                item.child(inc).setExpanded(True)

                for child in children:
                    child.setExpanded(True)

    def _set_all_checked(self, int):

        if not self.update_checkbox:
            return

        state = None
        if int == 2:
            state = qt.QtCore.Qt.Checked
        if int == 0:
            state = qt.QtCore.Qt.Unchecked

        value = qt_ui.get_permission('This will activate/deactivate all code.'
                                     ' Perhaps consider saving your manifest before continuing.\n\n\n Continue?',
                                     self, title='Warning:  Activate/Deactivate all code')

        if not value:
            self.update_checkbox = False
            if int == 0:
                self.checkbox.setCheckState(qt.QtCore.Qt.Checked)
            if int == 2:
                self.checkbox.setCheckState(qt.QtCore.Qt.Unchecked)

            self.update_checkbox = True
            return

        for iterator in qt.QTreeWidgetItemIterator(self):

            item = iterator.value()

            if item:
                item.setCheckState(0, state)

    def _create_context_menu(self):

        self.context_menu = qt_ui.BasicMenu()

        new_python = self.context_menu.addAction('New Python Code')
        new_data_import = self.context_menu.addAction('New Data Import')

        self.new_actions = [new_python, new_data_import]

        self.context_menu.addSeparator()

        self.run_action = self.context_menu.addAction('Run')
        self.run_group_action = self.context_menu.addAction('Run Group')

        self.context_menu.addSeparator()
        rename_action = self.context_menu.addAction(self.tr('Rename'))
        duplicate_action = self.context_menu.addAction('Duplicate')
        self.delete_action = self.context_menu.addAction('Delete')

        self.context_menu.addSeparator()
        log_window = self.context_menu.addAction('Show Last Log')
        new_window_action = self.context_menu.addAction('Open In New Window')
        external_window_action = self.context_menu.addAction('Open In External')
        browse_action = self.context_menu.addAction('Browse')
        refresh_action = self.context_menu.addAction('Refresh')

        self.context_menu.addSeparator()
        start_action = self.context_menu.addAction('Set Startpoint')
        self.cancel_start_action = self.context_menu.addAction('Cancel Startpoint')
        self.context_menu.addSeparator()
        break_action = self.context_menu.addAction('Set Breakpoint')
        self.cancel_break_action = self.context_menu.addAction('Cancel Breakpoint')
        self.context_menu.addSeparator()
        self.cancel_points_action = self.context_menu.addAction('Cancel Start/Breakpoint')

        self.edit_actions = [self.run_action, self.run_group_action, rename_action, duplicate_action,
                             self.delete_action]

        new_python.triggered.connect(self.create_python_code)
        new_data_import.triggered.connect(self.create_import_code)

        self.run_action.triggered.connect(self.run_current_item)
        self.run_group_action.triggered.connect(self.run_current_group)
        start_action.triggered.connect(self.set_startpoint)
        self.cancel_start_action.triggered.connect(self.cancel_startpoint)
        break_action.triggered.connect(self.set_breakpoint)
        self.cancel_break_action.triggered.connect(self.cancel_breakpoint)
        self.cancel_points_action.triggered.connect(self.cancel_points)
        rename_action.triggered.connect(self._activate_rename)
        duplicate_action.triggered.connect(self._duplicate_current_item)
        self.delete_action.triggered.connect(self.remove_current_item)

        log_window.triggered.connect(self._open_log_window)
        new_window_action.triggered.connect(self._open_in_new_window)
        external_window_action.triggered.connect(self._open_in_external)
        browse_action.triggered.connect(self._browse_to_code)
        refresh_action.triggered.connect(self._refresh_action)

    def _item_menu(self, position):

        items = self.selectedItems()

        item = None

        if items:
            item = items[0]

        if item:
            self._edit_actions_visible(True)

        if not item:
            self._edit_actions_visible(False)

        if len(items) > 1:
            self._edit_actions_visible(False)
            self.run_action.setVisible(True)
            self.delete_action.setVisible(True)

        self.context_menu.exec_(self.viewport().mapToGlobal(position))

    def _edit_actions_visible(self, bool_value):

        for action in self.edit_actions:
            action.setVisible(bool_value)

    def _refresh_action(self):
        self.refresh(sync=True)

    def _activate_rename(self, item=None):

        if not item:
            items = self.selectedItems()
            if not items:
                return

            item = items[0]

        self.old_name = str(item.get_text())

        new_name = qt_ui.get_new_name('New Name', self, self.old_name)

        if new_name == self.old_name:
            return

        if not new_name:
            return

        if new_name == 'manifest' or new_name == 'manifest.py':
            qt_ui.warning('Manifest is reserved. Name your script something else.', self)
            return

        self._rename_item(item, new_name)

    def _open_log_window(self):
        text_window = qt_ui.BasicWindow(self)

        items = self.selectedItems()

        if not items:
            qt_ui.message('No log. Please select an item', self)
            return

        item = items[0]
        log = item.log

        if not log:
            qt_ui.message('No log. Please process first', self)
            return

        text_window.setWindowTitle('%s log' % item.get_text())

        log_text = qt.QPlainTextEdit()
        log_text.setReadOnly(True)
        log_text.setPlainText(log)
        log_text.setLineWrapMode(qt.QPlainTextEdit.NoWrap)
        log_text.setMinimumHeight(300)
        log_text.setMinimumWidth(600)

        text_window.main_layout.addWidget(log_text)

        text_window.show()

    def _open_in_new_window(self):

        items = self.selectedItems()
        item = items[0]

        self.script_open.emit(item, True, False)

    def _open_in_external(self):

        self.script_open_external.emit()

    def _browse_to_code(self):

        items = self.selectedItems()

        process_tool = process.Process()
        process_tool.set_directory(self.directory)

        if items:
            item = items[0]

            code_name = self._get_item_path_name(item)
            code_path = process_tool.get_code_folder(code_name)

            util_file.open_browser(code_path)

        if not items:
            code_path = process_tool.get_code_path()
            util_file.open_browser(code_path)

    def _define_header(self):
        return ['       Manifest']

    def _name_clash(self, name):

        process_tool = process.Process()
        process_tool.set_directory(self.directory)

        folders = process_tool.get_code_folders()

        for folder in folders:

            other_name = folder

            if name == other_name:
                return True

        return False

    def _rename_item(self, item, new_name):

        new_name = str(new_name)

        test_name = util_file.remove_extension(new_name)

        if new_name and not test_name:
            new_name = '_' + new_name[1:]

        new_name = util_file.remove_extension(new_name)

        path = self._get_item_path(item)

        if path:
            new_name = util_file.join_path(path, new_name)

        old_name = self.old_name
        old_name = util_file.remove_extension(old_name)

        if path:
            old_name = util_file.join_path(path, old_name)

        inc = util.get_last_number(new_name)

        if inc is None:
            inc = 0

        while self._name_clash(new_name):

            inc += 1

            if not util.get_trailing_number(new_name):
                new_name = new_name + '1'
                continue

            new_name = util.replace_last_number(new_name, str(inc))

            if inc >= 1000:
                return

        if old_name == new_name:
            return

        process_tool = process.Process()
        process_tool.set_directory(self.directory)

        file_name = process_tool.rename_code(old_name, new_name)

        new_file_name = util_file.remove_extension(file_name)

        filepath = process_tool.get_code_file(new_file_name)

        basename = util_file.get_basename(filepath)

        item.set_text(basename)

        self.item_renamed.emit(old_name, new_name)

        self._update_manifest()

    def _define_item(self):
        return ManifestItem()

    def _setup_item(self, item, state):

        if not state:
            item.setCheckState(0, qt.QtCore.Qt.Unchecked)
        if state:
            item.setCheckState(0, qt.QtCore.Qt.Checked)

        if not self.hierarchy:
            # dont remove this comment.  You can make an item not be drop enabled by giving it every flag except drop enabled.
            item.setFlags(qt.QtCore.Qt.ItemIsSelectable |
                          qt.QtCore.Qt.ItemIsEditable |
                          qt.QtCore.Qt.ItemIsEnabled |
                          qt.QtCore.Qt.ItemIsDragEnabled |
                          qt.QtCore.Qt.ItemIsUserCheckable)

        if self.hierarchy:
            # this allows for dropping
            item.setFlags(qt.QtCore.Qt.ItemIsSelectable |
                          qt.QtCore.Qt.ItemIsEnabled |
                          qt.QtCore.Qt.ItemIsDragEnabled |
                          qt.QtCore.Qt.ItemIsUserCheckable |
                          qt.QtCore.Qt.ItemIsDropEnabled)

        # setData in the item is an issue. If this isn't happening then the manifest will update every time the check state changes by the program.
        # this avoids it updating while it is being set by the program.
        if hasattr(item, 'handle_manifest'):
            item.handle_manifest = True

    def _create_item(self, filename, state=False):

        item = self._define_item()

        item.set_text(filename)

        self._setup_item(item, state)

        return item

    def _add_item(self, filename, state, parent=None, update_manifest=True, skip_emit=False):

        item = None
        if filename:
            if filename.count('/') > 0:
                basename = util_file.get_basename(filename)

                item = super(CodeManifestTree, self)._add_item(basename, parent=False)

            if filename.count('/') == 0:
                item = super(CodeManifestTree, self)._add_item(filename, parent)

        self._setup_item(item, state)

        if update_manifest:
            self._update_manifest()

        if not skip_emit:
            self.item_added.emit(item)

        return item

    def _add_items(self, files, item=None):

        scripts, states = files

        script_count = len(scripts)

        found_false = False

        order_scripts = {}
        order_of_scripts = []

        parents = {}

        for inc in range(0, script_count):
            script_full = scripts[inc]
            script_name = script_full.split('.')[0]

            slash_count = script_name.count('/')

            if slash_count not in order_scripts:
                order_scripts[slash_count] = []
                order_of_scripts.append(slash_count)

            parents[script_name] = None
            order_scripts[slash_count].append([script_name, script_full, states[inc]])

        ordered_scripts = []

        for count in order_of_scripts:
            ordered_scripts += order_scripts[count]

        built_parents = {}

        for inc in range(0, script_count):

            script_name, script_full, state = ordered_scripts[inc]

            basename = util_file.get_basename(script_full)

            item = self._add_item('...temp...', state, parent=False, update_manifest=False, skip_emit=True)

            if script_name in parents:
                built_parents[script_name] = item

            dirname = util_file.get_dirname(script_full)

            if dirname in built_parents:
                current_parent = built_parents[dirname]

                current_parent.addChild(item)

                item.set_text(basename)

            if not dirname:
                self.addTopLevelItem(item)
                item.set_text(basename)

            if not state:
                found_false = True

        self.update_checkbox = False

        if not found_false:
            self.checkbox.setChecked(True)
        if found_false:
            self.checkbox.setChecked(False)

        self.update_checkbox = True

    def _reparent_item(self, name, item, parent_item):

        current_parent = item.parent()

        if not current_parent:
            current_parent = self.invisibleRootItem()

        if current_parent and parent_item:
            old_name = self._get_item_path_name(item)
            parent_path = self._get_item_path_name(parent_item)

            new_name = util_file.join_path(parent_path, name)

            current_parent.removeChild(item)
            parent_item.addChild(item)

            old_name = util_file.remove_extension(old_name)
            new_name = util_file.remove_extension(new_name)

            self._move_item(old_name, new_name, item)

    def _get_current_manifest(self):
        scripts = []
        states = []

        items = self._get_all_items()

        for item in items:

            name = item.get_text()

            path = self._get_item_path(item)

            if path:
                name = util_file.join_path(path, name)

            state = item.checkState(0)
            if state == 0:
                state = False

            if state == 2:
                state = True

            scripts.append(name)
            states.append(state)

        return scripts, states

    def _update_manifest(self):

        if not self.allow_manifest_update:
            return

        scripts, states = self.get_current_manifest()

        process_tool = self.process
        process_tool.set_manifest(scripts, states)

    def _run_item(self, item, process_tool, run_children=False):

        self.scrollToItem(item)

        item.set_state(2)

        item.setExpanded(True)

        background = item.background(0)
        orig_background = background
        color = qt.QColor(1, 0, 0)
        background.setColor(color)
        item.setBackground(0, background)

        name = self._get_item_path_name(item)

        code_file = process_tool.get_code_file(name)

        if in_maya:
            import maya.cmds as cmds
            cmds.select(cl=True)
            core.auto_focus_view()

        util.start_temp_log()
        status = process_tool.run_script(code_file, False, return_status=True)
        if process_tool._skip_children:
            run_children = False
            process_tool._skip_children = None

        log = util.get_last_temp_log()

        item.set_log(log)

        if status == 'Success':
            item.set_state(1)

        if not status == 'Success':
            item.set_state(0)

        if log.find('Warning!') > -1:
            item.set_state(3)

        item.setBackground(0, orig_background)

        if status == 'Success':
            if run_children:
                self._run_children(item, process_tool, recursive=True)

    def _run_children(self, item, process_tool, recursive=True):
        child_count = item.childCount()

        if not child_count:
            return

        item.setExpanded(True)

        if child_count:

            for inc in range(0, child_count):
                child_item = item.child(inc)
                child_item.set_state(-1)

            for inc in range(0, child_count):
                child_item = item.child(inc)

                check_state = child_item.checkState(0)

                if check_state == qt.QtCore.Qt.Unchecked:
                    continue

                self._run_item(child_item, process_tool, run_children=recursive)

    def _duplicate_current_item(self):

        self.setFocus(qt.QtCore.Qt.ActiveWindowFocusReason)

        items = self.selectedItems()
        item = items[0]

        new_item = self._duplicate_item(item)

        self.item_duplicated.emit()

        self.scrollToItem(new_item)
        self.setCurrentItem(new_item)

        self._activate_rename(new_item)

    def _duplicate_item(self, item, parent_item=None, adjacent=True):

        current_check_state = item.checkState(0)

        name = self._get_item_path_name(item)

        process_tool = process.Process()
        process_tool.set_directory(self.directory)

        filepath = process_tool.get_code_file(name)

        if not parent_item:
            parent_item = item.parent()

        new_name = name

        if parent_item:
            parent_name = self._get_item_path_name(parent_item)

            new_name = util_file.get_basename(name)
            new_name = util_file.join_path(parent_name, new_name)

        code_path = process_tool.create_code(new_name, 'script.python', inc_name=True)

        file_lines = util_file.get_file_lines(filepath)

        util_file.write_lines(code_path, file_lines, append=False)

        name = util_file.get_basename(code_path)

        new_item = self._add_item(name, False, parent=parent_item)

        new_item.setCheckState(0, current_check_state)

        if not parent_item:
            parent_item = self.invisibleRootItem()

        if adjacent and parent_item:
            index = parent_item.indexOfChild(item)

            new_index = parent_item.indexOfChild(new_item)
            new_item = parent_item.takeChild(new_index)
            parent_item.insertChild(index + 1, new_item)

        child_count = item.childCount()

        for inc in range(0, child_count):
            child_item = item.child(inc)
            self._duplicate_item(child_item, new_item, adjacent=False)

        return new_item

    def _custom_refresh(self, scripts, states):

        files = self._get_files(scripts, states)

        if not files:
            self.clear()
            return

        self._load_files(files)

        self.refreshed.emit()

    def sync_manifest(self):

        process_tool = process.Process()
        process_tool.set_directory(self.directory)

        process_tool.sync_manifest()

    def refresh(self, sync=False, scripts_and_states=None):

        if scripts_and_states is None:
            scripts_and_states = []
        break_item_path = None
        if self.break_item:
            break_item_path = self._get_item_path_name(self.break_item, keep_extension=True)

        start_item_path = None
        if self.start_item:
            start_item_path = self._get_item_path_name(self.start_item, keep_extension=True)

        if sync:
            self.sync_manifest()

        self.allow_manifest_update = False
        if not scripts_and_states:
            super(CodeManifestTree, self).refresh()

        if scripts_and_states:
            self._custom_refresh(scripts_and_states[0], scripts_and_states[1])

        self.allow_manifest_update = True

        if self.start_item:
            item = self._get_item_by_name(start_item_path)

            if item:
                self.set_startpoint(item)

        if self.break_item:
            item = self._get_item_by_name(break_item_path)

            if item:
                self.set_breakpoint(item)

    def update_manifest_file(self):
        self._update_manifest()

    def get_current_item_file(self):

        items = self.selectedItems()

        if not items:
            return
        item = items[0]

        name = self._get_item_path_full_name(item, keep_extension=True)

        path = util_file.join_path(self.directory, name)

        return path

    def get_current_manifest(self):
        scripts = []
        states = []

        items = self._get_all_items()

        for item in items:

            name = item.get_text()

            path = self._get_item_path(item)

            if path:
                name = util_file.join_path(path, name)

            state = item.checkState(0)

            if state == qt.QtCore.Qt.Unchecked:
                state = False

            if state == qt.QtCore.Qt.Checked:
                state = True

            scripts.append(name)
            states.append(state)

        return scripts, states

    def set_directory(self, directory, refresh=True):

        self.directory = directory

        if refresh:
            self.refresh(refresh)

    def reset_process_script_state(self):

        items = self._get_all_items()

        for item in items:
            item.set_state(-1)

    def set_process_script_state(self, directory, state):

        script_name = directory

        item = self._get_item_by_name(script_name)

        if not item:
            return

        if state > -1:
            self.scrollToItem(item)

        item.set_state(state)

    def set_process_script_log(self, directory, log):
        script_name = directory

        item = self._get_item_by_name(script_name)

        if not item:
            return

        item.set_log(log)

    def is_process_script_breakpoint(self, directory):

        item = self._get_item_by_name(directory)

        model_index = self.indexFromItem(item)

        index = model_index.internalId()

        if index == self.break_index:
            return True

        return False

    def has_startpoint(self):

        if self.start_index is not None:
            return True

        return False

    def is_process_script_startpoint(self, directory):

        item = self._get_item_by_name(directory)

        model_index = self.indexFromItem(item)

        index = model_index.internalId()

        if index == self.start_index:
            return True

        return False

    def create_python_code(self):

        process_tool = process.Process()
        process_tool.set_directory(self.directory)

        items = self.selectedItems()

        code = 'code'
        parent = None

        if items:

            parent = items[0]

            path = self._get_item_path_name(parent, keep_extension=False)
            if path:
                code = path + '/' + code

        code_path = process_tool.create_code(code, 'script.python', inc_name=True)

        name = util_file.get_basename(code_path)

        item = self._add_item(name, False, parent=parent)

        item.setCheckState(0, qt.QtCore.Qt.Checked)

        self.scrollToItem(item)
        self.setCurrentItem(item)

        self._update_manifest()

        self._activate_rename()

    def create_import_code(self):

        process_tool = process.Process()
        process_tool.set_directory(self.directory)

        folders = process_tool.get_data_folders()

        picked = qt_ui.get_pick(folders, 'Pick the data to import.', self)

        if not picked:
            return

        parent_item = None
        items = self.selectedItems()
        if items:
            parent_item = items[0]

        code_path = process_tool.create_code('import_%s' % picked, 'script.python', import_data=picked, inc_name=True)

        name = util_file.get_basename(code_path)
        item = self._add_item(name, False)

        item.setCheckState(0, qt.QtCore.Qt.Checked)

        self._reparent_item('import_%s' % picked, item, parent_item)

        self.scrollToItem(item)
        self.setCurrentItem(item)

        self._update_manifest()

    def run_current_item(self, external_code_library=None, group_only=False):

        util.set_env('VETALA RUN', True)
        util.set_env('VETALA STOP', False)

        process_tool = self.process

        scripts, states = process_tool.get_manifest()

        items = self.selectedItems()

        if len(items) > 1:

            if util.is_in_maya():

                value = qt_ui.get_permission('Start a new scene?', self)
                if value:
                    core.start_new_scene()

                if value is None:
                    return

        watch = util.StopWatch()
        watch.start(feedback=False)

        for item in items:
            item.set_state(-1)

        if external_code_library:
            process_tool.set_external_code_library(external_code_library)

        inc = 0

        last_name = items[-1].text(0)

        last_path = self._get_item_path(items[-1])
        if last_path:
            last_name = util_file.join_path(last_path, last_name)

        set_end_states = False

        for inc in range(0, len(scripts)):

            if os.environ.get('VETALA RUN') == 'True':
                if os.environ.get('VETALA STOP') == 'True':
                    break

            if set_end_states:

                item = self._get_item_by_name(scripts[inc])
                if item:
                    item.set_state(-1)

            item_count = len(items)

            for item in items:

                name = item.text(0)

                path = self._get_item_path(item)

                if path:
                    name = util_file.join_path(path, name)

                if name == scripts[inc]:

                    run_children = False

                    if group_only:
                        run_children = True

                    self._run_item(item, process_tool, run_children)

                    if group_only:
                        break

                    if name == last_name:
                        set_end_states = True

        util.set_env('VETALA RUN', False)
        util.set_env('VETALA STOP', False)

        minutes, seconds = watch.stop()

        if minutes:
            util.show('Processes run in %s minutes and %s seconds.' % (minutes, seconds))
        else:
            util.show('Processes run in %s seconds.' % seconds)

    def run_current_group(self):
        self.run_current_item(group_only=True)

    def remove_current_item(self):

        items = self.selectedItems()

        delete_state = False

        if len(items) > 1:
            delete_state = qt_ui.get_permission('Delete selected codes?')

            if not delete_state:
                return

        for item in items:

            name = self._get_item_path_name(item)

            if len(items) == 1:
                delete_state = qt_ui.get_permission('Delete %s?' % name)

            process_tool = process.Process()
            process_tool.set_directory(self.directory)

            filepath = process_tool.get_code_file(name)

            if delete_state:

                index = self.indexFromItem(item)

                parent = item.parent()

                if parent:
                    parent.removeChild(item)
                if not parent:
                    self.takeTopLevelItem(index.row())

                process_tool.delete_code(name)

                self._update_manifest()

            self.item_removed.emit(filepath)

    def set_breakpoint(self, item=None):

        self.cancel_breakpoint()

        if not item:
            items = self.selectedItems()

            if not items:
                return

            item = items[0]

        self.clearSelection()

        item_index = self.indexFromItem(item)

        if item_index.internalId() == self.start_index:
            self.cancel_startpoint()

        self.break_index = item_index.internalId()
        self.break_item = item

        brush = qt.QBrush(qt.QColor(70, 0, 0))
        item.setBackground(0, brush)

    def set_startpoint(self, item=None):

        self.cancel_startpoint()

        if not item:
            items = self.selectedItems()

            if not items:
                return

            item = items[0]

        self.clearSelection()

        item_index = self.indexFromItem(item)

        if item_index.internalId() == self.break_index:
            self.cancel_breakpoint()

        self.start_index = item_index.internalId()

        self.start_item = item

        brush = qt.QBrush(qt.QColor(0, 70, 20))
        item.setBackground(0, brush)

    def cancel_breakpoint(self):

        if self.break_item:
            try:
                self.break_item.setBackground(0, qt.QBrush())
            except:
                pass

        self.break_index = None
        self.break_item = None

        self.repaint()

    def cancel_startpoint(self):

        if self.start_item:
            try:
                self.start_item.setBackground(0, qt.QBrush())
            except:
                pass

        self.start_index = None
        self.start_item = None

        self.repaint()

    def cancel_points(self):
        self.cancel_startpoint()
        self.cancel_breakpoint()

    def set_process_data(self, process_runtime_dictionary, put_class):

        self.process.runtime_values = process_runtime_dictionary
        self.process._put = put_class


class CodeScriptTree(qt_ui.FileTreeWidget):

    script_open = qt_ui.create_signal(object, object, object)
    script_open_external = qt_ui.create_signal()

    def __init__(self):
        super(CodeScriptTree, self).__init__()

        self.setColumnCount(1)
        self.setContextMenuPolicy(qt.QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._item_menu)

        self._build_action_items()

    def _define_item(self):
        return ScriptItem()

    def _item_menu(self, position):

        self.context_menu.exec_(self.viewport().mapToGlobal(position))

        pass

    def _build_action_items(self):
        self.context_menu = qt_ui.BasicMenu()

        new_python = self.context_menu.addAction('New Python File')
        new_json = self.context_menu.addAction('New JSON File')

        self.new_actions = [new_python, new_json]

        self.context_menu.addSeparator()
        rename_action = self.context_menu.addAction(self.tr('Rename'))
        duplicate_action = self.context_menu.addAction('Duplicate')
        self.delete_action = self.context_menu.addAction('Delete')

        self.context_menu.addSeparator()
        new_window_action = self.context_menu.addAction('Open In New Window')
        external_window_action = self.context_menu.addAction('Open In External')
        browse_action = self.context_menu.addAction('Browse')
        refresh_action = self.context_menu.addAction('Refresh')

        new_python.triggered.connect(self._create_python)
        new_json.triggered.connect(self._create_json)

        rename_action.triggered.connect(self._activate_rename)
        duplicate_action.triggered.connect(self._duplicate_current_item)
        self.delete_action.triggered.connect(self._delete_current_item)

        new_window_action.triggered.connect(self._open_in_new_window)
        external_window_action.triggered.connect(self._open_in_external)
        browse_action.triggered.connect(self._browse_to_code)
        refresh_action.triggered.connect(self._refresh_action)

    def _create_python(self):
        self._create_file('file.py')

    def _create_json(self):
        self._create_file('file.json')

    def _create_file(self, filename, parent=None):

        file_created = util_file.create_file(filename, self.directory, make_unique=True)

        if file_created:

            name = util_file.get_basename(file_created)

            tree_item = ScriptItem()
            tree_item.setText(0, name)

            self.addTopLevelItem(tree_item)
            tree_item.setSelected(True)

    def _activate_rename(self):
        pass

    def _duplicate_current_item(self):
        pass

    def _delete_current_item(self):
        pass

    def _open_in_new_window(self):

        items = self.selectedItems()
        item = items[0]

        self.script_open.emit(item, True, False)

    def _open_in_external(self):

        self.script_open_external.emit()

    def _refresh_action(self):
        self.refresh()

    def _browse_to_code(self):

        items = self.selectedItems()

        process_tool = process.Process()
        process_tool.set_directory(self.directory)

        if items:
            item = items[0]

            code_name = self._get_item_path_name(item)
            code_path = process_tool.get_code_folder(code_name)

            util_file.open_browser(code_path)

        if not items:
            code_path = process_tool.get_code_path()
            util_file.open_browser(code_path)

    def _get_files(self, directory=None):

        found = super(CodeScriptTree, self)._get_files(directory)
        if not found:
            return

        if '.version' in found:
            found.remove('.version')

        return found

    def mouseDoubleClickEvent(self, event):

        item = None

        items = self.selectedItems()
        if items:
            item = items[0]

        if not item:
            return

        settings_file = os.environ.get('VETALA_SETTINGS')

        settings = util_file.SettingsFile()
        settings.set_directory(settings_file)

        double_click_option = settings.get('manifest_double_click')

        name = self.get_item_path_string(item)
        name = '/' + name

        if double_click_option:

            if double_click_option == 'open tab':
                self.script_open.emit(name, False, False)
            if double_click_option == 'open new':
                self.script_open.emit(name, True, False)
            if double_click_option == 'open external':
                self.script_open.emit(name, False, True)

            return True

        self.script_open.emit(item, False, False)

        return True


class ScriptItem(qt.QTreeWidgetItem):

    def __lt__(self, other):
        column = self.treeWidget().sortColumn()
        return util.convert_text_for_sorting(self.text(column)) < util.convert_text_for_sorting(other.text(column))


class ManifestItem(qt_ui.TreeWidgetItem):

    def __init__(self):

        self.handle_manifest = False

        super(ManifestItem, self).__init__()

        height = 20

        height = util.scale_dpi(height)

        self.setSizeHint(0, qt.QtCore.QSize(10, height))

        maya_version = util.get_maya_version()

        if maya_version > 2015 or maya_version == 0:
            self.status_icon = self._circle_fill_icon(0, 0, 0)

        if maya_version < 2016 and maya_version != 0:
            self.status_icon = self._radial_fill_icon(0, 0, 0)

        self.setCheckState(0, qt.QtCore.Qt.Unchecked)

        self.run_state = -1
        self.log = ''

    def _square_fill_icon(self, r, g, b):

        alpha = 1

        if r == 0 and g == 0 and b == 0:
            alpha = 0

        pixmap = qt.QPixmap(20, 20)
        pixmap.fill(qt.QColor.fromRgbF(r, g, b, alpha))

        painter = qt.QPainter(pixmap)
        painter.fillRect(0, 0, 100, 100, qt.QColor.fromRgbF(r, g, b, alpha))
        painter.end()

        icon = qt.QIcon(pixmap)

        self.setIcon(0, icon)

    def _circle_fill_icon(self, r, g, b):
        alpha = 1

        if r == 0 and g == 0 and b == 0:
            alpha = 0

        pixmap = qt.QPixmap(20, 20)
        pixmap.fill(qt.QtCore.Qt.transparent)

        painter = qt.QPainter(pixmap)
        painter.setBrush(qt.QColor.fromRgbF(r, g, b, alpha))

        painter.setPen(qt.QtCore.Qt.NoPen)
        painter.drawEllipse(0, 0, 20, 20)

        painter.end()

        icon = qt.QIcon(pixmap)

        self.setIcon(0, icon)

    def _radial_fill_icon(self, r, g, b):

        alpha = 1

        if r == 0 and g == 0 and b == 0:
            alpha = 0

        pixmap = qt.QPixmap(20, 20)
        pixmap.fill(qt.QtCore.Qt.transparent)
        gradient = qt.QRadialGradient(10, 10, 10)
        gradient.setColorAt(0, qt.QColor.fromRgbF(r, g, b, alpha))
        gradient.setColorAt(1, qt.QColor.fromRgbF(0, 0, 0, 0))

        painter = qt.QPainter(pixmap)
        painter.fillRect(0, 0, 100, 100, gradient)
        painter.end()

        icon = qt.QIcon(pixmap)

        self.setIcon(0, icon)

    def setData(self, column, role, value):
        super(ManifestItem, self).setData(column, role, value)

        # TODO: Refactor use elif statements.
        check_state = None
        if value == 0:
            check_state = qt.QtCore.Qt.Unchecked
        if value == 2:
            check_state = qt.QtCore.Qt.Checked

        if role == qt.QtCore.Qt.CheckStateRole:

            if self.handle_manifest:
                tree = self.treeWidget()
                tree._update_manifest()

                if tree.shift_activate:

                    child_count = self.childCount()
                    for inc in range(0, child_count):

                        child = self.child(inc)

                        child.setCheckState(column, check_state)

                        children = tree._get_ancestors(child)

                        for child in children:
                            child.setCheckState(column, check_state)

    def set_state(self, state):

        maya_version = util.get_maya_version()

        if maya_version < 2016 and maya_version != 0:

            if state == 0:
                self._radial_fill_icon(1.0, 0.0, 0.0)
            if state == 1:
                self._radial_fill_icon(0.0, 1.0, 0.0)
            if state == -1:
                self._radial_fill_icon(0.6, 0.6, 0.6)
            if state == 2:
                self._radial_fill_icon(1.0, 1.0, 0.0)
            if state == 3:
                self._radial_fill_icon(.65, .7, 0.225)

        if maya_version > 2015 or maya_version == 0:

            if state == 0:
                self._circle_fill_icon(1.0, 0.0, 0.0)
            if state == 1:
                self._circle_fill_icon(0.0, 1.0, 0.0)
            if state == -1:
                self._circle_fill_icon(0, 0, 0)
            if state == 2:
                self._circle_fill_icon(1.0, 1.0, 0.0)
            if state == 3:
                self._circle_fill_icon(.65, .7, .225)

        self.run_state = state

    def get_run_state(self):
        return self.run_state

    def get_state(self):
        return self.checkState(0)

    def set_text(self, text):
        text = '   ' + text
        super(ManifestItem, self).setText(0, text)

    def get_text(self):
        text_value = super(ManifestItem, self).text(0)
        return str(text_value).strip()

    def text(self, index):

        return self.get_text()

    def setText(self, index, text):
        return self.set_text(text)

    def set_log(self, log):
        self.log = log
