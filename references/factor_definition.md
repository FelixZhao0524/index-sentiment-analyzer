# Factor Definition Reference

This document defines the meaning, calculation logic, threshold interpretation, and overheating/oversold signal criteria for all 14 core factors in the sentiment index system.

---

## Framework Overview

The composite sentiment index is constructed by equal-weighting 6 major factor groups, then applying a 180-day percentile rank normalization, outputting a 0-100 composite index called `sentiment_index_avg60_plus`.

6 Major Factor Groups:

| Group | Factors | Interpretation |
|---|---|---|
| Basic Momentum | mfi / leverage / pcr / ar / br / RSI / daily_return / equity_bond_effective | Comprehensive assessment of current sentiment position and directional tone via price-volume, leverage, and derivatives |
| Trend Strength | emascore_long / signal_macd | Candle patterns and trend indicators to assess trend stability and short-term strength |
| Market Activity | turnover_amount | Total market trading volume and turnover rate; activity is the foundation of sustained sentiment |
| Short-term Momentum | highlow | Short-term index special patterns; monitors sentiment explosive force |
| Fund Flow | obv | OBV anomalies linked to major player behavior |
| Breadth Consistency | up_number_rate | Market-wide up/down stock ratio; confirms sentiment breadth |

---

## Factor Details

---

### 1. obv_factor (On-Balance Volume Factor)

**Group:** Fund Flow

**Source Indicator:** OBV (On-Balance Volume)

**Calculation:**
```
OBV_t = OBV_{t-1} + (Close_t - Close_{t-1}) * Volume_t
(close up = positive accumulation, down = negative accumulation)
obv_change = OBV_t - OBV_{t-90} (90-day change)
obv_factor = 180-day percentile rank of obv_change
```

**Core Meaning:** OBV reflects the dynamic balance of bullish/bearish energy. An OBV breakout above prior highs means major players are continuously accumulating, reinforcing price; an OBV breakdown below prior lows means bearish momentum dominates and sentiment turns cautious. The 90-day change captures medium-term money flow direction.

**Overheating Signal (obv_factor > 80):**
- Money continuously flowing in, abundant upward momentum
- Major players pushing prices higher, market sentiment euphoric
- **Risk:** Upward momentum may be exhausting; chasing risk is high

**Oversold Signal (obv_factor < 20):**
- Money continuously flowing out, major players retreating
- Market sentiment at ice point, bears in control
- **Opportunity:** Panic selling fully released; rebound may be forming

**Marginal Change Interpretation:**
- obv_factor slope turns from negative to positive → Money re-entering, bullish signal
- obv_factor slope turns from positive to negative → Money accelerating exit, bearish signal
- obv_factor high-level钝化 then first decline → Warning signal (major players may have already distributed)

---

### 2. mfi_factor (Money Flow Index Factor)

**Group:** Basic Momentum

**Source Indicator:** MFI (Money Flow Index)

**Calculation:**
```
Typical Price Typ = (High + Low + Close) / 3
Money Flow MF = Typ * Volume
PMF = Sum of positive money flow rolling(30 days) (days when Typ rises)
NMF = Sum of negative money flow rolling(30 days) (days when Typ falls)
MFI = 100 - 100 / (PMF/NMF + 1)
mfi_factor = 180-day percentile rank of MFI
```

**Core Meaning:** MFI combines price and volume to measure the intensity of money inflow/outflow. It is an effective leading indicator for capturing market sentiment overheating and recovery.

**Overheating Signal (mfi_factor > 80):**
- Money inflow intensity at extreme levels
- Investor sentiment in the overheat zone
- **Warning:** Profit-taking pressure increasing; market may be hitting a phase top

**Oversold Signal (mfi_factor < 20):**
- Money outflow pressure fully released
- Market sentiment entering the ice point zone
- **Opportunity:** Sentiment repair brewing; window for bottom-building positions

