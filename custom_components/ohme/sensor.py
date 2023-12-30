"""Platform for sensor integration."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import UnitOfPower, UnitOfEnergy, UnitOfElectricCurrent, UnitOfElectricPotential
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import generate_entity_id
from homeassistant.util.dt import (utcnow)
from .const import DOMAIN, DATA_CLIENT, DATA_COORDINATORS, COORDINATOR_CHARGESESSIONS, COORDINATOR_STATISTICS, COORDINATOR_ADVANCED
from .coordinator import OhmeChargeSessionsCoordinator, OhmeStatisticsCoordinator
from .utils import charge_graph_next_slot


async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities
):
    """Setup sensors and configure coordinator."""
    client = hass.data[DOMAIN][DATA_CLIENT]
    coordinators = hass.data[DOMAIN][DATA_COORDINATORS]

    coordinator = coordinators[COORDINATOR_CHARGESESSIONS]
    stats_coordinator = coordinators[COORDINATOR_STATISTICS]
    adv_coordinator = coordinators[COORDINATOR_ADVANCED]

    sensors = [PowerDrawSensor(coordinator, hass, client),
               CurrentDrawSensor(coordinator, hass, client),
               VoltageSensor(coordinator, hass, client),
               CTSensor(adv_coordinator, hass, client),
               EnergyUsageSensor(stats_coordinator, hass, client),
               NextSlotEndSensor(coordinator, hass, client),
               NextSlotStartSensor(coordinator, hass, client)]

    async_add_entities(sensors, update_before_add=True)


class PowerDrawSensor(CoordinatorEntity[OhmeChargeSessionsCoordinator], SensorEntity):
    """Sensor for car power draw."""
    _attr_name = "Power Draw"
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = SensorDeviceClass.POWER

    def __init__(
            self,
            coordinator: OhmeChargeSessionsCoordinator,
            hass: HomeAssistant,
            client):
        super().__init__(coordinator=coordinator)

        self._state = None
        self._attributes = {}
        self._last_updated = None
        self._client = client

        self.entity_id = generate_entity_id(
            "sensor.{}", "ohme_power_draw", hass=hass)

        self._attr_device_info = hass.data[DOMAIN][DATA_CLIENT].get_device_info(
        )

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self._client.get_unique_id("power_draw")

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


class CurrentDrawSensor(CoordinatorEntity[OhmeChargeSessionsCoordinator], SensorEntity):
    """Sensor for car power draw."""
    _attr_name = "Current Draw"
    _attr_device_class = SensorDeviceClass.CURRENT
    _attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE

    def __init__(
            self,
            coordinator: OhmeChargeSessionsCoordinator,
            hass: HomeAssistant,
            client):
        super().__init__(coordinator=coordinator)

        self._state = None
        self._attributes = {}
        self._last_updated = None
        self._client = client

        self.entity_id = generate_entity_id(
            "sensor.{}", "ohme_current_draw", hass=hass)

        self._attr_device_info = hass.data[DOMAIN][DATA_CLIENT].get_device_info(
        )

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self._client.get_unique_id("current_draw")

    @property
    def icon(self):
        """Icon of the sensor."""
        return "mdi:current-ac"

    @property
    def native_value(self):
        """Get value from data returned from API by coordinator"""
        if self.coordinator.data and self.coordinator.data['power']:
            return self.coordinator.data['power']['amp']
        return 0


class VoltageSensor(CoordinatorEntity[OhmeChargeSessionsCoordinator], SensorEntity):
    """Sensor for EVSE voltage."""
    _attr_name = "Voltage"
    _attr_device_class = SensorDeviceClass.VOLTAGE
    _attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT

    def __init__(
            self,
            coordinator: OhmeChargeSessionsCoordinator,
            hass: HomeAssistant,
            client):
        super().__init__(coordinator=coordinator)

        self._state = None
        self._attributes = {}
        self._last_updated = None
        self._client = client

        self.entity_id = generate_entity_id(
            "sensor.{}", "ohme_voltage", hass=hass)

        self._attr_device_info = hass.data[DOMAIN][DATA_CLIENT].get_device_info(
        )

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self._client.get_unique_id("voltage")

    @property
    def icon(self):
        """Icon of the sensor."""
        return "mdi:sine-wave"

    @property
    def native_value(self):
        """Get value from data returned from API by coordinator"""
        if self.coordinator.data and self.coordinator.data['power']:
            return self.coordinator.data['power']['volt']
        return None


class CTSensor(CoordinatorEntity[OhmeChargeSessionsCoordinator], SensorEntity):
    """Sensor for car power draw."""
    _attr_name = "CT Reading"
    _attr_device_class = SensorDeviceClass.CURRENT
    _attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE

    def __init__(
            self,
            coordinator: OhmeChargeSessionsCoordinator,
            hass: HomeAssistant,
            client):
        super().__init__(coordinator=coordinator)

        self._state = None
        self._attributes = {}
        self._last_updated = None
        self._client = client

        self.entity_id = generate_entity_id(
            "sensor.{}", "ohme_ct_reading", hass=hass)

        self._attr_device_info = hass.data[DOMAIN][DATA_CLIENT].get_device_info(
        )

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self._client.get_unique_id("ct_reading")

    @property
    def icon(self):
        """Icon of the sensor."""
        return "mdi:gauge"

    @property
    def native_value(self):
        """Get value from data returned from API by coordinator"""
        return self.coordinator.data


class EnergyUsageSensor(CoordinatorEntity[OhmeStatisticsCoordinator], SensorEntity):
    """Sensor for total energy usage."""
    _attr_name = "Accumulative Energy Usage"
    _attr_native_unit_of_measurement = UnitOfEnergy.WATT_HOUR
    _attr_suggested_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_suggested_display_precision = 1
    _attr_device_class = SensorDeviceClass.ENERGY

    def __init__(
            self,
            coordinator: OhmeChargeSessionsCoordinator,
            hass: HomeAssistant,
            client):
        super().__init__(coordinator=coordinator)

        self._state = None
        self._attributes = {}
        self._last_updated = None
        self._client = client

        self.entity_id = generate_entity_id(
            "sensor.{}", "ohme_accumulative_energy", hass=hass)

        self._attr_device_info = hass.data[DOMAIN][DATA_CLIENT].get_device_info(
        )

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self._client.get_unique_id("accumulative_energy")

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


class NextSlotStartSensor(CoordinatorEntity[OhmeStatisticsCoordinator], SensorEntity):
    """Sensor for next smart charge slot start time."""
    _attr_name = "Next Charge Slot Start"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(
            self,
            coordinator: OhmeChargeSessionsCoordinator,
            hass: HomeAssistant,
            client):
        super().__init__(coordinator=coordinator)

        self._state = None
        self._attributes = {}
        self._last_updated = None
        self._client = client

        self.entity_id = generate_entity_id(
            "sensor.{}", "ohme_next_slot", hass=hass)

        self._attr_device_info = hass.data[DOMAIN][DATA_CLIENT].get_device_info(
        )

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self._client.get_unique_id("next_slot")

    @property
    def icon(self):
        """Icon of the sensor."""
        return "mdi:clock-star-four-points"

    @property
    def native_value(self):
        """Return pre-calculated state."""
        return self._state

    @callback
    def _handle_coordinator_update(self) -> None:
        """Calculate next timeslot. This is a bit slow so we only update on coordinator data update."""
        if self.coordinator.data is None or self.coordinator.data["mode"] == "DISCONNECTED":
            self._state = None
        else:
            self._state = charge_graph_next_slot(
                self.coordinator.data['startTime'], self.coordinator.data['chargeGraph']['points'])['start']

        self._last_updated = utcnow()

        self.async_write_ha_state()


class NextSlotEndSensor(CoordinatorEntity[OhmeStatisticsCoordinator], SensorEntity):
    """Sensor for next smart charge slot end time."""
    _attr_name = "Next Charge Slot End"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(
            self,
            coordinator: OhmeChargeSessionsCoordinator,
            hass: HomeAssistant,
            client):
        super().__init__(coordinator=coordinator)

        self._state = None
        self._attributes = {}
        self._last_updated = None
        self._client = client

        self.entity_id = generate_entity_id(
            "sensor.{}", "ohme_next_slot_end", hass=hass)

        self._attr_device_info = hass.data[DOMAIN][DATA_CLIENT].get_device_info(
        )

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self._client.get_unique_id("next_slot_end")

    @property
    def icon(self):
        """Icon of the sensor."""
        return "mdi:clock-star-four-points-outline"

    @property
    def native_value(self):
        """Return pre-calculated state."""
        return self._state

    @callback
    def _handle_coordinator_update(self) -> None:
        """Calculate next timeslot. This is a bit slow so we only update on coordinator data update."""
        if self.coordinator.data is None or self.coordinator.data["mode"] == "DISCONNECTED":
            self._state = None
        else:
            self._state = charge_graph_next_slot(
                self.coordinator.data['startTime'], self.coordinator.data['chargeGraph']['points'])['end']

        self._last_updated = utcnow()

        self.async_write_ha_state()
