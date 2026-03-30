"""Compatibility wrapper around the framework-agnostic earthquake service layer."""

from __future__ import annotations

import pandas as pd

from data_config import CONFIG
from services import earthquake_service
from utils.data_utils import normalize_schema

fetch_gdacs_xml = earthquake_service.fetch_gdacs_xml
fetch_usgs_geojson = earthquake_service.fetch_usgs_geojson
fetch_usgs_xml = earthquake_service.fetch_usgs_xml
gdacs_xml_to_df = earthquake_service.gdacs_xml_to_df
geojson_to_df = earthquake_service.geojson_to_df


def _load_usgs_with_cache(
    start_date: str | None, end_date: str | None, min_mag: float | None
) -> tuple[pd.DataFrame, str | None]:
    return earthquake_service._load_usgs_with_cache(start_date, end_date, min_mag)


def _load_gdacs_with_cache(
    start_date: str | None, end_date: str | None, min_mag: float | None
) -> tuple[pd.DataFrame, str | None]:
    return earthquake_service._load_gdacs_with_cache(start_date, end_date, min_mag)


def _load_combined_sources(
    start_date: str | None, end_date: str | None, min_mag: float | None
) -> tuple[pd.DataFrame, str | None]:
    frames_and_warns = [
        _load_usgs_with_cache(start_date, end_date, min_mag),
        _load_gdacs_with_cache(start_date, end_date, min_mag),
    ]
    frames = [frame for frame, _ in frames_and_warns if frame is not None and not frame.empty]
    warns = [warn for _, warn in frames_and_warns if warn]

    if not frames:
        return normalize_schema(pd.DataFrame()), " | ".join(warns) or None

    merged = pd.concat(frames, ignore_index=True)
    merged = normalize_schema(merged).sort_values("main_time")
    return merged, " | ".join(warns) if warns else None


def load_data_by_source(
    start_date: str | None = None,
    end_date: str | None = None,
    min_mag: float | None = None,
    source: str = "USGS",
) -> tuple[pd.DataFrame, str | None]:
    selected = (source or "USGS").strip().upper()

    if selected == "USGS":
        return _load_usgs_with_cache(start_date, end_date, min_mag)
    if selected == "GDACS":
        return _load_gdacs_with_cache(start_date, end_date, min_mag)
    if selected == "BOTH":
        return _load_combined_sources(start_date, end_date, min_mag)

    return normalize_schema(pd.DataFrame()), f"⚠️ Unknown source: {source}"


def load_data_with_cache(from_date=None, to_date=None, min_magnitude=None):
    return load_data_by_source(from_date, to_date, min_magnitude, source="USGS")


__all__ = [
    "CONFIG",
    "_load_combined_sources",
    "_load_gdacs_with_cache",
    "_load_usgs_with_cache",
    "fetch_gdacs_xml",
    "fetch_usgs_geojson",
    "fetch_usgs_xml",
    "gdacs_xml_to_df",
    "geojson_to_df",
    "load_data_by_source",
    "load_data_with_cache",
]
