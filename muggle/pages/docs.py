#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import hashlib
import gradio as gr
from typing import Union, List, Tuple
from muggle.config import cli_args
from muggle.pages.base import BaseLayout, T_Component, TaskArgs
from muggle.pages.demo.http import (
    java_prefix_code, java_define_param_code, java_req_body_code, java_suffix_code,
    python_demo_code, e_prefix_code, e_exec_code, e_suffix_code, csharp_demo_code
)
from muggle.engine.session import project_entities
from muggle.constants import modules_enabled
from muggle.utils import Import
from fastapi import Response


class Demo:

    @classmethod
    def java(cls, host, project_name, params, token="", sign=""):
        blank = '        '
        json_title = blank + 'data.put("title", {title_var});\n'
        base_im_d = blank + 'String {title_name} = Base64.getEncoder().encodeToString(toByteArray("image_{idx}.jpg"));'
        sign_code = blank + 'data.put("sign", MD5Utils.stringToMD5(imageParam.substring(0, 100)+"SECRET_KEY"));\n' if sign else ""
        token_code = blank + f'data.put("token", "{token}");\n' if token else ""
        for param in params:
            if param['type'] == 'text':
                json_title = json_title.format(title_var='"限定文本"')
            elif param['type'] == 'image':
                im_define = base_im_d.format(title_name='titleImageParam', idx=0)
                json_title = im_define + "\n" + json_title.format(title_var='titleImageParam')
            elif param['type'] == 'images':
                base_array = blank + f"JSONArray title = new JSONArray();\n"
                array_add_code = blank + blank.join([
                    f'title.add(titleImage{i}Param);\n' for i in range(len(param['value']))
                ])
                im_define = "\n".join([
                    base_im_d.format(title_name=f'titleImageParam_{i}', idx=i)
                    for i in range(len(param['value']))
                ]) + "\n"
                json_title = base_array + im_define + array_add_code + json_title.format(title_var='title')
            elif param['type'] == 'radio':
                options = list(param['value'].keys())
                json_title = json_title.format(title_var=f"\"限定选项: {' / '.join(options)}\"")
            break
        return java_prefix_code + java_define_param_code.format(
            project_name=project_name, params_code=sign_code + token_code + (json_title if params else "")
        ) + java_req_body_code.format(host=host) + java_suffix_code

    @classmethod
    def python(cls, host, project_name, params, token="", sign=""):
        base_im_d = 'title_{idx} = base64.b64encode(open(r"title_{idx}.png", "rb").read()).decode()'
        json_title = '    "title": {title_var},\n'
        sign_code = '    "sign": hashlib.md5(main_b64[:100]+"SECRET_KEY").hexdigest(),\n' if sign else ""
        token_code = f'    "token": "{token}",\n' if token else ""
        im_define = ""

        for param in params:
            if param['type'] == 'text':
                json_title = json_title.format(title_var='"限定文本"')
            elif param['type'] == 'image':
                im_define = base_im_d.format(idx=0) + "\n"
                json_title = json_title.format(title_var='title_0')
            elif param['type'] == 'images':
                im_define = "\n".join([
                    base_im_d.format(idx=i)
                    for i in range(len(param['value']))
                ]) + "\n"
                array_add_code = '[' + ', '.join([
                    f'title_{i}' for i in range(len(param['value']))
                ]) + ']'
                json_title = json_title.format(title_var=array_add_code)
            elif param['type'] == 'radio':
                options = list(param['value'].keys())
                json_title = json_title.format(title_var=f"\"限定选项: {' / '.join(options)}\"")
            break

        return python_demo_code.format(
            host=host, define_code=im_define, project_name=project_name,
            params_code=sign_code + token_code + (json_title if params else "")
        )

    @classmethod
    def csharp(cls, host, project_name, params, token="", sign=""):
        base_im_d = 'var title{idx}Base64 = Convert.ToBase64String(File.ReadAllBytes("title_{idx}.png"));'
        json_title = '    title = {title_var},\n'
        sign_code = '    sign = GetMD5Hash(imageBase64.Substring(0, 100) + "SECRET_KEY")\n' if sign else ""
        token_code = f'    token = "{token}",\n' if token else ""
        im_define = ""

        for param in params:
            if param['type'] == 'text':
                json_title = json_title.format(title_var='"限定文本"')
            elif param['type'] == 'image':
                im_define = base_im_d.format(idx=0) + "\n"
                json_title = json_title.format(title_var='title0Base64')
            elif param['type'] == 'images':
                im_define = "\n".join([
                    base_im_d.format(idx=i)
                    for i in range(len(param['value']))
                ]) + "\n"
                array_add_code = 'new string[] {' + ', '.join([
                    f'title{i}Base64' for i in range(len(param['value']))
                ]) + '}'
                json_title = json_title.format(title_var=array_add_code)
            elif param['type'] == 'radio':
                options = list(param['value'].keys())
                json_title = json_title.format(title_var=f"\"限定选项: {' / '.join(options)}\"")
            break

        return csharp_demo_code.format(
            host=host, define_code=im_define, project_name=project_name,
            params_code=sign_code + token_code + (json_title if params else "")
        )

    @classmethod
    def e(cls, host, project_name, params, token="", sign=""):
        base_json_title = 'json.置属性 (“title”, {title_var}, )'
        base_im_d = '加入成员 (title, 读入文件 (“title_{idx}.png”))'
        sign_code = "json.置属性 (“sign”, 取数据摘要 (到字节集 (取文本左边 (image, 100) ＋ “SECRET_KEY”)), )\n" if sign else ""
        token_code = f"json.置属性 (“token”, “{token}”, )\n" if token else ""
        # impl_code = ''
        im_define = ''
        exec_code = e_exec_code.format(title_code='')
        suffix_code = e_suffix_code.format(
            exec_code='',
            project_name=project_name,
            impl_code='',
            host=host
        )
        for param in params:
            if param['type'] == 'text':
                im_define = ''
                json_title = base_json_title.format(title_var='“限定文本”')
                exec_code = e_exec_code.format(title_code='')
                impl_code = sign_code + token_code + json_title
                suffix_code = e_suffix_code.format(
                    exec_code='',
                    project_name=project_name,
                    impl_code=impl_code,
                    host=host
                )
            elif param['type'] == 'image':
                im_define = base_im_d.format(idx=0) + "\n"
                json_title = base_json_title.format(title_var='编码_BASE64编码 (标题 [1])')
                exec_code = e_exec_code.format(title_code=', title')
                impl_code = sign_code + token_code + json_title
                suffix_code = e_suffix_code.format(
                    exec_code='.参数 标题, 字节集, 数组',
                    project_name=project_name,
                    impl_code=impl_code,
                    host=host
                )
            elif param['type'] == 'images':
                im_define = "\n".join([
                    base_im_d.format(idx=i)
                    for i in range(len(param['value']))
                ]) + "\n"
                exec_code = e_exec_code.format(title_code=', title')
                impl_code = '.计次循环首 (取数组成员数 (标题), i)\n' \
                            '    json.加成员 (编码_BASE64编码 (标题 [i]), “title”, , )\n' \
                            '.计次循环尾 ()\n'
                impl_code = sign_code + token_code + impl_code
                suffix_code = e_suffix_code.format(
                    exec_code='.参数 标题, 字节集, 数组',
                    project_name=project_name,
                    impl_code=impl_code,
                    host=host
                )
            elif param['type'] == 'radio':
                options = list(param['value'].keys())
                json_title = base_json_title.format(title_var=f"“限定选项: {' / '.join(options)}”")
                exec_code = e_exec_code.format(title_code='')
                impl_code = sign_code + token_code + json_title
                suffix_code = e_suffix_code.format(
                    exec_code='',
                    project_name=project_name,
                    impl_code=impl_code,
                    host=host
                )
            break
        return e_prefix_code + im_define + exec_code + suffix_code


