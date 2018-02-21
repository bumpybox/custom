import os


def __main__(deadlinePlugin):
    deadlinePlugin.SetProcessEnvironmentVariable(
        "NUKE_PATH",
        os.path.abspath(os.path.join(__file__, "..", "Cryptomatte", "nuke"))
    )
