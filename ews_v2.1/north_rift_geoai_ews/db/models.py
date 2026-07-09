"""
SQLAlchemy + GeoAlchemy2 models for the Platform Data Store (PostGIS/TimescaleDB).

Requires DATABASE_URL to point at a PostGIS-enabled Postgres instance.
See CREDENTIALS_AND_ACCESS_REQUIRED.pdf, section "Database".
"""
from __future__ import annotations

import datetime as dt

from geoalchemy2 import Geometry
from sqlalchemy import (
    Column, DateTime, Float, ForeignKey, Integer, String, JSON, Boolean
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Farmer(Base):
    __tablename__ = "farmers"

    id = Column(Integer, primary_key=True)
    phone_number = Column(String, unique=True, nullable=False)
    preferred_channel = Column(String, default="whatsapp")  # whatsapp | ussd | sms
    language = Column(String, default="en")
    registered_at = Column(DateTime, default=dt.datetime.utcnow)

    plots = relationship("Plot", back_populates="farmer")


class Plot(Base):
    __tablename__ = "plots"

    id = Column(Integer, primary_key=True)
    farmer_id = Column(Integer, ForeignKey("farmers.id"), nullable=False)
    county = Column(String, nullable=False)
    ward = Column(String, nullable=True)
    geom = Column(Geometry(geometry_type="POINT", srid=4326), nullable=False)

    # Cell keys used to join GeoAI layers (computed at onboarding)
    earth_index_tile_id = Column(String, nullable=True)
    dem_cell_id = Column(String, nullable=True)
    borehole_grid_cell_id = Column(String, nullable=True)

    farmer = relationship("Farmer", back_populates="plots")


class RiskGridCell(Base):
    """Sub-county composite risk grid cell — output of the fusion/scoring step."""
    __tablename__ = "risk_grid_cells"

    id = Column(Integer, primary_key=True)
    cell_id = Column(String, unique=True, nullable=False)
    county = Column(String, nullable=False)
    ward = Column(String, nullable=True)
    geom = Column(Geometry(geometry_type="POLYGON", srid=4326), nullable=False)

    recharge_vulnerability_score = Column(Float, nullable=True)
    embedding_anomaly_score = Column(Float, nullable=True)
    ndvi_deficit_score = Column(Float, nullable=True)
    rainfall_deficit_score = Column(Float, nullable=True)
    composite_risk_score = Column(Float, nullable=True)
    risk_class = Column(String, nullable=True)  # low | watch | alert

    computed_at = Column(DateTime, default=dt.datetime.utcnow)


class Advisory(Base):
    __tablename__ = "advisories"

    id = Column(Integer, primary_key=True)
    plot_id = Column(Integer, ForeignKey("plots.id"), nullable=False)
    risk_cell_id = Column(String, nullable=True)
    message_text = Column(String, nullable=False)
    advisory_type = Column(String, default="scheduled")  # scheduled | alert
    water_stress_clause_included = Column(Boolean, default=False)
    sent_at = Column(DateTime, default=dt.datetime.utcnow)
    delivery_status = Column(String, default="pending")  # pending | sent | failed
    raw_payload = Column(JSON, nullable=True)


class FeedbackRecord(Base):
    __tablename__ = "feedback_records"

    id = Column(Integer, primary_key=True)
    advisory_id = Column(Integer, ForeignKey("advisories.id"), nullable=False)
    farmer_response = Column(String, nullable=True)
    was_accurate = Column(Boolean, nullable=True)
    notes = Column(String, nullable=True)
    recorded_at = Column(DateTime, default=dt.datetime.utcnow)
