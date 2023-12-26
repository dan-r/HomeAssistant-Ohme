from datetime import timedelta
import logging

from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed
)

from .const import DOMAIN, DATA_CLIENT

_LOGGER = logging.getLogger(__name__)


class OhmeUpdateCoordinator(DataUpdateCoordinator):
    """Coordinator to pull from API periodically."""

    def __init__(self, hass):
        """Initialise coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Ohme Charger",
            update_interval=timedelta(seconds=60),
        )
        self._client = hass.data[DOMAIN][DATA_CLIENT]

    async def _async_update_data(self):
        """Fetch data from API endpoint."""
        try:
            return await self._client.async_get_charge_sessions()

        except BaseException:
            raise UpdateFailed("Error communicating with API")
