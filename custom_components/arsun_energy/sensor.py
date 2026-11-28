"""Sensors for ARSUN Energy."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfPower, UnitOfEnergy
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.util import dt as dt_util

from .const import CONF_BATTERY_SENSOR, CONF_LED_1, CONF_LED_2, CONF_OUTPUT_1, CONF_OUTPUT_2, CONF_POWER_SENSOR, DOMAIN

DEFAULT_ENTITIES = {
    CONF_POWER_SENSOR: "sensor.arsun_routeur_injection_soutirage",
    CONF_OUTPUT_1: "sensor.arsun_routeur_sortie_1",
    CONF_OUTPUT_2: "sensor.arsun_routeur_sortie_2",
    CONF_LED_1: "sensor.arsun_routeur_etat_led_s1",
    CONF_LED_2: "sensor.arsun_routeur_etat_led_s2",
}


def _source(hass, entry_id, key):
    configured = hass.data.get(DOMAIN, {}).get(entry_id, {})
    if key in configured:
        return configured[key]
    return DEFAULT_ENTITIES[key]


def _dependencies(hass, entry_id):
    return [value for value in (
        _source(hass, entry_id, CONF_POWER_SENSOR),
        _source(hass, entry_id, CONF_OUTPUT_1),
        _source(hass, entry_id, CONF_OUTPUT_2),
        _source(hass, entry_id, CONF_LED_1),
        _source(hass, entry_id, CONF_LED_2),
    ) if value]


def _number(hass, entity_id):
    state = hass.states.get(entity_id)
    if state is None:
        return 0.0
    try:
        value = float(state.state)
    except (TypeError, ValueError):
        return 0.0
    unit = state.attributes.get("unit_of_measurement")
    if unit == "kW":
        value *= 1000
    return value


def _split_heater_power(hass, entry_id):
    """Estimate solar/grid power for ARSUN heater outputs.

    H/P: forced mode. Allocate the measured global EDF import across forced
    outputs in proportion to their measured power; any remaining heater power
    is attributed to solar.
    ON: surplus solar is feeding the heater (100% solar).
    - / --- / OFF: output is stopped or not powered (0 W).
    """
    led_entities = {
        1: _source(hass, entry_id, CONF_LED_1),
        2: _source(hass, entry_id, CONF_LED_2),
    }
    output_entities = {
        1: _source(hass, entry_id, CONF_OUTPUT_1),
        2: _source(hass, entry_id, CONF_OUTPUT_2),
    }

    stopped_states = {"-", "---", "OFF"}
    forced_states = {"H", "P"}
    powers = {}
    states = {}

    for channel in (1, 2):
        led_entity = led_entities[channel]
        led_state = hass.states.get(led_entity) if led_entity else None
        state = led_state.state.strip().upper() if led_state else None
        states[channel] = state

        output_entity = output_entities[channel]
        measured_power = max(0.0, _number(hass, output_entity)) if output_entity else 0.0
        powers[channel] = 0.0 if state in stopped_states else measured_power

    # Only forced channels are eligible for the estimated EDF share.
    # An ON channel remains 100% solar, even if the other channel is forced.
    forced_channels = [
        channel for channel in (1, 2) if states[channel] in forced_states
    ]
    forced_total = sum(powers[channel] for channel in forced_channels)

    grid_import = 0.0
    if forced_total > 0:
        grid_entity = _source(hass, entry_id, CONF_POWER_SENSOR)
        # ARSUN convention: negative = import from EDF, positive = export.
        grid_import = max(0.0, -_number(hass, grid_entity)) if grid_entity else 0.0

    # The EDF share cannot exceed the measured power of the forced heaters.
    allocated_grid = min(grid_import, forced_total)

    result = {
        "s1_solar": 0.0,
        "s1_grid": 0.0,
        "s2_solar": 0.0,
        "s2_grid": 0.0,
    }
    for channel in (1, 2):
        power = powers[channel]
        grid_share = 0.0
        if channel in forced_channels and forced_total > 0:
            grid_share = allocated_grid * power / forced_total

        result[f"s{channel}_grid"] = grid_share
        result[f"s{channel}_solar"] = max(0.0, power - grid_share)

    return result


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    source = _source(hass, entry.entry_id, CONF_POWER_SENSOR)
    output1 = _source(hass, entry.entry_id, CONF_OUTPUT_1)
    output2 = _source(hass, entry.entry_id, CONF_OUTPUT_2)
    led1 = _source(hass, entry.entry_id, CONF_LED_1)
    led2 = _source(hass, entry.entry_id, CONF_LED_2)
    device = DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name="ARSUN Energy",
        manufacturer="ARSUN × SOSUNELEC",
        model="Partenariat avec Solaire Domotique — site et chaîne YouTube",
        configuration_url="https://solaire-domotique.fr/ha/github/arsun/",
        sw_version="0.4.4",
    )
    async_add_entities([
        ArsunOriginalPowerSensor(hass, entry, source, device),
        ArsunBatteryPowerSensor(hass, entry, _source(hass, entry.entry_id, CONF_BATTERY_SENSOR), device),
        ArsunOutputPowerSensor(hass, entry, output1, "1", device),
        ArsunOutputPowerSensor(hass, entry, output2, "2", device),
        ArsunOutputModeSensor(hass, entry, led1, "1", device),
        ArsunOutputModeSensor(hass, entry, led2, "2", device),
        ArsunGridSplitPowerSensor(hass, entry, source, "consumption", device),
        ArsunGridSplitPowerSensor(hass, entry, source, "export", device),
        ArsunGaugePowerSensor(hass, entry, source, device),
        ArsunGridEnergySensor(hass, entry, source, "consumption", device),
        ArsunGridEnergySensor(hass, entry, source, "export", device),
        ArsunHeaterEnergySensor(hass, entry, "s1_solar", "Cumulus sortie 1 solaire", device),
        ArsunHeaterEnergySensor(hass, entry, "s1_grid", "Cumulus sortie 1 réseau", device),
        ArsunHeaterEnergySensor(hass, entry, "s2_solar", "Cumulus sortie 2 solaire", device),
        ArsunHeaterEnergySensor(hass, entry, "s2_grid", "Cumulus sortie 2 réseau", device),
    ])


class ArsunOriginalPowerSensor(SensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Puissance réseau (origine)"
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, hass, entry, source, device):
        self.hass, self.source = hass, source
        self._attr_device_info = device
        self._attr_unique_id = f"{entry.entry_id}_original_signed_power"
        self._attr_native_value = None

    async def async_added_to_hass(self):
        self._update()
        self.async_on_remove(async_track_state_change_event(self.hass, [self.source], self._changed) if self.source else (lambda: None))

    @callback
    def _changed(self, event):
        self._update()
        self.async_write_ha_state()

    def _update(self):
        self._attr_native_value = _number(self.hass, self.source)


class ArsunBatteryPowerSensor(SensorEntity):
    """Read-only display of the ARSUN battery instantaneous power."""

    _attr_has_entity_name = True
    _attr_name = "Puissance batterie"
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:battery-sync"

    def __init__(self, hass, entry, source, device):
        self.hass = hass
        self.source = source
        self._attr_device_info = device
        self._attr_unique_id = f"{entry.entry_id}_battery_power"
        self._attr_native_value = None

    async def async_added_to_hass(self):
        self._update()
        self.async_on_remove(
            async_track_state_change_event(self.hass, [self.source], self._changed)
            if self.source else (lambda: None)
        )

    @callback
    def _changed(self, event):
        self._update()
        self.async_write_ha_state()

    def _update(self):
        state = self.hass.states.get(self.source) if self.source else None
        self._attr_native_value = _number(self.hass, self.source) if state is not None else None


class ArsunOutputPowerSensor(SensorEntity):
    """Instantaneous power measured on one ARSUN output."""

    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, hass, entry, source, channel, device):
        self.hass = hass
        self.source = source
        self._attr_device_info = device
        self._attr_unique_id = f"{entry.entry_id}_output_{channel}_power"
        self._attr_name = f"Puissance cumulus sortie {channel}"
        self._attr_native_value = None

    async def async_added_to_hass(self):
        self._update()
        self.async_on_remove(
            async_track_state_change_event(self.hass, [self.source], self._changed) if self.source else (lambda: None)
        )

    @callback
    def _changed(self, event):
        self._update()
        self.async_write_ha_state()

    def _update(self):
        self._attr_native_value = max(0.0, _number(self.hass, self.source)) if self.source else None


class ArsunOutputModeSensor(SensorEntity):
    """Human-readable ARSUN operating mode for one output."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:state-machine"

    STATE_LABELS = {
        "H": "Forcé H1H2",
        "P": "Programme Horaire",
        "---": "Arrêt / attente de surplus",
        "ON": "Surplus alimentant le chauffe-eau",
        "OFF": "Sortie non alimentée",
        "-": "Arrêt du chauffe-eau",
    }

    def __init__(self, hass, entry, source, channel, device):
        self.hass = hass
        self.source = source
        self._attr_device_info = device
        self._attr_unique_id = f"{entry.entry_id}_output_{channel}_mode"
        self._attr_name = f"Mode canal {channel}"
        self._attr_native_value = None

    async def async_added_to_hass(self):
        self._update()
        self.async_on_remove(
            async_track_state_change_event(self.hass, [self.source], self._changed) if self.source else (lambda: None)
        )

    @callback
    def _changed(self, event):
        self._update()
        self.async_write_ha_state()

    def _update(self):
        state = self.hass.states.get(self.source) if self.source else None
        if state is None:
            self._attr_native_value = None
            return
        raw = state.state.strip().upper()
        self._attr_native_value = self.STATE_LABELS.get(raw, raw)


