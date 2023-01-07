#!/usr/bin/env python
# -*- coding: utf-8 -*-
import platform
from setuptools import setup, find_packages
from setuptools.dist import Distribution
dist = Distribution()
dist.parse_config_files()

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

data_files = [
    ('muggle/resource', [
        'muggle/resource/icon.ico',
        'muggle/resource/icon.png',
    ]),
    ('muggle/resource/fonts', [
        'muggle/resource/fonts/msyh.ttc',
        'muggle/resource/fonts/index.ttf',
        'muggle/resource/fonts/text.ttf',
    ]),
    ('muggle/package/lib', [
        'muggle/package/lib/patchelf-0.14.3-x86_64.tar.gz',
        'muggle/package/lib/Python-3.9.9.tar.gz',
        'muggle/package/lib/gunicorn-master.zip',
        'muggle/package/lib/appimagetool-x86_64.AppImage',
        'muggle/package/lib/CentOS7-Base-163.repo',
        'muggle/package/lib/zlibwapi.dll',

    ]),
    ('muggle/package/lib/cv', [
        'muggle/package/lib/cv/__init__.py',
        'muggle/package/lib/cv/cv2.cpython-39-x86_64-linux-gnu.so',
        'muggle/package/lib/cv/lib.tar.gz',
    ]),
    ('muggle/corpus', [
        'muggle/corpus/builtin.dict'
    ]),
    ('.', [
        'test_compile.py',
        'test_sdk.py',
        'test_server.py',
        'deploy_build.sh',
        'Dockerfile_Compile',
        'Dockerfile_Deploy',
    ]),
    ('muggle', [
        'muggle/requirements.txt'
    ])
]

install_requires = [
    'scikit-build', 'certifi', 'pyyaml', 'psutil',
    'requests', 'tinyaes', 'certifi', 'requests',
    'paramiko', 'six', 'zstandard', 'nuitka', 'loguru', 'jinja2', 'altair',
    'pyyaml', 'pycryptodome', 'easycython', 'pyOpenSSL', 'cryptography', 'pydantic',
    'fastapi', 'uvicorn', 'gradio==3.12', 'httpcore==0.15', 'markupsafe', 'numpy', 'Pillow', 'opencv-python-headless',
]

dependency_links = []

if platform.system() != 'Windows':
    install_requires.append('gunicorn')

extras = dist.get_option_dict('extras_require')

if 'gpu' not in extras:
    install_requires.append('onnxruntime')

setup(
    name="muggle-deploy",
    version="1.0.0",
    author="kerlomz",
    description="muggle-deploy",
    extras_require={
        'gpu': ['onnxruntime-gpu'],
    },
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kerlomz",
    packages=find_packages(where='.', exclude=['logic', 'ext'], include=('*',)),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    data_files=data_files,
    install_requires=install_requires,
    python_requires='>=3.9,<3.11',
    include_package_data=True,
    install_package_data=True,
)
