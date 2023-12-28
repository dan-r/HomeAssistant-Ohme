from datetime import timedelta
import logging

from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed
)

from .const import DOMAIN, DATA_CLIENT

_LOGGER = logging.getLogger(__name__)


class OhmeChargeSessionsCoordinator(DataUpdateCoordinator):
    """Coordinator to pull from API periodically."""

    def __init__(self, hass):
        """Initialise coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Ohme Charger",
            update_interval=timedelta(seconds=30),
        )
        self._client = hass.data[DOMAIN][DATA_CLIENT]

    async def _async_update_data(self):
        """Fetch data from API endpoint."""
        try:
            return await self._client.async_get_charge_sessions()

        except BaseException:
            raise UpdateFailed("Error communicating with API")

class OhmeAccountInfoCoordinator(DataUpdateCoordinator):
    """Coordinator to pull from API periodically."""

    def __init__(self, hass):
        """Initialise coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Ohme Account Info",
            update_interval=timedelta(minutes=1),
        )
        self._client = hass.data[DOMAIN][DATA_CLIENT]

    async def _async_update_data(self):
        """Fetch data from API endpoint."""
        try:
            return await self._client.async_get_account_info()

        except BaseException:
            raise UpdateFailed("Error communicating with API")


class OhmeStatisticsCoordinator(DataUpdateCoordinator):
    """Coordinator to update statistics from API periodically.
       (But less so than OhmeUpdateCoordinator)"""

    def __init__(self, hass):
        """Initialise coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Ohme Charger Statistics",
            update_interval=timedelta(minutes=30),
        )
        self._client = hass.data[DOMAIN][DATA_CLIENT]

    async def _async_update_data(self):
        """Fetch data from API endpoint."""
        try:
            return await self._client.async_get_charge_statistics()

        except BaseException:
            raise UpdateFailed("Error communicating with API")
