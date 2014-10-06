import vtool.qt_ui
import vtool.util_file
import vtool.util

import ui_data
import process
from PyQt4.Qt import QMimeData, QDataStream, QIODevice
from vtool.qt_ui import get_pick

if vtool.qt_ui.is_pyqt():
    from PyQt4 import QtGui, QtCore, Qt, uic
if vtool.qt_ui.is_pyside():
    from PySide import QtCore, QtGui
    

class CodeProcessWidget(vtool.qt_ui.DirectoryWidget):
    
    def _build_widgets(self):
        
        self.splitter = QtGui.QSplitter()
        self.main_layout.addWidget(self.splitter)
        
        self.code_widget = CodeWidget()
        self.script_widget = ScriptWidget()
        
        self.code_widget.manifest_changed.connect(self._update_manifest)
        self.script_widget.selection_changed.connect(self._code_change)
        
        self.splitter.addWidget(self.script_widget)
        self.splitter.addWidget(self.code_widget)
        
        
        self.restrain_move = True
        self.skip_move = False
        
        width = self.splitter.width()
        self.splitter.moveSplitter(width, 1)
        
        self.splitter.splitterMoved.connect(self._splitter_moved)
                
    def _splitter_moved(self, pos, index):
        
        if self.restrain_move:
            if not self.skip_move:
                self.skip_move = True
                width = self.splitter.width()
                self.splitter.moveSplitter(width,1)
                return
                
            if self.skip_move:
                self.skip_move = False
                return
        
        
    def _define_main_layout(self):
        return QtGui.QVBoxLayout()
        
    def _code_change(self, code):
        
        if not code:
            self.code_widget.set_code_path(None)
            self.restrain_move = True
            width = self.splitter.width()
            self.splitter.moveSplitter(width,1)
            return
        
        if self.restrain_move == True:
            self.restrain_move = False
            width = self.splitter.width()
            
            section = width/2.0
            
            self.splitter.setSizes([section, section])
        
        
        if not code:
            return
            
        process_tool = process.Process()
        process_tool.set_directory(self.directory)
        
        split_code = code.split('.')
        
        path = process_tool.get_code_folder(split_code[0])

        code_file = vtool.util_file.join_path(path, code)
        
        self.code_widget.set_code_path(code_file)
        
    def _update_manifest(self):
        
        self.script_widget.code_manifest_tree.refresh()
        
    def set_directory(self, directory):
        super(CodeProcessWidget, self).set_directory(directory)
        
        self.script_widget.set_directory(directory)
        
    def set_code_directory(self, directory):
        self.code_directory = directory
        
    def reset_process_script_state(self):
        self.script_widget.reset_process_script_state()
        
    def set_process_script_state(self, directory, state):
        self.script_widget.set_process_script_state(directory, state)
        
    def refresh(self):
        self._update_manifest()
    
        
class CodeWidget(vtool.qt_ui.BasicWidget):
    
    manifest_changed = vtool.qt_ui.create_signal()
    
    def __init__(self, parent= None):
        super(CodeWidget, self).__init__(parent)
               
        self.directory = None
        
    def _build_widgets(self):
        
        self.code_edit = vtool.qt_ui.CodeTextEdit()
        self.code_edit.hide()
        
        self.code_edit.setWordWrapMode(QtGui.QTextOption.NoWrap)
        
        self.save_file = ui_data.ScriptFileWidget()
        self.save_file.set_text_widget(self.code_edit)
        
        self.code_edit.save.connect( self._code_saved )
        self.save_file.save_widget.file_changed.connect( self._code_widget_saved)
        
        self.main_layout.addWidget(self.code_edit, stretch = 1)
        self.main_layout.addWidget(self.save_file, stretch = 0)
        
        
        self.alt_layout = QtGui.QVBoxLayout()
        
        self.save_file.hide()
        
    def _load_file_text(self, path):
        
        self.code_edit.set_file(path)
                
    def _is_manifest(self):
        
        basename = vtool.util_file.get_basename(self.directory)
        
        if basename == 'manifest.data':
            return True
                  
    def _code_saved(self):
        
        self.save_file.save_widget._save()
        
        if self._is_manifest():    
            self.manifest_changed.emit()
        
        
    def _code_widget_saved(self):
        
        if self._is_manifest():
            self.manifest_changed.emit()
                    
    def set_code_path(self, path):
        
        if not path:
            self.save_file.hide()
            self.code_edit.hide()
            return
        
        folder_path = vtool.util_file.get_parent_path(path)
        
        self.directory = path
        
        self.save_file.set_directory(folder_path)
        
        self._load_file_text(path)
        
        if path:
            self.save_file.show()
            self.code_edit.show()
            
        
