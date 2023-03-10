#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import os
import sys
import yaml
import altair
import pandas
import shutil
import anyio
import jinja2
import starlette
import markdown_it
import Crypto.Cipher
import platform
import websockets
import numpy.core.overrides
from onnxruntime.capi import __file__ as capi_file
from muggle.package.config import build_path, dist_path, path_join
from muggle.package.prepare import build_prepare, copy_projects, get_models
from muggle.config import cli_args, STARTUP_PARAM
from muggle.logger import logger
from muggle.package.obfuscate import stardust_obfuscate
from muggle.middleware.memory_load import MemoryLoader
from muggle.engine.model import ONNXRuntimeEngine
import charset_normalizer


try:
    import dns
    need_dns = True
except:
    need_dns = False

try:
    from stardust.runtime import Runtime
    Runtime.dynamic_import("stardust.crypto_utils")
    BaseCrypto = Runtime.get_class('BaseCrypto')
    encrypted_model_supported = True
except Exception as e:
    encrypted_model_supported = False
    logger.warning("[StarDust] 框架未加载, 暂不支持加密模型")
    logger.warning(f'{e}')

SYSTEM = platform.system()

capi_path = os.path.dirname(capi_file).replace("\\", "/")

cuda_available = ONNXRuntimeEngine.cuda_available()
cuda_libs_exists = os.path.exists("muggle/package/lib/cuda")
if cuda_libs_exists and cuda_available and SYSTEM == 'Windows':
    cuda_libs_cmd = f'--include-data-dir=./muggle/package/lib/cuda/win=./'
else:
    cuda_libs_cmd = ""


is_charset_normalizer = os.path.exists(os.path.dirname(charset_normalizer.__file__))
if is_charset_normalizer:
    charset_normalizer_dir = os.path.dirname(charset_normalizer.__file__)

logger.info(f'当前引擎类型 {"GPU" if cuda_available else "CPU"}')

# print(ie_api_path)
gcc11_path = "/opt/rh/devtoolset-11"


def encrypt_models(model_paths, root_dir):
    for model_path in model_paths:
        src, trt = model_path[0], model_path[1]
        packages = {
            trt: open(path_join(root_dir, src), "rb").read()
        }
        encrypted_files = BaseCrypto.compress(
            tree=packages,
            password=STARTUP_PARAM.get('encryption_key')
        )
        open(path_join(root_dir, trt), "wb").write(encrypted_files)
        os.remove(path_join(root_dir, src))


def compile_aging_projects(need_projects, root_dir=build_path, aging=60 * 30):
    from muggle.engine.session import project_entities
    for project_name in need_projects:
        MemoryLoader.export_project(
            BaseCrypto, project_entities.get(project_name), root_dir=root_dir, aging=aging
        )


def compile_projects(**kwargs):
    # parser = argparse.ArgumentParser(description=f'MUGGLE Inference Engine')
    # parser.add_argument('--projects', type=str, nargs='+')
    # parser.add_argument("--onefile", action="store_true")
    # opt = parser.parse_args()
    if cli_args.projects:
        logger.info(f"编译项目为 | {' | '.join(cli_args.projects)} |")
    else:
        logger.info("暂无编译项目, 仅编译运行时")
    cli_args.__dict__.update(kwargs)
    logger.info(cli_args.__dict__)
    cur_dir = os.getcwd()

    try:
        shutil.rmtree(build_path)
        print("清理build目录成功")
    except:
        print("清理build目录失败")

    if not os.path.exists(build_path):
        os.makedirs(build_path)

    build_prepare()

    stardust_obfuscate(path_join(build_path, "muggle"))

    os.chdir(build_path)
    os.environ['PYTHONPATH'] = os.path.join(build_path)

    compile_engine(kwargs.get('user_info'))

    if kwargs.get('include_runtime') in [None, True]:
        compile_runtime(onefile=cli_args.onefile, compile_sdk=cli_args.compile_sdk)

    os.chdir(cur_dir)
    if cli_args.projects:
        model_paths = get_models(cli_args.projects)
        copy_projects(cli_args.projects, src_dir="./", trt_dir=build_path)
        encrypt_models(model_paths, root_dir=build_path)

        if aging := cli_args.aging:
            compile_aging_projects(cli_args.projects, root_dir=build_path, aging=aging)
        src_compile_aging_project_dir = path_join(build_path, "compile_projects")
        trt_compile_aging_project_dir = path_join(dist_path, "compile_projects")
        if os.path.exists(src_compile_aging_project_dir):
            try:
                shutil.rmtree(trt_compile_aging_project_dir)
            except:
                pass
            if not os.path.exists(trt_compile_aging_project_dir):
                os.makedirs(trt_compile_aging_project_dir)
            shutil.copytree(src_compile_aging_project_dir, trt_compile_aging_project_dir, dirs_exist_ok=True)
        copy_projects(cli_args.projects, src_dir=build_path, trt_dir=dist_path)
    logger.info(f"编译路径 = {dist_path}")


