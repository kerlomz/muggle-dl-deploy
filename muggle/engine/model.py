#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import builtins
import hashlib
import os
import time

import yaml
import base64
import threading
import PIL.Image
import PIL.GifImagePlugin
import onnxruntime
import numpy as np
from abc import abstractmethod
from muggle.logger import logger
from typing import List, Tuple, Dict, Union, TypeVar, Set
from dataclasses import dataclass, field
from muggle.config import cli_args, STARTUP_PARAM, MUGGLE_DIR
from muggle.engine.utils import Path, MODEL_PATH, PROJECT_PATH
from muggle.entity import RuntimeType
from muggle.exception import ModelException
from muggle.engine.project import ProjectEntity, ProjectEntities
from muggle.categories import CATEGORIES_MAP


RUNTIME_MAP = {
    'ONNXRuntime': RuntimeType.ONNXRuntime,
}

try:
    from stardust.runtime import Runtime

    Runtime.dynamic_import("stardust.crypto_utils")
    BaseCrypto = Runtime.get_class('BaseCrypto')
    create_open_with_fs = Runtime.get_method("create_open_with_fs")
    logger.info("[StarDust] 框架已加载, 支持加密模型")
    encrypted_model_supported = True
except Exception as e:
    encrypted_model_supported = False
    logger.warning("[StarDust] 框架未加载, 暂不支持加密模型")
    logger.warning(f'{e}')


InputShape = tuple[str, Union[int, str], int, int]
ImageSize = tuple[int, int]

GifImage = PIL.GifImagePlugin.GifImageFile
InputImage = Union[PIL.Image.Image, GifImage]
InputImages = List[PIL.Image.Image]


class RuntimeEngine:

    def __init__(self, path_or_bytes: Union[bytes, str]):
        self.path_or_bytes = path_or_bytes
        self._hash = None
        self._session = None

    @property
    @abstractmethod
    def hash(self):
        pass

    @property
    def session(self):
        if not hasattr(self, '_session') or self._session is None:
            raise RuntimeError("引擎已卸载或尚未初始化")
        return self._session

    @classmethod
    @abstractmethod
    def cuda_available(cls): pass

    @property
    @abstractmethod
    def input_shape(self) -> InputShape: pass

    @property
    @abstractmethod
    def input_shapes(self) -> List[InputShape]: pass

    @abstractmethod
    def run(self, *input_arr):
        pass

    def release(self):
        if self._session is None:
            raise RuntimeError("引擎已卸载或尚未初始化")
        del self._session
        del self


class ONNXRuntimeEngine(RuntimeEngine):

    def __init__(self, model_bytes):
        super(ONNXRuntimeEngine, self).__init__(model_bytes)
        self.sess_options = onnxruntime.SessionOptions()

        # self.sess_options.execution_mode = onnxruntime.ExecutionMode.ORT_SEQUENTIAL
        # self.sess_options.intra_op_num_threads = multiprocessing.cpu_count()
        # self.sess_options.inter_op_num_threads = 24
        # self.sess_options.intra_op_num_threads = multiprocessing.cpu_count() // 2
        # self.sess_options.graph_optimization_level = onnxruntime.GraphOptimizationLevel.ORT_ENABLE_ALL
        # self.sess_options.execution_mode = onnxruntime.ExecutionMode.ORT_PARALLEL
        # self.model_bytes = model_bytes
        self.set_session(self.path_or_bytes)
        self.outputs_names = [_.name for _ in self.session.get_outputs()]
        self.inputs_names = [_.name for _ in self.session.get_inputs()]
        # self.warm_up()

    @property
    def hash(self) -> str:
        if not self._hash:
            raise RuntimeError(f"[ONNXRuntimeEngine] 尚未初始化")
        return self._hash

    def set_session(self, model_bytes):
        sess_options = onnxruntime.SessionOptions()
        providers = [p for p in onnxruntime.get_available_providers() if p in [
            'CUDAExecutionProvider', 'CPUExecutionProvider'
        ]]
        self._session = onnxruntime.InferenceSession(
            model_bytes, sess_options, providers=providers
        )
        self._hash = hashlib.md5(self.path_or_bytes).hexdigest()
        self._session._model_bytes = None
        self.path_or_bytes = None

    @property
    def input_shape(self) -> InputShape:
        inputs = self.session.get_inputs()[0]
        return tuple(inputs.shape)

    @property
    def input_shapes(self) -> List[InputShape]:
        return [tuple(_.shape) for _ in self.session.get_inputs()]

    @classmethod
    def cuda_available(cls):
        return 'CUDAExecutionProvider' in onnxruntime.get_available_providers() and onnxruntime.get_device() == 'GPU'

    def run(self, *input_arr):
        return self.session.run(
            self.outputs_names, {input_name: input_arr[idx] for idx, input_name in enumerate(self.inputs_names)}
        )


