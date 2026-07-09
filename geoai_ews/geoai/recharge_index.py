"""
Composite recharge vulnerability index and full risk-grid fusion.

Combines:
  - DEM terrain derivatives (slope, elevation zone)
  - Borehole density grid
  - Earth Index embedding anomaly score
  - NDVI / rainfall deficit (from the EWS EO Data Layer)

No external credentials required — this is a pure fusion/scoring step over
already-computed layers.
"""
from __future__ import annotations

import logging

import geopandas as gpd
import numpy as np

logger = logging.getLogger(__name__)

DEFAULT_WEIGHTS = {
    "slope": 0.15,
    "borehole_density": 0.30,
    "embedding_anomaly": 0.30,
    "ndvi_deficit": 0.15,
    "rainfall_deficit": 0.10,
}

RISK_THRESHOLDS = {
    "watch": 0.4,
    "alert": 0.7,
}


def _normalize(series: "np.ndarray | gpd.pd.Series") -> np.ndarray:
    arr = np.asarray(series, dtype="float64")
    if np.nanmax(arr) == np.nanmin(arr):
        return np.zeros_like(arr)
    return (arr - np.nanmin(arr)) / (np.nanmax(arr) - np.nanmin(arr))


def compute_recharge_vulnerability_index(
    grid: gpd.GeoDataFrame,
    weights: dict[str, float] = None,
) -> gpd.GeoDataFrame:
    """Compute the composite recharge vulnerability / risk score per grid cell.

    Expects `grid` to already contain (post-join) columns:
    slope_deg, borehole_density_per_km2, anomaly_score, ndvi_deficit, rainfall_deficit
    """
    weights = weights or DEFAULT_WEIGHTS
    out = grid.copy()

    norm_slope = _normalize(out.get("slope_deg", np.zeros(len(out))))
    norm_borehole = _normalize(out.get("borehole_density_per_km2", np.zeros(len(out))))
    norm_anomaly = _normalize(out.get("anomaly_score", np.zeros(len(out))))
    norm_ndvi_deficit = _normalize(out.get("ndvi_deficit", np.zeros(len(out))))
    norm_rain_deficit = _normalize(out.get("rainfall_deficit", np.zeros(len(out))))

    out["composite_risk_score"] = (
        weights["slope"] * norm_slope
        + weights["borehole_density"] * norm_borehole
        + weights["embedding_anomaly"] * norm_anomaly
        + weights["ndvi_deficit"] * norm_ndvi_deficit
        + weights["rainfall_deficit"] * norm_rain_deficit
    )

    out["risk_class"] = np.select(
        [
            out["composite_risk_score"] >= RISK_THRESHOLDS["alert"],
            out["composite_risk_score"] >= RISK_THRESHOLDS["watch"],
        ],
        ["alert", "watch"],
        default="low",
    )

    logger.info(
        "Risk grid computed: %d cells (%d alert, %d watch, %d low)",
        len(out),
        int((out["risk_class"] == "alert").sum()),
        int((out["risk_class"] == "watch").sum()),
        int((out["risk_class"] == "low").sum()),
    )
    return out
