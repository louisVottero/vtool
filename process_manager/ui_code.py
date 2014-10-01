import vtool.qt_ui
import vtool.util_file

import ui_data
import process

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
        
    def get_process_script_check_state(self, directory):
        return self.script_widget.get_process_script_check_state(directory)
    
        
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
        
        code_tree_separator = QtGui.QSplitter()
        code_tree_separator.setOrientation(QtCore.Qt.Vertical)
        
        self.code_manifest_tree = CodeManifestTree()
        self.code_tree = CodeTree()
        
        code_tree_separator.addWidget(self.code_manifest_tree)
        code_tree_separator.addWidget(self.code_tree)
        
        add_code = QtGui.QPushButton('Create Code')
        
        self.code_manifest_tree.itemSelectionChanged.connect(self._selection_changed)
        self.code_tree.refreshed.connect(self._selection_changed)
        self.code_tree.itemRenamed.connect(self._selection_changed)
        
        add_code.clicked.connect(self._create_code)
        
        self.main_layout.addWidget(code_tree_separator)
        self.main_layout.addWidget(add_code)        
        
        
    def _selection_changed(self):
        
        code_folder = self._get_current_code()
        self.selection_changed.emit(code_folder)
        
        
    def _get_current_code(self):
        item = self.code_manifest_tree.selectedItems()
        if item:
            item = item[0]
        
        if not item:
            return
        
        return item.text(1)
        
    def _create_code(self):
        
        process_tool = process.Process()
        process_tool.set_directory(self.directory)
        
        code_path = process_tool.create_code('code', 'script.python', inc_name = True)
        
        name = vtool.util_file.get_basename(code_path)
        
        self.code_tree._add_item(name)
        
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
        
    def get_process_script_check_state(self, directory):
        return self.code_manifest_tree.get_process_script_check_state(directory)
    
class CodeManifestTree(vtool.qt_ui.FileTreeWidget):
    def __init__(self):
        
        
        super(CodeManifestTree, self).__init__()
        
        self.title_text_index = 1
        
        self.setSortingEnabled(False)
        
        self.setIndentation(False)
        
    
    def _define_header(self):
        return ['state', 'name']
    
    def _define_item(self):
        return ManifestItem()
            
        
    def _add_item(self, filename):
        
        item = self._define_item()
        
        path = vtool.util_file.join_path(self.directory, filename)
        
        item.set_text(filename)
        
        if vtool.util_file.is_file(path):
            size = vtool.util_file.get_filesize(path)
            date = vtool.util_file.get_last_modified_date(path)
            
            item.setText(1, size)
            item.setText(2, date)
        
        self.addTopLevelItem(item)
    
    def _get_files(self):
        process_tool = process.Process()
        process_tool.set_directory(self.directory)
        
        scripts = process_tool.get_manifest_scripts()

        return scripts

    def _get_item_by_name(self, name):
        item_count = self.topLevelItemCount()
        
        for inc in range(0, item_count):
            
            item = self.topLevelItem(inc)
            
            if item.get_text() == name:
                return item

    def reset_process_script_state(self):
        item_count = self.topLevelItemCount()
        
        for inc in range(0, item_count):
            item = self.topLevelItem(inc)
            item.widget.set_state(-1)

    def set_process_script_state(self, directory, state):
        
        script_name = vtool.util_file.get_basename(directory)

        item = self._get_item_by_name(script_name)
        item.widget.set_state(state)
        
    def get_process_script_check_state(self, directory):
        
        script_name = vtool.util_file.get_basename(directory)
        
        item = self._get_item_by_name(script_name)
        return item.widget.get_check_state()

class ManifestItem(vtool.qt_ui.TreeWidgetItem):
    
    def _define_widget(self):
        return ManifestItemWidget()
    
    def set_text(self, text):
        self.setText(1, text)
        #self.widget.set_text(text)
        
    def get_text(self):
        #return self.widget.get_text()
        return self.text(1)
    
    
class ManifestItemWidget(vtool.qt_ui.TreeItemWidget):
    
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
    