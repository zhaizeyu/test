from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

from src.board import compute_board_metrics
from src.data_api import get_stock_daily
from src.get_data import (
    get_all_stock_codes,
    get_stock_data_bulk,
    get_boards_with_members,
    save_boards_and_members,
)
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

    # Determine universe
    if isinstance(universe, str) and universe.upper() == "ALL":
        codes = get_all_stock_codes()
    else:
        codes = list(universe)

    # Fetch stock data in bulk with MA5/10/20
    stock_data: dict[str, pd.DataFrame] = get_stock_data_bulk(codes, start, end, add_ma=True)
    # Add volume ratio for later signals
    for code, df in list(stock_data.items()):
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

    # Fetch board list and members from THS and persist
    boards_all, members = get_boards_with_members(kind="both")
    save_boards_and_members(boards_all, members, date_tag=today, out_dir=str(output_dir / "cache"))

    print("Top20 signals:")
    print(signals_df.head(20)[["symbol", "score"]])

    signals_path = output_dir / f"signals_{today}.csv"
    boards_path = output_dir / f"boards_{today}.csv"
    signals_df.to_csv(signals_path, index=False)
    boards_df.to_csv(boards_path, index=False)

    # 可选输出 Excel 报告（默认关闭；改为 CSV 统一格式）
    if bool(config.get("write_excel", False)):
        report_path = output_dir / f"report_{today}.xlsx"
        with pd.ExcelWriter(report_path) as writer:
            signals_df.to_excel(writer, sheet_name="signals", index=False)
            boards_df.to_excel(writer, sheet_name="boards", index=False)


if __name__ == "__main__":
    main()
