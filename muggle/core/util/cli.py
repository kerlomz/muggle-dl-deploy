#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import argparse
from muggle.config import SYSTEM, CPU_COUNT, sys_args

cli_parser = argparse.ArgumentParser(description=f'MUGGLE Compile Engine (System: {SYSTEM})')

# 编译
cli_parser.add_argument('--projects', type=str, nargs='+')
cli_parser.add_argument("--onefile", action="store_true")
cli_parser.add_argument("--compile_sdk", action="store_true")
cli_parser.add_argument('--aging', type=float, default=None)
cli_parser.add_argument("--encrypted", action="store_true")
cli_parser.add_argument('--encryption_key', type=str, default=sys_args.get('encryption_key'))

cli_args = cli_parser.parse_args()
