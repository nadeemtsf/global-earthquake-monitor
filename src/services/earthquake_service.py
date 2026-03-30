"""Framework-agnostic earthquake data orchestration services."""

from __future__ import annotations

import logging
import os
from concurrent.futures import ThreadPoolExecutor

import pandas as pd

from data_config import CONFIG
from providers import gdacs_provider, usgs_provider
from services.cache import ttl_cache
from utils.data_utils import (
    extract_country,
    extract_magnitude,
    mag_to_alert_level,
    normalize_schema,
    parse_rfc_datetime,
)

logger = logging.getLogger(__name__)
CACHE_TTL = CONFIG["cache_ttl"]

# Ensure persistent cache directory exists
os.makedirs(".cache", exist_ok=True)


@ttl_cache(ttl_seconds=CACHE_TTL)
def fetch_usgs_geojson(
    start_date: str | None, end_date: str | None, min_mag: float | None = None
) -> dict:
    return usgs_provider.fetch_usgs_geojson(
        CONFIG["api_base"],
        start_date,
        end_date,
        min_mag or CONFIG["default_min_magnitude"],
    )


@ttl_cache(ttl_seconds=CACHE_TTL)
def fetch_usgs_xml(
    start_date: str | None, end_date: str | None, min_mag: float | None = None
) -> str:
    return usgs_provider.fetch_usgs_xml(
        CONFIG["api_base"],
        start_date,
        end_date,
        min_mag or CONFIG["default_min_magnitude"],
    )


def geojson_to_df(data: dict) -> pd.DataFrame:
    df = usgs_provider.geojson_to_df(data, mag_to_alert_level, extract_country)
    return normalize_schema(df)


@ttl_cache(ttl_seconds=CACHE_TTL)
def fetch_gdacs_xml() -> str:
    return gdacs_provider.fetch_gdacs_xml(CONFIG["gdacs_rss_url"])


def gdacs_xml_to_df(
    xml_text: str,
    start_date: str | None = None,
    end_date: str | None = None,
    min_mag: float | None = None,
) -> pd.DataFrame:
    df = gdacs_provider.gdacs_xml_to_df(
        xml_text,
        start_date,
        end_date,
        min_mag,
        extract_magnitude,
        parse_rfc_datetime,
    )
    return normalize_schema(df)


def load_data_with_cache(from_date=None, to_date=None, min_magnitude=None):
    return load_data_by_source(from_date, to_date, min_magnitude, source="USGS")


def load_data_by_source(
    start_date: str | None = None,
    end_date: str | None = None,
    min_mag: float | None = None,
    source: str = "USGS",
) -> tuple[pd.DataFrame, str | None]:
    """Orchestrate data loading from providers with cache fallback."""
    selected = (source or "USGS").strip().upper()

    if selected == "USGS":
        return _load_usgs_with_cache(start_date, end_date, min_mag)
    if selected == "GDACS":
        return _load_gdacs_with_cache(start_date, end_date, min_mag)
    if selected == "BOTH":
        return _load_combined_sources(start_date, end_date, min_mag)

    return normalize_schema(pd.DataFrame()), f"⚠️ Unknown source: {source}"


def _load_combined_sources(
    start_date: str | None, end_date: str | None, min_mag: float | None
) -> tuple[pd.DataFrame, str | None]:
    """Fetch from both USGS and GDACS in parallel."""
    with ThreadPoolExecutor(max_workers=2) as executor:
        future_usgs = executor.submit(
            _load_usgs_with_cache, start_date, end_date, min_mag
        )
        future_gdacs = executor.submit(
            _load_gdacs_with_cache, start_date, end_date, min_mag
        )
        u_df, u_w = future_usgs.result()
        g_df, g_w = future_gdacs.result()

    frames = [f for f in [u_df, g_df] if f is not None and not f.empty]
    if not frames:
        warns = [w for w in [u_w, g_w] if w]
        return normalize_schema(pd.DataFrame()), " | ".join(warns) or None

    merged = pd.concat(frames, ignore_index=True)
    merged = normalize_schema(merged).sort_values("main_time")
    warns = [w for w in [u_w, g_w] if w]
    return merged, " | ".join(warns) if warns else None


def _load_usgs_with_cache(
    start_date: str | None, end_date: str | None, min_mag: float | None
) -> tuple[pd.DataFrame, str | None]:
    try:
        data = fetch_usgs_geojson(start_date, end_date, min_mag)
        df = geojson_to_df(data)
        try:
            xml = fetch_usgs_xml(start_date, end_date, min_mag)
            usgs_provider.save_raw_xml(xml, CONFIG["xml_output_file"])
        except Exception as e:
            logger.warning("USGS XML error: %s", e)
        df.to_csv(CONFIG["cache_file"], index=False)
        return df, None
    except Exception as e:
        logger.warning("USGS fetch failed: %s", e)
        if os.path.exists(CONFIG["cache_file"]):
            return normalize_schema(
                pd.read_csv(CONFIG["cache_file"])
            ), "⚠️ USGS fetch failed — using cached data."
        return pd.DataFrame(), "⚠️ USGS fetch failed and no cache found."


def _load_gdacs_with_cache(
    start_date: str | None, end_date: str | None, min_mag: float | None
) -> tuple[pd.DataFrame, str | None]:
    try:
        xml = fetch_gdacs_xml()
        gdacs_provider.save_gdacs_xml(xml, CONFIG["gdacs_xml_output_file"])
        df = gdacs_xml_to_df(xml, start_date, end_date, min_mag)
        df.to_csv(CONFIG["gdacs_cache_file"], index=False)
        return df, None
    except Exception as e:
        logger.warning("GDACS fetch failed: %s", e)
        if os.path.exists(CONFIG["gdacs_cache_file"]):
            return normalize_schema(
                pd.read_csv(CONFIG["gdacs_cache_file"])
            ), "⚠️ GDACS fetch failed — using cached data."
        return pd.DataFrame(), "⚠️ GDACS fetch failed and no cache found."
