# A股市场情绪指数深度分析工具

> 触发词（高优先级）：A股情绪、今日A股情绪、市场情绪怎么样、A股现在热不热、A股买点、A股卖点、刷新数据、更新数据
>
> 触发词（中优先级）：沪深300情绪、沪深300今日情绪、ETF情绪、情绪指数、CSI 300 sentiment
>
> 触发词（低优先级）：沪深300现在怎么样、当前市场情绪

---

## 何时使用

当用户询问 A股整体市场情绪、热点方向、资金流向、市场热度、买点卖点时，使用本 skill。

> 📖 各因子的历史验证、通识误区和配合使用，见 [references/factor_definition.md](./references/factor_definition.md)

---

## 分析流程

### 第零步：判断是否需要强制刷新

**如果用户明确说「刷新数据」「更新数据」「重新下载」「获取最新数据」**，直接跳过缓存检查，立即执行第二步从 GitHub 重新下载最新 Excel（覆盖本地文件），再生成新缓存。这是**强制刷新**，不走缓存。

**否则**，按正常流程处理（第一步 → 第二步或第三步）。

### 第一步：检查本地缓存

先用 Python 检查本地是否有当天的缓存：

```python
import os, json
from datetime import date

cache_dir = "assets"
today = date.today().isoformat()

cache_file = os.path.join(cache_dir, "sentiment_cache.json")
excel_file = os.path.join(cache_dir, "df_sentiment.xlsx")
```

**如果同时满足以下条件，直接读取本地缓存，跳过下载：**
1. `sentiment_cache.json` 存在
2. `df_sentiment.xlsx` 存在
3. Excel 文件的修改时间 >= 今天 00:00（即当天下载的）

```python
import datetime
if os.path.exists(cache_file) and os.path.exists(excel_file):
    mtime = datetime.datetime.fromtimestamp(os.path.getmtime(excel_file))
    if mtime.date() >= today:
        with open(cache_file) as f:
            cache = json.load(f)
        print(f"使用本地缓存，日期: {mtime.date()}")
```

---

### 第二步：从 GitHub 下载最新 Excel（无缓存时）

```python
import urllib.request, os, ssl
import sys

REPO = "FelixZhao0524/index-sentiment-analyzer"
LOCAL_FILE = "assets/df_sentiment.xlsx"
os.makedirs("assets", exist_ok=True)

# 跨平台 SSL 上下文（Windows + Anaconda 兼容）
try:
    import certifi
    ssl_context = ssl.create_default_context(cafile=certifi.where())
except Exception:
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

# 下载 Excel（公开仓库，无需 Token）
raw_url = f"https://raw.githubusercontent.com/{REPO}/main/assets/df_sentiment.xlsx"
req = urllib.request.Request(raw_url)
with urllib.request.urlopen(req, context=ssl_context) as r:
    raw = r.read()

with open(LOCAL_FILE, "wb") as f:
    f.write(raw)
print(f"下载完成: {len(raw)/1024:.0f} KB")

# 运行预计算生成缓存
PY = sys.executable
import subprocess
result = subprocess.run(
    [PY, "scripts/precompute.py", "--local", LOCAL_FILE],
    capture_output=True, text=True
)
print(result.stdout)
```

> ⚠️ 公开仓库无需 Token，任何用户安装后可直接使用。
> ⚠️ 若出现 SSL 证书错误（Windows + Anaconda 环境），运行 `conda install ca-certificates` 或 `pip install certifi`。
> ⚠️ 所有 Python 命令需在 skill 目录下执行。

---

### 第三步：读取数据

```python
import pandas as pd

df = pd.read_excel("assets/df_sentiment.xlsx", engine="openpyxl")
df = df[df["Times"].notna()]
df["Times"] = pd.to_datetime(df["Times"], errors="coerce")  # 统一转datetime
df = df.dropna(subset=["Times"])
df = df.sort_values("Times").reset_index(drop=True)

当日 = df.iloc[-1]
前日 = df.iloc[-2]

sentiment_now  = 当日["sentiment_index_avg60_plus"]
sentiment_prev = 前日["sentiment_index_avg60_plus"]
change         = sentiment_now - sentiment_prev
```

