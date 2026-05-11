# 沪深300ETF情绪指数深度分析工具

> 触发词：A股情绪、沪深300情绪、市场情绪、ETF情绪、情绪指数、沪深300今日情绪、当前市场情绪

---

## 分析流程

### 第一步：下载最新数据

用 Python 从 GitHub 下载 Excel 文件（通过 GitHub API + base64 解码）：

```python
import urllib.request, json, base64, os

REPO = "FelixZhao0524/index-sentiment-analyzer"
LOCAL_FILE = "assets/df_sentiment.xlsx"

os.makedirs("assets", exist_ok=True)

req = urllib.request.Request(
    f"https://api.github.com/repos/{REPO}/contents/assets/df_sentiment.xlsx?ref=main"
)
with urllib.request.urlopen(req) as r:
    d = json.loads(r.read())

raw = base64.b64decode(d["content"])
with open(LOCAL_FILE, "wb") as f:
    f.write(raw)
print(f"Downloaded: {len(raw)/1024:.0f} KB")
```

### 第二步：读取数据

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

### 第三步：输出分析报告

直接输出文字报告，**不生成任何文件**。

---

## 14个因子含义

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

## 核心因子深入理解

**ar_factor（人气因子）：**
AR衡量最近一段时间里收盘价落在日内波动区间的相对位置。AR极低（≤20）说明沪深300持续收于日内低点——指数本身可能没跌多少，但买家每天都不愿意在日内高位接单，做多人气涣散，是短期人气涣散的明确信号。这类信号往往出现在下跌尾声或横盘磨底阶段。

**equity_bond_effective_factor（广义拥挤度）：**
这是整个体系里最有预警价值的反转因子。它综合了"赔率"（沪深300 PE的倒数）和"热度"（全市场成交金额）两个维度。读数高（≥80）意味着赔率低但成交活跃，是最危险的组合——历史上每次此处往往伴随重要顶部。

**leverage_factor（融资杠杆）：**
杠杆资金是市场里最敏感的一群人，借来的钱有成本必须快速获利。读数高（≥80）说明融资客大规模入场，市场亢奋，但一旦反转平仓踩踏会更剧烈。

**pcr_factor（期权多空因子）：**
PCR高（看跌期权远超看涨期权）反而是市场短期高点的预警——因为大量持有看跌期权的往往是对冲基金在"买保险"，当他们普遍感到需要保险时往往是市场最脆弱的时刻。

---

## 输出格式

```
【沪深300ETF情绪指数】
报告日期：{当日['Times']}

▎一、综合情绪指数
  当前读数：{sentiment_now:.1f} / 100
  档位：{档位}
  较昨日：{↑↓} {abs(change):.1f}（{变化解读}）

▎二、预警信号
  状态：{触发 / 未触发}
  {描述}

▎三、重点因子解读
  {选取3-5个最有解释力的因子，结合通俗含义+当前数值+市场含义，写出有判断的段落}

▎四、综合研判
  {综合读数+因子极值，给出有观点的结论}
```

---

## 档位表

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

## 较昨日变化解读

| 变化幅度 | 解读 |
|---|---|
| 上升 > 5 | 情绪大幅回暖，资金快速涌入 |
| 上升 1–5 | 情绪稳中向好，做多力量温和增强 |
| ±1 以内 | 情绪基本平稳 |
| 下降 1–5 | 情绪有所回落 |
| 下降 > 5 | 情绪快速降温 |

---

## 预警信号

**触发条件：** `sentiment_now >= 99` AND `sentiment_now < sentiment_prev`

**触发时：**
历史7次触发中6次在随后约20个交易日内出现超过10%回撤，平均最大回撤-13.77%，单次最大-32.46%（2017年末）。

**未触发时：**
- 读数 < 90：尚未进入过热区间，预警条件未满足
- 读数 ≥ 90 但仍在上升：处于历史高位，需等拐点
- 读数 ≥ 99 但未下降：需等待下降拐点确认

---

## 综合研判写法

模板：`综合读数{sentiment_now:.0f}（{档位}），{定性}。{最大亮点或风险}。{总体评价}。`

档位基调：
- ≥80：高位，回调风险大于上涨空间
- 65–79：偏热，可持有但不宜重仓
- 50–64：中性，方向不明
- 35–49：偏冷，控制仓位
- ≤34：历史低位，关注左侧机会
