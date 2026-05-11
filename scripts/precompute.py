#!/usr/bin/env python3
"""
预计算情绪指数缓存
支持两种数据源：
  1. 飞书云表格（默认）：传入 feishu_sheet_url 或 spreadsheet_token
  2. 本地 Excel 文件：传入 excel_path

用法：
  python3 scripts/precompute.py                           # 使用飞书云盘（如已配置）
  python3 scripts/precompute.py --local assets/df_sentiment.xlsx
  python3 scripts/precompute.py --feishu https://xxx.feishu.cn/sheets/TOKEN
  python3 scripts/precompute.py --token J2yUsT52RhOCdEtiVQKchkiin3f
"""
import pandas as pd
import json
import sys
import argparse
from pathlib import Path

# ─── 飞书云表格读取 ────────────────────────────────────────────
# 提示：实际调用由主 agent 通过 feishu_sheet 工具完成，
# 此函数接收 already-fetched 的数据二维数组。

def load_from_feishu(rows, headers):
    """处理从飞书云表格 API 获取的数据"""
    df = pd.DataFrame(rows, columns=headers)
    # 过滤空行
    df = df[df["Times"].notna() & (df["Times"] != "")]
    df = df.sort_values("Times").reset_index(drop=True)
    return df

# ─── 本地 Excel ────────────────────────────────────────────────
def load_from_excel(excel_path):
    df = pd.read_excel(excel_path, engine="openpyxl")
    df = df.sort_values("Times").reset_index(drop=True)
    return df

# ─── 预计算核心 ────────────────────────────────────────────────
def precompute(df, json_path=None):
    json_path = json_path or "assets/sentiment_cache.json"

    headers = list(df.columns)
    rows = df.values.tolist()

    latest_row = rows[-1]
    prev_row   = rows[-2]

    sentiment_col = headers.index("sentiment_index_avg60_plus")
    vals_all = [r[sentiment_col] for r in rows]
    slope_5  = round((vals_all[-1] - vals_all[-6]) / 5, 3) if len(vals_all) >= 6 else 0

    def row_dict(r):
        return dict(zip(headers, r))

    cur = row_dict(latest_row)
    pre = row_dict(prev_row)

    sentiment_now  = cur["sentiment_index_avg60_plus"]
    sentiment_prev = pre["sentiment_index_avg60_plus"]

    # EMA5 / EMA20（用于趋势信号）
    ema5  = round(sum(vals_all[-5:]) / 5, 2)
    ema20 = round(sum(vals_all[-20:]) / 20, 2) if len(vals_all) >= 20 else ema5
    ema_diff = round(ema5 - ema20, 2)

    # 所有因子
    all_factors_list = [
        "obv_factor","mfi_factor","leverage_factor","pcr_factor",
        "turnover_amount_factor","ar_factor","br_factor",
        "emascore_long_factor","signal_macd_factor","highlow_factor",
        "RSI_factor","daily_return_factor","up_number_rate_factor",
        "equity_bond_effective_factor",
    ]
    factor_vals = {f: round(float(cur.get(f, 0) or 0), 1) for f in all_factors_list}

    hot_factor  = max(factor_vals, key=factor_vals.get)
    cold_factor = min(factor_vals, key=factor_vals.get)

    # 过热（≥80）/ 偏冷（≤20）
    overheat = {k: v for k, v in factor_vals.items() if v >= 80}
    cold     = {k: v for k, v in factor_vals.items() if v <= 20}

    # 历史
    history_5  = rows[-5:]
    history_20 = rows[-20:]

    output = {
        "headers":            headers,
        "latest_row":         latest_row,
        "prev_row":           prev_row,
        "slope_5":            slope_5,
        "sentiment_now":      round(sentiment_now, 4),
        "sentiment_prev":     round(sentiment_prev, 4),
        "ema5":               ema5,
        "ema20":              ema20,
        "ema_diff":           ema_diff,
        "hot_factor":         hot_factor,
        "hot_factor_value":   factor_vals[hot_factor],
        "cold_factor":        cold_factor,
        "cold_factor_value":  factor_vals[cold_factor],
        "all_factors":        factor_vals,
        "overheat_factors":   overheat,
        "cold_factors":       cold,
        "history_5":          history_5,
        "history_20":         history_20,
    }

    Path(json_path).parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"[OK] sentiment_cache.json updated")
    print(f"     sentiment_now={sentiment_now:.2f}  slope_5={slope_5:+.3f}  EMA_diff={ema_diff:+.2f}")
    print(f"     hot={hot_factor}({factor_vals[hot_factor]:.0f})  cold={cold_factor}({factor_vals[cold_factor]:.0f})")
    print(f"     → {json_path}")
    return output

# ─── CLI ───────────────────────────────────────────────────────
if __name__ == "__main__":
    import os
    skill_dir = Path(__file__).parent.parent.resolve()
    os.chdir(skill_dir)

    parser = argparse.ArgumentParser(description="预计算情绪指数缓存")
    parser.add_argument("--local", dest="excel_path", help="本地 Excel 路径")
    parser.add_argument("--feishu-url", dest="feishu_url", help="飞书云表格 URL（仅解析 token，不实际拉数据，由 agent 调用 API）")
    parser.add_argument("--token", dest="spreadsheet_token", help="飞书 spreadsheet token")
    parser.add_argument("--json-path", dest="json_path", default="assets/sentiment_cache.json")
    args = parser.parse_args()

    if args.excel_path:
        df = load_from_excel(args.excel_path)
        precompute(df, args.json_path)
    else:
        print("[INFO] 飞书云表格数据由 agent 通过 feishu_sheet 工具读取后传入")
        print("       触发更新请说：更新数据 / 刷新缓存")
