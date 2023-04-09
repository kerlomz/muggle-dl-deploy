#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import shutil
import gradio as gr
from functools import partial
from muggle.pages.base import BaseLayout, TaskArgs
from muggle.engine.session import project_entities
from muggle.config import STARTUP_PARAM

# project_entities = ProjectEntities()


class WebVision:

    @classmethod
    def input_image_map_fn(cls, project_name):
        project_config = project_entities.get(project_name)
        default_ims = project_config.input_images
        items_cfgs = [{
            "value": default_ims[0] if default_ims else None
        }]
        return items_cfgs

    @classmethod
    def input_title_map_fn(cls, project_name):
        project_config = project_entities.get(project_name)
        items_cfgs = project_config.titles
        return items_cfgs

    @classmethod
    def val_project_title_map_fn(cls, project_name):
        project_config = project_entities.get(project_name)
        items_cfgs = [{
            "value": project_config.title,
        }]
        return items_cfgs

    @classmethod
    def web_title_map_fn(cls, project_name):
        project_config = project_entities.get(project_name)
        items_cfgs = [{
            "value": f"# <center>{project_config.title} 验证码测试页面",
        }]
        return items_cfgs

    @classmethod
    def web_desc_map_fn(cls, project_name):
        project_config = project_entities.get(project_name)
        if 'preview_prompt' in project_config.cfg:
            preview_prompt = project_config.cfg.get('preview_prompt')
        else:
            preview_prompt = STARTUP_PARAM.get('preview_prompt')
        items_cfgs = [{
            "value": f"{preview_prompt}<br />"
        }]
        return items_cfgs

    @classmethod
    def image_predict_title_map_fn(cls, project_name):
        project_config = project_entities.get(project_name)
        items_cfgs = [{
            "value": None,
            "item_visible": True if project_config.cfg.get('outputs', 'image') == 'image' else False,
        }]
        return items_cfgs

    @classmethod
    def label_predict_title_map_fn(cls, project_name):
        project_config = project_entities.get(project_name)
        items_cfgs = [{
            "value": None,
            "item_visible": True if project_config.cfg.get('outputs') == 'text' else False
        }]
        return items_cfgs

    @classmethod
    def project_dropdown_map_fn(cls, project_name):
        project_config = project_entities.get(project_name)
        items_cfgs = [{
            "value": project_config.title,
        }]
        return items_cfgs


class PreviewLayout(BaseLayout):

    def __init__(self, preview_fn, uri):
        super(PreviewLayout, self).__init__(
            "preview", "验证码识别测试页面", uri, preview_fn=preview_fn
        )

    def define(self, **extra_fns):
        remote_ip = self.widgets.text(name="host", visible=False, value="$remote_ip")
        val_project_name = self.widgets.variable(
            name="project_name",
            value="",
        )
        web_title = self.widgets.markdown(
            name="web_title",
            map_fn=WebVision.web_title_map_fn, value="# 请先选择项目", interactive=True
        )
        web_desc = self.widgets.markdown(
            name="web_desc",
            map_fn=WebVision.web_desc_map_fn, value="", interactive=True
        )
        with gr.Row():
            with gr.Column(scale=3):
                search_edit = self.widgets.text(
                    name=self.elem_name.format(name="search_edit"), label="模型搜索", map_fn='empty'
                )

            with gr.Column(scale=7):
                project_dropdown = self.widgets.dropdown(
                    name="project_dropdown",
                    label="模型列表",
                    map_fn=WebVision.project_dropdown_map_fn,
                    choices_dicts={k: v.title for k, v in project_entities.all.items()},
                    interactive=True,
                    variable=val_project_name
                )

                search_edit.change(
                    fn=self.find_projects, inputs=[search_edit], outputs=[project_dropdown]
                )

        with gr.Row():
            with gr.Column(scale=4):
                input_image = self.widgets.input_image(
                    name="input",
                    label="图片",
                    map_fn=WebVision.input_image_map_fn
                )
                input_titles = self.widgets.input_title(name="title", map_fn=WebVision.input_title_map_fn)

                text_predict_label = self.widgets.label(
                    name="text_predict_label",
                    label="(文本)预测结果",
                    map_fn=WebVision.label_predict_title_map_fn,
                    visible=False, interactive=False,
                )
                image_predict_label = self.widgets.image(
                    name="image_predict_label",
                    shape=(256, 256),
                    label="(图像)预测结果",
                    map_fn=WebVision.image_predict_title_map_fn,
                    visible=False, interactive=False,
                )

                input_sets = [
                    remote_ip,
                    val_project_name,
                    input_image,
                    input_titles
                ]
                predict_labels = [
                    text_predict_label,
                    image_predict_label
                ]
                self.widgets.button(
                    name="predict", label="预测",
                    map_fn=self.extra_fns['preview_fn'], inputs=input_sets, outputs=predict_labels,
                )

            with gr.Column(scale=1):
                with gr.Accordion("模型列表", open=True):
                    self.widgets.example(
                        name="model_example",
                        label="模型",
                        examples=[
                            [i, v.title, ims[0] if (ims := v.input_images) else None]
                            for i, (k, v) in enumerate(project_entities.all.items())
                        ],
                        id_maps=project_entities.ids_maps,
                        id_variable=val_project_name
                    )

                    project_outputs = [
                        web_title,
                        web_desc,
                        project_dropdown,
                        search_edit,
                        input_image,
                        text_predict_label,
                        image_predict_label,
                        input_titles
                    ]
                    val_project_name.bind(project_outputs)
        return [
            input_titles,
            input_image,
            web_title,
            web_desc,
            val_project_name,
            text_predict_label,
            image_predict_label,
            project_dropdown
        ]

    def external_params_process(self, *external_params) -> dict:
        return {}

    @property
    def app(self):
        return self.blocks.app

    @property
    def config(self):
        return self.blocks.config

    @classmethod
    def find_projects(cls, name):
        if not name:
            return gr.update(choices=project_entities.titles)
        return gr.update(choices=[title for title in project_entities.titles if name in title])