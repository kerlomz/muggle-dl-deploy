#!/usr/bin/env python3
# -*- coding:utf-8 -*-
from __future__ import annotations
import io
import base64
import json
import gradio as gr
import gradio.processing_utils
from gradio_client import utils as client_utils
from typing import Union, List, Dict, Callable, Optional, Any
from muggle.pages.components.base import BaseParametricComponent, ComponentItem, ComponentsItem, ComponentsValues
from muggle.pages.utils import GradioCfg
from muggle.entity import ComponentType
from muggle.pages.components.examples import Examples
from muggle.pages.components.utils import DisplayUtils

gradio.processing_utils.encode_pil_to_base64 = DisplayUtils.encode_pil_to_base64


class BaseParametricDisplays(BaseParametricComponent):

    def __init__(
            self, name: str,
            label: str,
            map_fn: Union[Callable, str, None],
            component_type: ComponentType,
            interactive=True,
            visible=True,
            value=None,
            **kwargs
    ):
        super(BaseParametricDisplays, self).__init__(name, component_type, map_fn, value)
        self.label = label
        self.value = value
        self.visible = visible
        self.interactive = interactive
        self.component: ComponentsItem = self.define(name, label, value, component_type, **kwargs)

    def change_fn(self, **kwargs):
        if change_fn := getattr(self.base_change_fn(**kwargs), str(self.component_type.value), None):
            return change_fn
        raise RuntimeError(f"当前组件类别 [{self.component_type}] 暂不支持")

    def update_fn(self, **kwargs):
        if update_fn := getattr(self.item_update_fn(**kwargs), str(self.component_type.value), None):
            return update_fn
        raise RuntimeError(f"当前组件类别 [{self.component_type}] 暂不支持")

    @property
    def instance(self):
        if component := getattr(self.component, str(self.component_type.value), None):
            return component.instance
        raise RuntimeError(f"当前组件类别 [{self.component_type}] 暂不支持")

    def define(self, name, label, default_value, component_type: ComponentType, **kwargs):
        components = ComponentsItem()
        if component_type is ComponentType.TextBox:
            components.text = ComponentItem(
                value=dict(visible=self.visible, value=default_value if default_value else ""),
                instance=gr.Textbox(
                    label=label,
                    visible=self.visible,
                    interactive=self.interactive,
                    elem_id=f"${name}_text_d",
                    value="" if default_value is None else str(default_value),
                    placeholder=kwargs.get('placeholder', None)
                )
            )
        elif component_type is ComponentType.Radio:
            components.radio = ComponentItem(
                value=dict(visible=self.visible, choices=[], value=default_value if default_value else ""),
                instance=gr.Radio(
                    [],
                    label=label,
                    type="index",
                    interactive=self.interactive,
                    visible=self.visible,
                    elem_id=f"${name}_radio_d",
                    value=default_value,
                )
            )
        elif component_type is ComponentType.Image:
            components.image = ComponentItem(
                value=dict(
                    visible=self.visible,
                    value=self.path2image(default_value) if default_value else None,
                ),
                instance=gr.components.Image(
                    shape=kwargs.get('shape', None),
                    type='filepath' if self.interactive else 'pil',
                    label=label,
                    interactive=self.interactive,
                    visible=self.visible,
                    elem_id=f"${name}_image_d",
                    value=default_value,
                )
            )
        elif component_type is ComponentType.Label:
            components.label = ComponentItem(
                value=dict(visible=self.visible, value=None),
                instance=gr.components.Label(
                    label=label,
                    interactive=self.interactive,
                    visible=self.visible,
                    elem_id=f"${name}_label_d",
                    value=default_value,
                )
            )
        elif component_type is ComponentType.Markdown:
            components.markdown = ComponentItem(
                value=dict(visible=self.visible, value=None),
                instance=gr.components.Markdown(
                    label=label,
                    interactive=self.interactive,
                    visible=self.visible,
                    elem_id=f"${name}_markdown_d",
                    value=default_value
                )
            )
        elif component_type is ComponentType.Code:
            components.code = ComponentItem(
                value=dict(visible=self.visible, value=None),
                instance=gr.components.Code(
                    label=label,
                    interactive=self.interactive,
                    visible=self.visible,
                    elem_id=f"${name}_code_d",
                    language=kwargs.get('language'),
                    value=default_value
                )
            )
        elif component_type is ComponentType.HTML:
            components.html = ComponentItem(
                value=dict(visible=self.visible, value=None),
                instance=gr.components.HTML(
                    label=None,
                    elem_id=f"{name}_html_d",
                    value=default_value,
                    visible=self.visible,
                    interactive=True,
                )
            )
        elif component_type is ComponentType.Dropdown:
            choices_map = kwargs.get('choices_dicts', {})
            variable: ParametricVariable = kwargs.get('variable')
            components.dropdown = ComponentItem(
                value=dict(visible=self.visible, value=None),
                instance=gr.components.Dropdown(
                    choices=list(choices_map.values()),
                    label=label,
                    type="index",
                    interactive=self.interactive,
                    visible=self.visible,
                    elem_id=f"${name}_dropdown_d",
                    value=default_value
                )
            )
            components.dropdown.instance.change(
                lambda i: gr.update(value=[]) if i is None else gr.update(value=list(choices_map.keys())[i]),
                inputs=[components.dropdown.instance],
                outputs=[variable.instance]
            )

        elif component_type is ComponentType.Number:
            components.number = ComponentItem(
                value=dict(visible=self.visible, value=None),
                instance=gr.components.Number(
                    label=label,
                    interactive=self.interactive,
                    visible=self.visible,
                    elem_id=f"${name}_number_d",
                    value=default_value,
                    precision=kwargs.get('precision', 0),
                )
            )
        elif component_type is ComponentType.Table:
            components.table = ComponentItem(
                value=dict(visible=self.visible, value=None),
                instance=gr.components.Dataframe(
                    interactive=self.interactive,
                    visible=self.visible,
                    headers=kwargs.get('headers'),
                    elem_id=f"${name}_table_d",
                    value=default_value,
                )
            )
        elif component_type is ComponentType.Button:
            components.button = ComponentItem(
                value=dict(visible=self.visible),
                instance=gr.components.Button(
                    value=self.label,
                    visible=self.visible,
                    elem_id=f"${name}_button_d",
                )
            )
            components.button.instance.click(
                fn=self.map_fn,
                inputs=self.components2instances(kwargs.get('inputs')),
                outputs=self.components2instances(kwargs.get('outputs')),
                preprocess=kwargs.get('preprocess'),
                _js=kwargs.get('js', None)
            )
        elif component_type is ComponentType.Example:
            exam_title = gr.Textbox(visible=False, label=f"{label}名称")
            exam_id = gr.Textbox(visible=False, label="序号")
            examples = kwargs.get('examples')
            image_input = gr.Image(visible=False, label="缩略图")
            id_variable: ParametricVariable = kwargs.get('id_variable')
            id_maps = kwargs.get('id_maps')

            def exam_fn(idx, title, *args):
                return id_maps.get(int(idx)), title

            instance = Examples(
                label=f"{label}",
                examples_per_page=10,
                examples=examples,
                inputs=[
                    exam_id,
                    exam_title,
                    image_input
                ],
                elem_id=f"${name}_example_d",
                outputs=[
                    id_variable.instance,
                    exam_title,
                ],
                fn=exam_fn,
                # _api_mode=True,

            )
            instance = client_utils.synchronize_async(instance.create)

            components.example = ComponentItem(
                value=dict(),
                instance=instance
            )
        return components

    def parametric_change_fn(
            self,
            components: ComponentsItem,
            values: ComponentsValues,
            config: dict
    ):
        cfg = GradioCfg(config)
        cfg.update(components.radio.name, **values.radio)
        cfg.update(components.text.name, **values.text)
        cfg.update(components.image.name, **values.image)
        cfg.update(components.dropdown.name, **values.dropdown)
        cfg.update(components.markdown.name, **values.markdown)
        cfg.update(components.html.name, **values.html)
        cfg.update(components.label.name, **values.label)
        cfg.update(components.number.name, **values.number)
        cfg.update(components.table.name, **values.table)
        cfg.update(components.code.name, **values.code)
        return cfg.config


