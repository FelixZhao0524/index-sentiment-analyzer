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

缓存文件与 Excel 文件**必须同时有效**才算缓存可用：

```python
import os, json
from datetime import date, timedelta

cache_dir = "assets"
today = date.today().isoformat()

cache_file = os.path.join(cache_dir, "sentiment_cache.json")
excel_file = os.path.join(cache_dir, "df_sentiment.xlsx")
```

**同时满足以下条件时，直接读取本地缓存，跳过下载：**
1. `sentiment_cache.json` 存在
2. `df_sentiment.xlsx` 存在
3. **两者的修改时间均在今天 00:00 之前（即当天下载的）**

```python
import datetime
today_zero = datetime.datetime.combine(date.today(), datetime.time())
if (os.path.exists(cache_file) and os.path.exists(excel_file)):
    cache_mtime = datetime.datetime.fromtimestamp(os.path.getmtime(cache_file))
    excel_mtime = datetime.datetime.fromtimestamp(os.path.getmtime(excel_file))
    if cache_mtime >= today_zero and excel_mtime >= today_zero:
        with open(cache_file) as f:
            cache = json.load(f)
        print(f"使用本地缓存，数据日期: {cache['history_5'][-1]['date']}")
```

> **注意**：只要 Excel 和缓存中任意一个不是当天更新的，即视为缓存失效，会重新下载并生成。

---

### 第二步：从 GitHub 下载最新 Excel（无缓存时）

```python
import urllib.request, os, ssl, sys, subprocess, datetime
from pathlib import Path

REPO = "FelixZhao0524/index-sentiment-analyzer"
SKILL_DIR = Path(__file__).parent.resolve() if "__file__" in dir() else Path(".").resolve()
LOCAL_FILE = SKILL_DIR / "assets" / "df_sentiment.xlsx"
LOCAL_FILE.parent.mkdir(parents=True, exist_ok=True)

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

# 生成新缓存（强制刷新必须重算）
PY = sys.executable
result = subprocess.run(
    [PY, str(SKILL_DIR / "scripts" / "precompute.py"), "--local", str(LOCAL_FILE)],
    capture_output=True, text=True,
    cwd=str(SKILL_DIR)   # 明确指定工作目录，避免隐式 chdir 依赖
)
print(result.stdout)
if result.returncode != 0:
    print("[WARN] 缓存生成失败:", result.stderr)
```

> ⚠️ 公开仓库无需 Token，任何用户安装后可直接使用。
> ⚠️ 若出现 SSL 证书错误（Windows + Anaconda 环境），运行 `conda install ca-certificates` 或 `pip install certifi`。
> ⚠️ 所有 Python 命令需在 skill 目录下执行。

---

### 第三步：读取数据

```python
import pandas as pd, datetime

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

# 数据时效性检查（超过 5 个自然日未更新则警告）
latest_date = 当日["Times"].date()
days_old = (datetime.date.today() - latest_date).days
if days_old > 5:
    print(f"[WARN] 数据已过期 {days_old} 天（最新数据: {latest_date}），建议刷新最新数据")
```

---

### 第四步：输出分析报告

直接输出文字报告（结构见下方「报告输出规范」）。

同时自动生成一份 Word 报告（详见 Step 5），包含完整分析内容和嵌入图表，保存至 skill 工作目录。

---

### 第五步：生成 Word 报告（含图表）

文字报告输出完成后，立即生成一份 Word 文档。相比文字报告，Word 版本增加：封面横幅、档位进度条、近5日情绪迷你走势图、14因子全表、历史统计卡、场景推演等丰富内容，格式更精美。

