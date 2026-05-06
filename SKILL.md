---
name: index-sentiment-analyzer
description: |
  OpenClaw Skill for deep analysis of A-share CSI 300 ETF sentiment index indicators. Triggered when user asks about: (1) A-share market sentiment and sentiment index questions; (2) analysis of specific factors (MFI, OBV, MACD, RSI, etc.); (3) historical sentiment index trends, marginal changes, percentile levels; (4) factor logic questions; (5) market condition descriptions; (6) any quantitative indicators or market activity related topics. Provides 14 core factor interpretations, 6 group analyses, composite index levels, marginal change analysis, and warning signal detection.
---

# 沪深300ETF情绪指数深度分析工具

## 数据文件

- 实时数据：`assets/sentiment_cache.json`（预计算缓存，毫秒级加载，**每次分析优先读此文件**）
- 原始明细：`assets/df_sentiment.xlsx`（仅查询多日历史走势时才用）
- 预计算脚本：`scripts/precompute.py`（Excel更新后运行可刷新缓存）
- 时间范围：2016-01-04 至 2026-04-30（约2500个交易日）

> **性能说明**：从 JSON 缓存读取仅需 <1ms，无需解析 Excel。Excel 仅在查历史走势（Type E）时使用。
> 
> **缓存更新**：Excel 数据更新（如新加一行）后，运行 `python3 scripts/precompute.py` 刷新缓存。

---

## 工作流程

### 步骤1：加载预计算缓存（秒级）

```python
import json

with open('assets/sentiment_cache.json', 'r') as f:
    cache = json.load(f)

cur = dict(zip(cache['headers'], cache['latest_row']))
pre = dict(zip(cache['headers'], cache['prev_row']))

# 预计算好的指标（直接使用，无需再算）
sentiment_now = cache['sentiment_now']
sentiment_prev = cache['sentiment_prev']
slope_5 = cache['slope_5']
group_means = cache['group_means']        # 6大组均值
hot_factor = cache['hot_factor']           # 最热因子名
hot_factor_value = cache['hot_factor_value']
cold_factor = cache['cold_factor']       # 最冷因子名
cold_factor_value = cache['cold_factor_value']
all_factors = cache['all_factors']        # 全部14因子当前值
latest_date = cur['Times']
```

### 步骤1b：历史走势查询（慢，仅Type E时使用）

```python
import pandas as pd
df = pd.read_excel('assets/df_sentiment.xlsx', engine='openpyxl')
df = df.sort_values('Times').tail(30)  # 最近30条
# 或 tail(N) 查询更多
```

### 步骤2：识别问题类型

| 类型 | 典型问法 |
|------|----------|
| A — 整体状态解读 | "今天情绪指数怎么样？" / "当前市场情绪如何？" |
| B — 单因子追问 | "XX因子是什么意思？" / "XX因子目前处于什么水平？" |
| C — 预警信号查询 | "现在有预警信号吗？" / "市场见顶了吗？" |
| D — 因子分化分析 | "哪类因子最过热？" / "因子之间有没有分化？" |
| E — 历史走势查询 | "最近一个月情绪指数怎么走的？" |

### 步骤3：直接使用预计算结果

```python
# 拐点判断（来自缓存）
is_100 = (sentiment_now == 100)
is_crossdown = (sentiment_now < sentiment_prev)

# 5日斜率（已预计算）
slope_5  # 直接用 cache['slope_5']

# 6大类因子分组（已预计算）
group_means = cache['group_means']
# {
#   '市场基础动能': 39.0,
#   '市场趋势强度': 15.5,
#   '市场活跃度': 40.5,
#   '短期势能': 46.0,
#   '资金流向': 29.0,
#   '广度一致性': 57.0,
# }
```

---

## 输出结构（重要）

### 整体状态解读（类型A）

严格按照以下格式输出。**不要偏离，不要自行增加额外章节。**

**严格禁止：** 生成"操作建议"、"关键矛盾"、"数据来源"或超出以下结构的任何内容。

