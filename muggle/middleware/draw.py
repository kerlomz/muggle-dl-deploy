#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import hashlib
import os
import cv2
import shutil
import base64
import gradio as gr
import random
import numpy as np
import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont
import PIL.ImageFilter
import PIL.ImageEnhance
from muggle.utils import Core
from muggle.entity import Blocks, APIType
from muggle.constants import preview_prompt, modules_enabled, app_dir
from muggle.pages.preview import PreviewLayout
from muggle.pages.utils import BlocksFuse
from muggle.entity import RequestBody
from muggle.exception import ServerException
from muggle.engine.session import project_entities
from functools import partial
from muggle.handler import Handler
from collections import namedtuple


RESOURCE = namedtuple('Resource', ['index', 'text', 'default'])
mini_prompt = preview_prompt.split("，")[-1] if preview_prompt and '，' in preview_prompt else ""


class Draw:

    def __init__(self, handler: Handler, uri):
        preview_fn = partial(self.preview_fn, handler)
        BlocksFuse.clear_cache()
        self.layout = PreviewLayout(preview_fn, uri)
        self.resource = self.load_resource()
        self.template = self.Template(self.resource)

    @classmethod
    def load_resource(cls):
        if os.path.exists((resource_path := os.path.join(app_dir, 'resource'))):
            index_font_path = os.path.join(resource_path, "fonts", "index.ttf")
            text_font_path = os.path.join(resource_path, "fonts", "text.ttf")
            default_font_path = os.path.join(resource_path, "fonts", "msyh.ttc")
            try:
                index_font = PIL.ImageFont.truetype(index_font_path, 16)
            except:
                raise RuntimeError(f"字体资源 [{index_font_path}] 加载失败")
            try:
                text_font = PIL.ImageFont.truetype(text_font_path, 24)
            except:
                raise RuntimeError(f"字体资源 [{text_font_path}] 加载失败")
            try:
                default_font = PIL.ImageFont.truetype(default_font_path, 35)
            except:
                raise RuntimeError(f"字体资源 [{default_font_path}] 加载失败")
            return RESOURCE(index=index_font, text=text_font, default=default_font)

    @classmethod
    def is_null_list(cls, images):
        if not images:
            return True
        for im in images:
            if im:
                return False
        return True

    @classmethod
    def preview_fn(cls, handler, *inputs):
        remote_ip, project_name, input_image, input_title, title_radio, title_image, *image_titles = inputs
        if not project_name:
            ServerException(
                message="尚未选择项目",
                code=1010,
                api_type=APIType.IMAGE,
                project_name=project_name,
                remote_ip=remote_ip
            )
            return "", None
        if not input_image:
            ServerException(
                message="图片输入缺失",
                code=1011,
                api_type=APIType.IMAGE,
                project_name=project_name,
                remote_ip=remote_ip
            )
            return "", None

        project_entity = project_entities.get(project_name)

        options = [title for title in project_entity.titles if title['type'] == 'radio']
        option_map = {v: k for k, v in options[0]['value'].items()} if options else []

        if input_title:
            title = input_title
        elif title_radio:
            title = option_map.get(title_radio)
        elif title_image and cls.is_null_list(image_titles):
            title = title_image
        elif not cls.is_null_list(image_titles) and not title_image:
            title = [_ for _ in image_titles if _]
        else:
            title = None

        body = RequestBody(image=input_image, project_name=project_name, title=title)
        try:
            project_name, input_image, title = handler.parse_params(body)
        except Exception as e:
            print(e, project_name, input_image, title)

        result = handler.process(APIType.IMAGE, project_name, body, None, input_image, title, remote_ip=remote_ip)
        preview_im = Core.bytes2image(result.image) if result.image else None
        if project_entity.outputs == 'text':
            preview_text = str(result.data)
        elif project_entity.outputs == 'image':
            preview_text = ''
        else:
            preview_text = ''
        return preview_text, preview_im

    class Template:

        def __init__(self, resource: RESOURCE):
            self.resource = resource
            self.index_font = self.resource.index
            self.text_font = self.resource.text
            self.default_font = self.resource.default

        def watermark(self, main_image, text, width):
            if not text:
                return main_image
            text_height = 45
            text_width = int(len(text) * text_height * 0.6)
            mask = PIL.Image.new("L", (text_width, text_height), 0)
            watermark = PIL.Image.new("RGBA", mask.size, (255, 255, 255, 255))
            draw = PIL.ImageDraw.Draw(mask)
            draw.text((0, 0), text, fill=255, font=self.default_font)
            watermark.putalpha(mask)
            new_w = int(width / 2)
            ratio = new_w / text_width
            new_h = int(ratio * text_height)
            watermark = watermark.resize((new_w, new_h))
            x, y = main_image.width - watermark.width, main_image.height - watermark.height
            main_image.paste(watermark, (x, y), watermark)
            return main_image

        @classmethod
        def gauss_noise(cls, image, mean=0, sigma=0.2):
            img_ = np.array(image).copy()
            img_ = img_ / 255.0
            # 产生高斯 noise
            sigma = (random.randint(1, int(sigma * 100))) / 100
            noise = np.random.normal(mean, sigma, img_.shape)
            # noise = np.random.normal(self.mean, self.sigma, img_.shape)
            # 将噪声和图片叠加
            gaussian_out = img_ + noise
            # 将超过 1 的置 1，低于 0 的置 0
            gaussian_out = np.clip(gaussian_out, 0, 1)
            # 将图片灰度范围的恢复为 0-255
            gaussian_out = np.uint8(gaussian_out * 255)
            # 将噪声范围搞为 0-255
            # noise = np.uint8(noise*255)
            return PIL.Image.fromarray(gaussian_out).convert('RGB')

        @classmethod
        def gradient(cls, size, list_of_colors, blur=3, fillcolor=None):
            width, height = size
            bg = PIL.Image.new("RGBA", (width, height), (255, 255, 255, 255))
            draw = PIL.ImageDraw.Draw(bg)

            for i in range(len(list_of_colors)):
                for x in range(width // len(list_of_colors)):
                    draw.line(
                        (x + (width / len(list_of_colors) * i), 0, x + (width / len(list_of_colors) * i), height),
                        fill=list_of_colors[i]

                    )
            im = bg.filter(PIL.ImageFilter.GaussianBlur(radius=random.randint(1, blur)))
            im = im.rotate(random.randint(-30, 30), expand=True, fillcolor=fillcolor).resize(im.size)
            return im

        @property
        def rand_color(self):
            return random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), 255

        @classmethod
        def label_box(cls, draw, bounding_box, label, font):
            x0, y0, x1, y1 = bounding_box
            draw.rectangle(((x0, y0), (x1, y1)), fill=(0, 255, 0, 50), outline=(0, 255, 0, 150), width=2)
            if not label:
                return
            label_boxes = [
                (x0 + 2, y0 + 2, x0 + 18, y0 + 18),
                (x0 + 2, y1 - 20 + 2, x0 + 18, y1 - 20 + 18),
                (x1 - 20 + 2, y0 + 2, x1 - 20 + 18, y0 + 18),
                (x1 - 20 + 2, y1 - 20 + 2, x1 - 20 + 18, y1 - 20 + 18),
            ]
            label_box = random.choice(label_boxes)
            lx0, ly0, lx1, ly1 = label_box
            draw.rectangle(((lx0, ly0), (lx1, ly1)), fill=(0, 255, 0, 150), outline=None, width=0)
            draw.text((lx0 + 3, ly0 - 2), label, font=font, fill=(255, 255, 255, 255))

        @classmethod
        def padding_bg(cls, main_image: PIL.Image.Image):
            main_image = main_image.convert("RGBA")
            raw_w, raw_h = main_image.size
            resize = (raw_w // 5 * 4, raw_h // 5 * 4)
            pad_w = resize[1] * 4
            pad_x = (pad_w - resize[0]) // 2
            output_im = PIL.Image.new("RGBA", (pad_w, resize[1]), (0, 0, 0, 0))
            main_image = main_image.resize(resize)
            output_im.paste(main_image, (pad_x, 0), main_image)
            return output_im

        @classmethod
        def new_canvas(cls, main_image: PIL.Image.Image):
            main_image = main_image.convert("RGBA")
            main_image = main_image.filter(PIL.ImageFilter.GaussianBlur)
            canvas = PIL.Image.new("RGBA", main_image.size, (0, 0, 0, 0))
            draw = PIL.ImageDraw.Draw(canvas)
            return main_image, canvas, draw

        def blocks_click(self, main_image: PIL.Image.Image, blocks: Blocks, draw_label=True):
            main_image, canvas, draw = self.new_canvas(main_image)
            for index, (key, block) in enumerate(blocks):
                x0, y0, x1, y1 = block.bounding_box[:4]
                self.label_box(draw, (x0, y0, x1, y1), str(index + 1) if draw_label else "", self.index_font)
            main_image.paste(canvas, (0, 0), canvas)
            main_image = self.watermark(main_image, mini_prompt, main_image.width)
            output_im = self.padding_bg(main_image)

            # output_im.show()
            return output_im

        def crops_click(self, main_image: PIL.Image.Image, crops_map: list, indexes, draw_label=True):
            main_image, canvas, draw = self.new_canvas(main_image)
            for index, need_idx in enumerate(indexes):
                x0, y0, x1, y1 = crops_map[need_idx]
                self.label_box(draw, (x0, y0, x1, y1), str(index + 1) if draw_label else "", self.index_font)
            main_image.paste(canvas, (0, 0), canvas)
            main_image = self.watermark(main_image, mini_prompt, main_image.width)
            output_im = self.padding_bg(main_image)
            # output_im.show()
            return output_im

        def line(self, main_image: PIL.Image.Image, x0):
            main_image, canvas, draw = self.new_canvas(main_image)
            x0, y0, x1, y1 = (int(x0), 0, int(x0), main_image.size[1])
            draw.line((x0, y0, x1, y1), fill=(255, 0, 0), width=5)
            main_image.paste(canvas, (0, 0), canvas)
            main_image = self.watermark(main_image, mini_prompt, main_image.width)
            output_im = self.padding_bg(main_image)
            # output_im.show()
            return output_im

        def rotate(self, main_image: PIL.Image.Image, rotate_degree: int, title: PIL.Image.Image = None):
            image = main_image.rotate(-rotate_degree)
            if title:
                tw, th = title.size
                mw, mh = image.size
                title = title.resize((tw * 4, th * 4))
                image = image.resize((mw * 4, mh * 4))
                if mw > tw:
                    r = (mw * 4 - tw * 4) // 2
                    image.paste(title, (r, r), title)
                    need_im = image.resize((mw, mh))
                else:
                    r = (tw * 4 - mw * 4) // 2
                    title.paste(image, (r, r), image)
                    need_im = title.resize((tw, th))
            else:
                need_im = image
            need_im = self.watermark(need_im, mini_prompt, need_im.width)
            output_im = self.padding_bg(need_im)
            # output_im.show()
            return output_im

        def jigsaw(self, main_image: PIL.Image.Image, crops_map: list, indexes):
            output_im = main_image.convert("RGBA")
            a, b = crops_map[indexes[0]], crops_map[indexes[1]]
            crop_a, crop_b = main_image.crop(a), main_image.crop(b)
            output_im.paste(crop_a, (b[0], b[1]))
            output_im.paste(crop_b, (a[0], a[1]))
            output_im, canvas, draw = self.new_canvas(output_im)
            for crop in [a, b]:
                self.label_box(draw, tuple(crop), "", None)
            output_im.paste(canvas, (0, 0), canvas)
            output_im = self.watermark(output_im, mini_prompt, output_im.width)
            output_im = self.padding_bg(output_im)
            return output_im

        def text(self, text: str):
            text = str(text)
            height = 30
            width = len(text) * height + 40
            mask = PIL.Image.new("L", (width, height), 0)
            text_bg = self.gradient(mask.size, [self.rand_color for _ in range(5)], fillcolor=self.rand_color)
            mask_bg = self.gradient(mask.size, [self.rand_color for _ in range(15)])
            bg = self.gradient(mask.size, [self.rand_color for _ in range(15)], fillcolor=self.rand_color)
            bg.paste(mask_bg, (0, 0), mask_bg)

            bg = bg.filter(PIL.ImageFilter.GaussianBlur)
            draw = PIL.ImageDraw.Draw(mask)
            draw.text((random.randint(2, 40), random.randint(-2, 4)), text, fill=255, font=self.text_font)
            text_bg.putalpha(mask)
            text_shadow = text_bg.copy().filter(PIL.ImageFilter.GaussianBlur)
            text_shadow = PIL.ImageEnhance.Brightness(text_shadow).enhance(0.3)
            bg = self.gauss_noise(bg)
            bg.paste(text_shadow, (-1, -1), text_shadow)
            bg.paste(text_shadow, (1, 1), text_shadow)
            bg.paste(text_bg, (0, 0), text_bg)
            output_im = self.watermark(bg, mini_prompt, bg.width)
            # bg.show()
            return output_im

    @classmethod
    def pil2bytes(cls, image):
        is_transparent = image.mode == "RGBA"
        image = np.asarray(image)
        if is_transparent:
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2RGBA)
        else:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        # if random.random() < 0.5:
        #     image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        return np.array(cv2.imencode('.png', image)[1]).tobytes()

    def draw_process(
            self, logic, input_image, title, blocks
    ):

        strategy: str = logic.project_config.get('strategy')
        if draw_func := getattr(logic, 'draw', None):
            image = draw_func(input_image, title, blocks)
            if isinstance(image, PIL.Image.Image):
                img_bytes = self.pil2bytes(image)
            else:
                img_bytes = image
        elif strategy.endswith("ClsLogic") or strategy.endswith("CTCLogic"):
            dump_data = logic.dumps(blocks)
            pil_image = self.template.text(dump_data[0])
            img_bytes = self.pil2bytes(pil_image)
        elif strategy.endswith("SliderRegLogic"):
            if (resize_argv := logic.project_config.get('resize')) and 'main' in resize_argv:
                input_image.pil = input_image.pil.resize(tuple(resize_argv['main']))
            pil_image = self.template.line(input_image.pil, blocks)
            img_bytes = self.pil2bytes(pil_image)
        elif strategy.endswith("RotateRegLogic"):
            if (resize_argv := logic.project_config.get('resize')) and 'main' in resize_argv:
                input_image.pil = input_image.pil.resize(tuple(resize_argv['main']))
            pil_image = self.template.rotate(input_image.pil, blocks, title)
            img_bytes = self.pil2bytes(pil_image)
        elif strategy.startswith("Click"):
            draw_label = logic.project_config.get('draw_label', True)
            crop_params = logic.project_config.get('crop_params')
            if crop_params and isinstance(blocks, list):
                crop_params = crop_params.get('main') if crop_params.get('main') else crop_params
                crops_map = logic.auxiliary.get_crop_param(crop_params)
                pil_image = self.template.crops_click(input_image.pil, crops_map, blocks, draw_label)
            else:
                pil_image = self.template.blocks_click(input_image.pil, blocks, draw_label)
            img_bytes = self.pil2bytes(pil_image)
        elif strategy == "JigsawLogic":
            crop_params = logic.project_config.get('crop_params')
            crop_params = crop_params.get('main') if crop_params.get('main') else crop_params
            crops_map = logic.auxiliary.get_crop_param(crop_params)
            pil_image = self.template.jigsaw(input_image.pil, crops_map, blocks)
            img_bytes = self.pil2bytes(pil_image)
        else:
            raise NotImplementedError("中间件<Draw>过程失败: 逻辑不匹配")
        return img_bytes


# if os.path.exists((resource_path := os.path.join(app_dir, 'resource'))):
#     index_font_path = os.path.join(resource_path, "fonts", "index.ttf")
#     text_font_path = os.path.join(resource_path, "fonts", "text.ttf")
#
#     if os.path.exists(index_font_path) and os.path.exists(text_font_path):
#
#         index_font = PIL.ImageFont.truetype(index_font_path, 16)
#         text_font = PIL.ImageFont.truetype(text_font_path, 24)

if __name__ == '__main__':
    pass