class ScriptWidget(vtool.qt_ui.DirectoryWidget):
    
    selection_changed = vtool.qt_ui.create_signal(object)
        
    def _define_main_layout(self):
        return QtGui.QVBoxLayout()
        
    def _build_widgets(self):
        
        self.code_manifest_tree = CodeManifestTree()
        self.code_tree = CodeTree()
        
        buttons_layout = QtGui.QHBoxLayout()
        
        run_code = QtGui.QPushButton('Run')
        add_code = QtGui.QPushButton('Create')
        import_data_code = QtGui.QPushButton('Create Data Import')
        remove_code = QtGui.QPushButton('Delete')
        
        
        add_code.setMaximumWidth(50)
        import_data_code.setMaximumWidth(120)
        remove_code.setMaximumWidth(50)
        run_code.setMaximumWidth(50)
        
        self.code_manifest_tree.itemSelectionChanged.connect(self._selection_changed)
        self.code_manifest_tree.itemRenamed.connect(self._selection_changed)
        
        run_code.clicked.connect(self._run_code)
        add_code.clicked.connect(self._create_code)
        import_data_code.clicked.connect(self._create_import_code)
        remove_code.clicked.connect(self._remove_code)
        
        self.main_layout.addWidget(self.code_manifest_tree)
        self.main_layout.addWidget(run_code)
        self.main_layout.addLayout(buttons_layout)
        
        buttons_layout.addWidget(add_code)
        buttons_layout.addWidget(import_data_code)
        buttons_layout.addWidget(remove_code)
        
             
        
    def _selection_changed(self):
        
        if self.code_manifest_tree.handle_selection_change:
        
            code_folder = self._get_current_code()
            self.selection_changed.emit(code_folder)
            
    def _get_current_code(self):
        
        item = self.code_manifest_tree.selectedItems()
        if item:
            item = item[0]
        
        if not item:
            return
        
        return item.text(0)
        
    def _run_code(self):
        
        process_tool = process.Process()
        process_tool.set_directory(self.directory)
        
        self.code_manifest_tree.run_current_item()
        
            
    def _create_code(self):
        
        process_tool = process.Process()
        process_tool.set_directory(self.directory)
        
        code_path = process_tool.create_code('code', 'script.python', inc_name = True)
        
        name = vtool.util_file.get_basename(code_path)
        
        item = self.code_manifest_tree._add_item(name, False)
        
        self.code_manifest_tree.scrollToItem(item)
        
    def _create_import_code(self):
        
        process_tool = process.Process()
        process_tool.set_directory(self.directory)
        
        folders = process_tool.get_data_folders()
        
        picked = vtool.qt_ui.get_pick(folders, 'Pick the data to import.', self)
        
        process_tool.create_code('import_%s' % picked, import_data = picked)
        self.code_manifest_tree._add_item('import_%s.py' % picked, False)
        
        
    def _remove_code(self):
        
        
        self.code_manifest_tree.remove_current_item()
        
    def set_directory(self, directory):
        super(ScriptWidget, self).set_directory(directory)
        
        if self.directory == self.last_directory:
            return
        
        self.code_tree.set_directory(directory)
        self.code_manifest_tree.set_directory(directory)
        
    def reset_process_script_state(self):
        self.code_manifest_tree.reset_process_script_state()
        
    def set_process_script_state(self, directory, state):
        self.code_manifest_tree.set_process_script_state(directory, state)
    