```
【沪深300ETF情绪指数概览】
📅 数据日期：{cur['Times']}（有数据的最新交易日）

━━━━━━━━━━━━━━━━━━
📊 综合情绪指数
━━━━━━━━━━━━━━━━━━
读数：{sentiment_now} / 100
档位：{档位名称}（{档位解释}）

━━━━━━━━━━━━━━━━━━
📈 边际变化（斜率）
━━━━━━━━━━━━━━━━━━
5日斜率：{斜率符号}{斜率值}（{斜率含义}）
较昨日：{上升/下降} {diff_abs}（{变化含义}）

━━━━━━━━━━━━━━━━━━
🔥 预警信号检查
━━━━━━━━━━━━━━━━━━
预警状态：{触发/未触发}
（触发条件：情绪指数达到历史最高分位100 AND 次日环比下降。两个条件同时满足。）

{如果触发:
触发原因：情绪指数读数{sencent_prev}，已出现拐点，
说明市场情绪达到历史极端过热状态。历史统计显示，
此后85.71%的概率会出现超过10%的回撤。请高度重视风险。}

{如果未触发:
未触发原因：当前读数{sentiment_now}尚未达到历史最高分位100，
或者虽然达到100但尚未出现下降拐点（今日={sentiment_now}，
昨日={sentiment_prev}），不满足系统预警触发条件。}

━━━━━━━━━━━━━━━━━━
📋 6大类因子 — 分组百分位一览
━━━━━━━━━━━━━━━━━━
（括号内为分组均值；0-20=过冷/20-40=偏冷/40-60=中性/60-80=偏热/80-100=过热）

市场基础动能：均值={momentum_mean} — {过热/中性/偏冷}（{一句话解读}）
  └ 包含：资金流量（MFI）、融资杠杆、期权多空比、人气活跃（AR）、
         多空买卖意愿（BR）、RSI、日收益率、股债有效性 — 共8个因子

市场趋势强度：均值={trend_mean} — {过热/中性/偏冷}（{一句话解读}）
  └ 包含：均线突破评分、MACD趋势背离 — 共2个因子

市场活跃度：均值={activity_mean} — {过热/中性/偏冷}（{一句话解读}）
  └ 包含：成交金额与换手率 — 共1个因子

短期势能：均值={momentum_st_mean} — {过热/中性/偏冷}（{一句话解读}）
  └ 包含：高低价动量（价格高/低位斜率变化）— 共1个因子

资金流向：均值={flow_mean} — {过热/中性/偏冷}（{一句话解读}）
  └ 包含：能量潮（OBV，净资金流向）— 共1个因子

广度一致性：均值={breadth_mean} — {过热/中性/偏冷}（{一句话解读}）
  └ 包含：市场广度（全市场涨跌家数比）— 共1个因子

━━━━━━━━━━━━━━━━━━
🔍 重点因子追踪
━━━━━━━━━━━━━━━━━━
最过热：{hot_factor_name} = {hot_factor_value}（{通俗解释}）
最偏冷：{weak_factor_name} = {weak_factor_value}（{通俗解释}）

因子分化：{分化/一致}（{分化说明}）
```

---

### 因子详解（类型B — 单因子追问）

对于抽象因子，提供通俗语言解释：

**OBV（能量潮因子）**：
> OBV将成交量与价格变动结合。当收盘价高于昨天时，将今日成交量作为正向资金流量累加；低于昨天时作为负向累加。OBV反映"钱流向哪里"——如果指数创新高但OBV没有跟上，说明资金在撤退，是预警信号。本体系中，obv_factor取OBV变化的90日历史百分位。数值越高，说明中期资金流入越强。

**MFI（资金流量因子）**：
> MFI类似RSI，但加入了成交量。典型价格 = (最高价+最低价+收盘价)/3。典型价格上涨×成交量=资金流入，下跌×成交量=资金流出。MFI高于80说明资金流入强度达到历史极值，市场可能短期过热；低于20说明卖压充分释放，可能接近底部。

**MACD（趋势背离因子）**：
> MACD由DIF（快线）和DEA（慢线）组成，MACD柱 = DIF - DEA。当MACD由负转正且DIF在零轴上方时，短期上涨动能在加强。本体系中，signal_macd_factor追踪MACD动量方向。数值越高，说明上涨趋势越健康。

**RSI（相对强弱因子）**：
> RSI衡量上涨日涨幅之和与下跌日跌幅之和的比值，反映价格涨/跌的相对强度。RSI高于70=超买（涨过头），低于30=超卖。本体系采用多周期RSI融合，减少单周期假信号。

**股债有效性因子**：
> 该因子综合两个维度：沪深300 PE倒数（E/P，"收益率"比——越高说明股票相对债券越便宜/越有吸引力）和全市场成交金额（越活跃=越拥挤）。它用这个合成信号的5日均线减去60日均线。数值越小说明越拥挤。该因子高于80表示极端拥挤——是最重要的反转预警信号之一。

