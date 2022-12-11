#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import os
import shutil
import time
import yaml
import tempfile

project_path = "projects"

build_path = os.path.join(tempfile.gettempdir(), f"muggle_build")
dist_path = os.path.join(tempfile.gettempdir(), f"muggle_dist")


if not os.path.exists(dist_path):
    os.makedirs(dist_path)


def path_join(parent, child, *args):
    return os.path.join(parent, child, *args).replace("\\", "/")