class CodeManifestTree(vtool.qt_ui.FileTreeWidget):
    
    itemRenamed = vtool.qt_ui.create_signal(object)
    
    def __init__(self):
        
        super(CodeManifestTree, self).__init__()
        
        self.title_text_index = 0
        
        self.setSortingEnabled(False)
        
        
        self.setIndentation(False)
        
        #palette = self.palette()
        
        #palette.setColor(palette.Background, QtGui.QColor(75,75,75))
        
        #self.setPalette(palette)
        
        self.setDragDropMode(self.InternalMove)
        self.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.invisibleRootItem().setFlags(QtCore.Qt.ItemIsDropEnabled) 
        
        self.dragged_item = None
        self.handle_selection_change = True
        
    def dragMoveEvent(self, event):
        super(CodeManifestTree, self).dragMoveEvent(event)
        
        self.handle_selection_change = False
        
        self.dragged_item = self.currentItem()
        
    def dropEvent(self, event):
        
        super(CodeManifestTree, self).dropEvent(event)
        
        self.clearSelection()
        
        self.setItemSelected(self.dragged_item, True)
        
        self.dragged_item = None
        self.handle_selection_change = True
        
        self._update_manifest()
    
    def mousePressEvent(self, event):
        super(CodeManifestTree, self).mousePressEvent(event)
        
        self.handle_selection_change = True

    def _define_header(self):
        return ['scripts']
    
    def _edit_finish(self, item):
        super(CodeManifestTree, self)._edit_finish(item)
        
        if type(item) == int:
            return
        
        name = str(item.text(self.title_text_index))
        
        if name.find('.'):
            split_name = name.split('.')
            name = split_name[0]
        
        if self.old_name.find('.'):
            split_old_name = self.old_name.split('.')
            old_name = split_old_name[0]
        
        process_tool = process.Process()
        process_tool.set_directory(self.directory)

        file_name = process_tool.rename_code(old_name, name)
        
        item.setText(self.title_text_index, file_name)
        
        self.itemRenamed.emit(file_name)
    
    def _define_item(self):
        return ManifestItem()
        
    def _add_item(self, filename, state):
        item = super(CodeManifestTree,self)._add_item(filename)
        
        if not state:
            item.setCheckState(0, QtCore.Qt.Unchecked)
        if state:
            item.setCheckState(0, QtCore.Qt.Checked)
        
        item.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsEditable|QtCore.Qt.ItemIsEnabled|QtCore.Qt.ItemIsDragEnabled|QtCore.Qt.ItemIsUserCheckable)
        item.tree = self
        
        return item
    

    
    def _add_items(self, files):
        
        scripts, states = files
        
        script_count = len(scripts)
        
        for inc in range(0, script_count):
            self._add_item(scripts[inc], states[inc])
    
    def _get_files(self):
        
        process_tool = process.Process()
        process_tool.set_directory(self.directory)
        
        scripts, states = process_tool.get_manifest()
        
        return [scripts, states]

    def _get_item_by_name(self, name):
        item_count = self.topLevelItemCount()
        
        for inc in range(0, item_count):
            
            item = self.topLevelItem(inc)
            
            if item.get_text() == name:
                return item

    def _update_manifest(self):
        process_tool = process.Process()
        process_tool.set_directory(self.directory)
        
        count = self.topLevelItemCount()
        
        scripts = []
        states = []
        
        for inc in range(0, count):
            
            item = self.topLevelItem(inc)
            
            name = item.text(0)
            state = item.checkState(0)
            
            if state == 0:
                state = False
            
            if state == 2:
                state = True
                
            scripts.append(name)
            states.append(state)
        
        process_tool.set_manifest(scripts, states)

    def reset_process_script_state(self):
        item_count = self.topLevelItemCount()
        
        for inc in range(0, item_count):
            item = self.topLevelItem(inc)
            item.set_state(-1)

    def set_process_script_state(self, directory, state):
        
        script_name = vtool.util_file.get_basename(directory)

        item = self._get_item_by_name(script_name)
        item.set_state(state)
        
    def run_current_item(self):
        
        items = self.selectedItems()
        item = items[0]
        
        name = item.text(0)
        name = name.split('.')
        name = name[0]
        
        process_tool = process.Process()
        process_tool.set_directory(self.directory)
        code_file = process_tool.get_code_files(name)
        process_tool.run_script(code_file)
        
    def remove_current_item(self):
        
        
        
        items = self.selectedItems()
        item = items[0]
        
        name = item.text(0)
        name = name.split('.')
        name = name[0]
        
        delete_state = vtool.qt_ui.get_permission('Delete %s?' % name)
        
        if delete_state:
        
            index = self.indexFromItem(item)
            
            self.takeTopLevelItem(index.row())
            
            process_tool = process.Process()
            process_tool.set_directory(self.directory)
            
            process_tool.delete_code(name)
            
            self._update_manifest()
                
        
        
        

