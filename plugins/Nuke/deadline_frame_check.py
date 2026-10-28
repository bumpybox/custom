"""Post-render output frame verification for the Deadline Nuke plugin.

This module runs INSIDE Nuke (Nuke 11 / Python 2.7 up to Nuke 17 / Python 3), so
it must stay Python 2 and Python 3 compatible.

Usage (driven by Nuke.py over stdin)::

    state = snapshot(["WriteNode1"], 1001, 1010)   # or snapshot(None, 1001, 1010)
    nuke.execute("WriteNode1", 1001, 1010, 1)
    verify(state, min_size=1, require_fresh=True, retries=3, retry_wait=5)

The module is deliberately fail-open: any internal problem prints a
"Frame check: skipped ..." line and never raises. None of the printed text may
contain the substrings that Deadline's Nuke plugin treats as render errors
(see ``_sanitize``). The only line that fails the task is the
``DEADLINE_FRAME_CHECK_FAILED: ...`` line, which Nuke.py handles explicitly.
"""
from __future__ import print_function

import os
import re
import sys
import time

try:
    import nuke
except ImportError:  # pragma: no cover - only happens outside of Nuke.
    nuke = None

MAX_FAILURE_LINES = 50

_PADDING_RE = re.compile(r"%\d*d")
_PRINTF_RE = re.compile(r"%(\d*)d")
_HASH_RE = re.compile(r"#+")
_FORBIDDEN_RE = re.compile(r"(Error|ERROR) ?:")


class FrameCheckState(object):
    """Expected output files and their pre-render stat."""

    def __init__(self):
        # List of dicts: path, node, frame, pre (None or (size, mtime)).
        self.entries = []


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------
def _sanitize(text):
    """Make sure the text can never match Deadline's error regexes."""
    return _FORBIDDEN_RE.sub(lambda m: m.group(1) + " -", text)


def _out(message):
    try:
        sys.stdout.write(_sanitize(message) + "\n")
    except Exception:
        try:
            sys.stdout.write("Frame check: (unprintable message)\n")
        except Exception:
            pass
    try:
        sys.stdout.flush()
    except Exception:
        pass


def _skipped(exception):
    _out("Frame check: skipped due to internal exception (%s)" % repr(exception))


# ---------------------------------------------------------------------------
# Node helpers
# ---------------------------------------------------------------------------
def _knob_value(node, knob_name, default=None):
    if knob_name in node.knobs():
        return node[knob_name].value()
    return default


def _is_enabled(node):
    """True if the node and all its parent groups are not disabled."""
    if _knob_value(node, "disable", False):
        return False

    parts = node.fullName().split(".")
    for index in range(1, len(parts)):
        parent = nuke.toNode(".".join(parts[:index]))
        if parent is not None and _knob_value(parent, "disable", False):
            return False
    return True


def _walk_write_nodes(parent):
    """Return Write nodes under parent, recursing into groups manually."""
    found = []
    for node in nuke.allNodes(group=parent):
        if node.Class() == "Write":
            found.append(node)
        if isinstance(node, nuke.Group):
            found.extend(_walk_write_nodes(node))
    return found


def _collect_write_nodes(node_names):
    """Return the enabled Write nodes for the given names (None = all)."""
    writes = []

    if node_names is None:
        candidates =         _walk_write_nodes(nuke.root())
    else:
        candidates = []
        for name in node_names:
            name = str(name).strip()
            node = nuke.toNode(name)
            if node is None:
                _out("Frame check: warning, node '%s' not found, skipping" % name)
                continue
            if node.Class() == "Write":
                candidates.append(node)
            else:
                candidates.extend(_walk_write_nodes(node))

    seen = set()
    for node in candidates:
        full_name = node.fullName()
        if full_name in seen:
            continue
        seen.add(full_name)
        if _is_enabled(node):
            writes.append(node)
    return writes


def _frame_range(node, first, last):
    lo, hi = int(first), int(last)
    if _knob_value(node, "use_limit", False):
        lo = max(lo, int(node["first"].value()))
        hi = min(hi, int(node["last"].value()))
    return lo, hi


def _file_knob_name(node):
    if "proxy" in node.knobs() and nuke.root()["proxy"].value():
        if node["proxy"].value():
            return "proxy"
    return "file"


def _views_for(node, raw_path):
    if "%V" not in raw_path and "%v" not in raw_path:
        return [None]
    views = []
    view_value = _knob_value(node, "views", "")
    if view_value:
        views = str(view_value).split()
    if not views:
        views = list(nuke.views())
    return views or [None]


