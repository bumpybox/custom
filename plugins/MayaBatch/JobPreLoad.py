from System import *
from System.IO import *


def __main__(deadlinePlugin):
    env = {
        "BIFROST_LIB_CONFIG_FILES": (
            "L:/Maya/BIFROST_LIB_CONFIG_FILES/config.json"
        )
    }

    for key, value in env.items():
        deadlinePlugin.LogInfo("Setting {} to:\n{}".format(key, value))
        deadlinePlugin.SetProcessEnvironmentVariable(key, value)
