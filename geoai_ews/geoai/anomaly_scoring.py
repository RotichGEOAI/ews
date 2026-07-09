"""
Embedding-based anomaly / similarity scoring.

Given a set of reference embeddings representing a known stress pattern
(e.g. a degraded wetland patch, a bare-soil borehole pad, a stressed maize
field), score every tile in the AOI by similarity to that reference set.
No external credentials required — pure numerical computation on already
downloaded Earth Index embeddings.
"""
from __future__ import annotations

import logging

import geopandas as gpd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


def compute_anomaly_scores(
    tile_embeddings: gpd.GeoDataFrame,
    reference_embeddings: np.ndarray,
    embedding_col: str = "embedding",
) -> gpd.GeoDataFrame:
    """Score each tile by max cosine similarity to any reference embedding.

    `reference_embeddings` should be an (n_refs, 384) array built from tiles
    the analyst has manually flagged as examples of the stress pattern of
    interest (e.g. Kingwal Wetland degradation, a known stressed field).

    Returns the input GeoDataFrame with an added `similarity_score`
    (0-1, higher = more similar to the reference pattern) and
    `anomaly_score` (1 - similarity, higher = more anomalous vs. reference).
    """
    if tile_embeddings.empty:
        logger.warning("compute_anomaly_scores called with empty tile_embeddings")
        return tile_embeddings

    embeddings_matrix = np.vstack(tile_embeddings[embedding_col].to_numpy())
    sims = cosine_similarity(embeddings_matrix, reference_embeddings)
    max_sim = sims.max(axis=1)

    out = tile_embeddings.copy()
    out["similarity_score"] = max_sim
    out["anomaly_score"] = 1.0 - max_sim
    return out


def flag_change_over_time(
    current: gpd.GeoDataFrame,
    previous: gpd.GeoDataFrame,
    embedding_col: str = "embedding",
    id_col: str = "id",
    change_threshold: float = 0.25,
) -> gpd.GeoDataFrame:
    """Flag tiles whose embedding has shifted significantly since the last pull
    (monitored-search style change detection for the Alert/Escalation agent).
    """
    merged = current.merge(
        previous[[id_col, embedding_col]], on=id_col, suffixes=("_curr", "_prev")
    )
    if merged.empty:
        return merged

    curr_matrix = np.vstack(merged[f"{embedding_col}_curr"].to_numpy())
    prev_matrix = np.vstack(merged[f"{embedding_col}_prev"].to_numpy())
    sims = np.array([
        cosine_similarity(c.reshape(1, -1), p.reshape(1, -1))[0, 0]
        for c, p in zip(curr_matrix, prev_matrix)
    ])
    merged["change_score"] = 1.0 - sims
    merged["changed"] = merged["change_score"] >= change_threshold
    n_changed = int(merged["changed"].sum())
    logger.info("Change detection: %d / %d tiles flagged as changed", n_changed, len(merged))
    return merged
