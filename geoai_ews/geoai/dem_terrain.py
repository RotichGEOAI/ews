"""
DEM-derived terrain layers: slope, hillshade, elevation zones.

Data source: Copernicus GLO-30 DEM via the Copernicus Data Space Ecosystem.
CREDENTIALS REQUIRED: COPERNICUS_CLIENT_ID / COPERNICUS_CLIENT_SECRET
(OAuth2 client credentials — see CREDENTIALS_AND_ACCESS_REQUIRED.pdf).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import rasterio
from rasterio.enums import Resampling

from config.settings import settings

logger = logging.getLogger(__name__)

COPERNICUS_TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
COPERNICUS_DEM_SEARCH_URL = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"


@dataclass
class TerrainDerivatives:
    slope_deg: np.ndarray
    hillshade: np.ndarray
    elevation_zones: np.ndarray
    transform: rasterio.Affine
    crs: str


def _get_copernicus_access_token() -> str:
    """Obtain an OAuth2 access token for the Copernicus Data Space Ecosystem.

    Requires COPERNICUS_CLIENT_ID and COPERNICUS_CLIENT_SECRET to be set.
    """
    import requests

    if not settings.copernicus_client_id or not settings.copernicus_client_secret:
        raise EnvironmentError(
            "COPERNICUS_CLIENT_ID / COPERNICUS_CLIENT_SECRET not set. "
            "Register at https://dataspace.copernicus.eu/ to obtain OAuth2 "
            "client credentials before fetching GLO-30 DEM tiles."
        )
    resp = requests.post(
        COPERNICUS_TOKEN_URL,
        data={
            "grant_type": "client_credentials",
            "client_id": settings.copernicus_client_id,
            "client_secret": settings.copernicus_client_secret,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def fetch_glo30_dem(bbox: str | None = None, out_path: Path | None = None) -> Path:
    """Download the GLO-30 DEM covering `bbox` (minx,miny,maxx,maxy in EPSG:4326).

    This is a thin wrapper illustrating the auth + request flow. In production,
    prefer the `copernicus-dem` or `elevation` Python packages, or the AWS
    Open Data GLO-30 bucket (s3://copernicus-dem-30m, public, no credentials
    required) as an alternative that avoids the OAuth flow entirely.
    """
    bbox = bbox or settings.copernicus_dem_bbox
    out_path = out_path or Path("data/dem/glo30_north_rift.tif")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    token = _get_copernicus_access_token()  # noqa: F841 (kept for real implementation)
    logger.warning(
        "fetch_glo30_dem: implement actual product search + download against "
        "%s using the obtained token, or switch to the public AWS Open Data "
        "GLO-30 bucket which requires no credentials. bbox=%s",
        COPERNICUS_DEM_SEARCH_URL, bbox,
    )
    return out_path


def compute_terrain_derivatives(dem_path: Path) -> TerrainDerivatives:
    """Compute slope, hillshade, and elevation zones from a DEM GeoTIFF."""
    with rasterio.open(dem_path) as src:
        elevation = src.read(1, resampling=Resampling.bilinear).astype("float32")
        transform = src.transform
        crs = src.crs.to_string() if src.crs else "EPSG:4326"
        px_size_x = transform.a
        px_size_y = -transform.e

    gy, gx = np.gradient(elevation, px_size_y, px_size_x)
    slope_rad = np.arctan(np.sqrt(gx ** 2 + gy ** 2))
    slope_deg = np.degrees(slope_rad)

    azimuth, altitude = 315.0, 45.0
    az_rad = np.radians(360.0 - azimuth + 90.0)
    alt_rad = np.radians(altitude)
    aspect = np.arctan2(-gx, gy)
    hillshade = (
        np.sin(alt_rad) * np.sin(slope_rad)
        + np.cos(alt_rad) * np.cos(slope_rad) * np.cos(az_rad - aspect)
    )
    hillshade = np.clip(hillshade * 255, 0, 255).astype("uint8")

    zone_edges = np.array([-np.inf, 1500, 1800, 2100, 2400, np.inf])
    elevation_zones = np.digitize(elevation, zone_edges).astype("uint8")

    return TerrainDerivatives(
        slope_deg=slope_deg,
        hillshade=hillshade,
        elevation_zones=elevation_zones,
        transform=transform,
        crs=crs,
    )


def write_terrain_rasters(derivatives: TerrainDerivatives, out_dir: Path) -> dict[str, Path]:
    """Persist terrain derivatives as GeoTIFFs for downstream fusion."""
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs: dict[str, Path] = {}

    profile_base = dict(
        driver="GTiff",
        height=derivatives.slope_deg.shape[0],
        width=derivatives.slope_deg.shape[1],
        count=1,
        crs=derivatives.crs,
        transform=derivatives.transform,
        compress="lzw",
    )

    for name, array, dtype in [
        ("slope_deg", derivatives.slope_deg, "float32"),
        ("hillshade", derivatives.hillshade, "uint8"),
        ("elevation_zones", derivatives.elevation_zones, "uint8"),
    ]:
        path = out_dir / f"{name}.tif"
        profile = {**profile_base, "dtype": dtype}
        with rasterio.open(path, "w", **profile) as dst:
            dst.write(array.astype(dtype), 1)
        outputs[name] = path
        logger.info("Wrote %s", path)

    return outputs
