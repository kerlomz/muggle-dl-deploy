#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import numpy as np
from muggle.logic.base import BaseLogic, Response, InputImage, Title
from muggle.utils import Core


class RegLogic(BaseLogic):

    def process(self, image: InputImage, title: Title = None) -> Response:
        to_rgb = self.project_config.get('to_rgb')
        predictions = self.session.reg.predict(image, to_rgb=to_rgb)
        return predictions, 1

    def dumps(self, response: Response) -> str:
        return response


class SliderRegLogic(BaseLogic):
    """
    滑块逻辑
    """

    def process(self, image: InputImage, title: Title = None) -> Response:
        if title:
            title = Core.text2image(title)
            if resize_argv := self.project_config.get('resize'):
                if 'main' in resize_argv:
                    image = image.pil.resize(tuple(resize_argv['main']))
                if 'title' in resize_argv:
                    title = title.pil.resize(tuple(resize_argv['title']))

            image = image.pil.convert("RGBA")
            y = int(self.param['y']) if self.param.get('y') else 0
            image.paste(title, (0, y), title)
            image = image.convert("RGB")
        else:
            image = image.pil

        engine = self.session.default_engine
        x0 = engine.predict(image)
        ratio = engine.input_shape[3] / image.size[0]
        return round(float(x0) / ratio)

    def dumps(self, response: Response) -> tuple[str, float]:
        # print(response)
        return response, 1


class RotateRegLogic(BaseLogic):

    def process(self, image: InputImage, title: Title = None) -> Response:
        predictions = self.session.engine['reg'].predict(image.pil)
        degree = round(predictions[0] * 360)
        return degree

    def dumps(self, response: Response):
        return response, 1
