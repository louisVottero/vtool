# Copyright (C) 2016 Louis Vottero louis.vot@gmail.com    All rights reserved.

from vtool import qt_ui
from vtool import util

if qt_ui.is_pyqt():
    from PyQt4 import QtGui, QtCore, Qt, uic
if qt_ui.is_pyside():
    from PySide import QtCore, QtGui

class ProcessOptionsWidget(qt_ui.BasicWidget):
    
    def __init__(self):
        super(ProcessOptionsWidget, self).__init__()
        
        policy = self.sizePolicy()
        policy.setHorizontalPolicy(policy.Expanding)
        policy.setVerticalPolicy(policy.Expanding)
        
        self.setSizePolicy(policy)
                
        
    
    def _build_widgets(self):
        
        
        
        title = QtGui.QLabel('Variables')
        
        self.option_palette = ProcessOptionPalette()
        
        """
        arm_group = self.option_palette.add_group('Arm Rig')
        self.option_palette.add_title('Left', arm_group)
        self.option_palette.add_string_option('Arm_L', 'joint_arm_L', arm_group)
        self.option_palette.add_string_option('Elbow_L', 'joint_elbow_L', arm_group)
        self.option_palette.add_string_option('Wrist_L', 'joint_wrist_L', arm_group)
        self.option_palette.add_number_option('testing_L', 100, arm_group)
        #self.tree = ProcessOptionTree()
        """
        
        tree = ProcessOptionTree()
        
        self.main_layout.addWidget(title)
        self.main_layout.addWidget(self.option_palette)
        


        
class ProcessOptionPalette(qt_ui.BasicWidget):
    
    def __init__(self):
        super(ProcessOptionPalette, self).__init__()
        
        self.main_layout.setContentsMargins(0,10,0,0)
        self.main_layout.setSpacing(1)
        self.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding))
        
        self.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.create_right_click()
        
    def _build_widgets(self):
        self.child_layout = QtGui.QVBoxLayout()
        
        self.main_layout.addLayout(self.child_layout)
        self.main_layout.addSpacing(10)
        
    def _get_widget_names(self):
        
        item_count = self.child_layout.count()
        found = []
        for inc in range(0, item_count):
            
            item = self.child_layout.itemAt(inc)
            widget = item.widget()
            label = widget.get_name()
            found.append(label)
            
        return found
        
    def _get_unique_name(self, name):
        
        found = self._get_widget_names()
        while name in found:
            name = util.increment_last_number(name)
            
        return name
        
    def create_right_click(self, ):
        
        self.add_string = QtGui.QAction(self)
        self.add_string.setText('Add String')
        self.add_string.triggered.connect(self.add_string_option)
        self.addAction(self.add_string)
        
        add_number = QtGui.QAction(self)
        add_number.setText('Add Number')
        add_number.triggered.connect(self.add_number_option)
        self.addAction(add_number)
        
        self.add_group_action = QtGui.QAction(self)
        self.add_group_action.setText('Add Group')
        self.add_group_action.triggered.connect(self.add_group)
        self.addAction(self.add_group_action)
        
    def add_group(self, name = 'group'):
        
        name = self._get_unique_name(name)
        
        group = ProcessOptionGroup(name)
        self.child_layout.addWidget(group)
        
    def add_title(self, name, group = None):
        
        name = self._get_unique_name(name)
        
        title = QtGui.QLabel(name)
        self.child_layout.addWidget(title)
        
    def add_number_option(self, name = 'number', value = 0, group = None):
        
        name = self._get_unique_name(name)
        
        number_option = ProcessOptionNumber(name)
        number_option.set_value(value)
        self.child_layout.addWidget(number_option)
        
    def add_string_option(self, name = 'string', value = '', group = None):
        
        name = self._get_unique_name(name)
        
        string_option = ProcessOptionText(name)
        string_option.set_value(value)
        
        self.child_layout.addWidget(string_option)
        
