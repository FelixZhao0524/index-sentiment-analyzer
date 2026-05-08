---
name: index-sentiment-analyzer
description: A股沪深300 ETF情绪指数分析工具。当用户询问以下问题时触发本skill：(1) 关于A股市场情绪、情绪指数、预警信号的问题；(2) 需要分析沪深300ETF的某个因子或多个因子的含义、当前位置、过热/过冷信号；(3) 需要解读情绪指数的历史走势、边际变化、档位含义；(4) 需要了解某个因子背后的逻辑（如MFI、OBV、MACD、RSI等指标在情绪体系中的含义）；(5) 用户提供了一段行情描述，希望判断当前市场情绪状态；(6) 任何与情绪择时、量化指标、市场热门程度相关的问题；(7) 用户要求更新数据、刷新数据、从GitHub更新数据时。

**设计原则**：本skill提供情绪指数数据和14个因子的通俗解读。数据分析维度和回复方式由调用方自行决定，本skill不预设输出框架。
---

# 情绪指数分析工具

## 核心概念（设计哲学）

本skill的数据基础是14个市场情绪因子，原始数值均为**历史分位**（0-100），反映当前状态在近180个交易日中的相对位置。

**使用方式**：调用方获取数据后，自行决定分析维度和回复方式。本skill提供：
1. 最新数据（直接可用）
2. 14个因子的通俗含义（帮助解读）
3. 预警规则（帮助判断风险）

---

## Step 0：判断问题类型

| 类型 | 触发关键词 | 执行动作 |
|------|-----------|---------|
| A-D | 情绪指数/因子/预警/走势等 | 直接读取缓存数据，进入Step 1 |
| **E — 数据更新** | "更新数据""刷新数据""从GitHub更新""更新情绪指数" | **执行 GitHub 数据更新流程（见Step 5）** |

---

## Step 1：读取最新数据

**优先使用缓存**（`assets/sentiment_cache.json`），无需每次重新计算Excel。

缓存数据结构说明：

```python
{
  "headers": ["Times","close_price","obv_factor","mfi_factor","leverage_factor",
               "pcr_factor","turnover_amount_factor","ar_factor","br_factor",
               "emascore_long_factor","signal_macd_factor","highlow_factor",
               "RSI_factor","daily_return_factor","up_number_rate_factor",
               "equity_bond_effective_factor","sentiment_index_avg60_plus"],
  "latest_row": [...],        # 最新交易日完整数据
  "prev_row": [...],          # 前一交易日（用于判断拐点）
  "slope_5": float,           # 5日斜率（情绪指数变化速度）
  "sentiment_now": float,     # 当前综合情绪指数（0-100）
  "sentiment_prev": float,    # 昨日综合情绪指数
  "group_means": {            # 因子分组均值（仅供参考，不必强制使用）
    "市场基础动能": 39.0,
    "市场趋势强度": 15.5,
    "市场活跃度": 40.5,
    "短期势能": 46.0,
    "资金流向": 29.0,
    "广度一致性": 57.0
  },
  "all_factors": {            # 14个因子当前值（分位）
    "obv_factor": 29,
    "mfi_factor": 60,
    "leverage_factor": 42,
    "pcr_factor": 34.0,
    "turnover_amount_factor": 40.5,
    "ar_factor": 10,
    "br_factor": 19,
    "emascore_long_factor": 12.3,
    "signal_macd_factor": 18.7,
    "highlow_factor": 46,
    "RSI_factor": 50,
    "daily_return_factor": 54,
    "up_number_rate_factor": 57,
    "equity_bond_effective_factor": 43
  },
  "hot_factor": "mfi_factor",     # 当前最高因子
  "cold_factor": "ar_factor",      # 当前最低因子
  "history_5": [...],              # 最近5个交易日
  "history_20": [...]              # 最近20个交易日
}
```

**读取缓存**：
```python
import json
with open('assets/sentiment_cache.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
```

