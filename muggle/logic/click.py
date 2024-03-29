#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import json
import os.path
import random
import string
import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont
import PIL.ImageEnhance
import muggle
import numpy as np
from abc import ABC
from muggle.logic.base import BaseLogic, Response, Title
from muggle.entity import Blocks, Block, BoundingBox, InputImage, ImageType
from muggle.utils import Core
from muggle.logic.utils import LogicAuxiliary


app_dir = os.path.dirname(muggle.__file__)
resource_path = os.path.join(app_dir, 'resource')


class BlockOrder:

    @staticmethod
    def many_or_many(blocks, title_list):
        return Blocks.Import.by_index([
            blocks.get(i)
            for title_item in title_list for i, (k, block_classification) in enumerate(blocks.classifications)
            if set(block_classification) >= {title_item}
        ])

    @staticmethod
    def many_and_many(blocks, title_list, attr, src_coord):
        score, cls, coordinates, boxes = zip(*[
            ((it := blocks.get(i)).score, it.classification, it.coordinate, it.bounding_box)
            for i, classification in enumerate(blocks.classifications)
            if set(classification) >= set(title_list)
               and not Blocks.Util.skip_opposite_position_coordinates(attr, blocks.get(i).bounding_box, src_coord)
        ])
        if coordinates and attr and attr[0] == 'nearest_side':
            centre_x = int((src_coord[0] + src_coord[2]) / 2)
            centre_y = int((src_coord[1] + src_coord[3]) / 2)
            group = [Blocks.Util.distance([centre_x, centre_y], _) for _ in coordinates]
            score, cls, coordinates, boxes = [score[(i := group.index(min(group)))]], [cls[i]], [coordinates[i]], [boxes[i]]
        dumps_blocks = Blocks.Import.by_params(score, cls, coordinates, boxes)
        return dumps_blocks

    @staticmethod
    def one_to_one(blocks, title_list):
        return Blocks.Import.by_index(
            [blocks.get(title_item) for title_item in title_list if title_item in blocks.map]
        )

    @staticmethod
    def one_to_many(blocks, title_list):
        return Blocks.Import.by_index(
            [blocks.get(i) for i, block_text in enumerate(blocks.classifications)
             if list(block_text) == list(title_list) and block_text != ['-']]
        )

    @staticmethod
    def none(blocks):
        return blocks


