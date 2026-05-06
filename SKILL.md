---
name: index-sentiment-analyzer
description: |
  OpenClaw Skill for deep analysis of A-share CSI 300 ETF sentiment index indicators. Triggered when user asks about: (1) A-share market sentiment and sentiment index questions; (2) analysis of specific factors (MFI, OBV, MACD, RSI, etc.); (3) historical sentiment index trends, marginal changes, percentile levels; (4) factor logic questions; (5) market condition descriptions; (6) any quantitative indicators or market activity related topics. Provides 14 core factor interpretations, 6 group analyses, composite index levels, marginal change analysis, and warning signal解读.
---

# 情绪指数分析工具

## 数据文件

- 文件：`assets/df_sentiment.xlsx`
- 数据区间：2016-01-04 至 2026-04-30（约2500个交易日）
- Sheet：Sheet1
- 截止日期：2026-04-30

---

## 工作流程

### Step 1：读取 Excel 数据

```python
import openpyxl
wb = openpyxl.load_workbook('assets/df_sentiment.xlsx', data_only=True)
ws = wb['Sheet1']
data = list(ws.iter_rows(values_only=True))
headers = data[0]
rows = data[1:]        # 数据行（按日期升序）
latest = rows[-1]     # 最新交易日
prev = rows[-2]       # 前一交易日（用于判断拐点）
wb.close()
```

### Step 2：识别问题类型

| 类型 | 用户问法示例 |
|---|---|
| A — 综合状态 | "今天情绪指数怎么样？" / "当前市场情绪如何？" |
| B — 单因子追问 | "XX因子是什么意思？" / "最近XX因子到哪个档位了？" |
| C — 预警信号 | "现在有预警信号吗？" / "市场见顶了吗？" |
| D — 因子分化 | "哪类因子最过热？" / "因子之间有什么分化？" |
| E — 历史走势 | "最近一个月情绪指数走势如何？" |

### Step 3：计算关键指标

```python
def row_to_dict(row):
    return dict(zip(headers, row))

cur = row_to_dict(latest)
pre = row_to_dict(prev)

sentiment_col = headers.index('sentiment_index_avg60_plus')

# 综合情绪指数
sentiment_now = cur['sentiment_index_avg60_plus']
sentiment_prev = pre['sentiment_index_avg60_plus']

# 拐点判断
is_100 = (sentiment_now == 100)
is_crossdown = (sentiment_now < sentiment_prev)  # 今日低于昨日

# 5日斜率
vals_all = [r[sentiment_col] for r in rows]
slope_5 = (vals_all[-1] - vals_all[-6]) / 5

# 6大类因子分组
groups = {
    '市场基础动能': ['mfi_factor','leverage_factor','pcr_factor','ar_factor',
                    'br_factor','RSI_factor','daily_return_factor','equity_bond_effective_factor'],
    '市场趋势强度': ['emascore_long_factor','signal_macd_factor'],
    '市场活跃度':   ['turnover_amount_factor'],
    '短期势能':     ['highlow_factor'],
    '资金流向':     ['obv_factor'],
    '广度一致性':   ['up_number_rate_factor'],
}
```

---

## 输出结构（重点）

### 综合状态解读（类型 A）

按以下格式输出，**直接照写，不要自己发挥、不要添加格式以外的内容**。

⚠️ **严格禁止：** 生成"操作建议"、"关键矛盾"、"数据来源"等额外模块，只需按以下格式输出纯客观描述。