**判断预警状态**（最重要）：
```python
sentiment_now = data['sentiment_now']
sentiment_prev = data['sentiment_prev']
is_100 = (sentiment_now == 100)
is_crossdown = (sentiment_now < sentiment_prev)  # 今日低于昨日

if is_100 and is_crossdown:
    alert_triggered = True   # 预警信号触发
    # 历史胜率：85.71%的概率随后出现超过10%回撤
else:
    alert_triggered = False
```

---

## Step 2：因子通俗解读（按需查询）

当用户询问某个具体因子时，提供以下通俗解释。**不要照搬输出格式，用自己的话组织语言**，让投顾客户听得懂。

---

### OBV因子（能量潮因子）
**通俗解释**：把成交量和价格涨跌挂钩。如果今天涨了，就把今天的成交量当作"正向资金流入"累加；如果跌了，当作"资金流出"。OBV的90日变化量反映中期资金是净流入还是净流出。OBV创新高说明主力资金在持续买入；OBV创新低说明资金在撤退。

**分位解读**：
- 80以上：资金持续净流入，市场亢奋，但也要注意"高位钝化"（指数还在涨但OBV开始下降=预警）
- 20以下：资金持续净流出，市场悲观，往往是底部积累信号

---

### MFI因子（资金流量因子）
**通俗解释**：MFI是成交量的RSI。计算典型价格（最高+最低+收盘的均值），乘以当日成交量得到资金流量。资金流入的日子累加，资金流出的日子减掉。MFI超过80意味着资金流入强度达到历史极限，市场可能短期过热；低于20说明资金在撤退。

**分位解读**：
- 80以上：资金流入历史极值，过热信号
- 20以下：资金流出压力充分释放，可能接近底部

---

### 融资杠杆因子（leverage_factor）
**通俗解释**：直接看融资融券余额中融资买入的活跃程度。借钱买股票的人越多、借钱金额越高，说明市场越热。杠杆资金是市场情绪的放大器——涨时助推涨，跌时加剧踩踏。

**分位解读**：
- 80以上：借钱炒股最热的时刻，预警信号
- 20以下：杠杆资金几乎消失，市场冷到冰点

---

### PCR因子（期权多空因子）
**通俗解释**：PCR = 认沽期权持仓量 / 认购期权持仓量。买认沽期权的人多，说明大家在担心下跌、对冲风险；买认购的人多，说明大家乐观看涨。PCR处于历史高位说明市场恐慌情绪浓厚（投资者在疯狂买入保险），往往对应短期局部高点。

**分位解读**：
- 80以上：投资者对冲需求激增，市场谨慎信号
- 20以下：过度乐观，认购期权被大量买入

---

### 成交额/换手率因子（turnover_amount_factor）
**通俗解释**：把全市场成交金额和换手率结合起来，看市场有多活跃。数值越高说明市场越热、参与者越多；数值越低说明市场越冷清。这个指标变化较快，适合观察短期情绪波动。

**分位解读**：
- 80以上：市场交易异常活跃，可能是顶部信号
- 20以下：成交极度萎缩，市场冷清

---

### AR因子（人气活跃因子）
**通俗解释**：AR = Σ(最高价-开盘价) / Σ(开盘价-最低价)，反映开盘后多方力量能把价格推到日内多高的位置。AR高说明价格持续收在日内高位，买方力量强；AR低说明卖方主导，价格收在日内低位。

**分位解读**：
- 80以上：价格持续收在日内高点，追涨情绪强
- 20以下：持续收在日内低点，投资者不愿买入

---

### BR因子（多空买卖意愿因子）
**通俗解释**：BR类似于AR，但用的是昨收而不是开盘价。衡量持仓者在当前位置是否还愿意持有——BR高说明资金在高位仍愿意承接，BR低说明恐慌情绪释放。

**分位解读**：
- 80以上：持筹信心强，但也要警惕"价格涨但BR阶梯式下降"的背离
- 20以下：恐慌抛压充分释放

---

