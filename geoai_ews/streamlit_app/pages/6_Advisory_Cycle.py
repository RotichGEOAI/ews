"""Run the 10-step agentic advisory workflow for a sample plot, interactively."""
import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ews.advisory_agent import AdvisoryAgent
from ews.forecast_agent import ForecastAgent
from ews.reconciliation_agent import ReconciliationAgent
from ews.alert_escalation_agent import AlertEscalationAgent

st.title("🤖 Advisory Cycle — Interactive Walkthrough")
st.caption(
    "This page runs steps 5-8 of the 10-step workflow (Reconciliation → Forecast "
    "→ Advisory generation → Alert/escalation) against manually entered values, "
    "without requiring a live database or messaging credentials. Use this to "
    "sanity-check thresholds before wiring in real data via the Data-Fetch Agent."
)

col1, col2 = st.columns(2)
with col1:
    ndvi_value = st.slider("NDVI value", 0.0, 1.0, 0.55, 0.01)
    ndvi_threshold = st.slider("NDVI healthy threshold", 0.0, 1.0, 0.5, 0.01)
with col2:
    embedding_anomaly_score = st.slider("Earth Index anomaly score", 0.0, 1.0, 0.42, 0.01)
    recharge_vulnerability_score = st.slider("Composite recharge vulnerability score", 0.0, 1.0, 0.55, 0.01)

if st.button("Run advisory cycle"):
    reconciliation = ReconciliationAgent().reconcile(
        plot_id=0,
        ndvi_value=ndvi_value,
        ndvi_healthy_threshold=ndvi_threshold,
        embedding_anomaly_score=embedding_anomaly_score,
    )
    st.write("**Step 5 — Reconciliation**")
    st.json(reconciliation.__dict__)

    forecast = ForecastAgent().generate_forecast(
        plot_id=0,
        rainfall_outlook_favorable=not reconciliation.discrepancy_flagged,
        recharge_vulnerability_score=recharge_vulnerability_score,
    )
    st.write("**Step 6 — Forecast**")
    st.json(forecast.__dict__)

    risk_class = "alert" if recharge_vulnerability_score >= 0.7 else (
        "watch" if recharge_vulnerability_score >= 0.4 else "low"
    )
    advisory = AdvisoryAgent().generate_advisory(
        plot_id=0, recommended_action=forecast.recommended_action, risk_class=risk_class
    )
    st.write("**Step 7 — Advisory message**")
    st.info(advisory.text)

    alert = AlertEscalationAgent().check_and_escalate(
        plot_id=0, change_score=embedding_anomaly_score, change_type="crop_stress_match"
    )
    st.write("**Step 8 — Alert/escalation**")
    if alert:
        st.warning(alert.text)
    else:
        st.write("No out-of-cycle alert triggered at this anomaly score.")
