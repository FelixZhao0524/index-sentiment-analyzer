# index-sentiment-analyzer

A股沪深300 ETF 情绪指数深度分析 Skill for OpenClaw。

## 功能

- 14个核心情绪因子实时解读（MFI、OBV、MACD、RSI、杠杆资金、期权PCR 等）
- 6大类情绪分组分析（基础动能/趋势强度/活跃度/短期势能/资金流向/广度一致性）
- 综合情绪指数档位判断（0-100 分位）
- 预警信号判断（历史胜率 85.71%，回撤捕捉率 100%）
- 边际变化斜率分析（5日/20日方向）
- 10类情绪场景矩阵解读

## 内置数据

- 沪深300ETF 情绪指数历史数据
- 时间区间：2016-01-04 至 2026-04-30（约2500个交易日）
- 14个因子 + 综合情绪指数

## 安装

在目标 Agent 上执行：
```bash
openclaw skill install index-sentiment-analyzer.skill
```

或通过 URL 直接安装（需先创建 Release）：
```bash
openclaw skill install https://github.com/FelixZhao0524/index-sentiment-analyzer/releases/download/v1.0/index-sentiment-analyzer.skill
```

## 因子列表（14个）

| 因子 | 中文名 | 大类 |
|---|---|---|
| obv_factor | 能量潮因子 | 资金流向 |
| mfi_factor | 资金流量因子 | 市场基础动能 |
| leverage_factor | 融资杠杆因子 | 市场基础动能 |
| pcr_factor | 期权多空因子 | 市场基础动能 |
| turnover_amount_factor | 流动活性因子 | 市场活跃度 |
| ar_factor | 人气活跃因子 | 市场基础动能 |
| br_factor | 多空买卖意愿因子 | 市场基础动能 |
| emascore_long_factor | 均线突破因子 | 市场趋势强度 |
| signal_macd_factor | 趋势背离因子 | 市场趋势强度 |
| highlow_factor | 上涨势能因子 | 短期势能 |
| RSI_factor | 相对强弱因子 | 市场基础动能 |
| daily_return_factor | 日收益率因子 | 市场基础动能 |
| up_number_rate_factor | 市场广度因子 | 广度一致性 |
| equity_bond_effective_factor | 广义拥挤度因子 | 市场基础动能 |

## 预警规则

- **触发条件**：`sentiment_index_avg60_plus == 100` 且次日环比下降
- **历史胜率**：85.71%（7次预警中6次回撤超10%）
- **平均提前预警**：约19天

## 免责

本工具仅供辅助参考，不构成投资建议。
