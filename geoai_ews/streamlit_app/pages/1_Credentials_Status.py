"""Credentials Status page — shows which env vars are populated, never their values."""
import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from streamlit_app.secrets_bridge import load_secrets_into_env, credential_status

st.title("🔑 Credentials Status")
load_secrets_into_env()

status = credential_status()
rows = [{"Environment variable": k, "Set?": "✅" if v else "❌"} for k, v in status.items()]
st.dataframe(rows, width="stretch", hide_index=True)

st.info(
    "Fill in `.streamlit/secrets.toml` (local) or the Secrets panel in Streamlit "
    "Community Cloud (deployed) to populate these. See "
    "CREDENTIALS_AND_ACCESS_REQUIRED.pdf for where to obtain each one."
)
