from __future__ import annotations

from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import pandas as pd

from .utils import ensure_dir


def plot_kline(df: pd.DataFrame, code: str, out_dir: str | Path) -> Path:
    """Plot 30-day kline with MA5/10/20 and volume."""
    df = df.tail(30).copy()
    df["date"] = pd.to_datetime(df["date"])
    df.set_index("date", inplace=True)
    ensure_dir(out_dir)

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(10, 6), sharex=True, gridspec_kw={"height_ratios": [2, 1]}
    )
    width = 0.6
    for dt, row in df.iterrows():
        color = "red" if row["close"] >= row["open"] else "green"
        ax1.plot([dt, dt], [row["low"], row["high"]], color=color)
        rect = Rectangle(
            (mdates.date2num(dt) - width / 2, min(row["open"], row["close"])),
            width,
            abs(row["close"] - row["open"]),
            color=color,
        )
        ax1.add_patch(rect)
    ax1.plot(df.index, df["ma5"], label="MA5")
    ax1.plot(df.index, df["ma10"], label="MA10")
    ax1.plot(df.index, df["ma20"], label="MA20")
    ax1.legend()

    ax2.bar(df.index, df["volume"], color="gray")
    ax2.set_ylabel("Volume")

    fig.autofmt_xdate()
    path = Path(out_dir) / f"{code}.png"
    fig.savefig(path)
    plt.close(fig)
    return path
