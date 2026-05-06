---
name: index-sentiment-analyzer
description: |
  OpenClaw Skill for deep analysis of A-share CSI 300 ETF sentiment index indicators. Triggered when user asks about: (1) A-share market sentiment and sentiment index questions; (2) analysis of specific factors (MFI, OBV, MACD, RSI, etc.); (3) historical sentiment index trends, marginal changes, percentile levels; (4) factor logic questions; (5) market condition descriptions; (6) any quantitative indicators or market activity related topics. Provides 14 core factor interpretations, 6 group analyses, composite index levels, marginal change analysis, and warning signal detection.
---

# CSI 300 ETF Sentiment Index Analyzer

## Data File

- File: `assets/df_sentiment.xlsx`
- Range: 2016-01-04 to 2026-04-30 (~2500 trading days)
- Sheet: Sheet1

---

## Workflow

### Step 1: Load Excel Data

```python
import openpyxl
wb = openpyxl.load_workbook('assets/df_sentiment.xlsx', data_only=True)
ws = wb['Sheet1']
data = list(ws.iter_rows(values_only=True))
headers = data[0]
rows = data[1:]        # data rows (sorted by date ascending)
latest = rows[-1]      # latest trading day
prev = rows[-2]        # previous trading day (for拐点 detection)
wb.close()
```

### Step 2: Identify Question Type

| Type | Example |
|------|---------|
| A — Overall Status | "How is today's sentiment index?" / "What is the current market sentiment?" |
| B — Single Factor Follow-up | "What does XX factor mean?" / "What level is XX factor at recently?" |
| C — Warning Signal | "Any warning signals now?" / "Has the market topped?" |
| D — Factor Divergence | "Which factor group is most overheated?" / "Any divergence between factors?" |
| E — Historical Trend | "How has the sentiment index moved in the past month?" |

### Step 3: Calculate Key Indicators

```python
def row_to_dict(row):
    return dict(zip(headers, row))

cur = row_to_dict(latest)
pre = row_to_dict(prev)

sentiment_col = headers.index('sentiment_index_avg60_plus')

# Composite sentiment index
sentiment_now = cur['sentiment_index_avg60_plus']
sentiment_prev = pre['sentiment_index_avg60_plus']

#拐点 detection
is_100 = (sentiment_now == 100)
is_crossdown = (sentiment_now < sentiment_prev)

# 5-day slope
vals_all = [r[sentiment_col] for r in rows]
slope_5 = (vals_all[-1] - vals_all[-6]) / 5

# 6 major factor groups
groups = {
    'Basic Momentum': ['mfi_factor','leverage_factor','pcr_factor','ar_factor',
                       'br_factor','RSI_factor','daily_return_factor','equity_bond_effective_factor'],
    'Trend Strength': ['emascore_long_factor','signal_macd_factor'],
    'Market Activity': ['turnover_amount_factor'],
    'Short-term Momentum': ['highlow_factor'],
    'Fund Flow': ['obv_factor'],
    'Breadth Consistency': ['up_number_rate_factor'],
}
```

---

## Output Structure (Important)

### Overall Status (Type A)

Follow this format exactly. **Do not deviate, do not add extra sections.**

**Strictly prohibited:** generating "trading suggestions", "key contradictions", "data sources", or any content beyond the structure below.

