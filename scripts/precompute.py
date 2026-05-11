#!/usr/bin/env python3
"""
预计算情绪指数缓存（手动工具）

当用户明确说「更新数据」时，由人工触发此脚本。
日常分析不需要运行此脚本，分析时直接读取飞书云表格即可。

用法：
  python3 scripts/precompute.py --local assets/df_sentiment.xlsx

此脚本不做任何自动执行，分析流程完全由 SKILL.md 规范。
"""
import pandas as pd
import json
import argparse
from pathlib import Path

def load_from_excel(excel_path):
    df = pd.read_excel(excel_path, engine="openpyxl")
    df = df[df["Times"].notna() & (df["Times"] != "")]
    df = df.sort_values("Times").reset_index(drop=True)
    return df

def precompute(df, json_path=None):
    json_path = json_path or "assets/sentiment_cache.json"
    headers = list(df.columns)
    rows = df.values.tolist()
    latest_row = rows[-1]
    prev_row = rows[-2]

    cur = dict(zip(headers, latest_row))
    pre = dict(zip(headers, prev_row))

    all_factors_list = [
        "obv_factor","mfi_factor","leverage_factor","pcr_factor",
        "turnover_amount_factor","ar_factor","br_factor",
        "emascore_long_factor","signal_macd_factor","highlow_factor",
        "RSI_factor","daily_return_factor","up_number_rate_factor",
        "equity_bond_effective_factor",
    ]
    factor_vals = {f: round(float(cur.get(f, 0) or 0), 1) for f in all_factors_list}
    hot_factor = max(factor_vals, key=factor_vals.get)
    cold_factor = min(factor_vals, key=factor_vals.get)

    output = {
        "headers": headers,
        "latest_row": latest_row,
        "prev_row": prev_row,
        "sentiment_now": round(float(cur["sentiment_index_avg60_plus"]), 4),
        "sentiment_prev": round(float(pre["sentiment_index_avg60_plus"]), 4),
        "hot_factor": hot_factor,
        "hot_factor_value": factor_vals[hot_factor],
        "cold_factor": cold_factor,
        "cold_factor_value": factor_vals[cold_factor],
        "all_factors": factor_vals,
        "overheat_factors": {k: v for k, v in factor_vals.items() if v >= 80},
        "cold_factors": {k: v for k, v in factor_vals.items() if v <= 20},
        "history_5": rows[-5:],
        "history_20": rows[-20:],
    }

    Path(json_path).parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"[OK] sentiment_cache.json updated")
    print(f"     sentiment_now={output['sentiment_now']:.2f}")
    print(f"     hot={hot_factor}({factor_vals[hot_factor]:.0f})  cold={cold_factor}({factor_vals[cold_factor]:.0f})")
    return output

if __name__ == "__main__":
    import os
    skill_dir = Path(__file__).parent.parent.resolve()
    os.chdir(skill_dir)
    parser = argparse.ArgumentParser(description="预计算情绪指数缓存（手动工具）")
    parser.add_argument("--local", dest="excel_path", required=True, help="本地 Excel 路径")
    parser.add_argument("--json-path", dest="json_path", default="assets/sentiment_cache.json")
    args = parser.parse_args()
    df = load_from_excel(args.excel_path)
    precompute(df, args.json_path)
