#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
无界面 Rime 测试台：用 ctypes 直接调用 rime.dll 的 C API，
在临时 user 目录部署某个方案，模拟按键并打印 preedit / 候选 / 上屏结果，
用来验证 schema + dict + lua 的真实行为，不需要开输入法。

用法:
    python rime_test.py maq maw mae mar
    python rime_test.py --schema=pinyin_tone "niq haoe"
                （空格 = 音节分隔符，按原样逐键喂给 Rime）
选项:
    --schema=ID    方案 ID，默认 luna_pinyin
    --shared=DIR   共享数据目录，默认小狼毫自带 data
    --user=DIR     用户目录，默认 <项目>/.test
    --clean        先删掉 build 目录强制重新部署
    --select=N     测试串结束后用选第 N 个候选上屏（默认 1）
"""

import ctypes
import os
import shutil
import sys
from ctypes import POINTER, Structure, byref, c_char_p, c_int, c_void_p

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SHARED = r"C:\Program Files\Rime\weasel-0.17.4\data"
DEFAULT_DLL = r"C:\Program Files\Rime\weasel-0.17.4\rime.dll"


class RimeTraits(Structure):
    _fields_ = [
        ("data_size", c_int),
        ("shared_data_dir", c_char_p),
        ("user_data_dir", c_char_p),
        ("distribution_name", c_char_p),
        ("distribution_code_name", c_char_p),
        ("distribution_version", c_char_p),
        ("app_name", c_char_p),
        ("modules", c_void_p),
        ("min_log_level", c_int),
        ("log_dir", c_char_p),
        ("prebuilt_data_dir", c_char_p),
        ("staging_dir", c_char_p),
    ]


class RimeComposition(Structure):
    _fields_ = [
        ("length", c_int),
        ("cursor_pos", c_int),
        ("sel_start", c_int),
        ("sel_end", c_int),
        ("preedit", c_char_p),
    ]


class RimeCandidate(Structure):
    _fields_ = [
        ("text", c_char_p),
        ("comment", c_char_p),
        ("reserved", c_void_p),
    ]


class RimeMenu(Structure):
    _fields_ = [
        ("page_size", c_int),
        ("page_no", c_int),
        ("is_last_page", c_int),
        ("highlighted_candidate_index", c_int),
        ("num_candidates", c_int),
        ("candidates", POINTER(RimeCandidate)),
        ("select_keys", c_char_p),
    ]


class RimeContext(Structure):
    _fields_ = [
        ("data_size", c_int),
        ("composition", RimeComposition),
        ("menu", RimeMenu),
        ("commit_text_preview", c_char_p),
        ("select_labels", POINTER(c_char_p)),
    ]


class RimeCommit(Structure):
    _fields_ = [("data_size", c_int), ("text", c_char_p)]


def struct_init(obj):
    obj.data_size = ctypes.sizeof(obj) - ctypes.sizeof(c_int)


def load(dll_path=DEFAULT_DLL):
    lib = ctypes.CDLL(dll_path)
    lib.RimeInitialize.argtypes = [POINTER(RimeTraits)]
    lib.RimeFinalize.argtypes = []
    lib.RimeStartMaintenance.argtypes = [c_int]
    lib.RimeJoinMaintenanceThread.argtypes = []
    lib.RimeCreateSession.restype = c_void_p
    lib.RimeDestroySession.argtypes = [c_void_p]
    lib.RimeProcessKey.argtypes = [c_void_p, c_int, c_int]
    lib.RimeProcessKey.restype = c_int
    lib.RimeGetContext.argtypes = [c_void_p, POINTER(RimeContext)]
    lib.RimeGetContext.restype = c_int
    lib.RimeFreeContext.argtypes = [POINTER(RimeContext)]
    lib.RimeGetCommit.argtypes = [c_void_p, POINTER(RimeCommit)]
    lib.RimeGetCommit.restype = c_int
    lib.RimeFreeCommit.argtypes = [POINTER(RimeCommit)]
    lib.RimeSelectSchema.argtypes = [c_void_p, c_char_p]
    lib.RimeSelectSchema.restype = c_int
    lib.RimeGetCurrentSchema.argtypes = [c_void_p, c_char_p, ctypes.c_size_t]
    lib.RimeGetCurrentSchema.restype = c_int
    lib.RimeSetOption.argtypes = [c_void_p, c_char_p, c_int]
    lib.RimeSimulateKeySequence.argtypes = [c_void_p, c_char_p]
    lib.RimeSimulateKeySequence.restype = c_int
    lib.RimeCommitComposition.argtypes = [c_void_p]
    lib.RimeCommitComposition.restype = c_int
    lib.RimeClearComposition.argtypes = [c_void_p]
    lib.RimeSelectCandidateOnCurrentPage.argtypes = [c_void_p, ctypes.c_size_t]
    lib.RimeSelectCandidateOnCurrentPage.restype = c_int
    return lib


def start(lib, shared, user, log_level=1, maintenance=True):
    os.makedirs(user, exist_ok=True)
    t = RimeTraits()
    struct_init(t)
    t.shared_data_dir = shared.encode()
    t.user_data_dir = user.encode()
    t.distribution_name = b"Rime"
    t.distribution_code_name = b"test"
    t.distribution_version = b"1.0"
    t.app_name = b"rime.test"
    t.min_log_level = log_level
    t.log_dir = user.encode()
    lib.RimeInitialize(byref(t))
    if maintenance:
        lib.RimeStartMaintenance(1)
        lib.RimeJoinMaintenanceThread()


def snapshot(lib, session):
    ctx = RimeContext()
    struct_init(ctx)
    if not lib.RimeGetContext(session, byref(ctx)):
        return "", [], "", ""
    preedit = ctx.composition.preedit or b""
    preedit = preedit.decode("utf-8", "replace")
    preview = (ctx.commit_text_preview or b"").decode("utf-8", "replace")
    cands = []
    for i in range(ctx.menu.num_candidates):
        c = ctx.menu.candidates[i]
        cands.append(((c.text or b"").decode("utf-8", "replace"),
                      (c.comment or b"").decode("utf-8", "replace")))
    lib.RimeFreeContext(byref(ctx))
    return preedit, cands, preview, ""


def commit_text(lib, session):
    c = RimeCommit()
    struct_init(c)
    if lib.RimeGetCommit(session, byref(c)):
        text = (c.text or b"").decode("utf-8")
        lib.RimeFreeCommit(byref(c))
        return text
    return None


def show(session, lib, label=""):
    preedit, cands, preview, _ = snapshot(lib, session)
    body = " | ".join(f"{i + 1}.{t}" + (f"〔{m}〕" if m else "") for i, (t, m) in enumerate(cands[:12]))
    print(f"{label}preedit=[{preedit}] 预览=[{preview}] 候选: {body}")
    return cands


def sync_sources(user, schema):
    """把项目里的方案文件（*.yaml + lua/）同步到测试用户目录，
    并写一份 default.custom.yaml 把待测方案列进 schema_list（否则不会编译进 build）"""
    root = os.path.dirname(HERE)
    os.makedirs(user, exist_ok=True)
    for name in os.listdir(root):
        if name.endswith(".yaml") and not name.startswith("default") and not name.startswith("weasel"):
            shutil.copy2(os.path.join(root, name), os.path.join(user, name))
        elif name == "rime.lua":
            shutil.copy2(os.path.join(root, name), os.path.join(user, name))
    src_lua = os.path.join(root, "lua")
    if os.path.isdir(src_lua):
        dst_lua = os.path.join(user, "lua")
        os.makedirs(dst_lua, exist_ok=True)
        for name in os.listdir(src_lua):
            shutil.copy2(os.path.join(src_lua, name), os.path.join(dst_lua, name))
    with open(os.path.join(user, "default.custom.yaml"), "w", encoding="utf-8") as f:
        f.write("patch:\n  schema_list:\n    - schema: %s\n    - schema: luna_pinyin\n" % schema)


def main(argv):
    pos = [a for a in argv if not a.startswith("--")]
    schema, shared, dll = "luna_pinyin", DEFAULT_SHARED, DEFAULT_DLL
    user = os.path.join(os.path.dirname(HERE), ".test")
    clean, pick, no_sync, no_maint = False, 1, False, False
    for a in argv:
        if a.startswith("--schema="):
            schema = a.split("=", 1)[1]
        elif a.startswith("--shared="):
            shared = a.split("=", 1)[1]
        elif a.startswith("--user="):
            user = a.split("=", 1)[1]
        elif a.startswith("--dll="):
            dll = a.split("=", 1)[1]
        elif a.startswith("--select="):
            pick = int(a.split("=", 1)[1])
        elif a == "--clean":
            clean = True
        elif a == "--no-sync":
            no_sync = True
        elif a == "--no-maint":
            no_maint = True
    if clean:
        shutil.rmtree(os.path.join(user, "build"), ignore_errors=True)
    if not no_sync:
        sync_sources(user, schema)

    lib = load(dll)
    start(lib, shared, user, maintenance=not no_maint)
    session = lib.RimeCreateSession()
    print("session", session, "schema", schema)
    lib.RimeSelectSchema(session, schema.encode())
    buf = ctypes.create_string_buffer(256)
    if lib.RimeGetCurrentSchema(session, buf, 256):
        print("当前方案:", buf.value.decode())

    for word in pos:
        print(f"\n=== {word!r} ===")
        lib.RimeClearComposition(session)
        for i, ch in enumerate(word):
            ok = lib.RimeProcessKey(session, ord(ch), 0)
            preedit, cands, preview, _ = snapshot(lib, session)
            print(f"  [{i:02d}] 键 {ch!r} {'√' if ok else '×'}  preedit={preedit!r}")
        show(session, lib, "  最终 ")
        if pick:
            lib.RimeSelectCandidateOnCurrentPage(session, pick - 1)
            print("  上屏:", repr(commit_text(lib, session)))

    lib.RimeDestroySession(session)
    lib.RimeFinalize()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
