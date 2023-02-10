#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import json
import os
import sys
import time
import uuid
import yaml
import base64
import hashlib
import gradio as gr
import gradio.processing_utils
import builtins
import importlib
from collections import OrderedDict
from muggle.engine.project import Path, ProjectEntity
from muggle.engine.model import ModelManager
from stardust.runtime import Runtime
from muggle.config import STARTUP_PARAM
from muggle.logger import logger
from muggle.exception import ServerException
from fastapi import Request
from fastapi.responses import JSONResponse


class MemoryLoader:

    def __init__(self, handler, interface, model_manager: ModelManager):
        self.model_manager: ModelManager = model_manager
        self.handler = handler
        self.interface = interface
        self.setting_route()
        # logger.info("[MemoryLoader] 中间件已加载, 支持项目内存动态加载")

    def setting_route(self):
        self.interface.app.add_api_route("/runtime/import/project", self.logic_route, methods=["POST"])

    def reset_layouts(self, fs):
        create_open_with_fs = Runtime.get_method("create_open_with_fs")
        encode_file_to_base64 = gradio.processing_utils.encode_file_to_base64

        def encode(f, encryption_key=None):
            if fs and f in fs.namelist():
                file_bytes = create_open_with_fs(fs)(f, "rb").read()
                base64_str = base64.b64encode(file_bytes).decode()
                if not os.path.exists(fr := os.path.dirname(f)):
                    os.makedirs(fr)
                if not os.path.exists(f):
                    open(f, "wb").write(file_bytes)
                mimetype = gradio.processing_utils.get_mimetype(f)
                return (
                        "data:"
                        + (mimetype if mimetype is not None else "")
                        + ";base64,"
                        + base64_str
                )
            else:
                return encode_file_to_base64(f, encryption_key)

        gradio.processing_utils.encode_file_to_base64 = encode

        self.interface.reset_layouts()

    @property
    def logic_route(self):
        async def memory_load(request: Request):
            data = await request.body()
            st = time.time()
            try:
                project_name, timer, fs = self.load_project(data)
            except RuntimeError as e:
                return ServerException(e.args[0], 403, request=request).response()
            response = {
                "uuid": str(uuid.uuid4()).replace("-", ""),
                "msg": f"成功导入项目 [{project_name}], 时效 [{(str(int(timer)) + '秒') if timer else '不限'}]",
                "data": "",
                "code": 0,
                "success": True,
                "consume": time.time() - st,
            }
            self.reset_layouts(fs)
            return JSONResponse(response, status_code=200)

        return memory_load

    @classmethod
    def get_logics_map(cls, logic_dir):
        logic_maps = {}

        if logic_dir != 'logic':
            logic_dir = Path.filter(logic_dir[logic_dir.find("projects"):])

        package = logic_dir.replace("./", "").replace("/", ".")
        modules_maps = {
            _.split(".")[0]: Path.join(logic_dir, _)
            for _ in (os.listdir(logic_dir) if os.path.exists(logic_dir) else []) if not _.startswith("__")
        }
        for module_name, path in modules_maps.items():
            # print(f"{package}.{module_name}")
            module = importlib.import_module(f"{package}.{module_name}")
            logic_maps.update({k: path for k, v in module.__dict__.items() if "Logic" in k})
        return logic_maps

    @classmethod
    def find_need_logic(cls, logic_dir, need_logic_name):
        logics_map = cls.get_logics_map(logic_dir)
        for logic_name, path in logics_map.items():
            if need_logic_name == logic_name:
                return path
        return None

    @classmethod
    def export_project(cls, base_crypto, project_entity, root_dir=".", aging=None, dynamic_key=False):
        deadline = (time.time() + aging) if aging and aging != -1 else None
        project_name = project_entity.project_name
        logger.info(f"正在导出项目 [{project_name}], 时效 [{aging if aging and aging != -1 else '不限'}]")
        packages = OrderedDict()
        packages[f"projects/{project_name}/ext_params"] = json.dumps({"deadline": deadline}).encode("utf8")
        for key, model_name in project_entity.models.items():
            model_path = Path.model_path(project_entity.project_path, model_name)
            onnx_path = Path.join(root_dir, model_path.onnx_path)
            crypto_path = Path.join(root_dir, model_path.crypto_path)
            model_cfg_path = Path.join(root_dir, model_path.config_path)
            corpus_path = Path.join(root_dir, model_path.corpus_path)
            category_path = Path.join(root_dir, model_path.category_path)
            packages[
                f"projects/{project_name}/models/{model_name}/model.yaml"
            ] = open(model_cfg_path, "rb").read()
            if os.path.exists(onnx_path):
                packages[
                    f"projects/{project_name}/models/{model_name}/model.onnx"
                ] = open(onnx_path, "rb").read()
            if os.path.exists(crypto_path):
                packages[
                    f"projects/{project_name}/models/{model_name}/model.crypto"
                ] = open(crypto_path, "rb").read()
            if os.path.exists(corpus_path):
                packages[
                    f"projects/{project_name}/models/{model_name}/corpus.dict"
                ] = open(corpus_path, "rb").read()
            if os.path.exists(category_path):
                packages[
                    f"projects/{project_name}/models/{model_name}/categories.label"
                ] = open(category_path, "rb").read()
        project_demo_dir = Path.join(root_dir, project_entity.project_path.demo_dir)
        project_cfg_path = Path.join(root_dir, project_entity.project_path.config_path)
        private_logic_dir = Path.join(root_dir, project_entity.project_path.logic_dir)
        global_logic_dir = Path.join(root_dir, "logic")
        global_logic_path = cls.find_need_logic(global_logic_dir, project_entity.strategy)
        for demo_name in os.listdir(project_demo_dir):
            demo_path = Path.join(project_demo_dir, demo_name)
            packages[
                f".cached_examples/{project_name}/{demo_name}"
            ] = open(demo_path, "rb").read()
        if global_logic_path:
            packages[
                f"projects/{project_name}/logic/logic.py"
            ] = open(global_logic_path, "rb").read()
        private_logic_path = cls.find_need_logic(private_logic_dir, project_entity.strategy)
        if private_logic_path:
            packages[
                f"projects/{project_name}/logic/logic.py"
            ] = open(private_logic_path, "rb").read()

        packages[
            f"projects/{project_name}/project_cfg.yaml"
        ] = open(project_cfg_path, "rb").read()

        base_encryption_key = STARTUP_PARAM.get('encryption_key')
        if dynamic_key:
            password = base_crypto.totp(base_encryption_key.encode("utf8"), aging=1800) + base_encryption_key[::-1]
            password = hashlib.md5(password.encode("utf8")).hexdigest().upper()
            prefix = b"1"
        else:
            password = base_encryption_key[::-1]
            prefix = b"0"
        encrypted_files = base_crypto.compress(
            tree=packages,
            password=password
        )
        compile_dir = Path.join(root_dir, "compile_projects")
        if not os.path.exists(compile_dir):
            os.makedirs(compile_dir)
        open(Path.join(compile_dir, f"{project_name}.crypto"), "wb").write(prefix+encrypted_files)

    def iters_crypto_projects(self):
        if not os.path.exists("compile_projects"):
            return
        for project_file in os.listdir("compile_projects"):
            if not project_file.endswith(".crypto"):
                continue
            try:
                project_bytes = open(Path.join("compile_projects", project_file), "rb").read()
                project_name, timer, fs = self.load_project(project_bytes)
                self.reset_layouts(fs)
            except Exception as e:
                logger.error(f"编译项目 [{project_file}] 加载失败: {e}")

    @classmethod
    def export_projects(cls, need_projects, root_dir=".", aging=None):
        Runtime.dynamic_import("stardust.crypto_utils")
        base_crypto = Runtime.get_class('BaseCrypto')
        from muggle.engine.session import project_entities
        for project_name in need_projects:
            project_entity = project_entities.get(project_name)
            cls.export_project(base_crypto, project_entity, root_dir, aging=aging)

    def load_project(self, project_crypto: bytes):
        Runtime.dynamic_import("stardust.crypto_utils")
        base_crypto = Runtime.get_class('BaseCrypto')
        create_open_with_fs = Runtime.get_method("create_open_with_fs")
        dynamic_flag, project_crypto = project_crypto[:1], project_crypto[1:]
        base_encryption_key = STARTUP_PARAM.get('encryption_key')
        if dynamic_flag == b'0':
            password = base_encryption_key[::-1]
        elif dynamic_flag == b'1':
            password = base_crypto.totp(base_encryption_key.encode("utf8"), aging=1800) + base_encryption_key[::-1]
            password = hashlib.md5(password.encode("utf8")).hexdigest().upper()
        else:
            # print(dynamic_flag)
            raise RuntimeError("加密模型格式异常") from None
        fs = base_crypto.decompress(
            project_crypto,
            password
        )
        project_name = fs.namelist()[0].split("/")[1]
        _open = create_open_with_fs(fs)
        ext_params = json.loads(_open(f'projects/{project_name}/ext_params', "r", encoding="utf8").read())
        deadline = ext_params['deadline']
        timer = None
        if isinstance(deadline, float):
            timer = deadline - time.time()
            if timer < 0:
                raise RuntimeError("该项目已过时效") from None

        project_cfg = yaml.load(
            "".join(_open(f"projects/{project_name}/project_cfg.yaml", "r", encoding="utf8").read()),
            Loader=yaml.SafeLoader
        )
        project_cfg['input_images'] = []
        project_cfg['title_images'] = []

        if self.model_manager.project_entities.get(project_name):
            # logger.warning(f"项目 [{project_name}] 已存在")
            raise RuntimeError(f"项目 [{project_name}] 已存在")
        for filepath in fs.namelist():

            if filepath.startswith(f"projects/{project_name}/models"):
                continue

            if filepath.endswith("logic.py"):
                logic_code = _open(filepath, "r", encoding="utf8").read()
                logic_module = type(sys)('logic')
                try:
                    exec(logic_code, logic_module.__dict__)
                    self.handler.add_logic(logic_module)
                except Exception as e:
                    raise RuntimeError(f"[Logic] 加载失败 {e}")

            demo_image_dir = f".cached_examples/{project_name}/image"
            demo_title_dir = f".cached_examples/{project_name}/title"
            if filepath.startswith(demo_image_dir):
                if not os.path.exists(demo_image_dir):
                    os.makedirs(demo_image_dir)
                open(filepath, "wb").write(_open(filepath, "rb").read())
                project_cfg['input_images'].append(filepath)
            if filepath.startswith(demo_title_dir):
                if not os.path.exists(demo_title_dir):
                    os.makedirs(demo_title_dir)
                open(filepath, "wb").write(_open(filepath, "rb").read())
                filename = os.path.basename(filepath)
                idx = int(filename.split(".")[0].split("_")[1]) if filename.startswith("title_") else 0
                self.model_manager.project_entities.iter_image_titles(
                    project_cfg,
                    idx,
                    filepath,
                )

        project_entity = ProjectEntity(project_name=project_name, cfg=project_cfg)
        self.model_manager.project_entities.add(project_name, project_entity)
        for _, model_name in project_entity.models.items():
            self.model_manager.add_model(project_name, model_name, open_fn=_open, fs=fs)
        if timer:
            self.model_manager.timer_release(project_name, seconds=timer)

        msg = f"项目 [{project_name}] 导入成功, 时效 [{(str(int(timer)) + ' 秒') if timer else '不限'}]"
        logger.info(msg)
        return project_name, timer, fs
