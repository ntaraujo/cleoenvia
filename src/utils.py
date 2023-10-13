from collections import defaultdict
import appdirs
import os
import json
import contextlib
import sys
import builtins
import pickle
import win32clipboard
import time
import random

_current_progress = 0
_total_progress = 0


def add_total(total_progress):
    global _total_progress
    _total_progress += total_progress


def add_progress(progress=1):
    global _current_progress
    _current_progress += progress
    print(f"Progress: {_current_progress}/{_total_progress}")


def progress_for(func, total_progress=None):
    if total_progress is not None:
        add_total(total_progress)

    def new_func(*args, **kwargs):
        res = func(*args, **kwargs)
        add_progress()
        return res

    return new_func


config_dir = appdirs.user_config_dir("cleoenvia")
config_path = os.path.join(config_dir, "config.pkl")


def save_config(config):
    os.makedirs(config_dir, exist_ok=True)
    with open(config_path, "wb") as f:
        pickle.dump(config, f)


def load_config():
    if os.path.exists(config_path):
        with contextlib.suppress(json.JSONDecodeError):
            with open(config_path, "rb") as f:
                return pickle.load(f)
    return defaultdict(str)


cache_dir = appdirs.user_cache_dir("cleoenvia")


def save_cache(name, data):
    with open(os.path.join(cache_dir, f"{name}.pkl"), "wb") as f:
        pickle.dump(data, f)


def load_cache(file_name, default):
    cache_path = os.path.join(cache_dir, f"{file_name}.pkl")
    if not os.path.exists(cache_path):
        return default
    with open(cache_path, "rb") as f:
        return pickle.load(f)


compiled = getattr(sys, "frozen", False)


def path(file):
    return os.path.join(sys._MEIPASS, file) if compiled else file


# TODO try to substitute by https://github.com/chriskiehl/Gooey/issues/665

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
    kwargs["flush"] = True

    old_print(*new_values, **kwargs)


builtins.print = new_print


def send_to_clipboard(data, clip_type="text"):
    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()

        if clip_type == "text":
            clip_type = win32clipboard.CF_UNICODETEXT
        elif clip_type == "image":
            clip_type = win32clipboard.CF_DIB
        win32clipboard.SetClipboardData(clip_type, data)
    finally:
        win32clipboard.CloseClipboard()


debugger_active = getattr(sys, "gettrace", lambda: None)() is not None
if debugger_active:
    print("Rodando em modo de depuração")


def retry(func, exc=Exception, times=2, wait=1, on_debug=False):
    if not on_debug and debugger_active:
        return func

    def new_func(*args, **kwargs):
        for t in range(times):
            try:
                return func(*args, **kwargs)
            except exc as e:
                print(f"Erro suprimido. Tentando novamente. ({t+1}/{times})")
                if debugger_active:
                    print(f"\n{type(e).__name__}\n{e}")
                time.sleep(wait)
        return func(*args, **kwargs)

    return new_func


def random_intervals(len_, sum_min, sum_max, min_):
    sequence = [random.uniform(min_, sum_max / len_) for _ in range(len_)]
    while sum(sequence) < sum_min:
        index = random.randint(0, len_ - 1)
        sequence[index] += 0.01
    return sequence


def class_exc_waiting(func, seconds_attr="_next_interval"):
    def new_func(self, *args, **kwargs):
        start = time.time()
        res = func(self, *args, **kwargs)
        seconds = getattr(self, seconds_attr)
        while time.time() - start < seconds:
            pass
        return res

    return new_func
