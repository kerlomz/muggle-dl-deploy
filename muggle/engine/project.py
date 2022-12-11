#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import builtins
import hashlib
import os
import yaml
import importlib
import base64
from muggle.logger import logger
from typing import List, Tuple, Dict
from collections import OrderedDict, namedtuple
from dataclasses import dataclass, field
from muggle.engine.utils import Path, base_projects_dir, PROJECT_PATH


@dataclass
class ProjectEntity:
    cfg: dict = field(default_factory=lambda: {})
    project_name: str = field(default_factory=str)

    @property
    def models(self) -> Dict[str, str]:
        return self.cfg.get('models', {})

    @property
    def project_path(self) -> PROJECT_PATH:
        return Path.project_path(self.project_name)

    @property
    def outputs(self):
        return self.cfg.get('outputs')

    @property
    def strategy(self):
        strategy = self.cfg.get('strategy')
        if not strategy:
            raise RuntimeError("项目配置参数缺失 [strategy]")
        return strategy

    @property
    def title(self):
        title = self.cfg.get('title')
        if not title:
            raise RuntimeError("项目配置参数缺失 [title]")
        return title

    @property
    def titles(self) -> list:
        titles = self.cfg.get('titles')
        return titles if titles else []

    @property
    def input_images(self) -> list:
        input_images = self.cfg.get('input_images')
        return input_images if input_images else []

    @property
    def title_images(self) -> list:
        title_images = self.cfg.get('title_images')
        return title_images if title_images else []

    @property
    def model_params(self):
        return {k: {"project_name": self.project_name, "model_name": v} for k, v in self.models.items()}


class ProjectEntities:

    def __init__(self):
        self.all = self.iter_projects_from_dirs()

    @property
    def titles(self):
        return [v.cfg.get('title') for k, v in self.all.items()]

    @property
    def name_maps(self):
        return {k: i for i, (k, _) in enumerate(self.all.items())}

    @property
    def ids_maps(self):
        return {i: k for i, (k, v) in enumerate(self.all.items())}

    def get(self, project_name) -> ProjectEntity:
        return self.all.get(project_name)

    def add(self, project_name, project_entity: ProjectEntity):
        self.all[project_name] = project_entity

    def remove(self, project_name):
        del self.all[project_name]

    @classmethod
    def iter_image_titles(cls, project_config, index, value):
        project_config['title_images'].append(value)
        for title in project_config['titles']:
            if title['type'] == 'images':
                title['value'][index]['path'] = value
            elif title['type'] == 'image':
                title['value'] = value

    @classmethod
    def iter_projects_from_dirs(cls) -> OrderedDict[str, ProjectEntity]:
        all_models: OrderedDict[str, ProjectEntity] = OrderedDict()
        if not os.path.exists(base_projects_dir):
            return all_models
        for project_name in os.listdir(base_projects_dir):
            try:
                project_path = Path.project_path(project_name)
                # print(project_path)
                cfg = yaml.load(
                    "".join(open(project_path.config_path, "r", encoding="utf8").read()), Loader=yaml.SafeLoader
                )
                demo_files = os.listdir(project_path.demo_dir)
                cfg['input_images'] = []
                cfg['title_images'] = []

                for filename in demo_files:
                    filepath = os.path.join(project_path.demo_dir, filename)
                    if filename.startswith("image."):
                        cfg['input_images'].append(filepath)
                    elif filename.startswith("title_") or filename.startswith("title."):
                        idx = int(filename.split(".")[0].split("_")[1]) if filename.startswith("title_") else 0
                        cls.iter_image_titles(cfg, idx, filepath)
                # if os.path.exists(project_path)
                project_entity = ProjectEntity(project_name=project_name, cfg=cfg)
                # print(project_entity)
                all_models[project_name] = project_entity
            except Exception as e:
                logger.warning(f"跳过项目 [{project_name}]: {e}")
                # print('skip', project_name)
                continue
        return all_models

