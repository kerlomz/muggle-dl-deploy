#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import os
import time
import uuid
import datetime
from fastapi import Request
from fastapi.responses import JSONResponse
from muggle.exception import ServerException
from muggle.config import STARTUP_PARAM


class Ageing:

    def __init__(self, seconds=0, minutes=0, hours=0, days=0):
        self.seconds = int(seconds) + int(minutes) * 60 + int(hours) * 60 * 60 + int(days) * 60 * 60 * 24


class Token:

    def __init__(self, quota: int = 0, ageing: Ageing = Ageing(), project_name: str = None):
        self.quota: int = quota
        self.project_name: str = project_name
        self.ageing: Ageing = ageing
        self.start_time = datetime.datetime.now()
        self.expired_time = self.start_time + datetime.timedelta(seconds=ageing.seconds)

    def info(self):
        return {
            "quota": self.quota,
            "project_name": self.project_name,
            "remain_time": self.remain_time(),
            "is_expire": self.is_expire()
        }

    def is_expire(self):
        return self.expired_time - datetime.datetime.now() < datetime.timedelta(seconds=1)

    def consume(self):
        self.quota -= 1

    def available(self, project_name: str):
        return self.quota > 0 and not self.is_expire() and project_name == self.project_name

    @staticmethod
    def seconds_to_dhms(seconds):
        days = int(seconds // (3600 * 24))
        hours = int((seconds // 3600) % 24)
        minutes = int((seconds // 60) % 60)
        seconds = int(seconds % 60)
        return days, hours, minutes, seconds

    def remain_time(self):
        remain_time = self.expired_time - datetime.datetime.now()
        days, hours, minutes, seconds = self.seconds_to_dhms(remain_time.total_seconds())
        if remain_time < datetime.timedelta(seconds=1):
            return '0 天 0 时 0 分 0 秒'
        return f'{days} 天 {hours} 时 {minutes} 分 {seconds} 秒'


class Charge:

    def __init__(self, ctx, interface):
        self.ctx = ctx
        self.interface = interface
        self.setting_route()

    def add(self, token_id, quota, project_name, seconds=0, minutes=0, hours=0, days=0):
        self.ctx[token_id] = Token(
            quota=quota,
            project_name=project_name,
            ageing=Ageing(seconds=seconds, minutes=minutes, hours=hours, days=days)
        )
        return self.ctx[token_id].info()

    def all_info(self):
        return {k: v.info() for k, v in self.ctx.items()}

    def get(self, uid) -> Token:
        return self.ctx.get(uid)

    def setting_route(self):
        self.interface.app.add_api_route(
            f"/runtime/{STARTUP_PARAM.get('doc_tag')}/display", self.display_route, methods=["GET"]
        )

    @property
    def display_route(self):

        async def display(request: Request):
            st = time.time()
            try:
                all_data = self.all_info()
            except RuntimeError as e:
                return ServerException(e.args[0], 403, request=request).response()
            response = {
                "uuid": str(uuid.uuid4()).replace("-", ""),
                "msg": f"",
                "data": all_data,
                "code": 0,
                "success": True,
                "consume": time.time() - st,
            }
            return JSONResponse(response, status_code=200)

        return display


if __name__ == '__main__':
    pass