from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import pandas as pd
import yaml
from tenacity import retry, stop_after_attempt, wait_exponential


def read_config(path: str | Path) -> dict:
    """Load YAML configuration file."""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def cache_path(key: str, cache_dir: str | Path = "outputs/cache") -> Path:
    cache_dir = ensure_dir(cache_dir)
    return cache_dir / f"{key}.pkl"


def load_cache(path: str | Path):
    p = Path(path)
    if p.exists():
        return pd.read_pickle(p)
    return None


def save_cache(df: pd.DataFrame, path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    df.to_pickle(p)


def retry_fn(func: Callable | None = None, *, tries: int = 3) -> Callable:
    """Retry decorator with exponential backoff."""
    if func is None:
        return lambda f: retry_fn(f, tries=tries)

    @retry(stop=stop_after_attempt(tries), wait=wait_exponential(multiplier=1, min=1, max=3))
    def wrapper(*args: Any, **kwargs: Any):
        return func(*args, **kwargs)

    return wrapper
