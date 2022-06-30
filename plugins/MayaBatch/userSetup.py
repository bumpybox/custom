import socket
import os

from maya import cmds

from maya.plugin.evaluator.cache_preferences import CachePreferenceEnabled


def open_deadline_port():

    cmds.commandPort(
        name=":{}".format(os.environ["MAYASEQUENCE_RENDER_PORT"]),
        sourceType="python"
    )
    print("Deadline port is open.")

    # Reply to Deadline server waiting on Maya boot.
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = ("localhost", int(os.environ["MAYASEQUENCE_LAUNCH_PORT"]))
    sock.connect(server_address)


def load_plugins():
    print("Loading plugins...")
    cmds.loadPlugin("mtoa.mll")
    cmds.loadPlugin("AbcExport.mll", quiet=True)
    cmds.loadPlugin("AbcImport.mll", quiet=True)


def setup():
    # Turn off cached playback. This can cause issues when renders are jumping
    # back and forth on the timeline.
    print("Disabling playback cache...")
    CachePreferenceEnabled().set_value(False)


cmds.evalDeferred(load_plugins)
cmds.evalDeferred(setup)
cmds.evalDeferred(open_deadline_port, lowestPriority=True)
