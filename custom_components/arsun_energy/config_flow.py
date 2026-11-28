"""Config flow for ARSUN Energy with validated automatic entity discovery."""
from __future__ import annotations

import unicodedata
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_BATTERY_SENSOR, CONF_DETECTION_MODE, CONF_LED_1, CONF_LED_2,
    CONF_OUTPUT_1, CONF_OUTPUT_2, CONF_POWER_SENSOR, DOMAIN,
)

REQUIRED_KEYS = (CONF_POWER_SENSOR, CONF_OUTPUT_1, CONF_LED_1)
ALL_KEYS = (
    CONF_POWER_SENSOR, CONF_OUTPUT_1, CONF_OUTPUT_2,
    CONF_LED_1, CONF_LED_2, CONF_BATTERY_SENSOR,
)

# Specific terms are deliberately preferred over generic words such as
# "injection" or "canal", which can match unrelated entities.
TOKENS = {
    CONF_POWER_SENSOR: (
        "injection_soutirage", "injection soutirage", "puissance reseau",
        "puissance réseau", "soutirage edf", "grid power",
    ),
    CONF_OUTPUT_1: (
        "arsun routeur sortie 1", "routeur sortie 1", "sortie 1",
        "sortie_1", "sortie1", "output 1", "output_1", "output1",
    ),
    CONF_OUTPUT_2: (
        "arsun routeur sortie 2", "routeur sortie 2", "sortie 2",
        "sortie_2", "sortie2", "output 2", "output_2", "output2",
    ),
    CONF_LED_1: (
        "arsun routeur etat led s1", "etat led s1", "état led s1",
        "led s1", "led_s1", "etat_led_1", "led_1",
    ),
    CONF_LED_2: (
        "arsun routeur etat led s2", "etat led s2", "état led s2",
        "led s2", "led_s2", "etat_led_2", "led_2",
    ),
    CONF_BATTERY_SENSOR: (
        "arsun routeur batterie", "puissance batterie", "batterie arsun",
        "battery power",
    ),
}

POWER_KEYS = {
    CONF_POWER_SENSOR, CONF_OUTPUT_1, CONF_OUTPUT_2, CONF_BATTERY_SENSOR
}
KNOWN_LED_STATES = {"H", "P", "ON", "OFF", "-", "---"}


def _norm(value):
    value = unicodedata.normalize("NFKD", str(value or ""))
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return " ".join(value.lower().replace("_", " ").replace("-", " ").split())


def _power_unit(state):
    return state.attributes.get("unit_of_measurement") in ("W", "kW")


def _score(state, key):
    entity_id = _norm(state.entity_id)
    friendly = _norm(state.attributes.get("friendly_name", ""))
    combined = f"{entity_id} {friendly}"
    best = 0
    for token in TOKENS[key]:
        normalized = _norm(token)
        if normalized in friendly:
            best = max(best, 100 + len(normalized))
        if normalized in entity_id:
            best = max(best, 80 + len(normalized))

    if key in POWER_KEYS:
        if not _power_unit(state):
            return 0
        if state.attributes.get("device_class") == "power":
            best += 35
        else:
            best += 10
    else:
        # LED entities are identified by their channel-specific name.
        if "led" not in combined and "etat" not in combined:
            return 0
        led_value = state.state.strip().upper()
        if led_value in KNOWN_LED_STATES:
            best += 20
        elif led_value in ("UNKNOWN", "UNAVAILABLE", ""):
            best -= 5
        # Other values (including N) are not interpreted or rejected.
    return best


def _discover(hass):
    """Return the highest-scoring candidate per source, without hard matching prefixes."""
    sensors = hass.states.async_all("sensor")
    found = {}
    for key in ALL_KEYS:
        ranked = sorted(
            ((_score(state, key), state.entity_id) for state in sensors),
            key=lambda item: (item[0], item[1]),
            reverse=True,
        )
        found[key] = ranked[0][1] if ranked and ranked[0][0] > 0 else None
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


def _validate_power(hass, entity_id):
    state = hass.states.get(entity_id) if entity_id else None
    if state is None:
        return "entity_not_found"
    if not _power_unit(state):
        return "invalid_power_unit"
    return None


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
                error = _validate_power(self.hass, user_input.get(key)) if key != CONF_LED_1 else None
                if key == CONF_LED_1:
                    entity_id = user_input.get(key)
                    if not entity_id or self.hass.states.get(entity_id) is None:
                        error = "entity_not_found"
                if error:
                    errors[key] = error

            for key in (CONF_OUTPUT_2, CONF_BATTERY_SENSOR):
                entity_id = user_input.get(key)
                if entity_id:
                    error = _validate_power(self.hass, entity_id)
                    if error:
                        errors[key] = error

            for key in (CONF_LED_2,):
                entity_id = user_input.get(key)
                if entity_id and self.hass.states.get(entity_id) is None:
                    errors[key] = "entity_not_found"

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
            if state:
                value = state.state
                unit = state.attributes.get("unit_of_measurement", "")
                device_class = state.attributes.get("device_class", "non précisée")
                score = _score(state, key)
                preview_lines.append(
                    f"{key}: {entity_id} = {value} {unit} "
                    f"(device_class: {device_class}, score: {score})".strip()
                )
            else:
                preview_lines.append(f"{key}: aucune correspondance automatique")
        return self.async_show_form(
            step_id="sources",
            data_schema=_schema(defaults),
            errors=errors,
            description_placeholders={"preview": "\\n".join(preview_lines)},
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
            CONF_BATTERY_SENSOR: "sensor.arsun_routeur_batterie",
        }
        defaults = {
            key: self.config_entry.options.get(
                key, self.config_entry.data.get(key, legacy_defaults[key])
            )
            for key in ALL_KEYS
        }
        return self.async_show_form(step_id="init", data_schema=_schema(defaults))
