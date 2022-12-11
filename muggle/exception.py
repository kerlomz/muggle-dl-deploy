#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# Author: kerlomz <kerlomz@gmail.com>
import os
from muggle.logger import logger
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Union, TypeVar, Iterator
from muggle.entity import APIType
from fastapi import Request
from fastapi.responses import JSONResponse

executor = ThreadPoolExecutor(5)


class ServerException(BaseException):

    @property
    def uuid(self):
        return str(uuid.uuid4()).replace("-", "")

    def __init__(
            self,
            message,
            code: int,
            api_type: APIType = None,
            project_name: str = None,
            request: Request = None,
            remote_ip: str = None
    ):
        super().__init__(message)

        self.message = message
        self.code = code
        self.request = request
        self.current_uuid = self.uuid
        log_text = ""
        if api_type:
            log_text += f"{api_type} | "
        if self.request:
            ua: str = self.request.headers.get('user-agent')
            ua = ua if (not ua) or (not ua.startswith("Mozilla")) else "-"
            log_text += f"IP [{self.request.client.host}] | "
            log_text += f"UA [{ua}] | "
        if not self.request and remote_ip:
            log_text += f"IP [{remote_ip}] | "
        if project_name:
            f"[{project_name}] | "
        log_text += f"ERROR [{message}] "
        log_text += f"DETAIL [{self.current_uuid}]"
        logger.error(log_text)

    def response(self):
        return JSONResponse(
            content={
                "uuid": self.current_uuid,
                "msg": self.message,
                "data": "",
                "success": False,
                "code": self.code
            },
            status_code=self.code if 100 < self.code < 600 else 500
        )


class ImageException(ServerException):

    def __init__(
            self,
            message,
            code: int,
            api_type: APIType = None,
            project_name: str = None,
            request: Request = None
    ):
        super(ImageException, self).__init__(message, code, api_type, project_name, request)


class BusinessException(ServerException):

    def response(self):
        return {
            "uuid": self.uuid,
            "data": f"{self.message}",
            "success": False,
            "code": self.code
        }


class ModelException(Exception):

    def __init__(self, model_name, prompt, message, code: int):
        super().__init__(message)
        self.message = message
        self.code = code
        self.prompt = prompt
        self.model_name = model_name
        logger.error(f"[Unable to load model] [{model_name}] | ERROR[{self.prompt}]")

    def response(self):
        return {
            "data": f"Unable to load model [{self.model_name}] | ({self.message})",
            "success": False,
            "code": self.code
        }


class ProjectException(Exception):

    def __init__(self, project_name, prompt, message, code: int):
        super().__init__(message)
        self.message = message
        self.code = code
        self.prompt = prompt
        self.project_name = project_name
        logger.error(f"[Unable to load project] [{project_name}] | ERROR[{self.prompt}]")

    def response(self):
        return {
            "data": f"Unable to load project [{self.project_name}] | ({self.message})",
            "success": False,
            "code": self.code
        }
