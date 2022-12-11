#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import numpy as np
import cv2
from muggle.logic.base import BaseLogic, Response, InputImage, Title


class JigsawLogic(BaseLogic):

    @staticmethod
    def fix_image(raw_im, indexes, row=2, col=4):
        im = np.asarray(raw_im)
        im = cv2.cvtColor(im, cv2.COLOR_RGB2BGR)
        d_row, d_col = im.shape[0] // row, im.shape[1] // col

        for crop_a, crop_b in indexes:
            row_a, col_a = int(crop_a) // col, int(crop_a) % col
            row_b, col_b = int(crop_b) // col, int(crop_b) % col
            # Copy and Paste
            temp = im[row_a * d_row:(row_a + 1) * d_row, col_a * d_col:(col_a + 1) * d_col].copy()
            im[row_a * d_row:(row_a + 1) * d_row, col_a * d_col:(col_a + 1) * d_col] = im[row_b * d_row:(row_b + 1) * d_row, col_b * d_col:(col_b + 1) * d_col]
            im[row_b * d_row:(row_b + 1) * d_row, col_b * d_col:(col_b + 1) * d_col] = temp
        success, encoded_image = cv2.imencode(".png", im)
        return encoded_image.tobytes()

    def process(self, image: InputImage, title: Title = None) -> Response:
        return self.session.default_engine.predict(image.pil)

    def dumps(self, response: Response) -> tuple[str, float]:
        return response, 1.

    # def draw(self, input_image: InputImage, title, indexes):
    #     print('=====')
    #     return self.fix_image(raw_im=input_image.pil, indexes=[indexes])