class BaseClickLogic(BaseLogic, ABC):

    def __init__(self, project_name: str, param=None):
        super().__init__(project_name, param)
        self.get_crop_param = self.auxiliary.get_crop_param
        self.crop = self.auxiliary.crop

    def dumps(self, response: Response) -> tuple[str, float]:
        if self.param and 'dump_bounding_box' in self.param:
            return response.dump_bounding_box(), response.score
        if self.param and 'dump_all' in self.param:
            return response.dumps(), response.score
        coordinates = response.dumps_coordinates()
        result = "|".join([",".join(str(j) for j in i) for i in coordinates])
        if self.param and 'dump_classifications' in self.param:
            result += f'#{"".join(response.classifications)}'
        if self.param and 'dump_indexes' in self.param:
            result = response.indexes
        return result, response.score

    @classmethod
    def parse_title(cls, title, fill_bg=True):
        if isinstance(title, PIL.Image.Image):
            title = LogicAuxiliary.fill_bg(title, skip=not fill_bg)
        elif isinstance(title, str) and title.startswith("data:image"):
            title = LogicAuxiliary.fill_bg(Core.text2image(title).pil, skip=not fill_bg)
        elif isinstance(title, str) and len(title) > 100:
            title = LogicAuxiliary.fill_bg(Core.text2image(title).pil, skip=not fill_bg)
        elif isinstance(title, str) and title.startswith("["):
            title = [LogicAuxiliary.fill_bg(Core.text2image(_).pil, skip=not fill_bg) for _ in json.loads(title)]
        elif isinstance(title, list) and len(title) > 0 and isinstance(title[0], str) and len(title[0]) > 100:
            title = [LogicAuxiliary.fill_bg(Core.text2image(_).pil, skip=not fill_bg) for _ in title]
        return title

    @classmethod
    def in_box(cls, src_box, target_box):
        x0, y0, x1, y1 = src_box[:4]
        coordinate = [(x0 + x1) / 2, (y0 + y1) / 2]
        if target_box[0] < coordinate[0] < target_box[2] and target_box[1] < coordinate[1] < target_box[3]:
            return True
        return False

    @classmethod
    def box_range_filter(cls, src_box, target_box) -> tuple[int, int, int, int]:
        sx0, sy0, sx1, sy1 = src_box[:4]
        tx0, ty0, tx1, ty1 = target_box

        x0 = max(sx0, tx0)
        y0 = max(sy0, ty0)
        x1 = min(sx1, tx1)
        y1 = min(sy1, ty1)
        return x0, y0, x1, y1

    @classmethod
    def std_box(cls, src_box) -> tuple[int, int, int, int]:
        x0, y0, x1, y1 = tuple(src_box)[:4]
        return x0, y0, x1, y1

    @classmethod
    def split_boxes(cls, box_range, src_group):
        in_range_ims, in_range_box, out_range_box, out_range_ims = [], [], [], []
        for im, box in zip(*src_group):
            if cls.in_box(box, box_range):
                in_range_ims.append(im)
                in_range_box.append(box)
            else:
                out_range_ims.append(im)
                out_range_box.append(box)

        in_range_group = list(zip(in_range_ims, in_range_box))
        in_range_group = sorted(in_range_group, key=lambda t: t[1][0])

        out_range_group = list(zip(out_range_ims, out_range_box))

        return in_range_group, out_range_group

    def similarity_process(self, ims_title, ims_main, boxes_main):
        orders = self.session.engine['sim'].batch_predict(
            list(ims_title), list(ims_main),
        )

        need_title = [str(i) for i in orders]
        main_text = [str(i + 1) for i in range(len(ims_main))]
        blocks = Blocks.Archive.from_text(main_text, boxes_main)
        return BlockOrder.one_to_one(blocks, need_title)

    def extract_target(
            self,
            image: ImageType,
            sub_name='det',
            split_area=None,
            sort=True,
            expect_area=None,
            contrast=None,
            sharpness=None
    ):
        predictions = self.session.engine[sub_name].predict(image)

        im_group, boxes = [], []
        try:
            if sort:
                predictions = sorted(predictions, key=lambda t: t[0])
            boxes = [
                list(bounding_box) for bounding_box in predictions
            ]
        except ValueError:
            boxes = []

        if split_area:
            ims_in, ims_out, boxes_in, boxes_out = [], [], [], []
            for box in boxes:
                if self.in_box(box, split_area):
                    box = self.box_range_filter(box, split_area)
                    if expect_area and self.in_box(box, expect_area):
                        continue
                    ims_in.append(image.crop(box))
                    boxes_in.append(self.box_range_filter(box, split_area))
                else:
                    if expect_area and self.in_box(box, expect_area):
                        continue
                    ims_out.append(image.crop(self.std_box(box)))
                    boxes_out.append(box)

            if self.param.get('debug'):
                if not os.path.exists("img"):
                    os.makedirs("img")

                for idx, title_im in enumerate(ims_in):
                    title_im.save(f"img/in_{idx}.png")

                for idx, main_im in enumerate(ims_out):
                    main_im.save(f"img/out_{idx}.png")

            return ims_in, ims_out, boxes_in, boxes_out
        for box in boxes:
            if expect_area and self.in_box(box, expect_area):
                boxes.remove(box)
                continue
            im = image.crop(self.std_box(box))
            if contrast:
                im = PIL.ImageEnhance.Contrast(im).enhance(contrast)
            if sharpness:
                im = PIL.ImageEnhance.Sharpness(im).enhance(sharpness)
            im_group.append(im)
        if self.param.get('debug'):
            for idx, title_im in enumerate(im_group):
                title_im.save(f"img/im_{idx}.png")
        return list(im_group), list(boxes)

    @classmethod
    def word_order(cls, lines, dictionary, label_map, outputs):
        if len(outputs.shape) == 3:
            outputs = outputs.squeeze(1)
        target = ''.join([label_map[single] for single in np.argmax(outputs, axis=1)])
        target = set(target)
        result = (-1, "")

        for index, i in enumerate(dictionary):
            score = len(target & i) / len(target | i)
            if score > result[0]:
                result = (score, lines[index])
        return result[1]

    @staticmethod
    def semantic_inference(text: str, inference_map: dict, result_group: list, boxes_group: list):
        for k, v in inference_map.items():
            if k == 'obj_index':
                continue
            if '***' in k:
                part = k.split("***", 2)
                text = text.replace(part[0], "").replace(part[1], v)
            else:
                text = text.replace(k, "" if v == "remove" else v)
        items = tuple()
        if 'same:' in text:
            group = text.split("$")
            attr_index = group.index("".join([_ for _ in group if 'same' in _]))
            src, attribute, target = group[0:attr_index], group[attr_index], group[attr_index + 1:]
            _, index = attribute.split(":")
            index = int(index)
            src_index, need_attr = None, ""
            for i, predictions in enumerate(result_group):
                items, score = zip(*predictions)
                if set(src) <= set(items):
                    need_attr = items[index]
                    src_index = i
                    break
            for i, predictions in enumerate(result_group):
                items, score = zip(*predictions)
                if set(target) <= set(items) and need_attr == items[index] and i != src_index:
                    return items, ([attribute], boxes_group[i])
            for i, predictions in enumerate(result_group):
                items, score = zip(*predictions)
                if set(target) <= set(items) and i != src_index:
                    return items, ([attribute], boxes_group[i])
            return items, ([attribute], [])

        elif '_side$' in text:
            group = text.split("$")
            side_index = group.index("".join([_ for _ in group if '_side' in _]))
            src, attribute, target = group[0:side_index], group[side_index], group[side_index + 1:]
            src_coord, target_item = None, None
            for i, predictions in enumerate(result_group):
                items, score = zip(*predictions)
                if set(src) <= set(items):
                    src_coord = boxes_group[i]
                elif set(target) <= set(items):
                    target_item = target
            return target_item, ([attribute], src_coord)

        elif '$' in text:
            attribute = [_ for _ in text.split("$") if _]
            index_group = []
            for i, predictions in enumerate(result_group):
                items, score = zip(*predictions)
                if 'lower' in attribute:
                    if set(items) > (set(attribute) - {'lower'}) and items[inference_map['obj_index']].islower():
                        index_group.append(i)
                elif 'upper' in attribute:
                    if set(items) > (set(attribute) - {'upper'}) and items[inference_map['obj_index']].isupper():
                        index_group.append(i)
                elif set(items) >= set(attribute):
                    index_group.append(i)
            if len(index_group) > 1:
                return attribute, (attribute, [boxes_group[_] for _ in index_group])
            elif len(index_group) == 1:
                need_items, _ = zip(*result_group[index_group[0]])
                return need_items, (attribute, boxes_group[index_group[0]])

        else:
            title = [text]
            for i, predictions in enumerate(result_group):
                items, score = zip(*predictions)
                if set(items) >= set(title):
                    return items, (title, boxes_group[i])

        return items, tuple([[], []])


