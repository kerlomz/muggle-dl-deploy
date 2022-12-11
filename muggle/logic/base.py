#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import PIL.Image
import PIL.GifImagePlugin
import numpy as np
from abc import abstractmethod
from typing import List, Union, Tuple
from muggle.entity import Blocks, Block, Response, InputImage, Title, ImageEntity, ImageType
from muggle.utils import Core
from muggle.engine.session import ProjectSession
from muggle.logic.utils import LogicAuxiliary


class BaseLogic:

    def __init__(self, project_name: str, param=None):
        self.project_name = project_name
        self.print_process = False
        self.param = {} if param is None else param
        self.session = ProjectSession(project_name=self.project_name)
        self.project_entity = self.session.project_entity
        self.project_config = self.project_entity.cfg
        self.auxiliary = LogicAuxiliary()

    @abstractmethod
    def process(self, image: InputImage, title: Title = None) -> Response:
        pass

    @abstractmethod
    def dumps(self, response: Response) -> tuple[str, float]:
        pass

    def execute(self, image: ImageType, title: Title = None):
        image = Core.image_progress(image)
        image = ImageEntity(pil=image.copy(), hash="", raw_bytes=b"", base64="")
        response = self.process(image, title)
        return self.dumps(response)