#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import gradio as gr
from typing import Union, List, Dict, Callable
from dataclasses import dataclass, field
from muggle.pages.components.base import BaseParametricComponent, ComponentItem, ComponentsItem, ComponentsValues
from muggle.pages.utils import GradioCfg
# from muggle.project_config import get_config
from muggle.entity import ComponentType
from collections import namedtuple


class ParametricInputs(BaseParametricComponent):

    def __init__(self, name, component_type: ComponentType, map_fn: Callable):
        super(ParametricInputs, self).__init__(name, component_type, map_fn, value=None)
        self.component: ComponentsItem = self.define(name, component_type)

    @property
    def instance(self):
        if self.component_type is ComponentType.InputGroup:
            Instance = namedtuple('Instance', ['images', 'radio', 'text', 'image'])
            return Instance(
                images=[_.instance for _ in self.component.images],
                radio=self.component.radio.instance,
                text=self.component.text.instance,
                image=self.component.image.instance,
            )
        elif self.component_type is ComponentType.Image:
            return self.component.image.instance
        raise RuntimeError(f"当前组件类别 [{self.component_type}] 暂不支持")

    def define(self, name, component_type):
        components = ComponentsItem()
        if component_type is ComponentType.InputGroup:
            with gr.Box():
                components.text = ComponentItem(
                    value=dict(visible=False, value=""),
                    instance=gr.Textbox(
                        visible=False, interactive=True, elem_id=f"${name}_text_ig"
                    )
                )
                components.radio = ComponentItem(
                    value=dict(visible=False, choices=[], value=""),
                    instance=gr.Radio(
                        [],
                        type="index",
                        interactive=True,
                        visible=False,
                        elem_id=f"${name}_radio_ig"
                    )
                )
                components.image = ComponentItem(
                    value=dict(visible=False, value=None),
                    instance=gr.components.Image(
                        type='filepath',
                        label=f"图片标题",
                        interactive=True,
                        visible=False,
                        elem_id=f"${name}_image_ig"
                    )
                )
                with gr.Row():
                    for i in range(9):
                        with gr.Column():
                            components.images.append(
                                ComponentItem(
                                    value=dict(visible=False, value=None),
                                    instance=gr.components.Image(
                                        type='filepath',
                                        label=f"图片标题 {i}",
                                        interactive=True,
                                        visible=False,
                                        elem_id=f"${name}_image_ig_{i}"
                                    )
                                )
                            )
        elif component_type is ComponentType.Image:
            components.image = ComponentItem(
                value=dict(visible=False, value=None),
                instance=gr.components.Image(
                    type='filepath',
                    label=f"图片输入",
                    interactive=True,
                    visible=True,
                    elem_id=f"${name}_image_i"
                )
            )
        return components

    def parametric_change_fn(
            self,
            components: ComponentsItem,
            values: ComponentsValues,
            config: dict
    ):
        cfg = GradioCfg(config)
        if self.component_type is ComponentType.Image:
            cfg.update(components.image.name, **values.image)
        elif self.component_type is ComponentType.InputGroup:
            cfg.update(components.radio.name, **values.radio)
            cfg.update(components.text.name, **values.text)
            cfg.update(components.image.name, **values.image)
            for idx, im_dict in enumerate(values.images):
                cfg.update(components.images[idx].name, **im_dict)
        return cfg.config


class ParametricInputTitle(ParametricInputs):

    def __init__(self, name, map_fn: Callable):
        super(ParametricInputTitle, self).__init__(name, ComponentType.InputGroup, map_fn)

    def change_fn(self, **kwargs):
        return self.base_change_fn(**kwargs)

    def update_fn(self, **kwargs):
        values = self.item_update_fn(**kwargs)
        return (values.text, values.radio, values.image) + tuple(values.images)

    @property
    def instances(self):
        images_instances = [_.instance for _ in self.component.images]
        return [
                   self.component.text.instance,
                   self.component.radio.instance,
                   self.component.image.instance
               ] + images_instances


class ParametricInputImage(ParametricInputs):

    def __init__(self, name, map_fn, label=None):
        super(ParametricInputImage, self).__init__(name, ComponentType.Image, map_fn)
        self.label = label if label else "图片"

    def change_fn(self, **kwargs):
        return self.base_change_fn(**kwargs).image

    def update_fn(self, **kwargs):
        return self.item_update_fn(**kwargs).image
