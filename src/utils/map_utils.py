"""
Map rendering utilities for the Global Earthquake Monitor.

Builds an interactive pydeck ScatterplotLayer with colour-coded markers
(by alert level), magnitude-based sizing, and styled hover tooltips.
"""

import pydeck as pdk
import pandas as pd
import streamlit as st

from constants import ALERT_RGBA_COLORS, DEFAULT_ALERT_RGBA


def filter_by_time(df: pd.DataFrame, current_time: pd.Timestamp) -> pd.DataFrame:
    """Filter earthquakes occurring on or before the current_time."""
    if df.empty or "main_time" not in df.columns:
        return df
    
    # Ensure current_time is a pandas Timestamp for comparison
    ts = pd.to_datetime(current_time)
    
    # Filter and return the data
    return df[pd.to_datetime(df["main_time"]) <= ts].copy()


def _prepare_map_data(df: pd.DataFrame) -> pd.DataFrame:
    """Add colour, radius, and display-friendly columns for the map layer."""
    df = df.copy()

    # Colour by alert level — separate RGBA columns for pydeck serialisation
    rgba = (
        df["alert_level"]
        .map(ALERT_RGBA_COLORS)
        .apply(
            lambda c: c if isinstance(c, list) and len(c) == 4 else DEFAULT_ALERT_RGBA
        )
    )
    df["color_r"] = rgba.apply(lambda c: c[0]).astype(int)
    df["color_g"] = rgba.apply(lambda c: c[1]).astype(int)
    df["color_b"] = rgba.apply(lambda c: c[2]).astype(int)
    df["color_a"] = rgba.apply(lambda c: c[3]).astype(int)

    # Radius scaled by magnitude (min 3 000 m, grows exponentially)
    df["radius"] = df["magnitude"].apply(lambda m: max(3000, 2 ** (m - 1) * 2000))

    # Highlight tsunami advisories with a brighter border and thicker stroke
    if "tsunami" in df.columns:
        df["tsunami"] = (
            pd.to_numeric(df["tsunami"], errors="coerce").fillna(0).astype(int)
        )
    else:
        df["tsunami"] = 0
    df["line_r"] = df["tsunami"].apply(lambda t: 56 if t == 1 else 255).astype(int)
    df["line_g"] = df["tsunami"].apply(lambda t: 189 if t == 1 else 255).astype(int)
    df["line_b"] = df["tsunami"].apply(lambda t: 248 if t == 1 else 255).astype(int)
    df["line_a"] = df["tsunami"].apply(lambda t: 255 if t == 1 else 80).astype(int)
    df["line_width"] = df["tsunami"].apply(lambda t: 3 if t == 1 else 1).astype(int)

    # Human-readable strings for the tooltip
    df["time_str"] = df["main_time"].dt.strftime("%Y-%m-%d %H:%M UTC").fillna("N/A")
    df["depth_display"] = df["depth_km"].round(1).fillna("N/A").astype(str) + " km"
    df["mag_display"] = df["magnitude"].round(1).astype(str)
    df["tsunami_display"] = df["tsunami"].map({1: "Yes", 0: "No"}).fillna("No")

    return df


def render_earthquake_map(
    df: pd.DataFrame, 
    max_points: int = 200, 
    center_lat: float | None = None, 
    center_lon: float | None = None,
    sort_by: str = "magnitude"
) -> None:
    """
    Render an interactive pydeck earthquake map in Streamlit.

    Parameters
    ----------
    df         : pd.DataFrame  Filtered earthquake data (must contain latitude,
                                longitude, magnitude, alert_level, depth_km,
                                main_time, place, country columns).
    max_points : int            Maximum number of markers to display.
    center_lat : float | None   Optional fixed center latitude for viewport.
    center_lon : float | None   Optional fixed center longitude for viewport.
    sort_by    : str            Sort the points before truncating ('magnitude' or 'time').
    """
    map_df = df.dropna(subset=["latitude", "longitude", "magnitude"]).copy()
    
    if sort_by == "time" and "main_time" in map_df.columns:
        map_df = map_df.sort_values("main_time", ascending=False)
    else:
        map_df = map_df.sort_values("magnitude", ascending=False)
        
    map_df = map_df.head(max_points)

    if map_df.empty:
        st.info("No earthquake data to display on map.")
        return

    map_df = _prepare_map_data(map_df)

    # Select only necessary columns and convert to native Python types to avoid JSON serialization errors
    map_data = map_df[
        [
            "latitude",
            "longitude",
            "radius",
            "color_r",
            "color_g",
            "color_b",
            "color_a",
            "line_r",
            "line_g",
            "line_b",
            "line_a",
            "line_width",
            "place",
            "mag_display",
            "depth_display",
            "time_str",
            "country",
            "alert_level",
            "tsunami_display",
        ]
    ].copy()

    # Ensure native types (float, int, str) - pandas often keeps numpy types even in to_dict
    for col in ["latitude", "longitude", "radius"]:
        map_data[col] = map_data[col].astype(float)

    for col in ["color_r", "color_g", "color_b", "color_a"]:
        map_data[col] = map_data[col].astype(int)
    for col in ["line_r", "line_g", "line_b", "line_a", "line_width"]:
        map_data[col] = map_data[col].astype(int)

    for col in [
        "place",
        "mag_display",
        "depth_display",
        "time_str",
        "country",
        "alert_level",
        "tsunami_display",
    ]:
        map_data[col] = map_data[col].astype(str)

    # Convert to list of dicts for pydeck
    map_data_dicts = map_data.to_dict(orient="records")

    layer = pdk.Layer(
        "ScatterplotLayer",
        id="earthquake-layer",
        data=map_data_dicts,
        get_position=["longitude", "latitude"],
        get_radius="radius",
        get_fill_color=["color_r", "color_g", "color_b", "color_a"],
        pickable=True,
        opacity=0.7,
        stroked=True,
        get_line_color=["line_r", "line_g", "line_b", "line_a"],
        get_line_width="line_width",
        line_width_min_pixels=1,
    )

    c_lat = center_lat if center_lat is not None else map_df["latitude"].mean()
    c_lon = center_lon if center_lon is not None else map_df["longitude"].mean()

    view_state = pdk.ViewState(
        latitude=c_lat,
        longitude=c_lon,
        zoom=1.5,
        pitch=0,
    )

    tooltip = {
        "html": """
            <div style="font-family: system-ui, sans-serif; padding: 4px 0;">
                <div style="font-weight: 600; font-size: 14px; margin-bottom: 6px; color: #38bdf8;">
                    {place}
                </div>
                <table style="font-size: 12px; border-spacing: 4px 2px;">
                    <tr><td style="color: #94a3b8;">Magnitude</td><td><b>{mag_display}</b></td></tr>
                    <tr><td style="color: #94a3b8;">Depth</td><td>{depth_display}</td></tr>
                    <tr><td style="color: #94a3b8;">Time</td><td>{time_str}</td></tr>
                    <tr><td style="color: #94a3b8;">Country</td><td>{country}</td></tr>
                    <tr><td style="color: #94a3b8;">Alert</td><td>{alert_level}</td></tr>
                    <tr><td style="color: #94a3b8;">Tsunami</td><td>{tsunami_display}</td></tr>
                </table>
            </div>
        """,
        "style": {
            "backgroundColor": "#1e293b",
            "color": "#e2e8f0",
            "border": "1px solid #334155",
            "border-radius": "8px",
            "padding": "10px 14px",
        },
    }

    st.pydeck_chart(
        pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            tooltip=tooltip,
            map_provider="carto",
            map_style=pdk.map_styles.DARK,
        )
    )
