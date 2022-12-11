#!/usr/bin/env python3
# -*- coding:utf-8 -*-
from pip._internal.cli.main import main


if __name__ == '__main__':
    main("install --upgrade pip".split(" "))
    main("install muggle/package/lib/gunicorn-master.zip --no-cache-dir --force-reinstall".split(" "))
    main("install -r requirements.txt -i https://mirrors.cloud.tencent.com/pypi/simple".split(" "))
    main('install Nuitka'.split(" "))