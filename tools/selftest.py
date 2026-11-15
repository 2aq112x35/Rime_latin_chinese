#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
带调拼音方案的回归测试：把「输入 -> 首候选」的期望值写死，逐条比对。
    python tools/selftest.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rime_test as rt  # noqa: E402

SCHEMA = "pinyin_tone"
USER = os.path.join(os.path.dirname(HERE), ".test")

# (输入, 首候选期望值)  —— 期望值是标准汉语拼音写法
CASES = [
    # 四声基本盘
    ("maq", "mā"), ("maw", "má"), ("mae", "mǎ"), ("mar", "mà"),
    ("niq", "nī"), ("niw", "ní"), ("nie", "nǐ"), ("nir", "nì"),
    ("haoq", "hāo"), ("haow", "háo"), ("haoe", "hǎo"), ("haor", "hào"),
    ("zhongq", "zhōng"), ("zhongr", "zhòng"),
    ("shiq", "shī"), ("shiw", "shí"), ("shie", "shǐ"), ("shir", "shì"),
    ("zhiq", "zhī"), ("zhie", "zhǐ"), ("zhir", "zhì"), ("ziq", "zī"),
    # 零声母 / 单元音
    ("aq", "ā"), ("aw", "á"), ("ae", "ǎ"), ("ar", "à"),
    ("ow", "ó"), ("eq", "ē"), ("erq", "ēr"), ("erw", "ér"), ("err", "èr"),
    ("aiq", "āi"), ("air", "ài"), ("ouq", "ōu"), ("eiq", "ēi"),
    # 复韵母标调位置
    ("liuw", "liú"), ("liur", "liù"), ("guiq", "guī"), ("guie", "guǐ"), ("guir", "guì"),
    ("huiq", "huī"), ("duir", "duì"), ("jiuq", "jiū"),
    # ü / v 规则
    ("lvr", "lǜ"), ("lve", "lǚ"), ("lver", "lüè"),
    ("nve", "nǚ"), ("nver", "nüè"),
    ("juq", "jū"), ("juew", "jué"), ("quer", "què"), ("xuew", "xué"), ("yuer", "yuè"),
    ("yue", "yǔ"),
    # 常用词（多音节，用 ' 分隔最稳妥）
    ("nie'haoe", "nǐ hǎo"),
    ("hanr'yue", "hàn yǔ"),
    ("zhongq'guow", "zhōng guó"),
    ("beiq'jingq", "bēi jīng"),
    # 不打声调键
    ("ma", "ma"),
    ("nihao", "ni hao"),
    # 儿化与特殊情况
    ("huar", "huà"),
    ("lv", "lü"),
]


def main():
    lib = rt.load()
    rt.sync_sources(USER, SCHEMA)
    rt.start(lib, rt.DEFAULT_SHARED, USER)
    session = lib.RimeCreateSession()
    lib.RimeSelectSchema(session, SCHEMA.encode())

    ok = fail = skip = 0
    for inp, exp in CASES:
        if exp is None:
            skip += 1
            continue
        lib.RimeClearComposition(session)
        for ch in inp:
            lib.RimeProcessKey(session, ord(ch), 0)
        _, cands, _, _ = rt.snapshot(lib, session)
        got = cands[0][0] if cands else None
        if got == exp:
            ok += 1
            print(f"  通过 {inp!r:18} -> {got}")
        else:
            fail += 1
            listing = " | ".join(t for t, _ in cands[:6])
            print(f"  失败 {inp!r:18} 期望 {exp!r} 实得 {got!r}   候选: {listing}")
    lib.RimeDestroySession(session)
    lib.RimeFinalize()
    print(f"\n通过 {ok} / 失败 {fail} / 跳过 {skip}")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
