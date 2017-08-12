# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

from vtool import qt

import util
import util_file
import string
import re
import random
import sys

QWIDGETSIZE_MAX = qt.QWIDGETSIZE_MAX

global type_QT
type_QT = qt.type_QT

def is_pyqt():
    if qt.is_pyqt():
        return True
    return False
    
def is_pyside():
    if qt.is_pyside():
        return True
    return False

def is_pyside2():
    if qt.is_pyside2():
        return True
    return False

def build_qt_application(*argv):
    application = qt.QApplication(*argv)
    return application

def create_signal(*arg_list):
    if is_pyqt():
        return qt.QtCore.pyqtSignal(*arg_list)
    if is_pyside() or is_pyside2():
        return qt.QtCore.Signal(*arg_list)
    

class BasicGraphicsView(qt.QGraphicsView):
    
    def __init__(self):
        
        super(BasicGraphicsView, self).__init__()
        
        self.scene = qt.QGraphicsScene()
        
        self.setViewportUpdateMode(self.FullViewportUpdate)
        
        self.setScene(self.scene)
        

class BasicWindow(qt.QMainWindow):
    
    title = 'BasicWindow'
    _last_instance = None

    def __init__(self, parent = None, use_scroll = False):
        
        self.main_layout = self._define_main_layout()
        
        self.__class__._last_instance = self
        
        super(BasicWindow, self).__init__(parent)
        
        self.setWindowTitle(self.title)
        self.setObjectName(self.title)
        
        main_widget = qt.QWidget()
        
        if use_scroll:
            scroll = qt.QScrollArea()
            scroll.setWidgetResizable(True)
            
            scroll.setWidget(main_widget)
            self._scroll_widget = scroll
        
            main_widget.setSizePolicy(qt.QSizePolicy(qt.QSizePolicy.Expanding, qt.QSizePolicy.Expanding))
            self.setCentralWidget( scroll )
        #util.show('Main layout: %s' % self.main_layout)
        
        if not use_scroll:
            self.setCentralWidget(main_widget)
        
        main_widget.setLayout(self.main_layout)
        
        self.main_widget = main_widget
        
        self.main_layout.expandingDirections()
        self.main_layout.setContentsMargins(1,1,1,1)
        self.main_layout.setSpacing(2)
        
        self._build_widgets()
        
        
        
        
    def keyPressEvent(self, event):
        return
        
    def _define_main_layout(self):
        return qt.QVBoxLayout()
    
    def _build_widgets(self):
        return       
       
class DirectoryWindow(BasicWindow):
    
    def __init__(self, parent = None):
        
        self.directory = None
        
        super(DirectoryWindow, self).__init__(parent)
        
    def set_directory(self, directory):
        self.directory = directory
       
class BasicWidget(qt.QWidget):

    def __init__(self, parent = None, scroll = False):
        super(BasicWidget, self).__init__(parent)
        
        self.main_layout = self._define_main_layout() 
        self.main_layout.setContentsMargins(2,2,2,2)
        self.main_layout.setSpacing(2)
        
        
        if scroll:
            
            layout = qt.QHBoxLayout()
            self.setLayout(layout)
            
            
            scroll = qt.QScrollArea()
            scroll.setWidgetResizable(True)
            
            layout.addWidget(scroll)
            
            widget = qt.QWidget()
                
            scroll.setWidget(widget)
            self._scroll_widget = scroll
            
            widget.setLayout(self.main_layout)
            
            widget.setSizePolicy(qt.QSizePolicy(qt.QSizePolicy.Expanding, qt.QSizePolicy.Expanding))
            self.setSizePolicy(qt.QSizePolicy(qt.QSizePolicy.Expanding, qt.QSizePolicy.Expanding))
            
            
            
            #self.setLayout(self.main_layout)
        
        if not scroll:
            self.setLayout(self.main_layout)
        
        
        self._build_widgets()
        
    def keyPressEvent(self, event):
        return

    def _define_main_layout(self):
        layout = qt.QVBoxLayout()
        layout.setAlignment(qt.QtCore.Qt.AlignTop)
        return layout
        
    def _build_widgets(self):
        pass
    
class BasicDialog(qt.QDialog):
    
    def __init__(self, parent = None):
        super(BasicDialog, self).__init__(parent)
        
        self.main_layout = self._define_main_layout() 
        self.main_layout.setContentsMargins(2,2,2,2)
        self.main_layout.setSpacing(2)
        
        self.setLayout(self.main_layout)
        
        self.setWindowFlags( self.windowFlags() ^ qt.QtCore.Qt.WindowContextHelpButtonHint | qt.QtCore.Qt.WindowStaysOnTopHint)
        
        self._build_widgets()  
            
    def _define_main_layout(self):
        layout = qt.QVBoxLayout()
        layout.setAlignment(qt.QtCore.Qt.AlignTop)
        return layout

    def _build_widgets(self):
        pass
       
        
class BasicDockWidget(qt.QDockWidget):
    def __init__(self, parent = None):
        super(BasicDockWidget, self).__init__()
        
        self.main_layout = self._define_main_layout() 
        self.main_layout.setContentsMargins(2,2,2,2)
        self.main_layout.setSpacing(2)
        
        self.setLayout(self.main_layout)
        
        self._build_widgets()

    def _define_main_layout(self):
        layout = qt.QVBoxLayout()
        layout.setAlignment(qt.QtCore.Qt.AlignTop)
        return layout
        
    def _build_widgets(self):
        pass

        
class DirectoryWidget(BasicWidget):
    def __init__(self, parent = None):
        
        self.directory = None
        self.last_directory = None
        
        super(DirectoryWidget, self).__init__()
        
        
        
    def set_directory(self, directory):
        
        self.last_directory = self.directory
        self.directory = directory
     
    
       
class TreeWidget(qt.QTreeWidget):
    
    def __init__(self):
        super(TreeWidget, self).__init__()
        
        self._auto_add_sub_items = True
        
        self.title_text_index = 0
        self.itemExpanded.connect(self._item_expanded)
        self.itemCollapsed.connect(self._item_collapsed)
        self.setIndentation(25)
        self.setExpandsOnDoubleClick(False)
        
        version = util.get_maya_version()
        if version < 2016:
            self.setAlternatingRowColors(True)
        if util.is_in_nuke():
            self.setAlternatingRowColors(False)
            
        self.setSortingEnabled(True)
        self.sortByColumn(0, qt.QtCore.Qt.AscendingOrder)
        
        self.itemActivated.connect(self._item_activated)
        self.itemChanged.connect(self._item_changed)
        self.itemSelectionChanged.connect(self._item_selection_changed)
        self.itemClicked.connect(self._item_clicked)
        
        self.text_edit = True
        self.edit_state = None
        self.old_name = None
        
        self.last_item = None
        self.current_item = None
        self.current_name = None
        
        if not util.is_in_maya() and not util.is_in_nuke():
            palette = qt.QPalette()
            palette.setColor(palette.Highlight, qt.QtCore.Qt.gray)
            self.setPalette(palette)
            
        self.dropIndicatorRect = qt.QtCore.QRect()

    def paintEvent(self, event):
        painter = qt.QPainter(self.viewport())
        self.drawTree(painter, event.region())
        # in original implementation, it calls an inline function paintDropIndicator here
        self.paintDropIndicator(painter)
    
    def paintDropIndicator(self, painter):

        if self.state() == qt.QAbstractItemView.DraggingState:
            opt = qt.QStyleOption()
            opt.initFrom(self)
            opt.rect = self.dropIndicatorRect
            rect = opt.rect

            color = qt.QtCore.Qt.black
            
            if util.is_in_maya():
                color = qt.QtCore.Qt.white
            

            brush = qt.QBrush(qt.QColor(color))

            if rect.height() == 0:
                pen = qt.QPen(brush, 2, qt.QtCore.Qt.DotLine)
                painter.setPen(pen)
                painter.drawLine(rect.topLeft(), rect.topRight())
            else:
                pen = qt.QPen(brush, 2, qt.QtCore.Qt.DotLine)
                painter.setPen(pen)
                painter.drawRect(rect)
    
    
    def dragMoveEvent(self, event):
        
        
        
        pos = event.pos()
        item = self.itemAt(pos)

        if item:
            index = self.indexFromItem(item)  # this always get the default 0 column index

            rect = self.visualRect(index)
            rect_left = self.visualRect(index.sibling(index.row(), 0))
            rect_right = self.visualRect(index.sibling(index.row(), self.header().logicalIndex(self.columnCount() - 1)))  # in case section has been moved

            self.dropIndicatorPosition = self.position(event.pos(), rect, index)
            
            if self.dropIndicatorPosition == self.AboveItem:
                self.dropIndicatorRect = qt.QtCore.QRect(rect_left.left(), rect_left.top(), rect_right.right() - rect_left.left(), 0)
                event.accept()
            elif self.dropIndicatorPosition == self.BelowItem:
                self.dropIndicatorRect = qt.QtCore.QRect(rect_left.left(), rect_left.bottom(), rect_right.right() - rect_left.left(), 0)
                event.accept()
            elif self.dropIndicatorPosition == self.OnItem:
                self.dropIndicatorRect = qt.QtCore.QRect(rect_left.left(), rect_left.top(), rect_right.right() - rect_left.left(), rect.height())
                event.accept()
            else:
                self.dropIndicatorRect = qt.QtCore.QRect()

            self.model().setData(index, self.dropIndicatorPosition, qt.QtCore.Qt.UserRole)
        
        self.viewport().update()
        
        super(TreeWidget, self).dragMoveEvent(event)
        
    def drop_on(self, l):

        event, row, col, index = l

        root = self.rootIndex()

        if self.viewport().rect().contains(event.pos()):
            index = self.indexAt(event.pos())
            if not index.isValid() or not self.visualRect(index).contains(event.pos()):
                index = root

        if index != root:

            dropIndicatorPosition = self.position(event.pos(), self.visualRect(index), index)
            
            if self.dropIndicatorPosition == self.AboveItem:
                #'dropon above'
                row = index.row()
                col = index.column()
                index = index.parent()

            elif self.dropIndicatorPosition == self.BelowItem:
                #'dropon below'
                row = index.row() + 1
                col = index.column()
                index = index.parent()

            elif self.dropIndicatorPosition == self.OnItem:
                #'dropon onItem'
                pass
            elif self.dropIndicatorPosition == self.OnViewport:
                pass
            else:
                pass

        else:
            self.dropIndicatorPosition = self.OnViewport

        l[0], l[1], l[2], l[3] = event, row, col, index

        # if not self.droppingOnItself(event, index):
        return True
        
    def position(self, pos, rect, index):
        r = qt.QAbstractItemView.OnViewport
        # margin*2 must be smaller than row height, or the drop onItem rect won't show
        margin = 5
        if pos.y() - rect.top() < margin:
            r = qt.QAbstractItemView.AboveItem
        elif rect.bottom() - pos.y() < margin:
            r = qt.QAbstractItemView.BelowItem

        # this rect is always the first column rect
        # elif rect.contains(pos, True):
        elif pos.y() - rect.top() > margin and rect.bottom() - pos.y() > margin:
            r = qt.QAbstractItemView.OnItem

        return r
    
    def is_item_dropped(self, event, strict = False):
        """
        
        Args
            strict: False is good for lists that are ordered alphabetically. True is good for lists that are not alphabetical and can be reordered.
        """
        position = event.pos()
        index = self.indexAt(position)

        is_dropped = False

        if event.source == self and event.dropAction() == qt.QtCore.Qt.MoveAction or self.dragDropMode() == qt.QAbstractItemView.InternalMove:
            
            topIndex = qt.QtCore.QModelIndex()
            col = -1
            row = -1
            l = [event, row, col, topIndex]

            if self.drop_on(l):
                event, row, col, topIndex = l
                
                if row > -1:
                    if row == (index.row() - 1):
                        is_dropped = False
                if row == -1:
                    is_dropped = True
                    
                
                if row == (index.row() + 1):
                    if strict:
                        is_dropped = False
                    if not strict:
                        is_dropped = True
                    
                    
        return is_dropped
    
    def _define_item(self):
        return qt.QTreeWidgetItem()
    
    def _define_item_size(self):
        return 
        
    def _clear_selection(self):
        
        self.clearSelection()
        self.current_item = None
        
        if self.edit_state:
            self._edit_finish(self.last_item)
            
    def _item_clicked(self, item, column):
        
        self.last_item = self.current_item
        
        self.current_item = self.currentItem()

        if not item or column != self.title_text_index:
            if self.last_item:
                self._clear_selection()

    def mousePressEvent(self, event):
        super(TreeWidget, self).mousePressEvent(event)
        
        item = self.itemAt(event.x(), event.y())
                
        if not item:
            self._clear_selection()
                          
    def _item_selection_changed(self):
        
        item_list = self.selectedItems()
        
        current_item = None
        
        if item_list:
            current_item = item_list[0]
        
        if current_item:
            self.current_name = current_item.text(self.title_text_index)
        
        if self.edit_state:
            self._edit_finish(self.edit_state)
    
        if not current_item:        
            self._emit_item_click(current_item)
        
    def _emit_item_click(self, item):
        
        if item:
            name = item.text(self.title_text_index)
        if not item:
            name = ''
                        
        self.itemClicked.emit(item, 0)      
            
    def _item_changed(self, current_item, previous_item):
        
        if self.edit_state:
            self._edit_finish(previous_item)
        
    def _item_activated(self, item):
        
        if not self.edit_state:
            
            if self.text_edit:
                self._edit_start(item)
            return
                
        if self.edit_state:
            self._edit_finish(self.edit_state)
            
            return
            
    def _item_expanded(self, item):
        if self._auto_add_sub_items == True:
            self._add_sub_items(item) 
        
        #self.resizeColumnToContents(self.title_text_index)
        
    def _item_collapsed(self, item):
        
        pass
        
    def _edit_start(self, item):
        
        self.old_name = str(item.text(self.title_text_index))
        
        #close is needed
        self.closePersistentEditor(item, self.title_text_index)
        
        self.openPersistentEditor(item, self.title_text_index)
        
        self.edit_state = item
        
        return
        
    
    def _edit_finish(self, item):
        
        if not hasattr(self.edit_state, 'text'):
            return
        
        self.edit_state = None
               
        
        if type(item) == int:
            return self.current_item
        
        self.closePersistentEditor(item, self.title_text_index)
        
        state = self._item_rename_valid(self.old_name, item)
        
        if not state:
            item.setText(self.title_text_index, self.old_name ) 
            return item
            
        if state:
        
            state = self._item_renamed(item)
            
            if not state:
                item.setText( self.title_text_index, self.old_name  )
         
            return item
                
        return item
    
    def _item_rename_valid(self, old_name, item):
        
        new_name = item.text(self.title_text_index)
        
        if not new_name:
            return False
        
        if self._already_exists(item):
            return False
        
        if old_name == new_name:
            return False
        if old_name != new_name:
            return True
    
    def _already_exists(self, item, parent = None):    
        
        name = item.text(0)
        parent = item.parent()
        
        if not parent:
        
            skip_index = self.indexFromItem(item)
            skip_index = skip_index.row()
        
        
            for inc in range(0, self.topLevelItemCount() ):
                
                if skip_index == inc:
                    continue
                
                other_name = self.topLevelItem(inc).text(0)
                other_name = str(other_name)
                                
                if name == other_name:
                    return True
        
        if parent:
            
            skip_index = parent.indexOfChild(item)
            
            for inc in range( 0, parent.childCount() ):
                
                if inc == skip_index:
                    continue
                
                other_name = parent.child(inc).text(0)
                other_name = str(other_name)
                
                if name == other_name:
                    return True
                
            
        return False
    
    def _item_renamed(self, item):
        return False

    def _delete_children(self, item):
        self.delete_tree_item_children(item)
        
    def _add_sub_items(self, item):
        pass
        
    def addTopLevelItem(self, item):
        
        super(TreeWidget, self).addTopLevelItem(item)
        
        if hasattr(item, 'widget'):
            if hasattr(item, 'column'):
                self.setItemWidget(item, item.column, item.widget)
                
            if not hasattr(item, 'column'):
                self.setItemWidget(item, 0, item.widget)
                
    def insertTopLevelItem(self, index, item):
        super(TreeWidget, self).insertTopLevelItem(index, item)
        
        if hasattr(item, 'widget'):
            if hasattr(item, 'column'):
                self.setItemWidget(item, item.column, item.widget)
                
            if not hasattr(item, 'column'):
                self.setItemWidget(item, 0, item.widget)
           
    def unhide_items(self):
            
        for inc in range( 0, self.topLevelItemCount() ):
            item = self.topLevelItem(inc)
            self.setItemHidden(item, False)

    def filter_names(self, string):
        
        self.unhide_items()
                        
        for inc in range( 0, self.topLevelItemCount() ):
                
            item = self.topLevelItem(inc)
            text = str( item.text(self.title_text_index) )
            
            string = str(string)
            
            if text.find(string) == -1:
                self.setItemHidden(item, True)
                
            #if not text.startswith(string) and not text.startswith(string.upper()):
                
            #    self.setItemHidden(item, True)  
            
    def get_tree_item_path(self, tree_item):
                
        parent_items = []
        parent_items.append(tree_item)
        
        if not tree_item:
            return
        
        
        try:
            #when selecting an item in the tree and refreshing it will throw this error:
            #wrapped C/C++ object of type ProcessItem has been deleted
            parent_item = tree_item.parent()
        except:
            parent_item = None
        
        while parent_item:
            parent_items.append(parent_item)
            
            parent_item = parent_item.parent()
            
        return parent_items
    
    def get_tree_item_names(self, tree_items):
        
        item_names = []
        
        if not tree_items:
            return item_names
        
        for tree_item in tree_items:
            name = self.get_tree_item_name(tree_item)
            if name:
                item_names.append(name)    
            
        return item_names
    
    def get_tree_item_name(self, tree_item):
        try:
            #when selecting an item in the tree and refreshing it will throw this error:
            #wrapped C/C++ object of type ProcessItem has been deleted
            count = qt.QTreeWidgetItem.columnCount( tree_item )
        except:
            count = 0
            
        name = []
            
        for inc in range(0, count):
                
            name.append( str( tree_item.text(inc) ) )
            
        return name
    
    def get_item_path_string(self, item):
        
        parents = self.get_tree_item_path(item)
        parent_names = self.get_tree_item_names(parents)
        
        names = []
        
        if not parent_names:
            return
        
        if len(parent_names) == 1 and not parent_names[0]:
            return
        
        for name in parent_names:
            names.append(name[0])
        
        names.reverse()
        
        path = string.join(names, '/')
        
        return path
    
    def delete_empty_children(self, tree_item):
        
        count = tree_item.childCount()
        
        if count <= 0:
            return
        
        for inc in range(0, count):
            
            item = tree_item.child(inc)
            
            if item and not item.text(0):
                item = tree_item.takeChild(inc)
                del(item)
               
    def delete_tree_item_children(self, tree_item):
        
        count = tree_item.childCount()
        
        if count <= 0:
            return
        
        children = tree_item.takeChildren()

        for child in children:
            del(child)
            
        
            
    def get_tree_item_children(self, tree_item):
        count = tree_item.childCount()
        
        items = []
        
        for inc in range(0, count):
            items.append( tree_item.child(inc) )
        
        return items
    
    def set_text_edit(self, bool_value):
        self.text_edit = bool_value
        
