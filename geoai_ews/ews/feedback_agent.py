"""
Feedback-Learning Agent.

Logs farmer feedback on advisories (accurate / not accurate) and feeds it
back into reference-signature calibration for the Earth Index anomaly
scoring and forecast models. No external credentials required beyond the
database.
"""
from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from db.models import Advisory, FeedbackRecord

logger = logging.getLogger(__name__)


class FeedbackAgent:
    def __init__(self, session: Session):
        self.session = session

    def record_feedback(
        self, advisory_id: int, farmer_response: str, was_accurate: bool | None, notes: str = ""
    ) -> FeedbackRecord:
        record = FeedbackRecord(
            advisory_id=advisory_id,
            farmer_response=farmer_response,
            was_accurate=was_accurate,
            notes=notes,
        )
        self.session.add(record)
        self.session.commit()
        logger.info("Recorded feedback for advisory %s: accurate=%s", advisory_id, was_accurate)
        return record

    def accuracy_summary(self) -> dict:
        """Simple rollup used to recalibrate reference signatures / thresholds."""
        records = self.session.query(FeedbackRecord).all()
        total = len(records)
        accurate = sum(1 for r in records if r.was_accurate)
        return {
            "total_feedback": total,
            "accurate": accurate,
            "accuracy_rate": round(accurate / total, 3) if total else None,
        }
