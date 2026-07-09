"""
Bridges Streamlit's st.secrets (TOML) into the same environment variables
that config/settings.py already reads via python-dotenv. This means the
core geoai/ and ews/ modules require ZERO code changes to run inside
Streamlit — they stay framework-agnostic.

Call `load_secrets_into_env()` once at the very top of app.py, before
importing anything from config/geoai/ews/db/messaging.
"""
from __future__ import annotations

import os

import streamlit as st

# Maps st.secrets[section][key] -> environment variable name
_SECRET_MAP = {
    ("copernicus", "client_id"): "COPERNICUS_CLIENT_ID",
    ("copernicus", "client_secret"): "COPERNICUS_CLIENT_SECRET",
    ("copernicus", "dem_bbox"): "COPERNICUS_DEM_BBOX",
    ("earth_index", "account_email"): "EARTH_INDEX_APP_ACCOUNT_EMAIL",
    ("earth_index", "api_key"): "EARTH_INDEX_API_KEY",
    ("earth_index", "source_coop_token"): "EARTH_INDEX_SOURCE_COOP_TOKEN",
    ("nasa", "earthdata_username"): "NASA_EARTHDATA_USERNAME",
    ("nasa", "earthdata_password"): "NASA_EARTHDATA_PASSWORD",
    ("gee", "service_account_email"): "GEE_SERVICE_ACCOUNT_EMAIL",
    ("gee", "service_account_key_path"): "GEE_SERVICE_ACCOUNT_KEY_PATH",
    ("icpac", "api_key"): "ICPAC_API_KEY",
    ("tahmo", "username"): "TAHMO_API_USERNAME",
    ("tahmo", "password"): "TAHMO_API_PASSWORD",
    ("wra_wris", "api_key"): "WRA_WRIS_API_KEY",
    ("wra_wris", "client_id"): "WRA_WRIS_CLIENT_ID",
    ("wpdx", "api_key"): "WPDX_API_KEY",
    ("acled", "api_key"): "ACLED_API_KEY",
    ("acled", "email"): "ACLED_EMAIL",
    ("whatsapp", "phone_number_id"): "META_WHATSAPP_PHONE_NUMBER_ID",
    ("whatsapp", "business_account_id"): "META_WHATSAPP_BUSINESS_ACCOUNT_ID",
    ("whatsapp", "access_token"): "META_WHATSAPP_ACCESS_TOKEN",
    ("whatsapp", "app_id"): "META_APP_ID",
    ("whatsapp", "app_secret"): "META_APP_SECRET",
    ("twilio", "account_sid"): "TWILIO_ACCOUNT_SID",
    ("twilio", "auth_token"): "TWILIO_AUTH_TOKEN",
    ("twilio", "from_number"): "TWILIO_FROM_NUMBER",
    ("database", "url"): "DATABASE_URL",
}


def load_secrets_into_env() -> list[str]:
    """Copy every configured st.secrets value into os.environ.

    Returns the list of environment variable names that were populated,
    so the app can show the person which credentials are actually live.
    """
    populated = []
    for (section, key), env_var in _SECRET_MAP.items():
        try:
            value = st.secrets[section][key]
        except (KeyError, FileNotFoundError):
            continue
        if value:
            os.environ[env_var] = str(value)
            populated.append(env_var)
    return populated


def credential_status() -> dict[str, bool]:
    """Report which of the known env vars are currently set (for the
    Credentials Status page) — never displays the actual values.
    """
    all_vars = sorted({v for v in _SECRET_MAP.values()})
    return {var: bool(os.getenv(var)) for var in all_vars}
