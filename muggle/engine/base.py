#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import hashlib
import os.path
from loguru import logger
import PIL.Image
import numpy as np
import onnxruntime
from abc import abstractmethod
from muggle.config import cli_args
from typing import Union, TypeVar, List
from muggle.engine.model import ModelEntity, RuntimeEngineType, InputShape
from muggle.engine.project import ProjectEntity
from muggle.engine.components.preprocess import ProcessUtils


class BaseEngine:

    utils_cls = ProcessUtils

    def __init__(self, model_entity: ModelEntity, project_entity: ProjectEntity):
        self.model_entity: ModelEntity = model_entity
        self.runtime_engine: RuntimeEngineType = self.model_entity.model_runtime
        self.project_entity: ProjectEntity = project_entity
        self.session = self.runtime_engine.session
        self.input_shape: InputShape = self.runtime_engine.input_shape
        self.with_postprocess = self.get_cfg('postprocess', True)
        self.utils = self.utils_cls(model_entity)

    @property
    def hash(self):
        if not self.runtime_engine:
            raise RuntimeError("请先初始化运行时引擎 [BaseEngine -> runtime_engine] ")
        return self.runtime_engine.hash

    def get_cfg(self, name, default=None):
        if name in self.model_cfg:
            return self.model_cfg.get(name)
        elif name in self.project_cfg:
            return self.project_cfg.get(name)
        return default if default is not None else None

    @property
    def model_cfg(self) -> dict:
        if not self.model_entity:
            raise RuntimeError("未定义模型实体 [BaseEngine -> model_entity]")
        return self.model_entity.cfg if self.model_entity else {}

    @property
    def project_cfg(self) -> dict:
        return self.project_entity.cfg if self.project_entity else {}

    @abstractmethod
    def preprocess(self, *args, **kwargs): pass

    @abstractmethod
    def postprocess(self, *args, **kwargs): pass

    @abstractmethod
    def predict(self, *args, **kwargs): pass

    @abstractmethod
    def batch_predict(self, *args, **kwargs): pass

    def close(self):
        return self.runtime_engine.close()


ModelEngineType = TypeVar('ModelEngineType', bound=BaseEngine)


