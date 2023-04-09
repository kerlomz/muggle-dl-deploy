#!/usr/bin/env python3
# -*- coding:utf-8 -*-
from __future__ import annotations
import base64
import shutil
import gradio as gr
from gradio.blocks import Context
from collections import namedtuple
from abc import abstractmethod
from dataclasses import dataclass, field
from gradio.routes import templates
from fastapi import Request, Response
from typing import Dict, Callable, List, Union, TypeVar, Tuple, NoReturn
from muggle.pages.components.inputs import ParametricInputs, ComponentType, ParametricInputTitle, ParametricInputImage
from muggle.pages.components.displays import BaseParametricDisplays, GradioCfg
from muggle.pages.components.displays import (
    ParametricText, ParametricLabel, ParametricImage,
    ParametricMarkdown, ParametricDropdown, ParametricNumber,
    ParametricVariable, ParametricExample, ParametricButton, ParametricTable, ParametricHTML, ParametricCode
)

T_Component = TypeVar('T_Component', bound=Union[ParametricInputs, BaseParametricDisplays])


class BaseLayoutValsEntity:

    def __init__(self, project_config: dict):
        self.project_config = project_config

    @classmethod
    def path2image(cls, im_path):
        ext = im_path.split(".")[-1]
        return f'data:image/{ext};base64,{base64.b64encode(open(im_path, "rb").read()).decode()}'


