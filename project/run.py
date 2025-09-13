from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

from src.board import compute_board_metrics
from src.data_api import get_stock_daily
from src.indicators import add_volume_ratio, calc_ma
from src.plotting import plot_kline
from src.strategy import evaluate
from src.utils import ensure_dir, read_config


def main() -> None:
    base = Path(__file__).resolve().parent
    config = read_config(base / "config.yaml")
    today = datetime.today().strftime("%Y%m%d")
    start = (datetime.today() - timedelta(days=120)).strftime("%Y%m%d")
    end = today

    output_dir = ensure_dir(base / "outputs")
    figs_dir = ensure_dir(output_dir / "figs")

    universe = config["universe"]
    board_defs = config.get("boards", {})

    stock_data: dict[str, pd.DataFrame] = {}
    for code in universe:
        df = get_stock_daily(code, start, end)
        df = calc_ma(df)
        df = add_volume_ratio(df)
        stock_data[code] = df

    # board metrics
    board_metrics = {}
    board_records = []
    stock_board_map = {}
    for board, info in board_defs.items():
        symbols = info.get("symbols", [])
        data = {s: stock_data[s] for s in symbols if s in stock_data}
        metrics, leaders = compute_board_metrics(board, data)
        board_metrics[board] = metrics
        board_records.append({**metrics, "leaders": ",".join(leaders["symbol"].tolist())})
        for s in symbols:
            stock_board_map[s] = board

    results = []
    for code, df in stock_data.items():
        binfo = board_metrics.get(stock_board_map.get(code, ""), {})
        res = evaluate(code, df, binfo, config)
        results.append(res)
        if res["selected"]:
            plot_kline(df, code, figs_dir)

    signals_df = pd.DataFrame(results).sort_values("score", ascending=False)
    boards_df = pd.DataFrame(board_records)

    print("Top20 signals:")
    print(signals_df.head(20)[["symbol", "score"]])

    signals_path = output_dir / f"signals_{today}.csv"
    boards_path = output_dir / f"boards_{today}.csv"
    signals_df.to_csv(signals_path, index=False)
    boards_df.to_csv(boards_path, index=False)

    report_path = output_dir / f"report_{today}.xlsx"
    with pd.ExcelWriter(report_path) as writer:
        signals_df.to_excel(writer, sheet_name="signals", index=False)
        boards_df.to_excel(writer, sheet_name="boards", index=False)


if __name__ == "__main__":
    main()