class TreeWidgetItem(qt.QTreeWidgetItem):
    
    def __init__(self, parent = None):
        self.widget = self._define_widget()
        if self.widget:
            self.widget.item = self
                
        self.column = self._define_column()
        
        super(TreeWidgetItem, self).__init__(parent)
        
        
    def _define_widget(self):
        return
    
    def _define_column(self):
        return 0
        
     
class TreeItemWidget(BasicWidget):
        
    def __init__(self, parent = None):
        self.label = None
        
        super(TreeItemWidget, self).__init__(parent)
        
    def _define_main_layout(self):
        return qt.QHBoxLayout()
    
    def _build_widgets(self):
        self.label = qt.QLabel()
        
        self.main_layout.addWidget(self.label)
    
    def set_text(self, text):
        self.label.setText(text)
        
    def get_text(self):
        return self.label.text()
        
class TreeItemFileWidget(TreeItemWidget):
    pass
        
class FileTreeWidget(TreeWidget):
    
    refreshed = create_signal()
    
    def __init__(self):
        self.directory = None
        
        super(FileTreeWidget, self).__init__()
        
        self.setHeaderLabels(self._define_header())
    
    def _define_new_branch_name(self):
        return 'new_folder'  
        
    def _define_header(self):
        return ['name','size','date']

    def _define_item(self):
        return qt.QTreeWidgetItem()
    
    def _define_exclude_extensions(self):
        return

    def _get_files(self, directory = None):
        
        if not directory:
            directory = self.directory
            
        return util_file.get_files_and_folders(directory)
    
    def _load_files(self, files):
        self.clear()
        
        self._add_items(files)
        
    def _add_items(self, files, parent = None):
        
        for filename in files:
            if parent:
                self._add_item(filename, parent)
            if not parent:
                self._add_item(filename)

    def _add_item(self, filename, parent = None):
        
        self.clearSelection()
        
        path_name = filename
        
        found = False
        
        if parent:
            parent_path = self.get_item_path_string(parent)
            path_name = '%s/%s' % (parent_path, filename)
            
            for inc in range(0,parent.childCount()):
                item = parent.child(inc)
                if item.text(0) == filename:
                    found = item
        
        if not parent:
            for inc in range(0, self.topLevelItemCount()):
                item = self.topLevelItem(inc)
                if item.text(0) == filename:
                    found = item
                
        exclude = self._define_exclude_extensions()
        
        if exclude:
            split_name = filename.split('.')
            extension = split_name[-1]
    
            if extension in exclude:
                return
        
        if not found:
            item = self._define_item()
        if found:
            item = found
        
        size = self._define_item_size()
        if size:
            size = qt.QtCore.QSize(*size)
            
            item.setSizeHint(self.title_text_index, size)
            
        path = util_file.join_path(self.directory, path_name)
        
        sub_files = util_file.get_files_and_folders(path)
                
        item.setText(self.title_text_index, filename)
        
        if util_file.is_file(path):
            size = util_file.get_filesize(path)
            date = util_file.get_last_modified_date(path)
            
            item.setText(self.title_text_index+1, str(size))
            item.setText(self.title_text_index+2, str(date))
        
        if sub_files:
            
            self._delete_children(item)
            
            exclude_extensions = self._define_exclude_extensions()
            exclude_count = 0
        
            if exclude_extensions:
                for file in sub_files:
                    for exclude in exclude_extensions:
                        if file.endswith(exclude):
                            exclude_count += 1
                            break
            
            if exclude_count != len(sub_files):
                
                qt.QTreeWidgetItem(item)
        
        if not parent == False:
            
            if not parent:
                self.addTopLevelItem(item)
            if parent:
                parent.addChild(item)
            
            self.setCurrentItem(item)
            
        return item
    
    def _add_sub_items(self, item):
        
        self.delete_empty_children(item)
        self._delete_children(item)
                
        path_string = self.get_item_path_string(item)
        
        path = util_file.join_path(self.directory, path_string)
        
        files = self._get_files(path)
        
        self._add_items(files, item)
        
            
    def create_branch(self, name = None):
        
        current_item = self.current_item
        
        if current_item:
            path = self.get_item_path_string(self.current_item)
            path = util_file.join_path(self.directory, path)
            
            if util_file.is_file(path):
                path = util_file.get_dirname(path)
                current_item = self.current_item.parent()
            
        if not current_item:
            path = self.directory
                
        if not name:
            name = self._define_new_branch_name()
            
        util_file.create_dir(name, path)
        
        
        if current_item:
            self._add_sub_items(current_item)
            self.setItemExpanded(current_item, True)
            
        if not current_item:
            self.refresh()
            
    def delete_branch(self):
        item = self.current_item
        path = self.get_item_directory(item)
        
        name = util_file.get_basename(path)
        directory = util_file.get_dirname(path)
        
        if util_file.is_dir(path):
            util_file.delete_dir(name, directory)
        if util_file.is_file(path):
            util_file.delete_file(name, directory)
            if path.endswith('.py'):
                util_file.delete_file((name+'c'), directory)
        
        index = self.indexOfTopLevelItem(item)
        
        parent = item.parent()
        if parent:
            parent.removeChild(item)
        if not parent:
            self.takeTopLevelItem(index)

    def refresh(self):
        
        files = self._get_files()
        
        if not files:
            self.clear()
            return
        
        self._load_files(files)
        
        self.refreshed.emit()
        

    def get_item_directory(self, item):
        
        path_string = self.get_item_path_string(item)
        
        return util_file.join_path(self.directory, path_string)

    def set_directory(self, directory, refresh = True):
        
        
        
        self.directory = directory
        
        if refresh:
            
            self.refresh()
        
class EditFileTreeWidget(DirectoryWidget):
    
    description = 'EditTree'
    
    item_clicked = create_signal(object, object)
    
    
    def __init__(self, parent = None):        
        
        self.tree_widget = None
        
        
        
        super(EditFileTreeWidget, self).__init__(parent)
        
        self.setSizePolicy(qt.QSizePolicy.Minimum, qt.QSizePolicy.Minimum) 
        
    def _define_tree_widget(self):
        return FileTreeWidget()
    
    def _define_manager_widget(self):
        return ManageTreeWidget()
    
    def _define_filter_widget(self):
        return FilterTreeWidget()
        
    def _build_widgets(self):
        
        
        self.tree_widget = self._define_tree_widget()   
        
        self.tree_widget.itemClicked.connect(self._item_selection_changed)
        
          
        self.manager_widget = self._define_manager_widget()
        self.manager_widget.set_tree_widget(self.tree_widget)
        
        self.filter_widget = self._define_filter_widget()
        
        self.filter_widget.set_tree_widget(self.tree_widget)
        self.filter_widget.set_directory(self.directory)
        
        
        self.main_layout.addWidget(self.tree_widget)
        self.main_layout.addWidget(self.filter_widget)
               
        
        self.main_layout.addWidget(self.manager_widget)
        
        
    """
    def _item_clicked(self, item, column):
        
        if not item:
            name = ''
        
        if item:
            name = item.text(column)
        
        self.item_clicked.emit(name, item)
    """
        
    def _item_selection_changed(self):
               
        items = self.tree_widget.selectedItems()
        
        name = None
        item = None
        
        if items:
            item = items[0]
            name = item.text(0)
        
            self.item_clicked.emit(name, item)
            
        return name, item

    def get_current_item(self):
        return self.tree_widget.current_item
    
    def get_current_item_name(self):
        return self.tree_widget.current_name
    
    def get_current_item_directory(self):
        item = self.get_current_item()
        return self.tree_widget.get_item_directory(item)

    def refresh(self):
        self.tree_widget.refresh()
    
    def set_directory(self, directory, sub = False):
        super(EditFileTreeWidget, self).set_directory(directory)
        
        if not sub:
            self.directory = directory
            
        self.tree_widget.set_directory(directory)
        self.filter_widget.set_directory(directory)
        
        if hasattr(self.manager_widget, 'set_directory'):
            self.manager_widget.set_directory(directory)
       
class ManageTreeWidget(BasicWidget):
        
    def __init__(self):
        
        self.tree_widget = None
        
        super(ManageTreeWidget,self).__init__()
    
    def set_tree_widget(self, tree_widget):
        self.tree_widget = tree_widget
       
class FilterTreeWidget( DirectoryWidget ):
    
    def __init__(self):
        
        self.tree_widget = None
        
        super(FilterTreeWidget, self).__init__()
    
    def _define_main_layout(self):
        return qt.QHBoxLayout()
    
    def _build_widgets(self): 
        self.filter_names = qt.QLineEdit()
        self.filter_names.setPlaceholderText('filter names')
        self.sub_path_filter = qt.QLineEdit()
        self.sub_path_filter.setPlaceholderText('set sub path')
        self.sub_path_filter.textChanged.connect(self._sub_path_filter_changed)
        
        self.filter_names.textChanged.connect(self._filter_names)
                
        self.main_layout.addWidget(self.filter_names)
        self.main_layout.addWidget(self.sub_path_filter)
        
    def _filter_names(self, text):
        
        self.tree_widget.filter_names(text)
        self.skip_name_filter = False
        
    def _sub_path_filter_changed(self):
        current_text = str( self.sub_path_filter.text() )
        current_text = current_text.strip()
        
        if not current_text:
            self.set_directory(self.directory)
            self.tree_widget.set_directory(self.directory)
            
            text = self.filter_names.text()
            self._filter_names(text)    
            
            return
            
        sub_dir = util_file.join_path(self.directory, current_text)
        if not sub_dir:
            
            return
        
        if util_file.is_dir(sub_dir):
            self.tree_widget.set_directory(sub_dir)
            
            text = self.filter_names.text()
            self._filter_names(text)    
                    
    def clear_sub_path_filter(self):
        self.sub_path_filter.setText('')
            
    def set_tree_widget(self, tree_widget):
        self.tree_widget = tree_widget
        
    
        
