from __future__ import annotations

import pandas as pd
import akshare as ak

from .utils import cache_path, load_cache, save_cache, retry_fn


@retry_fn
def _stock_daily(symbol: str) -> pd.DataFrame:
    """Fetch A-share日线数据，带回退与标准化。

    首选 `stock_zh_a_daily`（Sina 源）。若异常（如 KeyError: 'date'），
    则回退到 `stock_zh_a_hist` 并规范列名与日期格式。
    返回的 DataFrame 至少包含：date/open/close/high/low/volume/amount，
    其中 `date` 为 `YYYYMMDD` 字符串。
    """
    try:
        df = ak.stock_zh_a_daily(symbol=symbol, adjust="qfq")
    except Exception:
        # 回退到 hist 接口
        df = ak.stock_zh_a_hist(symbol=symbol, adjust="qfq")
        mapping = {
            "日期": "date",
            "开盘": "open",
            "收盘": "close",
            "最高": "high",
            "最低": "low",
            "成交量": "volume",
            "成交额": "amount",
            "换手率": "turnover_rate",
        }
        df = df.rename(columns=mapping)
        if "turnover_rate" in df.columns:
            df["turnover_rate"] = pd.to_numeric(
                df["turnover_rate"].astype(str).str.rstrip("%"), errors="coerce"
            ) / 100.0
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y%m%d")
        return df

    # 正常路径：Sina 接口成功
    if "date" not in df.columns:
        # 常见情况：日期在索引中
        df = df.reset_index()
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y%m%d")
    return df


def get_stock_daily(symbol: str, start: str, end: str) -> pd.DataFrame:
    """Get A-share daily kline data."""
    key = f"stock_{symbol}_{start}_{end}"
    path = cache_path(key)
    df = load_cache(path)
    if df is not None:
        return df
    df = _stock_daily(symbol)
    # 兜底一次列名规范（兼容极端场景）
    df = df.rename(columns={
        "日期": "date",
        "开盘": "open",
        "收盘": "close",
        "最高": "high",
        "最低": "low",
        "成交量": "volume",
        "成交额": "amount",
    })
    if "date" not in df.columns:
        raise ValueError("获取的日线数据缺少 'date' 列，无法筛选区间")
    df = df[(df["date"] >= start) & (df["date"] <= end)].reset_index(drop=True)
    # 保证按日期排序
    df = df.sort_values("date").reset_index(drop=True)
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
