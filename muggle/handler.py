#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import io
import os
import PIL.Image
import time
import base64
import traceback
import importlib
from functools import partial
import gradio as gr
from fastapi import Request
from muggle.entity import APIType
from muggle.logger import logger
from typing import TypeVar, Union, Tuple, List, Optional
from muggle.engine.session import project_entities, model_manager
from muggle.engine.project import ProjectEntity
from muggle.exception import ServerException
from muggle.constants import modules_enabled, SYSTEM
from muggle.logic import *
from muggle.utils import Import, Core
from multiprocessing import get_context
from muggle.entity import RequestBody, ResponseBody, ImageEntity, LogEntity
from muggle.pages.utils import BlocksEntities, BlocksFuse
from muggle.config import cli_args


Logic = TypeVar('Logic', bound=BaseLogic)
interface_map = {}

sdk_module = importlib.import_module("muggle.sdk")
# globals().update({k: v for k, v in sdk_module.__dict__.items() if k.endswith("Logic")})
Strategy = sdk_module.SDK


class Handler:

    @classmethod
    def add_logic(cls, logic_module):
        sdk_module.__dict__.update({k: v for k, v in logic_module.__dict__.items() if k.endswith("Logic")})

    @classmethod
    def parse_params(cls, param: RequestBody) -> Tuple[
        str, Union[List[ImageEntity], ImageEntity], Union[List[ImageEntity], ImageEntity, str]
    ]:
        input_images = param.image
        project_name = param.project_name
        title = param.title
        project_config = project_entities.get(project_name)

        if not project_name:
            project_name = list(project_entities.all.keys())[0]
        if not project_config:
            raise RuntimeError(f"项目名 [{project_name}] 不存在")

        if isinstance(input_images, list):
            input_image = [Core.text2image(_) for _ in input_images]
        else:
            input_image = Core.text2image(input_images)

        if title and 'ImageTitle' in project_config.strategy:
            if isinstance(title, list):
                title = [Core.text2image(_) for _ in title]
            else:
                title = Core.text2image(title)
        return project_name, input_image, title

    @classmethod
    def process(
            cls,
            api_type: APIType,
            project_name: str,
            param: RequestBody,
            request: Optional[Request],
            input_image: InputImage,
            title: Title = None,
            **kwargs
    ) -> ResponseBody:
        st = time.time()
        if project_name not in project_entities.all:
            raise ServerException(
                api_type=api_type,
                project_name=project_name,
                request=request,
                message=f"项目名 <{project_name}> 不存在",
                code=4049
            )

        if request and ("Sign" in modules_enabled and api_type != APIType.IMAGE):
            try:
                Import.get_class("Sign").check_sign(request, project_name, param.image, param.sign)
            except ModuleNotFoundError:
                raise ServerException(
                    api_type=api_type,
                    project_name=project_name,
                    request=request,
                    message=f"中间件<Sign>加载失败",
                    code=4040
                )
        # print(request)
        if request:
            ua: str = request.headers.get('user-agent')
            ua = ua if (not ua) or (not ua.startswith("Mozilla")) else "-"
            ip = request.client.host
        else:
            ua = ""
            ip = kwargs.get('remote_ip')
        logic = Strategy.get(project_name, param.extra)
        use_cache = logic.project_config.get('cache')
        log_entity = LogEntity(
            api_type=api_type,
            ip=ip,
            ua=ua,
            project_name=project_name,
            title=title,
        )
        is_text_outputs = (api_type is APIType.TEXT) or (logic.project_entity.outputs in ['text', None])
        if use_cache and "MD5Cache" in modules_enabled and is_text_outputs:
            Import.get_class("MD5Cache").dumps_task()
            if result_data := Import.get_class("MD5Cache").get(input_image.hash):
                consume = (time.time() - st) * 1000
                log_entity.consume = consume
                log_entity.predictions = (result_data, -1)
                logger.info(log_entity.log_text)

                return ResponseBody(
                    uuid=Core.uuid(),
                    data=result_data,
                    consume=consume,
                    score=-1
                )
        try:
            blocks = logic.process(input_image, title=title)
        except RuntimeError as e:
            with open("runtime-error.log", "w") as f:
                f.write(traceback.format_exc())

            raise ServerException(
                message=e,
                code=4049,
                api_type=api_type,
                project_name=project_name,
                request=request
            )

        result_data, score = logic.dumps(blocks)
        if isinstance(score, list) or isinstance(score, tuple):
            score = (sum(score) / len(score)) if score else 0

        consume = (time.time() - st) * 1000
        log_entity.consume = consume
        log_entity.predictions = (blocks if logic.print_process else result_data, score)
        logger.info(log_entity.log_text)

        if 'Charge' in modules_enabled and api_type == APIType.TEXT:
            request_token = param.token
            token = Import.get_class('Charge').get(request_token)
            if not token or not token.available(project_name=project_name):
                raise ServerException(
                    message="中间件<Charge>过程失败: 当前授权不存在或者已过期",
                    code=4053,
                    api_type=api_type,
                    project_name=project_name,
                    request=request
                )
            token.consume()

        if "Draw" in modules_enabled and logic.project_entity.outputs == 'image' and api_type == APIType.IMAGE:
            try:
                img_bytes = Import.get_class('Draw').draw_process(
                    logic, input_image, title, blocks
                )
            except ModuleNotFoundError:
                raise ServerException(
                    message="中间件<Draw>加载失败",
                    code=4041,
                    api_type=api_type,
                    project_name=project_name,
                    request=request
                )
            except NotImplementedError:
                raise ServerException(
                    message="中间件<Draw>过程失败: 逻辑不匹配",
                    code=4043,
                    api_type=api_type,
                    project_name=project_name,
                    request=request
                )
            return ResponseBody(
                uuid=Core.uuid(),
                data=result_data,
                image=img_bytes,
                score=round(score, 3),
                consume=consume
            )

        response = ResponseBody(
            uuid=Core.uuid(),
            data=result_data,
            consume=consume,
            score=round(score, 3)
        )
        if use_cache and "MD5Cache" in modules_enabled:
            Import.get_class("MD5Cache").put(input_image.hash, result_data)
        return response


