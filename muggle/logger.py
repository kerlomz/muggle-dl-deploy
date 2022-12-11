#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import os.path
from loguru import logger
import loguru

log_path = "logs"
if not os.path.exists(log_path):
    os.makedirs(log_path)

error_logfile = 'logs/critical-error.log'

logger.add(error_logfile, filter=lambda x: 'ERROR' in x['message'])