class FileManagerWidget(DirectoryWidget):
    
    def __init__(self, parent = None):
        super(FileManagerWidget, self).__init__(parent)
        
        save_tip = self._define_io_tip()
        if save_tip:
            self.save_widget.set_io_tip(save_tip)
        
        self.data_class = self._define_data_class()
        
        self.history_attached = False
        
    def _define_io_tip(self):
        return ''
        
    def _define_main_layout(self):
        return qt.QHBoxLayout()
        
    def _define_data_class(self):
        return
    
    def _define_main_tab_name(self):
        return 'Data File'
    
    def _build_widgets(self):
        
        self.tab_widget = qt.QTabWidget()
        
        self.main_tab_name = self._define_main_tab_name()
        self.version_tab_name = 'Version'
                
        self.save_widget = self._define_save_widget()
        
        self.save_widget.file_changed.connect(self._file_changed)
                
        self.tab_widget.addTab(self.save_widget, self.main_tab_name)
        self._add_history_widget()
        
        self._add_option_widget()
            
        self.tab_widget.currentChanged.connect(self._tab_changed)    
        self.main_layout.addWidget(self.tab_widget)
        
        self.setSizePolicy(qt.QSizePolicy.MinimumExpanding, qt.QSizePolicy.MinimumExpanding)

    def _add_history_widget(self):
        self.history_buffer_widget = BasicWidget()
        
        self.history_widget = self._define_history_widget()
        self.history_widget.file_changed.connect(self._file_changed)
        
        self.tab_widget.addTab(self.history_buffer_widget, self.version_tab_name)
        
        self.history_widget.hide()
        
    def _add_option_widget(self):
        
        self.option_widget = self._define_option_widget()
        
        if not self.option_widget:
            return
        
        self.option_buffer_widget = BasicWidget()
        
        self.tab_widget.addTab(self.option_buffer_widget, 'Options')
        
    def _define_save_widget(self):
        return SaveFileWidget()
        
    def _define_history_widget(self):
        return HistoryFileWidget()
        
    def _define_option_widget(self):
        return
        
    def _hide_history(self):
        
        self.history_widget.hide()
        
        if self.history_attached:
            self.history_buffer_widget.main_layout.removeWidget(self.history_widget)
                
        self.history_attached = False
    
    def _show_history(self):
        self.update_history()
    
    def _hide_options(self):
        if self.option_widget:
            self.option_buffer_widget.main_layout.removeWidget(self.option_widget)
    
    def _show_options(self):
        if self.option_widget:
            self.option_buffer_widget.main_layout.addWidget(self.option_widget)
            self.option_widget.set_directory(self.directory)
            self.option_widget.data_class = self.data_class
            
        self.option_widget.tab_update()
        
    def _tab_changed(self):
                                
        if self.tab_widget.currentIndex() == 0:
            
            self.save_widget.set_directory(self.directory)
            
            self._hide_history()
            self._hide_options()
            
        if self.tab_widget.currentIndex() == 1:
            
            self._hide_options()
            self._show_history()
                
        if self.tab_widget.currentIndex() == 2:
            
            self._show_options()
            self._hide_history()
                        
    def _file_changed(self):
        
        if not util_file.is_dir(self.directory):     
            return
        
        self._activate_history_tab()
        
    def _activate_history_tab(self):
        
        if not self.directory:
            return
        
        version_tool = util_file.VersionFile(self.directory)   
         
        has_versions = version_tool.has_versions()
        
        if has_versions:
            self.tab_widget.setTabEnabled(1, True)
        if not has_versions:
            self.tab_widget.setTabEnabled(1, False) 
        
    def add_option_widget(self):
        self._add_option_widget()
        
    def update_history(self):
        self.history_buffer_widget.main_layout.addWidget(self.history_widget)
            
        self.history_widget.show()
        self.history_widget.set_directory(self.directory)
        self.history_widget.refresh()
        self.history_attached = True
        
        self._activate_history_tab()
            
    def set_directory(self, directory):
        super(FileManagerWidget, self).set_directory(directory)
        
        if self.data_class:
            self.data_class.set_directory(directory)
        
        if self.tab_widget.currentIndex() == 0:
            self.save_widget.set_directory(directory)
            self.save_widget.data_class = self.data_class
        
        if self.tab_widget.currentIndex() == 1:
            self.history_widget.set_directory(directory)
            self.history_widget.data_class = self.data_class
            
        if self.tab_widget.currentIndex() == 2:
            self.option_widget.set_directory(directory)
            self.option_widget.data_class = self.data_class
        
        
            
        self._file_changed()
        
        
class SaveFileWidget(DirectoryWidget):
    
    file_changed = create_signal()
    
    def __init__(self, parent = None):
        
        self.tip = self._define_tip()
        
        super(SaveFileWidget, self).__init__(parent)
        
        if self.tip:
            self._create_io_tip()
        
        self.data_class = None
        
        
    def _define_tip(self):
        
        return ''
        
    def _define_main_layout(self):
        return qt.QHBoxLayout()
        
    def _build_widgets(self):
        
        
        
        self.save_button = qt.QPushButton('Save')
        self.load_button = qt.QPushButton('Open')
        
        self.save_button.setMaximumWidth(100)
        self.load_button.setMaximumWidth(100)
        self.save_button.setMinimumWidth(70)
        self.load_button.setMinimumWidth(70)
        
        self.save_button.setSizePolicy(qt.QSizePolicy.Minimum, qt.QSizePolicy.Fixed)
        self.load_button.setSizePolicy(qt.QSizePolicy.Minimum, qt.QSizePolicy.Fixed)
        

        self.save_button.clicked.connect(self._save)
        self.load_button.clicked.connect(self._open)
        
        self.main_layout.addWidget(self.load_button)
        self.main_layout.addWidget(self.save_button)
        
        
        self.main_layout.setAlignment(qt.QtCore.Qt.AlignTop)

    def _save(self):
        
        self.file_changed.emit()
    
    def _open(self):
        pass

    def _create_io_tip(self):
        self.setToolTip(self.tip)
        """
        self.tip_widget = QLineEdit()
        self.tip_widget.setText(self.tip)
        self.tip_widget.setReadOnly(True)
        self.main_layout.insertWidget(0, self.tip_widget)
        """
    def set_io_tip(self, value):
        self.tip = value
        
        if self.tip:
            self._create_io_tip()

    

    def set_data_class(self, data_class_instance):
        self.data_class = data_class_instance
        
        if self.directory:
            self.data_class.set_directory(self.directory)
    
    def set_directory(self, directory):
        super(SaveFileWidget, self).set_directory(directory)
        
        if self.data_class:
            self.data_class.set_directory(self.directory)
            
    def set_no_save(self):
        self.save_button.setDisabled(True)
    
class HistoryTreeWidget(FileTreeWidget):
    

    def __init__(self):
        super(HistoryTreeWidget, self).__init__()
        
        if is_pyside() or is_pyside2():
            self.sortByColumn(0, qt.QtCore.Qt.SortOrder.DescendingOrder)
        
        self.setColumnWidth(0, 70)  
        self.setColumnWidth(1, 150)
        self.setColumnWidth(2, 50)
        self.setColumnWidth(3, 50)
        
        self.padding = 1
    
    def _item_activated(self, item):
        return
        
    def _define_header(self):
        return ['version','comment','size','user','date']
    
    def _get_files(self):

        if self.directory:
            
            version_tool = util_file.VersionFile(self.directory)
            
            version_data = version_tool.get_organized_version_data()
            
            if not version_data:
                return []
            
            if version_data:
                self.padding = len(str(len(version_data)))
                return version_data
    
    def _add_items(self, version_list):
        
        if not version_list:
            self.clear()
        
        for version_data in version_list:
            self._add_item(version_data)
    
    def _add_item(self, version_data):
        
        version, comment, user, file_size, file_date, version_file = version_data
        version_str = str(version).zfill(self.padding)
        
        item = qt.QTreeWidgetItem()
        item.setText(0, version_str)
        item.setText(1, comment)
        item.setText(2, str(file_size))
        item.setText(3, user)
        item.setText(4, file_date)
        
        self.addTopLevelItem(item)
        item.filepath = version_file

class HistoryFileWidget(DirectoryWidget):
    
    file_changed = create_signal()
    
    def _define_main_layout(self):
        return qt.QVBoxLayout()
    
    def _define_list(self):
        return HistoryTreeWidget()
    
    def _build_widgets(self):
        
        self.setSizePolicy(qt.QSizePolicy.MinimumExpanding,
                           qt.QSizePolicy.MinimumExpanding)
        
        self.button_layout = qt.QHBoxLayout()
        
        open_button = qt.QPushButton('Open')
        open_button.clicked.connect(self._open_version)
        
        open_button.setMaximumWidth(100)
                
        self.button_layout.addWidget(open_button)
        
        self.version_list = self._define_list()
        
        self.main_layout.addWidget(self.version_list)
        self.main_layout.addLayout(self.button_layout)

    def _open_version(self):
        pass
            
    def refresh(self):
        self.version_list.refresh()
                
    def set_data_class(self, data_class_instance):
        self.data_class = data_class_instance
        
        if self.directory:
            self.data_class.set_directory(self.directory)
        
    def set_directory(self, directory):
        
        super(HistoryFileWidget, self).set_directory(directory)
        
        if self.isVisible():
            self.version_list.set_directory(directory, refresh = True)
        if not self.isVisible():    
            self.version_list.set_directory(directory, refresh = False)

class OptionFileWidget(DirectoryWidget):
    
    def __init__(self, parent = None):
        super(OptionFileWidget, self).__init__(parent)
        
        self.data_class = None
        
    def set_data_class(self, data_class_instance):
        self.data_class = data_class_instance
        
        if self.directory:
            self.data_class.set_directory(self.directory)
    
    def set_directory(self, directory):
        super(OptionFileWidget, self).set_directory(directory)
        
        if self.data_class:
            self.data_class.set_directory(self.directory)
            
    def tab_update(self):
        return
            
class GetString(BasicWidget):
    
    text_changed = create_signal(object)
    
    def __init__(self, name, parent = None):
        self.name = name
        super(GetString, self).__init__(parent)
        
        self._use_button = False
    
    def _define_main_layout(self):
        return qt.QHBoxLayout()
            
    def _build_widgets(self):
        
        self.main_layout.setContentsMargins(0,0,0,0)
        self.main_layout.setSpacing(0)
        
        self.text_entry = qt.QLineEdit()
        
        
        self.label = qt.QLabel(self.name)
        self.label.setAlignment(qt.QtCore.Qt.AlignLeft)
        self.label.setMinimumWidth(100)
        self._setup_text_widget()
        
        self.main_layout.addWidget(self.label)
        self.main_layout.addSpacing(5)
        self.main_layout.addWidget(self.text_entry)
        
        
        insert_button = qt.QPushButton('<')
        insert_button.setMaximumWidth(20)
        insert_button.clicked.connect(self._button_command)
        self.main_layout.addWidget(insert_button)
        insert_button.hide()
        
        self.button = insert_button
        
    def _setup_text_widget(self):
        self.text_entry.textChanged.connect(self._text_changed)
                    
    def _text_changed(self):
        self.text_changed.emit(self.text_entry.text())
        
    def _button_command(self):
        if util.is_in_maya():
            import maya.cmds as cmds
            
            selection = cmds.ls(sl = True)
            
            if len(selection) > 1:
                selection = self._remove_unicode(selection)
                selection = str(selection)
            
            if len(selection) == 1:
                selection = str(selection[0])
                
            self.set_text(selection)
            
    def _remove_unicode(self, list_or_tuple):
            new_list = []
            for sub in list_or_tuple:
                new_list.append(str(sub))
                
            return new_list
        
    def set_text(self, text):
        self.text_entry.setText(text)
        
    def set_placeholder(self, text):
        self.text_entry.setPlaceholderText(text)
        
    def get_text(self):
        return self.text_entry.text()
        
    def set_label(self, label):
        self.label.setText(label)  
        
    def get_label(self):
        return self.label.text()
        
    def set_password_mode(self, bool_value):
        
        if bool_value:
            self.text_entry.setEchoMode(self.text_entry.Password)
        if not bool_value:
            self.text_entry.setEchoMode(self.text_entry.Normal) 
    
    def set_use_button(self, bool_value):
        
        if bool_value:
            self.button.show()
        else:
            self.button.hide()
        
    def get_text_as_list(self):
        
        text = self.text_entry.text()
        
        text = str(text)
        
        if text.find('[') > -1:
            try:
                text = eval(text)
                return text
            except:
                pass
        
        if text:
            return [text]
    
class GetDirectoryWidget(DirectoryWidget):
    
    directory_changed = create_signal(object)
    
    def __init__(self, parent = None):
        super(GetDirectoryWidget, self).__init__(parent)
        
        self.label = 'directory'
    
    def _define_main_layout(self):
        return qt.QHBoxLayout()
    
    def _build_widgets(self):
        
        self.directory_label = qt.QLabel('directory')
        self.directory_label.setMinimumWidth(100)
        self.directory_label.setMaximumWidth(100)
        
        self.directory_edit = qt.QLineEdit()
        self.directory_edit.textChanged.connect(self._text_changed)
        directory_browse = qt.QPushButton('browse')
        
        directory_browse.clicked.connect(self._browser)
        
        self.main_layout.addWidget(self.directory_label)
        self.main_layout.addWidget(self.directory_edit)
        self.main_layout.addWidget(directory_browse)
        
    def _browser(self):
        
        filename = get_folder(self.get_directory() , self)
        
        filename = util_file.fix_slashes(filename)
        
        if filename and util_file.is_dir(filename):
            self.directory_edit.setText(filename)
            self.directory_changed.emit(filename)
        
    def _text_changed(self):
        
        directory = self.get_directory()
        
        if util_file.is_dir(directory):
            self.directory_changed.emit(directory)
        
    def set_label(self, label):
        self.directory_label.setText(label)
        
    def set_directory(self, directory):
        super(GetDirectoryWidget, self).set_directory(directory)
        
        self.directory_edit.setText(directory)
        
    def set_directory_text(self, text):
        
        self.directory_edit.setText(text)
        
    def get_directory(self):
        return self.directory_edit.text()
     
