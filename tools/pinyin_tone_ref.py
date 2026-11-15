#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
带调拼音的 Python 参考实现：标调规则、拼式转换。
作用有二：
  1. gen_data.py 生成对照表时用它算出「标准写法」
  2. verify_all.py 拿它跟 Rime 里的 lua 实现逐条对账
"""

# 《汉语拼音方案》标调元音
MARK_TABLE = {
    "a": {"1": "ā", "2": "á", "3": "ǎ", "4": "à"},
    "o": {"1": "ō", "2": "ó", "3": "ǒ", "4": "ò"},
    "e": {"1": "ē", "2": "é", "3": "ě", "4": "è"},
    "i": {"1": "ī", "2": "í", "3": "ǐ", "4": "ì"},
    "u": {"1": "ū", "2": "ú", "3": "ǔ", "4": "ù"},
    "v": {"1": "ǖ", "2": "ǘ", "3": "ǚ", "4": "ǜ"},  # 拼式里的 ü
}

TONE_KEY = {"1": "q", "2": "w", "3": "e", "4": "r"}
TONE_NAME = {"1": "阴平", "2": "阳平", "3": "上声", "4": "去声", "5": "轻声"}


def display(base):
    """拼式 -> 书写形式"""
    return base.replace("v", "ü")


def tone_pos(base):
    """返回该标调的元音在拼式里的下标；找不到返回 None"""
    for v in ("a", "o", "e"):
        i = base.find(v)
        if i >= 0:
            return i
    i = base.find("iu")
    if i >= 0:
        return i + 1          # liu -> liù
    i = base.find("ui")
    if i >= 0:
        return i + 1          # gui -> guì
    for v in ("i", "u", "v"):
        i = base.find(v)
        if i >= 0:
            return i
    return None


def toned(base, tone):
    """把拼式 base 标上 tone（1-4；None/5 = 轻声，不标）"""
    if tone in (None, "", 5, "5"):
        return display(base)
    key = str(tone)
    pos = tone_pos(base)
    if pos is None:
        return display(base)
    ch = base[pos]
    if ch not in MARK_TABLE:
        return display(base)
    return display(base[:pos] + MARK_TABLE[ch][key] + base[pos + 1:])


def numbered(base, tone):
    """数字调写法"""
    return display(base) + ("" if tone in (None, "", 5) else str(tone))


def input_code(base, tone):
    """要打哪些键"""
    return base + (TONE_KEY.get(str(tone), "") if tone not in (None, "") else "")