def _evaluate_path(node, knob_name, frame, view):
    path = None
    try:
        context = nuke.OutputContext()
        context.setFrame(frame)
        all_views = list(nuke.views())
        if view and view in all_views:
            context.setView(all_views.index(view) + 1)
        else:
            context.setView(1)
        path = node[knob_name].getEvaluatedValue(context)
    except Exception:
        path = None
    if not path:
        path = node[knob_name].value()
    return path


def _expand_tokens(path, frame, view):
    """Resolve any frame/view tokens left in an evaluated path."""
    if view:
        path = path.replace("%V", view).replace("%v", view[0])
    path = _PRINTF_RE.sub(lambda m: ("%" + m.group(1) + "d") % frame, path)
    path = _HASH_RE.sub(lambda m: "%0*d" % (len(m.group(0)), frame), path)
    return os.path.normpath(path)


def _stat(path):
    try:
        info = os.stat(path)
    except Exception:
        return None
    return (info.st_size, info.st_mtime)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def snapshot(node_names, first, last):
    """Resolve expected output files and record their state before rendering.

    Returns a FrameCheckState, or None if anything went wrong.
    """
    try:
        state = FrameCheckState()
        known_paths = set()

        for node in _collect_write_nodes(node_names):
            knob_name = _file_knob_name(node)
            raw_path = node[knob_name].value()
            if not raw_path:
                continue

            lo, hi = _frame_range(node, first, last)
            if lo > hi:
                continue

            is_sequence = bool(_PADDING_RE.search(raw_path) or "#" in raw_path)
            frames = range(lo, hi + 1) if is_sequence else [lo]

            for view in _views_for(node, raw_path):
                for frame in frames:
                    evaluated = _evaluate_path(node, knob_name, frame, view)
                    path = _expand_tokens(evaluated, frame, view)
                    if path in known_paths:
                        continue
                    known_paths.add(path)
                    state.entries.append(
                        {
                            "path": path,
                            "node": node.fullName(),
                            "frame": frame,
                            "pre": _stat(path),
                        }
                    )

        return state
    except Exception as e:
        _skipped(e)
        return None


def _failure_reason(entry, min_size, require_fresh):
    """Return None if the entry is OK, otherwise a short reason string."""
    current = _stat(entry["path"])
    if current is None:
        return "missing"

    size = current[0]
    if size < min_size:
        if size == 0:
            return "empty file"
        return "too small (%d bytes)" % size

    if require_fresh and entry["pre"] is not None and current == entry["pre"]:
        return "not updated by this render"

    return None


def _refresh_directories(entries):
    """List parent directories to refresh network share caches."""
    for directory in set(os.path.dirname(entry["path"]) for entry in entries):
        try:
            os.listdir(directory)
        except Exception:
            pass


def verify(state, min_size=1, require_fresh=True, retries=3, retry_wait=5):
    """Check that every expected output file exists and was written.

    Prints DEADLINE_FRAME_CHECK_FAILED / DEADLINE_FRAME_CHECK_PASSED.
    Never raises.
    """
    try:
        if state is None or not isinstance(getattr(state, "entries", None), list):
            _out("Frame check: skipped, no valid snapshot available")
            return

        entries = state.entries
        total = len(entries)
        if total == 0:
            _out("Frame check: no write nodes/output files resolved, skipping verification")
            return

        failures = []
        for entry in entries:
            reason = _failure_reason(entry, min_size, require_fresh)
            if reason:
                failures.append((entry, reason))

        attempt = 0
        while failures and attempt < int(retries):
            attempt += 1
            time.sleep(max(0, float(retry_wait)))
            _refresh_directories([entry for entry, _ in failures])
            still_failing = []
            for entry, _ in failures:
                reason = _failure_reason(entry, min_size, require_fresh)
                if reason:
                    still_failing.append((entry, reason))
            failures = still_failing

        if not failures:
            _out("DEADLINE_FRAME_CHECK_PASSED: %d output files verified" % total)
            return

        for entry, reason in failures[:MAX_FAILURE_LINES]:
            _out(
                "Frame check: %s: %s (node %s, frame %s)"
                % (reason, entry["path"], entry["node"], entry["frame"])
            )
        if len(failures) > MAX_FAILURE_LINES:
            _out("... and %d more" % (len(failures) - MAX_FAILURE_LINES))

        _out(
            "DEADLINE_FRAME_CHECK_FAILED: %d of %d expected output files missing or invalid"
            % (len(failures), total)
        )
    except Exception as e:
        _skipped(e)
