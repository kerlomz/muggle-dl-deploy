#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import string

BLANK_TOKEN = ['_']
OBJECT = ['DefaultObject']
CHINESE_2W = sorted([chr(i) for i in range(ord(u'\u4e00'), ord(u'\u9fa5'))])
CHINESE_3755 = sorted([
        _.decode("gb2312") for _ in
        [bytearray.fromhex('%x %x' % (c+0xa0, p+0xa0)) for c in range(16, 56) for p in range(1, 95)][:-5]
])
ALPHA = list(string.ascii_lowercase + string.ascii_uppercase)
NUMERIC = list(string.digits)
PUNCTUATION = [',', '，', '.', '。', '"', "'", "“", "”", '‘', '’', '~', '-', '_', '@', '!', '#', '￥', '$', '%', '……', '^', '&', '*', '(', ')', '[', ']', '{', '}', "|", '<', '>', '?', ':', ';', '`', '=', '+', '/', '\\', '【', '】', '《', '》']
OPERATIONAL_SYMBOL = ['(', ')', '+', '-', '×', '÷', '=', '?']


CATEGORIES_MAP = {
    'Chinese2W': BLANK_TOKEN + CHINESE_2W,
    'Chinese3755': BLANK_TOKEN + CHINESE_3755,
    'Numeric': BLANK_TOKEN + NUMERIC,
    'Alphabet': BLANK_TOKEN + ALPHA,
    'AlphaNumeric': BLANK_TOKEN + NUMERIC + ALPHA,
    'AlphaNumericLower': BLANK_TOKEN + NUMERIC + ALPHA[:len(ALPHA)//2],
    'NumericOperators': BLANK_TOKEN + NUMERIC + OPERATIONAL_SYMBOL,
    'AlphaNumericOperators': BLANK_TOKEN + NUMERIC + ALPHA + OPERATIONAL_SYMBOL,
    'AlphaPunctuation': BLANK_TOKEN + ALPHA + PUNCTUATION,
    'OCR': BLANK_TOKEN + NUMERIC + ALPHA + CHINESE_2W + PUNCTUATION,
    'DefaultObject': OBJECT
}