```
【CSI 300 ETF Sentiment Index Overview】
📅 Data as of: {latest['Times']} (latest trading day with data)

━━━━━━━━━━━━━━━━━━
📊 Composite Sentiment Index
━━━━━━━━━━━━━━━━━━
Reading: {sentiment_now} / 100
Level: {level name} ({level explanation})

━━━━━━━━━━━━━━━━━━
📈 Marginal Change (Slope)
━━━━━━━━━━━━━━━━━━
5-day slope: {slope_sign}{slope_value} ({slope meaning})
vs Yesterday: {up/down} {diff_abs} ({change meaning})

━━━━━━━━━━━━━━━━━━
🔥 Warning Signal Check
━━━━━━━━━━━━━━━━━━
Warning status: {status}
(Trigger conditions: sentiment index at 100th percentile AND next-day sequential decline.
Both required: (1) today's reading=100, (2) tomorrow < today.)

{if triggered:
Trigger reason: sentiment index reading is 100, and higher than yesterday ({sentiment_prev}),
meaning market sentiment has reached historical extreme overheat. Historically there is an 85.71%
probability of a >10% drawdown following. Please heed risk.}

{if not triggered:
Non-trigger reason: current reading {sentiment_now} has not reached the 100th percentile,
or although at 100 has not yet shown a downward turning point (today={sentiment_now},
yesterday={sentiment_prev}), meaning current conditions do not meet the system's warning trigger.}

━━━━━━━━━━━━━━━━━━
📋 6 Major Factor Groups - Percentile Overview
━━━━━━━━━━━━━━━━━━
(Values in parentheses are group means; 0-20=oversold/20-40=below neutral/40-60=neutral/60-80=elevated/80-100=overheated)

Basic Momentum: mean={momentum_mean} — {overheated/neutral/below} ({one-sentence interpretation})
  └ Contains: Money Flow (MFI), Leverage, Options PCR, Activity (AR), Buy/Sell (BR), RSI,
               Daily Return, Equity-Bond Effectiveness — 8 factors

Trend Strength: mean={trend_mean} — {overheated/neutral/below} ({one-sentence interpretation})
  └ Contains: EMA Score, MACD Trend Divergence — 2 factors

Market Activity: mean={activity_mean} — {overheated/neutral/below} ({one-sentence interpretation})
  └ Contains: Turnover & Trading Activity — 1 factor

Short-term Momentum: mean={momentum_st_mean} — {overheated/neutral/below} ({one-sentence interpretation})
  └ Contains: High-Low Momentum (price high/low slope change) — 1 factor

Fund Flow: mean={flow_mean} — {overheated/neutral/below} ({one-sentence interpretation})
  └ Contains: On-Balance Volume (OBV, net money flow) — 1 factor

Breadth Consistency: mean={breadth_mean} — {overheated/neutral/below} ({one-sentence interpretation})
  └ Contains: Market Breadth (up/down stock ratio) — 1 factor

━━━━━━━━━━━━━━━━━━
🔍 Key Factor Tracking
━━━━━━━━━━━━━━━━━━
Most overheated: {hot_factor_name} = {hot_factor_value} ({plain explanation})
Most weak: {weak_factor_name} = {weak_factor_value} ({plain explanation})

Factor divergence: {divergent/consistent} ({divergence note})
```

---

### Factor Detail (Type B — Single Factor Follow-up)

For abstract factors, provide plain-language explanations:

**OBV (On-Balance Volume Factor)**:
> OBV combines volume with price movement. When close > yesterday, add today's volume as positive money flow; when close < yesterday, add as negative flow. OBV shows "where the money flows" — if the index makes a new high but OBV doesn't follow, money is pulling back, which is a warning signal. In this system, obv_factor uses the 90-day historical percentile of OBV change. Higher values indicate stronger medium-term money inflow.

**MFI (Money Flow Index Factor)**:
> MFI is like RSI but incorporates volume. Typical Price = (High + Low + Close) / 3. When typical price rises, multiply by volume = money inflow; when falls = outflow. MFI above 80 means money inflow has reached historical extreme — market may be short-term overheated; below 20 means selling pressure fully released, possibly near a bottom.

**MACD (Trend Divergence Factor)**:
> MACD consists of DIF (fast line) and DEA (slow line). MACD histogram = DIF - DEA. When MACD turns from negative to positive and DIF is above zero, short-term upward momentum is strengthening. In this system, signal_macd_factor tracks MACD momentum direction. Higher values mean a healthier uptrend.

**RSI (Relative Strength Index Factor)**:
> RSI measures the ratio of sum of up-day gains to sum of down-day losses, reflecting the relative strength of price rises vs. falls. RSI above 70 = overbought (stretched higher), below 30 = oversold. This system uses multi-period RSI fusion to reduce false signals.

**Equity-Bond Effectiveness Factor**:
> This factor combines two dimensions: the inverse P/E of CSI 300 (E/P, the "yield" ratio — higher means stocks are cheaper/more attractive vs. bonds) and total market trading volume (more active = more crowded). It subtracts the 5-day MA from the 60-day MA of this combined signal. Smaller values mean more crowding. Values above 80 indicate extreme crowding — one of the most important reversal warning signals.

