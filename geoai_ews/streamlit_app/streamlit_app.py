"""
North Rift GeoAI + Agentic EWS — Streamlit front-end.

Run locally:
    streamlit run streamlit_app/streamlit_app.py

Deploy on Streamlit Community Cloud:
    Point the app at this file as the main module (see
    STREAMLIT_DEPLOYMENT_GUIDE.md in the project root).
"""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# Make the project root importable (config/, geoai/, ews/, db/, messaging/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# IMPORTANT: bridge Streamlit secrets into env vars BEFORE importing
# anything from config/geoai/ews — those modules read os.environ at import time.
from streamlit_app.secrets_bridge import load_secrets_into_env, credential_status

st.set_page_config(
    page_title="North Rift GeoAI + Agentic EWS",
    page_icon="🌾",
    layout="wide",
)

populated = load_secrets_into_env()

st.title("🌾 North Rift GeoAI + Agentic EWS")
st.caption("Nandi · Uasin Gishu · Trans Nzoia · Elgeyo-Marakwet · West Pokot")

st.markdown(
    """
Use the pages in the left sidebar to work through each module:

1. **Credentials Status** — confirm which API keys/IDs are currently loaded
2. **Upload Boundaries** — upload county/ward GeoJSON files
3. **DEM & Terrain** — upload a GLO-30 DEM GeoTIFF and compute slope/hillshade
4. **Borehole & Recharge Index** — upload/fetch borehole points and compute the
   composite recharge vulnerability grid
5. **Earth Index Embeddings** — upload embedding GeoParquet tiles and score
   anomalies against reference signatures
6. **Advisory Cycle** — run the 10-step agentic workflow for a sample plot

All modules import directly from `geoai/` and `ews/` — nothing here duplicates
the pipeline logic; this app is a thin interactive layer on top of it.
    """
)

with st.expander("Credential status (quick check)", expanded=False):
    status = credential_status()
    missing = [k for k, v in status.items() if not v]
    if missing:
        st.warning(f"{len(missing)} credential(s) not yet set. See the Credentials Status page for detail.")
    else:
        st.success("All known credentials are populated.")
