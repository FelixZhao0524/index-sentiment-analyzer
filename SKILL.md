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

### 步骤1：加载预计算缓存（毫秒级）

```python
import json

with open('assets/sentiment_cache.json', 'r') as f:
    cache = json.load(f)

cur = dict(zip(cache['headers'], cache['latest_row']))
pre = dict(zip(cache['headers'], cache['prev_row']))

# 预计算好的指标（直接使用，无需再算）
sentiment_now = cache['sentiment_now']           # 综合情绪指数
sentiment_prev = cache['sentiment_prev']         # 前日综合情绪指数
slope_5 = cache['slope_5']                       # 5日斜率
group_means = cache['group_means']               # 6大组均值 dict
hot_factor = cache['hot_factor']                  # 最热因子名
hot_factor_value = cache['hot_factor_value']      # 最热因子值
cold_factor = cache['cold_factor']               # 最冷因子名
cold_factor_value = cache['cold_factor_value']    # 最冷因子值
all_factors = cache['all_factors']              # 全部14因子 {名:值}
latest_date = cur['Times']
```

### 步骤1b：历史走势查询（慢，仅Type E时使用）

```python
import pandas as pd
df = pd.read_excel('assets/df_sentiment.xlsx', engine='openpyxl')
df = df.sort_values('Times').tail(30)  # 最近30条
```

### 步骤2：识别问题类型

| 类型 | 典型问法 |
|------|----------|
| A — 整体状态解读 | "今天情绪指数怎么样？" / "当前市场情绪如何？" |
| B — 单因子追问 | "XX因子是什么意思？" / "XX因子目前处于什么水平？" |
| C — 预警信号查询 | "现在有预警信号吗？" / "市场见顶了吗？" |
| D — 因子分化分析 | "哪类因子最过热？" / "因子之间有没有分化？" |
| E — 历史走势查询 | "最近一个月情绪指数怎么走的？" |

---

## 输出结构（重要）

### 整体状态解读（类型A）

**严格禁止：** 生成"操作建议"、"关键矛盾"、"数据来源"，或超出以下结构的内容。

**格式规范：**
- 主标题用 `【】`，子标题用 `▎` 开头，段落之间不多余空行
- 数字精确到小数点后1位
- 每组因子一行，格式：`组名：均值=XX → 档位（深度解读）`
- 分化判断统一在"重点因子追踪"节说明

```
【沪深300ETF情绪指数】
报告日期：{cur['Times']}

▎综合情绪指数
  读数：{sentiment_now:.1f} / 100
  档位：{档位名称}
  含义：{档位深度解读}

▎边际变化
  5日斜率：{斜率方向}{abs(slope_5):.2f}（{斜率解读}）
  较昨日：{↑上升/↓下降} {abs(sentiment_now - sentiment_prev):.1f}（{变化解读}）

▎预警信号
  状态：{触发 ✓ / 未触发 ✗}
  {触发: 读数100+拐点，历史胜率85.71%，建议关注回撤风险。}
  {未触发: 当前读数{sentiment_now:.1f}，{不满足条件描述}。}

▎6大类因子分组读数
  市场基础动能：均值={momentum_mean:.1f} → {档位}（{深度金融解读}）
    · 最强因子：{最强因子名}={最强因子值:.1f}　最弱因子：{最弱因子名}={最弱因子值:.1f}
  市场趋势强度：均值={trend_mean:.1f} → {档位}（{深度金融解读}）
  市场活跃度：均值={activity_mean:.1f} → {档位}（{深度金融解读}）
  短期势能：均值={momentum_st_mean:.1f} → {档位}（{深度金融解读}）
  资金流向：均值={flow_mean:.1f} → {档位}（{深度金融解读}）
  广度一致性：均值={breadth_mean:.1f} → {档位}（{深度金融解读}）

▎重点因子追踪
  最过热：{hot_factor}={hot_factor_value:.1f}（{该因子金融含义解读}）
  最偏冷：{cold_factor}={cold_factor_value:.1f}（{该因子金融含义解读}）
  分化状态：{分化/一致} — {分化/一致的具体解读}
```