class GetNumberBase(BasicWidget):
    
    valueChanged = create_signal(object)
    
    def __init__(self, name, parent = None):
        self.name = name
        super(GetNumberBase, self).__init__(parent)
    
    def _define_main_layout(self):
        return qt.QHBoxLayout()
    
    def _define_number_widget(self):
        return
    
    def _build_widgets(self):
        
        self.main_layout.setContentsMargins(0,0,0,0)
        self.main_layout.setSpacing(0)
        
        self.number_widget = self._define_number_widget()
        self.number_widget.setMaximumWidth(100)
        
        self.label = qt.QLabel(self.name)
        self.label.setAlignment(qt.QtCore.Qt.AlignRight)
        
        self.value_label = qt.QLabel('value')
        self.value_label.hide()
        
        self.main_layout.addWidget(self.label)
        self.main_layout.addSpacing(5)
        self.main_layout.addWidget(self.value_label, alignment = qt.QtCore.Qt.AlignRight)
        self.main_layout.addWidget(self.number_widget)
                    
    def _value_changed(self):
        self.valueChanged.emit(self.get_value())
        
    def set_value(self, value):
        self.number_widget.setValue(value)
        
    def get_value(self):
        return self.number_widget.value()
        
    def set_value_label(self, text):
        self.value_label.show()
        return self.value_label.setText(text)
        
    def set_label(self, label):
        self.label.setText(label)
        
    def get_label(self):
        
        return self.label.text()
    
    
class GetNumber(GetNumberBase):
    
    valueChanged = create_signal(object)
    enter_pressed = create_signal()
    
    def __init__(self, name, parent = None):
        super(GetNumber, self).__init__(name, parent)
        
        self._setup_spin_widget()
    
    def _define_main_layout(self):
        return qt.QHBoxLayout()
    
    def _define_number_widget(self):
        return qt.QDoubleSpinBox()
        
    def _setup_spin_widget(self):
        
        if hasattr(self.number_widget, 'CorrectToNearestValue'):
            self.number_widget.setCorrectionMode(self.number_widget.CorrectToNearestValue)
            
        if hasattr(self.number_widget, 'setWrapping'):
            self.number_widget.setWrapping(False)
        
        if hasattr(self.number_widget, 'setDecimals'):    
            self.number_widget.setDecimals(3)
            
        self.number_widget.setMaximum(100000000)
        self.number_widget.setMinimum(-100000000)
        self.number_widget.setButtonSymbols(self.number_widget.NoButtons)
        
        self.number_widget.valueChanged.connect(self._value_changed)
        
    def keyPressEvent(self, event):
        
        if event.key() == qt.QtCore.Qt.Key_Return:
            self.enter_pressed.emit()
            
        if event.key() == qt.QtCore.Qt.Key_Enter:
            self.enter_pressed.emit()
        
    
class GetInteger(GetNumber):
    
    def _define_number_widget(self):
        return qt.QSpinBox()
    
class GetBoolean(GetNumberBase):
    
    def __init__(self, name, parent = None):
        super(GetBoolean, self).__init__(name, parent)
        
        self.number_widget.stateChanged.connect(self._value_changed)
    
    def _value_changed(self):
        self.valueChanged.emit(self.get_value())
        
    
    def _define_number_widget(self):
        return qt.QCheckBox()
    
    def set_value(self, value):
        
        if value:
            state = qt.QtCore.Qt.CheckState.Checked
        if not value:
            state = qt.QtCore.Qt.CheckState.Unchecked
        self.number_widget.setCheckState(state)
        
        
    def get_value(self):
        
        value = self.number_widget.isChecked()
        
        if value == None:
            value = False
        
        return value
             
class GetNumberButton(GetNumber):
    
    clicked = create_signal(object)
    
    def _build_widgets(self):   
        super(GetNumberButton, self)._build_widgets()
        
        self.button = qt.QPushButton('run')
        self.button.clicked.connect(self._clicked)
        self.button.setMaximumWidth(60)
        
        self.main_layout.addWidget(self.button)
        
    def _clicked(self):
        self.clicked.emit(self.number_widget.value())
        
class GetIntNumberButton(GetNumberButton):
    def _define_number_widget(self):
        number_widget = qt.QSpinBox()
        return number_widget
    
class GetCheckBox(BasicWidget):
    
    check_changed = create_signal(object)
    
    def __init__(self, name, parent = None):
        
        self.name = name
        
        super(GetCheckBox, self).__init__(parent)
        
        
        
    def _define_main_layout(self):
        return qt.QHBoxLayout()
            
    def _build_widgets(self):
        
        self.check_box = qt.QCheckBox()
        self.check_box.setText(self.name)
        self.main_layout.addWidget(self.check_box)
        
        self.check_box.stateChanged.connect(self._state_changed)
        
    def _state_changed(self, state):
        
        if state:
            self.check_changed.emit(True)
        if not state:
            self.check_changed.emit(False)
        
    def get_state(self):
        
        if self.check_box.isChecked():
            return True
        if not self.check_box.isChecked():
            return False
        
    def set_state(self, bool_value):
        if bool_value != None:
            self.check_box.setChecked(bool_value)
            
class Group(qt.QGroupBox):
    
    def __init__(self, name):
        super(Group, self).__init__()
        
        
        self.setTitle(name)
        
        layout = qt.QHBoxLayout()
        
        self._widget = qt.QWidget()
        
        manager_layout = qt.QVBoxLayout()
        manager_layout.setContentsMargins(10,10,10,10)
        manager_layout.setSpacing(2)
        manager_layout.setAlignment(qt.QtCore.Qt.AlignCenter)
        
        self._widget.setLayout(manager_layout)
        layout.addWidget(self._widget)
        
        self.main_layout = manager_layout
        
        self.setLayout(layout)
        
        self._build_widgets()
        

    def mousePressEvent(self, event):
        
        super(Group, self).mousePressEvent(event)
        
        if not event.button() == qt.QtCore.Qt.LeftButton:
            return
        
        #half = self.width()/2
        
        if event.y() < 15:
            
            if self._widget.isHidden():
                self._widget.setVisible(True)
            elif not self._widget.isHidden():
                self._widget.setVisible(False)
            
    def _build_widgets(self):
        
        pass
        
    def collapse_group(self):
        
        self._widget.setVisible(False)
        
    def expand_group(self):
        
        self.setFixedSize(QWIDGETSIZE_MAX, QWIDGETSIZE_MAX)
        self.setVisible(True)
        
    def set_title(self, titlename):
        
        self.setTitle(titlename)
        
class Slider(BasicWidget):
    
    value_changed = create_signal(object)
    
    def __init__(self, title = None, parent = None):
        
        self.title = title
        
        super(Slider, self).__init__(parent)
        
        self.emit_value_change = True
        self.last_value = None
        
        
    def _build_widgets(self):
        
        self.label = qt.QLabel()
        self.label.setText(self.title)
        self.slider = qt.QSlider()
        self.slider.setOrientation(qt.QtCore.Qt.Horizontal)
        
        self.slider.valueChanged.connect(self._value_change)
        
        self.main_layout.addWidget(self.label)
        self.main_layout.addWidget(self.slider)
        
    def set_title(self, title):
        
        self.label.setText(title)
        
        self.title = title
        
    def _value_change(self, value):
        
        if self.emit_value_change:
            self.value_changed.emit(value)
    
    def _reset_slider(self):
        
        self.emit_value_change = False
        self.slider.setValue(0)
        self.last_scale_value = None
        self.emit_value_change = True
    
    def set_auto_recenter(self, bool_value):
        
        if bool_value:
            
            self.slider.sliderReleased.connect(self._reset_slider)
            
        if not bool_value:
            self.slider.sliderReleased.disconnect(self._reset_slider)
        

       
class ProgressBar(qt.QProgressBar):
    
    def set_count(self, count):
        
        self.setMinimum(0)
        self.setMaximum(count)
        
    def set_increment(self, int_value):
        self.setValue(int_value)
        
class LoginWidget( BasicWidget ):
    
    login = create_signal(object, object)
    
    def _build_widgets(self):
        
        group_widget = qt.QGroupBox('Login')
        group_layout = qt.QVBoxLayout()
        group_widget.setLayout(group_layout)
        
        self.login_widget = GetString('User: ')
        self.password_widget = GetString('Password: ')
        self.password_widget.set_password_mode(True)
        
        self.login_state = qt.QLabel('Login failed.')
        self.login_state.hide()
        
        login_button = qt.QPushButton('Enter')

        login_button.clicked.connect( self._login )
        
        self.password_widget.text_entry.returnPressed.connect(self._login)

        group_layout.addWidget(self.login_widget)
        group_layout.addWidget(self.password_widget)
        group_layout.addWidget(login_button)
        group_layout.addWidget(self.login_state)

        self.main_layout.addWidget(group_widget)
        
        self.group_layout = group_layout

        
    def _login(self):
        
        login = self.login_widget.get_text()
                
        password = self.password_widget.get_text()
        
        self.login.emit(login, password)
        
    def set_login(self, text):
        self.login_widget.set_text(text)
        
    def set_login_failed(self, bool_value):
        if bool_value:
            self.login_state.show()
            
        if not bool_value:
            self.login_state.hide()
     
class WidgetToPicture(BasicDialog):
    
    def __init__(self):
        super(WidgetToPicture, self).__init__()
        
        self.last_path = ''
    
    def _build_widgets(self):
        
        #widget_button = qt.QPushButton('Get widget')
        #widget_button.clicked.connect(self._get_widget())
        
        self.setMinimumHeight(100)
        self.setMinimumWidth(100)
        self.setMouseTracking(True)
        #self.main_layout.addWidget()
        
    def mouseReleaseEvent(self, event):
        super(WidgetToPicture, self).mousePressEvent(event)
        
        position = event.globalPos()
        
        app = qt.qApp
        widget = app.widgetAt(position)
        
        self.take_picture(widget)
        
        
    def take_picture(self, widget):
        
        pixmap =  qt.QPixmap.grabWidget(widget)
        
        
        filename = qt.QFileDialog.getSaveFileName(self, "Save Image", filter = '*.png', dir = self.last_path)
        
        if filename:
            if util_file.is_file(filename[0]):
                name = util_file.get_basename(filename[0])
                directory = util_file.get_dirname(filename[0])
                util_file.delete_file(name, directory)
            pixmap.save(filename[0], 'png')
            
            self.last_path = filename[0]
        
#--- Code Editor
        
class CodeEditTabs_ActiveFilter(qt.QtCore.QObject):
    def eventFilter(self, obj, event):
        
        if event.type() == qt.QtCore.QEvent.WindowActivate:
            obj._tabs_activated()
            return True
            
        else:
            # standard event processing
            return qt.QtCore.QObject.eventFilter(self, obj, event)
        