### 均线突破因子（emascore_long_factor）
**通俗解释**：综合评估价格与多条均线的位置关系。收盘价在均线上方、短期均线在长期均线上方、均线向上倾斜——这些都是多头排列的信号。得分越高说明趋势越强。

**分位解读**：
- 80以上：均线多头排列完整，趋势向上
- 20以下：均线空头排列，趋势向下

---

### MACD趋势因子（signal_macd_factor）
**通俗解释**：MACD由快线(DIFF)和慢线(DEM)的差值构成。MACD由负转正说明短期上涨动量在加强；DIFF在零轴上方说明均价在上升。该因子融合了动量方向和强度两个信息。

**分位解读**：
- 80以上：MACD多头信号强，上涨趋势健康
- 20以下：MACD空头主导，趋势向下

---

### 高低点斜率因子（highlow_factor）
**通俗解释**：比较最近10个交易日最高价和最低价的斜率变化。涨的时候最高价斜率大于最低价斜率=做多力量强；跌的时候最低价没创新低=有资金在托底。这个指标变化快，适合捕捉短期动量转换。

**分位解读**：
- 80以上：动量处于历史最强区间
- 20以下：动量最弱，可能酝酿反转

---

### RSI因子（相对强弱因子）
**通俗解释**：RSI是最经典的超买超卖指标。计算上涨日涨幅之和与下跌日跌幅之和的比值。超过70视为超买（涨过头），低于30视为超卖（跌过头）。本体系使用多周期RSI融合减少假信号。

**分位解读**：
- 80以上：超买区域
- 20以下：超卖区域

---

### 日收益率因子（daily_return_factor）
**通俗解释**：直接看最近30个交易日的平均日收益率。数值高说明近期累计涨幅大，属于短期强势市场；数值低说明近期累计跌幅大。

**分位解读**：
- 80以上：短期涨幅处于历史高位，警惕回调
- 20以下：短期跌幅处于历史低位，可能超跌反弹

---

### 市场广度因子（up_number_rate_factor）
**通俗解释**：追踪全市场上涨股票数占上涨+下跌总数的比例。个股普涨说明情绪健康蔓延；个股普跌说明情绪收缩。这个指标能发现"指数撑住但个股在退潮"的隐蔽背离。

**分位解读**：
- 80以上：绝大多数个股在涨，情绪高度一致
- 20以下：绝大多数个股在跌，情绪极度悲观

---

### 广义拥挤度因子（equity_bond_effective_factor）
**通俗解释**：综合考虑估值（沪深300 PE的倒数，代表股票相对债券的吸引力）和交易活跃度（成交金额）。逻辑是：股票吸引力和交易活跃度一起衡量市场状态——当股票赔率低但成交非常活跃时，市场最危险，因为大家都在里面搏傻，一旦反转就是踩踏。这个因子是本体系中最重要的**反转预警因子**。

**分位解读**：
- 80以上：极度拥挤（PE高+成交活跃），历史胜率最高的预警信号
- 20以下：低拥挤+高赔率，较好的逆向布局区间

---

## Step 3：预警规则（最重要）

**触发条件（同时满足）**：
1. 综合情绪指数 = 100（达到历史最高分位）
2. 今日读数低于昨日（出现向下拐点）

```python
alert_triggered = (sentiment_now == 100) and (sentiment_now < sentiment_prev)
```

**预警含义**：市场情绪达到历史极端过热水平，历史上有约**85.71%**的概率在随后出现超过10%的回撤，平均提前约19天预警。

**分位档位参考**（0-100综合情绪指数）：

| 分位 | 状态 | 含义 |
|------|------|------|
| 100 + 拐点 | 🔴 预警信号 | 极端过热，择机减仓 |
| 90-99 | 🟠 极度乐观 | 接近过热，密切观察 |
| 80-89 | 🟠 过度乐观 | 可能过热，注意止盈 |
| 70-79 | 🟡 乐观偏热 | 情绪较好，可持有 |
| 60-69 | 🟡 偏热 | 中性偏多 |
| 40-59 | 🟢 正常区间 | 无明显方向 |
| 20-39 | 🔵 偏冷 | 情绪较弱，关注机会 |
| 0-19 | 🔵 冰点 | 情绪极端，逆向布局参考 |

