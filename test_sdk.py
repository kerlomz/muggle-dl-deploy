#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import io
import time
import PIL.Image
from muggle import SDK

# 1.1 直接使用PIL.Image.open 打开图片
# im = PIL.Image.open("projects/bd/preview.png")

# 1.2 希望给PIL传入 bytes
img_path = r"projects\<project_name>\demo\image.png"

data_stream = io.BytesIO(open(img_path, "rb").read())
im = PIL.Image.open(data_stream)

# 2. 指定需要加载的引擎, 相当于初始化, (首次调用预测函数依然会比较慢, 懒加载真正初始化是在首次调用预测函数时)
handler = SDK.get("<project_name>")

# 3. 多次调用该模型
for i in range(100):
    st = time.time()
    predict_text, score = handler.execute(im)
    print(predict_text, score, time.time() - st)

# 要记得关闭文件流, 可以用 with xxx as
data_stream.close()