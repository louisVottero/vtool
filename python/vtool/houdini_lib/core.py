import hou


def save(filepath):
    hou.hipFile.save(filepath)


def load(filepath):
    hou.hipFile.load(filepath)
