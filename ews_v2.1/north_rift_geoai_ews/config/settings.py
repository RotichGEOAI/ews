"""
Central configuration loader.

All credentials and environment-specific values are read from environment
variables (populated via a `.env` file in local/dev, or a real secrets
manager / CI variables in production). Nothing is hard-coded.

See CREDENTIALS_AND_ACCESS_REQUIRED.pdf for what each variable is, where to
obtain it, and which pipeline component depends on it.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)


def _get(key: str, default: str | None = None, required: bool = False) -> str | None:
    val = os.getenv(key, default)
    if required and not val:
        raise EnvironmentError(
            f"Missing required environment variable: {key}. "
            f"See CREDENTIALS_AND_ACCESS_REQUIRED.pdf."
        )
    return val


@dataclass
class Settings:
    environment: str = field(default_factory=lambda: _get("ENVIRONMENT", "development"))
    log_level: str = field(default_factory=lambda: _get("LOG_LEVEL", "INFO"))

    # Copernicus / DEM
    copernicus_client_id: str | None = field(default_factory=lambda: _get("COPERNICUS_CLIENT_ID"))
    copernicus_client_secret: str | None = field(default_factory=lambda: _get("COPERNICUS_CLIENT_SECRET"))
    copernicus_dem_bbox: str = field(
        default_factory=lambda: _get("COPERNICUS_DEM_BBOX", "34.74,-0.108,35.44,0.563")
    )

    # Earth Index
    earth_index_account_email: str | None = field(default_factory=lambda: _get("EARTH_INDEX_APP_ACCOUNT_EMAIL"))
    earth_index_api_key: str | None = field(default_factory=lambda: _get("EARTH_INDEX_API_KEY"))
    earth_index_source_coop_token: str | None = field(
        default_factory=lambda: _get("EARTH_INDEX_SOURCE_COOP_TOKEN")
    )

    # NASA Earthdata / GEE
    nasa_earthdata_username: str | None = field(default_factory=lambda: _get("NASA_EARTHDATA_USERNAME"))
    nasa_earthdata_password: str | None = field(default_factory=lambda: _get("NASA_EARTHDATA_PASSWORD"))
    gee_service_account_email: str | None = field(default_factory=lambda: _get("GEE_SERVICE_ACCOUNT_EMAIL"))
    gee_service_account_key_path: str | None = field(
        default_factory=lambda: _get("GEE_SERVICE_ACCOUNT_KEY_PATH")
    )

    # ICPAC / TAHMO
    icpac_api_key: str | None = field(default_factory=lambda: _get("ICPAC_API_KEY"))
    tahmo_username: str | None = field(default_factory=lambda: _get("TAHMO_API_USERNAME"))
    tahmo_password: str | None = field(default_factory=lambda: _get("TAHMO_API_PASSWORD"))

    # Water resources
    wra_wris_api_key: str | None = field(default_factory=lambda: _get("WRA_WRIS_API_KEY"))
    wra_wris_client_id: str | None = field(default_factory=lambda: _get("WRA_WRIS_CLIENT_ID"))
    wpdx_api_key: str | None = field(default_factory=lambda: _get("WPDX_API_KEY"))

    # ACLED
    acled_api_key: str | None = field(default_factory=lambda: _get("ACLED_API_KEY"))
    acled_email: str | None = field(default_factory=lambda: _get("ACLED_EMAIL"))

    # Messaging — WhatsApp Business Cloud API
    meta_whatsapp_phone_number_id: str | None = field(
        default_factory=lambda: _get("META_WHATSAPP_PHONE_NUMBER_ID")
    )
    meta_whatsapp_business_account_id: str | None = field(
        default_factory=lambda: _get("META_WHATSAPP_BUSINESS_ACCOUNT_ID")
    )
    meta_whatsapp_access_token: str | None = field(
        default_factory=lambda: _get("META_WHATSAPP_ACCESS_TOKEN")
    )
    meta_app_id: str | None = field(default_factory=lambda: _get("META_APP_ID"))
    meta_app_secret: str | None = field(default_factory=lambda: _get("META_APP_SECRET"))

    # Messaging — Twilio
    twilio_account_sid: str | None = field(default_factory=lambda: _get("TWILIO_ACCOUNT_SID"))
    twilio_auth_token: str | None = field(default_factory=lambda: _get("TWILIO_AUTH_TOKEN"))
    twilio_from_number: str | None = field(default_factory=lambda: _get("TWILIO_FROM_NUMBER"))

    # Database
    database_url: str = field(
        default_factory=lambda: _get(
            "DATABASE_URL", "postgresql://user:password@localhost:5432/north_rift_ews"
        )
    )


settings = Settings()
