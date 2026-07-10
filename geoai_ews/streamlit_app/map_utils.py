"""
Shared helper for feeding GeoDataFrames into st.map().

st.map() requires a plain DataFrame with a latitude/longitude column pair
named one of 'lat'/'lon', 'LAT'/'LON', or 'latitude'/'longitude' — it does
not understand a GeoDataFrame's `geometry` column directly, and different
upstream sources name their coordinate columns differently (WPDx uses
lat_deg/lon_deg; uploaded boundaries are polygons with no lat/lon columns
at all). This function normalizes any GeoDataFrame into the format st.map()
expects, regardless of source or geometry type.
"""
from __future__ import annotations

import geopandas as gpd
import pandas as pd


def gdf_to_map_df(gdf: gpd.GeoDataFrame) -> pd.DataFrame:
    """Return a minimal DataFrame with 'lat'/'lon' columns suitable for st.map().

    - Reprojects to EPSG:4326 if not already in that CRS.
    - Point geometries: uses the point's x/y directly.
    - Non-point geometries (polygons, lines): uses the geometry's centroid —
      sufficient for a location preview, not for precision analysis.
    """
    if gdf.empty:
        return pd.DataFrame(columns=["lat", "lon"])

    working = gdf
    if working.crs is not None and working.crs.to_epsg() != 4326:
        working = working.to_crs(epsg=4326)
    elif working.crs is None:
        # Assume already lon/lat if no CRS is set (common for hand-built test data)
        pass

    geoms = working.geometry
    is_point = geoms.geom_type.eq("Point")

    lon = pd.Series(index=geoms.index, dtype="float64")
    lat = pd.Series(index=geoms.index, dtype="float64")

    if is_point.any():
        point_geoms = geoms[is_point]
        lon.loc[is_point] = point_geoms.x.to_numpy()
        lat.loc[is_point] = point_geoms.y.to_numpy()

    if (~is_point).any():
        # Compute centroids in a projected CRS (UTM 36N, appropriate for the
        # North Rift/Kenya AOI) for accuracy, then reproject back to 4326 —
        # avoids geopandas' "geographic CRS centroid" accuracy warning.
        non_point_geoms = geoms[~is_point]
        projected_centroids = non_point_geoms.to_crs(epsg=32636).centroid
        centroids = gpd.GeoSeries(projected_centroids, crs=32636).to_crs(epsg=4326)
        lon.loc[~is_point] = centroids.x.to_numpy()
        lat.loc[~is_point] = centroids.y.to_numpy()

    return pd.DataFrame({"lat": lat.to_numpy(), "lon": lon.to_numpy()})