---

### 第四步：输出分析报告

直接输出文字报告（结构见下方「报告输出规范」）。

同时自动生成一份 Word 报告（详见 Step 5），包含完整分析内容和嵌入图表，保存至 skill 工作目录。

---

### 第五步：生成 Word 报告（含图表）

文字报告输出完成后，立即生成一份 Word 文档，包含完整七章内容和嵌入的情绪指数图表。

```python
import pandas as pd, json, os
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

SKILL_DIR = os.path.dirname(os.path.abspath("SKILL.md"))
CACHE_FILE = os.path.join(SKILL_DIR, "assets/sentiment_cache.json")
IMG_FILE = os.path.join(SKILL_DIR, "assets/情绪指数图表.png")
OUT_FILE = os.path.join(os.path.expanduser("~/.openclaw/workspace"),
                        f"A股情绪指数报告_{当日['Times'].date()}.docx")

with open(CACHE_FILE) as f:
    cache = json.load(f)

headers = cache["headers"]
当日 = dict(zip(headers, cache["latest_row"]))
前日 = dict(zip(headers, cache["prev_row"]))
sentiment_now  = cache["sentiment_now"]
sentiment_prev = cache["sentiment_prev"]
change         = sentiment_now - sentiment_prev
all_factors   = cache["all_factors"]

# --- 档位映射 ---
def get_tier(v):
    if v >= 95: return "🔴 历史极值", "FF0000"
    if v >= 80: return "🟠 过度乐观", "FF8C00"
    if v >= 65: return "🟡 乐观偏热", "FFD700"
    if v >= 50: return "🟢 中性偏暖", "00C853"
    if v >= 35: return "🟢 中性偏冷", "64DD17"
    if v >= 20: return "🔵 悲观偏冷", "2979FF"
    if v >= 5:  return "🔵 过度悲观", "2962FF"
    return "🔵 冰点", "0D47A1"

factor_cn = {
    "obv_factor":"能量潮","mfi_factor":"资金流量",
    "leverage_factor":"融资杠杆","pcr_factor":"期权多空",
    "turnover_amount_factor":"换手热度","ar_factor":"人气因子",
    "br_factor":"买卖意愿","emascore_long_factor":"均线多头",
    "signal_macd_factor":"MACD动量","highlow_factor":"高低价动量",
    "RSI_factor":"相对强弱","daily_return_factor":"日收益率",
    "up_number_rate_factor":"市场广度","equity_bond_effective_factor":"广义拥挤度",
}

tier_name, tier_color = get_tier(sentiment_now)
factors_sorted = sorted(all_factors.items(), key=lambda x: x[1], reverse=True)
hot_key = cache["hot_factor"]; hot_cn = factor_cn.get(hot_key, hot_key); hot_val = cache["hot_factor_value"]
cold_key = cache["cold_factor"]; cold_cn = factor_cn.get(cold_key, cold_key); cold_val = cache["cold_factor_value"]

# --- 创建文档 ---
doc = Document()
s = doc.sections[0]
s.page_width = Inches(8.27); s.page_height = Inches(11.69)
s.left_margin = Inches(1.0); s.right_margin = Inches(1.0)
s.top_margin = Inches(0.9); s.bottom_margin = Inches(0.9)

def sr(run, size=11, bold=False, color=None):
    run.font.size = Pt(size); run.font.bold = bold
    run.font.name = "Microsoft YaHei"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    if color:
        try: run.font.color.rgb = RGBColor.from_string(color)
        except: pass

def hd(text, size=13, color="1A1A2E"):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(14); p.paragraph_format.space_after = Pt(4)
    sr(p.add_run(text), size=size, bold=True, color=color)

def bd(text, size=10.5, color="333333"):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(2); p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.first_line_indent = Pt(18)
    sr(p.add_run(text), size=size, color=color)

def banner(text, bg="1A1A2E", fg="FFFFFF"):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(8); p.paragraph_format.space_after = Pt(8)
    r = p.add_run(f"  {text}  ")
    sr(r, size=12, bold=True, color=fg)
    pPr = p._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"),"clear"); shd.set(qn("w:color"),"auto"); shd.set(qn("w:fill"), bg)
    pPr.append(shd)

# 标题
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
sr(p.add_run("【A股市场情绪指数】"), size=20, bold=True, color="1A1A2E")
p2 = doc.add_paragraph(); p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
sr(p2.add_run(f"报告日期：{当日['Times']}"), size=11, color="888888")
banner(f"综合读数：{sentiment_now:.1f} / 100  |  档位：{tier_name}（较昨日 {'↑' if change>=0 else '↓'} {abs(change):.1f}）")
doc.add_paragraph()

# 一、行情与情绪回顾
hd("一、行情与情绪回顾")
bd(f"近 5 个交易日情绪指数从 {sentiment_prev:.1f} 变动至 {sentiment_now:.1f}，"
   f"累计变化 {change:+.1f} 个点，{'回暖势头值得关注' if change>0 else '情绪仍在低位徘徊'}。"
   f"当前读数仍处历史极低区间，整体市场信心仍有待修复。")
bd(f"本轮核心驱动力来自资金流量因子（MFI = {all_factors.get('mfi_factor',0):.0f}），"
   f"但人气因子（AR = {all_factors.get('ar_factor',0):.0f}）持续低迷，买方每日追高意愿不足，"
   f"需警惕价格与情绪之间的背离风险。")

# 二、情绪状态
hd("二、当前情绪状态与重点因子解读")
tbl = doc.add_table(rows=1, cols=4); tbl.style = "Table Grid"; tbl.autofit = False
for row in tbl.rows:
    for i,w in enumerate([Inches(1.8),Inches(0.85),Inches(0.85),Inches(2.95)]):
        row.cells[i].width = w
for i,txt in enumerate(["因子","当前值","前日值","状态"]):
    tbl.rows[0].cells[i].text = txt
    tbl.rows[0].cells[i].paragraphs[0].runs[0].font.bold = True
    tbl.rows[0].cells[i].paragraphs[0].runs[0].font.size = Pt(9.5)
for fname, fval in factors_sorted:
    name = factor_cn.get(fname, fname)
    prev_v = 前日.get(fname, 0)
    _, tc = get_tier(fval)
    row = tbl.add_row().cells
    row[0].text = name; row[1].text = f"{fval:.0f}"
    row[1].paragraphs[0].runs[0].font.color.rgb = RGBColor.from_string(tc)
    row[1].paragraphs[0].runs[0].font.bold = True
    row[2].text = f"{prev_v:.0f}"
    row[3].text = "← 过热" if fval>=80 else ("← 过冷" if fval<=20 else "← 中性")
    for c in row: c.paragraphs[0].runs[0].font.size = Pt(9)
doc.add_paragraph()
p_hc = doc.add_paragraph()
sr(p_hc.add_run(f"🔥 最热因子：{hot_cn} = {hot_val:.0f}    "), size=11, bold=True, color="FF5722")
sr(p_hc.add_run(f"❄️ 最冷因子：{cold_cn} = {cold_val:.0f}"), size=11, bold=True, color="2962FF")

# 三、经济学理解
hd("三、当前情绪的经济学理解与含义解读")
bd(f"读数 {sentiment_now:.1f} 分位意味着当前A股市场处于历史上极度悲观的区间。")
bd("MFI大幅回升但AR持续低迷，说明主力资金在悄然布局，但散户跟随意愿极低——"
   "这种「机构买、散户不买」的组合往往出现在行情左侧布局阶段，是主力吸筹的典型特征。")
bd("融资杠杆因子仍处低位，说明杠杆资金尚未参与。行情能否从「超跌反弹」演变为「趋势上涨」，"
   "关键观察指标是融资余额何时开始回升。")

# 四、历史回测
is_warn = (sentiment_now >= 99) and (sentiment_now < sentiment_prev)
hd("四、历史回测与胜率参考")
bd("⚠️ 预警信号已触发，市场交易较为拥挤，请注意适时止盈。" if is_warn
   else "✅ 预警信号未触发（读数未达到历史极值区间，或尚未出现拐点）。")
stats = [
    ("统计区间","2017年1月–2025年8月"),("预警总次数","7次"),
    ("触发后回撤>10%","6次/7次"),("平均最大回撤","-13.77%"),
    ("平均预警后见顶","约19天"),("最大回撤平均持续","约101天"),
    ("单次最大回撤","-32.46%（2017年末）"),("大幅回撤捕捉率","100%"),
]
st = doc.add_table(rows=2, cols=4); st.style = "Light Shading Accent 1"
for i,(k,v) in enumerate(stats):
    ri,ci = i//4, i%4
    st.rows[ri].cells[ci].text = f"{k}：{v}"
    st.rows[ri].cells[ci].paragraphs[0].runs[0].font.size = Pt(9)
doc.add_paragraph()
bd("典型预警节点：2017年11月、2021年12月、2022年7月、2023年2月——均在回撤开始前或初期发出。")
if os.path.exists(IMG_FILE):
    hd("情绪指数历史走势图", size=12)
    p_img = doc.add_paragraph(); p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img.add_run().add_picture(IMG_FILE, width=Inches(5.8))
    bd("▲ 图：情绪指数历史走势，标注了7次预警信号位置，历次预警后市场均出现显著回撤。", size=9, color="888888")

# 五、择时建议
hd("五、择时操作建议")
timing = [
    ("⚡ 短线（< 1个月）","观望","FF5722",
     f"读数{sentiment_now:.1f}处历史极低区间，AR持续低迷，短线暂无明确机会。"
     f"若1-3日内AR不能从{all_factors.get('ar_factor',0):.0f}修复至30以上，建议继续观望。"),
    ("📈 中线（1–6个月）","持有","00C853",
     f"MFI={all_factors.get('mfi_factor',0):.0f}表明资金悄然布局，但融资杠杆={all_factors.get('leverage_factor',0):.0f}"
     f"说明杠杆资金尚未跟进，行情大概率仍属超跌反弹，建议持有观察。"),
    ("🏠 长线（> 6个月）","布局","FF8C00",
     f"读数{sentiment_now:.1f}处历史极端低位，赔率吸引，建议定投分批布局，用时间换赔率。"),
]
for period,signal,sc,reason in timing:
    pt = doc.add_paragraph(); pt.paragraph_format.space_before = Pt(6)
    sr(pt.add_run(period+"："), size=10.5, bold=True, color="1A1A2E")
    sr(pt.add_run(signal), size=10.5, bold=True, color=sc)
    bd(reason)

doc.add_paragraph()
pr = doc.add_paragraph(); pr.paragraph_format.left_indent = Pt(10)
sr(pr.add_run("⚠️ 风险提示：以上内容仅供研究参考，不构成投资建议。情绪指标反映历史规律，不预示未来走势。"),
   size=9, color="999999")

os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
doc.save(OUT_FILE)
print(f"[OK] Word报告已生成: {OUT_FILE}")
```

