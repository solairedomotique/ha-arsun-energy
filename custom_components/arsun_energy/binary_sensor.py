"""Binary sensors for ARSUN Energy."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.entity import DeviceInfo

from .const import CONF_LED_1, CONF_LED_2, DOMAIN

DEFAULT_LEDS = {
    CONF_LED_1: "sensor.arsun_routeur_etat_led_s1",
    CONF_LED_2: "sensor.arsun_routeur_etat_led_s2",
}

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    device = DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name="ARSUN Energy",
        manufacturer="ARSUN × SOSUNELEC",
        model="Partenariat avec Solaire Domotique — site et chaîne YouTube",
        configuration_url="https://solaire-domotique.fr/ha/github/arsun/",
        sw_version="2.4",
    )
    configured = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
    async_add_entities([
        ArsunForcedModeBinarySensor(
            hass, entry, "1", configured.get(CONF_LED_1, DEFAULT_LEDS[CONF_LED_1]), device
        ),
        ArsunForcedModeBinarySensor(
            hass, entry, "2", configured.get(CONF_LED_2, DEFAULT_LEDS[CONF_LED_2]), device
        ),
    ])


class ArsunForcedModeBinarySensor(BinarySensorEntity):
    """Indicates whether one ARSUN output is forced (LED state H or P)."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:flash"

    def __init__(self, hass, entry, channel, source, device):
        self.hass = hass
        self.source = source
        self._attr_device_info = device
        self._attr_name = f"Marche forcée canal {channel}"
        self._attr_unique_id = f"{entry.entry_id}_forced_channel_{channel}"
        self._attr_is_on = None

    async def async_added_to_hass(self):
        self._update()
        if self.source:
            self.async_on_remove(
                async_track_state_change_event(self.hass, [self.source], self._changed)
            )

    @callback
    def _changed(self, event):
        self._update()
        self.async_write_ha_state()

    def _update(self):
        state = self.hass.states.get(self.source) if self.source else None
        self._attr_is_on = state is not None and state.state.upper() in ("H", "P")