class ManifestItem(vtool.qt_ui.TreeWidgetItem):
    
    def __init__(self):
        
        super(ManifestItem, self).__init__()
        
        self.setSizeHint(0, QtCore.QSize(10, 30))
        
        self.status_icon = self._radial_fill_icon(0.6, 0.6, 0.6)
        
        self.setCheckState(0, QtCore.Qt.Unchecked)
        
        #self.palette = QtGui.QPalette()
        #self.palette.setColor(self.palette.Background, QtGui.QColor(.5,.5,.5))
        
        
        
        #if vtool.util.is_in_maya():
            #brush = self.foreground(0)
        
        
            #brush.setColor(QtGui.QColor(100,100,100))
        
            #self.setForeground(0, brush)
            #self.setBackgroundColor(0, QtGui.QColor(75,75,75))
        
        
    
    def _radial_fill_icon(self, r,g,b):
        pixmap = QtGui.QPixmap(20, 20)
        pixmap.fill(QtCore.Qt.transparent)
        gradient = QtGui.QRadialGradient(10, 10, 10)
        gradient.setColorAt(0, QtGui.QColor.fromRgbF(r, g, b, 1))
        gradient.setColorAt(1, QtGui.QColor.fromRgbF(0, 0, 0, 0))
        
        painter = QtGui.QPainter(pixmap)
        painter.fillRect(0, 0, 100, 100, gradient)
        painter.end()
        
        icon = QtGui.QIcon(pixmap)
        
        self.setIcon(0, icon)
        
    def setData(self, column, role, value):
        super(ManifestItem, self).setData(column, role, value)
        
        if role == QtCore.Qt.CheckStateRole:
            
            if hasattr(self, 'tree'):
                self.tree._update_manifest()
                        
    def set_state(self, state):
        
        if state == 0:
            self._radial_fill_icon(1.0, 0.0, 0.0)    
        if state == 1:
            self._radial_fill_icon(0.0, 1.0, 0.0)
        if state == -1:
            self._radial_fill_icon(0.6, 0.6, 0.6)
    
    def set_text(self, text):
        self.setText(0, text)
        
    def get_text(self):
        return self.text(0)
    
