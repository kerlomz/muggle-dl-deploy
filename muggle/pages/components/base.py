#!/usr/bin/env python3
# -*- coding:utf-8 -*-
from __future__ import annotations
import base64
import os.path
import gradio as gr
from typing import List, Union, Dict, Callable, TypeVar, Optional
from abc import abstractmethod
from dataclasses import dataclass, field
from muggle.entity import ComponentType
from muggle.pages.components.examples import Examples


T_Component = TypeVar('T_Component', bound='BaseParametricComponent')


class MapFnTemplate:

    @classmethod
    def empty(cls, **kwargs):
        items_cfgs = [{
            "value": "",
        }]
        return items_cfgs


@dataclass
class ComponentItem:
    value: Union[Dict] = None
    instance: Union[
        gr.Radio, gr.Textbox, gr.Image, gr.Label, gr.Markdown,
        gr.Number, gr.Button, gr.Dataframe, gr.HTML, Examples, gr.Dropdown, gr.Code
    ] = None

    @property
    def name(self):
        if not self.instance:
            return None
        return self.instance.elem_id


@dataclass
class ComponentsItem:
    text: ComponentItem = field(default_factory=ComponentItem)
    label: ComponentItem = field(default_factory=ComponentItem)
    radio: ComponentItem = field(default_factory=ComponentItem)
    image: ComponentItem = field(default_factory=ComponentItem)
    images: List[ComponentItem] = field(default_factory=lambda: [])
    number: ComponentItem = field(default_factory=ComponentItem)
    markdown: ComponentItem = field(default_factory=ComponentItem)
    dropdown: ComponentItem = field(default_factory=ComponentItem)
    example: ComponentItem = field(default_factory=ComponentItem)
    button: ComponentItem = field(default_factory=ComponentItem)
    table: ComponentItem = field(default_factory=ComponentItem)
    html: ComponentItem = field(default_factory=ComponentItem)
    code: ComponentItem = field(default_factory=ComponentItem)


@dataclass
class ComponentsValues:
    text: Union[Dict] = field(default_factory=lambda: {})
    label: Union[Dict] = field(default_factory=lambda: {})
    radio: Union[Dict] = field(default_factory=lambda: {})
    image: Union[Dict] = field(default_factory=lambda: {})
    images: List[Union[Dict]] = field(default_factory=lambda: [])
    number: Union[Dict] = field(default_factory=lambda: {})
    markdown: Union[Dict] = field(default_factory=lambda: {})
    dropdown: Union[Dict] = field(default_factory=lambda: {})
    table: Union[Dict] = field(default_factory=lambda: {})
    html: Union[Dict] = field(default_factory=lambda: {})
    code: Union[Dict] = field(default_factory=lambda: {})


