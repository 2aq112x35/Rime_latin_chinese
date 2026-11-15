--[[
pinyin_tone —— 带声调汉语拼音输入方案的翻译器
（由 pinyin_tone.schema.yaml 通过 lua_translator@pinyin_tone 引用）

输入：拼音音节 + 声调键（写在音节末尾）
    q = 一声（阴平）   w = 二声（阳平）   e = 三声（上声）   r = 四声（去声）
    不加声调键 = 轻声 / 不标调
    ü 用 v 打（lvr = lǜ，nvee = nǚ）

输出：带声调符号的拼音；多音节之间用空格分隔
    maq      -> mā            maw -> má
    mae      -> mǎ            mar -> mà
    nie'haoe -> nǐ hǎo        zhongq -> zhōng
]]

local data = require("pinyin_tone_data")

local MAXLEN = 6          -- 最长音节 zhuang / chuang / shuang = 6 字母
local TONE_KEY = { q = 1, w = 2, e = 3, r = 4 }
local TONE_NAME = { [1] = "阴平", [2] = "阳平", [3] = "上声", [4] = "去声", [5] = "轻声" }

-- 拼式里 v 代表 ü，所以这里也给 v 准备一套带调字符
local MARKS = {
  a = { "ā", "á", "ǎ", "à" },
  o = { "ō", "ó", "ǒ", "ò" },
  e = { "ē", "é", "ě", "è" },
  i = { "ī", "í", "ǐ", "ì" },
  u = { "ū", "ú", "ǔ", "ù" },
  v = { "ǖ", "ǘ", "ǚ", "ǜ" },
}

-- 拼式 -> 书写形式（v 写成 ü）
local function display(base)
  return (base:gsub("v", "ü"))
end

-- 标调。标调位置遵循《汉语拼音方案》：
-- 有 a 标 a，没 a 有 o 标 o，没 o 有 e 标 e；iu 标 u，ui 标 i；其余标唯一元音。
local function with_tone(base, tone)
  local s = base
  if not tone or tone == 5 then
    return display(s)
  end
  local pos = s:find("a", 1, true) or s:find("o", 1, true) or s:find("e", 1, true)
  if not pos then
    local iu_end = select(2, s:find("iu", 1, true))
    if iu_end then
      pos = iu_end                                  -- liu -> liù
    else
      local ui_start = s:find("ui", 1, true)
      if ui_start then
        pos = ui_start + 1                          -- gui -> guì（标在 i 上）
      else
        pos = s:find("i", 1, true) or s:find("u", 1, true) or s:find("v", 1, true)
      end
    end
  end
  if not pos then return display(s) end
  local marks = MARKS[s:sub(pos, pos)]
  if not marks then return display(s) end
  return display(s:sub(1, pos - 1) .. marks[tone] .. s:sub(pos + 1))
end

-- 这个「音节 + 声调」在普通话里是否存在
local function is_valid(base, tone)
  local valid = data[base]
  if not valid then return false end
  return valid:find(tostring(tone or 5), 1, true) ~= nil
end

