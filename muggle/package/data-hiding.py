#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
#
#     Commercial grade license of Nuitka. No distribution to outside of the
#     buyer is allowed, the file must be kept secret. Usage is limited to
#     Nuitka. Changed versions, or versions of changes sent to the
#     copyright holder are automatically licensed to him under the Apache
#     License, Version 2.0 as used in proper Nuitka, to allow opening code
#     up later.
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#
""" Commercial plug-in to make data not plain-text.
This obfuscucates data used for constants in Nuitka, but obviously
it can be reversed.
"""

import hashlib
import random
import zlib

from nuitka.__past__ import to_byte
from nuitka.plugins.PluginBase import NuitkaPluginBase
from nuitka.utils.FileOperations import getFileContents


class NuitkaPluginWindowsService(NuitkaPluginBase):
    """This is to obfuscucate constants data."""

    plugin_name = "data-hiding"
    plugin_desc = "Commercial: Hide program constant Python data from offline inspection of created binaries."

    def __init__(self):
        self.salt_value = "runtime"

        self.mapping = None
        self.size = None
        self.digest = None

        # Pseudo random mapping used to encode early C string names to e.g. find module data.
        r = random.Random(27)

        self.mapping2 = list(range(1, 256))
        random.shuffle(self.mapping2, r.random)
        self.mapping2.insert(0, 0)

    # @classmethod
    # def addPluginCommandLineOptions(cls, group):
    #     group.add_option(
    #         "--data-hiding-salt-value",
    #         action="store",
    #         dest="salt_value",
    #         default=None,
    #         help="""Salt value to make encryption result unique.""",
    #     )

    def onDataComposerResult(self, blob_filename):
        contents = getFileContents(blob_filename, "rb")
        self.size = len(contents)

        if self.salt_value is None:
            self.salt_value = zlib.adler32(contents)

        r = random.Random(self.salt_value)

        self.mapping = list(range(256))

        random.shuffle(self.mapping, r.random)

        mapping2 = dict((to_byte(c), to_byte(x)) for c, x in enumerate(self.mapping))

        with open(blob_filename, "wb") as blob_file:
            contents_iter = iter(contents)

            for count in range(8):
                c = next(contents_iter)
                if str is not bytes:
                    c = to_byte(c)

                blob_file.write(c)

            assert blob_file.tell() == 8

            last = 0
            count = 0

            self.digest = hashlib.md5(contents).digest()

            if str is not bytes:
                self.digest = [to_byte(d) for d in self.digest]

            for c in self.digest:
                temp = (last + count) % 256
                last = (ord(c) + ord(self.digest[count % 8])) % 256
                c = mapping2[c]
                c = to_byte(ord(c) ^ temp)
                blob_file.write(c)

                count += 1

            for c in contents_iter:
                if str is not bytes:
                    c = to_byte(c)

                temp = (last + count) % 256
                last = (ord(c) + ord(self.digest[count % 8])) % 256
                c = mapping2[c]
                c = to_byte(ord(c) ^ temp)
                blob_file.write(c)

                count += 1

    def encodeDataComposerName(self, data_name):
        if str is bytes:
            data_name = tuple(ord(d) for d in data_name)

        return b"".join(to_byte(self.mapping2[d]) for d in data_name)

    @staticmethod
    def getPreprocessorSymbols():
        return {"_NUITKA_EXPERIMENTAL_WRITEABLE_CONSTANTS": "1"}

    def getExtraCodeFiles(self):
        extra_code_header = r"""
extern unsigned char *decode_hidden(unsigned char *input);
extern char const *decode_public(char const *input);
#if defined(_NUITKA_CONSTANTS_FROM_RESOURCE)
#define DECODE(x) x=decode_hidden((unsigned char *)x)
#else
#define DECODE(x) decode_hidden((unsigned char *)x)
#endif
#define UNTRANSLATE(x) (char const *)decode_public(x)
"""

        extra_code_body = r"""
#include <stdint.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
static unsigned char _mapping[] = {
    %(mapping)s
};
unsigned char *decode_hidden(unsigned char *input) {
    unsigned char last = 0;
#if defined(_NUITKA_CONSTANTS_FROM_RESOURCE)
    unsigned char *output = (unsigned char *)malloc(%(size)d+8);
    memcpy(output, input, 32);
#else
    unsigned char *output = input;
#endif
    for (size_t i = 8; i < %(size)d+16; i++) {
        unsigned char c = input[i];
        unsigned char temp = (last + i - 8) %% 256;
        c = c ^ temp;
        c = _mapping[c];
        if (i >= 8+16) {
            output[i-16] = c;
        }
        last = c;
        switch(i %% 8) {
            case 0: last = (last + %(d0)s) %% 256;
            break;
            case 1: last = (last + %(d1)s) %% 256;
            break;
            case 2: last = (last + %(d2)s) %% 256;
            break;
            case 3: last = (last + %(d3)s) %% 256;
            break;
            case 4: last = (last + %(d4)s) %% 256;
            break;
            case 5: last = (last + %(d5)s) %% 256;
            break;
            case 6: last = (last + %(d6)s) %% 256;
            break;
            case 7: last = (last + %(d7)s) %% 256;
            break;
        }
    }
    return output;
}
static unsigned char _mapping2[] = {
    %(mapping2)s
};
char const *decode_public(char const *input) {
    unsigned char *buffer = (unsigned char *)malloc(strlen(input) + 1);
    unsigned char *result = buffer;
    while(*input != 0) {
        *result++ = _mapping2[*(unsigned char *)input];
        input += 1;
    }
    *result = 0;
    return (char const *)buffer;
}
"""
        m = {}
        for c, v in enumerate(self.mapping):
            m[v] = c

        m2 = {}
        for c, v in enumerate(self.mapping2):
            m2[v] = c

        return {
            "nuitka_data_decoder.h": extra_code_header,
            "data_decoder.c": extra_code_body
            % {
                "size": self.size,
                "mapping": ",".join(str(m[x]) for x in range(256)),
                "mapping2": ",".join(str(m2[x]) for x in range(256)),
                "d0": ord(self.digest[0]),
                "d1": ord(self.digest[1]),
                "d2": ord(self.digest[2]),
                "d3": ord(self.digest[3]),
                "d4": ord(self.digest[4]),
                "d5": ord(self.digest[5]),
                "d6": ord(self.digest[6]),
                "d7": ord(self.digest[7]),
            },
        }