"""Platform for sensor integration."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import generate_entity_id
from .const import DOMAIN, DATA_COORDINATOR, DATA_CLIENT
from .coordinator import OhmeUpdateCoordinator


async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities,
):
    """Setup sensors and configure coordinator."""
    client = hass.data[DOMAIN][DATA_CLIENT]
    coordinator = hass.data[DOMAIN][DATA_COORDINATOR]

    sensors = [ConnectedSensor(coordinator, hass, client),
               ChargingSensor(coordinator, hass, client)]

    async_add_entities(sensors, update_before_add=True)


class ConnectedSensor(
        CoordinatorEntity[OhmeUpdateCoordinator],
        BinarySensorEntity):
    """Binary sensor for if car is plugged in."""

    _attr_name = "Car Connected"
    _attr_device_class = BinarySensorDeviceClass.PLUG

    def __init__(
            self,
            coordinator: OhmeUpdateCoordinator,
            hass: HomeAssistant,
            client):
        super().__init__(coordinator=coordinator)

        self._attributes = {}
        self._last_updated = None
        self._state = False
        self._client = client

        self.entity_id = generate_entity_id(
            "binary_sensor.{}", "ohme_car_connected", hass=hass)

        self._attr_device_info = hass.data[DOMAIN][DATA_CLIENT].get_device_info(
        )

    @property
    def icon(self):
        """Icon of the sensor."""
        return "mdi:ev-plug-type2"

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self._client.get_unique_id("car_connected")

    @property
    def is_on(self) -> bool:
        if self.coordinator.data is None:
            self._state = False
        else:
            self._state = bool(self.coordinator.data["mode"] != "DISCONNECTED")

        return self._state


class ChargingSensor(
        CoordinatorEntity[OhmeUpdateCoordinator],
        BinarySensorEntity):
    """Binary sensor for if car is charging."""

    _attr_name = "Car Charging"
    _attr_device_class = BinarySensorDeviceClass.BATTERY_CHARGING

    def __init__(
            self,
            coordinator: OhmeUpdateCoordinator,
            hass: HomeAssistant,
            client):
        super().__init__(coordinator=coordinator)

        self._attributes = {}
        self._last_updated = None
        self._state = False
        self._client = client

        self.entity_id = generate_entity_id(
            "binary_sensor.{}", "ohme_car_charging", hass=hass)

        self._attr_device_info = hass.data[DOMAIN][DATA_CLIENT].get_device_info(
        )

    @property
    def icon(self):
        """Icon of the sensor."""
        return "mdi:battery-charging-100"

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self._client.get_unique_id("ohme_car_charging")

    @property
    def is_on(self) -> bool:
        if self.coordinator.data and self.coordinator.data["power"]:
            # Assume the car is actively charging if drawing over 0 watts
            self._state = self.coordinator.data["power"]["watt"] > 0
        else:
            self._state = False

        return self._state