> ⚠️ Word 报告默认保存至 `~/.openclaw/workspace/`，文件名格式：`A股情绪指数报告_YYYY-MM-DD.docx`
> ⚠️ 报告中不包含任何 GitHub Token 或敏感信息


按以下结构展开论述，语言风格：专业但不晦涩，兼具通俗概况能力。

> 💡 报告中所有情绪读数均基于**大类资产研究团队最新A股情绪指数**编制，综合反映A股大盘整体情绪温度。

---

## 【A股市场情绪指数】
**📅 报告日期：{当日['Times']}**

## 一、行情与情绪回顾

描述近期市场走势与情绪变化趋势。要求：
- 简洁回顾近 5–20 个交易日的关键变化
- 点明情绪变化的方向和节奏（加速/放缓/反复）
- 选取 2–3 个最有代表性的因子变化作过渡

---

## 二、当前情绪状态与重点因子解读

**📊 综合读数：{sentiment_now:.1f} / 100**
**📍 档位：{档位}**（较昨日 {↑↓} {abs(change):.1f}）

逐一解读 3–5 个当前最有解释力的因子，要求：
- 说明因子含义（通俗表达，不要照抄指标名）
- 给出当前数值和历史定位（处于历史什么分位）
- 结合市场含义给出判断，不止步于"偏高"或"偏低"的描述