**Marginal Change Interpretation:**
- mfi_factor rebounds quickly from lows → Money actively bottom-fishing, bullish signal
- mfi_factor flattening at highs → Momentum exhaustion warning
- mfi_factor turns from high to low → Sentiment shifting from hot to cold, confirms downtrend

---

### 3. leverage_factor (Leverage Factor)

**Group:** Basic Momentum

**Source Indicator:** Margin Buying Amount

**Calculation:**
```
Margin_Buy_Amount_5d_ma -> rolling(5)
leverage_factor = 180-day percentile rank of Margin_Buy_Amount_5d_ma
```

**Core Meaning:** Leveraged investors' behavior is a key amplifier of market sentiment. Margin buying volume reflects leveraged money's willingness to go long. Its extreme values often correspond to sentiment phase tops (excessive optimism) or bottoms (excessive pessimism).

**Overheating Signal (leverage_factor > 80):**
- Leveraged money flooding in at scale
- Market may be entering irrational optimism
- **Warning:** Deleveraging risk accumulating; reversal can trigger severe cascade selling

**Oversold Signal (leverage_factor < 20):**
- Leveraged money severely contracted
- Market sentiment extremely pessimistic
- **Opportunity:** Can wait for bottom-building positions in this zone

**Marginal Change Interpretation:**
- leverage_factor climbing rapidly → Leveraged money accelerating entry, sentiment warming
- leverage_factor pulling back from highs → Margin buyers starting to exit, sentiment cooling
- leverage_factor making new low then flattening → Panic may be bottoming

---

### 4. pcr_factor (Options Put/Call Ratio Factor)

**Group:** Basic Momentum

**Source Indicator:** Options Open Interest PCR (Put/Call Ratio)

**Calculation:**
```
PCR = Put Option Open Interest / Call Option Open Interest
pcr_factor = 180-day percentile rank of PCR
```

**Core Meaning:** PCR reflects how bearish/bullish options market investors are on the outlook. High PCR means investors holding large put positions for downside hedging — often corresponds to short-term market highs; low PCR reflects optimism prevailing.

**Overheating Signal (pcr_factor > 80):**
- Put open interest far exceeds call open interest
- Hedging demand surges, market cautious sentiment thickens
- **Warning:** Historical pattern shows this zone frequently corresponds to short-term local highs

**Oversold Signal (pcr_factor < 20):**
- Call open interest far exceeds put open interest
- Market excessively optimistic, chasing sentiment euphoric
- **Warning:** Optimism may be overextended; reversal risk building

**Marginal Change Interpretation:**
- pcr_factor rising rapidly from lows → Investor hedging awareness strengthening, bearish signal
- pcr_factor pulling back from highs → Market tension easing, but not necessarily turning bullish
- pcr_factor diverging from price (price up + PCR up) → Strong warning signal

---

### 5. turnover_amount_factor (Turnover Activity Factor)

**Group:** Market Activity

**Source Indicator:** Total Market Trading Amount + Turnover Rate

**Calculation:**
```
Trading_Amount_5d_ma -> rolling(5)
tot_amount_percentile = 180-day percentile rank of Trading_Amount_5d_ma
turnover_rate_percentile = 180-day percentile rank of Turnover_Rate_5d_ma
turnover_amount_factor = (tot_amount_percentile + turnover_rate_percentile) / 2
```

**Core Meaning:** High turnover and volume are correlated with investor excitement. When trading activity reaches historical highs, it often means the market is filled with excessively optimistic irrational sentiment. Extremely low activity reflects market lethargy and sentiment ice points.

**Overheating Signal (turnover_amount_factor > 80):**
- Market abnormally active, turnover extremely high
- Group speculation sentiment evident
- **Warning:** Overcrowding risk; when sentiment reverses the selloff pressure is large

**Oversold Signal (turnover_amount_factor < 20):**
- Market trading severely shrunk
- Investor participation willingness at ice point
- **Opportunity:** Lethargic markets often harbor bottom reversals

