# 带调拼音（pinyin_tone）—— Rime 输入方案

输入拼音，音节末尾按一下声调键，直接上屏**带声调符号的汉语拼音**。

```
maq  →  mā        maw  →  má        mae  →  mǎ        mar  →  mà
nie'haoe  →  nǐ hǎo         hanr'yue  →  hàn yǔ
lvr  →  lǜ                  zhongq  →  zhōng
```

## 声调键

| 键 | 声调 | 例 |
|---|---|---|
| `q` | 一声（阴平） | `maq` → mā |
| `w` | 二声（阳平） | `maw` → má |
| `e` | 三声（上声） | `mae` → mǎ |
| `r` | 四声（去声） | `mar` → mà |
| 不打 | 轻声 / 不标调 | `ma` → ma |

ü 用 `v` 打：`lvr` → lǜ，`nve` → nǚ，`lver` → lüè。

## 用法

- **单音节**：`maq` → 候选第一项就是 mā，空格上屏。
- **多音节**：用单引号 `'` 分隔（空格是上屏键，不能当分隔符用）：
  `nie'haoe` → nǐ hǎo，一次性上屏，中间的空格已经带好。
  不加分隔符也能切（`niehaoe` → nǐ hǎo），但遇到 `guwen` 这类会有歧义，见下文。
- **候选菜单**：
  1. 带声调写法（注释里给数字调，如 `ni3 hao3`）
  2. 数字调写法（`ni3 hao3`，录入数据、查表时方便）
  3. 不标调写法（`ni hao`）
- **只打音节不打声调键**（如 `ma`）：第一项是不标调的 ma，后面把 mā / má / mǎ / mà 都列出来，按数字键挑。
- **普通话里没有的读音**（如 `fī`、`nüé`）：照样给候选，但注释里带 `⚠普通话无此读音` 提示。

## 安装

### 一键安装（推荐）

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

脚本会：把方案文件复制到 `%APPDATA%\Rime`、备份并改写 `default.custom.yaml` 的 `schema_list`、调用 WeaselDeployer 重新部署。

### 手工安装

1. 把下面这些复制到 `%APPDATA%\Rime`（小狼毫用户目录）：

```
%APPDATA%\Rime\
├─ pinyin_tone.schema.yaml     ← 方案定义
├─ rime.lua                    ← lua 模块入口（必须放在用户目录根，不是 lua 子目录）
└─ lua\
   ├─ pinyin_tone.lua          ← 翻译器：切音节、加声调符号
   └─ pinyin_tone_data.lua     ← 音节-声调数据（自动生成，勿手改）
```

2. 在 `default.custom.yaml` 的 `patch: schema_list:` 下加一行：

```yaml
patch:
  schema_list:
    - {schema: luna_pinyin}
    - {schema: pinyin_tone}     # ← 加这行
```

3. 右键任务栏小狼毫图标 →「重新部署」（或命令行执行 `"C:\Program Files\Rime\weasel-0.17.4\WeaselDeployer.exe" /deploy`）。

4. 用 Ctrl+` 或方案选单切到「带调拼音」。（F4 也可以，看你自己的按键绑定）

## 目录结构

```
hanyulading\
├─ pinyin_tone.schema.yaml      方案
├─ rime.lua                     lua 模块入口
├─ lua\
│  ├─ pinyin_tone.lua           翻译器（切分 + 标调）
│  └─ pinyin_tone_data.lua      数据（gen_data.py 生成）
├─ docs\
│  └─ 音节声调对照表.csv         421 音节 × 4 声的全表（含是否为普通话实有读音）
├─ tools\
│  ├─ gen_data.py               从 terra_pinyin 词典提取音节声调、生成数据与对照表
│  ├─ pinyin_tone_ref.py        标调规则的 Python 参考实现
│  ├─ rime_test.py              无界面按键测试台（直接调 rime.dll 的 C API）
│  ├─ selftest.py               62 条手写期望值的回归测试
│  ├─ verify_all.py             1684 条全量对账（Rime 实跑 vs Python 参考）
│  └─ 以上脚本会在 .test/ 里建一个临时 user 目录，不动你真实的 Rime 配置
├─ install.ps1                  安装脚本
└─ README.md
```

## 它是怎么做的

- 音节表和「音节+声调」组合不是瞎编的，而是从 Rime 自带的 **terra_pinyin（地球拼音）词典**里提取的：凡是词典里有汉字读这个音的，才算普通话有这个读音。结果是 **421 个音节、1695 个音节-声调组合**。
- 标调位置按《汉语拼音方案》：有 a 标 a，没 a 有 o 标 o，没 o 有 e 标 e；`iu` 标在 u 上（liù），`ui` 标在 i 上（guì）；剩下只有一个元音就标它。
- 切分用动态规划，打分优先级：**拼不通的字符最少 → 不抢下一个音节的首字母 → 尽量读出声调键 → 音节数最少**。

## 已知限制（都是声调键占用了普通字母导致的老问题）

1. **多音节请用 `'` 分隔**。空格在 Rime 里是上屏键，不能当音节分隔符。
2. **连续输入有歧义**。`guwen` 会被读成 `gú en` 还是 `gu wén`？方案里的规则是「不抢下一个音节的首字母」，所以给 `gu wen`；`qiangq` 这类则正常读成 `qiāng`。真要精确就加 `'`：`guq'wenw` → `gū wén`。
3. **儿化的 `r` 和四声键冲突**：`huar` 会被当成 `huà`。儿化目前请写成 `hua'er` 那种形式（这个方案里 `hua'er` 的 `er` 是独立音节，可以打 `hua'erw` 之类），或者干脆不打声调。
4. 输入栏（preedit）里显示的仍是 `maq` 这种原始字母，带调结果在候选和「预览」里；上屏后才是 mā。
5. 需要 **librime-lua**：小狼毫 0.15+、fcitx5-rime、同文等主流发行版都自带；纯 librime 裸编译的环境需要自己装 lua 插件。
6. 这个方案只输出拼音，不输出汉字。要打汉字请切回朙月拼音。

## 维护

```powershell
# 重新生成音节数据（换了 terra_pinyin 词典或想改判定规则时）
python tools\gen_data.py

# 回归测试（62 条手写用例）
python tools\selftest.py

# 全量对账（421 音节 × 4 声，逐条打进 Rime 比对）
python tools\verify_all.py

# 手动按键试验，看每一步的候选
python tools\rime_test.py --schema=pinyin_tone maq "nie'haoe"
```

测试台的原理：用 ctypes 直接调用 `rime.dll` 的 C API，在 `%项目%\.test` 这个临时用户目录里部署方案，模拟按键、读候选，不需要打开输入法面板，也不碰你真实的 Rime 配置。

## 想改声调键？

改两个地方的一处即可（数据不用动）：

- `lua/pinyin_tone.lua` 里的 `TONE_KEY = { q = 1, w = 2, e = 3, r = 4 }`
- 若还想要数字键，需同时在 `pinyin_tone.schema.yaml` 的 `speller/alphabet` 里加上 `1234`，但那样数字就不能直接打出来了。