class ProcessOptionGroup(ProcessOptionPalette):
    
    def __init__(self, name):
        
        self.name = name
        
        super(ProcessOptionGroup, self).__init__()
        self.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum))
        self.main_layout.setContentsMargins(0,0,0,5)
        
        self.add_group_action.setVisible(False)
        
    def _get_widget_names(self):
        
        parent = self.parent()
        item_count = parent.child_layout.count()
        found = []
        for inc in range(0, item_count):
            
            item = parent.child_layout.itemAt(inc)
            widget = item.widget()
            label = widget.get_name()
            found.append(label)
            
        return found
        
    def create_right_click(self):
        super(ProcessOptionGroup, self).create_right_click()
        
        move_up = QtGui.QAction(self)
        move_up.setText('Move Up')
        move_up.triggered.connect(self.move_up)
        
        move_dn = QtGui.QAction(self)
        move_dn.setText('Move Down')
        move_dn.triggered.connect(self.move_down)
        
        rename = QtGui.QAction(self)
        rename.setText('Rename')
        rename.triggered.connect(self.rename)
        
        self.insertAction(self.add_string, move_up)
        self.insertAction(self.add_string, move_dn)
        self.insertAction(self.add_string, rename)
        
    def _build_widgets(self):
        main_group_layout = QtGui.QVBoxLayout()
        
        main_group_layout.setContentsMargins(0,0,0,0)
        
        self.child_layout = QtGui.QVBoxLayout()
        self.child_layout.setContentsMargins(0,5,5,10)
        
        self.child_layout.setSpacing(0)
        
        main_group_layout.addLayout(self.child_layout)
        main_group_layout.addSpacing(10)
        
        self.group = QtGui.QGroupBox(self.name)
        self.group.setLayout(main_group_layout)
        
        self.group.child_layout = self.child_layout
        
        self.main_layout.addWidget(self.group)
        
    def move_up(self):
        
        parent = self.parent()
        layout = parent.child_layout
        index = layout.indexOf(self)
        
        if index == 0:
            return
        
        index = index - 1
        
        parent.child_layout.removeWidget(self)
        layout.insertWidget(index, self)
        
    def move_down(self):
        
        parent = self.parent()
        layout = parent.child_layout
        index = layout.indexOf(self)
        
        if index == (layout.count() - 1):
            return
        
        index = index + 1
        
        parent.child_layout.removeWidget(self)
        layout.insertWidget(index, self)
        
    def rename(self):
        
        found = self._get_widget_names()
        print 'widget names', found
        title = self.group.title()
        
        new_name =  qt_ui.get_new_name('Rename group', self, title)
        
        if new_name == title:
            return
        
        if new_name == None:
            return
        
        while new_name in found:
            new_name = util.increment_last_number(new_name)
            
        self.group.setTitle(new_name)
        
    def get_name(self):
        return self.group.title()
    
    def set_name(self, name):
        
        self.group.setTitle(name)

        
class ProcessOption(qt_ui.BasicWidget):
    
    def __init__(self, name):
        super(ProcessOption, self).__init__()
        
        self.name = name
        
        self.option_widget = self._define_option_widget()
        if self.option_widget:
            self.main_layout.addWidget(self.option_widget)
        self.main_layout.setContentsMargins(0,0,0,0)
        
        self.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.create_right_click()
        
    def _get_widget_names(self):
        
        parent = self.parent()
        item_count = parent.child_layout.count()
        found = []
        for inc in range(0, item_count):
            
            item = parent.child_layout.itemAt(inc)
            widget = item.widget()
            label = widget.get_name()
            found.append(label)
            
        return found
        
    def create_right_click(self):
        
        move_up = QtGui.QAction(self)
        move_up.setText('Move Up')
        move_up.triggered.connect(self.move_up)
        self.addAction(move_up)
        
        move_dn = QtGui.QAction(self)
        move_dn.setText('Move Down')
        move_dn.triggered.connect(self.move_down)
        self.addAction(move_dn)
        
        rename = QtGui.QAction(self)
        rename.setText('Rename')
        rename.triggered.connect(self._rename)
        self.addAction(rename)
        
        remove = QtGui.QAction(self)
        remove.setText('Remove')
        remove.triggered.connect(self.remove)
        self.addAction(remove)
        
    def remove(self):
        parent = self.parent()
        
        print parent
        
        parent.child_layout.removeWidget(self)
        self.deleteLater()
        
    def move_up(self):
        
        parent = self.parent()
        layout = parent.child_layout
        index = layout.indexOf(self)
        
        if index == 0:
            return
        
        index = index - 1
        
        parent.child_layout.removeWidget(self)
        layout.insertWidget(index, self)
        
    def move_down(self):
        
        parent = self.parent()
        layout = parent.child_layout
        index = layout.indexOf(self)
        
        if index == (layout.count() - 1):
            return
        
        index = index + 1
        
        parent.child_layout.removeWidget(self)
        layout.insertWidget(index, self)
        
    def _rename(self):
        
        title = self.get_name() 
        
        new_name =  qt_ui.get_new_name('Rename group', self, title)
        
        found = self._get_widget_names()
        
        if new_name == title:
            return
        
        if new_name == None:
            return
        
        while new_name in found:
            new_name = util.increment_last_number(new_name)
        
        self.set_name(new_name)
        
    def _define_option_widget(self):
        return
    
    def get_name(self):
        
        name = self.option_widget.get_label()
        
        return name
    
    def set_name(self, name):
        
        self.option_widget.set_label(name)
        
        
