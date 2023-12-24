"""Platform for sensor integration."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import generate_entity_id
from .const import DOMAIN, DATA_CLIENT, DATA_COORDINATOR
from .coordinator import OhmeUpdateCoordinator


async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities
):
    coordinator = hass.data[DOMAIN][DATA_COORDINATOR]

    sensors = [ExampleSensor(coordinator, hass)]

    async_add_entities(sensors, update_before_add=True)


class ExampleSensor(CoordinatorEntity[OhmeUpdateCoordinator], SensorEntity):
    _attr_name = "Ohme Power Draw"
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = SensorDeviceClass.POWER

    def __init__(
            self,
            coordinator: OhmeUpdateCoordinator,
            hass: HomeAssistant):
        super().__init__(coordinator=coordinator)

        self._state = None
        self._attributes = {}
        self._last_updated = None

        self.entity_id = generate_entity_id(
            "sensor.{}", "ohme_power_draw", hass=hass)

        self._attr_device_info = hass.data[DOMAIN][DATA_CLIENT].get_device_info()

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self.entity_id

    @property
    def icon(self):
        """Icon of the sensor."""
        return "mdi:ev-station"


    @property
    def native_value(self):
        if self.coordinator.data and self.coordinator.data['power']:
            return self.coordinator.data['power']['watt']
        return 0
