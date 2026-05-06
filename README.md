# index-sentiment-analyzer

OpenClaw Skill for deep analysis of A-share CSI 300 ETF Sentiment Index indicators.

## Features

- 14 core sentiment factors real-time interpretation (MFI, OBV, MACD, RSI, leverage funds, options PCR, etc.)
- 6 major factor group analysis (Basic Momentum / Trend Strength / Market Activity / Short-term Momentum / Fund Flow / Breadth Consistency)
- Composite sentiment index level determination (0-100 percentile)
- Warning signal detection (historical win rate 85.71%, drawdown capture rate 100%)
- Marginal change slope analysis (5-day / 20-day direction)
- 10-class sentiment scenario matrix interpretation

## Built-in Data

- CSI 300 ETF Sentiment Index historical data
- Time range: 2016-01-04 to 2026-04-30 (~2500 trading days)
- 14 factors + composite sentiment index

## Installation

On any OpenClaw agent:
```bash
openclaw skill install https://github.com/FelixZhao0524/index-sentiment-analyzer/releases/download/v1.0/index-sentiment-analyzer.skill
```

## 14 Factors

| Factor | Name | Group |
|--------|------|-------|
| obv_factor | On-Balance Volume | Fund Flow |
| mfi_factor | Money Flow Index | Basic Momentum |
| leverage_factor | Leverage Factor | Basic Momentum |
| pcr_factor | Options Put/Call Ratio | Basic Momentum |
| turnover_amount_factor | Turnover Activity | Market Activity |
| ar_factor | Activity Ratio | Basic Momentum |
| br_factor | Buy/Sell Ratio | Basic Momentum |
| emascore_long_factor | EMA Score Long | Trend Strength |
| signal_macd_factor | MACD Signal | Trend Strength |
| highlow_factor | High-Low Momentum | Short-term Momentum |
| RSI_factor | Relative Strength Index | Basic Momentum |
| daily_return_factor | Daily Return | Basic Momentum |
| up_number_rate_factor | Upward Breadth | Breadth Consistency |
| equity_bond_effective_factor | Equity-Bond Effectiveness | Basic Momentum |

## Composite Index Calculation

```
Composite = (Basic Momentum + Trend Strength + Market Activity + Short-term Momentum + Fund Flow + Breadth Consistency) / 6
Composite_60d_ma -> rolling(60)
sentiment_index_avg60_plus = percentile(180d, Composite_60d_ma)
```

Value range: 0-100 (percentile vs. last 180 trading days)

## Warning Signal

- **Trigger**: sentiment_index_avg60_plus == 100 AND next day sequential decline (turning point)
- **Historical win rate**: 85.71% (6 out of 7 warnings were followed by >10% drawdown)
- **Avg lead time**: ~19 trading days

## Disclaimer

For educational and research purposes only. Not investment advice.
