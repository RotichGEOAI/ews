"""
Ground-Truth Reconciliation Agent.

Cross-checks NDVI/rainfall signal against:
  - Earth Index embedding anomaly score (independent pattern-based check)
  - In-situ AWS / farmer-reported ground truth

No external credentials required — this agent operates on already-fetched
data from the Data-Fetch Agent.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

DISCREPANCY_THRESHOLD = 0.35  # anomaly score vs. NDVI-implied health mismatch


@dataclass
class ReconciliationResult:
    plot_id: int
    ndvi_ok: bool
    embedding_anomaly_score: float
    discrepancy_flagged: bool
    notes: str


class ReconciliationAgent:
    def reconcile(
        self,
        plot_id: int,
        ndvi_value: float,
        ndvi_healthy_threshold: float,
        embedding_anomaly_score: float,
        ground_truth_report: str | None = None,
    ) -> ReconciliationResult:
        ndvi_ok = ndvi_value >= ndvi_healthy_threshold

        discrepancy = ndvi_ok and embedding_anomaly_score >= DISCREPANCY_THRESHOLD
        notes = ""
        if discrepancy:
            notes = (
                "NDVI reads healthy but Earth Index embedding anomaly score "
                f"({embedding_anomaly_score:.2f}) matches known stress signatures — "
                "flagging for manual review rather than auto-publishing an advisory."
            )
            logger.warning("Reconciliation discrepancy for plot %s: %s", plot_id, notes)
        elif ground_truth_report:
            notes = f"Ground truth report on file: {ground_truth_report}"

        return ReconciliationResult(
            plot_id=plot_id,
            ndvi_ok=ndvi_ok,
            embedding_anomaly_score=embedding_anomaly_score,
            discrepancy_flagged=discrepancy,
            notes=notes,
        )