**均线突破因子**：
> 该因子评估收盘价与多条均线的位置关系，以及各均线的方向。信号包括：收盘价是否在30日均线上方、短期均线是否在长期均线上方、均线是否向上倾斜等。得分越高，说明均线多头排列越完整，趋势越强。

**高低价动量因子**：
> 该因子通过比较10日高价斜率与10日低价斜率来判断动量方向。上涨趋势中，如果高价斜率超过低价斜率，买方力量强；下跌趋势中，如果低价没有创新低，说明资金在托市。该因子变化较快，适合捕捉短期动量切换。

---

## 因子名称速查表

| Excel列名 | 名称 | 分组 | 通俗解释 |
|---|---|---|---|
| sentiment_index_avg60_plus | 综合情绪指数 | 最终输出 | 6大类等权融合的百分位 |
| close_price | 沪深300ETF收盘价 | 基准价格 | 指数价格，不参与因子计算 |
| obv_factor | 能量潮因子 | 资金流向 | 资金流向哪儿 |
| mfi_factor | 资金流量因子 | 市场基础动能 | 资金流入强度 |
| leverage_factor | 融资杠杆因子 | 市场基础动能 | 融资炒股有多热 |
| pcr_factor | 期权多空因子 | 市场基础动能 | 对冲需求强弱 |
| turnover_amount_factor | 流动活性因子 | 市场活跃度 | 市场/ETF换手热度 |
| ar_factor | 人气活跃因子 | 市场基础动能 | 开盘价在日内区间位置 |
| br_factor | 多空买卖意愿因子 | 市场基础动能 | 持仓者对波动承受力 |
| emascore_long_factor | 均线突破因子 | 市场趋势强度 | 均线多头排列强度 |
| signal_macd_factor | MACD信号因子 | 市场趋势强度 | MACD动量方向 |
| highlow_factor | 高低价动量因子 | 短期势能 | 价格高/低价斜变动量 |
| RSI_factor | 相对强弱因子 | 市场基础动能 | 超买超卖参考 |
| daily_return_factor | 日收益率因子 | 市场基础动能 | 短期累计涨跌幅 |
| up_number_rate_factor | 市场广度因子 | 广度一致性 | 全市场涨跌家数比 |
| equity_bond_effective_factor | 股债有效性因子 | 市场基础动能 | 市场拥挤程度 |

---

## 6大类因子分组

```python
市场基础动能 = [mfi_factor, leverage_factor, pcr_factor, ar_factor,
                br_factor, RSI_factor, daily_return_factor, equity_bond_effective_factor]
市场趋势强度 = [emascore_long_factor, signal_macd_factor]
市场活跃度 = [turnover_amount_factor]
短期势能 = [highlow_factor]
资金流向 = [obv_factor]
广度一致性 = [up_number_rate_factor]
```

---

## 关键阈值参考

| 因子 | 过热阈值(>) | 过冷阈值(<) | 通俗含义 |
|---|---|---|---|
| mfi_factor | 80 | 20 | 历史极端流入 / 冰点 |
| leverage_factor | 80 | 20 | 融资最热 / 最冷 |
| pcr_factor | 80 | 20 | 对冲需求极强 / 极弱 |
| ar_factor | 80 | 20 | 持续日内高位 / 低位收盘 |
| br_factor | 80 | 20 | 信心最强 / 恐慌抛售 |
| RSI_factor | 80 | 20 | 超买 / 超卖 |
| equity_bond_effective_factor | 80 | 20 | 极端拥挤 / 低拥挤+高赔率 |
| obv_factor | 80 | 20 | 持续净流入 / 净流出 |
| emascore_long_factor | 80 | 20 | 完美均线多头 / 空头排列 |
| signal_macd_factor | 80 | 20 | MACD最强 / 最弱 |
| highlow_factor | 80 | 20 | 动量最强 / 反转信号 |
| turnover_amount_factor | 80 | 20 | 成交最热 / 最冷 |
| up_number_rate_factor | 80 | 20 | 普涨 / 普跌 |
| daily_return_factor | 80 | 20 | 历史最高 / 最低短期收益 |

---

## 参考文档

- 因子定义与逻辑：`references/factor_definition.md`
- 预警规则与档位解读：`references/signal_rules.md`
