"""
Data-Fetch Agent.

Pulls all EO / in-situ / GeoAI source data on a schedule:
  - CHIRPS / TAMSAT rainfall            (public, no key)
  - NASA POWER meteorological variables (public, no key)
  - MODIS NDVI (via NASA Earthdata or Google Earth Engine)
  - ICPAC seasonal outlook
  - TAHMO in-situ station data
  - Earth Index embeddings (bulk / Source Cooperative)
  - WRA WRIS / WPDx borehole data

CREDENTIALS REQUIRED: see per-source docstrings and CREDENTIALS_AND_ACCESS_REQUIRED.pdf.
"""
from __future__ import annotations

import logging
from pathlib import Path

import requests

from config.settings import settings
from geoai import earth_index_client, borehole_density

logger = logging.getLogger(__name__)

CHIRPS_BASE_URL = "https://iridl.ldeo.columbia.edu/SOURCES/.UCSB/.CHIRPS/.v2p0"  # public
NASA_POWER_BASE_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"     # public


class DataFetchAgent:
    """Coordinates all scheduled data pulls for a given AOI / plot cell."""

    def fetch_rainfall(self, lon: float, lat: float, start: str, end: str) -> dict:
        """CHIRPS rainfall — public endpoint, no credentials required."""
        # Illustrative: real implementation should call the CHIRPS/TAMSAT
        # data service appropriate for the deployment (IRI Data Library,
        # Climate Hazards Center THREDDS, or a pre-mirrored local copy).
        logger.info("Fetching CHIRPS rainfall for (%s, %s) %s -> %s", lon, lat, start, end)
        return {"source": "CHIRPS", "lon": lon, "lat": lat, "start": start, "end": end, "values": []}

    def fetch_nasa_power(self, lon: float, lat: float, start: str, end: str) -> dict:
        """NASA POWER meteorological variables — public API, no key required."""
        params = {
            "parameters": "T2M,RH2M,WS2M,PRECTOTCORR",
            "community": "AG",
            "longitude": lon,
            "latitude": lat,
            "start": start.replace("-", ""),
            "end": end.replace("-", ""),
            "format": "JSON",
        }
        resp = requests.get(NASA_POWER_BASE_URL, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def fetch_modis_ndvi(self, lon: float, lat: float, start: str, end: str) -> dict:
        """MODIS NDVI via NASA Earthdata (LP DAAC) or Google Earth Engine.

        CREDENTIALS REQUIRED: NASA_EARTHDATA_USERNAME/PASSWORD, or
        GEE_SERVICE_ACCOUNT_EMAIL + GEE_SERVICE_ACCOUNT_KEY_PATH.
        """
        if settings.gee_service_account_key_path:
            logger.info("Using Google Earth Engine service account for MODIS NDVI pull")
            # ee.Initialize(credentials=...) — implement with the `earthengine-api` package
        elif settings.nasa_earthdata_username and settings.nasa_earthdata_password:
            logger.info("Using NASA Earthdata credentials for MODIS NDVI pull via LP DAAC")
        else:
            raise EnvironmentError(
                "No MODIS access path configured. Set either "
                "GEE_SERVICE_ACCOUNT_EMAIL/GEE_SERVICE_ACCOUNT_KEY_PATH or "
                "NASA_EARTHDATA_USERNAME/NASA_EARTHDATA_PASSWORD."
            )
        return {"source": "MODIS_NDVI", "lon": lon, "lat": lat, "start": start, "end": end, "values": []}

    def fetch_icpac_outlook(self, region: str) -> dict:
        """ICPAC seasonal rainfall outlook. CREDENTIALS: ICPAC_API_KEY if using partner API."""
        if not settings.icpac_api_key:
            logger.warning(
                "ICPAC_API_KEY not set — falling back to public bulletin scraping/manual ingestion."
            )
        return {"source": "ICPAC", "region": region, "outlook": "not yet fetched"}

    def fetch_tahmo_station_data(self, station_id: str, start: str, end: str) -> dict:
        """TAHMO in-situ AWS data. CREDENTIALS: TAHMO_API_USERNAME/PASSWORD."""
        if not (settings.tahmo_username and settings.tahmo_password):
            raise EnvironmentError("TAHMO_API_USERNAME/TAHMO_API_PASSWORD not set.")
        return {"source": "TAHMO", "station_id": station_id, "start": start, "end": end, "values": []}

    def fetch_earth_index_embeddings(self, tile_codes: list[str], date_range: str, out_dir: Path):
        """Bulk Earth Index embeddings pull (Source Cooperative GeoParquet)."""
        paths = []
        for tile in tile_codes:
            path = earth_index_client.download_embedding_tile(tile, date_range, out_dir)
            paths.append(path)
        return paths

    def fetch_borehole_layers(self, county: str):
        """WRA WRIS + WPDx borehole/water-point pull for a county."""
        wris_points = borehole_density.fetch_wra_wris_points(county)
        wpdx_points = borehole_density.fetch_wpdx_points(county)
        return wris_points, wpdx_points
