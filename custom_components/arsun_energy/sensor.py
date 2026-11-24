"""Power and cumulative energy sensors for ARSUN Energy."""
from __future__ import annotations

from datetime import datetime
import logging

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfPower, UnitOfEnergy
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.util import dt as dt_util

from .const import CONF_POWER_SENSOR, DOMAIN, NAME

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    """Create the four ARSUN entities."""
    source = entry.options.get(CONF_POWER_SENSOR, entry.data[CONF_POWER_SENSOR])
    device_info = DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name="Youtube : Solaire-domotique",
        manufacturer="ARSUN / Youtube solaire-domotique",
        model="solaire-domotique.fr",
    )
    async_add_entities(
        [
            ArsunOriginalPowerSensor(hass, entry, source, device_info),
            ArsunPowerSensor(hass, entry, source, "consumption", device_info),
            ArsunPowerSensor(hass, entry, source, "export", device_info),
            ArsunGaugePowerSensor(hass, entry, source, device_info),
            ArsunEnergySensor(hass, entry, source, "consumption", device_info),
            ArsunEnergySensor(hass, entry, source, "export", device_info),
        ]
    )


class ArsunBaseSensor(SensorEntity):
    """Common source handling and device metadata."""

    _attr_has_entity_name = True

    def __init__(self, hass, entry, source, direction, device_info):
        self.hass = hass
        self.entry = entry
        self.source = source
        self.direction = direction
        self._attr_device_info = device_info
        suffix = "soutirage" if direction == "consumption" else "injection"
        self._attr_unique_id = f"{entry.entry_id}_{suffix}_{self.entity_kind}"
        self._attr_name = (
            ("Puissance " if self.entity_kind == "power" else "Énergie ")
            + ("soutirée" if direction == "consumption" else "injectée")
        )

    def _watts(self, state) -> float | None:
        if state is None:
            return None
        try:
            value = float(state.state)
        except (ValueError, TypeError):
            return None
        unit = state.attributes.get("unit_of_measurement")
        if unit == "kW":
            value *= 1000
        elif unit != "W":
            return None
        # ARSUN convention confirmed by the user:
        # positive = power drawn from grid; negative = power exported to grid.
        if self.direction == "consumption":
            return max(0.0, value)
        return max(0.0, -value)


class ArsunPowerSensor(ArsunBaseSensor):
    """Instantaneous split power sensor."""

    entity_kind = "power"
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, hass, entry, source, direction, device_info):
        super().__init__(hass, entry, source, direction, device_info)
        self._attr_unique_id += "_power"
        self._attr_native_value = None
        self._unsub = None

    async def async_added_to_hass(self):
        self._update_from_state(self.hass.states.get(self.source))
        self._unsub = async_track_state_change_event(
            self.hass, [self.source], self._handle_state_change
        )

    async def async_will_remove_from_hass(self):
        if self._unsub:
            self._unsub()

    @callback
    def _handle_state_change(self, event):
        self._update_from_state(event.data.get("new_state"))
        self.async_write_ha_state()

    def _update_from_state(self, state):
        self._attr_native_value = self._watts(state)


class ArsunOriginalPowerSensor(SensorEntity):
    """Expose the original signed ARSUN power value unchanged."""

    _attr_has_entity_name = True
    _attr_name = "Puissance réseau (origine)"
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, hass, entry, source, device_info):
        self.hass = hass
        self.source = source
        self._attr_device_info = device_info
        self._attr_unique_id = f"{entry.entry_id}_original_signed_power"
        self._attr_native_value = None
        self._unsub = None

    async def async_added_to_hass(self):
        self._update_from_state(self.hass.states.get(self.source))
        self._unsub = async_track_state_change_event(
            self.hass, [self.source], self._handle_state_change
        )

    async def async_will_remove_from_hass(self):
        if self._unsub:
            self._unsub()

    @callback
    def _handle_state_change(self, event):
        self._update_from_state(event.data.get("new_state"))
        self.async_write_ha_state()

    def _update_from_state(self, state):
        if state is None:
            self._attr_native_value = None
            return
        try:
            value = float(state.state)
        except (ValueError, TypeError):
            self._attr_native_value = None
            return
        unit = state.attributes.get("unit_of_measurement")
        if unit == "kW":
            value *= 1000
        elif unit != "W":
            self._attr_native_value = None
            return
        self._attr_native_value = value


class ArsunGaugePowerSensor(SensorEntity):
    """Signed power sensor for a bipolar Home Assistant gauge.

    Keep the ARSUN sign convention unchanged: positive is grid consumption,
    negative is export. Set a negative minimum and positive maximum on the
    Lovelace gauge card to display both directions around zero.
    """

    _attr_has_entity_name = True
    _attr_name = "Puissance jauge"
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, hass, entry, source, device_info):
        self.hass = hass
        self.source = source
        self._attr_device_info = device_info
        self._attr_unique_id = f"{entry.entry_id}_gauge_power"
        self._attr_native_value = None
        self._unsub = None

    async def async_added_to_hass(self):
        self._update_from_state(self.hass.states.get(self.source))
        self._unsub = async_track_state_change_event(
            self.hass, [self.source], self._handle_state_change
        )

    async def async_will_remove_from_hass(self):
        if self._unsub:
            self._unsub()

    @callback
    def _handle_state_change(self, event):
        self._update_from_state(event.data.get("new_state"))
        self.async_write_ha_state()

    def _update_from_state(self, state):
        if state is None:
            self._attr_native_value = None
            return
        try:
            value = float(state.state)
        except (ValueError, TypeError):
            self._attr_native_value = None
            return
        unit = state.attributes.get("unit_of_measurement")
        if unit == "kW":
            value *= 1000
        elif unit != "W":
            self._attr_native_value = None
            return
        # Preserve ARSUN sign: positive = grid consumption, negative = export.
        self._attr_native_value = value


class ArsunEnergySensor(ArsunBaseSensor, RestoreEntity):
    """Cumulative kWh sensor using trapezoidal integration and state restore."""

    entity_kind = "energy"
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, hass, entry, source, direction, device_info):
        super().__init__(hass, entry, source, direction, device_info)
        self._attr_unique_id += "_energy"
        self._attr_native_value = 0.0
        self._last_power = None
        self._last_time = None
        self._unsub = None

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state is not None:
            try:
                self._attr_native_value = max(0.0, float(last_state.state))
            except (ValueError, TypeError):
                self._attr_native_value = 0.0
        # Start a fresh integration interval at startup. This avoids inventing
        # energy during a Home Assistant shutdown or unavailable period.
        self._last_power = self._watts(self.hass.states.get(self.source))
        self._last_time = dt_util.utcnow()
        self._unsub = async_track_state_change_event(
            self.hass, [self.source], self._handle_state_change
        )
        self.async_write_ha_state()

    async def async_will_remove_from_hass(self):
        if self._unsub:
            self._unsub()

    @callback
    def _handle_state_change(self, event):
        now = dt_util.utcnow()
        new_power = self._watts(event.data.get("new_state"))
        if new_power is not None and self._last_power is not None and self._last_time:
            elapsed = max(0.0, (now - self._last_time).total_seconds())
            # Trapezoidal integration: average W × elapsed hours / 1000.
            self._attr_native_value += (
                (self._last_power + new_power) / 2.0
            ) * elapsed / 3_600_000.0
        self._last_power = new_power
        self._last_time = now
        self.async_write_ha_state()