**档位对应：**
| 读数区间 | 档位 |
|---|---|
| 95–100 | 🔴 历史极值 |
| 80–94 | 🟠 过度乐观 |
| 65–79 | 🟡 乐观偏热 |
| 50–64 | 🟢 中性偏暖 |
| 35–49 | 🟢 中性偏冷 |
| 20–34 | 🔵 悲观偏冷 |
| 5–19 | 🔵 过度悲观 |
| 0–4 | 🔵 冰点 |

---

## 三、当前情绪的经济学理解与含义解读

从市场微观结构、资金行为、机构预期三个角度，对当前读数进行深层解读。要求：
- 揭示读数背后的经济学逻辑（为什么会出现这个读数）
- 结合 2–3 个关键因子的联动关系说明
- 给出胜率较高的市场情景判断

---

## 四、历史回测与胜率参考

**⚠️ 预警信号：** sentiment_now >= 99 且 sentiment_now < sentiment_prev（即读数触及历史极值区间后出现拐点向下）

**本节需读取并展示图表 `assets/情绪指数图表.png`，结合图表进行解读。**

**预警触发时，输出以下全部内容：**

> 发出预警时，说明市场交易较为拥挤或存在过度乐观的非理性情绪，此时可根据实际需求适当进行止盈。
>
> **历史统计（2017年1月 – 2025年8月，共8年）：**
>
> 共发出 **7次** 预警信号，其中 **6次** 市场在随后发生超过 10% 的回撤。
>
> | 统计项 | 数值 |
> |---|---|
> | 预警总次数 | 7次 |
> | 触发后回撤 > 10% 的次数 | 6次 |
> | 平均最大回撤 | **-13.77%** |
> | 平均预警后见顶天数 | **约19天** |
> | 最大回撤平均持续时间 | 约101天 |
> | 单次最大回撤 | **-32.46%**（2017年末，持续227天） |
> | 大幅回撤捕捉率（回撤>20%） | **100%** |
> | 预警后回撤>10%胜率 | **85.71%** |
>
> 典型预警时间节点：2017年11月、2021年12月、2022年7月、2023年2月——预警均在回撤开始前或回撤初期发出。
>
> **📊 图表解读：**
> 从图表可见，历史上7次预警信号均出现在情绪指数触及100分位数高位的拐点处（图表中红色圆点标记），每次预警后市场平均在约19个交易日见顶，随后进入回撤。2021年12月和2022年7月的预警后回撤幅度最为剧烈，分别对应成长股和消费股的集中杀跌阶段。

