# A股市场情绪指数深度分析工具

> 触发词（高优先级）：A股情绪、今日A股情绪、市场情绪怎么样、A股现在热不热、A股买点、A股卖点
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
import urllib.request, json, base64, os
from datetime import date

REPO = "FelixZhao0524/index-sentiment-analyzer"
LOCAL_FILE = "assets/df_sentiment.xlsx"
os.makedirs("assets", exist_ok=True)

# 1. 下载 Excel
req = urllib.request.Request(
    f"https://api.github.com/repos/{REPO}/contents/assets/df_sentiment.xlsx?ref=main"
)
with urllib.request.urlopen(req) as r:
    d = json.loads(r.read())

raw = base64.b64decode(d["content"])
with open(LOCAL_FILE, "wb") as f:
    f.write(raw)
print(f"下载完成: {len(raw)/1024:.0f} KB")

# 2. 运行预计算生成缓存
import subprocess
result = subprocess.run(
    ["python3", "scripts/precompute.py", "--local", LOCAL_FILE],
    capture_output=True, text=True
)
print(result.stdout)
```

> ⚠️ 所有 Python 命令需在 skill 目录下执行：
> `cd /root/.openclaw/workspace/skills/index-sentiment-analyzer && python3 scripts/precompute.py --local assets/df_sentiment.xlsx`

---

### 第三步：读取数据

```python
import pandas as pd

df = pd.read_excel("assets/df_sentiment.xlsx", engine="openpyxl")
df = df[df["Times"].notna()]
df = df.sort_values("Times").reset_index(drop=True)

当日 = df.iloc[-1]
前日 = df.iloc[-2]

sentiment_now  = 当日["sentiment_index_avg60_plus"]
sentiment_prev = 前日["sentiment_index_avg60_plus"]
change         = sentiment_now - sentiment_prev
```

---

### 第四步：输出分析报告

直接输出文字报告，**不生成任何文件**。

---

## 报告输出规范

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

仅当预警信号触发时展开此章节，否则略过。

**⚠️ 预警信号：** sentiment_now >= 99 且 sentiment_now < sentiment_prev

触发时输出：
> 历史 7 次触发中 6 次在随后约 20 个交易日内出现超过 10% 回撤，平均最大回撤 -13.77%，单次最大 -32.46%（2017年末）。

未触发时输出：
> 当前未触发预警信号（读数未达到历史极值区间，或尚未出现拐点）。

---

## 五、择时操作建议

按不同投资周期给出操作建议，每类建议需有明确判断和理由：

**⚡ 短线投资者（持仓 < 1个月）：**
- 当前信号：{做多 / 做空 / 观望}
- 理由：{结合 1–2 个高频因子说明}

**📈 中线投资者（持仓 1–6个月）：**
- 当前信号：{加仓 / 减仓 / 持有}
- 理由：{结合中期趋势因子和情绪周期位置说明}

**🏠 长线投资者（持仓 > 6个月）：**
- 当前信号：{布局 / 等待 / 持盈}
- 理由：{从估值、赔率、机构行为角度说明}

> ⚠️ 以上内容仅供研究参考，不构成投资建议。

---

## 六、异常处理

- **GitHub 下载失败** → 若本地缓存存在且有效，读取本地缓存；否则返回「今日数据暂不可用，请稍后重试」
- **本地缓存不存在且下载失败** → 打印错误原因，终止分析并提示用户
- **Excel 解析失败** → 打印原始错误，终止分析
- **数据行不足2行** → 打印 `[ERROR] 数据行不足2行`，终止分析
- **缺少必要字段** → 打印缺失的字段名，终止分析

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
2. 从 GitHub 下载 df_sentiment.xlsx（219KB）
3. 运行 precompute.py 生成缓存
4. 读取数据：当日 sentiment=13.2，前日=11.8

**模型输出示例：**
```
【A股市场情绪指数】
📅 报告日期：2026-04-30

一、行情与情绪回顾
近5日情绪持续回暖，从8.3一路上行至13.2，
累计升幅为近三月最大的一波反弹。资金类因子
（OBV、MFI）同步回升，但换手热度尚未明显
放大，说明本轮由主力资金主导，散户跟随意愿
尚在恢复中。

二、当前情绪状态与重点因子解读
📊 综合读数：13.2 / 100
📍 档位：🔵 过度悲观（较昨日 ↑1.4）

当前最值得关注的三个因子：

① 资金流量（MFI）= 22 —— 仍处历史低位，
买盘尚未全面启动，但较上周的12已明显回升，
资金面最困难的时期可能已过。

② 融资杠杆（leverage）= 18 —— 杠杆资金仍
在撤退，这是近期最悲观的信号之一，融资客
对短期行情仍偏谨慎。

③ 人气因子（AR）= 31 —— 收盘持续落在日
内低位，买方每天都不愿在高位接单，人气
修复仍需时间。

三、当前情绪的经济学理解与含义解读
读数13.2处于历史上极为悲观的区间，仅高于
约13%的时间。资金面最紧张的阶段（MFI极低、
杠杆资金撤退）往往对应着行情的底部区间，
但情绪从冰点恢复需要催化剂——可能是政策
信号、增量资金或外部环境改善。当前AR持续
低迷说明买方每天都在回避接盘，短期内若没
有放量阳线，情绪可能仍在低位反复。

四、历史回测与胜率参考
当前未触发预警信号（读数未达到历史极值区间，
或尚未出现拐点）。

五、择时操作建议

⚡ 短线（< 1个月）：观望
  理由：情绪仍处冰点，AR持续低迷，尚无企稳信号。

📈 中线（1–6个月）：持有
  理由：MFI已从极低值回升，资金面最坏时候或已过，
  中期赔率较好。

🏠 长线（> 6个月）：布局
  理由：13.2的历史分位意味着当前估值处于历史
  低位区间，赔率吸引，可定投布局。

⚠️ 以上内容仅供研究参考，不构成投资建议。
```

---

## 反模式说明

**以下场景不应使用本 skill：**
- ❌ **用于个股分析**：本 skill 只反映A股大盘整体情绪，不适用于个股
- ❌ **依赖单一因子决策**：不应用某一个因子的极值直接作为买卖依据
- ❌ **作为唯一决策依据**：情绪指标是辅助工具，需结合政策、基本面、宏观环境综合判断
