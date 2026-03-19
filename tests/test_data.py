from pathlib import Path
import sys

import pandas as pd
import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import data  # noqa: E402


@pytest.fixture
def sample_geojson():
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "title": "M 6.1 - 10 km E of Testville, Testland",
                    "url": "https://earthquake.usgs.gov/earthquakes/eventpage/test1",
                    "type": "earthquake",
                    "mag": 6.1,
                    "magType": "mw",
                    "sig": 500,
                    "tsunami": 1,
                    "felt": 42,
                    "status": "reviewed",
                    "time": 1700000000000,
                    "place": "10 km E of Testville, Testland",
                },
                "geometry": {"type": "Point", "coordinates": [100.1, 20.2, 35.0]},
            },
            {
                "type": "Feature",
                "properties": {
                    "title": "M 3.4 - 5 km N of Fooville",
                    "url": "https://earthquake.usgs.gov/earthquakes/eventpage/test2",
                    "type": "earthquake",
                    "mag": 3.4,
                    "magType": "ml",
                    "sig": 100,
                    "tsunami": 0,
                    "felt": None,
                    "status": "automatic",
                    "time": 1700001000000,
                    "place": "5 km N of Fooville",
                },
                "geometry": {"type": "Point", "coordinates": [101.2, 21.3, 10.0]},
            },
        ],
    }


def test_mag_to_alert_level_red():
    assert data._mag_to_alert_level(7.2) == "Red"


def test_mag_to_alert_level_orange():
    assert data._mag_to_alert_level(5.6) == "Orange"


def test_mag_to_alert_level_yellow():
    assert data._mag_to_alert_level(4.2) == "Yellow"


def test_mag_to_alert_level_green():
    assert data._mag_to_alert_level(3.9) == "Green"


def test_mag_to_alert_level_unknown_on_nan():
    assert data._mag_to_alert_level(float("nan")) == "Unknown"


def test_extract_country_with_comma():
    assert data._extract_country("7 km E of Lakatoro, Vanuatu") == "Vanuatu"


def test_extract_country_without_comma():
    assert data._extract_country("Northern Mid-Atlantic Ridge") == "Northern Mid-Atlantic Ridge"


def test_geojson_to_df_maps_expected_fields(sample_geojson):
    df = data.geojson_to_df(sample_geojson)
    assert len(df) == 2
    assert set(["place", "magnitude", "depth_km", "latitude", "longitude", "link"]).issubset(df.columns)
    assert df["source"].eq("USGS").all()


def test_geojson_to_df_sets_date_and_sorted(sample_geojson):
    df = data.geojson_to_df(sample_geojson)
    assert "date_utc" in df.columns
    assert df["main_time"].is_monotonic_increasing


def test_geojson_to_df_alert_level_derived(sample_geojson):
    df = data.geojson_to_df(sample_geojson)
    high_mag_alert = df.loc[df["magnitude"] == 6.1, "alert_level"].iloc[0]
    assert high_mag_alert == "Orange"


def test_load_data_with_cache_falls_back_to_cached_csv(monkeypatch, tmp_path):
    cache_path = tmp_path / "USGS_cache.csv"
    cached = pd.DataFrame(
        [
            {
                "title": "Cached M5",
                "link": "https://example.com/cached",
                "event_type": "Earthquake",
                "alert_level": "Yellow",
                "country": "CachedLand",
                "magnitude": 5.0,
                "magnitude_type": "mw",
                "depth_km": 15.0,
                "latitude": 1.0,
                "longitude": 2.0,
                "place": "Cached Place",
                "alert_score": 200,
                "tsunami": 0,
                "felt": 7,
                "status": "reviewed",
                "main_time": "2025-01-01T00:00:00Z",
                "severity_text": "M5.0",
                "population_text": "Felt by 7",
                "source": "USGS",
            }
        ]
    )
    cached.to_csv(cache_path, index=False)

    monkeypatch.setitem(data.CONFIG, "cache_file", str(cache_path))

    def raise_request_error(*args, **kwargs):
        raise requests.RequestException("network down")

    monkeypatch.setattr(data, "fetch_usgs_geojson", raise_request_error)

    df, warn = data.load_data_with_cache("2025-01-01", "2025-01-02", 2.5)
    assert not df.empty
    assert "using cached data" in (warn or "").lower()
    assert "source" in df.columns

