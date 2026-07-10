"""Upload county/ward boundary GeoJSON files for the North Rift pipeline."""
import sys
from pathlib import Path

import geopandas as gpd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from geoai.boundaries import NORTH_RIFT_COUNTIES
from streamlit_app.map_utils import gdf_to_map_df

st.title("🗺️ Upload County Boundaries")

county = st.selectbox("County", NORTH_RIFT_COUNTIES)
uploaded = st.file_uploader("Upload verified boundary GeoJSON", type=["geojson", "json"])

if uploaded is not None:
    gdf = gpd.read_file(uploaded)
    st.success(f"Loaded {len(gdf)} feature(s) for {county}.")
    st.map(gdf_to_map_df(gdf))

    save_dir = PROJECT_ROOT / "data" / "boundaries"
    save_dir.mkdir(parents=True, exist_ok=True)
    slug = county.lower().replace(" ", "_").replace("-", "_")
    out_path = save_dir / f"{slug}.geojson"
    if st.button(f"Save as {out_path.relative_to(PROJECT_ROOT)}"):
        gdf.to_file(out_path, driver="GeoJSON")
        st.success(f"Saved to {out_path}")
        st.caption(
            "Note: on Streamlit Community Cloud the filesystem is ephemeral — "
            "re-upload after each redeploy, or persist to a bucket/DB instead "
            "(see the deployment guide, 'Persisting uploaded files')."
        )
