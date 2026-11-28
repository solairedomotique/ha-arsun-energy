"""ARSUN Energy integration."""
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_BATTERY_SENSOR, CONF_LED_1, CONF_LED_2, CONF_OUTPUT_1, CONF_OUTPUT_2,
    CONF_POWER_SENSOR, DOMAIN, PLATFORMS,
)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    keys = (CONF_POWER_SENSOR, CONF_OUTPUT_1, CONF_OUTPUT_2, CONF_LED_1, CONF_LED_2, CONF_BATTERY_SENSOR)
    # Keep absent keys absent: legacy entries from <= 0.3.3 must continue
    # using the historical default entity IDs in sensor.py.
    configured = {}
    for key in keys:
        if key in entry.options:
            configured[key] = entry.options[key]
        elif key in entry.data:
            configured[key] = entry.data[key]
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = configured
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the integration when its options are changed."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unloaded
