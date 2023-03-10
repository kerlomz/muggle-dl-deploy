#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import builtins
import hashlib
import io
import os
import re
import cv2
import sys
import time
import uuid
import base64
import datetime
from muggle.logger import logger
import socket
import numpy as np
import PIL.Image
import PIL.ImageSequence
import PIL.GifImagePlugin
import PIL.ImageFont
import PIL.ImageDraw
import PIL.ImageEnhance
from urllib import parse
from typing import Union, Optional
from muggle.entity import ImageEntity


class Core:

    @staticmethod
    def contains(text, char_list):
        for char in char_list:
            if char in text:
                return True
        return False

    @staticmethod
    def uuid():
        return str(uuid.uuid4()).replace("-", "")

    @staticmethod
    def date_calc(days):
        d1 = datetime.datetime.strptime(time.strftime("%Y-%m-%d", time.localtime()), '%Y-%m-%d')
        dt = d1 + datetime.timedelta(days=days)
        return dt.strftime("%Y-%m-%d")

    @staticmethod
    def resource_path(relative_path):
        if os.path.exists(relative_path):
            return relative_path
        try:
            # Nuitka temp folder
            base_path = os.path.dirname(__file__)
        except AttributeError:
            base_path = os.path.abspath("..")
        return os.path.join(base_path, relative_path)

    @classmethod
    def date_string(cls):
        return time.strftime("%Y-%m-%d", time.localtime())

    @classmethod
    def datetime_string(cls):
        return time.strftime("%Y%m%d%H%M%S", time.localtime())

    @classmethod
    def compare_date(cls, now, deadline):
        d1 = datetime.datetime.strptime(now, '%Y-%m-%d')
        d2 = datetime.datetime.strptime(deadline, '%Y-%m-%d')
        delta = d2 - d1
        return delta.days

    @classmethod
    def filter_base64(cls, source: str):
        return re.sub("data:image/.+?base64,", "", source, 1) if ',' in source else source

    @classmethod
    def image_progress(cls, image):
        if isinstance(image, PIL.GifImagePlugin.GifImageFile):
            gif_frames = cls.gif_loader(image)
            image = gif_frames if gif_frames else image.copy()
        return image

    @classmethod
    def bytes2image(cls, source: Optional[bytes]) -> Optional[PIL.Image.Image]:
        if not source:
            return
        return PIL.Image.open(io.BytesIO(source))

    @classmethod
    def text2image(cls, source: Union[str, ImageEntity]) -> ImageEntity:
        if isinstance(source, ImageEntity):
            return source
        b64_text = cls.filter_base64(source)
        try:
            img_bytes = base64.b64decode(cls.filter_base64(b64_text))
        except Exception:
            raise ValueError("Base64编码解析失败")
        md5 = hashlib.md5(img_bytes).hexdigest()
        with io.BytesIO(img_bytes) as data_stream:
            image = PIL.Image.open(data_stream)
            image = cls.image_progress(image)
            return ImageEntity(pil=image.copy(), hash=md5, raw_bytes=img_bytes, base64=b64_text)

    @classmethod
    def gif_loader(cls, im: Union[PIL.GifImagePlugin.GifImageFile, PIL.Image.Image]):
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
    def blend_frame(cls, image_objs, need_frame=None):
        start_frame = image_objs[0]
        blend_im = start_frame
        for idx, im in enumerate(image_objs[1:]):
            if (idx + 2) not in need_frame:
                continue
            blend_im = PIL.Image.blend(blend_im, im, 0.5)
        return blend_im

    @classmethod
    def illumination_correction(cls, im):
        im = np.asarray(im)
        lab = cv2.cvtColor(im, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(15, 15))
        cl = clahe.apply(l)
        limg = cv2.merge((cl, a, b))
        final = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
        return PIL.Image.fromarray(np.uint8(final))

    @staticmethod
    def avoid_suspension():
        """
        禁用快速编辑模式，防止误操作
        :return:
        """
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-10), (0x4 | 0x80 | 0x20 | 0x2 | 0x10 | 0x1 | 0x00 | 0x100))
            logger.info('禁用快速编辑模式')
        except:
            logger.warning(
                f'禁用快速编辑模式失败, 请勿误选择黑框内容导致程序暂停'
            )

    @staticmethod
    def unpack_url(params):
        url = "http://localhost?"
        query = parse.urlparse(url+params).query
        return dict([(k, v[0]) for k, v in parse.parse_qs(query, keep_blank_values=True).items()])

    @classmethod
    def check_port_in_use(cls, port, host='127.0.0.1'):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((host, int(port)))
            s.settimeout(1)
            s.shutdown(2)
            return True
        except:
            return False


class Import:

    @classmethod
    def extract_path(cls, package):
        path_group = package.split(".")
        module_path = ".".join(path_group[0:-1])
        class_name = path_group[-1]
        return module_path, class_name

    @classmethod
    def as_class(cls, package):
        import importlib
        module_path, class_name = cls.extract_path(package)
        tmp_module = importlib.import_module(module_path)
        tmp_class = getattr(tmp_module, class_name)
        return tmp_class

    @classmethod
    def dynamic_import(cls, package, instance=False, **kwargs):
        _, class_name = cls.extract_path(package)
        draw_class = cls.as_class(package)(**kwargs) if instance else cls.as_class(package)
        globals()[class_name] = draw_class

    @staticmethod
    def get_class(name):
        if name not in globals():
            raise ModuleNotFoundError(f"找不到模块 [{name}]")
        return globals().get(name)

    @staticmethod
    def get_param(name, default_value=None):
        if name not in globals():
            globals()[name] = default_value
        return globals().get(name)