class ParametricText(BaseParametricDisplays):

    def __init__(self, name, map_fn, label=None, interactive=True, visible=True, value=None, placeholder=None):
        super(ParametricText, self).__init__(
            name, label if label else "文本", map_fn, ComponentType.TextBox,
            interactive=interactive, visible=visible, value=value, placeholder=placeholder
        )

    def bind(self, variable):
        def update_fn(value):
            return gr.update(value=value)

        self.change(update_fn, inputs=[self], outputs=[variable])


class ParametricRadio(BaseParametricDisplays):

    def __init__(self, name, map_fn, label, interactive=True, visible=True, value=None):
        super(ParametricRadio, self).__init__(
            name, label if label else "单选", map_fn, ComponentType.Radio,
            interactive=interactive, visible=visible, value=value
        )


class ParametricImage(BaseParametricDisplays):

    def __init__(self, name, map_fn, label, interactive=True, visible=True, shape=None, value=None):
        super(ParametricImage, self).__init__(
            name, label, map_fn, ComponentType.Image, interactive=interactive, visible=visible, shape=shape, value=value
        )


class ParametricLabel(BaseParametricDisplays):

    def __init__(self, name, map_fn, label, interactive=True, visible=True, value=None):
        super(ParametricLabel, self).__init__(
            name, label, map_fn, ComponentType.Label, interactive=interactive, visible=visible, value=value
        )


class ParametricMarkdown(BaseParametricDisplays):

    def __init__(self, name, value, map_fn=None, label=None, interactive=True, visible=True):
        super(ParametricMarkdown, self).__init__(
            name, label if label else "", map_fn, ComponentType.Markdown,
            interactive=interactive, visible=visible, value=value
        )


class ParametricCode(BaseParametricDisplays):

    def __init__(self, name, value, language, map_fn=None, label=None, interactive=True, visible=True):
        super(ParametricCode, self).__init__(
            name, label if label else "", map_fn, ComponentType.Code,
            interactive=interactive, visible=visible, value=value, language=language
        )


