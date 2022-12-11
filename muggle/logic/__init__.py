#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import os
import importlib
from muggle.logic.click import *
from muggle.logic.cls import *
from muggle.logic.ctc import *
from muggle.logic.jigsaw import *
from muggle.logic.reg import *

extra_logics = []

if os.path.exists("logic"):
    modules_name = [
        (_name := _).split(".")[0]
        for _ in os.listdir("logic")
        if not _.startswith("__") and (_.endswith("py") or _.endswith("pyd") or _.endswith("so"))
    ]
    for module_name in modules_name:
        module = importlib.import_module(f"logic.{module_name}")
        globals().update({k: v for k, v in module.__dict__.items() if k.endswith("Logic")})

__all__ = [k for k, v in globals().items() if k.endswith("Logic")] + ['InputImage', 'Title']
