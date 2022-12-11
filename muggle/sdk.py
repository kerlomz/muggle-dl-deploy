#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import os
import threading

import PIL.Image
import importlib
from muggle.engine.session import project_entities
from muggle.engine.project import Path
from typing import TypeVar
from muggle.logic import *
from muggle.logger import logger


Logic = TypeVar('Logic', bound=BaseLogic)


class SDK:

    @classmethod
    def load_logics(cls, logic_dir):
        logic_paths = [
            Path.filter(os.path.join(logic_dir, name.split(".")[0]))
            for name in os.listdir(logic_dir) if name.endswith(".py")
        ]
        for logic_path in logic_paths:
            package_name = logic_path.replace("/", ".")
            logic_module = importlib.import_module(package_name)
            globals().update({k: v for k, v in logic_module.__dict__.items() if k.endswith("Logic")})

    @classmethod
    def get(cls, project_name, param=None) -> Logic:
        project_entity = project_entities.get(project_name)
        logic_dir = project_entity.project_path.logic_dir
        logic_name = project_entity.strategy
        if logic_name not in globals() and os.path.exists(logic_dir):
            cls.load_logics(logic_dir)
        return globals()[logic_name](
            project_name=project_name, param=param
        )

    @classmethod
    def warm_up(cls, project_entity):
        project_name = project_entity.project_name
        logic = cls.get(project_name)
        if project_entity.titles:
            item = project_entity.titles[0]
            title_type = item['type']
            title_val = item['value']
            if title_type not in ['image', 'images']:
                title = list(title_val.keys())[0] if isinstance(title_val, dict) else title_val
            else:
                title = [PIL.Image.open(_) for _ in project_entity.title_images]
                title = title[0] if len(title) == 1 else title
        else:
            title = None
        image = PIL.Image.open(project_entity.input_images[0])
        logic.execute(image, title=title)

    @classmethod
    def warm_up_task(cls):
        th = threading.Thread(target=cls.batch_warm_up)
        th.start()

    @classmethod
    def batch_warm_up(cls):
        logger.info("<模型预热任务> 正在后台进行...")
        threads = []
        for _, project_entity in project_entities.all.items():
            th = threading.Thread(target=cls.warm_up, args=(project_entity, ))
            threads.append(th)

        for t in threads:
            t.start()
            t.join()
        logger.info(f"{len(threads)}个 <模型预热任务> 已完成.")
