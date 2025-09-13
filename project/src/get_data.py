from __future__ import annotations

from typing import Dict, List, Tuple

import pandas as pd
import akshare as ak

from .data_api import get_stock_daily, get_board_members
from .indicators import calc_ma
from .utils import cache_path, load_cache, save_cache


def get_all_stock_codes() -> List[str]:
    """Fetch all A-share stock codes.

    Prefer the realtime spot list which includes codes for both SSE/SZSE.
    Returns codes like "000001", "600000".
    """
    # Use EastMoney spot api for stability
    df = ak.stock_zh_a_spot_em()
    # Column usually named "代码"
    code_col = "代码" if "代码" in df.columns else "code"
    codes = df[code_col].astype(str).str.zfill(6).tolist()
    return codes


def get_stock_data_bulk(codes: List[str], start: str, end: str,
                        *, add_ma: bool = True,
                        ma_windows: Tuple[int, int, int] = (5, 10, 20)) -> Dict[str, pd.DataFrame]:
    """Fetch daily data for multiple stocks with optional MA calculation.

    Returns a dict: code -> DataFrame including columns date/open/close/high/low/volume/amount
    and ma5/ma10/ma20 if add_ma is True.
    """
    out: Dict[str, pd.DataFrame] = {}
    for code in codes:
        try:
            df = get_stock_daily(code, start, end)
            if add_ma:
                df = calc_ma(df, windows=ma_windows)
            out[code] = df
        except Exception:
            # Skip problematic codes to keep the batch running
            continue
    return out


def get_all_boards(kind: str = "both") -> pd.DataFrame:
    """Fetch board lists.

    kind: "concept" | "industry" | "both"
    Returns columns: code, name, category
    """
    frames = []
    if kind in ("concept", "both"):
        df = ak.stock_board_concept_name_ths()
        if not df.empty:
            # Standardize
            cols = {
                "代码": "code",
                "名称": "name",
            }
            df = df.rename(columns=cols)
            keep = [c for c in ["code", "name"] if c in df.columns]
            df = df[keep].copy()
            df["category"] = "concept"
            frames.append(df)
    if kind in ("industry", "both"):
        df = ak.stock_board_industry_name_ths()
        if not df.empty:
            cols = {
                "代码": "code",
                "名称": "name",
            }
            df = df.rename(columns=cols)
            keep = [c for c in ["code", "name"] if c in df.columns]
            df = df[keep].copy()
            df["category"] = "industry"
            frames.append(df)
    if not frames:
        return pd.DataFrame(columns=["code", "name", "category"])
    boards = pd.concat(frames, ignore_index=True)
    return boards


def get_boards_with_members(kind: str = "both") -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Fetch boards and their member stocks.

    Returns (boards, members):
    - boards: columns [code, name, category]
    - members: columns [board_code, board_name, symbol, name]
    """
    boards = get_all_boards(kind=kind)
    all_members = []
    for _, row in boards.iterrows():
        bcode = row["code"]
        bname = row["name"]
        try:
            mem = get_board_members(bcode)
        except Exception:
            continue
        # THS members columns are typically: 代码, 名称
        code_col = "代码" if "代码" in mem.columns else ("code" if "code" in mem.columns else None)
        name_col = "名称" if "名称" in mem.columns else ("name" if "name" in mem.columns else None)
        if code_col is None:
            continue
        mem = mem.rename(columns={
            code_col: "symbol",
            name_col or "名称": "name",
        })
        keep = [c for c in ["symbol", "name"] if c in mem.columns]
        mem = mem[keep].copy()
        mem.insert(0, "board_name", bname)
        mem.insert(0, "board_code", bcode)
        all_members.append(mem)
    members = pd.concat(all_members, ignore_index=True) if all_members else pd.DataFrame(
        columns=["board_code", "board_name", "symbol", "name"]
    )
    return boards, members


def save_boards_and_members(boards: pd.DataFrame, members: pd.DataFrame, *, date_tag: str | None = None, out_dir: str | None = None) -> Tuple[str, str]:
    """Persist boards and members mapping to CSV with simple caching keys."""
    if date_tag is None:
        # Use generic key to avoid explosion
        boards_key = "boards_all"
        members_key = "board_members_all"
    else:
        boards_key = f"boards_{date_tag}"
        members_key = f"board_members_{date_tag}"
    bpath = cache_path(boards_key, cache_dir=(out_dir or "outputs/cache"))
    mpath = cache_path(members_key, cache_dir=(out_dir or "outputs/cache"))
    save_cache(boards, bpath)
    save_cache(members, mpath)
    return str(bpath), str(mpath)