if 'Sign' in modules_enabled:
    Import.dynamic_import("muggle.middleware.verification.Sign")

if 'MD5Cache' in modules_enabled:
    Import.dynamic_import("muggle.middleware.md5_cache.MD5Cache", instance=True)

if 'Docs' in modules_enabled:
    Import.dynamic_import(
        "muggle.middleware.docs.Docs", instance=True,
        guide_uri=f"/runtime/{cli_args.doc_tag}/guide",
        docs_uri="/runtime/api/{dynamic_token}/docs"
    )
    docs_layout = Import.get_class('Docs').docs_layout
    guide_layout = Import.get_class('Docs').guide_layout
    interface_map["guide"] = guide_layout
    interface_map["docs"] = docs_layout


if 'Draw' in modules_enabled:
    Import.dynamic_import("muggle.middleware.draw.Draw", instance=True, handler=Handler, uri="/preview")
    preview_layout = Import.get_class('Draw').layout
    interface_map["preview"] = preview_layout
else:
    interface = BlocksEntities.empty_blocks()


interface = BlocksFuse(**interface_map)
interface.setting_routes()

if 'Charge' in modules_enabled:
    if SYSTEM == 'Windows':
        token_pool = dict()
    else:
        token_pool = get_context('fork').Manager().dict()
    token_pool.update({})
    Import.dynamic_import("muggle.middleware.charge.Charge", instance=True, ctx=token_pool, interface=interface)

if 'MemoryLoader' in modules_enabled:
    Import.dynamic_import(
        "muggle.middleware.memory_load.MemoryLoader", instance=True,
        handler=Handler,
        model_manager=model_manager,
        interface=interface
    )
    memory_loader = Import.get_class('MemoryLoader')
    memory_loader.iters_crypto_projects()
    # interface.app.add_api_route("/runtime/import/project", memory_loader.logic_route, methods=["POST"])

if cli_args.warm_up:
    Strategy.warm_up_task()