**EMA Score Long Factor**:
> This factor evaluates the relationship between closing price and multiple moving averages, plus the direction of each MA. Signals include: whether close is above the 30-day MA, whether short-term MAs are above long-term MAs, whether MAs are sloping upward, etc. Higher scores mean more complete MA bullish alignment and stronger trend.

**High-Low Momentum Factor**:
> This factor judges momentum direction by comparing the slope of 10-day highs vs. the slope of 10-day lows. In an uptrend, if the high slope exceeds the low slope, buying pressure is strong. In a downtrend, if lows are not making new lows, money is supporting the market. This factor changes quickly — good for capturing short-term momentum shifts.

---

## Factor Name Quick Reference

| Excel Column | Name | Group | Plain Explanation |
|---|---|---|---|
| sentiment_index_avg60_plus | Composite Sentiment Index | Final Output | Equal-weighted 6-group fusion percentile |
| close_price | CSI 300 ETF Close Price | Base Price | Index price, not used in factor calculation |
| obv_factor | On-Balance Volume | Fund Flow | Where money flows |
| mfi_factor | Money Flow Index | Basic Momentum | Money inflow intensity |
| leverage_factor | Leverage Factor | Basic Momentum | How hot leveraged trading is |
| pcr_factor | Options Put/Call Ratio | Basic Momentum | Hedging demand strength |
| turnover_amount_factor | Turnover Activity | Market Activity | Market/ETF turnover heat |
| ar_factor | Activity Ratio | Basic Momentum | Open price position within daily range |
| br_factor | Buy/Sell Ratio | Basic Momentum | Holders' tolerance for volatility |
| emascore_long_factor | EMA Score Long | Trend Strength | MA bullish alignment strength |
| signal_macd_factor | MACD Signal | Trend Strength | MACD momentum direction |
| highlow_factor | High-Low Momentum | Short-term Momentum | Price high/low slope momentum |
| RSI_factor | Relative Strength Index | Basic Momentum | Overbought/oversold reference |
| daily_return_factor | Daily Return | Basic Momentum | Short-term cumulative change |
| up_number_rate_factor | Market Breadth | Breadth Consistency | Up/down stock ratio across market |
| equity_bond_effective_factor | Equity-Bond Effectiveness | Basic Momentum | Market crowding level |

---

## 6 Major Factor Groups

```python
Basic Momentum = [mfi_factor, leverage_factor, pcr_factor, ar_factor,
                   br_factor, RSI_factor, daily_return_factor, equity_bond_effective_factor]
Trend Strength = [emascore_long_factor, signal_macd_factor]
Market Activity = [turnover_amount_factor]
Short-term Momentum = [highlow_factor]
Fund Flow = [obv_factor]
Breadth Consistency = [up_number_rate_factor]
```

---

## Key Threshold Reference

| Factor | Overheated (>) | Oversold (<) | Plain Meaning |
|---|---|---|---|
| mfi_factor | 80 | 20 | Historical extreme inflow / ice point |
| leverage_factor | 80 | 20 | Hottest / coldest leveraged trading |
| pcr_factor | 80 | 20 | Extreme / weak hedging demand |
| ar_factor | 80 | 20 | Persistent daily high / low closes |
| br_factor | 80 | 20 | Strongest confidence / panic selling |
| RSI_factor | 80 | 20 | Overbought / oversold |
| equity_bond_effective_factor | 80 | 20 | Extreme crowding / low crowding + high yield |
| obv_factor | 80 | 20 | Sustained net inflow / net outflow |
| emascore_long_factor | 80 | 20 | Perfect MA bullish / bearish alignment |
| signal_macd_factor | 80 | 20 | MACD strongest / weakest |
| highlow_factor | 80 | 20 | Strongest momentum / reversal signal |
| turnover_amount_factor | 80 | 20 | Hottest / coldest trading |
| up_number_rate_factor | 80 | 20 | Widespread up / down |
| daily_return_factor | 80 | 20 | Historical high / low short-term gain |

---

## Reference Documents

- Factor definitions and logic: `references/factor_definition.md`
- Warning rules and level interpretation: `references/signal_rules.md`
