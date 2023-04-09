#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import string
import re
import PIL.ImageEnhance
import numpy as np
from abc import ABC
from itertools import groupby
from muggle.utils import Core

from muggle.logic.base import BaseLogic, Response, InputImage, Title, ImageEntity


class BaseCTCLogic(BaseLogic, ABC):

    def dumps(self, response: Response) -> Response:
        join_tag = self.project_config.get('join_tag', ',')
        texts, scores = zip(*response)
        return join_tag.join(texts), float(np.prod(scores))


class CTCLogic(BaseCTCLogic):

    def process(self, image: InputImage, title: Title = None) -> Response:
        self.project_config['join_tag'] = ''
        return self.session.default_engine.predict(image.pil)


class GIFAllFramesCTCLogic(BaseCTCLogic):

    @classmethod
    def elem_cont_len(cls, x, src):
        return max(len(list(g)) for k, g in groupby(src) if k == x)

    @classmethod
    def get_continuity_max(cls, src: list):
        if not src:
            return ""
        target_list = [cls.elem_cont_len(i, src) for i in src]
        target_index = target_list.index(max(target_list))
        return src[target_index]

    def process(self, images: InputImage, title: Title = None) -> Response:
        self.project_config['join_tag'] = ''
        concat_items = self.session.default_engine.batch_predict(images.pil)
        need_items = [["", 0] for _ in concat_items[0]]
        for idx in range(len(need_items)):

            for items in concat_items:
                try:
                    if items[idx][1] > need_items[idx][1]:
                        need_items[idx][1] = items[idx][1]
                        need_items[idx][0] = items[idx][0]
                except:
                    continue
        return need_items


class GIFBlendCTCLogic(BaseCTCLogic):

    def process(self, image: InputImage, title: Title = None) -> Response:
        self.project_config['join_tag'] = ''
        need_frame = self.project_config.get('need_frame')
        blend_im = Core.blend_frame(image, need_frame=need_frame)
        blend_im = PIL.ImageEnhance.Contrast(blend_im).enhance(2.5)
        items = self.session.default_engine.predict(blend_im)
        return items


class GIFConcatCTCLogic(BaseCTCLogic):

    def process(self, images: InputImage, title: Title = None) -> Response:
        self.project_config['join_tag'] = ''
        need_frame = self.project_config.get('need_frame')
        need_ims = [images.pil[i] for i in need_frame]
        concat_items = []
        items = self.session.default_engine.batch_predict(need_ims)
        for item in items:
            concat_items += item
        return concat_items


class ArithmeticCTCLogic(BaseLogic):

    def process(self, image: InputImage, title: Title = None) -> Response:
        items = self.session.default_engine.predict(image.pil)
        predict_texts, scores = zip(*items)
        predict_text = "".join(predict_texts)
        calc_result = str(int(self.auxiliary.Arithmetic.calc(predict_text)))
        return calc_result, list(scores)

    def dumps(self, response: Response) -> str:
        return response


class AdaptionArithmeticCTCLogic(BaseLogic):

    def process(self, image: InputImage, title: Title = None) -> Response:
        items = self.session.default_engine.predict(image.pil)
        predict_texts, scores = zip(*items)
        predict_text = "".join(predict_texts)
        if Core.contains(predict_text, ['+', '-', '×', '÷', '=', '?']):
            result = str(int(self.auxiliary.Arithmetic.calc(predict_text)))
        else:
            result = predict_text
        return result, scores

    def dumps(self, response: Response) -> str:
        return response


class DoubleCTCLogic(BaseCTCLogic):

    def process(self, image: InputImage, title: Title = None) -> Response:
        engine = self.session.default_engine
        option_map = {v: k for i, (k, v) in enumerate(self.project_config.get('option_label_map').items())}
        if title not in map(str, option_map.values()):
            title = option_map[title]
        predictions = engine.predict(image.pil)
        items, attrs = predictions[0]
        need_texts = []
        scores = []
        for text, attr in zip(items, attrs):
            if attr[0] == title:
                need_texts.append(text[0])
                scores.append(text[1]*attr[1])
        return "".join(need_texts), scores

    def dumps(self, response: Response) -> str:
        return response


if __name__ == '__main__':
    pass