#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import json
import time
import os.path
import threading
from muggle.logger import logger


class MD5Cache:

    FILENAME = ".cache"

    def __init__(self):
        self.cache_pool = globals().get("cache_from_file") if "cache_from_file" in globals() else {}
        self.is_started = False

    def put(self, key, value):
        self.cache_pool[key] = value

    def get(self, key):
        return self.cache_pool.get(key)

    def dumps(self):
        logger.info("正在写入缓存文件")
        with open(MD5Cache.FILENAME, "w", encoding="utf8") as f:
            f.write(json.dumps(self.cache_pool, ensure_ascii=False))

    def dumps_task(self):
        if self.is_started:
            return
        self.is_started = True

        def func():
            while True:
                try:
                    self.dumps()
                except KeyboardInterrupt:
                    break
                time.sleep(300)

        threading.Timer(interval=60, function=func).start()


if os.path.exists(MD5Cache.FILENAME):
    try:
        cache_from_file = json.loads(open(MD5Cache.FILENAME, "r", encoding="utf8").read())
    except:
        cache_from_file = {}


