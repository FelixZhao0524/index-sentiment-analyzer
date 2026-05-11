# 沪深300ETF情绪指数深度分析工具

> 触发词：A股情绪、沪深300情绪、市场情绪、ETF情绪、情绪指数、沪深300今日情绪、当前市场情绪

---

## 分析流程

### 第一步：读取飞书数据

调用 `feishu_sheet`（只读最后 20 行，速度快）：

```
action: read
spreadsheet_token: J2yUsT52RhOCdEtiVQKchkiin3f
range: Sheet1!A2490:T2510
```

### 第二步：更新本地缓存 Excel

用 `pandas` 将返回的最新行追加到 `assets/df_sentiment.xlsx`：

```python
import pandas as pd
from openpyxl import load_workbook

df_cache = pd.read_excel('assets/df_sentiment.xlsx', engine='openpyxl')
new_rows = pd.DataFrame([...], columns=df_cache.columns)

# 去重：Times 已存在则跳过
for _, row in new_rows.iterrows():
    if row['Times'] not in df_cache['Times'].values:
        df_cache = pd.concat([df_cache, pd.DataFrame([row])], ignore_index=True)

df_cache.to_excel('assets/df_sentiment.xlsx', index=False)
```

**如果 `assets/df_sentiment.xlsx` 不存在**，则改用全量读取：

```
range: Sheet1!A1:T2510
```

读取后保存为 `assets/df_sentiment.xlsx`，之后都用增量追加逻辑。

### 第三步：从本地 Excel 读取数据

```python
df = pd.read_excel('assets/df_sentiment.xlsx', engine='openpyxl')
df = df.sort_values('Times').reset_index(drop=True)
当日 = df.iloc[-1]
前日 = df.iloc[-2]
```

### 第四步：输出分析报告

从当日行读取 `sentiment_index_avg60_plus` 及 14 个因子值，直接输出报告，**不生成任何文件**。

---

## 输出格式（严格按此结构）

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

## 14个因子通俗参考

| 因子 | 通俗含义 | 高值（≥80） | 低值（≤20） |
|------|----------|------------|------------|
| obv_factor | 钱往哪里流 | 主力净流入 | 主力净流出 |
| mfi_factor | 买盘有多旺 | 资金流入极强 | 卖压充分释放 |
| leverage_factor | 融资杠杆有多热 | 杠杆资金大规模入场 | 融资客撤退 |
| pcr_factor | 对冲需求有多强 | 看跌期权远超看涨 | 看涨远超看跌 |
| turnover_amount_factor | 市场换手热度 | 成交极度活跃 | 成交极度萎缩 |
| ar_factor | 收盘在日内高位还是低位 | 收于日内高点 | 收于日内低点 |
| br_factor | 持仓者信心强弱 | 高位强势承接 | 恐慌抛压释放 |
| RSI_factor | 超买超卖 | 超买明显 | 超卖明显 |
| daily_return_factor | 短期累计涨跌 | 涨幅历史高位 | 跌幅历史低位 |
| equity_bond_effective_factor | 市场拥挤程度 | 极度拥挤，最危险反转信号 | 低拥挤高赔率 |
| emascore_long_factor | 均线多头排列强度 | 多头向上 | 空头向下 |
| signal_macd_factor | MACD动量方向 | 多头信号强 | 空头主导 |
| highlow_factor | 高低价斜率谁更强 | 买方主导 | 动量衰竭 |
| up_number_rate_factor | 全市场涨跌家数比 | 普涨注意踩踏 | 普跌恐慌主导 |

---

## 重点因子写法参考

**ar_factor = 10（人气因子极低）：**
> AR衡量最近收盘价落在日内区间的相对位置。AR极低说明沪深300持续收于日内低点，买家不愿在高位接单，做多人气涣散，常出现在下跌尾声或横盘磨底阶段。

**equity_bond_effective_factor = 95（拥挤度极高）：**
> 衡量市场拥挤程度——读数95意味着赔率低但参与者众多，历史上每次此处往往伴随重要顶部。低赔率+高成交是最危险的反转信号。

---

## 综合研判写法

模板：`综合读数{sentiment_now:.0f}（{档位}），{定性}。{最大亮点或风险}。{总体评价}。`

档位基调：≥80防御为主 / 65-79观察拐点 / 50-64等待信号 / 35-49控制仓位 / ≤34关注左侧机会
