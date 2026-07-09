"""
Earth Genome — Earth Index client.

Earth Index is a Sentinel-2 embedding / similarity-search platform, not a
single scalar index. Two access paths are supported here:

  1. Bulk embeddings (preferred, reproducible): GeoParquet files hosted on
     Source Cooperative (earthgenome/earthindexembeddings), tiled by UTM
     grid cell. No confirmed API key required for public read access, but
     EARTH_INDEX_SOURCE_COOP_TOKEN is included in case bucket policy changes.

  2. App/API workflow: requires an Earth Index account and (if available)
     an API key. CONFIRM CURRENT AUTH MODEL DIRECTLY WITH EARTH GENOME —
     no public REST API was documented at time of writing.

CREDENTIALS REQUIRED (see CREDENTIALS_AND_ACCESS_REQUIRED.pdf):
  - EARTH_INDEX_APP_ACCOUNT_EMAIL (app workflow)
  - EARTH_INDEX_API_KEY (if/when Earth Genome issues one)
  - EARTH_INDEX_SOURCE_COOP_TOKEN (bulk workflow, if required)
"""
from __future__ import annotations

import logging
from pathlib import Path

import geopandas as gpd
import pandas as pd
import pyarrow.parquet as pq
import requests

from config.settings import settings

logger = logging.getLogger(__name__)

SOURCE_COOP_BASE_URL = "https://data.source.coop/earthgenome/earthindexembeddings"


def utm_tiles_for_north_rift() -> list[str]:
    """UTM 36N grid tile codes covering the North Rift counties.

    Populate with the exact MGRS/UTM tile codes once confirmed against the
    Earth Index / Source Cooperative tiling scheme for this AOI.
    """
    return ["36NYF", "36NYG", "36NXF", "36NXG"]  # placeholder — verify against actual tiling


def download_embedding_tile(tile_code: str, date_range: str, out_dir: Path) -> Path:
    """Download a single GeoParquet embeddings tile from Source Cooperative.

    `date_range` matches the archive naming convention, e.g. '2024-01-01_2025-01-01'.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{tile_code}_{date_range}.parquet"
    url = f"{SOURCE_COOP_BASE_URL}/{filename}"
    out_path = out_dir / filename

    headers = {}
    if settings.earth_index_source_coop_token:
        headers["Authorization"] = f"Bearer {settings.earth_index_source_coop_token}"

    logger.info("Downloading Earth Index embeddings tile: %s", url)
    resp = requests.get(url, headers=headers, timeout=120, stream=True)
    resp.raise_for_status()
    with open(out_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=1 << 20):
            f.write(chunk)
    return out_path


def load_embeddings(parquet_path: Path) -> gpd.GeoDataFrame:
    """Load a downloaded embeddings GeoParquet into a GeoDataFrame.

    Fields: id (uint64), embedding (float[384]), geometry (Point, EPSG:4326-ish
    per the source README — reprojected here for consistency).
    """
    table = pq.read_table(parquet_path)
    df = table.to_pandas()
    gdf = gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4626")
    gdf = gdf.to_crs(epsg=4326)
    logger.info("Loaded %d embedding tiles from %s", len(gdf), parquet_path.name)
    return gdf


def clip_embeddings_to_boundary(embeddings: gpd.GeoDataFrame, boundary: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Clip embedding points to a county/region boundary."""
    boundary_union = boundary.to_crs(embeddings.crs).unary_union
    clipped = embeddings[embeddings.within(boundary_union)]
    logger.info("Clipped embeddings to boundary: %d -> %d points", len(embeddings), len(clipped))
    return clipped


def submit_app_search(reference_feature_geojson: dict, aoi_geojson: dict) -> dict:
    """Illustrative wrapper for the Earth Index app-based similarity search.

    No documented public REST endpoint was confirmed at time of writing.
    Placeholder raises until Earth Genome confirms an API path — use the
    hosted app (app.earthindex.ai) for this workflow in the meantime.
    """
    raise NotImplementedError(
        "Earth Index does not currently expose a documented public REST API. "
        "Use the hosted app at app.earthindex.ai for interactive searches, "
        "or the bulk embeddings workflow (download_embedding_tile / load_embeddings) "
        "for a reproducible pipeline. Confirm with EARTH_INDEX_APP_ACCOUNT_EMAIL "
        "account holder if API access has since been granted."
    )
