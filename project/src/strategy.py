from __future__ import annotations

from typing import Any, Dict

import pandas as pd

from .indicators import (
    has_limit_up,
    is_doji,
    ma_proximity,
    upper_shadow_ratio,
    volume_signal,
)


def evaluate(code: str, df: pd.DataFrame, board_info: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate a single stock against strategy rules."""
    th = config["thresholds"]
    weight = config["weights"]
    latest = df.iloc[-1]

    rules: Dict[str, bool] = {}
    rules["limit_up"] = has_limit_up(df, days=th.get("limit_up_days", 30))
    rules["ma_near"] = ma_proximity(df, threshold=th["ma_proximity"])
    rules["close_gt_open_ma"] = latest["close"] > latest["open"] and all(
        latest["close"] > latest[f"ma{x}"] for x in (5, 10, 20)
    )
    rules["close_up"] = latest["close"] > df["close"].iloc[-2]
    vol_sig = volume_signal(df, n=5, up=th["vol_up"], down=th["vol_down"])
    rules["volume"] = vol_sig in {"up", "down"}
    rules["board_volume"] = board_info.get("vol_ratio", 0) >= th["board_vol_up"]
    rules["board_up"] = board_info.get("pct_chg", 0) > 0
    rules["board_limit_up"] = board_info.get("limit_up", 0) > 1
    rules["upper_shadow"] = upper_shadow_ratio(latest) >= th["upper_shadow"]
    rules["doji"] = is_doji(latest, body_thresh=th["doji_body"])
    rules["turnover"] = th["turnover_low"] <= latest.get("turnover_rate", 0) <= th["turnover_high"]

    score = sum(weight.get(k, 0) for k, v in rules.items() if v)
    failed = [k for k, v in rules.items() if not v]
    selected = score >= config["score_threshold"]
    result: Dict[str, Any] = {"symbol": code, "score": score, "selected": selected, "failed": failed}
    result.update(rules)
    return result
