"""
Forecast Agent.

Generates the planting-window / crop-stage recommendation, conditioned on
the composite recharge vulnerability index computed by the GeoAI layer.
No external credentials required.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ForecastResult:
    plot_id: int
    recommended_action: str  # e.g. "plant_now" | "delay_7_days" | "delay_14_days"
    confidence: float
    recharge_vulnerability_score: float
    rationale: str


class ForecastAgent:
    def generate_forecast(
        self,
        plot_id: int,
        rainfall_outlook_favorable: bool,
        recharge_vulnerability_score: float,
        base_confidence: float = 0.75,
    ) -> ForecastResult:
        if recharge_vulnerability_score >= 0.7:
            action = "delay_14_days"
            rationale = "High recharge vulnerability (aquifer/borehole pressure) — recommend delaying planting."
        elif recharge_vulnerability_score >= 0.4 or not rainfall_outlook_favorable:
            action = "delay_7_days"
            rationale = "Moderate recharge vulnerability or unfavorable rainfall outlook — short delay advised."
        else:
            action = "plant_now"
            rationale = "Rainfall outlook favorable and recharge vulnerability low."

        confidence = base_confidence - (0.1 if recharge_vulnerability_score >= 0.7 else 0.0)

        logger.info("Forecast for plot %s: %s (score=%.2f)", plot_id, action, recharge_vulnerability_score)
        return ForecastResult(
            plot_id=plot_id,
            recommended_action=action,
            confidence=round(confidence, 2),
            recharge_vulnerability_score=recharge_vulnerability_score,
            rationale=rationale,
        )
