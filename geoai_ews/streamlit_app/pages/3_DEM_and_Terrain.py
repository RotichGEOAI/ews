"""Upload a GLO-30 DEM GeoTIFF and compute slope/hillshade/elevation zones."""
import sys
import tempfile
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from geoai.dem_terrain import compute_terrain_derivatives, write_terrain_rasters

st.title("⛰️ DEM & Terrain Derivatives")
st.caption(
    "If you already have Copernicus credentials configured, you can wire in "
    "`dem_terrain.fetch_glo30_dem()` instead of uploading manually. Manual "
    "upload avoids needing live Copernicus access during development."
)

uploaded = st.file_uploader("Upload GLO-30 DEM GeoTIFF (.tif)", type=["tif", "tiff"])

if uploaded is not None:
    with tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as tmp:
        tmp.write(uploaded.read())
        tmp_path = Path(tmp.name)

    with st.spinner("Computing slope, hillshade, elevation zones..."):
        derivatives = compute_terrain_derivatives(tmp_path)

    col1, col2, col3 = st.columns(3)
    col1.image(derivatives.hillshade, caption="Hillshade", clamp=True)
    col2.write("Slope (deg) — summary")
    col2.write(
        {
            "min": float(derivatives.slope_deg.min()),
            "max": float(derivatives.slope_deg.max()),
            "mean": float(derivatives.slope_deg.mean()),
        }
    )
    col3.write("Elevation zones — unique values")
    col3.write(sorted(set(derivatives.elevation_zones.flatten().tolist())))

    if st.button("Save terrain rasters to data/terrain/"):
        out_dir = PROJECT_ROOT / "data" / "terrain" / "uploaded"
        outputs = write_terrain_rasters(derivatives, out_dir)
        st.success(f"Saved: {', '.join(str(p) for p in outputs.values())}")
