#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import argparse
from muggle.config import SYSTEM, CPU_COUNT, sys_args

cli_parser = argparse.ArgumentParser(description=f'MUGGLE Inference Engine (System: {SYSTEM})')
cli_parser.add_argument(
    '--host', dest='host', default=sys_args.get("host"), type=str,
    help='Server Listening Address (default 0.0.0.0)'
)
cli_parser.add_argument(
    '--port', dest='port', default=sys_args.get("port"), type=int,
    help='Server Listening Port (default 19199)'
)

cli_parser.add_argument(
    '--workers', dest='workers', default=sys_args.get("workers"), type=int,
    help=f'Workers (default {1 if SYSTEM == "Windows" else 4})'
)
cli_parser.add_argument(
    '--threads', dest='threads', default=sys_args.get("threads"), type=int,
    help=f'Threads (default {CPU_COUNT} (physical cpu count))'
)
cli_parser.add_argument(
    '--dirty_data', dest='dirty_data', default=sys_args.get("dirty_data"), type=int,
    help=f'Turn on dirty data to prevent free-rider'
)

# 运行
cli_parser.add_argument('--enabled_module', type=str, nargs='+', default=sys_args.get('enabled_module'))
cli_parser.add_argument("--warm_up", action="store_true", default=sys_args.get('warm_up'))
cli_parser.add_argument('--invoke_route', type=str, default=sys_args.get('invoke_route'))
cli_parser.add_argument('--secret_key', type=str, default=sys_args.get('secret_key'))
cli_parser.add_argument('--title', type=str, default=sys_args.get('title'))
cli_parser.add_argument('--doc_tag', type=str, default=sys_args.get('doc_tag'))
cli_parser.add_argument('--admin', type=str, default=sys_args.get('admin'))
cli_parser.add_argument('--preview_prompt', type=str, default=sys_args.get('preview_prompt'))

cli_args = cli_parser.parse_args()

sys_args.update(
    enabled_module=cli_args.enabled_module,
    warm_up=cli_args.warm_up,
    invoke_route=cli_args.invoke_route,
    secret_key=cli_args.secret_key,
    title=cli_args.title,
    doc_tag=cli_args.doc_tag,
    admin=cli_args.admin,
    preview_prompt=cli_args.preview_prompt,
)
