#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
从 terra_pinyin.dict.yaml（地球拼音，带调号码表）里提取真实存在的
「音节 + 声调」组合，生成 lua 方案用的数据文件 lua/pinyin_tone_data.lua

顺带做几处统计/自检，方便看数据有没有漏。
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pinyin_tone_ref as ref  # noqa: E402

ROOT = os.path.dirname(HERE)
SRC = r"C:\Program Files\Rime\weasel-0.17.4\data\terra_pinyin.dict.yaml"
OUT = os.path.join(ROOT, "lua", "pinyin_tone_data.lua")

CODE_RE = re.compile(r"^([a-z]+)([1-5])$")


def parse_terra(path=SRC):
    tries = {}
    in_body = False
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not in_body:
                if line.strip() == "...":
                    in_body = True
                continue
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            code = parts[1].strip()
            if len(parts) >= 3 and parts[2].strip():
                try:
                    w = int(float(parts[2]))
                except ValueError:
                    w = 1
            else:
                w = 1
            for piece in code.split():
                m = CODE_RE.match(piece)
                if not m:
                    continue
                base, tone = m.group(1), m.group(2)
                tries.setdefault(base, set()).add(int(tone))
    return tries


def main():
    tries = parse_terra()
    bases = sorted(tries)
    print("基础音节数:", len(bases))
    print("音节+声调组合数:", sum(len(v) for v in tries.values()))
    print("含 v(ü) 的音节:", [b for b in bases if "v" in b][:30])
    print("以 j/q/x/y 开头含 v 的:", [b for b in bases if "v" in b and b[0] in "jqxy"])
    for special in ("a", "e", "o", "er", "m", "n", "ng", "lo", "yo", "ei"):
        print(f"  {special}: {sorted(tries.get(special, []))}")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("-- 由 tools/gen_data.py 从 terra_pinyin 词典自动生成，请勿手改\n")
        f.write("-- 格式: [基础音节(拼式, ü 写作 v)] = \"可用的声调数字\"\n")
        f.write("local data = {\n")
        for b in bases:
            f.write('  ["%s"] = "%s",\n' % (b, "".join(str(t) for t in sorted(tries[b]))))
        f.write("}\nreturn data\n")
    print("已写出:", OUT, os.path.getsize(OUT), "字节")

    # 附带生成一张人看的对照表：输入码 -> 带调写法
    csv_out = os.path.join(ROOT, "docs", "音节声调对照表.csv")
    os.makedirs(os.path.dirname(csv_out), exist_ok=True)
    with open(csv_out, "w", encoding="utf-8-sig", newline="") as f:
        f.write("输入码,音节,声调,带调写法,数字调,普通话有此读音\n")
        for b in bases:
            for tone in (1, 2, 3, 4):
                key = ref.TONE_KEY[str(tone)]
                code = "%s%s" % (b, key)
                f.write('"%s","%s","%s(%d)","%s","%s","%s"\n' % (
                    code, ref.display(b), ref.TONE_NAME[str(tone)], tone,
                    ref.toned(b, tone), ref.numbered(b, tone),
                    "是" if tone in tries[b] else "否"))
            f.write('"%s","%s","轻声","%s","%s","%s"\n' % (
                b, ref.display(b), ref.display(b), ref.display(b),
                "是" if 5 in tries[b] else "否"))
    print("已写出:", csv_out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