class CodeEditTabs(BasicWidget):
    
    save = create_signal(object)
    tabChanged = create_signal(object)
    no_tabs = create_signal()
    multi_save = create_signal(object, object)
    completer =  None
    
    
    def __init__(self):
        super(CodeEditTabs, self).__init__()
        
        self.code_tab_map = {}
        self.code_floater_map = {}
        self.code_window_map = {}
        
        self.tabs.setMovable(True)
        self.tabs.setTabsClosable(True)
        
        self.tabs.tabCloseRequested.connect(self._close_tab)
        self.tabs.currentChanged.connect(self._tab_changed)
        
        self.previous_widget = None
        
        self.suppress_tab_close_save = False
        self.current_process = None
        
        self.find_widget = None
        
        
        self.installEventFilter(CodeEditTabs_ActiveFilter(self))
        
    def _find(self, text_edit):
        
        if not self.find_widget:
            find_widget = FindTextWidget(text_edit)
            find_widget.closed.connect(self._clear_find)
            find_widget.show()
            
        
            self.find_widget = find_widget
            
    def _clear_find(self):
        
        self.find_widget = None
            
    def _set_tab_find_widget(self, current_widget):

        if not current_widget:
            if self.find_widget:
                self.find_widget.close()
                self.find_widget = None
                
        if self.find_widget:
            self.find_widget.set_widget(current_widget.text_edit)
            
    def _tab_changed(self):
        
        current_widget = self.tabs.currentWidget()
        
        self._set_tab_find_widget(current_widget)
        
        self.tabChanged.emit(current_widget)

    def _code_window_activated(self, widget):
        
        if self.find_widget:
            self.find_widget.set_widget(widget.code_edit.text_edit)
            
    def _tabs_activated(self):
        
        current_tab = self.tabs.currentWidget()
        
        self._set_tab_find_widget(current_tab)
        
    def _code_window_deactivated(self):
        
        current_widget = self.tabs.currentWidget()

        self._set_tab_find_widget(current_widget)
        
    
    def _close_tab(self, index):
        
        if not self.suppress_tab_close_save:
                    
            widget = self.tabs.widget(index)
            
            #there would be no widget if changing processes
            if widget:
                if widget.text_edit.document().isModified():
                    permission = get_permission('Unsaved changes. Save?', self)
                    if permission == True:
                        self.multi_save.emit(widget.text_edit, None)
                    if permission == None:
                        return
        
        title = self.tabs.tabText(index)
        
        if not self.tabs.count() > index:
            return
        
        
        
        widget = self.tabs.widget(index)
        widget.hide()
        widget.close()
        widget.deleteLater()
        self.tabs.removeTab(index)
                
        if self.code_tab_map.has_key(str(title)):
            self.code_tab_map.pop(str(title))

        if self.tabs.count() == 0:
            self.no_tabs.emit()
    
    def _save(self, current_widget):
        
        title = current_widget.titlename
        
        filepath = current_widget.filepath
        
        if hasattr(current_widget, 'text_edit'):
            current_widget = current_widget.text_edit
        
        self.save.emit(current_widget)
        
        if self.code_floater_map.has_key(title):
            floater_widget = self.code_floater_map[title]
            
            if floater_widget.filepath == filepath:
                floater_widget.set_no_changes()
            
        if self.code_tab_map.has_key(title):
            tab_widget = self.code_tab_map[title]
            
            if tab_widget.filepath == filepath:
                tab_widget.set_no_changes()
    
    def _build_widgets(self):
        
        self.tabs = CodeTabs()
        
        self.main_layout.addWidget(self.tabs)
        
        self.tabs.double_click.connect(self._tab_double_click)
        
    def _tab_double_click(self, index):
        
        title = str(self.tabs.tabText(index))
        code_widget = self.code_tab_map[title]
        filepath = code_widget.text_edit.filepath
        
        #if util.get_maya_version() > 2016:
            #there is a bug in maya 2017 and on that would crash maya when closing the tab.
            #this avoids the crash but leaves the tab open...
            #util.warning('Could not open floating code window %s in Maya 2017 and 2018... hopefully this can be fixed in the future.' % title)
            #return
        
        self.add_floating_tab(filepath, title)
        
    def _window_close_requested(self, widget):
        
        self.multi_save.emit(widget.code_edit.text_edit, None)
        
    def clear(self):
        self.tabs.clear()
        
        self.code_tab_map = {}
        
    def goto_tab(self, name):
        widget = None
        if self.code_tab_map.has_key(name):
            
            widget = self.code_tab_map[name]
                
            self.tabs.setCurrentWidget(widget)
            widget.text_edit.setFocus()
        
        return widget
        
    def goto_floating_tab(self, name):
        
        widget = None
        if self.code_floater_map.has_key(name):
            
            widget = self.code_floater_map[name]
            widget.show()
            widget.activateWindow()
            widget.raise_()
            widget.text_edit.setFocus()
        
        return widget
        
    def add_floating_tab(self, filepath, name):
        
        basename = name
        
        if self.code_tab_map.has_key(basename):
            code_widget = self.code_tab_map[basename]
            index = self.tabs.indexOf(code_widget)
        
            if index > -1:
                self.suppress_tab_close_save = True
                self._close_tab(index)
                self.suppress_tab_close_save = False
        
        if self.code_tab_map.has_key(basename):
            #do something
            return
        
        code_edit_widget = CodeEdit()
        if self.__class__.completer:
            code_edit_widget.set_completer(self.__class__.completer)
        
        code_edit_widget.filepath = filepath

        code_edit_widget.add_menu_bar()
        
        if self.current_process:
            code_edit_widget.add_process_title(self.current_process)
            
        code_edit_widget.set_file(filepath)
        
        code_widget = code_edit_widget.text_edit
        code_widget.titlename = basename
        code_widget.set_file(filepath)
        code_widget.save.connect(self._save)
        code_widget.find_opened.connect(self._find)
        
        window = CodeTabWindow(self)
        window.resize(600, 800)
        #basename = util_file.get_basename(filepath)
        
        window.setWindowTitle(basename)
        window.set_code_edit(code_edit_widget)
        window.closed_save.connect(self._window_close_requested)
        window.closed.connect(self._close_window)
        
        window.activated.connect(self._code_window_activated)
        
        self.code_floater_map[basename] = code_edit_widget
        self.code_window_map[filepath] = window
        
        window.show()
        window.setFocus()
        
        if self.code_tab_map.has_key(basename):
            tab_widget = self.code_tab_map[basename]
            
            if tab_widget:
                code_widget.setDocument(tab_widget.text_edit.document())
            
        return code_edit_widget
        
        
        
    def add_tab(self, filepath, name):
        
        basename = name
        
        if self.code_tab_map.has_key(basename):
            self.goto_tab(basename)
            return
                
        code_edit_widget = CodeEdit()
        if self.__class__.completer:
            code_edit_widget.set_completer(self.__class__.completer)
        code_edit_widget.filepath = filepath
        
        self.tabs.addTab(code_edit_widget, basename)
        
        code_widget = code_edit_widget.text_edit
        code_widget.set_file(filepath)
        code_widget.titlename = basename
        
        code_widget.save.connect(self._save)
        code_widget.find_opened.connect(self._find)
        
        self.code_tab_map[basename] = code_edit_widget
        
        self.goto_tab(basename)
        
        if self.code_floater_map.has_key(basename):
            float_widget = self.code_floater_map[basename]
            
            if float_widget:
                if filepath == float_widget.filepath:
                    
                    code_widget.setDocument(float_widget.text_edit.document())
        
        return code_edit_widget
            
    def save_tabs(self, note = None):
        
        found = []
        
        for inc in range(0, self.tabs.count()):
            widget = self.tabs.widget(inc)
            
            if widget.text_edit.document().isModified():
                found.append(widget.text_edit)
        
        self.multi_save.emit(found, note)
      
    def has_tabs(self):
        
        if self.tabs.count():
            return True
        
        return False
    
    def get_widgets(self, name = None):
        
        widgets = []
        
        for key in self.code_tab_map:
            
            if name != None:
                if key != name:
                    continue
            
            widget = self.code_tab_map[key]
            if widget:
                widgets.append(widget)
    
        for key in self.code_floater_map:
            
            if name != None:
                if key != name:
                    
                    continue
            
            widget = self.code_floater_map[key]
            if widget:
                widgets.append(widget)
                
        return widgets
            
    def set_tab_title(self, index, name):
        
        self.tabs.setTabText(index, name)
        
    def set_completer(self, completer_class):
        
        self.__class__.completer = completer_class
        
        
    def rename_tab(self, old_path, new_path, old_name, new_name):
        
        if old_path == new_path:
            return
        
        widgets = self.get_widgets(old_name)
        
        if not widgets:
            return
        
        removed_old_tab = False
        
        for widget in widgets:
            
            index = self.tabs.indexOf(widget)
            
            if index > -1:
                
                self.set_tab_title(index, new_name)
                
                self.code_tab_map[new_name] = widget
                if self.code_tab_map.has_key(old_name):
                    self.code_tab_map.pop(old_name)
                    removed_old_tab = True
                widget.text_edit.filepath = new_path
                widget.text_edit.titlename = new_name
                widget.filepath = new_path
                
                
            if index == -1 or index == None:
                
                parent = widget.parent()
                window_parent = parent.parent()

                window_parent.setWindowTitle(new_name)
                
                self.code_floater_map[new_name] = widget
                if self.code_floater_map.has_key(old_name):
                    self.code_floater_map.pop(old_name)
                    removed_old_tab = True
                widget.text_edit.filepath = new_path
                widget.text_edit.titlename = new_name
                widget.set_file(new_path)
                widget.filepath = new_path
                            
            current_widget = self.tabs.currentWidget()
            current_titlename = current_widget.text_edit.titlename
            
            if new_name == current_titlename:
                self.tabChanged.emit(widget)
                
                
        if not removed_old_tab:
            util.warning('Failed to remove old code widget entry: %s' % old_name)
              
    def close_tab(self, name):
        
        if not name:
            return
        
        widgets = self.get_widgets(name)
        
        for widget in widgets:
                        
            index = self.tabs.indexOf(widget)
            
            if index > -1:
                
                self.tabs.removeTab(index)
                if self.code_tab_map.has_key(name):
                    self.code_tab_map.pop(name)
            
            if index == -1 or index == None:
                
                parent = widget.parent()
                window_parent = parent.parent()
                window_parent.close()
                window_parent.deleteLater()
                
                if self.code_floater_map.has_key(name):
                    self.code_floater_map.pop(name)                            
                
    def _close_window(self, widget):
        name = widget.code_edit.text_edit.titlename
        
        if name in self.code_floater_map:
            self.code_floater_map.pop(name)
        
                
    def close_tabs(self):
        
        self.save_tabs()
        
        tab_count = self.tabs.count()
        
        for inc in range(0, tab_count):
            self._close_tab(inc)
            
    def close_windows(self):
        
        for key in self.code_floater_map:
            widget = self.code_floater_map[key]
            parent = widget.parent()
            window = parent.parent()
            window.close()
        
                
    def show_window(self, filepath):
        
        if not filepath:
            return
        
        if self.code_window_map.has_key(filepath):
            
            
            window = self.code_window_map[filepath]
            
            floater = self.code_floater_map[filepath]
            
            if floater.text_edit.filepath == filepath:
            
                window.hide()
                window.show()
                window.setFocus()
                     
class CodeTabs(qt.QTabWidget):
    
    double_click = create_signal(object)
    
    def __init__(self):
        super(CodeTabs, self).__init__()
        
        self.code_tab_bar = CodeTabBar()
        
        self.setTabBar( self.code_tab_bar )
        
        self.code_tab_bar.double_click.connect(self._bar_double_click)
    
    def _bar_double_click(self, index):
    
        self.double_click.emit(index)
        
class CodeTabBar(qt.QTabBar):
    
    double_click = create_signal(object)
    
    def __init__(self):
        super(CodeTabBar, self).__init__()
        self.setAcceptDrops(True)
    
    def mouseDoubleClickEvent(self, event):
        super(CodeTabBar, self).mouseDoubleClickEvent(event)
        
        index = self.currentIndex()
        
        self.double_click.emit(index)
        
class CodeTabWindow_ActiveFilter(qt.QtCore.QObject):
    def eventFilter(self, obj, event):
        
        if event.type() == qt.QtCore.QEvent.WindowActivate:
            
            obj.activated.emit(obj)
            return True
        
        else:
            # standard event processing
            return qt.QtCore.QObject.eventFilter(self, obj, event)
        
class CodeTabWindow(BasicWindow):
    
    closed_save = create_signal(object)
    closed = create_signal(object)
    activated = create_signal(object)
    
    def __init__(self, parent):
        super(CodeTabWindow, self).__init__(parent)
        
        self.installEventFilter(CodeTabWindow_ActiveFilter(self))
        #self.setWindowFlags(qt.QtCore.Qt.WindowStaysOnTopHint)
        
        self.code_edit = None
        
    def closeEvent(self, event):
        
        permission = False
        
        if self.code_edit:
            
            if self.code_edit.text_edit.document().isModified():
                permission = get_permission('Unsaved changes. Save?', self)
                
                if permission == None:
                    event.ignore()
                    return
        
        event.accept()
        if permission == True:
            self.closed_save.emit(self)
        if not permission:
            self.closed.emit(self)
            
    def set_code_edit(self, code_edit_widget):
        
        self.main_layout.addWidget(code_edit_widget)
        self.code_edit = code_edit_widget
        
class CodeEdit(BasicWidget):
    
    save_done = create_signal(object)
    
    def __init__(self):
        super(CodeEdit, self).__init__()
        
        self.text_edit.cursorPositionChanged.connect(self._cursor_changed)
        self.fullpath = None
        
    def _build_widgets(self):
        
        self.text_edit = CodeTextEdit()
        
        self.status_layout = qt.QHBoxLayout()
        
        self.line_number = qt.QLabel('Line:')
        self.save_state = qt.QLabel('No Changes')
        
        self.status_layout.addWidget(self.line_number)
        self.status_layout.addWidget(self.save_state)
        
        self.main_layout.addWidget(self.text_edit)
        self.main_layout.addLayout(self.status_layout)
        
        self.text_edit.save_done.connect(self._save_done)
        self.text_edit.textChanged.connect(self._text_changed)
        self.text_edit.file_set.connect(self._text_file_set)
        
        #completer on off... comment out to turn completer off.
        #self.text_edit.set_completer( PythonCompleter() )
        
    def _build_menu_bar(self):
        
        self.menu_bar = qt.QMenuBar()
        
        self.main_layout.insertWidget(0, self.menu_bar)
        
        file_menu = self.menu_bar.addMenu('File')
        
        save_action = file_menu.addAction('Save')
        
        browse_action = file_menu.addAction('Browse')
        
        save_action.triggered.connect(self.text_edit._save)
        browse_action.triggered.connect(self._open_browser)
        
    def _build_process_title(self, title):
        
        process_title = qt.QLabel('Process: %s' % title)
        self.main_layout.insertWidget(0, process_title)
        
    def _open_browser(self):
        
        filepath = self.text_edit.filepath
        
        filepath_only = util_file.get_dirname(filepath)
        
        util_file.open_browser(filepath_only)
        
    def _cursor_changed(self):
        
        code_widget = self.text_edit
        text_cursor = code_widget.textCursor()
        block_number = text_cursor.blockNumber()
        
        self.line_number.setText('Line: %s' % (block_number+1))
    
    def _text_changed(self):
        
        self.save_state.setText('Unsaved Changes')
    
    def _save_done(self, bool_value):
        
        if bool_value:
            self.save_state.setText('No Changes')
            self.save_done.emit(self)
            
    def _find(self, text_edit):
        
        if not self.find:
            self.find = FindTextWidget(text_edit)
            self.find.show()
            self.find.closed.connect(self._close_find)
            
    def _close_find(self):
        self.find = None
    
    def _text_file_set(self):
        self.save_state.setText('No Changes')
    
    def add_process_title(self, title):
        self._build_process_title(title)
        
    def add_menu_bar(self):
        
        self._build_menu_bar()
        
    def set_file(self, filepath):
        
        self.save_state.setText('No Changes')
        
    def set_no_changes(self):
        
        self.save_state.setText('No Changes')
        if self.text_edit:
            self.text_edit.document().setModified(False)
            
    def set_completer(self, completer_class):
        self.text_edit.set_completer(completer_class)
        
    def get_document(self):
        return self.text_edit.document()
    
    def set_document(self, document):
        modified = document.isModified()
        
        self.text_edit.setDocument(document)
        
        if not modified:
            self.save_state.setText('No Changes')
        
class ListAndHelp(qt.QListView):
    
    def __init__(self):
        super(ListAndHelp, self).__init__()
        
        layout = qt.QHBoxLayout()
        
        self.setLayout(layout)
        
        self.list = qt.QListView()
        
        button = qt.QTextEdit()
        
        layout.setContentsMargins(0,0,0,0)
        
        layout.addWidget(self.list)
        layout.addWidget(button)
        