class WebVision:

    @classmethod
    def doc_params_map_fn(cls, project_name, trial_days=None, token=None, quota=None, **kwargs):
        project_config = project_entities.get(project_name)
        items_cfgs = project_config.titles
        base_param = [
            [
                'project_name',
                'Yes',
                "String",
                f'项目名: {project_name}',
            ],
            [
                'image',
                'Yes',
                "String",
                '主图: Base64 编码',
            ],
        ]
        ext_param: list[str] = []
        for items_cfg in items_cfgs:
            if items_cfg['type'] == 'text':
                if not ext_param:
                    ext_param = [
                        'title',
                        'No' if len(items_cfgs) > 1 else 'Yes',
                        'String',
                        "限定文本",
                    ]
                else:
                    ext_param = [
                        'title',
                        'Yes',
                        ext_param[2] + ' | String',
                        ext_param[3] + " | 限定文本",
                    ]
            elif items_cfg['type'] == 'images':
                if not ext_param:
                    ext_param = [
                        'title',
                        'No' if len(items_cfgs) > 1 else 'Yes',
                        'List[String]',
                        "限定副图组: Base64 编码 数组",
                    ]
                else:
                    ext_param = [
                        'title',
                        'Yes',
                        ext_param[2] + ' | List[String]',
                        ext_param[3] + " | 限定副图组: Base64 编码 数组",
                    ]
            elif items_cfg['type'] == 'image':
                if not ext_param:
                    ext_param = [
                        'title',
                        'No' if len(items_cfgs) > 1 else 'Yes',
                        'String',
                        "限定副图: Base64 编码",
                    ]
                else:
                    ext_param = [
                        'title',
                        'Yes',
                        ext_param[2] + ' | String',
                        ext_param[3] + " | 限定副图: Base64 编码",
                    ]
            elif items_cfg['type'] == 'radio':
                options = list(items_cfg['value'].keys())
                if not ext_param:
                    ext_param = [
                        'title',
                        'No' if len(items_cfgs) > 1 else 'Yes',
                        'String',
                        f"限定选项: {' / '.join(options)}",
                    ]
                else:
                    ext_param = [
                        'title',
                        'Yes',
                        ext_param[2] + ' | String',
                        ext_param[3] + f" | 限定选项: {' / '.join(options)}",
                    ]
        if ext_param:
            base_param.append(ext_param)
        if 'Sign' in modules_enabled:
            base_param.append([
                'sign',
                'Yes',
                "String",
                f'MD5(主图 Base64 编码前100位 + SECRET_KEY)',
            ])
        if token:
            base_param.append([
                'token',
                'Yes',
                "String",
                f'调用授权 Token: {token}',
            ])
        items_cfgs = [{
            "item_type": "table",
            "value": base_param
        }]
        return items_cfgs


