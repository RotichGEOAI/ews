"""
Onboarding Agent.

Registers a farmer, captures plot geolocation, and assigns the plot to the
GeoAI cell keys (Earth Index tile, DEM cell, borehole grid cell) used by all
downstream agents. No external credentials required beyond the database.
"""
from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from db.models import Farmer, Plot

logger = logging.getLogger(__name__)


class OnboardingAgent:
    def __init__(self, session: Session):
        self.session = session

    def register_farmer(self, phone_number: str, channel: str = "whatsapp", language: str = "en") -> Farmer:
        farmer = Farmer(phone_number=phone_number, preferred_channel=channel, language=language)
        self.session.add(farmer)
        self.session.commit()
        logger.info("Registered farmer %s via %s", phone_number, channel)
        return farmer

    def register_plot(
        self, farmer: Farmer, county: str, ward: str, lon: float, lat: float
    ) -> Plot:
        from geoalchemy2.shape import from_shape
        from shapely.geometry import Point

        plot = Plot(
            farmer_id=farmer.id,
            county=county,
            ward=ward,
            geom=from_shape(Point(lon, lat), srid=4326),
            earth_index_tile_id=self._assign_earth_index_tile(lon, lat),
            dem_cell_id=self._assign_dem_cell(lon, lat),
            borehole_grid_cell_id=self._assign_borehole_cell(lon, lat),
        )
        self.session.add(plot)
        self.session.commit()
        logger.info("Registered plot for farmer %s in %s/%s", farmer.phone_number, county, ward)
        return plot

    @staticmethod
    def _assign_earth_index_tile(lon: float, lat: float) -> str:
        # Placeholder — replace with actual UTM/MGRS tile lookup logic
        # matching the Earth Index / Source Cooperative tiling scheme.
        return f"36N_{int(lon*100)}_{int(lat*100)}"

    @staticmethod
    def _assign_dem_cell(lon: float, lat: float) -> str:
        return f"dem_{round(lon, 2)}_{round(lat, 2)}"

    @staticmethod
    def _assign_borehole_cell(lon: float, lat: float) -> str:
        return f"borehole_{round(lon, 2)}_{round(lat, 2)}"
