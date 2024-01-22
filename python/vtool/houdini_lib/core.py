import hou


def save(filepath):
    hou.hipFile.save(filepath)


def load(filepath):
    hou.hipFile.load(filepath)


def merge(filepath):
    hou.hipFile.merge(filepath)
