import os


def __main__(deadlinePlugin):

    deadlinePlugin.LogInfo("Adding custom userSetup.py")

    deadlinePlugin.SetProcessEnvironmentVariable(
        "PYTHONPATH", os.path.dirname(__file__)
    )