class ClickByTextTitleLogic(BaseClickLogic):

    """
    文本标题逻辑
    """

    def process(self, image: InputImage, title: Title = None) -> Response:
        title = list(title) if title else None
        # print(title)
        target_ims, boxes = self.extract_target(image=image.pil)
        # calc_score = self.project_config.get('calc_score') in [None, True]
        if title:
            need_text, block_classifications = self.session.engine['cls'].batch_predict(
                list(target_ims),
                need_title=title,
                order_func=None,
            )
        else:
            block_classifications = self.session.engine['cls'].batch_predict(
                list(target_ims),
                order_func=None,
            )

        blocks = Blocks.Archive.from_text(block_classifications, boxes)

        return BlockOrder.one_to_one(blocks, list(locals().get('need_text'))) if title else blocks


class ClickBySimTextTitleLogic(BaseClickLogic):

    # TODO
    default_font = PIL.ImageFont.truetype(font=os.path.join(resource_path, "fonts", "msyh.ttc"), size=54)

    @classmethod
    def draw_text(cls, char):
        bg = PIL.Image.new("RGB", (64, 64), (255, 255, 255))
        draw = PIL.ImageDraw.Draw(bg)
        draw.text((5, -5), char, fill=(0, 0, 0), font=cls.default_font)
        return bg

    def process(self, image: InputImage, title: Title = None) -> Response:
        if not title:
            raise RuntimeError("请输入限定文本")

        ims_title = [
            self.draw_text(char) for char in title
        ]

        ims_main, boxes_main = self.extract_target(
            image=image.pil,
            expect_area=self.project_config.get('except_area')
        )
        return self.similarity_process(ims_title, ims_main, boxes_main)


