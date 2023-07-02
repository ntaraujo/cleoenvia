import appdirs
import os
import json
import contextlib
import sys
import builtins

_current_progress = 0
_total_progress = 0


def progress_for(func, total_progress=None):
    if total_progress is not None:
        global _total_progress
        _total_progress += total_progress

    def new_func(*args, **kwargs):
        res = func(*args, **kwargs)
        global _current_progress
        _current_progress += 1
        print(f"Progress: {_current_progress}/{_total_progress}")
        return res

    return new_func


def add_total(total_progress):
    global _total_progress
    _total_progress += total_progress


def add_progress(progress=1):
    global _current_progress
    _current_progress += progress
    print(f"Progress: {_current_progress}/{_total_progress}")


config_dir = appdirs.user_config_dir("cleoenvia")
config_path = os.path.join(config_dir, "config.json")


cache_dir = appdirs.user_cache_dir("cleoenvia")


def save_config(config):
    os.makedirs(config_dir, exist_ok=True)
    with open(config_path, "w") as f:
        json.dump(config, f)


def load_config():
    if os.path.exists(config_path):
        with contextlib.suppress(json.JSONDecodeError):
            with open(config_path, "r") as f:
                return json.load(f)


compiled = getattr(sys, "frozen", False)


def path(file):
    return os.path.join(sys._MEIPASS, file) if compiled else file


old_print = builtins.print


def new_print(*values, **kwargs):
    new_values = []
    for value in values:
        if not isinstance(value, str):
            value = str(value)
        new_values.append(value.encode("ascii", "replace").decode())
    if "sep" in kwargs:
        kwargs["sep"] = kwargs["sep"].encode("ascii", "replace").decode()
    if "end" in kwargs:
        kwargs["end"] = kwargs["end"].encode("ascii", "replace").decode()

    old_print(*new_values, **kwargs)


builtins.print = new_print
