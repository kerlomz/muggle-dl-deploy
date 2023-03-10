#!/usr/bin/env python3
# -*- coding:utf-8 -*-
from muggle.package.runner import compile_projects


if __name__ == '__main__':
    compile_projects(include_runtime=False, onefile=True, user_info=None)