**Marginal Change Interpretation:**
- turnover_amount_factor spiking → Funds flooding in, sentiment warming rapidly
- turnover_amount_factor consecutively declining at highs → Activity decaying, sentiment ebbing
- turnover_amount_factor gently expanding from lows → Money slowly entering, bottom-building signal

---

### 6. ar_factor (Activity Ratio Factor)

**Group:** Basic Momentum

**Source Indicator:** AR (Activative Ratio)

**Calculation:**
```
AR = Sum(High - Open) / Sum(Open - Low), rolling(60 days)
ar_factor = 180-day percentile rank of AR
```

**Core Meaning:** AR measures buying pressure's effect on the price center through the ratio of open price to intraday price range. High AR means price persistently closing in the upper intraday range (strong bullish candles), with strong market chasing momentum; low AR means sellers in control, price center shifting down.

**Overheating Signal (ar_factor > 80):**
- Price persistently closing at intraday highs, buying pressure extremely strong
- Market entering a frantic chasing phase
- **Warning:** May be short-term overheated; risk of pullback after spike

**Oversold Signal (ar_factor < 20):**
- Price persistently closing at intraday lows, sellers in control
- Investor participation willingness at ice point
- **Opportunity:** May rebound after panic selling exhausts itself

**Marginal Change Interpretation:**
- ar_factor rebounding quickly from lows → Buying pressure reasserting dominance
- ar_factor flattening at highs → Momentum possibly exhausting
- ar_factor diverging from price (price down but AR rising) → Warning signal

---

### 7. br_factor (Buy/Sell Ratio Factor)

**Group:** Basic Momentum

**Source Indicator:** BR (Bulls/Bears Ratio)

**Calculation:**
```
BR = Sum(High - PrevClose) / Sum(PrevClose - Low), rolling(60 days)
br_factor = 180-day percentile rank of BR
```

**Core Meaning:** BR focuses on position-holders' tolerance for price fluctuations, quantifying investor confidence by the relative position of close price within the fluctuation range. High BR means funds maintaining strong support at current levels, but position risk accumulating rapidly; low BR means panic selling fully released.

**Overheating Signal (br_factor > 80):**
- Funds still strongly supporting at high levels, position confidence strong
- Market sentiment extremely optimistic
- **Risk:** Watch for "momentum decay" signal (price up but BR stepping down)

**Oversold Signal (br_factor < 20):**
- Panic selling pressure fully released
- Market entering sentiment repair window
- **Opportunity:** Watch for "sentiment resilience" signal (price plunging but BR holding up)

**Marginal Change Interpretation:**
- br_factor trending lower at highs → Funds' position confidence loosening, bearish
- br_factor flattening then rebounding from lows → Panic bottoming, bounce likely
- br_factor diverging from price → Major player behavior signal, deserves close attention

---

### 8. emascore_long_factor (EMA Score Long Factor)

**Group:** Trend Strength

**Source Indicator:** Multi-period Moving Averages (MA5/10/20/30/60/120 days)

**Calculation:**
```
Signal = Sum(multi-period MA long scores), rolling(60 days)
emascore_factor = 180-day percentile rank of Sum(Signal)
emascore_long_factor = 30-day rolling mean of emascore_factor
```

**Individual MA Signal Definitions:**
- signal0: Close > MA30 → 0.1 points
- signal1: MA5 > MA20 → 0.1 points
- signal2: MA10 > MA20 → 0.1 points
- signal3: MA10 > MA30 → 0.1 points
- signal4: MA10 > MA60 → 0.1 points
- signal5: MA10 > MA120 → 0.1 points
- signal6: MA20 > MA60 → 0.1 points
- signal7: MA20 trending up (today's MA20 > yesterday's MA20) → 0.1 points
- signal8: MA60 trending up (today's MA60 > yesterday's MA60) → 0.1 points
- signal9: SAR trend signal (Close > SAR) → 0.1 points

