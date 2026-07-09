"""Unit tests for the composite recharge vulnerability index (no credentials needed)."""
import geopandas as gpd
from shapely.geometry import box

from geoai.recharge_index import compute_recharge_vulnerability_index


def _sample_grid() -> gpd.GeoDataFrame:
    data = [
        {"geometry": box(0, 0, 1, 1), "slope_deg": 5, "borehole_density_per_km2": 1,
         "anomaly_score": 0.1, "ndvi_deficit": 0.1, "rainfall_deficit": 0.1},
        {"geometry": box(1, 0, 2, 1), "slope_deg": 25, "borehole_density_per_km2": 8,
         "anomaly_score": 0.8, "ndvi_deficit": 0.6, "rainfall_deficit": 0.5},
    ]
    return gpd.GeoDataFrame(data, crs="EPSG:4326")


def test_composite_risk_score_ranks_expected_cell_higher():
    grid = _sample_grid()
    scored = compute_recharge_vulnerability_index(grid)
    assert scored.iloc[1]["composite_risk_score"] > scored.iloc[0]["composite_risk_score"]
    assert scored.iloc[1]["risk_class"] in ("watch", "alert")
    assert scored.iloc[0]["risk_class"] == "low"


def test_risk_class_thresholds_present():
    grid = _sample_grid()
    scored = compute_recharge_vulnerability_index(grid)
    assert set(scored["risk_class"]).issubset({"low", "watch", "alert"})
