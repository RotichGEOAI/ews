"""
Main GeoAI pipeline entry point — regional extension of the Nandi
water-resource pipeline across the North Rift (boundary loading, DEM
terrain derivatives, borehole density, Earth Index embeddings, composite
recharge vulnerability index).

Usage:
    python pipeline.py --county Nandi
    python pipeline.py --all-north-rift
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path

from geoai import boundaries, dem_terrain, borehole_density, earth_index_client, anomaly_scoring
from geoai.recharge_index import compute_recharge_vulnerability_index

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("pipeline")

DATA_DIR = Path("data")


def run_for_county(county: str) -> None:
    logger.info("=== Running GeoAI pipeline for %s ===", county)

    # 1. Boundary
    boundary = boundaries.load_county_boundary(county)

    # 2. DEM terrain derivatives (requires Copernicus credentials — see .env)
    dem_path = dem_terrain.fetch_glo30_dem()
    try:
        derivatives = dem_terrain.compute_terrain_derivatives(dem_path)
        dem_terrain.write_terrain_rasters(derivatives, DATA_DIR / "terrain" / county.lower())
    except Exception as exc:  # noqa: BLE001
        logger.warning("Terrain derivative step skipped (DEM not yet available): %s", exc)

    # 3. Borehole density (requires WRA WRIS / WPDx credentials — see .env)
    try:
        wris_points, wpdx_points = borehole_density.fetch_wra_wris_points(county), borehole_density.fetch_wpdx_points(county)
        grid = borehole_density.compute_borehole_density_grid(wpdx_points)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Borehole density step skipped: %s", exc)
        grid = None

    # 4. Earth Index embeddings (bulk workflow)
    try:
        tiles = earth_index_client.utm_tiles_for_north_rift()
        paths = [
            earth_index_client.download_embedding_tile(t, "2024-01-01_2025-01-01", DATA_DIR / "embeddings")
            for t in tiles
        ]
        logger.info("Downloaded %d embedding tiles", len(paths))
    except Exception as exc:  # noqa: BLE001
        logger.warning("Earth Index embeddings step skipped: %s", exc)

    # 5. Fusion — composite recharge vulnerability index
    if grid is not None and not grid.empty:
        scored = compute_recharge_vulnerability_index(grid)
        out_path = DATA_DIR / "risk_grid" / f"{county.lower()}_risk_grid.geojson"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        scored.to_file(out_path, driver="GeoJSON")
        logger.info("Wrote composite risk grid: %s", out_path)

    logger.info("=== Completed GeoAI pipeline for %s ===", county)


def main():
    parser = argparse.ArgumentParser(description="North Rift GeoAI pipeline")
    parser.add_argument("--county", type=str, help="Run for a single county, e.g. Nandi")
    parser.add_argument("--all-north-rift", action="store_true", help="Run for all five North Rift counties")
    args = parser.parse_args()

    if args.all_north_rift:
        for county in boundaries.NORTH_RIFT_COUNTIES:
            run_for_county(county)
    elif args.county:
        run_for_county(args.county)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