**Core Meaning:** The EMA Score factor comprehensively evaluates the position of price relative to multiple moving averages and the direction of those averages. It is a core tool for judging market trend strength.

**Level Interpretation:**

| Percentile | Signal | Meaning |
|---|---|---|
| 80-100 | 🟢 Bullish | MAs in bullish alignment, trend up |
| 60-80 | 🟡 Cautiously Bullish | Most MAs up, but monitor sustainability |
| 40-60 | 🟠 Neutral | Balanced, trend unclear |
| 20-40 | 🔴 Cautiously Bearish | Most MAs down, trend weak |
| 0-20 | 🔴 Bearish | MAs in bearish alignment, trend down |

**Marginal Change Interpretation:**
- emascore_long_factor in uptrend → Trend strengthening, hold longs
- emascore_long_factor declining from highs → Trend exhaustion, reduce position signal
- emascore_long_factor golden cross from lows → Trend reversing, bullish signal

---

### 9. signal_macd_factor (Trend Divergence Factor)

**Group:** Trend Strength

**Source Indicator:** MACD (Moving Average Convergence Divergence)

**Calculation:**
```
EMA1 = 10-day EMA of Close
EMA2 = 25-day EMA of Close
DIFF = EMA1 - EMA2
DEM = 9-day MA of DIFF
MACD = DIFF - DEM

signal7 = (MACD_today - MACD_yesterday > 0) ? 1 : 0
signal8 = (MACD_today - MACD_yesterday > 0 AND DIFF > 0) ? 1 : 0
signal9 = (DIFF > 0) ? 1 : 0

signal8_sum = Sum signal8, rolling(20 days)
signal9_sum = Sum signal9, rolling(20 days)

signal_macd_factor = 180-day percentile rank of ((signal8_sum + signal9_sum)/2)
signal_macd_factor = 20-day rolling mean of signal_macd_factor
```

**Core Meaning:** MACD is a classic trend-following indicator. signal7 judges MACD momentum direction; signal8 confirms trend strength (MACD up AND DIFF > 0 = healthy uptrend); signal9 reflects average price momentum direction. The three are fused and smoothed to reduce noise.

**Overheating Signal (signal_macd_factor > 80):**
- MACD bullish signals strong
- DIFF continuously expanding above zero line
- Trend continuity good, but watch for high-level钝化

**Oversold Signal (signal_macd_factor < 20):**
- MACD bearish signals dominant
- DIFF running below zero line
- Trend down, but may be brewing bottom divergence

**Marginal Change Interpretation:**
- signal_macd_factor turning from low to high + DIFF crossing above zero → Trend confirmed up, long signal
- signal_macd_factor declining at highs (but DIFF still above zero) → Upward momentum fading, caution
- signal_macd_factor turning from high to low + DIFF crossing below zero → Trend confirmed down, exit signal
- MACD positive divergence with price (price makes new low but MACD does not) → Strong bottom-fishing signal

---

### 10. highlow_factor (High-Low Momentum Factor)

**Group:** Short-term Momentum

**Source Indicator:** 10-day slope comparison of High/Low/Close prices

**Calculation:**
```
Uptrend:
  K_max = (High_{t-1} - High_{t-2}) / High_{t-2}
  K_min = (Low_{t-1} - Low_{t-2}) / Low_{t-2}
  Signal = 1 (if Close up AND K_max > K_min)

Downtrend:
  Signal = 1 (if Close down AND K_min < K_max)
  (Low slope relatively steeper = bottom supported)

highlow_signal = Sum Signal, rolling(20 days)
highlow_factor = 180-day percentile rank of highlow_signal
```

**Core Meaning:** The high-low momentum factor judges current momentum strength by capturing relative changes in high and low price slopes. In uptrends, if the high price slope leads the low price slope → uptrend momentum healthy; in downtrends, if the low price doesn't make new lows → bottom support, potential reversal.

