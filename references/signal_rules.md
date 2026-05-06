# Signal Interpretation Rules

This document defines interpretation rules for the sentiment index and individual factor signals, including warning conditions, level meanings, marginal change interpretation, and extreme scenario detection.

---

## 1. Composite Sentiment Index (sentiment_index_avg60_plus)

### Core Meaning

`sentiment_index_avg60_plus` is the equal-weighted composite score of 6 major factor groups, processed through a 180-day percentile rank normalization, with a value range of 0-100.

Equal-weight fusion of 6 major groups:
```
Composite Factor = (Basic Momentum + Trend Strength + Market Activity + Short-term Momentum + Fund Flow + Breadth Consistency) / 6
Composite_60d_ma -> rolling(60)
sentiment_index_avg60_plus = 180-day percentile rank of Composite_60d_ma
```

> Note: sentiment_index_avg60_plus output is between 0-100, reflecting the current sentiment's percentile position relative to the last 180 trading days.

---

## 2. Core Warning Rules (Most Important)

### Warning Trigger Conditions (Both Required)

1. `sentiment_index_avg60_plus == 100` (reaching historical highest percentile)
2. **Next-day value declining sequentially** (turning point appears)

```
Warning Signal = (Today's_sentiment == 100) AND (Today's_sentiment > Tomorrow's_sentiment)
```

### Warning Meaning

When a warning fires, it means market trading has become extremely crowded, or there is excessive irrational optimism. This is the highest historical win-rate risk warning signal in the system.

### Historical Statistics (January 2017 — August 2025)

| Metric | Value |
|---|---|
| Total warning count | 7 |
| Warnings followed by >10% drawdown | 6 |
| **Warning win rate** | **85.71%** |
| Average max drawdown | -13.77% |
| Largest single drawdown | -32.46% (late 2017) |
| Average lead time after warning | ~19 trading days |
| Average drawdown duration | ~101 trading days |
| Large drawdown capture rate | **100%** (all drawdowns >20% were warned in advance) |

---

## 3. Sentiment Index Level Interpretation

### Absolute Position (Current Reading)

| Percentile Range | Status | Color | Meaning |
|---|---|---|---|
| 100 + turning point | 🔴 **Warning Signal** | Red | Extreme overheat; reduce position opportunistically |
| 90-99 | 🟠 Extremely Optimistic | Orange | Approaching overheat; watch closely |
| 80-89 | 🟠 Excessively Optimistic | Orange | Possibly overheating; take profits |
| 70-79 | 🟡 Optimistic-Warm | Yellow | Good sentiment; can hold positions |
| 60-69 | 🟡 Warm | Yellow | Neutral-bullish |
| 50-59 | 🟢 Neutral-Warm | Green | Normal range |
| 40-49 | 🟢 Neutral | Green | Normal range |
| 30-39 | 🔵 Cool | Blue | Neutral-weak |
| 20-29 | 🔵 Pessimistic-Cool | Blue | Weak sentiment |
| 10-19 | 🔵 Excessively Pessimistic | Blue | Near ice point; watch for opportunity |
| 0-9 | 🔵 Extremely Pessimistic | Blue | Ice point; sentiment extreme |

---

## 4. Marginal Change Interpretation (Slope Analysis)

Marginal change is a core tool for judging sentiment trend direction, compensating for the limitation that absolute position can only show "cold/hot" but not "direction."

### Calculation Method

```python
# 5-day slope (short-term marginal change)
slope_5 = sentiment_index_avg60_plus.diff(5) / 5

# 20-day slope (medium-term marginal change)
slope_20 = sentiment_index_avg60_plus.diff(20) / 20

# Difference between 5-day MA and 20-day MA (judge directional health)
ema_5 = sentiment.rolling(5).mean()
ema_20 = sentiment.rolling(20).mean()
ema_cross = ema_5 - ema_20
```

### Marginal Change Levels

| slope_5 | Direction | Meaning |
|---|---|---|
| > +2/day | Strong Warming | Sentiment warming rapidly; watch for short-term overheat |
| +1 ~ +2/day | Moderate Warming | Sentiment gradually improving |
| 0 ~ +1/day | Steady Slight Rise | No clear direction; slow change |
| -1 ~ 0/day | Steady Slight Fall | No clear direction; slow contraction |
| -2 ~ -1/day | Moderate Cooling | Sentiment gradually weakening |
| < -2/day | Strong Cooling | Sentiment ebbing rapidly |

### EMA Crossover Signals (EMA5 vs EMA20)

| Crossover Type | Signal | Meaning |
|---|---|---|
| EMA5 crosses above EMA20 | 🟢 Golden Cross | Medium-term trend shifting from weak to strong; bullish signal |
| EMA5 crosses below EMA20 | 🔴 Death Cross | Medium-term trend shifting from strong to weak; bearish signal |
| EMA5 above EMA20 and both rising | 🟢 Strong Bullish | Trend healthy; hold signal |
| EMA5 above EMA20 but both falling | 🟡 Bullish Fading | Uptrend weakening; stay alert |
| EMA5 below EMA20 and both falling | 🔴 Strong Bearish | Downtrend dominating |
| EMA5 below EMA20 but both rising | 🟡 Bearish Fading | Downtrend weakening; bottom building |