**未触发时，输出以下内容：**

> 当前未触发预警信号（读数未达到历史极值区间，或尚未出现拐点）。
>
> 以下是历史7次预警的完整统计（供参考）：
>
> | 统计项 | 数值 |
> |---|---|
> | 统计区间 | 2017年1月 – 2025年8月 |
> | 预警总次数 | 7次 |
> | 触发后回撤 > 10% 的次数 | 6次 |
> | 平均最大回撤 | **-13.77%** |
> | 平均预警后见顶天数 | **约19天** |
> | 最大回撤平均持续时间 | 约101天 |
> | 单次最大回撤 | **-32.46%**（2017年末，持续227天） |
> | 大幅回撤捕捉率（回撤>20%） | **100%** |
> | 预警后回撤>10%胜率 | **85.71%** |
>
> 典型预警时间节点：2017年11月、2021年12月、2022年7月、2023年2月。
>
> **📊 图表解读：**
> 当前读数远离预警阈值，图表中可见历史上每次指数触及极高位（100分位数）后均伴随大幅回撤，是重要的反向择时参考。当前 13.2 处于极低区间，结合图表历史经验，长线赔率较为吸引。

---

## 五、择时操作建议

按不同投资周期给出操作建议。**理由部分要求深入挖掘逻辑，不仅止步于"偏高/偏低"的描述，要给出大模型自身的分析推理。**

