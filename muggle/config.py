import json
import os
import sys
import argparse
import platform
import onnxruntime
import multiprocessing
import muggle
import yaml

MUGGLE_DIR = os.path.dirname(muggle.__file__)
CPU_COUNT = multiprocessing.cpu_count()
# PLATFORM = onnxruntime.get_device()  # CPU / GPU ...
SYSTEM = platform.system()  # Windows ...
IS_ADVANCED_PLATFORM = SYSTEM != "Windows"
STARTUP_PARAM = {
    "engine-backend": 'ONNXRuntime',
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
    STARTUP_PARAM.update(yaml.load(open(STARTUP_PARAM_FILE, "r", encoding="utf8").read(), Loader=yaml.SafeLoader))

cli_parser = argparse.ArgumentParser(description=f'MUGGLE Inference Engine (System: {SYSTEM})')
cli_parser.add_argument(
    '--host', dest='host', default=STARTUP_PARAM.get("host"), type=str,
    help='Server Listening Address (default 0.0.0.0)'
)
cli_parser.add_argument(
    '--port', dest='port', default=STARTUP_PARAM.get("port"), type=int,
    help='Server Listening Port (default 19199)'
)

cli_parser.add_argument(
    '--engine-backend', dest='engine', default=STARTUP_PARAM.get("engine-backend"), type=str,
    help='Engine Backend (OpenVINO, ONNXRuntime)'
)

cli_parser.add_argument(
    '--workers', dest='workers', default=STARTUP_PARAM.get("workers"), type=int,
    help=f'Workers (default {1 if SYSTEM == "Windows" else 4})'
)
cli_parser.add_argument(
    '--threads', dest='threads', default=STARTUP_PARAM.get("threads"), type=int,
    help=f'Threads (default {CPU_COUNT} (physical cpu count))'
)
cli_parser.add_argument(
    '--dirty_data', dest='dirty_data', default=STARTUP_PARAM.get("dirty_data"), type=int,
    help=f'Turn on dirty data to prevent free-rider'
)
# 编译
cli_parser.add_argument('--projects', type=str, nargs='+')
cli_parser.add_argument("--onefile", action="store_true")
cli_parser.add_argument("--compile_sdk", action="store_true")
cli_parser.add_argument('--aging', type=float, default=None)
cli_parser.add_argument("--encrypted", action="store_true")
cli_parser.add_argument('--encryption_key', type=str, default=STARTUP_PARAM.get('encryption_key'))

# 运行
cli_parser.add_argument('--enabled_module', type=str, nargs='+', default=STARTUP_PARAM.get('enabled_module'))
cli_parser.add_argument("--warm_up", action="store_true", default=STARTUP_PARAM.get('warm_up'))
cli_parser.add_argument('--invoke_route', type=str, default=STARTUP_PARAM.get('invoke_route'))
cli_parser.add_argument('--secret_key', type=str, default=STARTUP_PARAM.get('secret_key'))
cli_parser.add_argument('--title', type=str, default=STARTUP_PARAM.get('title'))
cli_parser.add_argument('--doc_tag', type=str, default=STARTUP_PARAM.get('doc_tag'))
cli_parser.add_argument('--admin', type=str, default=STARTUP_PARAM.get('admin'))
cli_parser.add_argument('--preview_prompt', type=str, default=STARTUP_PARAM.get('preview_prompt'))
cli_parser.add_argument('--use_builtin_corpus', action="store_true", default=STARTUP_PARAM.get('use_builtin_corpus'))
cli_args = cli_parser.parse_args()

__all__ = ['cli_args', 'SYSTEM', 'IS_ADVANCED_PLATFORM', 'resource_path']
