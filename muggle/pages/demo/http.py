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

var imageBase64 = Convert.ToBase64String(File.ReadAllBytes("main.png"));
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


nodejs_demo_code = """
const restler = require('restler');
const fs = require('fs');
const path = require('path');
const btoa = require('btoa');
const crypto = require('crypto');

const imageBase64 = btoa(fs.readFileSync(path.join(__dirname, 'main.png')));
{define_code}

const requestData = {{
    image: imageBase64,
    project_name: '{project_name}',
{params_code}
}};

restler.post('http://{host}/runtime/text/invoke', {{
    data: JSON.stringify(requestData),
    headers: {{
        'Content-Type': 'application/json',
    }},
}}).on('complete', function(result) {{
    console.log(result);
}});
"""

cpp_demo_code = """
#include <iostream>
#include <fstream>
#include <sstream>
#include <vector>
#include <cstring>
#include <cstdlib>
#include <boost/asio.hpp>
#include <openssl/md5.h>
#include <nlohmann/json.hpp>
#include <openssl/bio.h>
#include <openssl/evp.h>
#include <openssl/buffer.h>



using namespace boost::asio;
using namespace boost::asio::ip;
using json = nlohmann::json;

std::string readFileToBase64(const std::string& filePath) {{
    std::ifstream inputFileStream(filePath, std::ios::binary);
    if (!inputFileStream) {{
        std::cerr << "Cannot open file: " << filePath << std::endl;
        return "";
    }}

    std::ostringstream fileContentStream;
    fileContentStream << inputFileStream.rdbuf();

    std::string fileContent = fileContentStream.str();
    const char* buffer = fileContent.c_str();
    size_t length = fileContent.size();

    BIO* bio = BIO_new(BIO_f_base64());
    BIO_set_flags(bio, BIO_FLAGS_BASE64_NO_NL);
    BIO* bioMem = BIO_new(BIO_s_mem());
    bio = BIO_push(bio, bioMem);

    BIO_write(bio, buffer, length);
    BIO_flush(bio);

    BUF_MEM* bufferPtr = nullptr;
    BIO_get_mem_ptr(bio, &bufferPtr);
    std::string base64Content(bufferPtr->data, bufferPtr->length);

    BIO_free_all(bio);

    return base64Content;
}}

std::string md5(const std::string& str) {{
    unsigned char digest[MD5_DIGEST_LENGTH];
    MD5(reinterpret_cast<const unsigned char*>(str.c_str()), str.size(), digest);
    std::stringstream ss;
    for (int i = 0; i < MD5_DIGEST_LENGTH; i++) {{
        ss << std::hex << std::setw(2) << std::setfill('0') << static_cast<int>(digest[i]);
    }}
    return ss.str();
}}

void sendRequest() {{

    std::string mainBase64 = readFileToBase64("main.png");
{define_code}  

    json requestData;
    requestData["project_name"] = "{project_name}";
    requestData["image"] = mainBase64;
{params_code}
    std::string requestJson = requestData.dump();

    std::string requestString = "POST /runtime/text/invoke HTTP/1.1\\r\\n";
    requestString += "Host: {host} \\r\\n";
    requestString += "Content-Type: application/json\\r\\n";
    requestString += "Content-Length: " + std::to_string(requestJson.size()) + "\\r\\n";
    requestString += "Connection: close\\r\\n\\r\\n";
    requestString += requestJson;

    io_context io;
    tcp::resolver resolver(io);
    tcp::resolver::results_type endpoints = resolver.resolve("{ip}", "{port}");
    tcp::socket socket(io);
    boost::asio::connect(socket, endpoints);

    boost::asio::write(socket, boost::asio::buffer(requestString));

    std::vector<char> responseBuffer;
    boost::system::error_code error;
    size_t responseLength = 0;
    do {{
        responseBuffer.resize(responseLength + 1024);
        responseLength += socket.read_some(boost::asio::buffer(responseBuffer.data() + responseLength, 1024), error);
    }} while (error != boost::asio::error::eof);

    responseBuffer.resize(responseLength);
    std::string responseString(responseBuffer.begin(), responseBuffer.end());
    std::cout << responseString << std::endl;

}}

int main() {{
    sendRequest();
    return 0;
}}
"""

lua_demo_code = """
local http = require("socket.http")
local json = require("json")
local base64 = require("base64")
local md5 = require("md5")

function file_to_base64(filename)
    local file = assert(io.open(filename, "rb"))
    local data = file:read("*all")
    file:close()
    return base64.encode(data)
end

-- 转换为Base64编码
local main_b64 = file_to_base64("main.png")
{define_code}

-- 组装JSON对象
local json_data = {{
  project_name = "{project_name}",
  image = main_b64,
{params_code}
}}

-- 将JSON对象转换为JSON字符串
local payload = json.encode(json_data)

local response = {{}}
local res, status, headers = http.request{{
    url = "http://{host}/runtime/text/invoke",
    method = "POST",
    headers = {{
        ["Content-Type"] = "application/json",
        ["Content-Length"] = #payload,
    }},
    source = ltn12.source.string(payload),
    sink = ltn12.sink.table(response),
}}

local res_body = table.concat(response)
---- 检查请求是否成功
if res and status == 200 then
    -- 解码JSON响应体
    print(res_body)
else
    print(res_body)
    print("HTTP request failed.")
end
"""

php_demo_code = """
<?php

// 读取文件并将其转换为Base64编码
function file_to_base64($filename) {{
    $data = file_get_contents($filename);
    return base64_encode($data);
}}

$main_b64 = file_to_base64("main.jpg");
{define_code}

// 组装JSON对象
$json_data = [
    "project_name" => "{project_name}",
    "image" => $main_b64,
{params_code}
];

// 将JSON对象转换为JSON字符串
$payload = json_encode($json_data);

// 发送HTTP POST请求
$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, "http://{host}/runtime/text/invoke");
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_HTTPHEADER, [
    "Content-Type: application/json",
    "Content-Length: " . strlen($payload),
]);
curl_setopt($ch, CURLOPT_POSTFIELDS, $payload);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
$response = curl_exec($ch);
curl_close($ch);

// 解码JSON响应体
$response_data = json_decode($response, true);
print_r($response_data);
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