**档位填充规则（代入实际读数）：**

| sentiment_now 区间 | 档位名称 | 深度解读（代入X） |
|---|---|---|
| 90-100 | 🔴 极端乐观 | 读数X，处于历史最高区间，市场情绪极度亢奋，均值回归概率较高 |
| 80-89 | 🟠 过度乐观 | 读数X，处于历史偏高区间，赚钱效应明显，注意情绪过热反转风险 |
| 70-79 | 🟡 乐观偏热 | 读数X，情绪较好，多头格局延续，可持有但避免过度追涨 |
| 60-69 | 🟡 偏热 | 读数X，中性偏多，市场情绪稳中向好 |
| 50-59 | 🟢 中性偏暖 | 读数X，情绪处于正常区间，市场平稳运行 |
| 40-49 | 🟢 中性 | 读数X，情绪正常，多空相对均衡 |
| 30-39 | 🔵 偏冷 | 读数X，中性偏弱，情绪有所回落，谨慎信号 |
| 20-29 | 🔵 悲观偏冷 | 读数X，情绪较弱，市场参与度下降 |
| 10-19 | 🔵 过度悲观 | 读数X，接近冰点，历史上此处往往蕴含布局机会 |
| 0-9 | 🔵 极度悲观 | 读数X，冰点区域，市场恐慌充分释放，反弹概率较高 |

**斜率填充规则：**

| slope_5 区间 | 斜率解读 |
|---|---|
| > +2.0/日 | 情绪快速升温，市场热情高涨，注意短期过热回调风险 |
| +1.0 ~ +2.0 | 情绪温和改善，趋势向好，做多情绪积累中 |
| 0 ~ +1.0 | 情绪平稳，无明显方向，缓慢变化 |
| -1.0 ~ 0 | 情绪平稳偏弱，无明显方向 |
| -2.0 ~ -1.0 | 情绪温和降温，做多情绪消退 |
| < -2.0/日 | 情绪快速退潮，市场热情骤降，注意防范风险 |

**分组档位判断（代值时直接套用）：**

| 分组均值区间 | 档位 |
|---|---|
| ≥ 80 | 🔥过热 |
| 60-79 | 🟡偏热 |
| 40-59 | 🟢中性 |
| 20-39 | 🔵偏冷 |
| < 20 | 🔵过冷 |

**分组深度金融解读填充规则（必须代入实际数值）：**

- **市场基础动能（均值=X）：**
  - X≥60：`综合动能指数X，资金面+趋势面共振偏强，MFI/BR等因子处于历史偏高区间，趋势类因子协同向上，做多胜率较高`
  - X≤40：`综合动能指数X，MFI/BR/AR等偏低，价格动量不足，趋势延续性弱，市场缺乏明确方向`
  - 40<X<60：`综合动能指数X，各因子分化，多空信号均有，趋势方向待确认`

- **市场趋势强度（均值=X）：**
  - X≥60：`趋势强度指数X，均线多头排列完整（MA5>MA10>MA20>MA60），MACD动量向上，趋势健康`
  - X≤40：`趋势强度指数X，均线仍为空头或混乱，信号不明，做多胜率低，趋势类策略应谨慎`
  - 40<X<60：`趋势强度指数X，多空势力均衡，趋势突破方向待确认`

- **市场活跃度（均值=X）：**
  - X≥60：`活跃度指数X，成交处于历史高位，换手率高，市场参与热情高涨`
  - X≤40：`活跃度指数X，成交冷清，处于历史低位，市场参与意愿低，往往是底部特征`
  - 40<X<60：`活跃度指数X，成交正常，无明显异常`

