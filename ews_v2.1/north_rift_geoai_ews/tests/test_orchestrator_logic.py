"""Unit tests for individual agent logic (no database / network required)."""
from ews.advisory_agent import AdvisoryAgent
from ews.forecast_agent import ForecastAgent
from ews.reconciliation_agent import ReconciliationAgent


def test_forecast_agent_delays_planting_on_high_vulnerability():
    agent = ForecastAgent()
    result = agent.generate_forecast(plot_id=1, rainfall_outlook_favorable=True, recharge_vulnerability_score=0.8)
    assert result.recommended_action == "delay_14_days"


def test_forecast_agent_plants_now_on_low_vulnerability():
    agent = ForecastAgent()
    result = agent.generate_forecast(plot_id=1, rainfall_outlook_favorable=True, recharge_vulnerability_score=0.1)
    assert result.recommended_action == "plant_now"


def test_reconciliation_flags_discrepancy():
    agent = ReconciliationAgent()
    result = agent.reconcile(
        plot_id=1, ndvi_value=0.8, ndvi_healthy_threshold=0.5, embedding_anomaly_score=0.5
    )
    assert result.discrepancy_flagged is True


def test_advisory_includes_water_clause_on_watch_risk():
    agent = AdvisoryAgent()
    msg = agent.generate_advisory(plot_id=1, recommended_action="plant_now", risk_class="watch")
    assert msg.water_stress_clause_included is True
    assert "water" in msg.text.lower()
