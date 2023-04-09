#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import PIL.Image
import PIL.GifImagePlugin
import math
import datetime
from enum import Enum, unique
from typing import Dict, Union, List, Tuple, Optional
from collections import OrderedDict
from types import SimpleNamespace
from collections import namedtuple
from pydantic import BaseModel
import numpy as np
from dataclasses import dataclass, field

ImageType = Union[
    PIL.GifImagePlugin.GifImageFile,
    PIL.Image.Image,
    List[PIL.Image.Image],
    List[PIL.GifImagePlugin.GifImageFile],
]


@unique
class RuntimeType(Enum):
    ONNXRuntime = 'ONNXRuntime'


@unique
class APIType(Enum):
    TEXT = 'Text'
    IMAGE = 'Image'
    DOC = 'DOC'
    PREVIEW = 'PREVIEW'


@unique
class DumpType(Enum):
    classification = 'classification'
    coordinate = 'coordinate'
    bounding_box = 'bounding_box'


@unique
class ComponentType(Enum):
    Radio = 'radio'
    Image = 'image'
    TextBox = 'text'
    Markdown = 'markdown'
    Label = 'label'
    Dropdown = 'dropdown'
    InputGroup = 'input_group'
    Number = 'number'
    Example = 'example'
    Button = 'button'
    Table = 'table'
    HTML = 'html'
    Code = 'code'


class RequestBody(BaseModel):
    image: Union[str, List[str]] = None
    project_name: str = None
    sign: str = None
    title: Union[str, List[str]] = None
    token: str = None
    extra: dict = {}


class ResponseBody(BaseModel):
    uuid: str = None
    data: Union[int, str, List[int], List[str]] = None
    image: Optional[bytes] = None
    score: Union[List[float], float]
    consume: float


@dataclass
class ImageEntity:
    pil: ImageType
    hash: str
    raw_bytes: bytes
    base64: str


@dataclass
class LogEntity:
    api_type: APIType
    ip: str
    ua: str
    project_name: str
    consume: float = field(init=False)
    predictions: Optional[tuple[str, float]] = field(init=False)
    title: str

    @property
    def log_text(self):
        api = f"{self.api_type}" if self.api_type else ""
        ip = f"IP [{self.ip}]" if self.ip else ""
        ua = f"UA [{self.ua}]" if self.ua else ""
        project_name = f"[{self.project_name}]" if self.project_name else ""
        consume = f"- 总耗时 [{round(self.consume, 2)} 毫秒] -" if self.consume is not None else ""
        predictions = f"[{self.predictions[0]} - ({round(self.predictions[1], 2)})]" if self.predictions is not None else ""
        title = f"[{self.title}]"[:100] if self.title else ""
        return "  ".join([
            _ for _ in [api, ip, ua, project_name, consume, predictions, title] if _
        ])


def missing_request_param(required_params, body: RequestBody):
    missing_required_param = []
    for name, value in zip(
            required_params,
            [getattr(body, param) for param in required_params]
    ):
        if not value:
            missing_required_param.append(name)
    if any(missing_required_param):
        return SimpleNamespace(is_missing=True, names=missing_required_param)

    return SimpleNamespace(is_missing=False, names=missing_required_param)


class Block:

    def __init__(
            self,
            score,
            classification: Union[str, List[str]],
            coordinate: List[int] = None,
            bounding_box: list[int] = None,
            index: int = None
    ):
        self.index = index
        self.classification = classification
        self.coordinate = coordinate
        self.bounding_box = bounding_box
        self.score = score

    def copy(self):
        block = Block(
            score=self.score, classification=self.classification, coordinate=self.coordinate, index=self.index
        )
        block.bounding_box = self.bounding_box
        return block

    def dumps(self):
        item = {"classification": self.classification}
        if self.coordinate:
            item['coordinate'] = self.coordinate
        if self.bounding_box:
            item['bounding_box'] = self.bounding_box
        if self.score:
            item['score'] = self.score
        if self.index:
            item['index'] = self.index
        return item