class Widgets:

    def __init__(self, name):
        self.name = name
        self.elem_name = f"{name}:{{name}}"
        self.attr = namedtuple('Attr', ['object', 'variable'])

    def text(
            self, name,
            map_fn=None, label=None, interactive=True, visible=True, value=None, placeholder=None, to_variable=False
    ):
        text = ParametricText(
            self.elem_name.format(name=name),
            map_fn, label=label, interactive=interactive, visible=visible, value=value, placeholder=placeholder
        )
        if to_variable:
            variable = self.variable(name=self.name, value="" if value is None else value)
            text.bind(variable)
            return self.attr(object=text, variable=variable)
        return text

    def number(
            self, name,
            map_fn=None, label=None, interactive=True, visible=True, value=None, precision=None, to_variable=False
    ):
        number = ParametricNumber(
            self.elem_name.format(name=name),
            map_fn, label=label,
            interactive=interactive, visible=visible, value=value, precision=precision
        )
        if to_variable:
            variable = self.variable(name=self.name, value=-1 if value is None else value)
            number.bind(variable)
            return self.attr(object=number, variable=variable)
        return number

    def label(self, name, map_fn, label, interactive=True, visible=True, value=None):
        return ParametricLabel(
            self.elem_name.format(name=name),
            map_fn, label=label, interactive=interactive, visible=visible, value=value
        )

    def image(self, name, map_fn, label, interactive=True, visible=True, shape=None, value=None):
        return ParametricImage(
            self.elem_name.format(name=name),
            map_fn, label=label, interactive=interactive, visible=visible, shape=shape, value=value
        )

    def markdown(self, name, value, map_fn=None, label=None, interactive=True, visible=True):
        return ParametricMarkdown(
            self.elem_name.format(name=name),
            value, map_fn=map_fn, label=label, interactive=interactive, visible=visible
        )

    def code(self, name, value, language=None, map_fn=None, label=None, interactive=False, visible=True):
        return ParametricCode(
            self.elem_name.format(name=name),
            value, map_fn=map_fn, label=label, interactive=interactive, visible=visible, language=language
        )

    def html(self, name, value, map_fn=None):
        return ParametricHTML(
            self.elem_name.format(name=name), value, map_fn=map_fn
        )

    def dropdown(
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
        return ParametricDropdown(
            self.elem_name.format(name=name),
            map_fn, label=label,
            interactive=interactive, visible=visible, value=value, choices_dicts=choices_dicts, variable=variable
        )

    def variable(
            self,
            name,
            value,
            outputs=None,
            output_preprocess_fn=None
    ):
        return ParametricVariable(
            self.elem_name.format(name=name),
            value=value, outputs=outputs,
            output_preprocess_fn=output_preprocess_fn
        )

    def example(
            self,
            name,
            label,
            examples: List[list[int, str, str]],
            id_variable: ParametricVariable,
            id_maps: Dict[int, str]
    ):
        return ParametricExample(
            self.elem_name.format(name=name),
            label=label,
            examples=examples,
            id_variable=id_variable,
            id_maps=id_maps
        )

    def button(self, name, map_fn, label, inputs, outputs, preprocess=False, js=None):
        return ParametricButton(
            self.elem_name.format(name=name),
            map_fn=map_fn,
            label=label,
            inputs=inputs,
            outputs=outputs,
            preprocess=preprocess,
            js=js
        )

    def inputs(self, name, component_type: ComponentType, map_fn: Callable):
        return ParametricInputs(
            self.elem_name.format(name=name),
            component_type=component_type,
            map_fn=map_fn,
        )

    def input_title(self, name, map_fn: Callable):
        return ParametricInputTitle(
            self.elem_name.format(name=name),
            map_fn=map_fn,
        )

    def input_image(self, name, map_fn: Callable, label=None):
        return ParametricInputImage(
            self.elem_name.format(name=name),
            map_fn=map_fn,
            label=label
        )

    def table(self, name, headers, value, map_fn=None):
        return ParametricTable(self.elem_name.format(name=name), headers, value, map_fn=map_fn)


class PageTaskManager:

    def __init__(self):
        self.before: List[Callable[[TaskArgs], Union[dict, Response]]] = []
        self.after: List[Callable[[TaskArgs], NoReturn]] = []


class TaskArgs:

    def __init__(self, config: dict, req: Request, params: dict):
        # self.cfg: GradioCfg = GradioCfg(config)
        self.config: dict = config
        self.req: Request = req
        self.params: dict = params

    @property
    def cfg(self) -> GradioCfg:
        return GradioCfg(self.config)


class BaseLayout:

    @dataclass
    class RequestParams:
        remote_ip: str = '$remote_ip'
        host: str = '$host'

    def __init__(self, name: str, title: str, uri, **extra_fns):
        self.name: str = name
        self.uri: str = uri
        self.title = title
        self.widgets = Widgets(name)
        self.elem_name = f"{name}:{{name}}"
        self.extra_fns = extra_fns
        self.req_params = BaseLayout.RequestParams()
        self.task_pool = PageTaskManager()
        self.blocks = self.base_blocks(title)
        with self.blocks:
            self.components: List[T_Component] = list(self.define(**extra_fns))

    def reset(self):
        Context.id = 0
        self.blocks = self.base_blocks(self.title)
        with self.blocks:
            self.components: List[T_Component] = list(self.define(**self.extra_fns))

    @classmethod
    def sys_parametric_fn(cls, config, request: Request):
        cfg = GradioCfg(config)
        cfg.replace("$remote_ip", request.client.host)
        cfg.replace("$host", request.headers['Host'])
        return cfg.config

    def render_fn(self, interface):

        async def render(request: Request):
            template = (
                "frontend/index.html"
            )
            config = interface.get_config(self.name)
            params = dict(**dict(request.query_params.items()), **request.path_params)

            task_args = TaskArgs(config, request, params)

            for before_task in self.task_pool.before:
                task_resp = before_task(task_args)
                if isinstance(task_resp, dict):
                    task_args.config = before_task(task_args)
                elif isinstance(task_resp, Response):
                    return task_resp

            if params:
                for component in self.components:
                    task_args.config = component.parametric_fn(task_args.config, **params)

            task_args.config = self.sys_parametric_fn(task_args.config, request)

            for after_task in self.task_pool.after:
                after_task(task_args)

            return templates.TemplateResponse(
                template, {"request": request, "config": task_args.config}
            )

        return render

    @abstractmethod
    def define(self, **extra_fns) -> Union[List[T_Component], Tuple[T_Component]]:
        ...

    @abstractmethod
    def external_params_process(self, *external_params) -> dict:
        ...

    def base_blocks(self, layout_title: str):
        Context.id = 0
        base_blocks = gr.Blocks(title=layout_title, mode="blocks", elem_id=self.elem_name.format(name="base_blocks"))
        # base_blocks.blocks = {}
        # base_blocks.fns = []
        # base_blocks.dependencies = []
        # base_blocks.children = []
        # print(base_blocks.blocks, base_blocks.fns, base_blocks.dependencies, base_blocks.children)
        base_blocks.dev_mode = False
        base_blocks.show_error = True
        return base_blocks

    @property
    def app(self):
        return self.blocks.app

    @property
    def config(self):
        return self.blocks.config
