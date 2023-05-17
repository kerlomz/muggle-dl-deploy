#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import muggle
from typing import Tuple, List, TypeVar
from muggle.engine.project import ProjectEntities
from muggle.engine.model import (
    ModelEntity, RuntimeEngineType, RuntimeManager, ModelManager, InputImage, InputImages, GifImage
)
from muggle.engine.base import ModelEngineType
from collections import OrderedDict, namedtuple
from muggle.engine.impl import *
from muggle.logger import logger


project_entities: ProjectEntities = ProjectEntities()
model_manager = ModelManager(project_entities)
if not project_entities.all and not os.path.exists("compile_projects"):
    logger.info(f"当前尚未发现任何工程, 请将项目相关文件 [*projects|*logic] 置于根目录")
if loaded_project_names := '|'.join(project_entities.all.keys()):
    # model_manager.warm_up_task(getattr(globals()['BaseEngine'], 'utils_cls'))
    logger.info(f"加载引擎 [{loaded_project_names}]")


class ProjectSession:

    def __init__(self, project_name: str):
        self.project_name = project_name
        self.project_entity = project_entities.get(self.project_name)

    @property
    def models(self) -> OrderedDict[str, ModelEntity]:
        return OrderedDict({
            k: model_manager.from_project(**v)
            for k, v in project_entities.get(self.project_name).model_params.items()
        })

    @property
    def runtime(self) -> OrderedDict[str, RuntimeEngineType]:
        return OrderedDict({
            k: model_manager.from_project(**v).model_runtime
            for k, v in project_entities.get(self.project_name).model_params.items()
        })

    @property
    def engine(self) -> OrderedDict[str, ModelEngineType]:
        return OrderedDict({
            k: model_manager.from_project(**v).get_engine(globals(), self.project_entity)
            for k, v in project_entities.get(self.project_name).model_params.items()
        })

    @property
    def default_engine(self) -> ModelEngineType:
        return [_ for _ in self.engine.values()][0]

    @classmethod
    def engine_from_project(cls, project_name, model_name=None):
        project_entity = project_entities.get(project_name)
        engines = OrderedDict({
            v.get('model_name'): model_manager.from_project(**v).get_engine(globals(), project_entity)
            for k, v in project_entities.get(project_name).model_params.items()
        })
        return engines.get(model_name) if model_name else engines


