"""Platform for sensor integration."""
from __future__ import annotations
import logging
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import generate_entity_id
from homeassistant.util.dt import (utcnow)
from .const import DOMAIN, DATA_COORDINATORS, COORDINATOR_CHARGESESSIONS, DATA_CLIENT
from .coordinator import OhmeChargeSessionsCoordinator
from .utils import charge_graph_in_slot
from time import time

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities,
):
    """Setup sensors and configure coordinator."""
    client = hass.data[DOMAIN][DATA_CLIENT]
    coordinator = hass.data[DOMAIN][DATA_COORDINATORS][COORDINATOR_CHARGESESSIONS]

    sensors = [ConnectedBinarySensor(coordinator, hass, client),
               ChargingBinarySensor(coordinator, hass, client),
               PendingApprovalBinarySensor(coordinator, hass, client),
               CurrentSlotBinarySensor(coordinator, hass, client)]

    async_add_entities(sensors, update_before_add=True)


class ConnectedBinarySensor(
        CoordinatorEntity[OhmeChargeSessionsCoordinator],
        BinarySensorEntity):
    """Binary sensor for if car is plugged in."""

    _attr_name = "Car Connected"
    _attr_device_class = BinarySensorDeviceClass.PLUG

    def __init__(
            self,
            coordinator: OhmeChargeSessionsCoordinator,
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


class ChargingBinarySensor(
        CoordinatorEntity[OhmeChargeSessionsCoordinator],
        BinarySensorEntity):
    """Binary sensor for if car is charging."""

    _attr_name = "Car Charging"
    _attr_device_class = BinarySensorDeviceClass.BATTERY_CHARGING

    def __init__(
            self,
            coordinator: OhmeChargeSessionsCoordinator,
            hass: HomeAssistant,
            client):
        super().__init__(coordinator=coordinator)

        self._attributes = {}
        self._last_updated = None
        self._state = False
        self._client = client

        # Cache the last power readings
        self._last_reading = None

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
        return self._state

    def _calculate_state(self) -> bool:
        """Some trickery to get the charge state to update quickly."""
        bsoc = self.coordinator.data['batterySoc']        
        power = self.coordinator.data["power"]["watt"]

        # If no last reading or no batterySoc, fallback to power > 0
        if not self._last_reading or not self._last_reading['batterySoc']:
            return self.coordinator.data["power"]["watt"] > 0
        
        # If Wh has positive delta and a nonzero power reading, we are charging
        # This isn't ideal - eg. quirk of MG ZS in #13, so need to revisit
        lr_bsoc = self._last_reading['batterySoc']
        delta = bsoc['wh'] - lr_bsoc['wh']
        if delta > 0 and power > 0:
            return True
        
        return False

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update data."""
        # If we have power info and the car is plugged in, calculate state. Otherwise, false
        if self.coordinator.data and self.coordinator.data["power"] and self.coordinator.data['mode'] != "DISCONNECTED":
            self._state = self._calculate_state()
        else:
            self._state = False

        self._last_reading = self.coordinator.data
        self._last_updated = utcnow()

        self.async_write_ha_state()


class PendingApprovalBinarySensor(
        CoordinatorEntity[OhmeChargeSessionsCoordinator],
        BinarySensorEntity):
    """Binary sensor for if a charge is pending approval."""

    _attr_name = "Pending Approval"

    def __init__(
            self,
            coordinator: OhmeChargeSessionsCoordinator,
            hass: HomeAssistant,
            client):
        super().__init__(coordinator=coordinator)

        self._attributes = {}
        self._last_updated = None
        self._state = False
        self._client = client

        self.entity_id = generate_entity_id(
            "binary_sensor.{}", "ohme_pending_approval", hass=hass)

        self._attr_device_info = hass.data[DOMAIN][DATA_CLIENT].get_device_info(
        )

    @property
    def icon(self):
        """Icon of the sensor."""
        return "mdi:alert-decagram"

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self._client.get_unique_id("pending_approval")

    @property
    def is_on(self) -> bool:
        if self.coordinator.data is None:
            self._state = False
        else:
            self._state = bool(
                self.coordinator.data["mode"] == "PENDING_APPROVAL")

        return self._state


class CurrentSlotBinarySensor(
        CoordinatorEntity[OhmeChargeSessionsCoordinator],
        BinarySensorEntity):
    """Binary sensor for if we are currently in a smart charge slot."""

    _attr_name = "Charge Slot Active"

    def __init__(
            self,
            coordinator: OhmeChargeSessionsCoordinator,
            hass: HomeAssistant,
            client):
        super().__init__(coordinator=coordinator)

        self._attributes = {}
        self._last_updated = None
        self._state = False
        self._client = client

        self.entity_id = generate_entity_id(
            "binary_sensor.{}", "ohme_slot_active", hass=hass)

        self._attr_device_info = hass.data[DOMAIN][DATA_CLIENT].get_device_info(
        )

    @property
    def icon(self):
        """Icon of the sensor."""
        return "mdi:calendar-check"

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self._client.get_unique_id("ohme_slot_active")

    @property
    def is_on(self) -> bool:
        return self._state

    @callback
    def _handle_coordinator_update(self) -> None:
        """Are we in a charge slot? This is a bit slow so we only update on coordinator data update."""
        if self.coordinator.data is None:
            self._state = None
        elif self.coordinator.data["mode"] == "DISCONNECTED":
            self._state = False
        else:
            self._state = charge_graph_in_slot(
                self.coordinator.data['startTime'], self.coordinator.data['chargeGraph']['points'])

        self._last_updated = utcnow()

        self.async_write_ha_state()
