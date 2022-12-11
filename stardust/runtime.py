#!/usr/bin/env python3
# -*- coding:utf-8 -*-
from types import MethodType
# from stardust.parser import run_code, get_code
import os
import io
import sys
import time
import datetime
import base64
import importlib
from Crypto.Cipher import AES
from typing import Union
from enum import Enum, unique


class AttrType(Enum):
    FunctionType = 'FunctionType'
    ClassType = 'ClassType'


globals_param = {
    AttrType.FunctionType: {},
    AttrType.ClassType: {}
}


class _Cipher:
    BS = 16

    @classmethod
    def encrypt(cls, raw: Union[str, bytes]) -> bytes:
        if isinstance(raw, str):
            raw = raw.encode("utf8")
        key, boundary, io_bytes = os.urandom(16), os.urandom(256), io.BytesIO()
        pad = (lambda x: x + (cls.BS - len(x) % cls.BS) * chr(cls.BS - len(x) % cls.BS).encode("utf8"))
        raw = pad(raw)
        pk, sk = key[::2], key[1::2]
        cipher = AES.new((sk+pk), AES.MODE_CBC, key)
        p, s = raw[::2], raw[1::2]
        ep = AES.new(boundary[:16], AES.MODE_CBC, boundary[:16]).encrypt(pad(p))
        es = AES.new(boundary[-16:], AES.MODE_CBC, boundary[-16:]).encrypt(pad(s))
        ek = cipher.encrypt(pad(key))[:16]
        enc_bytes = AES.new(ek, AES.MODE_CBC, ek).encrypt(pad(es + boundary + boundary[::-1] + ep))
        p, s = enc_bytes[::2], enc_bytes[1::2]
        io_bytes.write(boundary)
        io_bytes.write(key)
        io_bytes.write(boundary)
        io_bytes.write(base64.b85encode(s + boundary + p))
        return base64.b85encode(io_bytes.getvalue())

    @classmethod
    def decrypt(cls, enc: Union[bytes]):
        pad = (lambda x: x + (cls.BS - len(x) % cls.BS) * chr(cls.BS - len(x) % cls.BS).encode("utf8"))
        enc = base64.b85decode(enc)
        boundary = enc[:256]
        data = enc[256:].split(boundary)
        pk, sk = data[0][::2], data[0][1::2]
        cipher = AES.new((sk + pk), AES.MODE_CBC, data[0])
        ek = cipher.encrypt(pad(data[0]))[:16]
        c1 = AES.new(boundary[:16], AES.MODE_CBC, boundary[:16])
        c2 = AES.new(boundary[-16:], AES.MODE_CBC, boundary[-16:])
        ck = AES.new(ek, AES.MODE_CBC, ek)

        s, p = base64.b85decode(data[1]).split(boundary)
        dec = [0] * (len(p) + len(s))
        dec[::2], dec[1::2] = list(p), list(s)
        try:
            pad = (lambda x: x[:-ord(x[len(x) - 1:])])

            decrypted = pad(ck.decrypt(bytes(dec)))
            es, ep = decrypted.split(boundary + boundary[::-1])

            p = pad(c1.decrypt(ep))
            s = pad(c2.decrypt(es))
            dec = [0] * (len(p) + len(s))
            dec[::2], dec[1::2] = list(p), list(s)
            decrypted = pad(bytes(dec))
        except Exception as e:
            print(e)
            return None
        return decrypted


