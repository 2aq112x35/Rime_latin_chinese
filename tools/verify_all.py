#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
全量校验：421 个音节 × 4 个声调（q/w/e/r）逐个打进 Rime，
跟 Python 参考实现算出来的标准写法逐条比对。
    python tools/verify_all.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pinyin_tone_ref as ref  # noqa: E402
import rime_test as rt  # noqa: E402
from gen_data import parse_terra  # noqa: E402

SCHEMA = "pinyin_tone"
USER = os.path.join(os.path.dirname(HERE), ".test")


def main():
    tries = parse_terra()
    lib = rt.load()
    rt.sync_sources(USER, SCHEMA)
    rt.start(lib, rt.DEFAULT_SHARED, USER)
    session = lib.RimeCreateSession()
    lib.RimeSelectSchema(session, SCHEMA.encode())

    total = bad = 0
    failures = []
    for base in sorted(tries):
        for tone in (1, 2, 3, 4):
            code = ref.input_code(base, tone)
            expect = ref.toned(base, tone)
            lib.RimeClearComposition(session)
            for ch in code:
                lib.RimeProcessKey(session, ord(ch), 0)
            _, cands, _, _ = rt.snapshot(lib, session)
            got = cands[0][0] if cands else None
            total += 1
            if got != expect:
                bad += 1
                failures.append((code, expect, got, [t for t, _ in cands[:5]]))

    lib.RimeDestroySession(session)
    lib.RimeFinalize()

    print(f"共测 {total} 条，不一致 {bad} 条")
    for code, expect, got, listing in failures[:40]:
        print(f"  {code:10} 期望 {expect:8} 实得 {got!r:10} 候选: {' | '.join(listing)}")
    if len(failures) > 40:
        print(f"  …… 还有 {len(failures) - 40} 条")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
