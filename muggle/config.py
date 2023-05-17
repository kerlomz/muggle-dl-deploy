import json
import os
import sys
import argparse
import platform
import onnxruntime
import multiprocessing
import muggle
import yaml
import types

MUGGLE_DIR = os.path.dirname(muggle.__file__)
CPU_COUNT = multiprocessing.cpu_count()
# PLATFORM = onnxruntime.get_device()  # CPU / GPU ...
SYSTEM = platform.system()  # Windows ...

sys_args = {
    "engine_backend": 'ONNXRuntime',
    "workers": 1 if SYSTEM == 'Windows' else 4,
    "threads": CPU_COUNT,
    "port": 19199,
    "host": "0.0.0.0",
    "enabled_module": ['Draw', 'Docs', 'MemoryLoader'],
    "invoke_route": "/runtime/text/invoke",
    "secret_key": "@",
    "title": "muggle-deploy",
    "doc_tag": "api",
    "preview_prompt": "",
    "use_builtin_corpus": True,
    "encryption_key": "@~-X(193)!",
    "dirty_data": False,
    "warm_up": True,
    "admin": ""
}
# print(STARTUP_PARAM)
STARTUP_PARAM_FILE = "startup_param.yaml"
BLACKLIST_FILE = "blacklist.txt"


def resource_path(relative_path):
    if os.path.exists(relative_path):
        return relative_path
    try:
        # Nuitka temp folder
        base_path = os.path.dirname(__file__)
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


if os.path.exists(STARTUP_PARAM_FILE):
    sys_args.update(yaml.load(open(STARTUP_PARAM_FILE, "r", encoding="utf8").read(), Loader=yaml.SafeLoader))


__all__ = ['SYSTEM', 'sys_args', 'CPU_COUNT', 'MUGGLE_DIR', 'BLACKLIST_FILE', 'resource_path', 'sys_args']
