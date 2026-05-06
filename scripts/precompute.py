#!/usr/bin/env python3
"""
预计算情绪指数缓存
将 Excel 数据预计算为 JSON，加载速度从 ~10秒 提升到 ~10毫秒
"""
import pandas as pd
import json
import sys
from pathlib import Path

def precompute(excel_path=None, json_path=None):
    excel_path = excel_path or "assets/df_sentiment.xlsx"
    json_path = json_path or "assets/sentiment_cache.json"

    df = pd.read_excel(excel_path, engine="openpyxl")
    df = df.sort_values("Times").reset_index(drop=True)

    headers = list(df.columns)
    rows = df.values.tolist()

    latest_row = rows[-1]
    prev_row = rows[-2]

    sentiment_col = headers.index("sentiment_index_avg60_plus")
    vals_all = [r[sentiment_col] for r in rows]
    slope_5 = round((vals_all[-1] - vals_all[-6]) / 5, 3) if len(vals_all) >= 6 else 0

    groups = {
        "市场基础动能": ["mfi_factor","leverage_factor","pcr_factor","ar_factor",
                       "br_factor","RSI_factor","daily_return_factor","equity_bond_effective_factor"],
        "市场趋势强度": ["emascore_long_factor","signal_macd_factor"],
        "市场活跃度": ["turnover_amount_factor"],
        "短期势能": ["highlow_factor"],
        "资金流向": ["obv_factor"],
        "广度一致性": ["up_number_rate_factor"],
    }

    def row_dict(r):
        return dict(zip(headers, r))

    cur = row_dict(latest_row)
    sentiment_now = cur["sentiment_index_avg60_plus"]
    sentiment_prev = row_dict(prev_row)["sentiment_index_avg60_plus"]

    group_means = {}
    for gname, factors in groups.items():
        vals = [cur.get(f, 0) for f in factors]
        group_means[gname] = round(sum(vals) / len(vals), 1)

    all_factors_list = sum(groups.values(), [])
    factor_vals = {f: round(cur.get(f, 0), 1) for f in all_factors_list}
    hot_factor = max(factor_vals, key=factor_vals.get)
    cold_factor = min(factor_vals, key=factor_vals.get)

    # 最近5日 / 20日历史（用于历史走势查询）
    history_5 = rows[-5:]
    history_20 = rows[-20:]

    output = {
        "latest_row": latest_row,
        "prev_row": prev_row,
        "headers": headers,
        "slope_5": slope_5,
        "sentiment_now": round(sentiment_now, 4),
        "sentiment_prev": round(sentiment_prev, 4),
        "group_means": group_means,
        "hot_factor": hot_factor,
        "hot_factor_value": factor_vals[hot_factor],
        "cold_factor": cold_factor,
        "cold_factor_value": factor_vals[cold_factor],
        "all_factors": factor_vals,
        "history_5": history_5,
        "history_20": history_20,
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"[OK] sentiment_cache.json updated")
    print(f"     sentiment_now={sentiment_now:.2f}, slope_5={slope_5:.3f}")
    print(f"     {json_path}")

if __name__ == "__main__":
    # 支持从任意目录运行
    import os
    skill_dir = Path(__file__).parent.resolve()
    os.chdir(skill_dir)
    precompute()