**Overheating Signal (highlow_factor > 80):**
- Consecutive 20 days mostly showing strong momentum characteristics
- In uptrends: highs continuously making new highs with increasing slope → extreme momentum
- **Note:** This factor changes frequently; may oscillate in range-bound markets

**Oversold Signal (highlow_factor < 20):**
- Consecutive 20 days mostly showing weak momentum or reversal characteristics
- In downtrends: lows continuously making new lows
- **Opportunity:** After bottom formation, if highlow_factor stabilizes and rebounds, it预示着 reversal

**Marginal Change Interpretation:**
- highlow_factor rising rapidly from lows → Momentum shifting from weak to strong, short-term long signal
- highlow_factor declining from highs → Short-term momentum fading, may consolidate or pull back
- highlow_factor first rising after low-level钝化 → Worth watching closely; may be precursor to trend reversal

---

### 11. RSI_factor (Relative Strength Index Factor)

**Group:** Basic Momentum

**Source Indicator:** RSI (Relative Strength Index)

**Calculation:**
```
Up-day gains / Down-day absolute losses -> build change sequence
RSI1 = 12-period RSI
RSI2 = 25-period RSI
RSI3 = 40-period RSI
signal10_RSI = Sum RSI1, rolling(5 days)
RSI_factor = 180-day percentile rank of signal10_RSI
```

**Core Meaning:** RSI measures the speed and magnitude of price changes. It is a classic indicator for judging market overbought/oversold conditions. This system uses multi-period RSI fusion to reduce false signals from single-period indicators.

**Overheating Signal (RSI_factor > 80):**
- RSI at historical highs, market overbought
- Investor sentiment too aggressive
- **Warning:** May face short-term pullback pressure

**Oversold Signal (RSI_factor < 20):**
- RSI at historical lows, market oversold
- Investor sentiment excessively pessimistic
- **Opportunity:** Oversold zone is often a bottom-building opportunity

**Marginal Change Interpretation:**
- RSI_factor rebounding from lows + breaking through 50 midpoint → Medium-term rebound confirmed
- RSI_factor pulling back from highs → Momentum fading, reduce position signal
- RSI negative divergence with price (price makes new high but RSI does not) → Strong warning signal
- RSI positive divergence with price (price makes new low but RSI does not) → Bottom-fishing signal

---

### 12. daily_return_factor (Daily Return Factor)

**Group:** Basic Momentum

**Source Indicator:** Moving average of daily returns

**Calculation:**
```
Daily Return = (Close - PrevClose) / PrevClose
Daily_Return_30d_ma -> rolling(30)
daily_return_factor = 180-day percentile rank of Daily_Return_30d_ma
```

**Core Meaning:** Reflects the index's short-term (30-day) average return level — the most direct indicator of short-term market performance.

**Overheating Signal (daily_return_factor > 80):**
- Short-term cumulative gain at historical highs
- Market short-term performance extremely strong
- **Warning:** Short-term gains too large, profit-taking pressure high

**Oversold Signal (daily_return_factor < 20):**
- Short-term cumulative loss at historical lows
- Market short-term performance extremely weak
- **Opportunity:** Rebound probability high after oversold

**Marginal Change Interpretation:**
- daily_return_factor climbing rapidly → Short-term profit effect strong, sentiment euphoric
- daily_return_factor pulling back from highs → Short-term profit effect weakening
- daily_return_factor flattening at lows → Downside momentum slowing, bottom building

---

### 13. up_number_rate_factor (Market Breadth Factor)

**Group:** Breadth Consistency

**Source Indicator:** Ratio of rising stocks across the whole market

**Calculation:**
```
Up Ratio = Rising Stock Count / (Rising Stock Count + Falling Stock Count)
Up_Ratio_20d_ma -> rolling(20)
up_number_rate_factor = 180-day percentile rank of Up_Ratio_20d_ma
```

