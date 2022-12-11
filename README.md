# 1. 部署项目

| 文件                      | 功能                                                         |
| ------------------------- | ------------------------------------------------------------ |
| fastapi_app.py            | FastAPI 服务应用堆栈，包括服务的路由定义等等，可在这里修改API路由 |
| config.py                 | 配置文件，定义一些基本传参，详细见附录                       |
| constants.py              | 静态变量定义，原本这个框架是包含授权，试用模式，加密，网络验证等等的，还有配置文件化，不过因为是加密的，与项目无关，就都优化掉了，只保留最基本的几个配置，需要关注的只有 modules_enabled，该模式也方便后续自己添加中间件，控制开启或关闭。 |
| engine/*                  | 包含运行时引擎，模型引擎，项目引擎，会话引擎等引擎基类       |
| entity.py                 | 这块主要是针对点选拓展的，基础数据结构如坐标这些的           |
| exception.py              | 自定义异常                                                   |
| handler.py                | WEB服务的核心逻辑，最精简实现可以参考SDK核心逻辑             |
| logger.py                 | 日志                                                         |
| main.py                   | Web服务启动文件                                              |
| sdk.py                    | SDK服务的核心逻辑                                            |
| utils.py                  | 系统工具类，动态加载中间件，WEB服务参数解析等                |
| requirements.txt          | 依赖声明，使用pip install -r requirements.txt 一键安装依赖   |
| logic/base.py             | 逻辑模块的基本逻辑                                           |
| logic/cls.py              | Cls 模型逻辑                                                 |
| logic/ctc.py              | CTC 模型逻辑                                                 |
| logic/click.py            | 点选逻辑                                                     |
| middleware                | 中间件，包括展示页面（主要方便测试），授权逻辑等，目前该项目没用到，图像展示 (Draw) 默认开启。http://127.0.0.1:19199/preview 可以访问测试页面。 |
| /projects/*               | 工程路径， 路径下的文件夹即为实际调用时的项目名 [project_name] 参数 |
| /ext/engine/*             | 附加模型引擎的实现类                                         |
| /logic/*                  | 附加项目逻辑的实现类                                         |
| server/gunicorn_server.py | gunicorn server, 通过config.py启动参数控制                   |



| 项目工程（Projects） |       |
|----------------|-------|
| xxx            | xxx识别 |



## 1.1 系统要求

最低：Windows 2012 内核以上 / Ubuntu18以上

| Linux                     | Windows                      |
| ------------------------- | ---------------------------- |
| Ubuntu 20/18；CentOS 7.6+ | Windows 2012/2016/2019/10/11 |




## 1.2 环境要求

Python3.9 (:=表达式所以最低只能3.8)



## 1.3 项目部署核心流程

1. 安装 Python3.9

2. ```pip install muggle-deploy-1.0.0.tar.gz -i https://mirrors.cloud.tencent.com/pypi/simple ``` 在自己的项目中，安装项目依赖。

3. 服务部署：

   1. SDK方式调用：参考 test_sdk.py

   2. WEB部署：``` python test_server.py --port 19199 ``` 启动项目主服务

4. 编译可执行文件（可移植无需Python运行环境部署框架）：

    ```python3.9 test_compile.py --projects 项目1 项目2``

   默认编译路径在 %TEMP%/muggle_dist 下。



**test_server.py**

```python
#!/usr/bin/env python3
# -*- coding:utf-8 -*-
from muggle import serve

if __name__ == '__main__':
    serve()
```



### 1.3.1 CentOS部署全流程

```shell
# 工作路径为 muggle-deploy-1.0.0 项目中

# 1. 安装 Python3.9.9 环境
sudo yum -y update
sudo yum install gcc openssl-devel bzip2-devel libffi-devel zlib-devel git -y

cd muggle/package/lib && tar -xvf Python-3.9.9.tar.gz && cd Python-3.9.9/
sudo ./configure --enable-optimizations --enable-shared
make clean &&  make altinstall

# 配置环境变量 & 安装 muggle 模块
cd ../../../../ && echo "/usr/local/lib" >> /etc/ld.so.conf && ldconfig -v
python3.9 -m pip install muggle-deploy-1.0.0.tar.gz -i https://mirrors.cloud.tencent.com/pypi/simple

# 2. 把 projects / logic 结构的模型和相关配置放置于项目根目录

# 3.1 前台启动，用于测试环境安装是否有误 
# python3.9 test_server.py --port 19199 
# 3.2 后台启动
nohup python3.9 test_server.py --port 19199 &

# 4. 查看 nohup 日志
tail -f -n 100 nohup.out 查看实时日志
```



### 1.3.2 Ubuntu部署流程

```bash
# 工作路径为 muggle-deploy-1.0.0 项目中

# 1. 安装 Python3.9.9 环境
sudo wget -O /etc/apt/sources.list http://mirrors.cloud.tencent.com/repo/ubuntu20_sources.list
sudo apt-get clean all
sudo apt-get update
sudo apt install software-properties-common -y
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install python3.9 -y
sudo apt install python3.9-dev -y
sudo apt install python3-pip -y
sudo apt-get install ccache -y
sudo apt install chrpath -y
sudo apt-get install patchelf

# 配置环境变量 & 安装 muggle 模块
python3.9 -m pip install git+git://github.com/benoitc/gunicorn.git --no-cache-dir --force-reinstall
python3.9 -m pip install muggle-deploy-1.0.0.tar.gz -i https://mirrors.cloud.tencent.com/pypi/simple

# 2. 把 projects / logic  结构的模型和相关配置放置于项目根目录

# 3.1 前台启动，用于测试环境安装是否有误 
# python3.9 test_server.py --port 19199 
# 3.2 后台启动
nohup python3.9 test_server.py --port 19199 &

# 4. 查看 nohup 日志
tail -f -n 100 nohup.out 查看实时日志
```



### 1.3.3 Linux编译版部署

```shell
cd main.dist

# 1. 把 projects / logic 结构的模型和相关配置放置于项目根目录

# 2.1 前台启动，用于测试环境安装是否有误 
# ./main --port 19199 
# 2.2 后台启动
nohup ./main.bin --port 19199 &

# 3. 查看 nohup 日志
tail -f -n 100 nohup.out 查看实时日志
```





### 1.3.2 启动参数附录

| 启动参数 | 介绍                        |
| -------- | --------------------------- |
| host     | 服务监听地址，默认为0.0.0.0 |
| port     | 服务监听端口，默认为19199   |
| workers  | 进程数                      |
| threads  | 线程数                      |



## 1.4 服务调用

服务启动之后根据服务日志可见提示：

调用文档：http://127.0.0.1:19199/runtime/api/guide，端口号若自定义需自行修改（调用文档请使用该地址访问，因为生成之后的文档有一定的时效，若404请刷新该引导页面重试。



SDK调用方式（可用于嵌入Python的跨语言调用）：

```python
import os

import PIL.Image
from muggle import SDK

# 演示项目中获取demo图片示例
project_name = "项目名"
project_dir = rf"projects/{project_name}/demo"
image_path = [os.path.join(project_dir, name) for name in os.listdir(project_dir) if name.startswith("image")][0]
title_paths = [os.path.join(project_dir, name) for name in os.listdir(project_dir) if name.startswith("title")]

if len(title_paths) > 1:
    title = [PIL.Image.open(path) for path in title_paths]
elif len(title_paths) == 1:
    title = PIL.Image.open(title_paths[0])
else:
    title = None
    
image = PIL.Image.open(image_path)

# 这部分开始才是核心调用，
# image 是 [主图: PIL.Image 格式]， 
# title 看具体项目逻辑，可以是List[PIL.Image]/PIL.Image/None/str，视具体情况而定

# 初始化项目SDK，如果调用循环调用预测函数，那么sdk必须在循环以外避免重复初始化
sdk = SDK.get(project_name)

# 预测函数
predictions, score = sdk.execute(image, title=title)
print(predictions, score)
```