class BaseParametricComponent:

    def __init__(self, name: str, component_type: ComponentType, map_fn: Union[Callable, str, None], value=None):
        self.name: str = name
        self.value = value
        if map_fn == 'empty':
            map_fn = MapFnTemplate.empty
        self.map_fn: Union[Callable, str, None] = map_fn
        self.component_type: ComponentType = component_type

    @classmethod
    def copy_dicts(cls, value):
        return gr.update(**value.copy()) if value else gr.update(**{})

    @classmethod
    def values_from_component(cls, component: ComponentsItem) -> ComponentsValues:
        return ComponentsValues(
            text=cls.copy_dicts(component.text.value),
            radio=cls.copy_dicts(component.radio.value),
            label=cls.copy_dicts(component.label.value),
            image=cls.copy_dicts(component.image.value),
            images=[cls.copy_dicts(_.value) for _ in component.images],
            number=cls.copy_dicts(component.number.value),
            markdown=cls.copy_dicts(component.markdown.value),
            dropdown=cls.copy_dicts(component.dropdown.value),
            html=cls.copy_dicts(component.html.value),
            code=cls.copy_dicts(component.code.value),
        )

    @classmethod
    def path2image(cls, im_path):
        ext = im_path.split(".")[-1]
        return f'data:image/{ext};base64,{base64.b64encode(open(im_path, "rb").read()).decode()}'

    @classmethod
    def components2instances(cls, components: List[T_Component]) -> List[gr.components.Component]:
        outs = []
        for c in components:
            if hasattr(c, 'instances'):
                outs.extend(c.instances)
            else:
                outs.append(c.instance)
        return outs

    def change(
            self, fn: Callable, inputs: List, outputs: List
    ) -> Callable:
        return self.instance.change(
            fn,
            self.components2instances(inputs),
            self.components2instances(outputs)
        )

    def parametric_fn(
        self,
        config: dict,
        **kwargs
    ):

        items_cfgs = self.map_fn(**kwargs)
        return self.base_parametric_fn(
            getattr(self, 'component'),
            config=config,
            items_cfgs=items_cfgs,
        )

    def base_change_fn(self, **kwargs) -> ComponentsValues:
        items_cfgs = self.map_fn(**kwargs)
        components_values: ComponentsValues = self.values_from_component(getattr(self, 'component'))
        component_value = self.dicts(
            components_values=components_values,
            items_cfgs=items_cfgs,
            raw_data=False
        )
        return component_value

    def item_update_fn(self, **kwargs):
        items_cfgs = self.map_fn(**kwargs)
        components_values: ComponentsValues = self.values_from_component(getattr(self, 'component'))
        component_value = self.dicts(
            components_values=components_values,
            items_cfgs=items_cfgs,
            raw_data=True
        )
        return component_value

    def base_parametric_fn(
        self,
        component: ComponentsItem,
        config: dict,
        items_cfgs: List[Dict[str, Union[str, dict, list]]],
    ):
        components_values: ComponentsValues = self.values_from_component(component)
        component_value = self.dicts(
            components_values=components_values,
            items_cfgs=items_cfgs,
            raw_data=False
        )
        config = self.parametric_change_fn(
            components=component,
            values=component_value,
            config=config
        )
        return config

    @property
    @abstractmethod
    def instance(self): ...

    @abstractmethod
    def define(self, **kwargs): ...

    @abstractmethod
    def parametric_change_fn(self, components: ComponentsItem, values: ComponentsValues, config: dict): ...

    def dicts(
            self,
            components_values: ComponentsValues,
            items_cfgs: List[Dict[str, Union[str, dict, list, List[dict]]]],
            raw_data: bool
    ):
        if not items_cfgs:
            return components_values
        for item_cfg in items_cfgs:
            item_name = item_cfg.get('name', '')
            item_type = item_cfg.get('type') if item_cfg.get('type') else self.component_type.value
            item_value = item_cfg.get('value')
            item_visible = item_cfg.get('item_visible', True)
            if item_type == 'radio':
                option_names = list(item_value.values())
                components_values.radio.update(
                    visible=True, label=item_name, choices=option_names, value=option_names[0]
                )
            elif item_type == 'text':
                default_value = item_cfg.get('default_value', None)
                components_values.text.update(
                    visible=item_visible,
                    # label=item_name,
                    placeholder=item_value if item_visible else "",
                    value=str(default_value) if default_value else None
                )
                if item_visible is False:
                    components_values.text.update(value=item_value)
                if item_name:
                    components_values.text.update(label=item_name)
            elif item_type == 'images':
                image_item_count = len(item_value)
                if image_item_count == 1:
                    components_values.image.update(
                        visible=True,
                        label="图片标题",
                        value=item_value[0].get('path')
                    )
                else:
                    for idx in list(range(9)):
                        if idx < image_item_count and (path := item_value[idx].get('path')):
                            im_title_val = path if raw_data else self.path2image(path)
                            im_title_label = f"{item_name} {item_value[idx].get('label')}"
                        else:
                            im_title_val = None
                            im_title_label = f"图片标题 {idx}"

                        components_values.images[idx].update(
                            visible=True if idx < image_item_count else False,
                            label=im_title_label,
                            value=im_title_val
                        )
            elif item_type == 'image':
                if raw_data and item_value and os.path.exists(item_value):
                    im_title_val = item_value
                elif not raw_data and item_value and os.path.exists(item_value):
                    im_title_val = self.path2image(item_value)
                else:
                    im_title_val = None
                # im_title_val = item_value if raw_data else self.path2image(item_value)
                # print(im_title_val)
                components_values.image.update(
                    # type='path',
                    # shape=item_cfg.get('shape', None),
                    visible=item_visible,
                    value=im_title_val
                )
            elif item_type == 'dropdown':
                components_values.dropdown.update(
                    visible=item_visible,
                    value=item_value
                )
            elif item_type == 'html':
                components_values.html.update(
                    visible=item_visible,
                    value=item_value
                )
            elif item_type == 'code':
                components_values.code.update(
                    visible=item_visible,
                    value=item_value
                )
            elif item_type == 'markdown':
                components_values.markdown.update(
                    value=gr.Markdown().postprocess(item_value),
                    visible=item_visible
                )
            elif item_type == 'label':
                components_values.label.update(
                    # label=item_name,
                    visible=item_visible,
                    value=item_value
                )
            elif item_type == 'number':
                components_values.number.update(
                    label=item_name,
                    visible=item_visible,
                    value=item_value
                )
            elif item_type == 'table':
                components_values.table.update(
                    value=item_value
                )
        return components_values
