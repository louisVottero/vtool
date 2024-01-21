import hou


def save(filepath):
    print('save ', filepath)
    hou.hipFile.save(filepath)


def load(filepath):
    print('load ', filepath)
    hou.hipFile.load(filepath)