class CodeTextEdit(qt.QPlainTextEdit):
    
    save = create_signal(object)
    save_done = create_signal(object)
    file_set = create_signal()
    find_opened = create_signal(object)
    
    def __init__(self):
        
        self.filepath = None
        
        super(CodeTextEdit, self).__init__()
        
        self.setFont( qt.QFont('Courier', 9)  )
        
        shortcut_save = qt.QShortcut(qt.QKeySequence(self.tr("Ctrl+s")), self)
        shortcut_save.activated.connect(self._save)
        
        shortcut_find = qt.QShortcut(qt.QKeySequence(self.tr('Ctrl+f')), self)
        shortcut_find.activated.connect(self._find)
        
        shortcut_goto_line = qt.QShortcut(qt.QKeySequence(self.tr('Ctrl+l')), self)
        shortcut_goto_line.activated.connect(self._goto_line)
        
        plus_seq = qt.QKeySequence( qt.QtCore.Qt.CTRL + qt.QtCore.Qt.Key_Plus)
        equal_seq = qt.QKeySequence( qt.QtCore.Qt.CTRL + qt.QtCore.Qt.Key_Equal)
        minus_seq = qt.QKeySequence( qt.QtCore.Qt.CTRL + qt.QtCore.Qt.Key_Minus)
        
        shortcut_zoom_in = qt.QShortcut(plus_seq, self)
        shortcut_zoom_in.activated.connect(self._zoom_in_text)
        shortcut_zoom_in_other = qt.QShortcut(equal_seq, self)
        shortcut_zoom_in_other.activated.connect(self._zoom_in_text)
        shortcut_zoom_out = qt.QShortcut(minus_seq, self)
        shortcut_zoom_out.activated.connect(self._zoom_out_text)
        
        self._setup_highlighter()
        
        self.setWordWrapMode(qt.QTextOption.NoWrap)
        
        self.last_modified = None
        
        self.skip_focus = False
        
        self.line_numbers = CodeLineNumber(self)
        
        self._update_number_width(0)
        
        self.blockCountChanged.connect(self._update_number_width)
        self.updateRequest.connect(self._update_number_area)
        self.cursorPositionChanged.connect(self._line_number_highlight)
        
        self._line_number_highlight()
        
        self.find_widget = None
        
        self.completer = None
        
        
    def _activate(self, value):
        pass
        
    def resizeEvent(self, event):
        
        super(CodeTextEdit, self).resizeEvent(event)
        
        rect = self.contentsRect()
        
        new_rect = qt.QtCore.QRect( rect.left(), rect.top(), self._line_number_width(), rect.height() )
        
        self.line_numbers.setGeometry( new_rect )   
    
    def wheelEvent(self, event):
        
        delta = event.delta()
        keys =  event.modifiers()
        
        if keys == qt.QtCore.Qt.CTRL:           
            if delta > 0:
                self._zoom_in_text()
            if delta < 0:
                self._zoom_out_text()
        
        return super(CodeTextEdit, self).wheelEvent(event)
    
    def focusInEvent(self, event):

        if self.completer:
            self.completer.setWidget(self)
        
        super(CodeTextEdit, self).focusInEvent(event)
        
        if not self.skip_focus:
            self._update_request()
            
    def keyPressEvent(self, event):
        
        if self.completer:
            self.completer.activated.connect(self._activate)
        
        if self.completer:
                        
            if self.completer.popup().isVisible():
                    
                if event.key() == qt.QtCore.Qt.Key_Enter:
                    event.ignore()
                    return
                if event.key() == qt.QtCore.Qt.Key_Return:
                    event.ignore()
                    return

        pass_on = True
        
        if event.key() == qt.QtCore.Qt.Key_Backtab or event.key() == qt.QtCore.Qt.Key_Tab:
            self._handle_tab(event)
            pass_on = False

        if event.key() == qt.QtCore.Qt.Key_Enter or event.key() == qt.QtCore.Qt.Key_Return:
            self._handle_enter(event)
            pass_on = False

        if pass_on:
            super(CodeTextEdit, self).keyPressEvent(event)
        
        if self.completer:
            text = self.completer.text_under_cursor()
            
            if text:
                
                result = self.completer.handle_text(text)
                
                if result == True:
                    
                    rect = self.cursorRect()
                    
                    width = self.completer.popup().sizeHintForColumn(0) + self.completer.popup().verticalScrollBar().sizeHint().width()
                    
                    if width > 350:
                        width = 350
                    
                    rect.setWidth(width)
                    
                    self.completer.complete(rect)
                
                if result == False:
                    
                    self.completer.popup().hide()
                    self.completer.clear_completer_list()
                    self.completer.refresh_completer = True

    def _line_number_paint(self, event):
        
        paint = qt.QPainter(self.line_numbers)
        
        if not util.is_in_maya():
            paint.fillRect(event.rect(), qt.QtCore.Qt.lightGray)
        
        if util.is_in_maya():
            paint.fillRect(event.rect(), qt.QtCore.Qt.black)
        
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        
        top = int( self.blockBoundingGeometry(block).translated(self.contentOffset()).top() )
        bottom = int( top + self.blockBoundingRect(block).height() )
        
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = block_number + 1
                
                if util.is_in_maya():
                    paint.setPen(qt.QtCore.Qt.lightGray)
                if not util.is_in_maya():
                    paint.setPen(qt.QtCore.Qt.black)
                
                paint.drawText(0, top, self.line_numbers.width(), self.fontMetrics().height(), qt.QtCore.Qt.AlignRight, str(number))
                
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            
            block_number += 1
        
    def _line_number_width(self):
        
        digits = 1
        max_value = max(1, self.blockCount())
        
        while (max_value >= 10):
            max_value /= 10
            digits+=1
        
        space = 1 + self.fontMetrics().width('1') * digits
        
        return space
    
    def _line_number_highlight(self):
        
        extra_selection = qt.QTextEdit.ExtraSelection()
        
        selections = [extra_selection]
        
        if not self.isReadOnly():
            selection = qt.QTextEdit.ExtraSelection()
            
            if util.is_in_maya():
                line_color = qt.QColor(qt.QtCore.Qt.black)
            if not util.is_in_maya():
                line_color = qt.QColor(qt.QtCore.Qt.lightGray)
                
            selection.format.setBackground(line_color)
            selection.format.setProperty(qt.QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            selections.append(selection)
            
        self.setExtraSelections(selections)
    
    def _update_number_width(self, value = 0):
        
        self.setViewportMargins(self._line_number_width(), 0,0,0)
        
    def _update_number_area(self, rect, y_value):
        
        if y_value:
            self.line_numbers.scroll(0, y_value)
        
        if not y_value:
            self.line_numbers.update(0, rect.y(), self.line_numbers.width(), rect.height())
            
        if rect.contains(self.viewport().rect()):
            self._update_number_width()
        
    def _save(self):
        
        if not self.document().isModified():
            util.warning('No changes to save in %s.' % self.filepath)
            return
        
        old_last_modified = self.last_modified
        
        try:
            self.save.emit(self)
        except:
            pass
        
        new_last_modified = util_file.get_last_modified_date(self.filepath)
        
        if old_last_modified == new_last_modified:
            self.save_done.emit(False)
            
        if old_last_modified != new_last_modified:
            self.save_done.emit(True)
            self.document().setModified(False)
            self.last_modified = new_last_modified
    
    def _find(self):
        
        self.find_opened.emit(self)
    
    def _goto_line(self):
        
        line = get_comment(self, '', 'Goto Line')
        
        if not line:
            return
        
        line_number = int(line)
        
        text_cursor = self.textCursor()
        
        block_number = text_cursor.blockNumber()
        
        number = line_number - block_number
        
        if number > 0:
            move_type = text_cursor.NextBlock
            number -= 2
        if number < 0:
            move_type = text_cursor.PreviousBlock
            number = abs(number)
        
        text_cursor.movePosition(move_type, text_cursor.MoveAnchor, (number+1))
        self.setTextCursor(text_cursor)
        
    def _zoom_in_text(self):
        font = self.font()
        
        size = font.pointSize()
        size += 1
        
        font.setPointSize( size )
        self.setFont( qt.QFont('Courier', size) )

    def _zoom_out_text(self):
        font = self.font()
                
        size = font.pointSize()
        size -= 1
        
        if size < 0:
            return
        
        font.setPointSize( size )
        self.setFont( qt.QFont('Courier', size) )
        
    def _has_changed(self):
        
        if self.filepath:
            if util_file.is_file(self.filepath):
                
                last_modified = util_file.get_last_modified_date(self.filepath)
                
                if last_modified != self.last_modified:
                    return True
                
        return False
        
    def _update_request(self):
                
        
        if not self._has_changed():
            return
        
        last_modified = util_file.get_last_modified_date(self.filepath)
                    
        self.skip_focus = True
        
        permission = get_permission('File:\n%s\nhas changed, reload?' % util_file.get_basename(self.filepath), self)
        
        if permission:
            self.set_file(self.filepath)
            
        if not permission:
            self.last_modified = last_modified
            
        self.skip_focus = False
             
    def _setup_highlighter(self):
        self.highlighter = PythonHighlighter(self.document())
    
    def _remove_tab(self,string_value):
        
        string_section = string_value[0:4]
        
        if string_section == '    ':
            return string_value[4:]
        
        return string_value
        
        
    def _add_tab(self,string_value):
    
        return '    %s' % string_value
    
    def _handle_enter(self, event):
        
        cursor = self.textCursor()
        current_block = cursor.block()
        
        cursor_position = cursor.positionInBlock()
                
        current_block_text = str(current_block.text())
        current_found = ''
        
        if not current_found:
            current_found = re.search('^ +', current_block_text)
            
            if current_found:
                current_found = current_found.group(0)
        
        indent = 0
        
        if current_found:
            indent = len(current_found)
        
        if cursor_position < indent:
            indent = (cursor_position - indent) + indent
        
        cursor.insertText(('\n' + ' ' * indent))
        
    def _handle_tab(self, event):
        
        cursor = self.textCursor()
        
        document = self.document()
        
        start_position = cursor.anchor()
        select_position = cursor.selectionStart()
        
        select_start_block = document.findBlock(select_position)
        
        start = select_position - select_start_block.position()
        
        #qt.QTextCursor.position()
        end_position = cursor.position()
        
        if start_position > end_position:
            
            temp_position = end_position
            
            end_position = start_position
            start_position = temp_position
        
        if event.key() == qt.QtCore.Qt.Key_Tab:
            
            if not cursor.hasSelection():
                
                self.insertPlainText('    ')
                start_position += 4
                end_position = start_position
            
            if cursor.hasSelection():
                
                cursor.setPosition(start_position)
                cursor.movePosition(qt.QTextCursor.StartOfLine)
                cursor.setPosition(end_position,qt.QTextCursor.KeepAnchor)
                
                text = cursor.selection()
                text = text.toPlainText()
                
                split_text = text.split('\n')
                
                edited = []
                
                inc = 0
                
                for text_split in split_text:
                        
                    edited.append( self._add_tab(text_split) )
                    if inc == 0:
                        start_position += 4
                        
                    end_position += 4
                    inc+=1
            
                edited_text = string.join(edited, '\n')
                cursor.insertText(edited_text)
                self.setTextCursor(cursor)
                
        if event.key() == qt.QtCore.Qt.Key_Backtab:
            
            
                
            
            if not cursor.hasSelection():
                
                cursor = self.textCursor()
                
                cursor.movePosition(qt.QTextCursor.StartOfLine)
                cursor.movePosition(qt.QTextCursor.Right, qt.QTextCursor.KeepAnchor, 4)
                
                text = cursor.selection()
                text = text.toPlainText()
                
                if text:
                    
                    
                    if text == '    ':
                        
                        cursor.insertText('')
                        self.setTextCursor(cursor)
                        start_position -= 4
                        end_position = start_position
            
            if cursor.hasSelection():
                
                cursor.setPosition(start_position)
                cursor.movePosition(qt.QTextCursor.StartOfLine)
                cursor.setPosition(end_position,qt.QTextCursor.KeepAnchor)
                cursor.movePosition(qt.QTextCursor.EndOfLine, qt.QTextCursor.KeepAnchor)
                self.setTextCursor(cursor)
                text = cursor.selection()
                text = str(text.toPlainText())
                
                split_text = text.split('\n')
                
                edited = []
                
                inc = 0
                skip_indent = False
                for text_split in split_text:
                    
                    new_string_value = text_split
                    
                    if not skip_indent:
                        new_string_value = self._remove_tab(text_split)
                    
                    if inc == 0 and new_string_value == text_split:
                        skip_indent = True
                    
                    if not skip_indent:
                        if new_string_value != text_split:
                            if inc == 0:
                                
                                offset = (start - 4) + 4
                                if offset > 4:
                                    offset = 4
                                start_position -= offset
                            
                            end_position -=4
                    
                    edited.append( new_string_value )
                    
                    inc += 1
            
                edited_text = string.join(edited, '\n')
            
                cursor.insertText(edited_text)
                self.setTextCursor(cursor)
        
        cursor = self.textCursor()
        cursor.setPosition(start_position)
        cursor.setPosition(end_position,qt.QTextCursor.KeepAnchor)
        self.setTextCursor(cursor)
    
    def set_file(self, filepath):
        
        in_file = qt.QtCore.QFile(filepath)
        
        if in_file.open(qt.QtCore.QFile.ReadOnly | qt.QtCore.QFile.Text):
            text = in_file.readAll()
            
            text = str(text)
            
            self.setPlainText(text)
            
        self.filepath = filepath
        
        self.last_modified = util_file.get_last_modified_date(self.filepath)
        
        if self.completer:
            self.completer.set_filepath(filepath)
        
        self.file_set.emit()
    

    def set_completer(self, completer):
        
        self.completer = completer()
        
        self.completer.setWidget(self)
        
        self.completer.set_filepath(self.filepath)

    
    def set_find_widget(self, widget):
        
        self.find_widget.set_widget(widget)
        
        
    
    def load_modification_date(self):
        
        self.last_modified = util_file.get_last_modified_date(self.filepath)
      
    def is_modified(self):
        if not self.document().isModified():
            return False
        if self.document().isModified():
            return True
        
        
class FindTextWidget(BasicDialog):
    
    closed = create_signal()
    
    def __init__(self, text_widget):
        self.found_match = False
        
        super(FindTextWidget, self).__init__(parent = text_widget)
        
        self.text_widget = text_widget
        
        self.text_widget.cursorPositionChanged.connect(self._reset_found_match)
        
        #self.setWindowFlags( self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint | QtCore.Qt.WindowStaysOnTopHint)
        #self.setWindowFlags( QtCore.Qt.WindowStaysOnBottomHint)
        
        self.setWindowTitle('Find/Replace')
        
    def closeEvent(self, event):
        super(FindTextWidget, self).closeEvent(event)
        
        self.closed.emit()
        
    def _build_widgets(self):
        super(FindTextWidget, self)._build_widgets()
        
        self.find_string = GetString( 'Find' )
        self.replace_string = GetString( 'Replace' )
        
        h_layout = qt.QHBoxLayout()
        h_layout2 = qt.QHBoxLayout()
        
        find_button = qt.QPushButton('Find')
        replace_button = qt.QPushButton('Replace')
        replace_all_button = qt.QPushButton('Replace All')
        replace_find_button = qt.QPushButton('Replace/Find')
        
        find_button.setMaximumWidth(100)
        replace_button.setMaximumWidth(100)
        
        replace_find_button.setMaximumWidth(100)
        replace_all_button.setMaximumWidth(100)
        
        h_layout.addWidget(find_button)
        h_layout.addWidget(replace_button)
        
        h_layout2.addWidget(replace_find_button)
        h_layout2.addWidget(replace_all_button)
        
        find_button.clicked.connect(self._find)
        replace_button.clicked.connect(self._replace)
        replace_find_button.clicked.connect(self._replace_find)
        replace_all_button.clicked.connect(self._replace_all)
        
        self.main_layout.addWidget(self.find_string)
        self.main_layout.addWidget(self.replace_string)
        self.main_layout.addLayout(h_layout)
        self.main_layout.addLayout(h_layout2)
        
        self.setMaximumHeight(125)
        
    def _reset_found_match(self):
        self.found_match = False
        
    def _get_cursor_index(self):
        
        cursor = self.text_widget.textCursor()
        return cursor.position()
        
    def _move_cursor(self,start,end):
        
        cursor = self.text_widget.textCursor()
        
        cursor.setPosition(start)
        
        cursor.movePosition(qt.QTextCursor.Right,qt.QTextCursor.KeepAnchor,end - start)
        
        self.text_widget.setTextCursor(cursor)
        
        
    def _find(self):
        
        text = self.text_widget.toPlainText()
        
        find_text = str(self.find_string.get_text())
        
        pattern = re.compile( find_text, 0)

        start = self._get_cursor_index()

        match = pattern.search(text,start)

        if match:
            
            start = match.start()
            end = match.end()
            
            self._move_cursor(start,end)
            self.found_match = True
            
        if not match:
            self.found_match = False
            
            if start != 0:
                permission = get_permission('Wrap Search?', self)
                
                if not permission:
                    return
                
                self._move_cursor(0, 0)
                self._find()

    def _replace(self):
        
        if not self.found_match:
            return
        
        cursor = self.text_widget.textCursor()
    
        cursor.insertText( self.replace_string.get_text() )

        self.text_widget.setTextCursor(cursor)
    
    def _replace_find(self):
        
        self._replace()
        self._find()
        
    def _replace_all(self):
        
        cursor = self.text_widget.textCursor()
        
        cursor.setPosition(0)
        self.text_widget.setTextCursor(cursor)
        
        self._find()
        
        while self.found_match:
            self._replace()
            self._find()
            
    def set_widget(self, widget):
        
        self.found_match = False
        self.text_widget = widget

class CodeLineNumber(qt.QWidget):
    
    def __init__(self, code_editor):
        super(CodeLineNumber, self).__init__()
        
        self.setParent(code_editor)
        
        self.code_editor = code_editor
    
    def sizeHint(self):
        
        return qt.QtCore.QSize(self.code_editor._line_number_width(), 0)
    
    def paintEvent(self, event):
        
        self.code_editor._line_number_paint(event)

class NewItemTabWidget(qt.QTabWidget):
    
    tab_closed = create_signal(object)
    tab_renamed = create_signal(object)
    tab_add = create_signal(object)
    
    def __init__(self):
        super(NewItemTabWidget, self).__init__()
        
        #self.tabBar().setMinimumHeight(60)
        
        self.tabBar().setContextMenuPolicy(qt.QtCore.Qt.CustomContextMenu)
        self.tabBar().customContextMenuRequested.connect(self._item_menu)
        
        self._create_context_menu()
        
        self.currentChanged.connect(self._tab_changed)
        
    def _create_context_menu(self):
        
        self.context_menu = qt.QMenu()
        
        rename = self.context_menu.addAction('Rename')
        rename.triggered.connect(self._rename_tab)
        
        close = self.context_menu.addAction('Close')
        close.triggered.connect(self._close_tab)
        
    def _item_menu(self, position):
        
        self.context_menu.exec_(self.tabBar().mapToGlobal(position))
    
    def _rename_tab(self):
        
        index = self.currentIndex()
        
        tab_name = self.tabText(index)
        
        new_name = get_new_name('New Name', self, tab_name)
        
        if not new_name:
            return
        
        self.setTabText(index, new_name)
        
        self.tab_renamed.emit(index)
        
    def _close_tab(self, index = None):
        
        
        if index == None:
            current_index = self.currentIndex()
            
        
        if not index == None:
            current_index = index
        
        self.setCurrentIndex( (current_index - 1) )
        
        self.tab_closed.emit(current_index)
        
        widget = self.widget( current_index )
        
        if hasattr(widget, 'scene'):
            widget.scene.clearSelection()
        
        widget.close()
        
        widget.deleteLater()
        
        self.removeTab( current_index )
        
        
        
    def _tab_changed(self):
        
        index = self.currentIndex()
        
        title = self.tabText(index)
        
        if title == '+':
            self.removeTab(index)
            self.tab_add.emit(index)
            self.addTab(qt.QWidget(), '+')
            self.setCurrentIndex(index)
            
            index = index + 1
            
        #if not title == '+':
        #    self.edit_buttons.set_picker(self.pickers[index])
        

    def custom_close(self):
        return
        
    def close_tabs(self):
        
        tab_count = self.count()
        
        for inc in reversed(range(0, tab_count)):
            self._close_tab(inc)

#start
def get_syntax_format(color = None, style=''):
    """Return a QTextCharFormat with the given attributes.
    """
    
    _color = None
    
    if type(color) == str:
    
        _color = qt.QColor()
        _color.setNamedColor(color)
    if type(color) == list:
        _color = qt.QColor(*color)

    if color == 'green':
        _color = qt.QtCore.Qt.green

    

    _format = qt.QTextCharFormat()
    
    if _color:
        _format.setForeground(_color)
    if 'bold' in style:
        _format.setFontWeight(qt.QFont.Bold)
    if 'italic' in style:
        _format.setFontItalic(True)

    return _format

def syntax_styles(name):
    
    if name == 'keyword':
        if util.is_in_maya():
            return get_syntax_format('green', 'bold')
        if not util.is_in_maya():
            return get_syntax_format([0, 150, 150], 'bold')
    if name == 'operator':
        if util.is_in_maya():
            return get_syntax_format('gray')
        if not util.is_in_maya():
            return get_syntax_format('darkGray')
    if name == 'brace':
        if util.is_in_maya():
            return get_syntax_format('lightGray')
        if not util.is_in_maya():
            return get_syntax_format('darkGray')
    if name == 'defclass':
        if util.is_in_maya():
            return get_syntax_format(None, 'bold')
        if not util.is_in_maya():
            return get_syntax_format(None, 'bold')
    if name == 'string':
        if util.is_in_maya():
            return get_syntax_format([230, 230, 0])
        if not util.is_in_maya():
            return get_syntax_format('blue') 
    if name == 'string2':       
        if util.is_in_maya():
            return get_syntax_format([230, 230, 0])
        if not util.is_in_maya():
            return get_syntax_format('lightGreen')
    if name == 'comment':
        if util.is_in_maya():
            return get_syntax_format('red')
        if not util.is_in_maya():
            return get_syntax_format('red')
    if name == 'self':
        if util.is_in_maya():
            return get_syntax_format(None, 'italic')
        if not util.is_in_maya():
            return get_syntax_format('black', 'italic')
    if name == 'bold':
        return get_syntax_format(None, 'bold')
    if name == 'numbers':
        if util.is_in_maya():
            return get_syntax_format('cyan')
        if not util.is_in_maya():
            return get_syntax_format('brown')
         
class PythonHighlighter (qt.QSyntaxHighlighter):
    """Syntax highlighter for the Python language.
    """
    # Python keywords
    keywords = [
        'and', 'assert', 'break', 'class', 'continue', 'def',
        'del', 'elif', 'else', 'except', 'exec', 'finally',
        'for', 'from', 'global', 'if', 'import', 'in',
        'is', 'lambda', 'not', 'or', 'pass', 'print',
        'raise', 'return', 'try', 'while', 'yield',
        'None', 'True', 'False', 'process'
    ]

    # Python operators
    operators = [
        '=',
        # Comparison
        '==', '!=', '<', '<=', '>', '>=',
        # Arithmetic
        '\+', '-', '\*', '/', '//', '\%', '\*\*',
        # In-place
        '\+=', '-=', '\*=', '/=', '\%=',
        # Bitwise
        '\^', '\|', '\&', '\~', '>>', '<<',
    ]

    # Python braces
    braces = [
              '\{', '\}', '\(', '\)', '\[', '\]',
              ]
    def __init__(self, document):
        qt.QSyntaxHighlighter.__init__(self, document)

        # Multi-line strings (expression, flag, style)
        # FIXME: The triple-quotes in these two lines will mess up the
        # syntax highlighting from this point onward
        self.tri_single = (qt.QtCore.QRegExp("'''"), 1, syntax_styles('string2'))
        self.tri_double = (qt.QtCore.QRegExp('"""'), 2, syntax_styles('string2'))

        rules = []

        # Keyword, operator, and brace rules
        rules += [(r'\b%s\b' % w, 0, syntax_styles('keyword'))
            for w in PythonHighlighter.keywords]
        rules += [(r'%s' % o, 0, syntax_styles('operator'))
            for o in PythonHighlighter.operators]
        rules += [(r'%s' % b, 0, syntax_styles('brace'))
            for b in PythonHighlighter.braces]

        # All other rules
        rules += [
            # 'self'
            (r'\bself\b', 0, syntax_styles('self')),

            # Double-quoted string, possibly containing escape sequences
            (r'"[^"\\]*(\\.[^"\\]*)*"', 0, syntax_styles('string')),
            # Single-quoted string, possibly containing escape sequences
            (r"'[^'\\]*(\\.[^'\\]*)*'", 0, syntax_styles('string')),

            # 'def' followed by an identifier
            #(r'\bdef\b\s*(\w+)', 0, syntax_styles('defclass')),
            # 'class' followed by an identifier
            #(r'\bclass\b\s*(\w+)', 0, syntax_styles('defclass')),

            # From '#' until a newline
            (r'#[^\n]*', 0, syntax_styles('comment')),
            #('\\b\.[a-zA-Z_]+\\b(?=\()', 0, syntax_styles('bold')),
            # Numeric literals
            (r'\b[+-]?[0-9]+[lL]?\b', 0, syntax_styles('numbers')),
            (r'\b[+-]?0[xX][0-9A-Fa-f]+[lL]?\b', 0, syntax_styles('numbers')),
            (r'\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b', 0, syntax_styles('numbers')),
        ]

        # Build a QRegExp for each pattern
        self.rules = [(qt.QtCore.QRegExp(pat), index, fmt)
            for (pat, index, fmt) in rules]


    def highlightBlock(self, text):
        """Apply syntax highlighting to the given block of text.
        """
        # Do other syntax formatting
        for expression, nth, format_value in self.rules:
            index = expression.indexIn(text, 0)

            while index >= 0:
                # We actually want the index of the nth match
                index = expression.pos(nth)
                length = len(expression.cap(nth))
                self.setFormat(index, length, format_value)
                index = expression.indexIn(text, index + length)

        self.setCurrentBlockState(0)

        # Do multi-line strings
        in_multiline = self.match_multiline(text, *self.tri_single)
        if not in_multiline:
            in_multiline = self.match_multiline(text, *self.tri_double)


    def match_multiline(self, text, delimiter, in_state, style):
        """Do highlighting of multi-line strings. ``delimiter`` should be a
        ``QRegExp`` for triple-single-quotes or triple-double-quotes, and
        ``in_state`` should be a unique integer to represent the corresponding
        state changes when inside those strings. Returns True if we're still
        inside a multi-line string when this function is finished.
        """
        # If inside triple-single quotes, start at 0
        if self.previousBlockState() == in_state:
            start = 0
            add = 0
        # Otherwise, look for the delimiter on this line
        else:
            start = delimiter.indexIn(text)
            # Move past this match
            add = delimiter.matchedLength()

        # As long as there's a delimiter match on this line...
        while start >= 0:
            # Look for the ending delimiter
            end = delimiter.indexIn(text, start + add)
            # Ending delimiter on this line?
            if end >= add:
                length = end - start + add + delimiter.matchedLength()
                self.setCurrentBlockState(0)
            # No; multi-line string
            else:
                self.setCurrentBlockState(in_state)
                length = len(text) - start + add
            # Apply formatting
            self.setFormat(start, length, style)
            # Look for the next match
            start = delimiter.indexIn(text, start + length)

        # Return True if still inside a multi-line string, False otherwise
        if self.currentBlockState() == in_state:
            return True
        else:
            return False


class PythonCompleter(qt.QCompleter):
    
    def __init__(self):
        super(PythonCompleter, self).__init__()
        
        
        self.model_strings = []
        
        self.reset_list = True
        
        self.string_model =qt.QStringListModel(self.model_strings, self)
        
        self.setCompletionMode(self.PopupCompletion)
        #self.setCompletionMode(self.Un)
        #self.setCompletionMode(self.InlineCompletion)
        self.setCaseSensitivity(qt.QtCore.Qt.CaseSensitive)
        self.setModel(self.string_model)
        self.setModelSorting(self.CaseInsensitivelySortedModel)
        self.setWrapAround(False)
        self.activated.connect(self._insert_completion)
        
        self.refresh_completer = True
        self.sub_activated = False
        
        self.last_imports = None
        self.last_lines = None
        
        self.last_path = None
        self.current_defined_imports = None
        
        self.last_path_and_part = None
        self.current_sub_functions = None
        
        self.last_column = 0
        
        
        
    def keyPressEvent(self):
        return
        
    def show_info_popup(self, info = None):
        
        
        self.info = qt.QTextEdit()
        self.info.setEnabled(False)
        
        
        self.info.setWindowFlags(qt.QtCore.Qt.Popup)
        self.info.show()
    
    def _get_available_modules(self, paths = None):
        
        imports = []
        
        if not paths:
            paths = sys.path
        if paths:
            paths = util.convert_to_sequence(paths)
        
        for path in paths:
            
            fix_path = util_file.fix_slashes(path)
            
            if not util_file.is_dir(fix_path):
                continue
            
            folders = util_file.get_folders(fix_path)
            
            for folder in folders:
                
                folder_path = util_file.join_path(fix_path, folder)
                files = util_file.get_files_with_extension('py', folder_path, fullpath = False)
                
                if '__init__.py' in files:
                    import_name = 'import %s' % folder
                    imports.append(str(folder))
            
            python_files = util_file.get_files_with_extension('py', fix_path, fullpath = False)
            
            for python_file in python_files:
                
                if python_file == '__init__.py':
                    continue
                
                python_file_name = python_file.split('.')[0]
                
                imports.append(str(python_file_name))
                
        if imports:
            imports = list(set(imports))
        
        return imports
    
    def _insert_completion(self, completion_string):
        
        widget = self.widget()
        
        cursor = widget.textCursor()
        
        if completion_string == self.completionPrefix():
            return
        
        extra = len(completion_string) - len(self.completionPrefix() )
        
        cursor.insertText( completion_string[-extra:] )
        
        
        widget.setTextCursor(cursor)
    
    def setWidget(self, widget):
    
        super(PythonCompleter, self).setWidget(widget)
        
        self.setParent(widget)
        
    def get_imports(self, paths = None):
        
        imports = self._get_available_modules(paths)
        imports.sort()
        
        return imports
        
    
    def get_sub_imports(self, path):
        """
        get namespaces in a module.
        """
        
        defined = util_file.get_defined(path)
        defined.sort()
        
        return defined
    
    def clear_completer_list(self):
        
        self.string_model.setStringList([])
        
    def handle_text(self, text):
        """
        Parse a single line of text.
        """
        
        if text:
            
            cursor = self.widget().textCursor()
            
            column = cursor.columnNumber() - 1
            if column < self.last_column:
                self.last_column = column
                return False
            self.last_column = column
            
            
            if column == -1:
                return False
            
            text = str(text)
            
            passed = self.handle_from_import(text, column)
            if passed:
                return True
            
            passed = self.handle_sub_import(text, column)
            if passed:
                return True
            
            passed = self.handle_import_load(text, cursor)
            if passed:
                return True

        return False
    
    def handle_import(self, text):
    
        m = re.search('(from|import)(?:\s+?)(\w*)', text)
        if m:
            
            #this would need to find available modules in the python path...
            pass 
            
    def handle_sub_import(self, text, column):
        
        m = re.search('(from|import)(?:\s+?)(\w*.?\w*)\.(\w*)$', text)
        
        if m:
            if column < m.end(2):
                return False
            from_module = m.group(2)
            module_path = util_file.get_package_path_from_name(from_module)
            last_part = m.group(3)
            
            if module_path:
                defined = self.get_imports(module_path)
            
                self.string_model.setStringList(defined)
            
                self.setCompletionPrefix(last_part)
                self.popup().setCurrentIndex(self.completionModel().index(0,0))
                
                return True
        
        return False
    
    def handle_import_load(self, text, cursor):
        
        m = re.search('\s*([a-zA-Z0-9._]+)\.([a-zA-Z0-9_]*)$', text)
        
        column = cursor.columnNumber() - 1
        block_number = cursor.blockNumber()
        line_number = block_number + 1
        
        all_text = self.widget().toPlainText()
        
        scope_text = all_text[:(cursor.position() - 1)]
        
        if m and m.group(2):
            scope_text = all_text[:(cursor.position() - len(m.group(2)) + 1)]
        
        if m:
            
            assignment = m.group(1)
            
            if column < m.end(1):
                return False
            
            sub_m = re.search('(from|import)\s+(%s)' % assignment, text)
            
            if sub_m:
                return False
            
            text = self.widget().toPlainText()
            lines = util_file.get_text_lines(text)
            
            
            path = None
            
            assign_map = util_file.get_ast_assignment(scope_text, line_number-1, assignment)
            sub_part = None
            
            target = None
            #searching for assignments
            
            if assign_map:
                
                if assignment in assign_map:
                    target = assign_map[assignment]
                    
                else:
                    split_assignment = assignment.split('.')
                    
                    inc = 1
                    
                    while not assignment in assign_map:
                        
                        sub_assignment = string.join(split_assignment[:(inc*-1)],'.')
                        
                        if sub_assignment in assign_map:
                            target = assign_map[sub_assignment]
                            break
                        
                        inc += 1
                        if inc > (len(split_assignment) - 1):
                            break
                
                    sub_part = string.join(split_assignment[inc:], '.')
                    
            module_name = m.group(1)
            
            if target and len(target) == 2:
                if target[0] == 'import':
                    module_name = target[1]
                if not target[0] == 'import':
                    
                    module_name = target[0]
                    sub_part = target[1]
                    
            #import from module   
            if module_name:
                
                imports = None
                
                if lines == self.last_lines:
                    imports = self.last_imports
                
                if not imports:
                    imports = util_file.get_line_imports(lines)
                
                self.last_imports = imports
                self.last_lines = lines
                
                if module_name in imports:
                    path = imports[module_name]
                    
                if not module_name in imports:
                
                    split_assignment = module_name.split('.')
                    
                    last_part = split_assignment[-1]
                    
                    if last_part in imports:
                        path = imports[last_part]
    
                    #if not last_part in imports:
                    #    module_name = None
                
                
                if path and not sub_part:
                    test_text = ''
                    defined = None
                    
                    if path == self.last_path:
                        defined = self.current_defined_imports
                    
                    if len(m.groups()) > 0:
                        test_text = m.group(2)
                    
                    if not defined:
                        if util_file.is_dir(path):
                            defined = self.get_imports(path)
                            self.current_defined_imports = defined
                        
                        if util_file.is_file(path):
                            defined = self.get_sub_imports(path)
                    
                    custom_defined = self.custom_import_load(assign_map, module_name)
                    
                    if custom_defined:
                        defined = custom_defined
                    
                    self.string_model.setStringList(defined)
                    self.setCompletionPrefix(test_text)
                    self.popup().setCurrentIndex(self.completionModel().index(0,0))
                    return True
    
                #import from a class of a module
                
                if path and sub_part:
                    
                    sub_functions = None
                    
                    if self.last_path_and_part:
                        if path == self.last_path_and_part[0] and sub_part == self.last_path_and_part[1]:
                            sub_functions = self.current_sub_functions
                        
                    if not sub_functions:
                        sub_functions = util_file.get_ast_class_sub_functions(path, sub_part)
                        self.current_sub_functions = sub_functions
                    
                    self.last_path_and_part = [path, sub_part]
                    
                    if not sub_functions:
                        return False
                    
                    test_text = ''
                    
                    if len(m.groups()) > 0:
                        test_text = m.group(2)
                                        
                    self.string_model.setStringList(sub_functions)
                    self.setCompletionPrefix(test_text)
                    self.popup().setCurrentIndex(self.completionModel().index(0,0))
                    
                    return True
                
            module_name = m.group(1)
            
            if module_name:
                custom_defined = self.custom_import_load(assign_map, module_name)
                
                test_text = ''
                    
                if len(m.groups()) > 0:
                    test_text = m.group(2)
                
                self.string_model.setStringList(custom_defined)
                self.setCompletionPrefix(test_text)
                self.popup().setCurrentIndex(self.completionModel().index(0,0))
                return True
            
        return False
    
    def custom_import_load(self, assign_map, module_name):
        
        return
    
    def handle_from_import(self, text, column):
        
        m = re.search('(from)(?:\s+?)(\w*.?\w*)(?:\s+?)(import)(?:\s+?)(\w+)?$', text)
        
        if m:
            if column < m.end(3):
                return False
            from_module = m.group(2)
            module_path = util_file.get_package_path_from_name(from_module)
            
            last_part = m.group(4)
            
            if not last_part:
                last_part = ''
            
            if module_path:
                
                defined = self.get_imports(module_path)
                
                self.string_model.setStringList(defined)
                self.setCompletionPrefix(last_part)
                self.popup().setCurrentIndex(self.completionModel().index(0,0))
                
                return True
            
        return False
                
    def text_under_cursor(self):
        
        cursor = self.widget().textCursor()
        
        cursor.select(cursor.LineUnderCursor)
        
        return cursor.selectedText()
    
    def set_filepath(self, filepath):
        if not filepath:
            return
        
        self.filepath = filepath
     
   
#--- Custom Painted Widgets

class TimelineWidget(qt.QWidget):

    def __init__(self):
        super(TimelineWidget, self).__init__()
        self.setSizePolicy(qt.QSizePolicy.Expanding,qt.QSizePolicy.Expanding)
        self.setMaximumHeight(120)
        self.setMinimumHeight(80)
        self.values = []
        self.skip_random = False
        
    def sizeHint(self):
        return qt.QtCore.QSize(100,80)
       
    def paintEvent(self, e):

        painter = qt.QPainter()
        
        painter.begin(self)
                        
        if not self.values and not self.skip_random:
            self._draw_random_lines(painter)
            
        if self.values or self.skip_random:
            self._draw_lines(painter)
            
        self._draw_frame(painter)
            
        painter.end()
        
    def _draw_frame(self, painter):
        
        pen = qt.QPen(qt.QtCore.Qt.gray)
        pen.setWidth(2)
        painter.setPen(pen)
        
        height_offset = 20
        
        size = self.size()
        
        width = size.width()
        height = size.height()
        
        section = (width-21.00)/24.00
        accum = 10.00
        
        for inc in range(0, 25):
            
            value = inc
            
            if inc > 12:
                value = inc-12
                
            painter.drawLine(accum, height-(height_offset+1), accum, 30)
            
            sub_accum = accum + (section/2.0)
            
            painter.drawLine(sub_accum, height-(height_offset+1), sub_accum, height-(height_offset+11))
            
            painter.drawText(accum-15, height-(height_offset+12), 30,height-(height_offset+12), qt.QtCore.Qt.AlignCenter, str(value))
            
            accum+=section
        
    def _draw_random_lines(self, painter):
      
        pen = qt.QPen(qt.QtCore.Qt.green)
        pen.setWidth(2)
        
        height_offset = 20
        
        painter.setPen(pen)
        
        size = self.size()
        
        for i in range(500):
            x = random.randint(10, size.width()-11)               
            painter.drawLine(x,10,x,size.height()-(height_offset+2))
            
    def _draw_lines(self, painter):
        
        pen = qt.QPen(qt.QtCore.Qt.green)
        pen.setWidth(3)
        
        height_offset = 20
        
        painter.setPen(pen)
        
        size = self.size()
        
        if not self.values:
            return
        
        for inc in range(0, len(self.values)):
            
            width = size.width()-21
            
            x_value = (width * self.values[inc]) / 24.00  
                        
            x_value += 10
                         
            painter.drawLine(x_value,10,x_value,size.height()-(height_offset+2))
        
    def set_values(self, value_list):
        self.skip_random = True
        self.values = value_list
        
  
def get_comment(parent = None,text_message = 'add comment', title = 'save', comment_text = ''):
    
    dialogue = qt.QInputDialog()
    
    flags = dialogue.windowFlags() ^ qt.QtCore.Qt.WindowContextHelpButtonHint | qt.QtCore.Qt.WindowStaysOnTopHint
    
    comment, ok = dialogue.getText(parent, title,text_message, flags = flags, text = comment_text)
    comment = comment.replace('\\', '_')  
    
    if ok:
        return comment

def get_file(directory, parent = None):
    fileDialog = qt.QFileDialog(parent)
    
    if directory:
        fileDialog.setDirectory(directory)
    
    directory = fileDialog.getOpenFileName()
    
    directory = util.convert_to_sequence(directory)
    directory = directory[0]
    
    if directory:
        return directory
    
    
def get_folder(directory, parent = None):
    fileDialog = qt.QFileDialog(parent)
    
    if directory:
        fileDialog.setDirectory(directory)
    
    directory = fileDialog.getExistingDirectory()
    
    if directory:
        return directory
    

def get_permission(message = None, parent = None, cancel = True, title = 'Permission'):
    
    message_box = qt.QMessageBox()

    flags = message_box.windowFlags() ^ qt.QtCore.Qt.WindowContextHelpButtonHint | qt.QtCore.Qt.WindowStaysOnTopHint

    if message:
        message_box.setText(message)
    message_box.setWindowTitle(title)
    if cancel:
        message_box.setStandardButtons(qt.QMessageBox.Yes | qt.QMessageBox.No | qt.QMessageBox.Cancel)
    if not cancel:
        message_box.setStandardButtons(qt.QMessageBox.Yes | qt.QMessageBox.No)
    
    message_box.setWindowFlags(flags)
    
    message = message_box.exec_()
    
    if message == message_box.Yes:
        return True
    
    if message == message_box.No:
        return False
    
    if message == message_box.Cancel:
        return None

def get_save_permission(message, parent = None, path = None):
    parent = None
    message_box = qt.QMessageBox(parent)
    
    flags = message_box.windowFlags() ^ qt.QtCore.Qt.WindowContextHelpButtonHint | qt.QtCore.Qt.WindowStaysOnTopHint
    
    #flags = message_box.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint | QtCore.Qt.WindowStaysOnTopHint
    message_box.setWindowFlags(flags)
    message_box.setText(message)
    message_box.setWindowTitle('Permission')
    if path:
        path_message = 'Path:  %s' % path
        message_box.setInformativeText(path_message)
    
    save = message_box.addButton('Save', qt.QMessageBox.YesRole)
    no_save = message_box.addButton("Don't Save", qt.QMessageBox.NoRole)
    cancel = message_box.addButton('Cancel', qt.QMessageBox.RejectRole)
    
    #message_box.setWindowFlags(flags)
    message = message_box.exec_()
    
    if message_box.clickedButton() == save:
        return True
    
    if message_box.clickedButton() == no_save:
        return False
    
    if message_box.clickedButton() == cancel:
        return None
    
    
def get_new_name(message, parent = None, old_name = None):
    
    #this is to make the dialog always on top.
    parent = None
    
    dialog = qt.QInputDialog()
    
    flags = dialog.windowFlags() ^ qt.QtCore.Qt.WindowContextHelpButtonHint | qt.QtCore.Qt.WindowStaysOnTopHint
    
    if not old_name:
        comment, ok = dialog.getText(parent, 'Rename', message, flags = flags)
    if old_name:
        comment, ok = dialog.getText(parent, 'Rename', message, text = old_name, flags = flags)
    
    
    comment = comment.replace('\\', '_')  
    
    if ok:
        return str(comment)
    
def critical(message, parent = None):
    #this is to make the dialog always on top.
    parent = None
    message_box = qt.QMessageBox(parent)
    flags = message_box.windowFlags() ^ qt.QtCore.Qt.WindowContextHelpButtonHint | qt.QtCore.Qt.WindowStaysOnTopHint
    message_box.setWindowFlags(flags)
    message_box.critical(parent, 'Critical Error', message)
    
def warning(message, parent = None):
    #this is to make the dialog always on top.
    message_box = qt.QMessageBox(parent)
    parent = None
    flags = message_box.windowFlags() ^ qt.QtCore.Qt.WindowContextHelpButtonHint | qt.QtCore.Qt.WindowStaysOnTopHint
    message_box.setWindowFlags(flags)
    message_box.warning(parent, 'Warning', message)

def about(message, parent = None):
    parent = None
    message_box = qt.QMessageBox(parent)
    flags = message_box.windowFlags() ^ qt.QtCore.Qt.WindowContextHelpButtonHint | qt.QtCore.Qt.WindowStaysOnTopHint
    message_box.setWindowFlags(flags)
    message_box.about(parent, 'About', message)

def get_pick(list_values, text_message, parent = None):
    parent = None
    input_dialog = qt.QInputDialog(parent)
    input_dialog.setComboBoxItems(list_values)
    
    flags = input_dialog.windowFlags() ^ qt.QtCore.Qt.WindowContextHelpButtonHint | qt.QtCore.Qt.WindowStaysOnTopHint
    picked, ok = qt.QInputDialog.getItem(parent, 'Pick One', text_message, list_values, flags = flags)
    
    if ok:
        return picked
    
def get_icon(icon_name_including_extension):
    
    vetala_directory = util_file.get_vetala_directory()
    icon_path = util_file.join_path(vetala_directory, 'icons/%s' % icon_name_including_extension)
    icon = qt.QIcon(icon_path)
    
    return icon