class DocumentLayout(BaseLayout):

    def __init__(self, uri):
        super(DocumentLayout, self).__init__("docs", "调用文档", uri)
        self.secret_key = cli_args.secret_key if 'Sign' in modules_enabled else ""
        self.task_pool.before.append(self.before_verification)
        if 'Charge' in modules_enabled:
            self.task_pool.after.append(self.setting_token)

    @classmethod
    def before_verification(cls, args: TaskArgs):
        try:
            from stardust.runtime import Runtime
            crypto = Runtime.get_class('BaseCrypto')
            dynamic_token = args.params.get('dynamic_token')
            dynamic_tag = hashlib.md5(crypto.totp(cli_args.doc_tag.encode("utf8")).encode("utf8")).hexdigest()
            if dynamic_token != dynamic_tag:
                return Response(status_code=404)
        except:
            return None

    @classmethod
    def setting_token(cls, args: TaskArgs):
        token = args.params.get('token')
        if not token:
            return
        quota = args.params.get('quota')
        project_name = args.params.get('project_name')
        trial_days = args.params.get('trial_days')
        info_cls = Import.get_class("Charge")
        info = info_cls.add(
            token_id=token, quota=int(quota), project_name=project_name, days=trial_days
        )
        all_info = info_cls.all_info()

    def doc_java_demo_map_fn(self, project_name, trial_days=None, token=None, quota=None, **kwargs):
        project_config = project_entities.get(project_name)
        items_cfgs = project_config.titles

        java_code = Demo.java(
            self.req_params.host, project_name=project_name, params=items_cfgs, token=token, sign=self.secret_key
        )

        items_cfgs = [{
            "value": f'```\n{java_code}\n```'
        }]
        return items_cfgs

    def doc_python_demo_map_fn(self, project_name, trial_days=None, token=None, quota=None, **kwargs):
        project_config = project_entities.get(project_name)
        items_cfgs = project_config.titles

        python_code = Demo.python(
            self.req_params.host, project_name=project_name, params=items_cfgs, token=token, sign=self.secret_key
        )

        items_cfgs = [{
            "value": f'```\n{python_code}\n```'
        }]
        return items_cfgs

    def doc_csharp_demo_map_fn(self, project_name, trial_days=None, token=None, quota=None, **kwargs):
        project_config = project_entities.get(project_name)
        items_cfgs = project_config.titles

        csharp_code = Demo.csharp(
            self.req_params.host, project_name=project_name, params=items_cfgs, token=token, sign=self.secret_key
        )

        items_cfgs = [{
            "value": f'```\n{csharp_code}\n```'
        }]
        return items_cfgs

    def doc_e_demo_map_fn(self, project_name, trial_days=None, token=None, quota=None, **kwargs):
        project_config = project_entities.get(project_name)
        items_cfgs = project_config.titles

        e_code = Demo.e(
            self.req_params.host, project_name=project_name, params=items_cfgs, token=token, sign=self.secret_key
        )

        items_cfgs = [{
            "value": f'```\n{e_code}\n```'
        }]
        return items_cfgs

    def define(self, **extra_fns) -> Union[List[T_Component], Tuple[T_Component]]:
        val_project_name = self.widgets.variable(
            name="project_name", value="",
        )
        self.widgets.markdown(name="title", value="# 生产接口")
        self.widgets.table(
            name="form_uri",
            headers=['请求地址', 'Content-Type', '参数形式', '请求方法'],
            value=[
                [
                    f'http://$host/runtime/text/invoke',
                    'application/json',
                    "JSON",
                    'POST',
                ]
            ]
        )
        self.widgets.markdown(name="param_title", value="**具体参数：**")
        form_params = self.widgets.table(
            name="form_params",
            map_fn=WebVision.doc_params_map_fn,
            headers=['参数名', '必填', '类型', '说明/默认值'],
            value=[
                [
                    'project_name',
                    'Yes',
                    "String",
                    '项目名',
                ],
                [
                    'image',
                    'Yes',
                    "String",
                    '主图: Base64 编码',
                ],
            ]
        )
        self.widgets.markdown(
            name="response",
            value='请求为JSON格式，形如：\n```{"image": "Base64 编码后的图像二进制流", "project_name": "项目名", ......}```'
        )
        self.widgets.markdown(name="return_title", value="**返回结果：**")

        param_list = [
            ['uuid', 'String', "返回唯一编号"],
            ['msg', 'String', "错误消息"],
            ['data', 'String', "返回数据信息"],
            ['score', 'Float', "置信度"],
            ['consume', 'Float', "耗时"],
            ['code', 'Integer', "状态码"],
            ['success', 'Boolean', "是否请求成功"],
        ]
        if 'Charge' in modules_enabled:
            param_list.append(['remain', 'Integer', "剩余额度"])

        self.widgets.table(
            name="response_param",
            headers=['参数名', '类型', '说明'],
            value=param_list
        )
        self.widgets.markdown(
            name="response_demo",
            value='该返回为JSON格式，形如：\n'
                  '```{"uuid": "92d2c0f752724b0fa43ce186b18b6172", "msg": "", "data": "识别内容", "code": 0,'
                  ' "success": true, "consume": 10.1033878326416, "score":1.0}```'
        )

        with gr.Accordion("Java 用例", open=False):
            default_java_demo = Demo.java(
                host="$host",
                project_name="项目名",
                params=[{'name': '文本标题', 'type': 'text', 'value': '请输入限定文本（必填）'}]
            )
            demo_java = self.widgets.markdown(
                name="java_code",
                map_fn=self.doc_java_demo_map_fn,
                value=f'```\n{default_java_demo}\n```'
            )

        with gr.Accordion("Python 用例", open=False):
            default_python_demo = Demo.python(
                host="$host",
                project_name="项目名",
                params=[{'name': '文本标题', 'type': 'text', 'value': '请输入限定文本（必填）'}]
            )
            demo_python = self.widgets.markdown(
                name="python_code",
                map_fn=self.doc_python_demo_map_fn,
                value=f'```\n{default_python_demo}\n```'
            )

        with gr.Accordion("CSharp 用例", open=False):
            default_csharp_demo = Demo.csharp(
                host="$host",
                project_name="项目名",
                params=[{'name': '文本标题', 'type': 'text', 'value': '请输入限定文本（必填）'}]
            )
            demo_csharp = self.widgets.markdown(
                name="csharp_code",
                map_fn=self.doc_csharp_demo_map_fn,
                value=f'```\n{default_csharp_demo}\n```'
            )

        with gr.Accordion("易语言 用例", open=False):
            default_e_demo = Demo.e(
                host="$host",
                project_name="项目名",
                params=[{'name': '文本标题', 'type': 'text', 'value': '请输入限定文本（必填）'}]
            )
            demo_e = self.widgets.markdown(
                name="e_code",
                map_fn=self.doc_e_demo_map_fn,
                value=f'```\n{default_e_demo}\n```'
            )

        val_project_name.bind([form_params])
        return [demo_java, demo_python, demo_csharp, demo_e, form_params]

    def external_params_process(self, *external_params) -> dict:
        pass
