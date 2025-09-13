from __future__ import annotations

import pandas as pd
import akshare as ak

from .utils import cache_path, load_cache, save_cache, retry_fn


@retry_fn
def _stock_daily(symbol: str) -> pd.DataFrame:
    return ak.stock_zh_a_daily(symbol=symbol, adjust="qfq")


def get_stock_daily(symbol: str, start: str, end: str) -> pd.DataFrame:
    """Get A-share daily kline data."""
    key = f"stock_{symbol}_{start}_{end}"
    path = cache_path(key)
    df = load_cache(path)
    if df is not None:
        return df
    df = _stock_daily(symbol).reset_index()
    df = df.rename(columns={
        "date": "date",
        "open": "open",
        "close": "close",
        "high": "high",
        "low": "low",
        "volume": "volume",
        "amount": "amount",
    })
    df = df[(df["date"] >= start) & (df["date"] <= end)].reset_index(drop=True)
    save_cache(df, path)
    return df


@retry_fn
def get_board_members(symbol: str) -> pd.DataFrame:
    """Get board members from THS."""
    return ak.stock_board_cons_ths(symbol=symbol)


@retry_fn
def get_index_daily(symbol: str, start: str, end: str) -> pd.DataFrame:
    df = ak.stock_zh_index_daily(symbol=symbol).reset_index()
    df = df.rename(columns={
        "date": "date",
        "open": "open",
        "close": "close",
        "high": "high",
        "low": "low",
        "volume": "volume",
        "amount": "amount",
    })
    df = df[(df["date"] >= start) & (df["date"] <= end)].reset_index(drop=True)
    return df
