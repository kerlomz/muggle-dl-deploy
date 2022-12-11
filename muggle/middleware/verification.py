#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import hashlib

from muggle.logger import logger
from muggle.exception import ServerException, Request
from muggle.entity import APIType
try:
    from muggle.constants import secret_key
except ImportError:
    logger.warning("当前不支持<Sign>中间件")


class Sign:

    @classmethod
    def get_sign(cls, b64):
        p = b64
        if isinstance(b64, list):
            p = "".join(b64)
        if not p:
            return None
        if len(p) < 100:
            return None
        param = p[:100]
        sign = hashlib.md5("{}{}".format(param, secret_key).encode("utf8")).hexdigest()
        return sign

    @classmethod
    def check_sign(cls, request: Request, project_name: str, param: str, sign: str):
        if sign != cls.get_sign(param):
            raise ServerException(
                api_type=APIType.TEXT,
                project_name=project_name,
                request=request,
                message=f"授权失败",
                code=405
            )

