# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

import string

from vtool import util
from vtool import util_file
from vtool import qt, qt_ui


class ScriptManagerWidget(qt_ui.BasicWindow):
    
    title = 'Script Manager'
    
    def __init__(self, parent = None):
        
        self.directory = None
        self.user = None
        
        super(ScriptManagerWidget, self).__init__(parent)
        
    def _build_widgets(self):
        
        tab_widget = qt.QTabWidget()
        
        self.tree = EditScriptTreeWidget()
        self.tree.edit_mode_button.hide()
        self.tree.filter_widget.hide()
        
        self.tree.item_clicked.connect(self._tree_item_clicked)
        self.tree.script_changed.connect(self._load_code)
        
        self.code_view = CodeWidget()
        
        
        tab_widget.addTab(self.tree, 'Files')
        tab_widget.addTab(self.code_view, 'Code')
        
        tab_widget.setTabEnabled(1, False)
        
        self.main_layout.addWidget(tab_widget)
        
        self.tab_widget = tab_widget
        
    def _tree_item_clicked(self):
        self._load_code()
        
    def _load_code(self, filepath = None):
        
        if not self.tree.tree_widget.selectedItems():
            
            self.tab_widget.setTabEnabled(1, False)
            self.tree.manager_widget.run_script.hide()
            return
                
        if not filepath:
            self.tab_widget.setTabEnabled(1, True)
            filepath = self.tree.get_current_item_directory()
            self.tree.manager_widget.run_script.show()
        
        if filepath:
            if not util_file.is_file(filepath):
                self.tab_widget.setTabEnabled(1, False)
                self.tree.manager_widget.run_script.hide()
                return
        
        self.code_view.set_file(filepath)
        
        
    def set_directory(self, directory):
        
        self.directory = directory
        self.tree.set_directory(directory)
        
        default_path = util_file.join_path(self.directory, 'Default')
        if not util_file.is_dir(default_path):
            self.tree.tree_widget.create_branch('Default')
            
    def set_user(self, user):
        self.user = user
        
        user_path = util_file.join_path(self.directory, user)
        
        if not util_file.is_dir(user_path):
            self.tree.tree_widget.create_branch( user.capitalize() )
        
class CodeWidget(qt_ui.BasicWidget):
    
    def _build_widgets(self):
        
        self.code_edit = qt_ui.CodeTextEdit()
        self.code_edit.set_completer(CodeCompleter)
        save_button = qt.QPushButton('save')
        save_button.clicked.connect(self._save)
        
        self.main_layout.addWidget(self.code_edit)
        self.main_layout.addWidget(save_button)
        
    def _save(self):
        
        text = self.code_edit.toPlainText()
        
        lines= util_file.get_text_lines(text)
        
        util_file.write_lines(self.code_edit.filepath, lines)
        
    def set_file(self, path):
        self.code_edit.set_file(path)
    

class EditScriptTreeWidget(qt_ui.EditFileTreeWidget):
    
    description = 'Scripts'
    
    script_changed = qt_ui.create_signal(object)       
      
    def _define_tree_widget(self):
        return ScriptTreeWidget()
    
    def _define_manager_widget(self):
        manager = ManageScriptTreeWidget()
        manager.script_changed.connect(self._script_changed)
        
        return manager
                
    def _script_changed(self, filepath):
        
        self.script_changed.emit(filepath)
                
    def refresh(self):
        self.tree_widget.refresh()
        
    
        
        
    
              
