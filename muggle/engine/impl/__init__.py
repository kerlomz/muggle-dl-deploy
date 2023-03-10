#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import os
import importlib
from muggle.logger import logger

if os.path.exists("ext/engine"):
    modules_name = [
        (_name := _).split(".")[0]
        for _ in os.listdir("ext/engine")
        if not _.startswith("__") and (_.endswith("py") or _.endswith("pyd") or _.endswith("so"))
    ]
    for module_name in modules_name:
        module = importlib.import_module(f"ext.engine.{module_name}")
        globals().update({k: v for k, v in module.__dict__.items() if k.endswith("Engine")})

if os.path.exists("ext.pyd") or os.path.exists("ext.so"):
    loader = importlib.import_module(f"ext.loader")
    engine_list = getattr(loader, 'engine_list')
    user_info = getattr(loader, 'user_info')
    if user_info:
        logger.info(f"-----------<{user_info}>-------------")

    for engine_name in engine_list:
        engine_module = importlib.import_module(f"ext.engine.{engine_name}")
        globals().update({k: v for k, v in engine_module.__dict__.items() if k.endswith("Engine")})
