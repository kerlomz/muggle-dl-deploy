#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import os
import psutil
import muggle
import webbrowser
from muggle.logger import logger
from muggle.config import SYSTEM, cli_args
from muggle.utils import Core

app_dir = os.path.dirname(muggle.__file__)

modules_enabled = cli_args.enabled_module


def description():
    # cli_args.port = 19196
    if Core.check_port_in_use(cli_args.port):
        raise RuntimeError('端口已被占用')
    # logger.info(f"MUGGLE-DEPLOY - 作者 QQ: 27009583")
    # logger.info(f'服务器已启动监听 http://0.0.0.0:{cli_args.port}')
    logger.info(
        f'当前启用模块 | {" | ".join(modules_enabled)} |'
    )
    memory_usage = memory_info()
    logger.info(
        f'当前操作系统 {SYSTEM}, 工作进程: {cli_args.workers}, 工作线程: {cli_args.threads}, 内存占用: {int(memory_usage)} MB'
    )
    if not globals().get('hide_doc'):
        logger.info(f'调用文档 http://127.0.0.1:{cli_args.port}/runtime/{doc_tag}/guide\n')
    if SYSTEM == 'Windows':
        Core.avoid_suspension()
        check_runtime()
        if os.path.exists(".first_time"):
            webbrowser.open(f"http://127.0.0.1:{cli_args.port}/runtime/{doc_tag}/guide")
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


if SYSTEM == 'Windows' and cli_args.title:
    try:
        os.system(f"title {cli_args.title}")
    except:
        pass

secret_key = cli_args.secret_key
doc_tag = cli_args.doc_tag
preview_prompt = cli_args.preview_prompt

# description()