**⚡ 短线投资者（持仓 < 1个月）：**
- 当前信号：{做多 / 做空 / 观望}
- 理由要求（需全部覆盖）：
  1. **当前档位基调**：结合综合读数和档位，说明当前情绪对短线操作是利多还是利空
  2. **关键信号识别**：找出 1–2 个对短线最有指示意义的高频因子（如 AR、BR、换手热度），说明它们目前的状态和含义
  3. **近期演变预判**：基于因子动量和近期变化方向，给出对未来 1–5 个交易日的大致判断
  4. **风险提示**：如果存在背离信号（如价格涨但 AR 持续低），需特别指出

**📈 中线投资者（持仓 1–6个月）：**
- 当前信号：{加仓 / 减仓 / 持有}
- 理由要求（需全部覆盖）：
  1. **趋势位置判断**：结合均线多头因子和 MACD 动量，说明当前中期趋势是向上、向下还是震荡
  2. **情绪周期定位**：当前读数在历史上处于什么分位？属于历史低位（赔率好）还是高位（风险积累）
  3. **资金行为分析**：结合融资杠杆因子和资金流量的联动，判断中期资金是否支持趋势延续
  4. **情景推演**：给出 2–3 种可能的情景（乐观/基准/悲观），每种情景下中线操作应如何应对

**🏠 长线投资者（持仓 > 6个月）：**
- 当前信号：{布局 / 等待 / 持盈}
- 理由要求（需全部覆盖）：
  1. **估值与赔率**：结合报告的历史分位和广义拥挤度因子，说明当前A股整体赔率处于什么区间
  2. **机构行为信号**：融资杠杆因子的绝对水平和趋势，反映机构和中长期资金的态度
  3. **周期位置**：基于当前档位和历史数据，判断市场处于周期哪个阶段（左侧/右侧/顶部/底部）
  4. **配置思路**：长线视角下，当前应不应该分批布局，怎么控制买入节奏

> ⚠️ 以上内容仅供研究参考，不构成投资建议。

---

## 六、异常处理

- **GitHub 下载失败** → 若本地缓存存在且有效，读取本地缓存；否则返回「今日数据暂不可用，请稍后重试」
- **本地缓存不存在且下载失败** → 打印错误原因，终止分析并提示用户
- **SSL 证书验证错误（Windows + Anaconda 环境）** → 备用方案：临时跳过 SSL 验证（`ssl_context.verify_mode = ssl.CERT_NONE`），同时提示用户运行 `conda install ca-certificates` 或 `pip install certifi`
- **Excel 解析失败** → 打印原始错误，终止分析
- **数据行不足2行** → 打印 `[ERROR] 数据行不足2行`，终止分析
- **缺少必要字段** → 打印缺失的字段名，终止分析
- **Word 文档生成失败** → 打印警告（`[WARN] Word报告生成失败`），但文字报告仍正常输出，不终止流程

---

## 七、风险提示

- 情绪指标反映历史规律，不预示未来走势
- 极端读数（≥95 或 ≤5）往往对应反转节点，但反转时机无法精确预测
- 重大政策或外部冲击可瞬间改变市场结构，模型可能失效

