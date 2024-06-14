from vtool import util

character_import = None


def set_current_character_import(node):

    global character_import

    character_import = node.path()

    util.show('Set current character to %s' % character_import)
