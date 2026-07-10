"""
Borehole / water-point density gridding.

Data sources:
  - Kenya Water Resources Authority (WRA) WRIS  -> WRA_WRIS_API_KEY, WRA_WRIS_CLIENT_ID
  - Water Point Data Exchange (WPDx)             -> WPDX_API_KEY
See CREDENTIALS_AND_ACCESS_REQUIRED.pdf.
"""
from __future__ import annotations

import logging

import geopandas as gpd
import numpy as np
import pandas as pd
import requests
from shapely.geometry import Point

from config.settings import settings

logger = logging.getLogger(__name__)

WRA_WRIS_BASE_URL = "https://wris.wra.go.ke/api/v1"   # placeholder — confirm with WRA
WPDX_BASE_URL = "https://data.waterpointdata.org/resource/eqje-vguj.json"  # Socrata endpoint


def fetch_wra_wris_points(county: str) -> gpd.GeoDataFrame:
    """Fetch registered/permitted borehole points from WRA WRIS for a county.

    CREDENTIALS REQUIRED: WRA_WRIS_API_KEY, WRA_WRIS_CLIENT_ID.
    """
    if not settings.wra_wris_api_key:
        raise EnvironmentError(
            "WRA_WRIS_API_KEY not set. Request WRIS API access from the Kenya "
            "Water Resources Authority before fetching borehole permit data."
        )
    headers = {
        "Authorization": f"Bearer {settings.wra_wris_api_key}",
        "X-Client-Id": settings.wra_wris_client_id or "",
    }
    resp = requests.get(
        f"{WRA_WRIS_BASE_URL}/boreholes", params={"county": county}, headers=headers, timeout=30
    )
    resp.raise_for_status()
    records = resp.json().get("results", [])
    if not records:
        logger.warning("No WRA WRIS records returned for %s", county)
        return gpd.GeoDataFrame(columns=["geometry", "permit_status"], geometry="geometry", crs="EPSG:4326")

    df = pd.DataFrame(records)
    geometry = [Point(r["longitude"], r["latitude"]) for r in records]
    return gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")


def fetch_wpdx_points(county: str) -> gpd.GeoDataFrame:
    """Fetch community water points from WPDx for a county.

    CREDENTIALS REQUIRED: WPDX_API_KEY (app token for higher rate limits;
    the public Socrata endpoint works unauthenticated at low volume).
    """
    params = {"clean_country_name": "Kenya", "clean_adm1": county, "$limit": 5000}
    headers = {}
    if settings.wpdx_api_key:
        headers["X-App-Token"] = settings.wpdx_api_key
    resp = requests.get(WPDX_BASE_URL, params=params, headers=headers, timeout=60)
    resp.raise_for_status()
    records = resp.json()
    if not records:
        logger.warning("No WPDx records returned for %s", county)
        return gpd.GeoDataFrame(columns=["geometry"], geometry="geometry", crs="EPSG:4326")

    df = pd.DataFrame(records)
    geometry = [
        Point(float(r.get("lon_deg", 0)), float(r.get("lat_deg", 0))) for r in records
    ]
    return gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")


def compute_borehole_density_grid(
    points: gpd.GeoDataFrame, grid_size_m: float = 1000.0
) -> gpd.GeoDataFrame:
    """Rasterize borehole/water-point counts onto a regular grid (points-per-cell)."""
    if points.empty:
        logger.warning("No points supplied to compute_borehole_density_grid")
        return points

    points_m = points.to_crs(epsg=32636)  # UTM 36N, appropriate for North Rift
    minx, miny, maxx, maxy = points_m.total_bounds
    xs = np.arange(minx, maxx + grid_size_m, grid_size_m)
    ys = np.arange(miny, maxy + grid_size_m, grid_size_m)

    from shapely.geometry import box

    cells = []
    for x0 in xs[:-1]:
        for y0 in ys[:-1]:
            cell = box(x0, y0, x0 + grid_size_m, y0 + grid_size_m)
            count = points_m[points_m.intersects(cell)].shape[0]
            cells.append({"geometry": cell, "borehole_count": count})

    grid = gpd.GeoDataFrame(cells, crs=points_m.crs).to_crs(epsg=4326)
    grid["borehole_density_per_km2"] = grid["borehole_count"] / ((grid_size_m / 1000) ** 2)
    logger.info("Computed borehole density grid: %d cells", len(grid))
    return grid
