#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import copy
import json
import shutil
import starlette.routing
import gradio as gr
from gradio import Blocks
from gradio.context import Context
from typing import Dict, List
from gradio.routes import App


class GradioCfg:

    def __init__(self, config: dict):
        self.config: dict = copy.deepcopy(config)

    def replace(self, source, target, elem_name='value'):
        for component in self.config['components']:
            value = component['props'].get(elem_name)
            if isinstance(value, str) and "$" in value:
                component['props'][elem_name] = value.replace(source, target)
            elif isinstance(value, dict) or isinstance(value, list):
                component['props'][elem_name] = json.loads(json.dumps(value, ensure_ascii=False).replace(source, target))

    def update(self, elem_id: str, **kwargs):
        if not kwargs:
            return
        for component in self.config['components']:
            if component['props'].get('elem_id') == elem_id:
                for k, v in kwargs.items():
                    component['props'][k] = v


class BlocksEntities:

    def __init__(self):
        self.routes_dicts: Dict[str, List[str]] = {}
        self.layout_dicts: Dict[str, dict] = {}
        self.blocks_dicts: Dict[str, dict] = {}
        self.dependencies_dicts: Dict[str, list] = {}
        self.components_dicts: Dict[str, list] = {}
        self.fns_dicts: Dict[str, list] = {}

    @classmethod
    def empty_blocks(cls):
        with (blocks := gr.Blocks(title="Empty")):
            gr.HTML("")
        return blocks


class BlocksFuse:

    def __init__(self, **layouts):
        self.layouts_maps = layouts
        self.title_maps = {}
        self.map = BlocksEntities()
        self.blocks = self.merge()
        self.resource_paths = [
            '/static/{path:path}',
            '/assets/{path:path}',
            '/file={path:path}',
            '/file/{path:path}',
            '/run/{api_name}',
            '/run/{api_name}/',
            '/api/{api_name}',
            '/api/{api_name}/',
        ]
        self.resource_route = [
            (r.path, r.endpoint, r.methods) for r in self.blocks.app.routes if r.path in self.resource_paths
        ]
        self.setting_routes()
        self.shield_sys_docs()

    @property
    def blocks_maps(self):
        return {k: v.blocks for k, v in self.layouts_maps.items()}

    @property
    def config_maps(self):
        return self.fuse_config(self.blocks.config)

    @classmethod
    def clear_cache(cls):
        try:
            shutil.rmtree(gr.examples.CACHED_FOLDER)
        except :
            pass

    def reset_layouts(self):
        self.clear_cache()
        for name, layout in self.layouts_maps.items():
            layout.reset()
        self.map = BlocksEntities()
        blocks = self.merge()
        self.app.configure_app(blocks)
        self.blocks = blocks
        self.setting_routes()

    def get_config(self, name):
        config = self.config_maps.get(name).copy()
        config['title'] = self.title_maps.get(name)
        return config

    # def resetting_layout_routes(self):
    #     for name, layout in self.layouts_maps.items():
    #         del_routes = [route for i, route in enumerate(self.app.routes) if route.path == layout.uri]
    #         for route in del_routes:
    #             print(f'删除布局路由 {route.path}, {route.endpoint}, {route}')
    #             self.app.routes.remove(route)
    #         print(f'重建布局路由 {f"{layout.uri}"}')
    #         self.app.add_api_route(layout.uri, layout.render_fn(self), methods=['GET'])
    #
    # def resetting_resource_routes(self):
    #     uri_rels = set()
    #     for name, layout in self.layouts_maps.items():
    #         uri_rels.add("/".join(layout.uri.split("/")[:-1]))
    #     for uri in uri_rels:
    #         for r in self.resource_route:
    #             del_routes = [route for i, route in enumerate(self.app.routes) if route.path == f"{uri}{r[0]}"]
    #             for route in del_routes:
    #                 print(f'删除资源路由 {route.path}, {route.endpoint}, {route}')
    #                 self.app.routes.remove(route)
    #             print(f'重建资源路由 {f"{uri}{r[0]}"}')
    #             self.app.add_api_route(f"{uri}{r[0]}", r[1], methods=r[2])
    def shield_sys_docs(self):
        del_routes = [route for i, route in enumerate(self.app.routes) if route.path == "/docs"]
        for route in del_routes:
            # print(f'屏蔽自带路由 {route.path}, {route.endpoint}, {route}')
            self.app.routes.remove(route)

    def setting_routes(self):
        uri_rels = set()
        for name, layout in self.layouts_maps.items():
            uri_rels.add("/".join(layout.uri.split("/")[:-1]))
            self.app.add_api_route(layout.uri, layout.render_fn(self), methods=['GET'])
        for uri in uri_rels:
            for r in self.resource_route:
                self.app.add_api_route(f"{uri}{r[0]}", r[1], methods=r[2])

    @property
    def app(self):
        return self.blocks.app

    def fuse_config(self, base_config: dict):
        config_maps: dict = {}
        for name, layout in self.map.layout_dicts.items():
            config = copy.deepcopy(base_config)
            config['layout'] = layout
            config_maps[name] = config
        return config_maps

    @classmethod
    def iter_child(cls, start_index, child: dict):
        if isinstance(child, list):
            return [cls.iter_child(start_index, c) for c in child]
        elif isinstance(child, dict):
            child_dict = child.copy()
            child_dict['id'] += start_index
            if 'children' in child_dict:
                child_dict['children'] = cls.iter_child(start_index, child_dict['children']) if child_dict['children'] else []
            return child_dict

    def merge(self):
        base_blocks = (list(self.blocks_maps.values())[0])
        for name, layout in self.layouts_maps.items():
            self.title_maps[name] = layout.blocks.title
            self.map.layout_dicts[name] = layout.blocks.config['layout']
            self.map.components_dicts[name] = layout.blocks.config['components']
            self.map.dependencies_dicts[name] = layout.blocks.dependencies
            self.map.blocks_dicts[name] = layout.blocks.blocks
            self.map.fns_dicts[name] = layout.blocks.fns

        base_blocks.fns = []
        base_blocks.config['components'] = []
        base_blocks.config['layout'] = {}
        base_blocks.dependencies = []
        base_blocks.blocks = {}

        start_idx = 1000
        for k, components in self.map.components_dicts.items():

            for c in components:
                c['id'] += start_idx

            self.map.layout_dicts[k] = self.iter_child(start_idx, self.map.layout_dicts[k])
            base_blocks.config['layout'].update(self.map.layout_dicts[k])

            base_blocks.config['components'] += components
            for d in self.map.dependencies_dicts[k]:
                d['targets'] = [(i+start_idx) for i in d['targets']]
                d['inputs'] = [(i+start_idx) for i in d['inputs']]
                d['outputs'] = [(i+start_idx) for i in d['outputs']]

            base_blocks.dependencies += self.map.dependencies_dicts[k]
            base_blocks.fns += self.map.fns_dicts[k]

            self.map.blocks_dicts[k] = {(idx + start_idx): _ for idx, _ in self.map.blocks_dicts[k].items()}
            base_blocks.blocks.update(self.map.blocks_dicts[k])
            start_idx += len(components)

        base_blocks.config['dependencies'] = base_blocks.dependencies

        base_blocks.dev_mode = False
        base_blocks.show_error = True

        return base_blocks