class Runtime:

    class Loader:

        @classmethod
        def from_code(cls, *args, **kwargs):
            Runtime.dynamic_import("stardust.loader")
            return Runtime.get_class("Loader").from_code(*args, **kwargs)

    class Compile:

        @classmethod
        def from_file(cls, *args, **kwargs):
            Runtime.dynamic_import("stardust.package")
            return Runtime.get_class("Compile").from_file(*args, **kwargs)

        @classmethod
        def traversal_compile(cls, *args, **kwargs):
            Runtime.dynamic_import("stardust.package")
            return Runtime.get_class("Compile").traversal_compile(*args, **kwargs)

    class SessionX:

        def __new__(cls, *args, **kwargs):
            Runtime.dynamic_import("stardust.session")
            return Runtime.get_class("SessionX")(*args, **kwargs)

    @classmethod
    def get_params(cls, globals_params: dict):

        kk = str(sum([v(*range(4)) for k, v in tuple(globals_params.items()) if k.startswith("*")]))
        kk = int(float(kk))

        x = sorted(list([len(k) for k in tuple(globals_params.keys()) if not k.startswith("_")]))
        q = sorted([(_, x.count(_)) for _ in set(x) if _ > 30], key=lambda t: t[1])

        d = datetime.datetime.today().day
        z = len(getattr(base64, '_b32alphabet')) + int(str(time.time())[3]) + int(str(time.time())[5]) * (kk % 100) + d

        v1 = sorted(
            [k[1::3][1::2][1::3][1::3]
             for k, v in tuple(globals_params.items())
             if len(k) == q[-3][0] and not k.startswith("_")]
        )
        v2 = sorted(
            [k[1::3][1::2][1::3][1::3]
             for k, v in tuple(globals_params.items())
             if len(k) == q[-4][0] and not k.startswith("_")]
        )
        v3 = sorted(
            [k[1::3][1::2][1::3][1::3]
             for k, v in tuple(globals_params.items())
             if len(k) == q[-5][0] and not k.startswith("_")]
        )

        v1 = "_" + base64.b85encode(
            (str(int(int(z) // 3) * kk) + "".join(v1) + time.strftime('%Y%m%d', time.localtime())).encode()).decode()[
                   1::2]
        v2 = "_" + base64.b85encode(
            (str(int(int(z) // 2) * kk) + "".join(v2) + time.strftime('%m%Y%d', time.localtime())).encode()).decode()[
                   1::2]
        v3 = "_" + base64.b85encode(
            (str(int(int(z) // 5) * kk) + "".join(v3) + time.strftime('%d%Y%m', time.localtime())).encode()).decode()[
                   1::2]

        del kk, x, q, z
        return globals_params[v1](1, 2, 3, 4), globals_params[v2](1, 2, 3, 4), globals_params[v3](1, 2, 3, 4)

    @classmethod
    def merge_code(cls, code, chrset_a, chrset_b):
        code = _Cipher.decrypt(code).decode()
        chrset_a, chrset_b = _Cipher.decrypt(chrset_a).decode(), _Cipher.decrypt(chrset_b).decode()
        chrset_1 = list(chrset_a)
        chrset_2 = list(chrset_b)
        chrset_1n_map = {i: _ for i, _ in enumerate(chrset_1)}
        chrset_2n_map = {i: _ for i, _ in enumerate(chrset_2)}
        chrset_1r_map = {i: _ for i, _ in enumerate(chrset_1[::-1])}
        chrset_2r_map = {i: _ for i, _ in enumerate(chrset_2[::-1])}

        def decode(_):
            return chrset_1n_map[
                chrset_2.index(
                    chrset_1r_map[
                        chrset_1.index(
                            chrset_2r_map[
                                chrset_1.index(
                                    chrset_2n_map[
                                        chrset_2[::-1].index(_)
                                    ]
                                )
                            ]
                        )
                    ]
                )
            ]

        decoded = list(base64.b85decode(code.encode()).decode())
        del code
        decoded = [chrset_1n_map[chrset_2[::-1].index(_)] for _ in decoded]
        decoded = list(base64.b64decode("".join(decoded).encode()).decode())
        decoded = "".join([chrset_2n_map[chrset_2[::-1].index(_)] for _ in decoded])
        decoded = list(base64.b85decode(decoded.encode()).decode())
        decoded = [decode(_) for _ in decoded]
        del decode
        return "".join(decoded)

    @classmethod
    def exec_code(cls, context, code, c1, c2):
        ast = importlib.import_module("ast")
        globals().update({k: v for k, v in ast.__dict__.items() if not k.startswith("__")})
        zlib = importlib.import_module("zlib")
        ast_data = cls.merge_code(code, c1, c2)
        del code, c1, c2
        ast_data = base64.b85decode(ast_data.encode())
        ast_data = getattr(zlib, 'decompress')(ast_data)
        module = eval(ast_data)
        del ast_data, zlib
        cm = compile(globals()['fix_missing_locations'](module), context['__file__'], 'exec')
        del module
        exec(cm, context)

    @classmethod
    def extract_path(cls, package):
        path_group = package.split(".")
        module_path = ".".join(path_group[0:-1])
        attr_name = path_group[-1]
        return module_path, attr_name

    @classmethod
    def as_module(cls, package):
        import importlib
        module = importlib.import_module(package)

        code, c1, c2 = cls.get_params(module.__dict__)
        cls.exec_code(module.__dict__, code, c1, c2)

        for class_name in [k for k, v in module.__dict__.items() if type(v) == type(cls)]:
            globals_param.get(AttrType.ClassType)[f"{package}.{class_name}"] = package

        for method_name in [k for k, v in module.__dict__.items() if
                            hasattr(v, '__call__') and not type(v).__name__.startswith("cython_")]:
            globals_param.get(AttrType.FunctionType)[f"{package}.{method_name}"] = package

        return module

    @classmethod
    def dynamic_import(cls, package):
        attrs = set(list(globals_param.get(AttrType.ClassType).keys()) + list(globals_param.get(AttrType.FunctionType)))
        attrs = set([".".join(attr.split(".")[0:-1]) for attr in attrs])
        if package in attrs:
            return
        module = cls.as_module(package)
        globals()[package] = module

    @classmethod
    def get_attr(cls, name, attr_type: AttrType):
        if '.' in name:
            module_path, attr_name = cls.extract_path(name)
            if module_path not in globals():
                raise ModuleNotFoundError(f"找不到模块 [{module_path}]")
            return getattr(globals().get(module_path), attr_name)
        attr_list = set()
        for k, v in globals_param[attr_type].items():
            if k.endswith(f".{name}") and hasattr(globals()[v], name):
                attr_list.add(getattr(globals()[v], name))
        attr_list = [attr for attr in attr_list if attr.__name__ != 'ast']
        if len(attr_list) > 1:
            attr_name = ','.join(list(attr_list))
            raise RuntimeError(f"命名空间中存在多个模块[{attr_name}]，请使用完整模块名")
        elif len(attr_list) == 1:
            return list(attr_list)[0]
        raise ModuleNotFoundError(f"找不到模块 [{name}]")

    @classmethod
    def get_method(cls, name):
        return cls.get_attr(name, AttrType.FunctionType)

    @classmethod
    def get_class(cls, name):
        return cls.get_attr(name, AttrType.ClassType)

    @classmethod
    def get_classes(cls, name_list):
        class_list = []
        for name in name_list:
            class_list.append(cls.get_class(name))
        return tuple(class_list)
