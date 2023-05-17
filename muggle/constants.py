#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import os
import psutil
import muggle
import webbrowser
from muggle.logger import logger
from muggle.config import SYSTEM, BLACKLIST_FILE, sys_args
from muggle.utils import Core, Exp


app_dir = os.path.dirname(muggle.__file__)

modules_enabled = sys_args['enabled_module']

enable_modules = Exp.get_func(lambda name: name in modules_enabled)


def description():
    if Core.check_port_in_use(sys_args['port']):
        raise RuntimeError('端口已被占用')

    logger.info(
        f'当前启用模块 | {" | ".join(modules_enabled)} |'
    )
    memory_usage = memory_info()
    logger.info(
        f'当前操作系统 {SYSTEM}, '
        f'工作进程: {sys_args["workers"]}, '
        f'工作线程: {sys_args["threads"]}, '
        f'内存占用: {int(memory_usage)} MB'
    )
    if 'Docs' in modules_enabled:
        logger.info(f'调用文档 http://127.0.0.1:{sys_args["port"]}/runtime/{doc_tag}/guide\n')
    if SYSTEM == 'Windows':
        Core.avoid_suspension()
        check_runtime()
        if os.path.exists(".first_time"):
            webbrowser.open(f"http://127.0.0.1:{sys_args['port']}/runtime/{doc_tag}/guide")
            try:
                os.remove(".first_time")
            except Exception as e:
                pass


def check_runtime():
    if not os.path.exists("C:\\Windows\\System32\\vcruntime140_1.dll"):
        builtin_vc_setup = "VC_redist.x64.exe"
        if not os.path.exists(builtin_vc_setup):
            webbrowser.open("https://aka.ms/vs/16/release/VC_redist.x64.exe")
        else:
            logger.info('正在安装 Microsoft Visual C++ Redistributable for Visual Studio 2019, 请稍等...')
            os.system(f"{builtin_vc_setup} /q")
            logger.info('运行时安装完成')


def memory_info():
    process = psutil.Process()
    memory = process.memory_info().rss
    memory_mb = memory / 1024 / 1024
    return memory_mb


if SYSTEM == 'Windows' and sys_args['title']:
    try:
        os.system(f"title {sys_args['title']}")
    except:
        pass

secret_key = sys_args['secret_key']
doc_tag = sys_args['doc_tag']
preview_prompt = sys_args['preview_prompt']

if os.path.exists(BLACKLIST_FILE):
    with open(BLACKLIST_FILE) as file:
        BLACKLIST = set([line.strip() for line in file.readlines()])
else:
    BLACKLIST = set()

IP_COUNTS = {

}

# description()
