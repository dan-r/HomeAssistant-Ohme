from __future__ import annotations
import logging
import asyncio

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import generate_entity_id
from homeassistant.components.button import ButtonEntity

from .const import DOMAIN, DATA_CLIENT, DATA_COORDINATORS, COORDINATOR_CHARGESESSIONS
from .coordinator import OhmeChargeSessionsCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities
):
    """Setup switches."""
    client = hass.data[DOMAIN][DATA_CLIENT]
    coordinator = hass.data[DOMAIN][DATA_COORDINATORS][COORDINATOR_CHARGESESSIONS]

    buttons = []

    if client.is_capable("pluginsRequireApprovalMode"):
        buttons.append(
            OhmeApproveChargeButton(coordinator, hass, client)
        )

        async_add_entities(buttons, update_before_add=True)


class OhmeApproveChargeButton(ButtonEntity):
    """Button for approving a charge."""
    _attr_name = "Approve Charge"

    def __init__(self, coordinator: OhmeChargeSessionsCoordinator, hass: HomeAssistant, client):
        self._client = client
        self._coordinator = coordinator

        self._state = False
        self._last_updated = None
        self._attributes = {}

        self.entity_id = generate_entity_id(
            "switch.{}", "ohme_approve_charge", hass=hass)

        self._attr_device_info = client.get_device_info()

    @property
    def unique_id(self):
        """The unique ID of the switch."""
        return self._client.get_unique_id("approve_charge")

    @property
    def icon(self):
        """Icon of the switch."""
        return "mdi:check-decagram-outline"

    async def async_press(self):
        """Approve the charge."""
        await self._client.async_approve_charge()

        await asyncio.sleep(1)
        await self._coordinator.async_refresh()
