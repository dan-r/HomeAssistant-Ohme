from __future__ import annotations
import asyncio
from homeassistant.components.number import NumberEntity, NumberDeviceClass
from homeassistant.components.number.const import NumberMode, PERCENTAGE
from homeassistant.const import UnitOfTime
from homeassistant.helpers.entity import generate_entity_id
from homeassistant.core import callback, HomeAssistant
from .const import DOMAIN, DATA_CLIENT, DATA_COORDINATORS, COORDINATOR_ACCOUNTINFO, COORDINATOR_CHARGESESSIONS, COORDINATOR_SCHEDULES
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
        coordinators[COORDINATOR_CHARGESESSIONS], coordinators[COORDINATOR_SCHEDULES], hass, client),
        PreconditioningNumber(
        coordinators[COORDINATOR_CHARGESESSIONS], coordinators[COORDINATOR_SCHEDULES], hass, client),
        PriceCapNumber(coordinators[COORDINATOR_ACCOUNTINFO], hass, client)]

    async_add_entities(numbers, update_before_add=True)


class TargetPercentNumber(NumberEntity):
    """Target percentage sensor."""
    _attr_name = "Target Percentage"
    _attr_device_class = NumberDeviceClass.BATTERY
    _attr_native_unit_of_measurement = PERCENTAGE
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
        if session_in_progress(self.hass, self.coordinator.data):
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
        if session_in_progress(self.hass, self.coordinator.data):
            target = round(
                self.coordinator.data['appliedRule']['targetPercent'])
        elif self.coordinator_schedules.data:
            target = round(self.coordinator_schedules.data['targetPercent'])

        self._state = target if target > 0 else None

    @property
    def native_value(self):
        return self._state


class PreconditioningNumber(NumberEntity):
    """Preconditioning sensor."""
    _attr_name = "Preconditioning"
    _attr_device_class = NumberDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_native_min_value = 0
    _attr_native_step = 5
    _attr_native_max_value = 60

    def __init__(self, coordinator, coordinator_schedules, hass: HomeAssistant, client):
        self.coordinator = coordinator
        self.coordinator_schedules = coordinator_schedules

        self._client = client

        self._state = None
        self._last_updated = None
        self._attributes = {}

        self.entity_id = generate_entity_id(
            "number.{}", "ohme_preconditioning", hass=hass)

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
        return self._client.get_unique_id("preconditioning")

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        # If session in progress, update this session, if not update the first schedule
        if session_in_progress(self.hass, self.coordinator.data):
            if value == 0:
                await self._client.async_apply_session_rule(pre_condition=False)
            else:
                await self._client.async_apply_session_rule(pre_condition=True, pre_condition_length=int(value))
            await asyncio.sleep(1)
            await self.coordinator.async_refresh()
        else:
            if value == 0:
                await self._client.async_update_schedule(pre_condition=False)
            else:
                await self._client.async_update_schedule(pre_condition=True, pre_condition_length=int(value))
            await asyncio.sleep(1)
            await self.coordinator_schedules.async_refresh()

    @property
    def icon(self):
        """Icon of the sensor."""
        return "mdi:air-conditioner"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Get value from data returned from API by coordinator"""
        precondition = None
        # Set with the same logic as reading
        if session_in_progress(self.hass, self.coordinator.data):
            enabled = self.coordinator.data['appliedRule'].get(
                'preconditioningEnabled', False)
            precondition = 0 if not enabled else self.coordinator.data['appliedRule'].get(
                'preconditionLengthMins', None)
        elif self.coordinator_schedules.data:
            enabled = self.coordinator_schedules.data.get(
                'preconditioningEnabled', False)
            precondition = 0 if not enabled else self.coordinator_schedules.data.get(
                'preconditionLengthMins', None)

        self._state = precondition

    @property
    def native_value(self):
        return self._state


class PriceCapNumber(NumberEntity):
    _attr_name = "Price Cap"
    _attr_device_class = NumberDeviceClass.MONETARY
    _attr_mode = NumberMode.BOX
    _attr_native_step = 0.1
    _attr_native_min_value = 1
    _attr_native_max_value = 100

    def __init__(self, coordinator, hass: HomeAssistant, client):
        self.coordinator = coordinator
        self._client = client
        self._state = None
        self.entity_id = generate_entity_id(
            "number.{}", "ohme_price_cap", hass=hass)

        self._attr_device_info = client.get_device_info()

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.coordinator.async_add_listener(
                self._handle_coordinator_update, None
            )
        )

    @property
    def unique_id(self):
        """The unique ID of the switch."""
        return self._client.get_unique_id("price_cap")

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        await self._client.async_change_price_cap(cap=value)

        await asyncio.sleep(1)
        await self.coordinator.async_refresh()

    @property
    def native_unit_of_measurement(self):
        if self.coordinator.data is None:
            return None
        
        penny_unit = {
            "GBP": "p",
            "EUR": "c"
        }
        currency = self.coordinator.data["userSettings"].get("currencyCode", "XXX")

        return penny_unit.get(currency, f"{currency}/100")
    
    @property
    def icon(self):
        """Icon of the sensor."""
        return "mdi:cash"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Get value from data returned from API by coordinator"""
        if self.coordinator.data is not None:
            self._state = self.coordinator.data["userSettings"]["chargeSettings"][0]["value"]
        self.async_write_ha_state()

    @property
    def native_value(self):
        return self._state
