# Copyright (C) 2016 Louis Vottero louis.vot@gmail.com    All rights reserved.

from vtool import qt_ui

if qt_ui.is_pyqt():
    from PyQt4 import QtGui, QtCore, Qt, uic
if qt_ui.is_pyside():
    from PySide import QtCore, QtGui

class ProcessOptionsWidget(qt_ui.BasicWidget):
    
    def __init__(self):
        super(ProcessOptionsWidget, self).__init__()
        
        policy = self.sizePolicy()
        
        policy.setHorizontalPolicy(policy.Minimum)
        policy.setHorizontalStretch(2)
        
        self.setSizePolicy(policy)
    
    def _build_widgets(self):
        
        title = QtGui.QLabel('Variables')
        self.tree = ProcessOptionTree()
        
        self.main_layout.addWidget(title)
        self.main_layout.addWidget(self.tree)
        
    
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
        
        
        self._create_item_group('joints')
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