class ProcessTitle(ProcessOption):
    
    pass


    
class ProcessOptionText(ProcessOption):
    
    def _define_option_widget(self):
        return qt_ui.GetString(self.name)
        
    def set_value(self, value):
        self.option_widget.set_text(value)
        
class ProcessOptionNumber(ProcessOption):
    def _define_option_widget(self):
        return qt_ui.GetNumber(self.name)
    
    def set_value(self, value):
        self.option_widget.set_value(value)
        
        
        
class WidgetDelegate (QtGui.QStyledItemDelegate):
    
    def paint(self,painter, option, index):
        if index.column() == 1:
            progress = index.data().toInt()

            progressBarOption = QtGui.QStyleOptionProgressBar()
            progressBarOption.rect = option.rect
            progressBarOption.minimum = 0
            progressBarOption.maximum = 100
            progressBarOption.progress = progress
            
            progressBarOption.text = "%s%" % progress
            progressBarOption.textVisible = True

            
            QtGui.QApplication.style().drawControl(QtGui.QStyle.CE_ProgressBar, progressBarOption, painter)
        else:
            QtGui.QStyledItemDelegate.paint(self, painter, option, index)
        
    
class ProcessOptionTree(qt_ui.TreeWidget):
    
    def __init__(self):
        
        
        
        super(ProcessOptionTree, self).__init__()
        
        self.title_text_index = 0
        self.setColumnCount(2)
        self.setHeaderLabels(['name', 'value'])
        self.setSortingEnabled(False)
        self.setColumnWidth(0, 150)
        self.setIndentation(15)
        self.setAllColumnsShowFocus(False)
        
        self.setItemDelegate(WidgetDelegate())
        
        self._create_item_group('joints')
        """
        self._add_child_item('joints', 'arm_joints_L', "joint_arm_L, joint_elbow_L, joint_wrist_L")
        self._add_child_item('joints', 'arm_joints_R', "joint_arm_R, joint_elbow_R, joint_wrist_R")
        self._add_child_item('joints', 'leg_joints_L', "joint_leg_L, joint_knee_L, joint_ankle_L")
        self._add_child_item('joints', 'leg_joints_R', "joint_leg_R, joint_knee_R, joint_ankle_R")
        self._create_item_group('arm_L')
        self._create_item_group('arm_R')
        self._add_child_item('arm_L', 'arm joint', 'joint_arm_L')
        self._add_child_item('arm_L', 'elbow joint', 'joint_elbow_L')
        self._add_child_item('arm_L', 'wrist joint', 'joint_wrist_L')
        self._add_child_item('arm_R', 'arm joint', 'joint_arm_R')
        self._add_child_item('arm_R', 'elbow joint', 'joint_elbow_R')
        self._add_child_item('arm_R', 'wrist joint', 'joint_wrist_R')
        """

    def _create_item_group(self, name):
        
        item = QtGui.QTreeWidgetItem()
        item.setText(0, name)
        
        item.setSizeHint(0, QtCore.QSize(75, 25))
        
        self.addTopLevelItem(item)
        
    def _add_child_item(self, group, name, value):
        
        count = self.topLevelItemCount()
        
        for inc in range(0, count):
            
            if self.topLevelItem(inc).text(0) == group:
                parent = self.topLevelItem(inc)
                break
        
        if not parent:
            return
        
        item = QtGui.QTreeWidgetItem()
        item.setText(0, name)
        #item.setText(1, str(value))
        
        text_line = QtGui.QLineEdit()
        text_line.setText(str(value))
        text_line.setAutoFillBackground(True)
        
        
        item.setSizeHint(0, QtCore.QSize(100, 25))
        
        parent.addChild(item)

        self.setItemWidget(item, 1, text_line)

    def _edit_start(self, item):
        
        self.old_name = str(item.text(1))
        
        #close is needed
        self.closePersistentEditor(item, 1)
        self.openPersistentEditor(item, 1)
        
        self.edit_state = item
        
        return

    def load(self):
        pass