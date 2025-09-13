from __future__ import annotations

import pandas as pd


def compute_board_metrics(board: str, stock_data: dict[str, pd.DataFrame]):
    """Aggregate board level metrics and leader scoring."""
    members = []
    total_vol = 0.0
    total_vol_ma = 0.0
    limit_up = 0
    for code, df in stock_data.items():
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        pct_chg = latest["close"] / prev["close"] - 1
        turnover = latest.get("turnover_rate", 0)
        amount = latest.get("amount", 0)
        vol_ma = df["volume"].rolling(5).mean().iloc[-1]
        total_vol += latest["volume"]
        total_vol_ma += vol_ma
        if pct_chg >= 0.095:
            limit_up += 1
        members.append({
            "symbol": code,
            "pct_chg": pct_chg,
            "turnover_rate": turnover,
            "amount": amount,
        })
    members_df = pd.DataFrame(members)
    board_vol_ratio = total_vol / total_vol_ma if total_vol_ma else 0
    board_pct_chg = members_df["pct_chg"].mean()
    members_df["score"] = members_df[["pct_chg", "turnover_rate", "amount"]].rank(pct=True).mean(axis=1)
    leaders = members_df.sort_values("score", ascending=False).head(3)
    metrics = {
        "board": board,
        "pct_chg": board_pct_chg,
        "vol_ratio": board_vol_ratio,
        "limit_up": limit_up,
    }
    return metrics, leaders