RuntimeEngineType = TypeVar('RuntimeEngineType', bound=RuntimeEngine)


class RuntimeManager:

    def __init__(self):
        self.engine_type: RuntimeType = RUNTIME_MAP[cli_args.engine]
        self.session_map = {}
        if self.engine_type == RuntimeType.ONNXRuntime:
            self.runtime_engine = ONNXRuntimeEngine
        else:
            raise ModelException("-", 'EngineTypeError', f'引擎 [{self.engine_type}] 不存在', 9002)
        cuda_available = self.runtime_engine.cuda_available()
        logger.info(f'当前设备类型 [{"GPU" if cuda_available else "CPU"}]')

    @classmethod
    def read_model(cls, model_path, independent_key=None, open_fn=builtins.open):
        ext = os.path.splitext(model_path)[-1]
        if ext == '.crypto':
            encrypted_files = open_fn(model_path, "rb").read()
            fs = BaseCrypto.decompress(
                encrypted_files,
                STARTUP_PARAM.get('encryption_key') if not independent_key else independent_key
            )
            model_bytes = create_open_with_fs(fs)(model_path, "rb").read()
        else:
            model_bytes = open_fn(model_path, "rb").read()
        return model_bytes

    @classmethod
    def calc_hash(cls, model_bytes):
        return hashlib.md5(model_bytes).hexdigest()

    def add(self, model_path, independent_key=None, open_fn=builtins.open) -> RuntimeEngineType:
        model_bytes = self.read_model(model_path, independent_key=independent_key, open_fn=open_fn)
        if (model_hash := self.calc_hash(model_bytes)) in self.session_map:
            return self.session_map[model_hash]
        self.session_map[model_hash] = self.runtime_engine(model_bytes)
        return self.session_map[model_hash]

    def get(self, model_hash: str) -> RuntimeEngineType:
        return self.session_map.get(model_hash)


@dataclass
class ModelEntity:
    model_name: str = field(default_factory=str)
    model_path: str = field(default_factory=str)
    categories: list = field(default_factory=list)
    corpus: tuple = field(default_factory=lambda: tuple([[], []]))
    cfg: dict = field(default_factory=lambda: {})
    model_runtime: RuntimeEngine = None

    @property
    def model_hash(self) -> str:
        return getattr(self.model_runtime, 'hash') if self.model_runtime else None

    @property
    def model_type(self) -> str:
        return self.cfg.get('type')

    def get_engine(self, engines: dict, project_entity: ProjectEntity):
        engine_name = self.cfg.get('type')
        if not engine_name or engine_name not in engines:
            raise RuntimeError(f"未找到名为 [{engine_name}] 的引擎")
        engine_cls = engines.get(engine_name)
        engine = engine_cls(self, project_entity)
        return engine

    def load_model(self, cfg, model_runtime, model_name, model_path, categories, corpus):
        self.model_runtime = model_runtime
        self.model_path = model_path
        self.model_name = model_name
        self.cfg = cfg
        self.categories = categories if categories else []
        self.corpus = corpus if corpus else ([], [])