class ArsunGridSplitPowerSensor(SensorEntity):
    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, hass, entry, source, direction, device):
        self.hass, self.source, self.direction = hass, source, direction
        self._attr_device_info = device
        self._attr_unique_id = f"{entry.entry_id}_{direction}_power"
        self._attr_name = "Puissance consommée EDF" if direction == "consumption" else "Puissance redonnée à EDF"
        self._attr_native_value = None

    async def async_added_to_hass(self):
        self._update()
        self.async_on_remove(async_track_state_change_event(self.hass, [self.source], self._changed) if self.source else (lambda: None))

    @callback
    def _changed(self, event):
        self._update()
        self.async_write_ha_state()

    def _update(self):
        value = _number(self.hass, self.source)
        self._attr_native_value = max(0.0, -value) if self.direction == "consumption" else max(0.0, value)


class ArsunGaugePowerSensor(SensorEntity):
    """Positive = export to EDF; negative = import from EDF."""
    _attr_has_entity_name = True
    _attr_name = "Puissance jauge"
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, hass, entry, source, device):
        self.hass, self.source = hass, source
        self._attr_device_info = device
        self._attr_unique_id = f"{entry.entry_id}_gauge_power"
        self._attr_native_value = None

    async def async_added_to_hass(self):
        self._update()
        self.async_on_remove(async_track_state_change_event(self.hass, [self.source], self._changed) if self.source else (lambda: None))

    @callback
    def _changed(self, event):
        self._update()
        self.async_write_ha_state()

    def _update(self):
        # Keep the source sign: positive export, negative EDF consumption.
        self._attr_native_value = _number(self.hass, self.source)


