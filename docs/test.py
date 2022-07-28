
import sys
import os

print(os.getcwd())
os.listdir(os.getcwd())
print(__file__)

sys.path.append('./python')
from vtool import util
print('is linux?')
print(util.is_linux())