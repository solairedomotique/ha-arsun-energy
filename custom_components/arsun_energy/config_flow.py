"""Config flow for ARSUN Energy with automatic discovery and manual mapping."""
from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_DETECTION_MODE, CONF_LED_1, CONF_LED_2, CONF_OUTPUT_1,
    CONF_OUTPUT_2, CONF_POWER_SENSOR, DOMAIN,
)

REQUIRED_KEYS = (CONF_POWER_SENSOR, CONF_OUTPUT_1, CONF_LED_1)
ALL_KEYS = (CONF_POWER_SENSOR, CONF_OUTPUT_1, CONF_OUTPUT_2, CONF_LED_1, CONF_LED_2)

TOKENS = {
    CONF_POWER_SENSOR: ("injection_soutirage", "injection", "soutirage", "grid", "reseau", "réseau"),
    CONF_OUTPUT_1: ("sortie_1", "sortie1", "output_1", "output1", "canal_1"),
    CONF_OUTPUT_2: ("sortie_2", "sortie2", "output_2", "output2", "canal_2"),
    CONF_LED_1: ("etat_led_s1", "led_s1", "etat_led_1", "led_1"),
    CONF_LED_2: ("etat_led_s2", "led_s2", "etat_led_2", "led_2"),
}


def _norm(value):
    return value.lower().replace("-", "_").replace(" ", "_")


def _score(entity_id, friendly_name, key):
    text = _norm(entity_id + " " + friendly_name)
    return max((len(token) for token in TOKENS[key] if _norm(token) in text), default=0)


def _discover(hass):
    """Suggest likely entities without assuming an ARSUN instance prefix."""
    found = {}
    sensors = hass.states.async_all("sensor")
    for key in ALL_KEYS:
        ranked = sorted(
            ((_score(s.entity_id, s.attributes.get("friendly_name", ""), key), s.entity_id)
             for s in sensors),
            reverse=True,
        )
        found[key] = ranked[0][1] if ranked and ranked[0][0] else None
    return found


def _entity_selector():
    return selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor"))


def _schema(defaults):
    schema = {}
    for key in ALL_KEYS:
        default = defaults.get(key)
        if key in REQUIRED_KEYS:
            marker = vol.Required(key, default=default) if default else vol.Required(key)
        else:
            marker = vol.Optional(key, default=default) if default else vol.Optional(key)
        schema[marker] = _entity_selector()
    return vol.Schema(schema)


class ArsunEnergyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        return await self.async_step_detection(user_input)

    async def async_step_detection(self, user_input=None):
        if user_input is not None:
            self._detection_mode = user_input[CONF_DETECTION_MODE]
            self._discovered = _discover(self.hass) if self._detection_mode == "auto" else {}
            return await self.async_step_sources()
        schema = vol.Schema({
            vol.Required(CONF_DETECTION_MODE, default="auto"): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[
                        {"value": "auto", "label": "Détection automatique (proposer les entités trouvées)"},
                        {"value": "manual", "label": "Configuration manuelle"},
                    ],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            )
        })
        return self.async_show_form(step_id="detection", data_schema=schema)

    async def async_step_sources(self, user_input=None):
        errors = {}
        defaults = getattr(self, "_discovered", {})
        if user_input is not None:
            for key in REQUIRED_KEYS:
                entity_id = user_input.get(key)
                state = self.hass.states.get(entity_id) if entity_id else None
                if state is None:
                    errors[key] = "entity_not_found"
                elif key in (CONF_POWER_SENSOR, CONF_OUTPUT_1) and state.attributes.get("unit_of_measurement") not in ("W", "kW"):
                    errors[key] = "invalid_power_unit"
            for key in (CONF_OUTPUT_2, CONF_LED_1, CONF_LED_2):
                entity_id = user_input.get(key)
                state = self.hass.states.get(entity_id) if entity_id else None
                if entity_id and state is None:
                    errors[key] = "entity_not_found"
                elif key == CONF_OUTPUT_2 and state is not None and state.attributes.get("unit_of_measurement") not in ("W", "kW"):
                    errors[key] = "invalid_power_unit"
            if not errors:
                data = {key: user_input.get(key) for key in ALL_KEYS}
                data[CONF_DETECTION_MODE] = getattr(self, "_detection_mode", "manual")
                await self.async_set_unique_id(f"{data[CONF_POWER_SENSOR]}_{data[CONF_OUTPUT_1]}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title="ARSUN Energy", data=data)

        preview_lines = []
        for key in ALL_KEYS:
            entity_id = defaults.get(key)
            state = self.hass.states.get(entity_id) if entity_id else None
            if entity_id:
                value = state.state if state else "indisponible"
                unit = state.attributes.get("unit_of_measurement", "") if state else ""
                preview_lines.append(f"{key}: {entity_id} = {value} {unit}".strip())
            else:
                preview_lines.append(f"{key}: aucune correspondance automatique")
        return self.async_show_form(
            step_id="sources",
            data_schema=_schema(defaults),
            errors=errors,
            description_placeholders={"preview": "\n".join(preview_lines)},
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return ArsunEnergyOptionsFlow(config_entry)


class ArsunEnergyOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data={k: user_input.get(k) for k in ALL_KEYS})
        legacy_defaults = {
            CONF_POWER_SENSOR: "sensor.arsun_routeur_injection_soutirage",
            CONF_OUTPUT_1: "sensor.arsun_routeur_sortie_1",
            CONF_OUTPUT_2: "sensor.arsun_routeur_sortie_2",
            CONF_LED_1: "sensor.arsun_routeur_etat_led_s1",
            CONF_LED_2: "sensor.arsun_routeur_etat_led_s2",
        }
        defaults = {
            key: self.config_entry.options.get(
                key, self.config_entry.data.get(key, legacy_defaults[key])
            )
            for key in ALL_KEYS
        }
        return self.async_show_form(step_id="init", data_schema=_schema(defaults))
