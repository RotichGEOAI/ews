"""
County / ward boundary loading for the North Rift region.

No credentials required — boundaries are loaded from local/verified GeoJSON
files (or a public admin-boundary source such as GADM / Kenya OpenData,
which do not require API keys for bulk download).
"""
from __future__ import annotations

import logging
from pathlib import Path

import geopandas as gpd

logger = logging.getLogger(__name__)

NORTH_RIFT_COUNTIES = [
    "Nandi",
    "Uasin Gishu",
    "Trans Nzoia",
    "Elgeyo-Marakwet",
    "West Pokot",
]

DEFAULT_BOUNDARY_DIR = Path(__file__).resolve().parent.parent / "data" / "boundaries"


def load_county_boundary(county: str, boundary_dir: Path = DEFAULT_BOUNDARY_DIR) -> gpd.GeoDataFrame:
    """Load a single verified county boundary GeoJSON.

    Expects a file named `<county_slug>.geojson` in `boundary_dir`, e.g.
    `nandi.geojson`. Replace with your verified Nandi boundary and equivalent
    files for the other four North Rift counties.
    """
    slug = county.lower().replace(" ", "_").replace("-", "_")
    path = boundary_dir / f"{slug}.geojson"
    if not path.exists():
        raise FileNotFoundError(
            f"Boundary file not found: {path}. Place a verified GeoJSON for "
            f"'{county}' here before running the pipeline."
        )
    gdf = gpd.read_file(path)
    gdf["county"] = county
    logger.info("Loaded boundary for %s (%d feature(s))", county, len(gdf))
    return gdf


def load_north_rift_boundaries(boundary_dir: Path = DEFAULT_BOUNDARY_DIR) -> gpd.GeoDataFrame:
    """Load and concatenate all five North Rift county boundaries."""
    frames = [load_county_boundary(c, boundary_dir) for c in NORTH_RIFT_COUNTIES]
    combined = gpd.pd.concat(frames, ignore_index=True)
    return gpd.GeoDataFrame(combined, crs=frames[0].crs)
