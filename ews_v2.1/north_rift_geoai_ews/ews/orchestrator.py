"""
Orchestrator — implements the 10-step end-to-end integration workflow from
the master document ("North Rift GeoAI + Agentic EWS Master Document",
section 8):

  1. Register & geolocate
  2. Scheduled ingestion
  3. Feature derivation
  4. Fusion & scoring
  5. Reconciliation
  6. Forecast
  7. Advisory generation
  8. Alert / escalation
  9. Delivery
  10. Feedback

This module wires the individual agents together in sequence. It is the
main entry point for a single plot's advisory cycle, and is designed to be
called by a scheduler (see scripts/run_scheduled_cycle.py) for every
registered plot.
"""
from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from db.models import Advisory, Plot
from ews.advisory_agent import AdvisoryAgent
from ews.alert_escalation_agent import AlertEscalationAgent
from ews.data_fetch_agent import DataFetchAgent
from ews.feedback_agent import FeedbackAgent
from ews.forecast_agent import ForecastAgent
from ews.reconciliation_agent import ReconciliationAgent
from geoai.recharge_index import compute_recharge_vulnerability_index
from messaging.whatsapp_client import WhatsAppClient

logger = logging.getLogger(__name__)


class AdvisoryOrchestrator:
    def __init__(self, session: Session):
        self.session = session
        self.data_fetch = DataFetchAgent()
        self.reconciliation = ReconciliationAgent()
        self.forecast = ForecastAgent()
        self.advisory = AdvisoryAgent()
        self.alert_escalation = AlertEscalationAgent(self.advisory)
        self.feedback = FeedbackAgent(session)

    def run_cycle_for_plot(self, plot: Plot) -> Advisory:
        """Run the full 10-step workflow for a single plot and return the
        Advisory record that was generated (and, in production, sent).
        """
        logger.info("=== Starting advisory cycle for plot %s ===", plot.id)

        # Step 2: Scheduled ingestion (illustrative — plug in real lon/lat and dates)
        lon, lat = self._plot_lonlat(plot)
        rainfall = self.data_fetch.fetch_rainfall(lon, lat, "2026-06-01", "2026-07-01")
        power = self.data_fetch.fetch_nasa_power(lon, lat, "2026-06-01", "2026-07-01") if False else {}
        # NOTE: NASA POWER call above disabled by default in this scaffold to avoid
        # requiring live network access during dry-runs; enable once ready.

        # Step 3-4: Feature derivation & fusion (assumes precomputed grid cell lookup
        # in a real deployment; here we illustrate with placeholder scalar inputs)
        ndvi_value = 0.55          # placeholder — replace with real MODIS NDVI lookup
        ndvi_threshold = 0.5
        embedding_anomaly_score = 0.42   # placeholder — replace with Earth Index score lookup
        recharge_vulnerability_score = 0.55  # placeholder — replace with grid lookup by plot.borehole_grid_cell_id

        # Step 5: Reconciliation
        reconciliation_result = self.reconciliation.reconcile(
            plot_id=plot.id,
            ndvi_value=ndvi_value,
            ndvi_healthy_threshold=ndvi_threshold,
            embedding_anomaly_score=embedding_anomaly_score,
        )

        # Step 6: Forecast
        forecast_result = self.forecast.generate_forecast(
            plot_id=plot.id,
            rainfall_outlook_favorable=not reconciliation_result.discrepancy_flagged,
            recharge_vulnerability_score=recharge_vulnerability_score,
        )

        # Determine risk class the same way the fusion grid would
        risk_class = "alert" if recharge_vulnerability_score >= 0.7 else (
            "watch" if recharge_vulnerability_score >= 0.4 else "low"
        )

        # Step 7: Advisory generation
        advisory_msg = self.advisory.generate_advisory(
            plot_id=plot.id,
            recommended_action=forecast_result.recommended_action,
            risk_class=risk_class,
        )

        # Step 8: Alert/escalation (independent of the scheduled cycle in production;
        # shown here for completeness within a single cycle)
        alert_msg = self.alert_escalation.check_and_escalate(
            plot_id=plot.id, change_score=embedding_anomaly_score, change_type="crop_stress_match"
        )
        final_message = alert_msg if alert_msg else advisory_msg

        # Persist advisory
        advisory_record = Advisory(
            plot_id=plot.id,
            message_text=final_message.text,
            advisory_type=final_message.advisory_type,
            water_stress_clause_included=final_message.water_stress_clause_included,
        )
        self.session.add(advisory_record)
        self.session.commit()

        # Step 9: Delivery
        self._deliver(plot, final_message.text, advisory_record)

        logger.info("=== Completed advisory cycle for plot %s ===", plot.id)
        return advisory_record

    def _deliver(self, plot: Plot, message: str, advisory_record: Advisory) -> None:
        farmer = plot.farmer
        try:
            if farmer.preferred_channel == "whatsapp":
                client = WhatsAppClient()
                client.send_text_message(farmer.phone_number, message)
            else:
                from messaging.sms_client import SmsClient
                client = SmsClient()
                client.send_sms(farmer.phone_number, message)
            advisory_record.delivery_status = "sent"
        except EnvironmentError as exc:
            logger.error("Delivery skipped — missing credentials: %s", exc)
            advisory_record.delivery_status = "failed"
        self.session.commit()

    @staticmethod
    def _plot_lonlat(plot: Plot) -> tuple[float, float]:
        from geoalchemy2.shape import to_shape
        point = to_shape(plot.geom)
        return point.x, point.y

    # Step 10: Feedback — exposed separately, invoked when a farmer replies
    def record_farmer_feedback(self, advisory_id: int, response_text: str, was_accurate: bool | None):
        return self.feedback.record_feedback(advisory_id, response_text, was_accurate)
