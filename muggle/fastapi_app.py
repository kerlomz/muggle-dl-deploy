#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import os
import PIL
from muggle.handler import Handler, interface
from muggle.entity import APIType
from muggle.exception import ImageException, ServerException
from muggle.config import cli_args, BLACKLIST
from muggle.constants import description
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from muggle.entity import RequestBody, missing_request_param
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY
from fastapi.exceptions import RequestValidationError

app = interface.app
description()
app_dir = os.path.dirname(__file__)


# @app.middleware("http")
# async def block_ips(request: Request, call_next):
#     client_host = request.client.host
#
#     if client_host in BLACKLIST:
#         return ServerException(
#             message="Forbidden",
#             code=403,
#             api_type=None,
#             project_name=None,
#             request=request,
#             is_print=False
#         ).response()
#
#     response = await call_next(request)
#     return response


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(
        request: Request, e: RequestValidationError
) -> JSONResponse:
    detail = e.errors()
    return ServerException(
        message=detail,
        code=HTTP_422_UNPROCESSABLE_ENTITY,
        api_type=None,
        project_name=None,
        request=request,
    ).response()


@app.exception_handler(500)
async def error_handler(request: Request, e):
    error_info = f'{e.__class__.__name__}: {str(e)}'
    return ServerException(
        message=error_info,
        code=500,
        api_type=None,
        project_name=None,
        request=request,
    ).response()


@app.exception_handler(405)
async def error_handler(request: Request, e):
    return ServerException(
        message="Method Not Allowed",
        code=500,
        api_type=None,
        project_name=None,
        request=request,
    ).response()


@app.post(cli_args.invoke_route)
async def invoke(request: Request, body: RequestBody):
    missing_entity = missing_request_param(["project_name", "image"], body)
    if missing_entity.is_missing:
        return ServerException(
            message=f"Missing parameters [{', '.join(missing_entity.names)}]",
            code=400,
            api_type=None,
            project_name=None,
            request=request,
        ).response()
    try:
        project_name, input_image, title = Handler.parse_params(body, request)
    except PIL.UnidentifiedImageError:
        return ImageException(
            api_type=APIType.TEXT,
            request=request,
            project_name=body.project_name,
            message=f"图片无法识别",
            code=5001
        ).response()
    except RuntimeError as e:
        return ServerException(
            message=e.args[0],
            code=500,
            api_type=APIType.TEXT,
            project_name=None,
            request=request,
        ).response()
    try:
        r = Handler.process(APIType.TEXT, project_name, body, request, input_image, title)
    except ServerException as e:
        return e.response()

    response = {
        "uuid": r.uuid,
        "msg": "",
        "data": r.data,
        "code": 0,
        "success": True,
        "consume": r.consume,
        "score": r.score
    }
    return JSONResponse(response, status_code=200)
