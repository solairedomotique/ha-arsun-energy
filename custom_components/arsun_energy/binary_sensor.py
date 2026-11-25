"""Binary sensors for ARSUN Energy."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN

CHANNELS = {
    "1": "sensor.arsun_routeur_etat_led_s1",
    "2": "sensor.arsun_routeur_etat_led_s2",
}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    device = DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name="Youtube : Solaire-domotique",
        manufacturer="ARSUN / Youtube solaire-domotique",
        model="solaire-domotique.fr",
    )
    async_add_entities([
        ArsunForcedModeBinarySensor(hass, entry, channel, entity_id, device)
        for channel, entity_id in CHANNELS.items()
    ])


class ArsunForcedModeBinarySensor(BinarySensorEntity):
    """Indicates whether one ARSUN output is forced (LED state H)."""

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
        self.async_on_remove(
            async_track_state_change_event(self.hass, [self.source], self._changed)
        )

    @callback
    def _changed(self, event):
        self._update()
        self.async_write_ha_state()

    def _update(self):
        state = self.hass.states.get(self.source)
        self._attr_is_on = state is not None and state.state.upper() == "H"
