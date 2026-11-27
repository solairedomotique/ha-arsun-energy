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

from .const import CONF_LED_1, CONF_LED_2, CONF_OUTPUT_1, CONF_OUTPUT_2, CONF_POWER_SENSOR, DOMAIN

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
    """Return solar/grid W for outputs 1 and 2.

    ARSUN grid convention: negative = import from EDF, positive = export.
    If either LED reports H or P, grid import is allocated proportionally
    across the measured heater output powers. Otherwise all measured output
    power is classified as solar, as agreed for this integration.
    """
    p1_entity = _source(hass, entry_id, CONF_OUTPUT_1)
    p1 = max(0.0, _number(hass, p1_entity)) if p1_entity else 0.0
    p2_entity = _source(hass, entry_id, CONF_OUTPUT_2)
    p2 = max(0.0, _number(hass, p2_entity)) if p2_entity else 0.0
    led1_entity = _source(hass, entry_id, CONF_LED_1)
    led1 = hass.states.get(led1_entity) if led1_entity else None
    led2_entity = _source(hass, entry_id, CONF_LED_2)
    led2 = hass.states.get(led2_entity) if led2_entity else None
    forced = (
        (led1 is not None and led1.state.upper() in ("H", "P"))
        or (led2 is not None and led2.state.upper() in ("H", "P"))
    )
    if not forced:
        return {"s1_solar": p1, "s1_grid": 0.0, "s2_solar": p2, "s2_grid": 0.0}

    grid_entity = _source(hass, entry_id, CONF_POWER_SENSOR)
    grid_import = max(0.0, -_number(hass, grid_entity)) if grid_entity else 0.0
    total = p1 + p2
    if total <= 0:
        return {"s1_solar": 0.0, "s1_grid": 0.0, "s2_solar": 0.0, "s2_grid": 0.0}

    # Do not allocate more EDF power to the heaters than their measured load.
    allocated_grid = min(grid_import, total)
    grid1 = allocated_grid * p1 / total
    grid2 = allocated_grid * p2 / total
    return {
        "s1_solar": max(0.0, p1 - grid1),
        "s1_grid": grid1,
        "s2_solar": max(0.0, p2 - grid2),
        "s2_grid": grid2,
    }


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    source = _source(hass, entry.entry_id, CONF_POWER_SENSOR)
    output1 = _source(hass, entry.entry_id, CONF_OUTPUT_1)
    output2 = _source(hass, entry.entry_id, CONF_OUTPUT_2)
    led1 = _source(hass, entry.entry_id, CONF_LED_1)
    led2 = _source(hass, entry.entry_id, CONF_LED_2)
    device = DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name="Youtube : Solaire-domotique",
        manufacturer="ARSUN / Youtube solaire-domotique",
        model="solaire-domotique.fr",
    )
    async_add_entities([
        ArsunOriginalPowerSensor(hass, entry, source, device),
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
        "---": "Automatique en attente de surplus",
        "ON": "Surplus alimentant le chauffe-eau",
        "OFF": "Sortie non alimentée",
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