---

## 14个因子含义速查

| 因子 | 列名 | 通俗含义 | 高值（≥80） | 低值（≤20） |
|------|------|----------|------------|------------|
| 能量潮 | `obv_factor` | 钱往哪里流 | 主力净流入 | 主力净流出 |
| 资金流量 | `mfi_factor` | 买盘有多旺 | 资金流入极强 | 卖压充分释放 |
| 融资杠杆 | `leverage_factor` | 杠杆资金有多热 | 杠杆资金大规模入场 | 融资客撤退 |
| 期权多空 | `pcr_factor` | 对冲需求有多强 | 看跌期权远超看涨 | 看涨远超看跌 |
| 换手热度 | `turnover_amount_factor` | 市场换手热度 | 成交极度活跃 | 成交极度萎缩 |
| 人气因子 | `ar_factor` | 收盘在日内高位还是低位 | 收于日内高点 | 收于日内低点 |
| 买卖意愿 | `br_factor` | 持仓者信心强弱 | 高位强势承接 | 恐慌抛压释放 |
| 均线多头 | `emascore_long_factor` | 均线多头排列强度 | 多头向上 | 空头向下 |
| MACD动量 | `signal_macd_factor` | MACD动量方向 | 多头信号强 | 空头主导 |
| 高低价动量 | `highlow_factor` | 高低价斜率谁更强 | 买方主导 | 动量衰竭 |
| 相对强弱 | `RSI_factor` | 超买超卖 | 超买明显 | 超卖明显 |
| 日收益率 | `daily_return_factor` | 短期累计涨跌 | 涨幅历史高位 | 跌幅历史低位 |
| 市场广度 | `up_number_rate_factor` | 全市场涨跌家数比 | 普涨注意踩踏 | 普跌恐慌主导 |
| 广义拥挤度 | `equity_bond_effective_factor` | 市场拥挤程度 | 极度拥挤，最危险反转 | 低拥挤高赔率 |

---

## 使用样例

**用户问：** "今日A股市场情绪如何？"

**模型执行步骤：**
1. 检查本地缓存 → 无
2. 从 GitHub 下载 df_sentiment.xlsx（raw.githubusercontent.com，无需 Token）
3. 运行 precompute.py 生成缓存
4. 读取数据：当日 sentiment=13.2，前日=11.8
5. 输出文字报告（Step 4），同时生成 Word 报告并保存至 `~/.openclaw/workspace/`（Step 5）

