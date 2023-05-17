#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import cv2
import PIL.Image
import PIL.GifImagePlugin
import PIL.ImageSequence
import numpy as np
from typing import Union
from muggle.engine.base import ProjectEntity
from muggle.engine.model import ModelEntity, InputImage, GifImage, InputImages


class ProcessUtils:

    def __init__(
            self,
            model_entity: ModelEntity,
    ):
        self.model_entity = model_entity
        self.runtime_engine = self.model_entity.model_runtime
        self.model_cfg = model_entity.cfg

    @classmethod
    def gif_load_func(cls, im: GifImage) -> InputImages:
        p = im.getpalette()
        last_frame = im.convert('RGBA')
        all_frames = []
        try:
            for frame in PIL.ImageSequence.Iterator(im):
                if not frame.getpalette() and p:
                    frame.putpalette(p)
                new_frame = PIL.Image.new('RGBA', frame.size)
                if frame.tile and frame.tile[0][1][2:] != frame.size:
                    new_frame.paste(last_frame)
                new_frame.paste(frame, (0, 0), frame.convert('RGBA'))
                all_frames.append(new_frame)
                last_frame = new_frame
        except:
            all_frames = [frame.convert("RGB") for frame in PIL.ImageSequence.Iterator(im)]
        return all_frames

    @classmethod
    def softmax(cls, x, axis=1):
        if len(x.shape) > 1:
            t = np.exp(x) / np.sum(np.exp(x), axis=axis).reshape(-1, 1)
        else:
            t = np.exp(x) / np.sum(np.exp(x), axis=axis)
        if len(t.shape) > 1 and (np.isnan(t[0][0]) or np.isinf(t[0][0])):
            return x
        return t

    @classmethod
    def sigmoid(cls, z):
        return 1 / (1 + np.exp(-z))

    @classmethod
    def normalize(cls, im, mean, std):
        if isinstance(mean, list):
            mean = tuple(mean)
            return cls.normalize(im, mean, std)
        elif isinstance(mean, float):
            mean = (mean,) * 3
        elif not isinstance(mean, tuple):
            raise TypeError("mean must be tuple of float / float / list of float")
        if len(mean) == 1:
            mean = mean * 3
        if isinstance(std, list):
            std = tuple(std)
            return cls.normalize(im, mean, std)
        elif isinstance(std, float):
            std = (std,) * 3
        elif not isinstance(std, tuple):
            raise TypeError("std must be tuple of float / float / list of float")
        if len(std) == 1:
            std = std * 3

        assert len(mean) == 3
        assert len(std) == 3

        im = im / 255
        im = np.subtract(im, [[list(mean)]])
        im = np.divide(im, [[list(std)]])
        return im.transpose(2, 0, 1)

    @classmethod
    def resize_shape(cls, input_image, input_shape):
        w0, h0 = input_shape
        if not isinstance(w0, str):
            return w0, h0
        w1, h1 = input_image.size
        w0 = int(h0 / h1 * w1)
        return w0, h0

    def std_load_func(self, input_image: InputImage, input_shape=None):
        to_rgb = self.model_cfg.get("to_rgb", False)
        input_shape = self.runtime_engine.input_shape if input_shape is None else input_shape

        resize_shape = input_shape[2:][::-1]
        if isinstance(input_image, list):
            input_image = input_image[0]
        resize_shape = self.resize_shape(input_image, resize_shape)
        im = input_image.resize(resize_shape, resample=PIL.Image.BILINEAR)
        if im.mode in ['P', 'L'] and not to_rgb and input_shape[1] == 3:
            im = im.convert("RGB")
        im = np.asarray(im)
        shape = im.shape
        if len(shape) > 2 and shape[2] == 4:
            b, g, r, a = cv2.split(im)
            mask = (a == 0)
            b[mask] = 255
            g[mask] = 255
            r[mask] = 255
            im = cv2.merge((b, g, r))
        if to_rgb and len(shape) > 2:
            im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
        elif to_rgb and len(shape) == 2:
            im = cv2.cvtColor(im, cv2.COLOR_GRAY2RGB)
        shape = im.shape
        if input_shape[1] == 1 and len(shape) == 3:
            im = cv2.cvtColor(im, cv2.COLOR_RGB2GRAY)
            im = im[:, :] / 255.
        elif input_shape[1] == 1 and len(shape) == 2:
            im = im[np.newaxis, :, :]
        elif input_shape[1] == 3 and len(shape) == 3:
            im = self.normalize(im, [0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        arr = np.array(im, dtype=np.float32)[:, :, :]
        return arr
