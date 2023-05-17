#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import os
import multiprocessing
from multiprocessing import Manager, get_context
from collections import namedtuple
from typing import TypeVar, Generic

K = TypeVar('K')
V = TypeVar('V')

base_projects_dir = "projects"
MODEL_PATH = namedtuple('MODEL_PATH', [
    'model_dir', 'onnx_path', 'crypto_path', 'config_path', 'corpus_path', 'category_path'
])
PROJECT_PATH = namedtuple('PROJECT_PATH', ['project_dir', 'model_dir', 'config_path', "demo_dir", "logic_dir"])


class Path:

    @classmethod
    def filter(cls, path: str):
        return path.replace("\\", "/")

    @classmethod
    def join(cls, parent, child, *args):
        return cls.filter(os.path.join(parent, child, *args))

    @classmethod
    def project_path(cls, project_name) -> PROJECT_PATH:
        project_dir = cls.filter(os.path.join(base_projects_dir, project_name))
        model_dir = cls.filter(os.path.join(project_dir, "models"))
        config_path = cls.filter(os.path.join(project_dir, "project_cfg.yaml"))
        demo_dir = cls.filter(os.path.join(project_dir, "demo"))
        logic_dir = cls.filter(os.path.join(project_dir, "logic"))
        return PROJECT_PATH(
            project_dir=project_dir,
            model_dir=model_dir,
            config_path=config_path,
            demo_dir=demo_dir,
            logic_dir=logic_dir
        )

    @classmethod
    def model_path(cls, project_path: PROJECT_PATH, model_name: str) -> MODEL_PATH:
        model_dir = cls.filter(os.path.join(project_path.model_dir, model_name))
        config_path = cls.filter(os.path.join(model_dir, "model.yaml"))
        onnx_path = cls.filter(os.path.join(model_dir, "model.onnx"))
        crypto_path = cls.filter(os.path.join(model_dir, "model.crypto"))
        corpus_path = cls.filter(os.path.join(model_dir, "corpus.dict"))
        category_path = cls.filter(os.path.join(model_dir, 'categories.label'))
        return MODEL_PATH(
            model_dir=model_dir,
            onnx_path=onnx_path,
            crypto_path=crypto_path,
            config_path=config_path,
            category_path=category_path,
            corpus_path=corpus_path,
        )