**边际变化**（5日斜率 > 0代表情绪在升温，< 0代表在降温）：
- 斜率 > +2/日：情绪快速升温
- 斜率 -1～+1：方向不明
- 斜率 < -2/日：情绪快速退潮

---

## Step 4：阈值速查表

| 因子 | 过热关注(>) | 过冷关注(<) | 通俗理解 |
|------|-----------|-----------|---------|
| obv_factor | 80 | 20 | 资金净流入/净流出极值 |
| mfi_factor | 80 | 20 | 资金流入/流出强度极值 |
| leverage_factor | 80 | 20 | 借钱炒股热度 |
| pcr_factor | 80 | 20 | 对冲需求/乐观程度 |
| turnover_amount_factor | 80 | 20 | 市场交易冷热 |
| ar_factor | 80 | 20 | 收在日内高位/低位 |
| br_factor | 80 | 20 | 持筹信心强弱 |
| emascore_long_factor | 80 | 20 | 均线多头/空头排列 |
| signal_macd_factor | 80 | 20 | MACD动量方向强度 |
| highlow_factor | 80 | 20 | 价格动量强弱 |
| RSI_factor | 80 | 20 | 超买/超卖 |
| daily_return_factor | 80 | 20 | 短期累计涨跌 |
| up_number_rate_factor | 80 | 20 | 个股普涨/普跌比例 |
| equity_bond_effective_factor | 80 | 20 | 市场交易拥挤程度 |

---

## Step 5：数据更新流程

当用户请求更新数据时执行：

**F-1. 下载最新Excel**
```bash
github_api="https://api.github.com/repos/FelixZhao0524/index-sentiment-analyzer/contents/assets/df_sentiment.xlsx"
curl -s "$github_api" | python3 -c "import sys,json,base64; d=json.load(sys.stdin); open('assets/df_sentiment.xlsx','wb').write(base64.b64decode(d['content']))"
```

**F-2. 运行预计算**
```python
import pandas as pd, json, os
os.chdir('/root/.openclaw/workspace/skills/index-sentiment-analyzer')
excel_path = 'assets/df_sentiment.xlsx'
json_path = 'assets/sentiment_cache.json'

df = pd.read_excel(excel_path, engine='openpyxl')
df = df.sort_values('Times').reset_index(drop=True)
headers = list(df.columns)
rows = df.values.tolist()
latest_row, prev_row = rows[-1], rows[-2]

sentiment_col = headers.index('sentiment_index_avg60_plus')
vals_all = [r[sentiment_col] for r in rows]
slope_5 = round((vals_all[-1] - vals_all[-6]) / 5, 3) if len(vals_all) >= 6 else 0

groups = {
    '市场基础动能': ['mfi_factor','leverage_factor','pcr_factor','ar_factor','br_factor','RSI_factor','daily_return_factor','equity_bond_effective_factor'],
    '市场趋势强度': ['emascore_long_factor','signal_macd_factor'],
    '市场活跃度': ['turnover_amount_factor'],
    '短期势能': ['highlow_factor'],
    '资金流向': ['obv_factor'],
    '广度一致性': ['up_number_rate_factor'],
}

def row_dict(r): return dict(zip(headers, r))
cur = row_dict(latest_row)
sentiment_now = cur['sentiment_index_avg60_plus']
sentiment_prev = row_dict(prev_row)['sentiment_index_avg60_plus']

group_means = {g: round(sum(cur.get(f,0) for f in fs)/len(fs), 1) for g, fs in groups.items()}
all_factors = sum(groups.values(), [])
factor_vals = {f: round(cur.get(f, 0), 1) for f in all_factors}
hot, cold = max(factor_vals, key=factor_vals.get), min(factor_vals, key=factor_vals.get)

output = {
    'latest_row': latest_row, 'prev_row': prev_row, 'headers': headers,
    'slope_5': slope_5, 'sentiment_now': round(sentiment_now, 4),
    'sentiment_prev': round(sentiment_prev, 4), 'group_means': group_means,
    'hot_factor': hot, 'hot_factor_value': factor_vals[hot],
    'cold_factor': cold, 'cold_factor_value': factor_vals[cold],
    'all_factors': factor_vals, 'history_5': rows[-5:], 'history_20': rows[-20:],
}
with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f'updated: {latest_row[0]}, sentiment={sentiment_now:.2f}, slope={slope_5:.3f}')
```

