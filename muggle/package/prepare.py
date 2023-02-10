#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import shutil
import time
import muggle
import stardust
import os.path
import importlib
import muggle.logic
from muggle.package.config import *
from muggle.engine.utils import Path
from muggle.engine.session import project_entities
from muggle.middleware.memory_load import MemoryLoader


muggle_path = os.path.dirname(muggle.__file__)
ext_path = os.path.join(os.path.dirname(os.path.dirname(muggle.__file__)), "ext")
logic_path = os.path.join(os.path.dirname(os.path.dirname(muggle.__file__)), "logic")
stardust_path = os.path.dirname(stardust.__file__)

main_template = """
 #!/usr/bin/env python3
# -*- coding:utf-8 -*-
from muggle.main import serve


if __name__ == '__main__':
    serve()
"""

__init__template = """
#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""


def add_logics(project_name):
    need_logic_name = project_entities.get(project_name).strategy
    global_logic_dir = "logic"
    global_logic_path = MemoryLoader.find_need_logic(global_logic_dir, need_logic_name)
    print(global_logic_path)
    if global_logic_path:
        filename = os.path.basename(global_logic_path)
        return global_logic_path, path_join(dist_path, "logic", filename)
    return None


def copy_project(project_name, src_dir="./", trt_dir=dist_path):
    target_path = path_join(trt_dir, "projects", project_name)
    if not os.path.exists(target_path):
        shutil.copytree(path_join(src_dir, "projects", project_name), path_join(trt_dir, "projects", project_name))
    logic_paths = add_logics(project_name)
    if logic_paths:
        src, target = logic_paths
        trt_dir = os.path.dirname(target)
        if not os.path.exists(trt_dir):
            os.makedirs(trt_dir)
        shutil.copy(src, target)


def copy_projects(need_projects, src_dir, trt_dir):
    print(f'复制项目: {src_dir} -> {trt_dir}')
    for project_name in need_projects:
        copy_project(project_name, src_dir=src_dir, trt_dir=trt_dir)


def get_models(need_projects):
    model_paths = []
    for project_name in need_projects:
        project_entity = project_entities.get(project_name)
        models = [model_name for _, model_name in project_entity.models.items()]
        model_dir = project_entity.project_path.model_dir
        for model in models:
            model_paths.append([
                path_join(model_dir, model, "model.onnx"),
                path_join(model_dir, model, "model.crypto")
            ])
    return model_paths


def build_prepare():
    shutil.copytree(muggle_path, os.path.join(build_path, "muggle"))
    shutil.copytree(ext_path, os.path.join(build_path, "ext"))
    if os.path.exists(logic_path):
        shutil.copytree(logic_path, os.path.join(build_path, "logic"))
    shutil.copytree(stardust_path, os.path.join(build_path, "stardust"))
    for main_name in ["main.py", "main_cpu.py", "main_gpu.py"]:
        open(os.path.join(build_path, main_name), "w", encoding="utf8").write(main_template)
    open(os.path.join(build_path, "__init__.py"), "w", encoding="utf8").write(__init__template)
    # if build_sdk:
    # print('正在删除 "__init__.py" 文件...')
    # init_path = os.path.join(build_path, "muggle", "__init__.py")
    # print('---', init_path)
    # os.remove(init_path)
    # # shutil.rmtree(init_path)
    # print('成功删除 "__init__.py" 文件...')
    shutil.copy(os.path.join(muggle_path, "package", "data-hiding.py"), os.path.join(build_path, "data-hiding.py"))