class ParametricHTML(BaseParametricDisplays):

    def __init__(self, name, value, map_fn=None, label=None, visible=True):
        super(ParametricHTML, self).__init__(
            name, label if label else "", map_fn, ComponentType.HTML, value=value, visible=visible
        )


class ParametricDropdown(BaseParametricDisplays):

    def __init__(
            self,
            name,
            map_fn,
            choices_dicts: dict,
            variable: ParametricVariable,
            label=None,
            interactive=True,
            visible=True,
            value=None
    ):
        super(ParametricDropdown, self).__init__(
            name, label if label else "", map_fn, ComponentType.Dropdown,
            interactive=interactive, visible=visible, value=value, choices_dicts=choices_dicts, variable=variable
        )


class ParametricNumber(BaseParametricDisplays):

    def __init__(self, name, map_fn, label=None, interactive=True, visible=True, value=None, precision=None):
        super(ParametricNumber, self).__init__(
            name, label if label else "", map_fn, ComponentType.Number,
            interactive=interactive, visible=visible, value=value, precision=precision
        )

    def bind(self, variable):
        def update_fn(value):
            return gr.update(value=value)

        self.change(update_fn, inputs=[self], outputs=[variable])


class ParametricButton(BaseParametricDisplays):

    def __init__(self, name, map_fn, label, inputs, outputs, preprocess=False, js=None):
        super(ParametricButton, self).__init__(
            name, label if label else "", map_fn, ComponentType.Button,
            interactive=True, visible=True, inputs=inputs, outputs=outputs, preprocess=preprocess, js=js
        )


class ParametricTable(BaseParametricDisplays):
    # 支持参数化

    def __init__(self, name, headers, value, map_fn=None):
        super(ParametricTable, self).__init__(
            name, "", map_fn, ComponentType.Table,
            interactive=False, visible=True, headers=headers, value=value
        )


class ParametricExample(BaseParametricDisplays):

    def __init__(
            self,
            name,
            label,
            examples: List[list[int, str, str]],
            id_variable: ParametricVariable,
            id_maps: Dict[int, str]
    ):
        self.examples = examples
        self.id_variable = id_variable
        self.id_maps = id_maps
        self.label = label
        super(ParametricExample, self).__init__(
            name, label, None, ComponentType.Example,
            interactive=True, visible=True, value=None, examples=examples, id_variable=id_variable, id_maps=id_maps
        )

    def example(self, idx):
        return self.instance.examples[idx]


class ParametricVariable(BaseParametricDisplays):

    def __init__(
            self,
            name,
            value,
            outputs=None,
            output_preprocess_fn=None,
    ):
        if isinstance(value, str) or isinstance(value, dict) or isinstance(value, list):
            component_type = ComponentType.TextBox
        elif isinstance(value, float) or isinstance(value, int):
            component_type = ComponentType.Number
        else:
            raise RuntimeError("组件类型异常")
        self.raw_name = name.split(":")[-1] if ':' in name else name
        super(ParametricVariable, self).__init__(
            name, "", self.variable_map_fn, component_type,
            interactive=False, visible=False, value=value, precision=None
        )
        self.outputs = outputs
        if self.outputs:
            self.bind(outputs, output_preprocess_fn)

    def hook(self, sources, target):
        inputs_names = [_.name.split(":")[-1] if ':' in _.name else _.name for _ in [self] + sources]

        def merge_params_fn(*args):
            return gr.update(value=json.dumps(dict(zip(inputs_names, args)), ensure_ascii=False))

        self.change(merge_params_fn, inputs=[self] + sources, outputs=[target])
        for source in sources:
            source.change(merge_params_fn, inputs=[self] + sources, outputs=[target])

    def variable_map_fn(self, **kwargs):
        items_cfgs = [{
            "value": kwargs.get(self.raw_name),
            "type": 'text' if self.component_type is ComponentType.TextBox else 'number',
            "item_visible": False,
        }]
        return items_cfgs

    def bind(
            self,
            outputs: List[BaseParametricDisplays],
            preprocess_fn: Callable = None
    ):
        assert outputs, '至少绑定一个输出'
        if preprocess_fn is None:
            def output_preprocess_fn(**kwargs):
                return kwargs
        else:
            output_preprocess_fn = preprocess_fn

        inputs = [self]

        def outputs_update_fn(value: str, **kwargs):
            if isinstance(self.value, list) or isinstance(self.value, dict):
                value = json.loads(value)
            kwargs.update({
                self.raw_name: value
            })
            processed_kwargs = output_preprocess_fn(**kwargs)

            update_fns = []
            for out_c in outputs:
                update_fn = out_c.update_fn(**processed_kwargs)
                if isinstance(update_fn, tuple):
                    update_fns += list(update_fn)
                else:
                    update_fns.append(update_fn)
            return update_fns[0] if len(update_fns) == 1 else tuple(update_fns)

        self.change(outputs_update_fn, inputs=inputs, outputs=outputs)
