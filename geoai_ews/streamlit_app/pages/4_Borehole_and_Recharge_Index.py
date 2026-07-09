"""Upload/fetch borehole points and compute the composite recharge vulnerability grid."""
import sys
from pathlib import Path

import geopandas as gpd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from geoai.borehole_density import compute_borehole_density_grid, fetch_wpdx_points, fetch_wra_wris_points
from geoai.recharge_index import compute_recharge_vulnerability_index
from geoai.boundaries import NORTH_RIFT_COUNTIES

st.title("💧 Borehole Density & Recharge Vulnerability Index")

county = st.selectbox("County", NORTH_RIFT_COUNTIES)
source = st.radio("Borehole data source", ["Upload GeoJSON/CSV", "Fetch from WRA WRIS", "Fetch from WPDx"])

points = None
if source == "Upload GeoJSON/CSV":
    uploaded = st.file_uploader("Upload borehole points", type=["geojson", "json", "csv"])
    if uploaded is not None:
        points = gpd.read_file(uploaded)
elif source == "Fetch from WRA WRIS":
    if st.button("Fetch from WRA WRIS"):
        try:
            points = fetch_wra_wris_points(county)
        except EnvironmentError as e:
            st.error(str(e))
elif source == "Fetch from WPDx":
    if st.button("Fetch from WPDx"):
        try:
            points = fetch_wpdx_points(county)
        except EnvironmentError as e:
            st.error(str(e))

if points is not None and not points.empty:
    st.success(f"Loaded {len(points)} borehole/water point(s).")
    st.map(points)

    grid_size = st.slider("Grid cell size (meters)", 250, 5000, 1000, step=250)
    if st.button("Compute density grid"):
        grid = compute_borehole_density_grid(points, grid_size_m=grid_size)
        st.session_state["borehole_grid"] = grid
        st.dataframe(grid.drop(columns="geometry").head(20))

if "borehole_grid" in st.session_state:
    st.subheader("Composite Recharge Vulnerability Index")
    if st.button("Compute composite index"):
        scored = compute_recharge_vulnerability_index(st.session_state["borehole_grid"])
        st.session_state["risk_grid"] = scored
        st.dataframe(
            scored[["borehole_count", "borehole_density_per_km2", "composite_risk_score", "risk_class"]].head(20)
        )
        st.bar_chart(scored["risk_class"].value_counts())
