#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import uvicorn
import muggle.logger
import logging
from muggle.core.api.cli import cli_args


from gunicorn.app.base import BaseApplication


class GunicornServer(BaseApplication):

    def init(self, parser, opts, args):
        super().__init__()

    def __init__(self, app):
        self.options = {
            'bind': [f'{cli_args.host}:{cli_args.port}'],
            'workers': cli_args.workers,
            'threads': cli_args.threads,
            'worker_class': 'uvicorn.workers.UvicornWorker',
            'max_requests': 1000,
            'timeout': 100,
            'keepalive': 1,
            # "logger_class": "loguru.GunicornLogger"
            # "preload": True
        }
        self.application = app
        super().__init__()

    def load_config(self):
        config = {key: value for key, value in self.options.items()
                  if key in self.cfg.settings and value is not None}
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application