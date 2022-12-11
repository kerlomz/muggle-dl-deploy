#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import numpy as np
from abc import ABC
from typing import List, Tuple, Union
from muggle.logic.base import BaseLogic, Response, InputImage, Title, Block


class BaseClsLogic(BaseLogic, ABC):

    def dumps(self, response: Response) -> Response:
        join_output = self.project_config.get("join_outputs")
        texts_or_indexes, scores = zip(*response)
        result = list(texts_or_indexes)
        if join_output and texts_or_indexes and isinstance(texts_or_indexes[0], str):
            result = ",".join(texts_or_indexes)
        return result, float(np.prod(scores))


class ClsLogic(BaseClsLogic):

    def process(self, image: InputImage, title: Title = None) -> Response:
        predictions = self.session.default_engine.predict(image.pil)
        return predictions







