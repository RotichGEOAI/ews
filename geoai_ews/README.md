# North Rift GeoAI + Agentic EWS — Production Codebase

Production-mode implementation of the workflows described in
**"North Rift GeoAI + Agentic EWS Master Document"**: the Nandi/North Rift
GeoAI pipeline (terrain, borehole pressure, Earth Index embeddings, composite
recharge vulnerability index) integrated into the seven-agent Agentic Early
Warning & Crop Advisory System (WhatsApp/SMS delivery).

## Structure

```
config/settings.py         Central credential/config loader (reads .env)
db/models.py               SQLAlchemy + GeoAlchemy2 models (PostGIS)
db/database.py             Engine/session setup
geoai/boundaries.py        County/ward boundary loading (North Rift)
geoai/dem_terrain.py       GLO-30 DEM -> slope, hillshade, elevation zones
geoai/borehole_density.py  WRA WRIS / WPDx -> borehole density grid
geoai/earth_index_client.py Earth Index bulk embeddings + app-search stub
geoai/anomaly_scoring.py   Embedding similarity/anomaly + change detection
geoai/recharge_index.py    Composite recharge vulnerability / risk fusion
ews/onboarding_agent.py    Farmer + plot registration, GeoAI cell keying
ews/data_fetch_agent.py    All scheduled EO/in-situ/GeoAI data pulls
ews/reconciliation_agent.py NDVI vs. embedding-anomaly cross-check
ews/forecast_agent.py      Planting-window recommendation
ews/advisory_agent.py      Farmer message drafting (+ water-stress clause)
ews/alert_escalation_agent.py Out-of-cycle change-triggered alerts
ews/feedback_agent.py      Farmer feedback logging + accuracy rollup
ews/orchestrator.py        The 10-step end-to-end workflow (see below)
messaging/whatsapp_client.py Meta WhatsApp Business Cloud API
messaging/sms_client.py    Twilio SMS fallback
pipeline.py                Standalone GeoAI pipeline runner (per county)
scripts/run_scheduled_cycle.py  Scheduler entry point (weekly cycle)
tests/                     Unit tests — no credentials required to run
```

## The 10-step workflow (ews/orchestrator.py)

1. Register & geolocate (Onboarding Agent)
2. Scheduled ingestion (Data-Fetch Agent)
3. Feature derivation (GeoAI layer)
4. Fusion & scoring (composite recharge vulnerability index)
5. Reconciliation (Ground-Truth Reconciliation Agent)
6. Forecast (Forecast Agent)
7. Advisory generation (Advisory-Generation Agent)
8. Alert/escalation (Alert/Escalation Agent)
9. Delivery (WhatsApp/SMS)
10. Feedback (Feedback-Learning Agent)

## Getting started

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # fill in real credentials — see CREDENTIALS_AND_ACCESS_REQUIRED.pdf
```

Run the standalone GeoAI pipeline for Nandi:
```bash
python pipeline.py --county Nandi
```

Initialize the database and run one advisory cycle for all registered plots:
```bash
python scripts/run_scheduled_cycle.py --init-db --once
```

Run the tests that require no external credentials:
```bash
pytest tests/
```

## Credentials

**Every external API/credential this codebase depends on is documented in
`CREDENTIALS_AND_ACCESS_REQUIRED.pdf`**, alongside `.env.example`, which lists
every environment variable the code reads. Populate `.env` before running
anything beyond the unit tests.

## Notes on production hardening

- Replace placeholder tile-code / cell-key logic (`_assign_earth_index_tile`,
  etc.) with your confirmed UTM/MGRS tiling scheme.
- `geoai/earth_index_client.submit_app_search` raises `NotImplementedError` —
  Earth Genome had no documented public REST API at time of writing; use the
  bulk embeddings path or confirm API availability directly with them.
- Add retry/backoff and circuit breakers around all external HTTP calls
  before production deployment.
- Add structured logging/observability (e.g. OpenTelemetry) if operating at
  scale across all five North Rift counties.
