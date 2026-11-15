-- rime.lua —— librime-lua 的模块入口，必须放在【用户目录根】下
-- （与本方案的 *.schema.yaml 同级；lua 模块文件放在 lua/ 目录里）
-- 方案文件用 lua_translator@pinyin_tone 引用下面的全局名。
-- 若你原本已有 rime.lua，只需把最后一行追加进去即可。

pinyin_tone = require("pinyin_tone")
