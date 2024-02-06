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
from .const import DOMAIN, DATA_COORDINATORS, DATA_SLOTS, COORDINATOR_CHARGESESSIONS, COORDINATOR_ADVANCED, DATA_CLIENT
from .coordinator import OhmeChargeSessionsCoordinator, OhmeAdvancedSettingsCoordinator
from .utils import charge_graph_in_slot

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities,
):
    """Setup sensors and configure coordinator."""
    client = hass.data[DOMAIN][DATA_CLIENT]
    coordinator = hass.data[DOMAIN][DATA_COORDINATORS][COORDINATOR_CHARGESESSIONS]
    coordinator_advanced = hass.data[DOMAIN][DATA_COORDINATORS][COORDINATOR_ADVANCED]

    sensors = [ConnectedBinarySensor(coordinator, hass, client),
               ChargingBinarySensor(coordinator, hass, client),
               PendingApprovalBinarySensor(coordinator, hass, client),
               CurrentSlotBinarySensor(coordinator, hass, client),
               ChargerOnlineBinarySensor(coordinator_advanced, hass, client)]

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
        self._last_reading_in_slot = False

        # State variables for charge state detection
        self._trigger_count = 0

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
        power = self.coordinator.data["power"]["watt"]

        # If no last reading or no batterySoc/power, fallback to power > 0
        if not self._last_reading or not self._last_reading['batterySoc'] or not self._last_reading['power']:
            _LOGGER.debug("ChargingBinarySensor: No last reading, defaulting to power > 0")
            return power > 0
        
        # See if we are in a charge slot now and if we were for the last reading
        in_charge_slot = charge_graph_in_slot(
            self.coordinator.data['startTime'], self.coordinator.data['chargeGraph']['points'])
        lr_in_charge_slot = self._last_reading_in_slot
        # Store this for next time
        self._last_reading_in_slot = in_charge_slot

        # If:
        # - Power has dropped by 40%+ since the last reading
        # - Last reading we were in a charge slot
        # - Now we are not in a charge slot
        # The charge has JUST stopped on the session bounary but the power reading is lagging.
        # This condition makes sure we get the charge state updated on the tick immediately after charge stop.
        lr_power = self._last_reading["power"]["watt"]
        if lr_in_charge_slot and not in_charge_slot and lr_power > 0 and power / lr_power < 0.6:
            _LOGGER.debug("ChargingBinarySensor: Power drop on state boundary, assuming not charging")
            self._trigger_count = 0
            return False
        
        # Failing that, we use the watt hours field to check charge state:
        # - If Wh has positive delta
        # - We have a nonzero power reading
        # We are charging. Using the power reading isn't ideal - eg. quirk of MG ZS in #13, so need to revisit
        wh_delta = self.coordinator.data['batterySoc']['wh'] - self._last_reading['batterySoc']['wh']
        trigger_state = wh_delta > 0 and power > 0

        _LOGGER.debug(f"ChargingBinarySensor: Reading Wh delta of {wh_delta} and power of {power}w")

        # If state is going upwards, report straight away
        if trigger_state and not self._state:
            _LOGGER.debug("ChargingBinarySensor: Upwards state change, reporting immediately")
            self._trigger_count = 0
            return True

        # If state is going to change (downwards only for now), we want to see 3 consecutive readings of the state having
        # changed before reporting it.
        if self._state != trigger_state:
            _LOGGER.debug("ChargingBinarySensor: Downwards state change, incrementing counter")
            self._trigger_count += 1
            if self._trigger_count > 2:
                _LOGGER.debug("ChargingBinarySensor: Counter hit, publishing downward state change")
                self._trigger_count = 0
                return trigger_state
        else:
            self._trigger_count = 0

        _LOGGER.debug("ChargingBinarySensor: Returning existing state")
            
        # State hasn't changed or we haven't seen 3 changed values - return existing state
        return self._state

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update data."""
        # Don't accept updates if 5s hasnt passed
        # State calculations use deltas that may be unreliable to check if requests are too often
        if self._last_updated and (utcnow().timestamp() - self._last_updated.timestamp() < 5):
            _LOGGER.debug("ChargingBinarySensor: State update too soon - suppressing")
            return

        # If we have power info and the car is plugged in, calculate state. Otherwise, false
        if self.coordinator.data and self.coordinator.data["power"] and self.coordinator.data['mode'] != "DISCONNECTED":
            self._state = self._calculate_state()
        else:
            self._state = False
            _LOGGER.debug("ChargingBinarySensor: No power data or car disconnected - reporting False")

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

        self._last_updated = None
        self._state = False
        self._client = client
        self._hass = hass

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
    def extra_state_attributes(self):
        """Attributes of the sensor."""
        now = utcnow()
        slots = self._hass.data[DOMAIN][DATA_SLOTS] if DATA_SLOTS in self._hass.data[DOMAIN] else []

        return {
            "planned_dispatches": [x for x in slots if not x['end'] or x['end'] > now],
            "completed_dispatches": [x for x in slots if x['end'] < now]
        }

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

class ChargerOnlineBinarySensor(
        CoordinatorEntity[OhmeAdvancedSettingsCoordinator],
        BinarySensorEntity):
    """Binary sensor for if charger is online."""

    _attr_name = "Charger Online"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(
            self,
            coordinator: OhmeAdvancedSettingsCoordinator,
            hass: HomeAssistant,
            client):
        super().__init__(coordinator=coordinator)

        self._attributes = {}
        self._last_updated = None
        self._state = None
        self._client = client

        self.entity_id = generate_entity_id(
            "binary_sensor.{}", "ohme_charger_online", hass=hass)

        self._attr_device_info = hass.data[DOMAIN][DATA_CLIENT].get_device_info(
        )

    @property
    def icon(self):
        """Icon of the sensor."""
        return "mdi:web"

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self._client.get_unique_id("charger_online")

    @property
    def is_on(self) -> bool:
        if self.coordinator.data and self.coordinator.data["online"]:
            return True
        elif self.coordinator.data:
            return False
        return None
