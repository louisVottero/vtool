# Copyright (C) 2024 Louis Vottero louis.vot@gmail.com    All rights reserved.

from __future__ import absolute_import

from ... import qt_ui, qt, util
from .. import ui_core
from .. import core

if util.is_in_maya():
    import maya.cmds as cmds


class CharacterTree(qt.QTreeWidget):
    characters_selected = qt_ui.create_signal(object)

    def __init__(self):
        super(CharacterTree, self).__init__()

        self.setHeaderHidden(True)

        ui_core.new_scene_signal.signal.connect(self.refresh)
        ui_core.open_scene_signal.signal.connect(self.refresh)
        ui_core.read_scene_signal.signal.connect(self.refresh)

        self.itemSelectionChanged.connect(self._item_selected)

        self.setSelectionMode(qt.QTreeWidget.ExtendedSelection)

        self.current_characters = []

        self.refresh()

    def _item_selected(self):

        selected = self.selectedItems()

        self.current_characters = []

        for select in selected:
            namespace = select.text(0)

            self.current_characters.append(namespace)

        self.characters_selected.emit(self.current_characters)

    def refresh(self):

        self.clear()

        characters = core.get_characters()

        self.current_characters = []

        for character in characters:
            item = qt.QTreeWidgetItem()
            item.setText(0, character)
            item.setSizeHint(0, qt.QtCore.QSize(20, 20))

            self.insertTopLevelItem(0, item)

        if not characters:
            item = qt.QTreeWidgetItem()
            item.setText(0, 'Nothing Referenced')
            item.setDisabled(True)

            self.addTopLevelItem(item)
