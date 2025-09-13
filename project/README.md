# Quantitative Stock Selection

本项目基于 `akshare`、`pandas`、`numpy`、`matplotlib` 实现了一个简易的量化选股与板块分析流程。

## Installation

```bash
pip install -r requirements.txt
```

## Usage

运行完整流程：

```bash
python run.py
```

结果以 CSV 形式保存在 `outputs/` 目录下：

- `signals_YYYYMMDD.csv`：个股打分与是否入选
- `boards_YYYYMMDD.csv`：板块聚合指标与龙头名单

可选输出 Excel 报告（多工作表）：在 `config.yaml` 中设置 `write_excel: true` 即可生成 `report_YYYYMMDD.xlsx`。

## 配置说明（config.yaml）

- thresholds: 策略阈值集合
  - ma_proximity: 均线粘合阈值（三条均线最大最小之差/最小值）
  - vol_up: 放量上限（`vol_ratio >= vol_up` 视为放量）
  - vol_down: 缩量下限（`vol_ratio <= vol_down` 视为缩量）
  - board_vol_up: 板块放量判断阈值（板块总量/均量）
  - upper_shadow: 上影线占比阈值（(high - max(open, close)) / (high - low)）
  - doji_body: 十字星实体占比阈值（|close-open| / (high-low)）
  - turnover_low / turnover_high: 换手率区间（小数形式，0.05 表示 5%）
  - limit_up_days: 近 N 日内是否出现涨停（按涨幅阈值判断）
- weights: 各规则的加权分值（命中则累加）
- score_threshold: 选股分数门槛，达到或超过则 `selected=true`
- universe: 股票代码列表（如 `"000001"`）
- boards: 板块定义
  - 每个板块下的 `symbols` 为成分股代码列表
- write_excel: 是否额外写出 Excel 报告（默认 `false`）

## 功能概述

- 数据获取（`src/data_api.py`）
  - 个股日线：优先使用 `ak.stock_zh_a_daily(adjust="qfq")`，若接口或字段异常，回退 `ak.stock_zh_a_hist`；统一列名与数据格式；日期统一为 `YYYYMMDD` 字符串。
  - 指数日线：`ak.stock_zh_index_daily`（如需与个股一致可扩展同样的回退与标准化）。
  - 缓存：使用 CSV 存储（`outputs/cache/*.csv`），首次命中旧 `.pkl` 会自动迁移为 CSV。
- 指标计算（`src/indicators.py`）
  - `calc_ma`: 计算 MA5/MA10/MA20
  - `add_volume_ratio`/`volume_signal`: 计算量比与放缩量信号
  - K 线形态：`is_doji`、`upper_shadow_ratio`
  - 涨停判定：`has_limit_up`
- 板块聚合（`src/board.py`）
  - 汇总成员股涨跌幅、成交量、均量、换手等，计算板块平均涨幅、放量比例与涨停数
  - 简单龙头评分并输出 Top3
- 策略评分（`src/strategy.py`）
  - 依据阈值与权重对单只股票进行多规则打分，并判断是否入选
- 结果输出与可视化（`src/plotting.py`）
  - 对入选股票绘制近 30 日 K 线、MA5/10/20 与成交量（保存于 `outputs/figs/`）
  - 输出选股结果与板块汇总 CSV（可选 Excel 报告）

## 代码入口

- `run.py`：
  - 读取配置、确定时间区间
  - 拉取并缓存个股数据，计算均线与量比
  - 计算板块指标与龙头
  - 按策略打分并筛选、绘图
  - 保存 CSV/可选 Excel 报告

## Tests

```bash
pytest
```
