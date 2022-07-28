
import sys
import os

print(os.getcwd())
print(__file__)
print( __dir__)

path = __dir__
path = path[:-4] + 'python'

sys.path.append()
from vtool import util
print('is linux?')
print(util.is_linux())