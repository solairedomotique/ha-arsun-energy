"""Config flow for ARSUN Energy."""
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import CONF_POWER_SENSOR, DOMAIN


class ArsunEnergyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ARSUN Energy."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Select the ARSUN power sensor."""
        errors = {}
        if user_input is not None:
            entity_id = user_input[CONF_POWER_SENSOR]
            state = self.hass.states.get(entity_id)
            if state is None:
                errors["base"] = "entity_not_found"
            else:
                unit = state.attributes.get("unit_of_measurement")
                if unit not in ("W", "kW"):
                    errors["base"] = "invalid_unit"
                else:
                    await self.async_set_unique_id(entity_id)
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title="ARSUN Energy",
                        data={CONF_POWER_SENSOR: entity_id},
                    )

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_POWER_SENSOR,
                    default="sensor.arsun_routeur_injection_soutirage",
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                )
            }
        )
        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return ArsunEnergyOptionsFlow(config_entry)


class ArsunEnergyOptionsFlow(config_entries.OptionsFlow):
    """Allow changing the source sensor."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_POWER_SENSOR,
                    default=self.config_entry.options.get(
                        CONF_POWER_SENSOR,
                        self.config_entry.data[CONF_POWER_SENSOR],
                    ),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                )
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