-- 把一段连续字母切成音节。
-- 打分顺序：①拼不通的字符越少越好 ②别把本该属于下一个音节的字母当成声调键
--          ③尽量读出声调键 ④音节数越少越好
-- 只要还剩拼不通的字符（比如刚打了半个音节 "zh"），就整块不给出候选。
local function segment(chunk)
  local n = #chunk
  local memo = {}
  memo[n + 1] = { lit = 0, pen = 0, toned = 0, syl = 0, steps = {} }

  -- 位置 p 上能不能起一个长度 >= 2 的真音节（用来判断声调键是不是"抢"了下一个音节的首字母）
  local starts_long = {}
  for p = 1, n do
    starts_long[p] = false
    for len = math.min(MAXLEN, n - p + 1), 2, -1 do
      if data[chunk:sub(p, p + len - 1)] then
        starts_long[p] = true
        break
      end
    end
  end

  local function better(a, b)
    if not b then return true end
    if a.lit ~= b.lit then return a.lit < b.lit end
    if a.pen ~= b.pen then return a.pen < b.pen end
    if a.toned ~= b.toned then return a.toned > b.toned end
    return a.syl < b.syl
  end

  local function link(step, rest, sc)
    local steps = { step }
    for _, s in ipairs(rest.steps) do steps[#steps + 1] = s end
    return { lit = sc.lit, pen = sc.pen, toned = sc.toned, syl = sc.syl, steps = steps }
  end

  for i = n, 1, -1 do
    local best = nil
    for len = math.min(MAXLEN, n - i + 1), 1, -1 do
      local base = chunk:sub(i, i + len - 1)
      if data[base] then
        -- ① 带声调：音节后面紧跟声调键
        local tone = TONE_KEY[chunk:sub(i + len, i + len)]
        if tone then
          local rest = memo[i + len + 1]
          if rest then
            local sc = {
              lit = rest.lit,
              pen = rest.pen + (starts_long[i + len] and 1 or 0),
              toned = rest.toned + 1,
              syl = rest.syl + 1,
            }
            if better(sc, best) then
              best = link({ base = base, tone = tone, raw = base .. chunk:sub(i + len, i + len) }, rest, sc)
            end
          end
        end
        -- ② 不带声调
        local rest = memo[i + len]
        if rest then
          local sc = { lit = rest.lit, pen = rest.pen, toned = rest.toned, syl = rest.syl + 1 }
          if better(sc, best) then
            best = link({ base = base, tone = nil, raw = base }, rest, sc)
          end
        end
      end
    end
    -- ③ 认不出来就记一个"拼不通"，整块最终会被丢弃
    local rest1 = memo[i + 1]
    if rest1 then
      local sc = { lit = rest1.lit + 1, pen = rest1.pen, toned = rest1.toned, syl = rest1.syl + 1 }
      if better(sc, best) then
        best = link({ literal = chunk:sub(i, i), raw = chunk:sub(i, i) }, rest1, sc)
      end
    end
    memo[i] = best
  end

  local result = memo[1]
  if not result or result.lit > 0 then return nil end
  return result.steps
end

-- 按空格、单引号切分成一个个音节块
local function split_chunks(input)
  local chunks = {}
  for piece in input:gmatch("[^%s']+") do
    chunks[#chunks + 1] = piece
  end
  return chunks
end

local function translator(input, seg)
  if input == "" then return end
  local chunks = split_chunks(input)
  if #chunks == 0 then return end

  local sylls = {}
  for _, chunk in ipairs(chunks) do
    local steps = segment(chunk)
    -- 只要有一段拼不通（比如刚打出半个音节）就整体不出候选，免得给出半截结果
    if not steps then return end
    for _, st in ipairs(steps) do sylls[#sylls + 1] = st end
  end
  if #sylls == 0 then return end

  local toned_parts, num_parts, plain_parts = {}, {}, {}
  local bad = {}
  local toned_count = 0
  for _, s in ipairs(sylls) do
    toned_parts[#toned_parts + 1] = with_tone(s.base, s.tone)
    num_parts[#num_parts + 1] = display(s.base) .. (s.tone and tostring(s.tone) or "")
    plain_parts[#plain_parts + 1] = display(s.base)
    if s.tone then
      toned_count = toned_count + 1
      if not is_valid(s.base, s.tone) then bad[#bad + 1] = s.raw end
    end
  end

  local main = table.concat(toned_parts, " ")
  local numbered = table.concat(num_parts, " ")
  local plain = table.concat(plain_parts, " ")

  -- 主候选：带声调符号
  local comment = numbered
  if #bad > 0 then
    comment = numbered .. "  ⚠普通话无此读音: " .. table.concat(bad, " ")
  end
  yield(Candidate("pinyin_tone", seg.start, seg._end, main, comment))

  -- 数字调候选（录入、查表时好用）
  if numbered ~= main then
    yield(Candidate("pinyin_tone", seg.start, seg._end, numbered, "数字调"))
  end

  -- 只打了一个音节、又没打声调键：把四个声调都列出来供挑
  if #sylls == 1 and toned_count == 0 then
    local base = sylls[1].base
    for tone = 1, 4 do
      if is_valid(base, tone) then
        yield(Candidate("pinyin_tone", seg.start, seg._end, with_tone(base, tone),
          TONE_NAME[tone] .. " " .. display(base) .. tone))
      end
    end
  end

  -- 不标调候选
  if toned_count > 0 and plain ~= main then
    yield(Candidate("pinyin_tone", seg.start, seg._end, plain, "不标调"))
  end
end

return translator
