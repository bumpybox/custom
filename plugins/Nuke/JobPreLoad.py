import os

from System import *
from System.IO import *

def __main__(deadlinePlugin):
    path = os.path.dirname(__file__)
    deadlinePlugin.LogInfo("Setting NUKE_PATH to {}".format(path))
    deadlinePlugin.SetProcessEnvironmentVariable("NUKE_PATH", path)
