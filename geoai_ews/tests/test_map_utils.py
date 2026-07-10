"""Unit tests for streamlit_app.map_utils.gdf_to_map_df — the fix for the
StreamlitAPIException seen in production logs when st.map() was called
directly on GeoDataFrames whose coordinate columns didn't match what
st.map() expects (e.g. WPDx's lat_deg/lon_deg), or on polygon boundaries
with no lat/lon columns at all.
"""
import geopandas as gpd
from shapely.geometry import Point, Polygon

from streamlit_app.map_utils import gdf_to_map_df


def test_point_geometries_use_direct_coordinates():
    gdf = gpd.GeoDataFrame(
        {"lat_deg": [0.1, 0.2], "lon_deg": [35.1, 35.2]},
        geometry=[Point(35.1, 0.1), Point(35.2, 0.2)],
        crs="EPSG:4326",
    )
    out = gdf_to_map_df(gdf)
    assert list(out.columns) == ["lat", "lon"]
    assert abs(out.loc[0, "lat"] - 0.1) < 1e-9
    assert abs(out.loc[0, "lon"] - 35.1) < 1e-9


def test_polygon_geometries_use_centroid():
    gdf = gpd.GeoDataFrame(
        {"county": ["Nandi"]},
        geometry=[Polygon([(35.0, 0.0), (35.1, 0.0), (35.1, 0.1), (35.0, 0.1)])],
        crs="EPSG:4326",
    )
    out = gdf_to_map_df(gdf)
    assert list(out.columns) == ["lat", "lon"]
    assert len(out) == 1


def test_mixed_geometry_types():
    gdf = gpd.GeoDataFrame(
        {"id": [1, 2]},
        geometry=[Point(35.1, 0.1), Polygon([(35.0, 0.0), (35.1, 0.0), (35.1, 0.1), (35.0, 0.1)])],
        crs="EPSG:4326",
    )
    out = gdf_to_map_df(gdf)
    assert len(out) == 2
    assert not out["lat"].isna().any()
    assert not out["lon"].isna().any()


def test_empty_geodataframe_returns_empty_frame_with_correct_columns():
    gdf = gpd.GeoDataFrame(columns=["geometry"], geometry="geometry", crs="EPSG:4326")
    out = gdf_to_map_df(gdf)
    assert list(out.columns) == ["lat", "lon"]
    assert len(out) == 0