**模型输出示例：**
```
【A股市场情绪指数】
📅 报告日期：2026-04-30

一、行情与情绪回顾
近5日情绪持续回暖，从8.3一路上行至13.2，
累计升幅为近三月最大的一波反弹。资金类因子
（能量潮、资金流量）同步回升，但换手热度尚未明显
放大，说明本轮由主力资金主导，散户跟随意愿
尚在恢复中。

二、当前情绪状态与重点因子解读
📊 综合读数：13.2 / 100
📍 档位：🔵 过度悲观（较昨日 ↑1.4）

当前最值得关注的三个因子：

① 资金流量因子 = 22 —— 仍处历史低位，
买盘尚未全面启动，但较上周的12已明显回升，
资金面最困难的时期可能已过。

② 融资杠杆因子 = 18 —— 杠杆资金仍在撤退，这是近期最悲观的信号之一，融资客对短期行情仍偏谨慎。

③ 人气因子（AR）= 31 —— 收盘持续落在日
内低位，买方每天都不愿在高位接单，人气
修复仍需时间。

三、当前情绪的经济学理解与含义解读
读数13.2处于历史上极为悲观的区间，仅高于
约13%的时间。资金面最紧张的阶段（资金流量因子极低、
杠杆资金撤退）往往对应着行情的底部区间，
但情绪从冰点恢复需要催化剂——可能是政策
信号、增量资金或外部环境改善。当前AR持续
低迷说明买方每天都在回避接盘，短期内若没
有放量阳线，情绪可能仍在低位反复。

四、历史回测与胜率参考

当前未触发预警信号（读数未达到历史极值区间，或尚未出现拐点）。

以下是历史7次预警的完整统计（供参考）：

| 统计项 | 数值 |
|---|---|
| 统计区间 | 2017年1月 – 2025年8月 |
| 预警总次数 | 7次 |
| 触发后回撤 > 10% 的次数 | 6次 |
| 平均最大回撤 | -13.77% |
| 平均预警后见顶天数 | 约19天 |
| 最大回撤平均持续时间 | 约101天 |
| 单次最大回撤 | -32.46%（2017年末，持续227天） |
| 大幅回撤捕捉率（回撤>20%） | 100% |
| 预警后回撤>10%胜率 | 85.71% |

典型预警时间节点：2017年11月、2021年12月、2022年7月、2023年2月。

📊 图表解读：
从图表可见，历史上7次预警信号（红色圆点标记）均出现在情绪指数触及100分位数高位的拐点处，预警发出后市场平均在约19个交易日见顶随后进入回撤，2021年12月和2022年7月预警后回撤最为剧烈。

五、择时操作建议

⚡ 短线（< 1个月）：观望
1. 当前档位基调：读数13.2处于历史极低区间（仅高于约13%的历史时段），情绪冰点对短线构成利空背景。
2. 关键信号：AR=10（人气因子）持续低迷，买方每天都在回避高位接单，说明短线资金参与意愿极低；换手热度=40.5未明显放大，缺乏短线博弈条件。
3. 近期演变预判：若未来1-3日内AR不能从10修复至30以上，情绪可能仍在低位反复，短线暂无明显机会。
4. 风险提示：近期价格小幅反弹但AR持续新低，出现背离——说明本轮反弹由存量资金主导，缺乏增量资金确认。

📈 中线（1–6个月）：持有
1. 趋势位置：均线多头因子 = 12.3（极低），MACD动量因子 = 18.7，说明中期趋势仍处弱势，大概率处于磨底阶段。
2. 情绪周期定位：13.2处于历史约第13百分位，属于历史低位，赔率较好，但情绪从低位回升需要催化剂，过程可能反复。
3. 资金行为分析：资金流量因子 = 60（近一个月从个位数大幅回升）表明有资金悄然布局，但融资杠杆因子 = 42（仍在低位）说明杠杆资金尚未跟进，两者背离意味着行情可能仍属超跌反弹而非趋势反转。
4. 情景推演：
  - 乐观情景（40%概率）：AR持续修复 + 融资杠杆因子突破60，市场进入中期上涨
  - 基准情景（45%概率）：情绪低位反复，指数区间整理，持有观望
  - 悲观情景（15%概率）：资金流量因子再次回落，行情二次探底

🏠 长线（> 6个月）：布局
1. 估值与赔率：读数13.2处于历史极端低位，结合广义拥挤度因子 = 43（未进入过热区间），说明当前赔率处于历史较好水平，长线具有配置价值。
2. 机构行为：融资杠杆因子 = 42处于历史偏低位置，中长期资金整体偏谨慎，这是市场见底前的常态特征——见底前杠杆资金往往最后离场。
3. 周期位置：从历史7次预警规律看，当前大概率处于长周期底部的左侧布局阶段，非右侧追涨时机。
4. 配置思路：建议采取定投思路分批布局，用时间换赔率，重点关注情绪指数从10以下启动后的右侧信号作为加仓确认。

⚠️ 以上内容仅供研究参考，不构成投资建议。
```

---

## 反模式说明

**以下场景不应使用本 skill：**
- ❌ **用于个股分析**：本 skill 只反映A股大盘整体情绪，不适用于个股
- ❌ **依赖单一因子决策**：不应用某一个因子的极值直接作为买卖依据
- ❌ **作为唯一决策依据**：情绪指标是辅助工具，需结合政策、基本面、宏观环境综合判断
