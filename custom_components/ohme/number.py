from __future__ import annotations
import asyncio
from homeassistant.components.number import NumberEntity, NumberDeviceClass
from homeassistant.helpers.entity import generate_entity_id
from homeassistant.core import callback, HomeAssistant
from .const import DOMAIN, DATA_CLIENT, DATA_COORDINATORS, COORDINATOR_CHARGESESSIONS, COORDINATOR_SCHEDULES
from .utils import session_in_progress

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities
):
    """Setup switches and configure coordinator."""
    coordinators = hass.data[DOMAIN][DATA_COORDINATORS]

    client = hass.data[DOMAIN][DATA_CLIENT]

    numbers = [TargetPercentNumber(
        coordinators[COORDINATOR_CHARGESESSIONS], coordinators[COORDINATOR_SCHEDULES], hass, client)]

    async_add_entities(numbers, update_before_add=True)


class TargetPercentNumber(NumberEntity):
    """Target percentage sensor."""
    _attr_name = "Target Percentage"
    _attr_device_class = NumberDeviceClass.BATTERY
    _attr_suggested_display_precision = 0

    def __init__(self, coordinator, coordinator_schedules, hass: HomeAssistant, client):
        self.coordinator = coordinator
        self.coordinator_schedules = coordinator_schedules

        self._client = client

        self._state = None
        self._last_updated = None
        self._attributes = {}

        self.entity_id = generate_entity_id(
            "number.{}", "ohme_target_percent", hass=hass)

        self._attr_device_info = client.get_device_info()

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.coordinator.async_add_listener(
                self._handle_coordinator_update, None
            )
        )
        self.async_on_remove(
            self.coordinator_schedules.async_add_listener(
                self._handle_coordinator_update, None
            )
        )
        
    @property
    def unique_id(self):
        """The unique ID of the switch."""
        return self._client.get_unique_id("target_percent")

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        # If session in progress, update this session, if not update the first schedule
        if session_in_progress(self.coordinator.data):
            await self._client.async_apply_session_rule(target_percent=int(value))
            await asyncio.sleep(1)
            await self.coordinator.async_refresh()
        else:
            await self._client.async_update_schedule(target_percent=int(value))
            await asyncio.sleep(1)
            await self.coordinator_schedules.async_refresh()

    @property
    def icon(self):
        """Icon of the sensor."""
        return "mdi:battery-heart"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Get value from data returned from API by coordinator"""
        # Set with the same logic as reading
        if session_in_progress(self.coordinator.data):
            target = round(self.coordinator.data['appliedRule']['targetPercent'])
        elif self.coordinator_schedules.data:
            target = round(self.coordinator_schedules.data['targetPercent'])

        self._state = target if target > 0 else None

    @property
    def native_value(self):
        return self._state
