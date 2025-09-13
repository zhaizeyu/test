import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.indicators import add_volume_ratio, calc_ma
from src.strategy import evaluate


def _sample_df():
    dates = pd.date_range("2024-01-01", periods=31)
    price = 10.0
    opens, closes, highs, lows, vols, turns = [], [], [], [], [], []
    for i, _ in enumerate(dates):
        if i == 1:
            price *= 1.1  # limit up
        else:
            price += 0.1
        opens.append(price - 0.05)
        closes.append(price)
        highs.append(price + 0.1)
        lows.append(price - 0.1)
        vols.append(1000 + i * 10)
        turns.append(0.1)
    df = pd.DataFrame(
        {
            "date": dates,
            "open": opens,
            "close": closes,
            "high": highs,
            "low": lows,
            "volume": vols,
            "turnover_rate": turns,
        }
    )
    df = calc_ma(df)
    df = add_volume_ratio(df)
    return df


def test_strategy_selected():
    df = _sample_df()
    board_info = {"vol_ratio": 1.5, "pct_chg": 0.02, "limit_up": 2}
    config = {
        "thresholds": {
            "limit_up_days": 30,
            "ma_proximity": 0.05,
            "vol_up": 1.2,
            "vol_down": 0.8,
            "board_vol_up": 1.0,
            "upper_shadow": 0.0,
            "doji_body": 0.2,
            "turnover_low": 0.05,
            "turnover_high": 0.15,
        },
        "weights": {
            "limit_up": 1,
            "ma_near": 1,
            "close_gt_open_ma": 1,
            "close_up": 1,
            "volume": 1,
            "board_volume": 1,
            "board_up": 1,
            "board_limit_up": 1,
            "upper_shadow": 0,
            "doji": 0,
            "turnover": 1,
        },
        "score_threshold": 6,
    }
    res = evaluate("000001", df, board_info, config)
    assert res["selected"]
    assert res["failed"] == []