class ManifestItemWidget(vtool.qt_ui.TreeItemWidget):
    
    def __init__(self):
        super(ManifestItemWidget, self).__init__()
        
        self.setSizePolicy(QtGui.QSizePolicy(10, 40))
    
    def _radial_fill_icon(self, r,g,b):
        pixmap = QtGui.QPixmap(20, 20)
        pixmap.fill(QtCore.Qt.transparent)
        gradient = QtGui.QRadialGradient(10, 10, 10)
        gradient.setColorAt(0, QtGui.QColor.fromRgbF(r, g, b, 1))
        gradient.setColorAt(1, QtGui.QColor.fromRgbF(0, 0, 0, 0))
        
        painter = QtGui.QPainter(pixmap)
        painter.fillRect(0, 0, 100, 100, gradient)
        painter.end()
        
        self.status_icon.setPixmap(pixmap)
        
    def _gradiant_fill_icon(self, r,g,b):
        
        pixmap = QtGui.QPixmap(20,20)
        pixmap.fill(QtCore.Qt.transparent)
        gradient = QtGui.QGradient()
        gradient.setColorAt(0, QtGui.QColor.fromRgbF(r,g,b,1))
        gradient.setColorAt(1, QtGui.QColor.fromRgbF(0, 0, 0, 0))
        
        painter = QtGui.QPainter(pixmap)
        painter.fillRect(0,0,100,100,gradient)
        painter.end()
        
        self.status_icon.setPixmap(pixmap)
    
    def _build_widgets(self):
        
        #check_box.setIcon(QtGui.QIcon())
        self.status_icon = QtGui.QLabel()
        self.status_icon.setMaximumSize(20,20)
        self._radial_fill_icon(0.6, 0.6, 0.6)
        #check_box.setIcon(QtGui.QIcon(pixmap))
        
        self.check_box = QtGui.QCheckBox()
        self.check_box.setCheckState(QtCore.Qt.Checked)
        
        self.palette = QtGui.QPalette()
        self.palette.setColor(self.palette.Background, QtGui.QColor(.5,.5,.5))
        
        self.check_box.setPalette(self.palette)
        
        #self.label = QtGui.QLabel()
        #self.label = QtGui.QLineEdit()
        #self.label.setReadOnly(True)
        
        
        self.main_layout.addWidget(self.status_icon)
        self.main_layout.addSpacing(5)
        self.main_layout.addWidget(self.check_box)
        self.main_layout.addSpacing(5)
        #self.main_layout.addWidget(self.label)
        self.main_layout.setAlignment(QtCore.Qt.AlignLeft)
        
    def set_text(self, text):
        pass
        #self.label.setText(text)
        
    def set_state(self, state):
        
        if state == 0:
            self._radial_fill_icon(1.0, 0.0, 0.0)    
        if state == 1:
            self._radial_fill_icon(0.0, 1.0, 0.0)
        if state == -1:
            self._radial_fill_icon(0.6, 0.6, 0.6)
            
    def get_check_state(self):
        return self.check_box.isChecked()
    
    def set_check_state(self, bool_value):
        
        if bool_value:
            self.check_box.setCheckState(QtCore.Qt.Checked)
        if not bool_value:
            self.check_box.setCheckState(QtCore.Qt.Unchecked)
        
                
class CodeTree(vtool.qt_ui.FileTreeWidget):
    
    itemRenamed = vtool.qt_ui.create_signal(object)
    
    def _define_header(self):
        return ['scripts']
        
    def _edit_finish(self, item):
        super(CodeTree, self)._edit_finish(item)
        
        if type(item) == int:
            return
        
        name = str(item.text(0))
        
        if name.find('.'):
            split_name = name.split('.')
            name = split_name[0]
        
        if self.old_name.find('.'):
            split_old_name = self.old_name.split('.')
            old_name = split_old_name[0]
        
        process_tool = process.Process()
        process_tool.set_directory(self.directory)

        file_name = process_tool.rename_code(old_name, name)
        
        item.setText(0, file_name)
        
        self.itemRenamed.emit(file_name)
        
    def _get_files(self):
        
        process_tool = process.Process()
        process_tool.set_directory(self.directory)
        
        scripts = process_tool.get_code_files(basename = True)
        
        return scripts
    