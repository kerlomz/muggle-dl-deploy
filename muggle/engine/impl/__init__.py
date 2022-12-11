#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import os
import importlib

if os.path.exists("ext/engine"):
    modules_name = [
        (_name := _).split(".")[0]
        for _ in os.listdir("ext/engine")
        if not _.startswith("__") and (_.endswith("py") or _.endswith("pyd") or _.endswith("so"))
    ]
    for module_name in modules_name:
        module = importlib.import_module(f"ext.engine.{module_name}")
        globals().update({k: v for k, v in module.__dict__.items() if k.endswith("Engine")})

if (os.path.exists("ext.pyd") or os.path.exists("ext.so")) and os.path.exists("engine.map"):
    engine_list = open("engine.map", "r", encoding="utf8").read().splitlines()

    for engine_name in engine_list:
        engine_module = importlib.import_module(f"ext.engine.{engine_name}")
        globals().update({k: v for k, v in engine_module.__dict__.items() if k.endswith("Engine")})