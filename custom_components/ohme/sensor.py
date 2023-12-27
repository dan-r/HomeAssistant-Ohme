"""Platform for sensor integration."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import UnitOfPower, UnitOfEnergy
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import generate_entity_id
from .const import DOMAIN, DATA_CLIENT, DATA_COORDINATOR, DATA_STATISTICS_COORDINATOR
from .coordinator import OhmeUpdateCoordinator, OhmeStatisticsUpdateCoordinator


async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities
):
    """Setup sensors and configure coordinator."""
    coordinator = hass.data[DOMAIN][DATA_COORDINATOR]
    stats_coordinator = hass.data[DOMAIN][DATA_STATISTICS_COORDINATOR]

    sensors = [PowerDrawSensor(coordinator, hass), EnergyUsageSensor(stats_coordinator, hass)]

    async_add_entities(sensors, update_before_add=True)


class PowerDrawSensor(CoordinatorEntity[OhmeUpdateCoordinator], SensorEntity):
    """Sensor for car power draw."""
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
        """Get value from data returned from API by coordinator"""
        if self.coordinator.data and self.coordinator.data['power']:
            return self.coordinator.data['power']['watt']
        return 0


class EnergyUsageSensor(CoordinatorEntity[OhmeStatisticsUpdateCoordinator], SensorEntity):
    """Sensor for total energy usage."""
    _attr_name = "Ohme Accumulative Energy Usage"
    _attr_native_unit_of_measurement = UnitOfEnergy.WATT_HOUR
    _attr_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_device_class = SensorDeviceClass.ENERGY

    def __init__(
            self,
            coordinator: OhmeUpdateCoordinator,
            hass: HomeAssistant):
        super().__init__(coordinator=coordinator)

        self._state = None
        self._attributes = {}
        self._last_updated = None

        self.entity_id = generate_entity_id(
            "sensor.{}", "ohme_accumulative_energy", hass=hass)

        self._attr_device_info = hass.data[DOMAIN][DATA_CLIENT].get_device_info()

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self.entity_id

    @property
    def icon(self):
        """Icon of the sensor."""
        return "mdi:lightning-bolt"

    @property
    def native_value(self):
        """Get value from data returned from API by coordinator"""
        if self.coordinator.data and self.coordinator.data['energyChargedTotalWh']:
            return self.coordinator.data['energyChargedTotalWh']

        return None
