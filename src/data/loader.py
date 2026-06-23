"""
Dataset Loader — fetches the Zomato dataset from Hugging Face.

Uses the `datasets` library to download the
ManikaSaini/zomato-restaurant-recommendation dataset. Falls back to a
local CSV cache when a cached copy already exists.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from src.config import settings

logger = logging.getLogger(__name__)


def load_from_huggingface() -> pd.DataFrame:
    """Download the dataset from Hugging Face and return as a DataFrame.

    Returns:
        pd.DataFrame: Raw dataset as a pandas DataFrame.

    Raises:
        RuntimeError: If the download fails after retries.
    """
    try:
        from datasets import load_dataset

        logger.info(
            "Downloading dataset '%s' from Hugging Face…", settings.HF_DATASET_NAME
        )
        dataset = load_dataset(settings.HF_DATASET_NAME, split="train")
        df = dataset.to_pandas()
        logger.info("Dataset loaded successfully — %d rows.", len(df))
        return df
    except Exception as exc:
        raise RuntimeError(
            f"Failed to load dataset from Hugging Face: {exc}"
        ) from exc


def load_from_cache(cache_path: Path | None = None) -> pd.DataFrame | None:
    """Attempt to load a previously cached CSV snapshot.

    Args:
        cache_path: Path to the cached CSV file. Defaults to settings value.

    Returns:
        pd.DataFrame if cache exists, else None.
    """
    path = cache_path or settings.DATA_CACHE_PATH
    if path.exists():
        logger.info("Loading dataset from cache: %s", path)
        return pd.read_csv(path)
    return None


def save_to_cache(df: pd.DataFrame, cache_path: Path | None = None) -> None:
    """Persist the DataFrame as a CSV for future reuse.

    Args:
        df: Preprocessed DataFrame to save.
        cache_path: Destination path. Defaults to settings value.
    """
    path = cache_path or settings.DATA_CACHE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    logger.info("Dataset cached at %s (%d rows).", path, len(df))


def load_dataset_df(force_download: bool = False) -> pd.DataFrame:
    """Primary entry point — returns a raw DataFrame, using cache when possible.

    Args:
        force_download: If True, skip the cache and re-download.

    Returns:
        pd.DataFrame: Raw (unprocessed) dataset.
    """
    if not force_download:
        cached = load_from_cache()
        if cached is not None:
            return cached

    df = load_from_huggingface()
    save_to_cache(df)
    return df
