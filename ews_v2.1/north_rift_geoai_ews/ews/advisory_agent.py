"""
Advisory-Generation Agent.

Drafts the farmer-facing message, adding a water-stress/aquifer-risk clause
when the composite risk grid flags Watch or Alert status for the plot's cell.
No external credentials required.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

ACTION_COPY = {
    "plant_now": "Conditions look favorable — you can proceed with planting this week.",
    "delay_7_days": "Hold off planting for about 7 days; conditions are borderline.",
    "delay_14_days": "Delay planting by at least 14 days — current conditions carry elevated risk.",
}

WATER_STRESS_CLAUSE = (
    " Note: water resource monitoring for your area shows elevated aquifer/borehole "
    "pressure — consider water-conserving practices and verify any new borehole "
    "has a valid WRA permit."
)


@dataclass
class AdvisoryMessage:
    plot_id: int
    text: str
    advisory_type: str  # "scheduled" | "alert"
    water_stress_clause_included: bool


class AdvisoryAgent:
    def generate_advisory(
        self,
        plot_id: int,
        recommended_action: str,
        risk_class: str,
        language: str = "en",
    ) -> AdvisoryMessage:
        base_message = ACTION_COPY.get(recommended_action, "Please check with your local extension officer.")
        include_water_clause = risk_class in ("watch", "alert")
        message = base_message + (WATER_STRESS_CLAUSE if include_water_clause else "")

        # Language localisation would be applied here (e.g. Swahili/Kalenjin templates).
        logger.info("Generated advisory for plot %s (water_clause=%s)", plot_id, include_water_clause)
        return AdvisoryMessage(
            plot_id=plot_id,
            text=message,
            advisory_type="scheduled",
            water_stress_clause_included=include_water_clause,
        )

    def generate_alert(self, plot_id: int, reason: str) -> AdvisoryMessage:
        message = f"Alert: {reason}. Please inspect your plot and contact your extension officer if concerned."
        logger.warning("Generated ALERT advisory for plot %s: %s", plot_id, reason)
        return AdvisoryMessage(
            plot_id=plot_id, text=message, advisory_type="alert", water_stress_clause_included=True
        )
