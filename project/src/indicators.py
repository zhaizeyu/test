from __future__ import annotations

import pandas as pd


def calc_ma(df: pd.DataFrame, windows=(5, 10, 20)) -> pd.DataFrame:
    for w in windows:
        df[f"ma{w}"] = df["close"].rolling(w).mean()
    return df


def add_volume_ratio(df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    df["vol_ma"] = df["volume"].rolling(n).mean()
    df["vol_ratio"] = df["volume"] / df["vol_ma"]
    return df


def volume_signal(df: pd.DataFrame, n: int = 5, up: float = 1.2, down: float = 0.8) -> str:
    df = add_volume_ratio(df, n)
    ratio = df["vol_ratio"].iloc[-1]
    if ratio >= up:
        return "up"
    if ratio <= down:
        return "down"
    return "normal"


def has_limit_up(df: pd.DataFrame, *, st: bool = False, days: int = 30) -> bool:
    ret = df["close"].pct_change()
    threshold = 0.05 if st else 0.10
    return ret.tail(days).ge(threshold).any()


def ma_proximity(df: pd.DataFrame, threshold: float = 0.01) -> bool:
    latest = df.iloc[-1]
    vals = latest[["ma5", "ma10", "ma20"]]
    max_ma = vals.max()
    min_ma = vals.min()
    if min_ma == 0:
        return False
    return (max_ma - min_ma) / min_ma <= threshold


def is_doji(row: pd.Series, body_thresh: float = 0.1) -> bool:
    body = abs(row["close"] - row["open"])
    total = row["high"] - row["low"]
    if total == 0:
        return False
    return body / total <= body_thresh


def upper_shadow_ratio(row: pd.Series) -> float:
    top = row["high"] - max(row["open"], row["close"])
    total = row["high"] - row["low"]
    if total == 0:
        return 0.0
    return top / total