class ClickBySemanticLogic(BaseClickLogic):

    """
    语义模型逻辑
    """

    def process(self, image: InputImage, title: Title = None) -> Response:
        target_ims, boxes = self.extract_target(image=image.pil)
        block_classifications = self.session.engine['cls'].batch_predict(
            list(target_ims),
            # need_title=title
        )
        title_desc = title
        title_desc, attribute = self.semantic_inference(
            title_desc,
            self.project_config.get('inference_map'),
            block_classifications,
            boxes,
        )
        attr, src_coord = attribute
        if self.param.get('debug'):
            print(attribute, '--->', block_classifications)
        blocks = Blocks.Archive.from_index(block_classifications, boxes)
        return BlockOrder.many_and_many(blocks, list(title_desc), attr, src_coord)


class ClickByOrderLogic(BaseClickLogic):

    """
    语序模型逻辑
    """
    @classmethod
    def fault_tolerance(cls, need_text: str, block_classifications: list):
        predict_chars = [_[0] for _ in block_classifications]
        nil_idx = [i for i, _ in enumerate(predict_chars) if _ == '-']
        # random.shuffle(nil_idx)
        for char in need_text:
            if char not in predict_chars and nil_idx:
                idx = nil_idx.pop()
                block_classifications[idx] = [char]
        return block_classifications

    def process(self, image: InputImage, title: Title = None) -> Response:

        target_ims, boxes = self.extract_target(image=image.pil)

        cls_engine = self.session.engine['cls']
        lines, dictionary = cls_engine.model_entity.corpus
        if self.param and 'raw_classifications' in self.param:
            order_func = None
        else:
            order_func = lambda label_map, outputs: self.word_order(
                lines, dictionary, label_map=label_map, outputs=outputs
            )

        need_title, block_classifications = cls_engine.batch_predict(
            list(target_ims),
            order_func=order_func,
        )
        if order_func:
            block_classifications = self.fault_tolerance(need_title, block_classifications)

        blocks = Blocks.Archive.from_text(block_classifications, boxes)
        return BlockOrder.one_to_one(blocks, list(need_title)) if order_func else blocks


class ClickSliderLogic(BaseClickLogic):

    """
    滑块逻辑
    """

    def process(self, image: InputImage, title: Title = None) -> Response:

        if title:
            title = self.parse_title(title, fill_bg=False)
            if resize_argv := self.project_config.get('resize'):
                if 'main' in resize_argv:
                    image.pil = image.pil.resize(tuple(resize_argv['main']))
                if 'title' in resize_argv:
                    title = title.resize(tuple(resize_argv['title']))
            # else:
            #     title = title.resize((title.width, image.pil.height))
            image.pil = image.pil.convert("RGBA")
            y = int(self.param['y']) if self.param.get('y') else 0
            image.pil.paste(title, (0, y), title)

        target_ims, boxes = self.extract_target(image=image.pil)
        if not boxes:
            raise RuntimeError("识别失败")
        block_classifications = [[('滑块', boxes[0:1][0][5])]]
        blocks = Blocks.Archive.from_index(block_classifications, boxes[0:1])
        return blocks

    def dumps(self, response: Response) -> tuple[str, float]:
        coordinates = response.dump_bounding_box()
        result_text = coordinates[0][0]
        return result_text, response.score
