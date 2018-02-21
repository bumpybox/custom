import os


def __main__(deadlinePlugin):

    deadlinePlugin.LogInfo("Adding custom userSetup.py")

    deadlinePlugin.SetProcessEnvironmentVariable(
        "PYTHONPATH",
        os.path.abspath(os.path.join(__file__, "..", "PYTHONPATH"))
    )

    deadlinePlugin.SetProcessEnvironmentVariable(
        "ARNOLD_PLUGIN_PATH",
        os.path.abspath(os.path.join(__file__, "..", "ARNOLD_PLUGIN_PATH"))
    )
