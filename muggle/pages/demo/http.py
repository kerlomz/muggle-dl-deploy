#!/usr/bin/env python3
# -*- coding:utf-8 -*-

java_prefix_code = """
package org.example;

import com.alibaba.fastjson.JSONArray;
import com.alibaba.fastjson.JSONObject;
import okhttp3.*;

import java.io.*;
import java.math.BigInteger;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.Base64;

public class Test {

    public static class MD5Utils {
        public static String stringToMD5(String plainText) {
            byte[]  secretBytes = null;
            try {
                secretBytes = MessageDigest.getInstance("md5").digest(plainText.getBytes());
            }  catch (NoSuchAlgorithmException e) {
                throw new RuntimeException("没有这个md5算法！");
            }
            StringBuilder md5code = new StringBuilder(new BigInteger(1, secretBytes).toString(16));
            for (int i = 0; i < 32 - md5code.length(); i++) {
                md5code.insert(0, "0");
            }
            return md5code.toString();
        }

    }

    public static byte[]  toByteArray(String filename) throws IOException {

        File f = new File(filename);
        if (!f.exists()) {
            throw new FileNotFoundException(filename);
        }

        try (ByteArrayOutputStream bos = new ByteArrayOutputStream((int) f.length())) {
            BufferedInputStream in = null;
            in = new BufferedInputStream(new FileInputStream(f));
            int buf_size = 1024;
            byte[] buffer = new byte[buf_size];
            int len = 0;
            while (-1 != (len = in.read(buffer, 0, buf_size))) {
                bos.write(buffer, 0, len);
            }
            return bos.toByteArray();
        } catch (IOException e) {
            e.printStackTrace();
            throw e;
        }
    }


    public static void main(String[] args) throws IOException {
        OkHttpClient client = new OkHttpClient().newBuilder().build();
        JSONObject data = new JSONObject();

        //  读取本地图片文件并用Base64编码
        String imageParam = Base64.getEncoder().encodeToString(toByteArray("image.jpg"));

        data.put("image", imageParam);
"""

java_suffix_code = """
        {
            try {
                response = client.newCall(request).execute();
                System.out.println(response.body().string());
            }  catch (IOException e) {
                e.printStackTrace();
            }
        }
    }
}
"""

java_define_param_code = """
        data.put("project_name", "{project_name}");
        
{params_code}
"""

java_req_body_code = """
        MediaType mediaType = MediaType.parse("application/json");
        RequestBody body = RequestBody.create(mediaType, String.valueOf(data));
        Request request = new Request.Builder()
                .url("http://{host}/runtime/text/invoke")
                .method("POST", body)
                .addHeader("Content-Type", "application/json")
                .build();
        Response response;
"""


python_demo_code = """
import requests
import base64
import hashlib

with open(r"main.png", "rb") as f:
    b = f.read()
    
main_b64 = base64.b64encode(b).decode()
{define_code}

r = requests.post("http://{host}/runtime/text/invoke", json={{
    "project_name": "{project_name}",
    "image": main_b64,
{params_code}
}})
print(r.json())
"""

csharp_demo_code = """
using System;
using System.IO;
using System.Text;
using System.Net.Http;
using System.Net.Http.Headers;

string GetMD5Hash(string input)
{{
    using var md5 = MD5.Create();
    var inputBytes = Encoding.UTF8.GetBytes(input);
    var hashBytes = md5.ComputeHash(inputBytes);
    return BitConverter.ToString(hashBytes).Replace("-", "").ToLowerInvariant();
}}

var imageBase64 = Convert.ToBase64String(File.ReadAllBytes("image.png"));
{define_code}

var payload = new
{{
    project_name = "{project_name}",
    image = imageBase64,
{params_code}
}};

var httpClient = new HttpClient();
var httpResponse = await httpClient.PostAsync("http://{host}/runtime/text/invoke", new StringContent(
    Newtonsoft.Json.JsonConvert.SerializeObject(payload),
    Encoding.UTF8,
    "application/json"
));

var responseString = await httpResponse.Content.ReadAsStringAsync();
Console.WriteLine(responseString);

"""


e_prefix_code = """
.版本 2
.支持库 internet
.支持库 spec

.程序集 窗口程序集_启动窗口

.子程序 __启动窗口_创建完毕

_启动子程序 ()


.子程序 _启动子程序, 整数型, , 本子程序在程序启动后最先执行
.局部变量 title, 字节集, , "0"

"""

e_define_param_code = """
{define_code}
"""

e_exec_code = """
识别验证码 (读入文件 (“main.png”){title_code})
"""

e_suffix_code = """

返回 (0)  ' 可以根据您的需要返回任意数值

.子程序 识别验证码
.参数 主体, 字节集
{exec_code}
.局部变量 json, 类_json
.局部变量 data, 文本型
.局部变量 image, 文本型
.局部变量 i, 整数型

image = 编码_BASE64编码 (主体)
json.置属性 (“project_name”, “{project_name}”, )
json.置属性 (“image”, image, )
{impl_code}

调试输出 (json.取数据文本 ())

data ＝ 编码_Utf8到Ansi (网页_访问 (“http://{host}/runtime/text/invoke”, 1, json.取数据文本 (), , , “Content-Type: application/json;charset:utf-8;”, , , , , , , ))
信息框 (data, 0, , )

"""