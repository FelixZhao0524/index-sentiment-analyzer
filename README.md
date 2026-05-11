# index-sentiment-analyzer

沪深300ETF情绪指数深度分析工具 — OpenClaw Skill。

分析直接读取飞书云表格，**每次分析自动从云端获取最新数据**，无需手动更新。

## 功能

- **14个核心情绪因子**实时解读（OBV、MFI、MACD、RSI、融资杠杆、PCR等）
- **综合情绪指数**档位判定（0–100百分位）
- **预警信号**检测（历史胜率85.71%，最大回撤捕捉率100%）
- **极值因子追踪**：自动识别过热（≥80）和偏冷（≤20）因子

## 数据范围

- 沪深300ETF情绪指数历史数据
- 时间：2016-01-04 至今（约2500个交易日）
- 14个因子 + 综合情绪指数

## 安装

在任意 OpenClaw agent 中安装：
```bash
openclaw skill install https://github.com/FelixZhao0524/index-sentiment-analyzer/releases/download/v1.0/index-sentiment-analyzer.skill
```

## 14个因子

| 因子 | 名称 | 高值含义 | 低值含义 |
|------|------|----------|----------|
| obv_factor | 能量潮因子 | 资金持续净流入 | 资金净流出 |
| mfi_factor | 资金流量因子 | 买盘极度旺盛 | 卖压充分释放 |
| leverage_factor | 融资杠杆因子 | 杠杆资金大规模入场 | 融资客撤退 |
| pcr_factor | 期权多空因子 | 对冲需求极强，市场谨慎 | 过度乐观 |
| turnover_amount_factor | 流动活性因子 | 成交极度活跃 | 成交极度萎缩 |
| ar_factor | 人气因子 | 持续收于日内高点 | 持续收于日内低点 |
| br_factor | 买卖意愿因子 | 持仓信心强 | 恐慌抛压释放 |
| emascore_long_factor | 均线多头因子 | 均线完美多头排列 | 均线空头排列 |
| signal_macd_factor | MACD动量因子 | 多头信号强 | 空头主导 |
| highlow_factor | 高低价动量因子 | 买方主导 | 动量衰竭 |
| RSI_factor | 相对强弱因子 | 超买 | 超卖 |
| daily_return_factor | 日收益率因子 | 短期涨幅历史高位 | 短期跌幅历史低位 |
| up_number_rate_factor | 市场广度因子 | 全市场普涨 | 全市场普跌 |
| equity_bond_effective_factor | 拥挤度因子 | 极度拥挤，最危险反转信号 | 低拥挤高赔率 |

## 综合情绪指数

所有14因子等权融合 → 60日均值 → 180日百分位化 → 最终读数0–100。

## 预警信号

- **触发条件**：读数达到极值（≥99）AND 次日出现下降拐点
- **历史胜率**：85.71%（7次触发中6次随后出现>10%回撤）
- **平均领先**：约20个交易日

## 数据来源

飞书云表格（首发），spreadsheet token：`J2yUsT52RhOCdEtiVQKchkiin3f`

## 免责声明

仅供教育和研究使用，不构成投资建议。
