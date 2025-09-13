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
    """Return cache file path using CSV format."""
    cache_dir = ensure_dir(cache_dir)
    return cache_dir / f"{key}.csv"


def load_cache(path: str | Path):
    """Load cached DataFrame from CSV; fallback to legacy PKL if present.

    If a legacy `.pkl` exists for the same key, it will be read once and
    automatically migrated to CSV for subsequent loads.
    """
    p = Path(path)
    if p.exists():
        try:
            return pd.read_csv(p)
        except Exception:
            # If CSV is corrupted, treat as missing
            return None
    # Fallback: migrate old pickle cache if it exists
    legacy = p.with_suffix(".pkl")
    if legacy.exists():
        try:
            df = pd.read_pickle(legacy)
            # Migrate to CSV for future fast loads
            df.to_csv(p, index=False)
            return df
        except Exception:
            return None
    return None


def save_cache(df: pd.DataFrame, path: str | Path) -> None:
    """Save DataFrame cache as CSV without index."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(p, index=False)


def retry_fn(func: Callable | None = None, *, tries: int = 3) -> Callable:
    """Retry decorator with exponential backoff."""
    if func is None:
        return lambda f: retry_fn(f, tries=tries)

    @retry(stop=stop_after_attempt(tries), wait=wait_exponential(multiplier=1, min=1, max=3))
    def wrapper(*args: Any, **kwargs: Any):
        return func(*args, **kwargs)

    return wrapper
