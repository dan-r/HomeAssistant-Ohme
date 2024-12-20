from datetime import timedelta
import logging

from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed
)

from .const import DOMAIN, DATA_CLIENT, DEFAULT_INTERVAL_CHARGESESSIONS, DEFAULT_INTERVAL_ACCOUNTINFO, DEFAULT_INTERVAL_ADVANCED, DEFAULT_INTERVAL_SCHEDULES
from .utils import get_option

_LOGGER = logging.getLogger(__name__)


class OhmeChargeSessionsCoordinator(DataUpdateCoordinator):
    """Coordinator to pull main charge state and power/current draw."""

    def __init__(self, hass, account_id):
        """Initialise coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Ohme Charge Sessions",
            update_interval=timedelta(minutes=
                get_option(hass, account_id, "interval_chargesessions", DEFAULT_INTERVAL_CHARGESESSIONS)
            ),
        )
        self._client = hass.data[DOMAIN][account_id][DATA_CLIENT]

    async def _async_update_data(self):
        """Fetch data from API endpoint."""
        try:
            return await self._client.async_get_charge_sessions()

        except BaseException:
            raise UpdateFailed("Error communicating with API")


class OhmeAccountInfoCoordinator(DataUpdateCoordinator):
    """Coordinator to pull charger settings."""

    def __init__(self, hass, account_id):
        """Initialise coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Ohme Account Info",
            update_interval=timedelta(minutes=
                get_option(hass, account_id, "interval_accountinfo", DEFAULT_INTERVAL_ACCOUNTINFO)
            ),
        )
        self._client = hass.data[DOMAIN][account_id][DATA_CLIENT]

    async def _async_update_data(self):
        """Fetch data from API endpoint."""
        try:
            return await self._client.async_get_account_info()

        except BaseException:
            raise UpdateFailed("Error communicating with API")


class OhmeAdvancedSettingsCoordinator(DataUpdateCoordinator):
    """Coordinator to pull CT clamp reading."""

    def __init__(self, hass, account_id):
        """Initialise coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Ohme Advanced Settings",
            update_interval=timedelta(minutes=
                get_option(hass, account_id, "interval_advanced", DEFAULT_INTERVAL_ADVANCED)
            ),
        )
        self._client = hass.data[DOMAIN][account_id][DATA_CLIENT]

    async def _async_update_data(self):
        """Fetch data from API endpoint."""
        try:
            return await self._client.async_get_advanced_settings()

        except BaseException:
            raise UpdateFailed("Error communicating with API")


class OhmeChargeSchedulesCoordinator(DataUpdateCoordinator):
    """Coordinator to pull charge schedules."""

    def __init__(self, hass, account_id):
        """Initialise coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Ohme Charge Schedules",
            update_interval=timedelta(minutes=
                get_option(hass, account_id, "interval_schedules", DEFAULT_INTERVAL_SCHEDULES)
            ),
        )
        self._client = hass.data[DOMAIN][account_id][DATA_CLIENT]

    async def _async_update_data(self):
        """Fetch data from API endpoint."""
        try:
            return await self._client.async_get_schedule()

        except BaseException:
            raise UpdateFailed("Error communicating with API")