```python
import pandas as pd, json, os, datetime
from pathlib import Path
from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

# --- 路径解析（兼容 SKILL.md 内嵌执行环境） ---
try:
    _skill_dir = Path(__file__).parent.resolve()
except NameError:
    _skill_dir = Path(".").resolve()

CACHE_FILE = _skill_dir / "assets" / "sentiment_cache.json"
IMG_FILE   = _skill_dir / "assets" / "情绪指数图表.png"
OUT_FILE   = Path.home() / ".openclaw" / "workspace" / f"A股情绪指数报告_{datetime.date.today()}.isoformat()}.docx"

OUT_FILE.parent.mkdir(parents=True, exist_ok=True)

with open(CACHE_FILE) as f:
    cache = json.load(f)

headers      = cache["headers"]
当日        = dict(zip(headers, cache["latest_row"]))
前日        = dict(zip(headers, cache["prev_row"]))
sentiment_now  = cache["sentiment_now"]
sentiment_prev = cache["sentiment_prev"]
change         = sentiment_now - sentiment_prev
all_factors    = cache["all_factors"]

# --- 档位映射 ---
def get_tier(v):
    if v >= 95: return "🔴 历史极值",     "FF1744", "1A1A2E"
    if v >= 80: return "🟠 过度乐观",     "FF6D00", "1A1A2E"
    if v >= 65: return "🟡 乐观偏热",     "FFC400", "1A1A2E"
    if v >= 50: return "🟢 中性偏暖",     "00C853", "FFFFFF"
    if v >= 35: return "🟢 中性偏冷",     "64DD17", "1A1A2E"
    if v >= 20: return "🔵 悲观偏冷",     "2979FF", "FFFFFF"
    if v >= 5:  return "🔵 过度悲观",     "2962FF", "FFFFFF"
    return "🔵 冰点", "0D47A1", "FFFFFF"

factor_cn = {
    "obv_factor":"能量潮","mfi_factor":"资金流量",
    "leverage_factor":"融资杠杆","pcr_factor":"期权多空",
    "turnover_amount_factor":"换手热度","ar_factor":"人气因子",
    "br_factor":"买卖意愿","emascore_long_factor":"均线多头",
    "signal_macd_factor":"MACD动量","highlow_factor":"高低价动量",
    "RSI_factor":"相对强弱","daily_return_factor":"日收益率",
    "up_number_rate_factor":"市场广度","equity_bond_effective_factor":"广义拥挤度",
}

factor_desc = {
    "obv_factor":"钱往哪里流","mfi_factor":"买盘有多旺",
    "leverage_factor":"杠杆资金有多热","pcr_factor":"对冲需求有多强",
    "turnover_amount_factor":"市场换手热度","ar_factor":"收盘在日内高位还是低位",
    "br_factor":"持仓者信心强弱","emascore_long_factor":"均线多头排列强度",
    "signal_macd_factor":"MACD动量方向","highlow_factor":"高低价斜率谁更强",
    "RSI_factor":"超买超卖","daily_return_factor":"短期累计涨跌",
    "up_number_rate_factor":"全市场涨跌家数比","equity_bond_effective_factor":"市场拥挤程度",
}

tier_name, tier_color, tier_fg = get_tier(sentiment_now)
factors_sorted = sorted(all_factors.items(), key=lambda x: x[1], reverse=True)
hot_key = cache["hot_factor"]; hot_cn = factor_cn.get(hot_key, hot_key); hot_val = cache["hot_factor_value"]
cold_key = cache["cold_factor"]; cold_cn = factor_cn.get(cold_key, cold_key); cold_val = cache["cold_factor_value"]
history_5 = cache.get("history_5", [])
is_warn = (sentiment_now >= 99) and (sentiment_now < sentiment_prev)

# =========================================================================
#  文档创建
# =========================================================================
doc = Document()
s = doc.sections[0]
s.page_width  = Inches(8.27)
s.page_height = Inches(11.69)
s.left_margin   = Inches(1.0)
s.right_margin  = Inches(1.0)
s.top_margin    = Inches(0.9)
s.bottom_margin = Inches(0.9)

# --- 字体工具函数 ---
def set_cell_bg(cell, hex_color):
    tc = cell._tc; tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd"); shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)

def set_cell_border(cell, **kwargs):
    tc = cell._tc; tcPr = tc.get_or_add_tcPr()
    tcBorders = OxmlElement("w:tcBorders")
    for edge in ("top","left","bottom","right"):
        tag = OxmlElement(f"w:{edge}")
        tag.set(qn("w:val"),   kwargs.get(edge, "single"))
        tag.set(qn("w:sz"),    kwargs.get("sz",  "4"))
        tag.set(qn("w:space"), "0")
        tag.set(qn("w:color"), kwargs.get("color", "auto"))
        tcBorders.append(tag)
    tcPr.append(tcBorders)

def sr(run, size=11, bold=False, color=None):
    run.font.size = Pt(size); run.font.bold = bold
    run.font.name = "Microsoft YaHei"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    if color:
        try: run.font.color.rgb = RGBColor.from_string(color)
        except: pass

def heading(text, size=13, color="1A1A2E"):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(16); p.paragraph_format.space_after = Pt(4)
    sr(p.add_run(text), size=size, bold=True, color=color)
    return p

def body(text, size=10.5, color="333333", indent=True):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(2); p.paragraph_format.space_after = Pt(4)
    if indent: p.paragraph_format.first_line_indent = Pt(18)
    sr(p.add_run(text), size=size, color=color)
    return p

def divider(color="DDDDDD"):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(4); p.paragraph_format.space_after = Pt(4)
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom"); bottom.set(qn("w:val"),"single")
    bottom.set(qn("w:sz"),"4"); bottom.set(qn("w:space"),"1")
    bottom.set(qn("w:color"), color)
    pBdr.append(bottom); pPr.append(pBdr)

def section_banner(text, bg="1A1A2E", fg="FFFFFF"):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(10); p.paragraph_format.space_after = Pt(10)
    r = p.add_run(f"  {text}  ")
    sr(r, size=12, bold=True, color=fg)
    pPr = p._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"),"clear"); shd.set(qn("w:color"),"auto"); shd.set(qn("w:fill"), bg)
    pPr.append(shd)

# =========================================================================
#  封面
# =========================================================================
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(30); p.paragraph_format.space_after = Pt(6)
sr(p.add_run("A股市场情绪指数"), size=28, bold=True, color="1A1A2E")

p2 = doc.add_paragraph()
p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
p2.paragraph_format.space_before = Pt(0); p2.paragraph_format.space_after = Pt(4)
sr(p2.add_run("CSI 300 ETF Sentiment Index"), size=12, color="888888")

p3 = doc.add_paragraph()
p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
p3.paragraph_format.space_before = Pt(0); p3.paragraph_format.space_after = Pt(20)
sr(p3.add_run(f"报告日期：{当日['Times']}"), size=11, color="888888")

# 档位横幅
section_banner(
    f"综合读数  {sentiment_now:.1f} / 100  |  档位：{tier_name}（较昨日 {'↑' if change>=0 else '↓'} {abs(change):.1f}）",
    bg=tier_color, fg=tier_fg
)

# 档位进度条（文字版）
bar_width = 40
filled = int(round(sentiment_now / 100 * bar_width))
bar_str = "█" * filled + "░" * (bar_width - filled)
p_bar = doc.add_paragraph()
p_bar.alignment = WD_ALIGN_PARAGRAPH.CENTER
p_bar.paragraph_format.space_before = Pt(6); p_bar.paragraph_format.space_after = Pt(20)
sr(p_bar.add_run(f"0  {bar_str}  100"), size=11, color=tier_color)

# 近5日情绪迷你走势
if history_5:
    dates_row = "  ".join([h["date"][-5:] for h in history_5])
    vals_row  = "  ".join([f"{h['sentiment']:.1f}" for h in history_5])
    p_d = doc.add_paragraph()
    p_d.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_d.paragraph_format.space_before = Pt(0); p_d.paragraph_format.space_after = Pt(4)
    sr(p_d.add_run("近5日情绪走势"), size=10, bold=True, color="888888")
    p_d2 = doc.add_paragraph()
    p_d2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_d2.paragraph_format.space_before = Pt(0); p_d2.paragraph_format.space_after = Pt(4)
    sr(p_d2.add_run(dates_row), size=9, color="AAAAAA")
    p_v = doc.add_paragraph()
    p_v.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_v.paragraph_format.space_before = Pt(0); p_v.paragraph_format.space_after = Pt(20)
    sr(p_v.add_run(vals_row), size=11, bold=True, color="1A1A2E")

divider(); doc.add_paragraph()

# =========================================================================
#  一、行情与情绪回顾
# =========================================================================
heading("一、行情与情绪回顾")
body(f"近 5 个交易日情绪指数从 {sentiment_prev:.1f} 变动至 {sentiment_now:.1f}，"
     f"累计变化 {change:+.1f} 个点，{'回暖势头值得关注' if change>0 else '情绪仍在低位徘徊'}。"
     f"当前读数仍处历史极低区间，整体市场信心仍有待修复。")
body(f"本轮核心驱动力来自资金流量因子（MFI = {all_factors.get('mfi_factor',0):.0f}），"
     f"但人气因子（AR = {all_factors.get('ar_factor',0):.0f}）持续低迷，买方每日追高意愿不足，"
     f"需警惕价格与情绪之间的背离风险。")

# =========================================================================
#  二、情绪状态
# =========================================================================
heading("二、当前情绪状态与重点因子解读")

# 因子全表（14因子，5列：因子名/通俗含义/当前值/历史分位/状态）
tbl = doc.add_table(rows=1, cols=5)
tbl.style = "Table Grid"
tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
col_widths = [Inches(1.3), Inches(1.6), Inches(0.7), Inches(0.9), Inches(2.0)]
for i, w in enumerate(col_widths):
    for cell in tbl.columns[i].cells:
        cell.width = w

hdrs = ["因子","通俗含义","当前值","历史分位","状态说明"]
for i, h in enumerate(hdrs):
    cell = tbl.rows[0].cells[i]
    cell.text = h
    cell.paragraphs[0].runs[0].font.bold = True
    cell.paragraphs[0].runs[0].font.size = Pt(9)
    set_cell_bg(cell, "1A1A2E")
    cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

for idx, (fname, fval) in enumerate(factors_sorted):
    row = tbl.add_row()
    name = factor_cn.get(fname, fname)
    desc = factor_desc.get(fname, "")
    prev_v = 前日.get(fname, 0)
    _, tc, _ = get_tier(fval)
    row.cells[0].text = name
    row.cells[1].text = desc
    row.cells[2].text = f"{fval:.0f}"
    row.cells[2].paragraphs[0].runs[0].font.color.rgb = RGBColor.from_string(tc)
    row.cells[2].paragraphs[0].runs[0].font.bold = True
    pct = f"{'极低' if fval<=20 else ('极低' if fval<=35 else ('中性' if fval<65 else ('偏高' if fval<80 else '极高')))}"
    row.cells[3].text = pct
    row.cells[4].text = f"前日 {prev_v:.0f}，{'过热⚠️' if fval>=80 else ('过冷⚠️' if fval<=20 else '正常')}"
    for c in row.cells:
        c.paragraphs[0].runs[0].font.size = Pt(9)
    if idx % 2 == 1:
        for c in row.cells:
            set_cell_bg(c, "F5F5F5")

doc.add_paragraph()
p_hc = doc.add_paragraph()
p_hc.paragraph_format.space_before = Pt(4)
sr(p_hc.add_run(f"🔥 最热因子：{hot_cn} = {hot_val:.0f}    "), size=11, bold=True, color="FF5722")
sr(p_hc.add_run(f"❄️ 最冷因子：{cold_cn} = {cold_val:.0f}"), size=11, bold=True, color="2962FF")

# =========================================================================
#  三、经济学理解
# =========================================================================
heading("三、当前情绪的经济学理解与含义解读")
body(f"读数 {sentiment_now:.1f} 分位意味着当前A股市场处于历史上极度悲观的区间。")
body("MFI大幅回升但AR持续低迷，说明主力资金在悄然布局，但散户跟随意愿极低——"
     "这种「机构买、散户不买」的组合往往出现在行情左侧布局阶段，是主力吸筹的典型特征。")
body("融资杠杆因子仍处低位，说明杠杆资金尚未参与。行情能否从「超跌反弹」演变为「趋势上涨」，"
     "关键观察指标是融资余额何时开始回升。")

# =========================================================================
#  四、历史回测
# =========================================================================
heading("四、历史回测与胜率参考")

if is_warn:
    section_banner("⚠️ 预警信号已触发，市场交易较为拥挤，请注意适时止盈。", bg="FF1744", fg="FFFFFF")
else:
    section_banner("✅ 预警信号未触发，当前远离历史极值区间", bg="00C853", fg="FFFFFF")

doc.add_paragraph()

# 历史统计卡
stats = [
    ("统计区间",        "2017年1月–2025年8月（8年）"),
    ("预警总次数",      "7次"),
    ("触发后回撤>10%",  "6次 / 7次"),
    ("平均最大回撤",    "-13.77%"),
    ("平均预警后见顶",  "约19个交易日"),
    ("最大回撤持续",    "约101天"),
    ("单次最大回撤",    "-32.46%（2017年末，227天）"),
    ("回撤>20%捕捉率", "100%"),
    ("预警后胜率",      "85.71%"),
]
st = doc.add_table(rows=3, cols=3)
st.style = "Light Shading Accent 1"
st.alignment = WD_TABLE_ALIGNMENT.CENTER
stat_vals = [
    ("统计区间", "2017年1月–2025年8月（8年）"),
    ("预警总次数", "7次（全部有效）"),
    ("触发后回撤>10%", "6次 / 7次（85.71%）"),
    ("平均最大回撤", "-13.77%"),
    ("平均预警后见顶", "约19个交易日"),
    ("最大回撤持续", "约101天"),
    ("单次最大回撤", "-32.46%（2017年末）"),
    ("回撤>20%捕捉率", "100%"),
    ("基准情景回撤幅度", "-8%~15%"),
]
for i, (k, v) in enumerate(stat_vals):
    ri, ci = i // 3, i % 3
    cell = st.rows[ri].cells[ci]
    cell.text = ""
    p_k = cell.paragraphs[0]; p_k.clear()
    sr(p_k.add_run(k + "："), size=9, bold=True, color="555555")
    p_v = cell.add_paragraph(); p_v.clear()
    sr(p_v.add_run(v), size=9, bold=True, color="1A1A2E")

doc.add_paragraph()
body("典型预警节点：2017年11月、2021年12月、2022年7月、2023年2月——均在回撤开始前或初期发出。")

if IMG_FILE.exists():
    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img.paragraph_format.space_before = Pt(8); p_img.paragraph_format.space_after = Pt(6)
    p_img.add_run().add_picture(str(IMG_FILE), width=Inches(5.8))
    body("▲ 图：情绪指数历史走势，标注了7次预警信号位置（红色圆点），历次预警后市场均出现显著回撤。",
         size=9, color="888888")

# =========================================================================
#  五、择时建议（Word版比文字版更详细，包含完整情景推演）
# =========================================================================
heading("五、择时操作建议")

# 三个周期卡片
for period, signal, bg, sc, items in [
    ("⚡ 短线（< 1个月）", "观  望", "FFF3E0", [
        ("档位基调", f"读数{sentiment_now:.1f}处历史极低区间（仅高于约{float(sentiment_now):.0f}%的历史时段），"
         "情绪冰点对短线构成系统性利空背景。"),
        ("关键信号", f"AR = {all_factors.get('ar_factor',0):.0f}（人气因子）持续低迷，买方每天都在回避高位接单，"
         f"说明短线资金参与意愿极低；换手热度 = {all_factors.get('turnover_amount_factor',0):.0f} 未明显放大，缺乏博弈条件。"),
        ("近期预判", f"若未来1-3日内AR不能从{int(all_factors.get('ar_factor',0))}修复至30以上，"
         "情绪可能仍在低位反复，短线暂无明确机会。"),
        ("风险提示", f"近期价格小幅反弹但AR持续新低——出现经典背离，"
         "说明本轮反弹由存量资金主导，缺乏增量资金确认，需高度警惕。"),
    ]),
    ("📈 中线（1–6个月）", "持  有", "E8F5E9", [
        ("趋势位置", f"均线多头因子 = {all_factors.get('emascore_long_factor',0):.1f}（{'极弱' if all_factors.get('emascore_long_factor',0)<30 else '偏弱'}），"
         f"MACD动量 = {all_factors.get('signal_macd_factor',0):.1f}，中期趋势仍处弱势，大概率处于磨底阶段。"),
        ("情绪周期", f"{sentiment_now:.1f}处于历史约第{int(sentiment_now)}百分位，属历史低位，赔率较佳，"
         "但情绪从低位回升需要催化剂，过程可能反复。"),
        ("资金行为", f"资金流量 = {all_factors.get('mfi_factor',0):.0f}，表明有资金悄然布局；"
         f"但融资杠杆 = {all_factors.get('leverage_factor',0):.0f}（仍在低位），两者背离意味着行情大概率仍属超跌反弹。"),
        ("情景推演",
         f"乐观（30%）：AR持续修复 + 融资杠杆突破60，市场进入中期上涨\n"
         f"基准（50%）：情绪低位反复，指数区间整理，持有观望\n"
         f"悲观（20%）：资金流量再次回落，行情二次探底"),
    ]),
    ("🏠 长线（> 6个月）", "布  局", "E3F2FD", [
        ("估值赔率", f"读数{sentiment_now:.1f}处历史极端低位，广义拥挤度 = {all_factors.get('equity_bond_effective_factor',0):.0f}（未过热），"
         "赔率处于历史较佳水平，长线具有配置价值。"),
        ("机构信号", f"融资杠杆 = {all_factors.get('leverage_factor',0):.0f}，中长期资金整体偏谨慎，"
         "这是市场见底前的常态——杠杆资金往往最后离场。"),
        ("周期位置", f"从历史7次预警规律看，当前大概率处于长周期底部左侧布局阶段，非右侧追涨时机。"),
        ("配置思路", f"建议采取定投分批布局，用时间换赔率；"
         f"重点关注情绪指数从10以下启动后的右侧信号，作为加仓确认依据。"),
    ]),
]:
    section_banner(period, bg=bg.replace("#",""), fg="1A1A2E")
    p_s = doc.add_paragraph()
    p_s.paragraph_format.space_before = Pt(4); p_s.paragraph_format.space_after = Pt(2)
    sr(p_s.add_run("信号：" + signal), size=13, bold=True, color=sc)
    for label, content in items:
        p_l = doc.add_paragraph()
        p_l.paragraph_format.space_before = Pt(4); p_l.paragraph_format.space_after = Pt(1)
        p_l.paragraph_format.first_line_indent = Pt(0)
        sr(p_l.add_run(label + "："), size=10, bold=True, color="555555")
        body(content, size=10, indent=True)

doc.add_paragraph()
pr = doc.add_paragraph()
pr.paragraph_format.left_indent = Pt(10)
sr(pr.add_run("⚠️ 风险提示：以上内容仅供研究参考，不构成投资建议。情绪指标反映历史规律，不预示未来走势。"),
   size=9, color="999999")

# =========================================================================
#  保存
# =========================================================================
doc.save(str(OUT_FILE))
print(f"[OK] Word报告已生成: {OUT_FILE}")
```

> ⚠️ Word 报告默认保存至 `~/.openclaw/workspace/`，文件名格式：`A股情绪指数报告_YYYY-MM-DD.docx`
> ⚠️ 报告中不包含任何 GitHub Token 或敏感信息

---

## 报告输出规范（文字报告）

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
> 当前读数远离预警阈值，图表中可见历史上每次指数触及极高位（100分位数）后均伴随大幅回撤，是重要的反向择时参考。当前 {sentiment_now} 处于极低区间，结合图表历史经验，长线赔率较为吸引。

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
1. 检查本地缓存（Excel + JSON 均当天更新）→ 有
2. 直接读取 `sentiment_cache.json`
3. 输出文字报告（Step 4），同时生成 Word 报告并保存至 `~/.openclaw/workspace/`（Step 5）

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