### Combined Signal Matrix

| | Absolute Position High (>60) | Absolute Position Mid (40-60) | Absolute Position Low (<40) |
|---|---|---|---|
| **Slope Up** | 🟡 Overheat + Warming = Watch for spike-then-pullback | 🟢 Neutral + Warming = Trend improving | 🔵 Oversold + Warming = Bottom rebound opportunity |
| **Slope Steady** | 🟠 Overheat + Steady = Hold but don't chase | 🟢 Neutral = Normal holding | 🔵 Oversold + Steady = Wait for signal |
| **Slope Down** | 🔴 Overheat + Cooling = **Warning reduce position** | 🔵 Neutral + Cooling = Cautiouswait-and-watch | 🔵 Oversold + Cooling = Bottom deepening |

---

## 5. 10-Class Sentiment Scenario Matrix

Combining absolute position with marginal change, market sentiment is classified into 10 scenarios; 4 are extreme scenarios requiring close attention:

```
            | Marginal Up  | Marginal Steady | Marginal Down
High (>80)  | 1.Optimism Accelerating | 2.Optimism Flattening | 3.Overheat Warning🔥 <- Key Warning
Mid (40-80) | 4.Sentiment Recovery | 5.Sentiment Stable | 6.Sentiment Cooling
Low (<40)   | 7.Rebound Opportunity | 8.Bottom Building | 9.Panic Brewing🔥 <- Key Warning
```

### 4 Extreme Scenarios Explained

**Scenario 1: Excessively Optimistic + Warming (High Absolute + Slope Up)**
- Characteristics: Sentiment index above 80 and continuing to climb
- Meaning: Market surging rapidly with euphoric upward movement
- Warning Level: ⚠️⚠️⚠️ (Very High)
- Action: Gradually reduce positions; do not chase

**Scenario 3: Excessively Optimistic + Cooling (High Absolute + Slope Down)**
- Characteristics: Sentiment index above 80 but has already shown a turning point
- Meaning: Stampede warning after market overheat
- Warning Level: ⚠️⚠️⚠️⚠️ (Very High — core warning scenario of this system)
- Action: **Reduce positions immediately** — this is the historical high win-rate warning scenario

**Scenario 9: Excessively Pessimistic + Cooling (Low Absolute + Slope Down)**
- Characteristics: Sentiment index below 40 and continuing to decline
- Meaning: Market entering panic sentiment with rapid downside
- Warning Level: ⚠️⚠️⚠️ (High)
- Action: Do not panic-sell; watch for sentiment repair signals

**Scenario 7: Excessively Pessimistic + Warming (Low Absolute + Slope Up)**
- Characteristics: Sentiment index below 40 but has already shown a turning point
- Meaning: Local bottom-building and warming phase
- Warning Level: 🟢 (Opportunity Signal)
- Action: Gradually build positions; wait for trend confirmation

---

## 6. Sub-Group Sentiment Coordination Judgement

Beyond the composite sentiment index, also monitor divergence across the 6 major factor groups:

| Divergence Type | Characteristics | Meaning |
|---|---|---|
| **Trend-Aligned** | All 6 groups moving in same direction (all high or all low) | Sentiment extreme; high probability of continued directional move |
| **Divergent** | Some groups high, others low | High market disagreement; high probability of range-bound oscillation |
| **Leading Divergence** | Fund flow factors (obv/mfi/leverage) diverging from price factors | Warning signal; potential turning point |
| **Breadth Divergence** | up_number_rate_factor diverging from composite index | Warning signal; rising/falling stock count inconsistent with index |

**Best Long Signal:** Composite sentiment index low + trend factors (e.g. emascore_long_factor, signal_macd_factor) simultaneously issuing golden crosses + fund flow factors starting to rebound

**Best Short/Warning Signal:** Composite sentiment index = 100 + turning point appears + multiple fund flow factors (pcr/leverage/turnover) simultaneously at highs

---

## 7. Historical Typical Scenarios (For Analogizing Current Market)

When judging current market status, refer to these historical archetypes:

1. **Sentiment Ice Point Rebound (<20, rising from lows)**: Reference Feb 2020, Apr 2022, Jan 2024
2. **Sentiment Overheat Warning (=100 + turning point)**: Reference Nov 2017, Dec 2021, Jul 2022, Feb 2023
3. **Sentiment Mid-Range Oscillation (40-60, direction unclear)**: Reference most of 2019, second half of 2023
4. **Sentiment Trending Upward (>60, slope up)**: Reference Jan-Apr 2019, Jul-Dec 2020, Sep-Oct 2024