class Blocks:

    def __init__(self):
        super().__init__()
        self.map: OrderedDict[int or str, Block] = OrderedDict()

    def __setitem__(self, key: Union[int, str], value: Block):
        self.map[key] = value.copy()

    def get(self, key: str) -> Block:
        return self.map.get(key)

    def __iter__(self) -> tuple[int or str, Block]:
        yield from self.map.items()

    @property
    def classifications(self):
        return [v.classification for k, v in self.map.items()]

    @property
    def indexes(self):
        return [v.index for k, v in self.map.items()]

    @property
    def score(self):
        return float(np.prod([v.score for k, v in self.map.items()]))

    def append(self, key: Union[int, str], block: Block):
        self.__setitem__(key=key, value=block)

    def dumps(self, filter_blank=True):
        if not self.map:
            return []
        result = []
        from_index = self.map and isinstance(list(self.map.keys())[0], int)
        if from_index:
            for i in range(len(self.map)):
                it = self.map[i]
                if filter_blank and isinstance(it.classification, str) and it.classification in ['', '-']:
                    continue
                result.append(it.dumps())
        else:
            for k, v in self.map.items():
                if filter_blank and isinstance(v.classification, str) and v.classification in ['', '-']:
                    continue
                result.append(v.dumps())
        return result

    def dumps_specified(self, dump_type: DumpType, filter_blank=True):
        result = []
        from_index = self.map and isinstance(list(self.map.keys())[0], int)
        if from_index:
            for i in range(len(self.map)):
                it = self.map[i]
                if filter_blank and isinstance(it.classification, str) and it.classification in ['', '-']:
                    continue
                result.append(getattr(it, dump_type.value))
        else:
            for k, v in self.map.items():
                if filter_blank and isinstance(v.classification, str) and v.classification in ['', '-']:
                    continue
                result.append(getattr(v, dump_type.value))
        return result

    def dumps_coordinates(self, filter_blank=True):
        coordinates = self.dumps_specified(dump_type=DumpType.coordinate, filter_blank=filter_blank)
        return coordinates

    def dump_bounding_box(self, filter_blank=True):
        bounding_box = self.dumps_specified(dump_type=DumpType.bounding_box, filter_blank=filter_blank)
        return bounding_box

    class Import:

        @staticmethod
        def by_one(score, classification, coordinate=None, index=0, bounding_box=None):
            new_blocks = Blocks()
            block = Block(
                score=score,
                classification=classification,
                coordinate=coordinate,
                index=index,
                bounding_box=bounding_box
            )
            new_blocks.append(index, block)
            return new_blocks

        @staticmethod
        def by_index(block_list: list[Block] = None):
            new_blocks = Blocks()
            if not block_list:
                return new_blocks
            for i, block in enumerate(block_list):
                new_blocks.append(i, block)
            return new_blocks

        @staticmethod
        def by_text(block_list: list[Block] = None):
            new_blocks = Blocks()
            if not block_list:
                return new_blocks
            for i, block in enumerate(block_list):
                new_blocks.append(block.classification, block)
            return new_blocks

        @staticmethod
        def by_params(score, classifications, coordinates, boxes):
            new_blocks = Blocks()
            for i, (score, classification, coordinate, bounding_box) in enumerate(
                    zip(score, classifications, coordinates, boxes)
            ):
                new_blocks.append(
                    i, Block(score=score, classification=classification, coordinate=coordinate, bounding_box=bounding_box)
                )
            return new_blocks

    class Archive:

        @staticmethod
        def from_text(block_classifications, coordinates):
            block_list = []
            for index, (block_classification, bounding_box) in enumerate(zip(*(block_classifications, coordinates))):
                if isinstance(block_classification[0], tuple):
                    block_classification, *scores = zip(*block_classification)
                    score = float(np.prod(scores)) if scores else -1
                else:
                    score = -1.
                for cls in block_classification:
                    block = Block(
                        score=score,
                        classification=cls,
                        coordinate=Blocks.Util.get_coordinates(bounding_box),
                        bounding_box=bounding_box,
                    )
                    block_list.extend([block])
            blocks = Blocks.Import.by_text(block_list)
            return blocks

        @staticmethod
        def from_index(block_classifications, coordinates):
            block_list = []
            for index, (block_classification, bounding_box) in enumerate(zip(*(block_classifications, coordinates))):
                if (b := block_classification) and isinstance(b, list) and isinstance(b[0], str):
                    block_classification, score = block_classification, -1
                else:
                    block_classification, *scores = zip(*block_classification)
                    score = float(np.prod(scores)) if scores else -1
                block_list.append(
                    Block(
                        score=score,
                        classification=block_classification,
                        coordinate=Blocks.Util.get_coordinates(bounding_box),
                        bounding_box=bounding_box,
                        index=index,
                    )
                )
            blocks = Blocks.Import.by_index(block_list)
            return blocks

    class Util:

        @staticmethod
        def distance(p0, p1):
            return math.sqrt((p0[0] - p1[0]) ** 2 + (p0[1] - p1[1]) ** 2)

        @staticmethod
        def positive_integer(x):
            return int(x) if x > 0 else 0

        @staticmethod
        def get_coordinates(box):
            x1, y1, x2, y2 = (Blocks.Util.positive_integer(_) for _ in box[:4])
            return [int((x1 + x2) / 2), int((y1 + y2) / 2)]

        @staticmethod
        def skip_opposite_position_coordinates(attr, origin, target):
            if not target:
                return False
            x1, y1, x2, y2 = target[:4]
            if '_side' in attr[0] and [x1, y1, x2, y2] == origin[:4]:
                return True
            if attr[0] == 'left_side' and x1 + x2 < origin[0] + origin[2]:
                return True
            elif attr[0] == 'right_side' and x1 + x2 > origin[0] + origin[2]:
                return True
            elif attr[0] == 'down_side' and y1 + y2 > origin[1] + origin[3]:
                return True
            elif attr[0] == 'up_side' and y1 + y2 < origin[1] + origin[3]:
                return True
            else:
                return False


Title = Union[PIL.Image.Image, np.ndarray, str, List[str], List[PIL.Image.Image], ImageEntity, List[ImageEntity]]
InputImage = Optional[ImageEntity]
BoundingBox = list[tuple[int, int, int, int, int, float]]
ClassificationLabel = Union[
    int, str, list[str], list[int], list[tuple[str, float]], list[tuple[int, float]], list[list[str, float]]
]
DiscriminatorLabel = bool
RegressionLabel = Union[float, List[float]]

Response = Union[
    BoundingBox, RegressionLabel, ClassificationLabel, Blocks, Block, tuple, DiscriminatorLabel, PIL.Image.Image
]