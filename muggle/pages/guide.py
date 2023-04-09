#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import hashlib
import json
from typing import Union, List, Tuple

import gradio as gr
from gradio.routes import templates, Request
from muggle.config import cli_args
from muggle.pages.base import BaseLayout, T_Component, TaskArgs
from muggle.engine.session import project_entities
from muggle.constants import modules_enabled


class GuideFns:

    def __init__(self):
        self.base_submit = f'<button class="lg primary svelte-1ipelgc" ' \
                           f'style="width: 100%;" {{onclick}}>跳转页面</button>'
        self.base_doc_uri = f"/runtime/{cli_args.doc_tag}/docs"
        self.base_dynamic_doc_uri = "/runtime/api/{dynamic_code}/docs"

    def make_link(self, project_name, trial_days=None, token=None, quota=None, base_uri=None):
        params = [f"{k}={v}" for k, v in {
            "project_name": project_name,
            "trial_days": trial_days,
            "token": token,
            "quota": quota
        }.items() if v]
        params_text = "&".join(params)
        return f"{base_uri if base_uri else self.base_doc_uri}?{params_text}"

    def dynamic_link(self, params):
        try:
            from stardust.runtime import Runtime
            crypto = Runtime.get_class('BaseCrypto')
            dynamic_code = crypto.totp(cli_args.doc_tag.encode("utf8")) + params.get('project_name')
            dynamic_tag = hashlib.md5(dynamic_code.encode("utf8")).hexdigest()
            base_uri = self.base_dynamic_doc_uri.format(dynamic_code=dynamic_tag)
            link = self.make_link(base_uri=base_uri, **params)
        except:
            link = self.make_link(**params)
        return link

    def gen_link_fn(self, params):
        link = self.dynamic_link(params)
        items_cfgs = [{
            "value": self.base_submit.format(
                onclick=f'''onclick="window.location.href = '{link}'"'''
            ),
            "item_visible": True,
        }]
        return items_cfgs

    @classmethod
    def merge_params_fn(cls, project_name, trial_days, token, quota):
        return gr.update(value=json.dumps(dict(
            project_name=project_name, trial_days=trial_days, token=token, quota=quota
        ), ensure_ascii=False))


class GuideLayout(BaseLayout):

    def __init__(self, uri):
        self.guide_fns = GuideFns()
        super(GuideLayout, self).__init__("guide", "使用指南", uri)

    def define(self, **extra_fns) -> Union[List[T_Component], Tuple[T_Component]]:
        val_project_name = self.widgets.variable(
            name="project_name", value='',
        )
        val_params = self.widgets.variable(
            name="params", value={},
        )
        with gr.Row():
            if 'Charge' in modules_enabled:
                with gr.Column(scale=1):
                    trial_days = self.widgets.number(
                        "trial_days", label="时效 (天)", value=1, precision=0
                    )
                with gr.Column(scale=1):
                    quota = self.widgets.number(
                        "quota", label="额度 (次数)", value=100, precision=0
                    )
                with gr.Column(scale=1):
                    token = self.widgets.text(
                        "token", label="Token", placeholder="Token (可空)"
                    )

        with gr.Row():
            self.widgets.dropdown(
                name="guide_projects",
                label="模型列表",
                map_fn=None,
                choices_dicts={k: v.title for k, v in project_entities.all.items()},
                interactive=True,
                variable=val_project_name,
            )
        html = self.widgets.html(
            "html",
            value=self.guide_fns.base_submit.format(onclick=""),
            map_fn=self.guide_fns.gen_link_fn,
        )
        if 'Charge' in modules_enabled:
            val_project_name.hook(sources=[trial_days, token, quota], target=val_params)
        else:
            val_project_name.hook(sources=[], target=val_params)
        val_params.bind(outputs=[html])
        return []

    def external_params_process(self, *external_params) -> dict:
        pass