**Core Meaning:** Market breadth reflects the consistency of up/down movements across individual stocks. It is an important indicator of market sentiment breadth. Breadth trending up means more stocks rising, sentiment spreading healthily; breadth declining means individual stocks diverging or universally falling, sentiment contracting.

**Overheating Signal (up_number_rate_factor > 80):**
- Vast majority of stocks rising, market sentiment highly consistent
- Group bullish sentiment euphoric
- **Warning:** After excessive consistency, stampede risk is high

**Oversold Signal (up_number_rate_factor < 20):**
- Vast majority of stocks falling, market sentiment extremely pessimistic
- Panic sentiment in control
- **Opportunity:** Often bounce follows sentiment ice points

**Marginal Change Interpretation:**
- up_number_rate_factor rising → Number of rising stocks expanding, sentiment continuing healthily
- up_number_rate_factor falling + index not falling → Divergence (index holding but stocks retreating) → Warning
- up_number_rate_factor rebounding from lows → Sentiment recovery signal

---

### 14. equity_bond_effective_factor (Equity-Bond Effectiveness / Crowding Factor)

**Group:** Basic Momentum

**Source Indicator:** CSI 300 P/E reciprocal + Total market trading amount

**Calculation:**
```
X_normalized = (X - min_180) / (max_180 - min_180) * 100

PE_reciprocal_normalized = normalize(1 / CSI300_PE)
tot_amount_normalized = normalize(Trading_Amount)

factor_index = PE_reciprocal_normalized - tot_amount_normalized
(High yield -> optimism; High volume -> crowding; so subtraction)

gap_5d_ma = rolling(factor_index, 5)
gap_60d_ma = rolling(factor_index, 60)
gap_marginal = gap_5d_ma - gap_60d_ma

equity_bond_effective_factor = 100 - 180-day percentile rank of gap_marginal
```

**Core Meaning:** The equity-bond effectiveness factor combines two dimensions: valuation (yield) and trading crowding. High yield (low P/E) means equity assets are relatively more attractive; high trading volume means market is crowded and sentiment overheated. The core logic: when yield is low but trading is active, the market is most dangerous (crowded trading).

**Overheating Signal (equity_bond_effective_factor > 80, equivalent to gap_marginal at lows):**
- Low yield (high P/E) + active trading -> Market excessively crowded
- Marginal change negative: crowding is intensifying
- **Strong Warning:** Historical backtesting shows this zone is an important risk signal

**Oversold Signal (equity_bond_effective_factor < 20, equivalent to gap_marginal at highs):**
- High yield (low P/E) + cold trading -> Market excessively pessimistic
- Marginal change positive: sentiment repair signal
- **Opportunity:** Low crowding + high yield = relatively good entry zone

**Marginal Change Interpretation:**
- equity_bond_effective_factor 5-day MA > 60-day MA (golden cross) -> Crowding declining, opportunity signal
- equity_bond_effective_factor 5-day MA < 60-day MA (death cross) -> Crowding rising, risk signal
- This factor is the most important reversal-type factor in the system; its directional changes deserve close attention

---

## Factor Interactions and Common Patterns

**Trend-Following Factors (momentum direction):**
- emascore_long_factor, signal_macd_factor, daily_return_factor, highlow_factor
- These have clear directional signals, suitable for trend-following

**Overbought/Oversold Factors (extreme positions):**
- mfi_factor, RSI_factor, ar_factor, br_factor
- High levels warn of pullback risk; low levels warn of rebound opportunity

**Money Flow & Crowding Factors (capital and structure):**
- obv_factor, leverage_factor, pcr_factor, turnover_amount_factor, equity_bond_effective_factor
- These are better at predicting medium-to-long-term turning points

**Breadth Factors (trend health confirmation):**
- up_number_rate_factor
- In trending markets, breadth factor must align with price direction; divergence is a warning