def compile_engine(user_info=None):
    sys.argv = [
        f"{sys.executable} -m nuitka",
        " --module", "ext",
        # '--clang',
        '--include-package=ext',
        '--user-plugin=muggle/package/data-hiding.py',
        # '--user-plugin=muggle/package/vmp-plugin.py',
        # '--include-package=onnxruntime',
        # '--include-package=numpy',
    ]
    engine_list = [
        _.split(".")[0] for _ in os.listdir(path_join(build_path, "ext", "engine")) if not _.startswith("__")
    ]
    engine_loader = f"engine_list = {engine_list}"
    user_info = f"user_info = '{user_info}'" if user_info else 'user_info = None'
    loader_info = "\n".join([engine_loader, user_info])
    open(path_join(build_path, "ext", "loader.py"), "w", encoding="utf8").write(loader_info)
    os.system(" ".join(sys.argv))
    ext_path = [_ for _ in os.listdir(build_path) if _.startswith("ext") and _.endswith("pyd") or _.endswith("so")][0]
    shutil.copy(path_join(build_path, ext_path), path_join(dist_path, "ext.pyd" if SYSTEM == 'Windows' else "ext.so"))


def compile_runtime(onefile=False, compile_sdk=False):
    import gradio

    cipher_path = os.path.dirname(Crypto.Cipher.__file__)

    if SYSTEM == 'Windows':
        capi_argv = f'{capi_path}/*.dll=./onnxruntime/capi/'
        crypto_argv = f'{path_join(cipher_path, "_pkcs1_decode.pyd")}=./Crypto/Cipher/'
    else:
        capi_argv = f'{capi_path}/*.so=./'
        crypto_argv = f'{path_join(cipher_path, "_pkcs1_decode.abi3.so")}=./Crypto/Cipher/'

    sys.argv = [
        'source /opt/rh/devtoolset-11/enable && gcc --version &&' if os.path.exists(gcc11_path) else '',
        f"{sys.executable} -m nuitka",
        '--clang' if SYSTEM == "Windows" else "",
        # '--clang',
        '--nofollow-import-to=*.tests',
        '--nofollow-import-to=pandas',
        # '--nofollow-import-to=gradio',
        '--nofollow-import-to=openvino',
        '--nofollow-import-to=markdown_it',
        '--nofollow-import-to=jinja2',
        '--nofollow-import-to=websockets',
        '--nofollow-import-to=charset_normalizer',
        # '--nofollow-import-to=anyio',
        '--nofollow-import-to=starlette',
        '--follow-imports',
        '--plugin-enable=numpy',
        # '--plugin-enable=gevent',
        '--plugin-enable=pylint-warnings',
        '--no-prefer-source-code',
        f'--windows-icon-from-ico=./muggle/resource/icon.{"ico" if SYSTEM == "Windows" else "png"}',
        '--include-package=cv2',
        '--include-package=stardust.runtime',
        '--include-package=stardust.session',
        '--include-package=stardust.package',
        '--include-package=stardust.loader',
        '--include-package=stardust.crypto_utils',
        '--include-package=muggle.fastapi_app',
        '--include-package=muggle.sdk',
        '--include-package=muggle.logic',
        '--include-package=muggle.engine',
        '--include-package=muggle.pages',
        '--include-package=muggle.pages.base',
        '--include-package=muggle.pages.docs',
        '--include-package=muggle.pages.preview',
        '--include-package=muggle.pages.utils',
        '--include-package=muggle.pages.components',
        '--include-package=muggle.pages.components.base',
        '--include-package=muggle.pages.components.displays',
        '--include-package=muggle.pages.components.inputs',
        '--include-package=muggle.pages.components.examples',
        '--include-package=muggle.middleware',
        '--include-package=muggle.categories',
        '--include-package=muggle.entity',
        '--include-package=muggle.constants',
        '--include-package=muggle.handler',
        '--include-package=easycython',
        '--include-package=cffi',
        # '--include-package=gevent',
        # '--include-package=eventlet',
        # '--include-package=gunicorn',
        # '--include-package=waitress',
        # '--include-package=flask',
        '--include-package=uvicorn',
        '--include-package=psutil',
        '--include-package=gradio',
        '--include-package=mdurl',
        '--include-package=matplotlib',
        # '--include-package=pandas',
        '--include-package=matplotlib.figure',
        '--include-package=pyparsing',
        '--include-package=yaml',
        '--include-package=numpy',
        '--include-package=markupsafe',
        '--include-package=pkg_resources.extern',
        '--include-package=pkg_resources._vendor',
        '--include-package=onnxruntime',
        '--include-package=PIL.Image',
        '--include-package=PIL.ImageDraw',
        '--include-package=PIL.ImageFont',
        '--include-package=PIL.ImageOps',
        '--include-package=PIL.ImageSequence',
        '--include-package=PIL.ImageEnhance',
        '--include-package=PIL.ImageFilter',
        '--include-package=Crypto.PublicKey.RSA',
        '--include-package=Crypto.Cipher.AES',
        '--include-package=Crypto.Cipher.DES3',
        '--include-package=Crypto.Cipher.DES',
        '--include-package=Crypto.Util._raw_api',
        '--include-package=Crypto.Util.Padding',
        '--include-package=Crypto.Cipher.PKCS1_v1_5',
        '--include-package=Crypto.Random',
        '--include-package=typing',
        '--include-package=pytz',
        '--include-package=gunicorn.glogging' if SYSTEM != 'Windows' else '',
        '--include-package=markdown_it',
        '--include-package=anyio',
        '--include-package=OpenSSL.crypto',
        '--include-package=numpy.core.multiarray',
        '--include-package=cryptography.hazmat.primitives.serialization.pkcs12',
        '--include-package=urllib3.contrib.pyopenssl',
        '--include-package=requests.adapters',
        f'--output-dir={dist_path}',
        '--onefile' if onefile is True else "",
        '--assume-yes-for-downloads',
        f'--include-data-file=./muggle/package/lib/zlibwapi.dll=./zlibwapi.dll' if cuda_available else "",
        f'--include-data-file=./muggle/corpus/*.*=./muggle/corpus/',
        f'--include-data-dir=./muggle/resource=./muggle/resource',
        f'--include-data-file={os.path.join(os.path.dirname(gradio.__file__), "*.txt")}=./gradio/',
        f"--include-data-file={capi_argv}",
        f'--include-data-dir={os.path.dirname(dns.__file__)}=dns/' if need_dns else "",
        f'--include-data-dir={os.path.dirname(pandas.__file__)}=pandas/',
        f'--include-data-dir={os.path.dirname(markdown_it.__file__)}=markdown_it/',
        f'--include-data-dir={os.path.dirname(anyio.__file__)}=anyio/',
        f'--include-data-dir={os.path.dirname(jinja2.__file__)}=jinja2/',
        f'--include-data-dir={os.path.dirname(starlette.__file__)}=starlette/',
        f'--include-data-dir={os.path.dirname(gradio.__file__)}=gradio/',
        f'--include-data-dir={os.path.dirname(websockets.__file__)}=websockets/',
        f'--include-data-dir={os.path.dirname(altair.__file__)}=altair/',
        f'--include-data-dir={charset_normalizer_dir}=charset_normalizer/' if is_charset_normalizer else "",
        cuda_libs_cmd if cuda_libs_exists else "",
        # f'--include-data-dir={os.path.join(os.path.dirname(gradio.__file__), "templates")}=gradio/templates',
        f'--include-data-file={crypto_argv}',
        '--user-plugin=./muggle/package/data-hiding.py',
        # '--user-plugin=./muggle/package/hinted-mods.py',
        '--nofollow-import-to=cython',
        '--plugin-enable=multiprocessing',
        # '--python-flag=no_annotations',
        # '--data-hiding-salt-value=run-time',
        '--plugin-enable=pkg-resources',
        '--show-progress',
        f'./main_{"gpu" if cuda_available else "cpu"}.py' if SYSTEM == 'Windows' else './main.py',
        '--standalone',
    ]

    sdk_argv = [
        'source /opt/rh/devtoolset-11/enable && gcc --version &&' if os.path.exists(gcc11_path) else '',
        f"{sys.executable} -m nuitka",
        '--module', "muggle",
        '--clang' if SYSTEM == "Windows" else "",
        # '--clang',
        '--nofollow-import-to=*.tests',
        # '--follow-imports',
        '--plugin-enable=pylint-warnings',
        '--no-prefer-source-code',
        '--include-package=muggle',
        # '--include-package=stardust.runtime',
        # '--include-package=stardust.session',
        # '--include-package=stardust.package',
        # '--include-package=stardust.loader',
        # '--include-package=stardust.crypto_utils',
        # '--include-package=muggle.core',
        # '--include-package=muggle.logic',
        # '--include-package=muggle.engine',
        # '--include-package=muggle.middleware',
        f'--output-dir={dist_path}',
        # '--onefile' if onefile is True else "",
        '--assume-yes-for-downloads',

        # f'--include-data-file=./muggle/corpus/*.*=./muggle/corpus/',
        # f'--include-data-file=./muggle/resource/*.*=./muggle/resource/',
        # f'--include-data-file=./muggle/templates/*.*=./muggle/templates/',
        # f'--include-data-file=./muggle/static/*.*=./muggle/static/',
        '--user-plugin=./muggle/package/data-hiding.py',
        # '--embed-',
        # '--nofollow-import-to=cython',
        # '--plugin-enable=multiprocessing',
        # '--python-flag=no_annotations',
        # '--plugin-enable=pkg-resources',
        '--show-progress',
        # '--standalone',
    ]

    print(" ".join(list(sys.argv)))
    if compile_sdk:
        os.system(" ".join(sdk_argv))
    else:
        os.system(" ".join(sys.argv))


if __name__ == '__main__':
    compile_projects(onefile=True, compile_sdk=False)