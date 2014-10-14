import vtool.qt_ui

if vtool.qt_ui.is_pyqt():
    from PyQt4 import QtGui, QtCore, Qt, uic
if vtool.qt_ui.is_pyside():
    from PySide import QtCore, QtGui
    
    
class SettingsWidget(vtool.qt_ui.BasicWidget):
    
    project_directory_changed = vtool.qt_ui.create_signal(object)
    code_directory_changed = vtool.qt_ui.create_signal(object)
    
    def __init__(self):
        super(SettingsWidget, self).__init__()
        
        self.project_history = []
    
    def _define_main_layout(self):
        layout = QtGui.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)
        return layout 
    
    def _build_widgets(self):
        
        self.project_directory_widget = vtool.qt_ui.GetDirectoryWidget()
        self.project_directory_widget.set_label('project directory')
        self.project_directory_widget.directory_changed.connect(self._project_directory_changed)
        
        history_label = QtGui.QLabel('previous projects')
        self.history_list = QtGui.QListWidget()
        self.history_list.setAlternatingRowColors(True)
        self.history_list.itemClicked.connect(self._history_item_selected)
        self.history_list.setSelectionMode(self.history_list.NoSelection)
        
        self.code_directory_widget = vtool.qt_ui.GetDirectoryWidget()
        self.code_directory_widget.set_label('code directory')
        self.code_directory_widget.directory_changed.connect(self._code_directory_changed)
        
        self.main_layout.addWidget(self.project_directory_widget)
        self.main_layout.addWidget(history_label)
        self.main_layout.addWidget(self.history_list)
        self.main_layout.addWidget(self.code_directory_widget)
        
    def _project_directory_changed(self, project):
        self.project_directory_changed.emit(project)
        
    def _code_directory_changed(self, code_directory):
        self.code_directory_changed.emit(code_directory)
        
    def _history_item_selected(self):
        item = self.history_list.currentItem()
        if not item:
            return
        
        directory = item.text()
        self.set_project_directory(directory)
        
    def get_project_directory(self):
        return self.project_directory_widget.get_directory()
        
    def set_project_directory(self, directory):
        self.project_directory_widget.set_directory(directory)

    def set_code_directory(self, directory):
        if directory:
            self.code_directory_widget.set_directory(directory)
            
    def set_history(self, project_list):
        
        self.project_history = project_list
        
        self.history_list.clear()
        
        items = []
        
        for history in self.project_history:
            item = QtGui.QListWidgetItem()
            item.setText(history)
            item.setSizeHint(QtCore.QSize(30, 40))
            
            items.append(item)
            self.history_list.addItem(item)
        
        #self.history_list.addItems(items)
        
        self.history_list.clearSelection()