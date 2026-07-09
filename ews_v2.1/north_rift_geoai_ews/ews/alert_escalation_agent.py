"""
Alert/Escalation Agent.

Issues out-of-cycle alerts when a recurring Earth Index monitored search
detects new bare-soil/borehole expansion or wetland conversion near a
registered plot. No external credentials required beyond messaging (see
messaging/ module).
"""
from __future__ import annotations

import logging

from ews.advisory_agent import AdvisoryAgent, AdvisoryMessage

logger = logging.getLogger(__name__)

CHANGE_SCORE_ALERT_THRESHOLD = 0.25


class AlertEscalationAgent:
    def __init__(self, advisory_agent: AdvisoryAgent | None = None):
        self.advisory_agent = advisory_agent or AdvisoryAgent()

    def check_and_escalate(self, plot_id: int, change_score: float, change_type: str) -> AdvisoryMessage | None:
        if change_score < CHANGE_SCORE_ALERT_THRESHOLD:
            return None

        reason_map = {
            "bare_soil_expansion": "new bare-soil / potential borehole activity detected nearby",
            "wetland_conversion": "wetland conversion detected near your plot",
            "crop_stress_match": "your field's imagery pattern now matches known stressed-field signatures",
        }
        reason = reason_map.get(change_type, "an environmental change was detected near your plot")

        alert = self.advisory_agent.generate_alert(plot_id, reason)
        logger.warning(
            "Escalating alert for plot %s: change_score=%.2f, type=%s", plot_id, change_score, change_type
        )
        return alert