- **短期势能（均值=X）：**
  - X≥60：`短期动量指数X，高/低价斜率共振向上，短期上涨动能充足，趋势加速概率大`
  - X≤40：`短期动量指数X，价格高低斜率收缩，上涨动能耗尽或底部酝酿中，注意方向选择`
  - 40<X<60：`短期动量指数X，方向不明，动能中性`

- **资金流向（均值=X）：**
  - X≥60：`资金流向指数X，OBV持续净流入，主力资金积极布局，中期方向偏多`
  - X≤40：`资金流向指数X，资金持续净流出，主力撤退明显，市场中期方向偏空`
  - 40<X<60：`资金流向指数X，资金面平衡，无明显方向`

- **广度一致性（均值=X）：**
  - X≥60：`广度指数X，上涨家数远超下跌家数，个股普涨，情绪蔓延健康，趋势延续性强`
  - X≤40：`广度指数X，全市场跌多涨少，广度收窄，市场情绪分化，指数可能有虚高成分`
  - 40<X<60：`广度指数X，涨跌家数基本均衡，市场无明显方向偏好`

**分化判断规则：**
- 统计6组均值中"过热/偏热"（≥60）的组数 vs "偏冷/过冷"（<40）的组数
- 两者均有（至少各1组）→ 分化：解读为"各因子方向不一致，市场未形成合力，震荡格局概率大"
- 6组全部同向（全部≥40或全部≤60）→ 一致：解读为"各因子方向一致，市场情绪共振，趋势延续概率高"
- 5-6组均值在40-60之间 → 中性：解读为"各因子均处于中性区间，市场无明确方向"

**最热/最冷因子金融含义填充（代实际值）：**

| 因子名 | 过热（≥80）解读 | 过冷（≤20）解读 |
|---|---|---|
| mfi_factor | 资金流量达历史极值，买盘极度旺盛，注意短期过热回调 | 资金流出压力充分释放，往往对应底部区域 |
| leverage_factor | 融资杠杆资金大规模涌入，市场亢奋，警惕平仓踩踏风险 | 融资客大规模撤退，市场情绪极度悲观，往往是底部信号 |
| pcr_factor | 期权看跌持仓远超看涨，对冲需求激增，市场谨慎情绪浓厚 | 期权看涨持仓远超看跌，市场过度乐观，反转风险累积 |
| ar_factor | 持续收于日内高点，买方力量极强，狂热追涨阶段 | 持续收于日内低点，卖方主导，往往恐慌见底 |
| br_factor | 资金高位仍强势承接，持仓信心强，警惕"动能衰减"预警 | 恐慌抛压充分释放，情绪修复窗口打开 |
| RSI_factor | RSI达历史高位，超买明显，短期回调概率大 | RSI达历史低位，超卖明显，布局机会区 |
| equity_bond_effective_factor | 股债拥挤度达极端高位（数值越小越拥挤），市场最危险信号 | 拥挤度极低+高赔率，历史上是较好布局区间 |
| obv_factor | OBV持续净流入，主力资金强势介入 | OBV持续净流出，主力撤退明显 |
| emascore_long_factor | 均线完美多头排列，趋势向上，做多信号 | 均线空头排列，趋势向下，做空信号 |
| signal_macd_factor | MACD动量极强，上涨趋势健康 | MACD空头主导，趋势向下 |
| highlow_factor | 高低价动量极强，上涨趋势加速 | 动量衰竭，趋势可能反转 |
| turnover_amount_factor | 成交极度活跃，投机情绪亢奋，注意回调 | 成交极度萎缩，市场冷清，往往是底部 |
| up_number_rate_factor | 普涨格局，市场情绪高度一致，一致性过高后警惕踩踏 | 普跌格局，恐慌情绪主导，冰点后往往反弹 |
| daily_return_factor | 短期累计收益达历史高位，获利回吐压力大 | 短期累计跌幅达历史低位，超跌反弹概率大 |

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