```
【情绪指数综合解读】
📅 数据截止：{latest['Times']}（最新有数据交易日）

━━━━━━━━━━━━━━━━━━
📊 综合情绪指数
━━━━━━━━━━━━━━━━━━
读数：{sentiment_now} / 100
档位：{对应档位名称}（{对应档位解释}）

━━━━━━━━━━━━━━━━━━
📈 边际变化（斜率）
━━━━━━━━━━━━━━━━━━
5日斜率：{slope_5符号}{slope_5数值}（{斜率含义}）
与昨日比较：{升/降} {diff绝对值}（{变化含义}）

━━━━━━━━━━━━━━━━━━
🔥 预警信号判断
━━━━━━━━━━━━━━━━━━
预警状态：{预警状态说明}
（预警触发条件：情绪指数达到100分位 + 次日出现向下拐点。
即同时满足：①今日读数=100，②明日低于今日。）

{如果触发预警：
触发原因：情绪指数读数为100，且高于昨日({sentiment_prev})，
说明市场情绪已达到历史极端过热水平，历史上有85.71%的概率
在随后出现超过10%的回撤，请注意风险。}
{如果未触发：
未触发原因：当前读数{sentiment_now}未达到100分位，
或虽为100但尚未出现向下拐点（今日={sentiment_now}，
昨日={sentiment_prev}），说明当前未达到本体系的预警触发条件。}

━━━━━━━━━━━━━━━━━━
📋 6大类情绪分位一览
━━━━━━━━━━━━━━━━━━
（括号内为该类因子当前均值，数值含义：0-20过低/20-40偏低/40-60中性/60-80偏高/80-100过热）

市场基础动能：均值={动能均值} — {过热/中性/偏低}（{一句话解读}）
  └ 包含：资金流量(MFI)、融资杠杆、期权PCR、人气AR、多空BR、RSI、
          日收益率、广义拥挤度等8个因子

市场趋势强度：均值={趋势均值} — {过热/中性/偏低}（{一句话解读}）
  └ 包含：均线突破因子(EMA Score)、MACD趋势背离因子，共2个因子

市场活跃度：  均值={活跃均值} — {过热/中性/偏低}（{一句话解读}）
  └ 包含：成交额与换手率综合因子(turnover_amount)，共1个因子

短期势能：    均值={势能均值} — {过热/中性/偏低}（{一句话解读}）
  └ 包含：上涨势能因子(highlow)，衡量价格高/低点斜率变化，共1个因子

资金流向：    均值={资金均值} — {过热/中性/偏低}（{一句话解读}）
  └ 包含：能量潮因子(OBV)，衡量资金净流入/净流出，共1个因子

广度一致性：  均值={广度均值} — {过热/中性/偏低}（{一句话解读}）
  └ 包含：市场广度因子(up_number_rate)，追踪全市场个股涨跌比例，共1个因子

━━━━━━━━━━━━━━━━━━
🔍 重点因子追踪
━━━━━━━━━━━━━━━━━━
最过热因子：{过热因子名} = {过热因子值}（{因子通俗解释}）
最疲弱因子：{疲弱因子名} = {疲弱因子值}（{因子通俗解释}）

因子分化情况：{分化/一致}（{分化说明}）
```

---

### 因子详细介绍（类型 B — 单因子追问）

对于抽象因子，给出如下**通俗解释**：

**OBV（能量潮因子）**：
> OBV 将成交量与价格变动结合。当收盘价高于昨日时，把当日成交量累加为正向资金流入；低于昨日时则累加为负向资金流出。OBV 反映的是"钱"往哪里流——如果指数创新高但 OBV 没有跟上，说明资金在撤退，这是预警信号。本体系的 obv_factor 取 OBV 90日变化量的历史分位，数值越高说明中期资金流入越强劲。

**MFI（资金流量因子）**：
> MFI 类似 RSI，但把成交量考虑进来。典型价格 =（最高+最低+收盘）/3，当典型价格上涨时乘以当日成交量视为资金流入，下跌时视为流出。MFI 超过80意味着资金流入强度达到历史极值，市场可能短期过热；低于20说明资金流出压力充分释放，可能接近底部。

**MACD（趋势背离因子）**：
> MACD 由 DIF（快线）和 DEA（慢线）的差值构成。DIF 与 DEA 的差值即为 MACD 柱。当 MACD 由负转正且 DIF 在零轴上方，说明短期上涨动量正在加强。本体系的 signal_macd_factor 追踪 MACD 动量方向，数值越高说明上涨趋势越健康。

**RSI（相对强弱因子）**：
> RSI 衡量上涨日涨幅之和与下跌日跌幅之和的比值，反映价格上涨下跌的相对力度。RSI 超过70视为超买（涨过头），低于30视为超卖（跌过头）。本体系使用多周期 RSI 融合，减少假信号。

**广义拥挤度因子（equity_bond_effective_factor）**：
> 这个因子综合考虑两个维度：沪深300市盈率的倒数（PE的倒数=赔率，越高说明股票相对债券越便宜/有吸引力）和全市场成交金额（越活跃说明市场越拥挤）。两者相减后取5日与60日均值之差——差值越小说明市场越拥挤。数值越高（80以上）说明拥挤度极高，是最重要的反转预警信号之一。

