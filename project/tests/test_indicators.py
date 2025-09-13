import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.indicators import (
    calc_ma,
    has_limit_up,
    is_doji,
    ma_proximity,
    volume_signal,
)


def test_volume_signal():
    df = pd.DataFrame({"volume": [1, 1, 1, 1, 5]})
    assert volume_signal(df) == "up"
    df = pd.DataFrame({"volume": [5, 1, 1, 1, 1]})
    assert volume_signal(df) == "down"


def test_has_limit_up():
    df = pd.DataFrame({"close": [10, 11]})
    assert has_limit_up(df)
    df_st = pd.DataFrame({"close": [10, 10.6]})
    assert has_limit_up(df_st, st=True)


def test_ma_proximity():
    df = pd.DataFrame({"close": [10] * 25})
    df = calc_ma(df)
    assert ma_proximity(df, threshold=0.02)


def test_is_doji():
    row = pd.Series({"open": 10, "close": 10.02, "high": 10.2, "low": 9.8})
    assert is_doji(row, body_thresh=0.1)