class ArsunGridEnergySensor(RestoreEntity, ArsunGridSplitPowerSensor):
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, hass, entry, source, direction, device):
        super().__init__(hass, entry, source, direction, device)
        self._attr_unique_id = f"{entry.entry_id}_{direction}_energy"
        self._attr_name = "Énergie consommée EDF" if direction == "consumption" else "Énergie redonnée à EDF"
        self._attr_native_value = 0.0
        self._last_power = None
        self._last_time = None

    async def async_added_to_hass(self):
        last = await self.async_get_last_state()
        if last:
            try:
                self._attr_native_value = max(0.0, float(last.state))
            except (TypeError, ValueError):
                pass
        self._update()
        self._last_power = self._attr_native_value_power()
        self._last_time = dt_util.utcnow()
        self.async_on_remove(async_track_state_change_event(self.hass, [self.source], self._changed) if self.source else (lambda: None))
        self.async_write_ha_state()

    def _attr_native_value_power(self):
        value = _number(self.hass, self.source)
        return max(0.0, -value) if self.direction == "consumption" else max(0.0, value)

    @callback
    def _changed(self, event):
        now = dt_util.utcnow()
        new = self._attr_native_value_power()
        if self._last_power is not None and self._last_time is not None:
            elapsed = max(0.0, (now - self._last_time).total_seconds())
            self._attr_native_value += (self._last_power + new) * 0.5 * elapsed / 3_600_000
        self._last_power, self._last_time = new, now
        self.async_write_ha_state()


class ArsunHeaterEnergySensor(SensorEntity, RestoreEntity):
    """Restored cumulative kWh from one calculated heater solar/grid share."""
    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, hass, entry, key, name, device):
        self.hass, self.key, self.entry = hass, key, entry
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_heater_{key}_energy"
        self._attr_device_info = device
        self._attr_native_value = 0.0
        self._last_power = None
        self._last_time = None

    async def async_added_to_hass(self):
        last = await self.async_get_last_state()
        if last:
            try:
                self._attr_native_value = max(0.0, float(last.state))
            except (TypeError, ValueError):
                pass
        self._last_power = _split_heater_power(self.hass, self.entry.entry_id)[self.key]
        self._last_time = dt_util.utcnow()
        self.async_on_remove(async_track_state_change_event(self.hass, _dependencies(self.hass, self.entry.entry_id), self._changed))
        self.async_write_ha_state()

    @callback
    def _changed(self, event):
        now = dt_util.utcnow()
        new_power = _split_heater_power(self.hass, self.entry.entry_id)[self.key]
        if self._last_power is not None and self._last_time is not None:
            elapsed = max(0.0, (now - self._last_time).total_seconds())
            self._attr_native_value += (self._last_power + new_power) * 0.5 * elapsed / 3_600_000
        self._last_power, self._last_time = new_power, now
        self.async_write_ha_state()