class ModelManager:

    def __init__(self, project_entities: ProjectEntities):
        self.runtime_manager: RuntimeManager = RuntimeManager()
        self.project_entities: ProjectEntities = project_entities
        self.builtin_corpus: Tuple[List[str], List[Set[str]]] = self.get_corpus(
            os.path.join(MUGGLE_DIR, "corpus", "builtin.dict")
        )
        # self.warm_up_im = PIL.Image.new("RGB", (64, 64), (255, 255, 255))
        self.model_maps: Dict[str, ModelEntity] = {}
        self.path_maps: Dict[str, str] = {}
        self.iter_models()

    # def warm_up_task(self, process_cls):
    #     th = threading.Timer(10, self.batch_warm_up, (process_cls, ))
    #     th.start()
    #
    # def batch_warm_up(self, process_cls):
    #     logger.info("正在预热模型...")
    #     for k, m in self.model_maps.items():
    #         need_arr = []
    #         for shape in m.model_runtime.input_shapes:
    #             shape = [1 if isinstance(s, str) else s for s in shape]
    #             arr = process_cls(m).std_load_func(self.warm_up_im, input_shape=shape)
    #             need_arr.append([arr])
    #         m.model_runtime.run(*need_arr)
    #     logger.info("完成模型预热.")

    def timer_release(self, project_name, seconds=60):
        def unload():
            project_entity = self.project_entities.get(project_name)
            for _, model_name in project_entity.models.items():
                model_entity = self.from_project(project_name, model_name)
                model_entity.model_runtime.release()
            self.project_entities.remove(project_name)
            logger.info(f"项目 [{project_name}] 已到期释放")
        th = threading.Timer(seconds, unload)
        th.start()

    def from_id(self, model_id) -> ModelEntity:
        return self.model_maps.get(model_id)

    def from_project(self, project_name, model_name) -> ModelEntity:
        model_id = self.path_maps.get(f"{project_name}/{model_name}")
        return self.from_id(model_id)

    @classmethod
    def get_corpus(cls, path) -> Tuple[List[str], List[Set[str]]]:
        lines = open(path, encoding="utf-8").read().splitlines(False)[::-1]
        return lines, [set(i) for i in lines]

    def get_model(self, model_name, model_path: MODEL_PATH, open_fn=builtins.open, fs=None):

        def exists(x):
            return os.path.exists(x) or x in getattr(fs, 'files', [])

        model_cfg: dict = yaml.load(
            open_fn(model_path.config_path, "r", encoding="utf8").read(), Loader=yaml.SafeLoader
        )

        if exists(model_path.category_path):
            categories = open_fn(model_path.category_path, "r", encoding="utf8").read().splitlines()
        elif (category_name := model_cfg.get('categories')) and category_name in CATEGORIES_MAP:
            categories = CATEGORIES_MAP.get(category_name)
        else:
            categories = []

        if exists(model_path.corpus_path):
            attach_corpus: Tuple[List[str], List[Set[str]]] = self.get_corpus(model_path.corpus_path)
        else:
            attach_corpus: Tuple[List[str], List[Set[str]]] = [], []

        corpus = (attach_corpus[0] + self.builtin_corpus[0], attach_corpus[1] + self.builtin_corpus[1])
        model_entity = ModelEntity()
        if exists(model_path.crypto_path):
            independent_key = model_cfg.get('encryption_key', None)
            runtime_model = self.runtime_manager.add(
                model_path.crypto_path, independent_key=independent_key, open_fn=open_fn
            )
            model_entity.load_model(
                model_cfg, runtime_model, model_name, model_path.crypto_path, categories, corpus
            )
        elif exists(model_path.onnx_path):
            runtime_model = self.runtime_manager.add(model_path.onnx_path, open_fn=open_fn)
            model_entity.load_model(
                model_cfg, runtime_model, model_name, model_path.onnx_path, categories, corpus
            )
        else:
            return None
        return model_entity

    def add_model(self, project_name, model_name, open_fn, fs):
        project_path = Path.project_path(project_name)
        model_path = Path.model_path(project_path, model_name)
        model_entity = self.get_model(model_name, model_path, open_fn, fs)
        self.model_maps[model_entity.model_hash] = model_entity
        self.path_maps[f"{project_name}/{model_name}"] = model_entity.model_hash

    def iter_models(self) -> dict:
        for project_name, project_entity in self.project_entities.all.items():
            project_path = Path.project_path(project_name)
            models = project_entity.cfg.get(f'models')
            for key_name, model_name in models.items():
                model_path = Path.model_path(project_path, model_name)
                model_entity = self.get_model(model_name, model_path)
                if not model_entity:
                    continue
                self.model_maps[model_entity.model_hash] = model_entity
                self.path_maps[f"{project_name}/{model_name}"] = model_entity.model_hash

        return self.model_maps
