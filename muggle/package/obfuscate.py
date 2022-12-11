#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import os.path

from muggle.package.config import path_join
from stardust.runtime import Runtime

Runtime.dynamic_import("stardust.package")
Compile = Runtime.get_class("Compile")


def write_file(path):
    encrypted_text = Compile.from_file(path)
    open(path, "w", encoding="utf8").write(encrypted_text)


def stardust_obfuscate(build_path):
    write_file(path_join(build_path, "engine", "model.py"))
    # write_file(path_join(build_path, "handler.py"))
    write_file(path_join(build_path, "config.py"))

