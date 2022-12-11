#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import re
import PIL.Image
from muggle.entity import BoundingBox


class LogicAuxiliary:
    class Arithmetic(object):

        opo_map = {
            "*": '/',
            '+': '-',
            '-': '+',
            '/': '*',
            '×': '÷',
            '÷': '×',
        }

        @classmethod
        def calc(cls, formula):
            if formula.startswith("?") and formula[1] in cls.opo_map:
                formula = f"{cls.opo_map[formula[1]]}".join(formula[2:].split("=")[::-1])
            if '?=' in formula:
                op = formula[formula.index('?') - 1]
                is_reverse = op not in ['-', '÷']
                digits = formula.split(formula[formula.index('?') - 1] + "?=")
                if is_reverse:
                    digits = digits[::-1]
                    op = cls.opo_map[op]
                formula = op.join(digits)
            formula = formula.replace("×", "*").replace("÷", "/").replace("=", "").replace("?", "")
            formula = re.sub(' ', '', formula)
            formula_ret = 0
            match_brackets = re.search(r'\([^()]+\)', formula)
            if match_brackets:
                calc_result = cls.calc(match_brackets.group().strip("(,)"))
                formula = formula.replace(match_brackets.group(), str(calc_result))
                return cls.calc(formula)
            else:
                formula = formula.replace('--', '+').replace('++', '+').replace('-+', '-').replace('+-', '-')
                count = 0
                while re.findall(r"[*/]", formula):
                    count += 1
                    get_formula = re.search(r"[.\d]+[*/]+[-]?[.\d]+", formula)
                    if get_formula:
                        get_formula_str = get_formula.group()
                        if get_formula_str.count("*"):
                            formula_list = get_formula_str.split("*")
                            ret = float(formula_list[0]) * float(formula_list[1])
                        else:
                            formula_list = get_formula_str.split("/")
                            ret = float(formula_list[0]) / float(formula_list[1])
                        formula = formula.replace(get_formula_str, str(ret)).replace('--', '+').replace('++', '+')
                    if not get_formula and count > 10:
                        return -999
                formula = re.findall(r'[-]?[.\d]+', formula)
                for num in formula:
                    formula_ret += float(num)
            return formula_ret

    @classmethod
    def _crop(cls, main_image: PIL.Image.Image, boxes: BoundingBox):
        for index, box in enumerate(boxes):
            x1, y1, x2, y2, *extra = tuple(map(int, box))
            x1, y1 = x1 if x1 >= 0 else 0, y1 if y1 >= 0 else 0
            cropped = main_image.crop((x1, y1, x2, y2))
            if 0 in cropped.size:
                continue
            yield cropped, [x1, y1, x2, y2]
        return

    @classmethod
    def crop(cls, image: PIL.Image.Image, crop_params):
        im_group, boxes = zip(*[
            (im_item, bounding_box) for im_item, bounding_box in cls._crop(image, crop_params)
        ])
        return list(im_group), list(boxes)

    @staticmethod
    def _coordinates_calc(param):
        result_group = []
        start_x, start_y = param['start_pos']
        crop_width, crop_height = param['crop_shape']
        cols, rows = param['crop_num']
        interval_w, interval_h = param['interval']
        start_h, end_h = start_y, start_y + crop_height
        for row in range(rows):
            start_w = start_x
            end_w = start_w + crop_width
            for col in range(cols):
                pos_range = [[start_w, end_w], [start_h, end_h]]
                result_group.append(pos_range)
                start_w = end_w + interval_w
                end_w = start_w + crop_width
            start_h = end_h + interval_h
            end_h = start_h + crop_height
        return result_group

    @classmethod
    def get_crop_param(cls, param):
        group = []
        pos_ranges = cls._coordinates_calc(param)
        for pos_range in pos_ranges:
            corp_arr = [pos_range[0][0], pos_range[1][0], pos_range[0][1], pos_range[1][1]]
            group.append(corp_arr)
        return group