**均线突破因子（emascore_long_factor）**：
> 该因子综合评估收盘价与多条均线的位置关系，以及各均线自身的方向。信号包括：收盘价是否在30日均线上方、各短期均线是否在长期均线上方、均线是否向上倾斜等。得分越高说明均线多头排列越完整，趋势越强。

**上涨势能因子（highlow_factor）**：
> 通过比较最近10个交易日的最高价斜率和最低价斜率判断动量方向。上涨行情中，如果最高价上涨斜率大于最低价，说明做多力量强；下跌行情中，如果最低价没有创新低，说明有资金在托底。该因子变化较快，适合捕捉短期动量转换。

---

## 各因子中文名速查

| Excel列名 | 中文名 | 大类 | 通俗一句话 |
|---|---|---|---|
| sentiment_index_avg60_plus | **情绪指数（综合）** | 最终输出 | 6大类因子的等权融合分位 |
| close_price | 沪深300ETF收盘价 | 基础价格 | 指数价格，不参与因子计算 |
| obv_factor | 能量潮因子 | 资金流向 | 钱往哪里流 |
| mfi_factor | 资金流量因子 | 市场基础动能 | 资金流入强度 |
| leverage_factor | 融资杠杆因子 | 市场基础动能 | 借钱买股票的热度 |
| pcr_factor | 期权多空因子 | 市场基础动能 | 投资者对冲需求强弱 |
| turnover_amount_factor | 流动活性因子 | 市场活跃度 | 市场和股票换手热度 |
| ar_factor | 人气活跃因子 | 市场基础动能 | 开盘价相对日内高低的位置 |
| br_factor | 多空买卖意愿因子 | 市场基础动能 | 持仓者对波动的耐受信心 |
| emascore_long_factor | 均线突破因子 | 市场趋势强度 | 均线多头排列强度 |
| signal_macd_factor | 趋势背离因子 | 市场趋势强度 | MACD动量方向 |
| highlow_factor | 上涨势能因子 | 短期势能 | 价格高低点斜率动量 |
| RSI_factor | 相对强弱因子 | 市场基础动能 | 超买超卖参考 |
| daily_return_factor | 日收益率因子 | 市场基础动能 | 短期累计涨跌 |
| up_number_rate_factor | 市场广度因子 | 广度一致性 | 全市场个股涨跌比例 |
| equity_bond_effective_factor | 广义拥挤度因子 | 市场基础动能 | 市场交易拥挤程度 |

---

## 6大类因子分组

```python
市场基础动能 = [mfi_factor, leverage_factor, pcr_factor, ar_factor,
                br_factor, RSI_factor, daily_return_factor, equity_bond_effective_factor]
市场趋势强度 = [emascore_long_factor, signal_macd_factor]
市场活跃度   = [turnover_amount_factor]
短期势能     = [highlow_factor]
资金流向     = [obv_factor]
广度一致性   = [up_number_rate_factor]
```

---

## 关键阈值速查

| 因子 | 过热(>) | 过冷(<) | 通俗理解 |
|---|---|---|---|
| mfi_factor | 80 | 20 | 资金流入历史极值/冰点 |
| leverage_factor | 80 | 20 | 借钱炒股最热/最冷时刻 |
| pcr_factor | 80 | 20 | 对冲需求极强/极弱 |
| ar_factor | 80 | 20 | 持续收在日内高点/低点 |
| br_factor | 80 | 20 | 持筹信心最强/恐慌抛售 |
| RSI_factor | 80 | 20 | 超买/超卖 |
| equity_bond_effective_factor | 80 | 20 | 极度拥挤/低拥挤+高赔率 |
| obv_factor | 80 | 20 | 资金持续净流入/净流出 |
| emascore_long_factor | 80 | 20 | 均线完全多头/空头 |
| signal_macd_factor | 80 | 20 | MACD极强/极弱 |
| highlow_factor | 80 | 20 | 动量最强/反转信号 |
| turnover_amount_factor | 80 | 20 | 交易最热/最冷清 |
| up_number_rate_factor | 80 | 20 | 个股普涨/普跌 |
| daily_return_factor | 80 | 20 | 短期涨幅历史高位/低位 |

---

## 参考文档

- 因子深度定义与逻辑：`references/factor_definition.md`
- 预警规则与档位解读：`references/signal_rules.md`