**F-3. 输出确认**
```
✅ 数据已更新！
📅 数据截止：{latest_row[0]}
📊 情绪指数：{sentiment_now}
📈 5日斜率：{slope_5}
```

---

## 模拟问答示例

以下是本skill在模拟场景下的典型问答，供参考：

---

**Q: 今天市场情绪怎么样？**

A（基于2026-04-30数据）:
> 数据截止4月30日，综合情绪指数读数为13.2（分位），处于冰点偏冷区域，较前一日（11.4）小幅上升，5日斜率为+1.47，情绪处于低位修复阶段。
>
> 从因子分化来看：MFI因子（60分位）和市场广度因子（57分位）相对偏高，说明资金面有一定流入且个股开始分化活跃；但均线因子（12分位）和MACD因子（19分位）处于历史低位，说明中长期趋势仍然偏弱。
>
> 预警状态：未触发（综合情绪指数未达到100分位）。当前整体判断：情绪处于冰点区域的修复初期，趋势信号偏弱，适合观察而非追涨。

---

**Q: 拥挤度因子最近怎么看？**

A:
> 广义拥挤度因子（equity_bond_effective_factor）最新读数为43分位，处于正常偏低的区间，说明当前市场整体不算拥挤。
>
> 该因子在80以上是预警区域——意味着PE偏高（股票吸引力下降）同时成交活跃（大家都在里面搏傻），历史上这个组合往往对应重要顶部。当前读数43，说明目前市场既没有严重低估也没有过度拥挤，处于相对平衡状态。
>
> 如果该因子进一步下降到20以下，可以关注逆向布局机会；如果快速攀升至80以上，则需要警惕。

---

**Q: 有没有出现预警信号？**

A:
> 经检查，最新数据（4月30日）综合情绪指数为13.2，未达到100分位的预警触发条件。
>
> 本体系的预警规则为：综合情绪指数达到100分位（历史最高）+ 次日出现向下拐点。满足此条件时，历史上有约85%的概率随后出现超过10%的回撤。当前未触发预警。

---

**Q: OBV因子是什么意思？**

A:
> OBV（能量潮）是一个将成交量与价格涨跌挂钩的指标。今天涨了，就把你今天的成交量当作"钱流入市场"累加起来；今天跌了，就当作"钱流出市场"。
>
> 本skill使用的obv_factor是OBV 90日变化量的历史分位。数值越高，说明中期资金净流入越强劲；数值越低，说明资金在持续净流出。
>
> 举一个直观的例子：如果指数创新高但OBV没有跟上，说明实际上资金在悄悄撤退——这是一个隐蔽的预警信号。反过来，指数还在跌但OBV已经开始回升，往往是见底的早期信号。
>
> 当前最新读数为29分位（4月30日），说明中期资金仍在净流出状态，情绪尚未进入乐观区间。

---

## 数据文件

- 文件：`assets/df_sentiment.xlsx`
- 数据区间：2016-01-04 至 2026-04-30（约2500个交易日）
- Sheet：Sheet1
- 截止日期：2026-04-30

---

## 参考文档

- 因子深度定义与逻辑：`references/factor_definition.md`
- 预警规则与档位解读：`references/signal_rules.md`