class ManageScriptTreeWidget(qt_ui.ManageTreeWidget):
    
    script_changed = qt_ui.create_signal(object)
    
    def _build_widgets(self):
        
        h_layout = qt.QHBoxLayout()
        
        create_folder = qt.QPushButton('Folder')
        create_folder.clicked.connect(self._create_folder)
        
        create_python_script = qt.QPushButton('Python Script')
        create_python_script.clicked.connect(self._create_python_script)
        
        delete = qt.QPushButton('Delete')
        delete.clicked.connect(self._delete)
                
        h_layout.addWidget(create_folder)
        h_layout.addWidget(create_python_script)
        h_layout.addWidget(delete)
                
        run_script = qt.QPushButton('Run Script')
        run_script.clicked.connect(self._run_script)
        run_script.setMinimumSize(40, 40)
        self.run_script = run_script
        self.run_script.hide()
        
        self.main_layout.addWidget(run_script)
        self.main_layout.addLayout(h_layout)
        
        if util.is_in_nuke():
            nuke_group = self._build_nuke_widgets()
            self.main_layout.addWidget(nuke_group)
        
    def _build_nuke_widgets(self):
        
        nuke_group = qt.QGroupBox('Nuke')
        
        nuke_layout = qt.QHBoxLayout()
        nuke_group.setLayout(nuke_layout)
        
        create_nuke_script = qt.QPushButton('Nuke Script')
        create_nuke_script.clicked.connect(self._create_nuke_script)
        
        populate_nuke_script = qt.QPushButton('Populate')
        populate_nuke_script.clicked.connect(self._populate_nuke_script)
        
        nuke_layout.addWidget(create_nuke_script)
        nuke_layout.addWidget(populate_nuke_script)
        
        return nuke_group
        
        
    def _create_folder(self):
        self.tree_widget.create_branch()
        
    def _delete(self):
        self.tree_widget.delete_branch()
        
    def _create_python_script(self):
        self.tree_widget.create_script()
        
    def _create_nuke_script(self):
        filepath = self.tree_widget.create_script('nk')
                
    def _populate_nuke_script(self):
        items = self.tree_widget.selectedItems()
        item = items[0]
        
        if not item:
            return
        filepath = self.tree_widget.get_item_directory(item)
                
        if util.is_in_nuke():
            import nuke
            nuke.nodeCopy(filepath)
            
        self.script_changed(filepath)
        
    def _run_script(self):
        
        items = self.tree_widget.selectedItems()
        item = items[0]
        
        if not item:
            return
        filepath = self.tree_widget.get_item_directory(item)
        
        print 'running', filepath
        
        if util.is_in_nuke() and filepath.endswith('.nk'):
            import nuke
            nuke.nodePaste(filepath)
            
        if filepath.endswith('.py'):
            #filename = util_file.get_basename(filepath)
            #directory = util_file.get_dirname(filepath)
            util_file.run_python_module(filepath)
            #util_file.load_python_module(filename, directory)
        

        
              
class ScriptTreeWidget(qt_ui.FileTreeWidget):
       
    script_changed = qt_ui.create_signal(object, object)
        
    def __init__(self):
        
        super(ScriptTreeWidget, self).__init__()
        
        self.itemExpanded.connect(self._item_expanded)
        
        self.setColumnWidth(0, 250)
        
        self.current_name = None
        
        #self.setDragEnabled(True)
        #self.setAcceptDrops(True)
        self.setTabKeyNavigation(True)
        
    def _define_exclude_extensions(self):
        return ['pyc']
         
    def _define_new_branch_name(self):
        return 'Script Folder'
    
    def _define_item_size(self):
        return [150,25]
        
    def _emit_item_click(self, item):
        
        if not item:
            return
        
        self.current_name = item.text(0)
        self.item_clicked.emit(self.current_name, item)
        
    def _item_renamed(self, item):
        path = self.get_item_path_string(item)
        
        filepath = util_file.join_path(self.directory, path)
        
        directory = util_file.get_dirname(filepath)
        new_filename = util_file.get_basename(filepath)
        
        directory = util_file.join_path(directory, self.old_name)
        
        state = util_file.rename(directory, new_filename)
                
        return state
                
    def create_script(self, extension = 'py'):
        
        current_item = self.current_item
        
        if current_item:
            path = self.get_item_path_string(self.current_item)
            path = util_file.join_path(self.directory, path)
            
        if not current_item:
            path = self.directory
                
        if util_file.is_file(path):
            return path
                
        filepath = util_file.create_file('script1.%s' % extension, path, True)
                
        if current_item:
            self._add_sub_items(current_item)
            self.setItemExpanded(current_item, True)
            
            
        if not current_item:
            self.refresh()
            
        return filepath
        
class CodeCompleter(qt_ui.PythonCompleter):
    
    def __init__(self):
        super(CodeCompleter, self).__init__()
    
    def keyPressEvent(self):
        return
    
    def _insert_completion(self, completion_string):

        
        super(CodeCompleter, self)._insert_completion(completion_string)

        #this stops maya from entering edit mode in the outliner, if something is selected
        if util.is_in_maya():
            import maya.cmds as cmds
            
            cmds.setFocus('modelPanel1')
            #cmds.select(cl = True)
    
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
                        
                    args_name = string.join(args,',')
                    
            function_name = '%s(%s)' % (function_instance.im_func.func_name, args_name)
            
        return function_name
    
    def custom_import_load(self, assign_map, module_name):
        
        found = []

        
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
        
        return found
    
